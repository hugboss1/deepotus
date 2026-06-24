"""Stripe Checkout compatibility shim.

Drop-in replacement for
``emergentintegrations.payments.stripe.checkout``.

Why this exists
---------------
Same rationale as :mod:`core.llm_compat` and
:mod:`core.openai_image_compat`: the Ecosystem/Payment feature was built
against the private ``emergentintegrations`` package, which is NOT
installable from the public PyPI index. When the backend is deployed
outside Emergent (Render, Fly, a plain VM…), ``pip install`` of that
package fails and the whole ``payments`` router crashes at import time.

This module preserves the exact public surface ``core.stripe_checkout``
relies on::

    from core.stripe_checkout_compat import (
        CheckoutSessionRequest, CheckoutSessionResponse,
        CheckoutStatusResponse, StripeCheckout,
    )

    sc = StripeCheckout(api_key=..., webhook_url=...)
    resp  = await sc.create_checkout_session(CheckoutSessionRequest(
        amount=39.99, currency="eur",
        success_url=..., cancel_url=..., metadata={...}))
    status = await sc.get_checkout_status(resp.session_id)
    event  = await sc.handle_webhook(body, signature)

Two routing modes (auto-detected at import time)
------------------------------------------------
**Mode A — Emergent proxy (preferred when available)**
    If ``emergentintegrations.payments.stripe.checkout`` is importable
    (Emergent preview/dev env where the package is pre-installed) we
    re-export the real classes verbatim. ``STRIPE_API_KEY`` then works
    exactly as before.

**Mode B — Native Stripe SDK fallback (host-agnostic)**
    If the import fails, we fall back to a hand-rolled implementation
    that calls the official ``stripe`` SDK already pinned in
    ``requirements.txt`` (``stripe==15.0.1``). ``STRIPE_API_KEY`` must be
    a real Stripe secret key (``sk_test_…`` / ``sk_live_…``).

Important parity notes
----------------------
* **Amount units.** The Emergent ``CheckoutSessionRequest.amount`` is a
  *float in major units* (EUR). The native Stripe API wants an *integer
  in minor units* (cents), so Mode B converts ``round(amount * 100)``.
* **Webhook verification.** Mode B verifies the ``Stripe-Signature`` only
  when ``STRIPE_WEBHOOK_SECRET`` ("whsec_…") is configured. When it is
  not set, the webhook body is parsed unverified and a warning is logged
  — the polling endpoint (``get_checkout_status``, which re-queries
  Stripe directly with the secret key) remains the trusted fulfilment
  path, so an unverified webhook can never credit an order on its own
  beyond what a direct Stripe status lookup confirms.

The module has zero hard dependency on the other ``core/*`` modules and
imports ``stripe`` lazily, so it loads even where ``stripe`` is absent
(Mode B simply raises on first use).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger("deepotus.stripe_checkout_compat")


# ---------------------------------------------------------------------
# Mode A — try the real Emergent proxy lib first.
# ---------------------------------------------------------------------
try:
    from emergentintegrations.payments.stripe.checkout import (  # type: ignore[import-not-found]
        CheckoutSessionRequest,
        CheckoutSessionResponse,
        CheckoutStatusResponse,
        StripeCheckout,
    )

    _USING_EMERGENT_PROXY = True
    logger.info(
        "[stripe_checkout_compat] Mode A active — routing through "
        "emergentintegrations.payments.stripe."
    )
    __all__ = [
        "CheckoutSessionRequest",
        "CheckoutSessionResponse",
        "CheckoutStatusResponse",
        "StripeCheckout",
    ]

except ImportError:
    _USING_EMERGENT_PROXY = False
    logger.info(
        "[stripe_checkout_compat] Mode B active — emergentintegrations not "
        "installed, falling back to the native Stripe SDK "
        "(real STRIPE_API_KEY required)."
    )

    # Human-readable product names for the hosted Checkout page, keyed by
    # the ``order_type`` stashed in metadata by core.stripe_checkout.
    # Mirrors PRODUCT_CATALOG labels; falls back to a generic name. Kept
    # here (not imported) so this module stays dependency-free.
    _PRODUCT_NAMES: Dict[str, str] = {
        "videogen": "DEEPOTUS Video Generator (one-time license)",
        "boardgame": "DEEPOTUS — FRAGMENTS (board game, founder edition)",
    }

    @dataclass
    class CheckoutSessionRequest:  # type: ignore[no-redef]
        """Native-mode equivalent of the Emergent request object.

        ``amount`` is a float in major currency units (EUR), matching the
        Emergent contract; the cents conversion happens in
        ``StripeCheckout.create_checkout_session``.
        """

        amount: float
        currency: str = "eur"
        success_url: str = ""
        cancel_url: str = ""
        metadata: Dict[str, str] = field(default_factory=dict)

    @dataclass
    class CheckoutSessionResponse:  # type: ignore[no-redef]
        url: str
        session_id: str

    @dataclass
    class CheckoutStatusResponse:  # type: ignore[no-redef]
        status: str
        payment_status: str
        amount_total: int  # minor units (cents), matching Stripe
        currency: str
        metadata: Dict[str, str] = field(default_factory=dict)

    @dataclass
    class WebhookEventResponse:  # type: ignore[no-redef]
        event_type: str
        event_id: str
        session_id: str
        payment_status: str
        metadata: Dict[str, str] = field(default_factory=dict)

    class StripeCheckout:  # type: ignore[no-redef]
        """Native-SDK equivalent of the Emergent ``StripeCheckout``.

        Signature-compatible with the original
        ``StripeCheckout(api_key=..., webhook_url=...)``. ``webhook_secret``
        is an additive optional argument; the existing call site never
        passes it, so it is sourced from ``STRIPE_WEBHOOK_SECRET``.
        """

        def __init__(
            self,
            api_key: Optional[str] = None,
            webhook_url: Optional[str] = None,
            webhook_secret: Optional[str] = None,
            **_kw: Any,
        ) -> None:
            self._api_key = (api_key or "").strip() or None
            self._webhook_url = webhook_url
            self._webhook_secret = (
                (webhook_secret or os.environ.get("STRIPE_WEBHOOK_SECRET", "")).strip()
                or None
            )

        def _require_key(self) -> None:
            if not self._api_key:
                raise ValueError(
                    "StripeCheckout (Mode B): empty api_key. Set a real "
                    "Stripe secret key in STRIPE_API_KEY."
                )

        async def create_checkout_session(
            self, request: "CheckoutSessionRequest"
        ) -> "CheckoutSessionResponse":
            import asyncio

            import stripe  # lazy — keeps cold-start light / import optional

            self._require_key()
            cents = int(round(float(request.amount) * 100))
            order_type = (request.metadata or {}).get("order_type", "")
            product_name = _PRODUCT_NAMES.get(order_type, "DEEPOTUS order")

            params: Dict[str, Any] = {
                "mode": "payment",
                "line_items": [
                    {
                        "price_data": {
                            "currency": (request.currency or "eur").lower(),
                            "product_data": {"name": product_name},
                            "unit_amount": cents,
                        },
                        "quantity": 1,
                    }
                ],
                "success_url": request.success_url,
                "cancel_url": request.cancel_url,
                "metadata": dict(request.metadata or {}),
            }

            def _create() -> Any:
                stripe.api_key = self._api_key
                return stripe.checkout.Session.create(**params)

            session = await asyncio.to_thread(_create)
            return CheckoutSessionResponse(
                url=session.url, session_id=session.id
            )

        async def get_checkout_status(
            self, session_id: str
        ) -> "CheckoutStatusResponse":
            import asyncio

            import stripe  # lazy

            self._require_key()

            def _retrieve() -> Any:
                stripe.api_key = self._api_key
                return stripe.checkout.Session.retrieve(session_id)

            session = await asyncio.to_thread(_retrieve)
            return CheckoutStatusResponse(
                status=(session.get("status") or "open"),
                payment_status=(session.get("payment_status") or "unpaid"),
                amount_total=int(session.get("amount_total") or 0),
                currency=(session.get("currency") or "eur").lower(),
                metadata=dict(session.get("metadata") or {}),
            )

        async def handle_webhook(
            self, body: bytes, signature: str
        ) -> "WebhookEventResponse":
            import asyncio
            import json

            import stripe  # lazy

            if self._webhook_secret:
                event: Dict[str, Any] = dict(
                    await asyncio.to_thread(
                        stripe.Webhook.construct_event,
                        body,
                        signature,
                        self._webhook_secret,
                    )
                )
            else:
                logger.warning(
                    "[stripe_checkout_compat] STRIPE_WEBHOOK_SECRET unset — "
                    "webhook signature NOT verified; the polling path remains "
                    "the trusted fulfilment source."
                )
                raw = (
                    body.decode("utf-8")
                    if isinstance(body, (bytes, bytearray))
                    else str(body)
                )
                event = json.loads(raw or "{}")

            obj = ((event.get("data") or {}).get("object")) or {}
            return WebhookEventResponse(
                event_type=event.get("type", "") or "",
                event_id=event.get("id", "") or "",
                session_id=obj.get("id", "") or "",
                payment_status=obj.get("payment_status", "") or "",
                metadata=dict(obj.get("metadata") or {}),
            )

    __all__ = [
        "CheckoutSessionRequest",
        "CheckoutSessionResponse",
        "CheckoutStatusResponse",
        "StripeCheckout",
        "WebhookEventResponse",
    ]
