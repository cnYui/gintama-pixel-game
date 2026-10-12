"""星海坊主 Umibozu — the strongest alien hunter, Kagura & Kamui's bald father.

Shiny bald head with ONE long hair strand, amber goggles pushed up on the
forehead, thick dark mustache, burly build in a long dusty cloak, umbrella.
Extra poses: umbrella_open, stop ('够了！').  Extra expr: goggles (pulled down).
"""
import numpy as np
from PIL import Image

from engine.core import step_frame
from engine.gfx import INK, stamp_line
from chars import register
from chars.rig import ChibiDef, POSES

# ------------------------------------------------------------------ palette
HEAD_PAL = {
    "o": INK,
    "K": (255, 250, 240),   # scalp shine
    "S": (255, 216, 186),   # skin
    "s": (230, 168, 138),   # skin shade
    "t": (206, 150, 126),   # stubble
    "G": (92, 76, 64),      # goggle strap
    "L": (250, 190, 80),    # amber lens
    "l": (255, 248, 220),   # lens glint
    "M": (82, 56, 46),      # mustache
    "N": (128, 92, 72),     # mustache highlight
    "E": (60, 120, 210),    # blue Yato eyes
    "w": (255, 255, 255),
    "m": (150, 60, 70),     # mouth
    "b": (250, 150, 150),
    "T": (120, 200, 255),
}

# 20 rows: 4 rows for the single wavy hair strand + 16-row bald head (eyes row 14)
BASE = [
    "..........ooo.....",   # 0  the ONE hair
    ".........o........",   # 1
    "..........o.......",   # 2
    "...........o......",   # 3
    ".....oooooooo.....",   # 4
    "...ooKKSSSSSSoo...",   # 5
    "..oKKKSSSSSSSSSo..",   # 6
    ".oKKSSSSSSSSSSSSo.",   # 7
    "osKSoooSSSoooSSsso",   # 8  goggles pushed up on the forehead
    "oGGoLlLoGoLlLoGGGo",   # 9
    "osSoLLLoSoLLLoSsso",   # 10
    "osSSoooSSSoooSSsso",   # 11
    "osSSSSSSSSSSSSSsso",   # 12
    "osSSMMMSSSSMMMSsso",   # 13 brows
    ".osSSwESSSSwESSso.",   # 14 eyes
    ".osSSSSSSSsSSSSso.",   # 15 nose
    "..oSMMMNNMMMNMMo..",   # 16 thick mustache
    "..otMMMSSSSMMMto..",   # 17
    "...ootSSSSSStoo...",   # 18
    ".....oooooooo.....",   # 19
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
    "blink": _head(r14=".osSooSSSSooSSSso."),
    "talk": _head(r17="..otMMMSmmSMMMto..", r18="...ootSSmmSStoo..."),
    "angry": _head(r12="osSSMSSSSSSSSMSsso", r13="osSSSMMSSSMMSSSsso",
                   r14=".osSSwESSSwESSSso.", r17="..otMMMmmmmMMMto.."),
    "shout": _head(r12="osSSMSSSSSSSSMSsso", r13="osSSSMMSSSMMSSSsso",
                   r14=".osSSwESSSwESSSso.", r17="..otMMooooMMMMto..",
                   r18="...ootommmoStoo..."),
    "shock": _head(r13="osSSSMMSSSSMMSSsso", r14=".osSowEoSSowEoSso.",
                   r15=".osSoooSSsoooSSso.", r17="..otMMMSooSMMMto..",
                   r18="...ootSSooSStoo..."),
    "happy": _head(r14=".osSoSoSSSoSoSSso.", r15=".osSbbSSSsSbbSSso.",
                   r17="..otMMmSSSSmMMto..", r18="...ootSmmmmStoo..."),
    "sad": _head(r13="osSSSSMMSSMMSSSsso", r14=".osSSwESSSSwESSso.",
                 r17="..otMMMmmmmMMMto.."),
    "cry": _head(r13="osSSSSMMSSMMSSSsso", r14=".osSTTTSSSTTTSSso.",
                 r15=".osSTSSSSsTSSSSso.", r17="..otMTMmmmmMTMto..",
                 r18="...ootTSSSSTtoo..."),
    "hurt": _head(r13="osSSSMMSSSSMMSSsso", r14=".osSoSoSSSoSoSSso.",
                  r15=".osSSoSSSsSoSSSso.", r17="..otMMMSooSMMMto.."),
    "smug": _head(r13="osSSMMMSSSSMMSSsso", r14=".osSSooSSSSooSSso.",
                  r17="..otMMMSSSmmMMto.."),
    # goggles pulled down over the eyes (serious battle mode)
    "goggles": _head(r8="osKSSSSSSSSSSSSsso", r9="osSSSSSSSSSSSSSsso",
                     r10="osSSSSSSSSSSSSSsso", r11="osSSSSSSSSSSSSSsso",
                     r12="osSSoooSSSoooSSsso", r13="oGGoLlLoGoLlLoGGGo",
                     r14=".oSoLLLoSoLLLoSso.", r15=".osSoooSsSoooSSso."),
}
HEADS["determined"] = HEADS["angry"]
HEADS["serious"] = HEADS["angry"]

