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
- **Phase 17.F — OpenAI image (gpt-image-1) pour preview bots (P1)** : ajouter un provider image alternatif on-demand, sans changer le dispatch réel (reste dry-run pré-mint).
- **Phase 17.G — Vercel deploy package (P1)** : livrer le trio de docs + validation pipeline locale pour que l’utilisateur finalise le déploiement en autonomie.

> Stratégie : “migration gates” (tsc/build + smoke tests) à chaque sprint + validation API (curl/testing) avant activation en prod.

### État actuel (mise à jour)
- Couverture TS/TSX : ~94% du frontend migré (reste quelques gros JSX stables : `AdminBots.jsx`, `AdminVault.jsx` — migration différée post-déploiement).
- Sécurité session : migration `localStorage` → **`sessionStorage`** effectuée.
- Backend : prêt Render (suppression libs propriétaires + chemins relatifs + wrapper LLM). **+ routing hybride LLM (Phase 17.D)**.
- Frontend : `yarn build` OK en local + `CI=true yarn build` OK.
- **Blocage/risque actuel** : déploiement frontend Vercel — nécessite que les derniers commits soient **poussés sur GitHub** puis redéployés via **Deploy Hook**.
- **Vercel SPA routing** : `vercel.json` contient déjà les **rewrites SPA** ; les 404 sur navigation directe (`/admin`, `/how-to-buy`) indiquent un déploiement Vercel sur un commit ancien.
- **Emails Resend (prod)** : ajout d’un endpoint diagnostic admin pour comparer configuration Preview vs Render.
- **Propaganda Engine** : Sprint 13.3.x livré (retry/backoff, preflight creds, bannière UI) — améliore l’opérationnalité pré-live.

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

#### Sprint 13.3 — Dispatchers & Worker cron (scaffold) — ✅ COMPLET
- Worker APScheduler (tick toutes les 30s) : claim atomique `approved → in_flight → sent|failed`.
- Dispatchers : `telegram.sendMessage` + `X POST /2/tweets` (OAuth1.0a) + mode dry-run.
- Garde-fous : `dispatch_enabled` (default false) + `dispatch_dry_run` (default true) + rate limits.
- Routes admin :
  - `GET /api/admin/propaganda/dispatch/status` (observabilité)
  - `POST /api/admin/propaganda/dispatch/toggle` (2FA)
  - `POST /api/admin/propaganda/dispatch/tick-now` (2FA)
- Doc ops : `/app/docs/SPRINT_13_3_DISPATCHERS.md`.

#### Sprint 13.3.x — Robustesse opérationnelle (pré-live) — ✅ COMPLET
- Retry/backoff exponentiel pour erreurs transientes (429/5xx/timeout/network) : **60s / 120s / 240s**, **max 3 tentatives** (`MAX_RETRIES=3`).
- Nouvel endpoint non destructif : `GET /api/admin/propaganda/dispatch/preflight` (audit des secrets Telegram/X, vault/env, sans fuite de valeurs).
- UI Admin Propaganda : **bannière de mode de dispatch** (PAUSED / DRY-RUN / LIVE / PANIC) dans `Propaganda.tsx`.
- Observabilité worker enrichie : champ `retried` dans le résumé de tick.

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

#### Emails transactionnels (Resend) — ✅ Diagnostics livrés
- Nouvel endpoint : `GET /api/admin/email/diagnostics` (présence des secrets, source vault/env, sender résolu, aperçu événements récents, compteurs whitelist sent/failed).
- But : debug rapide en production Render sans exposer de secret.

#### Tests automatisés & validations
- Cabinet Vault : E2E backend ✅ ; import/export ✅.
- Propaganda Engine : smoke tests backend + UI ✅.
- Infiltration Brain : E2E manuel + curls backend ✅.
- Phase 17 : reproduction bug AJV npm ✅ ; yarn build ✅.
- Phase 17.B : `CI=true yarn build` ✅.
- Phase 17.C : tests curl 9/9 ✅.
- Phase 17.D : tests preview bots + prophète ✅.
- Phase 17.E : `CI=true yarn build` ✅ + smoke tests preview ✅.
- Phase 17.F : curl tests image providers (Gemini + OpenAI) ✅ + `CI=true yarn build` ✅.
- **Phase 17.G** : validation pipeline Vercel local (install+build) ✅ + docs ✅.
- **Sprint 13.3.x** :
  - Build frontend prod OK (taille +624B) ✅
  - Tick worker simulé (1 item dispatched en dry-run Telegram+X) ✅
  - Preflight : Telegram READY / X MISSING creds ✅
  - Screenshot UI : bannière dispatch visible ✅
