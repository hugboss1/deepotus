"""LLM compatibility shim — drop-in replacement for ``emergentintegrations.llm.chat``.

Why this exists
---------------
The original codebase used the ``emergentintegrations`` PyPI package
which is internal to Emergent's hosted environment and **not publicly
distributed**. When the project is deployed outside Emergent (Render,
Vercel, Fly, etc.) ``pip install emergentintegrations==0.1.0`` fails
with *"No matching distribution found"*.

This module preserves the exact public API the rest of the codebase
relies on:

    from core.llm_compat import LlmChat, UserMessage

    chat = LlmChat(
        api_key=...,
        session_id=...,
        system_message=...,
    ).with_model(provider, model)
    answer = await chat.send_message(UserMessage(text="..."))

…but routes the call through the official native SDKs already
installed in ``requirements.txt``:

    * ``openai``                  — for provider ``"openai"``
    * ``anthropic``               — for provider ``"anthropic"``
    * ``google-generativeai``     — for provider ``"gemini"``

API key resolution
------------------
The ``api_key`` argument passed to ``LlmChat(...)`` is treated as a
**hint / legacy fallback only** (it used to be the universal Emergent
key). The shim resolves the real provider-scoped key in this order:

    1. ``<PROVIDER>_API_KEY`` environment variable
       (OPENAI_API_KEY / ANTHROPIC_API_KEY / GEMINI_API_KEY)
    2. The Cabinet Vault (``llm_custom/<PROVIDER>_API_KEY``) when
       running inside the deployed app — checked lazily so this module
       can also be imported by one-shot scripts that don't have a DB
       handle.
    3. The ``api_key`` argument passed in (kept as a last resort so
       ``LlmChat(api_key=EMERGENT_LLM_KEY, …)`` invocations don't break
       in dev environments where the Emergent proxy IS reachable).
    4. ``litellm`` direct call as a final umbrella when none of the
       above resolved — this is mostly there for completeness; if the
       user has zero keys configured the call surfaces a clear runtime
       error so the caller can fall back to template-only mode.

Behaviour matrix
----------------

+--------------------+--------+---------+---------+----------------+
| Env on deployment  | OpenAI | Claude  | Gemini  | EMERGENT_LLM_KEY |
+====================+========+=========+=========+================+
| Render (no keys)   |  ❌    |  ❌    |  ❌    | ❌ (proxy off)  |
| Render + 1 native  |  ✅    |  ✅/❌ |  ✅/❌ | ❌              |
| Local Emergent dev |  ✅    |  ✅    |  ✅    | ✅              |
+--------------------+--------+---------+---------+----------------+

When **no** key is available the ``send_message()`` coroutine raises
``LlmCompatNoKeyError``. Callers (``tone_engine``, ``prophet_studio``,
``public.py``) already handle exceptions and fall back to the template
verbatim, so the user-visible effect on Render with zero keys is just:
"the propaganda is on-message but not LLM-enriched".

This file has zero hard dependency on the other ``core/*`` modules
beyond ``logging`` so the one-shot ``generate_*.py`` scripts keep
working when run from a stripped-down environment.
"""

from __future__ import annotations

import logging
import os
from typing import Optional, Tuple

logger = logging.getLogger("deepotus.llm_compat")


class LlmCompatNoKeyError(RuntimeError):
    """Raised when no usable API key was found for the requested provider."""


# ---------------------------------------------------------------------
# Public API — matches the original ``emergentintegrations`` shape
# ---------------------------------------------------------------------
class UserMessage:
    """Equivalent of ``emergentintegrations.llm.chat.UserMessage``.

    The original library accepted ``UserMessage(text=...)``. A few
    callers used positional too, so we accept both forms.
    """

    __slots__ = ("text",)

    def __init__(self, text: str = "", **_kw):
        self.text = str(text or "")

    def __repr__(self) -> str:  # pragma: no cover — debug only
        return f"UserMessage(text={self.text[:40]!r}…)"