TORSO_PAL = {
    "o": INK,
    "L": (170, 152, 122),   # cloak light
    "C": (130, 112, 90),    # cloak
    "c": (92, 78, 66),      # cloak shade
    "F": (206, 190, 158),   # hood fold light
    "f": (156, 138, 112),   # hood fold
    "Y": (220, 180, 90),    # clasp
}

# 16 wide, 13 tall: broad shoulders, long closed cloak hanging 3 px below the hip
TORSO = [
    "....oooooooo....",   # 0
    "..ooFFFFFFffoo..",   # 1  hood bunched round the neck
    ".oLLoffYYffocCo.",   # 2  clasp
    ".oLLCCCooCCCCco.",   # 3
    "oLLCCCCCoCCCCcco",   # 4  front fold
    "oLCCCCCCoCCCCcco",   # 5
    "oLCCCCCCoCCCCcco",   # 6
    "oLCCCCCCoCCCccco",   # 7
    "oLCCCCCoCCCCccco",   # 8
    "oLCCCCCoCCCCccco",   # 9
    "oLCCCCCoCCCcccco",   # 10
    "ocCCCCoCCCCcccco",   # 11
    ".oooooooooooooo.",   # 12
]
for _i, _r in enumerate(TORSO):
    assert len(_r) == 16, (_i, _r, len(_r))
TORSO = "\n".join(TORSO)

# ------------------------------------------------------------------ umbrella
UMB = {  # rig umbrella colours -> Umibozu's weathered olive parasol
    (150, 70, 170): (112, 130, 90),
    (90, 40, 60): (64, 50, 40),
    (210, 210, 220): (226, 226, 236),
    (90, 60, 70): (70, 56, 46),
}


def _recolor(img, table):
    a = np.array(img)
    rgb = a[..., :3]
    vis = a[..., 3] > 0
    for src, dst in table.items():
        m = vis & (rgb[..., 0] == src[0]) & (rgb[..., 1] == src[1]) & (rgb[..., 2] == src[2])
        if m.any():
            rgb[m] = dst
    return Image.fromarray(a, "RGBA")


def sheathed_umbrella(img, torso_xy, torso_size):
    """Closed parasol tucked through the belt, handle forward, tip behind."""
    tx, ty = torso_xy
    h, tip = (tx + 17, ty + 6), (tx - 5, ty + 11)
    stamp_line(img, h, tip, 5, INK)
    stamp_line(img, (tx + 14, ty + 6.7), (tx - 3, ty + 10.5), 3, UMB[(150, 70, 170)])
    stamp_line(img, (tx + 14, ty + 6.2), (tx - 3, ty + 10), 1, (160, 176, 128))
    stamp_line(img, h, (tx + 15, ty + 6.5), 2, (64, 50, 40))
    stamp_line(img, (tx - 3, ty + 10.5), (tx - 4, ty + 10.8), 1, (226, 226, 236))


class UmibozuDef(ChibiDef):
    def render(self, pose="idle", t=0.0, p=None, expr=None, **kw):
        img, ax, ay = super().render(pose, t, p, expr, **kw)
        return _recolor(img, UMB), ax, ay


def pose_umbrella_open(pp, t, p, d):
    """Parasol open overhead."""
    POSES["idle"](pp, t, p, d)
    pp["arm_f"] = 150
    pp["weapon"] = 95
    pp["weapon_kind"] = "umbrella_open"
    pp["sheathed"] = False


def pose_stop(pp, t, p, d):
    """'够了！' — lands between the siblings, umbrella swept low, palm out."""
    f = step_frame(t, 4, 2)
    pp["legs"] = "spread"
    pp["arm_f"] = 60
    pp["weapon"] = -20
    pp["arm_b"] = 95
    pp["lean"] = 1
    pp["bob"] = -1 if f else 0
    pp["expr"] = "shout" if step_frame(t, 8) % 2 == 0 else "angry"


UMIBOZU = register(UmibozuDef(
    id="umibozu", name="星海坊主", color=(128, 104, 64), voice=0.72,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(8, 2), hip=(8, 9), shoulder_f=(12, 4), shoulder_b=(4, 4),
    arm_len=8, arm_w=3, sleeve_f=(130, 112, 90), sleeve_b=(92, 78, 66), sleeve_frac=0.72,
    hand=(255, 216, 186),
    leg_len=7, leg_w=3, leg_gap=5, pants=(62, 58, 70), shoes=(70, 50, 40),
    weapon="umbrella", weapon_len=19, sheathed=sheathed_umbrella,
    poses={"umbrella_open": pose_umbrella_open, "stop": pose_stop},
    desc="宇宙最强的外星猎人，神乐和神威的父亲。秃头上只剩一根头发，额头戴护目镜，披着旅行斗篷。",
))
