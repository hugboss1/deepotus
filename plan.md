# Sprint 20 — Écosystème, Roadmap, Financement & Paiement Stripe (plan)

## 1) Objectifs
- Ajouter une page **Écosystème** (4 produits + teaser extension JDR) bilingue FR/EN, conforme MiCA (« preuve, pas promesse », jamais nommer *le projet secret*).
- Ajouter une page **Paiement** (/paiement, /checkout) basée sur **Stripe Checkout** via playbook Emergent.
- Mettre à jour **Roadmap** (2 pistes : Produits + Projet secret) sans promesse, calendrier indicatif.
- Ajouter **Financement transparent** (marges produits + creator fees → 5 wallets) avec soldes live; lire les wallets depuis `wallet_registry` existant (placeholders si vide).
- Captures email : créer `genesis_subscribers` (nouvelle collection) et formulaires associés.

---

## 2) Étapes d’implémentation (phases)

### Phase 1 — POC “core payments” (isolation) ✅ **bloquant avant UI complète**
**User stories (POC)**
1. En tant qu’utilisateur, je peux lancer un checkout Stripe pour un produit fixe (Video Generator 65€) sans que le client fournisse le prix.
2. En tant qu’utilisateur, je reviens sur le site après paiement et je vois un statut « payé / en cours / expiré » via polling.
3. En tant que système, je reçois un webhook Stripe et j’enregistre l’événement sans double-traitement.
4. En tant que système, je crée une entrée `payment_transactions` avant redirection Stripe.
5. En tant qu’admin, je peux inspecter en DB une transaction et vérifier sa cohérence (session_id, montant, metadata).

**Tâches**
- Backend
  - Ajouter `STRIPE_API_KEY=sk_test_emergent` (env) + `load_dotenv` si nécessaire.
  - Créer `routers/payments.py` minimal:
    - `POST /api/payments/checkout/session` (body: `product_id`, `origin_url` seulement). Montant fixé côté serveur.
    - `GET /api/payments/checkout/status/{session_id}` (wrap `StripeCheckout.get_checkout_status`).
    - `POST /api/webhook/stripe` (wrap `StripeCheckout.handle_webhook`).
  - Créer collection **obligatoire** `payment_transactions` (indexes sur `session_id` unique).
  - Script de test POC (python) qui:
    - crée une session checkout
    - simule polling status (attend `open`) + valide schéma response
    - enregistre une transaction `INITIATED`
- Frontend
  - Créer une page POC `/checkout` temporaire (ou `/paiement`) avec bouton « Acheter Video Generator 65€ » → redirect.
  - Sur retour `?session_id=...` : polling status + UI states.

**Validation POC**
- `POST session` renvoie `url + session_id`, transaction créée en DB.
- Polling renvoie un statut exploitable.
- Webhook endpoint répond 2xx (même si pas “live”).

---

### Phase 2 — V1 App : pages Écosystème + Paiement + formulaires
**User stories (V1)**
1. En tant que visiteur, je peux consulter les 4 produits avec visuels cohérents et un ton premium.
2. En tant que lecteur, je peux rejoindre la Genesis list depuis la carte Roman.
3. En tant qu’acheteur, je peux pré-commander le jeu de plateau et voir le palier de prix courant + compteur Fondateur.
4. En tant qu’acheteur, je peux acheter Video Generator (65€) via Stripe et recevoir la confirmation de statut.
5. En tant que prospect B2B, je peux soumettre une demande white-label via un formulaire.

**Backend (V1)**
- Nouvelles collections:
  - `genesis_subscribers` (+ index unique email)
  - `b2b_inquiries`
  - `orders` (boardgame/videogen)
- Modules core (MVP):
  - `core/genesis.py` (CRUD minimal: create subscriber)
  - `core/orders.py` (fondateur counter atomic, tier pricing server-side)
  - `core/license_generator.py` (génère clé licence + token lien temporaire)
  - `core/stripe_checkout.py` (helper pour créer session + router glue)
- Routers:
  - `routers/ecosystem.py`
    - `POST /api/ecosystem/genesis` (email + source + locale)
    - `GET /api/ecosystem/board-game/counter` (X/500)
    - `POST /api/ecosystem/b2b-inquiry`
  - `routers/payments.py` (étendre POC):
    - support `product_id=boardgame|videogen`
    - metadata: `order_type`, `locale`, `founder_number` si boardgame
  - `routers/admin_orders.py` (MVP read-only): lister `orders`, `genesis_subscribers`, `b2b_inquiries`
