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
- **Sprint 15 — Brain Connect & Treasury Architecture (MiCA)** : relier l’indexation on-chain (Helius) au lore **sans logique de trading**, publier une politique de trésorerie transparente, outillage admin de disclosure.
- **Phase 17 — Déploiement Vercel (P0)** : fiabiliser le build CRA5 en environnement Vercel (Node + install toolchain) et éliminer le crash `ajv/dist/compile/codegen`.
- **Phase 17.B — Qualité build strict (P1)** : permettre le build Vercel en mode strict **sans** workaround `CI=false`.
- **Phase 17.C — Vault anti-récidive (P1)** : empêcher le scénario “vault init → mnemonic skippé → vault inaccessible” + recovery autonome.
- **Phase 17.D — Hotfix LLM routing (P0)** : garantir Preview Emergent OK avec `EMERGENT_LLM_KEY` tout en conservant compat Render via clés natives.
- **Phase 17.E — Code review hygiene (D only) (P2)** : appliquer uniquement le cleanup “motion inline objects” (perf/memo), sans refactors structurels.
- **Phase 17.F — OpenAI image (gpt-image-1) pour preview bots (P1)** : ajouter un provider image alternatif on-demand, sans changer le dispatch réel (reste dry-run pré-mint).
- **Phase 17.G — Vercel deploy package (P1)** : livrer le trio de docs + validation pipeline locale pour que l’utilisateur finalise le déploiement en autonomie.
- **Nouvel objectif (post-prod)** : opérationnaliser l’onboarding post-déploiement (Helius/dispatch/email) via docs et assets statiques (emails) pour accélérer la mise en live et réduire les erreurs humaines.

> Stratégie : “migration gates” (tsc/build + smoke tests) à chaque sprint + validation API (curl/testing) avant activation en prod.

### État actuel (mise à jour)
- **PRODUCTION LIVE** : `https://www.deepotus.xyz` sur Vercel (frontend) + Render (backend).
- Admin : **mot de passe modifié** (rotation effectuée), **2FA activée**, vault accessible.
- **Cabinet Vault** : déverrouillé en prod ; secrets déjà saisis : **LLM / Resend / Helius**.
- **Reste à saisir** : credentials **Telegram** (bot token + chat ID) et **X** (4 secrets OAuth1.0a) dans le vault.
- Frontend : `yarn build` OK ; correction UX **Prophétie Live** (hold 5 secondes) livrée.
- Backend : ajout d’un serveur d’assets statiques `/api/assets` pour les emails (hero image).
- Ops : documentation post-déploiement Helius + documentation de fonctionnement des bots livrées.

#### Cabinet Vault (Sprints 12.x) — ✅ COMPLET
- Backend BIP39 + PBKDF2 + AES-256-GCM + audit.
- Frontend UI `/admin/cabinet-vault` + export + import + audit.
- Import/Export chiffrés validés.
- **SecretProvider** en place (vault → fallback env) + script migration secrets.
- **2FA bootstrap** : init/unlock/list/audit autorisés **sans 2FA** uniquement si vault vide. CRUD/export/import restent **2FA strict**.
- Endpoint recovery `POST /api/admin/2fa/force-reset` + guide `/app/docs/2FA_SETUP_GUIDE.md`.

#### Propaganda Engine (Sprints 13.1–13.2) — ✅ LIVRÉ end-to-end
- **Sprint 13.1 MVP** ✅ : orchestrateur + templates DB + approval queue + panic kill-switch + UI admin (Triggers/Templates/Queue/Activity).
- **Sprint 13.2 COMPLET** ✅ :
  - Triggers + analytics + tone engine (LLM).
  - Templates FR/EN.
  - Settings LLM + tab UI.

#### Sprint 13.3 — Dispatchers & Worker cron — ✅ COMPLET
- Worker APScheduler (tick toutes les 30s) : claim atomique `approved → in_flight → sent|failed`.
- Dispatchers : `telegram.sendMessage` + `X POST /2/tweets` (OAuth1.0a) + mode dry-run.
- Garde-fous : `dispatch_enabled` (default false) + `dispatch_dry_run` (default true) + rate limits.
- Routes admin + doc ops.

