"""Private helpers for s08 真选组动乱篇 (owned by the s08 scene agent).

* traitor grunts: Shinsengumi rebels of Ito's faction (uniform + white hachimaki)
  -- a local SSGDef (NOT registered in chars), drawn through draw_fig(img, 'grunt', ...)
* draw_fig(): draw_char with extras (silhouette + rim light, glow outline, tint)
* aura(): rising flame-particle aura (cursed purple / awakened blue)
* train carriage / locomotive / police car sprites (cached) + animated parts
* static backgrounds for the HQ room, Ito's moon room and the sunset field
Everything is a pure function of its arguments (deterministic, rng keyed).
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import W, H, rng, wave, step_frame, clamp, lerp, ease_out
from engine.gfx import INK, rect, pset, shade, mix, flip_h, set_alpha, tint, stamp_line, overlay_rect
from engine.text import text_sprite
from chars import render_sprite
from chars.hijikata import SSGDef, SSG_BODY, sheathed_katana, mk_head
from bg import common as C

_CACHE = {}


def cached(key, fn):
    v = _CACHE.get(key)
    if v is None:
        v = fn()
        _CACHE[key] = v
    return v


# ============================================================ traitor grunts
_G_BASE = [
    "......oooooo......",   # 0
    "....ooHHHhhhoo....",   # 1
    "...oHHHhhhhhhhoo..",   # 2
    "..oHHhhhhhhhhhhho.",   # 3
    ".oHhhhhhhhhhhhhhdo",   # 4
    "ohHhhhhhhhhhhhhhdo",   # 5
    "oWWWWWWWWWWWWWWWwo",   # 6  white hachimaki (rebels' headband)
    "owwwwwwwwwwwwRRRwo",   # 7  red emblem on the front
    "odhhhhhhhhhhShhhdo",   # 8
    "odhhhhShhhhSSShhdo",   # 9
    "odhSooSShhSSooShdo",   # 10 angry V brows
    "odhSSSoSSSSoSSSSho",   # 11
    ".ohSSEESSSSEESSSo.",   # 12 glaring slit eyes
    ".ohSSSSSSSSSSSSso.",   # 13
    "..osSSSSSmmmSSSo..",   # 14 frown
    "...oosSSSSSSSsoo..",   # 15
    ".....ooooooooo....",   # 16
]


def _gh(**rows):
    return mk_head(_G_BASE, **rows)


G_HEADS = {
    "normal": _gh(),
    "angry": _gh(),
    "blink": _gh(r12=".ohSSooSSSSooSSSo."),
    "talk": _gh(r14="..osSSSSSSooSSSo..", r15="...oosSSSSmmSsoo.."),
    "shout": _gh(r13=".ohSSSSSSSoooSSso.", r14="..osSSSSSSomoSSo..", r15="...oosSSSSooSsoo.."),
    "shock": _gh(r10="odhSSSSShhSSSSShdo", r11="odhSSSSSSSSSSSSSho",
                 r12=".ohSowoSSSSowoSSo.", r14="..osSSSSSSooSSSo.."),
    "hurt": _gh(r10="odhSSSSShhSSSSShdo", r11="odhSoSoSSSSoSoSSho", r12=".ohSSoSSSSSSoSSSo.",
                r13=".ohSoSoSSSSoSoSso.", r14="..osSSSSSSooSSSo.."),
    "happy": _gh(r12=".ohSSooSSSSooSSSo.", r14="..osSSSSSmmmmSSo.."),
}
G_EYE = (40, 30, 44)
_G_HAIR = [((96, 90, 110), (58, 54, 70), (38, 34, 48)),
           ((150, 110, 84), (104, 72, 52), (72, 48, 36)),
           ((126, 84, 84), (86, 50, 52), (60, 34, 38)),
           ((150, 150, 160), (104, 104, 116), (74, 74, 86))]


def _grunt_def(v):
    hl, hm, hd = _G_HAIR[v]
    pal = {"o": INK, "H": hl, "h": hm, "d": hd, "S": (250, 212, 180), "s": (226, 164, 134),
           "W": (244, 244, 250), "w": (190, 192, 210), "R": (214, 44, 56), "E": G_EYE,
           "m": (150, 60, 70)}
    return SSGDef(id=f"s08_grunt{v}", name="叛徒", color=(120, 60, 70), voice=0.8,
                  heads=G_HEADS, head_pal=pal, **SSG_BODY, sheathed=sheathed_katana,
                  desc="伊东派的叛变队士")


GRUNTS = [_grunt_def(v) for v in range(4)]


# ============================================================ sprite helpers
def _dilate(mask, r):
    h, w = mask.shape
    out = np.zeros((h + 2 * r, w + 2 * r), bool)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r + 1:
                out[r + dy:r + dy + h, r + dx:r + dx + w] |= mask
    return out


def glow_of(spr, color, r=2, color2=None):
    """RGBA glow ring (r px) around the sprite's opaque pixels; returns (img, r)."""
    a = np.asarray(spr)[..., 3] > 0
    outer = _dilate(a, r)
    out = np.zeros(outer.shape + (4,), np.uint8)
    out[outer] = tuple(color[:3]) + (255,)
    if color2 is not None and r > 1:
        inner = np.pad(_dilate(a, r - 1), 1)
        out[inner] = tuple(color2[:3]) + (255,)
    return Image.fromarray(out, "RGBA")


