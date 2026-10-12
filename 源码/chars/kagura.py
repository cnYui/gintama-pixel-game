"""神乐 Kagura — Yato girl: vermilion hair in two covered buns, red qipao,
purple umbrella that is also a machine gun.

Extras: umbrella_shoot (muzzle flashes, loop on t), umbrella_open (parasol overhead),
        dropkick (p 0..1), sukonbu (chewing vinegar kelp).
Extra exprs: chew, determined, deadpan, sleep.
Weapon: 'umbrella' (slung on her back when not in hand).
"""
import math

from PIL import Image, ImageDraw

from engine.core import step_frame, clamp, lerp, ease_out, ease_in_out, ease_out_back, ANIM_FPS
from engine.gfx import INK, stamp_line, rect, pset, shade
from chars import register
from chars.rig import (ChibiDef, POSES, default_params, compose, _rotate_about, _draw_leg,
                       OX, OY, CW, CH, pose_idle, pose_jump, _blink)

# ------------------------------------------------------------------ head
HEAD_PAL = {
    "o": INK,
    "H": (255, 132, 84),    # vermilion hair light
    "h": (232, 84, 50),     # hair mid
    "d": (172, 50, 44),     # hair shade
    "C": (252, 244, 222),   # bun cover
    "c": (212, 192, 160),   # bun cover shade
    "R": (220, 40, 50),     # bun ribbon
    "S": (255, 220, 190),   # skin
    "s": (238, 176, 146),   # skin shade
    "E": (80, 150, 240),    # blue eyes
    "e": (36, 76, 170),     # iris dark
    "w": (255, 255, 255),
    "m": (176, 60, 70),     # mouth
    "r": (238, 110, 120),   # tongue
    "b": (255, 150, 150),   # blush
    "T": (120, 200, 255),   # tears
    "B": (80, 120, 220),    # gloom
    "K": (40, 60, 40),      # sukonbu strip
}

