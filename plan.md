# DEEPOTUS — Plan de finalisation TypeScript & sécurité “Cabinet Vault” **+ Propaganda Engine ΔΣ**
(Sprints 6 → 13.3 + Infiltration 14.x + Brain Connect 15.x + Déploiements 17 + Hardening 22.x → 24 + Sprint 23/24)

## 1) Objectives
- Stabiliser et clarifier le code **sans refactors risqués pré-launch** ; privilégier des fixes “safe” (build gates, guards sécurité, docs, tooling).
- Compléter la migration TS/TSX **sur le code applicatif** (hors Shadcn UI auto-généré), puis **durcir progressivement** le typage.
- Garantir une base prête pour un déploiement **Vercel (frontend) / Render (backend)** avec builds production OK.
- Préserver le comportement actuel (bots, vault, ROI, intro, admin) et éviter les surprises en prod.
- **Centraliser la gestion des secrets** via le **Cabinet Vault** (AES-256-GCM) et conserver la discipline : **pas de clés en `.env`** si elles doivent vivre dans le coffre.
- **Conformité sécurité** : 2FA côté admin pour les actions sensibles, audit logging, rotation, export/import de backups chiffrés.
- **PROTOCOL ΔΣ — Propaganda Engine** : logique scenario-based (triggers → queue → dispatch) avec garde-fous anti-slop, testable pré-mint via Manual Fire, opérable via UI admin.
- **PROTOCOL ΔΣ — Infiltration Brain** : livrer l’expérience publique “Proof of Intelligence” + surface admin conforme posture sécurité.
- **Sprint 14.2 — Infiltration Automation** : vérifications semi-automatiques (TG live, X review queue), + KOL DM drafts (approval mode) via UI.
- **Sprint 15 — Brain Connect & Treasury Architecture (MiCA)** : relier indexation on-chain (Helius) au lore **sans trading**, publier une politique de trésorerie transparente, outillage admin de disclosure + tokenomics tracker public.
- **Nouvel objectif (Pre-mint UX / deep-linking)** : assurer un parcours “recrutement / accréditation” sans friction via un deep-link unique `/#accreditation`.
- **Ops post-prod** : réduire les erreurs humaines (déploiement, secrets, webhooks) via docs exécutables, endpoints diagnostics, et tests automatisés.

> Stratégie : “migration gates” (tsc/build + smoke tests) à chaque sprint + validation API (curl/testing) avant activation en prod.

### État actuel (mise à jour)
- **PRODUCTION LIVE** : `https://www.deepotus.xyz` sur Vercel (frontend) + Render (backend).
- **TypeScript** : migration complète, `noImplicitAny: true`, `npx tsc --noEmit` : 0 erreurs.
- **Cabinet Vault** : AES-256-GCM + lecture stricte par les dispatchers.
- **Propaganda Engine** : dispatchers **X + Telegram LIVE** (réels) et branchés aux APIs, via secrets du vault.
- **Transparence MiCA** : page `/transparency` alimentée dynamiquement par le **Public Wallet Registry** (badges LOCKED/PENDING) + intégration RugCheck.
- **Tests** : backend Pytest (63 tests) + Playwright E2E + CI GitHub Actions.
- **UX micro-sprint (deep-link)** : `#accreditation` **déplacé** de Whitelist → **VaultSection**. L’accès à `/#accreditation` ou un `hashchange` ouvre automatiquement le **TerminalPopup DS-GATE-02** et déclenche un pulse ambre 2.6s autour du CTA.
- **Pré-launch standby** : en attente de vérification finale déploiement/production par l’utilisateur.

#### Cabinet Vault (Sprints 12.x) — ✅ COMPLET
- Backend : AES-256-GCM + audit.
- Frontend UI : `/admin/cabinet-vault`.
- Secrets sensibles gérés via le vault (pas de fuite `.env`).

#### Propaganda Engine (Sprints 13.1–13.3.x + Activation Live) — ✅ LIVRÉ end-to-end
- Triggers/templates/queue/dispatch + worker.
- X + Telegram : dispatch réel activé.

