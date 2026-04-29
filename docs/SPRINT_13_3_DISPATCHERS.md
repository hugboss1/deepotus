# Sprint 13.3 — Propaganda Dispatchers (scaffold)

> **Statut** : SCAFFOLD COMPLET, mode dry-run par défaut. Aucun POST réel à Telegram/X tant que les credentials ne sont pas vaultés ET les 2 toggles flippés.

---

## TL;DR

Le moteur Propaganda peut maintenant :
- **Pousser** tout item en statut `approved` vers Telegram + X automatiquement (toutes les 30s via APScheduler).
- **Respecter** des rate limits (per_hour / per_day / per_trigger_minutes) lus depuis `propaganda_settings`.
- **Tourner en dry-run** : la pipeline complète s'exécute, mais les dispatchers loggent au lieu de POSTer (état actuel).
- **Basculer en live** d'un toggle (avec 2FA) une fois les credentials prêts.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  APScheduler (every 30s)                                     │
│      └──→ core/dispatch_worker.tick_async()                  │
│             ├─ Read propaganda_settings                      │
│             │     panic? dispatch_enabled? dispatch_dry_run? │
│             │     rate_limits {per_hour, per_day, per_trig}  │
│             ├─ Fetch propaganda_queue WHERE                  │
│             │     status="approved" AND scheduled_for ≤ now  │
│             ├─ For each item (max 5/tick):                   │
│             │     Atomic claim: status=approved → in_flight  │
│             │     For each platform in item.platforms:       │
│             │         core/dispatchers/{platform}.send(...)  │
│             │     Aggregate results                          │
│             │     Final: status=sent | failed                │
└──────────────────────────────────────────────────────────────┘
```

### Fichiers ajoutés

| Fichier | Rôle |
|---|---|
| `core/dispatchers/__init__.py` | Registry + `DispatchResult` + `DispatchOutcome` |
| `core/dispatchers/telegram.py` | Telegram Bot API client (`sendMessage`) |
| `core/dispatchers/x.py` | X (Twitter) API v2 client (OAuth1.0a, `POST /2/tweets`) |
| `core/dispatch_worker.py` | Le worker (tick + claim + dispatch + finalise) |
| `docs/SPRINT_13_3_DISPATCHERS.md` | Ce document |

### Fichiers modifiés

| Fichier | Changement |
|---|---|
| `core/bot_scheduler.py` | Job `propaganda_dispatch` enregistré au boot |
| `core/propaganda_engine.py` | `set_dispatch_toggle()` + nouveaux defaults |
| `core/dispatch_queue.py` | `queue_counts()` pour le status endpoint |
| `routers/propaganda.py` | 3 nouvelles routes admin |

---

## Lifecycle d'un item

```
proposed   → admin reviews via /api/admin/propaganda/queue/{id}/approve
approved   → tick draine → claim atomique → in_flight
in_flight  → dispatchers parallèles → results agregés
sent       → ✅ tous platforms OK | sent_at timestamp
failed     → ❌ au moins un platform NOK | error string + per-platform results
```

L'admin peut **re-approuver** un item `failed` pour le re-pusher (l'item retombe en `approved`).

---

## Settings (`propaganda_settings` doc)

```jsonc
{
  // Existing
  "panic": false,
  "default_locale": "en",
  "rate_limits": {
    "per_hour": 8,
    "per_day": 24,
    "per_trigger_minutes": 15
  },
  "platforms": ["telegram", "x"],

  // NEW (Sprint 13.3) — both default to SAFEST
  "dispatch_enabled": false,    // master switch (worker no-ops if false)
  "dispatch_dry_run": true,     // dispatchers log instead of HTTP POST
}
```

---

## Routes admin

### `GET /api/admin/propaganda/dispatch/status`

Snapshot pour l'UI admin.

```json
{
  "settings": {
    "panic": false,
    "dispatch_enabled": false,
    "dispatch_dry_run": true,
    "rate_limits": { ... },
    "platforms": ["telegram", "x"]
  },
  "queue": {
    "proposed": 9, "approved": 2, "in_flight": 0,
    "sent": 0, "failed": 0, "rejected": 0, "killed": 0,
    "total": 11
  }
}
```

### `POST /api/admin/propaganda/dispatch/toggle` *(2FA required)*

```json
{ "enabled": true, "dry_run": true }
```

Both fields optional. Audit-logged.

### `POST /api/admin/propaganda/dispatch/tick-now` *(2FA required)*

Force one immediate drain pass. Honours all the same gates as the scheduled tick.

---

## ✅ Checklist pour passer en LIVE

> Faire dans cet ordre. Chaque étape est réversible.

### 1. Vault les credentials (admin UI Cabinet Vault)

| Plateforme | Catégorie | Clés à stocker |
|---|---|---|
| Telegram | `telegram` | `TELEGRAM_BOT_TOKEN` (depuis @BotFather) <br/> `TELEGRAM_CHAT_ID` (channel/group/user — le bot doit y être admin) |
| X (Twitter) | `x_twitter` | `X_API_KEY`, `X_API_SECRET` (consumer key/secret) <br/> `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` (user-context OAuth1.0a) |

> Pour X : tier **Elevated ou Pro** requis (la tier Free ne permet pas `POST /2/tweets`). Si tier non confirmée, laissez `dispatch_dry_run=true`.

### 2. Activer le worker en mode DRY-RUN

```bash
TOKEN=$(curl -s -X POST "$URL/api/admin/login" -H "Content-Type: application/json" \
  -d '{"password":"..."}' | jq -r '.token')

