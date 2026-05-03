# DEEPOTUS — Plan de finalisation TypeScript & sécurité “Cabinet Vault” **+ Propaganda Engine ΔΣ**
(Sprints 6 → 13.3 + Infiltration 14.x + Brain Connect 15.x + Déploiements 17)

## 1) Objectives
- Stabiliser et clarifier le code **sans refactors risqués pré-launch** ; privilégier des fixes “safe” (lint/build, guards sécurité, docs, tooling).
- Augmenter la couverture TS/TSX sur le code applicatif (hors Shadcn UI auto-généré) **après** stabilisation des déploiements.
- Garantir une base prête pour un déploiement **Vercel (frontend) / Render (backend)** avec builds production OK.
- Préserver le comportement actuel (bots en **dry-run** tant que credentials non fournis, vault, ROI, intro, admin).
- **Centraliser la gestion des secrets** via le **Cabinet Vault** (BIP39 + PBKDF2 + AES-256-GCM) et migrer les clés existantes (LLM, Resend, Helius, bots) vers ce coffre.
- **Conformité sécurité** : 2FA côté admin pour les actions sensibles, audit logging, rotation, export/import de backups chiffrés.
- **PROTOCOL ΔΣ — Propaganda Engine** : automatiser une logique “scenario-based” (triggers marché → message → queue → dispatch) pour réagir au marché avec garde-fous anti-slop, **testable pré-mint** via Manual Fire, et opérable via UI admin.
- **PROTOCOL ΔΣ — Infiltration Brain** : livrer l’expérience publique “Proof of Intelligence” (énigmes Terminal → clearance) + surface admin conforme posture sécurité.
- **Sprint 14.2 — Infiltration Automation** : ajouter des vérifications semi-automatiques **sans dépendre du tier X** (TG live, X en review queue), + préparation KOL DM drafts (approval mode).
- **Sprint 15 — Brain Connect & Treasury Architecture (MiCA)** : relier l’indexation on-chain (Helius) au lore **sans logique de trading**, publier une politique de trésorerie transparente, outillage admin de disclosure + tokenomics tracker public.
- **Ops post-prod** : réduire les erreurs humaines (déploiement, secrets, webhooks) via docs exécutables, endpoints diagnostics, et assets email hébergés.
- **Nouvel objectif (Pre-mint/Mint UX)** : aligner landing + pages publiques sur une stratégie **3 phases env-driven** (pre-mint / live / graduated), + page `/transparency` MiCA-style, + logs Treasury publics.

> Stratégie : “migration gates” (tsc/build + smoke tests) à chaque sprint + validation API (curl/testing) avant activation en prod.

### État actuel (mise à jour)
- **PRODUCTION LIVE** : `https://www.deepotus.xyz` sur Vercel (frontend) + Render (backend).
- Admin : **mot de passe modifié** (rotation effectuée), **2FA activée**, vault accessible.
- **Cabinet Vault** : déverrouillé en prod ; secrets déjà saisis : **LLM / Resend / Helius**.
- **Reste à saisir** : credentials **Telegram** (bot token + chat ID) et **X** (4 secrets OAuth1.0a) dans le vault.
- Branding : watermark **“Made with Emergent” supprimé** (frontend `public/index.html`).
- Déploiement : doc **push GitHub + Deploy Hook Vercel** livrée (Hobby plan).
- Emails : 4 hero images IA (25–55KB) servies via `/api/assets`, intégrées aux templates.
- **Grosse MAJ pre-mint/mint (8/10 tasks)** : système phases env-driven + `/transparency` + Hero/Tokenomics/HowToBuy/Roadmap/BurnCounter.

#### Cabinet Vault (Sprints 12.x) — ✅ COMPLET
- Backend BIP39 + PBKDF2 + AES-256-GCM + audit.
- Frontend UI `/admin/cabinet-vault` + export + import + audit.
- Import/Export chiffrés validés.
- **SecretProvider** en place (vault → fallback env) + script migration secrets.
- **Bootstrap writes** : writes autorisés sans 2FA jusqu’à `BOOTSTRAP_WRITE_LIMIT=30` ; reads/export/import restent **2FA strict**. Messages d’erreur structurés + normalisation mnemonic Unicode.
- Endpoint recovery `POST /api/admin/2fa/force-reset` + guide `/app/docs/2FA_SETUP_GUIDE.md`.

#### Propaganda Engine (Sprints 13.1–13.2) — ✅ LIVRÉ end-to-end
- **Sprint 13.1 MVP** ✅ : orchestrateur + templates DB + approval queue + panic kill-switch + UI admin (Triggers/Templates/Queue/Activity).
- **Sprint 13.2 COMPLET** ✅ : triggers + analytics + tone engine (LLM) + templates FR/EN + settings UI.

#### Sprint 13.3 — Dispatchers & Worker cron — ✅ COMPLET
- Worker APScheduler (tick toutes les 30s) : claim atomique `approved → in_flight → sent|failed`.
- Dispatchers : `telegram.sendMessage` + `X POST /2/tweets` (OAuth1.0a) + mode dry-run.
- Garde-fous : `dispatch_enabled` (default false) + `dispatch_dry_run` (default true) + rate limits.
- Routes admin + doc ops.

