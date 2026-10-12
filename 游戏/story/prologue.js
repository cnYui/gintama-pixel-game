// 序章：白夜叉 —— 攘夷战争的营地（自由走动、和战友聊天）→ 两场战斗 → 天人部队长
'use strict';
(function () {
  const G = window.G;
  const count = (key) => (G.flags[key] = (G.flags[key] || 0) + 1);

  // ---------------------------------------------------------------- 战友们
  async function talkKatsura(S) {
    const n = count('katN');
    if (n % 3 === 1) {
      await S.say('katsura', '听着，银时。我们拿起刀，不是为了送死。');
      await S.say('shiroyasha', '知道啦。……是为了把该拿回来的东西，拿回来。');
      await S.say('katsura', '……嗯。');
    } else if (n % 3 === 2) {
      await S.say('katsura', '天人的炮舰进不了这片林子。只要把他们的步兵打退，今晚就能睡个安稳觉。');
      await S.say('shiroyasha', '能睡觉就好。……要是还能吃点甜的，就更好了。');
    } else {
      await S.say('katsura', '对了，你那头卷毛，打仗的时候能不能用头巾包起来？在战场上太显眼了。');
      await S.say('shiroyasha', '天然卷又不是我自己想要的！', { expr: 'angry' });
      await S.say('katsura', '……我只是担心你被当成靶子。');
    }
  }
  async function talkSakamoto(S) {
    const n = count('sakaN');
    if (n === 1) {
      await S.say('sakamoto', '啊哈哈哈！金时！你又要一个人冲在最前面了吗！');
      await S.say('shiroyasha', '是银时。……你那边的补给怎么样了？');
      await S.say('sakamoto', '放心放心！粮食、火药，还有给伤员的绷带，全都齐了！');
      S.nameCard('sakamoto');
    } else if (n === 2) {
      await S.say('sakamoto', '我跟你说，金时。等仗打完，我要造一艘大船，到宇宙去做生意！');
      await S.say('shiroyasha', '宇宙？天人就是从那儿来的。你脑子被大炮震坏了吧。');
      await S.say('sakamoto', '正因为他们从那儿来，才更要去看看嘛！啊哈哈哈！');
    } else {
      await S.say('sakamoto', '金时，别死啊。死了就不能一起喝酒了。');
      await S.say('shiroyasha', '……是银时。你倒是先把我的名字记住啊。');
      await S.say('sakamoto', '啊哈哈哈哈！');
    }
  }
  async function talkShishiA(S) {
    const n = count('aN');
    if (n % 2 === 1) {
      await S.say('townsman', '白夜叉大人……听说您一个人砍倒了一整队天人？', { name: '年轻的志士' });
      await S.say('shiroyasha', '谁传的谣言。我只是迷了路，不小心走到他们中间而已。');
      await S.say('townsman', '……那、那也很厉害啊！', { name: '年轻的志士' });
    } else {
      await S.say('townsman', '等战争结束了，我想回老家开一间团子店。', { name: '年轻的志士' });
      await S.say('shiroyasha', '团子店啊……不错。开张那天记得叫我，第一串我包了。');
    }
  }
  async function talkShishiB(S) {
    const n = count('bN');
    if (n % 2 === 1) {
      await S.say('townsman', '天人的炮舰就停在山那边……那种东西，我们真的打得赢吗？', { name: '放哨的志士' });
      await S.say('shiroyasha', '打不打得赢，先打了再说。……反正我们也没有退路了。');
    } else {
      await S.say('townsman', '前面就是战场了。白夜叉大人，请您……一定要活着回来。', { name: '放哨的志士' });
      await S.say('shiroyasha', '放心。我还没吃到团子呢。');
    }
  }

  // ---------------------------------------------------------------- 调查点
  const HOT = [
    {
      id: 'fire', x: 172, y: 188, r: 16, label: '篝火',
      use: async (S) => {
        await S.say(null, '噼啪作响的篝火。锅里只有稀粥，一点甜味都没有。');
        await S.say('shiroyasha', '……至少给我放一勺糖啊。');
      },
    },
    {
      id: 'tent', x: 56, y: 168, r: 24, label: '营帐',
      use: async (S) => {
        await S.say(null, '营帐里堆着备用的刀和绷带。……角落里还有一本翻烂了的少年漫画杂志。');
        await S.say('shiroyasha', '这期的连载……我还没看完呢。');
      },
    },
    {
      id: 'banner', x: 352, y: 168, r: 12, label: '战旗',
      use: async (S) => { await S.say(null, '白底红纹的战旗，在风里猎猎作响。'); },
    },
    {
      id: 'tent2', x: 262, y: 168, r: 22, label: '营帐',
      use: async (S) => {
        await S.say(null, '桂的营帐。桌上摊着地图，旁边整整齐齐叠着一摞……写着「攘夷」的传单。');
        await S.say('shiroyasha', '……打仗的时候还印传单，这家伙真是一点都没变。');
      },
    },
  ];

  // ---------------------------------------------------------------- 战斗
  async function battle1(S) {
    const p = S.player;
    p.facing = 1;
    await S.say('shiroyasha', '……来了。');
    S.sfx('shing');
    S.flash(0.12, 0.5);
    S.hint('J 攻击（连按三连击）　K 跳跃（空中按 J 跳斩）　按住 L 防御', 8);
    await S.fight({
      arena: [470, 854],
      waves: [
        [{ cid: 'amanto_pig', name: '天人兵', hp: 24 }, { cid: 'amanto_cat', name: '天人兵', hp: 22 , side: 'right' }],
        [{ cid: 'harusame', name: '天人兵', hp: 28 }, { cid: 'amanto_pig', name: '天人兵', hp: 24, side: 'left' }, { cid: 'amanto_cat', name: '天人兵', hp: 22 }],
      ],
      onWave: async (S, i, es, attempt) => {
        if (attempt > 0) return;
        if (i === 0) await S.say('amanto_pig', '是攘夷志士！就一个人？围住他！', { name: '天人兵', actor: es[0] });
        if (i === 1) {
          await S.say('harusame', '地球的猴子，也敢挡我们的路！', { name: '天人兵', actor: es[0] });
          await S.say('shiroyasha', '猴子怎么了？猴子也是有尊严的。');
        }
      },
    });
    G.flags.b1 = true;
    await S.say('shiroyasha', '……还没完。前面还有。');
  }

  async function battle2(S) {
    const p = S.player;
    p.facing = 1;
    await S.say('shiroyasha', '……那个大块头，就是部队长吧。');
    await S.fight({
      arena: [900, 1284],
      waves: [
        [{ cid: 'harusame', name: '天人兵', hp: 28 }, { cid: 'amanto_cat', name: '天人兵', hp: 24, side: 'left' }, { cid: 'amanto_pig', name: '天人兵', hp: 26 }],
        [{ cid: 'amanto_pig', id: 'boss', name: '天人部队长', hp: 140, boss: true, scale: 1.45, speed: 38, range: 26, moves: ['E_SLASH', 'E_HEAVY'] }],
      ],
      onWave: async (S, i, es, attempt) => {
        if (i !== 1) return;
        const b = es[0];
        await S.say('amanto_pig', '你就是传说中的「白夜叉」？……看起来，不过是个白毛小鬼。', { name: '天人部队长', actor: b });
        await S.say('shiroyasha', '白毛是天生的。小鬼是你的错觉。');
        if (attempt === 0) {
          await S.say('amanto_pig', '等我们拿下这颗星球，你们这些武士，连刀都别想再拿！', { name: '天人部队长', actor: b });
          await S.say('shiroyasha', '那就趁现在……多砍几个。');
        }
        S.hint('部队长的大招前会闪红光、喊「!!」——按住 L 防御，或者跳开', 6);
      },
      after: null,
    });
    await afterWar(S);
  }

  async function afterWar(S) {
    const p = S.player, st = G.world.stage;
    S.music('sad', 1.2);
    await S.wait(0.5);
    const kat = S.spawn('katsura', st.camX - 24, 174, { id: 'kat2', facing: 1 });
    const sak = S.spawn('sakamoto', st.camX - 50, 188, { id: 'sak2', facing: 1 });
    await Promise.all([
      S.walk(kat, p.x - 44, 174, { anim: 'run', speed: 95 }),
      S.walk(sak, p.x - 70, 188, { anim: 'run', speed: 95 }),
    ]);
    S.face(p, kat);
    await S.say('katsura', '银时！……你一个人，把他们全打退了？');
    await S.say('sakamoto', '啊哈哈哈！金时果然是个怪物！');
    await S.say('shiroyasha', '是银时……还有，别把人家当怪物。');
    S.pose(p, 'sit');
    await S.say('shiroyasha', '……好累。有没有甜的东西。');
    await S.say('katsura', '……没有。');
    await S.say('sakamoto', '啊哈哈哈！等仗打完了，我请你吃到吐！');
    await S.wait(0.4);
    S.stopMusic(1.2);
    await S.fadeOut(1.2);
    await S.narrate('然而，赢下一场仗，改变不了整场战争的结局。', { onBlack: true });
    G.world.stage = null;
    G.ui.reset();
    await S.video('s00b');
    G.flags.prologueDone = true;
  }

  // ---------------------------------------------------------------- 地图（序章版）
  G.STAGES.war_pro = Object.assign({}, G.STAGES.war, {
    id: 'war_pro',
    npcs: [
      { cid: 'katsura', id: 'katsura', x: 206, y: 171, facing: -1, anim: 'arms_crossed', talk: talkKatsura },
      { cid: 'sakamoto', id: 'sakamoto', x: 306, y: 186, facing: -1, anim: 'laugh', talk: talkSakamoto },
      { cid: 'townsman__v1', id: 'shishiA', name: '年轻的志士', x: 146, y: 192, facing: 1, anim: 'sit', talk: talkShishiA },
      { cid: 'townsman__v3', id: 'shishiB', name: '放哨的志士', x: 452, y: 172, facing: 1, talk: talkShishiB },
    ],
    hotspots: HOT,
    triggers: [
      { id: 'battle1', x0: 486, x1: 5000, run: battle1 },
      { id: 'battle2', x0: 918, x1: 5000, cond: () => G.flags.b1, run: battle2 },
    ],
  });

  // ---------------------------------------------------------------- 序章主流程
  G.STORY.prologue = async function (S) {
    await S.video('s00a');
    G.fadeAlpha = 0;
    await S.chapterCard('prologue');
    const p = new G.Actor('shiroyasha', 92, 182, { id: 'player', team: 'player', hp: 100, speed: 76, name: '银时' });
    G.world.player = p;
    G.fadeAlpha = 1;
    await S.setStage('war_pro', { x: 92, y: 182, facing: 1 });
    await S.run(async (S) => {
      S.letterbox(true);
      S.nameCard('shiroyasha');
      await S.narrate('十几年前——攘夷战争，某处战场。', { top: true, auto: 2.6 });
      const kat = S.actor('katsura');
      kat.idleAnim = 'idle';
      await S.walk(kat, 128, 178, { speed: 52 });
      S.face(kat, p);
      S.face(p, kat);
      await S.say('katsura', '银时，天人的部队又在河对岸集结了。');
      await S.say('shiroyasha', '……又来？那帮家伙是蟑螂吗，打完一窝又冒出一窝。');
      await S.say('katsura', '斥候说，这次带队的是天人的一个部队长。高杉带着鬼兵队守右翼，坂本盯着补给线。');
      await S.say('katsura', '正面……就交给我们了。');
      await S.say('shiroyasha', '知道了知道了。打完这一仗，我要吃红豆饭。不对，要甜的，很甜很甜的那种。');
      await S.say('katsura', '战场上哪来的甜食。');
      await S.say('shiroyasha', '所以才要早点打完啊，假发。');
      S.emote(kat, '!!', 0.8, '#ff6a4a');
      S.sfx('vein', 0.8);
      await S.say('katsura', '不是假发，是桂！', { expr: 'angry' });
      S.nameCard('katsura');
      await S.walk(kat, 206, 171, { speed: 52 });
      kat.idleAnim = 'arms_crossed';
      kat.play('arms_crossed');
      kat.facing = -1;
      S.letterbox(false);
      S.hint(G.touch && G.touch.on
        ? '左下角方向盘移动；靠近人或东西按 E 对话、调查。准备好了就往右走，出营地。'
        : '←→↑↓ / WASD 移动；靠近人或东西按 Enter 对话、调查。准备好了就往右走，出营地。', 8);
    });
    await S.until(() => G.flags.prologueDone);
  };
})();
