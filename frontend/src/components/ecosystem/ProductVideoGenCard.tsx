/**
 * ProductVideoGenCard — Card 3 of the ecosystem (Video Generator).
 *
 * Visual: <VideoGenTeaserPlayer/> (renders a stylized mockup as
 * placeholder until the real teaser MP4 is uploaded — flip
 * ``HAS_TEASER`` in that file to switch).
 *
 * Sprint 20.1 additions:
 *   - Subscription tiers block (30 / 150 / 250 posts/month) with a
 *     "Soon" badge and a Contact CTA that pre-fills the B2B dialog
 *     with the relevant tier so the inquiry is segmented downstream.
 *   - The "Nous contacter" CTA now accepts an optional ``onContactWithContext``
 *     callback so the subscription button can pass a custom prefilled
 *     message; the white-label button keeps its generic intent.
 */
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Wand2,
  Cpu,
  Mic,
  CalendarClock,
  Building2,
  ChevronRight,
  ShoppingCart,
  FileText,
  KeyRound,
  Layers,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n/I18nProvider";
import { VideoGenTeaserPlayer } from "./VideoGenTeaserPlayer";

interface Props {
  onContactB2B: () => void;
  /** Sprint 20.1 — open the B2B dialog with a subscription-context message pre-filled. */
  onContactSubscription: (prefilledMessage: string) => void;
}

const SUBSCRIPTION_TIERS = [
  { posts: 30, labelKey: "ecosystem.cards.videogen.subscription.tier1Label" },
  { posts: 150, labelKey: "ecosystem.cards.videogen.subscription.tier2Label" },
  { posts: 250, labelKey: "ecosystem.cards.videogen.subscription.tier3Label" },
];

