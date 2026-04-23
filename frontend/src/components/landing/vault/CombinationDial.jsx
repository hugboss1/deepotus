import React, { useEffect, useRef, useState } from "react";
import { motion, useAnimation } from "framer-motion";
import { Lock, Unlock } from "lucide-react";

/**
 * CombinationDial — a single 0-9 vertical reel with mechanical rotation.
 *
 * Props:
 *  - value: number 0-9 (target digit when locked, or current display digit)
 *  - locked: boolean (locked dials freeze on their digit with green halo)
 *  - spinning: boolean (unlocked dials shuffle every 650ms by default)
 *  - stage: string (LOCKED | CRACKING | UNLOCKING | DECLASSIFIED) — styling hint
 *  - index: number — dial position, influences shuffle phase
 */
export default function CombinationDial({
  value = 0,
  locked = false,
  spinning = false,
  stage = "LOCKED",
  index = 0,
}) {
  const [display, setDisplay] = useState(value);
  const controls = useAnimation();
  const rafRef = useRef(null);

  // When locked: stop shuffle, show value
  // When unlocked: shuffle every ~600ms (phase-shifted by index for organic feel)
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
      // Animate a small rotation bump
      controls.start({
        y: [-4, 0],
        transition: { duration: 0.22, ease: "easeOut" },
      });
    };
    const interval = 520 + (index % 6) * 80; // stagger by dial index
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
        label: "LOCKED",
      };
    }
    if (stage === "DECLASSIFIED") {
      return {
        ring: "ring-[#18C964]/80",
        glow: "shadow-[0_0_24px_rgba(24,201,100,0.45)]",
        text: "text-[#18C964]",
        label: "OPEN",
      };
    }
    if (stage === "UNLOCKING") {
      return {
        ring: "ring-[#F59E0B]/70",
        glow: "shadow-[0_0_18px_rgba(245,158,11,0.35)]",
        text: "text-[#F59E0B]",
        label: "CRACKING",
      };
    }
    if (stage === "CRACKING") {
      return {
        ring: "ring-[#F59E0B]/50",
        glow: "shadow-[0_0_12px_rgba(245,158,11,0.25)]",
        text: "text-[#F59E0B]",
        label: "CRACKING",
      };
    }
    return {
      ring: "ring-red-500/50",
      glow: "shadow-[0_0_14px_rgba(239,68,68,0.25)]",
      text: "text-red-400",
      label: "LOCKED",
    };
  })();

  return (
    <div
      className="flex flex-col items-center gap-2"
      data-testid={`vault-dial-${index}`}
    >
      <div
        className={`relative w-14 h-20 md:w-16 md:h-24 rounded-lg bg-background border border-border ring-2 ${stageStyles.ring} ${stageStyles.glow} overflow-hidden flex items-center justify-center transition-shadow duration-300`}
      >
        {/* Vertical bevel lines for mechanical reel feel */}
        <div className="absolute inset-x-0 top-0 h-1/3 bg-gradient-to-b from-black/30 to-transparent dark:from-black/60 pointer-events-none" />
        <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-black/30 to-transparent dark:from-black/60 pointer-events-none" />
        <motion.div
          animate={controls}
          className={`font-mono font-bold text-3xl md:text-4xl select-none ${stageStyles.text}`}
        >
          {display}
        </motion.div>
        {locked && (
          <div className="absolute top-1 right-1 text-[#18C964]">
            <Lock size={10} strokeWidth={2.5} />
          </div>
        )}
        {!locked && stage === "DECLASSIFIED" && (
          <div className="absolute top-1 right-1 text-[#18C964]">
            <Unlock size={10} strokeWidth={2.5} />
          </div>
        )}
      </div>
      <span
        className={`font-mono text-[9px] uppercase tracking-[0.2em] ${locked ? "text-[#18C964]" : "text-muted-foreground"}`}
      >
        {locked ? "LOCKED" : "◌"}
      </span>
    </div>
  );
}