#### Sprint 13.3.x — Robustesse opérationnelle (pré-live) — ✅ COMPLET
- Retry/backoff exponentiel pour erreurs transientes (429/5xx/timeout/network) : **60s / 120s / 240s**, **max 3 tentatives** (`MAX_RETRIES=3`).
- Endpoint non destructif : `GET /api/admin/propaganda/dispatch/preflight` (audit des secrets Telegram/X, vault/env, sans fuite de valeurs).
- UI Admin Propaganda : **bannière de mode de dispatch** (PAUSED / DRY-RUN / LIVE / PANIC).
- Observabilité worker enrichie : champ `retried` dans le résumé de tick.

#### Infiltration Brain (Sprint 14.1) — ✅ Backend + ✅ Admin UI + ✅ Public Terminal flow
- Backend : riddles/clearance/sleeper cell + endpoints.
- Seeds 5 énigmes + anti-bruteforce.
- Admin UI : `/app/frontend/src/pages/Infiltration.tsx`.
- Public UX : intégration “Proof of Intelligence” via `TerminalPopup.tsx` + `RiddlesFlow.tsx`.

#### Sprint 14.2 — Infiltration Automation (backend scaffold) — ✅ BACKEND SCAFFOLD LIVRÉ
- Nouveau module : `backend/core/infiltration_auto.py`.
- Endpoints publics :
  - `POST /api/infiltration/verify/telegram` (LIVE via `getChatMember`)
  - `POST /api/infiltration/verify/x-follow` (stub → `x_tier_required`)
  - `POST /api/infiltration/verify/share` (soumission → review queue)
- Endpoints admin :
  - `GET /api/admin/infiltration/auto/status`
  - `GET /api/admin/infiltration/shares?status=pending_review`
  - `POST /api/admin/infiltration/shares/{id}/review`
  - `GET /api/admin/infiltration/kol-dm-drafts`
  - `POST /api/admin/infiltration/kol-dm-drafts/{id}/approve`
- Modèle d’opération **pré-tier X** : L2 via review queue (URL X) + KOL DMs via drafts approuvées.

#### Whale Watcher & disclosures (Sprint 15/16) — ✅ BASE LIVRÉE
- `TOKENOMICS_TREASURY_POLICY.md` créé.
- Helius webhooks + worker + UI admin.
- Seeds triggers/templates : `founder_buy`, `kol_mention`.
- **Doc post-déploiement Helius** livré : `/app/docs/HELIUS_POST_DEPLOY.md`.

#### Emails transactionnels (Resend)
- ✅ Diagnostics livrés : `GET /api/admin/email/diagnostics`.
- ✅ Hero assets servis via `/api/assets`.

#### Documentation Ops / Produit — ✅ LIVRÉE
- ✅ Helius post-deploy : `/app/docs/HELIUS_POST_DEPLOY.md`.
- ✅ Fonctionnement bots infiltration + propagande : `/app/docs/BOTS_OPERATIONS.md`.
- ✅ Push GitHub / Vercel Hobby contournement : `/app/docs/GITHUB_PUSH_MANUAL.md`.
- ✅ Phases env-driven : `/app/docs/PHASES_ENV_DRIVEN.md`.

#### Assets email — ✅ LIVRÉ (4 illustrations IA)
- ✅ `backend/static/loyalty_hero.jpg` + meta JSON.
- ✅ `backend/static/welcome_hero.jpg` + meta JSON.
- ✅ `backend/static/accreditation_hero.jpg` + meta JSON.
- ✅ `backend/static/prophet_update_hero.jpg` + meta JSON.
- ✅ `server.py` monte `StaticFiles` sur `/api/assets`.
- ✅ Intégration templates :
  - `render_loyalty_email()` → `loyalty_hero.jpg`
  - `render_welcome_email()` → `welcome_hero.jpg`
  - `render_access_card_email()` → `accreditation_hero.jpg`
  - `render_genesis_broadcast_email()` → `prophet_update_hero.jpg`
- Script générique : `backend/scripts/generate_email_asset.py`.

#### UX Landing — ✅ Hotfix
- ✅ `PropheciesFeed.tsx` : maintien de la prophétie live **5 secondes** après clic sur “Nouvelle prophétie” (`LIVE_HOLD_MS=5000`).

#### Grosse MAJ pre-mint/mint phases — ✅ 8/10 tasks LIVRÉS
- ✅ **TASK 10** : `frontend/src/lib/launchPhase.ts` (source of truth env-driven)
  - `getLaunchPhase()` + `URLS` + `getWallets()` + `hasMint()` + `getLaunchTimestamp()` + `getMint()`.
- ✅ **TASK 6** : backend `routers/treasury.py`
  - `GET /api/treasury/operations` + `GET /api/treasury/burns`
  - admin `POST/GET/DELETE /api/admin/treasury/operations`.
  - validation Pydantic stricte (base58 wallet + signature).
- ✅ **TASK 1** : page `frontend/src/pages/Transparency.tsx` + route `/transparency`
  - 5 wallets (env-driven placeholders)
  - lock cards (env-driven, placeholder si vide)
  - BubbleMaps iframe (post-mint only)
  - RugCheck fetch (post-mint only)
  - Treasury operations table (from TASK 6).
- ✅ **TASK 2** : Hero 3 phases (pre/live/graduated)
  - badge + countdown (`REACT_APP_LAUNCH_TS`) + CTAs phase-aware.
