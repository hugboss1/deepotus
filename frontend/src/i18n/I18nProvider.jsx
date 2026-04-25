import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { translations } from "./translations";

const I18nContext = createContext(null);

const STORAGE_KEY = "deepotus_lang";

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    if (typeof window === "undefined") return "fr";
    return localStorage.getItem(STORAGE_KEY) || "fr";
  });

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, lang);
      document.documentElement.lang = lang;

      // ---- Sync SEO meta tags with the active language ----
      const dictForLang = translations[lang] || translations.fr;
      const seoTitle = dictForLang?.seo?.title;
      const seoDesc = dictForLang?.seo?.description;

      if (seoTitle) {
        document.title = seoTitle;
      }

      const setMeta = (selector, attrName, value) => {
        if (!value) return;
        const el = document.head.querySelector(selector);
        if (el) {
          el.setAttribute(attrName, value);
        }
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
    }
  }, [lang]);

  const setLang = (l) => {
    if (l === "fr" || l === "en") setLangState(l);
  };

  const dict = translations[lang] || translations.fr;

  // t("path.to.key", fallback) — returns the string (or object/array) from dict
  const t = (path, fallback) => {
    const parts = path.split(".");
    let cur = dict;
    for (const p of parts) {
      if (cur == null) return fallback ?? path;
      cur = cur[p];
    }
    return cur ?? fallback ?? path;
  };

  const value = useMemo(() => ({ lang, setLang, t, dict }), [lang]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
