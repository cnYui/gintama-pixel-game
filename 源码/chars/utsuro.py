"""虚 Utsuro — the immortal, Shouyou's other face.

Shouyou's gentle features turned eerie: long dark hair (middle part, locks
hanging past the shoulders and down the back), glowing red eyes, very pale
skin, black high-collared robes lined with dark red. Katana.
Extra pose: regen (dark wisps swirl up around him, dark aura outline).
Extra expr: smile (serene, creepy), glow (eyes blazing).
"""
import math

import numpy as np
from PIL import Image

from engine.core import step_frame, clamp, lerp
from engine.gfx import INK, stamp_line
from chars import register
from chars.rig import ChibiDef, POSES

HEAD_PAL = {
    "o": INK,
    "l": (146, 138, 172),   # hair sheen
    "H": (100, 92, 124),    # dark hair
    "h": (70, 64, 92),      # hair mid
    "d": (46, 42, 64),      # hair shade
    "S": (246, 234, 230),   # deathly pale skin
    "s": (210, 190, 192),   # skin shade
    "R": (255, 50, 62),     # glowing red iris
    "r": (170, 18, 40),     # dark red
    "g": (255, 190, 190),   # glow highlight
    "x": (120, 100, 130),   # shadow under the bangs
    "m": (140, 76, 88),
    "w": (255, 255, 255),
    "T": (120, 200, 255),
}

# 20 rows: 17-row head + long locks hanging below the jaw (anchor = chin row 16)
BASE = [
    ".....oooooooo.....",   # 0
    "...oolHHHHHHHoo...",   # 1
    "..olHHHHHHHHHHHo..",   # 2
    ".olHHHHHHHHHHHHHo.",   # 3
    "odHHHHHHHHHHHHHHho",   # 4
    "odHHHHHHHHhHHHHHho",   # 5
    "odhHHHHHHHHhHHHHho",   # 6
    "odhHHHHHHHhShHHHho",   # 7  parting (3/4 view: off-centre)
    "odhHHHHHHhSSShHHho",   # 8
    "odhHHHhHhSSSSShHho",   # 9  long bangs sweep aside, ragged tips
    "odhHHhShxSSSSSxhho",   # 10
    "odhHSoooSSSoooShho",   # 11
    "odhHSgRrSSSgRrShho",   # 12 red eyes
    "odhHSSSSSSSSSSShho",   # 13
    "odhHSSSSSSSmSSShho",   # 14
    "odhHosSSSSSSSsohho",   # 15
    "odhHdoooooooooHhdo",   # 16 chin; hair keeps falling
    "odhHdo........ohdo",   # 17
    ".odho.........ohdo",   # 18
    "..oo...........oo.",   # 19
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
    "blink": _head(r11="odhHSSSSSSSSSSShho", r12="odhHSoooSSSoooShho"),
    "talk": _head(r14="odhHSSSSSSSoSSShho"),
    "angry": _head(r10="odhHHhShoSSSSoxhho", r11="odhHSSoooSoooSShho",
                   r12="odhHSSgRrSgRrSShho", r14="odhHSSSSSSmmmSShho"),
    "shout": _head(r10="odhHHhShoSSSSoxhho", r11="odhHSSoooSoooSShho",
                   r12="odhHSSgRrSgRrSShho", r13="odhHSSSSSSoooSShho",
                   r14="odhHSSSSSSomoSShho"),
    "shock": _head(r11="odhHoooSSSoooSShho", r12="odhHoRgoSSoRgoShho",
                   r13="odhHoooSSSoooSShho", r14="odhHSSSSSSSooSShho"),
    # serene, unsettling smile - Shouyou's smile with red eyes
    "smile": _head(r11="odhHSSoSSSSoSSShho", r12="odhHSoSoSSoSoSShho",
                   r14="odhHSSSSSmSSmSShho", r15="odhHosSSSSmmSsohho"),
    "happy": _head(r11="odhHSSoSSSSoSSShho", r12="odhHSoSoSSoSoSShho",
                   r14="odhHSSSSSmSSmSShho", r15="odhHosSSSSmmSsohho"),
    "smug": _head(r12="odhHSgRrSSSgRrShho", r14="odhHSSSSSSSSmSShho",
                  r15="odhHosSSSSmmmsohho"),
    "sad": _head(r10="odhHHhShxoSSoSxhho", r11="odhHSSooSSSooSShho",
                 r12="odhHSgRrSSSgRrShho"),
    "cry": _head(r10="odhHHhShxoSSoSxhho", r11="odhHSSooSSSooSShho",
                 r12="odhHSTTTSSSTTTShho", r13="odhHSTSSSSSTSSShho"),
    "hurt": _head(r11="odhHSoSoSSoSoSShho", r12="odhHSSoSSSSoSSShho",
                  r13="odhHSoSoSSoSoSShho", r14="odhHSSSSSSSooSShho"),
    # eyes blazing (regen / power-up)
    "glow": _head(r10="odhHHhxhxxxxxxxhho", r11="odhHSoooSSSoooShho",
                  r12="odhHSRgRSSSRgRShho", r13="odhHSSrSSSSSrSShho"),
}
HEADS["determined"] = HEADS["angry"]
HEADS["evil"] = HEADS["smile"]

TORSO_PAL = {
    "o": INK,
    "K": (44, 40, 56),      # black robe
    "k": (28, 26, 36),      # robe shade
    "L": (76, 70, 96),      # robe highlight
    "r": (150, 30, 52),     # dark red lining
    "H": (100, 92, 124),    # hair down the back
    "h": (70, 64, 92),
    "d": (46, 42, 64),
}

