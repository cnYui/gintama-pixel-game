"""bg.edo — the Edo panorama: tiled rooftops, Edo castle, the enormous
'Terminal' spaceport tower, alien ships and the final-arc armada.

skyline(img, cam_x, t, tod='day', ships=True, armada=0.0, sky=True, near=True, dy=0)
    Full panorama (sky + clouds + mountains + Terminal + far city + castle +
    mid roofs + near roofs). Parallax: terminal 0.1, far city 0.25,
    castle 0.4, mid 0.6, near 1.0. At cam_x=0 the Terminal is centred
    (TERMINAL_SX) and the castle is on the left. `armada` (0..1) inserts
    fleet() behind the city. near=False leaves the bottom band (~y>=176) to
    you (e.g. draw roof_walk instead). dy shifts everything but the sky down.
terminal(img, cam_x, t, tod='day', dy=0, parallax=0.1)   just the tower
ship(img, x, y, kind, t, scale=1, facing=1, tod='day', haze=0.0)
    kinds: SHIP_KINDS = ('saucer', 'shuttle', 'cruiser', 'pirate', 'kiheitai',
    'mothership'). (x, y) = centre. facing -1 flips (bows point right by default).
    ship_size(kind, scale=1) -> (w, h)
fleet(img, t, density=1.0, cam_x=0)
    Ominous armada: darkens the sky (reddish-purple) and fills it with
    silhouetted cruisers/pirates, drifting, lights pulsing, and a giant
    mothership looming at the top. Draw it right after the sky.
roof_walk(img, cam_x, y, t, tod='day')
    Foreground kawara rooftop whose RIDGE is a flat walkable line at row y
    (feet at y). Tiled slope below, eave at y+40, dark alley under it.
    For rooftop chases / the final-arc assembly on the roofs.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import W, H, rng, clamp, wave
from engine.gfx import INK, shade, mix, outline, flip_h, scale_nearest, overlay_rect
from . import common as C
from ._draw import (WrapLayer, graded_layer, paste_layer, roof, flat_roof, wall, post, beam,
                    shoji, glass, mushiko, window_grid, neon_tube, text_on, lattice, boards,
                    TILE, TILE_B, TILE_G, WOOD, WOOD_D, PLASTER, CONCRETE, GLOW, CLEAR)

TERMINAL_SX = W // 2        # screen x of the Terminal at cam_x = 0
CASTLE_SX = 84              # screen x of Edo castle at cam_x = 0
SHIP_KINDS = ("saucer", "shuttle", "cruiser", "pirate", "kiheitai", "mothership")

_FAR_P, _CASTLE_P, _MID_P, _NEAR_P, _WALK_P = 896, 1536, 1024, 768, 512
_WALK_TOP, _WALK_H = 30, 110


# ======================================================================== Terminal
def _terminal_sprite():
    w, h = 110, 190
    im = Image.new("RGBA", (w, h))
    em = Image.new("RGBA", (w, h))
    d, e = ImageDraw.Draw(im), ImageDraw.Draw(em)
    cx = w // 2
    hi, mid, dk, dk2 = (222, 228, 238), (184, 194, 212), (140, 150, 172), (104, 112, 136)
    win = (150, 232, 250)
    base_y = h - 1

    def shaft_w(y):
        if y < 30:
            return 5
        if y < 150:
            return 7 + (y - 30) * 0.02
        f = (y - 150) / 40.0
        return 9 + f * f * 26
    for y in range(h):
        hw = shaft_w(y)
        xa, xb = int(cx - hw), int(cx + hw)
        d.line([(xa, y), (xb, y)], fill=mid)
        d.line([(xa, y), (xa + max(1, int(hw * 0.4)), y)], fill=hi)
        d.line([(xb - max(1, int(hw * 0.35)), y), (xb, y)], fill=dk)
        d.point((xb, y), fill=dk2)
        if y % 9 == 0 and y > 30:
            d.line([(xa, y), (xb, y)], fill=dk)
        if 34 < y < 170 and y % 3:
            d.point((cx, y), fill=(120, 180, 200))
            e.point((cx, y), fill=win + (255,))
        if y > 160 and y % 4 == 1:
            for x in range(xa + 3, xb - 2, 4):
                d.point((x, y), fill=(96, 126, 150))
                e.point((x, y), fill=(255, 220, 150, 255))
    # spire needle above
    d.line([(cx, 0), (cx, 14)], fill=hi)
    d.line([(cx + 1, 0), (cx + 1, 14)], fill=dk)
    # upper disc (spaceport platform)
    for (yc, rw, rh) in ((46, 50, 7), (30, 24, 4), (100, 22, 3)):
        d.ellipse([cx - rw, yc - rh, cx + rw, yc + rh], fill=mid)
        d.ellipse([cx - rw, yc - rh, cx + rw, yc + rh - 2], fill=hi)
        d.ellipse([cx - rw + 3, yc - rh + 1, cx + rw - 3, yc + rh - 3], fill=mid)
        d.line([(cx - rw + 2, yc + rh - 1), (cx + rw - 2, yc + rh - 1)], fill=dk2)
        d.line([(cx - rw, yc), (cx + rw, yc)], fill=dk)
        for x in range(cx - rw + 4, cx + rw - 3, 5):
            d.point((x, yc + 1), fill=(90, 150, 180))
            e.point((x, yc + 1), fill=win + (255,))
    # underside of big disc + support struts
    d.polygon([(cx - 46, 50), (cx + 46, 50), (cx + 10, 62), (cx - 10, 62)], fill=dk)
    d.line([(cx - 46, 50), (cx - 10, 62)], fill=dk2)
    d.line([(cx + 46, 50), (cx + 10, 62)], fill=dk2)
    for sx in (-30, -15, 15, 30):
        d.line([(cx + sx, 51), (cx + sx * 0.3, 60)], fill=dk2)
    # docking arms on the lower ring
    for s in (-1, 1):
        d.line([(cx + s * 22, 100), (cx + s * 34, 96)], fill=dk, width=2)
        d.rectangle([cx + s * 34 - 2, 94, cx + s * 34 + 2, 97], fill=mid)
    # outline sparingly (INK-ish dark blue)
    arr = np.array(im)
    a = arr[..., 3] > 0
    edge = a & ~(np.roll(a, 1, 1) & np.roll(a, -1, 1) & np.roll(a, 1, 0) & np.roll(a, -1, 0))
    arr[edge, :3] = (70, 76, 100)
    return Image.fromarray(arr, "RGBA"), em


def _terminal_layer(tod):
    base, em = C.cached(("terminal_raw",), _terminal_sprite)
    g = C.grade_rgba(base, tod, 0.3)
    amt = C.lit_amount(tod)
    if amt > 0:
        g = C.light_up(g, em, max(0.35, amt), glow_radius=2, glow_strength=0.6)
    return g


def terminal(img, cam_x, t, tod="day", dy=0, parallax=0.1):
    """The Terminal spaceport tower (base ~ row 150+dy, needle beyond the top)."""
    spr = C.cached(("terminal", tod), lambda: _terminal_layer(tod))
    sx = int((TERMINAL_SX - cam_x * parallax + 258) % 900 - 258)     # wraps for huge pans
    x0, y0 = sx - spr.width // 2, 150 + dy - spr.height + 12
    img.paste(spr, (x0, y0), spr)
    # blinking aviation beacons + little shuttles docking at the platform
    d = ImageDraw.Draw(img)
    cx = sx
    on = (t * 1.3) % 1.0 < 0.5
    for (bx, by) in ((0, 0), (-50, 46), (50, 46), (-22, 100), (22, 100)):
        if on ^ (bx < 0):
            d.point((cx + bx, y0 + by), fill=(255, 70, 60))
            if tod in ("night", "storm", "dusk"):
                d.point([(cx + bx - 1, y0 + by), (cx + bx + 1, y0 + by)], fill=(150, 40, 50))
    for k in range(2):
        per = 9.0
        u = ((t + k * per / 2) % per) / per
        side = 1 if k == 0 else -1
        ox = side * (60 + (1 - u) * 120) if u < 0.5 else side * (60 + (u - 0.5) * 2 * 120)
        ox = side * (54 + abs(u - 0.5) * 2 * 150)
        oy = 44 - abs(u - 0.5) * 2 * 30 + k * 6
        ship(img, cx + ox, y0 + oy, "shuttle", t, facing=-side, tod=tod, haze=0.35)


# ======================================================================== ships
def _ship_art(kind):
    """Returns (sprite RGBA, lights[(x, y, rgb, phase)], engines[(x, y, h)])."""
    lights, engines = [], []
    if kind == "saucer":
        w, h = 30, 13
        im = Image.new("RGBA", (w, h))
        d = ImageDraw.Draw(im)
        d.ellipse([10, 0, 19, 8], fill=(124, 196, 224))
        d.point([(12, 2), (13, 2), (12, 3)], fill=(214, 244, 252))
        d.ellipse([0, 5, 29, 12], fill=(170, 176, 198))
        d.ellipse([1, 5, 28, 9], fill=(206, 212, 228))
        d.line([(3, 9), (26, 9)], fill=(98, 104, 132))
        d.line([(5, 11), (24, 11)], fill=(120, 126, 152))
        for i, x in enumerate(range(4, 27, 5)):
            lights.append((x, 9, (255, 226, 90), i * 0.2))
        engines.append((15, 12, 3))
    elif kind == "shuttle":
        w, h = 24, 11
        im = Image.new("RGBA", (w, h))
        d = ImageDraw.Draw(im)
        d.polygon([(0, 3), (5, 1), (16, 1), (23, 6), (16, 9), (0, 8)], fill=(192, 196, 210))
        d.line([(1, 7), (16, 8)], fill=(130, 136, 156))
        d.line([(1, 5), (19, 6)], fill=(200, 72, 64))
        d.polygon([(2, 1), (5, 1), (3, -2)], fill=(160, 166, 184))
        d.rectangle([15, 2, 18, 3], fill=(96, 180, 216))
        d.polygon([(6, 8), (12, 8), (7, 10)], fill=(150, 156, 176))
        lights.append((22, 6, (255, 80, 70), 0.0))
        engines.append((0, 5, 3))
    elif kind == "cruiser":
        w, h = 86, 25
        im = Image.new("RGBA", (w, h))
        d = ImageDraw.Draw(im)
        d.polygon([(0, 9), (10, 7), (58, 7), (85, 13), (58, 19), (10, 20), (0, 17)], fill=(150, 156, 178))
        d.polygon([(0, 9), (10, 7), (58, 7), (85, 13), (0, 13)], fill=(178, 184, 202))
        d.line([(10, 7), (58, 7)], fill=(210, 214, 228))
        d.polygon([(10, 17), (58, 17), (84, 13), (58, 19), (10, 20), (0, 17)], fill=(104, 110, 136))
        d.rectangle([16, 1, 36, 7], fill=(160, 166, 188))
        d.rectangle([16, 1, 36, 2], fill=(196, 202, 218))
        d.line([(22, 1), (22, -3)], fill=(150, 156, 176))
        d.rectangle([40, 3, 50, 7], fill=(140, 146, 170))
        for x in range(18, 35, 3):
            lights.append((x, 4, (140, 226, 250), 0.0))
        d.line([(8, 15), (70, 15)], fill=(188, 64, 60))
        for x in range(12, 64, 4):
            lights.append((x, 11, (255, 214, 140), (x % 7) * 0.13))
        lights.append((84, 13, (255, 70, 60), 0.0))
        d.rectangle([0, 9, 4, 17], fill=(80, 84, 104))
        engines += [(0, 11, 3), (0, 15, 3)]
    elif kind == "pirate":
        w, h = 124, 42
        im = Image.new("RGBA", (w, h))
        d = ImageDraw.Draw(im)
        hull = [(0, 15), (18, 9), (86, 9), (123, 21), (98, 31), (24, 35), (0, 29)]
        d.polygon(hull, fill=(128, 84, 72))
        d.polygon([(0, 15), (18, 9), (86, 9), (123, 21), (0, 21)], fill=(154, 104, 86))
        d.line([(18, 9), (86, 9)], fill=(186, 134, 106))
        d.polygon([(24, 29), (98, 29), (98, 31), (24, 35), (0, 29)], fill=(88, 56, 54))
        for x in range(28, 96, 9):                    # keel spikes
            d.polygon([(x, 31), (x + 4, 31), (x + 1, 38)], fill=(96, 62, 58))
        d.rectangle([30, 1, 58, 9], fill=(140, 94, 80))
        d.rectangle([30, 1, 58, 2], fill=(176, 126, 102))
        d.rectangle([62, 3, 76, 9], fill=(126, 84, 74))
        d.line([(44, 1), (44, -4)], fill=(120, 80, 70))
        for x in (36, 70, 96):                         # cannons
            d.line([(x, 9), (x + 10, 5)], fill=(70, 60, 64), width=2)
        d.ellipse([46, 14, 58, 25], fill=(90, 60, 60))
        d.ellipse([48, 16, 56, 23], fill=(210, 190, 120))
        d.line([(52, 16), (52, 23)], fill=(90, 60, 60))
        for x in range(10, 110, 6):
            lights.append((x, 25, (255, 110, 70), (x % 5) * 0.2))
        for x in range(33, 57, 3):
            lights.append((x, 5, (255, 200, 120), 0.0))
        engines += [(0, 18, 4), (0, 25, 4)]
    elif kind == "kiheitai":
        w, h = 112, 46
        im = Image.new("RGBA", (w, h))
        d = ImageDraw.Draw(im)
        # wooden hull like a Japanese warship
        d.polygon([(0, 22), (104, 22), (111, 16), (100, 36), (14, 38), (2, 30)], fill=(96, 62, 50))
        for y in range(24, 38, 3):
            d.line([(4, y), (104, y)], fill=(78, 50, 44))
        d.line([(0, 22), (111, 16)], fill=(150, 104, 74))
        d.rectangle([2, 19, 104, 22], fill=(122, 84, 60))      # deck rail
        for x in range(4, 104, 6):
            d.line([(x, 17), (x, 21)], fill=(122, 84, 60))
        d.line([(2, 17), (104, 17)], fill=(150, 104, 74))
        # cabin with tiled roof
        d.rectangle([30, 8, 70, 18], fill=(200, 190, 168))
        for x in range(34, 68, 8):
            d.rectangle([x, 11, x + 4, 15], fill=(80, 64, 60))
            lights.append((x + 2, 13, (255, 200, 120), 0.0))
        d.polygon([(24, 9), (76, 9), (68, 2), (32, 2)], fill=(74, 70, 92))
        d.line([(32, 2), (68, 2)], fill=(110, 106, 130))
        # mast + purple banner
        d.line([(84, 20), (84, 0)], fill=(90, 64, 52), width=2)
        d.polygon([(86, 1), (98, 3), (86, 9)], fill=(120, 70, 150))
        d.line([(10, 20), (10, 6)], fill=(90, 64, 52))
        d.polygon([(11, 6), (18, 8), (11, 11)], fill=(120, 70, 150))
        # engine pods under the hull
        d.ellipse([20, 34, 44, 42], fill=(80, 76, 90))
        d.ellipse([60, 34, 84, 42], fill=(80, 76, 90))
        lights += [(32, 41, (170, 120, 255), 0.0), (72, 41, (170, 120, 255), 0.5)]
        engines += [(0, 27, 3)]
    else:  # mothership
        w, h = 236, 76
        im = Image.new("RGBA", (w, h))
        d = ImageDraw.Draw(im)
        d.ellipse([0, 22, 235, 60], fill=(72, 66, 92))
        d.ellipse([0, 22, 235, 50], fill=(96, 90, 118))
        d.ellipse([56, 2, 180, 40], fill=(84, 78, 106))
        d.ellipse([60, 3, 176, 30], fill=(112, 106, 136))
        d.ellipse([90, 6, 146, 20], fill=(134, 126, 156))
        for x in range(12, 226, 12):                       # hull panel ribs
            d.line([(x, 30), (x + 4, 52)], fill=(64, 58, 82))
        for yy in (36, 44):
            d.line([(8, yy), (227, yy)], fill=(64, 58, 82))
        for (sx, sy, L) in ((82, 8, 10), (118, 3, 14), (152, 8, 10), (40, 26, 6), (196, 26, 6)):
            d.line([(sx, sy), (sx, sy - L)], fill=(90, 84, 110))
            lights.append((sx, sy - L, (255, 60, 60), sx * 0.01))
        d.ellipse([92, 50, 144, 70], fill=(60, 50, 72))
        d.ellipse([100, 54, 136, 68], fill=(150, 40, 70))
        for i, x in enumerate(range(10, 228, 9)):
            lights.append((x, 47, (255, 120, 80), i * 0.07))
        for x in range(70, 170, 6):
            lights.append((x, 26, (255, 200, 140), (x % 4) * 0.2))
        engines.append((118, 62, 7))
    arr = np.array(im)
    a = arr[..., 3] > 0
    return im, lights, engines


def ship_size(kind, scale=1):
    im, _, _ = C.cached(("shipart", kind), lambda: _ship_art(kind))
    return im.width * scale + 2, im.height * scale + 2


def _ship_sprite(kind, scale, facing, tod, haze):
    im, lights, engines = C.cached(("shipart", kind), lambda: _ship_art(kind))
    g = C.grade_rgba(im, tod, haze) if (tod != "day" or haze > 0) else im
    ol = INK if haze < 0.3 else C.grade_color((40, 36, 56), tod, haze)
    g = outline(g, ol)
    if scale != 1:
        g = scale_nearest(g, scale)
    if facing < 0:
        g = flip_h(g)
    return g


def ship(img, x, y, kind, t, scale=1, facing=1, tod="day", haze=0.0, lights=True):
    """Draw an alien/space ship centred at (x, y). Blinking lights + engine
    flicker are animated from t. haze 0..1 fades it into the sky (distance)."""
    kind = kind if kind in SHIP_KINDS else "saucer"
    hz = round(float(haze), 2)
    spr = C.cached(("ship", kind, scale, facing, tod, hz), lambda: _ship_sprite(kind, scale, facing, tod, hz))
    x0, y0 = int(round(x - spr.width / 2)), int(round(y - spr.height / 2))
    if x0 > W or y0 > H or x0 + spr.width < 0 or y0 + spr.height < 0:
        return
    img.paste(spr, (x0, y0), spr)
    if not lights:
        return
    _, lts, engs = C.cached(("shipart", kind), lambda: _ship_art(kind))
    d = ImageDraw.Draw(img)
    s = scale
    wv = spr.width

    def P(px, py):
        sx = (px + 1) * s
        if facing < 0:
            sx = wv - 1 - sx - (s - 1)
        return x0 + sx, y0 + (py + 1) * s
    fade = 1 - hz * 0.6
    for (lx, ly, c, ph) in lts:
        v = math.sin((t * 2.2 + ph) * 2 * math.pi)
        if v > -0.2:
            cc = shade(c, (1.0 if v > 0.5 else 0.6) * fade)
            px, py = P(lx, ly)
            d.rectangle([px, py, px + s - 1, py + s - 1], fill=cc)
    for (ex, ey, eh) in engs:
        fl = 2 + int((t * 20 + ex) % 3)
        px, py = P(ex, ey)
        if kind == "mothership" or kind == "saucer":
            col = (255, 90, 120) if kind == "mothership" else (140, 230, 255)
            k = 0.5 + 0.5 * math.sin(t * 5)
            rr = int(eh * s * (0.8 + 0.3 * k))
            C.add_sprite(img, C.glow_sprite(rr + 3, col, round(0.5 + 0.5 * k, 1)), px - rr - 3, py - rr - 3)
            continue
        L = fl * s
        if facing > 0:
            d.rectangle([px - L, py - s, px - 1, py + s - 1], fill=shade((255, 150, 60), fade))
            d.rectangle([px - L // 2, py - s // 2, px - 1, py + max(0, s // 2 - 1)], fill=shade((255, 236, 150), fade))
        else:
            d.rectangle([px + s, py - s, px + s + L - 1, py + s - 1], fill=shade((255, 150, 60), fade))


# ======================================================================== fleet
def _dark_overlay(level):
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = 34, 10, 30
    yy = np.arange(H, dtype=np.float32)[:, None]
    a = np.clip(0.62 - yy / 150 * 0.5, 0.06, 0.62) * level
    q = np.floor(a * 12 + C.bayer(H, W)) / 12
    arr[..., 3] = (np.clip(q, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def fleet(img, t, density=1.0, cam_x=0):
    """Alien armada filling the sky (final arc). density 0..1 scales the
    darkening and the number of ships. Draw after the sky, before the city."""
    if density <= 0:
        return
    lvl = round(clamp(density) * 4) / 4
    ov = C.cached(("fleetdark", lvl), lambda: _dark_overlay(lvl))
    img.paste(ov, (0, 0), ov)
    n_far = int(26 * density)
    for i in range(n_far):
        r = rng("fleetfar", i)
        kind = r.choice(("cruiser", "saucer", "cruiser", "pirate"))
        spx = r.uniform(3, 7)
        span = W + 160
        x = (r.uniform(0, span) - t * spx - cam_x * 0.08) % span - 80
        y = r.uniform(58, 118) + math.sin(t * 0.5 + i) * 1.5
        ship(img, x, y, kind, t + i, facing=-1, tod="night", haze=0.72)
    # looming mothership (behind the mid ships)
    mx = W / 2 - cam_x * 0.05 + math.sin(t * 0.15) * 6
    my = 18 + math.sin(t * 0.4) * 2 + (1 - density) * -30
    ship(img, mx, my, "mothership", t, tod="night", haze=0.1)
    # beams under the mothership (dithered)
    if density > 0.5:
        k = 0.5 + 0.5 * math.sin(t * 1.3)
        overlay_rect(img, int(mx) - 6, int(my) + 30, 12, H, (255, 90, 130), 0.08 + 0.06 * k)
    n_mid = int(7 * density)
    for i in range(n_mid):
        r = rng("fleetmid", i)
        kind = r.choice(("cruiser", "pirate", "cruiser"))
        spx = r.uniform(6, 10)
        span = W + 260
        x = (r.uniform(0, span) - t * spx - cam_x * 0.2) % span - 130
        y = r.uniform(62, 128)
        ship(img, x, y, kind, t + i * 0.3, facing=-1, tod="night", haze=0.3)


# ======================================================================== city layers
def _far_city():
    L = WrapLayer(_FAR_P, 216)
    d, e = L.d, L.e
    r = rng("farcity")
    x = -40
    while x < _FAR_P + 40:
        w = r.randint(14, 34)
        top = r.randint(128, 142)
        kind = r.random()
        X = L.x(x)
        if kind < 0.12:           # tall amanto block
            top2 = r.randint(96, 118)
            d.rectangle([X, top2, X + w, 216], fill=(120, 126, 148))
            d.line([(X, top2), (X + w, top2)], fill=(150, 156, 176))
            window_grid(d, e, X + 2, top2 + 3, X + w - 2, 200, 2, 2, 2, r, 0.5)
            d.line([(X + w // 2, top2), (X + w // 2, top2 - 8)], fill=(120, 126, 148))
        else:
            d.polygon([(X - 3, top + 6), (X + 3, top), (X + w - 3, top), (X + w + 3, top + 6)], fill=(94, 100, 122))
            d.line([(X + 3, top), (X + w - 3, top)], fill=(120, 126, 150))
            d.rectangle([X - 1, top + 7, X + w + 1, 216], fill=(150, 146, 146))
            for wx in range(X + 2, X + w - 2, 6):
                if r.random() < 0.55:
                    e.rectangle([wx, top + 10, wx + 1, top + 11], fill=GLOW + (255,))
        x += w + r.randint(-4, 3)
    return L.finish()


def _castle_parts(d, cx, base):
    stone, stone_d, mortar = (156, 150, 140), (130, 124, 118), (104, 100, 96)
    wallc, walls = (236, 234, 226), (198, 196, 192)
    rf, rf_d, rf_h = (84, 104, 112), (58, 74, 84), (118, 140, 146)
    gold = (238, 196, 84)
    # stone base with curved (fan) sides
    bh = 20
    for i in range(bh):
        f = i / (bh - 1)
        hw = 30 + f * f * 12
        y = base - bh + i
        d.line([(cx - hw, y), (cx + hw, y)], fill=stone if (i % 4) else mortar)
        d.point((cx - hw, y), fill=(176, 170, 160))
        d.point((cx + hw, y), fill=stone_d)
        if i % 4:
            off = 0 if (i // 4) % 2 else 4
            d.point([(xx, y) for xx in range(int(cx - hw) + off, int(cx + hw), 8)], fill=mortar)
    # tiers
    widths = [50, 40, 30, 22]
    wh = [12, 10, 9, 9]
    y = base - bh
    for k, (w, hgt) in enumerate(zip(widths, wh)):
        x0, x1 = cx - w // 2, cx + w // 2
        d.rectangle([x0, y - hgt, x1, y], fill=wallc)
        d.line([(x1 - 1, y - hgt), (x1 - 1, y)], fill=walls)
        d.line([(x0, y - 2), (x1, y - 2)], fill=walls)
        for wx in range(x0 + 3, x1 - 3, 5):
            d.rectangle([wx, y - hgt + 3, wx + 1, y - hgt + 5], fill=(60, 56, 64))
        y -= hgt
        # roof with upturned eaves
        nw = widths[k + 1] if k + 1 < len(widths) else 10
        rh = 5 if k < 3 else 7
        ex0, ex1 = x0 - 5, x1 + 5
        for j in range(rh):
            f = j / (rh - 1)
            a = ex0 + (cx - nw // 2 - 1 - ex0) * (1 - f) * 0 + (cx - nw // 2 - 1 - ex0) * (1 - f)
            yy = y - j
            xa = int(ex0 + (cx - nw // 2 - 1 - ex0) * f)
            xb = int(ex1 - (ex1 - (cx + nw // 2 + 1)) * f)
            d.line([(xa, yy), (xb, yy)], fill=rf if j else rf_d)
            d.point((xa, yy), fill=rf_h)
        d.point([(ex0 - 1, y - 1), (ex1 + 1, y - 1)], fill=rf_d)     # upturned tips
        d.line([(ex0, y + 1), (ex1, y + 1)], fill=(70, 70, 84))
        if k in (0, 1):                                            # chidori gable
            gw = 7 - k
            d.polygon([(cx - gw, y - 1), (cx, y - rh - 1), (cx + gw, y - 1)], fill=rf_d)
            d.polygon([(cx - gw + 2, y - 1), (cx, y - rh + 1), (cx + gw - 2, y - 1)], fill=wallc)
        y -= rh
    # top ridge + golden shachihoko
    d.line([(cx - 7, y), (cx + 7, y)], fill=rf_d)
    for s in (-1, 1):
        d.point([(cx + s * 7, y - 1), (cx + s * 7, y - 2), (cx + s * 8, y - 3), (cx + s * 6, y - 1)], fill=gold)


def _castle_layer():
    L = WrapLayer(_CASTLE_P, 216)
    d = L.d
    # the castle sits at world x such that it lands at CASTLE_SX at cam 0
    cx = L.x(CASTLE_SX)
    base = 150
    # hill + pines around the base
    d.ellipse([cx - 90, base - 10, cx + 90, base + 40], fill=(74, 100, 84))
    r = rng("castlepines")
    for i in range(26):
        px = cx + r.randint(-84, 84)
        py = base - 6 + abs(px - cx) * 0.08 + r.randint(-2, 4)
        d.ellipse([px - 5, py - 4, px + 5, py + 3], fill=(58, 86, 72))
        d.ellipse([px - 4, py - 4, px + 2, py], fill=(80, 112, 90))
    # outer walls (white with dark roofs) on the hill
    for (x0, x1, y) in ((cx - 78, cx - 36, base - 2), (cx + 36, cx + 80, base - 2)):
        d.rectangle([x0, y - 5, x1, y], fill=(226, 224, 216))
        d.line([(x0 - 1, y - 6), (x1 + 1, y - 6)], fill=(70, 86, 96))
        d.line([(x0 - 2, y - 7), (x1 + 2, y - 7)], fill=(90, 110, 118))
    _castle_parts(d, cx, base - 2)
    return L.finish()


def _pagoda(d, e, cx, base):
    wallc, dk = (160, 72, 58), (104, 48, 44)
    rf, rf_d, rf_h = (74, 80, 100), (52, 56, 72), (104, 110, 132)
    y = base
    for k in range(5):
        w = 18 - k * 2
        d.rectangle([cx - w // 2, y - 7, cx + w // 2, y], fill=wallc)
        d.line([(cx + w // 2, y - 7), (cx + w // 2, y)], fill=dk)
        d.rectangle([cx - 1, y - 5, cx + 1, y - 1], fill=(60, 40, 40))
        e.rectangle([cx - 1, y - 5, cx + 1, y - 1], fill=GLOW + (200,))
        y -= 7
        ew = w // 2 + 7
        for j in range(4):
            d.line([(cx - ew + j * 2, y - j), (cx + ew - j * 2, y - j)], fill=rf if j else rf_d)
            d.point((cx - ew + j * 2, y - j), fill=rf_h)
        d.point([(cx - ew - 1, y - 1), (cx + ew + 1, y - 1)], fill=rf_d)
        y -= 4
    d.line([(cx, y), (cx, y - 14)], fill=(170, 150, 90))
    for k in range(4):
        d.line([(cx - 1, y - 3 - k * 3), (cx + 1, y - 3 - k * 3)], fill=(200, 176, 100))


def _watchtower(d, cx, base):
    wd = WOOD_D
    d.line([(cx - 7, base), (cx - 4, base - 40)], fill=wd.mid, width=2)
    d.line([(cx + 7, base), (cx + 4, base - 40)], fill=wd.dark, width=2)
    for y in range(base - 36, base, 5):
        d.line([(cx - 6, y), (cx + 6, y)], fill=wd.dark)
    d.rectangle([cx - 6, base - 44, cx + 6, base - 40], fill=wd.mid)
    d.polygon([(cx - 9, base - 45), (cx, base - 52), (cx + 9, base - 45)], fill=(80, 84, 100))
    d.ellipse([cx - 2, base - 45, cx + 2, base - 41], fill=(190, 150, 70))


def _modern_block(d, e, x, w, top, base, r, neon=None):
    d.rectangle([x, top, x + w, base], fill=CONCRETE.mid)
    d.line([(x, top), (x, base)], fill=CONCRETE.hi)
    d.line([(x + w, top), (x + w, base)], fill=CONCRETE.dark)
    flat_roof(d, x, x + w, top)
    window_grid(d, e, x + 3, top + 5, x + w - 3, base - 4, 3, 3, 2, r, 0.55)
    # antenna / dish
    d.line([(x + w - 5, top - 3), (x + w - 5, top - 14)], fill=(110, 110, 124))
    d.line([(x + w - 8, top - 10), (x + w - 2, top - 10)], fill=(110, 110, 124))
    d.ellipse([x + 3, top - 8, x + 9, top - 3], fill=(190, 194, 204))
    if neon:
        col, txt = neon
        d.rectangle([x + 2, top - 1 + 6, x + 13, top + 6 + len(txt) * 12 + 2], fill=(50, 40, 56))
        text_on(d._image, x + 8, top + 7, txt, shade(col, 0.55), e, col, vertical=True)


def _mid_city():
    L = WrapLayer(_MID_P, 216)
    d, e = L.d, L.e
    r = rng("midcity")
    x = -30
    idx = 0
    specials = {3: "pagoda", 7: "tower", 11: "modern", 15: "kura", 19: "modern2", 23: "tower"}
    while x < _MID_P + 30:
        X = L.x(x)
        sp = specials.get(idx)
        if sp == "pagoda":
            _pagoda(d, e, X + 14, 150)
            w = 28
            wall(d, X - 6, 150, X + w + 6, 216, PLASTER, texture=False)
            roof(d, X - 8, X + w + 8, 146, 151, TILE, inset=2, ridge=False)
        elif sp == "tower":
            _watchtower(d, X + 10, 150)
            w = 20
            wall(d, X - 4, 148, X + w + 4, 216, Pal2(), texture=False)
            roof(d, X - 6, X + w + 6, 144, 149, TILE_B, inset=2, ridge=False)
        elif sp in ("modern", "modern2"):
            w = r.randint(30, 40)
            neon = ((255, 90, 170), "酒场") if sp == "modern" else ((90, 220, 255), "电视")
            _modern_block(d, e, X, w, r.randint(96, 110), 216, r, neon)
        else:
            w = r.randint(34, 58)
            ridge = r.randint(134, 146)
            eave = ridge + r.randint(8, 11)
            pal = TILE if r.random() < 0.7 else TILE_B
            if sp == "kura":
                wall(d, X, eave, X + w, 216, PLASTER, texture=False)
                d.rectangle([X + w // 2 - 3, eave + 5, X + w // 2 + 3, eave + 10], fill=(50, 44, 48))
            else:
                wall(d, X, eave, X + w, 216, PLASTER if r.random() < 0.5 else Pal2(), posts=[X, X + w - 3], texture=False)
                for wx in range(X + 5, X + w - 8, 12):
                    shoji(d, e if r.random() < 0.6 else None, wx, eave + 5, wx + 7, eave + 12, cols=2, rows=2)
            roof(d, X - 3, X + w + 3, ridge, eave, pal, inset=6)
        x += w + r.randint(-2, 3)
        idx += 1
    return L.finish()


def Pal2():
    from ._draw import Pal
    return Pal((150, 108, 78), (124, 88, 64), (98, 68, 52), (70, 50, 42))


def _near_roofs():
    L = WrapLayer(_NEAR_P, 216)
    d, e = L.d, L.e
    r = rng("nearroofs")
    x = -20
    while x < _NEAR_P + 20:
        X = L.x(x)
        w = r.randint(80, 130)
        ridge = r.randint(176, 184)
        eave = ridge + 18
        pal = TILE if r.random() < 0.75 else TILE_B
        wall(d, X, eave, X + w, 216, WOOD_D, texture=False)
        boards(d, X, eave + 2, X + w, 216, WOOD_D, step=5)
        for wx in range(X + 8, X + w - 16, 24):
            shoji(d, e if r.random() < 0.7 else None, wx, eave + 6, wx + 12, 214, cols=3, rows=3)
        roof(d, X - 4, X + w + 4, ridge, eave, pal, inset=14)
        x += w + r.randint(-6, 2)
    return L.finish()


def skyline(img, cam_x, t, tod="day", ships=True, armada=0.0, sky=True, near=True, dy=0):
    """Edo panorama. See module docstring."""
    if sky:
        C.sky(img, tod, t, horizon=150 + dy)
        C.clouds(img, t, cam_x, tod, seed=3, count=6, y0=4, y1=70 + dy)
    C.far_mountains(img, cam_x, tod, 138 + dy)
    if armada > 0:
        fleet(img, t, armada, cam_x)
    if ships and armada < 0.5:
        _ambient_ships(img, cam_x, t, tod, dy, far=True)
    terminal(img, cam_x, t, tod, dy)
    far = graded_layer(("edo_far",), _far_city, tod, depth=0.5, glow_radius=2, glow_strength=0.3)
    paste_layer(img, far, _FAR_P, cam_x * 0.25, dy)
    if ships and armada < 0.5:
        _ambient_ships(img, cam_x, t, tod, dy)
    cas = graded_layer(("edo_castle",), _castle_layer, tod, depth=0.32)
    paste_layer(img, cas, _CASTLE_P, cam_x * 0.4, dy)
    mid = graded_layer(("edo_mid",), _mid_city, tod, depth=0.18, glow_radius=3, glow_strength=0.45)
    paste_layer(img, mid, _MID_P, cam_x * 0.6, dy)
    if near:
        nr = graded_layer(("edo_near",), _near_roofs, tod, depth=0.0, glow_radius=3, glow_strength=0.5)
        paste_layer(img, nr, _NEAR_P, cam_x, dy)


def _ambient_ships(img, cam_x, t, tod, dy=0, far=False):
    plan = (("saucer", 42, 9, 0.2, 0.25, 1, False), ("saucer", 66, -6, 0.3, 0.15, 1, False),
            ("cruiser", 16, 3.5, 0.12, 0.5, 1, True), ("shuttle", 84, -14, 0.35, 0.1, 1, False),
            ("cruiser", 34, -2.2, 0.08, 0.62, 1, True))
    for i, (kind, y, spd, par, hz, sc, is_far) in enumerate(plan):
        if is_far != far:
            continue
        span = W + 240
        x = (i * 157 + t * spd - cam_x * par) % span - 120
        yy = y + dy + math.sin(t * 0.9 + i) * 2
        ship(img, x, yy, kind, t, scale=sc, facing=1 if spd > 0 else -1, tod=tod, haze=hz)


# ======================================================================== roof_walk
def _walk_layer():
    L = WrapLayer(_WALK_P, _WALK_H, margin=120)
    d, e = L.d, L.e
    pal = TILE
    top = _WALK_TOP             # ridge row inside the layer (feet line)
    eave = top + 40
    r = rng("roofwalk")
    seg_w = 256
    for s in range(-1, _WALK_P // seg_w + 1):
        X0 = L.x(s * seg_w)
        X1 = X0 + seg_w - 1
        # slope: rows grow taller toward the eave (perspective)
        y = top + 3
        row = 0
        rh = 3.0
        while y < eave:
            h = int(round(rh))
            y1 = min(eave, y + h)
            d.rectangle([X0, y, X1, y1 - 1], fill=pal.mid)
            d.line([(X0, y1 - 1), (X1, y1 - 1)], fill=pal.dk2)
            if h >= 3:
                d.line([(X0, y), (X1, y)], fill=pal.hi)
            step = 5 + row // 2
            off = (row % 2) * (step // 2)
            for cx in range(X0 + off, X1, step):
                d.line([(cx, y + 1), (cx, y1 - 2)], fill=pal.dk2)
                d.line([(cx + 1, y + 1), (cx + 1, y1 - 2)], fill=pal.dark)
                d.line([(cx + step - 2, y + 1), (cx + step - 2, y1 - 2)], fill=pal.hi)
                if h >= 5:
                    d.point((cx + 2, y + 1), fill=pal.hi)
            y = y1
            rh = min(9, rh * 1.25)
            row += 1
        # eave: round tile ends + deep shadow
        d.rectangle([X0, eave, X1, eave + 2], fill=pal.dk2)
        for cx in range(X0 + 2, X1, 6):
            d.ellipse([cx - 2, eave - 1, cx + 2, eave + 3], fill=pal.dark)
            d.point((cx - 1, eave), fill=pal.hi)
        d.rectangle([X0, eave + 3, X1, _WALK_H], fill=(40, 36, 48))
        # lit windows of the alley below
        for wx in range(X0 + 18, X1 - 20, 44):
            if r.random() < 0.7:
                d.rectangle([wx, eave + 12, wx + 10, eave + 22], fill=(70, 60, 66))
                e.rectangle([wx, eave + 12, wx + 10, eave + 22], fill=GLOW + (255,))
                d.line([(wx + 5, eave + 12), (wx + 5, eave + 22)], fill=(60, 44, 40))
                e.line([(wx + 5, eave + 12), (wx + 5, eave + 22)], fill=CLEAR)
        # ridge cap (munegawara), flat top = feet line
        d.rectangle([X0, top - 1, X1, top + 3], fill=pal.dk2)
        d.line([(X0, top - 1), (X1, top - 1)], fill=pal.hi)
        d.line([(X0, top), (X1, top)], fill=pal.mid)
        for cx in range(X0 + 3, X1, 8):
            d.point([(cx, top + 1), (cx + 1, top + 1)], fill=pal.dark)
        # onigawara ornament at the segment start + a TV antenna
        ox = X0 + 2
        d.rectangle([ox - 3, top - 7, ox + 4, top + 3], fill=pal.dk2)
        d.rectangle([ox - 2, top - 6, ox + 3, top - 1], fill=pal.dark)
        d.point([(ox, top - 4), (ox + 1, top - 4)], fill=pal.hi)
        ax = X0 + 150
        d.line([(ax, top - 1), (ax, top - 22)], fill=(96, 96, 108))
        for k, wv in enumerate((10, 8, 6)):
            d.line([(ax - wv // 2, top - 20 + k * 4), (ax + wv // 2, top - 20 + k * 4)], fill=(96, 96, 108))
    return L.finish()


def roof_walk(img, cam_x, y, t, tod="day"):
    """Walkable rooftop (ridge = feet line at y). Parallax 1.0 with cam_x."""
    lay = graded_layer(("roofwalk",), _walk_layer, tod, depth=0.0, glow_radius=3, glow_strength=0.5)
    y0 = int(y) - _WALK_TOP
    paste_layer(img, lay, _WALK_P, cam_x, y0)
    if y0 + _WALK_H < H:      # fill whatever is left below with the alley shadow
        img.paste(C.grade_color((40, 36, 48), tod), (0, y0 + _WALK_H, W, H))
