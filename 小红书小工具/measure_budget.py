"""量一下压进 10MB 的可能性：PNG→WebP 无损、音频不同码率。只读原 assets，输出放 _tmp/budget。"""
import os, io, json, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import numpy as np

G = r'D:\CodeWorkSpace\gintama-pixel-game\游戏'
D = os.path.join(G, 'dist-compressed')
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_tmp', 'budget'); os.makedirs(TMP, exist_ok=True)

s = open(os.path.join(D, 'data.js'), encoding='utf-8').read()
d = json.loads(s[len('window.GAME_DATA = '):].strip().rstrip(';'))
refs = set()
def walk(o):
    if isinstance(o, str):
        if re.search(r'\.(png|mp3)$', o, re.I) and not o.startswith(('http', 'data:')): refs.add(o)
    elif isinstance(o, list): [walk(v) for v in o]
    elif isinstance(o, dict): [walk(v) for v in o.values()]
walk(d)
refs.add('assets/bg/war/tent.png')          # 代码里硬写的，data.js 没登记
pngs = sorted(r for r in refs if r.endswith('.png')); mp3s = sorted(r for r in refs if r.endswith('.mp3'))

# 1) PNG → WebP 无损
def to_webp(r):
    im = Image.open(os.path.join(G, r)).convert('RGBA')
    b = io.BytesIO(); im.save(b, 'WEBP', lossless=True, quality=100, method=6, exact=False)
    return r, len(b.getvalue()), os.path.getsize(os.path.join(G, r)), b.getvalue()
with ThreadPoolExecutor(8) as ex: res = list(ex.map(to_webp, pngs))
png_total = sum(x[2] for x in res); webp_total = sum(x[1] for x in res)
bad = 0
for r, _, _, data in res[::40]:       # 抽样核对无损（可见像素完全一致）
    a = np.asarray(Image.open(os.path.join(G, r)).convert('RGBA')).astype(int); b = np.asarray(Image.open(io.BytesIO(data)).convert('RGBA')).astype(int)
    vis = a[..., 3] > 0
    if np.abs((a - b) * vis[..., None]).max() > 0 or not np.array_equal(a[..., 3], b[..., 3]): bad += 1
print(f'PNG {len(pngs)} 张: 原 {png_total/1e6:.2f} MB → WebP 无损 {webp_total/1e6:.2f} MB (抽样 {len(res[::40])} 张，不一致 {bad})')

# 2) 音频：从原 mp3 重编码
def enc(args):
    r, br, sr = args
    out = os.path.join(TMP, f'{br}_{sr}_' + r.replace('/', '_'))
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', os.path.join(G, r), '-ac', '1', '-ar', str(sr), '-b:a', f'{br}k', out], check=True)
    return os.path.getsize(out)
for br, sr in [(64, 44100), (48, 32000), (40, 32000), (32, 24000)]:
    music = [r for r in mp3s if '/music/' in r or '/user/' in r]; sfx = [r for r in mp3s if '/sfx/' in r]
    with ThreadPoolExecutor(8) as ex:
        m = sum(ex.map(enc, [(r, br, sr) for r in music])); f = sum(ex.map(enc, [(r, br, sr) for r in sfx]))
    print(f'音频 {br}kbps/{sr}Hz 单声道: 音乐+标题曲 {len(music)} 首 {m/1e6:.2f} MB, 音效 {len(sfx)} 个 {f/1e6:.2f} MB, 合计 {(m+f)/1e6:.2f} MB')

# 3) 其他
code = sum(os.path.getsize(os.path.join(D, p)) for p in ['data.js', 'index.html', 'main.js']) + sum(os.path.getsize(os.path.join(dp, f)) for sub in ['engine', 'story'] for dp, _, fs in os.walk(os.path.join(D, sub)) for f in fs)
vid = sum(os.path.getsize(os.path.join(D, 'assets/video', f)) for f in ['s00a.mp4', 's00b.mp4'])
print(f'代码+data.js {code/1e6:.2f} MB（zip 里文本约能压到 25%），仅 mp4 开场视频 {vid/1e6:.2f} MB')
