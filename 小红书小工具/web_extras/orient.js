// 公网版的设备适配：手机（陀螺仪提醒）和电脑（键盘提示）。
// ① 手机：用陀螺仪（DeviceOrientation）判断手机是竖着拿还是横着拿。
// 页面被系统锁成竖屏时（旋转锁定打开的手机、平板竖着放），游戏画面是转了 90° 显示的（core.js 的 G.layoutFrame）：
//   手机竖着拿  → 弹“请把手机横过来玩”，游戏先停住；点一下屏幕可以“就这样玩”
//   手机横过来  → 自动恢复；按手机往哪边倒，把画面转到正（G.rotDir：顺时针 / 逆时针 90°），两个方向都能玩
//   系统自己把页面转成横屏了（没锁旋转）→ 什么都不用做，G.rot 为 false
// 没有陀螺仪 / 没授权 / 浏览器不给读数：不做判断，保持画面转 90°，只弹一次文字提示。
// iPhone 读陀螺仪要玩家点一下同意（系统弹窗，且必须在点击里申请），所以竖着拿时先弹一次“轻点屏幕”。
// 小红书小工具容器拿不到陀螺仪、规范也禁用 DeviceOrientation，所以这个文件只放进公网版。
'use strict';
(function () {
  const G = window.G;
  if (!G || !G.layoutFrame) return;
  const RAD = Math.PI / 180, DEG = 180 / Math.PI;
  const needPerm = typeof window.DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function';   // iOS 13+

  // 手机 / 平板才需要这些提示；电脑上把窗口拉高了不要弹。判断用 core.js 的 G.touchDev（带触摸屏的笔记本 maxTouchPoints 也大于 0，所以不能只看它）
  const touchy = !!G.touchDev;
  let have = false;           // 收到过有效读数
  let cur = null;             // 已确认的朝向：'P' 竖着拿 / 'L+' 手机逆时针横过来（画面顺时针转） / 'L-' 手机顺时针横过来（画面逆时针转）
  let cand = null, since = 0; // 正在观察的朝向和它开始的时间（要稳定一小会儿才算数）
  let dismissed = false;      // 玩家点了“就这样玩”：到手机下次横过来之前不再提醒
  let asking = false;         // iPhone：1.2 秒内没有读数 → 等玩家点一下才能读陀螺仪
  let held = false;           // 提醒正在显示（游戏因此停住）
  let listening = false;

  // ---------------------------------------------------------------- 提醒的长相（在 #rot 外面：不跟着画面转，竖着拿时是正的）
  const style = document.createElement('style');
  style.textContent = `
  #rot-hint { position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 100; display: none; flex-direction: column; align-items: center; justify-content: center; gap: 22px;
              background: rgba(11, 10, 18, .94); color: #ffe9a8; font: 600 18px "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif; letter-spacing: 2px; text-align: center;
              cursor: pointer; -webkit-tap-highlight-color: transparent; -webkit-user-select: none; user-select: none; touch-action: manipulation; }
  body.rot-hint-on #rot-hint { display: flex; }
  #rot-hint i { display: block; width: 52px; height: 92px; box-sizing: border-box; border: 4px solid #ffd34a; border-radius: 11px; animation: rot-hint-turn 2.6s ease-in-out infinite; }
  #rot-hint small { display: block; margin-top: 8px; font: 400 13px/1.5 "Microsoft YaHei", "PingFang SC", sans-serif; letter-spacing: 1px; color: #9a93a8; }
  #rot-hint b { display: block; margin-top: 18px; padding: 7px 16px; border: 1px solid #3a3550; border-radius: 16px; font: 400 12px "Microsoft YaHei", "PingFang SC", sans-serif; letter-spacing: 1px; color: #77718a; }
  @keyframes rot-hint-turn { 0%, 15% { transform: rotate(0); } 55%, 85% { transform: rotate(-90deg); } 100% { transform: rotate(0); } }
  #rot-banner { position: fixed; left: 12px; right: 12px; top: calc(env(safe-area-inset-top, 0px) + 10px); z-index: 90; padding: 8px 14px; border-radius: 8px; box-sizing: border-box;
                background: rgba(14, 12, 26, .92); border: 1px solid #ffd34a; color: #fff4d6; text-align: center; font: 13px/1.5 "Microsoft YaHei", "PingFang SC", sans-serif;
                opacity: 0; transition: opacity .3s; pointer-events: none; }
  #rot-banner.show { opacity: 1; }
  #rot-banner.corner { top: 12px; left: 12px; right: auto; width: max-content; max-width: calc(100% - 24px); text-align: left; }`;   /* 电脑上放左上角的空白天空里：不挡底部的原作署名和中间的菜单 */
  document.head.appendChild(style);
  const hint = document.createElement('div');
  hint.id = 'rot-hint';
  hint.innerHTML = '<i></i><div>请把手机横过来玩<small></small></div><b></b>';
  document.body.appendChild(hint);
  const hintSub = hint.querySelector('small'), hintBtn = hint.querySelector('b');
  const banner = document.createElement('div');
  banner.id = 'rot-banner';
  banner.textContent = '手机竖着拿时画面会转 90°，请把手机横过来玩';
  document.body.appendChild(banner);

  // 提醒显示时游戏停住。touch.js 自己也会写 G.suspended（旧的“竖着拿就停住”），所以用访问器把两边合起来
  let baseSuspended = !!G.suspended;
  Object.defineProperty(G, 'suspended', { configurable: true, get() { return baseSuspended || held; }, set(v) { baseSuspended = !!v; } });

  function refresh() {
    const want = !!G.rot && (asking || (!dismissed && have && cur === 'P'));
    if (want === held) return;
    held = want;
    document.body.classList.toggle('rot-hint-on', held);
    if (held) {
      hintSub.textContent = asking ? '轻点屏幕后，手机横过来会自动识别方向' : '横屏才看得全画面和按键';
      hintBtn.textContent = asking ? '轻点屏幕继续' : '点一下屏幕：就这样玩';
      G.input.down = {};         // 停住的时候别留着按住的键
    }
  }

  // ---------------------------------------------------------------- 读陀螺仪
  // 从 beta / gamma 算出“天”在手机坐标系里的方向 u（W3C 规范的 Z-X'-Y'' 旋转，和偏航角 alpha 无关）：
  //   竖着拿 u = (0, 1, 0)；手机逆时针横过来（顶边朝左）u = (1, 0, 0)；顺时针横过来（顶边朝右）u = (-1, 0, 0)；平放 u = (0, 0, ±1)
  function onOrient(e) {
    if (e.beta == null || e.gamma == null) return;        // 电脑上的 Chrome 会发一个全是 null 的事件
    have = true;
    const b = e.beta * RAD, g = e.gamma * RAD;
    const ux = -Math.sin(g) * Math.cos(b), uy = Math.sin(b), uz = Math.cos(g) * Math.cos(b);
    if (Math.abs(uz) > 0.85) return;                      // 平放（屏幕朝上 / 朝下）：看不出朝向，保持原样
    const phi = Math.atan2(ux, uy) * DEG, a = Math.abs(phi);   // 0 = 竖着拿；+90 = 逆时针横过来；-90 = 顺时针横过来；±180 = 倒过来竖着拿
    const c = a > 60 && a < 120 ? (phi > 0 ? 'L+' : 'L-') : (a < 30 || a > 150) ? 'P' : null;
    if (c == null) return;                                // 30°–60° / 120°–150° 是死区：保持上一次的结论，边界上不会来回跳
    if (c !== cand) { cand = c; since = performance.now(); }
  }
  // 手机放稳了就不再有新读数，所以“稳定多久”用定时器判断，不靠读数触发
  function tick() {
    if (!cand || cand === cur || performance.now() - since < (cand === 'P' ? 700 : 250)) return;   // 弹提醒慢一点（要稳 0.7 秒），恢复快一点
    cur = cand;
    if (cur !== 'P') {
      dismissed = false;
      const d = cur === 'L+' ? 1 : -1;
      if (G.rotDir !== d) { G.rotDir = d; window.dispatchEvent(new Event('resize')); }      // core.js / touch.js 都在听 resize，会重新排版
    }
    refresh();
  }
  setInterval(tick, 100);

  // 没有陀螺仪时的兜底：文字提示一次（同一个标签页只提示一次）
  let bannerTimer = 0;
  function showBanner(text, ms, corner) {
    banner.textContent = text;
    banner.classList.toggle('corner', !!corner);
    banner.classList.add('show');
    clearTimeout(bannerTimer);
    bannerTimer = setTimeout(() => banner.classList.remove('show'), ms);
  }
  function fallback() {
    if (!G.rot || !touchy) return;
    try { if (sessionStorage.getItem('gintama-rot-tip')) return; sessionStorage.setItem('gintama-rot-tip', '1'); } catch (err) { /* 存不了就每次都提示 */ }
    showBanner('手机竖着拿时画面会转 90°，请把手机横过来玩', 7000, false);
  }
  function listen() {
    if (listening) return;
    listening = true;
    addEventListener('deviceorientation', onOrient, true);
    if (!needPerm) setTimeout(() => { if (!have) fallback(); }, 2000);        // 2 秒还没有读数：这台设备 / 浏览器不给陀螺仪
  }
  // iPhone：必须在点击 / 手指抬起里申请，系统会弹“是否允许访问运动与方向”
  function ask() {
    asking = false;
    refresh();
    try {
      DeviceOrientationEvent.requestPermission().then((r) => {
        if (r !== 'granted') { fallback(); return; }
        removeEventListener('deviceorientation', onOrient, true); listening = false; listen();     // 授权后重新挂一次，保证 iPhone 上一定收得到
        setTimeout(() => { if (!have) fallback(); }, 2000);
      }).catch(fallback);
    } catch (err) { fallback(); }
  }

  // ---------------------------------------------------------------- 接线
  hint.addEventListener('click', () => {
    if (asking) { ask(); return; }          // 这一下点击是申请权限用的，不算“就这样玩”：授权后手机还是竖着拿的话会再弹正式的提醒
    dismissed = true;
    refresh();
  });
  // 点提醒不要当成游戏里的点击（touch.js 会把点在画面外的手指当成“确认 / 点这里”，恢复时会误触发菜单或跳过一句对话）
  addEventListener('pointerdown', (e) => { if (held && hint.contains(e.target)) e.stopPropagation(); }, true);
  addEventListener('resize', refresh);
  addEventListener('orientationchange', () => setTimeout(refresh, 300));

  if (typeof window.DeviceOrientationEvent === 'undefined') setTimeout(fallback, 1500);
  else {
    listen();                               // 先直接听：Android / 电脑不用授权，一开始就有读数；iPhone 授权前不会有读数
    // 有 requestPermission 的浏览器（iPhone，新版 Chrome 也有）：1.2 秒内没有读数，才弹“轻点屏幕”去申请
    if (needPerm && touchy) setTimeout(() => { if (!have) { asking = true; refresh(); } }, 1200);
  }
  // 电脑（键盘 + 鼠标）：手机按键默认就是隐藏的（core.js 的 G.touchDev + touch.js），W A S D / J K L E / Esc 直接能用；第一次打开提示一下
  if (!touchy) {
    setTimeout(() => {
      if (G.touch && G.touch.on) return;
      try { if (localStorage.getItem('gintama-key-tip')) return; localStorage.setItem('gintama-key-tip', '1'); } catch (err) { /* 存不了就每次都提示 */ }
      showBanner('键盘：W A S D 移动　J 攻击　K 跳跃　L 防御　E 对话 / 调查　Esc 暂停', 9000, true);
      const hide = (e) => { if (e.code === 'Enter' || e.code === 'Space') { banner.classList.remove('show'); removeEventListener('keydown', hide, true); } };
      addEventListener('keydown', hide, true);        // 按了确认键（开始游戏）就收起来，不挡画面
    }, 2500);
  }
  G.orient = { get state() { return cur; }, get have() { return have; }, get held() { return held; } };    // 调试 / 测试用
})();
