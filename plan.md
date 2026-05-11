# DEEPOTUS — Plan de finalisation TypeScript & sécurité “Cabinet Vault” **+ Propaganda Engine ΔΣ**
(Sprints 6 → 13.3 + Infiltration 14.x + Brain Connect 15.x + Déploiements 17 + Hardening 22.x → 24 + Sprint 23/24 + **Sprint 17.5 Cabinet Expansion** + **Sprint 17.5b Admin Bots Panel** + **Sprint 17.5c Pre‑Mint Blockers** + **Sprint 17.6 Operation Incinerator**)

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
- **Pre-mint UX / deep-linking** : assurer un parcours “recrutement / accréditation” sans friction via un deep-link unique `/#accreditation`.
- **Sprint 17.5 — Cabinet Expansion** : croissance automatisée et conversationnelle sur X avec garde-fous (2FA, audit, rate-limits), reconnaissance quotidienne des Agents (Welcome Signal) et replies lore (Prophet Interaction Bot).
- **Sprint 17.5b — Admin Bots Panel Ops** :
  - permettre un **push immédiat** du contenu généré (Preview) vers X/Telegram via le **Real Dispatcher**,
  - éliminer les **exceptions ASGI** liées aux réponses partielles du générateur LLM (hardening Pydantic),
  - rendre le bouton **Release** opératoire en prod pour **forcer une exécution manuelle** des jobs APScheduler.
- **Sprint 17.5c — Pre‑Mint Blockers** :
  - fiabiliser **OAuth 1.0a sur X** (auth httpx‑native) pour débloquer les pushes manuels,
  - réduire la pression sur **DexScreener** (cadence + backoff) pour éliminer les 429,
  - corriger les TypeError “await bool” restant sur des routes/loops bots.
- **Sprint 17.6 — Operation Incinerator (Pre‑Mint P0)** :
  - publier des **burn disclosures** audités (preuve de rareté) + feed public,
  - annoncer les burns via le Propaganda Engine (trigger dédié),
  - mettre à jour `/transparency` avec un **Proof of Scarcity** conforme à la “mathematical honesty”,
  - calculer et afficher la **Real-time circulating supply** en excluant les allocations verrouillées (Treasury + Team).
- **Ops post-prod** : réduire les erreurs humaines (déploiement, secrets, webhooks) via docs exécutables, endpoints diagnostics, et tests automatisés.

> Stratégie : “migration gates” (tsc/build + smoke tests) à chaque sprint + validation API (curl/testing) avant activation en prod.

### État actuel (mise à jour)
- **PRODUCTION LIVE** : `https://www.deepotus.xyz` sur Vercel (frontend) + Render (backend).
- **TypeScript** : migration complète, `noImplicitAny: true`, `npx tsc --noEmit` : 0 erreurs.
- **Cabinet Vault** : AES-256-GCM + lecture stricte par les dispatchers.
- **Propaganda Engine** : dispatchers **X + Telegram LIVE** (réels) et branchés aux APIs, via secrets du vault.
- **Transparence MiCA** : page `/transparency` alimentée dynamiquement par le **Public Wallet Registry** (badges LOCKED/PENDING) + intégration RugCheck.
- **Tests** : backend Pytest (**140 tests**) + Playwright E2E + CI GitHub Actions.
- **UX micro-sprint (deep-link)** : `#accreditation` **déplacé** de Whitelist → **VaultSection**. L’accès à `/#accreditation` ou un `hashchange` ouvre automatiquement le **TerminalPopup DS-GATE-02** et déclenche un pulse ambre 2.6s autour du CTA.

