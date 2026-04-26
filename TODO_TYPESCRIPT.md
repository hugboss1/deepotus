# TypeScript Migration — continuation work

> Status: **infrastructure ready + Sprint 5 split complete**
> 16 files migrated · 99 to go (16/115 = 14% coverage)
> AdminBots.jsx: 2700+ → **1912 lines** after Loyalty + NewsRepost extraction

---

## Sprint 5 (just completed) ✅

### Component splits — pattern established
- ✅ `LoyaltySection.tsx` — extracted from AdminBots (~280 lines), self-contained
- ✅ `NewsRepostSection.tsx` — extracted from AdminBots (~340 lines), self-contained
- AdminBots.jsx reduced by **~670 lines** (2575 → 1912)

### TS migrations
- ✅ `components/landing/Footer.jsx` → `.tsx`
- ✅ `components/landing/LanguageToggle.jsx` → `.tsx`
- ✅ `components/landing/ThemeToggle.jsx` → `.tsx`
- ✅ `components/intro/hackScripts.js` → `.ts`
- ✅ `lib/adminAuth.js` → `.ts`
- ✅ `pages/classified-vault/useClassifiedSession.js` → `.ts`

### Infrastructure improvements
- ✅ `types/shadcn-shims.d.ts` — type shim so .tsx components can use Shadcn UI without TS errors (pragmatic `any` widening, replaceable file-by-file as primitives migrate)
- ✅ `types/index.ts` — added `LoyaltyStatus / LoyaltyTier / LoyaltyEmailStats / LoyaltyTestSendResult / NewsRepostStatus / NewsRepostQueueItem / NewsRepostTestResult` interfaces
- ✅ `i18n/I18nProvider.tsx` — relaxed `t()` return type from `unknown` to `any` so .tsx callers don't need wrappers

---

## Remaining priorities (Sprint 6+)

### 🔴 P0 — Big component splits (continue Sprint 5 pattern)
- [ ] `pages/Admin.jsx` (1075 lines) → extract Analytics tab, Vault Prophet tab, Whitelist tab into TSX sections
- [ ] `pages/AdminBots.jsx` (1912 lines, still big) → extract:
  - News Feed section (~150 lines, similar pattern)
  - Bot Studio / Preview section
  - Content Types section
- [ ] `pages/AdminVault.jsx` (850 lines) → split into VaultPresetEditor, VaultPlanList, VaultDevTools
- [ ] `components/landing/vault/TerminalPopup.jsx` (540 lines) → split phases (idle / request / digicode / declassified) into sub-components
- [ ] `pages/PublicStats.jsx` (461 lines)

### 🟠 P1 — Convert smaller .jsx files (low-effort, high coverage)
- [ ] `components/landing/vault/*.jsx` (VaultSection, VaultChassis, VaultMolettes — ~1200 lines)
- [ ] `components/landing/hero/*.jsx` (HeroHeadline, HeroPoster, HeroCountdown — ~800 lines)
- [ ] `components/landing/tokenomics/*.jsx` (~600 lines)
- [ ] `components/landing/classified-vault/*.jsx` (~700 lines)
- [ ] `components/landing/Hero.jsx`, `Manifesto.jsx`, `Mission.jsx`, `Roadmap.jsx`, `BrutalTruth.jsx`, `FAQ.jsx`, `Whitelist.jsx`, `Socials.jsx`, `ROISimulator.jsx`, `ProphetChat.jsx`, `PropheciesFeed.jsx`, `Tokenomics.jsx`, `TransparencyTimeline.jsx`, `TopNav.jsx`, `BackgroundProject.jsx`, `ProphetPinnedWhisper.jsx`
- [ ] `components/admin/TwoFASetupDialog.jsx` (203 lines, complexity 18)
- [ ] `components/landing/ActivityHeatmap.jsx` (84 lines, complexity 17)

### 🟢 P2 — Pages
- [ ] `pages/Landing.jsx` (45 lines, trivial)
- [ ] `pages/AdminEmails.jsx`
- [ ] `pages/classified-vault/*.jsx`

### 🟡 P3 — Misc
- [ ] `components/intro/DeepStateIntro.jsx` → `.tsx` (213 lines, complexity 28 — refactor + types together)
- [ ] `components/intro/TerminalWindow.jsx`, `MatrixRain.jsx`, `GlitchOverlay.jsx`
- [ ] `i18n/translations.js` → `.ts` (large, mostly strings — optional)

### 🔄 Type-shim debt
The `types/shadcn-shims.d.ts` uses `any` widening for ergonomics. As we migrate each Shadcn primitive to .tsx with proper types, the corresponding `declare module` block should be deleted. Track per-file in this file.

---

## Migration recipe (proven during Sprint 5)
1. **For a section split** :
   - Identify a self-contained block (own state, own API calls, own JSX)
   - Create new file under `/pages/admin/sections/<Name>.tsx`
   - Copy state + handlers, type the API responses with interfaces in `/types/index.ts`
   - Replace inline JSX with `<NewSection api={API} headers={headers} />`
   - Delete the now-orphaned state/handlers from the parent
   - Run `tsc --noEmit` → if Shadcn errors appear, add to `shadcn-shims.d.ts`
2. **For a simple .jsx → .tsx** :
   - Copy file with `.tsx` extension
   - Add `interface Props { ... }`
   - Type state hooks (`useState<T>`)
   - Run `tsc --noEmit`, fix errors
   - Delete the old `.jsx`
   - `supervisorctl restart frontend` if hot-reload didn't pick up

## Validation gate
Every migration session ends with:
- `npx tsc --noEmit` exits 0
- `npx eslint src/...` exits 0
- webpack compiled successfully
- Visual smoke test on the affected page
