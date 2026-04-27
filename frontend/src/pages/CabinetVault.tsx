/**
 * /admin/cabinet-vault — DEEPOTUS Cabinet Vault
 *
 * Single source-of-truth admin page for managing every site secret behind a
 * BIP39 seed phrase + 2FA. Three phases drive the UI:
 *   - "not_initialised" → Setup wizard (generates 24-word mnemonic).
 *   - "locked"          → Unlock prompt (paste mnemonic).
 *   - "unlocked"        → Categorised secrets browser + audit + export.
 *
 * Security UX:
 *   - 2FA enforcement guard (backend returns 403 TWOFA_REQUIRED).
 *   - Live countdown to auto-lock (15 min default).
 *   - Reveal-on-demand (single-shot, audit-logged server-side).
 *   - Mnemonic shown ONCE at setup; copy button + force-confirm 3 words.
 *   - All sensitive inputs use type=password until explicit reveal.
 */
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Lock,
  Unlock,
  ShieldAlert,
  KeyRound,
  Copy,
  RefreshCcw,
  Eye,
  EyeOff,
  Download,
  History,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Trash2,
  Plus,
} from "lucide-react";
import { getAdminToken, clearAdminToken } from "@/lib/adminAuth";
import { logger } from "@/lib/logger";
import ThemeToggle from "@/components/landing/ThemeToggle";

const API = process.env.REACT_APP_BACKEND_URL;

// -------------------------------------------------------------------------
// Types
// -------------------------------------------------------------------------
interface VaultStatus {
  initialised: boolean;
  locked: boolean;
  unlocked_at: string | null;
  expires_in_seconds: number | null;
  vault_created_at: string | null;
  secret_count: number;
}

interface SecretMeta {
  key: string;
  updated_at: string | null;
  rotation_count: number;
  value_length: number;
  value_fingerprint: string | null;
  _unset?: boolean;
}

interface ListResponse {
  categories: Record<string, SecretMeta[]>;
  schema: Record<string, string[]>;
}

interface AuditEntry {
  _id: string;
  action: string;
  at: string;
  jti?: string;
  ip?: string | null;
  category?: string | null;
  key?: string | null;
  // eslint-disable-next-line
  extra?: any;
}

const CATEGORY_LABELS: Record<string, { label: string; color: string }> = {
  auth: { label: "Authentication", color: "text-[#FF4D4D]" },
  llm_emergent: { label: "LLM · Emergent", color: "text-[#22D3EE]" },
  llm_custom: { label: "LLM · Custom providers", color: "text-[#22D3EE]" },
  email_resend: { label: "Email · Resend", color: "text-[#F59E0B]" },
  solana_helius: { label: "Solana · Helius", color: "text-[#A855F7]" },
  telegram: { label: "Telegram bot", color: "text-[#22D3EE]" },
  x_twitter: { label: "X / Twitter bot", color: "text-foreground" },
  trading_refs: { label: "Trading bot referrals", color: "text-[#18C964]" },
  site: { label: "Site · URLs", color: "text-foreground" },
  database: { label: "Database", color: "text-[#F59E0B]" },
};

