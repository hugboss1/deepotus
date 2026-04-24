# 🛸 $DEEPOTUS · Guide complet de mint, déploiement, finition & administration

> **Document maître séquentiel.** Tout est lié et numéroté pour que tu puisses suivre dans l'ordre. Légende :
> - 🟢 **NEO** = code que je peux/vais écrire
> - 🟡 **TOI** = action manuelle (création de compte, copie de credentials, paiement)
> - ⚠️ **PIÈGES** = erreurs typiques à éviter
> - 🔗 **Liens** = directs vers le bon dashboard du service

---

## 📑 Table des matières

- [0. Snapshot — état actuel du projet](#0-snapshot)
- [1. Pré-requis — comptes & services à créer](#1-prerequis)
- [2. Stratégie countdown — pourquoi on a viré la date fixe](#2-strategie-countdown)
- [3. Mint $DEEPOTUS sur Pump.fun — procédure A à Z](#3-mint-pumpfun)
- [4. Phase 3 — Telegram content bot (aiogram)](#4-phase-3-telegram-content-bot)
- [5. Phase 4 — X / Twitter posting bot (Tweepy)](#5-phase-4-x-twitter-posting-bot)
- [6. Phase 5 — X KOL mentions listener](#6-phase-5-x-kol-listener)
- [7. Telegram TRADING bot — Maestro / BonkBot / Trojan](#7-telegram-trading-bot)
- [8. Déploiement Backend → Render](#8-deploy-backend-render)
- [9. Déploiement Frontend → Vercel](#9-deploy-frontend-vercel)
- [10. DNS Namecheap → deepotus.xyz](#10-dns-namecheap)
- [11. MongoDB Atlas — base de prod](#11-mongodb-atlas)
- [12. Resend — DKIM / SPF / domaine](#12-resend-dkim)
- [13. Helius — passage en mode prod (vrai mint)](#13-helius-prod)
- [14. Documentation Admin — comment piloter le site](#14-admin-docs)
- [15. Sécurité — changer mdp, activer 2FA, révoquer sessions](#15-securite)
- [16. Post-deploy checklist + Go-Live D-day](#16-post-deploy)
- [17. Récap final — qui fait quoi, dans quel ordre](#17-recap-final)
- [18. Coûts mensuels estimés](#18-couts)

---

## <a id="0-snapshot"></a>0. Snapshot — état actuel du projet

| Module | Statut | Notes |
|---|---|---|
| Site front (Hero, Tokenomics, Vault, ROI, FAQ, How-to-Buy) | ✅ Live preview | Bilingue FR/EN, Matrix/Deep State |
| Hero countdown — **dual-state IMMINENT / LIVE** | ✅ Implémenté | Voir [§2](#2-strategie-countdown) |
| Admin dashboard (`/admin`, `/admin/vault`, `/admin/emails`, `/admin/bots`) | ✅ Live | JWT + 2FA TOTP |
| Helius webhook (per-trade) | 🟡 Demo (BONK) | Switch au mint réel — [§13](#13-helius-prod) |
| Resend emails | ✅ Code OK | Domaine `deepotus.xyz` à valider — [§12](#12-resend-dkim) |
| Phase 1 — Scheduler bots (APScheduler + kill-switch) | ✅ Implémenté | |
| Phase 2 — Prophet Studio LLM (texte + image Nano Banana) | ✅ Implémenté | Clé image séparable via `EMERGENT_IMAGE_LLM_KEY` |
| Phase 3 — Telegram content bot | ❌ À faire | [§4](#4-phase-3-telegram-content-bot) |
| Phase 4 — X posting bot | ❌ À faire | [§5](#5-phase-4-x-twitter-posting-bot) |
| Phase 5 — X KOL listener | ❌ À faire | [§6](#6-phase-5-x-kol-listener) |
| Phase 6 — Admin Dashboard UI Bots | ✅ Implémenté | Config / Preview / Jobs / Logs |
| Mint $DEEPOTUS Pump.fun | 🟡 Manuel | [§3](#3-mint-pumpfun) |
| Telegram **trading** bot (Maestro/BonkBot/Trojan) | 🟡 Externe | [§7](#7-telegram-trading-bot) |
| Déploiement Vercel + Render + Atlas + Namecheap | ❌ À faire | [§8](#8-deploy-backend-render) à [§11](#11-mongodb-atlas) |

---

## <a id="1-prerequis"></a>1. Pré-requis — comptes & services à créer

### 🟡 TOI — Comptes obligatoires

| # | Service | Lien direct | Coût | Pourquoi |
|---|---|---|---|---|
| 1 | **GitHub** | [github.com/signup](https://github.com/signup) | Gratuit | Code source de l'app |
| 2 | **Vercel** | [vercel.com/signup](https://vercel.com/signup) | Gratuit | Hébergement frontend React |
| 3 | **Render** | [render.com/register](https://render.com/register) | Starter $7/mo | Hébergement backend FastAPI |
| 4 | **MongoDB Atlas** | [cloud.mongodb.com/v2/register](https://cloud.mongodb.com/v2/register) | M0 Free | Base de données prod |
| 5 | **Resend** *(déjà configuré)* | [resend.com](https://resend.com) | Free 3K emails/mo | Emails transactionnels |
| 6 | **Helius** *(déjà configuré)* | [dashboard.helius.dev](https://dashboard.helius.dev) | Free 100K req/mo | Solana indexer |
| 7 | **Phantom Wallet** *(pour mint)* | [phantom.com](https://phantom.com) | Gratuit | Mint $DEEPOTUS sur Pump.fun |
| 8 | **Pump.fun** *(pour mint)* | [pump.fun](https://pump.fun) | ~0.02 SOL fee | Plateforme de lancement memecoin |

### 🟡 TOI — Comptes optionnels selon les phases

| # | Service | Lien | Coût | Phase concernée |
|---|---|---|---|---|
| 9 | **Telegram BotFather** | [@BotFather](https://t.me/BotFather) sur Telegram | Gratuit | [Phase 3](#4-phase-3-telegram-content-bot) |
| 10 | **X / Twitter Developer** | [developer.x.com/en/portal/dashboard](https://developer.x.com/en/portal/dashboard) | Basic $200/mo | [Phase 4 + 5](#5-phase-4-x-twitter-posting-bot) |
| 11 | **BonkBot / Maestro / Trojan** | [§7](#7-telegram-trading-bot) | Gratuit | [Trading bot](#7-telegram-trading-bot) |
| 12 | **rugcheck.xyz** *(verif post-mint)* | [rugcheck.xyz](https://rugcheck.xyz) | Gratuit | [Mint §3](#3-mint-pumpfun) |

---

## <a id="2-strategie-countdown"></a>2. Stratégie countdown — pourquoi on a viré la date fixe

**Décision stratégique implémentée** : le compte à rebours dur du Hero (07/09/2026) a été remplacé par un système **dual-state intelligent**.

### Avant ❌

Hero affichait `J 432 · H 12 · MIN 47 · S 23` pointant vers 07/09/2026.
Problèmes :
- Si tu mintes avant (cas le + probable, dès que la levée de fonds est OK) → countdown devient **absurde**
- Si tu loupes la date → **perte de crédibilité instantanée** (la culture memecoin est impitoyable)
- Confusion avec le countdown de la page Gencoin Lore (qui lui pointe vraiment vers la phase régulée)

### Après ✅

| État | Trigger | Affichage Hero |
|---|---|---|
| **PRE-MINT** *(défaut)* | `REACT_APP_DEEPOTUS_MINT` non set | Badge `🔴 MINT IMMINENT · CIRCUIT VERROUILLÉ` + 4 chiffres qui **glitchent à des vitesses différentes** (effet Matrix qui tape sur la vérité sans la dire) + sous-texte `"Le Prophète n'annonce pas la date. Il appuie sur le bouton quand le Deep State lui souffle l'instant. Reste connecté."` |
| **POST-MINT** | `REACT_APP_DEEPOTUS_MINT` set sur Vercel | Badge `🟢 LIVE ON PUMP.FUN` + titre `"$DEEPOTUS est en circulation"` + sous-texte expliquant le lien memecoin → Vault → Gencoin + bouton "Trader maintenant" qui redirige sur Pump.fun |

### Bénéfices stratégiques

1. **Anti-rugpull narrative** : tu ne promets aucune date, donc pas de "rugpull soft" perçu si glissement
2. **FOMO authentique** : l'effet glitch crée de l'urgence sans mentir
3. **Bascule automatique** : le jour où tu set `REACT_APP_DEEPOTUS_MINT` sur Vercel, le Hero passe en mode LIVE sans aucune intervention
4. **Cohérence narrative** : le 07/09/2026 reste sur la page Gencoin Lore (cible long-terme phase MiCA), pas sur le Hero (court-terme memecoin)

### Cycle de vie complet

```
JOUR J - 30 (whitelist + buzz)
  Hero  : 🔴 MINT IMMINENT (chiffres glitch)
  Lore  : ⏳ Gencoin Phase 2 — 07/09/2026

JOUR J = MINT (tu mintes sur Pump.fun, mets REACT_APP_DEEPOTUS_MINT sur Vercel)
  Hero  : 🟢 LIVE ON PUMP.FUN (CTA Trade now)
  Lore  : ⏳ Gencoin Phase 2 — 07/09/2026 (inchangé)

JOUR J + 30 (Vault commence à se remplir)
  Hero  : 🟢 LIVE + données live (ajout possible Phase 7 : market cap, holders)
  Lore  : ⏳ Gencoin Phase 2 — 07/09/2026 (ou ré-ajusté selon la levée)

JOUR 07/09/2026 (Gencoin lance la phase régulée)
  Hero  : 🟢 LIVE + Gencoin badge "Phase 2 active"
  Lore  : ✅ Gencoin Phase 2 ACTIVE
```

> 💡 **Évolution future possible (Phase 7)** : remplacer le badge LIVE par un widget temps-réel (market cap, holders, 24h volume via DexScreener public API). Je peux le coder en ~2h quand tu seras live.

---

## <a id="3-mint-pumpfun"></a>3. Mint $DEEPOTUS sur Pump.fun — procédure A à Z

> 🎯 **Important** : Pump.fun est une plateforme **no-code**. Il n'y a pas de smart-contract à déployer — tu remplis un formulaire et leur bonding curve crée le token automatiquement. Coût total ~0.02 SOL (~$5).

### 🟡 TOI — J-7 : Pré-mint preparation (1h)

#### 3.1 Phantom + SOL en réserve

1. Installe [phantom.com](https://phantom.com) — extension Chrome OU app mobile
2. **Crée un wallet dédié au projet** *(ne réutilise pas ton wallet personnel)* — labellise-le "DEEPOTUS-DEPLOYER"
3. **Note la seed phrase** sur papier, dans un coffre, jamais en photo, jamais cloud
4. **Approvisionne** le wallet avec **3-5 SOL** *(0.02 pour le mint, le reste pour : dev buy initial + fees + mint des futurs lock Jupiter)*
5. **Récupère ton adresse publique** du wallet (44 chars base58) — tu en auras besoin pour les locks plus tard

#### 3.2 Préparer les assets visuels

Sur Emergent ou en local, vérifie que tu as :

| Asset | Chemin actuel | Format Pump.fun |
|---|---|---|
| **Logo carré 512×512** *(token icon)* | `/app/frontend/public/logo_v4_matrix_face.png` | PNG, max 1 MB |
| **Banner X 1500×500** *(optionnel mais conseillé)* | À générer via Phase 2 Nano Banana avec prompt "X header banner $DEEPOTUS" | PNG/JPG |
| **Description courte** *(280 chars)* | À rédiger en bilingue | Pump.fun field "description" |

> 💡 Si tu veux générer le banner X depuis l'admin : `/admin/bots` → Preview → content_type `prophecy` → image toggle ON → ratio `16:9` → ajuste le prompt manuellement si besoin.

**Description Pump.fun proposée (FR + EN combinées)** *(279 chars, copy-paste direct)* :

```
$DEEPOTUS — The Deep State's chosen AI Prophet for World President. Funds a classified Operation: PROTOCOL ΔΣ. Memecoin → Vault → Gencoin (regulated MiCA phase). Pure satire. Highly speculative. Not advice. → deepotus.xyz
```

#### 3.3 Préparer les liens à attacher au token

Au moment du mint, Pump.fun te demande :
- **Website** : `https://deepotus.xyz` *(à condition que [§10](#10-dns-namecheap) soit fait)*
- **Twitter / X** : `https://x.com/deepotus_ai`
- **Telegram** : `https://t.me/deepotus_official` *(à condition que [§4](#4-phase-3-telegram-content-bot) soit fait)*

> ⚠️ **Mint AVANT que ces 3 liens soient prêts** est risqué : Pump.fun n'autorise pas l'édition des liens après création (sauf Pro plan $100/mo). Donc finis [§10](#10-dns-namecheap) + [§4](#4-phase-3-telegram-content-bot) **avant** le mint.

#### 3.4 Choix stratégiques pré-mint

| Question | Recommandation |
|---|---|
| **Dev buy initial ?** | OUI, ~10-20% de la supply en achetant immédiatement après création (snipe protection contre les bots) |
| **Wallet du dev buy ?** | Le **même** wallet "DEEPOTUS-DEPLOYER" — un sniper bot voyant un autre wallet "drainer" la curve va crier scam |
| **Anti-bot delay ?** | Pump.fun n'a pas d'option native. Solution : annonce le mint **simultanément** sur Telegram/X au moment du clic, pas avant |
| **Lock supply ?** | OUI, dès que tu as 30% de la supply, lock 15% team + 30% Treasury via [Jupiter Lock](https://lock.jup.ag) (cf [§3.6](#3-mint-pumpfun)) |

### 🟡 TOI — Jour J : Mint live (15 min total)

#### 3.5 Procédure de mint sur Pump.fun

1. Va sur [pump.fun](https://pump.fun) → connecte ton wallet Phantom (top right)
2. Clique **`Start a new coin`** (gros bouton rose)
3. Remplis le formulaire :

| Champ | Valeur |
|---|---|
| **Token name** | `DEEPOTUS` |
| **Ticker** | `DEEPOTUS` |
| **Description** | *(le texte de §3.2)* |
| **Image** | Upload `logo_v4_matrix_face.png` |
| **Twitter link** | `https://x.com/deepotus_ai` |
| **Telegram link** | `https://t.me/deepotus_official` |
| **Website** | `https://deepotus.xyz` |
| **Banner** *(optionnel)* | Upload ton banner 1500×500 |
| **Buy amount (SOL)** *(optionnel)* | `0.5` à `2` SOL pour le snipe initial |

4. Clique **`Create coin`** → Phantom popup pour signer la transaction (~0.02 SOL fee)
5. Confirme dans Phantom → attends 5-15 secondes
6. Une fois confirmé, Pump.fun t'envoie sur la page de ton token — l'**URL contient le mint address** :
   `https://pump.fun/coin/<TON_MINT_44_CHARS>`
7. **COPIE le mint address immédiatement** (44 chars base58, commence souvent par un chiffre ou une lettre random)

#### 3.6 Lock du Treasury via Jupiter Lock

> Lock = blocage on-chain d'une portion de la supply pour X mois → preuve de non-rugpull, exigée par les holders sérieux.

1. Va sur [lock.jup.ag](https://lock.jup.ag) → connecte ton wallet Phantom
2. **Create lock** :

| Champ | Valeur |
|---|---|
| **Token mint** | `<TON_MINT>` |
| **Recipient** | `<TON_ADRESSE_PUBLIQUE>` *(toi-même, à débloquer plus tard)* |
| **Amount** | 15% de la supply (équipe) |
| **Vesting** | Cliff 6 mois, puis linear sur 12 mois |
| **Cancellable** | NON *(important, un lock cancellable ne compte pas)* |

3. Confirm → tu reçois une **URL publique** style `https://lock.jup.ag/lock/xxxxxx` → **copie-la**
4. Refais l'opération pour 30% Treasury (mêmes paramètres ou cliff plus long)

#### 3.7 Mise à jour env vars Vercel + Render

| Service | Clé | Valeur |
|---|---|---|
| **Vercel** | `REACT_APP_DEEPOTUS_MINT` | `<TON_MINT_44_CHARS>` |
| **Vercel** | `REACT_APP_PUMPFUN_URL` | `https://pump.fun/coin/<TON_MINT>` |
| **Vercel** | `REACT_APP_TEAM_LOCK_URL` | `https://lock.jup.ag/lock/<lock_team>` |
| **Vercel** | `REACT_APP_TREASURY_LOCK_URL` | `https://lock.jup.ag/lock/<lock_treasury>` |

→ Vercel **Redeploy** *(les env vars ne s'appliquent pas à chaud, il faut redéployer)*
→ Le Hero bascule automatiquement sur le mode `🟢 LIVE` ([§2](#2-strategie-countdown))

#### 3.8 Switch Helius vers le vrai mint

→ Voir [§13](#13-helius-prod)

#### 3.9 Vérification rugcheck.xyz

1. Va sur [rugcheck.xyz](https://rugcheck.xyz)
2. Colle ton mint → Analyze
3. **Score attendu : GOOD ou EXCELLENT**
4. Vérifications clés :
   - **Mint authority** : `null` ou `revoked` *(sinon = peut mint à l'infini = scam)*
   - **Freeze authority** : `null` ou `revoked` *(sinon = peut geler les wallets = scam)*
   - **LP locked** : OUI *(ta liquidité est dans la bonding curve Pump.fun, donc verrouillée tant que pas migré)*

> ⚠️ Si le score est "DANGER" ou "WARNING", **NE PROMEUVE PAS le token tant que tu n'as pas compris pourquoi**. Pump.fun par défaut révoque mint + freeze authority — si ce n'est pas le cas, tu as un bug à corriger avec leur support.

#### 3.10 Migration vers Raydium (J + variable)

Pump.fun migre **automatiquement** vers Raydium quand le marketcap atteint **~$69K** (graduation event). Tu n'as **rien à faire** — la liquidité bascule, le LP est burn (locked forever) par Pump.fun. C'est ce qui te donne définitivement le label "rug-resistant".

### ⚠️ PIÈGES Mint

- **Wallet leaks** : ne JAMAIS partager la seed du wallet "DEEPOTUS-DEPLOYER", même par DM officiel — aucun service légitime ne te la demandera
- **Mint trop tôt** : sans Telegram + X + site live, tu cannibalise ton lancement (les sniper bots arrivent avant tes vrais holders)
- **Dev buy trop gros** : >25% de la supply = "dev premine" perçu = rugpull-vibe
- **Liens cassés sur Pump.fun** : ils ne sont **pas éditables après création** sauf Pro plan. Triple-check avant de cliquer Create coin
- **Banner X aux mauvaises dimensions** : Pump.fun crop si ce n'est pas pile 1500×500
- **Description > 280 chars** : Pump.fun tronque, ton ":" stratégique peut sauter
- **Pas de SOL pour les fees** : prévois 5 SOL min sinon tu peux te retrouver bloqué entre mint + lock + dev buy
- **Snipe bots** : 99% des memecoins se font sniper dans les 3 premières secondes. Ton dev buy + annonce simultanée Telegram/X minimisent l'impact

---

## <a id="4-phase-3-telegram-content-bot"></a>4. Phase 3 — Telegram content bot (aiogram)

> Le bot publie automatiquement les prophéties de Phase 2 dans ton canal Telegram, à la fréquence définie dans l'admin.

### 🟡 TOI — Avant que je code (5 min)

#### 4.1 Créer le bot Telegram

1. Sur Telegram, ouvre [@BotFather](https://t.me/BotFather)
2. Tape `/newbot`
3. **Name** : `DEEPOTUS Prophet`
4. **Username** : `deepotus_prophet_bot` *(doit finir par `bot`)*
5. BotFather te renvoie un **token** au format `7891234567:AAH-xxxxx` → **copie-le**
6. Tape `/setdescription` → *"The Prophet's official broadcast channel · PROTOCOL ΔΣ · Not financial advice"*
7. Tape `/setuserpic` → upload `logo_v4_matrix_face.png`
8. Tape `/setprivacy` → **Disable**

#### 4.2 Créer le canal de diffusion

1. Telegram → menu burger → **New Channel**
2. Nom : `$DEEPOTUS · PROTOCOL ΔΣ`
3. Username public : `@deepotus_official`
4. Description : copy ton manifeste court
5. **Add Subscribers** → ajoute `@deepotus_prophet_bot` comme **Admin** avec permissions `Post Messages` + `Edit Messages`

#### 4.3 Récupérer le `chat_id` numérique

1. Envoie un message test depuis ton compte dans le canal
2. Ouvre dans le navigateur :
   `https://api.telegram.org/bot<TON_TOKEN>/getUpdates`
3. Cherche `"chat":{"id":-100xxxxxxxxxx,...}` → copie ce nombre négatif

### ⚠️ PIÈGES Phase 3
- Token leak : ne JAMAIS commit `BOT_TOKEN` dans git
- Bot non-admin : sans `Post Messages` → 403
- Privacy ON : sans `/setprivacy disable`, le bot ignore les replies de groupe
- Aspect ratio image Telegram : 16:9 OK, 1:1 OK, 3:4 cropped

### 🟢 NEO — Une fois token + chat_id reçus (~1h)

```
Backend additions:
  • backend/integrations/telegram_bot.py  (aiogram async)
  • backend/integrations/posters/telegram_poster.py
  • routers/bots.py: POST /admin/bots/post-now {platform:"telegram"}
  • core/bot_scheduler.py: hook sync_jobs_from_config pour activer Telegram
  • requirements.txt: + aiogram>=3.4

Frontend additions:
  • AdminBots.jsx Preview: bouton "🚀 Post to Telegram now"
```

**Env vars Render** :
| Clé | Valeur |
|---|---|
| `TELEGRAM_BOT_TOKEN` | de BotFather |
| `TELEGRAM_CHAT_ID` | numérique du canal |
| `TELEGRAM_PARSE_MODE` | `MarkdownV2` |

---

## <a id="5-phase-4-x-twitter-posting-bot"></a>5. Phase 4 — X / Twitter posting bot (Tweepy)

### 🟡 TOI — Compte X Developer (15-30 min)

#### 5.1 Subscribe Basic plan ($200/mo)

1. Connecte-toi avec **@deepotus_ai** sur [developer.x.com/en/portal/dashboard](https://developer.x.com/en/portal/dashboard)
2. Souscris **Basic ($200/mo)** *(le Free tier est insuffisant)*
3. Crée un **Project** : `DEEPOTUS Prophet`
4. Crée une **App** : `deepotus-poster`
5. **User authentication settings** :
   - App permissions : `Read and write`
   - Type : `Web App, Automated App or Bot`
   - Callback URL : `https://deepotus.xyz/admin/bots/x/callback`
   - Website URL : `https://deepotus.xyz`

#### 5.2 Récupérer les 5 credentials

| Credential | Section | Format |
|---|---|---|
| `X_API_KEY` | API Key and Secret → API Key | `AbCdEfGh1234567890` |
| `X_API_SECRET` | API Key and Secret → API Key Secret | 50+ chars |
| `X_BEARER_TOKEN` | Bearer Token | 80+ chars |
| `X_ACCESS_TOKEN` | Access Token and Secret → Access Token | `123-Ab...` |
| `X_ACCESS_TOKEN_SECRET` | Access Token Secret | 45 chars |

> ⚠️ Génère l'Access Token APRÈS Read+Write sinon il sera read-only.

### ⚠️ PIÈGES Phase 4
- Free = useless (pas de post automatique)
- Permissions read-only → regen Access Token après Read+Write
- Image upload requires v1.1 + v2 combo
- Char limit 280 → Phase 2 truncate à 270
- 403 = 95% des cas = perms ou Access Token pas regen
- 429 Rate Limit = Basic 1500 posts/mois (50/jour) → on en fait 6 OK

### 🟢 NEO — Une fois 5 credentials reçus (~1.5h)

```
Backend additions:
  • backend/integrations/x_client.py  (Tweepy async OAuth1 + media)
  • backend/integrations/posters/x_poster.py
  • routers/bots.py: POST /admin/bots/post-now {platform:"x"}
  • core/bot_scheduler.py: scheduled X jobs
  • requirements.txt: + tweepy>=4.14
```

**Env vars Render** :
```
X_API_KEY=...
X_API_SECRET=...
X_BEARER_TOKEN=...
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...
```

---

## <a id="6-phase-5-x-kol-listener"></a>6. Phase 5 — X KOL mentions listener

### 🟡 TOI — Liste KOLs

Donne-moi 3 à 10 handles X. Exemples :

| Handle | Pourquoi |
|---|---|
| `@SolanaFloor` | Sentiment Solana |
| `@pumpdotfun` | Plateforme launch |
| `@ansemf` | KOL Solana memecoin |
| `@JupiterExchange` | DEX agrégateur |
| `@aeyakovenko` | Co-fondateur Solana |
| `@FartCoinSOL` | Memecoin culture |

#### 6.2 Mode de modération (à choisir)
- **a) Approbation manuelle** *(recommandé)* : queue admin avant chaque post
- **b) Auto-post avec score min** : LLM auto-évalue safeness 0-10, post si ≥ 8
- **c) Hybride** : auto pour prophecy/market, approbation pour kol_reply

### ⚠️ PIÈGES Phase 5
- Filtered Stream v2 → Basic+ obligatoire
- Cooldown 1 reply/KOL/24h sinon ban
- Detection sarcasme imparfaite → queue admin = ta safety
- Mention loops (ignore tes propres replies)
- MiCA : aucune réponse "buy now" / "10x guaranteed"

### 🟢 NEO — Une fois liste reçue (~2.5h)

```
Backend:
  • backend/integrations/x_listener.py (filtered stream v2 async)
  • core/kol_queue.py (Mongo collection 'kol_queue')
  • routers/bots.py:
    GET /admin/bots/kol-queue
    POST /admin/bots/kol-queue/{id}/approve
    POST /admin/bots/kol-queue/{id}/reject
    PUT /admin/bots/config/kol_targets

Frontend:
  • AdminBots.jsx: nouvel onglet "KOL Queue"
```

---

## <a id="7-telegram-trading-bot"></a>7. Telegram TRADING bot — Maestro / BonkBot / Trojan

> ⚠️ **Important** : "Telegram trading bot" = **bots tiers existants**. On ne dev pas, on **liste** $DEEPOTUS dessus.

| Bot | Lien | Force | Faiblesse | Volume mensuel |
|---|---|---|---|---|
| **BonkBot** | [@BONKbot_bot](https://t.me/BONKbot_bot) | Plus utilisé Solana, simple | Frais 1% | ~$300M/mo |
| **Maestro** | [@MaestroSniperBot](https://t.me/MaestroSniperBot) | Multi-chain, copy trading | Plus complexe | ~$150M/mo |
| **Trojan** | [@solana_trojanbot](https://t.me/solana_trojanbot) | Sniper + auto-buy | UI moins propre | ~$100M/mo |

### 🟡 TOI — Setup post-launch (30 min)

#### 7.1 Listing automatique (rien à faire)

Dès que ton mint est sur Pump.fun puis migre Raydium, ces 3 bots détectent automatiquement et le rendent tradable. Aucune action.

#### 7.2 Liens d'affiliation

| Bot | Comment |
|---|---|
| **BonkBot** | `/start` → Settings → Referrals → copy. *Pas de revenue share, juste tracking.* |
| **Maestro** | `/start` → Refer → copy. **35% revenue share 6 mois** |
| **Trojan** | `/start` → Referrals → Generate. **35% payer / 25% referrer** |

#### 7.3 Intégration site

🟢 **NEO peut faire** : ajout d'un bloc "Trade $DEEPOTUS in 1 click on Telegram" sur `/how-to-buy` avec les 3 logos + boutons + bannière "Powered by community trading bots — none endorsed by $DEEPOTUS". Donne-moi les 3 ref links et c'est fait en 30 min.

### ⚠️ PIÈGES Phase 7
- MiCA : promo d'outils tiers, low risk si disclaimer
- Jamais demander seed phrase
- Slippage défaut trop bas → 2-5% sur memecoin
- Honeypot : check rugcheck.xyz BEFORE promoting

> 💡 **Custom Telegram trading bot** = déconseillé : custodial wallets, audit sécurité ($10K), license CASP MiCA. Reste sur les 3 ci-dessus.

---

## <a id="8-deploy-backend-render"></a>8. Déploiement Backend → Render

### 🟡 TOI — Préparation repo (15 min)

#### 8.1 Download code Emergent + push GitHub

1. Emergent dashboard → ton projet → **Download Code** → `.zip`
2. [github.com/new](https://github.com/new) → repo `deepotus-prod` → **Private** ✅
3. ```bash
   unzip deepotus-source.zip && cd deepotus
   git init && git add . && git commit -m "initial production push"
   git branch -M main
   git remote add origin git@github.com:<TON_USER>/deepotus-prod.git
   git push -u origin main
   ```

#### 8.2 Vérifie qu'aucune clé n'est commitée

```bash
grep -rE "EMERGENT_LLM_KEY|RESEND_API_KEY|HELIUS_API_KEY|MONGO_URL" \
  --include="*.py" --include="*.js" --include="*.json"
# Doit retourner SEULEMENT des os.environ.get() / process.env, JAMAIS la valeur
```

### 🟡 TOI — Setup Render (15 min)

#### 8.3 Service Web

1. [dashboard.render.com](https://dashboard.render.com) → **New +** → **Web Service**
2. Connect repo `deepotus-prod`
3. **Configure** :

| Champ | Valeur |
|---|---|
| **Name** | `deepotus-api` |
| **Region** | `Frankfurt (EU Central)` |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn server:app --host 0.0.0.0 --port $PORT --workers 1` |
| **Instance Type** | **Starter ($7/mo)** ⚠️ |

#### 8.4 Environment Variables

```bash
# === MongoDB Atlas (voir §11) ===
MONGO_URL=mongodb+srv://deepotus_api:<password>@cluster0.xxxxx.mongodb.net/deepotus?retryWrites=true&w=majority
DB_NAME=deepotus

# === CORS (à ajuster après §10) ===
CORS_ORIGINS=https://deepotus.xyz,https://www.deepotus.xyz

# === LLM ===
EMERGENT_LLM_KEY=<ta_clé_actuelle>
EMERGENT_IMAGE_LLM_KEY=<ta_DEUXIÈME_clé_pour_les_images>  # optionnel mais recommandé

# === Admin auth ===
ADMIN_PASSWORD=<MOTDEPASSE_LONG_ET_ALEATOIRE_CHANGE_LE>
JWT_SECRET=<openssl rand -hex 32 — généré localement>

# === Resend (voir §12) ===
RESEND_API_KEY=<ta_clé_actuelle>
SENDER_EMAIL=wcu@deepotus.xyz
PUBLIC_BASE_URL=https://deepotus.xyz
RESEND_WEBHOOK_SECRET=<ta_clé_actuelle>

# === Helius (voir §13) ===
HELIUS_API_KEY=<ta_clé_actuelle>
HELIUS_WEBHOOK_AUTH=<ta_clé_actuelle>

# === Launch ===
DEEPOTUS_LAUNCH_ISO=2026-09-07T14:00:00+00:00

# === Telegram (Phase 3 — ajouter plus tard) ===
# TELEGRAM_BOT_TOKEN=
# TELEGRAM_CHAT_ID=

# === X (Phase 4 — ajouter plus tard) ===
# X_API_KEY=
# X_API_SECRET=
# X_BEARER_TOKEN=
# X_ACCESS_TOKEN=
# X_ACCESS_TOKEN_SECRET=
```

#### 8.5 Deploy

1. **Create Web Service** → build ~3-4 min
2. URL : `https://deepotus-api.onrender.com`
3. ```bash
   curl https://deepotus-api.onrender.com/api/stats
   ```

### ⚠️ PIÈGES Render

- Free tier spin-down → toujours Starter+
- ModuleNotFoundError → `pip freeze > backend/requirements.txt`
- Mongo refused → autorise `0.0.0.0/0` Atlas
- Webhook 502 → secret matché entre Render env + Helius

---

## <a id="9-deploy-frontend-vercel"></a>9. Déploiement Frontend → Vercel

### 🟡 TOI — Setup (10 min)

1. [vercel.com/new](https://vercel.com/new) → import `deepotus-prod`
2. **Configure** :

| Champ | Valeur |
|---|---|
| **Framework Preset** | `Create React App` |
| **Root Directory** | `frontend` |
| **Build Command** | `yarn build` *(défaut)* |
| **Output Directory** | `build` *(défaut)* |
| **Install Command** | `yarn install` *(défaut)* |

3. **Environment Variables** :

| Clé | Valeur initiale | Quand mettre à jour |
|---|---|---|
| `REACT_APP_BACKEND_URL` | `https://api.deepotus.xyz` | Après [§10](#10-dns-namecheap) |
| `REACT_APP_PUMPFUN_URL` | *(vide)* | Après mint [§3.7](#3-mint-pumpfun) |
| `REACT_APP_DEEPOTUS_MINT` | *(vide)* | Après mint [§3.7](#3-mint-pumpfun) |
| `REACT_APP_TEAM_LOCK_URL` | *(vide)* | Après lock Jupiter [§3.6](#3-mint-pumpfun) |
| `REACT_APP_TREASURY_LOCK_URL` | *(vide)* | Après lock Jupiter [§3.6](#3-mint-pumpfun) |

4. Deploy → preview `https://deepotus-prod.vercel.app`

### ⚠️ PIÈGES Vercel

- 404 sur `/admin` → `frontend/vercel.json` :
  ```json
  { "rewrites": [{ "source": "/(.*)", "destination": "/" }] }
  ```
- Env var changée mais pas appliquée → **Redeploy**
- Mixed content blocked si `REACT_APP_BACKEND_URL=http://...`
- Watermark "Made with Emergent" : SEULEMENT sur preview Emergent. Sur Vercel = AUCUN

---

## <a id="10-dns-namecheap"></a>10. DNS Namecheap → deepotus.xyz

### 🟡 TOI — Configuration (10 min + 30 min propag)

#### 10.1 Custom domain Vercel

1. Vercel → ton projet → **Settings** → **Domains** → Add `deepotus.xyz`
2. Vercel te donne :
   - **A record** : `76.76.21.21`
   - **CNAME** : `cname.vercel-dns.com`
3. Add aussi `www.deepotus.xyz` (Vercel auto-redirect)

#### 10.2 Custom domain Render

1. Render → `deepotus-api` → **Settings** → **Custom Domains** → Add `api.deepotus.xyz`
2. Render te donne un CNAME `xxxxx.onrender.com`

#### 10.3 Namecheap Advanced DNS

1. Namecheap → **Domain List** → `deepotus.xyz` → **Manage**
2. **Advanced DNS** → supprime tous les records existants sauf NS
3. **Add** :

| Type | Host | Value | TTL |
|---|---|---|---|
| **A Record** | `@` | `76.76.21.21` *(Vercel)* | Auto |
| **CNAME** | `www` | `cname.vercel-dns.com` *(Vercel)* | Auto |
| **CNAME** | `api` | `<le_cname_render>` | Auto |

#### 10.4 Vérifier propagation

```bash
dig deepotus.xyz +short        # → 76.76.21.21
dig www.deepotus.xyz +short    # → cname.vercel-dns.com.
dig api.deepotus.xyz +short    # → IP Render
curl https://api.deepotus.xyz/api/stats  # → JSON
```

#### 10.5 Update CORS + REACT_APP_BACKEND_URL

1. Render env `CORS_ORIGINS` → `https://deepotus.xyz,https://www.deepotus.xyz`
2. Vercel env `REACT_APP_BACKEND_URL` → `https://api.deepotus.xyz`
3. **Redeploy** les deux

### ⚠️ PIÈGES DNS

- TTL > 1h → bloque Cloudflare future
- SSL Pending > 1h → re-add le domain
- AAAA IPv6 facultatif
- MX records existants supprimés en 10.3 → check email
- DNSSEC laisse off

---

## <a id="11-mongodb-atlas"></a>11. MongoDB Atlas — base de prod

### 🟡 TOI — Setup (15 min)

1. [cloud.mongodb.com/v2/register](https://cloud.mongodb.com/v2/register)
2. **Build a Database** → **M0 Free**
3. Provider **AWS** · Region **eu-west-1 (Ireland)**
4. Cluster name `deepotus-prod`
5. **Database Access** → New User : `deepotus_api` + password 32 chars (alphanumérique seulement, sinon URL-encoding)
6. Built-in Role : `Read and write to any database`
7. **Network Access** → Add IP → `0.0.0.0/0`
8. **Database** → Connect → **Drivers** Python → connection string
9. Format final : `mongodb+srv://deepotus_api:<password>@deepotus-prod.xxxxx.mongodb.net/deepotus?retryWrites=true&w=majority`

### ⚠️ PIÈGES Atlas

- Password URL-encoding : `@` → `%40`, `/` → `%2F`. Génère sans caractères spéciaux
- Cluster pause après 60 jours d'inactivité (M0)
- 5 GB hard limit M0 → upgrade M10 à 100K MAU
- Backup : seulement à partir de M10

---

## <a id="12-resend-dkim"></a>12. Resend — DKIM / SPF / domaine

### 🟡 TOI — Setup (15 min + 1h propag)

#### 12.1 Add domain Resend

1. [resend.com/domains](https://resend.com/domains) → Add Domain → `deepotus.xyz`
2. Resend te donne ~6 records DNS

#### 12.2 Add records dans Namecheap

| Type | Host | Value | TTL |
|---|---|---|---|
| `MX` | `send` | `feedback-smtp.eu-west-1.amazonses.com` (priority 10) | Auto |
| `TXT` | `send` | `v=spf1 include:amazonses.com ~all` | Auto |
| `TXT` | `resend._domainkey` | *(long DKIM Resend)* | Auto |
| `TXT` | `_dmarc` | `v=DMARC1; p=none; rua=mailto:dmarc@deepotus.xyz` | Auto |

> Copie-colle EXACT depuis Resend, jamais à la main.

#### 12.3 Verify

1. Resend → ton domaine → **Verify** → status Verified en 5-30 min
2. Update Render `SENDER_EMAIL=wcu@deepotus.xyz`

### ⚠️ PIÈGES Resend

- SPF conflicts avec Google Workspace : merge en un seul record
  `v=spf1 include:_spf.google.com include:amazonses.com ~all`
- DMARC trop strict : commence `p=none`, monte à `p=quarantine` après 30 jours
- DKIM key trop long : Namecheap UI tronque, edit en raw mode

---

## <a id="13-helius-prod"></a>13. Helius — passage en mode prod (vrai mint)

### 🟡 + 🟢 — Procédure (5 min après le mint)

#### 13.1 Récupère le mint

Cf [§3.5](#3-mint-pumpfun) — copié au moment du Create coin Pump.fun.

#### 13.2 Update Vercel env vars

Cf [§3.7](#3-mint-pumpfun).

#### 13.3 Reconfigure Helius webhook

1. Va sur `https://deepotus.xyz/admin/vault`
2. Section **Helius indexer** → **Register mint**
3. Colle le mint → submit
4. Le système :
   - Désactive `helius_demo_mode`
   - Update Helius webhook avec le nouveau mint
   - Reset les compteurs vault à 0
5. Vérifie que les premiers swaps apparaissent et incrémentent les dials

#### 13.4 Renforce le webhook auth

```bash
openssl rand -hex 32
# 1. Update Render: HELIUS_WEBHOOK_AUTH=<new_secret>
# 2. Update Helius dashboard → ton webhook → Auth Header: <new_secret>
```

### ⚠️ PIÈGES Helius
- Mint typo → vault qui ne bouge jamais
- Webhook signature mismatch → 401 sur tous events
- Quota Free 100K req/mo
- Demo mode oublié → vérifier `helius_demo_mode` flag dans Mongo `vault_state`

---

## <a id="14-admin-docs"></a>14. Documentation Admin — comment piloter le site

> Le dashboard admin est accessible sur `https://deepotus.xyz/admin` (pas de lien public depuis le site, URL à connaître).

### 14.1 Login

1. Va sur `https://deepotus.xyz/admin`
2. Entre ton `ADMIN_PASSWORD` *(défini en env Render)*
3. Si 2FA activé → entre le code 6 chiffres TOTP
4. Tu reçois un **JWT** valide 24h, stocké dans `localStorage` *(automatique)*

### 14.2 Architecture des 4 modules

```
/admin                  → Tableau de bord principal (whitelist + emails events + 2FA)
/admin/vault            → Pilotage du Coffre PROTOCOL ΔΣ (Helius, dials, vault state)
/admin/emails           → Logs Resend détaillés
/admin/bots             → Bot fleet (Phase 1+2+6) — kill-switch + LLM + preview
```

---

### 14.3 Module `/admin` — Dashboard principal

#### Sections

| Section | Description | Actions disponibles |
|---|---|---|
| **Overview** | KPIs : whitelist count, emails sent, vault state, AI usage | Read-only |
| **Whitelist** | Liste tous les emails inscrits sur le site | Add manuel · Export CSV · Resend email à un user · **Move to blacklist** |
| **Blacklist** | Emails bloqués (cooldown ou abus) | Add raison + cooldown_days · Restaurer |
| **Email events** | Historique Resend webhook (sent / delivered / bounced / complained) | Filter par status |
| **2FA setup** | Activer/désactiver 2FA pour ton compte admin | Cf [§15](#15-securite) |
| **Sessions** | Liste des sessions admin actives (JWT non révoqués) | Revoke session par jti |

#### Workflows typiques

**A. Quelqu'un s'inscrit à la whitelist** :
1. L'email part dans `whitelist` collection
2. Resend envoie l'email d'accueil
3. Tu vois la nouvelle entrée + status email en temps réel sur ce dashboard

**B. Un email rebondit** :
1. Resend webhook nous notifie `email.bounced`
2. L'entrée passe en `email_status: bounced` rouge
3. Tu peux soit retry, soit blacklist l'email

**C. Quelqu'un abuse du formulaire (spam)** :
1. Tu cliques **Move to blacklist** sur sa ligne
2. Choisis raison (`abuse`, `spam`, `manual`) + cooldown (7/30/365 jours)
3. Le formulaire de whitelist refuse cet email pendant la période

---

### 14.4 Module `/admin/vault` — PROTOCOL ΔΣ

> Pilotage on-chain et présentation publique du Coffre.

#### Sections

| Section | Description | Actions |
|---|---|---|
| **Vault state** | Stage actuel (PRE_LAUNCH / LIVE / FINAL), dials_locked count, micro_ticks_total | Manuel reset (debug) |
| **Helius indexer** | Status webhook, dernière swap reçue, mode (demo/prod) | **Register mint** · Toggle demo_mode · Refresh registration |
| **Vault dials** | Les 6 cadrans (chacun a un seuil de micro-ticks pour s'ouvrir) | **Override dial** : forcer ouverture/fermeture (URGENCE) · Edit thresholds |
| **Vault presets** | Configurations pré-définies (mode démo BONK, mode launch, mode prod) | Switch preset en 1 clic |
| **Public stats** | Ce qui s'affiche sur la page publique `/classified-vault` | Edit narrative public |

#### Workflows critiques

**A. Au moment du mint $DEEPOTUS** :
1. Cf [§13](#13-helius-prod) — Register mint
2. Vérifie que `helius_demo_mode = false`
3. Observe les premiers ticks arriver dans les 30s post-mint

**B. Un cadran ne s'ouvre pas malgré assez de volume** :
1. Va dans Vault state → check `micro_ticks_total`
2. Compare au seuil du cadran dans Vault dials
3. Si le seuil est mal configuré : edit threshold
4. Si tout semble OK : check Helius webhook logs *(events arrivent ? signature valide ?)*

**C. Tu veux faire une démo presse / investor avant le mint** :
1. Active un preset démo (BONK live ticks)
2. Le Vault s'incrémente avec du vrai trafic on-chain de BONK (high volume)
3. Tu peux faire un demo run et reset après

---

### 14.5 Module `/admin/emails` — Resend logs

#### Sections

- Logs détaillés de chaque email (sender, recipient, subject, body preview, status)
- Filter par status / date / recipient
- Re-send un email depuis l'UI
- Export CSV pour analyse marketing

#### Workflows

**A. Audit MiCA** *(important pour la phase régulée)* : tous les emails sont loggés ad vitam, exportable en CSV pour ton DPO / régulateur.

---

### 14.6 Module `/admin/bots` — Bot fleet (Phases 1+2+6 implémentées)

> Pilotage complet des bots Telegram + X (publication automatique de prophéties).

#### Header

- **Kill-switch hero** (rouge si ON, vert si OFF) avec deux boutons : `Release` / `Arm`
- **Refresh button**
- **Back to /admin**

#### 4 Tabs

##### 14.6.1 Tab `Config`

| Bloc | Contrôles |
|---|---|
| **Platforms · X / Twitter** | Toggle enabled · Frequency (heures, 1-48) |
| **Platforms · Telegram** | Toggle enabled · Frequency (heures, 1-48) |
| **Content modes** | 4 toggles : prophecy, market_commentary, vault_update, kol_reply |
| **LLM preset** | Dropdown : Claude Sonnet 4.5 / GPT-4o / GPT-5 / Gemini 2.5 Pro / Custom |
| **Heartbeat interval** | Input minutes (1-1440) |
| **Max posts / day** | Input (0-500) |

> 💡 Tous les changements sont **persistants** sur Mongo dès le blur/click + reschedulent les jobs APScheduler en live.

##### 14.6.2 Tab `Preview`

> Génère du contenu en mode dry-run (PAS publié). Idéal pour tester ton voicing avant d'enable les platforms.

**Studio input** :
- Content type dropdown (4 archétypes)
- Platform dropdown (X 270 chars / Telegram 800 chars)
- KOL tweet body *(uniquement si type = kol_reply)*
- **Toggle Nano Banana illustration** + aspect ratio (16:9 / 3:4 / 1:1)
- Bouton "Generate text + illustration"

**Prophet output** :
- Bloc FR avec compteur chars
- Bloc EN avec compteur chars
- Hashtags + emoji
- **Image inline** (data URI) + bouton Download
- Footer model utilisé

##### 14.6.3 Tab `Jobs`

- Liste les jobs APScheduler en mémoire (heartbeat + plus tard X / Telegram)
- Pour chaque : ID, trigger, next run time, max instances, coalesce flag
- Auto-refresh 10s

##### 14.6.4 Tab `Logs`

- Histogramme par status : heartbeat / posted / killed / skipped / failed
- Filtres : platform (X / Telegram / system) · status
- Table 30 entrées paginées avec timestamp, content preview, error si fail
- Auto-refresh 10s

#### Workflows critiques

**A. Lancement bot Telegram (Phase 3)** :
1. Set env vars Render `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` *(redeploy auto)*
2. `/admin/bots` → Config tab → toggle Telegram **ON**
3. Genère un preview en Telegram → vérifier que le ton est OK
4. Fais un **test post manuel** (bouton apparaîtra une fois Phase 3 codée)
5. Si OK → kill-switch **Release** → premier post auto dans (frequency_hours)

**B. Crisis lockdown** *(le bot vient de poster une connerie)* :
1. `/admin/bots` → Hero → **Arm kill-switch** (rouge)
2. Tous les jobs en cours sont killed (status `killed` dans logs)
3. Tu prends ton temps pour fix le system prompt
4. Tu redémarre via **Release** quand prêt

**C. Switch de modèle LLM si Claude est down** :
1. Config → LLM preset → switch sur GPT-4o (OpenAI)
2. Apply auto, prochains posts utilisent OpenAI

**D. Audit du dernier mois** :
1. Logs tab → filter `status = posted`
2. Export Mongo `bot_posts` collection si tu veux du detail (CSV via mongoexport)

---

## <a id="15-securite"></a>15. Sécurité — changer mdp, activer 2FA, révoquer sessions

### 15.1 Changer le mot de passe admin

> ⚠️ Le mot de passe admin n'est PAS stocké en DB hashé — il est dans l'env var Render `ADMIN_PASSWORD`. Pour le changer :

#### Procédure

1. Render dashboard → `deepotus-api` → **Environment**
2. Edit `ADMIN_PASSWORD` → nouvelle valeur (≥ 24 chars, mix alphanumérique + symboles)
3. **Save Changes** → Render redéploie automatiquement (~1-2 min)
4. **Logout** dans `/admin` (top-right) puis re-login avec le nouveau mdp
5. **Toutes les sessions JWT existantes** restent valides 24h (le hash mdp n'est pas dans le JWT) → si tu veux force-logout : passe à [§15.3](#15-securite)

#### Recommandations
- Mot de passe ≥ 24 chars, généré via password manager (1Password, Bitwarden)
- Rotation : changer tous les 90 jours
- Si suspicion de leak : changer + révoquer sessions ([§15.3](#15-securite)) + regen `JWT_SECRET`

### 15.2 Activer le 2FA TOTP

> Implémenté avec PyOTP (RFC 6238) — compatible Google Authenticator, Authy, 1Password, etc.

#### Setup (1ère fois)

1. Login sur `/admin` (sans 2FA)
2. Top-right → **Activer 2FA** *(modal s'ouvre)*
3. **Étape 1** : ouvre ton authenticator app (Authy / Google Auth / 1Password) → scan le QR code affiché OU copie le secret base32
4. **Étape 2** : entre le **code 6 chiffres** que ton app génère
5. Submit → si valide, 2FA est activé sur ton compte
6. **IMPORTANT** : copie les **8 codes de récupération** affichés une seule fois (utilisable si tu perds ton phone). Stocke dans password manager.

#### Login avec 2FA actif

1. Entre password
2. Entre code 6 chiffres TOTP du moment
3. Reçois JWT

#### Désactivation

Si tu changes de phone et que tu n'as pas backup :
1. Logout
2. Login avec un **code de récupération** (à la place du TOTP)
3. Top-right → **Désactiver 2FA**
4. Re-setup avec le nouveau phone

#### ⚠️ PIÈGES 2FA
- **Time drift** : si l'horloge de ton phone est désync de plus de 30s, le code est rejeté. Active "Set time automatically"
- **Backup codes perdus + phone perdu** : seul recours = SSH dans Render → modifier la collection `admin_2fa` Mongo manuellement (ne te mets pas dans cette situation)

### 15.3 Révoquer toutes les sessions

> Si tu suspectes qu'un JWT a leak (ex. tu as oublié ton laptop dans un café) :

#### Méthode A — Via UI (recommandé)

1. `/admin` → section **Sessions** (visible si > 1 session active)
2. Click **Revoke all** → toutes les sessions JWT (sauf la courante) sont marquées révoqués en DB
3. Les autres clients perdent l'accès au prochain refresh

#### Méthode B — Force par regen JWT_SECRET (nuke)

1. ```bash
   openssl rand -hex 32
   ```
2. Render env → `JWT_SECRET` = nouvelle valeur
3. Save → redeploy auto
4. **TOUS** les JWT actuels deviennent invalides (toi inclus → tu dois re-login)

### 15.4 Audit log des accès admin

Toutes les sessions admin sont loggées dans Mongo collection `admin_sessions` avec :
- `jti` (JWT ID unique)
- `created_at`
- `last_seen` *(updated à chaque request authentifié)*
- `ip_address`
- `revoked` (boolean)

Pour audit : connecte-toi à Atlas → Browse Collections → `admin_sessions` → filter par date/IP.

### 15.5 Bonnes pratiques générales

- ✅ Activer 2FA dès le J1 prod
- ✅ Mot de passe stocké uniquement dans password manager
- ✅ Backup codes 2FA stockés séparément
- ✅ Whitelist IP MongoDB Atlas (passer à Render Pro pour IP statique → $25/mo)
- ✅ Rotate `JWT_SECRET` tous les 90 jours
- ✅ Surveiller `admin_sessions` collection pour IPs inattendues
- ❌ Ne jamais partager le mot de passe (même par DM officiel)
- ❌ Ne jamais commit `.env` ou `ADMIN_PASSWORD` dans git
- ❌ Ne jamais utiliser le même password sur Render / Atlas / autre

---

## <a id="16-post-deploy"></a>16. Post-deploy checklist + Go-Live D-day

### J-7 (avant launch)

- [ ] DNS deepotus.xyz propagé (`dig` retourne IPs correctes sur les 3 hosts)
- [ ] SSL actif sur `deepotus.xyz`, `www`, `api`
- [ ] Resend domain Verified
- [ ] Test email whitelist : reçu signé `wcu@deepotus.xyz` dans inbox (pas spam)
- [ ] `/admin` login OK
- [ ] **2FA activé sur ton compte admin** ([§15.2](#15-securite))
- [ ] `/admin/bots` : kill-switch ON, generate text + image preview OK
- [ ] Backend logs Render : pas de 500 récurrents
- [ ] Mongo Atlas : collections présentes (`whitelist`, `vault_state`, `bot_config`, `bot_posts`)

### J-3 (lancement bots Phases 3+4 si credentials prêts)

- [ ] Bot Telegram admin du canal, test post manuel via admin OK
- [ ] X bot test post via admin OK (visible @deepotus_ai)
- [ ] Kill-switch OFF, observe 1 cycle complet (4-6h)
- [ ] Logs `bot_posts` montrent `posted` (pas `failed`)

### J-Day (mint $DEEPOTUS)

Cf [§3](#3-mint-pumpfun) procédure complète

- [ ] Wallet "DEEPOTUS-DEPLOYER" prêt avec 5 SOL
- [ ] Logo + banner + description prêts
- [ ] Liens (site + X + Telegram) tous LIVE
- [ ] Mint Pump.fun → copy mint address
- [ ] Lock 15% team + 30% Treasury via Jupiter Lock
- [ ] Update Vercel env vars (mint + pumpfun + locks) + Redeploy
- [ ] `/admin/vault` → Register mint Helius
- [ ] rugcheck.xyz → score GOOD
- [ ] Annonce simultanée Telegram + X bot (manual ou via admin)
- [ ] Add ref links BonkBot/Maestro/Trojan sur `/how-to-buy`

### J+1 (monitoring)

- [ ] Vault dials : combien sont déverrouillés ?
- [ ] Whitelist : nb d'emails reçus dans la journée
- [ ] Posts X + Telegram engagement
- [ ] Render bandwidth + CPU/RAM stables
- [ ] **Premier scan rugcheck.xyz post-migration** quand le marketcap atteint $69K et migre Raydium

---

## <a id="17-recap-final"></a>17. Récap final — qui fait quoi, dans quel ordre

| # | Étape | Acteur | Durée | Bloque |
|---|---|---|---|---|
| 1 | [Créer GitHub privé + push code](#8-deploy-backend-render) | 🟡 TOI | 15 min | tout |
| 2 | [Créer MongoDB Atlas](#11-mongodb-atlas) | 🟡 TOI | 15 min | Render |
| 3 | [Créer Render service + env vars](#8-deploy-backend-render) | 🟡 TOI | 30 min | rien |
| 4 | [Créer Vercel project + env vars](#9-deploy-frontend-vercel) | 🟡 TOI | 15 min | rien |
| 5 | [Custom domains Vercel + Render](#10-dns-namecheap) | 🟡 TOI | 5 min | DNS |
| 6 | [Config DNS Namecheap](#10-dns-namecheap) | 🟡 TOI | 5 min + 30min propag | tout |
| 7 | [Update CORS + REACT_APP_BACKEND_URL](#10-dns-namecheap) | 🟡 TOI | 5 min | rien |
| 8 | [Resend DKIM/SPF](#12-resend-dkim) | 🟡 TOI | 15 min + 1h propag | emails |
| 9 | [Activer 2FA admin sur prod](#15-securite) | 🟡 TOI | 5 min | sécu |
| 10 | **Test post-deploy checklist J-7** | 🟡 TOI | 30 min | go-live |
| 11 | [Créer bot Telegram BotFather](#4-phase-3-telegram-content-bot) | 🟡 TOI | 10 min | Phase 3 |
| 12 | **Phase 3 — Implémentation Telegram** | 🟢 NEO | ~1h | rien |
| 13 | [Créer compte X Developer Basic](#5-phase-4-x-twitter-posting-bot) | 🟡 TOI | 30 min + paiement | Phase 4 |
| 14 | **Phase 4 — Implémentation X posting** | 🟢 NEO | ~1.5h | rien |
| 15 | [Donner liste KOLs](#6-phase-5-x-kol-listener) | 🟡 TOI | 5 min | Phase 5 |
| 16 | **Phase 5 — KOL listener + queue** | 🟢 NEO | ~2.5h | rien |
| 17 | [Préparer wallet + assets pré-mint](#3-mint-pumpfun) | 🟡 TOI | 1h | mint |
| 18 | [Mint $DEEPOTUS sur Pump.fun](#3-mint-pumpfun) | 🟡 TOI | 15 min | go-live |
| 19 | [Lock 15% team + 30% Treasury Jupiter Lock](#3-mint-pumpfun) | 🟡 TOI | 10 min | trust |
| 20 | [Update env vars Vercel mint+locks + Redeploy](#3-mint-pumpfun) | 🟡 TOI | 5 min | site live |
| 21 | [Helius register mint](#13-helius-prod) | 🟡 + 🟢 | 5 min | vault |
| 22 | [Get ref links BonkBot/Maestro/Trojan + intégration](#7-telegram-trading-bot) | 🟡 + 🟢 | 30 min | rien |

---

## <a id="18-couts"></a>18. Coûts mensuels estimés

| Service | Plan | Coût mensuel | Quand activer |
|---|---|---|---|
| GitHub | Free | 0 € | J0 |
| Vercel | Hobby | 0 € | J0 |
| Render | Starter | **7 $ (~6.50 €)** | J0 |
| MongoDB Atlas | M0 Free | 0 € | J0 |
| Resend | Free | 0 € | J0 |
| Helius | Free Dev | 0 € | J0 |
| Namecheap | renew deepotus.xyz | ~10 €/an | déjà payé |
| Pump.fun mint fee | one-time | ~$5 (0.02 SOL) | mint |
| Jupiter Lock | one-time | ~$2 (0.01 SOL) | post-mint |
| Emergent LLM Key (texte) | Pay-per-use | ~5-30 €/mo | J0 |
| Emergent LLM Key (image) | Pay-per-use | ~5-50 €/mo | J0 |
| **Total minimum** | | **~12 €/mo** | |
| **+ Phase 4 X Basic** | | **+ 200 $/mo** | optionnel |

> 💡 Si X Basic $200/mo est trop cher : mode "manuel-assisté" disponible (bot prépare, toi cliques Approve depuis ton phone X app).

---

## ✅ Conclusion

Ce document couvre l'intégralité de ce qui reste : mint, déploiement, finition bots, administration, sécurité.

**Action immédiate suggérée** :
1. **Commencer immédiatement** par les étapes 1-10 du [récap](#17-recap-final) — déploiement complet sans attendre Phase 3/4/5
2. **En parallèle** : créer wallet + acheter SOL ([§3.1](#3-mint-pumpfun)) — peut prendre des heures pour confirmation bancaire
3. **Quand tout est live** : pinger Neo avec credentials Telegram (Phase 3), puis X (Phase 4+5)
4. **Quand prêt à mint** : suivre [§3](#3-mint-pumpfun) pas-à-pas

**Pour toute question pendant l'exécution** : ping-moi avec le numéro d'étape et le message d'erreur exact, je débogue en live.

— Neo
