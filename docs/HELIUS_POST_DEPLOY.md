# Helius — Post-deploy sur `deepotus.xyz`

**Objectif :** (re)wire Helius pour que chaque SWAP impliquant le mint `$DEEPOTUS`
sur Solana mainnet-beta soit poussé vers votre backend Render et alimente le vault
en temps réel.

> 👉 **Garde-je mon ancienne API key + webhook ?**
> - **API key Helius** : **OUI, vous pouvez la garder**. Elle est liée à votre
>   compte Helius, pas à un domaine. Il suffit de vérifier qu'elle est bien
>   renseignée dans le Cabinet Vault en prod.
> - **Webhook ID existant** : **NON, il faut le recréer** (ou au minimum
>   mettre à jour son `webhookURL`) car l'ancien pointait sur l'URL de preview
>   Emergent. Helius exige un HTTPS joignable publiquement — votre nouveau
>   domaine ne peut recevoir les events tant que le webhook n'a pas l'URL
>   `https://VOTRE-BACKEND.onrender.com/api/webhooks/helius`.

---

## Prérequis (vérifications rapides)

Ouvrez un terminal et lancez ces 3 checks :

```bash
# 1) Votre URL backend Render répond
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://VOTRE-BACKEND.onrender.com/api/
# Attendu : HTTP 200

# 2) Admin login fonctionne
TOKEN=$(curl -s -X POST https://VOTRE-BACKEND.onrender.com/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"password":"VOTRE_MDP_ADMIN"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
echo "TOKEN length: ${#TOKEN}"
# Attendu : 212

# 3) Vault déverrouillé + 2FA validée (la commande ci-dessous nécessite les deux)
curl -s https://VOTRE-BACKEND.onrender.com/api/admin/cabinet-vault/status \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
# Attendu : "state":"unlocked"
```

---

## Étape 1 · Récupérer (ou créer) votre API key Helius

1. Connectez-vous à https://dashboard.helius.dev/
2. `Settings → API Keys` — copiez votre clé existante (format `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).
3. Si vous voulez une **clé dédiée à la prod** (recommandé pour segmenter les
   logs Helius), cliquez sur `+ New API Key` et nommez-la `deepotus-prod`.

> **Conseil :** gardez votre clé preview pour continuer à tester en staging
> sans polluer les quotas prod.

---

## Étape 2 · Stocker la clé dans le Cabinet Vault (production)

1. Ouvrez https://www.deepotus.xyz/admin/cabinet-vault (2FA active — votre
   vault n'est plus en bootstrap mode).
2. Déverrouillez avec votre mnemonic BIP39 + code TOTP.
3. Dans la catégorie **`helius`** (ou créez-la), ajoutez ces 2 secrets :

   | Clé (EXACTE) | Valeur |
   |---|---|
   | `HELIUS_API_KEY` | la clé récupérée à l'étape 1 |
   | `HELIUS_WEBHOOK_AUTH` | une chaîne aléatoire **longue** (≥ 32 char) — voir commande ci-dessous |

   Pour générer un `HELIUS_WEBHOOK_AUTH` solide :

   ```bash
   python3 -c "import secrets;print(secrets.token_urlsafe(48))"
   ```

   Exemple de sortie : `M3_Hk2-...` — copiez-la **UNE SEULE FOIS** dans le vault,
   vous la réinjecterez à Helius à l'étape 4.

4. Cliquez sur **Save** pour chacun. Le Cabinet Vault chiffre en AES-256-GCM
   avant persistance Mongo.

---

## Étape 3 · Vérifier la config `mint` + `pool_address`

Le backend a besoin de deux adresses **Solana mainnet-beta** pour parser les
swaps :

- `dex_token_address` = le mint de `$DEEPOTUS` (la vraie adresse quand le token
  sera minté — si vous êtes encore en pre-launch, gardez l'adresse demo
  `So11111111111111111111111111111111111111112` qui est celle du wrapped SOL
  utilisée comme placeholder et qui active le mode demo).
- `helius_pool_address` = l'adresse du pool Raydium/Orca — connue seulement
  après création du pool.

**Depuis l'admin UI**, section **Whale Watcher → Helius Config** (ou via curl) :

```bash
curl -X POST https://VOTRE-BACKEND.onrender.com/api/admin/vault/helius-config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mint": "VOTRE_MINT_DEEPOTUS_ADDRESS",
    "pool_address": "VOTRE_POOL_ADDRESS_OU_null_SI_PAS_ENCORE",
    "webhook_auth": "LA_CHAINE_GENEREE_ETAPE_2"
  }'
