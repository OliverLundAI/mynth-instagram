// Mynth Reels – scenmotor. Varje scen är en deterministisk funktion av tiden t (ms):
// buildScene(typ, params, ctx) -> {duration, cues, render(t)}.
// cues = [[ms, ljud, volym, variant], ...] mixas av tools/reel/sfx.py.
// Stil: platt tecknat i Mynths färger (svart, benvitt, mint), skarpa former, studs i rörelserna.

const W = 1080, H = 1920, MINT = '#0bbfa6', INK = '#141413', PAPER = '#faf9f5';
const NS = 'http://www.w3.org/2000/svg';
const root = document.getElementById('stage');

// ---------- hjälpfunktioner ----------
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const prog = (t, s, d) => clamp((t - s) / d);
const lerp = (a, b, x) => a + (b - a) * x;
const E = {
  out: x => 1 - Math.pow(1 - x, 3),
  out5: x => 1 - Math.pow(1 - x, 5),
  inout: x => (x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
  back: x => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); },
  expo: x => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x)),
  // dämpad fjäder: översväng och sätter sig
  spring: x => (x >= 1 ? 1 : 1 - Math.exp(-6 * x) * Math.cos(11 * x)),
};
function div(cls, parent, html) {
  const e = document.createElement('div');
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  (parent || root).appendChild(e);
  return e;
}
function svg(w, h, inner, parent, cls) {
  const s = document.createElementNS(NS, 'svg');
  s.setAttribute('width', w); s.setAttribute('height', h); s.setAttribute('viewBox', `0 0 ${w} ${h}`);
  if (cls) s.setAttribute('class', cls);
  s.innerHTML = inner;
  (parent || root).appendChild(s);
  return s;
}
function place(e, x, y, w, h) {
  Object.assign(e.style, { position: 'absolute', left: x + 'px', top: y + 'px' });
  if (w !== undefined) e.style.width = w + 'px';
  if (h !== undefined) e.style.height = h + 'px';
}
function set(e, { x = 0, y = 0, s = 1, sx, sy, r = 0, o = 1 } = {}) {
  e.style.transform = `translate(${x}px,${y}px) rotate(${r}deg) scale(${sx ?? s},${sy ?? s})`;
  e.style.opacity = o;
}
// krymper texten tills inget ord sticker ut (stora versaler kan annars gå utanför bilden)
function fit(e, min = 48) {
  let fs = parseFloat(getComputedStyle(e).fontSize);
  while ((e.scrollWidth > e.clientWidth + 1) && fs > min) { fs -= 2; e.style.fontSize = fs + 'px'; }
  return e.scrollWidth <= e.clientWidth + 1;
}
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// Rubrik + seriens etikett, gemensamt för alla scener utom panelen.
function header(ctx, caption, start = 150) {
  const kick = div('kick', root, esc(ctx.kicker || ''));
  place(kick, 96, 236);
  const logo = svg(70, 49, `<polygon fill="${PAPER}" points="0,0 0,243 49.5,243 49.5,71 110.5,243 151.5,243 212.5,71 212.5,243 262,243 262,0 186.5,0 131,168 75.5,0" transform="scale(.2)"/><circle fill="${MINT}" cx="64.8" cy="43.8" r="4.8"/>`);
  place(logo, W - 96 - 70, 226);
  let cap = null;
  if (caption) { cap = div('cap', root, esc(caption)); place(cap, 96, 300, 888); fit(cap, 40); }
  return t => {
    const a = E.out(prog(t, start - 100, 400));
    set(kick, { y: lerp(20, 0, a), o: a });
    set(logo, { o: a });
    if (cap) { const c = E.out5(prog(t, start, 600)); set(cap, { y: lerp(60, 0, c), o: c }); }
  };
}

// Den tecknade AI:n: en benvit klot-figur med ögon som blinkar och tittar.
function orb(parent, size, light = true) {
  const g = div('orb', parent);
  g.style.width = g.style.height = size + 'px';
  g.style.background = light ? PAPER : INK;
  const eyes = div('eyes', g);
  const ew = size * .11, eh = size * .17;
  const mk = dx => { const e = div('eye', eyes); Object.assign(e.style, { width: ew + 'px', height: eh + 'px', left: (size / 2 + dx - ew / 2) + 'px', top: (size * .42 - eh / 2) + 'px', background: light ? INK : PAPER }); return e; };
  const L = mk(-size * .16), R = mk(size * .16);
  return {
    el: g,
    look(dx, dy, blink = 0) {
      const sy = 1 - .9 * blink;
      for (const e of [L, R]) e.style.transform = `translate(${dx * size * .06}px,${dy * size * .06}px) scaleY(${sy})`;
    },
  };
}
// blink-kurva: korta blinkningar vid givna tider
const blinkAt = (t, times) => times.reduce((m, b) => Math.max(m, 1 - Math.abs(t - b) / 90 > 0 ? 1 - Math.abs(t - b) / 90 : 0), 0);

