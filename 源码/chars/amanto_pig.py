"""天人(猪) — pig-faced amanto thug (the bullies of episode 1).

Big pink pig head: pointy ears, bristle tuft, beady angry eyes, huge snout with
nostrils, white tusks.  Dark armour with metal shoulder pads, katana at the hip.
Extra poses: `laugh` (belly laugh, pointing), `bully` (leaning in, fist raised).
"""
import math

from engine.core import step_frame
from engine.gfx import INK, stamp_line, rect, pset
from chars import register
from chars.rig import ChibiDef, pose_idle, pose_point, _blink

HEAD_PAL = {
    "o": INK,
    "P": (244, 166, 178),   # pig skin
    "p": (206, 116, 138),   # shade
    "L": (255, 204, 208),   # light
    "N": (255, 196, 204),   # snout
    "n": (224, 138, 156),   # snout shade
    "K": (70, 44, 50),      # bristles
    "k": (116, 76, 72),
    "W": (250, 246, 226),   # tusks
    "w": (255, 255, 255),
    "E": (30, 22, 30),      # beady eyes
    "r": (230, 60, 60),     # angry red eye glint
    "m": (130, 40, 60),     # mouth inside
    "T": (120, 200, 255),   # tears
    "B": (80, 120, 220),    # gloom
}

BASE = [
    "..oo....oo...oo...",   # 0  ear tips + tuft
    ".oLpo..oKKo.oPpo..",   # 1
    ".oPPpooKkKKopPPo..",   # 2
    ".oPPPPPLLPPPPPPPo.",   # 3
    "opPPLLLLPPPPPPPPPo",   # 4
    "opPLLPPPPPPPPPPPPo",   # 5
    "opPPPPPPPPPPPPPPPo",   # 6
    "opPPooPPPPPPPooPPo",   # 7  brows
    "opPPPPooPPPPoPPPPo",   # 8
    "opPPPwEPPPPPwEPPPo",   # 9  beady eyes
    "opPPPPPPooooooPPPo",   # 10 snout top
    "opPppPPoNNNNNNoPPo",   # 11
    "opPPPPPoNoNNoNoPPo",   # 12 nostrils
    ".opPWPPonNNNNnoPo.",   # 13 tusks up
    ".opPWPPPooooooWPo.",   # 14
    "..opmmmmmmmmmmpo..",   # 15 mouth
    "...oooooooooooo...",   # 16
]
for _i, _r in enumerate(BASE):
    assert len(_r) == 18, (_i, _r, len(_r))


def _head(**rows):
    r = list(BASE)
    for k, v in rows.items():
        i = int(k[1:])
        assert len(v) == len(BASE[i]), (k, v, len(v))
        r[i] = v
    return "\n".join(r)


HEADS = {
    "normal": _head(),
    "blink": _head(r9="opPPPooPPPPPooPPPo"),
    "talk": _head(r15="..opmmmmmoommmpo..", r14=".opPWPPPoooooooWo."),
    "angry": _head(r7="opPPoPPPPPPPPPoPPo", r8="opPPPooPPPPPooPPPo", r9="opPPPwrPPPPPwrPPPo"),
    "shout": _head(r7="opPPoPPPPPPPPPoPPo", r8="opPPPooPPPPPooPPPo", r9="opPPPwrPPPPPwrPPPo",
                   r14=".opPWPPPoooooooWo.", r15="..opmmmmmmmmmmpo..", r16="...ommmmmmmmmmo..."),
    "shock": _head(r7="opPPPPPPPPPPPPPPPo", r8="opPPoooPPPPoooPPPo", r9="opPPowoPPPPowoPPPo",
                   r10="opPPoooPooooooPPPo", r15="..opmmmmoommmmpo.."),
    "happy": _head(r7="opPPPPPPPPPPPPPPPo", r8="opPPPoPPPPPPoPPPPo", r9="opPPoPoPPPPoPoPPPo",
                   r15="..opmmwwwwwwmmpo.."),
    "sad": _head(r7="opPPPPPPPPPPPPPPPo", r8="opPPPPooPPPooPPPPo", r9="opPPoEPPPPPPoEPPPo"),
    "cry": _head(r7="opPPPPPPPPPPPPPPPo", r8="opPPPPooPPPooPPPPo", r9="opPPTTTPPPPTTTPPPo",
                 r10="opPPPTPPooooooPPPo", r11="opPpTPPoNNNNNNoPPo"),
    "hurt": _head(r7="opPPPPPPPPPPPPPPPo", r8="opPPoPoPPPPoPoPPPo", r9="opPPPoPPPPPPoPPPPo",
                  r10="opPPoPoPooooooPPPo"),
    "smug": _head(r8="opPPPPPPPPPPPPPPPo", r9="opPPPooEPPPooEPPPo",
                  r15="..opmmmmmmmmwwpo.."),
    "gloom": _head(r3=".oPPPBPPBPPBPPPPo.", r4="opPPBPPBPPBPPPPPPo", r5="opPPPBPPBPPBPPPPPo"),
}

