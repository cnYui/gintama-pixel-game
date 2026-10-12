"""日轮 Hinowa — the 'Sun of Yoshiwara', Seita's mother.

Oiran: black hair in a big hyogo-mage with a gold comb, flower ornaments and
gold kanzashi fanning out (pins drawn behind the head), red/gold kimono with a
big mae-obi, floor-length hem (legs hidden). She cannot walk:
  sit        : seated in her wooden wheelchair (default feet anchor = wheel
               bottom). Seita's `push` pose lines up with the handles when his
               feet are at hinowa_x - 21 (same y).  kw chair=0 -> cushion instead.
  sit_talk   : same, mouth flapping
  smile      : seated, hands together at the chest, warm smile
  sit_cushion: kneeling (seiza) on a purple zabuton cushion
Extra exprs: smile, determined.
"""
import math

from PIL import ImageDraw

from engine.core import step_frame, clamp
from engine.gfx import INK, stamp_line
from chars import register
from chars.rig import pose_idle, _blink
from chars.shouyou import LayeredDef

HAIR = (58, 54, 84)
HEAD_PAL = {
    "o": INK,
    "L": (116, 116, 164),   # hair highlight
    "H": HAIR,
    "h": (44, 40, 66),
    "d": (34, 30, 50),
    "G": (246, 202, 84),    # gold comb
    "g": (196, 146, 48),
    "R": (222, 58, 70),     # red ornaments
    "P": (255, 176, 196),   # flower
    "p": (236, 120, 150),
    "S": (255, 238, 226),   # pale oiran make-up skin
    "s": (238, 200, 186),
    "r": (244, 170, 176),   # soft red eye make-up
    "E": (84, 46, 62),
    "w": (255, 255, 255),
    "m": (214, 36, 60),     # red lips
    "b": (252, 170, 176),
    "T": (120, 200, 255),
}

BASE = [
    "......oooo..oooo......",   # 0  hyogo loops
    ".....oHLHHooHHLHo.....",   # 1
    "....oHHdHHHHHHdHHo....",   # 2
    "....oHHHHHHHHHHHHHo...",   # 3
    "..ooHHHGRGGGGGRGHHHoo.",   # 4  gold comb
    ".oHHLLHHHHHHHHHHHHHHo.",   # 5
    "oHHLHHHHHHHHHHHHHHHHHo",   # 6
    "oHLHHHHhHHHHHHHhHHHHho",   # 7
    "odHHHHHHHHHHHHHHHHHHho",   # 8
    "odHHHPPHHHHHHHHHHHPPho",   # 9  flowers
    "odHHPpPHHHHHHHHHHHHPdo",   # 10
    ".odHHPHHHHHHHHHHHHHdo.",   # 11
    ".odHHHHHHSHHHSHHHHHdo.",   # 12 bangs
    ".odHHHHHSSSHHSSSHHHdo.",   # 13
    ".odHHSSSSSSSSSSSSHHdo.",   # 14
    ".odHHSroooSSSooorHHdo.",   # 15 soft lids + red make-up
    ".odHHSSwEESSSwEESHHdo.",   # 16
    ".odHHSSSSSSSSSSSSHHdo.",   # 17
    ".odHHsSSSSSSmmSSsHHdo.",   # 18 red lips
    ".odHHosSSSSSSSSsoHHdo.",   # 19
    ".oddHooooooooooooHddo.",   # 20
    "..ooo............ooo..",   # 21
]


def _head(**rows):
    r = list(BASE)
    for k, v in rows.items():
        i = int(k[1:])
        assert len(v) == len(BASE[i]), (k, v, len(v), len(BASE[i]))
        r[i] = v
    return "\n".join(r)