// ---------- scener ----------
const SCENES = {};

// 1. Panelen: Mintsolen glider in uppifrån och landar exakt i omslaget.
SCENES.panel = (p, ctx) => {
  const s = svg(W, H, ctx.panelSvg); place(s, 0, 0);
  const sun = s.querySelector('.sun'), txt = s.querySelector('.ptxt');
  return {
    duration: 2700,
    cues: [[0, 'whoosh', .9], [560, 'boom', 1], [950, 'tick', .5]],
    render(t) {
      const a = E.out5(prog(t, 0, 1100));
      sun.setAttribute('transform', `translate(0 ${lerp(-1500, 0, a)})`);
      txt.style.opacity = E.out(prog(t, 950, 400));
    },
  };
};

// 2. Fråga: en kund skriver en fråga till en AI-assistent, svaret räknar upp några alternativ,
//    förstoringsglaset letar efter "Ert företag".  params: caption, question, outcome ("missing" | "question")
SCENES.ask = (p, ctx) => {
  const hdr = header(ctx, p.caption);
  const phone = div('phone'); place(phone, 190, 520, 700, 1080);
  const scr = div('screen', phone);
  const top = div('apphead', scr, '');
  const av = orb(top, 46, false); top.appendChild(document.createTextNode('AI-assistent'));
  const input = div('input', scr); const itext = div('itext', input); const caret = div('caret', input);
  const send = div('send', input, `<svg width="34" height="34" viewBox="0 0 34 34"><path d="M17 27V8M8 16l9-9 9 9" stroke="${PAPER}" stroke-width="4.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`);
  div('notch', scr);
  const chat = div('chat', scr);
  const bubble = div('bubble', chat, esc(p.question));
  const resp = div('resp', chat);
  const think = div('think', resp); const tav = orb(think, 44, false);
  const dots = [0, 1, 2].map(() => div('tdot', think));
  const card = div('card', resp);
  const rows = [0, 1, 2].map(i => {
    const r = div('arow', card);
    div('aav', r);
    const b = div('abars', r);
    const w1 = [250, 210, 280][i], w2 = [330, 290, 250][i];
    div('ab1', b).style.width = w1 + 'px'; div('ab2', b).style.width = w2 + 'px';
    return r;
  });
  const lens = div('lens', scr);
  svg(150, 150, `<circle cx="58" cy="58" r="42" fill="rgba(11,191,166,.14)" stroke="${MINT}" stroke-width="12"/><path d="M90 90l40 40" stroke="${INK}" stroke-width="16" stroke-linecap="round"/>`, lens);
  const chip = div('chip', lens, p.outcome === 'question' ? 'Nämns ni?' : 'Ert företag');
  const stamp = div('stamp', scr, 'Inte nämnt');
  const offTop = (e) => { let y = 0; while (e && e !== scr) { y += e.offsetTop; e = e.offsetParent; } return y; };
  stamp.style.left = (scr.clientWidth - stamp.offsetWidth) / 2 + 'px';
  stamp.style.top = (offTop(card) + card.offsetHeight / 2 - stamp.offsetHeight / 2) + 'px';

  // layout mäts när typsnitten är laddade
  const q = String(p.question || '');
  const T0 = 850, CH = 34, typeEnd = T0 + q.length * CH, SEND = typeEnd + 300;
  const THINK = SEND + 450, ROWS = THINK + 950, SCAN = ROWS + 3 * 240 + 350, STEP = 420;
  const STAMP = SCAN + 3 * STEP + 250;
  const missing = p.outcome !== 'question';
  const dur = (missing ? STAMP : SCAN + 3 * STEP) + 1500;
  const cues = [[0, 'whoosh', .8]];
  for (let i = 0; i < q.length; i++) if (q[i] !== ' ') cues.push([T0 + i * CH, 'click', .55, i]);
  cues.push([SEND, 'pop', .9, 0], [THINK, 'blip', .4]);
  for (let i = 0; i < 3; i++) cues.push([ROWS + i * 240, 'pop', .7, i + 1]);
  for (let i = 0; i < 3; i++) cues.push([SCAN + 250 + i * STEP, 'scan', .5, i]);
  if (missing) cues.push([STAMP, 'thud', 1]);
  else cues.push([SCAN + 3 * STEP + 100, 'blip', .6]);

  // positioner i skärmen
  const rowY = i => offTop(rows[i]) + rows[i].offsetHeight / 2;
  // kameran zoomar in mot svarskortet när förstoringsglaset letar
  phone.style.transformOrigin = `${16 + scr.clientWidth / 2}px ${16 + offTop(card) + card.offsetHeight / 2}px`;
  const overflow = offTop(card) + card.offsetHeight > input.offsetTop - 20 || input.offsetHeight > 140
    || (document.querySelector('.cap')?.offsetHeight || 0) > 140;
  return {
    duration: dur, cues, overflow,
    render(t) {
      hdr(t);
      const a = E.back(prog(t, 0, 750));
      let shake = 0;
      if (missing && t > STAMP && t < STAMP + 260) shake = Math.sin((t - STAMP) / 18) * 10 * (1 - (t - STAMP) / 260);
      const zoom = E.inout(prog(t, SCAN - 500, 700));
      set(phone, { y: lerp(1400, 0, a) + zoom * 120, x: shake, s: 1 + .32 * zoom });
      av.look(0, 0, blinkAt(t, [1400, 4200]));
      // skrivande
      const n = t < SEND ? clamp(Math.floor((t - T0) / CH) + 1, 0, q.length) : 0;
      itext.textContent = t < T0 ? 'Fråga vad som helst' : q.slice(0, n);
      itext.classList.toggle('ph', t < T0);
      caret.style.opacity = (t > T0 - 300 && t < SEND && (t < typeEnd || Math.floor(t / 380) % 2 === 0)) ? 1 : 0;
      const sp = prog(t, typeEnd, 200);
      set(send, { s: lerp(.6, 1, E.back(sp)), o: sp });
      // fråga skickas
      const b = E.back(prog(t, SEND, 420));
      set(bubble, { s: lerp(.5, 1, b), o: prog(t, SEND, 120), y: lerp(380, 0, E.out5(prog(t, SEND, 420))) });
      // AI tänker (tre mintprickar)
      const th = prog(t, THINK, 200) * (1 - prog(t, ROWS - 150, 150));
      set(think, { o: th, y: lerp(30, 0, E.out(prog(t, THINK, 300))) });
      tav.look(.2, -.1, blinkAt(t, [THINK + 500]));
      dots.forEach((d, i) => set(d, { y: -Math.max(0, Math.sin((t - THINK) / 140 - i * .9)) * 16 }));
      // svar
      const c = E.out5(prog(t, ROWS - 150, 400));
      set(card, { o: c, y: lerp(40, 0, c) });
      rows.forEach((r, i) => { const v = E.back(prog(t, ROWS + i * 240, 380)); set(r, { o: prog(t, ROWS + i * 240, 120), x: lerp(-60, 0, v), s: lerp(.9, 1, v) }); });
      // förstoringsglaset letar
      const enter = E.back(prog(t, SCAN, 420));
      let ly = rowY(0);
      for (let i = 1; i < 3; i++) ly = lerp(ly, rowY(i), E.inout(prog(t, SCAN + 250 + (i - 1) * STEP + 120, STEP - 120)));
      const lx = 330 + Math.sin(t / 260) * 70;
      const leave = missing ? E.out(prog(t, STAMP - 150, 300)) : 0;
      set(lens, { x: lerp(700, lx, enter) + leave * 500, y: ly - 58, o: enter * (1 - leave) , r: Math.sin(t / 300) * 6 });
      if (!missing) { const pulse = prog(t, SCAN + 3 * STEP + 100, 500); chip.style.transform = `scale(${1 + Math.sin(pulse * Math.PI) * .18})`; }
      // stämpel
      if (missing) {
        const st = prog(t, STAMP, 170);
        set(stamp, { s: lerp(2.4, 1, E.out(st)), o: st, r: -9 });
      } else stamp.style.opacity = 0;
    },
  };
};

