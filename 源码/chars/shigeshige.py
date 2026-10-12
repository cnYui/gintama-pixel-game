"""德川茂茂 Tokugawa Shigeshige — the 14th Shogun. Earnest to a fault.

Chonmage: shaved pate + black topknot lying forward, thick straight eyebrows,
round earnest eyes, formal light-blue kamishimo (winged kataginu shoulders with
white crests, matching hakama) over a dark kimono, white tabi. Katana.
Extra pose: bow (deep formal bow - sheared torso, head lowered, eyes closed).
Extra expr: haircut (the botched-haircut gag: topknot chopped, bald patches),
serious.
"""
from PIL import Image

from engine.core import step_frame, clamp, lerp
from engine.gfx import INK, stamp_line, ascii_sprite
from chars import register
from chars.rig import ChibiDef, POSES, _draw_arm

HEAD_PAL = {
    "o": INK,
    "l": (104, 108, 140),   # hair sheen
    "K": (62, 62, 84),      # black hair
    "k": (40, 40, 56),      # hair shade
    "P": (250, 228, 212),   # shaved pate (sakayaki)
    "p": (226, 198, 190),   # pate shade
    "S": (255, 222, 196),   # skin
    "s": (232, 176, 150),   # skin shade
    "E": (44, 40, 60),      # dark earnest eyes
    "w": (255, 255, 255),
    "m": (160, 70, 80),
    "b": (250, 160, 160),
    "T": (120, 200, 255),
    "B": (80, 120, 220),    # gloom lines
    "r": (230, 150, 150),   # sore scalp (haircut gag)
}

