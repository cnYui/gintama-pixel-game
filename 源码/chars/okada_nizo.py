"""冈田似藏 Okada Nizo — blind hitokiri of the Kiheitai, wielder of Benizakura.

Shaved head with blue-grey stubble, blind closed eyes, sly thin grin, dark
charcoal kimono. Weapon `benizakura` (red demon blade).
Extra pose `benizakura`: holds the red blade low while living red tendrils wrap
and pulse up his arm onto his body. kw `grow=0..1` controls how far the
tendrils have crawled (default 1 = fully fused).  Extra exprs `evil`, `open_eyes`.
"""
import math

from engine.core import step_frame, clamp, lerp
from engine.gfx import INK, stamp_line
from chars import register
from chars.rig import pose_idle, _blink
from chars.shouyou import LayeredDef

HEAD_PAL = {
    "o": INK,
    "L": (246, 226, 214),   # scalp shine
    "A": (206, 190, 190),   # shaved scalp (skin + blue-grey stubble)
    "a": (164, 148, 160),
    "q": (156, 142, 160),   # stubble dots
    "S": (240, 204, 172),   # skin (sallow)
    "s": (208, 160, 132),
    "c": (180, 150, 140),   # chin stubble
    "w": (250, 250, 250),
    "m": (120, 44, 56),
    "t": (255, 255, 255),   # teeth
    "b": (230, 150, 140),
    "T": (120, 200, 255),
    "E": (60, 50, 60),
}

BASE = [
    "......oooooo......",   # 0
    "....ooAAAAAAoo....",   # 1
    "...oAALLAAAAAAo...",   # 2
    "..oALLAAAqAAAAAo..",   # 3
    ".oaALAAqAAAAAqAAo.",   # 4
    ".oaAAAAAAAqAAAAAo.",   # 5
    ".oaAAqAAAAAAAqAAo.",   # 6
    "oaaAAAAAAqAAAAAAAo",   # 7
    "oaAASSSSSSSSSSSAAo",   # 8  hairline
    "oaSSSSSSSSSSSSSSso",   # 9
    "osoSSoSSSSSSoSSSSo",   # 10 ear / sly brows
    "oSoSSSooSSSSSooSSo",   # 11 blind closed eyes (slanted lines)
    ".osSSSSsSSSSSSsSso",   # 12 gaunt cheek lines
    ".osSSSSsSSSSSSsSo.",   # 13
    "..osSSSSSmmmmmSo..",   # 14 thin long grin
    "...oscSSSSSSScoo..",   # 15 stubble
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
    "blink": _head(),
    "talk": _head(r14="..osSSSSSmooomSo..", r15="...oscSSSSmmmcoo.."),
    "evil": _head(r13=".osSSSSSSSSSSSSmo.", r14="..osSSSSmtttttmo..", r15="...oscSSSmmmmmoo.."),
    "smug": _head(r14="..osSSSSSSmmmmmo..", r15="...oscSSSSSSmmoo.."),
    "happy": _head(r13=".osSSSSSSSSSSSSmo.", r14="..osSSSSmtttttmo..", r15="...oscSSSmmmmmoo.."),
    "angry": _head(r10="osoSSSoSSSSoSSSSSo", r11="oSoSSSSooSSooSSSSo",
                   r14="..osSSSSmtttttmo..", r15="...oscSSSmmmmmoo.."),
    "determined": _head(r10="osoSSSoSSSSoSSSSSo", r11="oSoSSSSooSSooSSSSo"),
    "shout": _head(r10="osoSSSoSSSSoSSSSSo", r11="oSoSSSSooSSooSSSSo", r13=".osSSSSSSooooSSso.",
                   r14="..osSSSSomtttmoo..", r15="...oscSSSooooooo.."),
    "shock": _head(r10="osoSSooSSSSSooSSSo", r11="oSoSowwoSSSowwoSSo", r12=".osSSooSSSSSooSSso",
                   r14="..osSSSSSSooSSSo..", r15="...oscSSSSooScoo.."),
    "open_eyes": _head(r10="osoSSooSSSSSooSSSo", r11="oSoSowwoSSSowwoSSo", r12=".osSSooSSSSSooSSso",
                       r13=".osSSSSSSSSSSSSmo.", r14="..osSSSSmtttttmo..", r15="...oscSSSmmmmmoo.."),
    "sad": _head(r10="osoSSSSoSSSoSSSSSo", r11="oSoSSooSSSSSSooSSo", r14="..osSSSSSSmmmSSo.."),
    "cry": _head(r10="osoSSSSoSSSoSSSSSo", r11="oSoSSooSSSSSSooSSo", r12=".osSSTSSSSSSSTSSso",
                 r13=".osSSTSSSSSSSTSso.", r14="..osSSTSSSmmmTSo.."),
    "hurt": _head(r10="osoSSoSoSSSoSoSSSo", r11="oSoSSSoSSSSSoSSSSo", r12=".osSSoSoSSSoSoSSso",
                  r14="..osSSSSSmtttmSo..", r15="...oscSSSSmmmcoo.."),
    "sleep": _head(r11="oSoSSoooSSSoooSSSo"),
}