// 3. Källor: AI:n bygger sin bild av företaget av det som finns på nätet.  params: caption
SCENES.sources = (p, ctx) => {
  const hdr = header(ctx, p.caption);
  const ICONS = {
    webb: `<rect x="8" y="14" width="84" height="64" rx="10" fill="none" stroke="${PAPER}" stroke-width="6"/><path d="M8 32h84" stroke="${PAPER}" stroke-width="6"/><circle cx="20" cy="23" r="3.5" fill="${MINT}"/><circle cx="31" cy="23" r="3.5" fill="${PAPER}"/><rect x="22" y="44" width="34" height="22" rx="4" fill="${MINT}"/><path d="M64 46h16M64 56h16M64 66h10" stroke="${PAPER}" stroke-width="5" stroke-linecap="round"/>`,
    artiklar: `<path d="M22 6h40l20 20v66H22z" fill="none" stroke="${PAPER}" stroke-width="6" stroke-linejoin="round"/><path d="M62 6v20h20" fill="none" stroke="${PAPER}" stroke-width="6" stroke-linejoin="round"/><path d="M34 44h36M34 58h36M34 72h22" stroke="${MINT}" stroke-width="6" stroke-linecap="round"/>`,
    databaser: `<ellipse cx="50" cy="22" rx="34" ry="12" fill="${MINT}"/><path d="M16 22v54c0 7 15 12 34 12s34-5 34-12V22" fill="none" stroke="${PAPER}" stroke-width="6"/><path d="M16 49c0 7 15 12 34 12s34-5 34-12" fill="none" stroke="${PAPER}" stroke-width="6"/>`,
    redaktioner: `<rect x="8" y="16" width="70" height="68" rx="6" fill="none" stroke="${PAPER}" stroke-width="6"/><path d="M78 34h12v42a8 8 0 0 1-8 8" fill="none" stroke="${PAPER}" stroke-width="6"/><rect x="20" y="28" width="46" height="18" fill="${MINT}"/><path d="M20 58h46M20 70h30" stroke="${PAPER}" stroke-width="5" stroke-linecap="round"/>`,
    handel: `<path d="M10 34l10-22h60l10 22" fill="none" stroke="${PAPER}" stroke-width="6" stroke-linejoin="round"/><path d="M10 34q10 12 20 0q10 12 20 0q10 12 20 0q10 12 20 0" fill="${MINT}" stroke="${MINT}" stroke-width="4"/><path d="M18 44v42h64V44" fill="none" stroke="${PAPER}" stroke-width="6"/><rect x="42" y="60" width="18" height="26" fill="${PAPER}"/>`,
  };
  const SRC = [
    ['webb', 'Er webbplats', 230, 660], ['artiklar', 'Artiklar', 540, 600], ['databaser', 'Databaser', 850, 660],
    ['redaktioner', 'Redaktioner', 300, 1480], ['handel', 'Återförsäljare', 780, 1480],
  ];
  const OX = 540, OY = 1070, OR = 120;
  const lines = svg(W, H, '', root, 'lines'); place(lines, 0, 0);
  const cards = SRC.map(([ic, label, x, y]) => {
    const c = div('scard', root, `<svg width="100" height="96" viewBox="0 0 100 96">${ICONS[ic]}</svg><span>${label}</span>`);
    place(c, x - 115, y - 100, 230, 200);
    return c;
  });
  const paths = SRC.map(([, , x, y]) => {
    const dx = OX - x, dy = OY - y, L = Math.hypot(dx, dy);
    const x2 = OX - dx / L * (OR + 14), y2 = OY - dy / L * (OR + 14), x1 = x + dx / L * 110, y1 = y + dy / L * 110;
    const pth = document.createElementNS(NS, 'path');
    pth.setAttribute('d', `M${x1} ${y1}L${x2} ${y2}`); pth.setAttribute('stroke', '#3a3a37'); pth.setAttribute('stroke-width', '4');
    pth.setAttribute('stroke-dasharray', '10 12'); lines.appendChild(pth);
    return { x1, y1, x2, y2, len: Math.hypot(x2 - x1, y2 - y1), el: pth };
  });
  const parts = [];
  paths.forEach((pp, i) => { for (let j = 0; j < 3; j++) { const c = document.createElementNS(NS, 'circle'); c.setAttribute('r', 11); c.setAttribute('fill', MINT); lines.appendChild(c); parts.push({ pp, i, j, c }); } });
  const o = orb(root, OR * 2, true); place(o.el, OX - OR, OY - OR);
  const ans = div('ans', root); place(ans, 170, 1230, 740);
  [520, 600, 430].forEach(w => div('ansbar', ans).style.width = w + 'px');

  const POP = 300, CARDS = 650, LINES = 1700, FLOW = 2200, FLOWD = 2300, OUT = FLOW + FLOWD + 300;
  const arrive = (i, j) => FLOW + i * 220 + j * 520 + 700;
  const cues = [[0, 'whoosh', .6], [POP, 'pop', .9, 0]];
  SRC.forEach((_, i) => cues.push([CARDS + i * 170, 'pop', .6, i + 1]));
  cues.push([LINES, 'swish', .5]);
  SRC.forEach((_, i) => cues.push([arrive(i, 0), 'blip', .45, i]));
  cues.push([OUT, 'whoosh', .5], [OUT + 450, 'pop', .8, 3]);
  [0, 1, 2].forEach(i => cues.push([OUT + 700 + i * 200, 'tick', .45]));
  return {
    duration: OUT + 2200, cues, overflow: (document.querySelector('.cap')?.offsetHeight || 0) > 140,
    render(t) {
      hdr(t);
      const fade = 1 - .9 * E.out(prog(t, OUT, 400));
      // klotet
      let squash = 0;
      SRC.forEach((_, i) => [0, 1, 2].forEach(j => { const d = t - arrive(i, j); if (d > 0 && d < 220) squash = Math.max(squash, Math.sin(d / 220 * Math.PI)); }));
      const pop = E.back(prog(t, POP, 500));
      const lift = E.inout(prog(t, OUT, 600));
      set(o.el, { s: pop, sx: pop * (1 + .08 * squash), sy: pop * (1 - .08 * squash), y: -170 * lift });
      // ögonen följer den källa som just levererar
      let tx = 0, ty = 0;
      SRC.forEach(([, , x, y], i) => { const w = prog(t, arrive(i, 0) - 500, 300) * (1 - prog(t, arrive(i, 0) + 150, 300)); tx += (x - OX) / 400 * w; ty += (y - OY) / 400 * w; });
      if (t > OUT) { tx = 0; ty = .4; }
      o.look(clamp(tx, -1, 1), clamp(ty, -1, 1), blinkAt(t, [1500, OUT + 1300]));
      cards.forEach((c, i) => { const v = E.back(prog(t, CARDS + i * 170, 450)); set(c, { s: v, o: prog(t, CARDS + i * 170, 100) * fade }); });
      paths.forEach((pp, i) => {
        const v = E.out(prog(t, LINES + i * 90, 500));
        pp.el.style.strokeDashoffset = 0;
        pp.el.setAttribute('d', `M${pp.x1} ${pp.y1}L${lerp(pp.x1, pp.x2, v)} ${lerp(pp.y1, pp.y2, v)}`);
        pp.el.style.opacity = fade;
      });
      parts.forEach(({ pp, i, j, c }) => {
        const s = arrive(i, j) - 700, v = prog(t, s, 700);
        const e = E.inout(v);
        c.setAttribute('cx', lerp(pp.x1, pp.x2, e)); c.setAttribute('cy', lerp(pp.y1, pp.y2, e));
        c.setAttribute('opacity', v > 0 && v < 1 ? 1 : 0);
        c.setAttribute('r', 11 * (1 - .5 * e));
      });
      // svaret som AI:n formulerar
      const a = E.back(prog(t, OUT + 450, 500));
      set(ans, { s: lerp(.4, 1, a), o: prog(t, OUT + 450, 150), y: lerp(-80, 0, a) });
      [...ans.children].forEach((b, i) => { b.style.transform = `scaleX(${E.out(prog(t, OUT + 700 + i * 200, 350))})`; });
    },
  };
};

