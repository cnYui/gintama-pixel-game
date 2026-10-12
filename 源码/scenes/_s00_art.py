"""Private art for s00 (prologue). Everything static is built once and cached
at module level; per-frame helpers only paste / draw a few primitives."""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import W, H, rng, clamp, lerp
from engine.gfx import INK, PAL, outline, shade, mix, rotate_nearest
from engine.text import font
from bg import common as C

_CACHE = {}


def cached(key, fn):
    v = _CACHE.get(key)
    if v is None:
        v = fn()
        _CACHE[key] = v
    return v


def bayer(h, w, ox=0, oy=0):
    return C.bayer(h, w, ox, oy)


# ====================================================================== silhouettes
def rim_silhouette(spr, body=(22, 12, 26), rim=(255, 170, 96), rim_top=None, sides=(1, -1)):
    """Turn a character sprite into a back-lit silhouette with a 1px rim light.
    sides: which horizontal edges get the rim (+1 = right edge, -1 = left)."""
    a = np.asarray(spr)
    al = a[..., 3] > 0
    out = np.zeros_like(a)
    out[al] = tuple(body) + (255,)
    rt = rim_top or rim
    up = np.zeros_like(al)
    up[1:] = al[:-1]
    top_edge = al & ~up
    out[top_edge] = tuple(rt) + (255,)
    for s in sides:
        nb = np.zeros_like(al)
        if s > 0:
            nb[:, :-1] = al[:, 1:]
        else:
            nb[:, 1:] = al[:, :-1]
        e = al & ~nb
        out[e] = tuple(rim) + (255,)
    return Image.fromarray(out, "RGBA")


def paste_feet(img, spr, ax, ay, x, y):
    img.paste(spr, (int(round(x - ax)), int(round(y - ay))), spr)


# ====================================================================== shot 1: descent
SKY1_H = 216 + 300          # tall sky strip (parallax 0.7 of a 420 px descent)


def _space_sky():
    h = SKY1_H
    stops = [(0.0, (2, 2, 9)), (0.30, (6, 6, 22)), (0.55, (14, 16, 44)),
             (0.78, (30, 30, 72)), (0.92, (58, 46, 96)), (1.0, (92, 62, 108))]
    arr = C.vgradient(h, W, stops, bands=22).astype(np.int16)
    r = rng("s00sky")
    # milky way: diagonal dithered band of faint violet light + dense dim stars
    yy, xx = np.mgrid[0:h, 0:W].astype(np.float32)
    dist = np.abs((yy - 40) - (xx - 40) * 0.55) / 34.0
    band = np.clip(1 - dist, 0, 1) * np.clip(1 - yy / 330.0, 0, 1)
    bz = bayer(h, W)
    arr += ((band * 0.9 > bz) * 1)[..., None] * np.array([14, 10, 26], np.int16)
    arr += ((band * 0.45 > bz) * 1)[..., None] * np.array([12, 10, 20], np.int16)
    for _ in range(900):
        x, y = r.randrange(W), int(r.random() ** 1.6 * (h - 60))
        if band[y, x] > r.random() * 1.4:
            v = r.randint(70, 150)
            arr[y, x] = (v, v, v + 30)
    for _ in range(260):
        x, y = r.randrange(W), int(r.random() ** 1.3 * (h - 40))
        v = r.randint(110, 255)
        c = r.choice(((v, v, v), (v, v - 20, v - 60 if v > 60 else v), (v - 40 if v > 40 else v, v - 20 if v > 20 else v, v)))
        arr[y, x] = c
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def space_sky(img, alt):
    """alt = camera altitude (420 = deep space, 0 = over the rooftops)."""
    sky = cached("space_sky", _space_sky)
    top = int(round(SKY1_H - H - alt * 0.7))
    top = max(0, min(SKY1_H - H, top))
    img.paste(sky.crop((0, top, W, top + H)), (0, 0))


def _twinkles():
    r = rng("s00tw")
    out = []
    for i in range(46):
        out.append((r.randrange(W), r.uniform(-300, 140), r.uniform(2, 6), r.uniform(0, 6.28),
                    r.choice(((255, 255, 255), (200, 214, 255), (255, 236, 200)))))
    return out


