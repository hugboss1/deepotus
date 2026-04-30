# Vercel Deployment Guide — DEEPOTUS Frontend

> **Stack** : Create React App 5 (CRA5) + CRACO + TypeScript + Tailwind + Shadcn UI
> **Cible** : Vercel (frontend) — fixé sur le sous-dossier `frontend/`

---

## 0) TL;DR

Le frontend repose sur **CRA 5** (Create React App), une stack qui est sensible aux versions de Node et au gestionnaire de paquets. Pour un déploiement Vercel stable :

- ✅ Utiliser **Yarn 1** (`yarn install --frozen-lockfile`) — **pas npm**
- ✅ Utiliser **Node 20.x** — **pas Node 22+ ou 24+**
- ✅ Garder le `yarn.lock` versionné dans le repo (déjà présent)

Les fichiers suivants ont été ajoutés au repo pour automatiser cela :

| Fichier | Rôle |
|---|---|
| `frontend/.nvmrc` | Indique Node 20 à Vercel |
| `frontend/vercel.json` | Force `yarn install --frozen-lockfile` + `yarn build` + framework CRA + SPA rewrites + cache headers |
| `frontend/.npmrc` | Filet de sécurité (`legacy-peer-deps=true`) si Vercel retombe sur npm |

> **⚠️ Attention** : les paramètres définis dans le **dashboard Vercel** (Project Settings → Build & Development) ont **priorité** sur `vercel.json`. Vous devez donc supprimer / désactiver les overrides du dashboard décrits ci-dessous.

---

## 1) Symptôme corrigé

Sur Vercel, le build échouait avec :

```
Cannot find module 'ajv/dist/compile/codegen'
Require stack:
  - /vercel/.../node_modules/ajv-keywords/dist/definitions/typeof.js
  - /vercel/.../node_modules/schema-utils/dist/validate.js
  - /vercel/.../node_modules/terser-webpack-plugin/dist/index.js
  - /vercel/.../node_modules/react-scripts/config/webpack.config.js
```

### Cause racine

- Vercel utilisait **`npm install --legacy-peer-deps`** + Node 24.
- npm hoiste `ajv@6` à la racine de `node_modules` (CRA5 et eslint en dépendent).
- Mais `ajv-keywords@5` (peer-dep `ajv@^8.8.2`, utilisé par `schema-utils@4`) est aussi hoisté au root et tente d’importer un chemin spécifique à `ajv@8` (`ajv/dist/compile/codegen`) qui n’existe pas dans `ajv@6`.
- Le résultat : `MODULE_NOT_FOUND` au moment du build.
- **Yarn 1 résout correctement ce conflit** en nestant `ajv@8` sous `schema-utils/node_modules/`.

### Vérifié

Reproduit localement avec exactement les mêmes paramètres que Vercel :

```bash
# (sandbox /tmp)
npm install --legacy-peer-deps
npx craco build  # → Cannot find module 'ajv/dist/compile/codegen' ❌

# Avec yarn et même lockfile
yarn install --frozen-lockfile
yarn build       # → SUCCESS ✅
```

---

## 2) Configuration à appliquer **côté dashboard Vercel**

> Aller dans : **Project Settings** → **Build and Deployment**

### A. Framework Settings

| Champ | Valeur |
|---|---|
| Framework Preset | `Create React App` |
| Build Command | (laisser vide / désactiver l’override) |
| Output Directory | (laisser vide / désactiver l’override) |
| **Install Command** | **Désactiver l’override** OU mettre `yarn install --frozen-lockfile` |
| Development Command | (laisser vide) |

> **Important** : le toggle « Override » à droite de **Install Command** doit être **OFF**, ou alors la valeur doit être `yarn install --frozen-lockfile`. Si vous laissez `npm install --legacy-peer-deps`, le build échouera.

### B. Root Directory

| Champ | Valeur |
|---|---|
| Root Directory | `frontend` ✅ |
| Include files outside the root directory | `Enabled` (déjà OK) |

### C. Runtime Settings (CRITIQUE)

| Champ | Avant | Après |
|---|---|---|
| **Node.js Version** | `24.x` ❌ | **`20.x`** ✅ |

> **Pourquoi Node 20 ?**
> - CRA 5 (`react-scripts@5.0.1`) n’est pas testé/maintenu sur Node ≥ 22.
> - Beaucoup de plugins webpack 5 et `fork-ts-checker-webpack-plugin` héritent d’`ajv@6` qui a des paths d’API spécifiques cassés sur Node récents.
> - Node 20 est le LTS officiel le plus récent supporté par CRA et par tous nos plugins (CRACO, Tailwind, Postcss, etc.).

### D. Environment Variables

