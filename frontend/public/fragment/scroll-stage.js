/* ============================================================================
   scroll-cinema-landing — Mode B engine ("scroll-stage")
   ----------------------------------------------------------------------------
   Vanilla JS, zéro dépendance. La page ne défile jamais : un track invisible de
   `height` viewport-heights donne la longueur de scroll, la scène reste fixe, et
   la progression (0→1, lissée par lerp/rAF) pilote une timeline de tweens
   déclaratifs sur les éléments que TU as mis dans le stage.

   USAGE
     const cine = mountScrollCinema(document.getElementById('cinema'), {
       height: 12,                 // longueur totale du film, en hauteurs d'écran
       smooth: 0.12,               // lerp du playhead (0.05 lourd … 0.3 sec)
       hint: 'scroll',             // pastille d'invite (auto-fade)
       progressBar: true,
       chapters: [                 // rail de navigation (clic = saute au beat)
         { label: 'Hero', at: 0.0 }, { label: 'Monde', at: 0.18 }, …
       ],
       copy: [                     // blocs texte épinglés par fenêtre de progression
         { el: '#copy-hero',  from: 0.00, to: 0.14, hold: 'start' }, // visible dès l'arrivée
         { el: '#copy-monde', from: 0.16, to: 0.30 },
         { el: '#copy-cta',   from: 0.90, to: 1.00, hold: 'end' },   // reste affiché à la fin
       ],
       tweens: [                   // interpolations transform/opacity UNIQUEMENT
         { el: '#card1', from: 0.02, to: 0.16, ease: 'smooth',
           props: { x: [-60, 0], y: [12, 0], rot: [-14, -4], scale: [0.7, 1], opacity: [0, 1] } },
         // x/y en vw/vh (unités viewport), rot en deg, scale/opacity sans unité.
         // Hors de [from,to] l'élément garde la valeur de la borne la plus proche
         // (clamp), donc chaîner plusieurs tweens sur le même el = keyframes.
       ],
       onProgress(p, v) {}         // hook par frame : p = playhead lissé, v = vitesse
     });
     cine.seek(0.5);               // saute (programmatique) ; cine.progress() → p

   RÈGLES DE PERF (les violer = jank)
     - props limités à x, y, rot, scale, opacity → composités GPU, jamais de layout.
     - Les éléments animés reçoivent will-change:transform,opacity au mount.
     - Le scroll natif reste le driver : ne jamais preventDefault la molette.
     - prefers-reduced-motion : la timeline saute directement aux états finaux et
       les blocs de copy deviennent tous visibles, empilés (page lisible sans anim).

   THÈME (variables CSS sur le container ou :root)
     --sc-bg, --sc-ink, --sc-ink-soft, --sc-accent, --sc-font-display, --sc-font-body
   ========================================================================== */