// -------------------------------------------------------------------------
// Page
// -------------------------------------------------------------------------
export default function CabinetVault() {
  const navigate = useNavigate();
  const [token, setToken] = useState<string>(() => getAdminToken() || "");
  const [status, setStatus] = useState<VaultStatus | null>(null);
  const [twofaRequired, setTwofaRequired] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  const headers = useMemo(
    () => (token ? { Authorization: `Bearer ${token}` } : {}),
    [token],
  );

  useEffect(() => {
    document.title = "DEEPOTUS · Cabinet Vault";
  }, []);

  const refreshStatus = useCallback(async () => {
    if (!token) return;
    try {
      const { data } = await axios.get<VaultStatus>(
        `${API}/api/admin/cabinet-vault/status`,
        { headers },
      );
      setStatus(data);
      setTwofaRequired(false);
    } catch (err: unknown) {
      // eslint-disable-next-line
      const e = err as any;
      const detail = e?.response?.data?.detail;
      if (e?.response?.status === 403 && detail?.code === "TWOFA_REQUIRED") {
        setTwofaRequired(true);
      } else if (e?.response?.status === 401) {
        clearAdminToken();
        setToken("");
        navigate("/admin");
      } else {
        logger.error(err);
      }
    } finally {
      setLoading(false);
    }
  }, [token, headers, navigate]);

  useEffect(() => {
    if (!token) {
      navigate("/admin");
      return;
    }
    refreshStatus();
  }, [token, navigate, refreshStatus]);

  // ===== Render gates =====
  if (!token) return null;

  if (loading) {
    return (
      <ShellFrame>
        <div className="text-muted-foreground font-mono text-sm">Loading…</div>
      </ShellFrame>
    );
  }

  if (twofaRequired) {
    return (
      <ShellFrame>
        <div
          className="rounded-xl border border-[#F59E0B]/40 bg-[#F59E0B]/5 p-6"
          data-testid="cabinet-2fa-required"
        >
          <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.25em] text-[#F59E0B]">
            <ShieldAlert size={14} /> ACCESS DENIED · 2FA REQUIRED
          </div>
          <h2 className="mt-2 font-display text-2xl font-semibold">
            Cabinet Vault is locked behind 2FA.
          </h2>
          <p className="mt-2 text-sm text-foreground/80 max-w-prose">
            The Cabinet Vault holds every secret used by the site (LLM keys,
            Resend, Helius, Telegram, X, trading bot refs, site URLs…). To
            keep the blast radius minimal we refuse to unlock it without a
            second factor. Enable 2FA from the <strong>Security</strong> tab,
            then return here.
          </p>
          <Button
            asChild
            variant="outline"
            className="mt-4 rounded-[var(--btn-radius)]"
            data-testid="cabinet-2fa-cta-back-to-security"
          >
            <Link to="/admin">
              <ArrowLeft size={14} className="mr-1" /> Back to Security tab
            </Link>
          </Button>
        </div>
      </ShellFrame>
    );
  }

  if (!status) return null;

  if (!status.initialised) {
    return (
      <ShellFrame>
        <SetupWizard
          headers={headers as { Authorization: string }}
          onDone={refreshStatus}
        />
      </ShellFrame>
    );
  }

  if (status.locked) {
    return (
      <ShellFrame>
        <UnlockForm
          headers={headers as { Authorization: string }}
          onUnlocked={refreshStatus}
        />
      </ShellFrame>
    );
  }

  return (
    <ShellFrame>
      <UnlockedPanel
        status={status}
        headers={headers as { Authorization: string }}
        onLocked={refreshStatus}
      />
    </ShellFrame>
  );
}

// -------------------------------------------------------------------------
// Shell (top nav + container)
// -------------------------------------------------------------------------
const ShellFrame: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="min-h-screen bg-background text-foreground">
    <header className="sticky top-0 z-30 bg-background/80 backdrop-blur-md border-b border-border">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            to="/"
            className="font-display font-semibold tracking-tight text-base md:text-lg"
            data-testid="cabinet-logo"
          >
            $DEEPOTUS
          </Link>
          <span className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
            / cabinet-vault
          </span>
          <Badge
            variant="outline"
            className="font-mono text-[10px] uppercase tracking-widest border-[#F59E0B]/50 text-[#F59E0B]"
          >
            classified
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button
            asChild
            variant="outline"
            size="sm"
            className="rounded-[var(--btn-radius)]"
            data-testid="cabinet-back-admin"
          >
            <Link to="/admin">
              <ArrowLeft size={14} className="mr-1" /> Admin
            </Link>
          </Button>
          <ThemeToggle />
        </div>
      </div>
    </header>
    <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">{children}</main>
  </div>
);

// -------------------------------------------------------------------------
// Phase 1 — Setup wizard
// -------------------------------------------------------------------------
interface SetupProps {
  headers: { Authorization: string };
  onDone: () => void;
}

