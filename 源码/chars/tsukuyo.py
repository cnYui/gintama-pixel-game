"""月咏 Tsukuyo — leader of the Hyakka, 'Death Tayuu' of Yoshiwara.

Blonde hair pinned up in a bun with a kanzashi (bun + pin drawn behind the
head), long side locks, scars on the forehead and cheek, violet eyes, short
black kimono with purple collar/obi, dark leggings.
Weapon `kunai`.  Extra poses: `throw_kunai` (p-driven: fan of 3 kunai wound up
over the shoulder -> whip -> kunai fly off to the right), `smoke` (kiseru to the
lips, smoke puffs).  Extra exprs `blush`, `drunk`, `determined`.
"""
import math

from engine.core import step_frame, clamp, lerp, ease_out, ease_in_out
from engine.gfx import INK, stamp_line, rect
from chars import register
from chars.rig import pose_idle, _blink, draw_weapon
from chars.shouyou import LayeredDef

HAIR_L, HAIR_H, HAIR_M, HAIR_D = (255, 244, 176), (250, 216, 104), (222, 172, 66), (168, 118, 46)
HEAD_PAL = {
    "o": INK,
    "L": HAIR_L,
    "H": HAIR_H,
    "h": HAIR_M,
    "d": HAIR_D,
    "S": (255, 222, 196),
    "s": (236, 178, 150),
    "x": (224, 136, 140),   # scars
    "E": (150, 96, 196),    # violet eyes
    "e": (96, 56, 140),
    "w": (255, 255, 255),
    "m": (186, 70, 90),     # lips
    "b": (252, 150, 160),
    "T": (120, 200, 255),
}

BASE = [
    "......oooooo......",   # 0
    "....ooHHHHHHoo....",   # 1
    "...oHHHLLLHHHHo...",   # 2
    "..oHHLLHHHHHHHHo..",   # 3
    ".odHLHHHHHHHHhHHo.",   # 4
    "odhHHHHHHHHHhHHHHo",   # 5
    "odhHHHHHHHHhHHHHHo",   # 6
    "odhHHHHHHHhHHHHhho",   # 7
    "odhHHHHHSShHHHHHho",   # 8  bangs swept, parted
    "odhHHHHSSxSHHSHhho",   # 9  forehead scar
    "odhHhSSSSSxSSSShho",   # 10
    "odhHSooooSSooooHho",   # 11 lashes
    "odhHSSwEESSwEESHho",   # 12 violet eyes
    "odhhSSSSSSSSSSxhdo",   # 13 cheek scar
    "odhhsSSSSSmSSxshdo",   # 14 small lips
    "odhdosSSSSSSSsohdo",   # 15
    "odhdo.ooooooo.ohdo",   # 16
    "..oo.........ohdo.",   # 17
    "..............oo..",   # 18
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
    "blink": _head(r11="odhHSSSSSSSSSSSHho", r12="odhHSooooSSooooHho"),
    "talk": _head(r14="odhhsSSSSSoSSxshdo", r15="odhdosSSSSmSSsohdo"),
    "determined": _head(r10="odhHhoSSSSxSSSohho", r12="odhHSSwEeSSwEeSHho"),
    "angry": _head(r10="odhHhoSSSSxSSSohho", r11="odhHSSoooSSoooSHho", r12="odhHSSEEwSSEEwSHho",
                   r14="odhhsSSSSmmmSxshdo"),
    "shout": _head(r10="odhHhoSSSSxSSSohho", r11="odhHSSoooSSoooSHho", r12="odhHSSEEwSSEEwSHho",
                   r13="odhhSSSSSooSSSxhdo", r14="odhhsSSSSomoSxshdo", r15="odhdosSSSSooSsohdo"),
    "shock": _head(r11="odhHSSooSSSooSSHho", r12="odhHSowwoSowwoSHho", r13="odhhSSooSSSooSxhdo",
                   r14="odhhsSSSSSoSSxshdo", r15="odhdosSSSSoSSsohdo"),
    "happy": _head(r11="odhHSSSoSSSSoSSHho", r12="odhHSSoSoSSoSoSHho", r13="odhhSbbSSSSbbSxhdo",
                   r14="odhhsSSSSmSmSxshdo", r15="odhdosSSSSmSSsohdo"),
    "blush": _head(r11="odhHSooooSSooooHho", r12="odhHSSSwESSSwESHho", r13="odhhSbbbSSSbbbxhdo",
                   r14="odhhsSSSSSmmSxshdo"),
    "drunk": _head(r10="odhHhSSoSSxSoSShho", r11="odhHSSooSSSSooSHho", r12="odhHSSSSSSSSSSSHho",
                   r13="odhhSbbbSSSbbbxhdo", r14="odhhsSSSSmmmSxshdo", r15="odhdosSSSSSmSsohdo"),
    "sad": _head(r10="odhHhSSoSSxSoSShho", r11="odhHSSooSSSSooSHho", r12="odhHSSwEESSwEESHho",
                 r14="odhhsSSSSSSSSxshdo", r15="odhdosSSSSmmSsohdo"),
    "cry": _head(r10="odhHhSSoSSxSoSShho", r11="odhHSSooSSSSooSHho", r12="odhHSSTTTSSTTTSHho",
                 r13="odhhSSTSSSSTSSxhdo", r14="odhhsSSTSSmSTxshdo", r15="odhdosSTSSSSTsohdo"),
    "hurt": _head(r11="odhHSSoSoSSoSoSHho", r12="odhHSSSoSSSSoSSHho", r13="odhhSSoSoSSoSoxhdo",
                  r14="odhhsSSSSSooSxshdo"),
    "smug": _head(r11="odhHSSSSSSSSSSSHho", r12="odhHSooooSSooooHho", r14="odhhsSSSSSSSmxshdo",
                  r15="odhdosSSSSSmmsohdo"),
    "sleep": _head(r11="odhHSSSSSSSSSSSHho", r12="odhHSSoooSSoooSHho"),
}
HEAD_ANCHOR = (9, 16)

