"""伊东鸭太郎 Ito Kamotarou — Shinsengumi staff officer, ambitious schemer.

Muted light-brown side-swept hair, rectangular glasses (glint!), cold eyes,
pale grey long coat over the black uniform (coat tails flap over the legs).
Extra pose: glasses_push (finger on the bridge, lenses flash white).
Extra exprs: glint (both lenses white — scheming), cold (narrowed), smile (the
gentle final 'thank you').
"""
import math

from engine.core import step_frame, clamp
from engine.gfx import INK, stamp_line, rect, pset
from chars import register
from chars.rig import pose_idle, _blink
from chars.hijikata import (SSGDef, SSG_TORSO_PAL, SSG_PANTS, SSG_SHOES, SKIN, sheathed_katana,
                            mk_head, katana_on_shoulder, star_glint, resolve_expr)

HEAD_PAL = {
    "o": INK,
    "H": (214, 190, 156),   # hair light
    "h": (172, 142, 108),   # muted light-brown hair
    "d": (124, 98, 76),     # hair shade
    "S": (255, 222, 196),   # pale skin
    "s": (232, 176, 150),
    "g": (196, 226, 244),   # lens
    "G": (150, 186, 214),   # lens shade
    "w": (255, 255, 255),
    "E": (70, 60, 70),      # cold dark eyes
    "m": (160, 80, 88),
    "b": (250, 150, 150),
    "T": (120, 200, 255),
    "R": (228, 40, 56),
    "B": (80, 120, 220),
}

BASE = [
    "......oooooo......",   # 0
    "....ooHHHHhhoo....",   # 1
    "...oHHHHHhhhhhoo..",   # 2
    "..oHHHhhhhhhhhhho.",   # 3
    ".oHHhhhhhhhhhhhhdo",   # 4
    "ohHhhhHHhhhhhhhhdo",   # 5
    "odhhhHhhhhhhhhhhdo",   # 6
    "odhhhhhhhhhhhhhhdo",   # 7
    "odhhhhhhhhhhhhhhdo",   # 8
    "odhhSSShhhhhhhhhdo",   # 9  side-swept bangs (sweep to the front)
    "odhSSSSSShhhhhShdo",   # 10
    "odhSoooooSoooooSdo",   # 11 rectangular frames
    ".ohSogEgooogEgoSo.",   # 12 lenses + bridge
    ".ohSoooooSoooooso.",   # 13
    "..osSSSSSSSSmmSo..",   # 14 thin cool mouth
    "...oosSSSSSSSsoo..",   # 15
    ".....ooooooooo....",   # 16
]


def _h(**rows):
    return mk_head(BASE, **rows)


SMILE_MOUTH = dict(r14="..osSSSSSSmSSmSo..", r15="...oosSSSSSmmsoo..")
HEADS = {
    "normal": _h(),
    "blink": _h(r12=".ohSoGGGoooGGGoSo."),
    "talk": _h(r14="..osSSSSSSSSooSo..", r15="...oosSSSSSSmsoo.."),
    "angry": _h(r10="odhSSSSoShhhhhShdo", r12=".ohSoggEoooEggoSo.",
                r14="..osSSSSSSSmmmSo.."),
    "shout": _h(r10="odhSSSSoShhhhhShdo", r12=".ohSoggEoooEggoSo.",
                r14="..osSSSSSSSomoSo..", r15="...oosSSSSSSoooo.."),
    "shock": _h(r12=".ohSowEwooowEwoSo.", r14="..osSSSSSSSooSSo.."),
    "happy": _h(r12=".ohSoGoGoooGoGoSo.", **SMILE_MOUTH),
    "sad": _h(r10="odhSSSoSShhhhhShdo", r14="..osSSSSSSSooSSo.."),
    "cry": _h(r12=".ohSoTTgoooTTgoSo.", r14="..osSTSSSSSTooSo..",
              r15="...oosTSSSSTSsoo.."),
    "hurt": _h(r12=".ohSoEgEoooEgEoSo.", r14="..osSSSSSSSooSSo.."),
    "smug": _h(r12=".ohSogEgooowwwoSo.", r14="..osSSSSSSSmmoSo.."),
    "glint": _h(r12=".ohSowwwooowwwoSo.", r14="..osSSSSSSSSmoSo.."),
    "cold": _h(r12=".ohSoGEGoooGEGoSo.", r14="..osSSSSSSSSmmSo.."),
    "smile": _h(r12=".ohSoGoGoooGoGoSo.", **SMILE_MOUTH),
    "sleep": _h(r12=".ohSoGGGoooGGGoSo.", r14="..osSSSSSSSSoSSo.."),
}