const SetupWizard: React.FC<SetupProps> = ({ headers, onDone }) => {
  const [step, setStep] = useState<"intro" | "show" | "verify">("intro");
  const [busy, setBusy] = useState<boolean>(false);
  const [phrase, setPhrase] = useState<string>("");
  const [revealed, setRevealed] = useState<boolean>(false);
  const words = useMemo(
    () => (phrase ? phrase.split(/\s+/).filter(Boolean) : []),
    [phrase],
  );

  // verification quiz: 3 random word indices
  const [quizIdx] = useState<number[]>(() => {
    const arr: number[] = [];
    while (arr.length < 3) {
      const r = Math.floor(Math.random() * 24);
      if (!arr.includes(r)) arr.push(r);
    }
    return arr.sort((a, b) => a - b);
  });
  const [quizAnswers, setQuizAnswers] = useState<string[]>(["", "", ""]);

  const generate = async () => {
    setBusy(true);
    try {
      const { data } = await axios.post(
        `${API}/api/admin/cabinet-vault/init`,
        {},
        { headers },
      );
      setPhrase(data.mnemonic);
      setStep("show");
    } catch (err: unknown) {
      // eslint-disable-next-line
      const detail = (err as any)?.response?.data?.detail;
      toast.error(
        typeof detail === "string" ? detail : "Vault init failed.",
      );
      logger.error(err);
    } finally {
      setBusy(false);
    }
  };

  const copyPhrase = async () => {
    try {
      await navigator.clipboard.writeText(phrase);
      toast.success("24 words copied. Paste into your offline backup NOW.");
    } catch {
      toast.error("Clipboard unavailable — write the words by hand.");
    }
  };

  const verifySubmit = () => {
    const ok = quizIdx.every((idx, i) =>
      quizAnswers[i].trim().toLowerCase() === words[idx],
    );
    if (!ok) {
      toast.error("One or more words don't match — re-check your backup.");
      return;
    }
    toast.success(
      "Mnemonic confirmed. Vault sealed. Press Continue to unlock and start storing secrets.",
    );
    onDone();
  };

  if (step === "intro") {
    return (
      <div
        className="rounded-xl border border-border bg-card p-6"
        data-testid="cabinet-setup-intro"
      >
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.25em] text-[#F59E0B]">
          <Lock size={14} /> CABINET VAULT · SETUP REQUIRED
        </div>
        <h1 className="mt-2 font-display text-2xl md:text-3xl font-semibold">
          Generate your master seed phrase.
        </h1>
        <p className="mt-3 text-sm text-foreground/80 max-w-prose leading-relaxed">
          The Cabinet Vault is a tamper-resistant safe for every secret your
          site needs to run: LLM keys, Resend, Helius, Telegram &amp; X bots,
          trading bot referrals, site URLs, and more. Access requires a{" "}
          <strong>24-word BIP39 mnemonic</strong> generated below.
        </p>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-[11px]">
          <div className="rounded-md border border-border bg-background/40 p-3">
            <div className="text-[#18C964] mb-1">✓ HOW IT WORKS</div>
            <div className="text-foreground/80 leading-relaxed">
              We derive a 256-bit AES-GCM key from your phrase via PBKDF2-SHA512
              (300 000 iterations). Secrets are stored encrypted in MongoDB.
            </div>
          </div>
          <div className="rounded-md border border-border bg-background/40 p-3">
            <div className="text-[#18C964] mb-1">✓ WHAT WE STORE</div>
            <div className="text-foreground/80 leading-relaxed">
              Encrypted ciphertext only. Your mnemonic is shown ONCE and{" "}
              <strong>never persisted server-side</strong>.
            </div>
          </div>
          <div className="rounded-md border border-[#FF4D4D]/40 bg-[#FF4D4D]/5 p-3">
            <div className="text-[#FF4D4D] mb-1">⚠ NO RECOVERY</div>
            <div className="text-foreground/80 leading-relaxed">
              Lose the phrase = lose every secret. Store it offline, on paper or
              hardware password manager. Two copies in two locations.
            </div>
          </div>
        </div>

        <div className="mt-6 flex items-center gap-3">
          <Button
            onClick={generate}
            disabled={busy}
            className="rounded-[var(--btn-radius)] btn-press"
            data-testid="cabinet-setup-generate"
          >
            {busy ? "…" : "Generate 24 words"} →
          </Button>
          <Button
            asChild
            variant="outline"
            className="rounded-[var(--btn-radius)]"
            data-testid="cabinet-setup-cancel"
          >
            <Link to="/admin">
              <ArrowLeft size={14} className="mr-1" /> Cancel
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  if (step === "show") {
    return (
      <div
        className="rounded-xl border border-[#F59E0B]/40 bg-card p-6"
        data-testid="cabinet-setup-show"
      >
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.25em] text-[#F59E0B]">
          <KeyRound size={14} /> SHOWN ONCE · WRITE THIS DOWN NOW
        </div>
        <h2 className="mt-2 font-display text-2xl font-semibold">
          Your 24-word recovery phrase.
        </h2>
        <p className="mt-2 text-sm text-foreground/80">
          Reveal, write/copy, then store offline. The Cabinet will quiz you
          on 3 random words before sealing the vault.
        </p>
        <div
          className="mt-4 rounded-md border border-border bg-background/60 p-4 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2"
          data-testid="cabinet-setup-words"
        >
          {words.map((w, i) => (
            <div
              key={`${i}-${w}`}
              className="flex items-center gap-2 px-2 py-1 rounded font-mono text-sm bg-background border border-border"
            >
              <span className="text-muted-foreground tabular text-[10px]">
                {String(i + 1).padStart(2, "0")}.
              </span>
              <span className={revealed ? "text-foreground" : "text-transparent select-none"}>
                {revealed ? w : "•••••••"}
              </span>
            </div>
          ))}
        </div>
        <div className="mt-3 flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setRevealed((v) => !v)}
            className="rounded-[var(--btn-radius)]"
            data-testid="cabinet-setup-reveal-toggle"
          >
            {revealed ? (
              <>
                <EyeOff size={14} className="mr-1" /> Hide
              </>
            ) : (
              <>
                <Eye size={14} className="mr-1" /> Reveal
              </>
            )}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={copyPhrase}
            disabled={!revealed}
            className="rounded-[var(--btn-radius)]"
            data-testid="cabinet-setup-copy"
          >
            <Copy size={14} className="mr-1" /> Copy
          </Button>
          <div className="ml-auto font-mono text-[10px] text-muted-foreground">
            BIP39 · 256 bits entropy · SHA-512 KDF
          </div>
        </div>
        <div className="mt-6 flex items-center gap-3">
          <Button
            onClick={() => setStep("verify")}
            disabled={!revealed}
            className="rounded-[var(--btn-radius)] btn-press"
            data-testid="cabinet-setup-continue-to-verify"
          >
            I wrote it down — verify →
          </Button>
        </div>
      </div>
    );
  }

  // step === "verify"
  return (
    <div
      className="rounded-xl border border-border bg-card p-6"
      data-testid="cabinet-setup-verify"
    >
      <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.25em] text-[#18C964]">
        <CheckCircle2 size={14} /> VERIFY YOUR BACKUP
      </div>
      <h2 className="mt-2 font-display text-2xl font-semibold">
        Type 3 words from your phrase.
      </h2>
      <p className="mt-2 text-sm text-foreground/80 max-w-prose">
        Pure security check — proves you wrote them down. The phrase is no
        longer visible. If you're stuck, you can{" "}
        <button
          type="button"
          onClick={() => setStep("show")}
          className="underline text-[#F59E0B]"
        >
          go back and re-reveal
        </button>{" "}
        before continuing.
      </p>
      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        {quizIdx.map((idx, i) => (
          <div key={idx}>
            <Label className="text-xs text-muted-foreground uppercase tracking-widest">
              Word #{idx + 1}
            </Label>
            <Input
              type="text"
              value={quizAnswers[i]}
              onChange={(e) => {
                const next = [...quizAnswers];
                next[i] = e.target.value;
                setQuizAnswers(next);
              }}
              autoComplete="off"
              spellCheck={false}
              className="mt-1 font-mono"
              data-testid={`cabinet-setup-verify-input-${i}`}
            />
          </div>
        ))}
      </div>
      <div className="mt-6 flex items-center gap-3">
        <Button
          onClick={verifySubmit}
          className="rounded-[var(--btn-radius)] btn-press"
          data-testid="cabinet-setup-verify-submit"
        >
          Seal the vault →
        </Button>
        <Button
          variant="outline"
          onClick={() => setStep("show")}
          className="rounded-[var(--btn-radius)]"
        >
          <ArrowLeft size={14} className="mr-1" /> Back
        </Button>
      </div>
    </div>
  );
};

// -------------------------------------------------------------------------
// Phase 2 — Unlock form
// -------------------------------------------------------------------------
const UnlockForm: React.FC<{
  headers: { Authorization: string };
  onUnlocked: () => void;
}> = ({ headers, onUnlocked }) => {
  const [phrase, setPhrase] = useState<string>("");
  const [busy, setBusy] = useState<boolean>(false);

  const wordCount = phrase.trim().split(/\s+/).filter(Boolean).length;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (busy) return;
    if (wordCount !== 24) {
      toast.error(`Mnemonic must be exactly 24 words (got ${wordCount}).`);
      return;
    }
    setBusy(true);
    try {
      await axios.post(
        `${API}/api/admin/cabinet-vault/unlock`,
        { mnemonic: phrase.trim() },
        { headers },
      );
      toast.success("Vault unlocked. Auto-lock in 15 minutes.");
      setPhrase("");
      onUnlocked();
    } catch (err: unknown) {
      // eslint-disable-next-line
      const detail = (err as any)?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Unlock failed.");
      logger.error(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form
      onSubmit={submit}
      className="rounded-xl border border-border bg-card p-6"
      data-testid="cabinet-unlock-form"
    >
      <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.25em] text-[#F59E0B]">
        <Lock size={14} /> CABINET VAULT · LOCKED
      </div>
      <h1 className="mt-2 font-display text-2xl md:text-3xl font-semibold">
        Type your 24-word phrase to unlock.
      </h1>
      <p className="mt-2 text-sm text-foreground/80 max-w-prose">
        The phrase derives the master encryption key in-memory. Auto-locks after
        15 minutes of inactivity. Wrong guesses are audit-logged.
      </p>
      <div className="mt-5">
        <Label className="text-xs text-muted-foreground uppercase tracking-widest">
          Mnemonic phrase ({wordCount} / 24 words)
        </Label>
        <textarea
          value={phrase}
          onChange={(e) => setPhrase(e.target.value)}
          rows={4}
          spellCheck={false}
          autoComplete="off"
          className="w-full mt-1 rounded-md border border-border bg-background px-3 py-2 font-mono text-sm text-foreground/90 leading-relaxed focus:outline-none focus:ring-2 focus:ring-[#F59E0B]/40"
          placeholder="word1 word2 word3 ... word24"
          data-testid="cabinet-unlock-input"
          disabled={busy}
        />
      </div>
      <div className="mt-4 flex items-center gap-3">
        <Button
          type="submit"
          disabled={busy || wordCount !== 24}
          className="rounded-[var(--btn-radius)] btn-press"
          data-testid="cabinet-unlock-submit"
        >
          {busy ? "…" : "Unlock vault"} →
        </Button>
        <Button
          asChild
          variant="outline"
          className="rounded-[var(--btn-radius)]"
        >
          <Link to="/admin">
            <ArrowLeft size={14} className="mr-1" /> Cancel
          </Link>
        </Button>
      </div>
    </form>
  );
};

// -------------------------------------------------------------------------
// Phase 3 — Unlocked panel (browser + audit + export)
// -------------------------------------------------------------------------
interface UnlockedProps {
  status: VaultStatus;
  headers: { Authorization: string };
  onLocked: () => void;
}

const UnlockedPanel: React.FC<UnlockedProps> = ({
  status,
  headers,
  onLocked,
}) => {
  const [list, setList] = useState<ListResponse | null>(null);
  const [audit, setAudit] = useState<AuditEntry[] | null>(null);
  const [editing, setEditing] = useState<{
    category: string;
    key: string;
    isNew: boolean;
  } | null>(null);
  const [revealed, setRevealed] = useState<Record<string, string>>({});
  const [auditOpen, setAuditOpen] = useState<boolean>(false);
  const [exportOpen, setExportOpen] = useState<boolean>(false);
  const [secondsLeft, setSecondsLeft] = useState<number>(
    status.expires_in_seconds ?? 900,
  );
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadList = useCallback(async () => {
    try {
      const { data } = await axios.get<ListResponse>(
        `${API}/api/admin/cabinet-vault/list`,
        { headers },
      );
      setList(data);
    } catch (err: unknown) {
      // eslint-disable-next-line
      if ((err as any)?.response?.status === 423) {
        toast.message("Vault auto-locked.");
        onLocked();
      } else {
        logger.error(err);
      }
    }
  }, [headers, onLocked]);

  const loadAudit = useCallback(async () => {
    try {
      const { data } = await axios.get<{ items: AuditEntry[] }>(
        `${API}/api/admin/cabinet-vault/audit?limit=200`,
        { headers },
      );
      setAudit(data.items);
    } catch (err) {
      logger.error(err);
    }
  }, [headers]);

  useEffect(() => {
    loadList();
  }, [loadList]);

  // Live countdown ticker
  useEffect(() => {
    if (tickRef.current) clearInterval(tickRef.current);
    tickRef.current = setInterval(() => {
      setSecondsLeft((s) => {
        if (s <= 1) {
          if (tickRef.current) clearInterval(tickRef.current);
          // Auto-trigger relock on the server side via status refresh
          onLocked();
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => {
      if (tickRef.current) clearInterval(tickRef.current);
    };
  }, [onLocked]);

  const lockNow = async () => {
    try {
      await axios.post(
        `${API}/api/admin/cabinet-vault/lock`,
        {},
        { headers },
      );
      toast.success("Vault locked.");
      onLocked();
    } catch (err) {
      logger.error(err);
    }
  };

  const reveal = async (category: string, key: string) => {
    try {
      const { data } = await axios.get<{ value: string }>(
        `${API}/api/admin/cabinet-vault/secret/${encodeURIComponent(category)}/${encodeURIComponent(key)}`,
        { headers },
      );
      setRevealed((r) => ({ ...r, [`${category}/${key}`]: data.value }));
    } catch (err: unknown) {
      // eslint-disable-next-line
      const status2 = (err as any)?.response?.status;
      if (status2 === 423) {
        toast.error("Vault locked. Re-enter mnemonic.");
        onLocked();
      } else {
        toast.error("Reveal failed.");
        logger.error(err);
      }
    }
  };

  const hide = (category: string, key: string) => {
    setRevealed((r) => {
      const next = { ...r };
      delete next[`${category}/${key}`];
      return next;
    });
  };

  const remove = async (category: string, key: string) => {
    if (!window.confirm(`Delete ${category}/${key} permanently?`)) return;
    try {
      await axios.delete(
        `${API}/api/admin/cabinet-vault/secret/${encodeURIComponent(category)}/${encodeURIComponent(key)}`,
        { headers },
      );
      toast.success(`Deleted ${key}.`);
      hide(category, key);
      await loadList();
    } catch (err) {
      toast.error("Delete failed.");
      logger.error(err);
    }
  };

  const ttlMin = Math.floor(secondsLeft / 60);
  const ttlSec = secondsLeft % 60;

  return (
    <div data-testid="cabinet-unlocked">
      {/* Top status bar */}
      <div className="rounded-xl border border-[#18C964]/40 bg-[#18C964]/5 p-4 mb-6 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Unlock size={16} className="text-[#18C964]" />
          <div className="font-display font-semibold">Vault unlocked</div>
          <Badge
            variant="outline"
            className="font-mono text-[10px] uppercase border-[#18C964]/50 text-[#18C964]"
            data-testid="cabinet-secret-count"
          >
            {status.secret_count} secrets stored
          </Badge>
          <Badge
            variant="outline"
            className="font-mono text-[10px] uppercase"
            data-testid="cabinet-ttl-badge"
          >
            auto-lock in {String(ttlMin).padStart(2, "0")}:{String(ttlSec).padStart(2, "0")}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setAuditOpen(true);
              loadAudit();
            }}
            className="rounded-[var(--btn-radius)]"
            data-testid="cabinet-audit-open"
          >
            <History size={14} className="mr-1" /> Audit log
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setExportOpen(true)}
            className="rounded-[var(--btn-radius)]"
            data-testid="cabinet-export-open"
          >
            <Download size={14} className="mr-1" /> Export
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={loadList}
            className="rounded-[var(--btn-radius)]"
            data-testid="cabinet-refresh"
          >
            <RefreshCcw size={14} />
          </Button>
          <Button
            size="sm"
            onClick={lockNow}
            className="rounded-[var(--btn-radius)]"
            data-testid="cabinet-lock-now"
          >
            <Lock size={14} className="mr-1" /> Lock now
          </Button>
        </div>
      </div>

      {/* Categorised secrets */}
      {list && (
        <div className="space-y-4">
          {Object.entries(list.categories).map(([cat, items]) => {
            const meta = CATEGORY_LABELS[cat] || {
              label: cat,
              color: "text-foreground",
            };
            const setCount = items.filter((i) => !i._unset).length;
            const totalCount = items.length;
            return (
              <section
                key={cat}
                className="rounded-xl border border-border bg-card p-4"
                data-testid={`cabinet-category-${cat}`}
              >
                <header className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span
                      className={`font-mono text-[11px] uppercase tracking-[0.25em] ${meta.color}`}
                    >
                      {meta.label}
                    </span>
                    <Badge
                      variant="outline"
                      className="font-mono text-[10px] uppercase"
                    >
                      {setCount}/{totalCount}
                    </Badge>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      setEditing({ category: cat, key: "", isNew: true })
                    }
                    className="rounded-[var(--btn-radius)] h-7"
                    data-testid={`cabinet-add-${cat}`}
                  >
                    <Plus size={12} className="mr-1" /> Add
                  </Button>
                </header>
                <div className="space-y-2">
                  {items.map((item) => {
                    const id = `${cat}/${item.key}`;
                    const isRevealed = id in revealed;
                    return (
                      <div
                        key={id}
                        className={`flex flex-wrap items-center gap-2 rounded-md border ${
                          item._unset ? "border-border/50 opacity-60" : "border-border"
                        } bg-background/40 px-3 py-2`}
                        data-testid={`cabinet-secret-${cat}-${item.key}`}
                      >
                        <span className="font-mono text-xs text-foreground/90 min-w-[180px]">
                          {item.key}
                        </span>
                        <span className="font-mono text-[10px] text-muted-foreground flex-1 truncate">
                          {item._unset ? (
                            <em>not set</em>
                          ) : isRevealed ? (
                            <span className="text-[#18C964]">{revealed[id]}</span>
                          ) : (
                            <span>
                              {"•".repeat(Math.min(item.value_length, 24))} ·
                              fp:{item.value_fingerprint}
                            </span>
                          )}
                        </span>
                        {item.updated_at && (
                          <span className="font-mono text-[10px] text-muted-foreground tabular">
                            {new Date(item.updated_at).toLocaleDateString()} · ×
                            {item.rotation_count}
                          </span>
                        )}
                        <div className="flex items-center gap-1 ml-auto">
                          {!item._unset && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() =>
                                isRevealed
                                  ? hide(cat, item.key)
                                  : reveal(cat, item.key)
                              }
                              className="h-7 px-2"
                              data-testid={`cabinet-reveal-${cat}-${item.key}`}
                            >
                              {isRevealed ? (
                                <EyeOff size={13} />
                              ) : (
                                <Eye size={13} />
                              )}
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              setEditing({
                                category: cat,
                                key: item.key,
                                isNew: !!item._unset,
                              })
                            }
                            className="h-7 px-2 text-[#F59E0B]"
                            data-testid={`cabinet-edit-${cat}-${item.key}`}
                          >
                            {item._unset ? <Plus size={13} /> : <KeyRound size={13} />}
                          </Button>
                          {!item._unset && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => remove(cat, item.key)}
                              className="h-7 px-2 text-[#FF4D4D]"
                              data-testid={`cabinet-delete-${cat}-${item.key}`}
                            >
                              <Trash2 size={13} />
                            </Button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>
      )}

      {/* Edit dialog */}
      {editing && (
        <SecretEditDialog
          key={`${editing.category}-${editing.key}-${editing.isNew}`}
          open={!!editing}
          onClose={() => setEditing(null)}
          headers={headers}
          category={editing.category}
          initialKey={editing.key}
          isNew={editing.isNew}
          onSaved={async () => {
            setEditing(null);
            await loadList();
          }}
        />
      )}

      {/* Audit dialog */}
      <Dialog
        open={auditOpen}
        onOpenChange={(v: boolean) => setAuditOpen(v)}
      >
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Audit log · last 200 actions</DialogTitle>
            <DialogDescription>
              Every read, write, rotate, and unlock is logged with timestamp,
              admin JTI, and IP. Secret values are NEVER stored in the log.
            </DialogDescription>
          </DialogHeader>
          <div
            className="max-h-[60vh] overflow-y-auto font-mono text-[11px]"
            data-testid="cabinet-audit-list"
          >
            {audit ? (
              audit.length === 0 ? (
                <div className="text-muted-foreground py-4">No entries.</div>
              ) : (
                <table className="w-full">
                  <tbody>
                    {audit.map((e) => (
                      <tr key={e._id} className="border-b border-border">
                        <td className="py-1 pr-2 text-muted-foreground tabular">
                          {new Date(e.at).toLocaleString()}
                        </td>
                        <td className="py-1 pr-2 text-[#F59E0B] uppercase">
                          {e.action}
                        </td>
                        <td className="py-1 pr-2 text-foreground/80">
                          {e.category && e.key ? `${e.category}/${e.key}` : "—"}
                        </td>
                        <td className="py-1 text-muted-foreground">
                          {e.ip || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )
            ) : (
              <div className="text-muted-foreground py-4">Loading…</div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Export dialog */}
      <ExportDialog
        open={exportOpen}
        onClose={() => setExportOpen(false)}
        headers={headers}
      />
    </div>
  );
};

// -------------------------------------------------------------------------
// Secret edit dialog
// -------------------------------------------------------------------------
const SecretEditDialog: React.FC<{
  open: boolean;
  onClose: () => void;
  headers: { Authorization: string };
  category: string;
  initialKey: string;
  isNew: boolean;
  onSaved: () => void;
}> = ({ open, onClose, headers, category, initialKey, isNew, onSaved }) => {
  const [keyName, setKeyName] = useState<string>(initialKey);
  const [value, setValue] = useState<string>("");
  const [reveal, setReveal] = useState<boolean>(false);
  const [busy, setBusy] = useState<boolean>(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyName.trim() || !value.trim()) {
      toast.error("Key and value are required.");
      return;
    }
    setBusy(true);
    try {
      await axios.put(
        `${API}/api/admin/cabinet-vault/secret/${encodeURIComponent(category)}/${encodeURIComponent(keyName.trim())}`,
        { value },
        { headers },
      );
      toast.success(isNew ? `${keyName} stored.` : `${keyName} rotated.`);
      onSaved();
    } catch (err: unknown) {
      // eslint-disable-next-line
      const detail = (err as any)?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Save failed.");
      logger.error(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v: boolean) => !v && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {isNew ? "Store new secret" : `Rotate · ${initialKey}`}
          </DialogTitle>
          <DialogDescription>
            Category: <span className="font-mono text-[#F59E0B]">{category}</span>.
            Value is encrypted with AES-256-GCM before persistence.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4" data-testid="cabinet-edit-form">
          <div>
            <Label className="text-xs text-muted-foreground uppercase tracking-widest">
              Key
            </Label>
            <Input
              type="text"
              value={keyName}
              onChange={(e) => setKeyName(e.target.value.toUpperCase().replace(/[^A-Z0-9_]/g, "_"))}
              disabled={!isNew || busy}
              className="mt-1 font-mono"
              autoComplete="off"
              spellCheck={false}
              data-testid="cabinet-edit-key"
            />
          </div>
          <div>
            <Label className="text-xs text-muted-foreground uppercase tracking-widest">
              {isNew ? "Value" : "New value"}
            </Label>
            <div className="relative mt-1">
              <Input
                type={reveal ? "text" : "password"}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                disabled={busy}
                className="font-mono pr-10"
                autoComplete="off"
                spellCheck={false}
                data-testid="cabinet-edit-value"
              />
              <button
                type="button"
                onClick={() => setReveal((v) => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                aria-label={reveal ? "Hide value" : "Show value"}
              >
                {reveal ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={busy}
              className="rounded-[var(--btn-radius)]"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={busy || !keyName.trim() || !value.trim()}
              className="rounded-[var(--btn-radius)]"
              data-testid="cabinet-edit-submit"
            >
              {busy ? "…" : isNew ? "Store secret" : "Rotate"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

// -------------------------------------------------------------------------
// Export dialog
// -------------------------------------------------------------------------
const ExportDialog: React.FC<{
  open: boolean;
  onClose: () => void;
  headers: { Authorization: string };
}> = ({ open, onClose, headers }) => {
  const [pp, setPp] = useState<string>("");
  const [busy, setBusy] = useState<boolean>(false);

  const doExport = async () => {
    if (pp.length < 12) {
      toast.error("Passphrase must be at least 12 characters.");
      return;
    }
    setBusy(true);
    try {
      const { data } = await axios.post(
        `${API}/api/admin/cabinet-vault/export`,
        { passphrase: pp },
        { headers },
      );
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `deepotus-vault-export-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success("Encrypted export downloaded. Store it offline.");
      setPp("");
      onClose();
    } catch (err) {
      toast.error("Export failed.");
      logger.error(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v: boolean) => !v && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Export encrypted backup</DialogTitle>
          <DialogDescription>
            Re-encrypts every secret with a separate passphrase (independent
            from your seed phrase). Store the exported JSON offline (USB,
            paper QR, encrypted drive).
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <Label className="text-xs text-muted-foreground uppercase tracking-widest">
            Export passphrase (≥12 chars)
          </Label>
          <Input
            type="password"
            value={pp}
            onChange={(e) => setPp(e.target.value)}
            placeholder="••••••••••••"
            className="font-mono"
            autoComplete="new-password"
            data-testid="cabinet-export-passphrase"
          />
          <div className="flex items-center gap-2 text-[10px] font-mono text-[#F59E0B]">
            <AlertTriangle size={11} />
            Lose the passphrase = the export is unrecoverable.
          </div>
        </div>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={busy}
            className="rounded-[var(--btn-radius)]"
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={doExport}
            disabled={busy || pp.length < 12}
            className="rounded-[var(--btn-radius)]"
            data-testid="cabinet-export-submit"
          >
            {busy ? "…" : "Download backup"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
