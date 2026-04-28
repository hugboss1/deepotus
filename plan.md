# DEEPOTUS — Plan de finalisation TypeScript & sécurité “Cabinet Vault” **+ Propaganda Engine ΔΣ** (Sprints 6 → 13.3 + Infiltration 14.1 + Brain Connect 15.x)

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

#### Qualité code (post-review) — ✅ PASS SAFE FIXES
- ✅ Remplacement des `catch {}` silencieux par logs debug (frontend).
- ✅ Remplacement de ternaires imbriqués (Propaganda/Infiltration/CabinetVault) pour lisibilité.
- ✅ Remplacement `random` → `secrets.SystemRandom()` là où pertinent (tone_engine/templates_repo/propaganda_engine).
- ✅ Audits confirmés :
  - “missing hook deps” et “is vs ==” = faux positifs dans la codebase actuelle.
  - Pylint `E0601/E0602` : 0 undefined variables.

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
- **Sprint 15.x** : Brain Connect & Treasury Architecture (MiCA) — **NEXT**.

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
(identique)

---

### Phase 14 — **Pre-Launch Infiltration Brain (PROTOCOL ΔΣ)**
(identique)

#### Phase 14.1 (P0) — Backend + Admin UI + Public Terminal flow ✅ **COMPLETED**
(identique)

---

### Phase 15 — **Brain Connect & Treasury Architecture (MiCA) — NEXT**
Objectif : connecter l’indexation on-chain (Helius) au Lore (Propaganda Engine) **sans logique de trading**, publier une politique publique de trésorerie conforme MiCA, et ajouter l’outillage admin de disclosure.

#### Architecture confirmée (user)
- **Wallet_TEAM_VESTING (15%)** : Streamflow public, vesting **12 mois** (protéger réputation).
- **Wallet_TREASURY (30%)** : Squads multisig, politique de take-profit **transparente** pour financer projet MiCA.
- **Founder buy** : achat personnel au launch (skin in the game) + disclosure publique outillée (Propaganda approval queue).
- **Whale Watcher** : 100% *observer/narrator*, intégré aux **webhooks Helius** + Propaganda Engine (latence minimale).
- **Performance** : APScheduler isolé + **queue Mongo-backed** (résilience, pas d’impact sur requêtes users).
- **Hors scope explicite** : ❌ aucun trading/snipe/floor/wash, ❌ aucune clé privée.

---

#### Phase 15.1 (P0) — Tokenomics & Treasury Policy (docs publiques)
**Livrable**
- `/app/docs/TOKENOMICS_TREASURY_POLICY.md`

**Contenu minimum**
- Répartition supply (Treasury 30%, Team vesting 15%, Airdrops, Marketing, etc.).
- Vesting team (Streamflow) : paramètres publics (cliff/durée).
- Politique Treasury (Squads multisig) :
  - phases x5/x15/post-Raydium “green candle”
  - garde-fous : limites max/jour, pas d’actions pendant panic, logs.
  - transparence : chaque mouvement annoncé et traçable.
- “Founder disclosure protocol” : format public, wallet(s), signature tx, timing.

**Validation gate**
- Doc revue + cohérence MiCA (transparence et absence de promesses trompeuses).

---

#### Phase 15.2 (P0) — Whale Watcher Core (backend, queue + worker APScheduler)
**Objectif** : absorber des rafales d’événements whales sans ralentir FastAPI.

**DB**
- Nouvelle collection `whale_alerts` avec FSM :
  - `status`: `detected → analyzed → propaganda_proposed → notified | skipped | error`
  - champs : `buyer`, `amount_sol`, `tx_signature`, `mint`, `ts`, `tier`, `source`, `error`
  - indexes :
    - unique sur `tx_signature` (idempotence)
    - index sur `status, ts`

**Code (nouveau)**
- `core/whale_watcher.py` :
  - `enqueue_alert(buyer, amount_sol, tx_sig, mint, source)`
  - `tier_for(amount_sol)` → `T1 (5–15) / T2 (15–50) / T3 (>50)`
  - `process_pending_alerts(limit=1)` : pop atomique (findOneAndUpdate), enrichit payload, propose Propaganda item via `trigger_key="whale_buy"` (policy actuelle), marque `propaganda_proposed`.

**Intégrations existantes à étendre**
- `helius.ingest_enhanced_transactions(...)` :
  - extraire `amount_sol` (SOL dépensés par buyer) depuis `nativeTransfers` (Helius enhanced schema)
  - appeler `whale_watcher.enqueue_alert(...)` dès `amount_sol ≥ 5`.
