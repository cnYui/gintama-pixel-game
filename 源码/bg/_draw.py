"""Private drawing primitives shared by the bg modules (roofs, walls, windows,
noren, signs, wrap-around layers). Everything is drawn in DAY colours into an
RGBA base layer plus an optional RGBA *emissive* layer (lit paper windows,
neon...), which bg.common.light_up composites per time of day.
Not for scene use — import bg.common / bg.kabukicho / bg.edo / bg.yorozuya.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import W, rng
from engine.gfx import shade, mix
from .common import grade_rgba, light_up, lit_amount, cached

CLEAR = (0, 0, 0, 0)


class Pal:
    def __init__(self, hi, mid, dark, dk2):
        self.hi, self.mid, self.dark, self.dk2 = hi, mid, dark, dk2


TILE = Pal((128, 136, 156), (94, 100, 120), (72, 78, 98), (50, 54, 70))
TILE_B = Pal((120, 108, 104), (92, 80, 80), (72, 62, 64), (50, 44, 48))      # brownish tiles
TILE_G = Pal((110, 140, 132), (80, 108, 104), (62, 86, 84), (44, 60, 62))    # copper-green
WOOD = Pal((152, 108, 76), (124, 86, 60), (94, 64, 48), (66, 46, 40))
WOOD_D = Pal((110, 78, 60), (88, 62, 50), (68, 48, 42), (48, 36, 36))
PLASTER = Pal((230, 222, 200), (210, 200, 176), (178, 168, 148), (150, 140, 124))
CONCRETE = Pal((176, 176, 180), (150, 150, 158), (122, 122, 132), (96, 96, 108))
PAPER = (232, 226, 206)
GLOW = (255, 204, 128)
GLOW_PAPER = (255, 222, 156)
INKB = (38, 30, 38)


# ------------------------------------------------------------------ wrap layer
class WrapLayer:
    """A horizontally wrapping layer of period P. Draw with canvas x = world x + M
    (use L.x(wx)). finish() folds the margins so the result tiles seamlessly."""

    def __init__(self, P, h, margin=200):
        self.P, self.h, self.M = P, h, margin
        self.img = Image.new("RGBA", (P + 2 * margin, h))
        self.emis = Image.new("RGBA", (P + 2 * margin, h))
        self.d = ImageDraw.Draw(self.img)
        self.e = ImageDraw.Draw(self.emis)

    def x(self, wx):
        return wx + self.M

    def _fold(self, im):
        P, M, h = self.P, self.M, self.h
        base = im.crop((M, 0, M + P, h))
        base.alpha_composite(im.crop((0, 0, M, h)), (P - M, 0))
        base.alpha_composite(im.crop((M + P, 0, M + P + M, h)), (0, 0))
        ext = Image.new("RGBA", (P + W, h))
        ext.paste(base, (0, 0))
        ext.paste(base.crop((0, 0, W, h)), (P, 0))
        return ext

    def finish(self):
        return self._fold(self.img), self._fold(self.emis)


def graded_layer(key, build, tod, depth=0.0, glow_radius=3, glow_strength=0.5, lit_scale=1.0):
    """Cache (base, emis) = build() once, then cache the tod-graded + lit layer."""
    base, emis = cached(("raw",) + key, build)

    def mk():
        g = grade_rgba(base, tod, depth)
        amt = lit_amount(tod) * lit_scale
        if amt > 0:
            g = light_up(g, emis, amt, glow_radius=glow_radius, glow_strength=glow_strength)
        return g
    return cached(("graded",) + key + (tod, depth), mk)


def paste_layer(img, layer, P, off, y=0):
    """Paste the visible W-wide window of an extended (P+W) wrap layer."""
    o = int(math.floor(off)) % P
    c = layer.crop((o, 0, o + W, layer.height))
    img.paste(c, (0, int(y)), c)


# ------------------------------------------------------------------ roofs
def roof(d, x0, x1, yt, yb, pal=TILE, inset=None, ridge=True, oni=True, eave_shadow=None):
    """Front-facing kawara roof: trapezoid from ridge (yt) to eave (yb)."""
    h = max(1, yb - yt)
    inset = h if inset is None else inset
    for y in range(yt, yb + 1):
        f = (y - yt) / h
        xa = int(round(x0 + inset * (1 - f)))
        xb = int(round(x1 - inset * (1 - f)))
        course = (yb - y) % 4 == 3
        d.line([(xa, y), (xb, y)], fill=pal.dark if course else pal.mid)
        if not course:
            d.point([(x, y) for x in range(xa + 1, xb, 3)], fill=pal.dark)
            if (yb - y) % 4 == 2:
                d.point([(x, y) for x in range(xa + 2, xb, 3)], fill=pal.hi)
        d.point((xa, y), fill=pal.hi)
        d.point((xb, y), fill=pal.dk2)
    # eave: row of round tile ends + shadow line
    d.line([(x0, yb), (x1, yb)], fill=pal.dark)
    d.point([(x, yb) for x in range(x0 + 1, x1, 3)], fill=pal.hi)
    d.line([(x0, yb + 1), (x1, yb + 1)], fill=pal.dk2)
    if eave_shadow:
        d.line([(x0 + 1, yb + 2), (x1 - 1, yb + 2)], fill=eave_shadow)
    if ridge:
        ra, rb = x0 + inset - 2, x1 - inset + 2
        d.rectangle([ra, yt - 3, rb, yt - 1], fill=pal.dk2)
        d.line([(ra, yt - 3), (rb, yt - 3)], fill=pal.dark)
        d.point([(x, yt - 2) for x in range(ra + 2, rb, 5)], fill=pal.dark)
        if oni:
            for ox in (ra - 1, rb - 2):
                d.rectangle([ox, yt - 6, ox + 3, yt - 1], fill=pal.dk2)
                d.point((ox + 1, yt - 5), fill=pal.dark)


def flat_roof(d, x0, x1, y, pal=CONCRETE):
    d.rectangle([x0 - 1, y - 3, x1 + 1, y], fill=pal.dark)
    d.line([(x0 - 1, y - 3), (x1 + 1, y - 3)], fill=pal.hi)
    d.line([(x0 - 1, y + 1), (x1 + 1, y + 1)], fill=pal.dk2)


# ------------------------------------------------------------------ walls
def wall(d, x0, y0, x1, y1, pal=PLASTER, posts=None, post_pal=WOOD, texture=True, seed=0):
    d.rectangle([x0, y0, x1, y1], fill=pal.mid)
    if texture:
        r = rng("wall", x0, y0, seed)
        pts = [(r.randint(x0, x1), r.randint(y0, y1)) for _ in range(max(1, (x1 - x0) * (y1 - y0) // 40))]
        d.point(pts, fill=pal.dark)
        pts = [(r.randint(x0, x1), r.randint(y0, y1)) for _ in range(max(1, (x1 - x0) * (y1 - y0) // 60))]
        d.point(pts, fill=pal.hi)
    if posts:
        for px in posts:
            post(d, px, y0, y1, post_pal)


def post(d, x, y0, y1, pal=WOOD, w=3):
    d.rectangle([x, y0, x + w - 1, y1], fill=pal.mid)
    d.line([(x, y0), (x, y1)], fill=pal.hi)
    d.line([(x + w - 1, y0), (x + w - 1, y1)], fill=pal.dark)


def beam(d, x0, x1, y, pal=WOOD, h=3):
    d.rectangle([x0, y, x1, y + h - 1], fill=pal.mid)
    d.line([(x0, y), (x1, y)], fill=pal.hi)
    d.line([(x0, y + h - 1), (x1, y + h - 1)], fill=pal.dark)


def boards(d, x0, y0, x1, y1, pal=WOOD_D, step=4):
    """Vertical wooden board siding."""
    d.rectangle([x0, y0, x1, y1], fill=pal.mid)
    for x in range(x0, x1 + 1, step):
        d.line([(x, y0), (x, y1)], fill=pal.dark)
        if x + 1 <= x1:
            d.line([(x + 1, y0), (x + 1, y1)], fill=pal.hi)


def siding_h(d, x0, y0, x1, y1, pal=WOOD_D, step=3):
    """Horizontal clapboard siding."""
    d.rectangle([x0, y0, x1, y1], fill=pal.mid)
    for y in range(y0, y1 + 1, step):
        d.line([(x0, y), (x1, y)], fill=pal.dark)
        if y + 1 <= y1:
            d.line([(x0, y + 1), (x1, y + 1)], fill=pal.hi)


# ------------------------------------------------------------------ windows & doors
def glow_rect(e, x0, y0, x1, y1, color=GLOW, alpha=255, falloff=0.72):
    """Emissive fill that is brighter at the top and dithers to a dimmer tone
    toward the bottom (reads as warm interior light, not a flat slab)."""
    if e is None or x1 < x0 or y1 < y0:
        return
    c1 = tuple(color[:3]) + (alpha,)
    c2 = tuple(int(v * falloff) for v in color[:3]) + (alpha,)
    h = max(1, y1 - y0)
    e.rectangle([x0, y0, x1, y1], fill=c1)
    for y in range(y0, y1 + 1):
        f = (y - y0) / h
        if f < 0.4:
            continue
        if f > 0.72:
            e.line([(x0, y), (x1, y)], fill=c2)
        else:
            e.point([(x, y) for x in range(x0 + (y % 2), x1 + 1, 2)], fill=c2)


def lattice(d, e, x0, y0, x1, y1, lit=True, pal=WOOD, gap=2, inner=(54, 40, 40)):
    """Koshi lattice (vertical slats) over a dark interior; interior glows when lit."""
    d.rectangle([x0, y0, x1, y1], fill=inner)
    if lit and e is not None:
        glow_rect(e, x0 + 1, y0 + 1, x1 - 1, y1 - 1, (246, 176, 96), 235)
    for x in range(x0, x1 + 1, gap + 1):
        d.line([(x, y0), (x, y1)], fill=pal.mid)
        if e is not None:
            e.line([(x, y0), (x, y1)], fill=CLEAR)
    d.line([(x0, y0 + (y1 - y0) // 3), (x1, y0 + (y1 - y0) // 3)], fill=pal.dark)
    if e is not None:
        e.line([(x0, y0 + (y1 - y0) // 3), (x1, y0 + (y1 - y0) // 3)], fill=CLEAR)
    frame(d, x0 - 1, y0 - 1, x1 + 1, y1 + 1, pal)


def frame(d, x0, y0, x1, y1, pal=WOOD):
    d.rectangle([x0, y0, x1, y1], outline=pal.dark)
    d.line([(x0, y0), (x1, y0)], fill=pal.hi)
    d.line([(x0, y0), (x0, y1)], fill=pal.hi)


def shoji(d, e, x0, y0, x1, y1, lit=True, pal=WOOD, cols=3, rows=4, paper=PAPER):
    d.rectangle([x0, y0, x1, y1], fill=paper)
    d.line([(x0, y1), (x1, y1)], fill=shade(paper, 0.86))
    if lit and e is not None:
        glow_rect(e, x0, y0, x1, y1, GLOW_PAPER, 240, 0.8)
    for i in range(1, cols):
        x = x0 + (x1 - x0) * i // cols
        d.line([(x, y0), (x, y1)], fill=pal.mid)
        if e is not None:
            e.line([(x, y0), (x, y1)], fill=CLEAR)
    for j in range(1, rows):
        y = y0 + (y1 - y0) * j // rows
        d.line([(x0, y), (x1, y)], fill=pal.mid)
        if e is not None:
            e.line([(x0, y), (x1, y)], fill=CLEAR)
    frame(d, x0 - 1, y0 - 1, x1 + 1, y1 + 1, pal)
    if e is not None:
        e.rectangle([x0 - 1, y0 - 1, x1 + 1, y1 + 1], outline=CLEAR)


def glass(d, e, x0, y0, x1, y1, lit=True, pal=WOOD, bars=1, tint=(78, 96, 118)):
    d.rectangle([x0, y0, x1, y1], fill=tint)
    # sky reflection streaks
    for k in range(0, (x1 - x0) + (y1 - y0), 9):
        d.line([(x0 + k, y0), (x0 + k - 5, y0 + 5)], fill=mix(tint, (200, 220, 236), 0.45))
    if lit and e is not None:
        glow_rect(e, x0, y0, x1, y1, (250, 204, 140), 225)
    d.rectangle([x0, y0, x1, y1], outline=pal.dark)
    for i in range(1, bars + 1):
        x = x0 + (x1 - x0) * i // (bars + 1)
        d.line([(x, y0), (x, y1)], fill=pal.mid)
        if e is not None:
            e.line([(x, y0), (x, y1)], fill=CLEAR)
    frame(d, x0 - 1, y0 - 1, x1 + 1, y1 + 1, pal)
    if e is not None:
        e.rectangle([x0, y0, x1, y1], outline=CLEAR)


def mushiko(d, x0, y0, x1, y1, pal=PLASTER):
    """Plaster slit window (mushiko-mado) typical of machiya upper floors."""
    d.rectangle([x0, y0, x1, y1], fill=(60, 50, 50))
    for x in range(x0 + 1, x1, 3):
        d.rectangle([x, y0, x + 1, y1], fill=pal.mid)
        d.point((x, y0), fill=pal.hi)
    d.rectangle([x0 - 1, y0 - 1, x1 + 1, y1 + 1], outline=pal.dark)


def noren(d, x0, y0, x1, y1, color, text=None, text_color=(240, 236, 226), panels=3, img=None, e=None):
    """Split shop curtain (clears the emissive layer under it)."""
    if e is not None:
        e.rectangle([x0 - 1, y0 - 2, x1 + 1, y1], fill=CLEAR)
    d.rectangle([x0 - 1, y0 - 2, x1 + 1, y0 - 1], fill=(70, 50, 40))   # rod
    d.rectangle([x0, y0, x1, y1], fill=color)
    d.line([(x0, y0), (x1, y0)], fill=shade(color, 1.18))
    d.line([(x0, y1), (x1, y1)], fill=shade(color, 0.7))
    w = x1 - x0 + 1
    for i in range(1, panels):
        x = x0 + w * i // panels
        d.line([(x, y0 + 3), (x, y1)], fill=(40, 30, 34))
    if text and img is not None:
        from engine.text import draw_text
        draw_text(img, (x0 + x1) // 2 + 1, (y0 + y1) // 2 + 1, text, text_color, size=12, anchor="mm")
        if e is not None:   # lantern-lit lettering stays readable at night
            draw_text(e._image, (x0 + x1) // 2 + 1, (y0 + y1) // 2 + 1, text,
                      tuple(int(v * 0.8) for v in text_color), size=12, anchor="mm")


def sign(img, x0, y0, x1, y1, text, bg=(236, 230, 214), fg=(34, 26, 30), border=(70, 48, 36),
         e=None, glow=None, vertical=False, size=12):
    """Signboard with pixel-font text; e/glow -> emissive backlight at night."""
    from engine.text import draw_text
    d = ImageDraw.Draw(img)
    d.rectangle([x0, y0, x1, y1], fill=bg, outline=border)
    d.line([(x0 + 1, y0 + 1), (x1 - 1, y0 + 1)], fill=shade(bg, 1.1))
    if e is not None and glow is None:
        e.rectangle([x0, y0, x1, y1], fill=CLEAR)
    if e is not None and glow is not None:
        e.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=tuple(glow[:3]) + (255,))
    cx, cy = (x0 + x1 + 1) // 2, (y0 + y1 + 1) // 2
    if vertical:
        n = len(text)
        y = cy - n * size // 2
        for ch in text:
            draw_text(img, cx, y, ch, fg, size=size, anchor="mt")
            if e is not None and glow is not None:
                draw_text(e._image, cx, y, ch, fg, size=size, anchor="mt")
            y += size
    else:
        draw_text(img, cx, cy, text, fg, size=size, anchor="mm")
        if e is not None and glow is not None:
            draw_text(e._image, cx, cy, text, fg, size=size, anchor="mm")


def text_on(img, x, y, text, color, e=None, glow=None, anchor="mm", vertical=False, size=12, outline=None):
    from engine.text import draw_text
    if vertical:
        yy = y
        for ch in text:
            draw_text(img, x, yy, ch, color, size=size, anchor="mt", outline=outline)
            if e is not None:
                draw_text(e._image, x, yy, ch, glow or color, size=size, anchor="mt")
            yy += size
    else:
        draw_text(img, x, y, text, color, size=size, anchor=anchor, outline=outline)
        if e is not None:
            draw_text(e._image, x, y, text, glow or color, size=size, anchor=anchor)


def neon_tube(d, e, pts, color, off=(70, 60, 70), width=1):
    """Neon line: dim tube in base layer, bright in the emissive layer."""
    d.line(pts, fill=off, width=width)
    if e is not None:
        e.line(pts, fill=tuple(color[:3]) + (255,), width=width)


def window_grid(d, e, x0, y0, x1, y1, cw, ch, gap, r, lit_p=0.6, tint=(80, 96, 120), lit_c=(255, 214, 150)):
    """Grid of small modern windows; a random subset glows at night."""
    y = y0
    while y + ch <= y1:
        x = x0
        while x + cw <= x1:
            d.rectangle([x, y, x + cw - 1, y + ch - 1], fill=tint)
            d.point((x, y), fill=mix(tint, (220, 230, 240), 0.5))
            if e is not None and r.random() < lit_p:
                c = lit_c if r.random() < 0.8 else (170, 220, 255)
                e.rectangle([x, y, x + cw - 1, y + ch - 1], fill=c + (255,))
            x += cw + gap
        y += ch + gap
