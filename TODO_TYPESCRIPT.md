# TypeScript Migration — continuation work

> Status: **Sprint 6 complete**
> 31 files migrated · 96 to go (45 are auto-generated Shadcn UI primitives, kept .jsx)
> Effective coverage: 31 / (31 + 96 - 45) = **38% of application code is TypeScript**

---

## Sprint 6 (just completed) ✅

### Major splits + .tsx migrations
- ✅ **`pages/Admin.jsx` (1252 → migrated to `Admin.tsx` + 8 split files)**
  - `pages/admin/components/StatCard.tsx`
  - `pages/admin/components/Paginator.tsx`
  - `pages/admin/components/EmailStatusBadge.tsx`
  - `pages/admin/components/ChartTooltip.tsx`
  - `pages/admin/components/EvolutionChart.tsx`
  - `pages/admin/components/AdminLogin.tsx`
  - `pages/admin/sections/WhitelistTab.tsx`
  - `pages/admin/sections/ChatLogsTab.tsx`
  - `pages/admin/sections/BlacklistTab.tsx`
  - `pages/admin/sections/SessionsTab.tsx`
  - Orchestrator `Admin.tsx` (~530 lines, only auth + data loading + tab routing)
- ✅ **`pages/AdminBots.jsx` (1912 → 1553 lines, -19%)**
  - Extracted `pages/admin/sections/NewsFeedSection.tsx` (~390 lines, self-contained)
- ✅ **`pages/AdminVault.jsx` (876 → 656 lines, -25%)**
  - Extracted `pages/admin/sections/HeliusSection.tsx` (~290 lines, self-contained)
- ✅ **`components/landing/vault/TerminalPopup.jsx` (569 → migrated to `.tsx`)** with strict types (`TerminalPhase` union, typed handlers, typed result via `AccessSession`)
- ✅ **`pages/AdminEmails.jsx` (311 → migrated to `.tsx`)** with `EmailEventEntry` + `EmailEventsState` interfaces

### Type system enhancements (`src/types/index.ts`)
- ✅ Added admin types: `AdminStatsResponse`, `AdminEvolutionPoint`, `WhitelistEntry`, `ChatLogEntry`, `BlacklistEntry`, `AdminSession`, `TwoFAStatus`, `BlacklistImportResult`, `ConfirmMode`, `ConfirmState`, `PaginatedState<T>`
- ✅ Extended `AccessSession` with optional `email` + `message` fields

### Shadcn shim
- ✅ Added `@/components/ui/table` declarations (was missing, blocking 4 sections)

### Validation
- ✅ `tsc --noEmit` passes with 0 errors
- ✅ Webpack `compiled successfully · No issues found.`
- ✅ Smoke tested: `/admin`, `/admin/bots`, `/admin/vault`, `/admin/emails`, `/classified-vault`, landing — all good.

---

## Remaining priorities (Sprint 7+)

### 🔴 P0 — Big files still in JSX (mostly unsplit on purpose for safety)
- [ ] `pages/AdminBots.jsx` (1553 lines, still heavy) — could extract Platforms / Content&LLM / Custom-LLM-Keys / Bot Studio Preview / Logs Filter sections. Lower priority since the most state-isolated section (NewsFeed) is already out.
- [ ] `pages/AdminVault.jsx` (656 lines) — could extract DexScreener section + Recent events table.
- [ ] `pages/PublicStats.jsx` (572 lines) → `.tsx` migration recommended.
- [ ] `pages/HowToBuy.jsx` (407 lines), `pages/Operation.jsx` (340 lines) → `.tsx` migration.

### 🟠 P1 — Landing components (Sprint 7 target)
- [ ] `components/landing/Hero.jsx`, `Manifesto.jsx`, `Mission.jsx`, `Roadmap.jsx`, `BrutalTruth.jsx`, `FAQ.jsx`, `Whitelist.jsx`, `Socials.jsx`, `Tokenomics.jsx`, `TransparencyTimeline.jsx`, `TopNav.jsx`, `BackgroundProject.jsx`, `ProphetPinnedWhisper.jsx`, `ROISimulator.jsx`, `ProphetChat.jsx`, `PropheciesFeed.jsx`, `ConfirmDialog.jsx`, `ActivityHeatmap.jsx`
- [ ] `components/landing/hero/*.jsx` (HeroHeadline, HeroPoster, HeroCountdown)
- [ ] `components/landing/vault/*.jsx` (VaultSection, VaultChassis, CombinationDial, VaultActivityFeed)
- [ ] `components/landing/tokenomics/*.jsx` (chart, legend, taxAndBuy)
- [ ] `components/landing/roi/*.jsx` (PriceChart, DisclaimerMarquee)

### 🟡 P2 — Pages (Sprint 8)
- [ ] `pages/Landing.jsx` (45 lines, trivial)
- [ ] `pages/ClassifiedVault.jsx`, `pages/classified-vault/*.jsx` (GateView, AuthedVaultView)

### 🟢 P3 — Misc / intro / 2FA (Sprint 9)
- [ ] `components/intro/DeepStateIntro.jsx` (314 lines, complexity 28)
- [ ] `components/intro/{TerminalWindow, MatrixRain, GlitchOverlay}.jsx`
- [ ] `components/admin/TwoFASetupDialog.jsx` (220 lines)

### 🔵 P4 — Strings / optional (Sprint 10)
- [ ] `i18n/translations.js` → `.ts` (large, mostly strings)
- [ ] Final ESLint cleanup + production `yarn build` validation pre-deploy

### 🚫 Out of scope (intentional)
- 45 Shadcn UI primitives (`components/ui/*.jsx`) — covered by `types/shadcn-shims.d.ts`. Migrating each would be high-effort, low-value for the deploy goal.

---

## Migration recipe (proven)
1. **Section extraction**: identify a self-contained block (own state, own API calls, own JSX) → create `/pages/admin/sections/<Name>.tsx` → copy state+handlers, type API responses → replace inline JSX with `<NewSection api={API} headers={headers} ... />`.
2. **Simple .jsx → .tsx**: copy file with `.tsx` extension → add `interface Props {}` → type useState calls → run `tsc --noEmit`, fix errors → delete `.jsx`.
3. **Always validate**: `tsc --noEmit` 0 errors + `supervisorctl restart frontend` + smoke test.

## Validation gate per sprint
- `npx tsc --noEmit` exits 0
- Webpack `compiled successfully · No issues found.`
- Smoke test ciblé sur les pages affectées
