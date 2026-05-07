# DEEPOTUS — Plan de finalisation TypeScript & sécurité “Cabinet Vault” **+ Propaganda Engine ΔΣ**
(Sprints 6 → 13.3 + Infiltration 14.x + Brain Connect 15.x + Déploiements 17 + Hardening 22.x → 24 + Sprint 23/24 + **Sprint 17.5 Cabinet Expansion** + **Sprint 17.5b Admin Bots Panel** + **Sprint 17.5c Pre‑Mint Blockers**)

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
- **Sprint 17.5 — Cabinet Expansion (X)** :
  - **Production Mode X** forcé : `dispatch_enabled=True`, `dispatch_dry_run=False`.
  - Migration idempotente au démarrage : `bootstrap_production_mode()`.
  - Vérifs X follow/mention/DM : flags activés (live), cache follow 24h.
  - **Welcome Signal** : thread quotidien à 14:00 UTC, cite 2–5 Agents accrédités avec handle X.
  - **Prophet Interaction Bot** : replies lore 1–3/h, signé `— ΔΣ`, OFF par défaut → activation admin.
  - Frontend : champ `x_handle` optionnel dans Terminal (copy lore) + nouvel onglet **Cabinet** dans `/propaganda`.
- **Sprint 17.5b — Admin Bots Panel updates** :
  - ✅ **Push to X/Telegram** depuis l’onglet Preview (Admin Bots) : endpoint `POST /api/admin/bots/preview/push` → crée **1 item par plateforme** dans `propaganda_queue` avec `policy=auto` (prise en charge par le Real Dispatcher, tick ~5s).
  - ✅ **Fix ASGI “Exception in ASGI application”** : durcissement Pydantic de `GeneratePreviewResponse` (extra ignore + defaults) + coercion défensive + fallback `502 preview_render_failed`.
  - ✅ **Release button** dual-mode :
    - kill-switch armé → release (comportement historique)
    - kill-switch OFF → `POST /api/admin/bots/release-now` force l’exécution des jobs via `APScheduler.modify_job(next_run_time=now)`.
- **Sprint 17.5c — Pre‑Mint blockers (FIXED)** :
  - ✅ **X Dispatcher TypeError** : remplacement du shim `_OAuth1Adapter` (incompatible httpx) par `authlib.integrations.httpx_client.OAuth1Auth` (hérite de `httpx.Auth`, implémente `auth_flow`). Dead code supprimé + test anti-régression.
  - ✅ **DexScreener 429** : cadence `POLL_SECONDS` 30→60 + backoff exponentiel persistant (`dex_backoff_until`, `dex_429_streak`, reset sur succès 200).
  - ✅ **Bonus** : fix de 4 TypeError “await bool” dans `core/news_repost.py` (fonction sync `_platform_creds_present()` ne doit pas être await).
  - ✅ **Deps** : `Authlib==1.7.2` ajouté à `backend/requirements.txt`.
  - ✅ **Qualité** : Pytest **101/101** + testing agent 100% backend/front (régression clean).
- **Pré-launch standby** : prêt à push sur `main` + redéployer ; Helius live toujours bloqué jusqu’au mint/pool.

#### Cabinet Vault (Sprints 12.x) — ✅ COMPLET
- Backend : AES-256-GCM + audit.
- Frontend UI : `/admin/cabinet-vault`.
- Secrets sensibles gérés via le vault (pas de fuite `.env`).

#### Propaganda Engine (Sprints 13.1–13.3.x + Activation Live) — ✅ LIVRÉ end-to-end
- Triggers/templates/queue/dispatch + worker.
- X + Telegram : dispatch réel activé.

#### Infiltration Brain (Sprint 14.1) — ✅ Backend + ✅ Admin UI + ✅ Public Terminal flow
- Riddles/clearance + UX terminal.

#### Sprint 14.2 — Infiltration Automation — ✅ BACKEND + ✅ UI ADMIN LIVRÉE
- `AutoReviewTab.tsx` monté sur `/admin/infiltration`.

#### Transparence & confiance (Wallet Registry) — ✅ LIVRÉ
- CRUD admin + mapping public.
- `/transparency` dynamique + RugCheck.

#### Sprint 22 → 24 — Hardening TypeScript & tests — ✅ COMPLET
- `noImplicitAny: true`.
- CI E2E Playwright.

