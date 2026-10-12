"""夜王凤仙 Housen — King of the Night, ruler of Yoshiwara. HUGE old Yato.

~48 px tall (vs 34 for normal adults): bigger head/torso art, longer & thicker
limbs.  Long white hair swept back and flowing down his back, bushy white
brows, big white mustache + beard, pale skin, black cloak over a maroon robe,
dark wine umbrella.
Extra poses: punch (overridden: huge haymaker with impact streaks),
crumble (kneels in the sunlight, reaching up; p 0..0.35 = dust flaking off,
p 0.35..1 = body dissolves top-down into drifting dust).
Extra expr: peace (eyes closed, faint smile - "the sun is so warm").
"""
import math

import numpy as np
from PIL import Image

from engine.core import step_frame, clamp, lerp, ease_out, ease_out_back, ease_in_out, rng
from engine.gfx import INK, stamp_line
from chars import register
from chars.rig import ChibiDef, POSES, OX, OY, _draw_leg

# ------------------------------------------------------------------ palette
HEAD_PAL = {
    "o": INK,
    "H": (250, 250, 252),   # white hair
    "h": (210, 212, 228),   # hair mid
    "d": (152, 154, 180),   # hair shade
    "W": (244, 242, 236),   # beard / brows
    "V": (204, 200, 202),   # beard mid
    "v": (156, 150, 162),   # beard shade
    "S": (230, 196, 176),   # pale old skin
    "s": (192, 150, 136),   # skin shade / wrinkles
    "x": (120, 84, 96),     # deep eye sockets
    "E": (150, 210, 255),   # Yato blue glare
    "w": (255, 255, 255),
    "m": (110, 36, 50),     # mouth
    "b": (240, 150, 150),
    "T": (120, 200, 255),
}

# 23 rows x 20, 3/4 view facing right: swept-back hair on the left, face on the
# right, long beard hanging over the chest (head_anchor = jaw at row 19).
BASE = [
    ".....ooooooooo......",   # 0
    "...ooHHHHHHHHHoo....",   # 1
    "..oHHHHhhHHHHHHHo...",   # 2
    ".oHHhhHHHHHhhhHHHo..",   # 3
    "odHhHHHHhhhHHHHHHHo.",   # 4
    "odhHHHhhHHHHHHhhHHHo",   # 5  swept-back strands
    "odhHhHHHHHHhhhHHHHHo",   # 6
    "odhhHHHhhdddddddhHHo",   # 7  receding hairline
    "odhhHHdSSSSSSSSSSdHo",   # 8  forehead
    "odhhHdSSsSSSsSSSSSdo",   # 9  wrinkles
    "odhhHdWWWSSSSSSWWWWo",   # 10 bushy brows (outer ends high)
    "odhhHdSxWWWsSsWWWxSo",   # 11 (inner ends low)
    ".odhhdSxwEoxsxwEoxSo",   # 12 glaring eyes, frown crease
    ".odhhdSSSSSSsSSSSSSo",   # 13 nose
    ".odhhdSSvWWsssWWvSSo",   # 14 mustache
    "..odhdvWWWWWWWWWWWvo",   # 15
    "..odhoWWVVvmmvVVWWo.",   # 16 mouth in the beard
    "...odoVWWWWWWWWWWVo.",   # 17
    "....ooVWWWWWWWWWVo..",   # 18
    "......oVWWWWWWWVo...",   # 19 jaw level (anchor)
    ".......oVWWWWWVo....",   # 20 beard over the chest
    "........oVWWWVo.....",   # 21
    ".........ooooo......",   # 22
]
for _i, _r in enumerate(BASE):
    assert len(_r) == 20, (_i, _r, len(_r))


def _head(**rows):
    r = list(BASE)
    for k, v in rows.items():
        i = int(k[1:])
        assert len(v) == len(BASE[i]), (k, v, len(v))
        r[i] = v
    return "\n".join(r)


