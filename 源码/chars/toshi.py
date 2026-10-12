"""托西 Toshi — Hijikata cursed by the demon sword Muramasa into a timid otaku.

Same hair / uniform as Hijikata, but droopy watery eyes, a wobbly pout, no
cigarette, a permanent sweat drop and a slouch.
Extra poses: beg (dogeza, grounded: feet anchor = floor), figure (cradling a tiny
anime figurine). Extra exprs: otaku (sparkly eyes + blush), gloom.
"""
import math

from PIL import Image

from engine.core import step_frame, clamp
from engine.gfx import INK, stamp_line, rect, pset
from chars import register
from chars.rig import default_params, compose, OX, OY, CW, CH, pose_idle, _blink, _draw_leg
from chars.hijikata import (SSGDef, SSG_BODY, SKIN, BASE as HJ_BASE, HEAD_PAL as HJ_PAL, mk_head,
                            sheathed_katana, sweat_drop, star_glint, resolve_expr, katana_on_shoulder)

HEAD_PAL = dict(HJ_PAL)
HEAD_PAL.update({
    "E": (70, 92, 150),      # softer blue iris
    "e": (130, 160, 214),    # watery lower iris
})

BASE = list(HJ_BASE[:11]) + [
    "odhSSooSSSSSooSSho",    # 11 brows dropping outward (worried)
    ".odSSEEwSSSEEwSSo.",    # 12 big glossy eyes
    ".ohSoeeSSSSeeoSso.",    # 13 drooping outer corners
    "..osSSSSSoSoSSSo..",    # 14 wobbly pout
    "...oosSSSSoSSsoo..",    # 15
    ".....ooooooooo....",    # 16
]
BASE[10] = "odhSSSSoShSoSSSSho"   # inner brow ends raised


def _h(**rows):
    return mk_head(BASE, **rows)


GT = dict(r11="odhSSoSSShSSSoSSho", r12=".odSSSoSSSSSoSSSo.", r13=".ohSSoSSSSSSSoSso.")  # > <

HEADS = {
    "normal": _h(),
    "blink": _h(r12=".odSooooSSSooooSo.", r13=".ohSSSSSSSSSSSSso."),
    "talk": _h(r14="..osSSSSSSooSSSo..", r15="...oosSSSSmmSsoo.."),
    "angry": _h(**GT, r14="..osSSSSSoooSSSo..", r15="...oosSSSSSSSsoo.."),
    "shout": _h(**GT, r14="..osSSSSSomoSSSo..", r15="...oosSSSSooSsoo.."),
    "shock": _h(r11="odhSSooSShSooSSSho", r12=".odSowwoSSowwoSSo.",
                r13=".ohSSooSSSSooSSso.", r14="..osSSSSSSooSSSo..",
                r15="...oosSSSSSSSsoo.."),
    "happy": _h(r11="odhSSSoSShSSoSSSho", r12=".odSSoSoSSSoSoSSo.",
                r13=".ohSbbSSSSSSbbSso.", r14="..osSSSSSoooSSSo..",
                r15="...oosSSSSmmSsoo.."),
    "sad": _h(r13=".ohSoTeSSSSTeoSso."),
    "cry": _h(r12=".odSSTTwSSSTTwSSo.", r13=".ohSoTTSSSSTToSso.",
              r14="..osSTSSSoSoTSSo..", r15="...oosTSSSoSTsoo.."),
    "hurt": _h(r11="odhSoSoSShSoSoSSho", r12=".odSSoSSSSSSoSSSo.",
               r13=".ohSoSoSSSSoSoSso.", r14="..osSSSSSSooSSSo..",
               r15="...oosSSSSmmSsoo.."),
    "smug": _h(r11="odhSSSoSShSSoSSSho", r12=".odSSoSoSSSoSoSSo.",
               r13=".ohSbbSSSSSSbbSso.", r14="..osSSSSSmmmmSSo..",
               r15="...oosSSSmwwmsoo.."),
    "sleep": _h(r11="odhSSSSSShSSSSSSho", r12=".odSSoooSSSoooSSo.",
                r13=".ohSSSSSSSSSSSSso."),
    "otaku": _h(r11="odhSSooSShSooSSSho", r12=".odSwEwoSSwEwoSSo.",
                r13=".ohbbEEbSSbEEbbso.", r14="..osSSSSSoooSSSo..",
                r15="...oosSSSSmmSsoo.."),
    "gloom": _h(r8="odhhhBShhhhhBShhdo", r9="odhhSBSBhhhSBSBhdo"),
    # face pressed to the floor (dogeza): we only see hair + a sliver of wet cheek
    "down": _h(r8="odhhhhhhHhhhhhhhdo", r9="odhhhhhHhhhhhhhhdo", r10="odhhhhHhhhhhhhhhho",
               r11="odhhhhhhhhhhhhhhho", r12=".odhhhhhhhhhhhhho.", r13=".ohhhhhhhhhhhhhho.",
               r14="..osSSTSSSSSTSSo..", r15="...oosTSSSSSTsoo.."),
}


