// 地图：几何、道具、障碍物（NPC、调查点、触发区在各章文件里加）
'use strict';
(function () {
  const G = window.G;
  G.STAGES = {};
  G.STORY = {};
  // 对话框上显示的名字（图集里的名字太正式，或者同一个人换了称呼）
  G.NAMES = {
    shiroyasha: '银时', gintoki: '银时', katsura: '桂', sakamoto: '坂本', otose: '登势',
    amanto_pig: '天人', amanto_cat: '天人', harusame: '天人', townsman: '路人', townswoman: '路人', shinpachi: '新八', otae: '阿妙',
  };

  // 序章：攘夷战争的战场（黄昏）。左边是志士的营地，右边是战场
  G.STAGES.war = {
    id: 'war', bg: 'war', x0: 0, x1: 1300, yMin: 162, yMax: 198, music: 'prologue',
    props: [
      { type: 'image', image: 'assets/bg/war/tent.png', x: 56, y: 163, ax: 34, ay: 40 },
      { type: 'banner', kind: 'joui', x: 16, y: 165 },
      { type: 'banner', kind: 'joui', x: 108, y: 164, phase: 3 },
      { type: 'campfire', x: 172, y: 186 },
      { type: 'image', image: 'assets/bg/war/tent.png', x: 262, y: 163, ax: 34, ay: 40 },
      { type: 'banner', kind: 'joui', x: 352, y: 164, phase: 5 },
      { type: 'banner', kind: 'joui', x: 438, y: 163, phase: 1 },
      { type: 'banner', kind: 'joui_torn', x: 612, y: 164 },
      { type: 'banner', kind: 'joui_torn', x: 806, y: 165, phase: 2 },
      { type: 'banner', kind: 'amanto', x: 996, y: 164 },
      { type: 'banner', kind: 'amanto', x: 1210, y: 163, phase: 4 },
    ],
  };

  // 第一章：万事屋事务所（固定镜头）。桌子前景会盖住站在它后面的人
  G.STAGES.office = {
    id: 'office', kind: 'office', bg: 'office', x0: 0, x1: 384, yMin: 160, yMax: 200, music: 'yorozuya',
    props: [{ type: 'image', image: 'assets/bg/office/fg.png', screen: true, x: 0, y: 0, depth: 167 }],
    obstacles: [
      { x0: 54, x1: 126, y0: 100, y1: 166 },    // 左沙发
      { x0: 148, x1: 236, y0: 100, y1: 168 },   // 矮桌
      { x0: 258, x1: 330, y0: 100, y1: 166 },   // 右沙发
    ],
  };

  // 第一章：歌舞伎町大街（白天）。万事屋 / 登势酒馆在 290–450
  G.STAGES.street = {
    id: 'street', bg: 'street', x0: 0, x1: 1150, yMin: 162, yMax: 198, music: 'yorozuya',
    props: [],
  };

  G.STAGES.restaurant_ch2 = { id: 'restaurant_ch2', bg: 'restaurant', x0: 0, x1: 384, yMin: 150, yMax: 190, music: 'comedy', props: [], obstacles: [{ x0: 22, x1: 58, y0: 82, y1: 160 }, { x0: 205, x1: 350, y0: 130, y1: 160 }] };
  G.STAGES.dojo_gate_ch2 = { id: 'dojo_gate_ch2', bg: 'dojo_gate', x0: 0, x1: 640, yMin: 158, yMax: 198, music: 'tension', props: [] };
  G.STAGES.dojo_ch2 = { id: 'dojo_ch2', bg: 'dojo', x0: 0, x1: 384, yMin: 150, yMax: 190, music: 'yorozuya', props: [] };
})();
