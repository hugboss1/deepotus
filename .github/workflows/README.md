# GitHub Actions Workflows — DEEPOTUS

## `e2e-smoke.yml` (Sprint 24)

Playwright Chromium smoke suite. Runs the 3 specs under `/app/e2e/specs/`
against any deployed environment.

### Triggers

| Trigger              | Description                                                                   |
| -------------------- | ----------------------------------------------------------------------------- |
| `workflow_dispatch`  | Manual button on the Actions tab. Optional `base_url` input overrides env.   |
| `pull_request`       | PRs that touch `frontend/**`, `e2e/**`, or this workflow file.                |
| `schedule`           | Nightly at 03:00 UTC (preview deploy probe).                                  |

### Required repo secrets

Set under **Settings → Secrets and variables → Actions → Repository secrets**:

| Secret name                     | Default if unset                                                | Purpose                                       |
| ------------------------------- | --------------------------------------------------------------- | --------------------------------------------- |
| `PLAYWRIGHT_BASE_URL_PREVIEW`   | `https://prophet-ai-memecoin.preview.emergentagent.com`         | Target URL for nightly + PR runs              |
| `ADMIN_PASSWORD`                | `deepotus2026`                                                  | Used by `admin.spec.ts` to unlock the gate    |

> **Security**: The fallback values exist purely so the workflow stays
> useful before secrets are configured. **Set the real `ADMIN_PASSWORD`
> secret immediately** — the default is the demo password used in this
> public-preview environment only.

### Manual runs

Go to **Actions → e2e-smoke → Run workflow**. The optional `base_url`
input lets you target prod, a feature branch deploy, or a local tunnel
without committing changes.

```text
base_url: https://www.deepotus.xyz
```

### Reading failures

When a job fails, two artifacts are uploaded for 7 days:

- `playwright-report-{run_id}` — full HTML report (open `index.html`).
- `playwright-traces-{run_id}` — per-test traces + screenshots + video.

Drag the `.zip` into <https://trace.playwright.dev/> for the trace
viewer.

### Local repro

```bash
cd /app/e2e
PLAYWRIGHT_BASE_URL=https://www.deepotus.xyz \
  ADMIN_PASSWORD=changeme \
  yarn test --headed
```
