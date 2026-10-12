"""路人(男) townsman — Edo commoner for crowds.

kw variant=0..3 (default 0) swaps look + palette:
  0  topknot (chonmage), black hair, brown kimono, navy obi
  1  short messy brown hair, blue kimono
  2  old man: grey topknot, moustache, dark green kimono
  3  worker: short hair + white hachimaki headband, orange happi coat
Every standard pose works for every variant.  Extra pose: `gossip` (hand at mouth,
leaning to whisper), `flee` (= run_away), `cheer_crowd` (fist pumping).
"""
from engine.core import step_frame
from engine.gfx import INK, scale_nearest
from chars import register
from chars.rig import ChibiDef, pose_idle, pose_run_away, _blink

# ------------------------------------------------------------------ heads
# 'H/h/d' hair, 'B/P' shaved pate, 'X' headband (hair colour when absent), 'M' moustache
TOPKNOT = [
    ".......oooooo.....",   # 0  chonmage topknot lying forward
    "......odhHHHHo....",   # 1
    "....oooodhooooo...",   # 2
    "...oBBBBPBBBBBBo..",   # 3  shaved pate (sakayaki)
    "..oHBBBBBBBBBBBHo.",   # 4
    ".odHHBBBBBBBBBHHo.",   # 5
    "odHHHBBBBBBBBBHHHo",   # 6
    "odHHhSSSSSSSSSSHho",   # 7
    "odhSSSSSSSSSSSSShd",   # 8
    "odhSSSSSSSSSSSSSho",   # 9
    "odhSSooSSSSSooSSho",   # 10 brows
    "odhSSSSSSSSSSSSSho",   # 11
    ".ohSSoESSSSoESSSo.",   # 12 eyes
    ".osSSSSSSSSSSSSso.",   # 13
    "..osSSSSSSmmSSSo..",   # 14 mouth
    "...oosSSSSSSSsoo..",   # 15
    ".....ooooooooo....",   # 16
]
SHORT = [
    ".....oo.oooo......",   # 0
    "....oHHoHHHHoo....",   # 1
    "...oHHHHHHHHHHo...",   # 2
    "..oHHHhHHHHHHHHo..",   # 3
    ".odHHHHHHHHhHHHHo.",   # 4
    "odHHhHHHHHHHHHHHHo",   # 5
    "oXXXXXXXXXXXXXXXXo",   # 6  headband row
    "odhHHHHhHHHHHHHHho",   # 7
    "odhHSHHSSHHSSHHSho",   # 8
    "odhSSSSSSSSSSSSSho",   # 9
    "odhSSooSSSSSooSSho",   # 10 brows
    "odhSSSSSSSSSSSSSho",   # 11
    ".ohSSoESSSSoESSSo.",   # 12 eyes
    ".osSSSSSSSSSSSSso.",   # 13
    "..osSSSSSSmmSSSo..",   # 14 mouth
    "...oosSSSSSSSsoo..",   # 15
    ".....ooooooooo....",   # 16
]
for _b in (TOPKNOT, SHORT):
    for _i, _r in enumerate(_b):
        assert len(_r) == 18, (_i, _r, len(_r))

