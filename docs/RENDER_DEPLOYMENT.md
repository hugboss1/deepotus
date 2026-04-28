# DEEPOTUS — Render Deployment Notes

> Standalone deployment guide for the FastAPI backend + React frontend.
> The codebase is now portable: **no `emergentintegrations` dependency**.

## What changed (Sprint 17 / "render fix")

- `requirements.txt` — `emergentintegrations==0.1.0` removed.
- New file `backend/core/llm_compat.py` — drop-in `LlmChat` / `UserMessage`
  shim that routes to the **native SDKs** (`openai`, `anthropic`,
  `google-generativeai`) already pinned in `requirements.txt`.
- All 4 production files (`core/llm_router.py`, `core/tone_engine.py`,
  `core/prophet_studio.py`, `routers/public.py`) updated to import from
  `core.llm_compat` instead.
- 7 one-shot generator scripts patched the same way.
- The shim **gracefully falls back** when no provider key is configured:
  the propaganda templates ship verbatim instead of being LLM-enriched —
  no crash, no error visible to end-users.

## Render env vars required at minimum

Copy these from the local `backend/.env` into Render's
*Environment Variables* panel (Dashboard → Service → Environment).
**Never commit** any of the values below to git.

| Variable                     | Required? | What for                                                          |
|------------------------------|-----------|--------------------------------------------------------------------|
| `MONGO_URL`                  | ✅ yes     | Mongo Atlas connection string                                      |
| `DEEPOTUS_LAUNCH_ISO`        | ✅ yes     | ISO timestamp of the public mint (drives the seal status)          |
| `SECRETS_KEK_KEY`            | ✅ yes     | KEK for Cabinet Vault wrapping                                     |
| `HELIUS_API_KEY`             | ✅ yes     | On-chain swap monitoring (free tier OK at 100k credits/month)      |
| `HELIUS_WEBHOOK_AUTH`        | ✅ yes     | Signing secret for the `/api/webhooks/helius` endpoint             |
| `TELEGRAM_BOT_TOKEN`         | for TG    | The `123:ABC...` value from @BotFather                             |
| `TELEGRAM_CHAT_ID`           | for TG    | Negative supergroup id where the bot must be admin                 |
| `X_BEARER_TOKEN`             | for X     | OAuth2 bearer for read endpoints                                   |
| `X_CLIENT_ID`                | for X     | OAuth2 user-context (post / DM)                                    |
| `X_CLIENT_SECRET`            | for X     | OAuth2 user-context (post / DM)                                    |
| `BONKBOT_REF_URL`            | optional  | Affiliate URL surfaced on `/how-to-buy`                            |
| `TROJAN_REF_URL`             | optional  | Affiliate URL surfaced on `/how-to-buy`                            |
| `OPENAI_API_KEY`             | LLM tone  | Enables Tone Engine + Prophet rewrites; gpt-4o-mini ≈ $1/month     |
| `ANTHROPIC_API_KEY`          | LLM tone  | Alternative to OpenAI; Claude Sonnet 4.5 used for Prophet replies  |
| `GEMINI_API_KEY`             | LLM tone  | Alternative; free tier covers light usage                          |
| `RESEND_API_KEY`             | for email | Loyalty + clearance email pings                                    |
| `RESEND_WEBHOOK_SECRET`      | for email | Inbound webhook signature                                          |
| `SENDER_EMAIL`               | for email | The `From:` address                                                |

## LLM key strategy on Render

The shim resolves keys in this order:

```
<PROVIDER>_API_KEY env  →  Cabinet Vault llm_custom/<KEY>  →  api_key passed to LlmChat()
```

Recommended: **set just `OPENAI_API_KEY`** with a $5 starter credit.
Cost on `gpt-4o-mini` for the volumes this app generates is
~ $0.50 / month.

If you set **none** of the LLM keys, the app still works:
propaganda is sent using the seeded templates verbatim; only the
"tone enhancement" layer is bypassed.

## Helius webhook configuration (post-deploy)

Once the Render service is live at e.g. `https://deepotus.onrender.com`:

1. Helius dashboard → Webhooks → New webhook.
2. URL: `https://deepotus.onrender.com/api/webhooks/helius`
3. Auth header: `Bearer <HELIUS_WEBHOOK_AUTH>` (the value from your env).
4. Filter: choose `swap` events on the $DEEPOTUS pool address (set later
   via admin → Vault → Classified Status Override once the pool exists).

Until the pool address is set, the webhook will be received but treated
as demo data. The `whale_alerts` queue still accepts `simulate` calls
so you can verify the propaganda pipeline immediately.

## Credentials rotation to do post-launch

Because every value above transited through the chat history during
onboarding, rotate them once the project is publicly live:

| Credential          | How to rotate                                                              |
|---------------------|----------------------------------------------------------------------------|
| `X_BEARER_TOKEN`    | developer.x.com → Apps → DEEPOTUS → "Regenerate Bearer Token"              |
| `X_CLIENT_SECRET`   | developer.x.com → Apps → DEEPOTUS → OAuth 2.0 → "Regenerate"               |
| `TELEGRAM_BOT_TOKEN`| Telegram → @BotFather → `/revoke` → choose the bot → take the new token   |
| `HELIUS_API_KEY`    | helius.dev dashboard → Settings → Regenerate                               |
| `SECRETS_KEK_KEY`   | Roll only via the Cabinet Vault `rotate KEK` admin flow (existing endpoint)|

Then update the Render env vars panel with the new values and migrate
secrets that need richer storage to the **Cabinet Vault** through the
admin UI (`/admin/cabinet`).

## Pre-push checklist

Before the next `git push` (or "Save to GitHub" via the Emergent UI):

- [ ] `backend/.env` is gitignored (it is, verified by `git check-ignore`)
- [ ] No raw token strings are committed (verified by signature greps)
- [ ] `requirements.txt` does NOT contain `emergentintegrations` (done)
- [ ] All four production files import from `core.llm_compat` (done)
- [ ] `pip install -r requirements.txt` completes without errors (done)
- [ ] `python -c "from core.llm_compat import LlmChat, UserMessage"` succeeds (done)
