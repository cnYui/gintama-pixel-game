"""给每个场景导出一张“分镜图”（每 0.5 秒一帧的联系表，带时间标签）。

输出：分镜图\\sNN_*.png（原始像素 384×216 一帧，6 列）。画面是引擎真的渲染出来的（含字幕和淡入淡出）。
用法：python export_contact_sheets.py            # 全部场景
      python export_contact_sheets.py s07 s09   # 只做指定场景
"""
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "源码")
sys.dont_write_bytecode = True
sys.path.insert(0, SRC)
os.chdir(SRC)

from PIL import Image  # noqa: E402

from engine.core import W, H  # noqa: E402
from engine.render import load_scenes, render_frame  # noqa: E402
from engine.text import draw_text  # noqa: E402

STEP = 0.5
COLS = 6
GAP = 4
LABEL = 16
TOP = 24


def main():
    ids = sys.argv[1:] or None
    out = os.path.join(HERE, "分镜图")
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    for sc in load_scenes(ids):
        n = int(sc.duration / STEP) + 1
        ts = [min(i * STEP, sc.duration - 0.02) for i in range(n)]
        rows = math.ceil(n / COLS)
        sheet = Image.new("RGB", (COLS * (W + GAP) + GAP, TOP + rows * (H + LABEL + GAP)), (24, 24, 30))
        draw_text(sheet, 6, 6, f"{sc.id} {sc.title}   {sc.duration:g}s   每格 0.5s（场景内时间）", (255, 255, 255), outline=(0, 0, 0))
        for i, t in enumerate(ts):
            img = render_frame(sc, t)
            x = GAP + (i % COLS) * (W + GAP)
            y = TOP + (i // COLS) * (H + LABEL + GAP)
            sheet.paste(img, (x, y))
            draw_text(sheet, x + 2, y + H + 2, f"{t:.1f}s", (255, 240, 160))
        mod = type(sc).__module__.split(".")[-1]
        path = os.path.join(out, f"{mod}.png")
        sheet.save(path)
        print(f"{sc.id} {sc.title}: {n} 帧 → {os.path.basename(path)} ({sheet.width}x{sheet.height})  {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
