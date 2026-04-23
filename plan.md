# Landing Page $DEEPOTUS — Memecoin IA Prophète (Deep State POTUS)

## User-Validated Configuration
- **Ticker**: `$DEEPOTUS` (Deep State POTUS)
- **Language**: Bilingue FR/EN avec toggle
- **Art direction**: Hybride — haut de page institutionnel/MiCA-compliant + bas de page brutalist crypto-degen/meme + esthétique deepfake/IA.
- **LLM**: Emergent LLM key (validé)
- **Fonctionnalités interactives**: chat, prophéties, tokenomics interactifs, simulateur ROI, countdown, roadmap, FAQ, whitelist, social mockups
- **Narratif**: PROTOCOL ΔΣ (Black Op) + coffre électronique gamifié ; **GENCOIN** n’apparaît qu’au twist `/operation`

---

## Original Problem Statement (Full context preserved)

Le projet s’inscrit dans un cadre « dossier de cadrage » : $DEEPOTUS est un memecoin Solana fonctionnant comme **véhicule de trésorerie transparent** avec disclosures alignés MiCA.

### Narrative core
- IA Prophète cynique, lucide, moqueuse, annonçant récession/dépression, chaos géopolitique, fragilité des marchés.
- Repositionné comme **candidat Deep State à la présidence du Monde**.
- Inspirations: Dogecoin (viral), TURBO (co-design GPT-4), Truth Terminal/GOAT (IA acteur narratif).
- Pivot public: objectif de financement **classifié** via **PROTOCOL ΔΣ** (Black Op).
- **GENCOIN** est un twist révélé uniquement après déclassification, via `/api/operation/reveal` et la page `/operation`.
- Funnel post-déclassification : accès au “vrai coffre” derrière **Niveau 02** (carte d’accès email) sur `/classified-vault`.

### Financial parameters (must remain visible on site where applicable)
- Chain: **Solana**
- Supply: **1,000,000,000**
- Target price: **€0.0005**
- FDV: **€500,000**
- Initial LP: **€2,000** à J0 → **€10,000** à J+2 (~2M tokens injectés initialement)

> Note: l’objectif explicite (ex: €300,000 / 3 semaines) est volontairement **caché** dans le narratif public et remplacé par la mécanique classifiée du coffre.

### Tokenomics (30% Treasury scenario — final)
| Category | Allocation |
|---|---|
| Liquidity / DEX | 10–15% |
| Project / Operation Treasury (MiCA + operations) | **30%** |
| Marketing / KOL / partnerships | 10% |
| Airdrops / community | 20% |
| AI / lore reserve | 10% |
| Team / advisors (vesting) | 15–20% |

### Transaction tax
- **3%** total → **2%** Operation/compliance budget + **1%** liquidité/marketing
- Cap explicite + baisse de taxe une fois l’objectif atteint (reformulé : “quand le Coffre s’ouvre”)

### Liquidity plan
- **J0**: LP €2K symmetric (~€1K memecoin + ~€1K SOL/USDC), ~2M tokens en pool
- **J+2**: LP €2K → €10K (net +€8K)
  - ~€6K via vente contrôlée Treasury en blocs
  - ~€2K via taxes / contribution externe

### Anti-dump measures
- LP lock ou burn après renforcement J+2
- Treasury en **multisig** + **timelock** + caps de vente journaliers/hebdo
- Split des ventes
- Pas d’airdrop massif / pas de distribution KOL débloquée autour de J+2

### MiCA compliance disclosures (prominent)
- Token **hautement spéculatif**
- **Aucune promesse** de rendement
- **Pas un stablecoin**, **pas un titre financier**
- Fonction: véhicule de trésorerie transparent + structure, gouvernance, risques

### Honest success probabilities
- Taux de succès memecoin global: ~1.4%
- Estimation exécution forte: 2–3%
- Objectif atteint sur la fenêtre de lancement: ~1% (ordre de grandeur)

---

## Target audiences
- **Investisseurs sérieux**: transparence MiCA, tokenomics, risques, roadmap, vesting
- **Crypto-degens**: énergie meme, persona IA Prophète, shitpost/viral, esthétique deepfake

---

## Sections / features to build

