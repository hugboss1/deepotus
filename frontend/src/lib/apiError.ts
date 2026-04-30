/**
 * apiError.ts — Robust extractor for HTTP error messages.
 *
 * Why this exists
 * ---------------
 * FastAPI returns errors in three shapes that all hit ``response.data.detail``:
 *
 *   1. ``"Resource not found"``                       — bare string
 *   2. ``{ code: "FOO", message: "Human readable" }`` — structured object
 *   3. ``[{loc, msg, type}, ...]``                    — Pydantic validation
 *
 * Our toasts used to do ``typeof detail === "string" ? detail : "Something failed"``
 * which silently dropped the message in cases (2) and (3). That's how the
 * Cabinet Vault "Save failed" bug surfaced — the backend was actually
 * returning ``{code: "TWOFA_REQUIRED", message: "Enable 2FA…"}`` and the
 * UI threw it away.
 *
 * Usage
 * -----
 *     try { … } catch (err) {
 *       toast.error(extractErrorMsg(err, "Failed to save secret"));
 *     }
 *
 * Returns
 * -------
 * The most specific human-readable string we can recover from the error,
 * falling back to the supplied default.
 */

export interface StructuredApiError {
  code?: string;
  message?: string;
  hint?: string;
}

/**
 * Best-effort extraction. Never throws — always returns a string.
 *
 * Priority order:
 *   1. ``error.response.data.detail.message``   (structured)
 *   2. ``error.response.data.detail``           (string)
 *   3. ``error.response.data.message``          (some endpoints flatten)
 *   4. ``error.message``                        (axios network errors)
 *   5. ``fallback``                             (last resort)
 *
 * If a structured object also carries a ``code``, we prefix it as
 * ``[CODE] message`` so logs make the failure class obvious. We DO NOT
 * include the code if a ``hint`` is present — hints are user-facing and
 * shouldn't read like an enum dump.
 */
export function extractErrorMsg(err: unknown, fallback: string): string {
  // eslint-disable-next-line
  const e = err as any;
  const detail = e?.response?.data?.detail;

  // (1) Pydantic validation array — pull the first message.
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (typeof first === "object" && first?.msg) {
      return String(first.msg);
    }
  }

  // (2) Structured object {code, message, hint}.
  if (detail && typeof detail === "object") {
    const struct = detail as StructuredApiError;
    if (struct.message) {
      if (struct.code && !struct.hint) {
        return `[${struct.code}] ${struct.message}`;
      }
      return struct.hint
        ? `${struct.message} ${struct.hint}`
        : struct.message;
    }
    if (struct.code) {
      return String(struct.code);
    }
  }

  // (3) Bare string.
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  // (4) Some endpoints flatten to data.message
  const flatMsg = e?.response?.data?.message;
  if (typeof flatMsg === "string" && flatMsg.trim()) {
    return flatMsg;
  }

  // (5) Axios network/connection error.
  if (typeof e?.message === "string" && e.message.trim()) {
    return e.message;
  }

  return fallback;
}

/**
 * Inspect an error for a specific structured ``code`` field. Useful when
 * the UI needs to branch on the error type (e.g. redirect to /admin/security
 * when ``TWOFA_REQUIRED`` is detected) without parsing strings.
 */
export function getErrorCode(err: unknown): string | null {
  // eslint-disable-next-line
  const e = err as any;
  const detail = e?.response?.data?.detail;
  if (detail && typeof detail === "object" && typeof detail.code === "string") {
    return detail.code;
  }
  return null;
}
