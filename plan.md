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
- Public narrative pivot: funding goal is **classified** under **PROTOCOL ΔΣ** (Black Op). **GENCOIN** is a twist revealed only after vault declassification.

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
2. **Vault (PROTOCOL ΔΣ)** — animated “classified vault” section with 6-digit combination mechanics + AI vault chassis mockup + DexScreener live activity (Phases 10–13)
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
15. **Operation Reveal Page (`/operation`)** — gate-locked until vault declassified; reveals twist + countdown + (Phase 12) cinematic “Fall of Deep State” illustration
16. **Classified Vault (Level 02) (`/classified-vault`)** — gated full-page “real vault” with accreditation + session token, displaying live activity feed (Phase 13)

---

## Tech Stack
- Backend: FastAPI + MongoDB + `emergentintegrations` (Emergent LLM)
- Frontend: React + Tailwind + shadcn/ui + framer-motion + recharts + lucide-react
- i18n: Simple Context-based FR/EN (no heavy library)
- Email: Resend + webhooks (Svix verification)
- Dex / market feed: **DexScreener API** polling (Phase 11)
- Image generation: Gemini Nano Banana (`gemini-3.1-flash-image-preview`) (Phases 10–13)
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
- ✅ Implement vault progression logic: **1 dial per 1,000 $DEEPOTUS**
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
  - `POST /api/admin/vault/config` (admin; tokens_per_digit, hourly_tick_enabled, reset)
  - `GET /api/operation/reveal` (public; returns unlocked=false unless DECLASSIFIED)
- Background task:
  - `hourly_tick_loop(db)` started at app startup (keeps vault alive)
- Chat prompt updated to reference Vault/PROTOCOL ΔΣ and never mention GENCOIN

**Frontend**
- New section inserted (non-destructive): `VaultSection` placed between Manifesto and Chat
  - 6 animated mechanical dials
  - Live activity feed
  - Redacted progress bar
  - Stage badge (LOCKED/CRACKING/UNLOCKING/DECLASSIFIED)
- New route page: `/operation`
  - Locked gate view when vault not declassified
  - Reveal view with Prophet panic + full lore + countdown to GENCOIN launch + link to `https://gencoin.xyz`
- New admin page: `/admin/vault`
  - Crack manual, config (tokens per digit, hourly tick toggle), reset, event list
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
- ✅ Art direction: black-ops / Deep State / CIA bunker vibe, matte black metal, cyan+amber LEDs, keypad+scanner, and a **central empty display panel** reserved for overlay.

**Frontend (Vault UX refactor)**
- ✅ Added component: `/app/frontend/src/components/landing/vault/VaultChassis.jsx`
  - Displays `vault_frame.png`
  - Absolutely positions 6 compact dials inside the reserved central panel
  - Adds stage badge overlay + dials counter overlay + pulsing halo behind panel
- ✅ Updated: `VaultSection.jsx`
  - Uses `VaultChassis` and displays public DEX badge when enabled: `LIVE · {dex_label}`
- ✅ Updated: `CombinationDial.jsx`
  - Added size modes (`default`, `sm`, `chassis`) for responsive overlay

**Backend (DexScreener integration)**
- ✅ New module: `/app/backend/dexscreener.py`
  - Polls DexScreener every **30s** using `httpx`
  - Selects Solana pair by **activity** (h24 buys+sells)
  - Modes:
    - `off`: skip polling
    - `demo`: default BONK mint; symbolic ticks (`1 tick per DEMO_BUYS_PER_TICK=5 new buys`, capped)
    - `custom`: configured mint; approximates buy tokens via `Δvolume_usd * buy_ratio / price_usd` and applies **1 tick per `tokens_per_digit`** with carry
  - Stores rolling baselines + carry in `vault_state` to avoid double-counting
- ✅ Extended vault models (public + admin) to include DEX fields:
  - Public: `dex_mode`, `dex_label`, `dex_pair_symbol`
  - Admin: `dex_token_address`, `dex_demo_token_address`, `dex_last_*`, `dex_carry_tokens`, `dex_error`
- ✅ New admin endpoints:
  - `POST /api/admin/vault/dex-config`
  - `POST /api/admin/vault/dex-poll`
- ✅ Startup tasks:
  - Dex loop started at startup: `asyncio.create_task(dex_mod.dex_loop(db, vault_mod))`

**Admin UX (DEX controls)**
- ✅ Updated `/admin/vault` with “DEX Live Feed · DexScreener” section:
  - Mode selector: OFF / DEMO / CUSTOM
  - Custom mint input + “Save & activate”
  - Stats cards: price, h24 buys, h24 volume, carry
  - “Force poll now” + link to DexScreener + last poll timestamp

### Current Runtime Defaults
- ✅ Vault reset state: `LOCKED 0/6`
- ✅ Dex mode: `demo` enabled by default
- ✅ Live badge visible on public vault: e.g. `LIVE · Bonk · meteora`

### Testing
- ✅ Backend-only testing agent: **22/22 tests passed** (`/app/test_reports/iteration_8.json`)
- ✅ Security verified:
  - `GET /api/vault/state` never leaks `target_combination` nor admin-only `dex_*` fields
  - Admin endpoints require JWT (401 without auth)
- ✅ Regression verified: all existing endpoints still functional

---

## Phase 12 — Mobile Vault Fix + “Fall of Deep State” Illustration (completed ✅)

### Objectives
- ✅ Fix mobile vault layout so the dials remain anchored *inside* the vault mockup (no dials rendered below the image).
- ✅ Add a new AI-generated cinematic illustration on the `/operation` reveal page depicting the Prophet panicking and chased by the RIPPLED crowd (symbolic end of the Deep State).

### Implementation