TORSO_PAL = {
    "o": INK,
    "K": (70, 68, 92),      # charcoal kimono
    "k": (50, 48, 68),
    "l": (100, 98, 128),
    "W": (226, 224, 232),   # under-collar
    "G": (150, 144, 160),   # grey obi
    "g": (116, 110, 128),
}

TORSO = """
....oooooo....
...oKWWWKKo...
..oKlKWWKKko..
.oKlKKKWKKkko.
.oKlKKKKWKkko.
.oKKKKKKKKkko.
.oGGGGGGGGGgo.
.oKlKKKKkKkko.
.oKlKKKKkKkko.
.oKKKKKKkKkko.
.oKKKKKKkkkko.
..oooooooooo..
"""

RED_D, RED, RED_L, RED_HI = (120, 16, 34), (200, 30, 50), (255, 90, 100), (255, 190, 190)


def sheathed_benizakura(img, torso_xy, torso_size):
    """Benizakura in a crimson-black scabbard at the hip."""
    tx, ty = torso_xy
    a, b = (tx + 13, ty + 6), (tx - 6, ty + 10)
    stamp_line(img, a, b, 4, INK)
    stamp_line(img, a, b, 2, (92, 26, 40))
    stamp_line(img, (tx + 6, ty + 7), (tx - 5, ty + 9.4), 1, (150, 50, 64))
    stamp_line(img, a, (tx + 10, ty + 6.6), 2, (60, 20, 30))
    stamp_line(img, (tx + 9, ty + 5.5), (tx + 9, ty + 8), 1, (200, 60, 70))


# ------------------------------------------------------------------ Benizakura tendrils
def _tendril(img, pts, t, phase=0.0, width=1):
    """Draw a pulsing organic tendril along a polyline."""
    if len(pts) < 2:
        return
    for a, b in zip(pts, pts[1:]):
        stamp_line(img, a, b, width + 2, INK)
    pulse = step_frame(t + phase, 8, 4)
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        col = RED_L if (i + pulse) % 4 == 0 else RED
        stamp_line(img, a, b, width, col)


