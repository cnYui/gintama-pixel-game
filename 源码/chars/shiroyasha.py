"""白夜叉 Shiroyasha — Gintoki during the Joui war: silver perm, white headband
(hachimaki with a steel plate) whose tails flutter behind, white haori over light
armour, steel gauntlets, a REAL katana, grim determined face (default expression).

idle / walk / run carry the drawn katana (blade low / trailing behind);
`stand` is the plain idle with the sword sheathed. Extra: `stand`, `battle_idle`.
"""
import math

from engine.core import step_frame, clamp, lerp
from engine.gfx import INK, stamp_line, rect, pset, shade
from chars import register
from chars.rig import POSES, pose_idle, pose_walk, pose_run, _blink
from chars.katsura import LayeredChibi, make_head_builder, make_sheath

HEAD_PAL = {
    "o": INK,
    "H": (238, 240, 250),   # silver hair
    "h": (196, 202, 224),
    "d": (146, 152, 188),
    "S": (255, 214, 182),
    "s": (230, 166, 136),
    "E": (170, 30, 50),     # crimson eyes (sharper than present-day)
    "w": (255, 255, 255),
    "m": (160, 64, 74),
    "B": (250, 250, 255),   # headband
    "b": (200, 206, 224),
    "M": (150, 162, 188),   # steel plate
    "k": (214, 222, 238),   # plate shine
    "T": (120, 200, 255),
    "n": (206, 150, 128),   # grime / shadow on cheek
}

BASE = [
    "....o.oo.ooo.oo...",   # 0  wilder spikes
    "...oHooHoHHHoHHo..",   # 1
    "...oHHHHHHHHHHHHo.",   # 2
    "..oHHHHhHHHHHHHHHo",   # 3
    ".odHHHHHHHHHHhHHHo",   # 4
    "oooooooooooooooooo",   # 5  headband top
    "obBBBBBBoMkMoBBBbo",   # 6  hachimaki + steel plate
    "oooooooooooooooooo",   # 7
    "odHHHSHHSSHHSSHHho",   # 8  bangs under the band
    "odHHSSSHSSSSSHSSHo",   # 9
    "odHSoSSSSSSSSSoSHo",   # 10 hard brows
    "odHSSoooSSSoooSSHo",   # 11
    ".oHSSEEwSSSEEwSSo.",   # 12 narrowed crimson eyes
    ".ohSSnSSSSSSSSSso.",   # 13
    "..osSSSSSoooSSSo..",   # 14 set mouth
    "...oosSSSSSSSsoo..",   # 15
    ".....ooooooooo....",   # 16
]
_head = make_head_builder(BASE)

HEADS = {
    "normal": _head(),
    "determined": _head(),
    "blink": _head(r10="odHSSSSSSSSSSSSSHo", r11="odHSSSSSSSSSSSSSHo", r12=".oHSSoooSSSoooSSo."),
    "talk": _head(r14="..osSSSSSSooSSSo..", r15="...oosSSSSmmSsoo.."),
    "angry": _head(r12=".oHSSEEwSSSEEwSSo.", r13=".ohSSEESSSSEESSso.",
                   r14="..osSSSSSoooSSSo.."),
    "shout": _head(r13=".ohSSEESSSoooSSso.", r14="..osSSSSSomoSSSo..",
                   r15="...oosSSSSooSsoo.."),
    "shock": _head(r10="odHSSSSSSSSSSSSSHo", r11="odHSoooSSSoooSSSHo",
                   r12=".oHSowwoSowwoSSSo.", r13=".ohSoooSSoooSSSso.",
                   r14="..osSSSSSSooSSSo..", r15="...oosSSSSmmSsoo.."),
    "happy": _head(r10="odHSSSSSSSSSSSSSHo", r11="odHSSSoSSSSSoSSSHo",
                   r12=".oHSSoSoSSSoSoSSo.", r14="..osSSSSSmSSmSSo..",
                   r15="...oosSSSSmmSsoo.."),
    "sad": _head(r10="odHSSSoSSSSoSSSSHo", r11="odHSSooSSSSSooSSHo",
                 r12=".oHSSwEESSSwEESSo.", r14="..osSSSSSSSSSSSo..",
                 r15="...oosSSSSmmSsoo.."),
    "cry": _head(r10="odHSSSoSSSSoSSSSHo", r11="odHSSooSSSSSooSSHo",
                 r12=".oHSSwEESSSwEESSo.", r13=".ohSSTSSSSSTSSSso.",
                 r14="..osSTSSSSSTmSSo..", r15="...oosTSSSmTSsoo.."),
    "hurt": _head(r10="odHSSSSSSSSSSSSSHo", r11="odHSSoSoSSSoSoSSHo",
                  r12=".oHSSSoSSSSSoSSSo.", r13=".ohSSoSoSSSoSoSso.",
                  r14="..osSSSSSSooSSSo..", r15="...oosSSSSmmSsoo.."),
    "smug": _head(r12=".oHSSEEwSSSEEwSSo.", r14="..osSSSSSSSSSmSo..",
                  r15="...oosSSSSmmmsoo.."),
    "sleep": _head(r10="odHSSSSSSSSSSSSSHo", r11="odHSSSSSSSSSSSSSHo",
                   r12=".oHSSoooSSSoooSSo."),
}

