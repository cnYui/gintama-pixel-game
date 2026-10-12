"""土方十四郎 Hijikata Toushirou  +  the shared Shinsengumi (真选组) kit.

The kit (SSGDef, uniform torso, sheathed katana, helpers) is imported by
kondo / okita / toshi / yamazaki / ito, so it lives here with the vice-chief.

SSGDef = ChibiDef + a few extras:
  * pp['pre']    : callables(img, pctx) drawn BEFORE the body (behind everything);
                   pctx = predicted anchors {'hand_f','sf','tx','ty'}
  * pp['post']   : callables(img, ctx) drawn AFTER the whole-body rotation
  * pp['shift']  : (dx, dy) translate the finished sprite (ground lying poses)
  * self.tweak   : fn(pp, pose, t, p, d) character-wide pose modifier (slouch...)
  * self.always  : props drawn on every pose (cigarette smoke, sweat drops...)
  * self.special : {pose: fn(d, t, p, expr, kw) -> RGBA canvas} fully custom poses
  * extra_params : extra pose params a scene may override through draw_char kw
"""
import math

from PIL import Image

from engine.core import step_frame, clamp, lerp, ease_out, ease_in_out
from engine.gfx import INK, stamp_line, rect, pset
from chars import register
from chars.rig import (ChibiDef, POSES, EXPR_FALLBACK, default_params, compose, draw_weapon,
                       CW, CH, OX, OY, pose_idle, _blink)

# ======================================================================== kit
SSG_TORSO_PAL = {
    "o": INK,
    "K": (50, 48, 72),      # jacket black
    "k": (90, 88, 122),     # jacket highlight (top-left light)
    "j": (34, 32, 50),      # jacket shade
    "Y": (248, 204, 80),    # gold trim
    "y": (198, 144, 54),    # gold shade
    "W": (250, 250, 252),   # cravat
    "w": (192, 200, 224),   # cravat shade
}

SSG_TORSO = """
....oooooo....
...okWWWWKo...
..okkYWWwYKo..
.okKKYWWwYKjo.
.okKKKYWwYKjo.
.okKKKKYwYKjo.
.okKKKKKYKKjo.
.okKKKKKYKKjo.
.okKKKKKyKKjo.
.okKKKKKYKKjo.
.oyYYYYYYYYyo.
..oooooooooo..
"""

SSG_SLEEVE_F = (70, 68, 96)
SSG_SLEEVE_B = (40, 38, 56)
SSG_PANTS = (46, 44, 64)
SSG_SHOES = (24, 22, 30)
SKIN = (255, 218, 186)

# the common SSG ChibiDef arguments (uniform + katana)
SSG_BODY = dict(
    torso=SSG_TORSO, torso_pal=SSG_TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=SSG_SLEEVE_F, sleeve_b=SSG_SLEEVE_B, sleeve_frac=0.78,
    hand=SKIN,
    leg_len=7, leg_w=3, leg_gap=4, pants=SSG_PANTS, shoes=SSG_SHOES,
    weapon="katana", weapon_len=17,
)


def sheathed_katana(img, torso_xy, torso_size):
    """Katana in its black scabbard on the left hip: hilt forward, scabbard behind."""
    tx, ty = torso_xy
    tw, th = torso_size
    hilt = (tx + tw + 1, ty + th - 6.5)
    guard = (tx + tw - 2.5, ty + th - 5.5)
    end = (tx - 5, ty + th - 1.5)
    stamp_line(img, hilt, end, 4, INK)
    stamp_line(img, guard, end, 2, (44, 40, 58))
    stamp_line(img, (guard[0] - 3, guard[1] - 0.5), (end[0] + 1, end[1] - 0.5), 1, (96, 92, 124))
    stamp_line(img, hilt, guard, 2, (74, 82, 124))
    pset(img, hilt[0] - 1, hilt[1] - 1, (140, 150, 200))
    stamp_line(img, (guard[0], guard[1] - 1.5), (guard[0], guard[1] + 1.5), 1, (240, 196, 72))


