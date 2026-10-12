r"""小红书小工具容器永远是竖屏（拿不到陀螺仪，也不能 requestFullscreen / 锁方向）。
竖着的时候把整个游戏（画面 + 触屏按键）顺时针转 90° 显示，玩家把手机横过来拿就是正的；容器本身是横的就不转。

只改 dist 里的副本（core.js / touch.js / index.html），原来的 游戏\ 目录不动。
公网版（web=True）额外加 engine/orient.js（web_extras/orient.js）：用手机陀螺仪判断手机是竖着拿还是横着拿，
竖着拿时提醒“请把手机横过来玩”，横着拿时按手机往哪边倒把画面转到正（G.rotDir = 1 顺时针 / -1 逆时针）。
坐标约定：frame = 屏幕（竖屏）坐标，virtual = 游戏横屏坐标。顺时针转 90° 后 virtual(x, y) 在 frame 里是 (fw - y, x)，
反过来 frame(x, y) → virtual (y, fw - x)。
"""
import os


def _edit(root, rel, subs):
    p = os.path.join(root, rel)
    s = open(p, encoding='utf-8').read()
    for old, new, cnt in subs:
        n = s.count(old)
        assert n == cnt, f'{rel}: 找不到/次数不对 {old[:60]!r} 命中 {n} 次，应为 {cnt}'
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8', newline='\n').write(s)


CORE_HELPERS = r"""  // [小红书竖屏] 小工具容器永远竖屏：竖着的时候把整个游戏顺时针转 90° 显示（玩家把手机横过来拿），横着就不转
  // [设备适配] 手机 / 平板（主指针是手指，或 UA 是手机 / iPad / iPadOS 的电脑版 UA；和 touch.js 的 isCoarse 一致）才会转画面、弹手机按键。
  // 电脑 = 键盘 + 鼠标（带触摸屏的笔记本主指针也是鼠标）：窗口再窄也不转画面，也不弹手机按键。网址加 ?rot=1 / ?rot=0 可强制转 / 不转（调试用）
  G.touchDev = !!(window.matchMedia && matchMedia('(pointer: coarse)').matches) || /Android|Mobile|iP(hone|ad|od)/i.test(navigator.userAgent)
    || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  const rotParam = new URLSearchParams(location.search).get('rot');
  G.canRot = rotParam === '1' ? true : rotParam === '0' ? false : G.touchDev;
  G.rot = false; G.rotDir = 1; G.fw = innerWidth; G.fh = innerHeight; G.vw = innerWidth; G.vh = innerHeight;
  // rotDir：1 = 顺时针转 90°（玩家把手机逆时针横过来拿，默认）；-1 = 逆时针转 90°（玩家把手机顺时针横过来拿）。公网版的 orient.js 按陀螺仪改它
  G.layoutFrame = function () {
    const fw = innerWidth, fh = innerHeight;
    G.fw = fw; G.fh = fh;
    G.rot = G.canRot && fh > fw;
    G.vw = G.rot ? fh : fw; G.vh = G.rot ? fw : fh;
    const box = document.getElementById('rot');
    document.body.classList.toggle('rot', G.rot);
    document.body.classList.toggle('rot-ccw', G.rot && G.rotDir < 0);
    if (box) {
      box.style.width = G.vw + 'px'; box.style.height = G.vh + 'px';
      box.style.transformOrigin = '0 0';
      box.style.transform = !G.rot ? 'none' : G.rotDir > 0 ? 'translateX(' + fw + 'px) rotate(90deg)' : 'translateY(' + fh + 'px) rotate(-90deg)';
    }
  };
  // 屏幕上的点 → 游戏横屏坐标。顺时针：(x, y) → (y, fw - x)；逆时针：(x, y) → (fh - y, x)
  G.pt = (x, y) => (!G.rot ? { x: x, y: y } : G.rotDir > 0 ? { x: y, y: G.fw - x } : { x: G.fh - y, y: x });
  G.rect = (el) => {                                                           // 元素在游戏横屏坐标里的矩形
    const r = el.getBoundingClientRect();
    if (!G.rot) return r;
    const a = G.pt(r.left, r.top), b = G.pt(r.right, r.bottom);
    const left = Math.min(a.x, b.x), right = Math.max(a.x, b.x), top = Math.min(a.y, b.y), bottom = Math.max(a.y, b.y);
    return { left: left, right: right, top: top, bottom: bottom, width: right - left, height: bottom - top };
  };
"""

