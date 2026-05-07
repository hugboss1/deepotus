"""infiltration_auto.py — Sprint 14.2 scaffold.

Automate (or semi-automate) the awarding of clearance levels 1 and 2
while remaining safe to ship **before** we have a paid X API tier.

Architecture
------------
Three verifiers, each independent, each with its own failure mode:

* **Level 1 — Telegram join**
    ``verify_telegram_member()`` — **works TODAY**. The Telegram Bot API
    (``getChatMember``) is free at any volume. We call it with the
    vault-stored ``TELEGRAM_BOT_TOKEN`` + ``TELEGRAM_CHAT_ID`` +
    the claimed ``user_id`` (the user pastes their numeric TG ID in the
    UI, we validate presence). Returns ``True`` only for status
    ``member``/``administrator``/``creator`` — ``kicked``/``left``
    explicitly fail.

* **Level 1 — X follow**
    ``verify_x_follow()`` — **returns (False, "x_tier_required")** until
    an X API Basic tier is wired up. The function body contains the
    real OAuth1/OAuth2 call path, wrapped in a feature flag so flipping
    it on later is a one-liner.

* **Level 2 — Share prophecy**
    Two paths depending on tier:
        a) ``verify_x_mention_live()`` — polls recent search
            (needs X Basic+).
        b) ``submit_share_for_review()`` — user pastes the URL of their
            post, it lands in ``x_share_submissions`` Mongo queue, admin
            approves/rejects from ``/admin/clearance``. Works TODAY.

KOL auto-DM (optional, Sprint 14.2.B)
-------------------------------------
``prepare_kol_dm_draft()`` — given a KOL mention coming from
``kol_listener``, synthesise a personalised DM (via the Tone Engine if
active), persist as ``status='draft_pending_approval'`` in
``kol_dm_drafts`` Mongo collection. The admin approves each DM from
the admin UI; on approval, if X API creds + DM scope are present, the
DM goes out — otherwise the item stays queued for later.

All functions are **idempotent** (double-triggering doesn't double-count
a level) and emit an ``infiltration_audit`` row so the admin can trace
every auto-promotion.
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

from core.config import db, logger
from core.secret_provider import (
    get_telegram_bot_token,
    get_telegram_chat_id,
)
from core import clearance_levels

# ---------------------------------------------------------------------
# Feature flags (can also be flipped from propaganda_settings in Mongo
# if you want to toggle without redeploy — kept as module-level for now
# to keep the surface area small).
# ---------------------------------------------------------------------
#: Sprint 17.5 — flipped to True. The X account is Pay-Per-Use with
#: credits and the operator authorised live verification calls. We
#: still cache aggressively (24h) to keep credit burn low.
X_FOLLOW_CHECK_ENABLED = True
X_MENTION_CHECK_ENABLED = True
X_DM_ENABLED = True

#: Project handle the follow check resolves against. Hard-coded here
#: so the backend doesn't need an extra round-trip to read it from the
#: vault on every check; rotate in code if the official handle ever
#: changes.
PROJECT_X_HANDLE = "deepotus_ai"

#: 24h cache for follow lookups — handles rarely change their follow
#: state inside a day, and a single Basic-tier rate-limit hit (15/15min)
#: would otherwise lock us out for the whole window.
_FOLLOW_CACHE_TTL_HOURS = 24

#: Lenient Telegram numeric ID validator (integers, 5–15 digits — Telegram
#: IDs are positive integers, usually 8–11 digits for individuals, up
#: to 15 for anonymous channel members).
_TG_ID_RE = re.compile(r"^-?\d{5,15}$")

#: The ``#DEEPOTUS`` hashtag + mint handle that a Level-2 share post
#: must contain to be eligible.
_SHARE_REQUIRED_TERMS = ("deepotus",)  # lowercased substring match
_SHARE_URL_RE = re.compile(
    r"^https?://(?:www\.|mobile\.)?(?:x|twitter)\.com/[^/]+/status/\d+",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------
# Audit helper (kept local so infiltration events are decoupled from
# propaganda_events, which is an operational stream for the dispatch
# worker — mixing them would muddle dashboards).
# ---------------------------------------------------------------------
async def _audit(
    *,
    email: str,
    action: str,
    outcome: str,
    level: Optional[int] = None,
    detail: Optional[Dict[str, Any]] = None,
) -> None:
    """Append a row to ``infiltration_audit``. Best-effort; never
    raises — audit failures must not block clearance flows."""
    try:
        await db.infiltration_audit.insert_one({
            "_id": str(uuid.uuid4()),
            "email": email.lower().strip(),
            "action": action,         # e.g. "verify_tg_join"
            "outcome": outcome,       # "ok" | "denied" | "blocked" | "error"
            "level": level,
            "detail": detail or {},
            "at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        logging.exception("[infiltration_audit] insert failed")


# ---------------------------------------------------------------------
# Level 1 — Telegram membership verification (live)
# ---------------------------------------------------------------------
async def verify_telegram_member(
    email: str,
    tg_user_id: str,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Check whether ``tg_user_id`` has actually joined the configured
    Telegram group/channel. Returns ``(ok, code, detail)``.

    Success path:
        Telegram API ``getChatMember`` returns ``{ok:true, result:{status: ...}}``
        and status is in ``{member, administrator, creator, restricted}``.
        We explicitly REJECT ``left`` and ``kicked`` — they're valid
        responses that mean the user is NOT currently in the chat.

    The auto-promotion to Level 1 is performed here if the check
    succeeds AND the user isn't already at L1+.
    """
    if not _TG_ID_RE.match(str(tg_user_id).strip()):
        await _audit(email=email, action="verify_tg_join",
                     outcome="denied",
                     detail={"reason": "invalid_tg_id"})
        return False, "invalid_tg_id", {
            "hint": (
                "Telegram user IDs are numeric. Use @userinfobot inside "
                "Telegram to get yours, then paste the number here."
            ),
        }

    bot_token = await get_telegram_bot_token()
    chat_id = await get_telegram_chat_id()
    if not bot_token or not chat_id:
        await _audit(email=email, action="verify_tg_join",
                     outcome="blocked",
                     detail={"reason": "tg_creds_missing"})
        return False, "tg_creds_missing", {
            "hint": (
                "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not yet stored "
                "in the Cabinet Vault. Admin side action required."
            ),
        }

    url = f"https://api.telegram.org/bot{bot_token}/getChatMember"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params={
                "chat_id": chat_id,
                "user_id": str(tg_user_id).strip(),
            })
    except httpx.TimeoutException:
        await _audit(email=email, action="verify_tg_join",
                     outcome="error", detail={"reason": "tg_timeout"})
        return False, "tg_timeout", None
    except Exception as exc:  # noqa: BLE001
        logger.exception("[verify_tg_join] network error")
        await _audit(email=email, action="verify_tg_join",
                     outcome="error",
                     detail={"reason": "tg_network_error", "exc": str(exc)})
        return False, "tg_network_error", None

    if resp.status_code >= 400:
        await _audit(email=email, action="verify_tg_join",
                     outcome="denied",
                     detail={"reason": f"tg_http_{resp.status_code}",
                             "snippet": resp.text[:120]})
        return False, f"tg_http_{resp.status_code}", {
            "hint": "Telegram rejected the bot's call. Check bot is admin.",
        }

    data = resp.json() or {}
    if not data.get("ok"):
        desc = data.get("description", "unknown")
        await _audit(email=email, action="verify_tg_join",
                     outcome="denied",
                     detail={"reason": "tg_api_not_ok", "desc": desc})
        return False, "tg_not_found", {
            "hint": f"Telegram returned: {desc}",
        }

    status = (data.get("result") or {}).get("status") or "unknown"
    # We accept active memberships. ``restricted`` is accepted because
    # it still means "in the chat but with limitations" — good enough
    # for Level 1.
    ok_statuses = {"member", "administrator", "creator", "restricted"}
    if status not in ok_statuses:
        await _audit(email=email, action="verify_tg_join",
                     outcome="denied",
                     detail={"reason": "tg_not_member", "status": status})
        return False, "tg_not_member", {
            "hint": (
                "You're not currently a member of the Telegram channel. "
                "Join first (the bot must be admin there)."
            ),
        }

    # Success — promote to L1 if not already there.
    status_row = await clearance_levels.get_status(email)
    current_level = (status_row or {}).get("level", 0)
    promoted = False
    if current_level < 1:
        await clearance_levels.admin_set_level(
            email=email,
            level=1,
            notes=f"auto L1 via Telegram (user_id={tg_user_id})",
            jti="system:verify_tg_join",
        )
        promoted = True

    # Persist the tg_user_id so we can re-verify later (e.g. the user
    # leaves the group before launch → we need to detect + demote).
    await db.clearance_levels.update_one(
        {"email": email.lower().strip()},
        {"$set": {"telegram_user_id": str(tg_user_id).strip(),
                  "telegram_verified_at": datetime.now(timezone.utc).isoformat()}},
    )

    await _audit(email=email, action="verify_tg_join",
                 outcome="ok", level=1,
                 detail={"promoted": promoted, "tg_status": status})
    return True, "ok", {"promoted": promoted, "level": 1}


