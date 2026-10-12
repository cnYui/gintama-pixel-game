"""神威 Kamui — Kagura's big brother, captain of Harusame's 7th division.

Vermilion hair with an ahoge and a long braid, eternal closed-eye smile
(expr 'normal'/'smile'), scary open blue eyes (expr 'open_eyes'), dark navy
china outfit, umbrella (recoloured rig umbrella, slung on the back when not in hand).
"""
import math

import numpy as np

from engine.core import step_frame
from engine.gfx import INK, stamp_line
from chars import register
from chars.rig import ChibiDef, POSES, _blink

# ------------------------------------------------------------------ palette
HEAD_PAL = {
    "o": INK,
    "H": (255, 146, 96),    # vermilion hair light
    "h": (232, 90, 60),     # hair mid
    "d": (168, 50, 52),     # hair shade
    "S": (255, 224, 200),   # pale Yato skin
    "s": (236, 180, 156),   # skin shade
    "E": (96, 176, 255),    # sky-blue iris
    "e": (32, 64, 150),     # dark iris / pupil
    "w": (255, 255, 255),
    "m": (170, 70, 80),     # mouth
    "b": (250, 160, 160),   # blush
    "T": (120, 200, 255),   # tears
}

# 19 rows: 2 ahoge rows + 17-row chibi head (eyes at rows 13/14)
BASE = [
    "...........oo.....",   # 0  ahoge
    "..........oHo.....",   # 1
    ".....ooooooHooo...",   # 2
    "...ooHHHHHHHhhhoo.",   # 3
    "..oHHHHHHHhhhhhhho",   # 4
    ".odHHHHHhhhhhhhhho",   # 5
    "odhHHHhhhhhhhhhhdo",   # 6
    "odhhhhhhhhhdhhhhdo",   # 7
    "odhhhhdhhhhdhhhhdo",   # 8  strands
    "odhhhdShhhdShhhhdo",   # 9  bang tips
    "odhhdSSShdSSShhhdo",   # 10
    "odhdSSSSSdSSSSShdo",   # 11 centre strand
    "odhSSSSSSSSSSSSSho",   # 12
    "odhSSSoSSSSSoSSHho",   # 13 closed-eye arcs (top)
    ".ohSSoSoSSSoSoSho.",   # 14 closed-eye arcs (sides)
    ".ohSSSSSSSSSSSSho.",   # 15
    "..osSSSSSSmSmSSo..",   # 16 gentle smile
    "...oosSSSSSmSsoo..",   # 17
    ".....ooooooooo....",   # 18
]
for _i, _r in enumerate(BASE):
    assert len(_r) == 18, (_i, _r, len(_r))

OPEN_EYES = dict(r12="odhSSSSSSSSSSSSSho", r13="odhSSoooSSSoooSHho", r14=".ohSSEeESSSEeESho.")


def _head(**rows):
    r = list(BASE)
    for k, v in rows.items():
        i = int(k[1:])
        assert len(v) == len(BASE[i]), (k, v, len(v))
        r[i] = v
    return "\n".join(r)


HEADS = {
    "normal": _head(),
    "smile": _head(r15=".ohSbbSSSSSbbSSho.", r16="..osSSSSSmSSSmSo..", r17="...oosSSSSmmmsoo.."),
    "blink": _head(r13="odhSSSSSSSSSSSSHho", r14=".ohSSoooSSSoooSho."),
    "talk": _head(r16="..osSSSSSSooSSSo..", r17="...oosSSSSmmSsoo.."),
    # the scary one: shadowed brow, sharp lids, small pupils, smile stays
    "open_eyes": _head(r12="odhSssssSSsssssSho", r13="odhsoooosSooooSHho",
                       r14=".ohSSwEeSSSwEeSho.", r16="..osSSSSSmSSSmSo..",
                       r17="...oosSSSSmmmsoo.."),
    "angry": _head(r12="odhSSoSSSSSSoSSSho", r13="odhSSSoooSoooSSHho",
                   r14=".ohSSEEwSSSEEwSho.", r16="..osSSSSSSSSSSSo..",
                   r17="...oosSSSSmmSsoo.."),
    "shout": _head(r12="odhSSoSSSSSSoSSSho", r13="odhSSSoooSoooSSHho",
                   r14=".ohSSEEwSSSEEwSho.", r15=".ohSSSSSSSoooSSho.",
                   r16="..osSSSSSSomoSSo..", r17="...oosSSSSooSsoo.."),
    "shock": _head(r13="odhSoooSSSoooSSHho", r14=".ohSowEoSowEoSSho.",
                   r15=".ohSoooSSoooSSSho.", r16="..osSSSSSSooSSSo..",
                   r17="...oosSSSSmmSsoo.."),
    "happy": _head(r15=".ohSbbSSSSSbbSSho.", r16="..osSSSSSmSSmSSo..",
                   r17="...oosSSSSmmSsoo.."),
    "sad": _head(r12="odhSSSoSSSSoSSSSho", r13="odhSSooSSSSSooSHho",
                 r14=".ohSSSSSSSSSSSSho.", r16="..osSSSSSSSSSSSo..",
                 r17="...oosSSSSmmSsoo.."),
    "cry": _head(r12="odhSSSoSSSSoSSSSho", r13="odhSSooSSSSSooSHho",
                 r14=".ohSSTTTSSSTTTSho.", r15=".ohSSTSSSSSTSSSho.",
                 r16="..osSTSSSSSTmSSo..", r17="...oosTSSSmTSsoo.."),
    "hurt": _head(r13="odhSSoSoSSSoSoSHho", r14=".ohSSSoSSSSSoSSho.",
                  r15=".ohSSoSoSSSoSoSho.", r16="..osSSSSSSooSSSo..",
                  r17="...oosSSSSmmSsoo.."),
    # one eye opens a slit: amused / condescending
    "smug": _head(r13="odhSSSoSSSSoooSHho", r14=".ohSSoSoSSSwEeSho.",
                  r16="..osSSSSSSSSSmSo..", r17="...oosSSSSmmmsoo.."),
    "sleep": _head(r13="odhSSSSSSSSSSSSHho", r14=".ohSSoooSSSoooSho.",
                   r16="..osSSSSSSSoSSSo..", r17="...oosSSSSSSSsoo.."),
}
HEADS["determined"] = HEADS["open_eyes"]
HEADS["evil"] = HEADS["open_eyes"]
HEADS["cool"] = HEADS["normal"]