#### Sprint 17.5 — Cabinet Expansion (X) — ✅ COMPLET
- **Production Mode X** forcé : `dispatch_enabled=True`, `dispatch_dry_run=False`.
- Migration idempotente au démarrage : `bootstrap_production_mode()`.
- Vérifs X follow/mention/DM : flags activés (live), cache follow 24h.
- **Welcome Signal** : thread quotidien à 14:00 UTC, cite 2–5 Agents accrédités avec handle X.
- **Prophet Interaction Bot** : replies lore 1–3/h, signé `— ΔΣ`, OFF par défaut → activation admin.
- Frontend : champ `x_handle` optionnel dans Terminal (copy lore) + nouvel onglet **Cabinet** dans `/propaganda`.

#### Sprint 17.5b — Admin Bots Panel updates — ✅ COMPLET
- ✅ **Push to X/Telegram** depuis l’onglet Preview (Admin Bots) : endpoint `POST /api/admin/bots/preview/push` → crée **1 item par plateforme** dans `propaganda_queue` avec `policy=auto`.
- ✅ **Fix ASGI “Exception in ASGI application”** : durcissement Pydantic de `GeneratePreviewResponse` (extra ignore + defaults) + coercion défensive + fallback `502 preview_render_failed`.
- ✅ **Release button** dual-mode :
  - kill-switch armé → release (comportement historique)
  - kill-switch OFF → `POST /api/admin/bots/release-now` force l’exécution des jobs via `APScheduler.modify_job(next_run_time=now)`.

#### Sprint 17.5c — Pre‑Mint blockers (FIXED) — ✅ COMPLET
- ✅ **X Dispatcher TypeError** : OAuth 1.0a httpx‑native via `authlib.integrations.httpx_client.OAuth1Auth`.
- ✅ **DexScreener 429** : cadence 60s + backoff exponentiel persistant.
- ✅ **Bonus** : fix des `await bool` résiduels.
- ✅ **Deps** : `Authlib==1.7.2` ajouté (sans `pip freeze`).
- ✅ **Qualité** : Pytest **101/101** + testing agent 100% backend/front (à l’époque).

#### Sprint 17.6 — Operation Incinerator — ✅ COMPLET
**Tweak critique (Cabinet Investors) appliqué** :
- **Real Circulating Supply** affiché sur `/transparency` =
  `1_000_000_000 - total_burned - 300_000_000 (Treasury) - 150_000_000 (Team)`.
- **Tooltip + disclaimer inline bilingue** :
  - EN : “Real-time circulating supply, excluding the 45% currently under public multisig/vesting locks (300M Treasury + 150M Team).”
  - FR : “Supply circulante temps réel, excluant les 45 % actuellement sous multisig public / vesting locks (300 M Treasury + 150 M Team).”

Livrables — Backend :
- `core/burn_logs.py` :
  - Ajout constantes `TREASURY_LOCKED=300M`, `TEAM_LOCKED=150M`, `LOCKED_TOTAL=450M (45%)`.
  - Extension de `stats()` : `effective_circulating`, `locked_percent`, et conservation de `circulating_supply` (raw) pour compat.
- `core/triggers/burn_event.py` : nouveau trigger **manual-only**, idempotent sur `tx_signature`, calcule `burn_pct` et `burn_circulating_after`, validation base58 + garde cap.
- `core/triggers/__init__.py` : enregistre `burn_event`.
- `core/templates_repo.py` : 4 templates cyniques Prophet (2 EN, 2 FR) utilisant `{burn_amount_pretty}`, `{tx_link}`, `{burn_pct}`.
- `routers/burns.py` : router dédié (5 endpoints) :
  - Admin : `POST /api/admin/burns/disclose`, `GET /api/admin/burns`, `POST /api/admin/burns/{id}/redact`
  - Public : `GET /api/transparency/stats`, `GET /api/transparency/burns`
- `server.py` :
  - `burn_logs.ensure_indexes()` au startup.
  - Montage du router burns.

Livrables — Frontend :
- `Transparency.tsx` : `ProofOfScarcityHero` (3 métriques + tooltip Radix + disclaimer inline + feed burns avec lien Solscan).
- `CabinetTab.tsx` : `IncineratorCard` (form disclose + ledger admin + bouton redact).
- `i18n/translations.js` : section `transparencyPage.scarcity` FR + EN.