- Webhook Stripe:
  - À réception `checkout.session.completed` :
    - idempotency via `event_id` + `session_id`
    - créer/mettre à jour `orders`
    - si `videogen`: générer licence + déclencher email Resend

**Frontend (V1)**
- Routes:
  - `/ecosysteme` + alias `/ecosystem`
  - `/paiement` + alias `/checkout`
- Components `components/ecosystem/`:
  - Hero + 4 product cards + teaser D&D
  - `GenesisListDialog` (email capture)
  - `B2BInquiryDialog` (form)
  - `ProductBoardGameCard` avec compteur live + palier courant
  - `ProductVideoGenCard` avec mockup `VideoGenAppMockup.tsx` (placeholder)
- Paiement:
  - `Payment.tsx` support:
    - sélection produit
    - create session → redirect
    - retour success/cancel → polling
- Images:
  - Utiliser `/public/assets/products/*.(webp|jpg)` (déjà en repo)

**Fin de phase**
- `testing_agent_v3` : 1 E2E (checkout create → redirect URL, polling visible, forms post OK).

---

### Phase 3 — Roadmap + Financement transparent (intégration dans l’existant)
**User stories (roadmap/funding)**
1. En tant que visiteur, je comprends la roadmap en 2 pistes sans promesse ni jargon financier.
2. En tant que visiteur, je vois les 5 wallets et leur rôle en FR/EN.
3. En tant que visiteur, je vois les soldes live (ou un état placeholder si non configuré).
4. En tant que visiteur, je comprends le flux “marges + fees → wallet Frais → répartition”.
5. En tant que propriétaire, je peux mettre à jour les wallets via Admin et les pages se mettent à jour automatiquement.

**Tâches**
- Modifier `components/landing/Roadmap.tsx` : 2 pistes (A Produits, B Projet secret), disclaimer « calendrier indicatif ».
- Ajouter dans `pages/Transparency.tsx` une section “Financement transparent” + `FundingFlowDiagram.tsx`.
- Résumé sur landing (section courte) renvoyant vers `/transparency`.

**Fin de phase**
- `testing_agent_v3`: navigation + i18n FR/EN parity + rendu des placeholders wallets.

---

### Phase 4 — Nav, i18n, SEO, durcissement
**User stories (polish)**
1. En tant que visiteur, je navigue via TopNav vers Écosystème et Financement.
2. En tant que visiteur, je vois OpenGraph cohérent par page.
3. En tant que visiteur, les liens Instagram/YouTube existent et affichent “bientôt” si non final.
4. En tant que visiteur, aucune page ne fait de promesse de rendement (MiCA).
5. En tant que dev, `tsc --noEmit` et Pytest passent.

**Tâches**
- `TopNav.tsx`: ajouter entrées menu.
- `translations.js`: ajouter clés `ecosystem.*`, `payment.*`, `funding.*`, `roadmap.*` FR/EN.
- SEO: title/description par page via I18nProvider + og images produits.
- Docs: update `LAUNCH_PLAYBOOK.md` (activation Stripe + orders).

---

## 3) Next Actions (immédiates)
1. Implémenter **Phase 1 POC Stripe** (backend + page minimale + script test) et valider flows.
2. Créer collections + indexes `payment_transactions`.
3. Une fois POC stable, générer les fichiers V1 en une passe (Phase 2) : pages + routers + i18n.

---

## 4) Critères de succès
- Checkout Stripe fonctionne (create session → redirect → retour → polling statut) sans prix côté client.
- Webhook traite `checkout.session.completed` de façon idempotente; `payment_transactions` et `orders` sont cohérents.
- `genesis_subscribers` et `b2b_inquiries` créés via UI; FR/EN synchronisés.
- Page Écosystème conforme au prompt (visuels roman/jeu, placeholders VideoGen mockup, liens IG/YT).
- Roadmap + Financement transparent ajoutés sans promesse et lisent `wallet_registry` (placeholders si vide).
- Tests: Pytest nouveaux endpoints + `tsc --noEmit` clean.
