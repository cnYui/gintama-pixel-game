"""山崎退 Yamazaki Sagaru — Shinsengumi spy. Aggressively plain.

Plain dark-brown hair, plain dot eyes, plain everything.
Extra poses: anpan (munching the stakeout bean bun), badminton (racket swing;
p drives one swing, else loops every 0.9 s; the shuttlecock flies off on the hit).
Extra exprs: chew (puffed cheeks), dead (anpan-stakeout burnout eyes), focus.
"""
import math

from engine.core import step_frame, clamp, lerp, ease_in_out, ease_out
from engine.gfx import INK, stamp_line, rect, pset
from chars import register
from chars.rig import pose_idle, _blink
from chars.hijikata import SSGDef, SSG_BODY, SKIN, sheathed_katana, mk_head, katana_on_shoulder

HEAD_PAL = {
    "o": INK,
    "H": (124, 100, 90),    # hair light
    "h": (76, 58, 54),      # plain dark-brown hair
    "d": (50, 38, 38),      # hair shade
    "S": (255, 216, 184),
    "s": (234, 170, 140),
    "m": (170, 70, 80),
    "w": (255, 255, 255),
    "b": (250, 150, 150),
    "T": (120, 200, 255),
    "G": (170, 150, 170),   # eye bags
    "B": (80, 120, 220),
    "R": (228, 40, 56),
    "c": (214, 150, 80),    # anpan crumbs
}

BASE = [
    "......oooooo......",   # 0
    "....ooHHHhhhoo....",   # 1
    "...oHHHhhhhhhhoo..",   # 2
    "..oHHhhhhhhhhhhho.",   # 3
    ".oHhhhhhhhhhhhhhdo",   # 4
    "ohHhhhhhhhhhhhhhdo",   # 5
    "odhhhhhhhhhhhhhhdo",   # 6
    "odhhhhhhhhhhhhhhdo",   # 7
    "odhhhhhhhhhhShhhdo",   # 8  plain parted bangs
    "odhhhhShhhhSSShhdo",   # 9
    "odhSSSSShhSSSSShdo",   # 10
    "odhSSSoSSSSSoSSSho",   # 11 plain dot eyes (1x2)
    ".ohSSSoSSSSSoSSSo.",   # 12
    ".ohSSSSSSSSSSSSso.",   # 13
    "..osSSSSSSmmSSSo..",   # 14
    "...oosSSSSSSSsoo..",   # 15
    ".....ooooooooo....",   # 16
]


def _h(**rows):
    return mk_head(BASE, **rows)


HEADS = {
    "normal": _h(),
    "blink": _h(r11="odhSSSSSSSSSSSSSho", r12=".ohSSooSSSSSooSSo."),
    "talk": _h(r14="..osSSSSSSooSSSo..", r15="...oosSSSSmmSsoo.."),
    "angry": _h(r10="odhSSoSShhSSoSShdo", r11="odhSSSoSSSSSoSSSho",
                r14="..osSSSSSmmmSSSo.."),
    "shout": _h(r10="odhSSoSShhSSoSShdo", r13=".ohSSSSSSSoooSSso.",
                r14="..osSSSSSSomoSSo..", r15="...oosSSSSooSsoo.."),
    "shock": _h(r10="odhSSooShhSooSShdo", r11="odhSSowoSSSowoSSho",
                r12=".ohSSSoSSSSSoSSSo.", r14="..osSSSSSSooSSSo.."),
    "happy": _h(r11="odhSSSoSSSSSoSSSho", r12=".ohSSoSoSSSoSoSSo.",
                r13=".ohSbbSSSSSSbbSso.", r14="..osSSSSSomoSSSo.."),
    "sad": _h(r10="odhSSSSoShoSSSShdo", r13=".ohSSSSSSSSSSSSso.",
              r14="..osSSSSSSooSSSo.."),
    "cry": _h(r10="odhSSSSoShoSSSShdo", r12=".ohSSTTSSSSSTTSSo.",
              r13=".ohSSTSSSSSSTSSso.", r14="..osSTSSSSooTSSo..",
              r15="...oosTSSSSSTsoo.."),
    "hurt": _h(r11="odhSSoSoSSSoSoSSho", r12=".ohSSSoSSSSSoSSSo.",
               r13=".ohSSoSoSSSoSoSso.", r14="..osSSSSSSooSSSo.."),
    "smug": _h(r11="odhSSSSSSSSSSSSSho", r12=".ohSSooSSSSSooSSo.",
               r14="..osSSSSSSSmmoSo.."),
    "sleep": _h(r11="odhSSSSSSSSSSSSSho", r12=".ohSSooSSSSSooSSo.",
                r14="..osSSSSSSSoSSSo.."),
    "dead": _h(r11="odhSSoooSSSoooSSho", r12=".ohSSSoSSSSSoSSSo.",
               r13=".ohSSGGSSSSGGSSso.", r14="..osSSSSSmmmSSSo.."),
    "focus": _h(r10="odhSSooShhSooSShdo", r11="odhSSSoSSSSSoSSSho",
                r14="..osSSSSSSSoSSSo.."),
    "gloom": _h(r8="odhhhBhhhhhhBhhhdo", r9="odhhhBShhhhBSShhdo",
                r10="odhSSBSShhSBSSShdo"),
}
HEADS["chew"] = _h(r12=".ohSSSoSSSSSoSSSo.", r13="oSbSSSSSSSSSSSbSSo",
                   r14=".osSSSSSSSmmSSSSo.", r15="..oosSSSSSSSSsoo..")