# expression overrides (rows 10..15 are identical in both bases)
EXPR_ROWS = {
    "normal": {},
    "blink": {"r12": ".ohSSooSSSSooSSSo."},
    "talk": {"r14": "..osSSSSSSooSSSo..", "r15": "...oosSSSSmmSsoo.."},
    "angry": {"r10": "odhSoSSSSSSSSoSSho", "r11": "odhSSoSSSSSSoSSSho", "r12": ".ohSSEoSSSSEoSSSo.",
              "r14": "..osSSSSSoooSSSo.."},
    "shout": {"r10": "odhSoSSSSSSSSoSSho", "r11": "odhSSoSSSSSSoSSSho", "r12": ".ohSSEoSSSSEoSSSo.",
              "r13": ".osSSSSSSoooSSSso.", "r14": "..osSSSSSomoSSSo..", "r15": "...oosSSSSooSsoo.."},
    "shock": {"r10": "odhSSSSSSSSSSSSSho", "r11": "odhSoooSSSSoooSSho", "r12": ".ohSowoSSSSowoSSo.",
              "r13": ".osSoooSSSSoooSso.", "r14": "..osSSSSSSooSSSo..", "r15": "...oosSSSSooSsoo.."},
    "happy": {"r12": ".ohSSoSoSSoSoSSSo.", "r13": ".osSbSSSSSSSbSSso.", "r14": "..osSSSSSomoSSSo.."},
    "sad": {"r10": "odhSSSoSSSSoSSSSho", "r11": "odhSooSSSSSSooSSho", "r14": "..osSSSSSoooSSSo..",
            "r15": "...oosSSSoSSosoo.."},
    "cry": {"r10": "odhSSSoSSSSoSSSSho", "r11": "odhSooSSSSSSooSSho", "r12": ".ohSSTTSSSSTTSSSo.",
            "r13": ".osSSTSSSSSTSSSso.", "r14": "..osSTSSSooTSSSo.."},
    "hurt": {"r11": "odhSoSoSSSSoSoSSho", "r12": ".ohSSoSSSSSSoSSSo.", "r13": ".osSoSoSSSSoSoSso.",
             "r14": "..osSSSSSSooSSSo.."},
    "smug": {"r11": "odhSSSSSSSSSSSSSho", "r12": ".ohSSooSSSSooSSSo.", "r14": "..osSSSSSSSmSSSo..",
             "r15": "...oosSSSSmmsoo..."},
}

MOUSTACHE = {"r13": ".osSSSSSSMMMMSSso."}


def _heads(base, moustache=False):
    out = {}
    for e, rows in EXPR_ROWS.items():
        r = list(base)
        rr = dict(rows)
        if moustache and "r13" not in rr:
            rr.update(MOUSTACHE)
        for k, v in rr.items():
            i = int(k[1:])
            assert len(v) == 18, (e, k, v)
            r[i] = v
        out[e] = "\n".join(r)
    return out


def _head_pal(hair, skin=(255, 214, 180), band=None, pate=None):
    H, h, d = hair
    S, s = skin, tuple(int(c * 0.88) for c in skin)
    pate = pate or (max(0, skin[0] - 14), max(0, skin[1] - 6), min(255, skin[2] + 16))
    return {
        "o": INK, "H": H, "h": h, "d": d,
        "S": S, "s": s, "B": pate, "P": tuple(int(c * 0.9) for c in pate),
        "b": (250, 150, 150), "E": (40, 34, 48), "m": (170, 70, 80),
        "T": (120, 200, 255), "M": d,
        "X": band or h, "w": (255, 255, 255),
    }


def _torso_pal(kimono, obi, skin=(255, 214, 180)):
    K, k, L = kimono
    return {"o": INK, "K": K, "k": k, "L": L, "B": obi[0], "b": obi[1], "S": skin,
            "W": (240, 236, 226)}


TORSO = """
....oooooo....
...oLKSSKKo...
..oLKKSSKKKo..
.oLKKKKSKKKko.
.oLKKKKKKKKko.
.oKKKKKKKKKko.
.oBBBBBBBBBbo.
.okKKKKKKKKko.
.okKKKKKKKkko.
.okKKKKKKKkko.
.okkKkKkKkkko.
..oooooooooo..
"""

# worker's happi coat: white kanji-ish emblem on the chest
TORSO_HAPPI = """
....oooooo....
...oLKSSKKo...
..oLKKSSKKKo..
.oLKKWWWKKKko.
.oLKKWKWKKKko.
.oKKKWWWKKKko.
.oBBBBBBBBBbo.
.okKKKKKKKKko.
.okKKKKKKKkko.
.okKKKKKKKkko.
.oWkWkWkWkWko.
..oooooooooo..
"""

