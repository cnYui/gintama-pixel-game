"""胧 Oboro — leader of the Tendoshu's assassin corps Naraku, Shouyou's first pupil.

Grey-white straight hair falling over the face, pale skin with scars across the
nose and cheek, cold half-lidded lilac eyes with dark rings, black Naraku robes
with a high grey collar, grey sash and a white crow emblem. Katana.
Extra pose: needle (flick-throws three needles; p drives wind-up/throw/flight).
Extra expr: cold_smile.
"""
import math

from engine.core import step_frame, clamp, lerp, ease_out, ease_in_out
from engine.gfx import INK, stamp_line
from chars import register
from chars.rig import ChibiDef, POSES

HEAD_PAL = {
    "o": INK,
    "H": (208, 208, 222),   # ash-grey hair
    "h": (162, 162, 182),   # hair mid
    "d": (112, 112, 136),   # hair shade
    "S": (248, 226, 214),   # pale skin
    "s": (218, 184, 170),   # skin shade
    "u": (200, 170, 184),   # dark rings under the eyes
    "r": (176, 112, 122),   # scars
    "E": (176, 162, 204),   # pale lilac iris
    "e": (60, 48, 76),      # pupil
    "w": (255, 255, 255),
    "m": (150, 70, 80),
    "T": (120, 200, 255),
    "b": (240, 160, 160),
}

# 18x18: flat-topped grey hair, long ragged side locks ending in points below
# the jaw, bangs hanging between the eyes; scar across the cheek + nose.
BASE = [
    ".....oooooooo.....",   # 0
    "...ooHHHHHHHHoo...",   # 1
    "..oHHHHHHHHHHHHo..",   # 2
    ".oHHHHHHHHHHHHHHo.",   # 3
    "odHHHHHHHHHHHHHHho",   # 4
    "odHHHHHHHHhHHHHHho",   # 5
    "odhHHHHhHHHhHHHHho",   # 6
    "odhHHHhHHHHhHHHhho",   # 7
    "odhHHhSHHHhSHHHhho",   # 8  bangs
    "odhHhSSShHhSSSHhho",   # 9
    "odhhSSSSShSSSSShho",   # 10
    "odhhSoooSSSoooShho",   # 11 heavy lids
    "odhhSEeoSSSEeoShdo",   # 12 cold half-lidded eyes
    "odhdSuuSSrSuuSSdho",   # 13 dark rings, nose scar
    "odhdrSSSSSrSSSSdho",   # 14 cheek scars
    ".odo.rSSSmSSSSohdo",   # 15 ragged locks past the jaw
    "..o...ooooooo.odo.",   # 16
    "...............o..",   # 17
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
    "blink": _head(r11="odhhSSSSSSSSSSShho", r12="odhhSoooSSSoooShdo"),
    "talk": _head(r15=".odo.rSSSoSSSSohdo"),
    "angry": _head(r10="odhhSoSSShSSSoShho", r11="odhhSSoooSoooSShho",
                   r12="odhhSSEeoSoEeoShdo", r15=".odo.rSSmmmSSSohdo"),
    "shout": _head(r10="odhhSoSSShSSSoShho", r11="odhhSSoooSoooSShho",
                   r12="odhhSSEeoSoEeoShdo", r14="odhdrSSSoooSSSSdho",
                   r15=".odo.rSSomoSSSohdo"),
    "shock": _head(r11="odhhoooSSSoooSShho", r12="odhhowEoSSowEoShdo",
                   r13="odhdoooSSroooSSdho", r15=".odo.rSSSooSSSohdo"),
    "happy": _head(r11="odhhSSoSSSSoSSShho", r12="odhhSoSoSSoSoSShdo",
                   r15=".odo.rSSmSSmSSohdo"),
    "sad": _head(r10="odhhSSSoShSoSSShho", r11="odhhSSooSSSooSShho",
                 r12="odhhSEeSSSSEeSShdo"),
    "cry": _head(r10="odhhSSSoShSoSSShho", r11="odhhSSooSSSooSShho",
                 r12="odhhSTTTSSSTTTShdo", r13="odhdSTuSSrSTuSSdho",
                 r14="odhdrTSSSSrTSSSdho"),
    "hurt": _head(r11="odhhSoSoSSoSoSShho", r12="odhhSSoSSSSoSSShdo",
                  r13="odhdSoSoSroSoSSdho", r15=".odo.rSSSooSSSohdo"),
    "smug": _head(r12="odhhSooeSSSooeShdo", r15=".odo.rSSSSSmSSohdo"),
    "cold_smile": _head(r15=".odo.rSSmmmSSSohdo"),
}
HEADS["determined"] = HEADS["angry"]
HEADS["cool"] = HEADS["normal"]

