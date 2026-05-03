import React, { useEffect } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
  ArrowLeft,
  Copy,
  Check,
  AlertTriangle,
  ExternalLink,
  Rocket,
  ShieldAlert,
} from "lucide-react";
import TopNav from "@/components/landing/TopNav";
import Footer from "@/components/landing/Footer";
import AccessSecuredTerminals from "@/components/landing/AccessSecuredTerminals";
import HowToBuyPhasedSteps from "@/components/landing/HowToBuyPhasedSteps";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useI18n } from "@/i18n/I18nProvider";
import {
  DEEPOTUS_MINT,
  isMintConfigured,
  getBuyUrl,
  isBuyUrlExternal,
  PUMPFUN_URL,
} from "@/lib/links";

/**
 * Cynical, in-character onboarding guide.
 * The Prophet walks a new disciple through the 4 rituals:
 *   01 · wallet · 02 · fund · 03 · pump.fun · 04 · buy
 * All copy is in translations.js under `howToBuy.*`.
 */
export default function HowToBuy() {
  const { t, lang } = useI18n();
  const [copied, setCopied] = React.useState(false);

  useEffect(() => {
    const prevTitle = document.title;
    document.title =
      lang === "fr"
        ? "$DEEPOTUS · Guide d'achat · PROTOCOL ΔΣ"
        : "$DEEPOTUS · Buy Guide · PROTOCOL ΔΣ";
    return () => {
      document.title = prevTitle;
    };
  }, [lang]);

  useEffect(() => {
    // Ensure we land at the top of the page when navigating in from a CTA.
    window.scrollTo({ top: 0, behavior: "instant" });
  }, []);

  const handleCopyMint = async () => {
    try {
      await navigator.clipboard.writeText(DEEPOTUS_MINT);
      setCopied(true);
      toast.success(t("hero.mintCopied") || "Copied");
      setTimeout(() => setCopied(false), 1800);
    } catch (_err) {
      toast.error("Copy failed");
    }
  };

  const steps = t("howToBuy.steps") || [];
  const preflight = t("howToBuy.preflightBullets") || [];
  const mintLive = isMintConfigured();
  const buyExternal = isBuyUrlExternal();

  return (
    <div className="relative">
      <TopNav />
      <main className="relative">
        {/* Ambient background — same palette as Hero */}
        <div
          aria-hidden
          className="absolute inset-x-0 top-0 h-[520px] -z-10"
          style={{
            background:
              "linear-gradient(135deg, rgba(45,212,191,0.12) 0%, rgba(51,255,51,0.06) 45%, rgba(245,158,11,0.06) 100%), radial-gradient(60% 60% at 20% 10%, rgba(45,212,191,0.18) 0%, rgba(0,0,0,0) 60%)",
          }}
        />
        <div
          aria-hidden
          className="absolute inset-x-0 top-0 h-[520px] -z-10 opacity-[var(--noise-opacity)]"
          style={{
            backgroundImage:
              "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/></filter><rect width='120' height='120' filter='url(%23n)' opacity='0.35'/></svg>\")",
          }}
        />

        {/* Back link */}
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors"
            data-testid="how-to-buy-back-link"
          >
            <ArrowLeft size={13} />
            {t("howToBuy.backCta")}
          </Link>
        </div>

        {/* Hero section */}
        <section
          id="how-to-buy-hero"
          data-testid="how-to-buy-hero"
          className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 pb-14 md:pt-12 md:pb-20"
        >
          <div className="mb-10">
            <HowToBuyPhasedSteps />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            {/* Copy */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="lg:col-span-7 order-2 lg:order-1"
            >
              <div className="flex items-center gap-2 mb-5 flex-wrap">
                <span
                  className="glitch-stamp"
                  data-text={t("howToBuy.kicker")}
                >
                  <ShieldAlert size={12} />
                  {t("howToBuy.kicker")}
                </span>
              </div>

              <h1 className="font-display font-bold leading-[1.02] text-4xl sm:text-5xl lg:text-6xl text-foreground">
                {t("howToBuy.title")}
              </h1>

              <p className="mt-5 text-base md:text-lg text-foreground/80 max-w-2xl leading-relaxed">
                {t("howToBuy.subtitle")}
              </p>

              {/* Mint address — also shown on this page for autonomous use */}
              <div
                className="mt-7 rounded-xl border border-border bg-card/70 p-3 sm:p-4 max-w-2xl"
                data-testid="how-to-buy-mint-block"
              >
                <div className="flex items-center justify-between gap-3 mb-2 flex-wrap">
                  <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
                    {t("hero.mintLabel")}
                  </div>
                  <span
                    className={`font-mono text-[9px] uppercase tracking-widest px-2 py-0.5 rounded-full border ${
                      mintLive
                        ? "border-[#18C964]/50 bg-[#18C964]/10 text-[#18C964]"
                        : "border-[#F59E0B]/50 bg-[#F59E0B]/10 text-[#F59E0B]"
                    }`}
                  >
                    {mintLive
                      ? t("hero.mintStatusLive")
                      : t("hero.mintStatusPlaceholder")}
                  </span>
                </div>
                <div className="flex items-stretch gap-2">
                  <code className="flex-1 min-w-0 font-mono text-[11px] sm:text-xs text-foreground/90 bg-background/60 border border-border rounded-md px-3 py-2 overflow-x-auto whitespace-nowrap tabular">
                    {DEEPOTUS_MINT}
                  </code>
                  <button
                    type="button"
                    onClick={handleCopyMint}
                    aria-label="Copy mint address"
                    data-testid="how-to-buy-mint-copy-button"
                    className={`shrink-0 inline-flex items-center gap-1.5 px-3 rounded-md font-mono text-[10px] uppercase tracking-widest border transition-colors ${
                      copied
                        ? "border-[#18C964]/60 bg-[#18C964]/15 text-[#18C964]"
                        : "border-border bg-background/60 text-foreground/80 hover:bg-muted hover:text-foreground"
                    }`}
                  >
                    {copied ? <Check size={12} /> : <Copy size={12} />}
                    <span>
                      {copied ? t("hero.mintCopied") : t("hero.mintCopy")}
                    </span>
                  </button>
                </div>
              </div>

              {/* Preflight checklist */}
              <div className="mt-8">
                <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-[#2DD4BF] mb-2">
                  {t("howToBuy.preflightTitle")}
                </div>
                <ul
                  className="space-y-2"
                  data-testid="how-to-buy-preflight-list"
                >
                  {Array.isArray(preflight) &&
                    preflight.map((b) => (
                      <li
                        key={b}
                        className="flex items-start gap-2 text-sm text-foreground/85"
                      >
                        <span className="mt-1.5 inline-block w-1.5 h-1.5 rounded-full bg-[#2DD4BF] shrink-0" />
                        <span className="leading-relaxed">{b}</span>
                      </li>
                    ))}
                </ul>
              </div>
            </motion.div>

            {/* Prophet illustration */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="lg:col-span-5 order-1 lg:order-2"
            >
              <div
                className="relative bg-card border border-border rounded-xl shadow-[var(--shadow-elev-2)] overflow-hidden scanlines noise"
                data-testid="how-to-buy-hero-image"
              >
                <div className="relative aspect-[4/5] w-full bg-[#0b1117]">
                  <img
                    src="/prophet_guide.png"
                    alt={t("howToBuy.heroImageAlt")}
                    className="absolute inset-0 w-full h-full object-cover poster-img"
                    loading="eager"
                    draggable={false}
                    onError={(e) => {
                      e.currentTarget.src = "/logo_v4_matrix_face.png";
                    }}
                  />
                  <div className="absolute top-3 left-3 z-10">
                    <div
                      className="glitch-stamp"
                      data-text={"AI-GENERATED"}
                    >
                      AI-GENERATED
                    </div>
                  </div>
                  <div className="absolute top-3 right-3 z-10">
                    <div
                      className="glitch-stamp"
                      data-text={"MENTOR MODE"}
                    >
                      MENTOR MODE
                    </div>
                  </div>
                  <div
                    aria-hidden
                    className="absolute inset-0 pointer-events-none"
                    style={{
                      background:
                        "linear-gradient(180deg, rgba(0,0,0,0.0) 55%, rgba(14,20,27,0.80) 100%)",
                    }}
                  />
                  <div className="absolute left-4 bottom-4 right-4 z-10 pointer-events-none">
                    <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-[#33ff33]">
                      &gt; MENTOR.LOG
                    </div>
                    <div className="font-display text-white text-base leading-tight mt-1">
                      {t("howToBuy.heroCaption")}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        <Separator />

        {/* Steps section */}
        <section
          id="how-to-buy-steps"
          data-testid="how-to-buy-steps"
          className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-14 sm:py-18 lg:py-24"
        >
          <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
            {t("howToBuy.stepsTitle")}
          </div>
          <h2 className="mt-2 font-display text-3xl md:text-4xl lg:text-5xl font-semibold leading-tight">
            {t("howToBuy.stepsSubtitle")}
          </h2>

          <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-5 lg:gap-6">
            {Array.isArray(steps) &&
              steps.map((s, idx) => (
                <motion.article
                  key={s.id || idx}
                  initial={{ opacity: 0, y: 12 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-80px" }}
                  transition={{ duration: 0.5, delay: idx * 0.05 }}
                  className="rounded-xl border border-border bg-card p-5 md:p-6 flex flex-col gap-4 h-full"
                  data-testid={`how-to-buy-step-${s.id || idx}`}
                >
                  <header>
                    <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-[#2DD4BF]">
                      {s.label}
                    </div>
                    <h3 className="mt-1.5 font-display font-semibold text-xl md:text-2xl leading-tight">
                      {s.title}
                    </h3>
                    {s.cynicalLead && (
                      <p className="mt-3 text-sm italic text-foreground/80 leading-relaxed border-l-2 border-[#2DD4BF]/40 pl-3">
                        {s.cynicalLead}
                      </p>
                    )}
                  </header>

                  <ol
                    className="space-y-2.5 list-none"
                    data-testid={`how-to-buy-step-${s.id || idx}-actions`}
                  >
                    {Array.isArray(s.actions) &&
                      s.actions.map((a: string, i: number) => (
                        <li
                          key={`htb-${s.id || idx}-action-${i}-${(a || "").slice(0, 16)}`}
                          className="flex items-start gap-3 text-sm text-foreground/90"
                        >
                          <span className="shrink-0 mt-0.5 w-5 h-5 rounded-full border border-border bg-background/60 font-mono text-[10px] flex items-center justify-center tabular text-foreground/80">
                            {String(i + 1).padStart(2, "0")}
                          </span>
                          <span className="leading-relaxed">{a}</span>
                        </li>
                      ))}
                  </ol>

                  {s.warning && (
                    <div
                      className="mt-auto rounded-md border border-[#E11D48]/40 bg-[#E11D48]/5 px-3 py-2.5 flex items-start gap-2"
                      data-testid={`how-to-buy-step-${s.id || idx}-warning`}
                    >
                      <AlertTriangle
                        size={14}
                        className="text-[#E11D48] shrink-0 mt-0.5"
                      />
                      <p className="text-xs text-foreground/85 leading-relaxed">
                        {s.warning}
                      </p>
                    </div>
                  )}
                </motion.article>
              ))}
          </div>
        </section>

        {/* Final CTA */}
        <section
          id="how-to-buy-cta"
          data-testid="how-to-buy-cta-section"
          className="border-t border-border bg-secondary/30"
        >
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-14 sm:py-18 lg:py-20">
            <div className="rounded-xl border border-border bg-card p-6 md:p-8">
              <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-[#2DD4BF]">
                {t("howToBuy.kicker")}
              </div>
              <h2 className="mt-2 font-display text-2xl md:text-3xl lg:text-4xl font-semibold leading-tight">
                {t("howToBuy.ctaTitle")}
              </h2>
              <p className="mt-3 text-sm md:text-base text-foreground/85 leading-relaxed max-w-3xl">
                {t("howToBuy.ctaSubtitle")}
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Button
                  asChild
                  size="lg"
                  className="rounded-[var(--btn-radius)] btn-press font-semibold"
                  data-testid="how-to-buy-cta-primary"
                >
                  <a
                    href={getBuyUrl()}
                    target={buyExternal ? "_blank" : undefined}
                    rel={buyExternal ? "noopener noreferrer" : undefined}
                  >
                    <Rocket size={16} className="mr-1" />
                    {t("howToBuy.ctaPrimary")}
                    {buyExternal && (
                      <ExternalLink size={13} className="ml-1 opacity-80" />
                    )}
                  </a>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="rounded-[var(--btn-radius)] btn-press font-semibold"
                  data-testid="how-to-buy-cta-secondary"
                >
                  <Link to="/#whitelist">{t("howToBuy.ctaSecondary")}</Link>
                </Button>
              </div>
              {!PUMPFUN_URL && (
                <p className="mt-3 font-mono text-[10px] text-muted-foreground">
                  {t("howToBuy.ctaPrelaunchNote")}
                </p>
              )}

              <div className="mt-8 pt-6 border-t border-border">
                <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-[#F59E0B] mb-2">
                  ⚠ {t("howToBuy.disclaimerTitle")}
                </div>
                <p className="text-xs md:text-[13px] leading-relaxed text-foreground/75">
                  {t("howToBuy.disclaimer")}
                </p>
              </div>
            </div>
          </div>
        </section>
        <AccessSecuredTerminals />
      </main>
      <Footer />
    </div>
  );
}
