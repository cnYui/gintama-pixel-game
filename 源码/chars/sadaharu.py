"""定春 Sadaharu — the Yorozuya's ENORMOUS fluffy white dog (~50x40 px standing).

Custom renderer (not the humanoid rig). Facing right, feet anchor = ground under the
body centre. Parts are drawn back-to-front, each with its own 1px INK outline:
far legs -> body -> tail -> near legs -> head (drooping ears, red 'eyebrow' marks).

Poses: idle walk run sit sleep bite bark (+ fallbacks for every standard pose name:
talk shout point shock hit fly lie attack punch kick jump land cheer cry eat ...).
  bite : p=None -> looping CHOMP CHOMP (jaws open/close ~4x per second);
         p in 0..1 -> one-shot: jaws open wide, SNAP shut at p~0.4, then chew.
         While biting, MOUTH_BITE = (dx, dy) is the maw centre relative to the feet
         anchor (facing right) - put the victim's head there and draw Sadaharu after.
Expressions (head(expr) is also the dialogue portrait): normal blink talk angry shout
shock happy sad cry hurt smug sleep.
"""
import math

import numpy as np
from PIL import Image

from engine.core import step_frame, clamp, lerp, ease_out, ANIM_FPS
from engine.gfx import INK
from chars import register
from chars.rig import CustomChar

CW_, CH_ = 84, 70
AX, AY = 38, 64            # feet anchor inside the canvas

W_L = (255, 255, 255)
W_M = (234, 238, 250)
W_S = (200, 208, 232)
W_D = (162, 170, 204)
RED = (228, 62, 72)
RED_D = (168, 36, 52)
MAW = (120, 24, 44)
TONGUE = (246, 120, 140)
TONGUE_D = (206, 80, 104)
NOSE = (30, 26, 40)
NOSE_H = (110, 110, 130)
INK4 = INK + (255,)

MOUTH_BITE = (22, -27)


# ------------------------------------------------------------------ canvas helpers
class Canvas:
    def __init__(self, w=CW_, h=CH_):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.uint8)
        self.yy, self.xx = np.mgrid[0:h, 0:w].astype(np.float32)

    # -- masks
    def ellipse(self, cx, cy, rx, ry, rot=0.0, fur=0.0, fur_n=9, seed=0.0, fur_top=False):
        x = self.xx + 0.5 - cx
        y = self.yy + 0.5 - cy
        if rot:
            c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            x, y = x * c + y * s, -x * s + y * c
        th = np.arctan2(y, x)
        r = np.sqrt((x / rx) ** 2 + (y / ry) ** 2)
        lim = 1.0
        if fur:
            tuft = (0.5 + 0.5 * np.sin(fur_n * th + seed)) ** 3
            if fur_top:
                tuft = tuft * (y < ry * 0.3)
            lim = 1.0 + fur * tuft
        return r <= lim

    def capsule(self, p0, p1, rad):
        x0, y0 = p0
        x1, y1 = p1
        px, py = self.xx + 0.5, self.yy + 0.5
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy or 1.0
        t = np.clip(((px - x0) * dx + (py - y0) * dy) / L2, 0, 1)
        qx, qy = x0 + t * dx, y0 + t * dy
        return (px - qx) ** 2 + (py - qy) ** 2 <= rad * rad

    # -- painting
    def part(self, mask, cx, cy, rx, ry, tones=(W_L, W_M, W_S, W_D), outline=True, dark=0):
        """Paint a shaded part (light from the top-left) with a 1px ink outline."""
        if not mask.any():
            return
        if outline:
            ring = np.zeros_like(mask)
            ring[1:, :] |= mask[:-1, :]
            ring[:-1, :] |= mask[1:, :]
            ring[:, 1:] |= mask[:, :-1]
            ring[:, :-1] |= mask[:, 1:]
            ring &= ~mask
            self.a[ring] = INK4
        s = (self.xx + 0.5 - cx) / max(rx, 1) * 0.55 + (self.yy + 0.5 - cy) / max(ry, 1) * 0.85
        s = s + dark * 0.35
        chk = ((self.xx + self.yy) % 2) == 0
        idx = np.full(mask.shape, 1, np.int8)
        idx[(s < -0.42) | ((s < -0.34) & chk)] = 0
        idx[(s > 0.42) | ((s > 0.34) & chk)] = 2
        idx[(s > 0.85) | ((s > 0.77) & chk)] = 3
        for i, col in enumerate(tones):
            m = mask & (idx == i)
            self.a[m] = tuple(col) + (255,)

    def px(self, x, y, col):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = tuple(col[:3]) + (255,)

    def rect(self, x, y, w, h, col):
        x, y = int(round(x)), int(round(y))
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 > x0 and y1 > y0:
            self.a[y0:y1, x0:x1] = tuple(col[:3]) + (255,)

    def image(self):
        return Image.fromarray(self.a, "RGBA")


