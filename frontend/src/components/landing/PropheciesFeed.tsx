import React, { useCallback, useEffect, useRef, useState } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { RefreshCcw, Radio } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/i18n/I18nProvider";
import { FADE_TRANSITION_DEFAULT } from "@/lib/motionVariants";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Display cadence
// ---------------
// AUTO_ROTATE_MS  → time between two automatic (cached pool) prophecies
//                   when the user is just watching the ticker.
// LIVE_HOLD_MS    → minimum time the manually-requested LIVE prophecy
//                   stays on screen before auto-rotation resumes. Without
//                   this guard the next 9 s tick could land 100 ms after
//                   the click and overwrite the live prophecy
//                   instantaneously — that was the user-reported bug.
const AUTO_ROTATE_MS = 9000;
const LIVE_HOLD_MS = 5000;

// Prophecy text cross-fade: enters from below with a 6px blur, exits up
// with a softer blur. Module-level so each new prophecy reuses the same
// frames (which keeps framer-motion's internal interpolator stable).
const PROPHECY_TEXT_INITIAL = { opacity: 0, y: 8, filter: "blur(6px)" };
const PROPHECY_TEXT_ANIMATE = { opacity: 1, y: 0, filter: "blur(0px)" };
const PROPHECY_TEXT_EXIT = { opacity: 0, y: -6, filter: "blur(4px)" };

export default function PropheciesFeed() {
  const { t, lang } = useI18n();
  const [current, setCurrent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [counter, setCounter] = useState(0);
  // We use a single chained setTimeout (instead of setInterval) so the
  // cadence can be reset whenever the user manually fetches a live
  // prophecy. clearTimeout handles both lifecycle paths cleanly.
  const timerRef = useRef(null);
  const mountedRef = useRef(true);
  const reduceMotionRef = useRef(false);

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

  // Schedule the NEXT auto-rotation. Replaces any pending timer so the
  // cadence is always anchored on the most recent prophecy display.
  // ``delayMs`` lets the caller pick a custom hold window — used by
  // ``refreshLive`` to guarantee LIVE_HOLD_MS visibility regardless of
  // where we were in the previous 9 s cycle.
  const scheduleNext = useCallback(
    (delayMs: number) => {
      if (reduceMotionRef.current) return; // honour OS preference
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        if (!mountedRef.current) return;
        fetchOne(false).finally(() => {
          if (mountedRef.current) scheduleNext(AUTO_ROTATE_MS);
        });
      }, delayMs);
    },
    [fetchOne],
  );

  // Initial load + recurring auto-rotation (skipped when the user has
  // 'prefers-reduced-motion' enabled — no surprise text swaps).
  useEffect(() => {
    mountedRef.current = true;
    reduceMotionRef.current = Boolean(
      window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    );
    fetchOne(false).finally(() => {
      if (mountedRef.current) scheduleNext(AUTO_ROTATE_MS);
    });
    return () => {
      mountedRef.current = false;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [fetchOne, scheduleNext]);

  // Manual refresh — fetch a fresh LIVE prophecy and HOLD it on screen
  // for at least LIVE_HOLD_MS before the auto-rotation resumes. This
  // fixes the previous "click → text appears then disappears almost
  // immediately" bug (the 9 s setInterval was decoupled from clicks).
  const refreshLive = useCallback(async () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    await fetchOne(true);
    if (mountedRef.current) scheduleNext(LIVE_HOLD_MS);
  }, [fetchOne, scheduleNext]);

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
                initial={PROPHECY_TEXT_INITIAL}
                animate={PROPHECY_TEXT_ANIMATE}
                exit={PROPHECY_TEXT_EXIT}
                transition={FADE_TRANSITION_DEFAULT}
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
