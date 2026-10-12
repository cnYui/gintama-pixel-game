"""bg.common — shared background toolkit (skies, clouds, moon, mountains,
water, bridge, cherry trees, lanterns, ground/floor strips).

Every public function draws straight onto the 384x216 RGB canvas `img` and is a
PURE function of its arguments (t = scene time in seconds). Static artwork is
rendered once into module-level caches and just pasted per frame, so every call
costs well under 8 ms.

Time of day (`tod`) is one of TODS = ('day', 'dusk', 'night', 'dawn', 'storm').
Interiors may use indoor(tod) -> 'day_in' | 'dusk_in' | 'night_in' | ... (warm,
lamp-lit grades) for floors/walls, e.g. tatami(img, 140, 0, indoor('night')).
All scenery is drawn in "day" colours and then colour-graded per tod
(see grade_color / grade_rgba) so that every background module shares one
consistent light: night = blue-purple + warm lit windows/lanterns, dusk = warm
orange, dawn = pink/lilac, storm = desaturated grey-blue.

Quick reference
---------------
sky(img, tod='day', t=0, horizon=150, body=True)      banded/dithered sky + sun/moon/stars
storm_flash(t) -> 0..1                                 lightning timing used by sky('storm')
clouds(img, t, cam_x=0, tod='day', seed=0, count=7, y0=6, y1=92)
big_moon(img, x, y, r=28, tint=None)                   huge full moon with halo (drama shots)
far_mountains(img, cam_x, tod='day', y=150)            2 hazy ridges, fills ridge..y+40
river(img, y, h, t, tod='day', cam_x=0, reflect_x=None)
bridge(img, cam_x, y, tod='day', style='wood')         arched bridge, deck crest at y
bridge_deck_y(sx, cam_x=0, y=150)                      feet line on the bridge at screen x
cherry_tree(img, x, y, t, scale=1, tod='day', petals=True)   trunk base at (x, y)
lantern(img, x, y, t, color=RED, tod='day', glow=None, size=1, text=None, swing=1.0)
stone_street(img, y, cam_x=0, tod='day', h=None)       flagstone road y..y+h (perspective scroll)
wood_floor(img, y, cam_x=0, tod='day', h=None)
tatami(img, y, cam_x=0, tod='day', h=None)
dirt_ground(img, y, cam_x=0, tod='day', h=None, grass=0.5)
room_wall(img, cam_x=0, tod='day', y0=0, y1=136, style='shoji'|'fusuma'|'plaster')
Helpers for other bg modules: grade_color, grade_rgba, light_up, paste_wrap,
add_sprite, glow_sprite, cached, lit_amount, vgradient.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageFilter

from engine.core import W, H, rng, clamp, lerp, lerp_color, ANIM_FPS
from engine.gfx import INK, PAL, shade, mix

TODS = ("day", "dusk", "night", "dawn", "storm")

# Lantern colours (pass as `color=`)
RED = (206, 58, 52)
WHITE = (236, 228, 204)
YELLOW = (238, 188, 72)
PINK = (232, 120, 150)
BLUE = (80, 112, 190)

# ------------------------------------------------------------------ tod palettes
# sky    : gradient stops (pos 0..1 from top to horizon, colour)
# mul/add: colour grade applied to day-coloured scenery; sat = saturation
# haze   : atmospheric-perspective colour (far layers blend toward it)
# lit    : how strongly windows/neon/lanterns glow (0 day .. 1 night)
_TOD = {
    "day": dict(
        sky=[(0.0, (58, 110, 196)), (0.5, (96, 156, 222)), (0.85, (152, 196, 234)), (1.0, (188, 218, 238))],
        mul=(0.95, 0.95, 0.98), add=(0, 0, 4), sat=0.86, haze=(172, 204, 232), lit=0.0,
        sun=(322, 30)),
    "dusk": dict(
        sky=[(0.0, (36, 34, 84)), (0.35, (98, 58, 116)), (0.68, (206, 98, 100)), (0.88, (246, 150, 92)), (1.0, (252, 190, 110))],
        mul=(0.9, 0.72, 0.7), add=(18, 4, 14), sat=0.8, haze=(204, 122, 118), lit=0.75,
        split=((62, 38, 96), 0.4, (255, 176, 118), 0.32),
        sun=(300, 112)),
    "night": dict(
        sky=[(0.0, (6, 8, 24)), (0.55, (18, 22, 56)), (0.85, (36, 36, 80)), (1.0, (56, 48, 98))],
        mul=(0.36, 0.40, 0.62), add=(6, 6, 22), sat=0.72, haze=(46, 46, 92), lit=1.0,
        split=((16, 16, 44), 0.25, (150, 160, 230), 0.25),
        sun=(318, 34)),
    "dawn": dict(
        sky=[(0.0, (40, 56, 118)), (0.4, (116, 112, 172)), (0.75, (232, 156, 158)), (1.0, (255, 208, 150))],
        mul=(0.88, 0.8, 0.86), add=(16, 10, 18), sat=0.8, haze=(214, 174, 182), lit=0.3,
        split=((80, 70, 130), 0.3, (255, 206, 190), 0.25),
        sun=(74, 120)),
    "storm": dict(
        sky=[(0.0, (26, 28, 38)), (0.6, (48, 52, 66)), (1.0, (80, 84, 98))],
        mul=(0.50, 0.54, 0.62), add=(8, 10, 16), sat=0.5, haze=(78, 84, 100), lit=0.85,
        split=((26, 30, 46), 0.3, (170, 180, 200), 0.1),
        sun=(0, 0)),
}
# Lamp-lit INTERIOR variants (use for floors/walls/props of rooms; the sky
# seen through a window should still use the plain tod). They share the sky
# of their outdoor twin.
_TOD["dusk_in"] = dict(_TOD["dusk"], mul=(0.94, 0.8, 0.76), add=(12, 4, 8),
                       split=((70, 44, 90), 0.3, (255, 190, 130), 0.2))
_TOD["night_in"] = dict(_TOD["night"], mul=(0.66, 0.6, 0.66), add=(10, 6, 14), sat=0.8,
                        split=((34, 24, 52), 0.3, (255, 196, 140), 0.18))
_TOD["storm_in"] = dict(_TOD["storm"], mul=(0.6, 0.6, 0.66), add=(10, 6, 14), sat=0.65,
                        split=((34, 24, 52), 0.3, (255, 196, 140), 0.18))
_TOD["day_in"] = _TOD["day"]
_TOD["dawn_in"] = _TOD["dawn"]
INDOOR = {"day": "day_in", "dusk": "dusk_in", "night": "night_in", "dawn": "dawn_in", "storm": "storm_in"}


def indoor(tod):
    """Map an outdoor tod to its lamp-lit interior grade ('night' -> 'night_in')."""
    return INDOOR.get(tod, tod)


def tod_info(tod):
    return _TOD.get(tod, _TOD["day"])


def lit_amount(tod):
    """0..1 — how strongly emissive things (windows, neon, lanterns) glow."""
    return tod_info(tod)["lit"]


def haze_color(tod):
    return tod_info(tod)["haze"]


# ------------------------------------------------------------------ cache
_CACHE = {}


def cached(key, builder):
    """Module-level memo: builder() runs once per key."""
    v = _CACHE.get(key)
    if v is None:
        v = builder()
        _CACHE[key] = v
    return v


# ------------------------------------------------------------------ grading
def _grade_np(rgb, tod, depth=0.0):
    p = tod_info(tod)
    g = rgb.mean(axis=-1, keepdims=True)
    rgb = g + (rgb - g) * p["sat"]
    rgb = rgb * np.array(p["mul"], np.float32) + np.array(p["add"], np.float32)
    sp = p.get("split")
    if sp is not None:
        lum = (rgb @ np.array([0.3, 0.59, 0.11], np.float32))[..., None] / 255.0
        ts = np.clip(1 - lum * 2.2, 0, 1) * sp[1]
        th = np.clip(lum * 2 - 0.9, 0, 1) * sp[3]
        rgb = rgb * (1 - ts) + np.array(sp[0], np.float32) * ts
        rgb = rgb * (1 - th) + np.array(sp[2], np.float32) * th
    if depth > 0:
        rgb = rgb * (1 - depth) + np.array(p["haze"], np.float32) * depth
    return rgb


def grade_color(c, tod, depth=0.0):
    """Grade a single day-colour for tod (+ atmospheric haze `depth` 0..1)."""
    a = np.array(c[:3], np.float32)[None, :]
    return tuple(int(v) for v in np.clip(_grade_np(a, tod, depth)[0], 0, 255))


def grade_rgba(im, tod, depth=0.0):
    """Colour-grade an RGBA layer (alpha kept)."""
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    a[..., :3] = _grade_np(a[..., :3], tod, depth)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


_BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16.0


def bayer(h, w, ox=0, oy=0):
    return _BAYER4[((np.arange(h) + oy) % 4)[:, None], ((np.arange(w) + ox) % 4)[None, :]]


def light_up(base, emis, amount, glow_radius=4, glow_strength=0.55, glow_levels=3):
    """Composite an emissive RGBA layer (lit windows, neon...) onto a graded RGBA
    layer with strength `amount`, plus a dithered bloom halo. Pure numpy; call
    only at cache-build time."""
    if amount <= 0:
        return base
    b = np.asarray(base).astype(np.float32)
    e = np.asarray(emis).astype(np.float32)
    ea = e[..., 3:4] / 255.0 * amount
    b[..., :3] = b[..., :3] * (1 - ea) + e[..., :3] * ea
    b[..., 3:4] = np.maximum(b[..., 3:4], ea * 255)
    if glow_strength > 0 and glow_radius > 0:
        prem = Image.fromarray(np.clip(e[..., :3] * (e[..., 3:4] / 255.0), 0, 255).astype(np.uint8), "RGB")
        bl = np.asarray(prem.filter(ImageFilter.GaussianBlur(glow_radius))).astype(np.float32)
        lum = bl.max(axis=-1) / 255.0 * glow_strength * amount
        h, w = lum.shape
        q = np.floor(np.clip(lum * glow_levels * 1.6, 0, glow_levels) + bayer(h, w) - 0.5) / (glow_levels * 1.6)
        q = np.clip(q, 0, 0.6)[..., None]
        col = bl / np.maximum(bl.max(axis=-1, keepdims=True), 1) * 255
        alpha = b[..., 3:4] / 255.0
        # on opaque pixels: additive; on transparent pixels: coloured halo alpha
        b[..., :3] = b[..., :3] + col * q * alpha + col * (1 - alpha) * (q > 0)
        b[..., 3:4] = np.maximum(b[..., 3:4], q * 255 * 0.9)
    return Image.fromarray(np.clip(b, 0, 255).astype(np.uint8), "RGBA")


# ------------------------------------------------------------------ paste helpers
def paste_wrap(img, layer, off, y=0, period=None, mask=True):
    """Paste `layer` horizontally tiled so that layer-x == off lands at screen x 0."""
    period = period or layer.width
    x = -(int(math.floor(off)) % period)
    while x < W:
        if x + layer.width > 0:
            if mask:
                img.paste(layer, (x, int(y)), layer)
            else:
                img.paste(layer, (x, int(y)))
        x += period


def add_sprite(img, spr, x, y):
    """Additive blend of an RGB sprite (black = no-op) at top-left (x, y)."""
    x, y = int(x), int(y)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(img.width, x + spr.width), min(img.height, y + spr.height)
    if x1 <= x0 or y1 <= y0:
        return
    box = (x0, y0, x1, y1)
    reg = img.crop(box)
    sub = spr.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    img.paste(ImageChops.add(reg, sub), box)


def glow_sprite(radius, color, strength=1.0, levels=3):
    """Dithered radial glow (RGB, black background) for add_sprite. Cached."""
    key = ("glow", int(radius), tuple(color[:3]), round(strength, 2), levels)

    def build():
        r = int(radius)
        n = 2 * r + 1
        yy, xx = np.mgrid[0:n, 0:n]
        d = np.hypot(xx - r, yy - r) / max(1, r)
        f = np.clip(1 - d, 0, 1) ** 1.6 * levels
        q = np.floor(f + bayer(n, n) * 0.999) / levels
        q = np.clip(q, 0, 1) * 0.55 * strength
        arr = np.clip(np.array(color[:3], np.float32)[None, None, :] * q[..., None], 0, 255).astype(np.uint8)
        return Image.fromarray(arr, "RGB")
    return cached(key, build)


def vgradient(h, w, stops, bands=10, y_end=None, dither=True, oy=0):
    """(h,w,3) uint8 banded + ordered-dither gradient through colour `stops`
    [(pos, rgb), ...]; rows beyond y_end keep the last colour."""
    y_end = h if y_end is None else y_end
    t = np.clip(np.arange(h, dtype=np.float32) / max(1, y_end - 1), 0, 1)
    v = t[:, None] * (bands - 1) + np.zeros((1, w), np.float32)
    if dither:
        v = np.floor(v + bayer(h, w, 0, oy))
    else:
        v = np.round(v)
    v = np.clip(v / (bands - 1), 0, 1)
    ps = np.array([s[0] for s in stops], np.float32)
    cs = np.array([s[1] for s in stops], np.float32)
    out = np.empty((h, w, 3), np.float32)
    for c in range(3):
        out[..., c] = np.interp(v, ps, cs[:, c])
    return out.astype(np.uint8)


def _disc_mask(n, cx, cy, r):
    yy, xx = np.mgrid[0:n, 0:n]
    return (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r


# ------------------------------------------------------------------ sky
def _sun_patch(arr, cx, cy, r, core, ring, glow, halo=14, stripes=False):
    h, w = arr.shape[:2]
    R = r + halo
    x0, x1 = max(0, cx - R), min(w, cx + R + 1)
    y0, y1 = max(0, cy - R), min(h, cy + R + 1)
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = np.hypot(xx - cx, yy - cy)
    sub = arr[y0:y1, x0:x1].astype(np.float32)
    bz = bayer(y1 - y0, x1 - x0, x0, y0)
    # halo: 3 dithered levels
    f = np.clip(1 - (d - r) / halo, 0, 1)
    lev = np.floor(f * 3 + bz * 0.999) / 3.0
    amt = (lev * 0.42)[..., None] * (d > r)[..., None]
    sub = sub * (1 - amt) + np.array(glow, np.float32) * amt
    body = d <= r
    ringm = body & (d > r - 2)
    sub[body] = core
    sub[ringm] = ring
    if stripes:  # retro sunset stripes across the lower half
        for k, sy in enumerate(range(cy + 2, cy + r + 1, 3)):
            yy_i = sy - y0
            if 0 <= yy_i < sub.shape[0]:
                thick = 1 + (k >= 2)
                for q in range(thick):
                    if 0 <= yy_i + q < sub.shape[0]:
                        row = body[yy_i + q]
                        orig = arr[y0 + yy_i + q, x0:x1].astype(np.float32)
                        sub[yy_i + q][row] = orig[row]
    arr[y0:y1, x0:x1] = np.clip(sub, 0, 255).astype(np.uint8)


def _overcast(arr, horizon):
    """Heavy scalloped storm-cloud deck baked into the storm sky."""
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    bz = bayer(h, w)
    r = rng("overcast")
    tones = [(40, 42, 54), (52, 55, 68), (64, 67, 80), (76, 79, 92)]
    for k, base_y in enumerate((10, 30, 52, 76)):
        if base_y > horizon - 20:
            break
        m = yy < base_y - 6
        for i in range(0, w + 40, 18):
            cx = i + r.uniform(-6, 6)
            rad = r.uniform(9, 16)
            m |= (xx - cx) ** 2 + ((yy - (base_y - 4)) * 1.4) ** 2 <= rad * rad
        rim = m & ~np.roll(m, 2, axis=0)
        col = np.array(tones[k], np.float32)
        sub = m & (bz < (0.9 - k * 0.12))
        arr[sub] = (arr[sub] * 0.25 + col * 0.75).astype(np.uint8)
        arr[rim & (bz < 0.6)] = np.minimum(col * 1.25, 255).astype(np.uint8)


def _sky_base(tod, horizon):
    p = tod_info(tod)
    arr = vgradient(H, W, p["sky"], bands=12, y_end=horizon)
    if tod == "storm":
        _overcast(arr, horizon)
    if tod == "day":
        sx, sy = p["sun"]
        _sun_patch(arr, sx, sy, 8, (255, 252, 230), (255, 236, 170), (236, 244, 250), halo=16)
    elif tod == "dusk":
        sx, sy = p["sun"]
        _sun_patch(arr, sx, sy, 15, (255, 206, 120), (255, 170, 90), (255, 190, 120), halo=22, stripes=True)
    elif tod == "dawn":
        sx, sy = p["sun"]
        _sun_patch(arr, sx, sy, 12, (255, 232, 180), (255, 200, 150), (255, 220, 190), halo=20)
    elif tod == "night":
        sx, sy = p["sun"]
        # crescent moon with soft halo
        _sun_patch(arr, sx, sy, 9, (244, 238, 206), (226, 220, 190), (70, 76, 130), halo=18)
        R = 9
        yy, xx = np.mgrid[sy - R - 1:sy + R + 2, sx - R - 1:sx + R + 2]
        cut = (xx - (sx + 4)) ** 2 + (yy - (sy - 3)) ** 2 <= (R - 1) ** 2
        body = (xx - sx) ** 2 + (yy - sy) ** 2 <= R * R
        m = cut & body
        base = vgradient(H, W, p["sky"], bands=12, y_end=horizon)
        sub = arr[sy - R - 1:sy + R + 2, sx - R - 1:sx + R + 2]
        halo_col = np.array((52, 58, 110), np.float32)
        sub[m] = (base[sy - R - 1:sy + R + 2, sx - R - 1:sx + R + 2][m] * 0.5 + halo_col * 0.5).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def _star_list(seed, n, y1):
    r = rng("bgstars", seed)
    out = []
    for i in range(n):
        x, y = r.randint(0, W - 1), r.randint(0, y1)
        big = r.random() < 0.1
        out.append((x, y, r.uniform(0.6, 3.0), r.uniform(0, 6.28), big, r.choice(
            [(255, 255, 255), (206, 214, 255), (255, 236, 200), (180, 190, 240)])))
    return out


def storm_flash(t):
    """Lightning brightness 0..1 at time t (same timing sky('storm') uses).
    Scenes can add fx.flash(img, storm_flash(t) * 0.5) for full-frame flashes."""
    k = int(math.floor(t / 4.2))
    best = 0.0
    for kk in (k - 1, k):
        r = rng("lightning", kk)
        t0 = kk * 4.2 + r.uniform(0.5, 3.2)
        dt = t - t0
        if 0 <= dt < 0.4:
            seq = (1.0, 0.35, 0.9, 0.5, 0.2, 0.0)
            best = max(best, seq[min(5, int(dt * 15))])
    return best


def _bolt(img, t):
    k = int(math.floor(t / 4.2))
    r = rng("lightning", k)
    r.uniform(0.5, 3.2)
    x = r.randint(40, W - 40)
    y = 0
    pts = [(x, y)]
    while y < 120:
        y += r.randint(6, 14)
        x += r.randint(-9, 9)
        pts.append((x, y))
    d = ImageDraw.Draw(img)
    d.line(pts, fill=(170, 180, 255), width=3)
    d.line(pts, fill=(250, 250, 255), width=1)


def sky(img, tod="day", t=0.0, horizon=150, body=True, stars=True):
    """Fill the WHOLE canvas with the tod sky (gradient ends at `horizon`).
    body=False hides the sun/moon (e.g. when using big_moon). Night/dawn/dusk
    get twinkling stars; storm gets periodic lightning (see storm_flash)."""
    key = ("sky", tod, int(horizon), bool(body))

    def build():
        if body:
            return _sky_base(tod, int(horizon))
        p = tod_info(tod)
        return Image.fromarray(vgradient(H, W, p["sky"], bands=12, y_end=int(horizon)), "RGB")
    img.paste(cached(key, build), (0, 0))
    if stars and tod in ("night", "dusk", "dawn"):
        n = {"night": 80, "dusk": 18, "dawn": 14}[tod]
        ymax = {"night": int(horizon * 0.8), "dusk": 40, "dawn": 36}[tod]
        lst = cached(("stars", tod, ymax), lambda: _star_list(7, n, ymax))
        d = ImageDraw.Draw(img)
        sun = tod_info(tod)["sun"]
        dim = 1.0 if tod == "night" else 0.55
        for (x, y, sp, ph, big, c) in lst:
            if abs(x - sun[0]) < 14 and abs(y - sun[1]) < 14:
                continue
            tw = math.sin(t * sp + ph)
            if tw < -0.55:
                continue
            cc = shade(c, dim * (0.65 if tw < 0.2 else 1.0))
            d.point((x, y), fill=cc)
            if big and tw > 0.5:
                cs = shade(c, 0.5 * dim)
                d.point([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], fill=cs)
    if tod == "storm":
        f = storm_flash(t)
        if f > 0:
            bright = cached(("skyflash", int(horizon)), lambda: Image.fromarray(vgradient(
                H, W, [(0, (120, 124, 160)), (1, (190, 190, 214))], bands=8, y_end=int(horizon)), "RGB"))
            img.paste(Image.blend(img, bright, f * 0.8))
            if f > 0.6:
                _bolt(img, t)


# ------------------------------------------------------------------ clouds
_CLOUD_COLS = {
    "day": ((252, 253, 255), (224, 234, 248), (176, 196, 226)),
    "dusk": ((255, 206, 160), (222, 136, 138), (122, 76, 122)),
    "night": ((128, 132, 178), (74, 78, 124), (44, 46, 88)),
    "dawn": ((255, 228, 214), (222, 172, 196), (142, 122, 172)),
    "storm": ((112, 116, 132), (80, 84, 100), (54, 56, 70)),
}


def _cloud_sprite(seed, idx, tod, w, h, fade):
    r = rng("cloudshape", seed, idx)
    pad = 2
    hh, ww = h + pad * 2 + 4, w + pad * 2
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    m = np.zeros((hh, ww), bool)
    base = pad + h + 3
    n = max(3, int(w / 14))
    for i in range(n):
        fx_ = i / (n - 1)
        cx = pad + w * (0.12 + 0.76 * fx_) + r.uniform(-3, 3)
        mid = 1 - abs(fx_ - 0.5) * 2
        rad = h * (0.36 + 0.34 * mid) * r.uniform(0.85, 1.12)
        cy = base - rad * 0.85 - r.uniform(0, 2)
        m |= (xx - cx) ** 2 + ((yy - cy) * 1.1) ** 2 <= rad * rad
    m |= ((xx - (pad + w / 2)) / (w / 2)) ** 2 + ((yy - (base - 3)) / 4.0) ** 2 <= 1
    m[base:, :] = False
    light, midc, dark = _CLOUD_COLS.get(tod, _CLOUD_COLS["day"])
    up = np.zeros_like(m)
    up[2:, :] = m[:-2, :]
    up2 = np.zeros_like(m)
    up2[4:, 1:] = m[:-4, :-1]
    top = m & ~up
    top2 = m & ~up2 & ~top
    bz = bayer(hh, ww)
    arr = np.zeros((hh, ww, 4), np.uint8)
    col = np.zeros((hh, ww, 3), np.float32)
    col[:] = midc
    lower = (yy > base - 1 - h * 0.38)
    shadow = lower & ((yy > base - 3) | (bz < 0.5))
    col[shadow] = dark
    col[top2 & (bz < 0.5)] = light
    col[top] = light
    sky_c = np.array(tod_info(tod)["sky"][-2][1], np.float32)
    col = col * (1 - fade) + sky_c * fade
    arr[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    arr[..., 3] = m * 255
    return Image.fromarray(arr, "RGBA")


def clouds(img, t, cam_x=0, tod="day", seed=0, count=7, y0=6, y1=92, speed=1.0):
    """Drifting pixel clouds (3 tones, lit from top-left). Far/high clouds are
    smaller, slower and hazier. y0..y1 = vertical band for cloud tops."""
    span = W + 200
    for i in range(count):
        r = rng("cloud", seed, i)
        depth = r.uniform(0.25, 1.0)                     # 1 = near
        w = int(26 + 50 * depth * r.uniform(0.7, 1.2))
        h = int(max(7, w * r.uniform(0.22, 0.32)))
        fade = (1 - depth) * 0.45
        spr = cached(("cloud", seed, i, tod, w, h), lambda: _cloud_sprite(seed, i, tod, w, h, fade))
        y = int(y0 + (y1 - y0) * (1 - depth) * r.uniform(0.5, 1.0) + r.uniform(0, (y1 - y0) * 0.4))
        vx = (2.0 + 5.0 * depth) * speed
        x = (r.uniform(0, span) + t * vx - cam_x * (0.04 + 0.16 * depth)) % span - 100
        img.paste(spr, (int(x), y), spr)


# ------------------------------------------------------------------ big moon
def _moon_sprite(r, tint):
    halo = max(8, int(r * 0.7))
    R = r + halo
    n = 2 * R + 1
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.hypot(xx - R, yy - R)
    arr = np.zeros((n, n, 4), np.float32)
    bz = bayer(n, n)
    light = np.array(tint or (252, 248, 226), np.float32)
    # halo alpha levels
    f = np.clip(1 - (d - r) / halo, 0, 1)
    lev = np.floor(f * 4 + bz * 0.999) / 4.0
    arr[..., :3] = light * 0.92
    arr[..., 3] = (lev ** 1.4) * 110 * (d > r)
    body = d <= r
    col = np.zeros((n, n, 3), np.float32)
    col[:] = light
    mid = light * np.array((0.93, 0.92, 0.86))
    dk = light * np.array((0.80, 0.78, 0.72))
    # terminator shading toward lower-right (dithered)
    sh = ((xx - R) * 0.6 + (yy - R) * 0.8) / r
    col[(sh > 0.45) & (bz < 0.5)] = mid
    col[sh > 0.7] = mid
    col[(sh > 0.85) & (bz < 0.5)] = dk
    # craters / maria
    rr = rng("moon", r)
    for k in range(7 + r // 6):
        a = rr.uniform(0, 6.28)
        dist = rr.uniform(0, r * 0.72)
        cx, cy = R + math.cos(a) * dist, R + math.sin(a) * dist
        cr = rr.uniform(r * 0.06, r * 0.2)
        cm = (xx - cx) ** 2 + ((yy - cy) * 1.1) ** 2 <= cr * cr
        col[cm & body] = mid
        cm2 = (xx - cx - 1) ** 2 + ((yy - cy - 1) * 1.1) ** 2 <= (cr * 0.7) ** 2
        col[cm2 & cm & body] = dk
    for k in range(3):   # large soft maria
        a = rr.uniform(0, 6.28)
        dist = rr.uniform(r * 0.1, r * 0.5)
        cx, cy = R + math.cos(a) * dist, R + math.sin(a) * dist
        cr = rr.uniform(r * 0.2, r * 0.35)
        cm = ((xx - cx) ** 2 + (yy - cy) ** 2 <= cr * cr) & body & (bz < 0.5)
        col[cm] = mid
    rim = body & (d > r - 1.2)
    col[rim & (sh < 0)] = np.minimum(light * 1.03, 255)
    arr[..., :3][body] = col[body]
    arr[..., 3][body] = 255
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def big_moon(img, x, y, r=28, tint=None):
    """Huge full moon centred at (x, y) with craters and a dithered halo.
    tint: optional RGB for the lit surface (e.g. (255,200,160) blood-ish moon)."""
    spr = cached(("moon", int(r), tint), lambda: _moon_sprite(int(r), tint))
    img.paste(spr, (int(x) - spr.width // 2, int(y) - spr.height // 2), spr)


# ------------------------------------------------------------------ mountains
_MTN_P = 768


def _ridge(period, seed, amp, octaves):
    r = rng("ridge", seed)
    xs = np.arange(period, dtype=np.float32)
    hgt = np.zeros(period, np.float32)
    for o in range(octaves):
        k = (o + 1) * r.choice([1, 2, 3])
        ph = r.uniform(0, 6.28)
        hgt += np.sin(xs / period * 2 * math.pi * k * (o + 1) + ph) * amp / (o + 1.4)
    return hgt


def _mountain_layers(tod):
    P = _MTN_P
    hh = 110
    # far ridge with a snow-capped Fuji-like cone
    far = np.zeros((hh, P + W, 4), np.uint8)
    base_far = _ridge(P, 3, 10, 4) + 50
    cx = 520
    xs = np.arange(P)
    fuji = np.clip(92 - np.abs(xs - cx) * 0.52, 0, None)
    fuji = np.where(np.abs(xs - cx) < 16, 92 - (np.abs(xs - cx) ** 2) * 0.034 - 0.0, fuji)
    top_far = np.maximum(base_far, fuji)
    near_h = _ridge(P, 11, 7, 5) + 26 + 8 * np.sin(xs / P * 2 * math.pi * 3 + 1.2)
    yy = np.arange(hh)[:, None]
    ridge_far = hh - top_far[None, :]
    mfar = yy >= ridge_far
    c_far = np.zeros((hh, P, 3), np.float32)
    c_far[:] = (104, 124, 164)
    snow = (yy < hh - 72 + 3 * np.sin(xs / 3.0)[None, :]) & mfar
    c_far[snow] = (226, 232, 244)
    # lit left flanks of the peaks
    slope = np.gradient(top_far)
    lit = (slope[None, :] > 0.25) & mfar & (yy < ridge_far + 14)
    c_far[lit & ~snow] = (126, 146, 184)
    c_far[lit & snow] = (246, 248, 252)
    ga = grade_rgba(Image.fromarray(np.dstack([c_far.astype(np.uint8), (mfar * 255).astype(np.uint8)]), "RGBA"), tod, 0.55)
    # near ridge: forested bumps
    bump = (np.abs(np.sin(xs * 0.7)) * 2 + np.abs(np.sin(xs * 0.23 + 1)) * 2)
    ridge_near = hh - (near_h + bump)[None, :]
    mnear = yy >= ridge_near
    c_near = np.zeros((hh, P, 3), np.float32)
    c_near[:] = (60, 88, 92)
    bz = bayer(hh, P)
    c_near[(yy < ridge_near + 3) & mnear & (bz < 0.5)] = (80, 110, 108)
    c_near[(yy > hh - 18) & (bz < 0.35)] = (52, 76, 84)
    gb = grade_rgba(Image.fromarray(np.dstack([c_near.astype(np.uint8), (mnear * 255).astype(np.uint8)]), "RGBA"), tod, 0.3)
    out = []
    for g in (ga, gb):
        ext = Image.new("RGBA", (P + W, hh))
        ext.paste(g, (0, 0))
        ext.paste(g.crop((0, 0, W, hh)), (P, 0))
        out.append(ext)
    return out


def far_mountains(img, cam_x, tod="day", y=150):
    """Two hazy mountain ridges (far with snowy peak, near forested) whose foot
    is at screen row y (they fill down to y+40). Parallax 0.05 / 0.12."""
    far, near = cached(("mtn", tod), lambda: _mountain_layers(tod))
    hh = far.height
    top = int(y) + 40 - hh
    o1 = int(cam_x * 0.05) % _MTN_P
    img.paste(far.crop((o1, 0, o1 + W, hh)), (0, top), far.crop((o1, 0, o1 + W, hh)))
    o2 = int(cam_x * 0.12) % _MTN_P
    c = near.crop((o2, 0, o2 + W, hh))
    img.paste(c, (0, top), c)


# ------------------------------------------------------------------ river
def _river_base(h, tod):
    p = tod_info(tod)
    top_c = grade_color((120, 170, 204), tod)
    hz = p["sky"][-1][1]
    top_c = mix(top_c, hz, 0.35)
    bot_c = grade_color((40, 70, 104), tod)
    arr = vgradient(h, W, [(0, top_c), (0.5, mix(top_c, bot_c, 0.55)), (1, bot_c)], bands=6)
    arr[0, :] = np.array(grade_color((60, 72, 70), tod), np.uint8)      # far bank line
    arr[1, :] = np.array(mix(grade_color((96, 120, 120), tod), top_c, 0.5), np.uint8)
    return Image.fromarray(arr, "RGB")


def _river_dashes(h):
    out = []
    for i in range(int(h * 2.2)):
        r = rng("riv", i)
        depth = r.random()
        out.append((3 + int(depth * depth * (h - 4)), 2 + int(depth * 7), 3 + depth * 10,
                    r.uniform(0, 100), r.uniform(0, W + 40), r.uniform(1.5, 3.5), 0.7 + 0.5 * depth))
    return out


def river(img, y, h, t, tod="day", cam_x=0, reflect_x=None, reflect=True):
    """Water band from row y to y+h with animated shimmer dashes and a
    sun/moon reflection column (reflect_x overrides its screen x, e.g. the x
    of a big_moon; reflect=False disables it)."""
    y, h = int(y), int(h)
    img.paste(cached(("river", h, tod), lambda: _river_base(h, tod)), (0, y))
    d = ImageDraw.Draw(img)
    p = tod_info(tod)
    hi = grade_color((210, 234, 246), tod)
    if tod in ("night", "storm"):
        hi = (150, 160, 210)
    lo = grade_color((30, 56, 86), tod)
    # shimmer dashes, denser/longer toward the viewer
    dashes = cached(("rivdash", h), lambda: _river_dashes(h))
    mid_c = mix(hi, lo, 0.5)
    for (dyy, L, spd, ph, x0, bs, par) in dashes:
        x = (x0 + t * spd - cam_x * par) % (W + 40) - 20
        blink = math.sin(t * bs + ph)
        if blink > 0.1:
            d.line([(x, y + dyy), (x + L, y + dyy)], fill=hi if blink > 0.55 else mid_c)
        elif blink < -0.6:
            d.line([(x, y + dyy), (x + L, y + dyy)], fill=lo)
    # reflection column of the sun / moon
    rx = reflect_x if reflect_x is not None else (p["sun"][0] if tod != "storm" else None)
    if rx is not None and reflect:
        rc = {"day": (250, 248, 230), "dusk": (255, 196, 120), "dawn": (255, 222, 180),
              "night": (236, 232, 200)}.get(tod, (220, 220, 220))
        for k in range(h // 2):
            yy = y + 3 + k * 2
            if yy >= y + h:
                break
            half = 1 + int(k * 0.35) + int(abs(math.sin(t * 3 + k)) * 2)
            if math.sin(t * 4.0 + k * 1.7) > -0.4:
                xo = int(math.sin(t * 2 + k) * 1.5)
                d.line([(rx - half + xo, yy), (rx + half + xo, yy)], fill=rc)


# ------------------------------------------------------------------ bridge
BRIDGE_SPAN = 520
BRIDGE_RISE = 9
_BR_TOP = 20      # sprite row of the deck crest


def bridge_deck_y(sx, cam_x=0, y=150):
    """Feet line on the bridge deck at screen x `sx` (bridge drawn with same cam_x, y)."""
    cx = W / 2 - cam_x
    u = clamp(abs(sx - cx) / (BRIDGE_SPAN / 2), 0, 1)
    return int(round(y + BRIDGE_RISE * u * u))


def _bridge_sprite(tod, style):
    S = BRIDGE_SPAN
    hh = _BR_TOP + 64
    im = Image.new("RGBA", (S, hh))
    d = ImageDraw.Draw(im)
    if style == "red":
        c_hi, c_md, c_dk, c_sh = (222, 92, 70), (184, 56, 48), (128, 38, 40), (84, 30, 36)
    else:
        c_hi, c_md, c_dk, c_sh = (168, 122, 84), (130, 90, 62), (92, 62, 46), (62, 44, 38)
    gold = (206, 170, 84)
    cx = S / 2

    def dy(x):
        u = abs(x - cx) / (S / 2)
        return int(round(BRIDGE_RISE * u * u))
    # piers + bracing (behind)
    piers = list(range(40, S - 20, 72))
    for px in piers:
        top = _BR_TOP + dy(px) + 8
        d.rectangle([px - 2, top, px + 2, hh - 1], fill=c_sh)
        d.rectangle([px - 2, top, px - 2, hh - 1], fill=c_dk)
    for a, b in zip(piers, piers[1:]):
        ta, tb = _BR_TOP + dy(a) + 12, _BR_TOP + dy(b) + 12
        d.line([(a + 2, ta), (b - 2, tb + 22)], fill=c_sh, width=2)
        d.line([(a + 2, ta + 22), (b - 2, tb)], fill=c_sh, width=2)
        d.line([(a, ta + 30), (b, tb + 30)], fill=c_sh, width=2)
    # deck fascia + lower girder, column by column so the arch is crisp
    for x in range(S):
        yd = _BR_TOP + dy(x)
        d.line([(x, yd), (x, yd + 5)], fill=c_md)
        d.point((x, yd), fill=c_hi)
        d.point((x, yd + 1), fill=c_hi if x % 2 else c_md)
        d.point((x, yd + 5), fill=c_dk)
        d.line([(x, yd + 6), (x, yd + 7)], fill=c_sh)          # under-deck shadow
        d.line([(x, yd + 8), (x, yd + 10)], fill=c_dk)          # girder
        d.point((x, yd + 8), fill=c_md)
        if x % 24 == 0:
            d.line([(x, yd + 2), (x, yd + 4)], fill=c_dk)
    # railing
    for x in range(S):
        yd = _BR_TOP + dy(x)
        d.point((x, yd - 12), fill=c_hi)          # top rail (kasagi)
        d.point((x, yd - 11), fill=c_md)
        d.point((x, yd - 10), fill=c_dk)
        d.point((x, yd - 6), fill=c_md)           # middle rail
        d.point((x, yd - 2), fill=c_dk)           # bottom rail
        d.point((x, yd - 1), fill=c_sh)
    for x in range(4, S - 3, 14):
        yd = _BR_TOP + dy(x)
        d.rectangle([x, yd - 12, x + 1, yd - 1], fill=c_md)
        d.point((x, yd - 12), fill=c_hi)
        d.line([(x + 1, yd - 11), (x + 1, yd - 1)], fill=c_dk)
    # main posts with giboshi (onion caps) at ends and every quarter
    for x in (6, S // 4, S // 2, 3 * S // 4, S - 8):
        yd = _BR_TOP + dy(x)
        d.rectangle([x - 2, yd - 15, x + 2, yd], fill=c_md)
        d.line([(x - 2, yd - 15), (x - 2, yd)], fill=c_hi)
        d.line([(x + 2, yd - 15), (x + 2, yd)], fill=c_dk)
        gy = yd - 16
        d.ellipse([x - 3, gy - 5, x + 3, gy + 1], fill=gold)
        d.point((x - 1, gy - 3), fill=(250, 226, 150))
        d.line([(x, gy - 8), (x, gy - 5)], fill=gold)
        d.point((x, gy - 9), fill=(250, 226, 150))
        d.line([(x - 3, gy + 1), (x + 3, gy + 1)], fill=shade(gold, 0.6))
    return grade_rgba(im, tod)


def bridge(img, cam_x, y, tod="day", style="wood"):
    """Arched Japanese bridge (side view), centred on the screen at cam_x=0,
    spanning BRIDGE_SPAN px. Deck crest (feet line) at row y; use
    bridge_deck_y(sx, cam_x, y) for the feet line elsewhere. Railing is the far
    rail (characters stand in front of it). style 'wood' | 'red'."""
    spr = cached(("bridge", tod, style), lambda: _bridge_sprite(tod, style))
    x0 = int(round(W / 2 - BRIDGE_SPAN / 2 - cam_x))
    img.paste(spr, (x0, int(y) - _BR_TOP), spr)


# ------------------------------------------------------------------ cherry tree
def _tree_frames(scale, tod):
    s = float(scale)
    wv = int(100 * s)
    hv = int(84 * s)
    bx, by = wv // 2, hv - 1                      # trunk base in sprite
    r = rng("sakura_tree", round(s, 2))
    trunk_c, trunk_hi, trunk_dk = (86, 58, 54), (122, 86, 74), (56, 38, 42)
    petal = [(255, 222, 232), (246, 174, 198), (220, 128, 166), (168, 86, 128)]
    # --- branch skeleton: trunk -> 3 limbs -> twigs (list of polylines)
    fork = (bx - 1 * s, by - 24 * s)
    limbs = []
    for k, ang in enumerate((-148, -100, -40)):
        a = math.radians(ang + r.uniform(-8, 8))
        L = s * r.uniform(24, 30) * (1.15 if k != 1 else 1.0)
        mid = (fork[0] + math.cos(a) * L * 0.55 + r.uniform(-2, 2) * s, fork[1] + math.sin(a) * L * 0.45)
        end = (fork[0] + math.cos(a) * L * 1.3, fork[1] + math.sin(a) * L * 0.75 - 4 * s)
        limbs.append([fork, mid, end])
        for q in range(2):
            a2 = a + math.radians(r.choice((-1, 1)) * r.uniform(25, 45))
            L2 = s * r.uniform(8, 14)
            limbs.append([mid, (mid[0] + math.cos(a2) * L2, mid[1] + math.sin(a2) * L2 * 0.7)])
    # --- clusters sampled inside the crown ellipse
    ccx, ccy, rx, ry = bx, by - 50 * s, 44 * s, 24 * s
    clusters = []
    tries = 0
    while len(clusters) < int(30 * s) and tries < 500:
        tries += 1
        u, v = r.uniform(-1, 1), r.uniform(-1, 1)
        if u * u + v * v > 1:
            continue
        rad = r.uniform(5.5, 9.0) * s * (1.0 - 0.25 * abs(u))
        clusters.append((ccx + u * rx, ccy + v * ry * (0.85 if v > 0 else 1.0), rad))
    clusters.sort(key=lambda c: c[1])          # back (top) first, front (bottom) last
    holes = [(ccx + r.uniform(-0.7, 0.7) * rx, ccy + r.uniform(-0.1, 0.8) * ry, r.uniform(1.2, 2.0) * s)
             for _ in range(int(4 * s))]
    noise = np.array([[r.random() for _ in range(wv)] for _ in range(hv)], np.float32)
    frames = []
    for sway in (-1, 0, 1):
        im = Image.new("RGBA", (wv, hv))
        d = ImageDraw.Draw(im)

        def sw(p):   # sway offset grows with height
            k = clamp((by - p[1]) / (60 * s), 0, 1)
            return (p[0] + sway * k, p[1])
        # trunk: tapered with a bend
        pts = [(bx, by), (bx + 1 * s, by - 10 * s), fork]
        for i in range(len(pts) - 1):
            wa = max(2, int(round((6 - i * 1.5) * s)))
            d.line([pts[i], pts[i + 1]], fill=trunk_dk, width=wa + 2)
        for i in range(len(pts) - 1):
            wa = max(1, int(round((6 - i * 1.5) * s)))
            d.line([pts[i], pts[i + 1]], fill=trunk_c, width=wa)
        d.line([(bx - 2 * s, by - 1), (bx - 1 * s, by - 16 * s)], fill=trunk_hi, width=1)
        d.line([(bx - 6 * s, by), (bx - 1, by - 3 * s)], fill=trunk_dk, width=max(1, int(2 * s)))
        d.line([(bx + 6 * s, by), (bx + 1, by - 3 * s)], fill=trunk_dk, width=max(1, int(2 * s)))
        for li, lb in enumerate(limbs):
            ww = max(1, int(round((3 if li % 3 == 0 else 1.5) * s)))
            d.line([sw(p) for p in lb], fill=trunk_dk, width=ww + 1)
            d.line([sw(p) for p in lb], fill=trunk_c, width=ww)
        arr = np.array(im)
        yy, xx = np.mgrid[0:hv, 0:wv].astype(np.float32)
        tone = np.full((hv, wv), -1, np.int8)
        bz = bayer(hv, wv)
        for (cx, cy, rad) in clusters:
            k = clamp((by - cy) / (60 * s), 0, 1)
            cx2 = cx + sway * k
            dd = ((xx - cx2) ** 2 + ((yy - cy) * 1.2) ** 2) / (rad * rad)
            m = dd <= 1.0 + (noise - 0.5) * 0.35
            loc = ((xx - cx2) * 0.5 + (yy - cy) * 0.9) / rad
            tt = np.where(loc < -0.5, 0, np.where(loc > 0.5, 2, 1))
            tt = np.where((np.abs(loc + 0.5) < 0.13) & (bz < 0.5), 0, tt)
            tt = np.where((np.abs(loc - 0.5) < 0.13) & (bz < 0.5), 2, tt)
            # lower crown sits in shadow
            low = (cy - ccy) / ry
            if low > 0.35:
                tt = np.minimum(tt + 1, 3)
            elif low > 0.05:
                tt = np.where(bz < 0.4, np.minimum(tt + 1, 3), tt)
            tone[m] = tt[m]
        for (hx, hy, hr) in holes:
            hm = (xx - hx) ** 2 + (yy - hy) ** 2 <= hr * hr
            tone[hm] = -1
        cm = tone >= 0
        edge_b = cm & ~np.roll(cm, -1, 0)            # bottom boundary -> darkest
        pal = np.array(petal, np.uint8)
        col = pal[np.clip(tone, 0, 3)]
        col[edge_b] = pal[3]
        sp = cm & (noise > 0.93)
        col[sp] = pal[0]
        sp2 = cm & (noise < 0.05)
        col[sp2] = pal[2]
        arr[cm, :3] = col[cm]
        arr[cm, 3] = 255
        im = Image.fromarray(arr, "RGBA")
        d = ImageDraw.Draw(im)
        # a few twigs in front of the lower crown for depth
        for lb in limbs[1::3]:
            d.line([sw(p) for p in lb], fill=trunk_dk, width=1)
        frames.append(grade_rgba(im, tod))
    return frames, (bx, by), clusters


def cherry_tree(img, x, y, t, scale=1, tod="day", petals=True, phase=0.0):
    """Blooming sakura tree, trunk base at (x, y); ~96x80 px at scale 1.
    Canopy sways (3 frames) and petals drift down to the ground at y."""
    frames, (bx, by), clusters = cached(("tree", round(float(scale), 2), tod),
                                        lambda: _tree_frames(scale, tod))
    sw = math.sin(t * 2 * math.pi * 0.35 + phase + x * 0.05)
    k = 0 if sw < -0.45 else (2 if sw > 0.45 else 1)
    spr = frames[k]
    img.paste(spr, (int(x) - bx, int(y) - by), spr)
    if petals:
        d = ImageDraw.Draw(img)
        pc = [grade_color(c, tod) for c in ((255, 206, 222), (240, 150, 184))]
        s = float(scale)
        for i in range(int(9 * s)):
            r = rng("petal", round(x), i)
            per = r.uniform(3.5, 6.0)
            u = ((t + r.uniform(0, per)) % per) / per
            cx, cy, rad = clusters[r.randrange(len(clusters))]
            sx = x - bx + cx + u * 34 * s + math.sin(u * 9 + i) * 4
            sy = y - by + cy + u * (by - cy)
            c = pc[i % 2]
            if int(t * 8 + i) % 2:
                d.point([(sx, sy), (sx + 1, sy)], fill=c)
            else:
                d.point([(sx, sy), (sx, sy + 1)], fill=c)


# ------------------------------------------------------------------ lantern
def _lantern_sprite(color, size, lit, text):
    bw, bh = (7, 9) if size == 1 else (13, 17)
    capw = 3 if size == 1 else 7
    pad = 1
    wv, hv = bw + 2 * pad, bh + 4 + (1 if size == 1 else 2)
    im = Image.new("RGBA", (wv, hv))
    arr = np.zeros((hv, wv, 4), np.uint8)
    top = 2 if size == 1 else 3
    yy, xx = np.mgrid[0:bh, 0:bw].astype(np.float32)
    cx, cy = (bw - 1) / 2, (bh - 1) / 2
    e = ((xx - cx) / (bw / 2)) ** 2 + ((yy - cy) / (bh / 2 + 0.3)) ** 2
    body = e <= 1.0
    if lit:
        c_core = mix(color, (255, 236, 170), 0.75)
        c_mid = mix(color, (255, 214, 140), 0.35)
        c_edge = color
    else:
        c_core, c_mid, c_edge = shade(color, 1.08), color, shade(color, 0.72)
    col = np.zeros((bh, bw, 3), np.float32)
    col[:] = c_mid
    if lit:
        col[e < 0.45] = c_core
        col[e > 0.8] = c_edge
    else:
        col[(xx - cx) < -bw * 0.18] = c_core
        col[(xx - cx) > bw * 0.22] = c_edge
    rib = shade(c_edge, 0.8)
    for ry in range(1, bh - 1, 2):
        col[ry, body[ry]] = mix(col[ry, body[ry]].mean(0), rib, 0.5)
    sub = arr[top:top + bh, pad:pad + bw]
    sub[body, :3] = np.clip(col[body], 0, 255).astype(np.uint8)
    sub[body, 3] = 255
    im = Image.fromarray(arr, "RGBA")
    d = ImageDraw.Draw(im)
    ink = (40, 30, 34)
    mx = wv // 2
    d.rectangle([mx - capw // 2 - 1, top - 1, mx + capw // 2 + (0 if size == 1 else 1), top], fill=ink)
    d.rectangle([mx - capw // 2 - 1, top + bh - 1, mx + capw // 2 + (0 if size == 1 else 1), top + bh], fill=ink)
    d.line([(mx, 0), (mx, top - 1)], fill=ink)
    if text and size >= 2:
        from engine.text import draw_text
        draw_text(im, mx + 1, top + bh // 2, text, (40, 20, 20) if not lit else (130, 30, 20),
                  size=12, anchor="mm")
    return im


def lantern(img, x, y, t, color=RED, tod="day", glow=None, size=1, text=None, swing=1.0, string=4):
    """Paper chochin hanging from (x, y) on a short string, swaying gently.
    glow: 0..1 halo strength (default = lit_amount(tod): lit at night/dusk).
    size 1 (7x9 body) or 2 (13x17, can carry a 1-char `text`, e.g. '祭')."""
    g = lit_amount(tod) if glow is None else glow
    lit = g > 0.25
    spr = cached(("lantern", tuple(color[:3]), size, lit, text), lambda: _lantern_sprite(color, size, lit, text))
    ang = math.sin(t * 2 * math.pi * 0.32 + x * 0.071) * swing
    dx = int(round(ang * (1.4 if size == 1 else 2.2)))
    L = string * size
    d = ImageDraw.Draw(img)
    d.line([(x, y), (x + dx, y + L)], fill=(40, 30, 34))
    px, py = int(x + dx - spr.width // 2), int(y + L)
    if g > 0:
        rad = int(11 * size + 3)
        gc = mix(color, (255, 200, 120), 0.55)
        flick = 0.9 + 0.1 * math.sin(t * 13 + x)
        gs = glow_sprite(rad, gc, round(clamp(g * flick) * 4) / 4)
        add_sprite(img, gs, px + spr.width // 2 - rad, py + spr.height // 2 - rad)
    img.paste(spr, (px, py), spr)


# ------------------------------------------------------------------ ground strips
_GP = 192   # period of ground textures


def _ground_rows(h, first=3, grow=1.35, maxh=16):
    rows = []
    y, rh = 0, float(first)
    while y < h:
        hh = int(round(rh))
        rows.append((y, min(h, y + hh)))
        y += hh
        rh = min(maxh, rh * grow)
    return rows


def _paste_rows(img, strip, rows, y, cam_x, h):
    for (r0, r1) in rows:
        f = 1.0 + 0.55 * ((r0 + r1) / 2) / max(1, h)
        o = int(math.floor(cam_x * f)) % _GP
        img.paste(strip.crop((o, r0, o + W, r1)), (0, y + r0))


def _mk_strip(h, painter):
    arr = np.zeros((h, _GP, 3), np.uint8)
    painter(arr)
    return np.concatenate([arr, arr[:, :W]], axis=1) if W <= _GP else np.concatenate([arr] * (W // _GP + 2), axis=1)


def _stone_strip(h, tod):
    rows = _ground_rows(h, 3, 1.3, 14)
    r = rng("stones", h)
    tones = [(118, 112, 110), (106, 100, 100), (128, 122, 116), (98, 94, 96)]
    mortar = (74, 68, 72)
    hi = (150, 144, 138)

    def paint(arr):
        arr[:] = mortar
        for ri, (r0, r1) in enumerate(rows):
            rh = r1 - r0
            sw = max(8, int(rh * 2.6))
            x = r.randint(0, sw)
            xs = []
            while x < _GP:
                xs.append(x)
                x += int(sw * r.uniform(0.75, 1.3))
            if len(xs) < 1:
                xs = [0]
            bounds = xs + [xs[0] + _GP]
            for a, b in zip(bounds, bounds[1:]):
                tone = tones[r.randrange(len(tones))]
                for xx in range(a + 1, b):
                    xm = xx % _GP
                    arr[r0 + 1:r1, xm] = tone
                    if rh > 3:
                        arr[r0 + 1, xm] = mix(tone, hi, 0.55)
                if rh >= 6 and r.random() < 0.5:     # pebble / crack detail
                    px = (a + r.randint(2, max(3, b - a - 2))) % _GP
                    py = r0 + r.randint(2, rh - 2)
                    arr[py, px] = mix(tone, mortar, 0.6)
        arr[0, :] = (60, 56, 62)
        arr[1, :] = (84, 78, 82)
    strip = _mk_strip(h, paint)
    g = grade_rgba(Image.fromarray(strip, "RGB").convert("RGBA"), tod).convert("RGB")
    return g, rows


def stone_street(img, y=160, cam_x=0, tod="day", h=None):
    """Flagstone street from row y to y+h (default: to the bottom). Rows are
    taller and scroll faster toward the viewer (cheap perspective parallax)."""
    y = int(y)
    h = H - y if h is None else int(h)
    strip, rows = cached(("stone", h, tod), lambda: _stone_strip(h, tod))
    _paste_rows(img, strip, rows, y, cam_x, h)


def _wood_strip(h, tod):
    rows = _ground_rows(h, 3, 1.18, 12)
    r = rng("planks", h)
    tones = [(150, 104, 70), (138, 94, 64), (160, 112, 76), (130, 88, 60)]

    def paint(arr):
        for (r0, r1) in rows:
            rh = r1 - r0
            L = int(r.uniform(60, 110))
            x = r.randint(0, L)
            joints = []
            while x < _GP:
                joints.append(x)
                x += int(L * r.uniform(0.7, 1.2))
            bounds = (joints or [0]) + [(joints or [0])[0] + _GP]
            for a, b in zip(bounds, bounds[1:]):
                tone = np.array(tones[r.randrange(4)], np.float32)
                for xx in range(a, b):
                    xm = xx % _GP
                    arr[r0:r1, xm] = tone
                    arr[r0, xm] = np.minimum(tone * 1.16, 255)
                    arr[r1 - 1, xm] = tone * 0.72
                arr[r0:r1, a % _GP] = tone * 0.62
                for g in range(max(1, (b - a) // 14)):    # wood grain
                    gx = (a + r.randint(2, max(3, b - a - 6))) % _GP
                    gy = r0 + r.randint(1, max(1, rh - 2))
                    for q in range(r.randint(2, 6)):
                        arr[gy, (gx + q) % _GP] = tone * 0.86
    strip = _mk_strip(h, paint)
    return grade_rgba(Image.fromarray(strip, "RGB").convert("RGBA"), tod).convert("RGB"), rows


def wood_floor(img, y, cam_x=0, tod="day", h=None):
    """Polished wooden plank floor from row y to y+h (perspective rows)."""
    y = int(y)
    h = H - y if h is None else int(h)
    strip, rows = cached(("wood", h, tod), lambda: _wood_strip(h, tod))
    _paste_rows(img, strip, rows, y, cam_x, h)


def _tatami_strip(h, tod):
    rows = _ground_rows(h, 3, 1.25, 14)
    straw = np.array((190, 180, 112), np.float32)
    straw_d = np.array((170, 160, 96), np.float32)
    heri = np.array((52, 62, 46), np.float32)

    def paint(arr):
        # mats: every 2 perspective rows form one mat depth; seams every 96 px
        for ri, (r0, r1) in enumerate(rows):
            for yy in range(r0, r1):
                arr[yy, :] = straw if (yy % 2) else straw_d
            if ri % 2 == 0:
                arr[r0, :] = heri
                if r1 - r0 > 5:
                    arr[r0 + 1, :] = heri * 1.3
            off = 0 if (ri // 2) % 2 == 0 else 48
            for sx in range(off, _GP, 96):
                arr[r0:r1, sx % _GP] = straw * 0.7
    strip = _mk_strip(h, paint)
    return grade_rgba(Image.fromarray(strip, "RGB").convert("RGBA"), tod).convert("RGB"), rows


def tatami(img, y, cam_x=0, tod="day", h=None):
    """Tatami mats (straw weave + dark cloth borders) from row y to y+h."""
    y = int(y)
    h = H - y if h is None else int(h)
    strip, rows = cached(("tatami", h, tod), lambda: _tatami_strip(h, tod))
    _paste_rows(img, strip, rows, y, cam_x, h)


def _dirt_strip(h, tod, grass):
    rows = _ground_rows(h, 3, 1.3, 14)
    r = rng("dirt", h)
    base = np.array((132, 106, 80), np.float32)

    def paint(arr):
        bz = bayer(h, _GP)
        yy = np.arange(h)[:, None] / max(1, h)
        arr[:] = base
        noise = np.array([[r.random() for _ in range(_GP)] for _ in range(h)], np.float32)
        arr[(noise < 0.18)] = base * 0.88
        arr[(noise > 0.9)] = base * 1.1
        arr[0, :] = base * 0.75
        for i in range(int(_GP * h / 90)):
            px, py = r.randrange(_GP), r.randrange(2, h)
            arr[py, px] = (150, 140, 130)
            if py + 1 < h:
                arr[py + 1, px] = (96, 80, 66)
        gc = [(88, 128, 72), (110, 150, 84), (70, 104, 62)]
        for i in range(int(_GP * h / 60 * grass)):
            px, py = r.randrange(_GP), r.randrange(3, h)
            hgt = 2 + int(py / h * 4)
            c = gc[r.randrange(3)]
            for q in range(hgt):
                arr[py - q, px] = c
                if q < hgt - 1 and r.random() < 0.5:
                    arr[py - q, (px + 1) % _GP] = gc[2]
    strip = _mk_strip(h, paint)
    return grade_rgba(Image.fromarray(strip, "RGB").convert("RGBA"), tod).convert("RGB"), rows


def dirt_ground(img, y, cam_x=0, tod="day", h=None, grass=0.5):
    """Packed earth with pebbles and grass tufts (roads, fields, battlefields)."""
    y = int(y)
    h = H - y if h is None else int(h)
    strip, rows = cached(("dirt", h, tod, round(grass, 2)), lambda: _dirt_strip(h, tod, grass))
    _paste_rows(img, strip, rows, y, cam_x, h)


# ------------------------------------------------------------------ interior wall
_RW_P = 192


def _room_wall_strip(style, h):
    from ._draw import WOOD, WOOD_D, beam, glow_rect
    im = Image.new("RGBA", (_RW_P + W, h))
    em = Image.new("RGBA", (_RW_P + W, h))
    d, e = ImageDraw.Draw(im), ImageDraw.Draw(em)
    plaster = (212, 196, 164)
    d.rectangle([0, 0, _RW_P + W, h], fill=plaster)
    r = rng("roomwall", style)
    for _ in range((_RW_P + W) * h // 50):
        d.point((r.randrange(_RW_P + W), r.randrange(h)), fill=(196, 180, 150))
    top = 12 if h > 60 else 4
    lint = min(h - 30, 30)
    for x0 in range(0, _RW_P + W, 96):
        if style in ("shoji", "fusuma"):
            for k in range(2):
                px0, px1 = x0 + 8 + k * 42, x0 + 8 + k * 42 + 39
                y0, y1 = lint + 6, h - 6
                if style == "shoji":
                    d.rectangle([px0, y0, px1, y1], fill=(234, 228, 208))
                    glow_rect(e, px0, y0, px1, y1, (255, 222, 156), 235, 0.8)
                    for gx in range(px0, px1 + 1, 8):
                        d.line([(gx, y0), (gx, y1)], fill=WOOD.mid)
                        e.line([(gx, y0), (gx, y1)], fill=(0, 0, 0, 0))
                    for gy in range(y0, y1 + 1, 10):
                        d.line([(px0, gy), (px1, gy)], fill=WOOD.mid)
                        e.line([(px0, gy), (px1, gy)], fill=(0, 0, 0, 0))
                    d.rectangle([px0, y1 - 8, px1, y1], fill=WOOD.mid)
                    e.rectangle([px0, y1 - 8, px1, y1], fill=(0, 0, 0, 0))
                else:
                    d.rectangle([px0, y0, px1, y1], fill=(226, 214, 180))
                    # painted mountains + mist motif
                    base_y = y0 + (y1 - y0) * 2 // 3
                    d.polygon([(px0, base_y), (px0 + 12, base_y - 14), (px0 + 22, base_y - 4),
                               (px0 + 30, base_y - 18), (px1, base_y - 2), (px1, base_y)], fill=(150, 170, 150))
                    d.line([(px0 + 2, base_y + 4), (px1 - 6, base_y + 4)], fill=(236, 226, 196))
                    d.ellipse([px1 - 12, y0 + 4, px1 - 4, y0 + 12], fill=(220, 120, 90))
                    d.ellipse([px0 + 3 + (k * 30), (y0 + y1) // 2 - 2, px0 + 6 + (k * 30), (y0 + y1) // 2 + 2],
                              fill=(80, 70, 60))
                d.rectangle([px0 - 1, y0 - 1, px1 + 1, y1 + 1], outline=WOOD_D.dark)
        d.rectangle([x0, top, x0 + 5, h], fill=WOOD.mid)
        d.line([(x0, top), (x0, h)], fill=WOOD.hi)
        d.line([(x0 + 5, top), (x0 + 5, h)], fill=WOOD.dark)
    beam(d, 0, _RW_P + W, lint, WOOD, 4)
    d.rectangle([0, 0, _RW_P + W, top - 1], fill=(74, 56, 50))
    if top > 4:
        beam(d, 0, _RW_P + W, top - 3, WOOD_D, 3)
    d.rectangle([0, h - 3, _RW_P + W, h - 1], fill=WOOD.dark)
    return im, em


def room_wall(img, cam_x=0, tod="day", y0=0, y1=136, style="shoji", lit=None):
    """Generic Japanese interior back wall (ceiling strip, pillars, lintel)
    from row y0 to y1, scrolling with cam_x. style: 'shoji' (paper sliding
    panels, glow at night), 'fusuma' (painted sliding doors) or 'plaster'.
    Pair with tatami()/wood_floor() starting at y1. lit: glow 0..1 (default
    by tod)."""
    h = int(y1 - y0)
    raw = cached(("roomwall_raw", style, h), lambda: _room_wall_strip(style, h))
    amt = lit_amount(tod) if lit is None else lit

    def mk():
        g = grade_rgba(raw[0], tod)
        if amt > 0 and style == "shoji":
            g = light_up(g, raw[1], amt, glow_radius=2, glow_strength=0.35)
        return g
    lay = cached(("roomwall", style, h, tod, round(amt, 2)), mk)
    o = int(math.floor(cam_x)) % _RW_P
    c = lay.crop((o, 0, o + W, h))
    img.paste(c, (0, int(y0)), c)
