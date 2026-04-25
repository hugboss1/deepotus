import { Link } from "react-router-dom";
import { Rocket, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n/I18nProvider";
import { getBuyUrl, isBuyUrlExternal, PUMPFUN_URL } from "@/lib/links";

/**
 * The "0% Tax Protocol" + "Buy $DEEPOTUS" cinematic block in the right column
 * of the Tokenomics section. Sits below the legend.
 */
export function TokenomicsTaxAndBuy() {
  const { t } = useI18n();

  return (
    <>
      <div className="mt-6 rounded-xl border-2 border-[#18C964]/40 bg-gradient-to-br from-[#18C964]/5 to-card p-5">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-[#18C964]/50 bg-[#18C964]/10 px-2.5 py-1 font-mono text-[10px] uppercase tracking-widest text-[#18C964]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#18C964] animate-pulse" />
            Pump.fun
          </span>
          <div className="font-display font-semibold text-lg">
            {t("tokenomics.taxTitle")}
          </div>
          <span className="ml-auto font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            {t("tokenomics.taxBadge")}
          </span>
        </div>
        <p className="text-sm text-foreground/85 mt-2 leading-relaxed">
          {t("tokenomics.taxIntro")}
        </p>
        <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
          {t("tokenomics.taxCap")}
        </p>

        <div className="mt-4 pt-4 border-t border-[#18C964]/20">
          <div className="font-mono text-[10px] uppercase tracking-widest text-[#18C964] mb-1.5">
            {t("tokenomics.cynicalTitle")}
          </div>
          <p className="text-sm text-foreground/80 italic leading-relaxed">
            {t("tokenomics.cynicalBody")}
          </p>
        </div>
      </div>

      <div
        className="mt-6 rounded-xl border border-border bg-card p-5"
        data-testid="tokenomics-buy-cta-block"
      >
        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
          {t("tokenomics.buyKicker")}
        </div>
        <h3 className="mt-1 font-display font-semibold text-xl md:text-2xl">
          {t("tokenomics.buyTitle")}
        </h3>
        <p className="mt-2 text-sm text-foreground/80 leading-relaxed">
          {t("tokenomics.buyCopy")}
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Button
            asChild
            size="lg"
            className="rounded-[var(--btn-radius)] btn-press font-semibold"
            data-testid="tokenomics-buy-primary"
          >
            <a
              href={getBuyUrl()}
              target={isBuyUrlExternal() ? "_blank" : undefined}
              rel={isBuyUrlExternal() ? "noopener noreferrer" : undefined}
            >
              <Rocket size={16} className="mr-1" />
              {t("tokenomics.buyCtaPrimary")}
            </a>
          </Button>
          <Button
            asChild
            size="lg"
            variant="outline"
            className="rounded-[var(--btn-radius)] btn-press font-semibold"
            data-testid="tokenomics-buy-guide"
          >
            <Link to="/how-to-buy">
              <BookOpen size={16} className="mr-1" />
              {t("tokenomics.buyCtaGuide")}
            </Link>
          </Button>
        </div>
        {!PUMPFUN_URL && (
          <p className="mt-3 font-mono text-[10px] text-muted-foreground">
            {t("tokenomics.buyPrelaunchNote")}
          </p>
        )}
      </div>
    </>
  );
}

export default TokenomicsTaxAndBuy;