- ✅ **TASK 3** : `TokenomicsLockBadges` (3 buckets) + lien `/transparency`.
- ✅ **TASK 4** : `HowToBuyPhasedSteps` (4 steps par phase + BonkBot CTA).
- ✅ **TASK 5** : Roadmap 6 phases + `deriveStatuses()` env-driven.
- ✅ **TASK 9** : `BurnCounter` widget (fetch `/api/treasury/burns`).
- ✅ Nav + Footer : lien `/transparency`.
- ✅ Doc : `/app/docs/PHASES_ENV_DRIVEN.md` + index docs mis à jour.

#### Sprint 17.A — Refonte Tokenomics Cards (UI premium) — ✅ COMPLET
- ✅ 4 cartes illustrées (Public, Treasury, Shadows, Burn) avec illustrations IA générées via gpt-image-1.
- ✅ **Top slab à hauteur fixe** (`h-[180px]`) → toutes les illustrations alignées au même niveau Y (corrige le décrochage de la carte Public).
- ✅ **Animations Framer Motion** : `whileInView` fade-in staggered (delay × 0.08), `whileHover` translate-Y (-4), image scale 1.045 sur hover.
- ✅ **Ombres colorées dominantes** par carte via CSS var `--card-glow` :
  - Public → cyan/teal `rgba(45, 212, 191, 0.55)`
  - Treasury → amber/gold `rgba(245, 158, 11, 0.55)`
  - Shadows → indigo/violet `rgba(129, 140, 248, 0.5)`
  - Burn → ember red `rgba(239, 68, 68, 0.6)`
- ✅ **Titre style "Allocation & Discipline"** : kicker mono `tracking-[0.25em]` + `font-display text-3xl md:text-4xl lg:text-5xl font-semibold leading-tight` + subtitle.
- ✅ Edge top de l'illustration coloré dynamiquement (visible accent au hover).
- ✅ Validation visuelle light + dark mode + hover state.

#### Sprint 17.B — Refonte page /transparency (cinematic carousel) — ✅ COMPLET
- ✅ **Hero refait** : kicker amber + `font-display text-4xl/5xl/6xl semibold leading-[1.04]` (cohérent avec Hero landing).
- ✅ **Sections Wallets + Locks** : kicker mono + titres `font-display 2xl/3xl/4xl` (vs anciens `text-lg`).
- ✅ **Nouveau composant** : `frontend/src/components/transparency/TransparencyDataCarousel.tsx`.
- ✅ **3 slides classifiées** (modèle inspiré de `TransparencyTimeline` landing) :
  1. SCREEN/01 — Holder cartography (BubbleMaps iframe ou placeholder)
  2. SCREEN/02 — Live trust audit (RugCheck score + note MiCA-style)
  3. SCREEN/03 — Treasury operations log (table from /api/treasury/operations)
