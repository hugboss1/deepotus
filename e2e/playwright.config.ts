/**
 * Playwright config — Sprint 22.5 bootstrap.
 *
 * Kept intentionally minimal: single Chromium project, headless, targets
 * the preview deployment by default (override via PLAYWRIGHT_BASE_URL).
 * We don't wire a dev-server spawner because in this repo the frontend
 * is driven by supervisord.
 */
import { defineConfig, devices } from "@playwright/test";

const BASE_URL =
  process.env.PLAYWRIGHT_BASE_URL ||
  "https://prophet-ai-memecoin.preview.emergentagent.com";

export default defineConfig({
  testDir: "./specs",
  // Tests are short-lived smoke checks; fail fast instead of hanging.
  timeout: 30_000,
  expect: { timeout: 5_000 },
  // One worker by default — the preview deployment is shared and we
  // don't want parallel admin-logins racing each other.
  workers: 1,
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report" }],
  ],
  use: {
    baseURL: BASE_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    // Default viewport large enough to render the multi-column admin UI.
    viewport: { width: 1920, height: 900 },
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