def resolve_expr(d, e):
    arts = d.heads_art
    e = e or "normal"
    seen = set()
    while e not in arts and e not in seen:
        seen.add(e)
        e = EXPR_FALLBACK.get(e, "normal")
    return e if e in arts else "normal"


def predict(d, pp):
    """Where compose() will put the torso / front shoulder / front hand."""
    hip_y = OY - 1 - d.leg_len + pp["dy"]
    if pp["legs"] == "sit":
        hip_y = OY - 3 + pp["dy"]
    elif pp["legs"] == "kneel":
        hip_y = OY - 1 - d.leg_len + 3 + pp["dy"]
    elif pp["legs"] == "none":
        hip_y = OY - 1 + pp["dy"]
    tx = OX - d.hip[0] + pp["lean"] + pp["dx"]
    ty = hip_y - d.hip[1] + pp["bob"]
    sf = (tx + d.shoulder_f[0], ty + d.shoulder_f[1])
    a = math.radians(pp["arm_f"])
    hand = (sf[0] + math.sin(a) * d.arm_len, sf[1] + math.cos(a) * d.arm_len)
    return {"tx": tx, "ty": ty, "sf": sf, "hand_f": hand, "def": d, "params": pp}


class SSGDef(ChibiDef):
    def __init__(self, *a, tweak=None, always=None, special=None, extra_params=None, **k):
        super().__init__(*a, **k)
        self.extra_params = dict(extra_params or {})   # extra kw a scene may pass (e.g. stream=)
        self.tweak = tweak
        self.always = list(always or [])
        self.special = dict(special or {})
        for name in self.special:          # so charsheet / docs list them
            self.poses.setdefault(name, pose_idle)

    def params(self, pose, t, p, kw):
        fn = self.poses.get(pose) or POSES.get(pose) or POSES["idle"]
        pp = default_params()
        pp.update(pre=[], post=[], shift=(0, 0))
        pp.update(self.extra_params)
        fn(pp, t, p, self)
        if self.tweak:
            self.tweak(pp, pose, t, p, self)
        pp.update({k: v for k, v in kw.items() if k in pp})
        for late in pp.get("late", ()):       # pose hooks that depend on scene kw
            late(pp)
        return pp

    def draw_pp(self, pp, t):
        img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        if pp["pre"]:
            pc = predict(self, pp)
            pc["t"] = t
            for prop in pp["pre"]:
                prop(img, pc)
        ctx = compose(self, img, pp, t)
        for prop in pp["props"]:
            prop(img, ctx)
        for prop in self.always:
            prop(img, ctx)
        return img, ctx

    def render(self, pose="idle", t=0.0, p=None, expr=None, **kw):
        pq = p if p is not None else (t % 1.0)
        if pose in self.special:
            img = self.special[pose](self, t, pq, expr, kw)
            return img, OX, OY
        pp = self.params(pose, t, pq, kw)
        if expr is not None:
            pp["expr"] = expr
        img, ctx = self.draw_pp(pp, t)
        if pp["rot"]:
            img = img.rotate(pp["rot"], resample=Image.NEAREST, center=(OX, OY - 14))
        for prop in pp["post"]:
            prop(img, ctx)
        dx, dy = pp["shift"]
        if dx or dy:
            out = Image.new("RGBA", img.size, (0, 0, 0, 0))
            out.paste(img, (int(dx), int(dy)))
            img = out
        return img, OX, OY


def ground(img, floor=OY - 1):
    """Translate an RGBA canvas vertically so its lowest opaque pixel sits on `floor`."""
    bb = img.getbbox()
    if not bb:
        return img
    dy = floor - (bb[3] - 1)
    if dy == 0:
        return img
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(img, (0, dy))
    return out