# Already enabled by default after vault setup? Verify:
curl -H "Authorization: Bearer $TOKEN" $URL/api/admin/propaganda/dispatch/status

# Enable in dry-run
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"enabled": true, "dry_run": true, "totp_code": "...123"}' \
  $URL/api/admin/propaganda/dispatch/toggle
```

### 3. Approuver un item de test depuis l'admin UI

→ `Propaganda admin → Queue → "approve"`

### 4. Force tick + vérifier les logs dry-run

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"totp_code": "..."}' \
  $URL/api/admin/propaganda/dispatch/tick-now
```

Logs attendus (backend stdout) :
```
[telegram.dry_run] would_send chars=77 preview="$25k reached. Six figures or zero..."
[x.dry_run] would_post chars=77 preview="$25k reached..."
[dispatch_worker] item=<uuid> status=sent (platforms=['telegram','x'], dry_run=True)
```

L'item passe à `status=sent` mais aucun appel HTTP réel n'a été fait.

### 5. Quand vous êtes sûr de tout — basculer LIVE

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"dry_run": false, "totp_code": "..."}' \
  $URL/api/admin/propaganda/dispatch/toggle
```

L'admin UI doit afficher **"DISPATCH LIVE"** en rouge dans le banner top.

### 6. Approuver UN seul item de test → tick-now → vérifier sur Telegram + X

→ Si OK, le moteur tourne tout seul. L'admin n'a plus qu'à approuver les futurs items.

### 7. En cas d'incident : panic kill switch

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"panic": true, "totp_code": "..."}' \
  $URL/api/admin/propaganda/panic
```

Tous les items `proposed`/`approved` passent à `killed` immédiatement, le worker no-op.

---

## Failure mapping

| Erreur | Comportement worker | Item statut final |
|---|---|---|
| Pas de credentials Telegram | Dispatcher renvoie `no_credentials` | `failed` |
| Pas de credentials X (tous) | Idem | `failed` |
| Telegram `ok=false` | Erreur stockée dans `results.telegram.error` | `failed` |
| X HTTP 401 | `x_unauthorized` (creds invalides) | `failed` |
| X HTTP 403 | `x_tier_locked` (tier insuffisante) | `failed` |
| X HTTP 429 | `x_rate_limited` | `failed` |
| Timeout | `timeout` | `failed` |
| Crash inattendu | `crash: <exception>` | `failed` |
| Plateforme inconnue | `unsupported_platform` | `failed` |

> **Tous les échecs sont terminaux** dans ce sprint. Pas de retry auto. L'admin re-approuve manuellement pour relancer. Un retry counter + backoff est prévu en 13.3.x.

---

## Rate limits — comment ça marche

| Limite | Mécanisme |
|---|---|
| `per_hour` | Compte les items `status=sent` avec `sent_at` dans les 60 dernières minutes. Si ≥ limite, le worker no-op le tick. |
| `per_day` | Idem sur 1440 minutes. |
| `per_trigger_minutes` | Pour chaque candidate, vérifie qu'aucun autre item du même `trigger_key` n'a été envoyé dans les N dernières minutes. Si oui, skip ce candidate ce tick. |
| `MAX_ITEMS_PER_TICK = 5` | Plafond intra-tick pour ne pas brutaliser Mongo en cas de backlog. |

Tous les compteurs sont calculés "on the fly" depuis la collection `propaganda_queue` — aucun cache, toujours cohérent post-restart.

---

## Tests automatiques effectués (Sprint 13.3)

- ✅ Worker no-op quand `dispatch_enabled=false`
- ✅ Worker no-op quand `panic=true`
- ✅ 2 items approved → tick → 1 dispatched, 1 rate-limited (cooldown trigger)
- ✅ Item passe `approved → in_flight → sent` avec `results` per platform
- ✅ Routes `/dispatch/status`, `/dispatch/toggle`, `/dispatch/tick-now` actives
- ✅ 2FA gate sur toggle + tick-now (403 sans 2FA)
- ✅ Lint propre (ruff)
- ✅ Backend boot sans erreur (job `propaganda_dispatch` enregistré)

---

## Suite (13.3.x — backlog)

- [ ] Retry counter + exponential backoff sur transient failures (5xx, 429, timeout)
- [ ] Per-platform thread/reply support (X reply_to / Telegram reply_to_message_id)
- [ ] Admin UI : badge LIVE/DRY-RUN dans le top banner + bouton "Tick now"
- [ ] Webhook callback Telegram → marquer message_id côté DB (déjà capté côté tweet via response.data.id)
- [ ] Métriques : compteur Prometheus / Datadog des dispatch_outcome par platform

---

## Référence — credentials à fournir au passage en LIVE

> **Format Cabinet Vault** : catégorie `<cat>`, clé `<KEY>`, valeur = secret.

```
[telegram]
TELEGRAM_BOT_TOKEN     = 1234567890:AAGxxx...
TELEGRAM_CHAT_ID       = -100123456789  (ou @channelusername)

[x_twitter]
X_API_KEY              = AAAAAAA...
X_API_SECRET           = bbbbbbb...
X_ACCESS_TOKEN         = 1234567890-cccccc...
X_ACCESS_TOKEN_SECRET  = ddddddd...
```

→ Tester ensuite via `POST /api/admin/propaganda/dispatch/tick-now` avec `dispatch_dry_run=true` pour voir si les credentials sont bien chargés (pas d'erreur `no_credentials` dans les `results`).
