# Landing Page $DEEPOTUS — Memecoin IA Prophète (Deep State POTUS)

## User-Validated Configuration
- **Ticker**: `$DEEPOTUS` (Deep State POTUS)
- **Language**: Bilingue FR/EN avec toggle
- **Art direction**: Hybride — haut de page institutionnel/MiCA-compliant + bas de page brutalist crypto-degen/meme + esthétique deepfake/IA.
- **LLM**: Emergent LLM key (validé)
- **Go-to-market**: lancement sur **Pump.fun**, puis migration automatique vers **Raydium**
- **Intro Deepstate** (bonus, validé): **14s** · cooldown **24h** · **aucun audio** · terminaux **mix FR/EN**

---

## Original Problem Statement (Full context preserved)

Le projet s’inscrit dans un cadre « dossier de cadrage » : $DEEPOTUS est un memecoin Solana fonctionnant comme **véhicule de trésorerie transparent** avec disclosures alignés MiCA.

### Narrative core
- IA Prophète cynique, lucide, moqueuse, annonçant récession/dépression, chaos géopolitique, fragilité des marchés.
- Repositionné comme **candidat Deep State à la présidence du Monde**.
- Pivot public: objectif de financement **classifié** via **PROTOCOL ΔΣ** (Black Op).
- **GENCOIN** est un twist révélé uniquement après déclassification, via `/api/operation/reveal` et la page `/operation`.
- Funnel post-déclassification : accès au “vrai coffre” derrière **Niveau 02** (carte d’accès email) sur `/classified-vault`.

### Financial parameters (must remain visible on site where applicable)
- Chain: **Solana**
- Supply: **1,000,000,000**
- Target price: **€0.0005** (cible MiCA / FDV €500k)
- FDV: **€500,000**
- Initial LP: **Initiation Deep State** (montant masqué publiquement), première fenêtre de prix post-mint

> Note: l’objectif explicite (ex: €300,000 / 3 semaines) est volontairement **caché** dans le narratif public et remplacé par la mécanique classifiée du coffre.

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
- **3%** total → **2%** Operation/compliance budget + **1%** liquidité/marketing
- Cap explicite + baisse de taxe une fois l’objectif atteint (reformulé : “quand le Coffre s’ouvre”)

### Liquidity plan
- **Mint Pump.fun** (prix plancher bonding curve)
- **Initiation Deep State** quelques heures après le mint → prix de référence simulé
- Migration Pump.fun → Raydium (roadmap Δ02)

### Anti-dump measures
- LP lock ou burn après migration
- Treasury en **multisig** + **timelock** + caps de vente journaliers/hebdo
- Split des ventes
- Pas d’airdrop massif / pas de distribution KOL débloquée autour de la migration

### MiCA compliance disclosures (prominent)
- Token **hautement spéculatif**
- **Aucune promesse** de rendement
- **Pas un stablecoin**, **pas un titre financier**
- Fonction: véhicule de trésorerie transparent + structure, gouvernance, risques

### Honest success probabilities
- Taux de succès memecoin global: ~1.4%
- Estimation exécution forte: 2–3%
- Objectif atteint sur la fenêtre de lancement: ~1% (ordre de grandeur)

---

## Target audiences
- **Investisseurs sérieux**: transparence MiCA, tokenomics, risques, roadmap, vesting
- **Crypto-degens**: énergie meme, persona IA Prophète, shitpost/viral, esthétique deepfake

---

## Sections / features to build

1. **Hero** — bannière candidat présidentiel, toggle FR/EN, CTA, countdown
2. **DeepStateIntro** — page d’introduction hack-style (14s, show-once/24h) avant landing
3. **Prophet pinned whisper** — citation épinglée ultra-visible post-Hero (loyauté)
4. **Vault (PROTOCOL ΔΣ)** — coffre animé 6 digits + chassis IA + feed activité on-chain + funnel Niveau 02
5. **AI Prophet Live Chat** — Emergent LLM, persona FR/EN
6. **Prophecies Feed** — punchlines auto-refresh
7. **Mission Section** — framing MiCA + structure, reframé PROTOCOL ΔΣ
8. **Interactive Tokenomics** — pie chart (Recharts)
9. **Liquidity & Treasury Transparency** — timeline + anti-dump (**carrousel full-width**)
10. **ROI Simulator** — **simulateur dynamique** : graphe live + bandeau risque défilant + marqueurs roadmap + modèle Pump.fun+initiation (MiCA) + masquage montant + devise localisée
11. **Roadmap** — timeline
12. **FAQ** — MiCA, tax, treasury, vesting, risques, “pourquoi l’objectif est classifié”
13. **Whitelist / Email Capture** — MongoDB
14. **Social Mockups** — X/Twitter, Telegram, Discord
15. **Risk Disclaimer Footer** — MiCA + bilingue
16. **Language Switcher** — FR ↔ EN
17. **Operation Reveal Page (`/operation`)** — unlock quand DECLASSIFIED
18. **Classified Vault (`/classified-vault`)** — gate Niveau 02 + session token + “true vault”
19. **Admin Dashboard** — JWT/2FA + gestion vault + scheduler bots + **loyalty engine**

