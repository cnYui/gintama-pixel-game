"""竖屏旋转验收：模拟手机竖屏（393x852 @3x，触屏），检查
  1. 画面确实转了 90°（G.rot），画布在游戏横屏坐标里居中
  2. 触摸点标题菜单第一项 → 游戏开始（点画面坐标换算对）
  3. 方向盘：物理上往 下 / 上 / 右 / 左 推，分别应得到 游戏的 右 / 左 / 上 / 下
  4. J 按钮按住 → attack 键按下
用法: DIST=目录 [NOCSP=1] python portrait_test.py [名字]    截图存到 _tmp/portrait_<名字>*.png（另存一张转回正的方便看）
"""
import functools, http.server, io, os, socketserver, sys, threading
from playwright.sync_api import sync_playwright
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.environ.get('DIST') or os.path.join(HERE, 'dist-silent')
NAME = sys.argv[1] if len(sys.argv) > 1 else os.path.basename(DIST.rstrip('/\\'))
TMP = os.path.join(HERE, '_tmp'); os.makedirs(TMP, exist_ok=True)
CSP = ("default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
       "font-src 'self'; media-src 'self'; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'")

class H(http.server.SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def end_headers(self):
        if not os.environ.get('NOCSP'): self.send_header('Content-Security-Policy', CSP)
        self.send_header('Cache-Control', 'no-store'); super().end_headers()
    def log_message(self, *a): pass
class S(socketserver.ThreadingTCPServer):
    request_queue_size = 1024; daemon_threads = True
    def handle_error(self, *a): pass
PUBLIC = os.environ.get('URL')          # 给了 URL 就直接测公网地址，不起本地服务器
if PUBLIC:
    srv = None; url = PUBLIC + ('&' if '?' in PUBLIC else '?') + 'touch=1'
else:
    srv = S(('127.0.0.1', 0), functools.partial(H, directory=DIST)); threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{srv.server_address[1]}/index.html?touch=1'

results = []
def check(name, ok, detail=''):
    results.append(ok); print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))

with sync_playwright() as p:
    try: b = p.chromium.launch(channel='chrome', args=['--autoplay-policy=no-user-gesture-required'])
    except Exception: b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    ctx = b.new_context(viewport={'width': 393, 'height': 852}, device_scale_factor=3, is_mobile=True, has_touch=True)
    pg = ctx.new_page(); errs = []
    if os.environ.get('SENSOR'):      # 公网版：模拟“有陀螺仪、手机已经横过来”，不然没有读数时会弹授权 / 提醒盖住按键
        pg.add_init_script("try { delete DeviceOrientationEvent.requestPermission; } catch (e) {} "
                           "addEventListener('load', () => setTimeout(() => dispatchEvent(new DeviceOrientationEvent('deviceorientation', { alpha: 0, beta: 0, gamma: -80 })), 300));")
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(url, timeout=120000)
    pg.wait_for_function("() => window.G && G.scene && G.scene.name === 'title'", timeout=120000)
    pg.wait_for_timeout(1500)
    info = pg.evaluate("""() => { const r = G.rect(G.screen); return { rot: G.rot, fw: G.fw, fh: G.fh, vw: G.vw, vh: G.vh, scale: G.scale,
        canvas: { l: r.left, t: r.top, w: r.width, h: r.height }, touchOn: G.touch && G.touch.on, portraitPrompt: getComputedStyle(document.getElementById('tc-rotate')).display,
        suspended: !!G.suspended } }""")
    print('页面状态:', info)
    check('竖屏时进入旋转模式', info['rot'] is True and info['vw'] == 852 and info['vh'] == 393)
    check('画布在横屏坐标里水平居中', abs((info['canvas']['l'] + info['canvas']['w'] / 2) - info['vw'] / 2) < 2 and abs((info['canvas']['t'] + info['canvas']['h'] / 2) - info['vh'] / 2) < 2, str(info['canvas']))
    check('没有"请横过来"提示、游戏没被暂停', info['portraitPrompt'] == 'none' and not info['suspended'])
    shot = Image.open(io.BytesIO(pg.screenshot())).convert('RGB')
    shot.save(os.path.join(TMP, f'portrait_{NAME}.png'))
    shot.rotate(90, expand=True).save(os.path.join(TMP, f'portrait_{NAME}_upright.png'))      # 逆时针转 90° = 手机逆时针转着看的样子

    # 方向盘：物理方向 → 游戏方向（顺时针转 90°：物理往下 = 游戏往右；物理往右 = 游戏往上）
    pad = pg.evaluate("() => { const r = document.getElementById('tc-pad').getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }")
    for label, (dx, dy), want in [('物理往下', (0, 50), 'right'), ('物理往上', (0, -50), 'left'), ('物理往右', (50, 0), 'up'), ('物理往左', (-50, 0), 'down')]:
        pg.mouse.move(pad['x'], pad['y']); pg.mouse.down(); pg.mouse.move(pad['x'] + dx, pad['y'] + dy, steps=4); pg.wait_for_timeout(120)
        d = pg.evaluate("() => ({ left: !!G.input.down.left, right: !!G.input.down.right, up: !!G.input.down.up, down: !!G.input.down.down })")
        pg.mouse.up(); pg.wait_for_timeout(80)
        only = [k for k, v in d.items() if v]
        check(f'方向盘 {label} → 游戏 {want}', only == [want], str(only))

    # J 按钮
    j = pg.evaluate("() => { const r = document.querySelector('.tc-j').getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }")
    pg.mouse.move(j['x'], j['y']); pg.mouse.down(); pg.wait_for_timeout(100)
    atk = pg.evaluate("() => !!G.input.down.attack"); pg.mouse.up()
    check('J 按钮按住 → attack 键', atk)

    # 点标题菜单第一项（游戏坐标 192,152）→ 开始游戏
    pt = pg.evaluate("""() => { const r = G.rect(G.screen), gx = 192, gy = 152;
        const vx = r.left + gx * r.width / G.W, vy = r.top + gy * r.height / G.H; return { x: G.fw - vy, y: vx }; }""")
    pg.touchscreen.tap(pt['x'], pt['y'])
    pg.wait_for_timeout(2500)
    sc = pg.evaluate("() => G.scene && G.scene.name")
    check('触摸点标题"从序章开始" → 进入游戏', sc in ('world', 'video'), f'scene={sc}')
    pg.screenshot(path=os.path.join(TMP, f'portrait_{NAME}_play.png'))
    check('没有页面报错', not errs, str(errs[:2]))
    b.close()
if srv: srv.shutdown()
print('总结:', '全部通过' if all(results) else f'有 {results.count(False)} 项失败')
