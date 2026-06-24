/**
 * TwoTracksGraph — Sprint 20.3 sequenced bubble-graph visualisation.
 *
 * The previous Sprint 20.2 version showed 9 floating nodes with all
 * connections running in parallel (ambient motion). This iteration
 * turns the canvas into a **narrative bubble-graph** that loops a
 * funding flow: products feed the central hub, then the hub
 * redistributes to the secret-project wallets.
 *
 * Sequence (one loop ≈ 8.5 s)
 * ===========================
 *
 *   Phase 0  · reset (nothing active)
 *   Phase 1  · Roman ─→ Acquisition       (Roman bubble pulses)
 *   Phase 2  · Board game ─→ Acquisition  (Board game bubble pulses)
 *   Phase 3  · Video Generator ─→ Acquisition
 *   Phase 4  · Mobile ─→ Acquisition       (4 A→Hub lines all visible)
 *   Phase 5  · Acquisition grows · "climax / collection complete"
 *   Phase 6  · Acquisition ─→ Σ1 Foundations  (Σ1 grows)
 *   Phase 7  · Acquisition ─→ Σ3 Silent build (Σ3 grows)
 *   Phase 8  · Acquisition ─→ Σ4 Community    (Σ4 grows)
 *   Phase 9  · Acquisition ─→ Σ5 Curtain      (Σ5 grows — END of cycle)
 *   Phase 10 · final pause (all bubbles + 8 lines persistent)
 *   ↻ reset to phase 0
 *
 * Each link, once drawn, **stays visible** until the loop resets.
 * That mirrors the user requirement: "les liens, une fois établis,
 * doivent rester persistents jusqu'à la fin de la boucle qui est la
 * bulle Levée de rideau".
 *
 * Geometry
 * ========
 * - Track A : 4 bubbles in the LEFT column (cx = 12 %)
 * - Hub Acquisition : CENTERED (cx = 50 %, cy = 50 %)
 * - Track B : 4 bubbles (Σ1, Σ3, Σ4, Σ5) in the RIGHT column (cx = 88 %)
 * - Connections start/end **on the circle borders** (vector trim) so
 *   strokes never enter the bubble disc — the bubble-graph look.
 *
 * Layout / a11y / motion notes
 * ============================
 * - Column titles moved OUT of the canvas (top header bar) so they
 *   never overlap with the bubbles.
 * - Each bubble is a real `<button>` (modal on click/tap, full a11y).
 * - Active bubbles grow via Framer Motion `scale`. Inactive bubbles
 *   keep a subtle ambient float (CSS keyframe, GPU-only transform).
 * - Connections are SVG `<motion.path>` with animated stroke-dashoffset
 *   for the "data flowing" effect; the path appears with a
 *   `pathLength` 0→1 animation at its scheduled phase.
 * - `prefers-reduced-motion` collapses every animation while keeping
 *   the final state visually correct (all bubbles + lines static).
 */
import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import {
  BookOpen,
  Dices,
  Wand2,
  Smartphone,
  Coins,
  Banknote,
  Construction,
  Heart,
  EyeOff,
  X,
  Sparkles,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useI18n } from "@/i18n/I18nProvider";
import "./TwoTracksGraph.css";

// ---------------------------------------------------------------------
// Types & data
// ---------------------------------------------------------------------
type Track = "A" | "B";

interface TranslatedStep {
  code: string;
  label: string;
  note: string;
  wallet?: string;
}

interface GraphNode {
  id: string;
  track: Track;
  Icon: LucideIcon;
  /** % of container width (svg viewBox is 1000) */
  cx: number;
  /** % of container height (svg viewBox is 600) */
  cy: number;
  /** Per-node ambient float duration in seconds. */
  floatDuration: number;
  floatDelay: number;
  /** Index into the corresponding i18n step array. */
  i18nIndex: number;
  /** True for the central Acquisition / Fees hub. */
  isHub?: boolean;
  /** Phase at which the bubble grows / activates (0 = always inactive at reset). */
  activatePhase: number;
}

