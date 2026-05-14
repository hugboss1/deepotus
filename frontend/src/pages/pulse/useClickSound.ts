/**
 * Synthesizes a mechanical-keyboard "thock" via the Web Audio API.
 *
 * Why synthesize instead of shipping a .mp3?
 *  - Zero asset weight (the file would be ~3–5 KB at best, but adds
 *    a network request on first tap that shows up as audio latency).
 *  - Per-key pitch variation comes for free (each call randomises
 *    the carrier within ±300Hz), which makes a rapid-tap sequence
 *    feel like a real mechanical board instead of a single sample
 *    being machine-gunned.
 *  - Browsers gate AudioContext behind a user gesture; lazily
 *    creating it inside the first tap handler satisfies that
 *    requirement without any boot-time prompt.
 *
 * The "click" stacks two voices:
 *  1. **Noise burst** (high-passed) — provides the percussive
 *     transient that gives the sound its "click" character.
 *  2. **Triangle oscillator** at ~2.4–3 kHz with a fast downward
 *     pitch sweep — gives the tonal "thock" body of a Cherry-style
 *     switch.
 *
 * Both voices share a sharp exponential envelope (~3 ms attack,
 * ~40 ms decay). Total sound length is under 50 ms, well below the
 * perceptible audio-visual lag threshold (~100 ms) so the click
 * always feels glued to the tap.
 */
import { useCallback, useEffect, useRef } from "react";

type AudioCtxCtor = typeof AudioContext;

interface UseClickSoundReturn {
  playClick: () => void;
  /** True when the audio context exists AND is in `running` state. */
  ready: boolean;
}

export function useClickSound(): UseClickSoundReturn {
  const ctxRef = useRef<AudioContext | null>(null);
  const readyRef = useRef<boolean>(false);

  // Re-usable shaped noise buffer — generated once per AudioContext.
  // Doing this on every click would allocate ~2 KB of Float32 data
  // each time and trigger GC pressure on rapid taps.
  const noiseBufferRef = useRef<AudioBuffer | null>(null);

  const ensureContext = useCallback((): AudioContext | null => {
    if (typeof window === "undefined") return null;
    if (ctxRef.current) return ctxRef.current;
    // Safari < 14 still uses the webkit prefix; use a typed fallback
    // chain instead of `as any` to keep noImplicitAny happy.
    const Ctor: AudioCtxCtor | undefined =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext?: AudioCtxCtor })
        .webkitAudioContext;
    if (!Ctor) return null;
    try {
      const ctx = new Ctor();
      ctxRef.current = ctx;
      readyRef.current = ctx.state === "running";
      // Pre-bake the percussive noise burst — ~50 ms of exponentially
      // decaying white noise. Done once per ctx, re-used per click.
      const len = Math.floor(0.05 * ctx.sampleRate);
      const buf = ctx.createBuffer(1, len, ctx.sampleRate);
      const data = buf.getChannelData(0);
      for (let i = 0; i < len; i++) {
        const t = i / len;
        data[i] = (Math.random() * 2 - 1) * Math.pow(1 - t, 4);
      }
      noiseBufferRef.current = buf;
      return ctx;
    } catch {
      return null;
    }
  }, []);

  const playClick = useCallback((): void => {
    const ctx = ensureContext();
    if (!ctx || !noiseBufferRef.current) return;
    // Some browsers (Chrome, iOS) keep the context "suspended" until
    // a user gesture. The tap handler IS the gesture so this resume
    // succeeds; we still guard against failure (returns a Promise).
    if (ctx.state === "suspended") {
      ctx.resume().catch((): void => undefined);
    }
    const now = ctx.currentTime;

    // ----- Voice A: shaped noise burst (the "click" transient) -----
    const noise = ctx.createBufferSource();
    noise.buffer = noiseBufferRef.current;
    const hpf = ctx.createBiquadFilter();
    hpf.type = "highpass";
    // 2 kHz high-pass strips low-end mud and leaves the crisp
    // top-end snap typical of a tactile mechanical switch.
    hpf.frequency.value = 2000;
    const noiseGain = ctx.createGain();
    noiseGain.gain.setValueAtTime(0.0001, now);
    noiseGain.gain.exponentialRampToValueAtTime(0.28, now + 0.003);
    noiseGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.04);
    noise.connect(hpf).connect(noiseGain).connect(ctx.destination);
    noise.start(now);
    noise.stop(now + 0.05);

    // ----- Voice B: tonal "thock" body -----
    const osc = ctx.createOscillator();
    osc.type = "triangle";
    // Per-tap pitch variance: ±300 Hz around 2.6 kHz. Without this,
    // rapid-fire taps sound like one repeating sample.
    const baseFreq = 2400 + Math.random() * 600;
    osc.frequency.setValueAtTime(baseFreq, now);
    osc.frequency.exponentialRampToValueAtTime(baseFreq * 0.7, now + 0.03);
    const oscGain = ctx.createGain();
    oscGain.gain.setValueAtTime(0.0001, now);
    oscGain.gain.exponentialRampToValueAtTime(0.12, now + 0.002);
    oscGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.035);
    osc.connect(oscGain).connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.04);
  }, [ensureContext]);

  // Clean up on unmount — release the AudioContext so we don't leak
  // them when the user navigates away (especially on iOS where the
  // global hard cap is ~6 concurrent contexts per tab).
  useEffect(() => {
    return () => {
      const ctx = ctxRef.current;
      if (ctx && ctx.state !== "closed") {
        ctx.close().catch((): void => undefined);
      }
      ctxRef.current = null;
      noiseBufferRef.current = null;
    };
  }, []);

  return { playClick, ready: readyRef.current };
}
