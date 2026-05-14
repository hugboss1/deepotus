/**
 * MissionsSection — landing preview teaser for the Missions Hub.
 *
 * Shows up to 3 featured missions (Operation 001, Protocol 002,
 * Directive 003) with a clear "see all dossiers" CTA into /missions.
 * Also surfaces the May 20 giveaway via an inline chip so a visitor
 * skimming the landing instantly knows there is a reward window.
 *
 * Intentionally LESS dense than the /missions page — mission cards
 * here are 1-line teasers + family icon, never the full brief. That
 * forces the click into the dedicated hub.
 */
import React from "react";
import { Link } from "react-router-dom";
import { ArrowRight, FileLock2, Lock, Megaphone, Radar, Target, Wallet } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";
import { FEATURED_MISSION_KEYS, MISSIONS, type MissionFamily } from "@/lib/missions";

const FAMILY_ICON: Record<MissionFamily, LucideIcon> = {
  infiltration: Target,
  liquidity: Wallet,
  amplification: Megaphone,
  archive: FileLock2,
  signal: Radar,
  classified: Lock,
};
const FAMILY_ACCENT: Record<MissionFamily, string> = {
  infiltration: "#F59E0B",
  liquidity: "#33FF66",
  amplification: "#E11D48",
  archive: "#22D3EE",
  signal: "#A78BFA",
  classified: "#FF3B3B",
};

export const MissionsSection: React.FC = () => {
  const { t } = useI18n();
  const featured = MISSIONS.filter((m) => FEATURED_MISSION_KEYS.includes(m.id));

  return (
    <section
      id="missions"
      className="max-w-6xl mx-auto px-4 sm:px-6 py-16 sm:py-20"
      data-testid="landing-missions-section"
    >
      <div className="flex items-end justify-between flex-wrap gap-4 mb-7">
        <div>
          <p className="text-[11px] uppercase tracking-[0.25em] text-[#FF3B3B] font-mono">
            {t("missionsPage.hero.kicker") as string}
          </p>
          <h2 className="mt-2 font-display text-2xl sm:text-3xl lg:text-4xl font-semibold leading-tight tracking-tight">
            {t("missionsPage.hero.title") as string}
          </h2>
        </div>
        <Link
          to="/missions"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-md border border-foreground/20 hover:border-foreground/50 font-mono text-xs uppercase tracking-[0.18em] transition-colors"
          data-testid="landing-missions-see-all"
        >
          {t("missionsPage.list.sectionTitle") as string} <ArrowRight size={12} />
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-4">
        {featured.map((m) => {
          const Icon = FAMILY_ICON[m.family];
          const accent = FAMILY_ACCENT[m.family];
          return (
            <Link
              key={m.id}
              to="/missions"
              className="group rounded-md border bg-background overflow-hidden transition-transform hover:-translate-y-0.5"
              style={{ borderColor: accent + "40", boxShadow: `0 0 22px -14px ${accent}99` }}
              data-testid={`landing-mission-teaser-${m.id}`}
            >
              {/* Thumbnail — same illustration as the /missions hub, but
                  rendered as a 16:9 strip on the landing teaser to keep
                  the section dense. WebP first / JPG fallback. */}
              <div className="relative w-full aspect-[16/9] bg-black overflow-hidden">
                <picture>
                  <source srcSet={`/missions/mission_${m.id}.webp`} type="image/webp" />
                  <img
                    src={`/missions/mission_${m.id}.jpg`}
                    alt=""
                    loading="lazy"
                    decoding="async"
                    className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-[1.06]"
                  />
                </picture>
                <div
                  aria-hidden
                  className="absolute inset-0 pointer-events-none"
                  style={{
                    background: `linear-gradient(180deg, rgba(0,0,0,0) 55%, rgba(0,0,0,0.85) 100%)`,
                  }}
                />
                {/* Floating dossier ref + icon, anchored bottom-left so
                    they don't clash with the illustration's subject. */}
                <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between">
                  <span className="font-mono text-[10px] uppercase tracking-[0.22em] px-1.5 py-0.5 rounded-sm bg-black/55 backdrop-blur-[2px]" style={{ color: accent }}>
                    {m.dossierRef}
                  </span>
                  <Icon size={14} style={{ color: accent }} />
                </div>
              </div>

              <div className="p-4 sm:p-5">
                <h3 className="font-display text-base sm:text-lg font-semibold tracking-tight leading-snug">
                  {t(`missionsPage.cards.${m.i18nKey}.title`) as string}
                </h3>
                <p className="mt-2 text-xs text-foreground/65 leading-relaxed line-clamp-3">
                  {t(`missionsPage.cards.${m.i18nKey}.brief`) as string}
                </p>
                <div className="mt-4 inline-flex items-center gap-1 font-mono text-[11px] uppercase tracking-widest" style={{ color: accent }}>
                  {t("missionsPage.teaserCta") as string}
                  <ArrowRight size={11} className="transition-transform group-hover:translate-x-0.5" />
                </div>
              </div>
            </Link>
          );
        })}
      </div>

      {/* Inline giveaway chip — quick redirect for users who skim. */}
      <Link
        to="/giveaway"
        className="mt-6 inline-flex items-center gap-2 px-4 py-2 rounded-sm border border-[#F59E0B]/45 bg-[#F59E0B]/10 text-[#F59E0B] font-mono text-[11px] uppercase tracking-[0.22em] hover:bg-[#F59E0B]/20 transition-colors"
        data-testid="landing-missions-giveaway-chip"
      >
        ★ {t("missionsPage.giveawayCta.kicker") as string}
        <ArrowRight size={11} />
      </Link>
    </section>
  );
};

export default MissionsSection;