BASE = [
    ".oooo..........oooo.",   # 0  bun covers
    "oCCCco.oooooo.oCCCco",   # 1
    "oCCCcooHHHHhhooCCCco",   # 2
    "oCcccoHHHHHhhhoCccco",   # 3
    "oRRRRoHHHHHhhhoRRRRo",   # 4  red bands
    ".ooooHHHHHHhhhhoooo.",   # 5
    ".odHHHhHHHHHHhhhhdo.",   # 6
    ".odhHhhhHhhhhhhhhdo.",   # 7 strands
    ".odhhShhhShhhShhhdo.",   # 8 bangs tips
    ".odhSSooSSSSooSShdo.",   # 9  lashes
    ".odhSSwESSSSwESShdo.",   # 10 big blue eyes
    ".odhSSEeSSSSEeSShdo.",   # 11
    ".odhsSSSSSSSSSSshdo.",   # 12
    "..odhSSSSSmSSSShdo..",   # 13 mouth
    "..odhosSSSSSSsohdo..",   # 14 chin
    "..oho.ooooooo.oho...",   # 15 side-lock tips
    "...o...........o....",   # 16
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
    "blink": _head(r9=".odhSSSSSSSSSSSShdo.", r10=".odhSSooSSSSooSShdo.",
                   r11=".odhSSSSSSSSSSSShdo."),
    "talk": _head(r13="..odhSSSSSooSSShdo..", r14="..odhosSSSmmSsohdo.."),
    "angry": _head(r8=".odhhShoShhhoShhhdo.", r9=".odhSSSooSSooSSShdo.",
                   r10=".odhSSwESSSSwESShdo.", r13="..odhSSSSooSSSShdo.."),
    "shout": _head(r8=".odhhShoShhhoShhhdo.", r9=".odhSSSooSSooSSShdo.",
                   r10=".odhSSwESSSSwESShdo.", r12=".odhsSSSSoooSSSshdo.",
                   r13="..odhSSSomrmoSShdo..", r14="..odhosSSoooSsohdo.."),
    "shock": _head(r9=".odhSoooSSSoooSShdo.", r10=".odhSowwoSSowwoShdo.",
                   r11=".odhSoooSSSoooSShdo.", r13="..odhSSSSooSSSShdo..",
                   r14="..odhosSSoroSsohdo.."),
    "happy": _head(r9=".odhSSSSSSSSSSSShdo.", r10=".odhSSooSSSSooSShdo.",
                   r11=".odhSoSSoSSoSSoShdo.", r12=".odhsbbSSSSSbbSshdo.",
                   r13="..odhSSSSoooSSShdo..", r14="..odhosSSSrrSsohdo.."),
    "sad": _head(r8=".odhhShhhShhhShhhdo.", r9=".odhSSSoSSSSoSSShdo.",
                 r10=".odhSSwESSSSwESShdo.", r13="..odhSSSSSSSSSShdo..",
                 r14="..odhosSSmmSSsohdo.."),
    "cry": _head(r9=".odhSooSSSSSSooShdo.", r10=".odhSTTTSSSSTTTShdo.",
                 r11=".odhSTSSSSSSSTSShdo.", r12=".odhsTSSSSSSSTSshdo.",
                 r13="..odhTSSSoooTSShdo..", r14="..odhoTSSSmmSTohdo.."),
    "hurt": _head(r9=".odhSoSoSSSSoSoShdo.", r10=".odhSSoSSSSSSoSShdo.",
                  r11=".odhSoSoSSSSoSoShdo.", r13="..odhSSSSooSSSShdo..",
                  r14="..odhosSSmmSSsohdo.."),
    "smug": _head(r9=".odhSSSSSSSSSSSShdo.", r10=".odhSSooSSSSooSShdo.",
                  r11=".odhSSwESSSSwESShdo.", r13="..odhSSSSSSSmSShdo..",
                  r14="..odhosSSmmmSsohdo.."),
    "deadpan": _head(r9=".odhSSSSSSSSSSSShdo.", r10=".odhSSooSSSSooSShdo.",
                     r11=".odhSSEeSSSSEeSShdo.", r13="..odhSSSSSmmSSShdo.."),
    "determined": _head(r8=".odhhShoShhhoShhhdo.", r9=".odhSSSooSSooSSShdo.",
                        r13="..odhSSSSmmmSSShdo.."),
    "chew": _head(r12=".odhsSSSSSSSSSSsbdo.", r13="..odhSSSSSmmmSSSdo..",
                  r14="..odhosSSSSSSSohdo.."),
    "chew2": _head(r9=".odhSSSSSSSSSSSShdo.", r10=".odhSSooSSSSooSShdo.",
                   r11=".odhSSSSSSSSSSSShdo.", r12=".odhsSSSSSSSSSSbbdo.",
                   r13="..odhSSSSSSoKKKKdo..", r14="..odhosSSSSSSSohdo.."),
    "sleep": _head(r9=".odhSSSSSSSSSSSShdo.", r10=".odhSSooSSSSooSShdo.",
                   r11=".odhSSSSSSSSSSSShdo.", r13="..odhSSSSSoSSSShdo.."),
    "gloom": _head(r8=".odhhShBhShBhShhhdo.", r9=".odhSBooSBSSooBShdo."),
}

# ------------------------------------------------------------------ torso
TORSO_PAL = {
    "o": INK,
    "R": (226, 46, 52),     # qipao red
    "r": (170, 30, 44),     # red shade
    "L": (255, 96, 90),     # red highlight
    "Y": (255, 204, 70),    # gold trim
    "y": (206, 150, 40),    # gold shade
    "S": (255, 220, 190),
}

TORSO = """
...ooooo...
..oYYYYYo..
.oLRRRYRRro
.oLRRRRYRro
.oRRYRRRYro
.oRRRRRRRro
.oRRRYRRRro
.orRRRRRrro
.oYYYYyYyyo
..ooooooo..
"""

PANTS = (62, 52, 78)
SHOES = (30, 24, 38)
UMB = (150, 70, 170)
UMB_L = (192, 116, 206)
UMB_D = (104, 46, 124)