ROT_CSS = """
  /* [竖屏旋转] 竖着时整个游戏转 90°（core.js 的 G.layoutFrame 写 #rot 的宽高和 transform）。
     安全区也跟着转。顺时针（默认）：游戏左边 = 手机顶部@@NAV@@，游戏右边 = 手机底部；逆时针（body.rot-ccw）：左右 / 上下反过来 */
  #rot { position: absolute; left: 0; top: 0; width: 100%; height: 100%; overflow: hidden; }
  :root { --sal: env(safe-area-inset-left, 0px); --sar: env(safe-area-inset-right, 0px); --sat: env(safe-area-inset-top, 0px); --sab: env(safe-area-inset-bottom, 0px); }
  body.rot { --sal: @@TOP@@; --sar: env(safe-area-inset-bottom, 0px); --sat: env(safe-area-inset-right, 0px); --sab: env(safe-area-inset-left, 0px); }
  body.rot.rot-ccw { --sal: env(safe-area-inset-bottom, 0px); --sar: @@TOP@@; --sat: env(safe-area-inset-left, 0px); --sab: env(safe-area-inset-right, 0px); }
"""


def rot_css(web):
    # 小红书容器顶部有自带的返回 / 分享钮，游戏左边（= 手机顶部）多留 24px；公网版没有这个
    top = 'env(safe-area-inset-top, 0px)' if web else 'calc(env(safe-area-inset-top, 0px) + 24px)'
    return ROT_CSS.replace('@@TOP@@', top).replace('@@NAV@@', '' if web else '（状态栏 + 容器自带的返回钮，所以多留 24px）')


_TOUCHDEV_EXPR = ("  G.touchDev = !!(window.matchMedia && matchMedia('(pointer: coarse)').matches) || /Android|Mobile|iP(hone|ad|od)/i.test(navigator.userAgent)\n"
                  "    || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);\n")


def _core_helpers(web):
    """小红书版：容器永远是手机竖屏，平台审核用的模拟器是桌面 Chrome（鼠标 + 窗口很窄的竖屏）——也必须当手机处理：
    竖屏时一律顺时针转 90° + 屏幕按键常显。否则模拟器里游戏是一个没旋转的小横屏、没有按键，审核会判成“页面按钮无法点击”。
    公网版保留电脑 / 手机识别（电脑上不转、不弹手机按键）。"""
    if web: return CORE_HELPERS
    assert CORE_HELPERS.count(_TOUCHDEV_EXPR) == 1
    return CORE_HELPERS.replace(_TOUCHDEV_EXPR, "  G.touchDev = true;       // 小红书小工具容器 = 手机竖屏容器（含审核模拟器的桌面 Chrome）：竖屏就顺时针转 90°，屏幕按键常显\n")


