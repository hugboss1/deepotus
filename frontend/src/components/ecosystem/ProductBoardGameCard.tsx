/**
 * ProductBoardGameCard — Card 2 of the ecosystem (board game FRAGMENTS).
 *
 * Features the live Founder counter (X / 500) and dynamic price tier
 * pulled from the backend. Pre-order CTA routes the user to /paiement
 * with product_id=boardgame.
 */
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Dices, Package, Tags, Truck, Gift, Sparkles, ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useI18n } from "@/i18n/I18nProvider";
import { fetchBoardgameCounter, type BoardgameCounter } from "@/lib/ecosystem";

const TIERS: Array<{
  tier: BoardgameCounter["current_tier"];
  labelKey: string;
  priceEur: number;
  range: string;
}> = [
  { tier: "early_bird_1", labelKey: "ecosystem.cards.boardgame.tiers.earlyBird1", priceEur: 39.99, range: "1–100" },
  { tier: "early_bird_2", labelKey: "ecosystem.cards.boardgame.tiers.earlyBird2", priceEur: 45.0, range: "101–200" },
  { tier: "standard_founder", labelKey: "ecosystem.cards.boardgame.tiers.standardFounder", priceEur: 59.0, range: "201–500" },
  { tier: "standard", labelKey: "ecosystem.cards.boardgame.tiers.standard", priceEur: 59.0, range: "501+" },
];

function formatEur(n: number): string {
  return n.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " €";
}

