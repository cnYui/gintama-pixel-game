"""天人(猫) — cat-faced amanto thug.

Full orange tabby cat head (forehead stripes, pointy ears, slit eyes, white muzzle,
':3' mouth, whiskers poking out), dark purple thug kimono with orange sash,
furry paws/feet, katana at the hip.  Extra poses: `hiss` (arched, claws out), `laugh`.
"""
from engine.core import step_frame
from engine.gfx import INK, stamp_line, pset
from chars import register
from chars.rig import ChibiDef, pose_idle, _blink

HEAD_PAL = {
    "o": INK,
    "F": (240, 156, 72),    # orange fur
    "f": (206, 116, 48),    # fur shade
    "L": (255, 204, 130),   # fur light
    "s": (176, 84, 36),     # tabby stripes
    "d": (190, 100, 44),    # outline-side shade
    "P": (255, 170, 176),   # inner ear
    "W": (255, 246, 232),   # muzzle
    "w": (255, 255, 255),
    "N": (240, 110, 130),   # nose
    "Y": (200, 230, 80),    # slit eyes
    "R": (255, 70, 60),     # angry glow
    "m": (140, 40, 60),
    "T": (120, 200, 255),
}

# 20 wide (whiskers poke 1 px out of the 18 px head), 19 tall (ears on top)
BASE = [
    "...o............o...",   # 0
    "...oo..........oo...",   # 1
    "...oPo........oPo...",   # 2
    "...oPFo......oFPo...",   # 3
    "..oFPFFooooooFFPFo..",   # 4
    "..oFFFLLFsFFsFFFFo..",   # 5
    ".odFFLLFFsFFsFFsFFo.",   # 6
    ".odFFLFFFFFFFFFsFFo.",   # 7
    ".odFFFFFFFFFFFFFFFo.",   # 8
    ".odFFoooFFFoooFFFFo.",   # 9  lids
    ".odFFYoYFFFYoYFFFFo.",   # 10 slit eyes
    ".odFFYoYFFFYoYFFFFo.",   # 11
    "oodFFFFFFWNNWFFFFFoo",   # 12 whiskers + nose
    ".odfFFFFWWoWWoWFFFo.",   # 13 :3 mouth
    "oodffFFFWWWoWWWFFFoo",   # 14 whiskers
    "..odfFFFFWWWWWFFfo..",   # 15
    "...oodffFFFFFFfoo...",   # 16
    ".....ooooooooooo....",   # 17
]
for _i, _r in enumerate(BASE):
    assert len(_r) == 20, (_i, _r, len(_r))


def _head(**rows):
    r = list(BASE)
    for k, v in rows.items():
        i = int(k[1:])
        assert len(v) == len(BASE[i]), (k, v, len(v))
        r[i] = v
    return "\n".join(r)


HEADS = {
    "normal": _head(),
    "blink": _head(r9=".odFFFFFFFFFFFFFFFo.", r10=".odFFoooFFFoooFFFFo.", r11=".odFFFFFFFFFFFFFFFo."),
    "talk": _head(r13=".odfFFFFWWoWoWWFFFo.", r14="oodffFFFWWWmmWWFFFoo"),
    "angry": _head(r8=".odFFoFFFFFFFFoFFFo.", r9=".odFFFooFFFooFFFFFo.", r10=".odFFYoRFFFRoYFFFFo.",
                   r11=".odFFYoYFFFYoYFFFFo."),
    "shout": _head(r8=".odFFoFFFFFFFFoFFFo.", r9=".odFFFooFFFooFFFFFo.", r10=".odFFYoRFFFRoYFFFFo.",
                   r13=".odfFFFFWoooooWFFFo.", r14="oodffFFFWommmoWFFFoo", r15="..odfFFFFWoooWFFfo.."),
    "shock": _head(r9=".odFoooooFoooooFFFo.", r10=".odFowwwoFowwwoFFFo.", r11=".odFoooooFoooooFFFo.",
                   r13=".odfFFFFWWWoWWWFFFo.", r14="oodffFFFWWoWoWWFFFoo"),
    "happy": _head(r9=".odFFFFFFFFFFFFFFFo.", r10=".odFFFoFFFFFoFFFFFo.", r11=".odFFoFoFFFoFoFFFFo.",
                   r14="oodffFFFWWmmmWWFFFoo"),
    "sad": _head(r8=".odFFFFoFFFoFFFFFFo.", r9=".odFooFFFFFFFooFFFo.",
                 r13=".odfFFFFWWWoWWWFFFo.", r14="oodffFFFWWoWoWWFFFoo"),
    "cry": _head(r8=".odFFFFoFFFoFFFFFFo.", r9=".odFooFFFFFFFooFFFo.", r10=".odFFTTTFFFTTTFFFFo.",
                 r11=".odFFFTFFFFFTFFFFFo.", r12="oodFFFTFFWNNWTFFFFoo"),
    "hurt": _head(r9=".odFFoFoFFFoFoFFFFo.", r10=".odFFFoFFFFFoFFFFFo.", r11=".odFFoFoFFFoFoFFFFo.",
                  r14="oodffFFFWWoWoWWFFFoo"),
    "smug": _head(r10=".odFFoooFFFoooFFFFo.", r11=".odFFYoYFFFYoYFFFFo.", r9=".odFFFFFFFFFFFFFFFo.",
                  r13=".odfFFFFWWoWWoooFFo."),
}

