# Landing Page $DEEPOTUS — Memecoin IA Prophète (Deep State POTUS)

## User-Validated Configuration
- **Ticker**: `$DEEPOTUS` (Deep State POTUS)
- **Language**: Bilingual FR/EN with toggle
- **Art direction**: Hybrid — institutional/MiCA-compliant top + brutalist crypto-degen/meme bottom + deepfake/AI-generated aesthetic throughout. The AI Prophet is positioned as a **candidate for President of the entire World**, the chosen one of the Deep State to lead humanity.
- **LLM**: Emergent LLM key (user confirmed)
- **All interactive features**: live chat, prophecies feed, tokenomics pie, ROI sim, countdown, roadmap, FAQ, whitelist, social mockups

---

## Original Problem Statement (Full context preserved)

The project lives inside the framework of a comprehensive dossier de cadrage. The memecoin $DEEPOTUS is a Solana token functioning as a **transparent treasury vehicle** under MiCA-aligned disclosures.

### Narrative core
- Cynical, lucid, mocking AI prophet announcing global recession, potential depression, geopolitical disorder, market fragility
- Reframed for $DEEPOTUS as **the Deep State's chosen presidential candidate for the entire World**
- Inspirations: Dogecoin (community viral), Turbo/TURBO (first memecoin co-designed with GPT-4), Truth Terminal/GOAT (AI as autonomous narrative actor)
- Public narrative pivot: funding goal is **classified** under **PROTOCOL ΔΣ** (Black Op).
- **GENCOIN** is a twist revealed only after vault declassification on `/operation`
- Post-declassification funnel pivot: the “true vault” is gated behind **Level 02** accreditation (email access card) and lives at `/classified-vault`

### Financial parameters (must remain visible on site where applicable)
- Chain: **Solana**
- Supply: **1,000,000,000** (1B)
- Target price: **€0.0005**
- FDV: **€500,000**
- Initial LP: **€2,000** at J0 → **€10,000** at J+2 (~2M tokens injected initially)

> Note: The previous explicit fundraising goal (e.g. €300,000 / 3 weeks) is now intentionally **hidden** in the public narrative and replaced by a *classified* goal mechanism (PROTOCOL ΔΣ vault).

### Tokenomics (30% Treasury scenario — final)
| Category | Allocation |
|---|---|
| Liquidity / DEX | 10–15% |
| Project / Operation Treasury (MiCA + operations) | **30%** |
| Marketing / KOL / partnerships | 10% |
| Airdrops / community | 20% |
| AI / lore reserve | 10% |
| Team / advisors (vesting) | 15–20% |

### Transaction tax
- **3%** total → **2%** Operation / compliance budget + **1%** liquidity/marketing
- Clear cap + tax reduction once the objective is reached (reframed as “once the Vault opens”)

### Liquidity plan
- **J0**: LP €2K symmetric (~€1K memecoin + ~€1K SOL/USDC), ~2M tokens in pool
- **J+2**: Scale LP €2K → €10K (net +€8K)
  - ~€6K from controlled Treasury sale split into small blocks
  - ~€2K from taxes / external contribution

### Anti-dump measures
- LP lock or burn after J+2 reinforcement
- Treasury in **multisig** with **timelock** and daily/weekly sell caps
- Split sales into small blocks
- No massive airdrop or unlocked KOL distribution around J+2

### MiCA compliance disclosures (prominent)
- Token is **highly speculative**
- **No yield promise**
- **Not a stablecoin**, **not a financial security**
- Function: transparent treasury vehicle with clear structure, governance, risk disclosures

### Honest success probabilities (must remain honest)
- Global memecoin success rate: ~1.4%
- Qualitative estimate for strong execution: 2–3%
- Objective achievement within the launch window: ~1% (order of magnitude)

---

## Target audiences
- **Serious investors**: Need MiCA transparency, clear tokenomics, risk disclosure, roadmap, team info, vesting
- **Crypto-degen community**: Need meme energy, AI prophet persona, viral/shitpost tone, deepfake aesthetic

