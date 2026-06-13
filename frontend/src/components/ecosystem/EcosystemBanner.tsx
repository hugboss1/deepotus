/**
 * EcosystemBanner — bottom banner reminding visitors the memecoin is
 * the rallying point on pump.fun (Solana), without ever pitching it
 * as an investment (MiCA compliance).
 */
import { ExternalLink, Send, Twitter, Instagram, Youtube } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n/I18nProvider";
import { getBuyUrl } from "@/lib/links";

interface SocialLinks {
  pumpfun?: string;
  telegram?: string;
  x?: string;
  instagram?: string;
  youtube?: string;
  hasRealSocials: boolean;
}

interface Props extends SocialLinks {
  onSoonClick: () => void;
}

export function EcosystemBanner({
  pumpfun,
  telegram,
  x,
  instagram,
  youtube,
  hasRealSocials,
  onSoonClick,
}: Props): JSX.Element {
  const { t } = useI18n();

  const buyUrl = pumpfun || getBuyUrl();
  const isPlaceholderSocial = (url?: string): boolean =>
    !url || url.includes("REMPLACER");

  const handlePlaceholderClick =
    (url?: string) => (e: React.MouseEvent<HTMLAnchorElement>) => {
      if (isPlaceholderSocial(url) && !hasRealSocials) {
        e.preventDefault();
        onSoonClick();
      }
    };

  return (
    <section
      data-testid="ecosystem-banner"
      className="relative"
    >
      <div
        aria-hidden
        className="absolute inset-0 -z-10"
        style={{
          background:
            "radial-gradient(50% 50% at 50% 100%, rgba(245,158,11,0.08) 0%, rgba(0,0,0,0) 70%)",
        }}
      />
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20">
        <div className="rounded-2xl border border-border bg-card/40 backdrop-blur-sm p-7 sm:p-10">
          <div className="font-mono text-[11px] uppercase tracking-[0.28em] text-amber-400/85">
            {t("ecosystem.banner.kicker")}
          </div>
          <h3 className="mt-3 font-display font-semibold text-2xl sm:text-3xl text-foreground tracking-tight max-w-3xl">
            {t("ecosystem.banner.title")}
          </h3>
          <p className="mt-3 text-sm md:text-base text-foreground/70 leading-relaxed max-w-prose">
            {t("ecosystem.banner.disclaimer")}
          </p>

          <div className="mt-6 flex flex-wrap gap-2">
            <Button
              asChild
              className="gap-2 bg-amber-500/95 hover:bg-amber-500 text-zinc-950"
              data-testid="banner-pumpfun-cta"
            >
              <a href={buyUrl} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4" aria-hidden />
                {t("ecosystem.banner.pumpfun")}
              </a>
            </Button>
            <Button
              asChild
              variant="secondary"
              className="gap-2"
              data-testid="banner-telegram-cta"
            >
              <a
                href={telegram || "https://t.me/deepotus"}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Send className="h-4 w-4" aria-hidden />
                {t("ecosystem.banner.telegram")}
              </a>
            </Button>
            <Button
              asChild
              variant="secondary"
              className="gap-2"
              data-testid="banner-x-cta"
            >
              <a
                href={x || "https://x.com/deepotus"}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Twitter className="h-4 w-4" aria-hidden />
                {t("ecosystem.banner.x")}
              </a>
            </Button>
            <a
              href={instagram || "https://instagram.com/deepotus"}
              target="_blank"
              rel="noopener noreferrer"
              onClick={handlePlaceholderClick(instagram)}
              data-testid="banner-instagram-link"
            >
              <Button variant="secondary" className="gap-2" type="button">
                <Instagram className="h-4 w-4" aria-hidden />
                {t("ecosystem.banner.instagram")}
              </Button>
            </a>
            <a
              href={youtube || "https://youtube.com/@deepotus"}
              target="_blank"
              rel="noopener noreferrer"
              onClick={handlePlaceholderClick(youtube)}
              data-testid="banner-youtube-link"
            >
              <Button variant="secondary" className="gap-2" type="button">
                <Youtube className="h-4 w-4" aria-hidden />
                {t("ecosystem.banner.youtube")}
              </Button>
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