# ------------------------------------------------------------------ head
def draw_head(cv, hx, hy, expr="normal", jaw=0.0, ear_lift=0.0, tilt=0):
    """Frontal fluffy dog head centred at (hx, hy). jaw 0..1 opens the maw wide."""
    hx, hy = float(hx), float(hy)
    o = jaw * 10.0
    # floppy ears (behind the skull) hanging down beside the cheeks
    ea = 18 - ear_lift * 55
    for sgn, dark in ((-1, 0.5), (1, 0.9)):
        ex, ey = hx + sgn * (10.0 + ear_lift * 1.5), hy + 0.5 - ear_lift * 4
        m = cv.ellipse(ex, ey, 3.3, 6.4, rot=sgn * ea, fur=0.15, fur_n=4, seed=sgn)
        cv.part(m, ex - sgn, ey - 3, 3.3, 6.4, dark=dark)
    if jaw > 0.05:
        # maw + lower jaw
        mm = cv.ellipse(hx + 1, hy + 4.2 + o * 0.5, 8.4, 2.6 + o * 0.55)
        cv.part(mm, hx + 1, hy + 4 + o * 0.5, 7, 3 + o * 0.5, tones=(MAW, MAW, MAW, MAW))
        jm = cv.ellipse(hx + 1, hy + 6.5 + o, 8.2, 3.4, fur=0.14, fur_n=7, seed=2.0)
        cv.part(jm, hx + 1, hy + 6 + o, 8.2, 3.4, dark=0.3)
        # tongue on the lower jaw
        ty = hy + 5.0 + o
        cv.rect(hx - 2, ty, 6, 2, TONGUE)
        cv.rect(hx - 1, ty + 1, 4, 1, TONGUE_D)
        # teeth: upper row and lower row
        for i in range(6):
            tx = hx - 5 + i * 2.4
            cv.px(tx, hy + 5.0, W_L)
            cv.px(tx, ty - 1, W_L)
        for fx in (hx - 6, hx + 7):           # fangs
            cv.px(fx, hy + 5.0, W_L)
            cv.px(fx, hy + 6.0, W_L)
            cv.px(fx, ty - 1, W_L)
            cv.px(fx, ty - 2, W_L)
    # skull + fluffy cheeks
    cheek = cv.ellipse(hx, hy + 3.5, 10.6, 5.2, fur=0.22, fur_n=11, seed=0.7)
    skull = cv.ellipse(hx, hy - 1.0, 10.0, 8.6, fur=0.10, fur_n=8, seed=1.9, fur_top=True)
    if jaw > 0.05:
        cheek &= (cv.yy + 0.5) < hy + 4.6
    cv.part(skull | cheek, hx - 1, hy - 1, 10.5, 9.5)
    # muzzle bump (lighter)
    mz = cv.ellipse(hx + 1.2, hy + 3.2, 4.6, 2.8)
    cv.a[mz & (cv.a[..., 3] > 0)] = W_L + (255,)
    cv.px(hx + 4.5, hy + 4.4, W_S)
    cv.px(hx + 3.5, hy + 5.0, W_S)
    # --- face details
    lx, rx_, ey = hx - 4.0, hx + 4.0, hy - 1.0
    # red eyebrow marks
    if expr in ("angry", "shout"):
        for x0, sgn in ((lx, 1), (rx_, -1)):
            cv.rect(x0 - 1, ey - 4, 2, 1, RED)
            cv.rect(x0 + (0 if sgn > 0 else -1), ey - 3, 2, 1, RED)
    elif expr in ("sad", "cry"):
        for x0, sgn in ((lx, -1), (rx_, 1)):
            cv.rect(x0 - 1, ey - 3, 3, 1, RED)
            cv.px(x0 + sgn, ey - 4, RED)
    else:
        for x0 in (lx, rx_):
            cv.rect(x0 - 1, ey - 4, 3, 2, RED)
            cv.px(x0 - 1, ey - 4, (250, 120, 120))
            cv.px(x0 + 1, ey - 3, RED_D)
    # eyes
    for x0 in (lx, rx_):
        if expr in ("blink", "sleep"):
            cv.rect(x0 - 1, ey + 0.5, 3, 1, INK)
        elif expr in ("happy", "smug", "cheer"):
            cv.px(x0 - 1, ey + 0.5, INK)
            cv.px(x0, ey - 0.5, INK)
            cv.px(x0 + 1, ey + 0.5, INK)
        elif expr in ("shock",):
            cv.rect(x0 - 1, ey - 1, 3, 3, INK)
            cv.px(x0, ey, W_L)
        elif expr in ("hurt",):
            cv.px(x0 - 1, ey - 1, INK); cv.px(x0 + 1, ey - 1, INK)
            cv.px(x0, ey, INK)
            cv.px(x0 - 1, ey + 1, INK); cv.px(x0 + 1, ey + 1, INK)
        elif expr in ("angry", "shout"):
            cv.rect(x0 - 1, ey, 2, 2, INK)
            cv.px(x0 - 1, ey, (255, 240, 120))
        else:
            cv.rect(x0 - 1, ey - 1, 2, 3, INK)
            cv.px(x0 - 1, ey - 1, (150, 150, 170))
        if expr == "cry":
            cv.rect(x0 - 1, ey + 1.5, 1, 3, (120, 200, 255))
    # nose
    nx, ny = hx + 1, hy + 1.5
    cv.rect(nx - 2, ny, 4, 2, NOSE)
    cv.rect(nx - 1, ny + 2, 2, 1, NOSE)
    cv.px(nx - 1, ny, NOSE_H)
    # mouth
    if jaw > 0.05:
        return
    my = ny + 3
    if expr in ("talk", "happy", "cheer"):
        # little open smile with tongue
        cv.rect(nx - 2, my, 4, 2, MAW)
        cv.rect(nx - 1, my + 1, 2, 2, TONGUE)
        cv.px(nx - 3, my - 1, INK)
        cv.px(nx + 2, my - 1, INK)
    elif expr in ("shout",):
        cv.rect(nx - 3, my - 0.5, 6, 3, MAW)
        cv.rect(nx - 2, my + 1.5, 4, 1, TONGUE)
        cv.px(nx - 3, my - 0.5, W_L)
        cv.px(nx + 2, my - 0.5, W_L)
    elif expr in ("shock",):
        cv.rect(nx - 1, my, 2, 2, MAW)
    else:
        # the 'ω' dog mouth
        cv.px(nx - 3, my - 1, INK)
        cv.px(nx - 2, my, INK)
        cv.px(nx - 1, my, INK)
        cv.px(nx, my - 1, INK)
        cv.px(nx + 1, my, INK)
        cv.px(nx + 2, my, INK)
        cv.px(nx + 3, my - 1, INK)


