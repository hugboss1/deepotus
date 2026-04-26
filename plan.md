# Landing Page $DEEPOTUS — Memecoin IA Prophète (Deep State POTUS)

## User-Validated Configuration
- **Ticker**: `$DEEPOTUS` (Deep State POTUS)
- **Language**: Bilingue FR/EN avec toggle
- **Art direction**: Hybride — haut de page institutionnel/MiCA-compliant + bas de page brutalist crypto-degen/meme + esthétique deepfake/IA.
- **LLM**: Emergent LLM key (validé)
- **Fonctionnalités interactives**: chat, prophéties, tokenomics interactifs, simulateur ROI, countdown, roadmap, FAQ, whitelist, social mockups
- **Narratif**: PROTOCOL ΔΣ (Black Op) + coffre électronique gamifié ; **GENCOIN** n’apparaît qu’au twist `/operation`
- **Go-to-market**: lancement sur **Pump.fun**, puis migration automatique vers **Raydium**

---

## Original Problem Statement (Full context preserved)

Le projet s’inscrit dans un cadre « dossier de cadrage » : $DEEPOTUS est un memecoin Solana fonctionnant comme **véhicule de trésorerie transparent** avec disclosures alignés MiCA.

### Narrative core
- IA Prophète cynique, lucide, moqueuse, annonçant récession/dépression, chaos géopolitique, fragilité des marchés.
- Repositionné comme **candidat Deep State à la présidence du Monde**.
- Inspirations: Dogecoin (viral), TURBO (co-design GPT-4), Truth Terminal/GOAT (IA acteur narratif).
- Pivot public: objectif de financement **classifié** via **PROTOCOL ΔΣ** (Black Op).
- **GENCOIN** est un twist révélé uniquement après déclassification, via `/api/operation/reveal` et la page `/operation`.
- Funnel post-déclassification : accès au “vrai coffre” derrière **Niveau 02** (carte d’accès email) sur `/classified-vault`.

### Financial parameters (must remain visible on site where applicable)
- Chain: **Solana**
- Supply: **1,000,000,000**
- Target price: **€0.0005**
- FDV: **€500,000**
- Initial LP: **€2,000** à J0 → **€10,000** à J+2 (~2M tokens injectés initialement)

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
- **J0**: LP €2K symmetric (~€1K memecoin + ~€1K SOL/USDC), ~2M tokens en pool
- **J+2**: LP €2K → €10K (net +€8K)
  - ~€6K via vente contrôlée Treasury en blocs
  - ~€2K via taxes / contribution externe

### Anti-dump measures
- LP lock ou burn après renforcement J+2
- Treasury en **multisig** + **timelock** + caps de vente journaliers/hebdo
- Split des ventes
- Pas d’airdrop massif / pas de distribution KOL débloquée autour de J+2

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
2. **Vault (PROTOCOL ΔΣ)** — coffre animé 6 digits + chassis IA + feed activité on-chain + funnel Niveau 02
3. **AI Prophet Live Chat** — Emergent LLM, persona FR/EN
4. **Prophecies Feed** — punchlines auto-refresh
5. **Mission Section** — framing MiCA + structure, reframé PROTOCOL ΔΣ
6. **Interactive Tokenomics** — pie chart (Recharts)
7. **Liquidity & Treasury Transparency** — timeline + anti-dump (**carrousel full-width**)
8. **ROI Simulator** — **simulateur dynamique avec graphe live + bandeau risque défilant** (MiCA)
9. **Roadmap** — timeline
10. **FAQ** — MiCA, tax, treasury, vesting, risques, “pourquoi l’objectif est classifié”
11. **Whitelist / Email Capture** — MongoDB
12. **Social Mockups** — X/Twitter, Telegram, Discord
13. **Risk Disclaimer Footer** — MiCA + bilingue
14. **Language Switcher** — FR ↔ EN
15. **Operation Reveal Page (`/operation`)** — unlock quand DECLASSIFIED
16. **Classified Vault (`/classified-vault`)** — gate Niveau 02 + session token + “true vault”
17. **Admin Dashboard** — JWT/2FA + gestion vault presets/emails + scheduler bots (Phases 1/2/6)

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
7. **Simu ROI dynamique + graphe interactif + bandeau risque défilant**
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
30. Micro-rotations (10K tokens) + locks majeurs (100M tokens)
31. **Per-trade on-chain indexer**: activité reflétée par swaps réels (webhooks) + dédup
32. **Mode démo**: avant lancement, tracker BONK sans casser la progression du coffre
33. **Carrousel Transparence**: backgrounds IA propres + tampon CSS “CONFIDENTIEL” sans texte halluciné
34. **SEO/OG**: site partageable (aperçus X/Telegram/Discord) et indexable correctement
35. **Accès NIVEAU 02**: lien email/QR doit forcer l’atterrissage sur la page digicode
36. **Public Stats**: ne jamais exposer la date de lancement, remplacée par un dossier “REDACTED”

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
  - 4 images: `phase_01_launch.png` → `phase_04_anti_dump.png`
  - suppression des artefacts texte IA (“UNMDED/INK”) confirmée via captures
  - suppression du “(€2-4k)” confirmée (reste “≈ 12k$”)
