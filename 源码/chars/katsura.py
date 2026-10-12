"""桂小太郎 Katsura Kotarou — long straight black hair, dark-blue kimono + white haori.

Also defines helpers shared by the other agent-C characters (katsura_short,
takasugi, sakamoto, shiroyasha):
  * LayeredChibi  : ChibiDef + layers drawn BEHIND the whole body (long hair,
                    headband tails, railings) + kw passthrough (ctx['kw']).
  * make_sheath() : sheathed katana at the hip.
  * draw_bomb()   : Katsura's round bomb with a sparking fuse (scenes may use it
                    for a thrown bomb: from chars.katsura import draw_bomb).

Extra poses: bomb (holds a lit bomb), bomb_throw (p-driven wind-up + throw,
the bomb leaves the hand at p≈0.5), run_away (fleeing, hair streaming).
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import step_frame, clamp, lerp, ease_out, ease_in_out, rng
from engine.gfx import INK, stamp_line, rect, pset, shade
from chars import register
from chars.rig import (ChibiDef, POSES, CW, CH, OX, OY, compose, default_params,
                       pose_idle, pose_run, pose_walk, _blink)


# ================================================================== shared helpers
class LayeredChibi(ChibiDef):
    """ChibiDef that can draw layers BEHIND the whole character.

    behind : callable(layer_img, ctx) drawn behind everything (e.g. long hair)
    Poses may append more behind-callables to pp['behind'] and custom keys to pp.
    Any draw_char(**kw) is available to props as ctx['kw'].
    """

    def __init__(self, *a, behind=None, **k):
        super().__init__(*a, **k)
        self.behind = behind

    def render(self, pose="idle", t=0.0, p=None, expr=None, **kw):
        fn = self.poses.get(pose) or POSES.get(pose) or POSES["idle"]
        pp = default_params()
        pp["behind"] = []
        pp["pose"] = pose
        fn(pp, t, p if p is not None else (t % 1.0), self)
        pp.update({k: v for k, v in kw.items() if k in pp and k not in ("behind", "pose")})
        if expr is not None:
            pp["expr"] = expr
        img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        ctx = compose(self, img, pp, t)
        ctx["kw"] = kw
        layers = ([self.behind] if self.behind else []) + list(pp["behind"])
        if layers:
            back = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
            for f in layers:
                f(back, ctx)
            back.alpha_composite(img)
            img = back
        for prop in pp["props"]:
            prop(img, ctx)
        if pp["rot"]:
            img = img.rotate(pp["rot"], resample=Image.NEAREST, center=(OX, OY - 14))
        return img, OX, OY


def make_head_builder(base):
    def _head(**rows):
        r = list(base)
        for k, v in rows.items():
            i = int(k[1:])
            assert len(v) == len(base[i]), (k, v, len(v), len(base[i]))
            r[i] = v
        return "\n".join(r)
    return _head


def make_sheath(saya=(46, 40, 66), saya_hi=(84, 76, 110), hilt=(36, 30, 44),
                guard=(230, 180, 60), wrap=(200, 200, 214)):
    """Sheathed katana tucked in the belt: hilt forward, scabbard behind."""
    def sheathed(img, torso_xy, torso_size):
        tx, ty = torso_xy
        a, b = (tx + 14, ty + 5), (tx - 6, ty + 10)
        stamp_line(img, a, b, 4, INK)
        stamp_line(img, (tx + 10, ty + 6), b, 2, saya)
        stamp_line(img, (tx + 6, ty + 7), (tx - 5, ty + 9.6), 1, saya_hi)
        stamp_line(img, a, (tx + 11, ty + 5.7), 2, hilt)
        pset(img, tx + 12, ty + 5, wrap)
        stamp_line(img, (tx + 10, ty + 4), (tx + 10, ty + 7), 1, guard)
    return sheathed


def fill_shape(img, polys, colfn, outline=INK):
    """Fill polygon(s) (list of point lists) with per-pixel colours colfn(x, y)
    and give the union a 1px outline. Draws into RGBA img."""
    m = Image.new("L", img.size, 0)
    dr = ImageDraw.Draw(m)
    for pts in polys:
        dr.polygon([tuple(p) for p in pts], fill=255)
    a = np.asarray(m) > 0
    dil = a.copy()
    dil[1:, :] |= a[:-1, :]
    dil[:-1, :] |= a[1:, :]
    dil[:, 1:] |= a[:, :-1]
    dil[:, :-1] |= a[:, 1:]
    px = img.load()
    ys, xs = np.nonzero(dil & ~a)
    for y, x in zip(ys.tolist(), xs.tolist()):
        px[x, y] = tuple(outline) + (255,)
    ys, xs = np.nonzero(a)
    for y, x in zip(ys.tolist(), xs.tolist()):
        c = colfn(x, y)
        px[x, y] = tuple(c) + (255,)


def draw_bomb(img, x, y, t, r=3, lit=True):
    """Round black bomb centred at (x, y) with a fuse + animated spark.
    Works on RGB canvases and RGBA sprites."""
    x, y = int(round(x)), int(round(y))
    d = ImageDraw.Draw(img)
    d.ellipse([x - r - 1, y - r - 1, x + r + 1, y + r + 1], fill=INK)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(52, 52, 70))
    pset(img, x - 1, y - 1, (110, 112, 140))
    pset(img, x - 2, y - 1, (84, 86, 112))
    pset(img, x - 1, y - 2, (84, 86, 112))
    # cap + fuse
    rect(img, x, y - r - 2, 2, 2, INK)
    pset(img, x + 1, y - r - 2, (150, 150, 170))
    fx_, fy_ = x + 2, y - r - 3
    pset(img, x + 2, y - r - 2, (220, 200, 150))
    pset(img, fx_, fy_, (220, 200, 150))
    if not lit:
        return
    f = step_frame(t, 12)
    sx, sy = fx_ + 1, fy_ - 1
    core = [(255, 255, 255), (255, 240, 120), (255, 200, 60)][f % 3]
    pset(img, sx, sy, core)
    if f % 2 == 0:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            pset(img, sx + dx, sy + dy, (255, 196, 60))
    else:
        for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
            pset(img, sx + dx, sy + dy, (255, 150, 40))
    r_ = rng("bombspark", f)
    for _ in range(2):
        pset(img, sx + r_.randint(-3, 3), sy + r_.randint(-3, 1), (255, 230, 120))


# ================================================================== palette / heads
HEAD_PAL = {
    "o": INK,
    "L": (112, 120, 166),   # angel-ring shine
    "H": (60, 62, 94),      # black hair (blue sheen)
    "h": (42, 42, 68),      # hair shade
    "d": (30, 28, 48),      # deep shade
    "S": (255, 220, 190),   # skin (a bit fairer than Gintoki)
    "s": (236, 176, 146),   # skin shade
    "E": (112, 72, 50),     # brown eyes
    "e": (60, 34, 30),      # pupil
    "w": (255, 255, 255),
    "m": (176, 76, 84),     # mouth
    "b": (250, 156, 156),   # blush
    "T": (120, 200, 255),   # tears
    "B": (80, 120, 220),
}

BASE = [
    "......oooooo......",   # 0
    "....ooHHHHHHoo....",   # 1
    "...oHHHHHHHHHHo...",   # 2
    "..oHHHLLLLLHHHho..",   # 3
    ".oHHLLHHHHHLLHHho.",   # 4
    "ohHHHHHHHHHHHHHHho",   # 5
    "ohHHHHHHHhHHHHHHho",   # 6
    "ohHHHHHHhHhHHHHHho",   # 7
    "ohHHHhHhHSHhHhHHho",   # 8  bangs, parted
    "ohHhHShSSSSShSHHho",   # 9  bang tips
    "ohHSoooSSSSoooSHho",   # 10 lashes
    "ohHSwEeSSSSwEeSHho",   # 11 eyes (big, 2 rows)
    "ohHSEEeSSSSEEeSHho",   # 12
    "ohHSSSSSSSSSSSSHho",   # 13
    "ohHHsSSSSmSSSSsHho",   # 14 mouth
    "ohHHHosSSSSSsoHHho",   # 15 jaw
    "ohhHHHoooooooHHhho",   # 16 chin, side locks continue down
]

_head = make_head_builder(BASE)

_ANGRY = dict(r9="ohHoHShSSSSShSoHho", r10="ohHSoooSSSSoooSHho",
              r11="ohHSEEeSSSSEEeSHho", r12="ohHSSSSSSSSSSSSHho")

HEADS = {
    "normal": _head(),
    "blink": _head(r10="ohHSSSSSSSSSSSSHho", r11="ohHSoooSSSSoooSHho", r12="ohHSSSSSSSSSSSSHho"),
    "talk": _head(r14="ohHHsSSSooSSSSsHho", r15="ohHHHosSSmmSsoHHho"),
    "angry": _head(r14="ohHHsSSSooSSSSsHho", **_ANGRY),
    "determined": _head(**_ANGRY),
    "shout": _head(r13="ohHSSSSSoooSSSSHho", r14="ohHHsSSSomoSSSsHho",
                   r15="ohHHHosSSooSsoHHho", **_ANGRY),
    "shock": _head(r10="ohHSoooSSSSoooSHho", r11="ohHSowoSSSSowoSHho",
                   r12="ohHSoooSSSSoooSHho", r14="ohHHsSSSSooSSSsHho",
                   r15="ohHHHosSSmmSsoHHho"),
    "happy": _head(r10="ohHSSoSSSSSSoSSHho", r11="ohHSoSoSSSSoSoSHho",
                   r12="ohHSbbSSSSSSbbSHho", r14="ohHHsSSSmSSmSSsHho",
                   r15="ohHHHosSSmmSsoHHho"),
    "sad": _head(r9="ohHhHShoSSoShSHHho", r14="ohHHsSSSSmmSSSsHho"),
    "cry": _head(r9="ohHhHShoSSoShSHHho", r10="ohHSSSSSSSSSSSSHho",
                 r11="ohHSoooSSSSoooSHho", r12="ohHSTTSSSSSTTSSHho",
                 r13="ohHSTSSSSSSTSSSHho", r14="ohHHTSSSooSTSSsHho",
                 r15="ohHHHoTSSmmTsoHHho"),
    "hurt": _head(r10="ohHSoSSSSSSSSoSHho", r11="ohHSSooSSSSooSSHho",
                  r12="ohHSoSSSSSSSSoSHho", r14="ohHHsSSSooSSSSsHho"),
    "smug": _head(r10="ohHSSSSSSSSSSSSHho", r11="ohHSoooSSSSoooSHho",
                  r14="ohHHsSSSSSSSmSsHho", r15="ohHHHosSSmmmsoHHho"),
    "sleep": _head(r10="ohHSSSSSSSSSSSSHho", r11="ohHSoooSSSSoooSHho",
                   r12="ohHSSSSSSSSSSSSHho", r14="ohHHsSSSSoSSSSsHho"),
    "gloom": _head(r7="ohHHHBHHhHBHHBHHho", r8="ohHHHBHhHSBhHBHHho", r9="ohHhHBhSSSBShBHHho"),
}

TORSO_PAL = {
    "o": INK,
    "W": (240, 236, 222),   # white/beige haori
    "w": (196, 190, 170),   # haori shade
    "B": (54, 72, 128),     # dark blue kimono
    "b": (86, 108, 168),    # kimono highlight
    "c": (250, 250, 255),   # white under-collar
    "K": (36, 34, 56),      # obi
    "k": (86, 80, 112),
}

TORSO = """
....oooooo....
...oBBBBBBo...
..oWcBBBBcWo..
.oWWWcbBcWWwo.
.oWWWBcbBWWwo.
.oWWWBbBBWWwo.
.oWWWKkKKWWwo.
.oWWWBBBBWwwo.
.owWWBbBBWwwo.
.owWWBBBBwwwo.
.owWWBBBBwwwo.
..oooooooooo..
"""

HAIR_COLS = {"L": HEAD_PAL["L"], "H": HEAD_PAL["H"], "h": HEAD_PAL["h"], "d": HEAD_PAL["d"]}

_hair_cache = {}


def _hair_sprite(mode, frame):
    """Long back-hair curtain as a sprite relative to the head's top-left.
    Returns (sprite, ox, oy): paste at (hx + ox, hy + oy)."""
    key = (mode, frame)
    s = _hair_cache.get(key)
    if s is not None:
        return s
    im = Image.new("RGBA", (48, 40), (0, 0, 0, 0))
    ox, oy = -24, -2           # sprite origin relative to head top-left
    # coordinates below are head-relative (+24, +2 applied)
    X = lambda x: x - ox
    Y = lambda y: y - oy
    if mode == "stream":       # flying horizontally behind (running away)
        wv = [0, 1, 0, -1][frame % 4]
        pts = [(4, 5), (-3, 7), (-9, 8 + wv), (-14, 9 + wv), (-11, 11), (-15, 13 - wv),
               (-11, 15), (-13, 17 + wv), (-6, 19), (0, 21), (4, 21)]
        pts = [(X(x), Y(y)) for x, y in pts]
    elif mode == "run":
        wv = frame % 2
        pts = [(X(2), Y(6)), (X(15), Y(6)), (X(15), Y(20)), (X(9), Y(23)),
               (X(-3 - wv), Y(22 + wv)), (X(-2), Y(12))]
    else:                      # hang / sway
        sw = {0: 0, 1: -1, 2: 0, 3: 1}.get(frame % 4, 0) if mode == "sway" else 0
        if mode == "float":
            pts = [(X(1), Y(8)), (X(16), Y(8)), (X(17), Y(18)), (X(10), Y(22)),
                   (X(1), Y(23)), (X(-1), Y(16))]
        else:
            pts = [(X(1), Y(8)), (X(16), Y(8)), (X(16), Y(21)), (X(15 + sw), Y(24)),
                   (X(1 + sw), Y(25)), (X(1), Y(14))]

    horiz = mode in ("stream", "run")

    def col(x, y):
        hx, hy = x + ox, y + oy
        if horiz:                          # strands run horizontally
            b = (hy + (hx // 4)) % 3
            if b == 0:
                return HAIR_COLS["h"]
            if b == 1 and (hx + hy) % 5 == 0:
                return HAIR_COLS["L"]
            return HAIR_COLS["H"]
        if (hx * 3 + y // 5) % 5 == 0:
            return HAIR_COLS["h"]
        if hx <= 2 or hx >= 15:
            return HAIR_COLS["h"]
        if (hx + 1) % 4 == 0 and y > Y(12):
            return HAIR_COLS["L"] if (y % 7 == 0) else HAIR_COLS["H"]
        return HAIR_COLS["H"]

    fill_shape(im, [pts], col)
    s = (im, ox, oy)
    _hair_cache[key] = s
    return s


def katsura_hair_back(img, ctx):
    pp = ctx["params"]
    mode = pp.get("hair", "hang")
    if mode == "none":
        return
    t = ctx["t"]
    hx, hy, hw, hh = ctx["head"]
    frame = step_frame(t, 12)
    if mode == "sway":
        frame = step_frame(t, 6)
    spr, ox, oy = _hair_sprite(mode, frame % 4)
    img.alpha_composite(spr, (int(hx + ox), int(hy + oy)))


# ================================================================== poses
def _bomb_in_hand(img, ctx):
    h = ctx["hand_f"]
    if h:
        a = math.radians(ctx["params"]["arm_f"])
        draw_bomb(img, h[0] + math.sin(a) * 2.5 + 0.5, h[1] + math.cos(a) * 2.5 - 1.5, ctx["t"])


def pose_bomb(pp, t, p, d):
    """Deadpan: holds up a round bomb with a lit, sparking fuse."""
    pose_idle(pp, t, p, d)
    f = step_frame(t, 4, 4)
    pp["arm_f"] = 112 + (3 if f in (1, 2) else 0)
    pp["arm_b"] = -18
    pp["props"] = [_bomb_in_hand]


def pose_bomb_throw(pp, t, p, d):
    """p 0..1: wind-up (0-0.4), throw (0.4-0.55, bomb released), follow-through."""
    pp["expr"] = "determined"
    if p < 0.4:
        k = ease_out(p / 0.4)
        pp["arm_f"] = lerp(100, 165, k)
        pp["arm_b"] = lerp(-15, 40, k)
        pp["lean"] = -2
        pp["head_dx"] = -1
        pp["legs"] = "spread"
        pp["props"] = [_bomb_in_hand]
    elif p < 0.55:
        k = ease_in_out((p - 0.4) / 0.15)
        pp["arm_f"] = lerp(165, 80, k)
        pp["arm_b"] = lerp(40, -30, k)
        pp["lean"] = 2
        pp["legs"] = "lunge"
        if k < 0.5:
            pp["props"] = [_bomb_in_hand]
    else:
        pp["arm_f"] = 95
        pp["arm_b"] = -30
        pp["lean"] = 2
        pp["legs"] = "lunge"
        pp["expr"] = "smug"


def pose_walk_k(pp, t, p, d):
    pose_walk(pp, t, p, d)
    pp["hair"] = "sway"


def pose_run_k(pp, t, p, d):
    pose_run(pp, t, p, d)
    pp["hair"] = "run"


def pose_run_away_k(pp, t, p, d):
    """逃げの小太郎: full-speed retreat, serious face, hair streaming behind."""
    pose_run(pp, t, p, d)
    pp["lean"] = 3
    pp["hair"] = "stream"
    pp["expr"] = "determined"


def pose_jump_k(pp, t, p, d):
    POSES["jump"](pp, t, p, d)
    pp["hair"] = "float"


def pose_fly_k(pp, t, p, d):
    POSES["fly"](pp, t, p, d)
    pp["hair"] = "float"


KATSURA_POSES = {"bomb": pose_bomb, "bomb_throw": pose_bomb_throw, "run_away": pose_run_away_k,
                 "walk": pose_walk_k, "run": pose_run_k, "jump": pose_jump_k, "fly": pose_fly_k}

KATSURA_SHEATH = make_sheath(saya=(40, 44, 74), saya_hi=(84, 92, 140))

KATSURA = register(LayeredChibi(
    id="katsura", name="桂", color=(58, 84, 160), voice=0.92,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=(240, 236, 222), sleeve_b=(186, 180, 160), sleeve_frac=0.7,
    hand=(255, 220, 190),
    leg_len=7, leg_w=3, leg_gap=4, pants=(48, 58, 100), shoes=(34, 30, 40),
    weapon="katana", weapon_len=17, sheathed=KATSURA_SHEATH,
    poses=KATSURA_POSES,
    behind=katsura_hair_back,
    desc="攘夷志士首领。黑长直，一脸正经的天然呆，口头禅『不是假发，是桂！』，擅长逃跑和扔炸弹。",
))
