# DEEPOTUS — Plan de finalisation TypeScript & sécurité “Cabinet Vault” **+ Propaganda Engine ΔΣ**
(Sprints 6 → 13.3 + Infiltration 14.x + Brain Connect 15.x + Déploiements 17 + Hardening 22.x → 24 + Sprint 23/24)

## 1) Objectives
- Stabiliser et clarifier le code **sans refactors risqués pré-launch** ; privilégier des fixes “safe” (build gates, guards sécurité, docs, tooling).
- Compléter la migration TS/TSX **sur le code applicatif** (hors Shadcn UI auto-généré), puis **durcir progressivement** le typage.
- Garantir une base prête pour un déploiement **Vercel (frontend) / Render (backend)** avec builds production OK.
- Préserver le comportement actuel (bots en **dry-run** tant que credentials non fournis, vault, ROI, intro, admin).
- **Centraliser la gestion des secrets** via le **Cabinet Vault** (BIP39 + PBKDF2 + AES-256-GCM) et migrer les clés existantes (LLM, Resend, Helius, bots) vers ce coffre.
- **Conformité sécurité** : 2FA côté admin pour les actions sensibles, audit logging, rotation, export/import de backups chiffrés.
- **PROTOCOL ΔΣ — Propaganda Engine** : automatiser une logique “scenario-based” (triggers marché → message → queue → dispatch) pour réagir au marché avec garde-fous anti-slop, **testable pré-mint** via Manual Fire, et opérable via UI admin.
- **PROTOCOL ΔΣ — Infiltration Brain** : livrer l’expérience publique “Proof of Intelligence” (énigmes Terminal → clearance) + surface admin conforme posture sécurité.
- **Sprint 14.2 — Infiltration Automation** : ajouter des vérifications semi-automatiques **sans dépendre du tier X** (TG live, X en review queue), + préparation KOL DM drafts (approval mode) **avec UI opérable**.
- **Sprint 15 — Brain Connect & Treasury Architecture (MiCA)** : relier l’indexation on-chain (Helius) au lore **sans logique de trading**, publier une politique de trésorerie transparente, outillage admin de disclosure + tokenomics tracker public.
- **Ops post-prod** : réduire les erreurs humaines (déploiement, secrets, webhooks) via docs exécutables, endpoints diagnostics, et assets email hébergés.
- **Nouvel objectif (Pre-mint/Mint UX)** : aligner landing + pages publiques sur une stratégie **3 phases env-driven** (pre-mint / live / graduated), + page `/transparency` MiCA-style, + logs Treasury publics.
- **Objectif (Hardening 22.x → 24, maintenant atteint en grande partie)** :
  - Durcir TypeScript **sans bascule brutale** (progressif), puis activer `noImplicitAny`.
  - Augmenter la robustesse via tests : **pytest** backend + **Playwright E2E** + intégration CI.

> Stratégie : “migration gates” (tsc/build + smoke tests) à chaque sprint + validation API (curl/testing) avant activation en prod.

### État actuel (mise à jour)
- **PRODUCTION LIVE** : `https://www.deepotus.xyz` sur Vercel (frontend) + Render (backend).
- Admin : **mot de passe modifié** (rotation effectuée), **2FA activée**, vault accessible.
- **Cabinet Vault** : déverrouillé en prod ; secrets déjà saisis : **LLM / Resend / Helius**.
- **Reste à saisir** : credentials **Telegram** (bot token + chat ID) et **X** (4 secrets OAuth1.0a) dans le vault.
- Branding : watermark **“Made with Emergent” supprimé**.
- Déploiement : doc **push GitHub + Deploy Hook Vercel** livrée.
- Emails : 4 hero images IA (25–55KB) servies via `/api/assets`, intégrées aux templates.
- Phases env-driven + `/transparency` MiCA-style + landing 3 phases : **livré**.

