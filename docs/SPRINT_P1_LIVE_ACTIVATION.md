# Sprint P1 — Production Activation: X + Telegram Live Dispatch + KOL Polling

Date: 2026-05-03
Scope: flip production from "dry-run + admin-simulate" to **fully live**
on deepotus.xyz, now that the X Developer account has Pay-Per-Use
credits.

---

## 1. Code changes in this session

### 1.1 `core/kol_listener.py` — live X polling wired

**Before** (documented stub): `poll_x_api_once()` contained a TODO
block and the `_fetch_kol_recent_tweets` symbol only existed in the
docstring. The listener drained admin-simulated mentions but never
actually called X.

**After**: two new helpers + a full rewrite of `poll_x_api_once()`.

| Symbol                      | Auth            | Endpoint                                                    |
| --------------------------- | --------------- | ----------------------------------------------------------- |
| `_resolve_user_id(handle)`  | Bearer (app)    | `GET /2/users/by/username/:handle`                          |
| `_fetch_kol_recent_tweets`  | Bearer (app)    | `GET /2/users/:id/tweets?exclude=retweets,replies…`         |

Collections added:

- `kol_user_id_cache` — handle → user_id (TTL 7 days via Mongo TTL index).
- `kol_poll_state` — handle → `last_seen_id` for `since_id` continuation.

### 1.2 Bootstrap rule — no historic flood on day 1

On the **first poll** for a handle (no `last_seen_id` yet), the listener
records X's `meta.newest_id` as the baseline and **drops** the batch. This
prevents a 100-tweet backfill from swamping the propaganda approval queue
the moment the operator flips `enabled=true`.

Subsequent ticks fetch only tweets **strictly newer** than the stored
`last_seen_id`, filter by `match_terms` (case-insensitive substring), and
enqueue the hits via the existing `enqueue_mention()` path (which already
dedups on `tweet_id`).

### 1.3 Rate-limit awareness

With Pay-Per-Use + Bearer, both endpoints fit comfortably under the
ceilings: at **10 handles × 1 tick / 5 min → 120 req/hour**, far below
the 300/15min (user lookup) and 1500/15min (tweets) caps. On a 429,
the listener **bails that handle** for the tick without crashing.

### 1.4 Tests

- `tests/test_kol_listener_helpers.py` — 6 cases on `_match_terms_hit`.
- **Backend total: 25 → 57 → 63 tests**.

### 1.5 Dispatchers — **NO CODE CHANGE**

Both `core/dispatchers/x.py` and `core/dispatchers/telegram.py` are
**already real**:

- X: OAuth1.0a → `POST /2/tweets`, retries, timeout, error mapping
  (`x_unauthorized`, `x_tier_locked`, `x_rate_limited`, `http_*`).
- Telegram: `POST /bot<TOKEN>/sendMessage` with Markdown, 4096-char
  guard, transient/permanent classification.

Activation is a **config flip**, not a code change — see §2 below.

---

## 2. Production activation runbook (in order)

### Step 1 — Add secrets to Cabinet Vault

Navigate to https://www.deepotus.xyz/admin/cabinet-vault, unlock with
the mnemonic + admin password + 2FA, and add **seven** secrets under
the listed namespaces:

| Namespace       | Key                         | Value                                                           |
| --------------- | --------------------------- | --------------------------------------------------------------- |
| `telegram`      | `TELEGRAM_BOT_TOKEN`        | `NNNNNNNNNN:AA…` (from @BotFather)                              |
| `telegram`      | `TELEGRAM_CHAT_ID`          | `@deepotus_channel` or `-100XXXXXXXXXX` (channel id)            |
| `x_twitter`     | `X_API_KEY`                 | OAuth1 consumer key                                             |
| `x_twitter`     | `X_API_SECRET`              | OAuth1 consumer secret                                          |
| `x_twitter`     | `X_ACCESS_TOKEN`            | OAuth1 access token (generated for the bot account)             |
| `x_twitter`     | `X_ACCESS_TOKEN_SECRET`     | OAuth1 access token secret                                      |
| `x_twitter`     | `X_BEARER_TOKEN`            | App-only bearer token (**required for KOL polling**)            |

> **Do NOT put any of these in Render env vars.** The vault is the
> source of truth post-prod; env vars remain a dev-only fallback.

### Step 2 — Preflight check

```bash
curl -H "Authorization: Bearer $ADMIN_JWT" \
  https://www.deepotus.xyz/api/admin/propaganda/dispatch/preflight
```

Expected response:

```json
{
  "telegram": { "ready": true, "bot_token": "present", "chat_id": "present" },
  "x":        { "ready": true, "api_key": "present", "api_secret": "present",
                "access_token": "present", "access_token_secret": "present" }
}
```

If any field is `"missing"`, revisit Step 1.

### Step 3 — Activate Telegram first (lower blast-radius)

```bash
# Still dry-run, but now with real creds resolved
curl -X POST -H "Authorization: Bearer $ADMIN_JWT" \
     -H "X-2FA-Code: 123456" \
     https://www.deepotus.xyz/api/admin/propaganda/dispatch/tick-now
# Expect: item goes approved → sent, dry_run=true, message_id="dry-run"
```

Once the dry-run posts cleanly, flip **live**:

```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_JWT" -H "X-2FA-Code: 123456" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "dry_run": false, "platforms": {"telegram": true, "x": false}}' \
  https://www.deepotus.xyz/api/admin/propaganda/dispatch/toggle
```

Approve one queue item through the admin UI; verify the post lands in
the Telegram channel within ~30s.

### Step 4 — Activate X

Same as Step 3 but with `"x": true`. Watch the first approved tweet
publish on the bot account, then leave both platforms enabled.

### Step 5 — Enable the KOL listener