#### Infiltration Brain (Sprint 14.1) — ✅ Backend + ✅ Admin UI + ✅ Public Terminal flow
- Riddles/clearance + UX terminal.

#### Sprint 14.2 — Infiltration Automation — ✅ BACKEND + ✅ UI ADMIN LIVRÉE
- `AutoReviewTab.tsx` monté sur `/admin/infiltration`.

#### Transparence & confiance (Wallet Registry) — ✅ LIVRÉ
- CRUD admin + mapping public.
- `/transparency` dynamique + RugCheck.

#### Sprint 22 → 24 — Hardening TypeScript & tests — ✅ COMPLET
- `noImplicitAny: true`.
- CI E2E Playwright.

#### UX Micro-sprint — Deep-link `#accreditation` — ✅ COMPLET
- Anchor `#accreditation` pointe désormais vers le **bouton d’accréditation** (Vault).
- Auto-open TerminalPopup sur `/#accreditation` et sur `hashchange`.
- Pulse CTA 2.6s.
- Playwright : nouvelle spec `accreditation-deeplink.spec.ts` (3 tests, ~19.6s, green).
- Testing agent : sweep complet 100% backend/frontend/integration, 0 bug.

#### Helius live post-mint (Sprint 15/Brain Connect) — ⛔ BLOQUÉ
- Attente du mint + pool DEX.
- Procédure : `/app/docs/HELIUS_POST_DEPLOY.md`.

Docs récentes :
- `/app/docs/SPRINT_22_3_5_DEPLOY.md`
- `/app/docs/SPRINT_14_2_23_24_DEPLOY.md`
- `/app/docs/SPRINT_P1_LIVE_ACTIVATION.md`

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

### Phase 8 — Sprint 12.2 : Cabinet Vault Backend (AES-256-GCM) ✅ **COMPLETED**
(identique)

---

### Phase 9 — Sprint 12.3 : Cabinet Vault Frontend UI ✅ **COMPLETED**
(identique)

---

### Phase 10 — Sprint 12.4 : SecretProvider + discipline secrets ✅ **COMPLETED**
(identique)

---

### Phase 13 — **PROTOCOL ΔΣ : Propaganda Engine** ✅ **COMPLETED**
(identique, + activation live déjà effectuée)

---

### Phase 14 — **Pre-Launch Infiltration Brain (PROTOCOL ΔΣ)** ✅ **COMPLETED**
(identique)

---

### Phase 14.2 — Infiltration Automation ✅ **COMPLETED**
(identique)

---

