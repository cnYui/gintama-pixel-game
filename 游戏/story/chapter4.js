// 第四章：真选组（原片 s04）
//   开场：屯所门口的「诚」字旗，偷偷打羽毛球的山崎 → 阿妙托万事屋抓跟踪狂：大街上三个草丛，哪个长了张脸？
//   → 近藤现身（名牌）→ 阿妙的杀气、超级拳，近藤变成天边的星星 → 掉回来要求决斗（Boss 战）
//   → 土方、冲田来领人，近藤硬拉银时去屯所吃饭 → 食堂：「土方特制盖饭」（蛋黄酱特写 + 名牌）
//   → 午睡的冲田醒来：「土方先生，去死吧。」火箭筒 → 土方爆炸头、跳上桌子「总悟你这混蛋！！」
//   → 冲田的火箭筒连发（撑过去）→ 中庭的「诚」字旗前亮相，冲田的激光瞄准点又爬上了土方的爆炸头
'use strict';
(function () {
  const G = window.G;
  const F = () => G.flags;
  const count = (key) => (G.flags[key] = (G.flags[key] || 0) + 1);
  const SP = () => G.D.bg.ch4;           // 第四章的小道具（tools/bg_chapters.py 的 ch4 导出）
  const sweat = (a, dx = 7) => G.fx.img(G.D.bg.ch2.sweat.image, a.x + dx, a.headY() + 4, { vy: 7, life: 0.9, fade: true });
  const vein = (a, dx = -5) => G.fx.img(G.D.bg.ch2.vein.image, a.x + dx, a.headY() + 3, { life: 1.3, pulse: true });
  const frame = (fr, fps, t) => fr[G.mod(Math.floor(t * fps + 1e-6), fr.length)];
  const px = (g, x, y, c, w = 1, h = 1) => { g.fillStyle = c; g.fillRect(Math.round(x), Math.round(y), w, h); };
  const ALT = { kondo: 'kondo__s04', otae: 'otae__s04', hijikata: 'hijikata__s04', okita: 'okita__s04' };
  function gear(a) { const id = a && ALT[a.cid]; if (id && G.D.chars[id]) a.alt = [G.atlas(id)]; return a; }
  // 画一个 grab 导出的小道具（锚点 + 偏移）
  const grabProp = (d, x, y, depth, o = {}) => Object.assign({ type: 'image', image: d.image, x, y, ax: -d.ox, ay: -d.oy, depth }, o);

  function boom(S, x, y, size = 22, word = '轰!!') {
    S.sfx(size > 26 ? 'explosion' : 'explosion_small', 0.9);
    S.shake(size > 26 ? 6 : 4, size > 26 ? 0.6 : 0.35);
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
      g.fillStyle = `rgba(${cols[Math.min(4, Math.floor(k * 5))]},${1 - k * 0.8})`;
      for (const b of balls) {
        g.beginPath();
        g.arc(sx + Math.cos(b.a) * b.d * (0.5 + k), sy - size * 0.4 + Math.sin(b.a) * b.d * 0.6 * (0.5 + k) - k * size * 0.4, Math.max(0.5, b.r * (1 - k * 0.6)), 0, Math.PI * 2);
        g.fill();
      }
    } });
    G.world.ticks.push(() => { if (st.t - t0 > 0.75) { S.unprop(pr); return true; } return false; });
  }

  // ================================================================ 开场：屯所门口
  async function opening(S) {
    const st = G.world.stage, p = S.player;
    p.visible = false;
    S.letterbox(true);
    S.zoom(2.5, 343, 64, 0);
    await S.fadeIn(0.6);
    await S.wait(0.5);
    await S.zoom(1, 192, 116, 1.5);
    await S.say(null, '江户的武装警察「真选组」。');
    const y = S.actor('yamazaki');
    S.face(y, 1);
    await S.say('yamazaki', '……趁副长不在，再练一会儿羽毛球。', { actor: y, expr: 'focus' });
    S.sfx('pop', 0.4, 1.3);
    await S.wait(0.4);
    await S.fadeOut(0.6);
    p.visible = true;
    S.letterbox(false);
  }

  // ================================================================ 大街：找出跟踪狂
  const BUSHES = [{ id: 'b1', x: 384 }, { id: 'b2', x: 600 }, { id: 'b3', x: 768 }];
  const MISS = {
    b1: '草丛里蹲着一只猫。……猫看了你一眼，走了。',
    b2: '草丛里只有一个空的团子签子，和一张写着「阿妙小姐观察日记　第三十八册」的纸片。',
    b3: '草丛里什么都没有。……只有一股淡淡的、男人的汗味。',
  };
  async function talkOtae4(S, a) {
    if (!F().asked) {
      S.pose(a, 'idle_happy');
      await S.say('otae', '银时先生，来得正好。最近总觉得有人在暗处看着我呢～', { actor: a, expr: 'happy' });
      await S.say('gintoki', '跟踪狂？那种事找警察啊。');
      S.pose(a, 'idle_dark');
      S.sfx('aura', 0.6);
      await S.say('otae', '找过了哦。可是那个人……好像就是警察呢～', { actor: a, expr: 'dark_smile' });
      S.pose(a, 'idle_happy');
      await S.say('otae', '万事屋什么活都接吧？请帮我把他找出来。报酬是——我亲手做的煎蛋～', { actor: a, expr: 'happy' });
      await S.say('gintoki', '……那个报酬，能换成现金吗。');
      S.pose(a, 'eat_dango');
      F().asked = true;
      S.hint('跟踪狂就躲在这条街上。三个草丛里，哪一个长了张脸？（靠近调查）', 7);
      return;
    }
    await S.say('otae', '找到了吗～？我就在这里吃团子，不着急哦～', { actor: a, expr: 'happy' });
  }
  async function searchBush(S, b) {
    if (!F().asked) { await S.say('gintoki', '……一个草丛而已。'); return; }
    if (F().found) return;
    count('searched');
    await S.say(null, MISS[b.id]);
    if (F().searched === 2) await S.say('gintoki', '……跟踪狂会躲在离目标最近、又看得最清楚的地方。……大概。');
  }
  async function foundKondo(S, k) {
    const p = S.player, o = S.actor('otae'), st = G.world.stage;
    if (!F().asked) { await S.say('gintoki', '……这个草丛，怎么有点喘气声。'); return; }
    if (F().found) return;
    F().found = true;
    S.letterbox(true);
    S.sfx('squeak', 0.5, 1.2);
    await S.say('gintoki', '……喂。草丛先生。');
    await S.say('kondo', '阿妙小姐今天也好美啊～', { actor: k, expr: 'love' });
    S.nameCard('kondo');
    S.sfx('whoosh', 0.4);
    await S.say('gintoki', '你在这干什么。');
    await S.say('kondo', '……我只是路过的、普通的、在草丛里赏花的路人。', { actor: k, expr: 'peek' });
    await S.say('gintoki', '赏花的人，会顶着草丛一跳一跳地跟在女人后面吗。');
    // 阿妙转过身：「！」→ 近藤「！？」→ 笑眯眯地走过去 → 杀气
    S.pose(o, 'idle_open'); S.face(o, k);
    G.fx.word('！', o.x, o.y - 46, 0.8);
    S.sfx('shock', 0.7);
    await S.wait(0.3);
    S.pose(k, 'shock_shock', { restart: true });
    G.fx.word('！？', k.x, k.y - 44, 0.8);
    await S.wait(0.4);
    S.pose(o, 'idle_happy');
    const side = o.x < k.x ? -1 : 1;
    await S.walk(o, k.x + side * 22, k.y, { speed: 110, endAnim: 'idle_happy' });
    S.face(o, k);
    S.zoom(1.6, (o.x + k.x) / 2, k.y - 24, 0.15);
    await S.wait(0.3);
    S.sfx('aura', 0.9);
    S.state('dark', 0.55);
    S.pose(o, 'idle_dark');
    G.fx.word('杀气', o.x - 10, o.y - 52, 0.9);
    await S.say('otae', '跟踪狂给我去死吧～', { actor: o, expr: 'dark_smile' });
    S.pose(k, 'shock_cry', { restart: true });
    S.sfx('sweat', 0.5);
    // 超级拳
    S.pose(o, 'super_punch', { restart: true, speed: 0.6 });
    S.sfx('whoosh', 0.6);
    await S.wait(0.45);
    S.state('dark', 0);
    S.flash(0.06, 0.7);
    S.sfx('punch_big', 1.0); S.sfx('impact', 0.7);
    S.impact(3);
    G.fx.speedLines(192, 108, { count: 40, inner: 30, life: 0.3, color: '#ffffff' });
    G.fx.word('砰!!', k.x + 10, k.y - 50, 0.9);
    G.fx.debris(k.x, k.y - 10, ['#68ba52', '#3a8440', '#225834'], 18, [30, 110], 120, 1.1);
    S.shake(5, 0.4);
    S.zoom(1, null, null, 0.3);
    S.sfx('fly_away', 0.8);
    await S.arc(k, k.x - side * 90, k.y, 120, 0.7, { anim: 'fly_cry', z1: 220 });
    k.visible = false;
    G.fx.star(G.clamp(k.x - st.camX, 12, G.W - 12));
    S.sfx('twinkle', 0.8);
    G.fx.word('闪～☆', k.x - 12, 40, 1.0);
    await S.wait(0.9);
    S.pose(o, 'idle_happy');
    await S.say('otae', '谢谢你，银时先生～ 煎蛋改天再做给你吃哦。', { actor: o, expr: 'happy' });
    await S.say('gintoki', '……不用了。真的不用了。', { expr: 'gloom' });
    // 近藤从天上掉回来，要求决斗
    S.sfx('fall_whistle', 0.8);
    Object.assign(k, { visible: true, x: p.x + 60, y: p.y, z: 160 });
    await S.arc(k, p.x + 56, p.y, 4, 0.55, { anim: 'fly', z1: 0 });
    S.sfx('thud', 1.0); S.shake(3, 0.3);
    G.fx.dust(k.x, k.y, 10);
    S.pose(k, 'land_hurt', { restart: true });
    await S.wait(0.7);
    S.unpose(k); S.face(k, p); S.face(p, k);
    G.fx.img(SP().bump.image, k.x + 1, k.headY() - 2, { life: 2.0 });
    await S.say('kondo', '……天然卷！你和阿妙小姐是什么关系！？', { actor: k, expr: 'angry' });
    await S.say('gintoki', '雇主和打工的。');
    await S.say('kondo', '少骗人了！男人之间，用剑来说话！我真选组局长近藤勋，向你提出决斗！', { actor: k, expr: 'shout' });
    await S.say('gintoki', '……麻烦死了。打完就回去吃饭。');
    S.letterbox(false);
    S.hint('和近藤 1 对 1 决斗。他的重击之前会蓄力——看准了躲开或者按住 L 挡', 6);
    await S.fight({
      arena: [st.camX + 8, st.camX + 376],
      waves: [[{ actor: 'kondo', cid: 'kondo', name: '真选组局长 近藤勋', hp: 140, boss: true, speed: 52, range: 26, moves: ['E_SLASH', 'E_SLASH', 'E_HEAVY'], minHp: 1 }]],
      endWhen: () => { const b = S.actor('kondo'); return !!(b && b.team === 'enemy' && b.hp <= 14); },
      music: 'shinsengumi',
      after: null,
    });
    await afterDuel(S);
  }

  async function afterDuel(S) {
    const p = S.player, k = S.actor('kondo'), st = G.world.stage;
    S.letterbox(true);
    k.team = 'npc'; k.name = '近藤'; G.ui.boss = null;
    S.pose(k, 'kneel');
    await S.say('kondo', '……好身手。我输了。', { actor: k, expr: 'hurt' });
    await S.say('kondo', '不过！阿妙小姐的事，我是不会放弃的！', { actor: k, expr: 'determined' });
    // 土方、冲田来领人
    const h = gear(S.spawn('hijikata', st.camX - 20, 174, { id: 'hijikata', name: '土方', facing: 1 }));
    const o = gear(S.spawn('okita', st.camX - 44, 188, { id: 'okita', name: '冲田', facing: 1 }));
    S.sfx('run', 0.5);
    await Promise.all([S.walk(h, k.x - 44, 174, { speed: 90 }), S.walk(o, k.x - 66, 188, { speed: 90 })]);
    S.pose(h, 'smoke');
    await S.say('hijikata', '……近藤先生。又在大街上丢人现眼了吗。', { actor: h, expr: 'exhale' });
    await S.say('okita', '局长，跟踪狂被人打败，传出去真选组的脸往哪搁啊。……不过挺有意思的。', { actor: o, expr: 'smug' });
    S.unpose(k);
    await S.say('kondo', '十四、总悟！这家伙很强！我要请他到屯所吃饭！男人之间的友情！', { actor: k, expr: 'happy' });
    await S.say('hijikata', '……哈？', { actor: h, expr: 'angry' });
    await S.say('gintoki', '吃饭？免费的？那我去。');
    await S.fadeOut(0.6);
    F().toHQ = true;
  }

  // ================================================================ 屯所门口
  async function talkYamazaki(S, a) {
    if (count('yama') === 1) {
      S.unpose(a);
      await S.say('yamazaki', '啊，局长的客人？我是监察的山崎。……请不要告诉副长我在这儿打羽毛球。', { actor: a, expr: 'shock' });
      await S.say('gintoki', '监察是干什么的。');
      await S.say('yamazaki', '暗中调查、跟踪、潜入……总之就是不太起眼的工作。', { actor: a, expr: 'sad' });
      await S.say('gintoki', '……跟踪的话，你们局长也挺专业的。');
      S.pose(a, 'badminton');
    } else await S.say('yamazaki', '食堂在里面。……副长的盖饭，最好别看。', { actor: a, expr: 'gloom' });
  }

  // ================================================================ 食堂
  // 「土方特制盖饭」特写：转动的光芒、大碗、一圈圈挤上去的蛋黄酱山、横幅砸下来
  function mayoInsert(g, t) {
    const sp = SP();
    g.fillStyle = 'rgb(248,146,108)'; g.fillRect(0, 0, G.W, G.H);
    g.fillStyle = 'rgb(236,104,92)'; g.beginPath();
    for (let i = 0; i < 18; i++) {
      const a0 = t * 0.15 + (i * 2 * Math.PI) / 18, a1 = a0 + Math.PI / 18;
      g.moveTo(192, 150); g.lineTo(192 + Math.cos(a0) * 400, 150 + Math.sin(a0) * 400); g.lineTo(192 + Math.cos(a1) * 400, 150 + Math.sin(a1) * 400); g.closePath();
    }
    g.fill();
    g.fillStyle = 'rgb(120,74,46)'; g.fillRect(0, 184, G.W, 32);
    g.fillStyle = 'rgb(150,96,60)'; g.fillRect(0, 184, G.W, 3);
    const draw = (d, x, y) => { const im = G.image(d.image); if (G.ready(im)) g.drawImage(im, x + d.ox, y + d.oy); };
    draw(sp.big_bowl, 192, 164);
    const rv = Math.max(0, Math.min(1, (t - 0.05) / 0.95)), ease = rv < 0.5 ? 2 * rv * rv : 1 - Math.pow(-2 * rv + 2, 2) / 2;
    const fi = Math.min(23, Math.floor(ease * 23));
    draw(sp.pile_reveal[fi], 192, 161);
    const top = 161 - 98 * ease;
    let nozzle = Math.min(118, top - 12);
    if (t > 0.97) nozzle = 50 - 220 * Math.pow(Math.min(1, (t - 0.97) / 0.3), 2);
    if (rv < 1) {                                // 蛋黄酱从瓶嘴流下来
      const wob = Math.floor(t * 12) % 2;
      px(g, 190 + wob, nozzle + 1, '#e8d488', 4, Math.max(0, top + 2 - nozzle));
      px(g, 191 + wob, nozzle + 1, '#fff6c4', 2, Math.max(0, top + 2 - nozzle));
    }
    draw(sp.bottle[rv < 1 ? Math.floor(t * 6) % 2 : 2], 192, Math.round(nozzle));
    if (t > 0.95) {
      [[150, 90], [236, 70], [212, 130], [160, 128], [196, 50]].forEach(([x, y], i) => {
        const k = t - 0.95 - i * 0.08;
        if (k < 0 || k > 0.6) return;
        const s = Math.round(5 * Math.sin(Math.PI * k / 0.6));
        px(g, x - s, y, '#fff8d0', 2 * s + 1, 1); px(g, x, y - s, '#fff8d0', 1, 2 * s + 1);
      });
    }
    if (t > 0.5) {
      const im = G.image(sp.banner.image), s = 1 + 1.6 * Math.max(0, 1 - (t - 0.5) / 0.15);
      if (G.ready(im)) g.drawImage(im, Math.round(sp.banner.cx - im.width * s / 2), Math.round(sp.banner.cy - im.height * s / 2), Math.round(im.width * s), Math.round(im.height * s));
    }
  }
  async function talkHijikata(S, a) {
    if (F().afro) { await S.say('hijikata', '……别看我的头发。', { actor: a, expr: 'angry' }); return; }
    if (!F().mayo) {
      await S.say('hijikata', '……你就是让近藤先生出丑的那个天然卷？', { actor: a });
      await S.say('gintoki', '是他自己出丑的。我只是在旁边看着。');
      await S.say('hijikata', '哼。……吃饭吗？今天的特制盖饭，分你一碗。', { actor: a, expr: 'exhale' });
      await mayoBowl(S, a);
      return;
    }
    await S.say('hijikata', '蛋黄酱，就是正义。', { actor: a });
  }
  async function mayoBowl(S, h) {
    S.letterbox(true);
    S.sfx('slide_up', 0.6);
    S.insert(mayoInsert);
    await S.wait(0.5);
    S.sfx('shine', 0.7); S.shake(3, 0.2);
    await S.wait(0.5);
    S.sfx('sparkle', 0.6);
    await S.wait(1.0);
    S.insert(null);
    S.nameCard('hijikata');
    S.sfx('whoosh', 0.35);
    await S.say('hijikata', '蛋黄酱，就是正义。', { actor: h });
    const c = await S.choice(['吃一口', '「这已经不是饭了吧」', '「能换成红豆饭吗」'], '要吃吗？');
    if (c === 0) {
      await S.say(null, '……一口下去，满嘴都是蛋黄酱。');
      await S.say('gintoki', '……这是蛋黄酱，饭在哪里？', { expr: 'cry' });
      await S.say('hijikata', '饭在最底下。耐心挖。', { actor: h });
    } else if (c === 1) {
      vein(h);
      await S.say('hijikata', '……你说什么？', { actor: h, expr: 'angry' });
      await S.say('hijikata', '蛋黄酱是一切料理的完成形。饭只是盛蛋黄酱的容器。', { actor: h });
    } else {
      await S.say('gintoki', '在红豆饭上面再浇一层砂糖，这才是正义。');
      await S.say('hijikata', '……甜党是吧。我们合不来。', { actor: h, expr: 'angry' });
    }
    S.letterbox(false);
    F().mayo = true;
    S.hint('食堂另一头，有人在红坐垫上睡觉', 5);
  }
  async function talkOkitaNap(S, o) {
    if (F().afro) { await S.say('okita', '……嘘。我在想下一发要瞄准哪里。', { actor: o, expr: 'smug' }); return; }
    if (!F().mayo) { await S.say(null, '一个戴着眼罩的人在红坐垫上睡得正香。……眼罩上画着一双眼睛。'); return; }
    await okitaWakes(S, o);
  }
  async function okitaWakes(S, o) {
    const p = S.player, sp = SP(), st = G.world.stage;
    const h = S.actor('hijikata');
    S.letterbox(true);
    await S.say(null, '一个戴着眼罩的人在红坐垫上睡得正香。');
    await S.say('gintoki', '……喂，起床了。你们副长的盖饭要被我吃完了。');
    // 推近到脸上：眼罩掀开，抖S的眼睛
    S.zoom(3, o, -14, 0.1);
    S.sfx('whoosh', 0.55, 1.4);
    G.fx.speedLines(192, 108, { count: 30, inner: 70, life: 0.4, color: '#ffffff' });
    S.pose(o, 'nap_wake', { restart: true });
    S.sfx('shine', 0.7);
    S.nameCard('okita');
    await S.wait(0.6);
    await S.say('okita', '……吵死了。好不容易梦到土方先生被埋进土里。', { actor: o, expr: 'sadist' });
    S.zoom(1, null, null, 0.25);
    S.sfx('pop', 0.6);
    G.fx.dust(o.x, o.y, 8);
    S.unpose(o, { x: 404 });
    o.facing = -1;
    S.camera(G.clamp(Math.round((h.x + o.x) / 2 - G.W / 2), 0, 640 - G.W));   // 土方和冲田一起入镜
    await S.say('hijikata', '总悟！你又在值班的时候睡觉——', { actor: h, expr: 'angry' });
    S.pose(o, 'bazooka', { restart: true, speed: 0.6 });
    S.sfx('charge', 0.45);
    await S.wait(0.5);
    await S.say('okita', '土方先生，去死吧。', { actor: o, expr: 'sadist' });
    // 发射：炮弹横穿整个食堂
    S.sfx('bazooka', 0.9);
    S.flash(0.05, 0.35, '#fff0b4');
    const x0 = o.x - 26, y0 = o.y - 13, x1 = h.x + 4, y1 = h.y - 14;
    const rk = S.prop({ type: 'custom', x: x0, y: y0, depth: 400, draw: (g, x, y, t) => {
      const d = frame([sp.rocket0, sp.rocket1], 15, t), im = G.image(d.image);
      if (G.ready(im)) g.drawImage(im, x + d.ox, y + d.oy);
    } });
    S.sfx('whoosh', 0.7, 1.2);
    await S.animate(0.35, (u) => {
      const e = u * u;
      rk.x = G.lerp(x0, x1, e); rk.y = G.lerp(y0, y1, e);
      if (Math.random() < 0.6) G.fx.add({ kind: 'puff', x: rk.x + 18, y: rk.y, vx: 0, vy: -6, r: 2, life: 0.45, color: '230,230,230' });
    });
    S.unprop(rk);
    S.flash(0.06, 0.9);
    S.impact(2);
    boom(S, h.x, h.y - 6, 30, '轰!!');
    // 黑烟散开：爆炸头，盖饭也烧焦了
    S.pose(h, 'sit_afro');
    st.state.charred = true;
    F().afro = true;
    await S.wait(1.0);
    S.sfx('crow', 0.7);
    G.fx.word('阿呆～', h.x + 30, 60, 1.0);
    await S.wait(0.8);
    S.sfx('jump', 0.6);
    await S.arc(h, h.x - 4, h.y, 16, 0.16, { anim: 'jump_afro' });
    S.sfx('thud', 0.8); S.sfx('vein', 0.8); S.sfx('impact', 0.5);
    S.pose(h, 'point_afro', { restart: true });
    S.shake(3, 1.0);
    G.fx.word('怒', h.x + 20, h.y - 60, 1.0);
    vein(h);
    await S.say('hijikata', '总悟你这混蛋！！', { actor: h, expr: 'shout' });
    // 冲田看向别处吹口哨
    o.facing = 1;
    S.pose(o, 'idle');
    for (let i = 0; i < 4; i++) {
      G.fx.img(sp.note.image, o.x - 8 - i * 4, o.y - 26, { vx: -10, vy: -20, life: 0.9, fade: true });
      S.sfx('blip', 0.4, 2.2 + i * 0.2);
      await S.wait(0.19);
    }
    o.facing = -1;
    await S.say('okita', '啊，失手了。……下次会瞄准一点。', { actor: o, expr: 'smug' });
    await S.say('okita', '对了，旦那也在啊。……要不要一起被炸一下？', { actor: o, expr: 'sadist' });
    await S.say('gintoki', '我拒绝！', { expr: 'shout' });
    S.unpose(h);
    S.camera(null);
    S.letterbox(false);
    S.hint('冲田的火箭筒连发！左右跑、上下躲、按 K 跳——撑 12 秒', 7);
    await S.fight({
      arena: [Math.max(0, st.camX) + 8, Math.max(0, st.camX) + 376],
      music: 'battle',
      waves: [[{ actor: 'okita', cid: 'okita', name: '一番队队长 冲田总悟', hp: 999, boss: true, ranged: 130, speed: 46, moves: ['E_BAZOOKA'], dmgMul: () => 0, noCharge: true }]],
      timer: { label: '撑住！还有 ', until: 12 },
      survive: true,
      endWhen: () => G.world.fightT >= 12,
      after: 'shinsengumi',
    });
    o.team = 'npc'; o.name = '冲田';
    G.ui.boss = null;
    await finalPose(S);
  }

  // ================================================================ 中庭：「诚」字旗前亮相
  async function finalPose(S) {
    const p = S.player, sp = SP();
    S.letterbox(true);
    await S.say('okita', '……撑下来了啊。不愧是旦那。', { actor: S.actor('okita'), expr: 'smug' });
    await S.say('gintoki', '这里到底是警察局还是战场。');
    await S.fadeOut(0.6);
    await S.setStage('courtyard_ch4', { x: 330, y: 186, facing: -1, fade: false });
    S.music('shinsengumi', 0.5);
    const st = G.world.stage;
    const k = gear(S.actor('kondo')), h = gear(S.actor('hijikata')), o = gear(S.actor('okita'));
    S.pose(h, 'idle_afro'); S.pose(o, 'idle');
    k.visible = false;
    await S.fadeIn(0.6);
    // 近藤从天上掉下来（被阿妙打飞的那一下，现在才落地）
    S.sfx('fall_whistle', 0.7);
    Object.assign(k, { visible: true, z: 180 });
    await S.arc(k, k.x, k.y, 2, 0.55, { anim: 'fly', z1: 0 });
    S.sfx('thud', 0.9); S.shake(4, 0.3);
    G.fx.dust(k.x, k.y, 10);
    S.pose(k, 'land_hurt', { restart: true });
    await S.wait(0.6);
    S.pose(k, 'shoulder_smug');
    G.fx.img(sp.bump.image, k.x + 1, k.headY() - 2, { life: 3.0 });
    await S.say('kondo', '天然卷！今天的饭，好吃吗！', { actor: k, expr: 'happy' });
    await S.say('gintoki', '……蛋黄酱和火药的味道。');
    // 亮相
    S.flash(0.07, 0.8);
    S.sfx('sting_dramatic', 0.8); S.sfx('impact', 0.5);
    S.pose(h, 'draw_afro', { restart: true });
    S.pose(o, 'bazooka', { restart: true, speed: 0.3 });
    st.state.raysHi = true;
    G.fx.speedLines(192, 136, { count: 40, inner: 26, life: 0.45, color: '#fffff0' });
    const t0 = st.t;
    const title = S.prop({ type: 'custom', x: 0, y: 0, depth: 999, draw: (g, x, y, t) => {
      const im = G.image(sp.title.image), u = t - t0;
      const s = 1 + 2 * Math.max(0, 1 - u / 0.15);
      if (G.ready(im)) g.drawImage(im, Math.round(sp.title.cx - im.width * s / 2), Math.round(sp.title.cy - 60 - im.height * s / 2), Math.round(im.width * s), Math.round(im.height * s));
      if (u > 0.35) G.f12.draw(g, '江户特别武装警察', G.W / 2, sp.title.cy - 60 + 22, '#ffec96', { align: 'center', outline: '#181425' });
    } });
    S.sfx('shing', 0.6);
    await S.wait(0.6);
    S.sfx('sparkle', 0.5);
    await S.wait(1.6);
    S.unprop(title);
    // 冲田悄悄把炮口转向土方：激光瞄准点爬上爆炸头
    S.pose(o, 'bazooka_aim_sadist', { restart: true });
    S.sfx('laser', 0.25, 1.4);
    const l0 = st.t;
    const laser = S.prop({ type: 'custom', x: 0, y: 0, depth: 998, draw: (g, x, y, t) => {
      const u = Math.min(1, (t - l0) / 0.25), cx = st.camX;
      const ax = o.x - 22 - cx, ay = o.y - 17, bx = h.x - cx, by = h.headY() - 6;
      const ex = G.lerp(ax, bx, u), ey = G.lerp(ay, by, u), f = Math.floor(t * 12);
      for (let i = 0; i < 40; i++) {
        const k2 = i / 40;
        if ((i + f) % 4 === 3) continue;
        px(g, G.lerp(ax, ex, k2), G.lerp(ay, ey, k2), (i + f) % 4 === 0 ? 'rgb(255,236,236)' : 'rgb(255,50,50)', 2, 1);
      }
      if (u >= 1) { const r = Math.floor(t * 8) % 2 ? 3 : 2; px(g, bx - r, by - r, 'rgb(255,40,40)', 2 * r + 1, 2 * r + 1); px(g, bx - 1, by - 1, 'rgb(255,220,220)', 3, 3); }
    } });
    await S.wait(0.35);
    S.sfx('shock', 0.5); S.sfx('sweat', 0.6);
    G.fx.word('喂！', h.x + 4, h.y - 56, 1.6);
    G.fx.img(sp.sweat.image, h.x + 8, h.headY() + 2, { vy: 8, life: 1.0, fade: true });
    await S.say('hijikata', '喂！总悟！', { actor: h, expr: 'shock' });
    await S.say('okita', '……顺便一提，土方先生的头发，大概要三天才能长回来。', { actor: o, expr: 'sadist' });
    await S.say('kondo', '哈哈哈！真选组今天也很有精神！', { actor: k, expr: 'happy' });
    await S.say('gintoki', '……这就是江户的警察啊。江户完蛋了。', { expr: 'gloom' });
    S.unprop(laser);
    S.letterbox(false);
    await S.fadeOut(1.2);
    F().ch4Done = true;
  }

  // ================================================================ 地图（第四章版）：进这一章时才建（要用到导出的素材）
  function defineStages() {
    const sp = SP();
    // 屯所门口（开场的空镜头用）
    G.STAGES.hq_open_ch4 = { id: 'hq_open_ch4', bg: 'hq_gate', x0: 0, x1: 384, yMin: 160, yMax: 204, music: 'shinsengumi', props: [],
      npcs: [{ cid: 'yamazaki', id: 'yamazaki', x: 92, y: 172, facing: 1, anim: 'badminton' }] };
    // 大街：三个草丛，近藤躲在其中一个（每次开局随机）；阿妙在甘味处门口吃团子
    const at = F().kondoAt;
    G.STAGES.street_ch4 = Object.assign({}, G.STAGES.street, {
      id: 'street_ch4', music: 'comedy',
      props: BUSHES.filter((b) => b.id !== at).map((b, i) => ({ type: 'image', image: sp[`bush${i % 2}`].image, x: b.x, y: 168, ax: 13, ay: 19, depth: 168 }))
        .concat([{ type: 'custom', x: 0, y: 0, depth: 9998, draw: (g) => {           // 阿妙的杀气：整个世界暗下来
          const a = G.world.stage.state.dark || 0;
          if (a > 0) { g.fillStyle = `rgba(34,10,50,${a})`; g.fillRect(0, 0, G.W, G.H); }
        } }]),
      npcs: [
        { cid: 'otae', id: 'otae', alt: ['otae__s04'], x: 484, y: 172, facing: -1, anim: 'eat_dango', label: '阿妙', talk: talkOtae4 },
        { cid: 'kondo', id: 'kondo', alt: ['kondo__s04'], x: BUSHES.find((b) => b.id === at).x, y: 168, facing: 1, anim: 'stalk', label: '草丛', talk: foundKondo },
        { cid: 'townsman__v1', id: 'passer', x: 300, y: 178, facing: 1, label: '路人',
          talk: async (S) => {
            await S.say('townsman', '……那边有个草丛，刚才是不是跟着那位小姐挪了一下？', { name: '路人' });
            await S.say('townsman', '而且……草丛里好像有人在流口水。', { name: '路人' });
          } },
        { cid: 'townswoman__v1', id: 'dango', x: 530, y: 168, facing: -1, label: '团子店大婶',
          talk: async (S) => {
            await S.say('townswoman', '那位警察先生每天都来。买一串团子，然后在草丛里看阿妙小姐一整天。', { name: '团子店大婶' });
            await S.say('gintoki', '……这种事你倒是早点报警啊。');
            await S.say('townswoman', '可他就是警察啊。', { name: '团子店大婶' });
          } },
        { cid: 'otose', id: 'otose', x: 356, y: 168, facing: -1, anim: 'smoke', label: '登势',
          talk: async (S, a) => { await S.say('otose', '跟踪狂？……这条街上奇怪的人太多了，你得说清楚是哪一个。', { actor: a }); } },
      ],
      hotspots: BUSHES.filter((b) => b.id !== at).map((b) => ({ id: b.id, x: b.x, y: 172, r: 16, ry: 14, label: '草丛', ly: 136, use: async (S) => searchBush(S, b) })),
    });
    // 屯所门口（可以逛）
    G.STAGES.hq_ch4 = { id: 'hq_ch4', bg: 'hq_gate', x0: 0, x1: 384, yMin: 164, yMax: 204, music: 'shinsengumi', props: [],
      npcs: [
        { cid: 'yamazaki', id: 'yamazaki', x: 92, y: 172, facing: 1, anim: 'badminton', label: '山崎', talk: talkYamazaki },
        { cid: 'kondo', id: 'kondo', x: 236, y: 176, facing: -1, label: '近藤',
          talk: async (S, a) => { await S.say('kondo', '进来进来！食堂在里面！十四今天做了他的拿手菜！', { actor: a, expr: 'happy' }); } },
      ],
      hotspots: [
        { id: 'gate', x: 192, y: 166, r: 26, ry: 8, label: '进屯所', ly: 100,
          use: async (S) => { await S.setStage('canteen_ch4', { x: 40, y: 184, facing: 1 }); } },
        { id: 'sign', x: 250, y: 168, r: 10, ry: 10, label: '门牌', ly: 88, use: async (S) => { await S.say(null, '门柱上挂着「真选组屯所」的门牌。字写得很有气势。'); } },
        { id: 'flag', x: 330, y: 168, r: 16, ry: 10, label: '旗', ly: 60, use: async (S) => { await S.say(null, '旗杆上飘着一面「诚」字旗。'); await S.say('gintoki', '……诚。跟踪狂的局长、蛋黄酱副长，诚在哪里。'); } },
      ] };
    // 食堂（640 宽）：土方坐在桌子后面抽烟，碗里是蛋黄酱山；冲田在最里面的红坐垫上午睡
    G.STAGES.canteen_ch4 = { id: 'canteen_ch4', bg: 'canteen', x0: 0, x1: 640, yMin: 166, yMax: 204, music: 'shinsengumi',
      props: [
        grabProp(sp.table, 0, 0, 170),
        grabProp(sp.small_bowl_0, 160, 150, 170.4),
        { type: 'custom', x: 160, y: 144, depth: 170.6, draw: (g, x, y, t) => {
          const d = G.world.stage.state.charred ? frame(sp.pile_charred, 12, t) : sp.pile_clean, im = G.image(d.image);
          if (G.ready(im)) g.drawImage(im, x + d.ox, y + d.oy);
        } },
        grabProp(sp.tea_cup, 118, 150, 170.5),
      ],
      npcs: [
        { cid: 'hijikata', id: 'hijikata', alt: ['hijikata__s04'], x: 140, y: 151, facing: 1, anim: 'smoke_sit', label: '土方', talk: talkHijikata, talkRy: 26 },
        { cid: 'okita', id: 'okita', alt: ['okita__s04'], x: 424, y: 160, facing: -1, anim: 'nap', label: '睡觉的人', talk: talkOkitaNap },
        { cid: 'townsman__v2', id: 'cook', x: 356, y: 168, facing: 1, label: '食堂大叔',
          talk: async (S) => { await S.say('townsman', '副长每天要用掉三瓶蛋黄酱。……我们食堂的进货单，一半都是蛋黄酱。', { name: '食堂大叔' }); } },
      ],
      hotspots: [
        { id: 'menu', x: 80, y: 168, r: 30, ry: 10, label: '菜单', ly: 70,
          use: async (S) => { await S.say(null, '墙上挂着菜单：定食、乌冬、团子、荞麦，还有用红字写的「蛋黄酱」。'); await S.say('gintoki', '……蛋黄酱是一道菜吗。'); } },
        { id: 'scroll', x: 460, y: 168, r: 16, ry: 10, label: '挂轴', ly: 70,
          use: async (S) => { await S.say(null, '挂轴上写着「局中法度」。第一条：违背武士道者，切腹。'); await S.say('gintoki', '……那在草丛里跟踪女人，算不算违背武士道。'); } },
        { id: 'hatch', x: 300, y: 168, r: 30, ry: 6, label: '厨房', ly: 76,
          use: async (S) => { await S.say(null, '厨房的窗口里堆着一箱箱蛋黄酱。最上面那箱写着「副长专用」。'); } },
      ] };
    // 中庭：巨大的「诚」字旗
    G.STAGES.courtyard_ch4 = { id: 'courtyard_ch4', bg: 'courtyard', x0: 0, x1: 384, yMin: 164, yMax: 204, music: 'shinsengumi', props: [],
      npcs: [
        { cid: 'hijikata', id: 'hijikata', alt: ['hijikata__s04'], x: 150, y: 176, facing: -1 },
        { cid: 'kondo', id: 'kondo', alt: ['kondo__s04'], x: 192, y: 176, facing: 1 },
        { cid: 'okita', id: 'okita', alt: ['okita__s04'], x: 236, y: 176, facing: -1 },
      ] };
  }

  // ================================================================ 第四章主流程
  G.STORY.chapter4 = async function (S) {
    G.flags.kondoAt = G.pick(BUSHES).id;
    defineStages();
    G.fadeAlpha = 0;
    G.world.stage = null;
    await S.chapterCard('ch4');
    const p = new G.Actor('gintoki', 192, 200, { id: 'player', team: 'player', hp: 100, speed: 72, name: '银时' });
    G.world.player = p;
    G.fadeAlpha = 1;
    await S.setStage('hq_open_ch4', { x: 192, y: 200, facing: 1, fade: false });
    await S.run(async (S) => {
      await opening(S);
      await S.setStage('street_ch4', { x: 200, y: 182, facing: 1, fade: false });
      await S.fadeIn(0.6);
      await S.say('gintoki', '（阿妙说有事找万事屋。……该不会又要请我吃煎蛋吧。）');
      S.hint('去甘味处门口找阿妙', 5);
    });
    await S.until(() => G.flags.toHQ);
    await S.run(async (S) => {
      await S.setStage('hq_ch4', { x: 40, y: 190, facing: 1, fade: false });
      await S.fadeIn(0.6);
      await S.say('gintoki', '（真选组屯所。……警察局请我吃饭，这辈子还是头一回。）');
      S.hint('从大门进屯所', 4);
    });
    await S.until(() => G.flags.ch4Done);
  };
})();
