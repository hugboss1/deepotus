import React from "react";
import { useI18n } from "@/i18n/I18nProvider";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";

export function LanguageToggle({ className = "" }) {
  const { lang, setLang } = useI18n();
  return (
    <div
      data-testid="language-toggle"
      className={`inline-flex items-center gap-0 rounded-[var(--btn-radius)] border border-border bg-background/80 backdrop-blur px-0.5 py-0.5 font-mono text-[11px] ${className}`}
      role="tablist"
      aria-label="Language"
    >
      {["fr", "en"].map((l) => {
        const active = lang === l;
        return (
          <button
            key={l}
            role="tab"
            aria-selected={active}
            data-testid={`lang-${l}`}
            onClick={() => setLang(l)}
            className={`relative px-2.5 py-1 rounded-[8px] uppercase tracking-widest transition-colors ${
              active
                ? "text-background"
                : "text-foreground/70 hover:text-foreground"
            }`}
          >
            {active && (
              <motion.span
                layoutId="lang-active-pill"
                className="absolute inset-0 rounded-[8px] bg-foreground"
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
              />
            )}
            <span className="relative">{l.toUpperCase()}</span>
          </button>
        );
      })}
    </div>
  );
}

export default LanguageToggle;
