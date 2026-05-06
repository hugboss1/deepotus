import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import { Mail, CheckCircle2 } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { useI18n } from "@/i18n/I18nProvider";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/** Hash that scrolls to this section + triggers the focus pulse. */
const ACCREDITATION_HASH = "#accreditation";

export default function Whitelist() {
  const { t, lang } = useI18n();
  const [email, setEmail] = useState("");
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null);
  // Drives the transient glow + input highlight when an Agent lands
  // via /#accreditation. Flips back to false after the animation so a
  // subsequent visit retriggers cleanly.
  const [focusPulse, setFocusPulse] = useState<boolean>(false);

  const sectionRef = useRef<HTMLElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  /**
   * Anchor-driven focus choreography.
   *
   * Why an `IntersectionObserver` instead of a plain on-mount check?
   * The landing page opens with a full-screen DeepState intro (~6-8s)
   * that covers the Whitelist section. If we fired the pulse on mount
   * the 2.6s glow would expire **behind** the intro and the Agent
   * would never see it. Solution:
   *
   *   1. Mount → record `pendingFocus` if `location.hash` matches.
   *   2. Observer fires when ≥40 % of the section enters the viewport
   *      (covers normal scroll AND the moment the intro fades).
   *   3. Drain `pendingFocus` exactly once: smooth-scroll, focus the
   *      input after 550 ms, glow for 2.6 s.
   *
   * Re-runs on every `hashchange` so a user who clicks a second
   * `#accreditation` link during the same session still gets the cue.
   */
  useEffect(() => {
    if (typeof window === "undefined") return undefined;

    let pendingFocus: boolean = window.location.hash === ACCREDITATION_HASH;

    const drainPendingFocus = (): void => {
      if (!pendingFocus) return;
      pendingFocus = false;
      requestAnimationFrame(() => {
        sectionRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
        setFocusPulse(true);
        window.setTimeout(() => {
          inputRef.current?.focus({ preventScroll: true });
        }, 550);
        window.setTimeout(() => setFocusPulse(false), 2600);
      });
    };

    // The observer waits until the section is ≥40 % visible. Once the
    // intro overlay disposes (its container's `display:none` hides it
    // from the viewport stack), the section becomes observable and we
    // fire the choreography. If the user already scrolled past the
    // section by the time the intro ends, the observer still triggers
    // because the section *was* in the viewport.
    let observer: IntersectionObserver | null = null;
    if (sectionRef.current && pendingFocus && "IntersectionObserver" in window) {
      observer = new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (entry.isIntersecting && entry.intersectionRatio >= 0.4) {
              drainPendingFocus();
              observer?.disconnect();
              observer = null;
              break;
            }
          }
        },
        { threshold: [0.4] },
      );
      observer.observe(sectionRef.current);
      // Hard fallback — if for some reason the observer never fires
      // (legacy browsers, headless environments, etc.) drain after 9 s.
      window.setTimeout(() => {
        if (pendingFocus) drainPendingFocus();
      }, 9000);
    } else if (pendingFocus) {
      // No IntersectionObserver — fire immediately as before.
      drainPendingFocus();
    }

    // In-page hashchange (a click on a link with `href="#accreditation"`
    // during the session). The intro is already gone, so we drain
    // synchronously without re-arming the observer.
    const onHashChange = (): void => {
      if (window.location.hash !== ACCREDITATION_HASH) return;
      pendingFocus = true;
      drainPendingFocus();
    };
    window.addEventListener("hashchange", onHashChange);

    return () => {
      observer?.disconnect();
      window.removeEventListener("hashchange", onHashChange);
    };
  }, []);

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const v = email.trim().toLowerCase();
    if (!v || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) {
      toast.error(t("whitelist.error"));
      return;
    }
    setSending(true);
    try {
      const res = await axios.post(`${API}/whitelist`, { email: v, lang });
      setResult(res.data);
    } catch (e) {
      toast.error(t("whitelist.error"));
    } finally {
      setSending(false);
    }
  };

  const successTemplate = t("whitelist.success") || "✓";

  return (
    <section
      id="whitelist"
      ref={sectionRef}
      data-testid="whitelist-section"
      className="py-14 sm:py-18 lg:py-24 border-t border-border scroll-mt-24"
    >
      {/* Second, dedicated anchor for the recruitment deep-link.
          Lives as a zero-height div so it lands above the heading (not
          clipped under a sticky header) and doesn't shift layout. */}
      <div
        id="accreditation"
        data-testid="accreditation-anchor"
        aria-hidden="true"
        className="relative -top-24 h-0 w-0"
      />
      <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
        <div className="font-mono text-[11px] uppercase tracking-[0.25em] text-muted-foreground">
          {t("whitelist.kicker")}
        </div>
        <h2 className="mt-2 font-display text-3xl md:text-5xl font-semibold leading-tight">
          {t("whitelist.title")}
        </h2>
        <p className="mt-3 text-foreground/80">{t("whitelist.subtitle")}</p>

        {result ? (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-8 inline-flex items-center gap-3 rounded-xl border-2 border-[#18C964] bg-[#18C964]/10 px-5 py-4"
            data-testid="whitelist-success-message"
          >
            <CheckCircle2 size={22} className="text-[#18C964]" />
            <span className="font-mono text-sm">
              {successTemplate.replace("__POS__", String(result.position))}
            </span>
          </motion.div>
        ) : (
          <form
            onSubmit={onSubmit}
            // `focusPulse` toggles a terminal-style amber glow +
            // caret-color highlight for 2.6s so an Agent arriving via
            // /#accreditation can't miss the input. We animate the
            // box-shadow (GPU-friendly) rather than anything that
            // triggers layout.
            data-focus-pulse={focusPulse ? "true" : "false"}
            className={[
              "mt-8 max-w-xl mx-auto flex flex-col sm:flex-row items-stretch gap-3",
              "rounded-xl p-2 transition-[box-shadow,border-color] duration-500 ease-out border",
              focusPulse
                ? "border-[#F59E0B]/70 shadow-[0_0_0_4px_rgba(245,158,11,0.15),0_0_32px_rgba(245,158,11,0.35)] motion-safe:animate-[pulse_1.3s_ease-in-out_1]"
                : "border-transparent",
            ].join(" ")}
            data-testid="whitelist-form"
          >
            <div className="flex-1 relative">
              <Mail
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
              />
              <Input
                data-testid="whitelist-email-input"
                ref={inputRef}
                type="email"
                required
                value={email}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                placeholder={t("whitelist.placeholder")}
                aria-label={t("whitelist.emailLabel")}
                className={[
                  "h-12 pl-9 font-mono",
                  // Amber caret-color + ring during the pulse so the
                  // OS cursor visibly switches to the terminal palette
                  // — subtle but unmistakable for the Agent.
                  focusPulse ? "caret-[#F59E0B] ring-2 ring-[#F59E0B]/40" : "",
                ].join(" ")}
              />
            </div>
            <Button
              type="submit"
              disabled={sending}
              size="lg"
              className="rounded-[var(--btn-radius)] btn-press font-semibold"
              data-testid="whitelist-submit-button"
            >
              {sending ? "…" : t("whitelist.submit")}
            </Button>
          </form>
        )}

        <p className="mt-3 text-[11px] font-mono text-muted-foreground max-w-xl mx-auto">
          {t("whitelist.miniDisclaimer")}
        </p>
      </div>
    </section>
  );
}
