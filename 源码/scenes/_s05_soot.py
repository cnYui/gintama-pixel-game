"""s05 private helper: post-explosion Gintoki (soot face + his silver perm blown
into a giant AFRO).

The lead-owned gintoki def has no soot/afro expression, so this module builds a
PRIVATE shallow copy of the def with extra afro heads (the shared def is never
mutated).  Afro heads are generated from Gintoki's own expression heads: the
face rows are kept (skin -> soot, eyes/mouth/tears intact) and his silver hair is
replaced by a big bumpy afro with soot patches, so he stays recognisable.

API
    draw_soot_gintoki(img, x, y, pose, t, p=None, expr="shock", facing=1, **kw)
        feet at (x, y); expr = any gintoki expression (shock/blink/talk/shout/
        angry/cry/sad/normal...).  Returns dict(head=(cx, cy)) = afro centre and
        eyes=((lx, ly), (rx, ry)) in canvas coords (for tears / sparks).
"""
import copy
import math

import numpy as np
from PIL import Image

from engine.core import step_frame
from engine.gfx import INK, flip_h, overlay_rect
from chars import get_def
from chars.rig import EXPR_FALLBACK

HW, HH = 30, 25          # afro head sprite size
FX0, FY0 = 6, 8          # where base-head column 0 / row 0 land (face rows 8..16 -> y 16..24)

SOOT_PAL = {
    "g": (126, 110, 114),    # soot on skin
    "G": (94, 80, 90),       # soot shade
    "k": (150, 150, 168),    # sooty silver curl
    "K": (104, 100, 120),    # burnt curl
    "q": (255, 214, 184),    # clean skin (washed by tears)
}

_DEF = None
_SOOT_KEYS = set()

# extra face variants (row overrides on top of one of Gintoki's own heads)
CUSTOM = {
    # wide-open yelling mouth
    "yell": ("shout", {13: ".ohSSSSSSoooooSso.", 14: "..osSSSSSommmoSo..", 15: "...oosSSSSoooSoo.."}),
    # wailing: squeezed eyes, tear streams, mouth wide open
    "wail": ("cry", {13: ".ohSSTSSoooSTSSso.", 14: "..osSTSommmoTSSo..", 15: "...oosTSoooSTsoo.."}),
}


def _resolve(heads, e):
    seen = set()
    while e not in heads and e not in seen:
        seen.add(e)
        e = EXPR_FALLBACK.get(e, "normal")
    return e if e in heads else "normal"


def _afro_art(base_rows, frame, tear_wash=False):
    grid = [["." for _ in range(HW)] for _ in range(HH)]
    cx, cy, rx, ry = 14.5, 11.0, 14.4, 11.2
    for y in range(HH):
        for x in range(HW):
            a = math.atan2((y - cy) / ry, (x - cx) / rx)
            r = 1.0 + 0.085 * math.cos(a * 11 + frame * 1.7) + 0.03 * math.cos(a * 5 - frame)
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= r * r and y <= 21:
                grid[y][x] = "h"
    # curl texture on a staggered grid: highlight arc top-left, shade bottom-right
    for y in range(HH):
        for x in range(HW):
            if grid[y][x] != "h":
                continue
            best = None
            for j in range(-1, 8):
                for i in range(-1, 8):
                    ccx, ccy = 1.5 + i * 4.4 + (j % 2) * 2.2, 1.0 + j * 3.5
                    dd = (x - ccx) ** 2 + (y - ccy) ** 2
                    if best is None or dd < best[0]:
                        best = (dd, x - ccx, y - ccy, i, j)
            dd, dx, dy, ci, cj = best
            sooty = ((ci * 7 + cj * 13 + 3) % 5) in (0, 3)       # some curls are scorched
            if 1.2 <= dd <= 4.6 and dx + dy < -0.5:
                grid[y][x] = "k" if sooty else "H"
            elif dd >= 2.0 and dx + dy > 1.0:
                grid[y][x] = "K" if sooty else "d"
            elif sooty:
                grid[y][x] = "k"
    # face rows from the expression head (skin -> soot)
    for r in range(8, 17):
        row = base_rows[r]
        for xx, ch in enumerate(row):
            if ch == ".":
                continue
            X, Y = FX0 + xx, FY0 + r
            if ch in "Hhd" and grid[Y][X] != ".":
                continue                       # side locks merge into the afro
            grid[Y][X] = {"S": "g", "s": "G"}.get(ch, ch)
    if tear_wash:                              # tears wash clean stripes through the soot
        for r in range(12, 16):
            for xx in range(18):
                if base_rows[r][xx] == "T":
                    for yy in range(r + 1, 16):
                        if grid[FY0 + yy][FX0 + xx] in "gG":
                            grid[FY0 + yy][FX0 + xx] = "q"
    # ink outline around everything
    out = [row[:] for row in grid]
    for y in range(HH):
        for x in range(HW):
            if grid[y][x] == ".":
                for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + ddx, y + ddy
                    if 0 <= xx < HW and 0 <= yy < HH and grid[yy][xx] not in ".o":
                        out[y][x] = "o"
                        break
            elif (x in (0, HW - 1) or y == 0) and grid[y][x] != "o":
                out[y][x] = "o"
    return "\n".join("".join(r) for r in out)


