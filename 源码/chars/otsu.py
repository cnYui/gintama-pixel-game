"""寺门通 Terakado Tsuu — idol singer (twin tails, pink/black idol outfit, microphone).

Extra pose: `sing` (mic at the mouth, free arm waving, floating music notes).
Extra exprs: `sing` (eyes shut, mouth wide open), `wink`.
The mic is also held in idle / talk / wave / cheer so she always reads as "the idol".
"""
import math

from engine.core import step_frame
from engine.gfx import INK, rect, pset, stamp_line, scale_nearest
from chars import register
from chars.rig import ChibiDef, pose_idle, pose_talk, pose_wave, pose_cheer, _blink

# ------------------------------------------------------------------ palette
HEAD_PAL = {
    "o": INK,
    "H": (118, 96, 136),    # dark plum-brown hair highlight
    "h": (74, 58, 92),      # hair mid
    "d": (48, 38, 66),      # hair shade
    "R": (255, 120, 180),   # pink hair tie
    "r": (206, 70, 138),    # tie shade
    "S": (255, 220, 192),   # skin
    "s": (238, 176, 148),   # skin shade
    "E": (96, 36, 72),      # plum eyes
    "e": (186, 84, 132),    # iris light
    "w": (255, 255, 255),
    "m": (200, 70, 100),    # mouth
    "b": (255, 150, 170),   # blush
    "T": (120, 200, 255),   # tears
}

# 18x17 base face (same grid as gintoki) -> embedded at x=4 of a 26x22 sprite with twin tails
BASE = [
    ".....oooooooo.....",   # 0
    "...oohHHHHhhhoo...",   # 1
    "..ohHHHHhhhhhhhho.",   # 2
    ".ohHHHhhhhhhhhhhho",   # 3
    "odhHHhhhhHHhhhhhho",   # 4  shine band
    "odhhhhHHhhhhhhhhho",   # 5
    "odhhhhhhhhhhhhhhho",   # 6
    "odhhhhhhhhhhhhhhho",   # 7
    "odhhShhhShhhhShhho",   # 8  bang tips
    "odhSSSSSSSSSSSSSho",   # 9
    "odhSoooSSSSoooSSho",   # 10 lashes
    "odhSSwESSSSwESSSho",   # 11 eyes
    ".ohSSEeSSSSEeSSSho",   # 12
    ".ohSbbSSSSSSbbSSho",   # 13 blush
    "..ohsSSSSSmSSsho..",   # 14 mouth
    "...oosSSSSSSsoo...",   # 15
    ".....oooooooo.....",   # 16
]

# twin tails + hair ties overlay (26 wide, 22 rows); '.' keeps what is under it
TAILS = [
    "..........................",  # 0
    "..........................",  # 1
    "..........................",  # 2
    ".ooo..................ooo.",  # 3
    "oRRR..................RRRo",  # 4
    "orRr..................rRro",  # 5
    ".ooo..................ooo.",  # 6
    ".ohd..................dho.",  # 7
    "oHhd..................dhho",  # 8
    "oHhd..................dhho",  # 9
    "ohhd..................dhho",  # 10
    "ohhd..................dhho",  # 11
    "ohhd..................dhdo",  # 12
    "ohhdo................odhho",  # 13
    "ohhdo................odhho",  # 14
    "ohho..................ohho",  # 15
    "ohho..................ohdo",  # 16
    "ohdo..................ohho",  # 17
    "ohho..................odho",  # 18
    "ohdo..................ohho",  # 19
    ".oho..................oho.",  # 20
    "..o....................o..",  # 21
]


def _head(**rows):
    r = list(BASE)
    for k, v in rows.items():
        i = int(k[1:])
        assert len(v) == len(BASE[i]), (k, v, len(v))
        r[i] = v
    grid = [["."] * 26 for _ in range(22)]
    for y, row in enumerate(r):
        for x, ch in enumerate(row):
            if ch != ".":
                grid[y][x + 4] = ch
    for y, row in enumerate(TAILS):
        assert len(row) == 26, (y, row)
        for x, ch in enumerate(row):
            if ch != ".":
                grid[y][x] = ch
    return "\n".join("".join(g) for g in grid)


for _i, _r in enumerate(BASE):
    assert len(_r) == 18, (_i, _r)