1. **Hero** — bannière candidat présidentiel, toggle FR/EN, CTA, countdown
2. **Vault (PROTOCOL ΔΣ)** — coffre animé 6 digits + chassis IA + feed activité DexScreener + funnel Niveau 02
3. **AI Prophet Live Chat** — Emergent LLM, persona FR/EN
4. **Prophecies Feed** — punchlines auto-refresh
5. **Mission Section** — framing MiCA + structure, reframé PROTOCOL ΔΣ
6. **Interactive Tokenomics** — pie chart (Recharts)
7. **Liquidity & Treasury Transparency** — timeline J0→J+2 + anti-dump
8. **ROI Simulator** — avertissement risque
9. **Roadmap** — timeline
10. **FAQ** — MiCA, tax, treasury, vesting, risques, “pourquoi l’objectif est classifié”
11. **Whitelist / Email Capture** — MongoDB
12. **Social Mockups** — X/Twitter, Telegram, Discord
13. **Risk Disclaimer Footer** — MiCA + bilingue
14. **Language Switcher** — FR ↔ EN
15. **Operation Reveal Page (`/operation`)** — unlock quand DECLASSIFIED
16. **Classified Vault (`/classified-vault`)** — gate Niveau 02 + session token + “true vault”

---

## Tech Stack
- Backend: FastAPI + MongoDB (Motor)
- Frontend: React + Tailwind + shadcn/ui + framer-motion + recharts + lucide-react
- i18n: Context FR/EN
- Email: Resend + webhooks (Svix)
- Dex feed: DexScreener polling (off/demo/custom)
- Images: Gemini Nano Banana (gemini-3.1-flash-image-preview)
- Image processing: Pillow (PIL) + qrcode

---

## Phases

### Phase 1 — Core POC (AI Prophet LLM Persona) — LIGHT POC
- ✅ Script POC validant Emergent LLM + FR/EN + prophéties
- **Status**: ✅ COMPLETED

### Phase 2 — Full Landing Page Build
- ✅ Backend: `/api/chat`, `/api/prophecy`, `/api/whitelist`, `/api/stats`
- ✅ Frontend: landing bilingue animée
- ✅ MongoDB: `whitelist`, `chat_logs`, `counters` (+ autres)
- **Status**: ✅ COMPLETED

### Phase 3 — Testing & Polish
- ✅ End-to-end tests + correctifs
- **Status**: ✅ COMPLETED

---

## User Stories (ALL must be validated in testing)

1. Compréhension immédiate MiCA-aware + gouvernance + risques
2. Meme energy + persona Deep State POTUS
3. FR/EN switch instant
4. Chat live in-character
5. Prophéties auto-refresh
6. Tokenomics interactifs
7. Simu ROI avec avertissement
8. Countdown
9. Timeline liquidité + anti-dump
10. Whitelist email OK
11. Risk disclaimer MiCA
12. Roadmap visible
13. Probabilités de succès honnêtes
14. Social mockups
15. Admin: emails transactionnels + observabilité webhook
16. Coffre classifié progressif (stages)
17. `/operation` lock/unlock + twist
18. Coffre illustré (chassis IA)
19. Activité marché reflétée (DexScreener)
20. Admin: switch mode feed + force poll
21. Mobile: dials ancrés dans l’image
22. Illustration “Fall of Deep State” sur `/operation`
23. Terminal CRT gaslighting avant Level 02
24. Request Level 02 + réception carte d’accès email
25. Gate `/classified-vault` + token session
26. True vault: activité live + progression
27. Gate door keypad immersif (desktop/mobile)
28. Reuse VaultChassis sur true vault
29. Animation CTA DECLASSIFIED identique + lien `/operation`
30. Micro-rotations (10K tokens) + locks majeurs (100M tokens)

---

## Current Status
- Plan ✅
- Backend ✅
- Frontend ✅
- Testing ✅
- **Delivery ✅**
- **Architecture backend modulaire ✅ (Opération B terminée)**
- **Hardening code quality ✅ (Phase 17 terminée)**

---

## Phase 8 — 2FA, Heatmap, Full Export, Email Events Drill-down, Cooldown Blacklist — completed ✅
- ✅ 2FA TOTP + backup codes + enable/disable
- ✅ Heatmap activité
- ✅ Export CSV whitelist complet
- ✅ Drill-down email events
- ✅ Blacklist cooldown + auto-unblock

