# DEEPOTUS — Plan de finalisation TypeScript & sécurité “Cabinet Vault” **+ Propaganda Engine ΔΣ** (Sprints 6 → 13.3)

## 1) Objectives
- Stabiliser et clarifier le code (split des gros composants, réduction de complexité) **avant** migration d’hébergement (Vercel/Render).
- Augmenter la couverture TS/TSX sur le code **applicatif** (hors Shadcn UI auto-généré), sans casser l’existant.
- Garantir une base prête pour un déploiement **Vercel (frontend) / Render (backend)** avec builds production OK.
- Préserver le comportement actuel (bots en **dry-run** tant que credentials non fournis, vault, ROI, intro, admin).
- **Centraliser la gestion des secrets** via le **Cabinet Vault** (BIP39 + PBKDF2 + AES-256-GCM) et migrer les clés existantes (LLM, Resend, Helius, bots) vers ce coffre.
- **Conformité sécurité** : 2FA côté admin pour les actions sensibles, audit logging, rotation, export/import de backups chiffrés.
- **NOUVEAU : PROTOCOL ΔΣ — Propaganda Engine** : automatiser une logique “scenario-based” (triggers marché → message → dispatch) pour réagir au marché avec des garde-fous anti-slop, un mode test pré-mint et une UI admin.

> Stratégie : “migration gates” (tsc/build + smoke tests) à chaque sprint + validation API (curl/testing agent) avant activation en prod.

### État actuel (mise à jour)
- Couverture TS/TSX : **~94% du frontend** migré (reste quelques gros JSX stables : `AdminBots.jsx`, `AdminVault.jsx` — migration différée post-déploiement).
- Sécurité session : migration `localStorage` → **`sessionStorage`** effectuée.
- Build : **`yarn build` OK** + doc déploiement (`DEPLOY.md`).
- **Cabinet Vault** complet end-to-end ✅ :
  - Backend BIP39 + PBKDF2 + AES-256-GCM + audit
  - Frontend UI `/admin/cabinet-vault` + export + import + audit
  - Import/Export chiffrés validés
  - SecretProvider en place (vault → fallback env) + script migration secrets
- **2FA bootstrap** : ajout d’un mode bootstrap Cabinet Vault (init/unlock/list/audit autorisés **sans 2FA** uniquement si vault vide). CRUD/export/import restent **2FA strict**. Endpoint recovery `POST /api/admin/2fa/force-reset` + guide `/app/docs/2FA_SETUP_GUIDE.md`.
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
- ✅ Dialogs : audit log + export + import + édition/rotation.
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
- ✅ Régression backend 100% : `/app/test_reports/iteration_17.json`.

---

### Phase 12 — Sprint 12.5 : Import backups (backend + UI) ✅ **COMPLETED**
**Objectif** : cycle complet sauvegarde/restauration chiffrée.

**Travaux (réalisés)**
- ✅ Backend : `cabinet_vault.import_encrypted(bundle, passphrase, overwrite)` + audit.
- ✅ Router : `POST /api/admin/cabinet-vault/import` + invalidation cache SecretProvider.
- ✅ Frontend : `ImportDialog` + bouton Import (barre d’actions du panel déverrouillé).
- ✅ `yarn build` : **Compiled successfully**.

**Tests & validation gate**
- ✅ 22 scénarios import/export : `/app/test_reports/iteration_18.json`.

---

## 3) Next Actions (NOUVEAU)

### Phase 13 — **PROTOCOL ΔΣ : Propaganda Engine (NEW MAJOR FEATURE)**
Objectif : implémenter une logique “scenario-based” de propagande automatisée avec garde-fous (anti-spam, anti-slop), testable **avant le mint** via Manual Fire.

#### Choix validés (scope global)
- **Génération messages** : Hybride **templates + LLM** (70/30)
- **Langues** : **EN par défaut**, FR optionnel par trigger
- **Détection triggers** : **Helius + Manual Fire** (testable maintenant)
- **Roadmap** : MVP itératif **13.1 → 13.2 → 13.3**
- **Garde-fous** : **Approval queue** + policy auto/manuel par trigger + **Panic Kill Switch**
- **Rate limits** (défaut) : **8/h**, **24/jour**, **1/trigger/15min**
- **Injection liens** : automatique depuis Cabinet Vault `trading_refs`
- **Override “Vault mention”** : chaque 3e message mentionne l’état des dials/progression (traffic driver)
- **Human delay** : 10–30s après trigger

---

