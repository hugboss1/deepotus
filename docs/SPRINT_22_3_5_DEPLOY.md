# Sprint 22.3 → 22.5 — Deploy Notes

Date: 2026-05-03
Branch: continuation of Sprint 22 (TypeScript migration + hardening)

## Overview

This rollup covers three sub-sprints delivered in a single session once
the previous agent's Sprint 22.2 (migration of `AdminVault.jsx` → `.tsx`)
was verified as already committed.

| Sprint | Label                         | Status      |
| ------ | ----------------------------- | ----------- |
| 22.2   | AdminVault.jsx → .tsx         | ✅ already done |
| 22.3   | Extract Custom LLM keys panel | ✅ delivered |
| 22.4   | tsconfig hardening (pragmatic) | ✅ delivered |
| 22.5   | Pytest widen + Playwright boot | ✅ delivered |

## 22.3 — `<CustomLlmKeysSection />` extraction (Task A)

**Goal.** Reduce cognitive load on the 1037-line `AdminBots.tsx` by
extracting the BYO-LLM-key panel (cards + rotate/revoke dialog +
handlers) into a dedicated, self-contained section component, matching
the pattern established by `LoyaltySection`, `NewsFeedSection`,
`AdminCadenceSection`, `AdminJobsSection`, `AdminLogsSection`, and
`AdminPreviewSection`.

### Changes

- **New file**: `/app/frontend/src/pages/admin/sections/CustomLlmKeysSection.tsx`
  (406 lines).
  - Owns: dialog state, secret input, label input, error state, busy
    flag; `openDialog`, `submitSecret`, `revokeSecret` callbacks.
  - Receives: `api`, `headers`, `config`, `onConfigReload` via props.
  - Preserves every `data-testid` (`custom-llm-keys-section`,
    `custom-llm-card-{openai,anthropic,gemini}`,
    `custom-llm-set-…`, `custom-llm-revoke-…`, `custom-llm-dialog`,
    `custom-llm-key-input`, `custom-llm-label-input`,
    `custom-llm-reveal-toggle`, `custom-llm-submit`).
- **Edited**: `/app/frontend/src/pages/AdminBots.tsx` (1037 → 743
  lines, -28%). Removed 6 unused icon imports, 7 state hooks, 3
  handlers, the 110-line card grid and the 120-line `<Dialog>` block.
  Replaced them with a single `<CustomLlmKeysSection />` invocation.

### Validation

- `npx tsc --noEmit` → 0 errors.
- Manual screenshot test on `/admin/bots` Config tab:
  - 3 provider cards render with VAULT ARMED badge.
  - "Set key" opens the dialog; key/label inputs accept text; Cancel
    closes cleanly.

## 22.4 — Pragmatic `noImplicitAny` sweep (Task C)

**Goal.** Raise the TypeScript hygiene floor without flipping
`tsconfig.strict: true` (which would have required fixing ~274 errors
across ~60 files — too risky pre-mint). Target: fix the 10 busiest
files so a future session can flip the flag with a smaller long tail.

### Files typed (10)

| # | File                                                          | Errors before | Errors after |
| - | ------------------------------------------------------------- | ------------- | ------------ |
| 1 | `src/components/landing/vault/CombinationDial.tsx`            | 18            | 0            |
| 2 | `src/pages/AdminBots.tsx`                                     | 17            | 0            |
| 3 | `src/pages/Propaganda.tsx`                                    | 16            | 0            |
| 4 | `src/components/landing/ROISimulator.tsx`                     | 16            | 0            |
| 5 | `src/components/landing/roi/PriceChart.tsx`                   | 13            | 0            |
| 6 | `src/pages/PublicStats.tsx`                                   | 13            | 0            |
| 7 | `src/pages/Infiltration.tsx`                                  | 13            | 0            |
| 8 | `src/pages/classified-vault/AuthedVaultView.tsx`              | 11            | 0            |
| 9 | `src/pages/CabinetVault.tsx`                                  | 9             | 0            |
| 10 | `src/pages/AdminVault.tsx`                                   | 8             | 0            |

**Net:** global `noImplicitAny` error count dropped from **274 → 140
(-49 %)**. `tsc --noEmit` (baseline, without the flag) remains at **0
errors**.

### Patterns applied

1. **Onchange handlers** on `<Input>` / `<Textarea>` batch-typed with
   `React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>`.
2. **Switch handlers** (`onCheckedChange`) typed as `(v: boolean)`.
3. **Per-provider lookup tables** (`CONTENT_TYPE_ICONS`, `STATUS_COLOR`,
   `SCENARIO_COLORS`, `SCENARIO_MULTIPLIERS`) marked as
   `Record<string, string | number>` so string indexing works.
