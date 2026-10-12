"""Private art for s02 新八登场: family-restaurant set, Shimura dojo set, props,
eye close-up band.  Everything static is built once and cached at module level.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import W, H, clamp, wave, step_frame, rng
from engine.gfx import INK, ascii_sprite, shade, mix, stamp_line, pset, outline, scale_nearest
from engine.text import draw_text, text_width
from chars import render_sprite
from bg import common as C, kabukicho as K

_CACHE = {}


def cached(key, fn):
    v = _CACHE.get(key)
    if v is None:
        v = fn()
        _CACHE[key] = v
    return v


# ======================================================================= layout
FLOOR_Y = 160
WALL_BASE = 136
DOOR = (22, 82, 36, 54)            # kitchen swing door (x, y, w, h)
DOOR_CX = DOOR[0] + DOOR[2] // 2
WIN = (143, 25, 297, 97)           # window glass (x0, y0, x1, y1)
MULLIONS = (193, 246)
POSTER = (306, 28, 358, 86)
CLOCK = (104, 36, 9)
HOLE = (100, 76)                   # centre of the pig-shaped hole
COUNTER = (206, 352)               # x range; top y 136..140, face 141..151
COUNTER_TOP = 136
STOOLS = (226, 304, 334)
SEAT_Y = 150                       # draw_char y for someone sitting on a stool
LAMPS = (64, 172, 268)
FAN_X = 330
PARFAIT_POS = (286, 136)           # bottom-centre of the parfait on the counter

# ======================================================================= sprites
PARFAIT_ART = """
.......yy.
......yYy.
...r.yYy..
..rRrYy...
..orroo...
.oWWWWWo..
oWWwWWWWo.
oWWWWwWWo.
.gCCCCCg..
.gcWWWcg..
.gCCCCCg..
.gFFfFFg..
.gCCCCCg..
..gcCcg...
...gGg....
....g.....
....g.....
..gggGg...
"""
PARFAIT_PAL = {
    "o": INK, "W": (255, 250, 240), "w": (226, 214, 204), "C": (104, 58, 40), "c": (150, 92, 62),
    "F": (232, 184, 96), "f": (250, 214, 140), "r": (214, 40, 56), "R": (255, 150, 150),
    "g": (178, 208, 236), "G": (120, 150, 190), "y": (214, 150, 70), "Y": (246, 200, 120),
}

HEART_ART = """
.oo.oo.
oRRoRRo
oRWRRRo
.oRRRo.
..oRo..
...o...
"""
HEART_PAL = {"o": INK, "R": (236, 76, 110), "W": (255, 200, 210)}

VEIN_ART = """
.rr.rr.
rr...rr
r.....r
.......
r.....r
rr...rr
.rr.rr.
"""
VEIN_PAL = {"r": (232, 48, 64)}

SWEAT_ART = """
..o..
.oBo.
oBBBo
oBwBo
.ooo.
"""
SWEAT_PAL = {"o": INK, "B": (130, 200, 255), "w": (240, 250, 255)}

HAT_ART = """
.ooo.ooo.
oWWWoWWWo
oWWWWWWwo
oWWWWWWwo
.oWWWWwo.
.owwwwwo.
.ooooooo.
"""
HAT_PAL = {"o": INK, "W": (252, 252, 255), "w": (206, 212, 226)}

CROW_ARTS = ("""
.o.......
okoo.....
.okkoo.oo
..okkkkoy
..okkkko.
...oooo..
""", """
.........
.........
..ooo..oo
.okkkkkoy
okkkkkko.
.ooooo...
""")
CROW_PAL = {"o": (10, 8, 16), "k": (44, 40, 60), "y": (250, 200, 60), "W": (255, 255, 255)}
CROW_PERCH = ("""
....oooo...
...okkkko..
.yyokWkkko.
..ookkkkko.
...okkkkkko
...okkkkkkko
....okkkkkko
.....ooooooo
......y..y..
""", """
.y..oooo...
..yokkkko..
...okWkkko.
.yyokkkkko.
...okkkkkko
...okkkkkkko
....okkkkkko
.....ooooooo
......y..y..
""")

SOUL_ART = """
..ooo..
.oWWWo.
oWoWoWo
oWWWWWo
oWWWWWo
.oWWWWo
..oWWo.
...oWo.
....oo.
"""
SOUL_PAL = {"o": (120, 140, 200), "W": (240, 246, 255)}

TRAY_ART = """
ooooooooooooo
oSSSSSSSSSSso
.ooooooooooo.
"""
TRAY_PAL = {"o": INK, "S": (222, 228, 240), "s": (170, 180, 200)}

EGG_ART = """
..oooo.
.oKKkKo
oKkKKKo
oKKKkKo
.ooooo.
"""
EGG_PAL = {"o": INK, "K": (30, 22, 36), "k": (84, 60, 96)}


def spr(key):
    table = {
        "parfait": (PARFAIT_ART, PARFAIT_PAL), "heart": (HEART_ART, HEART_PAL),
        "vein": (VEIN_ART, VEIN_PAL), "sweat": (SWEAT_ART, SWEAT_PAL), "hat": (HAT_ART, HAT_PAL),
        "crow0": (CROW_ARTS[0], CROW_PAL), "crow1": (CROW_ARTS[1], CROW_PAL),
        "perch0": (CROW_PERCH[0], CROW_PAL), "perch1": (CROW_PERCH[1], CROW_PAL),
        "soul": (SOUL_ART, SOUL_PAL), "tray": (TRAY_ART, TRAY_PAL), "egg": (EGG_ART, EGG_PAL),
    }
    return cached(("spr", key), lambda: ascii_sprite(*table[key]))


def parfait_big(k=2):
    return cached(("parfait_big", k), lambda: scale_nearest(spr("parfait"), k))


# ======================================================================= street view
def street_view():
    """A Kabukicho street frame (static) used for views through the window/hole."""
    def mk():
        im = Image.new("RGB", (W, H))
        K.street(im, 620, 0.0, "day")
        return im
    return cached("street_view", mk)


def _view_crop(x0, y0, w, h, sx, sy):
    sv = street_view()
    c = sv.crop((sx, sy, sx + w, sy + h))
    a = np.asarray(c).astype(np.float32)
    a = a * 0.86 + np.array((226, 238, 248), np.float32) * 0.14     # glass haze
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGB")


# ======================================================================= restaurant
WALL = (232, 220, 194)
WALL_S = (222, 206, 178)
WAIN = (146, 96, 64)
WAIN_D = (114, 72, 48)
WAIN_L = (172, 120, 82)
RAIL = (182, 66, 60)
F_LIGHT = (214, 198, 170)
F_DARK = (172, 128, 104)
CTR_TOP = (212, 168, 118)
CTR_TOP_L = (236, 200, 150)
CTR_FACE = (176, 62, 58)
CTR_FACE_D = (140, 46, 46)
CHROME = (206, 214, 228)
CHROME_D = (130, 140, 160)
STOOL_RED = (198, 62, 62)


def _floor(im):
    ys = np.arange(WALL_BASE, H, dtype=np.float32)[:, None]
    xs = np.arange(W, dtype=np.float32)[None, :]
    vpx, vpy = 192.0, 40.0
    s = (ys - vpy) / (H - vpy)
    xw = vpx + (xs - vpx) / s
    col = np.floor(xw / 26.0).astype(int)
    z = 1.0 / s
    row = np.floor((z - 1.0) * 8.0).astype(int)
    par = ((col + row) % 2).astype(bool)
    arr = np.empty((H - WALL_BASE, W, 3), np.float32)
    arr[par] = F_DARK
    arr[~par] = F_LIGHT
    depth = np.clip((ys - WALL_BASE) / (H - WALL_BASE), 0, 1)
    arr *= (0.8 + 0.2 * depth)[..., None] if depth.ndim == 2 else 1
    # soft reflection of the counter/lamps: a lighter streak band
    im.paste(Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGB"), (0, WALL_BASE))


def _door_frame(d):
    x, y, w, h = DOOR
    d.rectangle([x - 3, y - 3, x + w + 2, y + h], fill=(120, 78, 50), outline=INK)
    d.rectangle([x, y, x + w - 1, y + h], fill=(46, 32, 30))
    # 厨房 plate
    d.rectangle([x + 5, y - 14, x + w - 6, y - 5], fill=(40, 34, 44), outline=INK)


def _stool(d, x):
    d.rectangle([x - 1, 149, x, 157], fill=CHROME)
    d.line([(x - 2, 149), (x - 2, 157)], fill=INK)
    d.line([(x + 1, 149), (x + 1, 157)], fill=CHROME_D)
    d.ellipse([x - 6, 156, x + 5, 160], fill=CHROME_D, outline=INK)
    d.rectangle([x - 6, 144, x + 5, 148], fill=STOOL_RED, outline=INK)
    d.line([(x - 5, 145), (x + 3, 145)], fill=(236, 110, 104))


def _counter(d):
    x0, x1 = COUNTER
    d.rectangle([x0, 140, x1, 152], fill=CTR_FACE, outline=INK)
    for x in range(x0 + 20, x1, 24):
        d.line([(x, 145), (x, 149)], fill=CTR_FACE_D)
    d.line([(x0 + 1, 143), (x1 - 1, 143)], fill=CHROME)
    d.line([(x0 + 1, 144), (x1 - 1, 144)], fill=CHROME_D)
    d.rectangle([x0 + 1, 150, x1 - 1, 151], fill=(72, 44, 44))
    d.rectangle([x0 - 2, COUNTER_TOP, x1 + 2, 140], fill=CTR_TOP, outline=INK)
    d.line([(x0 - 1, COUNTER_TOP + 1), (x1 + 1, COUNTER_TOP + 1)], fill=CTR_TOP_L)
    # little counter props: napkin box, sugar pot, beer mug (pig A), menu stand
    d.rectangle([248, 130, 255, 135], fill=CHROME, outline=INK)
    d.line([(250, 129), (253, 129)], fill=(250, 250, 250))
    d.rectangle([338, 131, 344, 135], fill=(240, 236, 226), outline=INK)
    d.rectangle([339, 129, 343, 130], fill=(200, 160, 110), outline=INK)
    d.rectangle([209, 127, 216, 135], fill=(250, 214, 110), outline=INK)   # beer mug
    d.rectangle([210, 127, 215, 129], fill=(255, 252, 240))
    d.line([(217, 129), (218, 129), (218, 133), (217, 133)], fill=INK)
    d.rectangle([318, 128, 324, 135], fill=(40, 40, 52), outline=INK)       # menu stand
    d.line([(320, 130), (322, 130)], fill=(255, 220, 120))


def _poster(im, d):
    x0, y0, x1, y1 = POSTER
    d.rectangle([x0, y0, x1, y1], fill=(250, 246, 234), outline=INK)
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y0 + 14], fill=(206, 58, 60))
    draw_text(im, (x0 + x1) // 2, y0 + 2, "本日推荐", (255, 255, 255), anchor="mt")
    p = parfait_big(2)
    im.paste(p, ((x0 + x1) // 2 - p.width // 2, y0 + 17), p)
    # sparkles on the poster
    for sx, sy in ((x0 + 6, y0 + 24), (x1 - 7, y0 + 40), (x0 + 8, y1 - 12)):
        d.point((sx, sy), fill=(254, 200, 60))
        d.point((sx - 1, sy), fill=(254, 200, 60))
        d.point((sx + 1, sy), fill=(254, 200, 60))
        d.point((sx, sy - 1), fill=(254, 200, 60))
        d.point((sx, sy + 1), fill=(254, 200, 60))
    # pin
    d.point(((x0 + x1) // 2, y0 + 1), fill=(60, 60, 200))


def _clock_face(d):
    cx, cy, r = CLOCK
    d.ellipse([cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1], fill=(120, 78, 50), outline=INK)
    d.ellipse([cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1], fill=(250, 248, 240))
    for i in range(12):
        a = i * math.pi / 6
        d.point((cx + round(math.cos(a) * (r - 2)), cy + round(math.sin(a) * (r - 2))), fill=INK)


def rest_bg():
    """Static family-restaurant set (RGB)."""
    def mk():
        im = Image.new("RGB", (W, H), WALL)
        d = ImageDraw.Draw(im)
        for x in range(0, W, 12):
            d.line([(x, 12), (x, 104)], fill=WALL_S)
        # ceiling
        d.rectangle([0, 0, W, 10], fill=(70, 52, 48))
        d.line([(0, 8), (W, 8)], fill=(96, 72, 60))
        d.line([(0, 11), (W, 11)], fill=INK)
        # wainscot + rail
        d.rectangle([0, 105, W, WALL_BASE - 1], fill=WAIN)
        for x in range(4, W, 16):
            d.line([(x, 108), (x, WALL_BASE - 3)], fill=WAIN_D)
            d.line([(x + 1, 108), (x + 1, WALL_BASE - 3)], fill=WAIN_L)
        d.rectangle([0, 103, W, 106], fill=RAIL)
        d.line([(0, 103), (W, 103)], fill=INK)
        d.line([(0, 107), (W, 107)], fill=INK)
        d.line([(0, 104), (W, 104)], fill=(222, 104, 96))
        d.rectangle([0, WALL_BASE - 3, W, WALL_BASE - 1], fill=(84, 54, 40))
        _floor(im)
        d.line([(0, WALL_BASE), (W, WALL_BASE)], fill=(70, 50, 40))
        # window: view + frame
        x0, y0, x1, y1 = WIN
        im.paste(_view_crop(x0, y0, x1 - x0, y1 - y0, 150, 64), (x0, y0))
        d.rectangle([x0 - 4, y0 - 4, x1 + 4, y1 + 1], outline=INK)
        d.rectangle([x0 - 3, y0 - 3, x1 + 3, y0 - 1], fill=(150, 100, 64))
        d.rectangle([x0 - 3, y0, x0 - 1, y1], fill=(150, 100, 64))
        d.rectangle([x1 + 1, y0, x1 + 3, y1], fill=(126, 82, 52))
        d.rectangle([x0 - 7, y1 + 1, x1 + 7, y1 + 4], fill=(178, 124, 84), outline=INK)
        # kitchen door frame + plate text
        _door_frame(d)
        draw_text(im, DOOR_CX, DOOR[1] - 13, "厨房", (255, 236, 180), anchor="mt")
        _poster(im, d)
        _clock_face(d)
        # potted plant right corner
        d.rectangle([362, 122, 376, 135], fill=(170, 90, 60), outline=INK)
        for i, (lx, ly) in enumerate(((356, 104), (366, 96), (378, 104), (360, 114), (374, 112), (369, 106))):
            d.ellipse([lx - 5, ly - 3, lx + 5, ly + 5], fill=(62, 128, 72) if i % 2 else (84, 156, 86), outline=INK)
        _counter(d)
        for sx in STOOLS:
            _stool(d, sx)
        return im
    return cached("rest_bg", mk)


def window_overlay():
    """Mullions + glass glare (RGBA) drawn over the window view each frame."""
    def mk():
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        x0, y0, x1, y1 = WIN
        for mx in MULLIONS:
            d.rectangle([mx - 1, y0, mx + 1, y1], fill=(150, 100, 64, 255))
            d.line([(mx - 2, y0), (mx - 2, y1)], fill=INK + (255,))
            d.line([(mx + 2, y0), (mx + 2, y1)], fill=INK + (255,))
        d.line([(x0, 60), (x1, 60)], fill=(150, 100, 64, 255))
        d.line([(x0, 59), (x1, 59)], fill=INK + (255,))
        d.line([(x0, 61), (x1, 61)], fill=INK + (255,))
        # glare stripes
        for gx in (150, 204, 258):
            d.polygon([(gx, y1), (gx + 10, y1), (gx + 34, y0), (gx + 24, y0)], fill=(255, 255, 255, 46))
            d.polygon([(gx + 13, y1), (gx + 16, y1), (gx + 40, y0), (gx + 37, y0)], fill=(255, 255, 255, 30))
        return ov
    return cached("win_ov", mk)


def draw_clock_hands(img, t):
    cx, cy, r = CLOCK
    d = ImageDraw.Draw(img)
    a_h = math.radians(-60 + 90)
    d.line([(cx, cy), (cx + math.cos(a_h - math.pi / 2) * 4, cy + math.sin(a_h - math.pi / 2) * 4)], fill=INK, width=1)
    sec = step_frame(t, 1)
    a_s = sec * math.pi / 30 - math.pi / 2
    d.line([(cx, cy), (cx + round(math.cos(a_s) * 7), cy + round(math.sin(a_s) * 7))], fill=(210, 50, 50))
    d.point((cx, cy), fill=INK)


def draw_lamps(img, t):
    d = ImageDraw.Draw(img)
    for i, lx in enumerate(LAMPS):
        sw = wave(t, 0.23, 1.2, i * 0.31)
        bx = lx + sw
        d.line([(lx, 11), (round(bx), 26)], fill=(40, 36, 44))
        x = round(bx)
        d.polygon([(x - 7, 33), (x - 4, 27), (x + 4, 27), (x + 7, 33)], fill=(196, 72, 62), outline=INK)
        d.line([(x - 3, 28), (x + 2, 28)], fill=(236, 120, 100))
        d.line([(x - 6, 34), (x + 6, 34)], fill=(255, 238, 170))
        d.rectangle([x - 1, 35, x + 1, 36], fill=(255, 250, 220))
    # ceiling fan
    f = step_frame(t, 10, 3)
    d.rectangle([FAN_X - 1, 11, FAN_X, 14], fill=(60, 50, 50))
    spans = ((14, 3), (9, 9), (3, 14))[f]
    d.line([(FAN_X - spans[0], 16), (FAN_X + spans[1], 16)], fill=(92, 70, 60), width=2)
    d.rectangle([FAN_X - 2, 14, FAN_X + 1, 17], fill=(120, 100, 90), outline=INK)


def draw_door(img, t, open_k, lit=True):
    """Kitchen swing door. open_k 0 = closed, 1 = slammed fully open."""
    x, y, w, h = DOOR
    d = ImageDraw.Draw(img)
    if open_k > 0.02:
        # kitchen interior: back wall, shelf with ladles, stove with flickering flames, steaming pot
        d.rectangle([x, y, x + w - 1, y + h], fill=(96, 68, 56))
        d.rectangle([x + 10, y + 2, x + 24, y + 4], fill=(255, 226, 160))
        d.line([(x + 1, y + 12), (x + w - 2, y + 12)], fill=(60, 40, 34), width=2)
        for i in range(3):
            lx = x + 6 + i * 10
            d.line([(lx, y + 13), (lx, y + 21)], fill=(176, 180, 190))
            d.rectangle([lx - 1, y + 21, lx + 1, y + 22], fill=(176, 180, 190))
        d.rectangle([x, y + h - 14, x + w - 1, y + h], fill=(66, 48, 44))
        d.rectangle([x + 1, y + h - 16, x + w - 2, y + h - 14], fill=(160, 164, 176))
        for i, fx0 in enumerate((x + 8, x + 26)):
            fl = 2 + (step_frame(t, 12) + i) % 2
            d.rectangle([fx0 - 3, y + h - 16 - fl, fx0 + 3, y + h - 17], fill=(255, 140, 50))
            d.rectangle([fx0 - 1, y + h - 17 - fl, fx0 + 1, y + h - 17], fill=(255, 230, 120))
        d.rectangle([x + 3, y + h - 26, x + 14, y + h - 19], fill=(180, 184, 196), outline=INK)
        for i in range(3):
            ph = (t * 0.9 + i * 0.33) % 1.0
            sx = x + 6 + i * 3 + math.sin(ph * 6 + i) * 2
            sy = y + h - 28 - ph * 26
            r = 1 + ph * 2.5
            d.ellipse([sx - r, sy - r * 0.7, sx + r, sy + r * 0.7], fill=(214, 204, 198) if ph < 0.6 else (160, 136, 126))
    pw = int(round(w * (1 - open_k)))
    if pw > 3:
        d.rectangle([x, y, x + pw - 1, y + h], fill=(198, 154, 106), outline=INK)
        d.rectangle([x + 1, y + h - 8, x + pw - 2, y + h - 2], fill=CHROME)
        if pw > 14:
            cx = x + pw // 2
            d.ellipse([cx - 6, y + 10, cx + 6, y + 22], fill=(150, 196, 214), outline=INK)
            d.line([(cx - 3, y + 13), (cx - 1, y + 12)], fill=(236, 250, 255))
        d.line([(x + 1, y + 1), (x + 1, y + h - 1)], fill=(222, 184, 138))
    else:
        d.line([(x, y), (x, y + h)], fill=INK)
    # hinge-side slammed panel sliver
    if open_k > 0.9:
        d.rectangle([x - 5, y - 1, x - 2, y + h], fill=(198, 154, 106), outline=INK)


def hole_sprite():
    """Pig-shaped hole in the wall: outside view inside an ink-edged silhouette."""
    def mk():
        s, ax, ay = render_sprite("amanto_pig", "shock", 0.1, p=0.9, scale=1)
        bb = s.getbbox()
        s = s.crop(bb)
        s = scale_nearest(s, 0.9)
        mask = np.asarray(s)[..., 3] > 0
        h, w = mask.shape
        pad = 4
        m = np.zeros((h + pad * 2, w + pad * 2), bool)
        m[pad:pad + h, pad:pad + w] = mask
        # dilate once so the hole is a bit bigger than the pig
        mm = m.copy()
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            mm |= np.roll(np.roll(m, dy, 0), dx, 1)
        edge = np.zeros_like(mm)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            edge |= np.roll(np.roll(mm, dy, 0), dx, 1)
        edge &= ~mm
        hh, ww = mm.shape
        # bright outside view: sky, a cloud, far rooftops
        vim = Image.new("RGB", (ww, hh), (150, 204, 250))
        vd = ImageDraw.Draw(vim)
        for yy in range(hh):
            if yy > hh * 0.35:
                vd.line([(0, yy), (ww, yy)], fill=(186, 222, 250) if yy % 2 else (170, 214, 250))
        vd.ellipse([2, 5, 16, 12], fill=(255, 255, 255))
        vd.ellipse([9, 2, 22, 11], fill=(255, 255, 255))
        vd.polygon([(0, hh), (0, hh - 9), (8, hh - 13), (16, hh - 9), (22, hh - 12), (30, hh - 8),
                    (ww, hh - 10), (ww, hh)], fill=(112, 120, 156))
        view = np.asarray(vim).copy()
        out = np.zeros((hh, ww, 4), np.uint8)
        out[mm, :3] = view[mm]
        out[mm, 3] = 255
        out[edge] = INK + (255,)
        # broken plaster rim (lighter) just outside the ink edge
        rim = np.zeros_like(mm)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            rim |= np.roll(np.roll(edge, dy, 0), dx, 1)
        rim &= ~(mm | edge)
        r = rng("rim")
        ys, xs = np.nonzero(rim)
        for yy, xx in zip(ys, xs):
            if r.random() < 0.55:
                out[yy, xx] = (250, 242, 222, 255)
        return Image.fromarray(out, "RGBA")
    return cached("hole", mk)


def draw_hole(img, t, t0):
    hs = hole_sprite()
    x, y = HOLE
    img.paste(hs, (x - hs.width // 2, y - hs.height // 2), hs)
    # cracks radiating from the hole
    d = ImageDraw.Draw(img)
    r = rng("cracks")
    for i in range(9):
        a = i / 9 * math.tau + r.uniform(-0.2, 0.2)
        r0 = hs.width * 0.42
        pts = [(x + math.cos(a) * r0, y + math.sin(a) * r0 * 1.1)]
        L = r.uniform(6, 13)
        for k in range(3):
            a2 = a + r.uniform(-0.5, 0.5)
            px, py = pts[-1]
            pts.append((px + math.cos(a2) * L / 3, py + math.sin(a2) * L / 3))
        pts = [(px, min(py, 102)) for px, py in pts]
        d.line(pts, fill=(96, 80, 70))


# ======================================================================= dojo
def dojo_bg():
    def mk():
        im = Image.new("RGB", (W, H))
        C.room_wall(im, 20, "dusk_in", 0, 136, "shoji")
        C.wood_floor(im, 136, 0, "dusk_in")
        d = ImageDraw.Draw(im)
        # plaque 志村道场 on the lintel strip
        x0, x1 = 158, 226
        d.rectangle([x0 - 1, 11, x1 + 1, 29], fill=INK)
        d.rectangle([x0, 12, x1, 28], fill=(92, 58, 40))
        d.rectangle([x0 + 2, 14, x1 - 2, 26], fill=(118, 76, 50))
        draw_text(im, (x0 + x1) // 2 + 1, 15, "志村道场", (20, 12, 10), anchor="mt")
        draw_text(im, (x0 + x1) // 2, 14, "志村道场", (250, 226, 170), anchor="mt")
        d.line([(x0 + 8, 11), (x0 + 4, 4)], fill=INK)
        d.line([(x1 - 8, 11), (x1 - 4, 4)], fill=INK)
        # bokuto rack (right)
        rx = 318
        d.rectangle([rx, 96, rx + 44, 99], fill=(96, 62, 42), outline=INK)
        d.rectangle([rx, 124, rx + 44, 127], fill=(96, 62, 42), outline=INK)
        d.rectangle([rx + 1, 96, rx + 3, 135], fill=(80, 52, 36), outline=INK)
        d.rectangle([rx + 41, 96, rx + 43, 135], fill=(80, 52, 36), outline=INK)
        for i in range(5):
            bx = rx + 8 + i * 7
            d.line([(bx, 90), (bx + 2, 134)], fill=INK, width=3)
            d.line([(bx, 91), (bx + 2, 133)], fill=(206, 156, 100))
            d.line([(bx, 90), (bx + 1, 99)], fill=(80, 50, 36), width=2)
        # hanging scroll (left)
        sx = 290
        d.rectangle([sx, 40, sx + 18, 100], fill=(236, 226, 196), outline=INK)
        d.rectangle([sx - 2, 38, sx + 20, 40], fill=(90, 60, 40), outline=INK)
        d.rectangle([sx - 2, 100, sx + 20, 102], fill=(90, 60, 40), outline=INK)
        for i, ch in enumerate("一心"):
            draw_text(im, sx + 9, 46 + i * 16, ch, (30, 22, 20), anchor="mt")
        # zabuton cushions
        for cx in (104, 150):
            d.polygon([(cx - 10, 161), (cx - 7, 156), (cx + 9, 156), (cx + 12, 161)], fill=(120, 60, 110), outline=INK)
            d.line([(cx - 6, 157), (cx + 8, 157)], fill=(160, 90, 150))
        # evening light shafts from the left shoji
        a = np.asarray(im).astype(np.float32)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        for bx0, bw in ((40, 26), (120, 18), (190, 30)):
            u = (xx - bx0) - (yy * 0.55)
            m = ((u > 0) & (u < bw) & (yy > 30)).astype(np.float32)
            dm = (np.indices((H, W)).sum(0) % 2).astype(np.float32)
            k = m * (0.10 + 0.05 * dm)
            a = a * (1 - k[..., None]) + np.array((255, 210, 150), np.float32) * k[..., None]
        return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGB")
    return cached("dojo_bg", mk)


# ======================================================================= dojo gate (exterior)
GATE_TOD = "dusk"
GATE_CX = 192


def gate_back():
    """Dusk sky + hazy mountains (RGB)."""
    def mk():
        im = Image.new("RGB", (W, H))
        C.sky(im, GATE_TOD, 0.0, horizon=150)
        C.far_mountains(im, 40, GATE_TOD, y=150)
        return im
    return cached("gate_back", mk)


def gate_front():
    """Shimura dojo gate + plaster walls + road (RGBA, dusk-graded)."""
    def mk():
        from bg._draw import roof, TILE, WOOD, WOOD_D, PLASTER
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        # plaster walls both sides with tiled caps and dark wainscot
        for x0, x1 in ((-4, 128), (256, W + 4)):
            d.rectangle([x0, 92, x1, 156], fill=PLASTER.mid)
            for yy in range(96, 140, 7):
                d.line([(x0, yy), (x1, yy)], fill=PLASTER.dark if yy % 2 else PLASTER.mid)
            d.rectangle([x0, 136, x1, 156], fill=WOOD_D.mid)
            for xx in range(x0 + 3, x1, 6):
                d.line([(xx, 137), (xx, 155)], fill=WOOD_D.dark)
            d.line([(x0, 136), (x1, 136)], fill=INK)
            roof(d, x0 - 4, x1 + 4, 84, 91, TILE, inset=3, ridge=True, oni=False)
        # gate posts
        for px in (132, 244):
            d.rectangle([px - 5, 64, px + 5, 157], fill=WOOD.mid, outline=INK)
            d.line([(px - 3, 65), (px - 3, 156)], fill=WOOD.hi)
            d.line([(px + 3, 65), (px + 3, 156)], fill=WOOD.dark)
        # crossbeams
        d.rectangle([120, 66, 256, 72], fill=WOOD.dark, outline=INK)
        d.line([(121, 67), (255, 67)], fill=WOOD.mid)
        d.rectangle([127, 80, 249, 84], fill=WOOD.dark, outline=INK)
        # gate roof
        roof(d, 108, 276, 44, 64, TILE, inset=14, ridge=True, oni=True, eave_shadow=INK)
        # doors (one slightly open -> warm light inside)
        d.rectangle([138, 85, 238, 157], fill=WOOD_D.mid, outline=INK)
        for xx in range(140, 238, 5):
            d.line([(xx, 86), (xx, 156)], fill=WOOD_D.dark)
        d.rectangle([186, 85, 194, 157], fill=(255, 196, 120))
        d.line([(186, 85), (186, 157)], fill=INK)
        d.line([(194, 85), (194, 157)], fill=INK)
        for yy in (100, 128):
            d.rectangle([138, yy, 186, yy + 3], fill=WOOD.mid, outline=INK)
            d.rectangle([194, yy, 238, yy + 3], fill=WOOD.mid, outline=INK)
        # vertical signboard on the right post
        sx0, sy0 = 250, 86
        d.rectangle([sx0, sy0, sx0 + 15, sy0 + 58], fill=(244, 236, 214), outline=INK)
        d.rectangle([sx0 + 1, sy0 + 1, sx0 + 14, sy0 + 57], outline=(170, 150, 120))
        for i, ch in enumerate("志村道场"):
            draw_text(im, sx0 + 8, sy0 + 3 + i * 13, ch, (24, 16, 16, 255), anchor="mt")
        # road
        d.rectangle([0, 157, W, H], fill=(150, 128, 104))
        r = rng("gate_road")
        for _ in range(260):
            x, y = r.randrange(W), r.randrange(158, H)
            d.point((x, y), fill=(128, 108, 88) if r.random() < 0.6 else (172, 150, 124))
        d.line([(0, 157), (W, 157)], fill=(96, 80, 66))
        g = C.grade_rgba(im, GATE_TOD)
        # keep the door-gap light warm & bright after grading
        gd = ImageDraw.Draw(g)
        gd.rectangle([187, 86, 193, 156], fill=(255, 206, 130, 255))
        return g
    return cached("gate_front", mk)


# ======================================================================= eyes close-up
SKIN = (255, 216, 184)
SKIN_S = (236, 180, 150)
HAIR = ((238, 240, 250), (196, 202, 224), (146, 152, 188))
IRIS_DEAD = ((126, 32, 50), (86, 20, 36), (54, 12, 24))
IRIS_HOT = ((214, 44, 70), (150, 24, 48), (40, 6, 16))


def eye_band(serious):
    """Anime-style close-up of Gintoki's eyes, 192x40 (scale x2 on screen)."""
    def mk():
        bw, bh = 192, 40
        im = Image.new("RGB", (bw, bh), SKIN)
        d = ImageDraw.Draw(im)
        cy = 24
        for cx, o in ((62, -1), (130, 1)):      # o = direction of the outer corner
            iris = IRIS_HOT if serious else IRIS_DEAD
            outer = (cx + o * 18, cy + 1)
            inner = (cx - o * 15, cy + 2)
            if serious:
                top = [outer, (cx + o * 9, cy - 6), (cx - o * 4, cy - 4), inner]
            else:
                top = [outer, (cx + o * 9, cy - 1), (cx - o * 6, cy - 1), inner]
            bot = [inner, (cx - o * 7, cy + 6), (cx + o * 9, cy + 6), outer]
            d.polygon(top + bot[1:-1], fill=(255, 255, 255))
            # iris
            ix, iy = cx + o * 1, cy + 1
            d.ellipse([ix - 6, iy - 6, ix + 6, iy + 6], fill=iris[0])
            d.ellipse([ix - 6, iy - 6, ix + 6, iy + 6], outline=iris[1])
            if serious:
                d.ellipse([ix - 2, iy - 3, ix + 2, iy + 3], fill=iris[2])
                d.rectangle([ix + o * 2 - 1, iy - 4, ix + o * 2 + 1, iy - 2], fill=(255, 255, 255))
                d.point((ix - o * 3, iy + 3), fill=(255, 210, 220))
            else:
                d.ellipse([ix - 2, iy - 2, ix + 2, iy + 2], fill=iris[2])
            # cover everything above the lid with skin, then the lid line
            poly = [(outer[0] + o * 2, 0), (outer[0] + o * 2, outer[1])] + top[1:] + [(inner[0], 0)]
            d.polygon(poly, fill=SKIN)
            # lid shadow under the line (heavy for dead eyes)
            d.line(top, fill=SKIN_S if not serious else (200, 140, 130), width=3 if not serious else 1)
            d.line([(p[0], p[1] + (1 if not serious else 0)) for p in top], fill=INK, width=2)
            d.line(bot, fill=(200, 130, 120))
            # lashes at the outer corner
            d.line([outer, (outer[0] + o * 3, outer[1] - 2)], fill=INK, width=2)
            # brows
            if serious:
                d.line([(cx - o * 14, cy - 8), (cx + o * 16, cy - 14)], fill=INK, width=3)
                d.line([(cx - o * 13, cy - 9), (cx + o * 15, cy - 15)], fill=(150, 150, 176))
            else:
                d.line([(cx - o * 12, cy - 13), (cx + o * 15, cy - 14)], fill=INK, width=2)
        # nose bridge shading
        d.line([(96, 30), (97, 36)], fill=SKIN_S)
        # bangs: silver strands with ink edges
        r = rng("bangs")
        x = -6
        i = 0
        while x < bw + 6:
            wdt = r.randint(10, 17)
            tip = r.randint(6, 13) + (4 if 84 < x < 104 else 0)
            tipx = x + wdt // 2 + r.randint(-3, 3)
            col = HAIR[i % 3] if i % 3 != 2 else HAIR[0]
            d.polygon([(x, -1), (x + wdt, -1), (tipx, tip)], fill=col, outline=INK)
            d.line([(x + 2, 0), (tipx, tip - 2)], fill=HAIR[1])
            x += wdt - 3
            i += 1
        if serious:
            a = np.asarray(im).astype(np.float32)
            yy, xx = np.mgrid[0:bh, 0:bw]
            k = np.clip((14 - yy) / 14.0, 0, 1) * 0.55
            dm = ((xx + yy) % 2 == 0)
            k = np.where(dm, k, k * 0.6)
            a = a * (1 - k[..., None]) + np.array((60, 40, 80), np.float32) * k[..., None]
            im = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGB")
        return scale_nearest(im, 2)
    return cached(("eyes", bool(serious)), mk)


