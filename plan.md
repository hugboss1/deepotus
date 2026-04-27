# DEEPOTUS — Plan de finalisation TypeScript & sécurité “Cabinet Vault” **+ Propaganda Engine ΔΣ** (Sprints 6 → 14.1)

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
- Backend BIP39 + PBKDF2 + AES-256-GCM + audit
- Frontend UI `/admin/cabinet-vault` + export + import + audit
- Import/Export chiffrés validés
- **SecretProvider** en place (vault → fallback env) + script migration secrets
- **2FA bootstrap** : ajout d’un mode bootstrap Cabinet Vault (init/unlock/list/audit autorisés **sans 2FA** uniquement si vault vide). CRUD/export/import restent **2FA strict**.
- Endpoint recovery `POST /api/admin/2fa/force-reset` + guide `/app/docs/2FA_SETUP_GUIDE.md`.

#### Propaganda Engine (Sprints 13.1–13.2) — ✅ LIVRÉ end-to-end
- **Sprint 13.1 MVP** ✅ : orchestrateur + templates DB + approval queue + panic kill-switch + UI admin (Triggers/Templates/Queue/Activity)
- **Sprint 13.2 COMPLET** ✅ :
  - **5 triggers** : `mint`, `mc_milestone`, `jeet_dip`, `whale_buy`, `raydium_migration`
  - `market_analytics.py` : snapshots prix/MC (TTL 1h), dip detection, snapshot market synthétique
  - `tone_engine.py` : LLM hybride **70/30** (configurable), persona “weary intel officer”, post-processor (placeholders intacts, pas de hashtags/emoji, ≤280 chars)
  - **FR optionnel** : +12 templates FR seedés (EN=13)
  - `PATCH /api/admin/propaganda/settings` : `llm_enabled`, `llm_enhance_ratio`, `personality_prompt`, `provider/model`
  - Frontend : tab **Tone & LLM** (toggle + slider 0–100% + provider/model + editor prompt 4000 chars)

#### Infiltration Brain (Sprint 14.1) — ✅ Backend + ✅ Admin UI / ⏳ Public Terminal flow
- ✅ Backend : `core/riddles.py`, `core/clearance_levels.py`, `core/sleeper_cell.py` + endpoints `routers/infiltration.py`
- ✅ Seed de **5 énigmes** + anti-bruteforce (TTL 24h, soft-limit 6/h)
- ✅ Admin UI : `/app/frontend/src/pages/Infiltration.tsx` **déjà implémenté** (tabs Riddles/Clearance/Sleeper/Attempts)
- ⏳ Public UX : intégration “Proof of Intelligence” dans `TerminalPopup.tsx` (composant landing)

#### Tests automatisés & validations
- **Iteration 16** : backend Cabinet Vault (12.3.E2E backend) ✅
- **Iteration 17** : régression Sprint 12.4 (SecretProvider) ✅
- **Iteration 18** : Sprint 12.5 Import/Export (22/22) ✅
- **Sprint 13.2** : smoke tests backend (9/9) + screenshots frontend (5 tabs + Tone tab) ✅
- **Sprint 14.1** :
  - ✅ Smoke backend endpoints infiltration (manuel / curl)
  - ⏳ Screenshots + tests frontend du nouveau flow Terminal (à produire)

#### Restant
- **Sprint 13.3** : dispatchers réels (Telegram/X) + worker cron + rate limiting + onboarding credentials (bloqué par credentials Telegram/X).
- **Sprint 14.1 Frontend** : Proof of Intelligence dans le Terminal (P0).

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
- ✅ Refactor call sites (public/admin/webhooks/vault/email/llm/news_repost/prophet_studio).
- ✅ Script one-shot : `/app/backend/scripts/migrate_secrets_to_cabinet.py`.

**Tests & validation gate**
- ✅ Régression backend 100% : `/app/test_reports/iteration_17.json`.

---

### Phase 12 — Sprint 12.5 : Import backups (backend + UI) ✅ **COMPLETED**
**Objectif** : cycle complet sauvegarde/restauration chiffrée.

