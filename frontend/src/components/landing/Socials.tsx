import { motion } from "framer-motion";
import { toast } from "sonner";
import { useI18n } from "@/i18n/I18nProvider";
import { SOCIALS } from "@/lib/social";

export default function Socials() {
  const { t } = useI18n();

  const onSoon = () =>
    toast(t("socials.soonToast.title") as string, {
      description: t("socials.soonToast.body") as string,
    });

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

        <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {SOCIALS.map(({ key, Icon, color, url, live }, i) => {
            // X is monochrome → adapt to the active theme via foreground,
            // every other channel keeps its brand accent + tinted chip.
            const iconWrap = color
              ? "w-11 h-11 rounded-lg flex items-center justify-center mb-4"
              : "w-11 h-11 rounded-lg flex items-center justify-center mb-4 bg-foreground/10";
            const wrapStyle = color ? { background: `${color}18` } : undefined;

            const inner = (
              <>
                <div className={iconWrap} style={wrapStyle}>
                  {color ? (
                    <Icon size={20} style={{ color }} />
                  ) : (
                    <Icon size={20} className="text-foreground" />
                  )}
                </div>
                <div className="font-display font-semibold text-lg">
                  {t(`socials.${key}.name`)}
                </div>
                <div className="mt-1 font-mono text-sm text-foreground/70">
                  {live ? t(`socials.${key}.handle`) : t("socials.soon")}
                </div>
                <div className="mt-4 text-[11px] font-mono uppercase tracking-widest text-muted-foreground group-hover:text-foreground transition-colors">
                  {live ? "→ CONNECT.SIMULATION" : `→ ${t("socials.soon")}`}
                </div>
              </>
            );

            const cardClass =
              "group block text-left w-full rounded-xl border border-border bg-card p-5 hover:shadow-[var(--shadow-elev-2)] transition-shadow";
            const anim = {
              initial: { opacity: 0, y: 12 },
              whileInView: { opacity: 1, y: 0 },
              viewport: { once: true, margin: "-60px" },
              transition: { duration: 0.5, delay: i * 0.05 },
            } as const;

            return live ? (
              <motion.a
                key={key}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                {...anim}
                className={cardClass}
                data-testid={`social-${key}-link`}
              >
                {inner}
              </motion.a>
            ) : (
              <motion.button
                key={key}
                type="button"
                onClick={onSoon}
                {...anim}
                className={`${cardClass} cursor-pointer`}
                data-testid={`social-${key}-soon`}
              >
                {inner}
              </motion.button>
            );
          })}
        </div>
      </div>
    </section>
  );
}
