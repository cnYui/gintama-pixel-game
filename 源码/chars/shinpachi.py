"""志村新八 Shimura Shinpachi — the straight man. The glasses ARE the character.

Extras: waiter (carrying a tray), waiter_walk, otaku_cheer (happi coat + light sticks),
        expr 'glint' (lenses flash white), 'determined', 'sleep'.
Weapon: bokuto (tucked in the obi when not in hand).
"""
import math

import numpy as np
from PIL import Image

from engine.core import step_frame, clamp, lerp, ease_out, ANIM_FPS
from engine.gfx import INK, stamp_line, rect, pset, shade
from chars import register
from chars.rig import (ChibiDef, POSES, default_params, compose, _rotate_about, OX, OY, CW, CH,
                       pose_idle, pose_walk, pose_talk, pose_cheer, _blink)

# ------------------------------------------------------------------ head
HEAD_PAL = {
    "o": INK,
    "H": (104, 108, 146),   # black hair highlight (blue sheen)
    "h": (62, 62, 90),      # hair mid
    "d": (40, 38, 60),      # hair shade
    "S": (255, 216, 184),   # skin
    "s": (234, 170, 140),   # skin shade
    "L": (214, 234, 255),   # lens
    "G": (255, 255, 255),   # glint
    "E": (46, 40, 66),      # eyes
    "w": (255, 255, 255),
    "m": (170, 70, 80),     # mouth
    "r": (232, 110, 120),   # tongue
    "b": (250, 150, 150),   # blush
    "T": (120, 200, 255),   # tears
    "B": (80, 120, 220),    # gloom
}

BASE = [
    ".....ooooooo.....",   # 0
    "...ooHHHHHhhoo...",   # 1
    "..oHHHHHHHhhhho..",   # 2
    ".oHHHHHHHhhhhhdo.",   # 3
    "odHHHHhhhhhhhhhdo",   # 4
    "odHHhhhhhhhhhhhdo",   # 5
    "odhhhhhdhhhhdhhdo",   # 6 strands
    "odhhShhhShhhhShdo",   # 7 bangs tips
    "odhSSSSSSSSSSSSho",   # 8 forehead
    "odhSoooSSSoooSSho",   # 9 glasses top
    "odhoGLEoooGLEoSho",   # 10 lens (glint top-left, pupil right)
    "odhoLLEoSoLLEoSho",   # 11
    "odhSoooSSSoooSSho",   # 12 glasses bottom
    ".ohSSSSSSSSSSSso.",   # 13
    "..osSSSSSmmSSSo..",   # 14 mouth
    "...oosSSSSSSsoo..",   # 15
    ".....ooooooo.....",   # 16
]


def _head(**rows):
    r = list(BASE)
    for k, v in rows.items():
        i = int(k[1:])
        assert len(v) == len(BASE[i]), (k, v, len(v), len(BASE[i]))
        r[i] = v
    return "\n".join(r)