TORSO_PAL = {
    "o": INK,
    "P": (244, 166, 178),   # neck skin
    "A": (104, 72, 64),     # leather armour
    "a": (74, 50, 46),
    "l": (146, 104, 86),    # leather highlight
    "M": (184, 192, 212),   # metal plates
    "m": (122, 130, 156),
    "H": (230, 236, 246),   # metal highlight
    "R": (170, 52, 58),     # red sash
    "r": (120, 34, 44),
    "Y": (230, 186, 70),    # rivets / buckle
}

# 16 wide: bulkier thug than the 14 px heroes
TORSO = """
.....oooooo.....
..oooPPPPPPooo..
.oHHMooPPooMHHo.
oHMMMmoAAoMMMmmo
ommmmoAllAommmmo
.ooooAlAAAAoooo.
...oAlMMHMAAo...
...oAAMMMMAao...
...oRRRYYRRro...
...oAaAaAaAao...
...oaAaAaAaao...
....oooooooo....
"""


def sheathed_katana(img, torso_xy, torso_size):
    """Scabbard on the left hip: handle forward, sheath sloping back."""
    tx, ty = torso_xy
    a, b = (tx + 12, ty + 8), (tx - 3, ty + 12)
    stamp_line(img, a, b, 4, INK)
    stamp_line(img, (tx + 9, ty + 8.8), b, 2, (60, 48, 58))
    stamp_line(img, a, (tx + 9, ty + 8.8), 2, (200, 190, 170))
    pset(img, tx + 9, ty + 8, (230, 180, 60))


def pose_laugh(pp, t, p, d):
    """GUHAHAHA — head thrown back, belly shaking, pointing at the victim."""
    f = step_frame(t, 10, 2)
    pp["arm_f"] = 95 + (5 if f else 0)
    pp["arm_b"] = 30
    pp["lean"] = -1
    pp["head_dx"] = -1
    pp["head_dy"] = -1 if f else 0
    pp["bob"] = -1 if f else 0
    pp["expr"] = "happy" if f else "shout"


def pose_bully(pp, t, p, d):
    """Looming over someone: leaning in, fist raised, snarling."""
    f = step_frame(t, 4, 2)
    pp["arm_f"] = 150 + (8 if f else 0)
    pp["arm_b"] = 40
    pp["lean"] = 2
    pp["head_dx"] = 1
    pp["legs"] = "spread"
    pp["bob"] = -1 if f else 0
    pp["expr"] = "shout" if f else "angry"


def pose_idle_thug(pp, t, p, d):
    pose_idle(pp, t, p, d)
    pp["arm_f"] = 18 + (2 if pp["bob"] else 0)
    pp["arm_b"] = -18
    pp["expr"] = "blink" if _blink(t, 2.7) else "angry"


AMANTO_PIG = register(ChibiDef(
    id="amanto_pig", name="天人(猪)", color=(206, 96, 122), voice=0.66,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(8, 2), hip=(8, 9), shoulder_f=(12, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=3, sleeve_f=(104, 72, 64), sleeve_b=(74, 50, 46), sleeve_frac=0.6,
    hand=(244, 166, 178),
    leg_len=7, leg_w=4, leg_gap=5, pants=(70, 56, 70), shoes=(40, 32, 40), shoe_h=2,
    weapon="katana", weapon_len=16, sheathed=sheathed_katana,
    poses={"idle": pose_idle_thug, "laugh": pose_laugh, "bully": pose_bully},
    desc="猪脸天人打手。仗着天人身份在江户横行霸道，看不起『地球猴子』。",
))