# ------------------------------------------------------------------ bodies
def _leg(cv, x_top, y_top, x_foot, y_foot, dark):
    m = cv.capsule((x_top, y_top), (x_foot, y_foot - 2), 3.7)
    m |= cv.ellipse(x_foot + 0.8, y_foot - 1.8, 4.6, 2.4)
    cv.part(m, x_foot - 2, y_top + 4, 5, 9, dark=dark)
    # toe lines
    cv.px(x_foot + 1, y_foot - 1, W_D if dark > 0.5 else W_S)
    cv.px(x_foot + 3, y_foot - 1, W_D if dark > 0.5 else W_S)


def _tail(cv, x, y, wag):
    """Fluffy plume curling up and over toward the back."""
    tx, ty = x + wag * 0.5, y
    m = cv.ellipse(tx + 1, ty + 3, 3.6, 4.5, rot=-20, fur=0.2, fur_n=5, seed=0.4)
    m |= cv.ellipse(tx - 1 + wag * 0.4, ty - 3, 4.2, 5.2, rot=-35 + wag * 5, fur=0.32, fur_n=6, seed=1.3)
    m |= cv.ellipse(tx + 2 + wag * 0.6, ty - 7, 3.6, 2.8, rot=20, fur=0.3, fur_n=5, seed=2.1)
    cv.part(m, tx - 2, ty - 5, 5, 7)


