"""Private props / effects for s13 银之魂篇 (owned by the s13 scene agent).

Everything is a pure function of its arguments; static art is cached at
module level.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import W, H, rng, clamp, seg, lerp, ease_out, ease_in, ease_out_back, wave, step_frame
from engine.gfx import INK, paste, rect, overlay_rect, shade, mix, scale_nearest, set_alpha, tint
from engine.text import text_sprite, draw_text, text_width
from engine import fx
from bg import common as C, edo as E
from chars import render_sprite, get_def

_CACHE = {}


def cached(key, fn):
    v = _CACHE.get(key)
    if v is None:
        v = fn()
        _CACHE[key] = v
    return v


# ====================================================================== backgrounds
def edo_bg(img, t, cam, tod="night", armada=1.0, near=False, dy=0, ships=True):
    E.skyline(img, cam, t, tod, ships=ships, armada=armada, near=near, dy=dy)


def edo_blend(img, t, cam, k, armada=1.0, roof_y=None):
    """Night -> dawn blended Edo (k 0..1). Optional walkable roof ridge at roof_y."""
    k = round(clamp(k) * 12) / 12        # quantised: fewer distinct blends, retro stepping
    if k <= 0:
        edo_bg(img, t, cam, "night", armada)
        if roof_y is not None:
            E.roof_walk(img, cam, roof_y, t, "night")
        return
    if k >= 1:
        edo_bg(img, t, cam, "dawn", armada)
        if roof_y is not None:
            E.roof_walk(img, cam, roof_y, t, "dawn")
        return
    a = Image.new("RGB", (W, H))
    edo_bg(a, t, cam, "night", armada)
    b = Image.new("RGB", (W, H))
    edo_bg(b, t, cam, "dawn", armada)
    if roof_y is not None:
        E.roof_walk(a, cam, roof_y, t, "night")
        E.roof_walk(b, cam, roof_y, t, "dawn")
    img.paste(Image.blend(a, b, k))


def fire_glow(img, t, y0=96, y1=150, amount=1.0):
    """Burning-city glow on the horizon (dithered bands of red/orange)."""
    if amount <= 0:
        return
    key = ("fireglow", y0, y1)

    def build():
        h = y1 - y0
        arr = np.zeros((h, W, 4), np.uint8)
        yy = np.arange(h, dtype=np.float32)[:, None] / h
        a = np.clip(yy, 0, 1) ** 1.4 * 0.55
        q = np.floor(a * 6 + C.bayer(h, W)) / 6
        arr[..., 0], arr[..., 1], arr[..., 2] = 255, 96, 60
        arr[..., 3] = (np.clip(q, 0, 1) * 255).astype(np.uint8)
        return Image.fromarray(arr, "RGBA")
    lay = cached(key, build)
    fl = 0.8 + 0.2 * math.sin(t * 7.0) * math.sin(t * 3.1)
    if amount * fl < 0.99:
        lay = set_alpha(lay, amount * fl)
    img.paste(lay, (0, y0), lay)


def searchlights(img, t, base_y=150, n=3, alpha=34):
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    for i in range(n):
        bx = 50 + i * 140
        a = math.radians(-90 + 28 * math.sin(t * 0.7 + i * 2.1))
        L = 260
        w = 0.07
        p1 = (bx + math.cos(a - w) * L, base_y + math.sin(a - w) * L)
        p2 = (bx + math.cos(a + w) * L, base_y + math.sin(a + w) * L)
        d.polygon([(bx - 1, base_y), p1, p2, (bx + 1, base_y)], fill=alpha)
    img.paste((210, 225, 255), (0, 0), mask)


def light_rays(img, cx, cy, t, color=(255, 236, 190), alpha=40, n=12, length=460, width=0.07, spin=0.04):
    if alpha <= 0:
        return
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    for i in range(n):
        a = i / n * 2 * math.pi + t * spin + (0.2 if i % 2 else 0)
        w = width * (1.3 if i % 3 == 0 else 0.8)
        p1 = (cx + math.cos(a - w) * length, cy + math.sin(a - w) * length)
        p2 = (cx + math.cos(a + w) * length, cy + math.sin(a + w) * length)
        d.polygon([(cx, cy), p1, p2], fill=int(alpha))
    img.paste(tuple(color), (0, 0), mask)


def sun(img, cx, cy, r=15, t=0.0):
    C.add_sprite(img, C.glow_sprite(r * 3, (255, 170, 110), 1.0), cx - r * 3, cy - r * 3)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1], fill=(255, 196, 130))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 238, 190))
    d.ellipse([cx - r + 3, cy - r + 3, cx + r - 5, cy + r - 5], fill=(255, 252, 232))


def motes(img, t, count=30, seed=0, area=(0, 0, W, H), rise=14.0, colors=((255, 244, 200), (255, 214, 150))):
    x0, y0, x1, y1 = area
    d = ImageDraw.Draw(img)
    for i in range(count):
        r = rng("s13mote", seed, i)
        hh = y1 - y0
        y = y1 - (r.uniform(0, hh) + t * rise * r.uniform(0.6, 1.4)) % hh
        x = x0 + (r.uniform(0, x1 - x0) + wave(t, 0.3, 6, r.random())) % (x1 - x0)
        c = colors[i % len(colors)]
        if (int(t * 8) + i) % 6:
            d.point((x, y), fill=c)
            if i % 5 == 0:
                d.point((x + 1, y), fill=shade(c, 0.7))


# ====================================================================== ships / props
def ship_silhouette(kind, scale, color):
    """Ship shape as a flat-coloured RGBA silhouette (for the chapter card)."""
    def build():
        w, h = E.ship_size(kind, scale)
        tw, th = w + 12, h + 12
        tmp = Image.new("RGB", (tw, th), (0, 0, 0))
        E.ship(tmp, tw / 2, th / 2, kind, 0.0, scale=scale, tod="night", lights=False)
        m = np.asarray(tmp).max(axis=2) > 0
        arr = np.zeros((th, tw, 4), np.uint8)
        arr[m] = tuple(color) + (255,)
        return Image.fromarray(arr, "RGBA")
    return cached(("shipsil", kind, scale, tuple(color)), build)


def _kaien_ship():
    """Kaientai trading ship: wooden hull, cabin, red 快援队 banner."""
    w, h = 104, 58
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    wood, wood_l, wood_d = (150, 96, 60), (190, 130, 84), (100, 60, 40)
    # cabin
    d.rectangle([40, 22, 72, 38], fill=INK)
    d.rectangle([41, 23, 71, 37], fill=(236, 224, 196))
    for wx in (45, 55, 65):
        d.rectangle([wx, 27, wx + 5, 32], fill=(90, 130, 170))
        d.rectangle([wx, 27, wx + 5, 27], fill=(170, 210, 240))
    d.polygon([(36, 23), (46, 15), (68, 15), (76, 23)], fill=(70, 66, 96), outline=INK)
    d.line([(46, 16), (67, 16)], fill=(110, 106, 140))
    # hull
    hull = [(2, 36), (96, 36), (103, 28), (98, 44), (86, 54), (14, 54), (6, 46)]
    d.polygon(hull, fill=wood, outline=INK)
    d.line([(4, 37), (97, 37)], fill=wood_l)
    for y in (42, 48):
        d.line([(8, y), (94, y)], fill=wood_d)
    d.line([(4, 36), (99, 36)], fill=INK)
    # rail
    for x in range(8, 96, 7):
        d.line([(x, 31), (x, 36)], fill=INK)
    d.line([(4, 31), (100, 31)], fill=INK)
    d.line([(4, 30), (100, 30)], fill=wood_l)
    # engine pod
    d.rectangle([0, 44, 12, 52], fill=INK)
    d.rectangle([1, 45, 11, 51], fill=(120, 124, 150))
    # gold trim / emblem
    d.ellipse([60, 42, 70, 52], fill=INK)
    d.ellipse([61, 43, 69, 51], fill=(240, 196, 70))
    d.point((65, 47), fill=INK)
    # banner pole + banner (stern), drawn over the cabin roof
    tx = text_sprite("快援队", (255, 255, 255), 12, "pixel")
    bw = tx.width + 6
    d.line([(16, 2), (16, 36)], fill=INK, width=3)
    d.line([(16, 3), (16, 35)], fill=(120, 90, 60), width=1)
    d.rectangle([17, 2, 18 + bw, 19], fill=INK)
    d.rectangle([18, 3, 17 + bw, 18], fill=(206, 44, 52))
    d.rectangle([18, 3, 17 + bw, 4], fill=(240, 90, 96))
    im.alpha_composite(tx, (21, 4))
    return im


def kaien_ship(img, x, y, t):
    """Draw the Kaientai ship centred at (x, y) with engine flame; returns
    the bow-deck feet point (for Sakamoto)."""
    spr = cached("kaien", _kaien_ship)
    x0, y0 = int(x - spr.width / 2), int(y - spr.height / 2)
    # engine flame (stern, left side)
    fl = 4 + step_frame(t, 20, 3) * 2
    rect(img, x0 - fl, y0 + 46, fl, 5, (255, 150, 60))
    rect(img, x0 - fl // 2, y0 + 47, fl // 2, 3, (255, 236, 150))
    paste(img, spr, x0, y0)
    return x0 + 86, y0 + 31


def crow(img, x, y, t, seed=0, facing=1, s=1, rim=None):
    """Small flapping crow (black, 7x4 pixels, each pixel s x s). rim: optional
    light outline colour so it reads against a dark sky."""
    f = step_frame(t + seed * 0.07, 10, 2)
    rows = (["o.....o", ".o...o.", "..ooo..", "...o..."] if f == 0 else
            [".......", "..ooo..", ".oooooo", "o.....o"])
    col = (18, 14, 26)
    x, y = int(x), int(y)
    d = ImageDraw.Draw(img)
    pts = []
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == "o":
                pts.append((x + (i if facing > 0 else 6 - i) * s, y + j * s))
    if rim is not None:
        for px, py in pts:
            d.rectangle([px - 1, py - 1, px + s, py + s], fill=rim)
    for px, py in pts:
        d.rectangle([px, py, px + s - 1, py + s - 1], fill=col)
    ex, ey = x + (5 if facing > 0 else 1) * s, y + 2 * s
    d.rectangle([ex, ey, ex + s - 1, ey + s - 1], fill=(220, 40, 50))


def makoto_flag(img, x, y, t):
    """Shinsengumi 誠 banner on a pole; pole foot at (x, y)."""
    def build():
        w, h = 22, 30
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, w - 1, h - 1], fill=INK)
        d.rectangle([1, 1, w - 2, h - 2], fill=(232, 236, 248))
        # dandara (mountain) stripes at the bottom
        for i in range(0, w, 6):
            d.polygon([(i, h - 2), (i + 3, h - 7), (i + 6, h - 2)], fill=(52, 84, 170))
        g = text_sprite("诚", (190, 30, 44), 16, "pixel")
        im.alpha_composite(g, ((w - g.width) // 2, 2))
        return im
    cloth = cached("makoto", build)
    top = y - 58
    rect(img, x - 1, top, 3, 58, INK)
    rect(img, x, top + 1, 1, 57, (170, 130, 80))
    rect(img, x - 2, top - 2, 5, 3, (240, 196, 70))
    for i in range(cloth.width):
        dy = int(round(1.6 * math.sin(t * 7 - i * 0.35) * (i / cloth.width)))
        col = cloth.crop((i, 0, i + 1, cloth.height))
        img.paste(col, (x + 2 + i, top + 3 + dy), col)


# ====================================================================== text
def group_label(img, u, big, small, col, x=10, y=10):
    """Montage group caption: coloured slanted band + brush title slams in."""
    if u < 0:
        return
    k = ease_out(clamp(u / 0.12))
    bigspr = cached(("lbl", big), lambda: text_sprite(big, (255, 255, 255), 30, "brush", outline=INK, thick=2))
    tw = max(bigspr.width, text_width(small) + 10) + 18
    off = int((1 - k) * -(tw + 30))
    d = ImageDraw.Draw(img)
    x0, y0 = x + off, y
    bh = 50
    d.polygon([(x0 - 20, y0), (x0 + tw + 8, y0), (x0 + tw - 6, y0 + bh), (x0 - 20, y0 + bh)], fill=INK)
    d.polygon([(x0 - 20, y0 + 2), (x0 + tw + 5, y0 + 2), (x0 + tw - 8, y0 + bh - 2), (x0 - 20, y0 + bh - 2)], fill=tuple(col))
    d.polygon([(x0 - 20, y0 + bh - 14), (x0 + tw - 3, y0 + bh - 14), (x0 + tw - 8, y0 + bh - 2), (x0 - 20, y0 + bh - 2)], fill=INK)
    s = 1.0
    if u < 0.1:
        s = 1 + (1 - u / 0.1) * 0.9
    spr = bigspr if s == 1.0 else bigspr.resize((int(bigspr.width * s), int(bigspr.height * s)), Image.NEAREST)
    paste(img, spr, x0 + 4 + bigspr.width // 2, y0 + 19, anchor="center")
    if u > 0.08:
        from engine.text import typed
        draw_text(img, x0 + 6, y0 + bh - 13, typed(small, u, 0.08, 40), (255, 236, 150), size=12)


def slam_text(img, t, t0, text, cx, cy, size=40, color=(255, 255, 255), outline_col=(170, 20, 40), face="brush"):
    """Huge title that slams down from 2.5x with a shockwave ring."""
    if t < t0:
        return
    u = t - t0
    spr = cached(("slam", text, size, color, outline_col, face),
                 lambda: _double_outline(text_sprite(text, color, size, face, outline=outline_col, thick=2)))
    if u < 0.12:
        s = 2.4 - 1.4 * ease_in(u / 0.12)
        spr2 = spr.resize((int(spr.width * s), int(spr.height * s)), Image.NEAREST)
        paste(img, spr2, cx, cy, anchor="center", alpha=clamp(u / 0.06))
    else:
        jx = int(wave(t, 14, 1)) if u < 0.5 else 0
        paste(img, spr, cx + jx, cy, anchor="center")
    if 0.1 < u < 0.5:
        r = (u - 0.1) * 420
        d = ImageDraw.Draw(img)
        d.ellipse([cx - r, cy - r * 0.45, cx + r, cy + r * 0.45], outline=(255, 240, 200), width=2)


def _double_outline(spr):
    """Extra INK outline around an already outlined text sprite."""
    a = np.asarray(spr)
    h, w = a.shape[:2]
    out = np.zeros((h + 2, w + 2, 4), np.uint8)
    m = a[..., 3] > 0
    mm = np.zeros((h + 2, w + 2), bool)
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            mm[dy:dy + h, dx:dx + w] |= m
    out[mm] = (INK[0], INK[1], INK[2], 255)
    out[1:1 + h, 1:1 + w][m] = a[m]
    return Image.fromarray(out, "RGBA")


# ====================================================================== busts / faces
def bust(img, cid, t, expr, cx, top, k=4, facing=1, pose="idle", alpha=1.0, fade_bottom=None, tint_col=None,
         tint_amt=0.0, crop=1.0, **kw):
    """Head-and-shoulders close-up: sprite cropped to its top `crop` fraction,
    scaled k, top at `top`, bbox centre at cx. Returns (x0, y0, k, bbox)."""
    spr, ax, ay = render_sprite(cid, pose, t, None, expr, facing, **kw)
    bb = spr.getbbox()
    if bb is None:
        return None
    if crop < 1.0:
        bb = (bb[0], bb[1], bb[2], bb[1] + max(1, int((bb[3] - bb[1]) * crop)))
    spr = spr.crop(bb)
    if tint_col is not None and tint_amt > 0:
        spr = tint(spr, tint_col, tint_amt)
    spr = scale_nearest(spr, k)
    if fade_bottom is not None:
        spr = _fade_bottom(spr, fade_bottom)
    x0 = int(cx - spr.width / 2)
    paste(img, spr, x0, int(top), alpha=alpha)
    return x0, int(top), k, bb


def _fade_bottom(spr, start_frac):
    a = np.asarray(spr).copy()
    h, w = a.shape[:2]
    y0 = int(h * start_frac)
    if y0 >= h:
        return spr
    yy = np.arange(h, dtype=np.float32)
    f = np.clip(1 - (yy - y0) / max(1, h - y0), 0, 1)[:, None]
    q = np.floor(f * 4 + C.bayer(h, w)) / 4
    a[..., 3] = (a[..., 3].astype(np.float32) * np.clip(q, 0, 1)).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def head_big(img, cid, expr, cx, cy, k, alpha=1.0, tint_col=None, tint_amt=0.0):
    d = get_def(cid)
    h = d.head(expr)
    if tint_col is not None and tint_amt > 0:
        h = tint(h, tint_col, tint_amt)
    h = scale_nearest(h, k)
    paste(img, h, cx, cy, anchor="center", alpha=alpha)
    return h.size


# ====================================================================== shatter
def _shatter_data(key, spr):
    def build():
        a = np.asarray(spr)
        ys, xs = np.nonzero(a[..., 3] > 0)
        cols = a[ys, xs, :3].astype(np.float32)
        n = len(xs)
        seed = rng("s13shatter", key).randrange(1 << 30)
        g = np.random.default_rng(seed)
        h = max(1, spr.height)
        delay = (1 - ys / h) * 0.18 + g.uniform(0, 0.35, n)          # the head crumbles last
        vx = g.uniform(-16, 16, n)
        vy = g.uniform(-34, -10, n)
        life = g.uniform(0.9, 1.8, n)
        size = (g.uniform(0, 1, n) < 0.35).astype(np.int32) + 1
        ph = g.uniform(0, 6.28, n)
        return xs.astype(np.float32), ys.astype(np.float32), cols, delay, vx, vy, life, size, ph
    return cached(("shat", key), build)


def shatter(img, spr, key, x0, y0, t, t0, pull=None, light=(255, 244, 210)):
    """Sprite dissolves into rising motes of light from t0. (x0, y0) = the
    sprite's top-left on the canvas. pull=(px, py): gentle attraction point."""
    xs, ys, cols, delay, vx, vy, life, size, ph = _shatter_data(key, spr)
    dt = t - t0 - delay
    arr = np.asarray(img).copy()
    stay = dt < 0
    # un-dissolved pixels (glowing brighter as the moment nears)
    if stay.any():
        glow = clamp((t - t0 + 0.4) / 0.4)
        c = cols[stay] * (1 - glow * 0.6) + np.array(light, np.float32) * glow * 0.6
        px = (x0 + xs[stay]).astype(np.int32)
        py = (y0 + ys[stay]).astype(np.int32)
        ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
        arr[py[ok], px[ok]] = c[ok].astype(np.uint8)
    mv = ~stay
    if mv.any():
        d = np.maximum(dt[mv], 0)
        k = np.clip(d / life[mv], 0, 1)
        px = x0 + xs[mv] + vx[mv] * d + np.sin(d * 3 + ph[mv]) * 3
        py = y0 + ys[mv] + vy[mv] * d - 10 * d * d
        if pull is not None:
            pk = np.clip(d / 1.6, 0, 1) ** 2 * 0.6
            px = px + (pull[0] - px) * pk
            py = py + (pull[1] - py) * pk
        cc = np.clip(d * 5, 0, 1)[:, None]
        col = cols[mv] * (1 - cc) + np.array(light, np.float32) * cc
        a = (1 - k)[:, None]
        alive = k < 1
        px, py, col, a, sz = px[alive], py[alive], col[alive], a[alive], size[mv][alive]
        for s in (1, 2):
            sel = sz == s
            if not sel.any():
                continue
            for oy in range(s):
                for ox in range(s):
                    qx = (px[sel] + ox).astype(np.int32)
                    qy = (py[sel] + oy).astype(np.int32)
                    ok = (qx >= 0) & (qx < W) & (qy >= 0) & (qy < H)
                    base = arr[qy[ok], qx[ok]].astype(np.float32)
                    aa = a[sel][ok]
                    arr[qy[ok], qx[ok]] = (base * (1 - aa) + col[sel][ok] * aa).astype(np.uint8)
    img.paste(Image.fromarray(arr, "RGB"))