---

## Sections / features to build

1. **Hero** — Deepfake AI Prophet President candidate banner, bilingual toggle, main CTA, countdown, $DEEPOTUS ticker
2. **Vault (PROTOCOL ΔΣ)** — animated “classified vault” section with 6-digit combination mechanics + AI vault chassis mockup + DexScreener live activity + Level 02 funnel CTA (Phases 10–15)
3. **AI Prophet Live Chat** — Emergent LLM, in-character cynical Deep State POTUS candidate, bilingual
4. **Auto-refreshing Prophecies Feed** — LLM-generated apocalyptic one-liners
5. **Mission Section** — MiCA framing + transparent structure, reframed to PROTOCOL ΔΣ / classified operation
6. **Interactive Tokenomics** — Recharts pie with hover details
7. **Liquidity & Treasury Transparency** — Visual J0 → J+2 timeline, anti-dump measures
8. **ROI Simulator** — Investment input → theoretical tokens, honest risk warning
9. **Roadmap** — Visual timeline
10. **FAQ** — MiCA compliance, tax, treasury, vesting, risks, and “why goal is hidden”
11. **Whitelist / Email Capture** — Stored in MongoDB
12. **Social Mockups** — X/Twitter, Telegram, Discord
13. **Risk Disclaimer Footer** — Full MiCA-compliant language, bilingual
14. **Language Switcher** — FR ↔ EN toggle
15. **Operation Reveal Page (`/operation`)** — gate-locked until vault declassified; reveals twist + countdown + Phase 12 “Fall of Deep State” illustration
16. **Classified Vault (Level 02) (`/classified-vault`)** — gated full-page “real vault” with accreditation + session token, displaying live activity feed + Phase 14 door keypad gate UI + Phase 15 DECLASSIFIED CTA parity

---

## Tech Stack
- Backend: FastAPI + MongoDB + `emergentintegrations` (Emergent LLM)
- Frontend: React + Tailwind + shadcn/ui + framer-motion + recharts + lucide-react
- i18n: Simple Context-based FR/EN (no heavy library)
- Email: Resend + webhooks (Svix verification)
- Dex / market feed: **DexScreener API** polling (Phase 11)
- Image generation: Gemini Nano Banana (`gemini-3.1-flash-image-preview`) (Phases 10–15)
- Image processing: Pillow (PIL) + qrcode (Phase 13)

---

## Phases

### Phase 1 — Core POC (AI Prophet LLM Persona) — **LIGHT POC**
Single Python script (`/app/tests/test_core.py`) that validates:
- Emergent LLM integration works
- Chat persona stays in character in **FR + EN**
- Prophecy generation is memorable/memetic
- Language switching preserves persona
- **Status**: ✅ COMPLETED (PASSED)

### Phase 2 — Full Landing Page Build
- Backend routes: `/api/chat`, `/api/prophecy`, `/api/whitelist`, `/api/stats`
- Frontend: Full bilingual landing with all sections, i18n, animations
- MongoDB collections: `whitelist`, `chat_logs`, `prophecies_cache`
- **Status**: ✅ COMPLETED

### Phase 3 — Testing & Polish
- End-to-end testing covering ALL user stories
- Bug fixes
- **Status**: ✅ COMPLETED

---

## User Stories (ALL must be validated in testing)

