"""吉田松阳 Yoshida Shouyou — gentle sensei of Shoukasonjuku.

Long light-brown hair tied loosely low at the back (tail drawn BEHIND the body),
closed-eye smile, pale-green haori over a beige kimono, katana at the hip.
Extras: pose `headbutt` (p-driven: wind-up -> SLAM with a smile -> impact star),
pose `smile`; exprs `smile`, `determined`.
"""
from PIL import Image

from engine.core import step_frame, clamp, lerp, ease_out, ease_in_out
from engine.gfx import INK, stamp_line, scale_nearest, shade
from chars import register
from chars.rig import ChibiDef, POSES, default_params, compose, _rotate_about, CW, CH, OX, OY, \
    pose_idle, _blink

# ------------------------------------------------------------------ palette
HAIR_L, HAIR_M, HAIR_D = (222, 194, 150), (184, 150, 108), (134, 100, 72)
HAIR_HI = (246, 228, 190)
HEAD_PAL = {
    "o": INK,
    "L": HAIR_HI,
    "H": HAIR_L,
    "h": HAIR_M,
    "d": HAIR_D,
    "S": (255, 220, 190),   # skin (fair)
    "s": (236, 178, 150),   # skin shade
    "E": (92, 164, 118),    # soft green eyes
    "e": (50, 100, 70),
    "w": (255, 255, 255),
    "m": (150, 64, 72),     # mouth
    "n": (222, 140, 132),   # soft smile corners
    "b": (250, 160, 150),   # blush
    "T": (120, 200, 255),   # tears
}

BASE = [
    "......oooooo......",   # 0
    "....ooHHHHHHoo....",   # 1
    "...oHHHLLLHHHHo...",   # 2
    "..oHHLLHHHHLLHHo..",   # 3  silky highlight ring
    ".odHLHHHhHHHHHhHo.",   # 4
    "odhHHHHhHHHHhHHhHo",   # 5  strands
    "odhHHHHhHHHHhHHHho",   # 6
    "odhHHHhHHHHhHHHhho",   # 7
    "odhHHHhHHSHhHHhHho",   # 8  bangs, parted
    "odhHHhSHSSShHSShho",   # 9
    "odhHhSSSSSSSSSSSho",   # 10 brow row
    "odhHSSSoSSSSoSSHho",   # 11 closed-eye smile ^ ^
    "odhHSSoSoSSoSoSHho",   # 12
    "odhhSSSSSSSSSSShdo",   # 13
    "odhhsSSSSnSSnSshdo",   # 14 soft smile
    "odhdosSSSSmmSsohdo",   # 15
    "odhdo.ooooooo.ohdo",   # 16 chin; long side locks keep going
    ".odho........ohdo.",   # 17
    "..oo..........oo..",   # 18
]


def _head(**rows):
    r = list(BASE)
    for k, v in rows.items():
        i = int(k[1:])
        assert len(v) == len(BASE[i]), (k, v, len(v), len(BASE[i]))
        r[i] = v
    return "\n".join(r)


OPEN = dict(r11="odhHSSoooSSoooSHho", r12="odhHSSwEESSwEESHho")          # open green eyes
HEADS = {
    "normal": _head(),
    "blink": _head(r11="odhHSSSSSSSSSSSHho", r12="odhHSSoooSSoooSHho"),
    "talk": _head(r14="odhhsSSSSSooSSshdo", r15="odhdosSSSSmmSsohdo"),
    "smile": _head(r13="odhhSbbSSSSbbSShdo"),
    "happy": _head(r13="odhhSbbSSSSbbSShdo", r14="odhhsSSSSooooSshdo", r15="odhdosSSSSmmSsohdo"),
    "determined": _head(r10="odhHHSSSSSSSSSSSho", r11="odhHSSoooSSoooSHho",
                        r12="odhHSSEEeSSEEeSHho", r14="odhhsSSSSSmmSSshdo", r15="odhdosSSSSSSSsohdo"),
    "angry": _head(r10="odhHHoSSSSSSSoSSho", r11="odhHSSoooSSoooSHho",
                   r12="odhHSSEEwSSEEwSHho", r14="odhhsSSSSSmmSSshdo", r15="odhdosSSSSSSSsohdo"),
    "shout": _head(r10="odhHHoSSSSSSSoSSho", r11="odhHSSoooSSoooSHho",
                   r12="odhHSSEEwSSEEwSHho", r13="odhhSSSSSSooSSShdo",
                   r14="odhhsSSSSomoSSshdo", r15="odhdosSSSSooSsohdo"),
    "shock": _head(r11="odhHSSooSSSooSSHho", r12="odhHSowwoSowwoSHho",
                   r13="odhhSSooSSSooSShdo", r14="odhhsSSSSSooSSshdo", r15="odhdosSSSSooSsohdo"),
    "sad": _head(r10="odhHHSSoSSSoSSSSho", r11="odhHSSooSSSSooSHho",
                 r12="odhHSSwEESSwEESHho", r14="odhhsSSSSSSSSSshdo", r15="odhdosSSSSmmSsohdo"),
    # the famous smile with tears ("谢谢你")
    "cry": _head(r12="odhHSSoToSSoToSHho", r13="odhhSSSTSSSSTSShdo",
                 r14="odhhsSSTSnSSnSshdo", r15="odhdosSTSSmmSsohdo"),
    "hurt": _head(r11="odhHSSoSoSSoSoSHho", r12="odhHSSSoSSSSoSSHho",
                  r13="odhhSSoSoSSoSoShdo", r14="odhhsSSSSSooSSshdo", r15="odhdosSSSSmmSsohdo"),
    "smug": _head(r14="odhhsSSSSSSSSmshdo", r15="odhdosSSSSmmmsohdo"),
    "sleep": _head(r11="odhHSSSSSSSSSSSHho", r12="odhHSSoooSSoooSHho",
                   r14="odhhsSSSSSSSSSshdo", r15="odhdosSSSSmSSsohdo"),
}
HEAD_ANCHOR = (9, 16)

