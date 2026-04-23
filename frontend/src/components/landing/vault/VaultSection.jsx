import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Lock, Unlock, Shield, AlertTriangle, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n/I18nProvider";
import CombinationDial from "./CombinationDial";
import VaultActivityFeed from "./VaultActivityFeed";
import VaultChassis from "./VaultChassis";

const API = process.env.REACT_APP_BACKEND_URL;
const POLL_MS = 10000;

const STAGE_META = {
  LOCKED: { color: "text-red-400", ring: "ring-red-500/30", emoji: "🔒" },
  CRACKING: { color: "text-[#F59E0B]", ring: "ring-[#F59E0B]/40", emoji: "⚙️" },
  UNLOCKING: { color: "text-[#F59E0B]", ring: "ring-[#F59E0B]/60", emoji: "🔓" },
  DECLASSIFIED: {
    color: "text-[#18C964]",
    ring: "ring-[#18C964]/70",
    emoji: "💥",
  },
};

export default function VaultSection() {
  const { t } = useI18n();
  const [state, setState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const aliveRef = useRef(true);

  const fetchState = async () => {
    try {
      const res = await fetch(`${API}/api/vault/state`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (!aliveRef.current) return;
      setState(data);
      setError(null);
    } catch (e) {
      if (!aliveRef.current) return;
      setError(e.message || "fetch failed");
    } finally {
      if (aliveRef.current) setLoading(false);
    }
  };

  useEffect(() => {
    aliveRef.current = true;
    fetchState();
    const id = setInterval(fetchState, POLL_MS);
    return () => {
      aliveRef.current = false;
      clearInterval(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stage = state?.stage || "LOCKED";
  const meta = STAGE_META[stage] || STAGE_META.LOCKED;
  const locked = state?.digits_locked ?? 0;
  const total = state?.num_digits ?? 6;
  const combo = state?.current_combination || [0, 0, 0, 0, 0, 0];
  const progressPct = Math.round(state?.progress_pct ?? 0);
  const redactedBuckets = Math.min(10, Math.floor((progressPct / 100) * 10));
  const dexMode = state?.dex_mode || "off";
  const dexLabel = state?.dex_label || null;

  const stageLabel = useMemo(() => {
    return t(`vault.stages.${stage}`) || stage;
  }, [stage, t]);

  return (
    <section
      id="vault"
      data-testid="vault-section"
      className="py-16 sm:py-20 lg:py-28 border-t border-border relative overflow-hidden"
    >
      {/* Classified backdrop */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.06]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(245,158,11,0.35),transparent_50%),radial-gradient(circle_at_70%_80%,rgba(24,201,100,0.35),transparent_50%)]" />
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        {/* Header */}
        <div className="max-w-3xl">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.5 }}
          >
            <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
              {t("vault.kicker")}
            </div>
            <h2
              className="mt-3 font-display text-3xl md:text-4xl lg:text-5xl font-semibold leading-tight"
              data-testid="vault-title"
            >
              {t("vault.title")}
            </h2>
            <div className="mt-3 inline-flex items-center gap-2 font-mono text-xs uppercase tracking-[0.3em] text-[#F59E0B]">
              <Shield size={14} /> PROTOCOL ΔΣ
              {dexMode !== "off" && dexLabel && (
                <span
                  className="ml-2 inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-[#2DD4BF]/10 border border-[#2DD4BF]/30 text-[#2DD4BF] text-[10px]"
                  data-testid="vault-dex-status"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-[#2DD4BF] animate-pulse" />
                  LIVE · {dexLabel}
                </span>
              )}
            </div>
            <p className="mt-5 text-lg text-foreground/85">{t("vault.lead")}</p>
          </motion.div>
        </div>

        {/* CHASSIS ROW (desktop-first) */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6, delay: 0.05 }}
          className="mt-10"
        >
          {/* Desktop: AI-rendered vault image with dials overlaid */}
          <div className="hidden md:block">
            <VaultChassis
              combo={combo}
              locked={locked}
              stage={stage}
              stageLabel={stageLabel}
            />
          </div>

          {/* Mobile: image on top as banner + dials below in a regular row */}
          <div className="md:hidden">
            <div
              className="relative w-full overflow-hidden rounded-xl border border-border bg-black"
              style={{ aspectRatio: "16 / 9" }}
            >
              <img
                src="/vault_frame.png"
                alt="PROTOCOL ΔΣ vault"
                className="absolute inset-0 w-full h-full object-cover"
                draggable={false}
              />
              <div className="absolute top-3 left-3 px-2 py-0.5 rounded-md bg-black/60 border border-white/10">
                <span
                  className={`font-mono text-[9px] uppercase tracking-[0.25em] ${meta.color}`}
                >
                  {stageLabel}
                </span>
              </div>
            </div>
            <div className="mt-4 flex items-center justify-center gap-2">
              {combo.map((digit, i) => (
                <CombinationDial
                  key={i}
                  index={i}
                  value={digit}
                  locked={i < locked}
                  stage={stage}
                  size="sm"
                  showLabel={false}
                />
              ))}
            </div>
          </div>
        </motion.div>

        {/* DATA ROW: description + status + feed */}
        <div className="mt-10 grid grid-cols-1 lg:grid-cols-12 gap-10">
          {/* Description + status */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.5 }}
            className="lg:col-span-5"
          >
            <p className="text-foreground/80 leading-relaxed text-sm">
              {t("vault.body")}
            </p>

            <div
              className={`mt-5 inline-flex items-center gap-3 px-4 py-2 rounded-lg border border-border bg-card/60 backdrop-blur ring-2 ${meta.ring}`}
              data-testid="vault-status-badge"
            >
              <span className="text-base">{meta.emoji}</span>
              <span className={`font-mono text-xs uppercase tracking-[0.25em] ${meta.color}`}>
                {stageLabel}
              </span>
              <span className="font-mono text-[10px] text-muted-foreground">
                {locked}/{total} {t("vault.digitsLocked")}
              </span>
            </div>

            <div className="mt-5">
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                  {t("vault.progressLabel")}
                </span>
                <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                  ██░░ REDACTED
                </span>
              </div>
              <div className="h-3 w-full rounded-full bg-muted overflow-hidden relative">
                <div className="flex h-full">
                  {Array.from({ length: 10 }).map((_, i) => (
                    <div
                      key={i}
                      className={`flex-1 mx-px rounded-sm transition-colors duration-300 ${
                        i < redactedBuckets
                          ? stage === "DECLASSIFIED"
                            ? "bg-[#18C964]"
                            : stage === "UNLOCKING" || stage === "CRACKING"
                            ? "bg-[#F59E0B]"
                            : "bg-red-500/80"
                          : "bg-transparent"
                      }`}
                    />
                  ))}
                </div>
              </div>
              <p className="mt-2 text-xs text-muted-foreground font-mono">
                {t("vault.goalHidden")}
              </p>
            </div>

            <div className="mt-4 flex items-center gap-3 text-xs font-mono">
              <span className="text-muted-foreground uppercase tracking-wider">
                {t("vault.tokensMoved")}:
              </span>
              <span className="text-foreground font-semibold">
                {(state?.tokens_sold ?? 0).toLocaleString()} $DEEPOTUS
              </span>
              <span className="text-muted-foreground">/ ??? ??? $DEEPOTUS</span>
            </div>

            <div className="mt-6 flex items-start gap-3 p-3 rounded-md border border-border bg-muted/30">
              <AlertTriangle size={16} className="text-[#F59E0B] flex-none mt-0.5" />
              <p className="text-xs text-foreground/75 leading-relaxed">
                {t("vault.prophetWarning")}
              </p>
            </div>
          </motion.div>

          {/* Activity feed */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.5, delay: 0.08 }}
            className="lg:col-span-7"
          >
            <VaultActivityFeed events={state?.recent_events || []} />

            {/* DECLASSIFIED cta */}
            <AnimatePresence>
              {stage === "DECLASSIFIED" && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="mt-5 p-4 rounded-xl border border-[#18C964]/40 bg-[#18C964]/10"
                  data-testid="vault-declassified-cta"
                >
                  <div className="flex flex-col md:flex-row md:items-center gap-3 md:justify-between">
                    <div>
                      <div className="font-display font-semibold text-[#18C964]">
                        {t("vault.declassified.title")}
                      </div>
                      <div className="text-xs text-foreground/80 mt-1">
                        {t("vault.declassified.subtitle")}
                      </div>
                    </div>
                    <Button
                      asChild
                      size="sm"
                      className="rounded-[var(--btn-radius)] bg-[#18C964] hover:bg-[#18C964]/90 text-black"
                      data-testid="vault-open-operation-cta"
                    >
                      <a href="/operation">
                        {t("vault.declassified.cta")} <ArrowRight size={14} className="ml-1" />
                      </a>
                    </Button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {error && (
              <div className="mt-4 text-xs text-red-400 font-mono">
                transmission error — {error}
              </div>
            )}
            {loading && !state && (
              <div className="mt-4 text-xs text-muted-foreground font-mono">
                {t("vault.loading")}
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </section>
  );
}
