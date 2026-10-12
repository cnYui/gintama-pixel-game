"""模拟小红书容器的 CSP，把一个打包目录跑起来：加载 → 标题 → 点“从序章开始” → 看开场视频/序章，收集 CSP 违规、控制台报错、请求失败。

用法: python csp_smoke.py <目录> [--touch]
CSP 按 zip-artifact-spec.md §3 写：脚本只许包内外链；样式可内联；图片 self/data/blob；音视频只许 self；iframe/object 全禁；不联网。
"""
import functools, http.server, os, socketserver, sys, threading, time, json
from playwright.sync_api import sync_playwright

root = os.path.abspath(sys.argv[1]); touch = '--touch' in sys.argv
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_tmp'); os.makedirs(OUT, exist_ok=True)

CSP = ("default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
       "font-src 'self'; media-src 'self'; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'")

class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Content-Security-Policy', CSP); self.send_header('Cache-Control', 'no-store'); super().end_headers()
    def log_message(self, *a): pass
srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(H, directory=root))
srv.daemon_threads = True; threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{srv.server_address[1]}/index.html' + ('?touch=1' if touch else '')

errs = []; csp = []; failed = []
with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    ctx = b.new_context(viewport={'width': 844, 'height': 390} if touch else {'width': 1152, 'height': 648}, has_touch=touch)
    pg = ctx.new_page()
    pg.add_init_script("document.addEventListener('securitypolicyviolation', e => (window.__csp = window.__csp || []).push(e.violatedDirective + ' ' + e.blockedURI));")
    pg.on('console', lambda m: errs.append(f'[{m.type}] {m.text}') if m.type in ('error', 'warning') else None)
    pg.on('pageerror', lambda e: errs.append(f'[pageerror] {e}'))
    pg.on('requestfailed', lambda r: failed.append(f'{r.url} {r.failure}'))
    t0 = time.time()
    pg.goto(url)
    try:
        pg.wait_for_function("() => window.G && G.scene && G.scene.name === 'title'", timeout=120000)
        print(f'标题画面出现，加载用时 {time.time()-t0:.1f}s')
    except Exception as e:
        print('!! 标题没出现:', e, '| loading 文字:', pg.evaluate("() => (document.getElementById('loading')||{}).textContent"))
    pg.wait_for_timeout(600)
    pg.screenshot(path=os.path.join(OUT, f'smoke_title{"_touch" if touch else ""}.png'))
    pg.keyboard.press('Enter'); pg.wait_for_timeout(1200)       # 先按一次让音频解锁
    pg.keyboard.press('Enter')                                  # 菜单第 0 项：从序章开始
    scenes = []
    for i in range(24):
        pg.wait_for_timeout(500)
        scenes.append(pg.evaluate("() => G.scene ? G.scene.name : null"))
        if i in (2, 8, 20): pg.screenshot(path=os.path.join(OUT, f'smoke_play{i}{"_touch" if touch else ""}.png'))
    print('开始游戏后 12 秒内的场景序列:', scenes)
    info = pg.evaluate("""() => ({ csp: window.__csp || [], music: G.audio && G.audio.name, videoOK: !!document.createElement('video').canPlayType('video/webm; codecs="vp9, opus"') })""")
    print('CSP 违规:', info['csp'] or '无')
    print('当前音乐:', info['music'])
    b.close()
print('控制台错误/警告:', errs[:15] or '无')
print('请求失败:', failed[:10] or '无')
srv.shutdown()
