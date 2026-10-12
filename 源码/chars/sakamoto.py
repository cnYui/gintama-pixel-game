"""坂本辰马 Sakamoto Tatsuma — big messy curly dark-brown hair, sunglasses,
crimson coat over a dark kimono, western boots, eternal "AHAHAHA".

Extra poses:
  laugh : hands on hips, head thrown back, bouncing "AHAHAHA" (tiny HA letters pop)
          pass ha=False to draw_char to hide the letters.
  shoot : pistol aimed forward; muzzle flash + recoil at the start of each
          cycle (p 0..1; loops with t when p is None).
"""
import math

from engine.core import step_frame, clamp, lerp, ease_out
from engine.gfx import INK, stamp_line, rect, pset, shade
from chars import register
from chars.rig import pose_idle, _blink
from chars.katsura import LayeredChibi, make_head_builder, make_sheath

HEAD_PAL = {
    "o": INK,
    "L": (126, 88, 70),     # curl highlight
    "H": (80, 54, 46),      # near-black brown curly hair (canon: dark)
    "h": (56, 38, 38),      # shade
    "d": (38, 26, 30),      # deep
    "S": (255, 212, 176),   # skin (a little tanned)
    "s": (228, 160, 128),
    "G": (40, 44, 64),      # sunglasses lens
    "g": (70, 80, 112),     # lens lower reflection
    "w": (255, 255, 255),
    "m": (170, 60, 70),     # mouth
    "t": (255, 255, 255),   # teeth
    "b": (250, 150, 140),
    "T": (120, 200, 255),
    "E": (60, 40, 30),
}

BASE = [
    "....oo.ooo.ooo.o....",   # 0  big curly mop (bumpy outline)
    "...oLLoHLLoHLHoHo...",   # 1
    "..oHHHHHHHHHHHHHHo..",   # 2
    ".oHLLHHhHLLHHhHLLHo.",   # 3
    "oHHHHhHHHHHhHHHHHhHo",   # 4
    ".oLHHHHLLHHHHLLHHHo.",   # 5
    "oHHhHHHHHhHHHHHhHHHo",   # 6
    ".oHHHLLHHHHLLHHHHLo.",   # 7
    "oHhHSHHhSHHSHhHSHhHo",   # 8  curly fringe
    "ohHHSSSSSSSSSSSSHHho",   # 9
    "oHHSSooooSSSooooSHHo",   # 10 sunglasses frame
    "ohHSoGwGGooGwGGgoHho",   # 11 lenses
    "oHHSSoGgoSSSoGgoSHHo",   # 12
    ".oHhSSSSSSSSSSSShHo.",   # 13
    "..ohsSSSmSSSSmSSsho.",   # 14 grin
    "...oosSSSmmmmSSsoo..",   # 15
    ".....oooooooooo.....",   # 16
]
_head = make_head_builder(BASE)

_LAUGH = dict(r13=".oHhSSSooooooSSShHo.", r14="..ohsSottttttoSSsho.",
              r15="...oosommmmmmoSsoo..")

HEADS = {
    "normal": _head(),
    "blink": _head(),                      # sunglasses: blinking is invisible
    "talk": _head(r14="..ohsSSSSooooSSSsho.", r15="...oosSSSSmmSSSsoo.."),
    "angry": _head(r9="ohHHSoSSSSSSSSoSHHho", r14="..ohsSSSSooooSSSsho.",
                   r15="...oosSSSSSSSSSsoo.."),
    "determined": _head(r9="ohHHSoSSSSSSSSoSHHho", r14="..ohsSSSSSSSSSSSsho.",
                        r15="...oosSSSmmmmSSsoo.."),
    "shout": _head(r9="ohHHSoSSSSSSSSoSHHho", r13=".oHhSSSSooooSSSShHo.",
                   r14="..ohsSSSomwwmoSSsho.", r15="...oosSSSooooSSsoo.."),
    "shock": _head(r13=".oHhSSSSSooSSSSShHo.", r14="..ohsSSSSommoSSSsho.",
                   r15="...oosSSSSooSSSsoo.."),
    "happy": _head(**_LAUGH),
    "laugh": _head(**_LAUGH),
    "sad": _head(r9="ohHHSSSoSSSSoSSSHHho", r14="..ohsSSSSSSSSSSSsho.",
                 r15="...oosSSSSmmSSSsoo.."),
    "cry": _head(r12="oHHSSoTToSSSoTToSHHo", r13=".oHhSSTSSSSSSTSShHo.",
                 r14="..ohsSTSooooSTSSsho.", r15="...oosSTSmmmmTSsoo.."),
    "hurt": _head(r11="ohHSoGGGGooGGGGgoHho", r14="..ohsSSSSooooSSSsho.",
                  r15="...oosSSSmSSmSSsoo.."),
    "smug": _head(r14="..ohsSSSSSSSSSmSsho.", r15="...oosSSSSmmmmSsoo.."),
}

TORSO_PAL = {
    "o": INK,
    "R": (204, 56, 66),     # crimson coat
    "r": (150, 36, 52),     # coat shade
    "Q": (236, 104, 100),   # coat highlight
    "K": (44, 40, 58),      # dark kimono
    "k": (84, 78, 104),
    "W": (236, 234, 244),   # white under-collar
    "B": (110, 76, 50),     # leather belt
    "Y": (230, 190, 70),    # buckle
}

TORSO = """
....oooooo....
...oRWKKWRo...
..oRRWKKWRRo..
.oQRRRWKKRRro.
.oQRRRKkKRRro.
.oRRRRKKKRRro.
.oRRRBBYBRRro.
.oRRRRKKKRrro.
.oRRRRKKKRrro.
.orRRRKKKRrro.
.orRRRKKKrrro.
.orRRoKKKorro.
..ooo.ooo.ooo.
"""


