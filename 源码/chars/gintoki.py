"""坂田银时 Sakata Gintoki — REFERENCE CHARACTER for the chibi style.

Style rules shown here (copy them for every character):
  * head ~18x17 px, torso ~14x12 px, legs 7 px  -> ~34 px tall chibi
  * 1 px INK outline ('o') around every part
  * 2-3 tones per material (light / mid / shade), light from the top-left
  * expressions are row overrides of one base head, so they stay aligned
"""
import math

from engine.core import step_frame, clamp, lerp
from engine.gfx import INK, stamp_line
from chars import register
from chars.rig import ChibiDef, pose_idle, pose_sit, _blink

# ------------------------------------------------------------------ palette
HEAD_PAL = {
    "o": INK,
    "H": (238, 240, 250),   # silver hair light
    "h": (196, 202, 224),   # hair mid
    "d": (146, 152, 188),   # hair shade
    "S": (255, 216, 184),   # skin
    "s": (234, 170, 140),   # skin shade
    "E": (150, 36, 58),     # dead-fish crimson eyes
    "w": (255, 255, 255),
    "m": (170, 70, 80),     # mouth
    "b": (250, 150, 150),   # blush
    "T": (120, 200, 255),   # tears
    "B": (80, 120, 220),    # gloom lines
}

BASE = [
    ".....oo.ooo.oo....",   # 0
    "....oHHoHHHoHHo...",   # 1
    "...oHHHHHHHHHHHo..",   # 2
    "..oHHHHhHHHHHHHHo.",   # 3
    ".odHHHHHHHHHHhHHHo",   # 4
    "odHHHhHHHHHHHHHHHo",   # 5
    "odHHHHHHHHHHHHHHHo",   # 6
    "odhHHHHHHhHHHHHHho",   # 7
    "odHHHSHHSSHHSSHHho",   # 8  bangs
    "odHHSSSHSSSSSHSSHo",   # 9
    "odHSSSSSSSSSSSSSHo",   # 10
    "odHSSoooSSSoooSSHo",   # 11 heavy lids
    ".oHSSwEESSSwEESSo.",   # 12 dead-fish irises
    ".ohSSSSSSSSSSSSso.",   # 13
    "..osSSSSSSmmSSSo..",   # 14 mouth
    "...oosSSSSSSSsoo..",   # 15
    ".....ooooooooo....",   # 16
]


def _head(**rows):
    r = list(BASE)
    for k, v in rows.items():
        i = int(k[1:])
        assert len(v) == len(BASE[i]), (k, v, len(v))
        r[i] = v
    return "\n".join(r)


HEADS = {
    "normal": _head(),
    "blink": _head(r11="odHSSSSSSSSSSSSSHo", r12=".oHSSoooSSSoooSSo."),
    "talk": _head(r14="..osSSSSSSooSSSo..", r15="...oosSSSSmmSsoo.."),
    "angry": _head(r10="odHSoSSSSSSSSSoSHo", r11="odHSSoooSSSoooSSHo",
                   r12=".oHSSEEwSSSEEwSSo.", r13=".ohSSEESSSSEESSso."),
    "shout": _head(r10="odHSoSSSSSSSSSoSHo", r11="odHSSoooSSSoooSSHo",
                   r12=".oHSSEEwSSSEEwSSo.", r13=".ohSSSSSSSoooSSso.",
                   r14="..osSSSSSSomoSSo..", r15="...oosSSSSooSsoo.."),
    "shock": _head(r11="odHSoooSSSoooSSSHo", r12=".oHSowwoSowwoSSSo.",
                   r13=".ohSoooSSoooSSSso.", r14="..osSSSSSSooSSSo..",
                   r15="...oosSSSSmmSsoo.."),
    "happy": _head(r11="odHSSSoSSSSSoSSSHo", r12=".oHSSoSoSSSoSoSSo.",
                   r13=".ohSbbSSSSSbbSSso.", r14="..osSSSSSmSSmSSo..",
                   r15="...oosSSSSmmSsoo.."),
    "sad": _head(r10="odHSSSoSSSSoSSSSHo", r11="odHSSooSSSSSooSSHo",
                 r12=".oHSSwEESSSwEESSo.", r14="..osSSSSSSSSSSSo..",
                 r15="...oosSSSSmmSsoo.."),
    "cry": _head(r10="odHSSSoSSSSoSSSSHo", r11="odHSSooSSSSSooSSHo",
                 r12=".oHSSTTTSSSTTTSSo.", r13=".ohSSTSSSSSTSSSso.",
                 r14="..osSTSSSSSTmSSo..", r15="...oosTSSSmTSsoo.."),
    "hurt": _head(r11="odHSSoSoSSSoSoSSHo", r12=".oHSSSoSSSSSoSSSo.",
                  r13=".ohSSoSoSSSoSoSso.", r14="..osSSSSSSooSSSo..",
                  r15="...oosSSSSmmSsoo.."),
    "smug": _head(r11="odHSSoooSSSoooSSHo", r12=".oHSSwEESSSwEESSo.",
                  r14="..osSSSSSSSSSmSo..", r15="...oosSSSSmmmsoo.."),
    "gloom": _head(r8="odHHHSHHBBHHBBHHho", r9="odHHSSSHBSBSBHSSHo",
                   r10="odHSSSBSSBSSBSSSHo"),
    "sleep": _head(r11="odHSSSSSSSSSSSSSHo", r12=".oHSSoooSSSoooSSo.",
                   r14="..osSSSSSSSoSSSo..", r15="...oosSSSSSSSsoo.."),
}

