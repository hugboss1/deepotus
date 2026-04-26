/**
 * useClassifiedSession — hook encapsulating session + vault state for
 * the Classified Vault page.
 *
 * Migrated from .js → .ts (Sprint 5 TS migration). Behaviour unchanged.
 *
 * Security note: previously stored the session token in localStorage —
 * the code below sticks with that for now to keep behaviour identical,
 * but a follow-up should move this to sessionStorage (same rationale
 * as `lib/adminAuth.ts`). Tracked in TODO_TYPESCRIPT.md.
 */
import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { logger } from "@/lib/logger";

const API = process.env.REACT_APP_BACKEND_URL;
const SESSION_KEY = "deepotus_access_session";
const POLL_MS = 8000;

export interface ClassifiedSession {
  ok: boolean;
  session_token: string;
  accreditation_number?: string;
  display_name?: string;
  expires_at?: string;
}

export interface VaultState {
  stage?: string;
  tokens_sold?: number;
  tokens_per_micro?: number;
  // server returns more fields — kept loose so the hook is forward-compatible
  [key: string]: unknown;
}

export interface ClassifiedSessionApi {
  session: ClassifiedSession | null;
  codeInput: string;
  setCodeInput: (s: string) => void;
  verifying: boolean;
  gateError: string | null;
  vault: VaultState | null;
  verifyCode: () => Promise<void>;
  logout: () => void;
}

function loadStoredSession(): ClassifiedSession | null {
  try {
    if (typeof window !== "undefined") {
      // ?code= present (email/QR) → ALWAYS force the gate, even if a stored
      // session exists, so entry through the door stays explicit.
      const sp = new URLSearchParams(window.location.search);
      if (sp.get("code")) {
        localStorage.removeItem(SESSION_KEY);
        return null;
      }
    }
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? (JSON.parse(raw) as ClassifiedSession) : null;
  } catch {
    return null;
  }
}

export function useClassifiedSession(): ClassifiedSessionApi {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const aliveRef = useRef(true);

  const [session, setSession] = useState<ClassifiedSession | null>(() =>
    loadStoredSession(),
  );
  const [codeInput, setCodeInput] = useState<string>(() =>
    (params.get("code") || "").trim().toUpperCase(),
  );
  const [verifying, setVerifying] = useState(false);
  const [gateError, setGateError] = useState<string | null>(null);
  const [vault, setVault] = useState<VaultState | null>(null);

  // ---- Backend session validation ----
  useEffect(() => {
    if (!session?.session_token) return undefined;
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

    let timer: ReturnType<typeof setTimeout> | undefined;
    const tick = async () => {
      try {
        const res = await fetch(`${API}/api/vault/state`, {
          headers: { "X-Session-Token": token },
        });
        if (!res.ok) throw new Error(`status ${res.status}`);
        const data = (await res.json()) as VaultState;
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
  async function verifyCode(): Promise<void> {
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
      setSession(data as ClassifiedSession);
      setVerifying(false);
      // Clear `?code=` so a refresh does not re-trigger the gate.
      if (params.get("code")) {
        navigate("/classified-vault", { replace: true });
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setGateError(msg || "verification failed");
      setVerifying(false);
    }
  }

  function logout(): void {
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
