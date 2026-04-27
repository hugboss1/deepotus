"""Webhook receivers.

Two providers:
    - POST /api/webhooks/resend : email events (svix-signed)
    - POST /api/webhooks/helius : Solana swap events (authHeader-signed)

Each handler persists its raw payload into a dedicated Mongo collection
for audit + forwards the meaningful signal to the right consumer
(whitelist status update for Resend, vault.apply_crack() for Helius).
"""

from __future__ import annotations

import json as _json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from svix.webhooks import Webhook, WebhookVerificationError

import helius as helius_mod
import vault as vault_mod
from core.config import db
from core.secret_provider import (
    get_helius_webhook_auth,
    get_resend_webhook_secret,
)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/resend")
async def resend_webhook(request: Request):
    """Handle Resend events (delivered, bounced, complained, opened...).

    Signature verification via Svix Webhook header spec:
      svix-id, svix-timestamp, svix-signature
    Secret comes from the Cabinet Vault (email_resend / RESEND_WEBHOOK_SECRET)
    or, during transition, the RESEND_WEBHOOK_SECRET env var.
    """
    body_bytes = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}

    secret = await get_resend_webhook_secret()
    if secret:
        try:
            wh = Webhook(secret)
            payload = wh.verify(body_bytes, headers)
        except WebhookVerificationError:
            logging.warning("Webhook signature invalid")
            raise HTTPException(status_code=401, detail="Invalid signature")
        except Exception as e:
            logging.exception("Webhook verify failed")
            raise HTTPException(status_code=400, detail=f"Malformed webhook: {e}")
    else:
        # No secret configured yet — accept raw (logged)
        logging.warning(
            "RESEND_WEBHOOK_SECRET not set — accepting webhook without verification"
        )
        try:
            payload = _json.loads(body_bytes.decode("utf-8") or "{}")
        except Exception:
            payload = {}

    event_type = payload.get("type", "unknown")
    data = payload.get("data", {}) or {}
    email_id = data.get("email_id") or data.get("id")
    to_field = data.get("to", [])
    if isinstance(to_field, list) and to_field:
        recipient = (to_field[0] or "").lower()
    elif isinstance(to_field, str):
        recipient = to_field.lower()
    else:
        recipient = ""

    # Persist every event (small log collection)
    await db.email_events.insert_one(
        {
            "_id": str(uuid.uuid4()),
            "type": event_type,
            "email_id": email_id,
            "recipient": recipient,
            "raw": payload,
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    # Map event -> status
    status_map = {
        "email.sent": "sent",
        "email.delivered": "delivered",
        "email.delivery_delayed": "delayed",
        "email.bounced": "bounced",
        "email.complained": "complained",
        "email.opened": "opened",
        "email.clicked": "clicked",
    }
    status = status_map.get(event_type, event_type.split(".")[-1])

    # Update the whitelist entry for this email_id (preferred) or recipient
    query = None
    if email_id:
        query = {"email_id": email_id}
    elif recipient:
        query = {"email": recipient}

    if query:
        update = {
            "email_status": status,
            f"email_status_{status}_at": datetime.now(timezone.utc).isoformat(),
        }
        if status == "delivered":
            update["email_sent"] = True
        await db.whitelist.update_one(query, {"$set": update})

    return {"ok": True, "processed": event_type}



# ---------------------------------------------------------------------
# Helius — Solana swap feed (per-trade, push)
# ---------------------------------------------------------------------
@router.post("/helius")
async def helius_webhook(request: Request):
    """Receive enhanced Solana SWAP events pushed by Helius.

    Security: Helius sends the `authHeader` value we configured (stored in
    HELIUS_WEBHOOK_AUTH env var) verbatim in the `Authorization` header. If
    the env var is unset, we accept unsigned payloads in DEMO mode but log a
    prominent warning.

    Flow:
      1. Verify Authorization header matches HELIUS_WEBHOOK_AUTH.
      2. Read the vault config to pick up the configured mint + pool.
      3. Pass the transactions array to helius.ingest_enhanced_transactions(),
         which handles dedup and invokes vault.apply_crack() per buy.

    Helius retries on non-2xx, so we strive to always 2xx unless the
    signature is wrong. Internal errors are logged but still return 200.
    """
    # --- 1. Auth ---
    auth_hdr = request.headers.get("authorization") or ""
    helius_auth = await get_helius_webhook_auth()
    if helius_auth:
        if auth_hdr.strip() != helius_auth:
            logging.warning("[helius] webhook auth mismatch")
            raise HTTPException(status_code=401, detail="Invalid auth header")
    else:
        logging.warning(
            "[helius] HELIUS_WEBHOOK_AUTH not configured — accepting unsigned webhook"
        )

    # --- 2. Payload ---
    try:
        payload = await request.json()
    except Exception:
        raw = await request.body()
        try:
            payload = _json.loads(raw.decode("utf-8") or "[]")
        except Exception:
            payload = []

    # Helius sends an ARRAY of enhanced transactions
    txs: List[Dict[str, Any]] = payload if isinstance(payload, list) else [payload]

    # --- 3. Route through the ingest pipeline ---
    vs = await db.vault_state.find_one({"_id": "protocol_delta_sigma"}) or {}
    mint = (vs.get("dex_token_address") or "").strip()
    pool = (vs.get("helius_pool_address") or "").strip() or None
    demo_tokens_per_buy: int | None = None
    if vs.get("helius_demo_mode"):
        demo_tokens_per_buy = int(vs.get("tokens_per_micro") or 10_000)

    await helius_mod.ensure_dedup_index(db)

    # Always keep a raw audit trail (capped-ish: we just insert; the TTL on
    # helius_ingested covers the signature-level dedup)
    try:
        await db.helius_webhook_events.insert_one(
            {
                "_id": str(uuid.uuid4()),
                "received_at": datetime.now(timezone.utc).isoformat(),
                "tx_count": len(txs),
                "raw_sample": txs[:2],  # keep only first 2 for storage sanity
            }
        )
    except Exception:
        logging.exception("[helius] failed to persist raw audit trail")

    if not mint:
        logging.warning(
            "[helius] no dex_token_address configured on vault_state — ignoring payload"
        )
        return {"ok": True, "ignored": True, "reason": "no mint configured"}

    result = await helius_mod.ingest_enhanced_transactions(
        db,
        vault_mod,
        txs,
        mint=mint,
        pool=pool,
        source="webhook",
        demo_tokens_per_buy=demo_tokens_per_buy,
    )
    logging.info(
        f"[helius] webhook {result} (tx={len(txs)}, mint={mint[:8]}…, pool={pool}, demo={bool(demo_tokens_per_buy)})"
    )
    return {"ok": True, **result}
