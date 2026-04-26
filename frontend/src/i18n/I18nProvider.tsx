import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { translations } from "./translations";
import type { Lang } from "@/types";

/**
 * I18n provider — single source of truth for the active language.
 *
 * - Persists the choice in localStorage (`STORAGE_KEY`).
 * - Mirrors it on `<html lang="...">` for accessibility and SEO crawlers.
 * - Updates the page <title>, <meta description>, OG and Twitter cards on
 *   every language change (these are static at build-time but we override
 *   them at runtime so the browser, share previews and assistive tools all
 *   see the right language without an SSR pass).
 */

interface I18nValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  /**
   * Translation lookup — the return type is intentionally `any` because:
   *   - translation values can be strings, arrays, or nested objects,
   *   - paths are dynamic, so static narrowing is impossible,
   *   - call-sites would otherwise need a `String(...)` wrap on every
   *     usage which is the worst kind of TS noise.
   * Treat the return as ReactNode-compatible at the call-site.
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  t: (path: string, fallback?: any) => any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  dict: Record<string, any>;
}

const I18nContext = createContext<I18nValue | null>(null);

const STORAGE_KEY = "deepotus_lang";

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    if (typeof window === "undefined") return "fr";
    const saved = localStorage.getItem(STORAGE_KEY) as Lang | null;
    if (saved === "fr" || saved === "en") return saved;
    const browser = navigator.language?.toLowerCase() || "";
    return browser.startsWith("fr") ? "fr" : "en";
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    localStorage.setItem(STORAGE_KEY, lang);
    document.documentElement.lang = lang;

    // ---- Sync SEO meta tags with the active language ----
    const dictForLang =
      (translations as Record<string, Record<string, unknown>>)[lang] ||
      translations.fr;
    // narrow: dictForLang.seo can be a sub-object with title + description
    const seo = (dictForLang as { seo?: { title?: string; description?: string } })
      .seo;
    const seoTitle = seo?.title;
    const seoDesc = seo?.description;

    if (seoTitle) document.title = seoTitle;

    const setMeta = (
      selector: string,
      attrName: string,
      value: string | undefined,
    ) => {
      if (!value) return;
      const el = document.head.querySelector(selector);
      if (el) el.setAttribute(attrName, value);
    };
    // Standard description
    setMeta('meta[name="description"]', "content", seoDesc);
    // Open Graph
    setMeta('meta[property="og:title"]', "content", seoTitle);
    setMeta('meta[property="og:description"]', "content", seoDesc);
    setMeta(
      'meta[property="og:locale"]',
      "content",
      lang === "fr" ? "fr_FR" : "en_US",
    );
    setMeta(
      'meta[property="og:locale:alternate"]',
      "content",
      lang === "fr" ? "en_US" : "fr_FR",
    );
    // Twitter
    setMeta('meta[name="twitter:title"]', "content", seoTitle);
    setMeta('meta[name="twitter:description"]', "content", seoDesc);
  }, [lang]);

  const setLang = useCallback((l: Lang) => {
    if (l === "fr" || l === "en") setLangState(l);
  }, []);

  // `dict` is purely derived from `lang` and the static `translations` import.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const dict = useMemo<Record<string, any>>(
    () =>
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (translations as Record<string, Record<string, any>>)[lang] ||
      translations.fr,
    [lang],
  );

  // t("path.to.key", fallback) — returns the string (or object/array) from dict
  const t = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (path: string, fallback?: any): any => {
      const parts = path.split(".");
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      let cur: any = dict;
      for (const p of parts) {
        if (cur == null) return fallback ?? path;
        cur = cur[p];
      }
      return cur ?? fallback ?? path;
    },
    [dict],
  );

  const value = useMemo<I18nValue>(
    () => ({ lang, setLang, t, dict }),
    [lang, setLang, t, dict],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