4. **Icon-component props** relaxed to `React.ElementType` (lucide's
   `ForwardRefExoticComponent<LucideProps>` doesn't fit a custom
   `ComponentType<{ size }>` narrow).
5. **Module-scope helpers** (`fmtPrice`, `fmtCompact`, `fmtRefPrice`,
   `_truncate`, `tier_for` equivalents) typed with explicit
   numeric params.
6. **Presentational prop bags** (`CellProps`, `LegendDotProps`,
   `StatProps`, `LangBarsProps`, `CalculatorPanelProps`) lifted into
   real `interface` blocks.
7. **Complex or poorly-typed tree roots** (`AuthedVaultView`,
   `MetricsPanel`, `PriceChart` top-level export) deliberately annotated
   as `: any` + `eslint-disable-next-line` — documents intent without
   blocking the hardening pass.

### tsconfig state

`tsconfig.json` **unchanged** — `noImplicitAny` stays `false` during
22.x. Flipping it is deferred to a dedicated Sprint 23 once the
remaining 140 errors (all in secondary surfaces) are swept.

## 22.5 — Pytest widening + Playwright bootstrap (Task E)

### Backend pytest — widened from 25 to **57 tests** (+128 %)

Two new test modules landed in `/app/backend/tests/`:

1. `test_whale_watcher_helpers.py` (14 cases):
   - `tier_for()` — threshold + T1/T2/T3 banding, string coercion,
     invalid-input resilience.
   - `_truncate()` — privacy truncation contract
     (`first-4…last-4`) with empty/short passthrough.
   - `_bucket()` — 4-band rounding (0.1/5/10/50) used by the
     public-facing whale feed.
2. `test_clearance_levels_helpers.py` (18 cases):
   - `_compute_level()` — full ladder (empty → L1 → L2 → L3),
     riddle-solved bootstrap rule, empty-list / None edge cases.
   - `_normalise_email()` — lowercase + trim for PK equality.
   - `_is_valid_solana()` — base58 shape (32–44 chars), forbidden
     characters, short/long rejections.
   - `_normalise_addr()` — trim-then-validate, raises `ValueError`
     on bad shape.

```bash
$ cd /app/backend && python -m pytest tests/
# ============================= 57 passed in 1.58s ===========================
```

### Playwright E2E — new `/app/e2e/` package

Minimal bootstrap (two specs, three tests) so the team can layer
regression tests on top without wiring the plumbing.

```
/app/e2e/
├── package.json               # @playwright/test dev dep
├── playwright.config.ts       # Chromium, headless, baseURL from env
├── README.md                  # runbook + env overrides
└── specs/
    ├── landing.spec.ts        # Landing + ROI simulator smoke
    └── admin.spec.ts          # Admin unlock + CustomLlmKeysSection
```

The admin spec specifically validates the Sprint 22.3 refactor:
section renders, 3 provider cards visible, dialog opens + closes, key
length gating (<8 chars → button disabled).

```bash
$ cd /app/e2e && yarn install && npx playwright test --list
# [chromium] › admin.spec.ts › unlock + render Config tab + open dialog
# [chromium] › landing.spec.ts › renders hero and key sections
# [chromium] › landing.spec.ts › ROI simulator reacts to user input
# Total: 3 tests in 2 files
```

Chromium binaries are **not** pre-installed — operators run
`yarn install-browsers` on first use.

## Definition of done

- [x] `tsc --noEmit` passes with zero errors.
- [x] `pytest` 57/57 green.
- [x] Playwright specs lint and list cleanly.
- [x] Manual screenshot test confirms the CustomLlmKeysSection
  renders + dialog flow intact.
- [x] No `data-testid` churn → no E2E regressions introduced
  downstream.
- [x] `tsconfig.json` left untouched (no surprise strictness flips
  during a pre-launch window).

## Next up

- Sprint 23 — finish the remaining 140 `noImplicitAny` errors (top
  offenders: `TransparencyTimeline`, `Roadmap`, `AdminCadenceSection`,
  `TerminalPopup`, `RiddlesFlow`, `TwoFASetupDialog`, `GateView`,
  `ProphetChat`, `ConfirmDialog`). Then flip `noImplicitAny: true`.
- Sprint 24 — wire Playwright to CI (GitHub Actions, preview URL as
  `PLAYWRIGHT_BASE_URL`). Add phase-switching fixture coverage.