function mountScrollCinema(container, config) {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const HEIGHT = Math.max(2, config.height || 10);
  const SMOOTH = (config.smooth != null) ? config.smooth : 0.12;
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const smooth = x => { x = clamp(x); return x * x * (3 - 2 * x); };
  const EASES = {
    linear: x => clamp(x),
    smooth,
    in:  x => { x = clamp(x); return x * x; },
    out: x => { x = clamp(x); return 1 - (1 - x) * (1 - x); },
  };

  injectScrollStageCSS();
  container.classList.add('sc-root');

  // ---- DOM : track (donne la longueur de scroll) — la scène est TON markup, déjà
  // dans le container ; on le fixe simplement.
  const track = el('div', 'sc-track');
  track.style.height = (HEIGHT * 100) + 'vh';
  document.body.appendChild(track);
  container.classList.add('sc-stage');

  let progressFill = null;
  if (config.progressBar !== false) {
    const bar = el('div', 'sc-progress'); progressFill = el('span');
    bar.appendChild(progressFill); container.appendChild(bar);
  }
  let hintEl = null;
  if (config.hint) {
    hintEl = el('div', 'sc-hint');
    const t = el('span'); t.textContent = config.hint; hintEl.appendChild(t);
    hintEl.appendChild(el('i')); container.appendChild(hintEl);
  }
  const dots = [];
  if (config.chapters && config.chapters.length) {
    const rail = el('div', 'sc-rail');
    config.chapters.forEach(ch => {
      const d = el('button', 'sc-rail__dot');
      d.innerHTML = `<span class="sc-rail__label">${escSC(ch.label || '')}</span><i></i>`;
      d.addEventListener('click', () => seek(ch.at));
      rail.appendChild(d); dots.push({ d, at: ch.at });
    });
    container.appendChild(rail);
  }

  // ---- résolution des éléments + will-change ----
  const q = sel => (typeof sel === 'string') ? container.querySelector(sel) : sel;
  const TWEENS = (config.tweens || []).map(t => ({ ...t, node: q(t.el), ease: EASES[t.ease] || smooth }))
    .filter(t => t.node);
  const COPY = (config.copy || []).map(c => ({ ...c, node: q(c.el) })).filter(c => c.node);
  TWEENS.forEach(t => { t.node.style.willChange = 'transform,opacity'; });
  COPY.forEach(c => { c.node.classList.add('sc-copy'); });

  // Un élément peut porter plusieurs tweens (keyframes chaînées) : on groupe pour
  // composer UNE transform par frame, le dernier tween actif ou borné gagnant
  // propriété par propriété.
  const byNode = new Map();
  TWEENS.forEach(t => { if (!byNode.has(t.node)) byNode.set(t.node, []); byNode.get(t.node).push(t); });
  byNode.forEach(list => list.sort((a, b) => a.from - b.from));

  // ---- reduced motion : tout à l'état final, copy empilée, pas de timeline ----
  if (reduce) {
    byNode.forEach((list, node) => applyProps(node, finalProps(list)));
    COPY.forEach(c => { c.node.style.opacity = 1; c.node.style.position = 'relative'; c.node.style.pointerEvents = 'auto'; });
    container.classList.add('sc-reduced');
    track.style.height = '0px';
    return { seek() {}, progress: () => 1 };
  }

  // ---- boucle ----
  let target = 0, playhead = 0, lastPlayhead = 0, ticking = false;
  const total = () => Math.max(1, track.offsetHeight - window.innerHeight);

  function read() { target = clamp((window.scrollY || 0) / total()); ticking = false; }

  function frame() {
    playhead += (target - playhead) * SMOOTH;
    if (Math.abs(target - playhead) < 0.0004) playhead = target;
    const v = playhead - lastPlayhead; lastPlayhead = playhead;

    byNode.forEach((list, node) => {
      const p = {};
      list.forEach(t => {
        const lp = t.ease(clamp((playhead - t.from) / (t.to - t.from)));
        // clamp : avant `from` on tient la valeur [0], après `to` la valeur [1] —
        // mais un tween plus tardif sur la même prop prend le relais (ordre from).
        for (const k in t.props) {
          const pair = t.props[k];
          if (playhead >= t.from || !(k in p)) p[k] = pair[0] + (pair[1] - pair[0]) * lp;
        }
      });
      applyProps(node, p);
    });

    COPY.forEach(c => {
      const pr = clamp((playhead - c.from) / (c.to - c.from));
      let op;
      if (c.hold === 'start') op = (playhead > c.to) ? 0 : smooth(1 - Math.max(0, (pr - 0.55) / 0.45));
      else if (c.hold === 'end') op = (playhead < c.from) ? 0 : smooth(pr / 0.4);
      else op = (playhead < c.from || playhead > c.to) ? 0 : smooth(1 - Math.abs(pr - 0.5) / 0.5);
      c.node.style.opacity = op;
      // Ne JAMAIS écrire node.style.transform ici : ça écraserait le transform de
      // mise en page de la page (centrage translate(-50%,…)). On expose la dérive
      // verticale via --sc-dy ; le CSS (moteur ou page) décide comment la composer.
      c.node.style.setProperty('--sc-dy', ((0.5 - pr) * 3).toFixed(2) + 'vh');
      c.node.style.pointerEvents = op > 0.5 ? 'auto' : 'none';
    });

    if (progressFill) progressFill.style.transform = `scaleX(${playhead.toFixed(4)})`;
    if (hintEl) hintEl.style.opacity = clamp(1 - playhead / 0.04);
    let active = 0; dots.forEach((c, i) => { if (playhead >= c.at - 0.01) active = i; });
    dots.forEach((c, i) => c.d.classList.toggle('is-active', i === active));

    if (config.onProgress) config.onProgress(playhead, v);
    requestAnimationFrame(frame);
  }

  function seek(p) {
    window.scrollTo({ top: clamp(p) * total(), behavior: 'smooth' });
  }

  window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(read); } }, { passive: true });
  window.addEventListener('resize', read);
  read(); requestAnimationFrame(frame);
  return { seek, progress: () => playhead };

  // ---- helpers ----
  function applyProps(node, p) {
    const x = p.x || 0, y = p.y || 0, rot = p.rot || 0, sc = (p.scale != null) ? p.scale : 1;
    node.style.transform = `translate3d(${x.toFixed(3)}vw, ${y.toFixed(3)}vh, 0) rotate(${rot.toFixed(3)}deg) scale(${sc.toFixed(4)})`;
    if (p.opacity != null) node.style.opacity = clamp(p.opacity).toFixed(3);
  }
  function finalProps(list) {
    const p = {};
    list.forEach(t => { for (const k in t.props) p[k] = t.props[k][1]; });
    return p;
  }
}