def sweat_drop(img, x, y, col=(130, 200, 255)):
    """Tiny manga sweat drop with ink outline (x, y = top point)."""
    x, y = int(x), int(y)
    pset(img, x, y - 1, INK)
    for yy, (a, b) in enumerate(((0, 0), (-1, 1), (-1, 1))):
        pset(img, x + a - 1, y + yy, INK)
        pset(img, x + b + 1, y + yy, INK)
        for xx in range(a, b + 1):
            pset(img, x + xx, y + yy, col)
    rect(img, x - 1, y + 3, 3, 1, INK)
    pset(img, x - 1, y + 1, (230, 245, 255))


def star_glint(img, x, y, s=2, col=(255, 255, 255)):
    x, y = int(x), int(y)
    for i in range(-s, s + 1):
        pset(img, x + i, y, col)
        pset(img, x, y + i, col)


def puff(img, x, y, r, col=(226, 226, 236), edge=(170, 170, 188)):
    """Round pixel smoke puff (no ink outline -> reads as soft smoke)."""
    x, y, r = int(x), int(y), max(1, int(r))
    for yy in range(-r, r + 1):
        for xx in range(-r, r + 1):
            dd = xx * xx + yy * yy
            if dd <= r * r:
                c = edge if dd > (r - 1) * (r - 1) and (xx + yy) > 0 else col
                pset(img, x + xx, y + yy, c)


def mk_head(base, **rows):
    r = list(base)
    for k, v in rows.items():
        i = int(k[1:])
        assert len(v) == len(base[i]), (k, v, len(v), len(base[i]))
        r[i] = v
    return "\n".join(r)


def katana_on_shoulder(pp, t, p, d, length=25):
    """Cool pose for sword users: blade resting on the shoulder, passing BEHIND the head."""
    f = step_frame(t, 4, 4)
    pp["arm_f"] = 148
    pp["arm_b"] = 10
    pp["weapon"] = None
    pp["sheathed"] = False
    pp["bob"] = -1 if f in (1, 2) else 0
    pp["expr"] = "blink" if _blink(t) else "cool"

    def blade(img, pc, length=length):
        draw_weapon(img, "katana", pc["hand_f"], 174, length)
    pp["pre"] = pp.get("pre", []) + [blade]


# =================================================================== hijikata
HEAD_PAL = {
    "o": INK,
    "H": (112, 118, 160),   # hair shine
    "h": (60, 60, 88),      # hair
    "d": (40, 38, 60),      # hair shade
    "S": (255, 218, 186),   # skin
    "s": (234, 172, 142),   # skin shade
    "E": (56, 78, 132),     # blue-grey iris
    "e": (120, 140, 190),   # iris light
    "w": (255, 255, 255),
    "m": (170, 70, 80),     # mouth
    "f": (226, 150, 80),    # cigarette filter
    "C": (246, 246, 240),   # cigarette paper
    "r": (255, 92, 44),     # ember
    "Y": (255, 226, 120),   # hot ember (inhale)
    "R": (228, 40, 56),     # anger vein
    "T": (120, 200, 255),   # tears
    "b": (250, 150, 150),   # blush
    "B": (80, 120, 220),    # gloom lines
    "g": (92, 86, 100),     # soot
    "G": (62, 58, 72),      # soot dark
}

BASE = [
    "......oooooo......",   # 0
    "....ooHHhhhhoo....",   # 1
    "...oHHhhhhhhhhoo..",   # 2
    "..oHhhhhhHhhhhhho.",   # 3
    ".oHhhhhhHhhhhhhhdo",   # 4
    "ohHhhhhHhhhhhhhhdo",   # 5
    "odhhhhhhhhhhhhhhdo",   # 6
    "odhhhhhhhhhhhhhhdo",   # 7
    "odhhhSShhhhhSShhdo",   # 8  V-bangs
    "odhhSSSShhhSSSShdo",   # 9
    "odhSSSSSShSSSSSSho",   # 10 centre lock tip
    "odhSooooShSooooSho",   # 11 heavy scowling lids
    ".odSSEEoSSSoEESSo.",   # 12 blue-grey eyes, inner corners down
    ".ohSSSSSSSSSSSSso.",   # 13
    "..osSSSSSSmofCCro.",   # 14 cigarette
    "...oosSSSSSSsoooo.",   # 15
    ".....ooooooooo....",   # 16
]