// Track A — products. 4 bubbles, evenly distributed in the left column,
// each activated when its outgoing link to the hub is drawn.
const TRACK_A_NODES: GraphNode[] = [
  { id: "roman",     track: "A", Icon: BookOpen,   cx: 12, cy: 18, floatDuration: 5.0, floatDelay: 0.0, i18nIndex: 0, activatePhase: 1 },
  { id: "boardgame", track: "A", Icon: Dices,      cx: 12, cy: 40, floatDuration: 6.4, floatDelay: 0.7, i18nIndex: 1, activatePhase: 2 },
  { id: "videogen",  track: "A", Icon: Wand2,      cx: 12, cy: 62, floatDuration: 5.8, floatDelay: 1.3, i18nIndex: 2, activatePhase: 3 },
  { id: "mobile",    track: "A", Icon: Smartphone, cx: 12, cy: 84, floatDuration: 7.2, floatDelay: 0.4, i18nIndex: 3, activatePhase: 4 },
];

// Central hub — Acquisition / Fees (Σ2).
const HUB_NODE: GraphNode = {
  id: "acquisition",
  track: "B",
  Icon: Banknote,
  cx: 50,
  cy: 50,
  floatDuration: 4.8,
  floatDelay: 0.0,
  i18nIndex: 1,
  isHub: true,
  activatePhase: 5,
};

// Track B — secret project. 4 bubbles in the right column (Σ1, Σ3,
// Σ4, Σ5). Σ2 has been promoted to the central hub.
//
// IMPORTANT: ``i18nIndex`` keeps pointing at the original step array
// positions (0=Σ1, 2=Σ3, 3=Σ4, 4=Σ5) so the modal copy stays in sync
// with translations.js without any data duplication.
const TRACK_B_NODES: GraphNode[] = [
  { id: "fondations", track: "B", Icon: Coins,        cx: 88, cy: 16, floatDuration: 6.0, floatDelay: 0.2, i18nIndex: 0, activatePhase: 6 },
  { id: "silent",     track: "B", Icon: Construction, cx: 88, cy: 39, floatDuration: 7.0, floatDelay: 0.9, i18nIndex: 2, activatePhase: 7 },
  { id: "community",  track: "B", Icon: Heart,        cx: 88, cy: 62, floatDuration: 5.6, floatDelay: 1.4, i18nIndex: 3, activatePhase: 8 },
  { id: "curtain",    track: "B", Icon: EyeOff,       cx: 88, cy: 85, floatDuration: 6.6, floatDelay: 0.6, i18nIndex: 4, activatePhase: 9 },
];

const ALL_NODES: GraphNode[] = [...TRACK_A_NODES, HUB_NODE, ...TRACK_B_NODES];

// Sequenced connections. Each connection appears at its ``phase`` and
// stays visible until the loop resets.
interface Connection {
  from: string;
  to: string;
  phase: number;
  flowDuration: number;
}

const CONNECTIONS: Connection[] = [
  // A → Hub (collection / income)
  { from: "roman",     to: "acquisition", phase: 1, flowDuration: 2.6 },
  { from: "boardgame", to: "acquisition", phase: 2, flowDuration: 2.4 },
  { from: "videogen",  to: "acquisition", phase: 3, flowDuration: 2.8 },
  { from: "mobile",    to: "acquisition", phase: 4, flowDuration: 2.7 },
  // Hub → Σ (redistribution)
  { from: "acquisition", to: "fondations", phase: 6, flowDuration: 2.5 },
  { from: "acquisition", to: "silent",     phase: 7, flowDuration: 2.6 },
  { from: "acquisition", to: "community",  phase: 8, flowDuration: 2.4 },
  { from: "acquisition", to: "curtain",    phase: 9, flowDuration: 2.7 },
];

// Loop timing. Tweak with care — the narrative reads best at ~700ms
// per phase + a generous final pause so the eye can rest on the full
// network before it resets.
const PHASE_DURATION_MS = 750;
const FINAL_PAUSE_MS = 1800;
const TOTAL_PHASES = 10; // Phase 10 is the final pause; loop resets to 0 afterwards.

