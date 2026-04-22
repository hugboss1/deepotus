import React from "react";
import { motion } from "framer-motion";
import { Twitter, Send as TelegramIcon, MessageSquare } from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";

const CARDS = [
  { key: "x", icon: Twitter, color: "#1DA1F2" },
  { key: "telegram", icon: TelegramIcon, color: "#2AABEE" },
  { key: "discord", icon: MessageSquare, color: "#5865F2" },
];

export default function Socials() {
  const { t } = useI18n();

  return (
    <section
      id="socials"
      data-testid="socials-section"
      className="py-14 sm:py-18 lg:py-24 border-t border-border bg-secondary/30"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
          {t("socials.kicker")}
        </div>
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-3 mt-2">
          <h2 className="font-display text-3xl md:text-4xl font-semibold leading-tight">
            {t("socials.title")}
          </h2>
          <div className="text-muted-foreground">{t("socials.subtitle")}</div>
        </div>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-5">
          {CARDS.map(({ key, icon: Icon, color }, i) => (
            <motion.a
              key={key}
              href="#"
              onClick={(e) => e.preventDefault()}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.5, delay: i * 0.05 }}
              className="group block rounded-xl border border-border bg-card p-5 hover:shadow-[var(--shadow-elev-2)] transition-shadow"
              data-testid={`social-${key}-link`}
            >
              <div
                className="w-11 h-11 rounded-lg flex items-center justify-center mb-4"
                style={{ background: `${color}18` }}
              >
                <Icon size={20} style={{ color }} />
              </div>
              <div className="font-display font-semibold text-lg">
                {t(`socials.${key}.name`)}
              </div>
              <div className="mt-1 font-mono text-sm text-foreground/70">
                {t(`socials.${key}.handle`)}
              </div>
              <div className="mt-4 text-[11px] font-mono uppercase tracking-widest text-muted-foreground group-hover:text-foreground transition-colors">
                → CONNECT.SIMULATION
              </div>
            </motion.a>
          ))}
        </div>
      </div>
    </section>
  );
}