- ✅ Stamp CONFIDENTIEL rouge en CSS pur (zéro typo IA).
- ✅ Tag DOSSIER bottom-left avec accent color par slide (#33FF33 / #2DD4BF / #F59E0B).
- ✅ Navigation prev/next + hint scroll.
- ✅ **3 illustrations IA "écrans de visualisation"** générées via gpt-image-1 (~30-50 KB chacune) :
  - `transparency_distribution.jpg` : situation-room screen avec constellation de bubble nodes glowing green
  - `transparency_rugcheck.jpg` : moniteur embassy-grade avec heraldic shield wireframe teal + scanner rings
  - `transparency_operations.jpg` : ledger terminal sur desk brushed-steel + lampe ambre + dossier ΔΣ scellé
- ✅ Briefs `IMAGE_STYLE_BRIEFS` ajoutés dans `prophet_studio.py` + `--all-transparency` flag dans le script.
- ✅ CSS `viz-screen-frame` (radial green glow + scanlines overlay).
- ✅ Translations FR/EN complètes (`transparencyPage.viz.*`, `walletsKicker`, `locksKicker`, `rugcheck.note`).
- ✅ Validation visuelle light + dark mode.

#### Sprint 18 — Prophet Studio v2 (TASK 7) + AdminBots Cadence (TASK 8) — ✅ COMPLET
- ✅ **TASK 7 backend** :
  - `prophet_studio.PROMPT_TEMPLATES_V2` : 5 templates pondérés (`lore`·1, `satire_news`·3, `stats`·1, `prophecy`·4, `meme_visual`·1).
  - `generate_post_v2(platform, force_template?, extra_context?)` réutilise les helpers v1 (`_build_user_prompt`, `_call_llm`, `_parse_llm_json`, `_normalize_hashtags`, `_truncate`) — wire contract identique sauf champs additionnels `template_used` + `template_label`.
  - `list_v2_templates()` retourne metadata JSON-safe.
  - V1 `generate_post()` inchangé → fallback admin one-click.
- ✅ **TASK 7 endpoints** :
  - `GET /api/admin/bots/v2-templates` retourne les 5 templates avec poids + suggested hashtags.
  - `POST /api/admin/bots/generate-preview` accepte `use_v2` + `force_template_v2` ; response carries `template_used` + `template_label`.
  - Image generation sur path V2 fallback à `prophecy` content_type pour compat.
- ✅ **TASK 7 frontend** :
  - Toggle "Prompt V2 — 5 weighted templates" dans Config tab (data-testid `config-prompt-v2-toggle`).
  - Switch "Use V2" + dropdown "Force template (optional)" dans Preview tab (data-testid `preview-v2-toggle`, `preview-v2-template-select`).
  - Badge orange "V2 TEMPLATE <id>" + label affiché au-dessus du résultat (data-testid `preview-v2-template-badge`).
  - Test end-to-end : V2 a roulé `meme_visual` aléatoirement, produit "Un fauteuil vide face à douze écrans éteints…" — ton parfait.
- ✅ **TASK 8 backend** :
  - `bot_config.cadence` étendu : `daily_schedule.{x,telegram}.{enabled, post_times_utc, archetypes}` + `reactive_triggers.{enabled, whale_buy_min_sol, holder_milestones, marketcap_milestones_usd}` + `quiet_hours.{enabled, start_utc, end_utc}`.
  - `_shape_cadence()` helper + safe defaults exposés via `_shape_config`.
  - `CadencePatch` Pydantic avec validation HH:MM regex, max 8 slots, archetypes string list, milestones tri+dedupé.
- ✅ **TASK 8 frontend** :
  - Nouveau composant `frontend/src/pages/admin/sections/AdminCadenceSection.tsx` (auto-loaded GET /config + GET /v2-templates).
  - Onglet "Cadence" (5e tab) entre Preview et Jobs.
  - Daily schedule X/TG : time picker (input type=time), Add slot button, badges removables, archetype multi-select (toggle pills avec poids).
  - Reactive triggers : Switch global + 3 inputs (whale SOL, holder milestones CSV, marketcap milestones CSV).
  - Quiet hours : Switch + 2 time pickers UTC.
  - Tous les inputs persist on blur via `PUT /api/admin/bots/config` patch.cadence.
- ✅ **Tests** :
  - Backend : `ruff` All checks passed sur les 3 fichiers Python.
  - Frontend : `eslint` No issues found sur AdminBots.jsx + esbuild OK sur AdminCadenceSection.tsx.
  - curl : `/v2-templates` retourne 5 templates, `/config` expose nouveaux blocs avec defaults, `PUT /config` merge correctement, `/generate-preview use_v2=true force=lore` retourne content cohérent.
  - Screenshots : Cadence tab (top + scroll vers Quiet hours), Preview tab (V2 OFF, V2 ON, résultat avec badge), Config tab (toggle V2).
- ✅ **Doc** : `/app/docs/SPRINT_17_18_DEPLOY.md` (guide push GitHub + verify Vercel/Render + rollback).

#### Sprint 19 — Cadence wiring + reactive triggers + i18n cleanup — ✅ COMPLET
- ✅ **Carte Phase 4 "Loyalty Mandate"** : remplacement complet du copy "Charity / UNICEF / Téléthon" par un slogan politique de candidat (*"the Cabinet buys back for the loyal"*, buybacks conditionnels aux milestones, distributions Niveau 02+, *"the longer the crowd stays loyal the more the Cabinet rebuys"*).
- ✅ **Replace global `raydium` → `PumpSwap`** :
  - Translation strings (translations.js : 24 occurrences traduites + URLs `swap.pump.fun`)
  - Backend variables + comments (`raydium_link` → `pumpswap_link`, `_build_raydium_link` → `_build_pumpswap_link`)
  - Trigger key `raydium_migration` → `pumpswap_migration` + fichier renommé `triggers/raydium_migration.py` → `triggers/pumpswap_migration.py`
  - State value `dex_mode == "raydium"` → `dex_mode == "pumpswap"`
  - Docs Vercel + Tokenomics policy mis à jour
  - Total : **24 fichiers modifiés, 0 erreur lint, backend redémarre clean**.

- ✅ **TASK 3 — Cadence engine wiring (`core/cadence_engine.py`)** :
  - `is_in_quiet_hours(now_utc, qh)` — gère windows wrapping past midnight (e.g. 23:00 → 06:00).
  - `pick_archetype(allowed)` — weighted random parmi V2 templates (fallback vers full set si liste invalide).
  - `cadence_daily_tick()` — pour chaque platform `(x, telegram)`, vérifie si `enabled` + `now_utc.HH:MM in post_times_utc` + pas dans quiet hours + dedup `last_fired_today.{plat}.{slot} != today_iso`. Si oui → `generate_post_v2(force_template=archetype)` + `dispatch_queue.propose(policy="auto")`.
  - `cadence_reactive_tick()` — lit `_read_market_snapshot()` (price × 1B = MC, holders best-effort), compare aux milestones config, fire post v2 (archetype `prophecy` pour MC, `stats` pour holders) avec dedup persisté `fired_milestones.{marketcap_usd, holders}`.
  - `cadence_whale_react(sol_amount, tx_signature, wallet)` — appelé par `whale_watcher.process_pending_alerts` après le push v1 propaganda. Fire ADDITIONNEL post v2 archetype `satire_news` quand `sol_amount >= reactive_triggers.whale_buy_min_sol` ET `enabled=true` ET pas en quiet hours. Idempotent sur tx_signature.
  - `cadence_combined_tick()` — wrapper resilient pour APScheduler (try/except sur chaque branche).
  - **Persistance** : tout l'état dedup vit sur `bot_config.cadence._state.{last_fired_today, fired_milestones}` → survit aux restarts, restorable via Mongo.
  - **Trigger keys** : `cadence_daily`, `cadence_holder`, `cadence_marketcap`, `cadence_whale` — distincts du Propaganda Engine v1.

- ✅ **TASK 4 — Scheduler wiring** :
  - Nouveau job `cadence_tick` enregistré via `_cadence_tick_job` dans `bot_scheduler.py` — `IntervalTrigger(seconds=60)`, max_instances=1, coalesce=True, misfire_grace_time=60.
  - Job s'enregistre automatiquement à chaque `sync_jobs_from_config()`.
  - **Backend tests** : `GET /api/admin/bots/jobs` montre `cadence_tick` interval `0:01:00`. Configuré un slot `02:54 X archetypes=[prophecy]`, désactivé kill_switch, attendu 2min → log `[cadence] fired trigger=cadence_daily plat=x template=prophecy queue_id=19505fa4-...`. Mongo `propaganda_queue` contient l'item avec `status=approved`, `template_id=prophecy`, `content_en/fr` cohérents et longs ("Within 72 hours, a European sovereign wealth fund will disclose catastrophic liquidity losses..."). Dedup persisté `cadence._state.last_fired_today.x.02:54="2026-05-03"`. Reset post-test : kill_switch ON.

- ✅ **Whale watcher hook** : `core/whale_watcher.py:process_pending_alerts` ajoute un `try/except await cadence_whale_react(...)` après le push v1 propaganda (en fire-and-forget, swallow les exceptions pour ne pas casser la pipeline existante).

#### Sprint 19.1 — Holders poller (Helius DAS) — ✅ COMPLET
- ✅ Nouveau module `backend/core/holders_poller.py` (~290 lignes) :
  - **Source 1 — Helius DAS `getTokenAccounts`** : pagination via cursor, page_size=1000, max_pages=100 (cap = 100k accounts pour éviter runaway sur un token mature). Compte les `token_accounts` avec `amount > 0`.
  - **Source 2 — DexScreener** : placeholder explicite (pas de holders field exposé en early 2026), retourne erreur tagguée pour le fallback.
  - **Skip silencieux** si aucun mint dans `vault_state.dex_token_address` (état pre-mint).
  - Persiste sur succès : `dex_holders_count`, `dex_holders_polled_at`, `dex_holders_source="helius"`, `dex_holders_approximate` (true si cap atteint), `dex_holders_error=None`. Sur erreur : `dex_holders_error` préservé pour observabilité, count laissé inchangé.
  - Helper `_decode_amount_from_b64()` gardé sans usage immédiat — couvre une future migration vers `getProgramAccounts` raw.
- ✅ **Job scheduler** `holders_poll` enregistré dans `bot_scheduler.py` :
  - `IntervalTrigger(seconds=POLL_INTERVAL_SECONDS=300)` → 5 minutes.
  - `max_instances=1`, `coalesce=True`, `misfire_grace_time=60`.
  - `GET /api/admin/bots/jobs` confirme `holders_poll` actif aux côtés de `cadence_tick`, `whale_watcher`, etc.
- ✅ **Test live sur BONK** (`DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263`, ~870k holders) :
  - 100 pages × 1000 accounts paginées en ~13 secondes via Helius DAS.
  - Résultat : `count=99997, approximate=true` (cap 100k atteint comme attendu).
  - Persistance vault_state validée puis cleanup automatique.
- ✅ **Test E2E cadence_holder** :
  - Injection `dex_holders_count=750` via Mongo + `reactive_triggers.enabled=true` via router (proper deep merge).
  - Attente 1 cycle scheduler 60s → log `[cadence] fired trigger=cadence_holder plat=x template=stats queue_id=afa00d68-...`.
  - Mongo `propaganda_queue` → item avec `template_id="stats"` et content cohérent : *"Council ΔΣ archive: for every new holder, 3.7 European bureaucrats lose one hour of sleep."*
  - Dedup persisté `cadence._state.fired_milestones.holders=[500]`.
  - Cleanup final : kill_switch ON + reactive disabled + test mint retiré.
- ✅ `_read_market_snapshot()` dans `cadence_engine.py` corrigé : utilise `VAULT_DOC_ID = "protocol_delta_sigma"` (était `"deepotus_protocol"` — incorrect) → l'engine lit maintenant le bon doc.

#### Sprint 21 — Refactor (zero new feature) — ✅ COMPLET
- ✅ **AdminBots.jsx 1798 → 1017 lignes (-43%)** :
  - Extract Preview tab → `frontend/src/pages/admin/sections/AdminPreviewSection.tsx` (586 lignes — V1 + V2 + image gen, charge ses propres contentTypes/v2Templates).
  - Extract Jobs tab → `AdminJobsSection.tsx` (~110 lignes, auto-refresh 10s).
  - Extract Logs tab → `AdminLogsSection.tsx` (~210 lignes, status histogram + filters + table).
  - Page mère devient un router shell : auth + status banner + 5 tabs + LLM keys dialog. Cadence (ex-Sprint 18) + Loyalty/NewsRepost/NewsFeed déjà extraits.
  - States supprimés du shell : `previewType`, `previewPlatform`, `kolPost`, `previewKeywords`, `useNewsContext`, `useV2Preview`, `forceTemplateV2`, `v2Templates`, `imageProvider`, `imageAspect`, `includeImage`, `preview`, `previewBusy`, `jobs`, `posts`, `platformFilter`, `statusFilter` → tous ré-instanciés dans leurs sections respectives.
  - Helpers supprimés : `loadJobs`, `loadPosts`, `loadV2Templates`, `generatePreview`, `downloadPreviewImage`.
  - Validation visuelle : 5 onglets actifs + 9 jobs scheduler listés (incl. `cadence_tick` 1min + `holders_poll` 5min) + status histogram (17 heartbeat OK + 261 killed). Aucune régression.
- ✅ **cadence_engine.py — split functions complexes** :
  - `cadence_reactive_tick` (cyclo 28 → ~10) : extrait `_tick_marketcap_milestones`, `_tick_holder_milestones` + helper pur `_crossed_milestone`. Le tick principal est désormais un thin orchestrator.
  - `cadence_daily_tick` (cyclo 18 → ~8) : extrait `_iter_due_slots` (générateur pur, zero I/O).
  - **25 unit tests** dans `backend/tests/test_cadence_engine_helpers.py` couvrant `parse_hhmm`, `is_in_quiet_hours` (windows same-day + wrap past midnight + zero-length + malformed), `pick_archetype` (allowed list + fallback), `_iter_due_slots` (4 scénarios), `_crossed_milestone` (6 scénarios), `format_mc_label`. **Tous passent en 1.60s**.
- ✅ **Risk-vs-benefit decisions documented** : `import_encrypted` (security-critical) + `sync_jobs_from_config` (orchestrator stable) NON touchés cette session — voir `docs/CODE_REVIEW_RESPONSE.md` §5.

#### Sprint 22.1 — Migration TypeScript pilote — ✅ COMPLET
- ✅ **3 fichiers migrés** :
  - `src/index.js` → `src/index.tsx` (11 lignes — entry point typé avec cast `HTMLElement` sécurisé pour `getElementById('root')`).
  - `src/App.js` → `src/App.tsx` (60 lignes — router shell, `JSX.Element` return typé).
  - `src/pages/AdminBots.jsx` → `src/pages/AdminBots.tsx` (1017 lignes — interfaces minimales `BotConfig` + `ContentTypeMeta` ajoutées en haut, état interne reste implicit-any selon tsconfig `strict: false`).
- ✅ **6 sections relaxées** : `AdminCadenceSection.tsx`, `AdminJobsSection.tsx`, `AdminLogsSection.tsx`, `AdminPreviewSection.tsx`, `LoyaltySection.tsx`, `NewsRepostSection.tsx` passent de `headers: AxiosRequestHeaders` à `headers: Record<string, string>` → le `useMemo(() => ({ Authorization: "Bearer ..." }))` du parent devient assignable sans cast.
- ✅ **Validation visuelle** : `webpack compiled successfully · No issues found`. Screenshot AdminBots.tsx affiche tous les composants comme avant (Platforms, Content & LLM, Prompt V2, LLM Preset, Custom LLM keys vault).
- ✅ **Pas de breaking change** : tsconfig garde `strict: false`. Migration "soft" — futurs sprints peuvent durcir progressivement.
- ✅ **Reste à migrer** : `pages/AdminVault.jsx` (665 lignes — Sprint 22.2), Custom LLM keys dialog (~250 lignes inside AdminBots.tsx — Sprint 22.3 si voulu).

- ✅ **Doc** : `/app/docs/SPRINT_21_22_DEPLOY.md` (guide push + verify + rollback).

#### Sprint 22.2 — AdminVault.jsx → AdminVault.tsx — ✅ COMPLET
- ✅ **Migration complète** de `pages/AdminVault.jsx` (665 lignes) vers `.tsx`.
- ✅ **2 interfaces documentées** :
  - `VaultState` : shape complète du GET /api/admin/vault/state (crack mechanics, treasury, DEX wiring, recent_events, target_combination, progress_pct). Backend Pydantic schema = source of truth (`backend/vault.py:VaultStateResponse`).
  - `DexPollResult` : envelope retournée par le DEX poll endpoint (ok, mode, price_usd, source).
- ✅ **Fix type errors révélés par TS strict mode** (webpack plus strict qu'esbuild) :
  - `useEffect` : `return;` → `return undefined;` pour satisfaire `TS7030: Not all code paths return a value`.
  - `setDexMode(mode)` : `const payload = { mode }` → `const payload: { mode: string; token_address?: string } = { mode }` pour permettre l'affectation dynamique conditionnelle.
  - VaultState enrichie avec tous les champs utilisés (stage, progress_pct, target_combination, dex_last_h24_buys, etc.) pour éviter les `unknown` en reactNode position.
- ✅ **Validation visuelle** : `/admin/vault` rend impeccablement — dials (4/6 locked), metrics, Manual crack form, Config (presets, hourly auto-tick, treasury goal, EUR/USD), DEX Live Feed. Aucune régression.
- ✅ Bundle : 36.9 KB (identique au .jsx pré-migration).

- ✅ **TS coverage update** : seul 1 fichier legacy restant applicatif — `AdminVault.jsx` était le dernier gros fichier non-typé. Les `components/ui/*.jsx` (shadcn) restent intentionnellement en .jsx pour conserver la compat upstream.

---

## 2) Implementation Steps

### Phase 1 — Sprint 6 (P0) : Core admin maintenable (splits + TS) ✅ **COMPLETED**
(identique)

---

### Phase 2 — Sprint 7 (P1) : Landing components (TSX) ✅ **COMPLETED**
(identique)

---

### Phase 3 — Sprint 8 (P2) : Pages applicatives (TSX) ✅ **COMPLETED**
(identique)

---

### Phase 4 — Sprint 9 (P3) : Intro + 2FA (TSX) ✅ **COMPLETED**
(identique)

---

### Phase 5 — Sprint 10 : Polish final + readiness deploy ✅ **COMPLETED**
(identique)

---

### Phase 6 — Sprint 11 : “VAULT SEALED” pré-mint (P0) ✅ **COMPLETED**
(identique)

---

### Phase 7 — Sprint 12.1 : Sécurité admin (password rotation + 2FA UI) ✅ **COMPLETED**
(identique)

---

### Phase 8 — Sprint 12.2 : Cabinet Vault Backend (BIP39 + AES-256-GCM) ✅ **COMPLETED**
(identique)

---

### Phase 9 — Sprint 12.3 : Cabinet Vault Frontend UI ✅ **COMPLETED**
(identique)

---

### Phase 10 — Sprint 12.3.E2E : Tests E2E Cabinet Vault (backend) ✅ **COMPLETED**
(identique)

---

### Phase 11 — Sprint 12.4 : Migration des secrets vers Cabinet Vault via SecretProvider ✅ **COMPLETED**
(identique)

---

### Phase 12 — Sprint 12.5 : Import backups (backend + UI) ✅ **COMPLETED**
(identique)

---

### Phase 13 — **PROTOCOL ΔΣ : Propaganda Engine**

#### Phase 13.1 (P0) — MVP Squelette ✅ **COMPLETED**
(identique)

#### Phase 13.2 (P1) — Triggers complets + Tone Engine ✅ **COMPLETED**
(identique)

#### Phase 13.3 (P2) — Dispatchers + Worker cron + Rate limiting + Onboarding ✅ **COMPLETED**
(identique)

#### Phase 13.3.x (P1) — Robustesse + opérabilité ✅ **COMPLETED**
(identique)

**Post-prod activation checklist (mise à jour)**
1) Vérifier secrets via `GET /api/admin/propaganda/dispatch/preflight`.
2) Renseigner secrets manquants dans le vault :
   - Telegram : `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
   - X : `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`
3) Activer worker en dry-run (2FA) : `POST /api/admin/propaganda/dispatch/toggle` `{enabled:true, dry_run:true}`.
4) Forcer un tick (2FA) : `POST /api/admin/propaganda/dispatch/tick-now`.
5) Vérifier que les items passent `approved → sent` avec `dry_run:true`.
6) Passer LIVE d’abord Telegram (dry_run=false, X encore off possible si creds manquants) ; puis X.
7) Sur incident : `panic=true` immédiatement.

---

### Phase 14 — **Pre-Launch Infiltration Brain (PROTOCOL ΔΣ)**

#### Phase 14.1 (P0) — Backend + Admin UI + Public Terminal flow ✅ **COMPLETED**
(identique)

#### Phase 14.2 (P2) — KOL Infiltration Logic (X/Twitter) (**IN PROGRESS**) 
**Backend scaffold livré** ; reste l’UI admin + wiring KOL mention → DM drafts.

- ✅ Backend livré (voir section état actuel).
- ⏳ **UI Admin à livrer** (session future) :
  - Review queue `x_share_submissions` (pending_review) + Approve/Reject.
  - Review queue `kol_dm_drafts` + Approve + champ edit.
  - Chips `auto/status` (telegram live, x follow blocked, pending counts).
- ⏳ **Branchement KOL Listener** (safe) : quand une mention KOL est détectée, créer un draft DM (`prepare_kol_dm_draft`) au lieu (ou en plus) de déclencher la propagande.
- ⏳ **Activation tier X** (future) : follow check live (L1), share mention live (L2), DM dispatch live.

---

### Phase 15 — **Brain Connect & Treasury Architecture (MiCA) — NEXT**
Objectif : connecter l’indexation on-chain (Helius) au lore (Propaganda Engine) **sans logique de trading**, publier une politique publique de trésorerie conforme MiCA, et ajouter l’outillage admin de disclosure + tokenomics tracker.

- **Dépendances** : mint `$DEEPOTUS` + pool address DEX (Raydium/Orca) + passage Helius en mode live.
- **Doc ops** : `/app/docs/HELIUS_POST_DEPLOY.md` (procédure webhook + auth + smoke test).
- ✅ **Pré-work livré** : treasury ops endpoints + burn summary + page `/transparency` + phases env-driven.
- ⏳ **Reste en Phase 15** : tokenomics tracker public + admin dashboard Treasury (UI logging) + disclosure pages MiCA.

---

### Phase 17 — Déploiement Vercel : Fix build CRA5 / AJV (P0) — ✅ **COMPLETED (prod live)**
- Les étapes Node20/yarn/vercel.json/rewrites sont en prod.
- Branding : watermark “Made with Emergent” supprimé.

### Phase 17.H (P3/P4) — Migration CRA → Vite (optionnel)
- But : éliminer la dette CRA5 (AJV / toolchain) et accélérer builds.
- À faire uniquement après stabilisation post-mint.

---

## 3) Next Actions

### Priorité immédiate (P0) — Finaliser dispatch LIVE
- Ajouter dans Cabinet Vault :
  - Telegram : `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
  - X : `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`