# ------------------------------------------------------------------ anpan
BUN = (214, 150, 80)
BUN_L = (242, 194, 124)
BUN_D = (164, 100, 54)


def _anpan(img, x, y, bitten):
    """Round bean bun (6x5) centred at (x, y); `bitten` bites taken (0..2)."""
    x, y = int(x), int(y)
    rect(img, x - 2, y - 3, 5, 7, INK)
    rect(img, x - 3, y - 2, 7, 5, INK)
    rect(img, x - 2, y - 2, 5, 5, BUN)
    rect(img, x - 1, y - 2, 3, 1, BUN_L)
    pset(img, x - 2, y - 1, BUN_L)
    rect(img, x - 1, y + 2, 4, 1, BUN_D)
    pset(img, x + 2, y + 1, BUN_D)
    pset(img, x, y - 1, (90, 40, 40))           # the little navel on top
    if bitten >= 1:                              # bite: bean paste showing
        rect(img, x + 1, y - 3, 3, 3, (0, 0, 0, 0))
        pset(img, x + 1, y - 2, INK)
        pset(img, x + 2, y - 1, INK)
        pset(img, x + 3, y - 1, INK)
        pset(img, x + 1, y - 1, (110, 40, 50))
    if bitten >= 2:
        rect(img, x + 2, y, 2, 3, (0, 0, 0, 0))
        pset(img, x + 2, y, INK)
        pset(img, x + 2, y + 1, (110, 40, 50))
        pset(img, x + 2, y + 2, INK)


def pose_anpan(pp, t, p, d):
    """Stakeout lunch: munching an anpan (bite, chew, chew...). Loops every 1.5 s."""
    pose_idle(pp, t, p, d)
    ph = (t % 1.5) / 1.5
    bites = int(t / 1.5) % 3
    if ph < 0.25:            # bring to mouth
        pp["arm_f"] = 158
        pp["expr"] = "talk"
    elif ph < 0.35:          # CHOMP
        pp["arm_f"] = 162
        pp["expr"] = "chew"
        pp["head_dy"] = 1
    else:                    # chew chew
        f = step_frame(t, 6, 2)
        pp["arm_f"] = 112
        pp["expr"] = "chew" if f else "normal"
        pp["bob"] = -1 if f else 0
    pp["arm_b"] = 20
    bites_now = bites + (1 if ph >= 0.3 else 0)

    def bun(img, ctx, b=bites_now):
        hx, hy = ctx["hand_f"]
        _anpan(img, hx + 2, hy - 3, min(2, b))
        stamp_line(img, (hx, hy), (hx, hy), 3, INK)
        stamp_line(img, (hx, hy), (hx, hy), 2, SKIN)
    pp["props"] = [bun]


