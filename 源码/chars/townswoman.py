"""路人(女) townswoman — Edo commoner for crowds.

Hair tied up in a bun with a kanzashi hairpin (flower), side 'bin' puffs,
long kimono with a wide obi, white tabi.  kw variant=0..3 (default 0):
  0  black hair, indigo kimono, gold obi
  1  brown hair, purple kimono, pink obi
  2  black hair, red kimono, cream obi (young girl, pink flower)
  3  old lady: grey bun, brown-grey kimono, dark obi
Extra poses: `gossip` (hand at mouth), `flee` (= run_away), `cheer_crowd`, `fan` (fanning herself).
"""
from engine.core import step_frame
from engine.gfx import INK, stamp_line, pset
from chars import register
from chars.rig import ChibiDef, pose_idle, pose_run_away, _blink

# 18 wide x 19 tall (bun on top); chin = last row
BASE = [
    ".....oooooo.......",   # 0  bun
    "....oHHHHhho..oo..",   # 1
    "....oHhhhhdo.oRRo.",   # 2  kanzashi flower
    "...ooodddooYYoRo..",   # 3  pin
    "...oHHHHHHHhhoo...",   # 4
    "..oHHHHHhhhhhhho..",   # 5
    ".oHHHHhhhhhhhhhho.",   # 6
    "odHHhhhhhhhhhhhhho",   # 7
    "odHhhhhhhhhhhhhhho",   # 8
    "odhhhhhhhSShhhhhho",   # 9  centre parting
    "odhhhhhSSSSShhhhho",   # 10
    "odhhSSSSSSSSSShhho",   # 11
    "odhhSoooSSSoooShho",   # 12 lashes
    "odhhSSwESSSwESShho",   # 13 eyes
    ".ohhSSEESSSEESShho",   # 14
    ".ohhSbSSSSSSbSShho",   # 15 blush
    "..ohSSSSSSmSSSSho.",   # 16 lips
    "...ohsSSSSSSSsho..",   # 17
    "....ooooooooooo...",   # 18
]
for _i, _r in enumerate(BASE):
    assert len(_r) == 18, (_i, _r, len(_r))

EXPR_ROWS = {
    "normal": {},
    "blink": {"r12": "odhhSSSSSSSSSSShho", "r13": "odhhSoooSSSoooShho", "r14": ".ohhSSSSSSSSSSShho"},
    "talk": {"r16": "..ohSSSSSSoSSSSho.", "r17": "...ohsSSSSmSSsho.."},
    "angry": {"r11": "odhhSoSSSSSSSoShho", "r12": "odhhSSooSSSooSShho", "r13": "odhhSSEwSSSEwSShho",
              "r16": "..ohSSSSSooSSSSho."},
    "shout": {"r11": "odhhSoSSSSSSSoShho", "r12": "odhhSSooSSSooSShho", "r13": "odhhSSEwSSSEwSShho",
              "r15": ".ohhSSSSSoooSSShho", "r16": "..ohSSSSSomoSSSho.", "r17": "...ohsSSSooSSsho.."},
    "shock": {"r12": "odhhSoooSSSoooShho", "r13": "odhhSowoSSSowoShho", "r14": ".ohhSoooSSSoooShho",
              "r16": "..ohSSSSSSoSSSSho."},
    "happy": {"r12": "odhhSSoSSSSSoSShho", "r13": "odhhSoSoSSSoSoShho", "r14": ".ohhSSSSSSSSSSShho",
              "r16": "..ohSSSSSmmSSSSho."},
    "sad": {"r11": "odhhSSSoSSSoSSShho", "r12": "odhhSooSSSSSooShho", "r16": "..ohSSSSSooSSSSho."},
    "cry": {"r11": "odhhSSSoSSSoSSShho", "r12": "odhhSooSSSSSooShho", "r13": "odhhSTTTSSSTTTShho",
            "r14": ".ohhSSTSSSSSTSShho", "r15": ".ohhSbTSSSSSTSShho", "r16": "..ohSSTSSooTSSSho."},
    "hurt": {"r12": "odhhSoSoSSSoSoShho", "r13": "odhhSSoSSSSSoSShho", "r14": ".ohhSoSoSSSoSoShho",
             "r16": "..ohSSSSSooSSSSho."},
    "smug": {"r12": "odhhSSSSSSSSSSShho", "r13": "odhhSoooSSSoooShho", "r14": ".ohhSSEESSSEESShho",
             "r16": "..ohSSSSSSSmSSSho."},
}


def _heads():
    out = {}
    for e, rows in EXPR_ROWS.items():
        r = list(BASE)
        for k, v in rows.items():
            i = int(k[1:])
            assert len(v) == 18, (e, k, v)
            r[i] = v
        out[e] = "\n".join(r)
    return out


HEAD_ARTS = _heads()

TORSO = """
....oooooo....
...oLKSSKKo...
..oLKKWSKKKo..
.oLKKKKWKKKko.
.oLKKKKKKKKko.
.oBBBBBBBBBbo.
oBbBbBYYBBBbBo
.oBBBBBBBBBbo.
.okKKKKKKKKko.
.okKKKKKKKkko.
.okKKKKKKKkko.
..oooooooooo..
"""