TORSO_PAL = {
    "o": INK,
    "K": (46, 42, 58),      # black robe
    "k": (28, 26, 36),      # shade
    "L": (82, 78, 100),     # highlight
    "G": (150, 150, 166),   # grey collar / sash
    "g": (110, 110, 128),   # grey shade
    "w": (240, 240, 248),   # crow emblem
}

TORSO = [
    "....oooooo....",   # 0
    "...oGGGGgGo...",   # 1  high grey collar
    "..oLKGGgKKKo..",   # 2
    ".oLKKKKGwKwko.",   # 3  crow emblem
    ".oLKKKKGwwwko.",   # 4
    ".oLKKKKGKwKko.",   # 5
    ".oGGGGGGgGggo.",   # 6  sash
    ".oLKKKKKKKKko.",   # 7
    ".oLKKKKKKKKko.",   # 8
    ".oLKKKKKKKkko.",   # 9
    ".okKKKKKKKkko.",   # 10
    "..oooooooooo..",   # 11
]
for _i, _r in enumerate(TORSO):
    assert len(_r) == 14, (_i, _r, len(_r))
TORSO = "\n".join(TORSO)


def sheathed_katana(img, torso_xy, torso_size):
    """Black scabbard through the sash: hilt forward, scabbard behind."""
    tx, ty = torso_xy
    a, b = (tx + 13, ty + 5), (tx - 5, ty + 10)
    stamp_line(img, a, b, 4, INK)
    stamp_line(img, (tx + 9, ty + 6.2), b, 2, (40, 36, 52))
    stamp_line(img, a, (tx + 10, ty + 5.8), 2, (200, 200, 214))
    stamp_line(img, (tx + 9, ty + 5), (tx + 9, ty + 7), 1, (220, 180, 70))


# ------------------------------------------------------------------ needle
NEEDLE = (226, 232, 244)


def _needles_prop(img, ctx, fly):
    """Three needles fanning out from the throwing hand."""
    if not ctx["hand_f"]:
        return
    hx, hy = ctx["hand_f"]
    dist = 2 + fly * 34
    for ang in (-9, 0, 9):
        a = math.radians(ang)
        vx, vy = math.cos(a), -math.sin(a)
        x, y = hx + vx * dist, hy + vy * dist
        stamp_line(img, (x - vx * 5, y - vy * 5), (x, y), 1, NEEDLE)
        stamp_line(img, (x - vx * 7, y - vy * 7), (x - vx * 5, y - vy * 5), 1, (120, 126, 150))
    if fly < 0.25:   # glint at release
        stamp_line(img, (hx + 1, hy - 2), (hx + 1, hy + 2), 1, (255, 255, 255))
        stamp_line(img, (hx - 1, hy), (hx + 3, hy), 1, (255, 255, 255))


def _needles_held(img, ctx):
    if not ctx["hand_f"]:
        return
    hx, hy = ctx["hand_f"]
    for i, dx in enumerate((-1, 0, 1)):
        stamp_line(img, (hx + dx, hy - 1), (hx + dx * 2, hy - 5), 1, NEEDLE)


def pose_needle(pp, t, p, d):
    """Flick-throw of Naraku needles. p 0-0.3 draw back (needles between the
    fingers), 0.3-0.42 snap forward, 0.42-1 needles fly ~34 px ahead."""
    pp["expr"] = "normal"
    pp["sheathed"] = True
    if p < 0.3:
        k = ease_out(p / 0.3)
        pp["arm_f"] = lerp(60, 165, k)
        pp["arm_b"] = lerp(-10, 40, k)
        pp["lean"] = int(lerp(0, -1, k))
        pp["legs"] = "spread"
        pp["props"] = [_needles_held]
    else:
        k = ease_in_out(clamp((p - 0.3) / 0.12))
        pp["arm_f"] = lerp(165, 85, k)
        pp["arm_b"] = -30
        pp["lean"] = int(lerp(-1, 2, k))
        pp["legs"] = "lunge"
        if p < 0.42:
            pp["props"] = [_needles_held]
        else:
            fly = clamp((p - 0.42) / 0.58)
            pp["props"] = [lambda img, ctx, fly=fly: _needles_prop(img, ctx, fly)]


def pose_idle(pp, t, p, d):
    POSES["idle"](pp, t, p, d)
    pp["arm_f"] = 6
    pp["arm_b"] = -6


OBORO = register(ChibiDef(
    id="oboro", name="胧", color=(88, 92, 118), voice=0.8,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=(46, 42, 58), sleeve_b=(28, 26, 36), sleeve_frac=0.72,
    hand=(248, 226, 214),
    leg_len=7, leg_w=3, leg_gap=4, pants=(40, 38, 52), shoes=(26, 24, 32),
    weapon="katana", weapon_len=17, sheathed=sheathed_katana,
    poses={"needle": pose_needle, "idle": pose_idle},
    desc="天照院奈落首领，松阳的第一个弟子。灰白头发，脸上有伤疤，眼神冰冷，擅长暗器飞针。",
))
