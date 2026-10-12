"""冲田总悟 Okita Sougo — 1st division captain, the sadistic prince.

Sandy light-brown hair with pointed bangs, big red-brown eyes, pretty innocent
face that turns into a sadistic little smirk.
Extra poses: bazooka (aiming on the shoulder; fires at p=0.5 — pass p, or it
loops every second), nap (lying on his back with the red cartoon-eye sleep mask;
grounded: feet anchor = floor, body extends to the right).
Extra exprs: mask, sadist (shadowed smirk).
"""
import math

from PIL import Image

from engine.core import step_frame, clamp, lerp, ease_out
from engine.gfx import INK, stamp_line, rect, pset
from chars import register
from chars.rig import default_params, compose, OX, OY, CW, CH, pose_idle, _blink
from chars.hijikata import (SSGDef, SSG_BODY, SKIN, sheathed_katana, mk_head, katana_on_shoulder,
                            puff, star_glint, ground)

HEAD_PAL = {
    "o": INK,
    "H": (244, 208, 146),   # sandy hair light
    "h": (214, 164, 100),   # sandy light-brown hair
    "d": (160, 110, 66),    # hair shade
    "S": (255, 222, 192),   # fair skin
    "s": (236, 176, 146),   # skin shade
    "E": (150, 44, 40),     # red-brown iris
    "e": (206, 92, 70),     # iris light
    "w": (255, 255, 255),
    "m": (176, 76, 84),     # mouth
    "M": (214, 44, 50),     # sleep-mask red
    "N": (150, 26, 36),     # sleep-mask shade
    "R": (228, 40, 56),
    "b": (250, 156, 156),   # blush
    "T": (120, 200, 255),   # tears
    "G": (150, 120, 150),   # sadist shadow over the eyes
    "B": (80, 120, 220),
}

BASE = [
    "......oooooo......",   # 0
    "....ooHHHHhhoo....",   # 1
    "...oHHHHHhhhhhoo..",   # 2
    "..oHHHhhhhhhhhhho.",   # 3
    ".oHHhhhhhHhhhhhhdo",   # 4
    "oHHhhhhhHhhhhhhhdo",   # 5
    "odHhhhhHhhhhhHhhdo",   # 6
    "odhhhhhhhhhhhhhhdo",   # 7
    "odhhhhhhhhhhhhhhdo",   # 8
    "odhhShhhShhhhShhdo",   # 9  pointed bangs
    "odhSSShSSSShSSShdo",   # 10
    "odhSSoooSSSoooShdo",   # 11 lids
    ".ohSSwEESSSwEEShho",   # 12 big red-brown eyes
    ".ohSSSeeSSSSeeSho.",   # 13
    "..osSSSSSSSmSSso..",   # 14 small innocent mouth
    "...oosSSSSSSSsoo..",   # 15
    ".....ooooooooo....",   # 16
]


def _h(**rows):
    return mk_head(BASE, **rows)


