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
  Upload,
  History,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Trash2,
  Plus,
} from "lucide-react";
import { getAdminToken, clearAdminToken } from "@/lib/adminAuth";
import { extractErrorMsg, getErrorCode } from "@/lib/apiError";
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

  // verification quiz: 4 random word indices (was 3 — bumped up to make
  // the "I wrote it down" claim harder to bluff after the operator
  // accidentally skipped the step in the past).
  const [quizIdx] = useState<number[]>(() => {
    const arr: number[] = [];
    while (arr.length < 4) {
      const r = Math.floor(Math.random() * 24);
      if (!arr.includes(r)) arr.push(r);
    }
    return arr.sort((a, b) => a - b);
  });
  const [quizAnswers, setQuizAnswers] = useState<string[]>(["", "", "", ""]);

  // Magic confirmation phrase — the operator must literally type this
  // sentence to acknowledge they've stored the mnemonic offline.
  // This is on top of the per-word quiz: even if the operator copy-pastes
  // the 4 quiz words straight from the still-visible reveal, they have
  // to make a *separate* deliberate gesture acknowledging the persistence.
  const ACK_PHRASE = "I HAVE WRITTEN MY 24 WORDS OFFLINE";
  const [ackText, setAckText] = useState<string>("");

  // Force the operator to actually look at the words for at least 5 s
  // before they can move on to "I wrote it down — verify". Resets when
  // they Hide and Reveal again (so the timer can't be skipped by
  // backgrounding the tab).
  const [readSecondsLeft, setReadSecondsLeft] = useState<number>(0);
  useEffect(() => {
    // Always return a cleanup function (even a no-op) so all paths
    // satisfy `noImplicitReturns` strict-mode of the dev server's
    // fork-ts-checker (which is stricter than CRA's prod build).
    if (step !== "show" || !revealed) {
      setReadSecondsLeft(0);
      return () => {
        /* no-op cleanup */
      };
    }
    setReadSecondsLeft(5);
    const id = setInterval(() => {
      setReadSecondsLeft((s) => {
        if (s <= 1) {
          clearInterval(id);
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [revealed, step]);

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
      toast.error(extractErrorMsg(err, "Vault init failed."));
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
    const wordsOk = quizIdx.every((idx, i) =>
      quizAnswers[i].trim().toLowerCase() === words[idx],
    );
    if (!wordsOk) {
      toast.error("One or more words don't match — re-check your backup.");
      return;
    }
    if (ackText.trim().toUpperCase() !== ACK_PHRASE) {
      toast.error(
        `Type the acknowledgement phrase exactly: "${ACK_PHRASE}".`,
      );
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
            disabled={!revealed || readSecondsLeft > 0}
            className="rounded-[var(--btn-radius)] btn-press"
            data-testid="cabinet-setup-continue-to-verify"
          >
            {readSecondsLeft > 0
              ? `Read carefully… ${readSecondsLeft}s`
              : "I wrote it down — verify →"}
          </Button>
          {revealed && readSecondsLeft > 0 && (
            <span
              className="text-[10px] font-mono text-muted-foreground"
              data-testid="cabinet-setup-read-timer"
            >
              We'll unlock the next step once we're sure you actually
              looked at the words.
            </span>
          )}
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
        Type 4 words from your phrase + acknowledgement.
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
      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
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

      {/* Acknowledgement phrase — defeats "click-through" skipping. */}
      <div className="mt-6">
        <Label className="text-xs text-muted-foreground uppercase tracking-widest">
          Type{" "}
          <code className="px-1 bg-background border border-border rounded text-[#18C964]">
            {ACK_PHRASE}
          </code>{" "}
          to confirm
        </Label>
        <Input
          type="text"
          value={ackText}
          onChange={(e) => setAckText(e.target.value)}
          autoComplete="off"
          spellCheck={false}
          placeholder={ACK_PHRASE}
          className="mt-1 font-mono text-sm"
          data-testid="cabinet-setup-ack-phrase"
        />
        {ackText.trim() &&
          ackText.trim().toUpperCase() !== ACK_PHRASE && (
            <p className="text-[10px] text-[#FF4D4D] mt-1 font-mono">
              Phrase doesn't match. Case-insensitive but every word
              counts.
            </p>
          )}
      </div>

      <div className="mt-6 flex items-center gap-3">
        <Button
          onClick={verifySubmit}
          disabled={
            quizAnswers.some((a) => a.trim() === "") ||
            ackText.trim().toUpperCase() !== ACK_PHRASE
          }
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
      toast.error(extractErrorMsg(err, "Unlock failed."), {
        duration: 8000, // give the user time to read the hint for bad_checksum / vault_mismatch
      });
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

      {/*
        Recovery / Danger Zone — surfaced ONLY when the vault is locked
        (i.e. the operator is staring at the unlock form). The reset is
        gated by 4 cumulative server-side guards (vault locked, admin
        password, 2FA TOTP if active, magic confirm string), but we keep
        the entry-point visually red and collapsed by default so a casual
        click can never trip it.
      */}
      <FactoryResetSection headers={headers} onReset={onUnlocked} />
    </form>
  );
};

// -------------------------------------------------------------------------
// Factory reset (DANGER ZONE)
// -------------------------------------------------------------------------
const FACTORY_RESET_MAGIC = "FACTORY RESET DEEPOTUS";

const FactoryResetSection: React.FC<{
  headers: { Authorization: string };
  onReset: () => void;
}> = ({ headers, onReset }) => {
  const [open, setOpen] = useState<boolean>(false);
  const [dialogOpen, setDialogOpen] = useState<boolean>(false);

  return (
    <div
      className="mt-8 pt-6 border-t border-dashed border-[#FF4D4D]/30"
      data-testid="cabinet-danger-zone"
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 text-[11px] font-mono uppercase tracking-[0.25em] text-[#FF4D4D]/80 hover:text-[#FF4D4D]"
        data-testid="cabinet-danger-zone-toggle"
      >
        <AlertTriangle size={12} />
        {open ? "Hide" : "Show"} recovery options
      </button>

      {open && (
        <div className="mt-4 rounded-md border border-[#FF4D4D]/30 bg-[#FF4D4D]/5 p-4">
          <div className="text-sm font-medium text-[#FF4D4D]">
            Lost your 24-word phrase?
          </div>
          <p className="text-xs text-foreground/70 mt-1 leading-relaxed max-w-prose">
            Without the phrase, the vault is mathematically inaccessible.
            Factory-reset wipes the vault back to a pristine pre-init
            state so you can start over. <strong>Every encrypted secret
            currently stored will be permanently destroyed.</strong> Use
            this only when the mnemonic is truly unrecoverable.
          </p>
          <ul className="mt-3 text-[11px] font-mono text-foreground/60 leading-relaxed space-y-0.5">
            <li>• Vault must be currently locked (it is — that's why you're here).</li>
            <li>• Re-prove the admin password.</li>
            <li>• Provide a fresh 2FA code (if 2FA is enabled).</li>
            <li>
              • Type the literal phrase{" "}
              <code className="px-1 bg-background border border-border rounded">
                {FACTORY_RESET_MAGIC}
              </code>
              .
            </li>
          </ul>
          <div className="mt-4">
            <Button
              type="button"
              variant="destructive"
              size="sm"
              onClick={() => setDialogOpen(true)}
              className="rounded-[var(--btn-radius)]"
              data-testid="cabinet-factory-reset-open"
            >
              <Trash2 size={13} className="mr-1.5" /> Factory reset vault
            </Button>
          </div>
        </div>
      )}

      <FactoryResetDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        headers={headers}
        onResetDone={() => {
          setDialogOpen(false);
          setOpen(false);
          onReset();
        }}
      />
    </div>
  );
};

interface FactoryResetDialogProps {
  open: boolean;
  onClose: () => void;
  headers: { Authorization: string };
  onResetDone: () => void;
}

const FactoryResetDialog: React.FC<FactoryResetDialogProps> = ({
  open,
  onClose,
  headers,
  onResetDone,
}) => {
  const [password, setPassword] = useState<string>("");
  const [totpCode, setTotpCode] = useState<string>("");
  const [confirmText, setConfirmText] = useState<string>("");
  const [busy, setBusy] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Reset all fields whenever the dialog re-opens — never persist a
  // typed password / TOTP between opens.
  useEffect(() => {
    if (open) {
      setPassword("");
      setTotpCode("");
      setConfirmText("");
      setError(null);
      setBusy(false);
    }
  }, [open]);

  const confirmMatches = confirmText === FACTORY_RESET_MAGIC;
  const passwordOk = password.length >= 1;
  // We can't know server-side 2FA state from this component, so we DON'T
  // require a TOTP client-side — the backend will return 401 with a
  // 2fa-required header if needed, and we'll surface it.
  const canSubmit = !busy && confirmMatches && passwordOk;

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      await axios.post(
        `${API}/api/admin/cabinet-vault/factory-reset`,
        {
          password,
          totp_code: totpCode || undefined,
          confirm_text: confirmText,
        },
        { headers },
      );
      toast.success("Vault factory-reset. Generating a new mnemonic…");
      onResetDone();
    } catch (err: unknown) {
      // eslint-disable-next-line
      const e = err as any;
      const detail = e?.response?.data?.detail;
      const status = e?.response?.status;
      const msg =
        (typeof detail === "string" && detail) ||
        (detail && typeof detail === "object" && detail.message) ||
        `Factory reset failed (HTTP ${status ?? "?"}).`;
      setError(String(msg));
      logger.error("[cabinet] factory-reset failed", err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v: boolean) => !v && onClose()}>
      <DialogContent
        className="max-w-md"
        data-testid="cabinet-factory-reset-dialog"
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-[#FF4D4D]">
            <AlertTriangle size={18} /> Factory reset Cabinet Vault
          </DialogTitle>
          <DialogDescription className="text-foreground/70">
            This is destructive and final. Every encrypted secret stored
            in this vault will be wiped. Used only when the BIP39
            mnemonic is permanently lost.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div>
            <Label className="text-xs uppercase tracking-widest">
              Admin password
            </Label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              disabled={busy}
              className="font-mono text-sm"
              data-testid="cabinet-factory-reset-password"
            />
          </div>

          <div>
            <Label className="text-xs uppercase tracking-widest">
              2FA code (only if 2FA is enabled)
            </Label>
            <Input
              type="text"
              value={totpCode}
              onChange={(e) =>
                setTotpCode(e.target.value.replace(/\D/g, "").slice(0, 8))
              }
              placeholder="123456"
              inputMode="numeric"
              autoComplete="one-time-code"
              disabled={busy}
              className="font-mono text-sm tracking-[0.3em]"
              data-testid="cabinet-factory-reset-totp"
            />
            <p className="text-[10px] text-muted-foreground mt-1">
              Leave blank if 2FA isn't enabled yet.
            </p>
          </div>

          <div>
            <Label className="text-xs uppercase tracking-widest">
              Type{" "}
              <code className="px-1 bg-background border border-border rounded text-[#FF4D4D]">
                {FACTORY_RESET_MAGIC}
              </code>{" "}
              to confirm
            </Label>
            <Input
              type="text"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              autoComplete="off"
              spellCheck={false}
              disabled={busy}
              className={`font-mono text-sm ${
                confirmText && !confirmMatches
                  ? "border-[#FF4D4D] focus-visible:ring-[#FF4D4D]/40"
                  : ""
              } ${
                confirmMatches
                  ? "border-[#FF4D4D] focus-visible:ring-[#FF4D4D]/60"
                  : ""
              }`}
              data-testid="cabinet-factory-reset-confirm-text"
            />
            {confirmText && !confirmMatches && (
              <p className="text-[10px] text-[#FF4D4D] mt-1">
                Must match exactly (case-sensitive).
              </p>
            )}
          </div>

          {error && (
            <div
              className="text-xs text-[#FF4D4D] bg-[#FF4D4D]/10 border border-[#FF4D4D]/40 rounded px-3 py-2 font-mono"
              data-testid="cabinet-factory-reset-error"
            >
              <AlertTriangle size={11} className="inline mr-1" />
              {error}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={busy}
            className="rounded-[var(--btn-radius)]"
            data-testid="cabinet-factory-reset-cancel"
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={submit}
            disabled={!canSubmit}
            className="rounded-[var(--btn-radius)]"
            data-testid="cabinet-factory-reset-submit"
          >
            {busy ? (
              <RefreshCcw size={14} className="mr-1.5 animate-spin" />
            ) : (
              <Trash2 size={14} className="mr-1.5" />
            )}
            {busy ? "Wiping…" : "Wipe vault"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
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
  const [importOpen, setImportOpen] = useState<boolean>(false);
  const [twofaEnabled, setTwofaEnabled] = useState<boolean | null>(null);
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

  // Fetch the live 2FA status so the bootstrap banner only shows when
  // 2FA is actually still off. Cabinet Vault writes are gated by a
  // ``BOOTSTRAP_WRITE_LIMIT`` (~30 secrets); past that, the backend
  // hard-requires 2FA. Surfacing this in the panel turns "Save failed"
  // surprises into a deterministic, user-actionable message.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await axios.get<{ enabled: boolean }>(
          `${API}/api/admin/2fa/status`,
          { headers },
        );
        if (!cancelled) setTwofaEnabled(Boolean(data?.enabled));
      } catch (err) {
        // Non-fatal — banner just stays hidden if the probe fails.
        logger.debug("[cabinet-vault] 2fa status probe failed", err);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [headers]);

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
            onClick={() => setImportOpen(true)}
            className="rounded-[var(--btn-radius)]"
            data-testid="cabinet-import-open"
          >
            <Upload size={14} className="mr-1" /> Import
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

      {/* 2FA bootstrap notice — surfaces the security trade-off the
          backend allows during the very first secrets load, so the
          admin doesn't think "Save failed" is a bug when they cross
          the BOOTSTRAP_WRITE_LIMIT. */}
      {twofaEnabled === false && (
        <div
          className="rounded-md border border-[#F59E0B]/40 bg-[#F59E0B]/10 p-4 mb-6"
          data-testid="cabinet-bootstrap-notice"
          role="alert"
        >
          <div className="flex items-start gap-3">
            <AlertTriangle size={16} className="mt-0.5 text-[#F59E0B] shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="text-[11px] font-mono uppercase tracking-[0.25em] text-[#F59E0B]">
                Bootstrap mode — 2FA not enabled
              </div>
              <p className="text-xs text-foreground/80 mt-1.5 leading-relaxed">
                Writes are temporarily allowed without a second factor so
                you can populate the vault right after init.{" "}
                <strong>Reads, exports and imports still require 2FA.</strong>{" "}
                Once the vault holds 30+ secrets, writes will also lock
                behind 2FA.
              </p>
              <div className="mt-2.5">
                <Link
                  to="/admin/security"
                  className="text-[11px] font-mono uppercase tracking-widest text-[#F59E0B] hover:underline"
                  data-testid="cabinet-bootstrap-2fa-link"
                >
                  → Enable 2FA from Admin → Security
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

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
                          {(() => {
                            if (item._unset) return <em>not set</em>;
                            if (isRevealed) {
                              return (
                                <span className="text-[#18C964]">{revealed[id]}</span>
                              );
                            }
                            return (
                              <span>
                                {"•".repeat(Math.min(item.value_length, 24))} ·
                                fp:{item.value_fingerprint}
                              </span>
                            );
                          })()}
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
            {(() => {
              if (!audit) {
                return <div className="text-muted-foreground py-4">Loading…</div>;
              }
              if (audit.length === 0) {
                return <div className="text-muted-foreground py-4">No entries.</div>;
              }
              return (
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
              );
            })()}
          </div>
        </DialogContent>
      </Dialog>

      {/* Export dialog */}
      <ExportDialog
        open={exportOpen}
        onClose={() => setExportOpen(false)}
        headers={headers}
      />

      {/* Import dialog */}
      <ImportDialog
        open={importOpen}
        onClose={() => setImportOpen(false)}
        headers={headers}
        onImported={async () => {
          setImportOpen(false);
          await loadList();
        }}
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
      const code = getErrorCode(err);
      toast.error(extractErrorMsg(err, "Save failed."), {
        duration: code === "TWOFA_REQUIRED" ? 10000 : 6000,
        description:
          code === "TWOFA_REQUIRED"
            ? "Open Admin → Security to enable 2FA, then return here."
            : undefined,
      });
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
              {(() => {
                if (busy) return "…";
                return isNew ? "Store secret" : "Rotate";
              })()}
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


// -------------------------------------------------------------------------
// Import dialog (Sprint 12.5) — restore an encrypted backup bundle.
// -------------------------------------------------------------------------
interface ImportSummary {
  imported: number;
  replaced: number;
  skipped: number;
  total_in_bundle: number;
}

interface ImportDialogProps {
  open: boolean;
  onClose: () => void;
  headers: { Authorization: string };
  onImported: () => void;
}

function ImportDialog({
  open,
  onClose,
  headers,
  onImported,
}: ImportDialogProps) {
  const [pp, setPp] = useState<string>("");
  const [overwrite, setOverwrite] = useState<boolean>(false);
  const [busy, setBusy] = useState<boolean>(false);
  // eslint-disable-next-line
  const [bundle, setBundle] = useState<any | null>(null);
  const [bundleName, setBundleName] = useState<string>("");
  const [parseError, setParseError] = useState<string>("");
  const [summary, setSummary] = useState<ImportSummary | null>(null);

  const reset = () => {
    setPp("");
    setOverwrite(false);
    setBundle(null);
    setBundleName("");
    setParseError("");
    setSummary(null);
  };

  const onFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    setParseError("");
    setBundle(null);
    setBundleName("");
    setSummary(null);
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      setParseError("File too large (>5MB) — that's not a vault backup.");
      return;
    }
    try {
      const txt = await file.text();
      const parsed = JSON.parse(txt);
      if (parsed?.format !== "deepotus-vault-v1") {
        setParseError(
          "Unsupported file format — expected a 'deepotus-vault-v1' export.",
        );
        return;
      }
      if (!Array.isArray(parsed?.secrets)) {
        setParseError("Bundle is missing a 'secrets' array.");
        return;
      }
      setBundle(parsed);
      setBundleName(file.name);
    } catch (err) {
      logger.error(err);
      setParseError("File is not valid JSON.");
    }
  };

  const doImport = async () => {
    if (!bundle || pp.length < 12) return;
    setBusy(true);
    setSummary(null);
    try {
      const { data } = await axios.post<ImportSummary>(
        `${API}/api/admin/cabinet-vault/import`,
        { bundle, passphrase: pp, overwrite },
        { headers },
      );
      setSummary(data);
      toast.success(
        `Restored ${data.imported + data.replaced}/${data.total_in_bundle} secrets.`,
      );
    } catch (err: unknown) {
      toast.error(
        extractErrorMsg(err, "Import failed — wrong passphrase or tampered backup."),
      );
      logger.error(err);
    } finally {
      setBusy(false);
    }
  };

  const handleClose = () => {
    if (busy) return;
    reset();
    onClose();
  };

  const handleDone = () => {
    reset();
    onImported();
  };

  const secretCount = bundle?.secrets?.length ?? 0;
  const exportedAt = bundle?.exported_at as string | undefined;

  return (
    <Dialog open={open} onOpenChange={(v: boolean) => !v && handleClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Restore from encrypted backup</DialogTitle>
          <DialogDescription>
            Upload a JSON bundle previously produced by{" "}
            <strong>Export</strong>, then enter the passphrase you set at
            export time. Each secret is decrypted off the bundle and
            re-encrypted with the live vault master key.
          </DialogDescription>
        </DialogHeader>

        {!summary && (
          <div className="space-y-4">
            <div>
              <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                Encrypted bundle (.json)
              </Label>
              <Input
                type="file"
                accept="application/json,.json"
                onChange={onFile}
                disabled={busy}
                className="mt-1 font-mono text-xs"
                data-testid="cabinet-import-file"
              />
              {bundle && (
                <div className="mt-2 rounded-md border border-border bg-background/40 px-3 py-2 font-mono text-[11px]">
                  <div className="text-foreground/90 truncate">
                    {bundleName || "bundle.json"}
                  </div>
                  <div className="text-muted-foreground mt-0.5">
                    {secretCount} secrets ·{" "}
                    {exportedAt
                      ? new Date(exportedAt).toLocaleString()
                      : "no export date"}
                  </div>
                </div>
              )}
              {parseError && (
                <div
                  className="mt-2 flex items-center gap-2 rounded-md border border-[#FF4D4D]/40 bg-[#FF4D4D]/5 px-3 py-2 text-[11px] font-mono text-[#FF4D4D]"
                  data-testid="cabinet-import-parse-error"
                >
                  <AlertTriangle size={12} /> {parseError}
                </div>
              )}
            </div>

            <div>
              <Label className="text-xs text-muted-foreground uppercase tracking-widest">
                Passphrase used at export (≥12 chars)
              </Label>
              <Input
                type="password"
                value={pp}
                onChange={(e) => setPp(e.target.value)}
                disabled={busy}
                className="mt-1 font-mono"
                autoComplete="new-password"
                placeholder="••••••••••••"
                data-testid="cabinet-import-passphrase"
              />
            </div>

            <label
              className="flex items-center gap-2 cursor-pointer select-none text-xs"
              data-testid="cabinet-import-overwrite-label"
            >
              <input
                type="checkbox"
                checked={overwrite}
                onChange={(e) => setOverwrite(e.target.checked)}
                disabled={busy}
                className="accent-[#F59E0B]"
                data-testid="cabinet-import-overwrite"
              />
              <span className="text-foreground/80">
                Overwrite existing secrets (default: skip when a key already
                lives in the vault).
              </span>
            </label>

            <div className="flex items-center gap-2 text-[10px] font-mono text-[#F59E0B]">
              <AlertTriangle size={11} />
              Wrong passphrase → atomic abort. Nothing is written until every
              entry decrypts successfully.
            </div>
          </div>
        )}

        {summary && (
          <div
            className="rounded-md border border-[#18C964]/40 bg-[#18C964]/5 p-4 space-y-2"
            data-testid="cabinet-import-summary"
          >
            <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.25em] text-[#18C964]">
              <CheckCircle2 size={14} /> Import complete
            </div>
            <div className="grid grid-cols-2 gap-3 font-mono text-[11px]">
              <div className="rounded border border-border bg-background/40 px-3 py-2">
                <div className="text-muted-foreground">imported (new)</div>
                <div className="text-2xl text-[#18C964] tabular">
                  {summary.imported}
                </div>
              </div>
              <div className="rounded border border-border bg-background/40 px-3 py-2">
                <div className="text-muted-foreground">replaced</div>
                <div className="text-2xl text-[#F59E0B] tabular">
                  {summary.replaced}
                </div>
              </div>
              <div className="rounded border border-border bg-background/40 px-3 py-2">
                <div className="text-muted-foreground">skipped (kept live)</div>
                <div className="text-2xl text-foreground/70 tabular">
                  {summary.skipped}
                </div>
              </div>
              <div className="rounded border border-border bg-background/40 px-3 py-2">
                <div className="text-muted-foreground">bundle total</div>
                <div className="text-2xl text-foreground tabular">
                  {summary.total_in_bundle}
                </div>
              </div>
            </div>
          </div>
        )}

        <DialogFooter>
          {!summary ? (
            <>
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={busy}
                className="rounded-[var(--btn-radius)]"
              >
                Cancel
              </Button>
              <Button
                type="button"
                onClick={doImport}
                disabled={busy || !bundle || pp.length < 12}
                className="rounded-[var(--btn-radius)]"
                data-testid="cabinet-import-submit"
              >
                {busy ? "…" : `Restore ${secretCount} secrets`}
              </Button>
            </>
          ) : (
            <Button
              type="button"
              onClick={handleDone}
              className="rounded-[var(--btn-radius)]"
              data-testid="cabinet-import-done"
            >
              Done
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