---

## Phase 9 — Resend Webhook Finale (Svix) + Test Emails — completed ✅
- ✅ `RESEND_WEBHOOK_SECRET` injecté
- ✅ Webhook Resend signé et vérifié
- ✅ Endpoint admin `POST /api/admin/test-email`
- ✅ Events persistés + visibles

---

## Phase 10 — PROTOCOL ΔΣ (Coffre classifié + reveal twist) — COMPLETED ✅
- ✅ Vault module + collections + endpoints
- ✅ `/operation` reveal unlocké uniquement au stage DECLASSIFIED
- ✅ Hourly tick
- ✅ Sécurité : combinaison cible jamais exposée publiquement

---

## Phase 11 — AI Vault Mockup + DexScreener Live Activity — completed ✅
- ✅ Chassis IA + overlay dials responsive
- ✅ DexScreener modes (off/demo/custom)
- ✅ Admin dex-config + dex-poll

---

## Phase 12 — Mobile Vault Fix + “Fall of Deep State” Illustration — completed ✅
- ✅ Fix responsive
- ✅ Illustration prophet_chased

---

## Phase 13 — Funnel NIVEAU 02 (Terminal + Carte d’accès + Vault réel) — COMPLETED ✅
- ✅ Terminal CRT modal
- ✅ Carte d’accès (PIL + QR) + email Resend
- ✅ `/classified-vault` gate + session

---

## Phase 14 — AI Door Gate + VaultChassis Reuse — COMPLETED ✅
- ✅ door_keypad + input ancré
- ✅ continuité UI true vault

---

## Phase 15 — Production Mechanics + DECLASSIFIED Animation Parity — COMPLETED ✅
- ✅ 100M tokens/digit + 10K micro + goal 300K€ (custom)
- ✅ DexScreener demo/custom adaptés
- ✅ CTA DECLASSIFIED sur `/classified-vault`
- ✅ Tests backend iteration_10 ✅

---

## Phase 16 — Opération B: Refactor backend monolith → routers/core — **COMPLETED ✅**

### Objectif
- Modulariser `/app/backend/server.py` (monolithe 2221 lignes) en architecture FastAPI standard sans changer aucun comportement.

### Résultat (ce qui a été fait)
**Nouveau backend modulaire**
- ✅ `/app/backend/core/`
  - `config.py` (env, DB, Resend, LLM, prompts, CORS)
  - `security.py` (JWT rotation, rate-limit, require_admin, 2FA)
  - `models.py` (schemas Pydantic)
  - `email_service.py` (welcome email)
- ✅ `/app/backend/routers/`
  - `public.py` (`/api/*` public)
  - `public_stats.py` (`/api/public/stats`)
  - `webhooks.py` (`/api/webhooks/resend`)
  - `admin.py` (`/api/admin/*` hors vault)
  - `vault.py` (public + `/api/admin/vault/*`)
  - `access_card.py` (`/api/access-card/*`)
  - `operation.py` (`/api/operation/reveal`)

**Entrypoint minimal**
- ✅ `server.py` réécrit : **2221 → 106 lignes**
  - Factory FastAPI + CORS
  - `include_router()`
  - startup/shutdown
  - lancement des boucles `hourly_tick_loop` + `dex_loop`

### Compatibilité
- ✅ URLs, payloads, codes HTTP, auth flows préservés **1:1**
- ✅ Aucun changement fonctionnel

### Testing
- ✅ Backend testing agent iteration_11 : régression confirmée
  - Vault: 20/20
  - DexScreener: 22/22
  - Admin/Public/Access-card/Operation: OK
  - Startup background loops : OK

---

## Phase 17 — Code Quality Hardening (sécurité + maintenabilité) — **COMPLETED ✅**

### Objectif
- Appliquer les correctifs **réellement nécessaires** issus du code review, sans casser l’existant.
- Éviter les gros chantiers non prioritaires (split massif de composants) : **“seulement les pires”**.

