// 启动：载入资源 → 标题画面（从序章开始 / 选择章节 / 操作说明）→ 章节流程；暂停菜单；回标题；章末
'use strict';
(function () {
  const G = window.G;
  G.runId = 0;

  // 章节表：end / next 是这一章打完、后面还没有章节时，章末画面上的两行字
  G.CHAPTERS = [
    { key: 'prologue', title: '序章　白夜叉', run: (S) => G.STORY.prologue(S), end: '序章　完', next: '下一章：万事屋阿银' },
    { key: 'ch1', title: '第一章　万事屋阿银', run: (S) => G.STORY.chapter1(S), end: '第一章　完', next: '下一章：新八登场' },
    { key: 'ch2', title: '第二章　新八登场', run: (S) => G.STORY.chapter2(S), end: '第二章　完', next: '下一章：神乐与定春' },
    { key: 'ch3', title: '第三章　神乐与定春', run: (S) => G.STORY.chapter3(S), end: '第三章　完', next: '下一章：真选组' },
    { key: 'ch4', title: '第四章　真选组', run: (S) => G.STORY.chapter4(S), end: '第四章　完', next: '下一章：桂与伊丽莎白' },
    { key: 'ch5', title: '第五章　桂与伊丽莎白', run: (S) => G.STORY.chapter5(S), end: '第五章　完', next: '下一章：日常' },
    { key: 'ch6', title: '第六章　日常', run: (S) => G.STORY.chapter6(S), end: '第六章　完', next: '下一章：红樱篇' },
    { key: 'ch7', title: '第七章　红樱篇', run: (S) => G.STORY.chapter7(S), end: '第七章　完', next: '下一章：真选组动乱篇' },
    { key: 'ch8', title: '第八章　真选组动乱篇', run: (S) => G.STORY.chapter8(S), end: '第八章　完', next: '下一章：吉原炎上篇' },
    { key: 'ch9', title: '第九章　吉原炎上篇', run: (S) => G.STORY.chapter9(S), end: '第九章　完', next: '下一章：将军暗杀篇' },
    { key: 'ch10', title: '第十章　将军暗杀篇', run: (S) => G.STORY.chapter10(S), end: '第十章　完', next: '下一章：松阳老师' },
    { key: 'ch11', title: '第十一章　松阳老师', run: (S) => G.STORY.chapter11(S), end: '第十一章　完', next: '下一章：洛阳决战·离别' },
    { key: 'ch12', title: '第十二章　洛阳决战·离别', run: (S) => G.STORY.chapter12(S), end: '第十二章　完', next: '下一章：银之魂篇' },
    { key: 'ch13', title: '第十三章　银之魂篇', run: (S) => G.STORY.chapter13(S), end: '第十三章　完', next: '下一章：终章　两年后' },
    { key: 'ch14', title: '终章　两年后', run: (S) => G.STORY.chapter14(S), end: '终章　完', next: '全剧终　感谢游玩！' },
  ];
  const HELP = [
    ['移动', '← → ↑ ↓ / W A S D'],
    ['对话 / 调查', 'Enter / 空格 / E（靠近人或东西）'],
    ['推进对话', 'Enter / 空格 / J'],
    ['攻击', 'J / Z（连按三连击）'],
    ['跳跃', 'K / X（空中按 J = 跳斩）'],
    ['防御', '按住 L / C（挡住正面的攻击）'],
    ['暂停', 'Esc'],
  ];
  // 手机 / 平板（屏幕上有按键）时的操作说明：按键名字和屏幕上的按钮一致
  const HELP_TOUCH = [
    ['移动', '左下角的方向盘（按住滑动）'],
    ['对话 / 调查', 'E（靠近人或东西）'],
    ['推进对话', '点一下屏幕任意处'],
    ['攻击', 'J（连点三连击）'],
    ['跳跃', 'K（空中点 J = 跳斩）'],
    ['防御', '按住 L（挡住正面的攻击）'],
    ['暂停', '右上角的暂停钮'],
  ];
  const touchOn = () => !!(G.touch && G.touch.on);
  const helpLines = () => (touchOn() ? HELP_TOUCH : HELP);

  // ---------------------------------------------------------------- 游戏中
  G.worldScene = {
    name: 'world',
    get frozen() { return !!G.ui.menu; },
    update(dt) {
      if (G.ui.menu) { G.ui.update(dt); return; }
      if (G.input.hit('pause') && !G.ui.chapter) { G.input.consume('pause'); openPause(); return; }
      G.world.update(dt);
      G.ui.update(dt);
    },
    draw(g) { G.world.draw(g); G.ui.draw(g); },
  };
  async function openPause() {
    let idx = 0;
    for (;;) {
      // 手机 / 平板上多一项“按键大小”（小 / 中 / 大，点一下换一档，记在这台设备里）
      const items = [['继续游戏', 'resume'], ['操作说明', 'help']];
      if (touchOn()) items.push([`按键大小：${G.touch.sizeName()}`, 'size']);
      items.push(['回到标题', 'title']);
      const r = await G.ui.openMenu('暂停', items.map((x) => x[0]), { escIndex: 0, idx });
      const act = items[r][1];
      idx = r;
      if (act === 'help') { await G.ui.openMenu('操作说明', helpLines().map(([a, b]) => `${a}：${b}`), { escIndex: 0 }); continue; }
      if (act === 'size') { G.touch.cycleSize(); continue; }
      if (act === 'title') G.goTitle();
      return;
    }
  }

  function resetWorld() {
    G.timers = []; G.waiters = [];
    G.S.busy = false;
    G.ui.reset(); G.fx.clear();
    G.world.stage = null; G.world.player = null; G.world.combat = false; G.world.free = false;
    G.world.anims = []; G.world.ticks = []; G.world.shots = []; G.world.zoom = null;
    G.fadeAlpha = 0; G.flashAlpha = 0; G.hitStop = 0; G.impactT = 0; G.screenFilter = null;
  }

  G.playFrom = async function (idx) {
    const my = ++G.runId;
    G.flags = {};
    resetWorld();
    G.setScene(G.worldScene);
    for (let i = idx; i < G.CHAPTERS.length; i++) {
      G.world.free = false;      // 章节切换（标题卡、过场）期间不交操作
      G.lastChapter = i;
      await G.CHAPTERS[i].run(G.S);
      if (my !== G.runId) return;
      G.flags = {};
    }
    if (my !== G.runId) return;
    G.world.stage = null;
    G.ui.reset();
    G.fadeAlpha = 0;
    G.setScene(endScene);
  };

  G.goTitle = function () {
    G.runId++;
    resetWorld();
    G.setScene(titleScene);
  };

  // ---------------------------------------------------------------- 章末
  const endScene = {
    name: 'end',
    t: 0,
    enter() { this.t = 0; G.audio.music('ending', 1.0); },
    update(dt) {
      this.t += dt;
      if (this.t > 1.5 && (G.input.okHit() || G.input.hit('pause'))) { G.input.consumeOk(); G.goTitle(); }
    },
    draw(g) {
      const ch = G.CHAPTERS[G.lastChapter == null ? G.CHAPTERS.length - 1 : G.lastChapter];
      g.fillStyle = '#0b0a12'; g.fillRect(0, 0, G.W, G.H);
      const a = Math.min(1, this.t / 1.0);
      g.globalAlpha = a;
      G.f16.draw(g, ch.end, G.W / 2, 74, '#ffe9a8', { align: 'center', outline: '#2a1a10' });
      G.f12.draw(g, ch.next, G.W / 2, 104, '#cfc8dc', { align: 'center' });
      G.f12.draw(g, '原作：空知英秋《银魂》｜本作为同人像素致敬作品', G.W / 2, 150, '#8a8498', { align: 'center' });
      if (this.t > 1.5 && Math.floor(G.realTime * 2) % 2 === 0) G.f12.draw(g, touchOn() ? '点一下屏幕回到标题' : '按 Enter 回到标题', G.W / 2, 178, '#fff', { align: 'center' });
      g.globalAlpha = 1;
    },
  };

  // ---------------------------------------------------------------- 标题
  const MENU = ['从序章开始', '选择章节', '操作说明'];
  const titleScene = {
    name: 'title',
    idx: 0, t: 0, mode: 'main', petals: [],
    enter() {
      this.t = 0; this.mode = 'main'; this.idx = 0;
      // 标题音乐：用户提供的 title_song（assets/audio/user/），没有就用原工程的 title
      G.audio.music(G.D.audio.music.title_song ? 'title_song' : 'title', 0.8);
      this.petals = Array.from({ length: 26 }, () => ({ x: G.rand(0, G.W), y: G.rand(-G.H, G.H), v: G.rand(10, 22), s: G.rand(0, 6) }));
    },
    options() { return this.mode === 'chapters' ? [...G.CHAPTERS.map((c) => c.title), '返回'] : MENU; },
    // 点在第几项上（画面坐标），点空了返回 -1：几何要和 draw 里画的一致
    tapRow(t) {
      const opts = this.options();
      if (this.mode === 'chapters') {
        const N = 10, start = G.clamp(this.idx - 4, 0, Math.max(0, opts.length - N));
        const k = Math.floor((t.y - 40) / 15);
        return t.x >= 72 && t.x <= 312 && k >= 0 && k < Math.min(N, opts.length - start) ? start + k : -1;
      }
      const i = Math.floor((t.y - 143) / 18);
      return t.x >= 80 && t.x <= 304 && i >= 0 && i < opts.length ? i : -1;
    },
    update(dt) {
      this.t += dt;
      for (const p of this.petals) { p.y += p.v * dt; p.x += Math.sin(this.t * 1.3 + p.s) * 8 * dt; if (p.y > G.H + 4) { p.y = -4; p.x = G.rand(0, G.W); } }
      const I = G.input;
      if (this.mode === 'help') {
        if (I.okHit() || I.hit('pause') || I.hit('back')) { I.consumeOk(); I.consume('pause'); this.mode = 'main'; G.audio.sfx('pop', 0.5); }
        return;
      }
      const opts = this.options();
      if (I.tap) {        // 触屏 / 鼠标：点中某一项 = 选中并确认；点在空处不算
        const row = this.tapRow(I.tap);
        if (row >= 0) this.idx = row; else I.consume('ok');
      }
      if (I.hit('up')) { this.idx = (this.idx + opts.length - 1) % opts.length; G.audio.sfx('blip', 0.5, 1.4); }
      if (I.hit('down')) { this.idx = (this.idx + 1) % opts.length; G.audio.sfx('blip', 0.5, 1.4); }
      if (this.mode === 'chapters' && (I.hit('pause') || I.hit('back'))) { I.consume('pause'); this.mode = 'main'; this.idx = 1; G.audio.sfx('pop', 0.5); return; }
      if (!I.okHit()) return;
      I.consumeOk();
      if (this.mode === 'main') {
        G.audio.sfx('title_hit', 0.6);
        if (this.idx === 0) { G.audio.stopMusic(0.6); G.playFrom(0); }
        else if (this.idx === 1) { this.mode = 'chapters'; this.idx = 0; }
        else this.mode = 'help';
        return;
      }
      if (this.idx >= G.CHAPTERS.length) { this.mode = 'main'; this.idx = 1; G.audio.sfx('pop', 0.5); return; }
      G.audio.sfx('title_hit', 0.6);
      G.audio.stopMusic(0.6);
      G.playFrom(this.idx);
    },
    draw(g) {
      const bg = G.image(G.D.bg.title.image);
      g.drawImage(bg, 0, 0);
      g.fillStyle = 'rgba(10,8,24,0.30)'; g.fillRect(0, 0, G.W, G.H);
      for (const p of this.petals) { g.fillStyle = (p.s | 0) % 2 ? '#ffc4d8' : '#ff9ec0'; g.fillRect(Math.round(p.x), Math.round(p.y), 2, 1); }
      if (this.mode === 'chapters') {      // 章节多了放不下：单独一页，一次显示 10 行，跟着光标滚
        const opts = this.options(), N = 10, start = G.clamp(this.idx - 4, 0, Math.max(0, opts.length - N));
        g.fillStyle = 'rgba(10,8,24,0.45)'; g.fillRect(0, 0, G.W, G.H);
        G.f16.draw(g, '选择章节', G.W / 2, 12, '#ffe9a8', { align: 'center', outline: '#1a1020' });
        G.box(g, 72, 36, 240, N * 15 + 10, { fill: 'rgba(14,12,26,0.78)', border: '#ffd34a' });
        opts.slice(start, start + N).forEach((m, k) => {
          const i = start + k, sel = i === this.idx, y = 42 + k * 15;
          if (sel) { g.fillStyle = 'rgba(255,211,74,0.18)'; g.fillRect(78, y - 2, 228, 15); }
          G.f12.draw(g, (sel ? '► ' : '') + m + (sel ? ' ◄' : ''), G.W / 2, y, sel ? '#ffe14a' : '#e8e2f0', { align: 'center', outline: '#14101c' });
        });
        if (start > 0) G.f12.draw(g, '▲', G.W / 2, 27, '#ffd34a', { align: 'center' });
        if (start + N < opts.length) G.f12.draw(g, '▼', G.W / 2, 36 + N * 15 + 9, '#ffd34a', { align: 'center' });
        G.f12.draw(g, '原作：空知英秋《银魂》｜同人像素致敬作品', G.W / 2, 204, 'rgba(255,255,255,0.7)', { align: 'center', outline: 'rgba(0,0,0,0.6)' });
        return;
      }
      const logo = G.image(G.D.ui.logo), rib = G.image(G.D.ui.ribbon);
      const bob = Math.round(Math.sin(this.t * 1.6) * 1.5);
      g.drawImage(logo, Math.round((G.W - logo.width) / 2), 10 + bob);
      g.drawImage(rib, Math.round((G.W - rib.width) / 2), 104);
      G.f12.draw(g, '～ 游 戏 版 ～', G.W / 2, 124, '#fff2c8', { align: 'center', outline: '#2a1420' });
      if (this.mode === 'help') {
        G.box(g, 46, 40, 292, 150, { border: '#ffd34a' });
        G.f16.draw(g, '操作说明', G.W / 2, 48, '#ffe9a8', { align: 'center', outline: '#1a1020' });
        helpLines().forEach(([a, b], i) => {
          G.f12.draw(g, a, 64, 74 + i * 15, '#ffd34a');
          G.f12.draw(g, b, 140, 74 + i * 15, '#fff');
        });
        G.f12.draw(g, touchOn() ? '点一下屏幕返回' : '按 Enter 返回', G.W / 2, 176, '#9a93a8', { align: 'center' });
        return;
      }
      const opts = this.options();
      const y0 = this.mode === 'chapters' ? 140 : 146, gap = this.mode === 'chapters' ? 15 : 18;
      if (this.mode === 'chapters') { g.fillStyle = 'rgba(10,8,24,0.55)'; g.fillRect(96, y0 - 6, 192, opts.length * gap + 8); }
      opts.forEach((m, i) => {
        const sel = i === this.idx;
        const y = y0 + i * gap;
        if (sel) { const w = G.f12.width(m) + 36; g.fillStyle = 'rgba(14,16,28,0.72)'; g.fillRect(Math.round(G.W / 2 - w / 2), y - 3, w, 17); }
        G.f12.draw(g, (sel ? '► ' : '') + m + (sel ? ' ◄' : ''), G.W / 2, y, sel ? '#ffe14a' : '#e8e2f0', { align: 'center', outline: '#14101c' });
      });
      G.f12.draw(g, '原作：空知英秋《银魂》｜同人像素致敬作品', G.W / 2, 204, 'rgba(255,255,255,0.7)', { align: 'center', outline: 'rgba(0,0,0,0.6)' });
    },
  };

  // ---------------------------------------------------------------- 启动
  function collectImages(o, out) {
    if (typeof o === 'string') { if (/\.png$/i.test(o)) out.add(o); return out; }
    if (Array.isArray(o)) { for (const v of o) collectImages(v, out); return out; }
    if (o && typeof o === 'object') for (const k in o) collectImages(o[k], out);
    return out;
  }
  (async function boot() {
    const loading = document.getElementById('loading');
    if (!G.D || !G.D.chars) { loading.textContent = '缺少 data.js：先运行 tools/build_assets.py'; return; }
    const srcs = [...collectImages(G.D, new Set())];
    await G.preload(srcs, (d, n) => { loading.textContent = `载入中…… ${d} / ${n}`; });
    G.initFonts();
    await G.preload([G.D.font['12'].image, G.D.font['16'].image]);
    loading.remove();
    G.setScene(titleScene);
    G.start();
    // 浏览器要求先有一次按键 / 点击才能出声：第一次按键后补放标题音乐
    // 手机上手指“抬起来”（pointerup / touchend / click）才算数，按下去不算，所以一直试到放出声为止
    const kick = () => {
      const el = G.audio.el;
      if (!el || !el.paused) { if (el) ['keydown', 'pointerdown', 'pointerup', 'touchend', 'click'].forEach((n) => removeEventListener(n, kick, true)); return; }
      el.play().catch(() => {});
    };
    ['keydown', 'pointerdown', 'pointerup', 'touchend', 'click'].forEach((n) => addEventListener(n, kick, true));
  })();
})();
