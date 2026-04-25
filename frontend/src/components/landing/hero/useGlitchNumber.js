import { useEffect, useState } from "react";

/**
 * Random 2-digit number that shuffles fast — gives a "Matrix terminal
 * about to lock in" vibe without ever revealing a real countdown.
 */
export function useGlitchNumber(refreshMs = 80) {
  const [n, setN] = useState(() => Math.floor(Math.random() * 100));
  useEffect(() => {
    const id = setInterval(
      () => setN(Math.floor(Math.random() * 100)),
      refreshMs,
    );
    return () => clearInterval(id);
  }, [refreshMs]);
  return n;
}

/** Single 2-digit glitch tile (e.g. "76" labelled "DAYS"). */
export function GlitchNum({ label, refreshMs }) {
  const v = useGlitchNumber(refreshMs);
  return (
    <div className="text-center">
      <div className="tabular font-mono font-semibold text-2xl md:text-3xl text-foreground">
        {String(v).padStart(2, "0")}
      </div>
      <div className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground mt-1">
        {label}
      </div>
    </div>
  );
}
