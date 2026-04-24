import React, { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LanguageToggle } from "./LanguageToggle";
import ThemeToggle from "./ThemeToggle";
import { useI18n } from "@/i18n/I18nProvider";
import { getBuyUrl, isBuyUrlExternal, PUMPFUN_URL } from "@/lib/links";

const NAV_ITEMS = [
  { id: "manifesto", key: "nav.manifesto" },
  { id: "vault", key: "nav.vault" },
  { id: "chat", key: "nav.chat" },
  { id: "mission", key: "nav.mission" },
  { id: "tokenomics", key: "nav.tokenomics" },
  { id: "transparency", key: "nav.transparency" },
  { id: "roadmap", key: "nav.roadmap" },
  { id: "faq", key: "nav.faq" },
];

export default function TopNav() {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      data-testid="top-nav"
      className={`sticky top-0 z-40 w-full transition-colors duration-200 ${
        scrolled
          ? "bg-background/80 backdrop-blur-md border-b border-border"
          : "bg-background/0"
      }`}
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-4">
        <a
          href="#top"
          className="font-display font-semibold tracking-tight text-base md:text-lg"
          data-testid="nav-logo"
        >
          <span className="text-foreground">$DEEPOTUS</span>
          <span className="hidden sm:inline text-muted-foreground text-xs ml-2 font-mono uppercase tracking-widest">
            /deep-state-potus
          </span>
        </a>

        <nav className="hidden lg:flex items-center gap-5 text-sm text-foreground/80">
          {NAV_ITEMS.map((it) => (
            <a
              key={it.id}
              href={`#${it.id}`}
              className="hover:text-foreground transition-colors"
              data-testid={`nav-link-${it.id}`}
            >
              {t(it.key)}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          <LanguageToggle />
          <Button
            asChild
            size="sm"
            className="hidden sm:inline-flex rounded-[var(--btn-radius)] btn-press"
            data-testid="nav-buy-button"
          >
            <a
              href={PUMPFUN_URL ? getBuyUrl() : "#whitelist"}
              target={isBuyUrlExternal() ? "_blank" : undefined}
              rel={isBuyUrlExternal() ? "noopener noreferrer" : undefined}
            >
              {PUMPFUN_URL ? t("hero.buyCta") : t("nav.join")}
            </a>
          </Button>
          <button
            className="lg:hidden p-2 rounded-md border border-border bg-background/60"
            aria-label="Menu"
            onClick={() => setOpen(!open)}
            data-testid="nav-mobile-toggle"
          >
            {open ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {open && (
        <div className="lg:hidden border-t border-border bg-background/95 backdrop-blur-md">
          <nav className="max-w-6xl mx-auto px-4 py-4 flex flex-col gap-3 text-sm">
            {NAV_ITEMS.map((it) => (
              <a
                key={it.id}
                href={`#${it.id}`}
                onClick={() => setOpen(false)}
                className="py-1 hover:text-foreground text-foreground/80"
                data-testid={`nav-link-mobile-${it.id}`}
              >
                {t(it.key)}
              </a>
            ))}
            <Button
              asChild
              size="sm"
              className="mt-1 rounded-[var(--btn-radius)]"
              data-testid="nav-join-button-mobile"
            >
              <a href="#whitelist" onClick={() => setOpen(false)}>
                {t("nav.join")}
              </a>
            </Button>
          </nav>
        </div>
      )}
    </header>
  );
}