The `kol_config` singleton is `enabled=false` by default. Open
`/admin/propaganda` → KOL section → toggle `enabled=true`. First tick
after enabling will **silently baseline** each handle (no queue flood)
and subsequent ticks will propose posts for real mentions.

### Step 6 — Panic button

If **anything** goes sideways (wrong account posting, spam flood,
credentials leaked):

```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_JWT" -H "X-2FA-Code: 123456" \
  -H "Content-Type: application/json" \
  -d '{"panic": true}' \
  https://www.deepotus.xyz/api/admin/propaganda/dispatch/toggle
```

`panic=true` hard-disables every dispatcher and the KOL listener in a
single atomic write. Re-enable only after post-mortem.

---

## 3. Render + Vercel — what needs changing

### Vercel (frontend)

**Nothing.** The frontend is pure SPA — no runtime secrets, no
webhook routing. The existing `REACT_APP_BACKEND_URL` already points
at the Render backend. Redeploy only when you ship frontend changes.

### Render (backend)

Exactly **two** things, and neither is code:

1. **Restart the backend service** after Step 1 so the APScheduler
   picks up the fresh vault secrets (the `SecretProvider` cache TTL is
   60s, but a clean restart is cleaner).
   → Render dashboard → `deepotus-backend` → **Manual Deploy → Clear
   build cache & deploy**.
2. **Verify env vars are clean** — only `MONGO_URL`, `CORS_ORIGINS`,
   and `CABINET_VAULT_KEK` should live there. No X/TG/Helius keys;
   those are vault-owned.

No new env vars are required by Sprint P1 code.

### Helius webhooks

Unchanged by this sprint. They stay at their post-mint config per
`/app/docs/HELIUS_POST_DEPLOY.md` and are **independent** of the X/TG
dispatchers.

---

## 4. Credential rotation playbook

Rotation is mandatory every 90 days and after any suspected leak.
Follow the sequence below per platform; **never revoke the old
credential before the new one is installed and verified**.

### 4.1 Telegram bot token

1. Message [@BotFather](https://t.me/BotFather) → `/mybots` → your bot →
   `API Token` → **Revoke current token** (DO NOT CLICK YET — just have
   the screen open).
2. In a separate tab, generate a new token: `/revoke` → confirm. You
   get the new token inline.
3. In the vault, **update** `telegram/TELEGRAM_BOT_TOKEN` with the new
   value (old values are kept in the vault audit log — never shown
   again in the UI).
4. Preflight + tick-now dry-run. If OK, you're done. The old token is
   now dead; no revocation step needed (BotFather replaces it in one
   move).

### 4.2 X OAuth1 keys (bot account)

1. developer.x.com → your project → your app → **Keys & Tokens**.
2. **Regenerate Access Token & Secret** (keep the app's API Key/Secret
   stable — regenerating those breaks the app itself).
3. Update `x_twitter/X_ACCESS_TOKEN` and `x_twitter/X_ACCESS_TOKEN_SECRET`
   in the vault.
4. Preflight + tick-now dry-run on the X dispatcher.
5. Full rotation of the App itself (every 12 months or on suspected
   app-level leak): regenerate **API Key & API Secret** too, update
   `x_twitter/X_API_KEY` and `x_twitter/X_API_SECRET`, re-run Step 4.

### 4.3 X bearer token (KOL polling)

1. developer.x.com → Keys & Tokens → **Bearer Token** → **Regenerate**.
2. Update `x_twitter/X_BEARER_TOKEN` in the vault.
3. Trigger a manual poll: `POST /api/admin/kol/poll-now` (2FA gated).
   Expect `polled=true, handles_processed=N`.

### 4.4 Rotation log

Every rotation **must** be recorded in the vault audit trail
(automatic — `/admin/cabinet-vault` → Audit tab). Additionally, write a
short note in `docs/ROTATION_LOG.md` with (date, platform, reason,
operator). This is part of the MiCA compliance posture.

### 4.5 Post-incident rotation

If a key is suspected compromised:

1. **Panic button first** (Step 6 of §2) — stops all dispatch + KOL
   polling instantly.
2. Rotate in the order: bearer → OAuth1 access → TG token → app-level
   API key (worst → best blast-radius).
3. After each update, run preflight to confirm the system still sees
   the keys.
4. Re-enable dispatch platform-by-platform; don't flip everything at
   once.

---

## 5. Definition of done

- [x] `core/kol_listener.py`: `_fetch_kol_recent_tweets` + `_resolve_user_id`
      implemented against X API v2, `poll_x_api_once()` rewritten to
      drive real polling with `since_id` continuation.
- [x] `kol_user_id_cache` + `kol_poll_state` collections + TTL index.
- [x] `tests/test_kol_listener_helpers.py` — 6 new cases, all green.
- [x] Backend pytest: **63 passed**.
- [x] Backend restarts cleanly; no runtime errors in supervisor logs.
- [x] Dispatchers confirmed already real (no code change needed).
- [x] Activation runbook documented (§2).
- [x] Render/Vercel delta documented (§3).
- [x] Rotation playbook documented (§4).

## 6. Backlog after this session

- **Operator tasks** (not code): Step 1–6 of §2 — flip production live
  once the operator adds the 7 secrets.
- **Sprint P2** — per-handle cooldown (don't post twice within 4h for
  the same KOL even if they mention us back-to-back) to protect the
  X rate-limit budget + avoid looking spammy.
- **Sprint P3** — admin UI page showing the last poll tick summary +
  per-handle `last_seen_id` state, for easier troubleshooting. Hook
  into the existing `/admin/propaganda` layout.
- **Sprint 25 / 26** remain as in `/app/docs/SPRINT_14_2_23_24_DEPLOY.md`.