- **SEO/OG pack ✅** (OG image + twitter card + robots/sitemap/manifest + JSON-LD + sync FR/EN)
- **Roadmap “dossier classifié” ✅** (badges status + connector multicolore + mobile vertical)
- **Fix coffre NIVEAU 02 ✅**
  - `?code=` force désormais la page digicode (même si une session est en cache)
  - après vérification, l’URL est nettoyée (remove `?code=`)
- **Public Stats: date de lancement masquée ✅**
  - suppression de la card “Launch date”
  - ajout bannière `redacted_dossier.png` + rail explicatif FR/EN
- **ROI Simulator dynamique + Recharts + bandeau défilant ✅ (VALIDATION VISUELLE ✅)**
  - Chart live 90 jours (3 trajectoires) lié au calculateur
  - Tooltip custom (J+jour, prix, market cap, portefeuille)
  - Bandeau risque en marquee CSS (pause hover, reduced-motion)
  - Fixes UX: overlay contraste + z-index backdrop + tabs non chevauchants

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
- ✅ 100M tokens/digit + 10K micro + goal 300K€ (custom)
- ✅ DexScreener demo/custom adaptés
- ✅ CTA DECLASSIFIED sur `/classified-vault`
- ✅ Tests backend iteration_10 ✅

---

## Phase 16 — Opération B: Refactor backend monolith → routers/core — **COMPLETED ✅**

### Objectif
- Modulariser `/app/backend/server.py` (monolithe 2221 lignes) en architecture FastAPI standard sans changer aucun comportement.

### Résultat (ce qui a été fait)
**Nouveau backend modulaire**
- ✅ `/app/backend/core/`
  - `config.py` (env, DB, Resend, LLM, prompts, CORS)
  - `security.py` (JWT rotation, rate-limit, require_admin, 2FA)
  - `models.py` (schemas Pydantic)
  - `email_service.py` (welcome email)
- ✅ `/app/backend/routers/`
  - `public.py` (`/api/*` public)
  - `public_stats.py` (`/api/public/stats`)
  - `webhooks.py` (`/api/webhooks/resend` + plus tard Helius)
  - `admin.py` (`/api/admin/*` hors vault)
  - `vault.py` (public + `/api/admin/vault/*`)
  - `access_card.py` (`/api/access-card/*`)
  - `operation.py` (`/api/operation/reveal`)
  - `bots.py` (admin bots)

**Entrypoint minimal**
- ✅ `server.py` réécrit : **2221 → 106 lignes**
  - Factory FastAPI + CORS
  - `include_router()`
  - startup/shutdown
  - wiring boucles (hourly tick, dex loop, scheduler bots)

### Compatibilité
- ✅ URLs, payloads, codes HTTP, auth flows préservés **1:1**
- ✅ Aucun changement fonctionnel

### Testing
- ✅ Backend testing agent iteration_11 : régression confirmée

---

