# 🛸 $DEEPOTUS · Guide de déploiement & finition (Phases 3 → 7)

> **Document maître séquentiel.** Toutes les étapes sont liées entre elles dans l'ordre d'exécution recommandé. Les sections `🟢 NEO` sont du code que je peux implémenter, les sections `🟡 TOI` sont manuelles (création de comptes, copie de credentials, paiements). Les `⚠️ PIÈGES` listent les erreurs typiques à éviter.

---

## 📑 Table des matières

- [0. Snapshot — état actuel du projet](#0-snapshot)
- [1. Pré-requis : comptes & services à créer](#1-prerequis)
- [2. Phase 3 — Telegram content bot (aiogram)](#2-phase-3-telegram-content-bot)
- [3. Phase 4 — X / Twitter posting bot (Tweepy)](#3-phase-4-x-twitter-posting-bot)
- [4. Phase 5 — X KOL mentions listener](#4-phase-5-x-kol-listener)
- [5. Telegram TRADING bot — Maestro / BonkBot / Trojan](#5-telegram-trading-bot)
- [6. Déploiement Backend → Render](#6-deploy-backend-render)
- [7. Déploiement Frontend → Vercel](#7-deploy-frontend-vercel)
- [8. DNS Namecheap → deepotus.xyz](#8-dns-namecheap)
- [9. MongoDB Atlas — base de prod](#9-mongodb-atlas)
- [10. Resend — DKIM / SPF / domaine](#10-resend-dkim)
- [11. Helius — passage en mode prod (vrai mint)](#11-helius-prod)
- [12. Post-deploy checklist + Go-Live D-day](#12-post-deploy)
- [13. Récap : qui fait quoi, dans quel ordre](#13-recap-final)
- [14. Coûts mensuels estimés](#14-couts)

---

## <a id="0-snapshot"></a>0. Snapshot — état actuel du projet

| Module | Statut | Notes |
|---|---|---|
| Site front (Hero / Tokenomics / Vault / ROI / FAQ / How-to-Buy) | ✅ Live preview | Bilingue FR/EN, Matrix/Deep State theme |
| Admin dashboard (`/admin`, `/admin/vault`, `/admin/emails`, `/admin/bots`) | ✅ Live | JWT + 2FA |
| Helius webhook (per-trade DEX polling) | 🟡 Demo mode (BONK) | À basculer sur le vrai mint au launch — voir [§11](#11-helius-prod) |
| Resend emails (whitelist + access cards) | ✅ Live | Domaine `deepotus.xyz` à valider — voir [§10](#10-resend-dkim) |
| Phase 1 — Scheduler bots (APScheduler + kill-switch) | ✅ Implémenté | |
| Phase 2 — Prophet Studio LLM (texte + image Nano Banana) | ✅ Implémenté | Clé image séparable via `EMERGENT_IMAGE_LLM_KEY` |
| Phase 3 — Telegram content bot | ❌ À faire | [§2](#2-phase-3-telegram-content-bot) |
| Phase 4 — X posting bot | ❌ À faire | [§3](#3-phase-4-x-twitter-posting-bot) |
| Phase 5 — X KOL listener | ❌ À faire | [§4](#4-phase-5-x-kol-listener) |
| Phase 6 — Admin Dashboard UI Bots | ✅ Implémenté | Config / Preview / Jobs / Logs |
| Telegram **trading** bot | 🟡 Externe | [§5](#5-telegram-trading-bot) |
| Déploiement Vercel + Render + Atlas + Namecheap | ❌ À faire | [§6](#6-deploy-backend-render) à [§9](#9-mongodb-atlas) |

---

## <a id="1-prerequis"></a>1. Pré-requis — comptes & services à créer

> Crée tous ces comptes **avant** d'attaquer le déploiement. La plupart sont gratuits.

### 🟡 TOI — Comptes obligatoires

| # | Service | Lien direct | Coût | Pourquoi |
|---|---|---|---|---|
| 1 | **GitHub** | [github.com/signup](https://github.com/signup) | Gratuit | Héberger le code source de l'app |
| 2 | **Vercel** | [vercel.com/signup](https://vercel.com/signup) | Gratuit | Hébergement frontend React |
| 3 | **Render** | [render.com/register](https://render.com/register) | Starter $7/mo | Hébergement backend FastAPI |
| 4 | **MongoDB Atlas** | [cloud.mongodb.com/v2/register](https://cloud.mongodb.com/v2/register) | M0 Free | Base de données prod |
| 5 | **Resend** *(déjà configuré)* | [resend.com](https://resend.com) | Free 3K emails/mo | Emails transactionnels |
| 6 | **Helius** *(déjà configuré)* | [dashboard.helius.dev](https://dashboard.helius.dev) | Free 100K req/mo | Solana indexer |
| 7 | **Namecheap** *(tu as déjà deepotus.xyz)* | [namecheap.com](https://namecheap.com) | — | DNS |

### 🟡 TOI — Comptes optionnels selon les phases

| # | Service | Lien | Coût | Phase concernée |
|---|---|---|---|---|
| 8 | **Telegram BotFather** | [@BotFather](https://t.me/BotFather) sur Telegram | Gratuit | [Phase 3](#2-phase-3-telegram-content-bot) |
| 9 | **X / Twitter Developer** | [developer.x.com/en/portal/dashboard](https://developer.x.com/en/portal/dashboard) | Basic $200/mo | [Phase 4 + 5](#3-phase-4-x-twitter-posting-bot) |
| 10 | **BonkBot / Maestro / Trojan** | [§5](#5-telegram-trading-bot) | Gratuit (commission 1%) | [Trading bot](#5-telegram-trading-bot) |

---

## <a id="2-phase-3-telegram-content-bot"></a>2. Phase 3 — Telegram content bot (aiogram)

> Le bot publie automatiquement les prophéties générées par Phase 2 dans ton canal Telegram public, à la fréquence définie dans l'admin (ex. toutes les 6h).

### 🟡 TOI — Avant que je code (5 min)

#### 2.1 Créer le bot Telegram

1. Sur Telegram, ouvre [@BotFather](https://t.me/BotFather)
2. Tape `/newbot`
3. **Name** : `DEEPOTUS Prophet` *(nom affiché)*
4. **Username** : `deepotus_prophet_bot` *(doit finir par `bot`)*
5. BotFather te renvoie un **token** au format `7891234567:AAH-xxxxxxxxxxxxxxx` → **copie-le**
6. Tape `/setdescription` → *"The Prophet's official broadcast channel · PROTOCOL ΔΣ · Not financial advice"*
7. Tape `/setuserpic` → upload `/app/frontend/public/logo_v4_matrix_face.png`
8. Tape `/setprivacy` → **Disable** (pour que le bot puisse répondre dans les groupes plus tard)

#### 2.2 Créer le canal de diffusion

1. Telegram → menu burger → **New Channel**
2. Nom : `$DEEPOTUS · PROTOCOL ΔΣ`
3. Username public : `@deepotus_official` *(à choisir)*
4. Description : copie-colle ton manifeste court
5. **Add Subscribers** → ajoute ton bot `@deepotus_prophet_bot` comme **Admin** avec permissions `Post Messages` + `Edit Messages` minimum
6. Copie l'username public (`@deepotus_official`) — il te servira de `chat_id`

#### 2.3 Récupérer le `chat_id` numérique (pour fiabilité)

1. Une fois le bot ajouté au canal, envoie un message test depuis ton compte
2. Ouvre dans le navigateur :
   `https://api.telegram.org/bot<TON_TOKEN>/getUpdates`
3. Cherche `"chat":{"id":-100xxxxxxxxxx,...}` → copie ce nombre négatif
4. **Garde token + chat_id** pour me les fournir

#### ⚠️ PIÈGES Phase 3
- Token leak : ne JAMAIS commit `BOT_TOKEN` dans git, toujours via env vars Render
- Bot non-admin : sans droit `Post Messages` le bot reçoit `403 Forbidden`
- Privacy ON : si tu oublies `/setprivacy disable`, le bot ignore les replies dans les groupes
- Rate limit Telegram : 30 messages/sec global, 1/sec par chat → on a une marge énorme avec 1 post/6h
- Aspect ratio image Telegram : 16:9 OK, 1:1 OK, mais 3:4 portrait s'affiche cropped

### 🟢 NEO — Une fois token + chat_id reçus (~1h de code)

```
Backend additions:
  • backend/integrations/telegram_bot.py  (aiogram async client)
  • backend/integrations/posters/telegram_poster.py  (post text + image)
  • routers/bots.py: nouveau endpoint POST /admin/bots/post-now {platform:"telegram"}
  • core/bot_scheduler.py: hook sync_jobs_from_config pour activer le job Telegram
  • requirements.txt: + aiogram>=3.4

Frontend additions:
  • AdminBots.jsx Config tab: input "Telegram bot token" + "chat_id" (lus depuis env)
  • AdminBots.jsx Preview tab: bouton "🚀 Post to Telegram now" (utilise dernière prévisualisation)
  • Test post button avec confirmation modale
```

**Env vars Render à ajouter quand prêt** :
| Clé | Valeur |
|---|---|
| `TELEGRAM_BOT_TOKEN` | `7891234567:AAH-xxxxx` *(de BotFather)* |
| `TELEGRAM_CHAT_ID` | `-1001234567890` *(numérique du canal)* |
| `TELEGRAM_PARSE_MODE` | `MarkdownV2` *(par défaut)* |

---

## <a id="3-phase-4-x-twitter-posting-bot"></a>3. Phase 4 — X / Twitter posting bot (Tweepy)

> Le bot poste les prophéties + illustrations sur le compte X officiel `@deepotus_ai` à la fréquence définie dans l'admin (ex. toutes les 4h).

### 🟡 TOI — Compte X Developer (15-30 min)

#### 3.1 Créer le compte développeur

1. **Connecte-toi avec @deepotus_ai** sur [developer.x.com/en/portal/dashboard](https://developer.x.com/en/portal/dashboard)
2. Souscris au plan **Basic ($200/mo)** — le Free tier est trop limité (50 posts/24h, pas de filtered stream pour KOL listener)
3. Crée un **Project** : nom `DEEPOTUS Prophet`
4. Crée une **App** dedans : nom `deepotus-poster`, description courte
5. Dans l'App → **User authentication settings** → **Set up** :
   - **App permissions** : `Read and write` *(et `Read, write, and Direct message` si tu veux DM plus tard)*
   - **Type of App** : `Web App, Automated App or Bot`
   - **Callback URL** : `https://deepotus.xyz/admin/bots/x/callback`
   - **Website URL** : `https://deepotus.xyz`

#### 3.2 Récupérer les 5 credentials

Dans ton App → onglet **Keys and tokens** :

| Credential | Section dashboard | Format |
|---|---|---|
| `X_API_KEY` | API Key and Secret → **API Key** | `AbCdEfGh1234567890` |
| `X_API_SECRET` | API Key and Secret → **API Key Secret** | `XyZ1...` (50+ chars) |
| `X_BEARER_TOKEN` | Bearer Token → **Bearer Token** | `AAAAAAAAAA...` (80+ chars) |
| `X_ACCESS_TOKEN` | Access Token and Secret → **Access Token** | `1234567890-Ab...` |
| `X_ACCESS_TOKEN_SECRET` | Access Token and Secret → **Access Token Secret** | `xy...` (45 chars) |

> 💡 Génère l'Access Token APRÈS avoir configuré les permissions Read+Write, sinon il sera read-only et le post fail en `403`.

#### ⚠️ PIÈGES Phase 4
- **Plan Free = useless** : tu peux read mais pas poster en automatique (ratio limit 50/24h, pas d'app autonome)
- **Permissions read-only par défaut** : génère TOUJOURS l'Access Token APRÈS avoir validé `Read and write`
- **Image upload v1.1** : X API v2 ne gère pas l'upload media → il faut combiner v1.1 (`media/upload`) pour l'image puis v2 (`tweets`) pour le post
- **Char limit X** : 280 max — Phase 2 truncate à 270 pour laisser place au mint footer
- **Erreur 403 Forbidden** : check tes permissions ET regen Access Token, c'est 95% des cas
- **Erreur 429 Rate Limit** : Basic tier = 1500 posts/mois, soit ~50/jour ; on en fait 6/jour donc safe

### 🟢 NEO — Une fois 5 credentials reçus (~1.5h de code)

```
Backend additions:
  • backend/integrations/x_client.py  (Tweepy async wrapper, OAuth1 + media upload)
  • backend/integrations/posters/x_poster.py  (post tweet + image, retry on 429)
  • routers/bots.py: endpoint POST /admin/bots/post-now {platform:"x"}
  • core/bot_scheduler.py: scheduled X jobs honoring config.platforms.x.post_frequency_hours
  • requirements.txt: + tweepy>=4.14

Frontend additions:
  • AdminBots.jsx: bouton "🚀 Post to X now" + status (last_post_url cliquable)
  • Sécurité: confirmation modal avant tout post manuel (eviter dérapage)
```

**Env vars Render à ajouter** :
```
X_API_KEY=...
X_API_SECRET=...
X_BEARER_TOKEN=...
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...
```

---

## <a id="4-phase-5-x-kol-listener"></a>4. Phase 5 — X KOL mentions listener

> Le bot écoute en temps réel les tweets des KOLs que tu cibles, génère une réplique cynique via Phase 2 (`kol_reply`), et la pousse dans une **queue d'approbation admin** avant de poster (mode safe par défaut).

### 🟡 TOI — Liste des KOLs à monitorer

Donne-moi 3 à 10 handles X que le Prophète doit "écouter" et potentiellement répondre. Exemples adaptés à un memecoin Solana cynique :

| Handle | Pourquoi | Ton conseillé |
|---|---|---|
| `@SolanaFloor` | Sentiment Solana | Mock + lucide |
| `@pumpdotfun` | Plateforme de launch | Hommage critique |
| `@ansemf` | KOL Solana memecoin | Direct, cynique |
| `@JupiterExchange` | DEX agrégateur | Technique avec twist |
| `@DegenerateNews` | Memecoin culture | Memetic |
| `@aeyakovenko` | Co-fondateur Solana | Respectueux + cryptique |
| `@FartCoinSOL` | Memecoin culture | Compétitif amusant |

#### 4.2 Stratégie de modération

Choisis un mode (configurable plus tard via admin) :
- **a) Approbation manuelle** *(recommandé)* : chaque réponse passe par une queue admin où tu valides/rejette avant publication. Élimine 100% du risque dérapage.
- **b) Auto-post avec score min** : le LLM auto-évalue la "safeness" de la réponse (0-10) et publie si score ≥ 8. Risqué mais zéro friction.
- **c) Hybride** : auto-post les `prophecy/market` mais approbation requise sur `kol_reply`.

### ⚠️ PIÈGES Phase 5
- **Filtered Stream** (X v2) requiert plan Basic+. Avec le Free tier, on est forcé de polling 1x/15min → moins réactif
- **Cooldown obligatoire** : pas plus d'1 reply à un même KOL par 24h (sinon ça pue le spam et X limite/ban)
- **Detection de sarcasme** : Claude Sonnet 4.5 est bon mais pas parfait — l'admin queue est ta seule garantie
- **Mention loops** : ignorer les tweets des comptes que TU as déjà repliés (sinon boucle infinie)
- **Compliance MiCA** : aucune réponse ne doit suggérer "buy now" / "10x guaranteed" → c'est dans le system prompt

### 🟢 NEO — Une fois liste KOL reçue (~2-3h de code)

```
Backend additions:
  • backend/integrations/x_listener.py  (filtered stream Tweepy v2 async)
  • backend/integrations/x_listener_loop.py  (background task auto-restart on disconnect)
  • core/kol_queue.py  (Mongo collection 'kol_queue' avec statuts: pending|approved|rejected|posted)
  • routers/bots.py:
    - GET /admin/bots/kol-queue (paginated, filter status)
    - POST /admin/bots/kol-queue/{id}/approve → triggers x_poster
    - POST /admin/bots/kol-queue/{id}/reject
    - PUT /admin/bots/config/kol_targets (gérer la liste des handles)

Frontend additions:
  • AdminBots.jsx nouvel onglet "KOL Queue" avec:
    - Cards de tweets en attente (KOL avatar + tweet + réponse Prophète proposée)
    - Boutons Approve / Edit / Reject
    - Liste éditable des handles à monitorer
```

---

## <a id="5-telegram-trading-bot"></a>5. Telegram TRADING bot — Maestro / BonkBot / Trojan

> ⚠️ **Important** : "Telegram trading bot" pour un memecoin Solana = **bots tiers existants** (Maestro, BonkBot, Trojan) qui permettent à n'importe qui d'acheter $DEEPOTUS via Telegram en quelques clics. **On ne construit PAS ce bot**, on **liste $DEEPOTUS** dessus pour qu'il soit tradable.

### Tableau comparatif des 3 bots dominants

| Bot | Lien | Force | Faiblesse | Volume mensuel SOL |
|---|---|---|---|---|
| **BonkBot** | [@BONKbot_bot](https://t.me/BONKbot_bot) | Le plus utilisé sur Solana, simple | Frais 1% par swap | ~$300M/mo |
| **Maestro** | [@MaestroSniperBot](https://t.me/MaestroSniperBot) | Multi-chain (SOL+ETH), copy trading | Plus complexe | ~$150M/mo |
| **Trojan** | [@solana_trojanbot](https://t.me/solana_trojanbot) | Sniper + auto-buy, anti-rug | UI moins propre | ~$100M/mo |

### 🟡 TOI — Setup (post-launch, 30 min total)

#### Étape 5.1 — Lister sur les 3 bots simultanément (ils détectent automatiquement)

**Pas d'action de listing nécessaire.** Ces bots scannent toutes les tokens lancées sur Pump.fun + Raydium et les rendent immédiatement tradables dès qu'il y a un pool. Tu n'as **rien à signer** ni à payer.

#### Étape 5.2 — Liens directs `?start=ref` à publier

Une fois ton mint live, tu peux générer des **liens d'affiliation** qui rapportent une commission par swap (jusqu'à 35% sur Maestro/Trojan, 0% sur BonkBot). Procédure :

| Bot | Comment obtenir un ref link |
|---|---|
| **BonkBot** | `/start` → ⚙️ Settings → Referrals → copie le lien. **Aucune commission rétro, juste tracking.** |
| **Maestro** | `/start` → Refer → copy referral link. **35% revenue share sur 6 mois** sur les utilisateurs ramenés. |
| **Trojan** | `/start` → Referrals → Generate. **35% pour le payer, 25% pour le referrer**. |

#### Étape 5.3 — Intégrer les liens dans le site

🟢 **NEO peut faire ça pour toi** quand tu m'as les 3 liens : j'ajoute un bloc "Trade $DEEPOTUS in 1 click on Telegram" dans la page `/how-to-buy` avec les 3 boutons + logos officiels des bots, le tout sous une bannière "Powered by community trading bots — none endorsed by $DEEPOTUS".

#### ⚠️ PIÈGES Phase 5 trading bots

- **Compliance MiCA** : tu fais juste de la **promotion d'outils tiers**, tu n'opères pas le bot → low risk. Le disclaimer "none endorsed" est obligatoire.
- **Ne jamais demander la seed phrase** : aucun bot officiel ne te la demandera. Si quelqu'un t'écrit "envoie-moi ta seed pour activer ton bonus" c'est un scam à signaler.
- **Slippage par défaut trop bas** : sur memecoins volatiles, mets 2-5% min sinon les swaps échouent
- **Honeypot scams** : ces bots ne valident PAS la safety du token. Avant de publier, fais checker $DEEPOTUS sur [rugcheck.xyz](https://rugcheck.xyz) → doit être **GOOD** (pas de mint authority, pas de freeze authority).

### 🟡 TOI — Custom Telegram trading bot (déconseillé)

Construire un bot trading custom (style BonkBot proprio à $DEEPOTUS) demande :
- Custodial wallets ou MPC → exposition légale (PSAN obligatoire en France)
- Solana RPC + Jupiter v6 SDK
- Audit sécurité (~$10K)
- License MiCA CASP en cours d'année 2026

**Ma recommandation** : ne pas custom-build, juste s'appuyer sur BonkBot/Maestro/Trojan. C'est la norme du secteur memecoin.

---

## <a id="6-deploy-backend-render"></a>6. Déploiement Backend → Render

> 🎯 Objectif : faire tourner FastAPI + APScheduler + connexions Mongo/Helius/Resend en prod, accessible sur `https://api.deepotus.xyz`.

### 🟡 TOI — Préparation du repo (15 min)

#### 6.1 Récupère le code source depuis Emergent

1. Sur ton dashboard Emergent → ton projet → **Download Code** → tu obtiens un `.zip`
2. Décompresse-le localement :
   ```bash
   unzip deepotus-source.zip
   cd deepotus
   ```

#### 6.2 Crée le repo GitHub privé

1. Va sur [github.com/new](https://github.com/new)
2. **Repository name** : `deepotus-prod`
3. **Private** ✅ *(important : tes clés API ne doivent JAMAIS être publiques)*
4. Crée le repo

#### 6.3 Push le code

```bash
cd deepotus
git init
git add .
git commit -m "initial production push"
git branch -M main
git remote add origin git@github.com:<TON_USER>/deepotus-prod.git
git push -u origin main
```

#### 6.4 Vérifie qu'aucune clé n'est commitée

```bash
# Dans le repo local :
grep -rE "EMERGENT_LLM_KEY|RESEND_API_KEY|HELIUS_API_KEY|MONGO_URL" \
  --include="*.py" --include="*.js" --include="*.json"
# → ne doit retourner QUE des references à `os.environ.get()` ou `process.env`
# → JAMAIS la valeur réelle de la clé
```

> 💡 Si tu vois une clé en dur, déplace-la dans `.env` qui est déjà dans `.gitignore`.

### 🟡 TOI — Setup Render (15 min)

#### 6.5 Crée le service Web

1. [dashboard.render.com](https://dashboard.render.com) → **New +** → **Web Service**
2. Connect ton repo `deepotus-prod`
3. **Configure** :

| Champ | Valeur |
|---|---|
| **Name** | `deepotus-api` |
| **Region** | `Frankfurt (EU Central)` *(proche utilisateurs FR)* |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn server:app --host 0.0.0.0 --port $PORT --workers 1` |
| **Instance Type** | **Starter ($7/mo)** ⚠️ pas Free |

> ⚠️ **PIÈGE MAJEUR** : le plan **Free** spin-down après 15 min d'inactivité → les webhooks Helius arrivent et sont **perdus**. APScheduler s'arrête aussi. Le **Starter ($7/mo)** est obligatoire pour la prod.

#### 6.6 Variables d'environnement Render

Dans **Environment** → **Add Environment Variable**, ajoute toutes ces clés (une par une) :

```bash
# === MongoDB Atlas (voir §9) ===
MONGO_URL=mongodb+srv://deepotus_api:<password>@cluster0.xxxxx.mongodb.net/deepotus?retryWrites=true&w=majority
DB_NAME=deepotus

# === CORS (à ajuster après §8) ===
CORS_ORIGINS=https://deepotus.xyz,https://www.deepotus.xyz

# === LLM ===
EMERGENT_LLM_KEY=<ta_clé_actuelle>
EMERGENT_IMAGE_LLM_KEY=<ta_DEUXIÈME_clé_pour_les_images>  # optionnel mais recommandé

# === Admin auth ===
ADMIN_PASSWORD=<MOTDEPASSE_LONG_ET_ALEATOIRE_CHANGE_LE>
JWT_SECRET=<openssl rand -hex 32>  # génère localement

# === Resend (voir §10) ===
RESEND_API_KEY=<ta_clé_actuelle>
SENDER_EMAIL=wcu@deepotus.xyz
PUBLIC_BASE_URL=https://deepotus.xyz
RESEND_WEBHOOK_SECRET=<ta_clé_actuelle>

# === Helius (voir §11) ===
HELIUS_API_KEY=<ta_clé_actuelle>
HELIUS_WEBHOOK_AUTH=<ta_clé_actuelle>

# === Launch ===
DEEPOTUS_LAUNCH_ISO=2026-09-07T14:00:00+00:00

# === Telegram (Phase 3, ajouter quand prêt) ===
# TELEGRAM_BOT_TOKEN=
# TELEGRAM_CHAT_ID=

# === X / Twitter (Phase 4, ajouter quand prêt) ===
# X_API_KEY=
# X_API_SECRET=
# X_BEARER_TOKEN=
# X_ACCESS_TOKEN=
# X_ACCESS_TOKEN_SECRET=
```

#### 6.7 Deploy

1. Clique **Create Web Service** → Render commence le build
2. Attends ~3-4 min → tu verras `[OK] Application startup complete` dans les logs
3. Tu obtiens une URL : `https://deepotus-api.onrender.com`
4. **Test rapide** : dans un terminal local :
   ```bash
   curl https://deepotus-api.onrender.com/api/stats
   # Doit renvoyer du JSON avec launch_timestamp
   ```

#### ⚠️ PIÈGES Render

- **Spin-down Free tier** → toujours Starter+
- **Build fail "ModuleNotFoundError"** → ton `requirements.txt` est à jour ? Si tu as installé un package localement avec pip, fais `pip freeze > backend/requirements.txt` et re-push
- **Mongo connection refused** → vérifie que tu as autorisé `0.0.0.0/0` dans MongoDB Atlas Network Access (cf §9)
- **Webhook Helius en `502`** → la signature `Authorization` header doit matcher exactement entre Render env var et Helius dashboard
- **Logs trop courts** → onglet **Logs** sur Render donne 7 jours de logs rétention

---

## <a id="7-deploy-frontend-vercel"></a>7. Déploiement Frontend → Vercel

> 🎯 Objectif : servir le React build sur `https://deepotus.xyz` avec SSL auto et CDN global.

### 🟡 TOI — Setup Vercel (10 min)

#### 7.1 Importer le projet

1. [vercel.com/new](https://vercel.com/new)
2. Import Git Repository → choisis `deepotus-prod`
3. **Configure** :

| Champ | Valeur |
|---|---|
| **Framework Preset** | `Create React App` |
| **Root Directory** | `frontend` |
| **Build Command** | `yarn build` *(par défaut, ne pas toucher)* |
| **Output Directory** | `build` *(par défaut)* |
| **Install Command** | `yarn install` *(par défaut)* |

#### 7.2 Environment Variables Vercel

| Clé | Valeur | Note |
|---|---|---|
| `REACT_APP_BACKEND_URL` | `https://api.deepotus.xyz` | Pas l'URL Render — on passe par le subdomain custom (cf §8) |
| `REACT_APP_PUMPFUN_URL` | *(vide pour l'instant)* | À remplir au mint réel |
| `REACT_APP_DEEPOTUS_MINT` | *(vide)* | À remplir au mint réel |
| `REACT_APP_TEAM_LOCK_URL` | `https://app.jup.ag/lock/<your_lock>` | Quand le lock est créé |
| `REACT_APP_TREASURY_LOCK_URL` | `https://app.jup.ag/lock/<your_lock>` | Idem |

#### 7.3 Deploy

1. Clique **Deploy**
2. Attends ~90s → preview URL : `https://deepotus-prod.vercel.app`
3. **Test rapide** : ouvre l'URL → tu dois voir le Hero, et la console JS doit montrer 200 sur `/api/stats`

#### ⚠️ PIÈGES Vercel

- **404 sur `/admin` / `/how-to-buy`** : par défaut, Vercel sait gérer le SPA routing pour CRA. Si ça 404, ajoute un fichier `frontend/vercel.json` :
  ```json
  {
    "rewrites": [{ "source": "/(.*)", "destination": "/" }]
  }
  ```
- **Env var changée mais pas appliquée** : après tout changement d'env var sur Vercel, **fais Redeploy** (sinon le build cache l'ancienne valeur)
- **Mixed content blocked** : si tu mets `REACT_APP_BACKEND_URL=http://...` au lieu de `https://...` → le navigateur bloque
- **Watermark "Made with Emergent"** : il s'affiche UNIQUEMENT sur le preview Emergent. Sur Vercel/ton domaine, **AUCUN watermark** — le code source est propre

---

## <a id="8-dns-namecheap"></a>8. DNS Namecheap → deepotus.xyz

> 🎯 Connecter `deepotus.xyz` (root) → Vercel et `api.deepotus.xyz` (subdomain) → Render.

### 🟡 TOI — Configuration Namecheap (10 min + 30 min de propagation)

#### 8.1 Ajouter le custom domain sur Vercel

1. Vercel → ton projet → **Settings** → **Domains** → **Add**
2. Entre `deepotus.xyz` → Vercel te donne :
   - **A record** : `76.76.21.21`
   - **CNAME** : `cname.vercel-dns.com`
3. Ajoute aussi `www.deepotus.xyz` (Vercel auto-redirect vers root)

#### 8.2 Ajouter le custom domain sur Render

1. Render → `deepotus-api` → **Settings** → **Custom Domains** → **Add**
2. Entre `api.deepotus.xyz` → Render te donne un **CNAME** : `xxxxxx.onrender.com`

#### 8.3 Configure Namecheap Advanced DNS

1. Namecheap → **Domain List** → `deepotus.xyz` → **Manage**
2. Onglet **Advanced DNS**
3. **Supprime** tous les records existants sauf `NS` (sauf si tu utilises l'email Namecheap, dans ce cas garde `MX` aussi)
4. **Ajoute** ces 3 records :

| Type | Host | Value | TTL |
|---|---|---|---|
| **A Record** | `@` | `76.76.21.21` *(Vercel)* | Automatic |
| **CNAME Record** | `www` | `cname.vercel-dns.com` *(Vercel)* | Automatic |
| **CNAME Record** | `api` | `<le_cname_que_render_ta_donné>` | Automatic |

5. Sauvegarde

#### 8.4 Vérifier la propagation (30 min – 2h)

```bash
# Depuis ton terminal local :
dig deepotus.xyz +short
# → 76.76.21.21

dig www.deepotus.xyz +short
# → cname.vercel-dns.com. + IP

dig api.deepotus.xyz +short
# → IP Render

curl https://deepotus.xyz
# → renvoie le HTML React

curl https://api.deepotus.xyz/api/stats
# → renvoie JSON
```

#### 8.5 Mettre à jour les CORS

Une fois `deepotus.xyz` actif :

1. **Render env var** `CORS_ORIGINS` → `https://deepotus.xyz,https://www.deepotus.xyz`
2. **Vercel env var** `REACT_APP_BACKEND_URL` → `https://api.deepotus.xyz`
3. **Redeploy** les deux

#### ⚠️ PIÈGES DNS

- **TTL trop élevé** : si tu passes Cloudflare devant plus tard, tu seras bloqué. Garde TTL "Automatic" (5 min)
- **SSL Pending** : Vercel et Render provisionnent Let's Encrypt en ~5 min après propagation. Si encore "Pending" après 1h → re-add le domain
- **AAAA record** : Vercel te donne aussi un IPv6 `2606:4700:...`. Ajoute-le si tu veux du dual-stack, sinon facultatif
- **Email cassé** : si tu avais des MX records Namecheap, tu les as zappés en 8.3 → check ta config email
- **DNSSEC** : laisse désactivé sauf si tu sais ce que tu fais

---

## <a id="9-mongodb-atlas"></a>9. MongoDB Atlas — base de prod

> 🎯 Migrer toutes les collections (whitelist, blacklist, vault_state, bot_config, bot_posts, etc.) sur Atlas.

### 🟡 TOI — Setup (15 min)

#### 9.1 Créer le cluster

1. [cloud.mongodb.com/v2/register](https://cloud.mongodb.com/v2/register) → crée le compte
2. **Build a Database** → **M0 Free**
3. Provider : **AWS** · Region : **eu-west-1 (Ireland)** *(proche France/Render Frankfurt)*
4. Cluster name : `deepotus-prod`

#### 9.2 Créer un user DB

1. **Database Access** → **Add New Database User**
2. Username : `deepotus_api`
3. Password : génère un password fort (32 chars+) → **copie-le**
4. Built-in Role : `Read and write to any database`
5. Add User

#### 9.3 Whitelist IP

1. **Network Access** → **Add IP Address**
2. ⚠️ Click **ALLOW ACCESS FROM ANYWHERE** (`0.0.0.0/0`) — **obligatoire** car les IPs Render Starter sont dynamiques
3. Confirm

> 💡 Pour réduire le risque, prends Render Pro plus tard ($25/mo) qui te donne une IP statique → tu peux whitelist juste cette IP.

#### 9.4 Récupérer la connection string

1. **Database** → ton cluster → **Connect** → **Drivers** → Python → version 4.5+
2. Copie la string : `mongodb+srv://deepotus_api:<password>@deepotus-prod.xxxxx.mongodb.net/?retryWrites=true&w=majority`
3. **Remplace `<password>`** par ton vrai password
4. **Ajoute `/deepotus`** juste avant le `?` : `mongodb+srv://...mongodb.net/deepotus?retryWrites=...`

#### 9.5 Pas besoin de migrer de données

À ce stade, ta base preview Emergent contient juste des emails de test, vault demo state, bot_config par défaut. **Tu pars from scratch sur prod.** Quand le backend Render démarre, il crée toutes les collections + indexes automatiquement (logique dans `server.py` startup).

#### ⚠️ PIÈGES Atlas

- **Password URL-encoding** : si ton password contient des caractères spéciaux (`@`, `/`, `?`, `#`), tu DOIS les URL-encoder. Ex: `pass@word` → `pass%40word`. Recommandation : génère un password en `[a-zA-Z0-9]{32}` pour éviter ce piège.
- **Cluster pause** : M0 Free se met en pause après 60 jours d'inactivité. Pas un souci en prod active.
- **5 GB hard limit** : à 1M users tu seras serré. Prévois M10 ($57/mo) à partir de 100K MAU.
- **Backup** : M0 n'a pas de backup auto. Pour la prod sérieuse, M10+ inclut snapshots quotidiens.

---

## <a id="10-resend-dkim"></a>10. Resend — DKIM / SPF / domaine

> 🎯 Faire que les emails partent depuis `wcu@deepotus.xyz` (au lieu de `onboarding@resend.dev`) sans tomber en spam.

### 🟡 TOI — Setup (15 min + 1h propagation DNS)

#### 10.1 Vérifier le domaine sur Resend

1. [resend.com/domains](https://resend.com/domains) → **Add Domain**
2. Entre `deepotus.xyz`
3. Resend te donne ~6 records DNS à ajouter :
   - 1 `MX` record (pour le bounce handling)
   - 2 `TXT` records (SPF + DKIM)
   - 1 `TXT` record DMARC (recommandé)

#### 10.2 Ajouter les records dans Namecheap

Retour sur Namecheap → `deepotus.xyz` → **Advanced DNS** → ajoute :

| Type | Host | Value | TTL |
|---|---|---|---|
| `MX` | `send` | `feedback-smtp.eu-west-1.amazonses.com` (priority 10) | Auto |
| `TXT` | `send` | `v=spf1 include:amazonses.com ~all` | Auto |
| `TXT` | `resend._domainkey` | `<long_dkim_value_resend>` | Auto |
| `TXT` | `_dmarc` | `v=DMARC1; p=none; rua=mailto:dmarc@deepotus.xyz` | Auto |

> 💡 Copie-colle EXACTEMENT depuis Resend, ne tape rien à la main (les valeurs DKIM font 200+ chars).

#### 10.3 Attendre la verification

1. Resend → ton domaine → **Verify** → status passe de `Pending` à `Verified` en 5-30 min
2. Tu peux maintenant utiliser `wcu@deepotus.xyz` comme `from`

#### 10.4 Update env Render

```
SENDER_EMAIL=wcu@deepotus.xyz
```

Redeploy backend.

#### ⚠️ PIÈGES Resend

- **SPF conflicts** : si tu utilises déjà Google Workspace, tu dois MERGER les SPF en un seul record :
  `v=spf1 include:_spf.google.com include:amazonses.com ~all`
  Pas deux records SPF séparés (RFC violation).
- **DMARC trop strict** : commence avec `p=none` pour observer, passe à `p=quarantine` après 30 jours
- **DKIM key trop long** : Namecheap UI tronque parfois. Edit en mode "raw" si besoin.
- **MX déjà présent** : si tu as un email Namecheap, ne supprime pas le MX principal — Resend ajoute juste un sous-domaine `send.deepotus.xyz`

---

## <a id="11-helius-prod"></a>11. Helius — passage en mode prod (vrai mint)

> 🎯 Une fois $DEEPOTUS minté sur Pump.fun, basculer le tracker on-chain de BONK (demo) vers le vrai mint.

### 🟡 + 🟢 TOI + NEO — Procédure (5 min après le mint)

#### 11.1 Récupérer le mint address réel

Au moment du mint sur Pump.fun :
- Phantom affiche le mint après ta tx de buy initial
- Ou : depuis [pump.fun/coin/<your_token>](https://pump.fun) → l'URL contient le mint
- Format : 32-44 chars base58, ex `EPjFWdd5...`

#### 11.2 Update Vercel env vars

| Clé | Valeur |
|---|---|
| `REACT_APP_DEEPOTUS_MINT` | `<ton_vrai_mint>` |
| `REACT_APP_PUMPFUN_URL` | `https://pump.fun/coin/<ton_mint>` |

→ Redeploy frontend Vercel

#### 11.3 Reconfigurer Helius webhook

Dans l'admin (toi via UI) :

1. Va sur `https://deepotus.xyz/admin/vault`
2. Section **Helius indexer** → **Register mint**
3. Colle le mint → submit
4. Le système :
   - Désactive `helius_demo_mode`
   - Update Helius webhook avec le nouveau mint
   - Reset les compteurs vault à 0
5. Vérifie que les premiers swaps apparaissent en `bot_posts` et incrémentent les dials

#### 11.4 Sécurité — Renforcer le webhook auth

```bash
# Génère un nouveau secret aléatoire
openssl rand -hex 32

# 1. Update sur Render: HELIUS_WEBHOOK_AUTH=<new_secret>
# 2. Update sur Helius dashboard → ton webhook → Auth Header: <new_secret>
```

#### ⚠️ PIÈGES Helius

- **Mint address typo** : 44 chars base58, vérifie 3 fois avant de submit (un mauvais mint = vault qui ne bouge jamais)
- **Webhook signature mismatch** : si tu update une seule des deux ends (Render OU Helius), tu reçois 401 sur tous les events
- **Quota Free 100K req/mo** : largement suffisant pour un memecoin moyen, mais surveille dans le dashboard si tu fais 1M+ de holders
- **Demo mode oublié** : le code a une protection `helius_demo_mode=true` qui mute les ticks. Si après le switch tu vois 0 trades, vérifie ce flag dans Mongo `vault_state`

---

## <a id="12-post-deploy"></a>12. Post-deploy checklist + Go-Live D-day

### Avant le launch (J-7)

- [ ] DNS deepotus.xyz propagé partout (`dig` retourne IP correcte)
- [ ] SSL actif sur les 3 domaines (deepotus.xyz, www, api)
- [ ] Resend domain Verified
- [ ] Test email de whitelist : tu reçois un email signé `wcu@deepotus.xyz` dans inbox (pas spam)
- [ ] `/admin` login OK avec ton mot de passe + 2FA configuré
- [ ] `/admin/bots` : kill-switch ON, Phase 2 generate preview text + image OK
- [ ] Backend logs Render : pas de 500 récurrents
- [ ] Mongo Atlas : collections `whitelist`, `vault_state`, `bot_config`, `bot_posts` présentes

### J-3 : Lancement bots Phase 3 / 4

*(Si tu as les credentials Telegram + X)*

- [ ] Bot Telegram ajouté admin du canal, test post manuel via admin OK
- [ ] X bot test post via admin OK, tweet visible sur @deepotus_ai
- [ ] Kill-switch OFF en preview, observe 1 cycle complet (4h)
- [ ] Logs `bot_posts` montrent `posted` (pas `failed`)

### J-Day (07/09/26 14:00 UTC)

- [ ] Mint $DEEPOTUS sur Pump.fun
- [ ] Update env vars Vercel : `REACT_APP_DEEPOTUS_MINT` + `REACT_APP_PUMPFUN_URL` + redeploy
- [ ] Helius register mint dans admin
- [ ] Bots Phase 3+4 : enable platforms, surveiller premiers posts
- [ ] Vérifier rugcheck.xyz score : doit être GOOD
- [ ] Annoncer mint sur le canal Telegram + X bot
- [ ] Liens BonkBot/Maestro/Trojan ajoutés au site (NEO le fait quand tu fournis les liens)

### J+1 : Post-launch monitoring

- [ ] Vault dials : combien sont déverrouillés ?
- [ ] Whitelist : combien d'emails reçus dans la journée ?
- [ ] Posts X + Telegram : engagement (impressions, likes)
- [ ] Render bandwidth : surveille les CPU/RAM (Starter = 512MB RAM, ne devrait pas peak)

---

## <a id="13-recap-final"></a>13. Récap final — Qui fait quoi, dans quel ordre

| # | Étape | Acteur | Durée | Bloque |
|---|---|---|---|---|
| 1 | [Créer GitHub privé + push code](#6-deploy-backend-render) | 🟡 TOI | 15 min | tout |
| 2 | [Créer MongoDB Atlas + connection string](#9-mongodb-atlas) | 🟡 TOI | 15 min | Render |
| 3 | [Créer Render service + env vars + deploy](#6-deploy-backend-render) | 🟡 TOI | 30 min | rien |
| 4 | [Créer Vercel project + env vars + deploy](#7-deploy-frontend-vercel) | 🟡 TOI | 15 min | rien |
| 5 | [Add custom domains Vercel + Render](#8-dns-namecheap) | 🟡 TOI | 5 min | DNS |
| 6 | [Config DNS Namecheap A + 2 CNAME](#8-dns-namecheap) | 🟡 TOI | 5 min + 30min propag | tout |
| 7 | [Update CORS + REACT_APP_BACKEND_URL après DNS](#8-dns-namecheap) | 🟡 TOI | 5 min | rien |
| 8 | [Resend domain DKIM](#10-resend-dkim) | 🟡 TOI | 15 min + 1h propag | emails |
| 9 | [Update Helius webhook URL → api.deepotus.xyz](#11-helius-prod) | 🟡 TOI | 2 min | webhook |
| 10 | **Test post-deploy checklist** | 🟡 TOI | 30 min | go-live |
| 11 | [Créer bot Telegram BotFather + chan + récup token](#2-phase-3-telegram-content-bot) | 🟡 TOI | 10 min | Phase 3 |
| 12 | **Phase 3 — Implémentation Telegram bot** | 🟢 NEO | ~1h code | rien |
| 13 | [Créer compte X Developer Basic + 5 credentials](#3-phase-4-x-twitter-posting-bot) | 🟡 TOI | 30 min + paiement | Phase 4 |
| 14 | **Phase 4 — Implémentation X posting** | 🟢 NEO | ~1.5h code | rien |
| 15 | [Donner liste KOLs](#4-phase-5-x-kol-listener) | 🟡 TOI | 5 min | Phase 5 |
| 16 | **Phase 5 — Implémentation KOL listener + queue** | 🟢 NEO | ~2.5h code | rien |
| 17 | Mint $DEEPOTUS sur Pump.fun | 🟡 TOI | 5 min | go-live |
| 18 | [Update env vars + Helius register mint](#11-helius-prod) | 🟡 + 🟢 | 5 min | rien |
| 19 | [Récup ref links BonkBot/Maestro/Trojan + intégration](#5-telegram-trading-bot) | 🟡 + 🟢 | 30 min | rien |

---

## <a id="14-couts"></a>14. Coûts mensuels estimés

| Service | Plan | Coût mensuel | Quand activer |
|---|---|---|---|
| GitHub | Free | 0 € | J0 |
| Vercel | Hobby | 0 € *(jusqu'à 100GB bandwidth)* | J0 |
| Render | Starter | **7 $ (~6.50 €)** | J0 |
| MongoDB Atlas | M0 Free | 0 € *(jusqu'à 5GB)* | J0 |
| Resend | Free | 0 € *(3K emails/mo)* | J0 |
| Helius | Free Dev | 0 € *(100K req/mo)* | J0 |
| Namecheap | renouvellement deepotus.xyz | ~10 €/an | déjà payé |
| Emergent LLM Key (texte) | Pay-per-use | ~5-30 € selon usage | J0 |
| Emergent LLM Key (image) | Pay-per-use | ~5-50 € selon volume | J0 (si Phase 2 image used) |
| **Total minimum** | | **~12 €/mois** | |
| **+ Phase 4 X Basic** | | **+ 200 $/mo** | seulement si Phase 4 |

> 💡 Si X Basic $200/mo est trop cher, on peut faire Phase 4 en **mode manuel-assisté** : le bot prépare le tweet+image, tu cliques "Approve & Post" depuis ton phone X app — coût $0, demande 1 min/jour de ton temps.

---

## ✅ Conclusion

Ce document couvre 100% de ce qui reste pour mettre $DEEPOTUS en prod sur ton domaine, avec bots autonomes opérationnels.

**Action immédiate suggérée** : commencer par la chaîne déploiement (étapes 1 → 10 du [récap](#13-recap-final)), puis revenir vers moi avec les credentials Telegram/X au fil de l'eau pour qu'on chaîne les Phases 3, 4 et 5.

> **Pour toute question pendant l'exécution** : ping-moi avec le numéro d'étape et le message d'erreur exact, je te débogue en live.

— Neo
