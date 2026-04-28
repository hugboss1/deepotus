"""$DEEPOTUS backend ASGI entrypoint.

This module is intentionally minimal: it wires together FastAPI, CORS,
lifecycle events and all domain routers. All business logic lives under
`core/` (infrastructure) and `routers/` (endpoints).

Modular backend layout:
    core/
        config.py        env vars, Mongo handle, LLM + Resend config, prompts
        security.py      JWT rotation, rate limiter, `require_admin`, 2FA
        models.py        all Pydantic schemas
        email_service.py welcome email background task
    routers/
        public.py        /api/chat /api/prophecy /api/whitelist /api/stats
        public_stats.py  /api/public/stats (enriched timeseries)
        webhooks.py      /api/webhooks/resend (svix-signed)
        admin.py         /api/admin/*      (JWT + 2FA protected)
        vault.py         /api/vault/* + /api/admin/vault/*
        access_card.py   /api/access-card/* (Level 2 gatekeeper)
        operation.py     /api/operation/reveal (GENCOIN twist)
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from core.config import CORS_ORIGINS, client, db, logger
from core.security import ensure_jwt_secrets
from routers import (
    access_card as access_card_router,
    admin as admin_router,
    bots as bots_router,
    cabinet_vault as cabinet_vault_router,
    infiltration as infiltration_router,
    operation as operation_router,
    propaganda as propaganda_router,
    public as public_router,
    public_stats as public_stats_router,
    vault as vault_router,
    webhooks as webhooks_router,
    whale_watcher as whale_watcher_router,
)

# ---------------------------------------------------------------------
# FastAPI factory
# ---------------------------------------------------------------------
app = FastAPI(title="$DEEPOTUS API")

# Mount routers (order is cosmetic for OpenAPI grouping)
app.include_router(public_router.router)
app.include_router(public_stats_router.router)
app.include_router(webhooks_router.router)
app.include_router(admin_router.router)
app.include_router(vault_router.router)
app.include_router(vault_router.admin_router)
app.include_router(cabinet_vault_router.router)
app.include_router(access_card_router.router)
app.include_router(operation_router.router)
app.include_router(bots_router.router)
app.include_router(propaganda_router.router)
app.include_router(infiltration_router.public_router)
app.include_router(infiltration_router.admin_router)
app.include_router(whale_watcher_router.public_router)
app.include_router(whale_watcher_router.admin_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------
# Lifecycle events
# ---------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    """Warm up JWT secrets, ensure Mongo indexes, launch background loops."""
    await ensure_jwt_secrets()

    try:
        await db.whitelist.create_index("email", unique=True)
        await db.blacklist.create_index("email", unique=True)
        await db.chat_logs.create_index("created_at")
        await db.admin_sessions.create_index("created_at")
        await db.vault_events.create_index("created_at")
    except Exception:
        logging.exception("Index creation warning (ignored)")

    # Initialize PROTOCOL ΔΣ vault + launch hourly auto-tick background coroutine
    try:
        import vault as vault_mod

        await vault_mod.initialize_vault(db)
        asyncio.create_task(vault_mod.hourly_tick_loop(db))

        # DexScreener live-feed poll loop (falls back silently when mode=helius/off)
        import dexscreener as dex_mod

        asyncio.create_task(dex_mod.dex_loop(db, vault_mod))

        # Helius: ensure dedup TTL index + opportunistic catch-up if configured
        import helius as helius_mod
        from core.secret_provider import get_helius_api_key

        await helius_mod.ensure_dedup_index(db)
        vs = await db.vault_state.find_one({"_id": "protocol_delta_sigma"}) or {}
        helius_api_key = await get_helius_api_key()
        if helius_api_key and vs.get("dex_mode") == "helius" and vs.get("dex_token_address"):
            startup_demo_tokens = None
            if vs.get("helius_demo_mode"):
                startup_demo_tokens = int(vs.get("tokens_per_micro") or 10_000)
            asyncio.create_task(
                helius_mod.catch_up_from_helius(
                    db,
                    vault_mod,
                    helius_api_key,
                    vs["dex_token_address"],
                    pool=vs.get("helius_pool_address"),
                    demo_tokens_per_buy=startup_demo_tokens,
                )
            )
            logger.info(
                f"[startup] Helius catch-up scheduled for mint={vs['dex_token_address'][:8]}… (demo={bool(startup_demo_tokens)})"
            )

        logger.info(
            "[startup] PROTOCOL ΔΣ vault ready + hourly tick + DexScreener + Helius wiring launched"
        )
    except Exception:
        logging.exception("[startup] failed to initialize vault")

    # ---- Phase 1 bot fleet foundation (X / Telegram) ----
    try:
        from core.bot_scheduler import start_scheduler
        await db.bot_posts.create_index("created_at")
        await db.bot_posts.create_index([("platform", 1), ("created_at", -1)])
        await db.bot_posts.create_index([("status", 1), ("created_at", -1)])
        await start_scheduler()
        logger.info("[startup] bot scheduler online (Phase 1 — kill-switch ON by default).")
    except Exception:
        logging.exception("[startup] bot scheduler failed to start")

    # ---- Sprint 13.1 — Propaganda Engine ΔΣ ----
    try:
        from core import market_analytics as _ma, templates_repo as _tpl
        await db.propaganda_templates.create_index([("trigger_key", 1), ("language", 1)])
        await db.propaganda_queue.create_index("proposed_at")
        await db.propaganda_queue.create_index("idem_hash")
        await db.propaganda_queue.create_index("status")
        await db.propaganda_events.create_index("at")
        await _ma.ensure_indexes()
        seeded = await _tpl.seed_default_templates()
        logger.info(
            "[startup] Propaganda engine ready (seeded %d default templates).",
            seeded,
        )
    except Exception:
        logging.exception("[startup] propaganda engine failed to initialize")

    # ---- Sprint 14.1 — Pre-Launch Infiltration Brain ----
    try:
        from core import clearance_levels as _cl, riddles as _rid
        await _rid.ensure_indexes()
        await _cl.ensure_indexes()
        seeded_riddles = await _rid.seed_default_riddles()
        logger.info(
            "[startup] Infiltration Brain ready (seeded %d riddles).",
            seeded_riddles,
        )
    except Exception:
        logging.exception("[startup] infiltration brain failed to initialize")

    # ---- Sprint 15.2 — Brain Connect / Whale Watcher ----
    try:
        from core import whale_watcher as _ww
        await _ww.ensure_indexes()
        logger.info("[startup] Whale Watcher ready (queue + APScheduler tick).")
    except Exception:
        logging.exception("[startup] whale watcher failed to initialize")


@app.on_event("shutdown")
async def shutdown_db_client():
    try:
        from core.bot_scheduler import shutdown_scheduler
        await shutdown_scheduler()
    except Exception:
        logging.exception("[shutdown] bot scheduler shutdown warning")
    client.close()
