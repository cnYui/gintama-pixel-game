"""Private art for s11 松阳老师 (owned by the s11 scene agent).

Battlefield of the dead, Shoukasonjuku (yard / classroom / fire), the Joui
battlefield, the sunset ridge, the execution cliff and the present-day sunset.
Everything is a pure function of its arguments; static layers are built once
and cached at module level.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import W, H, rng, clamp, lerp, wave, step_frame, ease_out, stable_hash
from engine.gfx import (INK, shade, mix, outline, flip_h, ascii_sprite, stamp_line, rect, tint, set_alpha,
                        scale_nearest, overlay_rect as overlay_rect_)
from engine.text import draw_text, text_sprite
from chars import render_sprite, get_def
from chars.rig import OX, OY
from bg import common as C

_CACHE = {}


def cached(key, fn):
    v = _CACHE.get(key)
    if v is None:
        v = fn()
        _CACHE[key] = v
    return v


def sky_layer(key, stops, horizon, bands=12):
    return cached(("sky", key), lambda: Image.fromarray(
        C.vgradient(H, W, stops, bands=bands, y_end=horizon), "RGB"))


# ====================================================================== crows
CROW = (30, 24, 34)
_CROW_PAL = {"k": CROW, "b": (74, 62, 44)}
_CROW_FR = [
    """
kk.....kk
.kk...kk.
..kkkkkkb
...kkk...
""",
    """
..kkkkkkb
kkkkkkkk.
""",
    """
