/**
 * TerminalWindow — retro-CRT terminal chrome with a line-by-line
 * typewriter effect. Used by DeepStateIntro to render the four "hack"
 * windows.
 *
 * Behaviour:
 *   - Mounts → starts typing immediately when `startAt` ms has elapsed
 *     (controlled by parent via prop change of `active` flag).
 *   - Each line types out at ~30-50ms/char (line.fast slows it down).
 *   - When all lines are typed, a blinking caret stays on the last line.
 *   - Tones map to colors (muted/ok/info/warn/danger).
 *
 * Performance: pure setTimeout, no animation frame loop. Cleans up on
 * unmount so a Skip click doesn't leak running timers.
 */
import { useEffect, useRef, useState } from "react";

const TONE_COLORS = {
  muted: "#9ca3af",
  ok: "#18C964",
  info: "#06B6D4",
  warn: "#F59E0B",
  danger: "#E11D48",
};

const CHAR_DELAY_MS = 22; // base typing speed
const LINE_GAP_MS = 90;   // pause between lines

export default function TerminalWindow({
  title = "shell",
  lines = [],
  active = false,
  className = "",
  style = {},
  testId = "intro-terminal",
}) {
  const [renderedLines, setRenderedLines] = useState([]);
  const timersRef = useRef([]);

  useEffect(() => {
    if (!active) {
      setRenderedLines([]);
      return undefined;
    }

    // Schedule each character append. Cancellable by clearing timersRef.
    let cumulative = 0;
    lines.forEach((line, lineIdx) => {
      const text = line.text || "";
      const tone = line.tone || "muted";

      for (let charIdx = 0; charIdx <= text.length; charIdx += 1) {
        const at = cumulative + charIdx * CHAR_DELAY_MS;
        const t = setTimeout(() => {
          setRenderedLines((prev) => {
            const next = [...prev];
            next[lineIdx] = { tone, text: text.slice(0, charIdx) };
            return next;
          });
        }, at);
        timersRef.current.push(t);
      }
      cumulative += text.length * CHAR_DELAY_MS + LINE_GAP_MS;
    });

    return () => {
      timersRef.current.forEach(clearTimeout);
      timersRef.current = [];
    };
  }, [active, lines]);

  return (
    <div
      data-testid={testId}
      className={`pointer-events-none select-none rounded-md border border-white/15 bg-[#05060A]/95 backdrop-blur-[2px] shadow-[0_25px_60px_rgba(0,0,0,0.6)] overflow-hidden font-mono text-[11px] sm:text-[12px] leading-[1.55] ${className}`}
      style={style}
    >
      {/* Title bar — three coloured dots + window label */}
      <div className="flex items-center gap-1.5 px-2.5 py-1.5 border-b border-white/10 bg-white/[0.04]">
        <span
          aria-hidden
          className="h-2 w-2 rounded-full bg-[#E11D48]/80"
        />
        <span
          aria-hidden
          className="h-2 w-2 rounded-full bg-[#F59E0B]/80"
        />
        <span
          aria-hidden
          className="h-2 w-2 rounded-full bg-[#18C964]/80"
        />
        <span className="ml-2 text-[10px] uppercase tracking-[0.2em] text-white/55">
          {title}
        </span>
      </div>

      {/* Body */}
      <div className="px-3 py-2 max-h-[200px] sm:max-h-[240px] overflow-hidden">
        {renderedLines.map((l, i) => {
          // Stable key derived from the source line definition (its
          // text + tone) so React doesn't recycle DOM nodes when the
          // typewriter mutates a different row. Falls back to a
          // pseudo-positional id when the source line is missing.
          const src = lines[i];
          const stableKey = src
            ? `${i}-${src.tone || "muted"}-${(src.text || "").length}`
            : `idx-${i}`;
          return (
            <div
              key={stableKey}
              className="whitespace-pre"
              style={{ color: TONE_COLORS[l.tone] || TONE_COLORS.muted }}
            >
              {l.text}
              {i === renderedLines.length - 1 && (
                <span
                  aria-hidden
                  className="inline-block w-[7px] h-[12px] align-[-1px] ml-0.5 motion-safe:animate-pulse"
                  style={{ background: TONE_COLORS[l.tone] || "#9ca3af" }}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
