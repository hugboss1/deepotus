"""Stripe payments router (Sprint 20).

Endpoints:
  * ``POST /api/payments/checkout/session``
      Body: ``{ product_id, origin_url, locale?, customer? }``
      Returns: ``{ url, session_id, amount_eur, currency }``
      The frontend MUST send only ``product_id`` + ``origin_url`` (the
      window.location.origin). Prices are resolved server-side.

  * ``GET  /api/payments/checkout/status/{session_id}``
      Polled by the frontend after Stripe redirects back to /paiement.
      Also updates the local ``payment_transactions`` row and triggers
      one-time order fulfilment on the success transition.

  * ``POST /api/webhook/stripe``
      Webhook endpoint (set on Stripe dashboard if/when live keys are
      used). Same idempotent fulfilment path as the polling endpoint.

  * ``GET  /api/payments/download/{token}``
      Stub endpoint for Video Generator download links. Currently
      returns a 404 with an explanatory payload until the actual
      binary host is wired in.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from core import license_generator, orders, stripe_checkout
from core.config import logger

router = APIRouter(tags=["payments"])


# ---------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------
class CustomerInput(BaseModel):
    """Optional customer pre-fill data. Stripe Checkout will still ask
    for shipping (boardgame) and email at the hosted page; this just
    helps with prefilling and persistence."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(default=None, max_length=120)
    email: Optional[EmailStr] = None


class CreateSessionPayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: str = Field(..., pattern=r"^(boardgame|videogen)$")
    origin_url: str = Field(..., max_length=300)
    locale: str = Field(default="fr", pattern=r"^(fr|en)$")
    customer: Optional[CustomerInput] = None


class CreateSessionResponse(BaseModel):
    url: str
    session_id: str
    amount_eur: float
    currency: str
    metadata: Dict[str, str]


class CheckoutStatusOut(BaseModel):
    session_id: str
    status: str
    payment_status: str
    amount_eur: float
    currency: str
    metadata: Dict[str, str]
    order: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _webhook_url_from_request(request: Request) -> str:
    base = str(request.base_url).rstrip("/")
    return f"{base}/api/webhook/stripe"


