"""长谷川泰三 Hasegawa Taizo — MADAO (a totally useless middle-aged man).
ALWAYS wears his sunglasses. Stubble, messy hair, shabby beige clothes, slouch.

Extras: box (sitting in his cardboard-box home), depressed (kneeling, head hung,
        gloom cloud + blue gloom lines).
Extra exprs: gloom, determined, sleep. (Eyes are hidden: expressions live in the
brows above the shades, the mouth, sweat and tears running out from under them.)
"""
import math

from PIL import Image, ImageDraw

from engine.core import step_frame, clamp, lerp, ANIM_FPS
from engine.gfx import INK, stamp_line, rect, pset
from chars import register
from chars.rig import (ChibiDef, POSES, default_params, compose, _rotate_about, OX, OY, CW, CH,
                       pose_idle, pose_walk, pose_kneel, _blink)

# ------------------------------------------------------------------ head
HEAD_PAL = {
    "o": INK,
    "H": (110, 96, 96),     # messy dark hair light
    "h": (74, 62, 68),      # hair mid
    "d": (48, 40, 50),      # hair shade
    "S": (246, 206, 172),   # skin (a bit sallow)
    "s": (214, 164, 134),   # skin shade
    "t": (150, 132, 128),   # stubble
    "L": (36, 36, 50),      # sunglass lens
    "l": (70, 76, 104),     # lens reflection band
    "G": (220, 232, 248),   # glint
    "m": (150, 70, 70),     # mouth
    "r": (210, 100, 110),
    "b": (240, 150, 140),
    "T": (120, 200, 255),   # tears
    "B": (80, 120, 220),    # gloom
    "w": (255, 255, 255),
    "W": (170, 220, 255),   # sweat
}

BASE = [
    "...o..o..oo..o....",   # 0  messy spikes
    "..oHo.oHooHHoHo...",   # 1
    ".oHHHooHHHHHHHho..",   # 2
    ".oHHHHHHHHHHhhhho.",   # 3
    "odHHHHHHhHHHhhhhdo",   # 4
    "odHHhHHHHHhhhhhhdo",   # 5
    "odhHHHhHhhhhhhhhdo",   # 6
    "odhhHhhhhhhhhhhhdo",   # 7
    "odhhhShhShhhShhhdo",   # 8  scruffy bangs
    "odhhSSShSSShSSShdo",   # 9
    "odhooooooooooooSho",   # 10 sunglasses top
    "odhoGlLLoooGlLoSho",   # 11
    "odhoLLLLoSoLLLoSso",   # 12
    ".ohSooooSSSoooSso.",   # 13
    "..osStSSSmmmStSo..",   # 14 sad mouth + stubble
    "...oostStStStsoo..",   # 15 stubbly chin
    ".....ooooooooo....",   # 16
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
    "blink": _head(),
    "talk": _head(r14="..osStSSSooStSSo..", r15="...oostSSmmStsoo.."),
    "angry": _head(r9="odhhSoSSSSSSoSShdo", r14="..osStSSooooStSo.."),
    "shout": _head(r9="odhhSoSSSSSSoSShdo",
                   r14="..osStSSomrmotSo..", r15="...oostStoootsoo.."),
    "shock": _head(r9="odhhSSooSSSooSShdo", r11="odhoGlLLoooGlLoSWo",
                   r12="odhoLLLLoSoLLLoSWo", r14="..osStSSSooStSSo..",
                   r15="...oostSSmmStsoo.."),
    "happy": _head(r13=".ohSooooSSSoooSso.", r14="..osbtSSmSSmSbSo..",
                   r15="...oostSSmmStsoo.."),
    "sad": _head(r9="odhhSSSoSSSoSSShdo", r14="..osStSSSSSSStSo..",
                 r15="...oostSSmmStsoo.."),
    "cry": _head(r9="odhhSSSoSSSoSSShdo", r13=".ohSTooTSSSToTSso.",
                 r14="..osTtSTSmmTStTo..", r15="...ooTStSTStTsoo.."),
    "hurt": _head(r11="odhoGoLLoooGLoLSho", r12="odhoLLoLoSoLoLoSso",
                  r14="..osStSSSooStSSo.."),
    "smug": _head(r11="odhoGGLLoooGGLoSho",
                  r14="..osStSSSSSmmtSo..", r15="...oostStSmmtsoo.."),
    "gloom": _head(r8="odhhhSBhSBhhSBhhdo", r9="odhhSBShSBShSBShdo",
                   r14="..osStSSSSSSStSo..", r15="...oostSmmmStsoo.."),
    "determined": _head(r9="odhhSoSSSSSSoSShdo", r14="..osStSSmmmSStSo.."),
    "sleep": _head(r14="..osStSSSSoSStSo.."),
}

# ------------------------------------------------------------------ torso
TORSO_PAL = {
    "o": INK,
    "B": (220, 198, 156),   # shabby beige
    "b": (180, 156, 116),   # beige shade
    "c": (240, 224, 188),   # beige light
    "K": (84, 80, 76),      # grubby undershirt
    "k": (112, 108, 100),
    "P": (150, 130, 96),    # patch
    "p": (120, 100, 74),    # patch stitches
    "N": (120, 84, 52),     # rope belt
    "n": (160, 116, 72),
}

TORSO = """
....oooooo....
...oKKKKKKo...
..ocBKKKKBBo..
.ocBBBKKKBBbo.
.oBBBBKkKBBbo.
.oBBBBKKBBBbo.
.oNnNnNnNnNNo.
.oBBBBKKBBBbo.
.obPPBBKBBbbo.
.obPpBBKBBbbo.
.obbBBBKBbbbo.
..oooooooooo..
"""

