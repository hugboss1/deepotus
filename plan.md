# DEEPOTUS — Plan de finalisation TypeScript & sécurité “Cabinet Vault” (Sprints 6 → 12.5)

## 1) Objectives
- Stabiliser et clarifier le code (split des gros composants, réduction de complexité) **avant** migration d’hébergement (Vercel/Render).
- Augmenter la couverture TS/TSX sur le code **applicatif** (hors Shadcn UI auto-généré), sans casser l’existant.
- Garantir une base prête pour un déploiement **Vercel (frontend) / Render (backend)** avec builds production OK.
- Préserver le comportement actuel (bots en **dry-run**, vault, ROI, intro, admin).
- **Centraliser la gestion des secrets** via le **Cabinet Vault** (BIP39 + PBKDF2 + AES-256-GCM) et migrer les clés existantes (LLM, Resend, Helius, bots) vers ce coffre.
- **Conformité sécurité** : 2FA obligatoire côté admin pour les actions sensibles, audit logging, rotation, export/import de backups chiffrés.

> Décision POC : **pas de POC d’intégration requis**. Stratégie “migration gates” (tsc/build + smoke tests) à chaque sprint.

**État actuel (mise à jour)**
- Couverture TS/TSX : **~94% du frontend** migré (reste quelques gros JSX stables : `AdminBots.jsx`, `AdminVault.jsx` — migration différée post-déploiement).
- Sécurité session : migration `localStorage` → **`sessionStorage`** effectuée.
- Build : **`yarn build` OK** + doc déploiement (`DEPLOY.md`).
- **Sprint 12.2 (backend Cabinet Vault)** : complet, endpoints testés au curl, audit log intégré.
- **Sprint 12.3 (frontend Cabinet Vault)** : **COMPLETED**
  - Page `CabinetVault.tsx` complète (SetupWizard / UnlockForm / SecretsBrowser / edit / export / audit)
  - Route **`/admin/cabinet-vault`** ajoutée dans `App.js`
  - Cache webpack purgé (corrige erreurs TS fantômes)

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
- ✅ `npm run build` / `yarn build` OK
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
- ✅ `routers/cabinet_vault.py` : 16 endpoints.
- ✅ Audit logging des actions (unlock/lock/read/write/delete/export).
- ✅ Tests curl complets.

**Validation gate**
- ✅ Tous endpoints testés (succès + cas d’erreur).

---

### Phase 9 — Sprint 12.3 : Cabinet Vault Frontend UI ✅ **COMPLETED**
**Travaux (réalisés)**
- ✅ Création/complétion : `/src/pages/CabinetVault.tsx`
  - Phase 1 : SetupWizard (génération + reveal + quiz 3 mots)
  - Phase 2 : UnlockForm (validation 24 mots)
  - Phase 3 : UnlockedPanel (liste catégorisée, reveal on-demand, rotate, delete)
  - Dialogs : audit log + export chiffré + SecretEditDialog
  - UX sécurité : inputs password, countdown TTL, auto-lock UX
- ✅ Route ajoutée : `/admin/cabinet-vault` dans `App.js`.
- ✅ Purge cache webpack (résout erreurs TS incohérentes).

**Validation gate**
- ✅ Frontend compile (HTTP 200)
- ✅ Backend accessible (401 sans token, OK avec auth)

---

### Phase 10 — Sprint 12.3.E2E : Tests E2E Cabinet Vault 🔄 **IN PROGRESS (Priorité actuelle — option D)**
**Objectif** : sécuriser et valider le coffre *avant* migration des secrets.

**User stories (min 5)**
1. En tant qu’admin, je veux être bloqué sans 2FA (403 `TWOFA_REQUIRED`).
2. En tant qu’admin, je veux initialiser le coffre et confirmer la seed via quiz.
3. En tant qu’admin, je veux déverrouiller, voir le TTL diminuer et constater l’auto-lock.
4. En tant qu’admin, je veux stocker/rotate/révéler/supprimer un secret et le retrouver en liste.
5. En tant qu’admin, je veux voir l’audit log refléter les actions sans leak de valeurs.

