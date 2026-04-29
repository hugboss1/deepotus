"""Propaganda Engine — the brain of PROTOCOL ΔΣ.

Responsibilities:
  * Resolve trigger config (DB) + market snapshot (Helius / vault_state).
  * Run the trigger detector → ``TriggerResult``.
  * Render a templated message (with vault-link injection rotation).
  * Hand the rendered message to the dispatch queue (auto vs approval).
  * Audit every fire / approve / reject in ``propaganda_events``.

Dispatcher I/O lives in ``core/dispatchers/*`` (Sprint 13.3) — here we
stay platform-agnostic so unit tests can run without network.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core import dispatch_queue, market_analytics, templates_repo, tone_engine
from core import sleeper_cell
from core.config import db
from core.triggers import KNOWN_TRIGGERS, TriggerCtx

logger = logging.getLogger("deepotus.propaganda.engine")

SETTINGS_ID = "settings"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "_id": SETTINGS_ID,
    "panic": False,
    "default_locale": "en",
    "vault_link_every": 3,           # every Nth message must mention the vault
    "vault_mention_counter": 0,      # rolling counter, increments on every dispatch
    "rate_limits": {
        "per_hour": 8,
        "per_day": 24,
        "per_trigger_minutes": 15,
    },
    # ---- Sprint 13.3 dispatcher toggles ----
    # Both default to the SAFEST possible scaffold:
    # - dispatch_enabled=False  → worker reads queue but does not
    #   touch any item. Admin opts in explicitly to start sending.
    # - dispatch_dry_run=True   → even when enabled, dispatchers
    #   short-circuit the HTTP call and just log. Admin flips this
    #   to False ONLY after credentials have been vaulted and
    #   verified (e.g. via the "tick now" button + audit log).
    "dispatch_enabled": False,
    "dispatch_dry_run": True,
    "default_delay_seconds_min": 10,
    "default_delay_seconds_max": 30,
    "platforms": ["telegram", "x"],
    "created_at": datetime.now(timezone.utc).isoformat(),
}


# ---------------------------------------------------------------------
# Settings + trigger config (Mongo-backed)
# ---------------------------------------------------------------------
async def get_settings() -> Dict[str, Any]:
    doc = await db.propaganda_settings.find_one({"_id": SETTINGS_ID})
    if not doc:
        await db.propaganda_settings.insert_one(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)
    return doc


async def set_panic(panic: bool, *, jti: Optional[str] = None) -> Dict[str, Any]:
    """Flip the panic kill switch. When turned ON we also kill every
    pending queue item immediately so nothing slips through."""
    await db.propaganda_settings.update_one(
        {"_id": SETTINGS_ID},
        {"$set": {"panic": bool(panic)}},
        upsert=True,
    )
    if panic:
        n = await dispatch_queue.kill_all_pending()
        await _audit("panic_on", jti=jti, meta={"killed": n})
    else:
        await _audit("panic_off", jti=jti)
    return await get_settings()


async def set_dispatch_toggle(
    *,
    enabled: Optional[bool] = None,
    dry_run: Optional[bool] = None,
    jti: Optional[str] = None,
) -> Dict[str, Any]:
    """Toggle the dispatcher's two safety knobs.

    Either argument may be omitted to leave that knob unchanged.
    Audit-logged so the admin can prove who flipped what when.

    The worker reads these on every tick — no scheduler restart needed.
    """
    patch: Dict[str, Any] = {}
    audit_meta: Dict[str, Any] = {}
    if enabled is not None:
        patch["dispatch_enabled"] = bool(enabled)
        audit_meta["dispatch_enabled"] = bool(enabled)
    if dry_run is not None:
        patch["dispatch_dry_run"] = bool(dry_run)
        audit_meta["dispatch_dry_run"] = bool(dry_run)
    if not patch:
        return await get_settings()
    await db.propaganda_settings.update_one(
        {"_id": SETTINGS_ID},
        {"$set": patch},
        upsert=True,
    )
    await _audit("dispatch_toggle", jti=jti, meta=audit_meta)
    return await get_settings()


async def list_triggers() -> List[Dict[str, Any]]:
    """Return one row per registered trigger, hydrated with its DB config
    (auto-creating it on first read so the admin always sees every key).
    """
    out: List[Dict[str, Any]] = []
    for key, t in KNOWN_TRIGGERS.items():
        cfg = await _ensure_trigger_cfg(key)
        out.append({
            "key": key,
            "label": t.label,
            "description": t.description,
            "enabled": bool(cfg.get("enabled", True)),
            "policy": cfg.get("policy", t.default_policy),
            "cooldown_minutes": int(cfg.get("cooldown_minutes", t.default_cooldown_minutes)),
            "last_fired_at": cfg.get("last_fired_at"),
            "fire_count": int(cfg.get("fire_count", 0)),
            "metadata": cfg.get("metadata") or {},
        })
    return out


async def update_trigger_cfg(
    key: str,
    *,
    enabled: Optional[bool] = None,
    policy: Optional[str] = None,
    cooldown_minutes: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if key not in KNOWN_TRIGGERS:
        raise ValueError(f"Unknown trigger '{key}'")
    patch: Dict[str, Any] = {}
    if enabled is not None:
        patch["enabled"] = bool(enabled)
    if policy is not None:
        if policy not in ("auto", "approval"):
            raise ValueError("policy must be 'auto' or 'approval'")
        patch["policy"] = policy
    if cooldown_minutes is not None:
        patch["cooldown_minutes"] = int(max(0, min(cooldown_minutes, 60 * 24)))
    if metadata is not None:
        patch["metadata"] = dict(metadata)
    if patch:
        await db.propaganda_triggers.update_one(
            {"_id": key}, {"$set": patch}, upsert=True,
        )
    cfg = await _ensure_trigger_cfg(key)
    return cfg


async def _ensure_trigger_cfg(key: str) -> Dict[str, Any]:
    t = KNOWN_TRIGGERS[key]
    doc = await db.propaganda_triggers.find_one({"_id": key})
    if doc:
        return doc
    new_doc = {
        "_id": key,
        "enabled": True,
        "policy": t.default_policy,
        "cooldown_minutes": t.default_cooldown_minutes,
        "metadata": dict(t.metadata_defaults),
        "last_fired_at": None,
        "fire_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.propaganda_triggers.insert_one(new_doc)
    return new_doc


async def _bump_trigger_fire(key: str) -> None:
    await db.propaganda_triggers.update_one(
        {"_id": key},
        {
            "$set": {"last_fired_at": datetime.now(timezone.utc).isoformat()},
            "$inc": {"fire_count": 1},
        },
        upsert=True,
    )


# ---------------------------------------------------------------------
# Core fire path
# ---------------------------------------------------------------------
async def fire(
    trigger_key: str,
    *,
    manual: bool = False,
    market: Optional[Dict[str, Any]] = None,
    payload_override: Optional[Dict[str, Any]] = None,
    locale_override: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    jti: Optional[str] = None,
    ip: Optional[str] = None,
) -> Dict[str, Any]:
    """Run a trigger end-to-end.

    Returns a dict describing what happened (queued / skipped / panic).
    Never raises on “normal” skip paths so the caller can surface a
    structured response to the admin UI.
    """
    if trigger_key not in KNOWN_TRIGGERS:
        return {"ok": False, "reason": "unknown_trigger", "trigger_key": trigger_key}

    settings = await get_settings()
    if settings.get("panic"):
        await _audit("fire_skip_panic", jti=jti, ip=ip, trigger_key=trigger_key)
        return {"ok": False, "reason": "panic_on"}

    # Pre-launch sleeper-cell gate: when active, market triggers that
    # would leak a buy link are blocked upstream. Manual fires for UI
    # smoke tests still go through so the operator can demo the engine.
    if not manual and await sleeper_cell.is_trigger_blocked(trigger_key):
        await _audit("fire_skip_sleeper", jti=jti, ip=ip,
                     trigger_key=trigger_key)
        return {"ok": False, "reason": "sleeper_cell_active"}

    cfg = await _ensure_trigger_cfg(trigger_key)
    if not cfg.get("enabled", True):
        await _audit("fire_skip_disabled", jti=jti, ip=ip, trigger_key=trigger_key)
        return {"ok": False, "reason": "trigger_disabled"}

    trig = KNOWN_TRIGGERS[trigger_key]

    # ---- Resolve market context -------------------------------------
    # When the caller didn't pre-build one (which is the common path for
    # Manual Fire from the admin UI), we synthesize a snapshot here so
    # detectors always see fresh links + bonding-curve state.
    if market is None:
        market = await market_analytics.current_market_snapshot()
        # Surface the trigger's own metadata (e.g. whale_buy threshold)
        # so the detector doesn't have to round-trip Mongo by itself.
        market["trigger_metadata"] = cfg.get("metadata") or {}
        # For the jeet_dip detector: include an on-demand dip analysis
        # so a manual fire still has the data it needs to assert.
        if trigger_key == "jeet_dip":
            market["dip_analysis"] = await market_analytics.detect_dip(
                window_minutes=2, threshold_pct=20.0,
            )

    ctx = TriggerCtx(
        trigger_key=trigger_key,
        manual=manual,
        market=market or {},
        payload_override=payload_override or {},
        jti=jti,
        ip=ip,
    )
    detect = trig.detect or (lambda _c: None)
    result = detect(ctx)
    if result is None or not result.fired:
        reason = (result.reason if result else "detector_returned_none") or "not_fired"
        await _audit("fire_skip", jti=jti, ip=ip, trigger_key=trigger_key,
                     meta={"reason": reason})
        return {"ok": False, "reason": reason}

    # ---- Pick template ----------------------------------------------
    locale = (locale_override or settings.get("default_locale") or "en").lower()
    every_n = max(1, int(settings.get("vault_link_every") or 3))
    counter = int(settings.get("vault_mention_counter") or 0) + 1
    must_mention_vault = (counter % every_n == 0)

    tpl = await templates_repo.pick(
        trigger_key=trigger_key,
        language=locale,
        mentions_vault_required=must_mention_vault,
    )
    if not tpl and must_mention_vault:
        # No vault-mention template available — fall back to any template.
        tpl = await templates_repo.pick(trigger_key=trigger_key, language=locale)
    if not tpl:
        await _audit("fire_no_template", jti=jti, ip=ip, trigger_key=trigger_key)
        return {"ok": False, "reason": "no_template"}

    # ---- Render placeholders ----------------------------------------
    payload = dict(result.payload)
    # Always offer the standard link placeholders so templates can
    # safely interpolate even when the trigger payload doesn't include
    # them explicitly.
    payload.setdefault("buy_link", market.get("buy_link", ""))
    payload.setdefault("raydium_link", market.get("raydium_link", ""))
    payload.setdefault("vault_link", market.get("vault_link", ""))
    rendered = _safe_format(tpl["content"], payload)

    # ---- Optional LLM rewrite (Sprint 13.2) -------------------------
    enhance = await tone_engine.maybe_enhance(rendered, locale=locale)
    final_content = enhance.get("content") or rendered
    used_llm = bool(enhance.get("used_llm"))

    # ---- Push to queue ----------------------------------------------
    plat_list = list(platforms or settings.get("platforms") or ["telegram", "x"])
    delay_min = int(settings.get("default_delay_seconds_min") or 10)
    delay_max = int(settings.get("default_delay_seconds_max") or 30)

    # Use `secrets.SystemRandom` rather than the stdlib PRNG so the
    # dispatch offset is harder to predict (and silences ruff S311).
    # Cosmetic only — the timing window stays humanized 10-30s.
    import secrets as _secrets

    delay = _secrets.SystemRandom().randint(delay_min, max(delay_min, delay_max))

    item = await dispatch_queue.propose(
        trigger_key=trigger_key,
        template_id=tpl["id"],
        rendered_content=final_content,
        platforms=plat_list,
        payload={**payload, "_llm_used": used_llm,
                 "_template_origin": tpl["content"] if used_llm else None},
        policy=cfg.get("policy", trig.default_policy),
        idempotency_key=result.idempotency_key,
        delay_seconds=delay,
        by_jti=jti,
        manual=manual,
    )

    # Persist counter increment + bump trigger stats.
    await db.propaganda_settings.update_one(
        {"_id": SETTINGS_ID},
        {"$set": {"vault_mention_counter": counter}},
    )
    await _bump_trigger_fire(trigger_key)
    # If this was a milestone announcement, persist the bump so we never
    # repeat the same tier.
    if trigger_key == "mc_milestone":
        try:
            tier = int(payload.get("mc") or 0)
            if tier > 0:
                await market_analytics.bump_last_milestone(tier)
        except Exception:  # noqa: BLE001
            pass
    await _audit("fire", jti=jti, ip=ip, trigger_key=trigger_key,
                 meta={"queue_item": item["id"], "manual": manual,
                       "policy": cfg.get("policy", trig.default_policy),
                       "llm_used": used_llm,
                       "tone_source": enhance.get("source")})
    return {"ok": True, "queue_item": item, "llm_used": used_llm}


def _safe_format(template: str, payload: Dict[str, Any]) -> str:
    """``str.format``-style interpolation that never raises on missing keys.

    Unknown placeholders are swapped for an empty string so a half-filled
    payload (e.g., no whale_amount) never crashes the engine — we’d rather
    ship a slightly empty message than crash and lose the trigger.
    """
    class _SafeDict(dict):
        def __missing__(self, k):  # noqa: D401
            return ""

    try:
        return template.format_map(_SafeDict(**payload))
    except Exception:  # noqa: BLE001
        return template


# ---------------------------------------------------------------------
# Audit log helper (reused by router approve/reject endpoints)
# ---------------------------------------------------------------------
async def audit(
    event_type: str,
    *,
    trigger_key: Optional[str] = None,
    queue_item_id: Optional[str] = None,
    jti: Optional[str] = None,
    ip: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    await _audit(event_type, jti=jti, ip=ip, trigger_key=trigger_key,
                 queue_item_id=queue_item_id, meta=meta)


async def list_activity(limit: int = 100) -> List[Dict[str, Any]]:
    cursor = db.propaganda_events.find({}).sort("at", -1).limit(min(max(limit, 1), 500))
    return [
        {
            "id": d["_id"],
            "type": d.get("type"),
            "trigger_key": d.get("trigger_key"),
            "queue_item_id": d.get("queue_item_id"),
            "by_jti": d.get("by_jti"),
            "ip": d.get("ip"),
            "at": d.get("at"),
            "meta": d.get("meta") or {},
        }
        async for d in cursor
    ]


async def _audit(
    event_type: str,
    *,
    jti: Optional[str] = None,
    ip: Optional[str] = None,
    trigger_key: Optional[str] = None,
    queue_item_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    await db.propaganda_events.insert_one({
        "_id": str(uuid.uuid4()),
        "type": event_type,
        "trigger_key": trigger_key,
        "queue_item_id": queue_item_id,
        "by_jti": jti,
        "ip": ip,
        "at": datetime.now(timezone.utc).isoformat(),
        "meta": meta or {},
    })