def sheathed_umbrella(img, torso_xy, torso_size):
    """Closed umbrella slung diagonally across her back: crook handle peeking
    over the back shoulder, metal tip poking out below the hem."""
    tx, ty = torso_xy
    # when she sits / kneels the torso drops: slide the umbrella up her back so
    # the metal tip never pokes through the floor (feet line = OY - 1)
    ty = ty - max(0, ty + 13 - OY)
    top, bot = (tx + 1, ty - 6), (tx - 5, ty + 12)
    stamp_line(img, top, bot, 5, INK)
    stamp_line(img, (tx + 0.3, ty - 3.5), (tx - 3.8, ty + 8.5), 3, UMB)
    stamp_line(img, (tx + 0.3, ty - 3.5), (tx - 3.8, ty + 8.5), 1, UMB_L)
    stamp_line(img, (tx - 4, ty + 9), bot, 1, (220, 220, 230))
    # crook handle
    stamp_line(img, top, (tx + 0.5, ty - 4.5), 2, (120, 70, 50))
    pset(img, tx + 2, ty - 7, (120, 70, 50, 255))
    pset(img, tx + 3, ty - 6, (120, 70, 50, 255))


# ------------------------------------------------------------------ props
def _muzzle_prop(img, ctx):
    """Umbrella-gun muzzle flash at the tip (flickers every other anim frame)."""
    tip = ctx["tip"]
    if not tip:
        return
    f = step_frame(ctx["t"], ANIM_FPS)
    x, y = int(round(tip[0])) + 1, int(round(tip[1]))
    if f % 2 == 0:
        big = (f // 2) % 2 == 0
        d = ImageDraw.Draw(img)
        r = 4 if big else 3
        pts = []
        for i in range(10):
            a = i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((x + r * 0.6 + math.cos(a) * rr, y + math.sin(a) * rr))
        d.polygon(pts, fill=(255, 196, 60), outline=INK)
        rect(img, x + 1, y - 1, 2, 3, (255, 255, 220))
        rect(img, x, y, 4, 1, (255, 255, 255))
    else:
        # smoke puff drifting up
        pset(img, x + 1, y - 2, (200, 200, 210, 255))
        pset(img, x + 2, y - 3, (170, 170, 186, 255))
        pset(img, x + 2, y - 2, (220, 220, 230, 255))


def _parasol_prop(img, ctx):
    """Open purple parasol held overhead (nicer than the rig's flat one)."""
    hand = ctx["hand_f"]
    if not hand:
        return
    hx, hy = hand
    apex = (hx - 1, hy - 17)
    stamp_line(img, (hx, hy + 2), apex, 3, INK)
    stamp_line(img, (hx, hy + 2), apex, 1, (120, 80, 70))
    cx, cy = apex[0], apex[1] + 6
    rx, ry = 14, 7
    d = ImageDraw.Draw(img)
    pts = []
    n = 16
    for i in range(n + 1):
        a = math.pi + math.pi * i / n
        pts.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
    # scalloped rim
    rim = []
    ribs = 6
    for i in range(ribs + 1):
        x = cx + rx - 2 * rx * i / ribs
        rim.append((x, cy + 1))
        if i < ribs:
            rim.append((x - rx / ribs, cy - 0.5))
    d.polygon(pts + rim, fill=UMB, outline=INK)
    # light panels on the left (light from top-left), dark on the right
    for i in range(ribs):
        x0 = cx - rx + 2 * rx * i / ribs
        x1 = x0 + 2 * rx / ribs
        col = UMB_L if i < 2 else (UMB if i < 4 else UMB_D)
        if col == UMB:
            continue
        seg_pts = [(cx, cy - ry + 1)]
        for k in range(5):
            xx = lerp(x0 + 1, x1 - 1, k / 4)
            yy = cy - ry * math.sqrt(max(0.0, 1 - ((xx - cx) / rx) ** 2)) + 1.5
            seg_pts.append((xx, max(yy, cy - ry + 1)))
        seg_pts += [(x1 - 1, cy - 1), (x0 + 1, cy - 1)]
        d.polygon(seg_pts, fill=col)
    # ribs
    for i in range(1, ribs):
        x = cx - rx + 2 * rx * i / ribs
        d.line([(cx, cy - ry + 1), (x, cy)], fill=UMB_D)
    d.line([(cx - rx + 2, cy - 2), (cx - 4, cy - ry + 1)], fill=(226, 170, 236))
    # finial
    rect(img, int(cx) - 1, int(cy - ry) - 3, 3, 3, INK)
    pset(img, int(cx), int(cy - ry) - 2, (230, 230, 240, 255))


def _sukonbu_prop(img, ctx):
    """Little red box of 酢昆布 in the front hand."""
    hand = ctx["hand_f"]
    if not hand:
        return
    x, y = int(round(hand[0])), int(round(hand[1]))
    rect(img, x - 2, y - 5, 6, 6, INK)
    rect(img, x - 1, y - 4, 4, 4, (220, 50, 50))
    rect(img, x - 1, y - 4, 4, 1, (255, 220, 90))
    pset(img, x, y - 2, (255, 255, 255, 255))
    # a strip sticking out of the box
    rect(img, x + 1, y - 7, 1, 3, (48, 70, 44))


def _dash_prop(img, ctx):
    """Motion streaks behind the dropkick."""
    k = ctx["params"].get("_dk", 0)
    if k <= 0:
        return
    hx, hy = ctx["hip"]
    for i, dy in enumerate((-8, -3, 2)):
        L = int(6 + 5 * k + (i % 2) * 3)
        x0 = int(hx) - 12 - i * 2
        rect(img, x0 - L, int(hy) + dy, L, 1, (255, 255, 255, 200))


# ------------------------------------------------------------------ poses
def pose_umbrella_shoot(pp, t, p, d):
    f = step_frame(t, ANIM_FPS)
    pp["arm_f"] = 88
    pp["arm_b"] = 72
    pp["weapon"] = 2
    pp["legs"] = "spread"
    pp["lean"] = -1 if f % 2 == 0 else 0
    pp["expr"] = "shout" if (f // 4) % 2 else "determined"
    pp["props"] = [_muzzle_prop]


def pose_umbrella_open(pp, t, p, d):
    pose_idle(pp, t, p, d)
    f = step_frame(t, 4, 4)
    pp["arm_f"] = 150 + (2 if f in (1, 2) else 0)
    pp["arm_b"] = -8
    pp["sheathed"] = False
    pp["expr"] = "blink" if _blink(t) else "deadpan"
    pp["props"] = [_parasol_prop]


def pose_dropkick(pp, t, p, d):
    if p < 0.25:
        k = ease_out(p / 0.25)
        pp["legs"] = "jump"
        pp["dy"] = -int(3 * k)
        pp["arm_f"] = lerp(20, 160, k)
        pp["arm_b"] = lerp(-10, 150, k)
        pp["expr"] = "determined"
        return
    k = ease_out_back(clamp((p - 0.25) / 0.25))
    pp["legs"] = "custom"
    pp["rot"] = int(lerp(20, 72, clamp(k)))
    pp["arm_f"] = -40
    pp["arm_b"] = -70
    pp["expr"] = "shout"
    pp["_dk"] = clamp(k)

    def legs(img, ctx, dd=d, kk=clamp(k)):
        hx, hy = ctx["hip"]
        L = dd.leg_len + 2
        _draw_leg(img, dd, (hx - 1, hy), (hx - 4 - 2 * (1 - kk), hy + L - 2), back=True)
        _draw_leg(img, dd, (hx + 1, hy), (hx + 2, hy + L + 1))
    pp["props"] = [legs]


def pose_sukonbu(pp, t, p, d):
    pose_idle(pp, t, p, d)
    f = step_frame(t, 6, 6)
    bite = f in (0, 1)
    pp["arm_f"] = 158 if bite else 118
    pp["arm_b"] = -10
    pp["expr"] = "chew2" if bite else ("chew" if f % 2 == 0 else "deadpan")
    pp["bob"] = -1 if f in (2, 4) else 0
    pp["props"] = [_sukonbu_prop]


def pose_sit_k(pp, t, p, d):
    """Sitting on the floor, legs stretched forward (her 5 px legs vanish under
    the qipao with the rig's generic sit)."""
    POSES["sit"](pp, t, p, d)
    pp["legs"] = "none"
    pp["dy"] = -2                       # hip at OY - 3, same as the rig's sit

    def legs(img, ctx, dd=d):
        hx, hy = ctx["hip"]
        _draw_leg(img, dd, (hx - 1, hy), (hx + 6, OY - 1), back=True)
        _draw_leg(img, dd, (hx + 1, hy), (hx + 8, OY - 2))
    pp["under"] = pp.get("under", []) + [legs]


def pose_kneel_k(pp, t, p, d):
    """One knee down (back shin on the floor), front foot planted."""
    POSES["kneel"](pp, t, p, d)
    pp["legs"] = "none"
    pp["dy"] = -3

    def legs(img, ctx, dd=d):
        hx, hy = ctx["hip"]
        _draw_leg(img, dd, (hx - 1, hy), (hx - 6, OY - 1), back=True)
        _draw_leg(img, dd, (hx + 1, hy), (hx + 5, OY - 1))
    pp["under"] = pp.get("under", []) + [legs]


class KaguraDef(ChibiDef):
    def render(self, pose="idle", t=0.0, p=None, expr=None, **kw):
        fn = self.poses.get(pose) or POSES.get(pose) or POSES["idle"]
        pp = default_params()
        pp["under"] = []
        pp["_dk"] = 0
        fn(pp, t, p if p is not None else (t % 1.0), self)
        pp.update({k: v for k, v in kw.items() if k in pp})
        if expr is not None:
            pp["expr"] = expr
        img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        if pp["under"]:
            ctx = compose(self, Image.new("RGBA", (CW, CH), (0, 0, 0, 0)), pp, t)
            for f in pp["under"]:
                f(img, ctx)
        ctx = compose(self, img, pp, t)
        for prop in pp["props"]:
            prop(img, ctx)
        ax, ay = OX, OY
        if pp["rot"]:
            img, ax, ay = _rotate_about(img, pp["rot"], OX, OY - 14, OX, OY)
        if pp["_dk"] > 0:
            k = pp["_dk"]
            for i, dy in enumerate((-19, -14, -9)):
                L = int(5 + 7 * k) + (i % 2) * 3
                x1 = OX - 17 - (i % 2) * 2
                for x in range(x1 - L, x1):
                    img.putpixel((x, OY + dy), (255, 255, 255, 230))
            if k > 0.6:
                # impact star at the soles
                a = math.radians(pp["rot"])
                fx0, fy0 = 2.0, 16.0
                sx = OX + fx0 * math.cos(a) + fy0 * math.sin(a) + 3
                sy = OY - 14 - fx0 * math.sin(a) + fy0 * math.cos(a)
                d = ImageDraw.Draw(img)
                r = 4 + (step_frame(t, ANIM_FPS) % 2)
                pts = []
                for i in range(8):
                    aa = i * math.pi / 4 + 0.2
                    rr = r if i % 2 == 0 else r * 0.45
                    pts.append((sx + math.cos(aa) * rr, sy + math.sin(aa) * rr))
                d.polygon(pts, fill=(255, 240, 150), outline=INK)
                d.point((int(sx), int(sy)), fill=(255, 255, 255))
        return img, ax, ay


KAGURA = register(KaguraDef(
    id="kagura", name="神乐", color=(222, 64, 52), voice=1.32,
    heads=HEADS, head_pal=HEAD_PAL, head_anchor=(10, 15),
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(5, 2), hip=(5, 7), shoulder_f=(8, 3), shoulder_b=(2, 3),
    arm_len=6, arm_w=2, sleeve_f=(226, 46, 52), sleeve_b=(170, 30, 44), sleeve_frac=0.5,
    hand=(255, 220, 190),
    leg_len=5, leg_w=3, leg_gap=3, pants=PANTS, shoes=SHOES, shoe_h=1,
    weapon="umbrella", weapon_len=17, sheathed=sheathed_umbrella,
    poses={"umbrella_shoot": pose_umbrella_shoot, "umbrella_open": pose_umbrella_open,
           "dropkick": pose_dropkick, "sukonbu": pose_sukonbu,
           "sit": pose_sit_k, "kneel": pose_kneel_k},
    desc="来自宇宙最强战斗民族『夜兔族』的少女。怪力、大胃王，说话爱加『阿鲁』，最爱醋昆布。",
))
