// 启动：载入资源 → 标题画面（选章节 / 操作说明）→ 章节流程；暂停菜单；回标题
'use strict';
(function () {
  const G = window.G;
  G.runId = 0;

  G.CHAPTERS = [
    { key: 'prologue', title: '序章　白夜叉', run: (S) => G.STORY.prologue(S) },
    { key: 'ch1', title: '第一章　万事屋阿银', run: (S) => G.STORY.chapter1(S) },
    { key: 'ch2', title: '第二章　新八登场', run: (S) => G.STORY.chapter2(S) },
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

  // ---------------------------------------------------------------- 游戏中
  G.worldScene = {
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
    for (;;) {
      const r = await G.ui.openMenu('暂停', ['继续游戏', '操作说明', '回到标题'], { escIndex: 0 });
      if (r === 1) { await G.ui.openMenu('操作说明', HELP.map(([a, b]) => `${a}：${b}`), { escIndex: 0 }); continue; }
      if (r === 2) G.goTitle();
      return;
    }
  }

  G.playFrom = async function (idx) {
    const my = ++G.runId;
    G.flags = {};
    G.timers = []; G.waiters = [];
    G.S.busy = false;
    G.ui.reset(); G.fx.clear();
    G.world.stage = null; G.world.player = null; G.world.combat = false; G.world.free = false;
    G.fadeAlpha = 0;
    G.setScene(G.worldScene);
    for (let i = idx; i < G.CHAPTERS.length; i++) {
      G.world.free = false;      // 章节切换（标题卡、过场）期间不交操作
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
    G.timers = []; G.waiters = [];
    G.S.busy = false;
    G.ui.reset(); G.fx.clear();
    G.world.stage = null; G.world.player = null; G.world.combat = false; G.world.free = false;
    G.fadeAlpha = 0; G.flashAlpha = 0; G.hitStop = 0;
    G.setScene(titleScene);
  };

  // ---------------------------------------------------------------- 章末
  const endScene = {
    t: 0,
    enter() { this.t = 0; G.audio.music('ending', 1.0); },
    update(dt) {
      this.t += dt;
      if (this.t > 1.5 && (G.input.okHit() || G.input.hit('pause'))) { G.input.consumeOk(); G.goTitle(); }
    },
    draw(g) {
      g.fillStyle = '#0b0a12'; g.fillRect(0, 0, G.W, G.H);
      const a = Math.min(1, this.t / 1.0);
      g.globalAlpha = a;
      const done = G.completedChapter || '第一章';
      const next = done === '第二章' ? '下一章：神乐与定春（制作中）' : '下一章：新八登场';
      G.f16.draw(g, `${done}　完`, G.W / 2, 74, '#ffe9a8', { align: 'center', outline: '#2a1a10' });
      G.f12.draw(g, next, G.W / 2, 104, '#cfc8dc', { align: 'center' });
      G.f12.draw(g, '原作：空知英秋《银魂》｜本作为同人像素致敬作品', G.W / 2, 150, '#8a8498', { align: 'center' });
      if (this.t > 1.5 && Math.floor(G.realTime * 2) % 2 === 0) G.f12.draw(g, '按 Enter 回到标题', G.W / 2, 178, '#fff', { align: 'center' });
      g.globalAlpha = 1;
    },
  };

  // ---------------------------------------------------------------- 标题
  const MENU = ['从序章开始', '第一章　万事屋阿银', '第二章　新八登场', '操作说明'];
  const titleScene = {
    idx: 0, t: 0, help: false, petals: [],
    enter() {
      this.t = 0; this.help = false; this.idx = 0;
      // 标题音乐：用户提供的 title_song（assets/audio/user/），没有就用原工程的 title
      G.audio.music(G.D.audio.music.title_song ? 'title_song' : 'title', 0.8);
      this.petals = Array.from({ length: 26 }, () => ({ x: G.rand(0, G.W), y: G.rand(-G.H, G.H), v: G.rand(10, 22), s: G.rand(0, 6) }));
    },
    update(dt) {
      this.t += dt;
      for (const p of this.petals) { p.y += p.v * dt; p.x += Math.sin(this.t * 1.3 + p.s) * 8 * dt; if (p.y > G.H + 4) { p.y = -4; p.x = G.rand(0, G.W); } }
      const I = G.input;
      if (this.help) { if (I.okHit() || I.hit('pause') || I.hit('back')) { I.consumeOk(); this.help = false; G.audio.sfx('pop', 0.5); } return; }
      if (I.hit('up')) { this.idx = (this.idx + MENU.length - 1) % MENU.length; G.audio.sfx('blip', 0.5, 1.4); }
      if (I.hit('down')) { this.idx = (this.idx + 1) % MENU.length; G.audio.sfx('blip', 0.5, 1.4); }
      if (I.okHit()) {
        I.consumeOk();
        G.audio.sfx('title_hit', 0.6);
        if (this.idx === 3) { this.help = true; return; }
        G.audio.stopMusic(0.6);
        G.playFrom(this.idx === 0 ? 0 : this.idx);
      }
    },
    draw(g) {
      const bg = G.image(G.D.bg.title.image);
      g.drawImage(bg, 0, 0);
      g.fillStyle = 'rgba(10,8,24,0.30)'; g.fillRect(0, 0, G.W, G.H);
      for (const p of this.petals) { g.fillStyle = (p.s | 0) % 2 ? '#ffc4d8' : '#ff9ec0'; g.fillRect(Math.round(p.x), Math.round(p.y), 2, 1); }
      const logo = G.image(G.D.ui.logo), rib = G.image(G.D.ui.ribbon);
      const bob = Math.round(Math.sin(this.t * 1.6) * 1.5);
      g.drawImage(logo, Math.round((G.W - logo.width) / 2), 10 + bob);
      g.drawImage(rib, Math.round((G.W - rib.width) / 2), 104);
      G.f12.draw(g, '～ 游 戏 版 ～', G.W / 2, 124, '#fff2c8', { align: 'center', outline: '#2a1420' });
      if (this.help) {
        G.box(g, 46, 40, 292, 150, { border: '#ffd34a' });
        G.f16.draw(g, '操作说明', G.W / 2, 48, '#ffe9a8', { align: 'center', outline: '#1a1020' });
        HELP.forEach(([a, b], i) => {
          G.f12.draw(g, a, 64, 74 + i * 15, '#ffd34a');
          G.f12.draw(g, b, 140, 74 + i * 15, '#fff');
        });
        G.f12.draw(g, '按 Enter 返回', G.W / 2, 176, '#9a93a8', { align: 'center' });
        return;
      }
      MENU.forEach((m, i) => {
        const sel = i === this.idx;
        const y = 146 + i * 18;
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
    const kick = () => { if (G.audio.el && G.audio.el.paused) G.audio.el.play().catch(() => {}); };
    addEventListener('keydown', kick, { once: true });
    addEventListener('pointerdown', kick, { once: true });
  })();
})();
