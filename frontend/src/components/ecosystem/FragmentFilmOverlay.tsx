/**
 * FragmentFilmOverlay — plein écran du film scroll-cinéma « DEEPOTUS — Fragment ».
 *
 * Le film est une page autonome (public/fragment/index.html : scroll-scrub,
 * zéro dépendance) chargée dans une iframe par-dessus le site. Fermeture par
 * bouton ou Escape ; le scroll du site est verrouillé tant que l'overlay est
 * ouvert (le scroll appartient au film).
 */
import { useEffect } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";

interface FragmentFilmOverlayProps {
  open: boolean;
  onClose: () => void;
}

export default function FragmentFilmOverlay({ open, onClose }: FragmentFilmOverlayProps): JSX.Element | null {
  const { t } = useI18n();

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === "Escape") onClose();
    };
    // Le film (iframe) envoie ce message quand le visiteur clique
    // « Revenir au site » à la fin de l'animation.
    const onMsg = (e: MessageEvent): void => {
      if (e.data === "fragment-film:close") onClose();
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("message", onMsg);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("message", onMsg);
      document.body.style.overflow = prevOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[120] bg-black"
      role="dialog"
      aria-modal="true"
      aria-label={t("ecosystem.cards.mobile.film.cta") as string}
      data-testid="fragment-film-overlay"
    >
      <iframe
        src="/fragment/index.html"
        title="DEEPOTUS — Fragment"
        className="absolute inset-0 h-full w-full border-0"
        data-testid="fragment-film-iframe"
      />
      <button
        type="button"
        onClick={onClose}
        aria-label={t("ecosystem.cards.mobile.film.close") as string}
        className="absolute top-4 right-4 z-10 inline-flex h-10 w-10 items-center justify-center rounded-full border border-amber-500/40 bg-black/60 text-amber-200/90 backdrop-blur-sm transition-colors hover:bg-black/85 hover:text-amber-100"
        data-testid="fragment-film-close"
      >
        <X className="h-5 w-5" aria-hidden />
      </button>
    </div>,
    document.body,
  );
}
