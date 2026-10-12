"""小银时 Kid Gintoki — the 'corpse-eating demon' child of the battlefield.

Messy spiky silver hair, blank crimson eyes, dirty ragged kimono with a rope
belt, bare feet, clutching a katana far too big for him.
  idle : hugs the big sheathed katana upright in front of him
  eat  : sits on the ground munching a rice ball, sword leaning on his shoulder
         (extra expr `chew`)
"""
import math

from engine.core import step_frame, lerp
from engine.gfx import INK, stamp_line, rect
from chars import register
from chars.rig import pose_idle, _blink
from chars.shouyou import LayeredDef

HAIR_L, HAIR_M, HAIR_D = (236, 238, 248), (192, 198, 220), (140, 146, 182)
HEAD_PAL = {
    "o": INK,
    "H": HAIR_L,
    "h": HAIR_M,
    "d": HAIR_D,
    "S": (255, 214, 182),
    "s": (230, 166, 136),
    "g": (190, 150, 128),   # dirt smudge
    "E": (170, 30, 52),     # crimson eyes
    "w": (255, 255, 255),
    "m": (150, 60, 70),
    "b": (250, 150, 150),
    "T": (120, 200, 255),
}

BASE = [
    "..o..oo.o.oo....",   # 0  wild spikes
    ".oHooHHoHoHHo.o.",   # 1
    ".oHHHHHhHHHHHoHo",   # 2
    "odHhHHHHhHHhHHHo",   # 3  curly clumps
    "odHHhHHHHhHHhHho",   # 4
    "odhHHHhHHHHHHHHo",   # 5
    "odHHSHHSSHHSSHHo",   # 6  spiky bangs
    "odHSSSHSSSSSHSHo",   # 7
    "odHSoooSSoooSSHo",   # 8  heavy lids
    ".oHSwEESSwEESSo.",   # 9  blank crimson stare
    ".ohSgSSSSSSSSso.",   # 10 dirt on cheek
    "..osSSSSSmSSso..",   # 11
    "...oosSSSSSoo...",   # 12
    ".....oooooo.....",   # 13
]


def _head(**rows):
    r = list(BASE)
    for k, v in rows.items():
        i = int(k[1:])
        assert len(v) == len(BASE[i]), (k, v, len(v), len(BASE[i]))
        r[i] = v
    return "\n".join(r)


HEADS = {
    "normal": _head(),
    "blink": _head(r8="odHSSSSSSSSSSSHo", r9=".oHSoooSSoooSSo."),
    "talk": _head(r11="..osSSSSSoSSso..", r12="...oosSSSmSoo..."),
    "chew": _head(r10=".ohSgSSSSSSSSSo.", r11="..osSSSSmmSSSo..", r12="...oosSSSSSoo..."),
    "angry": _head(r7="odHoSSHSSSSoSSHo", r8="odHSoooSSoooSSHo", r9=".oHSEEwSSEEwSSo."),
    "determined": _head(r7="odHoSSHSSSSoSSHo", r8="odHSoooSSoooSSHo", r9=".oHSwEESSwEESSo.",
                        r11="..osSSSSmmSSso.."),
    "shout": _head(r7="odHoSSHSSSSoSSHo", r8="odHSoooSSoooSSHo", r9=".oHSEEwSSEEwSSo.",
                   r10=".ohSgSSSoooSSso.", r11="..osSSSSomoSso..", r12="...oosSSooSoo..."),
    "shock": _head(r8="odHSSooSSSooSSHo", r9=".oHSowwoSowwoSo.", r10=".ohSgooSSSooSso.",
                   r11="..osSSSSSoSSso..", r12="...oosSSSoSoo..."),
    "happy": _head(r8="odHSSoSSSSoSSSHo", r9=".oHSoSoSSoSoSSo.", r10=".ohSbbSSSSbbSso.",
                   r11="..osSSSSmSmSso..", r12="...oosSSSmSoo..."),
    "sad": _head(r7="odHSSoHSSSoSSSHo", r8="odHSooSSSSooSSHo", r9=".oHSwEESSwEESSo.",
                 r11="..osSSSSSSSSso..", r12="...oosSSSmmoo..."),
    "cry": _head(r7="odHSSoHSSSoSSSHo", r8="odHSooSSSSooSSHo", r9=".oHSTTTSSTTTSSo.",
                 r10=".ohSTSSSSSTSSso.", r11="..osTSSSooSTso..", r12="...ooTSSmmToo..."),
    "hurt": _head(r8="odHSoSoSSoSoSSHo", r9=".oHSSoSSSSoSSSo.", r10=".ohSoSoSSoSoSso.",
                  r11="..osSSSSSooSso..", r12="...oosSSSSSoo..."),
    "smug": _head(r11="..osSSSSSSSmso..", r12="...oosSSSmmoo..."),
    "sleep": _head(r8="odHSSSSSSSSSSSHo", r9=".oHSoooSSoooSSo.", r11="..osSSSSSoSSso.."),
}

TORSO_PAL = {
    "o": INK,
    "W": (222, 216, 200),   # dirty off-white kimono
    "w": (174, 166, 150),
    "k": (136, 124, 112),   # collar shadow
    "g": (150, 128, 104),   # dirt / patches
    "B": (150, 116, 78),    # straw-rope belt
    "b": (112, 84, 56),
}