export function ProductBoardGameCard(): JSX.Element {
  const { t } = useI18n();
  const navigate = useNavigate();
  const [counter, setCounter] = useState<BoardgameCounter | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let mounted = true;
    fetchBoardgameCounter()
      .then((c) => {
        if (mounted) {
          setCounter(c);
        }
      })
      .catch((): void => undefined)
      .finally((): void => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const sold = counter?.sold ?? 0;
  const limit = counter?.founder_limit ?? 500;
  const pct = Math.min(100, Math.round((sold / Math.max(1, limit)) * 100));
  const currentTier = counter?.current_tier ?? "early_bird_1";
  const currentPrice = counter?.current_price_eur ?? 39.99;
  const isFounder = counter?.is_founder ?? true;

  return (
    <motion.section
      id="boardgame"
      data-testid="product-boardgame-card"
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="relative rounded-2xl border border-border bg-card/60 backdrop-blur-sm shadow-[0_2px_0_rgba(0,0,0,0.10),_0_18px_50px_rgba(0,0,0,0.18)] overflow-hidden"
    >
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-0">
        {/* Copy column (left on desktop for variety vs Roman) */}
        <div className="lg:col-span-7 p-7 sm:p-9 lg:p-12 flex flex-col gap-6">
          <div>
            <Badge
              variant="outline"
              className="font-mono text-[10px] uppercase tracking-[0.28em] border-amber-500/60 text-amber-400/95 bg-amber-500/5"
              data-testid="boardgame-badge"
            >
              {t("ecosystem.cards.boardgame.badge")}
            </Badge>
            <h2
              className="mt-4 font-display font-semibold text-3xl sm:text-4xl text-foreground tracking-tight"
              data-testid="boardgame-title"
            >
              {t("ecosystem.cards.boardgame.title")}
            </h2>
            <div className="mt-1 font-mono text-xs uppercase tracking-[0.20em] text-foreground/55">
              {t("ecosystem.cards.boardgame.subtitle")}
            </div>
          </div>

          <p className="text-sm md:text-base text-foreground/80 leading-relaxed max-w-prose">
            {t("ecosystem.cards.boardgame.pitch")}
          </p>

          {/* Live founder counter */}
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/[0.04] p-5">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-amber-400/95" aria-hidden />
                <div className="font-mono text-[11px] uppercase tracking-[0.24em] text-amber-300/90">
                  {t("ecosystem.cards.boardgame.counter.founder")}
                </div>
              </div>
              <div
                className="font-mono text-sm text-foreground tabular-nums"
                data-testid="boardgame-counter-text"
              >
                {loading ? "…" : `${sold} / ${limit}`}
              </div>
            </div>
            <div className="mt-3">
              <Progress value={pct} className="h-1.5" />
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
              <div className="rounded-md border border-border/70 bg-background/50 p-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-foreground/55">
                  {t("ecosystem.cards.boardgame.counter.currentPrice")}
                </div>
                <div
                  className="mt-1 font-display font-semibold text-lg text-foreground tabular-nums"
                  data-testid="boardgame-current-price"
                >
                  {formatEur(currentPrice)}
                </div>
              </div>
              <div className="rounded-md border border-border/70 bg-background/50 p-3">
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-foreground/55">
                  {t("ecosystem.cards.boardgame.counter.nextNumber")}
                </div>
                <div
                  className="mt-1 font-display font-semibold text-lg text-foreground tabular-nums"
                  data-testid="boardgame-next-number"
                >
                  {loading ? "…" : `#${counter?.next_number ?? 1}`}
                </div>
              </div>
            </div>
            {!isFounder && (
              <div
                className="mt-3 font-mono text-[10px] uppercase tracking-[0.20em] text-foreground/60"
                data-testid="boardgame-soldout-founder"
              >
                {t("ecosystem.cards.boardgame.counter.soldOutFounder")}
              </div>
            )}
          </div>

          {/* Tier ladder */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Tags className="h-4 w-4 text-foreground/70" aria-hidden />
              <div className="font-mono text-[11px] uppercase tracking-[0.24em] text-foreground/80">
                {t("ecosystem.cards.boardgame.tiers.heading")}
              </div>
            </div>
            <ul className="divide-y divide-border/60 border border-border/60 rounded-md overflow-hidden">
              {TIERS.map((tier) => {
                const active = tier.tier === currentTier;
                return (
                  <li
                    key={tier.tier}
                    className={`flex items-center justify-between gap-3 px-4 py-2.5 text-xs ${
                      active ? "bg-amber-500/10" : "bg-background/40"
                    }`}
                    data-testid={`boardgame-tier-row-${tier.tier}`}
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-block h-1.5 w-1.5 rounded-full ${
                          active ? "bg-amber-400" : "bg-foreground/30"
                        }`}
                      />
                      <span className="font-mono">{t(tier.labelKey)}</span>
                    </div>
                    <span
                      className={`font-mono tabular-nums ${
                        active ? "text-amber-300 font-semibold" : "text-foreground/65"
                      }`}
                    >
                      {formatEur(tier.priceEur)}
                    </span>
                  </li>
                );
              })}
            </ul>
            <p className="mt-2 text-[11px] text-foreground/55 leading-relaxed font-body">
              {t("ecosystem.cards.boardgame.tiers.founderNote")}
            </p>
          </div>

          {/* Shipping */}
          <div className="flex items-start gap-3 text-xs text-foreground/70">
            <Truck className="h-4 w-4 mt-0.5 text-foreground/55" aria-hidden />
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.20em] text-foreground/55">
                {t("ecosystem.cards.boardgame.shipping.heading")}
              </div>
              <div className="mt-1 leading-relaxed">
                {t("ecosystem.cards.boardgame.shipping.body")}
              </div>
            </div>
          </div>

          {/* Gift inside (Genesis card) */}
          <div className="flex items-start gap-3 text-xs text-foreground/70">
            <Gift className="h-4 w-4 mt-0.5 text-foreground/55" aria-hidden />
            <div className="leading-relaxed">
              {t("ecosystem.cards.boardgame.giftInside")}
            </div>
          </div>

          {/* Extension teaser (D&D) */}
          <div className="rounded-xl border border-border/60 bg-background/30 p-4">
            <div className="flex items-center gap-2">
              <Dices className="h-4 w-4 text-foreground/70" aria-hidden />
              <div className="font-mono text-[10px] uppercase tracking-[0.20em] text-foreground/70">
                {t("ecosystem.cards.boardgame.extension.heading")}
              </div>
            </div>
            <p className="mt-2 text-xs text-foreground/65 leading-relaxed font-body">
              {t("ecosystem.cards.boardgame.extension.body")}
            </p>
          </div>

          <div className="mt-auto flex flex-col sm:flex-row sm:items-center gap-3">
            <Button
              type="button"
              size="lg"
              className="gap-2 bg-amber-500/95 hover:bg-amber-500 text-zinc-950 font-medium"
              onClick={() => navigate("/paiement?product=boardgame")}
              data-testid="boardgame-buy-cta"
            >
              <Package className="h-4 w-4" aria-hidden />
              {t("ecosystem.cards.boardgame.cta")}
              <ChevronRight className="h-4 w-4" aria-hidden />
            </Button>
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-foreground/55">
              {t("ecosystem.cards.boardgame.status")}
            </div>
          </div>
        </div>

        {/* Visual column (right on desktop) */}
        <div className="lg:col-span-5 relative bg-[#0B0D10] order-first lg:order-last">
          <div className="relative aspect-[4/5] lg:aspect-auto lg:h-full overflow-hidden">
            <picture>
              <source
                srcSet="/assets/products/jeu-plateau.webp"
                type="image/webp"
              />
              <img
                src="/assets/products/jeu-plateau.jpg"
                alt={t("ecosystem.cards.boardgame.title")}
                className="absolute inset-0 w-full h-full object-cover"
                loading="lazy"
                data-testid="boardgame-hero-img"
              />
            </picture>
          </div>
        </div>
      </div>
    </motion.section>
  );
}
