# Vercel Dashboard — Pas-à-pas (changement Phase 17)

> **5 min, 2 toggles à changer.** Une seule fois.

---

## 🎯 Objectif

Désactiver les 2 overrides du dashboard qui forcent Vercel à utiliser `npm + Node 24` (ce qui casse la build CRA5 / AJV). Une fois fait, le redeploy passera.

---

## Étape 1️⃣ — Aller dans les Settings

1. Ouvre [https://vercel.com/dashboard](https://vercel.com/dashboard)
2. Clique sur ton projet **prophet-ai-memecoin** (ou le nom que tu as donné)
3. Dans la barre du haut, clique **Settings** (à droite de "Deployments")

---

## Étape 2️⃣ — Build & Development Settings

Dans la sidebar gauche, clique **Build and Deployment**.

Tu vas voir une section qui ressemble à ça :

```
┌─ Build Command ────────────────────────────┐
│  $ yarn run build                          │
│  [ Override (toggle) ]                     │
└────────────────────────────────────────────┘

┌─ Output Directory ─────────────────────────┐
│  build                                     │
│  [ Override (toggle) ]                     │
└────────────────────────────────────────────┘

┌─ Install Command ──────────────────────────┐
│  npm install --legacy-peer-deps  ❌        │
│  [✓ Override ON]   ← C'EST LE PROBLÈME     │
└────────────────────────────────────────────┘

┌─ Development Command ──────────────────────┐
│  ...                                       │
└────────────────────────────────────────────┘
```

### Action 🔧

→ Localise **Install Command**.
→ **Désactive le toggle "Override"** à droite (le passer de bleu → gris).
   *OU* alternative : laisse l'override mais remplace le contenu par :
   ```
   yarn install --frozen-lockfile
   ```

> 💡 Pourquoi ? Avec l'override désactivé, Vercel détecte automatiquement notre `yarn.lock` et utilise yarn. Notre `vercel.json` versionné dit aussi explicitement `yarn install --frozen-lockfile`.

---

## Étape 3️⃣ — Node.js Version

Dans la **même page Settings → Build and Deployment**, scrolle jusqu'à la section **Node.js Version**.

```
┌─ Node.js Version ──────────────────────────┐
│  ◯  16.x                                   │
│  ◯  18.x                                   │
│  ◯  20.x                                   │
│  ◯  22.x                                   │
│  ●  24.x  ❌  ← C'EST L'AUTRE PROBLÈME     │
└────────────────────────────────────────────┘
```

### Action 🔧

→ Sélectionne **`20.x`**.
→ Clique **Save** en bas.

> 💡 Pourquoi 20.x ? CRA 5 (`react-scripts@5.0.1`) n'est pas testé sur Node ≥ 22. Beaucoup de plugins webpack héritent d'`ajv@6` qui a des paths d'API spécifiques cassés sur Node récents. Node 20 est le LTS officiel le plus récent supporté par CRA et tous nos plugins.

---

## Étape 4️⃣ — Redeploy

1. Reviens à l'onglet **Deployments**
2. Le dernier déploiement (échoué) est en haut.
3. Clique sur les `…` à droite → **Redeploy**
4. Dans la modal, **DÉCOCHE** "Use existing Build Cache" pour cette fois (cache pollué par l'ancien échec).
5. Clique **Redeploy**.

⏱ Attendre ~80s.

---

## Étape 5️⃣ — Vérification

Dans le build log en cours, tu dois voir :

```
✓ Cloning github.com/...
✓ Restored build cache from previous deployment (...)
✓ Running "install" command: `yarn install --frozen-lockfile`...   ← yarn (pas npm)
✓ [1/4] Resolving packages...
✓ [2/4] Fetching packages...
✓ [3/4] Linking dependencies...
✓ [4/4] Building fresh packages...
✓ Done in XXs.
✓ Running "build" command: `yarn build`...
✓ Creating an optimized production build...
✓ Compiled successfully.
✓ The build folder is ready to be deployed.
✓ ✓ Build Completed in /vercel/output [...]
```

Si tu vois **`yarn install --frozen-lockfile`** ✅ → tout est bon, le déploiement va passer.

Si tu vois encore **`npm install --legacy-peer-deps`** ❌ → l'override n'a pas été désactivé. Retour à l'étape 2.

Si tu vois **`Cannot find module 'ajv/dist/compile/codegen'`** ❌ → soit Node version est encore 24, soit yarn.lock manque dans le repo. Vérifier :

```bash
cd /app/frontend
ls -la yarn.lock vercel.json .nvmrc .npmrc
```

Tous les 4 doivent exister.

---

## ❓ FAQ

**Q : Vercel me demande de re-link le projet ?**
R : Normal si tu as un nouveau token. Suis l'assistant : `cd /app/frontend && npx vercel link`.

**Q : Le build passe mais le site est blanc ?**
R : `Settings → Environment Variables` → ajouter `REACT_APP_BACKEND_URL` = ton URL Render (ex: `https://deepotus-api.onrender.com`).

**Q : Je veux voir le build log en direct ?**
R : Dans Deployments → clique sur le déploiement en cours → onglet "Building".

**Q : Comment savoir si yarn.lock est bien dans mon push ?**
R : `git ls-files frontend/yarn.lock` → doit retourner le path (sinon c'est gitignoré, ce qui causerait justement ce bug).

---

## 📦 Pour redéployer plus tard (sans modifier les settings)

Voir [`VERCEL_REDEPLOY_QUICK.md`](./VERCEL_REDEPLOY_QUICK.md) — ce sera 30 secondes de routine.
