"""高杉晋助 Takasugi Shinsuke — dark purple hair, bandage over his LEFT eye
(screen-right when facing right), flamboyant purple kimono with golden
butterflies, kiseru pipe, cold smirk.

Extra poses:
  smoke    : standing, kiseru at the mouth, smoke curling from the bowl
  sit_rail : sitting on a ship railing (one knee up) smoking. The pose draws a
             short wooden railing itself; feet anchor = the deck (rail top is
             14 px above it). Pass rail=False to draw_char to omit the railing
             (then put the anchor 14 px below your own rail top).
"""
import math

from engine.core import step_frame, clamp, lerp, rng
from engine.gfx import INK, stamp_line, rect, pset, shade
from chars import register
from chars.rig import OY, pose_idle, _blink
from chars.katsura import LayeredChibi, make_head_builder, make_sheath

HEAD_PAL = {
    "o": INK,
    "L": (112, 92, 162),    # hair highlight
    "H": (72, 54, 116),     # dark purple hair (darker than the violet kimono)
    "h": (52, 38, 90),      # hair shade
    "d": (36, 26, 64),      # deep shade
    "S": (255, 224, 200),   # pale skin
    "s": (232, 178, 152),
    "E": (70, 160, 120),    # green eye
    "e": (28, 72, 58),
    "w": (255, 255, 255),
    "m": (160, 70, 84),
    "B": (246, 246, 250),   # bandage
    "b": (196, 198, 216),   # bandage shade
    "T": (120, 200, 255),
    "k": (250, 156, 156),
}

BASE = [
    "....oo...oo.......",   # 0
    "...oHHo.oHHo.oo...",   # 1
    "..oHHHHooHHHoHHo..",   # 2
    "..oHHLLHHHHHHHHHo.",   # 3
    ".oHHLHHHHHHHHHHHho",   # 4
    "odHHHHHHHHHHHHHHho",   # 5
    "odHHHHHHHhHHHHHHho",   # 6
    "odhHHHhHHHHhHHHHHo",   # 7
    "odHHHHSHHhHSHHHHbo",   # 8  bangs
    "odHHhSSHSSHSSHBBbo",   # 9  bandage starts
    "odHhSSSSShSSBBBBbo",   # 10
    "odHSSooooSSBBbBBbo",   # 11 heavy lid | bandage over left eye
    ".oHSSSwEeSSBBBBbo.",   # 12 cold green eye
    ".ohSSSSSSSSSBBbbo.",   # 13
    "..osSSSSSSmmmSSo..",   # 14 thin smirk
    "...oosSSSSSSSsoo..",   # 15
    ".....ooooooooo....",   # 16
]
_head = make_head_builder(BASE)

HEADS = {
    "normal": _head(),
    "blink": _head(r11="odHSSSSSSSSBBbBBbo", r12=".oHSSSooooSBBBBbo."),
    "talk": _head(r14="..osSSSSSSooSSSo..", r15="...oosSSSSmmSsoo.."),
    "angry": _head(r10="odHhSoSSShSSBBBBbo", r11="odHSSSoooSSBBbBBbo",
                   r12=".oHSSSwEeSSBBBBbo.", r14="..osSSSSSSooSSSo.."),
    "determined": _head(r10="odHhSoSSShSSBBBBbo", r11="odHSSSoooSSBBbBBbo"),
    "shout": _head(r10="odHhSoSSShSSBBBBbo", r11="odHSSSoooSSBBbBBbo",
                   r13=".ohSSSSSSooooBbbo.", r14="..osSSSSSomwoSSo..",
                   r15="...oosSSSSoooSoo.."),
    "shock": _head(r11="odHSSoooSSSBBbBBbo", r12=".oHSSowoSSSBBBBbo.",
                   r13=".ohSSoooSSSSBBbbo.", r14="..osSSSSSSooSSSo.."),
    "happy": _head(r11="odHSSSSSSSSBBbBBbo", r12=".oHSSoSSoSSBBBBbo.",
                   r13=".ohSSSooSSSSBBbbo.", r14="..osSSSSSmSSmSSo..",
                   r15="...oosSSSSmmSsoo.."),
    "sad": _head(r10="odHhSSSoShSSBBBBbo", r11="odHSSooSSSSBBbBBbo",
                 r12=".oHSSSwEeSSBBBBbo.", r14="..osSSSSSSSSSSSo..",
                 r15="...oosSSSSmmSsoo.."),
    "cry": _head(r10="odHhSSSoShSSBBBBbo", r11="odHSSooSSSSBBbBBbo",
                 r12=".oHSSSTTTSSBBBBbo.", r13=".ohSSSTSSSSSBBbbo.",
                 r14="..osSSTSSSmmSSSo..", r15="...oosTSSSSSSsoo.."),
    "hurt": _head(r11="odHSSoSoSSSBBbBBbo", r12=".oHSSSoSSSSBBBBbo.",
                  r13=".ohSSoSoSSSSBBbbo.", r14="..osSSSSSSooSSSo.."),
    "smug": _head(r11="odHSSSSSSSSBBbBBbo", r12=".oHSSooooSSBBBBbo.",
                  r13=".ohSSSSSSSSSBBbbo.", r14="..osSSSSSSSSSmSo..",
                  r15="...oosSSSmmmmsoo.."),
    "sleep": _head(r11="odHSSSSSSSSBBbBBbo", r12=".oHSSSooooSBBBBbo."),
}

