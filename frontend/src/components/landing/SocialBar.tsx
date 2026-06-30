/**
 * SocialBar — compact row of the official $DEEPOTUS channel icons.
 *
 * Replicated across the Footer and the standalone pages (Missions,
 * Transparency, Giveaway, public stats…) so the channels are reachable
 * site-wide, not only from the landing "Official Channels" section.
 *
 * Live channels are real links; not-yet-opened ones (Instagram / Discord
 * / YouTube until their Vercel env var is set) render muted and emit the
 * shared "account being created" toast on click. See lib/social.ts.
 */
import { toast } from "sonner";
import { SOCIALS } from "@/lib/social";
import { useI18n } from "@/i18n/I18nProvider";

export default function SocialBar({
  className = "",
  size = 18,
}: {
  className?: string;
  size?: number;
}) {
  const { t } = useI18n();

  const onSoon = () =>
    toast(t("socials.soonToast.title") as string, {
      description: t("socials.soonToast.body") as string,
    });

  const base =
    "w-9 h-9 rounded-md grid place-items-center border border-border/60 bg-background/40 transition-colors";

  return (
    <div
      className={`flex items-center gap-2 ${className}`}
      data-testid="social-bar"
    >
      {SOCIALS.map(({ key, Icon, url, live }) => {
        const label = t(`socials.${key}.name`) as string;

        if (live) {
          return (
            <a
              key={key}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={label}
              title={label}
              data-testid={`social-bar-${key}`}
              className={`${base} text-foreground/65 hover:text-foreground hover:border-foreground/40`}
            >
              <Icon size={size} />
            </a>
          );
        }
        return (
          <button
            key={key}
            type="button"
            onClick={onSoon}
            aria-label={`${label} — ${t("socials.soon")}`}
            title={`${label} — ${t("socials.soon")}`}
            data-testid={`social-bar-${key}-soon`}
            className={`${base} text-foreground/30 hover:text-foreground/55 cursor-pointer`}
          >
            <Icon size={size} />
          </button>
        );
      })}
    </div>
  );
}