## Phase 17 — Code Quality Hardening (sécurité + maintenabilité) — **COMPLETED ✅**

### Objectif
- Appliquer les correctifs réellement nécessaires (sécurité RNG, hygiène prod, complexité) sans casser l’existant.

### Correctifs appliqués
- ✅ RNG crypto-secure (`secrets`) pour la combinaison du coffre + codes d’accès
- ✅ Logger dev-only (suppression console prod)
- ✅ Keys stables React sur listes dynamiques
- ✅ Refactors ciblés : `dex_poll_once`, `admin_blacklist_import`, `CombinationDial`

### Testing / Evidence
- ✅ Backend testing agent iteration_12 (93% — minor issue attendu sur webhook non signé)

---

## Phase 18 — Task C (P2) : Indexer Solana per-trade via Helius — **SHIPPED ✅ (LIVE)**

### Objectif
- Remplacer l’approximation DexScreener (delta/h24) par une ingestion **per-trade** fiable (swaps Solana) afin d’alimenter PROTOCOL ΔΣ avec des signaux réels.

### Résultat (implémentation)
**Backend core**
- ✅ `/app/backend/helius.py`
  - Parsing **primary** via `events.swap.tokenInputs/tokenOutputs`
  - Fallback `tokenTransfers + pool`
  - `ingest_enhanced_transactions()` avec **dédup** (signature) + `demo_tokens_per_buy`
  - `fetch_recent_swaps()` + `catch_up_from_helius()`
  - `register_webhook()` / `list_webhooks()` / `delete_webhook()`

**Config**
- ✅ `core/config.py` : `HELIUS_API_KEY`, `HELIUS_WEBHOOK_AUTH`

**Webhooks**
- ✅ `POST /api/webhooks/helius` (authHeader + audit trail + dédup TTL 30j)

**Admin endpoints**
- ✅ `/api/admin/vault/helius-status`
- ✅ `/api/admin/vault/helius-config`
- ✅ `/api/admin/vault/helius-register`
- ✅ `/api/admin/vault/helius-catchup`
- ✅ `/api/admin/vault/helius-webhook/{id}`

**DexScreener coexistence**
- ✅ `dex_poll_once()` skip si `dex_mode in (off, helius)`

**Startup**
- ✅ catch-up opportuniste au boot

### Garde-fou demo (critique)
- ✅ Si mint = BONK (`DEMO_TOKEN_ADDRESS`) → `helius_demo_mode=true`
- ✅ Chaque BUY applique `tokens_per_micro` (actuel: 100)

### Validation (live preview)
- ✅ Webhook Helius enregistré (enhanced/SWAP)
- ✅ Dédup OK
- ✅ 401 sans auth

---

## Phase 19 — Brand Assets (V4 + monogram ΔΣ + pièce en or) — **COMPLETED ✅**

### Objectif
- Stabiliser une identité visuelle moderne et mémétique cohérente avec le lore.

### Assets livrés (public)
- ✅ Logo officiel V4 : `/app/frontend/public/logo_v4_matrix_face.png`
- ✅ Pièce en or ΔΣ : `gold_coin_front.png`, `gold_coin_3d.png`
- ✅ Preview : `/app/frontend/public/logo-preview.html`

---

## Phase 20 — Pré-lancement Polish Pack (UI + Roadmap + SEO/OG) — **COMPLETED ✅**

### Objectif
Préparer le site pour partage public et campagne de lancement (Pump.fun mint imminent) :
- **site partageable** (preview OG/Twitter correct)
- **roadmap** alignée au thème "dossier classifié"
- **polish UI** (desktop + mobile)
- **performance** (CLS + lazy loading + preload)

### Sous-Phase 20a — SEO/OG Foundation — **COMPLETED ✅**
- ✅ OG image 1200×630 via PIL (`backend/scripts_generate_og_image.py`) + `og_image.png`/`twitter_card.png`
- ✅ `index.html` complet (SEO + OG + Twitter + JSON-LD) + sync FR/EN via `I18nProvider`
- ✅ `robots.txt`, `sitemap.xml`, `manifest.json`, favicon + apple-touch-icon + icon-512

