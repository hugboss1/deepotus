# Sprint 20 — Écosystème, Roadmap, Financement & Paiement Stripe (plan MIS À JOUR)

## 1) Objectifs
- ✅ Ajouter une page **Écosystème** (4 produits + teaser extension JDR) bilingue FR/EN, conforme MiCA (« preuve, pas promesse », ne jamais nommer *le projet secret*).
- ✅ Ajouter une page **Paiement** (`/paiement`, `/checkout`) basée sur **Stripe Checkout** via playbook Emergent.
- ✅ Ajouter une **Roadmap 2 pistes** (Produits + Projet secret) **sans promesse** et avec un calendrier indicatif.
- ✅ Ajouter **Financement transparent** sur `/transparency#funding` (marges produits + creator fees → 5 wallets) et lecture des wallets via `wallet_registry` existant (placeholders si vide).
- ✅ Captures email : créer `genesis_subscribers` (nouvelle collection) + formulaires associés (Genesis list).
- ✅ Lead B2B : collecte via `b2b_inquiries` (persistence garantie) + notification Resend best-effort.
- ✅ Préparer la bascule **commerce live** (Stripe live keys + webhook) via documentation + étapes fail-proof.

**Statut global** : **Sprint 20 livré, intégré, compilé strict TS, validé par tests c ✅ COMPLET**.

---

## 2) Étapes d’implémentation (phases)

### Phase 1 — POC “core payments” (isolation) ✅ **COMPLETED**
**User stories (POC)**
1. ✅ En tant qu’utilisateur, je peux lancer un checkout Stripe pour un produit fixe (Video Generator 65€) sans que le client fournisse le prix.
2. ⚠️ En tant qu’utilisateur, je reviens sur le site après paiement et je vois un statut « payé / en cours / expiré » via polling.
   - **Note** : le polling (`GET /api/payments/checkout/status/{session_id}`) peut retourner **502** avec `sk_test_emergent` (limitation attendue du mode test Emergent). En prod avec clés Stripe réelles, la fonctionnalité est prévue pour fonctionner.
3. ✅ En tant que système, je reçois un webhook Stripe et j’enregistre l’événement sans double-traitement.
4. ✅ En tant que système, je crée une entrée `payment_transactions` avant redirection Stripe.
5. ✅ En tant qu’admin, je peux inspecter en DB une transaction et vérifier sa cohérence (session_id, montant, metadata).

**Tâches (réalisées)**
- Backend
  - ✅ Ajout `STRIPE_API_KEY=sk_test_emergent` (backend/.env) + intégration config.
  - ✅ Création `routers/payments.py`:
    - ✅ `POST /api/payments/checkout/session`
    - ✅ `GET /api/payments/checkout/status/{session_id}`
    - ✅ `POST /api/webhook/stripe`
    - ✅ `GET /api/payments/download/{token}` (stub pour futur streaming binaire)
  - ✅ Création collection `payment_transactions` + indexes (`session_id` unique).
  - ✅ Définition source-of-truth server-side : `PRODUCT_CATALOG` + pricing autoritatif.
- Frontend
  - ✅ Page `/paiement` V1 intégrée (plus de page POC séparée) : sélection produit + create session → redirect.

**Validation POC**
- ✅ `POST session` renvoie `url + session_id`, transaction créée en DB.
- ⚠️ Polling : attendu instable/502 en mode `sk_test_emergent`.
- ✅ Webhook endpoint répond 2xx.

---

### Phase 2 — V1 App : pages Écosystème + Paiement + formulaires ✅ **COMPLETED**
**User stories (V1)**
1. ✅ En tant que visiteur, je peux consulter les 4 produits avec visuels cohérents et un ton premium.
2. ✅ En tant que lecteur, je peux rejoindre la Genesis list depuis la carte Roman.
3. ✅ En tant qu’acheteur, je peux pré-commander le jeu de plateau et voir le palier de prix courant + compteur Fondateur.
4. ✅ En tant qu’acheteur, je peux acheter Video Generator (65€) via Stripe.
5. ✅ En tant que prospect B2B, je peux soumettre une demande white-label via un formulaire.

**Backend (V1) — réalisé**
- ✅ Nouvelles collections:
  - `genesis_subscribers` (unique via `email_hash + source`)
  - `b2b_inquiries`
  - `orders` (boardgame/videogen)
  - `payment_transactions` (ledger)
  - `counters` (boardgame counter)
- ✅ Modules core:
  - `core/genesis.py`
  - `core/orders.py` (counter atomic + idempotence sur `stripe_session_id`)
  - `core/license_generator.py` (clé licence + token 72h + email)
  - `core/stripe_checkout.py` (catalogue + tiers + réservation number + ledger)
  - `core/b2b_inquiries.py` (persistence + notification Resend best-effort)
- ✅ Routers:
  - `routers/ecosystem.py`:
    - ✅ `POST /api/ecosystem/genesis`
    - ✅ `GET /api/ecosystem/board-game/counter`
    - ✅ `POST /api/ecosystem/b2b-inquiry`
  - `routers/admin_orders.py`:
    - ✅ `GET /api/admin/ecosystem/orders`
    - ✅ `GET /api/admin/ecosystem/genesis`
    - ✅ `GET /api/admin/ecosystem/b2b`
    - ✅ `GET /api/admin/ecosystem/payments/transactions`

