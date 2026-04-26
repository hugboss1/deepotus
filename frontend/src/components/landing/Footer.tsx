/**
 * Footer — bottom of every landing page.
 *
 * Migrated from .jsx → .tsx (Sprint 5 TS migration).
 * Pure presentational, no state — relies on the i18n provider for
 * copy.
 */
import { LanguageToggle } from "./LanguageToggle";
import ThemeToggle from "./ThemeToggle";
import { useI18n } from "@/i18n/I18nProvider";

export default function Footer() {
  const { t } = useI18n();
  return (
    <footer
      data-testid="footer"
      className="border-t border-border bg-[#0B0D10] text-zinc-200"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-8">
          <div className="max-w-md">
            <div className="font-display font-semibold text-lg text-white">
              $DEEPOTUS
            </div>
            <div className="mt-1 font-mono text-xs text-zinc-500 uppercase tracking-widest">
              {t("footer.tagline")}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <LanguageToggle />
          </div>
        </div>

        <div className="mt-10 rounded-xl border border-zinc-800 p-5 md:p-6 bg-[#0e141b]">
          <div
            data-testid="mica-disclaimer"
            className="font-mono text-[10px] uppercase tracking-[0.25em] text-[#F59E0B] mb-3"
          >
            ⚠ {t("footer.disclaimerTitle")}
          </div>
          <p className="text-xs md:text-[13px] leading-relaxed text-zinc-300">
            {t("footer.disclaimer")}
          </p>
        </div>

        <div className="mt-8 flex flex-col md:flex-row items-center justify-between gap-3 text-zinc-500 text-xs font-mono">
          <div>{t("footer.copyright")}</div>
          <div className="flex items-center gap-4">
            <a
              href="/stats"
              className="uppercase tracking-widest hover:text-zinc-200 transition-colors"
              data-testid="footer-public-stats-link"
            >
              → public stats
            </a>
            <span className="uppercase tracking-widest">
              /deep-state-potus · simulation
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
