"""验收：在小红书容器同款 CSP 下跑 dist，15 章逐个进入 + 开场视频 + 触屏模式 + 与原版画面对比。输出 _tmp/sweep.out。"""
import functools, http.server, os, socketserver, sys, threading, time, io
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.environ.get('DIST') or os.path.join(HERE, 'dist'); ORIG = r'D:\CodeWorkSpace\gintama-pixel-game\游戏'
TMP = os.path.join(HERE, '_tmp'); os.makedirs(TMP, exist_ok=True)
CSP = ("default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
       "font-src 'self'; media-src 'self'; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'")

def serve(root, csp):
    class H(http.server.SimpleHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'      # 长连接：否则两千多个文件会把 Windows 临时端口耗尽
        def end_headers(self):
            if csp: self.send_header('Content-Security-Policy', CSP)
            self.send_header('Cache-Control', 'no-store'); super().end_headers()
        def log_message(self, *a): pass
    class S(socketserver.ThreadingTCPServer):
        request_queue_size = 1024
        daemon_threads = True
        def handle_error(self, *a): pass
    srv = S(('127.0.0.1', 0), functools.partial(H, directory=root))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f'http://127.0.0.1:{srv.server_address[1]}/index.html'

srv_d, url_d = serve(DIST, not os.environ.get('NOCSP')); srv_o, url_o = serve(ORIG, False)
INIT = "document.addEventListener('securitypolicyviolation', e => (window.__csp = window.__csp || []).push(e.violatedDirective + ' ' + e.blockedURI));"
BROKEN = "() => Object.entries(G.images).filter(([k, im]) => im.complete && im.naturalWidth === 0).map(([k]) => k)"

def open_page(b, url, touch=False):
    ctx = b.new_context(viewport={'width': 844, 'height': 390} if touch else {'width': 1152, 'height': 648}, has_touch=touch)
    pg = ctx.new_page(); pg.add_init_script(INIT)
    log = {'err': [], 'bad': []}
    pg.on('console', lambda m: log['err'].append(m.text + ' @' + str((m.location or {}).get('url', '')[-60:])) if m.type == 'error' and 'favicon' not in str((m.location or {}).get('url', '')) else None)
    pg.on('pageerror', lambda e: log['err'].append('PAGEERROR ' + str(e)))
    pg.on('response', lambda r: log['bad'].append(f'{r.status} {r.url.split("/", 3)[-1]}') if r.status >= 400 and 'favicon' not in r.url else None)
    pg.goto(url + ('?touch=1' if touch else ''), timeout=120000)
    pg.wait_for_function("() => window.G && G.scene && G.scene.name === 'title'", timeout=120000)
    return ctx, pg, log

with sync_playwright() as p:
    try: b = p.chromium.launch(channel='chrome', args=['--autoplay-policy=no-user-gesture-required']); print('浏览器: 本机 Chrome（带 H.264）')
    except Exception: b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); print('浏览器: Playwright Chromium（无 H.264，mp4 视频这里放不了）')

    # 1) 标题画面：dist(CSP) vs 原版 逐像素对比（花瓣是随机的，所以允许少量差异）
    shots = {}
    for name, url in [('dist', url_d), ('orig', url_o)]:
        ctx, pg, log = open_page(b, url); pg.wait_for_timeout(800)
        shots[name] = Image.open(io.BytesIO(pg.screenshot())).convert('RGB'); ctx.close()
        if name == 'dist': print('标题: 报错', log['err'][:3] or '无', '| 4xx/5xx', log['bad'][:3] or '无')
    diff = np.abs(np.asarray(shots['dist']).astype(int) - np.asarray(shots['orig']).astype(int)).max(axis=2)
    print(f'标题画面与原版对比: 差异像素 {100*(diff>24).mean():.2f}%（花瓣随机，<1% 视为一致）')
    shots['dist'].save(os.path.join(TMP, 'sweep_title_dist.png'))

    # 2) 15 章逐个进入
    names = ['序章', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '终章']
    allbad = False
    for i in ([int(x) for x in os.environ['CH'].split(',')] if os.environ.get('CH') else range(15)):
        ctx, pg, log = open_page(b, url_d)
        pg.keyboard.press('Shift'); pg.wait_for_timeout(300)
        if i == 0:
            pg.keyboard.press('Enter')                     # 从序章开始
        else:
            pg.keyboard.press('ArrowDown'); pg.wait_for_timeout(150); pg.keyboard.press('Enter'); pg.wait_for_timeout(400)   # 选择章节
            for _ in range(i): pg.keyboard.press('ArrowDown'); pg.wait_for_timeout(150)
            pg.keyboard.press('Enter')
        pg.wait_for_timeout(9000 if i == 0 else 6000)
        st = pg.evaluate("() => ({scene: G.scene && G.scene.name, stage: G.world && G.world.stage ? G.world.stage.id : null, ch: G.lastChapter, music: G.audio.name, csp: window.__csp || []})")
        broken = pg.evaluate(BROKEN)
        ok = not log['err'] and not log['bad'] and not broken and not st['csp'] and st['ch'] == i
        allbad |= not ok
        print(f'第{names[i]}章: {"OK " if ok else "有问题"} scene={st["scene"]} stage={st["stage"]} 音乐={st["music"]}' +
              (f' | 报错={log["err"][:2]} 4xx={log["bad"][:3]} 坏图={broken[:3]} CSP={st["csp"][:2]}' if not ok else ''))
        if i in (0, 7, 14): pg.screenshot(path=os.path.join(TMP, f'sweep_ch{i}.png'))
        ctx.close()

    # 3) 开场视频（mp4）是否能放
    ctx, pg, log = open_page(b, url_d); pg.keyboard.press('Shift')
    pg.evaluate("() => { window.__vp = G.S.video('s00a'); }"); pg.wait_for_timeout(3000)
    v = pg.evaluate("() => ({scene: G.scene.name, t: G.scene.t})")
    print('开场视频 s00a 3 秒后:', v, '→', '在播放' if v['scene'] == 'video' and v['t'] > 2 else '没放出来（Playwright 自带 Chromium 不支持 H.264 时属正常）')
    pg.screenshot(path=os.path.join(TMP, 'sweep_video.png')); ctx.close()

    # 4) 触屏模式：全屏按钮应已隐藏，且没有报错
    ctx, pg, log = open_page(b, url_d, touch=True); pg.wait_for_timeout(800)
    fs = pg.evaluate("() => { const e = document.getElementById('tc-full'); return e ? getComputedStyle(e).display : 'none-element'; }")
    print('触屏模式: 全屏按钮 display =', fs, '| 报错', log['err'][:3] or '无', '| CSP 违规', pg.evaluate("() => window.__csp || []") or '无')
    pg.screenshot(path=os.path.join(TMP, 'sweep_touch.png')); ctx.close()
    b.close()
print('总结:', '有问题，见上' if allbad else '15 章全部通过')
srv_d.shutdown(); srv_o.shutdown()