def apply(root, web=False):
    # ---- core.js：画布尺寸按“虚拟横屏”算；点击坐标先转到横屏坐标
    _edit(root, 'engine/core.js', [
        ("  G.resize = function () {\n", _core_helpers(web) + "  G.resize = function () {\n    G.layoutFrame();\n", 1),
        ("Math.floor(Math.min((innerWidth * dpr) / G.W, (innerHeight * dpr) / G.H))", "Math.floor(Math.min((G.vw * dpr) / G.W, (G.vh * dpr) / G.H))", 1),
        ("const r = G.screen.getBoundingClientRect();", "const r = G.rect(G.screen), p = G.pt(e.clientX, e.clientY);", 1),
        ("return { x: ((e.clientX - r.left) * G.W) / r.width, y: ((e.clientY - r.top) * G.H) / r.height };",
         "return { x: ((p.x - r.left) * G.W) / r.width, y: ((p.y - r.top) * G.H) / r.height };", 1),
    ])
    # ---- touch.js：方向盘的方向、按钮测量都用横屏坐标；不再提示“竖着拿”；去掉 iOS 添加到主屏幕的提示
    _edit(root, 'engine/touch.js', [
        ("const r = el.pad.getBoundingClientRect();", "const r = G.rect(el.pad), pp = G.pt(e.clientX, e.clientY);", 1),
        ("dx = e.clientX - (r.left + R), dy = e.clientY - (r.top + R);", "dx = pp.x - (r.left + R), dy = pp.y - (r.top + R);", 1),
        ("const w = innerWidth, h = innerHeight;", "G.layoutFrame(); const w = G.vw, h = G.vh;", 1),
        ("const c = G.screen.getBoundingClientRect(), k = G.W / c.width;", "const c = G.rect(G.screen), k = G.W / c.width;", 1),
        ("  document.addEventListener('pointerdown', (e) => {\n    if (e.pointerType === 'touch' && force !== false) setOn(true);\n",
         "  // [电脑适配] 电脑（G.touchDev 为 false）上，单指触摸不算触屏：各种 PC 模拟器会把鼠标翻成触摸，不能因此弹出手机按键；\n"
         "  // 两指同时按下一定是真触屏（鼠标翻不出来）；?touch=1 照样能强制显示\n"
         "  const fingers = new Set();\n"
         "  ['pointerup', 'pointercancel'].forEach((n) => document.addEventListener(n, (e) => fingers.delete(e.pointerId), true));\n"
         "  document.addEventListener('pointerdown', (e) => {\n"
         "    if (e.pointerType === 'touch') {\n"
         "      fingers.add(e.pointerId);\n"
         "      if (force !== false && (G.touchDev || force === true || fingers.size >= 2)) setOn(true);\n"
         "    }\n", 1),
        ("  setOn(force !== null ? force : isCoarse());", "  setOn(force !== null ? force : (G.touchDev || isCoarse()));", 1),
        ("S.l = gx(el.pad.getBoundingClientRect().right);", "S.l = gx(G.rect(el.pad).right);", 1),
        ("S.r = gx(el.l.getBoundingClientRect().left);", "S.r = gx(G.rect(el.l).left);", 1),
        ("(el.full.style.display === 'none' ? el.pause : el.full).getBoundingClientRect().left", "G.rect(el.full.style.display === 'none' ? el.pause : el.full).left", 1),
    ] + ([] if web else [
        ("        if (T.ios && !navigator.standalone && once('gintama-touch-ios-tip')) toast('iPhone 想全屏玩：点浏览器的“分享”→“添加到主屏幕”，再从桌面图标打开', 7000);\n", "", 1),
    ]))
    # ---- index.html：把画面和按键包进 #rot；安全区改成变量（竖着时跟着转）
    p = os.path.join(root, 'index.html')
    s = open(p, encoding='utf-8').read()
    for a, b in [('env(safe-area-inset-left, 0px)', 'var(--sal)'), ('env(safe-area-inset-right, 0px)', 'var(--sar)'),
                 ('env(safe-area-inset-top, 0px)', 'var(--sat)'), ('env(safe-area-inset-bottom, 0px)', 'var(--sab)')]:
        assert a in s, a
        s = s.replace(a, b)
    assert s.count('</style>') == 1
    s = s.replace('</style>', rot_css(web) + '</style>', 1)
    if web:                                   # 公网版：加陀螺仪检测（小红书容器拿不到陀螺仪、规范也禁用 DeviceOrientation，所以小红书版不加）
        tag = '<script src="engine/touch.js"></script>'
        assert s.count(tag) == 1
        s = s.replace(tag, tag + '\n<script src="engine/orient.js"></script>', 1)
        src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web_extras', 'orient.js')
        open(os.path.join(root, 'engine', 'orient.js'), 'w', encoding='utf-8', newline='\n').write(open(src, encoding='utf-8').read())
    for old, new in [('<canvas id="screen" width="384" height="216"></canvas>', '<div id="rot">\n<canvas id="screen" width="384" height="216"></canvas>'),
                     ('<div id="tc-toast"></div>', '<div id="tc-toast"></div>\n</div>')]:
        assert s.count(old) == 1, old
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8', newline='\n').write(s)
    # :root 里的变量定义本身不能被上面的 env() 替换误伤（ROT_CSS 是替换之后才加进去的）
    assert 'var(--sal)' in s and '--sal: env(safe-area-inset-left' in s
