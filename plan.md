# Landing Page $DEEPOTUS — Memecoin IA Prophète (Deep State POTUS) finançant GENCOIN

## User-Validated Configuration
- **Ticker**: `$DEEPOTUS` (Deep State POTUS)
- **Language**: Bilingual FR/EN with toggle
- **Art direction**: Hybrid — institutional/MiCA-compliant top + brutalist crypto-degen/meme bottom + deepfake/AI-generated aesthetic throughout. The AI Prophet is positioned as a **candidate for President of the entire World**, the chosen one of the Deep State to lead humanity.
- **LLM**: Emergent LLM key (user confirmed — free integration)
- **All interactive features**: live chat, prophecies feed, tokenomics pie, ROI sim, countdown, roadmap, FAQ, whitelist, social mockups

## Original Problem Statement (Full context preserved)

The project lives inside the framework of a comprehensive dossier de cadrage. The memecoin $DEEPOTUS is a Solana token functioning as a **transparent treasury vehicle** to finance development, compliance, and regulatory costs of the future main token **GENCOIN**, under MiCA alignment.

### Narrative core
- Cynical, lucid, mocking AI prophet announcing global recession, potential depression, geopolitical disorder, market fragility
- Reframed for $DEEPOTUS as **the Deep State's chosen presidential candidate for the entire World**
- Inspirations: Dogecoin (community viral), Turbo/TURBO (first memecoin co-designed with GPT-4), Truth Terminal/GOAT (AI as autonomous narrative actor)

### Financial parameters (MUST appear on site)
- Chain: **Solana**
- Supply: **1,000,000,000** (1B)
- Target price: **€0.0005**
- FDV: **€500,000**
- Fundraising goal: **€300,000 in 3 weeks**
- Initial LP: **€2,000** at J0 → **€10,000** at J+2 (~2M tokens injected initially)

### Tokenomics (30% Treasury scenario — final)
| Category | Allocation |
|---|---|
| Liquidity / DEX | 10–15% |
| Project Treasury (GENCOIN + MiCA) | **30%** |
| Marketing / KOL / partnerships | 10% |
| Airdrops / community | 20% |
| AI / lore reserve | 10% |
| Team / advisors (vesting) | 15–20% |

### Transaction tax
- **3%** total → **2%** GENCOIN/compliance + **1%** liquidity/marketing
- Clear cap, tax reduction once goal reached

### Liquidity plan
- **J0**: LP €2K symmetric (~€1K memecoin + ~€1K SOL/USDC), ~2M tokens in pool
- **J+2**: Scale LP €2K → €10K (net +€8K)
  - ~€6K from controlled Treasury sale (~12M tokens = ~4% of 300M Treasury) split into small blocks
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
- Function: **transparently finance compliance and dev costs of the GENCOIN environment**

### Honest success probabilities (MUST display honestly)
- Global memecoin success rate: ~1.4%
- Qualitative estimate for strong execution: 2–3%
- Hitting €300K in 3 weeks: ~1% (prudent order of magnitude)

## Target audiences
- **Serious investors**: Need MiCA transparency, clear tokenomics, risk disclosure, roadmap, team info, vesting
- **Crypto-degen community**: Need meme energy, AI prophet persona, viral/shitpost tone, deepfake aesthetic

## Sections / features to build

1. **Hero** — Deepfake AI Prophet President candidate banner, bilingual toggle, main CTA ("Join the Deep State"), countdown to launch, $DEEPOTUS ticker big
2. **AI Prophet Live Chat** — Emergent LLM, in-character cynical Deep State POTUS candidate, bilingual
3. **Auto-refreshing Prophecies Feed** — LLM-generated apocalyptic one-liners
4. **Interactive Tokenomics** — Recharts pie with hover details for every allocation
5. **GENCOIN Mission Section** — Why this memecoin funds GENCOIN, MiCA framing
6. **Liquidity & Treasury Transparency** — Visual J0 → J+2 timeline, anti-dump measures explained
7. **ROI Simulator** — Investment input → theoretical tokens, scenarios, honest risk warning
8. **Roadmap** — Visual timeline with launch, LP scaling, GENCOIN milestones
9. **FAQ** — MiCA compliance, tax, treasury, team, vesting, risks
10. **Whitelist / Email Capture** — Stored in MongoDB
11. **Social Mockups** — X/Twitter, Telegram, Discord (faux handles)
12. **Risk Disclaimer Footer** — Full MiCA-compliant language, bilingual
13. **Language Switcher** — FR ↔ EN toggle (entire site)

## Tech Stack
- Backend: FastAPI + MongoDB + `emergentintegrations` (Emergent LLM)
- Frontend: React + Tailwind + shadcn/ui + framer-motion + recharts + lucide-react
- i18n: Simple Context-based FR/EN (no heavy library)

---

## Phases

### Phase 1 — Core POC (AI Prophet LLM Persona) — **LIGHT POC**
Single Python script (`/app/tests/test_core.py`) that validates:
- Emergent LLM integration works
- Chat persona stays in character in **FR + EN** (cynical Deep State POTUS candidate)
- Prophecy generation is memorable/memetic
- Language switching preserves persona
- **Status**: ✅ COMPLETED (PASSED)

### Phase 2 — Full Landing Page Build
- Backend routes: `/api/chat`, `/api/prophecy`, `/api/whitelist`, `/api/stats`
- Frontend: Full bilingual landing with all 13 sections above, i18n, animations, deepfake aesthetic
- MongoDB collections: `whitelist`, `chat_logs`, `prophecies_cache`
- **Status**: ✅ COMPLETED