# ======================================================================= egg insert (dark-matter close-up)
EGG_BIG_ART = """
.........oooooooo.........
......oooKKKhhKKKooo......
....ooKKhhhkKKKKKKKKoo....
...oKKhhKKKKKKpKKKKkKKo...
..oKKkhKKKKKKKKKKKKKKKKo..
.oKKKKKKKpKKKKKkKKKKKpKKo.
.oKhKKKKKKKKKKKKKKKKKKKKo.
oKKkKKKKKKKKKKKKpKKKKKKKKo
oKKKKKKKKkKKKKKKKKKKKkKKKo
oKKKKKKKKKKKKKKKKKKKKKKKKo
.oKKKpKKKKKKKKKKKKKKKKKKo.
..ooKKKKKKKkKKKKKKKpKKoo..
....ooooKKKKKKKKKKoooo....
........oooooooooo........
"""
EGG_BIG_PAL = {"o": INK, "K": (30, 22, 36), "k": (70, 52, 84), "h": (104, 88, 118), "p": (170, 80, 214)}

SKULL_ART = """
..ooooo..
.oWWWWWo.
oWWWWWWWo
oWooWooWo
oWooWooWo
oWWWoWWWo
.oWWWWWo.
..oWoWo..
...ooo...
"""
SKULL_PAL = {"o": (70, 30, 90), "W": (214, 186, 236)}


