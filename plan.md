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

> Stratégie : “migration gates” (tsc/build + smoke tests) à chaque sprint + validation API (curl/testing) avant activation en prod.

### État actuel (mise à jour)
- **PRODUCTION LIVE** : `https://www.deepotus.xyz` sur Vercel (frontend) + Render (backend).
- Admin : **mot de passe modifié** (rotation effectuée), **2FA activée**, vault accessible.
- **Cabinet Vault** : déverrouillé en prod ; secrets déjà saisis : **LLM / Resend / Helius**.
- **Reste à saisir** : credentials **Telegram** (bot token + chat ID) et **X** (4 secrets OAuth1.0a) dans le vault.
- Frontend : `yarn build` OK ; correction UX **Prophétie Live** (hold 5 secondes) livrée.
- Backend : serveur d’assets statiques `/api/assets` pour emails (hero images), et génération IA des assets email.
- Ops : documentation post-déploiement Helius + documentation de fonctionnement des bots livrées.
- Branding : watermark **“Made with Emergent” supprimé** (frontend `public/index.html`).
- Déploiement : doc **push GitHub + Deploy Hook Vercel** livrée (Hobby plan).

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
- ⏳ **UI Admin à livrer** :
  - Sur `/admin/clearance` ou `/admin/infiltration` :
    - Liste des `x_share_submissions` (pending_review) + boutons Approve/Reject.
    - Liste des `kol_dm_drafts` + bouton Approve + champ edit DM.
    - Chip d’état `auto/status` (telegram live, x follow blocked, share review count, dm drafts count).
- ⏳ **Branchement KOL Listener** (safe) : quand une mention KOL est détectée, créer un draft DM (`prepare_kol_dm_draft`) au lieu (ou en plus) de déclencher la propagande.
- ⏳ **Activation tier X** (future) : 
  - follow check live (L1)
  - share mention live (L2)
  - DM dispatch live

---

### Phase 15 — **Brain Connect & Treasury Architecture (MiCA) — NEXT**
Objectif : connecter l’indexation on-chain (Helius) au lore (Propaganda Engine) **sans logique de trading**, publier une politique publique de trésorerie conforme MiCA, et ajouter l’outillage admin de disclosure + tokenomics tracker.

- **Dépendances** : mint `$DEEPOTUS` + pool address DEX (Raydium/Orca) + passage Helius en mode live.
- **Doc ops** : `/app/docs/HELIUS_POST_DEPLOY.md` (procédure webhook + auth + smoke test).

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

### P1 — Terminer Sprint 14.2 (UI + wiring)
- Ajouter UI admin review queue : shares L2 + drafts KOL DM.
- Branchement `kol_listener` → `prepare_kol_dm_draft`.
- (Plus tard) activer follow/search/DM live quand tier X Basic est acquis.

### P1 — Helius live post-mint
- Suivre `/app/docs/HELIUS_POST_DEPLOY.md`.
- Enregistrer webhook sur Render backend ; supprimer ancien webhook preview.
- Renseigner `mint` + `pool_address` dès disponibles.

### P2 — Polish + Qualité
- Refactor prudent (sans changement comportement) : `AdminBots.jsx`, `TerminalPopup.tsx` (à faire en étapes, derrière tests E2E).
- Tests :
  - Pytest backend (smoke endpoints + vault + propaganda queue)
  - Playwright E2E (routing Vercel, login admin, vault unlock, queue approve, banner dispatch)

---

## 4) Success Criteria
- Site prod stable sur deepotus.xyz (sans watermark).
- Cabinet Vault : secrets centralisés, 2FA active, rotations possibles.
- Helius : webhook prod enregistré, ingestion on-chain stable.
- Propaganda : dispatch live contrôlé (rate limit + panic + audit) avec 0 fuites.
- Emails : 4 templates ont un hero asset fiable (25–55KB) servi par `/api/assets` + diagnostics Resend utilisables.
- Infiltration : riddles + clearance fonctionnels ; 14.2 prêt (TG live, share review queue, KOL DM drafts) ; auto X activable quand tier OK.

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

**Frontend**
- ✅ Panels admin : `pages/Propaganda.tsx`, `pages/Infiltration.tsx`, `pages/CabinetVault.tsx`.
- ✅ Propaganda UI : bannière d’état dispatch (PAUSED/DRYRUN/LIVE/PANIC).
- ✅ Terminal : `TerminalPopup.tsx` + `RiddlesFlow.tsx`.
- ✅ UX prophétie : hold 5s sur “Nouvelle prophétie” (`PropheciesFeed.tsx`).
- ⏳ Sprint 14.2 UI : review shares + approve KOL DM drafts (à livrer).

**DB Collections**
- Propaganda : `propaganda_templates`, `propaganda_queue`, `propaganda_events`, `propaganda_settings`, `propaganda_triggers`, `propaganda_price_snapshots`.
- Infiltration : `riddles`, `riddle_attempts` (TTL 24h), `clearance_levels`, `sleeper_cell`, `infiltration_audit`.
- Sprint 14.2 : `x_share_submissions`, `kol_dm_drafts`.
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