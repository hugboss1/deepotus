# Vercel Redeploy — Quick Guide

> **30 secondes pour redéployer.** À utiliser à chaque push ou changement de config.

---

## ✅ Pré-requis (une seule fois — Phase 17)

Avant le premier redeploy, vérifiez que le **dashboard Vercel** a ces 2 réglages.
Si vous voyez encore le crash AJV, c'est que ces 2 settings n'ont pas été appliqués :

| Réglage | Endroit | Valeur |
|---|---|---|
| **Install Command** | Settings → Build & Development Settings | `yarn install --frozen-lockfile` (ou désactiver l'override) |
| **Node.js Version** | Settings → Build & Development Settings → Node.js Version | **`20.x`** (pas 22, pas 24) |

> ✋ Une fois que c'est OK, ne plus y toucher. Les fichiers `frontend/.nvmrc`, `frontend/.npmrc` et `frontend/vercel.json` versionnés dans le repo prennent le relais.

---

## 🚀 Routine de redeploy (3 façons)

### A. Automatique (recommandé — 0 effort)

Push sur la branche connectée à Vercel :

```bash
cd /app
git add -A
git commit -m "deploy: <ce que tu veux>"
git push origin main   # ou ta branche prod
```

Vercel détecte le push et redéploie automatiquement (~2 min).

---

### B. Manuel via dashboard (sans git push)

1. Vercel dashboard → ton projet
2. Onglet **Deployments**
3. À droite du déploiement le plus récent : `…` → **Redeploy**
4. Coche `Use existing Build Cache` (pour gagner ~30s)
5. Clique **Redeploy**

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

Dans la **dernière minute du build log**, vous devez voir :

```
✓ Detected Yarn 1.x lockfile
✓ Running "install" command: `yarn install --frozen-lockfile`
✓ ...
✓ Running "build" command: `yarn build`
✓ Compiled successfully.
```

Si vous voyez `Running "install" command: 'npm install --legacy-peer-deps'` :
→ retournez dans `Settings` et désactivez l'override Install Command (cf. pré-requis).

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
| `Cannot find module 'ajv/dist/compile/codegen'` | Settings dashboard regressed (npm + Node 24 revenus) | Re-vérifier les pré-requis |
| `error TS2304: Cannot find name 'X'` | Vraie erreur TS dans le code | `cd /app/frontend && CI=true yarn build` localement, fixer, repush |
| `Module not found: Can't resolve '...'` | Import cassé | Idem |
| Site déployé mais blanc | API URL pas configurée | `Settings → Environment Variables` : ajouter `REACT_APP_BACKEND_URL=<URL Render>` |

---

## 📝 Cheat sheet

```bash
# Tester le build comme Vercel le fera (en local)
cd /app/frontend
yarn install --frozen-lockfile
CI=true yarn build

# Doit afficher "Compiled successfully." en moins de 35s.
# Si OK localement → OK sur Vercel (à condition que les 2 settings ci-dessus soient bons).
```

---

## 📚 Références plus détaillées

- `/app/docs/VERCEL_DEPLOYMENT.md` — guide initial complet (RCA AJV, plan B npm, migration Vite)
- `/app/frontend/vercel.json` — config Vercel versionnée
- `/app/frontend/.nvmrc` — pin Node 20
- `/app/frontend/.npmrc` — fallback si Vercel utilise npm malgré tout