#### UX Micro-sprint — Deep-link `#accreditation` — ✅ COMPLET
- Anchor `#accreditation` pointe désormais vers le **bouton d’accréditation** (Vault).
- Auto-open TerminalPopup sur `/#accreditation` et sur `hashchange`.
- Pulse CTA 2.6s.
- Playwright : `e2e/specs/accreditation-deeplink.spec.ts` (3 tests).

#### Sprint 17.5 — Cabinet Expansion — ✅ COMPLET
- **Dispatcher Unlocked / Prod Mode X** :
  - `propaganda_settings.dispatch_enabled=true`.
  - `propaganda_settings.dispatch_dry_run=false`.
  - Migration idempotente au boot `bootstrap_production_mode()` + respect des overrides opérateur (`_dry_run_explicit`).
- **Welcome Signal** (quotidien, thread déterministe sans LLM) :
  - Module `core/welcome_signal.py`.
  - Job APScheduler toutes les 30 minutes, fire à `hour_utc=14` (cooldown 23h).
  - Sélection : 5 plus récents Agents accrédités avec `x_handle`, non encore “signalés” (`welcome_signaled_at`), fenêtre 14j.
  - Dispatch : push en `propaganda_queue` policy=auto (rate-limits + panic + audit s’appliquent).
  - Marquage : `welcome_signaled_at` + `welcome_signaled_queue_id`.
  - Admin endpoints : `GET/PATCH/POST /api/admin/propaganda/welcome-signal`.
- **Prophet Interaction Bot** (replies 1–3/h, signé ΔΣ) :
  - Module `core/prophet_interaction.py`.
  - Job APScheduler hourly.
  - OFF par défaut, activation via admin.
  - Fetch tweets via X v2 (bearer), compose via Tone Engine, signature `— ΔΣ` enforced, reply via `in_reply_to_tweet_id`.
  - Audit : collection `prophet_replies` + indexes.
  - Admin endpoints : `GET/PATCH/POST /api/admin/propaganda/interaction-bot`.
- **X dispatcher** : support replies via `meta.reply_to_tweet_id` → body `reply.reply_to_tweet_id`.
- **Infiltration auto** : `verify_x_follow` live (X v2), cache 24h dans `x_follow_cache`, flags follow/mention/DM activés.
- **Frontend** :
  - TerminalPopup : champ optionnel `x_handle` (copy lore “ID de transmission publique… recensement du Cabinet”).
  - `/propaganda` : onglet **Cabinet** (Welcome Signal + Interaction Bot toggles + fire now + dry run + feed replies).
- **Qualité** :
  - `ruff` clean.
  - `pytest` : 79/79.

#### Sprint 17.5b — Admin Bots Panel Updates — ✅ COMPLET
- **Push to X/Telegram (Preview tab)** :
  - Backend : `POST /api/admin/bots/preview/push` → `dispatch_queue.propose(... policy=auto ...)` 1 item par plateforme.
  - Frontend : bouton CTA vert sous l’output preview + dialog (checkboxes X/TG + toggle EN/FR).
- **ASGI exception fix (requestID=11706258)** :
  - `GeneratePreviewResponse` : `ConfigDict(extra="ignore")` + defaults sûrs.
  - Coercion des champs (hashtags, emoji, strings, int) + `try/except` → `502 preview_render_failed` au lieu d’un crash ASGI.
- **Release button (header)** :
  - Frontend : bouton actif même quand kill-switch OFF (“Release · Run jobs now”).
  - Backend : `POST /api/admin/bots/release-now` + helper `force_run_all_now()` (APScheduler.modify_job).
- **Qualité** :
  - `pytest` : **90/90**.
  - `tsc --noEmit` : clean.
  - Testing agent : **100%** (backend + frontend).

#### Sprint 17.5c — Pre‑Mint Blockers — ✅ COMPLET
- **Bug 1 (X dispatcher TypeError)** :
  - `core/dispatchers/x.py` : OAuth 1.0a via `authlib.integrations.httpx_client.OAuth1Auth`.
  - Suppression du shim `_OAuth1Adapter` + stub PreparedRequest.
  - Test anti-régression : s’assure que le dispatcher passe un `httpx.Auth` natif et que les classes mortes n’existent plus.
