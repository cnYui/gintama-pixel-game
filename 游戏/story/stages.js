// 地图：几何、道具、障碍物（NPC、调查点、触发区在各章文件里加）
'use strict';
(function () {
  const G = window.G;
  G.STAGES = {};
  G.STORY = {};
  // 对话框上显示的名字（图集里的名字太正式，或者同一个人换了称呼）
  G.NAMES = {
    shiroyasha: '银时', gintoki: '银时', katsura: '桂', sakamoto: '坂本', otose: '登势',
    amanto_pig: '天人', amanto_cat: '天人', harusame: '天人', townsman: '路人', townswoman: '路人',
    shinpachi: '新八', shinpachi__apron: '新八', otae: '阿妙', townsman__chef: '店长',
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

  // 第二章：三张都是固定镜头的单屏地图（原片 s02 的布景，build_assets.py 的 build_bg_ch2 导出）
  // 家庭餐厅：吧台在后面（y < 160），人在吧台前面走；凳子 x = 226 / 304 / 334，坐着的人脚点 y = 150
  G.STAGES.restaurant = {
    id: 'restaurant', bg: 'restaurant', x0: 0, x1: 384, yMin: 162, yMax: 204, music: 'comedy', props: [],
  };
  // 志村道场门口（黄昏）：门在 x 138–238，门柱上挂着门牌，右边一棵樱花树
  G.STAGES.dojo_gate = {
    id: 'dojo_gate', bg: 'dojo_gate', x0: 0, x1: 384, yMin: 164, yMax: 204, music: 'tension', props: [],
  };
  // 道场里：坐垫在 x 104 / 150，木刀架在右边
  G.STAGES.dojo = {
    id: 'dojo', bg: 'dojo', x0: 0, x1: 384, yMin: 162, yMax: 204, music: 'comedy', props: [],
  };
})();
