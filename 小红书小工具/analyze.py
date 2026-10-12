"""统计游戏运行时真正引用的素材（data.js 里出现的文件），看体积和格式。只读，不改任何东西。"""
import json, re, os, sys
from collections import Counter

GAME = r'D:\CodeWorkSpace\gintama-pixel-game\游戏'
os.chdir(GAME)

s = open('data.js', encoding='utf-8').read()
d = json.loads(s[len('window.GAME_DATA = '):].strip().rstrip(';'))
print('顶层键:', list(d.keys()))
a = d.get('audio', {})
print('music:', {k: v for k, v in a.get('music', {}).items()})
print('sfx 数量:', len(a.get('sfx', {})))
print('video:', d.get('video'))

refs = set()
def walk(o):
    if isinstance(o, str):
        if re.search(r'\.(png|mp3|mp4|webm|json|woff2?)$', o, re.I) and not o.startswith(('http', 'data:')):
            refs.add(o)
    elif isinstance(o, list):
        for v in o: walk(v)
    elif isinstance(o, dict):
        for v in o.values(): walk(v)
walk(d)

by_ext = Counter(); size_ext = Counter(); missing = []
for r in refs:
    e = os.path.splitext(r)[1].lower()
    by_ext[e] += 1
    if os.path.exists(r): size_ext[e] += os.path.getsize(r)
    else: missing.append(r)
print('引用文件数:', len(refs), dict(by_ext))
print('各格式体积 MB:', {k: round(v / 1e6, 2) for k, v in size_ext.items()}, ' 合计', round(sum(size_ext.values()) / 1e6, 2))
print('缺失:', missing[:10], len(missing))

# png 调色板统计：≤256 色的可以无损转成 8 位调色板 PNG
from PIL import Image
pal_ok = 0; total = 0; big = 0; sizes = []
for r in sorted(refs):
    if not r.lower().endswith('.png') or not os.path.exists(r): continue
    total += 1
    im = Image.open(r).convert('RGBA')
    n = len(set(im.getdata())) if im.width * im.height <= 4_000_000 else 99999
    if n <= 256: pal_ok += 1
    sizes.append((os.path.getsize(r), r, n))
print(f'png {total} 张，其中 ≤256 色（可无损转调色板）{pal_ok} 张')
sizes.sort(reverse=True)
print('最大 5 张:', [(round(x / 1024), p, n) for x, p, n in sizes[:5]])

# 各目录里 json 是啥
for r in sorted(refs):
    if r.lower().endswith('.json'):
        print('json:', r, os.path.getsize(r))