#### Cabinet Vault (Sprints 12.x) — ✅ COMPLET
- Backend BIP39 + PBKDF2 + AES-256-GCM + audit.
- Frontend UI `/admin/cabinet-vault` + export + import + audit.
- Import/Export chiffrés validés.
- **SecretProvider** en place (vault → fallback env) + script migration secrets.
- **Bootstrap writes** : writes autorisés sans 2FA jusqu’à `BOOTSTRAP_WRITE_LIMIT=30` ; reads/export/import restent **2FA strict**.
- Endpoint recovery `POST /api/admin/2fa/force-reset` + guide `/app/docs/2FA_SETUP_GUIDE.md`.

#### Propaganda Engine (Sprints 13.1–13.3.x) — ✅ LIVRÉ end-to-end
- MVP + triggers + templates + queue + analytics + tone engine.
- Dispatchers TG/X + worker APScheduler + mode dry-run + kill switch.
- Robustesse : retry/backoff + preflight creds + bannière mode dispatch.

#### Infiltration Brain (Sprint 14.1) — ✅ Backend + ✅ Admin UI + ✅ Public Terminal flow
- Riddles/clearance/sleeper cell + anti-bruteforce.
- Admin UI : `frontend/src/pages/Infiltration.tsx`.
- Public UX : `TerminalPopup.tsx` + `RiddlesFlow.tsx`.

#### Sprint 14.2 — Infiltration Automation — ✅ BACKEND + ✅ UI ADMIN LIVRÉE
- Backend scaffold : `backend/core/infiltration_auto.py` + endpoints.
- **UI admin livrée (Sprint 14.2 UI)** : `frontend/src/pages/infiltration/AutoReviewTab.tsx` monté comme **5ème tab** sur `/admin/infiltration`.
  - Status chips : Telegram LIVE / X follow BLOCKED·X_TIER_REQUIRED / X share MANUAL REVIEW / KOL DRAFT QUEUE.
  - Review queue L2 `x_share_submissions` : Approve/Reject + note optionnelle.
  - KOL DM drafts : textarea inline éditable + Approve.
  - Auto-poll 30s + refresh manuel.
  - `data-testid` stables (≈21) pour E2E.

#### Whale Watcher & disclosures (Sprint 15/16) — ✅ BASE LIVRÉE
- `TOKENOMICS_TREASURY_POLICY.md` créé.
- Helius webhooks + worker + UI admin.
- Seeds triggers/templates : `founder_buy`, `kol_mention`.
- **Doc post-déploiement Helius** : `/app/docs/HELIUS_POST_DEPLOY.md`.

#### Sprint 21 — Refactor (zero new feature) — ✅ COMPLET
- `AdminBots.jsx` 1798 → 1017 lignes via extraction sections.
- `cadence_engine.py` split + **25 tests**.

#### Sprint 22 — Migration TypeScript (soft) — ✅ 22.1 → 22.5 COMPLET
- 22.1 : `index.tsx`, `App.tsx`, `AdminBots.tsx`.
- 22.2 : `AdminVault.tsx` (constaté terminé).
- 22.3 : extraction **Custom LLM keys** (`CustomLlmKeysSection.tsx`), `AdminBots.tsx` **1037 → 743**.
- 22.4 : hardening TS allégé (274 → 140 erreurs noImplicitAny).
- 22.5 : tests : pytest **25 → 57** + Playwright bootstrap `/app/e2e/`.

#### Sprint 23 — `noImplicitAny` final + flip — ✅ COMPLET
- Correction des ~140 erreurs restantes `--noImplicitAny` (≈30+ fichiers touchés).
- **`noImplicitAny: true` activé** dans `frontend/tsconfig.json`.
- `npx tsc --noEmit` : 0 erreurs, webpack hot-reload OK.

#### Sprint 24 — Playwright en CI — ✅ COMPLET
- Workflow GitHub Actions : `.github/workflows/e2e-smoke.yml`
  - PR + nightly (03:00 UTC) + manual dispatch (`base_url` override)
  - Ubuntu 22.04, Chromium, workers=1, yarn cache
  - Artifacts on failure : HTML report + traces
- Doc : `.github/workflows/README.md` (secret matrix + runbook)

#### Helius live post-mint (Sprint 15/Brain Connect) — ⛔ BLOQUÉ
- Aucun changement possible tant que le mint n’a pas eu lieu.
- Procédure à suivre : `/app/docs/HELIUS_POST_DEPLOY.md`.

