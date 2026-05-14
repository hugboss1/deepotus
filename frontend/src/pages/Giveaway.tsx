/**
 * /giveaway — May 20 Liquidity Pool draw rules (Sprint 19).
 *
 * Renders:
 *  - Hero with the headline + live countdown to drawDateIso.
 *  - Pool amount card (single source of truth from lib/missions.GIVEAWAY).
 *  - Two eligibility rule cards (3 invites + $30 hold).
 *  - Draw mechanics ladder (snapshot → cross-ref → VRF → announce).
 *  - Footer disclaimer + CTAs back to /missions and into BonkBot.
 *
 * Countdown uses a 1Hz interval; rebases against `Date.now()` each
 * tick so it stays accurate even if the browser throttles the timer
 * in background tabs.
 */
import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Coins,
  ExternalLink,
  Gauge,
  Sparkles,
  Users,
} from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";
import ThemeToggle from "@/components/landing/ThemeToggle";
import { BONKBOT_REF_URL, GIVEAWAY } from "@/lib/missions";

function useCountdown(targetIso: string): {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  isLive: boolean;
  isEnded: boolean;
} {
  const target = useMemo(() => new Date(targetIso).getTime(), [targetIso]);
  const [now, setNow] = useState<number>(() => Date.now());

  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);

  const diff = target - now;
  // The 60-minute "live" window is when the snapshot is being
  // processed; useful for showing a special chip instead of zeros.
  const isLive = diff <= 0 && diff > -60 * 60 * 1000;
  const isEnded = diff <= -60 * 60 * 1000;
  const clamped = Math.max(0, diff);
  const days = Math.floor(clamped / (1000 * 60 * 60 * 24));
  const hours = Math.floor((clamped / (1000 * 60 * 60)) % 24);
  const minutes = Math.floor((clamped / (1000 * 60)) % 60);
  const seconds = Math.floor((clamped / 1000) % 60);
  return { days, hours, minutes, seconds, isLive, isEnded };
}

const Cell: React.FC<{ value: number; label: string; testId?: string }> = ({ value, label, testId }) => (
  <div className="flex flex-col items-center min-w-[64px]" data-testid={testId}>
    <span className="font-mono text-3xl sm:text-4xl font-semibold tabular-nums text-foreground">
      {String(value).padStart(2, "0")}
    </span>
    <span className="mt-1 text-[9px] sm:text-[10px] font-mono uppercase tracking-[0.25em] text-foreground/45">
      {label}
    </span>
  </div>
);

const Separator: React.FC = () => (
  <span className="font-mono text-2xl sm:text-3xl text-foreground/25 select-none" aria-hidden>
    :
  </span>
);