TORSO_PAL = {
    "o": INK,
    "Q": (184, 126, 216),   # kimono highlight
    "P": (146, 84, 182),    # purple kimono
    "p": (106, 56, 140),    # shade
    "S": (255, 224, 200),   # chest skin (loose collar)
    "s": (226, 172, 148),
    "Y": (250, 214, 90),    # golden butterflies
    "y": (196, 146, 52),
    "K": (48, 36, 66),      # obi
    "k": (96, 76, 120),
    "c": (40, 30, 56),      # dark under-collar
}

TORSO = """
....oooooo....
...ocSSSSco...
..oPcSSSScPo..
.oQPPcSScPPpo.
.oPYyPcSPPYpo.
.oPPPPPcPyPpo.
.oKKKkKKKKKKo.
.oPPPYPPPPPpo.
.oQPYyPPPPYpo.
.oPPPPPPPyPpo.
.opYPPPPPPppo.
..oooooooooo..
"""


# ------------------------------------------------------------------ props
def _smoke_wisps(img, x, y, t, n=3, seed=0):
    """Thin pipe smoke curling up from (x, y)."""
    f = step_frame(t, 12)
    for i in range(n):
        life = ((f + i * 7) % 20) / 20.0      # 0..1
        r = rng("taka_smoke", seed, i)
        sx = x + math.sin(life * 5 + i) * 1.5 + life * 3
        sy = y - 1 - life * 12
        col = (230, 226, 240) if life < 0.5 else (190, 186, 206)
        pset(img, sx, sy, col)
        if life < 0.7:
            pset(img, sx + 1, sy - 1, col)
        if 0.3 < life < 0.8:
            pset(img, sx - 1, sy, (205, 200, 220))


def _kiseru_at_mouth(img, ctx):
    hx, hy, hw, hh = ctx["head"]
    mx, my = hx + 12, hy + 14
    bx, by = mx + 9, my + 2
    stamp_line(img, (mx, my), (bx, by), 3, INK)
    stamp_line(img, (mx, my), (bx, by), 1, (70, 44, 56))
    pset(img, mx, my, (220, 180, 60))              # gold mouthpiece
    rect(img, bx - 1, by - 2, 4, 3, INK)            # bowl
    rect(img, bx, by - 1, 2, 1, (230, 186, 64))
    pset(img, bx, by - 2, (255, 120, 60) if step_frame(ctx["t"], 4) % 2 else (255, 190, 80))
    _smoke_wisps(img, bx, by - 3, ctx["t"])


def pose_smoke(pp, t, p, d):
    pose_idle(pp, t, p, d)
    f = step_frame(t, 4, 8)
    pp["arm_f"] = 128
    pp["arm_b"] = -8
    pp["expr"] = "blink" if (_blink(t) or f in (3, 4)) else "normal"
    pp["props"] = [_kiseru_at_mouth]


RAIL_UP = 14   # rail top height above the anchor


