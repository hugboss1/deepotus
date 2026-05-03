# Sprint 19 + 19.1 — Push GitHub & Deploy Guide

> Last updated: 2026-05-03 — Cadence wiring + reactive triggers + holders
> live poller all shipped on the preview. Ready to deploy.

This guide is the **single source of truth** for getting Sprint 19 +
Sprint 19.1 (which all live on the preview right now) into your
production Vercel + Render deployments. Sprint 17 + 18 are already in
your prod (their guide is at `docs/SPRINT_17_18_DEPLOY.md`).

---

## TL;DR — what's in this push

### Copy & UI tweaks
- **Phase 4 card "Loyalty Mandate"** — replaced the "Charity / UNICEF /
  Téléthon" copy with a candidate-style political slogan: *"the
  Cabinet buys back for the loyal · ΔΣ buybacks fire on every
  milestone the people unlock · Monthly distributions to Niveau 02+
  citizens · the longer the crowd stays loyal, the more the Cabinet
  rebuys"*. FR + EN both rewritten.

### `raydium` → `PumpSwap` global rename (24 files)
- All translation strings (Pump.fun graduation, How-to-Buy, Tokenomics).
- All URLs migrated `raydium.io/swap` → `swap.pump.fun`.
- All Python variables (`raydium_link` → `pumpswap_link`,
  `_build_raydium_link` → `_build_pumpswap_link`).
- Trigger key `raydium_migration` → `pumpswap_migration` AND the file
  `core/triggers/raydium_migration.py` was renamed to
  `core/triggers/pumpswap_migration.py`.
- DEX state value `dex_mode == "raydium"` → `dex_mode == "pumpswap"`.

### Cadence engine (Sprint 19)
- New module `backend/core/cadence_engine.py` — implements the daily
  schedule + reactive triggers + whale-react hook.
- New scheduler job `cadence_tick` running every **60 s**.
- `cadence_engine` reads `bot_config.cadence` on every tick and pushes
  V2 posts into the propaganda queue with `policy="auto"`. The
  dispatch worker handles X / Telegram delivery once credentials are
  present in the Cabinet Vault.
- Per-day, per-slot dedup persisted in `cadence._state.last_fired_today`.
- Per-milestone dedup persisted in `cadence._state.fired_milestones`.

### Holders poller (Sprint 19.1)
- New module `backend/core/holders_poller.py` — periodic poll of the
  live SPL token holders count via **Helius DAS `getTokenAccounts`**.
  Falls back gracefully when the mint isn't set (pre-mint state).
- New scheduler job `holders_poll` running every **5 minutes**.
- Persists `vault_state.dex_holders_count` so the cadence reactive
  tick can fire holder-milestone posts cleanly.
- Tested live on BONK: paginated 100 × 1000 accounts in ~13 s, hit the
  100k cap (as expected for BONK), tagged `approximate=true`.

---

## Files (Sprint 19 + 19.1)

### Modified
```
backend/core/bot_config_repo.py        # cadence defaults + ALLOWED_PATCH_KEYS
backend/core/bot_scheduler.py          # +cadence_tick + holders_poll jobs
backend/core/cadence_engine.py         # NEW — engine
backend/core/holders_poller.py         # NEW — Helius DAS poller
backend/core/prophet_studio.py         # PROMPT_TEMPLATES_V2 (+5 archetypes)
backend/core/whale_watcher.py          # +cadence_whale_react hook
backend/routers/bots.py                # Pydantic patches + V2 endpoints
backend/core/triggers/pumpswap_migration.py   # RENAMED from raydium_migration.py
frontend/src/i18n/translations.js      # Phase 4 rewrite + raydium→PumpSwap
frontend/src/lib/launchPhase.ts        # PumpSwap URL only
frontend/src/pages/AdminBots.jsx       # +Cadence tab + V2 toggles
frontend/src/pages/admin/sections/AdminCadenceSection.tsx   # NEW
… plus ~14 other files via the global raydium→PumpSwap pass
```

### Suggested commit message

