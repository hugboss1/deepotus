import React, { useEffect, useState } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useI18n } from "@/i18n/I18nProvider";
import { Radio, ShieldAlert, Cpu, Coins } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const HERO_VARIANTS = [
  { src: "/deepotus_hero_serious.jpg", label: "SERIOUS" },
  { src: "/deepotus_hero_meme.jpg", label: "MEME" },
  { src: "/deepotus_hero_glitch.jpg", label: "GLITCH" },
];
const CYCLE_MS = 5000;

function useCountdown(targetIso) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  if (!targetIso) return null;
  const target = new Date(targetIso).getTime();
  const diff = Math.max(0, target - now);
  const s = Math.floor(diff / 1000);
  const days = Math.floor(s / 86400);
  const hours = Math.floor((s % 86400) / 3600);
  const minutes = Math.floor((s % 3600) / 60);
  const seconds = s % 60;
  return { days, hours, minutes, seconds };
}

function Num({ value, label }) {
  return (
    <div className="text-center">
      <div className="tabular font-mono font-semibold text-2xl md:text-3xl text-foreground">
        {String(value).padStart(2, "0")}
      </div>
      <div className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground mt-1">
        {label}
      </div>
    </div>
  );
}

export default function Hero() {
  const { t } = useI18n();
  const [launchIso, setLaunchIso] = useState(null);
  const [variantIdx, setVariantIdx] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    axios
      .get(`${API}/stats`)
      .then((r) => setLaunchIso(r.data.launch_timestamp))
      .catch(() => {});
  }, []);

  // Preload all variants
  useEffect(() => {
    HERO_VARIANTS.forEach((v) => {
      const img = new Image();
      img.src = v.src;
    });
  }, []);

  // Auto-cycle through variants
  useEffect(() => {
    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    )?.matches;
    if (paused || reduceMotion) return;
    const id = setInterval(() => {
      setVariantIdx((i) => (i + 1) % HERO_VARIANTS.length);
    }, CYCLE_MS);
    return () => clearInterval(id);
  }, [paused]);

  const cd = useCountdown(launchIso);
  const currentVariant = HERO_VARIANTS[variantIdx];

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
          {/* Left copy */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="lg:col-span-7 order-2 lg:order-1"
          >
            <div className="flex items-center gap-2 mb-5 flex-wrap">
              <span className="glitch-stamp" data-text={t("hero.stamp")}>
                <Radio size={12} />
                {t("hero.stamp")}
              </span>
              <span className="glitch-stamp" data-text={t("hero.candidate")}>
                <ShieldAlert size={12} />
                {t("hero.candidate")}
              </span>
            </div>

            <h1 className="font-display font-bold leading-[0.95] text-5xl sm:text-6xl lg:text-7xl text-foreground">
              {t("hero.title")}{" "}
              <span className="relative inline-block">
                <span className="relative z-10 tabular">{t("hero.ticker")}</span>
                <span
                  aria-hidden
                  className="absolute -inset-x-1 bottom-1 h-3 -z-0"
                  style={{
                    background:
                      "linear-gradient(90deg, rgba(45,212,191,0.5), rgba(245,158,11,0.4))",
                  }}
                />
              </span>
            </h1>

            <p className="mt-5 text-base md:text-lg text-foreground/80 max-w-2xl">
              {t("hero.subtitle")}
            </p>

            <div className="mt-6 flex flex-wrap gap-2">
              <Badge variant="secondary" className="font-mono text-xs">
                <Coins size={12} className="mr-1" /> {t("hero.chips.chain")}
              </Badge>
              <Badge variant="secondary" className="font-mono text-xs">
                <Cpu size={12} className="mr-1" /> {t("hero.chips.supply")}
              </Badge>
              <Badge variant="secondary" className="font-mono text-xs">
                🏷️ {t("hero.chips.price")}
              </Badge>
              <Badge variant="secondary" className="font-mono text-xs">
                🎯 {t("hero.chips.goal")}
              </Badge>
            </div>

            <div className="mt-7 flex flex-wrap gap-3">
              <Button
                asChild
                size="lg"
                className="rounded-[var(--btn-radius)] btn-press font-semibold"
                data-testid="hero-join-button"
              >
                <a href="#whitelist">{t("hero.joinCta")}</a>
              </Button>
              <Button
                asChild
                size="lg"
                variant="outline"
                className="rounded-[var(--btn-radius)] btn-press font-semibold"
                data-testid="hero-buy-button"
              >
                <a href="#chat">{t("hero.buyCta")}</a>
              </Button>
            </div>

            <p className="mt-5 text-[11px] font-mono text-muted-foreground max-w-md leading-relaxed">
              {t("hero.miniDisclaimer")}
            </p>
          </motion.div>

          {/* Right poster card with variant cycle */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="lg:col-span-5 order-1 lg:order-2"
          >
            <div
              className="relative bg-card border border-border rounded-xl shadow-[var(--shadow-elev-2)] overflow-hidden scanlines noise"
              onMouseEnter={() => setPaused(true)}
              onMouseLeave={() => setPaused(false)}
              data-testid="hero-poster"
            >
              <div
                className="absolute top-3 left-3 z-10 glitch-stamp"
                data-text={"AI-GENERATED"}
              >
                AI-GENERATED
              </div>
              <div
                className="absolute bottom-3 right-3 z-10 glitch-stamp"
                data-text={currentVariant.label}
                data-testid="hero-variant-label"
              >
                {currentVariant.label}
              </div>

              <div className="relative aspect-[4/5] w-full bg-[#0b1117]">
                <AnimatePresence mode="sync">
                  <motion.img
                    key={currentVariant.src}
                    src={currentVariant.src}
                    alt="AI Prophet Deep State Candidate"
                    initial={{ opacity: 0, scale: 1.02 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.9, ease: "easeInOut" }}
                    className="absolute inset-0 w-full h-full object-cover poster-img"
                    loading="eager"
                    draggable={false}
                    onError={(e) => {
                      e.currentTarget.src = "/deepotus_hero.jpg";
                    }}
                  />
                </AnimatePresence>
                <div
                  aria-hidden
                  className="absolute inset-0 pointer-events-none"
                  style={{
                    background:
                      "linear-gradient(180deg, rgba(0,0,0,0.0) 55%, rgba(14,20,27,0.75) 100%)",
                  }}
                />
                <div className="absolute left-4 bottom-4 right-4 z-10 pointer-events-none">
                  <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-[#33ff33]">
                    &gt; CANDIDATE.LOG
                  </div>
                  <div className="font-display text-white text-lg leading-tight mt-1">
                    {t("hero.ticker")} · {t("hero.chips.chain")}
                  </div>
                </div>
              </div>

              {/* Variant dots */}
              <div className="flex items-center justify-center gap-2 py-2 bg-[#0b1117] border-t border-[#1f2937]">
                {HERO_VARIANTS.map((v, i) => {
                  const active = i === variantIdx;
                  return (
                    <button
                      key={v.src}
                      type="button"
                      aria-label={`Show variant ${v.label}`}
                      data-testid={`hero-variant-dot-${i}`}
                      onClick={() => setVariantIdx(i)}
                      className={`h-2 rounded-full transition-all ${
                        active
                          ? "w-6 bg-[#33ff33]"
                          : "w-2 bg-zinc-600 hover:bg-zinc-400"
                      }`}
                    />
                  );
                })}
              </div>

              <Separator />

              <div className="p-4">
                <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground mb-3 flex items-center gap-2">
                  <span className="inline-block w-2 h-2 rounded-full bg-[--campaign-red]" />
                  {t("hero.countdownLabel")}
                </div>
                <div
                  data-testid="hero-countdown"
                  className="grid grid-cols-4 gap-2"
                >
                  <Num value={cd?.days ?? 0} label={t("hero.days")} />
                  <Num value={cd?.hours ?? 0} label={t("hero.hours")} />
                  <Num value={cd?.minutes ?? 0} label={t("hero.minutes")} />
                  <Num value={cd?.seconds ?? 0} label={t("hero.seconds")} />
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