TORSO_PAL = {
    "o": INK,
    "N": (46, 56, 108),     # navy
    "L": (74, 90, 156),     # navy light
    "n": (28, 32, 68),      # navy shade
    "k": (22, 22, 40),      # sash
    "C": (238, 224, 184),   # cream collar / frogs
    "Y": (214, 184, 120),   # frog button
    "H": (255, 146, 96),    # braid light
    "h": (232, 90, 60),     # braid mid
    "d": (168, 50, 52),     # braid shade
}

# 16 wide: braid on cols 0-3 (hangs down the back), body on cols 2-15
TORSO = [
    "......oooooo....",   # 0
    ".....oNCCCCNo...",   # 1
    "....oLNNNCNNNNo.",   # 2
    ".oooLLNNNCYNNno.",   # 3  braid starts at the nape
    "oHdoLNNNNNCNNno.",   # 4
    "odHoLNNNNNYCNno.",   # 5
    "oHdoknnnnnnnnko.",   # 6  sash
    "odHoLNNNNNNNNno.",   # 7
    "oHdoLNNNNNNNNno.",   # 8
    ".oCoLNNNNNNNnno.",   # 9  braid tie
    "oHhdonLNNNNNnno.",   # 10 tuft
    ".ooo.oooooooooo.",   # 11
]
for _i, _r in enumerate(TORSO):
    assert len(_r) == 16, (_i, _r, len(_r))


def _no_braid(rows):
    out = []
    for i, r in enumerate(rows):
        if 3 <= i <= 9:
            r = "..." + r[3:]
        elif i >= 10:
            r = "...." + r[4:]
        out.append(r)
    return out


TORSO = {"default": "\n".join(TORSO), "nobraid": "\n".join(_no_braid(TORSO))}

BRAID = ((255, 146, 96), (232, 90, 60), (168, 50, 52))


def _flying_braid(img, ctx, lift=0.3, amp=0.9):
    """Braid streaming out behind the head (used while running / leaping)."""
    tx, ty, _, _ = ctx["torso"]
    t = ctx["t"]
    ph = step_frame(t, 12) * 0.9
    x0, y0 = tx + 3, ty + 3
    pts = [(x0 - i * 2.0, y0 + i * lift + math.sin(i * 0.9 - ph) * amp * (i / 6.0))
           for i in range(8)]
    for a, b in zip(pts, pts[1:]):
        stamp_line(img, a, b, 4, INK)
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        stamp_line(img, a, b, 2, BRAID[i % 2])
    ex, ey = pts[-1]
    stamp_line(img, (ex, ey), (ex, ey), 3, INK)
    stamp_line(img, (ex, ey), (ex, ey), 1, (238, 224, 184))
    stamp_line(img, (ex - 2.5, ey - 0.5), (ex - 2.5, ey + 1), 3, INK)
    stamp_line(img, (ex - 2.5, ey), (ex - 2.5, ey + 0.5), 1, BRAID[0])

# ------------------------------------------------------------------ umbrella
UMB = {  # rig umbrella colours -> Kamui's dusky violet-blue parasol
    (150, 70, 170): (104, 92, 170),
    (90, 40, 60): (60, 40, 50),
    (210, 210, 220): (226, 226, 236),
    (90, 60, 70): (70, 52, 60),
}