// 4. Checklista: saker att titta efter, bockas av en i taget.  params: caption, items[2-4]
SCENES.checklist = (p, ctx) => {
  const hdr = header(ctx, p.caption);
  const items = (p.items || []).map((txt, i) => {
    const c = div('item', root, `<svg width="64" height="64" viewBox="0 0 64 64"><rect x="4" y="4" width="56" height="56" rx="14" fill="none" stroke="${PAPER}" stroke-width="5"/><path class="ck" d="M17 33l10 10 21-22" fill="none" stroke="${MINT}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" pathLength="1"/></svg><span>${esc(txt)}</span>`);
    place(c, 96, 0, 888);
    return c;
  });
  // stapla under rubriken
  // stapla mitt i bilden, under rubriken
  const total = items.reduce((h, c) => h + c.offsetHeight + 28, -28);
  let y = Math.max(300 + (document.querySelector('.cap')?.offsetHeight || 0) + 90, Math.round(1000 - total / 2));
  items.forEach(c => { c.style.top = y + 'px'; y += c.offsetHeight + 28; });
  const S = 700, D = 750;
  const cues = [];
  items.forEach((_, i) => cues.push([S + i * D, 'swish', .45], [S + i * D + 380, 'tick', .7]));
  return {
    duration: S + items.length * D + 1500, cues, overflow: y > 1600,
    render(t) {
      hdr(t);
      items.forEach((c, i) => {
        const v = E.out5(prog(t, S + i * D, 500));
        set(c, { x: lerp(160, 0, v), o: v });
        const ck = c.querySelector('.ck'); const k = E.back(prog(t, S + i * D + 380, 300));
        ck.style.strokeDasharray = '1 1'; ck.style.strokeDashoffset = 1 - clamp(k, 0, 1);
        const box = c.querySelector('svg'); box.style.transform = `scale(${1 + .15 * Math.sin(prog(t, S + i * D + 380, 260) * Math.PI)})`;
      });
    },
  };
};

