"""标题曲的真实下载量：在标题画面停留 N 秒，用 CDP 的 Network.dataReceived 累计各个资源实际收到的字节（含被中止的流式请求）。
用法: python title_bytes.py [秒数，默认 25]"""
import sys, collections
from playwright.sync_api import sync_playwright

URL = 'https://aaccx.pw/gintama/'
SECS = int(sys.argv[1]) if len(sys.argv) > 1 else 25
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome', args=['--autoplay-policy=no-user-gesture-required'])
    ctx = b.new_context(viewport={'width': 1152, 'height': 648}); pg = ctx.new_page()
    cdp = ctx.new_cdp_session(pg); cdp.send('Network.enable')
    urls = {}; got = collections.Counter(); reqs = collections.Counter(); ranges = collections.defaultdict(list)
    cdp.on('Network.requestWillBeSent', lambda e: (urls.__setitem__(e['requestId'], e['request']['url']), ranges[e['request']['url']].append(e['request'].get('headers', {}).get('Range', '-'))))
    cdp.on('Network.dataReceived', lambda e: got.update({urls.get(e['requestId'], '?'): e.get('encodedDataLength', 0)}))
    pg.goto(URL, timeout=120000)
    pg.wait_for_function("() => window.G && G.scene && G.scene.name === 'title'", timeout=120000)
    pg.keyboard.press('Shift')
    pg.wait_for_timeout(SECS * 1000)
    a = pg.evaluate("() => { const e = G.audio.el; return e ? { name: G.audio.name, t: +e.currentTime.toFixed(1), buffered: e.buffered.length ? +e.buffered.end(e.buffered.length - 1).toFixed(1) : 0, dur: +e.duration.toFixed(1) } : null; }")
    tot = sum(got.values())
    def kind(u):
        u = u.split('?')[0]
        return 'title_song.mp3' if u.endswith('title_song.mp3') else ('js' if u.endswith('.js') else ('mp3(其它)' if u.endswith('.mp3') else ('mp4' if u.endswith('.mp4') else 'html/其它')))
    by = collections.Counter()
    for u, n in got.items(): by[kind(u)] += n
    print(f'在标题画面停留 {SECS} 秒，网络层共收到 {tot/1e6:.2f} MB')
    for k, v in by.most_common(): print(f'   {k:14s} {v/1e6:.2f} MB')
    ts = [u for u in got if u.endswith('title_song.mp3')]
    print('标题曲请求的 Range 头:', ranges[ts[0]] if ts else None)
    print('播放状态:', a, f'→ 已缓冲 {a["buffered"]}/{a["dur"]} 秒' if a else '')
    b.close()
