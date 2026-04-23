import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Send, CheckCircle2, AlertTriangle, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useI18n } from "@/i18n/I18nProvider";

const API = process.env.REACT_APP_BACKEND_URL;

/**
 * TerminalPopup — a CRT-style terminal modal used as the GATE after the
 * fake vault cracks. It denies direct access, taunts the visitor ("nice try,
 * you only have LEVEL 1 clearance") and lets them request a Level 2 access card.
 *
 * Phases:
 *   "denied"    — typing-animated refusal + CTA to request clearance
 *   "form"      — email + optional display name
 *   "sending"   — loading animation with status lines
 *   "success"   — accreditation summary + "check your inbox"
 *   "error"     — technical failure (rare)
 */
export default function TerminalPopup({ open, onClose }) {
  const { t, lang } = useI18n();
  const [phase, setPhase] = useState("denied");
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [typedLines, setTypedLines] = useState([]);
  const [showCursor, setShowCursor] = useState(true);

  // Typing animation for the "denied" intro
  const deniedLines = useMemo(
    () => t("terminal.deniedLines") || [],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [lang]
  );

  useEffect(() => {
    if (!open) return;
    setPhase("denied");
    setTypedLines([]);
    setEmail("");
    setDisplayName("");
    setResult(null);
    setErrorMsg(null);
  }, [open]);

  // Animate typing of denied lines, one per ~700ms
  useEffect(() => {
    if (!open || phase !== "denied") return;
    let i = 0;
    setTypedLines([]);
    const id = setInterval(() => {
      if (i >= deniedLines.length) {
        clearInterval(id);
        return;
      }
      setTypedLines((prev) => [...prev, deniedLines[i]]);
      i += 1;
    }, 600);
    return () => clearInterval(id);
  }, [open, phase, deniedLines]);

  // Blinking cursor
  useEffect(() => {
    if (!open) return;
    const id = setInterval(() => setShowCursor((c) => !c), 520);
    return () => clearInterval(id);
  }, [open]);

  async function submitRequest(e) {
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
    } catch (err) {
      setErrorMsg(String(err?.message || err));
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
                    <div key={i} className="whitespace-pre-wrap mb-1">
                      {line}
                    </div>
                  ))}
                  {typedLines.length < deniedLines.length && (
                    <span className="inline-block w-2 h-4 bg-[#18C964] align-middle ml-1" />
                  )}
                  {typedLines.length >= deniedLines.length && (
                    <div className="mt-6 flex items-center gap-3 flex-wrap">
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
                  )}
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
                    <div>
                      &gt; accred: <span className="text-[#F59E0B] tracking-widest">{result.accreditation_number}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <Mail size={14} />
                      <span className="text-[#18C964]/80">
                        {t("terminal.successInbox").replace("__EMAIL__", result.email)}
                      </span>
                    </div>
                  </div>
                  <div className="mt-5 border-t border-[#18C964]/30 pt-4">
                    <div className="text-[#18C964]/70 text-[11px] mb-2">
                      &gt; {t("terminal.successNext")}
                    </div>
                    <div className="flex items-center gap-3 flex-wrap">
                      <Button
                        asChild
                        className="rounded-md bg-[#18C964] hover:bg-[#18C964]/90 text-black font-mono font-semibold"
                        data-testid="terminal-go-vault"
                      >
                        <a href={`/classified-vault?code=${result.accreditation_number}`}>
                          {t("terminal.openVault")} →
                        </a>
                      </Button>
                      <button
                        onClick={onClose}
                        className="text-[#18C964]/60 hover:text-[#18C964] font-mono text-xs"
                      >
                        {t("terminal.close")}
                      </button>
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
