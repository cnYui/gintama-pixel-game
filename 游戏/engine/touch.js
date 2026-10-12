// 触屏操作：屏幕上的方向盘、J / K / L / E 按钮、暂停、全屏。把手指的动作翻成键盘输入（G.input），游戏逻辑一行不用改。
// 长相和位置在 index.html 的 #tc 一段；这里管：什么时候出现、多指同时按、方向盘滑动、横屏提示、全屏、手机上的声音。
//   网址后面加 ?touch=1  强制显示（电脑上调试用）　?touch=0  强制不显示
// 点菜单 / 选项靠 G.input.tap（core.js 记点的位置，ui.js / main.js 判断点中了哪一项）。
'use strict';
(function () {
  const G = window.G;
  const I = G.input;
  const root = document.getElementById('tc');
  if (!root) return;
  const $ = (id) => document.getElementById(id);
  const param = new URLSearchParams(location.search).get('touch');
  const force = param === '1' ? true : param === '0' ? false : null;
  const ua = navigator.userAgent;
  const T = (G.touch = {
    on: false,
    ctx: '',            // 当前场景：explore / combat / menu / qte / story / title / end（按钮显示哪几个看它）
    haptic: true,       // 按下震一下（手机支持的话）
    ios: /iP(hone|ad|od)/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1),
    // 屏幕按键压在游戏画面上的范围（游戏画面坐标 0..384）：左下方向盘盖到 x < l；右下按钮从 x > r 起盖；右上暂停 / 全屏钮从 x > sys 起盖。
    // 按钮在黑边里（宽屏手机）时就是 0 / 384 / 384，没盖到画面。提示、选项框、计时靠它躲开按钮
    safe: { l: 0, r: G.W, sys: G.W },
  });
  const isCoarse = () => !!(window.matchMedia && matchMedia('(pointer: coarse)').matches) || /Android|Mobile|iP(hone|ad|od)/i.test(ua);

  // ---------------------------------------------------------------- 把按钮 / 方向翻成按键
  function setKey(a, on) {
    if (on) { if (!I.down[a]) I.hits[a] = true; I.down[a] = true; }
    else I.down[a] = false;
  }
  const buzz = (ms = 9) => { if (T.haptic && navigator.vibrate) { try { navigator.vibrate(ms); } catch (e) { /* 不支持就算了 */ } } };

  const el = {
    pad: $('tc-pad'), j: root.querySelector('.tc-j'), k: root.querySelector('.tc-k'), l: root.querySelector('.tc-l'),
    e: root.querySelector('.tc-e'), pause: $('tc-pause'), full: $('tc-full'),
  };
  const releasers = [];

  // 按钮：每个按钮自己记着哪几根手指按着它，多指（方向盘 + 攻击 + 跳）同时按没问题
  [el.j, el.k, el.l, el.e, el.pause].forEach((b) => {
    const a = b.dataset.key, ids = new Set();
    b.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      try { b.setPointerCapture(e.pointerId); } catch (err) { /* 合成事件没有对应的指针 */ }
      ids.add(e.pointerId);
      b.classList.add('on');
      G.audio.unlock();
      setKey(a, true);
      buzz();
    });
    const up = (e) => {
      if (!ids.delete(e.pointerId) || ids.size) return;
      b.classList.remove('on');
      setKey(a, false);
    };
    ['pointerup', 'pointercancel', 'lostpointercapture'].forEach((n) => b.addEventListener(n, up));
    releasers.push(() => { ids.clear(); b.classList.remove('on'); setKey(a, false); });
  });

  // 方向盘：手指落在盘上、滑到哪儿朝哪儿走；8 个方向，横竖方向的范围比斜向宽（这游戏主要往左右走）
  const knob = $('tc-knob');
  const arrows = {};
  el.pad.querySelectorAll('.arr').forEach((p) => { arrows[p.dataset.d] = p; });
  const AXIS = { right: 0, down: 90, left: 180, up: -90 };
  const padKeys = { left: false, right: false, up: false, down: false };
  let padId = null;
  function padSet(dir) {
    for (const a in padKeys) {
      const on = !!dir[a];
      if (on) setKey(a, true); else if (padKeys[a]) setKey(a, false);
      padKeys[a] = on;
      arrows[a].classList.toggle('on', on);
    }
  }
  function padMove(e) {
    const r = el.pad.getBoundingClientRect();
    const R = r.width / 2, dx = e.clientX - (r.left + R), dy = e.clientY - (r.top + R);
    const d = Math.hypot(dx, dy), lim = R * 0.45, k = d > lim ? lim / d : 1;
    knob.style.transform = `translate(${dx * k}px, ${dy * k}px)`;
    const dir = {};
    if (d >= R * 0.3) {
      const th = (Math.atan2(dy, dx) * 180) / Math.PI;
      for (const a in AXIS) {
        let diff = Math.abs(th - AXIS[a]) % 360;
        if (diff > 180) diff = 360 - diff;
        if (diff < (padKeys[a] ? 66 : 60)) dir[a] = true;      // 已经按着的方向多给 6 度，边界上不会来回跳
      }
    }
    padSet(dir);
  }
  el.pad.addEventListener('pointerdown', (e) => {
    if (padId != null) return;
    e.preventDefault();
    padId = e.pointerId;
    try { el.pad.setPointerCapture(e.pointerId); } catch (err) { /* 同上 */ }
    el.pad.classList.add('on');
    G.audio.unlock();
    padMove(e);
  });
  el.pad.addEventListener('pointermove', (e) => { if (e.pointerId === padId) padMove(e); });
  const padUp = (e) => {
    if (e && e.pointerId !== padId) return;
    padId = null;
    el.pad.classList.remove('on');
    knob.style.transform = '';
    padSet({});
  };
  ['pointerup', 'pointercancel', 'lostpointercapture'].forEach((n) => el.pad.addEventListener(n, padUp));
  releasers.push(() => padUp());

  // ---------------------------------------------------------------- 什么场景显示哪些按钮（1 = 亮，0.4 = 暗着但还能按，0 = 藏起来、手指能穿过去点到画面）
  const SHOW = {
    explore: { pad: 1, j: 0.4, k: 1, l: 0.4, e: 1, pause: 1 },     // 自由走动：J / L 暂时没用
    combat:  { pad: 1, j: 1, k: 1, l: 1, e: 0.4, pause: 1 },
    menu:    { pad: 1, j: 1, k: 0, l: 0, e: 1, pause: 1 },         // 菜单 / 选项：方向盘选、J 或 E 确认（也能直接点）
    qte:     { pad: 0, j: 1, k: 0, l: 0, e: 1, pause: 1 },         // 连按 / 看准时机：J（点屏幕任意处也行）
    story:   { pad: 0, j: 0, k: 0, l: 0, e: 0, pause: 1 },         // 对话 / 旁白：点屏幕任意处继续，按钮不挡字
    title:   { pad: 1, j: 1, k: 0, l: 0, e: 1, pause: 0 },
    end:     { pad: 0, j: 0, k: 0, l: 0, e: 0, pause: 0 },
  };
  function context() {
    const sc = G.scene && G.scene.name, U = G.ui;
    if (sc === 'title' || sc === 'end') return sc;
    if (sc === 'video') return 'story';
    if (!U) return 'explore';
    if (U.menu || U.choiceBox) return 'menu';
    if (U.dlg || U.narr || U.notice || U.chapter) return 'story';
    if (U.qte || U.waitKey) return 'qte';
    return G.world && G.world.combat ? 'combat' : 'explore';
  }
  const CAP = {   // 各场景下 J / E 按钮下面的小字
    j: { menu: '确认', title: '确认', qte: '连按' },
    e: { menu: '确认', title: '确认', qte: '确认' },
  };
  const caps = { j: el.j.querySelector('i'), e: el.e.querySelector('i') };
  const capDefault = { j: caps.j.textContent, e: caps.e.textContent };
  let lastKey = '';
  function refresh() {
    const c = context();
    const show = Object.assign({}, SHOW[c]);
    if (c === 'title' && G.scene.mode && G.scene.mode !== 'main') show.pause = 1;      // 选章节 / 说明页里，暂停钮 = 返回
    const key = c + (show.pause ? 'p' : '');
    T.ctx = c;
    if (key !== lastKey) {
      lastKey = key;
      for (const n in show) { el[n].classList.toggle('tc-off', show[n] === 0); el[n].classList.toggle('tc-dim', show[n] > 0 && show[n] < 1); }
      for (const n in caps) caps[n].textContent = (CAP[n] && CAP[n][c]) || capDefault[n];
    }
    el.e.classList.toggle('pulse', c === 'explore' && !!(G.world && G.world.near));     // 附近有人 / 东西可以调查：E 钮跳动
  }

  // 选菜单时按住上 / 下：过一会儿开始连着走（章节有 15 个，一格一格点太慢）
  const rep = { a: null, t0: 0, last: 0 };
  function repeat(now) {
    const menuish = T.ctx === 'menu' || T.ctx === 'title';
    const a = padKeys.up && !padKeys.down ? 'up' : padKeys.down && !padKeys.up ? 'down' : null;
    if (!menuish || !a) { rep.a = null; return; }
    if (rep.a !== a) { rep.a = a; rep.t0 = rep.last = now; return; }
    if (now - rep.t0 > 380 && now - rep.last > 110) { rep.last = now; I.hits[a] = true; }
  }

  // ---------------------------------------------------------------- 排版：按钮大小随屏幕高度走；竖着拿就停住、提示横过来
  const SIZES = [['小', 0.82], ['中', 1], ['大', 1.22]];       // 暂停菜单里的“按键大小”
  let sizeIdx = 1;
  try { const v = parseInt(localStorage.getItem('gintama-touch-size'), 10); if (v >= 0 && v < SIZES.length) sizeIdx = v; } catch (e) { /* 读不到就用“中” */ }
  T.sizeName = () => SIZES[sizeIdx][0];
  T.cycleSize = () => {
    sizeIdx = (sizeIdx + 1) % SIZES.length;
    try { localStorage.setItem('gintama-touch-size', String(sizeIdx)); } catch (e) { /* 存不了就这次有效 */ }
    layout();
  };
  function layout() {
    const w = innerWidth, h = innerHeight;
    root.style.setProperty('--b', G.clamp(Math.round(Math.min(h * 0.145, w * 0.075) * SIZES[sizeIdx][1]), 36, 96) + 'px');
    const portrait = T.on && h > w;
    document.body.classList.toggle('tc-portrait', portrait);
    G.suspended = portrait;
    measure();
  }
  function measure() {
    const S = T.safe;
    if (!T.on) { S.l = 0; S.r = S.sys = G.W; return; }
    const c = G.screen.getBoundingClientRect(), k = G.W / c.width;
    const gx = (x) => G.clamp((x - c.left) * k, 0, G.W);
    S.l = gx(el.pad.getBoundingClientRect().right);
    S.r = gx(el.l.getBoundingClientRect().left);
    S.sys = gx((el.full.style.display === 'none' ? el.pause : el.full).getBoundingClientRect().left);
  }
  addEventListener('resize', layout);
  addEventListener('orientationchange', () => setTimeout(layout, 250));

  // ---------------------------------------------------------------- 全屏（安卓 Chrome 全屏后还能锁横屏；iPhone 的 Safari 没有网页全屏，要“添加到主屏幕”）
  const de = document.documentElement;
  const reqFs = de.requestFullscreen || de.webkitRequestFullscreen;
  const exitFs = document.exitFullscreen || document.webkitExitFullscreen;
  const inFs = () => document.fullscreenElement || document.webkitFullscreenElement;
  if (!reqFs) el.full.style.display = 'none';
  else {
    el.full.addEventListener('click', () => {      // 全屏要求“手指抬起”这种用户动作，pointerdown 不算
      try {
        if (inFs()) { exitFs.call(document); return; }
        const p = reqFs.call(de, { navigationUI: 'hide' });
        const lock = () => { try { screen.orientation.lock('landscape').catch(() => {}); } catch (err) { /* 不支持锁定方向 */ } };
        if (p && p.then) p.then(lock).catch(() => {}); else lock();
      } catch (err) { /* 浏览器不让就算了 */ }
    });
    ['fullscreenchange', 'webkitfullscreenchange'].forEach((n) => document.addEventListener(n, () => { G.resize(); layout(); }));
  }

  // ---------------------------------------------------------------- 提示
  const toastEl = $('tc-toast');
  let toastTimer = 0;
  const queue = [];
  function toast(msg, ms = 5000) {
    queue.push([msg, ms]);
    if (!toastTimer) next();
    function next() {
      const q = queue.shift();
      if (!q) { toastTimer = 0; return; }
      toastEl.textContent = q[0];
      toastEl.classList.add('show');
      toastTimer = setTimeout(() => { toastEl.classList.remove('show'); toastTimer = setTimeout(next, 400); }, q[1]);
    }
  }
  T.toast = toast;
  function whenBooted(fn) { const t = setInterval(() => { if (G.scene) { clearInterval(t); fn(); } }, 200); }
  const once = (key) => { try { if (localStorage.getItem(key)) return false; localStorage.setItem(key, '1'); } catch (e) { /* 存不了就每次都提示 */ } return true; };

  // ---------------------------------------------------------------- 手机上的声音
  // 安卓 Chrome：手指抬起一次以后，什么时候放都行。
  // iPhone / iPad：每个 Audio 元素都要在手指抬起的那一下里先“点播”一次，之后才能随时播。
  // 音效先建好并各点播一次；音乐只用两个提前点过的元素轮流放（原来每换一首就 new 一个，新的会被拦下）。
  function silentWav(ms) {         // 一小段静音（Blob 地址），用来“点播”空元素
    const sr = 8000, n = Math.round((sr * ms) / 1000), buf = new ArrayBuffer(44 + n * 2), v = new DataView(buf);
    const str = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
    str(0, 'RIFF'); v.setUint32(4, 36 + n * 2, true); str(8, 'WAVE'); str(12, 'fmt '); v.setUint32(16, 16, true);
    v.setUint16(20, 1, true); v.setUint16(22, 1, true); v.setUint32(24, sr, true); v.setUint32(28, sr * 2, true);
    v.setUint16(32, 2, true); v.setUint16(34, 16, true); str(36, 'data'); v.setUint32(40, n * 2, true);
    return URL.createObjectURL(new Blob([buf], { type: 'audio/wav' }));
  }
  let primed = false;
  function primeAudio() {
    if (primed || !T.ios || !G.D.audio) return;
    primed = true;
    const A = G.audio;
    // 静音点播一下：手指抬起这一下里调用 play()，这个元素以后就能随时播了。返回 Promise（成功 true）
    const unlockEl = (a, src) => new Promise((res) => {
      if (src) a.src = src;
      a.muted = true;
      const done = (ok) => { try { a.pause(); a.currentTime = 0; } catch (e) { /* 还没加载 */ } a.muted = false; res(ok); };
      const p = a.play();
      if (p && p.then) p.then(() => done(true)).catch(() => done(false)); else done(true);
    });
    for (const n of Object.keys(G.D.audio.sfx || {})) {
      const pool = A.pools[n] || (A.pools[n] = []);
      if (!pool.length) { const a = new Audio(G.D.audio.sfx[n]); a.preload = 'auto'; pool.push(a); unlockEl(a); }
    }
    const slots = [new Audio(), new Audio()];
    const quiet = silentWav(250);
    Promise.all(slots.map((a) => { a.loop = true; return unlockEl(a, quiet); })).then((oks) => {
      if (!oks.every(Boolean)) return;        // 点播没成功：不换，还用原来的做法
      A.music = function (name, fade = 0.8) {
        if (this.name === name) return;
        const src = G.D.audio && G.D.audio.music[name];
        if (this.el) this.fadeTo(this.el, 0, fade, true);
        const old = this.el;
        this.el = null;
        this.name = name;
        if (!src) return;
        const a = slots.find((s) => s !== old) || slots[0];
        this.fades = this.fades.filter((f) => f.el !== a);
        a.volume = 0;
        a.src = src;
        a.loop = true;
        a.play().catch(() => {});
        this.el = a;
        this.fadeTo(a, this.musicVol, fade);
      };
      if (A.el && !slots.includes(A.el)) { const cur = A.name; A.name = null; A.music(cur, 0.3); }      // 标题曲换到点过的元素上接着放
    });
  }
  ['pointerup', 'touchend', 'click'].forEach((n) => addEventListener(n, () => { if (T.on) primeAudio(); }, true));

  // 切到别的应用 / 锁屏：音乐跟着停，回来再放；屏幕常亮（只有 https 或 localhost 才有这个接口）
  let wake = null, musicHeld = false;
  async function keepAwake() {
    try { if (navigator.wakeLock && !wake) { wake = await navigator.wakeLock.request('screen'); wake.addEventListener('release', () => { wake = null; }); } } catch (e) { /* 拿不到就算了 */ }
  }
  document.addEventListener('visibilitychange', () => {
    if (!T.on) return;
    const a = G.audio.el;
    if (document.hidden) { if (a && !a.paused) { a.pause(); musicHeld = true; } }
    else { if (a && musicHeld) a.play().catch(() => {}); musicHeld = false; keepAwake(); }
  });

  // 手离开屏幕一会儿，按键淡下去（少挡画面）；一碰就回来
  let lastAct = performance.now(), idle = false;
  const poke = () => { lastAct = performance.now(); };
  function fade(now) {
    const want = now - lastAct > 2500 && padId == null && !root.querySelector('.on');
    if (want !== idle) { idle = want; document.body.classList.toggle('tc-idle', want); }
  }
  ['pointerdown', 'pointermove'].forEach((n) => document.addEventListener(n, poke, true));

  // ---------------------------------------------------------------- 开关
  let timer = 0;
  function loop() { const now = performance.now(); refresh(); repeat(now); fade(now); }
  function setOn(v) {
    if (T.on === v) return;
    T.on = v;
    document.body.classList.toggle('tc-on', v);
    if (v) {
      layout();
      lastKey = '';
      lastAct = performance.now();
      refresh();
      timer = setInterval(loop, 50);
      keepAwake();
      whenBooted(() => {        // 等游戏载入完、标题出来了再弹，载入时弹的提示没人看得见
        if (once('gintama-touch-tip')) toast('左手方向盘走动，右手 J / K / L / E 按钮；对话和菜单直接点屏幕', 6000);
        if (T.ios && !navigator.standalone && once('gintama-touch-ios-tip')) toast('iPhone 想全屏玩：点浏览器的“分享”→“添加到主屏幕”，再从桌面图标打开', 7000);
      });
    } else {
      clearInterval(timer);
      releasers.forEach((f) => f());
      document.body.classList.remove('tc-portrait', 'tc-idle');
      idle = false;
      G.suspended = false;
    }
  }
  T.setOn = setOn;

  // 手指点在按钮以外的地方（画面里、黑边上）：算一次“确认 / 点这里”。点在画面里 core.js 已经管了，这里补黑边
  document.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'touch' && force !== false) setOn(true);
    if (!T.on || e.target === G.screen || (e.target.closest && e.target.closest('.tc-part'))) return;
    G.audio.unlock();
    I.hits.ok = true;
    I.tap = G.toGame(e);
  }, true);
  // 接了实体键盘就把屏幕按键收起来（再碰屏幕会自己出现）
  const KEYS = /^(Arrow|Key[WASDJKLZXCEP]$|Enter|Space|Escape|Backspace|Numpad)/;
  addEventListener('keydown', (e) => { if (force !== true && T.on && KEYS.test(e.code)) setOn(false); });
  document.addEventListener('contextmenu', (e) => { if (T.on) e.preventDefault(); });
  document.addEventListener('gesturestart', (e) => e.preventDefault());       // iOS 老版本的双指缩放

  setOn(force !== null ? force : isCoarse());
})();
