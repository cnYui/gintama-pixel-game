"""1) 量化 dist-compressed 里 PNG 的失真程度；2) 试试真正无损（精确调色板 / optimize）能压到多少；3) 导出最差一张的对比图。只读原文件，临时输出放 _tmp。"""
import os, io, json, re, sys
from PIL import Image
import numpy as np

G = r'D:\CodeWorkSpace\gintama-pixel-game\游戏'
D = os.path.join(G, 'dist-compressed')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_tmp'); os.makedirs(OUT, exist_ok=True)

pngs = []
for root, _, fs in os.walk(os.path.join(D, 'assets')):
    for f in fs:
        if f.endswith('.png'): pngs.append(os.path.relpath(os.path.join(root, f), D))

stats = []; lossless_total = 0; orig_total = 0; dist_total = 0; lossy_n = 0
for r in pngs:
    po, pd = os.path.join(G, r), os.path.join(D, r)
    a = np.asarray(Image.open(po).convert('RGBA')).astype(int)
    b = np.asarray(Image.open(pd).convert('RGBA')).astype(int)
    vis = (a[..., 3] > 0) | (b[..., 3] > 0)
    diff = np.abs(a - b).max(axis=2) * vis
    n_vis = int(vis.sum()) or 1
    stats.append((r, int(diff.max()), float((diff > 0).sum()) / n_vis, float(diff.sum()) / n_vis))
    if diff.max() > 0: lossy_n += 1
    orig_total += os.path.getsize(po); dist_total += os.path.getsize(pd)
    # 无损重压：原图若 ≤256 色，存成精确调色板 PNG（保留 alpha），否则 optimize
    im = Image.open(po).convert('RGBA')
    colors = im.getcolors(maxcolors=256)
    buf = io.BytesIO()
    if colors is not None:
        pal = im.quantize(colors=len(colors), method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE) if len(colors) > 1 else im
        back = pal.convert('RGBA')
        if np.array_equal(np.asarray(back)[..., 3], np.asarray(im)[..., 3]) and np.abs(np.asarray(back).astype(int) - np.asarray(im).astype(int)).max() == 0:
            pal.save(buf, 'PNG', optimize=True)
        else:
            im.save(buf, 'PNG', optimize=True)
    else:
        im.save(buf, 'PNG', optimize=True)
    lossless_total += min(buf.tell(), os.path.getsize(po))

print(f'共 {len(pngs)} 张，有失真 {lossy_n} 张')
print(f'体积：原图 {orig_total/1e6:.2f} MB → 现在的压缩版 {dist_total/1e6:.2f} MB → 真无损重压（估计）{lossless_total/1e6:.2f} MB')
stats.sort(key=lambda x: -x[3])
print('平均失真最大的 8 张 (文件, 最大通道差, 受影响像素占比, 平均差):')
for s in stats[:8]: print('  ', s[0], s[1], f'{s[2]*100:.1f}%', f'{s[3]:.2f}')
allm = [s[3] for s in stats if s[1] > 0]
print('失真图片的平均差中位数:', round(float(np.median(allm)), 3) if allm else 0)

# 对比图：最差一张，放大 3 倍，左原图 右压缩版
r = stats[0][0]
a = Image.open(os.path.join(G, r)).convert('RGBA'); b = Image.open(os.path.join(D, r)).convert('RGBA')
def flat(im):
    bg = Image.new('RGBA', im.size, (60, 60, 70, 255)); bg.alpha_composite(im); return bg.convert('RGB')
s = 3
a2 = flat(a).resize((a.width * s, a.height * s), Image.NEAREST); b2 = flat(b).resize((b.width * s, b.height * s), Image.NEAREST)
canvas = Image.new('RGB', (a2.width * 2 + 10, a2.height), (255, 0, 255)); canvas.paste(a2, (0, 0)); canvas.paste(b2, (a2.width + 10, 0))
if canvas.width > 1800: canvas = canvas.resize((1800, int(canvas.height * 1800 / canvas.width)), Image.NEAREST)
canvas.save(os.path.join(OUT, 'worst_compare.png'))
print('对比图:', r, a.size, '->', os.path.join(OUT, 'worst_compare.png'))
