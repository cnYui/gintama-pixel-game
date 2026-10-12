/* 小红书小工具版音频引擎（替换 core.js 里基于 HTMLAudio 的 G.audio，接口完全一致）。
   为什么要换：小红书小工具的 zip 里不允许有 mp3，容器 CSP 也不许 <audio> 用 data: / blob: 地址。
   做法：音频以 base64 文本写在 audio/*.js 里（js 是允许的类型），运行时 atob → decodeAudioData → WebAudio 播放。
   iPhone：WebAudio 会被侧边静音拨片吃掉，所以（探针实测有效）
     1) navigator.audioSession.type = 'playback'
     2) 输出接到 MediaStreamDestination，再用 <audio srcObject> 播（没有 URL，不受 media-src 限制）
   素材包：audio/manifest.js 记录「素材路径 → 所在 js 文件」；这些 js 在 index.html 里都是静态 <script>（小红书容器里 load 之后运行时插入的脚本会加载失败，所以不能动态加载）。
   页面加载完 1.5 秒后在后台把音效逐个解码好；音乐用到时才解码，缓存有上限。
   window.AUDIO_DEBUG 为真时，左下角显示一行状态，方便在真机上看是哪一步出了问题。 */
(function () {
  'use strict';
  const G = window.G;
  const AC = window.AudioContext || window.webkitAudioContext;
  if (!G || !G.audio || !AC) return;                       // 没有 WebAudio：保留原来的 G.audio（会没声音，但不会报错）
  let ctx;
  try { ctx = new AC(); } catch (e) { return; }

  const MAN = window.AUDIO_MANIFEST || {};                 // 素材路径 → 所在 pack 文件
  const MUSIC_BUDGET = 48e6;                               // 解码后音乐缓存上限（字节），超了丢最久没用的
  const USE_MEDIA_ROUTE = true;                            // 经 <audio> 媒体流输出（绕开 iPhone 静音拨片）；出问题可改成 false 只用 audioSession
  const dbg = { err: '', loaded: 0, route: '' };

  // ---------------------------------------------------------------- 输出线路
  const master = ctx.createGain();
  master.gain.value = 1;
  let media = null, direct = false;
  try { if (navigator.audioSession) navigator.audioSession.type = 'playback'; } catch (e) { /* 老系统没有 */ }
  if (USE_MEDIA_ROUTE && ctx.createMediaStreamDestination) {
    try {
      const msd = ctx.createMediaStreamDestination();
      master.connect(msd);
      media = new Audio();
      media.srcObject = msd.stream;
      media.setAttribute('playsinline', '');
      dbg.route = '媒体流';
    } catch (e) { media = null; }
  }
  if (!media) { master.connect(ctx.destination); direct = true; dbg.route = '直连'; }
  function goDirect() { if (!direct) { direct = true; try { master.connect(ctx.destination); } catch (e) { /* 已连 */ } dbg.route = '直连(媒体流失败)'; } }

  let primed = false;
  function resumeAll() {                                   // 必须在手势里调用才有效；多调无害
    if (ctx.state !== 'running') { try { const p = ctx.resume(); if (p && p.catch) p.catch(() => {}); } catch (e) { /* 忽略 */ } }
    if (media && media.paused) {
      try {
        const p = media.play();
        if (p && p.catch) p.catch((e) => { if (e && e.name !== 'NotAllowedError') goDirect(); });   // 没手势被拒不算失败，下次手势再试
      } catch (e) { goDirect(); }
    }
    if (!primed) {                                         // iOS：手势里「点播」一次
      primed = true;
      try { const b = ctx.createBuffer(1, 1, 22050), s = ctx.createBufferSource(); s.buffer = b; s.connect(ctx.destination); s.start(0); } catch (e) { /* 忽略 */ }
    }
  }
  ['pointerdown', 'pointerup', 'touchstart', 'touchend', 'click', 'keydown'].forEach((n) => addEventListener(n, resumeAll, true));
  document.addEventListener('visibilitychange', () => { if (!document.hidden) resumeAll(); });

  // ---------------------------------------------------------------- 素材：动态加载 pack → base64 → 解码
  // 注意：不能在页面 load 之后动态创建 script 标签来加载脚本——小红书容器里这种脚本会加载失败（jojo 的 loadScript 失败就是这个原因）。
  // 所以所有 audio/*.js 包都在 index.html 里写成静态 <script>，这里只等它们执行完（APACK 里出现这个素材）。
  function waitPack(path, file) {
    return new Promise((res, rej) => {
      const t0 = Date.now();
      (function tick() {
        if (window.APACK && window.APACK[path]) { res(); return; }
        if (Date.now() - t0 > 120000) { dbg.err = '等不到 ' + file; rej(new Error('等不到 ' + file)); return; }
        setTimeout(tick, 150);
      })();
    });
  }
  const bufs = {};                                         // 路径 → { buf, t, bytes, music }
  const pending = {};
  function evict(keepName) {
    let total = 0;
    const music = Object.keys(bufs).filter((p) => bufs[p].music);
    music.forEach((p) => { total += bufs[p].bytes; });
    music.sort((a, b) => bufs[a].t - bufs[b].t);
    for (const p of music) {
      if (total <= MUSIC_BUDGET) break;
      if (p === keepName) continue;
      total -= bufs[p].bytes; delete bufs[p];
    }
  }
  function getBuffer(path, isMusic) {
    const have = bufs[path];
    if (have) { have.t = performance.now(); return Promise.resolve(have.buf); }
    if (pending[path]) return pending[path];
    const p = waitPack(path, MAN[path]).then(() => new Promise((res, rej) => {
      const b64 = window.APACK && window.APACK[path];
      if (!b64) { rej(new Error('pack 里没有 ' + path)); return; }
      const bin = atob(b64), n = bin.length, u8 = new Uint8Array(n);
      for (let i = 0; i < n; i++) u8[i] = bin.charCodeAt(i);
      let done = false;
      const ok = (b) => { if (!done) { done = true; res(b); } };
      const no = (e) => { if (!done) { done = true; rej(e || new Error('解码失败 ' + path)); } };
      const q = ctx.decodeAudioData(u8.buffer, ok, no);
      if (q && q.then) q.then(ok, no);
    })).then((buf) => {
      bufs[path] = { buf, t: performance.now(), bytes: buf.length * buf.numberOfChannels * 4, music: !!isMusic };
      delete pending[path];
      evict(path);
      return buf;
    }, (e) => { delete pending[path]; dbg.err = String((e && e.message) || e).slice(0, 60); throw e; });
    return (pending[path] = p);
  }

  // ---------------------------------------------------------------- G.audio
  const adapter = {                                        // main.js 的“补放标题曲”和 touch.js 的“切后台暂停”会读 G.audio.el
    get paused() { return ctx.state !== 'running' || (media ? media.paused : false); },
    play() { resumeAll(); return Promise.resolve(); },
    pause() { try { ctx.suspend(); } catch (e) { /* 忽略 */ } if (media) { try { media.pause(); } catch (e) { /* 忽略 */ } } },
  };
  const active = {};                                       // 音效名 → 正在响的 source 们（每个音效最多同时 6 个，和原来一样）

  G.audio = {
    web: true,
    ctx, master,
    unlocked: false,
    el: null,
    name: null,
    musicVol: 0.42,
    sfxVol: 0.75,
    fades: [],
    pools: {},
    cur: null,
    token: 0,
    ducked: false,
    unlock() { this.unlocked = true; resumeAll(); },
    music(name, fade = 0.8) {
      if (this.name === name) return;
      this.dropCurrent(fade);
      this.name = name;
      const path = G.D.audio && G.D.audio.music[name];
      this.el = path ? adapter : null;
      if (!path) return;
      const token = ++this.token;
      getBuffer(path, true).then((buf) => { if (token === this.token) this.startTrack(name, buf, fade); }).catch(() => {});
    },
    startTrack(name, buf, fade) {
      const src = ctx.createBufferSource(), g = ctx.createGain(), t = ctx.currentTime;
      src.buffer = buf; src.loop = true;
      g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(this.musicVol * (this.ducked ? 0.35 : 1), t + Math.max(0.01, fade));
      src.connect(g); g.connect(master);
      src.start(0);
      this.cur = { src, g, name };
    },
    dropCurrent(fade) {
      const c = this.cur;
      if (!c) return;
      this.cur = null;
      const t = ctx.currentTime, d = Math.max(0.01, fade);
      try { c.g.gain.cancelScheduledValues(t); c.g.gain.setValueAtTime(c.g.gain.value, t); c.g.gain.linearRampToValueAtTime(0, t + d); } catch (e) { /* 忽略 */ }
      try { c.src.stop(t + d + 0.05); } catch (e) { /* 忽略 */ }
      c.src.onended = () => { try { c.g.disconnect(); } catch (e) { /* 忽略 */ } };
    },
    stopMusic(fade = 0.8) {
      this.token++;
      this.dropCurrent(fade);
      this.name = null;
      this.el = null;
    },
    duck(on) {
      this.ducked = !!on;
      const c = this.cur;
      if (!c) return;
      const t = ctx.currentTime;
      try { c.g.gain.cancelScheduledValues(t); c.g.gain.setValueAtTime(c.g.gain.value, t); c.g.gain.linearRampToValueAtTime(this.musicVol * (on ? 0.35 : 1), t + 0.3); } catch (e) { /* 忽略 */ }
    },
    fadeTo() { /* 淡入淡出改用 WebAudio 自带的参数渐变，这里留空保持接口一致 */ },
    update() { /* 同上，不需要每帧推进 */ },
    sfx(name, vol = 1, rate = 1) {
      const path = G.D.audio && G.D.audio.sfx[name];
      if (!path) return;
      const e = bufs[path];
      if (!e) { getBuffer(path, false).catch(() => {}); return; }       // 还没解码好：这一下不响，下次就有了
      if (ctx.state !== 'running') return;                              // 没解锁时不排队，免得一解锁全响起来
      const list = active[name] || (active[name] = []);
      if (list.length >= 6) { try { list.shift().stop(); } catch (err) { /* 忽略 */ } }
      const src = ctx.createBufferSource(), g = ctx.createGain();
      src.buffer = e.buf;
      src.playbackRate.value = rate;
      g.gain.value = G.clamp(vol * this.sfxVol, 0, 1);
      src.connect(g); g.connect(master);
      src.onended = () => { const i = list.indexOf(src); if (i >= 0) list.splice(i, 1); try { g.disconnect(); } catch (err) { /* 忽略 */ } };
      list.push(src);
      src.start(0);
    },
  };

  // ---------------------------------------------------------------- 后台预取：音效包 → 各首音乐包；音效逐个解码好
  async function warm() {
    const sfx = Object.values((G.D.audio && G.D.audio.sfx) || {});
    for (const p of sfx) {
      try { await getBuffer(p, false); } catch (e) { /* 记在 dbg.err */ }
      await new Promise((r) => setTimeout(r, 0));          // 让出主线程，别卡画面
    }
  }
  const start = () => setTimeout(warm, 1500);
  if (document.readyState === 'complete') start(); else addEventListener('load', start);

  // ---------------------------------------------------------------- 调试状态条（真机看一眼就知道哪一步出了问题）
  if (window.AUDIO_DEBUG) {
    const el = document.createElement('div');
    el.style.cssText = 'position:fixed;left:6px;bottom:calc(env(safe-area-inset-bottom,0px) + 4px);z-index:2147483647;pointer-events:none;' +
      'font:10px/1.4 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;color:#fff;background:rgba(0,0,0,.55);padding:2px 6px;border-radius:4px;max-width:90vw;';
    (document.body || document.documentElement).appendChild(el);
    setInterval(() => {
      const nSfx = Object.values((G.D.audio && G.D.audio.sfx) || {}).filter((p) => bufs[p]).length;
      const totSfx = Object.keys((G.D.audio && G.D.audio.sfx) || {}).length;
      el.textContent = '♪ ' + ctx.state + ' | ' + dbg.route + ' | 音效 ' + nSfx + '/' + totSfx + ' | 音乐 ' +
        (G.audio.name || '-') + (G.audio.cur ? ' 播放中' : (G.audio.name ? ' 载入中' : '')) + (dbg.err ? ' | ⚠ ' + dbg.err : '');
    }, 400);
  }
})();
