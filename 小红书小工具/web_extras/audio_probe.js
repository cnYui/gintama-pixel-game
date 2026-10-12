/* 声音探针（第 2 版）：验证小红书小工具容器能不能出声，以及 iPhone 上怎么绕开静音拨片。
   做法：音频不当成文件放进 zip（平台只收 js/图片等），而是以 base64 文本写在 probe/audio_data.js 里，
   运行时 atob → ArrayBuffer → WebAudio 的 decodeAudioData → BufferSource 播放（不用 data: / blob: URL）。
   第 1 版实测：iPhone 小红书里 WebAudio 运行中、解码成功、时钟在走，但听不到声音（疑似静音拨片：WebKit 会让 WebAudio 跟着静音，<audio> 不会）。
   第 2 版加三个按钮逐个试：
     A 直连  = 原来的路（master → destination）
     B <audio> = master → MediaStreamDestination → <audio srcObject>（没有 URL，不受 media-src 限制；media 元素播放不受静音拨片管）
     C 会话  = navigator.audioSession.type = 'playback'（iOS 16.4+ 的 Audio Session API）
   每点一次按钮都会重新「滴—滴」，听到了就说明那个办法有效。 */
(function () {
  'use strict';
  var el = null, txt = null;
  var S = { api: '检测中…', state: '…', beep: '等待 AudioContext 运行', dec: '…', music: '等待', clock: '…', sess: '…', route: 'A 直连 destination', csp: '', err: '' };

  function render() {
    if (!txt) return;
    txt.textContent = '🔊 声音探针 v2（WebAudio + 内嵌 base64）\n' +
      '① WebAudio：' + S.api + '\n' +
      '② 状态：' + S.state + '\n' +
      '③ 提示音：' + S.beep + '\n' +
      '④ 解码：' + S.dec + '\n' +
      '⑤ 音乐：' + S.music + '\n' +
      '⑥ 音频时钟：' + S.clock + '\n' +
      '⑦ 音频会话：' + S.sess + '\n' +
      '⑧ 输出通道：' + S.route +
      (S.csp ? '\n⚠ CSP：' + S.csp : '') + (S.err ? '\n⚠ 错误：' + S.err : '');
  }

  function mount() {
    el = document.createElement('div');
    el.id = 'audio-probe';
    el.style.cssText = 'position:fixed;left:0;right:0;top:0;z-index:2147483647;pointer-events:none;' +
      'padding:calc(env(safe-area-inset-top,0px) + 30px) 12px 8px;background:rgba(0,0,0,.82);color:#fff;' +
      'font:12px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;';
    txt = document.createElement('div');
    txt.style.cssText = 'white-space:pre-wrap;word-break:break-all;';
    el.appendChild(txt);
    (document.body || document.documentElement).appendChild(el);
    render();
  }
  mount();

  function button(label, fn) {
    var b = document.createElement('button');
    b.type = 'button'; b.textContent = label;
    b.style.cssText = 'pointer-events:auto;margin:8px 8px 0 0;padding:10px 12px;border:0;border-radius:8px;' +
      'background:#ffd34a;color:#222;font:700 14px -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;touch-action:manipulation;';
    ['pointerdown', 'touchstart', 'touchend', 'mousedown'].forEach(function (n) { b.addEventListener(n, function (e) { e.stopPropagation(); }); });
    b.addEventListener('click', function (e) { e.stopPropagation(); try { fn(); } catch (err) { S.err = String(err).slice(0, 90); } render(); });
    el.appendChild(b);
  }

  document.addEventListener('securitypolicyviolation', function (e) {
    S.csp = e.violatedDirective + ' 拦截了 ' + String(e.blockedURI).slice(0, 40); render();
  });
  window.addEventListener('error', function (e) { S.err = String(e.message || e).slice(0, 90); render(); });

  var AC = window.AudioContext || window.webkitAudioContext;
  if (!AC) { S.api = '不支持 ✗（没有 AudioContext）'; S.state = S.beep = S.dec = S.music = S.clock = S.sess = S.route = '-'; render(); return; }

  var ctx, master;
  try {
    ctx = new AC();
    master = ctx.createGain(); master.gain.value = 0.9; master.connect(ctx.destination);
    S.api = '支持 ✓（采样率 ' + ctx.sampleRate + ' Hz）';
  } catch (e) {
    S.api = '创建失败 ✗ ' + e; S.state = S.beep = S.dec = S.music = S.clock = S.sess = S.route = '-'; render(); return;
  }
  S.sess = navigator.audioSession ? '支持，当前 type = ' + navigator.audioSession.type : '不支持（没有 navigator.audioSession）';

  var buf = null, started = false, beeped = false;

  // ---- 提示音：滴—滴（振荡器合成，不依赖文件）
  function tones() {
    [[660, 0], [880, 0.28]].forEach(function (n) {
      var o = ctx.createOscillator(), g = ctx.createGain(), t = ctx.currentTime + n[1];
      o.type = 'sine'; o.frequency.value = n[0];
      g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.6, t + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.22);
      o.connect(g); g.connect(master); o.start(t); o.stop(t + 0.25);
    });
  }
  function beep() {
    if (beeped || ctx.state !== 'running') return;
    beeped = true; tones();
    S.beep = '已发出「滴—滴」（660Hz / 880Hz）。听到了吗？';
  }

  // ---- 音乐：解码好 + 上下文在运行，才开始（提示音之后 0.9 秒进入）
  function startMusic() {
    if (started || !buf || ctx.state !== 'running') return;
    started = true;
    var src = ctx.createBufferSource(), g = ctx.createGain();
    src.buffer = buf; src.loop = true; g.gain.value = 0.6;
    src.connect(g); g.connect(master);
    src.start(ctx.currentTime + 0.9);
    S.music = '已开始播放（循环，音量 60%）';
  }

  function sync() { beep(); startMusic(); render(); }

  function resume() {
    try {
      var p = ctx.resume();
      if (p && p.then) p.then(sync, function (e) { S.err = 'resume 失败：' + e; render(); });
    } catch (e) { S.err = 'resume 异常：' + e; }
  }

  // iOS：必须在手势里「点播」一次，之后才能出声
  function unlock() {
    resume();
    try {
      var b = ctx.createBuffer(1, 1, 22050), s = ctx.createBufferSource();
      s.buffer = b; s.connect(ctx.destination); s.start(0);
    } catch (e) { /* 忽略 */ }
  }
  ['touchstart', 'touchend', 'pointerdown', 'pointerup', 'mousedown', 'mouseup', 'click', 'keydown'].forEach(function (n) {
    document.addEventListener(n, unlock, true);
  });
  document.addEventListener('visibilitychange', function () { if (!document.hidden) resume(); });
  ctx.onstatechange = sync;

  // ---- 三种输出办法
  var msd = null, media = null;
  function routeA() {                     // A：直连
    try { master.disconnect(); } catch (e) { /* 没连过 */ }
    master.connect(ctx.destination);
    if (media) { try { media.pause(); } catch (e) { /* 忽略 */ } }
    S.route = 'A 直连 destination（原来的路）';
    tones();
  }
  function routeB() {                     // B：经 <audio> 媒体流（srcObject，没有 URL）
    if (!ctx.createMediaStreamDestination) { S.route = 'B 不可用：没有 createMediaStreamDestination'; return; }
    if (!msd) {
      msd = ctx.createMediaStreamDestination();
      media = document.createElement('audio');
      media.srcObject = msd.stream; media.setAttribute('playsinline', ''); media.style.display = 'none';
      (document.body || document.documentElement).appendChild(media);
    }
    try { master.disconnect(); } catch (e) { /* 没连过 */ }
    master.connect(msd);
    S.route = 'B 经 <audio> 媒体流：play() 调用中…';
    var p = media.play();
    if (p && p.then) p.then(function () { S.route = 'B 经 <audio> 媒体流：play() 成功 ✓'; render(); },
                            function (e) { S.route = 'B 经 <audio> 媒体流：play() 被拒 ✗ ' + e; render(); });
    else S.route = 'B 经 <audio> 媒体流：已调用 play()';
    tones();
  }
  function sessionPlayback() {            // C：音频会话设为 playback
    var as = navigator.audioSession;
    if (!as) { S.sess = '不支持（没有 navigator.audioSession）'; return; }
    try { as.type = 'playback'; S.sess = '已设为 type = ' + as.type + '（iOS 16.4+）'; } catch (e) { S.sess = '设置失败 ✗ ' + e; }
    tones();
  }
  button('A 直连', routeA);
  button('B 走<audio>', routeB);
  button('C 会话=playback', sessionPlayback);
  button('再响一声', function () { tones(); });

  // ---- 解码
  function b64ToBuf(b64) {
    var bin = atob(b64), n = bin.length, u8 = new Uint8Array(n);
    for (var i = 0; i < n; i++) u8[i] = bin.charCodeAt(i);
    return u8.buffer;
  }
  var t0 = Date.now(), done = false, ab = null;
  try {
    ab = b64ToBuf(window.__AUDIO_PROBE_B64);
    S.dec = '解码中…（mp3 ' + Math.round(ab.byteLength / 1024) + ' KB）';
  } catch (e) { S.dec = 'base64 还原失败 ✗ ' + e; }
  window.__AUDIO_PROBE_B64 = null;
  function onDecoded(b) {
    if (done) return; done = true; buf = b;
    S.dec = '成功 ✓ 时长 ' + b.duration.toFixed(1) + ' 秒，用时 ' + (Date.now() - t0) + ' ms';
    S.music = ctx.state === 'running' ? '准备播放' : '已解码，等待 AudioContext 运行';
    sync();
  }
  function onDecodeFail(e) { if (done) return; done = true; S.dec = '失败 ✗ ' + ((e && e.message) || e || '未知'); render(); }
  if (ab) {
    try {
      var p = ctx.decodeAudioData(ab, onDecoded, onDecodeFail);
      if (p && p.then) p.then(onDecoded, onDecodeFail);
    } catch (e) { onDecodeFail(e); }
  }

  // ---- 一加载就尝试出声；被拦住就等第一次触摸
  resume();

  // ---- 状态面板刷新
  var lastT = -1;
  setInterval(function () {
    var st = ctx.state;
    S.state = st === 'running' ? '运行中 ✓' :
              st === 'suspended' ? '被浏览器挂起 ✗ → 请点一下屏幕' :
              st === 'interrupted' ? '被系统打断（来电 / 切后台）→ 点一下屏幕' : st;
    var t = ctx.currentTime;
    S.clock = t.toFixed(1) + ' 秒' + (st === 'running' ? (t > lastT ? '（在走 ✓）' : '（没在走）') : '');
    lastT = t;
    if (st === 'running' && started) S.music = '播放中（循环，音量 60%）。听到了吗？';
    sync();
  }, 300);
})();