F = ".odHH%sHHdo."    # face row template: 12 face pixels between the hair puffs
HEADS = {
    "normal": _head(),
    "blink": _head(r15=F % "SrSSSSSSSSrS", r16=F % "SSoooSSSoooS"),
    "talk": _head(r18=F % "sSSSSSSooSSs", r19=F % "osSSSSSmmSso"),
    "smile": _head(r15=F % "SrSoSSSSSoSr", r16=F % "SSoSoSSSoSoS", r17=F % "SbbSSSSSSbbS",
                   r18=F % "sSSSSSmSSmSs", r19=F % "osSSSSSmmSso"),
    "happy": _head(r15=F % "SrSoSSSSSoSr", r16=F % "SSoSoSSSoSoS", r17=F % "SbbSSSSSSbbS",
                   r18=F % "sSSSSSooooSs", r19=F % "osSSSSSmmSso"),
    "determined": _head(r14=F % "SSSoSSSSoSSS", r16=F % "SSwEESSSwEES"),
    "angry": _head(r14=F % "SSoSSSSSSoSS", r15=F % "SrSoooSooorS", r16=F % "SSSEEwSEEwSS",
                   r18=F % "sSSSSSmmmSSs"),
    "shout": _head(r14=F % "SSoSSSSSSoSS", r15=F % "SrSoooSooorS", r16=F % "SSSEEwSEEwSS",
                   r17=F % "SSSSSSooSSSS", r18=F % "sSSSSomoSSSs", r19=F % "osSSSSooSSso"),
    "shock": _head(r15=F % "SSooSSSSooSS", r16=F % "SowwoSSowwoS", r17=F % "SSooSSSSooSS",
                   r18=F % "sSSSSSSoSSSs", r19=F % "osSSSSSoSSso"),
    "sad": _head(r14=F % "SSSSoSSoSSSS", r15=F % "SrooSSSSSoor", r16=F % "SSwEESSSwEES",
                 r18=F % "sSSSSSSmmSSs"),
    "cry": _head(r14=F % "SSSSoSSoSSSS", r15=F % "SrooSSSSSoor", r16=F % "SSTTTSSSTTTS",
                 r17=F % "SSTSSSSSTSSS", r18=F % "sSTSSSmSTmSs", r19=F % "osTSSSSmmSso"),
    "hurt": _head(r15=F % "SSoSoSSSoSoS", r16=F % "SSSoSSSSSoSS", r17=F % "SSoSoSSSoSoS",
                  r18=F % "sSSSSSSooSSs"),
    "smug": _head(r15=F % "SrSSSSSSSSrS", r16=F % "SSoooSSSoooS", r18=F % "sSSSSSSSSmSs",
                  r19=F % "osSSSSSmmmso"),
    "sleep": _head(r15=F % "SrSSSSSSSSrS", r16=F % "SSoooSSSoooS"),
}
HEAD_ANCHOR = (11, 20)

TORSO_PAL = {
    "o": INK,
    "R": (212, 46, 60),     # red outer kimono
    "r": (156, 28, 46),
    "Q": (240, 104, 110),   # red highlight
    "W": (252, 248, 240),   # white collar
    "Y": (246, 200, 84),    # gold obi / pattern
    "y": (196, 146, 50),
    "K": (70, 40, 80),      # dark obi pattern
}

# long standing kimono: hem trails to the floor (hip row 9, floor row 16)
TORSO_LONG = """
....oooooo....
...oRWWWWRo...
..oRRRWWRRro..
.oQRYRRWRRYro.
.oQRRRRRRRRro.
.oYYYYYYYYYyo.
.oYKYYKYYKYyo.
.oQRYYYYYYRro.
.oQRRYyYyRRro.
.oRYRRYKYRYro.
.oRRRRYyYRRro.
.oQRRRRRRRRro.
.oRYRRRRRYRro.
.oQRRRRRRRrro.
oRRRYRRRRYRrro
oRYRRRRRRRRYro
.oooooooooooo.
"""
# seated (wheelchair): cut at the hip, the lap is drawn separately
TORSO_SIT = """
....oooooo....
...oRWWWWRo...
..oRRRWWRRro..
.oQRYRRWRRYro.
.oQRRRRRRRRro.
.oYYYYYYYYYyo.
.oYKYYKYYKYyo.
.oQRYYYYYYRro.
.oQRRYyYyRRro.
.oRYRRYKYRYro.
.oRRRRYyYRRro.
..oooooooooo..
"""
# seiza on a cushion: kimono spreads over the folded legs
TORSO_SEIZA = """
....oooooo....
...oRWWWWRo...
..oRRRWWRRro..
.oQRYRRWRRYro.
.oQRRRRRRRRro.
.oYYYYYYYYYyo.
.oYKYYKYYKYyo.
.oQRYYYYYYRro.
.oQRRYyYyRRro.
.oRYRRYKYRYroo.
oRRRRYyYRRRRRro
oRYRRRRRRRRYRro
.ooooooooooooo.
"""
KIMONO, KIMONO_D, GOLD = (212, 46, 60), (156, 28, 46), (246, 200, 84)
WOOD, WOOD_D, WOOD_L = (150, 98, 58), (104, 64, 40), (196, 140, 88)


