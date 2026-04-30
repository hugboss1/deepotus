# Vercel Redeploy — Quick Guide

> **30 secondes pour redéployer.** À utiliser à chaque push ou changement de config.

---

## ✅ Pré-requis (une seule fois — cf. [`VERCEL_DASHBOARD_SETUP.md`](./VERCEL_DASHBOARD_SETUP.md))

Avant le premier redeploy, vérifiez que le **dashboard Vercel** a ces 3 réglages :

| Réglage | Endroit | Valeur attendue |
|---|---|---|
| **Install Command** | Settings → Build & Development Settings | `yarn install --frozen-lockfile` (ou override OFF) |
| **Node.js Version** | Settings → Build & Development Settings → Node.js Version | **`20.x`** (pas 22, pas 24) |
| **`REACT_APP_BACKEND_URL`** | Settings → Environment Variables | `https://deepotus.onrender.com` |

> ✋ Une fois que c'est OK, ne plus y toucher. Les fichiers `frontend/.nvmrc`, `frontend/.npmrc` et `frontend/vercel.json` versionnés dans le repo prennent le relais.

---

## 🚀 Routine de redeploy

### A. Automatique (recommandé — 0 effort)

Push sur la branche connectée à Vercel :

```bash
cd /app
git add -A
git commit -m "deploy: <ce que tu veux>"
git push origin main   # ou ta branche prod
```

Vercel détecte le push et redéploie automatiquement (~80s).

---

### B. Manuel via dashboard (sans git push)

1. Vercel dashboard → ton projet
2. Onglet **Deployments**
3. À droite du déploiement le plus récent : `…` → **Redeploy**

**Dans la modal** :

| Cas | Cocher `Use existing Build Cache` ? |
|---|---|
| Simple push de code | ✅ Coché — gagne ~30s |
| Changement d'ENV VAR | ⛔ **DÉCOCHER** — le cache contient l'ancien build |
| Fix d'un bug de déploiement | ⛔ **DÉCOCHER** — build propre |
| Après MAJ de `yarn.lock` | ⛔ **DÉCOCHER** — nouvelles deps |

4. Clique **Redeploy**.

---

### C. Manuel via CLI (avancé — pour CI/scripts)

```bash
# Une seule fois : login
npx vercel login

# Redeploy (du dossier frontend/)
cd /app/frontend
npx vercel --prod
```

---

## 🔍 Vérification post-deploy

### Dans le build log Vercel

```
✓ Running "install" command: `yarn install --frozen-lockfile`   ← yarn (pas npm)
✓ [1/4] Resolving packages...
✓ [2/4] Fetching packages...
✓ [3/4] Linking dependencies...
✓ [4/4] Building fresh packages...
✓ Running "build" command: `yarn build`
✓ Compiled successfully.                                         ← sans warning
✓ The build folder is ready to be deployed.
```

### Sur le site live (F12 → Network tab)

✅ Les appels API doivent pointer vers Render :
```
GET https://deepotus.onrender.com/api/prophecy   → 200
```

❌ Si tu vois :
```
GET https://undefined/api/prophecy               → DNS ERROR
```
→ Ton `REACT_APP_BACKEND_URL` n'était pas set au moment du build. Refais le redeploy en **décochant** Build Cache.

---

## ⏱ Temps moyens (référence)

| Étape | Cold | Warm (cache) |
|---|---|---|
| Install | ~30s | <5s |
| Build | ~25-30s | ~25-30s |
| Total deploy | ~80s | ~60s |

---

## 🚨 Si quelque chose casse

| Symptôme | Diagnostic | Fix |
|---|---|---|
| `undefined` dans les URLs réseau | ENV VAR pas set ou cachée par l'ancien build | Étape 1 de [`VERCEL_DASHBOARD_SETUP.md`](./VERCEL_DASHBOARD_SETUP.md) + redeploy SANS cache |
| `Cannot find module 'ajv/dist/compile/codegen'` | Settings dashboard regressed (npm + Node 24 revenus) | Re-vérifier les pré-requis |
| `error TS2304: Cannot find name 'X'` | Vraie erreur TS dans le code | `cd /app/frontend && CI=true yarn build` localement, fixer, repush |
| `Module not found: Can't resolve '...'` | Import cassé | Idem |
| Site déployé mais page blanche | API URL pointe sur preview Emergent au lieu de Render, OU erreur JS | F12 → Console, vérifier l'URL appelée et l'erreur |
| CORS error | Pas un bug Vercel — `CORS_ORIGINS` Render doit contenir l'URL Vercel | Render dashboard → env vars |

---

## 📝 Cheat sheet

```bash
# Tester le build comme Vercel le fera (en local)
cd /app/frontend
yarn install --frozen-lockfile
CI=true yarn build

# Doit afficher "Compiled successfully." en moins de 35s.
# Si OK localement → OK sur Vercel (à condition d'avoir bien fait les pré-requis).
```

---

## 📚 Références

- [`VERCEL_DASHBOARD_SETUP.md`](./VERCEL_DASHBOARD_SETUP.md) — **Setup complet du dashboard (ENV + Install + Node).** Lire en premier si premier déploiement ou si ça casse.
- [`VERCEL_DEPLOYMENT.md`](./VERCEL_DEPLOYMENT.md) — RCA technique AJV + plan B npm overrides + migration Vite future.
- `/app/frontend/vercel.json` — config Vercel versionnée (force yarn, SPA rewrites, cache headers).
- `/app/frontend/.nvmrc` — pin Node 20.
- `/app/frontend/.npmrc` — fallback si Vercel utilise npm malgré tout.
