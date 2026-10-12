"""小桂 Kid Katsura — Shoukasonjuku student.

Long straight black hair in a high ponytail (tail drawn BEHIND the body),
straight bangs + long side locks, earnest brown eyes, pale-blue school kimono
with navy hakama, bokuto.
"""
from engine.core import step_frame
from engine.gfx import INK, stamp_line
from chars import register
from chars.shouyou import LayeredDef

HAIR_L, HAIR_H, HAIR_D = (104, 112, 158), (56, 58, 88), (36, 34, 56)
HEAD_PAL = {
    "o": INK,
    "L": HAIR_L,
    "H": HAIR_H,
    "d": HAIR_D,
    "S": (255, 220, 190),
    "s": (234, 172, 144),
    "E": (120, 70, 44),     # warm brown eyes
    "w": (255, 255, 255),
    "m": (160, 70, 76),
    "b": (250, 156, 150),
    "T": (120, 200, 255),
    "W": (250, 250, 255),   # hair tie
}

BASE = [
    ".....oooooo.....",   # 0
    "...ooHHHHHHoo...",   # 1
    "..oHHLLLHHHHHo..",   # 2
    ".oHLLHHHHHHHHHo.",   # 3
    "odHHHHHHHHHHHHHo",   # 4
    "odHHHHHHHHHHHHHo",   # 5
    "odHHHHHHHHHHHHHo",   # 6
    "odHHSHHHHHHSHHHo",   # 7  straight bangs
    "odHSoooSSoooSHHo",   # 8
    "odHSwEESSwEESHdo",   # 9
    "odHSSSSSSSSSSHdo",   # 10
    "odHosSSSSmSSoHdo",   # 11
    "odHdoosSSSsooHdo",   # 12
    "odHdo.ooooo.oHdo",   # 13 long side locks
    ".odo.........odo",   # 14
    "..o...........o.",   # 15
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
    "blink": _head(r8="odHSSSSSSSSSSHHo", r9="odHSoooSSoooSHdo"),
    "talk": _head(r11="odHosSSSSoSSoHdo", r12="odHdoosSSmsooHdo"),
    "angry": _head(r7="odHoSHHHHHHSoHHo", r9="odHSEEwSSEEwSHdo"),
    "determined": _head(r7="odHoSHHHHHHSoHHo", r11="odHosSSSmmSSoHdo"),
    "shout": _head(r7="odHoSHHHHHHSoHHo", r9="odHSEEwSSEEwSHdo", r10="odHSSSSSoooSSHdo",
                   r11="odHosSSSomoSoHdo", r12="odHdoosSSoooOHdo".replace("O", "o")),
    "shock": _head(r8="odHSSooSSSooSHHo", r9="odHSowwoSowwoHdo", r10="odHSSooSSSooSHdo",
                   r11="odHosSSSSoSSoHdo", r12="odHdoosSSSsooHdo"),
    "happy": _head(r8="odHSSoSSSSoSSHHo", r9="odHSoSoSSoSoSHdo", r10="odHSbbSSSSbbSHdo",
                   r11="odHosSSSmSmSoHdo", r12="odHdoosSSmsooHdo"),
    "sad": _head(r7="odHHSoHHHHoSHHHo", r8="odHSooSSSSooSHHo", r11="odHosSSSSSSSoHdo",
                 r12="odHdoosSmmsooHdo"),
    "cry": _head(r7="odHHSoHHHHoSHHHo", r8="odHSooSSSSooSHHo", r9="odHSTTTSSTTTSHdo",
                 r10="odHSTSSSSSTSSHdo", r11="odHosTSSooSToHdo", r12="odHdooTSmmTooHdo"),
    "hurt": _head(r8="odHSoSoSSoSoSHHo", r9="odHSSoSSSSoSSHdo", r10="odHSoSoSSoSoSHdo",
                  r11="odHosSSSSooSoHdo"),
    "smug": _head(r8="odHSSSSSSSSSSHHo", r9="odHSoooSSoooSHdo", r11="odHosSSSSSSmoHdo",
                  r12="odHdoosSSmmooHdo"),
    "sleep": _head(r8="odHSSSSSSSSSSHHo", r9="odHSoooSSoooSHdo", r11="odHosSSSSoSSoHdo"),
}
HEAD_ANCHOR = (8, 13)

