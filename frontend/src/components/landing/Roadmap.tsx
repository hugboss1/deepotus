import React from "react";
import { motion } from "framer-motion";
import {
  Rocket,
  Layers,
  Banknote,
  Flag,
  Stamp,
  ShieldAlert,
  Lock,
  Radio,
  Heart,
  Sparkles,
  CheckCheck,
} from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";
import { getLaunchPhase, hasMint, URLS } from "@/lib/launchPhase";

const ICONS = [Rocket, Layers, Banknote, Flag, Heart, Sparkles];

// ----------------------------------------------------------------------------
// Status → visual mapping (color-coded "dossier" badges).
// Mirrors the rest of the site (terminal-green for "live", amber for warning,
// campaign-red for classified, ocean for queued/idle).
// ----------------------------------------------------------------------------
const STATUS_STYLES = {
  done: {
    color: "#33FF33",
    softBg: "rgba(51,255,51,0.10)",
    border: "rgba(51,255,51,0.55)",
    glow: "0 0 0 1px rgba(51,255,51,0.25), 0 8px 32px rgba(51,255,51,0.12)",
    Icon: CheckCheck,
    pulse: false,
  },
  next: {
    color: "#33FF33",
    softBg: "rgba(51,255,51,0.10)",
    border: "rgba(51,255,51,0.55)",
    glow: "0 0 0 1px rgba(51,255,51,0.25), 0 8px 32px rgba(51,255,51,0.12)",
    Icon: Radio,
    pulse: true,
  },
  active: {
    color: "#F59E0B",
    softBg: "rgba(245,158,11,0.10)",
    border: "rgba(245,158,11,0.55)",
    glow: "0 0 0 1px rgba(245,158,11,0.25), 0 8px 32px rgba(245,158,11,0.12)",
    Icon: Radio,
    pulse: true,
  },
  queued: {
    color: "#2DD4BF",
    softBg: "rgba(45,212,191,0.10)",
    border: "rgba(45,212,191,0.55)",
    glow: "0 0 0 1px rgba(45,212,191,0.20), 0 6px 24px rgba(45,212,191,0.10)",
    Icon: Stamp,
    pulse: false,
  },
  encrypted: {
    color: "#F59E0B",
    softBg: "rgba(245,158,11,0.10)",
    border: "rgba(245,158,11,0.55)",
    glow: "0 0 0 1px rgba(245,158,11,0.20), 0 6px 24px rgba(245,158,11,0.10)",
    Icon: Lock,
    pulse: false,
  },
  classified: {
    color: "#E11D48",
    softBg: "rgba(225,29,72,0.10)",
    border: "rgba(225,29,72,0.55)",
    glow: "0 0 0 1px rgba(225,29,72,0.20), 0 6px 24px rgba(225,29,72,0.10)",
    Icon: ShieldAlert,
    pulse: false,
  },
};

/**
 * Resolve the current status of each roadmap phase from the env-driven
 * launch phase. Hardcoded fallbacks where on-chain progress cannot be
 * detected automatically.
 *
 * Mapping:
 *   Phase 0 (Foundation)   → always "done" (the site you're looking at)
 *   Phase 1 (Mint)         → "active" if mint set, "next" otherwise
 *   Phase 2 (Graduation)   → "done" if PUMPSWAP set, "next" if mint set
 *                            but not graduated, "queued" otherwise
 *   Phase 3-5              → "queued" (manual flip via REACT_APP_PHASE_*_DONE
 *                            for future automation; "encrypted" by default).
 *
 * The status coming from i18n is treated as a default fallback so editors
 * can still hand-author surprise states, but the env override always wins
 * when set.
 */
function deriveStatuses() {
  const phase = getLaunchPhase();
  const mintSet = hasMint();
  const graduated = phase === "graduated" || Boolean(URLS.pumpswap);
  return [
    "done", // Phase 0 — Foundation
    mintSet ? (graduated ? "done" : "active") : "next", // Phase 1 — Mint
    graduated ? "done" : mintSet ? "next" : "queued", // Phase 2 — Graduation
    "encrypted", // Phase 3 — Expansion (J+30)
    "encrypted", // Phase 4 — Charity (J+60)
    "encrypted", // Phase 5 — Protocol ΔΣ (J+90)
  ];
}