// Approximate radii in viewBox units (the SVG uses viewBox 1000×600
// with preserveAspectRatio="none"). These don't have to match the
// rendered pixel radii exactly — the goal is only that connection
// strokes never appear to enter the visual disc of a bubble.
const HUB_RADIUS_VB = 56;
const NODE_RADIUS_VB = 38;

// ---------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------
/**
 * Build a smooth cubic-bezier path whose endpoints sit ON the borders
 * of the source/target circles (border trim via the direction unit
 * vector).
 *
 * The control points are biased horizontally so A→Hub and Hub→B
 * connections render as clean, readable arcs that visually leave the
 * source bubble on its right side and enter the destination bubble on
 * its left side — exactly the bubble-graph aesthetic the user asked
 * for.
 */
function buildBorderPath(from: GraphNode, to: GraphNode): string {
  const fromR = from.isHub ? HUB_RADIUS_VB : NODE_RADIUS_VB;
  const toR = to.isHub ? HUB_RADIUS_VB : NODE_RADIUS_VB;

  const x1 = (from.cx / 100) * 1000;
  const y1 = (from.cy / 100) * 600;
  const x2 = (to.cx / 100) * 1000;
  const y2 = (to.cy / 100) * 600;

  const dx = x2 - x1;
  const dy = y2 - y1;
  const dist = Math.sqrt(dx * dx + dy * dy) || 1;
  const ux = dx / dist;
  const uy = dy / dist;

  // Border-trim start / end points
  const sx = x1 + ux * fromR;
  const sy = y1 + uy * fromR;
  const ex = x2 - ux * toR;
  const ey = y2 - uy * toR;

  // Horizontal-biased control points — gives a soft S-curve.
  const c1x = sx + (ex - sx) * 0.55;
  const c1y = sy;
  const c2x = ex - (ex - sx) * 0.55;
  const c2y = ey;

  return `M ${sx.toFixed(1)} ${sy.toFixed(1)} C ${c1x.toFixed(1)} ${c1y.toFixed(1)}, ${c2x.toFixed(1)} ${c2y.toFixed(1)}, ${ex.toFixed(1)} ${ey.toFixed(1)}`;
}