TORSO_PAL = {
    "o": INK,
    "W": (244, 246, 252),   # white haori
    "w": (190, 200, 224),
    "K": (44, 40, 58),      # dark under-kimono
    "k": (80, 76, 98),
    "A": (152, 162, 188),   # armour plate
    "a": (212, 220, 236),   # plate highlight
    "n": (96, 104, 134),    # plate edge
    "r": (176, 50, 62),     # red lacing
    "B": (58, 60, 92),      # belt
}

TORSO = """
....oooooo....
...oKKKKKKo...
..oWWnaaAnWo..
.oWWWnaAAAnwo.
.oWWWnrrrrnwo.
.oWWWnAAAAnwo.
.oWWWBBBBBBwo.
.owWWKKKKKWwo.
.owWWKKkKKWwo.
.owWWKKKKKwwo.
.owwWKKKKKwwo.
..oooooooooo..
"""

SHEATH = make_sheath(saya=(40, 36, 52), saya_hi=(88, 84, 110))


# ------------------------------------------------------------------ behind layers
def _band_tails(img, ctx):
    """Two thin hachimaki tails fluttering behind the head."""
    hx, hy, hw, hh = ctx["head"]
    pp = ctx["params"]
    f = step_frame(ctx["t"], 8)
    fast = pp["legs"] == "run" or pp.get("pose") in ("run", "run_away", "jump", "fly")
    x0, y0 = hx + 2, hy + 6
    wv = (0, 1, 0, -1)[f % 4]
    wv2 = (1, 0, -1, 0)[f % 4]
    # two straight 2 px ribbons fanning out from the knot (the old kinked
    # 1 px tails read as the glyph "7")
    if fast:
        ends = ((x0 - 12, y0 + wv), (x0 - 10, y0 + 4 + wv2))
    else:
        ends = ((x0 - 9, y0 + 3 + wv), (x0 - 6, y0 + 8 + wv2))
    for e in ends:
        stamp_line(img, (x0, y0), e, 4, INK)
    for i, e in enumerate(ends):
        col = (250, 250, 255) if i == 0 else (206, 212, 230)
        stamp_line(img, (x0, y0), e, 2, col)
    rect(img, int(x0) - 1, int(y0) - 1, 3, 3, INK)     # knot
    pset(img, x0, y0, (230, 232, 244))


def _empty_saya(img, ctx):
    """Scabbard stays at the hip while the blade is drawn."""
    pp = ctx["params"]
    if pp["weapon"] is None:
        return
    tx, ty, tw, th = ctx["torso"]
    a, b = (tx + 11, ty + 6), (tx - 6, ty + 10)
    stamp_line(img, a, b, 4, INK)
    stamp_line(img, (tx + 10, ty + 6.2), b, 2, (40, 36, 52))
    stamp_line(img, (tx + 11, ty + 5), (tx + 11, ty + 7), 1, (230, 180, 60))


def _behind(img, ctx):
    _empty_saya(img, ctx)
    _band_tails(img, ctx)


# ------------------------------------------------------------------ poses
def pose_battle_idle(pp, t, p, d):
    """Standing on the battlefield, drawn katana held low, tip near the ground."""
    pose_idle(pp, t, p, d)
    pp["arm_f"] = 30 + (2 if step_frame(t, 4, 4) in (1, 2) else 0)
    pp["weapon"] = -28
    pp["arm_b"] = -12
    pp["expr"] = "blink" if (t % 3.7) < 0.12 else "normal"


def pose_walk_s(pp, t, p, d):
    pose_walk(pp, t, p, d)
    pp["arm_f"] = 22 + math.sin(t * 6) * 4
    pp["weapon"] = -18
    pp["expr"] = "blink" if (t % 3.7) < 0.12 else "normal"


def pose_run_s(pp, t, p, d):
    """Charging with the blade trailing behind."""
    pose_run(pp, t, p, d)
    pp["arm_f"] = -35
    pp["weapon"] = 196
    pp["lean"] = 3
    pp["expr"] = "determined"


def pose_stand(pp, t, p, d):
    pose_idle(pp, t, p, d)
    pp["expr"] = "blink" if (t % 3.7) < 0.12 else "normal"


SHIROYASHA = register(LayeredChibi(
    id="shiroyasha", name="白夜叉", color=(112, 118, 150), voice=0.84,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=(244, 246, 252), sleeve_b=(190, 200, 224), sleeve_frac=0.55,
    hand=(122, 128, 152),      # steel gauntlets
    leg_len=7, leg_w=3, leg_gap=4, pants=(44, 40, 58), shoes=(26, 22, 32), shoe_h=3,
    weapon="katana", weapon_len=17, sheathed=SHEATH,
    poses={"idle": pose_battle_idle, "battle_idle": pose_battle_idle, "stand": pose_stand,
           "walk": pose_walk_s, "run": pose_run_s},
    behind=_behind,
    desc="攘夷战争时期的银时。白发、白羽织、护额与轻甲，手持真刀，令天人闻风丧胆的传说『白夜叉』。",
))
