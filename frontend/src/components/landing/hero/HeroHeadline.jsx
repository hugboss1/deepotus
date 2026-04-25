import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useI18n } from "@/i18n/I18nProvider";
import {
  getBuyUrl,
  isBuyUrlExternal,
  DEEPOTUS_MINT,
  isMintConfigured,
} from "@/lib/links";
import {
  Radio,
  ShieldAlert,
  Cpu,
  Coins,
  Copy,
  Check,
  HelpCircle,
} from "lucide-react";
import { useState } from "react";

/**
 * Left column of the Hero — stamps, headline, subtitle, chip row, dual CTA,
 * mint-address terminal block, and the mini disclaimer.
 *
 * Stateless from the parent's POV — only owns its own clipboard "copied"
 * flash so the parent does not have to manage transient micro-state.
 */
export function HeroHeadline() {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);

  const mintLive = isMintConfigured();

  const handleCopyMint = async () => {
    try {
      await navigator.clipboard.writeText(DEEPOTUS_MINT);
      setCopied(true);
      toast.success(t("hero.mintCopied") || "Copied");
      setTimeout(() => setCopied(false), 1800);
    } catch (_err) {
      // Fallback for older browsers / insecure contexts
      const ta = document.createElement("textarea");
      ta.value = DEEPOTUS_MINT;
      ta.setAttribute("readonly", "");
      ta.style.position = "absolute";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
        setCopied(true);
        toast.success(t("hero.mintCopied") || "Copied");
        setTimeout(() => setCopied(false), 1800);
      } catch (_err2) {
        toast.error("Copy failed");
      }
      document.body.removeChild(ta);
    }
  };

  return (
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
          <a
            href={getBuyUrl()}
            target={isBuyUrlExternal() ? "_blank" : undefined}
            rel={isBuyUrlExternal() ? "noopener noreferrer" : undefined}
          >
            {t("hero.buyCta")}
          </a>
        </Button>
      </div>

      {/* $DEEPOTUS mint address — copyable terminal block */}
      <div
        className="mt-6 rounded-xl border border-border bg-card/70 p-3 sm:p-4 max-w-2xl"
        data-testid="hero-mint-address"
      >
        <div className="flex items-center justify-between gap-3 mb-2">
          <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
            {t("hero.mintLabel")}
          </div>
          <span
            className={`font-mono text-[9px] uppercase tracking-widest px-2 py-0.5 rounded-full border ${
              mintLive
                ? "border-[#18C964]/50 bg-[#18C964]/10 text-[#18C964]"
                : "border-[#F59E0B]/50 bg-[#F59E0B]/10 text-[#F59E0B]"
            }`}
            data-testid="hero-mint-status"
          >
            {mintLive
              ? t("hero.mintStatusLive")
              : t("hero.mintStatusPlaceholder")}
          </span>
        </div>
        <div className="flex items-stretch gap-2">
          <code
            className="flex-1 min-w-0 font-mono text-[11px] sm:text-xs text-foreground/90 bg-background/60 border border-border rounded-md px-3 py-2 overflow-x-auto whitespace-nowrap tabular"
            data-testid="hero-mint-value"
            aria-label="$DEEPOTUS mint address"
          >
            {DEEPOTUS_MINT}
          </code>
          <button
            type="button"
            onClick={handleCopyMint}
            aria-label="Copy mint address"
            data-testid="hero-mint-copy-button"
            className={`shrink-0 inline-flex items-center gap-1.5 px-3 rounded-md font-mono text-[10px] uppercase tracking-widest border transition-colors ${
              copied
                ? "border-[#18C964]/60 bg-[#18C964]/15 text-[#18C964]"
                : "border-border bg-background/60 text-foreground/80 hover:bg-muted hover:text-foreground"
            }`}
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            <span>{copied ? t("hero.mintCopied") : t("hero.mintCopy")}</span>
          </button>
        </div>
        <div className="mt-2 flex items-center justify-between gap-3 flex-wrap">
          <div className="font-mono text-[10px] text-muted-foreground">
            {t("hero.mintHint")}
          </div>
          <Link
            to="/how-to-buy"
            className="inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-widest text-[#2DD4BF] hover:underline"
            data-testid="hero-mint-guide-link"
          >
            <HelpCircle size={11} />
            {t("hero.mintGuideCta")}
          </Link>
        </div>
      </div>

      <p className="mt-5 text-[11px] font-mono text-muted-foreground max-w-md leading-relaxed">
        {t("hero.miniDisclaimer")}
      </p>
    </motion.div>
  );
}

export default HeroHeadline;
