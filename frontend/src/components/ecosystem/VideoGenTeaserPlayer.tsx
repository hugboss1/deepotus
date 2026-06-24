/**
 * VideoGenTeaserPlayer — Sprint 20.1 video viewer for the Video Generator
 * card.
 *
 * Acts as a swap-ready ``<video>`` player:
 *
 *   - When ``HAS_TEASER === false`` (default), it renders the existing
 *     <VideoGenAppMockup/> styled UI as a "poster" and overlays a play
 *     button + a "Teaser à venir" pill. Clicking the play button shows
 *     an info toast so visitors know it's coming.
 *
 *   - When ``HAS_TEASER === true`` (flip the constant once the actual
 *     teaser mp4 is uploaded to ``/assets/videos/video-gen-teaser.mp4``),
 *     it renders an HTML5 <video> element with native controls and the
 *     mockup as poster (saved as a static jpg). The aspect ratio,
 *     border-radius and shadow match the rest of the ecosystem card so
 *     the swap is visually seamless.
 *
 * Why a dedicated component (vs. inline <video>) ?
 *   - Centralises the "no teaser yet" placeholder logic so the
 *     ProductVideoGenCard stays declarative.
 *   - Keeps the swap to a 1-line constant flip when the teaser arrives.
 *   - Allows reusing the player later in /pulse or marketing pages.
 */
import { Play } from "lucide-react";
import { toast } from "sonner";
import { useI18n } from "@/i18n/I18nProvider";
import { VideoGenAppMockup } from "./VideoGenAppMockup";

// --------------------------------------------------------------------
// Toggle these once the teaser is uploaded.
// --------------------------------------------------------------------
const HAS_TEASER: boolean = false;
const TEASER_VIDEO_URL = "/assets/videos/video-gen-teaser.mp4";
const TEASER_POSTER_URL = "/assets/videos/video-gen-teaser-poster.jpg";

export function VideoGenTeaserPlayer(): JSX.Element {
  const { t } = useI18n();

  if (HAS_TEASER) {
    return (
      <div
        className="relative rounded-xl overflow-hidden border border-border bg-[#0a0e14] shadow-[0_2px_0_rgba(0,0,0,0.10),_0_24px_56px_rgba(0,0,0,0.40)]"
        data-testid="videogen-teaser-player-live"
      >
        <video
          src={TEASER_VIDEO_URL}
          poster={TEASER_POSTER_URL}
          controls
          preload="metadata"
          playsInline
          className="block w-full h-auto aspect-video object-cover bg-black"
        >
          {/* Fallback for browsers without <video> support */}
          Your browser does not support HTML5 video.
        </video>
      </div>
    );
  }

  // Placeholder mode — show the existing mockup with a "play" overlay.
  const handlePlayClick = (): void => {
    toast.info(t("ecosystem.cards.videogen.teaser.soonBadge"), {
      description: t("ecosystem.cards.videogen.teaser.soonToast"),
    });
  };

  return (
    <div
      className="relative"
      data-testid="videogen-teaser-player-placeholder"
    >
      <VideoGenAppMockup />
      {/* Play-button overlay — subtle, doesn't fully obscure the mockup */}
      <button
        type="button"
        onClick={handlePlayClick}
        aria-label={t("ecosystem.cards.videogen.teaser.playLabel")}
        className="absolute inset-0 grid place-items-center group focus:outline-none"
        data-testid="videogen-teaser-play-btn"
      >
        <span
          aria-hidden
          className="absolute inset-0 bg-black/30 backdrop-blur-[2px] opacity-90 group-hover:opacity-95 transition-opacity"
        />
        <span className="relative flex flex-col items-center gap-3">
          <span className="h-16 w-16 rounded-full border-2 border-amber-400/80 bg-amber-500/15 grid place-items-center shadow-[0_0_0_8px_rgba(245,158,11,0.10),_0_24px_48px_rgba(0,0,0,0.45)] transition-transform group-hover:scale-105">
            <Play
              className="h-7 w-7 text-amber-300 translate-x-[1px]"
              fill="currentColor"
              aria-hidden
            />
          </span>
          <span className="font-mono text-[10px] uppercase tracking-[0.30em] text-amber-200/95 rounded-full border border-amber-500/40 bg-amber-500/15 px-3 py-1">
            {t("ecosystem.cards.videogen.teaser.soonBadge")}
          </span>
        </span>
      </button>
    </div>
  );
}