export function ProductVideoGenCard({
  onContactB2B,
  onContactSubscription,
}: Props): JSX.Element {
  const { t } = useI18n();
  const navigate = useNavigate();

  const handleSubscribeClick = (postsPerMonth: number): void => {
    // Build the prefilled message by interpolating {tier} with the
    // selected posts/month value. The dialog seeds the textarea so the
    // visitor only has to confirm + add their name/email.
    const template = t(
      "ecosystem.cards.videogen.subscription.inquiryPrefill"
    ) as string;
    const message = template.replace("{tier}", String(postsPerMonth));
    onContactSubscription(message);
  };

  return (
    <motion.section
      id="videogen"
      data-testid="product-videogen-card"
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="relative rounded-2xl border border-border bg-card/60 backdrop-blur-sm shadow-[0_2px_0_rgba(0,0,0,0.10),_0_18px_50px_rgba(0,0,0,0.18)] overflow-hidden"
    >
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-0">
        {/* Mockup / teaser viewer column */}
        <div className="lg:col-span-6 p-6 sm:p-7 lg:p-10 bg-[#070A0E]">
          <VideoGenTeaserPlayer />
        </div>

        {/* Copy column */}
        <div className="lg:col-span-6 p-7 sm:p-9 lg:p-12 flex flex-col gap-6">
          <div>
            <Badge
              variant="outline"
              className="font-mono text-[10px] uppercase tracking-[0.28em] border-emerald-500/55 text-emerald-300/95 bg-emerald-500/5"
              data-testid="videogen-badge"
            >
              {t("ecosystem.cards.videogen.badge")}
            </Badge>
            <h2
              className="mt-4 font-display font-semibold text-3xl sm:text-4xl text-foreground tracking-tight"
              data-testid="videogen-title"
            >
              {t("ecosystem.cards.videogen.title")}
            </h2>
            <div className="mt-1 font-mono text-xs uppercase tracking-[0.20em] text-foreground/55">
              {t("ecosystem.cards.videogen.subtitle")}
            </div>
          </div>

          <p className="text-sm md:text-base text-foreground/80 leading-relaxed max-w-prose">
            {t("ecosystem.cards.videogen.pitch")}
          </p>

          {/* Price block */}
          <div className="flex items-baseline gap-3">
            <div
              className="font-display font-bold text-4xl text-foreground tabular-nums"
              data-testid="videogen-price"
            >
              {t("ecosystem.cards.videogen.price")}
            </div>
            <div className="font-mono text-[11px] uppercase tracking-[0.20em] text-foreground/55">
              {t("ecosystem.cards.videogen.priceNote")}
            </div>
          </div>

          {/* Features grid */}
          <ul className="grid grid-cols-2 gap-2 text-xs">
            <li className="flex items-center gap-2 rounded-md border border-border/60 bg-background/30 px-3 py-2">
              <Cpu className="h-3.5 w-3.5 text-foreground/60" aria-hidden />
              <span>{t("ecosystem.cards.videogen.features.local")}</span>
            </li>
            <li className="flex items-center gap-2 rounded-md border border-border/60 bg-background/30 px-3 py-2">
              <Wand2 className="h-3.5 w-3.5 text-foreground/60" aria-hidden />
              <span>{t("ecosystem.cards.videogen.features.nodes")}</span>
            </li>
            <li className="flex items-center gap-2 rounded-md border border-border/60 bg-background/30 px-3 py-2">
              <Mic className="h-3.5 w-3.5 text-foreground/60" aria-hidden />
              <span>{t("ecosystem.cards.videogen.features.avatars")}</span>
            </li>
            <li className="flex items-center gap-2 rounded-md border border-border/60 bg-background/30 px-3 py-2">
              <CalendarClock className="h-3.5 w-3.5 text-foreground/60" aria-hidden />
              <span>{t("ecosystem.cards.videogen.features.scheduler")}</span>
            </li>
          </ul>

          {/* Proof line */}
          <div className="text-xs text-foreground/55 leading-relaxed max-w-prose font-body italic">
            “{t("ecosystem.cards.videogen.proof")}”
          </div>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-3">
            <Button
              type="button"
              size="lg"
              className="gap-2 bg-emerald-500/95 hover:bg-emerald-500 text-zinc-950 font-medium"
              onClick={() => navigate("/paiement?product=videogen")}
              data-testid="videogen-buy-cta"
            >
              <ShoppingCart className="h-4 w-4" aria-hidden />
              {t("ecosystem.cards.videogen.cta")}
              <ChevronRight className="h-4 w-4" aria-hidden />
            </Button>
            <Button
              type="button"
              size="lg"
              variant="secondary"
              className="gap-2"
              data-testid="videogen-guide-cta"
            >
              <FileText className="h-4 w-4" aria-hidden />
              {t("ecosystem.cards.videogen.guideCta")}
            </Button>
          </div>

          {/* Subscription tiers (Sprint 20.1) — 30 / 150 / 250 posts/month */}
          <div
            className="mt-4 rounded-xl border border-amber-500/30 bg-amber-500/[0.05] p-5"
            data-testid="videogen-subscription-block"
          >
            <div className="flex items-center gap-2 mb-2">
              <Layers className="h-4 w-4 text-amber-300/95" aria-hidden />
              <Badge
                variant="outline"
                className="font-mono text-[10px] uppercase tracking-[0.24em] border-amber-500/40 text-amber-300/95 bg-transparent"
                data-testid="videogen-subscription-badge"
              >
                {t("ecosystem.cards.videogen.subscription.badge")}
              </Badge>
            </div>
            <div className="font-display font-semibold text-lg text-foreground">
              {t("ecosystem.cards.videogen.subscription.heading")}
            </div>
            <p className="mt-2 text-xs text-foreground/75 leading-relaxed font-body">
              {t("ecosystem.cards.videogen.subscription.body")}
            </p>

            {/* Keys-included argument */}
            <div className="mt-3 flex items-start gap-3 rounded-md border border-amber-500/25 bg-amber-500/[0.06] px-3 py-2.5">
              <KeyRound className="h-4 w-4 mt-0.5 text-amber-300/95 shrink-0" aria-hidden />
              <div className="min-w-0">
                <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-amber-200/95">
                  {t("ecosystem.cards.videogen.subscription.keysIncludedLabel")}
                </div>
                <p className="mt-0.5 text-[11px] text-foreground/70 leading-relaxed font-body">
                  {t("ecosystem.cards.videogen.subscription.keysIncludedBody")}
                </p>
              </div>
            </div>

            {/* 3 tier buttons */}
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-2">
              {SUBSCRIPTION_TIERS.map((tier) => (
                <button
                  key={tier.posts}
                  type="button"
                  onClick={() => handleSubscribeClick(tier.posts)}
                  className="group flex flex-col items-start gap-1 rounded-md border border-border/60 bg-background/40 px-3 py-2.5 text-left transition-colors hover:border-amber-500/45 hover:bg-amber-500/[0.06] focus:outline-none focus-visible:border-amber-500/60"
                  data-testid={`videogen-subscription-tier-${tier.posts}`}
                >
                  <span className="font-mono text-[9px] uppercase tracking-[0.22em] text-amber-300/85">
                    {t(tier.labelKey)}
                  </span>
                  <span className="font-display font-bold text-lg text-foreground tabular-nums">
                    {tier.posts}
                  </span>
                  <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-foreground/55">
                    {t("ecosystem.cards.videogen.subscription.postsLabel")}
                  </span>
                </button>
              ))}
            </div>

            <p className="mt-3 text-[11px] text-foreground/55 leading-relaxed font-body italic">
              {t("ecosystem.cards.videogen.subscription.soonNote")}
            </p>
          </div>

          {/* White-label encart */}
          <div className="mt-4 rounded-xl border border-cyan-500/30 bg-cyan-500/[0.05] p-5">
            <div className="flex items-center gap-2 mb-2">
              <Building2 className="h-4 w-4 text-cyan-300/90" aria-hidden />
              <Badge
                variant="outline"
                className="font-mono text-[10px] uppercase tracking-[0.24em] border-cyan-500/40 text-cyan-300/95 bg-transparent"
              >
                {t("ecosystem.cards.videogen.whitelabel.badge")}
              </Badge>
            </div>
            <div className="font-display font-semibold text-lg text-foreground">
              {t("ecosystem.cards.videogen.whitelabel.heading")}
            </div>
            <p className="mt-2 text-xs text-foreground/75 leading-relaxed font-body">
              {t("ecosystem.cards.videogen.whitelabel.body")}
            </p>
            <Button
              type="button"
              variant="outline"
              className="mt-3 border-cyan-500/50 text-cyan-200 hover:bg-cyan-500/15"
              onClick={onContactB2B}
              data-testid="videogen-b2b-cta"
            >
              {t("ecosystem.cards.videogen.whitelabel.cta")}
            </Button>
          </div>
        </div>
      </div>
    </motion.section>
  );
}
