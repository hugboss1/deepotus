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
  - mettre à jour `/transparency` avec un **Proof of Scarcity** conforme à la “mathematical honesty” demandée,
  - calculer et afficher la **Real/Efficient Circulating Supply** en excluant les allocations verrouillées.
- **Ops post-prod** : réduire les erreurs humaines (déploiement, secrets, webhooks) via docs exécutables, endpoints diagnostics, et tests automatisés.

> Stratégie : “migration gates” (tsc/build + smoke tests) à chaque sprint + validation API (curl/testing) avant activation en prod.

### État actuel (mise à jour)
- **PRODUCTION LIVE** : `https://www.deepotus.xyz` sur Vercel (frontend) + Render (backend).
- **TypeScript** : migration complète, `noImplicitAny: true`, `npx tsc --noEmit` : 0 erreurs.
- **Cabinet Vault** : AES-256-GCM + lecture stricte par les dispatchers.
- **Propaganda Engine** : dispatchers **X + Telegram LIVE** (réels) et branchés aux APIs, via secrets du vault.
- **Transparence MiCA** : page `/transparency` alimentée dynamiquement par le **Public Wallet Registry** (badges LOCKED/PENDING) + intégration RugCheck.
- **Tests** : backend Pytest (**101 tests**) + Playwright E2E + CI GitHub Actions.
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
- ✅ **Qualité** : Pytest **101/101** + testing agent 100% backend/front.

#### Sprint 17.6 — Operation Incinerator — 🟡 EN COURS (wiring restant)
- ✅ **Data layer** : `core/burn_logs.py` est **déjà implémenté** (record/redact/total/stats/list + validation + idempotence + indexes).
- ⛔ **Wiring manquant** : indexes au startup, routes admin/public, trigger Propaganda, templates, UI `/transparency` + admin Cabinet.
- ⚠️ **Tweak critique (Cabinet Investors)** : calcul de **Real-time circulating supply** doit exclure les locks :
  - `effective_circulating = 1_000_000_000 - total_burned - treasury_locked(300_000_000) - team_locked(150_000_000)`
  - Disclaimer/tooltip : « Supply circulante temps réel, excluant les 45 % actuellement sous multisig public / vesting locks. » (+ EN).

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

### Phase 17.6 — **Operation Incinerator (Burn Transparency Layer)** — **NEXT (P0)**
Objectif : enregistrer les burns (auditables), alimenter `/transparency` avec une preuve de rareté et déclencher des annonces Prophet (X/TG) **avec un calcul de circulating supply mathématiquement honnête**.

#### A) Backend — Data + triggers + routes
1) **Index bootstrap**
- Ajouter au startup (`backend/server.py`) :
  - `from core import burn_logs as _burn`
  - `await _burn.ensure_indexes()`

2) **Étendre `core/burn_logs.stats()` pour inclure le “Real Circulating Supply”**
- Constantes :
  - `TREASURY_LOCKED = 300_000_000`
  - `TEAM_LOCKED = 150_000_000`
  - `LOCKED_TOTAL = 450_000_000`
- Ajouter à la réponse `stats()` :
  - `treasury_locked`, `team_locked`, `locked_total`
  - `effective_circulating = max(0, INITIAL_SUPPLY - total_burned - locked_total)`
  - conserver `circulating_supply` si déjà utilisé ailleurs, mais l’UI `/transparency` doit afficher **effective_circulating**.

3) **Trigger Propaganda : `burn_event` (manual-only)**
- Créer `core/triggers/burn_event.py` sur le pattern de `founder_buy` :
  - manual-only
  - idempotent sur `tx_signature`
  - payload attendu : `burn_amount`, `tx_signature`, `tx_link`, `burned_at`, `burn_note`
  - payload dérivé utile pour templates : `burn_pct` (vs initial supply), `burn_amount_pretty`
- Enregistrer dans `core/triggers/__init__.py`.

4) **Templates Prophet (cyniques) — 4 templates (2 FR, 2 EN)**
- Ajouter dans `core/templates_repo.DEFAULT_TEMPLATES` :
  - `trigger_key="burn_event"` avec variantes FR/EN.

5) **Routes Burn (admin + public) — nouveau router dédié**
- Créer `routers/burns.py` (recommandé) ou extension ciblée d’un router existant.
- Admin :
  - `POST /api/admin/burns/disclose`
    - body : `amount`, `tx_signature`, `burned_at?`, `note?`, `language?`, `announce?` (toggle)
    - appelle `burn_logs.record_burn(...)`
    - si `announce=true` : appelle `propaganda_engine.fire(trigger_key="burn_event", manual=True, payload_override=...)`
    - renvoie : burn doc + éventuellement `queue_item_id`
  - `GET /api/admin/burns?limit=...&include_redacted=true`
  - `POST /api/admin/burns/{id}/redact` (soft-delete)
- Public :
  - `GET /api/transparency/stats`
    - renvoie `initial_supply`, `total_burned`, `treasury_locked`, `team_locked`, `locked_total`, `effective_circulating`, `burn_count`, `latest_burn`, etc.
  - `GET /api/transparency/burns?limit=...`

6) **Wiring des routers**
- Monter le router dans `server.py` (`app.include_router(burns_router.admin_router/public_router)`) en gardant la logique de tags `/api` vs `/api/admin` cohérente.

#### B) Frontend — Transparency + Admin Cabinet
1) **/transparency : section “Proof of Scarcity”**
- Ajouter un composant `ProofOfScarcityHero` (dans `Transparency.tsx` ou `components/transparency/`), rendu **juste après le Hero**.
- Fetch :
  - `GET ${BACKEND}/api/transparency/stats`
  - `GET ${BACKEND}/api/transparency/burns?limit=5`