def soot_def():
    global _DEF
    if _DEF is None:
        d0 = get_def("gintoki")
        d = copy.copy(d0)
        d.heads_art = dict(d0.heads_art)
        d.head_pal = dict(d0.head_pal)
        d.head_pal.update(SOOT_PAL)
        d._heads, d._torsos, d._ports = {}, {}, {}
        _DEF = d
    return _DEF


def _head_key(expr, frame):
    d = soot_def()
    heads = get_def("gintoki").heads_art
    if expr in CUSTOM:
        base_e, over = CUSTOM[expr]
        name = expr
    else:
        base_e, over = _resolve(heads, expr or "normal"), {}
        name = base_e
    key = f"_s05soot_{name}_{frame}"
    if key not in _SOOT_KEYS:
        rows = heads[base_e].split("\n")
        for r, v in over.items():
            assert len(v) == len(rows[r]), (expr, r)
            rows[r] = v
        d.heads_art[key] = _afro_art(rows, frame, tear_wash=(base_e == "cry"))
        _SOOT_KEYS.add(key)
    return key


def _soot_body(spr, seed=3):
    """Patchy soot on clothes/limbs (keeps ink, pure whites, tears and the afro head)."""
    a = np.asarray(spr).copy()
    rgb = a[..., :3].astype(np.float32)
    op = a[..., 3] > 0
    ink = np.abs(rgb - np.array(INK, np.float32)).sum(-1) < 8
    white = (rgb > 252).all(-1)
    h, w = op.shape
    yy, xx = np.mgrid[0:h, 0:w]
    cell = ((xx // 2) * 73856093) ^ ((yy // 2) * 19349663) ^ seed
    patch = (cell % 7) < 3
    k = np.where(patch, 0.5, 0.16)
    soot = np.array((58, 50, 62), np.float32)
    m = op & ~ink & ~white
    out = a.copy()
    mixed = rgb * (1 - k[..., None]) + soot * k[..., None]
    out[..., :3][m] = mixed[m].clip(0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def draw_soot_gintoki(img, x, y, pose, t, p=None, expr="shock", facing=1, head_region=None, **kw):
    d = soot_def()
    frame = step_frame(t, 6, 2)
    key = _head_key(expr, frame)
    spr, ax, ay = d.render(pose=pose, t=t, p=p, expr=key, **kw)
    # soot only below the head (the afro head already has its own soot pattern)
    ctx_head = _head_box(pose, t, p, key, kw)
    body = _soot_body(spr)
    if ctx_head is not None:
        hx0, hy0, hw, hh = ctx_head
        body.paste(spr.crop((hx0, hy0, hx0 + hw, hy0 + hh)), (hx0, hy0))
    spr = body
    if facing < 0:
        spr = flip_h(spr)
        ax = spr.width - 1 - ax
    x, y = int(round(x)), int(round(y))
    overlay_rect(img, x - 7, y - 1, 14, 2, (0, 0, 0), 0.3)
    img.paste(spr, (x - ax, y - ay), spr)
    if ctx_head is None:
        return None
    hx0, hy0, hw, hh = ctx_head
    f = 1 if facing >= 0 else -1
    # afro centre and the two eyes (base head eye columns 6 and 12, row 12)
    cxh = hx0 + hw / 2.0
    head = (x + (cxh - ax) * f, y + (hy0 + 11 - ay))
    eyes = tuple((x + (hx0 + FX0 + ex - ax) * f, y + (hy0 + FY0 + 12 - ay)) for ex in (6, 12))
    return {"head": head, "eyes": eyes, "top": (x + (cxh - ax) * f, y + (hy0 + 1 - ay))}


def _head_box(pose, t, p, key, kw):
    """Where compose() put the head in the working canvas (replays its maths)."""
    from chars.rig import POSES, default_params, OX, OY
    d = soot_def()
    fn = d.poses.get(pose) or POSES.get(pose) or POSES["idle"]
    pp = default_params()
    fn(pp, t, p if p is not None else (t % 1.0), d)
    pp.update({k: v for k, v in kw.items() if k in pp})
    hip_y = OY - 1 - d.leg_len + pp["dy"]
    if pp["legs"] == "sit":
        hip_y = OY - 3 + pp["dy"]
    elif pp["legs"] == "kneel":
        hip_y = OY - 1 - d.leg_len + 3 + pp["dy"]
    elif pp["legs"] == "none":
        hip_y = OY - 1 + pp["dy"]
    tx = OX - d.hip[0] + pp["lean"] + pp["dx"]
    ty = hip_y - d.hip[1] + pp["bob"]
    head = d.head(key)
    hw, hh = head.size
    ha = d.head_anchor or (hw // 2, hh - 1)
    hx = tx + d.neck[0] - ha[0] + pp["head_dx"]
    hy = ty + d.neck[1] - ha[1] + pp["head_dy"]
    return int(hx), int(hy), hw, hh