- Vérifier `GET /api/admin/propaganda/dispatch/preflight` → `ready=true`.
- Basculer dispatch : dry-run → live, plateforme par plateforme.

### P1 — Finir la grosse MAJ pre-mint/mint (2 tasks restantes)
- ⏳ **TASK 7** : `prophet_studio.py` V2 templates pondérés + toggle “Use V2” dans AdminBots.
- ⏳ **TASK 8** : AdminBots onglet “Cadence” + config quiet hours + triggers reactifs.

### P1 — Terminer Sprint 14.2 (UI + wiring)
- Ajouter UI admin review queue : shares L2 + approve KOL DM drafts.
- Branchement `kol_listener` → `prepare_kol_dm_draft`.
- (Plus tard) activer follow/search/DM live quand tier X est acquis.

### P1 — Helius live post-mint
- Suivre `/app/docs/HELIUS_POST_DEPLOY.md`.
- Enregistrer webhook sur Render backend ; supprimer ancien webhook preview.
- Renseigner `mint` + `pool_address` dès disponibles.

### P2 — Polish + Qualité
- Refactor prudent (sans changement comportement) : `AdminBots.jsx`, `TerminalPopup.tsx` (à faire en étapes, derrière tests E2E).
- Tests :
  - Pytest backend (smoke endpoints + vault + propaganda queue + treasury ops)
  - Playwright E2E (routing, login admin, vault unlock, transparency render, queue approve, banner dispatch)