#### Sprint 13.3.x — Robustesse opérationnelle (pré-live) — ✅ COMPLET
- Retry/backoff exponentiel pour erreurs transientes (429/5xx/timeout/network) : **60s / 120s / 240s**, **max 3 tentatives** (`MAX_RETRIES=3`).
- Nouvel endpoint non destructif : `GET /api/admin/propaganda/dispatch/preflight` (audit des secrets Telegram/X, vault/env, sans fuite de valeurs).
- UI Admin Propaganda : **bannière de mode de dispatch** (PAUSED / DRY-RUN / LIVE / PANIC) dans `Propaganda.tsx`.
- Observabilité worker enrichie : champ `retried` dans le résumé de tick.

#### Infiltration Brain (Sprint 14.1) — ✅ Backend + ✅ Admin UI + ✅ Public Terminal flow
- Backend : riddles/clearance/sleeper cell + endpoints.
- Seeds 5 énigmes + anti-bruteforce.
- Admin UI : `/app/frontend/src/pages/Infiltration.tsx`.
- Public UX : intégration “Proof of Intelligence” via `TerminalPopup.tsx` + `RiddlesFlow.tsx`.

#### Whale Watcher & disclosures (Sprint 15/16) — ✅ BASE LIVRÉE
- `TOKENOMICS_TREASURY_POLICY.md` créé.
- Helius webhooks + worker + UI admin.
- Seeds triggers/templates : `founder_buy`, `kol_mention`.
- **Doc post-déploiement Helius** livré : `/app/docs/HELIUS_POST_DEPLOY.md`.

#### Emails transactionnels (Resend)
- ✅ Diagnostics livrés : `GET /api/admin/email/diagnostics`.
- ✅ **Email loyauté** amélioré : hero illustration IA servie depuis `/api/assets/loyalty_hero.jpg`.

#### Documentation Ops / Produit — ✅ LIVRÉE
- ✅ Helius post-deploy : `/app/docs/HELIUS_POST_DEPLOY.md` (deepotus.xyz + Render).
- ✅ Fonctionnement bots infiltration + propagande : `/app/docs/BOTS_OPERATIONS.md`.

#### Assets email — ✅ LIVRÉ
- ✅ `backend/static/loyalty_hero.jpg` (gpt-image-1), optimisé **960×540**, ~**50KB** + meta JSON.
- ✅ `server.py` monte `StaticFiles` sur `/api/assets`.
- ✅ `email_templates.render_loyalty_email()` inclut l’image + alt bilingue + lien vers `classified-vault`.

#### UX Landing — ✅ Hotfix
- ✅ `PropheciesFeed.tsx` : maintien de la prophétie live **5 secondes** après clic sur “Nouvelle prophétie” (`LIVE_HOLD_MS=5000`).

#### Restant (post-prod)
- **P0** : saisir et valider les creds Telegram + X dans le vault et passer Propaganda en LIVE progressivement.
- **P1** : Sprint 14.2 (KOL Infiltration auto-DMs + validation clearance L1/L2) — dépend du tier X API.
- **P1** : Sprint 15 (Brain Connect MiCA / Helius live) — dépend du mint + pool address.
- **P2/P3** : migration CRA→Vite (optionnel, stabilisation toolchain) — Phase 17.H.

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

#### Phase 14.2 (P2) — KOL Infiltration Logic (X/Twitter) (**UPCOMING**) 
- Automatisation “Mirror” et “Recruitment” (auto-DMs).
- Validation Clearance Levels 1 & 2 (Follow X / Join TG).
- Garde-fous : anti-spam + quotas.
- **Dépendance** : tier X API (Basic/Elevated) + endpoints follow/search/DM autorisés.

---

### Phase 15 — **Brain Connect & Treasury Architecture (MiCA) — NEXT**
Objectif : connecter l’indexation on-chain (Helius) au lore (Propaganda Engine) **sans logique de trading**, publier une politique publique de trésorerie conforme MiCA, et ajouter l’outillage admin de disclosure.

- **Dépendances** : mint `$DEEPOTUS` + pool address DEX (Raydium/Orca) + passage Helius en mode live.
- **Doc ops** : `/app/docs/HELIUS_POST_DEPLOY.md` (procédure webhook + auth + smoke test).