### Phase 13.1 (P0) — MVP Squelette (1 jour)
**Livrables**
- Backend :
  - `core/propaganda_engine.py` (orchestrateur)
  - `core/dispatch_queue.py` (approval queue + transitions : proposed→approved→sent/rejected)
  - `core/templates_repo.py` (templates DB-backed) + seed initial templates EN
  - `core/triggers/mint.py` + `core/triggers/mc_milestone.py`
  - `routers/propaganda.py` : endpoints admin (CRUD templates, list queue, approve/reject, manual fire)
  - `propaganda_events` collection + `propaganda_queue` + `propaganda_templates`
- Frontend :
  - `pages/Propaganda.tsx` (nouvelle page admin) : Tabs **Triggers / Templates / Queue / Activity**
  - Panic Kill Switch (global ON/OFF)
  - Manual Fire UI (sélecteur trigger + payload minimal)
  - Approval queue UI (Approve/Reject)
- Sécurité : endpoints sous `require_admin` + 2FA exigée pour **approve/send** (recommandé)

**Validation gate**
- `yarn build` OK
- Tests API : manual fire → queue → approve → (dry-run dispatcher) → activity log

---

### Phase 13.2 (P1) — Triggers complets + Tone Engine (1 jour)
**Ajouts**
- Triggers :
  - `jeet_dip` (drop -20% en 2 min après rally)
  - `whale_buy` (tx > 5 SOL)
  - `raydium_migration` (bonding curve 100%)
- `core/market_analytics.py` : rolling windows prix/MC, thresholds, cooldowns
- `core/tone_engine.py` : prompt “weary 50yo intel officer” + LLM hybrid (30% rewrite)
- FR optionnel : champs `templates.fr[]` par trigger (fallback EN)
- Injection “Vault mention” : compteur global → chaque 3e message inclut l’état des dials + lien landing
- Anti-slop :
  - 70% templates stricts
  - 30% LLM “rewrite-with-constraints” (max 1-2 variations, pas de contenu non sollicité)

**Validation gate**
- Tests unitaires fonctions analytics (drop detection)
- Simulation via Manual Fire sur chaque trigger → queue/approve → dry-run

---

### Phase 13.3 (P2) — Dispatchers réels + Rate limiting + Activity feed + Onboarding (1 jour, dépend credentials)
**Pré-requis**
- Credentials Telegram + X API (stockés via Cabinet Vault catégories `telegram`, `x_twitter`) + éventuellement `trading_refs`.

**Livrables**
- `core/dispatchers/telegram.py` (Bot API) + `core/dispatchers/x.py` (OAuth2 user PKCE)
- Rate limiting réel (DB) + dedup sur événements (idempotency keys)
- Activity feed complet dans l’admin (filtre par trigger, statut, platform)
- Onboarding screen : checklist credentials + test post (sandbox channel)
- Tests E2E :
  - Manual Fire → approve → envoi réel Telegram
  - Manual Fire → approve → envoi réel X

**Validation gate**
- E2E “happy path” sur Telegram + X
- Vérification anti-spam : limites/h + limites/jour + cooldown per trigger

---

## 4) Success Criteria
- Phases 1–12 :
  - TS/TSX quasi complet, build prod OK.
  - Cabinet Vault opérationnel avec export/import + audit.
  - SecretProvider en place (rotation secrets sans redémarrage).
- Phase 13.1 :
  - Propaganda Engine MVP testable **pré-mint** via Manual Fire.
  - Approval queue + panic switch fonctionnels.
- Phase 13.2 :
  - 5 triggers complets + tone engine hybride + FR optionnel + vault mention every 3rd.
- Phase 13.3 :
  - Dispatch Telegram + X réels, rate limiting robuste, activity feed complet.

---

## 5) Notes d’architecture (Phase 13)
**Backend (proposé)**
- `core/propaganda_engine.py` : orchestration, cooldowns, randomization, delay 10–30s
- `core/triggers/*` : détecteurs et normalisation payload
- `core/market_analytics.py` : price/MC windows, bonding curve progress
- `core/templates_repo.py` : storage templates + versioning
- `core/dispatch_queue.py` : approval queue + sending pipeline
- `core/tone_engine.py` : LLM rewrite constrained + safety
- `routers/propaganda.py` : API admin

**Frontend**
- `pages/Propaganda.tsx` : panel admin Propaganda
- Intégration i18n : EN default, FR optionnel par trigger

**DB Collections**
- `propaganda_templates`
- `propaganda_queue`
- `propaganda_events`
- `price_snapshots` (TTL, si nécessaire pour jeet_dip)

**Sécurité**
- Lecture/édition templates : admin JWT
- Approve/send : admin JWT + 2FA enabled
- Secrets dispatchers : Cabinet Vault (catégories `telegram`, `x_twitter`, `trading_refs`)
