import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { logger } from "@/lib/logger";

const API = process.env.REACT_APP_BACKEND_URL;
const SESSION_KEY = "deepotus_access_session";
const POLL_MS = 8000;

/**
 * Custom hook encapsulating ALL session / vault state for the classified
 * vault page.
 *
 * Responsibilities:
 *   - Restore (or force-clear) the localStorage session at mount, depending
 *     on whether the visitor arrived via a `?code=` deep-link.
 *   - Pre-fill the digicode input from the URL query.
 *   - Validate the stored token against the backend on mount / on changes.
 *   - Poll the vault state every POLL_MS once authed.
 *   - Expose `verifyCode` and `logout` actions.
 *
 * Returns a flat object so the page itself stays declarative:
 *   { session, codeInput, setCodeInput, verifying, gateError, vault,
 *     verifyCode, logout }
 */
export function useClassifiedSession() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const aliveRef = useRef(true);

  const [session, setSession] = useState(() => {
    // ?code= present (email/QR) → ALWAYS force the gate, even if a stored
    // session exists, so entry through the door stays explicit.
    try {
      if (typeof window !== "undefined") {
        const sp = new URLSearchParams(window.location.search);
        if (sp.get("code")) {
          localStorage.removeItem(SESSION_KEY);
          return null;
        }
      }
      const raw = localStorage.getItem(SESSION_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });
  const [codeInput, setCodeInput] = useState(() =>
    (params.get("code") || "").trim().toUpperCase(),
  );
  const [verifying, setVerifying] = useState(false);
  const [gateError, setGateError] = useState(null);
  const [vault, setVault] = useState(null);

  // ---- Backend session validation ----
  useEffect(() => {
    if (!session?.session_token) return;
    const token = session.session_token;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API}/api/access-card/status`, {
          headers: { "X-Session-Token": token },
        });
        const data = await res.json();
        if (cancelled) return;
        if (!data.ok) {
          localStorage.removeItem(SESSION_KEY);
          setSession(null);
        }
      } catch (e) {
        // Transient network error: keep the existing session, the next
        // poll or a user action will revalidate naturally.
        logger.error("[classified-vault] session status check failed", e);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [session]);

  // ---- Vault polling once authed ----
  useEffect(() => {
    aliveRef.current = true;
    if (!session?.session_token) return undefined;
    const token = session.session_token;

    let timer;
    const tick = async () => {
      try {
        const res = await fetch(`${API}/api/vault/state`, {
          headers: { "X-Session-Token": token },
        });
        if (!res.ok) throw new Error(`status ${res.status}`);
        const data = await res.json();
        if (aliveRef.current) setVault(data);
      } catch (e) {
        logger.error("[classified-vault] vault poll failed", e);
      } finally {
        if (aliveRef.current) timer = setTimeout(tick, POLL_MS);
      }
    };

    tick();
    return () => {
      aliveRef.current = false;
      if (timer) clearTimeout(timer);
    };
  }, [session]);

  // ---- Actions ----
  async function verifyCode() {
    setGateError(null);
    setVerifying(true);
    try {
      const res = await fetch(`${API}/api/access-card/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accreditation_number: codeInput.trim() }),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        throw new Error(
          data.detail || data.message || "Invalid accreditation number",
        );
      }
      localStorage.setItem(SESSION_KEY, JSON.stringify(data));
      setSession(data);
      setVerifying(false);
      // Clear `?code=` so a refresh does not re-trigger the gate.
      if (params.get("code")) {
        navigate("/classified-vault", { replace: true });
      }
    } catch (e) {
      setGateError(String(e?.message || e));
      setVerifying(false);
    }
  }

  function logout() {
    localStorage.removeItem(SESSION_KEY);
    setSession(null);
    setCodeInput("");
    navigate("/classified-vault", { replace: true });
  }

  return {
    session,
    codeInput,
    setCodeInput,
    verifying,
    gateError,
    vault,
    verifyCode,
    logout,
  };
}