HEADS = {
    "normal": _head(),
    "blink": _head(r10="odhSSSSSSSSSSSSSho", r11="odhSoooSSSSoooSSho", r12=".ohSSSSSSSSSSSSSho"),
    "talk": _head(r14="..ohsSSSSSoSSsho..", r15="...oosSSSSmSsoo..."),
    "angry": _head(r9="odhSoSSSSSSSSoSSho", r10="odhSSooSSSSooSSSho",
                   r11="odhSSEwSSSSEwSSSho", r13=".ohSSSSSSSSSSSSSho",
                   r14="..ohsSSSSooSSsho.."),
    "shout": _head(r9="odhSoSSSSSSSSoSSho", r10="odhSSooSSSSooSSSho",
                   r11="odhSSEwSSSSEwSSSho", r13=".ohSSSSSSoooSSSSho",
                   r14="..ohsSSSSomoSsho..", r15="...oosSSSooSsoo..."),
    "shock": _head(r11="odhSowoSSSSowoSSho", r12=".ohSoooSSSSoooSSho",
                   r13=".ohSSSSSSSSSSSSSho", r14="..ohsSSSSSoSSsho.."),
    "happy": _head(r10="odhSSoSSSSSSoSSSho", r11="odhSoSoSSSSoSoSSho",
                   r12=".ohSSSSSSSSSSSSSho", r14="..ohsSSSSmmSSsho.."),
    "sad": _head(r9="odhSSSoSSSSoSSSSho", r10="odhSooSSSSSSooSSho",
                 r13=".ohSSSSSSSSSSSSSho", r14="..ohsSSSSooSSsho.."),
    "cry": _head(r9="odhSSSoSSSSoSSSSho", r10="odhSooSSSSSSooSSho",
                 r11="odhSTTTSSSSTTTSSho", r12=".ohSSTSSSSSSTSSSho",
                 r13=".ohSSTSSSSSSTSSSho", r14="..ohsTSSSooSTsho.."),
    "hurt": _head(r10="odhSoSSSSSSSSoSSho", r11="odhSSoSSSSSSoSSSho",
                  r12=".ohSoSSSSSSSSoSSho", r13=".ohSSSSSSSSSSSSSho",
                  r14="..ohsSSSSooSSsho.."),
    "smug": _head(r10="odhSSSSSSSSSSSSSho", r11="odhSoooSSSSoooSSho",
                  r12=".ohSSEESSSSEESSSho", r14="..ohsSSSSSSmSsho..",
                  r15="...oosSSSSmmsoo..."),
    "wink": _head(r10="odhSoooSSSSSoSSSho", r11="odhSSwESSSSoSoSSho",
                  r12=".ohSSEeSSSSSSSSSho", r14="..ohsSSSSmmSSsho.."),
    "sing": _head(r10="odhSSoSSSSSSoSSSho", r11="odhSoSoSSSSoSoSSho",
                  r12=".ohSSSSSSSSSSSSSho", r13=".ohSbbSSSoooSbbSho",
                  r14="..ohsSSSSomoSsho..", r15="...oosSSSSoSsoo..."),
    "sing2": _head(r10="odhSSSSSSSSSSSSSho", r11="odhSoooSSSSoooSSho",
                   r12=".ohSSSSSSSSSSSSSho", r14="..ohsSSSSomoSsho..",
                   r15="...oosSSSSoSsoo..."),
}

TORSO_PAL = {
    "o": INK,
    "S": (255, 220, 192),   # skin (neckline)
    "s": (238, 176, 148),
    "P": (255, 122, 176),   # hot pink
    "p": (214, 78, 142),    # pink shade
    "L": (255, 190, 220),   # pink light
    "K": (46, 40, 60),      # black
    "k": (92, 84, 112),     # black highlight
    "Y": (255, 222, 90),    # gold star
    "W": (255, 250, 255),   # white frill
    "w": (220, 206, 230),
}

TORSO = """
....oooooo....
...osSSSSso...
..oLPoKKoPPo..
.oLPPKYYKPPpo.
.oPPPPKKPPPpo.
.oPPPPPPPPPpo.
.oKKKPPKKKKKo.
.okKKKKKKKKKo.
okKKKkKKKKkKKo
oWPWPWPWPWPWPo
owPwPwPwPwPwwo
.oooooooooooo.
"""


# ------------------------------------------------------------------ props
MIC_GREY = (200, 204, 216)


