# TypeScript Migration — continuation work

> Status: **infrastructure ready · 6 files migrated · 60+ files remaining**
> Last updated during Phase 21 (Code Quality Pack).

## What's done

- ✅ TypeScript 5.9 + `@types/react@18` + `@types/react-dom@18` + `@types/node` installed
- ✅ `frontend/tsconfig.json` configured (`allowJs: true`, `strict: false` for progressive migration, `paths` alias `@/*` → `src/*`)
- ✅ Old `jsconfig.json` removed (CRA cannot have both)
- ✅ Shared types defined in `src/types/index.ts`:
  - `VaultState`, `VaultStage`, `VaultEvent`, `DexMode`
  - `AccessSession`
  - `BotConfig`, `BotPostPreview`, `ContentType`, `BotPlatform`
  - `PublicStats`
  - `Lang`
- ✅ Files converted to `.ts` / `.tsx`:
  - `src/lib/utils.ts`
  - `src/lib/logger.ts`
  - `src/lib/links.ts`
  - `src/hooks/use-toast.ts`
  - `src/i18n/I18nProvider.tsx`
  - `src/theme/ThemeProvider.tsx`
- ✅ App compiles cleanly with **0 errors / 0 warnings** in dev mode
- ✅ Coexistence with `.jsx` confirmed — no behavioural regression on landing, classified-vault, admin

## What's left

### Quick wins (low risk, no behaviour change)
- [ ] `src/App.js` → `src/App.tsx`
- [ ] `src/index.js` → `src/index.tsx`
- [ ] `src/components/landing/hero/HeroHeadline.jsx` → `.tsx`
- [ ] `src/components/landing/hero/HeroPoster.jsx` → `.tsx`
- [ ] `src/components/landing/hero/HeroCountdown.jsx` → `.tsx`
- [ ] `src/components/landing/Hero.jsx` → `.tsx`
- [ ] `src/components/landing/Tokenomics.jsx` + `tokenomics/*.jsx` → `.tsx`
- [ ] `src/components/landing/TopNav.jsx` → `.tsx`
- [ ] `src/components/landing/Footer.jsx` → `.tsx`
- [ ] `src/components/landing/LanguageToggle.jsx` → `.tsx`

### Medium (page components)
- [ ] `src/pages/Landing.jsx` → `.tsx`
- [ ] `src/pages/HowToBuy.jsx` → `.tsx`
- [ ] `src/pages/PublicStats.jsx` → `.tsx`
- [ ] `src/pages/Operation.jsx` → `.tsx`

### Large surface (admin pages — split first per Phase 21d follow-up, then convert)
- [ ] `src/pages/Admin.jsx` (1251 lines) — split into smaller `.tsx` modules
- [ ] `src/pages/AdminBots.jsx` (1124 lines) — split into BotsList / BotEditor / JobsPanel `.tsx`
- [ ] `src/pages/AdminVault.jsx` (877 lines) — split into VaultPresetEditor / VaultPlanList / VaultDevTools `.tsx`
- [ ] `src/pages/AdminEmails.jsx` → `.tsx`
- [ ] `src/components/admin/*.jsx` → `.tsx`

### Vault sub-tree
- [ ] `src/components/landing/vault/VaultChassis.jsx` → `.tsx`
- [ ] `src/components/landing/vault/VaultSection.jsx` → `.tsx`
- [ ] `src/components/landing/vault/TerminalPopup.jsx` (537 lines) — split first
- [ ] `src/components/landing/vault/VaultActivityFeed.jsx` → `.tsx`

### Other landing components
- [ ] Manifesto, Mission, FAQ, Whitelist, ProphetChat, PropheciesFeed,
  Roadmap, BrutalTruth, ROISimulator, ActivityHeatmap, TransparencyTimeline → `.tsx`

### Stretch goal — strict mode
Once 90%+ of the codebase is `.tsx`, flip these in `tsconfig.json`:
- [ ] `"strict": true`
- [ ] `"noImplicitAny": true`
- [ ] `"noUnusedLocals": true`
- [ ] `"noUnusedParameters": true`
- [ ] `"strictNullChecks": true`
And resolve any newly surfaced errors.

## How to convert a file safely

1. **Rename** `.jsx` → `.tsx` (or `.js` → `.ts` if no JSX inside).
2. **Add types** for component props using `interface PropsName { ... }` and `function Foo({ ... }: PropsName) { ... }`.
3. **For event handlers** use `React.ChangeEvent<HTMLInputElement>`, `React.MouseEvent`, etc.
4. **For state** use `useState<T>(...)` when the inferred type is wrong.
5. **For refs** use `useRef<HTMLDivElement>(null)` or `useRef<number>()`.
6. **For context** see `I18nProvider.tsx` / `ThemeProvider.tsx` — define an interface for the value, type the context as `interface | null`, and throw in the consumer hook if null.
7. **Run** `yarn build` (or watch `frontend.out.log`) to surface compile errors before committing.

## Why progressive vs. big-bang?

- The app is in a launch window — we cannot afford a regression batch.
- `allowJs: true` lets `.jsx` and `.tsx` co-exist seamlessly.
- Converting the most critical files first (`I18nProvider`, `ThemeProvider`, shared `lib/`, `types/`) gives downstream files the type information they need when they get migrated, so each subsequent migration becomes easier rather than harder.