# ------------------------------------------------------------------ props
_H3 = ["x.x", "x.x", "xxx", "x.x", "x.x"]
_A3 = [".x.", "x.x", "xxx", "x.x", "x.x"]


def _glyph(img, x, y, g, col):
    for j, row in enumerate(g):
        for i, ch in enumerate(row):
            if ch == "x":
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        px, py = x + i + dx, y + j + dy
                        if 0 <= px < img.width and 0 <= py < img.height and img.getpixel((px, py))[3] == 0:
                            img.putpixel((px, py), INK + (255,))
    for j, row in enumerate(g):
        for i, ch in enumerate(row):
            if ch == "x":
                pset(img, x + i, y + j, col)


def _ha_letters(img, ctx):
    if ctx.get("kw", {}).get("ha", True) is False:
        return
    hx, hy, hw, hh = ctx["head"]
    f = step_frame(ctx["t"], 6)
    col = (255, 236, 120)
    spots = [(hx + hw + 1, hy + 1), (hx + hw + 5, hy - 5), (hx - 6, hy - 3), (hx + 6, hy - 9)]
    for i in range(2):
        k = (f + i * 2) % len(spots)
        sx, sy = spots[k]
        sy -= (f % 2)
        _glyph(img, int(sx), int(sy), _H3, col)
        _glyph(img, int(sx) + 4, int(sy), _A3, col)


def _akimbo(img, ctx, front=True):
    """Bent arm with the fist planted on the hip (hands-on-hips laugh)."""
    d = ctx["def"]
    sx, sy = ctx["shoulder_f"] if front else ctx["shoulder_b"]
    sg = 1 if front else -1
    el = (sx + sg * 4, sy + 3)
    hd = (sx + sg * 1, sy + 7)
    col = d.sleeve_f if front else d.sleeve_b
    hand = d.hand if front else shade(d.hand, 0.85)
    w = d.arm_w
    for a, b in (((sx, sy), el), (el, hd)):
        stamp_line(img, a, b, w + 2, INK)
    stamp_line(img, hd, hd, w + 3, INK)
    stamp_line(img, (sx, sy), el, w, col)
    stamp_line(img, el, hd, w, col)
    stamp_line(img, hd, hd, w + 1, hand)


def pose_laugh(pp, t, p, d):
    """AHAHAHA! hands on hips, head thrown back, bouncing."""
    f = step_frame(t, 8, 2)
    pp["expr"] = "laugh"
    pp["hide_arm_f"] = True
    pp["hide_arm_b"] = True
    pp["head_dx"] = -1
    pp["head_dy"] = -1 if f else 0
    pp["bob"] = -1 if f else 0
    pp["behind"] = [lambda img, ctx: _akimbo(img, ctx, False)]
    pp["props"] = [lambda img, ctx: _akimbo(img, ctx, True), _ha_letters]


def _pistol(img, ctx):
    h = ctx["hand_f"]
    if not h:
        return
    x, y = int(round(h[0])), int(round(h[1]))
    pp = ctx["params"]
    # barrel pointing forward (slightly up with recoil)
    up = pp.get("recoil", 0)
    rect(img, x - 1, y - 3 - up, 9, 4, INK)          # outline
    rect(img, x, y - 2 - up, 7, 2, (120, 124, 140))  # barrel
    rect(img, x, y - 2 - up, 7, 1, (180, 186, 204))
    rect(img, x - 1, y - 1, 4, 5, INK)                # grip
    rect(img, x, y, 2, 3, (110, 70, 44))
    stamp_line(img, h, h, 3, ctx["def"].hand)         # fist over grip
    if pp.get("flash"):
        mx, my = x + 8, y - 2 - up
        r = 3 if step_frame(ctx["t"], 30) % 2 else 2
        for dx in range(-r, r + 1):
            pset(img, mx + 1 + dx + r, my, (255, 240, 150))
        for dy in range(-r + 1, r):
            pset(img, mx + 1 + r, my + dy, (255, 240, 150))
        pset(img, mx + 1 + r, my, (255, 255, 255))
        pset(img, mx + r, my - 1, (255, 200, 80))
        pset(img, mx + r, my + 1, (255, 200, 80))


def pose_shoot(pp, t, p, d):
    """Pistol aimed forward; p<0.18 = bang (muzzle flash, recoil)."""
    f = step_frame(t, 4, 2)
    kick = p < 0.18
    pp["arm_f"] = 96 if kick else 88
    pp["arm_b"] = -20
    pp["lean"] = -1 if kick else 0
    pp["legs"] = "spread"
    pp["expr"] = "determined" if not kick else "shout"
    pp["recoil"] = 1 if kick else 0
    pp["flash"] = p < 0.1
    pp["props"] = [_pistol]


SAKAMOTO = register(LayeredChibi(
    id="sakamoto", name="坂本", color=(184, 50, 62), voice=0.9,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=(204, 56, 66), sleeve_b=(150, 36, 52), sleeve_frac=0.7,
    hand=(255, 212, 176),
    leg_len=7, leg_w=3, leg_gap=4, pants=(46, 42, 60), shoes=(96, 60, 40), shoe_h=3,
    weapon="katana", weapon_len=17,
    sheathed=make_sheath(saya=(60, 40, 36), saya_hi=(110, 76, 60)),
    poses={"laugh": pose_laugh, "shoot": pose_shoot},
    desc="快援队队长，银时的攘夷战友。天然卷黑发配墨镜，红色外套，开朗到烦人的『啊哈哈哈』，梦想做宇宙生意。",
))
