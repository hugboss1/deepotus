/* ============================================================================
   world-bg — fond animé du film DEEPOTUS - Fragment : globe orbital ILLUSTRÉ
   ----------------------------------------------------------------------------
   Le fond est l'œuvre `assets/globe.jpg` (la Terre de nuit vue d'orbite, style
   DEEPOTUS). Le moteur l'anime sans la déformer :
   - Ken Burns piloté par le playhead (zoom lent + panoramique subtil) ;
   - par-dessus, en COORDONNÉES IMAGE (elles suivent donc le Ken Burns) :
     · lumières nocturnes des deux factions — échantillonnées offline sur les
       vrais pixels brillants de l'illustration (assets/globe-lights.txt),
       teintées or (Système) / orange cuivré (Rippled) selon le hub le plus
       proche, scintillement + pulsations par acte ;
     · halos urbains pulsants sur les hubs du roman ;
     · foules : agents lumineux en arcs orbitaux (béziers soulevés à l'opposé
       du centre de la planète) entre les hubs ;
     · bannières "DEEPOTUS" / "RIPPLED" plantées sur les hubs.
   API inchangée : mountWorldBackground(canvas) → { render(playhead), resize }
   — render à chaque frame (hook onProgress) ; un appel isolé = frame statique.
   ========================================================================== */