---

## Tech Stack
- Backend: FastAPI + MongoDB (Motor)
- Frontend: React + Tailwind + shadcn/ui + framer-motion + recharts + lucide-react
- i18n: Context FR/EN
- Email: Resend + webhooks (Svix)
- **On-chain feed (authoritative)**: **Helius Enhanced Transactions (webhooks + catch-up polling)**
- Dex feed (fallback): DexScreener polling (off/demo/custom) — **bypass automatique quand `dex_mode=helius`**
- Images: Gemini Nano Banana (gemini-3.1-flash-image-preview)
- Image processing: Pillow (PIL) + qrcode
- Automation: APScheduler (backend) + Admin UI

---

## Phases

### Phase 1 — Core POC (AI Prophet LLM Persona) — LIGHT POC
- ✅ Script POC validant Emergent LLM + FR/EN + prophéties
- **Status**: ✅ COMPLETED

### Phase 2 — Full Landing Page Build
- ✅ Backend: `/api/chat`, `/api/prophecy`, `/api/whitelist`, `/api/stats`
- ✅ Frontend: landing bilingue animée
- ✅ MongoDB: `whitelist`, `chat_logs`, `counters` (+ autres)
- **Status**: ✅ COMPLETED

### Phase 3 — Testing & Polish
- ✅ End-to-end tests + correctifs
- **Status**: ✅ COMPLETED

---

## User Stories (ALL must be validated in testing)

1. Compréhension immédiate MiCA-aware + gouvernance + risques
2. Meme energy + persona Deep State POTUS
3. FR/EN switch instant
4. Chat live in-character
5. Prophéties auto-refresh
6. Tokenomics interactifs
7. **Simu ROI dynamique** : graphe interactif + bandeau risque défilant + marqueurs roadmap + Pump.fun mint très bas + Initiation Deep State (montant masqué) + devise localisée
8. Countdown
9. Timeline liquidité + anti-dump
10. Whitelist email OK
11. Risk disclaimer MiCA
12. Roadmap visible
13. Probabilités de succès honnêtes
14. Social mockups
15. Admin: emails transactionnels + observabilité webhook
16. Coffre classifié progressif (stages)
17. `/operation` lock/unlock + twist
18. Coffre illustré (chassis IA)
19. Activité marché reflétée (live)
20. Admin: switch mode feed + force poll
21. Mobile: dials ancrés dans l’image
22. Illustration “Fall of Deep State” sur `/operation`
23. Terminal CRT gaslighting avant Level 02
24. Request Level 02 + réception carte d’accès email
25. Gate `/classified-vault` + token session
26. True vault: activité live + progression
27. Gate door keypad immersif (desktop/mobile)
28. Reuse VaultChassis sur true vault
29. Animation CTA DECLASSIFIED identique + lien `/operation`
30. **Micro-rotations (100K tokens) + locks majeurs (100M tokens)**
31. **Per-trade on-chain indexer**: activité reflétée par swaps réels (webhooks) + dédup
32. **Mode démo**: avant lancement, tracker BONK sans casser la progression du coffre
33. **Carrousel Transparence**: backgrounds IA propres + tampon CSS “CONFIDENTIEL” sans texte halluciné
34. **SEO/OG**: site partageable (aperçus X/Telegram/Discord) et indexable correctement
35. **Accès NIVEAU 02**: lien email/QR doit forcer l’atterrissage sur la page digicode
36. **Public Stats**: ne jamais exposer la date de lancement, remplacée par un dossier “REDACTED”
37. **Loyalty narrative**: citation Prophète ultra visible + bots hints progressifs + email #3 post-N2 (sans nommer GENCOIN)
38. **DeepStateIntro**: écran noir + fenêtres terminal + glitch + fade vers landing en ≤15s, show-once/24h, skip + reduced-motion