Tests & qualité :
- **33 nouveaux tests Pytest** : `tests/test_operation_incinerator.py`.
- **Pytest total : 140 tests** (107 existants + 33 nouveaux), **0 régression**.
- **TypeScript** : `tsc --noEmit` clean.
- **Lint** : ruff OK sur les nouveaux fichiers.
- **Testing agent** : Backend 97% (30/31, différence mineure 422 vs 400 sur amount=0), Frontend 100%, Intégration 100%, **0 bug critique**.

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
(identique)

---

### Phase 17.5 — Cabinet Expansion (X) ✅ **COMPLETED**
(identique)

---

### Phase 17.5b — Admin Bots Panel Updates ✅ **COMPLETED**
(identique)

---

### Phase 17.5c — Pre‑Mint Blockers ✅ **COMPLETED**
(identique)

---

### Phase 17.6 — **Operation Incinerator (Burn Transparency Layer)** ✅ **COMPLETED (P0)**
Objectif : enregistrer les burns (auditables), alimenter `/transparency` avec une preuve de rareté et déclencher des annonces Prophet (X/TG) **avec un calcul de circulating supply mathématiquement honnête**.

#### A) Backend — Data + triggers + routes ✅
1) **Index bootstrap**
- `burn_logs.ensure_indexes()` branché au startup (`backend/server.py`).

2) **`core/burn_logs.stats()` — Real Circulating Supply “honest”**
- Ajout constantes `TREASURY_LOCKED`, `TEAM_LOCKED`, `LOCKED_TOTAL`.
- Ajout `effective_circulating = initial - burned - locked_total` + `locked_percent`.
- Compat conservée : `circulating_supply = initial - burned`.

3) **Trigger Propaganda : `burn_event` (manual-only)**
- Trigger sur le pattern `founder_buy`.
- Idempotent sur `tx_signature`.
- Payload + champs dérivés : `burn_pct`, `burn_circulating_after`, formats pretty.

4) **Templates Prophet cyniques — 4 templates (2 FR, 2 EN)**
- Ajout dans `core/templates_repo.DEFAULT_TEMPLATES`.

5) **Routes burns (admin + public)**
- Router `routers/burns.py` :
  - Admin : disclose/list/redact
  - Public : stats/burn feed

6) **Montage router**
- Router monté dans `server.py`.

#### B) Frontend — Transparency + Admin Cabinet ✅
1) **/transparency : section “Proof of Scarcity”**
- `ProofOfScarcityHero` rendu juste après le Hero.
- Fetch : `GET /api/transparency/stats` + `GET /api/transparency/burns?limit=5`.
- 3 cards : Initial / Total Burned / Real Circulating.
- Tooltip Radix + disclaimer inline (bilingue via i18n).
- Feed burns (liens Solscan).

2) **i18n**
- Ajout clés `transparencyPage.scarcity.*` (FR + EN).

3) **Admin /propaganda → CabinetTab**
- `IncineratorCard` : disclose form + ledger + redact.

#### C) Tests & validation ✅
1) **Pytest**
- Ajout `tests/test_operation_incinerator.py` (33 tests).
- Suite globale : **140 tests**.

2) **TypeScript**
- `tsc --noEmit` : 0 erreurs.

3) **Testing agent**
- Backend 97% (diff mineure 422 vs 400 sur amount=0), Frontend 100%, Intégration 100%.

---

### Phase 15 — **Brain Connect & Treasury Architecture (MiCA) — NEXT (bloqué)**
Objectif : connecter l’indexation on-chain (Helius) au lore (Propaganda Engine) **sans logique de trading**, publier une politique publique de trésorerie conforme MiCA, et ajouter l’outillage admin de disclosure + tokenomics tracker.
- **Dépendances** : mint `$DEEPOTUS` + pool address DEX + passage Helius en mode live.
- **Doc ops** : `/app/docs/HELIUS_POST_DEPLOY.md`.