HEADS = {
    "normal": _h(),
    "blink": _h(r11="odhSSSSSSSSSSSShdo", r12=".ohSSoooSSSoooShho", r13=".ohSSSSSSSSSSSSho."),
    "talk": _h(r14="..osSSSSSSooSSso..", r15="...oosSSSSmmSsoo.."),
    "angry": _h(r10="odhSoShSSSShSoShdo",
                r11="odhSSoooSSSoooShdo", r12=".ohSSEEwSSSwEEShho",
                r13=".ohSSSEeSSSSeESho.", r14="..osSSSSSSmmSSso.."),
    "shout": _h(r10="odhSoShSSSShSoShdo", r11="odhSSoooSSSoooShdo",
                r12=".ohSSEEwSSSwEEShho", r13=".ohSSSSSSSoooSSho.",
                r14="..osSSSSSomRmSso..", r15="...oosSSSSoooSoo.."),
    "shock": _h(r11="odhSoooSSSSoooShdo", r12=".ohSowwoSSowwoShho",
                r13=".ohSSooSSSSooSSho.", r14="..osSSSSSSSoSSso.."),
    "happy": _h(r11="odhSSSoSSSSSoSShdo", r12=".ohSSoSoSSSoSoShho",
                r13=".ohSbbSSSSSSbbSho.", r14="..osSSSSSomoSSso.."),
    "sad": _h(r10="odhSSShSoSShoSShdo", r11="odhSSooSSSSSooShdo",
              r14="..osSSSSSSoSoSso.."),
    "cry": _h(r12=".ohSSTTTSSSTTTShho", r13=".ohSSTSSSSSTSSSho.",
              r14="..osSTSSSSoSoTso..", r15="...oosTSSSSSTsoo.."),
    "hurt": _h(r11="odhSoSoSSSSoSoShdo", r12=".ohSSoSSSSSSoSShho",
               r13=".ohSoSoSSSSoSoSho.", r14="..osSSSSSSooSSso.."),
    "smug": _h(r11="odhSSSSSSSSSSSShdo", r12=".ohSSoooSSSoooShho",
               r13=".ohSSSEESSSSEESho.", r14="..osSSSSSSSSmoSo.."),
    "sadist": _h(r10="odhGGGhGGGGhGGGhdo", r11="odhGGGGGGGGGGGGhdo",
                 r12=".ohGGoooGGGoooGhho", r13=".ohSSSEESSSSEESho.",
                 r14="..osSSSSSmmmmoSo.."),
    "sleep": _h(r11="odhSSSSSSSSSSSShdo", r12=".ohSSoooSSSoooShho",
                r13=".ohSSSSSSSSSSSSho."),
    "none": ".",
    # red sleep mask with goofy glaring cartoon eyes drawn on it
    "mask": _h(r9="odhhShhhShhhhShhdo", r10="ooooooooooooooooo.",
               r11="oNMwwwMMMMwwwMMNNo", r12="oNMwoooMMMwoooMNNo",
               r13=".oMwwwMMMMwwwMMMo.", r14="..oooooooooooooo..",
               r15="...oosSSSSmSSsoo.."),
}

# ------------------------------------------------------------------ bazooka
OLIVE = (98, 118, 72)
OLIVE_L = (146, 166, 104)
OLIVE_D = (62, 78, 50)
STEEL = (54, 58, 62)


def _bazooka(img, sx, sy, t, fire_k):
    """Tube lying on the shoulder, pointing right. (sx, sy) = front shoulder."""
    cy = int(sy + 1)
    x0, x1 = int(sx - 15), int(sx + 17)
    rect(img, x0, cy - 3, x1 - x0 + 1, 7, INK)                     # tube outline
    rect(img, x0 + 1, cy - 2, x1 - x0 - 1, 5, OLIVE)
    rect(img, x0 + 1, cy - 2, x1 - x0 - 1, 1, OLIVE_L)
    rect(img, x0 + 1, cy + 2, x1 - x0 - 1, 1, OLIVE_D)
    rect(img, x0 - 2, cy - 4, 4, 9, INK)                           # flared rear end
    rect(img, x0 - 1, cy - 3, 2, 7, STEEL)
    rect(img, x1 - 2, cy - 4, 4, 9, INK)                           # muzzle ring
    rect(img, x1 - 1, cy - 3, 2, 7, STEEL)
    pset(img, x1 - 1, cy - 3, (110, 116, 124))
    rect(img, x0 + 7, cy - 2, 2, 5, (234, 196, 64))                # warning stripe
    rect(img, sx + 8, cy - 6, 4, 4, INK)                           # sight
    rect(img, sx + 9, cy - 5, 2, 2, STEEL)
    rect(img, sx + 4, cy + 2, 3, 4, INK)                           # grip
    rect(img, sx + 5, cy + 3, 1, 2, OLIVE_D)
    # firing: muzzle flash + back blast, then smoke
    if 0 < fire_k < 0.18:
        fx, fy = x1 + 3, cy
        r = 6 if fire_k < 0.09 else 4
        for a in range(8):
            ang = a * math.pi / 4
            L = r if a % 2 == 0 else r * 0.5
            stamp_line(img, (fx, fy), (fx + math.cos(ang) * L, fy + math.sin(ang) * L), 2, (255, 230, 90))
        rect(img, fx - 2, fy - 2, 5, 5, (255, 255, 230))
        puff(img, x0 - 5, cy, 3, (230, 230, 236), (190, 190, 200))
    elif 0.18 <= fire_k < 0.9:
        k = (fire_k - 0.18) / 0.72
        for i in range(3):
            kk = clamp(k * 1.3 - i * 0.15)
            if 0 < kk < 1:
                puff(img, x1 + 4 + kk * 10 + i * 3, cy - kk * 6 - i, 1 + kk * 3)
                puff(img, x0 - 4 - kk * 8, cy - kk * 5 - i, 1 + kk * 2.5, (210, 210, 218), (170, 170, 184))