TORSO_PAL = {
    "o": INK,
    "W": (244, 246, 252),   # white kimono
    "w": (196, 206, 228),   # kimono shade
    "K": (44, 40, 58),      # black undershirt
    "k": (80, 76, 98),      # black highlight
    "B": (58, 66, 110),     # belt
    "b": (70, 132, 214),    # blue swirl pattern
    "c": (150, 190, 240),   # light swirl
}

TORSO = """
....oooooo....
...oKKKKKKo...
..oWWKKKKWWo..
.oWWWWKKKWWwo.
.oWWWWKkKWWwo.
.oWWWWKKKWWwo.
.oBBBBBBBBBBo.
.owWWWKKKWWwo.
.owWWWKKKWbwo.
.owbWWKKKbcbo.
.obcbWKKKbbwo.
..oooooooooo..
"""


def sheathed_bokuto(img, torso_xy, torso_size):
    """洞爷湖 wooden sword tucked in the belt, handle forward, blade behind."""
    tx, ty = torso_xy
    a, b = (tx + 12, ty + 6), (tx - 4, ty + 9)
    stamp_line(img, a, b, 4, INK)
    stamp_line(img, a, b, 2, (204, 150, 92))
    stamp_line(img, a, (tx + 9, ty + 6.5), 2, (96, 58, 40))


# ------------------------------------------------------------------ props & poses
def _milk_prop(img, ctx):
    """Strawberry-milk carton in the front hand."""
    if not ctx["hand_f"]:
        return
    x, y = ctx["hand_f"]
    x, y = int(x), int(y)
    from engine.gfx import rect
    rect(img, x - 2, y - 6, 5, 7, INK)
    rect(img, x - 1, y - 5, 3, 5, (255, 190, 205))
    rect(img, x - 1, y - 3, 3, 1, (228, 59, 68))
    rect(img, x, y - 8, 1, 3, (255, 255, 255))


def _jump_prop(img, ctx):
    """Weekly Shonen Jump magazine held up to read."""
    if not ctx["hand_f"]:
        return
    x, y = ctx["hand_f"]
    x, y = int(x), int(y)
    from engine.gfx import rect
    rect(img, x - 1, y - 9, 8, 11, INK)
    rect(img, x, y - 8, 6, 9, (240, 200, 60))
    rect(img, x, y - 8, 6, 2, (228, 59, 68))
    rect(img, x + 1, y - 5, 4, 3, (255, 255, 255))


def pose_nosepick(pp, t, p, d):
    """Signature deadpan nose-pick (the finger flick happens at the end of each loop)."""
    pose_idle(pp, t, p, d)
    f = step_frame(t, 6, 6)
    pp["arm_f"] = 165 if f < 4 else 120
    pp["expr"] = "normal"
    pp["head_dx"] = 0


def pose_drink(pp, t, p, d):
    pose_idle(pp, t, p, d)
    f = step_frame(t, 4, 4)
    pp["arm_f"] = 165 if f in (1, 2) else 120
    pp["expr"] = "blink" if f in (1, 2) else "happy"
    pp["props"] = [_milk_prop]


def pose_read(pp, t, p, d):
    pose_sit(pp, t, p, d)
    pp["arm_f"] = 130
    pp["arm_b"] = 110
    pp["expr"] = "normal"
    pp["props"] = [_jump_prop]


GINTOKI = register(ChibiDef(
    id="gintoki", name="银时", color=(120, 150, 220), voice=0.85,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=(244, 246, 252), sleeve_b=(44, 40, 58), sleeve_frac=0.65,
    hand=(255, 216, 184),
    leg_len=7, leg_w=3, leg_gap=4, pants=(44, 40, 58), shoes=(26, 22, 32),
    weapon="bokuto", weapon_len=17, sheathed=sheathed_bokuto,
    poses={"nosepick": pose_nosepick, "drink": pose_drink, "read": pose_read},
    desc="万事屋老板。银色天然卷，死鱼眼，嗜甜如命，腰插木刀『洞爷湖』。前攘夷志士『白夜叉』。",
))