function el(tag, cls) { const n = document.createElement(tag); if (cls) n.className = cls; return n; }
function escSC(s) { return String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }

function injectScrollStageCSS() {
  if (document.getElementById('sc-css')) return;
  const css = `
  .sc-root{--sc-bg:#0d0b14;--sc-ink:#efe9dc;--sc-ink-soft:#9c94a8;--sc-accent:#7A6BB0;
    --sc-font-display:Georgia,'Times New Roman',serif;
    --sc-font-body:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,system-ui,sans-serif;
    color:var(--sc-ink);font-family:var(--sc-font-body);}
  html,body{margin:0;background:var(--sc-bg);}
  .sc-stage{position:fixed;inset:0;overflow:hidden;background:var(--sc-bg);}
  .sc-stage.sc-reduced{position:static;height:auto;overflow:visible;}
  .sc-track{position:relative;width:1px;pointer-events:none;}
  .sc-progress{position:fixed;top:0;left:0;right:0;height:3px;z-index:90;background:color-mix(in srgb,var(--sc-accent) 16%,transparent);}
  .sc-progress span{display:block;height:100%;width:100%;transform-origin:0 50%;transform:scaleX(0);background:var(--sc-accent);}
  .sc-copy{position:absolute;opacity:0;will-change:opacity,transform;pointer-events:none;transform:translateY(var(--sc-dy,0vh));}
  .sc-hint{position:fixed;left:50%;bottom:26px;z-index:80;transform:translateX(-50%);display:flex;flex-direction:column;align-items:center;gap:10px;font-size:.74rem;letter-spacing:.16em;text-transform:uppercase;color:var(--sc-ink-soft);transition:opacity .3s;}
  .sc-hint i{width:22px;height:34px;border-radius:12px;border:2px solid color-mix(in srgb,var(--sc-ink) 30%,transparent);position:relative;}
  .sc-hint i::after{content:"";position:absolute;left:50%;top:7px;width:4px;height:7px;border-radius:2px;background:var(--sc-accent);transform:translateX(-50%);animation:sc-wheel 1.7s ease-in-out infinite;}
  @keyframes sc-wheel{0%{opacity:0;top:6px}40%{opacity:1}100%{opacity:0;top:17px}}
  .sc-rail{position:fixed;right:clamp(12px,2vw,28px);top:50%;z-index:85;transform:translateY(-50%);display:flex;flex-direction:column;gap:20px;padding:16px 8px;}
  .sc-rail::before{content:"";position:absolute;left:50%;top:20px;bottom:20px;width:2px;transform:translateX(-50%);background:var(--sc-accent);opacity:.25;}
  .sc-rail__dot{position:relative;border:0;background:transparent;cursor:pointer;width:16px;height:16px;display:grid;place-items:center;}
  .sc-rail__dot i{width:8px;height:8px;border-radius:50%;background:color-mix(in srgb,var(--sc-accent) 45%,transparent);transition:transform .3s,background .3s,box-shadow .3s;}
  .sc-rail__dot:hover i{transform:scale(1.3);background:var(--sc-accent);}
  .sc-rail__dot.is-active i{background:var(--sc-accent);transform:scale(1.45);box-shadow:0 0 0 5px color-mix(in srgb,var(--sc-accent) 20%,transparent);}
  .sc-rail__label{position:absolute;right:26px;top:50%;transform:translateY(-50%) translateX(6px);white-space:nowrap;font-size:.76rem;font-weight:600;color:var(--sc-ink);background:color-mix(in srgb,var(--sc-bg) 82%,#fff 8%);backdrop-filter:blur(6px);padding:5px 11px;border-radius:999px;opacity:0;pointer-events:none;transition:opacity .25s,transform .25s;border:1px solid color-mix(in srgb,var(--sc-accent) 22%,transparent);}
  .sc-rail__dot:hover .sc-rail__label,.sc-rail__dot.is-active .sc-rail__label{opacity:1;transform:translateY(-50%) translateX(0);}
  @media (max-width:860px){ .sc-rail{gap:14px;right:5px;} .sc-rail__label{display:none;}
    .sc-hint{bottom:calc(18px + env(safe-area-inset-bottom));} }
  @media (hover:none) and (pointer:coarse){ .sc-rail__dot{width:26px;height:26px;} }
  @media (prefers-reduced-motion:reduce){ .sc-hint{display:none;} .sc-progress{display:none;} .sc-rail{display:none;} }
  `;
  const style = document.createElement('style'); style.id = 'sc-css';
  style.textContent = '@layer sc {\n' + css + '\n}';
  document.head.appendChild(style);
}

if (typeof module !== 'undefined' && module.exports) module.exports = { mountScrollCinema };
if (typeof window !== 'undefined') window.mountScrollCinema = mountScrollCinema;
