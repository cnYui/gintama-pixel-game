"""Private art for s12 洛阳决战·离别 (owned by the s12 scene agent).

Rakuyo (rain planet of the Yato): cold slate sky, rock spires, a colossal
crashed battleship, ruined Chinese-style town, wet flagstones with puddles.
Edo harbour / ship deck / dock at dawn for the Shinsengumi farewell.
Every function is a pure function of its arguments; static art is cached.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import W, H, rng, clamp, lerp, wave, step_frame, ease_out
from engine.gfx import INK, shade, mix, outline, gradient, overlay_rect, rect, flip_h, pset
from engine.text import text_sprite
from bg import common as C, edo as E

_CACHE = {}


def cached(key, fn):
    v = _CACHE.get(key)
    if v is None:
        v = fn()
        _CACHE[key] = v
    return v


# ======================================================================= camera
def zoom_at(img, k, px, py, sx=W / 2, sy=H / 2):
    """Zoom by k so that world point (px, py) lands on screen (sx, sy); the crop
    box is clamped inside the canvas. Returns f(x, y) -> screen coords."""
    if k <= 1.001:
        return lambda x, y: (x, y)
    w, h = W / k, H / k
    x0 = clamp(px - sx / k, 0, W - w)
    y0 = clamp(py - sy / k, 0, H - h)
    z = img.resize((W, H), Image.NEAREST, box=(x0, y0, x0 + w, y0 + h))
    img.paste(z)
    return lambda x, y: ((x - x0) * k, (y - y0) * k)


# ======================================================================= Rakuyo
R_SKY = [(0.0, (14, 18, 28)), (0.45, (30, 38, 50)), (0.8, (52, 64, 72)), (1.0, (74, 88, 92))]
LW = W + 260          # parallax layer width (pasted at -130 - cam*par)
FAR = (54, 64, 72)
FAR_HI = (74, 86, 92)
FAR_D = (44, 52, 60)
MID_WALL = (60, 66, 76)
MID_WALL_D = (47, 52, 62)
MID_ROOF = (36, 40, 52)
MID_ROOF_HI = (80, 88, 98)
MID_WIN = (22, 26, 34)
NEAR = (30, 34, 44)
NEAR_HI = (78, 90, 100)
NEAR_D = (22, 24, 32)


def _r_sky():
    arr = C.vgradient(H, W, R_SKY, bands=10, y_end=150)
    return Image.fromarray(arr, "RGB")


def _far():
    im = Image.new("RGBA", (LW, 160), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = rng("s12far")
    base = 152
    x = -10
    while x < LW + 10:                              # rock spires / mesas
        w = r.randint(16, 44)
        top = r.randint(96, 128)
        ln = r.randint(-5, 5)
        t2 = top + r.randint(0, 5)
        pts = [(x, base), (x + 3 + ln, top + 7), (x + 7 + ln, top), (x + w - 7 + ln, t2),
               (x + w - 2 + ln, t2 + 9), (x + w + 2, base)]
        d.polygon(pts, fill=FAR)
        d.line([(x + 3 + ln, top + 7), (x + 7 + ln, top), (x + w - 7 + ln, t2)], fill=FAR_HI)
        if r.random() < 0.35:                       # thin needle spire
            sx = x + w // 2 + ln
            sh = r.randint(20, 34)
            d.polygon([(sx - 3, top + 2), (sx + ln // 2, top - sh), (sx + 3, top + 2)], fill=FAR)
            d.line([(sx - 3, top + 2), (sx + ln // 2, top - sh)], fill=FAR_HI)
        x += w - r.randint(2, 10)
    # colossal crashed battleship: nose tilted up, broken stern buried
    cx, cy, ang = 360, 150, math.radians(20)
    ca, sa = math.cos(ang), math.sin(ang)

    def P(u, v):          # hull-local (u along the hull, v up) -> layer px
        return (cx + u * ca - v * sa * 0.35, cy - u * sa - v * ca)
    hull = [P(-70, -4), P(-66, 16), P(-52, 22), P(40, 24), P(96, 16), P(128, 6), P(136, 0),
            P(120, -8), P(60, -14), P(-20, -14), P(-60, -12)]
    d.polygon(hull, fill=(50, 58, 66))
    d.line([P(-52, 22), P(40, 24), P(96, 16), P(128, 6), P(136, 0)], fill=(86, 96, 104))
    for u in range(-40, 110, 9):                    # window row
        a, b = P(u, 10), P(u + 4, 10)
        d.line([a, b], fill=(30, 36, 44))
    d.polygon([P(20, 24), P(34, 44), P(52, 46), P(56, 24)], fill=(46, 54, 62))      # bridge tower
    d.line([P(34, 44), P(52, 46)], fill=(86, 96, 104))
    d.line([P(44, 46), P(46, 62)], fill=(46, 54, 62))                                # antenna
    for i, u in enumerate(range(-68, -44, 5)):     # exposed ribs at the broken stern
        d.line([P(u, -6), P(u - 3, 20 + (i % 2) * 5)], fill=(40, 46, 54), width=2)
    d.polygon([P(90, -8), P(110, -30), P(118, -24), P(104, -6)], fill=(46, 54, 62))  # fin
    return im


def _pagoda(d, x, base, tiers=4, w0=46, broken=True, r=None):
    y = base
    for i in range(tiers):
        w = w0 - i * 9
        wall_h = 13 - i
        x0, x1 = x - w // 2, x + w // 2
        if broken and i == tiers - 1:
            # jagged broken top storey
            pts = [(x0 + 2, y), (x0 + 2, y - wall_h + 3), (x0 + 6, y - wall_h - 2), (x0 + 9, y - wall_h + 2),
                   (x + 2, y - wall_h - 5), (x + 5, y - wall_h), (x1 - 3, y - wall_h + 4), (x1 - 2, y)]
            d.polygon(pts, fill=MID_WALL_D)
            d.line(pts[1:5], fill=MID_ROOF_HI)
            break
        d.rectangle([x0 + 3, y - wall_h, x1 - 3, y], fill=MID_WALL)
        d.rectangle([x1 - 8, y - wall_h, x1 - 3, y], fill=MID_WALL_D)
        for wx in range(x0 + 7, x1 - 8, 7):
            d.rectangle([wx, y - wall_h + 3, wx + 2, y - 2], fill=MID_WIN)
        # upturned eave roof
        ry = y - wall_h
        d.polygon([(x0 - 6, ry - 1), (x0 - 3, ry + 2), (x1 + 3, ry + 2), (x1 + 6, ry - 1),
                   (x1 - 2, ry - 6), (x0 + 2, ry - 6)], fill=MID_ROOF)
        d.line([(x0 - 6, ry - 1), (x0 + 2, ry - 6), (x1 - 2, ry - 6)], fill=MID_ROOF_HI)
        if i == 1 and broken:        # a chunk of eave missing
            d.polygon([(x1 - 2, ry - 6), (x1 + 6, ry - 1), (x1 + 3, ry + 2), (x1 - 6, ry - 3)], fill=(0, 0, 0, 0))
        y = ry - 6


def _house(d, x, base, w, h, r):
    x0, x1 = x, x + w
    top = base - h
    d.rectangle([x0, top, x1, base], fill=MID_WALL)
    d.rectangle([x1 - 6, top, x1, base], fill=MID_WALL_D)
    # windows (round moon-gate style or square)
    for wx in range(x0 + 5, x1 - 10, 11):
        if r.random() < 0.7:
            d.rectangle([wx, top + 6, wx + 5, top + 12], fill=MID_WIN)
            d.line([(wx, top + 6), (wx + 5, top + 6)], fill=MID_ROOF_HI)
    if w > 34:
        cx = x0 + w // 2
        d.ellipse([cx - 6, base - 13, cx + 6, base + 3], fill=MID_WIN)
    # partially collapsed roof: left half intact, right half a jagged stump
    cut = x0 + int(w * r.uniform(0.45, 0.75))
    ry = top
    d.polygon([(x0 - 5, ry + 1), (x0, ry - 7), (cut, ry - 7), (cut + 3, ry - 3), (cut - 2, ry + 1)], fill=MID_ROOF)
    d.line([(x0 - 5, ry + 1), (x0, ry - 7), (cut, ry - 7)], fill=MID_ROOF_HI)
    d.line([(cut, ry - 7), (cut + 3, ry - 3), (cut + 6, ry - 5), (x1, ry)], fill=MID_WALL_D)
    # broken wall hole
    hx = x0 + int(w * r.uniform(0.2, 0.6))
    d.polygon([(hx, top + 2), (hx + 5, top + 9), (hx + 3, top + 15), (hx + 9, top + 13), (hx + 7, top + 3)], fill=MID_WIN)
    # cracks
    d.line([(x1 - 10, top + 3), (x1 - 13, top + 10), (x1 - 11, top + 16)], fill=MID_WALL_D)


def _arch(d, x, base, w=40, h=46):
    x0, x1 = x - w // 2, x + w // 2
    for px in (x0, x1 - 5):
        d.rectangle([px, base - h, px + 5, base], fill=MID_WALL)
        d.line([(px, base - h), (px, base)], fill=MID_ROOF_HI)
    # lintel + roof, right side broken and hanging
    d.rectangle([x0 - 4, base - h - 4, x - 2, base - h + 2], fill=MID_WALL_D)
    d.polygon([(x0 - 9, base - h - 3), (x0 - 4, base - h - 10), (x, base - h - 10), (x + 3, base - h - 4)], fill=MID_ROOF)
    d.line([(x0 - 9, base - h - 3), (x0 - 4, base - h - 10), (x, base - h - 10)], fill=MID_ROOF_HI)
    d.polygon([(x + 1, base - h - 2), (x1 + 2, base - h + 14), (x1 - 2, base - h + 17), (x - 2, base - h + 2)], fill=MID_WALL_D)


def _tower(d, x, base, w=20, h=70):
    x0, x1 = x - w // 2, x + w // 2
    top = base - h
    pts = [(x0, base), (x0, top + 6), (x0 + 4, top), (x0 + 7, top + 5), (x0 + 11, top - 3),
           (x0 + 14, top + 8), (x1, top + 4), (x1, base)]
    d.polygon(pts, fill=MID_WALL)
    d.rectangle([x1 - 5, top + 8, x1, base], fill=MID_WALL_D)
    d.line(pts[1:7], fill=MID_ROOF_HI)
    for yy in range(top + 14, base - 8, 12):
        d.rectangle([x0 + 6, yy, x0 + 9, yy + 5], fill=MID_WIN)
    for yy in (top + 24, top + 48):
        d.rectangle([x0 - 3, yy, x1 + 3, yy + 2], fill=MID_ROOF)


def _mid():
    im = Image.new("RGBA", (LW, 160), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = rng("s12mid")
    base = 153
    _tower(d, 40, base, 20, 78)
    _house(d, 66, base, 48, 30, r)
    _pagoda(d, 160, base, 4, 50, True, r)
    _house(d, 196, base, 36, 24, r)
    _arch(d, 262, base, 44, 48)
    _house(d, 300, base, 56, 34, r)
    _tower(d, 380, base, 16, 58)
    _house(d, 398, base, 44, 26, r)
    _pagoda(d, 480, base, 3, 42, True, r)
    _house(d, 520, base, 50, 30, r)
    _tower(d, 600, base, 22, 84)
    # rubble line along the base
    for i in range(70):
        x = r.randint(0, LW)
        w = r.randint(3, 9)
        hh = r.randint(2, 5)
        d.polygon([(x, base + 1), (x + 2, base - hh), (x + w - 2, base - hh + 1), (x + w, base + 1)], fill=MID_WALL_D)
    d.rectangle([0, base, LW, 159], fill=MID_WALL_D)
    return im


def _column(d, x, top, base, w=14, lean=0):
    x0, x1 = x - w // 2, x + w // 2
    jag = [(x0 + lean, top + 5), (x0 + 3 + lean, top), (x0 + 6 + lean, top + 4), (x0 + 9 + lean, top - 3),
           (x1 + lean, top + 6)]
    pts = [(x0, base)] + jag + [(x1, base)]
    d.polygon(pts, fill=NEAR)
    for fx_ in range(x0 + 3, x1 - 1, 4):               # fluting
        d.line([(fx_ + lean * 0.3, top + 8), (fx_, base - 6)], fill=NEAR_D)
    d.line([(x0, base), (x0 + lean, top + 5)], fill=NEAR_HI)
    d.line(jag, fill=NEAR_HI)
    d.rectangle([x0 - 3, base - 5, x1 + 3, base], fill=NEAR)           # plinth
    d.line([(x0 - 3, base - 5), (x1 + 3, base - 5)], fill=NEAR_HI)


def _dead_tree(d, x, base):
    d.polygon([(x - 3, base), (x - 1, base - 30), (x + 2, base - 44), (x + 3, base - 30), (x + 4, base)], fill=NEAR)
    for (a, b, c) in (((x + 1, base - 30), (x - 12, base - 46), (x - 16, base - 44)),
                      ((x + 2, base - 38), (x + 14, base - 54), (x + 18, base - 56)),
                      ((x - 1, base - 22), (x - 10, base - 28), (x - 13, base - 34)),
                      ((x + 3, base - 18), (x + 12, base - 24), (x + 14, base - 30))):
        d.line([a, b, c], fill=NEAR, width=2)
    d.line([(x - 3, base), (x - 1, base - 30), (x + 1, base - 42)], fill=NEAR_HI)


def _near():
    im = Image.new("RGBA", (LW, 176), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = rng("s12near")
    base = 156
    _column(d, 150, 78, base, 16, 2)
    _column(d, 196, 112, base, 12, -1)
    _dead_tree(d, 268, base)
    _column(d, 470, 70, base, 18, -2)
    _column(d, 516, 120, base, 12, 1)
    # toppled column drum + rubble mounds
    for (x, w, hh) in ((110, 30, 8), (228, 22, 6), (330, 40, 7), (420, 26, 9), (560, 34, 8)):
        d.polygon([(x, base + 2), (x + 4, base - hh), (x + w // 2, base - hh - 3), (x + w - 3, base - hh + 1),
                   (x + w, base + 2)], fill=NEAR)
        d.line([(x + 4, base - hh), (x + w // 2, base - hh - 3)], fill=NEAR_HI)
    for i in range(40):
        x = r.randint(0, LW)
        d.rectangle([x, base - r.randint(1, 3), x + r.randint(2, 5), base + 1], fill=NEAR)
    return im


def _puddles():
    out = []
    r = rng("s12pud")
    for i in range(16):
        out.append((r.uniform(-120, W + 120), r.uniform(164, 214), r.uniform(14, 44)))
    return out


def lightning_amt(t, t0):
    dt = t - t0
    if 0 <= dt < 0.4:
        return (1.0, 0.3, 0.9, 0.5, 0.2, 0.0)[min(5, int(dt * 15))]
    return 0.0


def bolt(img, t0, x, seed=0, color=(220, 226, 255)):
    r = rng("s12bolt", seed)
    y = 0
    pts = [(x, y)]
    branches = []
    while y < 128:
        y += r.randint(6, 13)
        x += r.randint(-10, 10)
        pts.append((x, y))
        if r.random() < 0.3:
            branches.append([(x, y), (x + r.randint(-16, 16), y + r.randint(8, 18))])
    d = ImageDraw.Draw(img)
    d.line(pts, fill=(140, 150, 230), width=3)
    d.line(pts, fill=color, width=1)
    for b in branches:
        d.line(b, fill=(160, 170, 240), width=1)


def rakuyo(img, t, cam_x=0.0, flash=0.0, bolt_x=None, bolt_seed=0, dark=0.0):
    """Rakuyo ruins. Ground ~ rows 148..216, standard feet line 160.
    flash 0..1 brightens the sky (lightning); bolt_x draws a bolt."""
    img.paste(cached("rsky", _r_sky), (0, 0))
    C.clouds(img, t, cam_x, "storm", seed=21, count=9, y0=0, y1=58, speed=2.2)
    if flash > 0:
        bright = cached("rsky_hi", lambda: Image.fromarray(C.vgradient(
            H, W, [(0, (96, 104, 140)), (1, (176, 184, 204))], bands=8, y_end=150), "RGB"))
        img.paste(Image.blend(img, bright, flash * 0.75))
        if bolt_x is not None and flash > 0.45:
            bolt(img, 0, bolt_x, bolt_seed)
    far = cached("rfar", _far)
    img.paste(far, (-130 - int(round(cam_x * 0.15)), 0), far)
    mid = cached("rmid", _mid)
    img.paste(mid, (-130 - int(round(cam_x * 0.4)), 0), mid)
    # mist band between mid and near
    mist = cached("rmist", lambda: _mist_band())
    img.paste(mist, (0, 118), mist)
    near = cached("rnear", _near)
    img.paste(near, (-130 - int(round(cam_x * 0.75)), 0), near)
    C.stone_street(img, 150, cam_x, "storm", h=66)
    # wet sheen: darken + cool the stones, dithered sky reflection streaks
    wet = cached("rwet", _wet_overlay)
    img.paste(wet, (0, 150), wet)
    d = ImageDraw.Draw(img)
    for (px, py, pw) in cached("rpud", _puddles):
        x = px - cam_x
        if x + pw < 0 or x - pw > W:
            continue
        ph = max(2, int(pw * 0.16 * (py - 140) / 60))
        d.ellipse([x - pw / 2, py - ph / 2, x + pw / 2, py + ph / 2], fill=(58, 70, 82))
        d.line([(x - pw / 2 + 3, py - ph / 2), (x + pw / 2 - 3, py - ph / 2)], fill=(104, 118, 130))
        # ripples
        for k in range(2):
            rr = rng("rip", int(px), int(t * 5 + k * 0.5))
            age = (t * 5 + k * 0.5) % 1.0
            rx = x + rr.uniform(-pw * 0.3, pw * 0.3)
            rw = 1 + age * 6
            if age < 0.8:
                d.ellipse([rx - rw, py - rw * 0.3, rx + rw, py + rw * 0.3], outline=(130, 146, 160))
    if flash > 0:
        overlay_rect(img, 0, 90, W, 126, (190, 200, 230), flash * 0.18)
    if dark > 0:
        overlay_rect(img, 0, 0, W, H, (8, 10, 18), dark)


def _mist_band():
    arr = np.zeros((40, W, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = 92, 106, 112
    yy = np.arange(40, dtype=np.float32)[:, None]
    a = np.clip(np.sin(yy / 40 * math.pi) * 0.34, 0, 1)
    q = np.floor(a * 8 + C.bayer(40, W)) / 8
    arr[..., 3] = (np.clip(q, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def _wet_overlay():
    h = 66
    arr = np.zeros((h, W, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = 20, 28, 44
    arr[..., 3] = 70
    r = rng("wetsheen")
    for i in range(46):
        y = int(r.uniform(2, h - 1))
        x = int(r.uniform(0, W))
        L = int(r.uniform(6, 26))
        arr[y, x:x + L, :3] = (120, 136, 150)
        arr[y, x:x + L, 3] = 90
    return Image.fromarray(arr, "RGBA")


def ground_splashes(img, t, y0=152, y1=216, n=46, seed=0, color=(170, 186, 204)):
    d = ImageDraw.Draw(img)
    for i in range(n):
        r = rng("spl", seed, i)
        per = r.uniform(0.25, 0.5)
        ph = r.uniform(0, per)
        k = int((t + ph) / per)
        age = (t + ph) % per
        if age > 0.12:
            continue
        rr = rng("spl2", seed, i, k)
        x = int(rr.uniform(0, W))
        y = int(rr.uniform(y0, y1))
        if age < 0.05:
            d.point([(x, y - 1), (x - 1, y - 2), (x + 1, y - 2)], fill=color)
        else:
            d.point([(x - 2, y - 1), (x + 2, y - 1), (x, y)], fill=color)


def rain_layer(img, t, heavy=1.0, seed=0, slant=0.3):
    from engine import fx
    fx.rain(img, t, count=int(120 * heavy), seed=seed, color=(118, 136, 160), speed=420, slant=slant, length=7)
    fx.rain(img, t, count=int(26 * heavy), seed=seed + 9, color=(176, 192, 214), speed=640, slant=slant, length=12)


# ======================================================================= ship
HULL = (50, 48, 72)
HULL_HI = (90, 88, 122)
HULL_D = (32, 30, 48)
GOLD = (248, 204, 80)
GOLD_D = (198, 144, 54)


def _ship_art():
    """Shinsengumi flying ship, side view, bow RIGHT. ~128x86. Returns
    (sprite, info dict with thruster points + flag pole top)."""
    w, h = 132, 90
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    dy = 30                         # everything below the mast top
    # sail (junk style) on the main mast
    mx = 58
    d.line([(mx, 0), (mx, 34 + dy)], fill=(96, 62, 44), width=2)
    d.polygon([(mx - 26, 4), (mx + 22, 2), (mx + 26, 40), (mx - 30, 42)], fill=(238, 230, 206))
    for yy in (12, 21, 30):
        d.line([(mx - 27, 4 + yy), (mx + 24, 2 + yy)], fill=(176, 166, 146))
    d.line([(mx - 26, 4), (mx - 30, 42)], fill=(255, 250, 236))
    d.line([(mx + 22, 2), (mx + 26, 40)], fill=(186, 174, 150))
    mark = text_sprite("诚", (214, 40, 52), 22, "brush", outline=None)
    im.alpha_composite(mark, (mx - mark.width // 2, 22 - mark.height // 2))
    # stern cabin
    d.rectangle([12, 16 + dy, 42, 34 + dy], fill=(230, 220, 190))
    for xx in range(16, 42, 6):
        d.line([(xx, 18 + dy), (xx, 32 + dy)], fill=(160, 120, 80))
    d.line([(12, 25 + dy), (42, 25 + dy)], fill=(160, 120, 80))
    d.polygon([(6, 17 + dy), (12, 10 + dy), (42, 10 + dy), (48, 17 + dy)], fill=(44, 44, 62))
    d.line([(12, 10 + dy), (42, 10 + dy)], fill=GOLD)
    # hull (bow right, raised stern left)
    top = 34 + dy
    hull = [(2, top - 6), (10, top), (104, top), (126, top - 8), (128, top - 5), (116, top + 8),
            (100, top + 18), (26, top + 18), (10, top + 10)]
    d.polygon(hull, fill=HULL)
    d.polygon([(10, top), (104, top), (126, top - 8), (122, top - 3), (104, top + 4), (12, top + 4)], fill=HULL_HI)
    d.line([(10, top + 5), (104, top + 5), (124, top - 4)], fill=GOLD)
    d.line([(12, top + 6), (104, top + 6)], fill=GOLD_D)
    d.line([(16, top + 12), (106, top + 12)], fill=HULL_D)
    for px in range(24, 100, 12):                       # gold portholes
        d.rectangle([px, top + 8, px + 2, top + 10], fill=GOLD_D)
        d.point((px, top + 8), fill=GOLD)
    d.polygon([(118, top - 6), (126, top - 12), (124, top - 4)], fill=GOLD)       # bow crest
    # rail
    d.line([(8, top - 4), (104, top - 4)], fill=(120, 82, 56))
    for px in range(10, 104, 6):
        d.line([(px, top - 4), (px, top)], fill=(120, 82, 56))
    # tiny crew at the stern rail: Kondo, Hijikata, Okita (dots)
    for i, (hair, px) in enumerate((((50, 42, 48), 70), ((60, 60, 88), 76), ((214, 164, 100), 82))):
        d.rectangle([px, top - 7, px + 2, top - 1], fill=HULL_D)
        d.rectangle([px, top - 10, px + 2, top - 8], fill=(255, 214, 180))
        d.line([(px, top - 11), (px + 2, top - 11)], fill=hair)
    # engine pods
    for (x0, x1) in ((30, 52), (74, 96)):
        d.rounded_rectangle([x0, top + 16, x1, top + 23], radius=3, fill=(118, 124, 140))
        d.line([(x0 + 2, top + 17), (x1 - 2, top + 17)], fill=(170, 176, 192))
        d.rectangle([x0 - 2, top + 17, x0, top + 22], fill=(60, 62, 76))
    spr = outline(im, INK)
    info = {"thrusters": [(41 + 1, top + 25), (85 + 1, top + 25)], "flag": (5 + 1, top - 22 + 1),
            "size": spr.size}
    # flag pole at the stern
    return spr, info


def ship_sprite():
    return cached("ship", _ship_art)


def flag_frames(w=26, h=16, n=6, big=False):
    """Red Shinsengumi flag 「诚」 waving (to the LEFT of its pole)."""
    key = ("flag", w, h, n)

    def build():
        base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(base)
        d.rectangle([0, 0, w - 1, h - 1], fill=(206, 40, 48))
        d.rectangle([0, h - 3, w - 1, h - 1], fill=(250, 250, 250))
        for xx in range(0, w, 4):          # white dagger teeth (dandara)
            d.polygon([(xx, h - 3), (xx + 2, h - 6), (xx + 4, h - 3)], fill=(250, 250, 250))
        d.line([(0, 0), (w - 1, 0)], fill=(240, 90, 90))
        size = max(10, int(h * 0.8))
        mark = text_sprite("诚", (255, 255, 255), size, "brush" if big else "hei", outline=None)
        base.alpha_composite(mark, (w // 2 - mark.width // 2, (h - 3) // 2 - mark.height // 2))
        frames = []
        for f in range(n):
            out = Image.new("RGBA", (w, h + 6), (0, 0, 0, 0))
            for x in range(w):
                u = (w - 1 - x) / max(1, w - 1)            # 0 at the pole (right edge)
                off = int(round(math.sin(x * 0.35 + f * 2 * math.pi / n) * 2.2 * u))
                col = base.crop((x, 0, x + 1, h))
                # shade the troughs
                if math.cos(x * 0.35 + f * 2 * math.pi / n) < -0.4 and u > 0.2:
                    a = np.asarray(col).copy()
                    a[..., :3] = (a[..., :3] * 0.8).astype(np.uint8)
                    col = Image.fromarray(a, "RGBA")
                out.paste(col, (x, 3 + off), col)
            frames.append(outline(out, INK))
        return frames
    return cached(key, build)


def draw_flag(img, pole_x, pole_y, t, w=26, h=16, big=False, fps=10):
    fr = flag_frames(w, h, 6, big)
    f = fr[step_frame(t, fps, len(fr))]
    img.paste(f, (int(pole_x) - f.width + 1, int(pole_y) - 4), f)


def draw_ship(img, x, y, t, lift=1.0):
    """Ship centred at (x, y) (hull centre). lift 0..1 = thruster intensity."""
    spr, info = ship_sprite()
    x0, y0 = int(round(x - spr.width / 2)), int(round(y - spr.height * 0.62))
    img.paste(spr, (x0, y0), spr)
    fx_, fy_ = info["flag"]
    d = ImageDraw.Draw(img)
    d.line([(x0 + fx_, y0 + fy_ - 4), (x0 + fx_, y0 + fy_ + 20)], fill=INK, width=1)
    draw_flag(img, x0 + fx_ - 1, y0 + fy_ - 2, t, 22, 13)
    # thrusters (downward jets)
    f = step_frame(t, 15, 3)
    for (tx, ty) in info["thrusters"]:
        L = int((6 + f * 2) * lift)
        if L <= 0:
            continue
        X, Y = x0 + tx, y0 + ty
        d.polygon([(X - 5, Y), (X + 5, Y), (X, Y + L + 6)], fill=(110, 200, 255))
        d.polygon([(X - 3, Y), (X + 3, Y), (X, Y + L)], fill=(210, 245, 255))
        d.line([(X - 1, Y), (X + 1, Y)], fill=(255, 255, 255))
    return x0, y0


def ship_silhouette(scale):
    """Dark silhouette of the ship for back-lit distance shots."""
    spr, info = ship_sprite()
    q = round(scale * 40) / 40
    key = ("sil", q)

    def build():
        a = np.asarray(spr).copy()
        a[..., 0], a[..., 1], a[..., 2] = 70, 50, 86
        s = Image.fromarray(a, "RGBA")
        w, h = max(2, int(s.width * q)), max(2, int(s.height * q))
        s = s.resize((w, h), Image.BOX)
        b = np.asarray(s).copy()
        b[..., 3] = np.where(b[..., 3] > 90, 255, 0).astype(np.uint8)
        b[..., 0], b[..., 1], b[..., 2] = 70, 50, 86
        return Image.fromarray(b, "RGBA")
    return cached(key, build)


# ======================================================================= harbour
def _pier_sprite():
    w, h = 170, 44
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # posts
    for px in range(8, w, 20):
        d.rectangle([px, 8, px + 4, h - 1], fill=(70, 46, 40))
        d.line([(px, 8), (px, h - 1)], fill=(110, 76, 58))
    # deck
    d.rectangle([0, 0, w, 7], fill=(150, 104, 74))
    d.line([(0, 0), (w, 0)], fill=(196, 146, 104))
    d.line([(0, 7), (w, 7)], fill=(84, 56, 44))
    for px in range(3, w, 7):
        d.line([(px, 1), (px, 6)], fill=(128, 86, 60))
    # bollards
    for px in (24, 96):
        d.rectangle([px, -0, px + 4, 0], fill=(60, 56, 64))
    return im


def pier(img, x, y, t, tod="dawn"):
    spr = cached(("pier", tod), lambda: C.grade_rgba(_pier_sprite(), tod, 0.0) if tod != "day" else _pier_sprite())
    img.paste(spr, (int(x), int(y)), spr)
    d = ImageDraw.Draw(img)
    # bollards on top
    for px in (24, 96):
        X = int(x) + px
        d.rectangle([X - 1, int(y) - 5, X + 4, int(y)], fill=INK)
        d.rectangle([X, int(y) - 4, X + 3, int(y)], fill=(70, 64, 76))
        d.point((X, int(y) - 4), fill=(130, 120, 130))
    # little wakes around the posts
    for px in range(8, spr.width, 20):
        X = int(x) + px + 2
        k = step_frame(t + px * 0.01, 4, 2)
        d.line([(X - 4 - k, int(y) + 30), (X + 5 + k, int(y) + 30)], fill=(250, 232, 220))


def gulls(img, t, n=5, seed=0, area=(0, 20, W, 90), color=(250, 246, 240), speed=26):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = area
    for i in range(n):
        r = rng("gull", seed, i)
        sp = speed * r.uniform(0.7, 1.3)
        span = x1 - x0 + 40
        x = (r.uniform(0, span) + t * sp) % span + x0 - 20
        y = r.uniform(y0, y1) + math.sin(t * 1.3 + i) * 3
        f = step_frame(t + r.random(), 6, 2)
        if f == 0:
            d.point([(x - 2, y - 1), (x - 1, y), (x, y + 1), (x + 1, y), (x + 2, y - 1)], fill=color)
        else:
            d.point([(x - 2, y + 1), (x - 1, y), (x, y + 1), (x + 1, y), (x + 2, y + 1)], fill=color)


# ======================================================================= deck
def _rail_sprite():
    w, h = W, 30
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # gunwale (black lacquer + gold trim)
    d.rectangle([0, 16, w, h - 1], fill=HULL)
    d.line([(0, 16), (w, 16)], fill=HULL_HI)
    d.line([(0, 19), (w, 19)], fill=GOLD)
    d.line([(0, 20), (w, 20)], fill=GOLD_D)
    d.line([(0, h - 1), (w, h - 1)], fill=HULL_D)
    # rail posts + top bar
    for px in range(4, w, 22):
        d.rectangle([px - 1, 3, px + 2, 16], fill=INK)
        d.rectangle([px, 3, px + 1, 16], fill=(150, 98, 66))
        d.rectangle([px - 1, 1, px + 2, 3], fill=GOLD)
    d.rectangle([0, 3, w, 5], fill=INK)
    d.line([(0, 4), (w, 4)], fill=(176, 118, 78))
    for px in range(15, w, 22):          # rope loops between posts
        for k in range(8):
            d.point((px - 7 + k * 2, 9 + int(math.sin(k / 7 * math.pi) * 3)), fill=(214, 196, 150))
    return im


def deck(img, t, dy, rail_y=128, floor_y=146, tod="dawn", cam=0):
    """Ship deck at dawn: sky, sinking Edo (dy), stern rail, plank floor."""
    C.sky(img, tod, t, horizon=150)
    C.clouds(img, t, 0, tod, seed=12, count=7, y0=2, y1=70, speed=5.0)
    E.skyline(img, cam, t, tod, ships=False, sky=False, dy=int(dy))
    rail = cached(("rail", tod), lambda: C.grade_rgba(_rail_sprite(), tod, 0.0))
    img.paste(rail, (0, rail_y), rail)
    C.wood_floor(img, floor_y + 2, 0, tod, h=H - floor_y - 2)


def wind_streaks(img, t, color=(255, 240, 230), n=10, seed=0, y0=0, y1=H):
    from engine import fx
    fx.motion_lines(img, t, color=color, count=n, direction=-1, seed=seed, y0=y0, y1=y1, speed=520,
                    length=(10, 34))


# ======================================================================= dock
def _embank():
    w, h = 70, 70
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(8, 0), (w, 0), (w, h), (0, h)], fill=(126, 116, 118))
    for yy in range(4, h, 7):
        off = (yy // 7) % 2 * 6
        d.line([(8 - yy * 8 // h, yy), (w, yy)], fill=(98, 90, 96))
        for xx in range(8 + off, w, 12):
            d.line([(xx, yy - 7), (xx, yy)], fill=(98, 90, 96))
    d.line([(8, 0), (w, 0)], fill=(176, 164, 160))
    return im


def embankment(img, x, y, tod="dawn"):
    spr = cached(("emb", tod), lambda: C.grade_rgba(_embank(), tod, 0.0))
    img.paste(spr, (int(x), int(y)), spr)


# ======================================================================= sunrise
def _hills():
    w, h = W, 20
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = rng("s12hills")
    pts = [(0, h)]
    x = 0
    while x <= w:
        pts.append((x, r.randint(4, 12)))
        x += r.randint(10, 26)
    pts.append((w, h))
    d.polygon(pts, fill=(150, 120, 164))
    for i in range(30):                       # far city specks
        x = r.randint(150, w - 10)
        hh = r.randint(2, 7)
        d.rectangle([x, h - 6 - hh, x + r.randint(2, 5), h], fill=(132, 104, 150))
    d.rectangle([0, h - 3, w, h], fill=(170, 134, 170))
    return im


def sunrise(img, t, sx=118, sy=122, r=15):
    """Big rising sun with a dithered glow + retro stripes, far hills in front."""
    C.add_sprite(img, C.glow_sprite(r * 3, (255, 170, 120), 0.9), sx - r * 3, sy - r * 3)
    d = ImageDraw.Draw(img)
    d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 226, 170))
    d.ellipse([sx - r + 3, sy - r + 2, sx + r - 5, sy + r - 6], fill=(255, 244, 214))
    for i, yy in enumerate(range(sy + 3, sy + r + 1, 4)):
        d.line([(sx - r, yy), (sx + r, yy)], fill=(246, 170, 150), width=1 + i // 2)
    hills = cached("hills", _hills)
    img.paste(hills, (0, 124), hills)
