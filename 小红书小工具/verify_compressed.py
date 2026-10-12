"""核对 dist-compressed 相对原 assets：PNG 是否像素级一致、引用是否齐全、代码文件是否有改动。只读。"""
import json, os, re, subprocess, sys, hashlib
from PIL import Image, ImageChops

G = r'D:\CodeWorkSpace\gintama-pixel-game\游戏'
D = os.path.join(G, 'dist-compressed')

# 1. data.js 引用是否都在 dist 里
s = open(os.path.join(D, 'data.js'), encoding='utf-8').read()
d = json.loads(s[len('window.GAME_DATA = '):].strip().rstrip(';'))
refs = set()
def walk(o):
    if isinstance(o, str):
        if re.search(r'\.(png|mp3|mp4|webm|json|woff2?)$', o, re.I) and not o.startswith(('http', 'data:')): refs.add(o)
    elif isinstance(o, list): [walk(v) for v in o]
    elif isinstance(o, dict): [walk(v) for v in o.values()]
walk(d)
missing = [r for r in refs if not os.path.exists(os.path.join(D, r))]
print(f'引用 {len(refs)} 个，dist 里缺 {len(missing)} 个', missing[:5])

# 2. 代码文件是否与原版一致（逐字节）
def sha(p): return hashlib.sha1(open(p, 'rb').read()).hexdigest()
diff = []
for root, _, files in os.walk(D):
    for f in files:
        if f.endswith(('.js', '.html')):
            p = os.path.join(root, f); rel = os.path.relpath(p, D)
            o = os.path.join(G, rel)
            if not os.path.exists(o): diff.append((rel, '原版没有'))
            elif sha(p) != sha(o): diff.append((rel, '内容不同'))
print('代码文件与原版不同:', diff if diff else '无（代码一个字没改）')

# 3. PNG 像素级对比（RGBA 全部相等才算无损）
bad = []; n = 0; shrink_o = shrink_d = 0
for r in sorted(refs):
    if not r.lower().endswith('.png'): continue
    po, pd = os.path.join(G, r), os.path.join(D, r)
    if not os.path.exists(pd) or not os.path.exists(po): continue
    n += 1
    shrink_o += os.path.getsize(po); shrink_d += os.path.getsize(pd)
    a = Image.open(po).convert('RGBA'); b = Image.open(pd).convert('RGBA')
    if a.size != b.size: bad.append((r, 'size')); continue
    # 全透明像素的 RGB 不同不影响显示，先把 alpha=0 的像素归零再比
    ab = ImageChops.difference(a, b)
    px_a = a.load(); px_b = b.load(); ok = True; maxd = 0
    w, h = a.size
    for y in range(h):
        for x in range(w):
            pa = px_a[x, y]; pb = px_b[x, y]
            if pa == pb: continue
            if pa[3] == 0 and pb[3] == 0: continue
            dd = max(abs(pa[i] - pb[i]) for i in range(4)); maxd = max(maxd, dd); ok = False
    if not ok: bad.append((r, f'maxdiff={maxd}'))
print(f'PNG 对比 {n} 张: 体积 {shrink_o/1e6:.2f} → {shrink_d/1e6:.2f} MB，有差异 {len(bad)} 张', bad[:10])

# 4. 音视频：时长对比
def dur(p):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_name,channels,sample_rate,width,height',
                          '-of', 'json', p], capture_output=True, text=True).stdout
    j = json.loads(out); return float(j['format']['duration']), j['streams']
maxdelta = 0; worst = None
for r in sorted(refs):
    if r.endswith('.mp3'):
        a, _ = dur(os.path.join(G, r)); b, st = dur(os.path.join(D, r))
        if abs(a - b) > maxdelta: maxdelta, worst = abs(a - b), (r, a, b)
print('mp3 时长最大偏差(秒):', round(maxdelta, 3), worst)
for r in ['assets/video/s00a.mp4', 'assets/video/s00a.webm', 'assets/video/s00b.mp4', 'assets/video/s00b.webm', 'assets/audio/user/title_song.mp3']:
    a, _ = dur(os.path.join(G, r)); b, st = dur(os.path.join(D, r))
    print(r, f'{a:.2f}s → {b:.2f}s', [(x.get('codec_name'), x.get('width'), x.get('height'), x.get('channels')) for x in st])