---

## Current Status
- Plan ✅
- Backend ✅
- Frontend ✅
- Testing ✅
- **Delivery ✅**
- **Architecture backend modulaire ✅ (Opération B terminée)**
- **Hardening code quality ✅ (Phase 17 terminée)**
- **Indexer Solana per-trade via Helius ✅ (Phase 18 terminée, LIVE)**
- **Brand assets V4 + coin ΔΣ ✅ (Phase 19 terminée)**
- **Transparence On-chain carrousel full-width + images régénérées ✅ + VALIDATION VISUELLE ✅**
- **SEO/OG pack ✅** (Meta + OG + manifest + robots/sitemap + JSON-LD + sync FR/EN)
- **Roadmap “dossier classifié” ✅**
- **Fix coffre NIVEAU 02 ✅** (`?code=` force digicode)
- **Public Stats: date de lancement masquée ✅**

### ROI Simulator (extended) — ✅ COMPLETED (validated visually)
- **Modèle Pump.fun + Initiation Deep State**:
  - Mint floor: `MINT_PRICE_EUR = 0.0000005`
  - Initiation event: `INJECTION_PRICE_EUR = 0.000002` à `FOUNDER_INJECTION_DAY = 0.15` (≈ 3–4h)
  - Prix de référence calculateur: `LAUNCH_PRICE_EUR = 0.000002`
  - Cible MiCA: `TARGET_PRICE_EUR = 0.0005` (FDV €500k)
- **Scénarios canonisés**: brutal ×0.1 / base ×25 / optimistic ×250
- **Chart**:
  - YAxis **log scale**
  - 4 marqueurs roadmap (Δ01..Δ04) + légende sous le graphe
  - `ReferenceDot` cyan sur l’événement d’initiation
  - Tooltip supporte jours fractionnaires
- **Aesthetic + compliance**:
  - bandeau risque en marquee CSS
  - label: “INITIATION DEEP STATE” (FR) / “DEEP STATE INITIATION” (EN)
  - **montant masqué**: `xxxx€` (FR) / `xxxx$` (EN)
  - **devise localisée** partout (FR=€, EN=$)

### Vault production tuning — ✅ COMPLETED
- **Micro-rotations**: `10,000` → **`100,000` tokens**
- Backend default + fallback demo + AdminVault default + Mongo live doc mis à jour
- API confirmé: `GET /api/vault/state` → `tokens_per_micro: 100000`

### Loyalty narrative rollout (Sprints 2/3/4) — ✅ COMPLETED + validated

#### Sprint 2 — Citation épinglée du Prophète ✅
- Composant `ProphetPinnedWhisper` inséré juste après `Hero` (`Landing.jsx`)
- i18n FR/EN: `prophetWhisper.{kicker,classification,quote,signature,footnote}`
- data-testids: `prophet-pinned-whisper`, `prophet-pinned-quote`, `prophet-pinned-signature`, `prophet-pinned-classification`, `prophet-pinned-footnote`

#### Sprint 3 — Bots vault-aware loyalty hints ✅
- Module `core/loyalty.py`:
  - 5 tiers: silent (0–25) / subtle (25–50) / explicit (50–75) / loud (75–90) / reward (90+)
  - hints FR/EN curated
  - `compute_progress_percent()` depuis `vault_state`
  - `get_loyalty_context()` (+ `force=True` pour preview admin)
- Hook dans `core/prophet_studio.py:generate_post()`:
  - Injection d’une **directive de loyauté** dans `extra_context` (try/except, non bloquant)
  - Jamais de nom de token futur, jamais de date/montant, jamais d’incitation à acheter
- Toggle: `bot_config.loyalty.hints_enabled` (default false)
- Admin endpoints:
  - `GET /api/admin/bots/loyalty` (status + tiers + sample)
- Admin UI (`AdminBots.jsx` → Config tab):
  - Section “Loyalty engine · vault-aware hints” + preview + liste tiers + toggles

#### Sprint 4 — Email #3 « Allégeance notée » ✅
- Template HTML: `email_templates.py:render_loyalty_email()` + `loyalty_email_subject()`
- Module `core/loyalty_email.py`:
  - `_generate_prophet_message()` via LLM (provider/model de bot_config) + fallback curated
  - `list_pending(delay_hours)` sur `access_cards`
  - `_send_one()` → Resend + audit `email_events` + stamp `access_cards.loyalty_email_sent_at`
  - `loyalty_email_tick()` scheduler
  - `force_send_loyalty()` + `get_loyalty_email_stats()`
