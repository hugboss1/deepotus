import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n/I18nProvider";
import { getBuyUrl, isBuyUrlExternal } from "@/lib/links";
import { GlitchNum } from "./useGlitchNumber";

/**
 * Dual-state launch indicator embedded in the Hero poster card.
 *
 *  Pre-mint  → glitched random digits + cynical sub-line. No fixed date so
 *              we never miss a countdown / lose credibility.
 *  Post-mint → "LIVE ON PUMP.FUN" badge + buy CTA.
 *
 * The decision is taken by the parent via the `mintLive` boolean prop so
 * this component stays purely presentational.
 */
export function HeroCountdown({ mintLive }) {
  const { t } = useI18n();

  if (!mintLive) {
    return (
      <div className="p-4" data-testid="hero-countdown-block">
        <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground mb-3 flex items-center gap-2">
          <span className="relative inline-flex">
            <span className="absolute inset-0 inline-block w-2 h-2 rounded-full bg-[--campaign-red] animate-ping opacity-70" />
            <span className="relative inline-block w-2 h-2 rounded-full bg-[--campaign-red]" />
          </span>
          {t("hero.imminentKicker")}
        </div>
        <div
          className="grid grid-cols-4 gap-2 select-none"
          aria-hidden="true"
          data-testid="hero-countdown"
        >
          <GlitchNum label={t("hero.days")} refreshMs={420} />
          <GlitchNum label={t("hero.hours")} refreshMs={170} />
          <GlitchNum label={t("hero.minutes")} refreshMs={90} />
          <GlitchNum label={t("hero.seconds")} refreshMs={55} />
        </div>
        <p className="mt-3 font-mono text-[10px] text-muted-foreground leading-relaxed">
          {t("hero.imminentSubtitle")}
        </p>
      </div>
    );
  }

  return (
    <div className="p-4" data-testid="hero-countdown-block">
      <div data-testid="hero-live-badge">
        <div className="font-mono text-[10px] uppercase tracking-widest text-[#18C964] mb-2 flex items-center gap-2">
          <span className="relative inline-flex">
            <span className="absolute inset-0 inline-block w-2 h-2 rounded-full bg-[#18C964] animate-ping" />
            <span className="relative inline-block w-2 h-2 rounded-full bg-[#18C964]" />
          </span>
          {t("hero.liveKicker")}
        </div>
        <div className="font-display text-xl md:text-2xl font-semibold leading-tight">
          {t("hero.liveTitle")}
        </div>
        <p className="mt-2 text-sm text-foreground/80 leading-relaxed">
          {t("hero.liveSubtitle")}
        </p>
        <Button
          asChild
          size="sm"
          className="mt-3 rounded-[var(--btn-radius)] btn-press font-semibold"
          data-testid="hero-live-buy-button"
        >
          <a
            href={getBuyUrl()}
            target={isBuyUrlExternal() ? "_blank" : undefined}
            rel={isBuyUrlExternal() ? "noopener noreferrer" : undefined}
          >
            {t("hero.liveCta")}
          </a>
        </Button>
      </div>
    </div>
  );
}

export default HeroCountdown;