def _h(**rows):
    return mk_head(BASE, **rows)


NO_CIG = dict(r14="..osSSSSSSmmSSSo..", r15="...oosSSSSSSSsoo..")
VEIN = dict(r8="odhhhSShhhhhSRhhdo", r9="odhhSSSShhhSRSRhdo", r10="odhSSSSSShSSSRSSho")

HEADS = {
    "normal": _h(),
    "blink": _h(r11="odhSSSSSShSSSSSSho", r12=".odSooooSSSooooSo."),
    "talk": _h(r14="..osSSSSSSoofCCro.", r15="...oosSSSSmmsoooo."),
    "angry": _h(**VEIN, r11="odhSSoooShSoooSSho", r12=".odSSwEoSSSoEwSSo.",
                r14="..osSSSSSmmofCCro."),
    "shout": _h(**VEIN, r11="odhSSoooShSoooSSho", r12=".odSSwEoSSSoEwSSo.",
                r13=".ohSSSSSSSoooSSso.", r14="..osSSSSSomRmoSo..",
                r15="...oosSSSSoooSoo.."),
    "shock": _h(r11="odhSSooSShSooSSSho", r12=".odSowwoSSowwoSSo.",
                r13=".ohSSooSSSSooSSso.", r14="..osSSSSSSSooSSo..",
                r15="...oosSSSSSSSsoo.."),
    "happy": _h(r11="odhSSSoSShSSoSSSho", r12=".odSSoSoSSSoSoSSo.",
                r13=".ohSbbSSSSSSbbSso."),
    "sad": _h(r10="odhSSSSoShSoSSSSho", r11="odhSSooSSSSSooSSho",
              r12=".odSSEESSSSEESSSo.", r14="..osSSSSSSmofCSso.",
              r15="...oosSSSSSSsoCro.", r16=".....oooooooooooo."),
    "cry": _h(r10="odhSSSSoShSoSSSSho", r11="odhSSooSSSSSooSSho",
              r12=".odSSTToSSSoTTSSo.", r13=".ohSSTSSSSSSTSSso.",
              r14="..osSTSSSSmofCCro.", r15="...oosTSSSSSsoooo."),
    "hurt": _h(r11="odhSoSoSShSoSoSSho", r12=".odSSoSSSSSSoSSSo.",
               r13=".ohSoSoSSSSoSoSso.", r14="..osSSSSSSooSSSo..",
               r15="...oosSSSSmmSsoo.."),
    "smug": _h(r11="odhSSSSSShSSSSSSho", r12=".odSooooSSSooooSo.",
               r13=".ohSSEESSSSEESSso.", r14="..osSSSSSmmofCCro."),
    "sleep": _h(r11="odhSSSSSShSSSSSSho", r12=".odSSoooSSSoooSSo.", **NO_CIG),
    # --- smoke pose
    "inhale": _h(r11="odhSSSSSShSSSSSSho", r12=".odSooooSSSooooSo.",
                 r14="..osSSSSSSmofCCYo."),
    "exhale": _h(r11="odhSSSSSShSSSSSSho", r12=".odSooooSSSooooSo.",
                 r13=".ohSSEESSSSEESSso.", r14="..osSSSSSSSoSSSo..",
                 r15="...oosSSSSSSSsoo.."),
    # --- mayo bliss
    "bliss": _h(r11="odhSSSoSShSSoSSSho", r12=".odSSoSoSSSoSoSSo.",
                r13=".ohSbbbSSSSbbbSso.", r14="..osSSSSSmmofCCro."),
    # --- gloom lines (depressed)
    "gloom": _h(r8="odhhhBShhhhhBShhdo", r9="odhhSBSBhhhSBSBhdo",
                r10="odhSSBSBShSSBSBSho"),
}