### Phase 3 — Testing & Polish
- End-to-end testing via `testing_agent_v3` covering ALL user stories
- Bug fixes (all priorities)
- Final delivery via `finish`
- **Status**: ✅ COMPLETED

---

## User Stories (ALL must be validated in testing)

1. As a **serious investor**, I land on the site and immediately grasp it is a MiCA-aware memecoin funding a larger GENCOIN project
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
12. As a **visitor**, I see a clear roadmap with GENCOIN milestones
13. As a **skeptical reader**, I see honest success probabilities (1.4% / 2–3% / ~1%)
14. As a **visitor**, I see visible social mockups (X, Telegram, Discord)
15. As an **admin**, I can securely send transactional emails (welcome + test) and observe lifecycle events (sent/delivered/bounced) captured via signed webhooks

---

## Current Status
- Plan created ✅
- Integration playbook ✅
- Design guidelines ✅
- POC script: **✅ PASSED** (FR + EN chat persona + prophecies)
- Backend build ✅ (landing + admin — 17/17 tests)
- Frontend build ✅ (13 sections, bilingual, deepfake aesthetic — 22/22 tests)
- Testing: **✅ 100% / 100%** (both iterations)
- **Delivery ✅**

## Phase 8 — 2FA, Heatmap, Full Export, Email Events Drill-down, Cooldown Blacklist (completed ✅)
- ✅ **2FA TOTP** — pyotp + qrcode. Optional enable/disable depuis le dashboard admin. Setup flow complet : scan QR → 10 backup codes → verify 6-digit → enabled. Login protégé : password + TOTP code obligatoire quand activé. Backup codes supportés (consommés une seule fois). UI modal dédiée.
- ✅ **Activity heat-map** sur `/stats` — 7 jours (Lun/Mon..Dim/Sun) × 24 heures UTC, calculé sur les 30 derniers jours, intensité color-scaled teal, légende "Moins/Less → Plus/More", tooltip par cellule.
- ✅ **Full whitelist export** — Bouton "Export ALL (N)" qui télécharge la totalité de la whitelist en CSV via `/api/admin/whitelist/export` (media_type + Content-Disposition attachment).
- ✅ **Page `/admin/emails`** — Drill-down des événements webhook Resend avec filtre chips par type (`email.sent`, `email.delivered`, `email.bounced`, etc. colorés), filtre recipient, table paginée, lien back-to-cabinet.
- ✅ **Cooldown blacklist** — Champ `cooldown_days` optionnel sur l'ajout manuel et l'import CSV. `cooldown_until` stocké sur le doc blacklist. Auto-unblock lazy sur `POST /api/whitelist` si cooldown expiré. Table admin affiche "unlocks DATE" en amber ou badge "PERMANENT".

## Phase 9 — Resend Webhook Finale (Svix) + Test Emails (completed ✅)
Objectif : finaliser la boucle **emails sortants** → **webhooks entrants signés** → **observabilité admin**.

### Implémentation (révisée / finalisée)
1. ✅ **Injection du secret webhook**
   - Ajout de `RESEND_WEBHOOK_SECRET=whsec_+I+HgWL6ornO/mxuFljrruzFqJQOmauK` dans `/app/backend/.env`.
2. ✅ **Redémarrage backend**
   - `supervisorctl restart backend` pour recharger l’environnement.
3. ✅ **Option (a) — Flow whitelist classique**
   - Appel `POST /api/whitelist`.
   - Note : si l’email existe déjà, l’API ne renvoie pas de nouvel envoi. Pour éviter toute pollution et garantir un nouvel envoi tout en livrant dans la même inbox Gmail, usage du **plus-addressing**.
   - Test exécuté avec `olistruss639+whitelist@gmail.com` (livré dans la boîte `olistruss639@gmail.com`).
4. ✅ **Option (b) — Endpoint admin dédié (test propre)**
   - Création de `POST /api/admin/test-email` (JWT admin requis) pour envoyer un email de test **sans** créer d’entrée whitelist.
   - Ajout d’un event interne `admin.test.sent` dans `email_events` pour corrélation.
5. ✅ **Vérification observabilité côté admin**
   - Vérification via `GET /api/admin/email-events`.
   - Événements confirmés : `email.sent` + `email.delivered` pour les 2 emails.

### Critères d’acceptation (atteints ✅)
- ✅ Envoi Resend fonctionne depuis le sender **`wcu@deepotus.xyz`** (adresse inchangée).
- ✅ Endpoint webhook `/api/webhooks/resend` reçoit et **valide la signature Svix** via `RESEND_WEBHOOK_SECRET`.
- ✅ Les événements `email.sent` et `email.delivered` sont persistés dans `email_events` et visibles dans l’admin.

## Phase 9 Testing
- Backend: ✅ Webhook signing + event persistence validés (email.sent / email.delivered)
- Admin: ✅ endpoint `/api/admin/test-email` opérationnel (JWT requis)

---

## Remaining / Optional Improvements (P1)
- Refactor `server.py` (actuellement volumineux ~1500+ lignes) en routers dédiés (`routers/admin.py`, `routers/public.py`, `routers/webhooks.py`) pour améliorer maintenabilité.
- Warning Recharts au resize (cosmétique, non bloquant) : optionnel.
