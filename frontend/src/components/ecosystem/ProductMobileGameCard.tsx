/**
 * ProductMobileGameCard — Card 4: mobile game + web version (live build).
 *
 * No image uploaded yet — we render a stylized hero illustration
 * generated entirely in SVG/CSS to preserve the brand mood (a dystopian
 * golden silhouette behind a deep-sea radial wash). Easy to replace by
 * <img/> later.
 */
import { motion } from "framer-motion";
import { Smartphone, Globe, BellRing, Bug, ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n/I18nProvider";

interface Props {
  onJoinWaitlist: () => void;
}

export function ProductMobileGameCard({ onJoinWaitlist }: Props): JSX.Element {
  const { t } = useI18n();

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

        {/* Generated illustration column */}
        <div
          className="lg:col-span-5 relative min-h-[260px] lg:min-h-0 bg-[#070A0E] overflow-hidden"
          data-testid="mobile-illustration"
        >
          <div
            aria-hidden
            className="absolute inset-0"
            style={{
              background:
                "radial-gradient(60% 60% at 30% 30%, rgba(45,212,191,0.18) 0%, rgba(245,158,11,0.10) 45%, rgba(0,0,0,0) 75%)",
            }}
          />
          <svg
            viewBox="0 0 320 480"
            className="relative w-full h-full"
            preserveAspectRatio="xMidYMid slice"
            aria-hidden
          >
            <defs>
              <radialGradient id="goldHalo" cx="50%" cy="35%" r="35%">
                <stop offset="0" stopColor="#F59E0B66" />
                <stop offset="1" stopColor="#F59E0B00" />
              </radialGradient>
              <linearGradient id="silh" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stopColor="#0b1119" />
                <stop offset="1" stopColor="#101820" />
              </linearGradient>
            </defs>
            <circle cx="160" cy="170" r="110" fill="url(#goldHalo)" />
            {/* Silhouette */}
            <circle cx="160" cy="165" r="42" fill="url(#silh)" stroke="#F59E0B33" />
            <path
              d="M85 470 C85 330, 235 330, 235 470 Z"
              fill="url(#silh)"
              stroke="#F59E0B33"
            />
            {/* Scanlines */}
            {Array.from({ length: 18 }).map((_, i) => (
              <line
                key={i}
                x1="0"
                x2="320"
                y1={i * 28}
                y2={i * 28}
                stroke="#F6F2EA08"
                strokeWidth="1"
              />
            ))}
          </svg>
          <div className="absolute bottom-3 left-4 font-mono text-[10px] uppercase tracking-[0.22em] text-amber-400/85">
            {t("ecosystem.cards.mobile.placeholder")}
          </div>
        </div>
      </div>
    </motion.section>
  );
}