- `core/market_analytics.current_market_snapshot()` : inclure `last_buy` (buyer/amount_sol/tx_sig) lu depuis `whale_alerts` (dernier `analyzed`), pour compatibilité trigger `whale_buy`.
- `core/triggers/whale_buy.py` : rendre le payload tier-aware (buyer_short, whale_amount, tier).

**APScheduler isolation**
- Extension `core/bot_scheduler.py` : job `whale_watcher_tick` toutes les 5s
  - `max_instances=1`, `coalesce=True`, `misfire_grace_time=30`
  - exécution dans un executor isolé (ne pas bloquer loop d’API)

**Validation gate**
- Test en démo : endpoint simulate (15.3) + vérification propagation vers `propaganda_queue`.
- Charge : injection 20 alerts simultanées → API reste réactive + queue drainée.

---

#### Phase 15.3 (P1) — Routes + Admin UI (audit + simulate)
**Routes (nouveau router : `routers/whale_watcher.py`)**
- `GET /api/admin/whale-watcher/alerts?status=&tier=&limit=`
- `POST /api/admin/whale-watcher/simulate` (crée une alerte fake)
- `GET /api/public/whale-watcher/recent?limit=10` (feed public anonymisé : tier + montant (bucket) + timestamp, **pas** de wallet)

**Admin UI**
- Option A (reco) : nouvelle page `/admin/whale-watcher` avec table (status/tier/amount/time/txsig).
- Option B : tab additionnel dans `pages/Propaganda.tsx`.

**Validation gate**
- Auth admin + 2FA : simulate (admin-only, peut exiger 2FA selon politique) ; listing admin simple.

---

#### Phase 15.4 (P2) — Public Lore Feed (landing)
**Livrable**
- Section landing “Cabinet detected” : 5 dernières whales (badge tier + montant + temps relatif).
- Polling 30s (MVP). WebSocket optionnel plus tard.

---

#### Phase 15.5 (P2) — Founder buy disclosure tool (admin + Propaganda)
**Backend**
- `POST /api/admin/founder/disclose-buy` : payload `wallet_pubkey`, `sol_amount`, `mc_usd`, `tx_signature`.
- Génère un message EN+FR via Propaganda (tone engine possible) → pousse en `approval queue`.
- Exige admin JWT + 2FA (pour éviter faux communiqués).

**Frontend**
- Bouton “Disclose buy” dans Propaganda admin (ou page dédiée).

---

## 4) Success Criteria
- Phases 1–14 : inchangé, déjà atteint.
- **Sprint 15.1** : un document public source de vérité Treasury/Tokenomics/disclosure.
- **Sprint 15.2** : Whale Watcher résilient (queue DB), idempotent, isolé, alimente Propaganda sans latence perceptible.
- **Sprint 15.3** : simulate + audit admin + feed public anonymisé.
- **Sprint 15.4/15.5** : Lore feed visible + disclosure tool opérationnel (approval queue + 2FA).

---

## 5) Notes d’architecture (Phase 13–15)

**Backend**
- ✅ Propaganda : orchestrateur + triggers + queue + templates + tone engine.
- ⏳ 13.3 : dispatchers réels + worker cron + rate limiting + onboarding.
- ✅ Infiltration Brain : riddles/clearance/sleeper cell.
- ⏳ Sprint 15 : `whale_alerts` queue + worker APScheduler isolé + routes admin/public + simulate.

**Frontend**
- ✅ `pages/Propaganda.tsx` : panel admin complet.
- ✅ `pages/Infiltration.tsx` : panel admin infiltration.
- ✅ Terminal : `TerminalPopup.tsx` + `RiddlesFlow.tsx`.
- ⏳ Sprint 15 : page admin Whale Watcher + section landing “Cabinet detected” + modal/CTA disclosure.

**DB Collections**
- Propaganda : `propaganda_templates`, `propaganda_queue`, `propaganda_events`, `propaganda_settings`, `propaganda_triggers`, `propaganda_price_snapshots`.
- Infiltration : `riddles`, `riddle_attempts` (TTL 24h), `clearance_levels`, `sleeper_cell`.
- Sprint 15 : `whale_alerts` (+ indexes), option `founder_disclosures` (audit) si nécessaire.

**Sécurité**
- Propaganda : lecture/édition templates = admin JWT ; panic/approve/reject = admin JWT + 2FA.
- Infiltration : endpoints publics rate-limit ; mutations admin = 2FA.
- Sprint 15 :
  - Whale watcher feed public **anonymisé**.
  - simulate/admin listing = admin JWT (2FA optionnel selon exposition).
  - disclosure founder = admin JWT + 2FA.
- Secrets dispatchers : Cabinet Vault (catégories `telegram`, `x_twitter`, `trading_refs`).
