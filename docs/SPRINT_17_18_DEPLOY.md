# Sprint 17 + 18 — Push GitHub & Vercel Deployment Guide

> Last updated: 2026-05-03 — TASK 7 (Prophet V2) + TASK 8 (Cadence) shipped.

This guide is the **single source of truth** for getting Sprints 17.A.2,
17.B and 18 (which all live on the preview right now) into your
production Vercel + Render deployments.

---

## TL;DR — what's in this push

### Sprint 17.A.2 + 17.B (already auto-committed)

- **Tokenomics Cards refresh** — 4 illustrated cards aligned at the same
  Y, animated with Framer Motion, coloured glows per dossier, "Allocation
  & Discipline" typographic header.
- **Transparency page refresh** — full-width "Council Screens" carousel
  with 3 AI-generated visualisation screens (distribution / rugcheck /
  operations) modeled after the landing page's On-Chain Transparency
  carousel.
- **3 new AI assets** committed to `backend/static/`:
  - `transparency_distribution.jpg`
  - `transparency_rugcheck.jpg`
  - `transparency_operations.jpg`

### Sprint 18 (this is the active diff)

- **Prophet Studio v2 (TASK 7)** — 5 weighted prompt templates (lore,
  satire_news, stats, prophecy, meme_visual) with weights 1·3·1·4·1.
  V1 stays as fallback. Toggle `prompt_v2.enabled` on the Config tab.
- **AdminBots Cadence tab (TASK 8)** — daily schedule per platform
  (X / Telegram), reactive triggers (whales, holders, marketcap),
  quiet hours window. All persisted in MongoDB `bot_config`.

---

## Files changed (Sprint 18 — currently uncommitted)

```
modified:   backend/core/bot_config_repo.py
modified:   backend/core/prophet_studio.py
modified:   backend/routers/bots.py
modified:   frontend/src/pages/AdminBots.jsx
new file:   frontend/src/pages/admin/sections/AdminCadenceSection.tsx
```

Plus a small `.emergent/emergent_todos.json` housekeeping diff (safe to
include in the push).

## Files already auto-committed (Sprint 17.A.2 + 17.B)

```
modified:   backend/core/prophet_studio.py        (+3 IMAGE_STYLE_BRIEFS)
modified:   backend/scripts/generate_email_asset.py
new file:   backend/static/transparency_distribution.jpg
new file:   backend/static/transparency_rugcheck.jpg
new file:   backend/static/transparency_operations.jpg
new file:   backend/static/transparency_distribution.meta.json
new file:   backend/static/transparency_rugcheck.meta.json
new file:   backend/static/transparency_operations.meta.json
modified:   frontend/src/components/landing/tokenomics/TokenomicsCards.tsx
modified:   frontend/src/pages/Transparency.tsx
new file:   frontend/src/components/transparency/TransparencyDataCarousel.tsx
modified:   frontend/src/index.css
modified:   frontend/src/i18n/translations.js
```

---

## Step 1 — Push from Emergent to your GitHub fork

Use the **"Push to GitHub"** button in the Emergent UI (top-right):

1. Open the Emergent project header.
2. Click **`Push to GitHub`**.
3. Confirm the commit message (suggested below).
4. Wait for the green "Push successful" toast.

### Suggested commit message

```
sprint-17-18: tokenomics cards refresh + transparency carousel +
  prompt v2 + admin cadence tab

UI
- TokenomicsCards: 4 aligned illustrations, Framer Motion animations,
  per-card coloured glow (cyan/gold/indigo/red), "Allocation &
  Discipline" font-display header.
- Transparency page: rebuilt around the "Council Screens"
  full-width carousel — 3 AI-generated screens (distribution / rugcheck
  / operations) modelled after the landing page's On-Chain Transparency
  carousel. Hero + sections now use the site-wide font-display +
  mono-kicker typography.

Backend (Prophet v2)
- prophet_studio.PROMPT_TEMPLATES_V2: lore / satire_news / stats /
  prophecy / meme_visual with weights 1·3·1·4·1.
- generate_post_v2(platform, force_template?, extra_context?) +
  list_v2_templates() helpers. V1 generate_post() stays unchanged as
  fallback when bot_config.prompt_v2.enabled = false (default).
- /api/admin/bots/v2-templates GET endpoint exposes the 5 templates
  with weights + suggested hashtags for the dashboard.
- /api/admin/bots/generate-preview now accepts use_v2 +
  force_template_v2; response carries template_used + template_label.

Backend (Cadence)
- bot_config now stores cadence.{daily_schedule, reactive_triggers,
  quiet_hours} with safe defaults.
- ALLOWED_PATCH_KEYS extended; CadencePatch with HH:MM regex
  validation, 8-slot cap, archetype whitelist.

Admin dashboard
- New Cadence tab between Preview and Jobs.
- Config tab: "Prompt V2 — 5 weighted templates" switch.
- Preview tab: "Use V2" switch + "Force template" dropdown,
  result shows V2 TEMPLATE badge with rolled archetype.

Tested end-to-end:
- backend curl on /v2-templates, /config (prompt_v2 + cadence),
  /generate-preview with use_v2=true (lore template).
- frontend screenshots on Cadence + Preview + Config tabs in
  light + dark theme.
```