// ---------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------
export function TwoTracksGraph(): JSX.Element {
  const { t } = useI18n();
  // Wrapped in useMemo so the reference is stable across renders — the
  // `active` useMemo below depends on these, and a fresh array each render
  // (from the `|| []` fallback) would defeat its memoisation.
  const trackA = useMemo<TranslatedStep[]>(
    () => (t("roadmapTracks.trackA.steps") as TranslatedStep[]) || [],
    [t],
  );
  const trackB = useMemo<TranslatedStep[]>(
    () => (t("roadmapTracks.trackB.steps") as TranslatedStep[]) || [],
    [t],
  );

  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);
  /** Current phase index (0..10). */
  const [phase, setPhase] = useState<number>(0);

  // Loop driver — recursive setTimeout so each phase can have its own
  // dwell time. Cleaned up on unmount.
  const cancelledRef = useRef<boolean>(false);
  useEffect(() => {
    cancelledRef.current = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    let current = 0;

    const advance = (): void => {
      if (cancelledRef.current) return;
      // Compute the NEXT phase. After TOTAL_PHASES we reset to 0.
      current = current >= TOTAL_PHASES ? 0 : current + 1;
      setPhase(current);
      // Phase 10 (the final pause) gets a longer dwell.
      const dwell = current === TOTAL_PHASES ? FINAL_PAUSE_MS : PHASE_DURATION_MS;
      timer = setTimeout(advance, dwell);
    };

    // Initial kick — a short delay so the graph mounts in its reset
    // state, giving the viewer a beat before the sequence begins.
    timer = setTimeout(advance, 600);

    return (): void => {
      cancelledRef.current = true;
      if (timer) clearTimeout(timer);
    };
  }, []);

  // Memoised maps (node-by-id + path cache).
  const nodeMap = useMemo<Record<string, GraphNode>>(() => {
    const m: Record<string, GraphNode> = {};
    for (const n of ALL_NODES) m[n.id] = n;
    return m;
  }, []);

  const connectionPaths = useMemo(() => {
    return CONNECTIONS.map((c) => {
      const from = nodeMap[c.from];
      const to = nodeMap[c.to];
      return { ...c, d: from && to ? buildBorderPath(from, to) : "" };
    });
  }, [nodeMap]);

  // Resolve the active node for the modal (decoupled from sequence).
  const active = useMemo(() => {
    if (!activeNodeId) return null;
    const node = nodeMap[activeNodeId];
    if (!node) return null;
    const arr = node.track === "A" ? trackA : trackB;
    const step = arr[node.i18nIndex];
    if (!step) return null;
    return { node, step };
  }, [activeNodeId, nodeMap, trackA, trackB]);

  // Phase-derived helpers
  const isConnectionVisible = (connectionPhase: number): boolean => {
    if (phase === 0) return false; // reset
    return phase >= connectionPhase;
  };
  const isNodeAmplified = (nodeActivatePhase: number): boolean => {
    if (phase === 0) return false; // reset
    return phase >= nodeActivatePhase;
  };

  return (
    <>
      <div
        className="rounded-2xl border border-border/60 bg-card/30 backdrop-blur-sm two-tracks-graph overflow-hidden"
        data-testid="two-tracks-graph"
      >
        {/* ────────── Header (column titles, OUT of the canvas) ────────── */}
        <div
          className="flex items-center justify-between gap-3 px-5 sm:px-7 py-3 border-b border-border/40 bg-background/40"
          data-testid="ttg-header"
        >
          <div
            className="font-mono text-[9px] sm:text-[11px] uppercase tracking-[0.28em] text-amber-300/90"
            data-testid="ttg-track-a-title"
          >
            <span className="hidden sm:inline">
              {(t("roadmapTracks.trackA.label") as string) || "TRACK A"}
            </span>
            <span className="sm:hidden">Track A</span>
          </div>
          <div
            className="hidden md:flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.24em] text-foreground/45"
            aria-hidden
          >
            <Sparkles className="h-3 w-3" />
            Acquisition / Fees
          </div>
          <div
            className="font-mono text-[9px] sm:text-[11px] uppercase tracking-[0.28em] text-cyan-300/90"
            data-testid="ttg-track-b-title"
          >
            <span className="hidden sm:inline">
              {(t("roadmapTracks.trackB.label") as string) || "TRACK B"}
            </span>
            <span className="sm:hidden">Track B</span>
          </div>
        </div>

        {/* ────────── Canvas (bubbles + animated connections) ────────── */}
        <div
          className="relative w-full"
          style={{ aspectRatio: "16 / 9" }}
          data-testid="ttg-canvas"
        >
          {/* Decorative dual-tone wash (kept faint per design rule) */}
          <div
            aria-hidden
            className="absolute inset-0"
            style={{
              background:
                "radial-gradient(40% 60% at 14% 50%, rgba(245,158,11,0.10) 0%, rgba(0,0,0,0) 70%), radial-gradient(40% 60% at 86% 50%, rgba(45,212,191,0.10) 0%, rgba(0,0,0,0) 70%), radial-gradient(28% 36% at 50% 50%, rgba(45,212,191,0.10) 0%, rgba(0,0,0,0) 70%)",
            }}
          />

          {/* SVG connections layer */}
          <svg
            viewBox="0 0 1000 600"
            preserveAspectRatio="none"
            className="absolute inset-0 w-full h-full"
            aria-hidden
          >
            <defs>
              <linearGradient id="grad-a-to-b" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="rgba(245, 158, 11, 0.95)" />
                <stop offset="55%" stopColor="rgba(245, 158, 11, 0.65)" />
                <stop offset="100%" stopColor="rgba(45, 212, 191, 0.80)" />
              </linearGradient>
              <linearGradient id="grad-hub-out" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="rgba(45, 212, 191, 0.85)" />
                <stop offset="100%" stopColor="rgba(45, 212, 191, 0.50)" />
              </linearGradient>
            </defs>

            {connectionPaths.map((c) => {
              if (!c.d) return null;
              const visible = isConnectionVisible(c.phase);
              const stroke =
                nodeMap[c.from].track === "A"
                  ? "url(#grad-a-to-b)"
                  : "url(#grad-hub-out)";
              return (
                <g key={`${c.from}-${c.to}`}>
                  {/* Faint base line — only when visible */}
                  <motion.path
                    d={c.d}
                    fill="none"
                    stroke={stroke}
                    strokeWidth={1.4}
                    strokeLinecap="round"
                    initial={false}
                    animate={{
                      pathLength: visible ? 1 : 0,
                      opacity: visible ? 0.55 : 0,
                    }}
                    transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                  />
                  {/* Flowing dashes — animates only when visible */}
                  <motion.path
                    d={c.d}
                    fill="none"
                    stroke={stroke}
                    strokeWidth={2.4}
                    strokeLinecap="round"
                    strokeDasharray="4 14"
                    initial={false}
                    animate={{
                      pathLength: visible ? 1 : 0,
                      opacity: visible ? 1 : 0,
                    }}
                    transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
                    className={visible ? "ttg-flow" : undefined}
                    style={{ animationDuration: `${c.flowDuration}s` }}
                  />
                </g>
              );
            })}
          </svg>

          {/* Nodes layer — absolute-positioned buttons */}
          {ALL_NODES.map((node) => {
            const arr = node.track === "A" ? trackA : trackB;
            const step = arr[node.i18nIndex] || { code: "", label: node.id, note: "" };
            const amplified = isNodeAmplified(node.activatePhase);
            const colorRing =
              node.track === "A"
                ? "border-amber-500/55 bg-amber-500/12 text-amber-200 ring-amber-500/30 focus-visible:ring-amber-400/70"
                : "border-cyan-500/55 bg-cyan-500/12 text-cyan-200 ring-cyan-500/30 focus-visible:ring-cyan-400/70";
            const colorRingActive =
              node.track === "A"
                ? "border-amber-400/90 bg-amber-500/22 text-amber-50 ring-amber-400/50 shadow-[0_0_0_6px_rgba(245,158,11,0.10),_0_18px_40px_rgba(245,158,11,0.18)]"
                : "border-cyan-400/90 bg-cyan-500/22 text-cyan-50 ring-cyan-400/50 shadow-[0_0_0_6px_rgba(45,212,191,0.10),_0_18px_40px_rgba(45,212,191,0.18)]";
            const labelColor =
              node.track === "A" ? "text-amber-300/85" : "text-cyan-300/85";
            // Hub gets bigger base size + bigger amplified size.
            const sizeBase = node.isHub
              ? "h-14 w-14 sm:h-20 sm:w-20"
              : "h-11 w-11 sm:h-14 sm:w-14";
            const iconSize = node.isHub
              ? "h-6 w-6 sm:h-8 sm:w-8"
              : "h-4 w-4 sm:h-6 sm:w-6";
            return (
              <button
                key={node.id}
                type="button"
                onClick={() => setActiveNodeId(node.id)}
                aria-label={`${step.code ? step.code + " — " : ""}${step.label}`}
                data-testid={`ttg-node-${node.id}`}
                className="absolute -translate-x-1/2 -translate-y-1/2 ttg-node-wrap focus:outline-none"
                style={{
                  left: `${node.cx}%`,
                  top: `${node.cy}%`,
                  ["--ttg-float-duration" as string]: `${node.floatDuration}s`,
                  ["--ttg-float-delay" as string]: `${node.floatDelay}s`,
                }}
              >
                {/* Ambient float wrapper (paused when amplified to avoid
                    competing with the grow motion). */}
                <span
                  className={`${amplified ? "" : "ttg-node-float"} inline-block`}
                  style={{ willChange: "transform" }}
                >
                  <motion.span
                    initial={false}
                    animate={{
                      scale: amplified ? (node.isHub ? 1.18 : 1.22) : 1,
                    }}
                    transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
                    className={`relative grid place-items-center rounded-full border ring-4 transition-colors duration-300 ${sizeBase} ${
                      amplified ? colorRingActive : colorRing
                    }`}
                  >
                    {/* Pulse ring (only on the hub once it's amplified) */}
                    {node.isHub && amplified && (
                      <span
                        aria-hidden
                        className="absolute inset-0 rounded-full border border-cyan-400/45 ttg-pulse"
                      />
                    )}
                    <node.Icon className={iconSize} aria-hidden />
                  </motion.span>
                </span>
                <span
                  className={`block mt-1.5 font-mono text-[8.5px] sm:text-[10px] uppercase tracking-[0.18em] text-center ${labelColor} max-w-[92px] sm:max-w-[120px] truncate`}
                >
                  {step.code ? `${step.code} · ` : ""}
                  {step.label}
                </span>
              </button>
            );
          })}

          {/* Helper hint anchored at the bottom-right (compact, non-blocking) */}
          <div
            className="absolute bottom-2 right-3 font-mono text-[8.5px] sm:text-[10px] uppercase tracking-[0.22em] text-foreground/45 pointer-events-none select-none"
            data-testid="ttg-helper-hint"
          >
            <Sparkles className="inline h-3 w-3 mr-1 -translate-y-px" aria-hidden />
            {t("roadmapTracks.modal.helperHint")}
          </div>
        </div>
      </div>

      {/* ────────── Detail modal ────────── */}
      <Dialog
        open={!!active}
        onOpenChange={(open: boolean) => {
          if (!open) setActiveNodeId(null);
        }}
      >
        <DialogContent className="sm:max-w-md" data-testid="ttg-modal">
          {active && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-3">
                  <span
                    className={`grid place-items-center h-12 w-12 rounded-full border ${
                      active.node.track === "A"
                        ? "border-amber-500/45 bg-amber-500/12 text-amber-300"
                        : "border-cyan-500/45 bg-cyan-500/12 text-cyan-300"
                    }`}
                    aria-hidden
                  >
                    <active.node.Icon className="h-6 w-6" />
                  </span>
                  <div className="min-w-0">
                    <Badge
                      variant="outline"
                      className={`font-mono text-[9px] uppercase tracking-[0.22em] ${
                        active.node.track === "A"
                          ? "border-amber-500/45 text-amber-300/95 bg-amber-500/[0.06]"
                          : "border-cyan-500/45 text-cyan-300/95 bg-cyan-500/[0.06]"
                      }`}
                      data-testid="ttg-modal-track-badge"
                    >
                      {active.node.track === "A"
                        ? t("roadmapTracks.modal.productTrackLabel")
                        : t("roadmapTracks.modal.secretTrackLabel")}
                    </Badge>
                    <DialogTitle
                      className="mt-2 font-display font-semibold text-lg"
                      data-testid="ttg-modal-title"
                    >
                      {active.step.code ? `${active.step.code} · ` : ""}
                      {active.step.label}
                    </DialogTitle>
                  </div>
                </div>
              </DialogHeader>

              {active.step.wallet && (
                <div
                  className="mt-2 flex items-center gap-2"
                  data-testid="ttg-modal-wallet"
                >
                  <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-foreground/55">
                    {t("roadmapTracks.modal.walletLabel")}
                  </span>
                  <Badge
                    variant="outline"
                    className="font-mono text-[10px] uppercase tracking-[0.22em] border-cyan-500/40 text-cyan-200 bg-cyan-500/[0.06]"
                  >
                    {active.step.wallet}
                  </Badge>
                </div>
              )}

              <DialogDescription
                className="mt-3 text-sm leading-relaxed text-foreground/80 font-body"
                data-testid="ttg-modal-note"
              >
                {active.step.note}
              </DialogDescription>

              <div className="mt-5 flex justify-end">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setActiveNodeId(null)}
                  className="gap-2"
                  data-testid="ttg-modal-close"
                >
                  <X className="h-4 w-4" aria-hidden />
                  {t("roadmapTracks.modal.closeCta")}
                </Button>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