```

**Checklist post-config :**

```bash
curl -s https://VOTRE-BACKEND.onrender.com/api/admin/vault/helius-status \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Doit retourner :
```json
{
  "api_key_configured": true,
  "mint": "...",
  "pool_address": "...",
  "webhook_id": null,          // → on va le remplir à l'étape suivante
  "webhook_url": "https://VOTRE-BACKEND.onrender.com/api/webhooks/helius",
  "helius_webhooks": []        // vide → normal, on n'a pas encore appelé /register
}
```

---

## Étape 4 · Enregistrer le webhook auprès de Helius

Cette étape **remplace définitivement** votre ancien webhook (si vous en
aviez un sur l'URL preview).

```bash
curl -X POST https://VOTRE-BACKEND.onrender.com/api/admin/vault/helius-register \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "register_webhook": true
  }'
```

Retour attendu :
```json
{
  "ok": true,
  "webhook_id": "a8b2c...",
  "webhook_url": "https://VOTRE-BACKEND.onrender.com/api/webhooks/helius",
  "transactionTypes": ["SWAP"],
  "accountAddresses": ["VOTRE_MINT_DEEPOTUS"]
}
```

Le backend a :
1. Appelé `POST https://api.helius.xyz/v0/webhooks` avec votre clé.
2. Persisté le `webhookID` retourné dans `vault_state.helius_webhook_id`.
3. Injecté le `HELIUS_WEBHOOK_AUTH` dans le header `Authorization` que Helius
   renverra pour signer chaque push → le backend vérifie cette signature dans
   `routers/webhooks.py::helius_webhook`.

> **⚠️ Si vous aviez un ancien webhook** sur l'URL preview, il est toujours
> actif côté Helius et va continuer de pousser vers une URL 404. Deux options :
>
> - **Option propre** (recommandée) — listez les webhooks et supprimez
>   l'ancien :
>   ```bash
>   # Lister tous les webhooks sur votre compte Helius
>   curl -s https://api.helius.xyz/v0/webhooks?api-key=VOTRE_HELIUS_API_KEY \
>     | python3 -m json.tool
>   # Supprimer celui qui a l'URL preview
>   curl -X DELETE https://api.helius.xyz/v0/webhooks/ANCIEN_ID?api-key=VOTRE_HELIUS_API_KEY
>   ```
> - **Option lazy** — laissez-le tourner. Helius facturera des crédits pour
>   rien (chaque push 404) donc sur un quota serré, à éviter.

---

## Étape 5 · Smoke-test (simuler un SWAP)

Depuis l'admin UI, section **Whale Watcher → Simulate webhook** (ou curl) :

```bash
# Envoie un faux SWAP au webhook local (garde le mode demo ON si pas de mint réel)
curl -X POST https://VOTRE-BACKEND.onrender.com/api/webhooks/helius \
  -H "Authorization: Bearer VOTRE_HELIUS_WEBHOOK_AUTH" \
  -H "Content-Type: application/json" \
  -d '[{
    "signature": "smoketest-'$(date +%s)'",
    "type": "SWAP",
    "tokenTransfers": [
      {
        "mint": "VOTRE_MINT_DEEPOTUS",
        "fromUserAccount": "POOL_ADDRESS",
        "toUserAccount": "FakeBuyerAddr000000000000000000000000000001",
        "tokenAmount": 10000,
        "tokenStandard": "FUNGIBLE"
      }
    ]
  }]'
```

Retour attendu :
```json
{ "ingested": 1, "buys": 1, "sells": 0, "duplicates": 0, "skipped": 0 }
```

**Puis vérifiez que le vault a bien noté le BUY** :

```bash
curl -s https://VOTRE-BACKEND.onrender.com/api/admin/vault/status \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('cracks opened:', d.get('cracks_opened'))
print('last ingest:', d.get('last_helius_ingest_at'))
"
```

---

## Étape 6 · Activer les logs en temps réel (optionnel mais utile)

**Sur Render Dashboard** → votre service backend → `Logs` → mot-clé `[helius]`.
Vous devez voir les ingestion en continu :

```
[helius] webhook {'ingested': 1, 'buys': 1, 'sells': 0, 'duplicates': 0, 'skipped': 0} (tx=1, mint=ABC..., pool=XYZ..., demo=False)
```

Si vous voyez `demo=True` → vous êtes toujours sur le mint wrappedSOL
placeholder, mettez à jour le mint via `/helius-config`.

---

## Étape 7 · Basculer en mode live (post-mint only)

Tant que vous êtes en **pre-launch / pre-mint** :

```bash
curl -X POST https://VOTRE-BACKEND.onrender.com/api/admin/vault/dex-config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "dex_mode": "demo" }'
```

Une fois le pool créé sur Raydium et le mint mainnet annoncé :

```bash
curl -X POST https://VOTRE-BACKEND.onrender.com/api/admin/vault/dex-config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "dex_mode": "live" }'
```

Le mode `live` :
- Coupe les `demo_tokens_per_buy` (chaque BUY est compté à sa vraie quantité on-chain).
- Active le Whale Watcher réel (`whale_buy` trigger ne se déclenche que si
  `amount_usd >= trigger_metadata.threshold_usd`).
- Active les milestone announcements automatiques.

---

## Troubleshooting rapide

| Symptôme | Cause probable | Fix |
|---|---|---|
| `HTTP 401` sur `/api/webhooks/helius` | `HELIUS_WEBHOOK_AUTH` ≠ entre vault et Helius dashboard | Régénérer côté vault puis `POST /helius-register` pour ré-armer |
| `webhook_id: null` après /helius-register | API key invalide ou pool non Mainnet | `GET /helius-status` pour vérifier `api_key_configured`, tester la clé sur https://dashboard.helius.dev/ |
| Logs Render muets mais dashboard Helius montre des calls | Render cold-start kills le worker | Activer Render Starter plan ($7/mo) → no cold-start |
| `skipped: 1` au lieu de `ingested: 1` | Le mint du SWAP ≠ `dex_token_address` | Update via `/helius-config`, le parser filtre par mint |
| `demo: True` dans les logs | `dex_token_address` = wrappedSOL placeholder | Étape 3 : remplacer par le vrai mint post-launch |

---

## Récap visuel des dépendances

```
┌──────────────────┐     HTTPS POST /api/webhooks/helius (JSON body)
│   Helius dash    │────────────────────────────────────────────────┐
│  dashboard.helius│   + header Authorization: <HELIUS_WEBHOOK_AUTH>│
└──────────────────┘                                                ▼
                                                        ┌─────────────────┐
                                                        │  Render backend │
                                                        │   FastAPI       │
                                                        │                 │
                                                        │ webhooks.py     │
                                                        │   ├─ auth check │
                                                        │   ├─ dedup      │
                                                        │   ├─ parse SWAP │
                                                        │   └─► vault.    │
                                                        │      apply_crack│
                                                        └─────────────────┘
                                                                ▲
                                                                │
                                          ┌─────────────────────┴────────┐
                                          │ Cabinet Vault (MongoDB AES)  │
                                          │  helius/HELIUS_API_KEY       │
                                          │  helius/HELIUS_WEBHOOK_AUTH  │
                                          └──────────────────────────────┘
```

---

## TL;DR (recette express)

```bash
# 0) Setup
export BACKEND="https://VOTRE-BACKEND.onrender.com"
export MDP="VOTRE_MDP_ADMIN"
TOKEN=$(curl -s -X POST $BACKEND/api/admin/login -H "Content-Type: application/json" \
  -d "{\"password\":\"$MDP\"}" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

# 1) Stocker HELIUS_API_KEY + HELIUS_WEBHOOK_AUTH dans Cabinet Vault (UI recommandée)
# 2) Configurer mint + pool
curl -X POST $BACKEND/api/admin/vault/helius-config -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "mint": "VOTRE_MINT", "pool_address": "VOTRE_POOL", "webhook_auth": "LA_MEME_QUE_VAULT" }'

# 3) Enregistrer le webhook
curl -X POST $BACKEND/api/admin/vault/helius-register -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{ "register_webhook": true }'

# 4) Vérifier
curl -s $BACKEND/api/admin/vault/helius-status -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Si `webhook_id` est non-null dans la réponse finale → vous êtes live.** 🎯
