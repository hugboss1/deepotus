# DEEPOTUS — Plan de finalisation TypeScript & sécurité “Cabinet Vault” (Sprints 6 → 12.5)

## 1) Objectives
- Stabiliser et clarifier le code (split des gros composants, réduction de complexité) **avant** migration d’hébergement (Vercel/Render).
- Augmenter la couverture TS/TSX sur le code **applicatif** (hors Shadcn UI auto-généré), sans casser l’existant.
- Garantir une base prête pour un déploiement **Vercel (frontend) / Render (backend)** avec builds production OK.
- Préserver le comportement actuel (bots en **dry-run**, vault, ROI, intro, admin).
- **Centraliser la gestion des secrets** via le **Cabinet Vault** (BIP39 + PBKDF2 + AES-256-GCM) et migrer les clés existantes (LLM, Resend, Helius, bots) vers ce coffre.
- **Conformité sécurité** : 2FA obligatoire côté admin pour les actions sensibles, audit logging, rotation, export/import de backups chiffrés.

> Stratégie : “migration gates” (tsc/build + smoke tests) à chaque sprint.

### État actuel (mise à jour)
- Couverture TS/TSX : **~94% du frontend** migré (reste quelques gros JSX stables : `AdminBots.jsx`, `AdminVault.jsx` — migration différée post-déploiement).
- Sécurité session : migration `localStorage` → **`sessionStorage`** effectuée.
- Build : **`yarn build` OK** + doc déploiement (`DEPLOY.md`).
- **Cabinet Vault** complet end-to-end :
  - Backend BIP39 + PBKDF2 + AES-256-GCM + audit ✅
  - Frontend UI `/admin/cabinet-vault` + export + import + audit ✅
  - **Import/Export chiffrés** validés ✅
- **SecretProvider** (Sprint 12.4) en place : lecture Vault (si unlocked) → fallback env contrôlé ✅
- Tests automatisés (subagents) :
  - **Iteration 16** : backend Cabinet Vault (12.3.E2E backend) ✅
  - **Iteration 17** : régression Sprint 12.4 (SecretProvider) ✅
  - **Iteration 18** : Sprint 12.5 Import/Export (22/22) ✅

---

## 2) Implementation Steps

### Phase 1 — Sprint 6 (P0) : Core admin maintenable (splits + TS) ✅ **COMPLETED**
**User stories (min 5)**
1. En tant qu’admin, je veux des onglets admin rapides à comprendre (fichiers courts) pour modifier sans risque.
2. En tant qu’admin, je veux que le tableau Bots soit découpé par sections pour isoler les bugs.
3. En tant qu’admin, je veux conserver le login (sessionStorage) sans régression.
4. En tant qu’admin, je veux que les pages Admin/Vault/Bots restent 100% fonctionnelles après refactor.
5. En tant que développeur, je veux que `tsc --noEmit` reste vert pendant la migration.

**Travaux (réalisés)**
- ✅ `pages/Admin.jsx` → **`pages/Admin.tsx`** + split en composants/sections TSX.
- ✅ Extraction sections `NewsFeedSection.tsx`, `HeliusSection.tsx`.
- ✅ `TerminalPopup.jsx` → `TerminalPopup.tsx`.
- ✅ `AdminEmails.jsx` → `AdminEmails.tsx`.
- ✅ Types consolidés dans `src/types/index.ts`.

**Validation gate (réalisée)**
- ✅ `npx tsc --noEmit` OK
- ✅ Webpack dev OK
- ✅ Smoke test manuel des routes admin + landing.

---

### Phase 2 — Sprint 7 (P1) : Landing components (TSX) ✅ **COMPLETED**
**Résumé**
- Migration majeure de composants landing vers TSX, stabilisation i18n, conservation UX.

**Validation gate**
- ✅ `npx tsc --noEmit` OK
- ✅ Webpack compile OK
- ✅ Smoke test landing (scroll, ROI, toggles theme/lang, vault interactions).

---

### Phase 3 — Sprint 8 (P2) : Pages applicatives (TSX) ✅ **COMPLETED**
**Résumé**
- Migration des pages principales vers TSX (Landing/Operation/HowToBuy/PublicStats/ClassifiedVault) + corrections bundler.

**Validation gate**
- ✅ `npx tsc --noEmit` OK
- ✅ Smoke test navigation complète.

---

### Phase 4 — Sprint 9 (P3) : Intro + 2FA (TSX) ✅ **COMPLETED**
**Résumé**
- Typage intro + UI 2FA (activation/guard) intégré.

**Validation gate**
- ✅ `npx tsc --noEmit` OK
- ✅ Smoke test intro + 2FA.

---

### Phase 5 — Sprint 10 : Polish final + readiness deploy ✅ **COMPLETED**
**Travaux**
- ✅ Nettoyage build + variables d’environnement.
- ✅ Documentation déploiement : `/app/DEPLOY.md`.
- ✅ Validation `yarn build`.

**Validation gate**
- ✅ `yarn build` OK
- ✅ E2E de non-régression (manuel) : Landing + Admin + Classified Vault.

---

### Phase 6 — Sprint 11 : “VAULT SEALED” pré-mint (P0) ✅ **COMPLETED**
**Résumé**
- Double-layer protection du Classified Vault pré-lancement.
- Remplacement du flow email Genesis par “Allégeance”.

**Validation gate**
- ✅ Backend protections (403 + override admin)
- ✅ Smoke test UI + email flow.

---

### Phase 7 — Sprint 12.1 : Sécurité admin (password rotation + 2FA UI) ✅ **COMPLETED**
**Résumé**
- Password change endpoints + UI.
- Hardening des flows admin.

