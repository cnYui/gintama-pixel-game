"""电脑 / 手机适配验收（公网版）。
  电脑（键盘 + 鼠标）：手机按键默认隐藏；W A S D / 方向键 / J K L E 都能用；鼠标点菜单能用；首次打开提示一次键盘操作；
                      窗口拉成竖的也不转画面；鼠标翻译出来的单指触摸不会弹手机按键，两指同时按（真触屏）才会；?touch=1 / ?rot=1 可强制
  手机 / 平板：iPhone UA、Android 平板、iPadOS（电脑版 UA）都识别成触屏设备；竖着时转画面
用法: DIST=目录 python adapt_test.py [名字]      或      URL=https://aaccx.pw/gintama/ python adapt_test.py public
"""
import functools, http.server, io, os, socketserver, sys, threading
from playwright.sync_api import sync_playwright
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.environ.get('DIST') or os.path.join(HERE, 'dist-web')
NAME = sys.argv[1] if len(sys.argv) > 1 else 'web'
TMP = os.path.join(HERE, '_tmp'); os.makedirs(TMP, exist_ok=True)

class H(http.server.SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def end_headers(self): self.send_header('Cache-Control', 'no-store'); super().end_headers()
    def log_message(self, *a): pass
class S(socketserver.ThreadingTCPServer):
    request_queue_size = 1024; daemon_threads = True
    def handle_error(self, *a): pass
PUBLIC = os.environ.get('URL')
if PUBLIC: srv = None; BASE = PUBLIC
else:
    srv = S(('127.0.0.1', 0), functools.partial(H, directory=DIST)); threading.Thread(target=srv.serve_forever, daemon=True).start()
    BASE = f'http://127.0.0.1:{srv.server_address[1]}/index.html'

results = []
def check(name, ok, detail=''):
    results.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))

STATE = """() => ({ touchDev: G.touchDev, touchOn: !!(G.touch && G.touch.on), tc: getComputedStyle(document.getElementById('tc')).display, rot: G.rot, canRot: G.canRot,
  tf: document.getElementById('rot').style.transform, scene: G.scene && G.scene.name, hintOn: document.body.classList.contains('rot-hint-on'),
  banner: document.getElementById('rot-banner').classList.contains('show'), bannerBottom: document.getElementById('rot-banner').classList.contains('corner'),
  bannerText: document.getElementById('rot-banner').textContent, held: Object.keys(G.input.down).filter(k => G.input.down[k]),
  canvas: (() => { const r = G.screen.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })() })"""

def open_page(b, query='', init=None, **kw):
    ctx = b.new_context(**kw); pg = ctx.new_page(); errs = []
    if init: pg.add_init_script(init)
    pg.on('pageerror', lambda e: errs.append(str(e)))
    url = BASE + (('&' if '?' in BASE else '?') + query if query else '')
    pg.goto(url, timeout=120000)
    pg.wait_for_function("() => window.G && G.scene && G.scene.name === 'title' && window.G.orient", timeout=120000)
    return ctx, pg, errs

def finger(pg, kind, pid):
    pg.evaluate("([k, id]) => document.body.dispatchEvent(new PointerEvent(k, { pointerType: 'touch', pointerId: id, bubbles: true, cancelable: true, clientX: 50, clientY: 50, isPrimary: id === 5 }))", [kind, pid])

DESKTOP = dict(viewport={'width': 1280, 'height': 720})

