"""奈落 Naraku — Tendoshu assassin (天照院奈落).

Huge woven bamboo kasa hat hiding the eyes (face in shadow, eyes only glint when
angry), black robes with a crow-feather mantle over the shoulders, katana.
Extra poses: `ambush` (low crouch, blade held back, ready to spring),
`leap` (airborne, blade raised), `stand_guard` (motionless, hands in sleeves).
"""
from engine.core import step_frame
from engine.gfx import INK, stamp_line, pset, scale_nearest
from chars import register
from chars.rig import ChibiDef, pose_idle, _blink

HEAD_PAL = {
    "o": INK,
    "T": (214, 186, 124),   # bamboo straw light
    "t": (172, 142, 90),    # straw mid
    "u": (126, 100, 62),    # straw shade / weave lines
    "U": (88, 66, 44),      # brim underside
    "K": (34, 30, 46),      # deep shadow on the face
    "k": (70, 54, 64),      # shadow fading
    "d": (52, 44, 62),      # shadow edge
    "S": (214, 180, 160),   # lower face (shadowed skin)
    "s": (170, 136, 124),
    "m": (60, 30, 40),      # mouth
    "R": (255, 50, 60),     # glowing eyes (angry)
    "r": (150, 30, 40),
    "w": (255, 255, 255),
    "W": (230, 230, 236),
    "B": (120, 200, 255),   # tear
}

# 24 wide x 16 tall; chin row 15 -> head_anchor (12, 15)
BASE = [
    "..........oooo..........",   # 0  hat apex
    "........ooTTttoo........",   # 1
    "......ooTTTutttuoo......",   # 2
    "....ooTTTuTTttutttoo....",   # 3
    "..ooTTTuTTTTttuttuuuoo..",   # 4
    "ooTTTuTTTTTttttuttuuuuoo",   # 5
    "ouuUuuuUuuuuUuuuuUuuuuUo",   # 6  brim edge
    ".oooooooooooooooooooooo.",   # 7
    "...odKKKKKKKKKKKKKKdo...",   # 8  face in shadow
    "...odKKKKKKKKKKKKKKdo...",   # 9  (eyes hidden)
    "...odKKKKKKKKKKKKKKdo...",   # 10
    "....okkkkkkkkkkkkkko....",   # 11
    "....oskSSSSSSSSSSkso....",   # 12
    ".....osSSSSSmmSSSso.....",   # 13 mouth
    "......oosSSSSSSsoo......",   # 14
    "........oooooooo........",   # 15
]
for _i, _r in enumerate(BASE):
    assert len(_r) == 24, (_i, _r, len(_r))


def _head(**rows):
    r = list(BASE)
    for k, v in rows.items():
        i = int(k[1:])
        assert len(v) == len(BASE[i]), (k, v, len(v))
        r[i] = v
    return "\n".join(r)


def _put(i, **cols):
    """Row i of BASE with single pixels replaced: _put(9, c8='R')."""
    r = list(BASE[i])
    for k, v in cols.items():
        r[int(k[1:])] = v
    return "".join(r)


HEADS = {
    "normal": _head(),
    "blink": _head(),
    "talk": _head(r13=".....osSSSSSooSSSso.....", r14="......oosSSSmmSsoo......"),
    "angry": _head(r9=_put(9, c8="R", c9="r", c14="R", c15="r"),
                   r13=".....osSSSSooooSSso....."),
    "shout": _head(r9=_put(9, c8="R", c9="r", c14="R", c15="r"),
                   r12="....oskSSSSooooSSkso....",
                   r13=".....osSSSSommoSSso.....", r14="......oosSSSooSsoo......"),
    "shock": _head(r9=_put(9, c8="w", c9="w", c14="w", c15="w"),
                   r13=".....osSSSSSoSSSSso....."),
    "happy": _head(r13=".....osSSSSoSSoSSso.....", r14="......oosSSSooSsoo......"),
    "sad": _head(r13=".....osSSSSSooSSSso.....", r14="......oosSSoSSoSoo......"),
    "cry": _head(r10=_put(10, c8="B", c14="B"), r11=_put(11, c8="B", c14="B"),
                 r12=_put(12, c8="B", c14="B"), r13=".....osSSSSSooSSSso....."),
    "hurt": _head(r9=_put(9, c8="r", c9="r", c14="r", c15="r"), r13=".....osSSSwWwWSSSso....."),
    "smug": _head(r13=".....osSSSSSSSmSSso.....", r14="......oosSSSSmmsoo......"),
}
HEADS["determined"] = HEADS["angry"]