def twinkles(img, t, alt):
    d = ImageDraw.Draw(img)
    for (x, y0, sp, ph, c) in cached("twinkles", _twinkles):
        y = y0 + alt * 0.7
        if y < 0 or y >= H - 30:
            continue
        v = math.sin(t * sp + ph)
        if v < 0.2:
            continue
        d.point((x, y), fill=c)
        if v > 0.8:
            cc = shade(c, 0.55)
            d.point([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], fill=cc)


def _old_town():
    """Old Edo town (no Terminal, no amanto buildings): two rows of kawara-roofed
    houses with shoji windows, a pagoda and a fire watch-tower. Day colours;
    graded to night by old_town_layer()."""
    from bg._draw import roof, wall, shoji, boards, TILE, TILE_B, WOOD_D, PLASTER, Pal
    from bg.edo import _pagoda, _watchtower
    w = W + 160
    base = Image.new("RGBA", (w, H))
    emis = Image.new("RGBA", (w, H))
    d, e = ImageDraw.Draw(base), ImageDraw.Draw(emis)
    r = rng("s00town")
    brown = Pal((150, 108, 78), (124, 88, 64), (98, 68, 52), (70, 50, 42))
    # back row
    _watchtower(d, 30, 150)
    _pagoda(d, e, 318, 150)
    x = -10
    while x < w:
        ww = r.randint(26, 46)
        if 300 < x + ww // 2 < 336:
            x += ww
            continue
        ridge = r.randint(138, 146)
        eave = ridge + r.randint(7, 9)
        wall(d, x, eave, x + ww, H, PLASTER if r.random() < 0.5 else brown, texture=False)
        for wx in range(x + 4, x + ww - 7, 10):
            if r.random() < 0.55:
                shoji(d, e, wx, eave + 4, wx + 5, eave + 9, cols=2, rows=2)
        roof(d, x - 3, x + ww + 3, ridge, eave, TILE if r.random() < 0.7 else TILE_B, inset=5)
        x += ww + r.randint(-2, 2)
    # front row
    x = -20
    while x < w:
        ww = r.randint(48, 78)
        ridge = r.randint(154, 162)
        eave = ridge + r.randint(10, 13)
        wall(d, x, eave, x + ww, H, WOOD_D, texture=False)
        boards(d, x, eave + 2, x + ww, H, WOOD_D, step=5)
        for wx in range(x + 6, x + ww - 12, 17):
            if r.random() < 0.8:
                shoji(d, e, wx, eave + 5, wx + 9, eave + 14, cols=3, rows=2)
        roof(d, x - 4, x + ww + 4, ridge, eave, TILE if r.random() < 0.75 else TILE_B, inset=9)
        x += ww + r.randint(-5, 1)
    return base, emis


def old_town_layer(tod="night"):
    def mk():
        base, emis = _old_town()
        g = C.grade_rgba(base, tod, 0.12)
        return C.light_up(g, emis, C.lit_amount(tod), glow_radius=3, glow_strength=0.5)
    return cached(("oldtown", tod), mk)


def edo_layers(img, alt, tod="night", pan=0.0):
    """Old Edo panorama rising from the bottom as the camera descends (alt->0)."""
    C.far_mountains(img, pan * 0.3, tod, int(136 + alt * 0.85))
    try:
        from bg._draw import graded_layer, paste_layer
        from bg import edo as E
        cas = graded_layer(("edo_castle",), E._castle_layer, tod, depth=0.32)
        paste_layer(img, cas, E._CASTLE_P, -40 + pan * 0.5, int(alt * 0.9))
        town = old_town_layer(tod)
        ox = int(40 + pan * 0.7)
        c = town.crop((ox, 0, ox + W, H))
        img.paste(c, (0, int(alt * 0.95)), c)
        nr = graded_layer(("edo_near",), E._near_roofs, tod, depth=0.0, glow_radius=3, glow_strength=0.5)
        paste_layer(img, nr, E._NEAR_P, 200 + pan, int(alt))
    except Exception:          # shared-module internals changed -> fall back to the public panorama
        from bg import edo as E
        E.skyline(img, pan, 0.0, tod, ships=False, sky=False, dy=int(alt))


