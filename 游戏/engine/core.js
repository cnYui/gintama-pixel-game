// 核心：常量、工具、画布缩放、输入、音频、主循环、计时器
'use strict';
(function () {
  const G = (window.G = {});
  G.W = 384;
  G.H = 216;
  G.D = window.GAME_DATA || {};
  G.time = 0;          // 游戏时间（暂停时不走）
  G.realTime = 0;
  G.hitStop = 0;       // 命中顿帧
  G.fadeAlpha = 0;     // 全屏黑幕
  G.flashAlpha = 0;    // 全屏白闪
  G.shakeT = 0;
  G.shakeMag = 0;
  G.flashColor = '#fff';
  G.impactT = 0;       // 冲击帧（原片 fx.impact_frame：整屏变成黑白两色），剩余秒数
  G.screenFilter = null;   // 整屏滤镜（CSS filter 写法），比如回忆用 'sepia(0.85)'

  // ---------------------------------------------------------------- 工具
  G.clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
  G.lerp = (a, b, t) => a + (b - a) * t;
  G.mod = (a, n) => ((a % n) + n) % n;
  G.rand = (a = 0, b = 1) => a + Math.random() * (b - a);
  G.pick = (arr) => arr[Math.floor(Math.random() * arr.length)];
  G.sign = (v) => (v < 0 ? -1 : v > 0 ? 1 : 0);
  G.rgb = (c) => (Array.isArray(c) ? `rgb(${c[0]},${c[1]},${c[2]})` : c);
  // 固定种子的随机数（mulberry32）：樱花、集中线这类每次画都要一样的随机
  G.prng = (seed) => {
    let a = (seed * 2654435761) >>> 0 || 1;
    return () => {
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };
  G.ease = {
    out: (t) => 1 - Math.pow(1 - t, 3),
    in: (t) => t * t * t,
    inOut: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
    outBack: (t) => { const s = 1.70158; t -= 1; return t * t * ((s + 1) * t + s) + 1; },
  };

  // ---------------------------------------------------------------- 图片
  G.images = {};
  G.image = function (src) {
    let im = G.images[src];
    if (!im) { im = new Image(); im.src = src; G.images[src] = im; }
    return im;
  };
  G.ready = (im) => im && im.complete && im.naturalWidth > 0;
  G.preload = function (srcs, onProgress) {
    let done = 0;
    return Promise.all(srcs.map((s) => new Promise((res) => {
      const im = G.image(s);
      const fin = () => { done++; if (onProgress) onProgress(done, srcs.length); res(); };
      if (G.ready(im)) fin();
      else {
        im.addEventListener('load', fin, { once: true });
        im.addEventListener('error', () => { console.warn('缺图', s); fin(); }, { once: true });
      }
    })));
  };

  // ---------------------------------------------------------------- 画布：低分辨率画面 → 整数倍放大
  G.screen = document.getElementById('screen');
  G.sctx = G.screen.getContext('2d');
  G.view = document.createElement('canvas');
  G.view.width = G.W;
  G.view.height = G.H;
  G.g = G.view.getContext('2d');
  G.scale = 1;
  G.resize = function () {
    const dpr = window.devicePixelRatio || 1;
    const s = Math.max(1, Math.floor(Math.min((innerWidth * dpr) / G.W, (innerHeight * dpr) / G.H)));
    G.scale = s;
    G.screen.width = G.W * s;
    G.screen.height = G.H * s;
    G.screen.style.width = (G.W * s) / dpr + 'px';
    G.screen.style.height = (G.H * s) / dpr + 'px';
    G.sctx.imageSmoothingEnabled = false;
  };
  addEventListener('resize', G.resize);
  addEventListener('orientationchange', () => setTimeout(G.resize, 250));    // 手机转屏：尺寸要过一会儿才稳
  if (window.visualViewport) visualViewport.addEventListener('resize', G.resize);
  G.resize();
  // 屏幕上的一点（clientX / clientY）→ 游戏画面的坐标（0..384 × 0..216，点在画面外就是负数或更大）
  G.toGame = (e) => {
    const r = G.screen.getBoundingClientRect();
    return { x: ((e.clientX - r.left) * G.W) / r.width, y: ((e.clientY - r.top) * G.H) / r.height };
  };

  // ---------------------------------------------------------------- 输入
  const KEYMAP = {
    ArrowLeft: 'left', KeyA: 'left', ArrowRight: 'right', KeyD: 'right',
    ArrowUp: 'up', KeyW: 'up', ArrowDown: 'down', KeyS: 'down',
    KeyJ: 'attack', KeyZ: 'attack', KeyK: 'jump', KeyX: 'jump', KeyL: 'guard', KeyC: 'guard',
    Enter: 'ok', NumpadEnter: 'ok', Space: 'ok', KeyE: 'ok',
    Escape: 'pause', KeyP: 'pause', Backspace: 'back',
  };
  G.input = {
    down: {},
    hits: {},
    tap: null,       // 这一步里有人点了画面：{ x, y }（游戏画面坐标）。菜单靠它判断点中了哪一项
    isDown(a) { return !!this.down[a]; },
    hit(a) { return !!this.hits[a]; },
    consume(a) { this.hits[a] = false; },
    // 对话框 / 菜单里：确认键（回车、空格、E、J 都算）
    okHit() { return this.hit('ok') || this.hit('attack'); },
    consumeOk() { this.consume('ok'); this.consume('attack'); },
    endStep() { this.hits = {}; this.tap = null; },
  };
  addEventListener('keydown', (e) => {
    const a = KEYMAP[e.code];
    G.audio.unlock();
    if (!a) return;
    if (!G.input.down[a]) G.input.hits[a] = true;
    G.input.down[a] = true;
    e.preventDefault();
  });
  addEventListener('keyup', (e) => {
    const a = KEYMAP[e.code];
    if (a) { G.input.down[a] = false; e.preventDefault(); }
  });
  addEventListener('blur', () => { G.input.down = {}; });
  G.screen.addEventListener('pointerdown', (e) => { G.audio.unlock(); G.input.hits.ok = true; G.input.tap = G.toGame(e); });

  // ---------------------------------------------------------------- 音频（HTMLAudio：双击打开 html 也能播）
  G.audio = {
    unlocked: false,
    el: null,
    name: null,
    musicVol: 0.42,
    sfxVol: 0.75,
    fades: [],
    pools: {},
    unlock() { this.unlocked = true; },
    music(name, fade = 0.8) {
      if (this.name === name) return;
      const src = G.D.audio && G.D.audio.music[name];
      if (this.el) this.fadeTo(this.el, 0, fade, true);
      this.el = null;
      this.name = name;
      if (!src) return;
      const el = new Audio(src);
      el.loop = true;
      el.volume = 0;
      el.play().catch(() => {});
      this.el = el;
      this.fadeTo(el, this.musicVol, fade);
    },
    stopMusic(fade = 0.8) {
      if (this.el) this.fadeTo(this.el, 0, fade, true);
      this.el = null;
      this.name = null;
    },
    duck(on) { if (this.el) this.fadeTo(this.el, on ? this.musicVol * 0.35 : this.musicVol, 0.3); },
    fadeTo(el, to, dur, stopAfter) {
      this.fades = this.fades.filter((f) => f.el !== el);
      this.fades.push({ el, from: el.volume, to, t: 0, dur: Math.max(0.01, dur), stopAfter });
    },
    update(dt) {
      this.fades = this.fades.filter((f) => {
        f.t += dt;
        const k = Math.min(1, f.t / f.dur);
        f.el.volume = G.clamp(G.lerp(f.from, f.to, k), 0, 1);
        if (k >= 1) { if (f.stopAfter) f.el.pause(); return false; }
        return true;
      });
    },
    sfx(name, vol = 1, rate = 1) {
      const src = G.D.audio && G.D.audio.sfx[name];
      if (!src) return;
      const pool = this.pools[name] || (this.pools[name] = []);
      let el = pool.find((a) => a.paused || a.ended);
      if (!el) {
        if (pool.length >= 6) el = pool[0];
        else { el = new Audio(src); pool.push(el); }
      }
      try { el.currentTime = 0; } catch (e) { /* 还没加载 */ }
      el.volume = G.clamp(vol * this.sfxVol, 0, 1);
      el.preservesPitch = false;
      el.mozPreservesPitch = false;
      el.webkitPreservesPitch = false;
      el.playbackRate = rate;
      el.play().catch(() => {});
    },
  };

  // ---------------------------------------------------------------- 计时器 / 等待（剧情脚本用）
  G.timers = [];
  G.waiters = [];
  G.wait = (sec) => new Promise((res) => G.timers.push({ t: sec, res }));
  G.until = (fn) => new Promise((res) => G.waiters.push({ fn, res }));
  G.shake = (mag = 2, dur = 0.25) => { G.shakeMag = Math.max(G.shakeMag, mag); G.shakeT = Math.max(G.shakeT, dur); };

  // ---------------------------------------------------------------- 场景 + 主循环（固定 60 Hz 逻辑）
  G.scene = null;
  G.setScene = (s) => { if (G.scene && G.scene.leave) G.scene.leave(); G.scene = s; if (s && s.enter) s.enter(); };
  G.overlays = [];   // 每帧最后画的东西（淡入淡出、白闪）

  const STEP = 1 / 60;
  let acc = 0;
  let last = performance.now();
  function update(dt) {
    G.realTime += dt;
    G.audio.update(dt);
    if (G.ui && G.ui.updateGlobal) G.ui.updateGlobal(dt);
    if (G.impactT > 0) G.impactT -= dt;
    if (G.hitStop > 0) { G.hitStop -= dt; G.input.endStep(); return; }
    if (G.scene && G.scene.update) G.scene.update(dt);
    if (!(G.scene && G.scene.frozen)) {
      G.time += dt;
      if (G.shakeT > 0) { G.shakeT -= dt; if (G.shakeT <= 0) G.shakeMag = 0; }
      G.timers = G.timers.filter((tm) => { tm.t -= dt; if (tm.t <= 0) { tm.res(); return false; } return true; });
    }
    G.waiters = G.waiters.filter((w) => { if (w.fn()) { w.res(); return false; } return true; });
    G.input.endStep();
  }
  function render() {
    const g = G.g;
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.globalAlpha = 1;
    g.globalCompositeOperation = 'source-over';
    g.imageSmoothingEnabled = false;
    g.fillStyle = '#000';
    g.fillRect(0, 0, G.W, G.H);
    if (G.scene && G.scene.draw) G.scene.draw(g);
    if (G.flashAlpha > 0) { g.globalAlpha = G.flashAlpha; g.fillStyle = G.flashColor; g.fillRect(0, 0, G.W, G.H); g.globalAlpha = 1; }
    if (G.fadeAlpha > 0) { g.globalAlpha = G.fadeAlpha; g.fillStyle = '#000'; g.fillRect(0, 0, G.W, G.H); g.globalAlpha = 1; }
    if (G.ui && G.ui.drawTop) G.ui.drawTop(g);
    const s = G.sctx;
    s.imageSmoothingEnabled = false;
    // 冲击帧用画布滤镜做（file:// 打开时画布读不了像素，只能这样）：灰度 → 拉满对比 → 反相，亮的变黑、暗的变白
    // 整屏滤镜：G.screenFilter（回忆的泛黄 sepia 等）
    const filt = G.impactT > 0 ? 'grayscale(1) contrast(12) invert(1)' : G.screenFilter;
    if (filt) s.filter = filt;
    s.drawImage(G.view, 0, 0, G.screen.width, G.screen.height);
    if (filt) s.filter = 'none';
  }
  function frame(now) {
    const dt = Math.min(0.1, (now - last) / 1000);
    last = now;
    if (G.suspended) { acc = 0; render(); requestAnimationFrame(frame); return; }   // 手机竖着拿的时候停住（touch.js 设的）
    acc += dt;
    let n = 0;
    while (acc >= STEP && n < 6) { update(STEP); acc -= STEP; n++; }
    if (n === 6) acc = 0;
    render();
    requestAnimationFrame(frame);
  }
  G.start = () => requestAnimationFrame((t) => { last = t; requestAnimationFrame(frame); });

  // 黑幕 / 白闪（返回 Promise）
  G.fade = (to, dur = 0.5) => {
    const from = G.fadeAlpha;
    let t = 0;
    return new Promise((res) => {
      const w = { fn: () => { t += 1 / 60; G.fadeAlpha = G.lerp(from, to, Math.min(1, t / dur)); return t >= dur; }, res };
      G.waiters.push(w);
    });
  };
  G.flash = (dur = 0.25, peak = 1, color = '#fff') => {
    G.flashColor = color;
    let t = 0;
    G.waiters.push({ fn: () => { t += 1 / 60; G.flashAlpha = peak * Math.max(0, 1 - t / dur); return t >= dur; }, res: () => {} });
  };
})();