HEADS = {
    "normal": _head(),
    "blink": _head(r12=".odhhdSxoooxsxoooxSo"),
    "talk": _head(r16="..odhoWWVmoooomVWWo.", r17="...odoVWWmmmmWWWWVo."),
    "angry": _head(r10="odhhHdWWSSSSSSSSSWWo", r11="odhhHdSWWWWsSsWWWWSo",
                   r12=".odhhdSxwEoSSSwEoxSo"),
    "shout": _head(r10="odhhHdWWSSSSSSSSSWWo", r11="odhhHdSWWWWsSsWWWWSo",
                   r16="..odhoWWoooooooWWo..", r17="...odoVWowwwwwoWVo..",
                   r18="....ooVWoooooooVo..."),
    "shock": _head(r10="odhhHdSWWWSSSSSWWWSo", r11="odhhHdSSSSSsSsSSSSSo",
                   r12=".odhhdSowEoSSowEoSSo", r16="..odhoWWVWoooWVWWo..",
                   r17="...odoVWWWommoWWWVo."),
    # a king's menacing grin
    "happy": _head(r12=".odhhdSxoooSSSoooxSo", r16="..odhoWmwwwwwwmWWo..",
                   r17="...odoVWWmmmmmmWWVo."),
    "smug": _head(r12=".odhhdSxwEoSSSoooxSo", r16="..odhoWWVVmmmmmmWWo.",
                  r17="...odoVWWWWWWWmWWVo."),
    "sad": _head(r10="odhhHdSSSSSSSSSSSSSo", r11="odhhHdSSWWWsSsWWWSSo",
                 r12=".odhhdSSwEoSSSwEoSSo"),
    "cry": _head(r10="odhhHdSSSSSSSSSSSSSo", r11="odhhHdSSWWWsSsWWWSSo",
                 r12=".odhhdSTTTSSSSTTTSSo", r13=".odhhdSSTSSSsSSTSSSo"),
    "hurt": _head(r11="odhhHdSSWWWsSsWWWSSo", r12=".odhhdSoSoSSSSoSoSSo",
                  r13=".odhhdSSoSSSsSSoSSSo", r16="..odhoWWVWoooWVWWo.."),
    # "the sun... is this warm?" - eyes closed, peaceful
    "peace": _head(r10="odhhHdSSSSSSSSSSSSSo", r11="odhhHdSWWWSsSsWWWSSo",
                   r12=".odhhdSSoooSSSoooSSo", r16="..odhoWWVWmmmmWVWWo."),
}
HEADS["determined"] = HEADS["angry"]
HEADS["sleep"] = HEADS["peace"]

TORSO_PAL = {
    "o": INK,
    "K": (48, 44, 62),      # black cloak
    "k": (30, 28, 40),      # cloak shade
    "L": (86, 80, 108),     # cloak highlight
    "R": (126, 42, 62),     # maroon robe
    "r": (86, 28, 44),      # robe shade
    "G": (150, 140, 120),   # obi
    "g": (104, 96, 84),     # obi shade
    "H": (250, 250, 252),   # hair down the back
    "h": (210, 212, 228),
    "d": (152, 154, 180),
}

# 24 wide x 22 tall.  neck (12,2), hip (12,16); cloak hangs 5 px below the hip.
# White hair cascades down the back (cols 0-4).
TORSO = [
    "oHHHhdooooooooo.........",   # 0  long white hair continues from the head
    "oHHhhdoooKRRRRKooo......",   # 1  collar, maroon V at the throat
    "oHHhhdoKKKKoRRoKKKooo...",   # 2
    "oHHhhdKLKKKKoRoKKKKKKoo.",   # 3
    "oHHhhdLLKKKKoRRoKKKKKKko",   # 4  broad shoulders
    "oHHhhdLKKKKKoRRoKKKKKkko",   # 5
    "oHHhhdLKKKKKoRRoKKKKKkko",   # 6
    "oHHhhdLKKKKKoRRRoKKKKkko",   # 7
    ".oHhhdLKKKKKoRRRoKKKkkko",   # 8
    ".oHhhdLKKKKKoRRRoKKKkkko",   # 9
    "..oHhdLKKKKKoRRrroKKkkko",   # 10
    "..oHhdLKKKKKoRRrroKKkkko",   # 11
    "...ohoLKKKKoGGGGGGoKkkko",   # 12 obi
    "....ooLKKKKogggggoKKkkko",   # 13
    ".....oLKKKKoRRrroKKKkkko",   # 14
    ".....oLKKKKoRRrroKKKkkko",   # 15
    "....oLLKKKKoRRrroKKKkkko",   # 16 hip
    "...oLLKKKKKoRrrroKKKkkko",   # 17 cloak flares out
    "...oLKKKKKKoRrrroKKKkkko",   # 18
    "..oLKKKKKKKoRrrroKKkkkko",   # 19
    "..okKKKKKKoorrrrooKkkkko",   # 20
    "...oooooooo.oooo.ooooooo",   # 21
]
for _i, _r in enumerate(TORSO):
    assert len(_r) == 24, (_i, _r, len(_r))
