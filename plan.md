# DEEPOTUS — Plan de finalisation TypeScript & sécurité “Cabinet Vault” **+ Propaganda Engine ΔΣ** (Sprints 6 → 13.3 + Infiltration 14.1)

## 1) Objectives
- Stabiliser et clarifier le code (split des gros composants, réduction de complexité) **avant** migration d’hébergement (Vercel/Render).
- Augmenter la couverture TS/TSX sur le code **applicatif** (hors Shadcn UI auto-généré), sans casser l’existant.
- Garantir une base prête pour un déploiement **Vercel (frontend) / Render (backend)** avec builds production OK.
- Préserver le comportement actuel (bots en **dry-run** tant que credentials non fournis, vault, ROI, intro, admin).
- **Centraliser la gestion des secrets** via le **Cabinet Vault** (BIP39 + PBKDF2 + AES-256-GCM) et migrer les clés existantes (LLM, Resend, Helius, bots) vers ce coffre.
- **Conformité sécurité** : 2FA côté admin pour les actions sensibles, audit logging, rotation, export/import de backups chiffrés.
- **PROTOCOL ΔΣ — Propaganda Engine** : automatiser une logique “scenario-based” (triggers marché → message → queue → dispatch) pour réagir au marché avec garde-fous anti-slop, **testable pré-mint** via Manual Fire, et opérable via UI admin.
- **PROTOCOL ΔΣ — Infiltration Brain** : livrer l’expérience publique “Proof of Intelligence” (5 énigmes Terminal → Clearance Level 3 → lien wallet Solana) + surface admin (riddles/clearance/sleeper cell/audit) conforme à la posture sécurité.

> Stratégie : “migration gates” (tsc/build + smoke tests) à chaque sprint + validation API (curl/testing agent) avant activation en prod.

### État actuel (mise à jour)
- Couverture TS/TSX : **~94% du frontend** migré (reste quelques gros JSX stables : `AdminBots.jsx`, `AdminVault.jsx` — migration différée post-déploiement).
- Sécurité session : migration `localStorage` → **`sessionStorage`** effectuée.
- Build : **`yarn build` OK** + doc déploiement (`DEPLOY.md`).

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
  - **5 triggers** : `mint`, `mc_milestone`, `jeet_dip`, `whale_buy`, `raydium_migration`.
  - `market_analytics.py` : snapshots prix/MC (TTL 1h), dip detection.
  - `tone_engine.py` : LLM hybride **70/30** (configurable), persona “weary intel officer”, post-processor (placeholders intacts, pas de hashtags/emoji, ≤280 chars).
  - **FR optionnel** : +12 templates FR seedés (EN=13).
  - `PATCH /api/admin/propaganda/settings` : `llm_enabled`, `llm_enhance_ratio`, `personality_prompt`, `provider/model`.
  - Frontend : tab **Tone & LLM**.

#### Infiltration Brain (Sprint 14.1) — ✅ Backend + ✅ Admin UI + ✅ Public Terminal flow
- ✅ Backend : `core/riddles.py`, `core/clearance_levels.py`, `core/sleeper_cell.py` + endpoints `routers/infiltration.py`.
- ✅ Seed de **5 énigmes** + anti-bruteforce (TTL 24h, soft-limit 6/h).
- ✅ Admin UI : `/app/frontend/src/pages/Infiltration.tsx` (tabs Riddles/Clearance/Sleeper/Attempts).
- ✅ Public UX : intégration “Proof of Intelligence” dans le Terminal (landing) via `TerminalPopup.tsx` + composant dédié `RiddlesFlow.tsx`.
- ✅ Correction backend critique : index wallet MongoDB sur `clearance_levels` (unique) migré vers **partial index** (unique uniquement quand `wallet_address` est un string) + suppression du `wallet_address: null` à la création.

