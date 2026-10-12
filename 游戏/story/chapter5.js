// 第五章：桂与伊丽莎白（原片 s05）
//   黄昏的歌舞伎町：举着牌子找人的谜之生物 → 桂从屋顶掉下来，土方拔刀追来 → 银时被拖上屋顶
//   → 屋顶跑酷（跳过屋顶缝；冲田的准星锁定后开炮，要躲）→ 桂急停：「假发——」「不是假发，是桂！」
//   → 和冲田过招（撑 15 秒或打到半血）→ 桂扔炸弹，冲田一挡，炸弹飞上了天 → 银时跳回大街
//   → 炸弹正好掉进手里，看准时机往天上扔 → 「桂」字烟花，冲田和土方的逆光剪影
//   → 一颗火星掉下来：满脸黑灰的爆炸头「为什么每次倒霉的都是我啊！」
'use strict';
(function () {
  const G = window.G;
  const F = () => G.flags;
  const count = (key) => (G.flags[key] = (G.flags[key] || 0) + 1);
  const SP = () => G.D.bg.ch5;           // 第五章的小道具（tools/bg_chapters.py 的 ch5 导出）
  const sweat = (a, dx = 7) => G.fx.img(G.D.bg.ch2.sweat.image, a.x + dx, a.headY() + 4, { vy: 7, life: 0.9, fade: true });
  const frame = (fr, fps, t) => fr[G.mod(Math.floor(t * fps + 1e-6), fr.length)];
  const px = (g, x, y, c, w = 1, h = 1) => { g.fillStyle = c; g.fillRect(Math.round(x), Math.round(y), w, h); };
  function line(g, x0, y0, x1, y1, c, w = 1) {
    g.fillStyle = c;
    const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)) | 0;
    for (let i = 0; i <= n; i++) { const k = n ? i / n : 0; g.fillRect(Math.round(x0 + (x1 - x0) * k), Math.round(y0 + (y1 - y0) * k), w, w); }
  }
  // 原片 s05 的特殊动作（爆炸头、扛着火箭筒跑……）在「角色__s05」图集里
  const ALT = { gintoki: 'gintoki__s05', katsura: 'katsura__s05', okita: 'okita__s05', hijikata: 'hijikata__s05' };
  function gear(a) { const id = ALT[a.cid]; if (id && G.D.chars[id]) a.alt = [G.atlas(id)]; return a; }

  // 伊丽莎白只用牌子说话：图集里自带一块小牌子，牌子 prop 正好盖在它上面（朝右时在脚点右上 (23, -33)）
  async function sign(S, a, text, o = {}) {
    a = S.actor(a);
    S.pose(a, 'sign_loop', { restart: true });
    const p = S.prop({ type: 'sign', text, x: a.x + a.facing * 23, y: a.y - 31, depth: a.y + 0.5, pole: false, minW: 34, minH: 18 });
    S.sfx('pop', 0.5);
    await S.say('elizabeth', `［牌子］${text.replace(/\n/g, '')}`, { actor: a, name: '伊丽莎白' });
    if (!o.keep) { S.unprop(p); S.unpose(a); }
    return p;
  }

  // 爆炸：火球（白→黄→橙→红）+ 碎片 + 尘土 + 拟声字
  function boom(S, x, y, size = 22, word = '轰!') {
    S.sfx(size > 40 ? 'explosion' : 'explosion_small', 0.9);
    S.shake(size > 40 ? 5 : 4, size > 40 ? 0.45 : 0.35);
    G.fx.debris(x, y - 8, ['#ffd040', '#ff8a2a', '#ff4a20', '#584848', '#606480'], Math.round(size * 0.9), [40, 150], 200, 0.8);
    G.fx.dust(x, y, 10);
    if (word) G.fx.word(word, x, y - 30 - size * 0.3, 0.9);
    const st = G.world.stage, t0 = st.t, rnd = G.prng(Math.floor(x * 7 + y * 13));
    const balls = Array.from({ length: 8 }, () => ({ a: rnd() * Math.PI * 2, d: rnd() * size * 0.5, r: size * (0.22 + rnd() * 0.22) }));
    const cols = ['255,255,240', '255,230,120', '254,174,52', '220,80,40', '90,70,70'];
    const pr = S.prop({ type: 'custom', x, y, depth: y + 2, draw: (g, sx, sy, t) => {
      const k = (t - t0) / 0.7;
      if (k < 0 || k > 1) return;
      if (k < 0.18) { g.fillStyle = `rgba(255,255,230,${1 - k / 0.18})`; g.beginPath(); g.arc(sx, sy - size * 0.4, size * (0.4 + k * 3), 0, Math.PI * 2); g.fill(); }
      const c = cols[Math.min(4, Math.floor(k * 5))];
      g.fillStyle = `rgba(${c},${1 - k * 0.8})`;
      for (const b of balls) {
        const r = Math.max(0.5, b.r * (1 - k * 0.6));
        g.beginPath();
        g.arc(sx + Math.cos(b.a) * b.d * (0.5 + k), sy - size * 0.4 + Math.sin(b.a) * b.d * 0.6 * (0.5 + k) - k * size * 0.4, r, 0, Math.PI * 2);
        g.fill();
      }
    } });
    G.world.ticks.push(() => { if (st.t - t0 > 0.75) { S.unprop(pr); return true; } return false; });
  }

  // ================================================================ 黄昏的大街
  async function talkEliz(S, a) {
    const n = count('eliz');
    if (n === 1) {
      await sign(S, a, '……');
      await S.say('gintoki', '……你是什么东西。企鹅？鸭子？还是谁家走丢的吉祥物？');
      await sign(S, a, '我在找人');
      await S.say('gintoki', '会说话……不对，是会举牌子。');
      await sign(S, a, '长头发的笨蛋');
      await S.say('gintoki', '……这个描述，我好像认识一个。');
      F().eliz = true;
    } else await sign(S, a, '长头发的\n笨蛋');
  }
  function noticeBoard(x, y) {     // 街边的告示板：一张桂的通缉令 + 一张别的告示
    return { type: 'custom', x, y, depth: y, draw: (g, sx, sy) => {
      g.fillStyle = '#3a2820'; g.fillRect(sx - 18, sy - 30, 2, 30); g.fillRect(sx + 16, sy - 30, 2, 30);
      g.fillStyle = '#1a1424'; g.fillRect(sx - 21, sy - 37, 42, 22);
      g.fillStyle = '#6a4a34'; g.fillRect(sx - 20, sy - 36, 40, 20);
      g.fillStyle = '#4a3226'; g.fillRect(sx - 23, sy - 40, 46, 3);
      g.fillStyle = '#efe6cc'; g.fillRect(sx - 17, sy - 35, 16, 18);
      const hd = G.head('katsura', 'normal');
      if (hd && G.ready(hd)) g.drawImage(hd, sx - 16, sy - 34, 14, 13);
      g.fillStyle = '#c03a30'; g.fillRect(sx - 7, sy - 21, 5, 3);
      g.fillStyle = '#d8d0e0'; g.fillRect(sx + 2, sy - 34, 14, 11);
      g.fillStyle = '#8a8498'; g.fillRect(sx + 4, sy - 32, 10, 1); g.fillRect(sx + 4, sy - 30, 8, 1); g.fillRect(sx + 4, sy - 28, 10, 1); g.fillRect(sx + 4, sy - 26, 6, 1);
    } };
  }

  // 桂从屋顶掉下来，土方追来
  async function katsuraDrops(S) {
    const p = S.player, e = S.actor('elizabeth'), st = G.world.stage;
    F().met = true;
    S.letterbox(true);
    S.sfx('fall_whistle', 0.6);
    const k = gear(S.spawn('katsura', p.x + 34, p.y, { id: 'katsura', name: '桂', facing: -1 }));
    k.z = 120;
    await S.arc(k, p.x + 34, p.y, 6, 0.55, { anim: 'jump', z1: 0 });
    S.sfx('land', 0.8); S.shake(2, 0.2);
    G.fx.dust(k.x, k.y, 8);
    S.unpose(k);
    S.face(p, k);
    S.emote(p, '!', 0.5);
    await S.say('katsura', '银时！好久不见！', { actor: k, expr: 'happy' });
    await S.say('gintoki', '……假发？你怎么从天上掉下来了。');
    await S.say('katsura', '不是假发，是桂！', { actor: k, expr: 'angry' });
    if (e) {
      await S.walk(e, k.x + 30, k.y + 4, { speed: 70 });
      e.facing = -1;
      await sign(S, e, '桂先生！');
      await S.say('katsura', '伊丽莎白！你在找我吗……辛苦你了。', { actor: k, expr: 'happy' });
      await S.say('gintoki', '……原来长头发的笨蛋就是你啊。');
    }
    // 远处的喊声：真选组的副长拔着刀冲过来
    S.sfx('run', 0.6);
    const h = gear(S.spawn('hijikata', st.camX - 30, p.y - 4, { id: 'hijikata', name: '土方', facing: 1 }));
    S.pose(h, 'run_katana');
    await S.animate(0.8, (u) => { h.x = st.camX - 30 + u * 90; });
    G.fx.word('站住!!', h.x + 10, h.y - 44, 1.0);
    S.sfx('vein', 0.5);
    await S.say('hijikata', '给我站住，桂！', { actor: h, expr: 'shout' });
    await S.say('katsura', '真选组！银时，跟我走——上屋顶！', { actor: k, expr: 'determined' });
    await S.say('gintoki', '为什么我也要跑啊！？', { expr: 'shock' });
    await S.say('katsura', '你现在站在我旁边。在真选组眼里，就是同伙。', { actor: k });
    await S.say('gintoki', '……这家伙每次都这样。', { expr: 'gloom' });
    S.letterbox(false);
    await roofChase(S);
  }

  // ================================================================ 屋顶跑酷
  const ROOF_END = 1500;
  async function roofChase(S) {
    const p = S.player, sp = SP();
    await S.fadeOut(0.4);
    await S.setStage('roofs_ch5', { x: 120, y: 160, facing: 1, fade: false });
    const st = G.world.stage;
    const k = gear(S.spawn('katsura', 214, 152, { id: 'katsura', name: '桂', facing: 1 }));
    const e = S.spawn('elizabeth', 252, 160, { id: 'elizabeth', name: '伊丽莎白', facing: 1 });
    const h = gear(S.spawn('hijikata', 22, 168, { id: 'hijikata', name: '土方', facing: 1 }));
    const o = gear(S.spawn('okita', 48, 154, { id: 'okita', name: '冲田', facing: 1 }));
    for (const a of [k, e, h, o]) a.hold = true;
    k.play('run_away'); e.play('run'); h.play('run_katana'); o.play('run_bazooka');
    await S.fadeIn(0.4);
    S.hint('屋顶上逃跑：K 跳过屋顶之间的缝；准星变红就是冲田要开炮了——↑↓ 换位置、←→ 前后挪或者跳起来躲开', 8);
    // 冲田的瞄准 → 锁定 → 开炮（伤害自己算：world.explode 会把人打倒，卷轴就断了）
    const fx = { last: -1 };
    const reset = () => Object.assign(fx, { next: 2.0, phase: null, ring: null, lock: null, shell: null, marks: [] });
    reset();
    const overlay = S.prop({ type: 'custom', x: 0, y: 0, depth: 9999, draw: (g) => drawChaseFx(g, fx) });
    const obstacles = [420, 700, 980, 1240, 1460].map((x) => ({ x, y: 160, w: 22, h: 14, tall: 12, dmg: 12, word: '呜哇!', sfx: 'fall_whistle',
      prop: { image: sp.gap.image, ax: 12, ay: 13, depth: 140 } }));
    await S.runner({
      cam0: 0, endX: ROOF_END, speed: 96, y: 160, rx: 120, obstacles,
      onTick: (dt, t) => {
        if (t < fx.last) reset();
        fx.last = t;
        const cx = st.camX;
        k.x = cx + 214 + Math.sin(t * 2.2) * 4; k.y = 152;
        e.x = cx + 252 + Math.sin(t * 1.7 + 1) * 3; e.y = 160;
        h.x = cx + 22 + Math.sin(t * 1.3) * 6; h.y = 168;
        o.x = cx + 48 + Math.sin(t * 1.1 + 2) * 5; o.y = 154;
        chaseTick(S, fx, dt, t);
      },
    });
    S.unprop(overlay);
    await zuraMoment(S);
  }
  function chaseTick(S, fx, dt, t) {
    const p = S.player, st = G.world.stage;
    if (!fx.phase && t >= fx.next) { fx.phase = 'aim'; fx.t0 = t; fx.ring = { x: p.rx, y: p.y - 14 }; S.sfx('blip', 0.4, 1.3); }
    if (fx.phase === 'aim') {
      fx.ring.x += (p.rx - fx.ring.x) * Math.min(1, dt * 8);
      fx.ring.y += (p.y - 14 - p.z - fx.ring.y) * Math.min(1, dt * 8);
      if (Math.floor((t - fx.t0) * 3) !== Math.floor((t - fx.t0 - dt) * 3)) S.sfx('blip', 0.3, 1.5);
      if (t - fx.t0 >= 1.0) { fx.phase = 'lock'; fx.t0 = t; fx.lock = { x: p.rx, y: p.y }; fx.ring = { x: p.rx, y: p.y - 14 }; S.sfx('blip', 0.6, 0.8); }
    } else if (fx.phase === 'lock' && t - fx.t0 >= 0.55) {
      const o = S.actor('okita');
      fx.phase = 'shell'; fx.t0 = t;
      fx.shell = { x0: o.x - st.camX + 12, y0: o.y - 22 };
      S.sfx('bazooka', 0.6); S.sfx('whoosh', 0.5);
      G.fx.spark(o.x + 14, o.y - 22, '#fff4c0', 5);
    } else if (fx.phase === 'shell' && t - fx.t0 >= 0.5) {
      const bx = st.camX + fx.lock.x, by = fx.lock.y;
      boom(S, bx, by, 22);
      if (Math.abs(p.rx - fx.lock.x) < 18 && Math.abs(p.y - fx.lock.y) < 8 && p.z < 12 && p.invuln <= 0) {
        p.hp -= 14; p.invuln = 1.0; p.flash = 1;
        G.fx.word('呜哇!', p.x, p.y - 40);
      }
      fx.marks.push({ x: bx, y: by, t });
      Object.assign(fx, { phase: null, next: t + 1.05, shell: null, lock: null, ring: null });
    }
  }
  function drawChaseFx(g, fx) {
    const sp = SP(), st = G.world.stage, t = fx.last;
    for (const m of fx.marks) {          // 焦痕，冒着烟
      const x = Math.round(m.x - st.camX), y = m.y;
      if (x < -20 || x > G.W + 20) continue;
      px(g, x - 9, y - 2, 'rgb(40,30,40)', 18, 4);
      px(g, x - 5, y - 1, 'rgb(24,18,26)', 10, 2);
      for (let i = 0; i < 3; i++) {
        const k = ((t - m.t) * 0.9 + i / 3) % 1;
        px(g, x - 4 + i * 4, y - 4 - Math.round(k * 20), `rgba(150,140,150,${(0.6 * (1 - k)).toFixed(2)})`, 2, 2);
      }
    }
    if (fx.ring) {
      const red = fx.phase !== 'aim';
      const im = G.image((red ? sp.scope_red : sp.scope_green).image);
      if (G.ready(im)) g.drawImage(im, Math.round(fx.ring.x - im.width / 2), Math.round(fx.ring.y - im.height / 2));
      if (red && Math.floor(t * 8) % 2 === 0) G.f12.draw(g, '锁定', Math.round(fx.ring.x), Math.round(fx.ring.y) - 30, '#ff5a5a', { align: 'center', outline: '#1a1020' });
    }
    if (fx.shell && fx.lock) {
      const k = Math.min(1, (t - fx.t0) / 0.5);
      const pos = (kk) => [G.lerp(fx.shell.x0, fx.lock.x, kk), G.lerp(fx.shell.y0, fx.lock.y - 4, kk) - 72 * kk * (1 - kk)];
      for (let i = 5; i >= 1; i--) {
        const [tx, ty] = pos(Math.max(0, k - i * 0.06)), r = 1 + Math.round(i * 0.45);
        px(g, tx - r, ty - r, i < 3 ? 'rgba(236,230,226,0.85)' : 'rgba(190,182,190,0.6)', 2 * r, 2 * r);
      }
      const [x, y] = pos(k), im = G.image(sp.shell.image);
      if (G.ready(im)) {
        g.drawImage(im, Math.round(x - im.width / 2), Math.round(y - im.height / 2));
        px(g, x - im.width / 2 - 3 - (Math.floor(t * 24) % 3), y - 1, 'rgb(255,200,60)', 3 + (Math.floor(t * 24) % 3), 2);
      }
    }
  }

  // 「不是假发，是桂！」特写：蓝底 + 两层集中线 + 放大 4 倍的桂 + 毛笔大字砸下来
  function zuraInsert(g, t) {
    g.drawImage(G.image(SP().closeup_bg), 0, 0);
    const rnd = G.prng(11 + Math.floor(t * 15));
    for (const [n, inner, col] of [[56, 70, 'rgba(210,226,255,0.85)'], [26, 86, 'rgba(255,255,255,0.95)']]) {
      g.fillStyle = col;
      g.beginPath();
      for (let i = 0; i < n; i++) {
        const a = rnd() * Math.PI * 2, w = 0.01 + rnd() * 0.02, ri = inner + rnd() * 30;
        g.moveTo(298 + Math.cos(a) * ri, 84 + Math.sin(a) * ri);
        g.lineTo(298 + Math.cos(a - w) * 460, 84 + Math.sin(a - w) * 460);
        g.lineTo(298 + Math.cos(a + w) * 460, 84 + Math.sin(a + w) * 460);
        g.closePath();
      }
      g.fill();
    }
    const at = G.atlas('katsura'), an = at.anim('point');
    at.draw(g, 'point', Math.min(an.frames - 1, Math.floor(t / 1.2 * an.frames)), 306, 190, { scale: 4, flip: true });
    const slam = (key, t0, cx, cy, jitter) => {
      if (t < t0) return;
      const im = G.image(G.D.ui.texts[key].image);
      const s = 1 + 1.4 * Math.max(0, 1 - (t - t0) / 0.14);
      const jx = jitter ? Math.round(Math.sin(t * 60) * 2 * Math.max(0, 1 - (t - t0) / 0.5)) : 0;
      g.drawImage(im, Math.round(cx - im.width * s / 2) + jx, Math.round(cy - im.height * s / 2), Math.round(im.width * s), Math.round(im.height * s));
    };
    slam('zura_1', 0.07, 104, 58, false);
    slam('zura_2', 0.43, 112, 116, true);
  }

  async function zuraMoment(S) {
    const p = S.player, st = G.world.stage, cx = st.camX;
    const k = S.actor('katsura'), e = S.actor('elizabeth'), h = S.actor('hijikata'), o = S.actor('okita');
    S.letterbox(true);
    // 桂急停、回头
    S.pose(k, 'skid');
    S.sfx('record_scratch', 0.7);
    G.fx.word('嘎——!', k.x + 14, k.y - 46, 0.9);
    for (let i = 0; i < 4; i++) G.fx.dust(k.x - 6 - i * 6, k.y, 3);
    S.pose(e, 'idle');
    await S.animate(0.35, (u) => { k.x = cx + 214 + u * 12; });
    k.facing = -1; e.facing = -1;
    S.pose(k, 'angry_turn');
    S.sfx('whoosh', 0.5);
    await Promise.all([S.walk(p, cx + 150, 160, { speed: 80 }), (async () => { S.pose(h, 'idle'); S.pose(o, 'idle'); })()]);
    p.facing = -1;
    await Promise.all([S.walk(h, cx + 60, 166, { speed: 70 }), S.walk(o, cx + 92, 154, { speed: 70 })]);
    h.facing = 1; o.facing = 1;
    S.pose(o, 'bazooka_sadist');
    S.sfx('aura', 0.5);
    await S.say('okita', '假发——', { actor: o, expr: 'sadist' });
    // 特写
    S.insert(zuraInsert);
    S.sfx('shine', 0.5);
    await S.wait(0.07);
    S.sfx('impact', 0.7);
    await S.wait(0.36);
    S.sfx('punch_big', 0.8); S.sfx('impact', 0.8);
    S.flash(0.17, 0.7);
    await S.wait(0.5);
    await S.say('katsura', '不是假发，是桂！', { actor: k, expr: 'shout' });
    S.insert(null);
    S.pose(k, 'smug_arm');
    S.nameCard('katsura@s05');
    S.sfx('slide_up', 0.4);
    await S.wait(1.4);
    // 伊丽莎白举牌「……」；一发流弹在后面炸了 → 「快跑」
    const s1 = await sign(S, e, '……', { keep: true });
    S.sfx('crow', 0.5);
    await S.wait(0.6);
    S.sfx('whoosh', 0.7);
    await S.wait(0.2);
    boom(S, e.x + 46, e.y - 6, 22, '轰!!');
    S.unprop(s1);
    S.nameCard('elizabeth');
    S.sfx('slide_up', 0.35);
    sweat(e, 4);
    const s2 = await sign(S, e, '快跑', { keep: true });
    S.unprop(s2); S.unpose(e);
    S.pose(k, 'idle_shock');
    await S.say('hijikata', '这次跑不掉了，桂！还有你这天然卷，窝藏攘夷志士——', { actor: h, expr: 'angry' });
    await S.say('gintoki', '谁窝藏了！是他自己从天上掉下来的！', { expr: 'shout' });
    S.unpose(o);
    await S.say('okita', '土方先生，天然卷交给我。……要是不小心把土方先生也炸飞了，那也是意外。', { actor: o, expr: 'smug' });
    S.emote(h, '💢', 0.8, '#ff5050');
    S.sfx('vein', 0.6);
    await S.say('hijikata', '你小子刚才说什么！？', { actor: h, expr: 'angry' });
    S.unpose(k);
    await S.say('katsura', '银时，替我挡一会儿！我需要准备一点东西。', { actor: k, expr: 'determined' });
    await S.say('gintoki', '……事后请我吃芭菲。三份。');
    S.letterbox(false);
    // 和冲田过招：土方在一旁抽烟看着
    S.pose(h, 'smoke');
    h.x = cx + 30; h.y = 170;
    S.hint('和冲田过招！撑 15 秒，或者把他打到半血', 6);
    await S.fight({
      arena: [cx + 8, cx + 376],
      waves: [[{ actor: 'okita', cid: 'okita', name: '一番队队长 冲田总悟', hp: 120, boss: true, speed: 56, range: 26, minHp: 1,
        moves: ['E_SLASH', 'E_SLASH', 'E_BAZOOKA'] }]],
      timer: { label: '桂准备好还有 ', until: 15 },
      endWhen: () => { const b = S.actor('okita'); return G.world.fightT >= 15 || !!(b && b.hp <= 60); },
      music: 'battle',
      after: 'comedy',
    });
    o.team = 'npc'; o.name = '冲田'; G.ui.boss = null;
    await bombEscape(S);
  }

  // 桂点炸弹「后会有期！」→ 冲田用火箭筒一挡，炸弹飞上天 → 桂和伊丽莎白跑了，真选组追过去
  async function bombEscape(S) {
    const p = S.player, sp = SP(), st = G.world.stage, cx = st.camX;
    const k = S.actor('katsura'), e = S.actor('elizabeth'), h = S.actor('hijikata'), o = S.actor('okita');
    S.letterbox(true);
    S.unpose(o); S.unpose(h);
    o.x = G.clamp(o.x, cx + 40, cx + 200); o.facing = 1;
    S.face(p, o);
    await S.say('okita', '……天然卷，还挺能打的嘛。', { actor: o, expr: 'smug' });
    k.facing = -1;
    S.pose(k, 'bomb', { restart: true });
    S.sfx('bomb_fuse', 0.7);
    G.fx.word('嗤嗤…', k.x - 6, k.y - 40, 1.0);
    await S.say('katsura', '久等了！', { actor: k, expr: 'smug' });
    await S.say('katsura', '后会有期！', { actor: k, expr: 'happy' });
    S.pose(k, 'bomb_throw', { restart: true });
    await S.wait(0.25);
    S.sfx('whoosh', 0.7);
    // 炸弹飞向冲田 → 一挡 → 飞上天
    const b = S.prop({ type: 'custom', x: k.x - 8, y: k.y, z: 30, depth: 300, draw: (g, x, y, t) => {
      const im = G.image(frame(sp.bomb.frames, 12, t));
      if (G.ready(im)) g.drawImage(im, x - sp.bomb.ax, Math.round(y - b.z) - sp.bomb.ay);
    } });
    const x0 = b.x, x1 = o.x + 12;
    await S.animate(0.45, (u) => { b.x = G.lerp(x0, x1, u); b.y = G.lerp(k.y, o.y, u); b.z = 30 + 26 * 4 * u * (1 - u); });
    S.act(o, 'attack');
    S.sfx('clang', 0.8);
    G.fx.word('啪!', o.x + 10, o.y - 40, 0.6);
    G.fx.word('咻——', o.x - 20, o.y - 70, 0.9);
    const bx = b.x;
    await S.animate(0.6, (u) => { b.x = bx - u * 120; b.z = 30 + u * 200; });
    S.unprop(b);
    // 桂和伊丽莎白一溜烟跑了
    S.unpose(k); S.unpose(e);
    k.facing = 1; e.facing = 1;
    S.sfx('dash', 0.8);
    G.fx.dust(k.x, k.y, 10); G.fx.dust(e.x, e.y, 10);
    await Promise.all([S.walk(k, cx + 440, k.y, { speed: 240, anim: 'run_away' }), S.walk(e, cx + 460, e.y, { speed: 230, anim: 'run_away' })]);
    S.remove(k); S.remove(e);
    await S.say('okita', '啊，跑了。', { actor: o });
    await S.say('hijikata', '追！还愣着干什么！', { actor: h, expr: 'shout' });
    await Promise.all([S.walk(h, cx + 440, h.y, { speed: 160, anim: 'run' }), S.walk(o, cx + 420, o.y, { speed: 120, anim: 'run' })]);
    S.remove(h); S.remove(o);
    p.facing = 1;
    await S.wait(0.4);
    await S.say('gintoki', '……刚才飞上天的那个，是炸弹吧。往哪儿去了？');
    await S.say('gintoki', '……算了。不关我的事。回家。');
    S.sfx('jump', 0.6);
    await S.arc(p, p.x + 30, p.y + 6, 26, 0.45, { anim: 'jump' });
    await S.fadeOut(0.4);
    S.letterbox(false);
    await bombCatch(S);
  }

  // ================================================================ 回到大街：炸弹掉进手里
  async function bombCatch(S) {
    const p = gear(S.player), sp = SP();
    await S.setStage('street_dusk_ch5b', { x: 336, y: 182, facing: 1, fade: false });
    p.z = 70;
    await S.fadeIn(0.4);
    await S.arc(p, 346, 182, 2, 0.35, { anim: 'jump', z1: 0 });
    S.sfx('land', 0.8); G.fx.dust(p.x, p.y, 8);
    S.unpose(p);
    S.letterbox(true);
    await S.say('gintoki', '……总算甩掉了。今天一个委托都没接，怎么比打工还累。');
    const tm = S.spawn('townsman__v2', p.x + 76, p.y - 6, { id: 'oldman', name: '路过的大叔', facing: -1 });
    S.walk(tm, p.x + 44, p.y - 6, { speed: 18 });
    // 头顶上：哔——的哨音，一颗冒着火花的炸弹掉下来
    S.sfx('fall_whistle', 0.7);
    const bomb = S.prop({ type: 'custom', x: p.x + 9, y: p.y, z: 210, depth: p.y + 1, draw: (g, x, y, t) => {
      const im = G.image(frame(sp.bomb.frames, 12, t));
      if (G.ready(im)) g.drawImage(im, x - sp.bomb.ax, Math.round(y - bomb.z) - sp.bomb.ay);
    } });
    await S.animate(0.6, (u) => { bomb.z = G.lerp(210, 26, u * u); });
    S.pose(p, 'catch', { restart: true });
    S.sfx('slap', 0.4);
    G.fx.word('啪', p.x + 14, p.y - 38, 0.5);
    await S.animate(0.12, (u) => { bomb.z = 26 + 3 * Math.sin(u * Math.PI); });
    S.pose(p, 'hold_bomb');
    await S.wait(0.3);
    G.fx.word('？', p.x - 2, p.y - 48, 0.7);
    S.sfx('bomb_fuse', 0.6);
    await S.wait(0.4);
    await S.say('gintoki', '……嗯？圆圆的，还冒着火星……');
    // 反应过来：一下子推近到脸上
    S.pose(p, 'hold_bomb_shock');
    S.zoom(3.1, p, -26, 0.12);
    S.sfx('shock', 0.8); S.sfx('sweat', 0.6);
    S.flash(0.1, 0.6);
    G.fx.speedLines(192, 100, { count: 44, inner: 84, life: 0.9, color: '#ffffff' });
    G.fx.word('！？', p.x - 16, p.y - 40, 0.9);
    sweat(p);
    await S.wait(0.6);
    await S.say('gintoki', '炸、炸弹！？', { expr: 'shock' });
    await S.zoom(1, null, null, 0.25);
    S.emote(tm, '!!', 0.6);
    await S.say('townsman', '哇啊啊！炸弹啊——！', { name: '路过的大叔', actor: tm });
    S.walk(tm, p.x + 420, p.y - 6, { speed: 190, anim: 'run_away' });
    await S.say('gintoki', '等等！别丢下我一个人啊！……扔、扔哪儿！？', { expr: 'shock' });
    S.letterbox(false);
    const ok = await S.timing({ label: '往天上扔！看准时机按 J', speed: 1.5, zone: [0.44, 0.56], tries: 2 });
    S.letterbox(true);
    S.remove(tm);
    if (ok) {
      S.pose(p, 'throw_up', { restart: true });
      S.sfx('whoosh', 0.9);
      G.fx.word('嘿咻!', p.x + 22, p.y - 52, 0.6);
      await S.animate(0.45, (u) => { bomb.z = G.lerp(26, 260, u); });
      S.unprop(bomb);
      await S.wait(0.3);
      await S.say('gintoki', '……呼。飞得真高。');
      const px0 = p.x, py0 = p.y;
      await fireworks(S);
      await S.setStage('street_dusk_ch5b', { x: px0, y: py0, facing: 1, fade: false });
      S.unpose(p);
      p.visible = true;
    } else {
      S.unprop(bomb);
    }
    await sootEnding(S, ok);
  }

  // ================================================================ 烟花（原片 S5：低机位的天空，冲田和土方的逆光剪影）
  const FW = {
    GOLD: ['#ffffe6', '#ffe678', '#feae34', '#b45a1e'], PINK: ['#fff0fa', '#ff96be', '#e6508c', '#82285a'],
    CYAN: ['#f0ffff', '#8ce6ff', '#3ca0f0', '#1e468c'], GREEN: ['#f5ffe6', '#b4fa78', '#5ac850', '#286432'],
    VIOLET: ['#faf0ff', '#d2a0ff', '#965ae6', '#462878'],
  };
  const BURSTS = [
    { t: 0.4, x: 170, y: 66, R: 66, cols: FW.GOLD, n: 40, seed: 1, life: 1.3 },
    { t: 0.58, x: 62, y: 44, R: 42, cols: FW.PINK, n: 30, seed: 2, life: 1.1 },
    { t: 0.72, x: 262, y: 40, R: 44, cols: FW.CYAN, n: 30, seed: 3, life: 0.9 },
    { t: 1.22, x: 330, y: 28, R: 26, cols: FW.GREEN, n: 20, seed: 4, life: 0.5 },
    { t: 1.36, x: 250, y: 96, R: 22, cols: FW.VIOLET, n: 18, seed: 6, life: 0.4 },
  ];
  const GLYPH = { t: 0.86, x: 142, y: 54, life: 1.2 };
  const FLASHES = [[0.4, '255,230,120', 0.28], [0.58, '255,150,190', 0.16], [0.72, '140,230,255', 0.16], [0.86, '255,230,120', 0.22]];
  const GLOWS = [[0.4, 170, 66, '255,230,120', 46], [0.58, 62, 44, '255,150,190', 34], [0.72, 262, 40, '140,230,255', 34], [0.86, 142, 54, '255,230,120', 46]];
  function drawBurst(g, b, tau) {
    const dt = tau - b.t;
    if (dt < 0 || dt > b.life) return;
    if (dt < 0.1) { g.fillStyle = b.cols[0]; g.beginPath(); g.arc(b.x, b.y, 3 + dt * 60, 0, Math.PI * 2); g.fill(); }
    const fade = dt / b.life, rnd = G.prng(b.seed * 977), f20 = Math.floor(tau * 20);
    for (let i = 0; i < b.n; i++) {
      const ang = 2 * Math.PI * (i + (rnd() - 0.5) * 0.5) / b.n, spd = b.R * (0.8 + rnd() * 0.25);
      let prev = null;
      for (let j = 0; j < 5; j++) {
        const tt = dt - j * 0.04;
        if (tt < 0) break;
        const kk = 1 - Math.exp(-tt * 4);
        const x = b.x + Math.cos(ang) * spd * kk, y = b.y + Math.sin(ang) * spd * kk + 22 * tt * tt;
        const c = b.cols[Math.min(3, j + Math.floor(fade * 2.5))];
        if (fade > 0.72 && (f20 + i + j) % 3 === 0) { prev = null; continue; }
        if (prev && fade < 0.6) line(g, prev[0], prev[1], x, y, c);
        if (j === 0 && fade < 0.5) px(g, x, y, fade < 0.2 ? b.cols[0] : c, 2, 2);
        else px(g, x, y, c);
        prev = [x, y];
      }
    }
  }
  function drawGlyph(g, tau) {                 // 火花飞出去，拼成一个「桂」字，闪一闪，再垂下来熄灭
    const b = GLYPH, dt = tau - b.t, cols = FW.GOLD;
    if (dt < 0 || dt > b.life) return;
    if (dt < 0.1) { g.fillStyle = cols[0]; g.beginPath(); g.arc(b.x, b.y, 4 + dt * 70, 0, Math.PI * 2); g.fill(); }
    const k = 1 - Math.pow(1 - Math.min(1, dt / 0.35), 3), droop = Math.max(0, dt - 1.0);
    const f16 = Math.floor(tau * 16), f12 = Math.floor(tau * 12), rnd = G.prng(5);
    SP().glyph_kei.forEach(([gx, gy], i) => {
      const r1 = rnd() - 0.5, r2 = 0.6 + rnd() * 0.8;
      const tx = gx * 4, ty = gy * 4;
      const x = b.x + tx * k + r1 * 1.2 * droop * 10, y = b.y + ty * k + 34 * droop * droop * r2;
      if (dt > 1.15 && (f16 + i) % 3 === 0) return;
      const tw = (f12 + i * 7) % 11;
      const c = tw === 0 ? cols[0] : dt < 0.95 ? cols[1] : cols[2];
      if (dt < 0.35) line(g, b.x + tx * k * 0.6, b.y + ty * k * 0.6, x, y, cols[2]);
      if (dt > 0.35 && dt < 0.95 && tw === 0) { px(g, x - 1, y, c, 3, 1); px(g, x, y - 1, c, 1, 3); }
      else if (dt < 0.95) px(g, x, y, c, 2, 2);
      else px(g, x, y, c);
    });
  }
  function glow(g, x, y, r, rgb, a) {
    if (a <= 0.02) return;
    const gr = g.createRadialGradient(x, y, 0, x, y, r);
    gr.addColorStop(0, `rgba(${rgb},${(0.55 * a).toFixed(3)})`);
    gr.addColorStop(1, `rgba(${rgb},0)`);
    g.save(); g.globalCompositeOperation = 'lighter'; g.fillStyle = gr; g.fillRect(x - r, y - r, 2 * r, 2 * r); g.restore();
  }
  const tintCache = {};
  function tinted(src, rgb) {                  // 白色轮廓光图 → 染成烟花的颜色（只画、不读像素，file:// 也行）
    const key = src + '|' + rgb, im = G.image(src);
    let c = tintCache[key];
    if (!c && G.ready(im)) {
      c = document.createElement('canvas'); c.width = im.width; c.height = im.height;
      const x = c.getContext('2d');
      x.drawImage(im, 0, 0); x.globalCompositeOperation = 'source-in'; x.fillStyle = `rgb(${rgb})`; x.fillRect(0, 0, c.width, c.height);
      tintCache[key] = c;
    }
    return c;
  }
  function drawSil(g, s, x, y, tau, rgb, amt) {   // 逆光剪影：暗色身体 + 按烟花颜色染的轮廓光
    const i = G.mod(Math.floor(tau * s.fps), s.body.length), b = G.image(s.body[i]);
    if (!G.ready(b)) return;
    g.drawImage(b, x - s.ax, y - s.ay);
    const r = tinted(s.rim[i], rgb);
    if (r) { g.globalAlpha = Math.min(1, amt); g.drawImage(r, x - s.ax, y - s.ay); g.globalAlpha = 1; }
  }
  function drawFireworks(g, tau, show) {
    const sp = SP();
    for (const [t0, rgb, a] of FLASHES) {
      if (tau >= t0 && tau < t0 + 0.35) { g.fillStyle = `rgba(${rgb},${(a * (1 - (tau - t0) / 0.35)).toFixed(3)})`; g.fillRect(0, 0, G.W, 150); }
    }
    if (tau < 0.4) {                           // 往上冲的炸弹（带一串火花尾巴）
      const ease = (u) => 1 - Math.pow(1 - G.clamp(u, 0, 1), 2);
      const k = ease(tau / 0.4);
      for (let i = 1; i < 10; i++) {
        const kk = ease((tau - i * 0.025) / 0.4);
        px(g, 167 + 6 * kk + ((i * 7 + Math.floor(tau * 20)) % 3) - 1, G.lerp(216, 66, kk) + 3, FW.GOLD[Math.min(3, (i / 3) | 0)]);
      }
      const im = G.image(frame(sp.bomb.frames, 12, tau));
      if (G.ready(im)) g.drawImage(im, Math.round(164 + 6 * k) - sp.bomb.ax, Math.round(G.lerp(216, 66, k)) - sp.bomb.ay);
    }
    for (const [t0, x, y, rgb, r] of GLOWS) if (tau >= t0) glow(g, x, y, r, rgb, 1 - Math.min(1, (tau - t0) / 0.7));
    BURSTS.forEach((b) => drawBurst(g, b, tau));
    drawGlyph(g, tau);
    let lit = 0, lc = '255,230,120';
    for (const [t0, rgb] of FLASHES) if (tau >= t0) { const v = 1 - Math.min(1, (tau - t0) / 0.5); if (v > lit) { lit = v; lc = rgb; } }
    drawSil(g, sp.sil_okita, 262, 209, tau, lc, 0.35 + 0.65 * lit);
    drawSil(g, sp.sil_hijikata, 330, 209, tau, lc, 0.35 + 0.65 * lit);
    px(g, 318, 175, 'rgb(255,120,60)'); px(g, 317, 175, 'rgb(255,200,120)');      // 土方的烟头还亮着
    if (show.emberT != null) {                 // 一颗没烧完的火星，往下掉
      const kk = Math.min(1, (tau - show.emberT) / 1.2);
      const ex = G.lerp(170, 196, kk), ey = 66 + 150 * kk * kk;
      for (let i = 1; i < 12; i++) {
        const k2 = Math.max(0, kk - i * 0.016);
        px(g, G.lerp(170, 196, k2), 66 + 150 * k2 * k2, FW.GOLD[Math.min(3, (i / 3) | 0)], i < 5 ? 2 : 1, 1);
      }
      glow(g, ex, ey, 7, '255,170,80', 1);
      g.fillStyle = '#feae34'; g.beginPath(); g.arc(ex, ey, 2, 0, Math.PI * 2); g.fill();
      px(g, ex - 1, ey - 1, '#fffad2', 3, 3);
    }
  }
  async function fireworks(S) {
    const p = S.player;
    S.letterbox(false);
    await S.setStage('fw_sky_ch5', { x: -1010 + 192, y: 205, fade: false });
    p.visible = false;
    const st = G.world.stage, t0 = st.t;
    const show = S.prop({ type: 'custom', x: st.camX, y: 0, depth: 9999, draw: (g, x, y, t) => drawFireworks(g, t - t0, show) });
    show.emberT = null;
    S.sfx('slide_up', 0.7);
    await S.wait(0.4);
    S.sfx('explosion', 0.9); S.shake(3, 0.3); S.flash(0.12, 0.5);
    G.fx.word('咚——!', st.camX + 228, 110, 0.8);
    await S.wait(0.18); S.sfx('explosion_small', 0.6);
    await S.wait(0.14); S.sfx('explosion_small', 0.6); S.sfx('cheer', 0.4);
    await S.wait(0.14); S.sfx('explosion_small', 0.5); S.sfx('sparkle', 0.7);
    await S.wait(0.36); S.sfx('pop', 0.5);
    await S.wait(0.14); S.sfx('pop', 0.5);
    await S.wait(0.9);
    S.letterbox(true);
    await S.say('okita', '……是「桂」字的烟花呢。还挺好看的。', { name: '冲田' });
    await S.say('hijikata', '……喂。刚才那颗，是从万事屋那家伙站的地方飞上来的吧。', { name: '土方', expr: 'exhale' });
    await S.say('okita', '啊。有一颗火星掉下去了哦。', { name: '冲田' });
    show.emberT = st.t - t0;
    S.sfx('fall_whistle', 0.6);
    await S.wait(1.25);
    S.unprop(show);
  }

  // ================================================================ 爆炸头（原片 S6）
  function drawSmoke(g, x, y, u) {             // 炸完的黑烟，0.85 秒散开
    if (u > 0.85) return;
    const rnd = G.prng(81);
    for (let i = 0; i < 16; i++) {
      const a = rnd() * Math.PI * 2, d0 = rnd() * 24, r0 = 10 + rnd() * 7;
      const dist = d0 + Math.max(0, u - 0.12) * 68, r = r0 * (1 - u / 0.85);
      if (r < 1) continue;
      g.fillStyle = i % 2 ? 'rgb(44,40,50)' : 'rgb(66,60,72)';
      g.beginPath(); g.arc(x + Math.cos(a) * dist, y - 20 + Math.sin(a) * dist * 0.7 + u * 8, r, 0, Math.PI * 2); g.fill();
    }
  }
  function drawTears(g, eyes, t, amp) {        // 瀑布泪：从两只眼睛往两边喷出去再落下
    const f = Math.floor(t * 16);
    eyes.slice().sort((a, b) => a[0] - b[0]).forEach(([ex, ey], s) => {
      const side = s === 0 ? -1 : 1;
      let prev = null;
      for (let j = 0; j < 14; j++) {
        const u = j / 13, x = ex + side * (1 + u * 15 * amp), y = ey + u * u * 25 * amp;
        if (prev && (j + f) % 4 !== 0) {
          line(g, prev[0], prev[1], x, y, '#78c8ff', 2);
          if ((j + f) % 4 === 1) px(g, x, y - 1, '#ebfaff');
        }
        prev = [x, y];
      }
      if (amp > 0.9) for (let q = 0; q < 3; q++) if ((f + q + (side > 0 ? 1 : 0)) % 2 === 0) px(g, ex + side * (15 + q * 2), ey + 24 - q * 2 - (f % 2), '#aae1ff');
    });
  }
  function drawSootDeco(g, x, y, t, d) {
    const sp = SP(), f = G.world.player.facing, top = [x + f, y - 39];
    for (let i = 0; i < 3; i++) {             // 爆炸头一直在冒烟
      const ph = ((t - d.t0) * 0.8 + i / 3) % 1, r = 1 + ph * 3;
      g.fillStyle = ph < 0.6 ? 'rgb(130,124,136)' : 'rgb(100,94,108)';
      g.beginPath(); g.arc(top[0] - 8 + i * 7 + ph * 5, top[1] + 2 - ph * 20, r, 0, Math.PI * 2); g.fill();
    }
    const cu = (t - d.crowT) / 1.15;             // 乌鸦飞过：「阿呆～」
    if (cu >= 0 && cu < 1) {
      const im = G.image(frame(sp.crow.frames, 8, t));
      if (G.ready(im)) {
        g.save(); g.translate(Math.round(G.lerp(x + 90, x - 90, cu)), Math.round(y - 64 + Math.sin(t * 9) * 2)); g.scale(-1, 1);
        g.drawImage(im, -(im.width >> 1), -(im.height >> 1)); g.restore();
      }
    }
    if (d.coughT != null && t - d.coughT < 0.7) {   // 咳出一口黑烟
      const u = t - d.coughT;
      g.fillStyle = `rgba(70,64,76,${(1 - u / 0.7).toFixed(2)})`;
      for (let i = 0; i < 4; i++) { g.beginPath(); g.arc(x + f * (5 + u * 14 + i * 2), y - 18 - u * 6 - i, 2 + u * 4, 0, Math.PI * 2); g.fill(); }
    }
    if (d.tearsT != null) drawTears(g, [[x - 2 * f, y - 20], [x + 4 * f, y - 20]], t, Math.min(1, (t - d.tearsT) / 0.2));
    if (d.sparkT != null && d.fireT == null) {   // 最后一点火星飘下来
      const k = Math.min(1, (t - d.sparkT) / 0.3), sx = top[0] + 3 + Math.sin(t * 15) * 3 * (1 - k), sy = G.lerp(y - 90, top[1] + 1, k);
      px(g, sx, sy, '#fffac8'); px(g, sx, sy - 1, '#ffc850'); px(g, sx - 1, sy - 2, '#feae34');
    }
    if (d.fireT != null) {                       // ……落到爆炸头上，着了（他没发现）
      const im = G.image(frame(sp.afro_flame.frames, 12, t)), u = Math.min(1, (t - d.fireT) / 0.18);
      const s = u < 1 ? 1 + 2.70158 * Math.pow(u - 1, 3) + 1.70158 * Math.pow(u - 1, 2) : 1;
      if (G.ready(im) && s > 0.05) {
        const w = Math.max(1, Math.round(im.width * s)), h = Math.max(1, Math.round(im.height * s));
        g.drawImage(im, Math.round(top[0] + 3 * f - sp.afro_flame.ax * s), Math.round(top[1] + 2 - sp.afro_flame.ay * s), w, h);
      }
    }
  }
  async function sootEnding(S, thrown) {
    const p = gear(S.player), st = G.world.stage, t0 = st.t;
    p.visible = true;
    S.unpose(p);
    S.zoom(2.5, p, -21, 0);
    S.sfx('explosion', 1.0);
    S.flash(0.14, 0.85, '#ffecbe');
    S.shake(5, 0.45);
    G.fx.word('轰!!!', p.x - 30, p.y - 50, 1.0);
    boom(S, p.x, p.y - 4, 40, null);
    S.pose(p, 'soot_daze');
    const smoke = S.prop({ type: 'custom', x: p.x, y: p.y, depth: p.y + 5, draw: (g, x, y, t) => drawSmoke(g, x, y, t - t0) });
    const deco = S.prop({ type: 'custom', x: p.x, y: p.y, depth: p.y + 4, draw: (g, x, y, t) => drawSootDeco(g, x, y, t, deco) });
    Object.assign(deco, { t0, crowT: t0 + 0.25, coughT: null, tearsT: null, sparkT: null, fireT: null });
    await S.wait(0.35);
    S.sfx('crow', 0.7);
    await S.wait(0.4);
    G.fx.word('阿呆～', p.x + 8, p.y - 58, 0.9);
    S.sfx('crow', 0.6, 0.9);
    await S.wait(0.4);
    S.pose(p, 'soot_cough');
    deco.coughT = st.t;
    S.sfx('cough', 0.8);
    G.fx.word('咳', p.x + 16, p.y - 30, 0.5);
    await S.wait(0.4);
    S.pose(p, 'soot_shout');
    S.zoom(2.95, p, -24, 0.16);
    S.sfx('impact', 0.6); S.sfx('vein', 0.5);
    G.fx.speedLines(192, 96, { count: 44, inner: 96, life: 2.0, color: '#ffffff' });
    S.letterbox(true);
    if (!thrown) await S.say('gintoki', '……至少，让我把它扔出去啊……', { expr: 'hurt' });
    await S.say('gintoki', '为什么每次倒霉的都是我啊！', { expr: 'shout' });
    S.pose(p, 'soot_wail');
    deco.tearsT = st.t;
    S.sfx('fail', 0.55, 1.4);
    S.zoom(2.72, p, -21, 0.3);
    await S.wait(0.9);
    deco.sparkT = st.t;
    await S.wait(0.3);
    deco.fireT = st.t;
    S.sfx('pop', 0.6); S.sfx('fire', 0.35);
    G.fx.word('啵', p.x + 18, p.y - 44, 0.6);
    await S.wait(1.8);
    S.letterbox(false);
    await S.fadeOut(1.2);
    S.unprop(smoke); S.unprop(deco);
    G.world.zoom = null;
    F().ch5Done = true;
  }

  // ================================================================ 地图（第五章版）
  function defineStages() {
    G.STAGES.street_dusk_ch5 = {
      id: 'street_dusk_ch5', bg: 'street_dusk', x0: 0, x1: 1150, yMin: 162, yMax: 198, music: 'comedy',
      props: [noticeBoard(470, 164)],
      npcs: [
        { cid: 'elizabeth', id: 'elizabeth', x: 600, y: 178, facing: -1, label: '谜之生物', talk: talkEliz },
        { cid: 'otose', id: 'otose', x: 356, y: 168, facing: -1, anim: 'smoke', label: '登势',
          talk: async (S, a) => {
            if (count('otose5') === 1) {
              await S.say('otose', '银时，这个月的房租呢？', { actor: a });
              await S.say('gintoki', '……今天的晚霞真好看啊，老太婆。');
              await S.say('otose', '晚霞能当房租吗。', { actor: a, expr: 'angry' });
              await S.say('otose', '对了，刚才门口有只白色的大家伙转来转去，举着牌子找人。你认识？', { actor: a });
            } else await S.say('otose', '房租。', { actor: a, expr: 'exhale' });
          } },
        { cid: 'catherine', id: 'catherine', x: 286, y: 174, facing: 1, label: '凯瑟琳',
          talk: async (S, a) => {
            await S.say('catherine', '告示板上那个通缉犯，赏金可不少。抓到了分你一成。', { actor: a, expr: 'sly' });
            await S.say('gintoki', '……一成？你连抓的力气都不出吧。');
          } },
        { cid: 'townsman__v1', id: 'book', x: 120, y: 172, facing: 1, label: '书店店员',
          talk: async (S) => {
            await S.say('townsman', '最近那个长头发的攘夷志士又在这一带出没了。', { name: '书店店员' });
            await S.say('townsman', '真选组天天在屋顶上追来追去，瓦片都被踩碎了。', { name: '书店店员' });
          } },
      ],
      hotspots: [{ id: 'board', x: 470, y: 170, r: 22, ry: 10, label: '告示板', ly: 116,
        use: async (S) => {
          await S.say(null, '告示板上贴着通缉令：「攘夷志士　桂小太郎」。');
          await S.say('gintoki', '……画得一点都不像。本人比这个还要呆。');
          if (count('board') === 1) await S.say(null, '旁边一张小告示：「近日屋顶上时有炮声，敬请市民注意头顶。——真选组」');
        } }],
      triggers: [{ id: 'zura', x0: 0, x1: 5000, cond: () => F().eliz && !F().met, run: katsuraDrops }],
    };
    G.STAGES.street_dusk_ch5b = Object.assign({}, G.STAGES.street_dusk_ch5, { id: 'street_dusk_ch5b', props: [], npcs: [], hotspots: [], triggers: [] });
    G.STAGES.roofs_ch5 = { id: 'roofs_ch5', bg: 'roof_dusk', x0: 0, x1: ROOF_END + 384, yMin: 148, yMax: 172, music: 'battle', props: [] };
    G.STAGES.fw_sky_ch5 = { id: 'fw_sky_ch5', bg: 'fw_sky', x0: -1010, x1: -1010 + 384, camX: -1010, yMin: 196, yMax: 212, props: [] };
  }

  // ================================================================ 第五章主流程
  G.STORY.chapter5 = async function (S) {
    defineStages();
    G.fadeAlpha = 0;
    G.world.stage = null;
    await S.chapterCard('ch5');
    const p = gear(new G.Actor('gintoki', 300, 182, { id: 'player', team: 'player', hp: 100, speed: 72, name: '银时' }));
    G.world.player = p;
    G.fadeAlpha = 1;
    await S.setStage('street_dusk_ch5', { x: 300, y: 182, facing: 1 });
    await S.run(async (S) => {
      await S.say('gintoki', '（黄昏的歌舞伎町。今天的委托，一个都没有。）');
      await S.say('gintoki', '（新八去道场了，神乐带着定春去公园了。……难得清静。）');
      S.hint('在大街上逛逛。……那只举着牌子的白色东西是什么？', 6);
    });
    await S.until(() => G.flags.ch5Done);
  };
})();
