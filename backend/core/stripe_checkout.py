"""Stripe Checkout integration (Sprint 20 — Ecosystem & Payment).

Wrapper around the Stripe Checkout API, accessed through
``core.stripe_checkout_compat`` (Mode A: emergentintegrations proxy when
available; Mode B: native ``stripe`` SDK fallback for non-Emergent hosts).

All business logic for creating sessions, fetching status and handling
webhooks lives here so routers stay thin. The module ALSO owns the
``payment_transactions`` collection — its single source of truth for
any payment lifecycle event.

Key design rules (per the Emergent Stripe integration playbook):

  * **Never trust client-supplied prices.** The PRODUCT_CATALOG below is
    the only source of truth. Frontend submits a ``product_id`` (and
    optionally an originating URL for success/cancel redirects); the
    backend computes the amount.
  * **Idempotency.** Every Stripe ``checkout.session.completed`` webhook
    is keyed by ``event_id`` and ``session_id`` so duplicate calls do
    not double-credit anything. We deliberately reject re-processing
    by checking the existing ``payment_status`` before mutating order
    state.
  * **Atomic founder numbering.** Board-game pricing tiers depend on a
    server-side counter (1–500 = Founder edition with three sub-tiers).
    The counter is reserved BEFORE the Stripe session is created using
    Mongo ``$inc`` so two simultaneous buyers cannot grab the same
    number. Reservations are released if Stripe returns an error
    before redirect or the session expires.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from core.stripe_checkout_compat import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CheckoutStatusResponse,
    StripeCheckout,
)

from core.config import STRIPE_API_KEY, db, logger

_log = logger if logger else logging.getLogger("deepotus.stripe")

# ---------------------------------------------------------------------
# Product catalogue (server-side source of truth)
# ---------------------------------------------------------------------
# Amounts are EUR floats (Stripe wants float, NOT int per playbook).
# `boardgame` price is dynamic—resolved via tier function below.
PRODUCT_CATALOG: Dict[str, Dict[str, Any]] = {
    "videogen": {
        "label": "DEEPOTUS Video Generator (one-time license)",
        "amount_eur": 65.00,
        "currency": "eur",
        "requires_shipping": False,
        "deliverable": "software_license",
    },
    "boardgame": {
        "label": "DEEPOTUS — FRAGMENTS (board game, founder edition)",
        "amount_eur": None,  # computed via tier resolver
        "currency": "eur",
        "requires_shipping": True,
        "deliverable": "physical_boardgame",
    },
}

# Board-game tier ladder (1-indexed, inclusive ranges).
BOARDGAME_TIERS: List[Tuple[int, int, float, str]] = [
    (1, 100, 39.99, "early_bird_1"),
    (101, 200, 45.00, "early_bird_2"),
    (201, 500, 59.00, "standard_founder"),
    (501, 10_000_000, 59.00, "standard"),
]

FOUNDER_LIMIT = 500


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def boardgame_tier_for(counter_value: int) -> Tuple[float, str]:
    """Resolve the unit price + tier label for a given counter value.

    Counter is the 1-indexed *order number* (i.e. the n-th boardgame ever
    sold, or n-th reserved). Falls back to the last tier defensively.
    """
    for start, end, price, tier in BOARDGAME_TIERS:
        if start <= counter_value <= end:
            return price, tier
    # Fallback (unreachable in practice because last tier ceiling is huge)
    return BOARDGAME_TIERS[-1][2], BOARDGAME_TIERS[-1][3]


async def get_boardgame_counter_snapshot() -> Dict[str, Any]:
    """Return public-safe counter info (sold so far, next number, tier).

    Used by /api/ecosystem/board-game/counter for the live UI badge.
    """
    doc = await db.counters.find_one({"_id": "boardgame_orders"}) or {"value": 0}
    sold = int(doc.get("value", 0))
    next_number = sold + 1
    price_eur, tier = boardgame_tier_for(next_number)
    return {
        "sold": sold,
        "next_number": next_number,
        "founder_limit": FOUNDER_LIMIT,
        "is_founder": next_number <= FOUNDER_LIMIT,
        "current_price_eur": price_eur,
        "current_tier": tier,
    }


async def reserve_boardgame_number() -> Tuple[int, float, str]:
    """Atomically increment the counter and return (number, price, tier).

    This is called BEFORE creating a Stripe session. If the Stripe call
    fails, the reservation stays—which is fine because each next buyer
    just gets the following number. We don't compact gaps; the goal is
    fairness and atomicity, not zero-gap numbering.
    """
    res = await db.counters.find_one_and_update(
        {"_id": "boardgame_orders"},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=True,
    )
    # Motor returns the document AFTER the update when return_document=True
    if res is None:
        # Defensive—re-read
        doc = await db.counters.find_one({"_id": "boardgame_orders"}) or {"value": 1}
        new_value = int(doc.get("value", 1))
    else:
        new_value = int(res.get("value", 1))
    price, tier = boardgame_tier_for(new_value)
    _log.info("[stripe] reserved boardgame #%d (tier=%s, price=%.2f€)", new_value, tier, price)
    return new_value, price, tier


# ---------------------------------------------------------------------
# Stripe wrapper factory
# ---------------------------------------------------------------------
def _make_checkout(webhook_url: str) -> StripeCheckout:
    if not STRIPE_API_KEY:
        raise RuntimeError(
            "STRIPE_API_KEY is missing from environment. Add it to backend/.env."
        )
    return StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)


# ---------------------------------------------------------------------
# payment_transactions DB helpers
# ---------------------------------------------------------------------
async def ensure_indexes() -> None:
    """Idempotent index setup. Called at startup."""
    await db.payment_transactions.create_index("session_id", unique=True)
    await db.payment_transactions.create_index("created_at")
    await db.payment_transactions.create_index("payment_status")
    await db.orders.create_index("stripe_session_id", unique=True, sparse=True)
    await db.orders.create_index("founder_number", sparse=True)
    await db.orders.create_index("customer.email")
    await db.orders.create_index("created_at")
    await db.counters.create_index("_id")  # always exists; harmless
    _log.info("[stripe] payment_transactions / orders indexes ready")


async def record_transaction_initiated(
    *,
    session_id: str,
    amount_eur: float,
    currency: str,
    metadata: Dict[str, str],
) -> Dict[str, Any]:
    """Persist a freshly-created session as ``initiated`` BEFORE the user
    redirects. Required by the playbook so we never lose track of a
    pending payment.
    """
    now = _now_utc()
    doc = {
        "_id": str(uuid.uuid4()),
        "session_id": session_id,
        "amount": float(amount_eur),
        "currency": currency,
        "metadata": dict(metadata or {}),
        "status": "open",
        "payment_status": "initiated",
        "created_at": now,
        "updated_at": now,
        "history": [{"at": now, "event": "initiated", "source": "create_session"}],
    }
    await db.payment_transactions.insert_one(doc)
    return doc


async def update_transaction_status(
    *,
    session_id: str,
    status: str,
    payment_status: str,
    metadata: Optional[Dict[str, str]] = None,
    source: str = "poll",
) -> Optional[Dict[str, Any]]:
    """Update the transaction state. Returns the previous payment_status
    so callers can decide whether to trigger fulfilment exactly once.
    """
    now = _now_utc()
    update: Dict[str, Any] = {
        "$set": {
            "status": status,
            "payment_status": payment_status,
            "updated_at": now,
        },
        "$push": {
            "history": {"at": now, "event": payment_status, "source": source},
        },
    }
    if metadata:
        update["$set"]["metadata"] = metadata
    res = await db.payment_transactions.find_one_and_update(
        {"session_id": session_id},
        update,
        return_document=False,  # return PREVIOUS doc so we can detect transitions
    )
    return res


async def get_transaction(session_id: str) -> Optional[Dict[str, Any]]:
    return await db.payment_transactions.find_one({"session_id": session_id})


# ---------------------------------------------------------------------
# High-level operations used by routers
# ---------------------------------------------------------------------
async def create_session_for_product(
    *,
    product_id: str,
    origin_url: str,
    webhook_url: str,
    locale: str = "fr",
    extra_metadata: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Create a Stripe Checkout Session for a known product.

    Returns a dict ``{url, session_id, amount, currency, metadata}``
    suitable for the frontend, and records a `payment_transactions`
    row in the ``initiated`` state.

    For ``boardgame`` we reserve a founder number BEFORE calling
    Stripe so the tier price is locked-in.
    """
    if product_id not in PRODUCT_CATALOG:
        raise ValueError(f"Unknown product_id={product_id!r}")
    spec = PRODUCT_CATALOG[product_id]
    metadata: Dict[str, str] = {
        "order_type": product_id,
        "locale": locale,
        "source": "web_checkout",
        "created_at": _now_utc().isoformat(),
    }
    if extra_metadata:
        metadata.update({k: str(v) for k, v in extra_metadata.items() if v is not None})

    if product_id == "boardgame":
        founder_number, unit_price, tier = await reserve_boardgame_number()
        metadata["founder_number"] = str(founder_number)
        metadata["founder_tier"] = tier
        metadata["is_founder"] = "1" if founder_number <= FOUNDER_LIMIT else "0"
        amount_eur = float(unit_price)
    else:
        amount_eur = float(spec["amount_eur"])

    currency = spec["currency"]

    # Build success / cancel URLs from caller-provided origin
    origin_url = origin_url.rstrip("/")
    success_url = f"{origin_url}/paiement?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/paiement?canceled=1"

    stripe_checkout = _make_checkout(webhook_url)
    req = CheckoutSessionRequest(
        amount=amount_eur,
        currency=currency,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata,
    )
    t0 = time.time()
    session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(req)
    _log.info(
        "[stripe] session created product=%s amount=%.2f%s session_id=%s in %dms",
        product_id,
        amount_eur,
        currency.upper(),
        session.session_id[:14] + "…",
        int((time.time() - t0) * 1000),
    )

    await record_transaction_initiated(
        session_id=session.session_id,
        amount_eur=amount_eur,
        currency=currency,
        metadata=metadata,
    )

    return {
        "url": session.url,
        "session_id": session.session_id,
        "amount_eur": amount_eur,
        "currency": currency,
        "metadata": metadata,
    }


async def fetch_session_status(
    session_id: str, *, webhook_url: str
) -> CheckoutStatusResponse:
    """Wrap StripeCheckout.get_checkout_status with our webhook URL."""
    sc = _make_checkout(webhook_url)
    return await sc.get_checkout_status(session_id)


async def parse_webhook(
    *, body: bytes, signature: str, webhook_url: str
) -> Any:
    """Delegate to StripeCheckout.handle_webhook.

    The library returns a WebhookEventResponse with fields:
    event_type, event_id, session_id, payment_status, metadata.
    """
    sc = _make_checkout(webhook_url)
    return await sc.handle_webhook(body, signature)


__all__ = [
    "PRODUCT_CATALOG",
    "BOARDGAME_TIERS",
    "FOUNDER_LIMIT",
    "boardgame_tier_for",
    "get_boardgame_counter_snapshot",
    "reserve_boardgame_number",
    "ensure_indexes",
    "record_transaction_initiated",
    "update_transaction_status",
    "get_transaction",
    "create_session_for_product",
    "fetch_session_status",
    "parse_webhook",
]
