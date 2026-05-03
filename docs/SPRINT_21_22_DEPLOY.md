# Sprint 21 + 22 — Push GitHub & Deploy Guide

> Last updated: 2026-05-03 — refactor sprint, no behaviour change.

This guide covers the **Sprint 21** (refactor) and **Sprint 22.1**
(TypeScript migration pilot) shipped in this round. Pure code-quality
work — zero new features, zero user-facing behaviour change. Push +
deploy is mechanical; verify checklist is short.

---

## TL;DR

### Sprint 21 — Refactor (zero new features)
- **AdminBots.jsx**: 1798 → 1017 lines (-43%). Three giant tab blocks
  (Preview, Jobs, Logs) extracted into dedicated section components.
- **cadence_engine.py**: two complex orchestrators split into pure
  helpers; 25 unit tests added covering the helpers exhaustively.

### Sprint 22.1 — TypeScript migration pilot (3 files)
- `src/index.js` → `src/index.tsx`
- `src/App.js` → `src/App.tsx`
- `src/pages/AdminBots.jsx` → `src/pages/AdminBots.tsx` + minimal
  `BotConfig` / `ContentTypeMeta` interfaces.
- 6 section components: relaxed `AxiosRequestHeaders` →
  `Record<string, string>` so the parent's plain header object is
  assignable without a cast.

---

## What changed (file list)

### New files
```
backend/tests/test_cadence_engine_helpers.py          # 25 unit tests
frontend/src/pages/admin/sections/AdminJobsSection.tsx
frontend/src/pages/admin/sections/AdminLogsSection.tsx
frontend/src/pages/admin/sections/AdminPreviewSection.tsx
frontend/src/index.tsx                                # was index.js
frontend/src/App.tsx                                  # was App.js
docs/SPRINT_21_22_DEPLOY.md                           # this file
```

### Modified
```
backend/core/cadence_engine.py                        # split helpers
frontend/src/pages/AdminBots.jsx → AdminBots.tsx      # rename + minimal types
frontend/src/pages/admin/sections/AdminCadenceSection.tsx
frontend/src/pages/admin/sections/LoyaltySection.tsx
frontend/src/pages/admin/sections/NewsRepostSection.tsx
```

### Deleted
```
frontend/src/index.js          (replaced by index.tsx)
frontend/src/App.js            (replaced by App.tsx)
```

### Suggested commit message

```
sprint-21+22: AdminBots refactor (-43% lines) + cadence_engine split
  + 25 unit tests + TypeScript migration pilot

Refactor (Sprint 21)
- AdminBots.jsx: extract Preview / Jobs / Logs tabs into dedicated
  section components (each owns its own state + auto-refresh poll).
  Page goes from 1798 → 1017 lines, -43%. Matches the existing
  Cadence / Loyalty / NewsRepost / NewsFeed section pattern.
- cadence_engine.py: split cadence_reactive_tick (cyclo 28) into
  _tick_marketcap_milestones + _tick_holder_milestones + a pure
  _crossed_milestone helper. Split cadence_daily_tick (cyclo 18)
  into a pure _iter_due_slots generator. Orchestrator functions
  are now thin coordinators around the helpers.
- 25 unit tests in tests/test_cadence_engine_helpers.py covering
  parse_hhmm, is_in_quiet_hours (incl. wrap past midnight),
  pick_archetype, _iter_due_slots, _crossed_milestone, format_mc_label.
  All green in 1.6 s.

TypeScript migration pilot (Sprint 22.1)
- index.js → index.tsx (entry point)
- App.js → App.tsx (router shell, all page imports kept)
- AdminBots.jsx → AdminBots.tsx with minimal BotConfig / ContentTypeMeta
  interfaces. Inner sub-doc state stays implicit-any per tsconfig
  (strict: false / noImplicitAny: false).
- 6 section components: relax `AxiosRequestHeaders` →
  `Record<string, string>` so plain `{ Authorization: \"Bearer …\" }`
  is assignable.

Tested
- pytest tests/test_cadence_engine_helpers.py -v → 25 passed in 1.6s
- ruff check (entire backend) → all checks passed
- ESLint (entire frontend) → no issues found
- webpack compiled successfully, all 5 admin tabs render
- screenshot validation: Config / Preview / Cadence / Jobs / Logs all OK
- AdminBots.tsx: 51.2 KB bundle (no regression vs .jsx)
```

---

## Step 1 — Push from Emergent

Click **`Push to GitHub`** in the Emergent UI top-right. The pre-deploy
state of the repo is already auto-committed. Confirm + green toast.

---

## Step 2 — Vercel + Render auto-redeploy

No env-var changes, no schema changes. Watch the build, hard-refresh
the live URL, and verify:

1. Landing page loads cleanly (the `index.tsx` migration is the only
   thing that matters here — if the page renders, the build is good).
2. Admin login works (`/admin` → password → kick to `/admin/cabinet-vault`
   landing).
3. `/admin/bots`:
   - Hard refresh.
   - All 5 tabs (Config / Preview / Cadence / Jobs / Logs) render.
   - Switch between tabs — each section fetches its own data and
     renders independently.
   - `Custom LLM keys` block still renders the same modal flow as
     before (this is the part that touches `BotConfig`-typed state
     the most, so it's the canary for the AdminBots TS migration).
4. Backend: `pytest backend/tests/ -v` → green when run locally. The
   25 cadence-engine helper tests are the only new tests.

---

## Step 3 — Optional verification

Run the full test suite locally to be safe:

```bash
cd backend
python3 -m pytest tests/ -v
```

Expected: at minimum the 25 tests in
`test_cadence_engine_helpers.py` pass. Other test files are
out-of-scope for this sprint and may have pre-existing skips.

---

## What's still pending after this sprint

- **AdminVault.jsx** (665 lines) — next candidate for `.tsx`
  migration, likely Sprint 22.2.
- **Custom LLM keys dialog** inside `AdminBots.tsx` (~250 lines of
  the 1017-line file) — could be extracted into
  `AdminLLMKeysDialog.tsx` for further decomposition. Sprint 22.3.
- **Other complex Python functions** flagged in the original code
  review (`import_encrypted`, `sync_jobs_from_config`) — left
  intentionally untouched per the *risk-vs-benefit* analysis we
  documented in `docs/CODE_REVIEW_RESPONSE.md` §5. Reconsider after
  the launch window closes.
- **TypeScript strict mode** — currently `strict: false`, which
  worked for this pilot. Bumping it to true is itself a multi-sprint
  effort and should follow the legacy file migration, not lead it.

---

## Rollback

Pure refactor sprint — every change is internal. If anything breaks
post-deploy, **immediate rollback** is safe:

- **Vercel**: promote the previous deploy (Sprint 19.1) from the
  Deployments page. ~30 s.
- **Render**: same flow on the Events tab.

The previous deploy contains the original `.jsx` files and the
unsplit `cadence_engine.py` — no data migration, no schema change,
no deploy-state coupling.

— Council ΔΣ engineering log
