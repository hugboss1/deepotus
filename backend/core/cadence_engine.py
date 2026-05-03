"""
core/cadence_engine.py — Sprint 19

Implements the CADENCE wiring described in `bot_config.cadence`:

  1. **Daily schedule**: at every minute the scheduler ticks this
     module; we look up `cadence.daily_schedule.{x,telegram}` and, when
     "now" matches a configured UTC slot for an enabled platform, we
     generate a V2 Prophet post and push it to the propaganda queue.
     `quiet_hours.enabled` short-circuits the tick — bots stay silent
     inside the configured window even if a slot fires.
     Per-day, per-slot deduplication is persisted on the singleton
     under `cadence._state.last_fired_today.{platform}.{slot}` so a
     restart never replays a slot we already fired today.

  2. **Reactive triggers**: at every minute (same tick), we read the
     current market snapshot (price × supply for MC, best-effort
     holders) and compare it against the configured milestone arrays.
     The first time a milestone is crossed we generate ONE V2 post
     and persist the milestone in
     `cadence._state.fired_milestones.{holders,marketcap_usd}` so we
     never re-announce the same threshold twice.

  3. **Whale buy reactive**: exposed as a `cadence_whale_react()`
     helper called by `core.whale_watcher` AFTER its own propaganda
     v1 enqueue. When `cadence.reactive_triggers.enabled` is true AND
     the alert's SOL volume crosses
     `cadence.reactive_triggers.whale_buy_min_sol`, we synthesise an
     ADDITIONAL V2 post (independent of the v1 templates).

All cadence posts go through `core.dispatch_queue.propose()` with
`policy="auto"` — the propaganda dispatch worker (already wired) sends
them to X / Telegram once credentials are present in the Cabinet Vault.
Until then the items sit in the queue with status `approved`, exactly
like the v1 propaganda items, and admins can inspect them in the
dashboard.

Trigger keys we use:
    cadence_daily         (Daily schedule slot fired)
    cadence_holder        (Holder milestone crossed)
    cadence_marketcap     (Marketcap milestone crossed)
    cadence_whale         (Whale buy passed cadence threshold)

Each post embeds in `payload`:
    template_id     — V2 archetype rolled (lore, satire_news, …)
    template_label  — human label
    slot_utc / mc / holder_count / sol_amount  — context-specific
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from core.bot_config_repo import (
    CONFIG_COLLECTION,
    CONFIG_SINGLETON_ID,
    get_bot_config,
)
from core.config import db
from core.dispatch_queue import propose as queue_propose
from core.prophet_studio import (
    PROMPT_TEMPLATES_V2,
    generate_post_v2,
)

logger = logging.getLogger("deepotus.cadence")

# Total supply hard-coded — same value used by the Tokenomics UI.
DEEPOTUS_TOTAL_SUPPLY = 1_000_000_000

# Trigger keys (kept in this module so the dashboard can introspect them
# alongside the v1 trigger registry without importing the engine).
TRIGGER_DAILY = "cadence_daily"
TRIGGER_HOLDER = "cadence_holder"
TRIGGER_MARKETCAP = "cadence_marketcap"
TRIGGER_WHALE = "cadence_whale"


# =====================================================================
# Helpers — pure utilities, easy to unit-test
# =====================================================================
def parse_hhmm(s: str) -> Optional[Tuple[int, int]]:
    """Parse "HH:MM" → (h, m). Return None on malformed input."""
    if not isinstance(s, str) or len(s) != 5 or s[2] != ":":
        return None
    try:
        h, m = int(s[0:2]), int(s[3:5])
    except ValueError:
        return None
    if 0 <= h < 24 and 0 <= m < 60:
        return (h, m)
    return None


def is_in_quiet_hours(now_utc: datetime, qh: Dict[str, Any]) -> bool:
    """Return True when ``now_utc`` falls inside the configured window.

    Window may wrap past midnight (e.g. 23:00 → 06:00 means the window
    spans the last hour of day N and the first six hours of day N+1).
    """
    if not qh or not qh.get("enabled"):
        return False
    start = parse_hhmm(qh.get("start_utc") or "")
    end = parse_hhmm(qh.get("end_utc") or "")
    if start is None or end is None:
        return False
    now_min = now_utc.hour * 60 + now_utc.minute
    start_min = start[0] * 60 + start[1]
    end_min = end[0] * 60 + end[1]
    if start_min == end_min:
        return False  # zero-length window — treat as disabled
    if start_min < end_min:
        # Same-day window
        return start_min <= now_min < end_min
    # Wraps midnight: silent if now ≥ start OR now < end
    return now_min >= start_min or now_min < end_min


def pick_archetype(allowed: List[str]) -> str:
    """Return a V2 template id, weighted-random over `allowed` (or all)."""
    pool = (
        [t for t in allowed if t in PROMPT_TEMPLATES_V2]
        if allowed
        else list(PROMPT_TEMPLATES_V2.keys())
    )
    if not pool:
        # Either empty allowed-list resolved to empty pool, OR all the
        # allowed ids were typo'd — fall back to the full set.
        pool = list(PROMPT_TEMPLATES_V2.keys())
    weights = [int(PROMPT_TEMPLATES_V2[k]["weight"]) for k in pool]
    return random.choices(pool, weights=weights, k=1)[0]


def format_mc_label(amount: int) -> str:
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M".replace(".0M", "M")
    if amount >= 1_000:
        return f"${amount // 1000}k"
    return f"${amount}"


# =====================================================================
# Persistence helpers — read/write `cadence._state` on the singleton
# =====================================================================
async def _read_cadence_state() -> Dict[str, Any]:
    """Return the persisted cadence._state sub-document (always non-None)."""
    cfg = await get_bot_config()
    state = ((cfg.get("cadence") or {}).get("_state")) or {}
    state.setdefault("last_fired_today", {"x": {}, "telegram": {}})
    state.setdefault("fired_milestones", {"holders": [], "marketcap_usd": []})
    return state


async def _persist_state_patch(dot_path_value: Dict[str, Any]) -> None:
    """Persist a `$set` patch using dotted Mongo paths.

    Example: ``{"cadence._state.last_fired_today.x.08:30": "2026-05-03"}``.
    """
    if not dot_path_value:
        return
    await db[CONFIG_COLLECTION].update_one(
        {"_id": CONFIG_SINGLETON_ID},
        {"$set": dot_path_value},
        upsert=True,
    )


# =====================================================================
# Market snapshot — best-effort holders + computed marketcap
# =====================================================================
async def _read_market_snapshot() -> Dict[str, Any]:
    """Best-effort snapshot of the live market.

    Currently sources:
      - `vault_state.dex_last_price_usd` for the latest spot price.
      - `marketcap_usd = price × DEEPOTUS_TOTAL_SUPPLY` (1B circulating).
      - `holders` is left ``None`` until we wire a dedicated source
        (DexScreener `/tokens/{addr}` is the natural candidate; not
        plumbed yet so we no-op the holder-milestone branch when None).

    Never raises — failures degrade to an empty snapshot so the cadence
    tick stays harmless during transient DB hiccups.
    """
    snapshot: Dict[str, Any] = {
        "price_usd": None,
        "marketcap_usd": None,
        "holders": None,
    }
    try:
        # `VAULT_DOC_ID` is "protocol_delta_sigma" in vault.py — keep this
        # in sync if the singleton ID ever changes.
        doc = await db.vault_state.find_one({"_id": "protocol_delta_sigma"})
    except Exception:  # noqa: BLE001
        logger.exception("[cadence] vault_state read failed")
        return snapshot
    if not doc:
        return snapshot

    price = doc.get("dex_last_price_usd")
    if price is not None:
        try:
            price_f = float(price)
            snapshot["price_usd"] = price_f
            snapshot["marketcap_usd"] = price_f * DEEPOTUS_TOTAL_SUPPLY
        except (TypeError, ValueError):
            pass

    # Holders — placeholder hook. Replace with DexScreener / Helius RPC
    # call when we wire the dedicated polling source. For now we read
    # from `vault_state.dex_holders_count` if a future patch ever
    # populates it.
    holders = doc.get("dex_holders_count")
    if holders is not None:
        try:
            snapshot["holders"] = int(holders)
        except (TypeError, ValueError):
            pass

    return snapshot


# =====================================================================
# Core post-firing helper — one place that converts a (platform, ctx)
# tuple into a queued V2 post.
# =====================================================================
async def _fire_v2_post(
    *,
    trigger_key: str,
    platform: str,
    archetype: Optional[str],
    extra_context: Optional[str],
    payload_extras: Dict[str, Any],
    idempotency_key: str,
) -> Optional[Dict[str, Any]]:
    """Generate a V2 post and queue it for dispatch.

    Returns the queue document, or None when generation failed (an
    error log is emitted but the tick keeps running).
    """
    try:
        post = await generate_post_v2(
            platform=platform,
            force_template=archetype,
            extra_context=extra_context,
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "[cadence] generate_post_v2 failed trigger=%s plat=%s arch=%s",
            trigger_key,
            platform,
            archetype,
        )
        return None

    rendered = post["content_en"]
    payload = {
        "template_id": post.get("template_used"),
        "template_label": post.get("template_label"),
        "content_fr": post.get("content_fr"),
        "content_en": post.get("content_en"),
        "hashtags": list(post.get("hashtags") or []),
        "primary_emoji": post.get("primary_emoji") or "",
        **payload_extras,
    }
    try:
        item = await queue_propose(
            trigger_key=trigger_key,
            template_id=post.get("template_used"),
            rendered_content=rendered,
            platforms=[platform],
            payload=payload,
            policy="auto",  # cadence posts auto-approve
            idempotency_key=idempotency_key,
            delay_seconds=10,
            manual=False,
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "[cadence] queue_propose failed trigger=%s plat=%s",
            trigger_key,
            platform,
        )
        return None

    logger.info(
        "[cadence] fired trigger=%s plat=%s template=%s queue_id=%s",
        trigger_key,
        platform,
        post.get("template_used"),
        item.get("id"),
    )
    return item


# =====================================================================
# Tick — daily schedule
# =====================================================================
async def cadence_daily_tick(now_utc: Optional[datetime] = None) -> Dict[str, Any]:
    """Process the daily schedule once. Designed to run every minute.

    Skipped silently when:
      - the kill-switch is on,
      - quiet hours are active,
      - no platform schedule is enabled.

    Returns a small summary dict for logging / dashboard observability.
    """
    now = now_utc or datetime.now(timezone.utc)
    cfg = await get_bot_config()
    if cfg.get("kill_switch_active"):
        return {"status": "skipped", "reason": "kill_switch"}

    cadence = cfg.get("cadence") or {}
    if is_in_quiet_hours(now, cadence.get("quiet_hours") or {}):
        return {"status": "skipped", "reason": "quiet_hours"}

    daily = cadence.get("daily_schedule") or {}
    state = await _read_cadence_state()
    fired_today = state.get("last_fired_today") or {"x": {}, "telegram": {}}

    today_iso = now.date().isoformat()
    cur_hhmm = f"{now.hour:02d}:{now.minute:02d}"
    fired_summary: List[Dict[str, Any]] = []
    persist_patch: Dict[str, Any] = {}

    for plat in ("x", "telegram"):
        entry = daily.get(plat) or {}
        if not entry.get("enabled"):
            continue
        slots = list(entry.get("post_times_utc") or [])
        if cur_hhmm not in slots:
            continue
        # Per-day dedup
        last = (fired_today.get(plat) or {}).get(cur_hhmm)
        if last == today_iso:
            continue

        archetype = pick_archetype(list(entry.get("archetypes") or []))
        item = await _fire_v2_post(
            trigger_key=TRIGGER_DAILY,
            platform=plat,
            archetype=archetype,
            extra_context=None,
            payload_extras={
                "slot_utc": cur_hhmm,
                "scheduled_for_date": today_iso,
            },
            idempotency_key=f"daily:{plat}:{today_iso}:{cur_hhmm}",
        )
        if item:
            persist_patch[
                f"cadence._state.last_fired_today.{plat}.{cur_hhmm}"
            ] = today_iso
            fired_summary.append(
                {
                    "platform": plat,
                    "slot": cur_hhmm,
                    "archetype": archetype,
                    "queue_id": item.get("id"),
                },
            )

    if persist_patch:
        await _persist_state_patch(persist_patch)

    return {
        "status": "ok",
        "now_utc": now.isoformat(),
        "fired": fired_summary,
    }


# =====================================================================
# Tick — reactive milestones (holders + marketcap)
# =====================================================================
async def cadence_reactive_tick(
    now_utc: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Process holder + marketcap milestones once.

    Designed to share the minute tick with `cadence_daily_tick`. Skipped
    silently when kill-switch is on, quiet hours are active, or
    `reactive_triggers.enabled` is false.
    """
    now = now_utc or datetime.now(timezone.utc)
    cfg = await get_bot_config()
    if cfg.get("kill_switch_active"):
        return {"status": "skipped", "reason": "kill_switch"}

    cadence = cfg.get("cadence") or {}
    rt = cadence.get("reactive_triggers") or {}
    if not rt.get("enabled"):
        return {"status": "skipped", "reason": "disabled"}
    if is_in_quiet_hours(now, cadence.get("quiet_hours") or {}):
        return {"status": "skipped", "reason": "quiet_hours"}

    snapshot = await _read_market_snapshot()
    state = await _read_cadence_state()
    fired = state.get("fired_milestones") or {}
    fired_h = set(int(x) for x in (fired.get("holders") or []))
    fired_m = set(int(x) for x in (fired.get("marketcap_usd") or []))

    # ---- Marketcap milestones ----
    fired_summary: List[Dict[str, Any]] = []
    persist_patch: Dict[str, Any] = {}

    mc = snapshot.get("marketcap_usd")
    if mc is not None:
        target_tiers = sorted(
            int(t) for t in (rt.get("marketcap_milestones_usd") or []) if t > 0
        )
        crossed = [t for t in target_tiers if t <= mc and t not in fired_m]
        if crossed:
            top = max(crossed)
            ctx = (
                f"Marketcap just crossed {format_mc_label(top)}. The Cabinet "
                f"observes this milestone — reflect that gravity in your "
                f"prophecy without quoting the exact number verbatim."
            )
            # Default to X here; the platform fan-out is intentionally
            # narrow to keep cadence posts predictable. Tg can be added
            # by simply duplicating this block once we want it.
            item = await _fire_v2_post(
                trigger_key=TRIGGER_MARKETCAP,
                platform="x",
                archetype="prophecy",  # MC milestone → solemn prophecy
                extra_context=ctx,
                payload_extras={
                    "mc_usd": int(mc),
                    "mc_milestone": top,
                    "mc_label": format_mc_label(top),
                },
                idempotency_key=f"mc:{top}",
            )
            if item:
                fired_m.add(top)
                persist_patch["cadence._state.fired_milestones.marketcap_usd"] = sorted(
                    fired_m,
                )
                fired_summary.append(
                    {
                        "kind": "marketcap",
                        "milestone": top,
                        "queue_id": item.get("id"),
                    },
                )

    # ---- Holder milestones ----
    holders = snapshot.get("holders")
    if holders is not None:
        target_h = sorted(
            int(t) for t in (rt.get("holder_milestones") or []) if t > 0
        )
        crossed_h = [t for t in target_h if t <= holders and t not in fired_h]
        if crossed_h:
            top = max(crossed_h)
            ctx = (
                f"The faithful crowd just passed {top:,} holders. The "
                f"Cabinet records this expansion — frame it as inevitable, "
                f"never as a prediction of price."
            )
            item = await _fire_v2_post(
                trigger_key=TRIGGER_HOLDER,
                platform="x",
                archetype="stats",  # holder count → fits the stats archetype
                extra_context=ctx,
                payload_extras={
                    "holders": int(holders),
                    "holder_milestone": top,
                },
                idempotency_key=f"holders:{top}",
            )
            if item:
                fired_h.add(top)
                persist_patch["cadence._state.fired_milestones.holders"] = sorted(
                    fired_h,
                )
                fired_summary.append(
                    {
                        "kind": "holders",
                        "milestone": top,
                        "queue_id": item.get("id"),
                    },
                )

    if persist_patch:
        await _persist_state_patch(persist_patch)

    return {
        "status": "ok",
        "now_utc": now.isoformat(),
        "snapshot": {
            "marketcap_usd": snapshot.get("marketcap_usd"),
            "holders": snapshot.get("holders"),
        },
        "fired": fired_summary,
    }


