"""Private art helpers for s04 真选组 (owned by the s04 scene agent).

Static layers are built once (module-level caches); per-frame helpers are pure
functions of their arguments.
"""
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

from engine.core import W, H, rng, clamp, step_frame, lerp, ease_out
from engine.gfx import INK, shade, outline, paste, rect, pset, stamp_line, overlay_rect
from engine.text import text_sprite, draw_text
from bg import common as C

# ------------------------------------------------------------------ palette
TILE = (84, 92, 116)
TILE_HI = (124, 134, 158)
TILE_DK = (58, 64, 86)
TILE_DK2 = (40, 44, 62)
WOOD = (112, 74, 50)
WOOD_HI = (150, 104, 70)
WOOD_DK = (74, 48, 34)
PLASTER = (238, 232, 216)
PLASTER_SH = (210, 202, 184)
STONE = (150, 148, 142)
STONE_HI = (180, 178, 170)
STONE_DK = (106, 102, 100)
MORTAR = (82, 78, 78)
PINE = (46, 98, 62)
PINE_HI = (78, 136, 80)
PINE_DK = (30, 66, 48)
FLAG_RED = (206, 44, 52)
FLAG_WHITE = (250, 246, 236)
MAYO = (255, 244, 196)
MAYO_S = (228, 204, 140)
MAYO_HI = (255, 255, 236)
CAP_RED = (228, 52, 60)
CAP_RED_D = (170, 30, 44)
SKIN = (255, 218, 186)
SKIN_S = (232, 170, 140)
UNI = (50, 48, 72)
UNI_HI = (90, 88, 122)
GOLD = (248, 204, 80)
CHAR_BLACK = (34, 28, 34)
CHAR_GREY = (70, 62, 66)


def _rgba(c, a=255):
    return tuple(c[:3]) + (a,)


def _vtext(img, x, y, text, color, step=12, size=12):
    """Vertical pixel text, top-left of the first glyph at (x, y)."""
    for i, ch in enumerate(text):
        draw_text(img, x, y + i * step, ch, color, size=size)