**Checklist de test (à exécuter)**
- Auth : login admin (`deepotus2026`) → token présent en session.
- 2FA guard : essayer Cabinet Vault sans 2FA → message dédié.
- Init : générer 24 mots → reveal → copy → quiz 3 mots → status passe à locked.
- Unlock : coller 24 mots → passe à unlocked.
- CRUD :
  - `PUT secret` nouveau → visible + metadata (fingerprint, length, rotations)
  - `GET secret` reveal on-demand → valeur affichée puis hide
  - `PUT` rotate → rotation_count++
  - `DELETE` → retiré
- Audit : ouvrir modal → présence des actions.
- Export : passphrase >= 12 → JSON téléchargé.
- TTL : attendre expiration (ou simuler) → auto-lock + 423 géré.

**Validation gate**
- `npx tsc --noEmit` OK
- “Happy path” E2E validé (captures/screens + notes).
- Liste des bugs (si trouvés) corrigés, re-test.

---

### Phase 11 — Sprint 12.4 : Migration des clés LLM (Fernet → Cabinet Vault AES-256-GCM) ⏳ **NOT STARTED**
**Objectif** : centraliser toutes les clés externes (LLM, Resend, Helius, bots) dans Cabinet Vault.

**Travaux (prévus)**
- Identifier toutes les sources actuelles des secrets :
  - `secrets_vault.py` (Fernet KEK) + env vars fallback éventuel.
- Ajouter un adaptateur “SecretProvider” backend :
  - lecture `cabinet_vault.get_secret(category,key)`
  - fallback contrôlé (optionnel) en phase de transition.
- Migration de la logique LLM :
  - `llm_service.py` / modules IA → lecture depuis Cabinet Vault (`llm_emergent`, `llm_custom`).
- Script de migration (one-shot) :
  - lire anciens secrets → écrire dans Cabinet Vault (avec audit).
- Mise à jour Admin UX (si nécessaire) :
  - afficher quelles clés sont “set/not set” par schéma.

**Tests**
- Backend : tests unitaires légers + tests API (crud) + test d’appel LLM (dry-run si nécessaire).
- Frontend : vérifier catégories et états “not set”.

**Validation gate**
- Aucune clé LLM critique n’est lue depuis l’ancien vault en prod.
- Les appels IA fonctionnent (Prophet, repost engine dry-run).

---

### Phase 12 — Sprint 12.5 : Import backups + Audit viewer (compléter le cycle) ⏳ **NOT STARTED**
**Objectif** : restauration sécurisée + consultation avancée des logs.

**Travaux (prévus)**
- Backend :
  - `POST /api/admin/cabinet-vault/import` (décryptage via passphrase export, re-chiffrement via master key en mémoire).
  - garde-fous (structure, versioning, collisions).
- Frontend :
  - UI dialog import (upload JSON + passphrase + preview).
  - Audit viewer amélioré (filtre action / catégorie / key + pagination si utile).

**Validation gate**
- Round-trip : export → import sur base vide → secrets restaurés.
- Audit visible et cohérent.

---

## 3) Next Actions
1. **Sprint 12.3.E2E** : exécuter la checklist complète (screens/captures + bugfix si besoin).
2. **Sprint 12.4** : migrer les clés LLM vers Cabinet Vault (débloque la valeur réelle du coffre).
3. **Sprint 12.5** : import backups + audit viewer (cycle complet de sauvegarde/restauration).
4. Ensuite :
   - Bots Telegram/X (dépend des credentials)
   - Helius “demo mode” → vrai mint post-launch
   - Migration résiduelle JSX → TSX (post-déploiement, si nécessaire)

---

## 4) Success Criteria
- Phases 1–10 :
  - TS/TSX quasi complet, build prod OK.
  - Cabinet Vault UI accessible via `/admin/cabinet-vault`.
  - E2E Cabinet Vault validé (2FA guard + init/unlock + CRUD + audit + export + TTL).
- Phase 11 :
  - Les secrets LLM ne dépendent plus de `secrets_vault.py` (Fernet) en production.
  - Prophet / engines admin utilisent Cabinet Vault.
- Phase 12 :
  - Export + import chiffrés fonctionnels (restauration).
  - Audit viewer exploitable.
- Flows inchangés : landing + intro + ROI + vault + admin (bots restent dry-run tant que credentials non fournis).