TORSO_PAL = {
    "o": INK,
    "G": (196, 216, 174),   # pale sage-green haori
    "g": (156, 180, 138),
    "q": (116, 140, 104),
    "C": (250, 242, 220),   # beige/cream kimono
    "c": (214, 200, 168),
    "B": (86, 92, 118),     # obi
    "b": (120, 128, 156),
}

TORSO = """
....oooooo....
...oCCCCCCo...
..oGGCCCCgGo..
.oGGGGCCcgGgo.
.oGGGGGCcgGgo.
.oGGGGGCCgGqo.
.oGGGGBbBBgqo.
.oGgGGGCcgGqo.
.oGgGGGCcgGqo.
.oGgGGGCcggqo.
.ogqgGGCcgqqo.
..oooooooooo..
"""

HAKAMA = (104, 112, 132)


def sheathed_katana(img, torso_xy, torso_size):
    """Katana in a black-lacquer scabbard at the left hip (handle forward)."""
    tx, ty = torso_xy
    a, b = (tx + 13, ty + 6), (tx - 7, ty + 10)
    stamp_line(img, a, b, 4, INK)
    stamp_line(img, a, b, 2, (66, 50, 62))
    stamp_line(img, (tx + 6, ty + 7), (tx - 6, ty + 9.4), 1, (122, 100, 118))  # lacquer shine
    stamp_line(img, a, (tx + 10, ty + 6.6), 2, (206, 204, 214))      # white-wrapped hilt
    stamp_line(img, (tx + 11, ty + 6.4), (tx + 11, ty + 6.4), 1, (70, 64, 92))
    stamp_line(img, (tx + 9, ty + 5.5), (tx + 9, ty + 8), 1, (232, 184, 70))   # tsuba


def back_hair(img, ctx):
    """Long hair tied loosely low at the back: hangs behind the shoulders."""
    hx, hy, hw, hh = ctx["head"]
    t = ctx["t"]
    pp = ctx["params"]
    sway = 0
    if pp["legs"] in ("walk", "run"):
        sway = -1 if step_frame(t, 6, 2) else 0
        if pp["legs"] == "run":
            sway -= 1
    x0, y0 = hx + 3, hy + 12
    x1, y1 = hx + 2 + sway, hy + 24
    stamp_line(img, (x0, y0), (x1, y1), 6, INK)
    stamp_line(img, (x0, y0), (x1, y1), 4, HAIR_M)
    stamp_line(img, (x0 - 1, y0), (x1 - 1, y1 - 1), 1, HAIR_D)
    stamp_line(img, (x0 + 1, y0 + 2), (x1 + 1, y1 - 2), 1, HAIR_L)
    # loose tie
    stamp_line(img, (x0 - 1, y0 + 4), (x0 + 2, y0 + 4), 1, (110, 128, 96))


