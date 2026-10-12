"""春雨 Harusame — space-pirate grunt.

Green scaly reptile/fish head with a red fin crest, yellow slit eyes under heavy
brow ridges, gill slits and a wide toothy grin; dark navy space armour with metal
pauldrons and red trim; curved blade.  Extra poses: `charge` (running with blade
raised, yelling), `laugh`.
"""
from engine.core import step_frame
from engine.gfx import INK, stamp_line, pset
from chars import register
from chars.rig import ChibiDef, pose_idle, pose_run, _blink

HEAD_PAL = {
    "o": INK,
    "G": (122, 184, 112),   # scales
    "g": (84, 142, 92),     # scale shade
    "d": (56, 104, 74),     # deep shade
    "L": (176, 222, 140),   # highlight
    "F": (238, 92, 72),     # fin crest
    "f": (176, 50, 56),
    "Y": (252, 222, 64),    # eyes
    "R": (255, 60, 50),
    "W": (250, 248, 232),   # teeth
    "w": (255, 255, 255),
    "m": (120, 30, 50),     # mouth inside
    "T": (120, 200, 255),
}

# 18 wide x 20 tall (fin crest on top); chin = last row
BASE = [
    "......o...o...o...",   # 0  fin spikes
    ".....oFo.oFo.oFo..",   # 1
    ".....oFfooFfooFfo.",   # 2
    "....ooFFFFFFFFFoo.",   # 3
    "...ooGGLLGGGGGGGoo",   # 4
    "..oGLLGGGGGGgGGGGo",   # 5
    ".oGLLGGGgGGGGGGGGo",   # 6
    "odGGGGGGGGGgGGGGGo",   # 7
    "odGGgGGGGGGGGGgGGo",   # 8
    "odGGoooGGGGGoooGGo",   # 9  brow ridges
    "odgGYoYGGGGGYoYGGo",   # 10 slit eyes
    "odgGYoYGGGGGYoYGGo",   # 11
    "odgdGGGGGGGGGGGoGo",   # 12 nostril
    "odgdGGGGGGGGGGGGGo",   # 13 gills
    "odgdoooooooooooooo",   # 14 wide mouth line
    ".odgWoWoWoWoWoWgo.",   # 15 teeth
    "..odgGGGGGGGGGgo..",   # 16
    "...oodggggggdoo...",   # 17
    ".....oooooooooo...",   # 18
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
    "blink": _head(r10="odgGGGGGGGGGGGGGGo", r11="odgGoooGGGGGoooGGo"),
    "talk": _head(r15=".odgWmWmWmWmWmWgo.", r16="..odgWoWoWoWoWgo.."),
    "angry": _head(r9="odGGoGGGGGGGGGoGGo", r10="odgGYooGGGGGooYGGo", r11="odgGYRYGGGGGYRYGGo"),
    "shout": _head(r9="odGGoGGGGGGGGGoGGo", r10="odgGYooGGGGGooYGGo", r11="odgGYRYGGGGGYRYGGo",
                   r15=".odgWmmmmmmmmmWgo.", r16="..odgWoWoWoWoWgo.."),
    "shock": _head(r9="odGoooooGGGoooooGo", r10="odGowwwoGGGowwwoGo", r11="odGoooooGGGoooooGo",
                   r15=".odgWmmmmmmmmmWgo."),
    "happy": _head(r9="odGGGGGGGGGGGGGGGo", r10="odgGGoGGGGGGGoGGGo", r11="odgGoGoGGGGGoGoGGo"),
    "sad": _head(r9="odGGGGoGGGGGoGGGGo", r10="odgGooYGGGGGYooGGo"),
    "cry": _head(r9="odGGGGoGGGGGoGGGGo", r10="odgGooYGGGGGYooGGo", r11="odgGTTTGGGGGTTTGGo",
                 r12="odgdGTGGGGGGGTGoGo", r13="odgdGTGGGGGGGTGGGo"),
    "hurt": _head(r10="odgGoGoGGGGGoGoGGo", r11="odgGGoGGGGGGGoGGGo",
                  r15=".odgWWWWWWWWWWWgo."),
    "smug": _head(r10="odgGGGGGGGGGGGGGGo", r11="odgGoooGGGGGoooGGo", r12="odgdGYoYGGGGYoYoGo"),
}
HEADS["smug"] = _head(r10="odgGGGGGGGGGGGGGGo", r11="odgGYoYGGGGGYoYGGo")

TORSO_PAL = {
    "o": INK,
    "G": (122, 184, 112),   # neck scales
    "A": (56, 66, 104),     # navy armour
    "a": (38, 44, 74),
    "l": (90, 104, 150),
    "M": (178, 186, 206),   # metal pauldrons
    "m": (124, 132, 160),
    "H": (236, 240, 250),
    "R": (208, 52, 62),     # red trim
    "r": (140, 34, 46),
    "Y": (240, 196, 70),    # emblem
}

TORSO = """
....oooooo....
..oooGGGGooo..
.oHMMoAAoMMMo.
oHMMmoAYoMmmmo
ommmolAAAommmo
.oooAlAAAAaoo.
..oRRRRRRRRo..
..olAAAAAAao..
.olAAAAAAAAao.
.olAAAAAAAaao.
.oRRRRRRRRRro.
..oooooooooo..
"""


def sheathed_blade(img, torso_xy, torso_size):
    tx, ty = torso_xy
    a, b = (tx + 12, ty + 7), (tx - 4, ty + 11)
    stamp_line(img, a, b, 4, INK)
    stamp_line(img, (tx + 9, ty + 7.8), b, 2, (70, 60, 50))
    stamp_line(img, a, (tx + 9, ty + 7.8), 2, (150, 40, 50))


def pose_idle_pirate(pp, t, p, d):
    pose_idle(pp, t, p, d)
    pp["arm_f"] = 20 + (2 if pp["bob"] else 0)
    pp["arm_b"] = -20
    pp["expr"] = "blink" if _blink(t, 2.3) else "normal"


def pose_charge(pp, t, p, d):
    """Running charge with the blade raised overhead, yelling."""
    pose_run(pp, t, p, d)
    pp["arm_f"] = 160
    pp["weapon"] = 125
    pp["expr"] = "shout"


def pose_laugh(pp, t, p, d):
    f = step_frame(t, 10, 2)
    pp["arm_f"] = 150
    pp["weapon"] = 160
    pp["arm_b"] = 20
    pp["lean"] = -1
    pp["head_dy"] = -1 if f else 0
    pp["bob"] = -1 if f else 0
    pp["expr"] = "shout" if f else "happy"


HARUSAME = register(ChibiDef(
    id="harusame", name="春雨", color=(48, 132, 124), voice=0.72,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=(56, 66, 104), sleeve_b=(38, 44, 74), sleeve_frac=0.55,
    hand=(122, 184, 112),
    leg_len=7, leg_w=3, leg_gap=4, pants=(46, 54, 86), shoes=(30, 30, 40), shoe_h=2,
    weapon="katana", weapon_len=16, sheathed=sheathed_blade,
    poses={"idle": pose_idle_pirate, "charge": pose_charge, "laugh": pose_laugh},
    desc="宇宙海贼『春雨』的杂兵。鳞片脸、背鳍、满嘴尖牙，成群结队打劫的天人海盗。",
))
