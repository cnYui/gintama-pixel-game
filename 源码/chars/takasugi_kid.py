"""小高杉 Kid Takasugi — Shoukasonjuku student, Gintoki's rival.

Dark-purple hair with swept bangs, BOTH green eyes visible (before the
bandage), fierce slanted brows even when calm, plum school kimono + slate
hakama, bokuto.
"""
from engine.gfx import INK, stamp_line
from chars import register
from chars.shouyou import LayeredDef

HEAD_PAL = {
    "o": INK,
    "L": (128, 104, 178),   # hair highlight
    "H": (82, 62, 130),     # dark purple hair (matches adult Takasugi)
    "h": (60, 44, 100),
    "d": (40, 28, 72),
    "S": (255, 218, 188),
    "s": (232, 170, 140),
    "E": (74, 150, 96),     # green eyes
    "w": (255, 255, 255),
    "m": (150, 62, 72),
    "b": (250, 150, 150),
    "T": (120, 200, 255),
}

BASE = [
    ".....o.oooo.....",   # 0
    "...ooHoHHHHoo...",   # 1
    "..oHHHLLLHHHHo..",   # 2
    ".oHHLLHHHHHhHHo.",   # 3
    "odHHHHHHHHHHhHHo",   # 4
    "odhHHHHHhHHHHHHo",   # 5
    "odHHHhHHHHHHhHHo",   # 6
    "odHHHHSHHHHSHHho",   # 7  bangs swept to the side
    "odHoHHSSoHSSSoho",   # 8  fierce brows (outer ends up)
    "odhSoooSSoooSSo.",   # 9  lids
    ".ohSwEESSwEESSo.",   # 10 green eyes
    "..osSSSSSmmSso..",   # 11 tight mouth
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
    "blink": _head(r9="odhSSSSSSSSSSSo.", r10=".ohSoooSSoooSSo."),
    "talk": _head(r11="..osSSSSSooSso..", r12="...oosSSSmmoo..."),
    "angry": _head(r10=".ohSEEwSSEEwSSo.", r11="..osSSSSoooSso.."),
    "determined": _head(),
    "shout": _head(r10=".ohSEEwSSEEwSSo.", r11="..osSSSSomoSso..", r12="...oosSSoooo...."),
    "shock": _head(r8="odHHHHSSSHSSSHho", r9="odhSSooSSSooSSo.", r10=".ohSowwoSowwoSo.",
                   r11="..osSSSSSooSso..", r12="...oosSSSooo...."[:16]),
    "happy": _head(r8="odHHHHSSSHSSSHho", r9="odhSSoSSSSoSSSo.", r10=".ohSoSoSSoSoSSo.",
                   r11="..osbSSSmSmSbo..", r12="...oosSSSmSoo..."),
    "sad": _head(r8="odHHHoSSSHoSSHho", r9="odhSooSSSSooSSo.", r11="..osSSSSSSSSso..",
                 r12="...oosSSSmmoo..."),
    "cry": _head(r8="odHHHoSSSHoSSHho", r9="odhSooSSSSooSSo.", r10=".ohSTTTSSTTTSSo.",
                 r11="..osTSSSooSTso..", r12="...ooTSSmmToo..."),
    "hurt": _head(r9="odhSoSoSSoSoSSo.", r10=".ohSSoSSSSoSSSo.", r11="..osoSoSSooSso.."),
    "smug": _head(r10=".ohSSSSSSSSSSSo.", r9="odhSoooSSoooSSo.", r11="..osSSSSSSSmso..",
                  r12="...oosSSSmmoo..."),
    "sleep": _head(r9="odhSSSSSSSSSSSo.", r10=".ohSoooSSoooSSo.", r11="..osSSSSSoSSso.."),
}

TORSO_PAL = {
    "o": INK,
    "P": (136, 96, 168),    # plum kimono
    "p": (104, 70, 134),
    "W": (246, 244, 252),
    "G": (118, 118, 140),   # slate hakama
    "g": (90, 88, 110),
    "l": (150, 150, 172),
}

TORSO = """
..oooooo..
.oPPWWPPo.
oPPPWPPppo
oPPPPWPppo
oPPPPPPppo
oGlGGGGGgo
oGlGGGGGgo
oGlGGGgGgo
.oooooooo.
"""


def sheathed_bokuto(img, torso_xy, torso_size):
    tx, ty = torso_xy
    a, b = (tx + 9, ty + 5), (tx - 5, ty + 7)
    stamp_line(img, a, b, 4, INK)
    stamp_line(img, a, b, 2, (204, 150, 92))
    stamp_line(img, a, (tx + 7, ty + 5.3), 2, (96, 58, 40))


TAKASUGI_KID = register(LayeredDef(
    id="takasugi_kid", name="小高杉", color=(118, 70, 160), voice=1.18,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(5, 2), hip=(5, 6), shoulder_f=(7, 3), shoulder_b=(2, 3),
    arm_len=5, arm_w=2, sleeve_f=(136, 96, 168), sleeve_b=(100, 70, 128), sleeve_frac=0.65,
    hand=(255, 218, 188),
    leg_len=5, leg_w=3, leg_gap=3, pants=(118, 118, 140), shoes=(40, 34, 44), shoe_h=1,
    weapon="bokuto", weapon_len=13, sheathed=sheathed_bokuto,
    portrait_crop=14,
    desc="松下私塾的好胜少年，紫黑短发、双眼锐利，天天找银时单挑却从没赢过。",
))