def beam(img, x0, y0, x1, y1, w0, w1, color, alpha):
    """Translucent searchlight cone from (x0,y0) (width w0) to (x1,y1) (width w1)."""
    if alpha <= 0:
        return
    m = Image.new("L", (W, H), 0)
    dm = ImageDraw.Draw(m)
    a = int(255 * clamp(alpha))
    dm.polygon([(x0 - w0, y0), (x0 + w0, y0), (x1 + w1, y1), (x1 - w1, y1)], fill=a)
    dm.polygon([(x0 - w0 * 0.4, y0), (x0 + w0 * 0.4, y0), (x1 + w1 * 0.45, y1), (x1 - w1 * 0.45, y1)],
               fill=min(255, int(a * 1.7)))
    # dither the mask so the beam stays pixel-y
    arr = np.asarray(m).astype(np.float32) / 255.0
    q = (np.floor(arr * 4 + bayer(H, W) * 0.999) / 4.0 * 255).astype(np.uint8)
    img.paste(tuple(color), (0, 0, W, H), Image.fromarray(q, "L"))


# ====================================================================== shot 2: sunset war
def _sun(r):
    n = 2 * r + 1
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.hypot(xx - r, yy - r)
    body = d <= r
    arr = np.zeros((n, n, 4), np.uint8)
    f = yy / (n - 1)
    stops = [(0.0, (255, 246, 190)), (0.35, (255, 214, 110)), (0.62, (254, 160, 62)),
             (0.82, (246, 104, 60)), (1.0, (224, 64, 72))]
    bands = np.floor(f * 9 + bayer(n, n) * 0.999) / 9.0
    ps = np.array([s[0] for s in stops], np.float32)
    cs = np.array([s[1] for s in stops], np.float32)
    for c in range(3):
        arr[..., c] = np.interp(bands, ps, cs[:, c]).astype(np.uint8)
    arr[..., 3] = body * 255
    # retro horizontal cuts in the lower half (gaps widen toward the bottom)
    y = r + 4
    gap = 1
    while y < n:
        arr[int(y):int(y) + gap, :, 3] = 0
        y += max(3, 9 - gap * 2)
        gap = min(4, gap + 1) if (y - r) > r * 0.45 else gap
    return Image.fromarray(arr, "RGBA")


def sun(img, x, y, r, glow=True):
    spr = cached(("sun", r), lambda: _sun(r))
    if glow:
        C.add_sprite(img, C.glow_sprite(int(r * 1.9), (255, 150, 80), 0.8), x - int(r * 1.9), y - int(r * 1.9))
    img.paste(spr, (int(x) - r, int(y) - r), spr)


def smoke_column(img, t, x, y_base, h, seed, color=(46, 30, 44), width=10, lean=0.35):
    """Rising dark smoke column (analytic puffs drifting upward and leaning)."""
    d = ImageDraw.Draw(img)
    n = 12
    for i in range(n):
        r = rng("smk", seed, i)
        k = ((t * 0.18 + i / n + r.uniform(0, 0.05)) % 1.0)
        yy = y_base - k * h
        xx = x + k * h * lean + math.sin(t * 0.9 + i) * 2
        rad = width * (0.5 + k * 1.1) * r.uniform(0.8, 1.2)
        col = mix(color, (120, 70, 80), k * 0.45)
        d.ellipse([xx - rad, yy - rad * 0.7, xx + rad, yy + rad * 0.7], fill=col)


def nobori(img, x, y, t, h=36, color=(236, 226, 204), mark=(160, 30, 40), seed=0, torn=False, dark=None):
    """Tall war banner on a pole planted at (x, y); cloth flutters."""
    d = ImageDraw.Draw(img)
    pole = dark or (60, 40, 36)
    d.line([(x, y), (x, y - h)], fill=pole, width=1)
    d.line([(x, y - h), (x + 9, y - h)], fill=pole)
    cw, ch = 8, int(h * 0.62)
    top = y - h + 1
    pts_l, pts_r = [], []
    for j in range(0, ch + 1, 3):
        wv = math.sin(t * 7 + j * 0.35 + seed) * (1 + j / ch * 1.5)
        pts_l.append((x + 1 + wv * 0.4, top + j))
        pts_r.append((x + 1 + cw + wv, top + j))
    poly = pts_l + list(reversed(pts_r))
    col = color if dark is None else dark
    d.polygon(poly, fill=col, outline=INK if dark is None else dark)
    if dark is None:
        mx = x + 1 + cw // 2 + math.sin(t * 7 + 6 * 0.35 + seed)
        d.ellipse([mx - 2, top + 5, mx + 2, top + 9], fill=mark)
    if torn:
        by = top + ch
        for k in range(3):
            d.point((x + 2 + k * 3, by + 1 + k % 2), fill=col)


