"""凯瑟琳 Catherine — cat-eared amanto maid of Otose's snack bar.

Grey bob hair with cat ears, sly slit-pupil cat eyes with baggy lids, thin smirk,
dark kimono + white apron.  Extra exprs: `sly` (= smug), `sleep`.
"""
from engine.core import step_frame
from engine.gfx import INK, scale_nearest
from chars import register
from chars.rig import ChibiDef, pose_idle, _blink

HEAD_PAL = {
    "o": INK,
    "H": (172, 164, 200),   # ash-lilac grey hair light
    "h": (134, 124, 168),   # hair mid
    "d": (96, 88, 132),     # hair shade
    "P": (250, 160, 180),   # inner ear pink
    "S": (255, 222, 196),   # skin
    "s": (230, 172, 150),   # skin shade / eye bags
    "Y": (236, 208, 70),    # cat eyes
    "w": (255, 255, 255),
    "m": (180, 70, 90),     # mouth
    "b": (250, 150, 160),
    "T": (120, 200, 255),
}

# 18 wide x 20 tall (3 extra rows on top for the ears); chin = last row
BASE = [
    "..o............o..",   # 0  ear tips
    "..oo..........oo..",   # 1
    "..oPo........oPo..",   # 2
    "..oPHo......oHPo..",   # 3
    ".oHPHHooooooHHPHo.",   # 4
    ".oHHHHHHHHHHHHHHo.",   # 5
    "odHHHHHhHHHHHHHHHo",   # 6
    "odHHHHHHHHHHhHHHho",   # 7
    "odhHHHHHHhHHHHHHho",   # 8
    "odhHHhHHHHHHHHHhho",   # 9
    "odhHhShHHhSHhhShho",   # 10 parted bangs
    "odhhSSShhSSSShSSho",   # 11
    "odhSSSSShSSSSSSSho",   # 12
    "odhSSoooSSSoooSSho",   # 13 heavy lids
    "odhSSYoYSSSYoYSSho",   # 14 slit cat eyes
    ".ohSSsssSSSsssSSho",   # 15 eye bags
    ".ohSSSSSSSSSSSmSho",   # 16 smirk corner
    ".odhsSSSSSmmmSsho.",   # 17 thin sly mouth
    "..odhsSSSSSSSsho..",   # 18
    "...oooooooooooo...",   # 19
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
    "blink": _head(r13="odhSSSSSSSSSSSSSho", r14="odhSSoooSSSoooSSho"),
    "talk": _head(r16=".ohSSSSSSSSSSSSSho", r17=".odhsSSSSoooSSsho.", r18="..odhsSSSmmSSsho.."),
    "angry": _head(r12="odhSoSSSHSSSSSoSho", r13="odhSSoooSSSoooSSho", r14="odhSSYoYSSSYoYSSho",
                   r16=".ohSSSSSSSSSSSSSho", r17=".odhsSSSSoooSSsho."),
    "shout": _head(r12="odhSoSSSHSSSSSoSho", r13="odhSSoooSSSoooSSho", r14="odhSSYoYSSSYoYSSho",
                   r16=".ohSSSSSSooooSSSho", r17=".odhsSSSSommoSsho.", r18="..odhsSSSooSSsho.."),
    "shock": _head(r13="odhSooooSSooooSSho", r14="odhSoYoYoSoYoYoSho", r15=".ohSooooSSooooSSho",
                   r16=".ohSSSSSSSSSSSSSho", r17=".odhsSSSSSooSSsho.", r18="..odhsSSSSooSsho.."),
    "happy": _head(r13="odhSSSoSSSSSoSSSho", r14="odhSSoSoSSSoSoSSho", r15=".ohSbbSSSSSSbbSSho",
                   r16=".ohSSSSSSSSSSSSSho", r17=".odhsSSSoSSSoSsho.", r18="..odhsSSSoooSsho.."),
    "sad": _head(r12="odhSSSoSHSSoSSSSho", r13="odhSSooSSSSSooSSho",
                 r16=".ohSSSSSSSSSSSSSho", r17=".odhsSSSSSooSSsho."),
    "cry": _head(r12="odhSSSoSHSSoSSSSho", r13="odhSSooSSSSSooSSho", r14="odhSSTTTSSSTTTSSho",
                 r15=".ohSSTSSSSSSTSSSho", r16=".ohSSTSSSSSSTSSSho", r17=".odhsTSSSooSTSsho."),
    "hurt": _head(r13="odhSSoSoSSSoSoSSho", r14="odhSSSoSSSSSoSSSho", r15=".ohSSoSoSSSoSoSSho",
                  r16=".ohSSSSSSSSSSSSSho", r17=".odhsSSSSooooSsho."),
    "smug": _head(r13="odhSSSSSSSSSSSSSho", r14="odhSSoooSSSoooSSho", r15=".ohSSYoYSSSYoYSSho",
                  r16=".ohSSSSSSSSSSmmSho", r17=".odhsSSSSmmmmSsho."),
    "sleep": _head(r13="odhSSSSSSSSSSSSSho", r14="odhSSoooSSSoooSSho",
                   r17=".odhsSSSSSSoSSsho."),
}
HEADS["sly"] = HEADS["smug"]

TORSO_PAL = {
    "o": INK,
    "S": (255, 222, 196),
    "s": (230, 172, 150),
    "K": (86, 74, 112),     # dark purple-grey kimono
    "k": (62, 52, 84),      # kimono shade
    "L": (120, 108, 150),   # kimono highlight
    "W": (250, 250, 255),   # apron
    "w": (208, 206, 226),   # apron shade
    "R": (200, 60, 80),     # red obi cord
}

TORSO = """
....oooooo....
...oLKSSKKo...
..oLKKoSoKKo..
.oLLWKKKKWKko.
.oLKWKKKKWKko.
.oKKWWWWWWKko.
.oRRWWWWWWRRo.
.okKWWWWWWKko.
.okWWWWWWWwko.
.okWWWWWWWwko.
.okwWwWwWwwko.
..oooooooooo..
"""


def pose_idle_cat(pp, t, p, d):
    """Hand on the hip, weight shifted, occasionally narrowing her eyes slyly."""
    pose_idle(pp, t, p, d)
    pp["arm_b"] = -35
    if step_frame(t, 1, 5) == 3:
        pp["expr"] = "smug"


class CatherineDef(ChibiDef):
    def portrait_fn(self, expr, t, talking):
        e = expr or "normal"
        if talking and step_frame(t, 8) % 2 == 0:
            e = "talk" if expr in (None, "normal") else e
        elif expr is None and (t % 3.1) < 0.12:
            e = "blink"
        h = self.head(e).crop((0, 2, 18, 20))
        return scale_nearest(h, 2)


CATHERINE = register(CatherineDef(
    id="catherine", name="凯瑟琳", color=(140, 110, 176), voice=1.12,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=(86, 74, 112), sleeve_b=(62, 52, 84), sleeve_frac=0.72,
    hand=(255, 222, 196),
    leg_len=7, leg_w=3, leg_gap=3, pants=(74, 62, 98), shoes=(236, 232, 240), shoe_h=1,
    weapon=None,
    poses={"idle": pose_idle_cat},
    desc="猫耳天人凯瑟琳。前小偷，现为登势酒馆的店员，一脸奸笑，嘴巴很毒。",
))