VARIANTS = [
    dict(head=TOPKNOT, moustache=False, torso=TORSO,
         hair=((64, 58, 74), (44, 40, 54), (30, 28, 40)),
         kimono=((142, 100, 70), (104, 70, 50), (176, 132, 96)), obi=((52, 58, 96), (36, 40, 70)),
         pants=(104, 70, 50), color=(150, 110, 80)),
    dict(head=SHORT, moustache=False, torso=TORSO,
         hair=((150, 96, 58), (116, 70, 44), (84, 50, 34)),
         kimono=((70, 110, 170), (48, 78, 130), (110, 150, 206)), obi=((220, 200, 150), (180, 156, 110)),
         pants=(48, 70, 110), color=(80, 120, 180)),
    dict(head=TOPKNOT, moustache=True, torso=TORSO,
         hair=((214, 214, 222), (170, 170, 182), (128, 128, 142)), skin=(246, 204, 172),
         kimono=((72, 104, 78), (50, 76, 56), (104, 140, 108)), obi=((120, 84, 54), (90, 60, 40)),
         pants=(50, 76, 56), color=(90, 130, 96)),
    dict(head=SHORT, moustache=False, torso=TORSO_HAPPI, band=(244, 244, 248),
         hair=((58, 52, 66), (40, 36, 50), (28, 26, 38)), skin=(240, 190, 150),
         kimono=((236, 132, 60), (196, 96, 40), (252, 176, 110)), obi=((60, 52, 70), (40, 34, 50)),
         pants=(56, 50, 66), color=(220, 120, 50)),
]


def pose_gossip(pp, t, p, d):
    pose_idle(pp, t, p, d)
    f = step_frame(t, 6, 4)
    pp["arm_f"] = 150
    pp["lean"] = 1
    pp["head_dx"] = 1
    pp["expr"] = "talk" if f % 2 == 0 else "smug"


def pose_cheer_crowd(pp, t, p, d):
    f = step_frame(t, 6, 2)
    pp["arm_f"] = 170 if f else 120
    pp["arm_b"] = -10
    pp["dy"] = -1 if f else 0
    pp["expr"] = "shout" if f else "happy"


EXTRA_POSES = {"gossip": pose_gossip, "flee": pose_run_away, "cheer_crowd": pose_cheer_crowd}


def _make_def(cls, cid, name, desc, voice, vdefs, i):
    v = vdefs[i]
    skin = v.get("skin", (255, 214, 180))
    return cls(
        id=cid, name=name, color=VARIANTS_COLOR.get(cid, v["color"]), voice=voice,
        heads=_heads(v["head"], v.get("moustache", False)),
        head_pal=_head_pal(v["hair"], skin, v.get("band")),
        torso=v["torso"], torso_pal=_torso_pal(v["kimono"], v["obi"], skin),
        neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
        arm_len=7, arm_w=2, sleeve_f=v["kimono"][0], sleeve_b=v["kimono"][1], sleeve_frac=0.7,
        hand=skin,
        leg_len=7, leg_w=3, leg_gap=4, pants=v["pants"], shoes=(96, 70, 50), shoe_h=1,
        weapon=None, poses=dict(EXTRA_POSES), desc=desc,
    )


VARIANTS_COLOR = {"townsman": (132, 112, 92)}


class TownsmanDef(ChibiDef):
    """ChibiDef whose render/head accept variant=0..3 (cached sub-defs per variant)."""
    _vdefs = VARIANTS
    _voice = 0.9

    def _variant(self, v):
        try:
            v = int(v) % len(self._vdefs)
        except (TypeError, ValueError):
            v = 0
        if v == 0:
            return None
        cache = self.__dict__.setdefault("_vcache", {})
        d = cache.get(v)
        if d is None:
            d = _make_def(ChibiDef, self.id, self.name, self.desc, self.voice, self._vdefs, v)
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


TOWNSMAN = register(_make_def(TownsmanDef, "townsman", "路人", "江户的普通町人（男）。variant=0~3：发髻/短发/老爷爷/头巾工匠。",
                              0.9, VARIANTS, 0))