# ------------------------------------------------------------------ always: sweat + slouch
def nervous_sweat(img, ctx):
    pp = ctx["params"]
    if pp["rot"]:
        return
    e = resolve_expr(ctx["def"], pp["expr"])
    if e in ("happy", "otaku", "smug", "sleep"):
        return
    hx, hy, hw, hh = ctx["head"]
    ph = (ctx["t"] % 1.4) / 1.4
    f = step_frame(ph * 1.4, 8)
    if ph < 0.85:
        sweat_drop(img, int(hx) + 16, int(hy) + 3 + min(4, f // 2))


def slouch(pp, pose, t, p, d):
    if pp["rot"]:
        return
    pp["head_dy"] += 1
    pp["head_dx"] += 1
    if pose == "idle":
        # index fingers poking together, shy otaku fidget
        f = step_frame(t, 6, 4)
        pp["arm_f"] = 42 + (6 if f in (1, 3) else 0)
        pp["arm_b"] = 30 + (6 if f in (0, 2) else 0)


# ------------------------------------------------------------------ figure pose
FIG_ART = [
    "..oo.oo..",
    ".oTTooTTo",
    ".oTSSSTo.",
    "..oSSSo..",
    "..oPPPo..",
    ".oPWPWPo.",
    "..oPPPo..",
    "..oS.So..",
    ".ooooooo.",
    "oggggggGo",
    ".ooooooo.",
]
FIG_PAL = {"o": INK, "T": (70, 214, 200), "S": (255, 224, 200), "P": (255, 120, 170),
           "W": (255, 255, 255), "g": (190, 196, 214), "G": (130, 136, 160)}


def _figure(img, x, y, t):
    """Tiny twin-tail idol figurine standing on a round base; (x, y) = base centre."""
    x, y = int(x), int(y)
    for j, row in enumerate(FIG_ART):
        for i, ch in enumerate(row):
            if ch != ".":
                pset(img, x - 4 + i, y - len(FIG_ART) + 1 + j, FIG_PAL[ch])
    # sparkles
    f = step_frame(t, 6, 6)
    for k, (dx, dy) in enumerate(((-7, -10), (6, -12), (7, -4))):
        if (f + k * 2) % 6 < 2:
            star_glint(img, x + dx, y + dy, 1 if (f + k) % 2 else 2, (255, 250, 200))


def pose_figure(pp, t, p, d):
    """Cradling a tiny anime figurine at face height, gazing lovingly (sparkles)."""
    pose_idle(pp, t, p, d)
    f = step_frame(t, 4, 4)
    pp["arm_f"] = 112 + (4 if f in (1, 2) else 0)
    pp["arm_b"] = 96
    pp["expr"] = "otaku" if not _blink(t, 2.3) else "happy"
    pp["bob"] = -1 if f in (1, 2) else 0

    def fig(img, ctx):
        hx, hy = ctx["hand_f"]
        _figure(img, hx + 2, hy + 1, ctx["t"])
        # both hands under the base
        for dx in (0, 3):
            stamp_line(img, (hx + dx, hy + 1), (hx + dx, hy + 1), 3, INK)
            stamp_line(img, (hx + dx, hy + 1), (hx + dx, hy + 1), 2, SKIN)
    pp["props"] = [fig]


# ------------------------------------------------------------------ dogeza
BEG_ROT = 90          # clockwise body tilt (deg): >90 so the back slopes down to the head


def _rot_cw(pt, deg, c=(OX, OY - 14)):
    a = math.radians(deg)
    dx, dy = pt[0] - c[0], pt[1] - c[1]
    return (c[0] + dx * math.cos(a) - dy * math.sin(a), c[1] + dx * math.sin(a) + dy * math.cos(a))


def render_beg(d, t, p, expr, kw):
    """Dogeza (土下座): rear up on folded legs, back sloping down, forehead on the
    floor, hands flat under it. Grounded: lowest pixel on the feet line.
    Bows with t (every ~0.7 s), sweat flies off, a little tear puddle grows."""
    rot = kw.get("tilt", BEG_ROT)
    f = step_frame(t, 12, 9)
    lift = 2 if f in (0, 1) else (1 if f == 2 else 0)
    floor = OY - 1
    pp = default_params()
    pp.update(legs="custom", hide_arm_f=True, hide_arm_b=True, sheathed=False,
              expr=expr or "down")
    body = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    ctx = compose(d, body, pp, t)
    body = body.rotate(-rot, resample=Image.NEAREST, center=(OX, OY - 14))
    bb = body.getbbox()
    sx, sy = 3, floor - (bb[3] - 1)
    body_l = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    body_l.paste(body, (sx, sy - lift), body)

    def T(pt, dl=lift):
        x, y = _rot_cw(pt, rot)
        return (x + sx, y + sy - dl)

    out = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    hip = T(ctx["hip"], 0)
    # --- folded legs: knee on the floor under the belly, shin back, boot soles up
    knee = (hip[0] + 4, floor - 1)
    heel = (hip[0] - 4, floor - 1)
    for back, off in ((True, -1), (False, 0)):
        _draw_leg(out, d, (hip[0] + off, hip[1]), (knee[0] + off, knee[1]), back=back)
        _draw_leg(out, d, (knee[0] + off, knee[1]), (heel[0] + off, heel[1]), back=back)
    bx, by = int(heel[0]) - 2, int(heel[1])
    rect(out, bx - 2, by - 4, 4, 6, INK)
    rect(out, bx - 1, by - 3, 2, 4, d.shoes)
    pset(out, bx - 1, by - 3, (70, 66, 86))
    # --- arm from the shoulder down to the floor, forearm under the head
    sh = T(ctx["shoulder_f"])
    elbow = (sh[0] + 2, floor - 1)
    stamp_line(out, sh, elbow, 4, INK)
    stamp_line(out, elbow, (elbow[0] + 12, floor - 1), 4, INK)
    stamp_line(out, sh, elbow, 2, d.sleeve_f)
    stamp_line(out, elbow, (elbow[0] + 12, floor - 1), 2, d.sleeve_f)
    out.alpha_composite(body_l)
    # rounded rear sticking up at the back (drawn over the torso end)
    cx, cy = hip[0] + 1, hip[1] - 3 - lift * 0.5
    for yy in range(-6, 7):
        for xx in range(-6, 7):
            dd = xx * xx + yy * yy
            if dd <= 24 and (xx <= 2 or dd <= 12):
                c = INK if dd > 15 else ((80, 78, 106) if (xx + yy) < -3 else d.pants)
                if yy > 2 and c == INK and xx > -3:
                    continue
                pset(out, cx + xx, cy + yy, c)
    # fingertips poking out under the forehead
    bbx = body_l.getbbox()
    fx = bbx[2] - 3
    rect(out, fx - 1, floor - 2, 5, 3, INK)
    rect(out, fx, floor - 1, 3, 1, SKIN)
    # tear puddle + flying sweat
    pw = 2 + (int(t * 3) % 6)
    rect(out, fx + 3, floor, pw + 2, 1, (120, 200, 255))
    rect(out, fx + 4, floor - 1, pw, 1, (170, 225, 255))
    for k in range(2):
        ph = ((t + k * 0.35) % 0.7) / 0.7
        x = bbx[0] + 18 + k * 8 + ph * (5 if k else -5)
        y = bbx[1] - 2 - math.sin(ph * math.pi) * 6
        if ph < 0.8:
            sweat_drop(out, x, y)
    return out


TOSHI = register(SSGDef(
    id="toshi", name="托西", color=(168, 92, 150), voice=1.02,
    heads=HEADS, head_pal=HEAD_PAL, **SSG_BODY,
    sheathed=sheathed_katana,
    poses={"figure": pose_figure, "shoulder": katana_on_shoulder},
    special={"beg": render_beg},
    tweak=slouch,
    always=[nervous_sweat],
    desc="被妖刀村麻纱诅咒的土方——懦弱的宅男人格『托西』。土下座、手办、满头冷汗。",
))