def _afro():
    """Big round black afro (bumpy curls) + soot-covered face, 26x22, face centred."""
    W, Hh, ox, oy = 26, 22, 4, 5
    grid = [["." for _ in range(W)] for _ in range(Hh)]
    cx, cy, rx, ry = 12.5, 9.0, 12.4, 9.2
    for y in range(Hh):
        for x in range(W):
            a = math.atan2((y - cy) / ry, (x - cx) / rx)
            r = 1.0 + 0.075 * math.cos(a * 12)
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= r * r and y < 18:
                grid[y][x] = "h"
    # curl texture on a staggered grid: highlight arc top-left, shade bottom-right
    for y in range(Hh):
        for x in range(W):
            if grid[y][x] != "h":
                continue
            best = None
            for j in range(-1, 7):
                for i in range(-1, 7):
                    ccx, ccy = 1.5 + i * 4.6 + (j % 2) * 2.3, 1.5 + j * 3.6
                    dd = (x - ccx) ** 2 + (y - ccy) ** 2
                    if best is None or dd < best[0]:
                        best = (dd, x - ccx, y - ccy)
            dd, dx, dy = best
            if 1.4 <= dd <= 4.4 and dx + dy < -0.5:
                grid[y][x] = "H" if (x + y) < 30 else "h"
            elif dd >= 2.2 and dx + dy > 1.2:
                grid[y][x] = "d"
    # soot face from the shock expression (rows 8..16 of the base head)
    face = HEADS["shock"].split("\n")
    soot = {"S": "g", "s": "G", "E": "w", "e": "w"}
    for yy in range(8, 17):
        for xx, ch in enumerate(face[yy]):
            if ch == "." or (ch in "hdH" and grid[oy + yy][ox + xx] != "."):
                continue
            grid[oy + yy][ox + xx] = soot.get(ch, ch)
    for (x, y, c) in ((ox + 5, oy + 13, "S"), (ox + 13, oy + 13, "S"), (ox + 12, oy + 14, "f"),
                      (ox + 13, oy + 14, "C"), (ox + 14, oy + 15, "G")):
        grid[y][x] = c
    # ink outline around everything
    out = [row[:] for row in grid]
    for y in range(Hh):
        for x in range(W):
            if grid[y][x] == ".":
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < W and 0 <= yy < Hh and grid[yy][xx] not in ".o":
                        out[y][x] = "o"
                        break
            elif (x in (0, W - 1) or y == 0) and grid[y][x] != "o":
                out[y][x] = "o"
    return "\n".join("".join(r) for r in out)


HEADS["afro"] = _afro()

# where the cigarette ember sits in each head (head-local px) -> smoke wisps
EMBER = {"normal": (15, 14), "talk": (15, 14), "angry": (15, 14), "smug": (15, 14),
         "happy": (15, 14), "cry": (15, 14), "bliss": (15, 14), "gloom": (15, 14),
         "blink": (15, 14), "inhale": (15, 14), "sad": (15, 15)}


def smoke_wisp(img, x, y, t, seed=0, h=9, col=(214, 214, 226)):
    """Curling cigarette smoke rising from (x, y). Steps at 8 fps."""
    f = step_frame(t, 8)
    for i in range(h):
        k = (i + f) % h
        yy = y - 1 - k
        xx = x + round(1.3 * math.sin(k * 0.8 + seed + f * 0.15)) + k // 4
        if (k + f + seed) % 5 != 4:
            pset(img, xx, yy, col if k < h * 0.6 else (182, 182, 198))


