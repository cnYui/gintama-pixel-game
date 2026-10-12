"""Private backgrounds for s09 吉原炎上篇 (underground Yoshiwara).

Everything is drawn once in DAY colours (+ an emissive layer for lit
lattices / lanterns / lamps) and graded with bg.common so the look matches the
shared library:  'night'  = blue-purple + warm lanterns (the eternal night of
Yoshiwara),  'sun' = warm golden daylight after the iron lid opens.
All layers are cached at module level; per-frame work is just pastes.

Street world: screen x = world x - cam_x ; screen y = world y + tilt.
  world y  -210..40  iron ceiling (hatch at world y -170..-70, x 87..297)
  world y    30..152 far district + central tower (parallax 0.35)
  world y    32..152 street facades (parallax 1.0)
  world y   152..    flagstone street (feet line FLOOR = 160)
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import W, H, rng, clamp, lerp, wave, step_frame
from engine.gfx import INK, shade, mix
from engine.text import draw_text
from bg import common as C

FLOOR = 160
_CACHE = {}


def cached(key, fn):
    v = _CACHE.get(key)
    if v is None:
        v = fn()
        _CACHE[key] = v
    return v


# ----------------------------------------------------------------- grading
def sun_grade(im, depth=0.0):
    """Warm golden daylight grade (for after the lid opens)."""
    g = C.grade_rgba(im, "day", depth)
    a = np.asarray(g).astype(np.float32)
    a[..., :3] = a[..., :3] * np.array([1.06, 1.0, 0.86], np.float32) + np.array([16, 10, 0], np.float32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def graded(key, build, mode, depth=0.0, glow_radius=3, glow_strength=0.55):
    """(base, emis) = build() cached; returns the RGBA layer graded for mode
    'night' | 'sun' | 'night_in'."""
    base, emis = cached(("raw",) + key, build)

    def mk():
        if mode == "sun":
            g = sun_grade(base, depth)
            return C.light_up(g, emis, 0.22, glow_radius=glow_radius, glow_strength=0.2)
        g = C.grade_rgba(base, mode, depth)
        return C.light_up(g, emis, 1.0, glow_radius=glow_radius, glow_strength=glow_strength)
    return cached(("graded",) + key + (mode, depth), mk)


def blit(img, layer, x, y):
    img.paste(layer, (int(math.floor(x)), int(math.floor(y))), layer)


# ----------------------------------------------------------------- palette (day colours)
STEEL = (104, 108, 124)
STEEL_L = (136, 140, 156)
STEEL_D = (70, 72, 88)
STEEL_DD = (48, 50, 62)
RUST = (130, 92, 74)
TILE_M = (92, 96, 114)
TILE_L = (128, 132, 150)
TILE_D = (62, 64, 80)
WOOD = (122, 80, 60)
WOOD_D = (88, 56, 46)
WOOD_L = (158, 108, 80)
LAC = (196, 54, 50)        # red lacquer
LAC_D = (140, 34, 40)
LAC_L = (232, 104, 88)
GOLD = (236, 190, 84)
GOLD_D = (176, 130, 52)
PAPER = (236, 226, 200)
GLOWC = (255, 196, 118)
GLOWR = (255, 150, 96)
INDIGO = (58, 66, 128)
PLASTER = (214, 204, 184)


def _hline(d, x0, x1, y, c):
    d.line([(x0, y), (x1, y)], fill=c)


def _vline(d, x, y0, y1, c):
    d.line([(x, y0), (x, y1)], fill=c)


# ================================================================== iron ceiling
CEIL_W, CEIL_H = 640, 250
CEIL_OX, CEIL_OY = 128, 210          # layer (x, y) = world (x + OX, y + OY)
HATCH = (CEIL_OX + 87, 40, 210, 100)  # layer rect (x, y, w, h) of the opening
HATCH_WORLD = (87, -170, 210, 100)


def _rivets(d, x0, x1, y, step=7, hi=STEEL_L, lo=STEEL_DD):
    for x in range(x0, x1, step):
        d.point((x, y), fill=hi)
        d.point((x, y + 1), fill=lo)


def _build_ceiling():
    w, h = CEIL_W, CEIL_H
    im = Image.new("RGBA", (w, h), STEEL + (255,))
    em = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d, e = ImageDraw.Draw(im), ImageDraw.Draw(em)
    r = rng("s09", "ceil")
    # riveted plates (brick bond)
    for j, y in enumerate(range(0, 244, 26)):
        off = 0 if j % 2 == 0 else 26
        for x in range(-52 + off, w, 52):
            # plate shading: lighter top-left, darker bottom
            d.rectangle([x + 1, y + 1, x + 51, y + 3], fill=STEEL_L)
            d.rectangle([x + 1, y + 20, x + 51, y + 25], fill=shade(STEEL, 0.9))
            _vline(d, x, y, y + 25, STEEL_DD)
            _vline(d, x + 1, y + 1, y + 25, shade(STEEL_L, 0.95))
            for yy in range(y + 5, y + 24, 6):
                d.point((x + 3, yy), fill=STEEL_L)
                d.point((x + 3, yy + 1), fill=STEEL_DD)
        _hline(d, 0, w, y, STEEL_DD)
        _rivets(d, 2, w, y + 2, 7)
    # rust streaks + grime
    for i in range(60):
        x = r.randrange(w)
        y = r.randrange(0, 230)
        L = r.randrange(4, 16)
        c = RUST if i % 3 else shade(STEEL, 0.78)
        for k in range(L):
            if (k + x) % 2 == 0 or k < 3:
                d.point((x, y + k), fill=c)
    # radial heavy ribs (big I-beams) running to the hatch
    hx, hy, hw, hh = HATCH
    cx, cy = hx + hw // 2, hy + hh // 2
    for ang in (-160, -130, -50, -20, 20, 50, 130, 160, 90, -90):
        a = math.radians(ang)
        x0, y0 = cx + math.cos(a) * 118, cy + math.sin(a) * 62
        x1, y1 = cx + math.cos(a) * 520, cy + math.sin(a) * 300
        d.line([(x0, y0), (x1, y1)], fill=STEEL_DD, width=9)
        d.line([(x0, y0), (x1, y1)], fill=STEEL_D, width=7)
        d.line([(x0, y0 - 2), (x1, y1 - 2)], fill=STEEL_L, width=1)
    # hatch frame: a thick riveted ring around the opening
    d.rectangle([hx - 12, hy - 10, hx + hw + 11, hy + hh + 9], fill=STEEL_DD)
    d.rectangle([hx - 10, hy - 8, hx + hw + 9, hy + hh + 7], fill=STEEL_D)
    d.rectangle([hx - 10, hy - 8, hx + hw + 9, hy - 6], fill=STEEL_L)
    _rivets(d, hx - 8, hx + hw + 8, hy - 4, 6)
    _rivets(d, hx - 8, hx + hw + 8, hy + hh + 3, 6)
    for yy in range(hy - 2, hy + hh + 2, 6):
        d.point((hx - 6, yy), fill=STEEL_L)
        d.point((hx + hw + 5, yy), fill=STEEL_L)
    # hazard teeth on the frame lip
    for x in range(hx - 8, hx + hw + 8, 8):
        d.polygon([(x, hy - 1), (x + 4, hy - 1), (x + 2, hy - 4)], fill=(170, 150, 70))
    # the opening itself (sky shows through when the leaves slide)
    d.rectangle([hx, hy, hx + hw - 1, hy + hh - 1], fill=(0, 0, 0, 0))
    # bottom truss girder (visible at the top of the street view)
    ty0, ty1 = 206, 238
    d.rectangle([0, ty0, w, ty0 + 5], fill=STEEL_DD)
    d.rectangle([0, ty0 + 1, w, ty0 + 3], fill=STEEL_D)
    _hline(d, 0, w, ty0 + 1, STEEL_L)
    d.rectangle([0, ty1, w, ty1 + 5], fill=STEEL_DD)
    d.rectangle([0, ty1 + 1, w, ty1 + 3], fill=STEEL_D)
    _hline(d, 0, w, ty1 + 1, STEEL_L)
    for x in range(0, w, 32):
        d.line([(x, ty0 + 5), (x + 16, ty1)], fill=STEEL_DD, width=3)
        d.line([(x + 16, ty1), (x + 32, ty0 + 5)], fill=STEEL_DD, width=3)
        d.line([(x + 1, ty0 + 5), (x + 16, ty1 - 1)], fill=STEEL_D, width=1)
        _vline(d, x, ty0 + 5, ty1, STEEL_DD)
        _rivets(d, x + 2, x + 30, ty0 + 3, 5)
    # transparent below the truss, except hanging lamps + chains
    d.rectangle([0, ty1 + 6, w, h], fill=(0, 0, 0, 0))
    for i, x in enumerate(range(24, w, 72)):
        L = 4 + (i * 5) % 7
        _vline(d, x, ty1 + 6, ty1 + 6 + L, STEEL_DD)
        yb = ty1 + 6 + L
        d.polygon([(x - 5, yb + 4), (x + 5, yb + 4), (x + 2, yb), (x - 2, yb)], fill=STEEL_DD)
        d.rectangle([x - 2, yb + 4, x + 2, yb + 5], fill=(250, 230, 170))
        e.rectangle([x - 2, yb + 4, x + 2, yb + 6], fill=(255, 220, 150, 255))
    return im, em


def ceiling_layer(mode):
    return graded(("ceil",), _build_ceiling, mode, glow_radius=4, glow_strength=0.7)


def _build_leaf(side):
    """One sliding leaf of the lid (day colours). side -1 left, +1 right."""
    hx, hy, hw, hh = HATCH
    lw = hw // 2
    im = Image.new("RGBA", (lw + 2, hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, lw + 1, hh - 1], fill=STEEL_D)
    for x in range(3, lw, 12):
        d.rectangle([x, 2, x + 7, hh - 3], fill=STEEL)
        _vline(d, x, 2, hh - 3, STEEL_L)
        _vline(d, x + 7, 2, hh - 3, STEEL_DD)
    _hline(d, 0, lw + 1, 0, STEEL_L)
    _hline(d, 0, lw + 1, hh - 1, STEEL_DD)
    _hline(d, 0, lw + 1, hh // 2, STEEL_DD)
    _rivets(d, 2, lw, hh // 2 + 1, 5)
    # half of a faded red crest (sun disc) split across the seam
    seam = lw + 1 if side < 0 else 0
    d.ellipse([seam - 22, hh // 2 - 22, seam + 22, hh // 2 + 22], outline=(150, 60, 56), width=3)
    d.ellipse([seam - 13, hh // 2 - 13, seam + 13, hh // 2 + 13], fill=(150, 60, 56))
    _vline(d, seam, 0, hh - 1, STEEL_DD)
    return im, Image.new("RGBA", im.size, (0, 0, 0, 0))


def leaf(side, mode):
    return graded(("leaf", side), lambda: _build_leaf(side), mode)


# ================================================================== central tower
def _roof_tier(d, cx, y_ridge, y_eave, half_top, half_eave, lift=5):
    """Upturned-eave pagoda roof (front view)."""
    pts = [(cx - half_top, y_ridge), (cx + half_top, y_ridge),
           (cx + half_eave - 4, y_eave - 1), (cx + half_eave + 2, y_eave - lift),
           (cx + half_eave + 1, y_eave + 2), (cx - half_eave - 1, y_eave + 2),
           (cx - half_eave - 2, y_eave - lift), (cx - half_eave + 4, y_eave - 1)]
    d.polygon(pts, fill=TILE_M, outline=INK)
    hgt = y_eave - y_ridge
    for k in range(1, hgt, 3):
        f = k / max(1, hgt)
        xa = cx - lerp(half_top, half_eave - 3, f)
        xb = cx + lerp(half_top, half_eave - 3, f)
        _hline(d, xa + 1, xb - 1, y_ridge + k, TILE_D)
        if k % 6 == 1:
            _hline(d, xa + 2, xb - 2, y_ridge + k + 1, TILE_L)
    _hline(d, cx - half_eave, cx + half_eave, y_eave + 1, GOLD_D)
    _hline(d, cx - half_eave + 1, cx + half_eave - 1, y_eave, GOLD)
    d.rectangle([cx - half_top - 1, y_ridge - 3, cx + half_top + 1, y_ridge], fill=TILE_D, outline=INK)


def _lit_windows(d, e, x0, x1, y0, y1, n, lit=True):
    wv = (x1 - x0) / n
    for i in range(n):
        a = int(x0 + i * wv + 2)
        b = int(x0 + (i + 1) * wv - 2)
        d.rectangle([a, y0, b, y1], fill=LAC_D)
        d.rectangle([a + 1, y0 + 1, b - 1, y1 - 1], fill=PAPER)
        if lit:
            e.rectangle([a + 1, y0 + 1, b - 1, y1 - 1], fill=GLOWC + (255,))
        for x in range(a + 3, b - 1, 3):
            _vline(d, x, y0 + 1, y1 - 1, LAC_D)
            _vline(e, x, y0 + 1, y1 - 1, (150, 60, 40, 255))
        _hline(d, a + 1, b - 1, (y0 + y1) // 2, LAC_D)
        _hline(e, a + 1, b - 1, (y0 + y1) // 2, (150, 60, 40, 255))


def _railing(d, x0, x1, y):
    d.rectangle([x0, y, x1, y + 2], fill=LAC)
    _hline(d, x0, x1, y, LAC_L)
    _hline(d, x0, x1, y + 3, INK)
    for x in range(x0 + 2, x1, 5):
        _vline(d, x, y + 3, y + 7, LAC_D)
    _hline(d, x0, x1, y + 7, LAC_D)


TOWER_W, TOWER_H = 190, 470
TOWER_WIN = (95, 70, 19)     # round window centre + radius (in tower sprite coords)


def _build_tower():
    w, h = TOWER_W, TOWER_H
    cx = w // 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    em = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d, e = ImageDraw.Draw(im), ImageDraw.Draw(em)
    # stone base (ishigaki)
    by0 = 410
    d.polygon([(cx - 62, by0), (cx + 62, by0), (cx + 80, h - 1), (cx - 80, h - 1)], fill=(150, 146, 140), outline=INK)
    r = rng("s09", "stones")
    for y in range(by0 + 3, h - 1, 7):
        f = (y - by0) / (h - by0)
        half = lerp(62, 80, f)
        x = cx - half + (r.randrange(0, 9))
        while x < cx + half - 4:
            L = r.randrange(9, 17)
            d.rectangle([x, y, min(cx + half - 2, x + L), y + 5], fill=(170, 166, 158))
            _hline(d, x, min(cx + half - 2, x + L), y + 5, (110, 106, 104))
            x += L + 2
    # tiers: (wall top, wall bottom, half width)
    tiers = [(350, 410, 64), (282, 340, 56), (214, 272, 48), (150, 204, 42), (58, 140, 36)]
    roofs = [(332, 352, 50, 80), (264, 284, 44, 70), (196, 216, 38, 62), (132, 152, 32, 56), (20, 60, 16, 56)]
    for i, (y0, y1, hw) in enumerate(tiers):
        d.rectangle([cx - hw, y0, cx + hw, y1], fill=WOOD, outline=INK)
        # posts
        for x in range(cx - hw, cx + hw + 1, 16):
            d.rectangle([x, y0, x + 2, y1], fill=LAC_D)
            _vline(d, x, y0, y1, LAC)
        _hline(d, cx - hw, cx + hw, y0 + 2, WOOD_D)
        if i < 4:
            _lit_windows(d, e, cx - hw + 4, cx + hw - 4, y0 + 8, y1 - 14, max(3, hw // 12))
            _railing(d, cx - hw - 6, cx + hw + 6, y1 - 9)
        # hanging lanterns at the corners
        for sx in (-1, 1):
            lx = cx + sx * (hw + 10)
            ly = y0 - 2
            _vline(d, lx, ly - 4, ly, INK)
            d.ellipse([lx - 3, ly, lx + 3, ly + 8], fill=LAC, outline=INK)
            e.ellipse([lx - 2, ly + 1, lx + 2, ly + 7], fill=GLOWR + (255,))
    # top tier: round window (maru-mado) with a warm room
    wx, wy, wr = TOWER_WIN
    d.rectangle([cx - 36, 74, cx + 36, 140], fill=WOOD, outline=INK)
    _railing(d, cx - 44, cx + 44, 128)
    d.ellipse([wx - wr - 3, wy - wr - 3, wx + wr + 3, wy + wr + 3], fill=INK)
    d.ellipse([wx - wr, wy - wr, wx + wr, wy + wr], fill=(236, 200, 150))
    e.ellipse([wx - wr, wy - wr, wx + wr, wy + wr], fill=(255, 206, 140, 255))
    # side lattice panels
    for sx in (-1, 1):
        a = cx + sx * 26
        _lit_windows(d, e, min(a, a + sx * 8) - 2, max(a, a + sx * 8) + 2, 84, 112, 1)
    for i, (ry, ey, ht, he) in enumerate(roofs):
        _roof_tier(d, cx, ry, ey, ht, he, lift=6 if i == 4 else 5)
    # top roof: gable face + golden phoenix finial
    d.polygon([(cx - 14, 20), (cx, 6), (cx + 14, 20)], fill=GOLD_D, outline=INK)
    d.polygon([(cx - 9, 19), (cx, 11), (cx + 9, 19)], fill=LAC_D)
    for sx in (-1, 1):
        fx = cx + sx * 16
        d.polygon([(fx, 18), (fx + sx * 5, 8), (fx + sx * 2, 12), (fx + sx * 1, 4)], fill=GOLD, outline=INK)
    return im, em


def tower(mode):
    return graded(("tower",), _build_tower, mode, glow_radius=4, glow_strength=0.6)


def _build_window_ring():
    wx, wy, wr = TOWER_WIN
    s = 2 * wr + 12
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = s // 2
    d.ellipse([c - wr - 4, c - wr - 4, c + wr + 4, c + wr + 4], outline=INK, width=2)
    d.ellipse([c - wr - 2, c - wr - 2, c + wr + 2, c + wr + 2], outline=LAC, width=2)
    d.arc([c - wr - 3, c - wr - 3, c + wr + 3, c + wr + 3], 180, 280, fill=LAC_L)
    # rolled-up bamboo blind (sudare) at the top
    d.rectangle([c - wr + 3, c - wr + 2, c + wr - 3, c - wr + 6], fill=(188, 160, 100))
    for x in range(c - wr + 4, c + wr - 3, 3):
        _vline(d, x, c - wr + 2, c - wr + 6, (140, 112, 66))
    _hline(d, c - wr + 3, c + wr - 3, c - wr + 7, INK)
    # tassels
    for sx in (-8, 8):
        _vline(d, c + sx, c - wr + 7, c - wr + 13, LAC)
        d.point((c + sx, c - wr + 14), fill=GOLD)
    return im, Image.new("RGBA", im.size, (0, 0, 0, 0))


def window_ring(mode):
    return graded(("wring",), _build_window_ring, mode)


# ================================================================== far district
FAR_W, FAR_H = 760, 150
FAR_OX, FAR_WY = 190, 10       # screen x = layer x - FAR_OX - cam_x*0.35 ; top at world y 10
TOWER_FAR_X = 262              # screen x of the far tower at cam_x = 0


def _far_tower(d, e, cx, base):
    tiers = [(base - 34, 30), (base - 60, 25), (base - 84, 21), (base - 106, 17), (base - 128, 14)]
    prev = base
    for i, (y0, hw) in enumerate(tiers):
        d.rectangle([cx - hw, y0, cx + hw, prev], fill=(128, 78, 66))
        for xx in range(cx - hw + 3, cx + hw - 3, 6):
            d.rectangle([xx, y0 + 7, xx + 3, y0 + 14], fill=(200, 120, 90))
            e.rectangle([xx, y0 + 7, xx + 3, y0 + 14], fill=(255, 190, 120, 255))
        _hline(d, cx - hw - 3, cx + hw + 3, y0 + 18, LAC)
        ew = hw + 10
        d.polygon([(cx - ew, y0 + 2), (cx - ew - 3, y0 - 3), (cx - hw + 4, y0 - 9),
                   (cx + hw - 4, y0 - 9), (cx + ew + 3, y0 - 3), (cx + ew, y0 + 2)], fill=TILE_D)
        _hline(d, cx - ew, cx + ew, y0 + 2, GOLD_D)
        for sx in (-1, 1):
            e.rectangle([cx + sx * ew - 1, y0 + 3, cx + sx * ew + 1, y0 + 6], fill=(255, 120, 90, 255))
            d.rectangle([cx + sx * ew - 1, y0 + 3, cx + sx * ew + 1, y0 + 6], fill=LAC)
        prev = y0
    top = tiers[-1][0]
    d.polygon([(cx - 6, top - 8), (cx, top - 18), (cx + 6, top - 8)], fill=GOLD_D)
    e.ellipse([cx - 5, top + 5, cx + 5, top + 14], fill=(255, 214, 150, 255))   # Hinowa's window


def _build_far():
    w, h = FAR_W, FAR_H
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    em = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d, e = ImageDraw.Draw(im), ImageDraw.Draw(em)
    r = rng("s09", "far")
    x = -10
    while x < w:
        bw = r.randrange(30, 64)
        top = r.randrange(40, 86)
        d.rectangle([x, top, x + bw, h], fill=(112, 88, 96))
        d.polygon([(x - 5, top + 1), (x + 7, top - 9), (x + bw - 7, top - 9), (x + bw + 5, top + 1)], fill=TILE_D)
        _hline(d, x - 5, x + bw + 5, top + 1, TILE_M)
        for yy in range(top + 6, h - 8, 11):
            for xx in range(x + 4, x + bw - 6, 8):
                if r.random() < 0.55:
                    e.rectangle([xx, yy, xx + 4, yy + 4], fill=(255, 170, 110, 255))
                    d.rectangle([xx, yy, xx + 4, yy + 4], fill=(200, 120, 90))
        for xx in range(x + 3, x + bw, 6):
            if r.random() < 0.5:
                e.point((xx, top + 3), fill=(255, 120, 90, 255))
        x += bw + r.randrange(-6, 4)
    _far_tower(d, e, FAR_OX + TOWER_FAR_X, h)
    return im, em


def far_layer(mode):
    return graded(("far",), _build_far, mode, depth=0.42, glow_radius=3, glow_strength=0.75)


# ================================================================== street facades
MID_W, MID_H = 1100, 124
MID_OX, MID_WY = 260, 32
_SIGNS = ["花", "楼", "月", "夜", "蝶", "华", "屋", "酒", "吉", "梦"]


def _big_lantern(d, e, x, y, col=LAC):
    _vline(d, x, y - 3, y, INK)
    d.rectangle([x - 4, y, x + 4, y + 1], fill=INK)
    d.ellipse([x - 5, y + 1, x + 5, y + 13], fill=col, outline=INK)
    e.ellipse([x - 4, y + 2, x + 4, y + 12], fill=(255, 150, 100, 255))
    for yy in (y + 4, y + 7, y + 10):
        _hline(e, x - 3, x + 3, yy, (200, 80, 60, 255))
    d.rectangle([x - 3, y + 13, x + 3, y + 14], fill=INK)


def _facade(d, e, im, x0, bw, stories, seed):
    r = rng("s09", "fac", seed)
    base = MID_H - 4            # layer y of the street edge (world 152)
    sh = 30
    top = base - sh * stories - 4
    ry = top - 16
    ew = 9
    d.polygon([(x0 - ew, top + 2), (x0 - ew - 3, top - 3), (x0 + 10, ry), (x0 + bw - 10, ry),
               (x0 + bw + ew + 3, top - 3), (x0 + bw + ew, top + 2)], fill=TILE_M, outline=INK)
    for k in range(3, 17, 3):
        _hline(d, x0 - ew + k * 1.1, x0 + bw + ew - k * 1.1, top + 2 - k, TILE_D)
    _hline(d, x0 - ew, x0 + bw + ew, top + 1, TILE_L)
    _hline(d, x0 - ew, x0 + bw + ew, top + 2, GOLD_D)
    d.rectangle([x0 + 8, ry - 3, x0 + bw - 8, ry], fill=TILE_D, outline=INK)
    if r.random() < 0.5:      # gable crest
        gx = x0 + bw // 2
        d.polygon([(gx - 12, top - 1), (gx, top - 12), (gx + 12, top - 1)], fill=WOOD_D, outline=INK)
        d.polygon([(gx - 7, top - 2), (gx, top - 8), (gx + 7, top - 2)], fill=GOLD_D)
    for s in range(stories):
        y1 = base - s * sh
        y0 = y1 - sh + 3
        d.rectangle([x0, y0, x0 + bw, y1], fill=WOOD, outline=INK)
        for x in range(x0 + 1, x0 + bw, 3):
            _vline(d, x, y0 + 1, y1 - 1, WOOD_D if (x // 3) % 2 else WOOD)
        d.rectangle([x0, y0, x0 + 3, y1], fill=LAC_D)
        d.rectangle([x0 + bw - 3, y0, x0 + bw, y1], fill=LAC_D)
        if s == 0:
            door_w = 22
            side = r.random() < 0.5
            dx0 = x0 + 6 if side else x0 + bw - 6 - door_w
            lx0, lx1 = (dx0 + door_w + 4, x0 + bw - 6) if side else (x0 + 6, dx0 - 4)
            ly0, ly1 = y0 + 7, y1 - 2
            d.rectangle([lx0, ly0, lx1, ly1], fill=(190, 150, 110))
            e.rectangle([lx0, ly0, lx1, ly1], fill=GLOWC + (255,))
            for sx in range(lx0 + 8, lx1 - 6, 15):
                if r.random() < 0.65:
                    kc = [(150, 60, 70), (120, 70, 140), (60, 110, 140)][r.randrange(3)]
                    d.ellipse([sx - 3, ly1 - 17, sx + 3, ly1 - 11], fill=(70, 50, 60))
                    d.rectangle([sx - 5, ly1 - 11, sx + 5, ly1], fill=kc)
                    e.ellipse([sx - 3, ly1 - 17, sx + 3, ly1 - 11], fill=(90, 60, 70, 255))
                    e.rectangle([sx - 5, ly1 - 11, sx + 5, ly1], fill=kc + (255,))
            for x in range(lx0, lx1 + 1, 3):
                _vline(d, x, ly0, ly1, LAC)
                _vline(e, x, ly0, ly1, (120, 36, 36, 255))
            for y in (ly0, ly0 + 9, ly1):
                _hline(d, lx0, lx1, y, LAC_D)
                _hline(e, lx0, lx1, y, (110, 30, 34, 255))
            d.rectangle([dx0, y0 + 5, dx0 + door_w, y1], fill=(40, 30, 34))
            e.rectangle([dx0 + 2, y0 + 14, dx0 + door_w - 2, y1], fill=(200, 120, 70, 200))
            ncol = INDIGO if r.random() < 0.5 else (150, 40, 60)
            for k in range(3):
                nx = dx0 + 1 + k * 7
                d.rectangle([nx, y0 + 5, nx + 6, y0 + 16], fill=ncol, outline=INK)
            d.ellipse([dx0 + door_w // 2 - 3, y0 + 8, dx0 + door_w // 2 + 3, y0 + 13], fill=PAPER)
            d.polygon([(x0 - 6, y0 + 1), (x0 + bw + 6, y0 + 1), (x0 + bw + 2, y0 - 5), (x0 - 2, y0 - 5)],
                      fill=TILE_M, outline=INK)
            _hline(d, x0 - 5, x0 + bw + 5, y0, TILE_L)
            for lx in (x0 + 8, x0 + bw - 8):
                _big_lantern(d, e, lx, y0 + 2)
        else:
            n = max(2, bw // 22)
            _lit_windows(d, e, x0 + 5, x0 + bw - 5, y0 + 5, y1 - 10, n, lit=r.random() < 0.92)
            _railing(d, x0 - 2, x0 + bw + 2, y1 - 8)
            if s < stories - 1:
                d.polygon([(x0 - 5, y0 + 1), (x0 + bw + 5, y0 + 1), (x0 + bw + 2, y0 - 3), (x0 - 2, y0 - 3)],
                          fill=TILE_M, outline=INK)
    if r.random() < 0.85:
        sx = x0 + (5 if r.random() < 0.5 else bw - 15)
        sy = base - sh * stories + 6
        d.rectangle([sx, sy, sx + 10, sy + 26], fill=PAPER, outline=INK)
        e.rectangle([sx + 1, sy + 1, sx + 9, sy + 25], fill=(255, 236, 200, 150))
        ch = _SIGNS[seed % len(_SIGNS)]
        draw_text(im, sx + 6, sy + 13, ch, (40, 20, 20), size=12, anchor="mm")


def _build_mid():
    w, h = MID_W, MID_H
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    em = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d, e = ImageDraw.Draw(im), ImageDraw.Draw(em)
    r = rng("s09", "mid")
    x = 0
    i = 0
    pattern = [2, 3, 2, 2, 3, 2, 3, 2, 2, 3, 2, 2]
    while x < w:
        bw = r.randrange(80, 118)
        _facade(d, e, im, x, bw, pattern[i % len(pattern)], i)
        x += bw + (r.randrange(8, 20) if r.random() < 0.35 else 4)
        i += 1
    return im, em


def mid_layer(mode):
    return graded(("mid",), _build_mid, mode, glow_radius=3, glow_strength=0.6)


# ================================================================== haze / backdrop
def _build_backdrop(mode):
    """Opaque 384 x 400 backdrop behind everything (fog between ceiling and city)."""
    if mode == "sun":
        stops = [(0.0, (120, 110, 110)), (0.4, (236, 214, 170)), (1.0, (250, 232, 190))]
    else:
        stops = [(0.0, (14, 12, 26)), (0.4, (40, 26, 52)), (0.7, (96, 44, 60)), (1.0, (120, 56, 64))]
    arr = C.vgradient(BACK_H, W, stops, bands=10)
    return Image.fromarray(arr, "RGB")


BACK_H, BACK_WY = 220, -60


def backdrop(mode):
    return cached(("backdrop", mode), lambda: _build_backdrop(mode))


# ================================================================== street composite
_LANT_COLS = (C.RED, C.RED, C.PINK, C.YELLOW)


def lantern_string(img, t, cam_x, tilt, y, mode, par=1.25, seed=0, spacing=26, sag=10, offset=0):
    """A sagging wire of chochin across the street (foreground)."""
    tod = "night" if mode != "sun" else "day"
    period = 300
    ox = -(cam_x * par) + offset
    d = ImageDraw.Draw(img)
    wire = (30, 24, 34) if mode != "sun" else (70, 54, 50)
    base = -((int(ox) // period) + 1) * period
    for k in range(3):
        x0 = ox + base + k * period
        if x0 > W or x0 + period < 0:
            continue
        pts = [(x0 + i * 10, y + tilt + sag * math.sin(math.pi * i * 10 / period)) for i in range(period // 10 + 1)]
        d.line(pts, fill=wire)
        n = period // spacing
        for i in range(1, n):
            xx = x0 + i * spacing
            yy = y + tilt + sag * math.sin(math.pi * i * spacing / period)
            if -10 < xx < W + 10 and -20 < yy < H:
                col = _LANT_COLS[(i + seed) % len(_LANT_COLS)]
                C.lantern(img, int(xx), int(yy), t, color=col, tod=tod, swing=0.8)




def _build_spill():
    h = 26
    yy = np.arange(h, dtype=np.float32)[:, None]
    f = np.clip(1 - yy / h, 0, 1) ** 1.5
    q = np.floor(f * 4 + C.bayer(h, W) * 0.999) / 4
    col = np.array([84, 40, 14], np.float32)
    arr = (q[..., None] * col[None, None, :]).astype(np.uint8)
    return Image.fromarray(np.ascontiguousarray(arr), "RGB")


def street(img, cam_x, t, tilt=0, mode="night", leaves_open=0.0, lanterns=True):
    """Full Yoshiwara street view (no characters). tilt > 0 raises the camera
    toward the iron ceiling."""
    bd = backdrop(mode)
    img.paste(bd, (0, int(BACK_WY + tilt)))
    ceil = ceiling_layer(mode)
    cx = -CEIL_OX - cam_x * 0.5
    cy = -CEIL_OY + tilt
    if cy + CEIL_H > 0:
        if HATCH[1] + HATCH[3] + cy > 0:
            _hatch_contents(img, cx, cy, mode, leaves_open, t)
        blit(img, ceil, cx, cy)
    far = far_layer(mode)
    blit(img, far, -FAR_OX - cam_x * 0.35, FAR_WY + tilt)
    mid = mid_layer(mode)
    blit(img, mid, -MID_OX - cam_x, MID_WY + tilt)
    if 152 + tilt < H:
        C.stone_street(img, int(152 + tilt), cam_x, "night" if mode != "sun" else "day", h=64)
        if mode != "sun":
            C.add_sprite(img, cached(("spill",), _build_spill), 0, int(152 + tilt))
    if lanterns:
        lantern_string(img, t, cam_x, tilt, 58, mode, par=1.0, seed=1, spacing=22, sag=8, offset=40)


def _build_hatch_sky():
    hx, hy, hw, hh = HATCH
    arr = C.vgradient(hh, hw, [(0, (60, 130, 226)), (0.55, (140, 196, 248)), (1, (236, 246, 255))], bands=8)
    cx, cy = hw // 2, hh // 2 + 4
    yy, xx = np.mgrid[0:hh, 0:hw]
    dd = np.hypot(xx - cx, yy - cy)
    a = arr.astype(np.float32)
    halo = np.clip(1 - dd / 46, 0, 1) ** 1.3
    q = np.floor(halo * 4 + C.bayer(hh, hw) * 0.999) / 4
    a = a * (1 - q[..., None] * 0.8) + np.array([255, 250, 220], np.float32) * q[..., None] * 0.8
    a[dd <= 11] = (255, 255, 240)
    a[(dd > 11) & (dd <= 13)] = (255, 236, 150)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


def _hatch_contents(img, cx, cy, mode, open_k, t):
    """Sky behind the lid + the two sliding leaves."""
    hx, hy, hw, hh = HATCH
    x0, y0 = int(cx + hx), int(cy + hy)
    if open_k > 0:
        img.paste(cached(("hsky",), _build_hatch_sky), (x0, y0))
    lw = hw // 2
    sl = int(round(open_k * (lw + 8)))
    L = leaf(-1, mode)
    R = leaf(1, mode)
    reg = (x0, y0, x0 + hw, y0 + hh)
    tmp = img.crop(reg)
    tmp.paste(L, (-sl, 0), L)
    tmp.paste(R, (lw - 1 + sl, 0), R)
    img.paste(tmp, reg[:2])


# ================================================================== light
def shafts(img, polys, color=(255, 238, 190)):
    """Soft light shafts: polys = [(points, alpha 0..1), ...] (alpha-blended)."""
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    for pts, a in polys:
        if a > 0.01:
            d.polygon(pts, fill=int(clamp(a) * 255))
    img.paste(tuple(color), (0, 0, W, H), mask)


def sun_shafts(img, t, k, ox=120, oy=-160, spread=(-0.05, 0.62), n=6, seed=0, alpha=0.32, length=520):
    """Diagonal god rays falling from (ox, oy) (above the frame)."""
    if k <= 0:
        return
    polys = []
    r = rng("shaft", seed)
    for i in range(n):
        base = lerp(spread[0], spread[1], (i + 0.5) / n) + r.uniform(-0.04, 0.04)
        a = math.pi / 2 - base + 0.02 * math.sin(t * 0.6 + i)
        wdt = r.uniform(0.018, 0.045)
        p1 = (ox + math.cos(a - wdt) * length, oy + math.sin(a - wdt) * length)
        p2 = (ox + math.cos(a + wdt) * length, oy + math.sin(a + wdt) * length)
        al = alpha * k * (0.7 + 0.3 * math.sin(t * 1.3 + i * 1.7))
        polys.append(([(ox, oy), p1, p2], al))
    shafts(img, polys)


def dust_motes(img, t, count=40, seed=0, area=(0, 0, W, H), color=(255, 244, 200), rise=6.0):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = area
    for i in range(count):
        r = rng("mote", seed, i)
        x = x0 + (r.uniform(0, x1 - x0) + t * r.uniform(-4, 8) + wave(t, 0.2, 5, r.random())) % (x1 - x0)
        y = y0 + (r.uniform(0, y1 - y0) - t * rise * r.uniform(0.5, 1.5)) % (y1 - y0)
        if math.sin(t * r.uniform(2, 5) + i) > -0.2:
            d.point((int(x), int(y)), fill=tuple(color))


# ================================================================== tower shot
def tower_scene(img, t, v, mode="night"):
    """Hinowa's tower. v 0 = camera at the base, 1 = at the top window.
    Returns the screen (x, y) of the round window centre."""
    ty = lerp(H - TOWER_H + 8, 14, v)
    tilt = (ty - (H - TOWER_H + 8)) * 0.45
    street(img, 190, t, tilt=tilt, mode=mode, lanterns=False)
    tw = tower(mode)
    x0 = W // 2 - TOWER_W // 2
    blit(img, tw, x0, ty)
    wx, wy, wr = TOWER_WIN
    return x0 + wx, ty + wy


# ================================================================== rooftop (Kamui)
ROOF_W, ROOF_H = 560, 90
ROOF_RIDGE = 16          # ridge (feet line) row inside the roof sprite


def _build_roof():
    w, h = ROOF_W, ROOF_H
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ry = ROOF_RIDGE
    TM, TL, TD, TH = (140, 146, 170), (182, 188, 208), (84, 88, 110), (210, 214, 230)
    d.rectangle([0, ry + 6, w, h], fill=TD)
    y = ry + 8
    ch = 3
    while y < h:
        for x in range(0, w, 8):
            d.rectangle([x + 1, y, x + 6, y + ch - 1], fill=TM)
            d.rectangle([x + 2, y, x + 3, y + ch - 2], fill=TL)
            d.point((x + 2, y), fill=TH)
            d.rectangle([x + 6, y, x + 6, y + ch - 1], fill=shade(TM, 0.8))
        _hline(d, 0, w, y + ch, shade(TD, 0.7))
        y += ch + 1
        ch = min(14, int(ch * 1.35 + 1))
    d.rectangle([0, ry, w, ry + 7], fill=TD, outline=INK)
    _hline(d, 0, w, ry + 1, TH)
    _hline(d, 0, w, ry + 2, TL)
    for x in range(2, w, 6):
        d.rectangle([x, ry + 4, x + 3, ry + 5], fill=TM)
    _hline(d, 0, w, ry + 8, INK)
    ox = 36
    d.polygon([(ox - 10, ry + 8), (ox - 12, ry - 6), (ox - 4, ry - 14), (ox + 4, ry - 14),
               (ox + 12, ry - 6), (ox + 10, ry + 8)], fill=TM, outline=INK)
    d.ellipse([ox - 5, ry - 7, ox + 5, ry + 3], fill=TD, outline=INK)
    d.point((ox - 2, ry - 3), fill=GOLD)
    d.point((ox + 2, ry - 3), fill=GOLD)
    _hline(d, ox - 9, ox + 9, ry - 12, TL)
    return im, Image.new("RGBA", (w, h), (0, 0, 0, 0))


def roof_fg(mode):
    return graded(("roof",), _build_roof, mode)


def _build_big_lantern():
    from engine.text import text_sprite
    w, h = 58, 76
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    em = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d, e = ImageDraw.Draw(im), ImageDraw.Draw(em)
    d.ellipse([2, 3, w - 3, h - 4], fill=LAC, outline=INK)
    e.ellipse([5, 6, w - 6, h - 7], fill=(255, 140, 90, 255))
    for yy in range(10, h - 8, 6):
        f = (yy - h / 2) / (h / 2)
        half = (w / 2 - 4) * math.sqrt(max(0, 1 - f * f))
        _hline(d, w / 2 - half, w / 2 + half, yy, LAC_D)
        _hline(e, w / 2 - half + 1, w / 2 + half - 1, yy, (220, 90, 60, 255))
    for i, ch in enumerate("吉原"):
        s = text_sprite(ch, (30, 16, 20), 20, "brush")
        im.paste(s, (w // 2 - s.width // 2, 10 + i * 26), s)
        dark = Image.new("RGBA", s.size, (60, 20, 20, 255))
        em.paste(dark, (w // 2 - s.width // 2, 10 + i * 26), s)
    d.rectangle([14, 0, 44, 6], fill=(40, 30, 34), outline=INK)
    d.rectangle([14, h - 7, 44, h - 1], fill=(40, 30, 34), outline=INK)
    return im, em


def big_lantern(mode):
    return graded(("biglant",), _build_big_lantern, mode, glow_radius=6, glow_strength=0.9)


def roof_scene(img, t, cam=0.0, mode="night"):
    """Kamui's rooftop: ridge (feet line) at screen y 150 (shifted by -cam*0 )."""
    street(img, 120 + cam * 0.6, t, tilt=38, mode=mode, lanterns=False)
    lantern_string(img, t, cam, 0, 44, mode, par=1.0, seed=5, spacing=20, sag=10, offset=150)
    sw = math.sin(t * 1.1) * 2
    bl = big_lantern(mode)
    lx, ly = 70 - cam * 0.8 + sw, 42
    d = ImageDraw.Draw(img)
    d.line([(lx + 29 - sw, 0), (lx + 29, ly)], fill=(20, 16, 26), width=2)
    if mode != "sun":
        g = C.glow_sprite(64, (255, 120, 70), 0.9)
        C.add_sprite(img, g, lx + 29 - 64, ly + 38 - 64)
    blit(img, bl, lx, ly)
    rf = roof_fg(mode)
    blit(img, rf, -60 - cam, 150 - ROOF_RIDGE)
    if mode != "sun":
        g = C.glow_sprite(90, (255, 110, 60), 0.6)
        C.add_sprite(img, g, lx + 29 - 90, 150 - 50)


