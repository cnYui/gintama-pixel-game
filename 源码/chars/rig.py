"""Chibi character rig.

A character = ASCII head sprites (one per expression) + ASCII torso sprite +
procedurally drawn arms / legs / weapon. Poses are small functions returning a
parameter dict, so every character automatically supports the whole standard
pose library (walk, run, attack, hit, ...) with smooth, lively motion.

Conventions (sprite drawn FACING RIGHT, flipped for facing=-1):
  * arm angle   : degrees from straight DOWN rotating toward the FRONT
                  0 = hanging down, 90 = pointing forward, 180 = straight up,
                  -40 = swung backwards.
  * weapon angle: absolute screen degrees, 0 = pointing forward (right),
                  90 = up, -90 = down, 180 = backward.
  * rot         : whole-body rotation in degrees, counter-clockwise (PIL).
"""
import math
from functools import lru_cache

from PIL import Image, ImageDraw

from engine.core import ANIM_FPS, clamp, lerp, ease_out, ease_in_out, ease_out_back, step_frame
from engine.gfx import INK, ascii_sprite, flip_h, stamp_line, shade, tint, rotate_nearest, scale_nearest, set_alpha

CW, CH = 96, 96          # working canvas for one character frame
OX, OY = 48, 80          # feet (bottom-centre) inside the working canvas

EXPR_FALLBACK = {
    "hurt": "shock", "scared": "shock", "smug": "happy", "blush": "happy", "laugh": "happy",
    "determined": "angry", "serious": "angry", "cry": "sad", "deadpan": "normal",
    "talk_angry": "angry", "shout": "angry", "sleep": "blink", "dizzy": "shock",
    "evil": "smug", "cool": "normal",
}


class ChibiDef:
    """Declarative character definition. See chars/gintoki.py for the reference."""

    def __init__(self, id, name, color, heads, head_pal, torso, torso_pal,
                 neck, hip, shoulder_f, shoulder_b,
                 voice=1.0,
                 arm_len=7, arm_w=2, sleeve_f=(200, 200, 200), sleeve_b=None, sleeve_frac=0.6,
                 hand=(255, 214, 180),
                 leg_len=7, leg_w=3, leg_gap=4, pants=(40, 36, 48), shoes=(30, 26, 34), shoe_h=2,
                 legs_hidden=False,
                 weapon=None, weapon_len=16, sheathed=None,
                 head_anchor=None, poses=None, portraits=None, portrait_pal=None,
                 props=None, desc=""):
        self.id, self.name, self.color, self.voice = id, name, color, voice
        self.heads_art, self.head_pal = heads, head_pal
        self.torso_art, self.torso_pal = torso, torso_pal
        self.neck, self.hip = neck, hip
        self.shoulder_f, self.shoulder_b = shoulder_f, shoulder_b
        self.arm_len, self.arm_w = arm_len, arm_w
        self.sleeve_f = sleeve_f
        self.sleeve_b = sleeve_b if sleeve_b is not None else shade(sleeve_f, 0.78)
        self.sleeve_frac, self.hand = sleeve_frac, hand
        self.leg_len, self.leg_w, self.leg_gap = leg_len, leg_w, leg_gap
        self.pants, self.shoes, self.shoe_h = pants, shoes, shoe_h
        self.legs_hidden = legs_hidden
        self.weapon, self.weapon_len, self.sheathed = weapon, weapon_len, sheathed
        self.head_anchor = head_anchor
        self.poses = dict(poses or {})
        self.portraits_art, self.portrait_pal = portraits or {}, portrait_pal or head_pal
        self.props = props or {}
        self.desc = desc
        self._heads = {}
        self._torsos = {}
        self._ports = {}

    # ---- sprite access -------------------------------------------------
    def head(self, expr):
        e = expr or "normal"
        seen = set()
        while e not in self.heads_art and e not in seen:
            seen.add(e)
            e = EXPR_FALLBACK.get(e, "normal")
        if e not in self.heads_art:
            e = "normal"
        s = self._heads.get(e)
        if s is None:
            s = ascii_sprite(self.heads_art[e], self.head_pal)
            self._heads[e] = s
        return s

    def torso(self, variant="default"):
        arts = self.torso_art if isinstance(self.torso_art, dict) else {"default": self.torso_art}
        if variant not in arts:
            variant = "default"
        s = self._torsos.get(variant)
        if s is None:
            s = ascii_sprite(arts[variant], self.torso_pal)
            self._torsos[variant] = s
        return s

    def portrait(self, expr):
        if not self.portraits_art:
            return None
        e = expr or "normal"
        seen = set()
        while e not in self.portraits_art and e not in seen:
            seen.add(e)
            e = EXPR_FALLBACK.get(e, "normal")
        if e not in self.portraits_art:
            e = "normal"
        s = self._ports.get(e)
        if s is None:
            s = ascii_sprite(self.portraits_art[e], self.portrait_pal)
            self._ports[e] = s
        return s

    # ---- rendering -------------------------------------------------------
    def render(self, pose="idle", t=0.0, p=None, expr=None, **kw):
        """Return (RGBA sprite facing right, anchor_x, anchor_y) where the
        anchor is the feet point. Subclasses may override completely."""
        fn = self.poses.get(pose) or POSES.get(pose) or POSES["idle"]
        pp = default_params()
        fn(pp, t, p if p is not None else (t % 1.0), self)
        pp.update({k: v for k, v in kw.items() if k in pp})
        if expr is not None:
            pp["expr"] = expr
        img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        ctx = compose(self, img, pp, t)
        for prop in pp["props"]:
            prop(img, ctx)
        ax, ay = OX, OY
        if pp["rot"]:
            img, ax, ay = _rotate_about(img, pp["rot"], OX, OY - 14, OX, OY)
        return img, ax, ay


