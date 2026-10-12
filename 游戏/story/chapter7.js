// 第七章：红樱篇（原片 s07）
//   月夜的桥：桂和伊丽莎白走过，一个逆光的剑客迎面走来——一闪，只剩一缕长发飘落（过场）
//   → 第二天夜里，银时跟着伊丽莎白来到桥上调查（自由逛：伊丽莎白、断发、月亮）
//   → 红月下的屋顶：冈田似藏拔出妖刀红樱（名牌）「红樱……还没吃饱呢。」
//   → 雷雨中的桥：似藏 Boss 战，两个阶段（中途被红樱的触手砍伤跪地，眼神一变站起来；第二阶段红樱更大更快）
//   → 最后一击：红樱碎裂 → 满月前滑过的鬼兵队船，船舷上抽烟的高杉（名牌）「我只是要毁掉这个腐朽的世界。」
//   → 甲板：春雨海盗包围，短发的桂从天而降，背靠背：「背后交给你了，银时。」「别拖后腿啊，假发。」「不是假发，是桂！」
//   → 和桂一起打海盗（敌人从两边来）→ 上层甲板的高杉：「下次见面，你我就是敌人。」
'use strict';
(function () {
  const G = window.G;
  const F = () => G.flags;
  const count = (key) => (G.flags[key] = (G.flags[key] || 0) + 1);
  const SP = () => G.D.bg.ch7;
  const px = (g, x, y, c, w = 1, h = 1) => { g.fillStyle = c; g.fillRect(Math.round(x), Math.round(y), w, h); };
  const ALT = { okada_nizo: 'okada_nizo__s07', gintoki: 'gintoki__s07', elizabeth: 'elizabeth__s07', katsura_short: 'katsura_short__s07', takasugi: 'takasugi__s07', harusame: 'harusame__s07' };
  function gear(a) { const id = a && ALT[a.cid]; if (id && G.D.chars[id]) a.alt = [G.atlas(id)]; return a; }
  const ease = (u) => 1 - Math.pow(1 - G.clamp(u, 0, 1), 3);

  // 红色的斩击线（冲击帧那一下）
  function slashLine(S, x0, y0, x1, y1, life = 0.35) {
    const st = G.world.stage, t0 = st.t;
    const p = S.prop({ type: 'custom', x: 0, y: 0, depth: 9990, draw: (g, x, y, t) => {
      const u = (t - t0) / life;
      if (u > 1) return;
      const cx = st.camX;
      g.save();
      g.globalAlpha = 1 - u;
      g.strokeStyle = 'rgb(230,30,50)'; g.lineWidth = 5 * (1 - u) + 1;
      g.beginPath(); g.moveTo(x0 - cx, y0); g.lineTo(G.lerp(x0, x1, Math.min(1, u * 4)) - cx, G.lerp(y0, y1, Math.min(1, u * 4))); g.stroke();
      g.strokeStyle = '#fff'; g.lineWidth = 1;
      g.beginPath(); g.moveTo(x0 - cx, y0); g.lineTo(G.lerp(x0, x1, Math.min(1, u * 4)) - cx, G.lerp(y0, y1, Math.min(1, u * 4))); g.stroke();
      g.restore();
    } });
    G.world.ticks.push(() => { if (st.t - t0 > life + 0.05) { S.unprop(p); return true; } return false; });
  }
  // 飘落的红色花瓣（篇章的主题色）
  function petals(S, n = 18, dur = 3) {
    const st = G.world.stage, t0 = st.t, rnd = G.prng(77);
    const ps = Array.from({ length: n }, () => [rnd() * G.W, rnd() * 60 - 40, 10 + rnd() * 16, rnd() * 6]);
    const p = S.prop({ type: 'custom', x: 0, y: 0, depth: 9980, draw: (g, x, y, t) => {
      const u = t - t0;
      if (u > dur) return;
      g.globalAlpha = Math.min(1, (dur - u) / 0.6);
      for (const [x0, y0, v, ph] of ps) px(g, G.mod(x0 + u * 14 + Math.sin(u * 2 + ph) * 8, G.W), y0 + u * v * 2.2, ph > 3 ? 'rgb(220,40,60)' : 'rgb(255,110,130)', 2, 1);
      g.globalAlpha = 1;
    } });
    G.world.ticks.push(() => { if (st.t - t0 > dur + 0.1) { S.unprop(p); return true; } return false; });
  }

  // ================================================================ 月夜的桥（过场）
  async function bridgeAmbush(S) {
    const p = S.player, st = G.world.stage;
    p.visible = false;
    S.letterbox(true);
    const k = S.spawn('katsura', 70, 152, { id: 'katsura', name: '桂', facing: 1 });
    const e = gear(S.spawn('elizabeth', 46, 156, { id: 'elizabeth', name: '伊丽莎白', facing: 1 }));
    const n = gear(S.spawn('okada_nizo', 330, 152, { id: 'nizo', name: '？？？', facing: -1 }));
    S.pose(n, 'shadow_walk');
    S.music('tension', 0.5);
    await S.fadeIn(0.8);
    await Promise.all([S.walk(k, 150, 152, { speed: 30 }), S.walk(e, 126, 156, { speed: 30 }), S.animate(2.6, (u) => { n.x = 330 - u * 70; })]);
    S.pose(n, 'shadow_idle');
    await S.say('katsura', '……夜里的江户，还真是安静。', { expr: 'normal' });
    S.sfx('heartbeat', 0.8);
    await S.wait(0.5);
    S.zoom(1.5, 210, 130, 0.4);
    await S.wait(0.5);
    // 他消失了 → 冲击帧：一道红色的斩击穿过桂
    n.visible = false;
    S.sfx('whoosh', 0.8, 1.4);
    await S.wait(0.1);
    S.impact(3);
    S.sfx('slash_big', 1.0); S.sfx('impact', 0.8);
    S.flash(0.12, 0.6, '#ff3040');
    slashLine(S, k.x - 40, k.y - 24, k.x + 40, k.y - 18);
    petals(S, 22, 3);
    k.visible = false;
    S.shake(4, 0.3);
    await S.wait(0.6);
    S.zoom(1, null, null, 0.4);
    // 一缕长发飘落，落在桥板上
    const hair = S.prop({ type: 'custom', x: 150, y: 0, depth: 300, h0: st.t, draw: (g, x, y, t) => {
      const u = Math.min(1, (t - hair.h0) / 1.6), landed = u >= 1;
      const ang = landed ? 84 : Math.floor(Math.sin(t * 3) * 34 / 6) * 6;
      const im = G.image(SP().hair[String(ang)]);
      if (G.ready(im)) g.drawImage(im, Math.round(x + Math.sin(t * 2.2) * 10 * (1 - u) - im.width / 2), Math.round(G.lerp(60, 150, u) - im.height / 2));
    } });
    await S.wait(1.8);
    // 伊丽莎白一个人，牌子：「桂先生……」
    S.pose(e, 'sign_katsura', { restart: true });
    S.sfx('pop', 0.5);
    await S.wait(0.6);
    S.pose(e, 'sign_katsura_loop');
    await S.say('elizabeth', '［牌子］桂先生……', { actor: e, name: '伊丽莎白' });
    await S.fadeOut(1.0);
    S.unprop(hair);
    S.remove(n); S.remove(e); S.remove(k);
    S.letterbox(false);
  }

  // ================================================================ 第二天夜里：桥上调查
  async function talkEliz7(S, a) {
    S.pose(a, 'sign_katsura_loop');
    await S.say('elizabeth', '［牌子］桂先生……', { actor: a, name: '伊丽莎白' });
    if (count('eliz7') === 1) {
      await S.say('gintoki', '……昨晚你们走到这里，然后他就不见了？');
      await S.say('gintoki', '那家伙从小就麻烦。……不过，也不是会随随便便死掉的人。');
    }
    S.unpose(a);
  }
  const BRIDGE_HOT = [
    { id: 'hair', x: 150, y: 154, r: 16, ry: 10, label: '桥板', ly: 118,
      use: async (S) => {
        if (F().hair) { await S.say('gintoki', '……假发的头发。剪得真干净。'); return; }
        F().hair = true;
        await S.say(null, '桥板的缝里夹着一缕长长的黑发。切口平整得吓人。');
        await S.say('gintoki', '……这是假发的头发。');
        await S.say('gintoki', '能把那家伙的头发削成这样的剑……不是普通的刀。');
        S.hint('桥那头好像有人', 4);
      } },
    { id: 'moon', x: 256, y: 150, r: 14, ry: 8, label: '月亮', ly: 60,
      use: async (S) => { await S.say(null, '巨大的月亮挂在河面上。倒影被风吹得一闪一闪。'); } },
    { id: 'river', x: 60, y: 160, r: 20, ry: 6, label: '河面', ly: 130,
      use: async (S) => { await S.say(null, '河水黑漆漆的。……什么都看不见。'); } },
  ];
  async function onRoofs(S) {
    const p = S.player;
    await S.fadeOut(0.6);
    await S.setStage('roofs_red_ch7', { x: 1180, y: 166, facing: 1, fade: false });
    p.visible = false;
    const n = gear(S.spawn('okada_nizo', 1270, 160, { id: 'nizo', name: '冈田似藏', facing: -1 }));
    S.camera(1100);
    S.letterbox(true);
    S.music('tension', 0.5);
    await S.fadeIn(0.6);
    // 拔刀：红色的触手爬上手臂，心跳
    S.pose(n, 'benizakura_grow', { restart: true });
    S.sfx('shing', 0.8);
    await S.wait(0.3);
    S.nameCard('okada_nizo');
    for (let i = 0; i < 3; i++) { S.sfx('heartbeat', 0.7); S.flash(0.1, 0.25, '#ff2030'); await S.wait(0.6); }
    S.pose(n, 'benizakura');
    await S.say('okada_nizo', '红樱……还没吃饱呢。', { actor: n, expr: 'evil' });
    S.sfx('shine', 0.5);
    G.fx.spark(n.x + 14, n.y - 20, '#ffffff', 6);
    await S.wait(0.5);
    await S.fadeOut(0.6);
    S.camera(null);
    p.visible = true;
    S.letterbox(false);
  }

  // ================================================================ 雷雨中的桥：似藏 Boss 战（两个阶段）
  function lightningBolt(S) {
    const st = G.world.stage, bolts = G.D.bg.bridge_storm.bolts, b = bolts[Math.floor(Math.random() * bolts.length)], t0 = st.t;
    S.lightning();
    const p = S.prop({ type: 'custom', x: 0, y: 0, depth: -1, draw: (g, x, y, t) => {
      if (t - t0 < 0.18 && G.ready(G.image(b.image))) g.drawImage(G.image(b.image), b.x, b.y);
    } });
    G.world.ticks.push(() => { if (st.t - t0 > 0.25) { S.unprop(p); return true; } return false; });
  }
  async function stormFight(S) {
    const p = gear(S.player);
    await S.setStage('bridge_storm_ch7', { x: 100, y: 154, facing: 1, fade: false });
    const st = G.world.stage;
    const n = gear(S.spawn('okada_nizo', 290, 154, { id: 'nizo', name: '冈田似藏', facing: -1 }));
    S.pose(n, 'ready_evil');
    S.letterbox(true);
    await S.fadeIn(0.6);
    lightningBolt(S);
    await S.say('okada_nizo', '……白夜叉。你的血，红樱会喜欢的。', { actor: n, expr: 'evil' });
    await S.say('gintoki', '把假发的头发还回来。……顺便，把那把恶心的刀也扔了。', { expr: 'angry' });
    S.unpose(n);
    S.letterbox(false);
    S.hint('似藏的妖刀「红樱」——看准他的挥刀，躲开、按住 L 挡，再还手', 6);
    let flashes = 0;
    const storm = (dt) => { if (G.world.stage !== st) return true; if (Math.random() < dt / 4.5) { flashes++; lightningBolt(S); } return false; };
    G.world.ticks.push(storm);
    await S.fight({
      arena: [8, 376],
      music: 'battle',
      waves: [[{ actor: 'nizo', cid: 'okada_nizo', name: '人斩 冈田似藏', hp: 170, boss: true, speed: 54, range: 28, minHp: 1,
        moves: ['E_SLASH', 'E_SLASH', 'E_HEAVY'] }]],
      events: [{
        when: () => { const b = S.actor('nizo'); return !!(b && b.hp <= 95); },
        run: async (S) => {
          // 红樱的触手一甩：银时被砍中、跪地 → 眼神一变 → 站起来
          const b = S.actor('nizo');
          S.letterbox(true);
          S.pose(b, 'thrust_evil', { restart: true });
          S.sfx('slash_big', 1.0);
          slashLine(S, b.x - 50, b.y - 30, b.x + 10, b.y - 10, 0.3);
          await S.wait(0.2);
          S.flash(0.1, 0.6, '#ff2030'); S.shake(4, 0.3); S.sfx('hit', 1.0);
          S.pose(p, 'hit_sad', { restart: true });
          await S.wait(0.5);
          S.pose(p, 'kneel_bokuto_sad');
          await S.say('okada_nizo', '……这把刀会吃人。吃得越多，就越强。你挡不住的。', { actor: b, expr: 'evil' });
          S.zoom(2.6, p, -22, 0.3);
          await S.wait(0.4);
          S.pose(p, 'kneel_bokuto_angry');
          S.sfx('shine', 0.7);
          await S.say('gintoki', '……吃人的刀？', { expr: 'angry' });
          await S.say('gintoki', '我的剑，是用来守护该守护的东西的。……被刀吃掉的家伙，没资格叫剑客。', { expr: 'angry' });
          S.zoom(1, null, null, 0.3);
          S.unpose(p);
          S.sfx('charge', 0.6);
          // 第二阶段：红樱长大，攻击范围更大、更快
          b.scale = 1.18; b.speed = 66; b.range = 36; b.moves = [G.MOVES.E_HEAVY, G.MOVES.E_SLASH, G.MOVES.E_HEAVY];
          b.tint = { color: 'rgb(200,30,40)', k: 0.22 };
          S.letterbox(false);
          S.hint('第二阶段：红樱的攻击范围变大了！', 4);
        },
      }],
      endWhen: () => { const b = S.actor('nizo'); return !!(b && b.team === 'enemy' && b.hp <= 12); },
      after: null,
    });
    // 最后一击：两人交错 → 冲击帧 → 红樱碎裂
    const b = S.actor('nizo');
    b.team = 'npc'; G.ui.boss = null; b.tint = null;
    S.letterbox(true);
    await Promise.all([S.walk(p, 120, 154, { speed: 90 }), S.walk(b, 270, 154, { speed: 90 })]);
    S.face(p, b); S.face(b, p);
    S.sfx('charge', 0.6);
    await S.wait(0.4);
    S.sfx('dash', 0.8);
    await Promise.all([S.walk(p, 300, 154, { speed: 420, anim: 'run' }), S.walk(b, 90, 154, { speed: 420, anim: 'run' })]);
    S.impact(3);
    S.sfx('slash_big', 1.0); S.sfx('impact', 1.0);
    slashLine(S, 60, 40, 330, 190, 0.45);
    S.pose(p, 'attack', { restart: true }); S.pose(b, 'attack_end');
    await S.wait(0.6);
    G.fx.word('咔嚓!!', b.x, b.y - 46, 1.2);
    S.sfx('glass', 0.9);
    lightningBolt(S);
    S.pose(b, 'attack_broken');
    G.fx.debris(b.x + 12, b.y - 24, ['#d02030', '#ff8090', '#c8ccd8'], 20, [40, 140], 200, 1.0);
    await S.wait(0.8);
    S.pose(b, 'lie_sad');
    S.sfx('thud', 0.8);
    await S.say('okada_nizo', '……红樱……', { actor: b, expr: 'sad' });
    await S.say('gintoki', '……刀断了。剩下的，你自己去跟它谈吧。');
    await S.fadeOut(0.8);
    S.letterbox(false);
  }

  // ================================================================ 鬼兵队的船，高杉
  async function takasugiShip(S) {
    const p = S.player, sp = SP();
    await S.setStage('ship_moon_ch7', { x: 192, y: 200, fade: false });
    p.visible = false;
    const st = G.world.stage, t0 = st.t;
    const drawShip = (g, d, x, y) => { const im = G.image(d.image); if (G.ready(im)) g.drawImage(im, Math.round(x - d.w / 2), Math.round(y - d.h / 2)); };
    const ships = S.prop({ type: 'custom', x: 0, y: 0, depth: 9000, draw: (g, x, y, t) => {
      const u = t - t0;
      drawShip(g, sp.ship_pirate, 340 - u * 14, 58);
      drawShip(g, sp.ship_cruiser, 40 + u * 8, 150);
      drawShip(g, sp.ship_kiheitai, G.lerp(262, 206, ease(u / 1.6)), 118 + 1.5 * Math.sin(t * Math.PI));
    } });
    S.letterbox(true);
    S.music('tension', 0.6);
    await S.fadeIn(0.6);
    await S.wait(1.6);
    S.unprop(ships);
    await S.setStage('ship_side_ch7', { x: 192, y: 200, fade: false });
    p.visible = false;
    const seat = G.D.bg.ship_side.seat;
    const tk = gear(S.spawn('takasugi', seat[0], seat[1], { id: 'takasugi', name: '高杉', facing: -1 }));
    S.pose(tk, 'sit_rail_norail');
    const st2 = G.world.stage, b0 = st2.t, rnd = G.prng(9);
    const flies = Array.from({ length: 6 }, () => [rnd() * 200 + 100, rnd() * 80 + 40, rnd() * 6]);
    S.prop({ type: 'custom', x: 0, y: 0, depth: 9000, draw: (g, x, y, t) => {    // 金色的蝴蝶
      const u = t - b0, fr = sp.butterfly.frames;
      flies.forEach(([x0, y0, ph], i) => {
        const im = G.image(fr[Math.floor((t + ph) * 8) % fr.length]);
        if (G.ready(im)) g.drawImage(im, Math.round(x0 + Math.sin(u * 0.8 + ph) * 30 - u * 4), Math.round(y0 + Math.sin(u * 1.7 + i) * 10 - u * 3));
      });
    } });
    S.nameCard('takasugi');
    S.sfx('slide_up', 0.5);
    await S.wait(1.2);
    S.pose(tk, 'sit_rail_norail_smug');
    await S.say('takasugi', '我只是要毁掉这个腐朽的世界。', { actor: tk, expr: 'smug' });
    await S.fadeOut(0.8);
    p.visible = true;
    S.letterbox(false);
  }

  // ================================================================ 甲板：短发的桂，背靠背
  async function deckFight(S) {
    const p = S.player;
    await S.setStage('deck_f_ch7', { x: 192, y: 180, facing: 1, fade: false });
    const st = G.world.stage;
    const ring = [[60, 170, 1], [100, 196, 1], [300, 168, -1], [330, 194, -1], [40, 186, 1], [350, 182, -1]];
    const pirates = ring.map(([x, y, f], i) => gear(S.spawn('harusame', x, y, { id: `hp${i}`, name: '春雨海盗', facing: f })));
    S.letterbox(true);
    S.music('battle', 0.5);
    await S.fadeIn(0.5);
    await S.say('harusame', '白夜叉！把你的脑袋留下！', { name: '春雨海盗', actor: pirates[2], expr: 'angry' });
    // 一个冲上来——桂从天而降
    const a = pirates[2];
    S.pose(a, 'charge_angry');
    await S.walk(a, p.x + 30, p.y, { speed: 160, anim: 'charge_angry' });
    S.sfx('fall_whistle', 0.6);
    const k = gear(S.spawn('katsura_short', p.x + 40, p.y, { id: 'katsura', name: '桂', facing: -1 }));
    k.z = 120;
    await S.arc(k, p.x + 36, p.y, 4, 0.3, { anim: 'jump', z1: 0 });
    S.sfx('slash_big', 0.9);
    G.fx.word('唰!!', a.x, a.y - 40, 0.8);
    await S.arc(a, a.x + 80, a.y, 40, 0.5, { anim: 'fly' });
    S.remove(a);
    S.pose(k, 'ready_determined');
    S.zoom(2.4, k, -24, 0.12);
    G.fx.speedLines(192, 100, { count: 36, inner: 70, life: 0.6, color: '#ffffff' });
    S.sfx('shine', 0.6);
    await S.wait(0.7);
    S.zoom(1, null, null, 0.3);
    await S.say('gintoki', '……假发？你那头长发呢。', { expr: 'shock' });
    await S.say('katsura_short', '剪掉了。……一点小意外。', { actor: k, expr: 'determined' });
    // 背靠背
    k.facing = 1; p.facing = -1;
    k.x = p.x + 18;
    S.pose(p, 'ready_smug');
    await S.say('katsura_short', '背后交给你了，银时。', { actor: k, expr: 'determined' });
    await S.say('gintoki', '别拖后腿啊，假发。', { expr: 'smug' });
    // 桂转过身冲着银时的后脑勺：「不是假发，是桂！」
    k.facing = -1;
    S.zoom(1.8, (p.x + k.x) / 2, p.y - 24, 0.12);
    S.sfx('vein', 0.7); S.shake(4, 0.3);
    G.fx.speedLines(192, 100, { count: 30, inner: 60, life: 0.5, color: '#ffffff' });
    G.fx.word('是桂!!', k.x + 10, k.y - 50, 1.0);
    G.fx.img(SP().vein, k.x - 4, k.headY() + 2, { life: 1.2, pulse: true });
    await S.say('katsura_short', '不是假发，是桂！', { actor: k, expr: 'angry' });
    S.pose(p, 'nosepick_normal');
    G.fx.word('抠抠', p.x - 16, p.y - 44, 0.8);
    await S.wait(0.6);
    S.zoom(1, null, null, 0.2);
    G.fx.word('杀啊——!!', 192, 120, 0.9);
    S.sfx('crowd', 0.5);
    await S.say('harusame', '别光顾着吵架！上啊！', { name: '春雨海盗', actor: pirates[0], expr: 'angry' });
    S.unpose(p); S.unpose(k);
    S.letterbox(false);
    S.hint('和桂一起打春雨海盗！敌人从两边来', 6);
    await S.fight({
      arena: [8, 376],
      allies: ['katsura'], allyHp: 100,
      music: 'battle',
      waves: [
        pirates.filter((q) => !q.remove).map((q) => ({ actor: q.id, cid: 'harusame', name: '春雨海盗', hp: 28 })),
        [{ cid: 'harusame', id: 'hq1', name: '春雨海盗', hp: 30, side: 'left' }, { cid: 'harusame', id: 'hq2', name: '春雨海盗', hp: 30 },
          { cid: 'harusame', id: 'hq3', name: '春雨海盗', hp: 30, side: 'left' }, { cid: 'harusame', id: 'hqb', name: '春雨海盗 小头目', hp: 110, boss: true, scale: 1.2, speed: 44, moves: ['E_SLASH', 'E_HEAVY'] }],
      ],
      reinforce: { every: 3.5, max: 4, make: (i) => ({ cid: 'harusame', id: `hr${i}`, name: '春雨海盗', hp: 22, side: i % 2 ? 'left' : 'right' }) },
      after: null,
    });
    await finale(S);
  }

  // ================================================================ 上层甲板：高杉
  async function finale(S) {
    const p = S.player;
    S.letterbox(true);
    await S.say('katsura_short', '……背后，果然还是交给你最放心。', { actor: S.actor('katsura'), expr: 'determined' });
    await S.fadeOut(0.6);
    await S.setStage('deck_g_ch7', { x: 120, y: 184, facing: 1, fade: false });
    const st = G.world.stage;
    const top = G.D.bg.deck_g.upper_top;
    const tk = gear(S.spawn('takasugi', 300, top, { id: 'takasugi', name: '高杉', facing: -1 }));
    S.pose(tk, 'smoke_smug');
    const k = gear(S.spawn('katsura_short', 160, 182, { id: 'katsura', name: '桂', facing: 1 }));
    const e = gear(S.spawn('elizabeth', 96, 186, { id: 'elizabeth', name: '伊丽莎白', facing: 1 }));
    S.music('tension', 0.5);
    await S.fadeIn(0.6);
    await S.say('takasugi', '……假发。你的头发，倒是挺适合现在这样。', { actor: tk, expr: 'smug' });
    await S.say('katsura_short', '高杉。……我们曾经在同一个老师门下。', { actor: k, expr: 'determined' });
    await S.say('katsura_short', '下次见面，你我就是敌人。', { actor: k, expr: 'determined' });
    S.zoom(2.4, tk, -26, 0.4);
    await S.wait(0.6);
    G.fx.add({ kind: 'puff', x: tk.x - 8, y: tk.y - 30, vx: -6, vy: -10, r: 3, life: 1.2, color: '220,220,230' });
    S.sfx('wind', 0.4);
    await S.say('takasugi', '……随你。', { actor: tk, expr: 'smug' });
    await S.wait(0.6);
    S.zoom(1, null, null, 0.4);
    await S.say('gintoki', '……走吧，假发。伊丽莎白等你等得牌子都举酸了。');
    S.pose(e, 'sign_katsura_loop');
    await S.say('elizabeth', '［牌子］桂先生……', { actor: e, name: '伊丽莎白' });
    await S.fadeOut(1.2);
    S.letterbox(false);
    F().ch7Done = true;
  }

  // ================================================================ 地图（第七章版）
  function defineStages() {
    G.STAGES.bridge_night_ch7 = { id: 'bridge_night_ch7', bg: 'bridge_night', x0: 0, x1: 384, yMin: 146, yMax: 160, music: 'tension', props: [],
      npcs: [{ cid: 'elizabeth', id: 'elizabeth', alt: ['elizabeth__s07'], x: 210, y: 154, facing: -1, label: '伊丽莎白', talk: talkEliz7 }],
      hotspots: BRIDGE_HOT,
      triggers: [{ id: 'east', x0: 330, x1: 999, cond: () => F().hair, run: async (S) => { await onRoofs(S); await stormFight(S); await takasugiShip(S); await deckFight(S); } }] };
    G.STAGES.roofs_red_ch7 = { id: 'roofs_red_ch7', bg: 'roofs_red', x0: 0, x1: 1500, yMin: 156, yMax: 176, props: [] };
    G.STAGES.bridge_storm_ch7 = { id: 'bridge_storm_ch7', bg: 'bridge_storm', x0: 0, x1: 384, yMin: 146, yMax: 162, music: 'battle', props: [] };
    G.STAGES.ship_moon_ch7 = { id: 'ship_moon_ch7', bg: 'ship_moon', x0: 0, x1: 384, yMin: 190, yMax: 210, props: [] };
    G.STAGES.ship_side_ch7 = { id: 'ship_side_ch7', bg: 'ship_side', x0: 0, x1: 384, yMin: 190, yMax: 210, props: [] };
    G.STAGES.deck_f_ch7 = { id: 'deck_f_ch7', bg: 'deck_f', x0: 0, x1: 384, yMin: 162, yMax: 204, props: [] };
    G.STAGES.deck_g_ch7 = { id: 'deck_g_ch7', bg: 'deck_g', x0: 0, x1: 384, yMin: 162, yMax: 204, props: [] };
  }

  // ================================================================ 第七章主流程
  G.STORY.chapter7 = async function (S) {
    defineStages();
    G.fadeAlpha = 0;
    G.world.stage = null;
    await S.chapterCard('ch7');
    const p = gear(new G.Actor('gintoki', 40, 154, { id: 'player', team: 'player', hp: 100, speed: 72, name: '银时' }));
    G.world.player = p;
    G.fadeAlpha = 1;
    await S.setStage('bridge_night_ch7', { x: 20, y: 154, facing: 1, fade: false });
    const el = S.actor('elizabeth');
    if (el) el.visible = false;
    await S.run(async (S) => {
      await bridgeAmbush(S);
      await S.narrate('——第二天夜里。伊丽莎白举着牌子找上了万事屋。', { onBlack: true, auto: 2.2 });
      await S.setStage('bridge_night_ch7', { x: 40, y: 154, facing: 1, fade: false });
      p.visible = true;
      await S.fadeIn(0.6);
      await S.say('gintoki', '（……就是这座桥？）');
      S.hint('在桥上调查一下', 4);
    });
    await S.until(() => G.flags.ch7Done);
  };
})();