HEADS = {
    "normal": _head(),
    "blink": _head(r10="odhoGLLoooGLLoSho", r11="odhoEEEoSoEEEoSho"),
    "talk": _head(r14="..osSSSSSooSSSo..", r15="...oosSSSmmSsoo.."),
    "angry": _head(r8="odhSSoSSSSSoSSSho", r9="odhSooooSooooSSho",
                   r11="odhoLEEoSoLEEoSho", r14="..osSSSSoooSSSo.."),
    "shout": _head(r8="odhSSoSSSSSoSSSho", r10="odhoGLEoooGEEoSho",
                   r11="odhoLEEoSoLEEoSho", r13=".ohSSSSSooooSSso.",
                   r14="..osSSSSomrmoSo..", r15="...oosSSSooSsoo.."),
    "shock": _head(r8="odhSoooSSSoooSSho", r9="odhSSSSSSSSSSSSho",
                   r10="odhoGLLoooGLLoSho", r11="odhoLELoSoLELoSho",
                   r13=".ohSSSSSSooSSSso.", r14="..osSSSSomoSSSo..",
                   r15="...oosSSSooSsoo.."),
    "happy": _head(r10="odhoLoLoooLoLoSho", r11="odhooLooSooLooSho",
                   r13=".ohSbbSSSSbbSSso.", r14="..osSSSSmSSmSSo..",
                   r15="...oosSSSmmSsoo.."),
    "sad": _head(r8="odhSSSoSSSoSSSSho", r10="odhoGLLoooGLLoSho",
                 r11="odhoLELoSoLELoSho", r14="..osSSSSSSSSSSo..",
                 r15="...oosSSSmmSsoo.."),
    "cry": _head(r8="odhSSSoSSSoSSSSho", r10="odhoTTToooTTToSho",
                 r11="odhoTTToSoTTToSho", r13=".ohSSTSSSSSTSSso.",
                 r14="..osSTSSSmmTSSo..", r15="...oosTSSSSTsoo.."),
    "hurt": _head(r8="odhSSSoSSSoSSSSho", r10="odhoGoGoooGGooSho",
                  r11="odhooGGoSoGoGoSho", r13=".ohSSSSSSSSSSSso.",
                  r14="..osSSSSSooSSSo..", r15="...oosSSSmmSsoo.."),
    "smug": _head(r10="odhoGGLoooGGLoSho", r11="odhoLGLoSoLGLoSho",
                  r14="..osSSSSSSSSmSo..", r15="...oosSSSmmmsoo.."),
    "glint": _head(r10="odhoGGGoooGGGoSho", r11="odhoLGGoSoLGGoSho"),
    "determined": _head(r8="odhSSoSSSSSoSSSho", r14="..osSSSSmmmSSSo.."),
    "sleep": _head(r10="odhoLLLoooLLLoSho", r11="odhoEEEoSoEEEoSho",
                   r14="..osSSSSSSoSSSo..", r15="...oosSSSSSSsoo.."),
    "gloom": _head(r7="odhhShhBShhBhShdo", r8="odhSSBSSBSSBSSSho"),
}

# ------------------------------------------------------------------ torso
TORSO_PAL = {
    "o": INK,
    "W": (246, 246, 252),   # white gi
    "w": (198, 204, 226),   # gi shade
    "c": (120, 150, 200),   # inner collar
    "S": (255, 216, 184),   # neck skin
    "N": (46, 58, 108),     # dark obi
    "n": (70, 86, 140),     # obi highlight
    "B": (132, 184, 236),   # light-blue hakama
    "b": (98, 146, 206),    # hakama shade
    "d": (72, 108, 168),    # pleat line
    # waiter apron
    "A": (146, 92, 60), "a": (116, 70, 46),
    # happi coat (Otsu fan club)
    "P": (246, 112, 170), "p": (206, 78, 138), "Y": (255, 240, 140),
}

TORSO = """
...oooooo...
..oWcSScWo..
.oWWWcScWWwo
.oWWWWcWWWwo
.oWWWWWcWWwo
.oNnNNNNNNNo
.oBBBBBBBBbo
.oBBBBdBBBbo
.obBBBdBBBbo
.obBBBdBBbbo
..oooooooo..
"""

TORSO_APRON = """
...oooooo...
..oWcSScWo..
.oWWWcScWWwo
.oWWWWcWWWwo
.oWWWWWcWWwo
.oNnNNNNNNNo
.oBoAAAAAobo
.oBoAAAAaobo
.obBoAAaoBbo
.obBoAAaoBbo
..oooooooo..
"""

TORSO_HAPPI = """
...oooooo...
..oYcSScYo..
.oPPYcScYPpo
.oPPPYcYPPpo
.oPPPPYYPPpo
.oNnNNNNNNNo
.oPPPPYPPPpo
.oPPPPYPPPpo
.opPPPYPPPpo
.opPPPYPPppo
..oooooooo..
"""

SLEEVES = {
    "default": ((246, 246, 252), (198, 204, 226)),
    "apron": ((246, 246, 252), (198, 204, 226)),
    "happi": ((246, 112, 170), (206, 78, 138)),
}


def sheathed_bokuto(img, torso_xy, torso_size):
    """Bokuto tucked in the obi: handle forward, blade sticking out behind."""
    tx, ty = torso_xy
    a, b = (tx + 10, ty + 5), (tx - 6, ty + 8)
    stamp_line(img, a, b, 4, INK)
    stamp_line(img, a, b, 2, (204, 150, 92))
    stamp_line(img, (tx + 1, ty + 6.5), b, 1, (235, 190, 125))
    stamp_line(img, a, (tx + 7, ty + 5.5), 2, (96, 58, 40))


# ------------------------------------------------------------------ props
def _glint_prop(img, ctx):
    """Tiny star sparkle on the front lens."""
    hx, hy, hw, hh = ctx["head"]
    x, y = int(hx) + 11, int(hy) + 9
    for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
        pset(img, x + dx, y + dy, (255, 255, 255, 255))
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        pset(img, x + dx, y + dy, (255, 255, 200, 255))