#### Tests automatisés & validations
- **Iteration 16** : backend Cabinet Vault (12.3.E2E backend) ✅.
- **Iteration 17** : régression Sprint 12.4 (SecretProvider) ✅.
- **Iteration 18** : Sprint 12.5 Import/Export (22/22) ✅.
- **Sprint 13.2** : smoke tests backend (9/9) + screenshots frontend (5 tabs + Tone tab) ✅.
- **Sprint 14.1** :
  - ✅ E2E manuel (Playwright screenshot_tool) : intro → play → claim → wallet → complete (FR/EN), hint après 3 échecs, wrong answer, persistance sessionStorage.
  - ✅ Curls backend : attempt, clearance, link-wallet OK.
  - ⚠️ Testing agent Playwright : difficulté avec l’animation d’intro (DEEPSTATE.SYS) ; privilégier screenshots manuels pour ce module.

#### Restant
- **Sprint 13.3** : dispatchers réels (Telegram/X) + worker cron + rate limiting + onboarding credentials (bloqué par credentials Telegram/X).

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
- ✅ `npx tsc --noEmit` OK.
- ✅ Webpack dev OK.
- ✅ Smoke test manuel des routes admin + landing.

---

### Phase 2 — Sprint 7 (P1) : Landing components (TSX) ✅ **COMPLETED**
**Résumé**
- Migration majeure de composants landing vers TSX, stabilisation i18n, conservation UX.

**Validation gate**
- ✅ `npx tsc --noEmit` OK.
- ✅ Webpack compile OK.
- ✅ Smoke test landing (scroll, ROI, toggles theme/lang, vault interactions).

---

### Phase 3 — Sprint 8 (P2) : Pages applicatives (TSX) ✅ **COMPLETED**
**Résumé**
- Migration des pages principales vers TSX (Landing/Operation/HowToBuy/PublicStats/ClassifiedVault) + corrections bundler.

**Validation gate**
- ✅ `npx tsc --noEmit` OK.
- ✅ Smoke test navigation complète.

---

### Phase 4 — Sprint 9 (P3) : Intro + 2FA (TSX) ✅ **COMPLETED**
**Résumé**
- Typage intro + UI 2FA (activation/guard) intégré.

**Validation gate**
- ✅ `npx tsc --noEmit` OK.
- ✅ Smoke test intro + 2FA.

---

### Phase 5 — Sprint 10 : Polish final + readiness deploy ✅ **COMPLETED**
**Travaux**
- ✅ Nettoyage build + variables d’environnement.
- ✅ Documentation déploiement : `/app/DEPLOY.md`.
- ✅ Validation `yarn build`.

**Validation gate**
- ✅ `yarn build` OK.
- ✅ E2E de non-régression (manuel) : Landing + Admin + Classified Vault.

---

### Phase 6 — Sprint 11 : “VAULT SEALED” pré-mint (P0) ✅ **COMPLETED**
**Résumé**
- Double-layer protection du Classified Vault pré-lancement.
- Remplacement du flow email Genesis par “Allégeance”.

**Validation gate**
- ✅ Backend protections (403 + override admin).
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
- ✅ Ajout `get_secret_silent()` + `is_unlocked()` dans `core/cabinet_vault.py`.
- ✅ Refactor call sites.
- ✅ Script one-shot : `/app/backend/scripts/migrate_secrets_to_cabinet.py`.

**Tests & validation gate**
- ✅ Régression backend 100% : `/app/test_reports/iteration_17.json`.

---

### Phase 12 — Sprint 12.5 : Import backups (backend + UI) ✅ **COMPLETED**
**Objectif** : cycle complet sauvegarde/restauration chiffrée.

**Travaux (réalisés)**
- ✅ Backend : `cabinet_vault.import_encrypted(...)` + audit.
- ✅ Router : `POST /api/admin/cabinet-vault/import` + invalidation cache SecretProvider.
- ✅ Frontend : `ImportDialog` + bouton Import.
- ✅ `yarn build` : compiled successfully.

**Tests & validation gate**
- ✅ 22 scénarios import/export : `/app/test_reports/iteration_18.json`.

---

## 3) Next Actions

### Phase 13 — **PROTOCOL ΔΣ : Propaganda Engine**
Objectif : implémenter une logique “scenario-based” de propagande automatisée avec garde-fous (anti-spam, anti-slop), testable **avant le mint** via Manual Fire.