def default_params():
    return {
        "bob": 0, "lean": 0, "dy": 0, "dx": 0,
        "arm_f": 12, "arm_b": -12,
        "legs": "stand", "leg_phase": 0.0, "stride": 3.0, "lift": 2.0,
        "weapon": None,            # angle (deg) or None -> not drawn in hand
        "weapon_kind": None,       # override the def's weapon for this pose
        "sheathed": True,          # draw the sheathed weapon at the waist when not in hand
        "expr": "normal",
        "head_dx": 0, "head_dy": 0,
        "rot": 0,
        "trail": None,             # (a0, a1, progress, radius) slash trail
        "props": [],               # callables(img, ctx)
        "torso": "default",
        "hide_arm_f": False, "hide_arm_b": False,
    }


# ------------------------------------------------------------------ limbs
def _vec_arm(a_deg):
    a = math.radians(a_deg)
    return math.sin(a), math.cos(a)


def _draw_arm(img, d, s, a_deg, sleeve, back=False):
    sx, sy = s
    vx, vy = _vec_arm(a_deg)
    L = d.arm_len
    hx, hy = sx + vx * L, sy + vy * L
    ex, ey = sx + vx * L * d.sleeve_frac, sy + vy * L * d.sleeve_frac
    w = d.arm_w
    hand = shade(d.hand, 0.85) if back else d.hand
    stamp_line(img, (sx, sy), (hx, hy), w + 2, INK)
    stamp_line(img, (hx, hy), (hx, hy), w + 3, INK)
    stamp_line(img, (sx, sy), (hx, hy), w, hand)
    stamp_line(img, (sx, sy), (ex, ey), w, sleeve)
    stamp_line(img, (hx, hy), (hx, hy), w + 1, hand)
    return hx, hy


def _draw_leg(img, d, hip, foot, back=False):
    col = shade(d.pants, 0.8) if back else d.pants
    shoe = shade(d.shoes, 0.8) if back else d.shoes
    w = d.leg_w
    stamp_line(img, hip, foot, w + 2, INK)
    # toe pointing forward
    tx, ty = foot[0] + 1.5, foot[1] - 0.5
    stamp_line(img, foot, (tx, ty), w + 1, INK)
    stamp_line(img, hip, foot, w, col)
    fx, fy = foot
    L = math.hypot(fx - hip[0], fy - hip[1]) or 1
    k = clamp(d.shoe_h / L)
    sx, sy = fx + (hip[0] - fx) * k, fy + (hip[1] - fy) * k
    stamp_line(img, (sx, sy), foot, w, shoe)
    stamp_line(img, foot, (tx - 0.5, ty), w - 1 if w > 2 else w, shoe)


