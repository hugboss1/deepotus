# Landing Page $DEEPOTUS — Memecoin IA Prophète (Deep State POTUS)

## User-Validated Configuration
- **Ticker**: `$DEEPOTUS` (Deep State POTUS)
- **Language**: Bilingue FR/EN avec toggle
- **Art direction**: Hybride — haut de page institutionnel/MiCA-compliant + bas de page brutalist crypto-degen/meme + esthétique deepfake/IA.
- **LLM**: Emergent LLM key (validé)
- **Go-to-market**: lancement sur **Pump.fun**, puis migration automatique vers **Raydium**
- **Intro Deepstate** (bonus, validé): **14s** · cooldown **24h** · **aucun audio** · terminaux **mix FR/EN**
- **News repost** (bonus, validé): repost organique des **top-5 kept headlines RSS** sans LLM vers X & Telegram
  - **Préfixe**: `⚡ INTERCEPTÉ ·` (FR) / `⚡ INTERCEPT ·` (EN)
  - **Cadence**: 30 min (repost interval)
  - **Cap quotidien**: 10 / jour / plateforme
  - **Wait Prophet**: 2 min après un post Prophet

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
19. **Admin Dashboard** — JWT/2FA + gestion vault + scheduler bots + **loyalty engine** + **news repost engine**

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
30. **Micro-rotations (100K tokens) + locks majeurs (100M tokens) — production tuned**
31. **Per-trade on-chain indexer**: activité reflétée par swaps réels (webhooks) + dédup
32. **Mode démo**: avant lancement, tracker BONK sans casser la progression du coffre
33. **Carrousel Transparence**: backgrounds IA propres + tampon CSS “CONFIDENTIEL” sans texte halluciné
34. **SEO/OG**: site partageable (aperçus X/Telegram/Discord) et indexable correctement
35. **Accès NIVEAU 02**: lien email/QR doit forcer l’atterrissage sur la page digicode
36. **Public Stats**: ne jamais exposer la date de lancement, remplacée par un dossier “REDACTED”
37. **Loyalty narrative**: citation Prophète ultra visible + bots hints progressifs + email #3 post-N2 (sans nommer GENCOIN)
38. **DeepStateIntro**: écran noir + fenêtres terminal + glitch + fade vers landing en ≤15s, show-once/24h, skip + reduced-motion
39. **News repost**: repost automatique top-5 headlines RSS vers X + Telegram (sans LLM), cadence admin, cap/jour, dedup, wait-after-Prophet
40. **Code Quality Hardening**: circular imports cassés + auth token sessionStorage + refactors complexité + keys stables React

---

## Current Status
- Plan ✅
- Backend ✅
- Frontend ✅
- Testing ✅
- **Delivery ✅**
- **Architecture backend modulaire ✅ (Opération B terminée)**
- **Hardening code quality ✅ (Phase 17 terminée + Sprint Quality terminé)**
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
- Toggle: `bot_config.loyalty.hints_enabled` (default false)
- Admin endpoints:
  - `GET /api/admin/bots/loyalty` (status + tiers + sample)
- Admin UI (`AdminBots.jsx` → Config tab): section “Loyalty engine” + preview + liste tiers + toggles

#### Sprint 4 — Email #3 « Allégeance notée » ✅
- Template HTML: `email_templates.py:render_loyalty_email()` + `loyalty_email_subject()`
- Module `core/loyalty_email.py`:
  - `_generate_prophet_message()` via LLM + fallback curated
  - `list_pending(delay_hours)` sur `access_cards`
  - `_send_one()` → Resend + audit `email_events` + stamp `access_cards.loyalty_email_sent_at`
  - `loyalty_email_tick()` scheduler
  - `force_send_loyalty()` + `get_loyalty_email_stats()`
- Scheduler: job `loyalty_email` toutes les 30 min
- Toggles: `bot_config.loyalty.email_enabled`, `bot_config.loyalty.email_delay_hours`
- Admin endpoints: `GET /api/admin/bots/loyalty/email-stats`, `POST /api/admin/bots/loyalty/test-send`
- Admin UI (`AdminBots.jsx`): toggle + delay + stats + force-send + panneau résultat

### Sprint Bonus — DeepStateIntro (entrée hack-style) — ✅ COMPLETED + validated
- `/app/frontend/src/components/intro/` : `DeepStateIntro.jsx`, `TerminalWindow.jsx`, `MatrixRain.jsx`, `GlitchOverlay.jsx`, `hackScripts.js`
- Timeline 14s + skip + cooldown 24h + reduced-motion
- Mounted au-dessus de la landing (premier enfant de `Landing.jsx`)