function mountWorldBackground(canvas) {
  // référentiel image (l'œuvre est servie en 1920×1081)
  const IW = 1920, IH = 1081;
  const PLANET = { x: 1015, y: 1556 };            // centre du limbe (pour "soulever" les arcs)

  // hubs du roman pointés SUR l'illustration (px image)
  const HUBS = [
    { x: 618,  y: 303, banner: "DEEPOTUS", rippled: false },  // Londres (Helix / Ministère)
    { x: 768,  y: 292, banner: "RIPPLED",  rippled: true  },  // Berlin (cercle thermique)
    { x: 700,  y: 389, banner: "RIPPLED",  rippled: true  },  // Marseille (Aster-9)
    { x: 740,  y: 355, banner: null,       rippled: false },  // Alpes (JANUS)
    { x: 1046, y: 562, banner: null,       rippled: false },  // Golfe (le Capital)
    { x: 854,  y: 540, banner: null,       rippled: false },  // Le Caire
    { x: 998,  y: 249, banner: "DEEPOTUS", rippled: false },  // Moscou
    { x: 1238, y: 600, banner: "RIPPLED",  rippled: true  },  // Mumbai (grids locaux)
    { x: 1555, y: 432, banner: "DEEPOTUS", rippled: false },  // Shanghai (la Matrice)
    { x: 576,  y: 670, banner: "RIPPLED",  rippled: true  },  // Lagos (nœud communautaire)
  ];

  const isMobile = matchMedia('(max-width: 860px)').matches;
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
  const smooth = x => { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); };

  // ---- assets asynchrones : l'œuvre + ses lumières échantillonnées ----
  const img = new Image();
  let imgReady = false, lastP = 0.35;
  img.onload = () => { imgReady = true; render(lastP); };
  img.src = 'assets/globe.jpg';

  let LIGHTS = [];
  fetch('assets/globe-lights.txt').then(r => r.text()).then(txt => {
    LIGHTS = txt.split('|').map(s => {
      const [x, y, b] = s.split(',').map(Number);
      let dmin = 1e12, rip = false;
      for (const h of HUBS) { const d = (h.x - x) ** 2 + (h.y - y) ** 2; if (d < dmin) { dmin = d; rip = h.rippled; } }
      return { x, y, base: 0.25 + 0.08 * b, rippled: rip, seed: ((x * 7919) ^ (y * 104729)) % 1000 / 1000 };
    });
    render(lastP);
  }).catch(() => {});

  // foules : arcs orbitaux 2D entre hubs, soulevés à l'opposé du centre planète
  const N_AGENTS = isMobile ? 55 : 140;
  const agents = [];
  for (let k = 0; k < N_AGENTS; k++) {
    const a = HUBS[k % HUBS.length];
    let b = HUBS[(k * 3 + 1 + ((k / HUBS.length) | 0)) % HUBS.length];
    if (b === a) b = HUBS[(k + 1) % HUBS.length];
    const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
    const dx = mx - PLANET.x, dy = my - PLANET.y, dn = Math.hypot(dx, dy) || 1;
    const lift = 45 + ((k * 104729) % 100);
    agents.push({
      a, b, cx: mx + dx / dn * lift, cy: my + dy / dn * lift,
      phase: (k * 0.6180339887) % 1,
      speed: 0.010 + ((k * 7919) % 100) / 100 * 0.020,
      rippled: k % 5 < 2,
    });
  }

  const ctx = canvas.getContext('2d');
  const DPR = Math.min(1.5, window.devicePixelRatio || 1);
  let W = 0, H = 0;
  function resize() {
    W = canvas.clientWidth; H = canvas.clientHeight;
    canvas.width = Math.round(W * DPR); canvas.height = Math.round(H * DPR);
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    render(lastP);
  }
  window.addEventListener('resize', resize);
  resize();

  function actWeights(p) {
    const win = (a, b, f = 0.04) => clamp(Math.min((p - a) / f, (b - p) / f, 1), 0, 1);
    return { systeme: win(0.27, 0.45), rippled: win(0.45, 0.62), finale: win(0.88, 1.01) };
  }

  function render(p) {
    lastP = p;
    const time = performance.now() / 1000;
    const w8 = actWeights(p);
    ctx.clearRect(0, 0, W, H);
    if (!W || !H) return;

    // ---- Ken Burns : cover-fit + zoom lent + panoramique piloté par le film ----
    const kb = smooth(p);
    const s = Math.max(W / IW, H / IH) * (1.045 + 0.075 * kb);
    const tx = (W - IW * s) / 2 + (0.035 - 0.07 * kb) * W;   // glisse doucement vers l'ouest
    const ty = -(IH * s - H) * 0.18;                          // horizon gardé dans le cadre
    const M = (x, y) => ({ x: tx + x * s, y: ty + y * s });

    if (imgReady) {
      ctx.drawImage(img, tx, ty, IW * s, IH * s);
    }

    // ---- lumières de faction sur les vraies villes de l'illustration ----
    for (let i = 0; i < LIGHTS.length; i++) {
      const L = LIGHTS[i];
      if (isMobile && (i & 1)) continue;
      const q = M(L.x, L.y);
      if (q.x < -6 || q.x > W + 6 || q.y < -6 || q.y > H + 6) continue;
      const twinkle = 0.7 + 0.3 * Math.sin(time * (1.0 + L.seed) + L.seed * 40);
      const boost = L.rippled
        ? (0.55 + 1.0 * w8.rippled * (0.6 + 0.4 * Math.sin(time * 2.2 + L.y * 0.02)))
        : (0.6 + 0.55 * w8.systeme + 0.35 * w8.finale);
      const alpha = clamp(L.base * twinkle * boost, 0, 1) * (1 - 0.3 * w8.finale);
      if (alpha < 0.03) continue;
      ctx.fillStyle = L.rippled
        ? `rgba(236,146,80,${alpha.toFixed(3)})`
        : `rgba(240,214,150,${alpha.toFixed(3)})`;
      const r = (L.base > 0.8 ? 2.1 : 1.4);
      ctx.fillRect(q.x - r / 2, q.y - r / 2, r, r);
    }

    // ---- halos urbains pulsants sur les hubs ----
    for (const h of HUBS) {
      const q = M(h.x, h.y);
      if (q.x < -30 || q.x > W + 30 || q.y < -30 || q.y > H + 30) continue;
      const pulse = 0.5 + 0.5 * Math.sin(time * 1.6 + h.x * 0.01);
      const boost = h.rippled ? (0.5 + 1.0 * w8.rippled) : (0.6 + 0.7 * w8.systeme + 0.5 * w8.finale);
      const rad = 10 + 6 * pulse;
      const g = ctx.createRadialGradient(q.x, q.y, 0, q.x, q.y, rad);
      const col = h.rippled ? '216,122,59' : '224,197,106';
      g.addColorStop(0, `rgba(${col},${(0.40 * boost).toFixed(3)})`);
      g.addColorStop(1, `rgba(${col},0)`);
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(q.x, q.y, rad, 0, 6.2832); ctx.fill();
    }

    // ---- foules : agents en transit sur les arcs orbitaux ----
    for (const ag of agents) {
      const u = (ag.phase + time * ag.speed) % 1;
      const rippledNow = ag.rippled || (w8.rippled > 0.5 && ag.cy % 2 > 1);
      const flat = 1 - 0.45 * w8.systeme;             // arcs plus rasants chez le Système
      const mx = (ag.a.x + ag.b.x) / 2, my = (ag.a.y + ag.b.y) / 2;
      const cx2 = mx + (ag.cx - mx) * flat, cy2 = my + (ag.cy - my) * flat;
      const bez = (t) => {
        const o = 1 - t;
        return { x: o * o * ag.a.x + 2 * o * t * cx2 + t * t * ag.b.x,
                 y: o * o * ag.a.y + 2 * o * t * cy2 + t * t * ag.b.y };
      };
      const pt = bez(u), q = M(pt.x, pt.y);
      if (q.x < -8 || q.x > W + 8 || q.y < -8 || q.y > H + 8) continue;
      ctx.fillStyle = rippledNow
        ? `rgba(232,150,88,${(0.40 + 0.45 * w8.rippled).toFixed(3)})`
        : `rgba(230,205,130,${(0.35 + 0.4 * w8.systeme + 0.2 * w8.finale).toFixed(3)})`;
      ctx.beginPath(); ctx.arc(q.x, q.y, 1.7, 0, 6.2832); ctx.fill();
      for (let e = 1; e <= 2; e++) {                 // traînée
        const pe = bez((u - e * 0.016 + 1) % 1), qe = M(pe.x, pe.y);
        ctx.globalAlpha = 0.32 / e;
        ctx.beginPath(); ctx.arc(qe.x, qe.y, 1.2, 0, 6.2832); ctx.fill();
        ctx.globalAlpha = 1;
      }
    }

    // ---- bannières plantées sur les hubs ----
    ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
    for (const h of HUBS) {
      if (!h.banner) continue;
      const q = M(h.x, h.y);
      if (q.x < 50 || q.x > W - 50 || q.y < 40 || q.y > H + 10) continue;
      const rip = h.rippled;
      const vis = rip ? (0.4 + 0.6 * w8.rippled) : (0.5 + 0.35 * w8.systeme + 0.5 * w8.finale);
      const alpha = clamp(vis, 0, 1) * 0.9;
      if (alpha < 0.05) continue;
      const poleH = 24;
      const sway = Math.sin(time * 2.1 + h.y * 0.02) * 0.06;
      ctx.strokeStyle = `rgba(201,162,75,${(alpha * 0.8).toFixed(3)})`;
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(q.x, q.y); ctx.lineTo(q.x, q.y - poleH); ctx.stroke();
      ctx.save();
      ctx.translate(q.x, q.y - poleH);
      ctx.rotate(sway);
      const fs = 11;
      ctx.font = `600 ${fs}px ui-monospace, Consolas, monospace`;
      const tw = ctx.measureText(h.banner).width;
      ctx.fillStyle = rip ? `rgba(216,122,59,${(alpha * 0.25).toFixed(3)})` : `rgba(201,162,75,${(alpha * 0.22).toFixed(3)})`;
      ctx.fillRect(-tw / 2 - 4, -fs - 5, tw + 8, fs + 6);
      ctx.fillStyle = rip ? `rgba(240,196,162,${alpha.toFixed(3)})` : `rgba(230,215,172,${alpha.toFixed(3)})`;
      ctx.fillText(h.banner, 0, -2);
      ctx.restore();
    }
  }

  return { render, resize };
}

if (typeof module !== 'undefined' && module.exports) module.exports = { mountWorldBackground };
if (typeof window !== 'undefined') window.mountWorldBackground = mountWorldBackground;