---

## 4) Success Criteria
- Site prod stable sur deepotus.xyz (sans watermark).
- Cabinet Vault : secrets centralisés, 2FA active, rotations possibles.
- Helius : webhook prod enregistré, ingestion on-chain stable.
- Propaganda : dispatch live contrôlé (rate limit + panic + audit) avec 0 fuites.
- Emails : 4 templates ont un hero asset fiable (25–55KB) servi par `/api/assets` + diagnostics Resend utilisables.
- Infiltration : riddles + clearance fonctionnels ; 14.2 prêt (TG live, share review queue, KOL DM drafts) ; auto X activable quand tier OK.
- **Pre-mint/Mint UX** :
  - Les phases (pre/live/graduated) changent **uniquement via env vars**.
  - `/transparency` fonctionne en pre-mint (placeholders), et s’enrichit post-mint (BubbleMaps/RugCheck/ops).
  - Tokenomics affiche clairement locks pending/active + lien vers transparency.
  - HowToBuy affiche un guide “scan” phase-aware + BonkBot CTA.
  - Roadmap reflète l’état automatiquement.
  - BurnCounter s’alimente depuis `treasury_operations`.

---

## 5) Notes d’architecture (Phase 13–17)

**Backend**
- ✅ Propaganda : orchestrateur + triggers + queue + templates + tone engine.
- ✅ 13.3 : dispatchers + worker APScheduler + routes admin + doc ops.
- ✅ 13.3.x : retry/backoff + preflight creds + diagnostics état (résumé tick avec `retried`).
- ✅ Diagnostics Resend : `/api/admin/email/diagnostics`.
- ✅ Infiltration Brain : riddles/clearance/sleeper cell.
- ✅ Sprint 14.2 scaffold : `core/infiltration_auto.py` + endpoints verify/review/drafts.
- ✅ Whale watcher : Helius webhooks + monitoring admin (base).
- ✅ Assets email : `/api/assets` via `StaticFiles`.
- ✅ Génération IA email assets : `scripts/generate_email_asset.py` (gpt-image-1) + JPG optimisés.
- ✅ Treasury : `routers/treasury.py` (ops log + burns aggregates).

