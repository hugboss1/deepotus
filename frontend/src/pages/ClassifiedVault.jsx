import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Lock,
  Unlock,
  Shield,
  ExternalLink,
  LogOut,
  Radio,
  AlertTriangle,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useI18n } from "@/i18n/I18nProvider";
import TopNav from "@/components/landing/TopNav";
import Footer from "@/components/landing/Footer";
import VaultChassis from "@/components/landing/vault/VaultChassis";
import VaultActivityFeed from "@/components/landing/vault/VaultActivityFeed";

const API = process.env.REACT_APP_BACKEND_URL;
const SESSION_KEY = "deepotus_access_session";
const POLL_MS = 8000;

/**
 * ClassifiedVault — the full-page REAL vault, gated by a Level 2 accreditation.
 *
 * - Gate view: AI-generated BLACK-OPS DOOR with keypad illustration.
 *   On desktop the code input is overlaid INSIDE the LED display zone of the
 *   door; on mobile the door is a hero and the input sits below it.
 * - Authed view: REUSES the VaultChassis mockup (same anchoring as the home
 *   fake vault) so the real vault feels continuous with the narrative.
 */
export default function ClassifiedVault() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const [params] = useSearchParams();

  const [session, setSession] = useState(() => {
    try {
      const raw = localStorage.getItem(SESSION_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });
  const [codeInput, setCodeInput] = useState(() => params.get("code") || "");
  const [verifying, setVerifying] = useState(false);
  const [gateError, setGateError] = useState(null);
  const [vault, setVault] = useState(null);
  const aliveRef = useRef(true);

  // Auto-verify if ?code=... in URL and no session yet
  useEffect(() => {
    const code = params.get("code");
    if (code && !session) {
      verifyCode(code.trim());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Validate stored session on mount
  useEffect(() => {
    if (!session?.session_token) return;
    (async () => {
      try {
        const res = await fetch(`${API}/api/access-card/status`, {
          headers: { "X-Session-Token": session.session_token },
        });
        const data = await res.json();
        if (!data.ok) {
          localStorage.removeItem(SESSION_KEY);
          setSession(null);
        }
      } catch {
        /* ignore */
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Poll vault state when authed
  useEffect(() => {
    if (!session?.session_token) return;
    aliveRef.current = true;
    const fetchState = async () => {
      try {
        const res = await fetch(`${API}/api/vault/state`);
        if (!res.ok) return;
        const data = await res.json();
        if (!aliveRef.current) return;
        setVault(data);
      } catch {
        /* ignore */
      }
    };
    fetchState();
    const id = setInterval(fetchState, POLL_MS);
    return () => {
      aliveRef.current = false;
      clearInterval(id);
    };
  }, [session]);

  async function verifyCode(raw) {
    const code = (raw || codeInput || "").trim().toUpperCase();
    if (!code) return;
    setVerifying(true);
    setGateError(null);
    try {
      const res = await fetch(`${API}/api/access-card/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accreditation_number: code }),
      });
      const data = await res.json();
      if (!data.ok) {
        setGateError(data.message || t("classifiedVault.gateError"));
        setVerifying(false);
        return;
      }
      localStorage.setItem(SESSION_KEY, JSON.stringify(data));
      setSession(data);
      setVerifying(false);
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

  // =====================================================================
  // GATE VIEW — the cinematic DOOR with keypad illustration
  // =====================================================================
  if (!session?.session_token) {
    const statusColor = gateError ? "#EF4444" : verifying ? "#F59E0B" : "#22D3EE";
    const statusLabel = gateError
      ? "ERROR"
      : verifying
      ? "VERIFYING"
      : t("classifiedVault.gateIdle");

    return (
      <div className="min-h-screen bg-black">
        <TopNav />
        <main className="relative px-4 py-10 md:py-16">
          {/* Header */}
          <div className="max-w-6xl mx-auto mb-8 md:mb-12">
            <div className="inline-flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.3em] text-[#F59E0B]">
              <Lock size={14} /> {t("classifiedVault.gateKicker")}
            </div>
            <h1
              className="mt-3 font-display text-3xl md:text-5xl font-semibold leading-tight text-white"
              data-testid="classified-gate-title"
            >
              {t("classifiedVault.gateTitle")}
            </h1>
            <p className="mt-3 text-sm md:text-base text-white/70 max-w-2xl">
              {t("classifiedVault.gateSubtitle")}
            </p>
          </div>

          {/* DOOR CHASSIS with overlay input (desktop) */}
          <div className="max-w-6xl mx-auto">
            <div
              className="relative w-full overflow-hidden rounded-2xl border border-border bg-black shadow-[0_0_40px_rgba(34,211,238,0.12)] aspect-[16/9]"
              data-testid="classified-door-chassis"
            >
              <img
                src="/door_keypad.png"
                alt="Deep State reinforced door with digicode keypad"
                className="absolute inset-0 w-full h-full object-cover object-center select-none pointer-events-none"
                draggable={false}
              />

              {/* Ambient pulse behind the LED display (breathes) */}
              <motion.div
                aria-hidden
                className="absolute pointer-events-none"
                style={{
                  left: "42%",
                  top: "38%",
                  width: "17%",
                  height: "13%",
                  background: `radial-gradient(ellipse at center, ${statusColor}55, transparent 70%)`,
                  filter: "blur(6px)",
                }}
                animate={{ opacity: [0.45, 0.9, 0.45] }}
                transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
              />

              {/* LED DISPLAY overlay — desktop only (input sits INSIDE the door) */}
              <form
                className="hidden md:flex absolute items-center justify-center"
                onSubmit={(e) => {
                  e.preventDefault();
                  verifyCode();
                }}
                style={{
                  left: "42%",
                  top: "40%",
                  width: "17%",
                  height: "9%",
                }}
              >
                <input
                  value={codeInput}
                  onChange={(e) => setCodeInput(e.target.value.toUpperCase())}
                  placeholder="DS-02-••••-••••-••"
                  className="w-full h-full bg-transparent border-0 outline-none text-center font-mono tracking-[0.1em] text-[clamp(9px,0.95vw,14px)] uppercase"
                  style={{
                    color: statusColor,
                    textShadow: `0 0 8px ${statusColor}`,
                    caretColor: statusColor,
                  }}
                  aria-label="Accreditation number"
                  data-testid="classified-accred-input-desktop"
                  autoFocus
                  autoComplete="off"
                  spellCheck={false}
                />
              </form>

              {/* Status pulse label — only visible during verify / error overrides the baked-in IDLE label */}
              {(verifying || gateError) && (
                <div
                  className="hidden md:block absolute font-mono uppercase tracking-[0.2em] text-[clamp(7px,0.55vw,10px)] px-1.5 py-0.5 rounded"
                  style={{
                    left: "59.5%",
                    top: "39.5%",
                    color: statusColor,
                    background: "rgba(0,0,0,0.85)",
                    textShadow: `0 0 6px ${statusColor}`,
                  }}
                >
                  {statusLabel}
                </div>
              )}

              {/* Corner tags */}
              <div className="absolute top-3 left-3 flex items-center gap-2 px-2.5 py-1 rounded-md bg-black/60 border border-white/10 backdrop-blur-sm">
                <span
                  className="w-1.5 h-1.5 rounded-full animate-pulse"
                  style={{ background: statusColor }}
                />
                <span
                  className="font-mono text-[9px] md:text-[10px] uppercase tracking-[0.25em]"
                  style={{ color: statusColor }}
                >
                  {t("classifiedVault.gateChannel")}
                </span>
              </div>
              <div className="absolute bottom-3 right-3 px-2.5 py-1 rounded-md bg-black/60 border border-white/10 backdrop-blur-sm">
                <span className="font-mono text-[9px] md:text-[10px] uppercase tracking-[0.25em] text-[#F59E0B]">
                  {t("classifiedVault.gateLevel")}
                </span>
              </div>

              {/* Declassified flash on success (rare — the green victory pulse) */}
              <AnimatePresence>
                {verifying && (
                  <motion.div
                    key="verify-pulse"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: [0.0, 0.18, 0.0] }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 1.6, repeat: Infinity }}
                    className="absolute inset-0 pointer-events-none"
                    style={{ background: "#F59E0B", mixBlendMode: "screen" }}
                  />
                )}
              </AnimatePresence>
            </div>

            {/* MOBILE INPUT BELOW DOOR (hidden on desktop) */}
            <div className="md:hidden mt-4">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  verifyCode();
                }}
                className="rounded-xl border border-[#F59E0B]/30 bg-black/60 p-4"
              >
                <label
                  htmlFor="accred-input-mobile"
                  className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/60 block mb-2"
                >
                  {t("classifiedVault.gateLabel")}
                </label>
                <Input
                  id="accred-input-mobile"
                  value={codeInput}
                  onChange={(e) => setCodeInput(e.target.value.toUpperCase())}
                  placeholder="DS-02-XXXX-XXXX-XX"
                  className="font-mono bg-black border-[#F59E0B]/40 text-[#F59E0B] tracking-widest placeholder:text-white/20 focus-visible:ring-[#F59E0B]/60"
                  data-testid="classified-accred-input-mobile"
                  autoFocus
                />
                {gateError && (
                  <div className="mt-2 flex items-center gap-2 text-red-400 text-xs">
                    <AlertTriangle size={12} /> {gateError}
                  </div>
                )}
                <Button
                  type="submit"
                  disabled={verifying}
                  className="mt-4 w-full rounded-md bg-[#F59E0B] hover:bg-[#F59E0B]/90 text-black font-mono font-semibold"
                  data-testid="classified-verify-btn-mobile"
                >
                  {verifying ? t("classifiedVault.verifying") : t("classifiedVault.verify")}
                </Button>
              </form>
            </div>

            {/* DESKTOP ACTION BAR BELOW DOOR */}
            <div className="hidden md:flex mt-5 items-center justify-between gap-3 flex-wrap">
              <div className="flex items-center gap-3 flex-wrap">
                {gateError && (
                  <div className="flex items-center gap-2 text-red-400 text-xs font-mono">
                    <AlertTriangle size={12} />
                    {gateError}
                  </div>
                )}
                <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/40">
                  {t("classifiedVault.gateHintShort")}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  disabled={verifying}
                  onClick={() => verifyCode()}
                  className="rounded-md bg-[#F59E0B] hover:bg-[#F59E0B]/90 text-black font-mono font-semibold"
                  data-testid="classified-verify-btn-desktop"
                >
                  {verifying ? t("classifiedVault.verifying") : t("classifiedVault.verify")} →
                </Button>
              </div>
            </div>

            {/* Secondary info */}
            <div className="mt-6 rounded-xl border border-white/10 bg-white/[0.02] p-4">
              <p className="text-xs md:text-sm text-white/60 leading-relaxed">
                {t("classifiedVault.gateHint")}
              </p>
              <a
                href="/#vault"
                className="mt-2 inline-flex items-center gap-1 text-[11px] font-mono text-white/40 hover:text-white/80"
                data-testid="classified-back-link"
              >
                ← {t("classifiedVault.gateBack")}
              </a>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  // =====================================================================
  // AUTHED VIEW — THE REAL VAULT (reuses VaultChassis)
  // =====================================================================
  const stage = vault?.stage || "LOCKED";
  const locked = vault?.digits_locked ?? 0;
  const combo = vault?.current_combination || [0, 0, 0, 0, 0, 0];
  const dexMode = vault?.dex_mode || "off";
  const dexLabel = vault?.dex_label || null;
  const microTicksTotal = vault?.micro_ticks_total ?? 0;
  const stageLabel = (t(`vault.stages.${stage}`) || stage).toString();
  const isDeclassified = stage === "DECLASSIFIED";

  return (
    <div className="min-h-screen bg-[#060606] text-white">
      <TopNav />
      <main className="relative">
        {/* Authed header strip */}
        <div
          className="sticky top-14 z-30 border-b border-[#F59E0B]/20 bg-black/80 backdrop-blur"
          data-testid="classified-header"
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-11 flex items-center gap-3">
            <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.25em] text-[#F59E0B]">
              <Shield size={12} /> CLEARED · {session.display_name}
            </div>
            <div className="ml-auto flex items-center gap-2 font-mono text-[10px] text-white/50">
              <span className="hidden md:inline">
                {t("classifiedVault.sessionUntil")}:
              </span>
              <span>
                {session.expires_at
                  ? new Date(session.expires_at).toLocaleString()
                  : "—"}
              </span>
              <button
                onClick={logout}
                className="ml-2 inline-flex items-center gap-1 text-white/60 hover:text-white transition-colors"
                data-testid="classified-logout"
              >
                <LogOut size={12} /> {t("classifiedVault.logout")}
              </button>
            </div>
          </div>
        </div>

        {/* Hero */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 md:pt-16 pb-8">
          <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.3em] text-[#F59E0B]">
            <Unlock size={14} /> {t("classifiedVault.authedKicker")}
          </div>
          <h1
            className="mt-4 font-display text-4xl md:text-6xl font-semibold leading-[1.05] tracking-tight"
            data-testid="classified-authed-title"
          >
            {t("classifiedVault.authedTitle")}
          </h1>
          <p className="mt-4 text-lg text-white/75 max-w-2xl">
            {t("classifiedVault.authedSubtitle")}
          </p>

          {dexMode !== "off" && dexLabel && (
            <div
              className="mt-5 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#2DD4BF]/10 border border-[#2DD4BF]/30"
              data-testid="classified-dex-status"
            >
              <Radio size={12} className="text-[#2DD4BF] animate-pulse" />
              <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-[#2DD4BF]">
                LIVE DEX · {dexLabel}
              </span>
            </div>
          )}
        </section>

        {/* VAULT CHASSIS (same mockup as homepage) */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-10">
          <VaultChassis
            combo={combo}
            locked={locked}
            stage={stage}
            stageLabel={stageLabel}
            microTickVersion={microTicksTotal}
          />

          {/* DECLASSIFIED CTA — animated green button like the homepage.
              On the REAL vault the Agent is already Level 2, so we route
              directly to the /operation lore (GENCOIN reveal). */}
          <AnimatePresence>
            {isDeclassified && (
              <motion.div
                initial={{ opacity: 0, y: 12, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5 }}
                className="mt-6 p-5 rounded-2xl border border-[#18C964]/50 bg-[#18C964]/10 backdrop-blur relative overflow-hidden"
                data-testid="classified-declassified-cta"
              >
                {/* Ambient sparkle pulse */}
                <motion.div
                  aria-hidden
                  className="absolute inset-0 pointer-events-none"
                  style={{
                    background:
                      "radial-gradient(circle at 50% 50%, rgba(24,201,100,0.25), transparent 70%)",
                  }}
                  animate={{ opacity: [0.4, 0.9, 0.4] }}
                  transition={{ duration: 2.2, repeat: Infinity }}
                />
                <div className="relative flex flex-col md:flex-row md:items-center gap-4 md:justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Sparkles size={16} className="text-[#18C964]" />
                      <span className="font-mono text-[11px] uppercase tracking-[0.3em] text-[#18C964]">
                        {t("classifiedVault.declassified.kicker")}
                      </span>
                    </div>
                    <div className="font-display text-xl md:text-2xl font-semibold text-white">
                      {t("classifiedVault.declassified.title")}
                    </div>
                    <div className="text-sm text-white/75 mt-1 max-w-xl">
                      {t("classifiedVault.declassified.subtitle")}
                    </div>
                  </div>
                  <motion.div
                    initial={{ scale: 1 }}
                    animate={{ scale: [1, 1.04, 1] }}
                    transition={{ duration: 1.8, repeat: Infinity }}
                  >
                    <Button
                      asChild
                      size="lg"
                      className="rounded-[var(--btn-radius)] bg-[#18C964] hover:bg-[#18C964]/90 text-black font-semibold shadow-[0_0_30px_rgba(24,201,100,0.45)]"
                      data-testid="classified-declassified-cta-btn"
                    >
                      <a href="/operation">
                        {t("classifiedVault.declassified.cta")}
                        <ArrowRight size={16} className="ml-1.5" />
                      </a>
                    </Button>
                  </motion.div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </section>

        {/* Metrics + feed row */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Metrics panel */}
            <div className="lg:col-span-5">
              <div className="rounded-2xl border border-[#F59E0B]/20 bg-[#0A0A0A] p-5">
                <div className="grid grid-cols-2 gap-3 font-mono text-xs">
                  <div className="rounded-md border border-white/10 bg-black/40 p-3">
                    <div className="text-white/40 text-[10px] uppercase">
                      {t("classifiedVault.dials")}
                    </div>
                    <div className="text-white text-lg mt-0.5">
                      {locked}/{combo.length}
                    </div>
                  </div>
                  <div className="rounded-md border border-white/10 bg-black/40 p-3">
                    <div className="text-white/40 text-[10px] uppercase">
                      {t("classifiedVault.progress")}
                    </div>
                    <div className="text-white text-lg mt-0.5">
                      {Math.round(vault?.progress_pct ?? 0)}%
                    </div>
                  </div>
                  <div className="rounded-md border border-white/10 bg-black/40 p-3">
                    <div className="text-white/40 text-[10px] uppercase">
                      {t("classifiedVault.tokens")}
                    </div>
                    <div className="text-white text-lg mt-0.5">
                      {(vault?.tokens_sold ?? 0).toLocaleString()}
                    </div>
                  </div>
                  <div className="rounded-md border border-white/10 bg-black/40 p-3">
                    <div className="text-white/40 text-[10px] uppercase">
                      {t("classifiedVault.microTicks")}
                    </div>
                    <div className="text-[#F59E0B] text-lg mt-0.5">
                      {microTicksTotal.toLocaleString()}
                    </div>
                  </div>
                  <div className="rounded-md border border-white/10 bg-black/40 p-3 col-span-2">
                    <div className="text-white/40 text-[10px] uppercase">
                      {t("classifiedVault.treasury")}
                    </div>
                    <div className="flex items-baseline gap-2 mt-0.5">
                      <span className="text-[#18C964] text-lg">
                        €{(vault?.treasury_eur_value ?? 0).toLocaleString(undefined, {
                          maximumFractionDigits: 0,
                        })}
                      </span>
                      <span className="text-white/40 text-[10px] uppercase">
                        / €??? · {Math.round(vault?.treasury_progress_pct ?? 0)}%
                      </span>
                    </div>
                    {/* Mini progress bar */}
                    <div className="h-1.5 w-full rounded-full bg-white/10 mt-2 overflow-hidden">
                      <div
                        className="h-full bg-[#18C964] transition-all duration-500"
                        style={{
                          width: `${Math.min(100, Math.round(vault?.treasury_progress_pct ?? 0))}%`,
                        }}
                      />
                    </div>
                  </div>
                  <div className="rounded-md border border-white/10 bg-black/40 p-3 col-span-2">
                    <div className="text-white/40 text-[10px] uppercase">
                      {t("classifiedVault.mode")}
                    </div>
                    <div className="text-white text-lg mt-0.5 uppercase">
                      {dexMode}
                    </div>
                  </div>
                </div>

                <div className="mt-4 p-3 rounded-md border border-[#F59E0B]/20 bg-[#F59E0B]/5 text-xs text-white/70 leading-relaxed">
                  {t("classifiedVault.disclaimer")}
                </div>
              </div>

              <div className="mt-5 rounded-2xl border border-white/10 bg-[#0A0A0A] p-5">
                <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-white/60">
                  {t("classifiedVault.externalTitle")}
                </div>
                <a
                  href="https://dexscreener.com/solana"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 inline-flex items-center gap-2 text-[#2DD4BF] hover:text-white transition-colors text-sm font-mono"
                  data-testid="classified-dexscreener-link"
                >
                  dexscreener.com/solana <ExternalLink size={12} />
                </a>
              </div>
            </div>

            {/* Activity feed */}
            <div className="lg:col-span-7">
              <div className="rounded-2xl border border-white/10 bg-[#0A0A0A] p-5 md:p-6">
                <div className="flex items-center gap-2 mb-3">
                  <Radio size={14} className="text-[#2DD4BF] animate-pulse" />
                  <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-white/70">
                    {t("classifiedVault.feedTitle")}
                  </div>
                </div>
                <VaultActivityFeed events={vault?.recent_events || []} />
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
