/**
 * TwoTracksGraph — Sprint 20.2 interactive visualisation replacing the
 * static two-column lists previously rendered by <TwoTracksRoadmap/>.
 *
 * Visual model
 * ============
 *
 *   Track A (PRODUCTS)        Track B (SECRET PROJECT)
 *
 *   [📖]  ──╮                                 [Σ1] Fondations
 *           │                                   │
 *   [🎲]  ──┼──→  [Σ2] Acquisition  ──→  [Σ3] Silent build
 *           │    (Hub central / Fees)           │
 *   [🪄]  ──┤                                 [Σ4] Community returns
 *           │                                   │
 *   [📱]  ──╯                                 [Σ5] Curtain rises
 *
 * Every Track A "product" funnels into the **Acquisition / Fees** hub
 * (Σ2). The hub redistributes downstream to Σ1, Σ3, Σ4 and Σ5. This
 * structure matches the narrative tokenomics: product margins +
 * creator fees → fees wallet → other wallets.
 *
 * Animation strategy
 * ==================
 * - **Nodes** float independently via CSS keyframes with per-node
 *   delay/duration (kept short, only ``transform`` is animated to
 *   respect the design rule "animate only transform/opacity").
 * - **Connections** use `stroke-dasharray` + animated
 *   `stroke-dashoffset` for an infinite "data flowing" effect, with a
 *   different period per line so the network feels alive rather than
 *   robotic.
 * - **Hover / focus** scales the node up + lifts the connecting lines.
 *   On touch devices, tap → opens a Shadcn Dialog with the full
 *   description (icon, code, optional wallet, note).
 *
 * Layout
 * ======
 * The graph is a single, percentage-positioned <div> + <svg> layered
 * canvas. It uses an aspect-ratio container so it scales gracefully
 * from mobile to desktop. The viewBox of the underlying <svg> stays
 * fixed (1000×600) so the curves are crisp; the nodes are positioned
 * with CSS percentages on a sibling absolute layer for clean DOM /
 * a11y semantics (each node is a real <button>).
 *
 * Accessibility
 * =============
 * - Each node is a real <button> with aria-label.
 * - Connections are decorative (`aria-hidden`).
 * - Tab order follows visual order (Track A top→bottom, then Track B).
 * - Reduced motion: respects ``prefers-reduced-motion`` and stops the
 *   floating + flow animations (the static layout still reads).
 */
import React, { useMemo, useState } from "react";
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
  /** Stable id (used for connection wiring and react key). */
  id: string;
  /** "A" → Track A (products, amber). "B" → Track B (secret project, cyan). */
  track: Track;
  /** Lucide icon component. */
  Icon: LucideIcon;
  /** Horizontal position in % of container width (0–100). */
  cx: number;
  /** Vertical position in % of container height (0–100). */
  cy: number;
  /** Floating animation duration (s). Mixed per node for organic motion. */
  floatDuration: number;
  /** Floating animation phase offset (s). */
  floatDelay: number;
  /** Index into the corresponding i18n step array for label / note / wallet. */
  i18nIndex: number;
  /** True when this node is the central acquisition / fees hub. */
  isHub?: boolean;
}

// Track A — products. 4 nodes in a vertical column on the left.
const TRACK_A_NODES: GraphNode[] = [
  { id: "roman",     track: "A", Icon: BookOpen,   cx: 14, cy: 18, floatDuration: 5.0, floatDelay: 0.0, i18nIndex: 0 },
  { id: "boardgame", track: "A", Icon: Dices,      cx: 14, cy: 38, floatDuration: 6.4, floatDelay: 0.7, i18nIndex: 1 },
  { id: "videogen",  track: "A", Icon: Wand2,      cx: 14, cy: 58, floatDuration: 5.8, floatDelay: 1.3, i18nIndex: 2 },
  { id: "mobile",    track: "A", Icon: Smartphone, cx: 14, cy: 78, floatDuration: 7.2, floatDelay: 0.4, i18nIndex: 3 },
];

// Track B — secret project. 5 nodes in a vertical column on the right.
// The 2nd node (Acquisition / Fees) acts as the central hub.
const TRACK_B_NODES: GraphNode[] = [
  { id: "fondations",  track: "B", Icon: Coins,        cx: 86, cy: 10, floatDuration: 6.0, floatDelay: 0.2, i18nIndex: 0 },
  { id: "acquisition", track: "B", Icon: Banknote,     cx: 86, cy: 30, floatDuration: 4.8, floatDelay: 0.0, i18nIndex: 1, isHub: true },
  { id: "silent",      track: "B", Icon: Construction, cx: 86, cy: 50, floatDuration: 7.0, floatDelay: 0.9, i18nIndex: 2 },
  { id: "community",   track: "B", Icon: Heart,        cx: 86, cy: 70, floatDuration: 5.6, floatDelay: 1.4, i18nIndex: 3 },
  { id: "curtain",     track: "B", Icon: EyeOff,       cx: 86, cy: 90, floatDuration: 6.6, floatDelay: 0.6, i18nIndex: 4 },
];