Docs récentes :
- `/app/docs/SPRINT_22_3_5_DEPLOY.md`
- `/app/docs/SPRINT_14_2_23_24_DEPLOY.md`

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
6) Passer LIVE d’abord Telegram (dry_run=false), puis X.
7) Sur incident : `panic=true` immédiatement.

---

### Phase 14 — **Pre-Launch Infiltration Brain (PROTOCOL ΔΣ)**

#### Phase 14.1 (P0) — Backend + Admin UI + Public Terminal flow ✅ **COMPLETED**
(identique)

#### Phase 14.2 (P2) — Infiltration Automation (TG live + X review queue + KOL drafts) ✅ **COMPLETED**
- ✅ Backend livré (verify endpoints + admin endpoints).
- ✅ UI admin livrée : `AutoReviewTab.tsx` (status + L2 review + KOL drafts).
- ⏳ (Future) Activation tier X : follow check live (L1), share mention live (L2), DM dispatch live.
- ⏳ (Future) Wiring “safe” : `kol_listener` → `prepare_kol_dm_draft` renforcé / vérifié selon la stratégie finale.

---

### Phase 15 — **Brain Connect & Treasury Architecture (MiCA) — NEXT**
Objectif : connecter l’indexation on-chain (Helius) au lore (Propaganda Engine) **sans logique de trading**, publier une politique publique de trésorerie conforme MiCA, et ajouter l’outillage admin de disclosure + tokenomics tracker.

- **Dépendances** : mint `$DEEPOTUS` + pool address DEX + passage Helius en mode live.
- **Doc ops** : `/app/docs/HELIUS_POST_DEPLOY.md`.
- ✅ Pré-work livré : treasury ops endpoints + burn summary + page `/transparency` + phases env-driven.
- ⛔ Bloqué : passage Helius live tant que mint/pool pas disponibles.

---

### Phase 17 — Déploiement Vercel : Fix build CRA5 / AJV (P0) — ✅ **COMPLETED (prod live)**
(identique)

### Phase 17.H (P3/P4) — Migration CRA → Vite (optionnel)
- À faire uniquement après stabilisation post-mint.

---

### Phase 22 — TypeScript Hardening & Tests — ✅ **COMPLETED**
(voir état actuel)

### Phase 23 — `noImplicitAny` final + flip — ✅ **COMPLETED**
- `noImplicitAny: true` activé.
- `tsc --noEmit` clean.

### Phase 24 — Playwright CI — ✅ **COMPLETED**
- GitHub Actions `e2e-smoke.yml` + README secrets.

---

## 3) Next Actions