def kanzashi(img, ctx):
    """Gold hairpins fanning out of the hairdo (drawn behind the head)."""
    hx, hy, hw, hh = ctx["head"]
    cx, cy = hx + 11, hy + 8
    pins = ((-13, -5), (-12, -1), (-10, -9), (13, -5), (12, -1), (10, -9))
    for dx, dy in pins:
        stamp_line(img, (cx, cy), (cx + dx, cy + dy), 3, INK)
    for dx, dy in pins:
        stamp_line(img, (cx, cy), (cx + dx, cy + dy), 1, GOLD)
    for i, (dx, dy) in enumerate(pins):
        x, y = cx + dx, cy + dy
        stamp_line(img, (x, y), (x, y), 3, INK)
        stamp_line(img, (x, y), (x, y), 1, (222, 58, 70) if i % 3 == 0 else (255, 236, 150))
    # dangling bira-bira strings on the outer pins
    sw = 1 if step_frame(ctx["t"], 2, 2) else 0
    for dx, dy in ((-13, -5), (13, -5)):
        x, y = cx + dx, cy + dy
        for k in (-1, 1):
            stamp_line(img, (x + k, y + 1), (x + k + sw * k * 0, y + 4), 1, GOLD)


def _chair_geom(ctx):
    hip = ctx["hip"]
    return hip[0], hip[1]


def wheelchair_back(img, ctx):
    """Far wheel, frame, seat, backrest, push handles + her lap and feet."""
    if not ctx["params"].get("chair", 1):
        return cushion(img, ctx)
    hx, hy = _chair_geom(ctx)
    gy = 79                                   # ground row (OY - 1)
    dr = ImageDraw.Draw(img)
    # far wheel (peeks out behind)
    wx, wy = hx - 1, gy - 6
    dr.ellipse([wx - 6, wy - 6, wx + 6, wy + 6], outline=INK, width=3)
    dr.ellipse([wx - 5, wy - 5, wx + 5, wy + 5], outline=WOOD_D, width=1)
    # backrest + push handles
    stamp_line(img, (hx - 6, hy + 1), (hx - 7, hy - 14), 5, INK)
    stamp_line(img, (hx - 6, hy + 1), (hx - 7, hy - 14), 3, WOOD)
    stamp_line(img, (hx - 7, hy), (hx - 7, hy - 13), 1, WOOD_L)
    stamp_line(img, (hx - 7, hy + 1), (hx - 13, hy + 1), 4, INK)
    stamp_line(img, (hx - 7, hy + 1), (hx - 13, hy + 1), 2, WOOD_D)
    stamp_line(img, (hx - 13, hy + 1), (hx - 13, hy + 1), 3, (60, 40, 30))
    # seat + legs of the chair + footrest
    stamp_line(img, (hx - 6, hy + 2), (hx + 7, hy + 2), 4, INK)
    stamp_line(img, (hx - 6, hy + 2), (hx + 7, hy + 2), 2, WOOD)
    stamp_line(img, (hx + 6, hy + 2), (hx + 9, gy - 3), 3, INK)
    stamp_line(img, (hx + 6, hy + 2), (hx + 9, gy - 3), 1, WOOD_D)
    stamp_line(img, (hx + 7, gy - 3), (hx + 12, gy - 3), 3, INK)
    stamp_line(img, (hx + 7, gy - 3), (hx + 12, gy - 3), 1, WOOD)
    dr.ellipse([hx + 9, gy - 3, hx + 12, gy], fill=INK)                 # caster
    dr.ellipse([hx + 10, gy - 2, hx + 11, gy - 1], fill=WOOD_D)
    # lap (thighs) + shins under the kimono, white tabi feet on the footrest
    knee = (hx + 7, hy + 1)
    foot = (hx + 9, gy - 5)
    stamp_line(img, (hx, hy - 1), knee, 7, INK)
    stamp_line(img, knee, foot, 6, INK)
    stamp_line(img, (hx, hy - 1), knee, 5, KIMONO)
    stamp_line(img, (hx + 1, hy - 3), (knee[0], hy - 2), 1, (240, 104, 110))
    stamp_line(img, knee, foot, 4, KIMONO_D)
    stamp_line(img, (knee[0] - 1, knee[1] + 1), (foot[0] - 1, foot[1]), 1, GOLD)
    stamp_line(img, (foot[0] + 1, foot[1] + 1), (foot[0] + 2, foot[1] + 1), 3, INK)
    stamp_line(img, (foot[0] + 1, foot[1] + 1), (foot[0] + 2, foot[1] + 1), 1, (250, 250, 255))