TORSO = "\n".join(TORSO)

# ------------------------------------------------------------------ umbrella
UMB = {  # rig umbrella colours -> Housen's dark wine parasol
    (150, 70, 170): (104, 46, 70),
    (90, 40, 60): (40, 30, 36),
    (210, 210, 220): (220, 216, 226),
    (90, 60, 70): (60, 44, 52),
}


def _recolor(img, table):
    a = np.array(img)
    rgb = a[..., :3]
    vis = a[..., 3] > 0
    for src, dst in table.items():
        m = vis & (rgb[..., 0] == src[0]) & (rgb[..., 1] == src[1]) & (rgb[..., 2] == src[2])
        if m.any():
            rgb[m] = dst
    return Image.fromarray(a, "RGBA")


def sheathed_umbrella(img, torso_xy, torso_size):
    """Huge closed parasol through the sash: handle forward, canopy behind."""
    tx, ty = torso_xy
    h, tip = (tx + 25, ty + 11), (tx - 5, ty + 18)
    stamp_line(img, h, tip, 6, INK)
    stamp_line(img, (tx + 21, ty + 12), (tx - 3, ty + 17.5), 4, UMB[(150, 70, 170)])
    stamp_line(img, (tx + 21, ty + 11.2), (tx - 3, ty + 16.8), 1, (150, 80, 104))
    stamp_line(img, h, (tx + 22, ty + 11.6), 3, (40, 30, 36))
    stamp_line(img, (tx - 3, ty + 17.5), (tx - 4, ty + 17.8), 2, (220, 216, 226))


class HousenDef(ChibiDef):
    PAD = 18      # extra room: 24 px umbrella in thrust/ready + 50 px body tumbling in 'fly'

    def render(self, pose="idle", t=0.0, p=None, expr=None, **kw):
        if pose == "crumble" and p is None:
            p = 0.2          # looping use without p: just the flaking hint
        from chars.rig import default_params, compose, CW, CH
        fn = self.poses.get(pose) or POSES.get(pose) or POSES["idle"]
        pp = default_params()
        fn(pp, t, p if p is not None else (t % 1.0), self)
        pp.update({k: v for k, v in kw.items() if k in pp})
        if expr is not None:
            pp["expr"] = expr
        # compose() places parts absolutely from (OX, OY), so a canvas that is
        # larger to the right / bottom just gives the umbrella tip room.
        # (crumble's dust prop works on an exact CW x CH canvas.)
        ext = 0 if pose == "crumble" else self.PAD
        img = Image.new("RGBA", (CW + ext, CH + ext), (0, 0, 0, 0))
        ctx = compose(self, img, pp, t)
        for prop in pp["props"]:
            prop(img, ctx)
        pad = self.PAD
        big = Image.new("RGBA", (CW + 2 * pad, CH + 2 * pad), (0, 0, 0, 0))
        big.paste(img, (pad, pad))
        ax, ay = OX + pad, OY + pad
        if pp["rot"]:
            big = big.rotate(pp["rot"], resample=Image.NEAREST, center=(ax, ay - 14))
        return _recolor(big, UMB), ax, ay


# ------------------------------------------------------------------ poses
def pose_idle(pp, t, p, d):
    """Slow, heavy breathing; arms hanging like a mountain."""
    f = step_frame(t, 3, 4)
    pp["bob"] = -1 if f in (1, 2) else 0
    pp["arm_f"] = 8 + (2 if f in (1, 2) else 0)
    pp["arm_b"] = -8
    pp["expr"] = "blink" if (t % 3.7) < 0.12 else "normal"


