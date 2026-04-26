/**
 * MatrixRain — minimal canvas 2D Matrix-style rain, themed for PROTOCOL ΔΣ.
 *
 * Characters are drawn from a tiny custom set heavy on the project's symbols
 * (Δ, Σ, $, 01, katakana hooks). Each "drop" advances by a row per frame
 * and the canvas applies a low-alpha fill every frame so older glyphs fade
 * into a long dark trail.
 *
 * Resilience:
 *   - Resizes on window resize (the orchestrator typically un/remounts it).
 *   - Stops via cancelAnimationFrame on unmount.
 *   - Respects `active=false` (paints a single black fill then idles).
 */
import { useEffect, useRef } from "react";

const CHARS =
  "ΔΣ01$DEEPOTUSｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜｦﾝ"
    .split("");
const FONT_SIZE = 16;
const TRAIL_ALPHA = 0.085; // lower = longer trails

export default function MatrixRain({
  active = true,
  opacity = 0.65,
  color = "#18C964",
  highlight = "#A7F3D0",
}) {
  const canvasRef = useRef(null);
  const rafRef = useRef(0);
  const dropsRef = useRef([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return undefined;
    const ctx = canvas.getContext("2d");

    function resize() {
      const dpr = Math.max(1, Math.min(window.devicePixelRatio || 1, 2));
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      canvas.style.width = `${window.innerWidth}px`;
      canvas.style.height = `${window.innerHeight}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const cols = Math.ceil(window.innerWidth / FONT_SIZE);
      // Initialise drops at random heights so the screen looks "in motion"
      // immediately rather than starting empty at the top.
      dropsRef.current = new Array(cols)
        .fill(0)
        .map(() => Math.random() * (window.innerHeight / FONT_SIZE));
    }

    function tick() {
      // Trail fade — paint a low-alpha black rect over the previous frame.
      ctx.fillStyle = `rgba(0, 0, 0, ${TRAIL_ALPHA})`;
      ctx.fillRect(0, 0, window.innerWidth, window.innerHeight);

      ctx.font = `${FONT_SIZE}px "Source Code Pro", "Roboto Mono", monospace`;
      ctx.textBaseline = "top";

      const drops = dropsRef.current;
      for (let i = 0; i < drops.length; i += 1) {
        const ch = CHARS[(Math.random() * CHARS.length) | 0];
        const x = i * FONT_SIZE;
        const y = drops[i] * FONT_SIZE;
        // Highlight the bleeding edge of each drop with a brighter colour.
        ctx.fillStyle = Math.random() < 0.04 ? highlight : color;
        ctx.fillText(ch, x, y);

        // Reset drops that fell off-screen (with random offset for variety).
        if (y > window.innerHeight && Math.random() > 0.975) {
          drops[i] = 0;
        }
        drops[i] += 1;
      }

      if (active) {
        rafRef.current = requestAnimationFrame(tick);
      }
    }

    resize();
    window.addEventListener("resize", resize);
    if (active) rafRef.current = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", resize);
    };
  }, [active, color, highlight]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      data-testid="intro-matrix-rain"
      className="pointer-events-none absolute inset-0 z-0 transition-opacity duration-700"
      style={{ opacity: active ? opacity : 0 }}
    />
  );
}
