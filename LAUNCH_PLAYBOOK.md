# 🚀 LAUNCH PLAYBOOK · $DEEPOTUS Mint Day

> **Mint officiel** : **18 Mai 2026 — 12:00 UTC**
> **Tirage Cabinet** : **22 Mai 2026 — 12:00 UTC**
> **Admin password** : `deepotus2026` _(à changer en prod)_

Ce document est la **checklist fail-proof** pour le lancement. Tout y est : env vars Render, secrets Cabinet Vault, séquence d'actions admin avant et après mint, validations on-chain, déclenchement des bots, et procédures de récupération.

**Règle d'or** : aucune action de la section _POST-MINT_ ne doit être tentée tant que la section _PRE-MINT_ n'est pas verte à 100%.

---

## 📋 Table des matières

1. [Architecture des secrets — où vit quoi](#1-architecture-des-secrets)
2. [Phase PRE-MINT (J-1 = 17 mai)](#2-phase-pre-mint--j-1--17-mai)
3. [Phase MINT-DAY (18 mai 12:00 UTC)](#3-phase-mint-day--18-mai-1200-utc)
4. [Phase POST-MINT (18 mai 12:05 → 22 mai)](#4-phase-post-mint--18-mai-1205--22-mai)
5. [Tirage Cabinet (22 mai 12:00 UTC)](#5-tirage-cabinet--22-mai-1200-utc)
6. [Bugs connus pré-fixés](#6-bugs-connus-pré-fixés)
7. [Procédures de récupération](#7-procédures-de-récupération)

---

## 1 · Architecture des secrets

Il y a **3 couches** distinctes où vivent les configurations. Ne jamais les mélanger.

### 1.A — Variables d'environnement **Render** (backend FastAPI)

À configurer dans le dashboard Render → ton service backend → **Environment**.

| Variable | Obligatoire | Description | Comment l'obtenir |
|---|---|---|---|
| `MONGO_URL` | ✅ | Connection string MongoDB | Render fournit l'URL si tu utilises leur add-on, sinon Mongo Atlas |
| `DB_NAME` | ✅ | Nom de la DB Mongo (ex : `deepotus_prod`) | Au choix |
| `ADMIN_PASSWORD` | ✅ | Mot de passe panneau admin | À changer (actuellement `deepotus2026`) |
| `CORS_ORIGINS` | ✅ | Domaines autorisés (ex : `https://deepotus.vercel.app,https://www.deepotus.com`) | Vos domaines Vercel + custom |
| `EMERGENT_LLM_KEY` | ✅ | Clé universelle pour OpenAI / Anthropic / Gemini | Fourni par Emergent (déjà set) |
| `HELIUS_API_KEY` | ✅ | Lecture on-chain Solana | https://helius.dev → free tier OK |
| `HELIUS_WEBHOOK_AUTH` | ⚠️ post-mint | Token shared-secret pour webhooks Helius | Génère un UUID via `python3 -c "import uuid;print(uuid.uuid4())"` |
| `RESEND_API_KEY` | ❌ optionnel | Envoi d'emails de notification whitelist | https://resend.com |
| `RESEND_WEBHOOK_SECRET` | ❌ optionnel | Verify Resend webhook events | Resend dashboard |
| `SENDER_EMAIL` | ❌ optionnel | Adresse d'envoi (défaut : `onboarding@resend.dev`) | Custom (DNS Resend) |
| `DEEPOTUS_LAUNCH_ISO` | ❌ optionnel | ISO du launch (cosmétique HUD) | `2026-05-18T12:00:00Z` |
| `PUBLIC_BASE_URL` | ❌ optionnel | URL canonique du site | `https://deepotus.com` |

### 1.B — Variables d'environnement **Vercel** (frontend React)

Dashboard Vercel → project → **Settings → Environment Variables**.

| Variable | Obligatoire | Valeur |
|---|---|---|
| `REACT_APP_BACKEND_URL` | ✅ | URL publique de ton backend Render (ex : `https://deepotus-backend.onrender.com`) |

**⚠️ Ne JAMAIS modifier** `REACT_APP_BACKEND_URL` ni `MONGO_URL` après le premier déploiement : ça casserait l'intégration.

### 1.C — **Cabinet Vault** (secrets chiffrés AES-256-GCM dans MongoDB)

Ces secrets sont stockés chiffrés en base. Accessibles uniquement après déverrouillage via mnémonique de 12 mots. Catégories disponibles :

- `solana_helius` → `DEEPOTUS_MINT_ADDRESS`, `DEEPOTUS_POOL_ADDRESS`, `HELIUS_API_KEY`, `HELIUS_WEBHOOK_AUTH`
- `x_twitter` → `X_API_KEY`, `X_API_SECRET`, `X_BEARER_TOKEN`, `X_ACCESS_TOKEN`, `X_ACCESS_SECRET`, `X_KOL_HANDLES`
- `telegram` → `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- `llm_emergent` → `EMERGENT_LLM_KEY`, `EMERGENT_IMAGE_LLM_KEY`
- `trading_refs` → `BONKBOT_REF_URL`, `MAESTRO_REF_URL`, `TROJAN_REF_URL`, `PHOTON_REF_URL`
- `email_resend` → `RESEND_API_KEY`, `SENDER_EMAIL`, `RESEND_WEBHOOK_SECRET`

> **Vault vs ENV** : Le Vault prend la priorité quand les deux existent. Pour le mint-day, on utilise les **deux** : l'ENV pour le bootstrap (avant que le Vault soit déverrouillé), le Vault pour les secrets X/Telegram chargés à la demande.

---

## 2 · Phase PRE-MINT — J-1 (17 mai)

À faire **avant** que le mint n'arrive le 18 mai à midi.

### ✅ Checkpoint 2.1 — Backend Render opérationnel

```bash
# Depuis ton terminal local
curl https://<TON-BACKEND>.onrender.com/api/transparency/stats
# → doit retourner JSON avec initial_supply=1000000000
```

Si ❌ : vérifie le dashboard Render → Logs → cherche "Application startup complete".

### ✅ Checkpoint 2.2 — Cabinet Vault initialisé

1. Login admin : `https://<TON-SITE>/admin` (mdp `deepotus2026`)
2. Va sur **Cabinet** → **Initialize Vault**
3. **Sauvegarde la mnémonique 12 mots** dans un endroit sûr (1Password / coffre physique)
4. Test : déverrouille, ajoute un secret bidon, relock, redeverrouille → le secret est toujours là

### ✅ Checkpoint 2.3 — Wallets registry rempli

Page admin → **Wallet Registry**. Saisir les 5 wallets :

| Slot | Description | Action |
|---|---|---|
| `deployer` | Wallet ayant déployé le mint | Pubkey Solana + label "Deployer" |
| `treasury` | Multisig 300M (30%) | Pubkey + URL Squads/Streamflow lock |
| `team` | Team vesting 150M (15%) — 2 mois cliff + 12 mois linear | Pubkey + URL Streamflow contract |
| `creator_fees` | Wallet recevant les fees pump.fun | Pubkey + label "Creator fees" |
| `community` | Wallet airdrop / community | Pubkey + label "Community" |

> **Validation** : `https://<SITE>/transparency` doit afficher les 5 cards avec adresses + liens de lock cliquables.

### ✅ Checkpoint 2.4 — Mint Address (LAISSÉE VIDE jusqu'au mint)

**NE PAS** saisir d'adresse de mint maintenant. Le champ doit rester vide jusqu'au 18 mai 12:00 UTC.

> 🐛 **Bug pré-fixé** : précédemment, une route FastAPI capturait `mint-address` comme un slot wallet et silently 422'ait. **C'EST FIXÉ** (voir [section 6](#6-bugs-connus-pré-fixés)).

### ✅ Checkpoint 2.5 — Secrets X (Twitter) dans le Vault

Cabinet Vault → catégorie `x_twitter` :

1. `X_API_KEY` — depuis developer.twitter.com → Project → Keys
2. `X_API_SECRET` — idem
3. `X_BEARER_TOKEN` — onglet "Bearer Token"
4. `X_ACCESS_TOKEN` — généré dans "Authentication Tokens" pour ton compte
5. `X_ACCESS_SECRET` — idem
6. `X_KOL_HANDLES` _(optionnel)_ — JSON array, ex : `["solana","cryptohayes","Cobratate"]`

**Test** : `/admin/propaganda` → **Verify X identity** → doit retourner ton handle (sinon les clés sont mauvaises ou le compte est en mode "billable" sans crédits).

### ✅ Checkpoint 2.6 — Secrets Telegram dans le Vault

Cabinet Vault → catégorie `telegram` :

1. `TELEGRAM_BOT_TOKEN` — via @BotFather → `/newbot` → copy
2. `TELEGRAM_CHAT_ID` — chat ID du canal `@deepotus` (utiliser `@RawDataBot` ou similaire pour l'obtenir, format : `-100...`)

**Test** : `/admin/propaganda` → **Cabinet** → bouton **Test telegram** sur le bot welcome_signal.

### ✅ Checkpoint 2.7 — Tests bouton **manuels**

Avant le mint, valide visuellement :

- [ ] `/` (landing) charge, animation intro joue, missions s'affichent avec illustrations
- [ ] `/transparency` charge avec **Proof of Scarcity** = 1B / 0 burned / 550M circulating (PRE-MINT mode)
- [ ] `/missions` charge avec 6 dossiers + bingo drum
- [ ] `/giveaway` charge avec countdown vers **22 mai 12:00 UTC**
- [ ] `/pulse` charge **sans intro**, **sans nav/footer**, pieuvre rouge edge-to-edge
- [ ] `/pulse` peut être ouvert en iframe Telegram (testable avec un bot dev de test)

### ✅ Checkpoint 2.8 — Backups MongoDB

```bash
# Sur Render dashboard OU mongo CLI
mongodump --uri "$MONGO_URL" --out /tmp/backup_$(date +%Y%m%d)
```

Garde ce snapshot. Si le mint-day se passe mal et qu'on doit roll-back une config, on a une base saine.

---

## 3 · Phase MINT-DAY — 18 mai 12:00 UTC

### T-30 min · Bootstrap final

1. Vérifie que le backend Render répond toujours
2. Vérifie que Vercel n'a pas dépublié le site (cache invalidation déjà OK)
3. Déverrouille le Cabinet Vault et **garde la session ouverte** (les bots vont en avoir besoin)

### T+0 · Mint officiel sur Pump.fun

Le mint est exécuté sur pump.fun. Note bien :
- **Mint address** (commence souvent par `pump` ou base58 random) — ex : `pumpXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`
- **Pool address** (bonding curve)

### T+2 min · Saisir le Mint dans le panneau admin (ÉTAPE LA PLUS CRITIQUE)

1. `/admin/propaganda` → onglet **Cabinet** ou **Wallet Registry** _(les deux marchent)_
2. Champ **Token Mint Address** → coller la pubkey Solana du mint
3. Cliquer **Save**

**Effet immédiat (synchrone, < 1s)** :
- ✅ `/transparency` affiche le mint + lien RugCheck
- ✅ `/api/transparency/wallets` retourne `mint_live: true`
- ✅ `/api/transparency/stats` montre les bons supplies _(toujours en PRE-MINT pour les burns tant qu'il n'y en a pas)_
- ✅ Le pipeline Giveaway bascule automatiquement de PRE-MINT à mode "on-chain holdings check"

> 🚨 **SI rien ne se passe** : c'est probablement le bug route ordering qui revient. Vérifier : `curl -X PUT https://<BACKEND>/api/admin/wallet-registry/mint-address -H "Authorization: Bearer <TOKEN>" -d '{"address":"<MINT>"}'`. Si réponse `422 loc:["path","slot"]`, faut redéployer avec le fix.

### T+5 min · Sauvegarder le Mint dans le Vault aussi

Cabinet Vault → catégorie `solana_helius` :
- `DEEPOTUS_MINT_ADDRESS` = le mint qu'on vient de saisir
- `DEEPOTUS_POOL_ADDRESS` = adresse de la bonding curve pump.fun (optionnel mais utile pour Helius webhooks)

> Pourquoi en double ? Le `wallet_registry.token_mint_address` est la source canonique côté frontend public. Le Vault sert pour le Helius webhook setup en (T+10) qui en a besoin avec le pool_address pour s'abonner aux swaps.

### T+10 min · Configurer le webhook Helius

Référer à `/app/docs/HELIUS_POST_DEPLOY.md` (déjà préparé).

```bash
# Quick command pour créer le webhook depuis le terminal
HELIUS=<TON_HELIUS_API_KEY>
MINT=<TON_MINT>
POOL=<POOL_ADDRESS>
AUTH=<HELIUS_WEBHOOK_AUTH UUID>  # le même que ENV Render
curl -X POST "https://api.helius.xyz/v0/webhooks?api-key=$HELIUS" \
  -H 'Content-Type: application/json' \
  -d "{
    \"webhookURL\": \"https://<BACKEND>/api/webhooks/helius\",
    \"transactionTypes\": [\"SWAP\"],
    \"accountAddresses\": [\"$MINT\",\"$POOL\"],
    \"webhookType\": \"enhanced\",
    \"authHeader\": \"$AUTH\"
  }"
```

**Validation** : faire un trade de test sur pump.fun → vérifier que `db.helius_events` reçoit un document dans les ~10s.

### T+15 min · Fire le trigger MINT (premier tweet Cabinet)

`/admin/propaganda` → **Triggers** → `mint` → bouton **Fire manually**.

Le tweet sera placé dans la queue d'approbation. Va à `/admin/propaganda` → **Queue** → review → **Push to X & Telegram**.

> Si le push échoue avec HTTP 402 → ton compte X est en mode billable et n'a pas de crédits. Achète les credits sur developer.twitter.com → Pay-Per-Use.

### T+20 min · Activer les bots automatiques

`/admin/propaganda` → **Cabinet** :

- **WelcomeSignalCard** → toggle **ENABLE** + `chunk_size` et `cron_hour` au choix
- **InteractionBotCard** → toggle **ENABLE** + `replies_per_run`
- **IncineratorCard** → ne fait rien tant qu'aucun burn n'est déclaré (laissé prêt pour quand)

---

## 4 · Phase POST-MINT — 18 mai 12:05 → 22 mai

### Quotidien (jusqu'au 22 mai)

- [ ] Vérifier la queue Propaganda chaque matin (`/admin/propaganda`) → approuver/rejeter
- [ ] Inspect `db.helius_events` pour confirmer que les swaps arrivent
- [ ] Surveiller le RugCheck score (`/transparency` → CTA RugCheck) → doit rester ≥ 80

### Déclaration de Burns (Operation Incinerator)

Si tu fais des buybacks puis des burns :

1. Exécuter le burn on-chain (pump.fun a un bouton burn, ou via SPL token program)
2. `/admin/propaganda` → **Cabinet** → **IncineratorCard** :
   - **Amount** : nombre exact de tokens brûlés
   - **Tx signature** : la signature Solana de la transaction
   - **Note** _(optionnel)_ : ex "Q1 buyback"
   - Toggle **Push to Propaganda queue** = ✅
   - **Disclose burn**
3. Le burn apparaît immédiatement sur `/transparency` (Proof of Scarcity counter incrémente)
4. Une propagande "Operation Incinerator — X$DEEPOTUS gone" arrive dans la queue → review → push

### Whitelist organique (clearance_levels)

Les nouveaux signups via le Terminal Popup atterrissent dans `db.clearance_levels`. Tu peux les voir dans `/admin/propaganda` → **Cabinet** → **Giveaway Extraction** → **Refresh eligibility roll-call**.

---

## 5 · Tirage Cabinet — 22 mai 12:00 UTC

### T-1h · Préparation

1. Login admin
2. `/admin/propaganda` → **Cabinet** → scroll jusqu'à **Giveaway Extraction**
3. **Refresh** la eligibility roll-call → confirme le nombre de candidats `x_handle != null`
4. Pour chaque candidat **sans wallet linké**, demande son wallet via DM et remplis le panneau **Manual wallets** _(à venir si besoin — actuellement à passer via body JSON)_

### T-5 min · PREVIEW (dry-run)

1. **Preview (dry-run)** avec les paramètres par défaut :
   - Draw date : `2026-05-22T12:00:00Z` (déjà pré-rempli ✓)
   - Pool : `5` SOL (déjà pré-rempli ✓)
   - Winners : `2` (déjà pré-rempli ✓)
   - Min hold : `30` USD (déjà pré-rempli ✓)
2. Inspect le résultat :
   - `eligible_count` : nombre total de candidats whitelistés
   - `verified_count` : ceux qui passent le check on-chain
   - `winners` : les 2 @handles sélectionnés
   - `seed.slot` + `seed.fingerprint` : preuve cryptographique

> Le **preview ne lock pas** la date — tu peux en relancer plusieurs (l'identique si même slot Solana, différent à chaque shuffle si le slot a changé).

### T+0 · 12:00 UTC sharp — RUN EXTRACTION

1. **Run extraction (lock)** → confirme dans le dialog
2. Le snapshot est persisté avec `kind=extraction`, le draw_date est LOCKÉ
3. Note bien le `snapshot_id` (8 premiers chars)

> Si une erreur `duplicate_active_extraction` apparaît : tu as déjà tiré pour ce date. Cancel l'ancien snapshot d'abord (bouton 🗑 dans Snapshots history) puis re-run.

### T+1 min · Announce

1. Dans **Snapshots history** → trouve ton snapshot → bouton **📢 Announce**
2. Le tweet "EXTRACTION SUCCESS — The Cabinet has selected 2 agents. @alice, @bob..." atterrit dans la queue Propaganda
3. **Queue** → review → **Push to X & Telegram**

### Audit post-tirage

Quiconque peut vérifier le tirage :
1. Récupère le snapshot via `GET /api/admin/giveaway/snapshots/{id}` (authentifié)
2. Le snapshot contient :
   - `seed.blockhash` + `seed.slot` : récupérables publiquement via n'importe quel RPC Solana
   - `seed.fingerprint` : sha256 reproductible
   - `details` : liste complète des candidats avec leurs holdings
3. Replay avec le même seed → mêmes winners → preuve provable fairness

---

## 6 · Bugs connus pré-fixés

> Ces bugs **ont été corrigés** dans le code. Documentation pour mémoire si jamais ils refont surface.

### 🐛 Bug #1 — Token Mint admin ne se propage pas

**Symptôme observé par l'utilisateur** : "j'avais tenté de rentrer une adresse de token dans le vault admin mais rien n'avait été changé sur le site."

**Root cause** : route FastAPI ordering — `PUT /api/admin/wallet-registry/{slot}` (regex `^[a-z_]{2,32}$`) était déclarée AVANT `PUT /mint-address`. FastAPI match dans l'ordre de déclaration. "mint-address" contient un `-` qui ne matche pas `[a-z_]`, donc FastAPI rejetait avec `422 loc:["path","slot"]`. Le frontend ne montrait pas l'erreur car le toast d'erreur tombe dans le catch-all.

**Fix** : `routers/wallet_registry.py` — `/mint-address` declared BEFORE `/{slot}`. **Test de régression** dans `backend/tests/test_route_ordering_regression.py`.

### 🐛 Bug #2 — `X-Frame-Options: DENY` bloquait TMA Telegram

**Symptôme** : `/pulse` chargerait en navigateur normal mais resterait blanc dans Telegram.

**Root cause** : `vercel.json` envoyait `X-Frame-Options: DENY` sur toutes les routes. Telegram embed dans un iframe → browser refuse.

**Fix** : negative-lookahead `/((?!pulse$|pulse/).*)` exclut `/pulse` du XFO. Sur `/pulse` un `Content-Security-Policy: frame-ancestors` autorise explicitement `web.telegram.org` + variantes `k/z/a.telegram.org`.

### 🐛 Bug #3 — Intro animation leak sur `/pulse`

**Symptôme** : utilisateur TMA voyait l'intro DeepState pendant 14s.

**Root cause** : pas reproductible en pratique (DeepStateIntro était déjà uniquement dans Landing.tsx) mais défensif pour empêcher une régression future.

**Fix** : `shouldShowIntro()` a maintenant un blacklist hardcodé `["/pulse", "/trade"]` qui bypasse tout (y compris `?intro=force`).

### 🐛 Bug #4 — `cliff 3 mois` vs `cliff 6 mois` Team

**Symptôme** : incohérence visible entre Tokenomics card, FAQ, et /transparency.

**Fix** : unifié à `2-month cliff + 12-month linear vesting` partout (Team uniquement, Treasury garde 6 mois).

---

## 7 · Procédures de récupération

### "Le frontend ne montre pas mes changements admin"

1. Hard-refresh du navigateur (Ctrl+Shift+R / Cmd+Shift+R) — peut-être un cache Vercel
2. Vérifier que la mutation a réussi : `GET /api/admin/wallet-registry` doit retourner la valeur
3. Si l'API renvoie la bonne valeur mais pas le site, c'est un cache CDN → forcer une invalidation via Vercel dashboard ou attendre 60s

### "Mon mot de passe admin ne marche plus"

- L'ENV `ADMIN_PASSWORD` sur Render est la source de truth
- Si tu l'as changé après le 1er déploiement, redémarre le service Render pour qu'il prenne en compte

### "Le Vault est verrouillé et j'ai perdu la mnémonique"

- ⚠️ **Aucune backdoor**. La mnémonique est l'unique clé AES-256.
- Seule option : `factory_reset_vault` (endpoint `POST /api/admin/vault/factory-reset`). Ça purge TOUS les secrets et exige une réinitialisation propre. Tu vas devoir re-saisir tous les secrets X / Telegram / etc.

### "Le Helius webhook ne reçoit plus rien"

1. Helius dashboard → Webhooks → check le status (active/disabled)
2. Test du auth : `curl -X POST https://<BACKEND>/api/webhooks/helius -H "Authorization: <HELIUS_WEBHOOK_AUTH>" -d '{}'` → doit retourner 400 (mauvais payload), pas 401 (mauvais auth)
3. Re-créer le webhook avec le bon `accountAddresses` (mint + pool)

### "Le X push échoue avec HTTP 402"

- Compte X en mode billable → développeur.twitter.com → Subscriptions → ajouter Pay-Per-Use credits
- Si HTTP 403 → tes Bearer ou Access tokens sont périmés/révoqués → régénérer

### "RugCheck score s'écroule sous 80"

- Vérifier les transferts récents sur les wallets `team` et `treasury` — si tu touches au lock avant le cliff, le score plonge
- Mint authority et freeze authority **doivent rester revoked**. Confirme via Solscan.

---

## ✅ État du code · Final pre-deploy snapshot

| Item | Status |
|---|---|
| Backend Pytest | **175/175** passing |
| TypeScript `tsc --noEmit` | **0** errors |
| Ruff lint | Clean sur tous les fichiers nouveaux |
| Route ordering test régression | ✅ pinné |
| `/pulse` isolation | ✅ frame-ancestors Telegram OK, X-Frame-Options retiré, intro blacklist |
| Date tirage | ✅ 22 mai 12:00 UTC partout (front + back + i18n) |
| Bug propagation mint | ✅ fixé + couvert par test |
| Illustrations missions + bingo | ✅ tech-noir v2 servies en WebP |
| Cache /pulse | ✅ `no-store, max-age=0` pour TMA freshness |
| Robots /pulse | ✅ noindex via HTTP header + meta dynamique |

**Push GitHub** : utilise le bouton "Save to GitHub" de l'UI Emergent. Render + Vercel redéploieront automatiquement.

---

_Dernière mise à jour : 17 mai 2026 — pre-launch audit complet._