TORSO_PAL = {
    "o": INK,
    "K": (190, 214, 238),   # pale-blue kimono
    "k": (140, 170, 208),
    "W": (252, 252, 255),   # white under-collar
    "N": (58, 66, 112),     # navy hakama
    "n": (86, 98, 150),
}

TORSO = """
..oooooo..
.oKKWWKKo.
oKKKWKKkko
oKKKKWKkko
oKKKKKKkko
oNnNNNNNNo
oNnNNNNNNo
oNnNNNnNNo
.oooooooo.
"""


def sheathed_bokuto(img, torso_xy, torso_size):
    tx, ty = torso_xy
    a, b = (tx + 9, ty + 5), (tx - 5, ty + 7)
    stamp_line(img, a, b, 4, INK)
    stamp_line(img, a, b, 2, (204, 150, 92))
    stamp_line(img, a, (tx + 7, ty + 5.3), 2, (96, 58, 40))


def ponytail(img, ctx):
    """High ponytail swinging behind the head."""
    hx, hy, hw, hh = ctx["head"]
    pp, t = ctx["params"], ctx["t"]
    sw = 0
    if pp["legs"] in ("walk", "run"):
        sw = (-1 if step_frame(t, 6, 2) else 0) - (1 if pp["legs"] == "run" else 0)
    dy = 1 if sw else 0
    top = [(hx + 5, hy + 1), (hx + 3, hy - 1), (hx, hy + 1), (hx - 2, hy + 5 + dy)]
    low = [(hx - 2, hy + 5 + dy), (hx - 3 + sw, hy + 10), (hx - 2 + sw * 2, hy + 15)]
    for a, b in zip(top, top[1:]):
        stamp_line(img, a, b, 5, INK)
    for a, b in zip(low, low[1:]):
        stamp_line(img, a, b, 4, INK)
    for a, b in zip(top, top[1:]):
        stamp_line(img, a, b, 3, HAIR_H)
    for a, b in zip(low, low[1:]):
        stamp_line(img, a, b, 2, HAIR_H)
    stamp_line(img, (hx + 2, hy - 1), (hx - 1, hy + 2), 1, HAIR_L)
    stamp_line(img, (low[0][0] - 1, low[0][1]), (low[1][0], low[1][1]), 1, HAIR_L)
    # white hair tie at the crown
    stamp_line(img, (hx + 4, hy), (hx + 4, hy), 3, INK)
    stamp_line(img, (hx + 4, hy), (hx + 4, hy), 1, (250, 250, 255))


KATSURA_KID = register(LayeredDef(
    id="katsura_kid", name="小桂", color=(70, 96, 170), voice=1.2,
    heads=HEADS, head_pal=HEAD_PAL, head_anchor=HEAD_ANCHOR,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(5, 2), hip=(5, 6), shoulder_f=(7, 3), shoulder_b=(2, 3),
    arm_len=5, arm_w=2, sleeve_f=(190, 214, 238), sleeve_b=(140, 164, 200), sleeve_frac=0.65,
    hand=(255, 220, 190),
    leg_len=5, leg_w=3, leg_gap=3, pants=(58, 66, 112), shoes=(40, 34, 44), shoe_h=1,
    weapon="bokuto", weapon_len=13, sheathed=sheathed_bokuto,
    back_layers=(ponytail,), portrait_crop=14,
    desc="松下私塾的优等生，一头黑色长马尾，认真又有点天然呆。未来的『逃跑的小太郎』。",
))
