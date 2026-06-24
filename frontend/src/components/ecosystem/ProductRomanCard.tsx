/**
 * ProductRomanCard — Card 1 of the ecosystem (the novel).
 *
 * Visual hero: roman-couverture.webp dominates a large left column on
 * desktop. The inside-pages photo appears as a smaller, slightly
 * inset secondary visual to prove the book is a real, printed object.
 * The Instagram / YouTube CTAs are visible with a "Bientôt" badge
 * (account placeholders for now, swappable to real handles later).
 */
import { Instagram, Youtube, BookOpen, Mail } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useI18n } from "@/i18n/I18nProvider";

interface Props {
  onJoinGenesis: () => void;
  onSoonClick: () => void;
  instagramUrl: string;
  youtubeUrl: string;
  hasRealSocials: boolean;
}

export function ProductRomanCard({
  onJoinGenesis,
  onSoonClick,
  instagramUrl,
  youtubeUrl,
  hasRealSocials,
}: Props): JSX.Element {
  const { t } = useI18n();

  const handleSocialClick =
    (url: string) => (e: React.MouseEvent<HTMLAnchorElement>) => {
      if (!hasRealSocials) {
        e.preventDefault();
        onSoonClick();
      } else if (!url) {
        e.preventDefault();
      }
    };

  return (
    <motion.section
      id="roman"
      data-testid="product-roman-card"
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="relative rounded-2xl border border-border bg-card/60 backdrop-blur-sm shadow-[0_2px_0_rgba(0,0,0,0.10),_0_18px_50px_rgba(0,0,0,0.18)] overflow-hidden"
    >
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-0">
        {/* Visual column */}
        <div className="lg:col-span-6 relative bg-[#0B0D10]">
          <div className="relative aspect-[4/5] lg:aspect-auto lg:h-full overflow-hidden">
            <picture>
              <source
                srcSet="/assets/products/roman-couverture.webp"
                type="image/webp"
              />
              <img
                src="/assets/products/roman-couverture.jpg"
                alt={t("ecosystem.cards.roman.gallery.cover")}
                className="absolute inset-0 w-full h-full object-cover"
                loading="lazy"
                data-testid="roman-cover-img"
              />
            </picture>
            {/* Inside-pages inset (proof-of-physical-book) */}
            <div
              className="hidden md:block absolute right-4 bottom-4 lg:right-6 lg:bottom-6 w-[42%] max-w-[260px] rounded-lg overflow-hidden border border-white/10 shadow-2xl"
              data-testid="roman-pages-inset"
            >
              <picture>
                <source
                  srcSet="/assets/products/roman-pages.webp"
                  type="image/webp"
                />
                <img
                  src="/assets/products/roman-pages.jpg"
                  alt={t("ecosystem.cards.roman.gallery.pages")}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              </picture>
            </div>
          </div>
        </div>

        {/* Copy column */}
        <div className="lg:col-span-6 p-7 sm:p-9 lg:p-12 flex flex-col gap-6">
          <div>
            <Badge
              variant="outline"
              className="font-mono text-[10px] uppercase tracking-[0.28em] border-amber-500/60 text-amber-400/95 bg-amber-500/5"
              data-testid="roman-badge"
            >
              {t("ecosystem.cards.roman.badge")}
            </Badge>
            <h2
              className="mt-4 font-display font-semibold text-3xl sm:text-4xl text-foreground tracking-tight"
              data-testid="roman-title"
            >
              {t("ecosystem.cards.roman.title")}
            </h2>
            <div className="mt-1 font-mono text-xs uppercase tracking-[0.20em] text-foreground/55">
              {t("ecosystem.cards.roman.subtitle")}
            </div>
          </div>

          <p className="text-sm md:text-base text-foreground/80 leading-relaxed max-w-prose">
            {t("ecosystem.cards.roman.pitch")}
          </p>

          {/* Episodes block (Instagram / YouTube) */}
          <div className="rounded-xl border border-border/70 bg-background/40 p-5">
            <div className="flex items-center gap-2 mb-3">
              <BookOpen className="h-4 w-4 text-amber-400/90" aria-hidden />
              <div className="font-mono text-[11px] uppercase tracking-[0.24em] text-foreground/80">
                {t("ecosystem.cards.roman.episodes.heading")}
              </div>
            </div>
            <p className="text-xs md:text-sm text-foreground/65 leading-relaxed">
              {t("ecosystem.cards.roman.episodes.body")}
            </p>
            <div className="mt-4 flex flex-col sm:flex-row gap-2">
              <a
                href={instagramUrl}
                target="_blank"
                rel="noopener noreferrer"
                onClick={handleSocialClick(instagramUrl)}
                className="group flex-1"
                data-testid="roman-instagram-link"
              >
                <Button
                  variant="secondary"
                  className="w-full justify-start gap-2 relative"
                  type="button"
                >
                  <Instagram className="h-4 w-4" aria-hidden />
                  <span>{t("ecosystem.cards.roman.episodes.instagramCta")}</span>
                  {!hasRealSocials && (
                    <span
                      className="ml-auto font-mono text-[9px] uppercase tracking-[0.18em] rounded-sm px-1.5 py-0.5 bg-amber-500/15 text-amber-400 border border-amber-500/30"
                      data-testid="roman-instagram-soon"
                    >
                      {t("ecosystem.cards.roman.episodes.soonBadge")}
                    </span>
                  )}
                </Button>
              </a>
              <a
                href={youtubeUrl}
                target="_blank"
                rel="noopener noreferrer"
                onClick={handleSocialClick(youtubeUrl)}
                className="group flex-1"
                data-testid="roman-youtube-link"
              >
                <Button
                  variant="secondary"
                  className="w-full justify-start gap-2 relative"
                  type="button"
                >
                  <Youtube className="h-4 w-4" aria-hidden />
                  <span>{t("ecosystem.cards.roman.episodes.youtubeCta")}</span>
                  {!hasRealSocials && (
                    <span
                      className="ml-auto font-mono text-[9px] uppercase tracking-[0.18em] rounded-sm px-1.5 py-0.5 bg-amber-500/15 text-amber-400 border border-amber-500/30"
                      data-testid="roman-youtube-soon"
                    >
                      {t("ecosystem.cards.roman.episodes.soonBadge")}
                    </span>
                  )}
                </Button>
              </a>
            </div>
          </div>

          <div className="text-xs leading-relaxed text-foreground/55 max-w-prose font-body">
            {t("ecosystem.cards.roman.fullEdition")}
          </div>

          <div className="mt-auto">
            <Button
              type="button"
              onClick={onJoinGenesis}
              className="gap-2 bg-amber-500/95 hover:bg-amber-500 text-zinc-950 font-medium"
              data-testid="roman-genesis-cta"
            >
              <Mail className="h-4 w-4" aria-hidden />
              {t("ecosystem.cards.roman.cta")}
            </Button>
          </div>
        </div>
      </div>
    </motion.section>
  );
}