class LayeredDef(ChibiDef):
    """ChibiDef + extras shared by the chars_D characters (also imported by
    gintoki_kid / katsura_kid / takasugi_kid / okada_nizo / tsukuyo / hinowa / seita):

      * back_layers : callables(img, ctx) drawn BEHIND the whole body (hair tails,
                      wheelchair, swords leaning on the back...). A pose can add
                      more through pp["back_props"].
      * pp["pivot"] = "feet" rotates `rot` about the feet instead of the torso.
      * portrait_crop : dialogue portrait = head rows [0, n) (or (top, bottom)), x2.
    """

    def __init__(self, *a, back_layers=(), portrait_crop=None, **k):
        super().__init__(*a, **k)
        self.back_layers = tuple(back_layers)
        self.portrait_crop = portrait_crop

    def render(self, pose="idle", t=0.0, p=None, expr=None, **kw):
        fn = self.poses.get(pose) or POSES.get(pose) or POSES["idle"]
        pp = default_params()
        fn(pp, t, p if p is not None else (t % 1.0), self)
        pp.update({k: v for k, v in kw.items() if k in pp})
        if expr is not None:
            pp["expr"] = expr
        body = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        ctx = compose(self, body, pp, t)
        img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        for layer in self.back_layers + tuple(pp.get("back_props", ())):
            layer(img, ctx)
        img.alpha_composite(body)
        for prop in pp["props"]:
            prop(img, ctx)
        ax, ay = OX, OY
        if pp["rot"]:
            cy = OY - 1 if pp.get("pivot") == "feet" else OY - 14
            img, ax, ay = _rotate_about(img, pp["rot"], OX, cy, OX, OY)
        return img, ax, ay

    def portrait_fn(self, expr, t, talking):
        e = expr or "normal"
        if talking and step_frame(t, 8) % 2 == 0:
            e = "talk" if expr in (None, "normal", "smile") else e
        elif expr is None and (t % 3.1) < 0.12:
            e = "blink"
        h = self.head(e)
        if self.portrait_crop:
            top, bot = self.portrait_crop if isinstance(self.portrait_crop, tuple) else (0, self.portrait_crop)
            h = h.crop((0, top, h.width, min(h.height, bot)))
        return scale_nearest(h, 2)


# ------------------------------------------------------------------ props & poses
def _impact_star(img, ctx):
    """Little comic impact burst in front of the forehead."""
    hx, hy, hw, hh = ctx["head"]
    cx, cy = int(hx + hw + 2), int(hy + 5)
    k = ctx["params"].get("impact", 0)
    if k <= 0:
        return
    r = 2 + int(3 * k)
    for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1), (0.7, 0.7), (0.7, -0.7), (-0.7, 0.7), (-0.7, -0.7)):
        rr = r if dx == 0 or dy == 0 else r - 1
        stamp_line(img, (cx, cy), (cx + dx * rr, cy + dy * rr), 3, INK)
    for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1), (0.7, 0.7), (0.7, -0.7), (-0.7, 0.7), (-0.7, -0.7)):
        rr = r if dx == 0 or dy == 0 else r - 1
        stamp_line(img, (cx, cy), (cx + dx * rr, cy + dy * rr), 1, (255, 236, 110))
    stamp_line(img, (cx, cy), (cx, cy), 2, (255, 255, 255))


def pose_headbutt(pp, t, p, d):
    """Signature sensei headbutt, delivered with a gentle smile.
    p: 0-0.35 lean back, 0.35-0.5 SLAM forward, 0.5-1 hold + impact star.
    (kw impact=0 hides the star)."""
    pp["expr"] = "smile"
    pp["props"] = [_impact_star]
    pp["impact"] = 0
    if p < 0.35:
        k = ease_out(p / 0.35)
        pp["lean"] = int(round(lerp(0, -2, k)))
        pp["head_dx"] = int(round(lerp(0, -2, k)))
        pp["head_dy"] = -1 if k > 0.5 else 0
        pp["arm_f"] = lerp(10, 40, k)
        pp["arm_b"] = lerp(-10, 30, k)
        pp["legs"] = "spread"
    elif p < 0.5:
        k = ease_in_out((p - 0.35) / 0.15)
        pp["lean"] = int(round(lerp(-2, 3, k)))
        pp["head_dx"] = int(round(lerp(-2, 4, k)))
        pp["head_dy"] = int(round(lerp(-1, 2, k)))
        pp["arm_f"] = lerp(40, -30, k)
        pp["arm_b"] = lerp(30, -45, k)
        pp["legs"] = "lunge"
    else:
        k = (p - 0.5) / 0.5
        pp["lean"] = 3
        pp["head_dx"] = 4
        pp["head_dy"] = 2
        pp["bob"] = 1 if k < 0.2 else 0
        pp["arm_f"] = -30
        pp["arm_b"] = -45
        pp["legs"] = "lunge"
        pp["impact"] = 1.0 - k * 0.8 if k < 0.7 else 0


def pose_smile(pp, t, p, d):
    """Warm teacher smile, hands tucked into the sleeves."""
    pose_idle(pp, t, p, d)
    pp["arm_f"] = 55
    pp["arm_b"] = 50
    pp["expr"] = "blink" if _blink(t, 3.7) else "smile"


SHOUYOU = register(LayeredDef(
    id="shouyou", name="松阳", color=(112, 150, 98), voice=0.9,
    heads=HEADS, head_pal=HEAD_PAL, head_anchor=HEAD_ANCHOR,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=(196, 216, 174), sleeve_b=(140, 164, 124), sleeve_frac=0.7,
    hand=(255, 220, 190),
    leg_len=7, leg_w=3, leg_gap=4, pants=HAKAMA, shoes=(58, 46, 44),
    weapon="katana", weapon_len=17, sheathed=sheathed_katana,
    poses={"headbutt": pose_headbutt, "smile": pose_smile},
    back_layers=(back_hair,), portrait_crop=17,
    desc="松下私塾的老师。亚麻色长发低束，总是温柔地眯眼微笑，教孩子们何为武士之魂。",
))