**Travaux (réalisés)**
- ✅ Backend : `cabinet_vault.import_encrypted(bundle, passphrase, overwrite)` + audit.
- ✅ Router : `POST /api/admin/cabinet-vault/import` + invalidation cache SecretProvider.
- ✅ Frontend : `ImportDialog` + bouton Import.
- ✅ `yarn build` : **Compiled successfully**.

**Tests & validation gate**
- ✅ 22 scénarios import/export : `/app/test_reports/iteration_18.json`.

---

## 3) Next Actions

### Phase 13 — **PROTOCOL ΔΣ : Propaganda Engine**
Objectif : implémenter une logique “scenario-based” de propagande automatisée avec garde-fous (anti-spam, anti-slop), testable **avant le mint** via Manual Fire.

#### Choix validés (scope global)
- **Génération messages** : Hybride **templates + LLM** (70/30, ratio configurable)
- **Langues** : **EN par défaut**, FR optionnel par trigger (fallback EN)
- **Détection triggers** : **Helius + Manual Fire** (testable maintenant)
- **Roadmap** : MVP itératif **13.1 → 13.2 → 13.3**
- **Garde-fous** : **Approval queue** + policy auto/manuel par trigger + **Panic Kill Switch**
- **Rate limits** (défaut) : **8/h**, **24/jour**, **1/trigger/15min** (à implémenter réellement en 13.3)
- **Override “Vault mention”** : chaque 3e message doit mentionner le Vault (traffic driver)
- **Human delay** : 10–30s après trigger

---

### Phase 13.1 (P0) — MVP Squelette ✅ **COMPLETED**
**Livrables (réalisés)**
- Backend :
  - `core/propaganda_engine.py` (orchestrateur)
  - `core/dispatch_queue.py` (approval queue)
  - `core/templates_repo.py` (templates DB-backed) + seed initial EN
  - `core/triggers/mint.py` + `core/triggers/mc_milestone.py`
  - `routers/propaganda.py` : endpoints admin
  - Collections : `propaganda_events`, `propaganda_queue`, `propaganda_templates`, `propaganda_settings`, `propaganda_triggers`
- Frontend :
  - `pages/Propaganda.tsx` (admin) : Tabs **Triggers / Templates / Queue / Activity**
  - Panic Kill Switch + Manual Fire + Templates CRUD + Approval queue
- Sécurité : endpoints sous `require_admin`; actions “send-like” (panic/approve/reject) protégées par 2FA.

**Validation gate (réalisée)**
- ✅ `yarn build` OK
- ✅ API smoke : manual fire → queue → approve gated by 2FA → activity log
- ✅ Screenshots UI : page accessible, tabs render, queue items visibles

---

### Phase 13.2 (P1) — Triggers complets + Tone Engine ✅ **COMPLETED**
**Ajouts (réalisés)**
- Triggers :
  - ✅ `jeet_dip` (drop -20% / 2 min)
  - ✅ `whale_buy` (tx > 5 SOL, threshold configurable)
  - ✅ `raydium_migration` (dex_mode=raydium)
- ✅ `core/market_analytics.py` :
  - snapshots (TTL 1h) + `detect_dip()`
  - `current_market_snapshot()` pour fournir des links + contexte
- ✅ `core/tone_engine.py` :
  - LLM hybride (ratio configurable)
  - persona prompt configurable
  - post-processor strict (placeholders intacts, no hashtags/emoji, ≤280)
- ✅ FR optionnel : +12 templates FR seedés (EN=13)
- ✅ API : `GET /settings` enrichi (tone) + `PATCH /settings`
- ✅ Frontend : tab **Tone & LLM** (toggle, slider, provider/model, personality editor)

**Validation gate (réalisée)**
- ✅ Backend smoke tests 9/9 (LLM rewrite FR validé, persona terminologie OK)
- ✅ Frontend screenshots : 5 tabs + 5 triggers + Tone tab opérationnel
- ✅ `yarn build` OK

---

### Phase 13.3 (P2) — Dispatchers réels + Worker cron + Rate limiting + Onboarding (**NEXT**)
**Pré-requis**
- Credentials Telegram + X API (stockés via Cabinet Vault catégories `telegram`, `x_twitter`) + éventuellement `trading_refs`.