def _legs(img, d, pp, hip):
    """Draw both legs from the hip centre. Feet rest at OY unless airborne."""
    hx, hy = hip
    g = d.leg_gap / 2.0
    mode = pp["legs"]
    ph = pp["leg_phase"]
    st, lift = pp["stride"], pp["lift"]
    ground = OY - 1 + pp["dy"]
    if mode == "walk" or mode == "run":
        out = []
        for i, sgn in ((0, -1), (1, 1)):
            a = ph + (math.pi if i else 0)
            fx = hx + sgn * g * 0.5 + math.sin(a) * st
            fy = ground - max(0.0, math.cos(a)) * lift
            out.append((fx, fy))
        _draw_leg(img, d, (hx - g * 0.5, hy), out[0], back=True)
        _draw_leg(img, d, (hx + g * 0.5, hy), out[1])
    elif mode == "jump":
        _draw_leg(img, d, (hx - g, hy), (hx - g - 2, hy + d.leg_len - 3), back=True)
        _draw_leg(img, d, (hx + g, hy), (hx + g + 3, hy + d.leg_len - 2))
    elif mode == "sit":
        _draw_leg(img, d, (hx - g, hy), (hx - g + d.leg_len, hy + 1), back=True)
        _draw_leg(img, d, (hx + g, hy), (hx + g + d.leg_len, hy + 1))
    elif mode == "kneel":
        _draw_leg(img, d, (hx - g, hy), (hx - g - 3, ground), back=True)
        _draw_leg(img, d, (hx + g, hy), (hx + g + 4, ground - 1))
    elif mode == "spread":
        _draw_leg(img, d, (hx - g, hy), (hx - g - 3, ground), back=True)
        _draw_leg(img, d, (hx + g, hy), (hx + g + 3, ground))
    elif mode == "lunge":
        _draw_leg(img, d, (hx - g, hy), (hx - g - 5, ground), back=True)
        _draw_leg(img, d, (hx + g, hy), (hx + g + 5, ground))
    elif mode in ("none", "custom"):   # custom = pose draws its own legs via props
        pass
    else:  # stand
        _draw_leg(img, d, (hx - g, hy), (hx - g, ground), back=True)
        _draw_leg(img, d, (hx + g, hy), (hx + g, ground))