def egg_big():
    return cached("egg_big", lambda: scale_nearest(ascii_sprite(EGG_BIG_ART, EGG_BIG_PAL), 3))


def skull():
    return cached("skull", lambda: scale_nearest(ascii_sprite(SKULL_ART, SKULL_PAL), 2))


PLATE_C = (192, 146)


def egg_insert_bg():
    """Static backdrop for the egg insert: banded dark-purple radial glow + plate (RGB)."""
    def mk():
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.hypot((xx - 192) / 1.3, yy - 120) / 190.0
        dm = ((xx + yy) % 2).astype(np.float32) * 0.06
        band = np.clip(np.floor((1 - r + dm) * 6) / 6, 0, 1)
        c0, c1 = np.array((20, 8, 28), np.float32), np.array((96, 44, 116), np.float32)
        a = c0 + (c1 - c0) * band[..., None]
        im = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGB")
        d = ImageDraw.Draw(im)
        cx, cy = PLATE_C
        d.ellipse([cx - 82, cy - 16, cx + 82, cy + 20], fill=(12, 6, 18))                 # shadow
        d.ellipse([cx - 80, cy - 22, cx + 80, cy + 16], fill=(236, 236, 246), outline=INK)
        d.ellipse([cx - 62, cy - 15, cx + 62, cy + 9], fill=(214, 216, 232))
        d.arc([cx - 74, cy - 19, cx + 74, cy + 13], 200, 340, fill=(120, 150, 210))
        d.arc([cx - 70, cy - 18, cx + 70, cy + 12], 20, 160, fill=(120, 150, 210))
        return im
    return cached("egg_insert_bg", mk)
