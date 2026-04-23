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
export default function CombinationDial({
  value = 0,
  locked = false,
  stage = "LOCKED",
  index = 0,
  size = "default",
  showLabel = true,
}) {
  const [display, setDisplay] = useState(value);
  const controls = useAnimation();
  const rafRef = useRef(null);

  useEffect(() => {
    if (locked) {
      setDisplay(value);
      return;
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
  }, [locked, value, controls, index]);

  useEffect(() => {
    const r = rafRef;
    return () => {
      if (r.current) cancelAnimationFrame(r.current);
    };
  }, []);

  const stageStyles = (() => {
    if (locked) {
      return {
        ring: "ring-[#18C964]/60",
        glow: "shadow-[0_0_18px_rgba(24,201,100,0.35)]",
        text: "text-[#18C964]",
      };
    }
    if (stage === "DECLASSIFIED") {
      return {
        ring: "ring-[#18C964]/80",
        glow: "shadow-[0_0_24px_rgba(24,201,100,0.45)]",
        text: "text-[#18C964]",
      };
    }
    if (stage === "UNLOCKING") {
      return {
        ring: "ring-[#F59E0B]/70",
        glow: "shadow-[0_0_18px_rgba(245,158,11,0.35)]",
        text: "text-[#F59E0B]",
      };
    }
    if (stage === "CRACKING") {
      return {
        ring: "ring-[#F59E0B]/50",
        glow: "shadow-[0_0_12px_rgba(245,158,11,0.25)]",
        text: "text-[#F59E0B]",
      };
    }
    return {
      ring: "ring-red-500/50",
      glow: "shadow-[0_0_14px_rgba(239,68,68,0.25)]",
      text: "text-red-400",
    };
  })();

  // Sizing presets
  const dims =
    size === "chassis"
      ? "w-full h-full"
      : size === "sm"
      ? "w-10 h-14"
      : "w-14 h-20 md:w-16 md:h-24";
  const fontSize =
    size === "chassis"
      ? "text-[clamp(14px,3vw,42px)]"
      : size === "sm"
      ? "text-2xl"
      : "text-3xl md:text-4xl";
  const bgTint =
    size === "chassis"
      ? "bg-black/80 backdrop-blur-[1px]"
      : "bg-background";

  return (
    <div
      className={
        size === "chassis"
          ? "flex flex-col items-center justify-center w-full h-full"
          : "flex flex-col items-center gap-2"
      }
      data-testid={`vault-dial-${index}`}
    >
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
          className={`font-mono text-[9px] uppercase tracking-[0.2em] ${locked ? "text-[#18C964]" : "text-muted-foreground"}`}
        >
          {locked ? "LOCKED" : "◌"}
        </span>
      )}
    </div>
  );
}