# ------------------------------------------------------------------ weapons
def draw_weapon(img, kind, hand, angle, length=16, t=0.0):
    """Draw a hand-held weapon/prop from `hand` along absolute `angle` (deg)."""
    a = math.radians(angle)
    vx, vy = math.cos(a), -math.sin(a)
    hx, hy = hand
    tip = (hx + vx * length, hy + vy * length)
    back = (hx - vx * 4, hy - vy * 4)
    if kind == "bokuto":
        stamp_line(img, back, tip, 4, INK)
        stamp_line(img, back, tip, 2, (204, 150, 92))
        stamp_line(img, (hx + vx * 3, hy + vy * 3), (hx + vx * (length - 1), hy + vy * (length - 1)), 1, (235, 190, 125))
        stamp_line(img, back, (hx + vx * 2, hy + vy * 2), 2, (96, 58, 40))
    elif kind in ("katana", "sword"):
        stamp_line(img, back, tip, 4, INK)
        stamp_line(img, (hx + vx * 2, hy + vy * 2), tip, 2, (214, 224, 238))
        stamp_line(img, (hx + vx * 3, hy + vy * 3), tip, 1, (255, 255, 255))
        stamp_line(img, back, (hx + vx * 1, hy + vy * 1), 2, (48, 40, 60))
        gx, gy = hx + vx * 2, hy + vy * 2
        px, py = -vy, vx
        stamp_line(img, (gx - px * 2, gy - py * 2), (gx + px * 2, gy + py * 2), 2, (230, 180, 60))
    elif kind == "benizakura":
        stamp_line(img, back, tip, 5, INK)
        stamp_line(img, (hx + vx * 2, hy + vy * 2), tip, 3, (200, 30, 50))
        stamp_line(img, (hx + vx * 3, hy + vy * 3), tip, 1, (255, 120, 120))
        stamp_line(img, back, (hx + vx * 1, hy + vy * 1), 2, (60, 20, 30))
    elif kind == "umbrella":
        stamp_line(img, back, tip, 5, INK)
        stamp_line(img, (hx + vx * 1, hy + vy * 1), (hx + vx * (length - 3), hy + vy * (length - 3)), 3, (150, 70, 170))
        stamp_line(img, (hx + vx * (length - 3), hy + vy * (length - 3)), tip, 1, (210, 210, 220))
        stamp_line(img, back, (hx, hy), 2, (90, 40, 60))
    elif kind == "umbrella_open":
        stamp_line(img, back, tip, 3, INK)
        stamp_line(img, back, tip, 1, (90, 60, 70))
        d = ImageDraw.Draw(img)
        r = length * 0.75
        cx, cy = tip
        pts = []
        for i in range(9):
            aa = a - math.pi / 2 + math.pi * i / 8
            pts.append((cx + math.cos(aa) * r - vx * r * 0.2, cy - math.sin(aa) * r - vy * r * 0.2))
        d.polygon(pts, fill=(150, 70, 170), outline=INK)
    elif kind == "bazooka":
        stamp_line(img, (hx - vx * 10, hy - vy * 10), (hx + vx * 14, hy + vy * 14), 8, INK)
        stamp_line(img, (hx - vx * 9, hy - vy * 9), (hx + vx * 13, hy + vy * 13), 6, (70, 96, 70))
        stamp_line(img, (hx - vx * 9, hy - vy * 9 - 2), (hx + vx * 13, hy + vy * 13 - 2), 1, (120, 150, 110))
        stamp_line(img, (hx + vx * 12, hy + vy * 12), (hx + vx * 13, hy + vy * 13), 7, (40, 40, 48))
    elif kind == "kunai":
        stamp_line(img, back, (hx + vx * 7, hy + vy * 7), 3, INK)
        stamp_line(img, (hx + vx * 1, hy + vy * 1), (hx + vx * 6, hy + vy * 6), 1, (220, 225, 235))
    elif kind == "naginata":
        L = length + 10
        stamp_line(img, (hx - vx * 10, hy - vy * 10), (hx + vx * L, hy + vy * L), 3, INK)
        stamp_line(img, (hx - vx * 10, hy - vy * 10), (hx + vx * (L - 6), hy + vy * (L - 6)), 1, (150, 96, 60))
        stamp_line(img, (hx + vx * (L - 6), hy + vy * (L - 6)), (hx + vx * L, hy + vy * L), 2, (220, 225, 235))
    elif kind == "kiseru":
        stamp_line(img, back, (hx + vx * 9, hy + vy * 9), 3, INK)
        stamp_line(img, back, (hx + vx * 9, hy + vy * 9), 1, (60, 40, 50))
        stamp_line(img, (hx + vx * 9, hy + vy * 9), (hx + vx * 9, hy + vy * 9 - 1), 2, (220, 180, 60))
    elif kind == "staff":
        stamp_line(img, (hx - vx * 8, hy - vy * 8), tip, 3, INK)
        stamp_line(img, (hx - vx * 8, hy - vy * 8), tip, 1, (150, 110, 60))
    return tip


