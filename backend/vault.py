"""
PROTOCOL ΔΣ — Vault mechanics for $DEEPOTUS.

A 6-digit classified combination vault. The TARGET combination lives server-side,
never exposed to the client. Each `crack event` (purchase of 1,000 $DEEPOTUS)
advances one unlocked dial toward its target digit. When all 6 digits are locked,
the vault reaches the `declassified` stage and the /operation reveal unlocks.

Mechanics (deterministic):
  - target_combination : List[int] of 6 digits, random on first init
  - digits_locked      : int, 0..6 — first N dials are frozen on their target
  - current_combination: List[int] of 6 — locked dials show target[i]; unlocked
                          dials display pseudo-randomized spinning values
  - tokens_sold        : total $DEEPOTUS "moved" into the vault so far (mock for now;
                          later: replace with on-chain worker)
  - tokens_per_digit   : threshold of tokens to lock one additional dial (default 1,000)
                          6 digits × 1,000 → 6,000 tokens to fully crack (DEMO values,
                          admin-configurable).
  - stage              : computed from digits_locked: 0-1 LOCKED, 2-4 CRACKING,
                          5 UNLOCKING, 6 DECLASSIFIED

Auto-tick strategy (hybrid):
  - Every purchase (admin/crack endpoint or real Solana worker later) advances the vault
  - Additionally, a background coroutine runs hourly and performs +1 synthetic tick to
    keep the site feeling alive even before real on-chain activity begins
  - Both ticks create public `vault_events` entries (used for the activity feed)
"""

from __future__ import annotations

import asyncio
import logging
import random
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------
# Constants / Config
# ---------------------------------------------------------------------
VAULT_DOC_ID = "protocol_delta_sigma"
DEFAULT_TOKENS_PER_DIGIT = 1_000  # tokens that must flow to lock ONE additional dial
DEFAULT_NUM_DIGITS = 6
HOURLY_TICK_SECONDS = 3600  # 1h

# Stages
STAGE_LOCKED = "LOCKED"
STAGE_CRACKING = "CRACKING"
STAGE_UNLOCKING = "UNLOCKING"
STAGE_DECLASSIFIED = "DECLASSIFIED"