---

### Phase 17 — Déploiement Vercel : Fix build CRA5 / AJV (P0) — ✅ **COMPLETED (prod live)**
- Les étapes Node20/yarn/vercel.json/rewrites sont en prod.

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

### P1 — Helius live post-mint
- Suivre `/app/docs/HELIUS_POST_DEPLOY.md`.
- Enregistrer webhook sur Render backend ; supprimer ancien webhook preview.
- Renseigner `mint` + `pool_address` dès disponibles.

### P1 — Infiltration 14.2
- Activer KOL polling (tier X) + auto-validation L1/L2.

### P2 — Qualité 
- Régression tests simples (smoke) + scripts de préflight et diag.

---

## 4) Success Criteria
- Site prod stable sur deepotus.xyz.
- Cabinet Vault : secrets centralisés, 2FA active, rotations possibles.
- Helius : webhook prod enregistré, ingestion on-chain stable.
- Propaganda : dispatch live contrôlé (rate limit + panic + audit) avec 0 fuites.
- Emails : loyauté rendu cohérent (hero asset servie) + diagnostics Resend utilisables.
- Infiltration : riddles + clearance fonctionnels ; auto-validation 14.2 prête quand tier X OK.

---

## 5) Notes d’architecture (Phase 13–17)

**Backend**
- ✅ Propaganda : orchestrateur + triggers + queue + templates + tone engine.
- ✅ 13.3 : dispatchers + worker APScheduler + routes admin + doc ops.
- ✅ 13.3.x : retry/backoff + preflight creds + diagnostics état (résumé tick avec `retried`).
- ✅ Diagnostics Resend : `/api/admin/email/diagnostics`.
- ✅ Infiltration Brain : riddles/clearance/sleeper cell.
- ✅ Whale watcher : Helius webhooks + monitoring admin (base).
- ✅ Vault recovery : `factory_reset_vault()` + route sécurisée.
- ✅ LLM routing hybride (17.D) : Mode A (proxy Emergent) / Mode B (SDK natif).
- ✅ Assets email : `/api/assets` via `StaticFiles` (ex: `loyalty_hero.jpg`).
- ✅ IA illustration loyauté : `scripts/generate_loyalty_hero.py` + `backend/static/loyalty_hero.jpg`.

**Frontend**
- ✅ Panels admin : `pages/Propaganda.tsx`, `pages/Infiltration.tsx`, `pages/CabinetVault.tsx`.
- ✅ Propaganda UI : bannière d’état dispatch (PAUSED/DRYRUN/LIVE/PANIC).
- ✅ Terminal : `TerminalPopup.tsx` + `RiddlesFlow.tsx`.
- ✅ UX prophétie : hold 5s sur “Nouvelle prophétie” (`PropheciesFeed.tsx`).

**DB Collections**
- Propaganda : `propaganda_templates`, `propaganda_queue`, `propaganda_events`, `propaganda_settings`, `propaganda_triggers`, `propaganda_price_snapshots`.
- Infiltration : `riddles`, `riddle_attempts` (TTL 24h), `clearance_levels`, `sleeper_cell`.
- Email : `email_events` + champs email dans `whitelist` (`email_status`, `email_error`, etc.).
- Whale watcher / disclosure : selon implémentation courante + indexes (cf. docs).
- Vault : `cabinet_vault`, `cabinet_vault_audit`, `admin_2fa`.

**Sécurité**
- Propaganda : lecture/édition templates = admin JWT ; panic/approve/reject/toggles dispatch = admin JWT + 2FA.
- Infiltration : endpoints publics rate-limit ; mutations admin = 2FA.
- Whale watcher feed public : anonymisé.
- Secrets dispatchers : Cabinet Vault (recommandé) avec fallback env.
- Déploiement : CRA5 doit rester sur Node LTS (20) tant que Vite pas migré.
- Recovery : Factory reset exige vault LOCKED + password + 2FA (si active) + confirm string.
- LLM : Preview utilise proxy Emergent (EMERGENT_LLM_KEY) ; prod Render préfère clés natives (Mode B).
- Images : gpt-image-1 utilisé pour assets email (offline) et bots preview (optionnel).