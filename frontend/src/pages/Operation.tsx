import React, { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, ArrowLeft, ExternalLink, Lock, Rocket, Unlock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n/I18nProvider";
import TopNav from "@/components/landing/TopNav";
import Footer from "@/components/landing/Footer";
import { logger } from "@/lib/logger";

const API = process.env.REACT_APP_BACKEND_URL;

function useCountdown(targetIso: string | null | undefined) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  if (!targetIso) return { d: 0, h: 0, m: 0, s: 0, over: true };
  const target = new Date(targetIso).getTime();
  const diff = Math.max(0, target - now);
  const over = diff <= 0;
  const d = Math.floor(diff / (1000 * 60 * 60 * 24));
  const h = Math.floor((diff / (1000 * 60 * 60)) % 24);
  const m = Math.floor((diff / (1000 * 60)) % 60);
  const s = Math.floor((diff / 1000) % 60);
  return { d, h, m, s, over };
}

export default function Operation() {
  const { t, lang } = useI18n();
  const [reveal, setReveal] = useState(null);
  const [vault, setVault] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const [r1, r2] = await Promise.all([
          fetch(`${API}/api/operation/reveal`).then((r) => r.json()),
          fetch(`${API}/api/vault/state`).then((r) => r.json()),
        ]);
        if (!alive) return;
        setReveal(r1);
        setVault(r2);
      } catch (e) {
        logger.error("[operation] load error", e);
      } finally {
        if (alive) setLoading(false);
      }
    };
    load();
    const id = setInterval(load, 10000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  const unlocked = reveal?.unlocked === true;
  const countdown = useCountdown(reveal?.gencoin_launch_at);

  const lore = useMemo(() => {
    if (!reveal) return [];
    return lang === "fr" ? reveal.lore_fr || [] : reveal.lore_en || [];
  }, [reveal, lang]);

  const panic = useMemo(() => {
    if (!reveal) return "";
    return lang === "fr" ? reveal.panic_message_fr : reveal.panic_message_en;
  }, [reveal, lang]);

  const progressBuckets = Math.min(
    10,
    Math.floor(((vault?.progress_pct ?? 0) / 100) * 10)
  );

  return (
    <div className="relative min-h-screen">
      <TopNav />
      <main className="relative overflow-hidden">
        {/* Gate: vault still locked */}
        {!loading && !unlocked && (
          <section
            className="py-20 md:py-28"
            data-testid="operation-gate"
          >
            <div className="max-w-3xl mx-auto px-6 text-center">
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 font-mono text-[11px] uppercase tracking-[0.3em]"
              >
                <Lock size={14} /> {t("operation.gateTitle")}
              </motion.div>
              <h1 className="mt-6 font-display text-4xl md:text-6xl font-semibold leading-tight">
                PROTOCOL ΔΣ
              </h1>
              <p className="mt-4 text-lg text-foreground/80">
                {t("operation.gateSubtitle")}
              </p>
              <div className="mt-8">
                <div className="flex items-center justify-between mb-1.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                  <span>{t("operation.gateProgress")}</span>
                  <span>██░░ REDACTED</span>
                </div>
                <div className="h-3 w-full rounded-full bg-muted overflow-hidden">
                  <div className="flex h-full">
                    {Array.from({ length: 10 }).map((_, i) => (
                      <div
                        key={`operation-bucket-${i}`}
                        className={`flex-1 mx-px rounded-sm transition-colors duration-300 ${
                          i < progressBuckets
                            ? "bg-red-500/80"
                            : "bg-transparent"
                        }`}
                      />
                    ))}
                  </div>
                </div>
                <div className="mt-2 font-mono text-xs text-muted-foreground">
                  {vault?.digits_locked ?? 0}/{vault?.num_digits ?? 6} dials locked
                </div>
              </div>
              <div className="mt-8">
                <Button
                  asChild
                  variant="outline"
                  className="rounded-[var(--btn-radius)]"
                  data-testid="operation-gate-back"
                >
                  <a href="/#vault">
                    <ArrowLeft size={14} className="mr-1" /> {t("operation.gateCta")}
                  </a>
                </Button>
              </div>
            </div>
          </section>
        )}

        {/* Declassified reveal */}
        {!loading && unlocked && (
          <>
            {/* Panic banner */}
            <section className="py-16 md:py-24 relative" data-testid="operation-reveal">
              {/* Background flares */}
              <div className="absolute inset-0 pointer-events-none">
                <div className="absolute inset-0 opacity-[0.08] bg-[radial-gradient(circle_at_20%_20%,rgba(245,158,11,0.6),transparent_45%),radial-gradient(circle_at_80%_80%,rgba(24,201,100,0.6),transparent_45%)]" />
              </div>
              <div className="max-w-5xl mx-auto px-6 relative">
                <motion.div
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6 }}
                  className="inline-flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.3em] text-[#F59E0B] bg-[#F59E0B]/10 border border-[#F59E0B]/30 px-3 py-1.5 rounded-full"
                  data-testid="operation-panic-kicker"
                >
                  <AlertTriangle size={12} /> {t("operation.panicKicker")}
                </motion.div>

                <motion.h1
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.08 }}
                  className="mt-4 font-display text-4xl md:text-6xl font-semibold leading-[1.05] tracking-tight"
                  data-testid="operation-panic-title"
                >
                  {t("operation.panicTitle")}
                </motion.h1>

                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.6, delay: 0.2 }}
                  className="mt-3 font-mono text-xs uppercase tracking-[0.3em] text-muted-foreground"
                >
                  {t("operation.panicByline")}
                </motion.p>

                <motion.blockquote
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.3 }}
                  className="mt-8 pl-5 border-l-2 border-[#F59E0B] italic text-lg md:text-xl text-foreground/90 max-w-3xl"
                >
                  « {panic} »
                </motion.blockquote>

                {/* Cinematic illustration — the fall of the Deep State */}
                <motion.figure
                  initial={{ opacity: 0, scale: 0.98, y: 20 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: 0.5 }}
                  className="mt-12 relative"
                  data-testid="operation-chased-illustration"
                >
                  <div className="relative overflow-hidden rounded-2xl border border-border shadow-[var(--shadow-elev-1)] bg-black">
                    <img
                      src="/prophet_chased.png"
                      alt={t("operation.chasedAlt")}
                      className="w-full h-auto object-cover"
                      loading="eager"
                      draggable={false}
                    />
                    {/* Corner overlay tags */}
                    <div className="absolute top-3 left-3 flex items-center gap-2 px-2.5 py-1 rounded-md bg-black/60 border border-white/10 backdrop-blur-sm">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#E3D99F] animate-pulse" />
                      <span className="font-mono text-[9px] md:text-[10px] uppercase tracking-[0.25em] text-white/90">
                        {t("operation.chasedOverlay")}
                      </span>
                    </div>
                    <div className="absolute bottom-3 right-3 px-2.5 py-1 rounded-md bg-black/60 border border-white/10 backdrop-blur-sm">
                      <span className="font-mono text-[9px] md:text-[10px] uppercase tracking-[0.25em] text-[#E3D99F]">
                        AI-GENERATED · THE PEOPLE RISES
                      </span>
                    </div>
                  </div>
                  <figcaption className="mt-3 font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
                    ⸻ {t("operation.chasedCaption")}
                  </figcaption>
                </motion.figure>

                {/* Lore */}
                <div className="mt-12" data-testid="operation-lore">
                  <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
                    — {t("operation.loreTitle")}
                  </div>
                  <div className="mt-4 space-y-4 max-w-3xl text-foreground/85 leading-relaxed">
                    {lore.map((line: string, i: number) => (
                      <motion.p
                        key={`lore-${lang}-${i}-${(line || "").slice(0, 16)}`}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.4, delay: 0.2 + i * 0.08 }}
                      >
                        {line}
                      </motion.p>
                    ))}
                  </div>
                </div>
              </div>
            </section>

            {/* Countdown to GENCOIN */}
            <section
              className="py-16 md:py-20 border-t border-border"
              data-testid="operation-countdown"
            >
              <div className="max-w-5xl mx-auto px-6">
                <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
                  {t("operation.countdownKicker")}
                </div>
                <h2 className="mt-3 font-display text-3xl md:text-4xl font-semibold">
                  {t("operation.countdownTitle")}
                </h2>
                <p className="mt-3 text-foreground/75 max-w-2xl">
                  {t("operation.countdownSubtitle")}
                </p>
                <div
                  className="mt-8 grid grid-cols-4 gap-3 md:gap-5 max-w-2xl"
                  data-testid="operation-countdown-dials"
                >
                  {[
                    { k: "d", v: countdown.d },
                    { k: "h", v: countdown.h },
                    { k: "m", v: countdown.m },
                    { k: "s", v: countdown.s },
                  ].map((c) => (
                    <div
                      key={c.k}
                      className="flex flex-col items-center rounded-xl border border-border bg-card/70 backdrop-blur py-5"
                    >
                      <div className="font-mono text-3xl md:text-5xl font-bold text-[#18C964]">
                        {String(c.v).padStart(2, "0")}
                      </div>
                      <div className="mt-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                        {t(`operation.countdownLabels.${c.k}`)}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-8 flex flex-wrap items-center gap-3">
                  <Button
                    asChild
                    className="rounded-[var(--btn-radius)] bg-[#18C964] hover:bg-[#18C964]/90 text-black"
                    data-testid="operation-gencoin-cta"
                  >
                    <a
                      href={reveal?.gencoin_url || "#"}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Rocket size={14} className="mr-1" />
                      {t("operation.openCta")}
                      <ExternalLink size={12} className="ml-1" />
                    </a>
                  </Button>
                  <Button
                    asChild
                    variant="outline"
                    className="rounded-[var(--btn-radius)]"
                    data-testid="operation-back-cta"
                  >
                    <a href="/">
                      <ArrowLeft size={14} className="mr-1" />
                      {t("operation.backCta")}
                    </a>
                  </Button>
                </div>
                {reveal?.revealed_at && (
                  <div className="mt-6 font-mono text-[11px] text-muted-foreground">
                    — {t("operation.revealedAt")} :{" "}
                    <span className="text-foreground/80">
                      {new Date(reveal.revealed_at).toLocaleString()}
                    </span>
                  </div>
                )}
                <div className="mt-8 inline-flex items-center gap-2 text-[#18C964] font-mono text-xs">
                  <Unlock size={14} /> PROTOCOL ΔΣ · DECLASSIFIED
                </div>
              </div>
            </section>
          </>
        )}

        {loading && (
          <section className="py-24">
            <div className="max-w-3xl mx-auto px-6 text-center">
              <div className="font-mono text-sm text-muted-foreground">
                Transmitting…
              </div>
            </div>
          </section>
        )}
      </main>
      <Footer />
    </div>
  );
}
