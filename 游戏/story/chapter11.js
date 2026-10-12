// 第十一章：松阳老师（原片 s11，泛黄的回忆）
//   战场的尸山上啃饭团的小鬼 → 吉田松阳（名牌）把自己的剑递给他：「这把剑……」
//   → 松下私塾的院子（操控小银时自由走动，和小桂、小高杉、老师说话）→ 和小高杉木刀比试（练习战）→ 啪！
//   → 教室：上课打瞌睡（看准时机保持清醒……没用）→ 老师的头槌
//   → 私塾起火，奈落带走松阳：「银时，大家就拜托你了。」
//   → 攘夷战争：操控白夜叉（名牌）横扫天人 → 山脊上的四个人（坂本辰马，名牌）
//   → 悬崖：跪着的松阳回过头微笑「谢谢你。」→ 那一刀不交给玩家，自动切白屏；「住手——！！」→ 一滴泪
//   → 回到现在：和胧刀锋相抵
'use strict';
(function () {
  const G = window.G;
  const F = () => G.flags;
  const count = (key) => (G.flags[key] = (G.flags[key] || 0) + 1);
  const PR = () => G.D.bg.ch11.props;
  const px = (g, x, y, c, w = 1, h = 1) => { g.fillStyle = c; g.fillRect(Math.round(x), Math.round(y), w, h); };
  const ALT = { gintoki_kid: 'gintoki_kid__s11', takasugi_kid: 'takasugi_kid__s11', katsura_kid: 'katsura_kid__s11', shouyou: 'shouyou__s11',
    shiroyasha: 'shiroyasha__s11', katsura: 'katsura__s11', sakamoto: 'sakamoto__s11', oboro: 'oboro__s11', gintoki: 'gintoki__s11' };
  function gear(a) { const id = a && ALT[a.cid]; if (id && G.D.chars[id]) a.alt = [G.atlas(id)].concat(a.cid === 'shiroyasha' ? [G.atlas('shiroyasha__s11_sword')] : []); return a; }
  const ease = (u) => 1 - Math.pow(1 - G.clamp(u, 0, 1), 3);
  function propImg(d, x, y, depth, o = {}) { return Object.assign({ type: 'image', image: d.image, x, y, ax: d.ax || 0, ay: d.ay || 0, depth }, o); }

  // 泛黄的回忆：整屏滤镜 + 暗角 + 胶片的颗粒和划痕
  function memoryLook(S, amount = 0.62) {
    S.filter(`sepia(${amount}) saturate(${(1 - amount * 0.25).toFixed(2)}) contrast(1.06)`);
    const vig = G.D.bg.ch11.vignette;
    return S.prop({ type: 'custom', x: 0, y: 0, depth: 99990, draw: (g, x, y, t) => {
      g.globalAlpha = 0.85; g.drawImage(G.image(vig), 0, 0); g.globalAlpha = 1;
      const f = Math.floor(t * 12), rnd = G.prng(f * 7 + 3);
      for (let i = 0; i < 60; i++) px(g, rnd() * G.W, rnd() * G.H, i % 2 ? 'rgb(226,208,178)' : 'rgb(60,46,38)');
      if (rnd() < 0.18) { const sx = 30 + rnd() * 324, y0 = rnd() * 108, len = 30 + rnd() * 90; px(g, sx, y0, 'rgba(208,190,160,0.8)', 1, len); }
      if (rnd() < 0.12) px(g, rnd() * G.W, rnd() * G.H, 'rgb(40,30,26)', 3, 2);
    } });
  }
  function memoryCut(S) { S.flash(0.2, 0.85, '#ffffff'); }

  // ================================================================ A 战场：吃饭团的小鬼，老师递过来的剑
  async function battlefield(S) {
    const p = S.player, st = G.world.stage;
    p.visible = false;
    memoryLook(S, 0.74);
    S.letterbox(true);
    S.music('flashback', 0.6);
    const mx = G.D.bg.s11_battlefield.kid_seat || [280, 143];
    const kid = gear(S.spawn('gintoki_kid', mx[0], mx[1], { id: 'kid', name: '小鬼', facing: -1 }));
    kid.shadow = false;
    S.pose(kid, 'eat');
    const sy = gear(S.spawn('shouyou', 38, 160, { id: 'shouyou', name: '松阳', facing: 1 }));
    S.flash(0.9, 1, '#ffffff');
    await S.wait(0.4);
    await S.walk(sy, 198, 160, { speed: 60 });
    S.pose(sy, 'smile');
    S.nameCard('shouyou');
    S.pose(kid, 'eat_shock');
    G.fx.text('!', kid.x, kid.y - 34, { life: 0.8, color: '#ffe678' });
    S.sfx('shock', 0.6);
    await S.wait(0.4);
    S.sfx('jump', 0.6);
    await S.arc(kid, 250, 160, 16, 0.27, { anim: 'jump_sword' });
    S.pose(kid, 'ready_angry');
    G.fx.dust(kid.x, kid.y, 6);
    await S.say('shouyou', '……你就是传说中，在战场上吃死人饭团的鬼吗。', { actor: sy, expr: 'smile' });
    await S.say('shouyou', '真是个可怜的小鬼。……把剑放下吧。那种剑，只会让你越来越孤单。', { actor: sy, expr: 'smile' });
    S.zoom(2.7, 200, 139, 0.6);
    S.pose(sy, 'offer');
    const sword = S.prop(propImg(PR().sheathed_sword_0, 186, 150, 170));
    S.sfx('sparkle', 0.5);
    await S.say('shouyou', '这把剑，送给你。', { actor: sy, expr: 'smile' });
    S.pose(kid, 'lower_blade');
    await S.wait(0.4);
    S.sfx('clang', 0.6);
    const blade = S.prop(propImg(PR()['blade_ground_8'], 221, 161, 162));
    S.pose(kid, 'walk_sad');
    await S.walk(kid, 238, 160, { speed: 40, anim: 'walk_sad' });
    S.pose(kid, 'reach');
    await S.wait(0.3);
    sword.image = PR().sheathed_sword_90.image; sword.ax = PR().sheathed_sword_90.ax; sword.ay = PR().sheathed_sword_90.ay;
    sword.x = 199; sword.y = 152;
    await S.wait(0.2);
    S.unprop(sword);
    S.pose(kid, 'idle');
    S.pose(sy, 'smile_nosword');
    S.sfx('sparkle', 0.5);
    await S.say('shouyou', '这把剑，是用来斩断你心中的弱小，守护你自己的灵魂的。', { actor: sy, expr: 'smile' });
    await S.say('shouyou', '跟我来吧。……我那里，有很多和你一样的孩子。', { actor: sy, expr: 'smile' });
    S.unprop(blade);
    S.zoom(1, null, null, 0);
    await S.fadeOut(0.6);
    S.letterbox(false);
  }

  // ================================================================ B1 私塾的院子（操控小银时）
  async function yard(S) {
    const kid = S.setPlayer('gintoki_kid', { x: 290, y: 176, facing: -1, name: '小银时', hp: 100, speed: 66 });
    gear(kid);
    await S.setStage('yard_ch11', { x: 290, y: 176, facing: -1, fade: false });
    memoryLook(S, 0.62);
    memoryCut(S);
    await S.fadeIn(0.4);
    S.hint('松下私塾。（操控小银时）在院子里走走，和大家说说话', 6);
  }
  async function talkShouyou(S, a) {
    const n = count('sy');
    if (n === 1) {
      await S.say('shouyou', '银时，今天的功课做完了吗？', { actor: a, expr: 'smile' });
      await S.say('gintoki_kid', '……睡完了。', { name: '小银时' });
      await S.say('shouyou', '那就是还没做完呢。', { actor: a, expr: 'smile' });
    } else await S.say('shouyou', '晋助在等你哦。他说今天一定要赢你。', { actor: a, expr: 'smile' });
    F().sy = true;
  }
  async function talkKatsuraKid(S, a) {
    await S.say('katsura_kid', '银时，又逃课了吧。……老师会生气的。', { actor: a, name: '小桂' });
    await S.say('gintoki_kid', '假发才会生气。', { name: '小银时' });
    await S.say('katsura_kid', '不是假发，是桂！……从小就这么叫，以后也要这么叫吗！', { actor: a, name: '小桂', expr: 'shock' });
    F().zura = true;
  }
  async function talkTakasugiKid(S, a) {
    await S.say('takasugi_kid', '银时！今天一定要赢你！', { actor: a, name: '小高杉', expr: 'shout' });
    await S.say('gintoki_kid', '……又来。', { name: '小银时' });
    await spar(S, a);
  }
  async function spar(S, tk) {
    const p = S.player, st = G.world.stage;
    S.hint('木刀比试（练习战，输了也没关系）', 4);
    await S.fight({
      arena: [8, 376],
      music: null,
      waves: [[{ actor: tk.id, cid: 'takasugi_kid', name: '小高杉', hp: 40, boss: true, speed: 62, range: 24, minHp: 1, moves: ['E_SLASH'] }]],
      endWhen: () => { const b = S.actor(tk.id); return !!(b && b.team === 'enemy' && (b.hp <= 14 || G.world.fightT > 25)); },
      after: null,
    });
    tk.team = 'npc'; G.ui.boss = null; tk.name = '小高杉';
    // 最后一下：冲过来 → 跳起 → 啪！
    S.letterbox(true);
    S.face(p, tk);
    tk.x = G.clamp(tk.x, p.x - 120, p.x - 60); tk.y = p.y;
    S.pose(tk, 'run_bokuto_up');
    S.sfx('run', 0.4);
    await S.walk(tk, p.x - 22, p.y, { speed: 160, anim: 'run_bokuto_up' });
    await S.arc(tk, p.x - 2, p.y - 10, 12, 0.15, { anim: 'jump_bokuto_up' });
    S.pose(p, 'attack_bokuto', { restart: true });
    S.pose(tk, 'hit_frozen');
    S.sfx('slap', 0.9); S.sfx('punch_big', 0.6);
    G.fx.word('啪!!', p.x - 10, p.y - 50, 0.8);
    S.flash(0.06, 0.55);
    S.shake(4, 0.3);
    await S.wait(0.1);
    await S.arc(tk, p.x - 100, p.y + 2, 30, 0.5, { anim: 'fly' });
    S.pose(tk, 'lie');
    S.pose(p, 'shoulder_bokuto');
    await S.say('takasugi_kid', '……可恶……明天……明天一定……', { actor: tk, name: '小高杉', expr: 'hurt' });
    await S.say('gintoki_kid', '明天我要睡午觉。', { name: '小银时' });
    S.unpose(tk); S.unpose(p);
    S.letterbox(false);
    F().spar = true;
    await classroom(S);
  }

  // ================================================================ B2 教室：上课打瞌睡 → 头槌
  async function classroom(S) {
    const p = S.player;
    await S.fadeOut(0.5);
    await S.setStage('classroom_ch11', { x: 266, y: 158, facing: -1, fade: false });
    memoryLook(S, 0.6);
    const st = G.world.stage;
    p.visible = false;
    const desks = [['desk_books', 85], ['desk_paper', 153], ['desk', 253]].map(([k, x]) => S.prop(propImg(PR()[k], x, 157, 162)));
    const kz = gear(S.spawn('katsura_kid', 98, 158, { id: 'kz', name: '小桂', facing: -1 }));
    const tk = gear(S.spawn('takasugi_kid', 166, 158, { id: 'tk', name: '小高杉', facing: -1 }));
    const gk = gear(S.spawn('gintoki_kid', 266, 158, { id: 'gk', name: '小银时', facing: -1 }));
    const sy = gear(S.spawn('shouyou', 205, 160, { id: 'sy', name: '松阳', facing: -1 }));
    S.pose(kz, 'sit_read'); S.pose(tk, 'sit_angry'); S.pose(gk, 'sit'); S.pose(sy, 'smile_nosword');
    memoryCut(S);
    await S.fadeIn(0.4);
    await S.say('shouyou', '那么，今天我们来读《论语》。……「学而时习之」——', { actor: sy, expr: 'smile' });
    await S.say(null, '老师的声音，像午后的阳光一样暖洋洋的。……眼皮越来越重。');
    let awake = 0;
    for (let i = 0; i < 2; i++) {
      const ok = await S.timing({ label: `别睡着！看准时机按 J 保持清醒（${i + 1}/2）`, speed: 1.4 + i * 0.6, zone: [0.46, 0.54] });
      if (ok) awake++;
    }
    S.pose(gk, 'sit_sleep');
    const zzz = S.prop({ type: 'custom', x: 0, y: 0, depth: 300, draw: (g, x, y, t) => {
      for (let i = 0; i < 3; i++) { const k = G.mod(t * 0.9 + i / 3, 1); g.globalAlpha = 1 - k; G.f12.draw(g, 'Z', 268 + i * 4, Math.round(132 - k * 12), '#ffffff', { outline: '#2a2030' }); g.globalAlpha = 1; }
    } });
    await S.say(null, awake === 2 ? '……撑了两下。第三下，还是睡着了。' : '……三秒钟就睡着了。');
    // 老师走过来，笑着
    await S.walk(sy, 238, 160, { speed: 40, anim: 'walk_smile_nosword' });
    S.sfx('aura', 0.6);
    S.zoom(2.25, 250, 132, 0.35);
    await S.wait(0.3);
    S.unprop(zzz);
    S.pose(sy, 'headbutt_seq', { restart: true });
    S.sfx('whoosh', 0.6);
    await S.wait(0.3);
    S.impact(2);
    S.sfx('punch_big', 1.0); S.sfx('impact', 0.8);
    G.fx.word('咚!!', 250, 110, 0.8);
    S.shake(6, 0.4);
    S.pose(gk, 'sit_crushed');
    await S.wait(0.2);
    S.pose(gk, 'lie_ko');
    G.fx.debris(253, 150, ['#a07850', '#6a4a30'], 18, [40, 140], 260, 0.8);
    S.zoom(1.62, 188, 129, 0.4);
    S.pose(kz, 'sit_laugh'); S.pose(tk, 'sit_laugh');
    G.fx.text('哈哈哈', 120, 120, { vy: -8, life: 1.4 });
    await S.say('shouyou', '上课睡觉可不行哦～', { actor: sy, expr: 'smile' });
    await S.wait(0.5);
    desks.forEach((d) => S.unprop(d));
    S.zoom(1, null, null, 0);
    await S.fadeOut(0.6);
    await fire(S);
  }

  // ================================================================ C 私塾起火
  async function fire(S) {
    const p = S.player;
    await S.setStage('fire_ch11', { x: 30, y: 200, fade: false });
    memoryLook(S, 0.45);
    p.visible = false;
    S.music('sad', 0.6);
    const n1 = S.spawn('naraku', 186, 160, { id: 'n1', facing: 1 }), n2 = S.spawn('naraku', 238, 160, { id: 'n2', facing: 1 });
    const g3 = S.spawn('naraku', 128, 160, { id: 'n3', facing: -1 });
    S.pose(g3, 'ready');
    const sy = gear(S.spawn('shouyou', 212, 160, { id: 'sy', name: '松阳', facing: 1 }));
    S.pose(sy, 'walk_bound');
    const kids = [['takasugi_kid', 40, 'kneel_angry'], ['katsura_kid', 62, 'kneel_cry'], ['gintoki_kid', 86, 'kneel_reach']]
      .map(([cid, x, an]) => { const a = gear(S.spawn(cid, x, 160, { id: cid, facing: 1 })); S.pose(a, an); return a; });
    S.letterbox(true);
    memoryCut(S);
    S.sfx('fire', 0.5);
    await S.fadeIn(0.4);
    await Promise.all([S.animate(1.0, (u) => { n1.x = 186 + 16 * u; sy.x = 212 + 16 * u; n2.x = 238 + 16 * u; })]);
    S.pose(sy, 'idle_bound');
    S.zoom(2.6, 226, 134, 0.4);
    await S.wait(0.3);
    sy.facing = -1;
    S.pose(sy, 'idle_bound_smile');
    S.sfx('sparkle', 0.4);
    await S.say('shouyou', '银时，大家就拜托你了。', { actor: sy, expr: 'smile' });
    S.zoom(2.8, 84, 140, 0.3);
    await S.say('gintoki_kid', '……老师……！', { name: '小银时', expr: 'cry' });
    S.zoom(1, null, null, 0);
    await S.fadeOut(0.6);
    kids.forEach((a) => S.remove(a));
    await joui(S);
  }

  // ================================================================ D 攘夷战争：白夜叉
  async function joui(S) {
    const sh = S.setPlayer('shiroyasha', { x: 60, y: 176, facing: 1, name: '白夜叉', hp: 100, speed: 76 });
    gear(sh);
    await S.setStage('joui_ch11', { x: 60, y: 176, facing: 1, fade: false });
    memoryLook(S, 0.5);
    G.D.bg.s11_joui.fg = [{ type: 'rain', n: 70, slant: 0.2, len: 7, speed: 420, alpha: 0.8 }];
    memoryCut(S);
    S.music('battle', 0.5);
    await S.fadeIn(0.3);
    S.nameCard('shiroyasha');
    await S.say(null, '——几年后。攘夷战争。战场上的人们，叫他「白夜叉」。');
    S.hint('现在操控白夜叉', 4);
    const kinds = ['harusame', 'amanto_pig', 'harusame', 'amanto_cat'];
    await S.fight({
      arena: [8, 376],
      music: 'battle',
      waves: [
        kinds.map((cid, i) => ({ cid, id: `j${i}`, name: '天人', hp: 26, side: i % 2 ? 'left' : 'right' })),
        kinds.concat(['amanto_pig']).map((cid, i) => ({ cid, id: `j2_${i}`, name: '天人', hp: 28, side: i % 2 ? 'left' : 'right' })),
      ],
      after: null,
    });
    await S.fadeOut(0.5);
    await ridge(S);
  }
  async function ridge(S) {
    const p = S.player;
    await S.setStage('ridge_ch11', { x: 186, y: 150, facing: 1, fade: false });
    memoryLook(S, 0.55);
    p.visible = false;
    const four = [['katsura', 152, 'arms_crossed'], ['shiroyasha', 186, 'shoulder'], ['takasugi', 220, 'idle'], ['sakamoto', 255, 'laugh_noha']]
      .map(([cid, x, an]) => { const a = cid === 'takasugi' ? S.spawn('takasugi__young', x, 150, { id: cid, facing: 1 }) : gear(S.spawn(cid, x, 150, { id: cid, facing: 1 })); S.pose(a, an); a.tint = { color: 'rgb(38,22,34)', k: 0.9 }; return a; });
    S.letterbox(true);
    memoryCut(S);
    await S.fadeIn(0.3);
    S.zoom(1.5, 204, 125, 1.6);
    await S.animate(0.6, (u) => four.forEach((a) => { a.tint.k = G.lerp(0.9, 0.18, u); }));
    S.nameCard('sakamoto');
    S.pose(four[3], 'laugh');
    S.sfx('cheer', 0.4);
    await S.say('sakamoto', '啊哈哈哈！金时，今天也是好天气啊！', { actor: four[3], expr: 'happy' });
    await S.say('shiroyasha', '……是银时。', { actor: four[1] });
    await S.say(null, '桂、高杉、坂本，还有银时。在同一片天空下战斗的四个人。');
    S.zoom(1, null, null, 0);
    await S.fadeOut(0.6);
    S.letterbox(false);
    await cliff(S);
  }

  // ================================================================ E 悬崖
  async function cliff(S) {
    const p = S.player;
    await S.setStage('cliff_ch11', { x: 114, y: 160, facing: -1, fade: false });
    memoryLook(S, 0.78);
    const st = G.world.stage;
    p.visible = false;
    S.music('sad', 0.6);
    const sy = gear(S.spawn('shouyou', 74, 160, { id: 'sy', name: '松阳', facing: -1 }));
    S.pose(sy, 'kneel_bound');
    const sh = gear(S.spawn('shiroyasha', 114, 160, { id: 'sh', name: '银时', facing: -1 }));
    S.pose(sh, 'battle_idle_sad');
    const kz = gear(S.spawn('katsura', 248, 160, { id: 'kz', name: '桂', facing: -1 }));
    S.pose(kz, 'kneel_bound_sad');
    const ty = S.spawn('takasugi__young', 276, 160, { id: 'ty', name: '高杉', facing: -1 });
    S.pose(ty, 'kneel_bound_angry');
    const ob = gear(S.spawn('oboro', 306, 160, { id: 'ob', name: '胧', facing: -1 }));
    S.pose(ob, 'ready_low');
    [328, 350, 372].forEach((x, i) => { const n = S.spawn('naraku', x, 150, { id: `cn${i}`, facing: -1 }); S.pose(n, 'stand_guard'); n.tint = { color: 'rgb(170,166,170)', k: 0.38 }; });
    S.letterbox(true);
    S.flash(0.35, 1, '#000000');
    await S.fadeIn(0.35);
    await S.say('oboro', '……选吧。老师的命，还是同伴的命。', { actor: ob, expr: 'normal' });
    S.zoom(3.05, 80, 141, 0.4);
    await S.wait(0.4);
    sy.facing = 1;
    S.pose(sy, 'kneel_bound_cry');
    S.sfx('sparkle', 0.4);
    await S.say('shouyou', '谢谢你。', { actor: sy, expr: 'cry' });
    // 那一刀：不交给玩家，自动切白屏
    S.zoom(2.9, 108, 126, 0.2);
    S.pose(sh, 'raise', { restart: true });
    await S.wait(0.4);
    S.pose(sh, 'glint', { restart: true });
    S.sfx('shine', 0.6);
    await S.wait(0.3);
    S.zoom(3.2, 272, 144, 0.12);
    S.pose(ty, 'kneel_bound_shout');
    S.shake(3, 0.4);
    await S.say('takasugi__young', '住手——！！', { actor: ty, name: '高杉', expr: 'shout' });
    S.zoom(3.0, 108, 126, 0.1);
    S.pose(sh, 'fall', { restart: true });
    await S.animate(0.35, (u) => { G.flashAlpha = Math.pow(u, 0.7) * 0.95; G.flashColor = '#ffffff'; });
    S.stopMusic(0.1);
    // 白：一滴泪落下
    let t0 = null;
    S.insert((g, t) => {
      if (t0 == null) t0 = t;
      const u = t - t0;
      const c = u < 0.7 ? 255 : Math.round(G.lerp(255, 244, Math.min(1, (u - 0.7) / 1.0)));
      g.fillStyle = `rgb(${c},${Math.round(G.lerp(255, 238, Math.min(1, Math.max(0, u - 0.7))))},${Math.round(G.lerp(255, 226, Math.min(1, Math.max(0, u - 0.7))))})`;
      g.fillRect(0, 0, G.W, G.H);
      if (u > 0.8 && u < 1.4) {
        const fall = Math.max(0, u - 1.0), y = 34 + 380 * fall * fall;
        const d = PR()[u < 1.0 ? 'big_tear2' : 'big_tear3'];
        if (y < 110) g.drawImage(G.image(d.image), 192 - d.ax, Math.round(y) - d.ay);
      }
      if (u > 1.4) for (let i = 0; i < 3; i++) { const r = (u - 1.4 - i * 0.15) * 50; if (r > 0) { g.strokeStyle = `rgba(150,140,130,${Math.max(0, 0.6 - r / 80).toFixed(2)})`; g.beginPath(); g.ellipse(192, 150, r, r * 0.25, 0, 0, Math.PI * 2); g.stroke(); } }
    });
    G.flashAlpha = 0;
    await S.wait(1.4);
    S.sfx('bell', 0.5);
    await S.wait(1.4);
    S.insert(null);
    S.filter(null);
    await present(S);
  }

  // ================================================================ F 回到现在：和胧刀锋相抵
  async function present(S) {
    const p = S.player;
    await S.setStage('present_ch11', { x: 196, y: 160, facing: 1, fade: false });
    p.visible = false;
    const g = gear(S.spawn('gintoki', 196, 160, { id: 'gnow', name: '银时', facing: 1 }));
    S.pose(g, 'lock_shadow');
    const ob = gear(S.spawn('oboro', 238, 160, { id: 'onow', name: '胧', facing: -1 }));
    S.pose(ob, 'lock');
    S.flash(0.3, 1, '#ffffff');
    S.zoom(2.75, 208, 137, 0);
    S.letterbox(true);
    S.music('tension', 0.5);
    const tick = (dt) => { if (G.world.stage.id !== 'present_ch11') return true; if (Math.random() < dt * 8) G.fx.spark(216, 143, '#ffe678', 3); return false; };
    G.world.ticks.push(tick);
    await S.wait(0.8);
    await S.say('gintoki', '……老师。', { expr: 'angry' });
    await S.wait(0.6);
    await S.fadeOut(0.8);
    S.zoom(1, null, null, 0);
    S.letterbox(false);
    F().ch11Done = true;
  }

  // ================================================================ 地图（第十一章版）
  function defineStages() {
    G.STAGES.battlefield_ch11 = { id: 'battlefield_ch11', bg: 's11_battlefield', x0: 0, x1: 414, yMin: 156, yMax: 200, props: [] };
    G.STAGES.yard_ch11 = { id: 'yard_ch11', bg: 's11_yard', x0: 0, x1: 384, yMin: 160, yMax: 200, music: 'flashback', props: [],
      npcs: [
        { cid: 'shouyou', id: 'shouyou', alt: ['shouyou__s11'], x: 152, y: 138, facing: 1, anim: 'sit', label: '老师', talk: talkShouyou, talkRy: 30 },
        { cid: 'katsura_kid', id: 'katsura_kid', alt: ['katsura_kid__s11'], x: 206, y: 138, facing: -1, anim: 'sit', label: '小桂', talk: talkKatsuraKid, talkRy: 30 },
        { cid: 'takasugi_kid', id: 'takasugi_kid', alt: ['takasugi_kid__s11'], x: 128, y: 172, facing: 1, anim: 'ready_shout', label: '小高杉', talk: talkTakasugiKid },
      ],
      hotspots: [{ id: 'sign', x: 202, y: 162, r: 10, ry: 6, label: '门牌', ly: 76, use: async (S) => { await S.say(null, '门上挂着「松下私塾」的牌子。'); } }] };
    G.STAGES.classroom_ch11 = { id: 'classroom_ch11', bg: 's11_classroom', x0: 0, x1: 384, yMin: 156, yMax: 200, props: [] };
    G.STAGES.fire_ch11 = { id: 'fire_ch11', bg: 's11_fire', x0: 0, x1: 384, yMin: 190, yMax: 210, props: [] };
    G.STAGES.joui_ch11 = { id: 'joui_ch11', bg: 's11_joui', x0: 0, x1: 384, yMin: 156, yMax: 200, props: [] };
    G.STAGES.ridge_ch11 = { id: 'ridge_ch11', bg: 's11_ridge', x0: 0, x1: 384, yMin: 190, yMax: 210, props: [] };
    G.STAGES.cliff_ch11 = { id: 'cliff_ch11', bg: 's11_cliff', x0: 0, x1: 384, yMin: 190, yMax: 210, props: [] };
    G.STAGES.present_ch11 = { id: 'present_ch11', bg: 's11_present', x0: 0, x1: 384, yMin: 190, yMax: 210, props: [] };
  }

  // ================================================================ 第十一章主流程
  G.STORY.chapter11 = async function (S) {
    defineStages();
    G.fadeAlpha = 0;
    G.world.stage = null;
    await S.chapterCard('ch11');
    S.insert(null);      // 从第十章接着玩时，第十章结尾的白屏还盖着
    const p = new G.Actor('gintoki_kid', 200, 190, { id: 'player', team: 'player', hp: 100, speed: 66, name: '小银时' });
    G.world.player = p;
    G.fadeAlpha = 1;
    await S.setStage('battlefield_ch11', { x: 200, y: 190, facing: 1, fade: false });
    await S.run(async (S) => { await battlefield(S); await yard(S); });
    await S.until(() => G.flags.ch11Done);
    S.filter(null);
  };
})();
