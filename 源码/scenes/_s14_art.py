"""Private art helpers for s14 尾声 (owned by the s14 agent).

  hooded_gintoki(pose, t, hood, ...)  Gintoki wrapped in a travel cloak; hood 0 = up
                                      (face in shadow, two red glints), 1 = pulled down.
  draw_cloth(img, x, y, t, ang, k)    the loose cloak tumbling through the air / lying.
  stamp_sprite(crack)                 giant red hanko 「完」.
  crow_sprite(frame)                  tiny flapping crow (awkward silence).
  brush_title(...)                    cached brush-font text sprites.
"""
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

from engine.core import step_frame, clamp, lerp, rng
from engine.gfx import INK, outline, stamp_line, shade, rotate_nearest
from engine.text import text_sprite
from chars import get_def
from chars.rig import POSES, default_params, compose, CW, CH, OX, OY

# travel cloak palette (dusty brown-grey, lit from the top-left)
CL_L = (150, 128, 110)
CL_M = (116, 96, 84)
CL_D = (84, 68, 64)
CL_DD = (62, 50, 50)
CL_HI = (178, 160, 140)


def _render_ctx(cid, pose, t, p=None, expr=None, **kw):
    """Same as ChibiDef.render but also returns the compose() context (head/torso boxes)."""
    d = get_def(cid)
    fn = d.poses.get(pose) or POSES.get(pose) or POSES["idle"]
    pp = default_params()
    fn(pp, t, p if p is not None else (t % 1.0), d)
    pp.update({k: v for k, v in kw.items() if k in pp})
    if expr is not None:
        pp["expr"] = expr
    img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    ctx = compose(d, img, pp, t)
    for prop in pp["props"]:
        prop(img, ctx)
    return img, ctx


def _cape(d, ctx, t, flutter):
    """Cape polygon from the shoulders to just above the ankles."""
    tx, ty, tw, th = ctx["torso"]
    tx, ty = int(tx), int(ty)
    hem = OY - 5 + int(ctx["params"]["dy"])
    wob = [0, 1, 0, -1][step_frame(t, 6, 4)] if flutter else 0
    top_l, top_r = tx - 1, tx + tw
    pts = [(top_l + 1, ty + 1), (top_r - 1, ty + 1), (top_r + 2, ty + 5), (top_r + 3, hem - 1 + wob),
           (top_r + 1, hem + 1), (tx + tw - 4, hem - 1), (tx + 6, hem + 1 - wob), (tx + 2, hem - 1),
           (top_l - 4 - wob, hem + 1), (top_l - 3, ty + 6)]
    return pts, hem


