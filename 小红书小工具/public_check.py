"""从公网访问游戏，测流量和缓存命中：冷启动访客 / 边缘缓存已热的第二个访客 / 同一访客刷新。
用法: python public_check.py [URL]
统计每个阶段的请求数、传输字节（压缩后、含响应头）、按类型拆分、Cloudflare 缓存状态（HIT = 没打到源站）。
"""
import sys, time
from collections import Counter, defaultdict
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else 'https://aaccx.pw/gintama/'

def kind(url, ctype):
    u = url.split('?')[0].lower()
    for ext, k in (('.mp3', 'mp3'), ('.mp4', 'mp4'), ('.js', 'js'), ('.json', 'json'), ('.webp', 'webp'), ('.html', 'html')):
        if u.endswith(ext): return k
    return 'html' if 'text/html' in ctype else 'other'

def summarize(title, recs, fails):
    n = len(recs); tot = sum(r['body'] + r['hdr'] for r in recs)
    by = defaultdict(lambda: [0, 0])
    for r in recs:
        k = kind(r['url'], r['ctype']); by[k][0] += 1; by[k][1] += r['body'] + r['hdr']
    cache = Counter(r['cache'] for r in recs); status = Counter(r['status'] for r in recs)
    print(f'  [{title}] {n} 个请求, 传输 {tot/1e6:.2f} MB')
    print('     类型: ' + ', '.join(f'{k} {v[0]}个/{v[1]/1e6:.2f}MB' for k, v in sorted(by.items(), key=lambda x: -x[1][1])))
    print('     Cloudflare 缓存: ' + ', '.join(f'{k}={v}' for k, v in cache.most_common()) + '   状态码: ' + ', '.join(f'{k}={v}' for k, v in status.most_common()))
    enc = Counter(r['enc'] for r in recs if kind(r['url'], r['ctype']) in ('js', 'html', 'json'))
    print('     文本类压缩: ' + ', '.join(f'{k}={v}' for k, v in enc.most_common()))
    if fails: print('     !! 请求失败:', fails[:3])
    bad = [r for r in recs if r['status'] >= 400]
    if bad: print('     !! 4xx/5xx:', [(r['status'], r['url'][-60:]) for r in bad[:4]])
    return tot, n

def visitor(b, label, reload_after=False):
    ctx = b.new_context(viewport={'width': 1152, 'height': 648})
    pg = ctx.new_page(); recs = []; fails = []
    def done(req):
        try:
            resp = req.response(); sz = req.sizes(); h = resp.headers
            recs.append(dict(url=req.url, status=resp.status, cache=h.get('cf-cache-status', '-'), enc=h.get('content-encoding', '-'),
                             ctype=h.get('content-type', '-'), body=sz['responseBodySize'], hdr=sz['responseHeadersSize']))
        except Exception:
            pass
    pg.on('requestfinished', done); pg.on('requestfailed', lambda r: fails.append((r.url[-60:], r.failure)))
    print(f'--- {label}')
    t0 = time.time(); pg.goto(URL, timeout=120000)
    pg.wait_for_function("() => window.G && G.scene && G.scene.name === 'title'", timeout=120000)
    t_title = time.time() - t0
    pg.wait_for_timeout(1500)
    print(f'  标题画面出现用时 {t_title:.1f}s')
    t1, n1 = summarize('打开页面到标题', recs, fails)
    mark = len(recs)
    pg.keyboard.press('Shift'); pg.wait_for_timeout(300); pg.keyboard.press('Enter')       # 从序章开始：开场视频 + 音乐 + 音效
    pg.wait_for_timeout(14000)
    st = pg.evaluate("() => ({ scene: G.scene && G.scene.name, music: G.audio.name })")
    t2, n2 = summarize(f'开始游戏后 14 秒（scene={st["scene"]}）', recs[mark:], fails)
    out = {'first': (t1, n1), 'play': (t2, n2)}
    if reload_after:
        mark = len(recs); pg.reload(); pg.wait_for_function("() => window.G && G.scene && G.scene.name === 'title'", timeout=120000); pg.wait_for_timeout(1500)
        out['reload'] = summarize('同一访客刷新页面（浏览器缓存已热）', recs[mark:], fails)
    ctx.close()
    return out

with sync_playwright() as p:
    try: b = p.chromium.launch(channel='chrome', args=['--autoplay-policy=no-user-gesture-required'])
    except Exception: b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    v1 = visitor(b, '访客 A：第一个访客（浏览器和 Cloudflare 边缘都是冷的）', reload_after=True)
    v2 = visitor(b, '访客 B：第二个访客（新浏览器，但边缘节点已经有缓存）')
    b.close()
print('=== 结论数据')
print(f"访客 A 打开到标题: {v1['first'][0]/1e6:.2f} MB / {v1['first'][1]} 个请求;  进游戏 14 秒又加 {v1['play'][0]/1e6:.2f} MB / {v1['play'][1]} 个请求")
print(f"访客 A 刷新一次:   {v1['reload'][0]/1e6:.3f} MB / {v1['reload'][1]} 个请求")
print(f"访客 B 打开到标题: {v2['first'][0]/1e6:.2f} MB / {v2['first'][1]} 个请求;  进游戏 14 秒又加 {v2['play'][0]/1e6:.2f} MB / {v2['play'][1]} 个请求")