- **Email diagnostics** : endpoint testé et fonctionnel ✅

#### Restant
- **P0** : Phase 17 — confirmer que le dernier commit est sur GitHub et **redeploy Vercel** (Deploy Hook) ; valider fin des 404 SPA sur `/admin` et `/how-to-buy`.
- **P1 (activation live)** : Propaganda dispatch LIVE :
  - Telegram : prêt (creds détectés en env sur preview) → à migrer dans Vault si souhaité.
  - X : credentials manquants (nécessite tier Elevated/Pro) + secret vault/env.
- **P1** : Debug Resend sur Render : appeler `/api/admin/email/diagnostics` sur l’URL Render pour comparer (vault/env, sender, events) et corriger la config.
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

#### Phase 13.3 (P2) — Dispatchers + Worker cron + Rate limiting + Onboarding ✅ **COMPLETED**
**Objectif** : exécuter réellement les posts X/TG depuis la `propaganda_queue`.

✅ Livré :
- Worker cron (APScheduler 30s tick) + claim atomique.
- Dispatchers Telegram/X + dry-run.
- Settings `dispatch_enabled` + `dispatch_dry_run`.
- Routes admin + doc ops.

#### Phase 13.3.x (P1) — Robustesse + opérabilité ✅ **COMPLETED**
✅ Livré :
- Retry/backoff exponentiel sur erreurs transientes (max 3) et re-scheduling via `scheduled_for`.
- `GET /api/admin/propaganda/dispatch/preflight` (audit secrets, prêt à basculer).
- Bannière UI mode dispatch (PAUSED/DRYRUN/LIVE/PANIC).

⏳ Pour passer en LIVE (user-side) :
1) Vérifier les secrets via `GET /api/admin/propaganda/dispatch/preflight`.
2) Activer worker en dry-run (2FA) : `POST /api/admin/propaganda/dispatch/toggle` `{enabled:true, dry_run:true}`.
3) Forcer un tick (2FA) : `POST /api/admin/propaganda/dispatch/tick-now` et vérifier résultats.
4) Basculer LIVE : `POST /api/admin/propaganda/dispatch/toggle` `{dry_run:false}`.

Notes :
- Telegram est généralement activable immédiatement si bot token + chat_id sont prêts.
- X requiert 4 secrets OAuth1 + tier Elevated/Pro.

Backlog 13.3.y (optionnel) : threads/replies, métriques avancées, UI “preflight” intégré, auto-pause sur répétition d’échecs.

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

### Phase 17 — Déploiement Vercel : Fix build CRA5 / AJV (P0) — **IN PROGRESS (user dashboard pending)**

#### Problèmes identifiés
- Toolchain Vercel (npm/Node24) cause crash AJV.
- Navigation directe sur routes SPA (`/admin`, `/how-to-buy`) renvoie 404 si les rewrites ne sont pas déployés.

#### Fix appliqué (repo)
- ✅ `/app/frontend/.nvmrc` : `20`.
- ✅ `/app/frontend/vercel.json` : force yarn + SPA rewrites + cache headers.
- ✅ `/app/frontend/.npmrc` : filet de sécurité.
- ✅ Docs : `/app/docs/VERCEL_DASHBOARD_SETUP.md`, `/app/docs/VERCEL_REDEPLOY_QUICK.md`, `/app/docs/VERCEL_DEPLOYMENT.md`.

#### Actions requises (utilisateur — dashboard Vercel)
1) **Save to GitHub** depuis Emergent (pour pousser `vercel.json` et le reste).
2) Configurer Vercel : Node 20, install yarn (`yarn install --frozen-lockfile`), pas d’override npm.
3) Redeploy via **Deploy Hook**.
4) Valider :
   - `GET /admin` (direct URL) = 200 + app React
   - `GET /how-to-buy` (direct URL) = 200 + landing

---

### Phase 17.B — Ménage “Strict CI” (P1) — ✅ **COMPLETED**
(identique)

---

### Phase 17.C — Cabinet Vault anti-récidive (P1) — ✅ **COMPLETED**
(identique)

---

### Phase 17.D — Hotfix LLM routing (P0) — ✅ **COMPLETED**
(identique)

---

### Phase 17.E — Code review hygiene cleanup (D only) (P2) — ✅ **COMPLETED**
(identique)

---

### Phase 17.F — OpenAI image (gpt-image-1) pour preview bots (P1) — ✅ **COMPLETED**
(identique)

---