```
sprint-19: cadence wiring + reactive triggers + holders live poller +
  raydium→PumpSwap rename + Phase 4 loyalty mandate copy

UI / copy
- Phase 4 card "Charity" replaced with "Loyalty Mandate" — candidate-
  style political slogan with conditional buybacks tied to milestones
  and Niveau 02+ distributions. No UNICEF / Téléthon references.
- Global rename raydium → PumpSwap (24 files): translations, URLs,
  Python variables, trigger keys, state values. core/triggers/
  raydium_migration.py renamed to pumpswap_migration.py.

Cadence engine (Sprint 19)
- core/cadence_engine.py: daily schedule reader, quiet-hours logic
  (handles wrap past midnight), weighted archetype picker, three
  ticks (daily / reactive / whale_react). Per-day + per-milestone
  dedup persisted on bot_config.cadence._state.
- core/bot_scheduler.py: cadence_tick job (60 s interval).
- core/whale_watcher.py: fire-and-forget cadence_whale_react() hook
  after the v1 propaganda enqueue. Idempotent on tx_signature.
- Posts go through dispatch_queue.propose(policy="auto") with trigger
  keys cadence_daily / cadence_holder / cadence_marketcap /
  cadence_whale.

Holders poller (Sprint 19.1)
- core/holders_poller.py: Helius DAS getTokenAccounts pagination,
  page_size=1000, max_pages=100. DexScreener kept as a placeholder
  source for a future provider swap. No-op when mint is unset.
- core/bot_scheduler.py: holders_poll job (5 min interval).
- Persists vault_state.dex_holders_count + dex_holders_polled_at +
  dex_holders_source + dex_holders_approximate. Errors surface in
  dex_holders_error without overwriting the previous good value.

Bug fixes
- cadence_engine._read_market_snapshot() now reads vault_state with
  the canonical _id "protocol_delta_sigma" (was "deepotus_protocol").

Tested end-to-end
- Holders poll on BONK → 99997 / 100000 accounts paginated, approximate=true.
- Cadence daily slot fired in ≤ 60 s, propaganda_queue item with
  template "prophecy" (or whatever the slot's archetype whitelist
  allows) and bilingual content.
- Cadence reactive holder milestone fired with template "stats" when
  a synthetic holder count of 750 crossed the 500-milestone.
- All flows respect kill_switch + quiet_hours + per-slot dedup.
```

---

## Step 1 — Push from Emergent

Click **`Push to GitHub`** in the Emergent UI top-right. The auto-commits
already contain everything (the engine commits the diff every few file
ops). Confirm the push, wait for the green toast.

---

## Step 2 — Vercel auto-redeploys the frontend

Same as Sprint 17/18 — Vercel watches `main`, builds within a minute,
no env-var changes required. Verify after deploy:

1. Hard refresh, open the landing page.
2. Scroll to the roadmap → Phase 4 card title now reads **"Loyalty
   Mandate"**, no UNICEF / Téléthon strings anywhere on the page.
3. Anywhere you previously saw "Raydium" (Phase 2 graduation in the
   roadmap, How-to-Buy step copy, etc.) you now see **"PumpSwap"**.
4. `/admin/bots`:
   - 5 tabs visible (Config, Preview, **Cadence**, Jobs, Logs).
   - Cadence tab: Daily schedule, Reactive triggers, Quiet hours all
     render and persist on edit.
   - Jobs tab: scheduler list shows **`cadence_tick`** (60 s) and
     **`holders_poll`** (300 s = 5 min).

---

## Step 3 — Render auto-redeploys the backend

Render watches the same `main`. ~3-4 min downtime during swap. Verify:

1. `GET /api/admin/bots/jobs` (with admin Bearer) → response includes
   `{"id": "cadence_tick", "interval": "0:01:00"}` and
   `{"id": "holders_poll", "interval": "0:05:00"}`.
2. `GET /api/admin/bots/v2-templates` → 5 templates returned.
3. `GET /api/admin/bots/config` → top-level `prompt_v2` and `cadence`
   blocks with safe defaults.

### NEW required env vars on Render
**None.** Sprint 19 reuses the existing `HELIUS_API_KEY` (already in
your Render env via the Cabinet Vault) and the `EMERGENT_LLM_KEY` for
V2 generation. No new secrets.

---

## Step 4 — Post-deploy admin actions (optional)

Defaults are safe (kill-switch ON, all platforms disabled, reactive
triggers off). To activate:

1. **Disable the kill-switch** (`/admin/bots` header → kill-switch
   toggle).
2. **Enable Prompt V2** (Config tab → "Prompt V2 — 5 weighted
   templates").
3. **Configure the daily schedule** (Cadence tab → enable X / TG,
   add UTC slots, optionally restrict allowed archetypes).
4. **Enable reactive triggers** + tune milestones (Cadence tab →
   Reactive triggers block).
5. **Configure quiet hours** (Cadence tab → Quiet hours block).

The `holders_poll` job starts running automatically as soon as the
mint address is set on `vault_state.dex_token_address` (typically the
moment you mint via Pump.fun and the existing mint webhook fires).
**Until then it logs `skipped: no_mint` every 5 minutes** — totally
benign.

---

## Step 5 — What's still MOCKED

- **X / Telegram dispatch**: the propaganda queue items will pile up
  with `status="approved"` until you enter platform credentials in
  `/admin/cabinet-vault`. The dispatch worker is already wired —
  it'll start sending immediately once it sees credentials.
- **DexScreener as a holders source**: kept as a placeholder slot in
  `holders_poller.py:_fetch_via_dexscreener` since DexScreener does
  not expose a holder count today. If they ship that field (or you
  want to swap to Birdeye), it's a one-function change.

---

## Rollback

- **Vercel / Render**: promote the previous deploy (Sprint 17/18) from
  the Deployments page. ~30 s.
- **Disable cadence without rolling back**:
  - `PUT /api/admin/bots/config` `{"cadence": {"daily_schedule":
    {"x": {"enabled": false}, "telegram": {"enabled": false}}},
    "reactive_triggers": {"enabled": false}}`.
  - The schedulers stay alive but skip every tick.
- **Disable Prompt V2 without rolling back**:
  - `PUT /api/admin/bots/config` `{"prompt_v2": {"enabled": false}}`.

— Council ΔΣ engineering log
