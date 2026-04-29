# DEEPOTUS — Plan de finalisation TypeScript & sécurité “Cabinet Vault” **+ Propaganda Engine ΔΣ** (Sprints 6 → 13.3 + Infiltration 14.x + Brain Connect 15.x + Déploiements 17)

## 1) Objectives
- Stabiliser et clarifier le code (split des gros composants, réduction de complexité) **avant** migration d’hébergement (Vercel/Render).
- Augmenter la couverture TS/TSX sur le code **applicatif** (hors Shadcn UI auto-généré), sans casser l’existant.
- Garantir une base prête pour un déploiement **Vercel (frontend) / Render (backend)** avec builds production OK.
- Préserver le comportement actuel (bots en **dry-run** tant que credentials non fournis, vault, ROI, intro, admin).
- **Centraliser la gestion des secrets** via le **Cabinet Vault** (BIP39 + PBKDF2 + AES-256-GCM) et migrer les clés existantes (LLM, Resend, Helius, bots) vers ce coffre.
- **Conformité sécurité** : 2FA côté admin pour les actions sensibles, audit logging, rotation, export/import de backups chiffrés.
- **PROTOCOL ΔΣ — Propaganda Engine** : automatiser une logique “scenario-based” (triggers marché → message → queue → dispatch) pour réagir au marché avec garde-fous anti-slop, **testable pré-mint** via Manual Fire, et opérable via UI admin.
- **PROTOCOL ΔΣ — Infiltration Brain** : livrer l’expérience publique “Proof of Intelligence” (5 énigmes Terminal → Clearance Level 3 → lien wallet Solana) + surface admin (riddles/clearance/sleeper cell/audit) conforme à la posture sécurité.
- **Sprint 15 — Brain Connect & Treasury Architecture (MiCA)** : relier l’indexation on-chain (Helius) au Lore du site **sans logique de trading**, publier une politique de trésorerie transparente, et fournir l’outillage admin de disclosure.
- **Phase 17 — Déploiement Vercel (P0)** : fiabiliser le build CRA5 en environnement Vercel (Node + install toolchain) et éliminer le crash `ajv/dist/compile/codegen`.

> Stratégie : “migration gates” (tsc/build + smoke tests) à chaque sprint + validation API (curl/testing agent) avant activation en prod.

### État actuel (mise à jour)
- Couverture TS/TSX : **~94% du frontend** migré (reste quelques gros JSX stables : `AdminBots.jsx`, `AdminVault.jsx` — migration différée post-déploiement).
- Sécurité session : migration `localStorage` → **`sessionStorage`** effectuée.
- Backend : prêt Render (suppression libs propriétaires + chemins relatifs + wrapper LLM natif).
- Frontend : **`yarn build` OK** en local.
- **Blocage actuel** : déploiement frontend sur Vercel (tooling incorrect : npm + Node 24) → crash AJV.

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

#### Whale Watcher & disclosures (Sprint 15/16) — ✅ BASE LIVRÉE
- ✅ `TOKENOMICS_TREASURY_POLICY.md` créé.
- ✅ Intégration Helius webhooks + worker (`whale_watcher.py`) + UI admin.
- ✅ Seeds triggers/templates pour `founder_buy` et `kol_mention`.
- ✅ UI landing `AccessSecuredTerminals.tsx` pour liens BonkBot/Trojan.

#### Qualité code (post-review) — ✅ PASS SAFE FIXES
- ✅ Remplacement des `catch {}` silencieux par logs debug (frontend).
- ✅ Remplacement de ternaires imbriqués (Propaganda/Infiltration/CabinetVault) pour lisibilité.
- ✅ Remplacement `random` → `secrets.SystemRandom()` là où pertinent (tone_engine/templates_repo/propaganda_engine).