def sil_rim(spr, dark, rim=None, side=1, keep=None, top=True):
    """Silhouette in `dark` with a 1px rim light on the edges facing `side`
    (+1 = light from the right). keep={rgb: new_rgb} keeps/recolours pixels
    (e.g. glowing eyes)."""
    a = np.asarray(spr).copy()
    al = a[..., 3] > 0
    km = np.zeros_like(al)
    rep = []
    if keep:
        for src, dst in keep.items():
            m = al & (a[..., 0] == src[0]) & (a[..., 1] == src[1]) & (a[..., 2] == src[2])
            km |= m
            rep.append((m, dst))
    a[al, 0], a[al, 1], a[al, 2] = dark[0], dark[1], dark[2]
    if rim is not None:
        nb = np.zeros_like(al)
        if side > 0:
            nb[:, :-1] = al[:, 1:]
        else:
            nb[:, 1:] = al[:, :-1]
        edge = al & ~nb
        if top:
            up = np.zeros_like(al)
            up[1:, :] = al[:-1, :]
            edge |= al & ~up
        a[edge, 0], a[edge, 1], a[edge, 2] = rim[0], rim[1], rim[2]
    for m, dst in rep:
        a[m, 0], a[m, 1], a[m, 2] = dst[0], dst[1], dst[2]
    return Image.fromarray(a, "RGBA")


def fig_sprite(who, pose="idle", t=0.0, p=None, expr=None, facing=1, flash=0.0,
               flash_color=(255, 255, 255), rot=0, variant=0, **kw):
    """(sprite, ax, ay) for a registered character id or 'grunt'."""
    if who == "grunt":
        d = GRUNTS[variant % len(GRUNTS)]
        spr, ax, ay = d.render(pose, t, p, expr, **kw)
        if rot:
            spr = spr.rotate(rot, resample=Image.NEAREST, center=(ax, ay - 14))
        if facing < 0:
            spr = flip_h(spr)
            ax = spr.width - 1 - ax
        if flash > 0:
            spr = tint(spr, flash_color, clamp(flash))
        return spr, ax, ay
    return render_sprite(who, pose, t, p, expr, facing, flash, flash_color, 1.0, 1, rot, **kw)


def draw_fig(img, who, x, y, pose="idle", t=0.0, p=None, expr=None, facing=1, flash=0.0,
             flash_color=(255, 255, 255), alpha=1.0, rot=0, shadow=True, sil=None, rim=None,
             rim_side=1, keep=None, glow=None, tint_c=None, variant=0, **kw):
    """draw_char + extras. glow=(color, r[, inner]); tint_c=(color, amount);
    sil=dark colour -> silhouette (rim light colour `rim` from side `rim_side`)."""
    spr, ax, ay = fig_sprite(who, pose, t, p, expr, facing, flash, flash_color, rot, variant, **kw)
    if tint_c:
        spr = tint(spr, tint_c[0], tint_c[1])
    if sil is not None:
        spr = sil_rim(spr, sil, rim, rim_side, keep)
    if alpha < 1:
        spr = set_alpha(spr, alpha)
    px, py = int(round(x)) - ax, int(round(y)) - ay
    if glow is not None:
        r = glow[1]
        g = glow_of(spr, glow[0], r, glow[2] if len(glow) > 2 else None)
        img.paste(g, (px - r, py - r), g)
    if shadow and alpha > 0.3 and not rot:
        overlay_rect(img, int(round(x)) - 6, int(round(y)) - 1, 12, 2, (0, 0, 0), 0.25)
    img.paste(spr, (px, py), spr)
    return px, py, spr


def aura(img, t, cx, fy, w=24, h=44, cols=((255, 255, 255),), n=46, seed=0, speed=1.7,
         front=False):
    """Rising flame-streak aura around a character standing with feet at (cx, fy).
    front=True draws only the thinner front half (call once behind, once in front)."""
    d = ImageDraw.Draw(img)
    for i in range(n):
        if front and i % 3:
            continue
        r = rng("aura8", seed, i)
        sp = speed * r.uniform(0.7, 1.4)
        ph = (t * sp + r.random()) % 1.0
        if front and ph > 0.3:          # in front of the body: only the low flames (keep the face clear)
            continue
        side = r.uniform(-1, 1)
        x = cx + side * w * 0.5 * (1 - 0.55 * ph) + math.sin(t * 7 + i * 1.3) * 1.2 * ph
        y = fy + 2 - ph * h * r.uniform(0.55, 1.0)
        L = int(2 + (1 - ph) * 5)
        c = cols[min(len(cols) - 1, int(ph * len(cols)))]
        d.line([(int(x), int(y)), (int(x), int(y) + L)], fill=tuple(c))
        if i % 4 == 0 and ph < 0.6:
            d.point((int(x) + 1, int(y) + 1), fill=tuple(c))


