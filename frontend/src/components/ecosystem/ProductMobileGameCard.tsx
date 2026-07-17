/**
 * ProductMobileGameCard — Card 4: mobile game + web version (live build).
 *
 * No image uploaded yet — we render a stylized hero illustration
 * generated entirely in SVG/CSS to preserve the brand mood (a dystopian
 * golden silhouette behind a deep-sea radial wash). Easy to replace by
 * <img/> later.
 */
import { useState } from "react";
import { motion } from "framer-motion";
import { Smartphone, Globe, BellRing, Bug, ChevronRight, Play } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n/I18nProvider";
import FragmentFilmOverlay from "./FragmentFilmOverlay";

interface Props {
  onJoinWaitlist: () => void;
}

export function ProductMobileGameCard({ onJoinWaitlist }: Props): JSX.Element {
  const { t } = useI18n();
  const [filmOpen, setFilmOpen] = useState<boolean>(false);

  return (
    <motion.section
      id="mobile"
      data-testid="product-mobile-card"
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="relative rounded-2xl border border-border bg-card/60 backdrop-blur-sm shadow-[0_2px_0_rgba(0,0,0,0.10),_0_18px_50px_rgba(0,0,0,0.18)] overflow-hidden"
    >
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-0">
        {/* Copy column */}
        <div className="lg:col-span-7 p-7 sm:p-9 lg:p-12 flex flex-col gap-6">
          <div>
            <Badge
              variant="outline"
              className="font-mono text-[10px] uppercase tracking-[0.28em] border-cyan-500/55 text-cyan-300/95 bg-cyan-500/5"
              data-testid="mobile-badge"
            >
              {t("ecosystem.cards.mobile.badge")}
            </Badge>
            <h2
              className="mt-4 font-display font-semibold text-3xl sm:text-4xl text-foreground tracking-tight"
              data-testid="mobile-title"
            >
              {t("ecosystem.cards.mobile.title")}
            </h2>
            <div className="mt-1 font-mono text-xs uppercase tracking-[0.20em] text-foreground/55">
              {t("ecosystem.cards.mobile.subtitle")}
            </div>
          </div>

          <p className="text-sm md:text-base text-foreground/80 leading-relaxed max-w-prose">
            {t("ecosystem.cards.mobile.pitch")}
          </p>

          {/* Live build block */}
          <div className="rounded-xl border border-cyan-500/25 bg-cyan-500/[0.05] p-5">
            <div className="flex items-center gap-2">
              <Bug className="h-4 w-4 text-cyan-300/90" aria-hidden />
              <div className="font-mono text-[11px] uppercase tracking-[0.24em] text-cyan-200/85">
                {t("ecosystem.cards.mobile.liveBuild.heading")}
              </div>
            </div>
            <p className="mt-2 text-sm text-foreground/80 leading-relaxed font-body">
              {t("ecosystem.cards.mobile.liveBuild.body")}
            </p>
          </div>

          {/* Platforms hint */}
          <ul className="flex flex-wrap gap-3 text-xs text-foreground/65">
            <li className="flex items-center gap-2 rounded-md border border-border/60 bg-background/30 px-3 py-2">
              <Smartphone className="h-3.5 w-3.5 text-foreground/55" aria-hidden /> Mobile
            </li>
            <li className="flex items-center gap-2 rounded-md border border-border/60 bg-background/30 px-3 py-2">
              <Globe className="h-3.5 w-3.5 text-foreground/55" aria-hidden /> Web
            </li>
          </ul>

          <div className="flex flex-col sm:flex-row gap-3 mt-auto">
            <Button
              type="button"
              size="lg"
              variant="secondary"
              className="gap-2"
              data-testid="mobile-follow-cta"
              onClick={onJoinWaitlist}
            >
              {t("ecosystem.cards.mobile.cta")}
              <ChevronRight className="h-4 w-4" aria-hidden />
            </Button>
            <Button
              type="button"
              size="lg"
              className="gap-2 bg-cyan-500/95 hover:bg-cyan-500 text-zinc-950 font-medium"
              data-testid="mobile-notify-cta"
              onClick={onJoinWaitlist}
            >
              <BellRing className="h-4 w-4" aria-hidden />
              {t("ecosystem.cards.mobile.notifyCta")}
            </Button>
          </div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-foreground/55">
            {t("ecosystem.cards.mobile.status")}
          </div>
        </div>

        {/* Generated illustration column — encart cliquable : lance le film
            scroll-cinéma « Fragment » (l'univers du jeu) en overlay plein écran. */}
        <button
          type="button"
          onClick={() => setFilmOpen(true)}
          aria-label={t("ecosystem.cards.mobile.film.cta") as string}
          className="group lg:col-span-5 relative min-h-[260px] lg:min-h-0 bg-[#070A0E] overflow-hidden cursor-pointer text-left block w-full"
          data-testid="mobile-film-encart"
        >
          {/* Aperçu du film : le globe orbital DEEPOTUS (première image du voyage) */}
          <img
            src="/fragment/assets/globe.jpg"
            alt=""
            aria-hidden
            className="absolute inset-0 w-full h-full object-cover object-[62%_18%] transition-transform duration-700 ease-out group-hover:scale-[1.05]"
            loading="lazy"
          />
          <span className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/15 to-transparent" aria-hidden />
          <span className="absolute inset-x-0 bottom-0 p-5 sm:p-6 flex items-center gap-4">
            <span className="relative inline-flex h-12 w-12 shrink-0 items-center justify-center">
              <span className="absolute inline-flex h-full w-full rounded-full bg-cyan-400/25 animate-ping" aria-hidden />
              <span className="relative inline-flex h-12 w-12 items-center justify-center rounded-full border border-cyan-400/60 bg-black/55 text-cyan-300 backdrop-blur-sm transition-transform duration-300 group-hover:scale-110">
                <Play className="h-5 w-5 translate-x-[1px]" aria-hidden />
              </span>
            </span>
            <span className="min-w-0">
              <span className="block font-display font-semibold text-foreground text-base sm:text-lg leading-tight">
                {t("ecosystem.cards.mobile.film.cta")}
              </span>
              <span className="mt-0.5 block font-mono text-[10px] uppercase tracking-[0.22em] text-cyan-300/80">
                {t("ecosystem.cards.mobile.film.hint")}
              </span>
            </span>
          </span>
        </button>
      </div>
      <FragmentFilmOverlay open={filmOpen} onClose={() => setFilmOpen(false)} />
    </motion.section>
  );
}