#### Tests automatisés & validations
- **Iteration 16** : backend Cabinet Vault (12.3.E2E backend) ✅.
- **Iteration 17** : régression Sprint 12.4 (SecretProvider) ✅.
- **Iteration 18** : Sprint 12.5 Import/Export (22/22) ✅.
- **Sprint 13.2** : smoke tests backend (9/9) + screenshots frontend (5 tabs + Tone tab) ✅.
- **Sprint 14.1** :
  - ✅ E2E manuel : intro → play → claim → wallet → complete (FR/EN), hint après 3 échecs, wrong answer, persistance sessionStorage.
  - ✅ Curls backend : attempt, clearance, link-wallet OK.
  - ⚠️ Playwright : difficulté avec l’animation d’intro (DEEPSTATE.SYS) ; privilégier screenshots manuels.
- **Phase 17 (Vercel)** :
  - ✅ `yarn build` local : SUCCESS.
  - ✅ `yarn install --frozen-lockfile` : lockfile valide.
  - ✅ `npm install --legacy-peer-deps` : reproduit le bug `ajv/dist/compile/codegen`.

#### Restant
- **P0** : Phase 17 (Vercel build) — attente changement dashboard Vercel + redeploy.
- **NEXT** : Sprint 13.3 (dispatchers réels Telegram/X) — dépend credentials API et worker cron.
- **Upcoming** : Sprint 14.2 (KOL Infiltration auto-DMs + validation clearance levels 1/2).

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

## 3) Next Actions

### Phase 13 — **PROTOCOL ΔΣ : Propaganda Engine**
(identique)

#### Phase 13.1 (P0) — MVP Squelette ✅ **COMPLETED**
(identique)

#### Phase 13.2 (P1) — Triggers complets + Tone Engine ✅ **COMPLETED**
(identique)

#### Phase 13.3 (P2) — Dispatchers réels + Worker cron + Rate limiting + Onboarding (**NEXT**) 
**Objectif** : exécuter réellement les posts X/TG depuis la `propaganda_queue`.
- Worker cron/queue runner (APS cheduler ou job dédié).
- Intégration X API + Telegram Bot API.
- Rate limiting + retry/backoff.
- Secrets : credentials dans Cabinet Vault (`x_twitter`, `telegram`).

---

### Phase 14 — **Pre-Launch Infiltration Brain (PROTOCOL ΔΣ)**

#### Phase 14.1 (P0) — Backend + Admin UI + Public Terminal flow ✅ **COMPLETED**
(identique)

#### Phase 14.2 (P2) — KOL Infiltration Logic (X/Twitter) (**UPCOMING**) 
- Automatisation “Mirror” et “Recruitment” (auto-DMs).
- Validation Clearance Levels 1 & 2 (Follow X / Join TG).
- Garde-fous : anti-spam + quotas.

---

### Phase 15 — **Brain Connect & Treasury Architecture (MiCA) — NEXT**
Objectif : connecter l’indexation on-chain (Helius) au Lore (Propaganda Engine) **sans logique de trading**, publier une politique publique de trésorerie conforme MiCA, et ajouter l’outillage admin de disclosure.

#### Architecture confirmée (user)
- **Wallet_TEAM_VESTING (15%)** : Streamflow public, vesting **12 mois** (protéger réputation).
- **Wallet_TREASURY (30%)** : Squads multisig, politique de take-profit **transparente** pour financer projet MiCA.
- **Founder buy** : achat personnel au launch (skin in the game) + disclosure publique outillée (Propaganda approval queue).
- **Whale Watcher** : 100% *observer/narrator*, intégré aux **webhooks Helius** + Propaganda Engine.
- **Performance** : APScheduler isolé + **queue Mongo-backed**.
- **Hors scope explicite** : ❌ aucun trading/snipe/floor/wash, ❌ aucune clé privée.

(Phases 15.1–15.5 : identiques, déjà alignées avec l’implémentation actuelle ; mise à jour fine possible post-déploiement)

---

### Phase 17 — Déploiement Vercel : Fix build CRA5 / AJV (P0) — **IN PROGRESS**