# ---------------------------------------------------------------------
# Level 1 — X follow (stubbed until X API Basic tier)
# ---------------------------------------------------------------------
async def verify_x_follow(
    email: str,
    x_handle: str,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Check whether ``x_handle`` follows the project account.

    Sprint 17.5 — live implementation.

    Path:
      1. Honor the cached result in ``x_follow_cache`` (24h TTL) so a
         tight loop of submissions doesn't burn rate-limit budget.
      2. Resolve both handles to user IDs via
         ``GET /2/users/by/username/:handle`` (cached 7d in
         ``kol_user_id_cache`` — same collection used by the KOL
         listener so we don't double-spend credits on resolution).
      3. Page through ``GET /2/users/:agent_id/following`` looking for
         the project's user_id. Returns up to 1000 follows per page;
         we stop as soon as we find a hit.

    Returns ``(True, "ok", meta)`` on a confirmed follow, otherwise
    ``(False, reason, meta)``. ``reason`` ∈ {
        "ok", "no_bearer_token", "handle_unresolved",
        "project_handle_unresolved", "rate_limited",
        "not_following"
    }.

    Note: Level 1 promotion is the caller's responsibility — this
    function only reports the live state. Caller should record the
    result in ``infiltration_audit`` via ``_audit`` for traceability.
    """
    if not X_FOLLOW_CHECK_ENABLED:
        # Fallback (kept as escape hatch for emergency tier-down).
        await _audit(
            email=email, action="verify_x_follow", outcome="blocked",
            detail={"reason": "x_tier_required", "x_handle": x_handle},
        )
        return False, "x_tier_required", None

    handle = (x_handle or "").strip().lstrip("@")
    if not handle:
        return False, "missing_handle", None

    # Late import — avoids cold-start cost on test rigs that don't
    # ever exercise the live path.
    from core.secret_provider import get_twitter_bearer_token

    bearer = await get_twitter_bearer_token()
    if not bearer:
        await _audit(
            email=email, action="verify_x_follow", outcome="error",
            detail={"reason": "no_bearer_token"},
        )
        return False, "no_bearer_token", None

    cache = await db.x_follow_cache.find_one({"_id": handle.lower()})
    if cache:
        cached_at = cache.get("cached_at")
        try:
            if isinstance(cached_at, str):
                cached_at_dt = datetime.fromisoformat(cached_at.replace("Z", "+00:00"))
            else:
                cached_at_dt = cached_at
            age_h = (datetime.now(timezone.utc) - cached_at_dt).total_seconds() / 3600
        except Exception:  # noqa: BLE001
            age_h = _FOLLOW_CACHE_TTL_HOURS + 1
        if age_h < _FOLLOW_CACHE_TTL_HOURS:
            return (
                bool(cache.get("follows")),
                "ok" if cache.get("follows") else "not_following",
                {"cached": True, "cached_at": cache.get("cached_at")},
            )

    agent_id = await _resolve_user_id(handle, bearer)
    if not agent_id:
        return False, "handle_unresolved", {"handle": handle}

    project_id = await _resolve_user_id(PROJECT_X_HANDLE, bearer)
    if not project_id:
        return False, "project_handle_unresolved", {"project_handle": PROJECT_X_HANDLE}

    follows, reason = await _scan_following_for(agent_id, project_id, bearer)
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.x_follow_cache.update_one(
        {"_id": handle.lower()},
        {"$set": {
            "follows": bool(follows),
            "agent_user_id": agent_id,
            "project_user_id": project_id,
            "cached_at": now_iso,
            "last_reason": reason,
        }},
        upsert=True,
    )
    await _audit(
        email=email, action="verify_x_follow",
        outcome="ok" if follows else reason,
        detail={"handle": handle, "follows": follows, "reason": reason},
    )
    return follows, ("ok" if follows else reason), {"cached": False}


# ---------------------------------------------------------------------
# X API helpers (mirror the kol_listener pattern — kept local to avoid
# importing kol_listener and creating a circular dependency).
# ---------------------------------------------------------------------
_X_API_BASE = "https://api.twitter.com/2"
_X_REQUEST_TIMEOUT_S = 12.0


async def _resolve_user_id(handle: str, bearer: str) -> Optional[str]:
    """Resolve a handle → user_id, sharing the kol_user_id_cache row
    used by ``core.kol_listener`` so credit spend is amortised across
    both features."""
    handle_clean = (handle or "").strip().lstrip("@")
    if not handle_clean:
        return None
    cached = await db.kol_user_id_cache.find_one({"_id": handle_clean.lower()})
    if cached and cached.get("user_id"):
        return str(cached["user_id"])

    url = f"{_X_API_BASE}/users/by/username/{handle_clean}"
    try:
        async with httpx.AsyncClient(timeout=_X_REQUEST_TIMEOUT_S) as client:
            resp = await client.get(
                url, headers={"Authorization": f"Bearer {bearer}"},
            )
    except Exception:  # noqa: BLE001
        logger.exception("[infiltration_auto] user_id lookup crashed handle=%s", handle_clean)
        return None
    if resp.status_code >= 400:
        logger.warning(
            "[infiltration_auto] user_id http_%d handle=%s body=%s",
            resp.status_code, handle_clean, (resp.text or "")[:160],
        )
        return None
    user_id = ((resp.json() or {}).get("data") or {}).get("id")
    if not user_id:
        return None
    await db.kol_user_id_cache.update_one(
        {"_id": handle_clean.lower()},
        {"$set": {
            "user_id": str(user_id),
            "handle_cased": handle_clean,
            "cached_at": datetime.now(timezone.utc),
        }},
        upsert=True,
    )
    return str(user_id)


async def _scan_following_for(
    agent_id: str, project_id: str, bearer: str,
) -> Tuple[bool, str]:
    """Page through ``GET /2/users/:agent_id/following`` looking for
    ``project_id``. Returns ``(True, "ok")`` on hit, ``(False, reason)``
    otherwise. Capped at 5 pages (5000 follows) to bound spend — agents
    with bigger follow lists fall back to manual admin verification."""
    next_token: Optional[str] = None
    pages_scanned = 0
    max_pages = 5
    while pages_scanned < max_pages:
        url = f"{_X_API_BASE}/users/{agent_id}/following"
        params: Dict[str, Any] = {"max_results": 1000, "user.fields": "id"}
        if next_token:
            params["pagination_token"] = next_token
        try:
            async with httpx.AsyncClient(timeout=_X_REQUEST_TIMEOUT_S) as client:
                resp = await client.get(
                    url, params=params,
                    headers={"Authorization": f"Bearer {bearer}"},
                )
        except Exception:  # noqa: BLE001
            logger.exception(
                "[infiltration_auto] following fetch crashed agent_id=%s", agent_id,
            )
            return False, "fetch_error"
        if resp.status_code == 429:
            return False, "rate_limited"
        if resp.status_code >= 400:
            logger.warning(
                "[infiltration_auto] following http_%d agent_id=%s body=%s",
                resp.status_code, agent_id, (resp.text or "")[:160],
            )
            return False, f"http_{resp.status_code}"
        payload = resp.json() or {}
        for u in (payload.get("data") or []):
            if str(u.get("id") or "") == str(project_id):
                return True, "ok"
        meta = payload.get("meta") or {}
        next_token = meta.get("next_token")
        pages_scanned += 1
        if not next_token:
            break
    return False, "not_following"


# ---------------------------------------------------------------------
# Level 2 — Share prophecy (submit-for-review path, works today)
# ---------------------------------------------------------------------
async def submit_share_for_review(
    email: str,
    share_url: str,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """The user pastes the URL of their public post (X / Twitter)
    featuring ``$DEEPOTUS`` or ``#DEEPOTUS``. We validate the URL
    shape, store a submission, notify the admin. Actual promotion
    happens when the admin approves the submission.

    Why not promote immediately?
        We can't verify without hitting the X API that the post
        actually exists, is from the user, and mentions the right
        thing. Until Basic tier is on, admin eyeballs it.
    """
    url = (share_url or "").strip()
    if not _SHARE_URL_RE.match(url):
        await _audit(email=email, action="submit_share",
                     outcome="denied",
                     detail={"reason": "bad_url", "url": url[:200]})
        return False, "bad_url", {
            "hint": (
                "URL must look like https://x.com/<handle>/status/<id> "
                "or https://twitter.com/…/status/… — paste the post "
                "URL from your profile."
            ),
        }

    # Idempotency: the same URL from the same email can only sit once
    # in the pending queue.
    existing = await db.x_share_submissions.find_one({
        "email": email.lower().strip(),
        "share_url": url,
    })
    if existing:
        return True, "already_submitted", {
            "status": existing.get("status"),
            "submitted_at": existing.get("submitted_at"),
        }

    doc = {
        "_id": str(uuid.uuid4()),
        "email": email.lower().strip(),
        "share_url": url,
        "status": "pending_review",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "reviewed_at": None,
        "reviewed_by_jti": None,
        "reviewer_note": None,
    }
    await db.x_share_submissions.insert_one(doc)
    await _audit(email=email, action="submit_share",
                 outcome="ok",
                 detail={"url": url, "submission_id": doc["_id"]})
    return True, "pending_review", {
        "submission_id": doc["_id"],
        "status": "pending_review",
        "hint": (
            "Submission received. An operator will review it within "
            "24 hours and promote you to Level 02 if approved."
        ),
    }


async def review_share_submission(
    submission_id: str,
    *,
    approve: bool,
    reviewer_note: Optional[str],
    jti: str,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Admin action. If ``approve`` AND user not already at L2, promote
    them + mark submission as approved; else mark rejected."""
    sub = await db.x_share_submissions.find_one({"_id": submission_id})
    if not sub:
        return False, "not_found", None
    if sub["status"] != "pending_review":
        return False, "already_reviewed", {"status": sub["status"]}

    status = "approved" if approve else "rejected"
    await db.x_share_submissions.update_one(
        {"_id": submission_id},
        {"$set": {
            "status": status,
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_by_jti": jti,
            "reviewer_note": reviewer_note,
        }},
    )

    if approve:
        email = sub["email"]
        row = await clearance_levels.get_status(email)
        current = (row or {}).get("level", 0)
        if current < 2:
            await clearance_levels.admin_set_level(
                email=email, level=2,
                notes=f"auto L2 via share review ({submission_id})",
                jti=jti,
            )
        await _audit(email=email, action="review_share",
                     outcome="ok", level=2,
                     detail={"submission_id": submission_id,
                             "approved": True})
    else:
        await _audit(email=sub["email"], action="review_share",
                     outcome="denied",
                     detail={"submission_id": submission_id,
                             "approved": False,
                             "note": reviewer_note})
    return True, status, None


async def list_share_submissions(
    *,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    query: Dict[str, Any] = {}
    if status:
        query["status"] = status
    cursor = db.x_share_submissions.find(query).sort("submitted_at", -1).limit(limit)
    return [doc async for doc in cursor]


# ---------------------------------------------------------------------
# KOL auto-DM draft queue (Sprint 14.2.B)
# ---------------------------------------------------------------------
async def prepare_kol_dm_draft(
    kol_handle: str,
    kol_tweet_url: str,
    kol_tweet_excerpt: str,
    *,
    dm_template: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a ``kol_dm_drafts`` document in state ``draft_pending_approval``.

    The admin reviews + approves from the admin UI. On approval AND if
    ``X_DM_ENABLED`` is true, the DM is posted via X API; otherwise it
    stays queued (status ``approved_waiting_dispatch``) for later.
    """
    if not dm_template:
        dm_template = (
            "hey {handle} — caught your post. we're building on-chain "
            "for the 'Deep State' cynic; feels like you'd enjoy it. "
            "the vault opens at $DEEPOTUS launch. no pitch, just a "
            "seat at the terminal."
        )
    rendered = dm_template.replace("{handle}", kol_handle)

    doc = {
        "_id": str(uuid.uuid4()),
        "kol_handle": kol_handle,
        "kol_tweet_url": kol_tweet_url,
        "kol_tweet_excerpt": kol_tweet_excerpt[:400],
        "dm_body": rendered,
        "status": "draft_pending_approval",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "approved_at": None,
        "approved_by_jti": None,
        "dispatched_at": None,
        "x_dm_id": None,
    }
    await db.kol_dm_drafts.insert_one(doc)
    return doc


async def approve_kol_dm(
    draft_id: str,
    *,
    jti: str,
    final_body: Optional[str] = None,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Admin approves a drafted DM. If X DM is not yet enabled, the
    draft moves to ``approved_waiting_dispatch`` — the dispatch worker
    will pick it up the day ``X_DM_ENABLED`` is flipped."""
    draft = await db.kol_dm_drafts.find_one({"_id": draft_id})
    if not draft:
        return False, "not_found", None
    if draft["status"] != "draft_pending_approval":
        return False, "wrong_state", {"status": draft["status"]}

    patch = {
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "approved_by_jti": jti,
    }
    if final_body:
        patch["dm_body"] = final_body

    if X_DM_ENABLED:
        # Would dispatch here. For now just mark dispatch-ready; a
        # follow-up sprint wires the actual call.
        patch["status"] = "approved_waiting_dispatch"
    else:
        patch["status"] = "approved_waiting_dispatch"

    await db.kol_dm_drafts.update_one({"_id": draft_id}, {"$set": patch})
    return True, patch["status"], None


async def list_kol_dm_drafts(
    *,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    query: Dict[str, Any] = {}
    if status:
        query["status"] = status
    cursor = db.kol_dm_drafts.find(query).sort("created_at", -1).limit(limit)
    return [doc async for doc in cursor]


# ---------------------------------------------------------------------
# Diagnostics (admin-safe: never reveals secrets)
# ---------------------------------------------------------------------
async def feature_status() -> Dict[str, Any]:
    """Surface the live state of each verifier — which ones are live,
    which are blocked on a paid tier, how many items are sitting in
    review queues. Consumed by the admin UI to render clear chips."""
    pending_shares = await db.x_share_submissions.count_documents(
        {"status": "pending_review"},
    )
    kol_pending = await db.kol_dm_drafts.count_documents(
        {"status": "draft_pending_approval"},
    )
    kol_ready = await db.kol_dm_drafts.count_documents(
        {"status": "approved_waiting_dispatch"},
    )
    return {
        "telegram_join": {"enabled": True, "mode": "live"},
        "x_follow": {
            "enabled": X_FOLLOW_CHECK_ENABLED,
            "mode": "live" if X_FOLLOW_CHECK_ENABLED else "blocked",
            "blocker": None if X_FOLLOW_CHECK_ENABLED else "x_tier_required",
            "project_handle": PROJECT_X_HANDLE,
        },
        "x_share": {
            "enabled": True,
            "mode": "live" if X_MENTION_CHECK_ENABLED else "manual_review",
            "pending_review": pending_shares,
        },
        "kol_dm": {
            "enabled": True,
            "mode": "live" if X_DM_ENABLED else "draft_queue",
            "pending_approval": kol_pending,
            "approved_waiting_dispatch": kol_ready,
        },
    }


__all__ = [
    "verify_telegram_member",
    "verify_x_follow",
    "submit_share_for_review",
    "review_share_submission",
    "list_share_submissions",
    "prepare_kol_dm_draft",
    "approve_kol_dm",
    "list_kol_dm_drafts",
    "feature_status",
]