..kkkkkkb
.kk.kk...
kk...kk..
""",
]
_CROW_SIT = """
...kk.
..kkkb
.kkkk.
kkkkk.
.kkk..
..k.k.
"""


def _crow(i, facing):
    def mk():
        s = ascii_sprite(_CROW_FR[i], _CROW_PAL)
        return flip_h(s) if facing < 0 else s
    return cached(("crow", i, facing), mk)


def crow_fly(img, x, y, t, facing=1, phase=0.0):
    fr = (0, 1, 2, 1)[step_frame(t + phase, 10, 4)]
    s = _crow(fr, 1 if facing >= 0 else -1)
    img.paste(s, (int(x) - s.width // 2, int(y) - s.height // 2), s)


def crow_sit(img, x, y, facing=1, t=0.0, seed=0):
    """Perched crow, feet at (x, y). Occasionally dips its head."""
    s = cached(("crow_sit", facing), lambda: (lambda a: flip_h(a) if facing < 0 else a)(
        ascii_sprite(_CROW_SIT, _CROW_PAL)))
    dip = 1 if step_frame(t + seed * 0.37, 3, 7) == 0 else 0
    img.paste(s, (int(x) - s.width // 2, int(y) - s.height + dip), s)


def crows_circling(img, t, n=5, seed=0, cx=200, cy=40, rx=90, ry=16, spd=0.35):
    for i in range(n):
        r = rng("crowc", seed, i)
        a = t * spd * r.uniform(0.8, 1.3) * 2 * math.pi + r.uniform(0, 6.28)
        x = cx + math.cos(a) * rx * r.uniform(0.6, 1.1) + r.uniform(-30, 30)
        y = cy + math.sin(a) * ry * r.uniform(0.6, 1.2) + r.uniform(-12, 12)
        facing = 1 if -math.sin(a) > 0 else -1
        crow_fly(img, x, y, t, facing, i * 0.23)


# ====================================================================== generic props
def sun_disc(img, x, y, r, core=(255, 236, 190), rim=(250, 170, 110), glow=(255, 150, 90), bands=True):
    """Big low sun with dithered halo and horizontal haze bands cut through it."""
    key = ("sun", r, core, rim, glow, bands)

    def mk():
        n = 2 * (r + 16) + 1
        c = r + 16
        yy, xx = np.mgrid[0:n, 0:n]
        d = np.hypot(xx - c, yy - c)
        arr = np.zeros((n, n, 4), np.uint8)
        by = C.bayer(n, n)
        halo = np.clip(1 - (d - r) / 16, 0, 1)
        hq = np.floor(halo * 3 + by * 0.999) / 3
        m = (d > r) & (hq > 0)
        arr[m, :3] = np.array(glow, np.uint8)
        arr[m, 3] = (hq[m] * 110).astype(np.uint8)
        disc = d <= r
        k = np.clip((d / r) ** 2, 0, 1)
        kq = np.floor(k * 3 + by * 0.999) / 3
        col = np.array(core, np.float32) * (1 - kq[..., None]) + np.array(rim, np.float32) * kq[..., None]
        arr[disc, :3] = col[disc].astype(np.uint8)
        arr[disc, 3] = 255
        if bands:
            for j, (yy0, hh) in enumerate(((c + r * 0.25, 2), (c + r * 0.5, 3), (c + r * 0.72, 2))):
                y0 = int(yy0)
                arr[y0:y0 + hh, :, 3] = np.where(arr[y0:y0 + hh, :, 3] == 255, 0, arr[y0:y0 + hh, :, 3])
        return Image.fromarray(arr, "RGBA")
    s = cached(key, mk)
    img.paste(s, (int(x) - s.width // 2, int(y) - s.height // 2), s)


def _tree_sprite(scale=1.0):
    """Leafless dead tree silhouette (cached)."""
    def mk():
        w, h = int(110 * scale), int(96 * scale)
        im = Image.new("RGBA", (w, h))
        r = rng("deadtree", scale)
        col = (44, 34, 40)

        def branch(x, y, ang, L, wd, depth):
            if depth == 0 or L < 3:
                return
            x2 = x + math.cos(math.radians(ang)) * L
            y2 = y - math.sin(math.radians(ang)) * L
            stamp_line(im, (x, y), (x2, y2), max(1, int(wd)), col)
            n = 2 if depth > 1 else 1
            for k in range(n):
                na = ang + r.uniform(18, 42) * (1 if k == 0 else -1) + r.uniform(-8, 8)
                branch(x2, y2, na, L * r.uniform(0.58, 0.78), wd * 0.66, depth - 1)
        bx, by = w * 0.5, h - 1
        stamp_line(im, (bx - 3, by), (bx + 3, by), 3, col)
        branch(bx, by, 88, 34 * scale, 5 * scale, 6)
        branch(bx + 1, by - 22 * scale, 30, 26 * scale, 3 * scale, 4)
        branch(bx - 1, by - 28 * scale, 150, 24 * scale, 3 * scale, 4)
        return im
    return cached(("tree", scale), mk)


def dead_tree(img, x, y, scale=1.0):
    s = _tree_sprite(scale)
    img.paste(s, (int(x) - s.width // 2, int(y) - s.height), s)
    return s


def banner(img, x, y, t, h=46, cw=11, ch=26, col=(126, 64, 56), mon=None, lean=0, tatter=True, seed=0,
           pole=(70, 50, 40)):
    """Nobori war banner on a pole (foot at (x, y)), cloth fluttering in the wind."""
    d = ImageDraw.Draw(img)
    top = (x + lean, y - h)
    d.line([(x, y), top], fill=INK, width=3)
    d.line([(x, y), top], fill=pole, width=1)
    tq = step_frame(t, 12) / 12
    pts_l, pts_r = [], []
    for j in range(7):
        v = j / 6
        yy = top[1] + 2 + v * ch
        xx = top[0] + lean * v * 0.2
        fl = math.sin(tq * 7 + v * 4 + seed) * 2.2 * v
        pts_l.append((xx + 1, yy))
        tr = cw + fl + (math.sin(v * 13 + seed) * 1.5 if (tatter and v > 0.6) else 0)
        pts_r.append((xx + tr, yy + fl * 0.3))
    poly = pts_l + pts_r[::-1]
    d.polygon(poly, fill=col, outline=INK)
    d.line([(top[0], top[1] + 2), (top[0] + cw + 1, top[1] + 2)], fill=pole)
    if mon:
        cx, cy = top[0] + cw * 0.55, top[1] + 9
        d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], outline=mon)


# ====================================================================== battlefield (A)
BF_SKY = [(0.0, (34, 26, 44)), (0.4, (96, 56, 66)), (0.78, (178, 104, 80)), (1.0, (222, 156, 108))]
SIL = (44, 32, 38)
BF_SUN_X = 92


def _mound():
    """Dark silhouette heap of the fallen (armour, helmets, spears — no detail,
    non-graphic), rim-lit from the low sun on the left."""
    w, h = 88, 30
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    base, inner, rim = (30, 22, 28), (46, 36, 42), (150, 110, 88)
    pts = [(0, h - 1), (4, h - 5), (8, h - 7), (11, h - 11), (16, h - 12), (19, h - 16), (25, h - 17),
           (29, h - 21), (35, h - 22), (39, h - 26), (46, h - 26), (50, h - 23), (56, h - 22), (60, h - 18),
           (66, h - 16), (70, h - 12), (76, h - 10), (80, h - 6), (87, h - 1)]
    # protrusions behind the heap: spears, a broken banner pole, a sword hilt
    for (x0, y0, x1, y1) in ((14, h - 8, 3, h - 29), (62, h - 12, 80, h - 29), (52, h - 20, 56, h - 30)):
        d.line([(x0, y0), (x1, y1)], fill=base, width=2)
    d.polygon([(1, h - 29), (5, h - 29), (2, h - 33)], fill=base)
    d.polygon([(78, h - 29), (82, h - 28), (82, h - 33)], fill=base)
    d.polygon([(56, h - 30), (64, h - 29), (63, h - 25), (57, h - 26)], fill=base)      # torn flag
    d.polygon(pts, fill=base)
    # helmet silhouettes & crest bumps along the ridge
    d.pieslice([22, h - 21, 30, h - 13], 180, 360, fill=base)
    d.pieslice([64, h - 20, 72, h - 12], 180, 360, fill=base)
    d.arc([23, h - 25, 29, h - 19], 200, 340, fill=base, width=1)
    # faint inner structure (armour edges)
    r = rng("mound_in")
    for _ in range(18):
        x = r.uniform(8, 80)
        y = r.uniform(h - 14, h - 3)
        L = r.uniform(3, 8)
        d.line([(x, y), (x + L, y - r.uniform(-1, 2))], fill=inner)
    # rim light on the left/top-facing edges (sun on the left)
    for a, b in zip(pts[:11], pts[1:11]):
        d.line([a, b], fill=rim)
    d.line([(22, h - 17), (26, h - 21)], fill=rim)
    d.point((3, h - 30), fill=rim)
    return im


def mound_sprite():
    return cached("mound", _mound)


def _bf_mid():
    """Wide mid-ground strip of silhouettes: spears, fallen horses/soldiers
    (as anonymous dark lumps), broken wheels. Parallax ~0.55."""
    w, h = 900, 60
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    r = rng("bfmid")
    base = h - 6
    for i in range(34):                       # spears / arrows
        x = r.uniform(0, w)
        L = r.uniform(14, 34)
        a = math.radians(r.uniform(58, 122))
        x2, y2 = x + math.cos(a) * L, base - math.sin(a) * L
        d.line([(x, base + r.uniform(0, 4)), (x2, y2)], fill=SIL, width=1)
        d.polygon([(x2 - 1, y2 + 1), (x2 + 1, y2 + 1), (x2, y2 - 2)], fill=SIL)
    for i in range(16):                       # anonymous dark lumps (fallen)
        x = r.uniform(0, w)
        ww = r.uniform(10, 22)
        d.ellipse([x, base - 3, x + ww, base + 3], fill=SIL)
        d.ellipse([x + ww * 0.7, base - 5, x + ww * 0.7 + 5, base], fill=SIL)
    for x in (140, 520, 780):                 # broken cart wheels
        d.ellipse([x, base - 16, x + 16, base], outline=SIL, width=2)
        for k in range(4):
            a = k * math.pi / 4
            d.line([(x + 8 - math.cos(a) * 7, base - 8 - math.sin(a) * 7),
                    (x + 8 + math.cos(a) * 7, base - 8 + math.sin(a) * 7)], fill=SIL)
    return im


_BF_BANNERS = [(60, 0.55, (122, 60, 54)), (230, 0.55, (96, 84, 70)), (410, 0.55, (122, 60, 54)),
               (600, 0.55, (96, 84, 70))]


def battlefield(img, t, cam):
    """Sky + sun + ridges + smoke columns + silhouettes + ground (world at cam)."""
    img.paste(sky_layer("bf", BF_SKY, 142), (0, 0))
    sun_disc(img, BF_SUN_X - cam * 0.05, 116, 22, core=(255, 238, 200), rim=(250, 190, 130), glow=(255, 160, 100))
    C.far_mountains(img, cam, "dusk", y=140)
    # smoke columns rising from the far field
    d = ImageDraw.Draw(img)
    for ci, wx in enumerate((70, 250, 420)):
        sx = wx - cam * 0.3
        for j in range(12):
            u = ((t * 0.18 + j / 12 + ci * 0.31) % 1.0)
            y = 144 - u * 118
            x = sx + u * u * 46 + math.sin(u * 7 + j + ci) * 3
            rad = 3 + u * 11
            c = mix((58, 48, 56), (132, 112, 112), u)
            d.ellipse([x - rad, y - rad * 0.8, x + rad, y + rad * 0.8], fill=c)
    mid = cached("bfmid", _bf_mid)
    ox = int(cam * 0.55)
    img.paste(mid.crop((ox, 0, ox + W, mid.height)), (0, 150 - mid.height + 6), mid.crop((ox, 0, ox + W, mid.height)))
    for i, (wx, par, col) in enumerate(_BF_BANNERS):
        x = wx - cam * par
        if -30 < x < W + 30:
            banner(img, x, 150, t, h=40, cw=9, ch=22, col=col, lean=(-3, 2, -1, 4)[i], seed=i * 1.7,
                   mon=(200, 170, 110) if i % 2 == 0 else None)
    C.dirt_ground(img, 148, cam, "dusk", grass=0.15)


# ground scatter (world coords, parallax 1)
_SCATTER = [("katana", 40, 172, -70), ("arrow", 100, 168, 60), ("helmet", 132, 176, 0),
            ("arrow", 150, 184, 110), ("katana", 330, 178, -110), ("arrow", 350, 170, 75),
            ("helmet", 375, 186, 0), ("katana", 20, 196, -60), ("arrow", 250, 196, 100)]


def scatter(img, cam, t=0):
    d = ImageDraw.Draw(img)
    for kind, wx, y, ang in _SCATTER:
        x = wx - cam
        if not -20 < x < W + 20:
            continue
        if kind == "katana":
            a = math.radians(ang)
            tip = (x, y)
            top = (x - math.cos(a) * 16, y + math.sin(a) * 16)
            stamp_line(img, tip, top, 3, INK)
            stamp_line(img, tip, top, 1, (190, 196, 206))
            hx, hy = top[0] - math.cos(a) * 5, top[1] + math.sin(a) * 5
            stamp_line(img, top, (hx, hy), 3, INK)
            stamp_line(img, top, (hx, hy), 1, (60, 44, 52))
            stamp_line(img, (top[0] - 2, top[1]), (top[0] + 2, top[1]), 1, (170, 140, 70))
        elif kind == "arrow":
            a = math.radians(ang)
            x2, y2 = x + math.cos(a) * 12, y - math.sin(a) * 12
            d.line([(x, y), (x2, y2)], fill=(80, 60, 48))
            d.line([(x2 - 1, y2), (x2 + 1, y2 + 1)], fill=(220, 214, 200))
        elif kind == "helmet":
            d.pieslice([x - 6, y - 7, x + 6, y + 3], 180, 360, fill=(70, 66, 76), outline=INK)
            d.line([(x - 7, y - 2), (x + 7, y - 2)], fill=INK)
            d.line([(x - 3, y - 5), (x, y - 5)], fill=(120, 118, 130))


def sword_h(img, x0, x1, y, hilt_right=True):
    """Sheathed katana lying horizontally from x0 to x1 at row y (hilt at the right end)."""
    if x1 < x0:
        x0, x1 = x1, x0
        hilt_right = not hilt_right
    L = x1 - x0
    hx = x1 - 6 if hilt_right else x0 + 6
    rect(img, x0 - 1, y - 2, L + 3, 4, INK)
    if hilt_right:
        rect(img, x0, y - 1, hx - x0, 2, (66, 50, 62))
        rect(img, x0 + 1, y - 1, hx - x0 - 2, 1, (122, 100, 118))
        rect(img, hx + 1, y - 1, x1 - hx, 2, (206, 204, 214))
        rect(img, hx, y - 3, 1, 6, INK)
        rect(img, hx, y - 2, 1, 4, (232, 184, 70))
    else:
        rect(img, hx + 1, y - 1, x1 - hx, 2, (66, 50, 62))
        rect(img, hx + 1, y - 1, x1 - hx - 1, 1, (122, 100, 118))
        rect(img, x0, y - 1, hx - x0, 2, (206, 204, 214))
        rect(img, hx, y - 3, 1, 6, INK)
        rect(img, hx, y - 2, 1, 4, (232, 184, 70))


def blade_on_ground(img, x, y, ang=8):
    a = math.radians(ang)
    p0 = (x - math.cos(a) * 9, y + math.sin(a) * 9)
    p1 = (x + math.cos(a) * 9, y - math.sin(a) * 9)
    stamp_line(img, p0, p1, 3, INK)
    stamp_line(img, p0, p1, 1, (220, 226, 236))
    hp = (p0[0] - math.cos(a) * 5, p0[1] + math.sin(a) * 5)
    stamp_line(img, p0, hp, 3, INK)
    stamp_line(img, p0, hp, 1, (70, 64, 92))


def light_shaft(img, x_top, w_top, x_bot, w_bot, y0, y1, color=(255, 236, 190), alpha=0.18, t=0.0):
    """Soft diagonal god-ray (additive-ish blend) from the sky onto the ground."""
    mask = Image.new("L", (W, H), 0)
    a = int(255 * alpha * (0.85 + 0.15 * math.sin(t * 1.3)))
    ImageDraw.Draw(mask).polygon([(x_top, y0), (x_top + w_top, y0), (x_bot + w_bot, y1), (x_bot, y1)], fill=a)
    solid = Image.new("RGB", (W, H), color)
    img.paste(solid, (0, 0), mask)


def light_motes(img, t, area, n=18, seed=0, color=(255, 244, 210)):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = area
    for i in range(n):
        r = rng("mote", seed, i)
        per = r.uniform(4, 8)
        u = ((t + r.uniform(0, per)) % per) / per
        x = x0 + (r.uniform(0, 1) * (x1 - x0) + u * 20 + math.sin(u * 6 + i) * 4) % (x1 - x0)
        y = y1 - u * (y1 - y0)
        if math.sin(t * 3 + i) > -0.3:
            d.point((x, y), fill=color)


# ====================================================================== Shoukasonjuku
TILE, TILE_D, TILE_L = (78, 84, 104), (52, 56, 74), (116, 124, 146)
WOOD, WOOD_D, WOOD_L = (126, 86, 54), (78, 52, 36), (168, 122, 80)
PLASTER, PLASTER_D = (236, 228, 208), (204, 194, 170)
PAPER = (246, 240, 222)


def _school():
    w, h = 212, 84
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    # walls
    d.rectangle([12, 36, w - 13, 74], fill=PLASTER, outline=INK)
    d.rectangle([12, 36, w - 13, 40], fill=WOOD_D)
    # shoji panels between posts (some open)
    posts = list(range(12, w - 12, 31))
    opened = {2, 4}
    for i, px in enumerate(posts[:-1]):
        x0, x1 = px + 3, posts[i + 1] - 1
        y0, y1 = 45, 72
        if i in opened:
            d.rectangle([x0, y0, x1, y1], fill=(62, 46, 40))
            d.rectangle([x0, y1 - 5, x1, y1], fill=(92, 72, 56))
            d.line([(x0, y0), (x1, y0)], fill=(40, 30, 28))
        else:
            d.rectangle([x0, y0, x1, y1], fill=PAPER)
            for gx in range(x0 + 4, x1, 5):
                d.line([(gx, y0), (gx, y1)], fill=WOOD_L)
            for gy in range(y0 + 5, y1, 6):
                d.line([(x0, gy), (x1, gy)], fill=WOOD_L)
            d.rectangle([x0, y0, x1, y1], outline=WOOD)
            d.rectangle([x0, y1 - 4, x1, y1], fill=WOOD)
    for px in posts:
        d.rectangle([px, 40, px + 2, 74], fill=WOOD_D)
        d.line([(px, 40), (px, 74)], fill=WOOD)
    d.rectangle([12, 42, w - 13, 44], fill=WOOD)
    # roof (kawara)
    roof = [(30, 8), (w - 31, 8), (w - 1, 34), (0, 34)]
    d.polygon(roof, fill=TILE, outline=INK)
    for k in range(0, 62):
        xt = 30 + k * (w - 61) / 61
        xb = 0 + k * (w - 1) / 61
        d.line([(xt, 9), (xb, 33)], fill=TILE_D if k % 2 else TILE_L)
    for yy in (15, 22, 29):
        d.line([(0 + (34 - yy) * 30 / 26, yy), (w - 1 - (34 - yy) * 30 / 26, yy)], fill=TILE_D)
    d.rectangle([24, 3, w - 25, 9], fill=TILE_D, outline=INK)
    d.line([(25, 4), (w - 26, 4)], fill=TILE_L)
    d.rectangle([20, 0, 28, 9], fill=TILE_D, outline=INK)              # onigawara
    d.rectangle([w - 29, 0, w - 21, 9], fill=TILE_D, outline=INK)
    d.rectangle([0, 34, w - 1, 37], fill=TILE_D, outline=INK)          # eave
    for ex in range(2, w - 2, 5):
        d.point((ex, 35), fill=TILE_L)
    d.rectangle([4, 38, w - 5, 40], fill=(60, 50, 50))                   # eave shadow
    # engawa (veranda) + legs
    d.rectangle([2, 73, w - 3, 76], fill=WOOD_L, outline=INK)
    d.rectangle([2, 77, w - 3, 79], fill=WOOD_D)
    for lx in range(8, w - 6, 22):
        d.rectangle([lx, 80, lx + 2, h - 1], fill=WOOD_D)
    d.line([(2, h - 1), (w - 3, h - 1)], fill=(60, 44, 36))
    # signboard 「松下私塾」
    sx0, sy0 = w // 2 - 30, 18
    d.rectangle([sx0 - 1, sy0 - 1, sx0 + 61, sy0 + 15], fill=INK)
    d.rectangle([sx0, sy0, sx0 + 60, sy0 + 14], fill=(214, 176, 120))
    d.rectangle([sx0 + 1, sy0 + 1, sx0 + 59, sy0 + 13], outline=(150, 110, 70))
    draw_text(im, sx0 + 31, sy0 + 8, "松下私塾", (40, 26, 20), anchor="mm")
    return im


def school_sprite(state="day"):
    def mk():
        im = _school()
        if state == "burnt":
            a = np.asarray(im).astype(np.float32)
            paper = np.all(np.abs(a[..., :3] - np.array(PAPER, np.float32)) < 2, axis=-1)
            inner = np.all(np.abs(a[..., :3] - np.array((62, 46, 40), np.float32)) < 2, axis=-1)
            a[..., :3] *= np.array((0.32, 0.26, 0.3), np.float32)
            a[paper, :3] = (255, 150, 60)
            a[inner, :3] = (255, 214, 110)
            im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
        return im
    return cached(("school", state), mk)


def yard(img, t):
    """Shoukasonjuku courtyard on a sunny day (static camera)."""
    img.paste(cached("yard_static", _yard_static), (0, 0))
    C.clouds(img, t, 0, "day", seed=11, count=4, y0=6, y1=50, speed=0.6)
    s = school_sprite("day")
    img.paste(s, (96, 148 - s.height), s)
    C.cherry_tree(img, 92, 152, t, scale=1, tod="day")
    _fence(img, 318, 150)


def _yard_static():
    im = Image.new("RGB", (W, H))
    C.sky(im, "day", 0, horizon=132, body=False)
    C.far_mountains(im, 0, "day", y=132)
    C.dirt_ground(im, 142, 0, "day", grass=0.35)
    return im


def _fence(img, x0, y):
    d = ImageDraw.Draw(img)
    for i in range(0, W - x0, 4):
        x = x0 + i
        d.rectangle([x, y - 18, x + 2, y], fill=(150, 160, 96), outline=INK)
        d.point((x + 1, y - 17), fill=(196, 206, 130))
    d.rectangle([x0, y - 13, W, y - 12], fill=(96, 70, 44))
    d.rectangle([x0, y - 6, W, y - 5], fill=(96, 70, 44))


def _desk():
    w, h = 22, 9
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, 3], fill=WOOD_L, outline=INK)
    d.line([(1, 1), (w - 2, 1)], fill=(206, 160, 108))
    d.rectangle([2, 4, 4, h - 1], fill=WOOD_D, outline=INK)
    d.rectangle([w - 5, 4, w - 3, h - 1], fill=WOOD_D, outline=INK)
    return im


def desk(img, x, y, props=None, piece=None, rot=0):
    """Low writing desk, bottom-centre at (x, y). piece: 'L'/'R' half (broken)."""
    s = cached("desk", _desk)
    if piece:
        w = s.width // 2
        s = s.crop((0, 0, w, s.height)) if piece == "L" else s.crop((w, 0, s.width, s.height))
        if rot:
            s = s.rotate(rot, resample=Image.NEAREST, expand=True)
    img.paste(s, (int(x) - s.width // 2, int(y) - s.height), s)
    if props == "books" and not piece:
        rect(img, int(x) - 7, int(y) - 12, 9, 4, INK)
        rect(img, int(x) - 6, int(y) - 11, 7, 1, (200, 80, 70))
        rect(img, int(x) - 6, int(y) - 10, 7, 1, (240, 236, 220))
        rect(img, int(x) + 3, int(y) - 11, 5, 3, INK)
        rect(img, int(x) + 4, int(y) - 10, 3, 1, (60, 60, 70))
    elif props == "paper" and not piece:
        rect(img, int(x) - 6, int(y) - 10, 10, 2, (246, 242, 230))
        rect(img, int(x) - 4, int(y) - 10, 5, 1, (40, 36, 40))


def _classroom_static():
    im = Image.new("RGB", (W, H))
    C.room_wall(im, 30, "day", 0, 140, "shoji")
    C.tatami(im, 140, 30, "day")
    d = ImageDraw.Draw(im)
    # hanging scroll 「武士道」
    x, y = 180, 22
    d.rectangle([x - 1, y - 3, x + 14, y - 1], fill=WOOD_D)
    d.rectangle([x, y, x + 13, y + 50], fill=(240, 232, 206), outline=INK)
    d.rectangle([x + 2, y + 2, x + 11, y + 48], outline=(190, 170, 120))
    for i, ch in enumerate("武士道"):
        draw_text(im, x + 7, y + 11 + i * 14, ch, (30, 24, 26), anchor="mm")
    d.rectangle([x - 1, y + 51, x + 14, y + 53], fill=WOOD_D)
    d.line([(x + 6, y - 3), (x + 6, y - 9)], fill=INK)
    return im


def classroom(img, t):
    img.paste(cached("classroom", _classroom_static), (0, 0))
    # sun rays through the shoji
    for i, x in enumerate((40, 150, 260)):
        light_shaft(img, x, 26, x + 60, 40, 30, 190, (255, 246, 214), 0.10, t + i)
    light_motes(img, t, (0, 30, W, 150), n=16, seed=3)


# ====================================================================== fire (C)
FIRE_OUT, FIRE_MID, FIRE_CORE = (206, 52, 34), (250, 140, 40), (255, 228, 120)


def flames(img, t, spots, seed=0, scale=1.0):
    """Procedural flame tongues. spots: [(x, base_y, height, width)]."""
    d = ImageDraw.Draw(img)
    tq = step_frame(t, 12) / 12
    for i, (x, y, h, w) in enumerate(spots):
        r = rng("flame", seed, i)
        ph, sp = r.uniform(0, 6.28), r.uniform(5, 9)
        hh = h * scale * (0.78 + 0.22 * math.sin(tq * sp + ph) + 0.1 * math.sin(tq * sp * 2.3 + ph * 1.7))
        sway = math.sin(tq * sp * 0.7 + ph) * w * 0.4
        for col, kh, kw in ((FIRE_OUT, 1.0, 1.0), (FIRE_MID, 0.72, 0.72), (FIRE_CORE, 0.42, 0.45)):
            Hh, Ww = hh * kh, w * kw
            pts = [(x - Ww / 2, y), (x - Ww * 0.46, y - Hh * 0.35), (x - Ww * 0.18 + sway * 0.5, y - Hh * 0.72),
                   (x + sway, y - Hh), (x + Ww * 0.22 + sway * 0.4, y - Hh * 0.6), (x + Ww * 0.46, y - Hh * 0.3),
                   (x + Ww / 2, y)]
            d.polygon(pts, fill=col)


FIRE_SKY = [(0.0, (14, 10, 26)), (0.5, (54, 22, 36)), (0.85, (150, 52, 38)), (1.0, (214, 110, 50))]


def burning_school(img, t):
    img.paste(sky_layer("fire", FIRE_SKY, 146), (0, 0))
    d = ImageDraw.Draw(img)
    # smoke plumes
    for ci, wx in enumerate((150, 230, 300)):
        for j in range(10):
            u = ((t * 0.22 + j / 10 + ci * 0.37) % 1.0)
            y = 70 - u * 80
            x = wx + u * u * 60 + math.sin(u * 6 + j) * 4
            rad = 6 + u * 16
            c = mix((70, 40, 44), (40, 30, 42), u)
            d.ellipse([x - rad, y - rad * 0.8, x + rad, y + rad * 0.8], fill=c)
    C.far_mountains(img, 0, "night", y=146)
    C.add_sprite(img, C.glow_sprite(120, (255, 110, 40), 0.9 + 0.1 * math.sin(t * 9)), 200 - 120, 110 - 120)
    s = school_sprite("burnt")
    sx, sy = 94, 148 - s.height
    img.paste(s, (sx, sy), s)
    # flames: roof, windows, pillars
    spots = []
    for k in range(9):
        spots.append((sx + 14 + k * 23, sy + 12 + abs(k - 4) * 3, 26 + (k % 3) * 8, 16))
    for k in (0, 1, 3, 5):
        spots.append((sx + 30 + k * 31, sy + 72, 18, 12))
    flames(img, t, spots, seed=5)
    C.dirt_ground(img, 146, 0, "night", grass=0.2)
    # warm light pool on the ground
    C.add_sprite(img, C.glow_sprite(70, (255, 120, 40), 0.55), 200 - 70, 150 - 70)


# ====================================================================== Joui battlefield (D1)
def _army_strip():
    w, h = 800, 40
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    r = rng("army")
    col = (38, 34, 48)
    for row, (y, s) in enumerate(((30, 0.8), (36, 1.0))):
        x = r.uniform(0, 8)
        while x < w:
            hh = int(12 * s + r.uniform(-1, 2))
            d.rectangle([x, y - hh, x + 5 * s, y], fill=col)
            d.ellipse([x - 1, y - hh - 5 * s, x + 5 * s + 1, y - hh + 1], fill=col)
            if r.random() < 0.5:
                d.line([(x + 5, y - hh), (x + 8, y - hh - 14 * s)], fill=col)
            if r.random() < 0.15:
                d.ellipse([x - 2, y - hh - 8 * s, x + 7 * s, y - hh - 3 * s], fill=col)   # horned / big head
            x += r.uniform(6, 11) * s
    return im


WAR_SKY = [(0.0, (22, 16, 26)), (0.45, (70, 38, 44)), (0.8, (140, 66, 52)), (1.0, (196, 104, 66))]


def joui_field(img, t, cam, flash=0.0):
    img.paste(sky_layer("war", WAR_SKY, 140), (0, 0))
    C.clouds(img, t, cam * 0.2, "storm", seed=21, count=5, y0=4, y1=70, speed=2.0)
    from bg import edo as E
    E.ship(img, 318 - cam * 0.08 + t * 4, 46, "cruiser", t, scale=1, facing=-1, tod="dusk", haze=0.35)
    E.ship(img, 120 - cam * 0.06 + t * 3, 26, "pirate", t, scale=1, facing=-1, tod="dusk", haze=0.55)
    if flash > 0:
        overlay_rect_(img, 0, 0, W, 140, (236, 226, 255), flash)
    C.far_mountains(img, cam, "dusk", y=138)
    army = cached("army", _army_strip)
    ox = int(cam * 0.5) + 200
    c = army.crop((ox, 0, ox + W, army.height))
    img.paste(c, (0, 148 - army.height + 2), c)
    C.dirt_ground(img, 146, cam, "dusk", grass=0.25)


# ====================================================================== ridge (D2)
RIDGE_SKY = [(0.0, (44, 30, 64)), (0.4, (132, 60, 72)), (0.75, (230, 120, 70)), (1.0, (252, 186, 96))]


def _ridge_static():
    im = Image.new("RGB", (W, H))
    im.paste(sky_layer("ridge", RIDGE_SKY, 150), (0, 0))
    sun_disc(im, 196, 118, 44, core=(255, 240, 196), rim=(255, 184, 110), glow=(255, 150, 80))
    C.far_mountains(im, 40, "dusk", y=150)
    d = ImageDraw.Draw(im)
    # the ridge the four stand on (flat top ~ y=150 between x 110..300)
    pts = [(0, 186), (40, 176), (90, 160), (120, 152), (150, 150), (250, 150), (290, 152), (320, 160),
           (360, 172), (W, 180), (W, H), (0, H)]
    d.polygon(pts, fill=(46, 30, 40))
    d.line(pts[:10], fill=(120, 70, 60))
    return im


def ridge(img, t):
    img.paste(cached("ridge", _ridge_static), (0, 0))
    C.clouds(img, t, 0, "dusk", seed=4, count=3, y0=20, y1=70, speed=0.8)
    # grass tufts on the ridge, blowing
    d = ImageDraw.Draw(img)
    tq = step_frame(t, 12) / 12
    for i in range(30):
        r = rng("rgrass", i)
        x = r.uniform(80, 330)
        y = 150 + (0 if 120 < x < 290 else (abs(x - 205) - 85) * 0.25)
        sway = math.sin(tq * 5 + i) * 1.5 + 1.5
        d.line([(x, y + 1), (x + sway, y - 3 - r.uniform(0, 2))], fill=(70, 44, 50))


# ====================================================================== cliff (E)
CLIFF_SKY = [(0.0, (96, 96, 110)), (0.5, (160, 156, 160)), (1.0, (214, 206, 196))]
EDGE_X = 44


def _cliff_static():
    im = Image.new("RGB", (W, H))
    im.paste(sky_layer("cliff", CLIFF_SKY, 170), (0, 0))
    sun_disc(im, 300, 64, 12, core=(250, 246, 232), rim=(230, 224, 210), glow=(240, 232, 214), bands=False)
    d = ImageDraw.Draw(im)
    # distant low ranges far below (we are high up)
    r = rng("cliffmtn")
    for layer, (yb, col, amp) in enumerate(((150, (170, 168, 176), 10), (172, (140, 138, 150), 14),
                                            (196, (110, 108, 124), 12))):
        pts = [(0, H)]
        for x in range(0, W + 8, 8):
            y = yb - abs(math.sin(x * 0.021 + layer * 1.3)) * amp - r.uniform(0, 3)
            pts.append((x, y))
        pts.append((W, H))
        d.polygon(pts, fill=col)
    # plateau (ground only to the right of the cliff edge)
    ground = Image.new("RGB", (W, H))
    C.dirt_ground(ground, 156, 60, "dawn", grass=0.25)
    ga = np.asarray(ground).astype(np.float32)
    g = ga.mean(-1, keepdims=True)
    ga = g + (ga - g) * 0.45                         # drained, cold colour
    ga *= np.array((0.86, 0.86, 0.9), np.float32)
    ground = Image.fromarray(np.clip(ga, 0, 255).astype(np.uint8), "RGB")
    mask = Image.new("L", (W, H), 0)
    edge = [(EDGE_X, 156), (W, 156), (W, H), (EDGE_X - 10, H), (EDGE_X - 6, 196), (EDGE_X - 2, 180), (EDGE_X - 4, 168)]
    ImageDraw.Draw(mask).polygon(edge, fill=255)
    im.paste(ground, (0, 0), mask)
    # cliff face
    face = [(EDGE_X, 156), (EDGE_X - 4, 168), (EDGE_X - 2, 180), (EDGE_X - 6, 196), (EDGE_X - 10, H),
            (EDGE_X - 22, H), (EDGE_X - 16, 198), (EDGE_X - 12, 178), (EDGE_X - 8, 164)]
    d.polygon(face, fill=(70, 62, 66), outline=INK)
    for yy in range(162, H, 7):
        d.line([(EDGE_X - 12 - (yy - 156) * 0.12, yy), (EDGE_X - 5 - (yy - 156) * 0.1, yy + 2)], fill=(100, 92, 94))
    d.line([(EDGE_X, 156), (W, 156)], fill=(120, 116, 118))
    return im


def cliff(img, t):
    img.paste(cached("cliff", _cliff_static), (0, 0))
    # drifting mist bands in the void and over the plateau
    d = ImageDraw.Draw(img)
    for i in range(5):
        r = rng("mist", i)
        y = r.uniform(120, 200)
        L = r.uniform(60, 140)
        x = (r.uniform(0, W) + t * r.uniform(4, 9)) % (W + L) - L
        col = (226, 222, 216) if i % 2 else (206, 202, 200)
        d.rectangle([x, y, x + L, y + 1], fill=col)


# ====================================================================== present sunset (F)
def _present_static():
    im = Image.new("RGB", (W, H))
    C.sky(im, "dusk", 0, horizon=150, body=False)
    sun_disc(im, 262, 120, 38, core=(255, 214, 150), rim=(246, 110, 70), glow=(240, 90, 70))
    C.far_mountains(im, 20, "dusk", y=150)
    C.dirt_ground(im, 158, 20, "dusk", grass=0.2)
    return im


def present(img, t):
    img.paste(cached("present", _present_static), (0, 0))
    C.clouds(img, t, 0, "dusk", seed=9, count=3, y0=20, y1=80, speed=0.7)


# ====================================================================== young Takasugi
_BAND = ((246, 246, 250), (196, 198, 216))
_TS_SKIN, _TS_SKIN_S, _TS_HAIR = (255, 224, 200), (232, 178, 152), (52, 38, 90)


def _unbandage(a, eye_rows=4):
    """In-place: turn the bandage pixels of a (facing-right) Takasugi head/sprite
    array into skin + hair and mirror the visible eye onto the freed side."""
    B = np.all(a[..., :3] == _BAND[0], axis=-1) & (a[..., 3] > 0)
    b = np.all(a[..., :3] == _BAND[1], axis=-1) & (a[..., 3] > 0)
    m = B | b
    if not m.any():
        return a
    ys, xs = np.nonzero(m)
    ox, oy = int(xs.min()) - 11, int(ys.min()) - 8
    rel = xs - ox
    for yy, xx, rc in zip(ys, xs, rel):
        if rc >= 15:
            a[yy, xx, :3] = _TS_HAIR
        elif B[yy, xx]:
            a[yy, xx, :3] = _TS_SKIN
        else:
            a[yy, xx, :3] = _TS_SKIN_S
    if oy + 10 + eye_rows <= a.shape[0] and ox + 15 <= a.shape[1] and ox >= 0 and oy >= 0:
        blk = a[oy + 10:oy + 10 + eye_rows, ox + 5:ox + 9].copy()
        a[oy + 10:oy + 10 + eye_rows, ox + 11:ox + 15] = blk
    return a


def takasugi_young(pose="idle", t=0.0, p=None, expr=None, facing=1, **kw):
    """Adult Takasugi sprite with BOTH eyes (Joui-war era, before the bandage).
    Returns (sprite, ax, ay) like chars.render_sprite. Do not pass rot."""
    spr, ax, ay = render_sprite("takasugi", pose, t, p, expr, 1, **kw)
    a = np.array(spr)
    # shouting mouths sit on row 13 -> only mirror the eye rows 10..12 then
    _unbandage(a, eye_rows=3 if expr in ("shout", "shock") else 4)
    spr = Image.fromarray(a, "RGBA")
    if facing < 0:
        spr = flip_h(spr)
        ax = spr.width - 1 - ax
    return spr, ax, ay


class _YoungTakasugiSpeaker:
    """Dialogue-only speaker id for the Joui-era Takasugi: same name / colour /
    voice as `takasugi`, but the subtitle portrait shows BOTH eyes (no bandage
    yet). Only used as a `subs` speaker; never drawn with draw_char."""
    id = "s11_takasugi_young"

    @staticmethod
    def _base():
        from chars import get_def
        return get_def("takasugi")

    @property
    def name(self):
        b = self._base()
        return b.name if b is not None else "高杉"

    @property
    def color(self):
        b = self._base()
        return b.color if b is not None else (146, 84, 182)

    @property
    def voice(self):
        return getattr(self._base(), "voice", 1.0)

    def head(self, expr):
        a = np.array(self._base().head(expr).convert("RGBA"))
        return Image.fromarray(_unbandage(a), "RGBA")

    def portrait_fn(self, expr, t, talking):
        e = expr or "normal"
        if talking and step_frame(t, 8) % 2 == 0:
            e = "talk" if expr in (None, "normal") else e
        elif expr is None and (t % 3.1) < 0.12:
            e = "blink"
        return cached(("tk_port", e), lambda: scale_nearest(self.head(e), 2))


TAKASUGI_YOUNG_SPK = _YoungTakasugiSpeaker.id
try:
    from chars import register as _register
    _register(_YoungTakasugiSpeaker())
except Exception:          # never break the scene over a portrait
    TAKASUGI_YOUNG_SPK = "takasugi"


def draw_takasugi_young(img, x, y, pose="idle", t=0.0, p=None, expr=None, facing=1, flash=0.0,
                        flash_color=(255, 255, 255), shadow=True, **kw):
    spr, ax, ay = takasugi_young(pose, t, p, expr, facing, **kw)
    if flash > 0:
        spr = tint(spr, flash_color, clamp(flash))
    x, y = int(round(x)), int(round(y))
    if shadow:
        from engine.gfx import overlay_rect
        overlay_rect(img, x - 6, y - 1, 12, 2, (0, 0, 0), 0.25)
    img.paste(spr, (x - ax, y - ay), spr)


# ====================================================================== misc props
def rope_bind(img, x, y, kneel=True, w=7):
    """Ropes around the torso of a kneeling adult captive (feet anchor x, y)."""
    x, y = int(round(x)), int(round(y))
    top = y - (9 if kneel else 15)           # keep the ropes below the (big) chibi chin
    for dy in (3, 7):
        yy = top + dy
        rect(img, x - w, yy + 1, 2 * w + 1, 1, (70, 50, 40))
        rect(img, x - w, yy, 2 * w + 1, 1, (176, 138, 86))
        for xx in range(x - w + 1, x + w, 3):
            rect(img, xx, yy, 1, 1, (120, 90, 58))


def tear_drop(img, x, y, size=1, color=(150, 210, 255)):
    x, y = int(x), int(y)
    if size <= 1:
        rect(img, x, y - 1, 1, 1, color)
        rect(img, x - 1, y, 3, 2, color)
        rect(img, x, y, 1, 1, (235, 248, 255))
    else:
        rect(img, x - 1, y - 3, 3, 1, INK)
        rect(img, x - 2, y - 2, 5, 5, INK)
        rect(img, x, y - 4, 1, 1, INK)
        rect(img, x, y - 3, 1, 1, color)
        rect(img, x - 1, y - 2, 3, 4, color)
        rect(img, x - 1, y - 1, 1, 1, (235, 248, 255))


def dizzy_stars(img, cx, cy, t, n=3, r=6, color=(255, 230, 90)):
    for i in range(n):
        a = t * 7 + i * 2 * math.pi / n
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.4
        rect(img, int(x) - 1, int(y), 3, 1, color)
        rect(img, int(x), int(y) - 1, 1, 3, color)


def sweat_drop(img, x, y, color=(120, 190, 255)):
    x, y = int(x), int(y)
    rect(img, x, y - 2, 1, 1, INK)
    rect(img, x - 1, y - 1, 3, 4, INK)
    rect(img, x, y - 1, 1, 3, color)
    rect(img, x - 1, y, 1, 2, color)
    rect(img, x + 1, y + 1, 1, 1, color)


def zzz(img, x, y, t):
    for i in range(3):
        u = ((t * 0.9 + i / 3) % 1.0)
        zx, zy = x + u * 10 + i, y - u * 14
        s = 1 if u < 0.5 else 2
        c = (255, 255, 255)
        if s == 1:
            rect(img, int(zx), int(zy), 3, 1, c)
            rect(img, int(zx) + 1, int(zy) + 1, 1, 1, c)
            rect(img, int(zx), int(zy) + 2, 3, 1, c)
        else:
            rect(img, int(zx), int(zy), 4, 1, c)
            rect(img, int(zx) + 2, int(zy) + 1, 1, 1, c)
            rect(img, int(zx) + 1, int(zy) + 2, 1, 1, c)
            rect(img, int(zx), int(zy) + 3, 4, 1, c)


def snot_bubble(img, x, y, r):
    if r <= 0:
        return
    d = ImageDraw.Draw(img)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(196, 232, 255), outline=(90, 150, 200))
    d.point((x - r // 2, y - r // 2), fill=(255, 255, 255))


def bump(img, x, y, r=3):
    d = ImageDraw.Draw(img)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 170, 160), outline=INK)
    d.point((x - 1, y - 1), fill=(255, 230, 220))


# ====================================================================== big tear
_TEAR = """
...o...
...o...
..oTo..
..oTo..
.oTTTo.
.oWTTo.
oWTTTTo
oTTTTTo
oTTTTTo
.oTTTo.
..ooo..
"""


def big_tear(img, x, y, k=2):
    """A single large tear drop, bottom-centre at (x, y), scaled xk."""
    s = cached(("tear", k), lambda: scale_nearest(ascii_sprite(_TEAR, {
        "o": (80, 120, 170), "T": (156, 204, 246), "W": (240, 250, 255)}), k))
    img.paste(s, (int(x) - s.width // 2, int(y) - s.height), s)


# ====================================================================== shadowed eyes
def draw_shadowed(img, cid, x, y, pose, t, facing=1, rows=(0, 0), soft=2, k=0.32, **kw):
    """Draw a rig character whose sprite rows [r0, r1) (canvas rows, facing-right
    render) are sunk into shadow — 'eyes hidden under the bangs'. `soft` rows
    above r0 get a dithered half-shadow."""
    spr, ax, ay = render_sprite(cid, pose, t, None, kw.pop("expr", None), 1, **kw)
    a = np.asarray(spr).astype(np.float32)
    r0, r1 = rows
    ink = np.all(a[..., :3] == np.array(INK, np.float32), axis=-1)
    m = np.zeros(a.shape[:2], np.float32)
    m[r0:r1] = 1.0
    by = C.bayer(soft, a.shape[1])
    m[r0 - soft:r0] = (by < 0.5).astype(np.float32)
    f = 1 - (1 - k) * m
    f[ink] = 1.0
    a[..., :3] *= f[..., None]
    a[..., 0] += 10 * m
    a[..., 2] += 18 * m * (a[..., 3] > 0)
    spr = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    if facing < 0:
        spr = flip_h(spr)
        ax = spr.width - 1 - ax
    overlay_rect_(img, int(x) - 6, int(y) - 1, 12, 2, (0, 0, 0), 0.25)
    img.paste(spr, (int(x) - ax, int(y) - ay), spr)


def ghost_face(img, cid, expr, cx, cy, k, alpha, color=(196, 170, 140)):
    """Faint memory after-image: a character's head, scaled xk, flattened to
    one tone and blended at `alpha` (centre at cx, cy)."""
    if alpha <= 0.01:
        return
    def mk():
        h = get_def(cid).head(expr)
        a = np.asarray(h).astype(np.float32)
        lum = (a[..., :3] @ np.array([0.3, 0.59, 0.11], np.float32)) / 255.0
        out = np.zeros_like(a)
        out[..., :3] = np.array(color, np.float32)[None, None, :] * (0.2 + 0.8 * lum[..., None])
        out[..., 3] = a[..., 3]
        return scale_nearest(Image.fromarray(out.astype(np.uint8), "RGBA"), k)
    s = cached(("ghost", cid, expr, k, color), mk)
    s = set_alpha(s, alpha)
    img.paste(s, (int(cx) - s.width // 2, int(cy) - s.height // 2), s)


# ====================================================================== small props (review pass)
def sheathed_sword(img, cx, cy, ang=0.0, L=22, color=(66, 50, 62), hilt=(206, 204, 214)):
    """Sheathed katana centred at (cx, cy); `ang` = direction of the HILT in
    screen degrees (0 = hilt to the right, 90 = hilt up)."""
    a = math.radians(ang)
    vx, vy = math.cos(a), -math.sin(a)
    p0 = (cx - vx * L / 2, cy - vy * L / 2)          # tip end
    p1 = (cx + vx * L / 2, cy + vy * L / 2)          # hilt end
    g = (p1[0] - vx * 6, p1[1] - vy * 6)
    stamp_line(img, p0, p1, 4, INK)
    stamp_line(img, p0, g, 2, color)
    stamp_line(img, (p0[0] + vx * 2, p0[1] + vy * 2), (g[0] - vx * 2, g[1] - vy * 2), 1, shade(color, 1.7))
    stamp_line(img, (g[0] + vx, g[1] + vy), p1, 2, hilt)
    px, py = -vy, vx
    stamp_line(img, (g[0] - px * 2.5, g[1] - py * 2.5), (g[0] + px * 2.5, g[1] + py * 2.5), 3, INK)
    stamp_line(img, (g[0] - px * 2, g[1] - py * 2), (g[0] + px * 2, g[1] + py * 2), 1, (232, 184, 70))


def rice_ball(img, x, y):
    """Tiny onigiri, bottom-centre at (x, y)."""
    x, y = int(x), int(y)
    rect(img, x - 2, y - 4, 5, 4, INK)
    rect(img, x - 1, y - 5, 3, 1, INK)
    rect(img, x - 1, y - 4, 3, 2, (252, 252, 244))
    rect(img, x, y - 5 + 1, 1, 1, (255, 255, 255))
    rect(img, x - 1, y - 2, 3, 1, (40, 64, 50))


def dark_aura(img, cid, x, y, pose, t, facing=1, amt=1.0, color=(58, 34, 74), **kw):
    """Flickering dark 'menacing smile' aura: tinted silhouette copies of the
    character jittering 1-2 px around it (draw BEFORE the character)."""
    if amt <= 0:
        return
    p = kw.pop("p", None)
    rot = kw.pop("rot", 0)
    spr, ax, ay = render_sprite(cid, pose, t, p, None, facing, rot=rot, **kw)
    sil = tint(spr, color, 1.0)
    sil = set_alpha(sil, 0.8 * amt)
    f = step_frame(t, 12)
    x, y = int(round(x)), int(round(y))
    r = 2 + (f % 2)
    for dx, dy in ((-r, 0), (r, 0), (0, -r - 1), (-r + 1, -r), (r - 1, -r)):
        img.paste(sil, (x - ax + dx, y - ay + dy), sil)
    d = ImageDraw.Draw(img)
    for i in range(4):                               # rising wisps
        rr = rng("aura", i)
        u = ((t * 1.6 + rr.uniform(0, 1)) % 1.0)
        wx = x + rr.uniform(-9, 9)
        wy = y - 10 - u * 26
        if amt > 0.5:
            d.line([(wx, wy), (wx + math.sin(u * 9 + i), wy - 3)], fill=color)
