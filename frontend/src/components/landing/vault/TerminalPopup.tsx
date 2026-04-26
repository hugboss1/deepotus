import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Send, CheckCircle2, AlertTriangle, Mail, KeyRound, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useI18n } from "@/i18n/I18nProvider";
import { logger } from "@/lib/logger";
import type { AccessSession } from "@/types";

const API = process.env.REACT_APP_BACKEND_URL;
const SESSION_KEY = "deepotus_access_session";

type TerminalPhase =
  | "denied"
  | "sealed"
  | "form"
  | "genesis-form"
  | "verify-existing"
  | "sending"
  | "verifying"
  | "success"
  | "genesis-success"
  | "verify-success"
  | "error";

interface SealedStatus {
  sealed: boolean;
  mint_live: boolean;
  launch_eta: string | null;
  source: "auto" | "override";
}

interface GenesisResponse {
  ok: boolean;
  email: string;
  display_name: string;
  message: string;
  launch_eta: string | null;
  already_subscribed: boolean;
  position?: number;
}

interface TerminalPopupProps {
  open: boolean;
  onClose: () => void;
}

/**
 * TerminalPopup — a CRT-style terminal modal used as the GATE after the
 * fake vault cracks. It denies direct access, taunts the visitor ("nice try,
 * you only have LEVEL 1 clearance") and offers TWO branches:
 *   1. Request a fresh Level-2 access card (email-gated).
 *   2. Verify an existing accreditation code (for visitors returning within
 *      the 24 h validity window — they go straight to the vault).
 *
 * SEALED MODE: when /api/vault/classified-status returns sealed=true (mint
 * not yet on-chain), the terminal switches to the "sealed" phase narrative:
 * both Level-02 buttons are visually disabled and the only available action
 * is to subscribe to the Genesis broadcast (Mail #1).
 */