- Scheduler:
  - Job `loyalty_email` toutes les 30 min (`interval[0:30:00]`)
- Toggles:
  - `bot_config.loyalty.email_enabled` (default false)
  - `bot_config.loyalty.email_delay_hours` (default 12h, range 1–168)
- Admin endpoints:
  - `GET /api/admin/bots/loyalty/email-stats`
  - `POST /api/admin/bots/loyalty/test-send` (force send)
- Admin UI (`AdminBots.jsx`):
  - Toggle email_enabled + delay + stats + form “Force-send now” + panneau résultat
- Validation: testing agent a réussi un envoi via Resend (status=sent).

#### Bug fix during testing ✅
- `PUT /api/admin/bots/config` ignorait `payload.loyalty` → `empty_patch`.
  - Patch ajouté: merge `payload.loyalty` dans `patch_dict`.
  - `_shape_config()` + `BotConfigResponse` mis à jour pour exposer `loyalty`.
  - Fix confirmé via curl + UI.

### Sprint Bonus — DeepStateIntro (entrée hack-style) — ✅ COMPLETED + validated

#### Objectif
Créer une **page d’introduction mystérieuse** sur première visite (≤15s) : écran noir → fenêtres terminal “hack” → glitch → fondu vers la landing.

#### Livraison (14s)
- Écran noir + prologue "PROTOCOL ΔΣ · INITIATING SECURE BOOT..."
- 4 fenêtres terminal (kernel / nmap / handshake / access granted)
- Matrix rain (canvas) en arrière-plan
- Glitch RGB + flash blanc (200ms)
- Fade out vers landing (révélée en dessous)

#### Architecture
- `/app/frontend/src/components/intro/`
  - `DeepStateIntro.jsx` — orchestrateur timeline + skip + 24h cooldown + `?intro=force`
  - `TerminalWindow.jsx` — chrome rétro + typewriter effect
  - `MatrixRain.jsx` — canvas 2D + trails
  - `GlitchOverlay.jsx` — RGB split + scanlines + flash
  - `hackScripts.js` — scripts curated (mix FR/EN)
- CSS (`/app/frontend/src/index.css`):
  - `@keyframes deepstate-rgb-jitter`, `@keyframes deepstate-flash-keys`
  - `.deepstate-glitch-rgb`, `.deepstate-glitch-flash`, `.deepstate-scanlines`
  - `prefers-reduced-motion: reduce` → animations coupées

#### Features
- localStorage `deepstate.intro.lastSeenAt` (cooldown 24h)
- Skip button bottom-right (FR: "PASSER · ESC" / EN: "SKIP · ESC")
- ESC key handler + click anywhere
- `?intro=force` param
- Auto-skip si `prefers-reduced-motion: reduce`
- Body scroll lock pendant intro
- Corner badge progression "DEEPSTATE.SYS · X%"

#### Validation
- eslint OK
- webpack compiled successfully
- screenshots keyframes validés
- cooldown 24h confirmé
- skip confirmé

---

## Phase 8 — 2FA, Heatmap, Full Export, Email Events Drill-down, Cooldown Blacklist — completed ✅
- ✅ 2FA TOTP + backup codes + enable/disable
- ✅ Heatmap activité
- ✅ Export CSV whitelist complet
- ✅ Drill-down email events
- ✅ Blacklist cooldown + auto-unblock

---

## Phase 9 — Resend Webhook Finale (Svix) + Test Emails — completed ✅
- ✅ `RESEND_WEBHOOK_SECRET` injecté
- ✅ Webhook Resend signé et vérifié
- ✅ Endpoint admin `POST /api/admin/test-email`
- ✅ Events persistés + visibles

---

## Phase 10 — PROTOCOL ΔΣ (Coffre classifié + reveal twist) — COMPLETED ✅
- ✅ Vault module + collections + endpoints
- ✅ `/operation` reveal unlocké uniquement au stage DECLASSIFIED
- ✅ Hourly tick
- ✅ Sécurité : combinaison cible jamais exposée publiquement

---

## Phase 11 — AI Vault Mockup + DexScreener Live Activity — completed ✅
- ✅ Chassis IA + overlay dials responsive
- ✅ DexScreener modes (off/demo/custom)
- ✅ Admin dex-config + dex-poll

