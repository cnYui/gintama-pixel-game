// 第二章：新八登场（原片 s02）
//   家庭餐厅：拿过期优惠券点芭菲 → 芭菲被天人打翻（乌鸦「阿～呆～」、死鱼眼变认真）→ 大打出手，猪头被打穿墙
//   → 店长当场开除新八（托盘落地、石化）→「你给我等一下！！」→ 弹鼻屎 → 新八脱下围裙跟了出来
//   → 歌舞伎町：新八一路跟着，讲道场的债；街坊换了新台词
//   → 黄昏的志村道场门口：讨债的 + 借条解谜（利息每日三成）→ 和新八一起打 → 阿妙一拳收尾
//   → 道场里：阿妙的「煎蛋」（吃 / 不吃都一样）→ 银时倒下、灵魂出窍 →「我要跟着这个人，找回我的武士道！」
'use strict';
(function () {
  const G = window.G;
  const F = () => G.flags;
  const count = (key) => (G.flags[key] = (G.flags[key] || 0) + 1);
  const SP = () => G.D.bg.ch2;          // 第二章的小道具和特写（tools/build_assets.py 的 build_bg_ch2 导出）
  const R = () => G.D.bg.restaurant;    // 餐厅布景的坐标：凳子、吧台、墙洞、厨房门……

  // ================================================================ 小特效
  const sweat = (a, dx = 7, dy = 4) => G.fx.img(SP().sweat.image, a.x + dx, a.headY() + dy, { vy: 7, life: 0.9, fade: true });
  const vein = (a, dx = -5, life = 1.4) => G.fx.img(SP().vein.image, a.x + dx, a.headY() + 3, { life, pulse: true });
  const hearts = (x, y) => {
    for (let i = 0; i < 3; i++) G.fx.img(SP().heart.image, x - 5 + i * 5, y, { vx: (i - 1) * 3, vy: -15 - i * 3, life: 1.0 + i * 0.2, fade: true });
  };
  const aura = (a) => G.fx.debris(a.x, a.y - 22, ['rgb(150,80,180)', 'rgb(84,40,110)'], 12, [20, 60], -40, 0.5);
  const sparkle = (x, y, size = 7, color = '#fff') => G.fx.twinkle(x, y, size, color, 0.5);

  // 集中线（原片 fx.speed_lines），画在特写里
  function speedLinesAt(g, t, cx, cy, color, n, inner, seed) {
    const rnd = G.prng(seed + Math.floor(t * 15));
    const R2 = 460;
    g.fillStyle = color;
    g.beginPath();
    for (let i = 0; i < n; i++) {
      const a = rnd() * Math.PI * 2, ri = inner + rnd() * 40, w = (0.012 + rnd() * 0.018) * 2;
      g.moveTo(cx + Math.cos(a) * ri, cy + Math.sin(a) * ri);
      g.lineTo(cx + Math.cos(a - w) * R2, cy + Math.sin(a - w) * R2);
      g.lineTo(cx + Math.cos(a + w) * R2, cy + Math.sin(a + w) * R2);
      g.closePath();
    }
    g.fill();
  }

  // ================================================================ 特写
  // 银时的眼睛（原片镜头 D）：死鱼眼 →（锵！）认真的眼神。e = { serious, snap }
  function eyesInsert(e) {
    const rnd = G.prng(7);
    const lines = Array.from({ length: 20 }, (_, i) => ({
      y: i < 10 ? 6 + rnd() * 56 : 154 + rnd() * 56, L: 20 + rnd() * 50, x0: rnd() * 500, f: 0.7 + rnd() * 0.6, dir: i < 10 ? -1 : 1,
    }));
    return (g, t) => {
      const sp = SP();
      g.fillStyle = 'rgb(8,6,14)'; g.fillRect(0, 0, G.W, G.H);
      const band = G.image(e.serious ? sp.eyes_hot : sp.eyes_dead);
      const drift = Math.round(G.lerp(-6, 6, Math.min(1, t / 1.05)));
      const since = e.serious ? t - e.snap : -1;
      let dx = 0, dy = 0;
      if (since >= 0 && since < 0.25) { dx = Math.round(G.rand(-2, 2)); dy = Math.round(G.rand(-1, 1)); }
      const by = 68;
      if (e.serious) {   // 上下黑边里的红色速度线
        g.fillStyle = 'rgb(120,30,40)';
        for (const l of lines) {
          const span = G.W + l.L + 40;
          let x = G.mod(l.x0 + t * 700 * l.f, span) - l.L;
          if (l.dir < 0) x = G.W - x;
          g.fillRect(Math.round(x), Math.round(l.y), Math.round(l.L), 1);
        }
      }
      if (G.ready(band)) g.drawImage(band, drift + dx, by + dy);
      if (since >= 0 && since < 0.45) {   // 眼睛里一闪
        const s = Math.round(Math.sin((since / 0.45) * Math.PI) * 7);
        g.fillStyle = '#fff';
        for (const ex of [62, 130]) {
          const gx = drift + dx + (ex + (ex > 96 ? 1 : -1)) * 2 + (ex > 96 ? 4 : -4), gy = by + dy + 42;
          g.fillRect(gx - s, gy, 2 * s + 1, 1); g.fillRect(gx, gy - s, 1, 2 * s + 1);
        }
      }
      g.fillStyle = 'rgb(200,190,210)';
      g.fillRect(0, by - 2, G.W, 1); g.fillRect(0, by + 81, G.W, 1);
    };
  }

  // 阿妙的「煎蛋」（原片镜头 H 的插入画面）：冒泡、冒紫烟、骷髅、「※本品为煎蛋」
  function eggInsert(g, t) {
    const sp = SP();
    g.drawImage(G.image(sp.egg_bg), 0, 0);
    speedLinesAt(g, t, 192, 112, 'rgb(118,64,146)', 34, 96, 70);
    const [cx, cy] = sp.plate;
    const ey = cy + 2 + Math.round(Math.sin(t * 5 * 2 * Math.PI));
    [[cx - 22, 0], [cx + 2, 0.4], [cx + 24, 0.8]].forEach(([bx, ph], c) => {
      for (let i = 0; i < 12; i++) {
        const y = ey - 30 - i * 3.5 - ((t * 30) % 3.5);
        if (y < 76) break;
        const x = bx + Math.sin(y * 0.12 - t * 8 + ph * 6) * (2 + i * 0.6);
        const sz = i < 6 ? 4 : 3;
        g.fillStyle = (i + c + Math.floor(t * 12)) % 3 ? 'rgb(196,120,236)' : 'rgb(120,56,160)';
        g.fillRect(Math.floor(x) - (sz >> 1), Math.floor(y), sz, sz);
      }
    });
    const sk = G.image(sp.skull.image), egg = G.image(sp.egg_big.image);
    const k = Math.min(1, t / 0.56);
    g.drawImage(sk, Math.round(cx - 46 + Math.sin(t * 1.3 * 2 * Math.PI) * 3 - sk.width / 2), Math.round(100 - k * 8 + Math.sin(t * 2.1 * 2 * Math.PI) * 2 - sk.height / 2));
    g.drawImage(egg, Math.round(cx - egg.width / 2), ey - egg.height);
    const rnd = G.prng(5);
    for (let i = 0; i < 5; i++) {   // 硬壳上的气泡，鼓起来、破掉
      const bx = cx + Math.floor(rnd() * 56 - 28), by = ey - Math.floor(10 + rnd() * 20), sp_ = 2.2 + rnd(), off = rnd();
      const ph = G.mod(t * sp_ + off, 1);
      if (ph < 0.8) {
        const rr = Math.round(1 + ph * 4);
        g.fillStyle = 'rgb(170,80,214)'; g.fillRect(bx - rr, by - rr, 2 * rr + 1, 2 * rr + 1);
        g.fillStyle = 'rgb(60,40,70)'; g.fillRect(bx - rr + 1, by - rr + 1, 2 * rr - 1, 2 * rr - 1);
      } else if (ph < 0.95) {
        g.fillStyle = 'rgb(190,120,230)';
        for (const [dx, dy] of [[-4, -2], [4, -2], [0, -5], [-3, 2], [3, 2]]) g.fillRect(bx + dx, by + dy, 1, 1);
      }
    }
    G.f12.draw(g, '※本品为煎蛋', 14, 22, 'rgb(255,236,150)', { outline: '#140c18' });
    const vg = g.createRadialGradient(192, 108, 110, 192, 108, 250);
    vg.addColorStop(0, 'rgba(0,0,0,0)');
    vg.addColorStop(1, 'rgba(0,0,0,0.45)');
    g.fillStyle = vg; g.fillRect(0, 0, G.W, G.H);
  }

  // ================================================================ 家庭餐厅：点单
  async function talkWaiter(S, a) {
    if (F().ordered) { await S.say('shinpachi', '芭菲马上就好！请到吧台坐一下！', { name: '服务员', actor: a }); return; }
    S.pose(a, 'waiter');
    await S.say('shinpachi', '欢、欢迎光临！请问一位吗？', { name: '服务员', actor: a });
    await S.say('gintoki', '一位。巧克力芭菲，要最大的那种。还有——用这个。');
    S.sfx('pop', 0.6);
    await S.say(null, '银时掏出一张皱巴巴的优惠券。万事屋办公桌抽屉里翻出来的那张。');
    sweat(a);
    await S.say('shinpachi', '这是……隔壁甜品店的优惠券？而且上个月就过期了……', { name: '服务员', actor: a, expr: 'shock' });
    await S.say('gintoki', '眼镜，你知道吗？甜品是不会过期的。过期的，只是纸。');
    await S.say('shinpachi', '这是什么歪理啊！', { name: '服务员', actor: a, expr: 'shout' });
    await S.say('shinpachi', '……算了。我用员工折扣帮您垫上吧。请到吧台坐一下，马上就好。', { name: '服务员', actor: a, expr: 'sad' });
    F().ordered = true;
    // 端着托盘回厨房
    S.door(true);
    await S.walk(a, R().door[0] + 22, 166, { anim: 'waiter_walk', speed: 64 });
    a.visible = false;
    a.talk = null;
    S.door(false);
    S.hint('去吧台中间那张空凳子坐下', 5);
  }
  async function talkPigA(S, a) {
    if (count('pigA') === 1) {
      await S.say('amanto_pig', '看什么看，地球猴子。', { name: '天人客人', actor: a });
      await S.say('gintoki', '看你的啤酒杯。上面的指纹比啤酒还多。');
      await S.say('amanto_pig', '你说什么！？', { name: '天人客人', actor: a, expr: 'angry' });
    } else await S.say('amanto_pig', '哼，地球的菜，跟地球人一样没味道。', { name: '天人客人', actor: a });
  }
  async function talkPigB(S, a) {
    if (count('pigB') === 1) {
      await S.say('amanto_pig', '这家店的服务员，又慢又笨。戴着眼镜，连菜单都看不清吗？', { name: '猪头客人', actor: a });
      await S.say('gintoki', '……这跟眼镜有什么关系。');
      await S.say('amanto_pig', '有关系！戴眼镜的都是笨蛋！', { name: '猪头客人', actor: a, expr: 'shout' });
    } else await S.say('amanto_pig', '滚远点，天然卷。看着就热。', { name: '猪头客人', actor: a });
  }
  async function talkCat(S, a) {
    if (count('catA') === 1) {
      await S.say('amanto_cat', '这里的鱼，是冷冻的喵。', { name: '天人客人', actor: a });
      await S.say('gintoki', '家庭餐厅的鱼，本来就是冷冻的。');
      await S.say('amanto_cat', '……地球真是个悲哀的星球喵。', { name: '天人客人', actor: a, expr: 'sad' });
    } else await S.say('amanto_cat', '地球人连吃个饭都这么吵喵。', { name: '天人客人', actor: a });
  }

  const REST_HOT = [
    { id: 'kitchen', x: 40, y: 168, r: 18, ry: 12, label: '厨房门', ly: 66,
      use: async (S) => {
        if (!F().ordered) { await S.say(null, '门上挂着「厨房」的牌子。门缝里飘出炸东西的香味。'); return; }
        await S.say(null, '厨房里传来盘子碰撞的声音，还有人在喊：「眼镜！快点！」');
        await S.say('gintoki', '……这家店的人，也都叫他眼镜啊。');
      } },
    { id: 'clock', x: 100, y: 168, r: 12, ry: 12, label: '挂钟', ly: 22,
      use: async (S) => { await S.say(null, '挂钟的秒针走得很认真。'); await S.say('gintoki', '等甜品的时候，时间总是过得特别慢。'); } },
    { id: 'window', x: 188, y: 168, r: 14, ry: 12, label: '窗外', lx: 220, ly: 50,
      use: async (S) => {
        await S.say(null, '窗外是歌舞伎町的大街。窗台上蹲着一只乌鸦，一直盯着这边。');
        await S.say('gintoki', '……干嘛。芭菲不分你。');
      } },
    { id: 'stool', x: 304, y: 166, r: 10, ry: 10, label: '空凳子', ly: 128,
      use: async (S) => {
        if (!F().ordered) { await S.say('gintoki', '先点单。……芭菲又不会自己走过来。'); return; }
        await parfaitScene(S);
      } },
    { id: 'poster', x: 356, y: 170, r: 9, ry: 12, label: '海报', lx: 332, ly: 18,
      use: async (S) => {
        await S.say(null, '海报：「本日推荐　巧克力芭菲」。画上的芭菲闪闪发光。');
        await S.say('gintoki', '广告上的芭菲，永远比实物大一圈。……没关系，我原谅它。');
      } },
    { id: 'plant', x: 374, y: 180, r: 10, ry: 14, label: '盆栽', ly: 90,
      use: async (S) => { await S.say(null, '塑料做的观叶植物。'); await S.say('gintoki', '……比事务所那盆有精神。'); } },
  ];

  // ================================================================ 家庭餐厅：芭菲惨案（原片镜头 A–E）
  async function parfaitScene(S) {
    const p = S.player, st = G.world.stage, rs = R(), sp = SP();
    const pigA = S.actor('pigA'), pigB = S.actor('pigB'), cat = S.actor('catA'), shin = S.actor('shinpachi');
    const GIN_X = rs.stools[1];
    S.letterbox(true);
    await S.walk(p, GIN_X, 166, { speed: 60 });
    S.pose(p, 'sit', { y: rs.seat_y });
    p.facing = -1;
    await S.wait(0.4);
    // 新八端着芭菲从厨房出来
    S.door(true);
    S.sfx('door', 0.45);
    await S.wait(0.35);
    Object.assign(shin, { visible: true, x: rs.door[0] + 22, y: 166, facing: 1 });
    S.sfx('footsteps', 0.35);
    await S.walk(shin, 268, 178, { anim: 'waiter_walk', speed: 96 });
    S.door(false);
    S.pose(shin, 'waiter');
    shin.facing = 1;
    await S.say('shinpachi', '久等了！巧克力芭菲！', { name: '服务员', actor: shin, expr: 'happy' });
    const ph = sp.parfait.h;
    const parfait = S.prop({ image: sp.parfait.image, x: rs.parfait[0], y: rs.parfait[1] + 1 - ph / 2, ay: ph / 2, depth: rs.parfait[1] });
    S.sfx('pop', 0.5);
    await S.walk(shin, 192, 168, { anim: 'waiter_walk', speed: 70 });
    S.pose(shin, 'waiter');
    shin.facing = 1;
    // 人生的意义，全在这一杯里
    hearts(p.x - 2, p.y - 30);
    S.sfx('sparkle', 0.5);
    await S.say('gintoki', '（来了……巧克力、香草、玉米片、草莓。人生的意义，全在这一杯里。）', { expr: 'happy' });
    hearts(p.x - 2, p.y - 30);
    // 猪头跺脚：「地球猴子！上菜慢死了！」
    S.face(pigB, shin);
    await S.say('amanto_pig', '喂，眼镜！我们的菜呢！', { name: '猪头客人', actor: pigB });
    S.pose(pigB, 'bully', { restart: true });
    S.sfx('thud', 0.9); S.sfx('vein', 0.7); S.shake(3, 0.25);
    G.fx.word('咚!', pigB.x - 22, pigB.y - 40);
    G.fx.dust(pigB.x - 4, pigB.y, 6);
    vein(pigB, -4);
    sweat(shin);
    await S.say('amanto_pig', '地球猴子！上菜慢死了！', { name: '猪头客人', actor: pigB, expr: 'shout' });
    sweat(shin);
    await S.say('shinpachi', '对、对不起！马上就……！', { name: '服务员', actor: shin, expr: 'shock' });
    // 猪头转过来嘲笑银时，一拳砸在吧台上
    S.pose(pigB, 'laugh');
    pigB.facing = 1;
    await S.say('amanto_pig', '噗哈哈！你们看，一个大男人在吃芭菲！', { name: '猪头客人', actor: pigB, expr: 'smug' });
    await S.say('gintoki', '……吵死了。冰淇淋会化的。');
    await S.say('amanto_pig', '你说什么！？', { name: '猪头客人', actor: pigB, expr: 'angry' });
    S.sfx('whoosh', 0.6);
    S.pose(pigB, 'punch', { restart: true });
    await S.wait(0.18);
    S.sfx('thud', 0.8); S.sfx('hit', 0.4, 1.3); S.sfx('slide_up', 0.35);
    G.fx.word('咚!', pigB.x - 16, rs.counter_top - 22);
    G.fx.spark(pigB.x + 11, rs.counter_top + 2, '#fff0b4', 8);
    S.shake(2, 0.15);
    S.emote(p, '！', 0.6, '#fff');
    // 芭菲慢动作飞出去（原片 _parfait_flight：先蹦一下、在最高点慢动作、再猛地掉下来）
    const x0 = parfait.x, y0 = parfait.y, x1 = rs.splat[0], y1 = rs.splat[1] - 6;
    parfait.depth = 400;
    const FL = Array.from({ length: 5 }, (_, i) => { const r = G.prng(21 + i); return [r() * 18 - 9, r() * 14 - 10, r() * 12 - 6, 2 + r() * 4]; });
    const flecks = S.prop({ type: 'rects', x: x0, y: y0, depth: 401, rects: [] });
    await S.animate(0.57, (k) => {
      const u = k < 0.2 ? 0.3 * G.ease.out(k / 0.2) : k < 0.74 ? 0.3 + (0.12 * (k - 0.2)) / 0.54 : 0.42 + 0.58 * G.ease.in((k - 0.74) / 0.26);
      parfait.x = G.lerp(x0, x1, u);
      parfait.y = G.lerp(y0, y1, u) - 4 * 22 * u * (1 - u);
      parfait.rot = (Math.floor(u * 14) * 20 * Math.PI) / 180;
      flecks.x = parfait.x; flecks.y = parfait.y;
      flecks.rects = k > 0.18 && k < 0.8
        ? FL.map(([fx, fy, vx, vy], i) => [Math.round(fx + (k - 0.2) * vx), Math.round(fy - (k - 0.2) * vy), 1, 1, i % 3 ? 'rgb(255,248,236)' : 'rgb(214,40,56)'])
        : [];
    });
    S.unprop(parfait); S.unprop(flecks);
    S.prop({ type: 'image', image: sp.splat.image, x: sp.splat.x, y: sp.splat.y, ax: 0, ay: 0, depth: 158 });
    S.sfx('glass', 0.9); S.sfx('record_scratch', 0.9);
    S.stopMusic(0.05);
    G.fx.debris(x1, y1 + 4, ['rgb(104,58,40)', 'rgb(255,248,236)', 'rgb(190,222,246)'], 14, [30, 80], 260, 0.45);
    G.fx.word('啪嚓', x1 - 12, y1 - 10);
    S.shake(2, 0.2);
    await S.wait(0.6);
    // 一片死寂：乌鸦从窗外飞过，「阿～」……「呆～」
    const c0 = st.state.crow || { x: 278, y: 96 };
    let caw1 = false, caw2 = false;
    S.sfx('crow', 0.8, 1.3);
    await S.animate(1.3, (k) => {
      const tt = k * 1.3;
      const x = G.lerp(c0.x, 186, k), y = G.lerp(c0.y, 80, k) + Math.sin(tt * 1.6 * 2 * Math.PI) * 2;
      st.state.crow = { frames: [sp.crow0.image, sp.crow1.image], fps: 8, x, y, flip: true };
      if (!caw1 && tt > 0.12) { caw1 = true; G.fx.text('阿～', x + 12, y - 24, { vy: -10, life: 1.1 }); }
      if (!caw2 && tt > 0.72) { caw2 = true; G.fx.text('呆～', x + 12, y - 24, { vy: -10, life: 0.8 }); }
    });
    st.state.crow = null;
    S.emote(p, '…', 1.3, '#fff');
    await S.wait(1.0);
    // 特写：死鱼眼 →（锵！）认真的眼神
    const eyes = { serious: false, snap: 0 };
    S.insert(eyesInsert(eyes));
    S.sfx('sting_dramatic', 0.8);
    await S.wait(0.45);
    eyes.serious = true;
    eyes.snap = G.ui.insert.t;
    S.sfx('shing', 0.9);
    S.flash(0.1, 1);
    await S.wait(0.65);
    S.insert(null);
    // 从凳子上跳下来
    S.sfx('jump', 0.7);
    await S.arc(p, GIN_X - 12, 168, 10, 0.18, { anim: 'jump' });
    S.sfx('land', 0.4);
    S.unpose(p);
    p.facing = -1;
    S.face(pigB, p);
    await S.say('gintoki', '……喂，猪头。', { expr: 'angry' });
    await S.say('amanto_pig', '啊？', { name: '猪头客人', actor: pigB });
    await S.say('gintoki', '你知道一杯芭菲，对一个被医生说是「糖尿病预备军」的男人，意味着什么吗？', { expr: 'angry' });
    await S.say('gintoki', '一个星期，只能吃一杯。……这个星期的那一杯，被你打翻了。', { expr: 'angry' });
    await S.say('amanto_pig', '哈！一杯芭菲而已！兄弟们，把这个天然卷揍扁！', { name: '猪头客人', actor: pigB, expr: 'shout' });
    // 新八端着托盘躲到墙边；坐着的两个天人跳下凳子
    S.walk(shin, 110, 178, { anim: 'waiter_walk', speed: 120 }).then(() => { if (!shin.remove) { S.pose(shin, 'waiter'); shin.facing = 1; } });
    await Promise.all([S.arc(pigA, 220, 168, 6, 0.2, { anim: 'jump' }), S.arc(cat, 342, 174, 6, 0.2, { anim: 'jump' })]);
    S.unpose(pigA); S.unpose(cat);
    S.letterbox(false);
    S.hint('J 攻击（连按三连击）　K 跳跃（空中按 J 跳斩）　按住 L 防御', 7);
    await S.fight({
      arena: [8, 376],
      waves: [
        [{ actor: 'pigA', cid: 'amanto_pig', name: '天人客人', hp: 24 }, { actor: 'catA', cid: 'amanto_cat', name: '天人客人', hp: 22 },
          { cid: 'amanto_cat', id: 'catB', name: '天人客人', hp: 22, side: 'left' }],
        [{ actor: 'pigB', cid: 'amanto_pig', name: '猪头客人', hp: 110, boss: true, scale: 1.25, speed: 42, range: 26,
          moves: ['E_SLASH', 'E_PUNCH', 'E_HEAVY'], koImpact: true,
          koTo: { x: rs.hole[0], y: 166, z: 166 - rs.hole[1] - 16, dur: 0.42 }, onKo: crashThroughWall }],
      ],
      onWave: async (S, i, es, attempt) => {
        if (i !== 1) return;
        await S.say('amanto_pig', '没用的东西！……天然卷，老子亲手送你上天！', { name: '猪头客人', actor: es[0], expr: 'shout' });
        if (attempt === 0) await S.say('gintoki', '上天的是你。芭菲的账，连本带利。', { expr: 'angry' });
        S.hint('大块头的大招前会闪红光、喊「!!」——按住 L 防御，或者跳开', 6);
      },
      after: 'comedy',
    });
    await managerScene(S);
  }

  // 猪头被打穿后墙（原片 8.35 s）：墙上留下猪形的洞，透过洞变成天边的星星
  function crashThroughWall() {
    const rs = R(), st = G.world.stage;
    st.state.hole = true;
    G.audio.sfx('crash', 1.0);
    G.audio.sfx('thud', 0.6);
    G.shake(4, 0.4);
    G.fx.debris(rs.hole[0], rs.hole[1], ['rgb(250,242,222)', 'rgb(200,186,160)', 'rgb(120,100,90)'], 26, [40, 140], 260, 0.9);
    G.fx.dust(rs.hole[0], rs.hole[1] + 12, 10);
    G.fx.word('轰!', rs.hole[0] + 32, rs.hole[1] - 20, 1.0);
    G.wait(0.45).then(() => {
      if (G.world.stage !== st) return;
      G.fx.twinkle(rs.hole[0] + 5, rs.hole[1] - 1, 6, 'rgb(255,214,60)', 0.7);
      G.audio.sfx('twinkle', 0.7);
    });
  }

  // ================================================================ 家庭餐厅：「新八！你被开除了！」（原片镜头 F–G）
  async function managerScene(S) {
    const p = S.player, rs = R(), sp = SP();
    const shin = S.actor('shinpachi');
    S.letterbox(true);
    await S.walk(p, 262, 174, { speed: 60 });
    p.facing = -1;
    S.unpose(shin);
    await S.walk(shin, 192, 168, { anim: 'waiter_walk', speed: 80 });
    S.pose(shin, 'waiter');
    shin.facing = 1;
    sweat(shin);
    await S.say('shinpachi', '墙、墙上……店里的墙被打穿了……！', { name: '服务员', actor: shin, expr: 'shock' });
    // 店长踹开厨房门
    S.door(true, { instant: true });
    S.sfx('door_bang', 1.0);
    S.shake(3, 0.3);
    G.fx.word('砰!', rs.door[0] + 40, rs.door[1] + 6);
    const m = S.spawn('townsman__chef', rs.door[0] + 18, rs.wall_base + 2, { id: 'manager', name: '店长', facing: 1 });
    await S.walk(m, 70, 168, { speed: 110 });
    S.pose(m, 'point', { restart: true });
    m.facing = 1;
    S.sfx('vein', 0.7);
    vein(m, 9);
    shin.facing = -1;
    await S.say('townsman__chef', '新八！你被开除了！', { name: '店长', actor: m, expr: 'angry' });
    // 托盘落地，新八当场石化
    S.sfx('shock', 0.8);
    S.flash(0.08, 0.7, 'rgb(200,200,230)');
    S.pose(shin, 'shock', { freeze: 1 });
    shin.tint = { color: 'rgb(150,150,164)', k: 0.55 };
    G.fx.gloom(shin.x, { life: 1.6 });
    const tray = S.prop({ image: sp.tray.image, x: shin.x - 12, y: shin.y - 16, depth: shin.y + 1 });
    const ty0 = tray.y;
    await S.animate(0.25, (k) => { tray.x = shin.x - 12 - k * 4; tray.y = G.lerp(ty0, shin.y + 2, G.ease.in(k)); tray.rot = (25 * k * Math.PI) / 180; });
    tray.rot = 0;
    S.sfx('clang', 0.7); S.sfx('glass', 0.4, 1.3);
    G.fx.word('哐啷', shin.x - 30, shin.y - 6);
    G.fx.debris(tray.x, shin.y, ['rgb(190,222,246)', '#fff'], 10, [30, 70], 240, 0.4);
    await S.animate(0.2, (k) => { tray.y = shin.y + 2 - Math.sin(k * Math.PI) * 3; });
    S.sfx('clang', 0.3, 1.25);
    G.fx.word('咔嚓', shin.x + 22, shin.y - 40, 1.2);
    S.nameCard('shinpachi');
    await S.wait(1.2);
    await S.say('townsman__chef', '墙上的洞、地上的芭菲，全都从你的工资里扣！', { name: '店长', actor: m, expr: 'shout' });
    await S.say(null, '……新八一动不动。');
    S.unpose(m);
    await S.walk(m, rs.door[0] + 18, rs.wall_base + 2, { speed: 90 });
    S.remove(m);
    S.door(false);
    // 银时挖着鼻孔要走
    await S.walk(p, 330, 170, { speed: 48 });
    S.pose(p, 'nosepick');
    p.facing = -1;
    G.fx.word('抠…抠…', p.x, p.y - 42);
    await S.say('gintoki', '那么，我先走了。芭菲钱……就算了。');
    // 吐槽！
    S.unprop(tray);
    shin.tint = null;
    S.pose(shin, 'point', { restart: true });
    shin.facing = 1;
    S.sfx('slap', 1.0); S.sfx('shock', 0.5);
    G.fx.speedLines(Math.round(shin.x + 4), Math.round(shin.y - 24), { count: 46, inner: 70, life: 0.8 });
    G.fx.word('喂!!', 70, 104, 1.4);
    S.shake(4, 0.3);
    await S.say('shinpachi', '你给我等一下！！', { actor: shin, expr: 'shout' });
    S.emote(p, '？', 0.7, '#fff');
    await S.wait(0.6);
    // 弹鼻屎，正中眼镜
    S.sfx('pop', 0.6);
    const bx0 = p.x - 5, by0 = p.y - 26, bx1 = shin.x + 8, by1 = shin.y - 24;
    const booger = S.prop({ type: 'rects', x: bx0, y: by0, depth: 400, rects: [[-1, -1, 3, 3, '#140c18'], [0, 0, 1, 1, 'rgb(178,200,110)']] });
    await S.animate(0.26, (k) => { booger.x = G.lerp(bx0, bx1, k); booger.y = G.lerp(by0, by1, k) - 40 * k * (1 - k); });
    S.sfx('slap', 0.45, 1.6);
    S.sfx('vein', 0.6);
    G.fx.word('啪', shin.x + 22, shin.y - 40);
    vein(shin, 12);
    await S.wait(0.4);
    S.unpose(p);
    p.facing = -1;
    await S.say('shinpachi', '你、你、你……！我被开除了啊！这都是你害的！', { actor: shin, expr: 'angry' });
    S.unprop(booger);
    await S.say('gintoki', '是那头猪先动的手。');
    await S.say('shinpachi', '把墙打穿的是你吧！', { actor: shin, expr: 'shout' });
    await S.say('gintoki', '墙没事。它现在通风了。');
    await S.say('shinpachi', '这是什么歪理啊！', { actor: shin, expr: 'shout' });
    S.unpose(shin);
    await S.say('shinpachi', '……算了。反正已经被开除了。这身围裙，我不穿了！', { actor: shin, expr: 'angry' });
    // 换成便服的新八
    S.sfx('whoosh', 0.6);
    G.fx.dust(shin.x, shin.y, 10);
    const s2 = new G.Actor('shinpachi', shin.x, shin.y, { id: 'shinpachi', name: '新八', label: '新八', facing: 1, talk: talkShinStreet });
    shin.remove = true;
    G.world.stage.add(s2);
    await S.say('shinpachi', '喂，天然卷！你砸了我的饭碗，就得负责！', { actor: s2, expr: 'angry' });
    await S.say('gintoki', '负责？我可是万事屋。什么活都接——只要给钱。');
    await S.say('shinpachi', '我刚被开除，哪来的钱啊！', { actor: s2, expr: 'shout' });
    await S.say('gintoki', '……那就记账。');
    await S.say('shinpachi', '记账也要有个限度吧！', { actor: s2, expr: 'shout' });
    F().restaurantDone = true;
    // 走出餐厅，新八跟在后面
    s2.follow = p;
    await S.walk(p, 420, 176, { speed: 64 });
    S.letterbox(false);
    await S.setStage('street_ch2', { x: 150, y: 180, carry: [s2], facing: 1 });
    await streetIntro(S);
  }

  // ================================================================ 歌舞伎町：新八跟着走
  async function streetIntro(S) {
    const s = S.actor('shinpachi');
    S.letterbox(true);
    await S.say('shinpachi', '……我叫志村新八。家里是开剑术道场的。', { actor: s });
    await S.say('gintoki', '道场？');
    await S.say('shinpachi', '父亲去世以后，道场就没人来了。只剩我和姐姐两个人，还背着父亲留下的债。', { actor: s, expr: 'sad' });
    await S.say('shinpachi', '今天傍晚，讨债的人要上门。要是还不上……道场就要被收走了。', { actor: s, expr: 'sad' });
    await S.say('gintoki', '所以你才在家庭餐厅打工。');
    await S.say('shinpachi', '……嗯。虽然今天被开除了。', { actor: s, expr: 'gloom' });
    await S.say('shinpachi', '所以！请你跟我回道场一趟！刚才那一下……你很能打吧？', { actor: s, expr: 'determined' });
    await S.say('gintoki', '我只是个路过的天然卷。');
    await S.say('shinpachi', '刚才把天人打穿墙的路人是谁啊！', { actor: s, expr: 'shout' });
    await S.say('gintoki', '……带路吧。先说好，谈不拢我就跑。');
    S.letterbox(false);
    S.hint('跟新八去志村道场（一直往右走）。路上可以和街坊聊聊天', 7);
    F().toDojo = true;
  }
  async function talkShinStreet(S, a) {
    const lines = [
      ['道场就在这条街的尽头。一直往右走就到了。', null],
      ['姐姐她……人很好的。就是做饭的时候，有点可怕。', 'sad'],
      ['父亲说过，剑是用来守护重要的东西的。……可我现在，连饭碗都守不住。', 'gloom'],
    ];
    const n = count('shinSt');
    const [t, e] = lines[(n - 1) % lines.length];
    await S.say('shinpachi', t, { actor: a, expr: e });
    if (n === 3) await S.say('gintoki', '……饭碗这种东西，再找一个就是了。');
  }
  async function talkOtose2(S) {
    if (count('otose2') === 1) {
      await S.say('otose', '哟，银时。怎么还带了个眼镜回来？');
      await S.say('gintoki', '是他自己跟上来的。');
      await S.say('shinpachi', '我叫志村新八！请不要只看眼镜！', { expr: 'shout' });
      await S.say('otose', '新八是吧。……跟着这种男人，你的人生可是会走下坡路的。');
      await S.say('shinpachi', '已经在走了。今天刚被开除。', { expr: 'gloom' });
      await S.say('otose', '……那还真是辛苦你了。');
    } else await S.say('otose', '房租的事我可没忘。你那五千，只够抵这个月的。');
  }
  async function talkDango2(S) {
    if (count('dango2') === 1) {
      await S.say('townswoman', '阿银，今天带了个跟班？', { name: '团子店大婶' });
      await S.say('gintoki', '……是被开除的服务员。');
      await S.say('shinpachi', '请不要用这种方式介绍我！', { expr: 'shout' });
    } else await S.say('townswoman', '要来串团子吗？跟班那份，记在你的账上。', { name: '团子店大婶' });
  }
  async function talkBook2(S) {
    if (count('book2') === 1) {
      await S.say('townsman', '阿银，这周的 Jump——', { name: '书店店员' });
      await S.say('gintoki', '我知道，还没到。');
      await S.say('shinpachi', '你每天都来问吗！？', { expr: 'shock' });
      await S.say('townsman', '一天三次。', { name: '书店店员' });
    } else await S.say('townsman', '眼镜小哥，你也看 Jump 吗？', { name: '书店店员' });
  }
  async function talkRamen2(S) {
    await S.say('townsman', '那个眼镜小哥，是你新雇的伙计吗？', { name: '排队的客人' });
    await S.say('gintoki', '不是。');
    await S.say('shinpachi', '至少回答得犹豫一下吧！', { expr: 'shout' });
  }
  async function talkGossip2(S) {
    if (count('gossip2') === 1) {
      await S.say('townsman', '听说了吗？前面那家家庭餐厅，墙上多了一个猪形状的洞。', { name: '路人' });
      await S.say('gintoki', '……世上什么奇怪的事都有。');
      await S.say('shinpachi', '那就是你干的吧！', { expr: 'shout' });
    } else await S.say('townsman', '猪形状的洞……到底是怎么打出来的呢。', { name: '路人' });
  }
  async function talkBath2(S) {
    await S.say('townswoman', '眼镜小哥，泡完澡来瓶草莓牛奶吗？今天打八折哦。', { name: '澡堂的看板娘' });
    await S.say('shinpachi', '我、我现在没那个心情……', { expr: 'sad' });
    await S.say('gintoki', '我有。');
    await S.say('townswoman', '一百二十日元哦。', { name: '澡堂的看板娘' });
    await S.say('gintoki', '……我也没那个心情了。');
  }
  const STREET_HOT2 = [
    { id: 'pachinko', x: 140, y: 166, r: 26, label: '柏青哥店', ly: 104,
      use: async (S) => { await S.say(null, '柏青哥店「新台入荷」。'); await S.say('shinpachi', '……你不会想进去吧？'); await S.say('gintoki', '只是看看。看看而已。'); } },
    { id: 'sign', x: 360, y: 166, r: 18, label: '招牌', lx: 352, ly: 84,
      use: async (S) => {
        await S.say(null, '二楼挂着招牌：「万事屋银酱」。');
        await S.say('shinpachi', '万事屋……？你是开万事屋的？');
        await S.say('gintoki', '什么活都接。只要给钱。');
        await S.say('shinpachi', '这句话我已经听过了……', { expr: 'gloom' });
      } },
    { id: 'sweets', x: 530, y: 166, r: 14, label: '甘味处', ly: 104,
      use: async (S) => {
        await S.say(null, '甘味处的招牌：巧克力芭菲，800 日元。');
        await S.say('gintoki', '……今天不想看见芭菲。');
        await S.say('shinpachi', '你刚才明明为了芭菲打穿了一面墙！', { expr: 'shout' });
      } },
    { id: 'drug', x: 1090, y: 166, r: 22, label: '药铺', ly: 104,
      use: async (S) => { await S.say(null, '药铺。'); await S.say('gintoki', '老板，有没有治眼镜的药？'); await S.say('shinpachi', '眼镜不是病！', { expr: 'shout' }); } },
  ];

  // 走到街的尽头：黄昏，志村道场门口
  async function toGate(S) {
    const p = S.player;
    await S.fadeOut(0.6);
    await S.narrate('——傍晚。志村道场。', { onBlack: true, auto: 1.6 });
    await S.setStage('dojo_gate_ch2', { x: -12, y: 188, carry: ['shinpachi'], facing: 1, fade: false });
    S.letterbox(true);
    S.sfx('wind', 0.25);
    S.sfx('bell', 0.5);
    await S.fadeIn(0.6);
    await S.walk(p, 72, 188, { speed: 50 });
    await gateIntro(S);
  }

  // ================================================================ 志村道场门口（黄昏）：讨债的、借条
  async function gateIntro(S) {
    const s = S.actor('shinpachi'), boss = S.actor('boss'), cA = S.actor('collA');
    s.talk = talkShinGate;
    await S.say('amanto_cat', '哟，志村家的小鬼回来了。钱准备好了吗？', { name: '讨债头目', actor: boss, expr: 'smug' });
    await S.say('shinpachi', '上个月不是才还过……！', { actor: s, expr: 'shock' });
    await S.say('amanto_cat', '那是本金。利息呢？利息！', { name: '讨债头目', actor: boss, expr: 'shout' });
    await S.say('amanto_cat', '借条已经贴在门上了喵。今天还不上，这道场就归我们！', { name: '讨债的', actor: cA });
    sweat(s);
    await S.say('shinpachi', '（小声）……怎、怎么办……', { actor: s, expr: 'sad' });
    await S.say('gintoki', '……先看看借条上写了什么。');
    S.letterbox(false);
    S.hint('调查贴在门上的借条，找出哪里不对，再去和讨债头目谈判', 7);
  }
  async function talkShinGate(S, a) {
    if (!F().readIOU) { await S.say('shinpachi', '借条就贴在门上……我不敢去看。', { actor: a, expr: 'sad' }); return; }
    await S.say('shinpachi', '父亲当年借的是五十万。这些年，我和姐姐每个月都在还……', { actor: a, expr: 'sad' });
    await S.say('gintoki', '还了多少？');
    await S.say('shinpachi', '加起来……早就超过五十万了。可他们说，利息还没还完。', { actor: a, expr: 'gloom' });
  }
  async function talkCollA(S, a) { await S.say('amanto_cat', '看什么看喵。借条上白纸黑字，写得清清楚楚。', { name: '讨债的', actor: a, expr: 'smug' }); }
  async function talkCollB(S, a) { await S.say('amanto_pig', '我们可是合法经营的讨债公司！……大概。', { name: '讨债的', actor: a }); }
  async function talkBoss(S, a) {
    const s = S.actor('shinpachi');
    if (!F().readIOU) {
      await S.say('amanto_cat', '怎么，想求情？', { name: '讨债头目', actor: a, expr: 'smug' });
      await S.say('gintoki', '（……先看看门上的借条写了些什么。）');
      return;
    }
    await S.say('amanto_cat', '怎么样？借条上写得清清楚楚吧？', { name: '讨债头目', actor: a, expr: 'smug' });
    for (;;) {
      const c = await S.choice(['借款是五十万日元', '利息每日三成', '落款是十年前', '印章是个猫爪印'], '借条哪里不对？');
      if (c === 1) break;
      const why = ['金额没错。父亲借的，确实是五十万……', '', '父亲确实是十年前借的。……这不奇怪。', '……那确实是猫爪印。但这不是重点吧！'][c];
      await S.say('shinpachi', why, { actor: s, expr: c === 3 ? 'shout' : 'sad' });
      await S.say('gintoki', '（……再想想。）');
    }
    await S.say('gintoki', '一天三成。利滚利，十天就是将近七百万。');
    await S.say('gintoki', '这不是借条。是抢劫说明书。');
    await S.say('shinpachi', '原、原来如此……！这种利息，根本不可能合法！', { actor: s, expr: 'determined' });
    S.emote(a, '!!', 0.7, '#ff6a4a');
    await S.say('amanto_cat', '……少、少啰嗦！', { name: '讨债头目', actor: a, expr: 'angry' });
    await S.say('amanto_cat', '在歌舞伎町，规矩就是我们定的！小的们，给我上！', { name: '讨债头目', actor: a, expr: 'shout' });
    await gateFight(S);
  }
  const GATE_HOT = [
    { id: 'iou', x: 164, y: 170, r: 12, ry: 12, label: '借条', ly: 104, cond: () => !F().dojoWon,
      use: async (S) => {
        await S.say(null, '借条：「借款人　志村○○　借款　五十万日元」');
        await S.say(null, '「利息　每日三成。逾期未还，以道场抵押。」');
        if (!F().readIOU) {
          F().readIOU = true;
          await S.say('gintoki', '……每日三成？');
          S.hint('想好了就去找讨债头目（右边那个大块头）谈判', 6);
        }
      } },
    { id: 'gap', x: 190, y: 166, r: 7, ry: 8, label: '门缝', ly: 82,
      use: async (S) => { await S.say(null, '门缝里透出灯光。……里面有人。'); await S.say('shinpachi', '是姐姐。她让我在外面把事情处理好……', { expr: 'sad' }); } },
    { id: 'plate', x: 258, y: 168, r: 8, ry: 10, label: '门牌', ly: 80,
      use: async (S) => { await S.say(null, '门柱上挂着「志村道场」的门牌。墨迹有点褪色了。'); await S.say('shinpachi', '父亲亲手写的。……以前每天都有门生来练剑。', { expr: 'sad' }); } },
    { id: 'lantern', x: 132, y: 168, r: 8, ry: 10, label: '灯笼', ly: 70,
      use: async (S) => { await S.say(null, '门口的灯笼已经点上了。'); await S.say('shinpachi', '每天傍晚，我都会来点灯。……就算没有客人。', { expr: 'sad' }); } },
    { id: 'tree', x: 334, y: 178, r: 16, ry: 14, label: '樱花树', ly: 100,
      use: async (S) => { await S.say(null, '门边的樱花开得正好。'); await S.say('gintoki', '……讨债的人，也会看樱花吗。'); } },
  ];

  // ================================================================ 门口的战斗：新八一起打，头目留给阿妙
  async function gateFight(S) {
    const s = S.actor('shinpachi');
    await S.fight({
      arena: [8, 376],
      allies: ['shinpachi'], allyHp: 60,
      waves: [
        [{ actor: 'collA', cid: 'amanto_cat', name: '讨债的', hp: 26 }, { actor: 'collB', cid: 'amanto_pig', name: '讨债的', hp: 28 },
          { cid: 'amanto_cat', id: 'collC', name: '讨债的', hp: 24 }],
        [{ actor: 'boss', cid: 'amanto_cat', name: '讨债头目', hp: 130, boss: true, scale: 1.3, speed: 42, range: 26, minHp: 1,
          moves: ['E_SLASH', 'E_HEAVY'] }],
      ],
      endWhen: () => { const b = S.actor('boss'); return !!(b && b.team === 'enemy' && b.hp <= b.maxHp * 0.3); },
      onWave: async (S, i, es, attempt) => {
        if (i === 0 && attempt === 0) {
          await S.say('shinpachi', '我、我也来帮忙！道场的事，不能全靠别人！', { actor: s, expr: 'determined' });
          await S.say('gintoki', '别拖后腿啊，眼镜。');
          S.hint('新八会和你一起打。他被打倒了，过一会儿会自己爬起来', 6);
        }
        if (i === 1) await S.say('amanto_cat', '哼，有两下子。……让你们见识一下宇宙讨债人的手段！', { name: '讨债头目', actor: es[0], expr: 'shout' });
      },
      after: null,
    });
    await otaeArrives(S);
  }

  // 阿妙出场：一记超级拳把头目打成星星（名牌：志村妙）
  async function otaeArrives(S) {
    const p = S.player, s = S.actor('shinpachi'), boss = S.actor('boss');
    S.letterbox(true);
    S.stopMusic(0.4);
    boss.facing = -1;
    await S.say('amanto_cat', '可、可恶……！你们给我等着——', { name: '讨债头目', actor: boss, expr: 'hurt' });
    S.sfx('door', 0.5);
    const o = S.spawn('otae', 190, 166, { id: 'otae', facing: 1, name: '阿妙' });
    o.alpha = 0;
    await S.animate(0.4, (k) => { o.alpha = k; });
    o.alpha = 1;
    await S.say('otae', '哎呀～ 门口好热闹呢。', { actor: o, expr: 'happy' });
    S.emote(s, '!', 0.6);
    await S.say('shinpachi', '姐、姐姐！', { actor: s, expr: 'shock' });
    S.face(boss, o);
    await S.say('amanto_cat', '你就是志村家的姐姐？正好，钱——', { name: '讨债头目', actor: boss, expr: 'smug' });
    S.sfx('aura', 0.9);
    aura(o);
    await S.say('otae', '我家弟弟，承蒙你们照顾了呢～', { actor: o, expr: 'dark_smile' });
    aura(o);
    const dir = boss.x >= o.x ? 1 : -1;
    await S.walk(o, boss.x - dir * 30 * boss.scale, boss.y, { speed: 90 });
    o.facing = dir;
    boss.facing = -dir;
    S.sfx('whoosh', 0.7);
    S.pose(o, 'super_punch', { restart: true });
    await S.wait(0.3);
    S.sfx('punch_big', 1.0); S.sfx('impact', 0.7);
    S.impact(2);
    S.flash(0.2, 0.8);
    S.shake(5, 0.4);
    G.fx.word('砰!!', boss.x + 10, boss.y - 54);
    G.world.ko(boss, o);
    await S.until(() => o.animDone());
    await S.wait(1.0);
    S.unpose(o);
    S.nameCard('otae');
    S.music('comedy', 0.6);
    await S.wait(0.6);
    await S.say('otae', '借条？那种东西，烧掉就好了呀～', { actor: o, expr: 'happy' });
    const st = G.world.stage, iou = st.props.find((q) => q.id === 'iou');
    if (iou) {
      G.fx.debris(iou.x, iou.y - 8, ['rgb(255,140,50)', 'rgb(255,230,120)', 'rgb(80,70,70)'], 12, [20, 50], -60, 0.6);
      S.unprop(iou);
      S.sfx('pop', 0.5);
    }
    await S.say('shinpachi', '姐姐……还是那么可怕……', { actor: s, expr: 'gloom' });
    S.face(o, p);
    await S.say('otae', '新八，这位是？', { actor: o });
    await S.say('shinpachi', '他、他是……', { actor: s });
    await S.say('gintoki', '路过的万事屋。');
    await S.say('otae', '哎呀，那可得好好谢谢您。请进来坐吧——我来做点吃的～', { actor: o, expr: 'happy' });
    sweat(s, 7); sweat(s, -8);
    await S.say('shinpachi', '姐、姐姐要下厨……！？', { actor: s, expr: 'shock' });
    S.emote(p, '？', 0.8, '#fff');
    F().dojoWon = true;
    await S.walk(o, 190, 162, { speed: 70 });
    S.remove(o);
    S.letterbox(false);
    await S.setStage('dojo_ch2', { x: 60, y: 184, carry: ['shinpachi'], facing: 1 });
    await dojoIntro(S);
  }

  // ================================================================ 道场里：阿妙的「煎蛋」（原片镜头 H–I）
  async function dojoIntro(S) {
    const s = S.actor('shinpachi');
    s.talk = talkShinDojo;
    await S.say('shinpachi', '这里就是志村道场。……以前有很多门生，现在只剩下我一个了。', { actor: s, expr: 'sad' });
    await S.say('otae', '（厨房里传来声音）两位稍等哦～ 马上就好～');
    S.hint('在道场里看看。坐到坐垫上，就开饭了', 6);
  }
  async function talkShinDojo(S, a) {
    if (count('shinDojo') === 1) {
      await S.say('shinpachi', '姐姐的料理……你最好有心理准备。', { actor: a, expr: 'sad' });
      await S.say('gintoki', '能有多可怕？我连天人都不怕。');
      await S.say('shinpachi', '……天人至少不会让人失去意识。', { actor: a, expr: 'gloom' });
    } else await S.say('shinpachi', '坐垫在那边。……真的要坐吗？', { actor: a, expr: 'sad' });
  }
  const DOJO_HOT = [
    { id: 'plaque', x: 192, y: 166, r: 14, ry: 12, label: '匾额', ly: 4,
      use: async (S) => { await S.say(null, '匾额上写着「志村道场」。'); await S.say('shinpachi', '这是父亲亲手写的。', { expr: 'sad' }); } },
    { id: 'scroll', x: 299, y: 168, r: 10, ry: 12, label: '挂轴', ly: 32,
      use: async (S) => {
        await S.say(null, '挂轴上写着「一心」。');
        await S.say('gintoki', '一心……是一心一意吃甜食的意思吗。');
        await S.say('shinpachi', '绝对不是！', { expr: 'shout' });
      } },
    { id: 'rack', x: 340, y: 170, r: 16, ry: 12, label: '木刀架', ly: 80,
      use: async (S) => {
        await S.say(null, '木刀架上整整齐齐地摆着木刀。每一把都擦得很干净。');
        await S.say('shinpachi', '门生走光以后，我还是每天擦。……总觉得，哪天还会有人回来。', { expr: 'sad' });
        await S.say('gintoki', '……是吗。');
      } },
    { id: 'shoji', x: 40, y: 170, r: 16, ry: 12, label: '拉门', ly: 50,
      use: async (S) => { await S.say(null, '夕阳从拉门透进来，把地板染成了橘色。'); } },
    { id: 'cushion', x: 150, y: 168, r: 12, ry: 10, label: '坐垫', ly: 140, cond: () => !F().egg,
      use: async (S) => { F().egg = true; await eggScene(S); } },
  ];

  async function eggScene(S) {
    const p = S.player, s = S.actor('shinpachi'), st = G.world.stage, sp = SP();
    S.letterbox(true);
    await S.walk(p, 150, 166, { speed: 60 });
    S.pose(p, 'sit', { y: 160 });
    p.facing = 1;
    s.follow = null;
    await S.walk(s, 104, 166, { speed: 60 });
    S.pose(s, 'sit', { y: 160 });
    s.facing = 1;
    await S.wait(0.5);
    // 阿妙端着「煎蛋」出来
    const o = S.spawn('otae', 420, 166, { id: 'otae', facing: -1, name: '阿妙' });
    await S.walk(o, 182, 160, { speed: 70 });
    o.facing = -1;
    await S.say('otae', '久等了～', { actor: o, expr: 'happy' });
    S.pose(o, 'offer_egg', { restart: true });
    S.sfx('aura', 0.9);
    aura(o);
    await S.say('otae', '请用～', { actor: o, expr: 'dark_smile' });
    sweat(p, 10);
    S.emote(s, '…', 0.8);
    await S.say('gintoki', '……这是什么？', { expr: 'shock' });
    await S.say('otae', '煎蛋呀～', { actor: o, expr: 'dark_smile' });
    // 特写：煎蛋（※本品为煎蛋）
    S.sfx('heartbeat', 0.8);
    S.insert(eggInsert);
    await S.say('gintoki', '（……这不是煎蛋。这是黑洞。）', { expr: 'shock' });
    S.insert(null);
    sweat(p, 10); sweat(p, -9);
    S.sfx('sweat', 0.7);
    const c = await S.choice(['吃', '不吃'], '要吃吗？');
    if (c === 1) {
      await S.say('gintoki', '那个……我突然想起来，还有点急事——');
      S.sfx('aura', 1.0);
      S.shake(2, 0.4);
      aura(o); aura(o);
      await S.say('otae', '……您说什么？', { actor: o, expr: 'dark_smile' });
      await S.say('gintoki', '……我吃。', { expr: 'cry' });
    } else {
      await S.say('gintoki', '……既、既然是一番好意。', { expr: 'sad' });
      await S.say('shinpachi', '等等！别吃啊——！', { actor: s, expr: 'shout' });
    }
    // 嘎嘣 → 紫光 → 往后倒、腿朝天 → 灵魂出窍
    S.sfx('chomp', 0.9);
    G.fx.word('嘎嘣', p.x + 16, p.y - 40);
    await S.wait(0.22);
    S.sfx('gulp', 0.8);
    await S.wait(0.3);
    S.sfx('shock', 0.7);
    S.flash(0.12, 0.5, 'rgb(170,90,220)');
    p.tint = { color: 'rgb(120,60,170)', k: 0.35 };
    await S.wait(0.15);
    await S.animate(0.2, (k) => { p.rot = (-Math.PI / 2) * G.ease.in(k); p.z = -3 * k; });
    S.sfx('thud', 0.9); S.sfx('fail', 0.55, 1.35);
    S.shake(2, 0.2);
    G.fx.word('咚!', p.x - 26, p.y - 34);
    G.fx.dust(p.x - 8, p.y - 2, 10);
    const soulImg = G.image(sp.soul.image), soulT0 = st.t;
    S.prop({ type: 'custom', x: p.x - 14, y: p.y - 10, depth: 999, draw: (g, x, y, t) => {
      const k = Math.min(1, (t - soulT0) / 0.6);
      const sy = y - 4 - k * 18 - Math.sin(t * 0.8 * 2 * Math.PI) * 2, sx = x + Math.sin(t * 0.6 * 2 * Math.PI) * 3;
      G.pxLine(g, x, y, Math.round(sx), Math.round(sy + 8), 'rgb(200,210,240)');
      g.globalAlpha = 0.85;
      g.drawImage(soulImg, Math.round(sx - soulImg.width / 2), Math.round(sy - soulImg.height / 2));
      g.globalAlpha = 1;
    } });
    await S.wait(0.8);
    S.unpose(o);
    await S.say('otae', '哎呀～ 好吃到说不出话来了呢。', { actor: o, expr: 'happy' });
    S.emote(s, '…', 1.0);
    await S.wait(1.0);
    // 新八跳起来：光束、樱花、眼镜一闪
    S.stopMusic(0.5);
    S.unpose(s, { y: 160 });
    st.state.rays = { x: 112, y: 140, amount: 0 };
    S.sfx('jump', 0.6); S.sfx('shine', 0.5);
    S.animate(0.5, (k) => { st.state.rays.amount = k; });
    await S.arc(s, 108, 168, 10, 0.22, { anim: 'jump' });
    S.unpose(s);
    s.facing = 1;
    S.sfx('land', 0.5);
    G.fx.dust(s.x, s.y, 6);
    st.state.sakura = true;
    await S.wait(0.3);
    S.sfx('sparkle', 0.8);
    sparkle(s.x + 3, s.y - 22, 9);
    await S.say('shinpachi', '……我决定了。', { actor: s, expr: 'glint' });
    // 指着昏倒的银时：「这个人」
    S.pose(s, 'point', { restart: true });
    S.sfx('whoosh', 0.4);
    const lab = S.prop({ type: 'text', text: '这个人', x: p.x + 8, y: p.y - 46, depth: 999, bob: 1.5 });
    const arw = S.prop({ type: 'text', text: '↓', x: p.x + 8, y: p.y - 33, depth: 999, bob: 1.5, color: 'rgb(255,226,60)' });
    await S.say('shinpachi', '我要跟着这个人，找回我的武士道！', { actor: s, expr: 'determined' });
    S.unprop(lab); S.unprop(arw);
    // 木刀指天
    S.sfx('shing', 0.7);
    await S.act(s, 'slash_up', { keep: true });
    st.state.rays.amount = 1.7;
    sparkle(s.x + 10, s.y - 41, 11, 'rgb(255,246,190)');
    G.fx.debris(s.x + 10, s.y - 41, ['rgb(255,240,170)', '#fff'], 14, [60, 140], 0, 0.45);
    await S.wait(0.5);
    S.sfx('fanfare', 0.9, 1.1);
    await S.notice({ who: 'shinpachi', expr: 'happy', title: '志村新八', text: '加入了万事屋！', sub: '吐槽 +99　眼镜 +1' });
    await S.say('otae', '新八～ 晚饭还有很多哦～', { actor: o, expr: 'dark_smile' });
    await S.say('shinpachi', '……', { actor: s, expr: 'gloom' });
    await S.fadeOut(1.4);
    F().ch2Done = true;
  }

  // ================================================================ 地图（第二章版）
  G.STAGES.restaurant_ch2 = Object.assign({}, G.STAGES.restaurant, {
    id: 'restaurant_ch2',
    npcs: [
      { cid: 'shinpachi__apron', id: 'shinpachi', x: 150, y: 172, facing: -1, anim: 'waiter', label: '服务员', name: '新八', talk: talkWaiter },
      { cid: 'amanto_pig', id: 'pigA', x: 226, y: 150, facing: -1, anim: 'sit', label: '天人客人', name: '天人客人', talk: talkPigA },
      { cid: 'amanto_pig', id: 'pigB', x: 266, y: 164, facing: -1, anim: 'arms_crossed', label: '天人客人', name: '猪头客人', talk: talkPigB },
      { cid: 'amanto_cat', id: 'catA', x: 334, y: 150, facing: -1, anim: 'sit', label: '天人客人', name: '天人客人', talk: talkCat },
    ],
    hotspots: REST_HOT,
  });
  G.STAGES.street_ch2 = Object.assign({}, G.STAGES.street, {
    id: 'street_ch2',
    npcs: [
      { cid: 'otose', id: 'otose', x: 356, y: 168, facing: -1, anim: 'smoke', talk: talkOtose2 },
      { cid: 'townsman', id: 'ramen', x: 50, y: 170, facing: 1, talk: talkRamen2, label: '排队的客人' },
      { cid: 'townsman__v2', id: 'gossip', x: 196, y: 188, facing: -1, talk: talkGossip2, label: '路人' },
      { cid: 'townsman__v1', id: 'book', x: 250, y: 168, facing: 1, talk: talkBook2, label: '书店店员' },
      { cid: 'townswoman__v1', id: 'dango', x: 500, y: 168, facing: 1, talk: talkDango2, label: '团子店大婶' },
      { cid: 'townswoman__v3', id: 'girl', x: 864, y: 172, facing: -1, talk: talkBath2, label: '澡堂的看板娘' },
    ],
    hotspots: STREET_HOT2,
    triggers: [{ id: 'toGate', x0: 1080, x1: 5000, cond: () => F().toDojo, run: toGate }],
  });
  G.STAGES.dojo_gate_ch2 = Object.assign({}, G.STAGES.dojo_gate, {
    id: 'dojo_gate_ch2',
    npcs: [
      { cid: 'amanto_cat', id: 'collA', x: 206, y: 172, facing: -1, label: '讨债的', name: '讨债的', talk: talkCollA },
      { cid: 'amanto_pig', id: 'collB', x: 238, y: 192, facing: -1, label: '讨债的', name: '讨债的', talk: talkCollB },
      { cid: 'amanto_cat', id: 'boss', x: 292, y: 180, facing: -1, scale: 1.3, anim: 'arms_crossed', label: '讨债头目', name: '讨债头目', talk: talkBoss },
    ],
    props: [{ id: 'iou', type: 'sprite', image: SP().iou.image, x: 164, y: 128, depth: 120 }],
    hotspots: GATE_HOT,
  });
  G.STAGES.dojo_ch2 = Object.assign({}, G.STAGES.dojo, { id: 'dojo_ch2', hotspots: DOJO_HOT });

  // ================================================================ 第二章主流程
  G.STORY.chapter2 = async function (S) {
    G.fadeAlpha = 0;
    G.world.stage = null;
    await S.chapterCard('ch2');
    const p = new G.Actor('gintoki', 28, 186, { id: 'player', team: 'player', hp: 100, speed: 72, name: '银时' });
    G.world.player = p;
    G.fadeAlpha = 1;
    await S.setStage('restaurant_ch2', { x: 28, y: 186, facing: 1 });
    await S.run(async (S) => {
      const shin = S.actor('shinpachi');
      S.pose(shin, 'waiter');
      S.state('crow', { frames: [SP().perch0.image, SP().perch1.image], fps: 1.5, x: 278, y: 96, flip: true });
      S.letterbox(true);
      S.sfx('crowd', 0.22);
      await S.walk(p, 86, 182, { speed: 50 });
      await S.say('gintoki', '（没错。今天，就是吃芭菲的日子。）');
      await S.say('gintoki', '（事务所抽屉里那张优惠券……虽然过期了。看不清日期，就等于没过期。）');
      S.face(shin, p);
      await S.say('shinpachi', '欢、欢迎光临！', { name: '服务员', actor: shin });
      S.letterbox(false);
      S.hint('和服务员说话，点一份芭菲（靠近按 Enter）', 6);
    });
    await S.until(() => G.flags.ch2Done);
  };
})();