def draw_standing(cv, t, mode="idle", expr="normal", jaw=0.0, head_off=(0, 0), ear_lift=0.0, bob_extra=0):
    ox, oy = AX, AY
    f = step_frame(t, ANIM_FPS)
    if mode == "walk":
        ph = f / ANIM_FPS * 2 * math.pi * 1.4
        stride, lift, bob = 3.0, 2.0, (1 if math.sin(ph * 2) > 0 else 0)
    elif mode == "run":
        ph = f / ANIM_FPS * 2 * math.pi * 2.4
        stride, lift, bob = 5.5, 4.0, (2 if math.sin(ph * 2) > 0 else 0)
    else:
        ph = 0.0
        stride, lift = 0.0, 0.0
        bob = 1 if step_frame(t, 3, 4) in (1, 2) else 0
    bob += bob_extra
    by = oy - 20 - bob
    lean = 2 if mode == "run" else 0

    def foot(base_x, phase):
        if stride == 0:
            return base_x, oy
        return base_x + math.sin(phase) * stride, oy - max(0.0, math.cos(phase)) * lift

    # far legs
    fx, fy = foot(ox + 14, ph + math.pi)
    _leg(cv, ox + 12 + lean, by + 5, fx, fy, dark=0.9)
    fx, fy = foot(ox - 8, ph)
    _leg(cv, ox - 8, by + 5, fx, fy, dark=0.9)
    # tail (behind the body)
    wag = math.sin(f * (2.2 if mode in ("idle", "walk") else 3.0)) * 3
    if mode != "run":
        _tail(cv, ox - 19, by - 9, wag)
    # body
    bm = cv.ellipse(ox + lean, by, 19.5, 12, fur=0.12, fur_n=15, seed=0.3)
    bm |= cv.ellipse(ox + 12 + lean, by - 3, 9.5, 10.5, fur=0.16, fur_n=9, seed=2.2)   # chest ruff
    cv.part(bm, ox - 4 + lean, by - 4, 21, 13)
    if mode == "run":
        _tail(cv, ox - 21, by - 5, wag * 0.5)
    # near legs
    fx, fy = foot(ox + 9, ph)
    _leg(cv, ox + 9 + lean, by + 6, fx, fy, dark=0.2)
    fx, fy = foot(ox - 12, ph + math.pi)
    _leg(cv, ox - 12, by + 6, fx, fy, dark=0.2)
    # haunch line
    for i in range(4):
        cv.px(ox - 6 + i, by + 3 + (1 if i in (0, 3) else 0), W_S)
    # head
    hb = 1 if (mode == "walk" and bob) else 0
    draw_head(cv, ox + 19 + lean + head_off[0], by - 11 + hb + head_off[1], expr, jaw=jaw, ear_lift=ear_lift)


