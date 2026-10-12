"""Pixel drawing helpers. All drawing is aliased (no anti-aliasing) to keep a
clean pixel-art look. Canvas images are PIL 'RGB' 384x216; sprites are 'RGBA'.
"""
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

from .core import W, H, clamp, lerp_color

# ------------------------------------------------------------------ palette
# A shared master palette (Endesga-32-like). Using these keeps every scene
# looking like one game. Feel free to add shades, but prefer these.
INK = (24, 20, 37)          # outline colour for every sprite
PAL = {
    "ink": INK,
    "black": (12, 10, 18),
    "white": (255, 255, 255),
    "offwhite": (234, 236, 244),
    "silver": (192, 203, 220),
    "silver_d": (139, 155, 180),
    "grey": (90, 105, 136),
    "grey_d": (58, 68, 102),
    "navy": (38, 43, 68),
    "night": (24, 26, 48),
    "blue": (0, 149, 233),
    "blue_d": (18, 78, 137),
    "sky": (44, 232, 245),
    "sky_l": (140, 220, 255),
    "teal": (38, 92, 66),
    "green": (62, 137, 72),
    "green_l": (99, 199, 77),
    "lime": (190, 230, 90),
    "yellow": (254, 231, 97),
    "gold": (254, 174, 52),
    "orange": (247, 118, 34),
    "red": (228, 59, 68),
    "red_d": (162, 38, 51),
    "blood": (158, 40, 53),
    "maroon": (104, 56, 108),
    "pink": (246, 117, 122),
    "pink_l": (255, 190, 205),
    "sakura": (255, 183, 197),
    "purple": (104, 56, 108),
    "violet": (181, 80, 136),
    "brown": (116, 63, 57),
    "brown_l": (184, 111, 80),
    "wood": (190, 134, 82),
    "wood_d": (120, 78, 46),
    "tan": (228, 166, 114),
    "skin": (255, 214, 180),
    "skin_s": (232, 166, 136),
    "cream": (255, 240, 200),
}


def hexc(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def shade(c, k):
    """Multiply colour brightness by k (k<1 darker, k>1 lighter)."""
    return tuple(int(clamp(v * k, 0, 255)) for v in c[:3])


def mix(c1, c2, t):
    return lerp_color(c1[:3], c2[:3], t)


# ------------------------------------------------------------------ sprites
def ascii_sprite(art, palette, trim=True):
    """Build an RGBA sprite from ASCII art.

    '.' and ' ' are transparent; every other character must be a key in
    `palette` (value = RGB or RGBA tuple). Rows are left-aligned and padded.
    """
    lines = art.split("\n")
    if trim:
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
    w = max(len(l) for l in lines) if lines else 0
    img = Image.new("RGBA", (w, len(lines)), (0, 0, 0, 0))
    px = img.load()
    for y, line in enumerate(lines):
        for x, ch in enumerate(line):
            if ch in ". ":
                continue
            c = palette[ch]
            px[x, y] = c if len(c) == 4 else (c[0], c[1], c[2], 255)
    return img


_sprite_cache = {}


def cached_sprite(key, art, palette):
    """ascii_sprite with a cache (key must be hashable & unique per art)."""
    s = _sprite_cache.get(key)
    if s is None:
        s = ascii_sprite(art, palette)
        _sprite_cache[key] = s
    return s


def flip_h(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)


def scale_nearest(img, k):
    if k == 1:
        return img
    return img.resize((int(img.width * k), int(img.height * k)), Image.NEAREST)


def rotate_nearest(img, deg, expand=True):
    """Rotate a sprite counter-clockwise by `deg` degrees without smoothing."""
    return img.rotate(deg, resample=Image.NEAREST, expand=expand)


def tint(img, color, amount):
    """Blend an RGBA sprite's colours toward `color` (keeps alpha). amount 0..1"""
    if amount <= 0:
        return img
    a = np.asarray(img).astype(np.float32)
    c = np.array(color[:3], np.float32)
    a[..., :3] = a[..., :3] * (1 - amount) + c * amount
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")


def silhouette(img, color):
    a = np.asarray(img).copy()
    a[..., 0], a[..., 1], a[..., 2] = color[0], color[1], color[2]
    return Image.fromarray(a, "RGBA")


def set_alpha(img, alpha):
    """Scale the alpha channel of an RGBA sprite by alpha (0..1)."""
    if alpha >= 1:
        return img
    a = np.asarray(img).copy()
    a[..., 3] = (a[..., 3].astype(np.float32) * clamp(alpha)).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def outline(img, color=INK, diagonal=False):
    """Return a copy 2px larger with a 1px outline around opaque pixels."""
    a = np.asarray(img)
    h, w = a.shape[:2]
    out = np.zeros((h + 2, w + 2, 4), np.uint8)
    mask = a[..., 3] > 0
    m = np.zeros((h + 2, w + 2), bool)
    offs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        offs += [(-1, -1), (1, 1), (-1, 1), (1, -1)]
    for dy, dx in offs:
        m[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] |= mask
    out[m] = (color[0], color[1], color[2], 255)
    out[1:1 + h, 1:1 + w][mask] = a[mask]
    return Image.fromarray(out, "RGBA")


def paste(dst, sprite, x, y, anchor="topleft", alpha=1.0):
    """Paste an RGBA sprite onto dst.

    anchor: 'topleft' | 'center' | 'bottom' (x,y = bottom-centre, e.g. feet)
            | 'bottomleft' | 'top' (top-centre)
    """
    if alpha < 1:
        sprite = set_alpha(sprite, alpha)
    w, h = sprite.size
    if anchor == "center":
        x, y = x - w // 2, y - h // 2
    elif anchor == "bottom":
        x, y = x - w // 2, y - h
    elif anchor == "bottomleft":
        y = y - h
    elif anchor == "top":
        x = x - w // 2
    dst.paste(sprite, (int(round(x)), int(round(y))), sprite)


# ------------------------------------------------------------------ primitives
def draw(img):
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    return d


def rect(img, x, y, w, h, color, alpha=1.0):
    if w <= 0 or h <= 0:
        return
    if alpha >= 1 or img.mode != "RGB":
        ImageDraw.Draw(img).rectangle([x, y, x + w - 1, y + h - 1], fill=tuple(color))
    else:
        overlay_rect(img, x, y, w, h, color, alpha)


def overlay_rect(img, x, y, w, h, color, alpha):
    """Alpha-blended filled rectangle on an RGB canvas."""
    x0, y0 = max(0, int(x)), max(0, int(y))
    x1, y1 = min(img.width, int(x + w)), min(img.height, int(y + h))
    if x1 <= x0 or y1 <= y0:
        return
    region = img.crop((x0, y0, x1, y1))
    solid = Image.new("RGB", region.size, tuple(color[:3]))
    img.paste(Image.blend(region, solid, clamp(alpha)), (x0, y0))


def frame_rect(img, x, y, w, h, color):
    ImageDraw.Draw(img).rectangle([x, y, x + w - 1, y + h - 1], outline=tuple(color))


def line(img, p0, p1, color, width=1):
    ImageDraw.Draw(img).line([tuple(p0), tuple(p1)], fill=tuple(color), width=width)


def circle(img, cx, cy, r, color, outline_color=None):
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(color) if color else None,
              outline=tuple(outline_color) if outline_color else None)


