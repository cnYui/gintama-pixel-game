// 第十三章：银之魂篇（原片 s13，最终章「江户最漫长的一夜」）
//   巨大的母舰沉下来，探照灯扫过江户「天人舰队，遮蔽了江户的天空。」→ 屋顶上乌鸦炸开，虚现身（名牌）→ 特写睁眼：「我即是虚。」
//   → 沿着屋顶往右推进，三段，每段先是原片的蒙太奇（白闪、染色、集中线、组名牌滑进来，一组组人从天而降），再一起打：
//      ① 真选组 · 攘夷志士   ② 最强女子 · 登势酒馆 · MADAO（乌鸦「阿呆～」）   ③ 快援队 · 夜兔一族 · 万事屋
//      → 两道屋脊的大合影「全江户，集结！」→ 第三段可以选银时 / 神乐 / 新八来打。打完的人留在屋顶上，可以聊天
//   → 尽头：高杉落在背后「别拖后腿啊，银时。」→ 背靠背打奈落 → 两人一起 X 字斩，虚笑着再生
//   → 第一阶段：和高杉一起压制虚 → 虚的突刺，高杉推开银时替他挡下（冲击帧）→「高杉——！！」
//      → 怀里的高杉「银时……剩下的，交给你了。」→ 一闪而过的松下私塾（木刀「啪！」）→ 手垂下去 → 一滴泪
//   → 放下高杉，连按站起来，眼神亮起来 → 第二阶段：撑到天亮（天色一点点变亮，舰队一点点变淡）
//   → 天亮：看准时机最后一斩（冲击帧）→ 虚冻住、裂开、碎成光 → 光变成松阳：「……谢谢。你们都长大了呢。」
//   → 江户的日出：舰队退走，紫色的蝴蝶绕着银时飞了两圈，飞进太阳里
'use strict';
(function () {
  const G = window.G;
  const F = () => G.flags;
  const PR = () => G.D.bg.ch13.props;
  const FXD = () => G.D.bg.ch13_night.fx;
  const px = (g, x, y, c, w = 1, h = 1) => { g.fillStyle = c; g.fillRect(Math.round(x), Math.round(y), w, h); };
  const X = () => G.atlas('s13_extra');
  function gear(a) { if (a && G.D.chars.s13_extra) a.alt = [X()]; return a; }
  const seg = (t, a, b) => G.clamp((t - a) / (b - a), 0, 1);
  const easeOut = (u) => 1 - Math.pow(1 - G.clamp(u, 0, 1), 3);
  const easeIn = (u) => Math.pow(G.clamp(u, 0, 1), 2);
  const easeIO = (u) => { u = G.clamp(u, 0, 1); return u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2; };
  const im = (k) => G.image(PR()[k].image);
  const FY = 168;                 // 屋顶上站人的脚点（屋脊在 160，往下一点踩在瓦上；原片蒙太奇的脚点是 160，所以镜头中心都往下挪 8）
  const INK = 'rgb(24,20,37)';
  const DARK = { color: 'rgb(16,10,26)', k: 0.3 };      // 夜里的奈落，压暗一点
  const NAMES = { gintoki: '银时', kagura: '神乐', shinpachi: '新八' };
  const mark = (name) => { G.dbg = { shot: name }; };     // 给自动试玩截图用（没有台词的镜头）

  // ================================================================ 画面上层（不跟着镜头推近）
  // 组名牌、大字、气泡、特写都画在这里。S.insert 只有一个槽，这里自己排一个列表（z 小的先画，特写 z = -10）
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
  // 画在世界里（会跟着推近）、盖在人物上面的东西：火星、灰、光点、樱花
  function weather(S, fn, depth = 9000) { return S.prop({ type: 'custom', x: 0, y: 0, depth, draw: (g, x, y, t) => fn(g, t) }); }

  // ================================================================ 小特效（原片 fx / _s13_art 里的那些，按时间算）
  function sparkle(g, x, y, u, size = 6, color = '#fff', life = 0.45) {
    if (u < 0 || u > life) return;
    const s = Math.round(Math.sin((u / life) * Math.PI) * size);
    if (s <= 0) return;
    x = Math.round(x); y = Math.round(y);
    g.fillStyle = color;
    g.fillRect(x - s, y, 2 * s + 1, 1); g.fillRect(x, y - s, 1, 2 * s + 1);
    if (s > 2) g.fillRect(x - 1, y - 1, 3, 3);
  }
  function embers(g, t, n, seed, y0 = 40) {      // 往上飘的火星
    const rnd = G.prng(seed * 53 + 1), span = G.H - y0;
    for (let i = 0; i < n; i++) {
      const x0 = rnd() * G.W, yy = rnd() * span, sp = 14 + rnd() * 22, ph = rnd() * 6;
      if (Math.floor(t * 8 + ph * 2) % 5 === 0) continue;
      const c = i % 3 === 0 ? 'rgb(255,200,120)' : i % 3 === 1 ? 'rgb(255,120,60)' : 'rgb(200,50,40)';
      px(g, x0 + Math.sin(t * 1.3 + ph) * 5, y0 + G.mod(yy - t * sp, span), c);
    }
  }
  function ash(g, t, n, seed, color = 'rgb(150,146,160)') {      // 往下落的灰
    const rnd = G.prng(seed * 71 + 3);
    for (let i = 0; i < n; i++) {
      const x0 = rnd() * G.W, y0 = rnd() * G.H, sp = 8 + rnd() * 8, ph = rnd() * 6;
      px(g, x0 + Math.sin(t * 0.9 + ph) * 8, G.mod(y0 + t * sp, G.H), color);
    }
  }
  function motes(g, t, n, seed) {                 // 晨光里往上飘的光点
    const rnd = G.prng(seed * 101 + 7);
    for (let i = 0; i < n; i++) {
      const x0 = rnd() * G.W, y0 = rnd() * G.H, sp = 8 + rnd() * 10, ph = rnd() * 6;
      if (Math.floor(t * 12 + ph * 3) % 6 === 0) continue;
      px(g, x0 + Math.sin(t * 0.8 + ph) * 4, G.mod(y0 - t * sp, G.H + 10) - 5, i % 2 ? 'rgb(255,244,200)' : 'rgb(255,214,150)');
    }
  }
  function sakura(g, t, n, seed, wind, fall) {
    const rnd = G.prng(seed * 37 + 5);
    for (let i = 0; i < n; i++) {
      const x0 = rnd() * (G.W + 40), y0 = rnd() * G.H, ph = rnd() * 6, sp = 0.7 + rnd() * 0.6;
      const x = G.mod(x0 + t * wind * sp + Math.sin(t * 1.7 + ph) * 6, G.W + 40) - 20, y = G.mod(y0 + t * fall * sp, G.H + 10) - 5;
      px(g, x, y, i % 3 ? 'rgb(255,190,210)' : 'rgb(255,226,236)', Math.floor(t * 6 + ph) % 2 ? 2 : 1, 1);
    }
  }
  function feathers(g, t) {                       // 黑色的羽毛
    const rnd = G.prng(21);
    for (let i = 0; i < 12; i++) {
      const x0 = rnd() * G.W, y0 = rnd() * G.H, sp = 12 + rnd() * 14, ph = rnd() * 6;
      const x = x0 + Math.sin(t * 1.4 + ph) * 8, y = G.mod(y0 + t * sp, G.H + 10) - 5;
      px(g, x, y, 'rgb(14,10,18)', 4, 1); px(g, x + 1, y + 1, 'rgb(14,10,18)', 2, 1);
    }
  }
  // 柔和的集中线（原片 soft_speed_lines）：颜色 rgb、透明度 a
  function softLines(g, t, cx, cy, rgb, a, count = 40, inner = 56, seed = 11) {
    const rnd = G.prng(Math.floor(t * 15) * 7 + seed);
    g.fillStyle = `rgba(${rgb.join(',')},${a})`;
    g.beginPath();
    for (let i = 0; i < count; i++) {
      const ang = rnd() * Math.PI * 2, ri = inner + rnd() * 40, w = 0.012 + rnd() * 0.02;
      g.moveTo(cx + Math.cos(ang) * ri, cy + Math.sin(ang) * ri);
      g.lineTo(cx + Math.cos(ang - w) * 460, cy + Math.sin(ang - w) * 460);
      g.lineTo(cx + Math.cos(ang + w) * 460, cy + Math.sin(ang + w) * 460);
      g.closePath();
    }
    g.fill();
  }
  function rays(g, cx, cy, t, a) {                // 太阳的光柱（原片 light_rays：12 道，慢慢转）
    if (a <= 0) return;
    g.fillStyle = `rgba(255,236,190,${a.toFixed(3)})`;
    for (let i = 0; i < 12; i++) {
      const ang = t * 0.04 + (i * Math.PI * 2) / 12 + (i % 2 ? 0.2 : 0), w = 0.07 * (i % 3 === 0 ? 1.3 : 0.8);
      g.beginPath(); g.moveTo(cx, cy);
      g.lineTo(cx + Math.cos(ang - w) * 460, cy + Math.sin(ang - w) * 460);
      g.lineTo(cx + Math.cos(ang + w) * 460, cy + Math.sin(ang + w) * 460);
      g.closePath(); g.fill();
    }
  }
  let VIG = null;
  function vignette(g) {
    if (!VIG) { VIG = g.createRadialGradient(192, 108, 70, 192, 108, 236); VIG.addColorStop(0, 'rgba(60,40,20,0)'); VIG.addColorStop(1, 'rgba(60,40,20,0.7)'); }
    g.fillStyle = VIG; g.fillRect(0, 0, G.W, G.H);
  }
  // 乌鸦（两帧，10 fps）：c = crow_s1_* / crow_s3_* 的道具信息，(x, y) = 原片的落笔点
  function drawCrow(g, c, x, y, flip) {
    const img = G.image(c.image);
    if (!G.ready(img)) return;
    const ox = c.x - 8, oy = c.y - 8;
    if (!flip) g.drawImage(img, Math.round(x + ox), Math.round(y + oy));
    else { g.save(); g.translate(Math.round(x - ox), Math.round(y + oy)); g.scale(-1, 1); g.drawImage(img, 0, 0); g.restore(); }
  }
  // 画面坐标里画一个角色（合影、回忆这类不放真角色的镜头）：动作在 s13_extra 里就用它
  function drawChar(g, cid, anim, t, x, y, o = {}) {
    const at = X().has(anim) ? X() : G.atlas(cid), a = at.anim(anim);
    let f = o.frame;
    if (f == null && o.p != null) f = Math.floor(o.p * (a.frames - 1));
    if (f == null) f = a.kind === 'loop' ? Math.floor(Math.max(0, t) * a.fps) % a.frames : Math.min(a.frames - 1, Math.floor(Math.max(0, t) * a.fps));
    if (o.shadow !== false) { g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(Math.round(x) - 6, Math.round(y) - 1, 12, 2); }
    at.draw(g, anim, f, x, y, { flip: (o.facing || 1) < 0, tint: o.tint, alpha: o.alpha });
  }
  // 原片 drop()：tl 秒落地（提前 fall 秒从 h0 高处掉下来），落地 0.08 秒后摆姿势，hop = 跳起来几像素
  function dropDraw(g, cid, anim, x, y, u, tl, o = {}) {
    const fall = o.fall || 0.1, h0 = o.h0 || 70;
    if (u < tl - fall) return;
    if (u < tl) { const k = seg(u, tl - fall, tl); drawChar(g, cid, 'jump', u, x, y - h0 * (1 - k * k), Object.assign({}, o, { shadow: false, p: null })); return; }
    if (u < tl + 0.08) { drawChar(g, cid, 'land', u - tl, x, y, Object.assign({}, o, { p: null })); return; }
    drawChar(g, cid, anim, u - tl + (o.ph || 0), x, y - (o.hop || 0), Object.assign({}, o, { shadow: (o.hop || 0) < 2 }));
  }

  // ================================================================ 背景：火光 + 黎明 + 太阳
  // 原片 edo_blend：夜景上面按比例叠一整套黎明的图层（离屏画布，透明度按 1/12 取整）。st.state：dawn 0..1、armada 舰队浓度、sunX/sunY、rays
  const DAWN = {};
  function dawnStack(g, st, camX, t, withRoof) {
    const fx = FXD();
    DAWN.bg.layers.forEach((L, i) => {
      if (L.type === 'roof' && !withRoof) return;
      DAWN.bg.layer(g, L, camX, t, st);
      if (i !== 0) return;
      // 天空之后：光柱、太阳（在云、山、城的后面）
      const sx = st.state.sunX || 292, sy = st.state.sunY || 152;
      rays(g, sx, sy, t, (st.state.rays || 0) / 255);
      const glow = G.image(fx.sun.glow), disc = G.image(fx.sun.disc);
      g.save(); g.globalCompositeOperation = 'lighter';
      if (G.ready(glow)) g.drawImage(glow, Math.round(sx) + fx.sun.glow_off, Math.round(sy) + fx.sun.glow_off);
      g.restore();
      if (G.ready(disc)) g.drawImage(disc, Math.round(sx) + fx.sun.disc_off, Math.round(sy) + fx.sun.disc_off);
    });
  }
  function skyFx(S) {
    const st = G.world.stage, fx = FXD();
    DAWN.bg = new G.Background(G.D.bg.ch13_dawn);
    DAWN.oc = Object.assign(document.createElement('canvas'), { width: G.W, height: G.H });
    DAWN.ox = DAWN.oc.getContext('2d'); DAWN.ox.imageSmoothingEnabled = false;
    const fire = G.image(fx.fire.image);
    return S.prop({ type: 'custom', x: 0, y: 0, depth: -9999, draw: (g, x, y, t) => {
      const k = st.state.dawn || 0;
      if (k < 1 && G.ready(fire)) {          // 城里烧起来的火光（屋脊后面）
        g.save(); g.globalCompositeOperation = 'lighter';
        g.globalAlpha = 0.6 * (1 - k) * (0.8 + 0.2 * Math.sin(7 * t) * Math.sin(3.1 * t));
        g.drawImage(fire, 0, fx.fire.y); g.restore();
      }
      if (k <= 0) return;
      DAWN.ox.clearRect(0, 0, G.W, G.H);
      dawnStack(DAWN.ox, st, Math.round(st.camX), t, true);
      g.globalAlpha = Math.round(k * 12) / 12; g.drawImage(DAWN.oc, 0, 0); g.globalAlpha = 1;
    } });
  }

  // ================================================================ 蒙太奇用的零件
  const LABEL_DUR = 2.0;
  function groupLabel(i, dur = LABEL_DUR) {      // 组名牌：从左边滑进来，停一会儿，滑出去
    const L = PR()[`label_${i}_full`];
    return overlay((g, u) => {
      const img = G.image(L.image);
      if (!G.ready(img)) return;
      const k = u < 0.12 ? easeOut(u / 0.12) : u > dur - 0.15 ? 1 - easeOut((u - dur + 0.15) / 0.15) : 1;
      g.drawImage(img, Math.round(L.x - (L.w + 30) * (1 - k)), L.y);
    }, dur, 6);
  }
  // 镜头的背景：整屏染一层颜色 + 柔和的集中线（画在背景之上、人物之下）
  function cutBg(S) {
    const cb = { tint: null, lines: null, cx: 192, cy: 142 };
    cb.prop = S.prop({ type: 'custom', x: 0, y: 0, depth: -9000, draw: (g, x, y, t) => {
      if (cb.tint) { g.fillStyle = `rgba(${cb.tint.join(',')},0.18)`; g.fillRect(0, 0, G.W, G.H); }
      if (cb.lines) softLines(g, t, cb.cx, cb.cy, cb.lines, 0.35);
    } });
    return cb;
  }
  // 切镜头：白闪、换染色、推近（原片的镜头中心，脚点差 8 像素）、名牌滑进来
  function cutTo(S, cb, c) {
    const cx = G.world.stage.camX;
    S.flash(0.07, 0.8);
    S.sfx('whoosh', 0.7);
    cb.tint = c.tint; cb.lines = c.lines; cb.cx = c.z[2]; cb.cy = (c.lcy || 134) + 8;
    S.zoom(c.z[0], cx + c.z[2], c.z[3] + 8, 0);
    S.zoom(c.z[1], cx + c.z[2], c.z[3] + 8, c.hold || 1.4);
    if (c.label != null) groupLabel(c.label);
  }
  // 一个人登场：tl = 落地的时间（null = 直接站在那里），sx = 画面 x
  async function castIn(S, cid, sx, pose, tl, o = {}) {
    const st = G.world.stage;
    const a = gear(S.spawn(cid, st.camX + sx, o.y || FY, { id: o.id || cid, name: o.name, facing: o.facing || 1 }));
    if (tl == null) {
      S.pose(a, pose, { freeze: o.delay ? 0 : o.freeze });
      if (o.delay) { await S.wait(o.delay); S.pose(a, pose, { restart: true, freeze: o.freeze }); }
      return a;
    }
    const fall = o.fall || 0.14;
    a.visible = false;
    await S.wait(Math.max(0, tl - fall));
    a.visible = true; a.z = o.h0 || 90;
    await S.arc(a, a.x, a.y, 0, fall, { anim: 'jump', z1: 0 });
    a.z = 0;
    G.fx.dust(a.x - 5, a.y, 3); G.fx.dust(a.x + 5, a.y, 3);
    S.sfx('land', 0.5);
    S.pose(a, 'land', { restart: true });
    await S.wait(0.08);
    S.pose(a, pose, { restart: true, freeze: o.freeze });
    return a;
  }
  const hide = (list) => list.forEach((a) => { if (a) a.visible = false; });
  // 打之前把大家摆好：[id, 画面 x, y, 朝向]（pose 留空 = 解开姿势）
  function arrange(S, list) {
    const st = G.world.stage;
    for (const [id, sx, y, f, pose] of list) {
      const a = S.actor(id);
      if (!a) continue;
      a.x = st.camX + sx; a.y = y; a.facing = f; a.visible = true; a.z = 0;
      if (pose) S.pose(a, pose); else S.unpose(a);
    }
  }
  // 打完以后同伴别挤成一团：各自走回一个位置（能一个个过去搭话）
  function regroup(S, cx, spots) {
    for (const [id, sx, y, f] of spots) {
      const a = S.actor(id);
      if (!a || a.remove) continue;
      a.hold = false;
      S.walk(a, cx + sx, y, { speed: 70 }).then(() => { a.facing = f; });
    }
  }
  function frameCam(S, x) {      // 镜头直接跳过去（白闪盖住）
    const st = G.world.stage;
    x = Math.round(G.clamp(x, st.x0, st.x1 - G.W));
    st.camTarget = x; st.camX = x; G.world.focus = null;
    return x;
  }
  const foes = (tag, list, hp) => list.map((cid, i) => ({ cid, id: `${tag}${i}`, name: cid === 'naraku' ? '奈落' : cid === 'harusame' ? '春雨' : '天人', hp, side: i % 2 ? 'left' : 'right' }));
  const darkNaraku = (S, wi, sp) => sp.forEach((a) => { gear(a); if (a.cid === 'naraku') a.tint = DARK; });
  function makotoFlag(S, wx) {     // 插在屋顶上的「诚」字旗（12 帧，13.37 fps）
    const st = G.world.stage;
    return S.prop({ type: 'custom', x: 0, y: 0, depth: FY - 4, draw: (g, x, y, t) => {
      const f = PR()[`makoto_flag_${Math.floor(t * 13.37) % 12}`];
      g.drawImage(G.image(f.image), Math.round(wx - st.camX) - f.anchor[0], FY - 2 - f.anchor[1]);
    } });
  }
  function crowBurst(S, wx, wy, wisps = false) {    // 乌鸦炸开（wisps = 先有黑色的风卷进来）；返回乌鸦飞出去的时间点
    const st = G.world.stage, t0 = st.t, P = PR(), B = wisps ? 0.6 : 0;
    const pr = S.prop({ type: 'custom', x: 0, y: 0, depth: 9100, draw: (g, x, y, t) => {
      const u = t - t0, sx = wx - Math.round(st.camX);
      if (wisps && u < B) {
        for (let i = 0; i < 18; i++) {
          const k = seg(u, i * 0.012, B), r = (1 - k) * (60 + (i % 5) * 9), a = i * 2.4 + k * 5;
          if (k <= 0 || k >= 1) continue;
          px(g, sx + Math.cos(a) * r, wy + Math.sin(a) * r * 0.6, i % 3 ? 'rgb(40,14,48)' : 'rgb(150,40,90)', 2, 2);
        }
      }
      if (u < B) return;
      const d = u - B, rnd = G.prng(13);
      for (let i = 0; i < 10; i++) {
        const ang = -2.9 + rnd() * 2.65, v = 70 + rnd() * 70, ph = rnd() * 2;
        const cx2 = sx + Math.cos(ang) * v * d, cy2 = wy + Math.sin(ang) * v * d - 14 * d;
        if (cy2 < -20 || cx2 < -30 || cx2 > G.W + 30) continue;
        drawCrow(g, P[`crow_s${i % 3 === 0 ? 3 : 1}_${Math.floor(t * 10 + ph) % 2}`], cx2, cy2, Math.cos(ang) < 0);
      }
      if (d < 0.5) {
        const r2 = G.prng(5);
        for (let i = 0; i < 22; i++) { const a = r2() * Math.PI * 2, v = 30 + r2() * 60; px(g, sx + Math.cos(a) * v * d, wy + Math.sin(a) * v * d + 10 * d * d, i % 2 ? 'rgb(150,40,90)' : 'rgb(60,20,70)'); }
      }
    } });
    G.world.ticks.push(() => { if (G.world.stage !== st || st.t - t0 > B + 2.5) { S.unprop(pr); return true; } return false; });
    return B;
  }

  // ================================================================ 开场：舰队 → 虚
  async function opening(S) {
    const p = S.player, st = G.world.stage, P = PR();
    frameCam(S, 0);
    st.state.armada = 1; st.state.dawn = 0;
    p.visible = false;
    // B：巨大的母舰慢慢沉下来，江户暗下去，三道探照灯扫来扫去
    const ms = P.ship_mothership_x2_night_h5, t0 = st.t;
    const B = S.prop({ type: 'custom', x: 0, y: 0, depth: -9990, draw: (g, x, y, t) => {
      const k = easeIO(seg(t - t0, 0, 2.8));
      g.fillStyle = 'rgba(18,6,26,0.32)'; g.fillRect(0, 0, G.W, G.H);
      const img = G.image(ms.image);
      if (G.ready(img)) g.drawImage(img, Math.round(232 - 0.04 * st.camX - ms.w / 2), Math.round(G.lerp(-22, 4, k) - ms.h / 2));
      g.fillStyle = 'rgba(210,225,255,0.13)';
      for (let i = 0; i < 3; i++) {
        const bx = 50 + 140 * i, by = 146, a = -Math.PI / 2 + (28 * Math.PI / 180) * Math.sin(0.7 * t + 2.1 * i);
        g.beginPath(); g.moveTo(bx, by);
        g.lineTo(bx + Math.cos(a - 0.07) * 260, by + Math.sin(a - 0.07) * 260);
        g.lineTo(bx + Math.cos(a + 0.07) * 260, by + Math.sin(a + 0.07) * 260);
        g.closePath(); g.fill();
      }
    } });
    S.letterbox(true);
    S.zoom(1.9, 232, 60, 0); S.zoom(1, 232, 60, 2.6);
    S.sfx('engine_hum', 0.55); S.sfx('thunder', 0.6);
    S.shake(2, 1.6);
    await S.fadeIn(0.6);
    S.wait(1.2).then(() => mark('ch13_armada'));
    await S.narrate('天人舰队，遮蔽了江户的天空。', { auto: 2.6 });
    S.unprop(B);
    // C1：屋顶上，黑色的风卷进来 → 乌鸦炸开 → 虚慢慢显形
    S.flash(0.12, 0.7);
    p.visible = true; p.x = 60; p.y = FY; p.facing = 1;
    S.pose(p, 'ready');
    S.zoom(1.5, 180, 142, 0); S.zoom(1.7, 180, 142, 1.8);
    S.sfx('whoosh', 0.6); S.sfx('aura', 0.7);
    const ut = gear(S.spawn('utsuro', 230, FY, { id: 'utsuro', name: '虚', facing: -1 }));
    ut.alpha = 0; ut.tint = { color: 'rgb(10,4,16)', k: 1 };
    S.pose(ut, 'regen');
    await S.wait(crowBurst(S, 230, 142, true));
    S.sfx('crow', 0.8); S.sfx('sting_dramatic', 0.8);
    S.flash(0.06, 0.5, '#c03c64');
    S.animate(0.7, (u) => { ut.alpha = Math.min(1, u * 2.5); ut.tint = { color: 'rgb(10,4,16)', k: 1 - u }; });
    await S.wait(0.15);
    S.nameCard('utsuro');
    S.wait(0.6).then(() => mark('ch13_reveal'));
    await S.wait(1.7);
    ut.tint = null;
    // C2：血色的特写：闭着的眼睛 → 睁开，红光
    let glow = false, gT = 0;
    const C2 = overlay((g, u) => {
      g.drawImage(im('grad_c2'), 0, 0);
      g.save(); g.globalCompositeOperation = 'lighter'; g.drawImage(im('glow_r70_0.9'), 30, 40); g.restore();
      embers(g, u, 30, 21, 0);
      const b = PR()[glow ? 'bust_utsuro_glow' : 'bust_utsuro_blink'], x0 = Math.round(100 - b.w / 2), y0 = 76 + (Math.floor(u * 2) % 2);
      g.drawImage(G.image(b.image), x0, y0);
      if (glow) { sparkle(g, x0 + 34, y0 + 50, u - gT, 5, 'rgb(255,200,210)'); sparkle(g, x0 + 58, y0 + 50, u - gT - 0.03, 5, 'rgb(255,200,210)'); }
      feathers(g, u);
    }, null, -10);
    S.sfx('heartbeat', 0.8);
    await S.wait(0.4);
    glow = true; gT = G.time - C2.t0;
    S.sfx('shine', 0.8);
    S.flash(0.15, 0.5, '#ff3c50');
    await S.wait(0.3);
    await S.say('utsuro', '我即是虚。', { actor: ut, expr: 'glow' });
    unoverlay(C2);
    S.zoom(1, null, null, 0);
    S.flash(0.08, 0.5);
    S.pose(ut, 'utsuro_idle_smile');
    await S.say('gintoki', '……管你是谁。压在江户头顶上的东西，统统给我滚下去。', { expr: 'angry' });
    await S.say('utsuro', '……来吧，白夜叉。我在这片屋顶的尽头等你。', { actor: ut, expr: 'smile' });
    crowBurst(S, ut.x, 142);
    S.sfx('crow', 0.7); S.sfx('whoosh', 0.5);
    await S.animate(0.4, (u) => { ut.alpha = 1 - u; });
    S.remove(ut);
    S.unpose(p);
    S.letterbox(false);
    S.camera(null);
    S.hint('沿着屋顶往右走——一路上会有同伴赶来', 6);
  }

  // ================================================================ 打完以后留在屋顶上的人（可以聊天）
  const TALK = {
    hijikata: [['hijikata', '……万事屋。今晚的账，等天亮了再跟你算。', 'smoke']],
    kondo: [['kondo', '阿妙小姐也在这片屋顶上吧！？我得赶紧去保护她！', 'shout'], ['gintoki', '……她会先把你踢下屋顶的。']],
    okita: [['okita', '旦那，我在帮土方先生找个光荣战死的好地方。', 'smug']],
    katsura: [['gintoki', '……假发，你怎么也来了。'], ['katsura', '不是假发，是桂！……江户有难，攘夷志士岂能袖手旁观。', 'shout']],
    eliz: [[null, '伊丽莎白举起了牌子：『银时先生，加油』']],
    otae: [['otae', '银桑，打完了记得来道场吃煎蛋哦。', 'smile'], ['gintoki', '……那我还是死在这里比较好。']],
    tsukuyo: [['tsukuyo', '吉原的女人，可不会只躲在地底下。']],
    otose: [['otose', '……房租的事，等天亮了再说。活着回来，臭小子。', 'smoke']],
    catherine: [['catherine', '天人的船这么多，随便偷一艘就发财了！']],
    tama: [['tama', '银时先生，拖把的扫射模式已经充能完毕。']],
    hasegawa: [['hasegawa', '我、我也来了……好像谁都没注意到……', 'cry'], ['gintoki', '……注意到了。纸箱很显眼。']],
    kagura: [['kagura', '银酱！打完了要请我吃醋昆布阿鲁！', 'happy']],
    kamui: [['kamui', '……那个叫虚的家伙，好像很强呢。让给我吧？', 'smile'], ['gintoki', '……不行。']],
    umibozu: [['umibozu', '……我是来看女儿的。顺便收拾几个天人。']],
    shinpachi: [['shinpachi', '银时先生……这一次，我们也会一起回家的吧。'], ['gintoki', '……废话。']],
    sadaharu: [['sadaharu', '汪！']],
  };
  function talkable(S, id, key, label) {
    const a = S.actor(id);
    if (!a) return;
    a.label = label;
    a.talk = async (S, me) => {
      for (const [who, text, expr] of TALK[key]) await S.say(who, text, who && who !== 'gintoki' ? { actor: me, expr } : { expr });
    };
  }

  // ================================================================ 第一段：真选组 · 攘夷志士
  async function segment1(S) {
    G.ui.hints = [];
    const p = S.player;
    const cx = frameCam(S, p.x - 56);
    p.x = cx + 56; p.y = FY; p.facing = 1;
    S.pose(p, 'ready');
    const cb = cutBg(S);
    // ① 真选组：诚字旗，土方拔刀、近藤、冲田扛着火箭筒
    cutTo(S, cb, { label: 0, tint: [30, 40, 100], lines: [130, 150, 230], z: [1.7, 1.82, 194, 134], hold: 1.4 });
    const flag = makotoFlag(S, cx + 126);
    const ssg = await Promise.all([castIn(S, 'hijikata', 164, 'draw', 0.10), castIn(S, 'kondo', 194, 'ready', 0.14), castIn(S, 'okita', 228, 'bazooka', 0.18, { freeze: 1 })]);
    await S.wait(0.3);
    await S.say('kondo', '真选组，参上！江户的天空，由我们来守！', { actor: 'kondo', expr: 'shout' });
    // ② 攘夷志士：伊丽莎白军团举牌，桂落下来
    hide(ssg); flag.hidden = true;
    cutTo(S, cb, { label: 1, tint: [30, 60, 150], lines: [150, 190, 255], z: [1.5, 1.6, 196, 128], lcy: 128, hold: 1.4 });
    await Promise.all([
      castIn(S, 'elizabeth', 100, 'elizabeth_sign_桂先生', null, { id: 'eliz0', delay: 0.04 }),
      castIn(S, 'elizabeth', 146, 'elizabeth_sign_攘夷', null, { id: 'eliz1', delay: 0.09 }),
      castIn(S, 'elizabeth', 234, 'elizabeth_sign_天诛', null, { id: 'eliz2', delay: 0.14 }),
      castIn(S, 'elizabeth', 274, 'elizabeth_sign_天诛', null, { id: 'eliz3', delay: 0.19 }),
      castIn(S, 'katsura', 197, 'ready', 0.12)]);
    await S.wait(0.3);
    await S.say('katsura', '江户的危机，就是攘夷志士的危机！', { actor: 'katsura', expr: 'shout' });
    // 拉开：大家摆好
    S.flash(0.08, 0.7);
    cb.tint = null; cb.lines = null;
    S.zoom(1, null, null, 0);
    flag.hidden = false;
    arrange(S, [['okita', 30, FY + 6, 1, 'bazooka'], ['hijikata', 96, FY + 2, 1, 'draw'], ['kondo', 128, FY + 8, 1, 'ready'], ['katsura', 300, FY + 4, -1, 'ready'],
      ['eliz0', 198, FY - 6, 1, 'elizabeth_sign_桂先生'], ['eliz1', 232, FY - 6, -1, 'elizabeth_sign_攘夷'], ['eliz2', 334, FY - 7, -1, 'elizabeth_sign_天诛'],
      ['eliz3', 362, FY - 6, -1, 'elizabeth_sign_天诛']]);
    await S.say('okita', '哦，假发也来了。土方先生，顺便逮捕吗？', { actor: 'okita', expr: 'smug' });
    await S.say('hijikata', '……今晚先算了。先把天上掉下来的这群收拾掉。', { actor: 'hijikata', expr: 'smoke' });
    S.unprop(cb.prop);
    S.unpose(p);
    S.hint('和大家一起，把奈落和春雨打下屋顶！', 5);
    await S.fight({
      arena: [cx, cx + G.W], allies: ['hijikata', 'kondo', 'okita', 'katsura'], allyHp: 110, music: 'battle',
      waves: [foes('s1a', ['naraku', 'naraku', 'harusame', 'naraku'], 30), foes('s1b', ['naraku', 'harusame', 'naraku', 'naraku', 'harusame'], 32)],
      onWave: darkNaraku, after: 'epic',
    });
    regroup(S, cx, [['okita', 36, FY + 6, 1], ['hijikata', 92, FY + 2, 1], ['kondo', 140, FY + 8, 1], ['katsura', 300, FY + 4, -1]]);
    talkable(S, 'hijikata', 'hijikata', '土方'); talkable(S, 'kondo', 'kondo', '近藤'); talkable(S, 'okita', 'okita', '冲田');
    talkable(S, 'katsura', 'katsura', '桂'); talkable(S, 'eliz1', 'eliz', '伊丽莎白');
    S.camera(null);
    F().seg1 = true;
    S.hint('可以和大家说说话，然后继续往右', 5);
  }

  // ================================================================ 第二段：最强女子 · 登势酒馆 · MADAO
  async function segment2(S) {
    G.ui.hints = [];
    const p = S.player;
    const cx = frameCam(S, p.x - 56);
    p.x = cx + 56; p.y = FY; p.facing = 1;
    S.pose(p, 'ready');
    const cb = cutBg(S);
    // ③ 最强女子：阿妙（黑化的笑）、月咏甩苦无
    cutTo(S, cb, { label: 2, tint: [120, 30, 100], lines: [255, 160, 220], z: [1.75, 1.85, 190, 134], hold: 1.4 });
    const women = await Promise.all([castIn(S, 'otae', 164, 'otae_ready_dark', 0.10), castIn(S, 'tsukuyo', 214, 'throw_kunai', 0.14)]);
    await S.wait(0.3);
    await S.say('otae', '敢在江户撒野的家伙……一个都别想走哦～', { actor: 'otae', expr: 'smile' });
    // ④ 登势酒馆：凯瑟琳指着、登势抽烟、小玉拖把扫射
    hide(women);
    cutTo(S, cb, { label: 3, tint: [150, 90, 30], lines: [255, 214, 150], z: [1.45, 1.8, 194, 134], hold: 1.2 });
    const otose = await Promise.all([castIn(S, 'catherine', 160, 'point', null, { delay: 0.1 }), castIn(S, 'otose', 193, 'smoke', null), castIn(S, 'tama', 227, 'mop_shoot', null)]);
    await S.wait(0.5);
    await S.say('otose', '我们店的房客，可不能让外人欺负了。', { actor: 'otose', expr: 'smoke' });
    await S.say('catherine', '欠的房租还没还呢！别想死了一笔勾销！', { actor: 'catherine' });
    // ⑤ MADAO：整个画面灰掉，纸箱里的长谷川，没人理他，只有乌鸦「阿呆～」
    hide(otose);
    S.filter('grayscale(0.55)');
    cutTo(S, cb, { label: 4, tint: [60, 60, 70], lines: null, z: [1.8, 1.95, 194, 136], hold: 2.1 });
    const hs = await castIn(S, 'hasegawa', 194, 'box', null);
    const P = PR();
    S.wait(0.62).then(() => S.sfx('crow', 0.7));
    S.wait(0.95).then(() => { if (!hs.remove) S.pose(hs, 'hasegawa_box_cry'); });
    overlay((g, u) => {
      sparkle(g, 186, 104, u - 0.14, 6);
      if (u > 0.22) g.drawImage(im('bubble_madao'), P.bubble_madao.x, P.bubble_madao.y);
      const ck = seg(u, 0.5, 2.0);
      if (ck > 0 && ck < 1) {
        const x = G.lerp(G.W + 10, -40, ck), y = 40 + Math.sin(u * Math.PI * 4) * 3;
        drawCrow(g, P[`crow_s3_${Math.floor(u * 10) % 2}`], x, y, true);
        if (u > 0.62 && u < 1.28) {
          const w = P['sfx_阿呆～'], k = (u - 0.62) / 0.66;
          g.globalAlpha = k > 0.75 ? (1 - k) / 0.25 : 1;
          g.drawImage(G.image(w.image), Math.round(x + 12 - w.w / 2), Math.round(y - 12 - w.h / 2));
          g.globalAlpha = 1;
        }
      }
      if (u > 0.95) g.drawImage(im('sweat_drop'), 218, Math.round(G.lerp(90, 100, easeOut(seg(u, 0.95, 2.0)))));
    }, 2.2, 2);
    S.wait(1.1).then(() => mark('ch13_madao'));
    await S.wait(2.2);
    S.filter(null);
    await S.say('gintoki', '……MADAO，你还是回纸箱里待着吧。', { expr: 'gloom' });
    // 拉开
    S.flash(0.08, 0.7);
    cb.tint = null;
    S.zoom(1, null, null, 0);
    arrange(S, [['otae', 100, FY + 4, 1, 'otae_ready_dark'], ['tsukuyo', 132, FY, 1], ['catherine', 250, FY + 6, -1], ['tama', 286, FY + 2, -1, 'mop'],
      ['otose', 330, FY - 6, -1, 'smoke'], ['hasegawa', 360, FY - 7, -1, 'box']]);
    S.unprop(cb.prop);
    S.unpose(p);
    S.hint('最强女子和登势酒馆一起上！', 4);
    await S.fight({
      arena: [cx, cx + G.W], allies: ['otae', 'tsukuyo', 'catherine', 'tama'], allyHp: 110, music: 'battle',
      waves: [foes('s2a', ['harusame', 'naraku', 'amanto_pig', 'naraku'], 32), foes('s2b', ['naraku', 'amanto_cat', 'naraku', 'harusame', 'naraku'], 34)],
      onWave: darkNaraku, after: 'epic',
    });
    regroup(S, cx, [['otae', 96, FY + 4, 1], ['tsukuyo', 140, FY, 1], ['catherine', 246, FY + 6, -1], ['tama', 290, FY + 2, -1]]);
    talkable(S, 'otae', 'otae', '阿妙'); talkable(S, 'tsukuyo', 'tsukuyo', '月咏'); talkable(S, 'otose', 'otose', '登势');
    talkable(S, 'catherine', 'catherine', '凯瑟琳'); talkable(S, 'tama', 'tama', '小玉'); talkable(S, 'hasegawa', 'hasegawa', '纸箱');
    S.camera(null);
    F().seg2 = true;
    S.hint('继续往右——还有人在赶来', 5);
  }

  // ================================================================ 第三段：快援队 · 夜兔一族 · 万事屋 →「全江户，集结！」
  function kaienShip(S, cx) {      // 快援队的船从左边飞进来，坂本在甲板上笑
    const st = G.world.stage, ks = PR().kaien_ship, sa = G.atlas('sakamoto'), t0 = st.t, sh = { leave: null };
    sh.prop = S.prop({ type: 'custom', x: 0, y: 0, depth: -8990, draw: (g, x, y, t) => {
      const u = t - t0;
      let sx = G.lerp(-80, 214, easeOut(seg(u, 0, 0.42)));
      if (sh.leave != null) sx += easeIn(seg(t, sh.leave, sh.leave + 1.8)) * 560;
      const scx = cx + sx - Math.round(st.camX), sy = 92 + 2 * Math.sin(u * Math.PI * 1.6);
      if (u < 0.42) {          // 横向的速度线
        const rnd = G.prng(7);
        g.fillStyle = 'rgba(255,220,200,0.55)';
        for (let i = 0; i < 10; i++) { const ly = 60 + rnd() * 70, len = 20 + rnd() * 30; g.fillRect(Math.round(G.mod(rnd() * G.W - t * 700, G.W + 60) - 30), Math.round(ly), Math.round(len), 1); }
      }
      const img = G.image(ks.image);
      if (!G.ready(img)) return;
      const x0 = Math.round(scx - ks.w / 2), y0 = Math.round(sy - ks.h / 2), fl = 4 + 2 * (Math.floor(t * 20) % 3);
      px(g, x0 - fl, y0 + 46, 'rgb(255,150,60)', fl, 5); px(g, x0 - (fl >> 1), y0 + 47, 'rgb(255,236,150)', fl >> 1, 3);
      g.drawImage(img, x0, y0);
      const an = sa.anim('laugh');
      sa.draw(g, 'laugh', Math.floor(t * an.fps) % an.frames, x0 + ks.deck_feet[0] - 4, y0 + ks.deck_feet[1]);
    } });
    return sh;
  }
  function yatoImpact(S, wx) {     // 夜兔三人落地：冲击波、碎屑、震屏
    const st = G.world.stage, t0 = st.t;
    const ring = S.prop({ type: 'custom', x: 0, y: 0, depth: FY - 1, draw: (g, x, y, t) => {
      const r = (t - t0) * 260;
      if (r >= 150) return;
      g.strokeStyle = 'rgb(255,230,190)'; g.lineWidth = 2;
      g.beginPath(); g.ellipse(wx - Math.round(st.camX), FY, r, r * 0.18, 0, 0, Math.PI * 2); g.stroke();
    } });
    G.fx.debris(wx, FY - 2, ['#786e82', '#50465a'], 18, [40, 110], 260, 0.5);
    S.shake(3, 0.3); S.sfx('impact', 0.8); S.sfx('land', 0.9);
    G.world.ticks.push(() => { if (G.world.stage !== st || st.t - t0 > 0.6) { S.unprop(ring); return true; } return false; });
  }
  // 原片 W：两道屋脊的大合影。后排（屋脊在 118，压暗）+ 前排（脚点 166），大字砸下来的时候大家一起跳一下
  const W_BACK = [['elizabeth', 26, 1, 'elizabeth_sign_天诛'], ['hasegawa', 54, 1, 'idle'], ['otose', 82, 1, 'smoke'], ['catherine', 108, 1, 'idle'],
    ['tama', 134, 1, 'idle'], ['kamui', 250, -1, 'ready'], ['umibozu', 278, -1, 'idle'], ['sakamoto', 306, -1, 'laugh'],
    ['elizabeth', 330, 1, 'elizabeth_sign_攘夷'], ['elizabeth', 360, 1, 'elizabeth_sign_天诛']];
  const W_FRONT = [['okita', 34, 1, 'bazooka', { p: 0.2 }], ['hijikata', 62, 1, 'ready'], ['kondo', 90, 1, 'ready'], ['katsura', 118, 1, 'ready'],
    ['shinpachi', 150, 1, 'ready'], ['gintoki', 192, 1, 'ready'], ['kagura', 230, -1, 'umbrella_open'], ['sadaharu', 270, -1, 'idle'],
    ['otae', 312, -1, 'ready'], ['tsukuyo', 346, -1, 'arms_crossed']];
  async function rally(S) {
    const st = G.world.stage, cx = st.camX, SL = 0.4;
    const shown = st.actors.filter((a) => a.visible);
    hide(shown);
    const Ls = G.D.bg.ch13_night.layers, roofL = Ls[Ls.length - 1];
    const back = { color: 'rgb(34,26,64)', k: 0.28 }, t0 = st.t;
    S.zoom(1, null, null, 0);
    S.flash(0.1, 0.9);
    S.sfx('whoosh', 0.7);
    const Wp = S.prop({ type: 'custom', x: 0, y: 0, depth: -9100, draw: (g, x, y, t) => {
      const u = t - t0, camX = Math.round(st.camX);
      st.bg.layer(g, Object.assign({}, roofL, { k: 0.8, y: 118 - 30 }), camX, t, st);
      W_BACK.forEach(([cid, sx, f, anim], i) => {
        const hop = Math.round(3 * Math.sin(Math.PI * seg(u, SL + 0.08 + i * 0.025, SL + 0.3 + i * 0.025)));
        dropDraw(g, cid, anim, sx, 118, u, 0.08 + (i % 5) * 0.05, { facing: f, h0: 60, fall: 0.1, hop, tint: back, ph: i * 0.17 });
      });
      st.bg.layer(g, Object.assign({}, roofL, { y: 166 - 30 }), camX, t, st);
      W_FRONT.forEach(([cid, sx, f, anim, o], i) => {
        const tl = 0.1 + Math.abs(i - 5) * 0.045, ts = SL + 0.05 + Math.abs(i - 5) * 0.03;
        const hop = Math.round(4 * Math.sin(Math.PI * seg(u, ts, ts + 0.24)));
        dropDraw(g, cid, anim, sx, 166, u, tl, Object.assign({ facing: f, h0: 70, fall: 0.1, hop, ph: i * 0.13 }, o));
      });
    } });
    W_FRONT.forEach(([cid, sx], i) => S.wait(0.1 + Math.abs(i - 5) * 0.045).then(() => G.fx.dust(cx + sx, 166, 4)));
    await S.wait(SL);
    // 「全江户，集结！」：大字 2.4 倍砸下来、抖半秒、一圈光环扩出去
    const sl = PR().slam_quanjianghu;
    overlay((g, u) => {
      const img = G.image(sl.image);
      if (!G.ready(img)) return;
      const s = 1 + 1.4 * (1 - seg(u, 0, 0.12)), j = u < 0.5 ? (Math.floor(u * 30) % 2 ? 1 : -1) : 0;
      const w = Math.round(sl.w * s), h = Math.round(sl.h * s);
      g.globalAlpha = Math.min(1, u / 0.06);
      g.drawImage(img, Math.round(sl.centre[0] - w / 2) + j, Math.round(sl.centre[1] - h / 2), w, h);
      g.globalAlpha = 1;
      const r = (u - 0.1) * 420;
      if (r > 0 && r < 420) { g.strokeStyle = `rgba(255,240,200,${(1 - r / 420).toFixed(2)})`; g.lineWidth = 2; g.beginPath(); g.ellipse(192, 36, r, r * 0.45, 0, 0, Math.PI * 2); g.stroke(); }
    }, 2.3, 5);
    S.sfx('title_hit', 0.9); S.sfx('cheer', 0.7); S.sfx('crowd', 0.5);
    S.flash(0.15, 0.6); S.shake(4, 0.45);
    await S.wait(0.3);
    mark('ch13_rally');
    S.zoom(1.16, cx + 192, 128, 1.6);
    await S.wait(1.9);
    S.flash(0.1, 0.8);
    S.unprop(Wp);
    S.zoom(1, null, null, 0);
    shown.forEach((a) => { a.visible = true; });
  }
  async function segment3(S) {
    G.ui.hints = [];
    let p = S.player;
    const st = G.world.stage;
    const cx = frameCam(S, p.x - 56);
    p.x = cx + 56; p.y = FY; p.facing = 1;
    S.pose(p, 'ready');
    const cb = cutBg(S);
    // ⑥ 快援队
    cutTo(S, cb, { label: 5, tint: [130, 30, 30], lines: [255, 150, 130], z: [1.3, 1.3, 214, 108], lcy: 110, hold: 1.2 });
    const ship = kaienShip(S, cx);
    S.sfx('engine_hum', 0.6);
    await S.wait(0.8);
    await S.say('sakamoto', '啊哈哈哈！金时！快援队送货上门了！', { name: '坂本', expr: 'happy' });
    await S.say('gintoki', '……是银时！', { expr: 'angry' });
    // ⑦ 夜兔一族：三个人从更高的地方砸下来
    ship.prop.hidden = true;
    cutTo(S, cb, { label: 6, tint: [160, 56, 30], lines: [255, 180, 120], z: [1.7, 1.8, 194, 132], hold: 1.4 });
    S.wait(0.14).then(() => yatoImpact(S, cx + 194));
    const yato = await Promise.all([castIn(S, 'kagura', 160, 'umbrella_shoot', 0.14, { h0: 110 }), castIn(S, 'kamui', 194, 'ready', 0.14, { h0: 110 }),
      castIn(S, 'umibozu', 228, 'umbrella_open', 0.14, { h0: 110 })]);
    await S.wait(0.3);
    await S.say('kagura', '夜兔一族，全家出动阿鲁！', { actor: 'kagura', expr: 'happy' });
    await S.say('umibozu', '……别把老爸算成凑数的。', { actor: 'umibozu' });
    // ⑧ 万事屋：定春驮着新八冲进来
    hide(yato);
    cutTo(S, cb, { label: 7, tint: [60, 90, 160], lines: [200, 230, 255], z: [1.55, 1.65, 190, 128], lcy: 128, hold: 1.4 });
    const sd = gear(S.spawn('sadaharu', cx + 30, FY, { id: 'sadaharu', facing: 1 }));
    const sp = gear(S.spawn('shinpachi', cx + 24, FY, { id: 'shinpachi', facing: 1 }));
    sp.shadow = false; sp.z = 30;
    S.pose(sp, 'ready');
    let riding = true;
    G.world.ticks.push(() => { if (!riding || sp.remove || sd.remove) return true; sp.x = sd.x - 6; sp.y = sd.y; sp.z = sd.z + 30; return false; });
    S.sfx('run', 0.5);
    await S.arc(sd, cx + 196, FY, 36, 0.28, { anim: 'run' });
    S.pose(sd, 'land', { restart: true });
    G.fx.dust(sd.x - 5, FY, 4); G.fx.dust(sd.x + 5, FY, 4);
    S.sfx('land', 0.8);
    await S.wait(0.06);
    S.pose(sd, 'bark'); S.sfx('bark', 0.9);
    await S.wait(0.4);
    riding = false;
    await S.arc(sp, cx + 226, FY + 2, 14, 0.25, { anim: 'jump', z1: 0 });
    sp.shadow = true;
    S.pose(sp, 'ready');
    await S.say('shinpachi', '银时先生！万事屋，到齐了！', { actor: sp, expr: 'shout' });
    // 全江户，集结！
    S.unprop(cb.prop);
    await rally(S);
    ship.prop.hidden = false;
    ship.leave = st.t;
    S.sfx('engine_hum', 0.4);
    S.wait(2.0).then(() => S.unprop(ship.prop));
    arrange(S, [['kagura', 100, FY + 4, 1], ['shinpachi', 130, FY + 8, 1], ['kamui', 260, FY + 2, -1], ['umibozu', 300, FY + 6, -1], ['sadaharu', 350, FY - 6, -1]]);
    S.unpose(p);
    // 用谁来打（招式都一样：J / K / L）
    S.hint('这一战由谁来打？（招式都一样：J 攻击、K 跳、L 挡）', 6);
    const who = await S.choice(['银时', '神乐', '新八']);
    const pick = ['gintoki', 'kagura', 'shinpachi'][who];
    let allies = ['kagura', 'kamui', 'umibozu', 'shinpachi'];
    if (pick !== 'gintoki') {
      const other = S.actor(pick), ox = other.x, oy = other.y;
      S.remove(other);
      p = gear(S.setPlayer(pick, { x: ox, y: oy, facing: 1, name: NAMES[pick], hp: 100, speed: pick === 'kagura' ? 76 : 72, keep: 'gin' }));
      S.actor('gin').name = '银时';
      allies = allies.map((id) => (id === pick ? 'gin' : id));
      S.hint(`现在操控${NAMES[pick]}`, 3);
    }
    await S.fight({
      arena: [cx, cx + G.W], allies, allyHp: 120, music: 'battle',
      waves: [foes('s3a', ['naraku', 'harusame', 'naraku', 'amanto_pig', 'naraku'], 34), foes('s3b', ['naraku', 'naraku', 'amanto_cat', 'harusame', 'naraku', 'naraku'], 36)],
      onWave: darkNaraku, after: 'epic',
    });
    if (pick !== 'gintoki') {      // 换回银时（最后一战是他的）
      const gn = S.actor('gin');
      gear(S.setPlayer('gintoki', { x: gn.x, y: gn.y, facing: gn.facing, name: '银时', hp: 100, speed: 74, keep: pick }));
      S.remove(gn);
      const back = S.actor(pick);
      back.name = NAMES[pick];
      S.unpose(back);
      S.flash(0.08, 0.5);
    }
    regroup(S, cx, [['kagura', 96, FY + 4, 1], ['shinpachi', 140, FY + 8, 1], ['kamui', 262, FY + 2, -1], ['umibozu', 304, FY + 6, -1]]);
    talkable(S, 'kagura', 'kagura', '神乐'); talkable(S, 'kamui', 'kamui', '神威'); talkable(S, 'umibozu', 'umibozu', '星海坊主');
    talkable(S, 'shinpachi', 'shinpachi', '新八'); talkable(S, 'sadaharu', 'sadaharu', '定春');
    S.camera(null);
    F().seg3 = true;
    S.hint('虚就在屋顶的尽头', 5);
  }

  // ================================================================ 尽头：背靠背 → X 字斩 → 两个阶段的虚
  function moves() {
    const M = G.MOVES;
    if (M.U_SLASH) return;
    M.U_SLASH = Object.assign({}, M.E_SLASH, { anim: 'utsuro_attack_glow', dmg: 9 });
    M.U_THRUST = Object.assign({}, M.E_HEAVY, { anim: 'utsuro_thrust_glow', dmg: 14 });
  }
  function regenTick(S) {      // 虚一直在再生：血条慢慢回满，身上冒红色的光点
    const st = G.world.stage;
    G.world.ticks.push((dt) => {
      if (G.world.stage !== st || F().dawnDone) return true;
      const u = st.find('utsuro');
      if (u && u.team === 'enemy' && G.world.combat && u.hp < u.maxHp) {
        u.hp = Math.min(u.maxHp, u.hp + 7 * dt);
        if (Math.random() < dt * 4) G.fx.add({ kind: 'px', x: u.x + G.rand(-8, 8), y: u.y - G.rand(6, 40), vx: 0, vy: -24, color: Math.random() < 0.5 ? '#ff5a78' : '#8a2a4a', life: 0.5 });
      }
      return false;
    });
  }
  function xSlash(S, wx, wy, size = 16) {      // X 字斩：两道斜线 0.07 秒长出来（第二道晚 0.04 秒），0.38 秒内变细
    const st = G.world.stage, t0 = st.t;
    const pr = S.prop({ type: 'custom', x: 0, y: 0, depth: 9500, draw: (g, x, y, t) => {
      const u = t - t0;
      if (u > 0.4) return;
      const sx = wx - Math.round(st.camX), w = Math.max(1, Math.round(5 - 4 * seg(u, 0, 0.38)));
      const line = (k, dir) => {
        if (k <= 0) return;
        const x0 = sx - size * dir, y0 = wy - size, x1 = x0 + 2 * size * dir * k, y1 = y0 + 2 * size * k;
        g.lineCap = 'butt';
        g.strokeStyle = INK; g.lineWidth = w + 2; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
        g.strokeStyle = '#fff'; g.lineWidth = w; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
      };
      line(seg(u, 0, 0.07), 1); line(seg(u, 0.04, 0.11), -1);
    } });
    G.world.ticks.push(() => { if (G.world.stage !== st || st.t - t0 > 0.45) { S.unprop(pr); return true; } return false; });
  }
  async function finale(S) {
    G.ui.hints = [];
    const p = S.player, st = G.world.stage;
    moves();
    for (const a of st.actors) if (a !== p) a.remove = true;      // 前面几段的人留在后面的屋顶上（尽头只剩银时）
    const cx = frameCam(S, p.x - 181);
    S.flash(0.1, 0.7); S.sfx('whoosh', 0.5);
    G.ui.letterboxTarget = 12;
    p.x = cx + 181; p.y = FY; p.facing = -1;
    S.pose(p, 'ready');
    weather(S, (g, t) => embers(g, t, 30, 5, 40));
    // E1：四个奈落围上来，高杉落在背后
    const nk = [[88, 1], [116, 1], [268, -1], [296, -1]].map(([x, f], i) => {
      const a = gear(S.spawn('naraku', cx + x, FY + [0, 4, 4, 0][i], { id: `nk${i}`, name: '奈落', facing: f }));
      a.tint = { color: 'rgb(16,10,26)', k: 0.45 };
      S.pose(a, 'ready');
      return a;
    });
    S.zoom(1.6, cx + 192, 142, 0);
    await S.wait(0.5);
    const tk = gear(S.spawn('takasugi', cx + 204, FY, { id: 'takasugi', name: '高杉', facing: 1 }));
    tk.z = 120;
    S.sfx('whoosh', 0.7);
    await S.arc(tk, tk.x, tk.y, 0, 0.2, { anim: 'jump', z1: 0 });
    G.fx.dust(tk.x - 5, tk.y, 3); G.fx.dust(tk.x + 5, tk.y, 3);
    S.sfx('land', 0.8);
    S.pose(tk, 'ready');
    S.sfx('wind', 0.4);
    await S.say('takasugi', '别拖后腿啊，银时。', { actor: tk, expr: 'smug' });
    await S.say('gintoki', '……这句台词，该我说才对。', { expr: 'smug' });
    S.zoom(1.85, cx + 192, 142, 0.9);
    await S.animate(0.9, (u, dt) => { nk.forEach((a, i) => { a.x += (i < 2 ? 1 : -1) * 9 * dt; }); });
    S.zoom(1, null, null, 0.25);
    G.ui.letterboxTarget = 0;
    S.unpose(p); S.unpose(tk);
    p.facing = 1;
    S.hint('背靠背！和高杉一起，把围上来的奈落打下去', 5);
    await S.fight({
      arena: [cx, cx + G.W], allies: ['takasugi'], allyHp: 150, music: 'battle',
      waves: [nk.map((a) => ({ actor: a.id, cid: 'naraku', name: '奈落', hp: 30 })), foes('nkb', ['naraku', 'naraku', 'naraku', 'naraku', 'naraku'], 32)],
      onWave: darkNaraku, after: null,
    });
    // E2a：虚现身 → 两人一起冲上去 X 字斩 → 虚笑着再生
    S.music('epic', 0.6);
    G.ui.letterboxTarget = 12;
    const ut = gear(S.spawn('utsuro', cx + 252, FY, { id: 'utsuro', name: '虚', facing: -1 }));
    ut.alpha = 0;
    S.pose(ut, 'regen');
    crowBurst(S, cx + 252, 142);
    S.sfx('aura', 0.8); S.sfx('crow', 0.7);
    p.x = cx + 118; p.y = FY; p.facing = 1; tk.x = cx + 90; tk.y = FY + 2; tk.facing = 1;
    S.pose(p, 'ready'); S.pose(tk, 'ready');
    S.zoom(1.6, cx + 210, 142, 0.3);
    await S.animate(0.6, (u) => { ut.alpha = u; ut.tint = { color: 'rgb(10,4,16)', k: 1 - u }; });
    ut.tint = null;
    S.pose(ut, 'utsuro_idle_smile');
    await S.say('utsuro', '……松阳的学生们。来吧。', { actor: ut, expr: 'smile' });
    S.sfx('dash', 0.9);
    S.pose(p, 'run'); S.pose(tk, 'run');
    await S.animate(0.24, (u) => { p.x = G.lerp(cx + 118, cx + 224, easeOut(u / 0.9)); tk.x = G.lerp(cx + 90, cx + 204, easeOut(u)); });
    S.pose(p, 'attack', { restart: true }); S.pose(tk, 'slash_up', { restart: true });
    xSlash(S, cx + 252, 148);
    G.fx.spark(cx + 252, 148, '#ffffff', 8); G.fx.spark(cx + 252, 148, '#ff7882', 6);
    S.sfx('slash_big', 1.0); S.sfx('impact', 0.8);
    S.shake(4, 0.3);
    S.pose(ut, 'hit', { restart: true });
    ut.tint = { color: 'rgb(255,60,80)', k: 0.7 };
    await S.wait(0.12);
    ut.tint = null;
    S.pose(ut, 'regen');
    await S.wait(0.7);
    S.pose(ut, 'utsuro_idle_smile');
    await S.say('utsuro', '……没用的。我不会死。', { actor: ut, expr: 'smile' });
    await S.say('takasugi', '……那就砍到你不想再站起来为止。', { actor: tk, expr: 'angry' });
    S.zoom(1, null, null, 0.25);
    G.ui.letterboxTarget = 0;
    S.unpose(p); S.unpose(tk);
    // 第一阶段：和高杉一起压制
    regenTick(S);
    S.hint('虚会不断再生——和高杉一起压制住它', 5);
    await S.fight({
      arena: [cx, cx + G.W], allies: ['takasugi'], allyHp: 160, music: null,
      waves: [[{ actor: 'utsuro', cid: 'utsuro', name: '虚', hp: 240, boss: true, speed: 58, range: 30, minHp: 60, idle: 'utsuro_idle_smile', moves: ['U_SLASH', 'U_SLASH', 'U_THRUST'] }]],
      onWave: (S, wi, sp) => sp.forEach(gear),
      endWhen: () => { const u = S.actor('utsuro'); return G.world.fightT > 24 || !!(u && u.team === 'enemy' && u.hp <= 130); },
      after: null,
    });
    await takasugiFalls(S, cx);
    await rise(S, cx);
    // 第二阶段：撑到天亮
    G.world.ticks.push(() => {
      if (G.world.stage !== st || F().dawnDone) return true;
      if (G.world.combat) {
        const k = seg(G.world.fightT, 0, 30);
        Object.assign(st.state, { dawn: G.lerp(0.35, 0.92, k), armada: G.lerp(1, 0.55, k), sunY: G.lerp(166, 152, k), rays: Math.round(12 * k) });
        if (G.world.fightT > 20) mark('ch13_dawn_fight');
      }
      return false;
    });
    S.hint('撑到天亮！虚打不死——天一亮，就是反击的时候', 6);
    await S.fight({
      arena: [cx, cx + G.W], music: null,
      waves: [[{ actor: 'utsuro', cid: 'utsuro', name: '虚', hp: 260, boss: true, speed: 60, range: 30, minHp: 80, idle: 'utsuro_idle_smile', moves: ['U_SLASH', 'U_THRUST', 'U_SLASH'] }]],
      onWave: (S, wi, sp) => sp.forEach(gear),
      timer: { label: '天亮还有 ', until: 30 },
      reinforce: { every: 6, max: 2, make: (i) => (i < 8 ? { cid: 'naraku', id: `nd${i}`, name: '奈落', hp: 26 } : null) },
      endWhen: () => G.world.fightT >= 30,
      after: null,
    });
    await finalStrike(S, cx);
  }

  // ================================================================ 高杉
  async function takasugiFalls(S, cx) {
    const p = S.player, st = G.world.stage, tk = S.actor('takasugi'), ut = S.actor('utsuro');
    ut.team = 'npc'; tk.team = 'npc'; G.ui.boss = null; G.ui.hud = false;
    for (const e of st.actors) if (e.team === 'enemy') e.remove = true;
    G.ui.letterboxTarget = 12;
    S.flash(0.08, 0.6);
    // E2b：银时砍上去，虚的突刺从正面来；高杉从后面追上来，把银时推开，自己顶上去
    p.x = cx + 214; p.y = FY; p.facing = 1;
    S.pose(p, 'attack', { restart: true });
    tk.x = cx + 192; tk.y = FY + 1; tk.facing = 1; tk.visible = true;
    S.pose(tk, 'run');
    ut.x = cx + 280; ut.y = FY; ut.facing = -1; ut.tint = null; ut.alpha = 1; ut.visible = true;
    S.pose(ut, 'utsuro_thrust_glow', { restart: true });
    S.zoom(1.9, cx + 226, 142, 0); S.zoom(2.2, cx + 226, 142, 0.45);
    S.sfx('dash', 0.8);
    let shoved = false, braced = false;
    await S.animate(0.45, (u) => {
      const s = u * 0.45;
      ut.x = G.lerp(cx + 280, cx + 252, easeIn(seg(s, 0.16, 0.41)));
      tk.x = G.lerp(cx + 192, cx + 226, easeOut(seg(s, 0.12, 0.39)));
      if (s > 0.2) {
        p.x = G.lerp(cx + 214, cx + 188, easeOut(seg(s, 0.2, 0.45)));
        if (!shoved) { shoved = true; S.pose(p, 'gintoki_hit_shock', { restart: true }); S.sfx('punch', 0.6); }
      }
      if (s > 0.33 && !braced) { braced = true; S.pose(tk, 'takasugi_guard_brace'); }
    });
    // E2c：冲击帧（红底黑剪影，刀穿过去）
    const imp = overlay((g) => g.drawImage(im('impact_e2c'), 0, 0), null, -10);
    S.sfx('impact', 1.0); S.sfx('stab', 0.9);
    S.shake(3, 0.2);
    await S.wait(0.14);
    unoverlay(imp);
    // 灰掉、偏红，高杉踉跄，血滴飞出去
    S.filter('grayscale(0.7) sepia(0.4) hue-rotate(-28deg) saturate(1.8)');
    S.flash(0.17, 0.8);
    S.pose(tk, 'hit', { restart: true });
    S.pose(ut, 'utsuro_thrust_glow', { freeze: 4 });
    for (let i = 0; i < 7; i++) G.fx.add({ kind: 'px', x: cx + 222, y: 150, vx: G.rand(-40, 10), vy: G.rand(-40, -10), color: i % 2 ? '#c81e32' : '#961428', life: 0.5, g: 120 });
    S.zoom(2.3, cx + 220, 144, 0); S.zoom(2.4, cx + 220, 144, 0.3);
    await S.animate(0.3, (u) => { tk.x = cx + 226 - u * 3; });
    // 银时的大特写「高杉——！！」
    S.filter(null);
    S.music('sad', 0.5);
    S.sfx('shock', 0.9);
    const cu = overlay((g, u) => {
      const k = 1 + 0.08 * seg(u, 0, 0.45), j = Math.round(Math.sin(u * 14 * Math.PI * 2));
      g.drawImage(im('closeup_gintoki_shout'), Math.round(140 - 140 * k) + j, Math.round(110 - 110 * k), Math.round(G.W * k), Math.round(G.H * k));
    }, null, -10);
    mark('ch13_closeup');
    await S.wait(1.2);
    unoverlay(cu);
    // F：跪在地上，抱着高杉
    G.ui.letterboxTarget = 22;
    ut.visible = false;
    const gx = cx + 206;
    p.x = gx; p.y = FY; p.facing = -1;
    S.pose(p, 'gintoki_kneel_cradle');
    tk.x = gx - 6; tk.y = FY + 1; tk.facing = -1; tk.shadow = false;
    S.pose(tk, 'takasugi_cradled_raise', { freeze: 0 });
    const glowP = S.prop({ type: 'custom', x: 0, y: 0, depth: FY - 2, draw: (g) => {
      g.save(); g.globalCompositeOperation = 'lighter'; g.drawImage(im('glow_r34_0.35'), gx - 18 - 34 - Math.round(st.camX), 154 - 34); g.restore();
    } });
    const ashP = weather(S, (g, t) => ash(g, t, 50, 3));
    S.filter('grayscale(0.35)');
    S.zoom(2.6, gx - 18, 152, 0); S.zoom(2.8, gx - 18, 152, 2.6);
    S.sfx('wind', 0.4);
    await S.wait(0.4);
    S.pose(tk, 'takasugi_cradled_raise', { restart: true });
    await S.wait(0.4);
    await S.say('takasugi', '银时……剩下的，交给你了。', { actor: tk, expr: 'sad' });
    // FB：一闪而过的松下私塾
    await flashback(S);
    // FC：最后笑了一下，手垂下去
    S.zoom(3.1, gx - 14, 150, 0); S.zoom(3.35, gx - 14, 150, 1.8);
    S.pose(tk, 'takasugi_cradled_smile');
    await S.wait(0.8);
    S.pose(tk, 'takasugi_cradled_drop', { restart: true });
    S.pose(p, 'gintoki_kneel_cradle_shock');
    S.sfx('heartbeat', 0.7);
    await S.animate(0.25, (u) => S.filter(`grayscale(${(0.35 + 0.4 * u).toFixed(2)})`));
    await S.wait(0.35);
    S.pose(p, 'gintoki_kneel_cradle_bow');
    await S.wait(0.9);
    // F2：影子里的银时，一滴泪
    const f2 = overlay((g, u) => {
      g.drawImage(im('grad_f2'), 0, 0);
      ash(g, u, 40, 4, 'rgb(120,118,134)');
      g.save(); g.globalCompositeOperation = 'lighter'; g.drawImage(im('glow_r64_0.5'), 192 - 64, 96 - 64); g.restore();
      const b = PR().bust_gintoki_sad_shadow_x5, x0 = 192 - Math.floor(b.w / 2), y0 = 44 + (Math.floor(u * 2) % 2);
      g.drawImage(G.image(b.image), x0, y0);
      if (u > 0.08) { const ty = Math.floor(y0 + 65 + easeIn(seg(u, 0.1, 0.42)) * 34), ex = x0 + b.w - 29; px(g, ex, ty, 'rgb(150,210,255)', 3, 5); px(g, ex, ty, '#fff', 1, 2); }
    }, null, -10);
    S.wait(0.4).then(() => mark('ch13_tear'));
    await S.wait(1.5);
    unoverlay(f2);
    S.unprop(glowP); S.unprop(ashP);
    S.filter(null);
  }
  async function flashback(S) {    // 松下私塾：小高杉冲上来，小银时用木刀挡住「啪！」，小桂坐着看，老师在笑
    const st = G.world.stage, P = PR(), D = 1.6, clash = 0.3;
    const oc = Object.assign(document.createElement('canvas'), { width: G.W, height: G.H }), ox = oc.getContext('2d');
    ox.imageSmoothingEnabled = false;
    S.filter('sepia(0.9)');
    const fb = overlay((g, u) => {
      const t = st.t;
      ox.clearRect(0, 0, G.W, G.H);
      ox.drawImage(im('dojo_bg'), 0, 0);
      drawChar(ox, 'katsura_kid', 'sit', t, 116, 150, { facing: 1 });
      drawChar(ox, 'shouyou', 'smile', t, 266, 146, { facing: -1 });
      const k = easeOut(seg(u, 0, clash)), tx = G.lerp(140, 172, k), gx = G.lerp(236, 206, k);
      if (u < clash) {
        drawChar(ox, 'takasugi_kid', 'takasugi_kid_run_angry', t, tx, 152, { facing: 1 });
        drawChar(ox, 'gintoki_kid', 'gintoki_kid_idle_bokuto', t, gx, 152, { facing: -1 });
      } else {
        drawChar(ox, 'takasugi_kid', 'takasugi_kid_attack_shout', 0, tx, 152, { facing: 1, p: 0.45 });
        drawChar(ox, 'gintoki_kid', 'gintoki_kid_guard_bokuto', 0, gx, 152, { facing: -1 });
        const d = u - clash, rnd = G.prng(111);
        if (d < 0.4) for (let i = 0; i < 10; i++) { const a = rnd() * Math.PI * 2, v = 30 + rnd() * 50; px(ox, 189 + Math.cos(a) * v * d, 134 + Math.sin(a) * v * d + 45 * d * d, i % 2 ? 'rgb(255,250,220)' : 'rgb(230,200,140)'); }
      }
      sakura(ox, t, 12, 17, 22, 16);
      const z = G.lerp(1.62, 1.75, seg(u, 0, D)), w = G.W / z, h = G.H / z;
      const zx = G.clamp(190, w / 2, G.W - w / 2), zy = G.clamp(128, h / 2, G.H - h / 2);
      g.drawImage(oc, zx - w / 2, zy - h / 2, w, h, 0, 0, G.W, G.H);
      if (u >= clash && u < clash + 0.5) {
        const s = P['sfx_啪！'], kk = (u - clash) / 0.5, sc = kk < 0.15 ? 0.6 + (kk / 0.15) * 0.6 : 1.2 - Math.min(0.2, (kk - 0.15) * 0.6);
        g.drawImage(G.image(s.image), Math.round(146 - (s.w * sc) / 2), Math.round(74 - (s.h * sc) / 2), Math.round(s.w * sc), Math.round(s.h * sc));
      }
      vignette(g);
      const fl = Math.max(1 - u / 0.12, seg(u, D - 0.1, D)) * 0.9;
      if (fl > 0) { g.fillStyle = `rgba(255,248,230,${fl.toFixed(2)})`; g.fillRect(0, 0, G.W, G.H); }
    }, null, -10);
    S.sfx('twinkle', 0.45);
    S.wait(clash + 0.2).then(() => mark('ch13_flashback'));
    await S.wait(clash);
    S.sfx('clang', 0.7); S.sfx('punch', 0.5);
    await S.wait(D - clash);
    unoverlay(fb);
    S.filter('grayscale(0.35)');
  }
  // G1：放下高杉，站起来；G1b：眼神亮起来
  async function rise(S, cx) {
    const p = S.player, st = G.world.stage, tk = S.actor('takasugi'), ut = S.actor('utsuro');
    tk.x = cx + 151; tk.y = FY + 6; tk.facing = 1; tk.shadow = false;
    S.pose(tk, 'takasugi_lie_dead');
    p.x = cx + 190; p.y = FY; p.facing = 1;
    S.pose(p, 'kneel');
    ut.visible = true; ut.x = cx + 322; ut.y = FY; ut.facing = -1;
    S.pose(ut, 'regen');
    st.state.dawn = 0.2;
    S.zoom(1.4, cx + 232, 138, 0); S.zoom(1.5, cx + 232, 138, 3.0);
    S.flash(0.12, 0.5);
    const ashP = weather(S, (g, t) => ash(g, t, 30, 5, 'rgb(200,180,190)'));
    S.music('epic', 0.6);
    S.animate(3.0, (u) => { st.state.dawn = G.lerp(0.2, 0.35, u); });
    await S.wait(0.6);
    mark('ch13_rise');
    for (;;) {
      const ok = await S.mash({ label: '连按 J——站起来！', need: 14, time: 6, decay: 1.6 });
      if (ok) break;
      await S.say('gintoki', '……………………', { expr: 'sad' });
    }
    S.pose(p, 'gintoki_idle_sword_down_sad');
    S.sfx('whoosh', 0.5);
    await S.wait(0.7);
    // G1b：眼睛那一条
    let glare = false, gT = 0;
    const eye = overlay((g, u) => {
      g.drawImage(im('grad_g1b'), 0, 0);
      if (glare) softLines(g, u, 192, 108, [255, 120, 110], 0.6, 50, 40, 5);
      const h = PR()[glare ? 'head_gintoki_angry_x6' : 'head_gintoki_sad_shadow_x6'];
      g.drawImage(G.image(h.image), Math.round(h.centre[0] - h.w / 2), Math.round(h.centre[1] - h.h / 2));
      if (glare) { sparkle(g, 162, 104, u - gT, 10, 'rgb(255,230,230)'); sparkle(g, 224, 104, u - gT - 0.03, 10, 'rgb(255,230,230)'); }
      g.fillStyle = '#000'; g.fillRect(0, 0, G.W, 80); g.fillRect(0, 136, G.W, G.H - 136);
      px(g, 0, 80, 'rgb(140,30,40)', G.W, 1); px(g, 0, 135, 'rgb(140,30,40)', G.W, 1);
    }, null, -10);
    S.sfx('heartbeat', 0.8);
    await S.wait(0.5);
    glare = true; gT = G.time - eye.t0;
    S.sfx('shine', 0.9);
    S.flash(0.12, 0.6);
    S.wait(0.3).then(() => mark('ch13_glare'));
    await S.wait(1.0);
    unoverlay(eye);
    S.unprop(ashP);
    G.ui.letterboxTarget = 0;
    S.zoom(1, null, null, 0);
    S.unpose(p);
    p.facing = 1;
  }

  // ================================================================ 天亮：最后一斩 → 碎成光 → 松阳
  async function finalStrike(S, cx) {
    const p = S.player, st = G.world.stage, ut = S.actor('utsuro'), tk = S.actor('takasugi');
    for (const e of st.actors) if (e.team === 'enemy' && e !== ut) e.remove = true;
    ut.team = 'npc'; G.ui.boss = null; G.ui.hud = false;
    F().dawnDone = true;
    Object.assign(st.state, { dawn: 1, armada: 0.5, sunX: 292, sunY: 152, rays: 0 });
    S.flash(0.3, 0.8, '#fff4dc');
    G.ui.letterboxTarget = 22;
    if (tk) tk.visible = false;
    p.x = cx + 80; p.y = FY; p.facing = 1;
    S.pose(p, 'ready');
    ut.x = cx + 306; ut.y = FY; ut.facing = -1; ut.visible = true; ut.alpha = 1; ut.tint = null;
    S.pose(ut, 'utsuro_ready_glow');
    await S.say(null, '——天，亮了。');
    for (let n = 0; ; n++) {
      const ok = await S.timing({ label: '最后一斩！看准时机按 J', speed: 1.2, zone: [0.44, 0.58], tries: 2 });
      if (ok) break;
      S.shake(2, 0.2); S.sfx('clang', 0.6);
      await S.say('gintoki', n ? '……再来一次！' : '……还没完！', { expr: 'angry' });
    }
    // G2：冲刺、错身而过
    S.sfx('dash', 1.0);
    S.pose(p, 'run'); S.pose(ut, 'utsuro_run_glow');
    S.zoom(1.9, cx + 192, 146, 0.5);
    await S.animate(0.5, (u) => { const k = easeIn(u); p.x = G.lerp(cx + 80, cx + 214, k); ut.x = G.lerp(cx + 306, cx + 170, k); });
    S.zoom(1, null, null, 0);
    const imp = overlay((g) => g.drawImage(im('impact_g2'), 0, 0), null, -10);
    S.sfx('slash_big', 1.0); S.sfx('impact', 1.0);
    p.x = cx + 262; ut.visible = false;
    S.pose(p, 'attack', { freeze: 7 });
    await S.wait(0.1);
    unoverlay(imp);
    overlay((g, u) => {
      const wd = Math.floor(10 * (1 - seg(u, 0, 0.3))) + 1;
      g.lineCap = 'butt';
      g.strokeStyle = INK; g.lineWidth = wd + 4; g.beginPath(); g.moveTo(-10, 196); g.lineTo(G.W + 10, 64); g.stroke();
      g.strokeStyle = '#fff'; g.lineWidth = wd; g.beginPath(); g.moveTo(-10, 196); g.lineTo(G.W + 10, 64); g.stroke();
    }, 0.3, 4);
    S.flash(0.5, 0.9);
    S.shake(5, 0.35);
    await shatter(S, cx);
    await sunrise(S, cx);
  }
  // 碎成光：每一粒从身体上剥下来，往上飘，被吸向头顶上方那一点，颜色变成晨光
  function drawShatter(g, d, sx) {
    const rnd = G.prng(9), cols = [[40, 34, 52], [230, 230, 240], [90, 30, 50]];
    for (let i = 0; i < 150; i++) {
      const ox = (rnd() - 0.5) * 28, oy = -rnd() * 50;
      const delay = (1 + oy / 50) * 0.18 + rnd() * 0.35, vx = (rnd() - 0.5) * 32, vy = -(10 + rnd() * 24), life = 0.9 + rnd() * 0.9, big = rnd() < 0.35, ph = rnd() * 6;
      const dd = d - delay;
      if (dd < 0 || dd > life) continue;
      const pk = Math.pow(dd / 1.6, 2) * 0.6;
      let x = sx + ox + vx * dd + Math.sin(3 * dd + ph) * 3, y = FY + oy + vy * dd - 10 * dd * dd;
      x += (sx - x) * pk; y += (FY - 32 - y) * pk;
      const c0 = cols[i % 3], cm = Math.min(1, dd * 5);
      g.fillStyle = `rgba(${Math.round(G.lerp(c0[0], 255, cm))},${Math.round(G.lerp(c0[1], 244, cm))},${Math.round(G.lerp(c0[2], 210, cm))},${(1 - dd / life).toFixed(2)})`;
      g.fillRect(Math.round(x), Math.round(y), big ? 2 : 1, big ? 2 : 1);
    }
  }
  async function shatter(S, cx) {
    const p = S.player, st = G.world.stage, P = PR(), fr = P.utsuro_frozen, ux = cx + 122, t0 = st.t, SH = 0.8;
    S.animate(7.0, (u) => { st.state.sunY = G.lerp(152, 112, easeOut(u)); });
    S.animate(SH, (u) => { st.state.rays = Math.round(30 * seg(u, 0.3, 1)); });
    S.zoom(1.5, cx + 192, 142, 0); S.zoom(1.72, cx + 192, 142, SH);
    // G3：背对背定住，裂纹在虚身上爬开
    const fz = S.prop({ type: 'custom', x: 0, y: 0, depth: FY, draw: (g, x, y, t) => {
      const u = t - t0, sx = ux - Math.round(st.camX), pc = seg(u, 0.25, SH);
      const jit = pc > 0.5 && u < SH ? (Math.floor(t * 20) % 2 ? 1 : -1) : 0;
      if (u < SH + 0.5) {
        g.globalAlpha = u < SH ? 1 : 1 - seg(u, SH, SH + 0.5);
        g.drawImage(im('utsuro_frozen'), sx - fr.anchor[0] + jit, FY - fr.anchor[1]);
        if (u >= 0.25) g.drawImage(im(`utsuro_cracks_${Math.min(7, Math.floor(pc * 7 + 1e-6))}`), sx - fr.anchor[0] + jit, FY - fr.anchor[1]);
        g.globalAlpha = 1;
      }
      if (u >= 0.25 && u < SH + 0.4) {
        g.save(); g.globalCompositeOperation = 'lighter'; g.globalAlpha = Math.min(1, 0.2 + 0.5 * pc);
        g.drawImage(im('glow_r22_0.9'), sx - 22, FY - 16 - 22); g.restore();
      }
      if (u >= SH) drawShatter(g, u - SH, sx);
    } });
    const mt = weather(S, (g, t) => motes(g, t, 20, 3));
    S.wait(0.6).then(() => mark('ch13_cracks'));
    S.sfx('glass', 0.8);
    await S.wait(0.28); S.sfx('glass', 0.7, 1.2);
    await S.wait(0.27); S.sfx('glass', 0.9, 0.8);
    await S.wait(SH - 0.55);
    // G4：碎开 → 光聚成松阳的样子
    S.flash(0.2, 0.6, '#fff4dc');
    S.sfx('sparkle', 0.8);
    S.animate(2.3, (u) => { st.state.armada = G.lerp(0.5, 0, seg(u, 0.17, 1)); st.state.rays = Math.round(G.lerp(30, 46, u)); });
    S.zoom(1.3, cx + 190, 144, 1.4);
    await S.wait(0.35);
    const sy = gear(S.spawn('shouyou', ux, FY, { id: 'shouyou', name: '松阳', facing: 1 }));
    sy.alpha = 0; sy.shadow = false;
    S.pose(sy, 'smile');
    S.pose(p, 'gintoki_idle_sword_down');
    p.facing = -1;
    const gl = S.prop({ type: 'custom', x: 0, y: 0, depth: FY - 1, draw: (g) => {
      g.save(); g.globalCompositeOperation = 'lighter'; g.globalAlpha = Math.min(1, sy.alpha) * 0.8;
      g.drawImage(im('glow_r30_0.8'), ux - Math.round(st.camX) - 30, FY - 18 - 30); g.restore();
    } });
    await S.animate(0.45, (u) => { sy.alpha = 0.95 * u; sy.tint = { color: 'rgb(255,240,210)', k: 0.45 }; });
    mark('ch13_light');
    await S.animate(0.9, (u) => { sy.tint = { color: 'rgb(255,240,210)', k: 0.45 - 0.3 * u }; });
    await S.wait(0.4);
    // G4b：晨光里松阳的笑脸
    let fadeT = null;
    const g4b = overlay((g, u) => {
      const t = st.t;
      DAWN.ox.clearRect(0, 0, G.W, G.H);
      dawnStack(DAWN.ox, st, Math.round(st.camX), t, false);
      const k = G.lerp(1.55, 1.7, seg(u, 0, 4)), w = G.W / k, h = G.H / k;
      const zx = G.clamp(262, w / 2, G.W - w / 2), zy = G.clamp(118, h / 2, G.H - h / 2);
      g.drawImage(DAWN.oc, zx - w / 2, zy - h / 2, w, h, 0, 0, G.W, G.H);
      rays(g, 300, 60, t, 48 / 255);
      motes(g, t, 36, 6);
      g.save(); g.globalCompositeOperation = 'lighter'; g.drawImage(im('glow_r56_0.8'), 124 - 56, 80 - 56); g.restore();
      const b = P.bust_shouyou_smile_x4, x0 = 124 - Math.floor(b.w / 2), y0 = 30 + Math.round(Math.sin(t * 0.6 * Math.PI * 2) * 1.5);
      const a = fadeT == null ? Math.min(1, seg(u, 0, 0.2) + 0.6) : Math.max(0, 1 - (u - fadeT) / 0.6);
      if (a > 0) { g.globalAlpha = a; g.drawImage(G.image(b.image), x0, y0); g.globalAlpha = 1; }
      if (fadeT != null) {       // 笑脸散成光点，往上飘走
        const d = u - fadeT, rnd = G.prng(31);
        for (let i = 0; i < 80; i++) {
          const ox = x0 + 20 + rnd() * 60, oy = y0 + 10 + rnd() * 80, dl = rnd() * 0.4, life = 0.8 + rnd() * 0.8, dd = d - dl;
          if (dd < 0 || dd > life) continue;
          g.fillStyle = `rgba(255,244,210,${(1 - dd / life).toFixed(2)})`;
          g.fillRect(Math.round(ox + Math.sin(dd * 3 + i) * 3), Math.round(oy - (12 + (i % 5) * 4) * dd - 10 * dd * dd), i % 3 ? 1 : 2, i % 3 ? 1 : 2);
        }
      }
      const lb = Math.round(22 * (1 - (fadeT == null ? 0 : seg(u - fadeT, 0.3, 0.8))));
      if (lb > 0) { g.fillStyle = '#000'; g.fillRect(0, 0, G.W, lb); g.fillRect(0, G.H - lb, G.W, lb); }
    }, null, -10);
    S.music('sad', 0.6);
    await S.wait(0.5);
    await S.say('shouyou', '……谢谢。你们都长大了呢。', { name: '松阳', expr: 'smile' });
    fadeT = G.time - g4b.t0;
    S.sfx('sparkle', 0.6);
    await S.wait(1.3);
    await S.fadeOut(0.9);
    unoverlay(g4b);
    for (const pr of [fz, gl, mt]) S.unprop(pr);
    S.remove(sy);
  }
  // H：江户的日出：舰队往上退走，紫色的蝴蝶绕着银时飞，飞进太阳里
  function bflyPos(u, sunX, sunY) {
    const t0 = 0.3, t1 = 2.6, t2 = 6.4;
    if (u < t0 || u >= t2) return null;
    if (u < t1) { const k = (u - t0) / (t1 - t0), a = k * 8; return [150 + 14 * Math.sin(a) - 10 * (1 - k), 122 + 5 * Math.cos(a * 1.3) + 16 * (1 - k)]; }
    const k = easeIO((u - t1) / (t2 - t1));
    return [G.lerp(150 + 14 * Math.sin(8), sunX, k) + 6 * Math.sin(k * 12), G.lerp(122 + 5 * Math.cos(10.4), sunY + 4, k) + 4 * Math.sin(k * 19)];
  }
  async function sunrise(S, cx) {
    const st = G.world.stage, p = S.player, P = PR();
    for (const a of st.actors) if (a !== p) a.remove = true;
    G.ui.letterboxTarget = 0; G.ui.letterbox = 0;
    S.zoom(1, null, null, 0);
    Object.assign(st.state, { dawn: 1, armada: 0.45, sunX: 300, sunY: 120, rays: 38 });
    p.x = cx + 150; p.y = FY; p.facing = 1; p.visible = true;
    S.unpose(p);
    const shin = gear(S.spawn('shinpachi', cx + 122, FY, { id: 'h_shin', name: '新八', facing: 1 }));
    const kag = gear(S.spawn('kagura', cx + 178, FY, { id: 'h_kag', name: '神乐', facing: 1 }));
    S.pose(kag, 'umbrella_open');
    gear(S.spawn('sadaharu', cx + 218, FY, { id: 'h_sad', name: '定春', facing: 1 }));
    const t0 = st.t;
    S.prop({ type: 'custom', x: 0, y: 0, depth: 9200, draw: (g, x, y, t) => {
      const u = t - t0, sx0 = Math.round(cx - st.camX);
      for (let j = 5; j >= 0; j--) {
        const q = bflyPos(u - j * 0.06, st.state.sunX, st.state.sunY);
        if (!q) continue;
        if (j === 0) { const b = P[`butterfly_${[0, 1, 2, 1][Math.floor(t * 12) % 4]}`]; g.drawImage(G.image(b.image), Math.round(sx0 + q[0] - b.w / 2), Math.round(q[1] - b.h / 2)); }
        else if ((Math.floor(t * 15) + j) % 2 === 0) px(g, sx0 + q[0] - 1, q[1] + 2, j < 3 ? 'rgb(255,226,140)' : 'rgb(255,246,210)');
      }
      sparkle(g, sx0 + 125, 147, u - 1.6, 4);          // 新八的眼镜反光
    } });
    weather(S, (g, t) => { motes(g, t, 34, 9); sakura(g, t, 10, 13, 18, 10); });
    S.animate(3.5, (u) => { st.state.armada = G.lerp(0.45, 0, u); });
    S.animate(7, (u) => { st.state.sunY = G.lerp(120, 104, easeOut(u)); });
    S.zoom(1.14, cx + 176, 132, 0); S.zoom(1, cx + 176, 132, 3.0);
    S.music('ending', 0.6);
    S.sfx('wind', 0.35);
    await S.fadeIn(1.0);
    S.wait(1.6).then(() => mark('ch13_butterfly'));
    await S.wait(1.0);
    await S.narrate('长夜过去，江户迎来了黎明。', { auto: 2.8 });
    await S.wait(1.2);
    await S.say('kagura', '银酱……肚子饿了阿鲁。', { actor: kag, expr: 'happy' });
    await S.say('gintoki', '……回家吧。');
    await S.say('shinpachi', '……嗯！', { actor: shin, expr: 'happy' });
    S.sfx('bark', 0.7);
    await S.wait(2.0);
    await S.fadeOut(1.6);
    F().ch13Done = true;
  }

  // ================================================================ 地图（第十三章版）
  function defineStages() {
    G.STAGES.roofs_ch13 = { id: 'roofs_ch13', bg: 'ch13_night', x0: 0, x1: 2100, yMin: 160, yMax: 180, music: 'epic', props: [], state: { armada: 1, dawn: 0 },
      triggers: [
        { id: 'seg1', x0: 330, x1: 9999, cond: () => F().started && !F().seg1, run: async (S) => segment1(S) },
        { id: 'seg2', x0: 810, x1: 9999, cond: () => F().seg1 && !F().seg2, run: async (S) => segment2(S) },
        { id: 'seg3', x0: 1290, x1: 9999, cond: () => F().seg2 && !F().seg3, run: async (S) => segment3(S) },
        { id: 'final', x0: 1760, x1: 9999, cond: () => F().seg3 && !F().finale, run: async (S) => { F().finale = true; await finale(S); } },
      ] };
  }

  // ================================================================ 第十三章主流程
  G.STORY.chapter13 = async function (S) {
    defineStages();
    OV.length = 0;
    G.fadeAlpha = 0;
    G.world.stage = null;
    await S.chapterCard('ch13');
    const p = gear(new G.Actor('gintoki', 60, FY, { id: 'player', team: 'player', hp: 100, speed: 74, name: '银时' }));
    G.world.player = p;
    G.fadeAlpha = 1;
    await S.setStage('roofs_ch13', { x: 60, y: FY, facing: 1, fade: false });
    skyFx(S);
    await S.run(async (S) => { await opening(S); F().started = true; });
    await S.until(() => G.flags.ch13Done);
    clearOverlays();
    S.filter(null);
    G.ui.letterboxTarget = 0;
  };
})();