def _tray_prop(img, ctx):
    """Silver tray balanced on the front hand with a parfait glass + cup."""
    if not ctx["hand_f"]:
        return
    x, y = int(round(ctx["hand_f"][0])), int(round(ctx["hand_f"][1]))
    ty = y - 2
    rect(img, x - 6, ty - 1, 14, 3, INK)
    rect(img, x - 5, ty, 12, 1, (214, 220, 232))
    rect(img, x - 5, ty - 0, 5, 1, (245, 248, 255))
    # tea cup
    rect(img, x - 4, ty - 4, 5, 4, INK)
    rect(img, x - 3, ty - 3, 3, 2, (240, 240, 240))
    rect(img, x - 3, ty - 3, 3, 1, (120, 170, 90))
    # parfait glass
    rect(img, x + 1, ty - 9, 6, 9, INK)
    rect(img, x + 2, ty - 8, 4, 3, (255, 236, 220))
    rect(img, x + 2, ty - 5, 4, 2, (120, 70, 50))
    rect(img, x + 2, ty - 3, 4, 1, (255, 236, 220))
    rect(img, x + 3, ty - 2, 2, 2, (200, 210, 230))
    pset(img, x + 4, ty - 10, INK)
    pset(img, x + 3, ty - 9, (228, 59, 68, 255))
    pset(img, x + 4, ty - 9, (228, 59, 68, 255))


def _lightstick(img, hand, ang, col, glow):
    if not hand:
        return
    x, y = hand
    a = math.radians(ang)
    vx, vy = math.cos(a), -math.sin(a)
    tip = (x + vx * 8, y + vy * 8)
    base = (x - vx * 1, y - vy * 1)
    stamp_line(img, base, tip, 3, INK)
    stamp_line(img, (x + vx * 1.5, y + vy * 1.5), tip, 1, col)
    stamp_line(img, base, (x + vx * 1, y + vy * 1), 1, (60, 60, 70))
    # glow pixels around the tip
    tx, ty = int(round(tip[0])), int(round(tip[1]))
    for dx, dy in ((-2, -1), (2, 0), (0, -2), (-1, 2)):
        pset(img, tx + dx, ty + dy, glow)


def _headband_prop(img, ctx):
    """Otsu fan-club hachimaki around the forehead, tails flapping behind."""
    hx, hy, hw, hh = ctx["head"]
    x0, y = int(hx), int(hy) + 6
    t = ctx["t"]
    rect(img, x0 + 1, y - 1, hw - 2, 4, INK)
    rect(img, x0 + 2, y, hw - 4, 2, (250, 250, 250))
    rect(img, x0 + 9, y, 3, 2, (228, 59, 68))
    f = step_frame(t, 8, 2)
    # knot tails behind (left side)
    stamp_line(img, (x0 + 1, y + 1), (x0 - 4, y + 2 + f), 3, INK)
    stamp_line(img, (x0 + 1, y + 1), (x0 - 4, y + 2 + f), 1, (250, 250, 250))
    stamp_line(img, (x0 + 1, y + 1), (x0 - 3, y - 1 - f), 3, INK)
    stamp_line(img, (x0 + 1, y + 1), (x0 - 3, y - 1 - f), 1, (250, 250, 250))


def _stick_f(img, ctx):
    f = step_frame(ctx["t"], 8, 2)
    _lightstick(img, ctx["hand_f"], ctx["params"]["arm_f"] - 90 + (12 if f else -12),
                (120, 255, 140), (190, 255, 200, 255))


def _stick_b(img, ctx):
    f = step_frame(ctx["t"], 8, 2)
    _lightstick(img, ctx["hand_b"], ctx["params"]["arm_b"] - 90 + (-12 if f else 12),
                (255, 120, 200), (255, 200, 235, 255))


# ------------------------------------------------------------------ poses
def pose_idle_s(pp, t, p, d):
    pose_idle(pp, t, p, d)
    if (t % 4.3) > 3.95 and step_frame(t, ANIM_FPS) % 2 == 0:
        pp["props"] = [_glint_prop]