async def _fulfil_if_needed(
    *,
    session_id: str,
    payment_status: str,
    status: str,
    metadata: Dict[str, str],
    amount_total_cents: int,
    currency: str,
) -> Optional[Dict[str, Any]]:
    """Idempotent fulfilment after a successful payment.

    Called both from polling status and from the webhook handler.
    Returns the persisted order doc (or None if not paid yet).
    """
    if payment_status != "paid":
        return None

    # Quick race-condition guard: order already created?
    existing = await orders.get_order_by_session(session_id)
    if existing:
        return existing

    order_type = metadata.get("order_type") or ""
    if order_type not in ("boardgame", "videogen"):
        logger.warning(
            "[payments] missing/unknown order_type in metadata for session=%s metadata=%r",
            session_id[:14] + "…", metadata,
        )
        return None

    amount_eur = float(amount_total_cents) / 100.0

    customer = {
        "email": metadata.get("customer_email") or None,
        "name": metadata.get("customer_name") or None,
        "locale": metadata.get("locale", "fr"),
    }

    license_key: Optional[str] = None
    download_token: Optional[str] = None
    download_expires_at: Optional[datetime] = None

    if order_type == "videogen":
        license_key = license_generator.generate_license_key()
        download_token, download_expires_at = license_generator.generate_download_token(ttl_hours=72)
        # Best-effort email
        if customer["email"]:
            license_generator.send_license_email(
                to_email=customer["email"],
                customer_name=customer.get("name") or "",
                license_key=license_key,
                download_token=download_token,
                locale=customer.get("locale", "fr"),
            )

    order_doc = await orders.create_order(
        order_type=order_type,
        stripe_session_id=session_id,
        amount_eur=amount_eur,
        currency=currency,
        customer=customer,
        metadata=metadata,
        license_key=license_key,
        download_token=download_token,
        download_expires_at=download_expires_at,
    )
    return order_doc


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@router.post("/api/payments/checkout/session", response_model=CreateSessionResponse)
async def create_session(payload: CreateSessionPayload, request: Request) -> CreateSessionResponse:
    webhook_url = _webhook_url_from_request(request)
    extra_metadata: Dict[str, str] = {}
    if payload.customer:
        if payload.customer.email:
            extra_metadata["customer_email"] = payload.customer.email
        if payload.customer.name:
            extra_metadata["customer_name"] = payload.customer.name
    try:
        out = await stripe_checkout.create_session_for_product(
            product_id=payload.product_id,
            origin_url=payload.origin_url,
            webhook_url=webhook_url,
            locale=payload.locale,
            extra_metadata=extra_metadata,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # Missing STRIPE_API_KEY etc — surface a generic 503
        logger.exception("[payments] create_session runtime error")
        raise HTTPException(status_code=503, detail="Payment provider not configured")
    except Exception:
        logger.exception("[payments] create_session unexpected error")
        raise HTTPException(status_code=502, detail="Failed to create Stripe checkout session")
    return CreateSessionResponse(**out)


@router.get("/api/payments/checkout/status/{session_id}", response_model=CheckoutStatusOut)
async def checkout_status(session_id: str, request: Request) -> CheckoutStatusOut:
    webhook_url = _webhook_url_from_request(request)
    try:
        status_resp = await stripe_checkout.fetch_session_status(
            session_id, webhook_url=webhook_url
        )
    except Exception:
        logger.exception("[payments] fetch_session_status failed")
        raise HTTPException(status_code=502, detail="Failed to fetch session status")

    # Persist the update locally
    prev = await stripe_checkout.update_transaction_status(
        session_id=session_id,
        status=status_resp.status,
        payment_status=status_resp.payment_status,
        metadata=status_resp.metadata,
        source="poll",
    )
    # Fulfilment (idempotent)
    order_doc = None
    try:
        order_doc = await _fulfil_if_needed(
            session_id=session_id,
            payment_status=status_resp.payment_status,
            status=status_resp.status,
            metadata=status_resp.metadata or {},
            amount_total_cents=int(status_resp.amount_total or 0),
            currency=(status_resp.currency or "eur").lower(),
        )
    except Exception:
        logger.exception("[payments] fulfilment failed for session=%s", session_id[:14] + "…")

    return CheckoutStatusOut(
        session_id=session_id,
        status=status_resp.status,
        payment_status=status_resp.payment_status,
        amount_eur=float(status_resp.amount_total or 0) / 100.0,
        currency=(status_resp.currency or "eur").lower(),
        metadata=status_resp.metadata or {},
        order=_safe_order_dict(order_doc),
    )


def _safe_order_dict(o: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if o is None:
        return None
    # Avoid leaking the download_token to the client; the email holds it
    pub = dict(o)
    pub.pop("download_token", None)
    # datetime → isoformat for JSON
    for k in ("created_at", "updated_at", "download_expires_at"):
        if isinstance(pub.get(k), datetime):
            pub[k] = pub[k].isoformat()
    if isinstance(pub.get("events"), list):
        for ev in pub["events"]:
            if isinstance(ev.get("at"), datetime):
                ev["at"] = ev["at"].isoformat()
    return pub


@router.post("/api/webhook/stripe")
async def stripe_webhook(request: Request) -> Dict[str, Any]:
    """Stripe webhook receiver. Idempotent fulfilment.

    Stripe-Signature header is verified by the library wrapper.
    """
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    webhook_url = _webhook_url_from_request(request)
    try:
        event = await stripe_checkout.parse_webhook(
            body=body, signature=signature, webhook_url=webhook_url
        )
    except Exception:
        logger.exception("[payments] webhook parse failed")
        # 200 to acknowledge — Stripe will not retry-storm us; we log.
        return {"received": True, "parsed": False}

    event_type = getattr(event, "event_type", "")
    session_id = getattr(event, "session_id", "") or ""
    payment_status = getattr(event, "payment_status", "") or ""
    metadata = getattr(event, "metadata", {}) or {}
    logger.info(
        "[payments] webhook event=%s session=%s payment_status=%s",
        event_type, (session_id[:14] + "…") if session_id else "-", payment_status,
    )

    if not session_id:
        return {"received": True, "action": "noop_missing_session"}

    # Persist + fulfil
    await stripe_checkout.update_transaction_status(
        session_id=session_id,
        status="complete" if payment_status == "paid" else "open",
        payment_status=payment_status or "unknown",
        metadata=metadata,
        source="webhook",
    )
    if payment_status == "paid":
        # We don't have amount_total / currency on the webhook payload
        # directly; re-query for safety.
        try:
            status_resp = await stripe_checkout.fetch_session_status(
                session_id, webhook_url=webhook_url
            )
            await _fulfil_if_needed(
                session_id=session_id,
                payment_status=status_resp.payment_status,
                status=status_resp.status,
                metadata=status_resp.metadata or metadata,
                amount_total_cents=int(status_resp.amount_total or 0),
                currency=(status_resp.currency or "eur").lower(),
            )
        except Exception:
            logger.exception("[payments] webhook fulfilment fetch failed")

    return {"received": True, "action": "ok"}


@router.get("/api/payments/download/{token}")
async def download_stub(token: str) -> Dict[str, Any]:
    """Stub for the Video Generator binary download.

    Returns 410 (Gone) with instructions — the installer host has not
    been wired in yet. Once the binary is uploaded, this endpoint will
    stream it from object storage.
    """
    raise HTTPException(
        status_code=410,
        detail={
            "token_present": bool(token),
            "message": (
                "Installer not yet hosted. Reply to your purchase email and "
                "a fresh link will be issued."
            ),
        },
    )


__all__ = ["router"]
