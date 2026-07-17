/* ============================================================================
   world-bg — fond animé "plan du monde 3D" du film DEEPOTUS - Fragment
   ----------------------------------------------------------------------------
   Canvas 2D procédural, zéro dépendance, zéro asset réseau :
   - continents en points (grille 120×60 rasterisée depuis world-atlas 110m,
     embarquée en base64 ci-dessous), projetés sur un plan incliné (pseudo-3D,
     rangées proches plus larges et plus lumineuses) ;
   - la caméra panote lentement d'Est en Ouest, pilotée par le playhead du film ;
   - foules : agents lumineux qui voyagent en arcs entre les hubs du roman
     (Londres, Berlin, NY, Marseille, Tokyo…), or = flux du Système,
     orange = cascade Rippled — la répartition change selon l'acte ;
   - bannières "DEEPOTUS" / "RIPPLED" plantées sur les hubs, flottement sinus.
   API : const world = mountWorldBackground(canvas); world.render(playhead)
   — appeler render à chaque frame (hook onProgress du moteur scroll-stage) ;
   un seul appel = frame statique (fallback prefers-reduced-motion).
   ========================================================================== */

function mountWorldBackground(canvas) {
  const GRID_W = 120, GRID_H = 60;              // cellules de 3°, lat 72N → 60S
  const GRID_B64 = "gADg0Q/4HwAwQOz///////////////8DfhQAAAAA+P////////+ABAAAAAAAwP///z04YID3//////9/4P//Hw44AMD7//////978OP/D1wAAMDD/////38MgID/H3wAAIT7/////wcDAAD/f/wAAAT5/////wEDAAD+//0BAM7//////w8BAAD+//8AAOj//////w8AAAD8/18DAPj//////w8AAAD4/z8AAPj/3v///wsAAAD4/18AAPA+7v///wkAAAD4/w8AAB4dzP///wgAAAD4/wcAAA7q3///bwAAAAD4/wcAAA7pz///TwQAAADw/wcAAPAA////TwYAAADg/wMAAP4A////jwEAAADg/wEAAP7Z////nwAAAACADwEAAP7/7///HwAA";

  // hubs (lon, lat, bannière éventuelle)
  const HUBS = [
    { lon: -0.12, lat: 51.5, banner: "DEEPOTUS" },   // Londres (Helix / Ministère)
    { lon: 13.4,  lat: 52.5, banner: "RIPPLED"  },   // Berlin (cercle thermique)
    { lon: -74.0, lat: 40.7, banner: "DEEPOTUS" },   // New York (Aurora)
    { lon: 5.37,  lat: 43.3, banner: "RIPPLED"  },   // Marseille (Aster-9)
    { lon: 139.7, lat: 35.7, banner: "DEEPOTUS" },   // Tokyo (la Matrice)
    { lon: -46.6, lat: -23.5, banner: "RIPPLED" },   // São Paulo (grids locaux)
    { lon: 54.4,  lat: 24.5, banner: null },         // Golfe (le Capital)
    { lon: 8.2,   lat: 46.6, banner: null },         // Alpes (JANUS)
  ];

  // ---- décodage de la grille → points terre ----
  const bin = atob(GRID_B64);
  const dots = [];
  for (let i = 0; i < GRID_W * GRID_H; i++) {
    if (bin.charCodeAt(i >> 3) & (1 << (i & 7))) {
      const gx = i % GRID_W, gy = (i / GRID_W) | 0;
      dots.push({
        lon: -180 + (gx + 0.5) * (360 / GRID_W),
        lat: 72 - (gy + 0.5) * (132 / GRID_H),
        seed: ((gx * 73856093) ^ (gy * 19349663)) % 1000 / 1000,
      });
    }
  }

  // ---- agents de foule : routes en arc entre hubs ----
  const isMobile = matchMedia('(max-width: 860px)').matches;
  const N_AGENTS = isMobile ? 70 : 170;
  const agents = [];
  for (let k = 0; k < N_AGENTS; k++) {
    const a = HUBS[k % HUBS.length];
    let b = HUBS[(k * 3 + 1 + ((k / HUBS.length) | 0)) % HUBS.length];
    if (b === a) b = HUBS[(k + 1) % HUBS.length];
    agents.push({
      a, b,
      phase: (k * 0.6180339887) % 1,                 // nombre d'or : répartition uniforme
      speed: 0.010 + ((k * 7919) % 100) / 100 * 0.022,
      rippled: k % 5 < 2,                            // 40% orange de base (module par acte)
      bulge: 4 + ((k * 104729) % 100) / 100 * 10,
    });
  }

  const ctx = canvas.getContext('2d');
  const DPR = Math.min(1.5, window.devicePixelRatio || 1);
  let W = 0, H = 0;
  function resize() {
    W = canvas.clientWidth; H = canvas.clientHeight;
    canvas.width = Math.round(W * DPR); canvas.height = Math.round(H * DPR);
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }
  window.addEventListener('resize', resize);
  resize();

  const wrap = d => ((d + 540) % 360) - 180;
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));

  // projection plan incliné : t=0 nord/lointain (comprimé), t=1 sud/proche (large)
  function project(lon, lat, camLon) {
    const t = clamp((72 - lat) / 132, 0, 1);
    const row = Math.pow(t, 1.32);
    const y = H * (0.16 + 0.66 * row);
    const scale = 0.5 + 1.15 * row;
    const x = W / 2 + wrap(lon - camLon) * (W / 360) * 1.35 * scale;
    return { x, y, t, scale };
  }

  // fenêtres d'actes (alignées sur les tweens du film)
  function actWeights(p) {
    const win = (a, b, f = 0.04) => clamp(Math.min((p - a) / f, (b - p) / f, 1), 0, 1);
    return {
      systeme: win(0.27, 0.45),
      rippled: win(0.45, 0.62),
      finale:  win(0.88, 1.01),
    };
  }

  function render(p) {
    const time = performance.now() / 1000;
    const w8 = actWeights(p);
    const camLon = 25 - 145 * clamp(p * 1.12, 0, 1);   // Europe → Amériques au fil du film
    ctx.clearRect(0, 0, W, H);

    // -- continents en points --
    for (let i = 0; i < dots.length; i++) {
      const d = dots[i];
      if (isMobile && (i & 1)) continue;
      const pr = project(d.lon, d.lat, camLon);
      if (pr.x < -14 || pr.x > W + 14) continue;
      const shimmer = 0.12 * Math.sin(time * 0.9 + d.seed * 6.28);
      const alpha = (0.15 + 0.30 * pr.t + shimmer) * (1 - 0.35 * w8.finale);
      if (alpha <= 0.015) continue;
      // teinte : or par défaut, cuivre pendant l'acte Rippled
      const g = Math.round(162 - 40 * w8.rippled);
      ctx.fillStyle = `rgba(201,${g},75,${alpha.toFixed(3)})`;
      const r = 0.7 + 1.5 * pr.t;
      ctx.fillRect(pr.x - r / 2, pr.y - r / 2, r, r);
    }

    // -- hubs : halo pulsant --
    for (const h of HUBS) {
      const pr = project(h.lon, h.lat, camLon);
      if (pr.x < -20 || pr.x > W + 20) continue;
      const pulse = 0.5 + 0.5 * Math.sin(time * 1.6 + h.lon);
      const rip = h.banner === "RIPPLED";
      const boost = rip ? (0.5 + 0.9 * w8.rippled) : (0.6 + 0.7 * w8.systeme + 0.5 * w8.finale);
      ctx.beginPath();
      ctx.arc(pr.x, pr.y, (2.2 + 1.6 * pulse) * pr.scale * 0.8, 0, 6.2832);
      ctx.fillStyle = rip
        ? `rgba(216,122,59,${(0.28 * boost).toFixed(3)})`
        : `rgba(224,197,106,${(0.26 * boost).toFixed(3)})`;
      ctx.fill();
    }

    // -- foules : agents en transit sur les arcs --
    for (const ag of agents) {
      const u = (ag.phase + time * ag.speed) % 1;
      // acte Rippled : la part orange grossit et accélère ; acte Système : flux or réguliers
      const rippledNow = ag.rippled || (w8.rippled > 0.5 && (ag.bulge % 2 > 0.9));
      const lon = ag.a.lon + wrap(ag.b.lon - ag.a.lon) * u;
      const lat = ag.a.lat + (ag.b.lat - ag.a.lat) * u
        + Math.sin(u * Math.PI) * ag.bulge * (1 - 0.6 * w8.systeme); // arcs aplatis chez le Système
      const pr = project(lon, lat, camLon);
      if (pr.x < -10 || pr.x > W + 10) continue;
      const head = rippledNow
        ? `rgba(232,150,88,${(0.35 + 0.5 * w8.rippled).toFixed(3)})`
        : `rgba(230,205,130,${(0.30 + 0.4 * w8.systeme + 0.2 * w8.finale).toFixed(3)})`;
      ctx.fillStyle = head;
      const r = (1.1 + 1.3 * pr.t);
      ctx.beginPath(); ctx.arc(pr.x, pr.y, r, 0, 6.2832); ctx.fill();
      // trainée : deux échos en amont
      for (let e = 1; e <= 2; e++) {
        const ue = (u - e * 0.012 + 1) % 1;
        const lone = ag.a.lon + wrap(ag.b.lon - ag.a.lon) * ue;
        const late = ag.a.lat + (ag.b.lat - ag.a.lat) * ue + Math.sin(ue * Math.PI) * ag.bulge;
        const pe = project(lone, late, camLon);
        ctx.globalAlpha = 0.35 / e;
        ctx.beginPath(); ctx.arc(pe.x, pe.y, r * 0.7, 0, 6.2832); ctx.fill();
        ctx.globalAlpha = 1;
      }
    }

    // -- bannières plantées sur les hubs --
    ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
    for (const h of HUBS) {
      if (!h.banner) continue;
      const pr = project(h.lon, h.lat, camLon);
      if (pr.x < 30 || pr.x > W - 30) continue;
      const rip = h.banner === "RIPPLED";
      const vis = rip ? (0.35 + 0.65 * w8.rippled) : (0.45 + 0.4 * w8.systeme + 0.5 * w8.finale);
      const alpha = clamp(vis, 0, 1) * (0.45 + 0.4 * pr.t);
      if (alpha < 0.05) continue;
      const poleH = 16 + 12 * pr.t;
      const sway = Math.sin(time * 2.1 + h.lat) * 0.06;
      ctx.strokeStyle = `rgba(201,162,75,${(alpha * 0.8).toFixed(3)})`;
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(pr.x, pr.y); ctx.lineTo(pr.x, pr.y - poleH); ctx.stroke();
      ctx.save();
      ctx.translate(pr.x, pr.y - poleH);
      ctx.rotate(sway);
      const fs = Math.round(8 + 4 * pr.t);
      ctx.font = `600 ${fs}px ui-monospace, Consolas, monospace`;
      const tw = ctx.measureText(h.banner).width;
      ctx.fillStyle = rip ? `rgba(216,122,59,${(alpha * 0.22).toFixed(3)})` : `rgba(201,162,75,${(alpha * 0.20).toFixed(3)})`;
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