VARIANTS = [
    dict(hair=((70, 62, 84), (48, 42, 60), (32, 28, 44)), flower=((236, 60, 70), (170, 36, 50)),
         kimono=((72, 92, 160), (50, 64, 120), (112, 136, 200)), obi=((236, 196, 90), (190, 146, 60)),
         skin=(255, 222, 196)),
    dict(hair=((140, 90, 60), (108, 66, 44), (78, 48, 34)), flower=((250, 220, 90), (200, 160, 50)),
         kimono=((136, 90, 170), (100, 62, 130), (176, 132, 206)), obi=((250, 160, 190), (206, 110, 150)),
         skin=(255, 218, 190)),
    dict(hair=((62, 56, 76), (44, 40, 56), (30, 28, 42)), flower=((255, 150, 190), (220, 90, 140)),
         kimono=((214, 70, 82), (160, 44, 60), (246, 126, 128)), obi=((246, 236, 206), (200, 188, 160)),
         skin=(255, 224, 200)),
    dict(hair=((206, 204, 214), (164, 162, 178), (124, 122, 140)), flower=((140, 110, 170), (100, 76, 130)),
         kimono=((132, 112, 96), (98, 80, 68), (168, 148, 128)), obi=((70, 60, 78), (48, 40, 56)),
         skin=(246, 206, 176)),
]


def _head_pal(v):
    H, h, d = v["hair"]
    S = v["skin"]
    return {"o": INK, "H": H, "h": h, "d": d, "S": S, "s": tuple(int(c * 0.88) for c in S),
            "R": v["flower"][0], "r": v["flower"][1], "Y": (240, 200, 80),
            "E": (60, 40, 60), "w": (255, 255, 255), "m": (210, 60, 80), "b": (255, 160, 170),
            "T": (120, 200, 255)}


def _torso_pal(v):
    K, k, L = v["kimono"]
    return {"o": INK, "K": K, "k": k, "L": L, "B": v["obi"][0], "b": v["obi"][1],
            "S": v["skin"], "W": (246, 242, 236), "Y": v["flower"][0]}


def pose_gossip(pp, t, p, d):
    pose_idle(pp, t, p, d)
    f = step_frame(t, 6, 4)
    pp["arm_f"] = 150
    pp["lean"] = 1
    pp["head_dx"] = 1
    pp["expr"] = "talk" if f % 2 == 0 else "smug"


def pose_cheer_crowd(pp, t, p, d):
    f = step_frame(t, 6, 2)
    pp["arm_f"] = 165 if f else 130
    pp["arm_b"] = 150 if f else 120
    pp["dy"] = -1 if f else 0
    pp["expr"] = "happy"


def pose_fan(pp, t, p, d):
    """Fanning herself with a round uchiwa fan."""
    pose_idle(pp, t, p, d)
    f = step_frame(t, 8, 2)
    pp["arm_f"] = 140 if f else 125

    def uchiwa(img, ctx):
        h = ctx["hand_f"]
        if not h:
            return
        x, y = int(h[0]), int(h[1])
        stamp_line(img, (x, y), (x + 1, y - 3), 2, INK)
        from engine.gfx import ellipse
        ellipse(img, x - 2, y - 9, x + 4, y - 3, (246, 242, 236), INK)
        pset(img, x + 1, y - 6, (228, 59, 68))
    pp["props"] = [uchiwa]


EXTRA_POSES = {"gossip": pose_gossip, "flee": pose_run_away, "cheer_crowd": pose_cheer_crowd,
               "fan": pose_fan}
NAME_COLOR = (196, 104, 128)


def _make_def(cls, v):
    return cls(
        id="townswoman", name="路人", color=NAME_COLOR, voice=1.2,
        heads=HEAD_ARTS, head_pal=_head_pal(v),
        torso=TORSO, torso_pal=_torso_pal(v),
        neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
        arm_len=7, arm_w=2, sleeve_f=v["kimono"][0], sleeve_b=v["kimono"][1], sleeve_frac=0.75,
        hand=v["skin"],
        leg_len=7, leg_w=3, leg_gap=2, pants=v["kimono"][1], shoes=(240, 238, 232), shoe_h=1,
        weapon=None, poses=dict(EXTRA_POSES),
        desc="江户的普通町人（女）。发髻插着簪子，穿和服。variant=0~3 换装（3=老奶奶）。",
    )


class TownswomanDef(ChibiDef):
    """ChibiDef whose render/head accept variant=0..3 (cached sub-defs per variant)."""

    def _variant(self, v):
        try:
            v = int(v) % len(VARIANTS)
        except (TypeError, ValueError):
            v = 0
        if v == 0:
            return None
        cache = self.__dict__.setdefault("_vcache", {})
        d = cache.get(v)
        if d is None:
            d = _make_def(ChibiDef, VARIANTS[v])
            cache[v] = d
        return d

    def render(self, pose="idle", t=0.0, p=None, expr=None, **kw):
        sub = self._variant(kw.pop("variant", 0))
        if sub is not None:
            return sub.render(pose, t, p, expr, **kw)
        return ChibiDef.render(self, pose, t, p, expr, **kw)

    def head(self, expr, variant=0):
        sub = self._variant(variant)
        if sub is not None:
            return sub.head(expr)
        return ChibiDef.head(self, expr)


TOWNSWOMAN = register(_make_def(TownswomanDef, VARIANTS[0]))