# ------------------------------------------------------------------ compose
def compose(d, img, pp, t):
    """Draw the character into the working canvas; returns a context dict with
    useful anchor points (for props / scene effects)."""
    bob, lean = pp["bob"], pp["lean"]
    torso = d.torso(pp["torso"])
    tw, th = torso.size
    hip_y = OY - 1 - d.leg_len + pp["dy"]
    if pp["legs"] == "sit":
        hip_y = OY - 3 + pp["dy"]
    elif pp["legs"] == "kneel":
        hip_y = OY - 1 - d.leg_len + 3 + pp["dy"]
    elif pp["legs"] == "none":      # legless character (ghost, sitting in a box...)
        hip_y = OY - 1 + pp["dy"]
    tx = OX - d.hip[0] + lean + pp["dx"]
    ty = hip_y - d.hip[1] + bob
    hip = (tx + d.hip[0], ty + d.hip[1] + 0.5)
    sf = (tx + d.shoulder_f[0], ty + d.shoulder_f[1])
    sb = (tx + d.shoulder_b[0], ty + d.shoulder_b[1])
    kind = pp["weapon_kind"] or d.weapon
    wa = pp["weapon"]
    # sheathed weapon behind body
    if d.sheathed and pp["sheathed"] and (wa is None or kind != d.weapon):
        d.sheathed(img, (tx, ty), torso.size)
    # back arm + legs
    hand_b = None
    if not pp["hide_arm_b"]:
        hand_b = _draw_arm(img, d, sb, pp["arm_b"], d.sleeve_b, back=True)
    if not d.legs_hidden:
        _legs(img, d, pp, hip)
    img.alpha_composite(torso, (int(tx), int(ty)))
    head = d.head(pp["expr"])
    hw, hh = head.size
    ha = d.head_anchor or (hw // 2, hh - 1)
    hx = tx + d.neck[0] - ha[0] + pp["head_dx"]
    hy = ty + d.neck[1] - ha[1] + pp["head_dy"]
    img.alpha_composite(head, (int(hx), int(hy)))
    # front arm + weapon
    hand_f = None
    tip = None
    if not pp["hide_arm_f"]:
        vx, vy = _vec_arm(pp["arm_f"])
        hand_pos = (sf[0] + vx * d.arm_len, sf[1] + vy * d.arm_len)
        if wa is not None and kind:
            tip = draw_weapon(img, kind, hand_pos, wa, d.weapon_len, t)
        hand_f = _draw_arm(img, d, sf, pp["arm_f"], d.sleeve_f)
        if wa is not None and kind in ("bokuto", "katana", "sword", "benizakura", "umbrella", "naginata", "staff"):
            # knuckles over the grip
            stamp_line(img, hand_f, hand_f, d.arm_w + 1, d.hand)
    if pp["trail"]:
        a0, a1, prog, rad = pp["trail"]
        from engine.fx import slash_arc
        slash_arc(img, sf[0], sf[1], rad, a0, a1, prog, (255, 255, 255), 3)
    return {"hand_f": hand_f, "hand_b": hand_b, "tip": tip, "head": (hx, hy, hw, hh),
            "torso": (tx, ty, tw, th), "hip": hip, "shoulder_f": sf, "shoulder_b": sb,
            "t": t, "def": d, "params": pp}


def _rotate_about(img, deg, cx, cy, ax, ay):
    """Rotate the canvas about (cx,cy); return new img + where anchor (ax,ay) went."""
    r = img.rotate(deg, resample=Image.NEAREST, center=(cx, cy))
    return r, ax, ay


# ------------------------------------------------------------------ poses
def _blink(t, period=3.1, seed=0.0):
    return ((t + seed) % period) < 0.12


def pose_idle(pp, t, p, d):
    f = step_frame(t, 4, 4)
    pp["bob"] = -1 if f in (1, 2) else 0
    pp["arm_f"] = 10 + (2 if f in (1, 2) else 0)
    pp["arm_b"] = -10 - (2 if f in (1, 2) else 0)
    pp["expr"] = "blink" if _blink(t) else "normal"


def pose_walk(pp, t, p, d):
    tq = step_frame(t, ANIM_FPS) / ANIM_FPS
    ph = tq * 2 * math.pi * 1.6
    pp["legs"], pp["leg_phase"] = "walk", ph
    pp["stride"], pp["lift"] = 2.5, 2.0
    pp["bob"] = -1 if math.sin(ph * 2) > 0 else 0
    pp["arm_f"] = -math.sin(ph) * 30 + 5
    pp["arm_b"] = math.sin(ph) * 30 - 5
    pp["expr"] = "blink" if _blink(t) else "normal"


def pose_run(pp, t, p, d):
    tq = step_frame(t, ANIM_FPS) / ANIM_FPS
    ph = tq * 2 * math.pi * 2.6
    pp["legs"], pp["leg_phase"] = "run", ph
    pp["stride"], pp["lift"] = 4.0, 3.5
    pp["bob"] = -2 if math.sin(ph * 2) > 0 else 0
    pp["lean"] = 2
    pp["arm_f"] = -math.sin(ph) * 70 + 30
    pp["arm_b"] = math.sin(ph) * 70 + 10
    pp["expr"] = "determined"


def pose_run_away(pp, t, p, d):
    pose_run(pp, t, p, d)
    pp["arm_f"] = 150 + math.sin(t * 30) * 25
    pp["arm_b"] = 170 + math.cos(t * 30) * 25
    pp["expr"] = "shock"
    pp["lean"] = 1


def pose_talk(pp, t, p, d):
    pose_idle(pp, t, p, d)
    f = step_frame(t, 8)
    pp["expr"] = "talk" if f % 2 == 0 else "normal"
    pp["arm_f"] = 45 + 10 * math.sin(t * 5)


def pose_shout(pp, t, p, d):
    f = step_frame(t, 10)
    pp["expr"] = "shout" if f % 2 == 0 else "angry"
    pp["arm_f"] = 100 + 10 * math.sin(t * 20)
    pp["arm_b"] = -30
    pp["lean"] = 1
    pp["bob"] = -1 if f % 2 == 0 else 0


def pose_point(pp, t, p, d):
    """Tsukkomi! Arm thrust straight at someone, angry face."""
    k = ease_out_back(clamp(p * 4))
    pp["arm_f"] = lerp(20, 95, k)
    pp["arm_b"] = -25
    pp["lean"] = int(2 * k)
    pp["legs"] = "lunge" if k > 0.5 else "stand"
    pp["expr"] = "shout" if step_frame(t, 8) % 2 == 0 else "angry"


def pose_shock(pp, t, p, d):
    k = clamp(p * 5)
    pp["dy"] = -int(4 * math.sin(k * math.pi)) if p < 0.2 else 0
    pp["arm_f"] = 150 + 8 * math.sin(t * 40)
    pp["arm_b"] = 160 - 8 * math.sin(t * 40)
    pp["legs"] = "spread"
    pp["lean"] = -1
    pp["expr"] = "shock"
    pp["head_dx"] = int(math.sin(t * 50) * 1)


def pose_hit(pp, t, p, d):
    """Knocked back (use p 0..1). Tilts back, flails, pained face."""
    k = ease_out(clamp(p * 2))
    pp["rot"] = int(25 * k)
    pp["lean"] = -2
    pp["arm_f"] = 140 + 20 * math.sin(t * 30)
    pp["arm_b"] = 190
    pp["legs"] = "jump"
    pp["expr"] = "hurt"


def pose_fly(pp, t, p, d):
    """Sent flying / tumbling through the air (spins with t)."""
    pp["rot"] = int((t * 720) % 360)
    pp["arm_f"] = 160
    pp["arm_b"] = 200
    pp["legs"] = "spread"
    pp["expr"] = "hurt"


def pose_lie(pp, t, p, d):
    pp["rot"] = 90
    pp["arm_f"] = 170
    pp["arm_b"] = 190
    pp["expr"] = "hurt"


def pose_sleep(pp, t, p, d):
    pp["rot"] = 90
    pp["arm_f"] = 30
    pp["arm_b"] = -20
    pp["expr"] = "sleep"
    pp["bob"] = -1 if step_frame(t, 2) % 2 else 0


def pose_attack(pp, t, p, d):
    """Overhead slash. p: 0-0.35 wind up, 0.35-0.55 slash, rest follow-through."""
    pp["expr"] = "determined"
    if p < 0.35:
        k = ease_out(p / 0.35)
        pp["arm_f"] = lerp(40, 170, k)
        pp["weapon"] = lerp(20, 150, k)
        pp["lean"] = -1
        pp["arm_b"] = lerp(-10, 60, k)
    elif p < 0.55:
        k = ease_in_out((p - 0.35) / 0.2)
        pp["arm_f"] = lerp(170, 60, k)
        pp["weapon"] = lerp(150, -40, k)
        pp["lean"] = int(lerp(-1, 3, k))
        pp["legs"] = "lunge"
        pp["arm_b"] = lerp(60, -20, k)
        pp["trail"] = (-80, 60, k * 1.2, 16)
    else:
        k = (p - 0.55) / 0.45
        pp["arm_f"] = 60
        pp["weapon"] = -40
        pp["lean"] = 3
        pp["legs"] = "lunge"
        pp["arm_b"] = -20
        if k < 0.3:
            pp["trail"] = (-80, 60, 1.2 + k * 2, 16)


def pose_slash_up(pp, t, p, d):
    """Rising slash (low -> high)."""
    pp["expr"] = "determined"
    k = ease_in_out(clamp(p / 0.5))
    pp["arm_f"] = lerp(30, 160, k)
    pp["weapon"] = lerp(-60, 110, k)
    pp["legs"] = "lunge"
    pp["lean"] = 2
    if 0.1 < p < 0.8:
        pp["trail"] = (70, -90, k * 1.2, 16)


def pose_thrust(pp, t, p, d):
    k = ease_out_back(clamp(p * 3))
    pp["arm_f"] = 90
    pp["weapon"] = 0
    pp["lean"] = int(lerp(-2, 4, k))
    pp["legs"] = "lunge"
    pp["arm_b"] = -40
    pp["expr"] = "determined"


def pose_ready(pp, t, p, d):
    """Battle stance: weapon pointed forward."""
    f = step_frame(t, 4, 2)
    pp["arm_f"] = 70
    pp["weapon"] = 20
    pp["arm_b"] = 40
    pp["legs"] = "spread"
    pp["bob"] = -1 if f else 0
    pp["expr"] = "determined"


def pose_guard(pp, t, p, d):
    pp["arm_f"] = 80
    pp["weapon"] = 85
    pp["arm_b"] = 70
    pp["legs"] = "spread"
    pp["lean"] = -1
    pp["expr"] = "angry"


def pose_shoulder(pp, t, p, d):
    """Cool pose: weapon resting on the shoulder."""
    f = step_frame(t, 4, 4)
    pp["arm_f"] = 150
    pp["weapon"] = 160
    pp["arm_b"] = 10
    pp["bob"] = -1 if f in (1, 2) else 0
    pp["expr"] = "blink" if _blink(t) else "cool"


def pose_jump(pp, t, p, d):
    pp["legs"] = "jump"
    pp["arm_f"] = 150
    pp["arm_b"] = 140
    pp["expr"] = "determined"


def pose_land(pp, t, p, d):
    pp["legs"] = "spread"
    pp["bob"] = 2 if p < 0.3 else 0
    pp["arm_f"] = 60
    pp["arm_b"] = 50


def pose_sit(pp, t, p, d):
    pose_idle(pp, t, p, d)
    pp["legs"] = "sit"
    pp["arm_f"] = 40
    pp["arm_b"] = 30


def pose_kneel(pp, t, p, d):
    pp["legs"] = "kneel"
    pp["arm_f"] = 20
    pp["arm_b"] = 10
    pp["expr"] = "sad"
    pp["head_dy"] = 1


def pose_cheer(pp, t, p, d):
    f = step_frame(t, 8, 2)
    pp["arm_f"] = 170 if f else 140
    pp["arm_b"] = 140 if f else 170
    pp["dy"] = -2 if f else 0
    pp["legs"] = "jump" if f else "stand"
    pp["expr"] = "happy"


def pose_bow(pp, t, p, d):
    pp["lean"] = 2
    pp["head_dy"] = 2
    pp["head_dx"] = 2
    pp["arm_f"] = 5
    pp["arm_b"] = 5
    pp["expr"] = "blink"


def pose_cry(pp, t, p, d):
    f = step_frame(t, 10, 2)
    pp["expr"] = "cry"
    pp["arm_f"] = 150
    pp["arm_b"] = 150
    pp["head_dx"] = f
    pp["bob"] = -1 if f else 0


def pose_eat(pp, t, p, d):
    f = step_frame(t, 6, 2)
    pp["arm_f"] = 150 if f else 100
    pp["arm_b"] = 60
    pp["expr"] = "talk" if f else "happy"
    pp["bob"] = -1 if f else 0


def pose_think(pp, t, p, d):
    pp["arm_f"] = 160
    pp["arm_b"] = 40
    pp["expr"] = "normal"
    pp["head_dx"] = 0


def pose_arms_crossed(pp, t, p, d):
    f = step_frame(t, 4, 4)
    pp["arm_f"] = 70
    pp["arm_b"] = 60
    pp["bob"] = -1 if f in (1, 2) else 0
    pp["expr"] = "blink" if _blink(t) else "cool"


def pose_wave(pp, t, p, d):
    f = step_frame(t, 6, 2)
    pp["arm_f"] = 160 if f else 135
    pp["arm_b"] = -10
    pp["expr"] = "happy"


def pose_punch(pp, t, p, d):
    k = ease_out_back(clamp(p * 3))
    pp["arm_f"] = lerp(30, 95, k)
    pp["arm_b"] = -40
    pp["lean"] = int(lerp(-1, 4, k))
    pp["legs"] = "lunge"
    pp["expr"] = "shout"


def pose_kick(pp, t, p, d):
    k = ease_out_back(clamp(p * 3))
    pp["legs"] = "custom"
    pp["arm_f"] = 120
    pp["arm_b"] = -60
    pp["lean"] = -2
    pp["expr"] = "shout"

    def kick_leg(img, ctx, k=k, dd=d):
        hip = ctx["hip"]
        _draw_leg(img, dd, (hip[0] - 1, hip[1]), (hip[0] - 2, OY - 1), back=True)
        _draw_leg(img, dd, (hip[0] + 1, hip[1]), (hip[0] + 1 + dd.leg_len * k * 1.3, hip[1] - dd.leg_len * k * 0.4))
    pp["props"] = [kick_leg]


POSES = {
    "idle": pose_idle, "walk": pose_walk, "run": pose_run, "run_away": pose_run_away,
    "talk": pose_talk, "shout": pose_shout, "point": pose_point, "shock": pose_shock,
    "hit": pose_hit, "fly": pose_fly, "lie": pose_lie, "sleep": pose_sleep,
    "attack": pose_attack, "slash_up": pose_slash_up, "thrust": pose_thrust,
    "ready": pose_ready, "guard": pose_guard, "shoulder": pose_shoulder,
    "jump": pose_jump, "land": pose_land, "sit": pose_sit, "kneel": pose_kneel,
    "cheer": pose_cheer, "bow": pose_bow, "cry": pose_cry, "eat": pose_eat,
    "think": pose_think, "arms_crossed": pose_arms_crossed, "wave": pose_wave,
    "punch": pose_punch, "kick": pose_kick,
}


class CustomChar:
    """Base for characters that don't fit the humanoid rig (Sadaharu, Elizabeth...).

    Subclass and implement render(); optionally head(expr) (used for the dialogue
    portrait fallback, scaled x2) and extra `poses` names (documentation only).
    render must return (RGBA sprite FACING RIGHT, anchor_x, anchor_y=feet).
    """
    poses = {}
    portraits_art = {}

    def __init__(self, id, name, color, voice=1.0, desc=""):
        self.id, self.name, self.color, self.voice, self.desc = id, name, color, voice, desc

    def render(self, pose="idle", t=0.0, p=None, expr=None, **kw):  # pragma: no cover
        raise NotImplementedError

    def head(self, expr="normal"):
        """Default: crop the top 20 px of the idle sprite."""
        spr, ax, ay = self.render("idle", 0.0, None, expr)
        bb = spr.getbbox() or (0, 0, spr.width, spr.height)
        return spr.crop((bb[0], bb[1], bb[2], min(bb[3], bb[1] + 20)))

    def portrait(self, expr):
        return None