def pose_waiter(pp, t, p, d):
    pose_idle(pp, t, p, d)
    f = step_frame(t, 4, 4)
    pp["arm_f"] = 78 + (2 if f in (1, 2) else 0)
    pp["arm_b"] = -8
    pp["torso"] = "apron"
    pp["expr"] = "blink" if _blink(t) else "normal"
    pp["props"] = [_tray_prop]


def pose_waiter_walk(pp, t, p, d):
    pose_walk(pp, t, p, d)
    pp["arm_f"] = 80
    pp["torso"] = "apron"
    pp["props"] = [_tray_prop]


def pose_otaku_cheer(pp, t, p, d):
    f = step_frame(t, 8, 2)
    pp["torso"] = "happi"
    pp["arm_f"] = 172 if f else 128
    pp["arm_b"] = 128 if f else 172
    pp["dy"] = -2 if f else 0
    pp["legs"] = "jump" if f else "spread"
    pp["expr"] = "shout" if f else "glint"
    pp["props"] = [_headband_prop, _stick_f]
    pp["under"] = [_stick_b]


# The rig stamps shoes as leg_w x leg_w squares, which would make most of the
# short hakama leg white. Draw shoes in a sentinel colour and repaint them:
# lowest row -> white tabi, the rest -> hakama blue.
_SHOE_KEY = (241, 3, 239)
_PANTS = (132, 184, 236)
_TABI = (246, 246, 252)


def _tabi(img):
    a = np.array(img)
    rgb = a[..., :3]
    for key, pants, tabi in ((_SHOE_KEY, _PANTS, _TABI),
                             (shade(_SHOE_KEY, 0.8), shade(_PANTS, 0.8), shade(_TABI, 0.86))):
        m = (rgb == np.array(key, np.uint8)).all(-1) & (a[..., 3] > 0)
        if not m.any():
            continue
        below = np.zeros_like(m)
        below[:-1] = m[1:]
        rgb[m] = pants
        rgb[m & ~below] = tabi
    return Image.fromarray(a, "RGBA")


class ShinpachiDef(ChibiDef):
    """ChibiDef whose sleeve colours follow the torso variant (happi coat)."""

    def render(self, pose="idle", t=0.0, p=None, expr=None, **kw):
        fn = self.poses.get(pose) or POSES.get(pose) or POSES["idle"]
        pp = default_params()
        pp["under"] = []           # props drawn BEHIND the body (need ctx -> 2 passes)
        fn(pp, t, p if p is not None else (t % 1.0), self)
        pp.update({k: v for k, v in kw.items() if k in pp})
        if expr is not None:
            pp["expr"] = expr
        old = (self.sleeve_f, self.sleeve_b)
        self.sleeve_f, self.sleeve_b = SLEEVES.get(pp["torso"], SLEEVES["default"])
        try:
            img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
            if pp["under"]:
                ctx = compose(self, Image.new("RGBA", (CW, CH), (0, 0, 0, 0)), pp, t)
                for f in pp["under"]:
                    f(img, ctx)
            ctx = compose(self, img, pp, t)
            for prop in pp["props"]:
                prop(img, ctx)
            img = _tabi(img)
        finally:
            self.sleeve_f, self.sleeve_b = old
        ax, ay = OX, OY
        if pp["rot"]:
            img, ax, ay = _rotate_about(img, pp["rot"], OX, OY - 14, OX, OY)
        return img, ax, ay


SHINPACHI = register(ShinpachiDef(
    id="shinpachi", name="新八", color=(64, 118, 206), voice=1.12,
    heads=HEADS, head_pal=HEAD_PAL,
    torso={"default": TORSO, "apron": TORSO_APRON, "happi": TORSO_HAPPI}, torso_pal=TORSO_PAL,
    neck=(6, 2), hip=(6, 8), shoulder_f=(9, 3), shoulder_b=(2, 3),
    arm_len=6, arm_w=2, sleeve_f=(246, 246, 252), sleeve_b=(198, 204, 226), sleeve_frac=0.6,
    hand=(255, 216, 184),
    leg_len=6, leg_w=4, leg_gap=3, pants=_PANTS, shoes=_SHOE_KEY, shoe_h=1,
    weapon="bokuto", weapon_len=15, sheathed=sheathed_bokuto,
    poses={"idle": pose_idle_s, "waiter": pose_waiter, "waiter_walk": pose_waiter_walk,
           "otaku_cheer": pose_otaku_cheer},
    desc="志村道场的少主，万事屋的吐槽担当。眼镜是本体，偶像阿通的头号粉丝。",
))
