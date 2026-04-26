# DEEPOTUS — Plan de finalisation TypeScript & nettoyage code (Sprint 6+)

## 1) Objectives
- Stabiliser et clarifier le code (split des gros composants, réduction de complexité) **avant** migration d’hébergement (Vercel/Render).
- Augmenter la couverture TS/TSX sur le code **applicatif** (hors Shadcn UI auto-généré), sans casser l’existant.
- Garantir une base prête pour un déploiement **Vercel (frontend) / Render (backend)** avec builds production OK.
- Préserver le comportement actuel (bots en **dry-run**, vault, ROI, intro, admin).

> Décision POC : **pas de POC d’intégration requis** (objectif = refactor/migration). On applique une stratégie **core-first** via “migration gates” (tsc/build + smoke tests) à chaque sprint.

**État actuel (après Sprint 6)**
- Couverture TS/TSX : **16 → 31** fichiers TS/TSX.
- Couverture approximative : **~38% du code applicatif** typé (en excluant les primitives Shadcn UI laissées en JSX).
- Gros fichiers restants (hors `components/ui/*`) :
  - `pages/AdminBots.jsx` **1553** (ex-1912)
  - `pages/AdminVault.jsx` **656** (ex-876)
  - `pages/PublicStats.jsx` **572**
  - `pages/HowToBuy.jsx` **407**
  - `pages/Operation.jsx` **340**
  - `components/intro/DeepStateIntro.jsx` **314**
  - `components/landing/ROISimulator.jsx` **307**

---

## 2) Implementation Steps

### Phase 1 — Sprint 6 (P0) : Core admin maintenable (splits + TS) ✅ **COMPLETED**
**User stories (min 5)**
1. En tant qu’admin, je veux des onglets admin rapides à comprendre (fichiers courts) pour modifier sans risque.
2. En tant qu’admin, je veux que le tableau Bots soit découpé par sections pour isoler les bugs.
3. En tant qu’admin, je veux conserver le login (sessionStorage) sans régression.
4. En tant qu’admin, je veux que les pages Admin/Vault/Bots restent 100% fonctionnelles après refactor.
5. En tant que développeur, je veux que `tsc --noEmit` reste vert pendant la migration.

**Travaux (réalisés)**
- ✅ `pages/Admin.jsx` → **migré en `pages/Admin.tsx`** + split en composants/sections TSX.
  - Créés :
    - `src/pages/admin/components/{StatCard,Paginator,EmailStatusBadge,ChartTooltip,EvolutionChart,AdminLogin}.tsx`
    - `src/pages/admin/sections/{WhitelistTab,ChatLogsTab,BlacklistTab,SessionsTab}.tsx`
  - Résultat : `Admin.tsx` ~**530 lignes** (orchestrateur) au lieu de 1252.
- ✅ `pages/AdminBots.jsx` : **1912 → 1553 lignes (-19%)**
  - Extraction : `src/pages/admin/sections/NewsFeedSection.tsx`.
- ✅ `pages/AdminVault.jsx` : **876 → 656 lignes (-25%)**
  - Extraction : `src/pages/admin/sections/HeliusSection.tsx`.
- ✅ `components/landing/vault/TerminalPopup.jsx` → **migré en `TerminalPopup.tsx`**
  - Ajout d’union type `TerminalPhase` + types stricts sur handlers.
- ✅ `pages/AdminEmails.jsx` → **migré en `pages/AdminEmails.tsx`**
  - Ajout types `EmailEventEntry`, `EmailEventsState`.
- ✅ Types : enrichissement de `src/types/index.ts` (types admin + extension `AccessSession`).
- ✅ Shadcn shim : ajout du module `@/components/ui/table` dans `types/shadcn-shims.d.ts`.

**Validation gate (réalisée)**
- ✅ `npx tsc --noEmit` OK
- ✅ Webpack dev: `compiled successfully · No issues found`
- ✅ Smoke test manuel (réussi) :
  - `/admin` login + dashboard + 4 tabs
  - `/admin/bots` (kill hero + tabs + NewsFeed extracted)
  - `/admin/vault` (Helius extracted + DEX section)
  - `/admin/emails` (événements visibles)
  - Landing + `/classified-vault` OK

---

### Phase 2 — Sprint 7 (P1) : Landing components (TSX) sans casser l’UX (PRIORITÉ ACTUELLE)
**User stories (min 5)**
1. En tant que visiteur, je veux que la landing charge et reste fluide (anim + sections) après migration.
2. En tant qu’utilisateur, je veux que le simulateur ROI se comporte pareil (phases, masquage, devise).
3. En tant qu’utilisateur, je veux que le vault et ses éléments UI restent identiques.
4. En tant qu’utilisateur, je veux conserver FR/EN partout.
5. En tant que développeur, je veux des composants typés pour éviter les props implicites.

**Travaux (révisés après Sprint 6)**
Batch “low-risk / high coverage” (sans changement fonctionnel) :
- Migrer `components/landing/hero/*` → `.tsx`
  - `HeroHeadline.jsx`, `HeroPoster.jsx`, `HeroCountdown.jsx`
- Migrer `components/landing/vault/*` → `.tsx` (TerminalPopup déjà fait)
  - `VaultSection.jsx`, `VaultChassis.jsx`, `CombinationDial.jsx`, `VaultActivityFeed.jsx`
