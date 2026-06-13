/**
 * ProductVideoGenCard — Card 3 of the ecosystem (Video Generator).
 *
 * Visual: stylized mockup component (no real screenshot uploaded yet).
 * Includes the B2B white-label encart with a "Nous contacter" button
 * that opens the B2BInquiryDialog.
 */
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Wand2, Cpu, Mic, CalendarClock, Building2, ChevronRight, ShoppingCart, FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n/I18nProvider";
import { VideoGenAppMockup } from "./VideoGenAppMockup";

interface Props {
  onContactB2B: () => void;
}

export function ProductVideoGenCard({ onContactB2B }: Props): JSX.Element {
  const { t } = useI18n();
  const navigate = useNavigate();

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
        {/* Mockup column */}
        <div className="lg:col-span-6 p-6 sm:p-7 lg:p-10 bg-[#070A0E]">
          <VideoGenAppMockup />
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