### Sprint Bonus — News repost engine (RSS headlines) — ✅ COMPLETED + validated

#### Concept
Deux flux indépendants dans “Prophet Fleet · Bots Control” :
1. Prophet posts (LLM) selon interval admin
2. News reposts: top-5 kept headlines RSS sans LLM vers X/Telegram

#### Backend
- `core/news_repost.py`: format par plateforme, dédup SHA1, tick scheduler, force-send, status snapshot
- Scheduler job `news_repost` toutes les 5 min (rate-limited en interne)
- Endpoints: `GET /api/admin/bots/news-repost/status`, `POST /api/admin/bots/news-repost/test-send`
- Mode `dry_run` tant que creds absents (log DB)

#### Frontend Admin
- Section “News repost · auto-relay X & Telegram” dans `AdminBots.jsx` (toggles, inputs, queue preview, test result)

---

## Phase 17 — Code Quality Hardening (sécurité + maintenabilité) — **COMPLETED ✅**

### Sprint Quality (Code review fixes) — ✅ COMPLETED + regression validated
**Critical fixes**
1. **Circular import résolu**
   - Créé `core/bot_config_repo.py` (DEFAULT_BOT_CONFIG, ALLOWED_PATCH_KEYS, ensure/get config, persist patch)
   - `core/bot_scheduler.py` ne conserve que l’orchestration scheduler + `update_bot_config` (persist + sync)
   - Consommateurs (`loyalty_email.py`, `news_repost.py`, `prophet_studio.py`) importent désormais `get_bot_config` depuis `bot_config_repo`
   - Validation : backend tests 100%, jobs APScheduler OK

2. **Admin JWT migré localStorage → sessionStorage**
   - Nouveau helper `frontend/src/lib/adminAuth.js`
   - Migration legacy exécutée au module-load (copie + suppression de localStorage)
   - Admin pages migrées : Admin.jsx, AdminBots.jsx, AdminVault.jsx, AdminEmails.jsx
   - Validation : token en sessionStorage, localStorage vidé

3. **PRNG du dossier “redacted” sécurisé (scopé)**
   - `scripts_generate_redacted_dossier.py`: `_rng = random.Random(2026)  # noqa: S311` + remplacement des appels global random
   - Objectif: reproductibilité build + suppression de l’état global

4. **React key stability**
   - `TerminalWindow.jsx`: suppression `key={index}` au profit d’une clé stable dérivée

**Important fixes**
5. **Hook deps / idiome**
   - `DeepStateIntro.jsx`: `useMemo(() => () => ...)` → `useCallback(() => ...)`

6. **Refactor complexité**
   - `core/news_repost.py`: `_send_one()` et `news_repost_tick()` split en helpers (complexité réduite)
   - `core/loyalty_email.py`: `_send_one()` split en helpers (lisibilité + test)

**Nice-to-have**
7. **Console statements**
   - `TerminalPopup.jsx`: `console.warn` → `logger.warn` (logger prod-safe)

**Validation**
- backend lint clean + restart OK
- frontend eslint clean + compile OK
- testing agent regression : **100% backend** + **95% frontend**, 1 finding cosmétique corrigé (legacy localStorage purge)

---

## Remaining / Optional Improvements (P1)

### (A) Switch vers le vrai mint $DEEPOTUS (post-launch)
- ⏳ Remplacer le mint BONK démo par le vrai mint
- ⏳ `POST /api/admin/vault/helius-register` avec le vrai mint

### Bots — phases bloquées (attente credentials)
- ⏳ Phase 3: Telegram Bot API (token + chat_id) → **compléter `_dispatch_telegram()` dans `core/news_repost.py`** + dispatcher Prophet Telegram
- ⏳ Phase 4/5: X API v2 (OAuth2) → **compléter `_dispatch_x()` dans `core/news_repost.py`** + dispatcher Prophet X
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
- ✅ (H) News repost engine (RSS → X/Telegram, no-LLM): terminé
- ✅ (I) Sprint Quality (code review fixes): terminé
- ⏳ (A) Switch à $DEEPOTUS réel: dès que le mint Solana est connu

---

## Testing strategy (Phase 21)
- Après **21a (Python quick wins)**:
  - lint backend clean
  - smoke test backend
- Après **21b (React quick wins)**:
  - eslint clean
  - screenshots Landing + ClassifiedVault + PublicStats + Admin
- Après **21c/21d**:
  - non-régression emails + bots preview + admin login
- Après **21e (TypeScript)**:
  - build CRA OK + navigation smoke
