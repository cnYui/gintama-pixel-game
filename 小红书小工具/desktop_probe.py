"""电脑端表现探测：公网版在不同"电脑"场景下，触屏按键显不显示、会不会被旋转、键盘能不能用。
用法: python desktop_probe.py [URL]"""
import io, os, sys
from playwright.sync_api import sync_playwright
from PIL import Image

URL = sys.argv[1] if len(sys.argv) > 1 else 'https://aaccx.pw/gintama/'
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_tmp'); os.makedirs(TMP, exist_ok=True)
S = """() => ({ touchOn: !!(G.touch && G.touch.on), tcDisp: getComputedStyle(document.getElementById('tc')).display, rot: G.rot, scene: G.scene && G.scene.name,
  coarse: matchMedia('(pointer: coarse)').matches, hover: matchMedia('(hover: hover)').matches, maxTouch: navigator.maxTouchPoints,
  canvas: (() => { const r = G.screen.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })(), keys: Object.keys(G.input.down).filter(k => G.input.down[k]) })"""

def load(b, **kw):
    ctx = b.new_context(**kw); pg = ctx.new_page()
    pg.goto(URL, timeout=120000)
    pg.wait_for_function("() => window.G && G.scene && G.scene.name === 'title'", timeout=120000)
    pg.wait_for_timeout(1200)
    return ctx, pg

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome', args=['--autoplay-policy=no-user-gesture-required'])

    print('=== 1. 普通电脑（1280x720，鼠标）')
    ctx, pg = load(b, viewport={'width': 1280, 'height': 720})
    print('  打开时   ', pg.evaluate(S))
    pg.mouse.click(640, 360); pg.wait_for_timeout(300)
    print('  点一下鼠标', pg.evaluate(S)['touchOn'])
    pg.keyboard.down('d'); pg.wait_for_timeout(150)
    print('  按住 D   ', pg.evaluate(S)['keys'])
    pg.keyboard.up('d')
    Image.open(io.BytesIO(pg.screenshot())).convert('RGB').save(os.path.join(TMP, 'desktop_normal.png'))
    ctx.close()

    print('=== 2. 电脑上把窗口拉成竖的（500x900，鼠标）——游戏会不会被转 90°')
    ctx, pg = load(b, viewport={'width': 500, 'height': 900})
    print('  ', pg.evaluate(S))
    Image.open(io.BytesIO(pg.screenshot())).convert('RGB').save(os.path.join(TMP, 'desktop_tall.png'))
    ctx.close()

    print('=== 3. 带触摸屏的电脑（有触摸，但主指针是鼠标；这台测试电脑就是）：真手指碰一下')
    ctx, pg = load(b, viewport={'width': 1280, 'height': 720}, has_touch=True)
    s = pg.evaluate(S); print('  打开时   ', s)
    pg.touchscreen.tap(640, 360); pg.wait_for_timeout(500)
    print('  手指碰一下', pg.evaluate(S)['touchOn'], '→ 再按 D 键后:', end=' ')
    pg.keyboard.press('d'); pg.wait_for_timeout(300); print(pg.evaluate(S)['touchOn'])
    ctx.close()

    print('=== 4. 手机尺寸 + 触屏（对照）')
    ctx, pg = load(b, viewport={'width': 852, 'height': 393}, device_scale_factor=3, is_mobile=True, has_touch=True)
    print('  ', pg.evaluate(S))
    ctx.close()
    b.close()
