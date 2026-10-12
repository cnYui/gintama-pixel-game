// 第十二章：洛阳决战·离别（原片 s12）
//   雨中的洛阳星：换成操控神乐，和哥哥神威打 → 打到一半：雨伞相撞的冲击波，星海坊主从天而降「够了！」（名牌）
//   → 雨点叮叮叮地打在秃头上 → 神乐指着神威：「我一定会把哥哥带回家阿鲁！」→ 神威笑着撑开伞，走进雾里
//   → 黎明的江户港：被解散的真选组要离开江户。码头上自由走动，和近藤、土方、冲田、阿妙一一告别
//   → 船上：土方点上烟「……我们会回来的。」→ 船升空 → 樱花树下的阿妙挥手，船变成天边的一颗星
'use strict';
(function () {
  const G = window.G;
  const F = () => G.flags;
  const count = (key) => (G.flags[key] = (G.flags[key] || 0) + 1);
  const PR = () => G.D.bg.ch12.props;
  const px = (g, x, y, c, w = 1, h = 1) => { g.fillStyle = c; g.fillRect(Math.round(x), Math.round(y), w, h); };
  const ALT = { kagura: 'kagura__s12', kamui: 'kamui__s12', umibozu: 'umibozu__s12', hijikata: 'hijikata__s12', otae: 'otae__s12', okita: 'okita__s04' };
  function gear(a) { const id = a && ALT[a.cid]; if (id && G.D.chars[id]) a.alt = [G.atlas(id)]; return a; }
  const ease = (u) => 1 - Math.pow(1 - G.clamp(u, 0, 1), 3);

  function lightning(S) {
    const st = G.world.stage, L = G.D.bg.s12_rakuyo.lightning, keys = Object.keys(L.bolts), b = L.bolts[keys[Math.floor(Math.random() * keys.length)]], t0 = st.t;
    S.lightning();
    const p = S.prop({ type: 'custom', x: 0, y: 0, depth: -5, draw: (g, x, y, t) => {
      if (t - t0 < 0.3) { const im = G.image(b.image); if (G.ready(im)) g.drawImage(im, b.x, b.y); }
    } });
    G.world.ticks.push(() => { if (st.t - t0 > 0.35) { S.unprop(p); return true; } return false; });
  }

  // ================================================================ 洛阳：神乐 vs 神威
  async function rakuyo(S) {
    const k = S.setPlayer('kagura', { x: 120, y: 172, facing: 1, name: '神乐', hp: 100, speed: 76 });
    gear(k);
    G.D.bg.s12_rakuyo.fg = [{ type: 'rain', n: 120, slant: 0.18, len: 9, speed: 520, ground: [156, 204], splashes: 18, color: 'rgba(170,186,220,0.55)', alpha: 1 }];
    await S.setStage('rakuyo_ch12', { x: 120, y: 172, facing: 1, fade: false });
    const st = G.world.stage;
    const km = gear(S.spawn('kamui', 280, 172, { id: 'kamui', name: '神威', facing: -1 }));
    S.pose(km, 'idle_smile');
    S.music('battle', 0.5);
    S.sfx('rain', 0.55);
    S.letterbox(true);
    await S.fadeIn(0.6);
    lightning(S);
    await S.say('kamui', '……还在追我吗，神乐。', { actor: km, expr: 'smile' });
    await S.say('kagura', '哥哥！今天我一定要把你打醒阿鲁！', { expr: 'angry' });
    S.pose(km, 'ready_open_eyes');
    S.zoom(2.6, km, -28, 0.12); S.sfx('shine', 0.7);
    await S.wait(0.5);
    S.zoom(1, null, null, 0.2);
    S.unpose(km);
    S.letterbox(false);
    S.hint('现在操控神乐（招式一样：J 攻击、K 跳、L 挡）——和神威打', 6);
    const storm = (dt) => { if (G.world.stage !== st) return true; if (Math.random() < dt / 5) lightning(S); return false; };
    G.world.ticks.push(storm);
    await S.fight({
      arena: [st.camX + 8, st.camX + 376],
      music: 'battle',
      waves: [[{ actor: 'kamui', cid: 'kamui', name: '春雨第七师团团长 神威', hp: 180, boss: true, speed: 66, range: 26, minHp: 1, moves: ['E_PUNCH', 'E_SLASH', 'E_HEAVY'] }]],
      endWhen: () => { const b = S.actor('kamui'); return !!(b && b.team === 'enemy' && b.hp <= 90); },
      after: null,
    });
    km.team = 'npc'; G.ui.boss = null;
    await umibozuLands(S);
  }
  async function umibozuLands(S) {
    const p = S.player, st = G.world.stage, km = S.actor('kamui');
    S.letterbox(true);
    // 雨伞相撞：冲击波 → 两人跃起 → 一个影子越来越大
    p.x = st.camX + 150; km.x = st.camX + 230; p.y = km.y = 172;
    S.face(p, km); S.face(km, p);
    S.pose(p, 'thrust_shout'); S.pose(km, 'thrust_open');
    S.impact(2);
    S.sfx('clang', 1.0); S.sfx('impact', 1.0);
    G.fx.word('锵!!', st.camX + 190, 120, 0.7);
    const t0 = st.t;
    const ring = S.prop({ type: 'custom', x: 0, y: 0, depth: 999, draw: (g, x, y, t) => {
      const u = t - t0;
      if (u > 0.6) return;
      for (let i = 0; i < 3; i++) { const r = (u - i * 0.08) * 260; if (r <= 0) continue; g.strokeStyle = `rgba(255,255,255,${(0.8 * (1 - u / 0.6)).toFixed(2)})`; g.lineWidth = 2; g.beginPath(); g.ellipse(190, 150, r, r * 0.4, 0, 0, Math.PI * 2); g.stroke(); }
    } });
    S.shake(5, 0.4);
    await S.wait(0.6);
    S.unprop(ring);
    S.pose(p, 'jump_shout'); S.pose(km, 'land_smile');
    S.sfx('jump', 0.6);
    S.sfx('fall_whistle', 0.7);
    const um = gear(S.spawn('umibozu', st.camX + 190, 172, { id: 'umibozu', name: '星海坊主', facing: 1 }));
    um.z = 200;
    S.pose(um, 'jump_angry');
    await S.arc(um, um.x, um.y, 2, 0.55, { anim: 'jump_angry', z1: 0 });
    S.impact(3);
    S.sfx('explosion', 0.9); S.sfx('thud', 1.0);
    S.flash(0.12, 0.8);
    S.shake(6, 0.5);
    const cr = PR().crater;
    S.prop({ type: 'image', image: cr.image, x: um.x, y: um.y + 2, ax: cr.ax, ay: cr.ay, depth: 150 });
    G.fx.debris(um.x, um.y - 6, ['#5a5e70', '#3a3e50', '#9aa0b8'], 24, [60, 200], 300, 0.9);
    S.pose(um, 'land_angry');
    await Promise.all([S.arc(p, p.x - 60, p.y + 4, 20, 0.4, { anim: 'fly' }), S.arc(km, km.x + 60, km.y + 4, 20, 0.4, { anim: 'fly' })]);
    S.pose(p, 'land_angry'); S.pose(km, 'land_smile');
    await S.wait(0.3);
    S.pose(um, 'stop_angry');
    await S.say('umibozu', '够了！', { actor: um, expr: 'angry' });
    S.nameCard('umibozu');
    S.zoom(2.4, um, -24, 0.4);
    await S.wait(1.0);
    // 叮叮叮：雨点打在秃头上
    S.pose(um, 'stop_normal');
    S.pose(p, 'idle_deadpan');
    const dome = G.D.bg.ch12.anchors.umibozu_dome_rel_feet;
    for (const [d, w] of [[0.5, '叮!'], [0.4, '叮!'], [0.25, '叮'], [0.18, '叮'], [0.12, '叮']]) {
      await S.wait(d);
      S.sfx('blip', 0.5, 2.6);
      G.fx.word(w, um.x + dome[0] + G.rand(-8, 8), um.y + dome[1] - 14, 0.4);
      G.fx.spark(um.x + dome[0], um.y + dome[1], '#dfe8ff', 2);
    }
    await S.say('kagura', '……………………', { expr: 'normal' });
    S.sfx('vein', 0.6);
    G.fx.img(PR().vein7.image, um.x + dome[0] + 4, um.y + dome[1] - 4, { life: 1.4, pulse: true });
    await S.say('umibozu', '……别盯着爸爸的头看！', { actor: um, expr: 'angry' });
    S.zoom(1, null, null, 0.3);
    // 「我一定会把哥哥带回家阿鲁！」
    S.pose(p, 'point_determined', { restart: true });
    await S.say('kagura', '我一定会把哥哥带回家阿鲁！', { expr: 'determined' });
    S.music('sad', 0.5);
    S.pose(km, 'idle_smile');
    await S.say('kamui', '……那就变得更强吧，神乐。强到能把我拽回去为止。', { actor: km, expr: 'smile' });
    S.sfx('whoosh', 0.4);
    km.facing = 1;
    const mist = PR().mist_patch;
    S.prop({ type: 'image', image: mist.image, x: km.x + 30, y: 100, ax: 0, ay: 0, depth: 999 });
    await S.walk(km, km.x + 160, km.y, { speed: 30, anim: 'walk_umbrella' });
    S.remove(km);
    S.pose(p, 'point_sad', { restart: true });
    S.pose(um, 'idle_sad');
    await S.say('kagura', '……哥哥。', { expr: 'sad' });
    await S.fadeOut(1.0);
    S.letterbox(false);
  }

  // ================================================================ 黎明的码头：告别
  async function dock(S) {
    const g = S.setPlayer('gintoki', { x: 180, y: 172, facing: 1, name: '银时', hp: 100 });
    S.flash(0.6, 1, '#ffffff');
    await S.setStage('dock_ch12', { x: 180, y: 172, facing: 1, fade: false });
    S.music('sad', 0.5);
    await S.fadeIn(0.6);
    await S.narrate('被解散的真选组，在黎明时分离开了江户。', { auto: 2.4 });
    S.hint('在码头上和大家道个别', 5);
    void g;
  }
  async function bye(S, a, who) {
    const n = count('bye_' + who);
    if (who === 'kondo') {
      await S.say('kondo', '万事屋……阿妙小姐就拜托你了……呜呜呜……', { actor: a, expr: 'cry' });
      if (n === 1) await S.say('gintoki', '……你先把鼻涕擦干净再说。');
    } else if (who === 'hijikata') {
      await S.say('hijikata', '……别送了。又不是不回来。', { actor: a, expr: 'exhale' });
      if (n === 1) { await S.say('gintoki', '谁送你了。我是来看蛋黄酱有没有带够的。'); await S.say('hijikata', '……带了一船。', { actor: a }); }
    } else if (who === 'okita') {
      await S.say('okita', '旦那。土方先生要是在船上出了什么意外，记得替我开香槟。', { actor: a, expr: 'smug' });
    } else if (who === 'otae') {
      await S.say('otae', '……真选组的人，都是笨蛋呢。明明一个个都舍不得走。', { actor: a, expr: 'smile' });
      await S.say('gintoki', '……笨蛋才会回来。等着吧。');
    }
    F()['bye_' + who] = true;
  }

  // ================================================================ 船上：「……我们会回来的。」→ 升空 → 阿妙挥手
  async function departure(S) {
    const p = S.player;
    await S.fadeOut(0.6);
    await S.setStage('deck_ch12', { x: 30, y: 200, fade: false });
    p.visible = false;
    const spots = G.D.bg.s12_deck.spots;
    const kd = S.spawn('kondo', spots.kondo, 160, { id: 'kd', facing: 1 });
    const hj = gear(S.spawn('hijikata', spots.hijikata, 160, { id: 'hj', facing: -1 }));
    const ok = gear(S.spawn('okita', spots.okita, 160, { id: 'ok', facing: -1 }));
    S.pose(kd, 'cry'); S.pose(hj, 'light'); S.pose(ok, 'nap');
    S.letterbox(true);
    S.sfx('wind', 0.4);
    await S.fadeIn(0.6);
    await S.wait(0.6);
    S.sfx('fire', 0.3);
    S.pose(hj, 'inhale', { restart: true });
    await S.wait(0.5);
    S.pose(hj, 'exhale');
    G.fx.add({ kind: 'puff', x: hj.x - 8, y: hj.y - 28, vx: -10, vy: -6, r: 3, life: 1.4, color: '230,230,236' });
    await S.say('hijikata', '……我们会回来的。', { actor: hj, expr: 'exhale' });
    await S.say('kondo', '阿妙小姐～～！等我回来～～！', { actor: kd, expr: 'cry' });
    await S.fadeOut(0.6);
    // 港口：船升空
    await S.setStage('harbour_ch12', { x: 30, y: 200, fade: false });
    p.visible = false;
    const st = G.world.stage, t0 = st.t, ship = PR().ship, pier = G.D.bg.s12_harbour.pier;
    S.prop({ type: 'custom', x: 0, y: 0, depth: 500, draw: (g, x, y, t) => {
      const u = Math.max(0, t - t0 - 0.6), sx = pier.x + 60 + u * 6, sy = pier.y - 20 - u * u * 14;
      const im = G.image(ship.image);
      if (!G.ready(im)) return;
      const x0 = Math.round(sx - ship.w / 2), y0 = Math.round(sy - ship.h * 0.62);
      g.drawImage(im, x0, y0);
      const fl = PR().flag_small.frames[Math.floor(t * 10) % PR().flag_small.frames.length];
      g.drawImage(G.image(fl), x0 + 5 - 24 + 1, y0 + 41 - 4);
      for (const [tx, ty] of ship.info.thrusters) { const j = PR()[`jet${Math.floor(t * 12) % 3}`]; g.drawImage(G.image(j.image), x0 + tx - j.ax, y0 + ty - j.ay); }
    } });
    S.sfx('engine_hum', 0.6);
    await S.fadeIn(0.5);
    await S.wait(3.0);
    await S.fadeOut(0.6);
    // 樱花树下的阿妙
    await S.setStage('dock_ch12', { x: 30, y: 200, fade: false });
    p.visible = false;
    for (const id of ['kondo', 'hijikata', 'okita']) S.remove(id);
    const ot = gear(S.actor('otae'));
    S.pose(ot, 'idle_open');
    const st2 = G.world.stage, t1 = st2.t;
    S.prop({ type: 'custom', x: 0, y: 0, depth: 50, draw: (g, x, y, t) => {
      const u = Math.min(1, (t - t1) / 4.5), sc = Math.max(5, Math.round(16 - 11 * u));
      const d = PR().ship_silhouette.by_k40[String(sc)];
      if (u < 0.97 && d) { const im = G.image(d.image); if (G.ready(im)) g.drawImage(im, Math.round(G.lerp(150, 230, u) - d.w / 2), Math.round(G.lerp(90, 30, u) - d.h / 2)); }
      if (u >= 0.97) { const s = Math.round(3 + 2 * Math.sin(t * 12)); px(g, 230 - s, 30, '#fff8d0', 2 * s + 1, 1); px(g, 230, 30 - s, '#fff8d0', 1, 2 * s + 1); }
    } });
    S.letterbox(true);
    await S.fadeIn(0.6);
    await S.wait(1.2);
    G.fx.text('阿妙小姐～～！', 190, 50, { vy: -4, life: 1.8 });
    await S.wait(1.4);
    S.pose(ot, 'wave');
    S.sfx('twinkle', 0.6);
    await S.say('otae', '……路上小心哦。', { actor: ot, expr: 'smile' });
    await S.wait(1.6);
    await S.fadeOut(1.2);
    S.letterbox(false);
    F().ch12Done = true;
  }

  // ================================================================ 地图（第十二章版）
  function defineStages() {
    G.STAGES.rakuyo_ch12 = { id: 'rakuyo_ch12', bg: 's12_rakuyo', x0: -173, x1: 557, yMin: 156, yMax: 200, props: [] };
    G.STAGES.dock_ch12 = { id: 'dock_ch12', bg: 's12_dock', x0: 0, x1: 384, yMin: 160, yMax: 186, props: [],
      npcs: [
        { cid: 'kondo', id: 'kondo', x: 214, y: 166, facing: 1, anim: 'cry', label: '近藤', talk: async (S, a) => bye(S, a, 'kondo') },
        { cid: 'hijikata', id: 'hijikata', alt: ['hijikata__s12'], x: 250, y: 170, facing: -1, anim: 'exhale', label: '土方', talk: async (S, a) => bye(S, a, 'hijikata') },
        { cid: 'okita', id: 'okita', x: 292, y: 168, facing: -1, label: '冲田', talk: async (S, a) => bye(S, a, 'okita') },
        { cid: 'otae', id: 'otae', alt: ['otae__s12'], x: 340, y: 176, facing: -1, label: '阿妙', talk: async (S, a) => bye(S, a, 'otae') },
      ],
      triggers: [{ id: 'leave', x0: 0, x1: 999, cond: () => F().bye_kondo && F().bye_hijikata && F().bye_okita && F().bye_otae && !F().left,
        run: async (S) => { F().left = true; await departure(S); } }] };
    G.STAGES.deck_ch12 = { id: 'deck_ch12', bg: 's12_deck', x0: 0, x1: 384, yMin: 190, yMax: 210, props: [] };
    G.STAGES.harbour_ch12 = { id: 'harbour_ch12', bg: 's12_harbour', x0: 0, x1: 384, yMin: 190, yMax: 210, props: [] };
  }

  // ================================================================ 第十二章主流程
  G.STORY.chapter12 = async function (S) {
    defineStages();
    G.fadeAlpha = 0;
    G.world.stage = null;
    await S.chapterCard('ch12');
    const p = new G.Actor('kagura', 120, 172, { id: 'player', team: 'player', hp: 100, speed: 76, name: '神乐' });
    G.world.player = p;
    G.fadeAlpha = 1;
    await S.setStage('rakuyo_ch12', { x: 120, y: 172, facing: 1, fade: false });
    await S.run(async (S) => { await rakuyo(S); await dock(S); });
    await S.until(() => G.flags.ch12Done);
  };
})();