# 16 wide: long hair down the back on cols 0-3, body cols 2-15, robe 2 px below hip
TORSO = [
    "......oooooo....",   # 0
    "....ooKrKKrKo...",   # 1  high collar, red lining
    "ohdoLKKKrrKKKo..",   # 2
    "oHdoLKKKKrKKKko.",   # 3
    "ohdoLKKKKKrKKko.",   # 4
    "oHdoLKKKKKKrKko.",   # 5  red-edged lapel
    "ohdoLKKKKKKKrko.",   # 6
    "oHhoLKKKKKKKKko.",   # 7
    ".ohoLKKKKKKKKko.",   # 8
    ".oHoLKKKKKKKkko.",   # 9  hip
    "..ooLKKKKKKkkko.",   # 10
    "...okKKKKKKkkko.",   # 11
    "....ooooooooooo.",   # 12
]
for _i, _r in enumerate(TORSO):
    assert len(_r) == 16, (_i, _r, len(_r))
TORSO = "\n".join(TORSO)


def sheathed_katana(img, torso_xy, torso_size):
    tx, ty = torso_xy
    a, b = (tx + 15, ty + 5), (tx - 3, ty + 10)
    stamp_line(img, a, b, 4, INK)
    stamp_line(img, (tx + 11, ty + 6.2), b, 2, (36, 30, 44))
    stamp_line(img, a, (tx + 12, ty + 5.8), 2, (120, 30, 50))
    stamp_line(img, (tx + 11, ty + 5), (tx + 11, ty + 7), 1, (200, 170, 80))


# ------------------------------------------------------------------ regen
WISP = ((34, 14, 48), (120, 54, 160), (190, 110, 230))


def _regen_prop(img, ctx, t):
    a = np.array(img)
    mask = a[..., 3] > 0
    # dark aura outline (1 px, flickering)
    dil = mask.copy()
    dil[1:, :] |= mask[:-1, :]
    dil[:-1, :] |= mask[1:, :]
    dil[:, 1:] |= mask[:, :-1]
    dil[:, :-1] |= mask[:, 1:]
    ring = dil & ~mask
    f = step_frame(t, 12)
    col = (96, 36, 120) if f % 2 else (64, 22, 86)
    a[ring] = col + (220,)
    img.paste(Image.fromarray(a, "RGBA").copy(), (0, 0))
    # swirling smoke wisps rising around the body (translucent layer)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    hx, hy = ctx["hip"]
    tq = step_frame(t, 24) / 24.0
    for i in range(8):
        side = -1 if i % 2 == 0 else 1
        ph = (tq * 0.9 + i / 8.0) % 1.0
        fade = min(1.0, ph * 4) * (1 - ph)
        x0 = hx + side * (6 + (i % 3) * 2)
        y0 = hy + 7 - (i % 4) * 3
        pts = []
        for j in range(7):
            q = ph - j * 0.03
            if q < 0:
                break
            x = x0 + side * q * 8 + math.sin(q * 9 + i) * 3
            y = y0 - q * 32
            pts.append((x, y))
        for j in range(len(pts) - 1):
            w = 3 if j < 2 else (2 if j < 5 else 1)
            al = int(255 * min(1.0, fade * 1.8) * (1 - j / 9))
            stamp_line(layer, pts[j], pts[j + 1], w, WISP[0] + (al,))
            if w > 1:
                stamp_line(layer, pts[j], pts[j + 1], w - 1, WISP[2 if j == 0 else 1] + (al,))
        if i % 3 == 0 and pts and fade > 0.3:
            x, y = pts[0]
            stamp_line(layer, (x + side * 2, y - 2), (x + side * 2, y - 2), 1, (255, 70, 80, 255))
    img.alpha_composite(layer)


def pose_regen(pp, t, p, d):
    """Wounds knit shut: dark wisps swirl upward, aura flickers, eyes blaze."""
    f = step_frame(t, 4, 4)
    pp["bob"] = -1 if f in (1, 2) else 0
    pp["arm_f"] = 28 + (4 if f in (1, 2) else 0)
    pp["arm_b"] = -28
    pp["legs"] = "spread"
    pp["expr"] = "glow"
    pp["props"] = [lambda img, ctx, t=t: _regen_prop(img, ctx, t)]


def pose_idle(pp, t, p, d):
    POSES["idle"](pp, t, p, d)
    pp["arm_f"] = 5
    pp["arm_b"] = -5


UTSURO = register(ChibiDef(
    id="utsuro", name="虚", color=(172, 46, 68), voice=0.82,
    heads=HEADS, head_pal=HEAD_PAL, head_anchor=(9, 16),
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(9, 2), hip=(9, 9), shoulder_f=(12, 3), shoulder_b=(5, 3),
    arm_len=7, arm_w=2, sleeve_f=(44, 40, 56), sleeve_b=(28, 26, 36), sleeve_frac=0.75,
    hand=(246, 234, 230),
    leg_len=7, leg_w=3, leg_gap=4, pants=(36, 32, 46), shoes=(22, 20, 28),
    weapon="katana", weapon_len=17, sheathed=sheathed_katana,
    poses={"regen": pose_regen, "idle": pose_idle},
    desc="不死之身的『虚』，吉田松阳的另一面。与松阳同一张脸，却有着冰冷的红色双眼和漆黑长发。",
))