---

## 3) Next Actions

### Priorité immédiate (P0) — Post‑merge / déploiement
- ✅ Sprint 17.6 est livré et testé.
- Actions opérateur (prod) :
  1. Merge/push sur `main`.
  2. Redéployer Render (backend) + Vercel (frontend).
  3. Smoke test rapide :
     - `/transparency` → Proof of Scarcity visible + tooltip + disclaimer
     - `/api/transparency/stats` → `effective_circulating` correct
     - `/admin/propaganda` → onglet Cabinet → disclose burn (announce toggle ON/OFF)

### P1 — Exploitation Propaganda Engine (post‑déploiement)
- Vérifier la policy `burn_event` (approval vs auto) selon l’opération.
- Confirmer que la disclosure “announce” alimente bien la queue (X/TG).
- Vérifier `panic` / rate-limits / audit.

### P3 — Helius live post-mint
- Suivre `/app/docs/HELIUS_POST_DEPLOY.md`.

### P4 — Extension Playwright (optionnel)
- Ajouter smoke `/transparency` (Proof of Scarcity).

---

## 4) Success Criteria
- Site prod stable sur deepotus.xyz.
- Cabinet Vault : secrets centralisés, 2FA active, rotation possible.
- Propaganda : dispatch live contrôlé (rate limit + panic + audit) avec 0 fuite.
- Transparence : Wallet Registry public + `/transparency` dynamique et maintenable.
- Infiltration : riddles + clearance + auto-review opérables.
- UX Accréditation : `/#accreditation` ouvre le TerminalPopup DS-GATE-02 automatiquement.

### Critères spécifiques Sprint 17.6 — Operation Incinerator ✅
- `burn_logs` indexé au startup (idempotent).
- Endpoint public `/api/transparency/stats` expose :
  - `initial_supply = 1_000_000_000`
  - `total_burned`
  - `treasury_locked = 300_000_000`
  - `team_locked = 150_000_000`
  - `locked_total = 450_000_000`
  - `locked_percent = 45.0`
  - `effective_circulating = initial - burned - locked_total`
- `/transparency` affiche clairement la preuve de rareté + disclaimer/tooltip.
- Admin peut : disclose, lister, redact.
- Option “announce” crée un item de queue Propaganda via trigger `burn_event`.
- Qualité & hardening :
  - ✅ `tsc --noEmit` = 0 erreurs
  - ✅ `pytest` suite complète passe (140 tests)
  - ✅ 0 bug critique au testing_agent

---

## 5) Notes d’architecture (Phase 13–26)

**Backend**
- ✅ Propaganda : orchestrateur + triggers + queue + templates + tone engine.
- ✅ Dispatchers + worker APScheduler + routes admin + doc ops.
- ✅ Sprint 17.5 : `bootstrap_production_mode()` + `welcome_signal` + `prophet_interaction`.
- ✅ Sprint 17.5b : `/preview/push`, `/release-now`, hardening Pydantic.
- ✅ Sprint 17.5c : X OAuth1 via Authlib + DexScreener backoff.
- ✅ Sprint 17.6 : burn ledger + trigger `burn_event` + router public/admin + stats “honest circulating” + indexes au boot.

**Frontend**
- ✅ `/transparency` : Proof of Scarcity (3 métriques + tooltip/disclaimer + feed burns).
- ✅ `/admin/propaganda` → onglet `Cabinet` : `IncineratorCard` (disclose + ledger + redact).
- ✅ TS strict : `noImplicitAny`.

**DB Collections**
- `burn_logs` : collection active + indexes.
- `propaganda_templates` : templates `burn_event` seedés idempotemment.

**Sécurité**
- Mutations sensibles : admin + 2FA selon endpoints.
- Secrets dispatchers : Cabinet Vault (AES-256-GCM), pas de `.env`.
- Déploiement : garder les gates `tsc` + smoke E2E.