PANTS = (104, 96, 90)
SANDALS = (96, 66, 48)


# ------------------------------------------------------------------ props
def _box_prop(img, ctx):
    """Cardboard-box home (front face + two flaps folded outward), drawn over the
    lower body; his hands rest on the rim."""
    hx, hy = ctx["hip"]
    cx = int(round(hx))
    top = OY - 9
    x0, x1 = cx - 11, cx + 11
    d = ImageDraw.Draw(img)
    CB, CBd, CBl = (196, 150, 98), (158, 114, 70), (222, 180, 124)
    # flaps folded outward (low, so they never cover his face)
    d.polygon([(x0 + 2, top), (x0 - 6, top - 5), (x0 - 3, top - 9), (x0 + 3, top - 1)], fill=CBd, outline=INK)
    d.polygon([(x1 - 2, top), (x1 + 6, top - 6), (x1 + 4, top - 10), (x1 - 3, top - 1)], fill=CB, outline=INK)
    d.line([(x1 + 4, top - 8), (x1 + 5, top - 6)], fill=CBl)
    # front
    d.rectangle([x0, top, x1, OY - 1], fill=CB, outline=INK)
    d.line([(x0 + 1, top + 1), (x1 - 1, top + 1)], fill=CBl)
    d.line([(x1 - 1, top + 2), (x1 - 1, OY - 2)], fill=CBd)
    # tape + scribble label
    d.line([(cx - 1, top + 1), (cx - 1, OY - 2)], fill=(214, 196, 150))
    d.rectangle([cx + 3, top + 3, cx + 8, top + 6], fill=(240, 232, 214), outline=(120, 90, 60))
    d.line([(cx + 4, top + 4), (cx + 7, top + 4)], fill=(90, 70, 60))
    pset(img, cx - 6, top + 5, (170, 126, 82, 255))
    pset(img, cx - 5, top + 6, (170, 126, 82, 255))
    # hands on the rim
    for hand in (ctx["hand_f"], ctx["hand_b"]):
        if hand:
            x = int(round(hand[0]))
            rect(img, x - 1, top - 2, 4, 3, INK)
            rect(img, x, top - 1, 2, 1, (246, 206, 172))


def _gloom_prop(img, ctx):
    """Little rain cloud + falling gloom lines over his head."""
    hx, hy, hw, hh = ctx["head"]
    t = ctx["t"]
    cx, cy = int(hx) + hw // 2, int(hy) - 6
    d = ImageDraw.Draw(img)
    f = step_frame(t, 6)
    bob = f % 2
    for dx, r in ((-5, 3), (0, 4), (5, 3)):
        d.ellipse([cx + dx - r, cy - r + bob, cx + dx + r, cy + r + bob], fill=(92, 98, 128), outline=INK)
    d.line([(cx - 6, cy + bob - 1), (cx + 3, cy + bob - 3)], fill=(128, 134, 164))
    for i in range(4):
        x = cx - 5 + i * 3
        y0 = cy + 4 + ((f + i * 2) % 4) * 2
        d.line([(x, y0), (x, y0 + 2)], fill=(110, 150, 230))


# ------------------------------------------------------------------ poses
def pose_idle_h(pp, t, p, d):
    """Sad-sack idle: slouched, head hanging forward, arms dangling."""
    pose_idle(pp, t, p, d)
    f = step_frame(t, 3, 4)
    pp["arm_f"] = 4
    pp["arm_b"] = -4
    pp["head_dx"] = 1
    pp["head_dy"] = 1
    pp["bob"] = 1 if f in (2, 3) else 0     # heavy sighing breath (sags instead of rising)
    pp["expr"] = "sad" if (t % 6.0) > 5.0 else "normal"


def pose_walk_h(pp, t, p, d):
    pose_walk(pp, t, p, d)
    pp["arm_f"] = pp["arm_f"] * 0.4
    pp["arm_b"] = pp["arm_b"] * 0.4
    pp["stride"] = 2.0
    pp["head_dx"] = 1
    pp["head_dy"] = 1


def pose_box(pp, t, p, d):
    f = step_frame(t, 3, 4)
    pp["legs"] = "none"
    pp["dy"] = -5
    pp["arm_f"] = 75
    pp["arm_b"] = 62
    pp["sheathed"] = False
    pp["bob"] = 1 if f in (2, 3) else 0
    pp["head_dy"] = 1
    pp["expr"] = "sad" if (t % 5.0) < 3.5 else "cry"
    pp["props"] = [_box_prop]


def pose_depressed(pp, t, p, d):
    pose_kneel(pp, t, p, d)
    f = step_frame(t, 3, 4)
    pp["lean"] = 2
    pp["head_dx"] = 2
    pp["head_dy"] = 3
    pp["arm_f"] = 12
    pp["arm_b"] = 6
    pp["bob"] = 1 if f in (2, 3) else 0
    pp["expr"] = "gloom"
    pp["props"] = [_gloom_prop]


HASEGAWA = register(ChibiDef(
    id="hasegawa", name="长谷川", color=(150, 116, 74), voice=0.74,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=(220, 198, 156), sleeve_b=(170, 146, 108), sleeve_frac=0.55,
    hand=(246, 206, 172),
    leg_len=7, leg_w=3, leg_gap=4, pants=PANTS, shoes=SANDALS, shoe_h=1,
    weapon=None,
    poses={"idle": pose_idle_h, "walk": pose_walk_h, "box": pose_box, "depressed": pose_depressed},
    desc="前幕府入国管理局局长，如今是失业的『MADAO（彻底没用的大叔）』。墨镜是他最后的尊严。",
))
