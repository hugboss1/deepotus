/**
 * HowToBuyPhasedSteps — phase-aware quick-start strip rendered at the
 * top of /how-to-buy.
 *
 * Why this lives next to the existing in-character HowToBuy page (and
 * doesn't replace it) — the long page is the cynical, lore-driven
 * narrative and represents the authored voice of the Prophet. This
 * strip is a sober, scannable summary for users who already know
 * what they're doing and just want to click the right button for the
 * current phase.
 *
 * The 3 phase paths come straight from the brief (TASK 4):
 *
 *   PRE-MINT   : wallet → fund SOL → whitelist → wait
 *   LIVE       : open Pump.fun → connect → buy SOL → watch curve
 *   GRADUATED  : open PumpSwap → connect → swap → (optional PumpSwap)
 *
 * The "Trade on Telegram (BonkBot)" CTA is shown in EVERY phase — it
 * works pre-mint (waitlist) and post-mint (referral link if env is set)
 * and serves as the mobile-friendly fallback the brief explicitly
 * requested.
 */

import React from "react";
import { ExternalLink, Wallet, Coins, Mail, Bell, Cpu, Activity, Zap, Rocket } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n/I18nProvider";
import { getLaunchPhase, URLS as PHASE_URLS } from "@/lib/launchPhase";

interface PhaseStep {
  icon: React.ReactNode;
  labelKey: string;
  href?: string;
  external?: boolean;
}

function getStepsForPhase(phase: ReturnType<typeof getLaunchPhase>): PhaseStep[] {
  if (phase === "graduated") {
    return [
      {
        icon: <Rocket size={14} />,
        labelKey: "howToBuyPhased.graduated.s1",
        href: PHASE_URLS.pumpswap,
        external: true,
      },
      { icon: <Wallet size={14} />, labelKey: "howToBuyPhased.graduated.s2" },
      { icon: <Activity size={14} />, labelKey: "howToBuyPhased.graduated.s3" },
      ...(PHASE_URLS.pumpswap
        ? [
            {
              icon: <ExternalLink size={14} />,
              labelKey: "howToBuyPhased.graduated.s4_pumpswap",
              href: PHASE_URLS.pumpswap,
              external: true,
            },
          ]
        : []),
    ];
  }
  if (phase === "live") {
    return [
      {
        icon: <Zap size={14} />,
        labelKey: "howToBuyPhased.live.s1",
        href: PHASE_URLS.pumpfun,
        external: true,
      },
      { icon: <Wallet size={14} />, labelKey: "howToBuyPhased.live.s2" },
      { icon: <Coins size={14} />, labelKey: "howToBuyPhased.live.s3" },
      { icon: <Activity size={14} />, labelKey: "howToBuyPhased.live.s4" },
    ];
  }
  // PRE-MINT
  return [
    {
      icon: <Wallet size={14} />,
      labelKey: "howToBuyPhased.pre.s1",
      href: "https://phantom.app",
      external: true,
    },
    { icon: <Coins size={14} />, labelKey: "howToBuyPhased.pre.s2" },
    { icon: <Mail size={14} />, labelKey: "howToBuyPhased.pre.s3", href: "#whitelist" },
    { icon: <Bell size={14} />, labelKey: "howToBuyPhased.pre.s4" },
  ];
}

export function HowToBuyPhasedSteps() {
  const { t } = useI18n();
  const phase = getLaunchPhase();
  const steps = getStepsForPhase(phase);

  const phaseLabelKey =
    phase === "graduated"
      ? "howToBuyPhased.bannerGraduated"
      : phase === "live"
        ? "howToBuyPhased.bannerLive"
        : "howToBuyPhased.bannerPre";

  const phaseAccent =
    phase === "graduated"
      ? "border-[#2DD4BF]/40 bg-[#2DD4BF]/10 text-[#2DD4BF]"
      : phase === "live"
        ? "border-[#33FF33]/40 bg-[#33FF33]/10 text-[#33FF33]"
        : "border-[#F59E0B]/40 bg-[#F59E0B]/10 text-[#F59E0B]";

  // Live mode caveat (bonding curve graduation hint).
  const showLiveNote = phase === "live";

  return (
    <section
      className="rounded-md border border-foreground/15 bg-foreground/[0.02] p-5 sm:p-6"
      data-testid="howtobuy-phased-steps"
      data-phase={phase}
    >
      <div className="flex items-baseline justify-between gap-3 mb-4 flex-wrap">
        <h2 className="text-sm font-semibold tracking-wide flex items-center gap-2">
          <Cpu size={14} />
          {t("howToBuyPhased.title") as string}
        </h2>
        <span
          className={`inline-flex items-center px-2.5 py-1 rounded-full border text-[10px] font-mono uppercase tracking-[0.25em] ${phaseAccent}`}
        >
          {t(phaseLabelKey) as string}
        </span>
      </div>
      <ol className="space-y-2.5">
        {steps.map((step, idx) => {
          // Stable composite key — `labelKey` is a deterministic i18n
          // string (e.g. "howToBuyPhased.preMint.step1.label") and is
          // unique per step within a phase. Falls back to `href` when
          // present so this still works if a phase ever ships two steps
          // sharing a labelKey but pointing at different URLs.
          const stepKey = `${step.labelKey}::${step.href || "no-href"}`;
          const label = t(step.labelKey) as string;
          const inner = (
            <div className="flex items-start gap-3">
              <span className="shrink-0 w-6 h-6 rounded-full border border-foreground/15 bg-foreground/[0.04] flex items-center justify-center text-[10px] font-mono">
                {idx + 1}
              </span>
              <span className="shrink-0 mt-0.5 text-foreground/55">{step.icon}</span>
              <span className="flex-1 text-xs sm:text-sm text-foreground/85 leading-relaxed">
                {label}
              </span>
              {step.href && (
                <ExternalLink
                  size={12}
                  className={`shrink-0 mt-0.5 ${step.external ? "text-[#2DD4BF]" : "text-foreground/55"}`}
                />
              )}
            </div>
          );
          if (step.href) {
            return (
              <li key={stepKey}>
                <a
                  href={step.href}
                  target={step.external ? "_blank" : undefined}
                  rel={step.external ? "noopener noreferrer" : undefined}
                  className="block rounded-md px-2 py-1.5 hover:bg-foreground/[0.04] transition-colors"
                  data-testid={`howtobuy-step-${idx + 1}`}
                >
                  {inner}
                </a>
              </li>
            );
          }
          return (
            <li key={stepKey} className="px-2 py-1.5" data-testid={`howtobuy-step-${idx + 1}`}>
              {inner}
            </li>
          );
        })}
      </ol>
      {showLiveNote && (
        <p
          className="mt-4 text-[11px] text-foreground/55 italic leading-relaxed"
          data-testid="howtobuy-live-note"
        >
          {t("howToBuyPhased.live.note") as string}
        </p>
      )}
      {/* BonkBot CTA — present in every phase, especially useful on mobile. */}
      {PHASE_URLS.bonkbot && (
        <div className="mt-4 pt-4 border-t border-foreground/10">
          <Button
            asChild
            variant="outline"
            size="sm"
            className="rounded-[var(--btn-radius)]"
            data-testid="howtobuy-bonkbot-cta"
          >
            <a
              href={PHASE_URLS.bonkbot}
              target="_blank"
              rel="noopener noreferrer"
            >
              📲 {t("howToBuyPhased.bonkbotCta") as string}
              <ExternalLink size={12} className="ml-1.5" />
            </a>
          </Button>
        </div>
      )}
    </section>
  );
}

export default HowToBuyPhasedSteps;
