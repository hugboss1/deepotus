import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Unlock,
  Shield,
  ExternalLink,
  LogOut,
  Radio,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n/I18nProvider";
import {
  FADE_UP_SCALE_INITIAL,
  FADE_UP_SCALE_ANIMATE,
  FADE_UP_SCALE_EXIT,
  FADE_TRANSITION_DEFAULT,
  HALO_PULSE_ANIMATE,
  HALO_PULSE_TRANSITION,
  CTA_BREATHE_INITIAL,
  CTA_BREATHE_ANIMATE,
  CTA_BREATHE_TRANSITION,
} from "@/lib/motionVariants";
import TopNav from "@/components/landing/TopNav";
import Footer from "@/components/landing/Footer";
import VaultChassis from "@/components/landing/vault/VaultChassis";
import VaultActivityFeed from "@/components/landing/vault/VaultActivityFeed";

/**
 * AuthedVaultView — the REAL vault that an Agent unlocks after passing the
 * gate. Reuses the home `VaultChassis` mockup so the experience feels
 * continuous with the public-facing narrative.
 *
 * Pure presentational: receives session + vault state + logout from the
 * orchestrator hook.
 */

// eslint-disable-next-line
export function AuthedVaultView({ session, vault, logout }: any) {
  const { t } = useI18n();

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

        {/* VAULT CHASSIS */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-10">
          <VaultChassis
            combo={combo}
            locked={locked}
            stage={stage}
            stageLabel={stageLabel}
            microTickVersion={microTicksTotal}
          />

          <AnimatePresence>
            {isDeclassified && (
              <motion.div
                initial={FADE_UP_SCALE_INITIAL}
                animate={FADE_UP_SCALE_ANIMATE}
                exit={FADE_UP_SCALE_EXIT}
                transition={FADE_TRANSITION_DEFAULT}
                className="mt-6 p-5 rounded-2xl border border-[#18C964]/50 bg-[#18C964]/10 backdrop-blur relative overflow-hidden"
                data-testid="classified-declassified-cta"
              >
                <motion.div
                  aria-hidden
                  className="absolute inset-0 pointer-events-none"
                  style={{
                    background:
                      "radial-gradient(circle at 50% 50%, rgba(24,201,100,0.25), transparent 70%)",
                  }}
                  animate={HALO_PULSE_ANIMATE}
                  transition={HALO_PULSE_TRANSITION}
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
                    initial={CTA_BREATHE_INITIAL}
                    animate={CTA_BREATHE_ANIMATE}
                    transition={CTA_BREATHE_TRANSITION}
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
            <MetricsPanel
              t={t}
              vault={vault}
              locked={locked}
              combo={combo}
              dexMode={dexMode}
              microTicksTotal={microTicksTotal}
            />
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

// eslint-disable-next-line
function MetricsPanel({
  t,
  vault,
  locked,
  combo,
  dexMode,
  microTicksTotal,
}: any) {
  return (
    <div className="lg:col-span-5">
      <div className="rounded-2xl border border-[#F59E0B]/20 bg-[#0A0A0A] p-5">
        <div className="grid grid-cols-2 gap-3 font-mono text-xs">
          <Cell label={t("classifiedVault.dials")}>
            <span className="text-white text-lg">
              {locked}/{combo.length}
            </span>
          </Cell>
          <Cell label={t("classifiedVault.progress")}>
            <span className="text-white text-lg">
              {Math.round(vault?.progress_pct ?? 0)}%
            </span>
          </Cell>
          <Cell label={t("classifiedVault.tokens")}>
            <span className="text-white text-lg">
              {(vault?.tokens_sold ?? 0).toLocaleString()}
            </span>
          </Cell>
          <Cell label={t("classifiedVault.microTicks")}>
            <span className="text-[#F59E0B] text-lg">
              {microTicksTotal.toLocaleString()}
            </span>
          </Cell>
          <Cell label={t("classifiedVault.treasury")} colSpan={2}>
            <div className="flex items-baseline gap-2">
              <span className="text-[#18C964] text-lg">
                €
                {(vault?.treasury_eur_value ?? 0).toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                })}
              </span>
              <span className="text-white/40 text-[10px] uppercase">
                / €??? · {Math.round(vault?.treasury_progress_pct ?? 0)}%
              </span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-white/10 mt-2 overflow-hidden">
              <div
                className="h-full bg-[#18C964] transition-all duration-500"
                style={{
                  width: `${Math.min(
                    100,
                    Math.round(vault?.treasury_progress_pct ?? 0),
                  )}%`,
                }}
              />
            </div>
          </Cell>
          <Cell label={t("classifiedVault.mode")} colSpan={2}>
            <span className="text-white text-lg uppercase">{dexMode}</span>
          </Cell>
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
  );
}

interface CellProps {
  label: React.ReactNode;
  children: React.ReactNode;
  colSpan?: number;
}

function Cell({ label, children, colSpan = 1 }: CellProps) {
  return (
    <div
      className={`rounded-md border border-white/10 bg-black/40 p-3 ${
        colSpan === 2 ? "col-span-2" : ""
      }`}
    >
      <div className="text-white/40 text-[10px] uppercase">{label}</div>
      <div className="mt-0.5">{children}</div>
    </div>
  );
}

export default AuthedVaultView;