def pose_bazooka(pp, t, p, d):
    """Aims a bazooka on the shoulder with a sadistic calm; fires at p=0.5
    (muzzle flash, back blast, recoil, smoke). Without p it loops every second."""
    fire_k = (p - 0.5) / 0.5 if p >= 0.5 else -1
    recoil = 0
    if 0 <= fire_k < 0.25:
        recoil = -2 if fire_k < 0.12 else -1
    pp["arm_f"] = 50
    pp["arm_b"] = 60
    pp["legs"] = "spread"
    pp["lean"] = recoil
    pp["dx"] = recoil
    pp["sheathed"] = True
    pp["expr"] = "sadist" if 0 <= fire_k < 0.6 else ("blink" if _blink(t, 2.7) else "smug")
    if p < 0.5:
        pp["bob"] = -1 if step_frame(t, 4, 4) in (1, 2) else 0

    def prop(img, ctx, fk=fire_k):
        sx, sy = ctx["shoulder_f"]
        _bazooka(img, int(sx), int(sy), ctx["t"], fk)
        hx, hy = ctx["hand_f"]
        stamp_line(img, (hx, hy), (hx, hy), 4, INK)
        stamp_line(img, (hx, hy), (hx, hy), 3, SKIN)
    pp["props"] = [prop]


# ------------------------------------------------------------------ nap
def _zz(img, x, y, s, col=(236, 244, 255), sh=(60, 70, 110)):
    """Pixel 'Z' of size s with a 1px drop shadow."""
    x, y = int(x), int(y)
    pts = [(i, 0) for i in range(s)] + [(s - 1 - i, i) for i in range(1, s - 1)] + [(i, s - 1) for i in range(s)]
    for (a, b) in pts:
        pset(img, x + a + 1, y + b + 1, sh)
    for (a, b) in pts:
        pset(img, x + a, y + b, col)


NAP_TILT = 40          # how far the head leans back onto his hands (deg)


def render_nap(d, t, p, expr, kw):
    """Lying on his back (head left, feet right), hands behind the head as a
    pillow, red sleep mask with cartoon eyes, chest rising, zZ floating. Grounded."""
    tilt = kw.get("tilt", NAP_TILT)
    f = step_frame(t, 3, 2)
    pp = default_params()
    pp.update(arm_f=176, arm_b=184, sheathed=False, expr="none", bob=-1 if f else 0)
    body = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    ctx = compose(d, body, pp, t)
    c = (OX, OY - 14)
    body = body.rotate(90, resample=Image.NEAREST, center=c)
    # neck position after the CCW rotation
    nx = ctx["torso"][0] + d.neck[0]
    ny = ctx["torso"][1] + d.neck[1]
    nx, ny = c[0] + (ny - c[1]), c[1] - (nx - c[0])
    head = d.head(expr or "mask")
    hw, hh = head.size
    tmp = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    tmp.alpha_composite(head, (24 - hw // 2, 24 - (hh - 1)))
    tmp = tmp.rotate(tilt, resample=Image.NEAREST, center=(24, 24))
    out = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    out.alpha_composite(body)
    out.alpha_composite(tmp, (int(nx) - 24 - 3, int(ny) - 24 + 1))
    out = ground(out)
    bb = out.getbbox()
    for k in range(3):
        ph = ((t + k * 0.55) % 1.65) / 1.65
        zx = bb[0] + 12 + k * 2 + math.sin(ph * 5 + k) * 1.5 + ph * 6
        zy = bb[1] - 3 - ph * 14
        if ph < 0.9:
            _zz(out, zx, zy, 4 if k % 2 == 0 else 5)
    return out


OKITA = register(SSGDef(
    id="okita", name="冲田", color=(194, 104, 50), voice=0.95,
    heads=HEADS, head_pal=HEAD_PAL, **SSG_BODY,
    sheathed=sheathed_katana,
    poses={"bazooka": pose_bazooka, "shoulder": katana_on_shoulder},
    special={"nap": render_nap},
    desc="真选组一番队队长。浅栗色头发、红褐色大眼的美少年，天使脸孔下是抖S之魂，最爱拿火箭筒轰土方。",
))