**Frontend**
- ✅ Pages admin : `pages/Propaganda.tsx`, `pages/Infiltration.tsx`, `pages/CabinetVault.tsx`.
- ✅ Propaganda UI : bannière d’état dispatch (PAUSED/DRYRUN/LIVE/PANIC).
- ✅ Terminal : `TerminalPopup.tsx` + `RiddlesFlow.tsx`.
- ✅ UX prophétie : hold 5s sur “Nouvelle prophétie” (`PropheciesFeed.tsx`).
- ✅ Phases env-driven : `src/lib/launchPhase.ts` (utilisé par Hero/HowToBuy/Tokenomics/Roadmap/Transparency).
- ✅ Nouvelle page : `pages/Transparency.tsx` + route `/transparency`.
- ✅ Tokenomics : `TokenomicsLockBadges` + `BurnCounter`.
- ✅ HowToBuy : `HowToBuyPhasedSteps`.
- ✅ Nav/Footer : liens `/transparency`.
- ⏳ Sprint 14.2 UI : review shares + approve KOL DM drafts.

**DB Collections**
- Propaganda : `propaganda_templates`, `propaganda_queue`, `propaganda_events`, `propaganda_settings`, `propaganda_triggers`, `propaganda_price_snapshots`.
- Infiltration : `riddles`, `riddle_attempts` (TTL 24h), `clearance_levels`, `sleeper_cell`, `infiltration_audit`.
- Sprint 14.2 : `x_share_submissions`, `kol_dm_drafts`.
- Treasury : `treasury_operations`.
- Email : `email_events` + champs email dans `whitelist` (`email_status`, `email_error`, etc.).
- Vault : `cabinet_vault`, `cabinet_vault_audit`, `admin_2fa`.

**Sécurité**
- Propaganda : lecture/édition templates = admin JWT ; panic/approve/reject/toggles dispatch = admin JWT + 2FA.
- Infiltration : endpoints publics rate-limit ; mutations admin = 2FA.
- Treasury admin logging : admin JWT (2FA déjà actif côté opérateur).
- Secrets dispatchers : Cabinet Vault (recommandé) avec fallback env.
- Déploiement : CRA5 doit rester sur Node LTS (20) tant que Vite pas migré.
- Recovery : Factory reset exige vault LOCKED + password + 2FA (si active) + confirm string.
- LLM : Preview utilise proxy Emergent (EMERGENT_LLM_KEY) ; prod Render préfère clés natives (Mode B).
- Images : gpt-image-1 utilisé pour assets email (offline) et bots preview (optionnel).
