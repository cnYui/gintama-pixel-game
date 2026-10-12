// 第一章：万事屋阿银 —— 被催房租 → 在事务所里找私房钱（解谜）→ 被登势踢出窗外
//                       → 歌舞伎町自由闲逛、和街坊聊天 → 收“保护费”的天人混混（战斗）→ 今天的歌舞伎町也很和平
'use strict';
(function () {
  const G = window.G;
  const F = () => G.flags;
  const count = (key) => (G.flags[key] = (G.flags[key] || 0) + 1);

  // ================================================================ 事务所：找房租
  const OFFICE_HOT = [
    {
      id: 'tv', x: 36, y: 172, r: 22, ry: 16, label: '电视', ly: 96,
      use: async (S) => {
        await S.say(null, '电视里，结野主播正在播天气预报：「今天的歌舞伎町是晴天。局部地区，会有大叔从天而降。」');
        await S.say('gintoki', '……结野主播今天也很可爱。');
      },
    },
    {
      id: 'sofa', x: 90, y: 170, r: 26, ry: 14, label: '沙发', ly: 120,
      use: async (S) => {
        if (!F().note) {
          F().note = true;
          S.sfx('coin', 0.7);
          await S.say(null, '在沙发缝里摸到了 120 日元！……还有一张皱巴巴的字条。');
          await S.say(null, '「给未来的我：重要的钱，藏在你最重视的东西后面。——过去的我」');
          await S.say('gintoki', '……过去的我，你就不能写得清楚一点吗。');
          S.hint('“最重视的东西”是什么？再调查一下房间里的东西吧', 6);
        } else {
          await S.say(null, '沙发缝里只剩饼干渣了。');
        }
      },
    },
    {
      id: 'milk', x: 206, y: 172, r: 16, ry: 8, label: '草莓牛奶', ly: 140,
      use: async (S) => {
        await S.say(null, '最后一瓶草莓牛奶。');
        if (F().note && !F().money) await S.say('gintoki', '最重视的东西……草莓牛奶的后面是桌子。不对，不是这个。');
        else await S.say('gintoki', '这个不能卖。这是命。');
      },
    },
    {
      id: 'desk', x: 242, y: 166, r: 10, ry: 10, label: '办公桌', ly: 110,
      use: async (S) => {
        await S.say(null, '办公桌的抽屉里，只有一张过期的甜品店优惠券，和半根牙签。');
        if (F().note && !F().money) await S.say('gintoki', '……这里也没有。');
      },
    },
    {
      id: 'jump', x: 262, y: 168, r: 12, ry: 10, label: 'Jump', ly: 114,
      use: async (S) => {
        await S.say(null, '堆成小山的少年 Jump。最新一期要到下周一才发售。');
        if (F().note && !F().money) {
          await S.say('gintoki', '最重视的东西……是 Jump 吗？');
          await S.say(null, '一本一本翻过去，只翻出一张读者调查问卷。');
          await S.say('gintoki', '……不是 Jump。那就只剩下——');
        }
      },
    },
    {
      id: 'calendar', x: 296, y: 170, r: 14, ry: 12, label: '日历', ly: 64,
      use: async (S) => { await S.say(null, '日历上，下周一被红笔圈了起来：「Jump 发售日」。'); },
    },
    {
      id: 'clock', x: 128, y: 168, r: 10, ry: 12, label: '挂钟', ly: 66,
      use: async (S) => {
        await S.say(null, '挂钟指着十一点五十分。');
        await S.say('gintoki', '离太阳下山还早得很。……再睡一会儿也不是不行。');
      },
    },
    {
      id: 'sugar', x: 142, y: 166, r: 9, ry: 10, label: '「糖分」', lx: 190, ly: 8,
      use: async (S) => {
        if (!F().note) {
          await S.say(null, '墙上挂着「糖分」两个大字。万事屋的座右铭。');
        } else if (!F().money) {
          await S.say('gintoki', '最重视的东西……没错，是糖分！');
          S.sfx('sparkle', 0.8);
          await S.wait(0.3);
          S.sfx('coin');
          await S.say(null, '在「糖分」字画的背后，找到了一个信封——里面装着 5000 日元！');
          F().money = true;
          await S.say('gintoki', '我的私房钱！……这本来是留着吃巧克力芭菲的啊。', { expr: 'cry' });
          S.hint('带着钱，从右边的门出去', 5);
        } else {
          await S.say(null, '「糖分」。今天也辛苦你了。');
        }
      },
    },
    {
      id: 'plant', x: 362, y: 176, r: 14, ry: 12, label: '盆栽', ly: 112,
      use: async (S) => {
        await S.say(null, '一盆不知道是谁送的观叶植物。');
        await S.say('gintoki', '……好像该浇水了。算了，它自己会努力的。');
      },
    },
    {
      id: 'door', x: 338, y: 166, r: 12, ry: 10, label: '门', ly: 92,
      use: async (S) => {
        if (!F().money) {
          await S.say('gintoki', '空着手下楼，会被老太婆从窗户扔出去的。……得先凑点钱。');
          return;
        }
        await kickScene(S);
      },
    },
  ];

  // 交钱 → 三选一 → 被踢出窗外 → 落在大街上
  async function kickScene(S) {
    const p = S.player;
    S.door(true);
    S.sfx('door');
    await S.wait(0.35);
    const ot = S.spawn('otose', 338, 140, { id: 'otose', facing: -1 });
    await S.walk(p, 284, 172, { backward: true, speed: 50 });
    p.facing = 1;
    await S.walk(ot, 318, 168, { speed: 60 });
    await S.say('otose', '时间差不多了吧。钱呢？');
    S.emote(p, '!', 0.6);
    await S.say('gintoki', '这、这是……这个月的诚意。');
    S.sfx('coin');
    await S.say('otose', '……五千？三个月的房租，你就给我五千？', { expr: 'angry' });
    const c = await S.choice(['「剩下的，下个月一定给」', '「其实……这是押金」', '「老太婆，你今天看起来特别年轻」']);
    if (c === 0) await S.say('otose', '这句话，我已经听了整整三个月了。');
    else if (c === 1) await S.say('otose', '押金？你在这儿住了几年了，现在才想起来交押金？');
    else {
      await S.say('otose', '……嘴甜也没用。');
      await S.wait(0.4);
      await S.say('otose', '不过，还是谢谢你啊。', { expr: 'happy' });
    }
    S.music('comedy', 0.3);
    await S.say('otose', '——给我飞出去，好好反省！！', { expr: 'shout' });
    S.sfx('whoosh');
    await S.act(ot, 'kick', { speed: 1.6, keep: true });
    S.sfx('kick');
    S.sfx('punch_big', 0.8);
    S.word('砰!', p, -30);
    S.shake(4, 0.35);
    S.flash(0.15, 0.6);
    await S.arc(p, 192, 162, 70, 0.55, { anim: 'fly', z1: 60 });
    S.sfx('glass', 1);
    S.sfx('crash', 0.8);
    S.flash(0.4, 1);
    await S.fadeOut(0.15);
    // ---- 歌舞伎町：从二楼窗户掉下来
    G.world.setStage(G.STAGES.street_ch1, { player: p, x: 318, y: 176 });
    G.audio.music('comedy', 0.1);
    const st = G.world.stage;
    st.camTarget = 318 - 192;
    G.world.snapCamera();
    p.z = 112;
    p.hold = true;
    await S.fadeIn(0.15);
    S.sfx('fall_whistle', 0.8);
    await S.arc(p, 330, 178, 8, 0.6, { anim: 'fly', z1: 0 });
    p.z = 0;
    S.sfx('thud', 1);
    S.shake(3, 0.3);
    G.fx.dust(p.x, p.y, 10);
    S.word('咚!', p, -16);
    S.pose(p, 'lie');
    await S.wait(0.5);
    const ga = S.actor('passerby');
    if (ga) {
      S.face(ga, p);
      await S.say('townsman', '啊，又飞出来了。', { name: '路过的大叔', actor: ga });
      await S.say('townswoman', '今天也很准时呢。', { name: '路过的大婶', actor: S.actor('passerby2') });
    }
    await S.wait(0.3);
    S.unpose(p);
    p.facing = 1;
    await S.say('gintoki', '……疼死了。那个老太婆，踢人是一年比一年准了。');
    st.camTarget = null;
    S.music('yorozuya', 1.0);
    S.hint('去楼下酒馆门口，和登势说说话', 6);
    F().landed = true;
  }

  // ================================================================ 大街：街坊们
  async function talkOtose(S) {
    if (!F().thugs) {
      await S.say('otose', '还活着？那就别闲着。');
      await S.say('otose', '最近有一帮天人，在这条街上收什么「保护费」。连甘味处那边都被找上门了。');
      await S.say('gintoki', '那种事，找警察去啊。');
      await S.say('otose', '警察？你在这条街上看见警察管过天人吗。……反正你闲着也是闲着。');
      await S.say('gintoki', '我可不是闲着。我是在思考人生。');
      await S.say('otose', '思考完了，就去甘味处那边看看。往右走，红伞那家。');
      F().thugs = true;
      S.hint('往右走，去甘味处（红伞那家）看看', 6);
      return;
    }
    const n = count('otoseN');
    if (n === 1) {
      await S.say('otose', '……那年冬天，你蹲在我丈夫的坟前，偷吃供在那儿的馒头。');
      await S.say('gintoki', '那馒头挺好吃的。');
      await S.say('otose', '我那时候就想，这小子以后一定是个大麻烦。……结果还真被我说中了。');
    } else {
      await S.say('otose', '还愣着干什么。去吧，别给我丢人。');
    }
  }
  async function talkRamen(S) {
    const n = count('ramenN');
    if (n % 2 === 1) {
      await S.say('townsman', '最近天人越来越多，连一碗拉面的价钱都涨了。', { name: '排队的客人' });
      await S.say('gintoki', '拉面涨价是天人的错，房租交不起也是天人的错。');
      await S.say('townsman', '……后面那个不是吧。', { name: '排队的客人' });
    } else {
      await S.say('townsman', '这家的老板娘做的拉面特别好吃，就是不怎么爱笑。', { name: '排队的客人' });
    }
  }
  async function talkSword(S) {
    const n = count('swordN');
    if (n === 1) {
      await S.say('townsman', '废刀令以后，还敢在腰上插着刀到处走的，也就只有你了吧？', { name: '路人' });
      await S.say('gintoki', '这是木刀。洞爷湖的。');
      await S.say('townsman', '洞爷湖？', { name: '路人' });
      await S.say('gintoki', '电视购物买的。刀身上刻着字，很帅吧。');
    } else {
      await S.say('townsman', '电视购物……我也想买一把。', { name: '路人' });
    }
  }
  async function talkBookshop(S) {
    const n = count('bookN');
    if (n === 1) {
      await S.say('townsman', '阿银，这周的 Jump 还没到货哦。', { name: '书店店员' });
      await S.say('gintoki', '我知道。今天又不是周一。……我只是来确认一下，它真的还没到。');
    } else {
      await S.say('townsman', '……你已经确认第三次了。', { name: '书店店员' });
    }
  }
  async function talkDango(S) {
    if (F().beatThugs) {
      await S.say('townswoman', '多亏了你，今天总算能安心做生意了。', { name: '团子店大婶' });
      await S.say('gintoki', '那团子钱——');
      await S.say('townswoman', '照付。', { name: '团子店大婶' });
      return;
    }
    await S.say('townswoman', '要来串团子吗？……先把上次的账结了再说。', { name: '团子店大婶' });
  }

  const STREET_HOT = [
    { id: 'pachinko', x: 140, y: 166, r: 26, label: '柏青哥店', ly: 104,
      use: async (S) => { await S.say(null, '柏青哥店「新台入荷」。'); await S.say('gintoki', '兜里只剩 120 日元……还是算了。今天的运势不太行。'); } },
    { id: 'sign', x: 360, y: 166, r: 18, label: '招牌', lx: 352, ly: 84,
      use: async (S) => {
        await S.say(null, '二楼挂着招牌：「万事屋银酱」。什么活都接。');
        await S.say('gintoki', '……就是活不怎么来。');
      } },
    { id: 'stairs', x: 404, y: 166, r: 12, label: '楼梯', ly: 104,
      use: async (S) => { await S.say('gintoki', '现在上楼，又会被老太婆念叨。……先在外面晃一会儿。'); } },
    { id: 'sweets', x: 508, y: 166, r: 18, label: '甘味处', ly: 104,
      use: async (S) => { await S.say(null, '甘味处的招牌甜品：巧克力芭菲，800 日元。'); await S.say('gintoki', '……眼睛移不开。'); } },
    { id: 'sake', x: 594, y: 166, r: 18, label: '酒屋', ly: 104,
      use: async (S) => { await S.say(null, '酒屋。登势酒馆的酒，就是从这家进的货。'); } },
    { id: 'host', x: 684, y: 166, r: 24, label: '高天原', ly: 92,
      use: async (S) => {
        await S.say(null, '牛郎店「高天原」。门口贴着头牌的海报。');
        await S.say('gintoki', '……总觉得哪天会跟这家店扯上关系。');
      } },
    { id: 'tofu', x: 790, y: 166, r: 18, label: '豆腐店', ly: 104,
      use: async (S) => { await S.say(null, '豆腐店。今天的豆腐好像特别白。'); } },
    { id: 'sento', x: 889, y: 166, r: 24, label: '澡堂', ly: 104,
      use: async (S) => {
        await S.say(null, '澡堂。男汤在左，女汤在右。');
        await S.say('gintoki', '泡完澡来一瓶草莓牛奶，人生就圆满了。');
      } },
    { id: 'pawn', x: 983, y: 166, r: 18, label: '当铺', ly: 104,
      use: async (S) => { await S.say(null, '当铺。'); await S.say('gintoki', '洞爷湖可不能当。……房租的事，再想想别的办法吧。'); } },
    { id: 'drug', x: 1090, y: 166, r: 22, label: '药铺', ly: 104,
      use: async (S) => { await S.say(null, '药铺。'); await S.say('gintoki', '老板，有没有治天然卷的药？'); await S.say(null, '……没有人回答。'); } },
  ];

  // ================================================================ 大街：收保护费的天人
  async function thugScene(S) {
    const p = S.player;
    const lady = S.actor('dango');
    S.letterbox(true);
    const a = S.spawn('amanto_pig', 610, 172, { id: 'thugA', name: '天人混混', facing: -1 });
    const b = S.spawn('amanto_cat', 636, 184, { id: 'thugB', name: '天人混混', facing: -1 });
    const c = S.spawn('amanto_pig', 652, 166, { id: 'thugC', name: '天人混混', facing: -1 });
    S.camera(400);
    await S.walk(a, 548, 172, { speed: 55 });
    S.music('tension', 0.6);
    await S.say('amanto_pig', '喂，老太婆！这个月的「保护费」呢？', { name: '天人混混', actor: a });
    if (lady) S.pose(lady, 'shock');
    await S.say('townswoman', '我、我们这种小店，哪有那么多钱……', { name: '团子店大婶', actor: lady });
    await S.say('amanto_cat', '没钱？那就把你的店砸了喵！', { name: '天人混混', actor: b });
    S.camera(null);
    await S.walk(p, 500, 176, { speed: 60 });
    p.facing = 1;
    await S.say('gintoki', '喂。你们几个，挡着我去买草莓牛奶的路了。');
    S.face(a, p); S.face(b, p); S.face(c, p);
    S.emote(a, '?', 0.7);
    await S.say('amanto_pig', '啊？哪来的天然卷？……腰上还插着刀？废刀令知不知道啊！', { name: '天人混混', actor: a });
    await S.say('gintoki', '这是木刀。洞爷湖的。');
    S.emote(a, '!!', 0.7, '#ff6a4a');
    await S.say('amanto_pig', '管你什么湖！兄弟们，揍他！', { name: '天人混混', actor: a });
    if (lady) { await S.walk(lady, 474, 164, { speed: 80, anim: 'run_away' }); S.pose(lady, 'shock'); lady.facing = 1; }
    S.letterbox(false);
    S.hint('J 攻击（连按三连击）　K 跳跃（空中按 J 跳斩）　按住 L 防御', 7);
    await S.fight({
      arena: [430, 814],
      waves: [
        [{ actor: 'thugA', cid: 'amanto_pig', name: '天人混混', hp: 26 }, { actor: 'thugB', cid: 'amanto_cat', name: '天人混混', hp: 22 }, { actor: 'thugC', cid: 'amanto_pig', name: '天人混混', hp: 26, side: 'left' }],
        [{ cid: 'amanto_pig', id: 'aniki', name: '猪头大哥', hp: 120, boss: true, scale: 1.4, speed: 40, range: 26, moves: ['E_SLASH', 'E_PUNCH', 'E_HEAVY'] }],
      ],
      onWave: async (S, i, es, attempt) => {
        if (i !== 1) return;
        const boss = es[0];
        await S.say('amanto_pig', '敢动老子的小弟？……老子在这条街收了三年的钱，还没见过你这么不要命的地球猴子！', { name: '猪头大哥', actor: boss });
        if (attempt === 0) await S.say('gintoki', '三年？那你欠这条街的，可比我欠的房租多多了。');
        S.hint('大块头的大招前会闪红光、喊「!!」——按住 L 防御，或者跳开', 6);
      },
      after: 'yorozuya',
    });
    F().beatThugs = true;
    await ending(S);
  }

  async function ending(S) {
    const p = S.player;
    const lady = S.actor('dango');
    if (lady) {
      S.unpose(lady);
      await S.walk(lady, p.x - 26, p.y - 4, { speed: 60 });
      S.face(lady, p);
      S.face(p, lady);
      await S.say('townswoman', '谢、谢谢你，阿银！', { name: '团子店大婶', actor: lady });
      await S.say('gintoki', '谢就不用了。……之前的团子钱，就当一笔勾销吧。');
      await S.say('townswoman', '那可不行。', { name: '团子店大婶', actor: lady });
      S.emote(p, '…', 1.0);
      await S.wait(0.8);
    }
    const st = G.world.stage;
    const ot = S.spawn('otose', st.camX - 16, 170, { id: 'otose_end', facing: 1, anim: 'smoke' });
    await S.walk(ot, p.x - 40, 170, { speed: 55, endAnim: 'smoke' });
    S.face(p, ot);
    await S.say('otose', '哼。总算干了件正经事。');
    await S.say('otose', '这个月的房租……就先拿那五千抵着吧。');
    S.emote(p, '!', 0.6);
    await S.say('gintoki', '真的？老太婆，你今天果然特别年轻！', { expr: 'happy' });
    await S.say('otose', '少得寸进尺。下个月少一分，照样把你踢出去。', { expr: 'angry' });
    await S.walk(ot, st.camX - 30, 170, { speed: 60 });
    S.remove(ot);
    if (lady) { await S.walk(lady, 508, 164, { speed: 60 }); }
    S.letterbox(true);
    p.facing = 1;
    S.pose(p, 'nosepick');
    S.music('ending', 1.0);
    await S.wait(1.2);
    S.word('抠…抠…', p, -42);
    await S.wait(0.9);
    await S.say('gintoki', '……今天的歌舞伎町，也很和平呢。');
    await S.wait(0.6);
    await S.fadeOut(1.4);
    G.flags.ch1Done = true;
  }

  // ================================================================ 地图（第一章版）
  G.STAGES.office_ch1 = Object.assign({}, G.STAGES.office, {
    id: 'office_ch1',
    hotspots: OFFICE_HOT,
  });
  G.STAGES.street_ch1 = Object.assign({}, G.STAGES.street, {
    id: 'street_ch1',
    npcs: [
      { cid: 'otose', id: 'otose', x: 356, y: 168, facing: -1, anim: 'smoke', talk: talkOtose },
      { cid: 'townsman', id: 'ramen', x: 50, y: 170, facing: 1, talk: talkRamen, label: '排队的客人' },
      { cid: 'townsman__v2', id: 'sword', x: 156, y: 186, facing: -1, talk: talkSword, label: '路人' },
      { cid: 'townsman__v1', id: 'book', x: 250, y: 168, facing: 1, talk: talkBookshop, label: '书店店员' },
      { cid: 'townswoman__v1', id: 'dango', x: 508, y: 168, facing: 1, talk: talkDango, label: '团子店大婶' },
      { cid: 'townsman__v3', id: 'passerby', x: 266, y: 190, facing: 1, label: '路过的大叔',
        talk: async (S) => { await S.say('townsman', '阿银，又被登势婆婆踢出来啦？', { name: '路过的大叔' }); await S.say('gintoki', '这叫战略性撤退。'); } },
      { cid: 'townswoman__v2', id: 'passerby2', x: 300, y: 194, facing: 1, label: '路过的大婶',
        talk: async (S) => { await S.say('townswoman', '每个月都能看到一次，跟放烟花似的。', { name: '路过的大婶' }); } },
      { cid: 'townswoman__v3', id: 'girl', x: 864, y: 172, facing: -1, label: '澡堂的看板娘',
        talk: async (S) => {
          await S.say('townswoman', '欢迎光临～ 泡完澡的草莓牛奶，今天打八折哦。', { name: '澡堂的看板娘' });
          await S.say('gintoki', '……可恶，偏偏是今天。我身上只有 120 日元。');
        } },
    ],
    hotspots: STREET_HOT,
    triggers: [
      { id: 'thugs', x0: 452, x1: 5000, cond: () => G.flags.thugs && !G.flags.beatThugs, run: thugScene },
    ],
  });

  // ================================================================ 第一章主流程
  G.STORY.chapter1 = async function (S) {
    G.fadeAlpha = 0;
    G.world.stage = null;
    await S.chapterCard('ch1');
    const p = new G.Actor('gintoki', 90, 151, { id: 'player', team: 'player', hp: 100, speed: 72, name: '银时' });
    G.world.player = p;
    G.fadeAlpha = 1;
    await S.setStage('office_ch1', { x: 90, y: 151 });
    await S.run(async (S) => {
      S.letterbox(true);
      p.facing = 1;
      S.pose(p, 'sleep', { y: 151 });
      await S.wait(1.0);
      await S.say('gintoki', '……呼……草莓牛奶……再来一瓶……', { expr: 'sleep' });
      S.door(true);
      S.sfx('door_bang');
      S.shake(2, 0.2);
      await S.wait(0.4);
      const ot = S.spawn('otose', 338, 140, { id: 'otose', facing: -1 });
      await S.walk(ot, 300, 168, { speed: 70 });
      await S.say('otose', '银时！三个月的房租呢！', { expr: 'angry' });
      S.sfx('shock');
      S.emote(p, '!', 0.6);
      S.pose(p, 'sit', { y: 153 });
      await S.say('gintoki', '……啊？老太婆，大白天的别吼……');
      await S.say('otose', '大白天？太阳都晒到屁股了！这个月的房租，你打算怎么办？');
      await S.say('gintoki', '下个月……一定。');
      await S.say('otose', '你上个月也是这么说的。上上个月也是。');
      await S.say('gintoki', '上个月的我和这个月的我，是不同的人。人是会成长的。');
      await S.say('otose', '那就让成长了的你，把房租交出来。', { expr: 'angry' });
      S.nameCard('otose');
      await S.say('otose', '我在楼下等着。太阳下山之前见不到钱，就把你连同那一堆 Jump，一起扔到大街上。');
      await S.walk(ot, 338, 140, { speed: 70 });
      S.remove(ot);
      S.door(false);
      S.sfx('door');
      await S.wait(0.4);
      S.unpose(p, { y: 172, x: 108 });
      await S.say('gintoki', '……这下麻烦了。');
      await S.say('gintoki', '万事屋的金库里，应该还剩点钱吧……大概。');
      S.nameCard('gintoki');
      S.letterbox(false);
      S.hint('调查房间里的东西，凑出房租（靠近按 Enter）', 6);
    });
    await S.until(() => G.flags.landed);
    await S.until(() => G.flags.ch1Done);
  };
})();