def crows(img, t, t0, x0, y0, vx, vy, n=3, color=(20, 10, 20), seed=0):
    d = ImageDraw.Draw(img)
    dt = t - t0
    for i in range(n):
        r = rng("crow", seed, i)
        x = x0 + dt * vx + r.uniform(-18, 18)
        y = y0 + dt * vy + r.uniform(-8, 8) + math.sin(t * 3 + i) * 2
        up = int((t * 8 + i * 1.7)) % 2 == 0
        if up:
            d.line([(x - 3, y - 2), (x, y), (x + 3, y - 2)], fill=color)
        else:
            d.line([(x - 3, y + 1), (x, y), (x + 3, y + 1)], fill=color)
        d.point((x, y - 1), fill=color)


def big_crow(img, x, y, t, color=(22, 18, 28)):
    """A readable crow (~15 px wingspan) flying left, flapping at 6 fps — the
    'awkward silence' crow of Gintama comedy."""
    d = ImageDraw.Draw(img)
    x, y = int(x), int(y)
    up = int(t * 6) % 2 == 0
    d.ellipse([x - 3, y - 2, x + 4, y + 2], fill=color)          # body
    d.rectangle([x - 5, y - 2, x - 3, y], fill=color)             # head
    d.point((x - 6, y - 1), fill=(210, 170, 60))                  # beak
    d.polygon([(x + 4, y), (x + 8, y - 1), (x + 8, y + 2)], fill=color)   # tail
    if up:
        d.polygon([(x - 1, y - 1), (x + 3, y - 1), (x + 6, y - 8), (x + 2, y - 6)], fill=color)
        d.polygon([(x - 1, y - 1), (x + 2, y - 1), (x - 4, y - 7)], fill=color)
    else:
        d.polygon([(x - 1, y + 1), (x + 3, y + 1), (x + 7, y + 6), (x + 2, y + 5)], fill=color)
        d.polygon([(x - 1, y + 1), (x + 2, y + 1), (x - 3, y + 6)], fill=color)
    d.point((x - 4, y - 1), fill=(240, 240, 240))                 # eye


# ====================================================================== shot 3: rain
def _katana():
    """Big katana pointing RIGHT (hilt at left). ~60 x 9 px, INK outlined."""
    w, h = 62, 9
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    # handle (tsuka) with diamond wrap
    d.rectangle([1, 3, 14, 5], fill=(46, 34, 52))
    for x in range(2, 14, 3):
        d.point([(x, 3), (x + 1, 4), (x, 5)], fill=(214, 204, 176))
    d.rectangle([0, 3, 1, 5], fill=(170, 140, 70))        # kashira
    # tsuba (guard)
    d.rectangle([15, 0, 17, 8], fill=(60, 52, 60))
    d.point([(16, 1), (16, 7)], fill=(210, 170, 70))
    d.rectangle([18, 3, 19, 5], fill=(236, 190, 80))       # habaki
    # blade with a gentle curve (sori): rises 1px toward the tip
    for x in range(20, 60):
        k = (x - 20) / 40.0
        yo = -int(round(math.sin(k * math.pi * 0.5) * 1.2))
        d.point((x, 3 + yo), fill=(150, 162, 186))          # mune (back)
        d.point((x, 4 + yo), fill=(214, 224, 240))
        d.point((x, 5 + yo), fill=(255, 255, 255))           # edge
    d.point([(60, 3), (60, 4)], fill=(226, 234, 246))        # kissaki
    d.point((61, 3), fill=(255, 255, 255))
    return outline(im, INK)


def katana_sprite(angle):
    """Katana rotated `angle` degrees CCW (0 = pointing right). Quantised to 5deg."""
    a = int(round(angle / 5.0)) * 5
    return cached(("katana", a), lambda: rotate_nearest(cached("katana0", _katana), a))


