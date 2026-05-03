/**
 * Smoke test — admin flow (Sprint 22.5 bootstrap).
 *
 * Covers the surface that Sprint 22.3 refactored:
 *   1. Admin password gate unlocks with the canonical demo password.
 *   2. /admin/bots Config tab renders the freshly extracted
 *      <CustomLlmKeysSection /> with its 3 provider cards.
 *   3. The "Set key" dialog opens, inputs accept text, Cancel closes it.
 *
 * We **don't** submit a real key here — that would hit the live
 * encryption endpoint. The preview env's vault is purposefully
 * scoped, so a passing smoke test here confirms the React wiring is
 * intact without touching production secrets.
 */
import { expect, test } from "@playwright/test";

const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || "deepotus2026";

test.describe("Admin · Custom LLM keys · smoke", () => {
  test("unlock + render Config tab + open dialog", async ({ page }) => {
    // 1) Gate
    await page.goto("/admin");
    const pw = page.locator('input[type="password"]').first();
    await pw.fill(ADMIN_PASSWORD);

    // Click the first submit-like button (label may be "Unlock" or just
    // a form submit). This stays resilient to copy tweaks.
    const submit = page
      .locator('button[type="submit"], button:has-text("Unlock")')
      .first();
    await submit.click();

    // 2) /admin/bots — Config tab is the default
    await page.goto("/admin/bots");
    const section = page.locator('[data-testid="custom-llm-keys-section"]');
    await section.scrollIntoViewIfNeeded();
    await expect(section).toBeVisible();

    // The 3 provider cards are rendered.
    for (const prov of ["openai", "anthropic", "gemini"] as const) {
      await expect(
        page.locator(`[data-testid="custom-llm-card-${prov}"]`),
      ).toBeVisible();
    }

    // 3) Open the dialog on OpenAI. It must render the key input +
    //    label input + Save button, plus a working Cancel path.
    await page.locator('[data-testid="custom-llm-set-openai"]').click();
    const dialog = page.locator('[data-testid="custom-llm-dialog"]');
    await expect(dialog).toBeVisible();
    await expect(
      page.locator('[data-testid="custom-llm-key-input"]'),
    ).toBeVisible();
    await expect(
      page.locator('[data-testid="custom-llm-label-input"]'),
    ).toBeVisible();

    // The Save button stays disabled while the key is too short (<8).
    const save = page.locator('[data-testid="custom-llm-submit"]');
    await expect(save).toBeDisabled();
    await page
      .locator('[data-testid="custom-llm-key-input"]')
      .fill("sk-e2e-probe-do-not-submit");
    await expect(save).toBeEnabled();

    // Close without saving.
    await page.getByRole("button", { name: /Cancel/i }).click();
    await expect(dialog).toBeHidden();
  });
});
