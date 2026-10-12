// 第三章：神乐与定春（原片 s03）
//   周一夜里，银时骑小绵羊买完 Jump 回家（自动卷轴：跳过路上的东西）→ 撞上从巷子里冲出来的女孩
//   → 神乐：「你撞到人了阿鲁！」→ 她以为银时是来抓她的，雨伞机枪扫射（撑过去）
//   → 追她的黑道打手冲出来，和神乐一起打 → 回万事屋：吃空饭锅（抢最后一碗）、钱包里的伙食费飞走
//   → 第二天：门口的「请收养」纸箱，巨型犬定春，一口咬住银时的头（连按挣脱）→ 阳台上「万事屋，集结！」
'use strict';
(function () {
  const G = window.G;
  const F = () => G.flags;
  const count = (key) => (G.flags[key] = (G.flags[key] || 0) + 1);
  const SP = () => G.D.bg.ch3;           // 第三章的小道具（tools/bg_chapters.py 的 ch3 导出）
  const sweat = (a, dx = 7) => G.fx.img(G.D.bg.ch2.sweat.image, a.x + dx, a.headY() + 4, { vy: 7, life: 0.9, fade: true });
  const vein = (a, dx = -5) => G.fx.img(G.D.bg.ch2.vein.image, a.x + dx, a.headY() + 3, { life: 1.3, pulse: true });

  // ================================================================ 夜路：骑小绵羊回家（自动卷轴）
  function scooterRide() {
    const sp = SP();
    return { frames: sp.scooter.frames, fps: 16, ax: sp.scooter.ax, ay: sp.scooter.ay, seat: sp.scooter.seat, dx: sp.scooter.dx || 0,
      light: { image: sp.headlight.image, ox: sp.headlight.ox, oy: sp.headlight.oy } };
  }
  // 银时：骑车挖鼻孔、被定春叼着乱晃这些动作在 gintoki__s03 里
  function gearUp(p) { p.alt = [G.atlas('gintoki__s03')]; p.rideAnim = 'scooter_nosepick'; }
  async function nightRide(S) {
    const p = S.player, st = G.world.stage, sp = SP();
    // 路上的障碍：木箱、垃圾桶、躺在路上的醉汉（跳过去）
    const obstacles = [];
    const put = (x, y, key, o = {}) => obstacles.push(Object.assign({ x, y, w: sp[key].w, h: 8, tall: 14, dmg: 15,
      prop: { image: sp[key].image, ay: sp[key].h, depth: y } }, o));
    put(300, 176, 'crate');
    put(390, 190, 'bin');
    put(470, 168, 'crate');
    put(560, 184, 'bin');
    put(650, 172, 'crate');
    put(720, 190, 'crate');
    put(800, 168, 'bin');
    put(880, 180, 'crate');
    // 两个喝醉躺在路上的大叔（真人，压过去会被骂）
    const drunk1 = S.spawn('townsman__v3', 610, 188, { id: 'drunk1', anim: 'lie', facing: -1 });
    const drunk2 = S.spawn('townsman', 940, 170, { id: 'drunk2', anim: 'lie', facing: 1 });
    obstacles.push({ x: 610, y: 188, w: 26, h: 7, tall: 10, dmg: 10, word: '呜哇!', sfx: 'punch' });
    obstacles.push({ x: 940, y: 170, w: 26, h: 7, tall: 10, dmg: 10, word: '呜哇!', sfx: 'punch' });
    S.hint('骑小绵羊回万事屋：按 K 跳过路上的东西，↑ ↓ 换车道，← → 加减速', 7);
    S.sfx('scooter', 0.5);
    await S.runner({
      cam0: 0, endX: 760, speed: 92, y: 178, rx: 90, ride: scooterRide(), obstacles,
      onTick: (dt, t) => { if (Math.floor(t * 2) !== Math.floor((t - dt) * 2) && Math.random() < 0.5) S.sfx('engine_hum', 0.25); },
    });
    S.remove(drunk1); S.remove(drunk2);
  }

  // 撞上神乐
  async function crash(S) {
    const p = S.player, st = G.world.stage;
    const k = S.spawn('kagura', st.camX + 330, 166, { id: 'kagura', name: '神乐', facing: -1 });
    k.visible = false;
    p.runner = true;
    // 小绵羊冲向巷口，女孩突然冲出来
    S.stopMusic(0.3);
    await S.animate(0.5, (t) => { p.rx = G.lerp(110, 200, t); p.x = st.camX + p.rx; });
    p.runner = false;
    Object.assign(k, { visible: true, x: p.x + 30, y: p.y - 4 });
    S.emote(p, '!!', 0.5, '#fff');
    S.sfx('crash', 1.0); S.sfx('impact', 0.7);
    S.shake(4, 0.35);
    S.flash(0.12, 0.7);
    G.fx.word('咚!', p.x + 24, p.y - 46);
    G.fx.spark(p.x + 26, p.y - 20, '#fff4c0', 10);
    // 神乐飞起来再落下；银时连人带车摔出去
    const kx0 = k.x;
    S.arc(k, kx0 + 60, 172, 50, 0.7, { anim: 'fly' }).then(() => { S.pose(k, 'lie'); });
    p.ride = null;
    const dn = SP().scooter_down;
    const bike = S.prop({ image: dn.image, x: p.x, y: p.y, ax: -dn.ox, ay: -dn.oy, depth: p.y });
    await S.arc(p, p.x - 30, p.y + 6, 24, 0.5, { anim: 'fly' });
    S.sfx('thud', 0.9);
    S.pose(p, 'lie');
    G.fx.dust(p.x, p.y, 8);
    await S.wait(0.9);
    return bike;
  }

  async function meetKagura(S) {
    const p = S.player, k = S.actor('kagura');
    S.letterbox(true);
    S.unpose(k);
    S.sfx('jump', 0.6);
    await S.arc(k, k.x, k.y, 14, 0.3, { anim: 'jump' });
    S.unpose(k);
    S.face(k, p);
    S.music('comedy', 0.6);
    await S.say('kagura', '喂！你撞到人了阿鲁！', { actor: k, expr: 'angry' });
    S.nameCard('kagura');
    S.unpose(p);
    await S.say('gintoki', '……被小绵羊撞飞，还能自己站起来？', { expr: 'shock' });
    await S.say('kagura', '我是夜兔族阿鲁。这点程度，跟被蚊子叮了一下差不多。', { actor: k });
    await S.say('gintoki', '（夜兔族……听说是宇宙里最能打的战斗民族。）');
    await S.say('kagura', '……等一下。大半夜骑着小绵羊在这一带转悠——', { actor: k, expr: 'smug' });
    await S.say('kagura', '你也是那帮人派来抓我的阿鲁！？', { actor: k, expr: 'angry' });
    await S.say('gintoki', '哈？我只是买完 Jump 回家的路人——');
    S.pose(k, 'umbrella_open', { restart: true });
    S.sfx('whoosh', 0.6);
    await S.say('kagura', '少废话阿鲁！', { actor: k, expr: 'shout' });
    S.letterbox(false);
  }

  // 神乐误会了：雨伞机枪扫射，撑过去
  async function dodgeKagura(S) {
    const p = S.player;
    S.hint('神乐的雨伞机枪！左右走、上下换位置、K 跳、按住 L 挡——撑 12 秒', 7);
    await S.fight({
      arena: [G.world.stage.camX + 8, G.world.stage.camX + 376],
      music: 'battle',
      waves: [[{ actor: 'kagura', cid: 'kagura', name: '误会中的神乐', hp: 999, boss: true, ranged: 110, speed: 52,
        moves: ['E_GUN'], dmgMul: () => 0, noCharge: true }]],
      timer: { label: '撑住！还有 ', until: 12 },
      survive: true,
      endWhen: () => G.world.fightT >= 12,
      onWave: async (S, i, es, attempt) => {
        if (attempt === 0) await S.say('kagura', '哒哒哒哒哒——！', { actor: es[0], expr: 'shout' });
      },
      after: null,
    });
    const k = S.actor('kagura');
    k.team = 'npc';
    k.name = '神乐';
    G.ui.boss = null;
  }

  // 真正追她的黑道打手冲出来：和神乐一起打
  async function yakuzaFight(S) {
    const p = S.player, k = S.actor('kagura'), st = G.world.stage;
    S.letterbox(true);
    const cx = st.camX;
    const y1 = S.spawn('_yakuza0', cx + 410, 170, { id: 'ya1', name: '黑道打手', facing: -1 });
    const y2 = S.spawn('_yakuza1', cx + 430, 186, { id: 'ya2', name: '黑道打手', facing: -1 });
    S.sfx('run', 0.5);
    await Promise.all([S.walk(y1, cx + 330, 170, { speed: 90, anim: 'run' }), S.walk(y2, cx + 350, 186, { speed: 90, anim: 'run' })]);
    G.fx.word('站住!!', cx + 340, 130, 0.9);
    await S.say('_yakuza0', '找到了！那个丫头在这儿！', { name: '黑道打手', actor: y1, expr: 'shout' });
    await S.say('_yakuza1', '……旁边那个天然卷是谁？一起收拾了！', { name: '黑道打手', actor: y2 });
    S.emote(k, '!', 0.6);
    await S.say('kagura', '……原来你不是他们的人阿鲁。', { actor: k });
    await S.say('gintoki', '我一开始就说了吧！');
    await S.say('kagura', '那正好。天然卷，帮我一起揍他们阿鲁！', { actor: k, expr: 'smug' });
    await S.say('gintoki', '……我的 Jump 被你打了好几个洞，这笔账回头再算。');
    S.letterbox(false);
    k.ranged = 80;
    k.allyMoves = [G.MOVES.E_GUN];
    S.hint('神乐会在后面用雨伞机枪帮你打', 5);
    await S.fight({
      arena: [cx + 8, cx + 376],
      allies: ['kagura'], allyHp: 80,
      waves: [
        [{ actor: 'ya1', cid: '_yakuza0', name: '黑道打手', hp: 26 }, { actor: 'ya2', cid: '_yakuza1', name: '黑道打手', hp: 26 },
          { cid: '_yakuza2', id: 'ya3', name: '黑道打手', hp: 24, side: 'left' }],
        [{ cid: '_yakuza1', id: 'ya4', name: '黑道打手', hp: 24 }, { cid: '_yakuza0', id: 'ya5', name: '黑道打手', hp: 24, side: 'left' },
          { cid: '_yakuza2', id: 'yaboss', name: '黑道大哥', hp: 120, boss: true, scale: 1.25, speed: 40, moves: ['E_SLASH', 'E_PUNCH', 'E_HEAVY'] }],
      ],
      onWave: async (S, i, es) => {
        if (i === 1) {
          const b = es.find((e) => e.boss);
          await S.say('_yakuza2', '没用的东西……丫头，跟我回去干活！', { name: '黑道大哥', actor: b, expr: 'angry' });
          await S.say('kagura', '我不干了阿鲁！你们说的「打工」，根本不是正经工作！', { actor: k, expr: 'angry' });
        }
      },
      after: 'comedy',
    });
    k.ranged = 0;
    k.allyMoves = null;
  }

  // ================================================================ 万事屋（夜）：吃空饭锅
  async function officeNight(S) {
    const p = S.player, sp = SP();
    const k = S.actor('kagura'), s = S.actor('shinpachi');
    S.letterbox(true);
    await S.say('shinpachi', '银时先生，您总算回来了——这孩子是谁？', { actor: s, expr: 'shock' });
    await S.say('kagura', '我是神乐阿鲁。……好饿。有饭吗？', { actor: k });
    await S.say('gintoki', '电饭锅里应该还有点。……就一点。');
    // 神乐坐到桌边狂吃：碗越堆越高
    await S.walk(k, 192, 160, { speed: 80 });
    S.pose(k, 'eat', { y: 160 });
    const tower = S.prop({ type: 'custom', x: 214, y: 160, depth: 161, n: 0, draw: (g, x, y) => {
      const im = G.image(sp.bowl.image);
      for (let i = 0; i < tower.n; i++) g.drawImage(im, x - Math.floor(im.width / 2), y - (i + 1) * (sp.bowl.h - 2));
    } });
    for (let i = 0; i < 5; i++) { tower.n++; S.sfx('eat', 0.5, G.rand(0.9, 1.2)); await S.wait(0.28); }
    await S.say('kagura', '再来一碗阿鲁！', { actor: k, expr: 'happy' });
    for (let i = 0; i < 6; i++) { tower.n++; S.sfx('eat', 0.5, G.rand(0.9, 1.2)); await S.wait(0.2); }
    G.fx.word('嗖!', 214, 160 - tower.n * 8);
    sweat(s); sweat(p, -8);
    await S.say('shinpachi', '已、已经第十一碗了……！', { actor: s, expr: 'shock' });
    await S.say('gintoki', '新八，最后一碗。抢下来！不然明天早饭就没了！');
    S.letterbox(false);
    const ok = await S.timing({ label: '抢下最后一碗饭！（看准时机按 J）', speed: 1.3, zone: [0.45, 0.57] });
    S.letterbox(true);
    if (ok) {
      await S.say('gintoki', '拿到了！……嗯？');
      await S.say(null, '碗里空空如也。神乐已经把饭倒进嘴里了。');
    } else {
      await S.say(null, '手刚伸过去，碗已经空了。');
    }
    tower.n++;
    await S.say('kagura', '多谢款待阿鲁！', { actor: k, expr: 'happy' });
    // 钱包里的伙食费飞走（银时打开钱包看了一眼）
    const wx = p.x + p.facing * 10, wy = p.y - 13;
    const wallet = S.prop({ image: sp.wallet_open.image, x: wx, y: wy, ay: sp.wallet_open.h, depth: p.y + 1 });
    S.sfx('coin', 0.8);
    for (let i = 0; i < 5; i++) G.fx.img(sp.coin.frames[i % sp.coin.frames.length], wx - 6 + i * 3, wy - 10, { vx: G.rand(-40, 40), vy: G.rand(-90, -60), life: 0.9, fade: true });
    await S.wait(0.5);
    await S.say('shinpachi', '我们的伙食费啊！', { actor: s, expr: 'cry' });
    G.fx.text('空……', wx, wy - 26, { life: 1.4, vy: -6 });
    await S.wait(0.8);
    S.unprop(wallet);
    await S.say('gintoki', '……这个月，又要吃糖了。');
    await S.say('shinpachi', '糖不是饭！', { actor: s, expr: 'shout' });
    S.unpose(k, { y: 172 });
    S.letterbox(false);
    S.hint('在事务所里看看，再和神乐聊聊', 6);
    F().ate = true;
  }
  async function talkKaguraOffice(S, a) {
    if (!F().ate) return;
    const n = count('kagOffice');
    if (n === 1) {
      await S.say('kagura', '我是来地球打工赚钱的。结果被那帮人骗去当打手了阿鲁。', { actor: a, expr: 'sad' });
      await S.say('gintoki', '所以你就跑出来了。');
      await S.say('kagura', '嗯。我想回家……可是没有路费阿鲁。', { actor: a, expr: 'sad' });
      await S.say('gintoki', '……那就先在这儿住下吧。房租从你的饭钱里扣——');
      await S.say('shinpachi', '她的饭钱比房租还贵吧！', { expr: 'shout' });
      await S.say('kagura', '那就这么说定了阿鲁！', { actor: a, expr: 'happy' });
      F().stay = true;
      S.hint('天已经很晚了。到沙发那边睡一觉吧', 6);
    } else if (n === 2) {
      await S.say('kagura', '这里的沙发，比黑道那边的床软多了阿鲁。', { actor: a });
    } else await S.say('kagura', '醋昆布……明天要去买醋昆布阿鲁……', { actor: a, expr: 'sleep' });
  }
  async function talkShinOffice(S, a) {
    if (count('shinOffice') === 1) {
      await S.say('shinpachi', '银时先生……您该不会真打算让她住下吧？', { actor: a, expr: 'sad' });
      await S.say('gintoki', '外面那么多黑道在找她。总不能把一个小丫头扔到大街上。');
      await S.say('shinpachi', '……有时候，您还真像个好人。', { actor: a });
    } else await S.say('shinpachi', '明天开始，饭要煮三倍了……', { actor: a, expr: 'gloom' });
  }
  const OFFICE_HOT = [
    { id: 'umbrella', x: 318, y: 172, r: 14, ry: 12, label: '雨伞', ly: 118,
      use: async (S) => {
        await S.say(null, '神乐的雨伞靠在墙边。银时想拎起来——');
        S.sfx('thud', 0.7);
        await S.say('gintoki', '……重得不像话。这是伞还是铁块。');
      } },
    { id: 'jump', x: 262, y: 168, r: 12, ry: 10, label: 'Jump', ly: 114,
      use: async (S) => {
        await S.say(null, '今天刚买的 Jump。封面上有好几个被子弹打穿的洞。');
        await S.say('gintoki', '……我的周一。');
      } },
    { id: 'tv', x: 36, y: 172, r: 22, ry: 16, label: '电视', ly: 96,
      use: async (S) => { await S.say(null, '深夜的电视在放通宵电影。'); await S.say('gintoki', '……结野主播的节目要明早才有。'); } },
    { id: 'window', x: 192, y: 166, r: 14, ry: 10, label: '窗外', ly: 40,
      use: async (S) => { await S.say(null, '窗外的歌舞伎町还亮着灯。今晚的月亮很圆。'); } },
    { id: 'sofa', x: 90, y: 170, r: 26, ry: 14, label: '沙发', ly: 120,
      use: async (S) => {
        if (!F().stay) { await S.say('gintoki', '还不能睡。……这丫头的事，得先问清楚。'); return; }
        await sleepNight(S);
      } },
  ];
  async function sleepNight(S) {
    const p = S.player;
    S.letterbox(true);
    await S.walk(p, 90, 151, { speed: 50 });
    S.pose(p, 'sleep', { y: 151 });
    await S.wait(0.6);
    await S.say('gintoki', '……呼……', { expr: 'sleep' });
    await S.fadeOut(1.0);
    F().night = true;
  }

  // ================================================================ 第二天：「请收养」纸箱、定春
  async function morning(S) {
    const p = S.player;
    await S.narrate('——第二天。', { onBlack: true, auto: 1.4 });
    await S.setStage('street_ch3', { x: 400, y: 182, facing: 1, fade: false });
    S.unpose(p, { y: 182 });          // 昨晚睡沙发的姿势还在（hold），不解开就走不了
    const k = S.actor('kagura'), s = S.actor('shinpachi');
    await S.fadeIn(0.6);
    await S.say('kagura', '银酱！楼下有个奇怪的箱子阿鲁！', { actor: k, expr: 'happy' });
    await S.say('gintoki', '……银酱？谁准你这么叫了。');
    S.hint('看看甘味处门口的纸箱', 5);
    F().morning = true;
  }
  async function openBox(S) {
    const p = S.player, sp = SP(), st = G.world.stage;
    const k = S.actor('kagura'), s = S.actor('shinpachi');
    const box = st.props.find((q) => q.id === 'box');
    S.letterbox(true);
    await S.say(null, '纸箱上写着「请收养」。里面有什么东西在动。');
    await S.say('shinpachi', '是小狗吗？', { actor: s });
    S.sfx('squeak', 0.6);
    // 箱子晃了几下，然后——
    await S.animate(0.9, (t) => { box.x = box.x0 + Math.round(Math.sin(t * 40) * (t < 0.8 ? 1 : 0)); });
    S.sfx('boing', 0.8);
    S.shake(3, 0.3);
    const d = S.spawn('sadaharu', box.x0, box.y0 + 2, { id: 'sadaharu', name: '定春', facing: -1 });
    d.z = 30;
    S.arc(d, box.x0 - 10, box.y0 + 4, 30, 0.5, { anim: 'jump', z1: 0 }).then(() => S.unpose(d));
    box.image = sp.box_open.image;
    await S.wait(0.6);
    S.sfx('bark', 0.9);
    S.emote(p, '!!', 0.6, '#fff');
    await S.say('gintoki', '……这哪里是小狗。这是怪兽吧。');
    S.nameCard('sadaharu');
    await S.say('kagura', '好可爱阿鲁！', { actor: k, expr: 'happy' });
    // 伸手去摸：「乖～」……一口咬住银时的头
    await S.walk(p, d.x + 30, d.y, { speed: 50 });
    p.facing = -1;
    G.fx.word('乖～', p.x, p.y - 40, 0.9);
    await S.wait(0.6);
    S.emote(d, '!', 0.4, '#ff6060');
    S.sfx('chomp', 1.0); S.sfx('punch_big', 0.6);
    G.fx.word('咔嚓!!', p.x, p.y - 46, 1.2);
    S.shake(4, 0.4);
    S.flash(0.05, 0.55);
    p.visible = false; d.visible = false;   // 狗 + 被叼着乱晃的银时 + 上颚，三层画在一起（原片的叠法）
    const bx = d.x, by = d.y, t0 = G.world.stage.t;
    const bite = S.prop({ type: 'custom', x: bx, y: by, depth: by, draw: (g, x, y, t) => {
      const dt = t - t0, f = Math.floor(dt * 12);
      const dog = G.atlas('sadaharu'), head = G.atlas('sadaharu__bitehead'), gin = G.atlas('gintoki__s03');
      const tilt = (22 + 2.5 * Math.sin(11 * dt)) * Math.PI / 180;   // 狗朝左，叼起来往后仰
      g.save();
      g.translate(x + 14, y - 1); g.rotate(tilt); g.translate(-(x + 14), -(y - 1));
      dog.draw(g, 'bite_loop', f % dog.anim('bite_loop').frames, x, y, { flip: true });
      // 被叼着的银时：脚 = 嘴 + (8.5·sin θ, 13 + 8.5·cos θ)，绕脚上方 14 px 转（原片 s03 的算法）
      const th = (-40 + 10 * Math.sin(13 * dt)) * Math.PI / 180;
      const mx = x - 22, my = y - 27;
      const fx = mx + 8.5 * Math.sin(th), fy = my + 13 + 8.5 * Math.cos(th);
      g.save(); g.translate(fx, fy - 14); g.rotate(-th);
      gin.draw(g, 'dangle', f % gin.anim('dangle').frames, 0, 14, { flip: true });
      g.restore();
      head.draw(g, 'bite_loop_head', f % head.anim('bite_loop_head').frames, x, y, { flip: true });
      g.restore();
    } });
    S.letterbox(false);
    let ok = await S.mash({ label: '被定春咬住了！连按 J 挣脱！', need: 16, time: 4.5, decay: 2.2 });
    if (!ok) {
      G.fx.word('嚼', bx - 20, by - 50, 0.6);
      S.sfx('chomp', 0.75);
      await S.say(null, '越挣扎，咬得越紧。');
      ok = await S.mash({ label: '再来！连按 J！', need: 12, time: 5, decay: 1.8 });
    }
    S.unprop(bite);
    p.visible = true; d.visible = true;
    p.x = bx - 30; p.y = by + 2;
    S.unpose(d);
    S.sfx('pop', 0.8);
    await S.arc(p, p.x - 20, p.y + 4, 16, 0.4, { anim: 'fly' });
    S.unpose(p);
    S.letterbox(true);
    await S.say('gintoki', '……头……我的头还在吗……', { expr: 'hurt' });
    await S.say('shinpachi', '还在！只是有点湿！', { actor: s, expr: 'shock' });
    await S.say('kagura', '它很喜欢银酱阿鲁！就叫你「定春」阿鲁！', { actor: k, expr: 'happy' });
    await S.say('gintoki', '谁说要养了！！万事屋没钱养这么大的狗！', { expr: 'shout' });
    await S.say('kagura', '定春吃得不多阿鲁。……大概跟我差不多。', { actor: k });
    await S.say('shinpachi', '那就是很多啊！', { actor: s, expr: 'shout' });
    S.letterbox(false);
    await balcony(S);
  }

  // ================================================================ 阳台：「万事屋，集结！」
  async function balcony(S) {
    const p = S.player;
    await S.fadeOut(0.6);
    await S.setStage('yorozuya_front_ch3', { x: G.D.bg.front_dusk.camX + 200, y: 120, facing: -1, fade: false });
    const k = S.actor('kagura'), s = S.actor('shinpachi'), d = S.actor('sadaharu');
    S.letterbox(true);
    S.music('comedy', 0.5);
    await S.fadeIn(0.6);
    await S.say('shinpachi', '……就这样，万事屋多了一个大胃王和一条巨型犬。', { actor: s, expr: 'sad' });
    await S.say('gintoki', '还有一个吐槽眼镜。');
    await S.say('shinpachi', '请不要把我算成附赠品！', { actor: s, expr: 'shout' });
    S.pose(k, 'umbrella_open', { restart: true });
    S.pose(p, 'shoulder');
    S.sfx('shing', 0.8);
    G.fx.speedLines(192, 100, { count: 40, inner: 90, life: 2.2, color: 'rgba(255,240,200,0.9)' });
    const tx = G.D.ui.texts.yorozuya_assemble;
    const t0 = G.world.stage.t;
    S.prop({ type: 'custom', x: 192, y: 62, depth: 999, draw: (g, x, y, t) => {    // 横幅放在天上（下面会被对话框挡住）
      const im = G.image(tx.image);
      g.fillStyle = 'rgb(214,40,48)'; g.fillRect(0, y - 26, G.W, 26);
      const k2 = Math.min(1, (t - t0) * 3);
      g.drawImage(im, Math.round(G.W / 2 - im.width / 2 + (1 - k2) * 200), y - 13 - Math.round(im.height / 2));
    } });
    S.sfx('fanfare', 0.8);
    await S.wait(2.4);
    await S.say('kagura', '万事屋，集结阿鲁！', { actor: k, expr: 'happy' });
    S.sfx('chomp', 0.8);
    G.fx.word('咔嚓', p.x, p.y - 44, 1.0);
    S.emote(p, '!!', 0.6);
    await S.say('gintoki', '……定春，不要在这种时候咬我的头。', { expr: 'hurt' });
    await S.fadeOut(1.2);
    F().ch3Done = true;
  }

  // ================================================================ 地图（第三章版）：进这一章时才建（要用到导出的素材）
  function defineStages() {
    const sp = SP();
    G.STAGES.street_night = { id: 'street_night', bg: 'street_night', x0: 0, x1: 1150, yMin: 162, yMax: 198, music: 'comedy', props: [] };
    G.STAGES.street_night_ch3 = Object.assign({}, G.STAGES.street_night, { id: 'street_night_ch3' });
    G.STAGES.office_night_ch3 = Object.assign({}, G.STAGES.office, {
      id: 'office_night_ch3', bg: 'office_night', music: 'yorozuya',
      props: [{ type: 'image', image: G.D.bg.office_night.fg, screen: true, x: 0, y: 0, depth: 167 },
        { type: 'image', image: sp.umbrella.image, x: 318, y: 162, ax: sp.umbrella.w >> 1, ay: sp.umbrella.h, depth: 162 }],   // 神乐靠在墙边的伞
      npcs: [
        { cid: 'shinpachi', id: 'shinpachi', x: 250, y: 176, facing: -1, label: '新八', talk: talkShinOffice },
      ],
      hotspots: OFFICE_HOT,
    });
    G.STAGES.street_ch3 = Object.assign({}, G.STAGES.street, {
      id: 'street_ch3', music: 'comedy',
      props: [{ id: 'box', type: 'sprite', image: sp.box.image, x: 508, y: 176, x0: 508, y0: 176, ax: -sp.box.ox, ay: -sp.box.oy, depth: 176 }],
      npcs: [
        { cid: 'kagura', id: 'kagura', x: 470, y: 178, facing: -1, label: '神乐', talk: async (S, a) => { await S.say('kagura', '箱子里有东西在动阿鲁！', { actor: a }); } },
        { cid: 'shinpachi', id: 'shinpachi', x: 372, y: 186, facing: 1, label: '新八', talk: async (S, a) => { await S.say('shinpachi', '大清早的，这箱子是谁放在这儿的……', { actor: a }); } },
      ],
      hotspots: [{ id: 'box', x: 508, y: 178, r: 16, ry: 12, label: '纸箱', ly: 132, cond: () => F().morning && !F().box, use: async (S) => { F().box = true; await openBox(S); } }],
    });
    // 万事屋门口（黄昏）：镜头固定在 front_dusk.camX，人站在二楼阳台（脚 y = 120）
    const fx = G.D.bg.front_dusk.camX;
    G.STAGES.yorozuya_front_ch3 = { id: 'yorozuya_front_ch3', bg: 'front_dusk', x0: fx, x1: fx + 384, camX: fx, yMin: 112, yMax: 124, music: 'comedy', props: [],
      npcs: [
        { cid: 'shinpachi', id: 'shinpachi', x: fx + 136, y: 120, facing: 1 },
        { cid: 'kagura', id: 'kagura', x: fx + 162, y: 120, facing: 1 },
        { cid: 'sadaharu', id: 'sadaharu', x: fx + 244, y: 120, facing: -1 },
      ] };
  }

  // ================================================================ 第三章主流程
  G.STORY.chapter3 = async function (S) {
    defineStages();
    G.fadeAlpha = 0;
    G.world.stage = null;
    await S.chapterCard('ch3');
    const p = new G.Actor('gintoki', 90, 178, { id: 'player', team: 'player', hp: 100, speed: 72, name: '银时' });
    G.world.player = p;
    G.fadeAlpha = 1;
    await S.setStage('street_night_ch3', { x: 90, y: 178, facing: 1 });
    await S.run(async (S) => {
      gearUp(p);
      p.ride = scooterRide();
      S.pose(p, 'scooter_nosepick');
      S.letterbox(true);
      await S.say('gintoki', '（周一的夜晚。新一期 Jump 到手了。）');
      await S.say('gintoki', '（再顺路买瓶草莓牛奶……人生就圆满了。）');
      S.letterbox(false);
      S.unpose(p);
      await nightRide(S);
      const bike = await crash(S);
      await meetKagura(S);
      await dodgeKagura(S);
      await yakuzaFight(S);
      S.unprop(bike);
      const k = S.actor('kagura');
      S.letterbox(true);
      S.face(k, p);
      S.sfx('boing', 0.5, 0.6);
      await S.say('kagura', '……咕噜噜。', { actor: k, expr: 'sad' });
      await S.say('kagura', '打完架，肚子饿了阿鲁。', { actor: k, expr: 'sad' });
      await S.say('gintoki', '……先跟我回事务所再说。');
      await S.fadeOut(0.6);
      await S.setStage('office_night_ch3', { x: 300, y: 176, carry: [k], facing: -1, fade: false });
      G.world.stage.door = 0;
      k.talk = talkKaguraOffice; k.label = '神乐';
      await S.fadeIn(0.5);
      await officeNight(S);
    });
    await S.until(() => G.flags.night);
    await S.run(async (S) => { await morning(S); });
    await S.until(() => G.flags.ch3Done);
  };
})();
