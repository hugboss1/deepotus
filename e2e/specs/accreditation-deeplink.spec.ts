/**
 * Smoke test — `#accreditation` deep-link choreography.
 *
 * Guarantees the recruitment flow stays wired end-to-end:
 *   1. Visiting `/#accreditation` directly auto-opens the TerminalPopup
 *      (DS-GATE-02) once the DeepState intro fades.
 *   2. Triggering a `hashchange` mid-session (e.g. clicking an in-page
 *      `#accreditation` link) re-opens the popup synchronously and
 *      flips the CTA pulse flag on the request-clearance wrapper.
 *   3. The legacy Whitelist mailing-list section no longer carries the
 *      `accreditation` anchor (regression guard for the Sprint UX
 *      rewire that moved the anchor from Whitelist → VaultSection).
 *
 * The DeepState boot intro covers the vault for ~6-8s on first paint.
 * The component handles this by waiting on `IntersectionObserver`, so
 * we give the test up to 14s for the popup to surface.
 */
import { expect, test } from "@playwright/test";

const POPUP = '[data-testid="terminal-popup"]';
const ANCHOR = '[data-testid="accreditation-anchor"]';
const REQUEST_CTA_WRAPPER = '[data-cta-pulse]';

test.describe("Accreditation deep-link — smoke", () => {
  test("/#accreditation auto-opens the TerminalPopup gate", async ({ page }) => {
    await page.goto("/#accreditation");

    // Anchor must be present in the vault section (not Whitelist).
    await expect(page.locator(ANCHOR)).toHaveCount(1);

    // The popup is gated behind the IntersectionObserver — give it room
    // to wait for the DeepState intro to disposes (≤ 9s hard fallback +
    // a comfortable buffer).
    await expect(page.locator(POPUP)).toBeVisible({ timeout: 14_000 });

    // The popup must be the DS-GATE-02 terminal (header copy is stable
    // across FR/EN locales — protocol name is universal).
    await expect(page.locator(POPUP)).toContainText("PROTOCOL ΔΣ");
  });

  test("hashchange mid-session re-opens the popup and pulses the CTA", async ({
    page,
  }) => {
    // Land on the bare landing page first; wait for the intro to clear.
    await page.goto("/");
    // Ensure the vault section is mounted before we mutate the hash.
    await page.locator('[data-testid="vault-section"]').scrollIntoViewIfNeeded();
    await expect(page.locator(ANCHOR)).toHaveCount(1);

    // Now simulate an in-page anchor click via direct hash mutation —
    // this is exactly what `<a href="#accreditation">` triggers.
    await page.evaluate(() => {
      window.location.hash = "#accreditation";
    });

    // Popup should surface within the post-intro fast path (drain is
    // synchronous after the rAF + 350ms gate-open delay).
    await expect(page.locator(POPUP)).toBeVisible({ timeout: 5_000 });

    // CTA wrapper must briefly carry the `data-cta-pulse="true"` flag.
    // We poll because the pulse auto-clears after 2.6s.
    const pulse = page.locator(REQUEST_CTA_WRAPPER).first();
    await expect(pulse).toHaveAttribute("data-cta-pulse", "true", {
      timeout: 4_000,
    });
  });

  test("Whitelist section no longer owns the accreditation anchor", async ({
    page,
  }) => {
    await page.goto("/");
    // Whitelist section should still render (mailing-list opt-in is
    // independent of the accreditation flow).
    await expect(page.locator('[data-testid="whitelist-section"]')).toBeAttached();

    // But the anchor must NOT live inside it anymore — the only
    // `#accreditation` element should sit inside the vault section.
    const anchorsInWhitelist = page.locator(
      '[data-testid="whitelist-section"] [data-testid="accreditation-anchor"]',
    );
    await expect(anchorsInWhitelist).toHaveCount(0);

    const anchorsInVault = page.locator(
      '[data-testid="vault-section"] [data-testid="accreditation-anchor"]',
    );
    await expect(anchorsInVault).toHaveCount(1);
  });
});