#### Problème
- Vercel est configuré avec :
  - **Install Command** override : `npm install --legacy-peer-deps`
  - **Node.js 24.x**
- CRA5 + `schema-utils`/`ajv-keywords@5` sont sensibles au hoisting npm :
  - npm hoiste `ajv@6` au root (attendu par CRA/fork-ts-checker)
  - mais `ajv-keywords@5` exige `ajv@8` et tente `require("ajv/dist/compile/codegen")`
  - => `MODULE_NOT_FOUND: ajv/dist/compile/codegen`
- **Reproduit localement** : `npm install --legacy-peer-deps` + `craco build` => même crash.

#### Fix appliqué (repo)
- ✅ `/app/frontend/.nvmrc` : `20` (Node 20 LTS, compatible CRA5).
- ✅ `/app/frontend/vercel.json` :
  - force `yarn install --frozen-lockfile` + `yarn build`
  - `framework=create-react-app`
  - SPA rewrites vers `/index.html`
  - headers cache long pour `/static/*`.
- ✅ `/app/frontend/.npmrc` : filet de sécurité (`legacy-peer-deps=true`) si Vercel retombe sur npm.

#### Actions requises (utilisateur — dashboard Vercel)
1) **Build & Development Settings → Install Command**
   - Désactiver l’override `npm install --legacy-peer-deps` **ou** remplacer par :
     - `yarn install --frozen-lockfile`
2) **Runtime Settings → Node.js Version**
   - Passer de **24.x** à **20.x**

#### Validation gate
- Déclencher un redeploy et vérifier :
  - build log : `yarn install` + `yarn build`
  - absence d’erreur `ajv/dist/compile/codegen`

---

## 4) Success Criteria
- Phases 1–14 : inchangé, déjà atteint.
- **Phase 17** : déploiement Vercel stable (Node 20 + yarn) ; build prod OK.
- **Sprint 13.3** : dispatchers réels (Telegram/X) opérationnels (queue → dispatch) avec rate limiting.
- **Sprint 14.2** : KOL infiltration + validation clearance 1/2 (sans spam).
- **Sprint 15.x** : transparence MiCA (policy publique) + outillage disclosure + feed public anonymisé.

---

## 5) Notes d’architecture (Phase 13–17)

**Backend**
- ✅ Propaganda : orchestrateur + triggers + queue + templates + tone engine.
- ⏳ 13.3 : dispatchers réels + worker cron + rate limiting + onboarding.
- ✅ Infiltration Brain : riddles/clearance/sleeper cell.
- ✅ Whale watcher : Helius webhooks + monitoring admin (base).

**Frontend**
- ✅ `pages/Propaganda.tsx` : panel admin complet.
- ✅ `pages/Infiltration.tsx` : panel admin infiltration.
- ✅ Terminal : `TerminalPopup.tsx` + `RiddlesFlow.tsx`.
- ✅ Phase 17 : fichiers Vercel/Node ajoutés pour garantir le build.

**DB Collections**
- Propaganda : `propaganda_templates`, `propaganda_queue`, `propaganda_events`, `propaganda_settings`, `propaganda_triggers`, `propaganda_price_snapshots`.
- Infiltration : `riddles`, `riddle_attempts` (TTL 24h), `clearance_levels`, `sleeper_cell`.
- Whale watcher / disclosure : selon implémentation courante + indexes (cf. docs).

**Sécurité**
- Propaganda : lecture/édition templates = admin JWT ; panic/approve/reject = admin JWT + 2FA.
- Infiltration : endpoints publics rate-limit ; mutations admin = 2FA.
- Whale watcher feed public : **anonymisé**.
- Secrets dispatchers : Cabinet Vault (catégories `telegram`, `x_twitter`, `trading_refs`, `x_twitter`).
- **Déploiement** : CRA5 doit rester sur Node LTS (20) ; éviter Node 24+ tant que migration Vite non réalisée.