def draw_sitting(cv, t, expr="normal", jaw=0.0, head_off=(0, 0)):
    ox, oy = AX, AY
    f = step_frame(t, ANIM_FPS)
    bob = 1 if step_frame(t, 3, 4) in (1, 2) else 0
    wag = math.sin(f * 2.0) * 2.5
    # tail flat on the ground behind
    m = cv.ellipse(ox - 17 + wag * 0.4, oy - 4, 7, 3.5, rot=-8, fur=0.3, fur_n=8, seed=1.0)
    cv.part(m, ox - 18, oy - 5, 7, 3.5)
    # haunch
    hm = cv.ellipse(ox - 6, oy - 10, 13, 10, fur=0.12, fur_n=10, seed=0.5, fur_top=True)
    cv.part(hm, ox - 9, oy - 13, 13, 10)
    # far front leg
    _leg(cv, ox + 9, oy - 18, ox + 10, oy, dark=0.9)
    # chest/torso upright
    cm = cv.ellipse(ox + 4, oy - 22 - bob, 10.5, 13, fur=0.16, fur_n=11, seed=1.7)
    cv.part(cm, ox + 1, oy - 26, 10.5, 13)
    # hind paw peeking in front of the haunch
    pm = cv.ellipse(ox - 1, oy - 1.8, 5, 2.4)
    cv.part(pm, ox - 2, oy - 3, 5, 2.4, dark=0.3)
    # near front leg
    _leg(cv, ox + 6, oy - 16 - bob, ox + 6, oy, dark=0.2)
    draw_head(cv, ox + 7 + head_off[0], oy - 38 - bob + head_off[1], expr, jaw=jaw)


def draw_sleeping(cv, t):
    ox, oy = AX, AY
    br = 1 if step_frame(t, 2, 4) in (1, 2) else 0
    m = cv.ellipse(ox - 20, oy - 5, 7, 4, rot=-15, fur=0.3, fur_n=8, seed=1.0)
    cv.part(m, ox - 21, oy - 6, 7, 4)
    bm = cv.ellipse(ox - 2, oy - 10 - br * 0.5, 21, 10 + br * 0.5, fur=0.12, fur_n=14, seed=0.9, fur_top=True)
    cv.part(bm, ox - 6, oy - 14, 22, 11)
    # paws out front
    pm = cv.ellipse(ox + 22, oy - 2.5, 6, 2.8) | cv.ellipse(ox + 18, oy - 2.2, 5, 2.5)
    cv.part(pm, ox + 18, oy - 4, 7, 3, dark=0.2)
    cv.px(ox + 25, oy - 2, W_S)
    cv.px(ox + 23, oy - 2, W_S)
    draw_head(cv, ox + 17, oy - 13, "sleep", ear_lift=-0.3)
    # Zz (rising, 3 letters staggered)
    f = step_frame(t, 6)
    for i in range(2):
        k = (f + i * 6) % 12
        zx, zy = ox + 26 + k // 2 + i * 3, oy - 24 - k
        s = 3 if i == 0 else 4
        col = (240, 244, 255)
        for j in range(s):
            cv.px(zx + j, zy, col)
            cv.px(zx + j, zy + s - 1, col)
            cv.px(zx + s - 1 - j, zy + j, col)


# ------------------------------------------------------------------ the character
_POSE_MAP = {
    "idle": "idle", "walk": "walk", "run": "run", "run_away": "run", "sit": "sit",
    "sleep": "sleep", "lie": "sleep", "bite": "bite", "bark": "bark",
    "talk": "talk", "shout": "bark", "point": "bark", "shock": "shock", "hit": "hit",
    "fly": "fly", "attack": "bite", "slash_up": "bite", "thrust": "bite", "punch": "bite",
    "kick": "bite", "eat": "eat", "jump": "jump", "land": "sit", "kneel": "sit", "bow": "sit",
    "cheer": "cheer", "wave": "cheer", "cry": "cry", "ready": "bark", "guard": "idle",
    "shoulder": "idle", "think": "sit", "arms_crossed": "sit",
}