def cig_smoke(img, ctx):
    pp = ctx["params"]
    if pp["rot"]:
        return
    d = ctx["def"]
    e = resolve_expr(d, pp["expr"])
    hx, hy, hw, hh = ctx["head"]
    hx, hy = int(hx), int(hy)
    if e in EMBER:
        ex, ey = EMBER[e]
        smoke_wisp(img, hx + ex, hy + ey - 1, ctx["t"])
    elif e == "shock":
        # the cigarette dangles from the lower lip
        mx, my = hx + 12, hy + 15
        stamp_line(img, (mx, my), (mx + 1, my + 4), 3, INK)
        pset(img, mx, my, (226, 150, 80))
        pset(img, mx, my + 1, (246, 246, 240))
        pset(img, mx + 1, my + 2, (246, 246, 240))
        pset(img, mx + 1, my + 3, (255, 92, 44))
    elif e == "afro":
        # the afro is still smoking
        f = step_frame(t_of(ctx), 8)
        for i in range(3):
            k = ((f + i * 3) % 9) / 9.0
            puff(img, hx + 6 + i * 7 + k * 3, hy - 1 - k * 8, 1 + (1 - k) * 1.5,
                 col=(150, 146, 160), edge=(110, 106, 122))


def t_of(ctx):
    return ctx["t"]


# ------------------------------------------------------------------ props & poses
MAYO = (255, 244, 196)
MAYO_S = (228, 204, 140)
RED = (228, 52, 60)


def _mayo_bottle(img, x, y, squeeze, t, stream=11):
    """Upside-down squeeze bottle of mayonnaise, nozzle pointing down.
    (x, y) = grip point (hand)."""
    x, y = int(x), int(y)
    top = y - 4
    pinch = 1 if squeeze else 0
    widths = [1, 2, 2, 2 - pinch, 2 - pinch, 2, 1]          # half-widths of the body rows
    for i, wv in enumerate(widths):
        rect(img, x - wv - 1, top + i, 2 * wv + 3, 1, INK)
    rect(img, x - 1, top - 1, 3, 1, INK)
    for i, wv in enumerate(widths):
        rect(img, x - wv, top + i, 2 * wv + 1, 1, MAYO)
        pset(img, x + wv, top + i, MAYO_S)
    pset(img, x - 1, top + 1, (255, 255, 255))
    for xx in range(-2 + pinch, 3 - pinch):                  # red net label
        pset(img, x + xx, top + 3 + (xx % 2), RED)
    # red cap + star nozzle
    rect(img, x - 2, top + 7, 5, 3, INK)
    rect(img, x - 1, top + 7, 3, 2, RED)
    pset(img, x, top + 10, INK)
    if squeeze and stream > 0:
        f = step_frame(t, 12)
        y0 = top + 11
        for i in range(stream):
            xx = x + (1 if (i + f) % 6 in (2, 3) else 0)
            pset(img, xx - 1, y0 + i, INK)
            pset(img, xx + 1, y0 + i, INK)
            pset(img, xx, y0 + i, MAYO if (i + f) % 4 else MAYO_S)
        yy = y0 + stream
        rect(img, x - 2, yy, 5, 2, INK)
        rect(img, x - 1, yy, 3, 1, MAYO)


def pose_mayo(pp, t, p, d):
    """Squeezing a mayonnaise bottle (upside down) with a blissful face.
    kw stream=<px> sets the length of the mayo stream (default 6)."""
    pose_idle(pp, t, p, d)
    f = step_frame(t, 6, 4)
    sq = f in (1, 2)
    pp["arm_f"] = 58 if sq else 64
    pp["arm_b"] = 26
    pp["lean"] = 1
    pp["bob"] = 0 if sq else -1
    pp["expr"] = "bliss"

    def prop(img, ctx, sq=sq):
        length = ctx["params"].get("stream", 6)
        if ctx["hand_f"]:
            hx, hy = ctx["hand_f"]
            _mayo_bottle(img, hx + 2, hy, sq, ctx["t"], length)
            stamp_line(img, (hx, hy), (hx, hy), 3, INK)
            stamp_line(img, (hx, hy), (hx, hy), 2, SKIN)
    pp["props"] = [prop]