**Validation gate**
- ✅ Tests API + smoke test UI.

---

### Phase 8 — Sprint 12.2 : Cabinet Vault Backend (BIP39 + AES-256-GCM) ✅ **COMPLETED**
**User stories (min 5)**
1. En tant qu’admin, je veux initialiser un coffre par seed phrase BIP39 24 mots.
2. En tant qu’admin, je veux déverrouiller temporairement le coffre (TTL 15 min) sans stocker la seed.
3. En tant qu’admin, je veux CRUD + rotation des secrets avec audit log.
4. En tant qu’admin, je veux exporter un backup chiffré.
5. En tant qu’opérateur, je veux des erreurs standardisées (401/403/423) pour piloter l’UX.

**Travaux (réalisés)**
- ✅ `core/cabinet_vault.py` : PBKDF2-SHA512 + AES-256-GCM + TTL en mémoire.
- ✅ `routers/cabinet_vault.py` : endpoints lifecycle + CRUD + export + audit.
- ✅ Audit logging des actions.

**Validation gate**
- ✅ Endpoints validés (succès + cas d’erreur).

---

### Phase 9 — Sprint 12.3 : Cabinet Vault Frontend UI ✅ **COMPLETED**
**Travaux (réalisés)**
- ✅ `/src/pages/CabinetVault.tsx` : SetupWizard / UnlockForm / UnlockedPanel + CRUD.
- ✅ Dialogs : audit log + export + édition/rotation.
- ✅ Route `/admin/cabinet-vault` ajoutée dans `App.js`.

**Validation gate**
- ✅ Frontend compile + route accessible.

---

### Phase 10 — Sprint 12.3.E2E : Tests E2E Cabinet Vault (backend) ✅ **COMPLETED**
**Objectif** : valider sécurité et fonctionnalités avant migration des secrets.

**Résultat**
- ✅ 2FA guard, init/unlock, CRUD, audit, export, TTL/423 validés.
- ✅ Rapport : `/app/test_reports/iteration_16.json`.

---

### Phase 11 — Sprint 12.4 : Migration des secrets vers Cabinet Vault via SecretProvider ✅ **COMPLETED**
**Objectif** : centraliser la résolution des secrets (LLM, emails, Helius, bots) et permettre la rotation sans redémarrage.

**Travaux (réalisés)**
- ✅ Ajout `core/secret_provider.py` (Vault → fallback env, cache TTL, invalidation).
- ✅ Ajout `get_secret_silent()` + `is_unlocked()` dans `core/cabinet_vault.py` (évite flood audit côté services).
- ✅ Refactor call sites :
  - `routers/public.py` (Prophecy/Chat)
  - `core/llm_router.py` (Emergent key dynamique + custom keys via Cabinet Vault en priorité, fallback legacy Fernet)
  - `core/email_service.py`, `core/loyalty_email.py`, `routers/access_card.py`, `routers/admin.py`
  - `routers/vault.py`, `routers/webhooks.py`, `server.py` (Helius dynamique)
  - `core/news_repost.py` (credentials via provider, dry-run inchangé)
  - `core/prophet_studio.py` (image key dynamique)
- ✅ Script one-shot : `/app/backend/scripts/migrate_secrets_to_cabinet.py`.

**Tests & validation gate**
- ✅ Régression backend 100% (prophecy/chat/admin/webhooks/vault) : `/app/test_reports/iteration_17.json`.

---

### Phase 12 — Sprint 12.5 : Import backups (backend + UI) ✅ **COMPLETED**
**Objectif** : cycle complet sauvegarde/restauration chiffrée.

**Travaux (réalisés)**
- ✅ Backend : `cabinet_vault.import_encrypted(bundle, passphrase, overwrite)` + audit.
- ✅ Router : `POST /api/admin/cabinet-vault/import` + invalidation cache SecretProvider.
- ✅ Frontend : `ImportDialog` + bouton Import (barre d’actions du panel déverrouillé).
- ✅ `yarn build` : **Compiled successfully**.

**Tests & validation gate**
- ✅ 22 scénarios import/export (round-trip, collisions skip/overwrite, wrong passphrase atomic abort, audit) : `/app/test_reports/iteration_18.json`.

---

## 3) Next Actions
1. **(Optionnel) Sprint 12.3.E2E Frontend** : tests E2E UI complets du Cabinet Vault (init → unlock → CRUD → audit → export → import → TTL).
2. **(Optionnel) Stabilisation dev server** : si nécessaire, corriger l’affichage d’erreurs fork-ts-checker en mode dev (le build prod est OK).
3. **Post-12.5 / Go-to-market** :
   - Bots Telegram (Phase 3) : nécessite token + chat id.
   - Bots X (Phase 4/5) : nécessite credentials X API + liste KOL.
   - Helius : passer de demo mode au mint réel post-launch.
4. **Post-deploy (low priority)** : migration résiduelle JSX → TSX (`AdminBots.jsx`, `AdminVault.jsx`) si besoin.

---

## 4) Success Criteria
- Phases 1–9 :
  - TS/TSX quasi complet, build prod OK.
  - Cabinet Vault UI accessible via `/admin/cabinet-vault`.
- Phase 10 :
  - Backend Cabinet Vault validé (2FA guard + init/unlock + CRUD + audit + export + TTL).
- Phase 11 :
  - SecretProvider en place : lecture Vault (unlock) + fallback env, rotation sans redémarrage.
  - Services clés (Prophet, emails, Helius wiring, repost dry-run) fonctionnels.
- Phase 12 :
  - Export + import chiffrés fonctionnels (restauration) + audit.
- Reste inchangé : landing + intro + ROI + vault + admin (bots restent dry-run tant que credentials non fournis).