1. As a **serious investor**, I land on the site and immediately grasp it is a MiCA-aware memecoin with transparent structure and governance
2. As a **degen**, I feel the meme energy + AI Prophet Deep State POTUS persona instantly
3. As a **French user**, I read the whole site in French; as **English user**, I switch to EN in one click
4. As a **visitor**, I chat live with the AI Prophet and get cynical in-character responses
5. As a **visitor**, I see auto-refreshing fresh prophecies
6. As a **potential buyer**, I see an interactive tokenomics pie chart with details on every allocation
7. As a **potential buyer**, I use the ROI simulator with honest risk context shown
8. As a **visitor**, I see a live countdown to launch
9. As a **compliance-aware investor**, I see the J0 → J+2 liquidity timeline + anti-dump measures (multisig/timelock)
10. As a **visitor**, I submit my email to the whitelist successfully
11. As a **compliance reader**, I see the full MiCA-aligned risk disclaimer in the footer
12. As a **visitor**, I see a clear roadmap
13. As a **skeptical reader**, I see honest success probabilities
14. As a **visitor**, I see visible social mockups (X, Telegram, Discord)
15. As an **admin**, I can securely send transactional emails and observe lifecycle events via signed webhooks
16. As a **visitor**, I see a live “classified vault” that progresses through stages and creates narrative tension
17. As a **visitor**, I can access `/operation` only once the vault is declassified and see the twist + countdown
18. As a **visitor**, I see a **cinematic electronic vault mockup** containing the 6 dials (AI illustration) for stronger immersion
19. As a **visitor**, I see **real market activity** reflected in the vault activity feed (DexScreener) when enabled
20. As an **admin**, I can switch live activity feed modes (off/demo/custom), set the Solana mint, and force a poll for debugging
21. As a **mobile visitor**, I see the vault dials remain anchored inside the vault mockup (no layout drop below the image)
22. As a **visitor** (post-declassification), I see a cinematic illustration representing the “Fall of the Deep State” with the RIPPLED crowd on the `/operation` reveal page
23. As a **visitor** (post-declassification), clicking the vault CTA opens a **terminal popup** that sarcastically denies access to the “true vault” unless Level 02 clearance is obtained
24. As a **visitor**, I can request **Level 02** via email and receive a personalized **Deep State access card** (name + accreditation + QR)
25. As a **Level 02 visitor**, I can access `/classified-vault` by entering my accreditation number and receive a 24h session token
26. As a **Level 02 visitor**, I can view the “true vault” full-page UI showing live activity (DexScreener) and the combination progress
27. As a **Level 02 visitor**, the gate UI uses a cinematic AI door with digicode, and the code input is anchored inside the door display on desktop
28. As a **Level 02 visitor**, the authed “true vault” view uses the same VaultChassis mockup as the home vault for visual continuity
29. As a **Level 02 visitor**, the “true vault” authed view shows the same DECLASSIFIED green CTA animation as the homepage and links to `/operation` when declassified
30. As a **visitor**, the combination responds to real token activity with micro-rotations (10K tokens) and major locks (100M tokens)

---

## Current Status
- Plan created ✅
- Integration playbook ✅
- Design guidelines ✅
- POC script: ✅ PASSED
- Backend build ✅
- Frontend build ✅
- Testing: ✅ PASS
- **Delivery ✅**

---

## Phase 8 — 2FA, Heatmap, Full Export, Email Events Drill-down, Cooldown Blacklist (completed ✅)
- ✅ **2FA TOTP** — pyotp + qrcode, backup codes, enable/disable, protected login
- ✅ **Activity heat-map** on `/stats`
- ✅ **Full whitelist export** — `/api/admin/whitelist/export`
- ✅ **Admin Email Events** — `/admin/emails` drill-down backed by `/api/admin/email-events`
- ✅ **Cooldown blacklist** — cooldown_until + auto-unblock

---

## Phase 9 — Resend Webhook Finale (Svix) + Test Emails (completed ✅)
Objectif : finaliser la boucle **emails sortants** → **webhooks entrants signés** → **observabilité admin**.

### Implémentation
1. ✅ Inject `RESEND_WEBHOOK_SECRET` into `/app/backend/.env`
2. ✅ Restart backend
3. ✅ Option (a) whitelist flow test (plus-addressing)
4. ✅ Option (b) admin endpoint `POST /api/admin/test-email`
5. ✅ Verify `email.sent` + `email.delivered` events in `/api/admin/email-events`

### Critères d’acceptation
- ✅ Sender `wcu@deepotus.xyz` unchanged
- ✅ Svix signature verification enabled
- ✅ Events persisted + visible in admin

---

