/**
 * VideoGenAppMockup — stylized placeholder shown while real screenshots
 * of the DEEPOTUS Video Generator aren't uploaded yet.
 *
 * It looks like a tiny "studio" UI: a fake node graph on the left, a
 * fake preview pane on the right, and a fake timeline at the bottom.
 * Built with pure CSS / Tailwind — no images, no third-party libs —
 * so it always renders even on slow connections.
 *
 * Easily replaced by a real <img/> once the user uploads the actual
 * screenshots; just swap the JSX content (or render the screenshots
 * conditionally based on file existence).
 */
import { Cpu, Eye, Plus, Pause, Sparkles } from "lucide-react";
import { useI18n } from "@/i18n/I18nProvider";

export function VideoGenAppMockup(): JSX.Element {
  const { t } = useI18n();
  return (
    <div
      data-testid="videogen-mockup"
      className="relative rounded-xl overflow-hidden border border-border bg-[#0a0e14] shadow-[0_2px_0_rgba(0,0,0,0.10),_0_24px_56px_rgba(0,0,0,0.40)]"
    >
      {/* Title-bar */}
      <div className="flex items-center justify-between border-b border-border/60 px-4 py-2.5 bg-[#0c1219]">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-red-500/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/70" />
          </div>
          <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-foreground/60 ml-3">
            DEEPOTUS · VIDEO STUDIO · NODES.v2
          </span>
        </div>
        <div className="font-mono text-[10px] text-foreground/40">9:16 · 1080×1920</div>
      </div>

      {/* Body grid */}
      <div className="grid grid-cols-12 gap-0 min-h-[260px]">
        {/* Nodes column */}
        <div className="col-span-7 p-4 border-r border-border/40 relative">
          <div className="font-mono text-[9px] uppercase tracking-[0.22em] text-foreground/40 mb-3 flex items-center gap-1.5">
            <Cpu className="h-3 w-3" aria-hidden /> Nodes
          </div>
          <svg viewBox="0 0 400 220" className="w-full h-auto opacity-95" aria-hidden>
            <defs>
              <linearGradient id="nodeg" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stopColor="#16202c" />
                <stop offset="1" stopColor="#0c141d" />
              </linearGradient>
            </defs>
            {/* connectors */}
            <path d="M65 50 C110 50 120 100 165 100" stroke="#F59E0B66" fill="none" strokeWidth="1.4" />
            <path d="M65 130 C110 130 120 100 165 100" stroke="#F59E0B66" fill="none" strokeWidth="1.4" />
            <path d="M225 100 C275 100 285 60 335 60" stroke="#2DD4BF66" fill="none" strokeWidth="1.4" />
            <path d="M225 100 C275 100 285 150 335 150" stroke="#2DD4BF66" fill="none" strokeWidth="1.4" />
            {/* nodes */}
            {[
              { x: 18, y: 30, label: "PROMPT" },
              { x: 18, y: 110, label: "IMAGE" },
              { x: 165, y: 80, label: "AVATAR" },
              { x: 335, y: 40, label: "VIDEO" },
              { x: 335, y: 130, label: "AUDIO" },
            ].map((n) => (
              <g key={n.label} transform={`translate(${n.x},${n.y})`}>
                <rect width="60" height="40" rx="6" fill="url(#nodeg)" stroke="#1F2937" />
                <text
                  x="30"
                  y="24"
                  textAnchor="middle"
                  fontFamily="IBM Plex Mono, monospace"
                  fontSize="9"
                  fill="#F6F2EA99"
                >
                  {n.label}
                </text>
              </g>
            ))}
          </svg>
          {/* watermark */}
          <div className="absolute bottom-2 right-3 font-mono text-[9px] uppercase tracking-[0.22em] text-amber-400/85">
            {t("ecosystem.cards.videogen.mockupCaption")}
          </div>
        </div>

        {/* Preview column */}
        <div className="col-span-5 p-4">
          <div className="font-mono text-[9px] uppercase tracking-[0.22em] text-foreground/40 mb-3 flex items-center gap-1.5">
            <Eye className="h-3 w-3" aria-hidden /> Preview
          </div>
          <div className="relative aspect-[9/16] rounded-md overflow-hidden border border-border/60 bg-gradient-to-br from-[#1a2330] to-[#0b1119]">
            {/* Faux avatar silhouette */}
            <svg viewBox="0 0 100 178" className="w-full h-full" aria-hidden>
              <defs>
                <radialGradient id="avg" cx="50%" cy="30%" r="40%">
                  <stop offset="0" stopColor="#F59E0B33" />
                  <stop offset="1" stopColor="#00000000" />
                </radialGradient>
              </defs>
              <rect width="100" height="178" fill="url(#avg)" />
              <circle cx="50" cy="62" r="18" fill="#0b1119" stroke="#F59E0B66" strokeWidth="0.6" />
              <path
                d="M22 178 C22 130, 78 130, 78 178 Z"
                fill="#0b1119"
                stroke="#F59E0B66"
                strokeWidth="0.6"
              />
              <text
                x="50"
                y="160"
                textAnchor="middle"
                fontFamily="IBM Plex Mono, monospace"
                fontSize="5"
                fill="#F59E0BAA"
              >
                AVATAR · SCN.04
              </text>
            </svg>
            <div className="absolute bottom-1 right-1 font-mono text-[8px] text-foreground/40">
              00:14 / 00:30
            </div>
          </div>
          <div className="mt-2 flex items-center gap-1.5">
            <button
              type="button"
              className="h-6 w-6 rounded bg-[#1a2330] border border-border/60 grid place-items-center text-foreground/70"
              aria-label="pause"
            >
              <Pause className="h-3 w-3" />
            </button>
            <button
              type="button"
              className="h-6 px-2 rounded bg-[#1a2330] border border-border/60 grid place-items-center text-foreground/70 font-mono text-[10px] gap-1 flex"
              aria-label="new"
            >
              <Plus className="h-3 w-3" /> NEW
            </button>
            <button
              type="button"
              className="h-6 px-2 ml-auto rounded bg-amber-500/15 border border-amber-500/30 grid place-items-center text-amber-300 font-mono text-[10px] flex gap-1"
              aria-label="publish"
            >
              <Sparkles className="h-3 w-3" /> PUBLISH
            </button>
          </div>
        </div>
      </div>

      {/* Faux timeline */}
      <div className="border-t border-border/40 px-4 py-2.5 bg-[#0a0f15]">
        <div className="flex items-center gap-2">
          <div className="font-mono text-[9px] uppercase tracking-[0.22em] text-foreground/40 w-16">
            TIMELINE
          </div>
          <div className="flex-1 h-3 rounded-sm bg-[#101820] overflow-hidden flex">
            <div className="h-full bg-amber-500/40" style={{ width: "22%" }} />
            <div className="h-full bg-cyan-400/30" style={{ width: "38%" }} />
            <div className="h-full bg-emerald-500/30" style={{ width: "24%" }} />
          </div>
          <div className="font-mono text-[9px] text-foreground/50 tabular-nums w-12 text-right">
            00:30
          </div>
        </div>
      </div>
    </div>
  );
}
