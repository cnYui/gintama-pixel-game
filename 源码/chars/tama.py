"""小玉 Tama — karakuri robot maid of Otose's snack bar.

Long mint-green hair with blunt bangs, mechanical ear units, blank pupil-less
robot eyes, green kimono + white frilled apron.  Her mop is her weapon
(weapon kind "staff" + a mop-head prop on the tip in every armed pose).
Extra poses: `mop` (sweeping the floor), `mop_shoot` (mop handle turned gun).
Extra exprs: `scan` (eyes glowing red while analysing).
"""
import math

from engine.core import step_frame, clamp
from engine.gfx import INK, rect, pset, stamp_line, scale_nearest
from chars import register
from chars.rig import (ChibiDef, POSES, pose_idle, pose_attack, pose_slash_up, pose_thrust, pose_ready,
                       pose_guard, pose_shoulder, _blink)

HEAD_PAL = {
    "o": INK,
    "H": (170, 240, 206),   # mint hair light
    "h": (112, 204, 164),   # hair mid
    "d": (64, 150, 118),    # hair shade
    "M": (214, 218, 230),   # metal ear unit
    "m": (140, 146, 170),   # metal shade
    "L": (255, 120, 120),   # indicator light
    "S": (255, 226, 204),   # pale skin
    "s": (230, 184, 164),
    "E": (34, 110, 86),     # blank robot eyes (no highlight)
    "e": (84, 190, 150),
    "R": (255, 60, 70),     # scan mode
    "k": (190, 90, 100),    # mouth
    "b": (255, 170, 180),
    "T": (120, 200, 255),
}

# 18 x 17 face + long hair falling behind on the left (rows 17..25). Chin row = 16.
BASE = [
    ".....oooooooo.....",   # 0
    "...oohHHHHHhhoo...",   # 1
    "..ohHHHHHHhhhhhho.",   # 2
    ".ohHHHHhhhhhhhhhho",   # 3
    "odHHHhhhhHHhhhhhho",   # 4
    "odHHhhhHHhhhhhhhho",   # 5
    "odhhhhhhhhhhhhhhho",   # 6
    "odhhhhhhhhhhhhhhho",   # 7
    "odhhhhhhhhhhhhhhho",   # 8  blunt bangs
    "odhdddddddddddddho",   # 9  blunt bang edge
    "oMmSSSSSSSSSSSSSho",   # 10
    "oMLSoooSSSSoooSSho",   # 11
    "omMSSEESSSSEESSSho",   # 12 blank eyes
    "odhSSeeSSSSeeSSSho",   # 13
    "odhSSSSSSSSSSSSho.",   # 14
    "odhosSSSSkSSSsho..",   # 15
    "odhhoooooooooo....",   # 16
    "odhho.............",   # 17 long hair behind
    "odhho.............",   # 18
    "odhho.............",   # 19
    "odhhho............",   # 20
    "odhhho............",   # 21
    "odhhho............",   # 22
    "odhhho............",   # 23
    ".oddho............",   # 24
    "..ooo.............",   # 25
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
    "blink": _head(r11="oMLSSSSSSSSSSSSSho", r12="omMSoooSSSSoooSSho", r13="odhSSSSSSSSSSSSSho"),
    "talk": _head(r14="odhSSSSSSSkSSSSho.", r15="odhosSSSSkSSSsho.."),
    "angry": _head(r10="oMmSoSSSSSSSSoSSho", r11="oMLSSooSSSSooSSSho", r12="omMSSEESSSSEESSSho",
                   r15="odhosSSSSooSSsho.."),
    "shout": _head(r10="oMmSoSSSSSSSSoSSho", r11="oMLSSooSSSSooSSSho", r12="omMSSEESSSSEESSSho",
                   r14="odhSSSSSSoooSSSho.", r15="odhosSSSSokoSsho.."),
    "shock": _head(r11="oMLSoooSSSSoooSSho", r12="omMSoeoSSSSoeoSSho", r13="odhSoooSSSSoooSSho",
                   r15="odhosSSSSSoSSsho.."),
    "happy": _head(r11="oMLSSoSSSSSSoSSSho", r12="omMSoSoSSSSoSoSSho", r13="odhSbbSSSSSSbbSSho",
                   r14="odhSSSSSSkkSSSSho.", r15="odhosSSSSSSSSsho.."),
    "sad": _head(r10="oMmSSSoSSSSoSSSSho", r11="oMLSooSSSSSSooSSho",
                 r15="odhosSSSSooSSsho.."),
    "cry": _head(r10="oMmSSSoSSSSoSSSSho", r11="oMLSooSSSSSSooSSho",
                 r13="odhSSTeSSSSTeSSSho", r14="odhSSTSSSSSTSSSho.", r15="odhosTSSSkSTSsho.."),
    "hurt": _head(r11="oMLSoSoSSSSoSoSSho", r12="omMSSoSSSSSSoSSSho", r13="odhSoSoSSSSoSoSSho",
                  r15="odhosSSSooSSSsho.."),
    "smug": _head(r11="oMLSSSSSSSSSSSSSho", r12="omMSoooSSSSoooSSho", r13="odhSSeeSSSSeeSSSho",
                  r15="odhosSSSSSkkSsho.."),
    "scan": _head(r11="oMLSoooSSSSoooSSho", r12="omMSSRRSSSSRRSSSho", r13="odhSSRRSSSSRRSSSho"),
    "sleep": _head(r11="oMmSSSSSSSSSSSSSho", r12="omMSoooSSSSoooSSho", r13="odhSSSSSSSSSSSSSho"),
}