### Sous-Phase 20b — Roadmap Visual Upgrade — **COMPLETED ✅**
- ✅ Refonte `Roadmap.jsx` style dossier classifié + translations enrichies

### Sous-Phase 20c — UI Polish Audit — **COMPLETED ✅**
- ✅ Fix CSS `.glitch-stamp` (wrapper absolute) + validations desktop/mobile/dark

### Sous-Phase 20d — Performance & Polish Final — **COMPLETED ✅**
- ✅ Lazy load images sous le fold + font preconnect

---

## Phase 21 — Code Quality Pack (Tier 1 + Tier 3 + Tier 4) — **PARTIALLY COMPLETED / ONGOING**

### Objectif
Appliquer les recommandations code review **Tier 1 + Tier 3 + Tier 4**.
- **Tier 2 (sécurité auth: localStorage → cookies httpOnly)** reste volontairement **différé** (déjà loggé dans `TODO_POST_LAUNCH.md`), car plus risqué en période pré-launch.

### État actuel (mise à jour)
- ✅ **Fondations TypeScript** ajoutées (tsconfig, types, providers/hooks convertis partiellement) ; backlog restant loggé dans `TODO_TYPESCRIPT.md`.
- ✅ Splits partiels de composants React (Hero/Tokenomics/ClassifiedVault déjà découpés).
- ⏳ Reste: migrations TS supplémentaires + splits Admin/TerminalPopup et nettoyage eslint résiduel.

### Sous-Phase 21a — Tier 1 Python Quick Wins (qualité + stabilité)
- [ ] Exécuter ruff/pyflakes pour lister exactement :
  - `is` utilisé à tort sur littéraux (préserver `is None` / `is not None`)
  - variables non définies (ruff `F821`)
- [ ] Appliquer `is` → `==` (34 occurrences) sur :
  - `vault.py`, `routers/vault.py`, `routers/bots.py`, `routers/public_stats.py`
  - `helius.py`, `core/bot_scheduler.py`
- [ ] Corriger **3 variables non définies** (identifier les fonctions puis patch minimal)
- Validation:
  - ruff clean sur fichiers touchés
  - smoke test backend (boot + endpoints principaux non-auth)

### Sous-Phase 21b — Tier 1 React Quick Wins (correctness)
- [ ] Remplacer `key={index}` par des keys stables (13 instances) :
  - `Operation.jsx`, `AdminVault.jsx`, `VaultSection.jsx`
  - `ActivityHeatmap.jsx`, `Mission.jsx`, `FAQ.jsx`
- [ ] Corriger hooks avec dépendances manquantes (38 instances)
  - Décider pour chaque cas :
    - (1) ajouter deps correctement, ou
    - (2) stabiliser via `useCallback`/`useMemo`, ou
    - (3) utiliser `useRef` pour éviter re-triggers, ou
    - (4) conserver mount-only avec `eslint-disable` + commentaire justifiant
  - Fichiers prioritaires signalés :
    - `ThemeProvider.jsx`, `ClassifiedVault.jsx`, `AdminBots.jsx`, `Admin.jsx`, `I18nProvider.jsx`
- Validation:
  - eslint clean (ou warnings documentés)
  - smoke test visuel (Landing, Admin, ClassifiedVault, Stats)

### Sous-Phase 21c — Tier 3 Python Complex Function Refactor (maintenabilité)
Priorité (du plus risqué au plus critique) :
- [ ] `core/security.py:verify_admin_jwt` — réduire l’imbrication via **early returns**
- [ ] `dexscreener.py:dex_poll_once` — extraire logique de processing token/pool
- [ ] `core/prophet_studio.py:generate_post` — séparer validation / fetch / génération LLM / persistance
- [ ] `email_templates.py:render_welcome_email` — découper sections template
- [ ] `access_card.py:render_card` — extraire helpers (layout, QR, typography, overlays)
Validation:
- tests existants + smoke tests manuels des endpoints affectés
- vérification non-régression sur emails (welcome + access card)

