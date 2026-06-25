/**
 * TwoTracksGraph — "Track Flow v2 Meteor" interactive board.
 *
 * Re-implementation of the design handoff (design_handoff_track_flow_meteor):
 * two columns of trading-card nodes (Track A = products, Track B = secret
 * project) feeding a central Σ2 · ACQUISITION hub. Animated meteor
 * particles travel curved SVG links to represent revenue flowing through
 * the system — amber = money IN to Acquisition, cyan = redistribution OUT.
 * Each card tilts holographically on hover and flips to its detail (back)
 * card in a modal on click.
 *
 * Design space is a fixed 1280×820 stage, scaled to fit the container
 * width (transform set via ResizeObserver) so every coordinate below is
 * authored in spec units. Card faces are final raster artwork shipped in
 * /assets/track-cards (webp, front = board face, back = detail card).
 *
 * Only this canvas is owned here; the section copy (kicker / title / lead
 * / footer) lives in the parent <TwoTracksRoadmap />.
 */
import React, {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import "./TwoTracksGraph.css";

// Design tokens (per handoff)
const ACCENT_A = "#e6b34a"; // amber — inputs / card accent / glow
const ACCENT_B = "#34c6dd"; // cyan  — outputs (chain + branch)
const STAGE_W = 1280;
const STAGE_H = 820;
const CARD_BASE = "/assets/track-cards";
const FLOW_RATE = 1; // cadence multiplier (0.3–2.5)
const HOLO_STRENGTH = 0.3; // hover foil / glare opacity
const MAX_PARTICLES = 90;

interface NodeDef {
  id: string;
  name: string;
  cx: number;
  cy: number;
  w: number;
  h: number;
  front: string;
  back: string;
}

interface LinkDef {
  key: string;
  kind: "in" | "chain" | "branch";
  to: string;
  seq: number;
  color: string;
  d: string;
}

// Nodes — Track A (products, left), Σ2 hub (center), Track B (right).
const NODES: NodeDef[] = [
  { id: "p1", name: "DEEPOTUS · NOVEL", cx: 170, cy: 160, w: 124, h: 174, front: "p1_front", back: "p1_back" },
  { id: "p2", name: "DEEPOTUS · BOARD GAME", cx: 170, cy: 345, w: 124, h: 174, front: "p2_front", back: "p2_back" },
  { id: "p3", name: "DEEPOTUS · VIDEOGEN", cx: 170, cy: 530, w: 124, h: 174, front: "p3_front", back: "p3_back" },
  { id: "p4", name: "INSURRECTION · VIDEO GAME", cx: 170, cy: 715, w: 124, h: 174, front: "p4_front", back: "p4_back" },
  { id: "acq", name: "Σ2 · ACQUISITION", cx: 640, cy: 438, w: 152, h: 214, front: "acq_front", back: "acq_back" },
  { id: "b1", name: "Σ1 · FOUNDATION", cx: 1110, cy: 160, w: 124, h: 174, front: "b1_front", back: "b1_back" },
  { id: "b3", name: "Σ3 · SILENT BURN", cx: 1110, cy: 345, w: 124, h: 174, front: "b3_front", back: "b3_back" },
  { id: "b4", name: "Σ4 · COMMUNITY", cx: 1110, cy: 530, w: 124, h: 174, front: "b4_front", back: "b4_back" },
  { id: "b5", name: "Σ5 · CURTAIN REVEAL", cx: 1110, cy: 715, w: 124, h: 174, front: "b5_front", back: "b5_back" },
];

// Links — amber INPUTS → Acquisition; cyan BRANCH + sequential CHAIN OUT.
const LINKS: LinkDef[] = [
  { key: "in0", kind: "in", to: "acq", seq: 0, color: ACCENT_A, d: "M232 160 C 412 160, 392 438, 564 438" },
  { key: "in1", kind: "in", to: "acq", seq: 1, color: ACCENT_A, d: "M232 345 C 412 345, 392 438, 564 438" },
  { key: "in2", kind: "in", to: "acq", seq: 2, color: ACCENT_A, d: "M232 530 C 412 530, 392 438, 564 438" },
  { key: "in3", kind: "in", to: "acq", seq: 3, color: ACCENT_A, d: "M232 715 C 412 715, 392 438, 564 438" },
  { key: "inF", kind: "in", to: "acq", seq: 4, color: ACCENT_A, d: "M1048 160 C 860 160, 880 415, 716 415" },
  { key: "br", kind: "branch", to: "b4", seq: 0, color: ACCENT_B, d: "M712 478 C 860 478, 900 530, 1048 530" },
  { key: "c0", kind: "chain", to: "b3", seq: 0, color: ACCENT_B, d: "M716 460 C 850 460, 850 345, 1048 345" },
  { key: "c1", kind: "chain", to: "b4", seq: 1, color: ACCENT_B, d: "M1172 345 C 1218 408, 1218 470, 1172 530" },
  { key: "c2", kind: "chain", to: "b5", seq: 2, color: ACCENT_B, d: "M1172 530 C 1218 595, 1218 655, 1172 715" },
];

interface PathInfo {
  el: SVGPathElement;
  len: number;
  kind: string;
  to: string;
  seq: number;
  color: string;
}

interface Particle {
  el: HTMLDivElement;
  path: SVGPathElement;
  len: number;
  d: number;
  sp: number;
  acc: number;
  to: string;
  delay: number;
  chain: number | null;
}

const MONO =
  "'Space Mono', ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace";

export function TwoTracksGraph(): JSX.Element {
  const outerRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const meteorRef = useRef<HTMLDivElement>(null);
  const [selected, setSelected] = useState<NodeDef | null>(null);

  // ---- Scale the 1280×820 stage to the container width (no flash via
  // useLayoutEffect, kept in sync with a ResizeObserver). ----
  useLayoutEffect(() => {
    const outer = outerRef.current;
    const stage = stageRef.current;
    if (!outer || !stage) return undefined;
    const apply = (): void => {
      const w = outer.clientWidth;
      if (w > 0) stage.style.transform = `scale(${w / STAGE_W})`;
    };
    apply();
    const ro = new ResizeObserver(apply);
    ro.observe(outer);
    return () => ro.disconnect();
  }, []);

  // ---- Holographic hover: 3D tilt toward the cursor + foil + glare. ----
  const onCardMove = useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    const c = e.currentTarget;
    const r = c.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width;
    const py = (e.clientY - r.top) / r.height;
    const rx = (py - 0.5) * -16;
    const ry = (px - 0.5) * 16;
    c.style.transform = `translateY(-10px) rotateX(${rx}deg) rotateY(${ry}deg) scale(1.07)`;
    const wrap = c.parentElement;
    if (wrap) wrap.style.zIndex = "60";
    const holo = c.querySelector<HTMLElement>("[data-holo]");
    const glare = c.querySelector<HTMLElement>("[data-glare]");
    if (holo) {
      holo.style.opacity = String(HOLO_STRENGTH);
      holo.style.transform = `translate(${(px - 0.5) * 30}%, ${(py - 0.5) * 30}%) scale(1.6)`;
    }
    if (glare) {
      glare.style.opacity = String(HOLO_STRENGTH);
      glare.style.background = `radial-gradient(circle at ${px * 100}% ${py * 100}%, rgba(255,255,255,.55), rgba(255,255,255,0) 42%)`;
    }
  }, []);

  const onCardLeave = useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    const c = e.currentTarget;
    c.style.transform = "";
    const wrap = c.parentElement;
    if (wrap) wrap.style.zIndex = "5";
    const holo = c.querySelector<HTMLElement>("[data-holo]");
    const glare = c.querySelector<HTMLElement>("[data-glare]");
    if (holo) holo.style.opacity = "0";
    if (glare) glare.style.opacity = "0";
  }, []);

  // ---- Meteor particle engine (one rAF loop). ----
  useEffect(() => {
    const stage = stageRef.current;
    const layer = meteorRef.current;
    if (!stage || !layer) return undefined;
    const reduce =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return undefined; // keep a static board

    const paths: PathInfo[] = Array.from(
      stage.querySelectorAll<SVGPathElement>("path[data-link]")
    ).map((el) => ({
      el,
      len: el.getTotalLength(),
      kind: el.getAttribute("data-kind") || "",
      to: el.getAttribute("data-to") || "",
      seq: Number(el.getAttribute("data-seq") || 0),
      color: el.getAttribute("stroke") || ACCENT_A,
    }));
    const inPaths = paths.filter((p) => p.kind === "in");
    const chainPaths = paths
      .filter((p) => p.kind === "chain")
      .sort((a, b) => a.seq - b.seq);
    const branchPaths = paths.filter((p) => p.kind === "branch");

    let parts: Particle[] = [];
    let aT = 0.4; // input salvo timer
    let cT = 0.6; // chain relay timer
    let brT = 0.9; // branch timer
    let last = performance.now();
    let raf = 0;

    const spawn = (
      p: PathInfo,
      color: string,
      to: string,
      delay: number,
      chain: number | null
    ): void => {
      if (parts.length > MAX_PARTICLES) return;
      const el = document.createElement("div");
      el.style.cssText = `position:absolute;height:3.6px;border-radius:3px;background:linear-gradient(to left, ${color} 0%, ${color} 12%, rgba(0,0,0,0) 100%);filter:drop-shadow(0 0 5px ${color});transform-origin:100% 50%;pointer-events:none;opacity:0;will-change:transform,width`;
      layer.appendChild(el);
      parts.push({
        el,
        path: p.el,
        len: p.len,
        d: 0,
        sp: 120 + Math.random() * 70,
        acc: 110 + Math.random() * 150,
        to,
        delay,
        chain,
      });
    };
    const spawnChain = (idx: number): void => {
      const p = chainPaths[idx];
      if (p) spawn(p, ACCENT_B, p.to, 0, idx);
    };
    const spawnBranch = (): void => {
      const p = branchPaths[0];
      if (p) spawn(p, ACCENT_B, p.to, 0, null);
    };

    // Flash a destination card's glow ring when a meteor arrives.
    const pulse = (id: string): void => {
      const w = stage.querySelector(`[data-node="${id}"]`);
      const g = w?.querySelector<HTMLElement>("[data-glow]");
      if (!g) return;
      g.style.transition = "none";
      g.style.opacity = id === "b5" ? "1" : "0.8"; // finale flashes brighter
      g.getBoundingClientRect(); // force reflow so the fade restarts
      g.style.transition = "opacity .6s ease";
      g.style.opacity = "0";
    };

    const loop = (now: number): void => {
      const dt = Math.min(0.05, (now - last) / 1000);
      last = now;

      // Inputs (P1..P4 + Foundation) → Acquisition: bursty purchase salvos.
      aT -= dt;
      if (aT <= 0) {
        aT = (0.7 + Math.random() * 1.1) / FLOW_RATE;
        const p = inPaths[Math.floor(Math.random() * inPaths.length)];
        if (p) {
          const count = 2 + Math.floor(Math.random() * 3);
          for (let i = 0; i < count; i++) spawn(p, p.color, "acq", i * 0.14, null);
        }
      }
      // Acquisition → Silent Burn → Community → Curtain Reveal: steady relay.
      cT -= dt;
      if (cT <= 0) {
        cT = 0.5 / FLOW_RATE;
        spawnChain(0);
      }
      // Acquisition → Community: direct branch.
      brT -= dt;
      if (brT <= 0) {
        brT = 0.7 / FLOW_RATE;
        spawnBranch();
      }

      // Advance meteors (accelerating droplets with a speed-scaled trail).
      for (let i = parts.length - 1; i >= 0; i--) {
        const pt = parts[i];
        if (pt.delay > 0) {
          pt.delay -= dt;
          continue;
        }
        pt.sp += pt.acc * dt;
        pt.d += pt.sp * dt;
        if (pt.d >= pt.len) {
          pulse(pt.to);
          const ch = pt.chain;
          pt.el.remove();
          parts.splice(i, 1);
          if (ch != null && ch + 1 < chainPaths.length) spawnChain(ch + 1);
          continue;
        }
        const P = pt.path.getPointAtLength(pt.d);
        const Pa = pt.path.getPointAtLength(Math.min(pt.len, pt.d + 2));
        const ang = (Math.atan2(Pa.y - P.y, Pa.x - P.x) * 180) / Math.PI;
        const tail = Math.max(9, Math.min(64, pt.sp * 0.16));
        pt.el.style.width = `${tail}px`;
        pt.el.style.left = `${P.x}px`;
        pt.el.style.top = `${P.y}px`;
        pt.el.style.transform = `translate(-100%,-50%) rotate(${ang}deg)`;
        const prog = pt.d / pt.len;
        pt.el.style.opacity = String(
          prog < 0.12 ? prog / 0.12 : prog > 0.9 ? (1 - prog) * 10 : 1
        );
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(raf);
      parts.forEach((p) => p.el.remove());
      parts = [];
    };
  }, []);

  // ---- Escape closes the detail modal. ----
  useEffect(() => {
    if (!selected) return undefined;
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === "Escape") setSelected(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selected]);

  return (
    <div
      ref={outerRef}
      data-testid="two-tracks-graph"
      style={{ position: "relative", width: "100%", aspectRatio: `${STAGE_W} / ${STAGE_H}` }}
    >
      <div
        ref={stageRef}
        className="ttg-stage"
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: STAGE_W,
          height: STAGE_H,
          transformOrigin: "top left",
          fontFamily: MONO,
        }}
      >
        {/* Header bar */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: 54,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 26px",
            borderBottom: "1px solid rgba(120,160,200,.1)",
            zIndex: 30,
            fontSize: 12,
            letterSpacing: "2.5px",
          }}
        >
          <span style={{ color: ACCENT_A }}>TRACK A · PRODUCTS</span>
          <span style={{ color: "#5d6f82" }}>◇ ACQUISITION / FEES</span>
          <span style={{ color: ACCENT_B }}>TRACK B · SECRET PROJECT</span>
        </div>

        {/* Links */}
        <svg
          style={{
            position: "absolute",
            inset: 0,
            width: STAGE_W,
            height: STAGE_H,
            pointerEvents: "none",
            zIndex: 2,
          }}
          aria-hidden="true"
        >
          {LINKS.map((ln) => (
            <g key={ln.key}>
              <path
                d={ln.d}
                stroke={ln.color}
                style={{ fill: "none", strokeWidth: 1.1, opacity: 0.2, strokeLinecap: "round" }}
              />
              <path
                d={ln.d}
                data-link="1"
                data-kind={ln.kind}
                data-to={ln.to}
                data-seq={ln.seq}
                stroke={ln.color}
                className="ttg-dash"
                style={{
                  fill: "none",
                  strokeWidth: 1.3,
                  opacity: 0.4,
                  strokeLinecap: "round",
                  strokeDasharray: "1 9",
                }}
              />
            </g>
          ))}
        </svg>

        {/* Meteor overlay (particles appended here each frame) */}
        <div
          ref={meteorRef}
          style={{
            position: "absolute",
            inset: 0,
            width: STAGE_W,
            height: STAGE_H,
            pointerEvents: "none",
            zIndex: 3,
          }}
        />

        {/* Cards */}
        {NODES.map((n) => (
          <div
            key={n.id}
            data-node={n.id}
            style={{
              position: "absolute",
              left: n.cx,
              top: n.cy,
              width: n.w,
              height: n.h,
              transform: "translate(-50%,-50%)",
              perspective: "1100px",
              zIndex: 5,
            }}
          >
            <div
              data-glow
              style={{
                position: "absolute",
                inset: 0,
                borderRadius: 4,
                boxShadow: `0 0 0 1.5px ${ACCENT_A}, 0 0 24px 5px ${ACCENT_A}`,
                opacity: 0,
                transition: "opacity .6s ease",
                pointerEvents: "none",
              }}
            />
            <button
              type="button"
              className="ttg-card"
              onMouseMove={onCardMove}
              onMouseLeave={onCardLeave}
              onClick={() => setSelected(n)}
              aria-label={`${n.name} — open detail card`}
              style={{
                position: "relative",
                display: "block",
                width: "100%",
                height: "100%",
                padding: 0,
                border: 0,
                background: "transparent",
                borderRadius: 5,
                overflow: "hidden",
                cursor: "pointer",
                transformStyle: "preserve-3d",
                boxShadow: "0 8px 22px rgba(0,0,0,.6)",
              }}
            >
              <img
                src={`${CARD_BASE}/${n.front}.webp`}
                alt={n.name}
                draggable={false}
                loading="lazy"
                style={{
                  position: "absolute",
                  inset: 0,
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  display: "block",
                  pointerEvents: "none",
                }}
              />
              <div
                data-holo
                style={{
                  position: "absolute",
                  inset: 0,
                  borderRadius: 5,
                  opacity: 0,
                  transition: "opacity .25s",
                  mixBlendMode: "color-dodge",
                  background:
                    "conic-gradient(from 0deg, rgba(255,70,160,.5), rgba(80,200,255,.5), rgba(120,255,180,.5), rgba(255,225,90,.5), rgba(255,70,160,.5))",
                  backgroundSize: "160% 160%",
                  pointerEvents: "none",
                }}
              />
              <div
                data-glare
                style={{
                  position: "absolute",
                  inset: 0,
                  borderRadius: 5,
                  opacity: 0,
                  transition: "opacity .2s",
                  mixBlendMode: "overlay",
                  pointerEvents: "none",
                }}
              />
            </button>
          </div>
        ))}

        {/* Footer hint */}
        <div
          style={{
            position: "absolute",
            bottom: 16,
            left: "50%",
            transform: "translateX(-50%)",
            fontSize: 10,
            color: "#4a5a6e",
            letterSpacing: "1.5px",
            zIndex: 30,
            whiteSpace: "nowrap",
          }}
        >
          ◇ HOVER TO TILT · CLICK TO FLIP THE CARD
        </div>
      </div>

      {/* Detail modal (rendered outside the scaled stage, real size) */}
      {selected && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={`${selected.name} — detail card`}
          onClick={() => setSelected(null)}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 9999,
            background: "rgba(3,6,12,.74)",
            backdropFilter: "blur(4px)",
            WebkitBackdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 24,
          }}
        >
          <div onClick={(e) => e.stopPropagation()} style={{ position: "relative" }}>
            <img
              src={`${CARD_BASE}/${selected.back}.webp`}
              alt={`${selected.name} — detail`}
              style={{
                display: "block",
                height: 680,
                maxHeight: "84vh",
                width: "auto",
                borderRadius: 8,
                boxShadow: "0 30px 90px rgba(0,0,0,.8)",
              }}
            />
            <button
              type="button"
              onClick={() => setSelected(null)}
              aria-label="Close"
              style={{
                position: "absolute",
                top: -13,
                right: -13,
                width: 30,
                height: 30,
                borderRadius: "50%",
                background: "#0c1626",
                border: `1px solid ${ACCENT_A}`,
                color: ACCENT_A,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                fontSize: 13,
                lineHeight: 1,
                fontFamily: MONO,
              }}
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
