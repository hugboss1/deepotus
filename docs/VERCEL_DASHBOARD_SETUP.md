# Vercel Dashboard — Setup complet (3 étapes : ENV → Install → Node)

> **5–7 min, 3 sections à configurer.** À faire une seule fois. Ensuite, les redeploys sont automatiques.

> 🎯 **Si ton site déployé affiche `undefined` dans les appels réseau**, c'est l'étape 1 (ENV VARS) qui est mal faite. Tout le reste est cosmétique à côté.

---

## Étape 1️⃣ — Environment Variables (LE POINT CRITIQUE)

### 🔑 La SEULE variable qui compte

Le frontend est un projet **Create React App 5** (`react-scripts@5.0.1`).
Le préfixe accepté par CRA est **`REACT_APP_`**, point final.

- ❌ `VITE_*` → inutile (pas de Vite)
- ❌ `NEXT_PUBLIC_*` → inutile (pas de Next.js)
- ✅ **`REACT_APP_*`** → le SEUL qui fonctionne

### Variables à créer (dashboard Vercel → Settings → Environment Variables)

| Variable | Valeur d'exemple | Scope | Requise ? |
|---|---|---|---|
| **`REACT_APP_BACKEND_URL`** | `https://deepotus.onrender.com` | Production (+ Preview) | ✅ **OUI — sinon undefined** |
| `REACT_APP_SITE_URL` | `https://deepotus.com` | Production | Pour SEO meta tags (og:url, canonical) |
| `REACT_APP_DEEPOTUS_MINT` | `<mint address Solana>` | Production | Post-mint seulement |
| `REACT_APP_PUMPFUN_URL` | `https://pump.fun/coin/<MINT>` | Production | Optionnel |
| `REACT_APP_PUMPSWAP_URL` | `https://swap.pump.fun/?...` | Production | Optionnel |
| `REACT_APP_TEAM_LOCK_URL` | `https://team.finance/...` | Production | Optionnel |
| `REACT_APP_TREASURY_LOCK_URL` | `https://...` | Production | Optionnel |

### ⛔ Variables à NE PAS créer

Si vous voyez ces vars dans votre dashboard, **supprimez-les** (elles ne servent à rien et polluent la config) :

```
❌ NEXT_PUBLIC_BACKEND_URL      ← Next.js prefix, on n'utilise pas Next
❌ VITE_BACKEND_URL             ← Vite prefix, on n'utilise pas Vite
❌ VITE_API_URL                 ← idem
❌ NEXT_PUBLIC_API_URL          ← idem
❌ CI = false                   ← Plus nécessaire depuis Phase 17.B
                                  (build strict passe sans warning)
```

### 🔴 Pourquoi `undefined` dans le browser ?

Dans le code frontend, on a :
```js
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
```

CRA remplace `process.env.REACT_APP_*` au moment du **build** (pas du runtime).
Si la variable n'existait pas au moment du build, le code compilé contient :
```js
const BACKEND_URL = undefined;
```

→ d'où l'URL `undefined/api/prophecy?lang=fr` dans l'inspecteur réseau.

**Fix** : créer la variable **AVANT** le redeploy, **puis** forcer un build sans cache.

### ✅ Checklist ENV VARS

- [ ] `REACT_APP_BACKEND_URL` existe et vaut `https://deepotus.onrender.com` (sans `/api`, sans `/` à la fin)
- [ ] Scope = Production (et Preview si vous voulez tester les PRs)
- [ ] Cliqué **Save** après chaque variable
- [ ] Aucune variable `VITE_*` ou `NEXT_PUBLIC_*` dans la liste

---

## Étape 2️⃣ — Build & Development Settings

Dashboard Vercel → **Settings** → **Build and Deployment**.

```
┌─ Framework Preset ─────────────────────────┐
│  Create React App  ← doit être celui-ci    │
└────────────────────────────────────────────┘

┌─ Install Command ──────────────────────────┐
│  npm install --legacy-peer-deps  ❌        │
│  [✓ Override ON]  ← LE PROBLÈME ICI        │
└────────────────────────────────────────────┘
```

### Action 🔧

Deux options valables :

**Option recommandée** — désactiver l'override
→ Passe le toggle "Override" à **OFF** (bleu → gris)
→ Vercel lira alors `frontend/vercel.json` qui dit `yarn install --frozen-lockfile`

**Option alternative** — corriger l'override
→ Laisse "Override" ON mais remplace la valeur par :
```
yarn install --frozen-lockfile
```

Les autres champs (**Build Command**, **Output Directory**, **Root Directory** = `frontend`) peuvent rester tels quels.

---

## Étape 3️⃣ — Node.js Version (CRITIQUE)

Dans la **même page Settings → Build and Deployment**, scrolle jusqu'à **Node.js Version**.

```
┌─ Node.js Version ──────────────────────────┐
│  ◯  16.x                                   │
│  ◯  18.x                                   │
│  ●  20.x  ✅  ← SÉLECTIONNER CELUI-CI      │
│  ◯  22.x  (non testé sur CRA5)             │
│  ◯  24.x  ❌ casse AJV + CRA5              │
└────────────────────────────────────────────┘
```