---

## Step 2 — Vercel auto-deploys the frontend

Vercel watches `main`. Within ~1 minute of the push:

- Build starts automatically (`npm run build` via CRACO).
- New build is promoted to production.

You can watch the build at https://vercel.com/&lt;your-org&gt;/&lt;your-project&gt;/deployments.

### What you must verify post-deploy

1. **Hard refresh** your live URL (Cmd-Shift-R / Ctrl-F5) — there's a
   Service Worker that caches aggressively.
2. Open `/transparency`:
   - Hero title is in the large `font-display` style.
   - The 3 AI screens render in the carousel (they're served from the
     **backend** Render origin via `/api/assets/*`, so check that the
     production backend has been redeployed too — see Step 3).
3. Open the landing page → scroll to the Tokenomics section:
   - 4 cards with aligned illustrations.
   - Hover over each card → coloured glow intensifies.
4. Open `/admin/bots` (password `deepotus2026`):
   - 5 tabs visible (Config, Preview, **Cadence**, Jobs, Logs).
   - Config tab shows the "Prompt V2" toggle block.
   - Preview tab shows the V2 switch + "Force template" dropdown.
   - Cadence tab loads without errors.

### Vercel ENV variables (no change required)

The Sprint 17/18 patches are 100% backwards-compatible — they don't
introduce any new required environment variable. Reuse what's already
configured.

---

## Step 3 — Render auto-deploys the backend

Render watches the same `main` branch:

- New deploy starts automatically.
- ~3-4 minutes downtime is expected during the swap.

### What you must verify post-deploy

1. Open `https://&lt;your-render-app&gt;.onrender.com/api/admin/bots/v2-templates`
   (with `Authorization: Bearer &lt;admin_token&gt;`) — must return the 5
   templates as JSON.
2. Open `https://&lt;your-render-app&gt;.onrender.com/api/assets/transparency_distribution.jpg`
   — must return a ~50 KB JPEG (the AI illustration).
3. Open `https://&lt;your-render-app&gt;.onrender.com/api/admin/bots/config`
   — must include `prompt_v2` and `cadence` blocks at top level.

### Render ENV variables (no change required)

The Emergent LLM key + MongoDB URL stay the same. The 3 new
`transparency_*.jpg` static assets are committed to the repo — Render
serves them straight from disk via the existing `/api/assets/` mount.

---

## Step 4 — One-time post-deploy admin actions

(Optional — defaults are safe.)

1. **Enable Prompt V2** in production:
   - `/admin/bots` → Config tab → toggle "Prompt V2 — 5 weighted templates" ON.
   - The Prophet will start picking from the 5 archetypes on the next
     scheduled job (no restart required — config is read on every tick).

2. **Configure the daily schedule** for X/Telegram once you've added
   your platform credentials in `/admin/cabinet-vault`:
   - `/admin/bots` → Cadence tab → flip the platform switch ON, add up
     to 8 UTC time slots, optionally restrict the allowed archetypes.

3. **Configure quiet hours** if you want bots silent at night:
   - `/admin/bots` → Cadence tab → Quiet hours block → toggle ON, set
     start/end UTC. Window may wrap past midnight (e.g. 23:00 → 06:00).

---

## Rollback procedure

If anything goes wrong post-deploy:

1. **Vercel**: open the deployments page → find the previous green
   build → click "..." → "Promote to production". Instant rollback.
2. **Render**: same flow on Render's "Events" tab.
3. **Disable Prompt V2** without rolling back the deploy:
   - `PUT /api/admin/bots/config` `{ "prompt_v2": { "enabled": false } }`.
   - V1 `generate_post()` resumes; the V2 toggle stays in the UI but
     does nothing.

---

## Known limitations (intentional, documented)

- **Reactive triggers** (whale buys / holder milestones / mcap milestones)
  are persisted in `bot_config.cadence.reactive_triggers` but the
  scheduler does not yet consume them. Toggling the switch only stages
  the configuration. Wiring is a follow-up sprint (Sprint 19) once the
  Helius webhook moves out of demo mode.
- **KOL infiltration auto-DMs** stay in "preview-safe" mode until the X
  API tier is confirmed and credentials are entered in the Cabinet Vault.

— Council ΔΣ engineering log