- **Bug 2 (DexScreener 429)** :
  - `dexscreener.POLL_SECONDS` : 60s.
  - Backoff exponentiel : 60→180→300→600→1200→1800s (cap 30 min).
  - Persistance : `vault_state.dex_backoff_until`, `vault_state.dex_429_streak`, `vault_state.dex_last_429_at`.
  - Reset de streak sur fetch 200.
- **Bonus** : fix `core/news_repost.py` (ne pas `await` un bool).
- **Deps** : `Authlib==1.7.2` ajouté à `backend/requirements.txt`.
- **Qualité** : Pytest **101/101** + QA agent 100%.

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
Objectif : rendre `/#accreditation` “actionnable” (scroll + open gate) et le relier au bon CTA.
- ✅ Déplacer l’ancre `#accreditation` de **Whitelist** vers **VaultSection** (bouton “Demander un niveau d'accréditation”).
- ✅ Sur `/#accreditation` : attendre fin intro (IntersectionObserver) → scroll → auto-open TerminalPopup DS-GATE-02.
- ✅ Sur `hashchange` : re-trigger identique.
- ✅ Pulse visuel 2.6s autour du wrapper CTA (`data-cta-pulse=true`).
- ✅ Playwright : `e2e/specs/accreditation-deeplink.spec.ts` (3 tests).

---

### Phase 17.5 — Cabinet Expansion (X) ✅ **COMPLETED**
Objectif : forcer l’exécution live sur X et automatiser croissance + interaction.

1) **Production mode dispatchers / approval live**
- ✅ Default settings : `dispatch_enabled=True`, `dispatch_dry_run=False`.
- ✅ Migration idempotente `bootstrap_production_mode()` au boot.
- ✅ Respect des overrides opérateur (flag `_dry_run_explicit`).

2) **Welcome Signal (daily thread)**
- ✅ Module `core/welcome_signal.py`.
- ✅ Job scheduler 30min, fire à `hour_utc=14` + cooldown 23h.
- ✅ Dispatch policy=auto vers X.
- ✅ Marquage `welcome_signaled_at` + preview/diagnostics admin.
- ✅ Endpoints admin : GET/PATCH/POST.

3) **Prophet Interaction Bot (hourly replies)**
- ✅ Module `core/prophet_interaction.py` + indexes.
- ✅ Job scheduler hourly, OFF par défaut → activation admin.
- ✅ Fetch tweet récent original → génération Tone Engine → signature `— ΔΣ` enforced → reply via X dispatcher.
- ✅ Audit `prophet_replies` + endpoints admin.

4) **Collecte des handles X (hybride)**
- ✅ Champ `x_handle` optionnel ajouté au TerminalPopup.
- ✅ Backend accepte `x_handle`, normalise (strip @, max 15), stocke dans `access_cards` + `clearance_levels`.
- ✅ Option de vérification follow via X v2 (live), cachée via cache 24h et contrôles admin (activation “au besoin”).

5) **Admin UI**
- ✅ Nouvel onglet **Cabinet** dans `/propaganda` (toggles + fire now + dry run + feed replies).

6) **Tests**
- ✅ Pytest: 79/79 (incl. `tests/test_cabinet_expansion.py`).
- ✅ `tsc --noEmit` clean.
- ✅ QA agent : 0 bug critique.

---

### Phase 17.5b — Admin Bots Panel Updates ✅ **COMPLETED**
Objectif : rendre la console bots “actionnable” en prod (push immédiat + release jobs + zéro crash ASGI).

1) **Push to X/Telegram depuis Preview**
- ✅ Backend : `POST /api/admin/bots/preview/push` → enqueue `propaganda_queue` (policy=auto) 1 item / plateforme.
- ✅ Frontend : bouton CTA sous output + dialog choix plateformes + toggle EN/FR.

2) **Hardening Pydantic / Fix ASGI**
- ✅ `GeneratePreviewResponse` : extra ignore + defaults + coercion + fallback 502.

3) **Release (force job run)**
- ✅ Backend : `POST /api/admin/bots/release-now` + helper `force_run_all_now()`.
- ✅ Frontend : Release dual-mode (kill-switch OFF → force-run jobs).

4) **Tests**
- ✅ 11 nouveaux tests Pytest.
- ✅ Testing agent : 100%.

---

### Phase 17.5c — Pre‑Mint Blockers ✅ **COMPLETED**
Objectif : éliminer les blockers production qui empêchent la communication et l’indexation avant mint.