// All Track A products feed into the Acquisition hub (Σ2).
// Acquisition fans out to the other Σ nodes.
interface Connection {
  from: string;
  to: string;
  /** Period of the flowing-dot animation, in seconds. */
  flowDuration: number;
  /** Negative direction reverses the dot flow visually. */
  reverse?: boolean;
}

const CONNECTIONS: Connection[] = [
  // Track A → Acquisition hub (4 lines converging)
  { from: "roman",     to: "acquisition", flowDuration: 3.6 },
  { from: "boardgame", to: "acquisition", flowDuration: 3.0 },
  { from: "videogen",  to: "acquisition", flowDuration: 4.2 },
  { from: "mobile",    to: "acquisition", flowDuration: 3.4 },

  // Acquisition → other Σ nodes (4 lines fanning out)
  { from: "acquisition", to: "fondations", flowDuration: 4.0 },
  { from: "acquisition", to: "silent",     flowDuration: 3.2 },
  { from: "acquisition", to: "community",  flowDuration: 4.6 },
  { from: "acquisition", to: "curtain",    flowDuration: 3.8 },
];

// ---------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------
/**
 * Build a smooth cubic-bezier path between two %-positioned points in
 * the 1000×600 viewBox space. Curvature is biased outward so the
 * connections don't overlap visually with the node disks.
 */
function buildCurvePath(from: GraphNode, to: GraphNode): string {
  const x1 = (from.cx / 100) * 1000;
  const y1 = (from.cy / 100) * 600;
  const x2 = (to.cx / 100) * 1000;
  const y2 = (to.cy / 100) * 600;

  // Control points: horizontal bend with a slight vertical drift so
  // converging lines spread enough to be readable near the hub.
  const dx = x2 - x1;
  const dy = y2 - y1;
  const c1x = x1 + dx * 0.42;
  const c1y = y1 + dy * 0.05;
  const c2x = x2 - dx * 0.42;
  const c2y = y2 - dy * 0.05;
  return `M ${x1} ${y1} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${x2} ${y2}`;
}

