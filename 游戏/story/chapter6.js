// 第六章：日常（原片 s06：六个漫画格小短篇，幕间章，没有正式战斗，每一格一个小游戏）
//   其一 MADAO：河边纸箱里的长谷川（对话选项）→ 乌鸦「阿呆～」
//   其二 小钢珠：按 J 停转轮，7、7……7？……6。「输光」，两个人烧成白灰
//   其三 周一：连按撕日历 → 周一 → 神圣的 Jump 从天而降（看准时机接住）→ 星星眼
//   其四 偶像：寺门通的演唱会，新八跟着节拍喊 L·O·V·E
//   其五 醋昆布：定春的鼻涕泡越吹越大（看准时机戳破）→ 神乐被弹上天又掉回来，接着嚼
//   其六 跟踪狂：阿妙家地板下的近藤，薙刀从地板刺下来停在鼻尖 → 「※以上皆为日常」
// 画面照原片：漫画纸上的格子，格子里是放大 2–3 倍的像素画（S.insert 整页画，S.say / 小游戏照常叠在上面）
'use strict';
(function () {
  const G = window.G;
  const PR = () => G.D.bg.daily_props;
  const INK = '#181425';
  const BGS = {};
  const bgOf = (key) => BGS[key] || (BGS[key] = new G.Background(G.D.bg[key]));
  const NOST = { state: {}, door: 0 };
  const ease = (u) => 1 - Math.pow(1 - G.clamp(u, 0, 1), 3);
  const easeIO = (u) => { u = G.clamp(u, 0, 1); return u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2; };
  const px = (g, x, y, c, w = 1, h = 1) => { g.fillStyle = c; g.fillRect(Math.round(x), Math.round(y), w, h); };
  function pline(g, x0, y0, x1, y1, c, w = 1) {
    g.fillStyle = c;
    // 横线、竖线一次画完（原来一个像素一个 fillRect：小钢珠页光边框就 1600 多次，无显卡的浏览器里一帧要 0.8 秒）
    if ((x0 === x1 || y0 === y1) && Number.isInteger(x0) && Number.isInteger(y0) && Number.isInteger(x1) && Number.isInteger(y1)) {
      const rx = Math.round(Math.min(x0, x1)), ry = Math.round(Math.min(y0, y1));
      g.fillRect(rx, ry, Math.round(Math.abs(x1 - x0)) + w, Math.round(Math.abs(y1 - y0)) + w);
      return;
    }
    const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)) | 0;
    for (let i = 0; i <= n; i++) { const k = n ? i / n : 0; g.fillRect(Math.round(x0 + (x1 - x0) * k), Math.round(y0 + (y1 - y0) * k), w, w); }
  }
  function img(g, src, x, y, o = {}) {
    const im = G.image(src);
    if (!G.ready(im)) return;
    const s = o.scale || 1;
    if (o.alpha != null) g.globalAlpha = o.alpha;
    if (o.rot) {
      g.save(); g.translate(x, y); g.rotate(o.rot); g.drawImage(im, -im.width * s / 2, -im.height * s / 2, im.width * s, im.height * s); g.restore();
    } else if (o.center) g.drawImage(im, Math.round(x - im.width * s / 2), Math.round(y - im.height * s / 2), Math.round(im.width * s), Math.round(im.height * s));
    else g.drawImage(im, Math.round(x), Math.round(y), Math.round(im.width * s), Math.round(im.height * s));
    g.globalAlpha = 1;
  }
  // 画一个角色（t = 这个动作开始以后的秒数）
  function ch(g, cid, anim, t, x, y, o = {}) {
    const A = G.atlas(cid), a = A.anim(anim);
    if (!a) return;
    let f = Math.floor(t * a.fps * (o.speed || 1) + 1e-6);
    f = a.kind === 'loop' ? G.mod(f, a.frames) : G.clamp(f, 0, a.frames - 1);
    A.draw(g, anim, f, Math.round(x), Math.round(y), { flip: o.flip, scale: o.scale, alpha: o.alpha, tint: o.tint });
  }
  // 一个漫画格：多边形裁切；格子里的世界放大 k 倍，世界坐标 (cx, cy) 落在画面的 focus 上（同原片 panel()）
  function poly(g, P) { g.beginPath(); P.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); }
  function panel(g, P, cam, focus, world, post) {
    g.save();
    poly(g, P); g.clip();
    g.fillStyle = '#000'; g.fillRect(0, 0, G.W, G.H);
    g.save();
    const [k, cx, cy] = cam;
    g.translate(Math.round(focus[0] - cx * k), Math.round(focus[1] - cy * k));
    g.scale(k, k);
    g.imageSmoothingEnabled = false;
    world(g);
    g.restore();
    if (post) post(g, (wx, wy) => [focus[0] + (wx - cx) * k, focus[1] + (wy - cy) * k]);
    g.restore();
    for (let i = 0; i < P.length; i++) {        // 2 px 的墨线边框
      const [x0, y0] = P[i], [x1, y1] = P[(i + 1) % P.length];
      pline(g, x0, y0, x1, y1, INK, 2);
    }
  }
  const FULL = [[6, 6], [378, 6], [378, 210], [6, 210]];
  function paper(g) { img(g, PR().paper, 0, 0); }
  // 页面上的拟声字（画面坐标，弹出来再淡掉）
  function words(g, st) {
    for (const w of st.words) {
      const a = st.now - w.t0;
      if (a < 0 || a > w.life) continue;
      const d = G.D.ui.sfx[w.word];
      if (!d) continue;
      const s = a < 0.12 ? 0.4 + 0.6 * ease(a / 0.12) * 1.1 : 1;
      g.globalAlpha = a > w.life - 0.2 ? Math.max(0, (w.life - a) / 0.2) : 1;
      img(g, d.image, w.x + d.ox + (d.ox < 0 ? 0 : 0), w.y + d.oy, { scale: s });
      g.globalAlpha = 1;
    }
  }
  function word(st, wd, x, y, life = 0.8) { st.words.push({ word: wd, x, y, t0: st.now, life }); }
  function tag(g, n) { img(g, PR()[`tag${n}`], 10, 10); }
  function capBox(g, text, cx, cy, size = 12) {    // 白底墨框的说明框
    const f = size === 16 ? G.f16 : G.f12;
    const w = f.width(text) + 12, h = size + 8;
    const x = Math.round(cx - w / 2), y = Math.round(cy - h / 2);
    g.fillStyle = INK; g.fillRect(x - 2, y - 2, w + 4, h + 4);
    g.fillStyle = '#fff'; g.fillRect(x, y, w, h);
    f.draw(g, text, cx, y + 4, INK, { align: 'center' });
  }

  // ================================================================ 翻页（新的一页从右边滑进来，盖住旧的一页）
  let cur = null, turn = null, insT = 0;
  function root(g, t) {
    insT = t;
    if (!cur) return;
    const drawPage = (p) => { p.st.now = t - p.t0; p.draw(g, p.st.now, p.st); words(g, p.st); };
    if (turn) {
      const k = Math.min(1, (t - turn.t0) / 0.3), ox = Math.round((G.W + 8) * (1 - ease(k)));
      if (turn.old) drawPage(turn.old);
      g.save(); g.translate(ox, 0); drawPage(cur); g.restore();
      for (const [d, a] of [[1, 0.55], [2, 0.35], [3, 0.18]]) { g.fillStyle = `rgba(0,0,0,${a})`; g.fillRect(ox - d, 0, 1, G.H); }
      if (k >= 1) turn = null;
    } else drawPage(cur);
  }
  async function newPage(S, draw, st = {}) {
    st.words = st.words || [];
    const p = { draw, st, t0: insT };
    turn = { old: cur, t0: insT };
    cur = p;
    S.sfx('whoosh', 0.7);
    await S.wait(0.32);
    return st;
  }
  // 等玩家按一下 J（停转轮这种自己的小游戏）
  async function waitKey(S) {
    G.ui.waitKey = true;
    await S.until(() => { if (G.input.okHit()) { G.input.consumeOk(); return true; } return false; });
    G.ui.waitKey = false;
  }
  function prompt(g, text, t) {
    if (!G.ui.waitKey || Math.floor(t * 2.5) % 2) return;
    G.f12.draw(g, text, G.W / 2, 190, '#ffe14a', { align: 'center', outline: INK });
  }

  // ================================================================ 其一 MADAO（河边的黄昏）
  function reeds(g, t, x0, x1, base, n, seed, h0, h1, front) {
    const rnd = G.prng(seed * 101);
    for (let i = 0; i < n; i++) {
      const x = x0 + (x1 - x0) * rnd(), h = h0 + (h1 - h0) * rnd(), ph1 = rnd(), ph2 = rnd();
      const s = 2.5 * Math.sin(2 * Math.PI * (0.7 * t + ph1)) + 2 + 0.6 * Math.sin(2 * Math.PI * (2.3 * t + ph2));
      const c = front ? 'rgb(52,40,40)' : 'rgb(70,56,50)';
      pline(g, x, base, x + 0.35 * s, base - h / 2, c); pline(g, x + 0.35 * s, base - h / 2, x + s, base - h, c);
      px(g, x + s - 1, base - h - 4, front ? 'rgb(110,86,70)' : 'rgb(150,120,96)', 2, 5);
    }
  }
  function leaves(g, t, n, seed) {
    const rnd = G.prng(seed);
    const cols = ['rgb(222,120,50)', 'rgb(190,80,40)', 'rgb(240,180,80)'];
    for (let i = 0; i < n; i++) {
      const x0 = rnd() * (G.W + 40), y0 = rnd() * G.H, v = 14 * (0.6 + rnd() * 0.8), w = 46 * (0.6 + rnd() * 0.8), ph = rnd() * 6.28, c = cols[i % 3];
      const x = G.mod(x0 + t * w + Math.sin(t * 1.3 + ph) * 6, G.W + 40) - 20, y = G.mod(y0 + t * v, G.H + 10) - 5;
      px(g, x, y, c, Math.floor(t * 6 + ph) % 2 ? 2 : 1, Math.floor(t * 6 + ph) % 2 ? 1 : 2);
    }
  }
  function drawV1(g, t, st) {
    paper(g);
    const snap = st.snapT != null ? 0.5 * ease((t - st.snapT) / 0.18) : 0;
    const k = 2.0 + 0.25 * easeIO(t / 8) + snap;
    const cx = 196 + 10 * easeIO(t / 8) + (snap ? 14 * snap / 0.5 : 0), cy = 127 + (snap ? 2 : 0);
    panel(g, FULL, [k, cx, cy], [192, 100], (w) => {
      bgOf('daily_v1').draw(w, 0, t, NOST);
      reeds(w, t, 120, 320, 147, 12, 1, 10, 20, false);
      if (st.cryT != null) ch(w, 'hasegawa__s06', 'box_cry', t - st.cryT, 214, 150);
      else ch(w, 'hasegawa', 'box', t, 214, 150);
      if (st.cryT != null) {                    // 头上的阴郁线
        for (let i = 0; i < 7; i++) {
          const ph = (t * 1.2 + i * 0.37) % 1;
          px(w, 200 + i * 4, 112 - ph * 4, 'rgb(84,96,170)', 1, 6 + (i % 3) * 2);
        }
      }
      if (st.crowT != null) {                   // 小乌鸦飞来，停在纸箱角上
        const u = (t - st.crowT) / 0.55, f = G.D.bg.ch5.crow.frames;
        const x = u < 1 ? G.lerp(320, 230, ease(u)) : 230, y = u < 1 ? G.lerp(70, 128, ease(u)) : 128;
        const im = G.image(u < 1 ? f[Math.floor(t * 10) % 2] : f[0]);
        if (G.ready(im)) { w.save(); w.translate(Math.round(x), Math.round(y)); w.scale(-1, 1); w.drawImage(im, -6, -3); w.restore(); }
      }
      reeds(w, t, 96, 170, 172, 7, 2, 28, 42, true);
      reeds(w, t, 262, 330, 174, 6, 3, 30, 46, true);
      leaves(w, t, 22, 61);
    });
    tag(g, 1);
  }
  async function v1(S) {
    const st = await newPage(S, drawV1, {});
    await S.wait(0.3);
    S.nameCard('hasegawa');
    S.sfx('slide_up', 0.6);
    await S.wait(1.2);
    await S.say('gintoki', '……长谷川先生？你怎么住在纸箱里了。');
    await S.say('hasegawa', '啊，银桑。……工作丢了，老婆走了，房子也没了。', { expr: 'sad' });
    await S.say('hasegawa', '现在我的家，就是这个纸箱。', { expr: 'sad' });
    const c = await S.choice(['「振作一点啊」', '「分你一串团子」', '「纸箱住着舒服吗」'], '说点什么？');
    if (c === 0) {
      await S.say('gintoki', '振作一点啊，MADAO。');
      await S.say('hasegawa', '……你刚才是不是叫我 MADAO 了。', { expr: 'shock' });
      await S.say('gintoki', '彻底没用的大叔，简称 MADAO。');
      await S.say('hasegawa', '不要缩写别人的人生啊！', { expr: 'shout' });
    } else if (c === 1) {
      await S.say('gintoki', '……给。最后一串团子。');
      await S.say('hasegawa', '银桑……！你真是好人……', { expr: 'cry' });
      await S.say('gintoki', '签子给你。团子我刚才吃掉了。');
      await S.say('hasegawa', '你这是来报复社会的吗！', { expr: 'shout' });
    } else {
      await S.say('hasegawa', '……下雨天会漏。不过，风吹不进来。', { expr: 'sad' });
      await S.say('gintoki', '……这说明不了任何好事吧。');
    }
    st.crowT = st.now; S.sfx('whoosh', 0.35);
    await S.wait(0.7);
    S.sfx('crow', 0.9);
    await S.say('hasegawa', '……连乌鸦都来看我笑话了吗。', { expr: 'gloom' });
    st.snapT = st.now;
    word(st, '阿呆～', 236, 92, 1.0);
    S.sfx('crow', 0.8, 0.9);
    await S.wait(0.3);
    st.cryT = st.now; S.sfx('sweat', 0.45);
    await S.wait(0.4);
    await S.say('hasegawa', '纸箱……其实还挺暖和的。', { expr: 'cry' });
  }

  // ================================================================ 其二 小钢珠
  const INSET = [[238, 12], [372, 12], [372, 84], [222, 84]];
  function reelAt(r, now) {                     // 转轮现在停在哪个数字附近（v：数字 n 在窗口正中时 v = n）
    if (r.stop) {
      const u = G.clamp((now - r.stop.t0) / r.stop.dur, 0, 1);
      return G.lerp(r.stop.from, r.stop.to, r.stop.ease ? r.stop.ease(u) : ease(u));
    }
    return r.v0 + (now - r.t0) * r.speed;
  }
  function drawLcd(g, t, st) {
    g.save(); poly(g, INSET); g.clip();
    g.fillStyle = 'rgb(46,26,86)'; g.fillRect(200, 0, 184, 100);
    g.fillStyle = 'rgba(90,60,170,0.7)'; g.beginPath();
    for (let i = 0; i < 12; i++) {
      const a0 = t * 0.8 + (i * 2 * Math.PI) / 12, a1 = a0 + Math.PI / 12;
      g.moveTo(297, 48); g.lineTo(297 + Math.cos(a0) * 200, 48 + Math.sin(a0) * 200); g.lineTo(297 + Math.cos(a1) * 200, 48 + Math.sin(a1) * 200); g.closePath();
    }
    g.fill();
    st.reels.forEach((r, i) => {
      const x = 238 + i * 42, y = 32, v = reelAt(r, t);
      g.fillStyle = INK; g.fillRect(x - 2, y - 2, 38, 48);
      const spinning = !r.stop || t - r.stop.t0 < r.stop.dur * 0.55;
      const strip = PR()[!st.lit ? 'reel_unlit' : spinning ? 'reel_blur' : 'reel_red'];
      const row = Math.round(G.mod(40 * v, 400));
      const im = G.image(strip);
      if (G.ready(im)) g.drawImage(im, 0, row, 34, 44, x, y, 34, 44);
      if (spinning) for (let k = 0; k < 6; k++) px(g, x + 3 + k * 5, y + G.mod(t * 400 + k * 13, 44), 'rgba(255,255,255,0.7)', 1, 4);
    });
    if (st.reach && Math.floor(t * 6) % 2 === 0) G.f12.draw(g, 'REACH!!', 297, 14, '#ffe14a', { align: 'center', outline: 'rgb(150,20,40)' });
    if (st.hotT != null && t - st.hotT < 0.6 && Math.floor(t * 15) % 2 === 0) { g.strokeStyle = 'rgb(255,60,60)'; g.lineWidth = 2; g.strokeRect(234, 28, 128, 52); }
    g.restore();
    for (let i = 0; i < INSET.length; i++) { const [x0, y0] = INSET[i], [x1, y1] = INSET[(i + 1) % INSET.length]; pline(g, x0, y0, x1, y1, INK, 2); }
  }
  function drawV2(g, t, st) {
    paper(g);
    const k = 1.85 + 0.25 * easeIO(t / 3);
    if (st.grey) g.filter = 'grayscale(1) brightness(0.68)';
    panel(g, FULL, [k, 192, 116], [192, 100], (w) => {
      bgOf('daily_v2').draw(w, 0, t, NOST);
      img(w, PR().stool, 158 - 8, 141 - 2); img(w, PR().stool, 227 - 8, 141 - 2);
      const ash = st.ashT != null ? G.clamp((t - st.ashT) / 0.64, 0, 1) : 0;
      const pose = st.blank ? 'blank_sit' : st.shock ? 'shock_sit' : st.frozen ? 'frozen_sit' : 'cheer_sit';
      const tint = st.blank ? { color: 'rgb(236,236,240)', k: 0.85 } : null;
      if (ash < 1) {
        ch(w, 'gintoki__s06', pose, t, 158, 143, { tint, alpha: 1 - ash });
        ch(w, 'hasegawa__s06', pose, t + 0.1, 227, 143, { flip: true, tint, alpha: 1 - ash });
      }
      if (ash > 0) {                            // 烧成白灰，被风吹走
        const rnd = G.prng(7);
        for (let i = 0; i < 70; i++) {
          const bx = (i % 2 ? 227 : 158) - 8 + rnd() * 16, by = 112 + rnd() * 30, d = ash * (40 + rnd() * 60);
          if (rnd() < ash * 1.4) px(w, bx + d, by - d * 0.2 + Math.sin(t * 9 + i) * 2, 'rgb(225,225,230)');
        }
      }
      if (st.ballT != null) {                   // 一颗小钢珠孤零零地滚走
        const u = Math.min(1, (t - st.ballT) / 1.2);
        w.fillStyle = 'rgb(200,204,214)'; w.beginPath(); w.arc(202 + 100 * u, 152, 2, 0, Math.PI * 2); w.fill();
        px(w, 201 + 100 * u, 151, '#fff');
      }
      if (st.blank && ash < 0.3) {
        for (const hx of [158, 227]) for (let i = 0; i < 5; i++) px(w, hx - 8 + i * 4, 104 + (i % 2) * 2, 'rgb(70,70,96)', 1, 6);
      }
    });
    g.filter = 'none';
    if (st.lcd) drawLcd(g, t, st);
    if (st.flashT != null && t - st.flashT < 0.08) { g.fillStyle = 'rgba(255,255,255,0.6)'; g.fillRect(0, 0, G.W, G.H); }
    if (st.stampT != null) {
      const u = G.clamp((t - st.stampT) / 0.12, 0, 1);
      img(g, PR().stamp, 86, 56, { center: true, scale: 2.2 - 1.2 * u });
    }
    if (st.moneyT != null && t > st.moneyT) capBox(g, '所持金：0円', 56, 98);
    tag(g, 2);
    prompt(g, '按 J 停下转轮！', t);
  }
  async function stopReel(S, st, i, to, dur = 0.55, e) {
    const r = st.reels[i], v = reelAt(r, st.now);
    let target = Math.ceil(v) + 4;
    while (G.mod(target, 10) !== to) target++;
    r.stop = { from: v, to: target, t0: st.now, dur, ease: e };
    await S.wait(dur);
    S.sfx('coin', 0.4, 1.4 + i * 0.1);
  }
  async function v2(S) {
    const st = await newPage(S, drawV2, { reels: [0, 1, 2].map((i) => ({ v0: i * 3.3, t0: 0, speed: 16 })), lit: false });
    S.sfx('coin', 0.35, 1.3);
    await S.wait(0.4);
    await S.say('hasegawa', '银桑，今天手气一定不错！我感觉得到！', { expr: 'happy' });
    await S.say('gintoki', '今天的房租，就靠这台机器了。');
    st.lcd = true; st.lit = true;
    S.sfx('pop', 0.6);
    word(st, '来了!!', 249 - 120, 129 - 40, 0.6);
    S.sfx('coin', 0.5);
    S.hint('按 J 停下转轮（三次）', 4);
    for (let i = 0; i < 2; i++) { await waitKey(S); await stopReel(S, st, i, 7); }
    st.reach = true;
    S.sfx('drumroll', 0.55);
    word(st, '来了!!', 120, 60, 0.6);
    await S.say('gintoki', '来了来了！！', { expr: 'shout' });
    await waitKey(S);
    // 第三个：慢慢停在 7 上……「！？」……又往下爬……啪嗒，6
    await stopReel(S, st, 2, 7, 1.0, (u) => 1 - Math.pow(1 - u, 2.2));
    st.hotT = st.now; st.frozen = true;
    S.sfx('coin', 0.6, 1.8);
    word(st, '！？', 152 - 60, 98 - 40, 0.6);
    await S.wait(0.5);
    const r = st.reels[2], v = reelAt(r, st.now);
    r.stop = { from: v, to: v - 0.2, t0: st.now, dur: 0.22 };
    await S.wait(0.24);
    r.stop = { from: v - 0.2, to: v - 1, t0: st.now, dur: 0.08 };
    await S.wait(0.08);
    st.reach = false;
    S.sfx('record_scratch', 0.9);
    st.flashT = st.now; st.shock = true;
    await S.wait(0.1);
    st.grey = true; st.blank = true;
    S.sfx('fail', 0.8);
    await S.wait(0.25);
    st.stampT = st.now;
    S.sfx('thud', 0.9); S.shake(4, 0.3);
    await S.wait(0.3);
    st.moneyT = st.now;
    await S.say('gintoki', '……这台机器，是不是动过手脚。', { expr: 'gloom' });
    await S.say('hasegawa', '……所持金，零元。', { expr: 'cry' });
    st.ashT = st.now; S.sfx('wind', 0.5);
    await S.wait(0.4);
    st.ballT = st.now;
    await S.wait(1.0);
  }

  // ================================================================ 其三 周一
  const CAL_SPLIT = [[6, 6], [152, 6], [134, 210], [6, 210]];
  const GIN_PANEL = [[158, 6], [378, 6], [378, 210], [140, 210]];
  function drawCalendarWorld(w, t, st) {
    img(w, G.D.bg.daily_v3_cal.layers[0].image, 0, 0);
    const c = st.ripT == null ? PR().calendar_sun : PR().calendar_mon;
    img(w, c.image, c.x, c.y);
    if (st.ripT != null) {
      const p = t - st.ripT;
      if (p < 0.9) {
        const ang = (40 * p / 0.9 + 25 * ease(p / 0.2)) * Math.PI / 180;
        img(w, PR().cal_page_sun, 159 + 33 - 70 * ease(p / 0.6) - 30 * p, 70 + 42 - 100 * ease(p / 0.7), { rot: -ang });
      }
      if (p > 0.1 && p < 1.4) {                 // 「Jump!」那一格的闪光
        const s = Math.round(5 * Math.sin(Math.PI * G.clamp((p - 0.1) / 0.6, 0, 1)));
        px(w, 206 - s, 128, '#fff8d0', 2 * s + 1, 1); px(w, 206, 128 - s, '#fff8d0', 1, 2 * s + 1);
      }
    }
  }
  function drawShoujo(w, t, st) {
    img(w, G.D.bg.daily_v3_gin.layers[0].image, 0, 0);
    w.fillStyle = 'rgba(255,232,240,0.55)'; w.beginPath();
    for (let i = 0; i < 8; i++) {                // 转动的光芒
      const a0 = t * 0.21 + (i * 2 * Math.PI) / 8;
      w.moveTo(193, 119); w.lineTo(193 + Math.cos(a0 - 0.12) * 300, 119 + Math.sin(a0 - 0.12) * 300); w.lineTo(193 + Math.cos(a0 + 0.12) * 300, 119 + Math.sin(a0 + 0.12) * 300); w.closePath();
    }
    w.fill();
    w.fillStyle = 'rgba(255,255,255,0.25)';     // 两道光柱
    w.beginPath(); w.moveTo(186, 0); w.lineTo(190, 0); w.lineTo(204, 154); w.lineTo(170, 154); w.closePath(); w.fill();
    const rnd = G.prng(14);
    for (let i = 0; i < 14; i++) {              // 往上飘的泡泡
      const x = rnd() * G.W, sp = 10 + rnd() * 16, r = 1 + rnd() * 2.5, y = G.mod(rnd() * 216 - t * sp, 230) - 7;
      w.strokeStyle = 'rgba(255,255,255,0.8)'; w.lineWidth = 1; w.beginPath(); w.arc(x, y, r, 0, Math.PI * 2); w.stroke();
    }
    const kneelAnim = st.starsT != null ? 'kneel_stars' : 'kneel_reach';
    ch(w, 'gintoki__s06', kneelAnim, t - (st.starsT != null ? st.starsT : st.kneelT || 0), 176, 150);
  }
  function drawV3(g, t, st) {
    paper(g);
    if (!st.split) {
      panel(g, FULL, [1.6, 192, 99], [192, 108], (w) => drawCalendarWorld(w, t, st));
    } else {
      const u = ease((t - st.split) / 0.28);
      const P = FULL.map(([x, y], i) => [G.lerp(x, CAL_SPLIT[i][0], u), G.lerp(y, CAL_SPLIT[i][1], u)]);
      panel(g, P, [G.lerp(1.6, 1.3, u), 192, 99], [G.lerp(192, 76, u), 108], (w) => drawCalendarWorld(w, t, st));
      const off = Math.round((1 - u) * (G.W + 20));
      g.save(); g.translate(off, 0);
      const k = 2.9 + 0.2 * easeIO((t - st.split) / 2);
      panel(g, GIN_PANEL, [k, 185, 130], [262, 104], (w) => drawShoujo(w, t, st), (pg, S2) => {
        if (st.jumpT == null) return;
        const d = t - st.jumpT;
        const [jx, jy] = S2(193, 119);
        let y = jy + 2 * Math.sin(3.2 * t) - 110 * (1 - ease(d / 0.45));
        if (st.bonkT != null && t - st.bonkT < 0.4) y += 6 * Math.sin((t - st.bonkT) * 30);
        img(pg, PR().jump, jx, y, { center: true });
        const gl = G.mod(t, 0.9) / 0.9;          // 斜着扫过去的白光
        if (gl < 0.4) { pg.fillStyle = 'rgba(255,255,255,0.6)'; pg.fillRect(Math.round(jx - 17 + gl * 85), Math.round(y - 22), 3, 44); }
        if (st.starsT != null && t - st.starsT > 0.3) {     // 喜极而泣
          const [ex, ey] = S2(177, 136);
          for (let i = 0; i < 12; i++) {
            const ph = G.mod(t * 2.4 + i / 12, 1);
            const side = i % 2 ? 1 : -1;
            px(pg, ex + side * (6 + ph * 40), ey + ph * ph * 50, 'rgb(120,200,255)', 2, 2);
          }
        }
      });
      if (st.capT != null && t > st.capT) capBox(g, '周一＝Jump发售日', 262, 26, 16);
      g.restore();
    }
    tag(g, 3);
  }
  async function v3(S) {
    const st = await newPage(S, drawV3, {});
    await S.wait(0.4);
    await S.say('gintoki', '（……今天是星期几来着。）');
    const ok = await S.mash({ label: '撕掉日历！连按 J', need: 10, time: 4, decay: 1.5 });
    st.ripT = st.now;
    S.sfx('slide_up', 0.8);
    word(st, '唰!', 120, 50, 0.6);
    S.sfx('sparkle', 0.6);
    await S.wait(0.6);
    if (!ok) await S.say(null, '（手一滑，整本日历都扯下来了。……不过最上面那一页，正好是周一。）');
    await S.say('gintoki', '……二十五号。周一。', { expr: 'shock' });
    st.split = st.now; st.kneelT = st.now;
    S.sfx('whoosh', 0.5);
    await S.wait(0.3);
    st.jumpT = st.now;
    S.sfx('fanfare', 0.55);
    await S.wait(0.5);
    const got = await S.timing({ label: '神圣的 Jump 从天而降！看准时机伸手接住（按 J）', speed: 1.2, zone: [0.42, 0.58] });
    if (!got) { st.bonkT = st.now; S.sfx('thud', 0.8); await S.say(null, '……Jump 砸在了脸上。'); }
    st.starsT = st.now;
    S.sfx('shine', 0.5); S.sfx('sparkle', 0.4, 1.2);
    word(st, '闪!', 300, 70, 0.8);
    st.capT = st.now + 0.3;
    await S.wait(0.6);
    await S.say('gintoki', 'Jump是男人的圣经啊！', { expr: 'happy' });
  }

  // ================================================================ 其四 偶像（寺门通的演唱会）
  const OTSU_SPLIT = [[6, 6], [222, 6], [196, 210], [6, 210]];
  const SHIN_PANEL = [[228, 6], [378, 6], [378, 210], [202, 210]];
  function drawStageWorld(w, t, st) {
    bgOf('daily_v4').draw(w, 0, t, NOST);
    // 聚光灯
    const fx = 150 + 10 * Math.sin(1.6 * t);
    w.save(); w.globalCompositeOperation = 'lighter';
    for (const [sx, col] of [[20, 'rgba(255,200,240,0.16)'], [364, 'rgba(200,230,255,0.16)']]) {
      w.fillStyle = col; w.beginPath(); w.moveTo(sx - 4, 0); w.lineTo(sx + 4, 0); w.lineTo(fx + 14, 120); w.lineTo(fx - 14, 120); w.closePath(); w.fill();
    }
    for (const [a, col] of [[Math.sin(2.1 * t), 'rgba(255,120,200,0.12)'], [Math.sin(1.7 * t + 1), 'rgba(120,220,255,0.12)']]) {
      const tx = 192 + a * 140;
      w.fillStyle = col; w.beginPath(); w.moveTo(190, 0); w.lineTo(194, 0); w.lineTo(tx + 20, 216); w.lineTo(tx - 20, 216); w.closePath(); w.fill();
    }
    w.restore();
    ch(w, 'otsu', 'sing', t, 150, 118);
    // 观众（剪影 + 荧光棒，跟着节拍跳）
    const beat = Math.abs(Math.sin(t * Math.PI * 2.2));
    const rows = [[148, 16, 4, null], [160, 12, 5, [246, 280]], [188, 9, 7, [238, 290]]];
    const sticks = ['rgb(255,140,205)', 'rgb(130,220,255)', 'rgb(255,232,110)', 'rgb(170,255,150)'];
    rows.forEach(([y, n, r, gap], ri) => {
      for (let i = 0; i < n; i++) {
        const x = 12 + (i + 0.5) * (360 / n) + (ri % 2) * 8;
        if (gap && x > gap[0] && x < gap[1]) continue;
        const b = Math.round(beat * 2 * ((i + ri) % 2 ? 1 : 0.6));
        w.fillStyle = 'rgb(44,30,62)';
        w.beginPath(); w.arc(x, y - r * 2 - b, r, 0, Math.PI * 2); w.fill();
        w.fillRect(x - r * 1.6, y - r - b, r * 3.2, r * 2 + b);
        px(w, x + r * 1.4, y - r * 3 - b - 6, sticks[(i + ri) % 4], 2, 7);
      }
    });
    const rnd = G.prng(44);                      // 彩纸
    const cc = ['rgb(255,150,200)', 'rgb(150,210,255)', 'rgb(255,230,120)', 'rgb(170,240,150)'];
    for (let i = 0; i < 34; i++) {
      const x = G.mod(rnd() * 420 + t * 8 + Math.sin(t * 2 + i) * 4, 420) - 20, y = G.mod(rnd() * 170 + t * 26, 170);
      px(w, x, y, cc[i % 4], Math.floor(t * 6 + i) % 2 ? 2 : 1, 1);
    }
  }
  function drawV4(g, t, st) {
    paper(g);
    if (!st.split) {
      panel(g, FULL, [2.2 - 0.2 * easeIO(t / 3), 152, 96 + Math.sin(t * 2.5)], [192, 100], (w) => drawStageWorld(w, t, st), (pg, S2) => {
        for (let i = 0; i < 5; i++) {            // 麦克风里飘出来的音符
          const ph = G.mod(t * 0.75 + i / 5, 1), [nx, ny] = S2(158, 92);
          const d = PR()[`note${i % 4}${i % 2 ? 'd' : 's'}`];
          img(pg, d, nx + Math.sin(ph * 6 + i) * 12 + i * 8 - 16, ny - ph * 58, { alpha: 1 - ph });
        }
      });
    } else {
      const u = ease((t - st.split) / 0.3);
      const P = FULL.map(([x, y], i) => [G.lerp(x, OTSU_SPLIT[i][0], u), G.lerp(y, OTSU_SPLIT[i][1], u)]);
      panel(g, P, [2.0, 152, 96], [G.lerp(192, 108, u), 100], (w) => drawStageWorld(w, t, st));
      const off = Math.round((1 - u) * (G.H + 20));
      g.save(); g.translate(0, off);
      panel(g, SHIN_PANEL, [2.2, 262, 136], [300, 132], (w) => {
        drawStageWorld(w, t, st);
        ch(w, 'shinpachi', 'otaku_cheer', t, 264, 150, { flip: true });
      }, (pg, S2) => {
        for (let i = 0; i < 6; i++) {            // 冒出来的爱心
          const ph = G.mod(t * 0.9 + i / 6, 1), [hx, hy] = S2(262 + (i % 3) * 6 - 6, 112);
          pg.globalAlpha = 1 - ph;
          G.f12.draw(pg, '♥', hx + Math.sin(ph * 8 + i) * 6, hy - ph * 60, i % 2 ? '#ff6aa8' : '#ff3c78', { align: 'center' });
          pg.globalAlpha = 1;
        }
      });
      g.restore();
      const q = G.ui.qte, hits = q && q.type === 'rhythm' ? q.state : st.hits;
      if (q && q.type === 'rhythm') st.hits = q.state.slice();
      'LOVE'.split('').forEach((L, i) => {
        if (hits && hits[i] === 1) { const d = G.D.ui.sfx[L]; if (d) img(g, d.image, 360 + d.ox, 90 + 21 * i + d.oy); }
      });
    }
    tag(g, 4);
  }
  async function v4(S) {
    const st = await newPage(S, drawV4, {});
    S.sfx('crowd', 0.4); S.sfx('cheer', 0.55);
    await S.wait(0.4);
    S.nameCard('otsu');
    S.sfx('slide_up', 0.6);
    await S.wait(1.4);
    await S.say('otsu', '大家～！今天也要跟着通酱一起嗨起来哦～！', { expr: 'happy' });
    st.split = st.now;
    S.sfx('whoosh', 0.5);
    await S.wait(0.4);
    await S.say('shinpachi', '亲卫队全体！跟着节拍——！', { expr: 'shout' });
    await S.rhythm({ label: '跟着节拍喊！L · O · V · E（按 J）', notes: [1.0, 1.5, 2.0, 2.5], window: 0.18, travel: 1.4 });
    S.sfx('applause', 0.5); S.sfx('cheer', 0.7);
    await S.say('shinpachi', '通酱～！！', { expr: 'happy' });
    await S.say('gintoki', '（……这眼镜，在道场里可从来没这么有气势过。）');
  }

  // ================================================================ 其五 醋昆布
  function drawV5(g, t, st) {
    paper(g);
    let k = 2.4 + 0.4 * easeIO(t / 2.6), cx = 162 + 6 * easeIO(t / 2.6), cy = 146;
    if (st.jumpT != null) { const u = ease((t - st.jumpT) / 0.14); k = G.lerp(k, 2.1, u); cx = G.lerp(cx, 166, u); cy = G.lerp(cy, 131, u); }
    panel(g, FULL, [k, cx, cy], [192, 104], (w) => {
      bgOf('daily_v5').draw(w, 0, t, NOST);
      const dog = st.hurtT != null ? ['sadaharu__s06', 'idle_hurt', t - st.hurtT] : st.jumpT != null ? ['sadaharu', 'shock', t - st.jumpT] : ['sadaharu', 'sleep', t];
      ch(w, dog[0], dog[1], dog[2], 160, 164);
      // 神乐：坐在定春背上嚼醋昆布 → 被弹上天 → 掉回来
      let ky = 147, show = true, squash = 0;
      if (st.jumpT != null) {
        const u = t - st.jumpT;
        if (u < 0.18) ky = G.lerp(147, 30, ease(u / 0.18));
        else if (st.dropT == null) show = false;
      }
      if (st.dropT != null) {
        const u = t - st.dropT;
        ky = u < 0.16 ? G.lerp(-30, 135, u / 0.16) : 135; show = true;
        if (u >= 0.16 && u < 0.3) squash = 2;
      }
      if (show) ch(w, 'kagura__s06', 'sukonbu_sit', t, 156, ky + squash);
      if (st.jumpT != null && t - st.jumpT < 0.3) for (let i = 0; i < 5; i++) px(w, 148 + i * 4, ky + 6 + (i % 2) * 6, 'rgb(255,250,230)', 1, 14);
      // 鼻涕泡
      if (st.popT == null) {
        const gg = G.clamp((t - 0.3) / 2.6, 0, 1), r = 1 + 6.5 * gg + (0.6 + gg) * Math.sin(5 * t);
        const bx = 180 + 0.9 * r, by = 154 - 0.2 * r;
        w.fillStyle = 'rgb(196,226,250)'; w.strokeStyle = 'rgb(90,130,170)'; w.lineWidth = 1;
        w.beginPath(); w.arc(bx, by, Math.max(1, r), 0, Math.PI * 2); w.fill(); w.stroke();
        px(w, bx - r * 0.4, by - r * 0.5, '#fff', 2, 1);
      } else if (t - st.popT < 0.4) {
        const u = (t - st.popT) / 0.4, rnd = G.prng(3);
        for (let i = 0; i < 16; i++) {
          const a = rnd() * Math.PI * 2, sp = 30 + rnd() * 40;
          px(w, 186 + Math.cos(a) * sp * u, 152 + Math.sin(a) * sp * u + 45 * u * u, i % 3 ? 'rgb(210,235,255)' : '#fff');
        }
      }
    });
    tag(g, 5);
  }
  async function v5(S) {
    const st = await newPage(S, drawV5, {});
    S.sfx('eat', 0.45);
    await S.wait(0.4);
    await S.say('kagura', '嚼嚼……醋昆布，果然是最棒的零食阿鲁。', { expr: 'happy' });
    await S.say('gintoki', '（……定春的鼻涕泡，越吹越大了。）');
    await S.timing({ label: '鼻涕泡越吹越大……看准时机戳破它！（按 J）', speed: 1.1, zone: [0.44, 0.58] });
    st.popT = st.now;
    S.sfx('pop', 0.9);
    word(st, '啪!', 220, 110, 0.6);
    await S.wait(0.05);
    st.jumpT = st.now;
    S.sfx('boing', 0.8); S.sfx('whoosh', 0.5, 1.3);
    word(st, '嘣!', 150, 150, 0.6);
    await S.wait(0.3);
    word(st, '？', 200, 70, 0.6);
    S.sfx('fall_whistle', 0.45, 2.6);
    await S.wait(0.5);
    st.dropT = st.now;
    await S.wait(0.16);
    S.sfx('thud', 0.9); S.shake(3, 0.25);
    st.hurtT = st.now + 0.25;
    await S.wait(0.4);
    word(st, '嚼嚼', 120, 120, 0.8);
    S.sfx('eat', 0.45);
    await S.wait(0.4);
    await S.say('kagura', '醋昆布就是正义阿鲁！', { expr: 'happy' });
    await S.say('gintoki', '……刚才那一下，你一点都不在意吗。');
  }

  // ================================================================ 其六 跟踪狂（阿妙家地板下）
  const TOP = [[6, 6], [378, 6], [378, 90], [6, 98]];
  const BOT = [[6, 104], [378, 96], [378, 210], [6, 210]];
  function drawV6(g, t, st) {
    paper(g);
    panel(g, TOP, [2.0, 176, 124], [192, 52], (w) => {
      bgOf('daily_v6_room').draw(w, 0, t, NOST);
      const pose = st.stabT != null ? ['otae__s06', 'stab_down', t - st.stabT] : st.riseT != null ? ['otae__s06', 'rise_dark', t - st.riseT]
        : st.darkT != null ? ['otae__s06', 'sit_dark', t] : ['otae', 'sit', t];
      ch(w, pose[0], pose[1], pose[2], 170, 146);
      if (st.stabT != null) {                    // 薙刀刺进地板：把地板那几行盖回来
        const fo = G.D.bg.daily_v6_room.floor_overlay;
        img(w, fo.image, fo.x, fo.y);
        px(w, 178, 147, INK); px(w, 180, 147, INK);
      }
    }, (pg) => {
      if (st.darkT != null && st.stabT == null) {
        const n = Math.min(3, 1 + Math.floor((st.now - st.darkT) / 0.12));
        for (let i = 0; i < n; i++) { const d = G.D.ui.sfx['ゴ']; if (d) img(pg, d.image, 250 + i * 18 + d.ox, 30 + i * 8 + d.oy); }
      }
    });
    panel(g, BOT, [2.4, 159.08, 117.5], [192, 136], (w) => {
      bgOf('daily_v6_crawl').draw(w, 0, t, NOST);
      w.save(); w.globalCompositeOperation = 'lighter';     // 从地板缝漏下来的光
      [160.6, 205.6, 91.6, 257.6].forEach((gx, i) => {
        const b = 0.8 + 0.2 * Math.sin(3 * t + i);
        w.fillStyle = `rgba(255,236,190,${(0.12 * b).toFixed(3)})`;
        w.beginPath(); w.moveTo(gx, 103); w.lineTo(gx + 2, 103); w.lineTo(gx + 2 + 12, 138); w.lineTo(gx + 12, 138); w.closePath(); w.fill();
      });
      w.restore();
      if (st.stabT != null) ch(w, 'kondo__s06', 'frozen', t - st.stabT, 150, 138);
      else {
        ch(w, 'kondo__s06', 'stalk_nobush', t, 150, 138);
        for (let i = 0; i < 3; i++) {             // 飘起来的爱心
          const ph = G.mod(t * 0.7 + i / 3, 1);
          w.globalAlpha = 1 - ph;
          px(w, 156 + i * 5 + Math.sin(ph * 7) * 2, 112 - ph * 12, 'rgb(255,90,140)', 2, 2);
          w.globalAlpha = 1;
        }
      }
    }, (pg, S2) => {
      if (st.stabT != null && st.now - st.stabT < 0.8) {   // 集中线
        const rnd = G.prng(5 + Math.floor(st.now * 15));
        pg.fillStyle = 'rgba(255,255,255,0.8)'; pg.beginPath();
        const [cx, cy] = S2(152, 120);
        for (let i = 0; i < 30; i++) {
          const a = rnd() * Math.PI * 2, wd = 0.02 + rnd() * 0.03;
          pg.moveTo(cx + Math.cos(a) * 46, cy + Math.sin(a) * 46);
          pg.lineTo(cx + Math.cos(a - wd) * 300, cy + Math.sin(a - wd) * 300); pg.lineTo(cx + Math.cos(a + wd) * 300, cy + Math.sin(a + wd) * 300); pg.closePath();
        }
        pg.fill();
      }
    });
    if (st.stabT != null) {                       // 薙刀穿过两个格子之间的空白，刀尖停在近藤鼻子前
      const u = G.clamp((t - st.stabT) / 0.06, 0, 1), tip = G.lerp(100, 144.4, u);
      px(g, 195, 0, INK, 6, Math.max(0, tip - 18));
      px(g, 196, 0, 'rgb(150,96,60)', 4, Math.max(0, tip - 18));
      px(g, 194, tip - 20, 'rgb(220,180,60)', 8, 2);
      px(g, 196, tip - 18, 'rgb(200,210,228)', 4, 18);
      px(g, 198, tip - 18, '#fff', 1, 17);
    }
    if (st.capT != null) {
      const u = G.clamp((t - st.capT) / 0.14, 0, 1);
      img(g, PR().caption_daily, 300, 100, { center: true, scale: 1.8 - 0.8 * u });
    }
    if (st.crowT != null) {                       // 大乌鸦飞过页面上方：「阿呆～」
      const u = (t - st.crowT) / 1.1;
      if (u < 1) {
        const f = Math.floor(t * 8) % 4, caw = u > 0.14 && u < 0.5;
        img(g, PR()[`crow_big${f}${caw ? 'c' : ''}`], G.lerp(G.W + 24, 20, u) - 22, 22 + Math.sin(t * 10) * 3 - 17);
      }
    }
    tag(g, 6);
  }
  async function v6(S) {
    const st = await newPage(S, drawV6, {});
    await S.wait(0.5);
    await S.say('kondo', '阿妙小姐……今天也好美。', { expr: 'love' });
    await S.say('otae', '……今天的茶，好像有一股猩猩的味道呢～', { expr: 'happy' });
    st.darkT = st.now;
    S.sfx('aura', 0.7);
    await S.wait(0.5);
    const c = await S.choice(['左边的榻榻米', '茶杯旁边', '右边的榻榻米'], '阿妙拿起了薙刀。往哪里刺？');
    st.riseT = st.now;
    S.sfx('shing', 0.6);
    await S.wait(0.4);
    st.stabT = st.now;
    S.sfx('stab', 1.0); S.sfx('impact', 0.8);
    S.shake(5, 0.45);
    word(st, '咚!!', 250, 130, 0.9);
    await S.wait(0.3);
    S.sfx('shock', 0.6);
    await S.wait(0.4);
    await S.say('kondo', '…………………………', { expr: 'shock' });
    if (c === 1) await S.say(null, '（明明选的是茶杯旁边。刀尖还是正好停在了近藤的鼻子前面。）');
    else await S.say(null, '（不管往哪里刺，刀尖都会正好停在近藤的鼻子前面。这就是阿妙。）');
    st.capT = st.now;
    S.sfx('sweat', 0.6); S.sfx('rimshot', 0.8);
    await S.wait(0.6);
    st.crowT = st.now;
    S.sfx('crow', 0.8);
    await S.wait(0.3);
    word(st, '阿呆～', 200, 40, 0.8);
    await S.wait(1.4);
  }

  // ================================================================ 第六章主流程
  G.STORY.chapter6 = async function (S) {
    G.STAGES.daily_ch6 = { id: 'daily_ch6', bg: 'daily_v5', x0: 0, x1: G.W, yMin: 170, yMax: 200, props: [] };
    G.fadeAlpha = 0;
    G.world.stage = null;
    await S.chapterCard('ch6');
    const p = new G.Actor('gintoki', 192, 190, { id: 'player', team: 'player', hp: 100, speed: 72, name: '银时' });
    G.world.player = p;
    G.fadeAlpha = 1;
    await S.setStage('daily_ch6', { x: 192, y: 190, facing: 1, fade: false });
    p.visible = false;
    cur = null; turn = null;
    S.insert(root);
    S.music('comedy', 0.5);
    await S.fadeIn(0.5);
    await S.run(async (S) => {
      await v1(S);
      await v2(S);
      await v3(S);
      await v4(S);
      await v5(S);
      await v6(S);
      await S.fadeOut(1.0);
      S.insert(null);
      G.ui.waitKey = false;
      cur = null;
      G.flags.ch6Done = true;
    });
    await S.until(() => G.flags.ch6Done);
  };
})();