def _impact_prop(img, ctx, k):
    """Speed streaks behind the fist + a small shock ring in front."""
    if not ctx["hand_f"] or k <= 0:
        return
    x, y = ctx["hand_f"]
    for i, dy in enumerate((-3, 0, 3)):
        ln = 6 + 3 * (i % 2)
        stamp_line(img, (x - 4 - ln, y + dy), (x - 5, y + dy), 1, (255, 255, 255))
    r = 2 + 5 * k
    a = int(255 * (1 - k))
    if a > 30:
        for i in range(10):
            ang = i / 10 * 2 * math.pi
            px, py = x + 4 + math.cos(ang) * r * 0.6, y + math.sin(ang) * r
            stamp_line(img, (px, py), (px, py), 1, (255, 240, 200, a))


def pose_punch(pp, t, p, d):
    """Housen's haymaker. p 0-0.3 wind-up, 0.3-0.45 strike, then hold."""
    if p < 0.3:
        k = ease_out(p / 0.3)
        pp["arm_f"] = lerp(20, -50, k)
        pp["arm_b"] = lerp(-10, 60, k)
        pp["lean"] = int(lerp(0, -2, k))
        pp["legs"] = "spread"
        pp["expr"] = "angry"
    else:
        k = ease_out_back(clamp((p - 0.3) / 0.15))
        pp["arm_f"] = lerp(-50, 92, clamp(k))
        pp["arm_b"] = -40
        pp["lean"] = int(lerp(-2, 5, clamp(k)))
        pp["legs"] = "lunge"
        pp["expr"] = "shout"
        kk = clamp((p - 0.4) / 0.4)
        if p > 0.38:
            pp["props"] = [lambda img, ctx, kk=kk: _impact_prop(img, ctx, kk)]


# -- crumble -----------------------------------------------------------------
_NOISE = None


def _noise():
    global _NOISE
    if _NOISE is None:
        r = rng("housen", "crumble")
        _NOISE = np.array([[r.random() for _ in range(96)] for _ in range(96)], np.float32)
    return _NOISE


_DUST = ((226, 220, 210), (186, 180, 176), (246, 242, 232), (150, 144, 148))
_ASH = np.array([176, 170, 168], np.float32)


def _crumble_prop(img, ctx, p, t):
    a = np.array(img)
    alpha = a[..., 3]
    ys, xs = np.nonzero(alpha)
    if len(ys) == 0:
        return
    top, bot = int(ys.min()), int(ys.max())
    hgt = max(1, bot - top)
    nz = _noise()
    # the sun dries him out: colours drain toward ash grey
    ash = 0.12 + 0.5 * clamp(p / 0.6)
    vis = alpha > 0
    rgb = a[..., :3].astype(np.float32)
    rgb[vis] = rgb[vis] * (1 - ash) + _ASH * ash
    a[..., :3] = rgb.astype(np.uint8)
    # dissolve top-down (p > 0.35)
    k = (p - 0.35) / 0.65 * 1.15 if p > 0.35 else -1.0
    rel = (np.arange(96, dtype=np.float32)[:, None] - top) / hgt   # 0 top .. 1 bottom
    thr = 0.55 * nz + 0.45 * rel
    if k > 0:
        gone = vis & (thr < k)
        edge = vis & (thr >= k) & (thr < k + 0.08)
        g = a[edge, :3].astype(np.float32)
        a[edge, :3] = (g * 0.3 + np.array([214, 208, 200]) * 0.7).astype(np.uint8)
        a[gone, 3] = 0
    out = Image.fromarray(a, "RGBA").copy()
    px = out.load()

    def dot(x, y, c, al, big=False):
        ix, iy = int(x), int(y)
        for dx, dy in (((0, 0), (1, 0)) if big else ((0, 0),)):
            if 0 <= ix + dx < 96 and 0 <= iy + dy < 96:
                px[ix + dx, iy + dy] = c + (al,)

    # flaking: flecks peel off the upper body and drift up-right in the warm air
    r = rng("housen", "flake")
    upper = ys < top + hgt * 0.7
    uy, ux = ys[upper], xs[upper]
    if len(uy):
        n_flake = 16 + int(30 * clamp(p / 0.35))
        for i in range(n_flake):
            j = r.randrange(len(uy))
            sy, sx = int(uy[j]), int(ux[j])
            if k > 0 and thr[sy, sx] < k:
                continue
            life = (t * (0.5 + r.random() * 0.5) + r.random()) % 1.0
            fx = sx + life * (8 + r.random() * 12)
            fy = sy - life * (10 + r.random() * 14) + math.sin(life * 6 + i) * 1.5
            dot(fx, fy, _DUST[i % len(_DUST)], int(255 * (1 - life * 0.85)), big=(i % 3 == 0))
    # dust from the dissolved pixels
    if k > 0:
        gy, gx = np.nonzero(vis & (thr < k))
        for j in range(0, len(gy), 3):
            y0, x0 = int(gy[j]), int(gx[j])
            age = (k - thr[y0, x0]) * 2.2
            if age >= 1:
                continue
            seed = nz[(y0 * 7) % 96, (x0 * 13) % 96]
            fx = x0 + age * (10 + seed * 14)
            fy = y0 - age * (6 + seed * 16) + math.sin(age * 9 + seed * 20) * 1.5
            dot(fx, fy, _DUST[(y0 + x0) % len(_DUST)], int(255 * (1 - age)), big=(j % 9 == 0))
    img.paste(out, (0, 0))