### Priorité immédiate (P0) — Finaliser dispatch LIVE
- Ajouter dans Cabinet Vault :
  - Telegram : `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
  - X : `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`
- Vérifier `GET /api/admin/propaganda/dispatch/preflight` → `ready=true`.
- Basculer dispatch : dry-run → live, plateforme par plateforme.

### P2 — Refactors prudents (post-hardening, maintenant plus sûr)
- Split composants trop gros (comportement inchangé) :
  - `TerminalPopup.tsx` (~962 lignes)
  - `RiddlesFlow.tsx` (~980 lignes)
  - `Admin.tsx` (~632 lignes)
- Garder “behaviour parity” et verrouiller via Playwright.

### P3 — Helius live post-mint
- Suivre `/app/docs/HELIUS_POST_DEPLOY.md`.
- Enregistrer webhook sur Render backend ; supprimer ancien webhook preview.
- Renseigner `mint` + `pool_address` dès disponibles.

### P3/P4 — Hardening TypeScript “strict” (future)
- **Sprint 25** : activer `strictNullChecks: true` et corriger la vague d’erreurs.
- **Sprint 25/26** : éventuellement `strict: true` une fois le legacy résiduel stabilisé.

### P4 — Extension Playwright (future)
- **Sprint 26** : étendre couverture :
  - fixture phase-switching (pre-mint/live/graduated)
  - `/transparency` smoke
  - admin vault + propaganda approval queue end-to-end

---

## 4) Success Criteria
- Site prod stable sur deepotus.xyz (sans watermark).
- Cabinet Vault : secrets centralisés, 2FA active, rotations possibles.
- Helius : webhook prod enregistré, ingestion on-chain stable (post-mint).
- Propaganda : dispatch live contrôlé (rate limit + panic + audit) avec 0 fuite.
- Emails : hero assets fiables via `/api/assets` + diagnostics Resend utilisables.
- Infiltration : riddles + clearance fonctionnels ; **14.2 opérable** (TG live, share review queue, KOL DM drafts) ; X activable quand tier OK.
- **Pre-mint/Mint UX** : phases env-driven, `/transparency` enrichie post-mint, tokenomics/how-to-buy/roadmap/burncounter cohérents.
- **Qualité & hardening** :
  - ✅ `tsc --noEmit` = 0 erreurs.
  - ✅ `noImplicitAny: true`.
  - ✅ `pytest` backend : 57 tests passent.
  - ✅ Playwright E2E : bootstrap présent + **CI workflow** en place.

---

## 5) Notes d’architecture (Phase 13–26)

**Backend**
- ✅ Propaganda : orchestrateur + triggers + queue + templates + tone engine.
- ✅ Dispatchers + worker APScheduler + routes admin + doc ops.
- ✅ Retry/backoff + preflight creds + diagnostics état.
- ✅ Diagnostics Resend : `/api/admin/email/diagnostics`.
- ✅ Infiltration Brain : riddles/clearance/sleeper cell.
- ✅ 14.2 : `core/infiltration_auto.py` + endpoints verify/review/drafts.
- ✅ Whale watcher : Helius webhooks + monitoring admin (base).
- ✅ Assets email : `/api/assets` via `StaticFiles`.
- ✅ Treasury : `routers/treasury.py` (ops log + burns aggregates).
- ✅ Tests :
  - `backend/tests/test_cadence_engine_helpers.py` (25)
  - `backend/tests/test_whale_watcher_helpers.py`
  - `backend/tests/test_clearance_levels_helpers.py`

**Frontend**
- ✅ Pages admin : `Propaganda.tsx`, `Infiltration.tsx`, `CabinetVault.tsx`, `AdminVault.tsx`.
- ✅ 14.2 UI : `pages/infiltration/AutoReviewTab.tsx`.
- ✅ Terminal : `TerminalPopup.tsx` + `RiddlesFlow.tsx`.
- ✅ Phases env-driven : `src/lib/launchPhase.ts`.
- ✅ `/transparency` + composants associés.
- ✅ `AdminBots.tsx` : sections extraites + `CustomLlmKeysSection`.
- ✅ TS hardening : `noImplicitAny: true`.

**E2E (Playwright)**
- ✅ Bootstrap : `/app/e2e/` (3 smoke tests).
- ✅ CI : `.github/workflows/e2e-smoke.yml` + README secrets.

**DB Collections**
- Propaganda : `propaganda_templates`, `propaganda_queue`, `propaganda_events`, `propaganda_settings`, `propaganda_triggers`, `propaganda_price_snapshots`.
- Infiltration : `riddles`, `riddle_attempts` (TTL 24h), `clearance_levels`, `sleeper_cell`, `infiltration_audit`.
- 14.2 : `x_share_submissions`, `kol_dm_drafts`.
- Treasury : `treasury_operations`.
- Email : `email_events` + champs email dans `whitelist`.
- Vault : `cabinet_vault`, `cabinet_vault_audit`, `admin_2fa`.

**Sécurité**
- Propaganda : lecture/édition templates = admin JWT ; panic/approve/reject/toggles dispatch = admin JWT + 2FA.
- Infiltration : endpoints publics rate-limit ; mutations admin = 2FA.
- Treasury admin logging : admin JWT.
- Secrets dispatchers : Cabinet Vault recommandé (fallback env).
- Déploiement : CRA5 sur Node 20 tant que Vite pas migré.
- LLM : preview via proxy Emergent ; prod Render préfère clés natives.