def ellipse(img, x0, y0, x1, y1, color, outline_color=None):
    ImageDraw.Draw(img).ellipse([x0, y0, x1, y1], fill=tuple(color) if color else None,
                                outline=tuple(outline_color) if outline_color else None)


def polygon(img, pts, color, outline_color=None):
    ImageDraw.Draw(img).polygon([tuple(p) for p in pts], fill=tuple(color) if color else None,
                                outline=tuple(outline_color) if outline_color else None)


def pset(img, x, y, color):
    x, y = int(x), int(y)
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), tuple(color))


def stamp_line(img, p0, p1, size, color):
    """Draw a chunky line by stamping size x size squares along p0->p1.
    Good for limbs/weapons: stamp once with ink at size+2, then colour at size."""
    d = ImageDraw.Draw(img)
    x0, y0 = p0
    x1, y1 = p1
    n = max(1, int(math.hypot(x1 - x0, y1 - y0) * 2))
    half = size / 2.0
    c = tuple(color)
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        xa, ya = int(math.floor(x - half + 0.5)), int(math.floor(y - half + 0.5))
        d.rectangle([xa, ya, xa + size - 1, ya + size - 1], fill=c)


# ------------------------------------------------------------------ fills
_BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]],
                   np.float32) / 16.0


def gradient(img, x, y, w, h, c_top, c_bottom, steps=6, dither=True, vertical=True):
    """Banded + ordered-dithered gradient (classic pixel-art sky)."""
    x0, y0 = max(0, int(x)), max(0, int(y))
    x1, y1 = min(img.width, int(x + w)), min(img.height, int(y + h))
    if x1 <= x0 or y1 <= y0:
        return
    hh, ww = y1 - y0, x1 - x0
    if vertical:
        tt = (np.arange(y0, y1, dtype=np.float32) - y) / max(1, h - 1)
        tt = np.repeat(tt[:, None], ww, axis=1)
    else:
        tt = (np.arange(x0, x1, dtype=np.float32) - x) / max(1, w - 1)
        tt = np.repeat(tt[None, :], hh, axis=0)
    v = tt * (steps - 1)
    if dither:
        by = _BAYER4[(np.arange(y0, y1) % 4)[:, None], (np.arange(x0, x1) % 4)[None, :]]
        v = np.floor(v + by)
    else:
        v = np.round(v)
    v = np.clip(v / max(1, steps - 1), 0, 1)[..., None]
    ct = np.array(c_top[:3], np.float32)
    cb = np.array(c_bottom[:3], np.float32)
    arr = (ct * (1 - v) + cb * v).astype(np.uint8)
    img.paste(Image.fromarray(arr, "RGB"), (x0, y0))


def dither_mask(w, h, level, ox=0, oy=0):
    """Boolean mask (h,w) with ordered-dither density `level` 0..1."""
    by = _BAYER4[((np.arange(h) + oy) % 4)[:, None], ((np.arange(w) + ox) % 4)[None, :]]
    return by < level


def fill(img, color):
    img.paste(tuple(color[:3]), (0, 0, img.width, img.height))


def blank(color=(0, 0, 0)):
    return Image.new("RGB", (W, H), tuple(color[:3]))


def new_sprite(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))
