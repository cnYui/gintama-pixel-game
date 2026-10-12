"""陀螺仪验收（公网版 orient.js）：用合成的 DeviceOrientationEvent 模拟手机姿势。
  A  没有陀螺仪：只弹一次文字提示
  B  竖着拿的提醒（防抖 / 显示 / 停住 / 点一下就这样玩 / 点击不漏给游戏）、横过来的两个方向、平放和死区、系统自己转横屏
  D  逆时针 / 顺时针两种画面方向下：J 按钮、触摸点标题菜单
  E  浏览器有 requestPermission 但读数很快到（新版 Chrome / Android）：不拦玩家
  C  iPhone：读数迟迟不来 → 弹“轻点屏幕”，同意后才读；拒绝则只弹文字提示
用法: DIST=目录 python orient_test.py [名字]      或      URL=https://aaccx.pw/gintama/ python orient_test.py public
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
if PUBLIC: srv = None; url = PUBLIC + ('&' if '?' in PUBLIC else '?') + 'touch=1'
else:
    srv = S(('127.0.0.1', 0), functools.partial(H, directory=DIST)); threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{srv.server_address[1]}/index.html?touch=1'

# 模拟“没有 requestPermission 接口”的浏览器（Android 上老一点的 Chrome、大多数安卓浏览器）：直接听，不用授权
NO_PERM = "try { delete DeviceOrientationEvent.requestPermission; } catch (e) {} try { if (DeviceOrientationEvent.requestPermission) DeviceOrientationEvent.requestPermission = undefined; } catch (e) {}"

results = []
def check(name, ok, detail=''):
    results.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))

def tilt(pg, beta, gamma):
    pg.evaluate("([b, g]) => window.dispatchEvent(new DeviceOrientationEvent('deviceorientation', { alpha: 0, beta: b, gamma: g }))", [beta, gamma])

STATE = """() => ({ held: G.orient.held, state: G.orient.state, have: G.orient.have, rot: G.rot, dir: G.rotDir, susp: !!G.suspended,
  hintDisp: getComputedStyle(document.getElementById('rot-hint')).display, ccw: document.body.classList.contains('rot-ccw'),
  banner: document.getElementById('rot-banner').classList.contains('show'), bannerText: document.getElementById('rot-banner').textContent, tf: document.getElementById('rot').style.transform,
  hintSub: document.querySelector('#rot-hint small').textContent, scene: G.scene && G.scene.name })"""

def new_page(b, init=None, size=(393, 852), touch=True):
    ctx = b.new_context(viewport={'width': size[0], 'height': size[1]}, device_scale_factor=3 if touch else 1, is_mobile=touch, has_touch=touch)
    pg = ctx.new_page(); errs = []
    if init: pg.add_init_script(init)
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(url if touch else url.replace('?touch=1', '').replace('&touch=1', ''), timeout=120000)
    pg.wait_for_function("() => window.G && G.scene && G.scene.name === 'title' && window.G.orient", timeout=120000)
    return ctx, pg, errs

def pad_tests(pg, label, want):
    pad = pg.evaluate("() => { const r = document.getElementById('tc-pad').getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }")
    for name, (dx, dy), w in [('物理往下', (0, 50), want[0]), ('物理往上', (0, -50), want[1]), ('物理往右', (50, 0), want[2]), ('物理往左', (-50, 0), want[3])]:
        pg.mouse.move(pad['x'], pad['y']); pg.mouse.down(); pg.mouse.move(pad['x'] + dx, pad['y'] + dy, steps=4); pg.wait_for_timeout(120)
        d = pg.evaluate("() => ({ left: !!G.input.down.left, right: !!G.input.down.right, up: !!G.input.down.up, down: !!G.input.down.down })")
        pg.mouse.up(); pg.wait_for_timeout(80)
        only = [k for k, v in d.items() if v]
        check(f'{label}：方向盘 {name} → 游戏 {w}', only == [w], str(only))

def j_test(pg, label):          # 注意：在标题画面按 J = 确认 = 开始游戏，所以这一项放在独立页面最后做
    j = pg.evaluate("() => { const r = document.querySelector('.tc-j').getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; }")
    pg.mouse.move(j['x'], j['y']); pg.mouse.down(); pg.wait_for_timeout(100)
    atk = pg.evaluate("() => !!G.input.down.attack"); pg.mouse.up()
    check(f'{label}：J 按钮按住 → attack', atk)

def tap_title(pg):
    pt = pg.evaluate("""() => { const r = G.rect(G.screen), gx = 192, gy = 152, vx = r.left + gx * r.width / G.W, vy = r.top + gy * r.height / G.H;
        return G.rotDir > 0 ? { x: G.fw - vy, y: vx, dir: G.rotDir } : { x: vy, y: G.fh - vx, dir: G.rotDir }; }""")
    pg.touchscreen.tap(pt['x'], pt['y']); pg.wait_for_timeout(2500)
    return pt['dir'], pg.evaluate("() => G.scene && G.scene.name")

with sync_playwright() as p:
    try: b = p.chromium.launch(channel='chrome', args=['--autoplay-policy=no-user-gesture-required'])
    except Exception: b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])

    # ============ A. 没有陀螺仪读数：只弹一次文字提示
    ctx, pg, errs = new_page(b, init=NO_PERM)
    s = pg.evaluate(STATE)
    check('A1 刚打开：没有提醒、游戏没停', not s['held'] and not s['susp'] and s['hintDisp'] == 'none' and s['rot'] is True, str(s))
    pg.wait_for_timeout(2600)
    s = pg.evaluate(STATE)
    check('A2 2 秒还没有读数 → 弹一次文字提示，游戏不停', s['banner'] and not s['held'] and not s['susp'] and not s['have'])
    ctx.close()

    # ============ B. 有读数：提醒 / 方向 / 平放 / 死区 / 系统转横屏
    ctx, pg, errs = new_page(b, init=NO_PERM)
    tilt(pg, 90, 0); pg.wait_for_timeout(300)
    s = pg.evaluate(STATE)
    check('B1 手机刚竖起来 0.3 秒：先不弹（防抖）', not s['held'], str(s['state']))
    pg.wait_for_timeout(700)
    s = pg.evaluate(STATE)
    check('B2 竖着拿稳定 0.7 秒后：弹提醒、游戏停住', s['held'] and s['susp'] and s['hintDisp'] == 'flex' and s['state'] == 'P' and s['hintSub'] == '横屏才看得全画面和按键', str(s))
    Image.open(io.BytesIO(pg.screenshot())).convert('RGB').save(os.path.join(TMP, f'orient_{NAME}_hint.png'))

    pg.touchscreen.tap(196, 426); pg.wait_for_timeout(400)
    s = pg.evaluate(STATE); leaked = pg.evaluate("() => ({ ok: !!G.input.hits.ok, tap: G.input.tap })")
    check('B3 点提醒 = 就这样玩：提醒消失、游戏恢复', not s['held'] and not s['susp'], str(s['hintDisp']))
    check('B4 这一下点击没有漏给游戏（不会误触发菜单 / 对话）', not leaked['ok'] and leaked['tap'] is None, str(leaked))
    pg.wait_for_timeout(1200)
    check('B5 之后手机还是竖着拿：不再重复提醒', not pg.evaluate(STATE)['held'])

    tilt(pg, 0, -80); pg.wait_for_timeout(600)
    s = pg.evaluate(STATE)
    check('B6 手机逆时针横过来 → 画面顺时针转（rotDir=1）、没有提醒', s['state'] == 'L+' and s['dir'] == 1 and not s['ccw'] and 'rotate(90deg)' in s['tf'] and not s['held'], str(s))
    tilt(pg, 90, 0); pg.wait_for_timeout(1100)
    check('B7 横过来之后又竖起来：重新提醒（上次的“就这样玩”失效）', pg.evaluate(STATE)['held'])

    tilt(pg, 0, 80); pg.wait_for_timeout(600)
    s = pg.evaluate(STATE)
    check('B8 手机顺时针横过来 → 画面逆时针转（rotDir=-1）、提醒消失', s['state'] == 'L-' and s['dir'] == -1 and s['ccw'] and 'rotate(-90deg)' in s['tf'] and not s['held'] and not s['susp'], str(s))
    shot = Image.open(io.BytesIO(pg.screenshot())).convert('RGB')
    shot.rotate(-90, expand=True).save(os.path.join(TMP, f'orient_{NAME}_ccw_upright.png'))       # 顺时针转 90° = 手机顺时针横过来看到的样子
    pad_tests(pg, '逆时针模式', ['left', 'right', 'down', 'up'])

    tilt(pg, 0, -80); pg.wait_for_timeout(600)
    s = pg.evaluate(STATE)
    check('B9 再逆时针横回来 → 回到顺时针转', s['state'] == 'L+' and s['dir'] == 1 and not s['ccw'], str(s))
    pad_tests(pg, '顺时针模式', ['right', 'left', 'up', 'down'])

    tilt(pg, 0, 0); pg.wait_for_timeout(1000)
    s = pg.evaluate(STATE)
    check('B10 手机平放：保持原样（不提醒、方向不变）', s['state'] == 'L+' and s['dir'] == 1 and not s['held'], str(s))
    tilt(pg, 45, -40); pg.wait_for_timeout(1000)          # 落在 30°–60° 死区里
    check('B11 手机斜着（死区）：保持原样', pg.evaluate(STATE)['state'] == 'L+')

    tilt(pg, 90, 0); pg.wait_for_timeout(1100)
    held_before = pg.evaluate(STATE)['held']
    pg.set_viewport_size({'width': 852, 'height': 393}); pg.wait_for_timeout(600)
    s = pg.evaluate(STATE)
    check('B12 手机竖着拿但系统已转成横屏（没锁旋转）：不提醒、不转画面', held_before and not s['held'] and not s['rot'] and not s['susp'] and s['tf'] == 'none', str(s))
    check('B13 没有页面报错', not errs, str(errs[:2]))
    ctx.close()

    # ============ D. 两个画面方向下：J 按钮、触摸点标题（各用一个新页面，因为在标题按 J / 点菜单都会开始游戏）
    for label, gamma, want_dir in [('逆时针模式', 80, -1), ('顺时针模式', -80, 1)]:
        ctx, pg, errs = new_page(b, init=NO_PERM)
        tilt(pg, 0, gamma); pg.wait_for_timeout(600)
        check(f'D 手机倒向{"顺" if want_dir < 0 else "逆"}时针：画面方向对', pg.evaluate(STATE)['dir'] == want_dir)
        j_test(pg, label)
        ctx.close()
        ctx, pg, errs = new_page(b, init=NO_PERM)
        tilt(pg, 0, gamma); pg.wait_for_timeout(600)
        before = pg.evaluate("() => G.scene.name")
        d, sc = tap_title(pg)
        check(f'D {label}：触摸点标题"从序章开始" → 进入游戏', before == 'title' and d == want_dir and sc in ('world', 'video'), f'before={before} dir={d} scene={sc}')
        check(f'D {label}：没有页面报错', not errs, str(errs[:2]))
        ctx.close()

    # ============ E. 浏览器有 requestPermission，但读数很快就到（新版 Chrome / Android）：不能拦玩家
    stub = ("window.__perm = 0; DeviceOrientationEvent.requestPermission = () => { window.__perm++; return Promise.resolve('granted'); };"
            "addEventListener('load', () => setTimeout(() => dispatchEvent(new DeviceOrientationEvent('deviceorientation', { alpha: 0, beta: 0, gamma: -80 })), 300));")
    ctx, pg, errs = new_page(b, init=stub)
    pg.wait_for_timeout(2000)
    s = pg.evaluate(STATE)
    check('E 有 requestPermission 但读数很快到：不弹"轻点屏幕"、没申请权限、方向正常', not s['held'] and pg.evaluate('() => window.__perm') == 0 and s['state'] == 'L+', str(s))
    ctx.close()

    # ============ C. iPhone：读数迟迟不来 → 弹“轻点屏幕”，同意后才读；拒绝则只弹文字提示
    for verdict in ('granted', 'denied'):
        stub = "window.__perm = 0; DeviceOrientationEvent.requestPermission = () => { window.__perm++; return Promise.resolve('%s'); };" % verdict
        ctx, pg, errs = new_page(b, init=stub)
        pg.wait_for_function("() => G.orient.held", timeout=5000)
        s = pg.evaluate(STATE)
        check(f'C({verdict})1 竖着打开、没有读数：1.2 秒后弹"轻点屏幕"，游戏停住', s['held'] and s['susp'] and '轻点屏幕后' in s['hintSub'], str(s['hintSub']))
        pg.touchscreen.tap(196, 426); pg.wait_for_timeout(600)
        s = pg.evaluate(STATE); perm = pg.evaluate('() => window.__perm')
        check(f'C({verdict})2 点一下：申请了 1 次权限、提醒收起', perm == 1 and not s['held'], f'perm={perm}')
        if verdict == 'granted':
            tilt(pg, 90, 0); pg.wait_for_timeout(1100)
            s = pg.evaluate(STATE)
            check('C(granted)3 同意之后：竖着拿会弹正式的提醒（文案不同）', s['held'] and s['hintSub'] == '横屏才看得全画面和按键', str(s['hintSub']))
        else:
            pg.wait_for_timeout(600)
            s = pg.evaluate(STATE)
            check('C(denied)3 拒绝之后：弹一次文字提示，游戏照常', s['banner'] and not s['susp'])
        ctx.close()
    # ============ F. 电脑（没有触屏）上把窗口拉高：不弹手机专用的提示，游戏照常
    ctx, pg, errs = new_page(b, size=(500, 900), touch=False)
    pg.wait_for_timeout(3200)
    s = pg.evaluate(STATE)
    check('F 电脑上窗口拉高（没有触屏、没有读数）：不转画面，不弹手机相关的授权 / 提醒 / 文字提示（可以有键盘提示）',
          s['rot'] is False and not s['held'] and not s['susp'] and (not s['banner'] or s['bannerText'].startswith('键盘')), str(s))
    ctx.close()
    b.close()
if srv: srv.shutdown()
print('总结:', '全部通过' if all(results) else f'有 {results.count(False)} 项失败 / 共 {len(results)} 项')