# ------------------------------------------------------------------ badminton
def _racket(img, hand, ang):
    """Badminton racket from the hand along absolute angle `ang` (deg, 0=right, 90=up)."""
    a = math.radians(ang)
    vx, vy = math.cos(a), -math.sin(a)
    hx, hy = hand
    grip_end = (hx - vx * 2, hy - vy * 2)
    shaft_end = (hx + vx * 7, hy + vy * 7)
    stamp_line(img, grip_end, shaft_end, 3, INK)
    stamp_line(img, grip_end, (hx + vx * 1, hy + vy * 1), 1, (230, 230, 240))
    stamp_line(img, (hx + vx * 2, hy + vy * 2), shaft_end, 1, (170, 176, 196))
    # oval head (4 wide x 6 long) with strings
    cx, cy = hx + vx * 10.5, hy + vy * 10.5
    px, py = -vy, vx
    pts = []
    for i in range(24):
        th = i * 2 * math.pi / 24
        pts.append((cx + vx * math.cos(th) * 3.6 + px * math.sin(th) * 2.6,
                    cy + vy * math.cos(th) * 3.6 + py * math.sin(th) * 2.6))
    for (x, y) in pts:
        rect(img, int(round(x)) - 1, int(round(y)) - 1, 3, 3, INK)
    for u in (-1.8, 0, 1.8):
        for k in range(-3, 4):
            pset(img, cx + vx * k * 0.8 + px * u * 0.8, cy + vy * k * 0.8 + py * u * 0.8, (236, 236, 244))
            pset(img, cx + vx * u + px * k * 0.55, cy + vy * u + py * k * 0.55, (236, 236, 244))
    for (x, y) in pts:
        pset(img, int(round(x)), int(round(y)), (226, 70, 70))


def _shuttle(img, x, y):
    x, y = int(x), int(y)
    rect(img, x - 1, y - 1, 5, 3, INK)
    rect(img, x, y, 2, 1, (250, 250, 255))
    pset(img, x + 2, y, (220, 60, 60))


def pose_badminton(pp, t, p, d):
    """Badminton swing (Yamazaki's secret training). p: 0-0.4 wind-up behind,
    0.4-0.55 smash (trail + shuttlecock launches), then follow-through."""
    q = p if p is not None else (t % 0.9) / 0.9
    pp["legs"] = "spread"
    pp["expr"] = "focus"
    if q < 0.4:
        k = ease_out(q / 0.4)
        arm, ang = lerp(40, 190, k), lerp(-20, 150, k)
        pp["lean"] = -1
        pp["arm_b"] = lerp(0, 100, k)
    elif q < 0.55:
        k = ease_in_out((q - 0.4) / 0.15)
        arm, ang = lerp(190, 70, k), lerp(150, -30, k)
        pp["lean"] = int(lerp(-1, 3, k))
        pp["legs"] = "lunge"
        pp["arm_b"] = -30
        pp["expr"] = "shout"
    else:
        arm, ang = 60, -40
        pp["lean"] = 3
        pp["legs"] = "lunge"
        pp["arm_b"] = -30
    pp["arm_f"] = arm

    def prop(img, ctx, ang=ang, q=q):
        if 0.42 < q < 0.62:
            sx, sy = ctx["shoulder_f"]
            from engine.fx import slash_arc
            slash_arc(img, sx, sy, 15, -100, 30, clamp((q - 0.42) / 0.12), (255, 255, 255), 2)
        _racket(img, ctx["hand_f"], ang)
        hx, hy = ctx["hand_f"]
        stamp_line(img, (hx, hy), (hx, hy), 3, INK)
        stamp_line(img, (hx, hy), (hx, hy), 2, SKIN)
        if q >= 0.5:                               # shuttlecock rockets away
            k = (q - 0.5) / 0.5
            _shuttle(img, hx + 12 + k * 40, hy - 10 - k * 18)
        elif q < 0.3:                              # dropping toward him
            _shuttle(img, hx + 10, hy - 22 + q * 30)
    pp["props"] = [prop]


YAMAZAKI = register(SSGDef(
    id="yamazaki", name="山崎", color=(96, 120, 84), voice=0.92,
    heads=HEADS, head_pal=HEAD_PAL, **SSG_BODY,
    sheathed=sheathed_katana,
    poses={"anpan": pose_anpan, "badminton": pose_badminton, "shoulder": katana_on_shoulder},
    desc="真选组监察（密探）。存在感稀薄的普通人，蹲点只吃红豆面包，一有空就偷练羽毛球。",
))
