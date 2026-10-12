"""志村妙 Shimura Tae (阿妙) — sweet closed-eye smile ... with a murderous dark aura.

Default face ('normal') is the closed-eye smile.  expr 'dark_smile' = shadowed eyes +
a flickering dark-purple aura around the whole body (works with ANY pose).
Extras: super_punch (p 0..1, wind-up -> punch -> hold), offer_egg (plate of charred
'dark matter' egg, loops on t; pass expr='dark_smile' for the menace version).
Extra exprs: dark_smile, open (eyes open, gentle), determined, sleep.
Weapon: naginata.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from engine.core import step_frame, clamp, lerp, ease_out, ease_in, ease_out_back, ANIM_FPS
from engine.gfx import INK, stamp_line, rect, pset, shade
from chars import register
from chars.rig import (ChibiDef, POSES, default_params, compose, _rotate_about, OX, OY, CW, CH,
                       pose_idle, pose_sit, pose_kneel, _blink)

# ------------------------------------------------------------------ head
HEAD_PAL = {
    "o": INK,
    "H": (170, 110, 74),    # brown hair light
    "h": (126, 76, 52),     # hair mid
    "d": (88, 50, 40),      # hair shade
    "R": (230, 90, 140),    # hair tie
    "S": (255, 222, 196),   # skin
    "s": (238, 180, 152),   # skin shade
    "E": (120, 70, 50),     # brown eyes
    "w": (255, 255, 255),
    "m": (200, 70, 90),     # lips
    "r": (240, 120, 130),   # tongue
    "b": (255, 160, 170),   # blush
    "T": (120, 200, 255),   # tears
    "B": (80, 120, 220),    # gloom
    "P": (84, 40, 96),      # dark shadow over the eyes
    "p": (120, 64, 130),    # shadow edge
    "G": (255, 250, 250),   # menacing eye glint
}

BASE = [
    ".........ooooooo.....",   # 0
    "..oo...ooHHHHHhhoo...",   # 1
    ".oRRo.oHHHHHHHhhhho..",   # 2  hair tie + ponytail root
    "oHhRRooHHHHHHhhhhhdo.",   # 3
    "oHhhoodHHHHhHHhhhhhdo",   # 4
    "oHhhodHHHHhHHHhhhhhdo",   # 5
    "ohhdodHHHhSHHhhhhhhdo",   # 6  parting
    ".ohdodhhhSSShhhhShhdo",   # 7  bangs swept aside
    ".ohdodhSSSSSSShSSShdo",   # 8
    ".ohdodhSSSSSSSSSSShdo",   # 9
    ".ohdoohSSSoSSSSoSSSho",   # 10 closed smiling eyes (^ ^)
    ".ohdo.ohSoSoSSoSoSSho",   # 11
    "..oho.ohbbSSSSSSbbsho",   # 12 blush
    "...o..ohsSSSmSSmSSsho",   # 13 smile
    "......oohsSSSmmSSsoo.",   # 14
    ".......oosSSSSSSsoo..",   # 15
    ".........ooooooo.....",   # 16
]

W_ = len(BASE[0])


def _head(**rows):
    r = list(BASE)
    for k, v in rows.items():
        i = int(k[1:])
        assert len(v) == len(BASE[i]), (k, v, len(v), len(BASE[i]))
        r[i] = v
    return "\n".join(r)


HEADS = {
    "normal": _head(),
    "blink": _head(),
    "talk": _head(r13="...o..ohsSSSSooSSSsho", r14="......oohsSSSmmSSsoo."),
    "open": _head(r10=".ohdoohSSooSSSooSSSho", r11=".ohdo.ohSwEoSSSwEoSho",
                  r13="...o..ohsSSSSmmSSSsho"),
    "angry": _head(r9=".ohdodhSSoSSSSoSSShdo", r10=".ohdoohSSSooSSooSSSho",
                   r11=".ohdo.ohSwESSSSwESSho", r12="..oho.ohsSSSSSSSSSsho",
                   r13="...o..ohsSSSooooSSsho"),
    "shout": _head(r9=".ohdodhSSoSSSSoSSShdo", r10=".ohdoohSSSooSSooSSSho",
                   r11=".ohdo.ohSwESSSSwESSho", r12="..oho.ohsSSSooooSSsho",
                   r13="...o..ohsSSSomrmoSsho", r14="......oohsSSoooSSsoo."),
    "shock": _head(r10=".ohdoohSoooSSoooSSSho", r11=".ohdo.ohowwoSowwoSSho",
                   r12="..oho.ohsoooSSoooSsho", r13="...o..ohsSSSSooSSSsho",
                   r14="......oohsSSSmmSSsoo."),
    "happy": _head(r13="...o..ohsSSSooooSSsho", r14="......oohsSSSrrSSsoo."),
    "sad": _head(r9=".ohdodhSSSoSSoSSSShdo", r10=".ohdoohSSooSSSSooSSho",
                 r11=".ohdo.ohSwESSSSwESSho", r12="..oho.ohsSSSSSSSSSsho",
                 r13="...o..ohsSSSSmmSSSsho", r14="......oohsSSSSSSSsoo."),
    "cry": _head(r10=".ohdoohSoooSSSoooSSho", r11=".ohdo.ohTTTSSSSTTTSho",
                 r12="..oho.ohTSSSSSSTSSsho", r13="...o..ohTSSSooSTSSsho",
                 r14="......oohTSSmmSSTsoo."),
    "hurt": _head(r10=".ohdoohSoSoSSoSoSSSho", r11=".ohdo.ohSSoSSSSoSSSho",
                  r12="..oho.ohsoSoSSoSoSsho", r13="...o..ohsSSSSooSSSsho"),
    "smug": _head(r13="...o..ohsSSSSSSSmSsho", r14="......oohsSSSmmmSsoo."),
    "dark_smile": _head(r7=".ohdodhhhPSPhhhhPhhdo", r8=".ohdodhPSPSPSPhPSPhdo",
                        r9=".ohdodhPPPPPPPPPPPhdo", r10=".ohdoohPPPGPPPPGPPPho",
                        r11=".ohdo.ohPGPGPPGPGPPho", r12="..oho.ohpSpSSSSpSpsho",
                        r13="...o..ohsSSSmSSmSSsho", r14="......oohsSSSmmSSsoo."),
    "determined": _head(r9=".ohdodhSSoSSSSoSSShdo", r10=".ohdoohSSSooSSooSSSho",
                        r11=".ohdo.ohSwESSSSwESSho", r13="...o..ohsSSSSmmSSSsho"),
    "sleep": _head(r10=".ohdoohSSSSSSSSSSSSho", r11=".ohdo.ohSoooSSoooSSho",
                   r13="...o..ohsSSSSSoSSSsho"),
    "gloom": _head(r7=".ohdodhhhBSShBhhShhdo", r8=".ohdodhSSBSSBSSBSShdo"),
}

# ------------------------------------------------------------------ torso
TORSO_PAL = {
    "o": INK,
    "K": (250, 172, 196),   # pink kimono light
    "k": (234, 128, 166),   # kimono mid
    "q": (190, 88, 132),    # kimono shade
    "W": (255, 250, 250),   # white under-collar
    "S": (255, 222, 196),
    "O": (170, 50, 96),     # obi
    "l": (206, 80, 126),    # obi light
    "Y": (255, 214, 110),   # obijime cord
    "f": (255, 236, 240),   # tiny floral dots
}

TORSO = """
...oooooo...
..oKWSSWko..
.oKKKWSWkkqo
.oKKKKWkkkqo
.oKKfKKWkkqo
.oOlOOOOOOOo
.oOOYYYYOOOo
.oOlOOOOOOOo
.oKKkkWkkkqo
.oKfkkWkkfqo
.oKkkkWkkkqo
.okkfkWkkqqo
.okkkkWkkqqo
..oooooooo..
"""

TORSO_SHORT = """
...oooooo...
..oKWSSWko..
.oKKKWSWkkqo
.oKKKKWkkkqo
.oKKfKKWkkqo
.oOlOOOOOOOo
.oOOYYYYOOOo
.oOlOOOOOOOo
.oKKkkWkkkqo
.okkfkWkkqqo
..oooooooo..
"""

KIMONO = (234, 128, 166)
KIMONO_B = (190, 88, 132)
TABI = (250, 246, 246)


# ------------------------------------------------------------------ props
def _big_fist(img, ctx):
    k = ctx["params"].get("_fist", 0)
    hand = ctx["hand_f"]
    if not hand or k <= 0:
        return
    x, y = int(round(hand[0])), int(round(hand[1]))
    r = 2 + int(round(k))
    d = ImageDraw.Draw(img)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 222, 196), outline=INK)
    d.line([(x + r - 1, y - 1), (x + r - 1, y + 1)], fill=(238, 180, 152))
    pset(img, x - 1, y - r + 1, (255, 255, 255, 255))


def _impact(img, ctx):
    k = ctx["params"].get("_impact", 0)
    hand = ctx["hand_f"]
    if not hand or k <= 0:
        return
    x, y = hand[0] + 5, hand[1]
    d = ImageDraw.Draw(img)
    n = 8
    for i in range(n):
        a = i * 2 * math.pi / n + 0.3
        r0, r1 = 3 + 4 * k, 7 + 8 * k
        p0 = (x + math.cos(a) * r0, y + math.sin(a) * r0)
        p1 = (x + math.cos(a) * r1, y + math.sin(a) * r1)
        d.line([p0, p1], fill=(255, 240, 120), width=1)
    if k < 0.6:
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 255, 255))


def _egg_prop(img, ctx):
    """Plate with the infamous charred 'egg' (dark matter) + purple miasma."""
    hand = ctx["hand_f"]
    if not hand:
        return
    x, y = int(round(hand[0])), int(round(hand[1])) - 1
    t = ctx["t"]
    d = ImageDraw.Draw(img)
    # plate
    d.ellipse([x - 6, y - 1, x + 7, y + 2], fill=(236, 240, 250), outline=INK)
    d.line([(x - 4, y), (x + 3, y)], fill=(255, 255, 255))
    # the 'egg': lumpy black mass
    d.polygon([(x - 4, y), (x - 3, y - 3), (x - 1, y - 4), (x + 2, y - 4), (x + 4, y - 2), (x + 5, y)],
              fill=(30, 22, 36), outline=INK)
    pset(img, x - 1, y - 3, (70, 60, 84, 255))
    pset(img, x + 2, y - 3, (60, 50, 74, 255))
    pset(img, x, y - 1, (100, 40, 60, 255))
    # miasma curls rising (loop)
    f = step_frame(t, 8)
    for i in range(3):
        ph = (f + i * 3) % 9
        yy = y - 5 - ph
        xx = x - 3 + i * 3 + (1 if (ph // 2) % 2 else -1)
        col = (150, 90, 190, 255) if ph < 6 else (110, 70, 150, 255)
        pset(img, xx, yy, col)
        pset(img, xx + (1 if ph % 2 else -1), yy - 1, col)


# ------------------------------------------------------------------ poses
def pose_idle_o(pp, t, p, d):
    pose_idle(pp, t, p, d)
    pp["arm_f"] = 8 + (2 if step_frame(t, 4, 4) in (1, 2) else 0)
    pp["arm_b"] = -8
    pp["expr"] = "open" if (t % 5.0) > 4.3 else "normal"


def pose_sit_o(pp, t, p, d):
    pose_sit(pp, t, p, d)
    pp["torso"] = "short"
    pp["expr"] = "normal"


def pose_kneel_o(pp, t, p, d):
    pose_kneel(pp, t, p, d)
    pp["torso"] = "short"


def pose_super_punch(pp, t, p, d):
    if p < 0.35:
        k = ease_out(p / 0.35)
        pp["arm_f"] = lerp(20, -70, k)
        pp["arm_b"] = lerp(-10, 60, k)
        pp["lean"] = int(lerp(0, -2, k))
        pp["legs"] = "spread"
        pp["expr"] = "dark_smile"
        pp["_fist"] = k
        pp["head_dx"] = -1 if k > 0.5 else 0
    elif p < 0.5:
        k = ease_in((p - 0.35) / 0.15)
        pp["arm_f"] = lerp(-70, 95, k)
        pp["arm_b"] = lerp(60, -50, k)
        pp["lean"] = int(lerp(-2, 4, k))
        pp["legs"] = "lunge"
        pp["expr"] = "shout"
        pp["_fist"] = 2
    else:
        k = (p - 0.5) / 0.5
        pp["arm_f"] = 95
        pp["arm_b"] = -50
        pp["lean"] = 4
        pp["legs"] = "lunge"
        pp["expr"] = "shout" if k < 0.4 else "dark_smile"
        pp["_fist"] = 2
        pp["_impact"] = clamp(k * 2.2)
    pp["props"] = [_big_fist, _impact]


def pose_offer_egg(pp, t, p, d):
    pose_idle(pp, t, p, d)
    f = step_frame(t, 4, 4)
    pp["arm_f"] = 80 + (2 if f in (1, 2) else 0)
    pp["arm_b"] = 60
    pp["lean"] = 1
    pp["expr"] = "normal"
    pp["props"] = [_egg_prop]


# ------------------------------------------------------------------ renderer
_AURA_DARK = (60, 20, 76)
_AURA_MID = (104, 44, 130)
_AURA_HI = (150, 80, 180)
_SHOE_KEY = (243, 5, 241)


def _feet(a):
    """Repaint sentinel-coloured shoes: lowest row = white tabi, rest = kimono."""
    rgb = a[..., :3]
    for key, cloth, tabi in ((_SHOE_KEY, KIMONO, TABI),
                             (shade(_SHOE_KEY, 0.8), KIMONO_B, shade(TABI, 0.86))):
        m = (rgb == np.array(key, np.uint8)).all(-1) & (a[..., 3] > 0)
        if not m.any():
            continue
        below = np.zeros_like(m)
        below[:-1] = m[1:]
        rgb[m] = cloth
        rgb[m & ~below] = tabi
    return a


def _dil(mask, k):
    m = Image.fromarray((mask * 255).astype(np.uint8), "L")
    return np.asarray(m.filter(ImageFilter.MaxFilter(k))) > 0


def dark_aura(img, t, mask=None):
    """Flickering dark 'killing intent' aura behind a sprite (RGBA, same size):
    thin glowing rim + dithered halo + flame tongues licking upward + rising specks."""
    a = np.asarray(img)
    body = a[..., 3] > 0
    mask = body if mask is None else (mask | body)
    if not mask.any():
        return img
    h, w = mask.shape
    f = step_frame(t, 10)
    d3, d5 = _dil(mask, 3), _dil(mask, 5)
    yy, xx = np.mgrid[0:h, 0:w]
    out = np.zeros((h, w, 4), np.uint8)
    halo = d5 & ~d3 & (((xx + yy + f) % 2) == 0)
    out[halo] = _AURA_DARK + (255,)
    # flame tongues from the top edge of the halo
    top = np.where(d5.any(0), d5.argmax(0), -1)
    for x in np.nonzero(top >= 0)[0]:
        y0 = top[x]
        hgt = int(round(2.2 + 2.2 * math.sin(x * 1.25 + f * 1.9) + 1.4 * math.sin(x * 0.53 - f * 1.3)))
        for k in range(max(0, hgt)):
            y = y0 - 1 - k
            if 0 <= y < h:
                out[y, x] = (_AURA_MID if k < hgt - 1 else _AURA_HI) + (255,)
    out[d3 & ~body] = _AURA_MID + (255,)
    # rising specks
    for i in range(6):
        r = (i * 37 + 11) % max(1, w)
        cols = np.nonzero(top >= 0)[0]
        if len(cols) == 0:
            break
        x = cols[(i * 7 + f // 3) % len(cols)]
        y = top[x] - 3 - ((f * 2 + i * 5) % 9)
        if 0 <= y < h:
            out[y, x] = _AURA_HI + (255,)
    aura = Image.fromarray(out, "RGBA")
    aura.alpha_composite(img)
    return aura


class OtaeDef(ChibiDef):
    def render(self, pose="idle", t=0.0, p=None, expr=None, **kw):
        fn = self.poses.get(pose) or POSES.get(pose) or POSES["idle"]
        pp = default_params()
        pp["_fist"] = 0
        pp["_impact"] = 0
        pp["aura"] = None
        fn(pp, t, p if p is not None else (t % 1.0), self)
        pp.update({k: v for k, v in kw.items() if k in pp})
        if expr is not None:
            pp["expr"] = expr
        img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        ctx = compose(self, img, pp, t)
        body = img.copy()                      # aura hugs the body, not the props
        for prop in pp["props"]:
            prop(img, ctx)
        img = Image.fromarray(_feet(np.array(img)), "RGBA")
        ax, ay = OX, OY
        if pp["rot"]:
            img, ax, ay = _rotate_about(img, pp["rot"], OX, OY - 14, OX, OY)
            body, _, _ = _rotate_about(body, pp["rot"], OX, OY - 14, OX, OY)
        aura = pp["aura"] if pp["aura"] is not None else (pp["expr"] == "dark_smile")
        if aura:
            img = dark_aura(img, t, np.asarray(body)[..., 3] > 0)
        return img, ax, ay


OTAE = register(OtaeDef(
    id="otae", name="阿妙", color=(214, 84, 146), voice=1.2,
    heads=HEADS, head_pal=HEAD_PAL, head_anchor=(12, 15),
    torso={"default": TORSO, "short": TORSO_SHORT}, torso_pal=TORSO_PAL,
    neck=(6, 2), hip=(6, 8), shoulder_f=(9, 3), shoulder_b=(2, 3),
    arm_len=6, arm_w=2, sleeve_f=(242, 150, 182), sleeve_b=(200, 104, 146), sleeve_frac=0.7,
    hand=(255, 222, 196),
    leg_len=7, leg_w=3, leg_gap=3, pants=KIMONO, shoes=_SHOE_KEY, shoe_h=1,
    weapon="naginata", weapon_len=16,
    poses={"idle": pose_idle_o, "sit": pose_sit_o, "kneel": pose_kneel_o,
           "super_punch": pose_super_punch, "offer_egg": pose_offer_egg},
    desc="新八的姐姐，志村道场的看板娘。笑容温柔，拳头致命；做出的煎蛋是漆黑的『暗黑物质』。",
))