**Livrables**
- Worker :
  - `core/dispatcher_worker.py` (ou extension `core/bot_scheduler.py`) :
    - consomme `propaganda_queue` items `status=approved` et `scheduled_for <= now`
    - applique rate limiting (8/h, 24/j, per-trigger cooldown)
    - écrit `sent/failed` + results dans queue
    - logge dans `propaganda_events`
- Dispatchers réels :
  - `core/dispatchers/telegram.py` (Bot API `sendMessage`)
  - `core/dispatchers/x.py` (OAuth2 user context PKCE + refresh)
- Rate limiting DB :
  - table/collection `propaganda_rate_limits` (ou counters dans `propaganda_settings`)
  - règles : global/hour, global/day, per-trigger/minutes
- Onboarding :
  - checklist credentials + “Test post” vers un channel sandbox
  - intégration Cabinet Vault : lecture des secrets (token/chat_id, client_id/secret/refresh)
- Tests E2E :
  - Manual Fire → approve → envoi réel Telegram
  - Manual Fire → approve → envoi réel X
  - Tests limites : spam guard + cooldown per trigger

**Validation gate**
- E2E “happy path” Telegram + X
- Vérification anti-spam : limites/h + limites/jour + cooldown per trigger

---

### Phase 14 — **Pre-Launch Infiltration Brain (PROTOCOL ΔΣ)**
Objectif : rendre jouable le “Proof of Intelligence” côté landing + fournir le pilotage admin (riddles/clearance/sleeper cell/audit) + export airdrop.

#### Choix UX validés (user = “go reco”)
- **1a** Point d’entrée : visible dans Terminal **en mode `sealed` ET `denied`**
- **2a** Progression : **séquentielle** (1 énigme à la fois sur 5)
- **3b** Email : demandé **seulement à la 1ère victoire** (claim Level 3)
- **4a** Wallet Solana : capturé **immédiatement** après Level 3
- **5a** Esthétique : CRT vert cohérent, avec accents **ambre** (`#F59E0B`) pour signaler la branche “Clearance 3”

#### Endpoints consommés (public)
- `GET /api/infiltration/riddles?locale=fr|en` (liste sans keywords)
- `POST /api/infiltration/riddles/{slug}/attempt` `{ answer, email?, locale }`
- `GET /api/infiltration/clearance/{email}`
- `POST /api/infiltration/clearance/link-wallet` `{ email, wallet_address }`

---

### Phase 14.1 (P0) — Backend + Admin UI ✅ / Public Terminal flow ⏳ (**NEXT**)
**Livrables (réalisés)**
- ✅ Backend riddles/clearance/sleeper cell + seed 5 énigmes + anti-bruteforce
- ✅ Endpoints admin + public dans `routers/infiltration.py`
- ✅ Admin UI : `/app/frontend/src/pages/Infiltration.tsx` (tabs : Riddles/Clearance/Sleeper/Attempts)

**Livrables (à faire — P0)**
1) **I18n**
- Ajouter les clés `terminal.riddles.*` dans `/app/frontend/src/i18n/translations.js` (FR + EN)
  - intro/briefing, CTA, libellés inputs, erreurs, messages succès, hint/warning attempts_left

2) **TerminalPopup — ajout de la branche Proof of Intelligence**
- Fichier : `/app/frontend/src/components/landing/vault/TerminalPopup.tsx`
- Ajouter un CTA “Proof of Intelligence” dans les phases `denied` et `sealed`
- Étendre le type `TerminalPhase` avec les phases :
  - `riddles-intro`
  - `riddles-play`
  - `riddles-claim`
  - `riddles-wallet`
  - `riddles-complete`

3) **Sous-composant de flow**
- Créer un sous-composant interne (ou extrait) `RiddlesFlow` qui gère :
  - chargement `GET /api/infiltration/riddles?locale=${lang}`
  - progression séquentielle (index courant)
  - soumission `POST /api/infiltration/riddles/{slug}/attempt`
  - feedback correct/incorrect + affichage `attempts_left`
  - affichage `hint` après 3 échecs (heuristique client)
  - **claim email** seulement après 1ʳᵉ bonne réponse (phase `riddles-claim`)
  - persistance légère via `sessionStorage` : `{ email?, solvedSlugs[], currentIndex, level? }`

