import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Lock, Unlock, Shield, ExternalLink, LogOut, RefreshCcw, AlertTriangle, Radio } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useI18n } from "@/i18n/I18nProvider";
import TopNav from "@/components/landing/TopNav";
import Footer from "@/components/landing/Footer";
import CombinationDial from "@/components/landing/vault/CombinationDial";
import VaultActivityFeed from "@/components/landing/vault/VaultActivityFeed";

const API = process.env.REACT_APP_BACKEND_URL;
const SESSION_KEY = "deepotus_access_session";
const POLL_MS = 8000;

/**
 * ClassifiedVault — the full-page REAL vault, gated by a Level 2 accreditation.
 *
 * Flow:
 *   1. Check localStorage for an existing session_token
 *   2. If none, show a gate UI (accreditation input + code from query string)
 *   3. After verify: render the real vault — full-page immersive, shows the
 *      LIVE DEX-fed vault activity (same backend data, but presented as the
 *      "real vault" with larger live feed + price + volumes)
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
    const code = (raw || codeInput || "").trim();
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
  // GATE VIEW
  // =====================================================================
  if (!session?.session_token) {
    return (
      <div className="min-h-screen bg-black">
        <TopNav />
        <main className="relative min-h-[80vh] flex items-center justify-center px-4 py-16 overflow-hidden">
          {/* Bunker backdrop */}
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(245,158,11,0.08),transparent_60%)]" />
            <div
              aria-hidden
              className="absolute inset-0 opacity-[0.06]"
              style={{
                backgroundImage:
                  "repeating-linear-gradient(0deg, rgba(255,255,255,0.3) 0 1px, transparent 1px 4px)",
              }}
            />
          </div>

          <motion.div
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.45 }}
            className="relative w-full max-w-lg rounded-2xl border border-[#F59E0B]/40 bg-[#0A0A0A]/90 backdrop-blur p-8 shadow-[0_0_40px_rgba(245,158,11,0.18)]"
            data-testid="classified-gate"
          >
            <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.3em] text-[#F59E0B]">
              <Lock size={14} /> {t("classifiedVault.gateKicker")}
            </div>
            <h1
              className="mt-4 font-display text-3xl md:text-4xl font-semibold leading-tight text-white"
              data-testid="classified-gate-title"
            >
              {t("classifiedVault.gateTitle")}
            </h1>
            <p className="mt-3 text-sm md:text-base text-white/70 leading-relaxed">
              {t("classifiedVault.gateSubtitle")}
            </p>

            <form
              className="mt-6"
              onSubmit={(e) => {
                e.preventDefault();
                verifyCode();
              }}
            >
              <label
                htmlFor="accred-input"
                className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/60 block mb-2"
              >
                {t("classifiedVault.gateLabel")}
              </label>
              <Input
                id="accred-input"
                value={codeInput}
                onChange={(e) => setCodeInput(e.target.value.toUpperCase())}
                placeholder="DS-02-XXXX-XXXX-XX"
                className="font-mono bg-black border-[#F59E0B]/40 text-[#F59E0B] tracking-widest placeholder:text-white/20 focus-visible:ring-[#F59E0B]/60"
                data-testid="classified-accred-input"
                autoFocus
              />
              {gateError && (
                <div className="mt-2 flex items-center gap-2 text-red-400 text-xs">
                  <AlertTriangle size={12} />
                  {gateError}
                </div>
              )}
              <Button
                type="submit"
                disabled={verifying}
                className="mt-5 w-full rounded-md bg-[#F59E0B] hover:bg-[#F59E0B]/90 text-black font-mono font-semibold"
                data-testid="classified-verify-btn"
              >
                {verifying ? t("classifiedVault.verifying") : t("classifiedVault.verify")}
              </Button>
            </form>

            <div className="mt-6 pt-5 border-t border-white/10">
              <p className="text-xs text-white/50 leading-relaxed">
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
          </motion.div>
        </main>
        <Footer />
      </div>
    );
  }

  // =====================================================================
  // AUTHED VIEW — THE REAL VAULT
  // =====================================================================
  const stage = vault?.stage || "LOCKED";
  const locked = vault?.digits_locked ?? 0;
  const combo = vault?.current_combination || [0, 0, 0, 0, 0, 0];
  const dexMode = vault?.dex_mode || "off";
  const dexLabel = vault?.dex_label || null;

  return (
    <div className="min-h-screen bg-[#060606] text-white">
      <TopNav />
      <main className="relative">
        {/* Authed header strip */}
        <div className="sticky top-14 z-30 border-b border-[#F59E0B]/20 bg-black/80 backdrop-blur" data-testid="classified-header">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-11 flex items-center gap-3">
            <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.25em] text-[#F59E0B]">
              <Shield size={12} /> CLEARED · {session.display_name}
            </div>
            <div className="ml-auto flex items-center gap-2 font-mono text-[10px] text-white/50">
              <span className="hidden md:inline">{t("classifiedVault.sessionUntil")}:</span>
              <span>{session.expires_at ? new Date(session.expires_at).toLocaleString() : "—"}</span>
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
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 md:pt-20 pb-10">
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

        {/* Full vault dials + live feed */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Dials panel — larger for the real vault */}
            <div className="lg:col-span-7">
              <div
                className="relative rounded-2xl border border-[#F59E0B]/30 bg-[#0A0A0A] p-6 md:p-8 shadow-[0_0_36px_rgba(245,158,11,0.12)]"
                data-testid="classified-vault-panel"
              >
                <div className="flex items-center justify-between mb-5">
                  <div className="font-display text-lg md:text-xl font-semibold tracking-tight">
                    {t("classifiedVault.liveCombination")}
                  </div>
                  <AnimatePresence>
                    <motion.span
                      key={stage}
                      initial={{ opacity: 0, y: -4 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      className={`font-mono text-[10px] uppercase tracking-[0.25em] ${
                        stage === "DECLASSIFIED"
                          ? "text-[#18C964]"
                          : stage === "UNLOCKING" || stage === "CRACKING"
                          ? "text-[#F59E0B]"
                          : "text-red-400"
                      }`}
                    >
                      {t(`vault.stages.${stage}`) || stage}
                    </motion.span>
                  </AnimatePresence>
                </div>
                <div className="flex items-center justify-center gap-3 md:gap-5 py-6">
                  {combo.map((digit, i) => (
                    <CombinationDial
                      key={i}
                      index={i}
                      value={digit}
                      locked={i < locked}
                      stage={stage}
                      size="default"
                    />
                  ))}
                </div>
                <div className="flex items-center justify-center gap-3 md:gap-5 mt-1">
                  {combo.map((_, i) => (
                    <div
                      key={i}
                      className="w-14 md:w-16 text-center font-mono text-[9px] uppercase tracking-wider text-white/40"
                    >
                      Δ{i + 1}
                    </div>
                  ))}
                </div>

                {/* Metrics grid */}
                <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
                  <div className="rounded-md border border-white/10 bg-black/40 p-3">
                    <div className="text-white/40 text-[10px] uppercase">{t("classifiedVault.dials")}</div>
                    <div className="text-white text-lg mt-0.5">
                      {locked}/{combo.length}
                    </div>
                  </div>
                  <div className="rounded-md border border-white/10 bg-black/40 p-3">
                    <div className="text-white/40 text-[10px] uppercase">{t("classifiedVault.progress")}</div>
                    <div className="text-white text-lg mt-0.5">
                      {Math.round(vault?.progress_pct ?? 0)}%
                    </div>
                  </div>
                  <div className="rounded-md border border-white/10 bg-black/40 p-3">
                    <div className="text-white/40 text-[10px] uppercase">{t("classifiedVault.tokens")}</div>
                    <div className="text-white text-lg mt-0.5">
                      {(vault?.tokens_sold ?? 0).toLocaleString()}
                    </div>
                  </div>
                  <div className="rounded-md border border-white/10 bg-black/40 p-3">
                    <div className="text-white/40 text-[10px] uppercase">{t("classifiedVault.mode")}</div>
                    <div className="text-white text-lg mt-0.5 uppercase">
                      {dexMode}
                    </div>
                  </div>
                </div>

                <div className="mt-6 p-3 rounded-md border border-[#F59E0B]/20 bg-[#F59E0B]/5 text-xs text-white/70 leading-relaxed">
                  {t("classifiedVault.disclaimer")}
                </div>
              </div>
            </div>

            {/* Activity feed — taller variant */}
            <div className="lg:col-span-5">
              <div className="rounded-2xl border border-white/10 bg-[#0A0A0A] p-5 md:p-6">
                <div className="flex items-center gap-2 mb-3">
                  <Radio size={14} className="text-[#2DD4BF] animate-pulse" />
                  <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-white/70">
                    {t("classifiedVault.feedTitle")}
                  </div>
                </div>
                <VaultActivityFeed events={vault?.recent_events || []} />
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
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}