def glint_star(img, x, y, s, col=(255, 255, 255)):
    """Big 4-point anime glint (s = arm length)."""
    x, y = int(x), int(y)
    d = ImageDraw.Draw(img)
    d.polygon([(x - s, y), (x - 1, y - 1), (x, y - s), (x + 1, y - 1), (x + s, y), (x + 1, y + 1),
               (x, y + s), (x - 1, y + 1)], fill=col)
    if s > 4:
        d.line([(x - s // 2, y - s // 2), (x + s // 2, y + s // 2)], fill=col)
        d.line([(x - s // 2, y + s // 2), (x + s // 2, y - s // 2)], fill=col)


# ============================================================ train
CAR_W = 240
CAR_H = 72
CUT_Y = 42              # local row where Okita's slash cuts the carriage
ROOF_Y = 4              # local row of the roof top
WIN_Y0, WIN_Y1 = 16, 38
WIN_XS = [30 + 24 * i for i in range(8)]
WIN_W = 20

T_BODY, T_BODY_L, T_BODY_D = (64, 104, 106), (94, 138, 134), (42, 72, 80)
T_CREAM, T_CREAM_D = (236, 222, 178), (196, 178, 132)
T_ROOF, T_ROOF_L, T_ROOF_D = (118, 114, 130), (156, 152, 166), (82, 78, 96)
T_FRAME, T_UNDER = (34, 40, 52), (32, 30, 40)


def _carriage():
    im = Image.new("RGBA", (CAR_W, CAR_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, x1 = 0, CAR_W - 1
    # roof vents
    for vx in (44, 112, 180):
        d.rectangle([vx - 1, 0, vx + 14, ROOF_Y], fill=INK)
        d.rectangle([vx, 1, vx + 13, ROOF_Y], fill=T_ROOF)
        d.line([(vx, 1), (vx + 13, 1)], fill=T_ROOF_L)
    # roof (rounded ends)
    d.rectangle([x0 + 4, ROOF_Y, x1 - 4, ROOF_Y + 6], fill=INK)
    d.rectangle([x0 + 1, ROOF_Y + 2, x1 - 1, ROOF_Y + 7], fill=INK)
    d.rectangle([x0 + 5, ROOF_Y + 1, x1 - 5, ROOF_Y + 2], fill=T_ROOF_L)
    d.rectangle([x0 + 2, ROOF_Y + 3, x1 - 2, ROOF_Y + 4], fill=T_ROOF)
    d.rectangle([x0 + 2, ROOF_Y + 5, x1 - 2, ROOF_Y + 5], fill=T_ROOF_D)
    d.rectangle([x0, ROOF_Y + 6, x1, ROOF_Y + 7], fill=T_FRAME)
    # body
    top = ROOF_Y + 8
    d.rectangle([x0, top, x1, 64], fill=INK)
    d.rectangle([x0 + 1, top, x1 - 1, 63], fill=T_BODY)
    d.line([(x0 + 1, top), (x1 - 1, top)], fill=T_BODY_L)
    d.line([(x0 + 1, top), (x0 + 1, 63)], fill=T_BODY_L)
    d.line([(x1 - 1, top), (x1 - 1, 63)], fill=T_BODY_D)
    # cream belt right under the cut line + thin one under the roof
    d.rectangle([x0 + 1, CUT_Y, x1 - 1, CUT_Y + 3], fill=T_CREAM)
    d.line([(x0 + 1, CUT_Y + 3), (x1 - 1, CUT_Y + 3)], fill=T_CREAM_D)
    d.line([(x0 + 1, top + 2), (x1 - 1, top + 2)], fill=T_CREAM_D)
    # lower-body shading + rivets
    d.rectangle([x0 + 1, 60, x1 - 1, 63], fill=T_BODY_D)
    for rx in range(6, CAR_W - 6, 8):
        im.putpixel((rx, CUT_Y + 6), (120, 160, 150, 255))
    # windows (holes with glass glare)
    for wx in WIN_XS:
        d.rectangle([wx - 1, WIN_Y0 - 1, wx + WIN_W, WIN_Y1 + 1], fill=INK)
        d.rectangle([wx, WIN_Y0, wx + WIN_W - 1, WIN_Y1], fill=T_FRAME)
        d.rectangle([wx + 1, WIN_Y0 + 1, wx + WIN_W - 2, WIN_Y1 - 2], fill=(0, 0, 0, 0))
        d.line([(wx + 1, WIN_Y1 - 1), (wx + WIN_W - 2, WIN_Y1 - 1)], fill=(150, 150, 160))
        for k in range(5):
            im.putpixel((wx + 3 + k, WIN_Y0 + 8 - k), (255, 255, 255, 110))
            im.putpixel((wx + 5 + k, WIN_Y0 + 8 - k), (255, 255, 255, 60))
    # doors at both ends
    for dx in (5, CAR_W - 22):
        d.rectangle([dx, top + 3, dx + 16, 62], outline=INK)
        d.rectangle([dx + 1, top + 4, dx + 15, 61], fill=T_BODY_D)
        d.rectangle([dx + 1, CUT_Y, dx + 15, CUT_Y + 3], fill=T_CREAM_D)
        d.rectangle([dx + 3, WIN_Y0, dx + 13, WIN_Y0 + 14], fill=INK)
        d.rectangle([dx + 4, WIN_Y0 + 1, dx + 12, WIN_Y0 + 13], fill=(0, 0, 0, 0))
        d.line([(dx + 8, top + 4), (dx + 8, 61)], fill=INK)
    # line name plate
    ts = text_sprite("江户铁道", (250, 238, 200), 12, outline=None)
    im.alpha_composite(ts, (CAR_W // 2 - ts.width // 2, CUT_Y + 6))
    # underframe + equipment boxes
    d.rectangle([x0 + 8, 64, x1 - 8, 67], fill=T_UNDER)
    for ex, ew in ((70, 30), (130, 22), (160, 14)):
        d.rectangle([ex, 66, ex + ew, 70], fill=INK)
        d.rectangle([ex + 1, 66, ex + ew - 1, 69], fill=(52, 50, 62))
    return im


def carriage_sprite():
    return cached("carriage", _carriage)


def carriage_parts():
    def mk():
        c = carriage_sprite()
        return c.crop((0, 0, CAR_W, CUT_Y)), c.crop((0, CUT_Y, CAR_W, CAR_H))
    return cached("carriage_parts", mk)


def _interior(lit_people=False, seed=0):
    """What you see through the windows: warm-lit far wall, far windows with the
    dusk sky, lamps, hand straps, seat backs (+ optional passenger silhouettes)."""
    h = CUT_Y - ROOF_Y - 8 + 2
    im = Image.new("RGBA", (CAR_W - 2, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, CAR_W, h], fill=(206, 150, 98))
    d.rectangle([0, 0, CAR_W, 2], fill=(150, 104, 72))
    for fx in range(10, CAR_W, 24):
        d.rectangle([fx, 6, fx + 16, 18], fill=(250, 186, 140))
        d.rectangle([fx, 12, fx + 16, 18], fill=(236, 150, 120))
        d.rectangle([fx - 1, 5, fx + 17, 5], fill=(120, 80, 60))
        d.rectangle([fx + 3, 2, fx + 8, 2], fill=(255, 250, 220))    # ceiling lamp
    for sx in range(4, CAR_W, 12):
        d.line([(sx, 2), (sx, 6)], fill=(90, 70, 60))
        d.rectangle([sx - 1, 7, sx + 1, 9], outline=(90, 70, 60))
    d.rectangle([0, h - 8, CAR_W, h], fill=(150, 56, 58))
    d.line([(0, h - 8), (CAR_W, h - 8)], fill=(190, 90, 80))
    if lit_people:
        r = rng("interior_ppl", seed)
        for px in range(14, CAR_W - 14, 13):
            if r.random() < 0.55:
                hy = h - 12 - r.randint(0, 3)
                d.ellipse([px - 4, hy - 5, px + 4, hy + 3], fill=(70, 50, 56))
                d.rectangle([px - 5, hy + 2, px + 5, h], fill=(70, 50, 56))
    return im


def interior_sprite(people=False, seed=0):
    return cached(("interior", people, seed), lambda: _interior(people, seed))


def full_lit_carriage(seed=0):
    """Opaque carriage with passengers' silhouettes behind lit windows (bg trains)."""
    def mk():
        c = carriage_sprite()
        out = Image.new("RGBA", c.size, (0, 0, 0, 0))
        out.alpha_composite(interior_sprite(True, seed), (1, ROOF_Y + 8))
        out.alpha_composite(c)
        return out
    return cached(("full_lit", seed), mk)


def bogies(img, x, y, t, speed=1.0):
    """Two bogies under a carriage whose left edge is at screen x and bottom row
    (local CAR_H) at y. Wheels spin (12 fps)."""
    ang = step_frame(t, 12) * 0.9 * speed
    for bx in (38, CAR_W - 38):
        cx = x + bx
        rect(img, cx - 16, y - 7, 32, 5, INK)
        rect(img, cx - 15, y - 6, 30, 3, (58, 56, 66))
        for wx in (-9, 9):
            wcx, wcy = cx + wx, y - 1
            d = ImageDraw.Draw(img)
            d.ellipse([wcx - 5, wcy - 5, wcx + 5, wcy + 5], fill=INK)
            d.ellipse([wcx - 4, wcy - 4, wcx + 4, wcy + 4], fill=(96, 92, 104))
            d.ellipse([wcx - 2, wcy - 2, wcx + 2, wcy + 2], fill=(60, 58, 70))
            a = ang + wx
            d.line([(wcx - math.cos(a) * 4, wcy - math.sin(a) * 4),
                    (wcx + math.cos(a) * 4, wcy + math.sin(a) * 4)], fill=(150, 146, 160))


def _loco():
    """Locomotive (faces right): carriage body with a slanted nose, windscreen,
    headlight and a pantograph base."""
    Wl = 210
    im = Image.new("RGBA", (Wl, CAR_H), (0, 0, 0, 0))
    base = carriage_sprite().crop((0, 0, 170, CAR_H))
    im.alpha_composite(base, (0, 0))
    d = ImageDraw.Draw(im)
    top = ROOF_Y + 8
    # nose block
    nose = [(168, ROOF_Y), (186, ROOF_Y + 2), (206, top + 22), (208, 64), (168, 64)]
    d.polygon(nose, fill=INK)
    inner = [(168, ROOF_Y + 2), (185, ROOF_Y + 4), (204, top + 23), (206, 62), (168, 62)]
    d.polygon(inner, fill=T_BODY)
    d.polygon([(168, ROOF_Y + 2), (185, ROOF_Y + 4), (188, ROOF_Y + 8), (168, ROOF_Y + 8)], fill=T_ROOF)
    # windscreen
    d.polygon([(176, WIN_Y0 - 2), (190, WIN_Y0 - 2), (201, WIN_Y1 - 4), (176, WIN_Y1 - 4)], fill=INK)
    d.polygon([(177, WIN_Y0 - 1), (189, WIN_Y0 - 1), (199, WIN_Y1 - 5), (177, WIN_Y1 - 5)], fill=(60, 70, 96))
    d.line([(181, WIN_Y0 + 1), (186, WIN_Y0 + 8)], fill=(170, 190, 220))
    # driver silhouette
    d.ellipse([179, WIN_Y0 + 5, 187, WIN_Y0 + 13], fill=(30, 30, 44))
    d.rectangle([178, WIN_Y0 + 12, 189, WIN_Y1 - 5], fill=(30, 30, 44))
    # cream belt continues + red nose stripe
    d.polygon([(168, CUT_Y), (206, CUT_Y), (206, CUT_Y + 3), (168, CUT_Y + 3)], fill=T_CREAM)
    d.rectangle([188, CUT_Y + 8, 206, CUT_Y + 12], fill=(210, 60, 60))
    # headlight
    d.rectangle([199, CUT_Y + 14, 206, CUT_Y + 19], fill=INK)
    d.rectangle([200, CUT_Y + 15, 205, CUT_Y + 18], fill=(255, 246, 190))
    # underframe / cowcatcher
    d.rectangle([160, 64, 202, 67], fill=T_UNDER)
    d.polygon([(196, 62), (209, 62), (204, 69), (192, 69)], fill=INK)
    # pantograph base
    d.rectangle([90, ROOF_Y - 2, 118, ROOF_Y], fill=INK)
    return im


def loco_sprite():
    return cached("loco", _loco)


def pantograph(img, x, y_roof, y_wire, t):
    """Diamond pantograph from roof (x = centre) up to the catenary wire + sparks."""
    top = y_wire + 1
    mid = (y_roof + top) // 2
    for sgn in (-1, 1):
        stamp_line(img, (x + sgn * 10, y_roof - 1), (x + sgn * 4, mid), 1, INK)
        stamp_line(img, (x + sgn * 4, mid), (x + sgn * 8, top), 1, INK)
    rect(img, x - 10, top, 21, 1, (70, 70, 84))
    r = rng("panto", step_frame(t, 30))
    if r.random() < 0.6:
        sx = x + r.randint(-6, 6)
        for k in range(r.randint(2, 5)):
            pset(img, sx + r.randint(-3, 3), top - r.randint(0, 3), (255, 250, 200) if k % 2 else (150, 220, 255))


# ============================================================ police car
CAR_L = 168


def _police_car():
    L, Hc = CAR_L, 60
    im = Image.new("RGBA", (L, Hc), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    WHITE, WHITE_D = (236, 238, 244), (184, 188, 206)
    BLACK, BLACK_L = (34, 34, 46), (70, 72, 92)
    # greenhouse (roof + pillars) outline shape
    gh = [(40, 27), (52, 7), (122, 7), (140, 27)]
    d.polygon(gh, fill=INK)
    d.polygon([(42, 27), (53, 8), (121, 8), (138, 27)], fill=WHITE)
    # window holes: rear (46..90) and front (96..132)
    d.polygon([(47, 26), (55, 11), (89, 11), (89, 26)], fill=(0, 0, 0, 0))
    d.polygon([(95, 26), (95, 11), (119, 11), (133, 26)], fill=(0, 0, 0, 0))
    # light bar
    d.rectangle([72, 1, 98, 7], fill=INK)
    d.rectangle([73, 2, 84, 6], fill=(200, 40, 50))
    d.rectangle([86, 2, 97, 6], fill=(200, 40, 50))
    d.line([(73, 2), (97, 2)], fill=(255, 120, 120))
    # body
    body = [(4, 30), (36, 26), (146, 26), (164, 33), (166, 48), (2, 48)]
    d.polygon(body, fill=INK)
    d.polygon([(5, 31), (37, 27), (145, 27), (163, 34), (164, 41), (4, 41)], fill=WHITE)
    d.polygon([(4, 41), (164, 41), (165, 47), (3, 47)], fill=BLACK)
    d.line([(6, 42), (163, 42)], fill=BLACK_L)
    d.line([(38, 28), (144, 28)], fill=(255, 255, 255))
    d.line([(4, 40), (164, 40)], fill=WHITE_D)
    # doors
    for x in (50, 92, 136):
        d.line([(x, 27), (x, 46)], fill=INK)
    # door handles
    for x in (84, 128):
        d.rectangle([x, 31, x + 4, 32], fill=INK)
    # text on the rear door + a gold crest on the front door
    ts = text_sprite("真选组", (30, 30, 44), 12)
    bb = ts.getbbox()
    ts = ts.crop(bb)
    im.alpha_composite(ts, (54, 29))
    d.ellipse([106, 30, 114, 38], fill=INK)
    d.ellipse([107, 31, 113, 37], fill=(240, 196, 72))
    d.line([(110, 32), (110, 36)], fill=INK)
    # lights
    d.rectangle([160, 33, 165, 37], fill=INK)
    d.rectangle([161, 34, 164, 36], fill=(255, 244, 180))
    d.rectangle([3, 32, 7, 36], fill=INK)
    d.rectangle([4, 33, 6, 35], fill=(220, 40, 50))
    # bumpers
    d.rectangle([0, 43, 10, 47], fill=(120, 120, 136))
    d.rectangle([156, 43, 167, 47], fill=(120, 120, 136))
    # wheel arches
    for wx in (32, 134):
        d.pieslice([wx - 12, 38, wx + 12, 62], 180, 360, fill=(20, 18, 26))
    return im


def police_car_sprite():
    return cached("police_car", _police_car)


def car_wheels(img, x, y, t):
    """Car wheels for a car sprite drawn at (x, y) top-left."""
    ang = step_frame(t, 12) * 1.3
    d = ImageDraw.Draw(img)
    for wx in (32, 134):
        cx, cy = x + wx, y + 50
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=INK)
        d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(40, 40, 52))
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(170, 170, 186))
        for k in range(3):
            a = ang + k * 2.094
            d.line([(cx, cy), (cx + math.cos(a) * 4, cy + math.sin(a) * 4)], fill=(90, 90, 104))


def siren_glow(img, x, y, t):
    """Flashing red siren light with a halo (x, y = centre of the light bar)."""
    f = step_frame(t, 8, 4)
    col = [(255, 60, 60), (255, 200, 200), (255, 60, 60), (120, 30, 40)][f]
    on = f in (0, 1, 2)
    if on:
        g = C.glow_sprite(14 if f == 1 else 10, (255, 50, 60), 0.9)
        C.add_sprite(img, g, x - g.width // 2, y - g.height // 2)
    rect(img, x - 12, y - 2, 11, 5, col)
    rect(img, x + 1, y - 2, 11, 5, [(120, 30, 40), (255, 60, 60), (255, 200, 200), (255, 60, 60)][f])


# ============================================================ HQ room decor
def makoto_scroll(img, x, y, t):
    """Hanging scroll with 「诚」 (x = centre, y = top)."""
    def mk():
        s = Image.new("RGBA", (26, 52), (0, 0, 0, 0))
        d = ImageDraw.Draw(s)
        d.rectangle([0, 0, 25, 3], fill=INK)
        d.rectangle([1, 1, 24, 2], fill=(150, 110, 70))
        d.rectangle([2, 3, 23, 47], fill=INK)
        d.rectangle([3, 4, 22, 46], fill=(236, 226, 200))
        d.rectangle([3, 4, 22, 6], fill=(120, 60, 60))
        d.rectangle([3, 44, 22, 46], fill=(120, 60, 60))
        d.rectangle([0, 47, 25, 50], fill=INK)
        d.rectangle([1, 48, 24, 49], fill=(150, 110, 70))
        ts = text_sprite("诚", (30, 26, 40), 16, "kai")
        s.alpha_composite(ts, (13 - ts.width // 2, 25 - ts.height // 2))
        return s
    s = cached("scroll", mk)
    img.paste(s, (int(x) - 13, int(y)), s)


def andon(img, x, y, t, strength=1.0):
    """Floor paper lamp (x = centre, y = floor) with a flickering glow."""
    fl = 0.85 + 0.15 * math.sin(t * 13) * math.sin(t * 7.3)
    g = C.glow_sprite(26, (120, 80, 30), strength * fl)
    C.add_sprite(img, g, int(x) - g.width // 2, int(y) - 16 - g.height // 2)
    rect(img, x - 6, y - 26, 13, 26, INK)
    rect(img, x - 5, y - 24, 11, 21, (255, 226, 150))
    rect(img, x - 5, y - 24, 11, 2, (255, 246, 200))
    rect(img, x - 1, y - 24, 1, 21, (226, 180, 110))
    rect(img, x - 5, y - 3, 11, 3, (80, 50, 40))
    rect(img, x - 5, y - 26, 11, 2, (80, 50, 40))


# ============================================================ Ito's room
def ito_room_bg():
    """Dark room with a round moon window (maru-mado) and moonlight on the floor."""
    def mk():
        im = Image.new("RGB", (W, H), (26, 22, 44))
        d = ImageDraw.Draw(im)
        # wall with pillars
        im.paste(Image.fromarray(C.vgradient(150, W, [(0, (18, 16, 34)), (1, (40, 34, 64))]), "RGB"), (0, 0))
        for px in (20, 214, 360):
            d.rectangle([px, 0, px + 7, 150], fill=(22, 16, 26))
            d.line([(px, 0), (px, 150)], fill=(56, 44, 64))
        d.rectangle([0, 0, W, 8], fill=(16, 12, 22))
        d.rectangle([0, 146, W, 150], fill=(20, 14, 24))
        # moon window
        cx, cy, r = 112, 76, 46
        win = Image.new("RGB", (W, H), (0, 0, 0))
        C.sky(win, "night", 3.0, horizon=150, body=False)
        C.big_moon(win, cx + 10, cy - 8, 24)
        wd = ImageDraw.Draw(win)
        for k in range(-3, 4):          # lattice
            wd.line([(cx + k * 13, cy - r), (cx + k * 13, cy + r)], fill=(30, 22, 30))
        wd.line([(cx - r, cy + 14), (cx + r, cy + 14)], fill=(30, 22, 30))
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
        d.ellipse([cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5], fill=(14, 10, 18))
        d.ellipse([cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3], fill=(70, 50, 52))
        d.ellipse([cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1], fill=(30, 22, 28))
        im.paste(win, (0, 0), mask)
        # floor
        fl = Image.new("RGB", (W, H - 150))
        fl.paste(Image.fromarray(C.vgradient(H - 150, W, [(0, (54, 40, 52)), (1, (28, 22, 34))]), "RGB"))
        fd = ImageDraw.Draw(fl)
        for i in range(0, W, 32):
            fd.line([(i, 0), (i - 20, H - 150)], fill=(40, 30, 40))
        im.paste(fl, (0, 150))
        # moonlight shaft on the floor (dithered)
        a = np.asarray(im).astype(np.float32)
        yy, xx = np.mgrid[0:H, 0:W]
        shaft = (yy > 150) & (np.abs((xx - 112) - (yy - 150) * 1.1) < 34 + (yy - 150) * 0.6)
        dm = ((xx + yy) % 2 == 0)
        m = shaft & dm
        a[m] = a[m] * 0.55 + np.array([150, 160, 220]) * 0.45
        return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGB")
    return cached("ito_room", mk)


# ============================================================ sunset field
SUN_X, SUN_Y, SUN_R = 192, 134, 44
HORIZON_E = 150


def sunset_bg():
    """Static sunset: dramatic sky, huge striped sun, far ridges, train wreck."""
    def mk():
        im = Image.new("RGB", (W, H))
        sky = C.vgradient(HORIZON_E, W, [(0, (36, 18, 56)), (0.35, (120, 36, 70)),
                                          (0.7, (226, 84, 60)), (1, (255, 170, 80))], bands=12)
        im.paste(Image.fromarray(sky, "RGB"), (0, 0))
        d = ImageDraw.Draw(im)
        # sun halo + sun with retro stripes
        g = C.glow_sprite(90, (120, 60, 20), 0.9)
        C.add_sprite(im, g, SUN_X - g.width // 2, SUN_Y - g.height // 2)
        d.ellipse([SUN_X - SUN_R, SUN_Y - SUN_R, SUN_X + SUN_R, SUN_Y + SUN_R], fill=(255, 214, 120))
        d.ellipse([SUN_X - SUN_R + 6, SUN_Y - SUN_R + 4, SUN_X + SUN_R - 10, SUN_Y + 8], fill=(255, 236, 170))
        for i, y in enumerate(range(SUN_Y + 2, SUN_Y + SUN_R, 5)):
            d.rectangle([SUN_X - SUN_R, y, SUN_X + SUN_R, y + 1 + i // 2], fill=(255, 150, 70))
        # thin clouds across the sun
        for (cx, cy, w) in ((120, 98, 90), (270, 84, 110), (200, 112, 60), (330, 116, 60)):
            d.rectangle([cx - w // 2, cy, cx + w // 2, cy + 1], fill=(150, 50, 80))
            d.rectangle([cx - w // 2 + 8, cy + 2, cx + w // 2 - 12, cy + 2], fill=(180, 70, 80))
        # far ridges
        r = rng("ridge_e")
        pts = [(0, HORIZON_E)]
        for x in range(0, W + 16, 16):
            pts.append((x, HORIZON_E - 10 - int(8 * math.sin(x * 0.02) + r.uniform(0, 6))))
        pts.append((W, HORIZON_E))
        d.polygon(pts, fill=(90, 30, 60))
        pts = [(0, HORIZON_E)]
        for x in range(0, W + 12, 12):
            pts.append((x, HORIZON_E - 3 - int(4 * math.sin(x * 0.05 + 1) + r.uniform(0, 3))))
        pts.append((W, HORIZON_E))
        d.polygon(pts, fill=(60, 20, 46))
        # derailed train wreck on the right (silhouette)
        wreck = Image.new("RGBA", (130, 50), (0, 0, 0, 0))
        wd = ImageDraw.Draw(wreck)
        wd.rectangle([4, 14, 120, 40], fill=(44, 16, 36))
        wd.rectangle([8, 10, 116, 14], fill=(44, 16, 36))
        for k in range(6):
            wd.rectangle([14 + k * 17, 18, 24 + k * 17, 27], fill=(120, 44, 50))
        wk = wreck.rotate(-9, resample=Image.NEAREST, expand=True)
        im.paste(wk, (262, HORIZON_E - 48), wk)
        wk2 = wreck.rotate(14, resample=Image.NEAREST, expand=True)
        im.paste(wk2, (318, HORIZON_E - 46), wk2)
        # ground
        gr = C.vgradient(H - HORIZON_E, W, [(0, (48, 18, 38)), (1, (22, 10, 22))], bands=6)
        im.paste(Image.fromarray(gr, "RGB"), (0, HORIZON_E))
        # warm sun reflection streak on the ground
        for i, y in enumerate(range(HORIZON_E + 2, HORIZON_E + 20, 3)):
            w = 70 - i * 10
            d.rectangle([SUN_X - w // 2, y, SUN_X + w // 2, y], fill=(150, 60, 50))
        return im
    return cached("sunset", mk)


def grass_tips(img, t, y, cam=0.0, col=(28, 10, 24), seed=0, dens=3, hmax=7):
    """Wind-swept grass blades along row y (swaying toward the left)."""
    d = ImageDraw.Draw(img)
    for x in range(-4, W + 4, dens):
        r = rng("gt", seed, x)
        hh = r.randint(3, hmax)
        sway = math.sin(t * 5 + x * 0.21) * 1.5 - 2
        xx = x - cam
        d.line([(xx, y), (xx + sway, y - hh)], fill=col)


def wind_motes(img, t, count=40, seed=0, col=(255, 200, 140), area=(0, 30, W, 190), speed=160):
    """Dust / sparks blown right-to-left by the wind."""
    x0, y0, x1, y1 = area
    d = ImageDraw.Draw(img)
    for i in range(count):
        r = rng("mote", seed, i)
        sp = speed * r.uniform(0.6, 1.4)
        x = x1 - (r.uniform(0, x1 - x0) + t * sp) % (x1 - x0 + 20) + 10
        y = y0 + (r.uniform(0, y1 - y0) + math.sin(t * 2 + i) * 6) % (y1 - y0)
        if i % 3 == 0:
            d.line([(x, y), (x + 2, y)], fill=col)
        else:
            d.point((x, y), fill=col)


def sun_rays(img, t, n=6, col=(255, 214, 150), strength=0.35):
    """Soft god-rays fanning up from the sun (dithered, additive-ish blend)."""
    def mk(i):
        m = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(m)
        a = -2.55 + i * (1.9 / (n - 1))
        x1, y1 = SUN_X + math.cos(a) * 260, SUN_Y + math.sin(a) * 260
        d.polygon([(SUN_X, SUN_Y), (x1 - 16, y1), (x1 + 16, y1)], fill=255)
        arr = np.asarray(m) > 0
        yy, xx = np.mgrid[0:H, 0:W]
        dith = ((xx + yy) % 2 == 0) | ((xx % 2 == 0) & (yy % 2 == 0))
        return arr & dith
    a = np.asarray(img).astype(np.float32)
    for i in range(n):
        m = cached(("ray", i, n), lambda i=i: mk(i))
        k = strength * (0.6 + 0.4 * math.sin(t * 1.3 + i * 1.7))
        a[m] = a[m] * (1 - k) + np.array(col, np.float32) * k
    img.paste(Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGB"))
