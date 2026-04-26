/**
 * adminAuth — small, single-source helper for the admin JWT token.
 *
 * Why sessionStorage instead of localStorage?
 *   - localStorage persists FOREVER and is readable by any script on
 *     the same origin. A successful XSS injection can read it and
 *     pivot from there to admin-grade calls.
 *   - sessionStorage is scoped to the browser tab/session: closing
 *     the tab logs the admin out automatically. This is the security
 *     default recommended by OWASP for short-lived auth tokens that
 *     cannot be moved to httpOnly cookies (our backend currently
 *     accepts JWT in Authorization headers, so cookies aren't an
 *     option without a wider refactor).
 *
 * Migration: this module also reads-and-clears any LEGACY token left
 * in localStorage on first call so existing admins don't get a hard
 * logout the moment we ship this change.
 */

const TOKEN_KEY = "deepotus_admin_token";
const LEGACY_TOKEN_KEY = "deepotus_admin_token";

let migrated = false;

function migrateLegacyToken() {
  if (migrated || typeof window === "undefined") return;
  migrated = true;
  try {
    const legacy = window.localStorage.getItem(LEGACY_TOKEN_KEY);
    if (legacy && !window.sessionStorage.getItem(TOKEN_KEY)) {
      window.sessionStorage.setItem(TOKEN_KEY, legacy);
    }
    // Always strip from localStorage so persisted copies don't linger.
    window.localStorage.removeItem(LEGACY_TOKEN_KEY);
  } catch (_) {
    /* storage blocked — non-fatal */
  }
}

export function getAdminToken() {
  if (typeof window === "undefined") return "";
  migrateLegacyToken();
  try {
    return window.sessionStorage.getItem(TOKEN_KEY) || "";
  } catch (_) {
    return "";
  }
}

export function setAdminToken(token) {
  if (typeof window === "undefined") return;
  try {
    if (token) window.sessionStorage.setItem(TOKEN_KEY, token);
    else window.sessionStorage.removeItem(TOKEN_KEY);
  } catch (_) {
    /* storage blocked — non-fatal */
  }
}

export function clearAdminToken() {
  setAdminToken("");
}

export const ADMIN_TOKEN_KEY = TOKEN_KEY;