BASE = [
    "......oooooooo....",   # 0  topknot (chonmage) lying forward
    ".....oKllKKKKKo...",   # 1
    ".....oooKkkkooo...",   # 2  tie
    "...ooKKoPPPPPPoo..",   # 3  shaved pate
    "..oKKkoPPPPPPPPPo.",   # 4
    ".oKKkkPPPPPPPPPPo.",   # 5
    "oKKkkPPPPPPPPPPPpo",   # 6
    "oKKkkpPPPPPPPPPppo",   # 7
    "oKKkkKSSSSSSSSSKko",   # 8  hairline, sideburn
    "oKKkSSoooSSSoooSKo",   # 9
    "oKKkSooooSSooooSKo",   # 10 THICK straight brows
    "oKkkSSSSSSSSSSSSKo",   # 11
    ".oKkSSEwSSSSEwSSo.",   # 12 round earnest eyes
    ".oKkSSEESSSSEEsSo.",   # 13
    "..okSSSSSSSsSSSo..",   # 14
    "...osSSSSmmmSSso..",   # 15 firm straight mouth
    ".....ooooooooo....",   # 16
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


HAIRCUT = dict(  # topknot chopped off, bald patches, a sad little tuft
    r0="..................",
    r1="..........o.......",
    r2=".....oooooKoooo...",
    r3="...ooKKoPPPPPPoo..",
    r4="..oKoroPPPPrrPPPo.",
    r5=".oKKrrPPPPPrrPPPo.",
    r6="oKrrkPPPPPPPPPPPpo",
    r7="oKKrrpPPPPPPrrPppo",
    r8="oKKkkPSSSSSSSSSPko",
)

HEADS = {
    "normal": _head(),
    "blink": _head(r12=".oKkSSSSSSSSSSSSo.", r13=".oKkSoooSSSoooSSo."),
    "talk": _head(r15="...osSSSSSooSSso..", r14="..okSSSSSSSsSSSo.."),
    "angry": _head(r9="oKKkSooSSSSSooSSKo", r10="oKKkSSoooSoooSSSKo"),
    "serious": _head(r9="oKKkSoooSSSSoooSKo", r10="oKKkSSooooSooooSKo",
                     r15="...osSSSSmmmmSso.."),
    "shout": _head(r9="oKKkSooSSSSSooSSKo", r10="oKKkSSoooSoooSSSKo",
                   r14="..okSSSSSSoooSSo..", r15="...osSSSSomoSSso.."),
    "shock": _head(r9="oKKkSoooSSSSoooSKo", r10="oKKkSSSSSSSSSSSSKo",
                   r12=".oKkSowoSSSowoSSo.", r13=".oKkSoooSSSoooSSo.",
                   r15="...osSSSSSooSSso.."),
    "happy": _head(r12=".oKkSSoSSSSSoSSSo.", r13=".oKkSoSoSSSoSoSSo.",
                   r14="..okSbbSSSSsbbSo..", r15="...osSSSSmSSmSso.."),
    "sad": _head(r9="oKKkSSSooSSooSSSKo", r10="oKKkSooSSSSSSooSKo",
                 r15="...osSSSSSmSSSso.."),
    "cry": _head(r9="oKKkSSSooSSooSSSKo", r10="oKKkSooSSSSSSooSKo",
                 r12=".oKkSTTTSSSTTTSSo.", r13=".oKkSTSSSSSTSSSSo.",
                 r14="..okSTSSSSSTSSSo.."),
    "hurt": _head(r12=".oKkSoSoSSSoSoSSo.", r13=".oKkSSoSSSSSoSSSo.",
                  r15="...osSSSSSooSSso.."),
    "smug": _head(r12=".oKkSSSSSSSSSSSSo.", r13=".oKkSSooSSSSooSSo.",
                  r15="...osSSSSSSmmSso.."),
    # the botched haircut: earnest face, gloom lines
    "haircut": _head(r9="oKKkSSSooSSooSSSKo", r10="oKKkSooSSSSSSooSKo",
                     r11="oKkkSSBSSBSSBSSSKo", **HAIRCUT),
    "haircut_shock": _head(r9="oKKkSoooSSSSoooSKo", r10="oKKkSSSSSSSSSSSSKo",
                           r12=".oKkSowoSSSowoSSo.", r13=".oKkSoooSSSoooSSo.",
                           r15="...osSSSSSooSSso..", **HAIRCUT),
}
HEADS["determined"] = HEADS["serious"]
HEADS["cool"] = HEADS["normal"]

TORSO_PAL = {
    "o": INK,
    "B": (104, 160, 228),   # kamishimo light blue
    "b": (70, 118, 190),    # shade
    "l": (160, 204, 248),   # highlight
    "C": (250, 250, 255),   # white Tokugawa crest
    "W": (242, 242, 250),   # white under-collar
    "G": (62, 66, 94),      # dark kimono
    "g": (44, 46, 68),
}

# 18 wide: stiff winged kataginu shoulders (rows 2-4), hakama below the belt.
TORSO_ROWS = [
    "........oooooo........",   # 0
    "........oWGGWo........",   # 1
    "oooooooloWGWoBBooooooo",   # 2  stiff kataginu wings
    "ollllBBBBoWGWoBBBBbbbo",   # 3
    "oobbbbbBBBoWoBBBbbbboo",   # 4
    ".....oBCBBoGoBBCBo....",   # 5  white crests
    ".....olBBBoGoBBBbo....",   # 6
    ".....obbbbbbbbbbbo....",   # 7  himo belt
    ".....oBBBBoBBBBBbo....",   # 8  hakama (pleats)
    "....olBBBBoBBBBBbbo...",   # 9
    "....olBBBoBBBBBBbbo...",   # 10
    "....ooooooooooooooo...",   # 11
]
for _i, _r in enumerate(TORSO_ROWS):
    assert len(_r) == 22, (_i, _r, len(_r))


def _sheared(rows, k=0.7, pivot=8):
    """Formal bow: lean the upper body forward by shifting rows right."""
    shifts = [int(round(max(0, pivot - i) * k)) for i in range(len(rows))]
    m = max(shifts)
    return "\n".join("." * s + r + "." * (m - s) for s, r in zip(shifts, rows)), shifts


BOW_ART, BOW_SHIFT = _sheared(TORSO_ROWS)
TORSO = {"default": "\n".join(TORSO_ROWS), "bow": BOW_ART}


def sheathed_katana(img, torso_xy, torso_size):
    tx, ty = torso_xy
    a, b = (tx + 18, ty + 6), (tx + 1, ty + 10)
    stamp_line(img, a, b, 4, INK)
    stamp_line(img, (tx + 14, ty + 7), b, 2, (40, 30, 40))
    stamp_line(img, a, (tx + 15, ty + 6.7), 2, (236, 236, 244))
    stamp_line(img, (tx + 14, ty + 6), (tx + 14, ty + 8), 1, (230, 190, 70))


# ------------------------------------------------------------------ poses
def _bow_arm(img, ctx):
    d = ctx["def"]
    tx, ty, _, _ = ctx["torso"]
    sx = tx + d.shoulder_f[0] + BOW_SHIFT[d.shoulder_f[1]]
    sy = ty + d.shoulder_f[1]
    _draw_arm(img, d, (sx, sy), 12, d.sleeve_f)


def pose_bow(pp, t, p, d):
    """Deep formal bow (hands at the sides). p 0..0.3 bends down, holds."""
    k = clamp((p if p is not None else 1.0) / 0.3)
    if k < 0.5:
        pp["lean"] = 1
        pp["head_dx"] = 1
        pp["head_dy"] = 1
        pp["arm_f"] = 8
        pp["arm_b"] = 5
    else:
        pp["torso"] = "bow"
        pp["head_dx"] = BOW_SHIFT[d.neck[1]] + 1
        pp["head_dy"] = 4
        pp["hide_arm_f"] = True
        pp["hide_arm_b"] = True
        pp["props"] = [_bow_arm]
    pp["expr"] = "blink"


def pose_idle(pp, t, p, d):
    POSES["idle"](pp, t, p, d)
    pp["arm_f"] = 4
    pp["arm_b"] = -4


class ShogunDef(ChibiDef):
    def render(self, pose="idle", t=0.0, p=None, expr=None, **kw):
        if pose == "bow" and p is None:
            p = 1.0          # looping use: hold the bow
        return super().render(pose, t, p, expr, **kw)


SHIGESHIGE = register(ShogunDef(
    id="shigeshige", name="茂茂", color=(56, 100, 176), voice=0.86,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(11, 1), hip=(11, 8), shoulder_f=(15, 4), shoulder_b=(7, 4),
    arm_len=7, arm_w=2, sleeve_f=(62, 66, 94), sleeve_b=(44, 46, 68), sleeve_frac=0.7,
    hand=(255, 222, 196),
    leg_len=7, leg_w=4, leg_gap=4, pants=(104, 160, 228), shoes=(222, 224, 236), shoe_h=1,
    weapon="katana", weapon_len=17, sheathed=sheathed_katana,
    poses={"bow": pose_bow, "idle": pose_idle},
    desc="江户幕府第十四代将军德川茂茂。梳着丁髷、眉毛粗重，一本正经的老实人，经常遭遇各种不幸。",
))