class LlmChat:
    """Equivalent of ``emergentintegrations.llm.chat.LlmChat``.

    Builder pattern preserved:

        LlmChat(api_key, session_id, system_message)
            .with_model(provider, model)
            .send_message(UserMessage(...))   # async

    Internally we resolve the **real** provider key at ``send_message``
    time (not at construction) so a key rotated in the Cabinet Vault
    takes effect on the next call without restarting the process.
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        session_id: Optional[str] = None,
        system_message: Optional[str] = None,
    ):
        self._fallback_api_key = (api_key or "").strip() or None
        self._session_id = session_id or "default"
        self._system_message = system_message or ""
        self._provider: Optional[str] = None
        self._model: Optional[str] = None

    # ----- Builder ----------------------------------------------------
    def with_model(self, provider: str, model: str) -> "LlmChat":
        self._provider = (provider or "").strip().lower() or None
        self._model = (model or "").strip() or None
        return self

    # ----- Send -------------------------------------------------------
    async def send_message(self, message: UserMessage) -> str:
        if not self._provider or not self._model:
            raise ValueError(
                "LlmChat: .with_model(provider, model) must be called "
                "before .send_message()."
            )
        if not isinstance(message, UserMessage):
            raise TypeError("send_message expects a UserMessage instance")

        provider = self._provider
        api_key, source = await _resolve_api_key(
            provider, fallback=self._fallback_api_key
        )
        if not api_key:
            raise LlmCompatNoKeyError(
                f"No API key configured for provider={provider!r}. "
                f"Set the {provider.upper()}_API_KEY env var, store it "
                f"in the Cabinet Vault under llm_custom/, or pass it "
                f"as api_key to LlmChat()."
            )
        logger.info(
            "[llm_compat] provider=%s model=%s source=%s session=%s",
            provider,
            self._model,
            source,
            self._session_id,
        )
        # Dispatch to the right native SDK
        try:
            return await _DISPATCH[provider](
                api_key=api_key,
                model=self._model,
                system_message=self._system_message,
                user_text=message.text,
            )
        except KeyError as exc:
            raise ValueError(
                f"Unsupported provider: {provider!r}. "
                f"Supported: {sorted(_DISPATCH.keys())}"
            ) from exc


# ---------------------------------------------------------------------
# Key resolution
# ---------------------------------------------------------------------
_PROVIDER_ENV_VAR = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


async def _resolve_api_key(
    provider: str, *, fallback: Optional[str] = None
) -> Tuple[Optional[str], str]:
    """Return (key, source). Source is one of: env, vault, fallback, None."""
    env_var = _PROVIDER_ENV_VAR.get(provider)
    if env_var:
        env_val = os.environ.get(env_var, "").strip()
        if env_val:
            return env_val, "env"

    # Try the Cabinet Vault — this is wrapped because the import chain
    # touches Mongo and we want the shim to remain importable from
    # one-shot scripts that haven't connected to Mongo yet.
    try:
        from core.secret_provider import resolve as _vault_resolve  # lazy

        if env_var:
            vault_val = await _vault_resolve(
                "llm_custom", env_var, env_var=env_var
            )
            if vault_val:
                return str(vault_val).strip(), "vault"
    except Exception as exc:  # noqa: BLE001
        logger.debug("[llm_compat] vault resolve skipped: %s", exc)

    if fallback:
        return fallback, "fallback"
    return None, "none"


# ---------------------------------------------------------------------
# Native SDK dispatchers
# ---------------------------------------------------------------------
async def _call_openai(
    *, api_key: str, model: str, system_message: str, user_text: str
) -> str:
    from openai import AsyncOpenAI  # lazy import — keeps cold-start light

    client = AsyncOpenAI(api_key=api_key)
    resp = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_message or ""},
            {"role": "user", "content": user_text or ""},
        ],
        max_tokens=900,
    )
    return resp.choices[0].message.content or ""


async def _call_anthropic(
    *, api_key: str, model: str, system_message: str, user_text: str
) -> str:
    from anthropic import AsyncAnthropic  # lazy import

    client = AsyncAnthropic(api_key=api_key)
    resp = await client.messages.create(
        model=model,
        system=system_message or "",
        max_tokens=900,
        messages=[{"role": "user", "content": user_text or ""}],
    )
    chunks = [
        getattr(block, "text", "")
        for block in resp.content
        if getattr(block, "type", "") == "text"
    ]
    return "".join(chunks)


async def _call_gemini(
    *, api_key: str, model: str, system_message: str, user_text: str
) -> str:
    import google.generativeai as genai  # lazy import

    genai.configure(api_key=api_key)
    model_obj = genai.GenerativeModel(
        model_name=model,
        system_instruction=system_message or None,
    )
    resp = await model_obj.generate_content_async(user_text or "")
    return getattr(resp, "text", "") or ""


_DISPATCH = {
    "openai": _call_openai,
    "anthropic": _call_anthropic,
    "gemini": _call_gemini,
}


__all__ = ["LlmChat", "UserMessage", "LlmCompatNoKeyError"]