const Giveaway: React.FC = () => {
  const { t, lang } = useI18n();
  const cd = useCountdown(GIVEAWAY.drawDateIso);

  useEffect(() => {
    const prev = document.title;
    document.title = `Giveaway · PROTOCOL ΔΣ`;
    return () => {
      document.title = prev;
    };
  }, []);

  // Localised display of the absolute draw date below the countdown,
  // honouring the user's preferred language.
  const drawDatePretty = useMemo(() => {
    try {
      return new Date(GIVEAWAY.drawDateIso).toLocaleString(lang === "fr" ? "fr-FR" : "en-US", {
        dateStyle: "full",
        timeStyle: "short",
        timeZone: "UTC",
      });
    } catch {
      return GIVEAWAY.drawDateIso;
    }
  }, [lang]);

  return (
    <div className="min-h-screen bg-background text-foreground font-body" data-testid="giveaway-page">
      <header className="max-w-5xl mx-auto px-4 sm:px-6 pt-8 pb-4 flex items-center justify-between">
        <Link
          to="/missions"
          className="inline-flex items-center gap-2 text-xs uppercase tracking-widest text-foreground/55 hover:text-foreground transition-colors"
          data-testid="giveaway-back-link"
        >
          <ArrowLeft size={14} /> {t("missionsPage.hero.title") as string}
        </Link>
        <ThemeToggle />
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 pb-24">
        {/* ---- Hero ---- */}
        <section className="pt-6 pb-10 border-b border-foreground/10">
          <p className="text-[11px] uppercase tracking-[0.25em] text-[#F59E0B] font-mono">
            {t("giveawayPage.hero.kicker") as string}
          </p>
          <h1
            className="mt-3 font-display text-3xl sm:text-4xl lg:text-5xl font-semibold leading-tight tracking-tight"
            data-testid="giveaway-hero-title"
          >
            {t("giveawayPage.hero.title") as string}
          </h1>
          <p className="mt-4 text-sm sm:text-base text-foreground/70 leading-relaxed max-w-2xl">
            {t("giveawayPage.hero.subtitle") as string}
          </p>
        </section>

        {/* ---- Countdown + Pool ---- */}
        <section className="py-10 grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Countdown — spans 2 cols on lg */}
          <div className="lg:col-span-2 rounded-md border border-[#FF3B3B]/40 bg-gradient-to-br from-[#FF3B3B]/[0.05] to-[#F59E0B]/[0.04] px-5 sm:px-7 py-6" data-testid="giveaway-countdown">
            <p className="text-[10px] font-mono uppercase tracking-[0.25em] text-[#FF3B3B]">
              {cd.isLive
                ? (t("giveawayPage.countdown.live") as string)
                : cd.isEnded
                ? (t("giveawayPage.countdown.ended") as string)
                : (t("giveawayPage.countdown.label") as string)}
            </p>
            <div className="mt-4 flex items-end justify-start gap-3 sm:gap-5">
              <Cell value={cd.days} label={t("giveawayPage.countdown.days") as string} testId="giveaway-cd-days" />
              <Separator />
              <Cell value={cd.hours} label={t("giveawayPage.countdown.hours") as string} testId="giveaway-cd-hours" />
              <Separator />
              <Cell value={cd.minutes} label={t("giveawayPage.countdown.minutes") as string} testId="giveaway-cd-minutes" />
              <Separator />
              <Cell value={cd.seconds} label={t("giveawayPage.countdown.seconds") as string} testId="giveaway-cd-seconds" />
            </div>
            <p className="mt-5 text-[11px] font-mono text-foreground/55">
              {drawDatePretty} · UTC
            </p>
          </div>

          {/* Pool card */}
          <div className="rounded-md border border-[#F59E0B]/45 bg-[#F59E0B]/[0.06] px-5 py-6 flex flex-col items-start" data-testid="giveaway-pool">
            <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.25em] text-[#F59E0B]">
              <Coins size={12} /> {t("giveawayPage.pool.kicker") as string}
            </div>
            <p className="mt-3 font-display text-4xl sm:text-5xl font-semibold tracking-tight tabular-nums" data-testid="giveaway-pool-amount">
              {GIVEAWAY.rewardSol}
              <span className="ml-2 text-base text-foreground/55 font-mono uppercase tracking-widest">
                {t("giveawayPage.pool.amountSuffix") as string}
              </span>
            </p>
            <p className="mt-3 text-xs text-foreground/65 leading-relaxed">
              {(t("giveawayPage.pool.copy") as string).replace("{winnersCount}", String(GIVEAWAY.winnersCount))}
            </p>
          </div>
        </section>

        {/* ---- Rules ---- */}
        <section className="py-10 border-t border-foreground/10">
          <p className="text-[11px] uppercase tracking-[0.25em] text-[#FF3B3B] font-mono">
            {t("giveawayPage.rules.kicker") as string}
          </p>
          <h2 className="mt-2 font-display text-2xl sm:text-3xl font-semibold leading-tight tracking-tight">
            {t("giveawayPage.rules.title") as string}
          </h2>
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Rule 01 */}
            <div className="rounded-md border border-[#22D3EE]/30 bg-[#22D3EE]/[0.04] p-5" data-testid="giveaway-rule-01">
              <div className="flex items-center gap-2 mb-2">
                <span className="font-mono text-[10px] uppercase tracking-[0.2em] px-2 py-0.5 rounded-sm border border-[#22D3EE]/50 text-[#22D3EE]">
                  {t("giveawayPage.rules.rule1.tag") as string}
                </span>
                <Users size={14} className="text-[#22D3EE]" />
                <span className="font-mono text-[10px] text-foreground/55">
                  ≥ {GIVEAWAY.rules.minInvites}
                </span>
              </div>
              <h3 className="font-display text-lg font-semibold tracking-tight">
                {t("giveawayPage.rules.rule1.title") as string}
              </h3>
              <p className="mt-2 text-sm text-foreground/70 leading-relaxed">
                {t("giveawayPage.rules.rule1.body") as string}
              </p>
            </div>
            {/* Rule 02 */}
            <div className="rounded-md border border-[#33FF66]/30 bg-[#33FF66]/[0.05] p-5" data-testid="giveaway-rule-02">
              <div className="flex items-center gap-2 mb-2">
                <span className="font-mono text-[10px] uppercase tracking-[0.2em] px-2 py-0.5 rounded-sm border border-[#33FF66]/50 text-[#33FF66]">
                  {t("giveawayPage.rules.rule2.tag") as string}
                </span>
                <Sparkles size={14} className="text-[#33FF66]" />
                <span className="font-mono text-[10px] text-foreground/55">
                  ≥ ${GIVEAWAY.rules.minHoldingUsd}
                </span>
              </div>
              <h3 className="font-display text-lg font-semibold tracking-tight">
                {t("giveawayPage.rules.rule2.title") as string}
              </h3>
              <p className="mt-2 text-sm text-foreground/70 leading-relaxed">
                {t("giveawayPage.rules.rule2.body") as string}
              </p>
            </div>
          </div>
        </section>

        {/* ---- Mechanism ladder ---- */}
        <section className="py-10 border-t border-foreground/10">
          <p className="text-[11px] uppercase tracking-[0.25em] text-foreground/55 font-mono flex items-center gap-2">
            <Gauge size={12} /> {t("giveawayPage.mechanism.kicker") as string}
          </p>
          <h2 className="mt-2 font-display text-2xl sm:text-3xl font-semibold leading-tight tracking-tight">
            {t("giveawayPage.mechanism.title") as string}
          </h2>
          <ol className="mt-6 space-y-3" data-testid="giveaway-mechanism-list">
            {[
              t("giveawayPage.mechanism.step1") as string,
              t("giveawayPage.mechanism.step2") as string,
              t("giveawayPage.mechanism.step3") as string,
              (t("giveawayPage.mechanism.step4") as string).replace("{winnersCount}", String(GIVEAWAY.winnersCount)),
            ].map((step, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-foreground/80" data-testid={`giveaway-step-${i + 1}`}>
                <span className="shrink-0 mt-0.5 w-6 h-6 grid place-items-center rounded-full border border-[#F59E0B]/45 text-[#F59E0B] font-mono text-[10px] font-semibold">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="leading-relaxed">{step}</span>
              </li>
            ))}
          </ol>
        </section>

        {/* ---- CTAs + disclaimer ---- */}
        <section className="py-10 border-t border-foreground/10">
          <div className="flex items-center gap-3 flex-wrap" data-testid="giveaway-ctas">
            <Link
              to="/missions"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-md bg-foreground text-background font-mono text-xs uppercase tracking-[0.18em] hover:bg-foreground/85 transition-colors"
              data-testid="giveaway-cta-primary"
            >
              {t("giveawayPage.cta.primary") as string} <ArrowRight size={12} />
            </Link>
            <a
              href={BONKBOT_REF_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-md border border-[#33FF66]/50 text-[#33FF66] hover:bg-[#33FF66]/10 font-mono text-xs uppercase tracking-[0.18em] transition-colors"
              data-testid="giveaway-cta-secondary"
            >
              {t("giveawayPage.cta.secondary") as string} <ExternalLink size={12} />
            </a>
            <span className="ml-auto text-[10px] font-mono text-foreground/45 uppercase tracking-widest inline-flex items-center gap-1">
              <CheckCircle2 size={11} /> ON-CHAIN VRF
            </span>
          </div>
          <p className="mt-6 text-[11px] text-foreground/50 leading-relaxed italic" data-testid="giveaway-footer">
            ⚖ {t("giveawayPage.footer") as string}
          </p>
        </section>
      </main>
    </div>
  );
};

export default Giveaway;
