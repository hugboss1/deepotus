import { motion, AnimatePresence } from "framer-motion";
import { Lock, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useI18n } from "@/i18n/I18nProvider";
import {
  KEYPAD_PULSE_ANIMATE,
  KEYPAD_PULSE_TRANSITION,
  VERIFY_FLASH_ANIMATE,
  VERIFY_FLASH_TRANSITION,
  FADE_INITIAL,
  FADE_EXIT,
} from "@/lib/motionVariants";
import TopNav from "@/components/landing/TopNav";
import Footer from "@/components/landing/Footer";

/**
 * GateView — cinematic black-ops door + digicode keypad.
 *
 * Pure presentational: takes everything it needs as props from the orchestrator.
 * Renders the desktop overlay (LED display inside the keypad illustration) and
 * the mobile fallback (form below the door).
 */

export function GateView({
  codeInput,
  setCodeInput,
  verifying,
  gateError,
  verifyCode,
}) {
  const { t } = useI18n();
  const statusColor = gateError
    ? "#EF4444"
    : verifying
    ? "#F59E0B"
    : "#22D3EE";
  const statusLabel = gateError
    ? "ERROR"
    : verifying
    ? "VERIFYING"
    : t("classifiedVault.gateIdle");

  return (
    <div className="min-h-screen bg-black">
      <TopNav />
      <main className="relative px-4 py-10 md:py-16">
        {/* Header */}
        <div className="max-w-6xl mx-auto mb-8 md:mb-12">
          <div className="inline-flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.3em] text-[#F59E0B]">
            <Lock size={14} /> {t("classifiedVault.gateKicker")}
          </div>
          <h1
            className="mt-3 font-display text-3xl md:text-5xl font-semibold leading-tight text-white"
            data-testid="classified-gate-title"
          >
            {t("classifiedVault.gateTitle")}
          </h1>
          <p className="mt-3 text-sm md:text-base text-white/70 max-w-2xl">
            {t("classifiedVault.gateSubtitle")}
          </p>
        </div>

        {/* DOOR CHASSIS with overlay input (desktop) */}
        <div className="max-w-6xl mx-auto">
          <div
            className="relative w-full overflow-hidden rounded-2xl border border-border bg-black shadow-[0_0_40px_rgba(34,211,238,0.12)] aspect-[16/9]"
            data-testid="classified-door-chassis"
          >
            <img
              src="/door_keypad.png"
              alt="Deep State reinforced door with digicode keypad"
              className="absolute inset-0 w-full h-full object-cover object-center select-none pointer-events-none"
              draggable={false}
            />

            {/* Ambient pulse behind the LED display (breathes) */}
            <motion.div
              aria-hidden
              className="absolute pointer-events-none"
              style={{
                left: "42%",
                top: "38%",
                width: "17%",
                height: "13%",
                background: `radial-gradient(ellipse at center, ${statusColor}55, transparent 70%)`,
                filter: "blur(6px)",
              }}
              animate={KEYPAD_PULSE_ANIMATE}
              transition={KEYPAD_PULSE_TRANSITION}
            />

            {/* LED DISPLAY overlay — desktop only */}
            <form
              className="hidden md:flex absolute items-center justify-center"
              onSubmit={(e) => {
                e.preventDefault();
                verifyCode();
              }}
              style={{ left: "42%", top: "40%", width: "17%", height: "9%" }}
            >
              <input
                value={codeInput}
                onChange={(e) => setCodeInput(e.target.value.toUpperCase())}
                placeholder="DS-02-••••-••••-••"
                className="w-full h-full bg-transparent border-0 outline-none text-center font-mono tracking-[0.1em] text-[clamp(9px,0.95vw,14px)] uppercase"
                style={{
                  color: statusColor,
                  textShadow: `0 0 8px ${statusColor}`,
                  caretColor: statusColor,
                }}
                aria-label="Accreditation number"
                data-testid="classified-accred-input-desktop"
                autoFocus
                autoComplete="off"
                spellCheck={false}
              />
            </form>

            {(verifying || gateError) && (
              <div
                className="hidden md:block absolute font-mono uppercase tracking-[0.2em] text-[clamp(7px,0.55vw,10px)] px-1.5 py-0.5 rounded"
                style={{
                  left: "59.5%",
                  top: "39.5%",
                  color: statusColor,
                  background: "rgba(0,0,0,0.85)",
                  textShadow: `0 0 6px ${statusColor}`,
                }}
              >
                {statusLabel}
              </div>
            )}

            {/* Corner tags */}
            <div className="absolute top-3 left-3 flex items-center gap-2 px-2.5 py-1 rounded-md bg-black/60 border border-white/10 backdrop-blur-sm">
              <span
                className="w-1.5 h-1.5 rounded-full animate-pulse"
                style={{ background: statusColor }}
              />
              <span
                className="font-mono text-[9px] md:text-[10px] uppercase tracking-[0.25em]"
                style={{ color: statusColor }}
              >
                {t("classifiedVault.gateChannel")}
              </span>
            </div>
            <div className="absolute bottom-3 right-3 px-2.5 py-1 rounded-md bg-black/60 border border-white/10 backdrop-blur-sm">
              <span className="font-mono text-[9px] md:text-[10px] uppercase tracking-[0.25em] text-[#F59E0B]">
                {t("classifiedVault.gateLevel")}
              </span>
            </div>

            <AnimatePresence>
              {verifying && (
                <motion.div
                  key="verify-pulse"
                  initial={FADE_INITIAL}
                  animate={VERIFY_FLASH_ANIMATE}
                  exit={FADE_EXIT}
                  transition={VERIFY_FLASH_TRANSITION}
                  className="absolute inset-0 pointer-events-none"
                  style={{ background: "#F59E0B", mixBlendMode: "screen" }}
                />
              )}
            </AnimatePresence>
          </div>

          {/* MOBILE INPUT BELOW DOOR */}
          <div className="md:hidden mt-4">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                verifyCode();
              }}
              className="rounded-xl border border-[#F59E0B]/30 bg-black/60 p-4"
            >
              <label
                htmlFor="accred-input-mobile"
                className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/60 block mb-2"
              >
                {t("classifiedVault.gateLabel")}
              </label>
              <Input
                id="accred-input-mobile"
                value={codeInput}
                onChange={(e) => setCodeInput(e.target.value.toUpperCase())}
                placeholder="DS-02-XXXX-XXXX-XX"
                className="font-mono bg-black border-[#F59E0B]/40 text-[#F59E0B] tracking-widest placeholder:text-white/20 focus-visible:ring-[#F59E0B]/60"
                data-testid="classified-accred-input-mobile"
                autoFocus
              />
              {gateError && (
                <div className="mt-2 flex items-center gap-2 text-red-400 text-xs">
                  <AlertTriangle size={12} /> {gateError}
                </div>
              )}
              <Button
                type="submit"
                disabled={verifying}
                className="mt-4 w-full rounded-md bg-[#F59E0B] hover:bg-[#F59E0B]/90 text-black font-mono font-semibold"
                data-testid="classified-verify-btn-mobile"
              >
                {verifying
                  ? t("classifiedVault.verifying")
                  : t("classifiedVault.verify")}
              </Button>
            </form>
          </div>

          {/* DESKTOP ACTION BAR BELOW DOOR */}
          <div className="hidden md:flex mt-5 items-center justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-3 flex-wrap">
              {gateError && (
                <div className="flex items-center gap-2 text-red-400 text-xs font-mono">
                  <AlertTriangle size={12} />
                  {gateError}
                </div>
              )}
              <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-white/40">
                {t("classifiedVault.gateHintShort")}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                disabled={verifying}
                onClick={() => verifyCode()}
                className="rounded-md bg-[#F59E0B] hover:bg-[#F59E0B]/90 text-black font-mono font-semibold"
                data-testid="classified-verify-btn-desktop"
              >
                {verifying
                  ? t("classifiedVault.verifying")
                  : t("classifiedVault.verify")}{" "}
                →
              </Button>
            </div>
          </div>

          {/* Secondary info */}
          <div className="mt-6 rounded-xl border border-white/10 bg-white/[0.02] p-4">
            <p className="text-xs md:text-sm text-white/60 leading-relaxed">
              {t("classifiedVault.gateHint")}
            </p>
            <a
              href="/#vault"
              className="mt-2 inline-flex items-center gap-1 text-[11px] font-mono text-white/40 hover:text-white/80"
              data-testid="classified-back-link"
            >
              ← {t("classifiedVault.gateBack")}
            </a>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}

export default GateView;