def cracks(img, x0, y0, w, h, p, seed=0, color=(255, 246, 214), n=5, step=2.2, halo=None, clip=None):
    """Jagged light cracks spreading over a (w x h) box. p 0..1 growth.
    halo: optional darker/warm colour drawn 1 px around the crack (reads as glow).
    clip: optional RGBA sprite + (sx, sy) offset — cracks are only drawn where the sprite is opaque."""
    if p <= 0:
        return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    r = rng("s13crack", seed)
    paths = []
    for i in range(n):
        cx, cy = x0 + w * r.uniform(0.3, 0.7), y0 + h * r.uniform(0.2, 0.8)
        ang = r.uniform(0, 6.28)
        jit = [r.uniform(-0.9, 0.9) for _ in range(24)]
        if p < i / n * 0.7:
            continue
        L = int(3 + 9 * clamp((p - i / n * 0.7) / 0.5))
        pts = [(cx, cy)]
        x, y = cx, cy
        for j in range(L):
            ang += jit[j]
            x += math.cos(ang) * step
            y += math.sin(ang) * step
            pts.append((x, y))
        paths.append(pts)
        pts2 = [(cx, cy)]
        x, y, ang2 = cx, cy, ang + math.pi
        for j in range(L // 2 + 1):
            ang2 += jit[23 - j]
            x += math.cos(ang2) * step
            y += math.sin(ang2) * step
            pts2.append((x, y))
        paths.append(pts2)
    if halo is not None:
        for pts in paths:
            d.line(pts, fill=tuple(halo) + (255,), width=3)
    for pts in paths:
        d.line(pts, fill=tuple(color) + (255,), width=1)
    if clip is not None:
        spr, sx, sy = clip
        m = Image.new("L", (W, H), 0)
        m.paste(spr.getchannel("A"), (int(sx), int(sy)))
        a = ImageChopsMul(lay.getchannel("A"), m)
        lay.putalpha(a)
    img.paste(lay, (0, 0), lay)


def ImageChopsMul(a, b):
    from PIL import ImageChops
    return ImageChops.multiply(a, b)


def soft_speed_lines(img, t, cx, cy, color, alpha=0.4, count=40, inner=60, seed=0):
    tmp = Image.new("RGB", (W, H), (0, 0, 0))
    fx.speed_lines(tmp, t, cx, cy, color=(255, 255, 255), count=count, inner=inner, seed=seed)
    m = tmp.convert("L")
    if alpha < 1:
        lv = int(255 * alpha)
        m = m.point(lambda v: lv if v > 127 else 0)
    img.paste(tuple(color), (0, 0), m)


def ash(img, t, count=46, seed=0, color=(150, 146, 160), speed=14.0):
    d = ImageDraw.Draw(img)
    for i in range(count):
        r = rng("s13ash", seed, i)
        y = (r.uniform(0, H) + t * speed * r.uniform(0.6, 1.4)) % (H + 4) - 2
        x = (r.uniform(0, W) + t * 6 + wave(t, 0.3, 5, r.random())) % W
        x, y = int(x), int(y)
        c = color if i % 3 else shade(color, 0.75)
        if i % 5 == 0:
            d.rectangle([x, y, x + 1, y], fill=c)
        else:
            d.point((x, y), fill=c)


def zoom(img, k, cx=W / 2, cy=H / 2):
    """fx.zoom with the centre clamped so the source box stays on the canvas."""
    if abs(k - 1) < 1e-3:
        return
    hw, hh = W / (2 * k), H / (2 * k)
    cx = min(max(cx, hw), W - hw)
    cy = min(max(cy, hh), H - hh)
    fx.zoom(img, k, cx, cy)


def x_slash(img, cx, cy, t, t0, size=24, color=(255, 255, 255)):
    """Two crossing blade streaks (X) that shoot across (cx, cy) then thin out."""
    u = t - t0
    if u < 0 or u > 0.38:
        return
    d = ImageDraw.Draw(img)
    for j, (sx, sy) in enumerate(((-1, -1), (1, -1))):
        g = ease_out(clamp((u - j * 0.04) / 0.07))
        if g <= 0:
            continue
        w = max(1, int(round(5 * (1 - seg(u, 0.12, 0.38)))))
        p0 = (cx + sx * size, cy + sy * size * 0.8)
        p1 = (cx - sx * size, cy - sy * size * 0.8)
        pe = (p0[0] + (p1[0] - p0[0]) * g, p0[1] + (p1[1] - p0[1]) * g)
        d.line([p0, pe], fill=INK, width=w + 2)
        d.line([p0, pe], fill=tuple(color), width=w)


BLADE_COLS = ((214, 224, 238), (255, 255, 255))
BOKUTO_COLS = ((204, 150, 92), (235, 190, 125), (96, 58, 40))


UTSURO_EYES = ((255, 50, 62), (255, 190, 190), (170, 18, 40))
GIN_EYES = ((150, 36, 58),)


def sil_sprite(cid, pose, t, p, expr, facing, k, color, keep=(), keep_color=(255, 255, 255), glow=(),
               glow_color=(255, 40, 60), **kw):
    """Flat silhouette of a character (impact frames). Pixels whose colour is in
    `keep` (e.g. the blade) are painted keep_color so the weapon still reads;
    pixels in `glow` (e.g. eyes) are painted glow_color. Returns
    (sprite, ax, ay, blade) where blade = (x0, x1, y) of the kept pixels."""
    def build():
        spr, ax, ay = render_sprite(cid, pose, t, p, expr, facing, **kw)
        arr = np.asarray(spr).copy()
        m = arr[..., 3] > 0

        def match(cols):
            mm = np.zeros(m.shape, bool)
            for c in cols:
                mm |= m & np.all(np.abs(arr[..., :3].astype(np.int16) - np.array(c, np.int16)) < 3, axis=-1)
            return mm
        km, gm = match(keep), match(glow)
        arr[m, 0], arr[m, 1], arr[m, 2] = color[0], color[1], color[2]
        arr[km, 0], arr[km, 1], arr[km, 2] = keep_color[0], keep_color[1], keep_color[2]
        arr[gm, 0], arr[gm, 1], arr[gm, 2] = glow_color[0], glow_color[1], glow_color[2]
        arr[m, 3] = 255
        s = Image.fromarray(arr, "RGBA")
        ys, xs = np.nonzero(km)
        blade = None
        if len(xs):
            blade = (xs.min() * k, xs.max() * k + k - 1, int(np.median(ys)) * k + k // 2)
        return scale_nearest(s, k), ax * k, ay * k, blade
    key = ("sil", cid, pose, round(t, 3), p, expr, facing, k, tuple(color), tuple(keep), tuple(keep_color),
           tuple(glow), tuple(glow_color), tuple(sorted(kw.items())))
    spr, ax, ay, blade = cached(key, build)
    return spr, ax, ay, blade


def _butterfly_frame(f, wing=(156, 84, 210), wing_d=(104, 52, 150), spot=(250, 206, 80)):
    rows = {
        0: ["oo.....oo",      # wings open
            "owoo.oowo",
            "owwwowwwo",
            ".oswoswo.",
            ".owo.owo.",
            "..o...o.."],
        1: [".oo...oo.",      # half
            ".owo.owo.",
            ".owwowwo.",
            "..osoSo..",
            "...ooo...",
            "........."],
        2: ["...ooo...",      # closed (wings up)
            "...owo...",
            "...owo...",
            "...oso...",
            "....o....",
            "........."],
    }[f]
    pal = {"o": INK, "w": wing, "s": spot, "S": wing_d}
    im = Image.new("RGBA", (9, 6), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in pal:
                im.putpixel((x, y), tuple(pal[ch]) + (255,))
    return im


def butterfly(img, x, y, t, seed=0, s=2):
    """Purple butterfly with gold spots (Takasugi's kimono motif), centred at (x, y)."""
    f = (0, 1, 2, 1)[step_frame(t + seed * 0.13, 12, 4)]
    spr = cached(("bfly", f, s), lambda: scale_nearest(_butterfly_frame(f), s))
    paste(img, spr, int(x) - spr.width // 2, int(y) - spr.height // 2)


def sweat_drop(img, x, y, k=1.0):
    """Big anime sweat drop (tip up) at (x, y) = top point."""
    d = ImageDraw.Draw(img)
    x, y = int(x), int(y)
    d.polygon([(x, y), (x - 4, y + 7), (x - 4, y + 9), (x - 2, y + 11), (x + 2, y + 11), (x + 4, y + 9),
               (x + 4, y + 7)], fill=(150, 210, 255), outline=INK)
    d.rectangle([x - 2, y + 7, x - 1, y + 8], fill=(255, 255, 255))


def dojo_bg(img, t):
    """Sepia-ready Shoka Sonjuku classroom: shoji wall, pillars, tatami floor."""
    def build():
        im = Image.new("RGB", (W, H), (200, 170, 120))
        d = ImageDraw.Draw(im)
        wood, wood_d, paper, tat, tat_d = (120, 80, 50), (84, 54, 34), (236, 222, 190), (190, 176, 110), (150, 136, 80)
        # back wall: shoji panels between pillars
        d.rectangle([0, 0, W, 150], fill=paper)
        for x in range(0, W + 1, 12):
            d.line([(x, 20), (x, 150)], fill=(186, 160, 120))
        for y in range(20, 151, 16):
            d.line([(0, y), (W, y)], fill=(186, 160, 120))
        d.rectangle([0, 0, W, 19], fill=wood_d)
        d.rectangle([0, 16, W, 21], fill=wood)
        for x in (18, 116, 214, 312):
            d.rectangle([x, 0, x + 9, 150], fill=wood)
            d.rectangle([x, 0, x + 1, 150], fill=(150, 104, 66))
            d.rectangle([x + 8, 0, x + 9, 150], fill=wood_d)
        # calligraphy scroll
        sx, sy = 179, 78
        d.rectangle([sx - 2, sy - 3, sx + 22, sy - 1], fill=wood_d)
        d.rectangle([sx, sy, sx + 20, sy + 52], fill=INK)
        d.rectangle([sx + 1, sy + 1, sx + 19, sy + 51], fill=(242, 234, 212))
        for i, ch in enumerate("松下村塾"):
            g = text_sprite(ch, (40, 30, 30), 12, "pixel")
            im.paste(g, (sx + 10 - g.width // 2, sy + 2 + i * 12), g)
        # floor
        d.rectangle([0, 150, W, H], fill=tat)
        d.line([(0, 150), (W, 150)], fill=wood_d, width=2)
        for x in range(-40, W + 60, 64):
            d.line([(x, 152), (x - 30, H)], fill=tat_d)
        d.line([(0, 176), (W, 176)], fill=tat_d)
        return im
    img.paste(cached("dojo", build))


def bust_shadow(cid, expr, k, crop=0.62, r0=8, r1=12, hair=None, dark=(24, 18, 38), amt=0.8, facing=1,
                pose="idle", fade_bottom=None, **kw):
    """Head-and-shoulders bust whose eyes sink into shadow under the bangs.
    The head is the top element of the sprite, so rows r0..r1 of the head are
    rows bbox_top + r0 .. bbox_top + r1."""
    hair = hair or GIN_HAIR

    def build():
        spr, ax, ay = render_sprite(cid, pose, 0.0, None, expr, 1, **kw)
        bb = spr.getbbox()
        bb = (bb[0], bb[1], bb[2], bb[1] + max(1, int((bb[3] - bb[1]) * crop)))
        a = np.asarray(spr.crop(bb)).astype(np.float32).copy()
        rows = np.zeros(a.shape[:2], bool)
        rows[r0:r1 + 1] = True
        rgb = a[..., :3]
        is_hair = np.zeros(a.shape[:2], bool)
        for c in hair:
            is_hair |= np.all(np.abs(rgb - np.array(c, np.float32)) < 2, axis=-1)
        is_ink = np.all(np.abs(rgb - np.array(INK, np.float32)) < 2, axis=-1)
        m = rows & (a[..., 3] > 0) & ~is_hair & ~is_ink
        rgb[m] = rgb[m] * (1 - amt) + np.array(dark, np.float32) * amt
        a[..., :3] = rgb
        im = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
        if facing < 0:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        im = scale_nearest(im, k)
        if fade_bottom is not None:
            im = _fade_bottom(im, fade_bottom)
        return im
    return cached(("bshadow", cid, expr, k, crop, r0, r1, amt, facing, pose, fade_bottom,
                   tuple(sorted(kw.items()))), build)


GIN_HAIR = ((238, 240, 250), (196, 202, 224), (146, 152, 188))


def head_shadow(cid, expr, k, r0=8, r1=12, hair=GIN_HAIR, dark=(24, 18, 38), amt=0.8, facing=1):
    """Head sprite whose face (non-hair pixels) between rows r0..r1 sinks into
    shadow under the bangs — the classic 'eyes hidden' dramatic look."""
    def build():
        h = get_def(cid).head(expr)
        a = np.asarray(h).astype(np.float32).copy()
        rows = np.zeros(a.shape[:2], bool)
        rows[r0:r1 + 1] = True
        rgb = a[..., :3]
        is_hair = np.zeros(a.shape[:2], bool)
        for c in hair:
            is_hair |= np.all(np.abs(rgb - np.array(c, np.float32)) < 2, axis=-1)
        is_ink = np.all(np.abs(rgb - np.array(INK, np.float32)) < 2, axis=-1)
        m = rows & (a[..., 3] > 0) & ~is_hair & ~is_ink
        kk = np.full(a.shape[:2], amt, np.float32)
        rgb[m] = rgb[m] * (1 - kk[m][:, None]) + np.array(dark, np.float32) * kk[m][:, None]
        a[..., :3] = rgb
        im = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
        if facing < 0:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        return scale_nearest(im, k)
    return cached(("hshadow", cid, expr, k, r0, r1, amt, facing), build)


def bust_sprite(cid, t, expr, k=4, facing=1, pose="idle", crop=1.0, fade_bottom=None, tint_col=None,
                tint_amt=0.0, **kw):
    """Same framing as bust() but returns the finished RGBA sprite."""
    spr, ax, ay = render_sprite(cid, pose, t, None, expr, facing, **kw)
    bb = spr.getbbox()
    if crop < 1.0:
        bb = (bb[0], bb[1], bb[2], bb[1] + max(1, int((bb[3] - bb[1]) * crop)))
    spr = spr.crop(bb)
    if tint_col is not None and tint_amt > 0:
        spr = tint(spr, tint_col, tint_amt)
    spr = scale_nearest(spr, k)
    if fade_bottom is not None:
        spr = _fade_bottom(spr, fade_bottom)
    return spr
