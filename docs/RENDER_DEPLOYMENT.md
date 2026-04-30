# DEEPOTUS — Render Deployment Notes

> Backend FastAPI deployment on Render. Frontend is deployed separately on Vercel — see [`VERCEL_DASHBOARD_SETUP.md`](./VERCEL_DASHBOARD_SETUP.md).

## Statut au 29/04/2026 (Phase 17.D)

- ✅ `requirements.txt` — `emergentintegrations` retiré. Le build Render ne dépend pas du package privé Emergent.
- ✅ `backend/core/llm_compat.py` — **wrapper hybride auto-détection** (introduit en Phase 17.D) :
  - **Mode A** (preferred) : si `emergentintegrations` est importable → re-export direct de `LlmChat` / `UserMessage` (proxy Emergent, EMERGENT_LLM_KEY fonctionne)
  - **Mode B** (fallback) : sinon → SDKs natifs (`openai`, `anthropic`, `google-generativeai`) avec des clés provider-spécifiques
  - Aucune API publique modifiée — les callers voient la même classe quelle que soit la mode active.
- ✅ Même comportement pour les images : Nano Banana (Gemini) + `gpt-image-1` (Sprint 17.F) supportent les 2 modes.
- ✅ Sprint 13.3 — scaffold dispatchers Telegram/X ajouté (`core/dispatchers/`, `core/dispatch_worker.py`). Dry-run par défaut. Voir [`SPRINT_13_3_DISPATCHERS.md`](./SPRINT_13_3_DISPATCHERS.md).

## Stratégie LLM sur Render — 2 choix

### Option 1 (recommandé pour prod) — Clés natives (Mode B)

Fournir une ou plusieurs clés provider-natives dans Render env :

| Variable | Obtenir depuis | Coût typique |
|---|---|---|
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) | $5 starter, ~$0.50/mois sur gpt-4o-mini |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | $5 minimum, Claude Sonnet 4.5 |
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) | Free tier couvre l'usage |

`llm_compat.py` détecte automatiquement l'absence de `emergentintegrations` et bascule en Mode B. **Aucune ligne de code à changer**.

Si vous ne définissez **AUCUNE** clé LLM, l'app continue de fonctionner : les templates de propagande sont envoyés tels quels (sans l'enrichissement LLM). Pas de crash.

### Option 2 (passthrough Emergent) — PIP_EXTRA_INDEX_URL

Pour garder le Mode A (proxy Emergent avec `EMERGENT_LLM_KEY` universelle), deux ajouts à Render :

1. **Environment Variable** → `PIP_EXTRA_INDEX_URL=https://d33sy5i8bnduwe.cloudfront.net/simple/`
2. **Ajouter dans `requirements.txt`** :
   ```
   emergentintegrations==0.1.0
   ```

Puis redeploy. Le build Render lira l'extra-index, trouvera le package privé, l'installera. `llm_compat.py` passera automatiquement en Mode A.

> ⚠️ Option 2 couple votre prod à l'infrastructure Cloudfront Emergent. Si l'URL change ou le service devient payant, votre build cassera. **Option 1 est plus safe pour la prod**.

## Render env vars — liste complète

Copier depuis `backend/.env` local vers Render's *Environment Variables* panel.
**Ne jamais commit** ces valeurs.

### Backend core (obligatoires)

| Variable | Rôle |
|---|---|
| `MONGO_URL` | URI Mongo Atlas (`mongodb+srv://...`) |
| `DB_NAME` | Nom de la base (ex: `deepotus_prod`) |
| `CORS_ORIGINS` | URLs Vercel séparées par virgule (ex: `https://deepotus.com,https://www.deepotus.com`) |
| `DEEPOTUS_LAUNCH_ISO` | ISO timestamp du mint public (drive le seal status) |
| `SECRETS_KEK_KEY` | Fernet key pour wrapping Cabinet Vault |
| `ADMIN_PASSWORD` | Default: `deepotus2026` — À CHANGER en prod |
| `JWT_SECRET` | Auto-généré au 1er démarrage si absent |
| `PUBLIC_BASE_URL` | URL Vercel finale (ex: `https://deepotus.com`) |

### Helius (on-chain monitoring)

| Variable | Rôle |
|---|---|
| `HELIUS_API_KEY` | Free tier OK (100k credits/mois) |
| `HELIUS_WEBHOOK_AUTH` | Secret pour signer `/api/webhooks/helius` |

### Email (Resend)