def _cloak_layer(ctx, t, hood, flutter=True):
    """RGBA layer (CW x CH) with cape (+ hood or cowl). Returns (layer, face_mask or None)."""
    d = ctx["def"]
    hx, hy, hw, hh = [int(v) for v in ctx["head"]]
    tx, ty, tw, th = [int(v) for v in ctx["torso"]]
    lay = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    dr = ImageDraw.Draw(lay)
    pts, hem = _cape(d, ctx, t, flutter)
    dr.polygon(pts, fill=CL_M + (255,))
    # folds + light on the left shoulder
    for fx_, c in ((tx + 3, CL_D), (tx + 8, CL_D), (tx + 11, CL_D)):
        dr.line([(fx_, ty + 5), (fx_ + (1 if fx_ > tx + 6 else -1), hem - 1)], fill=c + (255,))
    dr.line([(tx, ty + 2), (tx + tw - 2, ty + 2)], fill=CL_L + (255,))
    dr.line([(tx - 1, ty + 3), (tx + 3, ty + 3)], fill=CL_HI + (255,))
    # hem shadow
    dr.line([(tx - 5, hem), (tx + tw + 3, hem)], fill=CL_DD + (255,))
    face = None
    if hood < 0.5:
        # hood up (hood 0) or being pulled back (0 < hood < 0.5)
        sx = -int(round(hood * 8))           # slides back...
        sy = -int(round(hood * 2))           # ...and a bit up
        hl = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        hd = ImageDraw.Draw(hl)
        box = [hx - 2 + sx, hy - 2 + sy, hx + hw + 1 + sx, hy + hh + sy]
        hd.ellipse(box, fill=CL_M + (255,))
        # drape down onto the shoulders + peak at the back of the hood
        hd.polygon([(box[0] + 1, box[1] + 8), (box[0] - 2, box[1] + 15), (box[0] + 4, box[3] + 1),
                    (box[2] - 3, box[3] + 1)], fill=CL_M + (255,))
        # top-left light band + back shade
        hd.arc([box[0] + 2, box[1] + 1, box[2] - 2, box[3] - 3], 195, 290, fill=CL_L + (255,))
        hd.arc([box[0] + 3, box[1] + 2, box[2] - 3, box[3] - 4], 205, 255, fill=CL_HI + (255,))
        hd.arc([box[0] + 1, box[1] + 1, box[2] - 1, box[3] - 1], 110, 175, fill=CL_D + (255,))
        hd.line([(box[0] + 1, box[1] + 10), (box[0] + 2, box[3] - 1)], fill=CL_D + (255,))
        # face opening (front-lower part of the hood)
        fm = Image.new("L", (CW, CH), 0)
        fd = ImageDraw.Draw(fm)
        ow = int(hood * 10)
        fd.ellipse([hx + 5 - ow, hy + 6 - ow // 2, hx + hw + 3, hy + hh + 4], fill=255)
        fd.rectangle([0, hy + hh, CW, CH], fill=0)
        hd.bitmap((0, 0), fm, fill=(0, 0, 0, 0))
        lay.alpha_composite(hl)
        face = fm
    else:
        # hood down: bunched cowl round the neck (behind the head is handled by drawing
        # the head again over it)
        cx, cy = hx + hw // 2 - 3, ty + 1
        dr.ellipse([cx - 9, cy - 3, cx + 8, cy + 4], fill=CL_M + (255,))
        dr.line([(cx - 7, cy - 2), (cx + 3, cy - 2)], fill=CL_L + (255,))
        dr.line([(cx - 8, cy + 2), (cx + 6, cy + 3)], fill=CL_D + (255,))
    # INK outline around the whole cloak shape
    ol = outline(lay, INK)
    out = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    out.alpha_composite(ol.crop((1, 1, CW + 1, CH + 1)))
    return out, face


_hg_cache = {}


def hooded_gintoki(pose, t, hood=0.0, expr=None, p=None, flutter=True, facing=1, flash=0.0,
                   arm=None):
    """Gintoki in the wanderer's cloak. Returns (RGBA, ax, ay) like render_sprite.

    hood : 0 = hood up (face hidden in shadow, dead-fish eyes glint red)
           0..0.5 = being pulled back (front arm raised to the hood)
           >= 0.5 = hood down, bunched at the neck (silver perm revealed)
    arm  : optional front-arm angle override (e.g. raised while pulling the hood)
    """
    f = step_frame(t, 12)
    hq = round(hood, 2)
    key = (pose, f % 48 if pose in ("walk", "idle", "run") else round(t, 3), hq, expr,
           None if p is None else round(p, 3), flutter, arm)
    hit = _hg_cache.get(key)
    if hit is None:
        kw = {"hide_arm_b": True, "sheathed": False}
        if arm is None:
            kw["hide_arm_f"] = True
        else:
            kw["arm_f"] = arm
        tq = f / 12.0
        base, ctx = _render_ctx("gintoki", pose, tq, p=p, expr=expr, **kw)
        lay, face = _cloak_layer(ctx, tq, hood, flutter)
        spr = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        if hood >= 0.5:
            # cowl behind the head: body, then cowl+cape, then head re-pasted on top
            spr.alpha_composite(base)
            spr.alpha_composite(lay)
            hx, hy, hw, hh = [int(v) for v in ctx["head"]]
            d = ctx["def"]
            head = d.head(ctx["params"]["expr"])
            spr.alpha_composite(head, (hx, hy))
        else:
            a = np.asarray(base).copy()
            if face is not None:
                m = np.asarray(face) > 0
                rgb = a[..., :3].astype(np.float32)
                kd = 0.28 + 0.9 * hood
                dark = rgb * kd + np.array([10, 8, 22], np.float32) * (1 - kd)
                a[..., :3][m] = dark[m].astype(np.uint8)
            spr.alpha_composite(Image.fromarray(a, "RGBA"))
            spr.alpha_composite(lay)
            if face is not None and hood < 0.2:
                hx, hy, hw, hh = [int(v) for v in ctx["head"]]
                px = spr.load()
                for ex in (hx + 7, hx + 13):
                    ey = hy + 12
                    if 0 <= ex < CW and 0 <= ey < CH:
                        px[ex, ey] = (235, 60, 70, 255)
            if arm is not None and ctx["hand_f"]:
                # hand gripping the hood edge, drawn over the cloth
                x, y = ctx["hand_f"]
                stamp_line(spr, (x, y), (x, y), 5, INK)
                stamp_line(spr, (x, y), (x, y), 3, (255, 216, 184))
        hit = (spr, OX, OY)
        if len(_hg_cache) > 400:
            _hg_cache.clear()
        _hg_cache[key] = hit
    spr, ax, ay = hit
    if facing < 0:
        spr = spr.transpose(Image.FLIP_LEFT_RIGHT)
        ax = spr.width - 1 - ax
    if flash > 0:
        from engine.gfx import tint
        spr = tint(spr, (255, 255, 255), flash)
    return spr, ax, ay


def draw_hooded(img, x, y, pose, t, hood=0.0, facing=1, shadow=True, **kw):
    spr, ax, ay = hooded_gintoki(pose, t, hood, facing=facing, **kw)
    x, y = int(round(x)), int(round(y))
    if shadow:
        from engine.gfx import overlay_rect
        overlay_rect(img, x - 7, y - 1, 14, 2, (0, 0, 0), 0.25)
    img.paste(spr, (x - ax, y - ay), spr)
    return spr, x - ax, y - ay


# ------------------------------------------------------------------ loose cloak
def draw_cloth(img, x, y, t, ang, k=1.0, lying=False):
    """The discarded cloak: a flapping cloth quad centred at (x, y), rotated `ang` deg."""
    d = ImageDraw.Draw(img)
    if lying:
        pts = [(x - 13, y), (x - 9, y - 4), (x - 2, y - 5), (x + 6, y - 3), (x + 13, y - 1), (x + 14, y + 1),
               (x - 14, y + 1)]
        d.polygon(pts, fill=CL_M, outline=INK)
        d.line([(x - 8, y - 2), (x + 8, y - 2)], fill=CL_L)
        d.line([(x - 3, y - 4), (x - 5, y)], fill=CL_D)
        d.line([(x + 5, y - 2), (x + 4, y)], fill=CL_D)
        return
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    ph = t * 14
    s1, s2, s3 = math.sin(ph), math.sin(ph + 1.7), math.sin(ph + 3.1)
    # empty hooded cape: hood lump on top, flaring ragged hem that ripples
    base = [(-3, -12), (3, -12), (6, -8), (5, -5), (9, -3), (13 + s1, 7), (9, 9 + 2 * s2),
            (5, 7), (1, 10 + 2 * s3), (-3, 7), (-7, 10 + 2 * s1), (-12 + s2, 6), (-9, -3),
            (-5, -5), (-6, -8)]
    pts = [(x + (px_ * ca - py_ * sa) * k, y + (px_ * sa + py_ * ca) * k) for px_, py_ in base]
    d.polygon(pts, fill=CL_M, outline=INK)

    def P(px_, py_):
        return (x + (px_ * ca - py_ * sa) * k, y + (px_ * sa + py_ * ca) * k)
    d.line([P(-3, -10), P(3, -10)], fill=CL_L)          # light on the hood
    d.line([P(-4, -7), P(4, -7)], fill=CL_DD)           # hood opening shadow
    d.line([P(-2, -2), P(-5, 7)], fill=CL_D)            # folds
    d.line([P(3, -2), P(6, 6)], fill=CL_D)
    d.line([P(-7, -2), P(-9, 3)], fill=CL_L)


# ------------------------------------------------------------------ hanko 完
@lru_cache(maxsize=4)
def stamp_sprite(crack=0):
    """Giant red seal 「完」 (~132 px), slightly worn hanko texture. crack>0 adds fractures."""
    S = 132
    red = (208, 36, 48)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([2, 2, S - 3, S - 3], radius=16, outline=red + (255,), width=9)
    d.rounded_rectangle([14, 14, S - 15, S - 15], radius=10, outline=red + (255,), width=2)
    g = text_sprite("完", red, 96, "brush", outline=None)
    img.alpha_composite(g, ((S - g.width) // 2, (S - g.height) // 2 - 2))
    # worn texture: knock random holes into the red
    a = np.asarray(img).copy()
    r = rng("hanko", 1)
    hole = np.zeros((S, S), bool)
    for _ in range(170):
        x, y = r.randrange(S), r.randrange(S)
        w = r.choice((1, 1, 2, 3))
        hole[y:y + (1 if w < 3 else 2), x:x + w] = True
    a[..., 3][hole] = 0
    img = Image.fromarray(a, "RGBA")
    if crack:
        d = ImageDraw.Draw(img)
        cr = rng("crack", crack)
        for s in range(4):
            x, y = S // 2 + cr.randint(-10, 10), S - 4
            for _ in range(7):
                nx = x + cr.randint(-12, 12)
                ny = y - cr.randint(8, 20)
                d.line([(x, y), (nx, ny)], fill=(0, 0, 0, 0), width=3)
                d.line([(x, y), (nx, ny)], fill=(255, 255, 255, 255), width=1)
                x, y = nx, ny
    # dark ink outline for readability on any backdrop
    return outline(img, (60, 10, 20))


# ------------------------------------------------------------------ crow
@lru_cache(maxsize=4)
def crow_sprite(frame):
    up = frame % 2 == 0
    art = [
        "....ooo.......",
        "...oBBBo......",
        ".oooBwBBoo....",
        "oyyoBBBBBBoo..",
        ".oooBBBBBBBBo.",
        "....oBBBBBBoBo",
        ".....ooooooo.o",
    ]
    wing_up = ["......oo......", ".....oBBo.....", "....oBBBo....."]
    wing_dn = [".....oBBBBo...", "......oBBBo...", ".......ooo...."]
    rows = (wing_up + art) if up else (art[:5] + wing_dn + art[5:])
    pal = {"o": INK, "B": (40, 36, 56), "w": (255, 255, 255), "y": (240, 190, 60)}
    w = max(len(r_) for r_ in rows)
    img = Image.new("RGBA", (w, len(rows)), (0, 0, 0, 0))
    px = img.load()
    for yy, row in enumerate(rows):
        for xx, ch in enumerate(row):
            if ch in ". ":
                continue
            c = pal[ch]
            px[xx, yy] = c + (255,)
    return img


EYE_RED = (235, 60, 70, 255)


def eye_points(spr):
    """Sprite-local (x, y) of the hooded wanderer's two red eye pixels."""
    key = id(spr)
    hit = _eye_cache.get(key)
    if hit is None or hit[0] is not spr:
        a = np.asarray(spr)
        m = (a[..., 0] == 235) & (a[..., 1] == 60) & (a[..., 2] == 70) & (a[..., 3] == 255)
        pts = [(int(x), int(y)) for y, x in np.argwhere(m)]
        if len(_eye_cache) > 200:
            _eye_cache.clear()
        hit = (spr, pts)
        _eye_cache[key] = hit
    return hit[1]


_eye_cache = {}


# ------------------------------------------------------------------ props
BR_L, BR_M, BR_D = (196, 142, 88), (158, 104, 62), (112, 70, 44)
HOOP = (70, 66, 80)


@lru_cache(maxsize=2)
def barrel_sprite(variant=0):
    """Small wooden street barrel / rain bucket (~12x13) with INK outline."""
    w, h = 12, 13
    img = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([1, 1, w, h], radius=3, fill=BR_M + (255,))
    d.rectangle([3, 2, 5, h - 1], fill=BR_L + (255,))          # lit staves (top-left light)
    d.rectangle([w - 3, 2, w - 1, h - 1], fill=BR_D + (255,))
    for y in (3, h - 3):
        d.line([(1, y), (w, y)], fill=HOOP + (255,))
    if variant:
        d.line([(1, h // 2), (w, h // 2)], fill=HOOP + (255,))
    return outline(img, INK)


def anger_vein(img, x, y, t, t0, size=5, color=(236, 48, 60)):
    """Manga anger mark (four little curved ticks) that pops and throbs."""
    if t < t0:
        return
    k = min(1.0, (t - t0) / 0.1)
    s = max(2, int(size * k * (1.0 + 0.2 * (step_frame(t, 8) % 2))))
    d = ImageDraw.Draw(img)
    for w, col in ((5, INK), (3, color)):
        for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            p0 = (x + sx * 2, y + sy * s)
            p1 = (x + sx * 2, y + sy * 2)
            p2 = (x + sx * s, y + sy * 2)
            d.line([p0, p1, p2], fill=col, width=w, joint="curve")


# ------------------------------------------------------------------ text
@lru_cache(maxsize=64)
def brush_text(text, size, color=(255, 255, 255), outline_c=INK, thick=2, face="brush"):
    return text_sprite(text, color, size, face, outline=outline_c, thick=thick)


@lru_cache(maxsize=32)
def rotated(key_img_text, size, color, angle, face="brush", thick=2):
    s = text_sprite(key_img_text, color, size, face, outline=INK, thick=thick)
    return rotate_nearest(s, angle) if angle else s
