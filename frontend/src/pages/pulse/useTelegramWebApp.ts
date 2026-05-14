/**
 * Lazy-loads the Telegram WebApp SDK and calls ``ready()`` + ``expand()``
 * so the page renders edge-to-edge when opened as a Telegram Mini App.
 *
 * Why lazy? The /pulse page is reachable both from a plain browser
 * (organic traffic) and from inside Telegram. Loading the SDK
 * unconditionally in ``index.html`` would force a third-party script
 * on every visitor of every page of the site, hurting LCP on the
 * landing. This hook injects the script only on /pulse, only once
 * per browsing session, and degrades silently in non-TMA contexts.
 *
 * Returns the live ``Telegram.WebApp`` object once the script
 * resolves, or ``null`` while loading / when running outside TMA.
 */
import { useEffect, useState } from "react";

// Minimal typing — only the surface area we touch. The SDK has many
// more fields but typing them here invites drift; if you need more
// later either extend this or add the full @types package.
interface TelegramWebApp {
  ready: () => void;
  expand: () => void;
  isExpanded: boolean;
  platform: string;
  version: string;
  colorScheme: "light" | "dark";
  // Used to "open inside Telegram" links — we don't currently call it,
  // but documenting it here makes future use type-safe.
  openTelegramLink?: (url: string) => void;
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

const TMA_SDK_URL = "https://telegram.org/js/telegram-web-app.js";
const TMA_SDK_TAG_ID = "tg-webapp-sdk";

export function useTelegramWebApp(): TelegramWebApp | null {
  const [webApp, setWebApp] = useState<TelegramWebApp | null>(null);

  useEffect(() => {
    // Server-side rendering / build-time guard.
    if (typeof window === "undefined") return undefined;

    // Path 1 — SDK already present (subsequent /pulse visits, or
    // direct TMA boot where Telegram preloaded it). Use the existing
    // global without injecting a duplicate script tag.
    const existing = window.Telegram?.WebApp;
    if (existing) {
      try {
        existing.ready();
        if (!existing.isExpanded) existing.expand();
      } catch {
        // ignore — non-TMA browsers throw on .expand() in some versions
      }
      setWebApp(existing);
      return undefined;
    }

    // Path 2 — Inject SDK script once. Re-entrant safe: if a previous
    // mount already started the load we just wait for the same tag.
    let script = document.getElementById(TMA_SDK_TAG_ID) as HTMLScriptElement | null;
    let createdHere = false;
    if (!script) {
      script = document.createElement("script");
      script.id = TMA_SDK_TAG_ID;
      script.src = TMA_SDK_URL;
      script.async = true;
      // ``defer`` is redundant with async but harmless; keep both for
      // older browsers that interpret one but not the other.
      script.defer = true;
      document.head.appendChild(script);
      createdHere = true;
    }

    const onLoad = (): void => {
      const tg = window.Telegram?.WebApp;
      if (!tg) {
        // Loaded but no global — means the user is on a desktop
        // browser, not in TMA. That's expected; just bail.
        return;
      }
      try {
        tg.ready();
        if (!tg.isExpanded) tg.expand();
      } catch {
        // ignore
      }
      setWebApp(tg);
    };

    const onError = (): void => {
      // Network blocked the script (corporate firewall, etc.). The
      // page still works as a plain web view; we just don't get the
      // TMA-specific affordances. No need to surface this to users.
      // eslint-disable-next-line no-console
      console.warn("[pulse] Telegram WebApp SDK failed to load");
    };

    script.addEventListener("load", onLoad);
    script.addEventListener("error", onError);

    return () => {
      script?.removeEventListener("load", onLoad);
      script?.removeEventListener("error", onError);
      // We intentionally do NOT remove the <script> tag on unmount.
      // Telegram caches the singleton on window.Telegram and a
      // second injection would race the first.
      if (createdHere) {
        // No-op; documentation hook for future cleanup if needed.
      }
    };
  }, []);

  return webApp;
}