# ================================================================== throne room (Housen)
def _build_throne():
    w, h = W, 150
    im = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    em = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 14], fill=(70, 46, 40))
    for x in range(0, w, 24):
        d.rectangle([x + 2, 2, x + 21, 11], fill=(96, 62, 50), outline=(50, 32, 30))
        d.point((x + 11, 6), fill=GOLD)
    d.rectangle([0, 14, w, 21], fill=(40, 28, 28))
    _hline(d, 0, w, 15, GOLD_D)
    x0, x1, y0, y1 = 28, w - 28, 22, h
    d.rectangle([x0, y0, x1, y1], fill=(222, 180, 84))
    for yy in range(y0, y1, 4):
        for xx in range(x0 + (yy // 4 % 2) * 4, x1, 8):
            d.rectangle([xx, yy, xx + 3, yy + 3], fill=(230, 190, 96))
    for cy_, cx_, L in ((40, 70, 90), (58, 220, 110), (112, 60, 70), (126, 250, 90), (84, 150, 70)):
        for k in range(4):
            d.ellipse([cx_ + k * L // 4 - 14, cy_ - 6, cx_ + k * L // 4 + 14, cy_ + 6], fill=(196, 150, 64))
        _hline(d, cx_ - 14, cx_ + L, cy_ + 6, (170, 124, 50))
    d.ellipse([240, 34, 312, 106], fill=(236, 232, 214), outline=(196, 150, 64))
    d.ellipse([252, 44, 300, 92], fill=(244, 240, 226))
    for bx, by, L, sgn in ((34, 60, 120, 1), (40, 100, 90, 1), (350, 54, 110, -1)):
        pts = [(bx + sgn * k * 6, by + math.sin(k * 0.9) * 4 + k * 0.6) for k in range(L // 6)]
        d.line(pts, fill=(50, 38, 36), width=4)
        for k in range(2, len(pts), 3):
            px, py = pts[k]
            d.ellipse([px - 9, py - 7, px + 9, py + 2], fill=(46, 84, 60))
            d.ellipse([px - 6, py - 7, px + 6, py - 2], fill=(70, 116, 80))
    for xx in range(x0, x1 + 1, (x1 - x0) // 6):
        d.rectangle([xx - 1, y0, xx + 1, y1], fill=(30, 22, 24))
        d.point((xx, y0 + 60), fill=GOLD)
    d.rectangle([x0 - 2, y0, x1 + 2, y0 + 2], fill=(30, 22, 24))
    for px in (6, w - 24):
        d.rectangle([px, 0, px + 18, h], fill=LAC, outline=INK)
        _vline(d, px + 3, 0, h, LAC_L)
        _vline(d, px + 14, 0, h, LAC_D)
        for yy in (20, 120):
            d.rectangle([px - 1, yy, px + 19, yy + 4], fill=GOLD_D, outline=INK)
    return im, em


def throne(img, t, light=1.0):
    """Housen's gilded audience chamber. light 0..1 (0 = pitch dark)."""
    th = graded(("throne",), _build_throne, "night_in")
    img.paste(th, (0, 0))
    C.tatami(img, 150, 0, "night_in")
    d = ImageDraw.Draw(img)
    for i, x in enumerate((64, 320)):
        fl = 0.85 + 0.15 * math.sin(t * 11 + i * 2) * math.sin(t * 7.3 + i)
        g = C.glow_sprite(26, (255, 170, 90), round(fl * light * 4) / 4)
        C.add_sprite(img, g, x - 26, 136 - 26)
        d.rectangle([x - 6, 128, x + 6, 150], fill=INK)
        d.rectangle([x - 5, 129, x + 5, 145], fill=(255, 226, 170) if light > 0.3 else (70, 50, 40))
        _hline(d, x - 5, x + 5, 137, (180, 120, 70))
        d.rectangle([x - 6, 146, x + 6, 150], fill=(60, 40, 34))
        _vline(d, x - 5, 150, 156, INK)
        _vline(d, x + 5, 150, 156, INK)
    if light < 1:
        from engine.gfx import overlay_rect
        overlay_rect(img, 0, 0, W, H, (6, 4, 10), (1 - light) * 0.92)


# ================================================================== corridor (smash)
COR_W = 1224


def _build_corridor():
    w, h = COR_W + W, 152
    im = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    em = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d, e = ImageDraw.Draw(im), ImageDraw.Draw(em)
    d.rectangle([0, 0, w, 22], fill=(64, 44, 40))
    for x in range(0, w, 30):
        _vline(d, x, 0, 22, (44, 30, 30))
    d.rectangle([0, 22, w, 29], fill=WOOD_D, outline=INK)
    _hline(d, 0, w, 23, WOOD_L)
    d.rectangle([0, 30, w, 150], fill=WOOD)
    for x in range(0, w, 72):
        for k in range(2):
            sx0 = x + 8 + k * 31
            d.rectangle([sx0, 40, sx0 + 28, 140], fill=(60, 40, 34))
            d.rectangle([sx0 + 1, 41, sx0 + 27, 139], fill=PAPER)
            e.rectangle([sx0 + 1, 41, sx0 + 27, 139], fill=(255, 200, 130, 255))
            for xx in range(sx0 + 7, sx0 + 27, 7):
                _vline(d, xx, 41, 139, (70, 48, 40))
                _vline(e, xx, 41, 139, (120, 70, 50, 255))
            for yy in range(51, 139, 12):
                _hline(d, sx0 + 1, sx0 + 27, yy, (70, 48, 40))
                _hline(e, sx0 + 1, sx0 + 27, yy, (120, 70, 50, 255))
        d.rectangle([x, 30, x + 5, 150], fill=WOOD_D, outline=INK)
        _vline(d, x + 1, 30, 150, WOOD_L)
        if (x // 72) % 2 == 0:
            _big_lantern(d, e, x + 3, 31)
    d.rectangle([0, 144, w, 151], fill=(50, 34, 32))
    return im, em


def corridor(img, cam_x, t):
    c = graded(("corridor",), _build_corridor, "night_in", glow_radius=3, glow_strength=0.5)
    o = int(cam_x) % COR_W
    img.paste(c.crop((o, 0, o + W, 152)), (0, 0))
    C.wood_floor(img, 152, cam_x, "night_in", h=64)


PART_HW = 13                 # half thickness of a partition wall (px)
PART_HOLE = (122, 25)        # hole centre y + half height once smashed


def partition(img, sx, broken, seed=0):
    """A thick timber-and-plaster partition wall (ceiling to floor) at screen x
    sx, painted with a blue wave fusuma motif. broken 0 = intact, 1 = smashed
    clean through (ragged hole around PART_HOLE, the corridor shows through)."""
    x0, x1 = int(sx) - PART_HW, int(sx) + PART_HW
    if x1 < -2 or x0 > W + 2:
        return
    lay = Image.new("RGBA", (x1 - x0 + 1, 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    w = x1 - x0
    Y = lambda y: y - 20          # screen y -> layer y
    face, face_d, face_l = (222, 208, 176), (188, 170, 138), (240, 230, 206)
    d.rectangle([0, Y(22), w, Y(156)], fill=INK)
    d.rectangle([1, Y(23), w - 1, Y(155)], fill=face)
    for yy in range(34, 150, 8):          # painted waves
        d.arc([4, Y(yy), w - 4, Y(yy + 7)], 180, 360, fill=(80, 104, 150))
        d.arc([7, Y(yy + 3), w - 7, Y(yy + 8)], 180, 360, fill=(126, 150, 190))
    d.line([(2, Y(23)), (2, Y(155))], fill=face_l)
    d.line([(w - 2, Y(23)), (w - 2, Y(155))], fill=face_d)
    for xx in (1, w - 4):                 # timber posts
        d.rectangle([xx, Y(23), xx + 3, Y(155)], fill=WOOD_D)
        d.line([(xx + 1, Y(23)), (xx + 1, Y(155))], fill=WOOD_L)
    d.rectangle([0, Y(22), w, Y(29)], fill=WOOD_D, outline=INK)
    d.line([(1, Y(23)), (w - 1, Y(23))], fill=WOOD_L)
    d.rectangle([0, Y(62), w, Y(66)], fill=WOOD, outline=INK)
    d.rectangle([0, Y(150), w, Y(156)], fill=WOOD_D, outline=INK)
    if broken > 0:
        r = rng("hole", seed)
        cy, hr = PART_HOLE
        top, bot = [], []
        n = 7
        for i in range(n + 1):
            x = w * i / n
            top.append((x, Y(cy - hr * r.uniform(0.75, 1.1))))
            bot.append((x, Y(cy + hr * r.uniform(0.7, 1.0))))
        # punch the hole out of the layer
        m = Image.new("L", lay.size, 255)
        ImageDraw.Draw(m).polygon(top + bot[::-1], fill=0)
        lay.putalpha(Image.fromarray(np.minimum(np.asarray(lay.getchannel("A")), np.asarray(m))))
        d = ImageDraw.Draw(lay)
        d.line(top, fill=INK, width=2)
        d.line(bot, fill=INK, width=2)
        # splintered laths + cracks spreading through the plaster
        for i in range(1, n, 2):
            x, y = top[i]
            d.line([(x, y), (x + r.uniform(-3, 3), y + r.uniform(4, 8))], fill=WOOD_D, width=2)
            x, y = bot[i + 1]
            d.line([(x, y), (x + r.uniform(-3, 3), y - r.uniform(3, 6))], fill=WOOD_D, width=2)
        for i in range(5):
            x, y = (top if i % 2 == 0 else bot)[r.randrange(1, n)]
            L = r.uniform(8, 18) * (-1 if i % 2 == 0 else 1)
            d.line([(x, y), (x + r.uniform(-4, 4), y + L * 0.5), (x + r.uniform(-6, 6), y + L)], fill=(90, 70, 60))
    img.paste(lay, (x0, 20), lay)


def chunks(img, t, t0, x, y, seed=0, n=14, vx=(60, 260), vy=(-150, 40), life=1.0,
           colors=((222, 208, 176), (188, 170, 138), (122, 80, 60), (80, 104, 150))):
    """Big tumbling wall chunks (quads with an ink outline) flung from (x, y)."""
    dt = t - t0
    if dt < 0 or dt > life:
        return
    d = ImageDraw.Draw(img)
    for i in range(n):
        r = rng("chunk", seed, i)
        ux, uy = r.uniform(*vx), r.uniform(*vy)
        px = x + r.uniform(-4, 4) + ux * dt
        py = y + r.uniform(-18, 18) + uy * dt + 0.5 * 420 * dt * dt
        if py > 158:
            py = 158 - abs(math.sin(dt * 9 + i)) * 2
        s = r.uniform(2, 5.5) * (1 - 0.3 * dt / life)
        a = r.uniform(0, 6.28) + dt * r.uniform(-14, 14)
        pts = [(px + math.cos(a + k * 1.7 + (0.3 if k % 2 else 0)) * s,
                py + math.sin(a + k * 1.7 + (0.3 if k % 2 else 0)) * s * 0.8) for k in range(4)]
        d.polygon(pts, fill=colors[i % len(colors)], outline=INK)


# ================================================================== control room (lever)
def _build_gear(R, teeth, col=(128, 118, 104)):
    s = 2 * R + 12
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = s / 2
    pts = []
    step = math.pi / teeth
    for i in range(teeth * 2):
        a = i * step
        rr = R + 4 if i % 2 == 0 else R - 1
        pts.append((c + math.cos(a - step * 0.35) * rr, c + math.sin(a - step * 0.35) * rr))
        pts.append((c + math.cos(a + step * 0.35) * rr, c + math.sin(a + step * 0.35) * rr))
    d.polygon(pts, fill=col, outline=INK)
    d.ellipse([c - R + 8, c - R + 8, c + R - 8, c + R - 8], fill=shade(col, 0.6), outline=INK)
    for k in range(5):
        a = k * 2 * math.pi / 5
        d.line([(c, c), (c + math.cos(a) * (R - 8), c + math.sin(a) * (R - 8))], fill=col, width=5)
    d.ellipse([c - 8, c - 8, c + 8, c + 8], fill=shade(col, 1.25), outline=INK)
    d.ellipse([c - 3, c - 3, c + 3, c + 3], fill=INK)
    return im


def gear(R, teeth, mode="night_in"):
    def mk():
        g = _build_gear(R, teeth)
        return g, Image.new("RGBA", g.size, (0, 0, 0, 0))
    return graded(("gear", R, teeth), mk, mode)


def control_room(img, t, spin, alarm=True):
    """Lid machinery: steel wall, big gears (angle `spin` deg), pipes, alarm."""
    from engine.gfx import overlay_rect, rotate_nearest
    ceil = ceiling_layer("night_in")
    img.paste((26, 20, 32), (0, 0, W, H))
    cr = ceil.crop((20, 0, 20 + W, H))
    img.paste(cr, (0, 0), cr)
    overlay_rect(img, 0, 0, W, H, (20, 12, 24), 0.3)
    d = ImageDraw.Draw(img)
    for y, c in ((30, (110, 84, 70)), (44, (96, 74, 64))):
        d.rectangle([0, y, W, y + 7], fill=c, outline=INK)
        _hline(d, 0, W, y + 1, shade(c, 1.4))
        for x in range(20, W, 90):
            d.rectangle([x, y - 2, x + 5, y + 9], fill=shade(c, 0.7), outline=INK)
    g1 = gear(46, 12)
    g2 = gear(30, 8)
    a = rotate_nearest(g1, spin, expand=False)
    b = rotate_nearest(g2, -spin * 46 / 30 + 11, expand=False)
    c3 = rotate_nearest(g2, spin * 1.3 + 5, expand=False)
    img.paste(a, (262 - a.width // 2, 98 - a.height // 2), a)
    img.paste(b, (336 - b.width // 2, 146 - b.height // 2), b)
    img.paste(c3, (44 - c3.width // 2, 92 - c3.height // 2), c3)
    d.rectangle([0, 160, W, H], fill=(34, 30, 42))
    for x in range(0, W, 6):
        _vline(d, x, 161, H, (22, 20, 30))
    _hline(d, 0, W, 160, (80, 76, 96))
    on = alarm and int(t * 6) % 2 == 0
    if on:
        g = C.glow_sprite(26, (255, 60, 40), 1.0)
        C.add_sprite(img, g, 150 - 26, 20 - 26)
    d.rectangle([144, 12, 156, 16], fill=(60, 60, 70), outline=INK)
    d.ellipse([146, 16, 154, 25], fill=(255, 90, 60) if on else (120, 40, 40), outline=INK)


def lever(img, x, y, ang, L=36, floor=None):
    """Giant lever pivoting at (x, y); ang in degrees from vertical (+ = right).
    floor: y of the floor the base block stands on (default y + 20).
    Returns the handle position."""
    d = ImageDraw.Draw(img)
    a = math.radians(ang)
    tx, ty = x + math.sin(a) * L, y - math.cos(a) * L
    fl = y + 20 if floor is None else floor
    d.rectangle([x - 18, y - 4, x + 18, fl], fill=(70, 72, 88), outline=INK)
    _hline(d, x - 17, x + 17, y - 3, (130, 134, 150))
    d.rectangle([x - 14, y + 5, x + 14, fl - 3], fill=(150, 120, 50))
    for i in range(-14, 6, 6):           # hazard stripes on the base
        d.polygon([(x + i, fl - 3), (x + i + 3, fl - 3), (x + i + 6, y + 5), (x + i + 3, y + 5)], fill=(40, 34, 40))
    d.line([(x, y), (tx, ty)], fill=INK, width=7)
    d.line([(x, y), (tx, ty)], fill=(170, 160, 150), width=4)
    d.ellipse([tx - 7, ty - 7, tx + 7, ty + 7], fill=LAC, outline=INK)
    d.ellipse([tx - 4, ty - 5, tx, ty - 1], fill=LAC_L)
    d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(200, 170, 80), outline=INK)
    return tx, ty


# ================================================================== up view (lid opens)
def up_view(img, t, open_k, sun_k, dy=0):
    """Looking straight up at the lid. open_k 0..1 slides the leaves apart,
    sun_k 0..1 regrades the ceiling toward sunlight. Returns the hatch centre."""
    hx, hy, hw, hh = HATCH
    ox = W // 2 - (hx + hw // 2)
    oy = H // 2 - (hy + hh // 2) - 6 + dy

    def comp(dst, mode):
        _hatch_contents(dst, ox, oy, mode, open_k, t)
        blit(dst, ceiling_layer(mode), ox, oy)
    comp(img, "night")
    if sun_k > 0:
        tmp = Image.new("RGB", (W, H))
        comp(tmp, "sun")
        img.paste(Image.blend(img, tmp, clamp(sun_k)))
    return ox + hx + hw // 2, oy + hy + hh // 2


def radial_rays(img, t, cx, cy, k, n=14, seed=0):
    if k <= 0:
        return
    polys = []
    r = rng("rays", seed)
    for i in range(n):
        a = i / n * 2 * math.pi + t * 0.15 + r.uniform(-0.1, 0.1)
        wdt = r.uniform(0.04, 0.09)
        L = 420
        polys.append(([(cx, cy), (cx + math.cos(a - wdt) * L, cy + math.sin(a - wdt) * L),
                       (cx + math.cos(a + wdt) * L, cy + math.sin(a + wdt) * L)],
                      k * (0.25 + 0.15 * math.sin(t * 3 + i))))
    shafts(img, polys, (255, 244, 200))