# =====================================================================
# Whale buy reactive — invoked synchronously from whale_watcher
# =====================================================================
async def cadence_whale_react(
    *,
    sol_amount: float,
    tx_signature: Optional[str],
    wallet: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Generate a V2 post when a whale buy passes the cadence threshold.

    Designed to be called from ``core.whale_watcher.process_pending_alerts``
    after the v1 propaganda enqueue. Idempotent on tx_signature so the
    same whale is never amplified twice.

    Returns the queue document on fire, or None when:
      - cadence.reactive_triggers is disabled,
      - sol_amount < whale_buy_min_sol,
      - kill-switch is on / quiet-hours are active,
      - LLM generation failed.
    """
    if sol_amount is None or sol_amount <= 0:
        return None

    cfg = await get_bot_config()
    if cfg.get("kill_switch_active"):
        return None

    cadence = cfg.get("cadence") or {}
    rt = cadence.get("reactive_triggers") or {}
    if not rt.get("enabled"):
        return None

    threshold = float(rt.get("whale_buy_min_sol") or 0)
    if threshold <= 0 or sol_amount < threshold:
        return None

    now = datetime.now(timezone.utc)
    if is_in_quiet_hours(now, cadence.get("quiet_hours") or {}):
        return None

    ctx_bits = [
        f"A single wallet just bought {sol_amount:.2f} SOL of $DEEPOTUS — "
        f"that's the kind of footprint the Cabinet logs in red ink."
    ]
    if wallet:
        ctx_bits.append(
            f"Wallet (truncated): {wallet[:6]}…{wallet[-4:]}",
        )
    extra_context = " ".join(ctx_bits)

    idem = f"whale:{tx_signature or 'no-tx'}:{int(now.timestamp() // 60)}"
    return await _fire_v2_post(
        trigger_key=TRIGGER_WHALE,
        platform="x",
        archetype="satire_news",  # whale → cynical commentary fits best
        extra_context=extra_context,
        payload_extras={
            "sol_amount": float(sol_amount),
            "tx_signature": tx_signature,
            "wallet": wallet,
        },
        idempotency_key=idem,
    )


# =====================================================================
# Single combined tick — used by the scheduler
# =====================================================================
async def cadence_combined_tick() -> Dict[str, Any]:
    """One-shot helper that runs both daily + reactive ticks back-to-back.

    Wrapped in defensive try/except so a failure on one branch never
    silences the other. Designed to be the body of an APScheduler job.
    """
    now = datetime.now(timezone.utc)
    daily_res: Dict[str, Any] = {"status": "skipped", "reason": "exception"}
    reactive_res: Dict[str, Any] = {"status": "skipped", "reason": "exception"}
    try:
        daily_res = await cadence_daily_tick(now_utc=now)
    except Exception:  # noqa: BLE001
        logger.exception("[cadence] daily tick crashed")
    try:
        reactive_res = await cadence_reactive_tick(now_utc=now)
    except Exception:  # noqa: BLE001
        logger.exception("[cadence] reactive tick crashed")
    return {
        "ran_at": now.isoformat(),
        "daily": daily_res,
        "reactive": reactive_res,
    }
