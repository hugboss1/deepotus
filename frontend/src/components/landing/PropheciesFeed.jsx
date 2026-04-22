import React, { useCallback, useEffect, useRef, useState } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { RefreshCcw, Radio } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n/I18nProvider";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function PropheciesFeed() {
  const { t, lang } = useI18n();
  const [current, setCurrent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [counter, setCounter] = useState(0);
  const timerRef = useRef(null);
  const mountedRef = useRef(true);

  const fetchOne = useCallback(
    async (live = false) => {
      setLoading(true);
      try {
        const res = await axios.get(`${API}/prophecy`, {
          params: { lang, live },
        });
        if (mountedRef.current) {
          setCurrent(res.data.prophecy);
          setCounter((c) => c + 1);
        }
      } catch (e) {
        if (mountedRef.current) setCurrent("[Signal perdu]");
      } finally {
        if (mountedRef.current) setLoading(false);
      }
    },
    [lang],
  );

  // Auto-rotate every 9s using seeded (non-live) pool to avoid LLM costs
  useEffect(() => {
    mountedRef.current = true;
    fetchOne(false);
    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    )?.matches;
    if (!reduceMotion) {
      timerRef.current = setInterval(() => {
        fetchOne(false);
      }, 9000);
    }
    return () => {
      mountedRef.current = false;
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [fetchOne]);

  const refreshLive = () => fetchOne(true);

  return (
    <section
      id="prophecies"
      data-testid="prophecies-feed"
      className="py-14 sm:py-18 border-t border-border bg-[#0B0D10] text-zinc-100"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
          <div>
            <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-zinc-500 flex items-center gap-2">
              <Radio size={12} className="text-[#33ff33]" />
              {t("prophecies.kicker")}
            </div>
            <h2 className="font-display text-3xl md:text-4xl font-semibold text-white mt-2">
              {t("prophecies.title")}
            </h2>
            <p className="text-zinc-400 mt-2">{t("prophecies.subtitle")}</p>
          </div>
          <Button
            onClick={refreshLive}
            disabled={loading}
            variant="outline"
            className="self-start md:self-auto rounded-[var(--btn-radius)] border-zinc-700 bg-transparent text-zinc-100 hover:bg-zinc-900 btn-press"
            data-testid="prophecies-refresh-button"
          >
            <RefreshCcw size={14} className={`mr-1 ${loading ? "animate-spin" : ""}`} />
            {loading ? t("prophecies.loading") : t("prophecies.refresh")}
          </Button>
        </div>

        <div
          className="relative rounded-xl border border-zinc-800 bg-gradient-to-b from-[#0e141b] to-[#070a0f] p-6 md:p-10 overflow-hidden scanlines"
          data-testid="prophecies-ticker"
        >
          <div className="absolute top-3 left-3 font-mono text-[10px] uppercase tracking-widest text-[#33ff33]">
            &gt; PROPHECY.STREAM
          </div>
          <div className="absolute top-3 right-3 font-mono text-[10px] text-zinc-500">
            #{String(counter).padStart(4, "0")}
          </div>

          <div className="min-h-[120px] flex items-center">
            <AnimatePresence mode="wait">
              <motion.p
                key={current || "loading"}
                initial={{ opacity: 0, y: 8, filter: "blur(6px)" }}
                animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                exit={{ opacity: 0, y: -6, filter: "blur(4px)" }}
                transition={{ duration: 0.5 }}
                className="font-display text-2xl md:text-3xl lg:text-4xl text-white leading-tight max-w-4xl caret"
                data-testid="prophecies-text"
              >
                {current || (loading ? t("prophecies.loading") : "…")}
              </motion.p>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