TORSO = """
..oooooo..
.oWWWWwWo.
oWWWkkWWwo
oWgWWkWwwo
oBbBBBBBbo
oWWWWgWwWo
owWWWWWwwo
owoWwowWoo
.o.oo.oo..
"""

SCABBARD, SCAB_HI = (60, 46, 58), (112, 92, 110)
HILT = (70, 64, 92)
TSUBA = (232, 184, 70)


def _scabbard(img, bot, top, hilt_len=5):
    """Sheathed katana from `bot` (tip end) to `top` (hilt end)."""
    (x0, y0), (x1, y1) = bot, top
    L = math.hypot(x1 - x0, y1 - y0) or 1
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    gx, gy = x1 - ux * hilt_len, y1 - uy * hilt_len
    stamp_line(img, bot, top, 4, INK)
    stamp_line(img, bot, (gx, gy), 2, SCABBARD)
    stamp_line(img, (x0 + ux * 2 - uy * 0.5, y0 + uy * 2 + ux * 0.5),
               (gx - ux * 2 - uy * 0.5, gy - uy * 2 + ux * 0.5), 1, SCAB_HI)
    stamp_line(img, (gx + ux, gy + uy), top, 2, HILT)
    stamp_line(img, (gx - uy * 2, gy + ux * 2), (gx + uy * 2, gy - ux * 2), 3, INK)
    stamp_line(img, (gx - uy * 1.5, gy + ux * 1.5), (gx + uy * 1.5, gy - ux * 1.5), 1, TSUBA)


def sheathed_katana(img, torso_xy, torso_size):
    """A big stolen katana stuck through the rope belt (too long for him)."""
    tx, ty = torso_xy
    _scabbard(img, (tx - 9, ty + 8), (tx + 10, ty + 4), hilt_len=5)


def _hand(img, pos, col=(255, 214, 182)):
    x, y = pos
    stamp_line(img, (x, y), (x, y), 4, INK)
    stamp_line(img, (x, y), (x, y), 3, col)


def _hug_sword(img, ctx):
    """Clutches the sheathed sword upright in front of him."""
    hf = ctx["hand_f"]
    if not hf:
        return
    x = hf[0] + 1
    _scabbard(img, (x, 78.5), (x, hf[1] - 9), hilt_len=6)
    _hand(img, hf)


def _rice_ball(img, ctx):
    hf = ctx["hand_f"]
    if not hf:
        return
    x, y = int(hf[0]) + 1, int(hf[1]) - 3
    rect(img, x - 2, y - 1, 5, 4, INK)
    rect(img, x - 1, y - 2, 3, 1, INK)
    rect(img, x, y - 3, 1, 1, INK)
    rect(img, x - 1, y - 1, 3, 2, (252, 252, 244))
    rect(img, x, y - 2, 1, 1, (252, 252, 244))
    rect(img, x - 1, y + 1, 3, 1, (40, 64, 50))       # nori band
    rect(img, x - 1, y - 1, 1, 1, (255, 255, 255))
    _hand(img, hf)


def _leaning_sword(img, ctx):
    """Behind the body: sword leaning on his shoulder while he sits."""
    hip = ctx["hip"]
    hx, hy, hw, hh = ctx["head"]
    _scabbard(img, (hip[0] + 8, 78.5), (hip[0] - 10, hy - 1), hilt_len=6)


def pose_idle_kid(pp, t, p, d):
    pose_idle(pp, t, p, d)
    pp["arm_f"] = 62 + (3 if pp["bob"] else 0)
    pp["arm_b"] = 45
    pp["sheathed"] = False
    pp["props"] = [_hug_sword]


def pose_eat(pp, t, p, d):
    f = step_frame(t, 5, 4)
    pp["legs"] = "sit"
    pp["arm_f"] = 150 if f in (1, 2) else 118
    pp["arm_b"] = 150
    pp["bob"] = -1 if f == 1 else 0
    pp["expr"] = "chew" if f in (1, 2) else ("blink" if _blink(t) else "normal")
    pp["sheathed"] = False
    pp["props"] = [_rice_ball]
    pp["back_props"] = [_leaning_sword]


GINTOKI_KID = register(LayeredDef(
    id="gintoki_kid", name="小银时", color=(130, 140, 180), voice=1.25,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(5, 2), hip=(5, 6), shoulder_f=(7, 3), shoulder_b=(2, 3),
    arm_len=5, arm_w=2, sleeve_f=(222, 216, 200), sleeve_b=(160, 152, 138), sleeve_frac=0.6,
    hand=(255, 214, 182),
    leg_len=5, leg_w=3, leg_gap=3, pants=(196, 188, 170), shoes=(226, 178, 146), shoe_h=1,
    weapon="katana", weapon_len=17, sheathed=sheathed_katana,
    poses={"idle": pose_idle_kid, "eat": pose_eat},
    desc="战场上啃饭团的孤儿『食尸鬼』。银色乱发、空洞红瞳，抱着一把比自己还大的刀。",
))
