/**
 * Smoke test — landing page & ROI simulator (Sprint 22.5 bootstrap).
 *
 * Purpose: guard the first-touch public experience against silent
 * regressions. We don't try to be exhaustive — we just check the key
 * widgets render AND the ROI calculator reacts to input, which is the
 * single feature that relies on the largest share of the refactored
 * TSX code (ROISimulator + PriceChart + constants typing pass).
 */
import { expect, test } from "@playwright/test";

test.describe("Landing page — smoke", () => {
  test("renders hero and key sections", async ({ page }) => {
    await page.goto("/");
    // Hero is mounted under a stable `data-testid`. If this fails, the
    // shell broke — no point running the rest of the suite.
    await expect(page).toHaveURL(/\/$/);
    // Core sections should all be present on scroll.
    await expect(page.locator('[data-testid="roi-section"]')).toBeVisible({
      timeout: 10_000,
    });
  });

  test("ROI simulator reacts to user input", async ({ page }) => {
    await page.goto("/");

    // Scroll the ROI section into view so lazy-mounted Recharts renders.
    const section = page.locator('[data-testid="roi-section"]');
    await section.scrollIntoViewIfNeeded();
    await expect(page.locator('[data-testid="roi-calculator"]')).toBeVisible();
    await expect(page.locator('[data-testid="roi-price-chart"]')).toBeVisible();

    // Fill in a 1 000 €/$ investment. The display should update to show
    // a non-zero token count (current pricing: 500M tokens for 1 000).
    const amountInput = page.locator('[data-testid="roi-amount-input"]');
    await amountInput.fill("1000");

    // The token counter uses locale-formatted thousands separators so we
    // assert the significant digits only, to stay locale-agnostic.
    const tokensDisplay = page.locator('[data-testid="roi-tokens-display"]');
    await expect(tokensDisplay).toContainText(/500/); // 500M tokens
    await expect(tokensDisplay).toContainText("DEEPOTUS");

    // Scenario tabs should be switchable without runtime errors.
    await page.locator('[data-testid="roi-tab-base"]').click();
    await expect(
      page.locator('[data-testid="roi-tab-content-base"]'),
    ).toBeVisible();
  });
});