## Phase 10 — PROTOCOL ΔΣ (Coffre classifié + reveal twist) — **COMPLETED ✅**

### Objectives (updated)
- ✅ Remove **all** public mentions of “GENCOIN” and replace narrative with **PROTOCOL ΔΣ** (Black Op)
- ✅ Hide the explicit fundraising goal and replace with *classified objective mechanics*
- ✅ Add a new animated **Vault section** without deleting existing sections
- ✅ Implement vault progression logic (initially 1 dial / 1,000 tokens; later updated in Phase 15)
- ✅ Add **hourly auto-tick** independent of purchases
- ✅ Add a gated **/operation** reveal page that only unlocks at **DECLASSIFIED**
- ✅ Provide admin controls for vault debugging/demo
- ✅ Ensure vault security: public endpoints never leak the target combination

### Implementation (what was built)
**Backend**
- New module: `/app/backend/vault.py`
- New collections:
  - `vault_state` (single doc: stage, digits_locked, tokens_sold, target_combination, config)
  - `vault_events` (public feed)
- New endpoints:
  - `GET /api/vault/state` (public)
  - `POST /api/vault/report-purchase` (public; clamped to <= 50,000 tokens)
  - `GET /api/admin/vault/state` (admin; reveals `target_combination`)
  - `POST /api/admin/vault/crack` (admin; manual crack)
  - `POST /api/admin/vault/config` (admin; config + reset)
  - `GET /api/operation/reveal` (public; returns unlocked=false unless DECLASSIFIED)
- Background task:
  - `hourly_tick_loop(db)` started at app startup (keeps vault alive)
- Chat prompt updated to reference Vault/PROTOCOL ΔΣ and never mention GENCOIN

**Frontend**
- New section inserted (non-destructive): `VaultSection` placed between Manifesto and Chat
- New route page: `/operation`
  - Locked gate view when vault not declassified
  - Reveal view with Prophet panic + full lore + countdown to GENCOIN launch + link to `https://gencoin.xyz`
- New admin page: `/admin/vault`
  - Crack manual, config, reset, event list
- i18n updated (FR/EN): all public copy switched from GENCOIN to PROTOCOL ΔΣ; GENCOIN appears only on `/operation`

### Testing
- ✅ Backend-only testing agent: **20/20 tests passed** (`/app/test_reports/iteration_7.json`)
- ✅ Security verified: `target_combination` never present in `GET /api/vault/state`
- ✅ Regression verified: existing endpoints still functional

---

## Phase 11 — AI Vault Mockup + DexScreener Live Activity (completed ✅)

### Objectives
- ✅ Replace the “floating dials” look with a **cinematic electronic vault chassis** generated via AI
- ✅ Overlay the 6 dials inside the chassis in a responsive, high-fidelity way
- ✅ Connect vault activity to **real token market activity** using DexScreener in a hybrid mode:
  - **off** (no polling)
  - **demo** (BONK live feed to demonstrate activity before $DEEPOTUS deployment)
  - **custom** (real $DEEPOTUS Solana mint address)
- ✅ Ensure security: public vault state remains non-sensitive (no admin DEX fields leaked)
- ✅ Provide admin UX to configure + debug live feed (force poll)

### Implementation

**AI Illustration (Gemini Nano Banana)**
- ✅ Script: `/app/tests/generate_vault_frame.py` (Gemini `gemini-3.1-flash-image-preview`)
- ✅ Output asset: `/app/frontend/public/vault_frame.png`

**Frontend (Vault UX refactor)**
- ✅ Added component: `/app/frontend/src/components/landing/vault/VaultChassis.jsx`
- ✅ Updated: `VaultSection.jsx` (DEX badge)
- ✅ Updated: `CombinationDial.jsx` (size modes)

**Backend (DexScreener integration)**
- ✅ New module: `/app/backend/dexscreener.py`
- ✅ New admin endpoints:
  - `POST /api/admin/vault/dex-config`
  - `POST /api/admin/vault/dex-poll`

### Testing
- ✅ Backend-only testing agent: **22/22 tests passed** (`/app/test_reports/iteration_8.json`)