TORSO_PAL = {
    "o": INK,
    "S": (255, 226, 204),
    "G": (74, 150, 98),     # green kimono
    "g": (48, 108, 72),     # shade
    "L": (116, 190, 128),   # highlight
    "W": (252, 252, 255),   # apron
    "w": (206, 214, 226),
    "Y": (240, 200, 90),    # obi band (yellow)
    "y": (190, 146, 60),
}

TORSO = """
....oooooo....
...oGGSSGGo...
..oLGGWWGGGo..
.oLLGWWWWGGgo.
.oLGWWWWWWGgo.
.oGGWWWWWWGgo.
.oYYYYYYYYYyo.
.oGgWWWWWWgGo.
.ogWWWWWWWWgo.
.ogWWWWWWWwgo.
.oWwWwWwWwWwo.
..oooooooooo..
"""

HAND = (255, 226, 204)


# ------------------------------------------------------------------ mop
def _mop_head(img, ctx):
    """Floppy white mop head at the weapon tip (weapon kind 'staff')."""
    tip, hand = ctx["tip"], ctx["hand_f"]
    if not tip or not hand:
        return
    vx, vy = tip[0] - hand[0], tip[1] - hand[1]
    L = math.hypot(vx, vy) or 1
    vx, vy = vx / L, vy / L
    px, py = -vy, vx
    cx, cy = tip
    strands = []
    for k in (-2, -1, 0, 1, 2):
        a = (cx + px * k * 1.1, cy + py * k * 1.1)
        # strands continue along the pole but droop with gravity
        b = (a[0] + vx * 4 + px * k * 0.6, a[1] + vy * 4 + py * k * 0.6 + 3)
        strands.append((a, b, k))
    for a, b, k in strands:
        stamp_line(img, a, b, 3, INK)
    for a, b, k in strands:
        stamp_line(img, a, b, 1, (244, 244, 236) if k % 2 == 0 else (196, 198, 190))
    # metal clamp
    stamp_line(img, (cx - px * 2, cy - py * 2), (cx + px * 2, cy + py * 2), 1, (120, 128, 150))


def _armed(fn):
    def pose(pp, t, p, d):
        fn(pp, t, p, d)
        pp["props"] = list(pp["props"]) + [_mop_head]
    return pose


def pose_mop(pp, t, p, d):
    """Diligently mopping the floor: mop swept left-right on the ground."""
    pose_idle(pp, t, p, d)
    f = step_frame(t, 6, 4)
    sweep = (0, 1, 2, 1)[f]
    pp["arm_f"] = 55 + sweep * 8
    pp["arm_b"] = 40 + sweep * 6
    pp["weapon"] = -60 + sweep * 6
    pp["lean"] = 1
    pp["expr"] = "blink" if _blink(t, 3.7) else "normal"
    pp["props"] = [_mop_head]


def pose_mop_shoot(pp, t, p, d):
    """Mop handle opens into a machine gun: aimed forward with muzzle flashes."""
    f = step_frame(t, 12, 2)
    pp["arm_f"] = 88
    pp["arm_b"] = 75
    pp["weapon"] = 180            # mop head backwards, handle-muzzle forward
    pp["legs"] = "spread"
    pp["lean"] = -1 if f else 0
    pp["expr"] = "scan"

    def flash(img, ctx, f=f):
        h = ctx["hand_f"]
        if not h:
            return
        x, y = int(h[0]) + 5, int(h[1])
        stamp_line(img, (h[0], h[1]), (x, y), 3, INK)
        stamp_line(img, (h[0], h[1]), (x, y), 1, (120, 130, 150))
        if f:
            rect(img, x + 1, y - 2, 4, 5, INK)
            rect(img, x + 1, y - 1, 5, 3, (255, 230, 90))
            rect(img, x + 2, y - 1, 3, 3, (255, 255, 220))
            pset(img, x + 6, y - 3, (255, 230, 90))
            pset(img, x + 6, y + 3, (255, 230, 90))
    pp["props"] = [_mop_head, flash]


class TamaDef(ChibiDef):
    def portrait_fn(self, expr, t, talking):
        e = expr or "normal"
        if talking and step_frame(t, 8) % 2 == 0:
            e = "talk" if expr in (None, "normal") else e
        elif expr is None and (t % 3.1) < 0.12:
            e = "blink"
        h = self.head(e).crop((0, 0, 18, 18))
        return scale_nearest(h, 2)


TAMA = register(TamaDef(
    id="tama", name="小玉", color=(52, 160, 118), voice=1.18,
    heads=HEADS, head_pal=HEAD_PAL, head_anchor=(9, 16),
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=(74, 150, 98), sleeve_b=(48, 108, 72), sleeve_frac=0.7,
    hand=HAND,
    leg_len=7, leg_w=3, leg_gap=3, pants=(60, 128, 84), shoes=(240, 240, 246), shoe_h=1,
    weapon="staff", weapon_len=15, sheathed=None,
    poses={"attack": _armed(pose_attack), "slash_up": _armed(pose_slash_up),
           "thrust": _armed(pose_thrust), "ready": _armed(pose_ready),
           "guard": _armed(pose_guard), "shoulder": _armed(pose_shoulder),
           "mop": pose_mop, "mop_shoot": pose_mop_shoot},
    desc="机械女仆小玉。绿色长发、无机质的眼睛，登势酒馆的店员，拖把就是武器。",
))
