"""bg.kabukicho — the Kabukicho street, home of the Yorozuya.

street(img, cam_x, t, tod='day', dy=0, wet=None)
    Long horizontally scrolling street. cam_x = WORLD x of the screen's left
    edge; the world wraps seamlessly every STREET_W px, so any cam_x works
    (e.g. cam_x = YOROZUYA_X - W // 2 centres the Yorozuya building).
    Layers: sky, clouds, Terminal tower (0.1), amanto high-rises (0.3), ships &
    a hovering car, rooftops/billboards (0.55), street facades (1.0), flagstone
    road. Animated: swaying lanterns, fluttering noren and nobori flags,
    flickering neon, steam/smoke, blinking pachinko bulbs.
    dy shifts the whole street down (sky fills the top) — used for tilt-ups.
    wet=True (default for 'storm') mirrors the shopfronts in the rainy road.
street_fg(img, cam_x, t, tod='day')
    Optional foreground (parallax 1.5): dark power-pole silhouettes that sweep
    past during pans. Draw AFTER the characters.
yorozuya_front(img, t, tod='day')
    Framed establishing shot: the Yorozuya building centred, camera tilted up
    (sky, Terminal above), a near power pole framing the left edge.
yorozuya_front_fg(img, t, tod='day')
    Re-draws the balcony railing + big sign over characters standing on the
    balcony at BALCONY_Y (hides their shins like the real railing would).

World constants (street coordinates; screen x = world x - cam_x):
    STREET_W        world width (wrap period)
    FLOOR_Y = 160   feet line of characters on the street
    BASE_Y  = 152   where facades meet the road (doors' bottom)
    YOROZUYA_X      world x of the Yorozuya / Otose building centre
    YOROZUYA_W      building width (160)
    YOROZUYA_WINDOW (x, y, w, h) 2nd-floor window Gintoki gets kicked out of
    YOROZUYA_DOOR   (x, y, w, h) ground floor 'Snack Otose' sliding door (42 tall)
    YOROZUYA_UPDOOR (x, y, w, h) 2nd-floor Yorozuya entrance
    STREET_BALCONY_Y = 84   feet line on the 2nd-floor balcony in street()
    BALCONY_X0/X1   world x range of the balcony walkway
    STAIRS          ((x_bottom, y_bottom), (x_top, y_top)) outside staircase
    stairs_y(wx)    feet y on the staircase at world x (None if off the stairs)
Front-shot constants (screen coordinates in yorozuya_front):
    FRONT_DY = 36, BALCONY_Y = 120, FRONT_FLOOR_Y = 196, FRONT_CX = 192,
    FRONT_WINDOW, FRONT_DOOR, FRONT_UPDOOR (x, y, w, h), FRONT_BALCONY_X0/X1
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import W, H, rng, clamp
from engine.gfx import INK, shade, mix
from . import common as C
from . import edo as E
from ._draw import (WrapLayer, graded_layer, paste_layer, roof, flat_roof, wall, post, beam, boards,
                    siding_h, lattice, frame, shoji, glass, mushiko, noren, sign, text_on, neon_tube,
                    window_grid, glow_rect, Pal, TILE, TILE_B, WOOD, WOOD_D, PLASTER, CONCRETE, PAPER, GLOW,
                    GLOW_PAPER, CLEAR)

STREET_W = 1152
FLOOR_Y = 160
BASE_Y = 152
_LAYER_H = 160

# ------------------------------------------------------------------ layout
# (type, width) placed left to right from world x 0; must sum to STREET_W
_LAYOUT = [
    ("ramen", 88), ("pachinko", 104), ("alley", 14), ("machiya0", 84), ("yorozuya", 160),
    ("alley", 12), ("sweets", 92), ("sake", 80), ("host", 100), ("alley", 14),
    ("machiya1", 86), ("sento", 110), ("pawn", 78), ("alley", 12), ("machiya2", 118),
]
assert sum(w for _, w in _LAYOUT) == STREET_W


def _x_of(kind):
    x = 0
    for k, w in _LAYOUT:
        if k == kind:
            return x
        x += w
    raise KeyError(kind)


_YX0 = _x_of("yorozuya")
YOROZUYA_W = 160
YOROZUYA_X = _YX0 + YOROZUYA_W // 2
YOROZUYA_WINDOW = (_YX0 + 10, 49, 35, 23)
YOROZUYA_DOOR = (_YX0 + 46, 110, 39, 42)
YOROZUYA_UPDOOR = (_YX0 + 116, 43, 25, 41)
STREET_BALCONY_Y = 84
BALCONY_X0, BALCONY_X1 = _YX0 + 4, _YX0 + 146
STAIRS = ((_YX0 + 92, BASE_Y), (_YX0 + 150, STREET_BALCONY_Y))


def stairs_y(wx):
    """Feet y on the outside staircase at world x (None outside it)."""
    (x0, y0), (x1, y1) = STAIRS
    if not (x0 <= wx <= x1):
        return None
    return int(round(y0 + (y1 - y0) * (wx - x0) / (x1 - x0)))


FRONT_DY = 36
FRONT_CX = W // 2
BALCONY_Y = STREET_BALCONY_Y + FRONT_DY
FRONT_FLOOR_Y = FLOOR_Y + FRONT_DY
_FCAM = YOROZUYA_X - FRONT_CX


def _front_rect(r):
    return (r[0] - _FCAM, r[1] + FRONT_DY, r[2], r[3])


FRONT_WINDOW = _front_rect(YOROZUYA_WINDOW)
FRONT_DOOR = _front_rect(YOROZUYA_DOOR)
FRONT_UPDOOR = _front_rect(YOROZUYA_UPDOOR)
FRONT_BALCONY_X0, FRONT_BALCONY_X1 = BALCONY_X0 - _FCAM, BALCONY_X1 - _FCAM

# dynamic (per-frame) decorations, filled while building the facade layer
_DYN = dict(lanterns=[], noren=[], neon=[], smoke=[], flags=[], bulbs=[], poles=[])

NOREN_INDIGO = (54, 62, 104)
NOREN_RED = (170, 52, 50)
NOREN_PURPLE = (92, 60, 110)
NOREN_WHITE = (226, 220, 206)


# ------------------------------------------------------------------ building painters
def _machiya(L, X, w, variant, r):
    d, e, img = L.d, L.e, L.img
    ridge = 42 + variant * 2
    wall(d, X, 57, X + w - 1, 99, PLASTER, posts=[X, X + w - 3], seed=X)
    beam(d, X, X + w - 1, 56, WOOD)
    if variant == 0:
        for wx in (X + 10, X + w // 2 + 4):
            mushiko(d, wx, 68, wx + w // 2 - 18, 84)
    else:
        n = 2
        for i in range(n):
            wx = X + 8 + i * (w - 16) // n
            ww = (w - 16) // n - 6
            shoji(d, e if r.random() < 0.7 else None, wx, 62, wx + ww, 86, cols=4, rows=3)
        # wooden balustrade
        d.rectangle([X + 3, 84, X + w - 4, 85], fill=WOOD.mid)
        d.line([(X + 3, 84), (X + w - 4, 84)], fill=WOOD.hi)
        for bx in range(X + 4, X + w - 4, 3):
            d.line([(bx, 86), (bx, 92)], fill=WOOD.dark)
        d.rectangle([X + 3, 93, X + w - 4, 94], fill=WOOD.mid)
    roof(d, X - 3, X + w + 2, ridge, 55, TILE if variant != 1 else TILE_B, inset=10)
    # ground floor
    boards(d, X, 107, X + w - 1, BASE_Y - 1, WOOD_D, step=4)
    post(d, X, 107, BASE_Y - 1, WOOD)
    post(d, X + w - 3, 107, BASE_Y - 1, WOOD)
    door_x = X + (w - 36) // 2 + (8 if variant == 2 else 0)
    # interior + sliding lattice doors
    lattice(d, e, door_x, 110, door_x + 35, BASE_Y - 1, lit=True, gap=3)
    lattice(d, e, X + 6, 116, door_x - 6, 146, lit=r.random() < 0.8, gap=1)
    lattice(d, e, door_x + 42, 116, X + w - 8, 146, lit=r.random() < 0.8, gap=1)
    goods = ["米", "茶", "药", "书", "豆腐", "布", "伞"]
    txt = goods[(X // 7) % len(goods)]
    col = (NOREN_INDIGO, NOREN_RED, NOREN_WHITE)[variant % 3]
    tcol = (240, 236, 226) if variant % 3 != 2 else (60, 40, 40)
    noren(d, door_x + 1, 110, door_x + 34, 124, col, txt, tcol, panels=3, img=img, e=e)
    _DYN["noren"].append((door_x + 1 - L.M, 110, door_x + 34 - L.M, 124))
    roof(d, X - 4, X + w + 3, 99, 106, TILE, inset=3, ridge=False, eave_shadow=(60, 48, 46))
    # hanging vertical signboard
    sign(img, X + w - 22, 108, X + w - 8, 134, txt if len(txt) == 2 else txt + "屋", vertical=True,
         bg=(214, 196, 156), fg=(50, 30, 26), border=(80, 52, 36))
    _DYN["lanterns"].append((door_x - 4 - L.M, 106, C.RED if variant != 1 else C.WHITE, 1, None))


def _yorozuya(L, X, r):
    d, e, img = L.d, L.e, L.img
    BY = STREET_BALCONY_Y
    # ---------------- 2nd floor
    wall(d, X + 2, 44, X + 157, BY - 1, PLASTER, posts=[X + 2, X + 52, X + 104, X + 155], seed=7)
    beam(d, X, X + 159, 43, WOOD)
    wx, wy, ww, wh = YOROZUYA_WINDOW
    wx += L.M
    glass(d, e, wx, wy, wx + ww - 1, wy + wh - 1, lit=True, bars=1)
    d.rectangle([wx - 2, wy + wh, wx + ww + 1, wy + wh + 1], fill=WOOD.dark)      # sill
    glass(d, e, X + 60, wy, X + 96, wy + wh - 1, lit=True, bars=1)
    d.rectangle([X + 58, wy + wh, X + 98, wy + wh + 1], fill=WOOD.dark)
    # 2F entrance: sliding door with glass upper half
    ux, uy, uw, uh = YOROZUYA_UPDOOR
    ux += L.M
    d.rectangle([ux - 2, uy - 1, ux + uw + 1, uy + uh], fill=WOOD.dark)
    d.rectangle([ux, uy + 1, ux + uw - 1, uy + uh - 1], fill=WOOD.mid)
    glass(d, e, ux + 2, uy + 3, ux + uw - 3, uy + 19, lit=True, bars=1)
    for yy in range(uy + 22, uy + uh - 2, 3):
        d.line([(ux + 2, yy), (ux + uw - 3, yy)], fill=WOOD.dark)
    d.line([(ux + uw // 2, uy + 1), (ux + uw // 2, uy + uh - 1)], fill=WOOD.dk2)
    d.rectangle([ux + uw + 4, uy + 8, ux + uw + 8, uy + 22], fill=(226, 218, 196), outline=WOOD.dk2)
    # ---------------- roof (taller than the neighbours: it's the hero building)
    roof(d, X - 4, X + 163, 28, 42, TILE, inset=12, eave_shadow=(120, 110, 96))
    # ---------------- balcony walkway + lattice railing
    _balcony(d, X, X + 159, BY)
    # ---------------- ground floor: Snack Otose
    boards(d, X, 106, X + 159, BASE_Y - 1, WOOD_D, step=4)
    post(d, X, 106, BASE_Y - 1, WOOD, 4)
    post(d, X + 42, 106, BASE_Y - 1, WOOD, 3)
    post(d, X + 86, 106, BASE_Y - 1, WOOD, 3)
    sign(img, X + 6, 112, X + 39, 123, "SNACK", bg=(238, 232, 214), fg=(120, 40, 60),
         border=(60, 40, 36), e=e, glow=(255, 236, 200))
    lattice(d, e, X + 7, 127, X + 38, 147, lit=True, gap=1)
    dx_, dy_, dw, dh = YOROZUYA_DOOR
    dx_ += L.M
    d.rectangle([dx_ - 1, dy_ - 1, dx_ + dw, dy_ + dh - 1], fill=WOOD.dk2)
    for i in range(2):
        px0 = dx_ + i * (dw // 2)
        glass(d, e, px0 + 1, dy_ + 1, px0 + dw // 2 - 2, dy_ + dh - 3, lit=True, bars=0, tint=(86, 96, 110))
        for yy in (dy_ + 20, dy_ + 30):
            d.line([(px0 + 1, yy), (px0 + dw // 2 - 2, yy)], fill=WOOD.mid)
            e.line([(px0 + 1, yy), (px0 + dw // 2 - 2, yy)], fill=CLEAR)
    noren(d, dx_, dy_, dx_ + dw - 1, dy_ + 13, NOREN_PURPLE, "登势", (240, 232, 214), panels=3, img=img, e=e)
    _DYN["noren"].append((dx_ - L.M, dy_, dx_ + dw - 1 - L.M, dy_ + 13))
    d.rectangle([X + 88, 144, X + 95, BASE_Y - 1], fill=(150, 90, 60))
    d.ellipse([X + 86, 134, X + 97, 146], fill=(70, 120, 70))
    d.point([(X + 89, 137), (X + 92, 136)], fill=(110, 160, 90))
    # ground floor eave over the snack, then the big sign hanging from the balcony
    roof(d, X - 3, X + 96, 104, 109, TILE, inset=3, ridge=False, eave_shadow=(60, 48, 46))
    d.rectangle([X - 1, BY + 4, X + 160, BY + 5], fill=WOOD.dark)          # fascia
    _big_sign(img, e, X + 24, BY + 4)
    # under-stairs: electricity meter + gas cylinders
    d.rectangle([X + 112, 116, X + 120, 126], fill=(180, 180, 176), outline=(90, 90, 96))
    d.rectangle([X + 138, 132, X + 143, BASE_Y - 1], fill=(170, 170, 176))
    d.rectangle([X + 145, 132, X + 150, BASE_Y - 1], fill=(170, 170, 176))
    d.line([(X + 138, 132), (X + 138, BASE_Y - 1)], fill=(210, 210, 214))
    _stairs(d, X)
    _DYN["lanterns"].append((X + 44 - L.M, 109, C.RED, 1, None))


def _balcony(d, x0, x1, BY):
    """Walkway floor (top at BY) + lattice railing BY-9..BY-1."""
    d.rectangle([x0, BY, x1, BY + 3], fill=WOOD.mid)
    d.line([(x0, BY), (x1, BY)], fill=WOOD.hi)
    d.line([(x0, BY + 3), (x1, BY + 3)], fill=WOOD.dk2)
    top = BY - 9
    d.rectangle([x0, top, x1, top + 2], fill=WOOD.mid)
    d.line([(x0, top), (x1, top)], fill=WOOD.hi)
    d.line([(x0, top + 2), (x1, top + 2)], fill=WOOD.dark)
    for bx in range(x0 + 2, x1, 3):
        d.line([(bx, top + 3), (bx, BY - 1)], fill=WOOD.dark)
    d.line([(x0, top + 6), (x1, top + 6)], fill=WOOD.dark)
    for px in (x0, x0 + 50, x0 + 102, x1 - 2):
        d.rectangle([px, top - 2, px + 2, BY + 3], fill=WOOD.mid)
        d.line([(px, top - 2), (px, BY + 3)], fill=WOOD.hi)
        d.line([(px + 2, top - 2), (px + 2, BY + 3)], fill=WOOD.dark)


def _big_sign(img, e, x, y):
    """「万事屋银酱」 signboard, 78x19, top-left at (x, y)."""
    d = ImageDraw.Draw(img)
    w, h = 78, 19
    d.rectangle([x - 1, y - 1, x + w, y + h], fill=(44, 30, 30))
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=(242, 238, 226))
    d.rectangle([x + 1, y + 1, x + w - 2, y + h - 2], outline=(200, 190, 170))
    d.line([(x, y), (x + w - 1, y)], fill=(255, 252, 244))
    from engine.text import draw_text
    draw_text(img, x + w // 2 + 1, y + h // 2 + 1, "万事屋银酱", (26, 20, 24), size=12, anchor="mm")
    if e is not None:
        e.rectangle([x + 1, y + 1, x + w - 2, y + h - 2], fill=(255, 244, 214, 150))
        draw_text(e._image, x + w // 2 + 1, y + h // 2 + 1, "万事屋银酱", (26, 20, 24), size=12, anchor="mm")
    # hanging hooks
    d.line([(x + 6, y - 3), (x + 6, y - 1)], fill=(60, 50, 50))
    d.line([(x + w - 7, y - 3), (x + w - 7, y - 1)], fill=(60, 50, 50))


def _stairs(d, X):
    (bx, by), (tx, ty) = STAIRS
    bx, tx = bx - _YX0 + X, tx - _YX0 + X
    n = 17
    rise = (by - ty) / n
    run = (tx - bx) / n
    # landing platform + support post
    d.rectangle([tx - 4, ty - 1, X + 159, ty + 2], fill=WOOD.mid)
    d.line([(tx - 4, ty - 1), (X + 159, ty - 1)], fill=WOOD.hi)
    post(d, X + 155, ty + 3, BASE_Y - 1, WOOD, 3)
    # stringer (thick diagonal beam)
    for k in range(4):
        d.line([(bx + 2, by - 1 + k), (tx + 2, ty + 3 + k)], fill=WOOD.dark if k < 3 else WOOD.dk2)
    # treads + risers
    for k in range(n):
        y = int(round(by - (k + 1) * rise))
        x = int(round(bx + k * run))
        d.line([(x, y), (x + int(run) + 2, y)], fill=WOOD.hi)
        d.line([(x, y + 1), (x + int(run) + 2, y + 1)], fill=WOOD.mid)
        d.line([(x, y + 1), (x, y + int(rise))], fill=WOOD.dk2)
    # handrail + posts
    d.line([(bx + 1, by - 16), (tx + 1, ty - 14)], fill=WOOD.mid, width=2)
    d.line([(bx + 1, by - 17), (tx + 1, ty - 15)], fill=WOOD.hi)
    for k in range(0, n + 1, 4):
        x = int(round(bx + 1 + k * run))
        y_top = int(round(by - 16 - k * rise))
        d.line([(x, y_top), (x, y_top + 15)], fill=WOOD.dark)
    d.line([(tx + 1, ty - 15), (X + 159, ty - 13)], fill=WOOD.mid, width=2)


def _ramen(L, X, w, r):
    d, e, img = L.d, L.e, L.img
    wall(d, X, 56, X + w - 1, 99, PLASTER, posts=[X, X + w - 3], seed=3)
    beam(d, X, X + w - 1, 55, WOOD)
    sign(img, X + 12, 62, X + w - 13, 78, "北斗心轩", bg=(230, 220, 190), fg=(150, 30, 30),
         border=(90, 50, 30), e=e, glow=(255, 236, 190))
    shoji(d, e, X + 14, 82, X + w - 15, 94, cols=6, rows=1)
    roof(d, X - 3, X + w + 2, 40, 54, TILE_B, inset=10)
    boards(d, X, 107, X + w - 1, BASE_Y - 1, WOOD_D)
    post(d, X, 107, BASE_Y - 1)
    post(d, X + w - 3, 107, BASE_Y - 1)
    # open counter front
    d.rectangle([X + 8, 112, X + w - 9, BASE_Y - 1], fill=(64, 44, 40))
    glow_rect(e, X + 9, 113, X + w - 10, 137, GLOW, 235)
    d.rectangle([X + 8, 138, X + w - 9, 141], fill=WOOD.hi)
    d.rectangle([X + 8, 142, X + w - 9, BASE_Y - 1], fill=WOOD.mid)
    for sx in range(X + 14, X + w - 12, 16):          # stools
        d.rectangle([sx, 146, sx + 5, 147], fill=(170, 50, 46))
        d.line([(sx + 2, 148), (sx + 2, BASE_Y - 1)], fill=(80, 80, 90))
    noren(d, X + 8, 110, X + w - 9, 126, NOREN_RED, "拉面", (250, 240, 220), panels=4, img=img, e=e)
    _DYN["noren"].append((X + 8 - L.M, 110, X + w - 9 - L.M, 126))
    roof(d, X - 4, X + w + 3, 100, 106, TILE_B, inset=3, ridge=False, eave_shadow=(60, 48, 46))
    for lx in (X + 4, X + w - 6):
        _DYN["lanterns"].append((lx - L.M, 106, C.RED, 2, "拉"))
    _DYN["smoke"].append((X + w - 20 - L.M, 38, (230, 230, 236)))
    d.rectangle([X + w - 23, 34, X + w - 17, 41], fill=(110, 110, 120))


def _pachinko(L, X, w, r):
    d, e, img = L.d, L.e, L.img
    top = 20
    d.rectangle([X, top, X + w - 1, BASE_Y - 1], fill=(196, 186, 200))
    d.line([(X, top), (X, BASE_Y - 1)], fill=(220, 214, 226))
    d.line([(X + w - 1, top), (X + w - 1, BASE_Y - 1)], fill=(150, 140, 160))
    flat_roof(d, X, X + w - 1, top, CONCRETE)
    # horizontal neon '★777★' band
    d.rectangle([X + 24, 30, X + w - 6, 50], fill=(60, 36, 70))
    text_on(img, X + 24 + (w - 30) // 2, 41, "★777★", (170, 140, 60), e, (255, 230, 90))
    _DYN["neon"].append((X + 24 - L.M, 30, X + w - 6 - L.M, 50, 0.9))
    # windows band
    window_grid(d, e, X + 26, 58, X + w - 6, 96, 8, 6, 3, r, 0.9, tint=(96, 90, 130), lit_c=(255, 170, 230))
    # vertical sign パチンコ with bulb border
    sx0, sy0, sx1, sy1 = X + 4, 24, X + 19, 84
    d.rectangle([sx0, sy0, sx1, sy1], fill=(170, 30, 60), outline=(90, 20, 40))
    text_on(img, (sx0 + sx1) // 2 + 1, sy0 + 6, "パチンコ", (255, 236, 150), e, (255, 250, 200), vertical=True)
    for yy in range(sy0 + 1, sy1, 3):
        _DYN["bulbs"].append((sx0 - L.M, yy))
        _DYN["bulbs"].append((sx1 - L.M, yy))
    # awning + bright glass front
    d.rectangle([X + 2, 100, X + w - 3, 106], fill=(220, 60, 80))
    for ax in range(X + 2, X + w - 3, 8):
        d.rectangle([ax, 100, ax + 3, 106], fill=(250, 236, 236))
    d.line([(X + 2, 107), (X + w - 3, 107)], fill=(120, 40, 50))
    d.rectangle([X + 4, 110, X + w - 5, BASE_Y - 1], fill=(90, 100, 120))
    e.rectangle([X + 5, 111, X + w - 6, BASE_Y - 2], fill=(255, 236, 200, 200))
    for gx in range(X + 4, X + w - 5, 24):
        d.line([(gx, 110), (gx, BASE_Y - 1)], fill=(200, 200, 210))
        e.line([(gx, 110), (gx, BASE_Y - 1)], fill=CLEAR)
    # rows of machines visible inside (just colored blips)
    for mx in range(X + 8, X + w - 8, 6):
        d.rectangle([mx, 118, mx + 3, 128], fill=(220, 120, 180))
        e.rectangle([mx, 118, mx + 3, 128], fill=(255, 160, 220, 255))
    # opening wreaths (hanawa)
    for i, hx in enumerate((X + 10, X + w - 18)):
        cols = [(250, 110, 150), (255, 220, 90), (130, 200, 250)]
        d.line([(hx + 4, 130), (hx + 4, BASE_Y - 1)], fill=(120, 110, 100))
        d.ellipse([hx - 2, 118, hx + 10, 130], fill=cols[i])
        d.ellipse([hx + 1, 121, hx + 7, 127], fill=(250, 250, 250))


def _sweets(L, X, w, r):
    d, e, img = L.d, L.e, L.img
    ridge, eave = 72, 88
    wall(d, X, eave + 1, X + w - 1, 106, PLASTER, posts=[X, X + w - 3], seed=5)
    roof(d, X - 3, X + w + 2, ridge, eave, TILE, inset=8)
    # little attic window
    mushiko(d, X + w // 2 - 10, 94, X + w // 2 + 10, 102)
    boards(d, X, 107, X + w - 1, BASE_Y - 1, WOOD)
    post(d, X, 107, BASE_Y - 1)
    post(d, X + w - 3, 107, BASE_Y - 1)
    d.rectangle([X + 6, 112, X + w - 7, BASE_Y - 1], fill=(70, 50, 44))
    glow_rect(e, X + 7, 113, X + w - 8, BASE_Y - 2, GLOW, 220)
    # shelves of dango / sweets
    for yy in (122, 132):
        d.line([(X + 8, yy), (X + w - 9, yy)], fill=WOOD.hi)
        e.line([(X + 8, yy), (X + w - 9, yy)], fill=CLEAR)
        for k, sx in enumerate(range(X + 10, X + w - 10, 7)):
            c = [(250, 220, 230), (240, 240, 230), (140, 190, 110)][k % 3]
            d.point([(sx, yy - 2), (sx + 1, yy - 2), (sx + 2, yy - 2)], fill=c)
            e.point([(sx, yy - 2), (sx + 1, yy - 2), (sx + 2, yy - 2)], fill=CLEAR)
    noren(d, X + 6, 110, X + w - 7, 122, NOREN_INDIGO, "甘味处", (240, 236, 226), panels=3, img=img, e=e)
    _DYN["noren"].append((X + 6 - L.M, 110, X + w - 7 - L.M, 122))
    roof(d, X - 4, X + w + 3, 101, 107, TILE, inset=3, ridge=False, eave_shadow=(60, 48, 46))
    # red felt bench + big red parasol (nodate-gasa)
    bx0, bx1 = X + 10, X + 48
    d.rectangle([bx0, 142, bx1, 145], fill=(200, 50, 52))
    d.line([(bx0, 142), (bx1, 142)], fill=(236, 90, 84))
    for lx in (bx0 + 2, bx1 - 3):
        d.line([(lx, 146), (lx, BASE_Y - 1)], fill=WOOD.dk2)
    px = X + 56
    d.line([(px, 104), (px, BASE_Y - 1)], fill=WOOD.dark)
    for k in range(10):
        hw = 4 + k * 2.3
        d.line([(px - hw, 96 + k), (px + hw, 96 + k)], fill=(206, 58, 54) if k < 8 else (160, 40, 44))
    for k in range(-2, 3):
        d.line([(px, 96), (px + k * 9, 105)], fill=(170, 44, 44))
    d.point((px, 95), fill=(80, 40, 40))
    sign(img, X + w - 21, 110, X + w - 7, 136, "团子", vertical=True, bg=(236, 228, 210), fg=(170, 40, 40))


def _sake(L, X, w, r):
    d, e, img = L.d, L.e, L.img
    wall(d, X, 57, X + w - 1, 99, PLASTER, posts=[X, X + w - 3], seed=11)
    beam(d, X, X + w - 1, 56, WOOD)
    mushiko(d, X + 10, 66, X + w - 11, 84)
    roof(d, X - 3, X + w + 2, 44, 55, TILE, inset=9)
    boards(d, X, 107, X + w - 1, BASE_Y - 1, WOOD_D)
    post(d, X, 107, BASE_Y - 1)
    post(d, X + w - 3, 107, BASE_Y - 1)
    lattice(d, e, X + 6, 112, X + w - 7, BASE_Y - 1, lit=True, gap=2)
    noren(d, X + 20, 112, X + w - 21, 126, NOREN_INDIGO, "酒", (240, 236, 226), panels=2, img=img, e=e)
    _DYN["noren"].append((X + 20 - L.M, 112, X + w - 21 - L.M, 126))
    roof(d, X - 4, X + w + 3, 100, 106, TILE, inset=3, ridge=False, eave_shadow=(60, 48, 46))
    # sugidama (cedar ball) hanging from the eave
    cx = X + 14
    d.line([(cx, 106), (cx, 110)], fill=(60, 50, 40))
    d.ellipse([cx - 6, 110, cx + 6, 122], fill=(96, 110, 62))
    d.ellipse([cx - 5, 111, cx + 2, 117], fill=(124, 138, 78))
    # straw sake barrels (komodaru)
    for (bx, by) in ((X + w - 30, BASE_Y - 12), (X + w - 18, BASE_Y - 12), (X + w - 24, BASE_Y - 23)):
        d.rectangle([bx, by, bx + 10, by + 11], fill=(222, 210, 176), outline=(140, 120, 90))
        d.line([(bx, by + 3), (bx + 10, by + 3)], fill=(140, 120, 90))
        d.line([(bx, by + 8), (bx + 10, by + 8)], fill=(140, 120, 90))
        d.rectangle([bx + 3, by + 4, bx + 7, by + 7], fill=(180, 40, 40))
    sign(img, X + w - 20, 60, X + w - 6, 86, "銘酒", vertical=True, bg=(60, 50, 44), fg=(236, 220, 160),
         border=(30, 24, 24))


def _host(L, X, w, r):
    d, e, img = L.d, L.e, L.img
    top = 26
    d.rectangle([X, top, X + w - 1, BASE_Y - 1], fill=(62, 50, 74))
    d.line([(X, top), (X, BASE_Y - 1)], fill=(92, 80, 106))
    flat_roof(d, X, X + w - 1, top, Pal((110, 96, 126), (84, 70, 100), (62, 52, 76), (44, 36, 56)))
    # vertical neon 高天原
    sx0, sy0 = X + w - 20, 32
    d.rectangle([sx0, sy0, sx0 + 14, sy0 + 42], fill=(40, 30, 50), outline=(120, 90, 140))
    text_on(img, sx0 + 8, sy0 + 3, "高天原", (170, 110, 170), e, (255, 130, 230), vertical=True)
    _DYN["neon"].append((sx0 - L.M, sy0, sx0 + 14 - L.M, sy0 + 42, 0.7))
    # star lights & window bands
    for i in range(3):
        yy = 36 + i * 22
        d.rectangle([X + 6, yy, X + w - 28, yy + 12], fill=(90, 80, 120))
        e.rectangle([X + 6, yy, X + w - 28, yy + 12], fill=(230, 150, 255, 170))
        for gx in range(X + 6, X + w - 28, 10):
            d.line([(gx, yy), (gx, yy + 12)], fill=(50, 40, 60))
            e.line([(gx, yy), (gx, yy + 12)], fill=CLEAR)
    for k in range(6):
        sx = X + 8 + k * 14
        neon_tube(d, e, [(sx, 102), (sx + 2, 99), (sx + 4, 102), (sx + 2, 105), (sx, 102)], (255, 220, 120))
    # entrance with gold frame + host posters
    d.rectangle([X + 34, 110, X + 66, BASE_Y - 1], fill=(200, 170, 80))
    d.rectangle([X + 36, 112, X + 64, BASE_Y - 1], fill=(40, 30, 50))
    e.rectangle([X + 37, 113, X + 63, BASE_Y - 1], fill=(255, 190, 240, 200))
    d.line([(X + 50, 112), (X + 50, BASE_Y - 1)], fill=(200, 170, 80))
    e.line([(X + 50, 112), (X + 50, BASE_Y - 1)], fill=CLEAR)
    for i, px in enumerate((X + 6, X + 18, X + 72, X + 84)):
        d.rectangle([px, 114, px + 9, 130], fill=(230, 220, 236), outline=(200, 170, 80))
        hair = [(240, 230, 120), (60, 50, 60), (200, 120, 60), (240, 240, 250)][i]
        d.ellipse([px + 2, 116, px + 7, 122], fill=(250, 214, 186))
        d.rectangle([px + 2, 116, px + 7, 118], fill=hair)
        d.rectangle([px + 2, 124, px + 7, 129], fill=(40, 36, 48))


def _sento(L, X, w, r):
    d, e, img = L.d, L.e, L.img
    # tall chimney behind
    cx = X + w - 22
    d.rectangle([cx, 2, cx + 7, 60], fill=(150, 124, 110))
    d.line([(cx, 2), (cx, 60)], fill=(176, 150, 132))
    d.line([(cx + 7, 2), (cx + 7, 60)], fill=(120, 96, 88))
    for yy in range(8, 60, 10):
        d.line([(cx, yy), (cx + 7, yy)], fill=(120, 96, 88))
    d.rectangle([cx - 1, 2, cx + 8, 4], fill=(90, 80, 80))
    _DYN["smoke"].append((cx + 4 - L.M, 0, (210, 210, 216)))
    wall(d, X, 57, X + w - 1, 106, PLASTER, posts=[X, X + w - 3], seed=13)
    for wx in range(X + 10, X + w - 16, 22):
        shoji(d, e, wx, 66, wx + 14, 84, cols=2, rows=3)
    roof(d, X - 3, X + w + 2, 42, 56, TILE, inset=10)
    boards(d, X, 107, X + w - 1, BASE_Y - 1, WOOD_D)
    post(d, X, 107, BASE_Y - 1)
    post(d, X + w - 3, 107, BASE_Y - 1)
    # entrance with a karahafu (curved gable) roof
    ex0, ex1 = X + 22, X + w - 22
    d.rectangle([ex0, 112, ex1, BASE_Y - 1], fill=(60, 44, 40))
    glow_rect(e, ex0 + 1, 113, ex1 - 1, BASE_Y - 1, GLOW, 230)
    mid = (ex0 + ex1) // 2
    noren(d, ex0 + 1, 112, mid - 1, 128, NOREN_INDIGO, "男", (240, 236, 226), panels=2, img=img, e=e)
    noren(d, mid + 1, 112, ex1 - 1, 128, NOREN_RED, "女", (250, 236, 226), panels=2, img=img, e=e)
    _DYN["noren"].append((ex0 + 1 - L.M, 112, ex1 - 1 - L.M, 128))
    roof(d, X - 4, X + w + 3, 100, 106, TILE, inset=3, ridge=False)
    hw = (ex1 - ex0) // 2 + 8
    for k in range(12):
        f = k / 11.0
        yy = 98 + k
        half = int(hw * (0.35 + 0.65 * math.sqrt(f)))
        lift = int(round(2 * math.sin(f * math.pi)))
        d.line([(mid - half, yy - lift), (mid + half, yy - lift)], fill=TILE.mid if k < 10 else TILE.dk2)
    d.line([(mid - hw, 109), (mid + hw, 109)], fill=TILE.dk2)
    d.ellipse([mid - 8, 100, mid + 8, 110], fill=(220, 210, 190))
    text_on(img, mid + 1, 105, "ゆ", (40, 60, 120))


def _pawn(L, X, w, r):
    d, e, img = L.d, L.e, L.img
    # kura storehouse: white plaster + namako (diamond tile) lower wall
    wall(d, X, 50, X + w - 1, BASE_Y - 1, PLASTER, texture=False)
    for yy in range(120, BASE_Y, 6):
        for xx in range(X + (yy // 6 % 2) * 3, X + w, 6):
            d.polygon([(xx, yy), (xx + 3, yy - 3), (xx + 6, yy), (xx + 3, yy + 3)], outline=(150, 150, 156), fill=(90, 94, 104))
    d.line([(X, 118), (X + w - 1, 118)], fill=(120, 120, 126))
    roof(d, X - 5, X + w + 4, 38, 49, TILE, inset=8)
    # barred window + circle sign 質
    d.rectangle([X + 12, 62, X + 30, 80], fill=(40, 36, 40))
    for bx in range(X + 14, X + 30, 4):
        d.line([(bx, 62), (bx, 80)], fill=(120, 120, 126))
    d.ellipse([X + w - 34, 60, X + w - 12, 82], fill=(40, 40, 50), outline=(200, 190, 170))
    text_on(img, X + w - 22, 72, "质", (236, 230, 214))
    # heavy door
    d.rectangle([X + w // 2 - 16, 110, X + w // 2 + 14, BASE_Y - 1], fill=(64, 58, 60))
    d.rectangle([X + w // 2 - 16, 110, X + w // 2 + 14, BASE_Y - 1], outline=(30, 28, 32))
    d.line([(X + w // 2 - 1, 110), (X + w // 2 - 1, BASE_Y - 1)], fill=(30, 28, 32))
    noren(d, X + w // 2 - 14, 112, X + w // 2 + 12, 126, NOREN_INDIGO, "质", (240, 236, 226), panels=2, img=img, e=e)
    _DYN["noren"].append((X + w // 2 - 14 - L.M, 112, X + w // 2 + 12 - L.M, 126))
    roof(d, X - 4, X + w + 3, 102, 108, TILE, inset=3, ridge=False)


def _alley(L, X, w, r, pole=True):
    d, e = L.d, L.e
    d.rectangle([X, 30, X + w - 1, BASE_Y - 1], fill=(44, 38, 50))
    d.rectangle([X, 30, X + 1, BASE_Y - 1], fill=(34, 30, 40))
    # clutter: trash bin / crates
    d.rectangle([X + 2, BASE_Y - 10, X + 9, BASE_Y - 1], fill=(90, 110, 100))
    d.line([(X + 2, BASE_Y - 10), (X + 9, BASE_Y - 10)], fill=(130, 150, 140))
    if pole:
        px = X + w // 2
        _DYN["poles"].append(px - L.M)


def _pole(d, px, top=14):
    """Wooden/concrete utility pole with crossbars and insulators."""
    d.rectangle([px - 2, top, px + 2, BASE_Y + 3], fill=(120, 116, 112))
    d.line([(px - 2, top), (px - 2, BASE_Y + 3)], fill=(150, 146, 140))
    d.line([(px + 2, top), (px + 2, BASE_Y + 3)], fill=(84, 80, 80))
    for k, yy in enumerate((top + 6, top + 14)):
        d.rectangle([px - 12 + k * 2, yy, px + 12 - k * 2, yy + 1], fill=(96, 92, 90))
        for ix in (px - 10 + k * 2, px + 9 - k * 2):
            d.rectangle([ix, yy - 2, ix + 1, yy - 1], fill=(220, 220, 214))
    d.rectangle([px + 3, top + 22, px + 9, top + 32], fill=(110, 116, 110))    # transformer
    d.line([(px - 2, BASE_Y - 30), (px + 2, BASE_Y - 30)], fill=(220, 200, 60))   # hazard band
    d.line([(px - 2, BASE_Y - 28), (px + 2, BASE_Y - 28)], fill=(40, 40, 40))


def _vending(d, e, x, y_base):
    d.rectangle([x, y_base - 26, x + 15, y_base - 1], fill=(200, 60, 60), outline=(90, 30, 30))
    d.rectangle([x + 2, y_base - 23, x + 13, y_base - 12], fill=(230, 236, 240))
    e.rectangle([x + 2, y_base - 23, x + 13, y_base - 12], fill=(200, 226, 250, 190))
    for k in range(4):
        for j in range(2):
            c = [(80, 160, 230), (240, 200, 60), (90, 200, 120), (250, 250, 250)][(k + j) % 4]
            d.rectangle([x + 3 + k * 3, y_base - 22 + j * 5, x + 4 + k * 3, y_base - 19 + j * 5], fill=c)
            e.rectangle([x + 3 + k * 3, y_base - 22 + j * 5, x + 4 + k * 3, y_base - 19 + j * 5], fill=c + (255,))
    d.rectangle([x + 3, y_base - 8, x + 12, y_base - 5], fill=(40, 30, 30))


# ------------------------------------------------------------------ layers
def _facade_layer():
    for k in _DYN:
        _DYN[k].clear()
    L = WrapLayer(STREET_W, _LAYER_H, margin=64)
    r = rng("kabuki")
    x = 0
    for kind, w in _LAYOUT:
        X = L.x(x)
        if kind.startswith("machiya"):
            _machiya(L, X, w, int(kind[-1]), r)
        elif kind == "yorozuya":
            _yorozuya(L, X, r)
        elif kind == "ramen":
            _ramen(L, X, w, r)
        elif kind == "pachinko":
            _pachinko(L, X, w, r)
        elif kind == "sweets":
            _sweets(L, X, w, r)
        elif kind == "sake":
            _sake(L, X, w, r)
        elif kind == "host":
            _host(L, X, w, r)
        elif kind == "sento":
            _sento(L, X, w, r)
        elif kind == "pawn":
            _pawn(L, X, w, r)
        elif kind == "alley":
            _alley(L, X, w, r)
        x += w
    # nobori banners (drawn per frame so they can flutter)
    _DYN["flags"] += [
        (_x_of("ramen") + 84, 96, (196, 52, 48), "拉面", (250, 240, 220)),
        (_x_of("pachinko") + 98, 90, (250, 214, 70), "新台", (200, 40, 40)),
        (_x_of("sweets") + 88, 96, (236, 230, 214), "团子", (190, 50, 50)),
        (_x_of("machiya1") + 4, 96, (70, 130, 90), "大卖", (250, 246, 230)),
    ]
    # street props
    _vending(L.d, L.e, L.x(_x_of("host") - 2) - 14, BASE_Y)
    _vending(L.d, L.e, L.x(_x_of("machiya2") + 100), BASE_Y)
    # red post box
    pbx = L.x(_x_of("sake") + 4)
    L.d.rectangle([pbx, BASE_Y - 18, pbx + 7, BASE_Y - 1], fill=(200, 50, 46), outline=(110, 30, 30))
    L.d.rectangle([pbx - 1, BASE_Y - 20, pbx + 8, BASE_Y - 18], fill=(170, 40, 40))
    L.d.line([(pbx + 2, BASE_Y - 14), (pbx + 5, BASE_Y - 14)], fill=(40, 20, 20))
    # utility poles + sagging wires between consecutive poles (wrapping)
    poles = sorted(_DYN["poles"])
    for px in poles:
        for off in (-STREET_W, 0, STREET_W):
            _pole(L.d, L.x(px + off))
    pp = poles + [poles[0] + STREET_W]
    for a, b in zip(pp, pp[1:]):
        for off in (-STREET_W, 0):
            for k, (yy, sag) in enumerate(((20, 10), (28, 12), (36, 9))):
                pts = []
                for i in range(0, 41):
                    f = i / 40.0
                    pts.append((L.x(a + off) + (b - a) * f, yy + sag * 4 * f * (1 - f)))
                L.d.line(pts, fill=(40, 36, 44))
    return L.finish()


def _back_row():
    """Distant amanto high-rises (parallax 0.3)."""
    P = 1024
    L = WrapLayer(P, _LAYER_H)
    d, e = L.d, L.e
    r = rng("kabuki_back")
    x = -20
    while x < P + 20:
        X = L.x(x)
        w = r.randint(22, 48)
        top = r.randint(4, 48)
        kind = r.random()
        base_c = (132, 136, 160) if kind < 0.5 else (150, 146, 164)
        d.rectangle([X, top, X + w, 150], fill=base_c)
        d.line([(X, top), (X, 150)], fill=shade(base_c, 1.12))
        d.line([(X + w, top), (X + w, 150)], fill=shade(base_c, 0.82))
        if kind < 0.25:                       # rounded / stepped top
            d.rectangle([X + 4, top - 8, X + w - 4, top], fill=base_c)
            d.ellipse([X + 6, top - 14, X + w - 6, top - 2], fill=shade(base_c, 1.05))
        elif kind < 0.5:
            d.line([(X + w // 2, top), (X + w // 2, top - 16)], fill=shade(base_c, 0.8))
            d.point((X + w // 2, top - 16), fill=(255, 80, 70))
        window_grid(d, e, X + 3, top + 4, X + w - 3, 148, 2, 3, 2, r, 0.45, tint=shade(base_c, 0.8))
        if r.random() < 0.3:                  # rooftop billboard with neon
            bw = min(w - 4, 26)
            bc = r.choice([(255, 90, 170), (90, 220, 255), (255, 220, 90)])
            d.rectangle([X + 2, top - 12, X + 2 + bw, top - 3], fill=(60, 56, 70))
            e.rectangle([X + 3, top - 11, X + 1 + bw, top - 4], fill=bc + (255,))
            d.line([(X + 6, top - 3), (X + 6, top)], fill=(80, 80, 90))
        x += w + r.randint(2, 14)
    return L.finish()


def _mid_row():
    """Rooftops & billboards just behind the street (parallax 0.55)."""
    P = 896
    L = WrapLayer(P, _LAYER_H)
    d, e, img = L.d, L.e, L.img
    r = rng("kabuki_mid")
    x = -20
    i = 0
    while x < P + 20:
        X = L.x(x)
        w = r.randint(44, 80)
        ridge = r.randint(26, 40)
        eave = ridge + 10
        wall(d, X, eave + 1, X + w, 150, PLASTER if r.random() < 0.6 else Pal(
            (150, 108, 78), (124, 88, 64), (98, 68, 52), (70, 50, 42)), texture=False, posts=[X, X + w - 3])
        for wx in range(X + 6, X + w - 12, 14):
            shoji(d, e if r.random() < 0.6 else None, wx, eave + 6, wx + 8, eave + 16, cols=2, rows=2)
        roof(d, X - 3, X + w + 3, ridge, eave, TILE if r.random() < 0.7 else TILE_B, inset=7)
        extra = i % 4
        if extra == 0:        # water tank on legs
            tx = X + w // 3
            d.line([(tx, ridge - 2), (tx, ridge - 10)], fill=(90, 90, 100))
            d.line([(tx + 10, ridge - 2), (tx + 10, ridge - 10)], fill=(90, 90, 100))
            d.rectangle([tx - 1, ridge - 20, tx + 11, ridge - 10], fill=(170, 174, 184))
            d.line([(tx - 1, ridge - 20), (tx + 11, ridge - 20)], fill=(200, 204, 214))
        elif extra == 2:      # billboard
            bx = X + 6
            txt = ["大江户", "卡拉OK", "新发售", "电视台"][(i // 4) % 4]
            d.line([(bx + 4, ridge - 2), (bx + 4, ridge - 8)], fill=(80, 80, 90))
            d.line([(bx + 38, ridge - 2), (bx + 38, ridge - 8)], fill=(80, 80, 90))
            d.rectangle([bx, ridge - 22, bx + 42, ridge - 8], fill=(236, 226, 110), outline=(80, 70, 50))
            text_on(img, bx + 22, ridge - 15, txt, (200, 50, 50), e, (255, 120, 120))
        x += w + r.randint(-4, 6)
        i += 1
    return L.finish()


def _light_pool(tod):
    """Additive warm light spilled onto the road in front of lit shopfronts."""
    _, emis = C.cached(("raw", "kabuki_facade"), _facade_layer)
    a = np.asarray(emis).astype(np.float32)
    band = a[BASE_Y - 24:BASE_Y, :, :]
    inten = (band[..., 3] / 255.0).mean(axis=0)
    k = np.ones(13, np.float32) / 13
    inten = np.convolve(inten, k, mode="same")
    hh = 30
    j = np.arange(hh, dtype=np.float32)[:, None]
    f = inten[None, :] * np.exp(-j / 9.0) * 0.55 * C.lit_amount(tod)
    q = np.floor(f * 4 + C.bayer(hh, f.shape[1])) / 4
    q = np.clip(q, 0, 0.5)[..., None]
    col = np.array((255, 190, 110), np.float32)
    return Image.fromarray((q * col).astype(np.uint8), "RGB")


def _dyn():
    C.cached(("raw", "kabuki_facade"), _facade_layer)
    return _DYN


def _facade(tod):
    return graded_layer(("kabuki_facade",), _facade_layer, tod, depth=0.0, glow_radius=3, glow_strength=0.4)


def _facade_unlit(tod):
    base, _ = C.cached(("raw", "kabuki_facade"), _facade_layer)
    return C.cached(("kabuki_unlit", tod), lambda: C.grade_rgba(base, tod))


# ------------------------------------------------------------------ per-frame decorations
def _smoke(img, sx, sy, t, col, tod, i):
    d = ImageDraw.Draw(img)
    c = C.grade_color(col, tod)
    for k in range(6):
        per = 3.0
        u = ((t / per + k / 6.0) % 1.0)
        x = sx + math.sin(u * 5 + i + k) * 3 + u * 16
        y = sy - u * 34
        rad = 1.5 + u * 5
        if u > 0.85:
            continue
        box = [x - rad, y - rad, x + rad, y + rad]
        if (k + int(t * 4)) % 5 == 0:
            continue
        d.ellipse(box, fill=mix(c, C.grade_color((160, 170, 190), tod), u * 0.6))


def _hover_car(img, x, y, t, tod):
    d = ImageDraw.Draw(img)
    body = C.grade_color((80, 150, 200), tod, 0.3)
    dk = C.grade_color((50, 90, 130), tod, 0.3)
    d.rectangle([x, y + 2, x + 13, y + 5], fill=body)
    d.rectangle([x + 3, y, x + 10, y + 2], fill=dk)
    d.point([(x + 5, y + 1), (x + 8, y + 1)], fill=(190, 230, 250))
    fl = (t * 12) % 2 < 1
    d.line([(x + 2, y + 7), (x + 11, y + 7)], fill=(120, 230, 255) if fl else (80, 170, 220))
    if tod in ("night", "dusk", "storm"):
        d.point((x + 13, y + 3), fill=(255, 250, 200))


def _gutter_strip(tod):
    """Wooden drain covers (dobu-ita) along the facade base, period 32."""
    im = Image.new("RGB", (W + 32, 4))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W + 32, 3], fill=C.grade_color((52, 46, 50), tod))
    for x in range(0, W + 32, 16):
        d.rectangle([x + 1, 0, x + 14, 2], fill=C.grade_color((104, 92, 84), tod))
        d.line([(x + 1, 0), (x + 14, 0)], fill=C.grade_color((130, 116, 104), tod))
        d.point((x + 7, 1), fill=C.grade_color((70, 62, 60), tod))
    return im


def _wet_reflection(img, t, dy):
    """Rain-soaked road: mirrored, rippling copy of the shopfronts."""
    top = BASE_Y + dy
    n = 34
    src = img.crop((0, top - n, W, top)).transpose(Image.FLIP_TOP_BOTTOM)
    dst = img.crop((0, top + 4, W, top + 4 + n))
    for y in range(n):
        off = int(round(math.sin(t * 7 + y * 0.9) * (1 + y * 0.06)))
        row = src.crop((0, y, W, y + 1))
        if off:
            row = row.transform(row.size, Image.AFFINE, (1, 0, -off, 0, 1, 0))
        a = 0.42 * (1 - y / n)
        if a > 0.02:
            drow = dst.crop((0, y, W, y + 1))
            dst.paste(Image.blend(drow, row, a), (0, y))
    img.paste(dst, (0, top + 4))


def street(img, cam_x, t, tod="day", dy=0, wet=None):
    """Kabukicho street (see module docstring). cam_x = world x of screen left.
    wet: mirror-like rainy road reflections (default: on for tod='storm')."""
    dy = int(dy)
    C.sky(img, tod, t, horizon=150 + dy)
    C.clouds(img, t, cam_x * 0.5, tod, seed=11, count=6, y0=2, y1=40 + dy)
    E.terminal(img, cam_x, t, tod, dy=dy, parallax=0.08)
    back = graded_layer(("kabuki_back",), _back_row, tod, depth=0.45, glow_radius=2, glow_strength=0.35)
    paste_layer(img, back, 1024, cam_x * 0.3, dy)
    # distant traffic: saucer + hovering cars
    E.ship(img, (t * 7 - cam_x * 0.3) % (W + 120) - 60, 16 + dy + math.sin(t) * 2, "saucer", t,
           tod=tod, haze=0.45)
    for k in range(3):
        hx = (k * 181 + t * (9 + k * 4) * (1 if k % 2 == 0 else -1) - cam_x * 0.4) % (W + 60) - 30
        _hover_car(img, hx, 30 + k * 7 + dy, t, tod)
    mid = graded_layer(("kabuki_mid",), _mid_row, tod, depth=0.22, glow_radius=2, glow_strength=0.45)
    paste_layer(img, mid, 896, cam_x * 0.55, dy)
    fac = _facade(tod)
    paste_layer(img, fac, STREET_W, cam_x, dy)
    C.stone_street(img, BASE_Y + dy, cam_x, tod)
    g = C.cached(("kabuki_gutter", tod), lambda: _gutter_strip(tod))
    o = int(math.floor(cam_x)) % 16
    img.paste(g.crop((o, 0, o + W, 4)), (0, BASE_Y + dy))
    if wet is None:
        wet = tod == "storm"
    if wet:
        _wet_reflection(img, t, dy)
    if C.lit_amount(tod) > 0.2:
        pool = C.cached(("kabuki_pool", tod), lambda: _light_pool(tod))
        o = int(math.floor(cam_x)) % STREET_W
        C.add_sprite(img, pool.crop((o, 0, o + W, pool.height)), 0, BASE_Y + 1 + dy)
    _decor(img, cam_x, t, tod, dy)


def _flag_frames(col, text, tcol, tod):
    """4 flutter frames of a nobori banner (12 x 40 cloth)."""
    from engine.text import draw_text
    w, h = 13, 30 + 6
    base = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(base)
    d.rectangle([0, 0, w - 1, h - 1], fill=col)
    d.line([(0, 0), (w - 1, 0)], fill=shade(col, 0.7))
    d.line([(w - 1, 0), (w - 1, h - 1)], fill=shade(col, 0.8))
    for i, ch in enumerate(text):
        draw_text(base, w // 2 + 1, 3 + i * 14, ch, tcol, size=12, anchor="mt")
    base = C.grade_rgba(base, tod)
    frames = []
    for ph in range(4):
        fr = Image.new("RGBA", (w + 2, h))
        for y in range(h):
            dx = int(round((math.sin(ph * math.pi / 2 + y * 0.28) + 1) * 0.5 * (y / h) * 2))
            fr.paste(base.crop((0, y, w, y + 1)), (dx, y))
        frames.append(fr)
    return frames


def _decor(img, cam_x, t, tod, dy):
    dyn = _dyn()
    lit = C.lit_amount(tod)

    def sx_of(wx):
        s = (wx - cam_x) % STREET_W
        return s if s < W + 40 else s - STREET_W

    # neon flicker: occasionally switch a sign off for a few frames
    if lit > 0.2:
        unlit = _facade_unlit(tod)
        for i, (x0, y0, x1, y1, rel) in enumerate(dyn["neon"]):
            sx = sx_of(x0)
            if sx > W or sx + (x1 - x0) < 0:
                continue
            fr = int(t * 15)
            r = rng("neonflick", i, fr // 4)
            if r.random() > rel and (fr % 3 != 0):
                crop = unlit.crop((x0 % STREET_W, y0, x0 % STREET_W + (x1 - x0) + 1, y1 + 1))
                img.paste(crop, (int(sx), y0 + dy), crop)
    # pachinko chase bulbs
    d = ImageDraw.Draw(img)
    for i, (bx, by) in enumerate(dyn["bulbs"]):
        sx = sx_of(bx)
        if -2 <= sx < W + 2 and ((i // 2 + int(t * 10)) % 3 == 0):
            d.point((sx, by + dy), fill=(255, 250, 190))
    # noren flutter (bottom rows shift sideways)
    for i, (x0, y0, x1, y1) in enumerate(dyn["noren"]):
        sx = sx_of(x0)
        if sx > W or sx + (x1 - x0) < 0:
            continue
        s = math.sin(t * 2.6 + i * 1.7)
        off = 1 if s > 0.35 else (-1 if s < -0.35 else 0)
        if off:
            box = (int(sx), y1 - 3 + dy, int(sx) + (x1 - x0) + 1, y1 + 1 + dy)
            reg = img.crop(box)
            img.paste(reg, (box[0] + off, box[1]))
    # lanterns
    for (lx, ly, col, size, txt) in dyn["lanterns"]:
        sx = sx_of(lx)
        if -20 < sx < W + 20:
            C.lantern(img, sx, ly + dy, t, color=col, tod=tod, size=size, text=txt)
    # nobori flags on poles
    pole_c = C.grade_color((70, 60, 56), tod)
    for i, (fx, fy, col, text, tcol) in enumerate(dyn["flags"]):
        sx = sx_of(fx)
        if -20 < sx < W + 20:
            frames = C.cached(("kflag", i, tod), lambda: _flag_frames(col, text, tcol, tod))
            d.line([(sx, fy - 3 + dy), (sx, BASE_Y + 1 + dy)], fill=pole_c)
            d.line([(sx, fy - 2 + dy), (sx + 13, fy - 2 + dy)], fill=pole_c)
            fr = frames[int(t * 5 + i) % 4]
            img.paste(fr, (int(sx) + 1, fy + dy), fr)
    # smoke / steam
    for i, (sx0, sy0, col) in enumerate(dyn["smoke"]):
        sx = sx_of(sx0)
        if -30 < sx < W + 10:
            _smoke(img, sx, sy0 + dy, t, col, tod, i)


# ------------------------------------------------------------------ foreground
def street_fg(img, cam_x, t, tod="day"):
    """Near-camera pole silhouettes (parallax 1.5) — draw after characters."""
    col = C.grade_color((34, 30, 40), tod)
    hi = C.grade_color((60, 56, 66), tod)
    d = ImageDraw.Draw(img)
    period = 520
    for k in range(-1, 3):
        x = int(k * period + 300 - cam_x * 1.5) % (period * 2) - 60
        if -20 < x < W + 20:
            d.rectangle([x - 5, 0, x + 5, H], fill=col)
            d.line([(x - 5, 0), (x - 5, H)], fill=hi)
            d.rectangle([x - 16, 10, x + 16, 13], fill=col)
            d.rectangle([x - 14, 26, x + 14, 28], fill=col)


# ------------------------------------------------------------------ establishing shot
def yorozuya_front(img, t, tod="day"):
    """Framed establishing shot of the Yorozuya / Snack Otose building.
    Characters: street feet at FRONT_FLOOR_Y, balcony feet at BALCONY_Y."""
    street(img, _FCAM, t, tod, dy=FRONT_DY)
    # framing: a close power pole on the left + wires
    col = C.grade_color((52, 48, 58), tod)
    hi = C.grade_color((86, 82, 92), tod)
    d = ImageDraw.Draw(img)
    x = 14
    d.rectangle([x - 4, 0, x + 4, H], fill=col)
    d.line([(x - 4, 0), (x - 4, H)], fill=hi)
    d.rectangle([x - 14, 18, x + 20, 21], fill=col)
    d.rectangle([x - 12, 34, x + 16, 36], fill=col)
    for ix in (x - 10, x + 14):
        d.rectangle([ix, 14, ix + 2, 17], fill=C.grade_color((210, 210, 204), tod))
    for (yy, sag) in ((16, 22), (20, 26)):
        pts = [(x + i * 4, yy + sag * 4 * (i / 40) * (1 - i / 40)) for i in range(41)]
        d.line(pts, fill=col)
    d.rectangle([x + 5, 104, x + 19, 156], fill=C.grade_color((236, 230, 212), tod),
                outline=C.grade_color((60, 50, 60), tod))
    from engine.text import draw_text
    for i, ch in enumerate("歌舞伎町"):
        draw_text(img, x + 13, 106 + i * 12, ch, C.grade_color((40, 40, 70), tod), size=12, anchor="mt")


def _railing_sprite(tod):
    im = Image.new("RGBA", (YOROZUYA_W, STREET_BALCONY_Y + 6))
    d = ImageDraw.Draw(im)
    _balcony(d, 0, YOROZUYA_W - 1, STREET_BALCONY_Y)
    return C.grade_rgba(im, tod)


def yorozuya_front_fg(img, t, tod="day"):
    """Balcony railing + sign drawn over characters standing at BALCONY_Y."""
    spr = C.cached(("kabuki_rail", tod), lambda: _railing_sprite(tod))
    img.paste(spr, (_YX0 - _FCAM, FRONT_DY), spr)