export default function TerminalPopup({ open, onClose }: TerminalPopupProps) {
  const { t, lang } = useI18n();
  const [phase, setPhase] = useState<TerminalPhase>("denied");
  const [email, setEmail] = useState<string>("");
  const [displayName, setDisplayName] = useState<string>("");
  const [existingCode, setExistingCode] = useState<string>("");
  const [result, setResult] = useState<AccessSession | null>(null);
  const [genesisResult, setGenesisResult] = useState<GenesisResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [typedLines, setTypedLines] = useState<string[]>([]);
  const [showCursor, setShowCursor] = useState<boolean>(true);
  const [sealedStatus, setSealedStatus] = useState<SealedStatus | null>(null);

  // Typing animation for the "denied" / "sealed" intro
  const deniedLines: string[] = useMemo(
    () => (t("terminal.deniedLines") as string[]) || [],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [lang],
  );
  const sealedLines: string[] = useMemo(
    () => (t("terminal.sealedLines") as string[]) || [],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [lang],
  );

  // Fetch the seal status whenever the terminal opens — this drives the
  // initial phase ("sealed" pre-mint, "denied" post-mint).
  useEffect(() => {
    if (!open) return undefined;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API}/api/vault/classified-status`);
        if (!res.ok) throw new Error(`status ${res.status}`);
        const data: SealedStatus = await res.json();
        if (cancelled) return;
        setSealedStatus(data);
      } catch (err) {
        logger.error(err);
        // On failure, fall back to "denied" (safer UX — never lock out users
        // due to a network blip on the public seal endpoint).
        if (!cancelled) setSealedStatus({ sealed: false, mint_live: true, launch_eta: null, source: "auto" });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open]);

  // Reset state on every open and switch to sealed/denied based on status.
  useEffect(() => {
    if (!open) return undefined;
    if (sealedStatus === null) return undefined; // wait for the fetch to settle
    setPhase(sealedStatus.sealed ? "sealed" : "denied");
    setTypedLines([]);
    setEmail("");
    setDisplayName("");
    setExistingCode("");
    setResult(null);
    setGenesisResult(null);
    setErrorMsg(null);
    return undefined;
  }, [open, sealedStatus]);

  // Animate typing of denied/sealed lines, one per ~700ms.
  // Uses a ref to ensure only ONE interval is active even under React 18
  // StrictMode double-effect runs (which would otherwise race & duplicate).
  const typingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  useEffect(() => {
    if (!open) return undefined;
    if (phase !== "denied" && phase !== "sealed") return undefined;
    // Always clear any prior interval first (defensive against StrictMode).
    if (typingIntervalRef.current) {
      clearInterval(typingIntervalRef.current);
      typingIntervalRef.current = null;
    }
    const lines = phase === "sealed" ? sealedLines : deniedLines;
    let i = 0;
    setTypedLines([]);
    const id = setInterval(() => {
      if (i >= lines.length) {
        clearInterval(id);
        if (typingIntervalRef.current === id) {
          typingIntervalRef.current = null;
        }
        return;
      }
      const next = lines[i];
      i += 1;
      // Functional update protects against double-pushes if React re-renders
      // before the interval ticks again.
      setTypedLines((prev) => {
        if (prev.length >= i) return prev; // already at or past this index
        return [...prev, next];
      });
    }, 600);
    typingIntervalRef.current = id;
    return () => {
      clearInterval(id);
      if (typingIntervalRef.current === id) {
        typingIntervalRef.current = null;
      }
    };
  }, [open, phase, deniedLines, sealedLines]);

  // Blinking cursor
  useEffect(() => {
    if (!open) return undefined;
    const id = setInterval(() => setShowCursor((c) => !c), 520);
    return () => clearInterval(id);
  }, [open]);

  async function submitRequest(e: React.FormEvent) {
    e?.preventDefault();
    const trimmed = email.trim();
    if (!trimmed || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) {
      setErrorMsg(t("terminal.emailInvalid"));
      return;
    }
    setErrorMsg(null);
    setPhase("sending");
    try {
      const res = await fetch(`${API}/api/access-card/request`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept-Language": lang,
        },
        body: JSON.stringify({
          email: trimmed,
          display_name: displayName.trim() || undefined,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setResult(data);
      setPhase("success");
    } catch (err: unknown) {
      // eslint-disable-next-line
      setErrorMsg(String((err as any)?.message || err));
      setPhase("error");
    }
  }

  async function submitVerifyExisting(e: React.FormEvent) {
    e?.preventDefault();
    // Sanitize: uppercase + only alnum and dashes
    const raw = (existingCode || "")
      .trim()
      .toUpperCase()
      .replace(/[^A-Z0-9-]/g, "");
    if (!raw || raw.length < 6) {
      setErrorMsg(t("terminal.codeInvalid") || "Invalid code");
      return;
    }
    setErrorMsg(null);
    setPhase("verifying");
    try {
      const res = await fetch(`${API}/api/access-card/verify`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept-Language": lang,
        },
        body: JSON.stringify({ accreditation_number: raw }),
      });
      const data = await res.json().catch(() => null);
      if (!data?.ok) {
        // Backend returns ok=false for "not recognized" / "expired" with a
        // human message — surface it back to the visitor.
        setErrorMsg(data?.message || t("terminal.codeRejected"));
        setPhase("verify-existing");
        return;
      }
      // Persist the session under the SAME key the /classified-vault page
      // reads — this lets the visitor land directly inside the vault when
      // we redirect, with no digicode prompt.
      try {
        localStorage.setItem(SESSION_KEY, JSON.stringify(data));
      } catch (storageErr) {
        // localStorage can throw in private mode — still proceed with the
        // redirect, the page will simply prompt for the code again.
        // (logged via console for dev)
        // eslint-disable-next-line no-console
        logger.warn("session persist failed", storageErr);
      }
      setResult(data);
      setPhase("verify-success");
      // Auto-redirect after a short beat so the user sees the confirmation
      setTimeout(() => {
        window.location.href = "/classified-vault";
      }, 1500);
    } catch (err: unknown) {
      // eslint-disable-next-line
      setErrorMsg(String((err as any)?.message || err));
      setPhase("error");
    }
  }

  async function submitGenesis(e: React.FormEvent) {
    e?.preventDefault();
    const cleanEmail = (email || "").trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cleanEmail)) {
      setErrorMsg(t("terminal.emailInvalid") || "Invalid email");
      return;
    }
    setErrorMsg(null);
    setPhase("sending");
    try {
      const res = await fetch(`${API}/api/access-card/genesis-broadcast`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept-Language": lang,
        },
        body: JSON.stringify({
          email: cleanEmail,
          display_name: (displayName || "").trim() || null,
          lang,
        }),
      });
      if (!res.ok) {
        // 410 VAULT_LIVE: vault opened between mount and submit — restart
        // the terminal in the regular "denied" flow.
        if (res.status === 410) {
          setSealedStatus({ sealed: false, mint_live: true, launch_eta: null, source: "auto" });
          setPhase("denied");
          return;
        }
        throw new Error(`HTTP ${res.status}`);
      }
      const data: GenesisResponse = await res.json();
      setGenesisResult(data);
      setPhase("genesis-success");
    } catch (err: unknown) {
      // eslint-disable-next-line
      setErrorMsg(String((err as any)?.message || err));
      setPhase("error");
    }
  }

  if (!open) return null;

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          key="terminal-root"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
          className="fixed inset-0 z-[200] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
          onClick={onClose}
          data-testid="terminal-popup-root"
        >
          <motion.div
            key="terminal-shell"
            initial={{ scale: 0.95, y: 20, opacity: 0 }}
            animate={{ scale: 1, y: 0, opacity: 1 }}
            exit={{ scale: 0.96, y: 8, opacity: 0 }}
            transition={{ duration: 0.3 }}
            onClick={(e) => e.stopPropagation()}
            className="relative w-full max-w-2xl rounded-xl border border-[#18C964]/40 bg-black shadow-[0_0_40px_rgba(24,201,100,0.25)] overflow-hidden"
            data-testid="terminal-popup"
          >
            {/* Scanline overlay */}
            <div
              aria-hidden
              className="pointer-events-none absolute inset-0 z-10 opacity-20"
              style={{
                backgroundImage:
                  "repeating-linear-gradient(0deg, rgba(255,255,255,0.04) 0, rgba(255,255,255,0.04) 1px, transparent 1px, transparent 3px)",
              }}
            />
            {/* CRT vignette */}
            <div
              aria-hidden
              className="pointer-events-none absolute inset-0 z-10"
              style={{
                background:
                  "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.45) 100%)",
              }}
            />

            {/* Title bar */}
            <div className="relative z-20 flex items-center justify-between px-4 py-2 border-b border-[#18C964]/30 bg-black">
              <div className="flex items-center gap-2 font-mono text-[11px] text-[#18C964]/90">
                <span className="inline-block w-2 h-2 rounded-full bg-[#18C964] animate-pulse" />
                TTY/DS-GATE-02 · PROTOCOL ΔΣ
              </div>
              <button
                onClick={onClose}
                className="text-[#18C964]/60 hover:text-[#18C964] transition-colors"
                aria-label="Close terminal"
                data-testid="terminal-close"
              >
                <X size={16} />
              </button>
            </div>

            {/* Terminal body */}
            <div
              className="relative z-20 min-h-[340px] p-5 md:p-6 font-mono text-[13px] md:text-sm text-[#18C964] leading-relaxed"
              style={{ textShadow: "0 0 6px rgba(24,201,100,0.55)" }}
            >
              {/* DENIED phase */}
              {phase === "denied" && (
                <div data-testid="terminal-phase-denied">
                  <div className="text-[#18C964]/70 text-[11px] mb-3">
                    &gt; BOOT · handshake OK · verifying clearance…
                  </div>
                  {typedLines.map((line, i) => (
                    <div
                      key={`tty-${i}-${(line || "").slice(0, 16)}`}
                      className="whitespace-pre-wrap mb-1"
                    >
                      {line}
                    </div>
                  ))}
                  {typedLines.length < deniedLines.length && (
                    <span className="inline-block w-2 h-4 bg-[#18C964] align-middle ml-1" />
                  )}
                  {typedLines.length >= deniedLines.length && (
                    <div className="mt-6 flex flex-col gap-3">
                      <div className="flex items-center gap-3 flex-wrap">
                        <Button
                          onClick={() => setPhase("form")}
                          className="rounded-md bg-[#18C964] hover:bg-[#18C964]/90 text-black font-mono font-semibold"
                          data-testid="terminal-request-level2"
                        >
                          {t("terminal.ctaRequest")} →
                        </Button>
                        <button
                          onClick={onClose}
                          className="text-[#18C964]/60 hover:text-[#18C964] font-mono text-xs underline decoration-dashed underline-offset-2"
                          data-testid="terminal-retreat"
                        >
                          {t("terminal.ctaRetreat")}
                        </button>
                      </div>
                      <div className="flex items-center gap-2 pt-2 border-t border-[#18C964]/20 mt-1">
                        <span className="text-[10px] text-[#18C964]/50 font-mono">
                          {t("terminal.alreadyCleared")}
                        </span>
                        <button
                          onClick={() => {
                            setErrorMsg(null);
                            setPhase("verify-existing");
                          }}
                          className="inline-flex items-center gap-1 text-[#22D3EE] hover:text-[#67E8F9] font-mono text-[11px] uppercase tracking-widest underline decoration-dotted underline-offset-2"
                          data-testid="terminal-verify-existing-cta"
                        >
                          <KeyRound size={11} />
                          {t("terminal.ctaVerifyExisting")}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* SEALED phase — pre-launch (mint not yet on-chain) */}
              {phase === "sealed" && (
                <div data-testid="terminal-phase-sealed">
                  <div className="text-[#F59E0B]/80 text-[11px] mb-3 inline-flex items-center gap-2">
                    <span className="inline-block w-2 h-2 rounded-full bg-[#F59E0B] animate-pulse" />
                    &gt; SECURE_CHANNEL · {String(t("terminal.sealedBadge"))} · {lang.toUpperCase()}
                  </div>
                  {typedLines.map((line, i) => (
                    <div
                      key={`tty-sealed-${i}-${(line || "").slice(0, 16)}`}
                      className="whitespace-pre-wrap mb-1"
                    >
                      {line}
                    </div>
                  ))}
                  {typedLines.length < sealedLines.length && (
                    <span className="inline-block w-2 h-4 bg-[#F59E0B] align-middle ml-1" />
                  )}
                  {typedLines.length >= sealedLines.length && (
                    <div className="mt-6 flex flex-col gap-4">
                      {/* Transmission schedule strip — kept mysterious by design.
                          The Deep State does not announce its own genesis;
                          launch_eta is intentionally stripped from the public
                          endpoint (admin still sees it). */}
                      <div className="rounded-md border border-[#F59E0B]/30 bg-[#F59E0B]/5 px-3 py-2 font-mono text-[11px] text-[#F59E0B]/90 inline-flex items-center gap-2 max-w-full">
                        <span className="font-bold whitespace-nowrap">
                          ⌛ {String(t("terminal.sealedEtaLabel"))}
                        </span>
                        <span className="text-[#F59E0B]/70">·</span>
                        <span
                          className="text-[#F59E0B]/70 italic"
                          data-testid="terminal-sealed-eta"
                        >
                          {sealedStatus?.launch_eta
                            ? new Date(sealedStatus.launch_eta).toLocaleString(
                                lang === "fr" ? "fr-FR" : "en-US",
                                {
                                  dateStyle: "long",
                                  timeStyle: "short",
                                },
                              )
                            : String(t("terminal.sealedNoEta"))}
                        </span>
                      </div>

                      {/* Locked CTAs (visually disabled) */}
                      <div className="flex flex-col gap-2 max-w-md">
                        <div
                          className="flex items-center justify-between gap-2 rounded-md border border-[#18C964]/15 bg-[#0A0F0A] px-3 py-2 opacity-60 cursor-not-allowed"
                          title={String(t("terminal.sealedLockedTooltip"))}
                          data-testid="terminal-sealed-locked-request"
                        >
                          <span className="font-mono text-xs text-[#18C964]/70 inline-flex items-center gap-2">
                            <Mail size={12} />
                            {t("terminal.sealedAccredLocked")}
                          </span>
                          <span className="font-mono text-[10px] uppercase tracking-widest text-[#F59E0B]/80">
                            🔒 LOCKED
                          </span>
                        </div>
                        <div
                          className="flex items-center justify-between gap-2 rounded-md border border-[#18C964]/15 bg-[#0A0F0A] px-3 py-2 opacity-60 cursor-not-allowed"
                          title={String(t("terminal.sealedLockedTooltip"))}
                          data-testid="terminal-sealed-locked-verify"
                        >
                          <span className="font-mono text-xs text-[#22D3EE]/70 inline-flex items-center gap-2">
                            <KeyRound size={12} />
                            {t("terminal.sealedVerifyLocked")}
                          </span>
                          <span className="font-mono text-[10px] uppercase tracking-widest text-[#F59E0B]/80">
                            🔒 LOCKED
                          </span>
                        </div>
                      </div>

                      {/* Genesis CTA — the only available branch */}
                      <div className="flex items-center gap-3 flex-wrap pt-2 border-t border-[#F59E0B]/20">
                        <Button
                          onClick={() => {
                            setErrorMsg(null);
                            setPhase("genesis-form");
                          }}
                          className="rounded-md bg-[#F59E0B] hover:bg-[#F59E0B]/90 text-black font-mono font-semibold"
                          data-testid="terminal-genesis-cta"
                        >
                          {t("terminal.sealedCtaGenesis")}
                        </Button>
                        <button
                          onClick={onClose}
                          className="text-[#18C964]/60 hover:text-[#18C964] font-mono text-xs underline decoration-dashed underline-offset-2"
                          data-testid="terminal-sealed-retreat"
                        >
                          {t("terminal.ctaRetreat")}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* GENESIS FORM — pre-launch subscription (Mail #1) */}
              {phase === "genesis-form" && (
                <form onSubmit={submitGenesis} data-testid="terminal-phase-genesis-form">
                  <div className="text-[#F59E0B]/80 text-[11px] mb-3">
                    &gt; archive.genesis.subscription · {lang.toUpperCase()}
                  </div>
                  <div className="mb-3">{t("terminal.sealedFormIntro")}</div>
                  <div className="space-y-3 max-w-md">
                    <div>
                      <label
                        htmlFor="terminal-genesis-email"
                        className="text-[11px] text-[#F59E0B]/80 block mb-1"
                      >
                        &gt; {t("terminal.emailLabel")}
                      </label>
                      <Input
                        id="terminal-genesis-email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder={String(t("terminal.emailPlaceholder"))}
                        className="bg-black/60 border-[#F59E0B]/30 text-[#18C964] font-mono placeholder:text-[#18C964]/30"
                        autoFocus
                        data-testid="terminal-genesis-email-input"
                      />
                    </div>
                    <div>
                      <label
                        htmlFor="terminal-genesis-name"
                        className="text-[11px] text-[#F59E0B]/80 block mb-1"
                      >
                        &gt; {t("terminal.nameLabel")}
                      </label>
                      <Input
                        id="terminal-genesis-name"
                        type="text"
                        value={displayName}
                        onChange={(e) => setDisplayName(e.target.value)}
                        placeholder={String(t("terminal.namePlaceholder"))}
                        className="bg-black/60 border-[#F59E0B]/30 text-[#18C964] font-mono placeholder:text-[#18C964]/30"
                        data-testid="terminal-genesis-name-input"
                      />
                    </div>
                    {errorMsg && (
                      <div className="text-[#FF4D4D] text-xs flex items-center gap-2">
                        <AlertTriangle size={12} />
                        {errorMsg}
                      </div>
                    )}
                    <div className="flex items-center gap-3 pt-1">
                      <Button
                        type="submit"
                        className="rounded-md bg-[#F59E0B] hover:bg-[#F59E0B]/90 text-black font-mono font-semibold"
                        data-testid="terminal-genesis-submit"
                      >
                        <Send size={14} className="mr-1" />
                        {t("terminal.sealedSubmit")}
                      </Button>
                      <button
                        type="button"
                        onClick={() => setPhase("sealed")}
                        className="text-[#18C964]/60 hover:text-[#18C964] font-mono text-xs underline decoration-dashed underline-offset-2"
                        data-testid="terminal-genesis-back"
                      >
                        {t("terminal.back")}
                      </button>
                    </div>
                  </div>
                </form>
              )}

              {/* GENESIS SUCCESS phase */}
              {phase === "genesis-success" && (
                <div data-testid="terminal-phase-genesis-success">
                  <div className="text-[#F59E0B]/80 text-[11px] mb-3 inline-flex items-center gap-2">
                    <CheckCircle2 size={12} className="text-[#F59E0B]" />
                    &gt; archive.confirmed · {lang.toUpperCase()}
                  </div>
                  <div className="text-[#F59E0B] text-base font-semibold mb-3">
                    {t("terminal.sealedSuccessTitle")}
                  </div>
                  <div className="text-[#18C964]/85 mb-3 leading-relaxed">
                    {String(t("terminal.sealedSuccessLead")).replace(
                      "__POSITION__",
                      String(genesisResult?.position ?? "—"),
                    )}
                  </div>
                  {genesisResult?.already_subscribed && (
                    <div className="text-[#22D3EE]/80 text-xs italic mb-3">
                      {t("terminal.sealedAlreadySubscribed")}
                    </div>
                  )}
                  <div className="text-[#18C964]/70 text-xs mb-4 leading-relaxed">
                    {t("terminal.sealedSuccessNext")}
                  </div>
                  <Button
                    onClick={onClose}
                    className="rounded-md bg-[#18C964] hover:bg-[#18C964]/90 text-black font-mono font-semibold"
                    data-testid="terminal-genesis-close"
                  >
                    {t("terminal.close")}
                  </Button>
                </div>
              )}


              {/* FORM phase */}
              {phase === "form" && (
                <form onSubmit={submitRequest} data-testid="terminal-phase-form">
                  <div className="text-[#18C964]/70 text-[11px] mb-3">
                    &gt; request.clearance.level_02 · {lang.toUpperCase()}
                  </div>
                  <div className="mb-3">{t("terminal.formIntro")}</div>
                  <div className="space-y-3 max-w-md">
                    <div>
                      <label
                        htmlFor="terminal-email"
                        className="text-[11px] text-[#18C964]/70 block mb-1"
                      >
                        &gt; {t("terminal.emailLabel")}
                      </label>
                      <Input
                        id="terminal-email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder={t("terminal.emailPlaceholder")}
                        type="email"
                        required
                        autoFocus
                        className="bg-black border-[#18C964]/40 focus-visible:ring-[#18C964]/60 text-[#18C964] font-mono placeholder:text-[#18C964]/30"
                        data-testid="terminal-email-input"
                      />
                    </div>
                    <div>
                      <label
                        htmlFor="terminal-name"
                        className="text-[11px] text-[#18C964]/70 block mb-1"
                      >
                        &gt; {t("terminal.nameLabel")}
                      </label>
                      <Input
                        id="terminal-name"
                        value={displayName}
                        onChange={(e) => setDisplayName(e.target.value)}
                        placeholder={t("terminal.namePlaceholder")}
                        className="bg-black border-[#18C964]/40 focus-visible:ring-[#18C964]/60 text-[#18C964] font-mono placeholder:text-[#18C964]/30"
                        data-testid="terminal-name-input"
                      />
                    </div>
                  </div>
                  {errorMsg && (
                    <div className="mt-3 flex items-center gap-2 text-red-400 text-xs">
                      <AlertTriangle size={12} /> {errorMsg}
                    </div>
                  )}
                  <div className="mt-5 flex items-center gap-3 flex-wrap">
                    <Button
                      type="submit"
                      className="rounded-md bg-[#18C964] hover:bg-[#18C964]/90 text-black font-mono font-semibold"
                      data-testid="terminal-submit"
                    >
                      <Send size={14} className="mr-1.5" />
                      {t("terminal.submit")}
                    </Button>
                    <button
                      type="button"
                      onClick={() => setPhase("denied")}
                      className="text-[#18C964]/60 hover:text-[#18C964] font-mono text-xs"
                    >
                      ← {t("terminal.back")}
                    </button>
                  </div>
                </form>
              )}

              {/* VERIFY-EXISTING phase — for visitors returning within 24h */}
              {phase === "verify-existing" && (
                <form
                  onSubmit={submitVerifyExisting}
                  data-testid="terminal-phase-verify-existing"
                >
                  <div className="text-[#22D3EE]/80 text-[11px] mb-3">
                    &gt; verify.existing.clearance · {lang.toUpperCase()}
                  </div>
                  <div className="mb-3 leading-relaxed">
                    {t("terminal.verifyExistingIntro")}
                  </div>
                  <div className="space-y-3 max-w-md">
                    <div>
                      <label
                        htmlFor="terminal-existing-code"
                        className="text-[11px] text-[#22D3EE]/80 block mb-1"
                      >
                        &gt; {t("terminal.codeLabel")}
                      </label>
                      <Input
                        id="terminal-existing-code"
                        value={existingCode}
                        onChange={(e) =>
                          setExistingCode(e.target.value.toUpperCase())
                        }
                        placeholder={t("terminal.codePlaceholder")}
                        autoFocus
                        autoComplete="off"
                        spellCheck={false}
                        className="bg-black border-[#22D3EE]/40 focus-visible:ring-[#22D3EE]/60 text-[#22D3EE] font-mono tracking-widest placeholder:text-[#22D3EE]/30"
                        data-testid="terminal-existing-code-input"
                      />
                    </div>
                  </div>
                  {errorMsg && (
                    <div className="mt-3 flex items-center gap-2 text-red-400 text-xs">
                      <AlertTriangle size={12} /> {errorMsg}
                    </div>
                  )}
                  <div className="mt-5 flex items-center gap-3 flex-wrap">
                    <Button
                      type="submit"
                      className="rounded-md bg-[#22D3EE] hover:bg-[#22D3EE]/90 text-black font-mono font-semibold"
                      data-testid="terminal-verify-existing-submit"
                    >
                      <KeyRound size={14} className="mr-1.5" />
                      {t("terminal.verifyExistingSubmit")}
                    </Button>
                    <button
                      type="button"
                      onClick={() => {
                        setErrorMsg(null);
                        setPhase("denied");
                      }}
                      className="text-[#18C964]/60 hover:text-[#18C964] font-mono text-xs"
                    >
                      ← {t("terminal.back")}
                    </button>
                  </div>
                  <div className="mt-4 text-[10px] text-[#22D3EE]/50 leading-relaxed">
                    {t("terminal.verifyExistingHint")}
                  </div>
                </form>
              )}

              {/* VERIFYING phase */}
              {phase === "verifying" && (
                <div data-testid="terminal-phase-verifying">
                  <div className="space-y-1 text-[13px] text-[#22D3EE]">
                    <div>&gt; CONTACTING DEEP-STATE REGISTRY…</div>
                    <div>&gt; CHECKING ACCREDITATION VALIDITY…</div>
                    <div>&gt; VERIFYING 24H WINDOW…</div>
                    <div>
                      &gt; FINALIZING CLEARANCE
                      {showCursor ? " █" : " "}
                    </div>
                  </div>
                </div>
              )}

              {/* VERIFY-SUCCESS phase — auto-redirects to /classified-vault */}
              {phase === "verify-success" && result && (
                <div data-testid="terminal-phase-verify-success">
                  <div className="flex items-center gap-2 mb-3">
                    <CheckCircle2 size={18} className="text-[#22D3EE]" />
                    <span className="text-[#22D3EE] font-semibold">
                      {t("terminal.verifySuccessTitle")}
                    </span>
                  </div>
                  <div className="space-y-1">
                    <div>
                      &gt; agent:{" "}
                      <span className="text-[#F59E0B]">
                        {result.display_name || "—"}
                      </span>
                    </div>
                    <div>
                      &gt; accred:{" "}
                      <span className="text-[#22D3EE] tracking-widest">
                        {result.accreditation_number}
                      </span>
                    </div>
                    <div>
                      &gt; status:{" "}
                      <span className="text-[#18C964]">CLEARED · LEVEL 02</span>
                    </div>
                  </div>
                  <div className="mt-5 flex items-center gap-2 text-[#22D3EE]/80 text-xs">
                    <ArrowRight size={12} />
                    {t("terminal.verifySuccessRedirecting")}
                  </div>
                </div>
              )}

              {/* SENDING phase */}
              {phase === "sending" && (
                <div data-testid="terminal-phase-sending">
                  <div className="space-y-1 text-[13px]">
                    <div>&gt; OPENING SECURE CHANNEL…</div>
                    <div>&gt; ENCRYPTING PAYLOAD…</div>
                    <div>&gt; SIGNING WITH ΔΣ CERT…</div>
                    <div>
                      &gt; DISPATCHING ACCESS CARD
                      {showCursor ? " █" : " "}
                    </div>
                  </div>
                </div>
              )}

              {/* SUCCESS phase */}
              {phase === "success" && result && (
                <div data-testid="terminal-phase-success">
                  <div className="flex items-center gap-2 mb-3">
                    <CheckCircle2 size={18} className="text-[#18C964]" />
                    <span className="text-[#18C964] font-semibold">
                      {t("terminal.successTitle")}
                    </span>
                  </div>
                  <div className="space-y-1">
                    <div>
                      &gt; agent: <span className="text-[#F59E0B]">{result.display_name}</span>
                    </div>
                    {/* SECURITY: accreditation number is intentionally NOT displayed
                        here. The visitor must read it from the email we just sent,
                        or scan the QR code on their access card. */}
                    <div>
                      &gt; accred: <span className="text-[#F59E0B]/60 tracking-widest">●●●● ●●●●</span>
                      <span className="ml-2 text-[#18C964]/50 text-[10px]">{t("terminal.accredHidden")}</span>
                    </div>
                    <div className="flex items-start gap-2 mt-3">
                      <Mail size={14} className="mt-0.5 shrink-0" />
                      <span className="text-[#18C964]/80">
                        {t("terminal.successInbox").replace("__EMAIL__", result.email)}
                      </span>
                    </div>
                  </div>
                  <div className="mt-5 border-t border-[#18C964]/30 pt-4">
                    <div className="text-[#18C964]/70 text-[11px] mb-3 leading-relaxed">
                      &gt; {t("terminal.successNext")}
                    </div>
                    <div className="flex items-center gap-3 flex-wrap">
                      <Button
                        asChild
                        className="rounded-md bg-[#18C964] hover:bg-[#18C964]/90 text-black font-mono font-semibold"
                        data-testid="terminal-go-vault"
                      >
                        <a href="/classified-vault">
                          {t("terminal.openVault")} →
                        </a>
                      </Button>
                      <button
                        onClick={onClose}
                        className="text-[#18C964]/60 hover:text-[#18C964] font-mono text-xs"
                        data-testid="terminal-close-button"
                      >
                        {t("terminal.close")}
                      </button>
                    </div>
                    <div className="mt-4 text-[10px] text-[#18C964]/50 leading-relaxed">
                      {t("terminal.shortcutHint")}
                    </div>
                  </div>
                </div>
              )}

              {/* ERROR phase */}
              {phase === "error" && (
                <div data-testid="terminal-phase-error">
                  <div className="flex items-center gap-2 text-red-400">
                    <AlertTriangle size={16} /> TRANSMISSION FAILED
                  </div>
                  <div className="text-red-400/80 text-xs mt-2">{errorMsg}</div>
                  <div className="mt-4">
                    <Button
                      onClick={() => setPhase("form")}
                      className="rounded-md bg-[#18C964] hover:bg-[#18C964]/90 text-black font-mono font-semibold"
                    >
                      {t("terminal.retry")} →
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