**Mobile vault anchoring fix**
- ✅ Unified vault rendering: removed the desktop/mobile split and always use `VaultChassis`.
- ✅ `VaultChassis` is responsive:
  - Mobile uses **aspect-ratio 4:3** with `object-cover object-center` to “zoom” into the central display area.
  - Desktop uses **aspect-ratio 16:9**.
  - Dial overlay coordinates are responsive via Tailwind (`left/top/width/height` with `md:` overrides).
- ✅ `CombinationDial` chassis font adjusted for small screens: `clamp(11px, 2.8vw, 42px)`.

**Operation reveal illustration**
- ✅ Script: `/app/tests/generate_prophet_chased.py`
- ✅ Asset: `/app/frontend/public/prophet_chased.png`
- ✅ Visual spec: Prophet in panic (suit + loosened red tie), diverse crowd pursuing, banners with RIPPLED logo (golden arcs + central human figure, `#E3D99F`), government architecture, apocalyptic sunset.
- ✅ Integrated into `/operation` reveal page between the panic quote and the lore.
- ✅ Added bilingual keys in i18n:
  - `operation.chasedOverlay`
  - `operation.chasedCaption`
  - `operation.chasedAlt`

### Current Runtime Defaults
- ✅ Vault reset state: `LOCKED 0/6`
- ✅ Dex mode remains `demo` enabled by default

---

## Phase 13 — Funnel NIVEAU 02 (Terminal + Carte d’accès + Vault réel) — **COMPLETED ✅**

### Objectives
- ✅ Keep the public vault as-is (PROTOCOL ΔΣ chassis + dials + DexScreener feed).
- ✅ Replace the declassification CTA behavior:
  - Instead of navigating directly to `/operation`, clicking the CTA opens a **sarcastic CRT terminal popup**.
  - The terminal denies “true vault” access for Level 01 and prompts the user to request **Level 02**.
- ✅ Implement Level 02 upgrade email:
  - Generate an accreditation code
  - Send a second email containing a personalized **Deep State access card** (AI template + overlays)
- ✅ Create a full-page “real vault” page `/classified-vault`:
  - Gate by accreditation code
  - Issue a 24h session token
  - Show the live combination + activity feed as the “true vault”
- ✅ Ensure deliverability   observability:
  - Resend delivery tracked via Svix webhooks
  - Access card email events visible via admin `/admin/emails`

### Implementation

**AI template (Access Card)**
- ✅ Script: `/app/tests/generate_access_card_template.py`
- ✅ Output: `/app/backend/assets/access_card_template.png` (~694KB)
- ✅ Visual spec: matte black covert-agency card, cyan/amber security accents, empty slots for name/accred/dates/QR.

**Backend (Access Card system)**
- ✅ New module: `/app/backend/access_card.py`
  - Accreditation format: `DS-02-XXXX-XXXX-XX`
  - Idempotent per email (same email → same accreditation)
  - PIL overlay pipeline:
    - Masks template placeholders (including “EMPTY BANNER” artifacts)
    - Overlays NAME, ACCREDITATION, issue/expire dates, QR code, microtext
  - 24h access sessions (`access_sessions`)
- ✅ New MongoDB collections:
  - `access_cards` (email → accreditation, display_name, card_path, issued_at, expires_at)
  - `access_sessions` (session_token, accred, display_name, expires_at)
- ✅ New API endpoints:
  - `POST /api/access-card/request` (public; generates card + sends email)
  - `POST /api/access-card/verify` (public; accred → session token)
  - `GET /api/access-card/status` (public; validates X-Session-Token)
  - `GET /api/access-card/image/{accred}` (public; serves PNG)
- ✅ Email templates:
  - Added bilingual template in `/app/backend/email_templates.py`:
    - `render_access_card_email` + `access_card_subject`
  - Email includes inline CID image attachment (card) + accreditation code + CTA to `/classified-vault?code=...`

**Frontend (Terminal + Real vault page)**
- ✅ New component: `/app/frontend/src/components/landing/vault/TerminalPopup.jsx`
  - CRT terminal modal with scanlines + phosphor glow + blinking cursor
  - 5 phases: denied (typing) → form → sending → success → error
  - Form collects email + optional agent name
  - Calls `/api/access-card/request`
- ✅ VaultSection behavior update:
  - DECLASSIFIED CTA now opens `TerminalPopup` (instead of `/operation`)
  - Added two shortcuts always visible:
    - “Demander un niveau d'accréditation” (opens terminal)
    - “J’ai déjà un numéro d'accréditation” (link to `/classified-vault`)
- ✅ New route + page: `/classified-vault` (`/app/frontend/src/pages/ClassifiedVault.jsx`)
  - Gate UI: accreditation input (auto-prefilled by `?code=`)
  - Verify via `/api/access-card/verify`
  - Persist session in `localStorage` (`deepotus_access_session`)
  - Authed full-page “true vault” view:
    - Session stripe header (expires + logout)
    - Large 6 dials + metrics + live feed + external link
- ✅ Router update: `/app/frontend/src/App.js` now includes `/classified-vault`
- ✅ i18n additions:
  - `terminal.*`
  - `classifiedVault.*`
  - `vault.requestClearance` + `vault.alreadyHaveCode`

### Testing
- ✅ Backend testing agent: **41/41 tests passed** (`/app/test_reports/iteration_9.json`)
  - 19 new access-card tests + 22 regressions
- ✅ Email test to `olistruss639@gmail.com` validated:
  - `access_card.sent` + `email.sent` + `email.delivered` visible in admin email events (Svix verified)

### Current Runtime Defaults
- ✅ Vault reset state: `LOCKED 0/6`
- ✅ Dex mode: `demo` enabled by default
- ✅ Terminal + access-card system ready for production demo

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