def _mic(img, ctx):
    """Handheld idol microphone (pink handle, silver head) in the front hand."""
    h = ctx["hand_f"]
    if not h:
        return
    x, y = int(round(h[0])), int(round(h[1]))
    arm = ctx["params"]["arm_f"]
    # mic head sits above the hand; when the arm is raised it tilts toward the mouth
    dx = -2 if arm > 110 else 0
    hx, hy = x + dx, y - 4
    stamp_line(img, (x, y + 1), (hx, hy), 3, INK)
    stamp_line(img, (x, y + 1), (hx, hy), 1, (255, 122, 176))
    rect(img, hx - 2, hy - 3, 4, 4, INK)
    rect(img, hx - 1, hy - 2, 2, 2, MIC_GREY)
    pset(img, hx - 1, hy - 2, (255, 255, 255))
    # knuckles back on top of the handle
    rect(img, x - 1, y - 1, 2, 2, (255, 220, 192))


NOTE = [
    "..oo.",
    "..oYo",
    "..o.o",
    "ooo..",
    "oYo..",
    "ooo..",
]
NOTE_COLS = [(255, 222, 90), (255, 140, 200), (140, 220, 255)]


def _notes(img, ctx):
    """Music notes floating up from the singer (12 fps stepping)."""
    hx, hy, hw, hh = ctx["head"]
    t = ctx["t"]
    tq = step_frame(t, 12) / 12.0
    for i in range(3):
        ph = (tq * 0.9 + i / 3.0) % 1.0
        x = int(hx + hw - 2 + i * 3 + round(math.sin((ph + i) * 6.0) * 2))
        y = int(hy + 8 - ph * 16)
        col = NOTE_COLS[i % 3]
        for yy, row in enumerate(NOTE):
            for xx, ch in enumerate(row):
                if ch == "o":
                    pset(img, x + xx, y + yy, INK)
                elif ch == "Y":
                    pset(img, x + xx, y + yy, col)


# ------------------------------------------------------------------ poses
def pose_idle_mic(pp, t, p, d):
    pose_idle(pp, t, p, d)
    pp["arm_f"] = 30 + (2 if pp["bob"] else 0)
    pp["props"] = [_mic]


def pose_talk_mic(pp, t, p, d):
    pose_talk(pp, t, p, d)
    pp["arm_f"] = 35 + 6 * math.sin(t * 5)
    pp["arm_b"] = -20
    pp["props"] = [_mic]


def pose_wave_mic(pp, t, p, d):
    pose_wave(pp, t, p, d)
    # wave with the back hand, mic in the front hand
    f = step_frame(t, 6, 2)
    pp["arm_f"] = 30
    pp["arm_b"] = 165 if f else 140
    pp["expr"] = "wink" if step_frame(t, 2, 4) == 3 else "happy"
    pp["props"] = [_mic]


def pose_cheer_mic(pp, t, p, d):
    pose_cheer(pp, t, p, d)
    pp["props"] = [_mic]


def pose_sing(pp, t, p, d):
    """On stage: mic at the mouth, free arm swinging to the beat, little hops, notes."""
    beat = step_frame(t, 4, 4)            # 4 beats per second-ish
    pp["arm_f"] = 138
    pp["arm_b"] = (110, 150, 170, 140)[beat]
    pp["bob"] = -1 if beat % 2 else 0
    pp["dy"] = -1 if beat == 2 else 0
    pp["lean"] = 1 if beat in (1, 2) else 0
    pp["legs"] = "spread" if beat in (0, 3) else "stand"
    pp["expr"] = "sing" if step_frame(t, 6) % 2 == 0 else "sing2"
    if _blink(t, 4.3):
        pp["expr"] = "wink"
    pp["props"] = [_mic, _notes]


class OtsuDef(ChibiDef):
    def portrait_fn(self, expr, t, talking):
        e = expr or "normal"
        if talking and step_frame(t, 8) % 2 == 0:
            e = "talk" if expr in (None, "normal") else e
        elif expr is None and (t % 3.1) < 0.12:
            e = "blink"
        h = self.head(e).crop((0, 0, 26, 19))
        return scale_nearest(h, 2)


OTSU = register(OtsuDef(
    id="otsu", name="阿通", color=(232, 74, 150), voice=1.32,
    heads=HEADS, head_pal=HEAD_PAL, head_anchor=(13, 16),
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=(255, 122, 176), sleeve_b=(214, 78, 142), sleeve_frac=0.35,
    hand=(255, 220, 192),
    leg_len=7, leg_w=3, leg_gap=4, pants=(250, 246, 252), shoes=(226, 70, 140), shoe_h=2,
    weapon=None,
    poses={"sing": pose_sing, "idle": pose_idle_mic, "talk": pose_talk_mic,
           "wave": pose_wave_mic, "cheer": pose_cheer_mic},
    desc="当红偶像歌手寺门通。双马尾+麦克风，新八是她亲卫队的队长。",
))
