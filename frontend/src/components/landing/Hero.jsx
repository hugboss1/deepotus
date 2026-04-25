/**
 * Hero — landing page top-of-fold orchestrator.
 *
 * Composed of three focused sub-components:
 *   - <HeroHeadline />  : left column copy, CTAs, mint terminal, mini-disclaimer
 *   - <HeroPoster />    : right poster with variant cycle + variant dots
 *   - <HeroCountdown /> : dual-state launch indicator (rendered inside HeroPoster)
 *
 * Keeping this file thin makes it trivial to A/B headlines or swap layouts
 * without touching presentational logic.
 */
import { HeroHeadline } from "./hero/HeroHeadline";
import { HeroPoster } from "./hero/HeroPoster";

export default function Hero() {
  return (
    <section
      id="top"
      data-testid="hero-section"
      className="relative overflow-hidden"
    >
      <div
        aria-hidden
        className="absolute inset-0 -z-10"
        style={{
          background:
            "linear-gradient(135deg, rgba(45,212,191,0.12) 0%, rgba(51,255,51,0.06) 45%, rgba(245,158,11,0.06) 100%), radial-gradient(60% 60% at 20% 10%, rgba(45,212,191,0.18) 0%, rgba(0,0,0,0) 60%)",
        }}
      />
      <div
        aria-hidden
        className="absolute inset-0 -z-10 opacity-[var(--noise-opacity)]"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/></filter><rect width='120' height='120' filter='url(%23n)' opacity='0.35'/></svg>\")",
        }}
      />

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 pb-16 md:pt-20 md:pb-24">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <HeroHeadline />
          <HeroPoster />
        </div>
      </div>
    </section>
  );
}