def _path(p0, p1, n, amp, freq, t, phase=0.0):
    """Wiggly path from p0 to p1 (perpendicular sine offset)."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0) or 1
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    out = []
    for i in range(n + 1):
        u = i / n
        w = math.sin(u * freq * math.pi + phase + t * 6) * amp * (0.4 + 0.6 * u)
        out.append((x0 + (x1 - x0) * u + nx * w, y0 + (y1 - y0) * u + ny * w))
    return out


def _cut(pts, frac):
    """First `frac` of a polyline."""
    if frac >= 1:
        return pts
    if frac <= 0:
        return pts[:1]
    n = (len(pts) - 1) * frac
    k = int(n)
    out = pts[:k + 1]
    if k + 1 < len(pts):
        a, b = pts[k], pts[k + 1]
        f = n - k
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return out


def benizakura_tendrils(img, ctx):
    pp, t = ctx["params"], ctx["t"]
    g = clamp(pp.get("grow", 1.0))
    hf, sf = ctx["hand_f"], ctx["shoulder_f"]
    if not hf or g <= 0:
        return
    tq = step_frame(t, 12) / 12.0
    tx, ty, tw, th = ctx["torso"]
    hx, hy, hw, hh = ctx["head"]
    # 1) coil wrapping the arm from the hilt to the shoulder
    arm = []
    n = 8
    for i in range(n + 1):
        u = i / n
        x = hf[0] + (sf[0] - hf[0]) * u
        y = hf[1] + (sf[1] - hf[1]) * u
        off = 1.6 if i % 2 == 0 else -1.6
        arm.append((x + off * 0.6, y + off))
    _tendril(img, _cut(arm, g / 0.45), tq)
    # 2) crawling over the shoulder onto the chest / back
    if g > 0.45:
        k = (g - 0.45) / 0.35
        chest = _path(sf, (tx + 5, ty + 8), 5, 1.2, 2, tq)
        _tendril(img, _cut(chest, k), tq, 0.2)
        neck = _path(sf, (hx + hw - 5, hy + hh - 4), 4, 1.0, 2, tq, 1.0)
        _tendril(img, _cut(neck, k), tq, 0.4)
    # 3) free tendrils writhing out of the arm + blade root
    if g > 0.7:
        k = (g - 0.7) / 0.3
        mid = ((hf[0] + sf[0]) / 2, (hf[1] + sf[1]) / 2)
        for j, (dx, dy) in enumerate(((-3, -8), (4, -7), (-6, 3))):
            end = (mid[0] + dx * (0.6 + 0.4 * k) + math.sin(tq * 9 + j) * 1.5,
                   mid[1] + dy * (0.6 + 0.4 * k) + math.cos(tq * 7 + j) * 1.2)
            _tendril(img, _cut(_path(mid, end, 4, 1.4, 1.5, tq, j), k), tq, 0.1 * j)
        root = (hf[0] + 3, hf[1] + 1)
        for j, (dx, dy) in enumerate(((5, -5), (6, 4))):
            end = (root[0] + dx + math.sin(tq * 8 + j) * 1.2, root[1] + dy)
            _tendril(img, _cut(_path(root, end, 3, 1.0, 1.5, tq, j), k), tq, 0.3 * j)
    # 4) pulsing red glow pixels on the hand (the blade feeding on him)
    if step_frame(t, 6, 2) and g > 0.2:
        x, y = hf
        stamp_line(img, (x, y), (x, y), 1, RED_HI)


def pose_benizakura(pp, t, p, d):
    """Blade held low and forward; the demon sword's tendrils wrap his arm."""
    f = step_frame(t, 4, 4)
    pp["arm_f"] = 62
    pp["weapon"] = -18
    pp["arm_b"] = -12
    pp["legs"] = "spread"
    pp["bob"] = -1 if f in (1, 2) else 0
    pp["expr"] = "evil"
    pp["grow"] = 1.0
    pp["props"] = [benizakura_tendrils]


def pose_idle_nizo(pp, t, p, d):
    pose_idle(pp, t, p, d)
    pp["expr"] = "normal"          # always 'closed' eyes -> no blink
    pp["arm_f"] = 14 if pp["bob"] else 10


OKADA_NIZO = register(LayeredDef(
    id="okada_nizo", name="冈田似藏", color=(170, 40, 60), voice=0.72,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=(70, 68, 92), sleeve_b=(50, 48, 68), sleeve_frac=0.7,
    hand=(240, 204, 172),
    leg_len=7, leg_w=3, leg_gap=4, pants=(56, 54, 74), shoes=(28, 24, 34),
    weapon="benizakura", weapon_len=18, sheathed=sheathed_benizakura,
    poses={"benizakura": pose_benizakura, "idle": pose_idle_nizo},
    portrait_crop=17,
    desc="鬼兵队的盲眼人斩，光头、闭眼、嘴角阴笑。被妖刀红樱寄生，手臂缠满红色触手。",
))