function StatusBadge({ status, label }) {
  const s = STATUS_STYLES[status] || STATUS_STYLES.queued;
  const Icon = s.Icon;
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full font-mono text-[9px] uppercase tracking-[0.22em]"
      style={{
        color: s.color,
        background: s.softBg,
        border: `1px solid ${s.border}`,
      }}
      data-testid={`roadmap-status-${status}`}
    >
      {s.pulse ? (
        <span className="relative inline-flex w-1.5 h-1.5">
          <span
            className="absolute inset-0 inline-block w-1.5 h-1.5 rounded-full animate-ping opacity-70"
            style={{ background: s.color }}
          />
          <span
            className="relative inline-block w-1.5 h-1.5 rounded-full"
            style={{ background: s.color }}
          />
        </span>
      ) : (
        <Icon size={10} />
      )}
      <span>{label}</span>
    </span>
  );
}

export default function Roadmap() {
  const { t } = useI18n();
  const phases = t("roadmap.phases") || [];
  const legend = t("roadmap.legend") || {};
  const stamps = t("roadmap.stamps") || {};
  const subtitle = t("roadmap.subtitle");
  const dynamicStatuses = deriveStatuses();

  return (
    <section
      id="roadmap"
      data-testid="roadmap-section"
      className="relative py-14 sm:py-18 lg:py-24 border-t border-border overflow-hidden"
    >
      {/* Subtle terminal grid background */}
      <div
        aria-hidden
        className="absolute inset-0 -z-10 opacity-[0.04] pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.6) 1px, transparent 1px)",
          backgroundSize: "44px 44px",
        }}
      />

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <div className="flex items-end justify-between flex-wrap gap-4">
          <div>
            <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
              {t("roadmap.kicker")}
            </div>
            <h2 className="mt-2 font-display text-3xl md:text-4xl lg:text-5xl font-semibold leading-tight">
              {t("roadmap.title")}
            </h2>
            {subtitle ? (
              <p className="mt-3 max-w-2xl text-sm md:text-base text-foreground/75 leading-relaxed">
                {subtitle}
              </p>
            ) : null}
          </div>

          {/* Top-right "operational doctrine" stamp */}
          <div
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-card/60 font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground"
            data-testid="roadmap-doctrine-stamp"
          >
            <Stamp size={11} className="text-[#E11D48]" />
            DOCTRINE OPÉRATIONNELLE · ΔΣ
          </div>
        </div>

        {/* ---------- Timeline ---------- */}
        <div className="relative mt-12">
          {/* Desktop horizontal connector with multi-stop gradient */}
          <div
            aria-hidden
            className="hidden md:block absolute top-[34px] left-2 right-2 h-px"
            style={{
              background:
                "linear-gradient(90deg, rgba(51,255,51,0.7) 0%, rgba(45,212,191,0.7) 33%, rgba(245,158,11,0.7) 66%, rgba(225,29,72,0.7) 100%)",
              boxShadow: "0 0 16px rgba(45,212,191,0.18)",
            }}
          />

          {/* Mobile vertical connector */}
          <div
            aria-hidden
            className="md:hidden absolute top-0 bottom-0 left-[26px] w-px"
            style={{
              background:
                "linear-gradient(180deg, rgba(51,255,51,0.65) 0%, rgba(45,212,191,0.65) 33%, rgba(245,158,11,0.65) 66%, rgba(225,29,72,0.65) 100%)",
              boxShadow: "0 0 12px rgba(45,212,191,0.18)",
            }}
          />

          <ol
            className="relative grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-6 md:gap-5 list-none"
            data-testid="roadmap-list"
          >
            {phases.map((p, i) => {
              const Icon = ICONS[i] || Rocket;
              // Env-driven status overrides any value baked into i18n.
              const status = dynamicStatuses[i] || p.status || "queued";
              const s = STATUS_STYLES[status] || STATUS_STYLES.queued;
              const statusLabel =
                legend[status] || legend.queued || status.toUpperCase();
              const stampLabel =
                status === "next"
                  ? stamps.opened
                  : status === "classified"
                    ? stamps.sealed
                    : stamps.signed;

              return (
                <motion.li
                  key={`phase-${p.code || p.tag || i}-${(p.title || "").slice(0, 16)}`}
                  initial={{ opacity: 0, y: 14 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-60px" }}
                  transition={{ duration: 0.5, delay: i * 0.06 }}
                  className="relative pl-14 md:pl-0"
                  data-testid={`roadmap-phase-${i}`}
                >
                  {/* Mobile: left-anchored node on the vertical connector */}
                  <div
                    aria-hidden
                    className="md:hidden absolute left-[12px] top-2 w-7 h-7 rounded-full bg-background border-2 flex items-center justify-center"
                    style={{ borderColor: s.color, color: s.color }}
                  >
                    <Icon size={12} />
                  </div>

                  {/* Desktop: top icon node on horizontal connector */}
                  <div className="hidden md:flex items-center justify-between mb-3">
                    <div
                      aria-hidden
                      className="w-12 h-12 rounded-xl bg-background border-2 flex items-center justify-center"
                      style={{
                        borderColor: s.color,
                        color: s.color,
                        boxShadow: s.glow,
                      }}
                    >
                      <Icon size={18} />
                    </div>
                    <span
                      className="font-mono text-[10px] uppercase tracking-[0.22em] opacity-80"
                      style={{ color: s.color }}
                      data-testid={`roadmap-code-${i}`}
                    >
                      {p.code}
                    </span>
                  </div>

                  {/* Card */}
                  <article
                    className="relative rounded-xl border border-border bg-card/70 backdrop-blur-sm p-4 sm:p-5 hover:border-foreground/30 transition-colors"
                    style={{ boxShadow: s.glow }}
                  >
                    {/* Mobile only: code + status row (top of card) */}
                    <div className="md:hidden flex items-center justify-between mb-3">
                      <span
                        className="font-mono text-[10px] uppercase tracking-[0.22em] opacity-80"
                        style={{ color: s.color }}
                      >
                        {p.code}
                      </span>
                      <StatusBadge status={status} label={statusLabel} />
                    </div>

                    {/* Desktop only: status badge top-right */}
                    <div className="hidden md:flex justify-end mb-2">
                      <StatusBadge status={status} label={statusLabel} />
                    </div>

                    <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
                      {p.tag}
                    </div>
                    <h3 className="mt-1 font-display font-semibold text-lg leading-tight">
                      {p.title}
                    </h3>
                    {p.subtitle ? (
                      <p className="mt-1 text-[12.5px] text-foreground/65 italic leading-snug">
                        {p.subtitle}
                      </p>
                    ) : null}

                    <ul className="mt-4 space-y-2 text-sm text-foreground/85">
                      {(p.bullets || []).map((b, j) => (
                        <li
                          key={`${p.code || p.tag || i}-bullet-${j}-${(b || "").slice(0, 12)}`}
                          className="flex gap-2"
                        >
                          <span
                            className="font-mono mt-0.5 select-none"
                            style={{ color: s.color }}
                            aria-hidden
                          >
                            ›
                          </span>
                          <span className="leading-snug">{b}</span>
                        </li>
                      ))}
                    </ul>

                    {/* Footer stamp */}
                    <div className="mt-5 pt-3 border-t border-border/70 flex items-center justify-between">
                      <span className="font-mono text-[9px] uppercase tracking-[0.25em] text-muted-foreground">
                        {stampLabel}
                      </span>
                      <span
                        className="font-mono text-[9px] uppercase tracking-[0.25em]"
                        style={{ color: s.color }}
                      >
                        ΔΣ
                      </span>
                    </div>
                  </article>
                </motion.li>
              );
            })}
          </ol>
        </div>
      </div>
    </section>
  );
}