def _kneel_robe(img, ctx):
    """Front knee under the robe for the legless kneel."""
    hx, hy = ctx["hip"]
    base = OY - 1
    pts = [(hx + 4, hy - 1), (hx + 13, base - 5), (hx + 15, base - 2), (hx + 14, base), (hx + 4, base)]
    from PIL import ImageDraw
    dr = ImageDraw.Draw(img)
    dr.polygon(pts, fill=(48, 44, 62), outline=INK)
    dr.line([(hx + 6, hy + 2), (hx + 12, base - 4)], fill=(86, 80, 108))


def pose_crumble(pp, t, p, d):
    """Kneels in the sunlight, face up, reaching for the sky, crumbling to dust.
    p 0..0.35: turns ashen, dust flakes off (hint);  p 0.35..1: dissolves
    top-down into drifting dust (gone at p=1).  Pass p explicitly."""
    pp["legs"] = "none"
    pp["dy"] = -5
    pp["arm_f"] = 158
    pp["arm_b"] = 25
    pp["lean"] = -1
    pp["head_dx"] = -1
    pp["expr"] = "peace"
    pp["sheathed"] = False
    pp["props"] = [_kneel_robe, lambda img, ctx, p=p, t=t: _crumble_prop(img, ctx, p, t)]


def pose_walk(pp, t, p, d):
    """Heavy, long strides."""
    POSES["walk"](pp, t, p, d)
    pp["stride"], pp["lift"] = 4.0, 2.5
    pp["expr"] = "normal"


def pose_run(pp, t, p, d):
    POSES["run"](pp, t, p, d)
    pp["stride"], pp["lift"] = 6.0, 4.0
    pp["expr"] = "angry"


def pose_kneel(pp, t, p, d):
    """Down on one knee, panting (the generic rig kneel reads as a wide stance
    with his 13 px legs): same robe-covered kneel as crumble."""
    f = step_frame(t, 3, 4)
    pp["legs"] = "none"
    pp["dy"] = -5
    pp["bob"] = -1 if f in (1, 2) else 0
    pp["arm_f"] = 24
    pp["arm_b"] = -12
    pp["lean"] = 1
    pp["head_dy"] = 1
    pp["expr"] = "hurt"
    pp["props"] = [_kneel_robe]


HOUSEN = register(HousenDef(
    id="housen", name="凤仙", color=(156, 56, 80), voice=0.62,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    head_anchor=(12, 19),
    neck=(12, 2), hip=(12, 16), shoulder_f=(18, 5), shoulder_b=(7, 5),
    arm_len=11, arm_w=4, sleeve_f=(48, 44, 62), sleeve_b=(30, 28, 40), sleeve_frac=0.72,
    hand=(236, 210, 194),
    leg_len=13, leg_w=4, leg_gap=7, pants=(40, 36, 52), shoes=(24, 20, 30), shoe_h=3,
    weapon="umbrella", weapon_len=24, sheathed=sheathed_umbrella,
    poses={"idle": pose_idle, "walk": pose_walk, "run": pose_run, "punch": pose_punch,
           "crumble": pose_crumble, "kneel": pose_kneel},
    desc="夜王凤仙，吉原的统治者，最强的夜兔之王。白发白须的巨汉老人，惧怕阳光，最后在阳光中化为尘土。",
))
