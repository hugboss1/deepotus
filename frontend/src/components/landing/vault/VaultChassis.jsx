import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import CombinationDial from "./CombinationDial";

/**
 * VaultChassis — wraps the 6 dials inside the AI-generated electronic vault image.
 *
 * The image reserves an empty central rectangular panel (computed in absolute %s).
 * We overlay the 6 dials and a stage pulse halo on top of that panel.
 *
 * Measured coordinates (relative to /vault_frame.png natural aspect ratio ~16:9):
 *   central panel: left 37%, top 39%, width 27%, height 25%
 *
 * On mobile (< md), we fall back to a stacked layout (handled by parent).
 */
export default function VaultChassis({
  combo = [0, 0, 0, 0, 0, 0],
  locked = 0,
  stage = "LOCKED",
  stageLabel = "LOCKED",
}) {
  const haloColor =
    stage === "DECLASSIFIED"
      ? "rgba(24,201,100,0.55)"
      : stage === "UNLOCKING" || stage === "CRACKING"
      ? "rgba(245,158,11,0.45)"
      : "rgba(239,68,68,0.35)";

  return (
    <div
      className="relative w-full overflow-hidden rounded-xl border border-border bg-black shadow-[var(--shadow-elev-1)]"
      style={{ aspectRatio: "16 / 9" }}
      data-testid="vault-chassis"
    >
      {/* Vault image */}
      <img
        src="/vault_frame.png"
        alt="PROTOCOL ΔΣ electronic vault"
        className="absolute inset-0 w-full h-full object-cover select-none pointer-events-none"
        draggable={false}
      />

      {/* Pulse halo behind the central panel (breathes with the stage) */}
      <motion.div
        aria-hidden
        className="absolute pointer-events-none"
        style={{
          left: "34%",
          top: "36%",
          width: "32%",
          height: "30%",
          background: `radial-gradient(ellipse at center, ${haloColor}, transparent 70%)`,
          filter: "blur(6px)",
        }}
        animate={{ opacity: [0.45, 0.9, 0.45] }}
        transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Dial zone — sits inside the empty central panel */}
      <div
        className="absolute flex items-center justify-center gap-[1.2%]"
        style={{ left: "37%", top: "39%", width: "27%", height: "25%" }}
        data-testid="vault-chassis-dials"
      >
        {combo.map((digit, i) => (
          <div
            key={i}
            className="flex-1 h-full"
            style={{ minWidth: 0 }}
          >
            <CombinationDial
              index={i}
              value={digit}
              locked={i < locked}
              stage={stage}
              size="chassis"
              showLabel={false}
            />
          </div>
        ))}
      </div>

      {/* Stage badge overlay — top-right corner of the image */}
      <AnimatePresence>
        <motion.div
          key={stage}
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="absolute top-[4%] left-[4%] flex items-center gap-2 px-2.5 py-1 rounded-md bg-black/60 border border-white/10 backdrop-blur-sm"
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              stage === "DECLASSIFIED"
                ? "bg-[#18C964]"
                : stage === "UNLOCKING" || stage === "CRACKING"
                ? "bg-[#F59E0B]"
                : "bg-red-500"
            } animate-pulse`}
          />
          <span
            className={`font-mono text-[9px] md:text-[10px] uppercase tracking-[0.25em] ${
              stage === "DECLASSIFIED"
                ? "text-[#18C964]"
                : stage === "UNLOCKING" || stage === "CRACKING"
                ? "text-[#F59E0B]"
                : "text-red-400"
            }`}
          >
            {stageLabel}
          </span>
        </motion.div>
      </AnimatePresence>

      {/* Locked/unlocked counter — bottom-left corner */}
      <div className="absolute bottom-[4%] left-[4%] px-2.5 py-1 rounded-md bg-black/60 border border-white/10 backdrop-blur-sm">
        <span className="font-mono text-[9px] md:text-[10px] uppercase tracking-[0.25em] text-white/90">
          {locked}/{combo.length} dials
        </span>
      </div>

      {/* Declassified flash */}
      <AnimatePresence>
        {stage === "DECLASSIFIED" && (
          <motion.div
            key="declass-flash"
            initial={{ opacity: 0 }}
            animate={{ opacity: [0, 0.3, 0] }}
            transition={{ duration: 1.8, repeat: Infinity }}
            className="absolute inset-0 pointer-events-none bg-[#18C964] mix-blend-screen"
          />
        )}
      </AnimatePresence>
    </div>
  );
}
