// 第二章：新八登场。家庭餐厅的芭菲惨案、志村道场与新八加入万事屋。
'use strict';
(function () {
  const G = window.G;
  const F = () => G.flags;

  const REST_HOT = [
    { id: 'menu', x: 90, y: 156, r: 24, label: '菜单', ly: 88, use: async (S) => { await S.say(null, '今日推荐：巧克力芭菲，800 日元。'); await S.say('gintoki', '这就是命运的味道。'); } },
    { id: 'clock', x: 132, y: 104, r: 16, label: '挂钟', ly: 70, use: async (S) => { await S.say(null, '挂钟慢了七分钟。'); await S.say('gintoki', '甜品店的时间，应该比别的地方走得快一点。'); } },
    { id: 'poster', x: 174, y: 72, r: 22, label: '海报', ly: 48, use: async (S) => { await S.say(null, '墙上贴着阿通的新单曲海报。'); await S.say('gintoki', '这个签名……像是用力过猛写穿了纸。'); } },
    { id: 'window', x: 250, y: 74, r: 28, label: '窗外', ly: 46, use: async (S) => { await S.say(null, '窗外电线上停着一只乌鸦。'); await S.say(null, '乌鸦：阿～'); await S.say('gintoki', '……总觉得它在等什么。'); } },
    { id: 'parfait', x: 286, y: 146, r: 22, label: '芭菲', ly: 112, cond: () => F().served, use: async (S) => { await S.say(null, '空杯子里只剩一颗融化的樱桃。'); } },
  ];

  async function restaurantTalk(S, a) {
    if (a.id === 'shinpachi_rest') {
      await S.say('shinpachi', '欢迎光临！请问您要点什么？', { actor: a });
      await S.say('gintoki', '巧克力芭菲。要最大的。');
      await S.say('shinpachi', '那个……优惠券已经过期三个月了。');
      await S.say('gintoki', '过期的不是优惠券，是这个社会。');
      await S.say('shinpachi', '我、我用员工折扣帮您垫上吧。请坐。');
      F().served = true; S.hint('调查餐厅，等芭菲送上来', 5); return;
    }
    await S.say(a.cid === 'amanto_pig' ? 'amanto_pig' : 'amanto_cat', '地球的菜单也就这样了。', { actor: a, name: '天人客人' });
    await S.say('gintoki', '嫌难吃可以不吃，嫌贵可以不付。');
  }

  async function parfaitIncident(S) {
    S.letterbox(true); await S.say(null, '芭菲上桌。银时眼里的星星，比杯子里的樱桃还亮。');
    await S.say('amanto_pig', '地球猴子！上菜慢死了！', { actor: S.actor('pigB'), name: '天人客人' });
    await S.say('shinpachi', '对、对不起！厨房刚才……');
    await S.say('gintoki', '别管他。芭菲要趁冰淇淋还没融化的时候吃。');
    S.sfx('crash'); S.shake(3, 0.25); await S.say(null, '猪头一拳砸在吧台上，芭菲飞起来，啪嚓一声碎在地上。');
    await S.say(null, '乌鸦从窗外飞过：阿～呆～'); await S.say('gintoki', '医生说我有糖尿病预备军，一星期只能吃一次。你知道这意味着什么吗？');
    await S.say('gintoki', '意味着这一星期的那一次，已经被你浪费了。');
    S.letterbox(false);
    await S.fight({ arena: [24, 360], waves: [
      [{ actor: 'pigA', cid: 'amanto_pig', name: '天人客人', hp: 28 }, { cid: 'amanto_cat', id: 'catA', name: '天人客人', hp: 24 }, { cid: 'amanto_cat', id: 'catB', name: '天人客人', hp: 24 }],
      [{ actor: 'pigB', cid: 'amanto_pig', name: '天人客人', hp: 80, boss: true, scale: 1.15, speed: 42, moves: ['E_SLASH', 'E_PUNCH', 'E_HEAVY'] }],
    ], onWave: async (S, i, es) => { if (i === 1) await S.say('amanto_pig', '敢砸我的芭菲？这可是我先看上的！', { actor: es[0], name: '天人客人' }); }, after: 'comedy' });
    const manager = S.spawn('townsman__v2', 50, 158, { id: 'manager', name: '店长', facing: 1 });
    manager.talk = null;
    manager.scale = 1.15;
    S.sfx('door_bang'); S.shake(2, 0.2);
    await S.walk(manager, 82, 158, { speed: 75 });
    await S.say('townsman', '新八！你被开除了！', { name: '店长', actor: manager });
    await S.say('shinpachi', '啊啊啊啊！我还没来得及结工资！');
    await S.walk(manager, 50, 158, { speed: 75 }); S.remove(manager);
    await S.say('shinpachi', '我、我竟然被开除了……');
    await S.say('shinpachi', '那句话应该由店长来说吧！');
    await S.say('gintoki', '走了，眼镜。');
    await S.say('shinpachi', '你给我等一下！！');
    F().restaurantDone = true;
  }

  async function dojoTalk(S, a) {
    if (a.id === 'debt') { await S.say('amanto_cat', '这张借条贴在门上，今天不还钱就把道场拿走。', { actor: a, name: '讨债的' }); return; }
    await S.say('shinpachi', '这里就是志村道场。父亲留下的道场，现在只剩我和姐姐了。', { actor: a });
  }

  async function debtPuzzle(S) {
    const c = await S.choice(['利息每日三成', '借款人名字写成了“志村新八郎”', '印章颜色太漂亮'], '借条哪里有问题？');
    if (c !== 0) { await S.say('shinpachi', '不对！这不是吐槽时间，重新看借条！'); return debtPuzzle(S); }
    await S.say('shinpachi', '对！利息每日三成，这种数字根本不可能合法！');
    await S.say('amanto_cat', '少啰嗦！你们两个一起上！');
    await S.fight({ arena: [20, 610], waves: [
      [{ cid: 'amanto_cat', id: 'debtA', name: '讨债的', hp: 30 }, { cid: 'amanto_pig', id: 'debtB', name: '讨债的', hp: 34 }],
      [{ cid: 'amanto_cat', id: 'debtBoss', name: '讨债头目', hp: 105, boss: true, scale: 1.25, speed: 40, moves: ['E_SLASH', 'E_HEAVY'] }],
    ], onWave: async (S, i, es) => { if (i === 1) await S.say('amanto_cat', '我可是歌舞伎町最讲规矩的讨债头目！', { actor: es[0], name: '讨债头目' }); }, after: 'yorozuya' });
    await S.say('otae', '弟弟，姐姐来晚了吗？', { actor: S.actor('otae') });
    await S.say('amanto_cat', '什、什么？'); S.sfx('punch_big'); S.flash(0.18, 0.7); S.shake(5, 0.35);
    await S.say('otae', '借条我会烧掉。你们，也请从门口消失。', { actor: S.actor('otae') });
    F().dojoWon = true;
  }

  async function eggScene(S) {
    S.letterbox(true); await S.say('otae', '请用～', { actor: S.actor('otae') });
    await S.say(null, '※本品为煎蛋');
    const c = await S.choice(['吃', '不吃']);
    if (c === 0) await S.say('gintoki', '嘎嘣……这不是煎蛋，是一块有梦想的石头。');
    else await S.say('gintoki', '我突然想起还有急事——');
    S.sfx('chomp'); S.flash(0.25, 0.7); await S.say(null, '银时的灵魂离开了身体。');
    await S.say('shinpachi', '我要跟着这个人，找回我的武士道！');
    S.nameCard('shinpachi'); await S.say(null, '志村新八 加入了万事屋！');
    S.letterbox(false); F().ch2Done = true;
  }

  G.STAGES.restaurant_ch2.npcs = [
    { cid: 'shinpachi__apron', id: 'shinpachi_rest', x: 178, y: 150, facing: -1, label: '服务员新八', talk: restaurantTalk },
    { cid: 'amanto_pig', id: 'pigA', x: 296, y: 155, facing: -1, label: '天人客人', talk: restaurantTalk },
    { cid: 'amanto_pig', id: 'pigB', x: 322, y: 158, facing: -1, label: '天人客人', talk: restaurantTalk },
  ];
  G.STAGES.restaurant_ch2.hotspots = REST_HOT;
  G.STAGES.restaurant_ch2.triggers = [{ x0: 250, x1: 350, y0: 145, y1: 190, cond: () => F().served && !F().restaurantDone, run: parfaitIncident }];
  G.STAGES.dojo_gate_ch2.npcs = [
    { cid: 'shinpachi', id: 'shinpachi_gate', x: 120, y: 180, facing: 1, label: '新八', talk: dojoTalk },
    { cid: 'amanto_cat', id: 'debt', x: 300, y: 176, facing: -1, label: '讨债的', talk: dojoTalk },
    { cid: 'otae', id: 'otae', x: 420, y: 180, facing: -1, label: '阿妙', talk: dojoTalk },
  ];
  G.STAGES.dojo_gate_ch2.hotspots = [{ x: 300, y: 166, r: 24, label: '借条', ly: 90, use: debtPuzzle }, { x: 192, y: 165, r: 20, label: '道场门牌', ly: 82, use: async (S) => S.say(null, '志村道场。字已经掉了一半。') }, { x: 70, y: 170, r: 25, label: '樱花树', ly: 90, use: async (S) => S.say(null, '樱花落在借条上，像一张粉色的欠条。') }];

  G.STAGES.dojo_ch2.npcs = [{ cid: 'otae', id: 'otae_inside', x: 214, y: 164, facing: -1, label: '阿妙', talk: async (S) => eggScene(S) }];
  G.STAGES.dojo_ch2.hotspots = [{ x: 84, y: 160, r: 22, label: '木刀架', ly: 90, use: async (S) => S.say(null, '木刀架上只剩一把木刀。银时的木刀不在这里。') }, { x: 310, y: 146, r: 25, label: '厨房', ly: 82, use: async (S) => S.say(null, '厨房里飘出一股无法解释的黑烟。') }];

  G.STORY.chapter2 = async function (S) {
    await S.chapterCard('ch2');
    const p = new G.Actor('gintoki', 84, 176, { id: 'player', team: 'player', hp: 100, speed: 72, name: '银时' });
    G.world.player = p;
    await S.setStage('restaurant_ch2', { x: 84, y: 176 });
    await S.run(async (S) => {
      await S.say('gintoki', '过期优惠券也是优惠券。今天的芭菲，我吃定了。');
      S.hint('和服务员新八说话，点一份巧克力芭菲', 6);
    });
    await S.until(() => F().restaurantDone);
    await S.setStage('street_ch1', { x: 300, y: 176 });
    const n = S.spawn('shinpachi', 270, 178, { id: 'shinpachi_follow', label: '新八', facing: 1, team: 'npc' });
    await S.run(async (S) => {
      await S.say('shinpachi', '我丢了工作，家里的道场还欠着债。讨债的人今天就会来。');
      await S.say('gintoki', '道场？听起来像是会提供免费午饭的地方。');
      S.hint('带新八去右侧的志村道场', 6);
    });
    G.world.stage.triggers.push({ x0: 520, x1: 1200, cond: () => true, run: async (S) => { await S.setStage('dojo_gate_ch2', { x: 96, y: 180 }); } });
    await S.until(() => G.world.stage.id === 'dojo_gate_ch2');
    const ally = S.actor('shinpachi_gate');
    if (ally) { ally.team = 'ally'; ally.talk = null; ally.maxHp = ally.hp = 45; }
    await S.until(() => F().dojoWon);
    await S.setStage('dojo_ch2', { x: 100, y: 176 });
    await S.until(() => F().ch2Done);
    G.completedChapter = '第二章';
  };
})();