- Migrer `components/landing/tokenomics/*` → `.tsx`
  - `TokenomicsChart.jsx`, `TokenomicsLegend.jsx`, `TokenomicsTaxAndBuy.jsx`
- Migrer `components/landing/roi/*` → `.tsx`
  - `PriceChart.jsx`, `DisclaimerMarquee.jsx`
- Migrer composants de page (ordre recommandé par dépendances) :
  - `TopNav.jsx`, `Hero.jsx`, `Manifesto.jsx`, `Mission.jsx`, `Roadmap.jsx`, `TransparencyTimeline.jsx`, `FAQ.jsx`, `Socials.jsx`, `Whitelist.jsx`, `Tokenomics.jsx`, `ROISimulator.jsx`, `ProphetChat.jsx`, `PropheciesFeed.jsx`, `ProphetPinnedWhisper.jsx`, `ConfirmDialog.jsx`, `ActivityHeatmap.jsx`, `BrutalTruth.jsx`

Notes :
- Shadcn UI reste en `.jsx` (hors scope) et continue d’être couvert par `shadcn-shims.d.ts`.
- Pas de refactor “design” pendant Sprint 7 : objectif = types + lisibilité.

**Validation gate**
- `npx tsc --noEmit` OK
- Webpack compile OK
- Smoke test landing : scroll complet + ROI interactions + toggles (theme/lang) + vault interactions

---

### Phase 3 — Sprint 8 (P2) : Pages applicatives (TSX)
**User stories (min 5)**
1. En tant que visiteur, je veux naviguer Landing → Operation → HowToBuy sans erreurs.
2. En tant qu’utilisateur, je veux accéder aux stats publiques et voir les graphs.
3. En tant qu’utilisateur, je veux accéder au Classified Vault (gate + authed view) sans régression.
4. En tant que développeur, je veux des pages typées pour stabiliser les routes et props.
5. En tant que QA, je veux des checks de navigation simples pour repérer les erreurs tôt.

**Travaux**
- Migrer :
  - `pages/Landing.jsx` → `.tsx`
  - `pages/Operation.jsx`, `pages/HowToBuy.jsx`, `pages/PublicStats.jsx` → `.tsx`
  - `pages/ClassifiedVault.jsx` + `pages/classified-vault/*` → `.tsx`

**Validation gate**
- `npx tsc --noEmit` OK
- Smoke test navigation complète (toutes routes principales)

---

### Phase 4 — Sprint 9 (P3) : Intro + 2FA (TSX)
**User stories (min 5)**
1. En tant que visiteur, je veux voir l’intro 14s au premier passage, puis cooldown 24h.
2. En tant que visiteur, je veux pouvoir skip et continuer sans bug.
3. En tant qu’admin, je veux ouvrir le setup 2FA et vérifier que l’UI marche.
4. En tant que développeur, je veux des types clairs sur les timers/animations.
5. En tant que QA, je veux vérifier que les effets visuels ne cassent pas le layout.

**Travaux**
- Migrer `components/intro/DeepStateIntro.jsx` → `.tsx` (refactor léger + types)
- Migrer `components/intro/{TerminalWindow, MatrixRain, GlitchOverlay}.jsx` → `.tsx`
- Migrer `components/admin/TwoFASetupDialog.jsx` → `.tsx`

**Validation gate**
- `npx tsc --noEmit` OK
- Smoke test : intro + admin 2FA dialog

---

### Phase 5 — Sprint 10 : Polish final + readiness deploy (Vercel/Render)
**User stories (min 5)**
1. En tant que mainteneur, je veux un build production stable avant déploiement.
2. En tant qu’admin, je veux que tous les écrans critiques marchent en prod build.
3. En tant que visiteur, je veux une landing sans erreurs console bloquantes.
4. En tant qu’opérateur, je veux pouvoir configurer l’URL backend via env vars.
5. En tant que QA, je veux un E2E de non-régression sur les flows principaux.

**Travaux**
- ESLint cleanup : corriger warnings réellement dangereux (éviter le churn)
- (Option) `i18n/translations.js` → `.ts` si faible risque et gain réel
- Retrait dead code rencontré pendant les sprints
- Build prod : `yarn build` / `npm run build` + correction erreurs bundler
- Vérif config env : `REACT_APP_BACKEND_URL` (frontend) + doc de déploiement Vercel/Render
- Mettre à jour `TODO_TYPESCRIPT.md`
- Lancer 1 passe E2E : Landing + Admin + Vault (+ Classified Vault)

**Validation gate**
- `npx tsc --noEmit` OK
- `npm run build` OK
- E2E green (ou bugs listés et fixés)

---

## 3) Next Actions
1. **Sprint 7** : migrer par lots les composants landing “à faible risque” (Hero/Vault/ROI/Tokenomics + composants de page).
2. Ensuite **Sprint 8** : migrer les pages (Landing/Operation/HowToBuy/PublicStats/ClassifiedVault).
3. **Sprint 9** : Intro + 2FA.
4. **Sprint 10** : build prod + doc de déploiement + E2E.

---

## 4) Success Criteria
- Sprint 6 : ✅ effectué (admin refactor + TS + smoke tests).
- Couverture TS/TSX nettement augmentée sur le code applicatif (hors Shadcn UI).
- `npx tsc --noEmit` passe à chaque sprint.
- Builds dev et prod OK (prêt Vercel/Render).
- Flows clés inchangés : landing + intro + ROI + vault + admin (bots toujours dry-run).