---

## Phase 12 — Mobile Vault Fix + “Fall of Deep State” Illustration (completed ✅)

### Objectives
- ✅ Fix mobile vault layout so the dials remain anchored *inside* the vault mockup
- ✅ Add a cinematic illustration on the `/operation` reveal page depicting the Prophet panicking and chased by the RIPPLED crowd

### Implementation
- ✅ `VaultChassis` responsive anchoring (mobile 4:3, desktop 16:9)
- ✅ Script: `/app/tests/generate_prophet_chased.py`
- ✅ Asset: `/app/frontend/public/prophet_chased.png`
- ✅ Integrated into `/operation` reveal with bilingual i18n keys

---

## Phase 13 — Funnel NIVEAU 02 (Terminal + Carte d’accès + Vault réel) — **COMPLETED ✅**

### Objectives
- ✅ Replace declassification CTA behavior: open a sarcastic CRT terminal popup instead of navigating directly
- ✅ Implement Level 02 access card email with personalized accreditation + QR
- ✅ Create `/classified-vault` full-page real vault gated by accreditation + session token

### Implementation
- ✅ Access card template generation + PIL overlay pipeline (`/app/backend/access_card.py`)
- ✅ Access card endpoints: request/verify/status/image
- ✅ Resend email template with inline CID attachment + CTA
- ✅ TerminalPopup CRT modal with typing denial + request form
- ✅ ClassifiedVault gate + authed view + session persistence
- ✅ Backend testing agent: **41/41 tests passed** (`/app/test_reports/iteration_9.json`)
- ✅ User validated: email receipt OK

### Runtime Defaults
- ✅ Vault reset state: `LOCKED 0/6`
- ✅ Dex mode: `demo` enabled by default

---

## Phase 14 — AI Door Gate + VaultChassis Reuse in ClassifiedVault — **COMPLETED ✅**

### Objectives
- ✅ Make the `/classified-vault` code-entry gate more immersive and anchored in-world
- ✅ Add an AI-generated reinforced door with keypad, with an empty LED display area reserved for overlay
- ✅ Anchor the accreditation input into the door display (desktop) while providing a mobile fallback
- ✅ Reuse the same **VaultChassis** mockup on the authed `/classified-vault` view (visual continuity)

### Implementation
- ✅ Script: `/app/tests/generate_door_keypad.py`
- ✅ Asset: `/app/frontend/public/door_keypad.png`
- ✅ Gate redesign: overlay input anchored to door LED display (`left 42% · top 40% · w 17% · h 9%`)
- ✅ i18n additions (FR/EN): `gateChannel`, `gateLevel`, `gateIdle`, `gateHintShort`

---

## Phase 15 — Production Mechanics Rework + True Vault DECLASSIFIED Animation Parity — **COMPLETED ✅**

### Objectives
- ✅ Move to production-aligned mechanics:
  - **1 dial locks per 100,000,000 tokens bought**
  - **1 micro-rotation per 10,000 tokens bought**
  - **Declassify at 600,000,000 tokens** (or earlier when treasury ≥ **300,000€** in custom mode)
- ✅ Implement treasury-based criterion (300K€) using DexScreener price (custom mode)
- ✅ Ensure hourly tick cannot overshoot in production scale
- ✅ Ensure DexScreener custom mode applies **real token volume** per poll (no batching)
- ✅ Implement deterministic micro-rotation animation on the active dial
- ✅ Bring the **same green DECLASSIFIED CTA animation** to the Level 02 true vault page (`/classified-vault`) with direct link to `/operation`
- ✅ Expand admin controls for new mechanics (presets + micro + treasury config)

### Implementation

**Backend (`/app/backend/vault.py`)**
- ✅ New production defaults:
  - `DEFAULT_TOKENS_PER_DIGIT = 100_000_000`
  - `DEFAULT_TOKENS_PER_MICRO = 10_000`
  - `DEFAULT_TREASURY_GOAL_EUR = 300_000`
  - `DEFAULT_EUR_USD_RATE = 1.08`