def _sword_field():
    """Mid-ground graveyard of swords/spears/banners stuck in the mud (RGBA, 1x)."""
    im = Image.new("RGBA", (W + 80, 70))
    d = ImageDraw.Draw(im)
    r = rng("swordfield")
    for i in range(46):
        x = r.uniform(0, W + 80)
        depth = r.random()
        gy = 20 + depth * 40
        L = 6 + depth * 14
        a = math.radians(r.uniform(-30, 30))
        c = mix((44, 46, 62), (70, 72, 92), depth)
        tip = (x + math.sin(a) * L, gy - math.cos(a) * L)
        d.line([(x, gy), tip], fill=c, width=1)
        if r.random() < 0.6:     # guard
            gx, gy2 = x + math.sin(a) * L * 0.25, gy - math.cos(a) * L * 0.25
            d.line([(gx - 2, gy2), (gx + 2, gy2)], fill=shade(c, 0.8))
        if r.random() < 0.15:    # tattered banner
            px = x
            d.line([(px, gy), (px, gy - L * 1.8)], fill=shade(c, 0.85))
            d.polygon([(px + 1, gy - L * 1.8), (px + 6, gy - L * 1.8), (px + 5, gy - L * 1.2), (px + 1, gy - L * 1.1)],
                      fill=shade(c, 0.9))
    return im


def sword_field(img, y, pan=0):
    im = cached("swordfield", _sword_field)
    ox = int(pan) % 80
    c = im.crop((ox, 0, ox + W, im.height))
    img.paste(c, (0, int(y)), c)


