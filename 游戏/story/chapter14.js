// 终章：两年后（原片 s14 尾声）
//   雨里的万事屋门口「两年后……」：新八和神乐站在阳台上 → 操控一个披斗篷的旅人走过雨里的歌舞伎町
//      （路人在聊万事屋的老板；踩过水洼：靴子特写、倒影、兜帽下两点红光）
//   → 走到万事屋楼下：新八「！」神乐「!?」→ 摘下兜帽，雨停了，光照下来：「我回来了。」
//   → 神乐从阳台上一记飞踢（冲击帧）→ 银时转着圈栽进木桶堆 → 新八：「你到底跑哪去了！！」→「……哟。」
//   → 神乐：「两年的份，一次讨回来阿鲁！」（打一场，新八中途也加进来）→「……欢迎回来。」
//   → 日常·回归中：白天的歌舞伎町自由闲逛，熟人各说一句；三个老段子要亲眼看一遍：
//      阿妙把草丛里的近藤打成星星 / 冲田在河堤上轰土方（爆炸头）/ 桂「不是假发，是桂！」（伊丽莎白「没错」）
//   → 回万事屋门口：「哟，定春～」→ 被咬头 → 画面定格变灰，巨大的「完」字砸下来，乌鸦飞过……
//   → 按 J 一脚踢飞「完」字：「才不会完呢！」→ 黄昏，大家列队走过（谢幕）→ 事务所：银时在看 Jump，「感谢观看」
'use strict';
(function () {
  const G = window.G;
  const F = () => G.flags;
  const PR = () => G.D.bg.ch14.props;
  const px = (g, x, y, c, w = 1, h = 1) => { g.fillStyle = c; g.fillRect(Math.round(x), Math.round(y), w, h); };
  const X = () => G.atlas('s14_extra');
  function gear(a) { if (a && G.D.chars.s14_extra) a.alt = [X()]; return a; }
  const seg = (t, a, b) => G.clamp((t - a) / (b - a), 0, 1);
  const easeOut = (u) => 1 - Math.pow(1 - G.clamp(u, 0, 1), 3);
  const easeIn = (u) => Math.pow(G.clamp(u, 0, 1), 2);
  const easeIO = (u) => { u = G.clamp(u, 0, 1); return u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2; };
  const back = (u) => G.ease.outBack(G.clamp(u, 0, 1));
  const im = (k) => G.image(PR()[k].image);
  const FLOOR = 160, BAL = 84, FF = 196, FB = 120;     // 街上 / 二楼阳台（街景）；万事屋门口那个镜头的街面 / 阳台
  const INK = 'rgb(24,20,37)';
  const mark = (name) => { G.dbg = { shot: name }; };   // 给自动试玩截图用

  // ================================================================ 画面上层（不跟着镜头推近；同第十三章）
  const OV = [];
  function ovDraw(g) {
    for (let i = 0; i < OV.length; i++) {
      const o = OV[i], u = G.time - o.t0;
      if (o.dur != null && u >= o.dur) { OV.splice(i--, 1); continue; }
      o.fn(g, u);
    }
  }
  function overlay(fn, dur = null, z = 0) {
    const o = { fn, t0: G.time, dur, z };
    OV.push(o);
    OV.sort((a, b) => a.z - b.z);
    if (!G.ui.insert || G.ui.insert.draw !== ovDraw) G.ui.insert = { draw: ovDraw, t: 0 };
    return o;
  }
  function unoverlay(o) { const i = OV.indexOf(o); if (i >= 0) OV.splice(i, 1); }
  function clearOverlays() { OV.length = 0; if (G.ui.insert && G.ui.insert.draw === ovDraw) G.ui.insert = null; }
  // 世界坐标 → 画面坐标（算上镜头推近）：上层的字、气泡要跟着人走
  function scr(wx, wy) {
    const W = G.world, st = W.stage, z = W.zoom;
    let x = wx - Math.round(st.camX), y = wy - st.camY;
    if (z && z.k > 1.001) {
      const w = G.W / z.k, h = G.H / z.k;
      const cx = G.clamp(z.x - Math.round(st.camX), w / 2, G.W - w / 2), cy = G.clamp(z.y - st.camY, h / 2, G.H - h / 2);
      x = (x - (cx - w / 2)) * z.k; y = (y - (cy - h / 2)) * z.k;
    }
    return [x, y];
  }
  function weather(S, fn, depth = 9000) { return S.prop({ type: 'custom', x: 0, y: 0, depth, draw: (g, x, y, t) => fn(g, t) }); }

  // ================================================================ 小特效
  function sparkle(g, x, y, u, size = 6, color = '#fff', life = 0.45) {
    if (u < 0 || u > life) return;
    const s = Math.round(Math.sin((u / life) * Math.PI) * size);
    if (s <= 0) return;
    x = Math.round(x); y = Math.round(y);
    g.fillStyle = color;
    g.fillRect(x - s, y, 2 * s + 1, 1); g.fillRect(x, y - s, 1, 2 * s + 1);
    if (s > 2) g.fillRect(x - 1, y - 1, 3, 3);
  }
  // 拟声字（原片 sfx_text：前 25% 弹出来，后 20% 淡掉）。at = () => [x, y] 画面坐标（可以跟着人走）
  function word(key, at, dur = 0.5, shake = 0) {
    const w = PR()[key];
    return overlay((g, u) => {
      const k = u / dur, img = G.image(w.image);
      if (!G.ready(img)) return;
      const s = k < 0.25 ? back(k / 0.25) : 1, [x, y] = typeof at === 'function' ? at() : at;
      const j = shake ? Math.round(Math.sin(u * 60) * shake) : 0;
      g.globalAlpha = k > 0.8 ? (1 - k) / 0.2 : 1;
      const ww = Math.max(1, Math.round(w.w * s)), hh = Math.max(1, Math.round(w.h * s));
      g.drawImage(img, Math.round(x - ww / 2) + j, Math.round(y - hh / 2), ww, hh);
      g.globalAlpha = 1;
    }, dur, 5);
  }
  function exclaim(key, at, dur = 0.9) {    // 头顶冒出来的「！」「!?」（底边居中，0.15 秒弹出来）
    const w = PR()[key];
    return overlay((g, u) => {
      const img = G.image(w.image), [x, y] = at(), s = back(u / 0.15);
      if (!G.ready(img)) return;
      const ww = Math.max(1, Math.round(w.w * s)), hh = Math.max(1, Math.round(w.h * s));
      g.drawImage(img, Math.round(x - ww / 2), Math.round(y - hh), ww, hh);
    }, dur, 4);
  }
  function tears(g, x, y, t, dir) {     // 哭成两道小喷泉
    for (let i = 0; i < 4; i++) {
      const u = G.mod(t * 3 + i / 4, 1);
      px(g, x + dir * (2 + u * 8), y + u * u * 12, i % 2 ? 'rgb(150,210,255)' : 'rgb(210,236,255)', 2, 1);
    }
  }
  function dizzy(g, x, y, t, r = 7) {   // 头上转圈的星星
    for (let i = 0; i < 3; i++) {
      const a = t * 5 + (i * Math.PI * 2) / 3, sx = x + Math.cos(a) * r, sy = y + Math.sin(a) * r * 0.35;
      g.fillStyle = 'rgb(255,226,90)';
      g.fillRect(Math.round(sx) - 1, Math.round(sy), 3, 1); g.fillRect(Math.round(sx), Math.round(sy) - 1, 1, 3);
    }
  }
  function sweat(g, x, y, t) {          // 冷汗往下滑
    const u = G.mod(t * 1.2, 1);
    px(g, x, y + u * 6, 'rgb(150,210,255)', 2, 3); px(g, x, y + u * 6, '#fff', 1, 1);
  }
  function rays(g, cx, cy, t, n, color, inner, R = 460) {   // 集中线（15 Hz 重新随机）
    const rnd = G.prng(Math.floor(t * 15) * 7 + 3);
    g.fillStyle = color; g.beginPath();
    for (let i = 0; i < n; i++) {
      const a = rnd() * Math.PI * 2, ri = inner + rnd() * 40, w = 0.012 + rnd() * 0.02;
      g.moveTo(cx + Math.cos(a) * ri, cy + Math.sin(a) * ri);
      g.lineTo(cx + Math.cos(a - w) * R, cy + Math.sin(a - w) * R);
      g.lineTo(cx + Math.cos(a + w) * R, cy + Math.sin(a + w) * R);
      g.closePath();
    }
    g.fill();
  }
  function sakura(g, t, n, seed, wind, fall, cols) {
    const rnd = G.prng(seed * 37 + 5);
    for (let i = 0; i < n; i++) {
      const x0 = rnd() * (G.W + 40), y0 = rnd() * G.H, ph = rnd() * 6, sp = 0.7 + rnd() * 0.6;
      const x = G.mod(x0 + t * wind * sp + Math.sin(t * 1.7 + ph) * 6, G.W + 40) - 20, y = G.mod(y0 + t * fall * sp, G.H + 10) - 5;
      px(g, x, y, cols[i % cols.length], Math.floor(t * 6 + ph) % 2 ? 2 : 1, 1);
    }
  }
  // 画面坐标里画一个角色（谢幕、特写这类不放真角色的镜头）
  function drawChar(g, cid, anim, t, x, y, o = {}) {
    const at = X().has(anim) ? X() : G.atlas(cid), a = at.anim(anim);
    let f = o.frame;
    if (f == null && o.p != null) f = Math.floor(o.p * (a.frames - 1));
    if (f == null) f = a.kind === 'loop' ? Math.floor(Math.max(0, t) * a.fps) % a.frames : Math.min(a.frames - 1, Math.floor(Math.max(0, t) * a.fps));
    if (o.shadow !== false) { g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(Math.round(x) - 6 * (o.scale || 1), Math.round(y) - 1, 12 * (o.scale || 1), 2); }
    at.draw(g, anim, f, x, y, { flip: (o.facing || 1) < 0, tint: o.tint, alpha: o.alpha, scale: o.scale });
  }
  const RAIN = { type: 'rain', n: 110, slant: 0.2, len: 7, speed: 420, color: 'rgba(150,166,206,0.85)', alpha: 1, ground: [158, 214], splashes: 16, seed: 5 };
  // 雷：天空的闪光在 kstreet 图层里画；这里补上整屏的白闪和雷声（表是原片的，按地图时间走）
  function storm(S, k = 0.4) {
    const st = G.world.stage;
    let last = -1;
    const pr = S.prop({ type: 'custom', x: 0, y: 0, depth: 99990, draw: (g) => {
      if (st.state.tod !== 'storm') return;
      const [f] = G.stormFlash(st.t);
      if (f > 0) { g.fillStyle = `rgba(220,230,255,${(f * k * (st.state.stormK == null ? 1 : st.state.stormK)).toFixed(3)})`; g.fillRect(0, 0, G.W, G.H); }
    } });
    G.world.ticks.push(() => {
      if (G.world.stage !== st) return true;
      const [f] = G.stormFlash(st.t), w = Math.floor(st.t / 4.2);
      if (st.state.tod === 'storm' && f >= 0.9 && w !== last) { last = w; S.sfx('thunder', 0.7); }
      return false;
    });
    return pr;
  }

  // ================================================================ A：雨里的万事屋门口
  async function rainyFront(S) {
    const p = S.player;
    p.visible = false;
    const kg = gear(S.spawn('kagura', 150, FB, { id: 'kag', name: '神乐', facing: 1 }));
    const sp = gear(S.spawn('shinpachi', 196, FB, { id: 'shin', name: '新八', facing: -1 }));
    S.pose(kg, 'kagura_umbrella_sad'); S.pose(sp, 'shinpachi_idle_sad');
    storm(S);
    S.letterbox(true);
    S.sfx('rain', 0.7);
    S.zoom(1.001, 180, 112, 0); S.zoom(1.14, 180, 112, 3.0);
    await S.fadeIn(0.6);
    // 「两年后……」
    const t0 = G.time;
    const title = overlay((g, u) => {
      const a = seg(u, 0.25, 0.8);
      if (a <= 0) return;
      g.fillStyle = `rgba(8,8,20,${(0.35 * a).toFixed(3)})`; g.fillRect(0, 16, G.W, 44);
      const T = PR().title_0, img = G.image(T.image), dy = Math.round((1 - easeOut(a)) * 6);
      g.globalAlpha = a; g.drawImage(img, Math.round(G.W / 2 - T.w / 2), Math.round(36 - dy - T.h / 2)); g.globalAlpha = 1;
      if (a >= 1) G.f12.draw(g, '—  TWO YEARS LATER  —', G.W / 2, 52, 'rgb(200,210,235)', { align: 'center', outline: INK });
    }, null, 3);
    void t0;
    mark('ch14_two_years');
    await S.wait(0.9);
    await S.narrate('歌舞伎町重建，新八和神乐守着万事屋。', { auto: 2.6, top: false });
    unoverlay(title);
    await S.say('shinpachi', '……今天也没有回来呢。', { actor: sp, expr: 'sad' });
    await S.say('kagura', '……那个笨蛋。明明说好要回来的阿鲁。', { actor: kg, expr: 'sad' });
    await S.wait(0.5);
    await S.fadeOut(0.8);
    S.zoom(1, null, null, 0);
    S.letterbox(false);
  }

  // ================================================================ B：雨里的歌舞伎町（操控斗篷旅人）
  const PUD = { x: 226, y: 163, rx: 24, ry: 5 };     // 水洼（世界坐标）
  const PILE_X = 268;                                 // 木桶堆（书店门口）
  function puddle(S) {
    const st = G.world.stage, P = PUD;
    let inside = false;
    return S.prop({ type: 'custom', x: 0, y: 0, depth: 100, draw: (g, x, y, t) => {
      const sx = P.x - Math.round(st.camX);
      if (sx < -40 || sx > G.W + 40) return;
      g.fillStyle = 'rgb(52,56,74)'; g.beginPath(); g.ellipse(sx, P.y, P.rx + 1, P.ry + 1, 0, 0, Math.PI * 2); g.fill();
      g.fillStyle = st.state.tod === 'storm' ? 'rgb(70,80,110)' : 'rgb(120,150,190)'; g.beginPath(); g.ellipse(sx, P.y, P.rx, P.ry, 0, 0, Math.PI * 2); g.fill();
      g.strokeStyle = 'rgb(130,146,180)'; g.lineWidth = 1; g.beginPath(); g.ellipse(sx, P.y, P.rx - 2, P.ry - 1, 0, (200 * Math.PI) / 180, (330 * Math.PI) / 180); g.stroke();
      // 倒影：倒过来的旅人，染上水的颜色，只在水洼里
      const pl = G.world.player;
      if (pl && pl.visible && Math.abs(pl.x - P.x) < P.rx + 14 && Math.abs(pl.y - P.y) < 8) {
        const at = pl.atlasFor(pl.anim);
        g.save(); g.beginPath(); g.ellipse(sx, P.y, P.rx, P.ry, 0, 0, Math.PI * 2); g.clip();
        g.translate(0, 2 * (pl.y + 1)); g.scale(1, -1);
        at.draw(g, pl.anim, pl.frameIndex(), pl.x - Math.round(st.camX), pl.y + 1, { flip: pl.facing < 0, alpha: 0.75, tint: { color: 'rgb(80,96,140)', k: 0.35 } });
        g.restore();
      }
      // 雨点打出来的涟漪
      if (st.state.tod === 'storm') {
        const rnd = G.prng(Math.floor(t * 4) * 13 + 1), ph = G.mod(t * 4, 1), rr = 1 + ph * 4;
        g.strokeStyle = 'rgb(150,166,200)';
        for (let i = 0; i < 4; i++) { const qx = sx + (rnd() * 2 - 1) * (P.rx - 4), qy = P.y + (rnd() * 2 - 1) * (P.ry - 1); g.beginPath(); g.ellipse(qx, qy, rr, rr * 0.35, 0, 0, Math.PI * 2); g.stroke(); }
      }
      // 踩进去：水花
      const now = !!(pl && Math.abs(pl.x - P.x) < P.rx - 4 && Math.abs(pl.y - P.y) < 5);
      if (now && !inside) splash(S, pl.x + 3, FLOOR);
      inside = now;
    } });
  }
  function splash(S, wx, wy) {
    const st = G.world.stage, t0 = st.t;
    S.sfx('land', 0.4, 1.5);
    for (let i = 0; i < 14; i++) { const a = G.rand(195, 345) * Math.PI / 180, v = G.rand(20, 55); G.fx.add({ kind: 'px', x: wx, y: wy, vx: Math.cos(a) * v, vy: Math.sin(a) * v, color: i % 2 ? 'rgb(200,214,245)' : 'rgb(150,170,215)', life: 0.4, g: 260 }); }
    const ring = S.prop({ type: 'custom', x: 0, y: 0, depth: 101, draw: (g, x, y, t) => {
      const u = t - t0;
      if (u > 0.5) return;
      const rr = 2 + u * 26;
      g.strokeStyle = 'rgb(170,186,220)'; g.beginPath(); g.ellipse(wx - Math.round(st.camX), wy + 1, rr, rr * 0.25, 0, 0, Math.PI * 2); g.stroke();
    } });
    G.world.ticks.push(() => { if (G.world.stage !== st || st.t - t0 > 0.55) { S.unprop(ring); return true; } return false; });
  }
  // 木桶堆：三个桶（左下、右下、上面）；被银时砸中就飞出去，转着落地、躺平
  function barrels(S) {
    const st = G.world.stage, pile = [[-6, 0, 0], [7, 0, 1], [1, -13, 0]], vel = [[-70, -150, -540], [60, -190, 620], [-10, -260, 900]];
    const B = { crash: null };
    B.prop = S.prop({ type: 'custom', x: 0, y: 0, depth: FLOOR + 1, draw: (g, x, y, t) => {
      pile.forEach(([dx, dy, v], i) => {
        const img = im(`barrel_${v}`), w = img.width, h = img.height;
        if (!G.ready(img)) return;
        let bx = PILE_X + dx, by = FLOOR + dy, rot = 0;
        if (B.crash != null) {
          const [vx, vy, spin] = vel[i], d = t - B.crash, gr = 520;
          const tl = (-vy + Math.sqrt(Math.max(0, vy * vy - 2 * gr * (by - FLOOR)))) / gr;
          if (d < tl) { bx += vx * d; by += vy * d + 0.5 * gr * d * d; rot = (spin * d * Math.PI) / 180; }
          else { bx += vx * tl + vx * 0.25 * Math.min(0.3, d - tl); by = FLOOR; rot = (vx < 0 ? 90 : -90) * Math.PI / 180; }
        }
        const sx = Math.round(bx - st.camX);
        g.save(); g.translate(sx, Math.round(by + 1 - h / 2)); g.rotate(rot); g.drawImage(img, -Math.floor(w / 2), -Math.floor(h / 2)); g.restore();
      });
    } });
    return B;
  }
  // 二楼阳台的栏杆盖在阳台上的人前面（原片 railing_strip：把店面第 73–88 行再贴一遍）
  function railing(S) {
    const st = G.world.stage;
    return S.prop({ type: 'custom', x: 0, y: 0, depth: BAL + 1, draw: (g) => {
      const m = G.D.bg.ch14_street[st.state.tod || 'storm'], fac = G.image(m.facade.image), P = G.D.bg.ch14_street.common.period;
      if (!G.ready(fac)) return;
      const o = G.mod(Math.floor(st.camX), P), mx = st.state.mix;
      g.drawImage(fac, o, 73, G.W, 16, 0, 73, G.W, 16);
      if (mx && mx.k > 0) { const f2 = G.image(G.D.bg.ch14_street[mx.tod].facade.image); g.globalAlpha = Math.min(1, mx.k); g.drawImage(f2, o, 73, G.W, 16, 0, 73, G.W, 16); g.globalAlpha = 1; }
    } });
  }
  async function rainyStreet(S) {
    const p = S.setPlayer('gintoki__hooded', { x: 30, y: FLOOR + 4, facing: 1, name: '？？？', hp: 100, speed: 46 });
    G.D.bg.ch14_storm.fg = [Object.assign({}, RAIN)];
    await S.setStage('street_ch14', { x: 30, y: FLOOR + 4, facing: 1, fade: false });
    const st = G.world.stage;
    storm(S);
    puddle(S);
    DATA.barrels = barrels(S);
    railing(S);
    // 二楼阳台上的两个人（还没注意到楼下）
    S.pose(gear(S.actor('shin')), 'shinpachi_idle_sad'); S.pose(gear(S.actor('kag')), 'kagura_umbrella_sad');
    S.sfx('rain', 0.7);
    await S.fadeIn(0.8);
    S.hint('（操控斗篷旅人）在雨里往右走', 5);
    void p; void st;
  }
  // 第一次踩进水洼：靴子特写 → 镜头往上摇 → 兜帽下两点红光（原片 B1）
  async function bootsCloseup(S) {
    const p = S.player;
    S.letterbox(true);
    p.x = PUD.x - 22; p.y = PUD.y; p.facing = 1;
    S.zoom(4.6, p.x + 6, FLOOR + 6, 0);
    S.sfx('footsteps', 0.35);
    const walk = S.walk(p, PUD.x + 16, PUD.y, { speed: 30 });
    await S.animate(1.3, (u) => { G.world.zoom = { k: G.lerp(4.6, 4.3, u), x: p.x + 6, y: FLOOR + 6 }; });
    await walk;
    S.pose(p, 'idle_hood');
    await S.animate(0.4, (u) => { G.world.zoom = { k: 4.2, x: p.x + 6, y: G.lerp(FLOOR + 6, FLOOR - 22, easeIO(u)) }; });
    // 两点红光
    S.sfx('shing', 0.5);
    overlay((g, u) => {
      const [ex, ey] = scr(p.x + (p.facing > 0 ? 1 : -1) * 1, p.y - 19);
      for (const dx of [-10, 13]) {
        const q = u / 0.22, s = Math.round(16 * Math.sin(Math.min(1, q) * Math.PI / 2) * (q < 1.4 ? 1 : 0.6)), x = Math.round(ex + dx), y = Math.round(ey);
        if (s > 0) {
          g.fillStyle = 'rgb(230,40,50)'; g.fillRect(x - s, y - 1, 2 * s + 1, 3);
          g.fillStyle = 'rgb(255,110,110)'; g.fillRect(x - s - 4, y, 2 * s + 9, 1); g.fillRect(x, y - (s >> 1), 1, s + 1);
          g.fillStyle = 'rgb(255,240,240)'; g.fillRect(x - (s >> 1), y, s + 1, 1);
        }
        g.fillStyle = 'rgb(255,245,245)'; g.fillRect(x - 1, y - 1, 3, 3);
      }
    }, 0.6, 3);
    mark('ch14_eyes');
    await S.wait(0.8);
    S.zoom(1, null, null, 0.3);
    await S.wait(0.3);
    S.unpose(p);
    S.letterbox(false);
  }
  const RAIN_TALK = {
    chef: [['townsman__chef', '这雨下了三天了……客人，要不要进来吃碗拉面，暖暖身子？'], [null, '旅人摇了摇头。']],
    aunt: [['townswoman__v1', '万事屋的老板？……两年前那一仗之后，就再也没人见过他了。'], ['townswoman__v1', '留下那两个孩子，每天都在店门口等。……真叫人心疼。']],
    madao: [['hasegawa', '……这位大哥，你也没地方去吗？纸箱可以分你一半哦。'], [null, '…………（旅人把伞往长谷川那边推了推，走了。）']],
  };
  function rainTalk(key) {
    return async (S, a) => { for (const [who, text] of RAIN_TALK[key]) await S.say(who, text, who ? { actor: a, name: who === 'townsman__chef' ? '拉面店老板' : who === 'townswoman__v1' ? '躲雨的大婶' : undefined } : {}); F()['rain_' + key] = true; };
  }

  // ================================================================ B2–B3：「我回来了。」
  async function homecoming(S) {
    let p = S.player;
    const st = G.world.stage, sp = S.actor('shin'), kg = S.actor('kag');
    G.ui.hints = [];
    S.letterbox(true);
    st.camTarget = 150;
    await S.walk(p, 314, FLOOR, { speed: 30 });
    S.pose(p, 'idle_hood');
    p.facing = 1;
    st.camTarget = 172;
    S.zoom(1.12, 372, 116, 0.6);
    await S.wait(0.5);
    // 新八注意到了「！」，眼镜一闪；神乐转过身来「!?」
    S.pose(sp, 'shock', { restart: true });
    S.sfx('shock', 0.6);
    exclaim('exclaim_0', () => scr(sp.x, BAL - 36));
    overlay((g, u) => { const [x, y] = scr(sp.x + 3, BAL - 22); sparkle(g, x, y, u - 0.02, 6); }, 0.6, 4);
    await S.wait(0.2);
    kg.facing = -1;
    S.pose(kg, 'umbrella_open');
    exclaim('exclaim_1', () => scr(kg.x, BAL - 36));
    mark('ch14_notice');
    await S.wait(0.8);
    // 摘下兜帽
    S.zoom(2.3, p.x + 2, FLOOR - 25, 0.5);
    await S.wait(0.6);
    S.pose(p, 'hood_off', { restart: true });
    S.sfx('whoosh', 0.7, 1.2);
    await S.wait(0.26);
    const np = S.setPlayer('gintoki__cloak', { x: p.x, y: p.y, facing: 1, name: '银时', hp: 100, speed: 72 });
    p = np;
    S.pose(p, 'idle_cloak');
    S.music('ending', 0.7);
    S.sfx('shine', 0.8); S.sfx('sparkle', 0.6);
    for (let i = 0; i < 10; i++) { const a = G.rand(0, Math.PI * 2), v = G.rand(20, 50); G.fx.add({ kind: 'px', x: p.x + 1, y: FLOOR - 30, vx: Math.cos(a) * v, vy: Math.sin(a) * v, color: i % 2 ? '#ffffff' : 'rgb(220,226,245)', life: 0.35, g: -10 }); }
    overlay((g, u) => { const [hx, hy] = scr(p.x - 2, FLOOR - 36); sparkle(g, hx, hy, u - 0.02, 9); sparkle(g, hx + 26, hy + 10, u - 0.18, 6); }, 0.8, 4);
    G.world.zoom = { k: 2.58, x: p.x + 2, y: FLOOR - 25 };
    S.zoom(2.3, p.x + 2, FLOOR - 20, 0.35);
    // 雨停了：雨后的街一点点叠上来，光从云缝里照下来
    const rain = st.bg.fg[0];
    const shafts = overlay((g, u) => {
      const k = (st.state.shafts || 0) * (0.85 + 0.15 * Math.sin(G.time * 2.3)), img = im('light_shafts');
      if (k <= 0 || !G.ready(img)) return;
      g.globalAlpha = 0.22 * k; g.drawImage(img, 0, 0); g.globalAlpha = 1;
    }, null, -5);
    DATA.shafts = shafts;
    await S.animate(1.0, (u) => {
      const k = easeIO(u);
      st.state.mix = { tod: 'day', wet: true, k }; st.state.stormK = 1 - k; st.state.shafts = k * 0.9;
      if (rain) rain.alpha = 1 - k;
    });
    st.state.tod = 'day'; st.state.wet = true; st.state.mix = null;
    if (rain) st.bg.fg = [];
    mark('ch14_back');
    await S.say('gintoki', '我回来了。', { expr: 'normal' });
    S.pose(p, 'idle_cloak_smug');
    await S.wait(0.4);
    // 阳台上：两个人哭了；神乐蹲下来，准备起跳
    S.zoom(2.3, (sp.x + kg.x) / 2, BAL - 16, 0.3);
    S.pose(sp, 'cry'); S.pose(kg, 'kagura_idle_cry');
    overlay((g, u) => {
      for (const [a, ph] of [[sp, 0], [kg, 0.3]]) { const [tx, ty] = scr(a.x - 4, BAL - 22); sparkle(g, tx, ty, u - 0.1 - ph, 4); tears(g, tx + 4, ty + 2, u + ph, -1); tears(g, tx + 10, ty + 2, u + ph + 0.2, 1); }
    }, 1.4, 4);
    await S.wait(1.0);
    S.pose(kg, 'kagura_crouch');
    S.sfx('charge', 0.6, 1.4);
    exclaim('exclaim_2', () => scr(kg.x, BAL - 36), 0.6);
    await S.wait(0.5);
    await dropkick(S);
  }

  // ================================================================ C1：飞踢 → 栽进木桶堆
  async function dropkick(S) {
    const p = S.player, st = G.world.stage, sp = S.actor('shin'), kg = S.actor('kag');
    const KS = [398, BAL], KH = [p.x + 30, FLOOR - 22];
    st.camTarget = 160; st.camX = 160;
    S.zoom(1.5, 160 + 196, 118, 0);
    S.pose(p, 'idle_cloak');
    // 「银酱——！！」
    const T2 = PR().title_2, t0 = G.time;
    overlay((g, u) => {
      const img = G.image(T2.image), k = back(u / 0.12), a = 1 - seg(u, 0.55, 0.7), j = Math.round(Math.sin(u * 14 * Math.PI * 2));
      if (!G.ready(img) || a <= 0) return;
      g.globalAlpha = a;
      g.drawImage(img, Math.round(118 - (T2.w * k) / 2) + j, Math.round(34 - (T2.h * k) / 2), Math.max(1, Math.round(T2.w * k)), Math.max(1, Math.round(T2.h * k)));
      g.globalAlpha = 1;
    }, 0.7, 5);
    void t0;
    S.sfx('jump', 0.8);
    kg.facing = -1; kg.y = FLOOR - 1; kg.z = FLOOR - 1 - BAL;
    S.pose(kg, 'dropkick', { restart: true, freeze: 1 });
    // 新八从阳台跑下楼梯
    shinpachiRuns(S, sp);
    // 斜着冲下来（0.6 秒）
    await S.animate(0.6, (u) => {
      const e = easeIn(u) * 0.7 + u * 0.3;
      kg.x = G.lerp(KS[0], KH[0], e);
      const yy = G.lerp(KS[1], KH[1], e) - 16 * Math.sin(Math.PI * Math.min(1, u * 1.15));
      kg.z = Math.max(0, FLOOR - 1 - yy);
      const a = kg.atlasFor('dropkick').anim('dropkick');
      kg.frozen = Math.floor(G.lerp(0.15, 0.75, u) * (a.frames - 1));
      if (Math.random() < 0.5) G.fx.add({ kind: 'px', x: kg.x + G.rand(4, 20), y: kg.y - kg.z - G.rand(4, 28), vx: 260, vy: 0, color: '#ffffff', life: 0.08 });
    });
    // 冲击帧：先黑剪影在白底上，再白剪影在黑底上
    const ia = overlay((g) => g.drawImage(im('impact_c1_a'), 0, 0), null, -10);
    S.sfx('punch_big', 1.0); S.sfx('impact', 0.9);
    await S.wait(0.035);
    unoverlay(ia);
    const ib = overlay((g) => g.drawImage(im('impact_c1_b'), 0, 0), null, -10);
    await S.wait(0.035);
    unoverlay(ib);
    S.shake(5, 0.35);
    word('sfx_1', () => { const [x, y] = scr(KH[0], KH[1]); return [x - 20, y - 40]; }, 0.4);
    overlay((g, u) => { if (u < 0.13) { const [x, y] = scr(KH[0], KH[1]); rays(g, x, y - 8, G.time, 44, '#ffffff', 60); } }, 0.13, 3);
    for (let i = 0; i < 18; i++) { const a = G.rand(0, Math.PI * 2), v = G.rand(60, 160); G.fx.add({ kind: 'px', x: KH[0] - 6, y: KH[1] - 8, vx: Math.cos(a) * v, vy: Math.sin(a) * v, color: i % 2 ? '#ffffff' : 'rgb(255,230,90)', life: 0.45, g: 80 }); }
    // 斗篷脱下来，飘下去
    const gx = p.x, gy = FLOOR, tc = st.t;
    const cloth = S.prop({ type: 'custom', x: 0, y: 0, depth: FLOOR - 2, draw: (g, x, y, t) => {
      const cl = seg(t - tc, 0, 0.65), sx = Math.round(gx - Math.round(st.camX));
      if (cl < 1) {
        const fr = PR()[`cloth_fly_${Math.floor(t * 17.83) % 8}`], img = G.image(fr.image);
        const cx = sx - 34 * easeOut(cl) + Math.sin(t * 2.2 * Math.PI * 2) * 4, cy = G.lerp(gy - 22, gy - 2, easeIn(cl)) - 8 * Math.sin(cl * Math.PI);
        g.save(); g.translate(Math.round(cx), Math.round(cy)); g.rotate((Math.sin(t * 1.6 * Math.PI * 2) * 35 * Math.PI) / 180); g.drawImage(img, -fr.anchor[0], -fr.anchor[1]); g.restore();
      } else { const l = PR().cloth_lying; g.drawImage(G.image(l.image), sx - 34 - l.anchor[0], gy - l.anchor[1]); }
    } });
    DATA.cloth = cloth;
    // 银时转着圈飞出去（换回不披斗篷的样子），砸进木桶堆
    const gin = gear(S.setPlayer('gintoki', { x: gx, y: FLOOR, facing: 1, name: '银时', hp: 100, speed: 72 }));
    S.pose(gin, 'fly', { speed: 2.2 });
    gin.shadow = false;
    // 神乐踢完弹回来，落地
    const kx0 = KH[0], kz0 = kg.z;
    S.animate(0.2, (u) => { kg.x = G.lerp(kx0, 350, u); kg.z = kz0 * (1 - u) + 22 * Math.sin(Math.PI * u); S.pose(kg, 'jump'); })
      .then(() => { kg.z = 0; kg.y = FLOOR; S.pose(kg, 'land', { restart: true }); G.fx.dust(350, FLOOR, 8); S.wait(0.25).then(() => S.pose(kg, 'shout')); });
    S.zoom(2.4, KH[0] - 4, KH[1] - 4, 0);
    S.zoom(1.5, 160 + 196, 118, 0.3);
    await S.animate(0.27, (u) => {
      const k = u;
      gin.x = G.lerp(gx - 4, PILE_X + 2, k); gin.y = FLOOR; gin.z = G.lerp(16, 4, k) + 4 * 10 * k * (1 - k);
    });
    // 哐当！！
    DATA.barrels.crash = st.t;
    gin.z = 0; gin.y = FLOOR - 25; gin.x = PILE_X + 1;
    S.pose(gin, 'gintoki_barrel_twitch');
    S.sfx('crash', 1.0); S.shake(3, 0.25);
    for (let i = 0; i < 14; i++) { const a = G.rand(190, 350) * Math.PI / 180, v = G.rand(60, 150); G.fx.add({ kind: 'px', x: PILE_X, y: FLOOR - 8, vx: Math.cos(a) * v, vy: Math.sin(a) * v, color: G.pick(['rgb(150,96,56)', 'rgb(100,62,38)', '#ffffff']), life: 0.5, g: 320 }); }
    G.fx.dust(PILE_X, FLOOR, 10); G.fx.dust(PILE_X + 16, FLOOR, 6);
    word('sfx_0', () => { const [x, y] = scr(PILE_X, FLOOR - 8); return [x + 12, y - 72]; }, 0.6);
    mark('ch14_crash');
    await S.wait(0.9);
    S.pose(gin, 'gintoki_barrel_twitch', { freeze: 0 });
    await S.wait(0.4);
    await tsukkomi(S);
  }
  function shinpachiRuns(S, sp) {     // 阳台 → 外楼梯 → 街上
    const SDc = G.D.bg.ch14_street.common, [[xb, yb], [xt, yt]] = SDc.stairs, st = G.world.stage, t0 = st.t;
    const stairY = (wx) => G.lerp(yb, yt, (wx - xb) / (xt - xb));
    S.pose(sp, 'run');
    G.world.ticks.push(() => {
      if (G.world.stage !== st) return true;
      const t = st.t - t0;
      if (t < 0.1) return false;
      if (t < 0.45) { sp.x = G.lerp(362, xt - 2, seg(t, 0.1, 0.45)); sp.y = BAL; sp.facing = 1; }
      else if (t < 1.05) { sp.x = G.lerp(xt - 2, xb, seg(t, 0.45, 1.05)); sp.y = stairY(sp.x); sp.facing = -1; }
      else if (t < 1.35) { sp.x = G.lerp(xb, 372, seg(t, 1.05, 1.35)); sp.y = FLOOR; }
      else { sp.y = FLOOR; S.pose(sp, 'shock'); return true; }
      return false;
    });
  }

  // ================================================================ C2：「你到底跑哪去了！！」
  async function tsukkomi(S) {
    const st = G.world.stage, gin = S.player, sp = S.actor('shin'), kg = S.actor('kag');
    // 银时从桶堆里掉出来，躺在地上冒星星；神乐跪在后面哭
    gin.x = 236; gin.y = FLOOR + 6; gin.z = 0;
    S.pose(gin, 'lie');
    kg.x = 246; kg.y = FLOOR - 2; kg.facing = -1;
    S.pose(kg, 'cry');
    st.camTarget = 120; st.camX = 120;
    S.zoom(2.2, 252, 146, 0); S.zoom(2.4, 252, 146, 3.5);
    const fx1 = overlay((g, u) => {
      const [hx, hy] = scr(gin.x - 10, gin.y - 16);
      if (!F().yo) dizzy(g, hx, hy, u, 9);
      const [kx, ky] = scr(kg.x - 3, kg.y - 17);
      tears(g, kx, ky, u, -1); tears(g, kx + 7, ky, u + 0.2, 1);
      if (kg.anim === 'cry' || kg.anim === 'shout') { if (Math.floor(u / 0.45) % 2) { if (kg.anim !== 'shout') kg.play('shout'); } else if (kg.anim !== 'cry') kg.play('cry'); }
    }, null, 3);
    // 新八冲过来，急刹车
    sp.x = 330; sp.y = FLOOR; sp.facing = -1;
    S.pose(sp, 'shinpachi_run_shock');
    S.sfx('run', 0.6);
    await S.animate(0.3, (u) => { sp.x = G.lerp(330, 290, easeOut(u)); if (Math.random() < 0.3) G.fx.dust(sp.x + 6, FLOOR, 1); });
    S.pose(sp, 'point', { restart: true });
    S.flash(0.12, 0.35);
    S.shake(3, 0.25);
    word('sfx_2', () => { const [x, y] = scr(sp.x - 6, FLOOR - 24); return [x + 30, y - 34]; }, 0.9);
    overlay((g, u) => { if (u < 0.55) { const [x, y] = scr(sp.x - 6, FLOOR - 24); rays(g, x - 30, y, G.time, 46, '#ffffff', 96); } }, 0.55, 2);
    mark('ch14_tsukkomi');
    await S.say('shinpachi', '你到底跑哪去了！！', { actor: sp, expr: 'shout' });
    // 举起一只手：「……哟。」→ 新八青筋暴起
    F().yo = true;
    S.pose(gin, 'gintoki_lie_wave', { restart: true });
    S.sfx('pop', 0.6, 0.8);
    const bub = overlay((g) => { const b = PR().bubble_yo, [hx, hy] = scr(gin.x - 12, gin.y - 20); g.drawImage(G.image(b.image), Math.round(hx - (b.tip[0] - b.x)), Math.round(hy - (b.tip[1] - b.y))); }, null, 4);
    await S.wait(0.8);
    S.sfx('vein', 0.7);
    S.shake(2, 0.15);
    const vein = overlay((g, u) => { const [vx, vy] = scr(sp.x + 3, FLOOR - 31), v = PR()[Math.floor(u * 8) % 2 ? 'anger_vein_b' : 'anger_vein_a']; g.drawImage(G.image(v.image), Math.round(vx - v.anchor[0]), Math.round(vy - v.anchor[1])); }, null, 4);
    await S.say('gintoki', '……哟。', { expr: 'normal' });
    unoverlay(bub);
    await S.say('shinpachi', '「哟」什么「哟」啊！！两年！整整两年！！一封信都没有！！', { actor: sp, expr: 'angry' });
    unoverlay(vein); unoverlay(fx1);
    S.zoom(1, null, null, 0.3);
    await kaguraFight(S);
  }

  // ================================================================ 神乐：「两年的份，一次讨回来阿鲁！」
  async function kaguraFight(S) {
    const st = G.world.stage, gin = S.player, sp = S.actor('shin'), kg = S.actor('kag');
    S.letterbox(true);
    gin.y = FLOOR + 4; S.unpose(gin); gin.facing = 1;
    kg.x = gin.x + 60; kg.y = FLOOR + 4; kg.facing = -1;
    S.pose(kg, 'ready');
    S.sfx('vein', 0.6);
    await S.say('kagura', '……两年。两年的份……一次讨回来阿鲁！！', { actor: kg, expr: 'angry' });
    await S.say('gintoki', '喂喂，刚回来就要动手吗！？', { expr: 'shock' });
    S.letterbox(false);
    S.camera(null);
    const cx = G.clamp(Math.round(gin.x - 150), 0, 1152 - G.W), sx0 = gin.x + 90;
    // 输了重来时，被打倒的人会被清出地图：把新八放回场边（他 5 秒后才加进来）
    const fresh = () => {
      if (!st.actors.includes(sp) || sp.remove) { sp.remove = false; sp.dead = false; st.add(sp); }
      Object.assign(sp, { team: 'npc', hp: 50, maxHp: 50, state: 'idle', hold: false, script: null, x: sx0, y: FLOOR + 6, facing: -1, z: 0 });
      S.pose(sp, 'shock');
    };
    S.hint('打到神乐消气为止（新八也会加进来）', 5);
    await S.fight({
      arena: [cx, cx + G.W], music: 'battle',
      waves: [[{ actor: 'kag', cid: 'kagura', name: '神乐（两年的份）', hp: 300, boss: true, speed: 76, range: 26, minHp: 60, moves: ['E_PUNCH', 'E_HEAVY', 'E_PUNCH', 'E_GUN'] }]],
      onWave: (S, wi, sp2, attempt) => { sp2.forEach(gear); if (attempt > 0) fresh(); },
      events: [{ when: (t) => t > 5, run: async (S) => {
        await S.say('shinpachi', '我……我也有份！！这两年的账！！', { actor: sp, expr: 'shout' });
        Object.assign(sp, { team: 'enemy', maxHp: 50, hp: 50, speed: 50, range: 24, moves: [G.MOVES.E_SLASH], state: 'idle', hold: false, script: null, cool: 1.2, minHp: 10, idleAnim: 'idle', boss: false, dead: false });
        S.unpose(sp);
      } }],
      endWhen: () => { const k = S.actor('kag'); return G.world.fightT > 35 || !!(k && k.team === 'enemy' && k.hp <= 150); },
      after: null,
    });
    const kg2 = gear(S.actor('kag') || kg);       // 输过的话，神乐是重新生成的那个
    for (const a of [kg2, sp]) { a.team = 'npc'; a.minHp = 0; }
    G.ui.boss = null;
    // 打完：神乐哭着不撒手
    S.letterbox(true);
    sp.x = gin.x + 50; sp.y = gin.y; sp.facing = -1; kg2.x = gin.x + 24; kg2.y = gin.y + 1; kg2.facing = -1;
    S.pose(kg2, 'kagura_idle_cry'); S.pose(sp, 'cry');
    gin.facing = 1;
    S.music('ending', 0.6);
    await S.say('kagura', '……笨蛋银酱。……欢迎回来阿鲁。', { actor: kg2, expr: 'cry' });
    await S.say('shinpachi', '……欢迎回来，银时先生。', { actor: sp, expr: 'cry' });
    await S.say('gintoki', '……嗯。让你们久等了。', { expr: 'normal' });
    await S.fadeOut(1.0);
    S.letterbox(false);
    await townStart(S);
  }

  // ================================================================ D：日常·回归中（白天的歌舞伎町）
  let caption = null;
  function cornerCaption() {      // 左上角「日常·回归中」：滑进来，小黄灯一闪一闪
    const c = PR().corner_caption;
    return overlay((g, u) => {
      const x = Math.round(G.lerp(c.x - 116, c.x, easeOut(u / 0.2))), y = c.y + Math.round(G.ui.letterbox);     // 有黑边时往下挪，别被盖住
      g.drawImage(G.image(c.image), x, y);
      if (Math.floor(G.time * 1.5 * 2) % 2 === 0) { g.fillStyle = 'rgb(255,214,60)'; g.fillRect(x + 82, y + 6, 5, 5); }
    }, null, 1);
  }
  async function townStart(S) {
    const p = S.setPlayer('gintoki', { x: 360, y: FLOOR + 6, facing: 1, name: '银时', hp: 100, speed: 74 });
    gear(p);
    await S.setStage('town_ch14', { x: 360, y: FLOOR + 6, facing: 1, fade: false });
    const sp = gear(S.spawn('shinpachi', 330, FLOOR + 2, { id: 'shin', name: '新八', facing: 1 }));
    const kg = gear(S.spawn('kagura', 312, FLOOR + 8, { id: 'kag', name: '神乐', facing: 1 }));
    S.follow(sp); S.follow(kg);
    talkFollower(S, sp, 'shin'); talkFollower(S, kg, 'kag');
    S.music('yorozuya', 0.6);
    await S.fadeIn(0.8);
    caption = cornerCaption();
    S.hint('日常·回归中：在街上逛逛，和大家打个招呼', 6);
  }
  function talkFollower(S, a, who) {
    a.label = who === 'shin' ? '新八' : '神乐';
    a.talk = async (S, me) => {
      const done = gags();
      if (who === 'shin') await S.say('shinpachi', done >= 3 ? '……大家都还是老样子呢。回家吧，银时先生。' : '大家都很想你哦。……虽然没人会说出口。', { actor: me });
      else await S.say('kagura', done >= 3 ? '定春在家里等着呢！快回去阿鲁！' : '银酱，今天的晚饭你请客阿鲁。两年的份。', { actor: me, expr: 'happy' });
    };
  }
  const gags = () => ['gag_kondo', 'gag_okita', 'gag_zura'].filter((k) => F()[k]).length;
  function gagDone(S, key) {
    F()[key] = true;
    if (gags() >= 3) S.hint('好像听到了定春的叫声……回万事屋门口看看', 6);
  }
  const TOWN_TALK = {
    otose: [['otose', '……两年没交的房租，利滚利，你自己算算吧。'], ['gintoki', '……当我没回来。'], ['otose', '哼。……回来就好。']],
    catherine: [['catherine', '哟，天然卷，还活着啊。我还以为能把你的房间租出去了。']],
    tama: [['tama', '欢迎回来，银时先生。房租的计算结果已经准备好了。一共是……'], ['gintoki', '不用念了。']],
    hasegawa: [['hasegawa', '银桑！你回来了啊！……我还住在纸箱里哦。'], ['gintoki', '……你倒是一点都没变。']],
    tsukuyo: [['tsukuyo', '……回来了啊。吉原的太阳，今天也照常升起。'], ['seita', '银桑！娘让我带句话：欢迎回来！']],
    yamazaki: [['yamazaki', '……副长在河堤那边。冲田队长也在。……我什么都没说哦。']],
    sakamoto: [['sakamoto', '啊哈哈哈！金时！两年不见，你一点都没长高啊！'], ['gintoki', '……是银时。还有你也没长。']],
    otsu: [['otsu', '新歌《两年后的歌舞伎町》发售中！请多指教～！'], ['shinpachi', '通酱～～！！']],
  };
  function townTalk(key) {
    return async (S, a) => {
      for (const [who, text] of TOWN_TALK[key]) await S.say(who, text, who === a.cid ? { actor: a } : {});
      F()['t_' + key] = true;
    };
  }
  // ---------------- 段子一：阿妙 × 草丛里的近藤
  async function gagKondo(S, ot) {
    const st = G.world.stage, kd = S.actor('kondo'), bush = DATA.bush;
    if (F().gag_kondo) { await S.say('otae', '近藤先生？今天应该在宇宙的某个地方吧。', { actor: ot, expr: 'smile' }); return; }
    await S.say('otae', '哎呀，银桑，欢迎回来。……请稍等一下哦。', { actor: ot, expr: 'smile' });
    S.letterbox(true);
    S.camera(Math.round(ot.x - 176));
    await S.wait(0.4);
    ot.facing = 1;
    kd.visible = true; kd.y = FLOOR; S.pose(kd, 'stalk');
    await S.say('kondo', '阿妙小姐～～！两年不见，请和我结婚吧～～！', { actor: kd, expr: 'shout' });
    S.pose(ot, 'otae_idle_dark');
    await S.wait(0.3);
    S.pose(ot, 'super_punch', { restart: true });
    await S.wait(0.22);
    // 砰！！ → 近藤飞上天变成星星
    S.sfx('punch_big', 1.0); S.flash(0.1, 0.4); S.shake(4, 0.3);
    for (let i = 0; i < 16; i++) { const a = G.rand(0, Math.PI * 2), v = G.rand(60, 150); G.fx.add({ kind: 'px', x: kd.x - 4, y: FLOOR - 20, vx: Math.cos(a) * v, vy: Math.sin(a) * v, color: i % 2 ? '#ffffff' : 'rgb(255,200,220)', life: 0.4, g: 60 }); }
    word('sfx_3', () => { const [x, y] = scr(kd.x - 4, FLOOR - 20); return [x + 10, y - 34]; }, 0.55);
    bush.shake = st.t;
    S.pose(kd, 'fly');
    const k0 = [kd.x, FLOOR - 6], sky = [kd.x + 30, 12];
    S.sfx('whoosh', 0.7);
    await S.animate(0.42, (u) => {
      const e = u * 0.35 + easeIO(u) * 0.65;
      kd.x = G.lerp(k0[0], sky[0], e); kd.y = FLOOR; kd.z = FLOOR - G.lerp(k0[1], sky[1], e); kd.scale = G.lerp(1, 0.3, easeIn(u));
    });
    kd.visible = false; kd.z = 0; kd.scale = 1;
    G.fx.star(G.clamp(sky[0] - Math.round(st.camX), 12, G.W - 12));
    S.sfx('twinkle', 0.7);
    mark('ch14_kondo_star');
    await S.wait(0.6);
    S.pose(ot, 'otae_idle_dark');
    await S.say('otae', '……真是的，两年了还是一点都没变呢。', { actor: ot, expr: 'smile' });
    S.unpose(ot);
    S.camera(null);
    S.letterbox(false);
    gagDone(S, 'gag_kondo');
  }
  // ---------------- 段子二：河堤上，冲田轰土方
  async function gagOkita(S, ok) {
    if (F().gag_okita) { await S.say('okita', '土方先生的爆炸头？……那是新发型，别笑他哦。噗。', { actor: ok, expr: 'smug' }); return; }
    await S.say('okita', '旦那，回来得正好。……要不要看看我新学的烟花？', { actor: ok, expr: 'smug' });
    const st0 = G.world.stage, back = { x: S.player.x, y: S.player.y }, carry = ['shin', 'kag'].map((id) => S.actor(id)).filter(Boolean);
    S.flash(0.1, 0.45);
    await S.fadeOut(0.25);
    await S.setStage('river_ch14', { x: -200, y: 190, fade: false });
    const st = G.world.stage;
    S.player.visible = false;
    const hj = gear(S.spawn('hijikata', 150, 176, { id: 'hj', name: '土方', facing: 1 }));
    const o2 = gear(S.spawn('okita', 300, 176, { id: 'ok2', name: '冲田', facing: -1 }));
    S.pose(hj, 'smoke'); S.pose(o2, 'bazooka', { freeze: 0 });
    S.zoom(1.75, 216, 146, 0); S.zoom(1.85, 216, 146, 2.5);
    const pet = weather(S, (g, t) => sakura(g, t, 14, 5, 22, 16, ['rgb(255,190,210)', 'rgb(255,226,236)']));
    S.letterbox(true);
    await S.fadeIn(0.25);
    await S.wait(0.3);
    // 瞄准 → 开火 → 炮弹 → 轰！！
    const bz = o2.atlasFor('bazooka').anim('bazooka');
    await S.animate(0.25, (u) => { o2.frozen = Math.floor(u * 0.5 * (bz.frames - 1)); });
    S.sfx('bazooka', 0.9);
    const t0 = st.t, x0 = 300 - 26, y0 = 176 - 24;
    const shell = S.prop({ type: 'custom', x: 0, y: 0, depth: 300, draw: (g, x, y, t) => {
      const k = seg(t - t0, 0, 0.08);
      if (k >= 1) return;
      const sx = G.lerp(x0, 156, k), sy = G.lerp(y0, 176 - 18, k);
      g.fillStyle = 'rgb(230,230,230)'; g.fillRect(Math.round(sx), Math.round(sy), 30, 1);
      g.fillStyle = INK; g.fillRect(Math.round(sx) - 3, Math.round(sy) - 2, 7, 4);
      g.fillStyle = 'rgb(90,110,80)'; g.fillRect(Math.round(sx) - 2, Math.round(sy) - 1, 5, 2);
    } });
    S.animate(0.5, (u) => { o2.frozen = Math.floor((0.5 + 0.5 * u) * (bz.frames - 1)); });
    await S.wait(0.08);
    S.unprop(shell);
    S.sfx('explosion', 1.0); S.flash(0.12, 0.5, '#fff0c8'); S.shake(5, 0.4);
    G.fx.debris(152, 158, ['#ffd25a', '#ff8a3c', '#ffffff', '#5a5a64'], 30, [40, 160], 200, 0.7);
    for (let i = 0; i < 10; i++) G.fx.add({ kind: 'puff', x: 152 + G.rand(-14, 14), y: 160 + G.rand(-6, 6), vx: G.rand(-20, 20), vy: G.rand(-30, -8), r: G.rand(4, 8), life: G.rand(0.6, 1.1), color: i % 3 ? '170,166,176' : '255,190,90' });
    word('sfx_4', () => { const [x, y] = scr(150, 176 - 50); return [x + 8, y - 6]; }, 0.5);
    await S.wait(0.26);
    S.pose(hj, 'hijikata_shock_afro');
    const wisp = weather(S, (g, t) => { for (let i = 0; i < 3; i++) { const ph = G.mod(t * 1.5 + i / 3, 1); px(g, hj.x - 4 + i * 4 - Math.round(st.camX) + Math.round(Math.sin(t * 2 * Math.PI * 2 + i) * 1.5), 176 - 40 - ph * 14, 'rgb(150,150,160)'); } });
    await S.wait(0.16);
    // 「总悟——！！」/ ♪
    const T5 = PR().title_5;
    const sg = overlay((g, u) => {
      const [hx, hy] = scr(hj.x, 176 - 46), j = Math.round(Math.sin(u * 16 * Math.PI * 2));
      g.drawImage(G.image(T5.image), Math.round(hx + 4 - T5.w / 2) + j, Math.round(hy - 8 - T5.h / 2));
      if (u > 0.12) { const [ox, oy] = scr(o2.x - 4, 176 - 44); G.f16.draw(g, '♪', ox, oy - Math.round(Math.sin(u * 2 * Math.PI * 2) * 2), '#ffffff', { align: 'center', outline: INK }); }
    }, null, 5);
    mark('ch14_afro');
    S.pose(hj, 'hijikata_idle_afro');
    await S.say('hijikata', '总悟——！！你小子！！', { actor: hj, expr: 'angry' });
    await S.say('okita', '欢迎回来，土方先生。……啊，说错了，是旦那。', { actor: o2, expr: 'smug' });
    unoverlay(sg);
    S.unprop(wisp); S.unprop(pet);
    S.flash(0.1, 0.45);
    await S.fadeOut(0.25);
    S.zoom(1, null, null, 0);
    S.letterbox(false);
    S.player.visible = true;
    await S.setStage('town_ch14', { x: back.x, y: back.y, carry, fade: false });
    carry.forEach((c) => S.follow(c));
    await S.fadeIn(0.3);
    void st0;
    gagDone(S, 'gag_okita');
  }
  // ---------------- 段子三：「不是假发，是桂！」
  async function gagZura(S, kt) {
    if (F().gag_zura) { await S.say('katsura', '……攘夷志士桂小太郎，今天也在为国家奔走。……嗯？这个荞麦面好吃。', { actor: kt }); return; }
    S.letterbox(true);
    await S.say('gintoki', '……假发～', { expr: 'smug' });
    const P = PR(), ka = G.atlas('katsura');
    let turned = false, zura = null, keira = null, eli = null;
    const D3 = overlay((g, u) => {
      // 转起来的放射背景
      g.fillStyle = 'rgb(255,176,60)'; g.fillRect(0, 0, G.W, G.H);
      g.fillStyle = 'rgb(255,214,110)';
      const rot = G.time * 0.6;
      for (let i = 0; i < 18; i++) {
        const a0 = rot + (i * 2 * Math.PI) / 18, a1 = a0 + Math.PI / 18;
        g.beginPath(); g.moveTo(268, 110); g.lineTo(268 + Math.cos(a0) * 460, 110 + Math.sin(a0) * 460); g.lineTo(268 + Math.cos(a1) * 460, 110 + Math.sin(a1) * 460); g.closePath(); g.fill();
      }
      rays(g, 268, 120, G.time, 36, 'rgba(255,250,230,0.9)', 110);
      const jx = keira != null ? Math.round(Math.sin(G.time * 18 * Math.PI * 2)) : 0;
      if (!turned) ka.draw(g, 'idle', Math.floor(G.time * 12) % ka.anim('idle').frames, 292, 198, { scale: 3 });
      else { const an = ka.anim('point'), f = Math.min(an.frames - 1, Math.floor((G.time - turned) / 0.35 * an.frames)); ka.draw(g, 'point', f, 292 + jx, 198, { scale: 3, flip: true }); }
      if (!turned) { const b = P.bubble_zura; g.drawImage(G.image(b.image), b.x, b.y); }
      if (zura != null) { const T3 = P.title_3, k = back((G.time - zura) / 0.12), img = G.image(T3.image); g.drawImage(img, Math.round(168 - (T3.w * k) / 2), Math.round(34 - (T3.h * k) / 2), Math.max(1, Math.round(T3.w * k)), Math.max(1, Math.round(T3.h * k))); }
      if (keira != null) {
        const T4 = P.title_4, s = G.lerp(2.2, 1, easeIn(seg(G.time - keira, 0, 0.08))), img = G.image(T4.image);
        g.drawImage(img, Math.round(176 + Math.round(Math.sin(G.time * 20 * Math.PI * 2)) - (T4.w * s) / 2), Math.round(84 - (T4.h * s) / 2), Math.round(T4.w * s), Math.round(T4.h * s));
        const fl = 0.6 * (1 - seg(G.time - keira, 0, 0.12));
        if (fl > 0) { g.fillStyle = `rgba(255,255,255,${fl.toFixed(2)})`; g.fillRect(0, 0, G.W, G.H); }
      }
      if (eli != null) {
        const k = seg(G.time - eli, 0, 0.22), ey = 250 - 82 * back(k), an = X().anim('elizabeth_sign_没错');
        X().draw(g, 'elizabeth_sign_没错', Math.floor((0.3 + 0.7 * k) * (an.frames - 1)), 34, ey, { scale: 2 });
      }
    }, null, -10);
    S.sfx('record_scratch', 0.7);
    await S.wait(0.3);
    turned = G.time;
    S.sfx('whoosh', 0.8);
    await S.wait(0.13);
    zura = G.time;
    S.sfx('pop', 0.7);
    await S.wait(0.22);
    keira = G.time;
    S.sfx('impact', 0.9);
    S.shake(5, 0.35);
    await S.wait(0.5);
    eli = G.time;
    S.sfx('pop', 0.7, 1.3);
    mark('ch14_zura');
    await S.say('katsura', '不是假发，是桂！', { expr: 'shout' });
    unoverlay(D3);
    await S.say('katsura', '……哼。回来得太晚了，银时。攘夷的同志们都等得不耐烦了。', { actor: kt });
    S.letterbox(false);
    gagDone(S, 'gag_zura');
    void D3;
  }

  // ================================================================ D4–E：定春 → 「完」→ 踢飞
  async function chompAndKan(S) {
    const p = S.player;
    G.ui.hints = [];
    unoverlay(caption);
    await S.fadeOut(0.4);
    p.visible = true;
    G.D.bg.ch14_front.fg = [{ type: 'kstreet_rail', alpha: 1 }];      // 雨早就停了
    await S.setStage('front_ch14', { x: 211, y: FF, facing: 1, fade: false });
    const st = G.world.stage;
    st.state.tod = 'day';
    const kg = gear(S.spawn('kagura', 156, FF, { id: 'kag', name: '神乐', facing: 1 }));
    const sp = gear(S.spawn('shinpachi', 182, FF, { id: 'shin', name: '新八', facing: 1 }));
    const sd = gear(S.spawn('sadaharu', 272, FF, { id: 'sada', name: '定春', facing: -1 }));
    S.pose(kg, 'cheer');
    S.pose(sd, 'bite', { freeze: 0 });
    p.x = 211; p.y = FF; p.facing = 1;
    S.pose(p, 'wave');
    S.letterbox(true);
    S.zoom(2.15, 214, 166, 0);
    S.music('comedy', 0.6);
    await S.fadeIn(0.4);
    S.walk(p, 221, FF, { speed: 40, anim: 'wave' }).then(() => S.pose(p, 'wave'));
    await S.say('gintoki', '哟，定春～。好久不见了啊～', { expr: 'happy' });
    // 扑上来 → 咬住
    const bt = sd.atlasFor('bite').anim('bite');
    await S.animate(0.3, (u) => { sd.x = G.lerp(272, 246, easeIn(u)); sd.frozen = Math.floor(0.34 * u * (bt.frames - 1)); });
    S.sfx('chomp', 1.0); S.flash(0.1, 0.35); S.shake(4, 0.25);
    sd.frozen = Math.floor(0.4 * (bt.frames - 1));
    S.pose(p, 'gintoki_chomped');
    p.x = 224;
    S.animate(0.15, (u) => { p.z = 2 + 6 * easeOut(u); });
    S.pose(sp, 'shock', { restart: true });
    G.world.zoom = { k: 2.4, x: 214, y: 166 };
    S.zoom(2.15, 214, 166, 0.25);
    const maw = () => scr(sd.x - 22, FF - 27);
    for (let i = 0; i < 12; i++) { const a = G.rand(0, Math.PI * 2), v = G.rand(50, 120); G.fx.add({ kind: 'px', x: sd.x - 22, y: FF - 27, vx: Math.cos(a) * v, vy: Math.sin(a) * v, color: i % 2 ? '#ffffff' : 'rgb(200,230,255)', life: 0.4, g: 240 }); }
    word('sfx_5', () => { const [x, y] = maw(); return [x - 30, y - 44]; }, 0.5);
    const sw = overlay((g, u) => { const [bx, by] = scr(221, FF - 16); sweat(g, bx - 16, by - 6, u); sweat(g, bx + 14, by - 10, u + 0.4); const [wx, wy] = scr(182, FF - 36); sweat(g, wx + 12, wy, u); }, null, 4);
    await S.wait(0.04);
    S.pose(sd, 'bite_loop');
    await S.wait(0.28);
    S.sfx('chomp', 0.8);
    word('sfx_6', () => { const [x, y] = maw(); return [x + 28, y - 52]; }, 0.55);
    mark('ch14_chomp');
    await S.wait(0.5);
    S.sfx('chomp', 0.8);
    await S.wait(0.3);
    unoverlay(sw);
    // E：定格，变灰，巨大的「完」字砸下来
    S.stopMusic(0.1);
    for (const a of G.world.stage.actors) { a.frozen = a.frameIndex(); a.script = null; }
    S.filter('grayscale(0.85) sepia(0.12)');
    S.sfx('record_scratch', 0.8);
    S.flash(0.1, 0.5);
    await S.wait(0.15);
    const P = PR(), tS = G.time;
    let kick = null, crackT = null;
    overlay((g, u) => {
      const now = G.time;
      if (kick == null) {
        const k = seg(u, 0, 0.1), s = G.lerp(2.6, 1, easeIn(k)), st2 = P[crackT != null ? 'stamp_kan_1' : 'stamp_kan_0'];
        let jx = 0, jy = 0;
        if (crackT != null) { jx = Math.round(Math.sin(now * 22 * Math.PI * 2) * 2); jy = -Math.abs(Math.round(Math.sin(now * 11 * Math.PI * 2) * 3)); }
        g.save(); g.translate(G.W / 2 + jx, G.H / 2 - 6 + jy); g.rotate((-9 * Math.PI) / 180); g.globalAlpha = 0.6 + 0.4 * k;
        g.drawImage(G.image(st2.image), Math.round((-st2.w * s) / 2), Math.round((-st2.h * s) / 2), Math.round(st2.w * s), Math.round(st2.h * s));
        g.restore();
      } else {         // 踢飞：一边转一边变小，飞到右上角变成星星
        const ks = seg(now - kick, 0, 0.5);
        if (ks < 1) {
          const st2 = P.stamp_kan_1, s = G.lerp(1, 0.12, easeIn(ks));
          g.save(); g.translate(Math.round(G.lerp(G.W / 2, 336, easeOut(ks))), Math.round(G.lerp(G.H / 2 - 6, 24, easeOut(ks)))); g.rotate(((-9 - 900 * ks) * Math.PI) / 180);
          g.drawImage(G.image(st2.image), Math.round((-st2.w * s) / 2), Math.round((-st2.h * s) / 2), Math.max(1, Math.round(st2.w * s)), Math.max(1, Math.round(st2.h * s)));
          g.restore();
        } else sparkle(g, 336, 24, now - kick - 0.5, 9, 'rgb(255,250,200)', 0.9);
      }
    }, null, 3);
    void tS;
    S.sfx('impact', 1.0); S.sfx('gong', 0.8);
    S.shake(6, 0.35);
    for (let i = 0; i < 22; i++) { const a = G.rand(0, Math.PI * 2), v = G.rand(90, 200); G.fx.add({ kind: 'px', x: G.world.stage.camX + G.W / 2, y: G.H / 2, vx: Math.cos(a) * v, vy: Math.sin(a) * v, color: i % 2 ? 'rgb(208,36,48)' : 'rgb(160,20,40)', life: 0.4, g: 40 }); }
    mark('ch14_kan');
    await S.wait(0.3);
    // 沉默……乌鸦飞过
    S.sfx('crow', 0.6);
    overlay((g, u) => { const c = PR()[`crow_${Math.floor(G.time * 8) % 2}`], k = u / 0.85; g.drawImage(G.image(c.image), Math.round(G.lerp(G.W + 10, -40, k)), Math.round(30 + Math.sin(u * 1.3 * Math.PI * 2) * 4)); }, 0.85, 4);
    await S.wait(0.6);
    crackT = G.time;
    S.sfx('thud', 0.8); word('sfx_7', [G.W / 2 - 24, G.H - 34], 0.25);
    await S.wait(0.15);
    S.sfx('thud', 0.8); word('sfx_7', [G.W / 2 + 20, G.H - 34], 0.25);
    await S.wait(0.4);
    // 按 J 踢飞
    G.ui.letterboxTarget = 0;
    for (let n = 0; ; n++) {
      const ok = await S.timing({ label: '才不会完呢——看准时机按 J，一脚踢飞！', speed: 1.1, zone: [0.4, 0.6], tries: 2 });
      if (ok) break;
      S.sfx('thud', 0.6); S.shake(2, 0.2);
      await S.say('gintoki', n ? '……可恶，这字怎么这么硬！' : '……还没完呢！', { expr: 'angry' });
    }
    // 活过来：一脚踢飞「完」字
    S.filter(null);
    for (const a of G.world.stage.actors) a.frozen = null;
    p.x = 190; p.y = FF; p.z = 0; p.facing = 1;
    sd.x = 240; S.pose(sd, 'shock');
    kg.x = 140; S.pose(kg, 'cheer'); sp.x = 160; S.pose(sp, 'cheer');
    S.pose(p, 'gintoki_kick_tilt', { restart: true });
    kick = G.time;
    S.sfx('kick', 1.0); S.sfx('crash', 0.7);
    S.flash(0.1, 0.55); S.shake(5, 0.35);
    word('sfx_8', [236, 70], 0.5);
    overlay((g, u) => { if (u < 0.45) rays(g, 200, 60, G.time, 44, 'rgba(255,236,120,0.9)', 80); }, 0.45, 2);
    S.zoom(2.55, 192, 190, 0);
    S.music('ending', 0.7);
    await S.wait(0.38);
    S.pose(p, 'gintoki_point_sky', { restart: true });
    S.pose(sd, 'bark'); S.sfx('bark', 0.8);
    S.sfx('twinkle', 0.7);
    S.zoom(2.8, 192, 190, 1.6);
    overlay((g, u) => { if (u < 0.6) { const [hx, hy] = scr(190, FF - 26); rays(g, hx, hy, G.time, 40, '#ffffff', 70); } }, 0.6, 2);
    mark('ch14_kick');
    await S.say('gintoki', '才不会完呢！', { expr: 'shout' });
    await S.say('kagura', '对阿鲁！！万事屋，今天也照常营业阿鲁！', { actor: kg, expr: 'happy' });
    S.sfx('cheer', 0.7);
    await S.wait(0.8);
    await S.fadeOut(1.0);
    clearOverlays();
    S.zoom(1, null, null, 0);
    S.letterbox(false);
    await parade(S);
  }

  // ================================================================ F：黄昏的谢幕队列
  const FRONT_ROW = ['shinpachi', 'SADA', 'otae', 'kondo', 'hijikata', 'okita', 'katsura', 'elizabeth', 'hasegawa', 'otose', 'catherine', 'tama', 'GIN'];
  const BACK_ROW = ['yamazaki', 'otsu', 'sakamoto', 'tsukuyo', 'seita', 'kamui', 'umibozu', 'shigeshige', 'townswoman__v1', 'townsman__v2', 'amanto_pig'];
  function layout(row, x0, gap) { const out = []; let x = x0; for (const cid of row) { const w = cid === 'SADA' ? 52 : gap; out.push([cid, x + (w - gap) / 2]); x += w; } return out; }
  async function parade(S) {
    const p = S.player;
    await S.setStage('parade_ch14', { x: -500, y: 200, fade: false });
    const st = G.world.stage;
    p.visible = false;
    const FP = layout(FRONT_ROW, 0, 29), BP = layout(BACK_ROW, 14, 30), CAM0 = 138, PAN = 95, SPD = 125, t0 = st.t, D = 7.2;
    st.camTarget = CAM0; st.camX = CAM0;
    S.prop({ type: 'custom', x: 0, y: 0, depth: 100, draw: (g, x, y, t) => {
      const lt = t - t0, base = 410 - SPD * lt;
      for (const [rows, gy, sd] of [[BP, 158, 0], [FP, 184, 0.37]]) {
        rows.forEach(([cid, off], i) => {
          const sx = base + off;
          if (sx < -40 || sx > G.W + 40) return;
          const tt = t + i * 0.13 + sd;
          if (cid === 'SADA') { drawChar(g, 'sadaharu', 'walk', tt, sx, gy, { facing: -1 }); drawChar(g, 'kagura', 'cheer', tt, sx + 2, gy - 30 - (Math.floor(tt * 6) % 2), { facing: -1, shadow: false }); }
          else if (cid === 'GIN') drawChar(g, 'gintoki', 'gintoki_walk_jump', tt, sx, gy, { facing: -1 });
          else if (cid === 'kondo') drawChar(g, 'kondo', 'kondo_walk_love', tt, sx, gy, { facing: -1 });
          else drawChar(g, cid, 'walk', tt, sx, gy, { facing: -1 });
        });
      }
    } });
    G.world.ticks.push(() => { if (G.world.stage !== st) return true; st.camTarget = st.camX = CAM0 + PAN * (st.t - t0); return false; });
    S.zoom(1.22, 0, 146, 0);
    G.world.ticks.push(() => { if (G.world.stage !== st) return true; G.world.zoom = { k: 1.22, x: Math.round(st.camX) + 192, y: 146 }; return false; });
    overlay((g, u) => {
      sakura(g, G.time, 20, 8, 22, 16, ['rgb(255,200,170)', 'rgb(255,225,200)', 'rgb(250,160,150)']);
      const a = seg(u, 0.1, 0.4);
      if (a > 0) {
        g.fillStyle = `rgba(14,8,24,${(0.55 * a).toFixed(3)})`; g.fillRect(0, 6, G.W, 46);
        g.fillStyle = 'rgb(255,200,120)'; g.fillRect(0, 6, G.W, 1); g.fillRect(0, 51, G.W, 1);
        G.f16.draw(g, '原作：空知英秋《银魂》', G.W / 2, 11 - Math.round((1 - easeOut(a)) * 6), 'rgb(255,240,210)', { align: 'center', outline: INK });
      }
      const a2 = seg(u, 0.45, 0.75);
      if (a2 > 0) G.f12.draw(g, '本作为同人像素致敬作品', G.W / 2, 33 + Math.round((1 - easeOut(a2)) * 5), 'rgb(255,214,150)', { align: 'center', outline: INK });
      sparkle(g, 60, 20, u - 0.2, 5, 'rgb(255,230,160)'); sparkle(g, 322, 38, u - 0.6, 4, 'rgb(255,230,160)');
    }, D + 0.6, 2);
    S.sfx('cheer', 0.6); S.sfx('crowd', 0.4);
    await S.fadeIn(0.6);
    mark('ch14_parade');
    await S.wait(D);
    await S.fadeOut(0.8);
    clearOverlays();
    S.zoom(1, null, null, 0);
    await thanks(S);
  }

  // ================================================================ G：黄昏的事务所「感谢观看」
  async function thanks(S) {
    const p = S.player;
    await S.setStage('office_ch14', { x: 92, y: 153, facing: 1, fade: false });
    const st = G.world.stage, P = PR();
    p.visible = true; p.x = 92; p.y = 153; p.facing = 1;
    S.pose(p, 'read');
    const sp = gear(S.spawn('shinpachi', 198, 128, { id: 'shin', name: '新八', facing: -1 })); S.pose(sp, 'sit');
    const kg = gear(S.spawn('kagura', 294, 151, { id: 'kag', name: '神乐', facing: -1 })); S.pose(kg, 'sleep');
    const sd = gear(S.spawn('sadaharu', 276, 196, { id: 'sada', name: '定春', facing: -1 })); S.pose(sd, 'lie');
    for (const [k, d] of [['dusk_desk_fg', 129], ['dusk_table_fg', 160]]) { const f = P[k]; S.prop({ type: 'image', image: f.image, x: f.x, y: f.y, depth: d }); }
    S.zoom(1.3, 176, 150, 0); S.zoom(1.4, 176, 150, 3.0);
    S.music('ending', 0.6);
    await S.fadeIn(0.8);
    const T1 = P.title_1;
    overlay((g, u) => {
      const a = seg(u, 0.15, 0.5);
      if (a <= 0) return;
      g.fillStyle = `rgba(20,10,26,${(0.5 * a).toFixed(3)})`; g.fillRect(0, 12, G.W, 70);
      g.fillStyle = 'rgb(255,200,120)'; g.fillRect(0, 12, G.W, 1); g.fillRect(0, 81, G.W, 1);
      const s = back(a), img = G.image(T1.image);
      g.drawImage(img, Math.round(G.W / 2 - (T1.w * s) / 2), Math.round(34 - (T1.h * s) / 2), Math.max(1, Math.round(T1.w * s)), Math.max(1, Math.round(T1.h * s)));
      const a2 = seg(u, 0.5, 0.8);
      if (a2 > 0) G.f12.draw(g, 'THANK YOU FOR WATCHING', G.W / 2, 56 - Math.round((1 - a2) * 4), 'rgb(230,220,255)', { align: 'center', outline: INK });
      if (u > 0.9) G.f12.draw(g, '银魂 · 像素剧场', G.W / 2, 70, 'rgb(255,190,150)', { align: 'center', outline: INK });
      sparkle(g, 96, 26, u - 0.4, 5, 'rgb(255,240,190)'); sparkle(g, 290, 44, u - 0.7, 4, 'rgb(255,240,190)'); sparkle(g, 262, 18, u - 1.1, 5, 'rgb(255,240,190)');
    }, null, 2);
    mark('ch14_thanks');
    await S.wait(3.2);
    // 银时抬眼一笑 → 镜头推近 → 圆形收光
    S.sfx('shine', 0.6);
    overlay((g, u) => { const [ex, ey] = scr(100, 133); sparkle(g, ex, ey, u, 5); }, 0.6, 3);
    await S.zoom(2.2, 98, 139, 0.85);
    S.sfx('slide_down', 0.6);
    const ir = overlay((g, u) => {
      const ip = easeIn(seg(u, 0, 0.62)), [hx, hy] = scr(96, 131), r = (1 - Math.min(1, ip / 0.93 * 0.93 + (ip > 0.92 ? 0.07 : 0))) * 260;
      g.fillStyle = '#000'; g.beginPath(); g.rect(0, 0, G.W, G.H); if (r > 0.5) g.arc(hx, hy, r, 0, Math.PI * 2, true); g.fill('evenodd');
    }, null, 8);
    await S.wait(1.4);
    void ir; void st;
    G.fadeAlpha = 1;
    clearOverlays();
    S.zoom(1, null, null, 0);
    F().ch14Done = true;
  }

  // ================================================================ 地图（终章版）
  const DATA = {};
  function defineStages() {
    G.STAGES.front_ch14 = { id: 'front_ch14', bg: 'ch14_front', x0: 0, x1: 384, yMin: 188, yMax: 206, props: [], state: { tod: 'storm' } };
    G.STAGES.street_ch14 = { id: 'street_ch14', bg: 'ch14_storm', x0: 0, x1: 1152, yMin: 158, yMax: 182, props: [], state: { tod: 'storm' },
      npcs: [
        { cid: 'townsman__chef', id: 'chef', x: 52, y: 159, facing: 1, label: '拉面店老板', talk: rainTalk('chef') },
        { cid: 'townswoman__v1', id: 'aunt', x: 150, y: 159, facing: -1, label: '躲雨的大婶', talk: rainTalk('aunt') },
        { cid: 'hasegawa', id: 'madao', x: 196, y: 158, facing: 1, anim: 'box', label: '纸箱', talk: rainTalk('madao') },
        { cid: 'shinpachi', id: 'shin', x: 362, y: BAL, facing: -1, name: '新八' },
        { cid: 'kagura', id: 'kag', x: 398, y: BAL, facing: 1, name: '神乐' },
      ],
      triggers: [
        { id: 'puddle', x0: PUD.x - 30, x1: PUD.x - 14, cond: () => !F().puddle, run: async (S) => { F().puddle = true; await bootsCloseup(S); } },
        { id: 'home', x0: 284, x1: 9999, cond: () => !F().home, run: async (S) => { F().home = true; await homecoming(S); } },
      ] };
    G.STAGES.town_ch14 = { id: 'town_ch14', bg: 'ch14_day', x0: 0, x1: 1152, yMin: 158, yMax: 182, props: [], state: { tod: 'day', wet: false },
      npcs: [
        { cid: 'hasegawa', id: 'madao', x: 196, y: 158, facing: 1, anim: 'box', label: '长谷川', talk: townTalk('hasegawa') },
        { cid: 'otose', id: 'otose', x: 352, y: 159, facing: 1, anim: 'smoke', label: '登势', talk: townTalk('otose') },
        { cid: 'catherine', id: 'cath', x: 410, y: 160, facing: -1, label: '凯瑟琳', talk: townTalk('catherine') },
        { cid: 'tama', id: 'tama', x: 440, y: 159, facing: -1, anim: 'mop', label: '小玉', talk: townTalk('tama') },
        { cid: 'katsura', id: 'zura', x: 560, y: 160, facing: -1, label: '桂', talk: async (S, a) => gagZura(S, a) },
        { cid: 'elizabeth', id: 'eli', x: 588, y: 159, facing: -1, label: '伊丽莎白', talk: async (S) => { await S.say(null, '伊丽莎白举起了牌子：『桂先生说的都对』'); } },
        { cid: 'otsu', id: 'otsu', x: 640, y: 160, facing: 1, label: '阿通', talk: townTalk('otsu') },
        { cid: 'okita', id: 'okita', x: 700, y: 160, facing: -1, anim: 'bazooka', label: '冲田', talk: async (S, a) => gagOkita(S, a) },
        { cid: 'yamazaki', id: 'yama', x: 760, y: 159, facing: -1, label: '山崎', talk: townTalk('yamazaki') },
        { cid: 'tsukuyo', id: 'tsuku', x: 840, y: 160, facing: -1, anim: 'smoke', label: '月咏', talk: townTalk('tsukuyo') },
        { cid: 'seita', id: 'seita', x: 866, y: 162, facing: -1, label: '晴太' },
        { cid: 'otae', id: 'otae', x: 976, y: 160, facing: -1, label: '阿妙', talk: async (S, a) => gagKondo(S, a) },
        { cid: 'kondo', id: 'kondo', x: 1032, y: 160, facing: -1, anim: 'stalk', visible: false, cond: () => !F().gag_kondo },
        { cid: 'sakamoto', id: 'sakamoto', x: 1100, y: 160, facing: -1, anim: 'laugh', label: '坂本', talk: townTalk('sakamoto') },
      ],
      triggers: [{ id: 'yorozuya', x0: 330, x1: 392, cond: () => gags() >= 3 && !F().kan, run: async (S) => { F().kan = true; await chompAndKan(S); } }] };
    G.STAGES.river_ch14 = { id: 'river_ch14', bg: 'ch14_river', x0: 0, x1: 384, yMin: 170, yMax: 200, props: [] };
    G.STAGES.parade_ch14 = { id: 'parade_ch14', bg: 'ch14_dusk', x0: -4000, x1: 8000, yMin: 150, yMax: 200, props: [], state: { tod: 'dusk' } };
    G.STAGES.office_ch14 = { id: 'office_ch14', kind: 'office', bg: 'ch14_office', x0: 0, x1: 384, yMin: 150, yMax: 200, props: [] };
  }
  // 白天的街：近藤藏的草丛（被打飞以后还在抖）
  function townProps(S) {
    const st = G.world.stage;
    if (st.id !== 'town_ch14') return;
    const B = { shake: null };
    B.prop = S.prop({ type: 'custom', x: 0, y: 0, depth: FLOOR + 1, draw: (g, x, y, t) => {
      const b = PR().kondo_bush_0, jx = B.shake != null ? Math.round(Math.sin((t - B.shake) * 12 * Math.PI * 2) * 1.5 * (1 - seg(t - B.shake, 0, 0.6))) : 0;
      g.drawImage(G.image(b.image), Math.round(1032 - st.camX - b.w / 2) + jx, FLOOR - b.h + 1);
    } });
    DATA.bush = B;
  }

  // ================================================================ 终章主流程
  G.STORY.chapter14 = async function (S) {
    defineStages();
    OV.length = 0;
    G.fadeAlpha = 0;
    G.world.stage = null;
    await S.chapterCard('ch14');
    const p = new G.Actor('gintoki__hooded', 30, FLOOR + 4, { id: 'player', team: 'player', hp: 100, speed: 46, name: '？？？' });
    G.world.player = p;
    G.fadeAlpha = 1;
    G.D.bg.ch14_front.fg = [{ type: 'kstreet_rail', alpha: 1 }, Object.assign({}, RAIN, { ground: [194, 214] })];
    await S.setStage('front_ch14', { x: 30, y: FF, facing: 1, fade: false });
    await S.run(async (S) => { await rainyFront(S); await rainyStreet(S); });
    // 白天的街每次进来都要摆上草丛
    const hook = () => { const st = G.world.stage; if (st && st.id === 'town_ch14' && !st._ch14) { st._ch14 = true; townProps(G.S); } return !!F().ch14Done; };
    await S.until(hook);
    clearOverlays();
    S.filter(null);
    G.ui.letterboxTarget = 0;
  };
})();