# pale grey long coat open over the black uniform; tails fall over the thighs
TORSO_PAL = dict(SSG_TORSO_PAL)
TORSO_PAL.update({"C": (232, 234, 242), "c": (182, 188, 208), "x": (140, 146, 172)})
TORSO = """
....oooooo....
...oCWWWWCo...
..oCCKWWKCCo..
.oCCCYWWYCcco.
.oCCCKYWYKCco.
.oCCCKKYKKCco.
.oCCCKKYKKCco.
.oCCCKKyKKCco.
.oCCCKKYKKCco.
.oCCCyYYYyCco.
.oCCCoooooCco.
.oCCco...oCco.
.oCcco...occo.
.occxo...oxco.
..ooo.....ooo.
"""


def ito_sheath(img, torso_xy, torso_size):
    sheathed_katana(img, torso_xy, (torso_size[0], 12))


def glint_prop(img, ctx):
    """Random-ish glasses glint on 'glint'/'smug' faces (4-point star on a lens)."""
    pp = ctx["params"]
    if pp["rot"]:
        return
    e = resolve_expr(ctx["def"], pp["expr"])
    if e not in ("glint", "smug"):
        return
    hx, hy, _, _ = ctx["head"]
    f = step_frame(ctx["t"], 8, 12)
    if f < 5:
        star_glint(img, int(hx) + 12, int(hy) + 11, 2 if f in (1, 2, 3) else 1)


def pose_glasses_push(pp, t, p, d):
    """Pushes his glasses up with one finger; the lenses flash (loops every 1.6 s).
    The arm passes behind the head so the glasses stay readable."""
    pose_idle(pp, t, p, d)
    ph = (t % 1.6) / 1.6
    push = 0.2 <= ph < 0.75
    if ph < 0.2:
        pp["arm_f"] = 20 + ph / 0.2 * 150
        pp["expr"] = "cold"
    elif push:
        pp["arm_f"] = 185
        pp["hide_arm_f"] = True
        pp["expr"] = "glint"
        pp["head_dy"] = -1 if ph < 0.3 else 0

        def arm_behind(img, pc):
            from chars.rig import _draw_arm
            _draw_arm(img, d, pc["sf"], 185, d.sleeve_f)
        pp["pre"] = [arm_behind]
    else:
        pp["arm_f"] = 170 - (ph - 0.75) / 0.25 * 150
        pp["expr"] = "cold"
    pp["arm_b"] = -10

    def finger(img, ctx, push=push, ph=ph):
        if not push:
            return
        X, Y, _, _ = ctx["head"]
        bx, by = int(X) + 9, int(Y) + 12          # bridge of the glasses
        rect(img, bx - 2, by + 2, 5, 4, INK)       # little fist under the nose
        rect(img, bx - 1, by + 3, 3, 2, SKIN)
        rect(img, bx - 1, by - 1, 3, 4, INK)       # index finger on the bridge
        rect(img, bx, by, 1, 3, SKIN)
        k = (ph - 0.2) / 0.55
        if k < 0.5:
            star_glint(img, int(X) + 13, int(Y) + 11, 2 if k < 0.3 else 1)
    pp["props"] = [finger]


def pose_ito_idle(pp, t, p, d):
    pose_idle(pp, t, p, d)
    if not _blink(t):
        pp["expr"] = "normal"


ITO = register(SSGDef(
    id="ito", name="伊东", color=(96, 110, 150), voice=0.84,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=(226, 228, 238), sleeve_b=(160, 166, 188), sleeve_frac=0.8,
    hand=SKIN,
    leg_len=7, leg_w=3, leg_gap=4, pants=SSG_PANTS, shoes=SSG_SHOES,
    weapon="katana", weapon_len=17, sheathed=ito_sheath,
    poses={"glasses_push": pose_glasses_push, "shoulder": katana_on_shoulder},
    always=[glint_prop],
    desc="真选组参谋。浅棕发、方框眼镜反光、冷漠的野心家，白色长外套下是真选组制服。",
))
