"""X (Twitter) API v2 dispatcher.

Spec
----
* Auth        : OAuth 1.0a User Context (consumer key/secret + access token)
                because v2 ``POST /2/tweets`` requires Elevated tier
                (Free tier ≠ tweet creation).
* Endpoint    : ``POST https://api.twitter.com/2/tweets``
* Body        : ``{"text": "..."}`` (260 chars hard cap)

Credentials read from the Cabinet Vault under ``x_twitter/`` :
    * X_API_KEY              (consumer key)
    * X_API_SECRET           (consumer secret)
    * X_ACCESS_TOKEN
    * X_ACCESS_TOKEN_SECRET

Or from env (same names) as fallback in dev.

Dry-run mode
------------
Default for the scaffold. When ``dry_run=True`` we LOG the would-be
tweet and return SENT without any HTTP call.

Failure mapping
---------------
* Any of the 4 OAuth secrets missing → FAILED ("no_credentials")
* Tier-locked / 403                  → FAILED with error="x_tier_locked"
* 429 rate limit                     → FAILED ("x_rate_limited")
* Other 4xx/5xx                      → FAILED ("http_<code>")
* Timeout                            → FAILED ("timeout")

Tier policy
-----------
The actual posting requires X Elevated/Pro. Until the user confirms
their tier, leaving ``dispatch_dry_run=true`` in propaganda_settings
keeps the worker exercising the full pipeline (queue → schedule →
formatting → "would-send" log) without making real calls.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import httpx

from core.dispatchers.base import DispatchOutcome, DispatchResult
from core.secret_provider import resolve as _vault_resolve

logger = logging.getLogger("deepotus.propaganda.dispatchers.x")

_API_URL = "https://api.twitter.com/2/tweets"
_REQUEST_TIMEOUT_S = 15.0
_TWEET_MAX_CHARS = 260  # X allows 280, we keep 20 for safety on URLs/emoji


async def send(
    item: Dict[str, Any],
    *,
    dry_run: bool = True,
    settings: Optional[Dict[str, Any]] = None,
) -> DispatchResult:
    """Post a tweet for the given queue item.

    Args:
        item: Normalised queue item; must contain ``rendered_content``.
            Optionally carries ``meta.reply_to_tweet_id`` to post the
            tweet as a reply (used by the Prophet Interaction Bot).
        dry_run: When True, no real HTTP call.
        settings: Reserved for future thread/reply support.
    """
    started = time.monotonic()
    text = (item.get("rendered_content") or "").strip()
    if not text:
        return DispatchResult(
            outcome=DispatchOutcome.FAILED,
            error="empty_content",
            dry_run=dry_run,
            duration_ms=_elapsed_ms(started),
        )
    if len(text) > _TWEET_MAX_CHARS:
        text = text[: _TWEET_MAX_CHARS - 1] + "…"

    # Optional reply target — when present, X v2 requires the
    # ``reply.in_reply_to_tweet_id`` shape inside the body. We extract
    # it here (rather than mutating callers) so any flow that puts a
    # tweet id under ``meta.reply_to_tweet_id`` automatically becomes
    # a reply, with no other code change needed.
    reply_to_id: Optional[str] = None
    meta = item.get("meta") or {}
    raw_reply = meta.get("reply_to_tweet_id") or item.get("reply_to_tweet_id")
    if raw_reply is not None:
        reply_to_id = str(raw_reply).strip() or None

    if dry_run:
        logger.info(
            "[x.dry_run] would_post chars=%d reply_to=%s preview=%r",
            len(text), reply_to_id, text[:80],
        )
        return DispatchResult(
            outcome=DispatchOutcome.SENT,
            platform_message_id="dry-run",
            dry_run=True,
            duration_ms=_elapsed_ms(started),
            response_snippet="(dry-run, no HTTP call)",
        )

    # ------------- Live mode -------------
    creds = await _resolve_x_credentials()
    if not creds:
        return DispatchResult(
            outcome=DispatchOutcome.FAILED,
            error="no_credentials",
            duration_ms=_elapsed_ms(started),
        )

    # OAuth 1.0a is required for v2 POST /2/tweets in Elevated tier.
    # We use ``authlib.integrations.httpx_client.OAuth1Auth`` which
    # inherits directly from ``httpx.Auth`` and implements the full
    # ``auth_flow`` contract — no shim, no manual signing.
    #
    # This replaces the previous home-rolled ``_OAuth1Adapter`` that
    # tried to bridge ``requests_oauthlib.OAuth1`` onto httpx via a
    # synthetic PreparedRequest stub. The bridge worked at signature
    # level but the OAuth1 client called ``prepare_headers()`` on the
    # stub (which doesn't exist), raising a TypeError that surfaced
    # in production as "Exception in ASGI application" whenever the
    # admin clicked Approve / Push on a real tweet item.
    try:
        from authlib.integrations.httpx_client import (  # type: ignore[import-not-found]
            OAuth1Auth,
        )
    except ImportError:
        return DispatchResult(
            outcome=DispatchOutcome.FAILED,
            error="missing_dep_authlib",
            duration_ms=_elapsed_ms(started),
        )

    auth = OAuth1Auth(
        client_id=creds["api_key"],
        client_secret=creds["api_secret"],
        token=creds["access_token"],
        token_secret=creds["access_token_secret"],
    )

    body: Dict[str, Any] = {"text": text}
    if reply_to_id:
        body["reply"] = {"in_reply_to_tweet_id": reply_to_id}
    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_S) as client:
            resp = await client.post(_API_URL, json=body, auth=auth)
        snippet = resp.text[:200] if resp.text else None
        if resp.status_code == 401:
            return DispatchResult(
                outcome=DispatchOutcome.FAILED,
                error="x_unauthorized",
                duration_ms=_elapsed_ms(started),
                response_snippet=snippet,
            )
        if resp.status_code == 402:
            # X's "Payment Required" — the API tier on the connected
            # account does NOT permit POST /2/tweets, OR Pay-Per-Use
            # credits are exhausted / not enabled for this endpoint.
            # Code-side this is fine: the tweet was formed + signed
            # correctly, X simply refuses on billing grounds. Surface
            # an explicit error so the admin doesn't go hunting for a
            # phantom code bug.
            logger.error(
                "[x] HTTP 402 Payment Required — X account tier does NOT "
                "permit POST /2/tweets (or Pay-Per-Use credits exhausted). "
                "Visit https://developer.x.com/en/portal/dashboard → "
                "verify the App is on a paid tier or top up credits. "
                "snippet=%s", snippet,
            )
            return DispatchResult(
                outcome=DispatchOutcome.FAILED,
                error="x_billing_required",
                duration_ms=_elapsed_ms(started),
                response_snippet=(
                    "X HTTP 402 — paid tier required for POST /2/tweets. "
                    "Check developer.x.com → App tier / Pay-Per-Use credits. "
                    + (snippet or "")
                )[:480],
            )
        if resp.status_code == 403:
            return DispatchResult(
                outcome=DispatchOutcome.FAILED,
                error="x_tier_locked",
                duration_ms=_elapsed_ms(started),
                response_snippet=snippet,
            )
        if resp.status_code == 429:
            return DispatchResult(
                outcome=DispatchOutcome.FAILED,
                error="x_rate_limited",
                duration_ms=_elapsed_ms(started),
                response_snippet=snippet,
                transient_failure=True,
            )
        if resp.status_code >= 400:
            # 5xx are transient (X gateway issue); 4xx other than the
            # ones already handled above (401/402/403/429) are
            # permanent (bad payload, duplicate, invalid chars, etc.).
            transient = resp.status_code >= 500

            # Sprint 17.5d follow-up — parse X's structured 400 body so
            # the operator sees WHAT X reproached. POST /2/tweets typical
            # 400 shapes:
            #   { "title":"Forbidden",
            #     "type":".../duplicate-rules",
            #     "detail":"You are not permitted to create a duplicate Tweet." }
            #   { "title":"Invalid Request",
            #     "errors":[{"parameters":{"text":["..."]}, "message":"..."}],
            #     "detail":"One or more parameters to your request was invalid." }
            #   { "errors":[{"message":"Tweet needs to be a bit shorter.",
            #               "code":186}], ... }
            error_code = f"http_{resp.status_code}"
            error_detail: Optional[str] = None
            try:
                err_body = resp.json() if resp.text else {}
            except Exception:  # noqa: BLE001
                err_body = {}

            if isinstance(err_body, dict):
                # Top-level "type" URL is the cleanest classifier.
                err_type = str(err_body.get("type") or "").lower()
                err_title = str(err_body.get("title") or "").lower()
                err_detail = str(err_body.get("detail") or err_body.get("message") or "")
                # Specific reasons we promote to first-class error codes
                # so the queue UI can render an actionable hint.
                if "duplicate" in err_type or "duplicate" in err_detail.lower():
                    error_code = "x_duplicate_content"
                elif "too-long" in err_type or "shorter" in err_detail.lower() \
                        or "too long" in err_detail.lower():
                    error_code = "x_text_too_long"
                elif "rule-violation" in err_type or "violates" in err_detail.lower():
                    error_code = "x_policy_violation"
                elif err_title in {"invalid request", "unprocessable entity"}:
                    error_code = "x_invalid_payload"
                # Fallback — keep the http_<n> code but surface the detail.
                error_detail = err_detail or err_title or None
                # Drill into "errors[*].message" if no top-level detail.
                if not error_detail:
                    inner = err_body.get("errors") or []
                    if isinstance(inner, list) and inner:
                        first = inner[0] or {}
                        error_detail = str(first.get("message") or "") or None

            logger.error(
                "[x] HTTP %d on POST /2/tweets → code=%s detail=%s body=%s",
                resp.status_code, error_code, error_detail, snippet,
            )
            return DispatchResult(
                outcome=DispatchOutcome.FAILED,
                error=error_code,
                duration_ms=_elapsed_ms(started),
                response_snippet=(
                    f"X HTTP {resp.status_code}: "
                    + (error_detail or snippet or "(no detail)")
                )[:480],
                transient_failure=transient,
            )
        data = resp.json()
        tweet_id = (data.get("data") or {}).get("id")
        logger.info(
            "[x] tweeted chars=%d id=%s in %d ms",
            len(text),
            tweet_id,
            _elapsed_ms(started),
        )
        return DispatchResult(
            outcome=DispatchOutcome.SENT,
            platform_message_id=str(tweet_id) if tweet_id else None,
            duration_ms=_elapsed_ms(started),
            response_snippet=snippet,
        )
    except httpx.TimeoutException:
        return DispatchResult(
            outcome=DispatchOutcome.FAILED,
            error="timeout",
            duration_ms=_elapsed_ms(started),
            transient_failure=True,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[x] dispatch crashed")
        return DispatchResult(
            outcome=DispatchOutcome.FAILED,
            error=f"network_error: {exc}",
            duration_ms=_elapsed_ms(started),
            transient_failure=True,
        )


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
async def _resolve_x_credentials() -> Optional[Dict[str, str]]:
    """Resolve all 4 OAuth1.0a values. Returns None if any one is
    missing — the dispatcher will fail with ``no_credentials``."""
    keys = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")
    out: Dict[str, str] = {}
    for k in keys:
        val = await _vault_resolve("x_twitter", k, env_var=k)
        if not val:
            return None
        out[k.lower().replace("x_", "")] = val.strip()
    return out


def _elapsed_ms(started_monotonic: float) -> int:
    return int((time.monotonic() - started_monotonic) * 1000)


# NOTE on auth: the OAuth 1.0a signing is done via
# ``authlib.integrations.httpx_client.OAuth1Auth`` (instantiated inline
# inside ``send()``). It already inherits ``httpx.Auth`` and implements
# ``auth_flow``, so no custom adapter is needed here.
#
# The previous in-tree shim (``_OAuth1Adapter`` + ``_PreparedRequestStub``)
# tried to bridge ``requests_oauthlib.OAuth1`` onto httpx but tripped a
# TypeError because the stub did not expose ``prepare_headers()``. We
# kept this pointer note so a future maintainer doesn't try to revive
# the bridge.




async def verify_identity() -> Dict[str, Any]:
    """Diagnostic helper — calls ``GET /2/users/me`` with the OAuth 1.0a
    credentials currently stored in the Cabinet Vault, and returns the
    handle / id / name of the X account those credentials authenticate
    AS.

    Used by the admin's "Verify X identity" button (Sprint 17.5d) to
    answer the question: "I clicked Push, the queue reports SENT, but
    I don't see the tweet on @Deepotus_AI — are the credentials
    actually for that account?".

    Return shape:
      ``{ok: True,  username: "Deepotus_AI", id: "...", name: "..."}``
      ``{ok: False, error: "no_credentials" | "x_billing_required" | "http_<n>"}``

    Never raises — always returns a structured dict so the route can
    surface it directly to the UI.
    """
    creds = await _resolve_x_credentials()
    if not creds:
        return {"ok": False, "error": "no_credentials"}

    try:
        from authlib.integrations.httpx_client import OAuth1Auth
    except ImportError:
        return {"ok": False, "error": "missing_dep_authlib"}

    auth = OAuth1Auth(
        client_id=creds["api_key"],
        client_secret=creds["api_secret"],
        token=creds["access_token"],
        token_secret=creds["access_token_secret"],
    )

    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_S) as client:
            resp = await client.get(
                "https://api.twitter.com/2/users/me",
                auth=auth,
                params={"user.fields": "username,id,name,verified"},
            )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"network_error: {exc}"}

    if resp.status_code == 401:
        return {"ok": False, "error": "x_unauthorized"}
    if resp.status_code == 402:
        return {"ok": False, "error": "x_billing_required"}
    if resp.status_code >= 400:
        return {"ok": False, "error": f"http_{resp.status_code}",
                "snippet": (resp.text or "")[:240]}

    user = (resp.json() or {}).get("data") or {}
    return {
        "ok": True,
        "id": str(user.get("id") or ""),
        "username": str(user.get("username") or ""),
        "name": str(user.get("name") or ""),
        "verified": bool(user.get("verified", False)),
    }