def pose_smoke(pp, t, p, d):
    """Signature smoke break: hand to the cigarette (inhale), then a long cool exhale."""
    pose_idle(pp, t, p, d)
    ph = (t % 2.4) / 2.4
    if ph < 0.4:
        pp["arm_f"] = 150
        pp["arm_b"] = -8
        pp["expr"] = "inhale"
    else:
        k = (ph - 0.4) / 0.6
        pp["arm_f"] = 112
        pp["arm_b"] = -8
        pp["expr"] = "exhale"
        pp["head_dy"] = -1 if k < 0.3 else 0

        def exhale(img, ctx, k=k):
            hx, hy = ctx["hand_f"]
            hx, hy = int(hx), int(hy)
            rect(img, hx, hy - 3, 5, 3, INK)                 # cigarette between fingers
            rect(img, hx + 1, hy - 2, 2, 1, (246, 246, 240))
            pset(img, hx + 3, hy - 2, (255, 92, 44))
            smoke_wisp(img, hx + 3, hy - 3, ctx["t"], seed=2, h=7)
            X, Y, _, _ = ctx["head"]
            mx, my = int(X) + 12, int(Y) + 14
            for i in range(3):
                kk = clamp(k * 1.5 - i * 0.2)
                if kk <= 0 or kk >= 1:
                    continue
                puff(img, mx + 3 + kk * 12 + i * 2, my - kk * 11 - i * 2, 1 + kk * 3.5)
        pp["props"] = [exhale]


def iai_streak(img, sx, sy, prog, fade=0.0, col=(255, 255, 255), col2=(170, 220, 255)):
    """Flat horizontal crescent in front of the body (iai flash). prog 0..1 sweep, fade 0..1."""
    n = 26
    head = clamp(prog)
    tail = clamp(prog * 0.35 + fade)
    if head <= tail:
        return
    for i in range(n):
        k = tail + (head - tail) * i / (n - 1)
        x = sx - 9 + 34 * k
        y = sy + 5 - 10 * k + 3.5 * math.sin(math.pi * k)
        wv = 1 if i < n * 0.55 else 2
        c = col2 if i < n * 0.3 else col
        rect(img, int(x), int(y), wv + 1, wv, c)


def pose_draw(pp, t, p, d):
    """Iai draw. p 0-0.3 crouch, hand on hilt; 0.3-0.45 flash draw; then hold + glint."""
    pp["expr"] = "angry"
    if p < 0.3:
        k = ease_out(p / 0.3)
        pp["arm_f"] = lerp(10, 30, k)
        pp["arm_b"] = lerp(-10, 20, k)
        pp["legs"] = "spread"
        pp["bob"] = 1
        pp["lean"] = 1
        pp["head_dy"] = 1
        return
    if p < 0.45:
        k = ease_in_out((p - 0.3) / 0.15)
        pp["arm_f"] = lerp(30, 100, k)
        pp["weapon"] = lerp(-40, 12, k)
        pp["arm_b"] = lerp(20, -40, k)
        pp["legs"] = "lunge"
        pp["lean"] = int(lerp(1, 4, k))
        prog, fade = k, 0.0
    else:
        k = (p - 0.45) / 0.55
        pp["arm_f"] = 100
        pp["weapon"] = 12
        pp["arm_b"] = -40
        pp["legs"] = "lunge"
        pp["lean"] = 4
        prog, fade = 1.0, k * 2.2

    def fx(img, ctx, prog=prog, fade=fade, p=p):
        sx, sy = ctx["shoulder_f"]
        iai_streak(img, sx, sy, prog, fade)
        if 0.47 < p < 0.75 and ctx["tip"]:
            x, y = ctx["tip"]
            star_glint(img, x - 3, y - 1, 2 if p < 0.62 else 1)
    pp["props"] = [fx]


HIJIKATA = register(SSGDef(
    id="hijikata", name="土方", color=(52, 84, 160), voice=0.78,
    heads=HEADS, head_pal=HEAD_PAL, **SSG_BODY,
    sheathed=sheathed_katana,
    poses={"smoke": pose_smoke, "mayo": pose_mayo, "draw": pose_draw,
           "shoulder": katana_on_shoulder},
    always=[cig_smoke],
    extra_params={"stream": 6},
    desc="真选组副长『鬼之副长』。V字刘海，眼神凶狠，烟不离口，蛋黄酱狂魔。",
))