### Décisions validées
- ✅ **Admin token en localStorage** : **conservé** (menace XSS reconnue, mitigée par TTL 24h + révocation serveur)
- ✅ “Faux positifs” du tool :
  - `payload undefined` dans `core/security.py` : non modifié (pas de chemin d’exécution réel)
  - `is None` en Python : conservé (correct)
  - majority des `exhaustive-deps` : conservé (désactivation volontaire / variables stables)
- ⏳ Split des très gros composants (Admin 1064 lignes, AdminVault 616, ClassifiedVault 591) : **reporté**

### Correctifs appliqués (immédiats)
**Backend — sécurité RNG**
- ✅ `vault.py` : génération de la combinaison cible via `secrets.randbelow(10)` (helper `_secure_digit()`)
  - ℹ️ `random` conservé uniquement pour éléments cosmétiques (agent codes, digits non-lockés, variance bump horaire)
- ✅ `access_card.py` : `generate_accreditation_number()` + `_derive_display_name()` via `secrets.choice()`
  - Raison: l’accréditation est le **Bearer token** du gate `/classified-vault`

**Frontend — hygiène prod**
- ✅ Ajout `src/lib/logger.js` (dev-only info/warn/debug, error toujours actif)
- ✅ Remplacement des `console.error` dans :
  - `AdminVault.jsx` (×4)
  - `Operation.jsx` (×1)
  - `PublicStats.jsx` (×1)

**Frontend — keys stables**
- ✅ Remplacement de `key={index}` pour listes dynamiques :
  - `ProphetChat.jsx` : messages ont maintenant `id` stable + keys sur rules/examples
  - `Roadmap.jsx` : key stable pour phases + bullets
  - `Operation.jsx` : lore paragraphs key stable
  - ℹ️ Boucles décoratives immuables `Array.from({length:10})` conservées (sans risque)

### Refactors “les pires seulement” (complexité)
- ✅ `dexscreener.py` : `dex_poll_once()` décomposé
  - `_resolve_token_address` / `_compute_deltas` / `_apply_demo_ticks` / `_apply_custom_ticks`
  - `_persist_baselines` / `_persist_fetch_error`
  - Complexité ~24 → ~7, comportement identique
- ✅ `routers/admin.py` : `admin_blacklist_import()` décomposé
  - `_parse_csv_candidates` / `_normalize_email_list` / `_compute_cooldown_iso` / `_insert_blacklist_entry`
- ✅ `CombinationDial.jsx` : refactor interne
  - constants de style + `computeStageStyle()`
  - `computeDimensions(size)`
  - hooks extraits `useShuffleLoop()` + `useMicroTickFlash()`

### Testing / Evidence
- ✅ Backend testing agent iteration_12 : **40/43** tests (93%)
  - Security tests: 4/4
  - Refactored tests: 6/6
  - Admin auth: 20/20
  - Access card: 5/5
  - Unique “minor issue” : webhook unsigned → 401 (comportement correct avec secret)
- ✅ Lint backend + frontend : clean
- ✅ Sanity screenshot landing (hero OK) + absence de crash console

---

## Remaining / Optional Improvements (P1)
- (A) **Switch DexScreener custom** vers le vrai token $DEEPOTUS (mint Solana) après déploiement
  - Action: configurer `dex_mode=custom` + mint via `/admin/vault`
  - Validation: feed live cohérent + ticks basés sur volume réel

---

## Future (P2)
- (C) **Upgrade précision on-chain**
  - Remplacer l’approx DexScreener (delta/h24) par un indexer trades Solana
  - Options:
    - Helius (webhooks / enhanced transactions)
    - Solscan/Solsniffer-like APIs
    - RPC direct + parsing Raydium/Orca
  - Objectif: détection per-trade fiable (buy volume), anti-abuse, meilleure corrélation UI ↔ chain

---

## Pending Operations (memorized for later — user requested)
- ✅ **(B) Backend refactor**: TERMINÉ — monolithe `server.py` → `core/` + `routers/`
- ✅ **(Hardening)**: TERMINÉ — secrets RNG + logger + keys stables + refactor complexité
- ⏳ **(A) Switch DexScreener mode to real token**: à faire quand le mint $DEEPOTUS est déployé
- ⏳ **(C) On-chain accuracy upgrade**: indexer Solana per-trade (P2)