// 5. Text: ett kort påstående.  params: title, sub
SCENES.text = (p, ctx) => {
  const hdr = header(ctx, null);
  const h = div('big', root, esc(p.title).replace(/\n/g, '<br>')); place(h, 96, 640, 888); fit(h);
  const s = p.sub ? div('sub2', root, esc(p.sub)) : null; if (s) place(s, 96, 0, 820);
  if (s) s.style.top = (640 + h.offsetHeight + 40) + 'px';
  return {
    duration: 3400, cues: [[150, 'swish', .5]], overflow: (s ? s.offsetTop + s.offsetHeight : 640 + h.offsetHeight) > 1550 || h.scrollWidth > 890,
    render(t) {
      hdr(t);
      const a = E.out5(prog(t, 150, 600)); set(h, { y: lerp(80, 0, a), o: a });
      if (s) { const b = E.out5(prog(t, 450, 600)); set(s, { y: lerp(50, 0, b), o: b }); }
    },
  };
};
SCENES.quote = (p, ctx) => SCENES.text({ title: p.quote, sub: p.by }, ctx);

// 6. Avslutning: Mynths tre prickar studsar in, uppmaningen, och solen återvänder.  params: title, em, url
SCENES.cta = (p, ctx) => {
  const hdr = header(ctx, null);
  const dots = [0, 1, 2].map(i => { const d = div('dot', root); place(d, 540 - 245 + i * 190 - 60, 640, 120, 120); return d; });
  const h = div('big', root, `${esc(p.title)}<br><em>${esc(p.em)}</em>`); place(h, 96, 840, 888); fit(h);
  const u = div('url2', root, esc(p.url || 'mynth.se')); place(u, 96, 0);
  u.style.top = (840 + h.offsetHeight + 36) + 'px';
  const s = svg(W, H, ctx.sunSvg); place(s, 0, 0);
  const sun = s.querySelector('.sun');
  const cues = [[200, 'chime', .6, 0], [420, 'chime', .6, 1], [640, 'chime', .7, 2], [1000, 'swish', .5], [1450, 'tick', .4], [2300, 'boom', .6]];
  return {
    duration: 4300, cues, overflow: h.scrollWidth > 890 || u.offsetTop > 1500,
    render(t) {
      hdr(t);
      dots.forEach((d, i) => { const v = E.spring(prog(t, 200 + i * 220, 700)); set(d, { s: v, y: -40 * Math.sin(prog(t, 200 + i * 220, 350) * Math.PI) }); });
      const a = E.out5(prog(t, 1000, 600)); set(h, { y: lerp(70, 0, a), o: a });
      const b = E.out5(prog(t, 1450, 500)); set(u, { y: lerp(40, 0, b), o: b });
      const c = E.out5(prog(t, 2300, 1200)); sun.setAttribute('transform', `translate(0 ${lerp(-1500, -1000, c)})`);
    },
  };
};

window.buildScene = (type, params, ctx) => {
  const make = SCENES[type];
  if (!make) throw new Error('okänd scen: ' + type);
  const s = make(params, ctx);
  // mjuk övergång: varje scen utom den sista tonar ut och drar sig lite bakåt
  const draw = s.render;
  s.render = t => {
    draw(t);
    const x = ctx.last ? 0 : E.inout(prog(t, s.duration - 260, 260));
    root.style.opacity = 1 - x;
    root.style.transform = `scale(${1 - .04 * x})`;
  };
  if (!ctx.last) s.cues.push([s.duration - 300, 'swish', .35, 1]);
  s.render(0);
  return s;
};
