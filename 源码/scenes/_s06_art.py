"""Private art helpers for s06 「日常」 (manga-panel vignettes).

Everything static is built once into module-level caches; per-frame helpers only
paste cached layers + draw a few animated pixels. All functions are pure
functions of their arguments (t = scene time).
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import W, H, clamp, lerp, seg, wave, step_frame, rng, ease_out
from engine.gfx import INK, PAL, rect, pset, shade, mix, ascii_sprite, gradient, dither_mask
from engine.text import text_sprite, draw_text, text_width

_CACHE = {}


def cached(key, fn):
    v = _CACHE.get(key)
    if v is None:
        v = fn()
        _CACHE[key] = v
    return v


INK4 = INK + (255,)
PAPER = (248, 244, 233)
PAPER_D = (226, 220, 206)

# ------------------------------------------------------------------ manga paper
def paper_layer():
    """Off-white manga paper with a faint dot screentone (full canvas RGB)."""
    def mk():
        a = np.empty((H, W, 3), np.uint8)
        a[:] = PAPER
        yy, xx = np.mgrid[0:H, 0:W]
        dots = ((xx % 4) == 0) & ((yy % 4) == 0) | ((xx % 4) == 2) & ((yy % 4) == 2)
        a[dots] = (238, 233, 220)
        return Image.fromarray(a, "RGB")
    return cached("paper", mk)


def tag(img, x, y, text, bg=INK, fg=(255, 255, 255)):
    """Small black chapter tab like「其一」in the panel corner."""
    w = text_width(text) + 8
    rect(img, x, y, w, 15, bg)
    rect(img, x + 1, y + 1, w - 2, 13, (60, 50, 70))
    rect(img, x + 2, y + 2, w - 4, 11, bg)
    draw_text(img, x + 4, y + 2, text, fg)


def caption_box(img, x, y, text, size=16, bg=(255, 255, 255), fg=INK, border=INK, pad=5, anchor="lt"):
    """Manga narration box (square, 2px ink frame)."""
    tw = text_width(text, size)
    w, h = tw + pad * 2, size + pad * 2 - 1
    if anchor == "mm":
        x, y = x - w // 2, y - h // 2
    rect(img, x - 2, y - 2, w + 4, h + 4, border)
    rect(img, x, y, w, h, bg)
    draw_text(img, x + pad, y + pad, text, fg, size=size)
    return x, y, w, h


# ------------------------------------------------------------------ 3x5 digits
_DIG = {
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "010", "010", "010"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
}


def digit(img, x, y, ch, col):
    for j, row in enumerate(_DIG[ch]):
        for i, c in enumerate(row):
            if c == "1":
                pset(img, x + i, y + j, col)


# ------------------------------------------------------------------ V1: riverbank
def crow(img, x, y, t, mode="fly", facing=-1, caw=False):
    """Little black crow. mode 'fly' (flapping) or 'perch'. (x, y) = feet/body bottom."""
    d = ImageDraw.Draw(img)
    x, y = int(round(x)), int(round(y))
    s = facing  # -1 faces left
    body = (30, 28, 44)
    hi = (70, 70, 104)
    if mode == "fly":
        up = step_frame(t, 10, 2) == 0
        d.ellipse([x - 4, y - 3, x + 4, y + 1], fill=body, outline=INK)
        # head
        hx = x + 4 * s
        d.rectangle([hx - 1, y - 4, hx + 1, y - 2], fill=body)
        pset(img, hx + 2 * s, y - 3, (150, 150, 150))
        pset(img, hx, y - 3, (230, 230, 240))
        # wings
        if up:
            d.polygon([(x - 2, y - 2), (x + 1, y - 2), (x - 3 - 2 * s, y - 9)], fill=body, outline=INK)
        else:
            d.polygon([(x - 2, y - 1), (x + 1, y - 1), (x - 2 - 2 * s, y + 5)], fill=body, outline=INK)
        # tail
        d.polygon([(x - 4 * s, y - 2), (x - 7 * s, y - 3), (x - 7 * s, y)], fill=body)
    else:
        # perched: upright oval body, tail down-back, feet
        d.ellipse([x - 3, y - 8, x + 3, y - 1], fill=body, outline=INK)
        d.polygon([(x - 2 * s, y - 2), (x - 6 * s, y + 2), (x - 4 * s, y + 2)], fill=body, outline=INK)
        hx, hy = x + 2 * s, y - 9
        d.ellipse([hx - 3, hy - 3, hx + 2, hy + 2], fill=body, outline=INK)
        pset(img, hx + 0 * s, hy - 1, (230, 230, 240))
        # beak (opens when cawing)
        bx = hx + 3 * s
        if caw:
            d.line([(bx, hy - 1), (bx + 2 * s, hy - 2)], fill=(120, 120, 128))
            d.line([(bx, hy + 1), (bx + 2 * s, hy + 2)], fill=(120, 120, 128))
        else:
            d.line([(bx, hy), (bx + 2 * s, hy)], fill=(120, 120, 128))
        pset(img, x - 1, y - 6, hi)
        pset(img, x - 1, y, (200, 150, 60))
        pset(img, x + 1, y, (200, 150, 60))


def crow_big(img, x, y, t, caw=False):
    """Screen-space flying crow (~26x20 px, facing LEFT), flapping at 8 fps."""
    d = ImageDraw.Draw(img)
    x, y = int(round(x)), int(round(y))
    body, hi = (34, 32, 50), (84, 84, 120)
    f = step_frame(t, 8, 4)
    # far wing (behind the body)
    tip_far = [(x + 1, y - 13), (x + 4, y - 9), (x + 3, y + 8), (x + 4, y - 9)][f]
    d.polygon([(x - 1, y - 2), (x + 4, y - 2), tip_far], fill=shade(body, 0.8), outline=INK)
    # tail fan
    d.polygon([(x + 5, y - 1), (x + 12, y - 4), (x + 13, y + 1), (x + 6, y + 2)], fill=body, outline=INK)
    # body + head
    d.ellipse([x - 7, y - 4, x + 7, y + 3], fill=body, outline=INK)
    d.ellipse([x - 12, y - 7, x - 4, y + 1], fill=body, outline=INK)
    pset(img, x - 9, y - 4, (240, 240, 250))
    # beak (opens on a caw)
    if caw:
        d.polygon([(x - 12, y - 4), (x - 18, y - 6), (x - 12, y - 3)], fill=(110, 110, 120), outline=INK)
        d.polygon([(x - 12, y - 2), (x - 17, y), (x - 12, y - 1)], fill=(110, 110, 120), outline=INK)
    else:
        d.polygon([(x - 12, y - 4), (x - 18, y - 2), (x - 12, y - 1)], fill=(110, 110, 120), outline=INK)
    # near wing
    tip = [(x - 3, y - 16), (x + 1, y - 11), (x - 1, y + 11), (x + 1, y - 11)][f]
    d.polygon([(x - 4, y - 1), (x + 3, y - 1), tip], fill=body, outline=INK)
    d.line([(x - 2, y - 1), ((x - 2 + tip[0]) // 2, (y - 1 + tip[1]) // 2)], fill=hi)


def reeds(img, t, x0, x1, base_y, n=9, seed=0, h=(16, 30), dark=False):
    """Susuki pampas grass swaying in the wind."""
    d = ImageDraw.Draw(img)
    stem = (120, 96, 60) if not dark else (70, 56, 50)
    plume = (236, 206, 150) if not dark else (150, 120, 96)
    plume_d = (200, 160, 110) if not dark else (110, 86, 70)
    for i in range(n):
        r = rng("reed", seed, i)
        x = x0 + (x1 - x0) * (i + r.uniform(-0.3, 0.3)) / max(1, n - 1)
        hh = r.uniform(*h)
        sway = wave(t, 0.7, 1.0, r.random()) * 2.5 + 2.0 + wave(t, 2.3, 0.6, r.random())
        tip = (x + sway, base_y - hh)
        mid = (x + sway * 0.35, base_y - hh * 0.5)
        d.line([(x, base_y), mid, tip], fill=stem)
        # plume: a few pixels bending with the wind
        for k in range(5):
            px = tip[0] + k * 0.9 + sway * 0.25
            py = tip[1] + k * 1.3
            pset(img, px, py, plume if k % 2 == 0 else plume_d)
            pset(img, px + 1, py, plume_d)


def sunset_sun(img, cx, cy, r):
    """Big retro setting sun: banded yellow->orange->pink disc with stripe gaps in its
    lower half and a dithered halo (cached RGBA)."""
    def mk():
        R = r + 10
        n = 2 * R + 1
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        dx, dy = xx - R, yy - R
        dist = np.sqrt(dx * dx + dy * dy)
        a = np.zeros((n, n, 4), np.uint8)
        by = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16.0
        bay = by[(np.arange(n) % 4)[:, None], (np.arange(n) % 4)[None, :]]
        halo = (dist > r) & (dist <= R) & (bay < (1 - (dist - r) / 10.0) * 0.55)
        a[halo] = (255, 190, 120, 255)
        disc = dist <= r
        k = np.clip((dy + r) / (2 * r), 0, 1)
        cols = [(255, 246, 170), (255, 214, 110), (255, 164, 80), (250, 120, 90), (236, 90, 110)]
        idx = np.clip((k * len(cols) + (bay - 0.5) * 0.8).astype(int), 0, len(cols) - 1)
        for i, c in enumerate(cols):
            m = disc & (idx == i)
            a[m] = c + (255,)
        # stripe gaps in the lower half (getting thicker toward the bottom)
        for j, (y0, th) in enumerate(((0.15, 1), (0.35, 1), (0.52, 2), (0.68, 2), (0.82, 3))):
            yy0 = int(R + y0 * r)
            a[yy0:yy0 + th][disc[yy0:yy0 + th]] = 0
        return Image.fromarray(a, "RGBA")
    spr = cached(("sun", r), mk)
    img.paste(spr, (int(cx - spr.width // 2), int(cy - spr.height // 2)), spr)


def sunset_river(img, y, h, t, sun_x):
    """Glowing dusk river: warm bands fading darker toward the viewer, drifting
    shimmer dashes and a broken sun-reflection column under sun_x."""
    def mk():
        c = Image.new("RGB", (W, h))
        gradient(c, 0, 0, W, h, (236, 150, 118), (104, 62, 96), steps=6)
        return c
    img.paste(cached(("sriver", h), mk), (0, int(y)))
    d = ImageDraw.Draw(img)
    for i in range(26):
        r = rng("shim", i)
        yy = y + 2 + (i * 7 % (h - 3))
        L = r.randint(3, 9)
        x = (r.uniform(0, W + 40) - t * r.uniform(4, 10)) % (W + 40) - 20
        k = (yy - y) / h
        col = mix((255, 214, 160), (190, 110, 120), k)
        if (step_frame(t, 4) + i) % 5:
            d.line([(x, yy), (x + L, yy)], fill=col)
    for j in range(0, h, 2):
        k = j / h
        wdt = int(10 + 8 * k + 3 * math.sin(t * 3 + j))
        off = int(2 * math.sin(t * 2.3 + j * 0.7))
        if (j // 2 + step_frame(t, 6)) % 3 != 0:
            d.line([(sun_x - wdt // 2 + off, y + j), (sun_x + wdt // 2 + off, y + j)],
                   fill=mix((255, 240, 170), (250, 160, 110), k))


def far_bank(img, y, col=(84, 52, 74)):
    """Silhouette of the far river bank: rooftops, trees and the Terminal needle."""
    def mk():
        im = Image.new("RGBA", (W, 40), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        r = rng("farbank")
        x = 0
        while x < W:
            w = r.randint(8, 20)
            h = r.randint(2, 6)
            d.rectangle([x, 40 - h, x + w, 39], fill=col)
            d.polygon([(x - 2, 40 - h), (x + w // 2, 40 - h - 3), (x + w + 2, 40 - h)], fill=col)
            x += w + r.randint(0, 6)
        for tx in (40, 118, 300, 350):
            d.ellipse([tx - 4, 30, tx + 4, 37], fill=col)
        # the Terminal tower far away (thin needle + saucer deck)
        d.line([(282, 8), (282, 39)], fill=col)
        d.rectangle([278, 16, 286, 17], fill=col)
        d.rectangle([280, 26, 284, 27], fill=col)
        return im
    lay = cached(("farbank", col), mk)
    img.paste(lay, (0, int(y) - 40), lay)


def river_bank(img, t, y, col=(52, 36, 50), rim=(150, 84, 76)):
    """Dark backlit grassy bank (dusk) from row y down, with a lit rim + tufts."""
    def mk():
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        pts = [(0, H)]
        for x in range(0, W + 8, 8):
            pts.append((x, y + 3 * math.sin(x * 0.03) + 2 * math.sin(x * 0.11)))
        pts.append((W, H))
        d.polygon(pts, fill=col)
        for x in range(0, W, 1):
            yy = y + 3 * math.sin(x * 0.03) + 2 * math.sin(x * 0.11)
            im.putpixel((x, int(yy)), rim + (255,))
        r = rng("tufts")
        for _ in range(60):
            x = r.randrange(W)
            yy = int(y + 3 * math.sin(x * 0.03) + 2 * math.sin(x * 0.11))
            hgt = r.randint(2, 5)
            d.line([(x, yy), (x + r.choice((-1, 0, 1)), yy - hgt)], fill=col)
            im.putpixel((x, yy - hgt), rim + (255,)) if 0 <= yy - hgt < H else None
        for _ in range(90):
            x, yy = r.randrange(W), r.randrange(int(y) + 6, H)
            im.putpixel((x, yy), (66, 46, 60, 255))
        return im
    lay = cached(("bank", y), mk)
    img.paste(lay, (0, 0), lay)


# ------------------------------------------------------------------ V2: pachinko
MW, MH = 46, 74
_RED = (206, 40, 62)
_RED_D = (150, 24, 48)
_CHROME = (214, 220, 232)
_CHROME_D = (150, 158, 182)
_GOLD = (254, 196, 60)
_FIELD = (30, 42, 96)


def _machine_static(small=False):
    """Pachinko cabinet (RGBA MW x MH), static parts only."""
    img = Image.new("RGBA", (MW, MH + 5), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    oy = 5
    # lamp dome on top (base)
    d.rectangle([MW // 2 - 5, 1, MW // 2 + 5, oy + 1], fill=_CHROME_D, outline=INK)
    # cabinet
    d.rectangle([0, oy, MW - 1, oy + MH - 1], fill=_RED, outline=INK)
    d.rectangle([1, oy + 1, 2, oy + MH - 2], fill=_CHROME)
    d.rectangle([MW - 3, oy + 1, MW - 2, oy + MH - 2], fill=_CHROME_D)
    d.line([(3, oy + 1), (MW - 4, oy + 1)], fill=(236, 90, 100))
    # glass play field
    fx0, fy0, fx1, fy1 = 4, oy + 5, MW - 5, oy + 47
    d.rectangle([fx0 - 1, fy0 - 1, fx1 + 1, fy1 + 1], fill=_CHROME, outline=INK)
    d.rectangle([fx0, fy0, fx1, fy1], fill=_FIELD)
    # gold rail (big circle)
    d.ellipse([fx0 + 1, fy0 + 1, fx1 - 1, fy1 + 8], outline=_GOLD)
    # pins (staggered grid)
    for j in range(0, 40, 4):
        for i in range(0, 36, 4):
            px = fx0 + 3 + i + (2 if (j // 4) % 2 else 0)
            py = fy0 + 3 + j
            if fx0 < px < fx1 and fy0 < py < fy1:
                img.putpixel((px, py), (150, 170, 220, 255))
    # decorative 'wings' around the LCD
    d.polygon([(8, oy + 20), (14, oy + 14), (14, oy + 34), (8, oy + 28)], fill=(90, 60, 150), outline=INK)
    d.polygon([(MW - 9, oy + 20), (MW - 15, oy + 14), (MW - 15, oy + 34), (MW - 9, oy + 28)],
              fill=(90, 60, 150), outline=INK)
    # LCD frame
    d.rectangle([14, oy + 15, MW - 15, oy + 31], fill=(10, 10, 20), outline=_GOLD)
    # start pocket
    d.rectangle([MW // 2 - 3, oy + 38, MW // 2 + 3, oy + 41], fill=_GOLD, outline=INK)
    # lower panel: tray + handle
    d.rectangle([4, oy + 52, MW - 5, oy + 60], fill=_CHROME, outline=INK)
    d.rectangle([5, oy + 53, MW - 6, oy + 54], fill=(250, 250, 255))
    d.rectangle([4, oy + 63, MW - 5, oy + 68], fill=_RED_D, outline=INK)
    d.ellipse([MW - 12, oy + 62, MW - 4, oy + 70], fill=_CHROME_D, outline=INK)
    pset(img, MW - 9, oy + 64, (255, 255, 255, 255))
    # name plate 「银魂」
    t = text_sprite("银魂", (255, 240, 180), 12, "pixel", outline=INK)
    img.alpha_composite(t, (MW // 2 - t.width // 2, oy + 46))
    return img


def machine_sprite():
    return cached("machine", _machine_static)


def machine_small():
    def mk():
        m = _machine_static()
        m = m.resize((MW * 3 // 5, (MH + 5) * 3 // 5), Image.NEAREST)
        a = np.asarray(m).astype(np.float32)
        a[..., :3] *= 0.62
        a[..., 2] += 12
        return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
    return cached("machine_small", mk)


def draw_machine(img, cx, bottom, t, reels=("7", "7", None), spin=True, lit=True, balls=True,
                 tray=1.0, lamp=0.0):
    """Big pachinko machine with animated balls, LCD reels, top lamp."""
    spr = machine_sprite()
    x0 = int(cx - MW // 2)
    y0 = int(bottom - spr.height)
    img.paste(spr, (x0, y0), spr)
    oy = y0 + 5
    d = ImageDraw.Draw(img)
    # top lamp (rotating siren when lamp > 0)
    f = step_frame(t, 12)
    lc = [(255, 70, 90), (255, 200, 60), (90, 220, 255)][f % 3] if lamp > 0 else (120, 90, 90)
    d.ellipse([cx - 5, y0 - 4, cx + 5, y0 + 5], fill=lc, outline=INK)
    pset(img, cx - 2, y0 - 2, (255, 255, 255))
    if lamp > 0 and f % 2 == 0:
        for a in range(0, 360, 45):
            r0, r1 = 7, 10
            aa = math.radians(a + f * 20)
            d.line([(cx + math.cos(aa) * r0, y0 + math.sin(aa) * r0 * 0.7),
                    (cx + math.cos(aa) * r1, y0 + math.sin(aa) * r1 * 0.7)], fill=(255, 240, 150))
    # balls raining through the pins
    if balls:
        for i in range(16):
            r = rng("pball", i)
            sp = r.uniform(26, 40)
            ph = r.random()
            yy = ((t * sp / 40.0 + ph) % 1.0) * 40
            xx = 6 + r.uniform(0, 32) + abs(((yy * 0.5 + i) % 4) - 2)
            pset(img, x0 + xx, oy + 6 + yy, (236, 238, 248))
    # LCD reels
    lx, ly = x0 + 16, oy + 18
    for k, ch in enumerate(reels):
        col = (255, 230, 90) if lit else (200, 200, 200)
        if ch is None:
            # spinning: random digit each 1/15 s + blur
            ch = "0123456789"[step_frame(t, 15) * 7 % 10]
            col = (255, 255, 255)
            digit(img, lx + k * 5, ly + 1, ch, col)
            pset(img, lx + k * 5 + 1, ly + 7, (120, 120, 160))
        else:
            digit(img, lx + k * 5, ly + 2, ch, col)
    if lit:
        # blinking frame bulbs
        for i in range(8):
            on = (f + i) % 3 == 0
            bx = x0 + 3 + i * 5.6
            pset(img, bx, oy + 2, (255, 240, 120) if on else (140, 60, 60))
    # tray balls
    if tray > 0:
        n = int(30 * tray)
        for i in range(n):
            r = rng("tray", i)
            px = x0 + 7 + r.uniform(0, MW - 16)
            py = oy + 55 + r.uniform(0, 3) - (1 if i % 3 == 0 else 0)
            pset(img, px, py, (236, 238, 248) if i % 2 else (170, 176, 196))


def parlor_bg(img, t, lit=True):
    """Pachinko parlor back wall with a row of small machines + carpet floor."""
    def mk():
        c = Image.new("RGB", (W, H), (0, 0, 0))
        gradient(c, 0, 0, W, 136, (46, 16, 36), (92, 30, 52), steps=6)
        # ceiling strip + light panels
        rect(c, 0, 0, W, 60, (34, 14, 30))
        for x in range(8, W, 36):
            rect(c, x, 56, 22, 3, (255, 236, 190))
            rect(c, x - 1, 55, 24, 1, (120, 80, 70))
        rect(c, 0, 60, W, 2, (20, 8, 20))
        # wall stripes
        for x in range(0, W, 12):
            rect(c, x, 62, 1, 74, (74, 24, 44))
        # carpet
        rect(c, 0, 136, W, H - 136, (120, 26, 40))
        a = np.asarray(c).copy()
        yy, xx = np.mgrid[136:H, 0:W]
        dia = ((np.abs((xx % 16) - 8) + np.abs(((yy - 136) % 12) - 6)) == 6)
        sub = a[136:H]
        sub[dia] = (178, 120, 60)
        sub[((xx + yy) % 2 == 0) & (((yy - 136) % 12) == 0)] = (96, 20, 34)
        a[136:H] = sub
        c = Image.fromarray(a, "RGB")
        rect(c, 0, 136, W, 1, (30, 10, 20))
        # row of small machines along the wall
        sm = machine_small()
        for i in range(-1, 14):
            x = i * 31 + 4
            c.paste(sm, (x, 136 - sm.height), sm)
        # base counter under them
        rect(c, 0, 132, W, 5, (60, 40, 50))
        rect(c, 0, 132, W, 1, (140, 110, 110))
        return c
    img.paste(cached("parlor", mk))
    # blinking lights on the small machines
    if lit:
        f = step_frame(t, 8)
        sm = machine_small()
        for i in range(-1, 14):
            x = i * 31 + 4
            y = 136 - sm.height
            r = rng("pl", i)
            for k in range(3):
                on = (f + i + k * 2) % 5 < 2
                if on:
                    c = [(255, 90, 120), (255, 220, 90), (100, 220, 255)][(i + k) % 3]
                    pset(img, x + 5 + k * 8, y + 3, c)
                    pset(img, x + 6 + k * 8, y + 3, c)
            # little LCD flicker
            if (f + i) % 4 == 0:
                rect(img, x + 10, y + 12, 6, 3, (120, 200, 255))


def stool(img, x, top, floor):
    d = ImageDraw.Draw(img)
    d.rectangle([x - 1, top + 2, x + 1, floor - 1], fill=_CHROME_D, outline=INK)
    d.rectangle([x - 5, floor - 2, x + 5, floor - 1], fill=(60, 60, 70), outline=INK)
    d.ellipse([x - 6, top - 1, x + 6, top + 3], fill=(200, 40, 50), outline=INK)
    d.line([(x - 4, top), (x + 2, top)], fill=(240, 110, 110))


def lcd_closeup(img, cx, cy, t, reels, spin_k, lit=True, flash=0.0, hot=False):
    """Big LCD close-up for the inset panel. reels: 3 entries, a char = stopped,
    None = generic spin, float = reel strip position (digit value, fractional part =
    scroll offset; decreasing values scroll the strip downward).
    spin_k: 0..1 vertical bounce of the 3rd reel when it stops.
    hot: the 'all three sevens?!' moment (frame blinks red/gold)."""
    w, h = 150, 74
    x0, y0 = int(cx - w // 2), int(cy - h // 2)
    d = ImageDraw.Draw(img)
    f = step_frame(t, 12)
    # background: dark with radial rainbow when lit
    rect(img, x0, y0, w, h, (14, 12, 34))
    if lit:
        for i in range(12):
            a = math.radians(i * 30 + f * 6)
            col = [(90, 30, 120), (30, 40, 110)][i % 2]
            d.polygon([(cx, cy), (cx + math.cos(a) * 120, cy + math.sin(a) * 120),
                       (cx + math.cos(a + 0.26) * 120, cy + math.sin(a + 0.26) * 120)], fill=col)
    # bulb frame
    for i in range(0, w, 6):
        on = lit and ((i // 6 + f) % 3 == 0)
        c = (255, 230, 100) if on else (90, 70, 60)
        pset(img, x0 + i, y0 + 1, c)
        pset(img, x0 + i, y0 + h - 2, c)
    # reel windows
    rw, rh = 34, 44
    gap = 8
    total = rw * 3 + gap * 2
    rx0 = cx - total // 2
    ry0 = cy - rh // 2 + 6
    for k in range(3):
        x = rx0 + k * (rw + gap)
        rect(img, x - 2, ry0 - 2, rw + 4, rh + 4, INK)
        rect(img, x, ry0, rw, rh, (250, 246, 236))
        rect(img, x, ry0, rw, 4, (220, 214, 200))
        rect(img, x, ry0 + rh - 4, rw, 4, (220, 214, 200))
        ch = reels[k]
        if isinstance(ch, float):
            # real reel strip: digit n sits at (n - v) * pitch below the window centre
            v = ch
            pitch = 40
            base = math.floor(v)
            speed_blur = v - 7.0 > 1.2
            for n in range(base - 1, base + 3):
                dch = "0123456789"[n % 10]
                col = (228, 40, 60) if dch == "7" else (60, 90, 200)
                if speed_blur:
                    col = (90, 90, 120)
                spr = _big_digit(dch, col)
                yy = int(round(ry0 + rh // 2 - spr.height // 2 + (n - v) * pitch))
                crop_top = max(0, ry0 - yy)
                crop_bot = min(spr.height, ry0 + rh - yy)
                if crop_bot > crop_top:
                    part = spr.crop((0, crop_top, spr.width, crop_bot))
                    img.paste(part, (x + rw // 2 - spr.width // 2, yy + crop_top), part)
            if speed_blur:
                for j in range(6):
                    yy = ry0 + 4 + (j * 7 + int(t * 300)) % (rh - 8)
                    rect(img, x + 3, yy, rw - 6, 1, (200, 200, 214))
            if hot and step_frame(t, 15) % 2 == 0:
                for i in range(2):
                    d.rectangle([x - 3 - i, ry0 - 3 - i, x + rw + 2 + i, ry0 + rh + 2 + i],
                                outline=(255, 220, 60) if i == 0 else (230, 40, 60))
        elif ch is None:
            # spinning strip: two digits scrolling fast + blur lines
            off = (t * 260) % 40
            for j in range(-1, 2):
                dch = "0123456789"[(int(t * 6.5) + j) % 10]
                spr = _big_digit(dch, (60, 60, 80))
                yy = int(ry0 + rh // 2 - spr.height // 2 + j * 40 + off - 20)
                crop_top = max(0, ry0 - yy)
                crop_bot = min(spr.height, ry0 + rh - yy)
                if crop_bot > crop_top:
                    part = spr.crop((0, crop_top, spr.width, crop_bot))
                    img.paste(part, (x + rw // 2 - spr.width // 2, yy + crop_top), part)
            for j in range(6):
                yy = ry0 + 4 + (j * 7 + int(t * 300)) % (rh - 8)
                rect(img, x + 3, yy, rw - 6, 1, (200, 200, 214))
        else:
            col = (228, 40, 60) if ch == "7" else (60, 90, 200)
            if not lit:
                col = (120, 120, 120)
            spr = _big_digit(ch, col)
            by = int(-6 * math.sin(clamp(spin_k) * math.pi) if spin_k < 1 else 0) if k == 2 else 0
            img.paste(spr, (x + rw // 2 - spr.width // 2, ry0 + rh // 2 - spr.height // 2 + by), spr)
    if lit and (f // 3) % 2 == 0:
        spr = cached(("reach",), lambda: text_sprite("REACH!!", (255, 240, 90), 12, "pixel", outline=INK))
        img.paste(spr, (cx - spr.width // 2, y0 + 3), spr)
    if flash > 0:
        from engine.gfx import overlay_rect
        overlay_rect(img, x0, y0, w, h, (255, 255, 255), flash)


def _big_digit(ch, col):
    return cached(("bigdig", ch, col), lambda: text_sprite(ch, col, 32, "hei", outline=INK, thick=2))


def stamp(img, cx, cy, t, t0, text="输光", sub="所持金：0円", col=(214, 36, 50)):
    """Red hanko stamp slamming onto the page."""
    if t < t0:
        return
    p = t - t0
    s = 1.0 if p > 0.12 else lerp(2.2, 1.0, ease_out(p / 0.12))

    def mk():
        big = text_sprite(text, col, 32, "brush", outline=None)
        w, h = big.width + 16, big.height + 12
        sub_s = text_sprite(sub, col, 12, "pixel") if sub else None
        sw, sh = (sub_s.width + 8, sub_s.height + 4) if sub_s else (0, 0)
        im = Image.new("RGBA", (max(w, sw), h + sh), (0, 0, 0, 0))
        dd = ImageDraw.Draw(im)
        ox = (im.width - w) // 2
        dd.rectangle([ox, 0, ox + w - 1, h - 1], outline=col, width=3)
        dd.rectangle([ox + 4, 4, ox + w - 5, h - 5], outline=col, width=1)
        im.alpha_composite(big, (ox + 8, 6))
        if sub_s:
            im.alpha_composite(sub_s, ((im.width - sub_s.width) // 2, h + 2))
        # distressed ink: knock out a few pixels
        a = np.asarray(im).copy()
        r = rng("stampnoise")
        for _ in range(60):
            x, y = r.randrange(im.width), r.randrange(im.height)
            a[y, x, 3] = 0
        im = Image.fromarray(a, "RGBA")
        return im.rotate(12, resample=Image.NEAREST, expand=True)
    spr = cached(("stamp", text, sub, col), mk)
    if s != 1.0:
        spr = spr.resize((int(spr.width * s), int(spr.height * s)), Image.NEAREST)
    img.paste(spr, (int(cx - spr.width / 2), int(cy - spr.height / 2)), spr)


# ------------------------------------------------------------------ V3: calendar + shoujo
CAL_W, CAL_H = 66, 96


def _cal_page(kind):
    img = Image.new("RGBA", (CAL_W, CAL_H - 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, CAL_W - 1, CAL_H - 13], fill=(252, 250, 244), outline=INK)
    d.line([(1, CAL_H - 14), (CAL_W - 2, CAL_H - 14)], fill=(214, 208, 196))
    if kind == "sun":
        num = text_sprite("24", (214, 40, 50), 32, "hei", outline=None)
        img.alpha_composite(num, (CAL_W // 2 - num.width // 2, 6))
        wd = text_sprite("周日", (214, 40, 50), 16, "pixel")
        img.alpha_composite(wd, (CAL_W // 2 - wd.width // 2, 46))
        s = text_sprite("SUNDAY", (214, 110, 110), 12, "pixel")
        s = s.resize((s.width * 2 // 3, s.height * 2 // 3), Image.NEAREST)
        img.alpha_composite(s, (CAL_W // 2 - s.width // 2, 63))
    else:
        num = text_sprite("25", (30, 26, 40), 32, "hei", outline=None)
        img.alpha_composite(num, (CAL_W // 2 - num.width // 2, 6))
        wd = text_sprite("周一", (30, 26, 40), 16, "pixel")
        img.alpha_composite(wd, (CAL_W // 2 - wd.width // 2, 46))
        # hand-drawn red circle around the weekday
        cx, cy = CAL_W // 2, 54
        pts = []
        for i in range(26):
            a = i / 24 * 2 * math.pi - 0.3
            rr = 1 + 0.06 * (i / 24)
            pts.append((cx + math.cos(a) * 22 * rr, cy + math.sin(a) * 10 * rr))
        d.line(pts, fill=(228, 40, 50), width=2)
        s = text_sprite("Jump!", (228, 40, 50), 12, "pixel")
        img.alpha_composite(s, (CAL_W - s.width - 2, 68))
    return img


def cal_page(kind):
    return cached(("calpage", kind), lambda: _cal_page(kind))


def wall_bg(img, col=(230, 214, 182)):
    def mk():
        c = Image.new("RGB", (W, H), col)
        a = np.asarray(c).copy()
        yy, xx = np.mgrid[0:H, 0:W]
        a[((xx % 10) == 0)] = shade(col, 0.94)
        a[((xx % 10) == 5) & ((yy % 6) == 0)] = shade(col, 0.9)
        c = Image.fromarray(a, "RGB")
        rect(c, 0, 178, W, 38, (150, 96, 64))
        rect(c, 0, 178, W, 2, (96, 58, 40))
        return c
    img.paste(cached(("wall", col), mk))


def calendar(img, cx, top, t, t_tear):
    """Tear-off calendar hanging on a nail; the top page rips away at t_tear."""
    d = ImageDraw.Draw(img)
    x0 = int(cx - CAL_W // 2)
    # nail + string
    pset(img, cx, top - 16, INK)
    d.line([(cx, top - 15), (x0 + 8, top)], fill=(120, 90, 70))
    d.line([(cx, top - 15), (x0 + CAL_W - 9, top)], fill=(120, 90, 70))
    rect(img, cx - 1, top - 17, 3, 3, (90, 90, 100))
    # backing board
    rect(img, x0 - 3, top - 1, CAL_W + 6, CAL_H + 5, INK)
    rect(img, x0 - 2, top, CAL_W + 4, CAL_H + 3, (190, 140, 90))
    # red header with binding
    rect(img, x0, top + 1, CAL_W, 11, (200, 40, 50))
    rect(img, x0, top + 1, CAL_W, 1, (240, 110, 110))
    for i in range(4):
        rect(img, x0 + 8 + i * 16, top - 1, 3, 4, (200, 200, 210))
        pset(img, x0 + 8 + i * 16, top - 1, INK)
    # pages underneath (stack edge)
    rect(img, x0 + 1, top + 12 + CAL_H - 12, CAL_W - 2, 2, (210, 204, 190))
    under = cal_page("mon")
    img.paste(under, (x0, top + 12), under)
    if t < t_tear:
        pg = cal_page("sun")
        # slight flutter before the tear
        img.paste(pg, (x0, top + 12), pg)
    else:
        p = t - t_tear
        if p < 0.9:
            pg = cal_page("sun")
            ang = 40 * p / 0.9 + 25 * ease_out(clamp(p / 0.2))
            r = pg.rotate(ang, resample=Image.NEAREST, expand=True)
            px = x0 - 70 * ease_out(clamp(p / 0.6)) - p * 30
            py = top + 12 - 100 * ease_out(clamp(p / 0.7))
            img.paste(r, (int(px - (r.width - CAL_W) / 2), int(py - (r.height - pg.height) / 2)), r)
        # torn stub under the binding
        for i in range(0, CAL_W, 2):
            hgt = 2 + (i * 7 % 3)
            rect(img, x0 + i, top + 12, 2, hgt, (252, 250, 244))
        d.line([(x0, top + 12), (x0 + CAL_W - 1, top + 12)], fill=INK)


def shoujo_bg(img, t, cx, cy):
    """Pink/lilac sparkly 'shoujo manga' background with light rays + bubbles."""
    def mk():
        c = Image.new("RGB", (W, H))
        gradient(c, 0, 0, W, H, (255, 206, 222), (206, 170, 240), steps=7)
        return c
    img.paste(cached("shoujo", mk))
    d = ImageDraw.Draw(img)
    rot = t * 12
    for i in range(16):
        a = math.radians(rot + i * 22.5)
        if i % 2:
            continue
        L = 300
        d.polygon([(cx, cy), (cx + math.cos(a - 0.12) * L, cy + math.sin(a - 0.12) * L),
                   (cx + math.cos(a + 0.12) * L, cy + math.sin(a + 0.12) * L)], fill=(255, 232, 240))
    # bubbles rising
    for i in range(14):
        r = rng("bub", i)
        x = r.uniform(0, W)
        y = H + 10 - ((t * r.uniform(8, 18) + r.uniform(0, H + 20)) % (H + 20))
        rr = r.choice((2, 3, 4))
        d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(255, 255, 255))
        pset(img, x - rr + 1, y - rr + 1, (255, 255, 255))
    # little flowers
    for i in range(8):
        r = rng("flw", i)
        x = r.uniform(0, W)
        y = (r.uniform(0, H) + t * 6) % H
        c = [(255, 150, 180), (255, 255, 255), (255, 210, 110)][i % 3]
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            pset(img, x + dx, y + dy, c)
        pset(img, x, y, (255, 230, 120))


JUMP_W, JUMP_H = 34, 44


def _mk_jump():
    """Weekly Shonen JUMP (screen-space prop, drawn chunky to sit with 3x-zoomed sprites)."""
    im = Image.new("RGBA", (JUMP_W, JUMP_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, JUMP_W - 1, JUMP_H - 1], fill=INK)
    d.rectangle([2, 2, JUMP_W - 3, JUMP_H - 3], fill=(252, 204, 52))          # yellow cover
    d.rectangle([2, 2, JUMP_W - 3, 15], fill=(226, 40, 52))                   # red masthead
    d.line([(2, 16), (JUMP_W - 3, 16)], fill=INK)
    logo = text_sprite("JUMP", (255, 255, 255), 12, "pixel", outline=INK)
    im.alpha_composite(logo, ((JUMP_W - logo.width) // 2, 2))
    # cover hero: spiky black hair, face, grin, orange gi
    cx = JUMP_W // 2
    d.polygon([(cx - 9, 25), (cx - 7, 18), (cx - 4, 22), (cx - 1, 17), (cx + 2, 22), (cx + 5, 18),
               (cx + 8, 23), (cx + 9, 27), (cx - 9, 27)], fill=(30, 26, 40))
    d.rectangle([cx - 6, 25, cx + 6, 32], fill=(255, 214, 180), outline=INK)
    d.point((cx - 3, 28), fill=INK)
    d.point((cx + 3, 28), fill=INK)
    d.line([(cx - 2, 30), (cx + 2, 30)], fill=(180, 60, 60))
    d.rectangle([cx - 9, 33, cx + 9, JUMP_H - 3], fill=(250, 130, 40), outline=INK)
    d.line([(cx, 33), (cx, JUMP_H - 3)], fill=(30, 60, 150))
    # burst sticker '新连载!'
    d.ellipse([JUMP_W - 13, 18, JUMP_W - 3, 28], fill=(255, 255, 255), outline=INK)
    d.point((JUMP_W - 8, 22), fill=(226, 40, 52))
    d.point((JUMP_W - 8, 23), fill=(226, 40, 52))
    d.point((JUMP_W - 8, 25), fill=(226, 40, 52))
    # spine shading + page edges
    d.line([(2, 17), (2, JUMP_H - 3)], fill=(214, 164, 30))
    d.line([(JUMP_W - 2, 2), (JUMP_W - 2, JUMP_H - 2)], fill=(236, 232, 220))
    return im


def jump_mag(img, cx, cy, t, glint_period=0.9):
    """Draw the JUMP centred at (cx, cy) with a diagonal glint sweeping across it."""
    spr = cached("jumpmag", _mk_jump)
    x0, y0 = int(cx - JUMP_W / 2), int(cy - JUMP_H / 2)
    img.paste(spr, (x0, y0), spr)
    ph = (t % glint_period) / glint_period
    gx = -10 + ph * (JUMP_W + 34)
    d = ImageDraw.Draw(img)
    for yy in range(2, JUMP_H - 2):
        xx = gx - yy * 0.6
        for w in range(3):
            px = int(xx + w)
            if 2 <= px < JUMP_W - 2:
                c = img.getpixel((x0 + px, y0 + yy)) if 0 <= x0 + px < W and 0 <= y0 + yy < H else None
                if c is not None:
                    d.point((x0 + px, y0 + yy), fill=mix(c, (255, 255, 255), 0.7 if w == 1 else 0.45))


def tears_spray(img, x, y, t, t0, side, n=12, col=(96, 186, 255), seed=0):
    """Comedic fountain of tears squirting sideways from an eye at screen (x, y)."""
    if t < t0:
        return
    d = ImageDraw.Draw(img)
    for i in range(n):
        r = rng("tear", seed, i)
        ph = ((t - t0) * 2.4 + i / n) % 1.0
        if t - t0 < ph / 2.4:            # not emitted yet
            continue
        vx = r.uniform(34, 58) * side
        vy = -r.uniform(22, 40)
        px = x + vx * ph * 0.5
        py = y + vy * ph * 0.5 + 70 * (ph * 0.5) ** 2 * 4
        s = 3 if ph < 0.45 else 2
        d.rectangle([int(px), int(py), int(px) + s - 1, int(py) + s - 1], fill=col)
        d.point((int(px), int(py)), fill=(235, 248, 255))


def _mk_note(col, double):
    im = Image.new("RGBA", (9 if double else 6, 9), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 6, 3, 8], fill=col)
    d.line([(3, 0), (3, 7)], fill=col)
    if double:
        d.ellipse([5, 5, 8, 7], fill=col)
        d.line([(8, 0), (8, 6)], fill=col)
        d.line([(3, 0), (8, 0)], fill=col)
        d.line([(3, 1), (8, 1)], fill=col)
    else:
        d.line([(4, 1), (5, 3)], fill=col)
        d.point((4, 0), fill=col)
    from engine.gfx import outline as _outline
    return _outline(im, INK)


def note(img, x, y, col=(255, 150, 210), double=False):
    """Music note (♪ / ♫) with ink outline, top-left at (x, y)."""
    spr = cached(("note", col, double), lambda: _mk_note(col, double))
    img.paste(spr, (int(x), int(y)), spr)


def star(img, cx, cy, r, rot=0.0, col=(255, 236, 90), outline=INK):
    """5-point star (e.g. kira-kira star eyes)."""
    pts = []
    for i in range(10):
        a = rot - math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    ImageDraw.Draw(img).polygon(pts, fill=col, outline=outline)
    pset(img, cx - 1, cy - 1, (255, 255, 255))


def twinkle(img, x, y, s, col=(255, 255, 255)):
    """4-point star of arm length s (drawn every frame, caller animates s)."""
    s = int(s)
    if s <= 0:
        return
    d = ImageDraw.Draw(img)
    d.line([(x - s, y), (x + s, y)], fill=col)
    d.line([(x, y - s), (x, y + s)], fill=col)
    if s >= 3:
        d.line([(x - 1, y - 1), (x + 1, y + 1)], fill=col)
        d.line([(x - 1, y + 1), (x + 1, y - 1)], fill=col)


# ------------------------------------------------------------------ V4: concert stage
STAGE_Y = 118


def stage_bg(img, t):
    def mk():
        c = Image.new("RGB", (W, H))
        gradient(c, 0, 0, W, H, (26, 16, 48), (60, 24, 70), steps=6)
        d = ImageDraw.Draw(c)
        # backdrop screen
        d.rectangle([44, 30, 340, STAGE_Y - 1], fill=(40, 26, 72), outline=INK)
        for x in range(46, 340, 8):
            d.line([(x, 31), (x, STAGE_Y - 2)], fill=(48, 32, 84))
        # banner (high up: only seen in wide framings)
        d.rectangle([96, 6, 288, 30], fill=(250, 90, 160), outline=INK)
        d.rectangle([98, 8, 286, 28], outline=(255, 190, 220))
        tx = text_sprite("寺门通 LIVE", (255, 255, 255), 16, "pixel", outline=(150, 20, 90))
        c.paste(tx, (192 - tx.width // 2, 10), tx)
        # lighting truss
        d.rectangle([30, 52, 354, 55], fill=(90, 90, 104), outline=INK)
        for x in range(34, 354, 6):
            d.line([(x, 53), (x + 3, 54)], fill=(60, 60, 72))
        # stars
        for sx, sy in ((72, 50), (312, 50), (60, 86), (324, 86)):
            d.polygon([(sx, sy - 6), (sx + 2, sy - 2), (sx + 6, sy - 2), (sx + 3, sy + 1), (sx + 4, sy + 6),
                       (sx, sy + 3), (sx - 4, sy + 6), (sx - 3, sy + 1), (sx - 6, sy - 2), (sx - 2, sy - 2)],
                      fill=(255, 220, 90), outline=INK)
        # speakers
        for sx in (20, 344):
            d.rectangle([sx, 70, sx + 20, STAGE_Y + 12], fill=(30, 30, 38), outline=INK)
            for yy in (80, 100):
                d.ellipse([sx + 4, yy, sx + 16, yy + 12], fill=(60, 60, 70), outline=INK)
                d.ellipse([sx + 8, yy + 4, sx + 12, yy + 8], fill=(20, 20, 26))
        # stage platform
        d.rectangle([30, STAGE_Y, 354, STAGE_Y + 14], fill=(70, 50, 60), outline=INK)
        d.rectangle([30, STAGE_Y, 354, STAGE_Y + 2], fill=(160, 120, 110))
        for x in range(34, 354, 20):
            d.line([(x, STAGE_Y + 3), (x, STAGE_Y + 13)], fill=(56, 40, 50))
        # audience floor
        d.rectangle([0, STAGE_Y + 15, W, H], fill=(22, 14, 34))
        return c
    img.paste(cached("stage", mk))
    # chasing bulbs around the backdrop
    f = step_frame(t, 10)
    k = 0
    for x in range(46, 340, 6):
        on = (k + f) % 4 == 0
        pset(img, x, 29, (255, 240, 150) if on else (110, 80, 60))
        k += 1
    for y in range(32, STAGE_Y, 6):
        on = (k + f) % 4 == 0
        pset(img, 43, y, (255, 240, 150) if on else (110, 80, 60))
        pset(img, 341, y, (255, 240, 150) if on else (110, 80, 60))
        k += 1
    # truss lamps (colour cycling)
    for i, x in enumerate(range(44, 350, 22)):
        c = [(255, 90, 160), (90, 200, 255), (255, 230, 90), (160, 255, 140)][(i + f // 2) % 4]
        rect(img, x - 3, 56, 7, 5, INK)
        rect(img, x - 2, 57, 5, 3, c)
        pset(img, x - 1, 57, (255, 255, 255))
    # footlights
    for i, x in enumerate(range(40, 350, 24)):
        c = [(255, 90, 160), (90, 200, 255), (255, 230, 90)][(i + f // 3) % 3]
        rect(img, x, STAGE_Y + 6, 4, 3, c)


def beams(img, beams_list, level=0.32):
    """Dithered light beams. beams_list: [(apex, p1, p2, color)]"""
    a = np.asarray(img).copy()
    dm = cached("beam_dither", lambda: dither_mask(W, H, level))
    for apex, p1, p2, col in beams_list:
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon([apex, p1, p2], fill=255)
        mm = (np.asarray(m) > 0) & dm
        a[mm] = (a[mm].astype(np.int16) // 2 + np.array(col, np.int16) // 2).astype(np.uint8)
    img.paste(Image.fromarray(a, "RGB"))


_STICK_COLS = [(120, 255, 150), (255, 110, 200), (110, 200, 255), (255, 240, 110)]


def crowd(img, t, y, n, r, x0=-10, x1=W + 10, seed=0, skip=None, col=(44, 30, 62), beat=2.2,
          rim=(110, 84, 150)):
    """Row of fan silhouettes bouncing to the beat, waving glow sticks."""
    d = ImageDraw.Draw(img)
    for i in range(n):
        rr = rng("crowd", seed, i)
        x = x0 + (x1 - x0) * (i + 0.5 + rr.uniform(-0.25, 0.25)) / n
        if skip and skip[0] <= x <= skip[1]:
            continue
        ph = rr.random()
        b = 1 if math.sin((t * beat + ph * 0.3) * 2 * math.pi) > 0 else 0
        hy = y - r * 2 - b * 2
        # shoulders + head
        d.ellipse([x - r * 1.6, hy + r * 1.3, x + r * 1.6, hy + r * 4], fill=col)
        d.ellipse([x - r, hy - r, x + r, hy + r], fill=col)
        d.arc([x - r, hy - r, x + r, hy + r], 200, 320, fill=rim)
        # glow stick
        sc = _STICK_COLS[i % 4]
        sw = math.sin((t * beat + ph * 0.3) * 2 * math.pi) * 0.7
        side = 1 if i % 2 else -1
        hx, hyy = x + side * r * 1.2, hy - r * 0.5
        L = r * 2.4
        tx, ty = hx + math.sin(sw) * L, hyy - math.cos(sw) * L
        d.line([(hx, hyy), (tx, ty)], fill=sc, width=2 if r >= 5 else 1)
        pset(img, tx, ty - 1, (255, 255, 255))


# ------------------------------------------------------------------ V6: Otae's room + crawlspace
JOIST_Y = 104    # underside of the floorboards (crawlspace ceiling) in bottom-panel world
DIRT_Y = 138     # crawlspace ground


def crawlspace(img, t, gap_xs=(118, 176, 236, 290)):
    def mk():
        c = Image.new("RGB", (W, H))
        gradient(c, 0, JOIST_Y, W, DIRT_Y - JOIST_Y, (40, 30, 34), (20, 16, 22), steps=5)
        rect(c, 0, 0, W, JOIST_Y, (20, 14, 18))
        d = ImageDraw.Draw(c)
        # floorboards underside
        rect(c, 0, JOIST_Y - 16, W, 16, (96, 64, 44))
        for x in range(0, W, 26):
            d.line([(x, JOIST_Y - 16), (x, JOIST_Y - 1)], fill=(60, 38, 28))
            d.line([(x + 1, JOIST_Y - 16), (x + 1, JOIST_Y - 1)], fill=(120, 84, 58))
        # joists (beams running into depth, seen end-on as blocks) + a long beam
        rect(c, 0, JOIST_Y, W, 5, (76, 50, 36))
        rect(c, 0, JOIST_Y + 5, W, 1, (40, 26, 20))
        rect(c, 0, JOIST_Y, W, 1, (130, 92, 64))
        # posts on foundation stones
        for x in (40, 206, 352):
            rect(c, x - 4, JOIST_Y + 6, 8, DIRT_Y - JOIST_Y - 8, (70, 46, 34))
            rect(c, x - 4, JOIST_Y + 6, 2, DIRT_Y - JOIST_Y - 8, (104, 70, 50))
            d.polygon([(x - 8, DIRT_Y + 1), (x - 6, DIRT_Y - 4), (x + 6, DIRT_Y - 4), (x + 8, DIRT_Y + 1)],
                      fill=(110, 108, 110), outline=INK)
        # dirt
        rect(c, 0, DIRT_Y, W, H - DIRT_Y, (74, 56, 44))
        r = rng("dirt")
        for _ in range(160):
            x, y = r.randrange(W), r.randrange(DIRT_Y + 1, H)
            pset(c, x, y, (96, 74, 58) if r.random() < 0.6 else (56, 42, 34))
        rect(c, 0, DIRT_Y, W, 1, (100, 80, 62))
        # cobwebs in the corners
        for (cx0, sgn) in ((0, 1), (W - 1, -1)):
            for k in range(4):
                d.line([(cx0, JOIST_Y + 6), (cx0 + sgn * (6 + k * 5), JOIST_Y + 6 + (18 - k * 4))],
                       fill=(120, 116, 124))
            for rr_ in (6, 11, 16):
                pts = [(cx0 + sgn * rr_ * math.sin(a), JOIST_Y + 6 + rr_ * math.cos(a))
                       for a in np.linspace(0.1, 1.45, 5)]
                d.line(pts, fill=(100, 96, 106))
        return c
    img.paste(cached("crawl", mk))
    # light leaking through the floorboard gaps (thin shafts + dust motes)
    d = ImageDraw.Draw(img)
    for i, gx in enumerate(gap_xs):
        fl = 0.8 + 0.2 * math.sin(t * 3 + i)
        col = mix((40, 30, 34), (255, 230, 170), 0.35 * fl)
        for yy in range(JOIST_Y - 16, DIRT_Y, 2):
            xx = gx + (yy - JOIST_Y) * 0.35
            pset(img, xx, yy, col)
        d.line([(gx - 1, JOIST_Y - 16), (gx - 1, JOIST_Y - 1)], fill=(255, 236, 180))
    for i in range(18):
        r = rng("mote", i)
        gx = gap_xs[i % len(gap_xs)]
        yy = JOIST_Y + ((t * r.uniform(3, 7) + r.uniform(0, 40)) % 40)
        xx = gx + (yy - JOIST_Y) * 0.35 + wave(t, 0.3, 2, r.random())
        if (step_frame(t, 6) + i) % 4:
            pset(img, xx, yy, (255, 240, 200))


def teacup(img, x, y, t, steam=True):
    d = ImageDraw.Draw(img)
    d.rectangle([x - 3, y - 5, x + 2, y - 1], fill=(120, 150, 110), outline=INK)
    d.line([(x - 2, y - 4), (x + 1, y - 4)], fill=(170, 200, 150))
    if steam:
        f = step_frame(t, 6)
        for i in range(2):
            ph = (f + i * 3) % 6
            pset(img, x - 1 + i * 2 + (1 if ph % 2 else 0), y - 7 - ph, (240, 240, 250))


def sweat(img, x, y, s=1, col=(140, 210, 255)):
    d = ImageDraw.Draw(img)
    d.polygon([(x, y - 3 * s), (x - 2 * s, y + s), (x + 2 * s, y + s)], fill=col, outline=INK)
    d.ellipse([x - 2 * s, y - s, x + 2 * s, y + 2 * s], fill=col, outline=INK)
    pset(img, x - s, y, (255, 255, 255))


def heart(img, x, y, col=(236, 56, 90), broken=False):
    pts = ((0, 0), (2, 0), (4, 0), (6, 0), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1),
           (-1, 2), (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2),
           (0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3),
           (1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (2, 5), (3, 5), (4, 5), (3, 6))
    for dx, dy in pts:
        if broken and dx == 3 - (dy % 2):
            continue
        ox = (-1 if dx < 3 else 1) if broken else 0
        pset(img, x + dx + ox, y + dy, col)
    pset(img, x + 1, y + 1, (255, 170, 190))


def naginata_line(img, p_top, p_tip, blade=14):
    """Page-level naginata shaft from p_top down to p_tip (screen space)."""
    from engine.gfx import stamp_line
    x0, y0 = p_top
    x1, y1 = p_tip
    L = math.hypot(x1 - x0, y1 - y0) or 1
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    bx, by = x1 - ux * blade, y1 - uy * blade
    stamp_line(img, (x0, y0), (bx, by), 6, INK)
    stamp_line(img, (bx, by), (x1, y1), 8, INK)
    stamp_line(img, (x0, y0), (bx, by), 4, (150, 96, 60))
    stamp_line(img, (x0 + 1, y0), (bx + 1, by), 1, (196, 140, 90))
    # blade: wide silver with a bright edge
    stamp_line(img, (bx, by), (x1, y1 - 1), 6, (200, 210, 228))
    stamp_line(img, (bx - 1, by), (x1 - 1, y1 - 3), 2, (255, 255, 255))
    stamp_line(img, (bx - 5, by), (bx + 5, by), 3, INK)
    stamp_line(img, (bx - 4, by), (bx + 4, by), 1, (200, 170, 80))
