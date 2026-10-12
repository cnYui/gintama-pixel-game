"""Private props for s03 「神乐与定春」 (owned by the s03 scene agent).

Gintoki's scooter, yakuza thugs (suit + sunglasses, built on the townsman head art),
rice bowls, the gama-guchi wallet + winged coins + moth, the 「请收养」 cardboard box,
sweat drops, a crow, dithered light cones. Every sprite is built once and cached.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import step_frame, clamp, lerp, rng, ANIM_FPS
from engine.gfx import INK, outline, flip_h, rect, pset, shade
from engine.text import draw_text
from chars.rig import ChibiDef
from chars import townsman as _tm

_CACHE = {}


def _cached(key, fn):
    s = _CACHE.get(key)
    if s is None:
        s = fn()
        _CACHE[key] = s
    return s


def paste_rgba(img, spr, x, y):
    img.paste(spr, (int(round(x)), int(round(y))), spr)


# ====================================================================== scooter
SC_W, SC_H = 42, 26          # sprite size; ground line = row SC_H-1
SC_SEAT = (-7, -16)          # rider feet-anchor offset from scooter bottom-centre (facing right)
SC_LIGHT = (17, -18)         # headlight offset from bottom-centre (facing right)
SC_BODY = (242, 238, 226)
SC_BODY_S = (206, 200, 196)
SC_BODY_D = (160, 156, 170)
SC_TRIM = (86, 132, 200)


def _scooter(frame):
    im = Image.new("RGBA", (SC_W, SC_H))
    d = ImageDraw.Draw(im)
    g = SC_H - 1
    body, bs, bd = SC_BODY + (255,), SC_BODY_S + (255,), SC_BODY_D + (255,)
    ink = INK + (255,)
    tire = (34, 30, 40, 255)
    metal = (176, 182, 196, 255)
    # wheels (spokes alternate per frame)
    for cx in (9, 32):
        cy = g - 4
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=tire)
        d.rectangle([cx - 1, cy - 1, cx + 1, cy + 1], fill=metal)
        if frame % 2:
            d.point((cx - 2, cy - 2), fill=(90, 90, 100, 255))
            d.point((cx + 2, cy + 2), fill=(90, 90, 100, 255))
        else:
            d.point((cx + 2, cy - 2), fill=(90, 90, 100, 255))
            d.point((cx - 2, cy + 2), fill=(90, 90, 100, 255))
    # rear cowl
    d.polygon([(2, 12), (5, 9), (18, 9), (21, 13), (21, 19), (4, 19), (2, 16)], fill=body)
    d.rectangle([4, 17, 21, 19], fill=bs)
    d.line([(4, 15), (20, 15)], fill=SC_TRIM + (255,))
    d.rectangle([2, 12, 3, 14], fill=(228, 59, 68, 255))          # tail light
    # seat
    d.rounded_rectangle([4, 6, 18, 9], radius=1, fill=(52, 44, 58, 255))
    d.line([(5, 6), (16, 6)], fill=(96, 88, 108, 255))
    # floorboard
    d.rectangle([18, 17, 27, 19], fill=bs)
    d.line([(18, 17), (27, 17)], fill=body)
    # front leg-shield + nose
    d.polygon([(25, 19), (23, 15), (26, 6), (29, 4), (32, 6), (33, 12), (32, 19)], fill=body)
    d.line([(26, 7), (24, 15)], fill=bs)
    d.line([(33, 12), (32, 18)], fill=bs)
    # front fender over the front wheel
    d.polygon([(27, 16), (36, 16), (38, 19), (27, 19)], fill=body)
    d.line([(28, 19), (37, 19)], fill=bd)
    # steering column + handlebar
    d.line([(29, 4), (28, 1)], fill=metal)
    d.line([(25, 1), (31, 1)], fill=metal)
    d.point((31, 1), fill=tire)
    d.point((32, 1), fill=tire)
    # headlight
    d.rectangle([32, 6, 34, 8], fill=(255, 240, 170, 255))
    d.point((33, 6), fill=(255, 255, 255, 255))
    # little mirror
    d.line([(26, 1), (25, -1)], fill=metal)
    im = outline(im)
    # internal ink seams (after outline, offset +1)
    d = ImageDraw.Draw(im)
    d.line([(6, 11), (19, 11)], fill=ink)          # seat bottom seam
    d.line([(24, 16), (26, 8)], fill=ink)          # shield seam
    return im


def scooter_sprite(frame=0, facing=1):
    spr = _cached(("scooter", frame % 2), lambda: _scooter(frame))
    if facing < 0:
        spr = _cached(("scooter_f", frame % 2), lambda: flip_h(_scooter(frame)))
    return spr


def draw_scooter(img, x, y, t, facing=1, moving=True, tilt=0):
    """Scooter with bottom-centre (ground) at (x, y)."""
    f = step_frame(t, 16) if moving else 0
    spr = scooter_sprite(f, facing)
    if tilt:
        spr = spr.rotate(tilt, resample=Image.NEAREST, expand=False, center=(spr.width // 2, spr.height - 2))
    bob = 1 if (moving and step_frame(t, 10) % 2) else 0
    paste_rgba(img, spr, x - spr.width // 2, y - spr.height + 1 - bob)
    return bob


def light_cone(img, pts, color, alpha):
    """Additive-looking translucent polygon (headlight beam / light pool)."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, y0 = max(0, int(min(xs))), max(0, int(min(ys)))
    x1, y1 = min(img.width, int(max(xs)) + 1), min(img.height, int(max(ys)) + 1)
    if x1 <= x0 or y1 <= y0:
        return
    mask = Image.new("L", (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(mask).polygon([(px - x0, py - y0) for px, py in pts], fill=int(255 * alpha))
    region = img.crop((x0, y0, x1, y1))
    a = np.asarray(region).astype(np.int16)
    m = np.asarray(mask).astype(np.int16)[..., None]
    c = np.array(color, np.int16)
    out = a + (c * m) // 255
    img.paste(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB"), (x0, y0))


# ====================================================================== yakuza
def _yk_heads():
    base = _tm._heads(_tm.SHORT)
    out = {}
    for e, art in base.items():
        rows = art.split("\n")
        rows[11] = "odhoooooSoooooSSho"
        rows[12] = ".ohoGGgoooGGgoSSo."
        if e == "hurt":
            rows[11] = "odhSSoooSSooooSSho"
            rows[12] = ".ohSoGgoSSoGGgoSo."
        out[e] = "\n".join(rows)
    return out


_YK_TORSO = """
....oooooo....
...oLKWWKKo...
..oLKKWrKKKo..
.oLKKKWrKKKko.
.oLKKKKrKKKko.
.oKKKKKKKKKko.
.oKKKKKKKKKko.
.okKKKKKKKKko.
.okKKKKKKKkko.
.okKKKKKKKkko.
.okkKKKKKkkko.
..oooooooooo..
"""

_YK_VARIANTS = [
    # hair, suit (K, k, L), shirt, tie, pants
    dict(hair=((70, 62, 78), (46, 40, 56), (30, 28, 40)), suit=((58, 56, 74), (38, 36, 50), (92, 90, 112)),
         shirt=(236, 236, 240), tie=(206, 40, 52), pants=(44, 42, 56)),
    dict(hair=((150, 96, 58), (116, 70, 44), (84, 50, 34)), suit=((224, 222, 228), (176, 174, 190), (250, 250, 252)),
         shirt=(40, 36, 52), tie=(230, 190, 60), pants=(190, 188, 200)),
    dict(hair=((64, 58, 74), (44, 40, 54), (30, 28, 40)), suit=((96, 60, 110), (70, 40, 84), (130, 90, 146)),
         shirt=(236, 236, 240), tie=(40, 36, 52), pants=(60, 40, 72)),
]


def _yk_def(i):
    v = _YK_VARIANTS[i]
    hp = _tm._head_pal(v["hair"])
    hp["G"] = (28, 28, 42)
    hp["g"] = (130, 140, 190)
    K, k, L = v["suit"]
    tp = {"o": INK, "K": K, "k": k, "L": L, "W": v["shirt"], "r": v["tie"]}
    return ChibiDef(
        id=f"_yakuza{i}", name="黑帮", color=(80, 80, 100),
        heads=_yk_heads(), head_pal=hp, torso=_YK_TORSO, torso_pal=tp,
        neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
        arm_len=7, arm_w=2, sleeve_f=K, sleeve_b=k, sleeve_frac=0.75, hand=(255, 214, 180),
        leg_len=7, leg_w=3, leg_gap=4, pants=v["pants"], shoes=(24, 20, 30), shoe_h=1,
        weapon="katana", weapon_len=13, sheathed=None)


YAKUZA = [_yk_def(i) for i in range(len(_YK_VARIANTS))]


def draw_def(img, d, x, y, pose="idle", t=0.0, p=None, expr=None, facing=1, flash=0.0, rot=0, **kw):
    """draw_char() for an unregistered ChibiDef (feet at x, y)."""
    spr, ax, ay = d.render(pose=pose, t=t, p=p, expr=expr, **kw)
    if rot:
        spr = spr.rotate(rot, resample=Image.NEAREST, center=(ax, ay - 14))
    if facing < 0:
        spr = flip_h(spr)
        ax = spr.width - 1 - ax
    if flash > 0:
        a = np.asarray(spr).astype(np.float32)
        a[..., :3] = a[..., :3] * (1 - flash) + 255 * flash
        spr = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
    x, y = int(round(x)), int(round(y))
    from engine.gfx import overlay_rect
    if rot == 0:
        overlay_rect(img, x - 6, y - 1, 12, 2, (0, 0, 0), 0.25)
    img.paste(spr, (x - ax, y - ay), spr)


# ====================================================================== rice bowls
BOWL_W, BOWL_H = 13, 7


def _bowl(rice):
    im = Image.new("RGBA", (BOWL_W, BOWL_H))
    d = ImageDraw.Draw(im)
    white, sh, blue = (240, 240, 246, 255), (196, 200, 218, 255), (70, 108, 190, 255)
    d.rectangle([1, 1, 11, 1], fill=INK + (255,))
    d.rectangle([0, 2, 12, 3], fill=INK + (255,))
    d.rectangle([1, 2, 11, 2], fill=(250, 250, 255, 255) if rice else (120, 110, 120, 255))
    d.rectangle([1, 3, 11, 3], fill=white)
    d.rectangle([1, 4, 11, 4], fill=blue)
    d.rectangle([2, 5, 10, 5], fill=sh)
    d.point((0, 4), fill=INK + (255,))
    d.point((12, 4), fill=INK + (255,))
    d.point((1, 5), fill=INK + (255,))
    d.point((11, 5), fill=INK + (255,))
    d.rectangle([3, 6, 9, 6], fill=INK + (255,))
    d.point((3, 3), fill=(255, 255, 255, 255))
    if rice:
        d.rectangle([3, 0, 9, 1], fill=(250, 250, 255, 255))
        d.line([(3, 0), (9, 0)], fill=INK + (255,))
        d.point((2, 1), fill=INK + (255,))
        d.point((10, 1), fill=INK + (255,))
    return im


def bowl_sprite(rice=False):
    return _cached(("bowl", rice), lambda: _bowl(rice))


def small_bowl_sprite():
    """7x5 bowl heaped with rice (held in a hand)."""
    def mk():
        im = Image.new("RGBA", (9, 7))
        d = ImageDraw.Draw(im)
        d.rectangle([2, 0, 6, 2], fill=INK + (255,))
        d.rectangle([3, 1, 5, 2], fill=(255, 255, 255, 255))
        d.rectangle([0, 3, 8, 4], fill=INK + (255,))
        d.rectangle([1, 3, 7, 3], fill=(255, 255, 255, 255))
        d.rectangle([1, 4, 7, 4], fill=(70, 108, 190, 255))
        d.rectangle([2, 5, 6, 5], fill=(214, 216, 232, 255))
        d.point((1, 5), fill=INK + (255,))
        d.point((7, 5), fill=INK + (255,))
        d.rectangle([2, 6, 6, 6], fill=INK + (255,))
        return im
    return _cached("smallbowl", mk)


# ====================================================================== wallet / coins / moth
_WALLET_PAL = {"o": INK, "B": (98, 150, 90), "b": (146, 196, 124), "d": (64, 104, 66), "G": (70, 118, 72),
               "Y": (242, 204, 84), "y": (190, 146, 50), "w": (255, 250, 210), "K": (34, 26, 32),
               "k": (70, 54, 60), "R": (200, 60, 70)}
# gama-guchi (kiss-lock) purse: brass frame with two ball clasps on a frog-green pouch
_WALLET_CLOSED = """
......oo.oo......
.....owYowYo.....
.....oYyoYyo.....
..oooooyoyooooo..
.owYYYYYYYYYYYyo.
.oyyyyyyyyyyyyyo.
oBbbBBBBBBBBBBBdo
oBbBBBBBGBBBBBBdo
oBbBBBBBBBBBBBBdo
oBBBBGBBBBBBGBBdo
oBBBBBBBBBBBBBddo
.oBBBBBBBBBBBBdo.
..oBBBBBBBBBBdo..
...ooooooooooo...
"""
_WALLET_OPEN = """
.oo...........oo.
owYo.........owYo
oYyo.........oYyo
.oyoooooooooooyo.
.owYYYYYYYYYYYyo.
.oyyyyyyyyyyyyyo.
okkkkkkkkkkkkkkko
oKKKKKKKKKKKKKKKo
oKKKKKKKKKKKKKKKo
owYYYYYYYYYYYYYyo
oyyyyyyyyyyyyyyyo
oBbbBBBBBBBBBBBdo
oBbBBBBGBBBBBBBdo
oBBBBBBBBBBBBGBdo
.oBBBBBBBBBBBBdo.
..oBBBBBBBBBBdo..
...ooooooooooo...
"""


def wallet_sprite(opened):
    """Gama-guchi (kiss-lock) purse, 15 px wide; bottom row = 'hand' line."""
    from engine.gfx import ascii_sprite
    return _cached(("wallet", opened),
                   lambda: ascii_sprite(_WALLET_OPEN if opened else _WALLET_CLOSED, _WALLET_PAL))


def draw_coin(img, x, y, t, seed=0):
    """Gold coin with flapping white wings (money flying away)."""
    x, y = int(round(x)), int(round(y))
    f = step_frame(t + seed * 0.05, 10, 2)
    d = ImageDraw.Draw(img)
    wing, wing_d = (252, 252, 255), (200, 208, 232)
    for sgn in (-1, 1):                       # wings: up-stroke / down-stroke
        wx = x + sgn * 4
        if f:
            pts = [(wx, y - 1), (wx + sgn * 5, y - 6), (wx + sgn * 6, y - 3), (wx + sgn * 2, y + 1)]
        else:
            pts = [(wx, y - 1), (wx + sgn * 6, y + 1), (wx + sgn * 4, y + 4), (wx, y + 2)]
        d.polygon(pts, fill=wing, outline=INK)
        pset(img, wx + sgn * 3, y + (-3 if f else 2), wing_d)
    d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(238, 190, 60), outline=INK)
    d.rectangle([x - 1, y - 1, x, y + 1], fill=(160, 110, 30))    # the hole of a mon coin
    pset(img, x - 2, y - 2, (255, 244, 170))


def draw_moth(img, x, y, t):
    """A dusty little moth (the only thing left in the wallet)."""
    x, y = int(round(x)), int(round(y))
    f = step_frame(t, 12, 2)
    c, cd = (196, 184, 160), (132, 120, 108)
    d = ImageDraw.Draw(img)
    for sgn in (-1, 1):
        if f:
            pts = [(x, y), (x + sgn * 4, y - 4), (x + sgn * 5, y - 1), (x + sgn * 1, y + 1)]
        else:
            pts = [(x, y), (x + sgn * 5, y + 1), (x + sgn * 3, y + 3), (x, y + 2)]
        d.polygon(pts, fill=c, outline=cd)
    d.line([(x, y - 1), (x, y + 2)], fill=INK)
    pset(img, x - 1, y - 2, INK)
    pset(img, x + 1, y - 2, INK)


# ====================================================================== adoption box
BOX_W, BOX_H = 46, 24          # front face incl. outline


def _box_front():
    im = Image.new("RGBA", (BOX_W, BOX_H))
    d = ImageDraw.Draw(im)
    card, sh, hi = (206, 160, 106, 255), (170, 124, 78, 255), (228, 186, 132, 255)
    ink = INK + (255,)
    d.rectangle([0, 0, BOX_W - 1, BOX_H - 1], fill=card, outline=ink)
    d.line([(1, 1), (BOX_W - 2, 1)], fill=hi)
    d.rectangle([1, BOX_H - 4, BOX_W - 2, BOX_H - 2], fill=sh)
    d.line([(BOX_W - 8, 2), (BOX_W - 8, BOX_H - 2)], fill=sh)      # corner fold
    # tape strip
    d.rectangle([BOX_W // 2 - 3, 1, BOX_W // 2 + 2, 4], fill=(222, 206, 160, 255))
    # marker text 请收养
    draw_text(im, 4, 7, "请收养", (40, 30, 34), size=12)
    return im


def _box_back():
    im = Image.new("RGBA", (BOX_W, 6))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, BOX_W - 1, 5], fill=INK + (255,))
    d.rectangle([1, 1, BOX_W - 2, 5], fill=(70, 50, 40, 255))
    return im


def draw_box_back(img, cx, ground, flap=0.0):
    """Interior strip + back flaps (draw BEFORE the dog)."""
    top = ground - BOX_H + 1
    back = _cached("boxback", _box_back)
    paste_rgba(img, back, cx - BOX_W // 2, top - 4)
    # back flap standing up / flung back
    d = ImageDraw.Draw(img)
    a = lerp(0, 1, flap)
    x0, x1 = cx - BOX_W // 2 + 3, cx + BOX_W // 2 - 3
    h = int(lerp(3, 9, a))
    d.polygon([(x0, top - 4), (x1, top - 4), (x1 + 2 * a, top - 4 - h), (x0 - 2 * a, top - 4 - h)],
              fill=(186, 140, 90), outline=INK)


def draw_box_front(img, cx, ground, flap=0.0, wiggle=0):
    """Front face with 请收养 + side flaps (draw AFTER the dog)."""
    top = ground - BOX_H + 1
    front = _cached("boxfront", _box_front)
    paste_rgba(img, front, cx - BOX_W // 2 + wiggle, top)
    d = ImageDraw.Draw(img)
    x0, x1 = cx - BOX_W // 2 + wiggle, cx + BOX_W // 2 - 1 + wiggle
    # side flaps: closed (lying inward) -> flung outward
    for sgn, xe in ((-1, x0), (1, x1)):
        ang = lerp(80, -35, flap)                        # degrees above horizontal, pointing inward
        L = 12
        rad = math.radians(ang)
        tipx = xe - sgn * math.cos(rad) * L
        tipy = top - math.sin(rad) * L
        if flap < 0.05:
            tipx, tipy = xe - sgn * 10, top - 2
        d.polygon([(xe, top), (xe, top + 1), (tipx, tipy + 1), (tipx, tipy)], fill=(214, 170, 116), outline=INK)
    # front flap
    fl = lerp(-2, 7, flap)
    d.polygon([(x0 + 2, top), (x1 - 2, top), (x1 - 4, top - fl), (x0 + 4, top - fl)] if flap > 0.05 else
              [(x0 + 2, top), (x1 - 2, top), (x1 - 3, top - 2), (x0 + 3, top - 2)],
              fill=(222, 178, 124), outline=INK)


# ====================================================================== little fx
def sweat_drop(img, x, y):
    x, y = int(x), int(y)
    d = ImageDraw.Draw(img)
    d.polygon([(x, y - 3), (x + 2, y + 1), (x, y + 3), (x - 2, y + 1)], fill=(150, 210, 255), outline=INK)
    pset(img, x - 1, y, (240, 250, 255))


def vein_mark(img, x, y, t):
    """Anime anger mark (red cross-vein) that pulses."""
    x, y = int(x), int(y)
    s = 2 + (step_frame(t, 8) % 2)
    col = (240, 60, 70)
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        ex, ey = x + dx * s, y + dy * s
        ImageDraw.Draw(img).line([(x + dx, y + dy), (ex, ey)], fill=col)
        ImageDraw.Draw(img).line([(ex, ey), (ex - dx, ey + dy * 0)], fill=col)


_CROW_PAL = {"k": (16, 14, 24), "g": (60, 58, 84), "Y": (236, 196, 70), "w": (255, 255, 255)}
_CROW = [
    """
...kk.........
...kkk........
....kkk.......
.....kkkk.....
kkkkkkkkkkkk..
..kkkkkkkkwkkY
.....kkkk.kk..
""",
    """
..............
..............
kkkkkkkkkk....
..kkkkkkkkwkkY
....kkkkkk.kk.
....kkkk......
...kkk........
""",
]


def draw_crow(img, x, y, t, facing=-1):
    """The awkward-silence crow (flies left by default). Centre at (x, y)."""
    from engine.gfx import ascii_sprite
    f = step_frame(t, 8, 2)
    spr = _cached(("crow", f, facing), lambda: (
        (lambda s: s if facing > 0 else flip_h(s))(outline(ascii_sprite(_CROW[f], _CROW_PAL), (200, 196, 220)))))
    paste_rgba(img, spr, x - spr.width // 2, y - spr.height // 2)


def tate_lines(img, x0, y0, x1, y1, t, color=(60, 70, 140), gap=4):
    """Manga 'gloom' vertical lines (tate-sen) that flicker slightly."""
    d = ImageDraw.Draw(img)
    r = rng("tate", int(t * 8))
    for x in range(int(x0), int(x1), gap):
        L = (y1 - y0) * r.uniform(0.45, 1.0)
        d.line([(x, y0), (x, y0 + L)], fill=color)