### Phase 17.G — Vercel deploy package (P1) — ✅ **COMPLETED**
(identique)

---

## 4) Success Criteria
- Phases 1–14 : inchangé, déjà atteint.
- **Phase 17** : déploiement Vercel stable (Node 20 + yarn) ; build prod OK ; **plus de 404 SPA** sur refresh/direct navigation.
- **Phase 17.B** : build strict sans `CI=false`.
- **Phase 17.C** : vault non-brickable + recovery autonome.
- **Phase 17.D** : Preview Emergent stable + Render compatible via fallback natif.
- **Phase 17.E** : réduction des inline motion objects sur les surfaces critiques (home + classified vault) sans régression.
- **Phase 17.F** : preview bots supporte A/B image (Gemini default + OpenAI gpt-image-1 variant) avec timeouts et UX safe.
- **Phase 17.G** : docs + validation pipeline locale permettant au user de redeploy Vercel en autonomie.
- **Sprint 13.3 + 13.3.x** :
  - Dispatchers opérationnels (dry-run) + robustesse retry/backoff.
  - Preflight creds disponible.
  - UI surfacing clair du mode PAUSED/DRYRUN/LIVE/PANIC.
- **Emails (Resend)** : endpoint diagnostic permet d’isoler la cause (secrets absents, sender non vérifié, events manquants) sur Render.

---

## 5) Notes d’architecture (Phase 13–17)

**Backend**
- ✅ Propaganda : orchestrateur + triggers + queue + templates + tone engine.
- ✅ 13.3 : dispatchers + worker APScheduler + routes admin + doc ops.
- ✅ 13.3.x : retry/backoff + preflight creds + diagnostics état (résumé tick avec `retried`).
- ✅ Diagnostics Resend : `/api/admin/email/diagnostics`.
- ✅ Infiltration Brain : riddles/clearance/sleeper cell.
- ✅ Whale watcher : Helius webhooks + monitoring admin (base).
- ✅ Vault recovery : `factory_reset_vault()` + route sécurisée.
- ✅ LLM routing hybride (17.D) : Mode A (proxy Emergent) / Mode B (SDK natif).
- ✅ Image routing bots preview (17.F) :
  - Gemini : `prophet_studio.generate_image()` via `LlmChat` multimodal
  - OpenAI : `core/openai_image_gen.generate_image_openai()` via `OpenAIImageGeneration`.

**Frontend**
- ✅ Panels admin : `pages/Propaganda.tsx`, `pages/Infiltration.tsx`.
- ✅ Propaganda UI : bannière d’état dispatch (PAUSED/DRYRUN/LIVE/PANIC).
- ✅ Terminal : `TerminalPopup.tsx` + `RiddlesFlow.tsx`.
- ✅ Phase 17 : fichiers Vercel/Node ajoutés.
- ✅ Phase 17.B : build strict nettoyé.
- ✅ Phase 17.C : Danger Zone + hardening wizard.
- ✅ Phase 17.E : `motionVariants.ts` + extraction d’inline objects.
- ✅ Phase 17.F : UI A/B image dans `AdminBots.jsx` via bouton variant.

**DB Collections**
- Propaganda : `propaganda_templates`, `propaganda_queue`, `propaganda_events`, `propaganda_settings`, `propaganda_triggers`, `propaganda_price_snapshots`.
- Infiltration : `riddles`, `riddle_attempts` (TTL 24h), `clearance_levels`, `sleeper_cell`.
- Email : `email_events` + champs email dans `whitelist` (`email_status`, `email_error`, etc.).
- Whale watcher / disclosure : selon implémentation courante + indexes (cf. docs).
- Vault : `cabinet_vault`, `cabinet_vault_audit`, `admin_2fa`.

**Sécurité**
- Propaganda : lecture/édition templates = admin JWT ; panic/approve/reject/toggles dispatch = admin JWT + 2FA.
- Infiltration : endpoints publics rate-limit ; mutations admin = 2FA.
- Whale watcher feed public : anonymisé.
- Secrets dispatchers : Cabinet Vault (recommandé) avec fallback env.
- Déploiement : CRA5 doit rester sur Node LTS (20) ; éviter Node 24+ tant que migration Vite non réalisée.
- Recovery : Factory reset exige vault LOCKED + password + 2FA (si active) + confirm string.
- LLM : Preview utilise proxy Emergent (EMERGENT_LLM_KEY) ; prod Render préfère clés natives (Mode B).
- Images : OpenAI gpt-image-1 via proxy Emergent (admin preview uniquement) ; coût et latence plus élevés, usage volontaire via bouton variant.
