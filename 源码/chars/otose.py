"""寺田登势 Otose — Kabukicho's toughest landlady. Grey bun, dark kimono, cigarette.

The cigarette lives in her mouth for most expressions (drawn into the head sprite),
with a thin smoke wisp from the ember in idle/talk.
Extras: smoke (inhale -> take the cigarette out -> exhale puffs, loops ~2 s),
        kick (p 0..1: chamber -> huge front kick -> hold; the rent-collection kick).
Extra exprs: exhale (no cigarette, 'o' mouth), determined, sleep.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import step_frame, clamp, lerp, ease_out, ease_in, ease_out_back, ANIM_FPS
from engine.gfx import INK, stamp_line, rect, pset, shade, ascii_sprite
from chars import register
from chars.rig import (ChibiDef, POSES, EXPR_FALLBACK, default_params, compose, _rotate_about, _draw_leg,
                       OX, OY, CW, CH, pose_idle, pose_talk, pose_sit, pose_kneel, _blink)

# ------------------------------------------------------------------ head
HEAD_PAL = {
    "o": INK,
    "H": (214, 214, 224),   # grey hair light
    "h": (164, 164, 180),   # hair mid
    "d": (116, 114, 134),   # hair shade
    "S": (250, 212, 184),   # skin
    "s": (216, 164, 140),   # skin shade / wrinkles
    "E": (60, 46, 58),      # eyes
    "w": (255, 255, 255),
    "m": (150, 50, 64),     # dark lipstick
    "r": (220, 110, 120),
    "b": (240, 150, 150),
    "T": (120, 200, 255),
    "B": (80, 120, 220),
    "k": (140, 90, 60),     # kanzashi pin
}

BASE = [
    "......oooooo......",   # 0
    "....ooHHHHHhoo....",   # 1
    "...oHHHhHHHHhhho..",   # 2
    "..oHHHhHHHHhhhhho.",   # 3
    ".oHHHhHHHHhhhhhhdo",   # 4 combed-back streaks
    ".odHhHHHHhhhhhhhdo",   # 5
    "odHhHHHhhhhhhhhhdo",   # 6
    "odHhhhhhSSSSShhhdo",   # 7 hairline
    "odhhSSSSSSSSSSShdo",   # 8
    "odhSSsSSsSSSsSSSso",   # 9 forehead creases
    "odhSSooSSSSSooSSso",   # 10 stern brows
    "odhSoooSSSSoooSSso",   # 11 heavy lids
    ".ohSwESSSSSSwESSso",   # 12 narrow eyes
    ".osSsSSSSSSSsSSso.",   # 13 eye bags
    "..osSsSSSSmmSsso..",   # 14 lips + smile lines
    "...oosSSSSSSSsoo..",   # 15
    ".....ooooooooo....",   # 16
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
    "blink": _head(r11="odhSSSSSSSSSSSSSso", r12=".ohSoooSSSSoooSSso"),
    "talk": _head(r14="..osSSSSSSooSSso..", r15="...oosSSSSmmSsoo.."),
    "angry": _head(r10="odhSSSoSSSSoSSSSso", r11="odhSoooSSSSoooSSso",
                   r12=".ohSSEwSSSSSSEwSso", r14="..osSSSSSoooSSso.."),
    "shout": _head(r10="odhSSSoSSSSoSSSSso", r11="odhSoooSSSSoooSSso",
                   r12=".ohSSEwSSSSSSEwSso", r13=".osSsSSSSooooSSso.",
                   r14="..osSSSSSomrmoSo..", r15="...oosSSSSoooSoo.."),
    "shock": _head(r10="odhSSooSSSSSooSSso", r11="odhSoooSSSSoooSSso",
                   r12=".ohSowoSSSSowoSSso", r13=".osSoooSSSSoooSso.",
                   r14="..osSSSSSSooSSso..", r15="...oosSSSSmmSsoo.."),
    "happy": _head(r11="odhSSoSSSSSSoSSSso", r12=".ohSoSoSSSSoSoSSso",
                   r14="..osSSSSSmSSmSso..", r15="...oosSSSSmmSsoo.."),
    "sad": _head(r10="odhSSSSoSSSoSSSSso", r12=".ohSwESSSSSSwESSso",
                 r14="..osSSSSSSSSSSso..", r15="...oosSSSSmmSsoo.."),
    "cry": _head(r11="odhSoooSSSSoooSSso", r12=".ohSTTSSSSSSTTSSso",
                 r13=".osSTSSSSSSSTSSso.", r14="..osSTSSSmmSTSso.."),
    "hurt": _head(r11="odhSoSoSSSSoSoSSso", r12=".ohSSoSSSSSSoSSSso",
                  r13=".osSoSoSSSSoSoSso.", r14="..osSSSSSSooSSso.."),
    "smug": _head(r11="odhSSSSSSSSSSSSSso", r12=".ohSoooSSSSoooSSso",
                  r14="..osSSSSSSSSmSso..", r15="...oosSSSSmmmsoo.."),
    "exhale": _head(r14="..osSSSSSSooSSso..", r15="...oosSSSSooSsoo.."),
    "determined": _head(r10="odhSSSoSSSSoSSSSso", r14="..osSSSSSmmmSSso.."),
    "sleep": _head(r11="odhSSSSSSSSSSSSSso", r12=".ohSoooSSSSoooSSso",
                   r14="..osSSSSSSSSSSso.."),
    "gloom": _head(r7="odHhhhhhSBSSBhhhdo", r8="odhhSSBSSBSSBSShdo"),
}
NO_CIG = {"shout", "shock", "exhale", "cry", "hurt", "sleep"}

BUN = ascii_sprite("""
..ooooo..
.oHHHhho.
oHHHhhhdo
oHhhhhddo
.ohhhddo.
..ooooo..
""", HEAD_PAL)

CIG = ascii_sprite("""
...oooo.
wwwwwFYo
...oooo.
""", {"o": INK, "w": (250, 250, 250), "F": (255, 110, 40), "Y": (255, 214, 110)})

FACE_OX, FACE_OY = 3, 1          # face position inside the composite head canvas
CIG_POS = (FACE_OX + 12, FACE_OY + 13)
EMBER = (CIG_POS[0] + 6, CIG_POS[1] + 1)   # ember pixel in head-canvas coords
HEAD_W, HEAD_H = FACE_OX + 18 + 5, FACE_OY + 17

# ------------------------------------------------------------------ torso
TORSO_PAL = {
    "o": INK,
    "K": (104, 76, 128),    # dark purple kimono light
    "k": (76, 52, 98),      # kimono mid
    "q": (52, 34, 70),      # kimono shade
    "W": (236, 232, 240),   # under-collar
    "S": (250, 212, 184),
    "O": (190, 170, 126),   # obi (muted gold)
    "l": (222, 206, 160),   # obi light
    "n": (140, 120, 86),    # obi shade
    "f": (136, 104, 160),   # faint pattern
}

TORSO = """
...oooooo...
..oKWSSWko..
.oKKKWSWkkqo
.oKKKKWkkkqo
.oKfKKKWkkqo
.oOlOOOOOnno
.oOlOOOOOOno
.oOlOOOOOnno
.oKkkkWkkkqo
.okkfkWkkqqo
.okkkkWkkfqo
.okkkkWkqqqo
..oooooooo..
"""

TORSO_SHORT = """
...oooooo...
..oKWSSWko..
.oKKKWSWkkqo
.oKKKKWkkkqo
.oKfKKKWkkqo
.oOlOOOOOnno
.oOlOOOOOOno
.oOlOOOOOnno
.oKkkkWkkkqo
.okkkkWkqqqo
..oooooooo..
"""

KIMONO = (76, 52, 98)
KIMONO_B = (60, 40, 80)
TABI = (246, 244, 244)
_SHOE_KEY = (239, 7, 237)


def _feet(a):
    rgb = a[..., :3]
    for key, cloth, tabi in ((_SHOE_KEY, KIMONO, TABI),
                             (shade(_SHOE_KEY, 0.8), KIMONO_B, shade(TABI, 0.86))):
        m = (rgb == np.array(key, np.uint8)).all(-1) & (a[..., 3] > 0)
        if not m.any():
            continue
        below = np.zeros_like(m)
        below[:-1] = m[1:]
        rgb[m] = cloth
        rgb[m & ~below] = tabi
    return a


# ------------------------------------------------------------------ props
SMOKE = [(226, 226, 234, 255), (196, 196, 210, 255), (160, 160, 178, 255)]


def _wisp_prop(img, ctx):
    """Thin smoke wisp curling up from the cigarette ember."""
    pp = ctx["params"]
    if pp["expr"] in NO_CIG or pp["rot"]:
        return
    hx, hy, hw, hh = ctx["head"]
    ex, ey = int(hx) + EMBER[0], int(hy) + EMBER[1]
    f = step_frame(ctx["t"], 8)
    for i in range(5):
        k = (f + i) % 10
        y = ey - 1 - k
        x = ex + int(round(math.sin((k + f * 0.3) * 0.9) * 1.2))
        if k < 7:
            pset(img, x, y, SMOKE[min(2, k // 3)])


def _puff(img, x, y, r, col):
    d = ImageDraw.Draw(img)
    d.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=(120, 120, 140, 255))


def _exhale_prop(img, ctx):
    ph = ctx["params"].get("_ph", 0)
    hx, hy, hw, hh = ctx["head"]
    mx, my = hx + FACE_OX + 12, hy + FACE_OY + 14
    if ph > 0.45:
        k = (ph - 0.45) / 0.55
        for i in range(3):
            kk = clamp(k * 1.6 - i * 0.3)
            if kk <= 0 or kk >= 1:
                continue
            x = mx + 3 + kk * (8 + i * 3)
            y = my - kk * (9 + i * 4)
            _puff(img, x, y, 1 + kk * 3, SMOKE[min(2, int(kk * 3))])
    # cigarette held between the fingers
    hand = ctx["hand_f"]
    if hand and ph > 0.4:
        x, y = int(round(hand[0])), int(round(hand[1]))
        rect(img, x, y - 3, 5, 3, INK)
        rect(img, x + 1, y - 2, 3, 1, (250, 250, 250))
        pset(img, x + 4, y - 2, (255, 110, 40, 255))
        pset(img, x + 5, y - 4, SMOKE[1])


def _kick_leg(img, ctx):
    pp = ctx["params"]
    d = ctx["def"]
    k = pp["_kick"]
    hx, hy = ctx["hip"]
    _draw_leg(img, d, (hx - 1, hy), (hx - 2, OY - 1 + pp["dy"]), back=True)
    if k < 0.35:      # chamber: knee up
        kk = k / 0.35
        knee = (hx + 2 + 3 * kk, hy + 4 - 5 * kk)
        foot = (knee[0] - 1, knee[1] + 4)
        _draw_leg(img, d, (hx + 1, hy), foot)
    else:
        kk = clamp((k - 0.35) / 0.2)
        L = d.leg_len * 1.5
        ang = math.radians(lerp(-40, 28, kk))
        foot = (hx + 1 + math.cos(ang) * L, hy - math.sin(ang) * L)
        _draw_leg(img, d, (hx + 1, hy), foot)
        if 0.3 < kk and k < 0.85:
            # whoosh arc behind the foot
            dr = ImageDraw.Draw(img)
            r = L + 3
            dr.arc([hx + 1 - r, hy - r, hx + 1 + r, hy + r], start=-22, end=50,
                   fill=(255, 255, 255, 230), width=2)
            r2 = r - 3
            dr.arc([hx + 1 - r2, hy - r2, hx + 1 + r2, hy + r2], start=-10, end=35,
                   fill=(220, 230, 255, 170))


# ------------------------------------------------------------------ poses
def pose_idle_o(pp, t, p, d):
    pose_idle(pp, t, p, d)
    pp["arm_f"] = 20 + (2 if step_frame(t, 4, 4) in (1, 2) else 0)
    pp["arm_b"] = -25
    pp["props"] = [_wisp_prop]


def pose_talk_o(pp, t, p, d):
    pose_talk(pp, t, p, d)
    f = step_frame(t, 8)
    pp["expr"] = "talk" if f % 2 == 0 else "normal"
    pp["props"] = [_wisp_prop]


def pose_smoke(pp, t, p, d):
    pose_idle(pp, t, p, d)
    ph = (t % 2.0) / 2.0
    pp["_ph"] = ph
    if ph < 0.4:
        pp["arm_f"] = 158
        pp["expr"] = "blink" if ph > 0.15 else "normal"
    else:
        pp["arm_f"] = 105 if ph < 0.5 else 100
        pp["expr"] = "exhale" if ph < 0.85 else "smug"
    pp["arm_b"] = -20
    pp["props"] = [_exhale_prop]


def pose_kick_o(pp, t, p, d):
    k = clamp(p)
    pp["_kick"] = k
    pp["legs"] = "custom"
    pp["torso"] = "short"
    pp["arm_f"] = 120 if k > 0.35 else 60
    pp["arm_b"] = -70 if k > 0.35 else -20
    pp["lean"] = -3 if k > 0.35 else -1
    pp["expr"] = "shout" if 0.3 < k < 0.8 else "angry"
    pp["props"] = [_kick_leg]


def pose_sit_o(pp, t, p, d):
    pose_sit(pp, t, p, d)
    pp["torso"] = "short"
    pp["props"] = [_wisp_prop]


def pose_kneel_o(pp, t, p, d):
    pose_kneel(pp, t, p, d)
    pp["torso"] = "short"


class OtoseDef(ChibiDef):
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
            face = ascii_sprite(self.heads_art[e], self.head_pal)
            s = Image.new("RGBA", (HEAD_W, HEAD_H), (0, 0, 0, 0))
            s.alpha_composite(BUN, (0, 0))
            # kanzashi pin through the bun
            px = s.load()
            for i in range(4):
                px[1 + i, 4 - i] = (140, 90, 60, 255)
            s.alpha_composite(face, (FACE_OX, FACE_OY))
            if e not in NO_CIG:
                s.alpha_composite(CIG, CIG_POS)
            self._heads[e] = s
        return s

    def render(self, pose="idle", t=0.0, p=None, expr=None, **kw):
        fn = self.poses.get(pose) or POSES.get(pose) or POSES["idle"]
        pp = default_params()
        pp["_ph"] = 0
        pp["_kick"] = 0
        fn(pp, t, p if p is not None else (t % 1.0), self)
        pp.update({k: v for k, v in kw.items() if k in pp})
        if expr is not None:
            pp["expr"] = expr
        img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        ctx = compose(self, img, pp, t)
        for prop in pp["props"]:
            prop(img, ctx)
        img = Image.fromarray(_feet(np.array(img)), "RGBA")
        ax, ay = OX, OY
        if pp["rot"]:
            img, ax, ay = _rotate_about(img, pp["rot"], OX, OY - 14, OX, OY)
        return img, ax, ay


OTOSE = register(OtoseDef(
    id="otose", name="登势", color=(128, 84, 156), voice=0.92,
    heads=HEADS, head_pal=HEAD_PAL, head_anchor=(FACE_OX + 9, FACE_OY + 16),
    torso={"default": TORSO, "short": TORSO_SHORT}, torso_pal=TORSO_PAL,
    neck=(6, 2), hip=(6, 8), shoulder_f=(9, 3), shoulder_b=(2, 3),
    arm_len=6, arm_w=2, sleeve_f=(104, 76, 128), sleeve_b=(64, 44, 84), sleeve_frac=0.7,
    hand=(250, 212, 184),
    leg_len=5, leg_w=3, leg_gap=3, pants=KIMONO, shoes=_SHOE_KEY, shoe_h=1,
    weapon=None,
    poses={"idle": pose_idle_o, "talk": pose_talk_o, "smoke": pose_smoke, "kick": pose_kick_o,
           "sit": pose_sit_o, "kneel": pose_kneel_o},
    desc="『登势酒馆』老板娘兼万事屋房东。嘴上叼着烟，催房租时一脚能把银时踹出窗外。",
))