def _recolor(img, table):
    a = np.array(img)
    rgb = a[..., :3]
    vis = a[..., 3] > 0
    for src, dst in table.items():
        m = vis & (rgb[..., 0] == src[0]) & (rgb[..., 1] == src[1]) & (rgb[..., 2] == src[2])
        if m.any():
            rgb[m] = dst
    from PIL import Image
    return Image.fromarray(a, "RGBA")


def sheathed_umbrella(img, torso_xy, torso_size):
    """Closed parasol tucked through the sash like a sword: handle forward at
    the front hip, canopy + tip sticking out behind."""
    tx, ty = torso_xy
    h, tip = (tx + 16, ty + 6), (tx - 5, ty + 11)
    stamp_line(img, h, tip, 5, INK)
    stamp_line(img, (tx + 13, ty + 6.7), (tx - 3, ty + 10.5), 3, UMB[(150, 70, 170)])
    stamp_line(img, (tx + 13, ty + 6.2), (tx - 3, ty + 10), 1, (140, 128, 210))
    stamp_line(img, h, (tx + 14, ty + 6.5), 2, (60, 40, 50))
    stamp_line(img, (tx - 3, ty + 10.5), (tx - 4, ty + 10.8), 1, (226, 226, 236))


class KamuiDef(ChibiDef):
    def render(self, pose="idle", t=0.0, p=None, expr=None, **kw):
        img, ax, ay = super().render(pose, t, p, expr, **kw)
        return _recolor(img, UMB), ax, ay


# ------------------------------------------------------------------ poses
def _smiley(pp, t):
    """Kamui's idle face never drops the smile; 'blink' is the same closed-eye face."""
    pp["expr"] = "normal"


def pose_idle(pp, t, p, d):
    POSES["idle"](pp, t, p, d)
    _smiley(pp, t)


def pose_walk(pp, t, p, d):
    POSES["walk"](pp, t, p, d)
    _smiley(pp, t)


def pose_run(pp, t, p, d):
    POSES["run"](pp, t, p, d)
    pp["expr"] = "smile"
    pp["torso"] = "nobraid"
    pp["props"] = [_flying_braid]


def pose_run_away(pp, t, p, d):
    POSES["run_away"](pp, t, p, d)
    pp["torso"] = "nobraid"
    pp["props"] = [_flying_braid]


def pose_jump(pp, t, p, d):
    POSES["jump"](pp, t, p, d)
    pp["expr"] = "smile"
    pp["torso"] = "nobraid"
    pp["props"] = [lambda img, ctx: _flying_braid(img, ctx, lift=1.2, amp=0.5)]


def pose_ready(pp, t, p, d):
    POSES["ready"](pp, t, p, d)
    pp["expr"] = "smile"


def pose_shoulder(pp, t, p, d):
    POSES["shoulder"](pp, t, p, d)
    pp["expr"] = "normal"


def pose_arms_crossed(pp, t, p, d):
    POSES["arms_crossed"](pp, t, p, d)
    pp["expr"] = "normal"


def pose_attack(pp, t, p, d):
    POSES["attack"](pp, t, p, d)
    pp["expr"] = "open_eyes" if 0.3 < p < 0.8 else "smile"


def pose_punch(pp, t, p, d):
    POSES["punch"](pp, t, p, d)
    pp["expr"] = "open_eyes"


def pose_open_eyes(pp, t, p, d):
    """Stands still, the smile stays but the eyes open. Menacing."""
    POSES["idle"](pp, t, p, d)
    pp["expr"] = "open_eyes"
    pp["arm_f"] = 35
    pp["weapon"] = -30
    pp["head_dy"] = 1


def pose_umbrella_open(pp, t, p, d):
    """Parasol open overhead (sunlight!)."""
    POSES["idle"](pp, t, p, d)
    pp["expr"] = "normal"
    pp["arm_f"] = 150
    pp["weapon"] = 95
    pp["weapon_kind"] = "umbrella_open"
    pp["sheathed"] = False


KAMUI = register(KamuiDef(
    id="kamui", name="神威", color=(206, 92, 52), voice=1.05,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(9, 2), hip=(9, 9), shoulder_f=(12, 3), shoulder_b=(5, 3),
    arm_len=7, arm_w=2, sleeve_f=(46, 56, 108), sleeve_b=(28, 32, 68), sleeve_frac=0.72,
    hand=(255, 224, 200),
    leg_len=7, leg_w=3, leg_gap=4, pants=(40, 46, 88), shoes=(22, 20, 30),
    weapon="umbrella", weapon_len=17, sheathed=sheathed_umbrella,
    poses={"idle": pose_idle, "walk": pose_walk, "run": pose_run, "run_away": pose_run_away,
           "jump": pose_jump, "ready": pose_ready,
           "shoulder": pose_shoulder, "arms_crossed": pose_arms_crossed,
           "attack": pose_attack, "punch": pose_punch,
           "open_eyes": pose_open_eyes, "umbrella_open": pose_umbrella_open},
    desc="春雨第七师团团长，神乐的哥哥。永远眯眼微笑的夜兔战斗狂，只对强者感兴趣。",
))
