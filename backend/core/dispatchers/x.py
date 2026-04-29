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

from core.dispatchers import DispatchOutcome, DispatchResult
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

    if dry_run:
        logger.info(
            "[x.dry_run] would_post chars=%d preview=%r",
            len(text),
            text[:80],
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
    # We rely on httpx + a tiny inline OAuth1 helper (rather than pulling
    # the full ``requests-oauthlib`` dep) to keep the deploy footprint
    # tight. The helper lives next to the call so it stays auditable.
    try:
        from requests_oauthlib import OAuth1  # type: ignore[import-not-found]
    except ImportError:
        return DispatchResult(
            outcome=DispatchOutcome.FAILED,
            error="missing_dep_requests_oauthlib",
            duration_ms=_elapsed_ms(started),
        )

    auth = OAuth1(
        creds["api_key"],
        client_secret=creds["api_secret"],
        resource_owner_key=creds["access_token"],
        resource_owner_secret=creds["access_token_secret"],
        signature_type="auth_header",
    )

    body = {"text": text}
    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_S) as client:
            resp = await client.post(_API_URL, json=body, auth=_OAuth1Adapter(auth))
        snippet = resp.text[:200] if resp.text else None
        if resp.status_code == 401:
            return DispatchResult(
                outcome=DispatchOutcome.FAILED,
                error="x_unauthorized",
                duration_ms=_elapsed_ms(started),
                response_snippet=snippet,
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
            )
        if resp.status_code >= 400:
            return DispatchResult(
                outcome=DispatchOutcome.FAILED,
                error=f"http_{resp.status_code}",
                duration_ms=_elapsed_ms(started),
                response_snippet=snippet,
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
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[x] dispatch crashed")
        return DispatchResult(
            outcome=DispatchOutcome.FAILED,
            error=f"network_error: {exc}",
            duration_ms=_elapsed_ms(started),
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


class _OAuth1Adapter:
    """Bridge ``requests_oauthlib.OAuth1`` (sync, requests.PreparedRequest
    contract) onto httpx's auth-flow protocol.

    httpx accepts callables matching ``Auth.auth_flow(request)``. We
    delegate body+header signing to OAuth1 by wrapping a synthetic
    ``requests.PreparedRequest`` shape. This avoids pulling the entire
    ``requests`` runtime just for auth signing.
    """

    def __init__(self, oauth1):
        self._oauth1 = oauth1

    def auth_flow(self, request):
        # Build a minimal PreparedRequest-like object the OAuth1 client
        # can sign. We only need .url, .method, .headers, .body.
        body = request.read()
        prepared = _PreparedRequestStub(
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
            body=body if body else None,
        )
        signed = self._oauth1(prepared)
        # Copy back the Authorization header.
        if "Authorization" in signed.headers:
            request.headers["Authorization"] = signed.headers["Authorization"]
        yield request


class _PreparedRequestStub:
    """Minimal duck-typed shape for ``requests_oauthlib.OAuth1.__call__``."""

    def __init__(self, *, method, url, headers, body):
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body
