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
- **Status**: 🟡 PENDING

### Phase 2 — Full Landing Page Build
- Backend routes: `/api/chat`, `/api/prophecy`, `/api/whitelist`, `/api/stats`
- Frontend: Full bilingual landing with all 13 sections above, i18n, animations, deepfake aesthetic
- MongoDB collections: `whitelist`, `chat_logs`, `prophecies_cache`
- **Status**: 🟡 PENDING

### Phase 3 — Testing & Polish
- End-to-end testing via `testing_agent_v3` covering ALL user stories
- Bug fixes (all priorities)
- Final delivery via `finish`
- **Status**: 🟡 PENDING

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

---

## Current Status
- Plan created ✅
- Integration playbook ✅
- Design guidelines ✅
- POC script: **✅ PASSED** (FR + EN chat persona + prophecies)
- Backend build ✅ (`/api/chat`, `/api/prophecy`, `/api/whitelist`, `/api/stats` — all curl-verified, 100% backend tests)
- Frontend build ✅ (13 sections, bilingual FR/EN, deepfake aesthetic, all interactive features live)
- Testing ✅ (Backend 11/11 • Frontend 19/20 — only minor testid naming, feature works)
- **Delivery ✅**