def _rail(img, ctx):
    """Short section of a ship's railing: thick top rail on turned balusters."""
    if ctx.get("kw", {}).get("rail", True) is False:
        return
    ox = 48
    top = OY - RAIL_UP
    wood, wood_l, wood_d = (112, 74, 52), (156, 108, 72), (70, 44, 34)
    x0, x1 = ox - 20, ox + 20
    rect(img, x0, OY - 3, x1 - x0, 3, INK)                 # foot rail
    rect(img, x0 + 1, OY - 2, x1 - x0 - 2, 1, wood_d)
    for px in range(x0 + 2, x1 - 2, 6):                    # balusters
        rect(img, px - 1, top + 2, 4, RAIL_UP - 3, INK)
        rect(img, px, top + 3, 2, RAIL_UP - 5, wood_d)
        pset(img, px, top + 6, wood)
    rect(img, x0 - 1, top - 1, x1 - x0 + 2, 5, INK)         # top rail
    rect(img, x0, top, x1 - x0, 3, wood)
    rect(img, x0, top, x1 - x0, 1, wood_l)
    rect(img, x0, top + 2, x1 - x0, 1, (92, 60, 44))


def _leg_seg(img, a, b, w, col):
    stamp_line(img, a, b, w + 2, INK)
    stamp_line(img, a, b, w, col)


def _rail_legs(img, ctx, swing=0):
    """Sitting sideways on the rail: back leg stretched along the rail top,
    front knee drawn up (the classic window-sill pose)."""
    d = ctx["def"]
    hx, hy = ctx["hip"]
    w = d.leg_w
    pc, pb = d.pants, shade(d.pants, 0.8)
    shoe = d.shoes
    # back leg: along the rail
    fb = (hx + 10 + swing * 0.5, hy + 0.5)
    _leg_seg(img, (hx - 1, hy), fb, w, pb)
    stamp_line(img, (fb[0] - 1, fb[1]), (fb[0] + 1, fb[1] - 1), w + 2, INK)
    stamp_line(img, (fb[0] - 1, fb[1]), (fb[0] + 0.5, fb[1] - 1), w - 1, shade(shoe, 0.9))
    # front leg: knee up, foot planted on the rail
    knee = (hx + 7, hy - 5)
    ff = (hx + 10, hy + 0.5)
    _leg_seg(img, (hx + 2, hy), knee, w, pc)
    _leg_seg(img, knee, ff, w, pc)
    stamp_line(img, (knee[0] - 1, knee[1] - 1), (knee[0], knee[1] - 1), 1, shade(pc, 1.25))
    stamp_line(img, (ff[0], ff[1]), (ff[0] + 2, ff[1]), w, INK)
    stamp_line(img, (ff[0], ff[1] - 0.5), (ff[0] + 1, ff[1] - 0.5), 1, shoe)


def pose_sit_rail(pp, t, p, d):
    pose_idle(pp, t, p, d)
    f = step_frame(t, 4, 8)
    pp["legs"] = "custom"
    pp["dy"] = -(RAIL_UP - d.leg_len + 1)
    pp["arm_f"] = 128
    pp["arm_b"] = 15
    pp["bob"] = 0
    pp["expr"] = "blink" if (_blink(t) or f in (3, 4)) else "normal"
    swing = 1 if step_frame(t, 2) % 2 else 0
    pp["behind"] = [_rail]
    pp["props"] = [lambda img, ctx, s=swing: _rail_legs(img, ctx, s), _kiseru_at_mouth]


TAKASUGI = register(LayeredChibi(
    id="takasugi", name="高杉", color=(124, 72, 168), voice=0.74,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=(146, 84, 182), sleeve_b=(106, 56, 140), sleeve_frac=0.75,
    hand=(255, 224, 200),
    leg_len=7, leg_w=3, leg_gap=4, pants=(120, 66, 154), shoes=(36, 28, 40),
    weapon="katana", weapon_len=17,
    sheathed=make_sheath(saya=(40, 30, 50), saya_hi=(90, 70, 110)),
    poses={"smoke": pose_smoke, "sit_rail": pose_sit_rail},
    desc="鬼兵队总督。紫发，左眼缠着绷带，华丽的金蝶紫色和服，叼着烟管冷笑——想毁掉这个世界的男人。",
))