class Sadaharu(CustomChar):
    poses = {k: None for k in ("idle", "walk", "run", "sit", "sleep", "bite", "bark")}
    MOUTH_BITE = MOUTH_BITE

    def __init__(self):
        super().__init__("sadaharu", "定春", (206, 72, 96), voice=0.7,
                         desc="万事屋的看门犬——其实是能长到小山那么大的『犬神』。最爱咬银时的脑袋。")
        self._cache = {}
        self._heads = {}

    # cache key: (mode, anim frame, expr, jaw quantised, extras)
    def _cached(self, key, fn):
        s = self._cache.get(key)
        if s is None:
            if len(self._cache) > 600:
                self._cache.clear()
            cv = Canvas()
            fn(cv)
            s = cv.image()
            self._cache[key] = s
        return s

    def render(self, pose="idle", t=0.0, p=None, expr=None, **kw):
        mode = _POSE_MAP.get(pose, "idle")
        f = step_frame(t, ANIM_FPS)
        blink = (t % 3.3) < 0.12
        e = expr
        if mode in ("idle", "walk", "run", "sit", "cheer", "cry", "talk", "jump", "shock", "hit", "fly"):
            if mode == "idle":
                e = e or ("blink" if blink else "normal")
                spr = self._cached(("idle", f % 12, e), lambda cv: draw_standing(cv, f / ANIM_FPS, "idle", e))
            elif mode == "walk":
                e = e or ("blink" if blink else "normal")
                spr = self._cached(("walk", f % 60, e), lambda cv: draw_standing(cv, f / ANIM_FPS, "walk", e))
            elif mode == "run":
                e = e or "happy"
                spr = self._cached(("run", f % 60, e),
                                   lambda cv: draw_standing(cv, f / ANIM_FPS, "run", e, ear_lift=0.6 if f % 2 else 0.9))
            elif mode == "jump":
                e = e or "happy"
                spr = self._cached(("jump", e), lambda cv: draw_standing(cv, 0.1, "run", e, ear_lift=1.0))
                return self._shift(spr, 0, -6)
            elif mode == "sit":
                e = e or ("blink" if blink else "normal")
                spr = self._cached(("sit", f % 12, e), lambda cv: draw_sitting(cv, f / ANIM_FPS, e))
            elif mode == "cheer":
                e = e or "happy"
                hop = -3 if (f // 2) % 2 else 0
                spr = self._cached(("cheer", f % 12, e), lambda cv: draw_standing(cv, f / ANIM_FPS * 2, "idle", e,
                                                                                   ear_lift=0.5 if hop else 0))
                return self._shift(spr, 0, hop)
            elif mode == "cry":
                e = e or "cry"
                spr = self._cached(("sit", f % 12, e), lambda cv: draw_sitting(cv, f / ANIM_FPS, e))
            elif mode == "talk":
                e = e or ("talk" if (f // 2) % 2 == 0 else "normal")
                spr = self._cached(("sit", f % 12, e), lambda cv: draw_sitting(cv, f / ANIM_FPS, e))
            elif mode == "shock":
                e = e or "shock"
                hop = -4 if (p if p is not None else (t % 1.0)) < 0.2 else 0
                spr = self._cached(("idle", 0, e, "shock"),
                                   lambda cv: draw_standing(cv, 0.0, "idle", e, ear_lift=1.0))
                return self._shift(spr, (1 if f % 2 else -1), hop)
            elif mode == "fly":
                e = e or "hurt"
                spr = self._cached(("idle", 0, e, "hit"), lambda cv: draw_standing(cv, 0.0, "idle", e, ear_lift=1.0))
                return self._rot(spr, int((t * 720) % 360))
            else:  # hit
                e = e or "hurt"
                spr = self._cached(("idle", 0, e, "hit"), lambda cv: draw_standing(cv, 0.0, "idle", e, ear_lift=0.8))
                k = clamp(p if p is not None else 1.0)
                return self._rot(spr, 20 * ease_out(clamp(k * 2)))
            return spr, AX, AY
        if mode == "sleep":
            spr = self._cached(("sleep", f % 24), lambda cv: draw_sleeping(cv, f / ANIM_FPS))
            return spr, AX, AY
        if mode == "bark":
            ff = step_frame(t, 8)
            woof = ff % 4 in (0, 1)
            e = e or ("shout" if woof else "angry")
            hop = -2 if ff % 4 == 0 else 0
            spr = self._cached(("bark", woof, e),
                               lambda cv: draw_standing(cv, 0.0, "idle", e, head_off=(1, -2 if woof else 0),
                                                        ear_lift=0.7 if woof else 0.2))
            return self._shift(spr, 0, hop)
        if mode in ("bite", "eat"):
            if p is None:
                ff = step_frame(t, 8)
                jaw = (1.0, 0.55, 0.0, 0.0)[ff % 4] if mode == "bite" else (0.4, 0.0)[ff % 2]
                shake = (0, 1, 0, -1)[ff % 4] if mode == "bite" else 0
            else:
                if p < 0.35:
                    jaw = ease_out(p / 0.35)
                    shake = 0
                elif p < 0.45:
                    jaw = 1 - (p - 0.35) / 0.1
                    shake = 0
                else:
                    ff = step_frame(t, 10)
                    jaw = (0.0, 0.2)[ff % 2]
                    shake = (1, -1)[ff % 2]
            e = e or ("angry" if jaw < 0.3 else "happy")
            jq = round(jaw * 8) / 8
            spr = self._cached(("bite", jq, e, shake),
                               lambda cv: draw_standing(cv, 0.0, "idle", e, jaw=jq, head_off=(3 + shake, -5),
                                                        ear_lift=0.3))
            return spr, AX, AY
        spr = self._cached(("idle", 0, "normal"), lambda cv: draw_standing(cv, 0.0, "idle", "normal"))
        return spr, AX, AY

    @staticmethod
    def _shift(spr, dx, dy):
        return spr, AX - dx, AY - dy

    @staticmethod
    def _rot(spr, deg):
        """Rotate about the body centre on a padded canvas (no clipping when
        tumbling in 'fly' / tilting in 'hit'); anchor moves with the padding."""
        if not deg:
            return spr, AX, AY
        pad = 26
        big = Image.new("RGBA", (spr.width + 2 * pad, spr.height + 2 * pad), (0, 0, 0, 0))
        big.paste(spr, (pad, pad))
        big = big.rotate(deg, resample=Image.NEAREST, center=(AX + pad, AY - 20 + pad))
        return big, AX + pad, AY + pad

    def portrait_fn(self, expr=None, t=0.0, talking=False):
        """Dialogue portrait: head x2, cropped to 18 rows so it fits the box."""
        e = expr or "normal"
        if talking and step_frame(t, 8) % 2 == 0:
            e = "talk" if expr in (None, "normal") else e
        elif expr is None and (t % 3.1) < 0.12:
            e = "blink"
        key = ("portrait", e)
        s = self._heads.get(key)
        if s is None:
            h = self.head(e)
            h = h.crop((0, 0, h.width, min(h.height, 18)))
            s = h.resize((h.width * 2, h.height * 2), Image.NEAREST)
            self._heads[key] = s
        return s

    def head(self, expr="normal"):
        e = expr or "normal"
        s = self._heads.get(e)
        if s is None:
            cv = Canvas(30, 26)
            draw_head(cv, 15, 13, e)
            img = cv.image()
            bb = img.getbbox() or (0, 0, 30, 26)
            s = img.crop(bb)
            self._heads[e] = s
        return s


SADAHARU = register(Sadaharu())