### Sous-Phase 21d — Tier 3 React Large Component Splits (maintenabilité)
Approche: refactor **structure-only** (pas de changement UI/UX), extraction progressive.
- [ ] `AdminBots.jsx` → `BotsList` + `BotEditor` + `JobsPanel` + `LLMConfig`
- [ ] `Admin.jsx` → `WhitelistManagement` + `ChatLogPanel` + `StatsDisplay` + `SettingsPanel`
- [ ] `AdminVault.jsx` → `VaultPresetEditor` + `VaultPlanList` + `VaultDevTools`
- [ ] `TerminalPopup.jsx` → `TerminalHistory` + `CommandParser`
Validation:
- capture screenshots avant/après pour diff visuel
- smoke test navigation + interactions (Admin, Vault, Terminal, Stats)

### Sous-Phase 21e — Tier 4 TypeScript Migration (multi-session)
Stratégie: progressive et compatible CRA via `allowJs`. Le but de cette phase est de **mettre en place TS** et convertir d’abord le socle.
- [ ] Continuer conversions vers `.ts/.tsx` selon `TODO_TYPESCRIPT.md` (60+ fichiers)
- [ ] Ajouter types API (vault, bots, stats, access card, admin) si manquants
- [ ] Monter progressivement le niveau de `strictness` (post-launch)
Validation:
- build front OK
- navigation smoke

### Phase 21 Status
- **ONGOING** (fondations déjà livrées, reste du backlog planifié)

---

## Remaining / Optional Improvements (P1)

### (A) Switch vers le vrai mint $DEEPOTUS (après déploiement)
- ⏳ Une fois le token déployé sur Solana :
  - `POST /api/admin/vault/helius-register` avec le vrai mint
  - `helius_demo_mode` s’éteint automatiquement
  - (optionnel) renseigner le pool LP address

### Bots — phases bloquées (attente credentials)
- ⏳ Phase 3: Telegram Bot API (token + chat_id)
- ⏳ Phase 4/5: X API v2 (OAuth2) + KOL list
- ⏳ Trading bot refs: liens BonkBot/Maestro/Trojan

### Intégration branding dans le front (en attente du feu vert)
- ⏳ Remplacer l’avatar/visuel hero par `logo_v4_matrix_face.png`
- ⏳ Ajouter `gold_coin_front.png` / `gold_coin_3d.png` dans hero/press-kit

---

## Future (P2+)
- (Option) Ajouter un parseur Raydium/Orca plus profond pour réduire les “skipped” sur swaps multi-hop
- (Option) Persister des métriques agrégées Helius (buys/sells/volume) pour un dashboard public plus précis
- (Post-launch) Refactors loggés dans `TODO_POST_LAUNCH.md` (cookies httpOnly, split components, type hints)

---

## Pending Operations (memorized for later — user requested)
- ✅ **(B) Backend refactor**: TERMINÉ — monolithe `server.py` → `core/` + `routers/`
- ✅ **(Hardening)**: TERMINÉ — secrets RNG + logger + keys stables + refactor complexité
- ✅ **(C) On-chain accuracy upgrade**: TERMINÉ — indexer Solana per-trade via Helius (webhooks + catch-up)
- ✅ **(D) ROI Simulator dynamique**: TERMINÉ — Recharts live + marquee disclaimers + i18n + validation visuelle
- ⏳ **(A) Switch à $DEEPOTUS réel**: à faire dès que le mint Solana est connu

---

## Testing strategy (Phase 21)
- Après **21a (Python quick wins)**:
  - ruff/pyflakes clean
  - smoke test backend (boot + endpoints non-auth)
- Après **21b (React quick wins)**:
  - eslint clean
  - screenshots Landing + ClassifiedVault + PublicStats + Admin
- Après **21c (Python refactors)**:
  - tests emails + bots preview + verify_admin_jwt (admin login)
  - non-régression vault polling + dex poll
- Après **21d (React splits)**:
  - screenshot diff avant/après sur pages touchées
- Après **21e (TypeScript setup/migration)**:
  - build CRA OK + navigation smoke