- Affichage :
  - Initial Supply : `1,000,000,000`
  - Total Burned : dynamique
  - **Real-time / Effective Circulating** : `effective_circulating` (avec tooltip/disclaimer)
  - % burned + date du dernier burn
  - liste 3–5 burns récents avec lien Solscan.
- Disclaimer obligatoire (FR/EN) :
  - FR : « Supply circulante temps réel, excluant les 45 % actuellement sous multisig public / vesting locks. »
  - EN : « Real-time circulating supply, excluding the 45% currently under public multisig/vesting locks. »

2) **i18n**
- Ajouter clés `transparencyPage.scarcity.*` (FR + EN) : titre, labels, tooltip, empty state, last burn label.

3) **Admin /propaganda → CabinetTab : bloc “Operation Incinerator”**
- Ajouter `IncineratorCard` en bas du tab :
  - Form disclose : amount, tx_signature, burned_at optionnel, note, language, toggle `announce`
  - Submit vers `POST /api/admin/burns/disclose`
  - Liste burns récents (admin) avec bouton `Redact`.
- Respecter `getAdminToken()` et le comportement 403/2FA de la page.

#### C) Tests & validation
1) **Pytest**
- Ajouter tests unitaires `core/burn_logs.py` :
  - validation amount/signature
  - idempotence duplicate signature
  - `stats()` inclut `effective_circulating` et respecte locks.
- Ajouter tests endpoints :
  - disclose (admin)
  - list public stats/burns
  - redact
  - announce via propaganda fire (mock) si activé.

2) **TypeScript**
- `yarn tsc --noEmit` doit rester 0 erreur.

3) **Playwright (optionnel P4, mais recommandé post‑P0)**
- smoke `/transparency` : vérifier présence du bloc “Proof of Scarcity” + rendu des métriques.

---

### Phase 15 — **Brain Connect & Treasury Architecture (MiCA) — NEXT (bloqué)**
(identique : attente mint + pool DEX)

---

## 3) Next Actions

### Priorité immédiate (P0) — **Sprint 17.6 Operation Incinerator**
1) Backend :
- Brancher `ensure_indexes()` au startup
- Créer trigger `burn_event` + templates
- Ajouter routes admin/public
- Étendre `stats()` avec `effective_circulating` et locks (300M + 150M)

2) Frontend :
- Ajouter “Proof of Scarcity” sur `/transparency` + tooltip/disclaimer
- Ajouter `IncineratorCard` dans `/propaganda` → onglet Cabinet
- i18n FR/EN

3) Tests :
- Pytest nouveaux tests + run suite complète
- `tsc --noEmit` + build frontend

### P1 — Exploitation Propaganda Engine (post-déploiement)
- Valider que `burn_event` suit la policy souhaitée (approval vs auto) selon déclenchement admin.
- Vérifier `panic` / rate-limits / audit.

### P3 — Helius live post-mint
- Suivre `/app/docs/HELIUS_POST_DEPLOY.md`.

### P4 — Extension Playwright
- Ajouter smoke `/transparency` (Proof of Scarcity).

---

## 4) Success Criteria
- Site prod stable sur deepotus.xyz.
- Cabinet Vault : secrets centralisés, 2FA active, rotation possible.
- Propaganda : dispatch live contrôlé (rate limit + panic + audit) avec 0 fuite.
- Transparence : Wallet Registry public + `/transparency` dynamique et maintenable.
- Infiltration : riddles + clearance + auto-review opérables.
- UX Accréditation : `/#accreditation` ouvre le TerminalPopup DS-GATE-02 automatiquement.

### Critères spécifiques Sprint 17.6 — Operation Incinerator
- `burn_logs` indexé au startup (pas d’insertion duplicate silencieuse).
- Endpoint public `/api/transparency/stats` expose :
  - `initial_supply = 1_000_000_000`
  - `total_burned`
  - `treasury_locked = 300_000_000`
  - `team_locked = 150_000_000`
  - `locked_total = 450_000_000`
  - `effective_circulating = initial - burned - locked_total`
- `/transparency` affiche clairement le calcul + disclaimer/tooltip.
- Admin peut : disclose, lister, redact.
- Option “announce” crée un item de queue Propaganda via trigger `burn_event`.
- Qualité & hardening :
  - ✅ `tsc --noEmit` = 0 erreurs
  - ✅ `pytest` suite complète passe

---

## 5) Notes d’architecture (Phase 13–26)

**Backend**
- ✅ Propaganda : orchestrateur + triggers + queue + templates + tone engine.
- ✅ Dispatchers + worker APScheduler + routes admin + doc ops.
- ✅ Sprint 17.5 : `bootstrap_production_mode()` + `welcome_signal` + `prophet_interaction`.
- ✅ Sprint 17.5b : `/preview/push`, `/release-now`, hardening Pydantic.
- ✅ Sprint 17.5c : X OAuth1 via Authlib + DexScreener backoff.
- 🟡 Sprint 17.6 : `core/burn_logs.py` déjà prêt ; il reste wiring routes + trigger + templates + stats locks + startup indexes.

**Frontend**
- ✅ `/transparency` page existante.
- 🟡 Sprint 17.6 : ajouter Proof of Scarcity + fetch stats/burns + tooltip/disclaimer.
- 🟡 Sprint 17.6 : ajouter IncineratorCard dans `CabinetTab.tsx`.

**DB Collections**
- Ajouter/activer : `burn_logs` (déjà défini via module) + indexes.

**Sécurité**
- Mutations sensibles : admin + 2FA selon endpoints.
- Secrets dispatchers : Cabinet Vault (AES-256-GCM), pas de `.env`.
- Déploiement : garder les gates `tsc` + smoke E2E.
