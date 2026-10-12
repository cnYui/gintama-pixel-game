// 第九章：吉原炎上篇（原片 s09）
//   地下花街吉原：铁顶盖住了天空。晴太想见娘（名牌）→ 苦无扎在脚边，月咏从屋顶落下（名牌）「死心吧。吉原……没有太阳。」
//   → 自由逛吉原大街 → 高塔窗里的日轮（名牌）→ 屋顶上的神威（名牌）「我只对强者感兴趣。」→ 王座间的夜王凤仙（名牌）
//   → 走廊里和凤仙交手：怎么打都没用 → 一拳打穿三道隔扇，飞到大街上 →「我的剑，是用来守护该守护的东西的。」
//   → 控制室（操控月咏）：照铭牌的顺序转齿轮、拉拉杆（解谜）→ 天顶打开，阳光照进吉原
//   → 阳光下的凤仙 Boss 战：把他引进光柱里才打得动 → 跃起，背着太阳的一刀 → 凤仙化成尘：「太阳……原来是这么温暖的东西。」
//   → 晴太和日轮重逢，银时脸朝下趴着：「……糖分……」
'use strict';
(function () {
  const G = window.G;
  const F = () => G.flags;
  const count = (key) => (G.flags[key] = (G.flags[key] || 0) + 1);
  const SP = () => G.D.bg.ch9;
  const px = (g, x, y, c, w = 1, h = 1) => { g.fillStyle = c; g.fillRect(Math.round(x), Math.round(y), w, h); };
  const ALT = { seita: 'seita__s09', tsukuyo: 'tsukuyo__s09', kamui: 'kamui__s09', housen: 'housen__s09', gintoki: 'gintoki__s09' };
  function gear(a) { const id = a && ALT[a.cid]; if (id && G.D.chars[id]) a.alt = [G.atlas(id)]; return a; }
  const ease = (u) => 1 - Math.pow(1 - G.clamp(u, 0, 1), 3);
  const GX = 256;                  // 游戏坐标 = 原片坐标 + 256
  const BOSS_CAM = 250 + GX;       // 阳光下的决战：镜头固定在原片 cam 250

  // ================================================================ 吉原大街（夜）
  async function intro(S) {
    const p = S.player, st = G.world.stage;
    S.letterbox(true);
    const s = gear(S.spawn('seita', st.camX - 20, 172, { id: 'seita', name: '晴太', facing: 1 }));
    await S.fadeIn(0.8);
    await S.say(null, '吉原——江户地下的花街。铁做的天顶盖住了天空，这里从来见不到太阳。');
    S.sfx('run', 0.5);
    await S.walk(s, st.camX + 170, 172, { speed: 150, anim: 'run' });
    G.fx.dust(s.x, s.y, 6);
    S.nameCard('seita');
    await S.say('seita', '我想见娘……哪怕一面也好！', { actor: s, expr: 'determined' });
    // 苦无扎在脚边 → 月咏从屋顶落下
    S.sfx('shine', 0.5, 1.3);
    G.fx.spark(s.x + 84, 84, '#ffffff', 5);
    await S.wait(0.2);
    S.sfx('whoosh', 0.7);
    const kn = S.prop({ type: 'custom', x: s.x + 8, y: s.y + 1, depth: s.y + 1, t0: st.t, draw: (g, x, y, t) => {
      const u = t - kn.t0, wob = u < 0.33 ? Math.round(14 * Math.sin(60 * u) * (1 - 3 * u)) : 0;
      const a = (-128 + wob) * Math.PI / 180, k = 1.3;
      const tx = x + Math.cos(a) * 13 * k, ty = y + Math.sin(a) * 13 * k;
      g.strokeStyle = '#c8ccd8'; g.lineWidth = 1; g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * 8 * k, y + Math.sin(a) * 8 * k); g.stroke();
      g.strokeStyle = '#3a2830'; g.beginPath(); g.moveTo(x + Math.cos(a) * 8 * k, y + Math.sin(a) * 8 * k); g.lineTo(tx, ty); g.stroke();
      g.strokeStyle = '#c8ccd8'; g.beginPath(); g.arc(tx, ty, 2 * k, 0, Math.PI * 2); g.stroke();
    } });
    S.sfx('stab', 0.8);
    G.fx.word('咚!', s.x + 8, s.y - 10, 0.5);
    G.fx.word('!!', s.x, s.y - 40, 0.6);
    S.shake(2, 0.2);
    S.sfx('shock', 0.8);
    await S.arc(s, s.x, s.y, 11, 0.25, { anim: 'shock' });
    S.pose(s, 'idle_sad');
    const tk = gear(S.spawn('tsukuyo', s.x + 50, 172, { id: 'tsukuyo', name: '月咏', facing: -1 }));
    tk.z = 90;
    S.sfx('whoosh', 0.6, 0.8);
    await S.arc(tk, s.x + 50, 172, 2, 0.2, { anim: 'jump', z1: 0 });
    S.sfx('land', 0.7);
    G.fx.dust(tk.x, tk.y, 8);
    S.pose(tk, 'smoke');
    S.nameCard('tsukuyo');
    await S.say('tsukuyo', '死心吧。吉原……没有太阳。', { actor: tk, expr: 'normal' });
    await S.say('gintoki', '……喂喂，对小孩子扔苦无，这就是吉原的待客之道？');
    await S.say('tsukuyo', '吉原的规矩，就是凤仙的规矩。……外面来的天然卷，最好别多管闲事。', { actor: tk });
    S.unprop(kn);
    S.unpose(s); S.unpose(tk);
    s.talk = talkSeita; s.label = '晴太';
    tk.talk = talkTsukuyo; tk.label = '月咏';
    S.letterbox(false);
    S.hint('在吉原大街上逛逛，和晴太、月咏说说话', 6);
  }
  async function talkSeita(S, a) {
    if (count('seita') === 1) {
      await S.say('seita', '我娘叫日轮。她被关在那座塔上……我从来没有见过她。', { actor: a, expr: 'sad' });
      await S.say('gintoki', '……想见就去见。小鬼的委托，万事屋也接。', {});
      await S.say('seita', '真的吗！？……可是我只有这点零花钱……', { actor: a, expr: 'happy' });
      await S.say('gintoki', '……先赊着。');
    } else await S.say('seita', '娘就在那座塔上。窗户里亮着灯的那间。', { actor: a });
    F().seita = true;
  }
  async function talkTsukuyo(S, a) {
    if (count('tsuk') === 1) {
      await S.say('tsukuyo', '凤仙是夜兔族的王。在吉原，没有人能违抗他。', { actor: a });
      await S.say('tsukuyo', '日轮……是他用来锁住整个吉原的锁。', { actor: a, expr: 'sad' });
      await S.say('gintoki', '那就把锁砸了。');
      await S.say('tsukuyo', '……你这个人，真是什么都不懂。', { actor: a });
    } else await S.say('tsukuyo', '头顶上那块铁板，二十年没有打开过。', { actor: a });
    F().tsukuyo = true;
  }
  const STREET_HOT = [
    { id: 'lid', x: 300, y: 166, r: 30, ry: 10, label: '天顶', ly: 30,
      use: async (S) => { await S.say(null, '抬头只能看见铁做的天顶和桁架。挂着的灯笼代替了星星。'); } },
    { id: 'tower', x: 520, y: 166, r: 24, ry: 10, label: '远处的塔', ly: 40,
      use: async (S) => { await S.say(null, '远处有一座高塔，顶上的窗户亮着一点光。'); } },
  ];

  // ================================================================ 塔、屋顶、王座（过场）
  async function cutsTowerRoofThrone(S) {
    const p = S.player;
    await S.fadeOut(0.6);
    // 塔：窗里的日轮
    await S.setStage('tower_ch9', { x: 30, y: 200, fade: false });
    p.visible = false;
    const tw = G.D.bg.tower_night;
    S.prop({ type: 'custom', x: 0, y: 0, depth: 50, draw: (g, x, y, t) => {
      const [wx, wy] = tw.window;
      g.save(); g.beginPath(); g.arc(wx, wy, 19, 0, Math.PI * 2); g.clip();
      g.fillStyle = 'rgb(120,70,60)'; g.fillRect(wx - 20, wy - 20, 40, 40);
      const at = G.atlas('hinowa'), an = at.anim('smile') ? 'smile' : 'idle';
      at.draw(g, an, Math.floor(t * 4) % at.anim(an).frames, wx + 2, wy + 36, { flip: true });
      g.restore();
      g.drawImage(G.image(tw.ring.image), tw.ring.x, tw.ring.y);
    } });
    S.letterbox(true);
    S.sfx('bell', 0.45);
    await S.fadeIn(0.6);
    S.zoom(2.2, 192, 90, 1.2);
    await S.wait(0.6);
    S.nameCard('hinowa');
    await S.say(null, '晴太的母亲，被囚禁在高塔之上。');
    await S.fadeOut(0.6);
    // 屋顶：神威
    await S.setStage('yoshi_roof_ch9', { x: 30, y: 200, fade: false });
    p.visible = false;
    const km = gear(S.spawn('kamui', 244, 151, { id: 'kamui', name: '神威', facing: -1 }));
    S.pose(km, 'sit');
    S.sfx('wind', 0.4);
    await S.fadeIn(0.5);
    S.nameCard('kamui');
    await S.wait(1.0);
    S.zoom(3.4, km, -24, 0.12);
    S.pose(km, 'sit_open_eyes');
    S.sfx('shine', 0.8); S.sfx('sting_dramatic', 0.8);
    S.flash(0.06, 0.55, '#ff3c3c');
    await S.say('kamui', '我只对强者感兴趣。', { actor: km, expr: 'open_eyes' });
    S.zoom(1, null, null, 0.3);
    await S.fadeOut(0.6);
    // 王座间：凤仙
    await S.setStage('throne_ch9', { x: 30, y: 200, fade: false });
    p.visible = false;
    const hs = gear(S.spawn('housen', 256, 166, { id: 'housen', name: '凤仙', facing: -1 }));
    hs.scale = 2;
    S.state('dark', 0.85);
    S.music('battle', 0.5);
    await S.fadeIn(0.4);
    S.sfx('heartbeat', 0.7);
    await S.wait(0.4);
    S.sfx('gong', 0.9); S.sfx('aura', 0.7);
    S.flash(0.12, 0.6, '#ff7864'); S.shake(3, 0.4);
    await S.animate(0.35, (u) => S.state('dark', 0.85 * (1 - u)));
    S.nameCard('housen');
    S.pose(hs, 'idle_smug');
    await S.say('housen', '吉原的太阳，只属于我一人。', { actor: hs, expr: 'smug' });
    await S.fadeOut(0.6);
    S.letterbox(false);
  }

  // ================================================================ 走廊：打不动的凤仙 → 一拳打穿三道隔扇
  async function corridor(S) {
    const p = S.player;
    await S.setStage('corridor_ch9', { x: 160, y: 176, facing: 1, fade: false });
    p.visible = true;
    const st = G.world.stage;
    const hs = gear(S.spawn('housen', 300, 176, { id: 'housen', name: '凤仙', facing: -1 }));
    hs.scale = 1.3;
    S.letterbox(true);
    await S.fadeIn(0.5);
    await S.say('housen', '……地上来的武士。你也是来抢日轮的？', { actor: hs, expr: 'talk' });
    await S.say('gintoki', '我是来砸锁的。顺便，替一个小鬼送封信给他娘。');
    S.letterbox(false);
    S.hint('夜王凤仙！……先撑住', 4);
    await S.fight({
      arena: [st.camX + 8, st.camX + 376],
      music: 'battle',
      waves: [[{ actor: 'housen', cid: 'housen', name: '夜王 凤仙', hp: 999, boss: true, scale: 1.3, speed: 50, range: 32, moves: ['E_PUNCH', 'E_HEAVY'], dmgMul: () => 0.02 }]],
      timer: { label: '撑住！还有 ', until: 12 },
      endWhen: () => G.world.fightT >= 12,
      after: null,
    });
    hs.team = 'npc'; G.ui.boss = null;
    // 一拳：冲击帧 → 飞出去，连穿三道隔扇
    S.letterbox(true);
    S.face(hs, p); S.face(p, hs);
    hs.x = p.x - 46; hs.y = p.y;
    S.pose(p, 'guard');
    S.pose(hs, 'punch', { restart: true, speed: 0.5 });
    S.sfx('charge', 0.6);
    await S.wait(0.35);
    S.sfx('punch_big', 1.0); S.sfx('impact', 0.9);
    S.impact(3);
    S.flash(0.12, 0.8);
    S.sfx('fly_away', 0.6);
    S.camera(p);
    S.pose(p, 'hit', { restart: true });
    const walls = [330, 520, 710].map((x) => st.camX + x - 160);
    const parts = walls.map((x) => S.prop({ type: 'image', image: SP().partition_intact, x, y: 20, ax: 13, ay: 0, depth: 150 }));
    const x0 = p.x, dist = walls[2] + 80 - x0;
    let broken = 0;
    await S.animate(dist / 620, (u) => {
      p.x = x0 + dist * u; p.z = 24 * Math.sin(Math.min(1, u * 3) * Math.PI / 2); p.rot = u * 12;
      while (broken < walls.length && p.x >= walls[broken]) {
        parts[broken].image = SP()[`partition_broken${broken}`];
        S.sfx('crash', 0.9); S.shake(3, 0.2);
        G.fx.debris(walls[broken], 120, ['#efe6cc', '#c8b898', '#7a5a3a', '#3a5aa0'], 16, [60, 260], 420, 1.0);
        G.fx.dust(walls[broken], 160, 3);
        G.fx.word('轰!', walls[broken], 70, 0.45);
        broken++;
      }
    });
    p.rot = 0; p.z = 0;
    S.camera(null);
    await S.fadeOut(0.3);
    // 大街：从店面的墙洞里撞出来
    await S.setStage('yoshi_night_ch9', { x: 694, y: 172, facing: 1, fade: false });
    const st2 = G.world.stage;
    S.camera(GX + 300);
    const hole = SP().hole, rub = SP().rubble;
    S.prop({ type: 'image', image: hole.image, x: 138 + GX + 300, y: 124, ax: -hole.ox, ay: -hole.oy, depth: 100 });
    S.prop({ type: 'image', image: rub.image, x: 222 + GX + 300, y: 162, ax: -rub.ox, ay: -rub.oy, depth: 161 });
    p.x = 138 + GX + 300; p.y = 172; p.z = 36;
    S.flash(0.12, 0.7, '#ffdcaa');
    await S.fadeIn(0.15);
    S.sfx('crash', 1.0); S.sfx('explosion_small', 0.7);
    G.fx.word('轰隆!!', st2.camX + 150, 60, 0.6);
    await S.arc(p, 222 + GX + 300, 176, 26, 0.3, { anim: 'fly', z1: 0 });
    S.pose(p, 'lie'); S.sfx('thud', 0.8);
    await S.wait(0.4);
    S.pose(p, 'kneel_hurt');
    await S.wait(0.4);
    S.zoom(1.9, p, -24, 1.2);
    S.pose(p, 'ready');
    S.sfx('shing', 0.6);
    await S.say('gintoki', '我的剑，是用来守护该守护的东西的。', { expr: 'angry' });
    // 墙洞里，凤仙的黑影
    const shadow = gear(S.spawn('housen', 138 + GX + 300, 130, { id: 'hshadow', facing: 1 }));
    shadow.scale = 1.3; shadow.tint = { color: 'rgb(8,6,12)', k: 1 }; shadow.alpha = 0; shadow.shadow = false;
    S.sfx('heartbeat', 0.6);
    await S.animate(0.6, (u) => { shadow.alpha = u; });
    await S.say('tsukuyo', '……天然卷！撑住！我们去打开天顶！', { name: '月咏' });
    S.zoom(1, null, null, 0.3);
    await S.fadeOut(0.6);
    S.camera(null);
    S.letterbox(false);
  }

  // ================================================================ 控制室（操控月咏）：转齿轮、拉拉杆
  const CTRL = { order: ['left', 'big', 'lever'] };
  function controlProp(S) {
    const sp = SP(), st = G.world.stage;
    return S.prop({ type: 'custom', x: 0, y: 0, depth: 120, draw: (g, x, y, t) => {
      const s = st.state, spin = s.spinT != null ? Math.pow(t - s.spinT, 2) * 500 : 0;
      const rot = (img, cx, cy, deg) => {
        const im = G.image(img.image);
        if (!G.ready(im)) return;
        g.save(); g.translate(cx, cy); g.rotate(deg * Math.PI / 180); g.drawImage(im, -im.width / 2, -im.height / 2); g.restore();
      };
      rot(sp.gear_big, 262, 98, -(spin + (s.big || 0)));
      rot(sp.gear_small, 336, 146, -(-spin * 46 / 30 + 11));
      rot(sp.gear_small, 44, 92, -(spin * 1.3 + 5 + (s.left || 0)));
      g.drawImage(G.image(G.D.bg.control.floor_img), 0, 160);
      const on = s.alarm && Math.floor(t * 6) % 2 === 0;
      if (on) { g.save(); g.globalCompositeOperation = 'lighter'; g.drawImage(G.image(sp.alarm_glow), 124, -6); g.restore(); }
      g.drawImage(G.image(on ? sp.alarm_on : sp.alarm_off), 144, 12);
      g.drawImage(G.image(sp.lever_base), 172, 140);
      const ang = G.clamp(Math.round((s.lever || 2) / 2), 0, 33);
      g.drawImage(G.image(sp.lever_arms[ang]), 180, 106);
      if (s.steamT != null && t - s.steamT < 1.2) {
        const u = t - s.steamT;
        g.fillStyle = `rgba(236,232,226,${(1 - u / 1.2).toFixed(2)})`;
        for (let i = 0; i < 5; i++) { g.beginPath(); g.arc(336 + i * 4 - 8, 140 - u * 30 - i * 3, 3 + u * 6, 0, Math.PI * 2); g.fill(); }
      }
      // 铭牌
      g.fillStyle = '#5a4a3a'; g.fillRect(96, 118, 34, 16); g.fillStyle = '#c8b070'; g.fillRect(98, 120, 30, 12);
    } });
  }
  async function wrongStep(S, what) {
    const st = G.world.stage;
    st.state.alarm = true;
    S.sfx('fail', 0.6); S.sfx('clang', 0.6);
    S.shake(2, 0.2);
    await S.say(null, `${what}——「咔！」机关卡住，又弹回了原位。`);
    CTRL.step = 0; st.state.left = 0; st.state.big = 0;
    st.state.alarm = false;
  }
  function ctrlHot(id, label, x, y, ly, run) {
    return { id, x, y, r: 18, ry: 12, label, ly, use: async (S) => {
      if (F().opened) return;
      if (id === 'plate') { await run(S); return; }
      if (CTRL.order[CTRL.step || 0] !== id) { await wrongStep(S, label); return; }
      CTRL.step = (CTRL.step || 0) + 1;
      await run(S);
    } };
  }
  const CTRL_HOT = [
    ctrlHot('plate', '铭牌', 113, 168, 104, async (S) => {
      await S.say(null, '铭牌上刻着：「开顶之序——先解左锁，再转主轮，后落其杆。」');
      await S.say('seita', '左锁……是左边那个小齿轮吧？主轮是最大的那个！', { name: '晴太', expr: 'determined' });
    }),
    ctrlHot('left', '左边的齿轮', 44, 168, 60, async (S) => {
      const st = G.world.stage;
      S.sfx('squeak', 0.6, 0.6);
      await S.animate(0.6, (u) => { st.state.left = 90 * u; });
      await S.say(null, '左边的小齿轮「咔」地转了一格，锁销松开了。');
    }),
    ctrlHot('big', '大齿轮', 262, 168, 50, async (S) => {
      const st = G.world.stage;
      S.sfx('squeak', 0.6, 0.5);
      await S.animate(0.8, (u) => { st.state.big = 60 * u; });
      await S.say(null, '主轮沉重地转了半圈。拉杆那边传来「咔哒」一声。');
    }),
    ctrlHot('lever', '拉杆', 196, 168, 96, async (S) => { await pullLever(S); }),
  ];
  async function pullLever(S) {
    const st = G.world.stage, p = S.player, s = S.actor('seita');
    S.letterbox(true);
    await S.say('tsukuyo', '……太重了。晴太，抓住把手！', { expr: 'determined' });
    S.sfx('squeak', 0.5, 0.6);
    await S.walk(s, 194, 160, { speed: 90 });
    S.pose(s, 'dangle');
    S.letterbox(false);
    const pm = S.mash({ label: '「嘿——!!」连按 J 把拉杆推到底！', need: 18, time: 6, decay: 1.6 });
    G.world.ticks.push(() => { if (!G.ui.qte) return true; st.state.lever = 2 + 18 * G.clamp((G.ui.qte.v || 0) / (G.ui.qte.need || 18), 0, 1) + Math.sin(st.t * 30) * 1.5; return false; });
    await pm;
    S.letterbox(true);
    G.fx.word('嘿——!!', 104 + st.camX, 56, 0.5);
    await S.animate(0.2, (u) => { st.state.lever = G.lerp(20, 66, u); });
    S.sfx('clang', 1.0); S.sfx('impact', 0.6);
    G.fx.word('咔嚓!!', 292 + st.camX, 54, 0.6);
    st.state.lever = 66; st.state.spinT = st.t; st.state.alarm = true; st.state.steamT = st.t;
    S.sfx('engine_hum', 0.6);
    S.pose(s, 'cheer');
    F().opened = true;
    await S.wait(1.0);
    await S.say('seita', '动、动了！天顶在动！', { name: '晴太', expr: 'happy' });
    await S.fadeOut(0.5);
    S.letterbox(false);
    await sunrise(S);
  }

  // ================================================================ 天顶打开（往上看）
  async function sunrise(S) {
    const sp = SP(), st = G.world.stage;
    let t0 = null;
    S.insert((g, t) => {
      if (t0 == null) t0 = t;
      const u = t - t0, open = ease((u - 0.3) / 0.75), sun = ease((u - 0.5) / 0.7), dy = Math.round(Math.sin(u * 40) * (u < 1.3 ? 2 : 0));
      g.fillStyle = '#000'; g.fillRect(0, 0, G.W, G.H);
      if (open > 0) g.drawImage(G.image(sp.hatch_sky), 87, 52 + dy);
      const sl = Math.round(open * 113);
      g.save(); g.beginPath(); g.rect(87, 52 + dy, 210, 100); g.clip();
      g.drawImage(G.image(sp[sun > 0.5 ? 'leaf_left_sun' : 'leaf_left_night']), 87 - sl, 52 + dy);
      g.drawImage(G.image(sp[sun > 0.5 ? 'leaf_right_sun' : 'leaf_right_night']), 191 + sl, 52 + dy);
      g.restore();
      g.drawImage(G.image(sp.ceiling_night), -128, 12 + dy);
      if (sun > 0) { g.globalAlpha = sun; g.drawImage(G.image(sp.ceiling_sun), -128, 12 + dy); g.globalAlpha = 1; }
      if (open > 0) {            // 放射状的光
        g.save(); g.globalCompositeOperation = 'lighter';
        for (let i = 0; i < 14; i++) {
          const a = (2 * Math.PI * i) / 14 + 0.15 * u, w = 0.06;
          g.fillStyle = `rgba(255,244,200,${(open * 1.1 * (0.25 + 0.15 * Math.sin(3 * u + i)) * 0.6).toFixed(3)})`;
          g.beginPath(); g.moveTo(192, 104); g.lineTo(192 + Math.cos(a - w) * 420, 104 + Math.sin(a - w) * 420); g.lineTo(192 + Math.cos(a + w) * 420, 104 + Math.sin(a + w) * 420); g.closePath(); g.fill();
        }
        g.restore();
      }
      if (u > 1.6) { g.fillStyle = `rgba(255,255,255,${Math.min(1, (u - 1.6) / 0.35).toFixed(2)})`; g.fillRect(0, 0, G.W, G.H); }
    });
    S.sfx('thunder', 0.6);
    S.shake(2, 1.2);
    await S.wait(0.5);
    S.sfx('slide_up', 0.7);
    await S.wait(0.5);
    S.music('epic', 0.6);
    S.sfx('shine', 1.0);
    await S.wait(0.9);
    S.sfx('sparkle', 0.8);
    await S.wait(0.4);
    void st;
  }

  // ================================================================ 阳光下的决战
  function shaftsProp(S, nm, worldOx) {
    const P = SP().shafts[nm], st = G.world.stage;
    return S.prop({ type: 'custom', x: 0, y: 0, depth: 9000, draw: (g, x, y, t) => {
      const ox = worldOx - st.camX, oy = P.oy;
      g.save(); g.globalCompositeOperation = 'lighter';
      P.shafts.forEach(([base, w], i) => {
        const a = Math.PI / 2 - base + 0.02 * Math.sin(0.6 * t + i);
        g.fillStyle = `rgba(255,238,190,${(P.alpha * 0.55 * (0.7 + 0.3 * Math.sin(1.3 * t + 1.7 * i))).toFixed(3)})`;
        g.beginPath(); g.moveTo(ox, oy); g.lineTo(ox + Math.cos(a - w) * 520, oy + Math.sin(a - w) * 520); g.lineTo(ox + Math.cos(a + w) * 520, oy + Math.sin(a + w) * 520); g.closePath(); g.fill();
      });
      g.restore();
    } });
  }
  function inShaft(a, nm, worldOx) {        // 脚下这一点在不在某道光柱里
    if (!a) return false;
    const P = SP().shafts[nm], t = G.world.stage.t, dy = a.y - P.oy;
    return P.shafts.some(([base, w], i) => {
      const am = Math.PI / 2 - base + 0.02 * Math.sin(0.6 * t + i);
      const xa = worldOx + dy * Math.cos(am - w) / Math.sin(am - w), xb = worldOx + dy * Math.cos(am + w) / Math.sin(am + w);
      return a.x >= Math.min(xa, xb) - 3 && a.x <= Math.max(xa, xb) + 3;
    });
  }
  async function sunBoss(S) {
    const g = S.setPlayer('gintoki', { x: BOSS_CAM + 96, y: 172, facing: 1, name: '银时', hp: 100 });
    gear(g);
    await S.setStage('yoshi_sun_ch9', { x: BOSS_CAM + 96, y: 172, facing: 1, fade: false });
    S.insert(null);
    const st = G.world.stage, ox = 90 + BOSS_CAM;
    shaftsProp(S, 'S9', ox);
    const hs = gear(S.spawn('housen', BOSS_CAM + 240, 172, { id: 'housen', name: '凤仙', facing: -1 }));
    hs.scale = 1.3;
    S.pose(hs, 'shock_hurt');
    S.flash(0.3, 1, '#ffffff');
    S.letterbox(true);
    await S.fadeIn(0.2);
    await S.say('housen', '……光？……这是……太阳……', { actor: hs, expr: 'hurt' });
    await S.say('gintoki', '吉原的太阳，现在属于所有人了。');
    S.unpose(hs);
    S.letterbox(false);
    S.hint('夜兔怕阳光！把凤仙引进光柱里，他就会变弱——在光里打他', 7);
    const steam = (dt) => {
      if (G.world.stage !== st) return true;
      const lit = inShaft(hs, 'S9', ox) && hs.team === 'enemy';
      hs.tint = lit ? { color: 'rgb(255,240,210)', k: 0.3 + 0.1 * Math.sin(st.t * 12) } : null;
      hs.speed = lit ? 30 : 58;
      if (lit && Math.random() < dt * 8) G.fx.add({ kind: 'puff', x: hs.x + G.rand(-8, 8), y: hs.y - 30 * hs.scale, vx: 0, vy: -18, r: 2, life: 0.6, color: '236,232,226' });
      return false;
    };
    G.world.ticks.push(steam);
    await S.fight({
      arena: [BOSS_CAM + 8, BOSS_CAM + 376],
      music: 'epic',
      waves: [[{ actor: 'housen', cid: 'housen', name: '夜王 凤仙', hp: 200, boss: true, scale: 1.3, speed: 58, range: 32, minHp: 1,
        moves: ['E_PUNCH', 'E_HEAVY', 'E_PUNCH'], dmgMul: () => (inShaft(S.actor('housen'), 'S9', ox) ? 1.8 : 0.22) }]],
      endWhen: () => { const b = S.actor('housen'); return !!(b && b.team === 'enemy' && b.hp <= 16); },
      after: null,
    });
    hs.team = 'npc'; G.ui.boss = null; hs.tint = null;
    // 最后一击：跃起，背着太阳斩下
    S.letterbox(true);
    S.pose(g, 'crouch');
    S.sfx('charge', 0.6);
    await S.wait(0.3);
    S.sfx('jump', 0.8);
    let t0 = null;
    S.insert((gg, t) => {
      if (t0 == null) t0 = t;
      const u = (t - t0) / 0.43;
      gg.fillStyle = 'rgb(255,236,190)'; gg.fillRect(0, 0, G.W, G.H);
      gg.fillStyle = 'rgb(255,250,230)'; gg.beginPath(); gg.arc(192, 150, 46, 0, Math.PI * 2); gg.fill();
      gg.save(); gg.globalCompositeOperation = 'lighter';
      for (let i = 0; i < 16; i++) {
        const a = (2 * Math.PI * i) / 16 + t * 2.5;
        gg.fillStyle = 'rgba(255,220,150,0.25)'; gg.beginPath(); gg.moveTo(192, 150);
        gg.lineTo(192 + Math.cos(a - 0.05) * 400, 150 + Math.sin(a - 0.05) * 400); gg.lineTo(192 + Math.cos(a + 0.05) * 400, 150 + Math.sin(a + 0.05) * 400); gg.closePath(); gg.fill();
      }
      gg.restore();
      const at = G.atlas('gintoki'), x = G.lerp(150, 226, Math.min(1, u)), y = G.lerp(236, 122, Math.min(1, u));
      gg.save(); gg.translate(x, y); gg.rotate(G.lerp(-16, 10, Math.min(1, u)) * Math.PI / 180);
      at.draw(gg, 'slash_up', 4, 0, 0, { scale: 2, tint: { color: 'rgb(24,14,22)', k: 1 } });
      gg.restore();
    });
    await S.wait(0.45);
    S.insert(null);
    g.x = hs.x - 20; g.z = 60;
    await S.arc(g, hs.x + 60, hs.y, 4, 0.1, { anim: 'attack', z1: 0 });
    S.impact(3);
    S.sfx('slash_big', 1.0); S.sfx('impact', 1.0);
    G.fx.word('斩!!', st.camX + 150, 58, 0.6);
    G.fx.speedLines(192, 108, { count: 40, inner: 40, life: 0.4, color: '#ffffff' });
    S.shake(5, 0.4);
    S.pose(g, 'attack', { restart: true });
    S.pose(hs, 'hit', { restart: true });
    await S.wait(0.6);
    S.pose(hs, 'kneel'); S.sfx('thud', 0.8);
    await S.wait(0.8);
    await crumble(S, hs);
  }
  async function crumble(S, hs) {
    const p = S.player, st = G.world.stage;
    S.music('sad', 0.5);
    hs.scale = 2; hs.x = st.camX + 214; hs.y = 176;
    S.pose(hs, 'crumble', { restart: true, speed: 0.12 });
    p.x = st.camX + 70; S.pose(p, 'shoulder');
    S.zoom(1.85, hs, -50, 0.6);
    for (let i = 0; i < 20; i++) G.fx.add({ kind: 'puff', x: hs.x + G.rand(-16, 16), y: hs.y - G.rand(10, 70), vx: G.rand(-4, 4), vy: -G.rand(8, 20), r: 1.5, life: 2.0, color: '220,200,170' });
    await S.say('housen', '太阳……原来是这么温暖的东西。', { actor: hs, expr: 'normal' });
    S.sfx('sparkle', 0.5);
    S.zoom(1.1, null, null, 0.8);
    await S.animate(1.2, (u) => { hs.alpha = 1 - u; });
    S.remove(hs);
    S.sfx('twinkle', 0.5);
    await S.fadeOut(1.0);
    S.letterbox(false);
    await reunion(S);
  }

  // ================================================================ 重逢
  async function reunion(S) {
    const p = S.player;
    await S.setStage('yoshi_sun_ch9', { x: 120 + GX + 308, y: 176, facing: 1, fade: false });
    const st = G.world.stage;
    S.camera(120 + GX);
    const cx = 120 + GX;
    const hw = S.spawn('hinowa', cx + 196, 174, { id: 'hinowa', name: '日轮', facing: -1 });
    S.pose(hw, 'smile');
    const s = gear(S.spawn('seita', cx + 120, 176, { id: 'seita', name: '晴太', facing: 1 }));
    const tk = gear(S.spawn('tsukuyo', cx + 334, 176, { id: 'tsukuyo', name: '月咏', facing: -1 }));
    S.pose(tk, 'smoke');
    p.x = cx + 308; p.y = 177; S.pose(p, 'lie');
    S.letterbox(true);
    S.music('sad', 0.5);
    await S.fadeIn(0.8);
    S.sfx('run', 0.45);
    await S.walk(s, cx + 184, 176, { speed: 130, anim: 'run' });
    S.pose(s, 'cry');
    await S.say('seita', '娘——！', { actor: s, expr: 'cry' });
    await S.say('hinowa', '……晴太。你长这么大了。', { actor: hw, expr: 'smile' });
    for (let i = 0; i < 3; i++) G.fx.text('♥', s.x + 6 + i * 4, s.y - 40, { vy: -14, life: 1.4, color: '#ff6e8c' });
    S.sfx('sparkle', 0.5);
    await S.wait(0.8);
    await S.say(null, '吉原，终于迎来了太阳。');
    S.zoom(1.85, p, -10, 0.4);
    await S.wait(0.4);
    S.sfx('pop', 0.6);
    await S.say('gintoki', '……糖分……', { expr: 'hurt' });
    await S.say('tsukuyo', '……这家伙，真的是来救吉原的吗。', { actor: tk });
    S.sfx('crow', 0.5);
    await S.wait(0.6);
    S.zoom(1, null, null, 0.4);
    await S.fadeOut(1.2);
    S.letterbox(false);
    S.camera(null);
    F().ch9Done = true;
  }

  // ================================================================ 地图（第九章版）
  function defineStages() {
    const ember = (nm, area, rise, cols) => ({ type: 'embers', items: SP().embers[nm], area, rise, colors: cols });
    const warm = [[255, 190, 110], [255, 140, 90], [255, 230, 170]];
    G.STAGES.yoshi_night_ch9 = { id: 'yoshi_night_ch9', bg: 'yoshi_night', x0: 0, x1: 1096, yMin: 162, yMax: 204, music: 'yoshiwara', props: [],
      npcs: [
        { cid: 'townswoman', id: 'w1', x: 360, y: 184, facing: 1, label: '路过的姑娘',
          talk: async (S) => { await S.say('townswoman', '月咏大人是百华的首领。……她脸上的伤，是为了保护我们留下的。', { name: '路过的姑娘' }); } },
        { cid: 'townsman__v2', id: 'w2', x: 620, y: 180, facing: -1, label: '卖团子的老爷子',
          talk: async (S) => { await S.say('townsman', '太阳？……我在吉原活了五十年，一次都没见过。', { name: '卖团子的老爷子' }); } },
      ],
      hotspots: STREET_HOT,
      triggers: [{ id: 'go', x0: 0, x1: 5000, cond: () => F().seita && F().tsukuyo && !F().went,
        run: async (S) => { F().went = true; await cutsTowerRoofThrone(S); await corridor(S); await control(S); } }] };
    G.STAGES.tower_ch9 = { id: 'tower_ch9', bg: 'tower_night', x0: 0, x1: 384, yMin: 190, yMax: 210, props: [] };
    G.STAGES.yoshi_roof_ch9 = { id: 'yoshi_roof_ch9', bg: 'yoshi_roof', x0: 0, x1: 384, yMin: 190, yMax: 210, props: [] };
    G.STAGES.throne_ch9 = { id: 'throne_ch9', bg: 'throne', x0: 0, x1: 384, yMin: 190, yMax: 210,
      props: [{ type: 'custom', x: 0, y: 0, depth: 9998, draw: (g) => { const a = G.world.stage.state.dark || 0; if (a > 0) { g.fillStyle = `rgba(6,4,10,${a})`; g.fillRect(0, 0, G.W, G.H); } } }] };
    G.STAGES.corridor_ch9 = { id: 'corridor_ch9', bg: 'corridor', x0: 0, x1: 1400, yMin: 160, yMax: 200, props: [] };
    G.STAGES.control_ch9 = { id: 'control_ch9', bg: 'control', x0: 0, x1: 384, yMin: 164, yMax: 200, props: [],
      npcs: [{ cid: 'seita', id: 'seita', alt: ['seita__s09'], x: 240, y: 172, facing: -1, label: '晴太',
        talk: async (S, a) => { await S.say('seita', '铭牌上写着开天顶的顺序！月咏姐，快看看！', { actor: a, expr: 'determined' }); } }],
      hotspots: CTRL_HOT };
    G.STAGES.yoshi_sun_ch9 = { id: 'yoshi_sun_ch9', bg: 'yoshi_sun', x0: BOSS_CAM, x1: BOSS_CAM + 384, yMin: 162, yMax: 204, props: [] };
    // 夜里的大街：飘着火星（加在背景的前景层里）
    G.D.bg.yoshi_night.fg = [Object.assign(ember('S1', [0, 20, 384, 170], 10, warm), { alpha: 1 })];
  }

  async function control(S) {
    const t = S.setPlayer('tsukuyo', { x: 120, y: 176, facing: 1, name: '月咏', hp: 100 });
    gear(t);
    await S.setStage('control_ch9', { x: 120, y: 176, facing: 1, fade: false });
    controlProp(S);
    CTRL.step = 0;
    await S.fadeIn(0.5);
    await S.say('tsukuyo', '……这就是控制天顶的机关室。', { expr: 'determined' });
    S.hint('现在操控月咏：看铭牌，照顺序操作齿轮和拉杆', 6);
  }

  // ================================================================ 第九章主流程
  G.STORY.chapter9 = async function (S) {
    defineStages();
    G.fadeAlpha = 0;
    G.world.stage = null;
    await S.chapterCard('ch9');
    const p = gear(new G.Actor('gintoki', 300, 186, { id: 'player', team: 'player', hp: 100, speed: 72, name: '银时' }));
    G.world.player = p;
    G.fadeAlpha = 1;
    await S.setStage('yoshi_night_ch9', { x: 300, y: 186, facing: 1, fade: false });
    await S.run(async (S) => { await intro(S); });
    await S.until(() => G.flags.opened);
    await S.run(async (S) => { await sunBoss(S); });
    await S.until(() => G.flags.ch9Done);
  };
})();
