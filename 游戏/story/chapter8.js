// 第八章：真选组动乱篇（原片 s08）
//   夜里的屯所：土方握着妖刀「村麻纱」，紫色的妖气、心跳 → 噗！变成土下座的宅男「托西」（名牌）
//   → 万事屋被叫来照看托西（自由逛：托西、山崎、近藤）
//   → 伊东的房间：圆窗、月光、红眼的叛军剪影，「近藤局长……该退场了。」（名牌，眼镜反光）
//   → 伊东叛变，近藤被困在列车上 → 万事屋开着警车追列车：神乐在车顶上扫射（跟着节拍按键打下叛军）
//   → 列车车顶上的群战：托西的手办被砍碎 → 连按破除诅咒 →「我是……真选组副长——土方十四郎！！」→ 土方加入
//   → 夕阳下的决斗：换成操控土方，打伊东 → 交错的一刀 → 伊东跪下：「……谢谢。」
'use strict';
(function () {
  const G = window.G;
  const F = () => G.flags;
  const count = (key) => (G.flags[key] = (G.flags[key] || 0) + 1);
  const SP = () => G.D.bg.ch8;
  const px = (g, x, y, c, w = 1, h = 1) => { g.fillStyle = c; g.fillRect(Math.round(x), Math.round(y), w, h); };
  const ALT = { hijikata: 'hijikata__s08', ito: 'ito__s08', toshi: 'toshi__s08', yamazaki: 'yamazaki__s08', kagura: 'kagura__s08' };
  function gear(a) { const id = a && ALT[a.cid]; if (id && G.D.chars[id]) a.alt = [G.atlas(id)]; return a; }
  const ease = (u) => 1 - Math.pow(1 - G.clamp(u, 0, 1), 3);
  const GRUNTS = ['s08_grunt0', 's08_grunt1', 's08_grunt2', 's08_grunt3'];

  // 紫色的妖气（土方 / 托西身上）：往上飘的细线
  function aura(S, a, dur, color = 'rgb(150,80,200)') {
    const st = G.world.stage, t0 = st.t, rnd = G.prng(5);
    const wisps = Array.from({ length: 10 }, () => [rnd() * 20 - 10, rnd(), 0.6 + rnd() * 0.8]);
    const p = S.prop({ type: 'custom', x: 0, y: 0, depth: a.y + 0.5, draw: (g, x, y, t) => {
      const u = t - t0;
      if (u > dur) return;
      for (const [dx, ph, sp] of wisps) {
        const k = G.mod(u * sp + ph, 1);
        g.globalAlpha = (1 - k) * Math.min(1, (dur - u) / 0.4);
        px(g, a.x - st.camX + dx + Math.sin(u * 5 + ph * 9) * 2, a.y - 6 - k * 40, color, 1, 4);
      }
      g.globalAlpha = 1;
    } });
    G.world.ticks.push(() => { if (st.t - t0 > dur + 0.1) { S.unprop(p); return true; } return false; });
  }

  // ================================================================ 夜里的屯所：妖刀村麻纱
  async function curse(S) {
    const p = S.player, st = G.world.stage;
    p.visible = false;
    const h = gear(S.spawn('hijikata', 192, 168, { id: 'hijikata_c', name: '土方', facing: 1 }));
    const y = gear(S.spawn('yamazaki', 296, 172, { id: 'yamazaki_c', name: '山崎', facing: -1 }));
    S.pose(h, 'ready_shout'); S.pose(y, 'anpan');
    S.letterbox(true);
    S.music('tension', 0.5);
    await S.fadeIn(0.6);
    await S.say(null, '真选组屯所。副长土方十四郎，握着一把来历不明的旧刀——「妖刀·村麻纱」。');
    aura(S, h, 3.0);
    S.sfx('aura', 0.7);
    S.state('violet', 0.35);
    for (const [k, d] of [[1.25, 0.5], [1.5, 0.35], [1.8, 0.25]]) {
      S.sfx('heartbeat', 0.9);
      await S.zoom(k, h, -24, 0.12);
      await S.zoom(1, null, null, 0.2);
      await S.wait(d);
    }
    // 噗！变成土下座的托西
    S.sfx('pop', 1.0); S.sfx('boing', 0.6);
    G.fx.dust(h.x, h.y, 14);
    G.fx.word('噗!', h.x, h.y - 50, 0.8);
    S.state('violet', 0);
    S.remove(h);
    const t = gear(S.spawn('toshi', 192, 168, { id: 'toshi_c', name: '托西', facing: 1 }));
    S.pose(t, 'beg');
    S.sfx('shock', 0.7);
    S.pose(y, 'idle_dead');
    await S.wait(0.3);
    S.sfx('thud', 0.6); G.fx.word('咚!', t.x + 8, t.y - 20, 0.5);
    S.nameCard('toshi');
    await S.say('toshi', '对不起！我马上去买炒面面包！', { actor: t, expr: 'cry' });
    S.sfx('thud', 0.6); G.fx.word('咚!', t.x + 8, t.y - 20, 0.5);
    await S.wait(0.4);
    S.pose(t, 'figure');
    S.sfx('sparkle', 0.8);
    for (let i = 0; i < 6; i++) G.fx.img(G.D.bg.ch4.note.image, t.x - 10 + i * 4, t.y - 30, { vx: (i - 3) * 6, vy: -20, life: 0.9, fade: true });
    await S.say('yamazaki', '……………………', { actor: y, expr: 'dead' });
    S.sfx('crow', 0.7);
    await S.fadeOut(0.6);
    S.remove(t); S.remove(y);
    S.letterbox(false);
  }

  async function talkToshi(S, a) {
    const n = count('toshi');
    if (n === 1) {
      await S.say('toshi', '啊、啊……您是万事屋的坂田先生吧！初、初次见面！', { actor: a, expr: 'shock' });
      await S.say('gintoki', '……谁？你是谁？我认识的那个蛋黄酱混蛋去哪了？');
      await S.say('toshi', '这个手办是限量版的寺门通酱，只有三百个哦！要摸一下吗？', { actor: a, expr: 'happy' });
      await S.say('shinpachi', '……副长他，被这把刀变成了宅男……？', { expr: 'shock' });
    } else if (n === 2) {
      await S.say('toshi', '打架什么的……太可怕了。我只想回房间打游戏……', { actor: a, expr: 'cry' });
      await S.say('gintoki', '这家伙真的是那个「鬼之副长」吗。');
    } else await S.say('toshi', '对、对不起！我马上去买炒面面包！', { actor: a, expr: 'cry' });
    F().talkedToshi = true;
  }
  async function talkYamazaki8(S, a) {
    await S.say('yamazaki', '副长握了那把「村麻纱」以后就变成这样了。听说是一个宅男的怨念附在刀上……', { actor: a, expr: 'sad' });
    await S.say('yamazaki', '最近伊东参谋那边也怪怪的。局长明天要坐火车去出差，也是伊东参谋安排的。', { actor: a });
    F().talkedYama = true;
  }
  async function talkKondo8(S, a) {
    await S.say('kondo', '万事屋……十四就拜托你们了。', { actor: a, expr: 'sad' });
    await S.say('kondo', '他那个样子，我实在看不下去。……我明天要出趟远门，回来再好好想办法。', { actor: a });
    F().talkedKondo = true;
  }

  // ================================================================ 伊东的房间
  async function itoScene(S) {
    const p = S.player;
    await S.fadeOut(0.6);
    await S.setStage('ito_room_ch8', { x: 30, y: 200, fade: false });
    p.visible = false;
    const ito = gear(S.spawn('ito', 230, 164, { id: 'ito', name: '伊东', facing: -1 }));
    S.pose(ito, 'idle_cold');
    const sils = [300, 326, 352, 270].map((x, i) => { const s = S.spawn('s08_grunt0', x, 150 + (i % 2) * 4, { id: `sil${i}`, facing: -1 }); s.alt = [G.atlas('grunt__s08')]; s.alpha = 0; S.pose(s, 'kneel_sil_redeyes'); return s; });
    S.letterbox(true);
    S.music('tension', 0.5);
    S.sfx('night', 0.35);
    await S.fadeIn(0.6);
    S.nameCard('ito');
    S.sfx('heartbeat', 0.6);
    await S.animate(1.0, (u) => { for (const s of sils) s.alpha = u; });
    S.sfx('aura', 0.45);
    await S.say('ito', '近藤局长……该退场了。', { actor: ito, expr: 'cold' });
    S.zoom(2.6, ito, -26, 0.2);
    S.pose(ito, 'glasses_push', { restart: true });
    S.sfx('impact', 0.5);
    await S.wait(0.35);
    S.sfx('shine', 1.0);
    G.fx.spark(ito.x + 2, ito.headY() + 8, '#ffffff', 8);
    S.flash(0.06, 0.4);
    await S.wait(0.8);
    S.zoom(1, null, null, 0.2);
    await S.fadeOut(0.6);
    S.letterbox(false);
  }

  // ================================================================ 警车追列车：神乐的雨伞机枪
  async function carChase(S) {
    const p = S.player, sp = SP();
    await S.narrate('伊东叛变！列车上的近藤陷入重围——', { onBlack: true, auto: 2.0 });
    await S.setStage('road_ch8', { x: 20, y: 200, fade: false });
    p.visible = false;
    const st = G.world.stage, t0 = st.t, roofY = G.D.bg.road.train_roof_y;
    const car = sp.police_car;
    const rebels = Array.from({ length: 6 }, (_, i) => ({ x0: 214 + i * 30, v: i % 4, hitT: null }));
    const qState = () => (G.ui.qte && G.ui.qte.type === 'rhythm' ? G.ui.qte.state : null);
    S.prop({ type: 'custom', x: 0, y: 0, depth: 500, draw: (g, x, y, t) => {
      const u = t - t0;
      // 车顶上的叛军（跟着列车一起慢慢往后退）；被打中的翻着跟头飞走
      const qs = qState();
      rebels.forEach((r, i) => {
        if (qs && qs[i] === 1 && r.hitT == null) r.hitT = t;
        const at = G.atlas(GRUNTS[r.v]);
        const bx = r.x0 - u * 6;
        if (r.hitT == null) { const a = at.anim('ready'); at.draw(g, 'ready', Math.floor(t * a.fps + i) % a.frames, Math.round(bx), roofY, { flip: true }); }
        else {
          const k = t - r.hitT;
          if (k < 1.2) { const a = at.anim('fly'); at.draw(g, 'fly', Math.floor(t * a.fps) % a.frames, Math.round(bx + 120 * k), Math.round(roofY - 260 * k + 300 * k * k), { flip: true }); }
        }
      });
      // 警车（银时开车、新八和托西在后座、神乐在车顶上）
      const ent = ease(u / 0.45), cxp = Math.round(G.lerp(-190, 104, ent) + 5 * Math.sin(Math.max(0, u - 0.45) * 3.2));
      const bob = Math.floor(t * 12) % 3 === 0 ? -1 : 0;
      const im = G.image(car.frames[Math.floor(t * car.fps) % car.frames.length]);
      if (G.ready(im)) g.drawImage(im, cxp, 104 - car.top + bob);
      if (qs && G.ui.qte && G.ui.qte.t != null) {   // 曳光弹
        const tgt = rebels.findIndex((r) => r.hitT == null);
        if (tgt >= 0 && Math.floor(t * 15) % 2 === 0) {
          const sx = cxp + 84, sy = 104 + bob - 22, ex = rebels[tgt].x0 - u * 6, ey = roofY - 16;
          for (let k = 0; k < 4; k++) {
            const ph = G.mod(t * 7 + k / 4, 1);
            px(g, G.lerp(sx, ex, ph), G.lerp(sy, ey, ph), 'rgb(255,240,150)', 2, 1);
          }
        }
      }
    } });
    S.letterbox(true);
    S.music('battle', 0.5);
    S.sfx('train', 0.6); S.sfx('scooter', 0.4, 0.7);
    await S.fadeIn(0.4);
    await S.wait(0.5);
    G.fx.word('吱——!!', st.camX + 70, 84, 0.6);
    await S.say('gintoki', '这委托，万事屋接下了！', { expr: 'angry' });
    await S.say('shinpachi', '银时先生！警车是从哪里借来的啊！？', { expr: 'shout' });
    await S.say('gintoki', '真选组的车，真选组的事。合情合理。');
    await S.say('kagura', '车顶上那些家伙，交给我阿鲁！', { expr: 'happy' });
    S.letterbox(false);
    const hits = await S.rhythm({ label: '神乐的雨伞机枪！跟着节拍按 J，把车顶上的叛军打下去', notes: [1.0, 1.45, 2.0, 2.45, 3.0, 3.4], window: 0.18, travel: 1.4 });
    void hits;
    S.letterbox(true);
    await S.say('gintoki', '靠过去！跳上车顶！', { expr: 'shout' });
    await S.say('toshi', '诶诶诶！？我、我也要跳吗！？', { expr: 'cry' });
    S.sfx('jump', 0.7);
    await S.fadeOut(0.5);
    S.letterbox(false);
  }

  // ================================================================ 列车车顶：群战 → 破除诅咒
  async function roofFight(S) {
    const p = S.player;
    await S.setStage('train_roof_ch8', { x: 120, y: 152, facing: 1, fade: false });
    p.visible = true;
    const st = G.world.stage;
    const k = gear(S.spawn('kagura', 80, 150, { id: 'kagura', name: '神乐', facing: 1 }));
    const s = S.spawn('shinpachi', 150, 154, { id: 'shinpachi', name: '新八', facing: 1 });
    const t = gear(S.spawn('toshi', 40, 152, { id: 'toshi', name: '托西', facing: 1 }));
    S.pose(t, 'figure');
    k.ranged = 80; k.allyMoves = [G.MOVES.E_GUN];
    await S.fadeIn(0.4);
    S.hint('列车车顶上的叛军！和神乐、新八一起打。托西……先让他躲着', 6);
    await S.fight({
      arena: [8, 376],
      allies: ['kagura', 'shinpachi'], allyHp: 90,
      music: 'battle',
      waves: [
        [0, 1, 2, 3].map((i) => ({ cid: GRUNTS[i], id: `r${i}`, name: '叛军', hp: 26, side: i % 2 ? 'left' : 'right' })),
        [0, 1, 2, 3].map((i) => ({ cid: GRUNTS[(i + 1) % 4], id: `r2_${i}`, name: '叛军', hp: 26, side: i % 2 ? 'left' : 'right' }))
          .concat([{ cid: 's08_grunt2', id: 'rboss', name: '叛军队长', hp: 120, boss: true, scale: 1.2, speed: 44, moves: ['E_SLASH', 'E_HEAVY'] }]),
      ],
      onWave: async (S, i) => { if (i === 1) await breakCurse(S); },
      after: null,
    });
    k.ranged = 0; k.allyMoves = null;
    await S.fadeOut(0.6);
  }
  async function breakCurse(S) {
    const st = G.world.stage, t = S.actor('toshi'), p = S.player;
    S.letterbox(true);
    // 一个叛军的刀扫过来，手办飞出去，摔得粉碎
    const r = gear(S.spawn('s08_grunt3', t.x + 40, t.y, { id: 'rx', name: '叛军', facing: -1 }));
    await S.walk(r, t.x + 20, t.y, { speed: 120, anim: 'run' });
    S.pose(r, 'attack', { restart: true });
    S.sfx('slash', 0.9);
    await S.wait(0.2);
    G.fx.debris(t.x + 6, t.y - 20, ['#ff8ac8', '#ffe0f0', '#a0d8ff'], 14, [30, 120], 260, 0.9);
    S.sfx('glass', 0.9);
    S.pose(t, 'idle_gloom');
    S.remove(r);
    await S.say('toshi', '……通酱的手办……限量版的……', { actor: t, expr: 'cry' });
    aura(S, t, 2.5, 'rgb(120,80,180)');
    S.zoom(2.2, t, -22, 0.4);
    await S.say(null, '心里有个声音在喊——「你到底是谁！？」');
    S.letterbox(false);
    await S.mash({ label: '破除诅咒！连按 J', need: 18, time: 5, decay: 2.0 });
    // 蓝色的气 → 托西变回土方
    S.flash(0.2, 0.9, '#a0c8ff');
    S.sfx('shine', 0.9); S.sfx('impact', 0.8);
    S.zoom(1, null, null, 0.2);
    const h = gear(S.spawn('hijikata', t.x, t.y, { id: 'hijikata', name: '土方', facing: 1 }));
    S.remove(t);
    aura(S, h, 1.5, 'rgb(120,180,255)');
    const ghost = S.prop({ type: 'custom', x: h.x, y: h.y, depth: 900, t0: st.t, draw: (g, x, y, tt) => {   // 托西的魂挥着手飘走
      const u = tt - ghost.t0;
      if (u > 2) return;
      const at = G.atlas('toshi');
      g.globalAlpha = Math.max(0, 0.6 - u * 0.3);
      at.draw(g, 'wave', Math.floor(tt * 8) % at.anim('wave').frames, Math.round(x - 10 - u * 10), Math.round(y - 20 - u * 40));
      g.globalAlpha = 1;
    } });
    S.letterbox(true);
    S.pose(h, 'ready_shout');
    await S.say('hijikata', '我是……真选组副长——土方十四郎！！', { actor: h, expr: 'shout' });
    // 拔刀一闪：一个叛军飞出去
    const r2 = gear(S.spawn('s08_grunt1', h.x + 50, h.y, { id: 'rx2', name: '叛军', facing: -1 }));
    S.pose(h, 'draw', { restart: true });
    S.sfx('slash_big', 1.0);
    await S.wait(0.15);
    G.fx.word('斩!', h.x + 30, h.y - 46, 0.8);
    S.shake(4, 0.3);
    await S.arc(r2, r2.x + 120, r2.y, 50, 0.6, { anim: 'fly' });
    S.remove(r2);
    S.pose(h, 'shoulder_angry');
    await S.say('gintoki', '……终于回来了啊，蛋黄酱混蛋。', { expr: 'smug' });
    await S.say('hijikata', '……少废话。万事屋，借你们的力气一用。', { actor: h, expr: 'angry' });
    S.unprop(ghost);
    S.unpose(h);
    h.team = 'ally'; h.maxHp = h.hp = 100;
    S.letterbox(false);
    S.hint('土方回来了！一起把叛军打下去', 4);
    void p;
  }

  // ================================================================ 夕阳下的决斗：土方 vs 伊东
  async function sunsetDuel(S) {
    await S.narrate('——夕阳下。列车的残骸还在冒烟。', { onBlack: true, auto: 1.6 });
    const hij = S.setPlayer('hijikata', { x: 110, y: 160, facing: 1, name: '土方', hp: 100 });
    gear(hij);
    await S.setStage('sunset_ch8', { x: 110, y: 160, facing: 1, fade: false });
    const ito = gear(S.spawn('ito', 280, 160, { id: 'ito', name: '伊东', facing: -1 }));
    const warm = { color: 'rgb(255,140,80)', k: 0.18 };
    hij.tint = warm; ito.tint = warm;
    S.letterbox(true);
    S.music('epic', 0.6);
    await S.fadeIn(0.8);
    await S.say('ito', '……土方。你从来都不认同我。', { actor: ito, expr: 'cold' });
    await S.say('hijikata', '我认同的是你的本事。……可惜你从来不认同你自己。', { expr: 'angry' });
    // 眼神的特写：先土方，再伊东
    S.zoom(3.2, hij, -28, 0.12); S.sfx('shine', 0.6);
    await S.wait(0.5);
    S.zoom(3.2, ito, -28, 0.12); S.sfx('shine', 0.6);
    await S.wait(0.5);
    S.zoom(1, null, null, 0.2);
    S.letterbox(false);
    S.hint('现在操控的是土方（招式一样：J 攻击、K 跳、L 挡）', 6);
    await S.fight({
      arena: [8, 376],
      music: 'battle',
      waves: [[{ actor: 'ito', cid: 'ito', name: '真选组参谋 伊东鸭太郎', hp: 160, boss: true, speed: 56, range: 28, minHp: 1, moves: ['E_SLASH', 'E_SLASH', 'E_HEAVY'] }]],
      endWhen: () => { const b = S.actor('ito'); return !!(b && b.team === 'enemy' && b.hp <= 12); },
      after: null,
    });
    ito.team = 'npc'; G.ui.boss = null;
    ito.tint = warm; hij.tint = warm;
    // 交错的一刀
    S.letterbox(true);
    await Promise.all([S.walk(hij, 120, 160, { speed: 90 }), S.walk(ito, 270, 160, { speed: 90 })]);
    S.face(hij, ito); S.face(ito, hij);
    S.stopMusic(0.4);
    await S.wait(0.6);
    S.sfx('dash', 0.8);
    await Promise.all([S.walk(hij, 290, 160, { speed: 460, anim: 'run' }), S.walk(ito, 100, 160, { speed: 460, anim: 'run' })]);
    S.impact(3);
    S.sfx('slash_big', 1.0); S.sfx('impact', 1.0);
    S.pose(hij, 'attack', { restart: true }); S.pose(ito, 'attack', { restart: true });
    await S.wait(1.0);
    S.sfx('clang', 0.6, 0.7);
    S.pose(ito, 'kneel_smile');
    S.sfx('thud', 0.6);
    await S.wait(0.6);
    S.music('sad', 0.6);
    S.zoom(2.2, ito, -20, 1.2);
    await S.say('ito', '……谢谢。', { actor: ito, expr: 'smile' });
    S.zoom(1, null, null, 0.8);
    hij.facing = 1;
    S.pose(hij, 'smoke');
    await S.say('hijikata', '……………………', { expr: 'exhale' });
    S.pose(ito, 'kneel_sleep');
    await S.wait(1.2);
    await S.fadeOut(1.4);
    S.letterbox(false);
    F().ch8Done = true;
  }

  // ================================================================ 地图（第八章版）
  function defineStages() {
    G.STAGES.hq_room_ch8 = { id: 'hq_room_ch8', bg: 'hq_room', x0: 0, x1: 384, yMin: 160, yMax: 204, music: 'tension',
      props: [{ type: 'custom', x: 0, y: 0, depth: 9998, draw: (g) => {     // 妖气染紫的房间
        const a = G.world.stage.state.violet || 0;
        if (a > 0) { g.fillStyle = `rgba(90,30,130,${a})`; g.fillRect(0, 0, G.W, G.H); }
      } }],
      npcs: [
        { cid: 'toshi', id: 'toshi', alt: ['toshi__s08'], x: 192, y: 172, facing: 1, anim: 'figure', label: '托西', talk: talkToshi },
        { cid: 'yamazaki', id: 'yamazaki', alt: ['yamazaki__s08'], x: 300, y: 176, facing: -1, anim: 'anpan', label: '山崎', talk: talkYamazaki8 },
        { cid: 'kondo', id: 'kondo', x: 88, y: 178, facing: 1, label: '近藤', talk: talkKondo8 },
        { cid: 'shinpachi', id: 'shinpachi', x: 140, y: 190, facing: 1, label: '新八',
          talk: async (S, a) => { await S.say('shinpachi', '……银时先生，副长要是一直这样，真选组会怎么样啊。', { actor: a, expr: 'sad' }); } },
      ],
      hotspots: [{ id: 'scroll', x: 150, y: 164, r: 16, ry: 8, label: '挂轴', ly: 50,
        use: async (S) => { await S.say(null, '墙上挂着「诚」字。'); await S.say('gintoki', '……这个字，现在的托西大概看不懂吧。'); } }],
      triggers: [{ id: 'toIto', x0: 0, x1: 999, cond: () => F().talkedToshi && F().talkedYama && F().talkedKondo,
        run: async (S) => { await itoScene(S); await carChase(S); await roofFight(S); await sunsetDuel(S); } }] };
    G.STAGES.ito_room_ch8 = { id: 'ito_room_ch8', bg: 'ito_room', x0: 0, x1: 384, yMin: 160, yMax: 204, props: [] };
    G.STAGES.road_ch8 = { id: 'road_ch8', bg: 'road', x0: 0, x1: 384, yMin: 196, yMax: 210, props: [] };
    G.STAGES.train_roof_ch8 = { id: 'train_roof_ch8', bg: 'train_roof', x0: 0, x1: 384, yMin: 144, yMax: 158, props: [] };
    G.STAGES.sunset_ch8 = { id: 'sunset_ch8', bg: 'sunset', x0: 0, x1: 384, yMin: 150, yMax: 172, props: [] };
  }

  // ================================================================ 第八章主流程
  G.STORY.chapter8 = async function (S) {
    defineStages();
    G.fadeAlpha = 0;
    G.world.stage = null;
    await S.chapterCard('ch8');
    const p = new G.Actor('gintoki', 40, 186, { id: 'player', team: 'player', hp: 100, speed: 72, name: '银时' });
    G.world.player = p;
    G.fadeAlpha = 1;
    await S.setStage('hq_room_ch8', { x: 40, y: 186, facing: 1, fade: false });
    for (const id of ['toshi', 'yamazaki', 'kondo', 'shinpachi']) { const a = S.actor(id); if (a) a.visible = false; }
    await S.run(async (S) => {
      await curse(S);
      await S.narrate('——第二天。近藤托万事屋照看「托西」。', { onBlack: true, auto: 1.8 });
      await S.setStage('hq_room_ch8', { x: 40, y: 186, facing: 1, fade: false });
      p.visible = true;
      await S.fadeIn(0.6);
      await S.say('gintoki', '（……真选组的副长，变成了这副样子？）');
      S.hint('和托西、山崎、近藤都说说话', 5);
    });
    await S.until(() => G.flags.ch8Done);
  };
})();