TORSO_PAL = {
    "o": INK,
    "F": (240, 156, 72),    # chest fur
    "f": (206, 116, 48),
    "K": (84, 58, 104),     # dark purple kimono
    "k": (60, 40, 76),
    "l": (120, 90, 142),
    "O": (250, 150, 50),    # orange sash
    "r": (196, 100, 34),
    "M": (170, 176, 196),   # metal bracer
}

TORSO = """
....oooooo....
...oKFFFFKo...
..olKKFFfKKo..
.olKKKFFKKkko.
.olKKKKFKKKko.
.oKKKKKKKKKko.
.oOOOOOOOOOro.
.oKKKKKKKKKko.
.okKKKKKKKkko.
.okKKKKKKKkko.
.okkKkKkKkkko.
..oooooooooo..
"""


def sheathed_katana(img, torso_xy, torso_size):
    tx, ty = torso_xy
    a, b = (tx + 11, ty + 6), (tx - 4, ty + 10)
    stamp_line(img, a, b, 4, INK)
    stamp_line(img, (tx + 8, ty + 6.8), b, 2, (120, 40, 50))
    stamp_line(img, a, (tx + 8, ty + 6.8), 2, (60, 50, 60))
    pset(img, tx + 8, ty + 6, (230, 180, 60))


def pose_idle_cat(pp, t, p, d):
    pose_idle(pp, t, p, d)
    pp["expr"] = "blink" if _blink(t, 2.9) else ("smug" if step_frame(t, 1, 4) == 2 else "normal")


def pose_hiss(pp, t, p, d):
    """Arched back, both clawed paws up, fur bristling (shakes)."""
    f = step_frame(t, 12, 2)
    pp["arm_f"] = 120
    pp["arm_b"] = 130
    pp["lean"] = 1
    pp["legs"] = "spread"
    pp["head_dx"] = 1 if f else 0
    pp["bob"] = -1 if f else 0
    pp["expr"] = "shout"

    def claws(img, ctx):
        for h in (ctx["hand_f"], ctx["hand_b"]):
            if h:
                x, y = int(h[0]), int(h[1])
                for dx in (-1, 1, 3):
                    pset(img, x + dx, y - 2, (255, 255, 255))
    pp["props"] = [claws]


def pose_laugh(pp, t, p, d):
    f = step_frame(t, 10, 2)
    pp["arm_f"] = 100 if f else 90
    pp["arm_b"] = 20
    pp["lean"] = -1
    pp["head_dy"] = -1 if f else 0
    pp["bob"] = -1 if f else 0
    pp["expr"] = "happy" if f else "shout"


AMANTO_CAT = register(ChibiDef(
    id="amanto_cat", name="天人(猫)", color=(222, 120, 40), voice=0.8,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=(84, 58, 104), sleeve_b=(60, 40, 76), sleeve_frac=0.7,
    hand=(240, 156, 72),
    leg_len=7, leg_w=3, leg_gap=4, pants=(70, 50, 88), shoes=(240, 156, 72), shoe_h=1,
    weapon="katana", weapon_len=16, sheathed=sheathed_katana,
    poses={"idle": pose_idle_cat, "hiss": pose_hiss, "laugh": pose_laugh},
    desc="猫脸天人打手。橘色虎斑，竖瞳，嘴角『:3』，腰挂武士刀的街头恶棍。",
))