#### Choix validés (scope global)
- **Génération messages** : Hybride **templates + LLM** (70/30, ratio configurable).
- **Langues** : **EN par défaut**, FR optionnel par trigger (fallback EN).
- **Détection triggers** : **Helius + Manual Fire**.
- **Roadmap** : **13.1 → 13.2 → 13.3**.
- **Garde-fous** : **Approval queue** + policy auto/manuel + **Panic Kill Switch**.
- **Rate limits** (défaut) : **8/h**, **24/jour**, **1/trigger/15min** (à implémenter réellement en 13.3).
- **Override “Vault mention”** : chaque 3e message mentionne le Vault.
- **Human delay** : 10–30s après trigger.

---

### Phase 13.1 (P0) — MVP Squelette ✅ **COMPLETED**
(identique au plan précédent)

---

### Phase 13.2 (P1) — Triggers complets + Tone Engine ✅ **COMPLETED**
(identique au plan précédent)

---

### Phase 13.3 (P2) — Dispatchers réels + Worker cron + Rate limiting + Onboarding (**NEXT**)
**Pré-requis**
- Credentials Telegram + X API (stockés via Cabinet Vault catégories `telegram`, `x_twitter`) + éventuellement `trading_refs`.

**Livrables**
- Worker :
  - `core/dispatcher_worker.py` (ou extension `core/bot_scheduler.py`) :
    - consomme `propaganda_queue` items `status=approved` et `scheduled_for <= now`.
    - applique rate limiting (8/h, 24/j, per-trigger cooldown).
    - écrit `sent/failed` + results dans queue.
    - logge dans `propaganda_events`.
- Dispatchers réels :
  - `core/dispatchers/telegram.py` (Bot API `sendMessage`).
  - `core/dispatchers/x.py` (OAuth2 user context PKCE + refresh).
- Rate limiting DB :
  - collection `propaganda_rate_limits` (ou counters persistants équivalents).
- Onboarding :
  - checklist credentials + “Test post” vers un channel sandbox.
  - intégration Cabinet Vault : lecture des secrets (token/chat_id, client_id/secret/refresh).

**Validation gate**
- E2E “happy path” Telegram + X.
- Vérification anti-spam : limites/h + limites/jour + cooldown per trigger.

---

### Phase 14 — **Pre-Launch Infiltration Brain (PROTOCOL ΔΣ)**
Objectif : rendre jouable le “Proof of Intelligence” côté landing + fournir le pilotage admin (riddles/clearance/sleeper cell/audit) + export airdrop.

#### Choix UX validés (user = “go reco”)
- **1a** Point d’entrée : visible dans Terminal **en mode `sealed` ET `denied`**.
- **2a** Progression : **séquentielle** (1 énigme à la fois sur 5).
- **3b** Email : demandé **seulement à la 1ère victoire**.
- **4a** Wallet Solana : capturé **immédiatement** après Level 3.
- **5a** Esthétique : CRT vert cohérent, accents **ambre** (`#F59E0B`).

#### Endpoints consommés (public)
- `GET /api/infiltration/riddles?locale=fr|en`.
- `POST /api/infiltration/riddles/{slug}/attempt`.
- `GET /api/infiltration/clearance/{email}`.
- `POST /api/infiltration/clearance/link-wallet`.

---

### Phase 14.1 (P0) — Backend + Admin UI + Public Terminal flow ✅ **COMPLETED**
**Livrables (réalisés)**
1) **I18n**
- ✅ Ajout des clés `terminal.riddles.*` (FR + EN) dans `/app/frontend/src/i18n/translations.js`.
- ✅ Ajout des messages d’erreur localisés : `walletAlreadyLinked`, `walletInvalid`.

2) **TerminalPopup — branche Proof of Intelligence**
- ✅ Fichier : `/app/frontend/src/components/landing/vault/TerminalPopup.tsx`.
- ✅ Extension `TerminalPhase` avec `"riddles"`.
- ✅ CTA ajouté :
  - `terminal-riddles-cta` (phase denied).
  - `terminal-riddles-cta-sealed` (phase sealed).
- ✅ Montage du flow via `phase === "riddles"`.