Vérifier que les variables suivantes sont définies (sinon l'app charge mais les appels API renvoient `undefined/api/...`) :

| Variable | Exemple | Notes |
|---|---|---|
| **`REACT_APP_BACKEND_URL`** | `https://deepotus.onrender.com` | **OBLIGATOIRE.** URL Render prod, SANS `/api`, SANS `/` à la fin. |
| `REACT_APP_SITE_URL` | `https://deepotus.com` | Pour les meta tags SEO (og:url, canonical, JSON-LD). |
| `REACT_APP_DEEPOTUS_MINT` | `<mint Solana>` | Post-mint. Avant le mint, laisser vide. |
| `REACT_APP_PUMPFUN_URL` / `REACT_APP_RAYDIUM_URL` | URLs Pump.fun / Raydium | Optionnelles, utilisées dans HowToBuy. |
| `REACT_APP_TEAM_LOCK_URL` / `REACT_APP_TREASURY_LOCK_URL` | URLs d'audit wallet | Optionnelles, utilisées dans le Transparency panel. |

> ⚠️ **Le seul préfixe accepté par CRA5 est `REACT_APP_`.** Ne PAS créer de `VITE_*` ou `NEXT_PUBLIC_*` — ils sont ignorés par le build et polluent la config.

> ⚠️ **Ne jamais** mettre la valeur Emergent (`...preview.emergentagent.com`) en prod — seul l'URL Render doit être utilisée.

> ℹ️ **`CI=false` n'est plus nécessaire** depuis Phase 17.B (mode strict clean, zéro warning ESLint). On peut le laisser pour la rétrocompatibilité mais c'est superflu.

> 🔴 **`undefined` dans les appels réseau** = signifie que la variable n'existait pas AU MOMENT DU BUILD. CRA remplace `process.env.REACT_APP_*` à la compilation (pas au runtime). Fix : créer la var, PUIS redeploy **sans** Build Cache.

---

## 3) Vérification post-redeploy

Après avoir mis à jour le dashboard et déclenché un redeploy, le log Vercel doit ressembler à :

```
Running "vercel build"
Vercel CLI 51.x
Detected Yarn 1.x lockfile
Running "install" command: `yarn install --frozen-lockfile`...
[1/4] Resolving packages...
[2/4] Fetching packages...
[3/4] Linking dependencies...
[4/4] Building fresh packages...
success
Running "build" command: `yarn build`...
Compiled with warnings.
The build folder is ready to be deployed.
```

Si vous voyez encore `Running "install" command: 'npm install ...'` : retournez dans le dashboard, l’override Install Command n’a pas été désactivé.

---

## 4) Plan B (si yarn ne marche toujours pas)

Si pour une raison X/Y Vercel refuse d’utiliser yarn (peu probable, vu le `vercel.json` + `yarn.lock`), il existe un plan B avec npm + overrides :

1. Ajouter dans `frontend/package.json` :
   ```jsonc
   "overrides": {
     "ajv": "^6.12.6",
     "ajv-keywords": "^3.5.2"
   }
   ```
   > Cela force npm à hoister une version compatible.

2. Garder `Install Command` = `npm install --legacy-peer-deps`.

⚠️ Cette voie est risquée car les versions forcées peuvent casser des plugins webpack récents. **Ne l’activer qu’en dernier recours**.

---

## 5) Migration Vite (long-terme)

CRA est officiellement déprécié depuis 2023. Pour éliminer la classe entière de problèmes ajv/webpack/schema-utils, une migration vers **Vite** est planifiée comme tâche de fond (post-mint, P3).

Bénéfices :
- Build 5–10× plus rapide.
- Plus de bug ajv/CRA.
- Stack moderne et activement maintenue.

Coût estimé : ~2h de migration + tests E2E.

---

## 6) Récapitulatif des fichiers ajoutés/modifiés

```
frontend/
├── .nvmrc            # NEW — pinning Node 20
├── .npmrc            # NEW — filet de sécurité (legacy-peer-deps)
├── vercel.json       # NEW — force yarn + framework CRA + SPA rewrites
├── package.json      # UNCHANGED
├── yarn.lock         # UNCHANGED (resté valide)
└── ...
```

---

## 7) Contact / Debug

En cas de nouvelle erreur de build sur Vercel :

1. Capturer le log complet (Build Logs panel, ou télécharger via dashboard).
2. Vérifier en priorité :
   - Quelle commande `install` est exécutée ?
   - Quelle version de Node ?
   - Y a-t-il un `package-lock.json` parasite dans le repo ? *(il ne doit y avoir QUE `yarn.lock`)*
3. Reproduire localement avec :
   ```bash
   cd /app/frontend
   rm -rf node_modules build
   yarn install --frozen-lockfile
   yarn build
   ```
   → Si OK en local et KO sur Vercel = problème de config Vercel (pas de code).