// ---------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------
export function TwoTracksGraph(): JSX.Element {
  const { t } = useI18n();
  const trackA = (t("roadmapTracks.trackA.steps") as TranslatedStep[]) || [];
  const trackB = (t("roadmapTracks.trackB.steps") as TranslatedStep[]) || [];

  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);

  // Build a lookup of node-by-id once (memoised) so connection lookups
  // stay cheap on every render.
  const nodeMap = useMemo<Record<string, GraphNode>>(() => {
    const map: Record<string, GraphNode> = {};
    for (const n of TRACK_A_NODES) map[n.id] = n;
    for (const n of TRACK_B_NODES) map[n.id] = n;
    return map;
  }, []);

  // Resolve the active node + its translated step (label / note / wallet).
  const active = useMemo(() => {
    if (!activeNodeId) return null;
    const node = nodeMap[activeNodeId];
    if (!node) return null;
    const arr = node.track === "A" ? trackA : trackB;
    const step = arr[node.i18nIndex];
    if (!step) return null;
    return { node, step };
  }, [activeNodeId, nodeMap, trackA, trackB]);

  return (
    <>
      <div
        className="relative w-full overflow-hidden rounded-2xl border border-border/60 bg-card/30 backdrop-blur-sm two-tracks-graph"
        data-testid="two-tracks-graph"
        style={{ aspectRatio: "16 / 11" }}
      >
        {/* Soft dual-tone wash to ground the canvas */}
        <div
          aria-hidden
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(40% 60% at 18% 50%, rgba(245,158,11,0.10) 0%, rgba(0,0,0,0) 70%), radial-gradient(40% 60% at 82% 50%, rgba(45,212,191,0.10) 0%, rgba(0,0,0,0) 70%)",
          }}
        />

        {/* Faint vertical labels in the gutters */}
        <div
          aria-hidden
          className="absolute left-3 top-1/2 -translate-y-1/2 -rotate-90 origin-center font-mono text-[9px] sm:text-[10px] uppercase tracking-[0.32em] text-amber-400/55 select-none"
        >
          {(t("roadmapTracks.trackA.label") as string) || "TRACK A"}
        </div>
        <div
          aria-hidden
          className="absolute right-3 top-1/2 -translate-y-1/2 rotate-90 origin-center font-mono text-[9px] sm:text-[10px] uppercase tracking-[0.32em] text-cyan-300/55 select-none"
        >
          {(t("roadmapTracks.trackB.label") as string) || "TRACK B"}
        </div>

        {/* Connections layer (decorative). The SVG covers the whole
            canvas; nodes will be drawn on top via the absolute layer. */}
        <svg
          viewBox="0 0 1000 600"
          preserveAspectRatio="none"
          className="absolute inset-0 w-full h-full"
          aria-hidden
        >
          <defs>
            {/* A→B gradient (amber → cyan) for product feeds */}
            <linearGradient id="grad-a-to-b" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="rgba(245, 158, 11, 0.85)" />
              <stop offset="55%" stopColor="rgba(245, 158, 11, 0.55)" />
              <stop offset="100%" stopColor="rgba(45, 212, 191, 0.75)" />
            </linearGradient>
            {/* Cyan-only gradient for hub fan-out */}
            <linearGradient id="grad-hub-out" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="rgba(45, 212, 191, 0.75)" />
              <stop offset="100%" stopColor="rgba(45, 212, 191, 0.40)" />
            </linearGradient>
          </defs>

          {CONNECTIONS.map((c, i) => {
            const from = nodeMap[c.from];
            const to = nodeMap[c.to];
            if (!from || !to) return null;
            const d = buildCurvePath(from, to);
            const isAToB = from.track === "A";
            const stroke = isAToB ? "url(#grad-a-to-b)" : "url(#grad-hub-out)";
            return (
              <g key={`${c.from}-${c.to}-${i}`}>
                {/* Base line — faint, always visible */}
                <path
                  d={d}
                  fill="none"
                  stroke={stroke}
                  strokeWidth={1.4}
                  strokeLinecap="round"
                  opacity={0.55}
                />
                {/* Flowing dashes — animated independently per line */}
                <path
                  d={d}
                  fill="none"
                  stroke={stroke}
                  strokeWidth={2.2}
                  strokeLinecap="round"
                  strokeDasharray="4 14"
                  className={c.reverse ? "ttg-flow ttg-flow-reverse" : "ttg-flow"}
                  style={{ animationDuration: `${c.flowDuration}s` }}
                />
              </g>
            );
          })}
        </svg>

        {/* Nodes layer (interactive) */}
        {[...TRACK_A_NODES, ...TRACK_B_NODES].map((node) => {
          const arr = node.track === "A" ? trackA : trackB;
          const step = arr[node.i18nIndex] || { code: "", label: node.id, note: "" };
          const colorClasses =
            node.track === "A"
              ? "border-amber-500/45 bg-amber-500/12 text-amber-200 ring-amber-500/30 hover:bg-amber-500/20 focus-visible:ring-amber-400/70"
              : "border-cyan-500/45 bg-cyan-500/12 text-cyan-200 ring-cyan-500/30 hover:bg-cyan-500/20 focus-visible:ring-cyan-400/70";
          const labelColor =
            node.track === "A" ? "text-amber-300/85" : "text-cyan-300/85";
          return (
            <button
              key={node.id}
              type="button"
              onClick={() => setActiveNodeId(node.id)}
              aria-label={`${step.code ? step.code + " — " : ""}${step.label}`}
              data-testid={`ttg-node-${node.id}`}
              className="absolute -translate-x-1/2 -translate-y-1/2 ttg-node-wrap"
              style={{
                left: `${node.cx}%`,
                top: `${node.cy}%`,
                // Per-node CSS custom props feed the keyframe — gives each
                // node its own organic float rhythm.
                ["--ttg-float-duration" as string]: `${node.floatDuration}s`,
                ["--ttg-float-delay" as string]: `${node.floatDelay}s`,
              }}
            >
              <span
                className={`ttg-node-float relative grid place-items-center rounded-full border ${colorClasses} ring-4 transition-all duration-200 group-hover:scale-110 focus-visible:ring-offset-0 ${
                  node.isHub
                    ? "h-16 w-16 sm:h-20 sm:w-20"
                    : "h-12 w-12 sm:h-14 sm:w-14"
                }`}
              >
                {node.isHub && (
                  <span
                    aria-hidden
                    className="absolute inset-0 rounded-full border border-cyan-400/40 ttg-pulse"
                  />
                )}
                <node.Icon
                  className={`${node.isHub ? "h-7 w-7 sm:h-8 sm:w-8" : "h-5 w-5 sm:h-6 sm:w-6"}`}
                  aria-hidden
                />
              </span>
              <span
                className={`block mt-1.5 font-mono text-[9px] sm:text-[10px] uppercase tracking-[0.18em] text-center ${labelColor} max-w-[88px] sm:max-w-[110px] truncate`}
              >
                {step.code ? `${step.code} · ` : ""}
                {step.label}
              </span>
            </button>
          );
        })}

        {/* Helper hint at the bottom (mobile-first, fades on desktop) */}
        <div
          className="absolute bottom-2 left-1/2 -translate-x-1/2 font-mono text-[9px] sm:text-[10px] uppercase tracking-[0.24em] text-foreground/45 pointer-events-none select-none"
          data-testid="ttg-helper-hint"
        >
          <Sparkles className="inline h-3 w-3 mr-1 -translate-y-px" aria-hidden />
          {t("roadmapTracks.modal.helperHint")}
        </div>
      </div>

      {/* Detail modal */}
      <Dialog
        open={!!active}
        onOpenChange={(open: boolean) => {
          if (!open) setActiveNodeId(null);
        }}
      >
        <DialogContent
          className="sm:max-w-md"
          data-testid="ttg-modal"
        >
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