3) **Sous-composant `RiddlesFlow`**
- ✅ Nouveau fichier : `/app/frontend/src/components/landing/vault/RiddlesFlow.tsx`.
- ✅ 5 phases internes : intro / play / claim / wallet / complete.
- ✅ UX : progression 0/5 → 5/5, `attempts_left`, hint après 3 échecs, rate-limit UX.
- ✅ Claim email après 1ère victoire (replay de la réponse gagnante persistée).
- ✅ Wallet : validation base58 côté client + mapping erreurs backend → i18n.

4) **Persistance sessionStorage**
- ✅ Clé : `deepotus_riddles_session` avec :
  - `{ email, solvedSlugs[], solvedAnswers{}, currentIndex, wallet, walletLinked, phaseSnapshot }`.

5) **Backend hardening (bug critique)**
- ✅ `clearance_levels.wallet_address` : passage de `unique+sparse` (insuffisant) à **unique+partial index**.
- ✅ `_ensure_row()` ne pose plus `wallet_address: null`.
- ✅ Migration DB one-shot : suppression indexes legacy + `$unset` sur `wallet_address: null`.

**Validation gate (réalisée)**
- ✅ `yarn build` (frontend).
- ✅ `npx tsc --noEmit` (frontend).
- ✅ `ruff check` (backend).
- ✅ E2E manuel + screenshots : sealed → riddles → claim → wallet → complete (FR/EN).

**Limitations connues**
- Pydantic `EmailStr` rejette certains TLDs réservés (`.test`, `.local`) : le frontend affiche désormais le message précis du backend.
- Le testing agent Playwright peut rester bloqué sur l’animation d’intro : préférer `screenshot_tool` pour le Terminal.

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
  - 5 triggers complets + tone engine hybride + FR optionnel.
- Phase 13.3 :
  - Dispatch Telegram + X réels, worker cron fiable, rate limiting robuste, onboarding clair.
- Phase 14.1 :
  - Terminal public : Proof of Intelligence jouable, UX cohérente CRT, **Level 3 obtenu** + wallet lié.
  - Admin : stats/ledger/snapshot CSV/sleeper cell opérationnels.

---

## 5) Notes d’architecture (Phase 13–14)

**Backend (réel, livré/planifié)**
- ✅ Propaganda : orchestrateur + triggers + queue + templates + tone engine.
- ⏳ 13.3 : dispatchers réels + worker cron + rate limiting + onboarding.

- ✅ Infiltration Brain :
  - `core/riddles.py` : seed 5 énigmes, normalisation accents, audit attempts, rate-limit soft.
  - `core/clearance_levels.py` : ledger (email PK), Level 3 via riddle solve, link wallet.
  - `core/sleeper_cell.py` : kill-switch pré-mint.
  - `routers/infiltration.py` : endpoints publics + admin (mutations admin = 2FA).
  - **DB** : `wallet_address` index = **partial unique** (quand string) — évite collision sur `null`.

**Frontend**
- ✅ `pages/Propaganda.tsx` : panel admin complet.
- ✅ `pages/Infiltration.tsx` : panel admin infiltration.
- ✅ Terminal :
  - `components/landing/vault/TerminalPopup.tsx` : nouvelle branche `riddles` + CTAs.
  - `components/landing/vault/RiddlesFlow.tsx` : flow public complet + persistance sessionStorage.

**DB Collections**
- Propaganda : `propaganda_templates`, `propaganda_queue`, `propaganda_events`, `propaganda_settings`, `propaganda_triggers`, `propaganda_price_snapshots`.
- Infiltration :
  - `riddles`.
  - `riddle_attempts` (TTL 24h).
  - `clearance_levels` (unique email; wallet unique via partial index).
  - `sleeper_cell`.

**Sécurité**
- Propaganda : lecture/édition templates = admin JWT ; panic/approve/reject = admin JWT + 2FA.
- Infiltration :
  - endpoints publics : pas de fuite des keywords, rate-limit côté `riddles.submit_attempt`.
  - endpoints admin : mutations = 2FA obligatoire (`TWOFA_REQUIRED`).
- Secrets dispatchers : Cabinet Vault (catégories `telegram`, `x_twitter`, `trading_refs`).