**Frontend (V1) — réalisé**
- ✅ Routes:
  - `/ecosysteme` + alias `/ecosystem`
  - `/paiement` + alias `/checkout`
- ✅ Assets produits optimisés :
  - `/public/assets/products/{roman-couverture, roman-pages, jeu-plateau}.{jpg,webp}`
- ✅ API helpers strict TS : `src/lib/ecosystem.ts`
- ✅ Composants :
  - `EcosystemHero`, `ProductRomanCard`, `ProductBoardGameCard`, `ProductVideoGenCard`, `ProductMobileGameCard`
  - `VideoGenAppMockup` (placeholder watermark)
  - `EcosystemBanner`
  - `GenesisListDialog`, `B2BInquiryDialog`
- ✅ `Payment.tsx` : sélection produit + create session → redirect + retour `session_id` (polling) + états UI.
- ✅ TopNav : ajout des entrées **Ecosystem** + **Funding**.

**Fin de phase**
- ✅ `yarn build` OK, TypeScript strict OK.

---

### Phase 3 — Roadmap + Financement transparent (intégration dans l’existant) ✅ **COMPLETED**
**User stories (roadmap/funding)**
1. ✅ En tant que visiteur, je comprends la roadmap en 2 pistes sans promesse ni jargon financier.
2. ✅ En tant que visiteur, je vois les 5 wallets et leur rôle en FR/EN.
3. ✅ En tant que visiteur, je vois les soldes live (ou un état placeholder si non configuré).
4. ✅ En tant que visiteur, je comprends le flux “marges + fees → wallet Frais → répartition”.
5. ✅ En tant que propriétaire, je peux mettre à jour les wallets via Admin et les pages se mettent à jour automatiquement.

**Tâches (réalisées)**
- ✅ Landing : ajout d’un composant **non destructif** `TwoTracksRoadmap` avant le `Roadmap` existant.
- ✅ Transparency : ajout `FundingFlowSection` à l’ancre **`#funding`** (narratif sources + diagramme + 5 rôles wallets).
- ✅ Données wallets : réutilise `useWalletRegistry` → propagation auto des updates admin.

---

### Phase 4 — Nav, i18n, SEO, durcissement ✅ **COMPLETED**
**User stories (polish)**
1. ✅ Navigation TopNav vers **Écosystème** et **Financement**.
2. ✅ Bilingue FR/EN synchronisé (parité des clés).
3. ✅ Liens Instagram/YouTube : placeholders + badge “Bientôt” (désactivable via constante quand comptes réels).
4. ✅ Aucun copy n’effectue de promesse de rendement (MiCA).
5. ✅ Build strict TS OK + lint backend OK.

**Tâches (réalisées)**
- ✅ `translations.js` : ajout clés `ecosystem.*`, `payment.*`, `funding.*`, `roadmapTracks.*` FR/EN.
- ✅ `TopNav.tsx` : entrées menu + funding anchor.
- ✅ Routes `App.tsx` : `/ecosysteme`, `/ecosystem`, `/paiement`, `/checkout`.

---

### Phase 5 — Documentation & Go-live commerce ✅ **COMPLETED**
- ✅ Mise à jour `LAUNCH_PLAYBOOK.md` : nouvelle section **8 · Sprint 20 — Activation Écosystème & Paiement Stripe**
  - ENV Render (`STRIPE_API_KEY`, `B2B_INQUIRY_EMAIL`)
  - commandes curl de vérification
  - endpoints admin read-only
  - bascule live keys + config webhook Stripe
  - activation Instagram/YouTube quand handles réels
  - remplacement visuels VideoGen

---

## 3) Next Actions (immédiates)
1. (Optionnel) **Brancher Stripe Live** : remplacer `STRIPE_API_KEY` par une clé live sur Render + configurer le webhook Stripe.
2. (Optionnel) **Uploader l’installeur VideoGen** (S3/stockage) et implémenter le streaming dans `GET /api/payments/download/{token}`.
3. (Optionnel) **Fournir les screenshots réels VideoGen** pour remplacer `VideoGenAppMockup`.
4. (Optionnel) **Activer les vrais liens Instagram/YouTube** : mettre `HAS_REAL_SOCIALS=true` et remplacer les URLs.
5. (À faire côté utilisateur) **Renseigner les 5 wallets** via admin (`Wallet Registry`) : la section funding/Transparency se met à jour automatiquement.

---

## 4) Critères de succès (état actuel)
- ✅ Checkout Stripe : create session → redirect (prix **server-side** non manipulable).
- ✅ Founder counter boardgame : **atomic** via Mongo `$inc`, tiers appliqués côté serveur.
- ✅ Webhook idempotent : transactions persistées, orders créés une seule fois.
- ✅ `genesis_subscribers` + `b2b_inquiries` créés via UI; FR/EN synchronisés.
- ✅ Pages `/ecosysteme`, `/paiement`, `TwoTracksRoadmap`, `/transparency#funding` conformes au prompt.
- ✅ Tests : `yarn build` OK, backend lint OK, `testing_agent_v3` itération 28 OK (aucun bug critique).
- ⚠️ Polling Stripe status peut échouer avec `sk_test_emergent` (limitation attendue) — bascule live pour validation end-to-end.