# Symbolic "agent codes" used in the public activity feed
AGENT_PREFIXES = ["OMEGA", "DELTA", "SIGMA", "KAPPA", "ZETA", "THETA", "RHO", "TAU"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compute_stage(digits_locked: int, num_digits: int) -> str:
    if digits_locked >= num_digits:
        return STAGE_DECLASSIFIED
    # Integer-based thresholds (avoids fraction traps on 6 dials)
    # 0-2 locked → LOCKED, 3-4 → CRACKING, 5 → UNLOCKING, 6 → DECLASSIFIED
    if digits_locked <= 2:
        return STAGE_LOCKED
    if digits_locked <= 4:
        return STAGE_CRACKING
    return STAGE_UNLOCKING


def _fake_agent_code() -> str:
    prefix = random.choice(AGENT_PREFIXES)
    num = random.randint(10, 9999)
    return f"{prefix}-{num:04d}"


def _render_current_combination(
    target: List[int], digits_locked: int
) -> List[int]:
    """Locked dials show target digit; unlocked dials show a random 0-9."""
    return [
        target[i] if i < digits_locked else random.randint(0, 9)
        for i in range(len(target))
    ]


# ---------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------
class VaultEvent(BaseModel):
    id: str
    kind: str  # "purchase" | "hourly_tick" | "admin_crack" | "reset"
    tokens_added: int
    digits_locked_before: int
    digits_locked_after: int
    agent_code: str
    created_at: str
    note: Optional[str] = None


class VaultStateResponse(BaseModel):
    # Public state — NEVER expose the target combination
    code_name: str = "PROTOCOL ΔΣ"
    stage: str
    num_digits: int
    digits_locked: int
    current_combination: List[int]  # display layer (locked=target, unlocked=random)
    tokens_per_digit: int
    tokens_sold: int
    # Redacted metrics (displayed as textures, no absolute goal exposed)
    progress_pct: float  # 0..100
    hourly_tick_enabled: bool
    last_hourly_tick_at: Optional[str] = None
    last_event_at: Optional[str] = None
    updated_at: str
    recent_events: List[VaultEvent] = Field(default_factory=list)
    # DEX public status (non-sensitive; just advertises live-feed source)
    dex_mode: str = "off"           # off | demo | custom
    dex_label: Optional[str] = None # e.g. "BONK · raydium"
    dex_pair_symbol: Optional[str] = None


class VaultAdminStateResponse(VaultStateResponse):
    # Admin-only extension that reveals the classified combination + DEX details
    target_combination: List[int]
    dex_token_address: Optional[str] = None
    dex_demo_token_address: Optional[str] = None
    dex_last_poll_at: Optional[str] = None
    dex_last_h24_buys: Optional[int] = None
    dex_last_h24_sells: Optional[int] = None
    dex_last_h24_volume_usd: Optional[float] = None
    dex_last_price_usd: Optional[float] = None
    dex_carry_tokens: Optional[float] = None
    dex_error: Optional[str] = None


class VaultCrackRequest(BaseModel):
    tokens: int = Field(..., gt=0, le=10_000_000)
    note: Optional[str] = None
    agent_code: Optional[str] = None


class VaultConfigUpdate(BaseModel):
    tokens_per_digit: Optional[int] = Field(None, gt=0, le=1_000_000)
    hourly_tick_enabled: Optional[bool] = None
    reset: Optional[bool] = False  # if true: wipe progress + re-roll target


# ---------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------
async def initialize_vault(db) -> Dict[str, Any]:
    """Create the vault doc on first boot."""
    doc = await db.vault_state.find_one({"_id": VAULT_DOC_ID})
    if doc:
        return doc
    target = [random.randint(0, 9) for _ in range(DEFAULT_NUM_DIGITS)]
    now = _now_iso()
    doc = {
        "_id": VAULT_DOC_ID,
        "code_name": "PROTOCOL ΔΣ",
        "num_digits": DEFAULT_NUM_DIGITS,
        "tokens_per_digit": DEFAULT_TOKENS_PER_DIGIT,
        "target_combination": target,
        "digits_locked": 0,
        "tokens_sold": 0,
        "hourly_tick_enabled": True,
        "last_hourly_tick_at": None,
        "last_event_at": None,
        "created_at": now,
        "updated_at": now,
    }
    await db.vault_state.insert_one(doc)
    logging.info(
        "[vault] initialized PROTOCOL ΔΣ — classified combination locked in DB."
    )
    return doc


async def _persist(db, doc: Dict[str, Any]) -> None:
    doc["updated_at"] = _now_iso()
    await db.vault_state.update_one(
        {"_id": VAULT_DOC_ID}, {"$set": doc}, upsert=True
    )


async def _log_event(
    db,
    *,
    kind: str,
    tokens_added: int,
    before: int,
    after: int,
    agent_code: str,
    note: Optional[str] = None,
) -> Dict[str, Any]:
    ev = {
        "_id": str(uuid.uuid4()),
        "kind": kind,
        "tokens_added": tokens_added,
        "digits_locked_before": before,
        "digits_locked_after": after,
        "agent_code": agent_code,
        "created_at": _now_iso(),
        "note": note,
    }
    await db.vault_events.insert_one(ev)
    return ev


async def _fetch_recent_events(db, limit: int = 25) -> List[Dict[str, Any]]:
    cursor = db.vault_events.find({}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


def _ev_to_pydantic(ev: Dict[str, Any]) -> VaultEvent:
    return VaultEvent(
        id=str(ev.get("_id", "")),
        kind=ev.get("kind", "unknown"),
        tokens_added=int(ev.get("tokens_added", 0)),
        digits_locked_before=int(ev.get("digits_locked_before", 0)),
        digits_locked_after=int(ev.get("digits_locked_after", 0)),
        agent_code=ev.get("agent_code", "UNKNOWN-0000"),
        created_at=ev.get("created_at", ""),
        note=ev.get("note"),
    )


# ---------------------------------------------------------------------
# Public state view
# ---------------------------------------------------------------------
async def get_public_state(db) -> VaultStateResponse:
    doc = await initialize_vault(db)
    target = doc["target_combination"]
    digits_locked = int(doc.get("digits_locked", 0))
    num_digits = int(doc.get("num_digits", DEFAULT_NUM_DIGITS))
    tokens_per_digit = int(doc.get("tokens_per_digit", DEFAULT_TOKENS_PER_DIGIT))
    tokens_sold = int(doc.get("tokens_sold", 0))

    target_total = num_digits * tokens_per_digit
    progress_pct = min(100.0, (tokens_sold / target_total) * 100) if target_total else 0.0

    events = await _fetch_recent_events(db, limit=25)
    stage = _compute_stage(digits_locked, num_digits)
    current = _render_current_combination(target, digits_locked)

    return VaultStateResponse(
        code_name=doc.get("code_name", "PROTOCOL ΔΣ"),
        stage=stage,
        num_digits=num_digits,
        digits_locked=digits_locked,
        current_combination=current,
        tokens_per_digit=tokens_per_digit,
        tokens_sold=tokens_sold,
        progress_pct=round(progress_pct, 2),
        hourly_tick_enabled=bool(doc.get("hourly_tick_enabled", True)),
        last_hourly_tick_at=doc.get("last_hourly_tick_at"),
        last_event_at=doc.get("last_event_at"),
        updated_at=doc.get("updated_at", _now_iso()),
        recent_events=[_ev_to_pydantic(ev) for ev in events],
        dex_mode=(doc.get("dex_mode") or "off"),
        dex_label=doc.get("dex_label"),
        dex_pair_symbol=doc.get("dex_pair_symbol"),
    )


async def get_admin_state(db) -> VaultAdminStateResponse:
    base = await get_public_state(db)
    doc = await db.vault_state.find_one({"_id": VAULT_DOC_ID})
    target = list(doc["target_combination"]) if doc else []
    return VaultAdminStateResponse(
        **base.model_dump(),
        target_combination=target,
        dex_token_address=(doc or {}).get("dex_token_address"),
        dex_demo_token_address=(doc or {}).get("dex_demo_token_address"),
        dex_last_poll_at=(doc or {}).get("dex_last_poll_at"),
        dex_last_h24_buys=(doc or {}).get("dex_last_h24_buys"),
        dex_last_h24_sells=(doc or {}).get("dex_last_h24_sells"),
        dex_last_h24_volume_usd=(doc or {}).get("dex_last_h24_volume_usd"),
        dex_last_price_usd=(doc or {}).get("dex_last_price_usd"),
        dex_carry_tokens=(doc or {}).get("dex_carry_tokens"),
        dex_error=(doc or {}).get("dex_error"),
    )


class VaultDexConfigUpdate(BaseModel):
    mode: str  # "off" | "demo" | "custom"
    token_address: Optional[str] = None  # Solana mint address for custom mode


async def update_dex_config(db, cfg: VaultDexConfigUpdate) -> VaultAdminStateResponse:
    mode = (cfg.mode or "off").lower().strip()
    if mode not in ("off", "demo", "custom"):
        mode = "off"

    doc = await initialize_vault(db)
    updates: Dict[str, Any] = {"dex_mode": mode}

    if mode == "custom":
        addr = (cfg.token_address or "").strip()
        if addr:
            updates["dex_token_address"] = addr
    elif mode == "demo":
        # Ensure demo default exists
        from dexscreener import DEMO_TOKEN_ADDRESS  # lazy import to avoid circular
        if not doc.get("dex_demo_token_address"):
            updates["dex_demo_token_address"] = DEMO_TOKEN_ADDRESS

    # When switching mode, reset baselines so the next poll doesn't apply stale deltas
    updates.update(
        {
            "dex_last_h24_buys": 0,
            "dex_last_h24_sells": 0,
            "dex_last_h24_volume_usd": 0.0,
            "dex_last_price_usd": 0.0,
            "dex_carry_tokens": 0.0,
            "dex_last_poll_at": None,
            "dex_error": None,
        }
    )

    await db.vault_state.update_one(
        {"_id": VAULT_DOC_ID},
        {"$set": updates},
    )
    return await get_admin_state(db)


# ---------------------------------------------------------------------
# Core: apply a crack (advance digits based on tokens added)
# ---------------------------------------------------------------------
async def apply_crack(
    db,
    *,
    tokens: int,
    kind: str,
    agent_code: Optional[str] = None,
    note: Optional[str] = None,
) -> Tuple[VaultEvent, VaultStateResponse]:
    """Add `tokens` to the vault, advance dials if thresholds are crossed.
    Returns (event, new_public_state).
    """
    doc = await initialize_vault(db)
    before_locked = int(doc.get("digits_locked", 0))
    num_digits = int(doc.get("num_digits", DEFAULT_NUM_DIGITS))
    tokens_per_digit = int(doc.get("tokens_per_digit", DEFAULT_TOKENS_PER_DIGIT))

    if before_locked >= num_digits:
        # Already declassified — still log the event but no state changes
        ev = await _log_event(
            db,
            kind=kind,
            tokens_added=tokens,
            before=before_locked,
            after=before_locked,
            agent_code=agent_code or _fake_agent_code(),
            note=note or "already declassified",
        )
        return _ev_to_pydantic(ev), await get_public_state(db)

    new_tokens_sold = int(doc.get("tokens_sold", 0)) + int(tokens)
    target_digits_total = num_digits * tokens_per_digit
    # digits_locked advances as a floor of (tokens_sold / tokens_per_digit)
    new_locked = min(num_digits, new_tokens_sold // tokens_per_digit)

    doc["tokens_sold"] = min(new_tokens_sold, target_digits_total)
    doc["digits_locked"] = new_locked
    doc["last_event_at"] = _now_iso()
    await _persist(db, doc)

    ev = await _log_event(
        db,
        kind=kind,
        tokens_added=int(tokens),
        before=before_locked,
        after=new_locked,
        agent_code=agent_code or _fake_agent_code(),
        note=note,
    )
    new_state = await get_public_state(db)
    return _ev_to_pydantic(ev), new_state


# ---------------------------------------------------------------------
# Config / admin ops
# ---------------------------------------------------------------------
async def update_config(db, cfg: VaultConfigUpdate) -> VaultAdminStateResponse:
    doc = await initialize_vault(db)
    if cfg.tokens_per_digit is not None:
        doc["tokens_per_digit"] = int(cfg.tokens_per_digit)
    if cfg.hourly_tick_enabled is not None:
        doc["hourly_tick_enabled"] = bool(cfg.hourly_tick_enabled)
    if cfg.reset:
        doc["target_combination"] = [
            random.randint(0, 9) for _ in range(int(doc.get("num_digits", DEFAULT_NUM_DIGITS)))
        ]
        doc["digits_locked"] = 0
        doc["tokens_sold"] = 0
        doc["last_event_at"] = _now_iso()
        await db.vault_events.insert_one(
            {
                "_id": str(uuid.uuid4()),
                "kind": "reset",
                "tokens_added": 0,
                "digits_locked_before": 0,
                "digits_locked_after": 0,
                "agent_code": "SYSTEM-0000",
                "note": "Vault reset by admin — new classified combination generated.",
                "created_at": _now_iso(),
            }
        )
        logging.info("[vault] RESET — new classified combination rolled.")
    await _persist(db, doc)
    return await get_admin_state(db)


# ---------------------------------------------------------------------
# Hourly auto-tick (background task)
# ---------------------------------------------------------------------
async def hourly_tick_loop(db):
    """Long-running asyncio coroutine. Performs one synthetic tick per hour when enabled.
    Also survives restarts: checks time since last_hourly_tick_at on boot."""
    logging.info("[vault] hourly_tick_loop started")
    # First-time boot delay: 30s so we don't race server startup
    await asyncio.sleep(30)
    while True:
        try:
            doc = await initialize_vault(db)
            enabled = bool(doc.get("hourly_tick_enabled", True))
            last = doc.get("last_hourly_tick_at")
            digits_locked = int(doc.get("digits_locked", 0))
            num_digits = int(doc.get("num_digits", DEFAULT_NUM_DIGITS))

            should_tick = False
            if enabled and digits_locked < num_digits:
                if not last:
                    should_tick = True
                else:
                    try:
                        last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
                        delta = (datetime.now(timezone.utc) - last_dt).total_seconds()
                        if delta >= HOURLY_TICK_SECONDS:
                            should_tick = True
                    except Exception:
                        should_tick = True

            if should_tick:
                # Inject a small token bump (randomized within the dial threshold so the
                # dial doesn't always fully lock in one go, only sometimes does).
                tokens_per_digit = int(doc.get("tokens_per_digit", DEFAULT_TOKENS_PER_DIGIT))
                # 40–110% of one dial per tick → occasionally locks a dial
                bump = random.randint(
                    int(tokens_per_digit * 0.4),
                    int(tokens_per_digit * 1.1),
                )
                await apply_crack(
                    db,
                    tokens=bump,
                    kind="hourly_tick",
                    agent_code=_fake_agent_code(),
                    note="Deep State auto-tick",
                )
                # Record last hourly tick
                doc = await db.vault_state.find_one({"_id": VAULT_DOC_ID})
                doc["last_hourly_tick_at"] = _now_iso()
                await _persist(db, doc)
                logging.info(f"[vault] hourly tick applied (+{bump} tokens)")
        except Exception:
            logging.exception("[vault] hourly_tick_loop error (will retry)")

        # Re-check every minute so a newly-enabled hourly toggle reacts quickly
        await asyncio.sleep(60)
