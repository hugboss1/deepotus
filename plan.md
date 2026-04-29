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

> Stratégie : “migration gates” (tsc/build + smoke tests) à chaque sprint + validation API (curl/testing agent) avant activation en prod.

### État actuel (mise à jour)
- Couverture TS/TSX : ~94% du frontend migré (reste quelques gros JSX stables : `AdminBots.jsx`, `AdminVault.jsx` — migration différée post-déploiement).
- Sécurité session : migration `localStorage` → **`sessionStorage`** effectuée.
- Backend : prêt Render (suppression libs propriétaires + chemins relatifs + wrapper LLM). **+ routing hybride LLM (Phase 17.D)**.
- Frontend : `yarn build` OK en local + `CI=true yarn build` OK.
- **Blocage actuel** : déploiement frontend sur Vercel (tooling incorrect : npm + Node 24) → crash AJV (Phase 17 en attente côté dashboard).
- **Preview Emergent** : Prophète + preview bots fonctionnels (Mode A via `emergentintegrations`).
- **Code review externe (374 “issues”)** : audit confirmé → majorité faux positifs ; seules actions retenues : **Phase 17.E (motion cleanup)**.

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
  - 5 triggers : `mint`, `mc_milestone`, `jeet_dip`, `whale_buy`, `raydium_migration`.
  - `market_analytics.py` : snapshots prix/MC (TTL 1h), dip detection.
  - `tone_engine.py` : LLM hybride 70/30 (configurable), persona, post-processor.
  - FR optionnel : templates FR seedés.
  - `PATCH /api/admin/propaganda/settings` : settings LLM.
  - Frontend : tab **Tone & LLM**.

#### Infiltration Brain (Sprint 14.1) — ✅ Backend + ✅ Admin UI + ✅ Public Terminal flow
- Backend : riddles/clearance/sleeper cell + endpoints.
- Seeds 5 énigmes + anti-bruteforce.
- Admin UI : `/app/frontend/src/pages/Infiltration.tsx`.
- Public UX : intégration “Proof of Intelligence” via `TerminalPopup.tsx` + `RiddlesFlow.tsx`.
- Fix index wallet MongoDB (partial unique index).

#### Whale Watcher & disclosures (Sprint 15/16) — ✅ BASE LIVRÉE
- `TOKENOMICS_TREASURY_POLICY.md` créé.
- Helius webhooks + worker + UI admin.
- Seeds triggers/templates : `founder_buy`, `kol_mention`.
- UI landing `AccessSecuredTerminals.tsx`.

#### Qualité code (post-review) — ✅ PASS SAFE FIXES
- catch silencieux → logs debug.
- ternaires imbriqués → refactor lisibilité.
- `random` → `secrets.SystemRandom()` là où pertinent.

#### Tests automatisés & validations
- Cabinet Vault : E2E backend ✅ ; import/export ✅.
- Propaganda Engine : smoke tests backend + UI screenshots ✅.
- Infiltration Brain : E2E manuel + curls backend ✅.
- Phase 17 : reproduction bug AJV npm ✅ ; yarn build ✅.
- Phase 17.B : `CI=true yarn build` ✅.
- Phase 17.C : tests curl 9/9 ✅.
- Phase 17.D : tests preview bots + prophète ✅.
- **Phase 17.E** : `CI=true yarn build` ✅ + smoke tests preview ✅.

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

#### Phase 13.1 (P0) — MVP Squelette ✅ **COMPLETED**
(identique)

#### Phase 13.2 (P1) — Triggers complets + Tone Engine ✅ **COMPLETED**
(identique)

#### Phase 13.3 (P2) — Dispatchers réels + Worker cron + Rate limiting + Onboarding (**NEXT**)
**Objectif** : exécuter réellement les posts X/TG depuis la `propaganda_queue`.
- Worker cron/queue runner (APScheduler ou job dédié).
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
Objectif : connecter l’indexation on-chain (Helius) au lore (Propaganda Engine) **sans logique de trading**, publier une politique publique de trésorerie conforme MiCA, et ajouter l’outillage admin de disclosure.

(Phases 15.1–15.5 : identiques ; mise à jour fine possible post-déploiement)

---

### Phase 17 — Déploiement Vercel : Fix build CRA5 / AJV (P0) — **IN PROGRESS**

#### Problème
- Vercel est configuré avec :
  - Install Command override : `npm install --legacy-peer-deps`
  - Node.js 24.x
- CRA5 + `schema-utils`/`ajv-keywords@5` sensibles au hoisting npm → `MODULE_NOT_FOUND: ajv/dist/compile/codegen`.

#### Fix appliqué (repo)
- ✅ `/app/frontend/.nvmrc` : `20`.
- ✅ `/app/frontend/vercel.json` : force yarn + SPA rewrites + cache headers.
- ✅ `/app/frontend/.npmrc` : filet de sécurité.
- ✅ Doc : `/app/docs/VERCEL_DEPLOYMENT.md`.

#### Actions requises (utilisateur — dashboard Vercel)
1) Désactiver l’override Install Command (ou mettre `yarn install --frozen-lockfile`).
2) Node.js Version : 24.x → 20.x.
3) Redeploy et vérifier `yarn install` + `yarn build`.

---

### Phase 17.B — Ménage “Strict CI” : suppression warnings hooks (P1) — ✅ **COMPLETED**
(identique)

---

### Phase 17.C — Cabinet Vault anti-récidive (P1) — ✅ **COMPLETED**
(identique)