with sync_playwright() as p:
    try: b = p.chromium.launch(channel='chrome', args=['--autoplay-policy=no-user-gesture-required'])
    except Exception: b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])

    # ================= 电脑
    ctx, pg, errs = open_page(b, **DESKTOP)
    s = pg.evaluate(STATE)
    check('电脑1 打开时：识别成电脑、手机按键隐藏、不转画面', s['touchDev'] is False and not s['touchOn'] and s['tc'] == 'none' and s['rot'] is False, str(s))
    pg.wait_for_timeout(3000)
    s = pg.evaluate(STATE)
    check('电脑2 第一次打开：左上角弹一次键盘操作提示', s['banner'] and s['bannerBottom'] and 'W A S D' in s['bannerText'] and 'Esc' in s['bannerText'], s['bannerText'])
    Image.open(io.BytesIO(pg.screenshot())).convert('RGB').save(os.path.join(TMP, f'adapt_{NAME}_desktop.png'))

    for keys, want in [(['w'], 'up'), (['a'], 'left'), (['s'], 'down'), (['d'], 'right'), (['ArrowUp'], 'up'), (['ArrowLeft'], 'left'),
                       (['j'], 'attack'), (['k'], 'jump'), (['l'], 'guard'), (['e'], 'ok')]:
        pg.keyboard.down(keys[0]); pg.wait_for_timeout(60)
        held = pg.evaluate(STATE)['held']; pg.keyboard.up(keys[0]); pg.wait_for_timeout(40)
        check(f'电脑3 按住 {keys[0]} → {want}', held == [want], str(held))
    check('电脑4 按键之后手机按键仍然隐藏', not pg.evaluate(STATE)['touchOn'])

    # 鼠标：点菜单第一项开始游戏
    pt = pg.evaluate("() => { const r = G.screen.getBoundingClientRect(); return { x: r.left + 192 * r.width / G.W, y: r.top + 152 * r.height / G.H }; }")
    pg.mouse.click(pt['x'], pt['y']); pg.wait_for_timeout(2500)
    sc = pg.evaluate(STATE)
    check('电脑5 鼠标点标题"从序章开始" → 进入游戏，手机按键仍隐藏', sc['scene'] in ('world', 'video') and not sc['touchOn'], str(sc['scene']))
    check('电脑6 没有页面报错', not errs, str(errs[:2]))
    ctx.close()

    # 提示只弹一次：同一个浏览器环境里再打开，不再弹
    ctx = b.new_context(**DESKTOP)
    pg = ctx.new_page(); pg.goto(BASE, timeout=120000); pg.wait_for_function("() => window.G && G.orient", timeout=60000); pg.wait_for_timeout(3200)
    first = pg.evaluate(STATE)['banner']
    pg2 = ctx.new_page(); pg2.goto(BASE, timeout=120000); pg2.wait_for_function("() => window.G && G.orient", timeout=60000); pg2.wait_for_timeout(3200)
    second = pg2.evaluate(STATE)['banner']
    check('电脑7 键盘提示只在第一次打开时弹（同一浏览器再开一个页面不再弹）', first and not second, f'first={first} second={second}')
    ctx.close()

    # 鼠标翻译出来的触摸（PC 模拟器）
    ctx, pg, errs = open_page(b, **DESKTOP)
    finger(pg, 'pointerdown', 5); pg.wait_for_timeout(200)
    check('电脑8 单指触摸（鼠标翻译出来的）：不弹手机按键', not pg.evaluate(STATE)['touchOn'])
    finger(pg, 'pointerdown', 6); pg.wait_for_timeout(200)
    check('电脑9 两指同时按（真触屏）：弹出手机按键', pg.evaluate(STATE)['touchOn'])
    finger(pg, 'pointerup', 5); finger(pg, 'pointerup', 6)
    pg.keyboard.press('d'); pg.wait_for_timeout(200)
    check('电脑10 再按键盘：手机按键收起', not pg.evaluate(STATE)['touchOn'])
    ctx.close()

    # URL 参数
    ctx, pg, errs = open_page(b, query='touch=1', **DESKTOP)
    pg.keyboard.press('d'); pg.wait_for_timeout(200)
    check('电脑11 ?touch=1：强制显示，按键盘也不收', pg.evaluate(STATE)['touchOn'])
    ctx.close()
    ctx, pg, errs = open_page(b, query='touch=0', **DESKTOP)
    finger(pg, 'pointerdown', 5); finger(pg, 'pointerdown', 6); pg.wait_for_timeout(200)
    check('电脑12 ?touch=0：两指同时按也不显示', not pg.evaluate(STATE)['touchOn'])
    ctx.close()

    # 窗口拉成竖的：不能转画面
    ctx, pg, errs = open_page(b, viewport={'width': 500, 'height': 900})
    s = pg.evaluate(STATE)
    ratio = s['canvas'][0] / max(1, s['canvas'][1])
    check('电脑13 窗口拉成竖的（500×900）：不转画面，16:9 的画面缩进窗口里', s['rot'] is False and s['tf'] == 'none' and abs(ratio - 16 / 9) < 0.05 and s['canvas'][0] <= 500 and not s['hintOn'], str(s))
    pg.wait_for_timeout(3000)
    pg.keyboard.down('d'); pg.wait_for_timeout(60)
    check('电脑14 窄窗口里键盘照样能用', pg.evaluate(STATE)['held'] == ['right'])
    Image.open(io.BytesIO(pg.screenshot())).convert('RGB').save(os.path.join(TMP, f'adapt_{NAME}_desktop_tall.png'))
    ctx.close()
    ctx, pg, errs = open_page(b, query='rot=1', viewport={'width': 500, 'height': 900})
    check('电脑15 ?rot=1：调试用，电脑上也能强制转', pg.evaluate(STATE)['rot'] is True)
    ctx.close()

    # ================= 手机 / 平板
    IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
    ctx, pg, errs = open_page(b, viewport={'width': 393, 'height': 852}, device_scale_factor=3, is_mobile=True, has_touch=True, user_agent=IPHONE)
    s = pg.evaluate(STATE)
    check('手机1 iPhone（竖屏）：识别成触屏设备、手机按键显示、画面转 90°', s['touchDev'] and s['touchOn'] and s['tc'] == 'block' and s['rot'] is True, str(s))
    ctx.close()
    ctx, pg, errs = open_page(b, viewport={'width': 1280, 'height': 800}, device_scale_factor=2, is_mobile=True, has_touch=True)
    s = pg.evaluate(STATE)
    check('手机2 安卓平板（横屏）：手机按键显示、不转画面', s['touchDev'] and s['touchOn'] and s['rot'] is False, str(s))
    ctx.close()
    IPADOS = "Object.defineProperty(navigator, 'platform', { get: () => 'MacIntel' }); Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 5 });"
    ctx, pg, errs = open_page(b, init=IPADOS, viewport={'width': 768, 'height': 1024})
    s = pg.evaluate(STATE)
    check('手机3 iPadOS（电脑版 UA，MacIntel + 多点触控）：识别成触屏设备、竖着时转画面', s['touchDev'] and s['rot'] is True, str(s))
    ctx.close()
    b.close()
if srv: srv.shutdown()
print('总结:', '全部通过' if all(results) else f'有 {results.count(False)} 项失败 / 共 {len(results)} 项')
