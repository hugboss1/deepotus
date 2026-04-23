import React, { useEffect, useRef, useState } from "react";
import { motion, useAnimation } from "framer-motion";
import { Lock, Unlock } from "lucide-react";

/**
 * CombinationDial — a single 0-9 reel with mechanical rotation.
 *
 * Props:
 *  - value: target digit (shown when locked)
 *  - locked: if true, freeze on `value` with green halo
 *  - stage: LOCKED | CRACKING | UNLOCKING | DECLASSIFIED — styling hint
 *  - index: dial position (staggers shuffle phase)
 *  - size: "default" | "sm" | "chassis"
 *      default → w-14 h-20 md:w-16 md:h-24 (standalone)
 *      sm      → smaller, for narrow contexts
 *      chassis → fills its parent (used inside the vault-image overlay). In chassis
 *                mode, sizing is driven 100% by the parent; no min/max.
 */

// ---------------------------------------------------------------------
// Pure style helpers (pulled out of the component to flatten complexity)
// ---------------------------------------------------------------------
const LOCKED_STYLE = {
  ring: "ring-[#18C964]/60",
  glow: "shadow-[0_0_18px_rgba(24,201,100,0.35)]",
  text: "text-[#18C964]",
};

const DECLASSIFIED_STYLE = {
  ring: "ring-[#18C964]/80",
  glow: "shadow-[0_0_24px_rgba(24,201,100,0.45)]",
  text: "text-[#18C964]",
};

const MICRO_FLASH_STYLE = {
  ring: "ring-[#F59E0B]",
  glow: "shadow-[0_0_26px_rgba(245,158,11,0.7)]",
  text: "text-[#F59E0B]",
};

const ACTIVE_STYLE = {
  ring: "ring-[#F59E0B]/60",
  glow: "shadow-[0_0_14px_rgba(245,158,11,0.3)]",
  text: "text-[#F59E0B]",
};

const UNLOCKING_STYLE = {
  ring: "ring-[#F59E0B]/70",
  glow: "shadow-[0_0_18px_rgba(245,158,11,0.35)]",
  text: "text-[#F59E0B]",
};

const CRACKING_STYLE = {
  ring: "ring-[#F59E0B]/50",
  glow: "shadow-[0_0_12px_rgba(245,158,11,0.25)]",
  text: "text-[#F59E0B]",
};

const LOCKED_FALLBACK_STYLE = {
  ring: "ring-red-500/50",
  glow: "shadow-[0_0_14px_rgba(239,68,68,0.25)]",
  text: "text-red-400",
};

function computeStageStyle({ locked, stage, microFlash, isActive }) {
  if (locked) return LOCKED_STYLE;
  if (stage === "DECLASSIFIED") return DECLASSIFIED_STYLE;
  if (microFlash) return MICRO_FLASH_STYLE;
  if (isActive) return ACTIVE_STYLE;
  if (stage === "UNLOCKING") return UNLOCKING_STYLE;
  if (stage === "CRACKING") return CRACKING_STYLE;
  return LOCKED_FALLBACK_STYLE;
}

function computeDimensions(size) {
  if (size === "chassis") {
    return {
      dims: "w-full h-full",
      fontSize: "text-[clamp(11px,2.8vw,42px)]",
      bgTint: "bg-black/80 backdrop-blur-[1px]",
    };
  }
  if (size === "sm") {
    return {
      dims: "w-10 h-14",
      fontSize: "text-2xl",
      bgTint: "bg-background",
    };
  }
  return {
    dims: "w-14 h-20 md:w-16 md:h-24",
    fontSize: "text-3xl md:text-4xl",
    bgTint: "bg-background",
  };
}

// ---------------------------------------------------------------------
// Custom hooks — encapsulate side-effects so the JSX stays declarative
// ---------------------------------------------------------------------
function useShuffleLoop({ locked, value, index, controls, setDisplay }) {
  useEffect(() => {
    if (locked) {
      setDisplay(value);
      return undefined;
    }
    let cancelled = false;
    const tick = () => {
      if (cancelled) return;
      setDisplay((d) => {
        const next = Math.floor(Math.random() * 10);
        return next === d ? (d + 1) % 10 : next;
      });
      controls.start({
        y: [-3, 0],
        transition: { duration: 0.22, ease: "easeOut" },
      });
    };
    const interval = 520 + (index % 6) * 80;
    const id = setInterval(tick, interval);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [locked, value, controls, index, setDisplay]);
}

function useMicroTickFlash({
  microTickVersion,
  isActive,
  locked,
  controls,
  setDisplay,
  setMicroFlash,
}) {
  const lastMicroRef = useRef(microTickVersion);
  useEffect(() => {
    if (locked || !isActive) return undefined;
    if (microTickVersion === lastMicroRef.current) return undefined;
    lastMicroRef.current = microTickVersion;
    setDisplay((d) => (d + 1) % 10);
    setMicroFlash(true);
    controls.start({
      y: [-8, 0],
      scale: [1.04, 1],
      transition: { duration: 0.28, ease: "easeOut" },
    });
    const t = setTimeout(() => setMicroFlash(false), 360);
    return () => clearTimeout(t);
  }, [microTickVersion, isActive, locked, controls, setDisplay, setMicroFlash]);
}

// ---------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------
export default function CombinationDial({
  value = 0,
  locked = false,
  stage = "LOCKED",
  index = 0,
  size = "default",
  showLabel = true,
  isActive = false, // true = first unlocked dial (receives micro-ticks)
  microTickVersion = 0, // increments when a new micro-purchase is detected
}) {
  const [display, setDisplay] = useState(value);
  const [microFlash, setMicroFlash] = useState(false);
  const controls = useAnimation();

  useShuffleLoop({ locked, value, index, controls, setDisplay });
  useMicroTickFlash({
    microTickVersion,
    isActive,
    locked,
    controls,
    setDisplay,
    setMicroFlash,
  });

  const stageStyles = computeStageStyle({ locked, stage, microFlash, isActive });
  const { dims, fontSize, bgTint } = computeDimensions(size);

  const containerClass =
    size === "chassis"
      ? "flex flex-col items-center justify-center w-full h-full"
      : "flex flex-col items-center gap-2";

  return (
    <div className={containerClass} data-testid={`vault-dial-${index}`}>
      <div
        className={`relative ${dims} rounded-md ${bgTint} border border-border/50 ring-2 ${stageStyles.ring} ${stageStyles.glow} overflow-hidden flex items-center justify-center transition-shadow duration-300`}
      >
        <div className="absolute inset-x-0 top-0 h-1/3 bg-gradient-to-b from-black/40 to-transparent pointer-events-none" />
        <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-black/40 to-transparent pointer-events-none" />
        <motion.div
          animate={controls}
          className={`font-mono font-bold ${fontSize} select-none ${stageStyles.text}`}
        >
          {display}
        </motion.div>
        {locked && size !== "chassis" && (
          <div className="absolute top-1 right-1 text-[#18C964]">
            <Lock size={10} strokeWidth={2.5} />
          </div>
        )}
        {!locked && stage === "DECLASSIFIED" && size !== "chassis" && (
          <div className="absolute top-1 right-1 text-[#18C964]">
            <Unlock size={10} strokeWidth={2.5} />
          </div>
        )}
      </div>
      {showLabel && size !== "chassis" && (
        <span
          className={`font-mono text-[9px] uppercase tracking-[0.2em] ${
            locked ? "text-[#18C964]" : "text-muted-foreground"
          }`}
        >
          {locked ? "LOCKED" : "◌"}
        </span>
      )}
    </div>
  );
}