TORSO_PAL = {
    "o": INK,
    "K": (42, 40, 58),      # black robe
    "k": (28, 26, 40),      # robe shade
    "l": (74, 72, 98),      # robe highlight
    "F": (98, 110, 162),    # crow feathers (blue-black sheen)
    "f": (60, 66, 108),
    "g": (38, 40, 70),
    "W": (214, 214, 226),   # white under-collar
    "R": (116, 36, 48),     # dark red cord
    "S": (214, 180, 160),
}

TORSO = """
....oooooo....
..ooFFWWFFoo..
.oFFFfWWfFFFo.
oFFfFfKWKfFfFo
ofFgFgKWKgFgfo
.ogofoKKWofogo
..oolKKKWKKoo.
.oRRRRRRRRRRo.
.olKKKKKKKKko.
.okKKKKKKKkko.
.okKkKkKkKkko.
..oooooooooo..
"""


def sheathed_katana(img, torso_xy, torso_size):
    tx, ty = torso_xy
    a, b = (tx + 12, ty + 6), (tx - 4, ty + 10)
    stamp_line(img, a, b, 4, INK)
    stamp_line(img, (tx + 9, ty + 6.8), b, 2, (24, 22, 32))
    stamp_line(img, a, (tx + 9, ty + 6.8), 2, (180, 170, 180))
    pset(img, tx + 9, ty + 6, (160, 150, 120))


def pose_idle_naraku(pp, t, p, d):
    """Motionless, faceless; only the robe breathes."""
    f = step_frame(t, 3, 4)
    pp["bob"] = -1 if f == 1 else 0
    pp["arm_f"] = 8
    pp["arm_b"] = -8
    pp["expr"] = "normal"


def pose_stand_guard(pp, t, p, d):
    pose_idle_naraku(pp, t, p, d)
    pp["arm_f"] = 60
    pp["arm_b"] = 55


def pose_ambush(pp, t, p, d):
    """Low crouch, blade held back in reverse, about to spring (eyes glint)."""
    f = step_frame(t, 4, 2)
    pp["legs"] = "kneel"
    pp["lean"] = 2
    pp["arm_f"] = 40
    pp["weapon"] = 195
    pp["arm_b"] = 60
    pp["bob"] = -1 if f else 0
    pp["expr"] = "angry"


def pose_leap(pp, t, p, d):
    """Airborne strike: body tucked, katana raised overhead."""
    pp["legs"] = "jump"
    pp["arm_f"] = 165
    pp["weapon"] = 120
    pp["arm_b"] = 120
    pp["lean"] = 1
    pp["expr"] = "angry"


class NarakuDef(ChibiDef):
    def portrait_fn(self, expr, t, talking):
        e = expr or "normal"
        if talking and step_frame(t, 8) % 2 == 0:
            e = "talk" if expr in (None, "normal") else e
        h = self.head(e).crop((1, 0, 23, 16))
        return scale_nearest(h, 2)


NARAKU = register(NarakuDef(
    id="naraku", name="奈落", color=(148, 58, 72), voice=0.7,
    heads=HEADS, head_pal=HEAD_PAL, head_anchor=(12, 15),
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=(42, 40, 58), sleeve_b=(28, 26, 40), sleeve_frac=0.75,
    hand=(214, 180, 160),
    leg_len=7, leg_w=3, leg_gap=4, pants=(36, 34, 50), shoes=(22, 20, 30), shoe_h=2,
    weapon="katana", weapon_len=16, sheathed=sheathed_katana,
    poses={"idle": pose_idle_naraku, "ambush": pose_ambush, "leap": pose_leap,
           "stand_guard": pose_stand_guard},
    desc="天照院奈落的杀手。斗笠遮面、一身黑衣，乌鸦为记，幕府背后的暗杀集团。",
))
