"""Private art/helpers for s07 红樱篇 (owned by the s07 scene agent).

Camera helpers (clamped zoom + world->screen mapping), silhouettes, the cut
lock of Katsura's hair, Benizakura shards/tendrils, lightning, rain splashes,
golden butterflies, and the two Kiheitai-ship sets (outer hull + rail for
Takasugi, main deck for the Harusame brawl). Everything is a pure function
of its arguments; static layers are cached at module level.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import W, H, clamp, lerp, rng, wave, step_frame, seg, ease_out
from engine.gfx import INK, stamp_line, rect, shade, mix, outline, rotate_nearest, set_alpha, scale_nearest
from engine import fx
from bg import common as C, edo as E
from chars import render_sprite

_cache = {}


def cached(key, fn):
    v = _cache.get(key)
    if v is None:
        v = fn()
        _cache[key] = v
    return v


# ------------------------------------------------------------------ camera
def zoom_at(img, k, cx, cy):
    """fx.zoom about (cx, cy) with the centre clamped so the crop box stays
    inside the canvas. Returns the camera tuple (k, cx, cy) actually used."""
    if k <= 1.0005:
        return (1.0, W / 2, H / 2)
    hw, hh = W / k / 2 + 0.01, H / k / 2 + 0.01
    cx = min(max(cx, hw), W - hw)
    cy = min(max(cy, hh), H - hh)
    fx.zoom(img, k, cx, cy)
    return (k, cx, cy)


def cam_clamp(k, cx, cy):
    if k <= 1.0005:
        return (1.0, W / 2, H / 2)
    hw, hh = W / k / 2 + 0.01, H / k / 2 + 0.01
    return (k, min(max(cx, hw), W - hw), min(max(cy, hh), H - hh))


def new_layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def zoom_layer(img, layer, k, cx, cy):
    """Zoom an RGBA layer about (cx, cy) (clamped) and composite it onto img.
    Lets far layers (sky, moon) stay crisp while near layers get the close-up."""
    cam = cam_clamp(k, cx, cy)
    k, cx, cy = cam
    if k > 1.0005:
        w, h = W / k, H / k
        layer = layer.resize((W, H), Image.NEAREST, box=(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
    img.paste(layer, (0, 0), layer)
    return cam


def silhouette_layer(layer, color=INK):
    """Flat-colour copy of an RGBA layer (impact-frame silhouettes)."""
    a = np.asarray(layer).copy()
    m = a[..., 3] > 0
    a[m, 0], a[m, 1], a[m, 2] = color[0], color[1], color[2]
    a[m, 3] = 255
    return Image.fromarray(a, "RGBA")


def to_screen(cam, x, y):
    k, cx, cy = cam
    return (x - cx) * k + W / 2, (y - cy) * k + H / 2


# ------------------------------------------------------------------ sprites
def paste_char(img, spr, ax, ay, x, y, alpha=1.0):
    if alpha < 1:
        spr = set_alpha(spr, alpha)
    img.paste(spr, (int(round(x - ax)), int(round(y - ay))), spr)


def shadowed(spr, body=(18, 14, 30), rim=(150, 140, 196), rim_dir=1, keep_red=True):
    """Backlit silhouette: flat dark body, 1px rim light on the side facing the
    light (rim_dir +1 = light on the right), red (Benizakura) pixels kept."""
    a = np.asarray(spr)
    alpha = a[..., 3] > 0
    out = np.zeros_like(a)
    out[alpha] = (body[0], body[1], body[2], 255)
    nb = np.zeros_like(alpha)
    if rim_dir > 0:
        nb[:, :-1] = alpha[:, 1:]
    else:
        nb[:, 1:] = alpha[:, :-1]
    up = np.zeros_like(alpha)
    up[1:, :] = alpha[:-1, :]
    edge = alpha & (~nb | ~up)
    out[edge] = (rim[0], rim[1], rim[2], 255)
    if keep_red:
        red = alpha & (a[..., 0] > 150) & (a[..., 1] < 100) & (a[..., 2] < 120)
        out[red] = a[red]
    return Image.fromarray(out, "RGBA")


def draw_shadow_char(img, cid, x, y, pose, t, p=None, facing=1, rim_dir=1, **kw):
    spr, ax, ay = render_sprite(cid, pose, t, p, None, facing, **kw)
    paste_char(img, shadowed(spr, rim_dir=rim_dir), ax, ay, x, y)


def afterimages(img, cid, x0, x1, y, pose, t, p=None, facing=1, n=3, expr=None, tint_col=(170, 200, 255), **kw):
    """Crisp flat-colour ghost copies between x0 (oldest) and x1 (current) for
    dashes: solid silhouettes with stepped opacity (no muddy smear)."""
    spr, ax, ay = render_sprite(cid, pose, t, p, expr, facing, **kw)
    sil = silhouette_layer(spr, tint_col)
    span = abs(x1 - x0)
    n = max(1, min(n, int(span // 14)))          # never stack ghosts on top of each other
    for i in range(n):
        k = (i + 1) / (n + 1)
        paste_char(img, sil, ax, ay, lerp(x0, x1, k), y, alpha=0.2 + 0.4 * k)


# ------------------------------------------------------------------ Katsura's hair lock
_HAIR = [(30, 28, 48), (42, 42, 68), (60, 62, 94), (112, 120, 166)]


def _hair_lock():
    """A lock of long straight black hair: S-curved tapered ribbon with a
    glossy sheen, two stray wisps at the tip and a clean sword-cut top."""
    im = Image.new("RGBA", (16, 34), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    L = 30

    def c(v):
        return 7.5 + math.sin(v * 3.6 + 0.3) * 2.2 * v, 1 + v * L

    def hw(v):
        return 3.6 * (1 - v) ** 0.8 + 0.4
    n = 24
    left, right = [], []
    for j in range(n + 1):
        v = j / n
        x, y = c(v)
        left.append((x - hw(v), y))
        right.append((x + hw(v), y))
    d.polygon(left + right[::-1], fill=_HAIR[1])
    for off in (-0.35, 0.4):                                   # strand grooves
        d.line([(c(j / n)[0] + off * hw(j / n) * 1.6, c(j / n)[1]) for j in range(3, n - 3)], fill=_HAIR[0])
    d.line([(c(j / n)[0] - hw(j / n) * 0.55, c(j / n)[1]) for j in range(2, int(n * 0.55))], fill=_HAIR[3])
    d.line([(c(j / n)[0] + hw(j / n) * 0.3, c(j / n)[1]) for j in range(3, int(n * 0.4))], fill=_HAIR[2])
    for sgn, v0, ln in ((-1, 0.55, 9), (1, 0.66, 8)):          # stray wisps
        x, y = c(v0)
        x0 = x + sgn * hw(v0) * 0.8
        d.line([(x0 + sgn * (2.5 * u + 1.2 * u * u), y + ln * u) for u in (k / 5 for k in range(6))],
               fill=_HAIR[1])
    x, y = c(0)
    d.line([(x - hw(0), 1), (x + hw(0), 1)], fill=(206, 208, 236))   # clean sword-cut end
    d.line([(x - hw(0) + 1, 2), (x + hw(0) - 1, 2)], fill=_HAIR[2])
    return outline(im)


def hair_lock(img, x, y, ang=0):
    """Cut lock of long black hair, top (cut end) centred at (x, y)."""
    spr = cached(("hair", int(ang) // 6), lambda: rotate_nearest(_hair_lock(), (int(ang) // 6) * 6))
    img.paste(spr, (int(x - spr.width / 2), int(y - spr.height / 2)), spr)


# ------------------------------------------------------------------ effects
RED_PETALS = ((228, 59, 68), (255, 120, 130), (170, 30, 52))


def red_petals(img, t, count=18, seed=3, area=(0, 0, W, H), wind=26.0, fall=16.0):
    fx.sakura(img, t, count=count, seed=seed, colors=RED_PETALS, wind=wind, fall=fall, area=area)


def bolt(img, seed, x=None, y1=150, color=(250, 250, 255), glow=(170, 180, 255)):
    r = rng("s07bolt", seed)
    x = r.randint(60, W - 60) if x is None else x
    y = -2
    pts = [(x, y)]
    branch = None
    while y < y1:
        y += r.randint(6, 14)
        x += r.randint(-10, 10)
        pts.append((x, y))
        if branch is None and y > 40 and r.random() < 0.35:
            branch = [(x, y)]
            bx, by = x, y
            for _ in range(4):
                by += r.randint(5, 10)
                bx += r.choice((-1, 1)) * r.randint(4, 9)
                branch.append((bx, by))
    d = ImageDraw.Draw(img)
    d.line(pts, fill=glow, width=3)
    d.line(pts, fill=color, width=1)
    if branch:
        d.line(branch, fill=glow, width=1)


def lightning_amount(t, t0):
    """Flash envelope for a lightning strike at t0 (double flicker)."""
    dt = t - t0
    if dt < 0 or dt > 0.45:
        return 0.0
    seq = (1.0, 0.3, 0.85, 0.45, 0.25, 0.12, 0.05)
    return seq[min(len(seq) - 1, int(dt * 15))]


def rain_splashes(img, t, y0, y1, count=26, seed=0, color=(170, 180, 220)):
    """Tiny analytic splash crowns on the ground between rows y0..y1."""
    d = ImageDraw.Draw(img)
    for i in range(count):
        r = rng("s07splash", seed, i)
        per = r.uniform(0.35, 0.7)
        off = r.random()
        ph = (t / per + off) % 1.0
        k = int((t / per + off) // 1)
        rr = rng("s07splash2", seed, i, k)
        x = rr.uniform(0, W)
        y = rr.uniform(y0, y1)
        if ph < 0.12:
            d.point((x, y), fill=color)
        elif ph < 0.26:
            d.point([(x - 1, y - 1), (x + 1, y - 1)], fill=color)
        elif ph < 0.36:
            d.point([(x - 2, y - 1), (x + 2, y - 1)], fill=shade(color, 0.75))


def shards(img, t, t0, x, y, n=12, seed=0, dirx=-1, life=1.0):
    """Benizakura blade fragments: small spinning red slivers flying outward."""
    dt = t - t0
    if dt < 0 or dt > life:
        return
    d = ImageDraw.Draw(img)
    cols = ((255, 190, 190), (228, 40, 60), (160, 20, 40), (255, 110, 120))
    for i in range(n):
        r = rng("s07shard", seed, i)
        a = math.radians(r.uniform(-150, -30) if r.random() < 0.8 else r.uniform(0, 360))
        v = r.uniform(50, 150)
        vx, vy = math.cos(a) * v, math.sin(a) * v
        vx = abs(vx) * dirx * (1 if r.random() < 0.75 else -1)
        px = x + vx * dt
        py = y + vy * dt + 0.5 * 220 * dt * dt
        L = r.uniform(2, 4)
        spin = r.uniform(8, 20) * dt + r.uniform(0, 6)
        ex, ey = px + math.cos(spin) * L, py + math.sin(spin) * L
        c = cols[i % len(cols)]
        if dt > life * 0.7 and (i + int(dt * 20)) % 2:
            continue
        d.line([(px, py), (ex, ey)], fill=c, width=1)


def tendrils(img, x0, y0, x1, y1, t, n=3, amp=4.0, grow=1.0, seed=0, width=1):
    """Writhing Benizakura tendrils from (x0,y0) reaching toward (x1,y1)."""
    if grow <= 0:
        return
    tq = step_frame(t, 12) / 12.0
    L = math.hypot(x1 - x0, y1 - y0) or 1
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    for j in range(n):
        r = rng("s07tend", seed, j)
        ph = r.uniform(0, 6.28)
        sp = r.uniform(0.7, 1.2)
        pts = []
        m = 10
        for i in range(m + 1):
            u = i / m * grow * sp
            w = math.sin(u * 7 + ph + tq * 9) * amp * u * (1 + j * 0.3)
            pts.append((x0 + (x1 - x0) * u + nx * w + (j - 1) * 2 * u,
                        y0 + (y1 - y0) * u + ny * w + (j - 1) * 3 * u))
        for a, b in zip(pts, pts[1:]):
            stamp_line(img, a, b, width + 2, INK)
        pulse = step_frame(t, 10, 4)
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            stamp_line(img, a, b, width, (255, 90, 100) if (i + pulse) % 4 == 0 else (200, 30, 50))


def butterfly(img, x, y, t, phase=0.0, color=(250, 206, 72)):
    """Tiny golden butterfly (Takasugi motif), flapping at ~8 fps."""
    f = step_frame(t + phase, 8, 3)
    d = ImageDraw.Draw(img)
    x, y = int(x), int(y)
    dark = shade(color, 0.6)
    if f == 0:
        d.point([(x - 2, y - 1), (x - 1, y - 1), (x + 1, y - 1), (x + 2, y - 1), (x - 1, y), (x + 1, y)], fill=color)
        d.point([(x - 2, y), (x + 2, y)], fill=dark)
    elif f == 1:
        d.point([(x - 1, y - 2), (x - 1, y - 1), (x + 1, y - 2), (x + 1, y - 1)], fill=color)
    else:
        d.point([(x - 2, y - 2), (x - 1, y - 1), (x + 2, y - 2), (x + 1, y - 1)], fill=color)
        d.point([(x - 1, y), (x + 1, y)], fill=dark)
    d.point((x, y - 1), fill=(60, 40, 30))
    d.point((x, y), fill=(60, 40, 30))


def spin_ring(img, cx, cy, rx, ry, p, a0=-90.0, color=(255, 255, 255), glow=(150, 200, 255), width=3):
    """Horizontal spin-slash ring (ellipse) swept by progress p (0..~1.4)."""
    if p <= 0:
        return
    head = a0 + 360 * min(1.0, p)
    tail = a0 + 360 * max(0.0, (p - 0.35) * 1.5)
    if head - tail < 2:
        return
    d = ImageDraw.Draw(img)
    n = 48
    pts = []
    for i in range(n + 1):
        a = math.radians(tail + (head - tail) * i / n)
        pts.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        k = i / n
        wdt = max(1, int(round(width * (0.3 + 0.7 * k))))
        d.line([a, b], fill=glow, width=wdt + 2)
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        k = i / n
        wdt = max(1, int(round(width * (0.3 + 0.7 * k))))
        d.line([a, b], fill=color, width=wdt)


def fall_streaks(img, x, y, t, n=4, length=26, color=(230, 236, 255), seed=0):
    d = ImageDraw.Draw(img)
    for i in range(n):
        r = rng("s07fs", seed, i, int(t * 15))
        xx = x + r.uniform(-9, 9)
        yy = y - r.uniform(20, 40)
        d.line([(xx, yy), (xx, yy - length * r.uniform(0.6, 1.2))], fill=color)


def _vein_sprite():
    """Manga anger mark: four arcs whose bulge points at the centre (each arc is
    centred on an outer corner), leaving a cross-shaped gap between them."""
    n = 15
    c = n // 2
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    R = 6
    for sx in (-1, 1):
        for sy in (-1, 1):
            ox, oy = c + sx * (c + 1), c + sy * (c + 1)
            a0 = {(1, 1): 180, (-1, 1): 270, (-1, -1): 0, (1, -1): 90}[(sx, sy)]
            d.arc([ox - R, oy - R, ox + R, oy + R], a0 + 8, a0 + 82, fill=(236, 40, 56), width=2)
            d.arc([ox - R + 1, oy - R + 1, ox + R - 1, oy + R - 1], a0 + 14, a0 + 76, fill=(255, 130, 130), width=1)
    return scale_nearest(outline(im), 2)


def vein(img, x, y, size=None):
    """Manga anger mark (four bulging corner arcs), centred at (x, y)."""
    spr = cached(("vein",), _vein_sprite)
    img.paste(spr, (int(x - spr.width / 2), int(y - spr.height / 2)), spr)


def diag_slash(img, p0, p1, width=5, color=(255, 255, 255), edge=INK):
    """Huge straight slash stroke (tapered) across the frame."""
    d = ImageDraw.Draw(img)
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0) or 1
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    poly = [(x0, y0), (mx + nx * width, my + ny * width), (x1, y1), (mx - nx * width, my - ny * width)]
    if edge is not None:
        d.polygon([(x0 - (x1 - x0) / L * 3, y0 - (y1 - y0) / L * 3),
                   (mx + nx * (width + 2), my + ny * (width + 2)),
                   (x1 + (x1 - x0) / L * 3, y1 + (y1 - y0) / L * 3),
                   (mx - nx * (width + 2), my - ny * (width + 2))], fill=edge)
    d.polygon(poly, fill=color)


# ------------------------------------------------------------------ night city far below
def _far_lights(tod):
    im = Image.new("RGBA", (W + 256, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = rng("s07city")
    base = C.grade_color((70, 64, 96), tod, 0.5)
    x = 0
    while x < im.width:
        w = r.randint(8, 22)
        h = r.randint(4, 18)
        d.rectangle([x, 40 - h, x + w, 40], fill=base)
        for _ in range(r.randint(0, 4)):
            wx, wy = r.randint(x + 1, x + w - 1), r.randint(40 - h + 2, 39)
            d.point((wx, wy), fill=(255, 214, 140) if r.random() < 0.8 else (150, 200, 255))
        x += w + r.randint(0, 3)
    return im


def far_city(img, cam_x, y, tod="night"):
    lay = cached(("farcity", tod), lambda: _far_lights(tod))
    off = int(cam_x * 0.15) % 256
    c = lay.crop((off, 0, off + W, 40))
    img.paste(c, (0, int(y) - 40), c)


# ------------------------------------------------------------------ Kiheitai ship: long rail
RAIL_W, RAIL_L, RAIL_D, RAIL_M = (112, 74, 52), (156, 108, 72), (70, 44, 34), (92, 60, 44)


def _rail_strip(n=W + 64):
    """Matches the railing drawn by takasugi's sit_rail pose (14 px tall)."""
    im = Image.new("RGBA", (n, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    top = 1
    d.rectangle([0, 13, n - 1, 15], fill=INK)
    d.line([(0, 14), (n - 1, 14)], fill=RAIL_D)
    for px in range(2, n, 6):
        d.rectangle([px - 1, top + 2, px + 2, top + 12], fill=INK)
        d.rectangle([px, top + 3, px + 1, top + 11], fill=RAIL_D)
        d.point((px, top + 6), fill=RAIL_W)
    d.rectangle([0, top - 1, n - 1, top + 3], fill=INK)
    d.line([(0, top), (n - 1, top)], fill=RAIL_L)
    d.line([(0, top + 1), (n - 1, top + 1)], fill=RAIL_W)
    d.line([(0, top + 2), (n - 1, top + 2)], fill=RAIL_M)
    return im


def long_rail(img, y_top, cam_x=0):
    """Ship railing across the whole screen, rail top at y_top."""
    s = cached(("rail",), _rail_strip)
    off = int(cam_x) % 6
    img.paste(s, (-off - 6, int(y_top) - 1), s)


def _hull_strip():
    w, h = W + 96, 80
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    wood, wood_d, wood_l = (58, 40, 44), (40, 28, 34), (84, 58, 56)
    d.rectangle([0, 0, w, h], fill=wood)
    for y in range(4, h, 6):
        d.line([(0, y), (w, y)], fill=wood_d)
        d.line([(0, y + 1), (w, y + 1)], fill=wood_l)
    r = rng("s07hull")
    for y in range(4, h, 6):
        for x in range(r.randint(0, 30), w, r.randint(28, 50)):
            d.line([(x, y + 2), (x, y + 5)], fill=wood_d)
    # gold trim band + purple lacquer stripe
    d.rectangle([0, 0, w, 3], fill=(30, 22, 30))
    d.line([(0, 1), (w, 1)], fill=(196, 150, 60))
    d.rectangle([0, 14, w, 19], fill=(66, 40, 86))
    d.line([(0, 14), (w, 14)], fill=(110, 78, 140))
    d.line([(0, 19), (w, 19)], fill=(30, 22, 30))
    # round portholes (lit)
    for x in range(20, w, 48):
        d.ellipse([x - 5, 28, x + 5, 38], fill=INK)
        d.ellipse([x - 4, 29, x + 4, 37], fill=(196, 150, 60))
        d.ellipse([x - 3, 30, x + 3, 36], fill=(255, 214, 130))
        d.point((x - 1, 31), fill=(255, 250, 220))
    return im


def hull(img, y, cam_x=0, t=0.0):
    s = cached(("hull",), _hull_strip)
    off = int(cam_x) % 48
    img.paste(s, (-off - 24, int(y)), s)
    # porthole glow flicker
    d = ImageDraw.Draw(img)
    for i, x in enumerate(range(20, W + 96, 48)):
        sx = x - off - 24
        if (step_frame(t, 3) + i) % 5 == 0:
            d.point((sx + 1, int(y) + 34), fill=(255, 240, 200))


# ------------------------------------------------------------------ Kiheitai ship: main deck set
def _mast_sprite():
    w, h = 90, 200
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = 45
    # furled sail on the yard
    d.rectangle([cx - 42, 30, cx + 42, 37], fill=INK)
    d.rectangle([cx - 41, 31, cx + 41, 36], fill=(206, 196, 176))
    for x in range(cx - 38, cx + 40, 7):
        d.line([(x, 31), (x + 2, 36)], fill=(160, 150, 136))
    d.line([(cx - 41, 36), (cx + 41, 36)], fill=(150, 140, 126))
    # mast pole
    d.rectangle([cx - 4, 0, cx + 4, h], fill=INK)
    d.rectangle([cx - 3, 0, cx + 3, h], fill=(96, 64, 46))
    d.line([(cx - 2, 0), (cx - 2, h)], fill=(136, 94, 64))
    d.line([(cx + 2, 0), (cx + 2, h)], fill=(70, 46, 36))
    for y in range(50, h, 30):   # iron bands
        d.rectangle([cx - 4, y, cx + 4, y + 2], fill=(40, 36, 44))
    # crow's nest
    d.rectangle([cx - 10, 6, cx + 10, 13], fill=INK)
    d.rectangle([cx - 9, 7, cx + 9, 12], fill=(96, 64, 46))
    d.line([(cx - 9, 9), (cx + 9, 9)], fill=(70, 46, 36))
    return im


def _flag_frames():
    frames = []
    for f in range(4):
        im = Image.new("RGBA", (30, 20), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        pts_top, pts_bot = [], []
        for x in range(0, 29):
            wv = math.sin(x * 0.35 - f * 1.57) * (x / 28) * 2.2
            pts_top.append((x, 2 + wv))
            pts_bot.append((x, 16 + wv - x * 0.12))
        poly = pts_top + pts_bot[::-1]
        d.polygon(poly, fill=INK)
        inner = [(x, y + 1) for x, y in pts_top[:-1]] + [(x, y - 1) for x, y in pts_bot[:-1][::-1]]
        d.polygon(inner, fill=(110, 60, 150))
        # white butterfly-ish crest
        cy = 9 + math.sin(12 * 0.35 - f * 1.57) * 0.9
        d.point([(11, cy - 2), (12, cy - 1), (13, cy - 2), (12, cy), (11, cy + 1), (13, cy + 1),
                 (10, cy - 1), (14, cy - 1)], fill=(236, 230, 240))
        frames.append(im)
    return frames


def mast(img, x, t, top=0):
    spr = cached(("mast",), _mast_sprite)
    img.paste(spr, (int(x) - 45, int(top)), spr)
    fr = cached(("flag",), _flag_frames)[step_frame(t, 8, 4)]
    img.paste(fr, (int(x) + 3, int(top) - 16), fr)
    d = ImageDraw.Draw(img)
    d.line([(int(x) + 3, int(top) - 18), (int(x) + 3, int(top) + 2)], fill=INK)


def rigging(img, x, top, y_left, y_right, color=(40, 32, 40), right=True):
    d = ImageDraw.Draw(img)
    d.line([(x, top + 8), (-10, y_left)], fill=color)
    d.line([(x, top + 40), (x - 140, y_left + 6)], fill=color)
    if right:
        d.line([(x, top + 8), (W + 10, y_right)], fill=color)
        d.line([(x, top + 40), (x + 150, y_right + 6)], fill=color)


def deck_world(img, t, cam_x=0.0, moon=(300, 46, 22), ships=True, mast_x=None, lanterns=True, right=True):
    """Night main deck of the Kiheitai ship. Floor (feet) at y=160."""
    tod = "night"
    C.sky(img, tod, t, horizon=150, body=False)
    if moon:
        C.big_moon(img, moon[0] - cam_x * 0.03, moon[1], moon[2])
    C.clouds(img, t, cam_x, tod, seed=11, count=6, y0=10, y1=70, speed=2.5)
    if ships:
        E.ship(img, (70 - cam_x * 0.1 + t * 3) % (W + 140) - 70, 52 + wave(t, 0.3, 2), "pirate", t, tod=tod, haze=0.45)
    far_city(img, cam_x, 140, tod)
    mx = (230 if mast_x is None else mast_x) - cam_x * 0.85
    rigging(img, mx, -10, 128, 132, right=right)
    mast(img, mx, t, top=-10)
    long_rail(img, 131, cam_x)
    rect(img, 0, 146, W, 6, (44, 30, 36))          # bulwark shadow line
    rect(img, 0, 146, W, 1, (70, 50, 52))
    C.wood_floor(img, 152, cam_x, tod)
    if lanterns:
        d = ImageDraw.Draw(img)
        # rope from the mast to the frame edges with lanterns
        for side, ex in (((-1, -20), (1, W + 20)) if right else ((-1, -20),)):
            pts = []
            for i in range(9):
                u = i / 8
                xx = lerp(mx, ex, u)
                yy = lerp(26, 20, u) + math.sin(u * math.pi) * 18
                pts.append((xx, yy))
            d.line(pts, fill=(34, 26, 32))
            for u in (0.3, 0.6, 0.88):
                xx = lerp(mx, ex, u)
                yy = lerp(26, 20, u) + math.sin(u * math.pi) * 18
                C.lantern(img, xx, yy, t, C.RED if side < 0 else C.YELLOW, tod, size=1, swing=1.6)


def upper_deck(img, x0, y_top, t, cam_x=0):
    """Raised quarterdeck on the right (Takasugi's vantage): top at y_top."""
    d = ImageDraw.Draw(img)
    x0 = int(x0 - cam_x)
    # front wall
    d.rectangle([x0, y_top, W + 4, 160], fill=INK)
    d.rectangle([x0 + 1, y_top + 4, W + 4, 158], fill=(58, 40, 44))
    for y in range(y_top + 8, 158, 6):
        d.line([(x0 + 1, y), (W, y)], fill=(40, 28, 34))
        d.line([(x0 + 1, y + 1), (W, y + 1)], fill=(80, 56, 54))
    d.rectangle([x0 + 1, y_top + 1, W + 4, y_top + 3], fill=(96, 64, 46))
    d.line([(x0 + 1, y_top + 1), (W, y_top + 1)], fill=(140, 98, 66))
    # stairs going up on the left of the wall
    for i in range(6):
        sx = x0 - 6 - i * 6
        sy = y_top + 6 + i * 8
        d.rectangle([sx, sy, sx + 8 + i * 6, sy + 3], fill=INK)
        d.rectangle([sx + 1, sy + 1, sx + 7 + i * 6, sy + 2], fill=(110, 76, 52))
    # lantern + emblem panel
    d.rectangle([x0 + 30, y_top + 12, x0 + 60, y_top + 34], fill=INK)
    d.rectangle([x0 + 31, y_top + 13, x0 + 59, y_top + 33], fill=(70, 44, 90))
    fx_ = x0 + 45
    fy_ = y_top + 23
    d.point([(fx_ - 3, fy_ - 3), (fx_ - 2, fy_ - 2), (fx_ - 1, fy_ - 1), (fx_ + 3, fy_ - 3), (fx_ + 2, fy_ - 2),
             (fx_ + 1, fy_ - 1), (fx_, fy_), (fx_ - 2, fy_ + 2), (fx_ + 2, fy_ + 2), (fx_ - 1, fy_ + 1),
             (fx_ + 1, fy_ + 1), (fx_ - 3, fy_ - 2), (fx_ + 3, fy_ - 2)], fill=(250, 206, 72))
    C.lantern(img, x0 + 12, y_top + 6, t, C.RED, "night", size=1)
    C.lantern(img, x0 + 80, y_top + 6, t, C.RED, "night", size=1)


# ------------------------------------------------------------------ name card with a custom tag
def name_card_tag(img, t, t0, dur, color, title, desc="", tag="", side="left", y=22):
    """Same look as engine.text.name_card, but the small grey tag after the big
    name is given explicitly (engine's card repeats the def name, which for
    okada_nizo equals the title -> '冈田似藏 冈田似藏')."""
    from engine.text import draw_text, text_width, typed
    if not (t0 <= t < t0 + dur):
        return
    p = t - t0
    slide = ease_out(seg(p, 0, 0.3)) * (1 - ease_out(seg(p, dur - 0.25, dur)))
    bh, y0 = 50, y
    d = ImageDraw.Draw(img)
    off = int((1 - slide) * (W + 40))
    if side == "right":
        xs = 150 + off
        d.polygon([(xs, y0), (W + 5, y0), (W + 5, y0 + bh), (xs - 16, y0 + bh)], fill=tuple(INK))
        d.polygon([(xs + 3, y0 + 3), (W + 5, y0 + 3), (W + 5, y0 + bh - 3), (xs - 13, y0 + bh - 3)], fill=tuple(color))
        d.polygon([(xs + 8, y0 + bh - 12), (W + 5, y0 + bh - 12), (W + 5, y0 + bh - 3), (xs - 9, y0 + bh - 3)],
                  fill=tuple(INK))
        tx = xs + 8
    else:
        xe = W - 150 - off
        d.polygon([(-5, y0), (xe + 16, y0), (xe, y0 + bh), (-5, y0 + bh)], fill=tuple(INK))
        d.polygon([(-5, y0 + 3), (xe + 13, y0 + 3), (xe - 3, y0 + bh - 3), (-5, y0 + bh - 3)], fill=tuple(color))
        d.polygon([(-5, y0 + bh - 12), (xe + 1, y0 + bh - 12), (xe - 3, y0 + bh - 3), (-5, y0 + bh - 3)],
                  fill=tuple(INK))
        tx = 12 - off
    draw_text(img, tx, y0 + 6, title, (255, 255, 255), size=16, outline=INK)
    if desc:
        draw_text(img, tx + 2, y0 + bh - 12, typed(desc, t, t0 + 0.35, cps=24), (255, 236, 150), size=12)
    if tag:
        draw_text(img, tx + text_width(title, 16) + 8, y0 + 10, tag, (30, 24, 40), size=12)


# ------------------------------------------------------------------ kiseru smoke
def pipe_smoke(img, x, y, t, n=7, rise=11.0, drift=-7.0, life=1.6, seed=0, color=(196, 192, 214)):
    """Thin curling kiseru smoke rising from (x, y) and drifting with the wind."""
    d = ImageDraw.Draw(img)
    for i in range(n):
        r = rng("s07smoke", seed, i)
        ph = ((t / life) + i / n + r.random() * 0.1) % 1.0
        age = ph * life
        px = x + drift * age + math.sin(age * 3.2 + i) * (1 + 2.2 * ph)
        py = y - rise * age
        sz = 1 if ph < 0.35 else 2 if ph < 0.8 else 1
        if ph > 0.85 and (i + step_frame(t, 10)) % 2:
            continue
        c = color if ph < 0.6 else shade(color, 0.8)
        d.rectangle([int(px), int(py), int(px) + sz - 1, int(py) + (1 if sz > 1 else 0)], fill=c)


# ------------------------------------------------------------------ foreground mob silhouettes
def fg_silhouette(img, cid, x, y, pose, t, scale=2, facing=1, color=(12, 10, 22), p=None, rim=(96, 80, 132), **kw):
    """Big dark foreground figure (screen space) framing a shot: flat body, rim
    light on the side facing the centre, red details (crest, eyes) kept."""
    spr, ax, ay = render_sprite(cid, pose, t, p, None, facing, **kw)
    spr = shadowed(spr, body=color, rim=rim, rim_dir=facing, keep_red=True)
    spr = scale_nearest(spr, scale)
    img.paste(spr, (int(round(x - ax * scale)), int(round(y - ay * scale))), spr)