### Action 🔧

Sélectionne **`20.x`** puis **Save**.

> **Pourquoi 20 et pas 24 ?**
> CRA 5 (`react-scripts@5.0.1`) + `ajv-keywords@5` + `schema-utils@4` sont incompatibles avec Node 22+. Node 20 est le LTS officiel le plus récent que toute notre pipeline supporte.

---

## Étape 4️⃣ — Redeploy (DÉCOCHER LE CACHE)

1. Onglet **Deployments**
2. Dernier déploiement → `…` → **Redeploy**
3. Dans la modal :
   - ⛔ **DÉCOCHE** `Use existing Build Cache` (très important pour un changement d'ENV VARS — le cache contient l'ancien build avec `undefined`)
   - ✅ Clique **Redeploy**

⏱ Attendre ~80s.

---

## Étape 5️⃣ — Vérification

Dans le build log en cours, tu dois voir :

```
✓ Cloning github.com/...
✓ Running "install" command: `yarn install --frozen-lockfile`      ← yarn (pas npm)
✓ [1/4] Resolving packages...
✓ [2/4] Fetching packages...
✓ [3/4] Linking dependencies...
✓ [4/4] Building fresh packages...
✓ Running "build" command: `yarn build`
✓ Creating an optimized production build...
✓ Compiled successfully.                                             ← sans warning
✓ The build folder is ready to be deployed.
```

### Test final (sur le site live)

Ouvrir le site déployé → ouvrir l'inspecteur réseau (F12 → Network) → recharger la page.

**Doit être OK** :
```
✅  GET https://deepotus.onrender.com/api/prophecy?...  → 200
```

**Toujours KO** :
```
❌  GET https://undefined/api/prophecy?...              → DNS error
```

Si toujours KO après les 4 étapes → retourne à l'étape 1, c'est 99% du temps une ENV VAR mal nommée (vérifie qu'elle commence bien par `REACT_APP_`).

---

## 🚨 Troubleshooting

### Symptôme 1 — `undefined` dans les URLs réseau

| Cause possible | Check |
|---|---|
| Variable mal nommée | `REACT_APP_BACKEND_URL` exact ? Pas de typo ? |
| Variable ajoutée mais pas redeploy | Redeploy + **décocher** Build Cache |
| Variable mise dans "Preview" mais site déployé en "Production" | Scope = Production (ou les 3) |
| Ancien build dans le cache | Redeploy sans cache |

### Symptôme 2 — `Cannot find module 'ajv/dist/compile/codegen'`

| Cause | Fix |
|---|---|
| Install Command = `npm install ...` | Étape 2 : désactiver override OU mettre `yarn install --frozen-lockfile` |
| Node.js Version = 22+ ou 24 | Étape 3 : `20.x` |

### Symptôme 3 — Build OK mais page blanche

| Cause | Fix |
|---|---|
| Erreur JS au runtime (voir console browser) | Console F12 → vérifier l'erreur exacte |
| `REACT_APP_BACKEND_URL` pointe sur Emergent preview | Doit être l'URL **Render** prod, pas `.preview.emergentagent.com` |
| Backend Render endormi (free tier) | Attendre 30s de cold start, puis refresh |

### Symptôme 4 — CORS errors dans la console

Pas un problème Vercel, mais Render.
→ Côté Render, la variable `CORS_ORIGINS` doit contenir l'URL Vercel de prod.
Exemple : `CORS_ORIGINS=https://deepotus.com,https://www.deepotus.com,https://deepotus-<hash>.vercel.app`

---

## ❓ FAQ

**Q : Je dois ajouter les 3 variants (`VITE_`, `NEXT_PUBLIC_`, `REACT_APP_`) pour être sûr ?**
R : **NON.** Seul `REACT_APP_BACKEND_URL` est lu par le code. Ajouter les autres pollue la config et ne sert à rien.

**Q : Vercel me demande de re-link le projet ?**
R : Normal après un changement de config. Suis l'assistant : `cd /app/frontend && npx vercel link`.

**Q : Comment tester avant de push ?**
R : En local, `cd /app/frontend && yarn install --frozen-lockfile && CI=true yarn build`. Si ça passe localement, ça passera sur Vercel (à condition d'avoir bien fait les étapes 1-3).

**Q : Le build marche mais les appels API renvoient 502/504 ?**
R : C'est Render qui dort (free tier). Premier appel = 30s de cold start. Ce n'est pas un problème Vercel.

**Q : Mon env var est bonne mais ça fait toujours `undefined` ?**
R : Le build a été fait AVANT la création de la var. Redeploy **sans cache**.

---

## 📦 Pour redéployer plus tard (après les 4 étapes)

Voir [`VERCEL_REDEPLOY_QUICK.md`](./VERCEL_REDEPLOY_QUICK.md) — 30 secondes de routine.