def wheelchair_front(img, ctx):
    """Near big wheel with spokes (in front of her hip)."""
    if not ctx["params"].get("chair", 1):
        return
    hx, hy = _chair_geom(ctx)
    gy = 79
    wx, wy = hx - 3, gy - 6
    dr = ImageDraw.Draw(img)
    rot = step_frame(ctx["t"], 6, 2) * 22 if ctx["params"].get("rolling") else 0
    dr.ellipse([wx - 6, wy - 6, wx + 6, wy + 6], outline=INK, width=1)
    dr.ellipse([wx - 5, wy - 5, wx + 5, wy + 5], outline=WOOD, width=2)
    dr.ellipse([wx - 4, wy - 4, wx + 4, wy + 4], outline=INK, width=1)
    for a in (0, 45, 90, 135):
        r = math.radians(a + rot)
        dx, dy = math.cos(r) * 3.5, math.sin(r) * 3.5
        stamp_line(img, (wx - dx, wy - dy), (wx + dx, wy + dy), 1, WOOD_D)
    stamp_line(img, (wx, wy), (wx, wy), 3, INK)
    stamp_line(img, (wx, wy), (wx, wy), 1, GOLD)
    dr.arc([wx - 5, wy - 5, wx + 5, wy + 5], 180, 260, fill=WOOD_L, width=1)


def cushion(img, ctx):
    """Purple zabuton under her (for chair=0 / sit_cushion)."""
    hip = ctx["hip"]
    x0, x1, gy = hip[0] - 9, hip[0] + 11, 79
    dr = ImageDraw.Draw(img)
    dr.rectangle([x0, gy - 3, x1, gy], fill=INK)
    dr.rectangle([x0 + 1, gy - 2, x1 - 1, gy - 1], fill=(130, 70, 150))
    dr.line([x0 + 1, gy - 2, x1 - 1, gy - 2], fill=(170, 110, 190))
    for x in (x0, x1):
        dr.point((x, gy - 3), fill=(246, 200, 84))


def _seated(pp, t, chair=1):
    f = step_frame(t, 4, 4)
    pp["legs"] = "sit"
    pp["torso"] = "sit"
    pp["dy"] = -7
    pp["chair"] = chair
    pp["arm_f"] = 38
    pp["arm_b"] = 30
    pp["bob"] = -1 if f in (1, 2) else 0
    pp["back_props"] = [wheelchair_back]
    pp["props"] = [wheelchair_front]
    pp["expr"] = "blink" if _blink(t, 3.4) else "normal"


def pose_sit(pp, t, p, d):
    _seated(pp, t)


def pose_sit_talk(pp, t, p, d):
    _seated(pp, t)
    pp["expr"] = "talk" if step_frame(t, 8) % 2 == 0 else "normal"
    pp["arm_f"] = 50 + 8 * math.sin(t * 4)


def pose_smile(pp, t, p, d):
    _seated(pp, t)
    pp["arm_f"] = 70
    pp["arm_b"] = 68
    pp["expr"] = "blink" if _blink(t, 3.4) else "smile"


def pose_sit_cushion(pp, t, p, d):
    f = step_frame(t, 4, 4)
    pp["legs"] = "sit"
    pp["torso"] = "seiza"
    pp["dy"] = 1
    pp["arm_f"] = 45
    pp["arm_b"] = 38
    pp["bob"] = -1 if f in (1, 2) else 0
    pp["chair"] = 0
    pp["back_props"] = [cushion]
    pp["expr"] = "blink" if _blink(t, 3.4) else "smile"


def pose_kneel_h(pp, t, p, d):
    pose_sit_cushion(pp, t, p, d)
    pp["back_props"] = []
    pp["expr"] = "sad"
    pp["head_dy"] = 1


def pose_idle_h(pp, t, p, d):
    pose_idle(pp, t, p, d)
    pp["arm_f"] = 30 + (3 if pp["bob"] else 0)
    pp["arm_b"] = 25


HINOWA = register(LayeredDef(
    id="hinowa", name="日轮", color=(206, 56, 70), voice=1.1,
    heads=HEADS, head_pal=HEAD_PAL, head_anchor=HEAD_ANCHOR,
    torso={"default": TORSO_LONG, "sit": TORSO_SIT, "seiza": TORSO_SEIZA}, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 4), shoulder_b=(3, 4),
    arm_len=7, arm_w=2, sleeve_f=(212, 46, 60), sleeve_b=(156, 28, 46), sleeve_frac=0.75,
    hand=(255, 238, 226),
    leg_len=7, leg_w=3, leg_gap=4, pants=KIMONO, shoes=(40, 30, 40), legs_hidden=True,
    weapon=None, sheathed=None,
    poses={"sit": pose_sit, "sit_talk": pose_sit_talk, "smile": pose_smile,
           "sit_cushion": pose_sit_cushion, "kneel": pose_kneel_h, "idle": pose_idle_h},
    back_layers=(kanzashi,), portrait_crop=(4, 21),
    desc="吉原第一花魁『吉原的太阳』，晴太的养母。发髻插满金簪，笑容温柔；被凤仙挑断脚筋，只能坐轮椅。",
))
