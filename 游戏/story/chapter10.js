// 第十章：将军暗杀篇（原片 s10）
//   理发店：万事屋替人看店，进来的客人是微服出巡的将军茂茂（名牌）→ 剪头发小游戏（注定剪坏）→ 发髻飞了 → 用胶带粘回去……又滑下来
//   → 护送将军走山道去京都（真选组 + 万事屋一路跟着）→ 乌鸦叫，奈落从山脊上落下：保护将军（护送战，将军倒下就输）
//   → 第二波：桂和伊丽莎白「天诛」也来帮忙 → 夕阳下的山脊：胧（名牌），毒针 → 对决 → 刀锋相抵
//   →「你还是和那时一样，白夜叉。」→ 银时的眼睛：老师的笑脸一闪 → 白屏（接第十一章的回忆）
'use strict';
(function () {
  const G = window.G;
  const F = () => G.flags;
  const count = (key) => (G.flags[key] = (G.flags[key] || 0) + 1);
  const SP = () => G.D.bg.ch10;
  const px = (g, x, y, c, w = 1, h = 1) => { g.fillStyle = c; g.fillRect(Math.round(x), Math.round(y), w, h); };
  const ALT = { shigeshige: 'shigeshige__s10', gintoki: 'gintoki__s10', kagura: 'kagura__s10', naraku: 'naraku__s10', elizabeth: 'elizabeth__s10', oboro: 'oboro__s10' };
  function gear(a) { const id = a && ALT[a.cid]; if (id && G.D.chars[id]) a.alt = [G.atlas(id)]; return a; }
  const ease = (u) => 1 - Math.pow(1 - G.clamp(u, 0, 1), 3);

  // ================================================================ 理发店
  function barberProps(S, st) {
    const sp = SP();
    // 理发店的旋转灯柱（条纹往上滚）
    S.prop({ type: 'custom', x: 0, y: 0, depth: 10, draw: (g, x, y, t) => {
      const im = G.image(sp.pole);
      if (G.ready(im)) g.drawImage(im, 0, G.mod(Math.floor(16 * t), 12), 7, 44, 158 - st.camX, 66, 7, 44);
    } });
    // 发髻：在头上 → 飞出去 → 落地；被胶带粘回去 → 滑下来
    st.knot = { mode: 'head' };
    S.prop({ type: 'custom', x: 0, y: 0, depth: 400, draw: (g, x, y, t) => {
      const k = st.knot, im = G.image(sp.topknot);
      if (!G.ready(im) || k.mode === 'head') return;
      let kx = k.x, ky = k.y, rot = k.rot || 0;
      if (k.mode === 'fly') {
        const u = Math.min(1, (t - k.t0) / 0.5);
        kx = G.lerp(207, 246, u); ky = G.lerp(127, 157, u) - 34 * 4 * u * (1 - u); rot = (t - k.t0) * 1100;
        if (u >= 1) { k.mode = 'floor'; k.x = 246; k.y = 157; k.rot = 0; }
      }
      g.save(); g.translate(Math.round(kx - st.camX), Math.round(ky)); g.rotate(-rot * Math.PI / 180);
      g.drawImage(im, -Math.floor(im.width / 2), -Math.floor(im.height / 2));
      if (k.tape) { g.fillStyle = 'rgb(250,248,236)'; g.fillRect(-3, -1, 6, 1); g.fillRect(-1, -3, 1, 6); }
      g.restore();
    } });
  }
  async function snip(S, n) {
    S.sfx('slash', 0.5, 2.2);
    for (let i = 0; i < n; i++) G.fx.add({ kind: 'px', x: 204 + G.rand(-3, 3), y: 128, vx: G.rand(-20, 20), vy: G.rand(-10, 10), g: 220, life: 0.6, color: '#2a2030' });
    await S.wait(0.1);
  }
  async function barber(S) {
    const p = gear(S.player), st = G.world.stage;
    const sh = gear(S.spawn('shigeshige', 206, 152, { id: 'shigeshige', name: '茂茂', facing: 1 }));
    S.pose(sh, 'sit_blink');
    p.x = 186; p.y = 148; p.facing = 1;
    S.pose(p, 'barber_snip');
    barberProps(S, st);
    S.zoom(2.0, 200, 112, 0);
    S.letterbox(true);
    S.sfx('bell_shop', 0.4);
    await S.fadeIn(0.6);
    await S.say(null, '理发店的老板出门了。看店的委托，落到了万事屋头上。');
    S.nameCard('shigeshige');
    await S.say('shigeshige', '……麻烦修一下。和平时一样就好。', { actor: sh, expr: 'normal' });
    await S.say('gintoki', '（这个客人……怎么那么像电视上的将军。）');
    await S.say('gintoki', '（……不会吧。将军怎么可能一个人跑到这种小店来剪头发。）');
    S.letterbox(false);
    let good = 0;
    for (let i = 0; i < 3; i++) {
      const ok = await S.timing({ label: `剪头发！看准时机按 J（${i + 1}/3）`, speed: 1.2 + i * 0.25, zone: [0.44, 0.58] });
      await snip(S, 3);
      if (ok) good++;
      else G.fx.text('……', 214, 120, { vy: -8, life: 0.8 });
    }
    S.letterbox(true);
    await S.say('gintoki', good >= 2 ? '（……还挺顺手的嘛。）' : '（……剪歪了一点。没关系，看不出来。）');
    // 打了个哈欠……咔嚓
    S.pose(p, 'barber_sleepy');
    S.pose(sh, 'sit_blink');
    G.fx.text('哈啊～', p.x, p.y - 34, { vy: -8, life: 0.9 });
    await S.wait(0.8);
    S.sfx('slash', 0.7, 1.5); S.sfx('pop', 0.8);
    S.flash(0.1, 0.7);
    G.fx.speedLines(214, 150, { count: 30, inner: 60, life: 0.35, color: '#ffffff' });
    G.fx.word('咔嚓！', 286, 96, 0.75);
    await S.zoom(2.45, 206, 128, 0.06);
    S.zoom(2.0, 204, 115, 0.4);
    st.knot = { mode: 'fly', t0: st.t };
    await snip(S, 6);
    S.pose(sh, 'sit_haircut_shock');
    S.pose(p, 'barber_shock');
    p.tint = { color: 'rgb(210,226,255)', k: 0.35 };
    S.sfx('shock', 0.6);
    await S.wait(0.5);
    S.sfx('thud', 0.35, 1.7);
    G.fx.dust(246, 157, 3);
    S.sfx('crow', 0.8);
    G.fx.text('阿呆～', 150, 80, { vy: -6, life: 1.0 });
    await S.wait(0.6);
    S.pose(sh, 'sit_haircut');
    // 特写：将军的发髻没了
    S.zoom(3.0, 202, 130, 0.3);
    p.tint = null;
    S.pose(p, 'barber_hold');
    st.knot = { mode: 'hand', x: p.x + 10, y: p.y - 22, rot: 20 };
    await S.say('gintoki', '将军家的头发……', { expr: 'gloom' });
    const c = await S.choice(['用胶带粘回去', '「这是最新流行的发型」', '……装作什么都没发生'], '怎么办？');
    if (c === 1) {
      await S.say('gintoki', '……这个，是江户最新流行的发型。叫「武士的觉悟」。');
      await S.say('shigeshige', '……是吗。', { actor: sh, expr: 'haircut' });
      await S.say('gintoki', '（……信了！？）', { expr: 'shock' });
      await S.say(null, '……还是粘回去吧。');
    } else if (c === 2) {
      await S.say('gintoki', '……………………');
      await S.say('shigeshige', '……头顶，凉飕飕的。', { actor: sh, expr: 'haircut' });
      await S.say(null, '……还是粘回去吧。');
    }
    S.pose(p, 'barber_slap', { restart: true });
    await S.wait(0.15);
    S.sfx('slap', 0.7);
    G.fx.word('啪！', 250, 38, 0.5);
    st.knot = { mode: 'stuck', x: 207, y: 129, rot: -24, tape: true };
    S.zoom(3.2, 202, 130, 0.08);
    S.sfx('sparkle', 0.45);
    await S.wait(0.2);
    S.zoom(3.0, 202, 130, 0.2);
    S.pose(p, 'thumbs_smug');
    await S.say('gintoki', '完美。', { expr: 'smug' });
    // ……滑下来了
    S.sfx('slide_down', 0.5);
    await S.animate(0.3, (u) => { st.knot.x = G.lerp(207, 216, u); st.knot.y = G.lerp(129, 135, u); st.knot.rot = G.lerp(-24, -70, u); });
    G.fx.word('哧溜～', 256, 58, 0.6);
    S.pose(p, 'barber_shock');
    await S.wait(0.3);
    await S.animate(0.3, (u) => { st.knot.y = 135 + 320 * u * u * 0.3; });
    st.knot = { mode: 'floor', x: 222, y: 158, rot: -90, tape: true };
    S.sfx('fail', 0.55);
    S.pose(p, 'barber_hold');
    await S.say('gintoki', '……………………', { expr: 'cry' });
    await S.say('shigeshige', '……谢谢。下次，也拜托你了。', { actor: sh, expr: 'haircut' });
    await S.say('gintoki', '（……还有下次！？）', { expr: 'shock' });
    await S.fadeOut(0.8);
    S.zoom(1, null, null, 0);
    S.letterbox(false);
  }

  // ================================================================ 山道：护送 → 奈落伏击
  function crowsProp(S) {
    const sp = SP(), st = G.world.stage;
    return S.prop({ type: 'custom', x: 0, y: 0, depth: 5, draw: (g, x, y, t) => {
      sp.circling.forEach(([rad, spd, a0], i) => {
        const a = a0 + 0.7 * Math.PI * spd * t, f = Math.floor((t + 0.13 * i) * 12) % 4;
        const im = G.image(sp.crow.frames[f]), cx = 196 + Math.cos(a) * rad, cy = 44 + 0.35 * Math.sin(a) * rad;
        if (!G.ready(im)) return;
        g.save(); g.translate(Math.round(cx), Math.round(cy)); if (-Math.sin(a) * spd < 0) g.scale(-1, 1);
        g.drawImage(im, -sp.crow.r, -sp.crow.r); g.restore();
      });
    } });
  }
  async function escort(S) {
    const p = gear(S.player);
    await S.setStage('pass_ch10', { x: 160, y: 176, facing: 1, fade: false });
    p.visible = true; p.tint = null;
    S.unpose(p);                      // 理发时摆的姿势（hold）要解开，不然走不了
    const st = G.world.stage;
    const party = [['shigeshige', '将军'], ['kondo', '近藤'], ['hijikata', '土方'], ['okita', '冲田'], ['shinpachi', '新八'], ['kagura', '神乐']]
      .map(([cid, nm], i) => { const a = gear(S.spawn(cid, 130 - i * 18, 172 + (i % 3) * 8, { id: cid, name: nm, facing: 1 })); S.follow(a, 'player'); return a; });
    const sh = party[0];
    sh.idleAnim = 'idle_haircut';
    crowsProp(S);
    S.music('tension', 0.5);
    await S.fadeIn(0.6);
    await S.narrate('将军上洛。真选组和万事屋，护送着将军走上去京都的山道。', { auto: 2.6 });
    await S.say('hijikata', '……将军的头发怎么回事。', { actor: party[2], expr: 'angry' });
    await S.say('gintoki', '……不要在意。那是最新流行的发型。');
    await S.say('okita', '旦那剪的吧。……很有品味。', { actor: party[3], expr: 'smug' });
    S.hint('护送将军往右走（将军会跟着你）', 5);
    F().escort = true;
  }
  async function ambush(S) {
    const p = S.player, st = G.world.stage, cx = st.camX;
    S.letterbox(true);
    S.sfx('crow', 0.8); S.sfx('crow', 0.55, 0.85);
    S.sfx('shing', 0.45, 0.8);
    S.flash(0.08, 0.35, '#ff3c46');
    const ridge = [40, 78, 124, 206, 286, 322, 352];
    const crest = G.D.bg.pass.crest;
    const sils = ridge.map((rx, i) => {
      const sy = crest[G.mod(Math.floor(rx + 0.5 * st.camX), 640)] + 2;
      const n = gear(S.spawn('naraku', cx + rx, sy, { id: `rn${i}`, name: '奈落', facing: rx < 200 ? 1 : -1 }));
      n.alpha = 0; n.shadow = false;
      S.pose(n, 'ridge');
      return n;
    });
    S.sfx('whoosh', 0.4, 1.3);
    await S.animate(0.3, (u) => sils.forEach((n, i) => { n.alpha = G.clamp(u * 3 - i * 0.2, 0, 1); }));
    for (const id of ['shigeshige', 'kondo', 'hijikata', 'okita', 'shinpachi', 'kagura']) { const a = S.actor(id); if (a) { a.follow = null; S.pose(a, id === 'shigeshige' ? 'shock_haircut' : 'shock'); } }
    S.pose(p, 'shock');
    await S.say('hijikata', '是奈落！保护将军！', { actor: S.actor('hijikata'), expr: 'shout' });
    // 跳下来
    S.sfx('whoosh', 0.7);
    const lands = [58, 30, 294, 320, 348];
    await Promise.all(lands.map((lx, i) => S.arc(sils[i], cx + lx, 176 + (i % 3) * 6, 30, 0.5, { anim: 'leap' })));
    S.sfx('land', 0.7);
    sils.slice(5).forEach((n) => S.remove(n));
    for (const n of sils.slice(0, 5)) { n.alpha = 1; n.shadow = true; S.pose(n, 'ambush'); }
    S.zoom(1.35, cx + 196, 140, 0.14);
    G.fx.speedLines(196, 118, { count: 34, inner: 110, life: 0.3, color: '#ffffff' });
    S.shake(3, 0.3);
    S.pose(S.actor('hijikata'), 'draw', { restart: true });
    S.sfx('shing', 0.8);
    await S.wait(0.6);
    S.zoom(1, null, null, 0.2);
    for (const id of ['shigeshige', 'kondo', 'hijikata', 'okita', 'shinpachi', 'kagura']) { const a = S.actor(id); if (a) S.unpose(a); }
    S.unpose(p);
    S.letterbox(false);
    S.hint('奈落的伏击！保护将军——将军倒下就输', 6);
    S.actor('kagura').ranged = 80; S.actor('kagura').allyMoves = [G.MOVES.E_GUN];
    await S.fight({
      arena: [cx + 8, cx + 376],
      allies: ['kondo', 'hijikata', 'okita', 'shinpachi', 'kagura'], allyHp: 90,
      vip: 'shigeshige', vipHp: 90,
      music: 'battle',
      waves: [
        sils.slice(0, 5).map((n) => ({ actor: n.id, cid: 'naraku', name: '奈落', hp: 30 })),
        [0, 1, 2, 3, 4].map((i) => ({ cid: 'naraku', id: `nk${i}`, name: '奈落', hp: 32, side: i % 2 ? 'left' : 'right' })),
      ],
      onWave: async (S, i) => { if (i === 1) await katsuraArrives(S); },
      after: null,
    });
    const k = S.actor('kagura'); k.ranged = 0; k.allyMoves = null;
    S.letterbox(true);
    await S.say('kondo', '将军，没事吧！', { actor: S.actor('kondo'), expr: 'shout' });
    await S.say('shigeshige', '……嗯。多亏了诸位。', { actor: S.actor('shigeshige'), expr: 'haircut' });
    S.sfx('crow', 0.6);
    await S.say('gintoki', '……还有一个。山脊上，有个家伙一直在看着我们。', { expr: 'angry' });
    await S.fadeOut(0.8);
    S.letterbox(false);
  }
  async function katsuraArrives(S) {
    const p = S.player, st = G.world.stage;
    S.letterbox(true);
    S.sfx('fall_whistle', 0.5);
    const k = S.spawn('katsura', st.camX + 300, 176, { id: 'katsura', name: '桂', facing: -1 });
    const e = gear(S.spawn('elizabeth', st.camX + 330, 182, { id: 'elizabeth', name: '伊丽莎白', facing: -1 }));
    k.z = 100; e.z = 100;
    await Promise.all([S.arc(k, k.x, k.y, 4, 0.4, { anim: 'jump', z1: 0 }), S.arc(e, e.x, e.y, 4, 0.45, { anim: 'jump', z1: 0 })]);
    S.sfx('land', 0.7);
    S.pose(e, 'sign_tenchu', { restart: true });
    await S.say('elizabeth', '［牌子］天诛', { actor: e, name: '伊丽莎白' });
    await S.say('katsura', '银时！将军的护卫，算我一份！', { actor: k, expr: 'determined' });
    await S.say('gintoki', '……你不是攘夷志士吗。保护将军没问题吗。', { expr: 'shock' });
    await S.say('katsura', '今天是休息日。', { actor: k });
    await S.say('hijikata', '……休息日的恐怖分子啊。', { actor: S.actor('hijikata'), expr: 'angry' });
    S.unpose(e);
    k.team = 'ally'; k.maxHp = k.hp = 90;
    S.letterbox(false);
  }

  // ================================================================ 夕阳下的山脊：胧
  async function oboroDuel(S) {
    const p = S.player;
    await S.setStage('duel_ch10', { x: 150, y: 176, facing: 1, fade: false });
    const st = G.world.stage;
    const ob = gear(S.spawn('oboro', 282, 176, { id: 'oboro', name: '胧', facing: -1 }));
    S.pose(ob, 'idle_cold_smile');
    const perch = G.D.bg.duel_ridge.perch;
    st.state.scatterT = null;
    S.prop({ type: 'custom', x: 0, y: 0, depth: 4, draw: (g, x, y, t) => {        // 枯树上的乌鸦（交锋时飞散）
      const sp = SP();
      perch.forEach(([cx, cy, f], i) => {
        if (st.state.scatterT == null) {
          const im = G.image(sp[f > 0 ? 'perch_r' : 'perch_l']);
          if (G.ready(im)) g.drawImage(im, cx - 3, cy - 6 + (Math.floor((t + 0.2 * i) * 3) % 5 === 0 ? 1 : 0));
        } else {
          const u = t - st.state.scatterT - 0.04 * i, im = G.image(sp.crow.frames[Math.floor(t * 12 + i) % 4]);
          if (u > 0 && G.ready(im)) g.drawImage(im, Math.round(cx + (i % 2 ? 70 : -50) * u - sp.crow.r), Math.round(cy - 80 * u - sp.crow.r));
        }
      });
    } });
    S.letterbox(true);
    S.sfx('wind', 0.4);
    await S.fadeIn(0.6);
    S.pose(ob, 'needle', { restart: true, speed: 0.6 });
    S.sfx('whoosh', 0.5, 1.6);
    S.letterbox(false);
    const ok = await S.timing({ label: '毒针飞来！看准时机按 J 挡开', speed: 1.6, zone: [0.42, 0.56] });
    S.letterbox(true);
    S.pose(p, 'guard');
    S.sfx('clang', 0.8);
    G.fx.word('锵！', p.x - 22, p.y - 60, 0.55);
    G.fx.spark(p.x + 10, p.y - 20, '#ffffff', 8);
    if (!ok) { p.hp -= 15; p.flash = 1; await S.say(null, '一根针擦过了手臂。'); }
    S.nameCard('oboro');
    await S.wait(0.6);
    await S.say('oboro', '……白夜叉。', { actor: ob, expr: 'cold_smile' });
    await S.say('gintoki', '……又是一个认识我的家伙。我欠你钱吗。', { expr: 'angry' });
    S.unpose(ob); S.unpose(p);
    S.letterbox(false);
    S.hint('天照院奈落的首领「胧」——会扔毒针，注意躲开', 5);
    await S.fight({
      arena: [8, 376],
      music: 'battle',
      waves: [[{ actor: 'oboro', cid: 'oboro', name: '天照院奈落首领 胧', hp: 180, boss: true, speed: 60, range: 28, ranged: 120, minHp: 1,
        moves: ['E_NEEDLE', 'E_SLASH', 'E_SLASH'] }]],
      endWhen: () => { const b = S.actor('oboro'); return !!(b && b.team === 'enemy' && b.hp <= 90); },
      after: null,
    });
    ob.team = 'npc'; G.ui.boss = null;
    // 冲刺 → 刀锋相抵
    S.letterbox(true);
    await Promise.all([S.walk(p, 150, 176, { speed: 100 }), S.walk(ob, 282, 176, { speed: 100 })]);
    S.face(p, ob); S.face(ob, p);
    S.sfx('dash', 0.7);
    await Promise.all([S.walk(p, 196, 176, { speed: 300, anim: 'dash_blade' }), S.walk(ob, 238, 176, { speed: 300, anim: 'run' })]);
    S.impact(2);
    S.sfx('clang', 1.0); S.sfx('impact', 0.9);
    S.flash(0.1, 0.5);
    st.state.scatterT = st.t; S.sfx('crow', 0.6);
    G.fx.word('铿——！！', st.camX + 104, 92, 0.8);
    G.fx.debris(216, 143, ['#ffffff', '#ffe678', '#ffa03c'], 22, [60, 200], 200, 0.6);
    S.pose(p, 'bladelock'); S.pose(ob, 'bladelock');
    S.zoom(1.6, 216, 140, 0.4);
    S.letterbox(false);
    await S.mash({ label: '刀锋相抵！连按 J 顶回去', need: 16, time: 5, decay: 2.2 });
    S.letterbox(true);
    S.sfx('clang', 0.6);
    S.zoom(2.25, 216, 136, 0.8);
    await S.say('oboro', '你还是和那时一样，白夜叉。', { actor: ob, expr: 'cold_smile' });
    await eyes(S);
  }

  // ================================================================ 眼睛：老师的笑脸 → 白屏
  async function eyes(S) {
    const sp = SP();
    let shot = 'eyes_lazy', t0 = null, white = 0;
    S.stopMusic(0.5);
    S.insert((g, t) => {
      if (t0 == null) t0 = t;
      const tremble = shot !== 'eyes_lazy' && shot !== 'sensei_smile' ? Math.round(Math.sin(t * 60)) : 0;
      g.drawImage(G.image(sp[shot]), tremble, 0);
      if (white > 0) { g.fillStyle = `rgba(255,255,255,${white})`; g.fillRect(0, 0, G.W, G.H); }
    });
    S.sfx('heartbeat', 0.8);
    await S.wait(0.6);
    shot = 'eyes_wide';
    S.sfx('heartbeat', 1.0); S.sfx('shock', 0.5);
    S.flash(0.1, 0.5);
    await S.wait(0.6);
    shot = 'sensei_smile';
    S.sfx('bell', 0.45);
    S.flash(0.15, 0.6);
    await S.wait(1.4);
    shot = 'eyes_wide_tears';
    S.sfx('heartbeat', 0.9);
    S.flash(0.1, 0.6);
    await S.wait(0.8);
    S.sfx('shine', 0.7, 0.8);
    await S.animate(0.4, (u) => { white = u; });
    await S.wait(0.8);
    S.zoom(1, null, null, 0);
    S.letterbox(false);
    F().ch10Done = true;
  }

  // ================================================================ 地图（第十章版）
  function defineStages() {
    G.STAGES.barber_ch10 = { id: 'barber_ch10', bg: 'barber', x0: 0, x1: 384, yMin: 146, yMax: 200, music: 'comedy', props: [] };
    G.STAGES.pass_ch10 = { id: 'pass_ch10', bg: 'pass', x0: 0, x1: 1700, yMin: 164, yMax: 200, props: [],
      triggers: [{ id: 'ambush', x0: 700, x1: 9999, cond: () => F().escort && !F().ambushed,
        run: async (S) => { F().ambushed = true; await ambush(S); await oboroDuel(S); } }] };
    G.STAGES.duel_ch10 = { id: 'duel_ch10', bg: 'duel_ridge', x0: 0, x1: 384, yMin: 164, yMax: 198, props: [] };
  }

  // ================================================================ 第十章主流程
  G.STORY.chapter10 = async function (S) {
    defineStages();
    G.fadeAlpha = 0;
    G.world.stage = null;
    await S.chapterCard('ch10');
    const p = gear(new G.Actor('gintoki', 186, 148, { id: 'player', team: 'player', hp: 100, speed: 72, name: '银时' }));
    G.world.player = p;
    G.fadeAlpha = 1;
    await S.setStage('barber_ch10', { x: 186, y: 148, facing: 1, fade: false });
    await S.run(async (S) => { await barber(S); await escort(S); });
    await S.until(() => G.flags.ch10Done);
    // 留在白屏上，接第十一章的回忆
    G.fadeAlpha = 0;
    G.flashAlpha = 0;
  };
})();