1) **X Dispatcher OAuth 1.0a httpx‑native**
- ✅ Remplacement `_OAuth1Adapter` → `OAuth1Auth` (Authlib) (hérite de `httpx.Auth`).
- ✅ Dead code supprimé, test anti-régression.

2) **DexScreener rate limit hardening**
- ✅ Cadence 60s.
- ✅ Backoff exponentiel persistant + reset sur succès.

3) **Bonus stability**
- ✅ Fix `news_repost.py` (ne pas `await` `_platform_creds_present()` sync).

4) **Deps + tests**
- ✅ `Authlib==1.7.2` ajouté à `requirements.txt`.
- ✅ Pytest : **101/101** + QA agent 100%.

---

### Phase 15 — **Brain Connect & Treasury Architecture (MiCA) — NEXT**
Objectif : connecter l’indexation on-chain (Helius) au lore (Propaganda Engine) **sans logique de trading**, publier une politique publique de trésorerie conforme MiCA, et ajouter l’outillage admin de disclosure + tokenomics tracker.
- **Dépendances** : mint `$DEEPOTUS` + pool address DEX + passage Helius en mode live.
- **Doc ops** : `/app/docs/HELIUS_POST_DEPLOY.md`.
- ✅ Pré-work livré : `/transparency`, registry, ops logs.
- ⛔ Bloqué : Helius live tant que mint/pool pas disponibles.

---

### Phase 17 — Déploiement Vercel/Render — ✅ **COMPLETED (prod live)**
(identique)

---

### Phase 22–24 — TypeScript Hardening & Tests — ✅ **COMPLETED**
(identique)

---

## 3) Next Actions

### Priorité immédiate (P0) — Push main + redéploiement
- ✅ Sprint 17.5 + ✅ Sprint 17.5b + ✅ Sprint 17.5c prêts.
- **Action utilisateur** : push sur `main` + redéploiement Render/Vercel.
- Après déploiement (checklist rapide) :
  1. Vérifier logs Render backend (Mongo, vault unlock, scheduler jobs, pas de TypeError OAuth).
  2. AdminBots → Preview → Generate → **Push to X/Telegram** (création d’items en queue + dispatch live).
  3. AdminBots → **Release · Run jobs now** (force-run des jobs).
  4. Propaganda queue : approve → dispatch X (live), et replies mode (`reply_to_tweet_id`) si utilisé.
  5. DexScreener : vérifier que la boucle poll ne spam pas (60s) et que les 429 arment correctement le backoff.

### P1 — Exploitation Propaganda Engine (post-déploiement)
- Valider cadence Welcome Signal (14:00 UTC) et seuils (min 2 / max 5).
- **Interaction Bot** : laisser OFF par défaut ; activer uniquement après validation coûts/tonalité.
- Vérifier `panic` / rate-limits / audit.

### P2 — Refactors prudents (post-launch, optionnel)
- Split composants trop gros (behaviour inchangé) :
  - `TerminalPopup.tsx`
  - `Propaganda.tsx`
  - `AdminPreviewSection.tsx`
- Verrouiller via Playwright.

### P3 — Helius live post-mint
- Suivre `/app/docs/HELIUS_POST_DEPLOY.md`.
- Renseigner mint + pool dès disponibles.

### P4 — Extension Playwright
- Ajouter smoke `/transparency`.
- Ajouter smoke “Propaganda queue end-to-end” (approve → dispatch live, + verify reply mode).
- Ajouter smoke “Cabinet tab” (render + toggles require 2FA).
- Ajouter smoke “AdminBots Preview push” (generate preview → open dialog → push).

---

## 4) Success Criteria
- Site prod stable sur deepotus.xyz.
- Cabinet Vault : secrets centralisés, 2FA active, rotation possible.
- Propaganda : dispatch live contrôlé (rate limit + panic + audit) avec 0 fuite.
- Transparence : Wallet Registry public + `/transparency` dynamique et maintenable.
- Infiltration : riddles + clearance + auto-review opérables.
- UX Accréditation : `/#accreditation` ouvre le TerminalPopup DS-GATE-02 automatiquement (scroll + pulse) ; aucun ancrage résiduel dans Whitelist.
- **Cabinet Expansion (Sprint 17.5)** :
  - `dispatch_enabled=True`, `dispatch_dry_run=False` en prod.
  - Welcome Signal opérationnel (daily 14:00 UTC, cite 2–5 handles).
  - Interaction Bot prêt et activable via admin, replies signées `— ΔΣ`.
  - Champ `x_handle` collecte + stockage `clearance_levels` pour recensement.
