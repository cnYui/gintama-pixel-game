"""晴太 Seita — Yoshiwara street kid who wants to see his mother Hinowa.

Small boy: short spiky dark hair with a cowlick, big brown eyes, simple
mustard short kimono with a navy obi, dark shorts, straw sandals.
Extra pose `push`: leaning forward pushing with both hands (e.g. Hinowa's
wheelchair: put his feet at hinowa_x - 21, same y).  `run`/`cry` are the
standard poses with his own faces.
"""
import math

from engine.core import step_frame, ANIM_FPS
from engine.gfx import INK, stamp_line
from chars import register
from chars.rig import _blink
from chars.shouyou import LayeredDef

HEAD_PAL = {
    "o": INK,
    "L": (120, 104, 110),   # hair highlight
    "H": (70, 56, 64),      # dark brown-black hair
    "h": (52, 40, 50),
    "d": (38, 28, 38),
    "S": (255, 216, 184),
    "s": (232, 168, 138),
    "E": (110, 66, 40),     # brown eyes
    "w": (255, 255, 255),
    "m": (160, 64, 72),
    "b": (250, 150, 150),
    "T": (120, 200, 255),
}

BASE = [
    ".......oo.......",   # 0  cowlick
    "....oooHo.oo....",   # 1
    "...oHHHHoHHHo...",   # 2
    "..oHHLLHHHHHHo..",   # 3
    ".oHLHHHHHHHHHHo.",   # 4
    "odHHHHHHHHHhHHHo",   # 5
    "odHHHHhHHHHHHHHo",   # 6
    "odHHSHHSHHSSHSHo",   # 7  spiky bangs
    "odHSSSSSSSSSSSHo",   # 8
    "odSSoooSSoooSSSo",   # 9  big eyes (2 rows)
    ".oSSwEESSwEESSo.",   # 10
    ".oSSEEESSEEESSo.",   # 11
    "..osSSSSmSSSSo..",   # 12
    "...oosSSSSsoo...",   # 13
    ".....oooooo.....",   # 14
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
    "blink": _head(r9="odSSSSSSSSSSSSSo", r10=".oSSSSSSSSSSSSo.", r11=".oSSoooSSoooSSo."),
    "talk": _head(r12="..osSSSSoSSSSo..", r13="...oosSSmSsoo..."),
    "determined": _head(r8="odHSoSSSSSSoSSHo", r12="..osSSSmmSSSSo.."),
    "angry": _head(r8="odHSoSSSSSSoSSHo", r10=".oSSEEwSSEEwSSo.", r12="..osSSSmmSSSSo.."),
    "shout": _head(r8="odHSoSSSSSSoSSHo", r10=".oSSEEwSSEEwSSo.", r12="..osSSSomoSSSo..",
                   r13="...oosSoooSoo..."),
    "shock": _head(r9="odSSooSSSooSSSSo", r10=".oSowwoSowwoSSo.", r11=".oSSooSSSooSSSo.",
                   r12="..osSSSSoSSSSo..", r13="...oosSSoSsoo..."),
    "happy": _head(r9="odSSSSSSSSSSSSSo", r10=".oSSSoSSSSoSSSo.", r11=".oSboSobSoSobSo.",
                   r12="..osSSSmSSmSSo..", r13="...oosSSmmsoo..."),
    "sad": _head(r8="odHSSSoSSoSSSSHo", r9="odSSooSSSSooSSSo", r12="..osSSSSSSSSSo..",
                 r13="...oosSmmSsoo..."),
    "cry": _head(r8="odHSSSoSSoSSSSHo", r9="odSSooSSSSooSSSo", r10=".oSTTTSSSTTTSSo.",
                 r11=".oSTSSSSSTSSSSo.", r12="..oTSSSooSTSSo..", r13="...ooTSmmTsoo..."),
    "hurt": _head(r9="odSSoSoSSoSoSSSo", r10=".oSSSoSSSSoSSSo.", r11=".oSSoSoSSoSoSSo.",
                  r12="..osSSSSooSSSo.."),
    "smug": _head(r9="odSSSSSSSSSSSSSo", r10=".oSSoooSSoooSSo.", r12="..osSSSSSSmSSo..",
                  r13="...oosSSmmsoo..."),
    "sleep": _head(r9="odSSSSSSSSSSSSSo", r10=".oSSSSSSSSSSSSo.", r11=".oSSoooSSoooSSo."),
}

TORSO_PAL = {
    "o": INK,
    "Y": (226, 196, 112),   # mustard kimono
    "y": (184, 152, 78),
    "l": (246, 222, 150),
    "N": (58, 66, 112),     # navy obi
    "n": (86, 98, 150),
    "W": (250, 248, 240),
}

TORSO = """
..oooooo..
.oYlWWYYo.
oYlYYWYyyo
oYlYYYWyyo
oNnNNNNNNo
oYlYYYYyyo
oYYYYYyYyo
.oooooooo.
"""


def pose_push(pp, t, p, d):
    """Leaning into it, both arms forward, slow determined steps."""
    tq = step_frame(t, ANIM_FPS) / ANIM_FPS
    ph = tq * 2 * math.pi * 1.1
    pp["legs"], pp["leg_phase"] = "walk", ph
    pp["stride"], pp["lift"] = 2.2, 1.5
    pp["lean"] = 2
    pp["bob"] = -1 if math.sin(ph * 2) > 0 else 0
    pp["arm_f"] = 100 + 3 * math.sin(ph)
    pp["arm_b"] = 96 - 3 * math.sin(ph)
    pp["expr"] = "blink" if _blink(t, 2.7) else "determined"


def pose_push_still(pp, t, p, d):
    pose_push(pp, 0.0, p, d)
    pp["legs"] = "spread"
    pp["bob"] = 0
    pp["expr"] = "blink" if _blink(t, 2.7) else "happy"


SEITA = register(LayeredDef(
    id="seita", name="晴太", color=(196, 140, 40), voice=1.35,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(5, 2), hip=(5, 5), shoulder_f=(7, 3), shoulder_b=(2, 3),
    arm_len=5, arm_w=2, sleeve_f=(226, 196, 112), sleeve_b=(184, 152, 78), sleeve_frac=0.55,
    hand=(255, 216, 184),
    leg_len=5, leg_w=3, leg_gap=3, pants=(78, 62, 60), shoes=(196, 164, 104), shoe_h=1,
    weapon=None, sheathed=None,
    poses={"push": pose_push, "push_still": pose_push_still},
    portrait_crop=15,
    desc="在吉原长大的孤儿少年，一心想见母亲日轮。个子小小，胆子却很大。",
))