### Phase 14.3 — UX Micro-sprint : Deep-link Accréditation ✅ **COMPLETED**
Objectif : rendre `/#accreditation` “actionnable” (scroll + open gate) et le relier au bon CTA.
- ✅ Déplacer l’ancre `#accreditation` de **Whitelist** vers **VaultSection** (bouton “Demander un niveau d'accréditation”).
- ✅ Sur `/#accreditation` : attendre fin intro (IntersectionObserver) → scroll → auto-open TerminalPopup DS-GATE-02.
- ✅ Sur `hashchange` : re-trigger identique.
- ✅ Pulse visuel 2.6s autour du wrapper CTA (`data-cta-pulse=true`).
- ✅ Playwright : `e2e/specs/accreditation-deeplink.spec.ts` (3 tests).
- ✅ Sweep QA : 100% OK.

---

### Phase 15 — **Brain Connect & Treasury Architecture (MiCA) — NEXT**
Objectif : connecter l’indexation on-chain (Helius) au lore (Propaganda Engine) **sans logique de trading**, publier une politique publique de trésorerie conforme MiCA, et ajouter l’outillage admin de disclosure + tokenomics tracker.
- **Dépendances** : mint `$DEEPOTUS` + pool address DEX + passage Helius en mode live.
- **Doc ops** : `/app/docs/HELIUS_POST_DEPLOY.md`.
- ✅ Pré-work livré : `/transparency`, registry, ops logs.
- ⛔ Bloqué : Helius live tant que mint/pool pas disponibles.

---

### Phase 17 — Déploiement Vercel/Render — ✅ **COMPLETED (prod live)**
(identique)

---

### Phase 22–24 — TypeScript Hardening & Tests — ✅ **COMPLETED**
(identique)

---

## 3) Next Actions

### Priorité immédiate (P0) — Vérification finale de déploiement
- L’utilisateur push sur `main` + redéploiement Render/Vercel.
- En cas de bug prod :
  - vérifier logs Render backend (connexions Mongo, Vault unlock, timeouts dispatchers),
  - vérifier `REACT_APP_BACKEND_URL` / CORS,
  - relancer `pytest` + smoke E2E.

### P1 — Exploitation Propaganda Engine (post-vérif prod)
- Vérifier la santé dispatch : preflight + tick-now.
- Confirmer que la lecture des secrets provient **uniquement** du Cabinet Vault.

### P2 — Refactors prudents (post-launch, optionnel)
- Split composants trop gros (behaviour inchangé) :
  - `TerminalPopup.tsx`
  - `RiddlesFlow.tsx`
  - `Admin.tsx`
- Garder “behaviour parity” et verrouiller via Playwright.

### P3 — Helius live post-mint
- Suivre `/app/docs/HELIUS_POST_DEPLOY.md`.
- Renseigner mint + pool dès disponibles.

### P4 — Extension Playwright
- Ajouter smoke `/transparency`.
- Ajouter smoke “Propaganda queue end-to-end” (approve → dispatch dry-run/live).

---

## 4) Success Criteria
- Site prod stable sur deepotus.xyz.
- Cabinet Vault : secrets centralisés, 2FA active, rotation possible.
- Propaganda : dispatch live contrôlé (rate limit + panic + audit) avec 0 fuite.
- Transparence : Wallet Registry public + `/transparency` dynamique et maintenable.
- Infiltration : riddles + clearance + auto-review opérables.
- UX Accréditation : `/#accreditation` ouvre le TerminalPopup DS-GATE-02 automatiquement (scroll + pulse) ; aucun ancrage résiduel dans Whitelist.
- Qualité & hardening :
  - ✅ `tsc --noEmit` = 0 erreurs
  - ✅ `noImplicitAny: true`
  - ✅ `pytest` backend : 63 tests passent
  - ✅ Playwright E2E : specs + CI workflow

---

## 5) Notes d’architecture (Phase 13–26)

**Backend**
- ✅ Propaganda : orchestrateur + triggers + queue + templates + tone engine.
- ✅ Dispatchers + worker APScheduler + routes admin + doc ops.
- ✅ Retry/backoff + preflight creds + diagnostics état.
- ✅ Infiltration Brain : riddles/clearance/sleeper cell.
- ✅ Transparence : Wallet Registry CRUD + endpoint public.
- ✅ Tests : Pytest + E2E bootstrap.

**Frontend**
- ✅ Vault : `VaultSection.tsx` (CTA + TerminalPopup).
- ✅ Terminal : `TerminalPopup.tsx` + `RiddlesFlow.tsx`.
- ✅ Whitelist : formulaire mailing list (désolidarisé du deep-link accréditation).
- ✅ `/transparency` dynamique.
- ✅ TS strict : `noImplicitAny: true`.

**E2E (Playwright)**
- ✅ Bootstrap : `/app/e2e/`.
- ✅ Spec deep-link : `specs/accreditation-deeplink.spec.ts`.
- ✅ CI : `.github/workflows/e2e-smoke.yml`.

**DB Collections**
- Propaganda : `propaganda_templates`, `propaganda_queue`, `propaganda_events`, `propaganda_settings`, `propaganda_triggers`, `propaganda_price_snapshots`.
- Infiltration : `riddles`, `riddle_attempts` (TTL 24h), `clearance_levels`, `sleeper_cell`, `infiltration_audit`.
- 14.2 : `x_share_submissions`, `kol_dm_drafts`.
- Treasury : `treasury_operations`.
- Transparence : `wallet_registry`.
- Vault : `cabinet_vault`, `cabinet_vault_audit`, `admin_2fa`.

**Sécurité**
- Mutations sensibles (panic/toggles/approvals) : admin + 2FA.
- Secrets dispatchers : Cabinet Vault (AES-256-GCM), pas de `.env`.
- Déploiement : garder les gates `tsc` + smoke E2E.