- **Admin Bots Panel (Sprint 17.5b)** :
  - Preview push poste via Real Dispatcher (`/preview/push` → queue auto → dispatch worker).
  - Zéro crash ASGI lié aux réponses LLM partielles/surplus (`GeneratePreviewResponse` durci).
  - Bouton Release opératoire : force-run jobs via `/release-now` quand kill-switch OFF.
- **Pre‑Mint Blockers (Sprint 17.5c)** :
  - X dispatcher OAuth 1.0a compatible httpx (`OAuth1Auth`), plus aucun TypeError `_OAuth1Adapter`.
  - DexScreener : 60s + backoff persistant (plus de spam 429, dégradation contrôlée).
- Qualité & hardening :
  - ✅ `tsc --noEmit` = 0 erreurs
  - ✅ `noImplicitAny: true`
  - ✅ `pytest` backend : **101** tests passent
  - ✅ Playwright E2E : specs + CI workflow

---

## 5) Notes d’architecture (Phase 13–26)

**Backend**
- ✅ Propaganda : orchestrateur + triggers + queue + templates + tone engine.
- ✅ Dispatchers + worker APScheduler + routes admin + doc ops.
- ✅ Sprint 17.5 : `bootstrap_production_mode()` + `welcome_signal` + `prophet_interaction`.
- ✅ Sprint 17.5b :
  - `POST /api/admin/bots/preview/push` (queue auto)
  - `POST /api/admin/bots/release-now` + `force_run_all_now()`
  - hardening `GeneratePreviewResponse` contre réponses LLM partielles.
- ✅ Sprint 17.5c :
  - X OAuth1 via **Authlib OAuth1Auth** (httpx.Auth natif)
  - DexScreener : cadence 60s + backoff exponentiel persistant
  - fix `news_repost.py` (await bool)
- ✅ Retry/backoff + preflight creds + diagnostics état.
- ✅ Infiltration Brain : riddles/clearance/sleeper cell.
- ✅ Transparence : Wallet Registry CRUD + endpoint public.
- ✅ Tests : Pytest + E2E bootstrap.

**Frontend**
- ✅ Vault : `VaultSection.tsx` (CTA + TerminalPopup).
- ✅ Terminal : `TerminalPopup.tsx` (incl. `x_handle` optionnel) + `RiddlesFlow.tsx`.
- ✅ Whitelist : formulaire mailing list (désolidarisé du deep-link accréditation).
- ✅ `/transparency` dynamique.
- ✅ Admin Propaganda : onglet Cabinet (Welcome Signal + Interaction Bot).
- ✅ Admin Bots :
  - Preview → CTA **Push to X/Telegram** + dialog
  - Release dual-mode (kill-switch OFF → run jobs now)
- ✅ TS strict : `noImplicitAny: true`.

**E2E (Playwright)**
- ✅ Bootstrap : `/app/e2e/`.
- ✅ Spec deep-link : `specs/accreditation-deeplink.spec.ts`.
- ✅ CI : `.github/workflows/e2e-smoke.yml`.

**DB Collections**
- Propaganda : `propaganda_templates`, `propaganda_queue`, `propaganda_events`, `propaganda_settings`, `propaganda_triggers`, `propaganda_price_snapshots`.
- Infiltration : `riddles`, `riddle_attempts` (TTL 24h), `clearance_levels`, `sleeper_cell`, `infiltration_audit`.
- 14.2 : `x_share_submissions`, `kol_dm_drafts`.
- Sprint 17.5 : `x_follow_cache`, `prophet_replies`.
- DexScreener : champs ajoutés sur `vault_state` (`dex_backoff_until`, `dex_429_streak`, `dex_last_429_at`).
- Treasury : `treasury_operations`.
- Transparence : `wallet_registry`.
- Vault : `cabinet_vault`, `cabinet_vault_audit`, `admin_2fa`.

**Sécurité**
- Mutations sensibles (panic/toggles/approvals/fire-now) : admin + 2FA.
- Secrets dispatchers : Cabinet Vault (AES-256-GCM), pas de `.env`.
- Déploiement : garder les gates `tsc` + smoke E2E.
