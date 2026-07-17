/* ============================================================================
   world-bg — fond animé "globe orbital de nuit" du film DEEPOTUS - Fragment
   ----------------------------------------------------------------------------
   Canvas 2D procédural, zéro dépendance, zéro asset réseau. Vue satellite :
   la Terre de nuit vue depuis l'orbite — horizon courbe, halo atmosphérique,
   continents en points sombres et LUMIÈRES NOCTURNES des deux factions
   (or = Système, orange cuivré = Rippled) comme les villes vues d'avion.
   - grille terre 120×60 rasterisée depuis world-atlas 110m (base64 embarquée) ;
   - le globe tourne : panoramique Europe → Amériques piloté par le playhead
     du film + rotation lente continue au temps ;
   - foules : agents lumineux en arcs orbitaux entre les hubs du roman
     (Londres, Berlin, NY, Marseille, Tokyo…), répartition or/orange par acte ;
   - bannières "DEEPOTUS" / "RIPPLED" plantées sur les hubs face caméra.
   API inchangée : mountWorldBackground(canvas) → { render(playhead), resize }
   — render à chaque frame (hook onProgress) ; un appel isolé = frame statique.
   ========================================================================== */

function mountWorldBackground(canvas) {
  const GRID_W = 120, GRID_H = 60;              // cellules de 3°, lat 72N → 60S
  const GRID_B64 = "gADg0Q/4HwAwQOz///////////////8DfhQAAAAA+P////////+ABAAAAAAAwP///z04YID3//////9/4P//Hw44AMD7//////978OP/D1wAAMDD/////38MgID/H3wAAIT7/////wcDAAD/f/wAAAT5/////wEDAAD+//0BAM7//////w8BAAD+//8AAOj//////w8AAAD8/18DAPj//////w8AAAD4/z8AAPj/3v///wsAAAD4/18AAPA+7v///wkAAAD4/w8AAB4dzP///wgAAAD4/wcAAA7q3///bwAAAAD4/wcAAA7pz///TwQAAADw/wcAAPAA////TwYAAADg/wMAAP4A////jwEAAADg/wEAAP7Z////nwAAAACADwEAAP7/7///HwAA";

  const HUBS = [
    { lon: -0.12, lat: 51.5, banner: "DEEPOTUS", rippled: false },  // Londres
    { lon: 13.4,  lat: 52.5, banner: "RIPPLED",  rippled: true  },  // Berlin
    { lon: -74.0, lat: 40.7, banner: "DEEPOTUS", rippled: false },  // New York
    { lon: 5.37,  lat: 43.3, banner: "RIPPLED",  rippled: true  },  // Marseille
    { lon: 139.7, lat: 35.7, banner: "DEEPOTUS", rippled: false },  // Tokyo
    { lon: -46.6, lat: -23.5, banner: "RIPPLED", rippled: true  },  // São Paulo
    { lon: 54.4,  lat: 24.5, banner: null,       rippled: false },  // Golfe
    { lon: 8.2,   lat: 46.6, banner: null,       rippled: false },  // Alpes (JANUS)
  ];

  // ---- décodage grille → points terre + génération des lumières urbaines ----
  const bin = atob(GRID_B64);
  const dots = [], lights = [];
  const dist2 = (a, b, lon, lat) => { const dl = ((a - lon + 540) % 360) - 180; return dl * dl + (b - lat) * (b - lat); };
  for (let i = 0; i < GRID_W * GRID_H; i++) {
    if (!(bin.charCodeAt(i >> 3) & (1 << (i & 7)))) continue;
    const gx = i % GRID_W, gy = (i / GRID_W) | 0;
    const lon = -180 + (gx + 0.5) * (360 / GRID_W);
    const lat = 72 - (gy + 0.5) * (132 / GRID_H);
    const seed = (((gx * 73856093) ^ (gy * 19349663)) % 1000) / 1000;
    dots.push({ lon, lat, seed });
    // lumière nocturne : densité plus forte près des hubs, éparse ailleurs
    let dmin = 1e9, nearRip = false;
    for (const h of HUBS) { const d = dist2(h.lon, h.lat, lon, lat); if (d < dmin) { dmin = d; nearRip = h.rippled; } }
    const near = dmin < 900;                       // ~30° du hub le plus proche
    if (seed > (near ? 0.35 : 0.72)) {
      lights.push({ lon: lon + (seed - 0.5) * 2.4, lat: lat + ((seed * 7) % 1 - 0.5) * 2.4,
                    seed, rippled: near ? nearRip : (seed * 13) % 1 < 0.35,
                    base: near ? 0.55 + 0.45 * seed : 0.25 + 0.3 * seed });
    }
  }

  const isMobile = matchMedia('(max-width: 860px)').matches;
  const N_AGENTS = isMobile ? 60 : 150;
  const agents = [];
  for (let k = 0; k < N_AGENTS; k++) {
    const a = HUBS[k % HUBS.length];
    let b = HUBS[(k * 3 + 1 + ((k / HUBS.length) | 0)) % HUBS.length];
    if (b === a) b = HUBS[(k + 1) % HUBS.length];
    agents.push({
      a, b,
      phase: (k * 0.6180339887) % 1,
      speed: 0.010 + ((k * 7919) % 100) / 100 * 0.020,
      rippled: k % 5 < 2,
      alt: 0.03 + ((k * 104729) % 100) / 100 * 0.05,   // altitude de l'arc orbital
    });
  }

  const ctx = canvas.getContext('2d');
  const DPR = Math.min(1.5, window.devicePixelRatio || 1);
  let W = 0, H = 0, CX = 0, CY = 0, R = 0;
  function resize() {
    W = canvas.clientWidth; H = canvas.clientHeight;
    canvas.width = Math.round(W * DPR); canvas.height = Math.round(H * DPR);
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    // Globe bas-centre : l'apex (horizon courbe) traverse l'écran à ~30% de la
    // hauteur, le limbe et son halo atmosphérique restent visibles.
    R = H * 1.05; CX = W * 0.5; CY = H * 0.30 + R;
  }
  window.addEventListener('resize', resize);
  resize();

  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
  // Inclinaison 26° : sur le méridien face caméra, les latitudes ≥ ~45°N sont
  // dans le cadre (Europe, NY en bas de calotte, bien éclairées), l'Arctique au fond.
  const RAD = Math.PI / 180, TILT = 26 * RAD, cosT = Math.cos(TILT), sinT = Math.sin(TILT);

  // lon/lat (+altitude) → écran ; depth = face caméra (z'>0) sinon caché
  function project(lon, lat, rotLon, alt) {
    const φ = lat * RAD, λ = (lon + rotLon) * RAD, c = Math.cos(φ);
    const x = c * Math.sin(λ), y = Math.sin(φ), z = c * Math.cos(λ);
    const y2 = y * cosT - z * sinT, z2 = y * sinT + z * cosT;
    const r = R * (1 + (alt || 0));
    return { x: CX + x * r, y: CY - y2 * r, depth: z2 };
  }

  function actWeights(p) {
    const win = (a, b, f = 0.04) => clamp(Math.min((p - a) / f, (b - p) / f, 1), 0, 1);
    return { systeme: win(0.27, 0.45), rippled: win(0.45, 0.62), finale: win(0.88, 1.01) };
  }

  function render(p) {
    const time = performance.now() / 1000;
    const w8 = actWeights(p);
    // front lon = -rotLon : Europe (~8°E) au début → Amériques (~-120°O) à la fin
    const rotLon = -8 + 130 * clamp(p * 1.1, 0, 1) + time * 0.15;
    ctx.clearRect(0, 0, W, H);

    // -- disque océan de nuit + halo atmosphérique (l'horizon orbital) --
    const oc = ctx.createRadialGradient(CX, CY, R * 0.55, CX, CY, R);
    oc.addColorStop(0, 'rgba(8,13,24,0.92)');
    oc.addColorStop(0.86, 'rgba(10,17,30,0.95)');
    oc.addColorStop(1, 'rgba(16,26,44,0.98)');
    ctx.beginPath(); ctx.arc(CX, CY, R, 0, 6.2832); ctx.fillStyle = oc; ctx.fill();
    const atm = ctx.createRadialGradient(CX, CY, R * 0.985, CX, CY, R * 1.06);
    atm.addColorStop(0, 'rgba(90,140,190,0)');
    atm.addColorStop(0.45, `rgba(110,160,205,${0.20 - 0.06 * w8.finale})`);
    atm.addColorStop(0.75, 'rgba(201,162,75,0.10)');
    atm.addColorStop(1, 'rgba(201,162,75,0)');
    ctx.beginPath(); ctx.arc(CX, CY, R * 1.06, 0, 6.2832); ctx.fillStyle = atm; ctx.fill();

    // -- continents : masses sombres à peine plus claires que l'océan --
    for (let i = 0; i < dots.length; i++) {
      const d = dots[i];
      if (isMobile && (i & 1)) continue;
      const pr = project(d.lon, d.lat, rotLon, 0);
      if (pr.depth < 0.02 || pr.y < -8 || pr.y > H + 8 || pr.x < -8 || pr.x > W + 8) continue;
      const b = clamp(0.3 + 1.6 * pr.depth, 0, 1);     // limbe relevé : cadrage orbital = tout est proche du bord
      const alpha = (0.05 + 0.10 * b) * (1 - 0.3 * w8.finale);
      ctx.fillStyle = `rgba(120,124,105,${alpha.toFixed(3)})`;
      const r = 1.1 + 1.6 * b;
      ctx.fillRect(pr.x - r / 2, pr.y - r / 2, r, r);
    }

    // -- LUMIÈRES NOCTURNES des deux factions (le cœur de l'effet) --
    for (let i = 0; i < lights.length; i++) {
      const L = lights[i];
      if (isMobile && (i % 3 === 0)) continue;
      const pr = project(L.lon, L.lat, rotLon, 0.002);
      if (pr.depth < 0.02 || pr.y < -6 || pr.y > H + 6 || pr.x < -6 || pr.x > W + 6) continue;
      const b = clamp(0.35 + 1.7 * pr.depth, 0, 1);
      const twinkle = 0.75 + 0.25 * Math.sin(time * (1.1 + L.seed) + L.seed * 40);
      // la cascade Rippled : vague de ré-allumage orange pendant son acte
      const boost = L.rippled ? (0.7 + 0.9 * w8.rippled * (0.6 + 0.4 * Math.sin(time * 2.2 + L.lat * 0.4)))
                              : (0.75 + 0.5 * w8.systeme + 0.35 * w8.finale);
      const alpha = clamp(L.base * b * twinkle * boost, 0, 1) * (1 - 0.25 * w8.finale);
      if (alpha < 0.02) continue;
      ctx.fillStyle = L.rippled
        ? `rgba(236,146,80,${alpha.toFixed(3)})`
        : `rgba(240,214,150,${alpha.toFixed(3)})`;
      const r = (0.6 + 1.0 * b) * (L.base > 0.7 ? 1.5 : 1);
      ctx.fillRect(pr.x - r / 2, pr.y - r / 2, r, r);
    }

    // -- hubs : halo urbain pulsant --
    for (const h of HUBS) {
      const pr = project(h.lon, h.lat, rotLon, 0.004);
      if (pr.depth < 0.04) continue;
      const b = clamp(0.35 + 1.6 * pr.depth, 0, 1);
      const pulse = 0.5 + 0.5 * Math.sin(time * 1.6 + h.lon);
      const boost = h.rippled ? (0.5 + 1.0 * w8.rippled) : (0.6 + 0.7 * w8.systeme + 0.5 * w8.finale);
      const g = ctx.createRadialGradient(pr.x, pr.y, 0, pr.x, pr.y, 9 + 5 * pulse);
      const col = h.rippled ? '216,122,59' : '224,197,106';
      g.addColorStop(0, `rgba(${col},${(0.5 * boost * b).toFixed(3)})`);
      g.addColorStop(1, `rgba(${col},0)`);
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(pr.x, pr.y, 9 + 5 * pulse, 0, 6.2832); ctx.fill();
    }

    // -- foules : agents en transit orbital entre hubs --
    for (const ag of agents) {
      const u = (ag.phase + time * ag.speed) % 1;
      const rippledNow = ag.rippled || (w8.rippled > 0.5 && ag.alt > 0.06);
      const lon = ag.a.lon + (((ag.b.lon - ag.a.lon + 540) % 360) - 180) * u;
      const lat = ag.a.lat + (ag.b.lat - ag.a.lat) * u;
      const alt = Math.sin(u * Math.PI) * ag.alt * (1 - 0.5 * w8.systeme);
      const pr = project(lon, lat, rotLon, alt);
      if (pr.depth < 0.03) continue;
      const b = clamp(0.35 + 1.6 * pr.depth, 0, 1);
      ctx.fillStyle = rippledNow
        ? `rgba(232,150,88,${(b * (0.4 + 0.5 * w8.rippled)).toFixed(3)})`
        : `rgba(230,205,130,${(b * (0.35 + 0.4 * w8.systeme + 0.2 * w8.finale)).toFixed(3)})`;
      const r = 0.9 + 1.1 * b;
      ctx.beginPath(); ctx.arc(pr.x, pr.y, r, 0, 6.2832); ctx.fill();
      for (let e = 1; e <= 2; e++) {                       // traînée orbitale
        const ue = (u - e * 0.014 + 1) % 1;
        const lone = ag.a.lon + (((ag.b.lon - ag.a.lon + 540) % 360) - 180) * ue;
        const late = ag.a.lat + (ag.b.lat - ag.a.lat) * ue;
        const pe = project(lone, late, rotLon, Math.sin(ue * Math.PI) * ag.alt);
        if (pe.depth < 0.03) continue;
        ctx.globalAlpha = 0.3 / e;
        ctx.beginPath(); ctx.arc(pe.x, pe.y, r * 0.7, 0, 6.2832); ctx.fill();
        ctx.globalAlpha = 1;
      }
    }

    // -- bannières plantées sur les hubs face caméra --
    ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
    for (const h of HUBS) {
      if (!h.banner) continue;
      const pr = project(h.lon, h.lat, rotLon, 0.004);
      if (pr.depth < 0.10 || pr.x < 40 || pr.x > W - 40) continue;
      const b = clamp(0.35 + 1.6 * pr.depth, 0, 1);
      const rip = h.rippled;
      const vis = rip ? (0.35 + 0.65 * w8.rippled) : (0.45 + 0.4 * w8.systeme + 0.5 * w8.finale);
      const alpha = clamp(vis, 0, 1) * (0.35 + 0.6 * b);
      if (alpha < 0.05) continue;
      const poleH = 14 + 14 * b;
      const sway = Math.sin(time * 2.1 + h.lat) * 0.06;
      ctx.strokeStyle = `rgba(201,162,75,${(alpha * 0.8).toFixed(3)})`;
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(pr.x, pr.y); ctx.lineTo(pr.x, pr.y - poleH); ctx.stroke();
      ctx.save();
      ctx.translate(pr.x, pr.y - poleH);
      ctx.rotate(sway);
      const fs = Math.round(8 + 4 * b);
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