---

### Phase 17.D — Hotfix LLM routing (P0) — ✅ **COMPLETED**
(identique)

---

### Phase 17.E — Code review hygiene cleanup (D only) (P2) — ✅ **COMPLETED**

#### Contexte
Un rapport externe a signalé ~374 “issues”. Audit avec les outils **sources de vérité** :
- CRA ESLint : 0 `react-hooks/exhaustive-deps`.
- Ruff : `F821` / `E711` / `E712` / `F632` clean.
- localStorage : thèmes (non-sensible) OK ; adminAuth déjà migré vers sessionStorage.
- `scripts_generate_redacted_dossier.py` : `random` seedé intentionnellement pour builds PNG byte-stables (`# noqa: S311`).

Décision utilisateur : **A** (pas de refactors majeurs maintenant) + **D** (motion cleanup uniquement).

#### Implémentation (D)
- ✅ Nouveau module `src/lib/motionVariants.ts`
  - 30+ constantes nommées pour `initial/animate/exit/transition/viewport`.
  - JSDoc : rationalise la perf (identité stable → évite restart des tweens) + conventions de nommage.
- ✅ Migration de 7 fichiers à fort trafic vers des variants stables (inline motion objects → 0) :
  - `components/landing/vault/VaultSection.tsx`
  - `components/landing/hero/HeroPoster.tsx`
  - `components/landing/Mission.tsx`
  - `components/landing/PropheciesFeed.tsx` (blur variants module-local + transition commune)
  - `components/landing/ROISimulator.tsx`
  - `pages/classified-vault/GateView.tsx`
  - `pages/classified-vault/AuthedVaultView.tsx`
- ✅ Total : **44 inline motion objects** extraits en références stables.

#### Non inclus (déféré explicitement)
- Refactor gros composants (`AdminBots.jsx`, `TerminalPopup.tsx`, etc.) → post-launch.
- Refactor complexité backend (ex: `cabinet_vault.import_encrypted`) → post-launch.
- Migration de tous les autres fichiers motion (Operation, TerminalPopup, HowToBuy, PublicStats…) → incrémental si nécessaire.

#### Validation
- ✅ `CI=true yarn build` : Compiled successfully.
- ✅ Smoke tests : preview URL 200, prophète OK, bots preview OK (Mode A Emergent).

---

## 4) Success Criteria
- Phases 1–14 : inchangé, déjà atteint.
- **Phase 17** : déploiement Vercel stable (Node 20 + yarn) ; build prod OK.
- **Phase 17.B** : build strict sans `CI=false`.
- **Phase 17.C** : vault non-brickable + recovery autonome.
- **Phase 17.D** : Preview Emergent stable + Render compatible via fallback natif.
- **Phase 17.E** : réduction des inline motion objects sur les surfaces critiques (home + classified vault) sans régression.
- **Sprint 13.3** : dispatchers réels (Telegram/X) opérationnels.
- **Sprint 14.2** : KOL infiltration + validation clearance 1/2.
- **Sprint 15.x** : transparence MiCA (policy publique) + outillage disclosure.

---

## 5) Notes d’architecture (Phase 13–17)

**Backend**
- ✅ Propaganda : orchestrateur + triggers + queue + templates + tone engine.
- ⏳ 13.3 : dispatchers réels + worker cron + rate limiting + onboarding.
- ✅ Infiltration Brain : riddles/clearance/sleeper cell.
- ✅ Whale watcher : Helius webhooks + monitoring admin (base).
- ✅ Vault recovery : `factory_reset_vault()` + route sécurisée.
- ✅ LLM routing hybride (17.D) : Mode A (proxy Emergent) / Mode B (SDK natif).

**Frontend**
- ✅ Panels admin : `pages/Propaganda.tsx`, `pages/Infiltration.tsx`.
- ✅ Terminal : `TerminalPopup.tsx` + `RiddlesFlow.tsx`.
- ✅ Phase 17 : fichiers Vercel/Node ajoutés.
- ✅ Phase 17.B : build strict nettoyé.
- ✅ Phase 17.C : Danger Zone + hardening wizard.
- ✅ Phase 17.E : `motionVariants.ts` + extraction de 44 inline objects sur surfaces critiques.

**DB Collections**
- Propaganda : `propaganda_templates`, `propaganda_queue`, `propaganda_events`, `propaganda_settings`, `propaganda_triggers`, `propaganda_price_snapshots`.
- Infiltration : `riddles`, `riddle_attempts` (TTL 24h), `clearance_levels`, `sleeper_cell`.
- Whale watcher / disclosure : selon implémentation courante + indexes (cf. docs).
- Vault : `cabinet_vault`, `cabinet_vault_audit`, `admin_2fa`.

**Sécurité**
- Propaganda : lecture/édition templates = admin JWT ; panic/approve/reject = admin JWT + 2FA.
- Infiltration : endpoints publics rate-limit ; mutations admin = 2FA.
- Whale watcher feed public : anonymisé.
- Secrets dispatchers : Cabinet Vault.
- Déploiement : CRA5 doit rester sur Node LTS (20) ; éviter Node 24+ tant que migration Vite non réalisée.
- Recovery : Factory reset exige vault LOCKED + password + 2FA (si active) + confirm string.
- LLM : Preview utilise proxy Emergent (EMERGENT_LLM_KEY) ; prod Render préfère clés natives (Mode B).