def _notice_board():
    """Kosatsu (official notice board) with 「废刀令」. Post bottoms on the bottom
    row; 150 x 106 px."""
    w, h = 150, 106
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    wood, wood_d, wood_l = (116, 80, 56), (78, 52, 40), (150, 108, 76)
    # posts
    for px in (18, w - 22):
        d.rectangle([px, 18, px + 3, h - 1], fill=wood)
        d.line([(px, 18), (px, h - 1)], fill=wood_l)
        d.line([(px + 3, 18), (px + 3, h - 1)], fill=wood_d)
    # little gabled roof
    d.polygon([(1, 16), (w // 2, 3), (w - 2, 16), (w - 2, 20), (1, 20)], fill=(64, 66, 84))
    for yy in range(6, 20, 3):
        half = (yy - 3) * 5.5
        d.line([(max(1, w // 2 - half), yy), (min(w - 2, w // 2 + half), yy)], fill=(84, 88, 108))
    d.line([(1, 20), (w - 2, 20)], fill=(40, 40, 54))
    d.line([(w // 2 - 3, 3), (w // 2 + 3, 3)], fill=(100, 104, 126))
    # board panel
    bx0, by0, bx1, by1 = 7, 23, w - 8, 82
    d.rectangle([bx0, by0, bx1, by1], fill=(222, 210, 178))
    d.rectangle([bx0, by0, bx1, by1], outline=wood_d)
    d.line([(bx0 + 1, by0 + 1), (bx1 - 1, by0 + 1)], fill=(240, 232, 206))
    for yy in (by0 + 20, by0 + 40):            # plank seams
        d.line([(bx0 + 1, yy), (bx1 - 1, yy)], fill=(206, 192, 160))
    # rain stains
    r = rng("stains")
    for _ in range(40):
        x, y = r.randint(bx0 + 2, bx1 - 2), r.randint(by0 + 2, by1 - 2)
        d.line([(x, y), (x, y + r.randint(2, 6))], fill=(204, 190, 158))
    cx = (bx0 + bx1) // 2
    f = font(24, "kai")
    for ox in (0, 1):                          # bold title
        d.text((cx + ox, by0 + 15), "废刀令", font=f, fill=(20, 14, 22), anchor="mm")
    f2 = font(12, "pixel")
    d.text((cx, by0 + 34), "凡武士者 禁止佩刀", font=f2, fill=(60, 44, 44), anchor="mm")
    d.text((bx0 + 40, by1 - 10), "幕府", font=f2, fill=(60, 44, 44), anchor="mm")
    d.rectangle([bx0 + 54, by1 - 16, bx0 + 64, by1 - 6], fill=(196, 40, 44))    # red seal
    d.rectangle([bx0 + 56, by1 - 14, bx0 + 62, by1 - 8], outline=(240, 180, 170))
    d.text((bx1 - 24, by1 - 10), "违者严惩", font=font(12, "pixel"), fill=(150, 40, 44), anchor="mm")
    # crossbar under the board
    d.rectangle([4, 86, w - 5, 89], fill=wood)
    d.line([(4, 86), (w - 5, 86)], fill=wood_l)
    # stone base blocks
    for px in (14, w - 26):
        d.rectangle([px, h - 6, px + 11, h - 1], fill=(120, 118, 124))
        d.line([(px, h - 6), (px + 11, h - 6)], fill=(150, 148, 154))
    return outline(im, INK)


def notice_board():
    return cached("notice", _notice_board)


def _sword_pile():
    """Confiscated swords stacked neatly in a heap (RGBA, bottom = ground)."""
    im = Image.new("RGBA", (70, 20))
    k0 = _katana()
    for i in range(6):
        a = (-4, 3, -2, 5, -3, 2)[i]
        s = rotate_nearest(k0.resize((46, 11), Image.NEAREST), a)
        flip = i % 2 == 1
        if flip:
            s = s.transpose(Image.FLIP_LEFT_RIGHT)
        x = (4, 14, 8, 18, 10, 6)[i]
        y = 20 - s.height - i * 2 + 2
        im.paste(s, (x, y), s)
    return im


def sword_pile():
    return cached("pile", _sword_pile)


def backlit(spr, dark=(30, 16, 36), amount=0.74, rim=(255, 170, 96), rim_top=None, sides=(1, -1)):
    """Back-lit character: colours pushed toward `dark` (details still faintly
    readable) + a 1px rim light on the top and the given side edges."""
    a = np.asarray(spr).astype(np.float32)
    al = a[..., 3] > 0
    out = a.copy()
    out[..., :3] = a[..., :3] * (1 - amount) + np.array(dark, np.float32) * amount
    rt = np.array(rim_top or rim, np.float32)
    up = np.zeros_like(al)
    up[1:] = al[:-1]
    top_edge = al & ~up
    out[top_edge, :3] = rt
    for s_ in sides:
        nb = np.zeros_like(al)
        if s_ > 0:
            nb[:, :-1] = al[:, 1:]
        else:
            nb[:, 1:] = al[:, :-1]
        e = al & ~nb
        out[e, :3] = np.array(rim, np.float32)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGBA")


def splashes(img, t, y0, y1, n=26, color=(170, 184, 220), seed=0):
    """Tiny rain splash crowns on the ground band y0..y1."""
    d = ImageDraw.Draw(img)
    for i in range(n):
        r = rng("splash", seed, i)
        per = r.uniform(0.35, 0.7)
        ph = r.random()
        k = ((t / per) + ph) % 1.0
        cyc = int((t / per) + ph)
        rr = rng("splash2", seed, i, cyc)
        x = rr.uniform(0, W)
        y = rr.uniform(y0, y1)
        if k < 0.25:
            d.point([(x - 1, y - 1), (x + 1, y - 1)], fill=color)
        elif k < 0.45:
            d.point([(x - 2, y - 1), (x + 2, y - 1), (x, y)], fill=shade(color, 0.8))


# ====================================================================== title
def _logo():
    """「银魂」 brush logo: bold silver fill, INK outline, deep red 3D extrusion."""
    f = font(84, "brush")
    b = f.getbbox("银魂")
    pad = 10
    w, h = b[2] - b[0] + pad * 2 + 6, b[3] - b[1] + pad * 2 + 6
    m = Image.new("L", (w, h), 0)
    dm = ImageDraw.Draw(m)
    dm.fontmode = "1"
    dm.text((pad - b[0], pad - b[1]), "银魂", font=f, fill=255)
    a = np.asarray(m) > 0

    def dil(mask, r):
        out = mask.copy()
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r + r:
                    out |= np.roll(np.roll(mask, dy, 0), dx, 1)
        return out
    fill = dil(a, 1)
    ol = dil(fill, 2)
    arr = np.zeros((h, w, 4), np.uint8)
    # extrusion (down-right), dark red -> ink
    for k in range(5, 0, -1):
        sh = np.roll(np.roll(ol, k, 0), k, 1)
        col = (120, 24, 40) if k < 5 else INK
        arr[sh] = col + (255,)
    arr[ol] = INK + (255,)
    # silver banded fill, light from the top-left
    yy = np.arange(h, dtype=np.float32)[:, None] + np.zeros((1, w), np.float32)
    ys = np.where(fill.any(1))[0]
    t = (yy - ys.min()) / max(1, ys.max() - ys.min())
    lv = np.floor(np.clip(t, 0, 1) * 5 + bayer(h, w) * 0.999)
    cols = np.array([(255, 255, 255), (240, 244, 252), (212, 222, 240), (178, 192, 220), (140, 156, 196),
                     (116, 130, 176)], np.uint8)
    fc = cols[np.clip(lv.astype(int), 0, 5)]
    arr[fill, :3] = fc[fill]
    arr[fill, 3] = 255
    # inner highlight: pixels whose upper-left neighbour is outside the fill
    ul = np.roll(np.roll(fill, 1, 0), 1, 1)
    hl = fill & ~ul
    arr[hl, :3] = (255, 255, 255)
    return Image.fromarray(arr, "RGBA")


def logo():
    return cached("logo", _logo)


def _ribbon():
    """Dark ribbon plate with 「GINTAMA · 像素剧场」."""
    from engine.text import text_width
    txt_a, txt_b = "G I N T A M A", "像素剧场"
    wa = text_width(txt_a, 12)
    wb = text_width(txt_b, 12)
    w = wa + wb + 36
    h = 16
    im = Image.new("RGBA", (w + 8, h))
    d = ImageDraw.Draw(im)
    d.polygon([(4, 0), (w + 7, 0), (w + 3, h - 1), (0, h - 1)], fill=INK)
    d.polygon([(5, 1), (w + 5, 1), (w + 2, h - 2), (2, h - 2)], fill=(150, 30, 44))
    d.line([(6, 2), (w + 4, 2)], fill=(214, 74, 80))
    d.fontmode = "1"
    f = font(12, "pixel")
    x = 14
    d.text((x + 1, 3), txt_a, font=f, fill=INK)
    d.text((x, 2), txt_a, font=f, fill=(255, 236, 170))
    x += wa + 6
    d.rectangle([x, 7, x + 1, 8], fill=(255, 236, 170))
    x += 8
    d.text((x + 1, 3), txt_b, font=f, fill=INK)
    d.text((x, 2), txt_b, font=f, fill=(255, 255, 255))
    return im


def ribbon():
    return cached("ribbon", _ribbon)


def rays(img, t, cx, cy, n=14, color=(255, 246, 214), alpha=0.18, spin=0.12):
    """Rotating sunburst wedges behind the logo (dithered translucency)."""
    if alpha <= 0:
        return
    m = Image.new("L", (W, H), 0)
    dm = ImageDraw.Draw(m)
    R = 420
    a0 = t * spin * 2 * math.pi
    for i in range(n):
        a = a0 + i * 2 * math.pi / n
        b = a + math.pi / n * 0.8
        dm.polygon([(cx, cy), (cx + math.cos(a) * R, cy + math.sin(a) * R),
                    (cx + math.cos(b) * R, cy + math.sin(b) * R)], fill=255)
    arr = np.asarray(m).astype(np.float32) / 255.0
    q = ((arr * alpha) > bayer(H, W) * 0.999).astype(np.uint8) * 255
    img.paste(tuple(color), (0, 0, W, H), Image.fromarray(q, "L"))


def _vig():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    k = np.clip((d - 0.55) / 0.75, 0, 1) * 0.6
    k = np.floor(k * 5 + bayer(H, W) * 0.999) / 5
    return (1 - k)[..., None].astype(np.float32)


def vignette(img, strength=1.0):
    k = cached("vig", _vig)
    a = np.asarray(img).astype(np.float32)
    if strength != 1.0:
        kk = 1 - (1 - k) * strength
    else:
        kk = k
    img.paste(Image.fromarray((a * kk).astype(np.uint8), "RGB"))


def _zclamp(k, cx, cy):
    hw, hh = W / (2 * k), H / (2 * k)
    return min(max(cx, hw), W - hw), min(max(cy, hh), H - hh)


def zoom(img, k, cx, cy):
    """fx.zoom with the centre clamped so the source box stays inside the canvas
    (engine fx.zoom raises when the box crosses an edge)."""
    if k <= 1.001:
        return
    from engine import fx
    cx, cy = _zclamp(k, cx, cy)
    fx.zoom(img, k, cx, cy)


def zoom_map(k, cx, cy, x, y):
    """Screen position of world point (x, y) after zoom(img, k, cx, cy)."""
    if k <= 1.001:
        return x, y
    cx, cy = _zclamp(k, cx, cy)
    return W / 2 + (x - cx) * k, H / 2 + (y - cy) * k
