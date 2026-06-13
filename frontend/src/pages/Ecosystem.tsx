/**
 * Ecosystem page (/ecosysteme + /ecosystem alias).
 *
 * Composed of:
 *   - TopNav + Footer (existing landing chrome)
 *   - EcosystemHero
 *   - 4 product cards (Roman, Boardgame, VideoGen, Mobile)
 *   - EcosystemBanner (memecoin rallying point)
 *
 * Dialogs (GenesisList, B2BInquiry) are mounted at the root of the
 * page so any card can trigger them via lifted state.
 */
import { useState, useEffect } from "react";
import { toast } from "sonner";
import TopNav from "@/components/landing/TopNav";
import Footer from "@/components/landing/Footer";
import { EcosystemHero } from "@/components/ecosystem/EcosystemHero";
import { ProductRomanCard } from "@/components/ecosystem/ProductRomanCard";
import { ProductBoardGameCard } from "@/components/ecosystem/ProductBoardGameCard";
import { ProductVideoGenCard } from "@/components/ecosystem/ProductVideoGenCard";
import { ProductMobileGameCard } from "@/components/ecosystem/ProductMobileGameCard";
import { EcosystemBanner } from "@/components/ecosystem/EcosystemBanner";
import { GenesisListDialog } from "@/components/ecosystem/GenesisListDialog";
import { B2BInquiryDialog } from "@/components/ecosystem/B2BInquiryDialog";
import { useI18n } from "@/i18n/I18nProvider";
import type { GenesisPayload } from "@/lib/ecosystem";

// Placeholder social links — swap to real handles when accounts exist.
// The boolean below switches the UI from "Bientôt" badges to live links.
const HAS_REAL_SOCIALS = false;
const INSTAGRAM_URL = "https://instagram.com/deepotus";
const YOUTUBE_URL = "https://youtube.com/@deepotus";
const TELEGRAM_URL = "https://t.me/deepotus";
const X_URL = "https://x.com/deepotus";

export default function Ecosystem(): JSX.Element {
  const { t } = useI18n();
  const [genesisOpen, setGenesisOpen] = useState<boolean>(false);
  const [genesisSource, setGenesisSource] =
    useState<GenesisPayload["source"]>("genesis_roman");
  const [b2bOpen, setB2bOpen] = useState<boolean>(false);

  useEffect(() => {
    document.title = t("ecosystem.seo.title");
  }, [t]);

  const openGenesis = (source: GenesisPayload["source"]): void => {
    setGenesisSource(source);
    setGenesisOpen(true);
  };

  const handleSoonClick = (): void => {
    toast.info(t("ecosystem.socialsSoonToast.title"), {
      description: t("ecosystem.socialsSoonToast.body"),
    });
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <TopNav />
      <main data-testid="ecosystem-page">
        <EcosystemHero />
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10 lg:space-y-14 pb-8">
          <ProductRomanCard
            onJoinGenesis={() => openGenesis("genesis_roman")}
            onSoonClick={handleSoonClick}
            instagramUrl={INSTAGRAM_URL}
            youtubeUrl={YOUTUBE_URL}
            hasRealSocials={HAS_REAL_SOCIALS}
          />
          <ProductBoardGameCard />
          <ProductVideoGenCard onContactB2B={() => setB2bOpen(true)} />
          <ProductMobileGameCard
            onJoinWaitlist={() => openGenesis("genesis_mobile")}
          />
        </div>
        <EcosystemBanner
          pumpfun=""
          telegram={TELEGRAM_URL}
          x={X_URL}
          instagram={INSTAGRAM_URL}
          youtube={YOUTUBE_URL}
          hasRealSocials={HAS_REAL_SOCIALS}
          onSoonClick={handleSoonClick}
        />
      </main>
      <Footer />
      <GenesisListDialog
        open={genesisOpen}
        onOpenChange={setGenesisOpen}
        source={genesisSource}
      />
      <B2BInquiryDialog open={b2bOpen} onOpenChange={setB2bOpen} />
    </div>
  );
}
