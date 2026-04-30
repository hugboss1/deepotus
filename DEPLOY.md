# DEEPOTUS · Guide de déploiement

> **Cible** : Vercel (frontend React) + Render (backend FastAPI) + MongoDB Atlas (DB)
> **Statut au 29/04/2026** : ✅ Build prod validé (yarn build strict CI=true). Infrastructure dispatchers Telegram/X scaffold ready (cf. `docs/SPRINT_13_3_DISPATCHERS.md`).

---

## 🧱 Architecture de déploiement

```
┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
│   Vercel (static)    │ ───▶ │   Render (FastAPI)   │ ───▶ │  MongoDB Atlas       │
│   Frontend React     │      │   Backend Python     │      │  Free tier M0        │
│   ~450 kB gzipped    │      │   /api/*             │      │                      │
└──────────────────────┘      └──────────────────────┘      └──────────────────────┘
        ↓ webhooks                      ↓ webhooks
   Resend → /api/webhooks/resend   Helius → /api/webhooks/helius
```

---

## 🅰️ Frontend — Vercel

### Étape 1 : Créer un projet Vercel

1. Connecter votre repo GitHub via [vercel.com/new](https://vercel.com/new)
2. **Root Directory** → `frontend/`
3. **Framework Preset** → `Create React App`
4. **Build Command** → (laisser auto — `vercel.json` définit `yarn build`)
5. **Output Directory** → (laisser auto — `build`)
6. **Install Command** → **DÉSACTIVER l'override** (le `vercel.json` versionné fait le job)

> 📘 Setup dashboard détaillé : [`docs/VERCEL_DASHBOARD_SETUP.md`](./docs/VERCEL_DASHBOARD_SETUP.md) (3 étapes, mockups ASCII, FAQ).

### Étape 2 : Node.js Version (CRITIQUE)

Settings → Build and Deployment → **Node.js Version** → **`20.x`** (pas 22, pas 24 — CRA5 incompat).

### Étape 3 : Variables d'environnement Vercel

Dans **Settings → Environment Variables**, ajouter (Production scope) :

| Variable | Exemple | Description |
|---|---|---|
| **`REACT_APP_BACKEND_URL`** | `https://deepotus.onrender.com` | **OBLIGATOIRE.** URL publique du backend Render (sans `/api`, sans `/` final) |
| `REACT_APP_SITE_URL` | `https://deepotus.com` | Domaine final du site (SEO meta tags : og:url, canonical, twitter, JSON-LD) |
| `REACT_APP_DEEPOTUS_MINT` | `<mint Solana>` | Post-mint |
| `REACT_APP_PUMPFUN_URL` | `https://pump.fun/coin/<MINT>` | Optionnel — HowToBuy |
| `REACT_APP_RAYDIUM_URL` | `https://raydium.io/swap?...` | Optionnel — HowToBuy |
| `REACT_APP_TEAM_LOCK_URL` | `https://team.finance/...` | Optionnel — Transparency panel |
| `REACT_APP_TREASURY_LOCK_URL` | `https://...` | Optionnel — Transparency panel |

> ⚠️ **Le seul préfixe accepté par CRA5 est `REACT_APP_`.** Pas de `VITE_*` ni `NEXT_PUBLIC_*` — ils sont ignorés par le build et polluent la config.

> ℹ️ **`CI=false` n'est plus nécessaire** depuis Phase 17.B (build strict clean). Peut être laissé pour rétrocompat mais superflu.

> 🔴 Si vous voyez `undefined/api/...` dans le browser : la var n'existait pas AU BUILD. Fix = ajouter la var + redeploy **sans** Build Cache.

### Étape 4 : Custom Domain (optionnel)

1. **Settings → Domains** → ajouter `deepotus.com` (ou autre)
2. Pointer le DNS A/CNAME vers `cname.vercel-dns.com`
3. Mettre à jour `REACT_APP_SITE_URL` pour qu'il matche.
4. **Redéployer** pour que les meta tags SEO se régénèrent avec la nouvelle URL.

---

## 🅱️ Backend — Render (FastAPI)

### Étape 1 : Créer un Web Service Render

1. [render.com/dashboard](https://dashboard.render.com) → **New + → Web Service**
2. Connecter le repo GitHub
3. **Root Directory** → `backend/`
4. **Environment** → `Python 3`
5. **Build Command** :
   ```bash
   pip install -r requirements.txt
   ```
6. **Start Command** :
   ```bash
   uvicorn server:app --host 0.0.0.0 --port $PORT
   ```
7. **Instance Type** → `Free` (suffisant pour MVP, upgrade si traffic)

### Étape 2 : Variables d'environnement Render (Secrets)

Dans **Environment**, ajouter chaque variable (toutes obligatoires sauf indication) :

| Variable | Description | Source |
|---|---|---|
| `MONGO_URL` | URI MongoDB Atlas (`mongodb+srv://...`) | Atlas → Connect → Drivers |
| `DB_NAME` | Nom de la base (ex: `deepotus_prod`) | Choix libre |
| `CORS_ORIGINS` | URLs Vercel séparés par virgule (ex: `https://deepotus.com,https://www.deepotus.com`) | Domaine Vercel (doit inclure le domaine final ET les preview URLs `*.vercel.app` si vous testez les PRs) |
| `EMERGENT_LLM_KEY` | Clé universelle Emergent (texte + image) | Profile → Universal Key sur Emergent |
| `ADMIN_PASSWORD` | Mot de passe admin (default: `deepotus2026`) | Choisir un fort |
| `JWT_SECRET` | Auto-généré au 1er démarrage si absent | Optionnel |
| `RESEND_API_KEY` | Clé API Resend pour emails | resend.com |
| `SENDER_EMAIL` | Email d'expédition validé Resend | Ex: `noreply@deepotus.com` |
| `RESEND_WEBHOOK_SECRET` | Secret webhook Resend (svix) | Resend dashboard |
| `PUBLIC_BASE_URL` | URL Vercel finale (ex: `https://deepotus.com`) | Votre domaine |
| `HELIUS_API_KEY` | Clé Helius pour Solana on-chain | dashboard.helius.dev |
| `HELIUS_WEBHOOK_AUTH` | Secret webhook Helius (header Authorization) | Choisir un fort |
| `DEEPOTUS_LAUNCH_ISO` | Date launch ISO (ex: `2026-07-04T17:00:00Z`) | À définir |
| `SECRETS_KEK_KEY` | Fernet AES-128 key pour chiffrer les LLM keys customs | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |

> ⚠️ **`emergentintegrations` sur Render** : le package est distribué via un extra-index Cloudfront privé, pas via PyPI public. Si le build Render échoue avec `No matching distribution found for emergentintegrations`, deux options :
>
> 1. **Recommandé (prod)** : fournir des clés natives `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` et laisser `llm_compat.py` basculer en **Mode B** (SDKs natifs — aucune dép sur la lib Emergent).
> 2. **Alternatif** : ajouter à la config Render → Environment → `PIP_EXTRA_INDEX_URL=https://d33sy5i8bnduwe.cloudfront.net/simple/` puis pinner `emergentintegrations==0.1.0` dans `requirements.txt`. Garde `EMERGENT_LLM_KEY` comme passthrough universel.
>
> Détails : [`docs/RENDER_DEPLOYMENT.md`](./docs/RENDER_DEPLOYMENT.md).

### Étape 3 : Webhooks externes

Une fois le backend déployé, configurer côté providers :

| Provider | URL webhook | Header / Auth |
|---|---|---|
| **Resend** | `https://deepotus-api.onrender.com/api/webhooks/resend` | Svix signature (auto) |
| **Helius** | `https://deepotus-api.onrender.com/api/webhooks/helius` | Header `Authorization: <HELIUS_WEBHOOK_AUTH>` |

---

## 🍃 MongoDB Atlas

1. Créer un cluster **Free Tier M0** sur [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. **Database Access** → créer un utilisateur (ex: `deepotus_app` avec read/write)
3. **Network Access** → **0.0.0.0/0** (Render IPs ne sont pas fixes en free tier)
4. **Connect → Drivers** → copier l'URI `mongodb+srv://...` → l'utiliser comme `MONGO_URL` côté Render
5. Index automatiques : créés au démarrage via `on_startup` (whitelist.email, blacklist.email, chat_logs.created_at, etc.)

---

## ✅ Checklist pré-déploiement

### Frontend
- [x] `yarn build` passe sans warnings (vérifié 26/04/2026)
- [x] `index.html` paramétré via `%REACT_APP_SITE_URL%` (12 substitutions)
- [x] Bundle JS = 408 kB gzipped (sain)
- [x] `tsc --noEmit` exit 0
- [ ] DNS pointé vers Vercel
- [ ] Custom domain configuré

### Backend
- [x] Routes API préfixées `/api/*`
- [x] CORS configurable via `CORS_ORIGINS`
- [x] Backend bind `0.0.0.0:$PORT` (compatible Render)
- [x] Mongo indexes créés au startup
- [x] Bots scheduler en kill-switch ON par défaut (sécurité)
- [ ] MongoDB Atlas configuré
- [ ] Toutes les env vars renseignées sur Render
- [ ] Webhooks Resend & Helius configurés

### Post-déploiement
- [ ] Tester `/admin` login avec le nouveau `ADMIN_PASSWORD`
- [ ] Vérifier `/api/stats` répond depuis le frontend Vercel
- [ ] Activer 2FA admin pour la production (`/admin` → Sessions tab → Enable 2FA)
- [ ] Activer les bots Telegram/X **uniquement** quand les credentials sont fournis (via `/admin/bots` config tab)

---

## 🛠️ Commandes utiles

```bash
# Build prod local pour validation
cd frontend && yarn build

# Test du bundle prod localement
cd frontend && yarn global add serve && serve -s build

# Backend prod simulation locale
cd backend && uvicorn server:app --host 0.0.0.0 --port 8001

# Générer un JWT_SECRET fort
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# Générer une SECRETS_KEK_KEY (Fernet)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## ⚠️ Notes importantes

1. **Helius mode démo** : par défaut le backend utilise un mint démo. Pour passer en réel post-launch Pump.fun, mettre à jour via l'admin `/admin/vault → Helius section → Save config + Register webhook`.

2. **Propaganda Dispatchers (Telegram/X)** : scaffold ready (Sprint 13.3). **Restent en dry-run par défaut** (`dispatch_enabled=False`, `dispatch_dry_run=True` dans `propaganda_settings`). Pour passer en live : voir [`docs/SPRINT_13_3_DISPATCHERS.md`](./docs/SPRINT_13_3_DISPATCHERS.md) — credentials à vaulter dans `telegram/*` et `x_twitter/*`.

3. **Resend SENDER_EMAIL** : doit être un email d'un domaine vérifié dans Resend (ou utiliser `onboarding@resend.dev` pour test). Le DNS du domaine final doit avoir les enregistrements SPF/DKIM Resend pour la délivrabilité.

4. **Render free tier** : le service s'endort après 15 min d'inactivité. Premier appel après pause = ~30s de cold start. Pour production réelle, upgrade vers `Starter` ($7/mois).

5. **MongoDB Atlas Free Tier** : 512 MB. Largement suffisant pour MVP. Si croissance forte, upgrade.

6. **`emergentintegrations` sur Render** : package hosted on private Cloudfront extra-index. Si build fail avec "No matching distribution", utiliser Mode B de `llm_compat.py` (clés natives) ou configurer `PIP_EXTRA_INDEX_URL` — détails dans `docs/RENDER_DEPLOYMENT.md`.

7. **Logs** : Render fournit les logs runtime. Pour prod sérieuse, brancher Sentry (à ajouter dans `core/config.py`).

---

## 🔗 Références

- [Vercel CRA deployment](https://vercel.com/docs/frameworks/create-react-app)
- [Render Python Web Service](https://render.com/docs/deploy-fastapi)
- [MongoDB Atlas free tier](https://www.mongodb.com/cloud/atlas/register)
- [Resend webhooks](https://resend.com/docs/dashboard/webhooks/introduction)
- [Helius webhooks](https://docs.helius.dev/webhooks-and-websockets/webhooks)
