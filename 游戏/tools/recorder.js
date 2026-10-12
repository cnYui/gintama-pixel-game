// 录屏（tools/playtest.py --record 用）：画面 + 混好的声音一条，BGM、音效各单独一条，三条同一时刻开录，时间对得上。
// 要用 http:// 打开游戏（file:// 下画布和音频都算跨域，录不出来）。数据每 3 秒一块，交给 Python 的 window.__recSave 写盘。
(() => {
  if (window.__recs) return;
  const ac = new (window.AudioContext || window.webkitAudioContext)();
  ac.resume().catch(() => {});
  const dMix = ac.createMediaStreamDestination(), dBgm = ac.createMediaStreamDestination(), dSfx = ac.createMediaStreamDestination();
  const busM = ac.createGain(), busS = ac.createGain();
  busM.connect(dMix); busM.connect(dBgm);
  busS.connect(dMix); busS.connect(dSfx);
  // 不接 ac.destination：录的时候电脑不会出声
  let BUS = null;
  const hook = (el, bus) => {
    if (el.__recHooked) return;
    el.__recHooked = true;
    ac.createMediaElementSource(el).connect(bus);
  };
  // 游戏里的声音都是 new Audio()：BGM 走 G.audio.music，音效走 G.audio.sfx；创建时就接进对应的那一轨
  const OrigAudio = window.Audio;
  window.Audio = function (src) { const el = new OrigAudio(src); hook(el, BUS || busS); return el; };
  window.Audio.prototype = OrigAudio.prototype;
  const wrap = (name, bus) => {
    const f = G.audio[name];
    G.audio[name] = function (...a) { const prev = BUS; BUS = bus; try { return f.apply(this, a); } finally { BUS = prev; } };
  };
  wrap('music', busM); wrap('sfx', busS);
  // 开场动画（video 元素）的原声算在 BGM 那一轨
  const origPlay = HTMLMediaElement.prototype.play;
  HTMLMediaElement.prototype.play = function () { if (!this.__recHooked && this.tagName === 'VIDEO') hook(this, busM); return origPlay.call(this); };
  if (G.audio.el) hook(G.audio.el, busM);        // 标题曲在注入之前就开始放了
  for (const pool of Object.values(G.audio.pools)) for (const el of pool) hook(el, busS);

  // 不传帧率：画布每画一次就收一帧。传 60 的话浏览器按“距上一帧满 1/60 秒”限流，帧间隔一抖（16.5 ms）就被丢，实测只剩 51 帧左右
  const vs = G.screen.captureStream();
  const streams = {
    full: new MediaStream([...vs.getVideoTracks(), ...dMix.stream.getAudioTracks()]),
    bgm: dBgm.stream,
    sfx: dSfx.stream,
  };
  window.__recs = {};
  window.__recPending = 0;
  for (const k of Object.keys(streams)) {
    const opt = k === 'full'
      ? { mimeType: 'video/webm;codecs=vp9,opus', videoBitsPerSecond: 8000000, audioBitsPerSecond: 256000 }
      : { mimeType: 'audio/webm;codecs=opus', audioBitsPerSecond: 256000 };
    const r = new MediaRecorder(streams[k], opt);
    let chain = Promise.resolve();
    r.ondataavailable = (e) => {
      if (!e.data || !e.data.size) return;
      window.__recPending++;
      chain = chain.then(async () => {
        const buf = new Uint8Array(await e.data.arrayBuffer());
        let s = '';
        for (let i = 0; i < buf.length; i += 0x8000) s += String.fromCharCode.apply(null, buf.subarray(i, i + 0x8000));
        await window.__recSave(k, btoa(s));
        window.__recPending--;
      });
    };
    window.__recs[k] = r;
  }
  for (const r of Object.values(window.__recs)) r.start(3000);
  window.__recStart = Date.now();
  window.__recStop = () => new Promise((res) => {
    const rs = Object.values(window.__recs);
    let n = 0;
    for (const r of rs) { r.onstop = () => { if (++n === rs.length) res(); }; r.stop(); }
  });
})();
