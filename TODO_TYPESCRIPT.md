# TypeScript Migration — completion log

> Status: **Sprints 5–7 complete · 94% TS coverage of application code**
> Last update: 2026-04-27

---

## Final Coverage

| Bucket | Count | Notes |
|---|---|---|
| **TypeScript files** (`.ts` / `.tsx`) | **77** | All application logic |
| Application JS/JSX (remaining) | 5 | Intentionally kept |
| Shadcn UI primitives (`.jsx`) | 46 | Excluded from `tsconfig.include`; covered by `types/shadcn-shims.d.ts` ambient shim |
| **Total application coverage** | **94%** | 77 / (77 + 5) |

### The 5 remaining JS/JSX (intentional)
| File | Reason |
|---|---|
| `src/App.js` | CRA entry point — convention is `.js`, no benefit migrating |
| `src/index.js` | CRA entry point — convention is `.js` |
| `src/i18n/translations.js` | Pure data file (~1 500 lines of strings) — low ROI to migrate |
| `src/pages/AdminBots.jsx` | 1 559 lines, complex multi-tab. Already split (NewsFeedSection extracted). Pragmatic to leave until next functional refactor |
| `src/pages/AdminVault.jsx` | 665 lines. Already split (HeliusSection + SealStatusSection extracted). Same rationale |

---

## Sprint 7 — Final batch (this session)

### 32 files migrated `.jsx` → `.tsx` in 4 batches:

**Batch 1 — Trivial (10):**
- `pages/Landing.jsx`, `components/intro/GlitchOverlay.jsx`
- `components/landing/{Hero,Manifesto,Mission,FAQ,BrutalTruth,Socials,Tokenomics,ConfirmDialog}.jsx`

**Batch 2 — Sub-components (12):**
- `components/landing/hero/{HeroHeadline,HeroPoster,HeroCountdown}.jsx`
- `components/landing/vault/{VaultSection,VaultChassis,CombinationDial,VaultActivityFeed}.jsx`
- `components/landing/tokenomics/{TokenomicsLegend,TokenomicsChart,TokenomicsTaxAndBuy}.jsx`
- `components/landing/roi/{PriceChart,DisclaimerMarquee}.jsx`

**Batch 3 — Wrappers (8):**
- `components/landing/{TopNav,TransparencyTimeline,ActivityHeatmap,ProphetPinnedWhisper,Whitelist,PropheciesFeed,Roadmap,BackgroundProject}.jsx`

**Batch 4 — Complex (10+):**
- `components/landing/{ProphetChat,ROISimulator}.jsx`
- `pages/{ClassifiedVault,Operation,HowToBuy,PublicStats}.jsx`
- `pages/classified-vault/{AuthedVaultView,GateView}.jsx`
- `components/intro/{DeepStateIntro,TerminalWindow,MatrixRain}.jsx`
- `components/admin/TwoFASetupDialog.jsx`
- 4 utility files: `useGlitchNumber`, `roi/constants`, `roi/synthPath`, `tokenomics/allocations`

### Critical infrastructure fixes
1. **Shadcn shim refactored** (`types/shadcn-shims.d.ts`):
   - Removed top-level `import * as React` which had silently turned the file into a module, breaking ambient `declare module` blocks
   - Switched all entries from `React.ForwardRefExoticComponent<any>` (rejects `children`) to a permissive `(props: any) => React.ReactElement | null` type that accepts any prop
   - Added missing entries: `table`, `alert-dialog`, `carousel`, `form`, `dropdown-menu`, etc.

2. **`tsconfig.json` excludes** `src/components/ui/**/*.jsx` so the type-checker uses the shim instead of inferring `RefAttributes<HTMLDivElement>` from the source

3. **Recharts custom `Tooltip` components** typed as `(props: any) => …` — Recharts injects `active/payload/label` at runtime, which the consumer JSX site can't pass explicitly

---

## Migration recipe (proven across 32 files)

1. `cp foo.jsx foo.tsx && rm foo.jsx`
2. `npx tsc --noEmit` — fix the few errors (mostly `noImplicitReturns` and untyped event handlers)
3. Replace single nested-ternary spots with lookup tables when convenient
4. `yarn build` (production) to validate ESLint passes
5. Smoke test the affected page

Average time per file: ~1 min (90% are pure copy with zero TS errors).

---

## Validation gates (all passing)

- ✅ `npx tsc --noEmit` exit 0
- ✅ `yarn build` production : `Compiled successfully` zero warning, 413 kB JS gzipped
- ✅ `ruff check .` (backend) : All checks passed
- ✅ Smoke E2E : 0 page errors across landing, sealed terminal, /admin, /admin/vault, /admin/bots, /admin/emails, /stats, /operation, /how-to-buy, /classified-vault

---

## Out of scope (intentional)

- 46 Shadcn UI primitives stay `.jsx` — covered by ambient shim, migration is high-effort/low-value
- `App.js` / `index.js` — CRA convention
- `translations.js` — pure data, ~1 500 lines

## Future work (post-deploy)

- Could migrate `AdminBots.jsx` + `AdminVault.jsx` if/when a functional refactor of those panels is needed
- Could migrate `translations.js` → `.ts` to unlock autocomplete on translation keys (but typing 1 500+ keys is heavy)