TORSO_PAL = {
    "o": INK,
    "K": (58, 52, 74),      # black kimono
    "k": (40, 36, 54),
    "l": (96, 88, 120),
    "P": (170, 116, 214),   # purple collar
    "V": (136, 82, 178),    # purple obi
    "v": (98, 56, 136),
    "G": (240, 196, 90),    # gold obi cord
}

TORSO = """
....oooooo....
...oKPPPKKo...
...oKKPPKko...
..oKlKKPKkko..
..oKlKKKPkko..
..oKlKKKKkko..
..oVVVGVVVvo..
..oKlKKKKkko..
.oKKlKKKKKkko.
.oKKKKKKKkkko.
.oPKKKKKKkkPo.
..oooooooooo..
"""


def hair_bun(img, ctx):
    """Bun at the back of the head pierced by a kanzashi (drawn behind the head)."""
    from PIL import ImageDraw
    hx, hy, hw, hh = ctx["head"]
    cx, cy = hx, hy + 5
    dr = ImageDraw.Draw(img)
    # kanzashi pin through the bun, sticking out up-back with a bead
    stamp_line(img, (cx + 3, cy + 1), (cx - 6, cy - 4), 3, INK)
    dr.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=INK)
    dr.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=HAIR_M)
    dr.ellipse([cx - 3, cy - 3, cx + 1, cy + 1], fill=HAIR_H)
    stamp_line(img, (cx - 2, cy - 2), (cx - 1, cy - 2), 1, HAIR_L)
    stamp_line(img, (cx - 3, cy + 1), (cx - 1, cy + 3), 1, HAIR_D)
    stamp_line(img, (cx - 1, cy - 1), (cx - 6, cy - 4), 1, (240, 200, 96))
    stamp_line(img, (cx - 6, cy - 4), (cx - 6, cy - 4), 4, INK)
    stamp_line(img, (cx - 6, cy - 4), (cx - 6, cy - 4), 2, (170, 116, 214))
    img.putpixel((int(cx - 7), int(cy - 5)), (220, 180, 240, 255))


# ------------------------------------------------------------------ props & poses
def _arm_to_screen(a):
    """rig arm angle -> screen angle (deg, 0 = right, 90 = up)."""
    r = math.radians(a)
    return math.degrees(math.atan2(-math.cos(r), math.sin(r)))


def _kunai_fan(img, ctx):
    hf = ctx["hand_f"]
    if not hf:
        return
    base = _arm_to_screen(ctx["params"]["arm_f"])
    for da in (-30, 0, 30):
        draw_weapon(img, "kunai", hf, base + da, 8)
    stamp_line(img, hf, hf, 4, INK)
    stamp_line(img, hf, hf, 3, (255, 222, 196))


def _flying_kunai(img, ctx):
    pp = ctx["params"]
    k = pp.get("fly", 0)
    hf = ctx["hand_f"]
    if k <= 0 or not hf:
        return
    x0, y0 = hf
    for i, dy in enumerate((-4, 0, 4)):
        d = 6 + k * 40 - i * 2
        x, y = x0 + d, y0 - 2 + dy * (0.4 + k)
        if x > 92:
            continue
        stamp_line(img, (x - 6, y), (x - 2, y), 1, (220, 226, 240))   # streak
        draw_weapon(img, "kunai", (x, y), 0, 8)