# ======================================================================== flag
@lru_cache(maxsize=8)
def flag_base(w, h, size, face="hei"):
    """Shinsengumi banner: red field, white brush 诚, white dandara teeth at the bottom."""
    img = Image.new("RGBA", (w, h), _rgba(FLAG_RED))
    d = ImageDraw.Draw(img)
    band = max(4, h // 6)
    y0 = h - band
    tooth = band + 1
    x = 0
    while x < w + tooth:
        d.polygon([(x, h), (x + tooth / 2.0, y0), (x + tooth, h)], fill=_rgba(FLAG_WHITE))
        x += tooth
    d.line([(0, y0 - 2), (w, y0 - 2)], fill=_rgba(FLAG_WHITE))
    spr = text_sprite("诚", FLAG_WHITE, size, face)
    img.alpha_composite(spr, (w // 2 - spr.width // 2, (y0 - 2) // 2 - spr.height // 2 + 1))
    return img


def flag_wave(w, h, size, t, amp=2.0, speed=6.5, k=0.26, face="hei"):
    """Waving flag sprite (pole on the left). Steps at 12 fps. Returns RGBA with
    a 1px ink outline; the pole attaches at local (1, A+1)."""
    base = np.asarray(flag_base(w, h, size, face))
    tq = step_frame(t, 12) / 12.0
    A = int(math.ceil(amp)) + 1
    out = np.zeros((h + 2 * A, w, 4), np.uint8)
    for x in range(w):
        f = (x / max(1, w - 1)) ** 0.8
        ph = x * k - tq * speed
        dy = int(round(amp * f * math.sin(ph)))
        col = base[:, x].copy()
        sl = math.cos(ph) * f
        if sl > 0.5:
            col[:, :3] = np.minimum(255, col[:, :3].astype(np.int32) * 118 // 100)
        elif sl < -0.5:
            col[:, :3] = col[:, :3].astype(np.int32) * 78 // 100
        out[A + dy:A + dy + h, x] = col
    return outline(Image.fromarray(out, "RGBA")), A


def draw_flag(img, px, py, t, w=44, h=30, size=20, amp=2.0, pole_h=None, pole_col=(184, 172, 150),
              face="hei", speed=6.5, k=0.26):
    """Flag attached to a pole whose top is at (px, py)."""
    if pole_h:
        rect(img, px - 1, py - 2, 4, pole_h + 2, INK)
        rect(img, px, py - 1, 2, pole_h, pole_col)
        rect(img, px, py - 1, 1, pole_h, shade(pole_col, 1.15))
        rect(img, px - 1, py - 5, 4, 4, INK)
        rect(img, px, py - 4, 2, 2, GOLD)
    spr, A = flag_wave(w, h, size, t, amp, speed, k, face)
    paste(img, spr, px + 2, py - A)


# ======================================================================== gate
def _tile_roof(d, pts, y_top, y_bot, step_x=4, rows=(0.18, 0.38, 0.6, 0.84)):
    """Kawara roof polygon: fill + tile channels + course lines (drawn in place)."""
    x0 = min(p[0] for p in pts)
    x1 = max(p[0] for p in pts)
    m = Image.new("L", (W + 40, H + 40), 0)
    ImageDraw.Draw(m).polygon([(p[0] + 20, p[1] + 20) for p in pts], fill=255)
    lay = Image.new("RGBA", (W + 40, H + 40), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.polygon([(p[0] + 20, p[1] + 20) for p in pts], fill=_rgba(TILE))
    for x in range(int(x0), int(x1) + 1, step_x):
        dl.line([(x + 20, y_top + 20), (x + 20, y_bot + 20)], fill=_rgba(TILE_DK))
        dl.line([(x + 21, y_top + 20), (x + 21, y_bot + 20)], fill=_rgba(TILE_HI))
    for fr in rows:
        y = int(y_top + (y_bot - y_top) * fr)
        dl.line([(x0 + 20, y + 20), (x1 + 20, y + 20)], fill=_rgba(TILE_DK2))
    a = np.asarray(lay).copy()
    a[..., 3] = np.minimum(a[..., 3], np.asarray(m))
    return Image.fromarray(a, "RGBA").crop((20, 20, W + 20, H + 20))


def _outline_poly(d, pts):
    d.polygon(pts, outline=_rgba(INK))


@lru_cache(maxsize=2)
def gate_layer():
    """HQ gate + compound wall + main building roof + pine + flagpole (no flag).
    Screen coords at the final framing, ground (feet) line 160. Day colours,
    graded with the shared 'day' grade."""
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    r = rng("s04gate")
    # ---- main HQ building behind the wall
    d.rectangle([18, 92, 366, 118], fill=_rgba(PLASTER_SH))
    for x in range(24, 366, 26):
        d.rectangle([x, 92, x + 2, 118], fill=_rgba(WOOD_DK))
        if 150 < x < 238:
            continue
        d.rectangle([x + 7, 100, x + 19, 112], fill=_rgba((226, 218, 196)))
        for xx in range(x + 7, x + 20, 4):
            d.line([(xx, 100), (xx, 112)], fill=_rgba(WOOD))
        d.line([(x + 7, 106), (x + 19, 106)], fill=_rgba(WOOD))
    d.rectangle([18, 96, 366, 97], fill=_rgba(WOOD_DK))
    roof = [(4, 94), (58, 58), (326, 58), (380, 94)]
    L.alpha_composite(_tile_roof(d, roof, 58, 94, 5))
    d = ImageDraw.Draw(L)
    _outline_poly(d, roof)
    d.rectangle([4, 93, 380, 96], fill=_rgba(TILE_DK2))
    for x in range(6, 380, 6):
        d.point((x, 94), fill=_rgba(TILE_HI))
    d.rectangle([54, 51, 330, 58], fill=_rgba(TILE_DK2), outline=_rgba(INK))
    d.line([(55, 52), (329, 52)], fill=_rgba(TILE_HI))
    for ox in (50, 326):
        d.rectangle([ox, 45, ox + 8, 58], fill=_rgba(TILE_DK), outline=_rgba(INK))
        d.rectangle([ox + 2, 47, ox + 6, 50], fill=_rgba(TILE_HI))
    # ---- pine tree (left, behind the wall)
    trunk = [(30, 118), (36, 96), (44, 76), (48, 58), (52, 58), (49, 78), (42, 98), (38, 118)]
    d.polygon(trunk, fill=_rgba((96, 66, 50)), outline=_rgba(INK))
    for (cx, cy, rx, ry) in ((18, 70, 16, 6), (58, 52, 20, 7), (36, 42, 16, 6), (70, 70, 14, 5),
                             (28, 88, 14, 5), (52, 34, 10, 4)):
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=_rgba(PINE), outline=_rgba(INK))
        d.ellipse([cx - rx + 3, cy - ry + 1, cx + rx - 5, cy], fill=_rgba(PINE_HI))
        for i in range(6):
            xx = cx - rx + 4 + r.randint(0, 2 * rx - 8)
            d.point((xx, cy + r.randint(1, max(1, ry - 2))), fill=_rgba(PINE_DK))
    # ---- flagpole (behind the wall, flag drawn per frame)
    d.rectangle([317, 8, 320, 110], fill=_rgba(INK))
    d.rectangle([318, 9, 319, 110], fill=_rgba((184, 172, 150)))
    d.rectangle([316, 4, 321, 8], fill=_rgba(INK))
    d.rectangle([317, 5, 320, 7], fill=_rgba(GOLD))
    # ---- courtyard seen through the gate
    d.rectangle([146, 92, 238, 160], fill=_rgba((70, 50, 40)))
    for x in range(150, 236, 14):
        d.rectangle([x, 104, x + 11, 128], fill=_rgba((228, 220, 196)))
        d.line([(x + 5, 104), (x + 5, 128)], fill=_rgba(WOOD))
        d.line([(x, 112), (x + 11, 112)], fill=_rgba(WOOD))
        d.line([(x, 120), (x + 11, 120)], fill=_rgba(WOOD))
    d.rectangle([146, 128, 238, 132], fill=_rgba(WOOD_HI))
    d.rectangle([146, 133, 238, 136], fill=_rgba((40, 30, 28)))
    d.rectangle([146, 137, 238, 160], fill=_rgba((214, 202, 172)))
    for i in range(70):
        x, y = r.randint(147, 237), r.randint(138, 159)
        d.point((x, y), fill=_rgba((184, 170, 140) if i % 2 else (236, 226, 200)))
    for (sx, sy) in ((186, 150), (196, 144), (190, 139)):
        d.ellipse([sx - 5, sy - 2, sx + 5, sy + 2], fill=_rgba(STONE_HI), outline=_rgba(STONE_DK))
    # open door leaves (swung inward)
    for (xa, xb) in ((146, 162), (238, 222)):
        pts = [(xa, 96), (xb, 102), (xb, 156), (xa, 160)]
        d.polygon(pts, fill=_rgba(WOOD_DK), outline=_rgba(INK))
        for k in range(1, 4):
            xx = xa + (xb - xa) * k / 4
            d.line([(xx, 97 + 6 * k / 4), (xx, 159 - 4 * k / 4)], fill=_rgba((58, 38, 28)))
        for yy in (110, 130, 148):
            for k in range(1, 4):
                xx = xa + (xb - xa) * (k - 0.5) / 4
                d.point((xx, yy), fill=_rgba(GOLD))
    # ---- compound wall (tsuijibei)
    for (x0, x1) in ((-4, 132), (252, 388)):
        cap = [(x0 - 2, 117), (x0 + 3, 108), (x1 - 3, 108), (x1 + 2, 117)]
        d.rectangle([x0, 117, x1, 146], fill=_rgba(PLASTER))
        d.rectangle([x0, 117, x1, 120], fill=_rgba(PLASTER_SH))
        for i in range(40):
            xx, yy = r.randint(x0 + 1, x1 - 1), r.randint(122, 145)
            d.point((xx, yy), fill=_rgba((224, 216, 198)))
        # ishigaki stone base
        d.rectangle([x0, 146, x1, 160], fill=_rgba(MORTAR))
        for row, y in enumerate((147, 154)):
            off = (row % 2) * 7
            for x in range(x0 - 14 + off, x1, 14):
                a0, a1 = max(x0, x + 1), min(x1, x + 12)
                if a1 <= a0:
                    continue
                d.rectangle([a0, y, a1, y + 5], fill=_rgba(STONE))
                d.line([(a0, y), (a1, y)], fill=_rgba(STONE_HI))
                d.line([(a1, y + 1), (a1, y + 5)], fill=_rgba(STONE_DK))
        L.alpha_composite(_tile_roof(d, cap, 108, 117, 4, rows=(0.5,)))
        d = ImageDraw.Draw(L)
        _outline_poly(d, cap)
        d.rectangle([x0 + 1, 105, x1 - 1, 108], fill=_rgba(TILE_DK2), outline=_rgba(INK))
        d.line([(x0 + 2, 106), (x1 - 2, 106)], fill=_rgba(TILE_HI))
        d.line([(x0 - 1, 117), (x1 + 1, 117)], fill=_rgba(TILE_DK2))
        d.line([(x0, 146), (x1, 146)], fill=_rgba(INK))
    # ---- gate: pillars, beams, roof
    for px in (136, 238):
        d.rectangle([px, 86, px + 9, 160], fill=_rgba(WOOD), outline=_rgba(INK))
        d.line([(px + 1, 87), (px + 1, 159)], fill=_rgba(WOOD_HI))
        d.line([(px + 8, 87), (px + 8, 159)], fill=_rgba(WOOD_DK))
        d.rectangle([px - 1, 154, px + 10, 160], fill=_rgba(STONE), outline=_rgba(INK))
    d.rectangle([128, 99, 256, 104], fill=_rgba(WOOD), outline=_rgba(INK))
    d.line([(129, 100), (255, 100)], fill=_rgba(WOOD_HI))
    d.rectangle([122, 84, 262, 90], fill=_rgba(WOOD_DK), outline=_rgba(INK))
    d.line([(123, 85), (261, 85)], fill=_rgba(WOOD))
    for x in range(128, 258, 9):
        d.rectangle([x, 80, x + 4, 84], fill=_rgba(WOOD_DK), outline=_rgba(INK))
    groof = [(104, 82), (112, 80), (134, 56), (250, 56), (272, 80), (280, 82)]
    L.alpha_composite(_tile_roof(d, groof, 56, 82, 4))
    d = ImageDraw.Draw(L)
    _outline_poly(d, groof)
    d.rectangle([106, 80, 278, 83], fill=_rgba(TILE_DK2))
    for x in range(108, 278, 5):
        d.point((x, 81), fill=_rgba(TILE_HI))
    d.rectangle([130, 49, 254, 56], fill=_rgba(TILE_DK2), outline=_rgba(INK))
    d.line([(131, 50), (253, 50)], fill=_rgba(TILE_HI))
    for ox in (125, 251):
        d.rectangle([ox, 43, ox + 9, 56], fill=_rgba(TILE_DK), outline=_rgba(INK))
        d.rectangle([ox + 2, 45, ox + 7, 48], fill=_rgba(TILE_HI))
    # gold crest on the gable
    d.ellipse([186, 60, 198, 72], fill=_rgba(GOLD), outline=_rgba(INK))
    d.ellipse([189, 63, 195, 69], fill=_rgba((200, 150, 50)))
    # ---- the signboard 「真选组屯所」 on the right pillar
    bx0, by0, bw, bh = 234, 92, 18, 66
    d.rectangle([bx0 - 1, by0 - 1, bx0 + bw, by0 + bh], fill=_rgba(INK))
    d.rectangle([bx0, by0, bx0 + bw - 1, by0 + bh - 1], fill=_rgba((244, 238, 222)))
    d.line([(bx0 + bw - 2, by0 + 1), (bx0 + bw - 2, by0 + bh - 2)], fill=_rgba((206, 196, 170)))
    d.line([(bx0 + 1, by0 + 1), (bx0 + bw - 3, by0 + 1)], fill=_rgba((255, 252, 244)))
    g = C.grade_rgba(L, "day")
    _vtext(g, bx0 + 3, by0 + 3, "真选组屯所", (22, 18, 26))
    return g


# ======================================================================== street bits
def birds(img, t, seed=0, n=3, y=30, speed=26.0, span=(0, W)):
    d = ImageDraw.Draw(img)
    for i in range(n):
        r = rng("s04bird", seed, i)
        x = (r.uniform(0, W + 60) + t * speed * r.uniform(0.8, 1.2)) % (W + 60) - 30
        yy = y + r.uniform(-10, 10) + math.sin(t * 2 + i) * 2
        f = step_frame(t + i * 0.2, 6, 2)
        c = (60, 60, 80)
        if f:
            d.line([(x - 2, yy - 1), (x, yy), (x + 2, yy - 1)], fill=c)
        else:
            d.line([(x - 2, yy + 1), (x, yy), (x + 2, yy + 1)], fill=c)


# ======================================================================== canteen
CANTEEN_W = 640
TABLE_X0, TABLE_X1, TABLE_TOP = 96, 214, 150


@lru_cache(maxsize=2)
def canteen_decor():
    """Wall decor in world coords (CANTEEN_W wide), placed in the band y 82..136 that
    the 2x-zoomed canteen shots see: menu tags, kitchen hatch with noren, 局中法度
    scroll, clock. 'day_in' graded."""
    L = Image.new("RGBA", (CANTEEN_W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    txt = []
    # menu rail + tags
    d.rectangle([28, 82, 134, 84], fill=_rgba(WOOD_DK), outline=_rgba(INK))
    tags = [("定食", False), ("乌冬", False), ("团子", False), ("荞麦", False), ("蛋黄酱", True)]
    x = 34
    for name, red in tags:
        hgt = len(name) * 12 + 6
        bg = (206, 48, 56) if red else (232, 206, 160)
        d.rectangle([x - 1, 85, x + 14, 86 + hgt], fill=_rgba(INK))
        d.rectangle([x, 86, x + 13, 85 + hgt], fill=_rgba(bg))
        d.line([(x + 12, 87), (x + 12, 84 + hgt)], fill=_rgba(shade(bg, 0.8)))
        txt.append((x + 1, 89, name, (255, 250, 240) if red else (40, 28, 26)))
        x += 19
    # kitchen hatch
    kx0, kx1 = 256, 344
    d.rectangle([kx0 - 3, 84, kx1 + 3, 132], fill=_rgba(WOOD_DK), outline=_rgba(INK))
    d.rectangle([kx0, 87, kx1, 124], fill=_rgba((62, 46, 44)))
    d.rectangle([kx0 + 10, 112, kx0 + 40, 124], fill=_rgba((90, 80, 84)), outline=_rgba(INK))
    d.ellipse([kx0 + 12, 102, kx0 + 38, 114], fill=_rgba((150, 150, 160)), outline=_rgba(INK))
    d.rectangle([kx0 + 12, 107, kx0 + 38, 113], fill=_rgba((150, 150, 160)))
    d.line([(kx0 + 12, 107), (kx0 + 38, 107)], fill=_rgba((200, 200, 210)))
    d.rectangle([kx0 + 52, 112, kx0 + 80, 124], fill=_rgba((104, 72, 52)), outline=_rgba(INK))
    for i in range(3):
        d.ellipse([kx0 + 54 + i * 8, 107, kx0 + 61 + i * 8, 112], fill=_rgba((240, 240, 236)), outline=_rgba(INK))
    d.rectangle([kx0 - 6, 124, kx1 + 6, 130], fill=_rgba(WOOD_HI), outline=_rgba(INK))
    d.line([(kx0 - 5, 125), (kx1 + 5, 125)], fill=_rgba((190, 140, 96)))
    for i, bx in enumerate(range(kx0 + 4, kx1 - 6, 16)):
        d.pieslice([bx, 117, bx + 10, 129], 180, 360, fill=_rgba((240, 240, 236)), outline=_rgba(INK))
        d.line([(bx + 2, 121), (bx + 8, 121)], fill=_rgba((80, 110, 180)))
    for i, (a, b) in enumerate(((kx0, kx0 + 43), (kx0 + 45, kx1))):
        d.rectangle([a, 87, b, 104], fill=_rgba((44, 62, 112)), outline=_rgba(INK))
        d.line([(a + 1, 88), (b - 1, 88)], fill=_rgba((70, 92, 150)))
    d.rectangle([kx0 - 2, 85, kx1 + 2, 87], fill=_rgba(WOOD_HI), outline=_rgba(INK))
    txt.append((kx0 + 15, 90, "食", (240, 236, 226)))
    txt.append((kx0 + 60, 90, "堂", (240, 236, 226)))
    # 局中法度 hanging scroll
    sx = 452
    d.rectangle([sx - 3, 82, sx + 20, 85], fill=_rgba(WOOD_DK), outline=_rgba(INK))
    d.rectangle([sx - 1, 86, sx + 18, 134], fill=_rgba((236, 226, 200)), outline=_rgba(INK))
    d.rectangle([sx + 1, 87, sx + 16, 133], fill=_rgba((246, 238, 216)))
    d.rectangle([sx - 3, 134, sx + 20, 137], fill=_rgba(WOOD_DK), outline=_rgba(INK))
    txt.append((sx + 3, 88, "局中法度", (40, 28, 26), "v"))
    # wall clock
    d.ellipse([352, 86, 370, 104], fill=_rgba((236, 230, 214)), outline=_rgba(INK))
    d.ellipse([354, 88, 368, 102], outline=_rgba(WOOD_DK))
    d.line([(361, 95), (361, 90)], fill=_rgba(INK))
    d.line([(361, 95), (365, 95)], fill=_rgba(INK))
    g = C.grade_rgba(L, "day_in")
    for item in txt:
        if len(item) == 5:
            _vtext(g, item[0], item[1], item[2], item[3], step=11)
        elif len(item[2]) > 1:
            _vtext(g, item[0], item[1], item[2], item[3])
        else:
            draw_text(g, item[0], item[1], item[2], item[3])
    return g


def steam(img, x, y, t, seed=0, h=18, col=(236, 236, 240)):
    """Rising pot steam wisps (canvas coords)."""
    d = ImageDraw.Draw(img)
    for i in range(6):
        r = rng("s04steam", seed, i)
        ph = ((t * 0.9 + r.random()) % 1.0)
        yy = y - ph * h
        xx = x + r.uniform(-6, 6) + math.sin(t * 3 + i) * 2
        rad = 1 + ph * 2.5
        if ph < 0.85:
            d.ellipse([xx - rad, yy - rad, xx + rad, yy + rad], fill=col)


def sunbeams(img, ox, oy, t):
    """Diagonal light shafts from the shoji onto the floor + floating dust."""
    for i, bx in enumerate((60, 250, 420, 560)):
        x0 = bx - ox
        if x0 < -140 or x0 > W + 40:
            continue
        pts = [(x0, 20 - oy), (x0 + 26, 20 - oy), (x0 + 96, 170 - oy), (x0 + 60, 170 - oy)]
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon(pts, fill=34)
        img.paste((255, 244, 210), (0, 0, W, H), m)
        d = ImageDraw.Draw(img)
        for k in range(7):
            r = rng("s04dust", i, k)
            ph = (t * 0.05 * r.uniform(0.5, 1.5) + r.random()) % 1.0
            yy = 30 + ph * 120
            xx = x0 + 18 + (yy - 20) * 0.47 + r.uniform(-8, 16) + math.sin(t + k) * 3
            if (step_frame(t, 6) + k) % 4:
                d.point((xx, yy - oy), fill=(255, 250, 226))


def table_fg(img, ox, oy, x0=TABLE_X0, x1=TABLE_X1, top=TABLE_TOP):
    """Long canteen table (drawn over the seated character), canvas = world - o."""
    X0, X1, T = x0 - ox, x1 - ox, top - oy
    rect(img, X0 - 1, T - 1, X1 - X0 + 3, 6, INK)
    rect(img, X0, T, X1 - X0 + 1, 2, (196, 146, 98))
    rect(img, X0, T + 2, X1 - X0 + 1, 2, (160, 112, 72))
    rect(img, X0 + 1, T + 5, X1 - X0 - 1, 5, INK)
    rect(img, X0 + 2, T + 5, X1 - X0 - 3, 4, (120, 80, 52))
    for lx in (X0 + 4, X1 - 8):
        rect(img, lx - 1, T + 9, 6, 11, INK)
        rect(img, lx, T + 9, 4, 10, (110, 74, 48))
        rect(img, lx, T + 9, 1, 10, (140, 98, 64))


def tea_cup(img, x, y):
    rect(img, x - 3, y - 6, 7, 7, INK)
    rect(img, x - 2, y - 5, 5, 5, (120, 150, 110))
    rect(img, x - 2, y - 5, 5, 1, (160, 190, 140))


# ======================================================================== mayo
def _pile_tiers(width, height, tier_h):
    n = max(1, int(round(height / tier_h)))
    tiers = []
    for i in range(n):
        f = i / n
        hw = width / 2.0 * (1 - f * 0.86) ** 0.9
        cy = -(i + 0.5) * tier_h
        sx = (1 if i % 2 else -1) * width * 0.03 * (1 - f)
        tiers.append((sx, cy, hw))
    return tiers


def mayo_pile(img, cx, base_y, width, height, tier_h, reveal=1.0, charred=False, t=0.0):
    """Soft-serve style mountain of mayonnaise. reveal 0..1 builds it bottom-up."""
    d = ImageDraw.Draw(img)
    tiers = _pile_tiers(width, height, tier_h)
    n = len(tiers)
    shown = reveal * (n + 1)
    body, sh, hi = (MAYO, MAYO_S, MAYO_HI) if not charred else (CHAR_GREY, CHAR_BLACK, (104, 96, 100))
    th = max(2.0, tier_h * 0.72)
    boxes = []
    for i, (sx, cy, hw) in enumerate(tiers):
        k = clamp(shown - i)
        if k <= 0:
            break
        hw2 = hw * (0.35 + 0.65 * k)
        x0, x1 = cx + sx - hw2, cx + sx + hw2
        y0, y1 = base_y + cy - th, base_y + cy + th * 0.9
        boxes.append((i, x0, y0, x1, y1, hw2))
    tip_pts = None
    if shown >= n + 0.5:
        sx, cy, hw = tiers[-1]
        tx, ty = cx + sx, base_y + cy - th * 0.9
        tip = max(2, tier_h * 0.8)
        tip_pts = [(tx - tip * 0.6, ty + 1), (tx + tip * 0.2, ty - tip * 1.3), (tx + tip * 0.9, ty - tip * 1.1),
                   (tx + tip * 0.3, ty - tip * 0.6), (tx + tip * 0.6, ty + 1)]
    # pass 1: one ink silhouette around the whole pile
    for (i, x0, y0, x1, y1, hw2) in boxes:
        d.ellipse([x0 - 1, y0 - 1, x1 + 1, y1 + 1], fill=INK)
    if tip_pts:
        d.polygon(tip_pts, fill=INK, outline=INK)
        d.polygon([(x + 1, y) for (x, y) in tip_pts], fill=INK)
        d.polygon([(x - 1, y) for (x, y) in tip_pts], fill=INK)
        d.polygon([(x, y - 1) for (x, y) in tip_pts], fill=INK)
    # pass 2: ridged rope, each tier casting a shade groove on the one below
    for (i, x0, y0, x1, y1, hw2) in boxes:
        d.ellipse([x0, y0, x1, y1], fill=sh)
        d.ellipse([x0, y0, x1 - max(1, hw2 * 0.22), y1 - max(1, th * 0.45)], fill=body)
        if hw2 > 3:
            d.arc([x0 + 1, y0 + 1, x1 - 2, y1 - 1], 195, 255, fill=hi)
        if hw2 > 5:  # twist groove
            gx = cx + hw2 * (0.45 if i % 2 else -0.2) + (x0 + x1) / 2 - cx
            d.line([(gx, y0 + th * 0.5), (gx + (2 if i % 2 else -2) * max(1, th / 4), y1 - th * 0.2)], fill=sh)
    if tip_pts:
        d.polygon(tip_pts, fill=body)
        d.line([tip_pts[1], tip_pts[2]], fill=hi)
    if charred:
        for i in range(3):
            ph = ((t * 0.8 + i * 0.33) % 1.0)
            px = cx - width * 0.2 + i * width * 0.2 + math.sin(t * 4 + i) * 1.5
            py = base_y - height - 2 - ph * height * 0.6
            rr = 1 + ph * max(1.5, width * 0.12)
            if ph < 0.85:
                d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=(150, 146, 156))
    tiers_top = base_y + tiers[min(n - 1, max(0, int(shown) - 1))][1] - th if shown > 0 else base_y
    return tiers_top


def small_bowl(img, cx, base_y, w=16, charred=False):
    """Chibi-scale donburi (bottom at base_y). Returns rim y."""
    d = ImageDraw.Draw(img)
    hw = w // 2
    rim = base_y - 6
    body = (236, 236, 232) if not charred else (90, 84, 88)
    band = (70, 100, 176) if not charred else (50, 50, 60)
    d.pieslice([cx - hw - 1, rim - 7, cx + hw + 1, base_y + 1], 0, 180, fill=INK)
    d.pieslice([cx - hw, rim - 6, cx + hw, base_y], 0, 180, fill=body)
    d.line([(cx - hw + 1, rim + 1), (cx + hw - 1, rim + 1)], fill=band)
    rect(img, cx - 3, base_y - 1, 7, 2, INK)
    rect(img, cx - hw - 1, rim - 1, w + 3, 2, INK)
    rect(img, cx - hw, rim - 1, w + 1, 1, (255, 255, 255) if not charred else (120, 110, 116))
    return rim


# ---------------------------------------------------------------- the insert shot
def sunburst(img, cx, cy, t, c1=(236, 104, 92), c2=(248, 146, 108), n=18, speed=0.15):
    """Food-show radial rays (fills the whole canvas)."""
    img.paste(c2, (0, 0, W, H))
    d = ImageDraw.Draw(img)
    R = 600
    rot = t * speed
    for i in range(n):
        a0 = rot + i * 2 * math.pi / n
        a1 = a0 + math.pi / n
        d.polygon([(cx, cy), (cx + math.cos(a0) * R, cy + math.sin(a0) * R),
                   (cx + math.cos(a1) * R, cy + math.sin(a1) * R)], fill=c1)


def big_bowl(img, cx, rim_y, hw=58):
    """Close-up donburi (porcelain w/ blue pattern) + rice dome. Returns rim y."""
    d = ImageDraw.Draw(img)
    depth = 44
    # body (lower half ellipse) + foot
    d.rectangle([cx - 26, rim_y + depth - 4, cx + 26, rim_y + depth + 6], fill=INK)
    d.rectangle([cx - 25, rim_y + depth - 4, cx + 25, rim_y + depth + 5], fill=(214, 214, 214))
    d.pieslice([cx - hw - 1, rim_y - depth - 1, cx + hw + 1, rim_y + depth + 1], 0, 180, fill=INK)
    d.pieslice([cx - hw, rim_y - depth, cx + hw, rim_y + depth], 0, 180, fill=(244, 244, 240))
    d.pieslice([cx - hw + 10, rim_y - depth, cx + hw, rim_y + depth], 10, 90, fill=(222, 222, 222))
    # blue band + wave pattern
    for yy in (rim_y + 6, rim_y + 7):
        xx = math.sqrt(max(0, 1 - ((yy - rim_y) / depth) ** 2)) * hw
        d.line([(cx - xx + 1, yy), (cx + xx - 1, yy)], fill=(60, 90, 170))
    for k in range(-4, 5):
        x = cx + k * 11
        y = rim_y + 18 + abs(k) * 0.5
        d.arc([x - 5, y - 4, x + 5, y + 4], 180, 360, fill=(80, 110, 190))
        d.arc([x - 3, y - 1, x + 3, y + 4], 180, 360, fill=(80, 110, 190))
    yy = rim_y + 32
    xx = math.sqrt(max(0, 1 - ((yy - rim_y) / depth) ** 2)) * hw
    d.line([(cx - xx + 2, yy), (cx + xx - 2, yy)], fill=(60, 90, 170))
    # rim + rice dome
    d.ellipse([cx - hw - 1, rim_y - 9, cx + hw + 1, rim_y + 9], fill=INK)
    d.ellipse([cx - hw, rim_y - 8, cx + hw, rim_y + 8], fill=(250, 250, 248))
    d.ellipse([cx - hw + 4, rim_y - 6, cx + hw - 4, rim_y + 6], fill=(236, 232, 222))
    d.ellipse([cx - hw + 6, rim_y - 12, cx + hw - 6, rim_y + 4], fill=(255, 255, 252), outline=INK)
    r = rng("s04rice")
    for i in range(60):
        x = cx + r.uniform(-hw + 12, hw - 12)
        y = rim_y + r.uniform(-9, 2)
        d.point((x, y), fill=(222, 220, 210) if i % 2 else (255, 255, 255))
    return rim_y


def big_bottle(img, cx, nozzle_y, t, squeeze=True):
    """Huge upside-down mayo squeeze bottle held by Hijikata's hand, from the top."""
    d = ImageDraw.Draw(img)
    pinch = 3 if (squeeze and step_frame(t, 6, 2)) else 0
    tip_y = nozzle_y
    cap_y1 = tip_y - 9
    cap_y0 = cap_y1 - 12
    body_y1 = cap_y0
    body_y0 = body_y1 - 58
    hw = 20
    # body (rounded)
    pts = []
    for yy in range(int(body_y0), int(body_y1) + 1, 2):
        f = (yy - body_y0) / (body_y1 - body_y0)
        wv = hw - pinch * math.sin(f * math.pi) - (6 * (f - 0.85) / 0.15 if f > 0.85 else 0)
        pts.append((cx - wv, yy))
    pts2 = [(2 * cx - x, y) for (x, y) in reversed(pts)]
    poly = pts + pts2
    # body drawn on its own layer so the red net label can be clipped to it
    lay = Image.new("RGB", (W, H), MAYO)
    dl = ImageDraw.Draw(lay)
    dl.line([(cx - hw + 4, body_y0 + 2), (cx - hw + 4 + pinch, body_y1 - 14)], fill=MAYO_HI, width=2)
    dl.line([(cx + hw - 4, body_y0 + 2), (cx + hw - 4 - pinch, body_y1 - 12)], fill=MAYO_S, width=3)
    ly0, ly1 = body_y0 + 20, body_y0 + 44
    for k in range(-4, 7):
        x = cx - hw + k * 8
        dl.line([(x, ly0), (x + 28, ly1)], fill=CAP_RED)
        dl.line([(x + 28, ly0), (x, ly1)], fill=CAP_RED)
    dl.line([(cx - hw, ly0), (cx + hw, ly0)], fill=CAP_RED_D)
    dl.line([(cx - hw, ly1), (cx + hw, ly1)], fill=CAP_RED_D)
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    img.paste(lay, (0, 0), m)
    d.polygon(poly, outline=INK)
    # cap + nozzle
    d.rectangle([cx - 11, cap_y0, cx + 11, cap_y1], fill=CAP_RED, outline=INK)
    for x in range(cx - 8, cx + 9, 4):
        d.line([(x, cap_y0 + 2), (x, cap_y1 - 2)], fill=CAP_RED_D)
    d.line([(cx - 10, cap_y0 + 1), (cx + 10, cap_y0 + 1)], fill=(255, 120, 120))
    d.polygon([(cx - 6, cap_y1), (cx + 6, cap_y1), (cx + 2, tip_y), (cx - 2, tip_y)], fill=CAP_RED, outline=INK)
    d.line([(cx - 1, cap_y1 + 1), (cx - 1, tip_y - 2)], fill=(255, 120, 120))
    # hand gripping from the right + black sleeve with gold trim
    hy = body_y0 + 22 - pinch
    d.polygon([(cx + 8, hy - 16), (W + 20, hy - 70), (W + 20, hy - 20), (cx + 26, hy + 8)], fill=UNI, outline=INK)
    d.line([(cx + 12, hy - 14), (W + 20, hy - 66)], fill=UNI_HI, width=2)
    d.line([(cx + 20, hy + 2), (cx + 30, hy - 22)], fill=GOLD, width=3)
    d.ellipse([cx + 6, hy - 16, cx + 30, hy + 10], fill=SKIN, outline=INK)
    d.arc([cx + 9, hy - 12, cx + 27, hy + 6], 200, 260, fill=(255, 236, 214))
    for k in range(3):                       # fingers wrapping the front of the bottle
        fy = hy - 12 + k * 7 + (pinch if k == 1 else 0)
        d.ellipse([cx - 4 + pinch, fy, cx + 12, fy + 7], fill=SKIN, outline=INK)
        d.line([(cx - 1 + pinch, fy + 5), (cx + 6, fy + 5)], fill=SKIN_S)
    d.ellipse([cx + 14, hy + 4, cx + 26, hy + 12], fill=SKIN, outline=INK)   # thumb
    return tip_y


def mayo_stream(img, x, y0, y1, t, w=4):
    if y1 <= y0:
        return
    d = ImageDraw.Draw(img)
    f = step_frame(t, 12)
    for y in range(int(y0), int(y1) + 1):
        wob = 1 if ((y + f * 3) // 5) % 2 else 0
        d.line([(x - w // 2 - 1 + wob, y), (x + w // 2 + 1 + wob, y)], fill=INK)
        d.line([(x - w // 2 + wob, y), (x + w // 2 + wob, y)], fill=MAYO)
        pset(img, x - w // 2 + wob, y, MAYO_HI)


# ======================================================================== misc fx
def rocket(img, x, y, t, facing=-1):
    """Bazooka shell flying horizontally (canvas coords, nose at x)."""
    s = -facing  # body extends behind the nose
    rect(img, int(min(x, x + s * 12)), int(y - 3), 13, 7, INK)
    rect(img, int(min(x + s * 2, x + s * 11)), int(y - 2), 10, 5, (98, 118, 72))
    rect(img, int(min(x + s * 2, x + s * 11)), int(y - 2), 10, 1, (146, 166, 104))
    rect(img, int(min(x, x + s * 3)), int(y - 2), 3, 5, CAP_RED)
    f = step_frame(t, 15, 2)
    fl = 5 + 2 * f
    tx = x + s * 13
    d = ImageDraw.Draw(img)
    d.polygon([(tx, y - 3), (tx + s * fl, y), (tx, y + 3)], fill=(255, 200, 60))
    d.polygon([(tx, y - 1), (tx + s * (fl - 2), y), (tx, y + 1)], fill=(255, 255, 220))


def trail(img, pts_t, t, life=0.5):
    """Smoke trail: pts_t = list of (x, y, t_emit)."""
    d = ImageDraw.Draw(img)
    for (x, y, te) in pts_t:
        age = t - te
        if age < 0 or age > life:
            continue
        k = age / life
        rr = 1.5 + k * 4
        c = (236, 236, 240) if k < 0.5 else (196, 196, 206)
        d.ellipse([x - rr, y - rr - k * 4, x + rr, y + rr - k * 4], fill=c)


def note(img, x, y, col=(40, 30, 40)):
    """Tiny eighth note ♪ (x, y = head bottom-left)."""
    x, y = int(x), int(y) - 7
    pts = set()
    for r, row in enumerate(_NOTE):
        for c, ch in enumerate(row):
            if ch == "#":
                pts.add((c, r))
    for (c, r) in pts:                          # white rim so it reads on any background
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (c + dx, r + dy) not in pts:
                pset(img, x + c + dx, y + r + dy, (255, 255, 255))
    for (c, r) in pts:
        pset(img, x + c, y + r, col)


_NOTE = ("...##.",
         "...#.#",
         "...#..",
         "...#..",
         ".###..",
         "####..",
         ".##...")


def vein(img, x, y, s=1, col=(228, 40, 56)):
    """Manga anger mark (4 bulging arcs)."""
    x, y = int(x), int(y)
    pts = []
    for sx in (-1, 1):                    # four L-brackets, corners pointing at the centre
        for sy in (-1, 1):
            pts += [(sx * 3, sy), (sx * 2, sy), (sx, sy), (sx, sy * 2), (sx, sy * 3)]
    for (a, b) in pts:
        rect(img, x + a * s - 1, y + b * s - 1, s + 2, s + 2, INK)
    for (a, b) in pts:
        rect(img, x + a * s, y + b * s, s, s, col)


def twinkle_star(img, x, y, t, t0, dur=0.9, size=7, col=(255, 250, 200)):
    """Big 4-point 'kira' star (a character flying off into the sky)."""
    p = (t - t0) / dur
    if p < 0 or p > 1:
        return
    s = size * (math.sin(p * math.pi) ** 0.5) * (1.0 + 0.25 * math.sin(t * 40))
    s = int(round(s))
    if s <= 0:
        return
    d = ImageDraw.Draw(img)
    d.polygon([(x - s, y), (x - 1, y - 1), (x, y - s), (x + 1, y - 1), (x + s, y), (x + 1, y + 1),
               (x, y + s), (x - 1, y + 1)], fill=col)
    d.point((x, y), fill=(255, 255, 255))
    if s > 3:
        k = s // 2
        for (a, b) in ((-k, -k), (k, k), (-k, k), (k, -k)):
            d.point((x + a, y + b), fill=col)


def kira_burst(img, x, y, t, t0, dur=0.3, n=8, length=16, col=(255, 250, 210)):
    """Short radial rays shooting out of a point (the 'kira!' of a new star)."""
    p = (t - t0) / dur
    if p < 0 or p > 1:
        return
    d = ImageDraw.Draw(img)
    r0 = 3 + length * ease_out(p)
    r1 = 3 + length * ease_out(min(1.0, p * 1.8))
    for i in range(n):
        a = i * 2 * math.pi / n + math.pi / n
        ll = 0.6 if i % 2 else 1.0
        d.line([(x + math.cos(a) * r0 * 0.5 * ll, y + math.sin(a) * r0 * 0.5 * ll),
                (x + math.cos(a) * r1 * ll, y + math.sin(a) * r1 * ll)], fill=col)


def dango_prop(img, ctx):
    """Character prop (pass as draw_char(..., props=[dango_prop])): a 3-ball
    hanami dango skewer held upright in the front hand (sprite-local coords)."""
    hand = ctx.get("hand_f")
    if not hand:
        return
    hx, hy = int(round(hand[0])), int(round(hand[1]))
    rect(img, hx, hy - 12, 1, 12, (196, 160, 108))                 # stick
    for i, col in enumerate(((120, 190, 110), (250, 250, 240), (250, 150, 180))):
        by = hy - 5 - i * 3
        rect(img, hx - 2, by - 2, 5, 4, INK)
        rect(img, hx - 1, by - 1, 3, 2, col)
    rect(img, hx - 1, hy - 1, 3, 3, INK)                           # fingers over the stick
    rect(img, hx, hy, 1, 1, (255, 222, 196))


def crow(img, x, y, t, s=1):
    """Gintama's awkward-silence crow: black bird flapping at 8 fps, facing left. (x, y) = body centre."""
    f = step_frame(t, 8, 2)
    body = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1),
            (7, 1), (2, 2), (3, 2), (4, 2), (5, 2), (-1, 0), (-2, 0), (-1, -1), (0, -1), (7, 2), (8, 2)]
    wing = ([(2, -1), (3, -1), (4, -2), (4, -1), (5, -3), (5, -2), (6, -4), (6, -3), (7, -4)] if f else
            [(2, 2), (3, 3), (4, 3), (4, 4), (5, 4), (5, 5), (6, 5)])
    pts = body + wing
    xs = {(px, py) for (px, py) in pts}
    for (px, py) in xs:
        rect(img, int(x + px * s), int(y + py * s), s, s, (26, 22, 34))
    for (px, py) in ((1, 0), (2, 0), (3, 1)):
        rect(img, int(x + px * s), int(y + py * s), s, s, (70, 66, 90))
    rect(img, int(x - 3 * s), int(y), s, s, (60, 56, 70))       # beak
    rect(img, int(x), int(y - 1 * s), s, s, (255, 255, 255))    # eye


def bump(img, x, y):
    """Swollen bump on the head (x, y = bump centre)."""
    d = ImageDraw.Draw(img)
    d.ellipse([x - 3, y - 3, x + 3, y + 2], fill=(255, 176, 176), outline=INK)
    pset(img, x - 1, y - 1, (255, 230, 230))


def sweat(img, x, y):
    from chars.hijikata import sweat_drop
    sweat_drop(img, x, y)


# ======================================================================== courtyard (final pose)
@lru_cache(maxsize=2)
def wall_strip():
    """Compound wall seen from inside the courtyard: tile cap y 0..9, plaster
    9..26, stone base 26..34 (local rows). W wide, 'day' graded."""
    L = Image.new("RGBA", (W, 36), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    r = rng("s04wall")
    d.rectangle([0, 9, W, 26], fill=_rgba(PLASTER))
    d.rectangle([0, 9, W, 11], fill=_rgba(PLASTER_SH))
    for i in range(60):
        d.point((r.randint(0, W - 1), r.randint(12, 25)), fill=_rgba((224, 216, 198)))
    d.rectangle([0, 26, W, 35], fill=_rgba(MORTAR))
    for row, y in enumerate((27, 31)):
        off = (row % 2) * 6
        for x in range(-12 + off, W, 12):
            d.rectangle([x + 1, y, x + 10, y + 2], fill=_rgba(STONE))
            d.line([(x + 1, y), (x + 10, y)], fill=_rgba(STONE_HI))
    cap = [(-2, 9), (0, 2), (W, 2), (W + 2, 9)]
    L.alpha_composite(_tile_roof(d, [(x, y) for (x, y) in cap], 2, 9, 4, rows=(0.5,)).crop((0, 0, W, 36)))
    d = ImageDraw.Draw(L)
    d.rectangle([0, 0, W, 2], fill=_rgba(TILE_DK2))
    d.line([(0, 0), (W, 0)], fill=_rgba(TILE_HI))
    d.line([(0, 9), (W, 9)], fill=_rgba(TILE_DK2))
    d.line([(0, 26), (W, 26)], fill=_rgba(INK))
    return C.grade_rgba(L, "day")


def light_rays(img, cx, cy, t, n=14, alpha=0.16, color=(255, 250, 230), speed=0.12):
    """Soft rotating god-rays (alpha overlay) from (cx, cy)."""
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    R = 500
    rot = t * speed
    a8 = int(255 * alpha)
    for i in range(n):
        a0 = rot + i * 2 * math.pi / n
        a1 = a0 + math.pi / n * 0.7
        d.polygon([(cx, cy), (cx + math.cos(a0) * R, cy + math.sin(a0) * R),
                   (cx + math.cos(a1) * R, cy + math.sin(a1) * R)], fill=a8)
    img.paste(color, (0, 0, W, H), m)