| Variable | Rôle |
|---|---|
| `RESEND_API_KEY` | Loyalty + clearance email pings |
| `RESEND_WEBHOOK_SECRET` | Inbound webhook signature (svix) |
| `SENDER_EMAIL` | Adresse `From:` (domaine vérifié Resend) |

### LLM (voir stratégie ci-dessus)

Soit Mode A (`EMERGENT_LLM_KEY` + `PIP_EXTRA_INDEX_URL` + pin emergentintegrations), soit Mode B (clés natives), soit rien (templates verbatim).

### Propaganda Dispatchers (Sprint 13.3) — optionnels jusqu'à activation LIVE

**Ces credentials ne sont PAS nécessaires pour le boot.** Le worker tourne en dry-run jusqu'à ce que vous flippiez `dispatch_dry_run=false` dans `propaganda_settings` (via admin UI ou route 2FA).

Quand prêt à activer le live, **vaulter ces valeurs** via l'UI Cabinet Vault (ne PAS les mettre dans env Render — la Vault chiffre en AES-256-GCM) :

**Telegram** (catégorie `telegram` dans le vault):
- `TELEGRAM_BOT_TOKEN` — depuis [@BotFather](https://t.me/BotFather)
- `TELEGRAM_CHAT_ID` — channel/group/user id (le bot doit y être admin)

**X / Twitter** (catégorie `x_twitter`) — **OAuth 1.0a User Context** (pas OAuth 2.0 pour POST tweets):
- `X_API_KEY` (consumer key)
- `X_API_SECRET` (consumer secret)
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`

> ⚠️ Pour `POST /2/tweets` il faut la **tier Elevated ou Pro** sur developer.x.com. Tier Free ne permet pas de tweeter. Tant que votre tier n'est pas confirmée, laissez `dispatch_dry_run=true`.

### Optionnels

| Variable | Rôle |
|---|---|
| `BONKBOT_REF_URL` | Affiliate surface sur `/how-to-buy` |
| `TROJAN_REF_URL` | Affiliate surface sur `/how-to-buy` |

## Helius webhook configuration (post-deploy)

Une fois Render live à `https://deepotus.onrender.com` :

1. Helius dashboard → Webhooks → New webhook.
2. URL : `https://deepotus.onrender.com/api/webhooks/helius`
3. Auth header : `Bearer <HELIUS_WEBHOOK_AUTH>` (la valeur de votre env)
4. Filter : swap events sur l'adresse du pool $DEEPOTUS (configurée via admin → Vault → Helius section une fois le pool existant).

Avant que le pool address soit set, le webhook reçoit mais traite comme demo data. La queue `whale_alerts` accepte les `simulate` calls pour vérifier la pipeline propaganda immédiatement.

## Credentials rotation (post-launch hygiene)

Toute valeur ayant transité par le chat onboarding doit être rotée une fois le projet publiquement live :

| Credential | Méthode |
|---|---|
| X_API_KEY / X_API_SECRET | [developer.x.com](https://developer.x.com) → Apps → DEEPOTUS → Regenerate |
| X_ACCESS_TOKEN / X_ACCESS_TOKEN_SECRET | developer.x.com → Apps → DEEPOTUS → Access Token → Revoke + Create new |
| TELEGRAM_BOT_TOKEN | Telegram → @BotFather → `/revoke` → bot → nouveau token |
| HELIUS_API_KEY | helius.dev dashboard → Settings → Regenerate |
| SECRETS_KEK_KEY | Rotate uniquement via l'admin flow `/admin/cabinet-vault/rotate-kek` |

Une fois les nouvelles valeurs obtenues, les stocker dans le **Cabinet Vault** via l'admin UI — ne pas les mettre en env Render (sauf `SECRETS_KEK_KEY` qui doit rester en env).

## Pre-push checklist

Avant le prochain `git push` :

- [ ] `backend/.env` est gitignored (vérifié via `git check-ignore`)
- [ ] Aucun raw token committé (`grep -rE "(tg_token|x_access|bearer)" ...` clean)
- [ ] `requirements.txt` ne contient PAS `emergentintegrations` *(OU contient-le avec `PIP_EXTRA_INDEX_URL` configuré)*
- [ ] Tous les production files importent depuis `core.llm_compat` (done)
- [ ] `pip install -r requirements.txt` complete sans erreurs
- [ ] `python -c "from core.llm_compat import LlmChat, UserMessage"` succède
- [ ] `ruff check backend/` clean
- [ ] Tests E2E backend : `python -c "import asyncio; from core.dispatch_worker import run_tick; asyncio.run(run_tick())"` retourne une `summary` dict

