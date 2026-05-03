# E2E Tests — Playwright Bootstrap (Sprint 22.5)

Minimal end-to-end smoke-test suite for the DEEPOTUS landing & admin surface.
Designed to catch the "app is totally broken" class of regressions after
a merge, **not** to be an exhaustive regression suite.

## Scope (on purpose, kept small)

- `specs/landing.spec.ts` — hero + ROI simulator interactive flow.
- `specs/admin.spec.ts`   — admin unlock + `/admin/bots` Config tab +
  the Sprint 22.3-extracted `<CustomLlmKeysSection />` dialog.

Every assertion targets a stable `data-testid` (see
`/app/design_guidelines.md` §Testability) so copy tweaks don't break the
suite.

## Running locally

```bash
cd /app/e2e
yarn install          # installs @playwright/test
yarn install-browsers # downloads Chromium (first run only)
yarn test             # run headless
yarn test:headed      # visible browser
yarn test:ui          # Playwright UI mode
yarn report           # open the HTML report after a run
```

## Environment overrides

| Env var                | Default                                                         | Description                            |
| ---------------------- | --------------------------------------------------------------- | -------------------------------------- |
| `PLAYWRIGHT_BASE_URL`  | `https://prophet-ai-memecoin.preview.emergentagent.com`         | Target base URL                        |
| `ADMIN_PASSWORD`       | `deepotus2026`                                                  | Demo admin password for the gate       |

Example — run against prod: `PLAYWRIGHT_BASE_URL=https://www.deepotus.xyz yarn test`

## Next steps (not in this bootstrap)

1. Add a seed step that flips the phase env flag (`pre-mint`, `live`,
   `graduated`) so the landing suite can assert the matching hero copy.
2. Cover the Propaganda approval queue once the admin fixtures ship.
3. Wire into CI (GitHub Actions workflow file) once the team picks
   between **Playwright-on-preview** and **Playwright-on-localhost**.