- ✅ Public state extended:
  - `tokens_per_micro`, `micro_ticks_total`
  - `treasury_eur_value`, `treasury_progress_pct`
- ✅ Admin-only state extended:
  - `treasury_goal_eur`, `eur_usd_rate`
- ✅ `apply_crack` supports dual declassification:
  - `digits_locked == num_digits` OR
  - `treasury_eur >= treasury_goal_eur` (only when `dex_mode=custom` with real price)
- ✅ `initialize_vault` soft-migration adds missing fields on existing docs
- ✅ `update_config` extended:
  - `tokens_per_micro`, `treasury_goal_eur`, `eur_usd_rate`
  - `preset: production|demo` (demo = 1K/100 fast-crack)
- ✅ Hourly tick scaled to micro-threshold and capped to ≤10% of one dial

**Backend (`/app/backend/dexscreener.py`)**
- ✅ Demo mode uses `demo_tick_tokens` scaled to micro threshold (keeps demo alive without cracking instantly at 100M)
- ✅ Custom mode applies **real estimated tokens** per poll (single event) with fractional carry

**Frontend (`CombinationDial.jsx`)**
- ✅ New props:
  - `isActive` (first unlocked dial)
  - `microTickVersion` (uses `micro_ticks_total`)
- ✅ On each micro-tick: deterministic `+1` spin with amber flash pulse
- ✅ Active dial has subtle amber emphasis

**Frontend (VaultChassis + VaultSection + ClassifiedVault)**
- ✅ Propagate `microTickVersion = micro_ticks_total` to drive micro animations
- ✅ `/classified-vault` authed view:
  - Added DECLASSIFIED CTA block matching homepage aesthetics
  - Green pulsing overlay + animated button → `/operation`
  - Added metrics: `micro-rotations`, `treasury (€)` with redacted goal display

**Frontend (AdminVault)**
- ✅ Preset buttons: `Production (100M/10K)` and `Demo (1K/100)`
- ✅ Config inputs:
  - `tokens_per_micro`
  - `treasury_goal_eur`
  - `eur_usd_rate`

**i18n (FR/EN)**
- ✅ Added:
  - `classifiedVault.microTicks`, `classifiedVault.treasury`
  - `classifiedVault.declassified.{kicker,title,subtitle,cta}`

### Testing
- ✅ Backend testing agent: **24/24 tests passed** (`/app/test_reports/iteration_10.json`)
- ✅ Regression coverage included

### Runtime Defaults (current)
- ✅ Vault: `LOCKED 0/6`
- ✅ Preset: `production` (100M / 10K)
- ✅ Dex mode: `demo`

---

## Remaining / Optional Improvements (P1)
- Refactor `server.py` (now larger) into routers (`routers/admin.py`, `routers/public.py`, `routers/webhooks.py`, `routers/vault.py`, `routers/access_card.py`)
- Recharts resize warning (cosmetic) — optional

---

## Future (P2)
- Replace client-reported `POST /api/vault/report-purchase` with a true Solana on-chain indexer/worker
- Improve DexScreener custom-mode accuracy by consuming per-trade endpoints (if available) rather than h24 deltas; or switch to direct on-chain parsing (Raydium/Orca)
- Optional: add WebSocket/SSE streaming for near-real-time vault feed updates (instead of polling)

---

## Pending Operations (memorized for later — user requested)
- **(A) Switch DexScreener mode to real token**: When $DEEPOTUS is deployed, switch `dex_mode` → `custom` and set the real Solana mint address from `/admin/vault`.
- **(B) Backend refactor**: Break `/app/backend/server.py` (now >2100 lines) into dedicated routers/modules (public/admin/webhooks/vault/access-card) without changing behavior.
- **(C) On-chain accuracy upgrade**: Replace the DexScreener h24-delta approximation with a Solana trade indexer (Raydium/Orca via Helius/Solscan or direct RPC parsing) for per-trade accuracy and robust buy volume detection.