4) **Claim + Link wallet**
- Après claim email :
  - `GET /api/infiltration/clearance/{email}` (afficher Level)
- Sur wallet :
  - `POST /api/infiltration/clearance/link-wallet` + validation base58 côté UI (32–44, regex similaire backend)

5) **Qualité / DX**
- Ajouter des `data-testid` pour le testing agent (CTA, inputs, submit, étapes)
- Garder la posture sécurité existante : pas de leak keywords (on consomme seulement la liste publique)

**Validation gate (Sprint 14.1 Frontend)**
- ✅ `yarn build` (frontend)
- ✅ Smoke manuel + screenshots :
  - Terminal open → CTA Proof of Intelligence en `sealed` et en `denied`
  - résolution d’énigme 1 → claim email → link wallet → complete
  - erreurs : mauvais answer → attempts_left diminue, hint visible après 3 erreurs
- ✅ Tests frontend (testing agent) *dans la limite sessionStorage* :
  - vérifier que le state `sessionStorage` permet de reprendre le flow en rouvrant le terminal

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
  - Dispatch Telegram + X réels, worker cron fiable, rate limiting robuste, onboarding clair.
- Phase 14.1 :
  - Terminal public : Proof of Intelligence jouable, UX cohérente CRT, **Level 3 obtenu** + wallet lié.
  - Admin : stats/ledger/snapshot CSV/sleeper cell opérationnels.

---

## 5) Notes d’architecture (Phase 13–14)

**Backend (réel, livré/planifié)**
- ✅ `core/propaganda_engine.py` : orchestration, randomization, delay 10–30s, template pick, LLM rewrite (13.2)
- ✅ `core/triggers/*` : détecteurs + idempotency
- ✅ `core/market_analytics.py` : windows prix/MC, detect_dip, snapshots TTL
- ✅ `core/templates_repo.py` : storage templates + versioning
- ✅ `core/dispatch_queue.py` : approval queue
- ✅ `core/tone_engine.py` : LLM rewrite constrained + safety
- ✅ `routers/propaganda.py` : API admin
- ⏳ 13.3 `core/dispatcher_worker.py` : consume queue + dispatch real platforms + mark sent/failed
- ⏳ 13.3 `core/dispatchers/telegram.py`, `core/dispatchers/x.py`

- ✅ Infiltration Brain :
  - `core/riddles.py` : seed 5 énigmes, normalisation accents, audit attempts, rate-limit soft
  - `core/clearance_levels.py` : ledger (email PK), Level 3 via riddle solve (bootstrapping), link wallet
  - `core/sleeper_cell.py` : kill-switch pré-mint (messages FR/EN + blocked triggers)
  - `routers/infiltration.py` : endpoints publics + admin, mutations admin 2FA

**Frontend**
- ✅ `pages/Propaganda.tsx` : panel admin complet (5 tabs incl. Tone)
- ✅ `pages/Infiltration.tsx` : panel admin infiltration (Riddles/Clearance/Sleeper/Attempts)
- ⏳ `components/landing/vault/TerminalPopup.tsx` : intégrer la branche Proof of Intelligence

**DB Collections**
- Propaganda :
  - `propaganda_templates`, `propaganda_queue`, `propaganda_events`, `propaganda_settings`, `propaganda_triggers`, `propaganda_price_snapshots` (TTL 1h)
  - (13.3) `propaganda_rate_limits` (proposé)
- Infiltration :
  - `riddles`
  - `riddle_attempts` (TTL 24h)
  - `clearance_levels` (unique email, unique wallet sparse)
  - `sleeper_cell` (state unique)

**Sécurité**
- Propaganda : lecture/édition templates = admin JWT ; panic/approve/reject = admin JWT + 2FA.
- Infiltration :
  - endpoints publics : pas de fuite des keywords, rate-limit côté `riddles.submit_attempt`
  - endpoints admin : mutations = 2FA obligatoire (`TWOFA_REQUIRED`)
- Secrets dispatchers : Cabinet Vault (catégories `telegram`, `x_twitter`, `trading_refs`)