def pose_throw_kunai(pp, t, p, d):
    """Kunai throw. p: 0-0.4 wind-up (fan of 3 kunai over the shoulder),
    0.4-0.55 whip forward, 0.45-1 kunai fly off to the right."""
    pp["expr"] = "determined"
    pp["fly"] = 0
    if p < 0.4:
        k = ease_out(p / 0.4)
        pp["arm_f"] = lerp(60, 150, k)
        pp["arm_b"] = lerp(-10, 60, k)
        pp["lean"] = int(round(lerp(0, -2, k)))
        pp["legs"] = "spread"
        pp["props"] = [_kunai_fan]
    elif p < 0.55:
        k = ease_in_out((p - 0.4) / 0.15)
        pp["arm_f"] = lerp(150, 80, k)
        pp["arm_b"] = lerp(60, -40, k)
        pp["lean"] = int(round(lerp(-2, 3, k)))
        pp["legs"] = "lunge"
        pp["props"] = [_kunai_fan] if k < 0.5 else [_flying_kunai]
        pp["fly"] = 0 if k < 0.5 else (k - 0.5) * 0.3
    else:
        k = (p - 0.55) / 0.45
        pp["arm_f"] = 80
        pp["arm_b"] = -40
        pp["lean"] = 3
        pp["legs"] = "lunge"
        pp["props"] = [_flying_kunai]
        pp["fly"] = 0.15 + k


def _kiseru(img, ctx):
    """Long kiseru pipe from the lips out past the hand, with smoke puffs."""
    hf = ctx["hand_f"]
    if not hf:
        return
    hx, hy, hw, hh = ctx["head"]
    mx, my = hx + 11, hy + 14
    bx, by = hf[0] + 7, hf[1] - 2
    stamp_line(img, (mx, my), (bx, by), 3, INK)
    stamp_line(img, (mx, my), (bx, by), 1, (70, 44, 58))
    stamp_line(img, (mx, my), (mx + 1, my), 1, (236, 200, 96))       # mouthpiece
    stamp_line(img, (bx, by - 1), (bx + 1, by - 1), 4, INK)             # bowl
    stamp_line(img, (bx, by - 1), (bx + 1, by - 1), 2, (236, 200, 96))
    stamp_line(img, (bx + 1, by - 2), (bx + 1, by - 2), 1, (255, 120, 60))
    stamp_line(img, hf, hf, 4, INK)
    stamp_line(img, hf, hf, 3, (255, 222, 196))
    # smoke puffs rising from the bowl (loop 2 s)
    t = ctx["t"]
    for i in range(3):
        u = ((t * 12 // 1) / 12 / 2.0 + i / 3.0) % 1.0
        px = bx + 1 + math.sin(u * 6 + i) * 2 + u * 3
        py = by - 3 - u * 16
        r = 1 + int(u * 3)
        col = (236, 234, 244) if u < 0.6 else (200, 198, 214)
        _puff(img, px, py, r, col)


def _puff(img, x, y, r, col):
    from PIL import ImageDraw
    x, y = int(round(x)), int(round(y))
    ImageDraw.Draw(img).ellipse([x - r, y - r, x + r, y + r], fill=col)
    if r >= 2:
        img.putpixel((x - r + 1, y - r + 1), (255, 255, 255, 255))


def pose_smoke(pp, t, p, d):
    pose_idle(pp, t, p, d)
    f = step_frame(t, 2, 4)
    pp["arm_f"] = 128 if f != 3 else 112
    pp["arm_b"] = 15
    pp["expr"] = "blink" if f == 1 else ("smug" if f == 3 else "normal")
    pp["sheathed"] = False
    pp["props"] = [_kiseru]


def pose_arms_crossed_t(pp, t, p, d):
    f = step_frame(t, 4, 4)
    pp["arm_f"] = 72
    pp["arm_b"] = 62
    pp["bob"] = -1 if f in (1, 2) else 0
    pp["expr"] = "blink" if _blink(t) else "normal"


TSUKUYO = register(LayeredDef(
    id="tsukuyo", name="月咏", color=(128, 76, 176), voice=1.12,
    heads=HEADS, head_pal=HEAD_PAL, head_anchor=HEAD_ANCHOR,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(4, 3),
    arm_len=7, arm_w=2, sleeve_f=(58, 52, 74), sleeve_b=(40, 36, 54), sleeve_frac=0.7,
    hand=(255, 222, 196),
    leg_len=7, leg_w=3, leg_gap=3, pants=(92, 78, 112), shoes=(34, 28, 40),
    weapon="kunai", weapon_len=9, sheathed=None,
    poses={"throw_kunai": pose_throw_kunai, "smoke": pose_smoke, "arms_crossed": pose_arms_crossed_t},
    back_layers=(hair_bun,), portrait_crop=17,
    desc="吉原自警团『百华』首领，人称死神太夫。金发盘髻、脸带伤疤，苦无百发百中，烟管不离手。",
))