---

## Phase 12 — Mobile Vault Fix + “Fall of Deep State” Illustration — completed ✅
- ✅ Fix responsive
- ✅ Illustration prophet_chased

---

## Phase 13 — Funnel NIVEAU 02 (Terminal + Carte d’accès + Vault réel) — COMPLETED ✅
- ✅ Terminal CRT modal
- ✅ Carte d’accès (PIL + QR) + email Resend
- ✅ `/classified-vault` gate + session

---

## Phase 14 — AI Door Gate + VaultChassis Reuse — COMPLETED ✅
- ✅ door_keypad + input ancré
- ✅ continuité UI true vault

---

## Phase 15 — Production Mechanics + DECLASSIFIED Animation Parity — COMPLETED ✅
- ✅ 100M tokens/digit + **100K micro** + goal 300K€ (custom)
- ✅ DexScreener demo/custom adaptés
- ✅ CTA DECLASSIFIED sur `/classified-vault`

---

## Phase 16 — Opération B: Refactor backend monolith → routers/core — **COMPLETED ✅**

---

## Phase 17 — Code Quality Hardening (sécurité + maintenabilité) — **COMPLETED ✅**

---

## Phase 18 — Task C (P2) : Indexer Solana per-trade via Helius — **SHIPPED ✅ (LIVE)**

---

## Phase 19 — Brand Assets (V4 + monogram ΔΣ + pièce en or) — **COMPLETED ✅**

---

## Phase 20 — Pré-lancement Polish Pack (UI + Roadmap + SEO/OG) — **COMPLETED ✅**

---

## Phase 21 — Code Quality Pack (Tier 1 + Tier 3 + Tier 4) — **PARTIALLY COMPLETED / ONGOING**

### Objectif
- Continuer le refactor structure-only + migration TS progressive sans casser l’existant.

### État actuel
- ✅ Fondations TypeScript (tsconfig + allowJs + base types)
- ✅ Splits partiels React (Hero/Tokenomics/ClassifiedVault)
- ⏳ Backlog restant: conversions TS + splits gros composants Admin.

---

## Remaining / Optional Improvements (P1)

### (A) Switch vers le vrai mint $DEEPOTUS (post-launch)
- ⏳ Remplacer le mint BONK démo par le vrai mint
- ⏳ `POST /api/admin/vault/helius-register` avec le vrai mint

### Bots — phases bloquées (attente credentials)
- ⏳ Phase 3: Telegram Bot API (token + chat_id)
- ⏳ Phase 4/5: X API v2 (OAuth2) + KOL list
- ⏳ Trading bot refs: liens BonkBot/Maestro/Trojan

---

## Future (P2+)
- (Option) Parse Raydium/Orca plus profond
- (Option) métriques agrégées Helius

---

## Sprints planifiés (next)

### Sprint 5 — Continuation backlog TypeScript (NEXT)
- Convertir en priorité:
  - `Admin.jsx`, `AdminBots.jsx`, `AdminVault.jsx`, `TerminalPopup.jsx`
- Continuer selon `TODO_TYPESCRIPT.md` (~60+ fichiers)
- Validation:
  - build CRA OK
  - smoke navigation (Landing/Admin/ClassifiedVault/PublicStats)

### Sprint 6 — Migration / déploiement
- Audit pré-déploiement
- Choix plateforme (Vercel/Render/Railway)
- Hardening final + variables d’env

---

## Pending Operations (memorized for later — user requested)
- ✅ (B) Backend refactor: terminé
- ✅ (Hardening): terminé
- ✅ (C) On-chain accuracy upgrade: terminé
- ✅ (D) ROI Simulator dynamique (extended): terminé
- ✅ (E) Vault production tuning: terminé (micro-rotations 100K)
- ✅ (F) Loyalty narrative rollout: terminé (Sprints 2/3/4)
- ✅ (G) DeepStateIntro (entrée hack-style 14s): terminé
- ⏳ (A) Switch à $DEEPOTUS réel: dès que le mint Solana est connu

---

## Testing strategy (Phase 21)
- Après **21a (Python quick wins)**:
  - ruff/pyflakes clean
  - smoke test backend
- Après **21b (React quick wins)**:
  - eslint clean
  - screenshots Landing + ClassifiedVault + PublicStats + Admin
- Après **21c/21d**:
  - non-régression emails + bots preview + admin login
- Après **21e (TypeScript)**:
  - build CRA OK + navigation smoke
