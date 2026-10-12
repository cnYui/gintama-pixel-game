"""bg.yorozuya — the Yorozuya Gin-chan office interior (side view).

office(img, t, tod='day', door=0.0)
    Back wall with the framed calligraphy 「糖分」 over the window (the window
    shows the tod sky + rooftops), Gintoki's desk + chair centre-back, two
    sofas facing each other with a low table (strawberry-milk carton, Jump,
    tea) between them, CRT TV on the left, a pile of Jump magazines, wall
    clock, pendant lamp, and the sliding entrance door on the right.
    door: 0 = closed .. 1 = fully slid open (animate it for Otose's entrance;
    a dark corridor shows behind). Ambient: TV flicker, clock ticking, dust in
    the sunbeam (day), lamp glow (night), clouds/saucer passing the window.
office_fg(img, t, tod='day')
    Low table (+ props) drawn again OVER characters — call after drawing
    characters that stand/sit behind the table.
desk_fg(img, t, tod='day')
    Desk front drawn over a character sitting in Gintoki's chair
    (draw_char(..., DESK_X, DESK_SEAT_Y, 'sit') then desk_fg()).

Constants (screen coords):
    FLOOR_Y = 160        standing feet line (mid-room)
    WALL_BASE_Y = 136    where back wall meets the floor
    SOFA_L_X, SOFA_R_X   centre x of the left / right sofa seats
    SOFA_SEAT_Y = 153    y to pass to draw_char for the 'sit' pose on a sofa
                         (use SOFA_LIE_Y = 151 for 'lie' / 'sleep' on it)
    TABLE_X, TABLE_Y     centre x / top y of the low table
    MILK_POS             (x, y) bottom-centre of the strawberry-milk carton
    DESK_X, DESK_Y       desk centre x / desk-top y;  DESK_SEAT_Y = 128
    DOOR_X               centre x of the sliding door; DOOR_BOX (x, y, w, h);
                         DOOR_FEET_Y = 138 (feet of someone in the doorway)
    WINDOW_BOX           (x, y, w, h) of the window glass
    TV_BOX               (x, y, w, h) of the TV screen
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import W, H, rng, clamp
from engine.gfx import INK, shade, mix
from . import common as C
from ._draw import (Pal, WOOD, WOOD_D, PLASTER, wall, post, beam, frame, glow_rect, CLEAR)

FLOOR_Y = 160
WALL_BASE_Y = 136
SOFA_L_X, SOFA_R_X = 90, 294
SOFA_SEAT_Y = 153
SOFA_LIE_Y = 151
TABLE_X, TABLE_Y = 192, 158
MILK_POS = (206, 158)
DESK_X, DESK_Y = 192, 118
DESK_SEAT_Y = 128
DOOR_BOX = (322, 94, 30, 42)
DOOR_X = DOOR_BOX[0] + DOOR_BOX[2] // 2
DOOR_FEET_Y = 138
WINDOW_BOX = (150, 50, 84, 48)
TV_BOX = (23, 99, 22, 15)
LAMP_X = 74

WALLP = Pal((230, 214, 182), (212, 194, 160), (186, 168, 136), (156, 140, 114))
LEATHER = Pal((150, 86, 74), (116, 62, 56), (86, 44, 44), (60, 32, 34))


def _ig(tod):
    """Indoor grade: rooms are lamp-lit, so night/storm are warmer + brighter."""
    return C.indoor(tod)


# ------------------------------------------------------------------ static room
def _room(tod):
    im = Image.new("RGBA", (W, H))
    em = Image.new("RGBA", (W, H))
    d, e = ImageDraw.Draw(im), ImageDraw.Draw(em)
    # ceiling + beams
    d.rectangle([0, 0, W, 12], fill=(74, 56, 50))
    for x in range(0, W, 24):
        d.line([(x, 0), (x, 11)], fill=(60, 44, 40))
    beam(d, 0, W, 11, WOOD_D, 4)
    # back wall
    wall(d, 0, 15, W, WALL_BASE_Y - 1, WALLP, seed=21)
    for px in (0, 104, 276, 378):
        d.rectangle([px, 15, px + 5, WALL_BASE_Y], fill=WOOD.mid)
        d.line([(px, 15), (px, WALL_BASE_Y)], fill=WOOD.hi)
        d.line([(px + 5, 15), (px + 5, WALL_BASE_Y)], fill=WOOD.dark)
    beam(d, 0, W, 42, WOOD, 4)                                 # nageshi lintel
    d.rectangle([0, 112, W, WALL_BASE_Y - 4], fill=WOOD_D.mid)             # wainscot
    for x in range(0, W, 5):
        d.line([(x, 113), (x, WALL_BASE_Y - 5)], fill=WOOD_D.dark)
        d.line([(x + 1, 113), (x + 1, WALL_BASE_Y - 5)], fill=WOOD_D.hi)
    beam(d, 0, W, 110, WOOD, 3)
    d.rectangle([0, WALL_BASE_Y - 4, W, WALL_BASE_Y], fill=WOOD.dark)   # baseboard
    d.line([(0, WALL_BASE_Y - 4), (W, WALL_BASE_Y - 4)], fill=WOOD.mid)
    # window frame (glass content is pasted per tod in _window_view)
    wx, wy, ww, wh = WINDOW_BOX
    d.rectangle([wx - 4, wy - 4, wx + ww + 3, wy + wh + 5], fill=WOOD.dark)
    d.rectangle([wx - 3, wy - 3, wx + ww + 2, wy + wh + 2], fill=WOOD.mid)
    d.line([(wx - 3, wy - 3), (wx + ww + 2, wy - 3)], fill=WOOD.hi)
    d.rectangle([wx, wy, wx + ww - 1, wy + wh - 1], fill=CLEAR)
    d.rectangle([wx - 6, wy + wh + 3, wx + ww + 5, wy + wh + 5], fill=WOOD.hi)   # sill
    d.line([(wx - 6, wy + wh + 5), (wx + ww + 5, wy + wh + 5)], fill=WOOD.dk2)
    # rolled bamboo blind at the top of the window
    d.rectangle([wx - 2, wy - 2, wx + ww + 1, wy + 3], fill=(196, 170, 112))
    for x in range(wx - 2, wx + ww + 2, 2):
        d.point((x, wy + 1), fill=(160, 136, 88))
    d.line([(wx - 2, wy + 4), (wx + ww + 1, wy + 4)], fill=(120, 100, 70))
    # 糖分 calligraphy frame above the window
    fx0, fy0, fx1, fy1 = 162, 17, 222, 40
    d.rectangle([fx0, fy0, fx1, fy1], fill=(58, 38, 30))
    d.rectangle([fx0 + 2, fy0 + 2, fx1 - 2, fy1 - 2], fill=(240, 232, 208))
    d.line([(fx0, fy0), (fx1, fy0)], fill=(96, 66, 50))
    from engine.text import draw_text
    for ox in (0, 1):   # doubled stroke = brush weight
        draw_text(im, (fx0 + fx1) // 2 + ox, (fy0 + fy1) // 2 + 1, "糖分", (24, 18, 20), size=18, face="kai", anchor="mm")
    d.rectangle([fx1 - 9, fy1 - 8, fx1 - 5, fy1 - 4], fill=(200, 50, 40))       # red seal
    d.line([(fx0 + 8, fy0 - 1), ((fx0 + fx1) // 2, fy0 - 5), (fx1 - 8, fy0 - 1)], fill=(60, 50, 40))
    # wall clock (hands animated per frame)
    d.ellipse([118, 50, 136, 68], fill=(92, 62, 46))
    d.ellipse([120, 52, 134, 66], fill=(240, 236, 220))
    for a in range(12):
        ang = a / 12 * 2 * math.pi
        d.point((127 + math.sin(ang) * 6, 59 - math.cos(ang) * 6), fill=(60, 50, 50))
    # calendar near the door
    d.rectangle([292, 58, 312, 84], fill=(246, 244, 236), outline=(150, 140, 130))
    d.rectangle([292, 58, 312, 64], fill=(200, 60, 60))
    for yy in range(67, 82, 3):
        for xx in range(294, 311, 3):
            d.point((xx, yy), fill=(90, 90, 100) if xx < 308 else (200, 60, 60))
    # TV cabinet + CRT TV
    d.rectangle([14, 118, 56, WALL_BASE_Y + 2], fill=WOOD.mid)
    d.line([(14, 118), (56, 118)], fill=WOOD.hi)
    d.rectangle([17, 124, 34, WALL_BASE_Y - 1], outline=WOOD.dark)
    d.rectangle([37, 124, 53, WALL_BASE_Y - 1], outline=WOOD.dark)
    d.point([(32, 130), (39, 130)], fill=(220, 200, 120))
    d.rectangle([18, 94, 52, 118], fill=(70, 66, 72))
    d.rectangle([18, 94, 52, 95], fill=(104, 100, 108))
    tx, ty, tw, th = TV_BOX
    d.rectangle([tx - 1, ty - 1, tx + tw, ty + th], fill=(30, 30, 36))
    d.rectangle([47, 100, 50, 112], fill=(50, 48, 54))
    d.point([(48, 102), (48, 106), (48, 110)], fill=(150, 150, 150))
    d.line([(30, 94), (22, 80)], fill=(120, 120, 130))
    d.line([(38, 94), (46, 78)], fill=(120, 120, 130))
    # Gintoki's chair (behind the desk) + desk
    d.rounded_rectangle([178, 96, 206, 124], 4, fill=LEATHER.dark)
    d.rounded_rectangle([180, 97, 204, 122], 3, fill=LEATHER.mid)
    d.line([(182, 99), (182, 118)], fill=LEATHER.hi)
    _desk(d, tod)
    # bokuto leaning on the desk (洞爷湖)
    d.line([(234, 138), (244, 102)], fill=(170, 130, 80), width=2)
    d.line([(233, 138), (243, 102)], fill=(120, 86, 56))
    d.rectangle([240, 110, 245, 112], fill=(40, 40, 50))
    # pile of Jump magazines
    jcols = [(236, 200, 60), (220, 70, 60), (70, 130, 210), (240, 240, 230), (236, 200, 60), (120, 190, 90)]
    y = WALL_BASE_Y + 3
    for i, c in enumerate(jcols):
        off = (i * 3) % 5 - 2
        d.rectangle([252 + off, y - 3, 272 + off, y - 1], fill=c)
        d.line([(252 + off, y - 1), (272 + off, y - 1)], fill=shade(c, 0.6))
        y -= 3
    d.rectangle([256, y - 1, 270, y + 1], fill=(236, 200, 60))
    # potted plant in the corner
    d.rectangle([362, 124, 374, WALL_BASE_Y + 2], fill=(160, 96, 64))
    d.line([(362, 124), (374, 124)], fill=(190, 120, 80))
    for k in range(7):
        a = -math.pi / 2 + (k - 3) * 0.4
        d.line([(368, 124), (368 + math.cos(a) * 12, 124 + math.sin(a) * 14)], fill=(70, 120, 64), width=2)
        d.point((368 + math.cos(a) * 12, 124 + math.sin(a) * 14), fill=(110, 160, 90))
    # sliding door opening (dark corridor) + frame; the panel is drawn per frame
    dx, dy_, dw, dh = DOOR_BOX
    d.rectangle([dx - 3, dy_ - 4, dx + dw + 2, dy_ + dh], fill=WOOD.dark)
    d.rectangle([dx, dy_, dx + dw - 1, dy_ + dh - 1], fill=(44, 36, 38))
    d.rectangle([dx, dy_ + dh - 10, dx + dw - 1, dy_ + dh - 1], fill=(60, 48, 46))
    d.line([(dx - 3, dy_ - 4), (dx + dw + 2, dy_ - 4)], fill=WOOD.hi)
    # sofas + table (the table is re-drawn by office_fg)
    _sofa(d, SOFA_L_X, 1)
    _sofa(d, SOFA_R_X, -1)
    # pendant lamp
    lx = LAMP_X
    d.line([(lx, 15), (lx, 26)], fill=(50, 40, 40))
    d.polygon([(lx - 9, 34), (lx + 9, 34), (lx + 4, 26), (lx - 4, 26)], fill=(236, 226, 196))
    d.line([(lx - 9, 34), (lx + 9, 34)], fill=(196, 180, 150))
    d.line([(lx - 2, 27), (lx - 6, 33)], fill=(250, 244, 226))
    e.polygon([(lx - 8, 33), (lx + 8, 33), (lx + 4, 27), (lx - 4, 27)], fill=(255, 236, 190, 255))
    return im, em


def _desk(d, tod=None, fg=False):
    x0, x1 = DESK_X - 34, DESK_X + 34
    top = DESK_Y
    d.rectangle([x0 - 2, top, x1 + 2, top + 3], fill=WOOD.hi)
    d.line([(x0 - 2, top + 3), (x1 + 2, top + 3)], fill=WOOD.dark)
    d.rectangle([x0, top + 4, x1, WALL_BASE_Y + 4], fill=WOOD.mid)
    d.line([(x0, top + 4), (x0, WALL_BASE_Y + 4)], fill=WOOD.hi)
    d.line([(x1, top + 4), (x1, WALL_BASE_Y + 4)], fill=WOOD.dark)
    for yy in (top + 9, top + 15):
        d.rectangle([x0 + 4, yy, x0 + 22, yy + 4], outline=WOOD.dark)
        d.point((x0 + 13, yy + 2), fill=(220, 190, 110))
    d.rectangle([x0 + 28, top + 8, x1 - 4, WALL_BASE_Y + 1], outline=WOOD.dark)
    if not fg:
        # props on the desk: black phone, papers, jump
        d.rectangle([x0 + 4, top - 5, x0 + 14, top - 1], fill=(30, 28, 34))
        d.rectangle([x0 + 5, top - 7, x0 + 13, top - 6], fill=(40, 38, 44))
        d.point((x0 + 9, top - 3), fill=(200, 200, 200))
        d.rectangle([x1 - 22, top - 2, x1 - 8, top - 1], fill=(236, 234, 226))
        d.rectangle([x1 - 20, top - 4, x1 - 7, top - 3], fill=(236, 200, 60))


def _sofa(d, cx, facing):
    """Profile sofa; facing +1 = seat opens to the right (backrest on the left)."""
    s = facing
    back_x = cx - 30 * s
    seat_top = SOFA_SEAT_Y - 3
    xa, xb = sorted((back_x, cx + 26 * s))
    # base + feet
    d.rectangle([xa, seat_top + 8, xb, seat_top + 12], fill=LEATHER.dk2)
    for fx in (xa + 2, xb - 4):
        d.rectangle([fx, seat_top + 13, fx + 2, seat_top + 16], fill=WOOD.dk2)
    # seat cushion
    d.rounded_rectangle([xa, seat_top, xb, seat_top + 9], 3, fill=LEATHER.mid)
    d.line([(xa + 2, seat_top), (xb - 2, seat_top)], fill=LEATHER.hi)
    d.line([(xa + 3, seat_top + 9), (xb - 3, seat_top + 9)], fill=LEATHER.dark)
    # backrest
    bx0, bx1 = sorted((back_x, back_x + 11 * s))
    d.rounded_rectangle([bx0, seat_top - 30, bx1, seat_top + 9], 5, fill=LEATHER.dark)
    d.rounded_rectangle([bx0 + 1, seat_top - 29, bx1 - 1, seat_top + 6], 4, fill=LEATHER.mid)
    d.line([(bx0 + 2, seat_top - 26), (bx0 + 2, seat_top + 2)], fill=LEATHER.hi)
    for yy in (seat_top - 20, seat_top - 10):                          # tufting buttons
        d.point(((bx0 + bx1) // 2, yy), fill=LEATHER.dk2)
    # front arm (low, rounded)
    ax = cx + 26 * s
    a0, a1 = sorted((ax, ax - 7 * s))
    d.rounded_rectangle([a0, seat_top - 8, a1, seat_top + 11], 3, fill=LEATHER.dark)
    d.rounded_rectangle([a0 + 1, seat_top - 7, a1 - 1, seat_top + 8], 2, fill=LEATHER.mid)
    d.line([(a0 + 1, seat_top - 7), (a1 - 1, seat_top - 7)], fill=LEATHER.hi)


def _table_sprite(tod):
    im = Image.new("RGBA", (84, 30))
    d = ImageDraw.Draw(im)
    ox, oy = TABLE_X - 42, TABLE_Y - 10
    x0, x1 = 6, 77
    top = TABLE_Y - oy
    # legs
    for lx in (x0 + 3, x1 - 6):
        d.rectangle([lx, top + 4, lx + 3, top + 14], fill=WOOD_D.mid)
        d.line([(lx, top + 4), (lx, top + 14)], fill=WOOD_D.hi)
    d.rectangle([x0 + 6, top + 9, x1 - 6, top + 10], fill=WOOD_D.dark)
    # top (thick slab)
    d.rectangle([x0, top, x1, top + 3], fill=WOOD.mid)
    d.line([(x0, top), (x1, top)], fill=WOOD.hi)
    d.line([(x0, top + 3), (x1, top + 3)], fill=WOOD.dk2)
    # props: strawberry-milk carton, tea cup, Jump
    mx = MILK_POS[0] - ox
    d.rectangle([mx - 3, top - 9, mx + 2, top - 1], fill=(250, 214, 224))
    d.polygon([(mx - 3, top - 9), (mx - 1, top - 12), (mx + 1, top - 12), (mx + 2, top - 9)], fill=(255, 236, 240))
    d.rectangle([mx - 3, top - 6, mx + 2, top - 4], fill=(236, 110, 140))
    d.point((mx - 1, top - 5), fill=(250, 240, 120))
    d.line([(mx + 2, top - 9), (mx + 2, top - 1)], fill=(210, 170, 186))
    d.line([(mx + 1, top - 13), (mx + 3, top - 16)], fill=(250, 250, 250))          # straw
    cx = x0 + 18
    d.rectangle([cx, top - 4, cx + 4, top - 1], fill=(120, 150, 110))
    d.line([(cx, top - 4), (cx + 4, top - 4)], fill=(160, 190, 150))
    d.rectangle([x0 + 30, top - 2, x0 + 46, top - 1], fill=(236, 200, 60))
    d.line([(x0 + 30, top - 2), (x0 + 46, top - 2)], fill=(220, 70, 60))
    return C.grade_rgba(im, _ig(tod)), (ox, oy)


def _window_view(tod):
    """Sky + rooftops seen through the window (RGB, WINDOW_BOX size)."""
    wx, wy, ww, wh = WINDOW_BOX
    full = Image.new("RGB", (W, H))
    C.sky(full, tod, 0.0, horizon=200, stars=False)
    view = full.crop((wx + 90, 0, wx + 90 + ww, wh + 30)).resize((ww, wh), Image.NEAREST)
    d = ImageDraw.Draw(view)
    r = rng("winview")
    roofc = C.grade_color((96, 100, 124), tod, 0.25)
    wallc = C.grade_color((170, 160, 150), tod, 0.25)
    x = -4
    while x < ww:
        w = r.randint(14, 24)
        top = wh - r.randint(8, 15)
        d.rectangle([x, top + 4, x + w, wh], fill=wallc)
        d.polygon([(x - 3, top + 5), (x + 3, top), (x + w - 3, top), (x + w + 3, top + 5)], fill=roofc)
        if C.lit_amount(tod) > 0.3 and r.random() < 0.6:
            d.rectangle([x + 4, top + 7, x + 6, top + 9], fill=(255, 210, 140))
        x += w + 1
    # the Terminal tower far away
    tc = C.grade_color((190, 198, 214), tod, 0.35)
    d.rectangle([ww - 22, 0, ww - 19, wh - 10], fill=tc)
    d.ellipse([ww - 34, 10, ww - 7, 15], fill=tc)
    return view


def _sunbeam():
    """Dithered additive light shaft from the window to the floor (day)."""
    wx, wy, ww, wh = WINDOW_BOX
    arr = np.zeros((H, W, 3), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    top_y = wy + wh
    k = (yy - top_y) / (H - top_y)
    left = wx + k * 70
    right = wx + ww + k * 110
    inside = (yy > top_y + 4) & (xx > left) & (xx < right)
    f = np.clip(1 - k, 0, 1) * 0.5
    q = np.floor(f * 3 + C.bayer(H, W) * 0.999) / 3 * 0.35
    q = q * inside
    arr[..., 0], arr[..., 1], arr[..., 2] = q * 255, q * 230, q * 170
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGB")


def _door_panel(tod):
    dx, dy_, dw, dh = DOOR_BOX
    im = Image.new("RGBA", (dw, dh))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, dw - 1, dh - 1], fill=WOOD.mid)
    d.rectangle([2, 2, dw - 3, dh - 12], fill=(232, 226, 204))
    for x in range(2, dw - 2, 6):
        d.line([(x, 2), (x, dh - 12)], fill=WOOD.mid)
    for y in range(2, dh - 12, 7):
        d.line([(2, y), (dw - 3, y)], fill=WOOD.mid)
    d.rectangle([2, dh - 10, dw - 3, dh - 3], fill=WOOD.dark)
    d.line([(0, 0), (0, dh - 1)], fill=WOOD.hi)
    d.line([(dw - 1, 0), (dw - 1, dh - 1)], fill=WOOD.dk2)
    d.rectangle([3, dh // 2, 5, dh // 2 + 4], fill=(60, 50, 44))                # finger pull
    return C.grade_rgba(im, _ig(tod))


def _static(tod):
    im, em = C.cached(("yz_room_raw",), lambda: _room(tod))
    ig = _ig(tod)
    g = C.grade_rgba(im, ig)
    lit = 1.0 if tod in ("night", "storm") else (0.5 if tod in ("dusk", "dawn") else 0.0)
    if lit > 0:
        g = C.light_up(g, em, lit, glow_radius=3, glow_strength=0.6)
    base = Image.new("RGB", (W, H))
    wx, wy, ww, wh = WINDOW_BOX
    base.paste(_window_view(tod), (wx, wy))
    C.wood_floor(base, WALL_BASE_Y, 0, ig)
    # contact shadow along the wall base
    ImageDraw.Draw(base).line([(0, WALL_BASE_Y), (W, WALL_BASE_Y)], fill=C.grade_color((70, 50, 40), ig))
    base.paste(g, (0, 0), g)
    # soft shadows under sofas / desk on the floor
    sh = Image.new("RGBA", (W, H))
    sd = ImageDraw.Draw(sh)
    for cx in (SOFA_L_X, SOFA_R_X):
        sd.ellipse([cx - 36, SOFA_SEAT_Y + 9, cx + 36, SOFA_SEAT_Y + 17], fill=(0, 0, 0, 60))
    sd.ellipse([TABLE_X - 40, TABLE_Y + 11, TABLE_X + 40, TABLE_Y + 17], fill=(0, 0, 0, 60))
    base.paste(sh, (0, 0), sh)
    # sofas were drawn in the RGBA layer above the shadow? re-composite sofas on top
    base.paste(g, (0, 0), g)
    return base


def _lamp_glow(tod):
    return C.glow_sprite(90, (255, 190, 120), 0.75 if tod in ("night", "storm") else 0.35)


def office(img, t, tod="day", door=0.0):
    """Yorozuya office interior (see module docstring)."""
    img.paste(C.cached(("yz_static", tod), lambda: _static(tod)), (0, 0))
    wx, wy, ww, wh = WINDOW_BOX
    # --- window life: stars / passing saucer
    if tod == "night":
        d = ImageDraw.Draw(img)
        for i in range(10):
            r = rng("winstar", i)
            x, y = wx + r.randint(1, ww - 2), wy + r.randint(1, wh - 18)
            if math.sin(t * r.uniform(1, 3) + i) > -0.2:
                d.point((x, y), fill=(230, 230, 255))
    per = 11.0
    u = (t % per) / per
    if u < 0.45:
        sub = img.crop((wx, wy, wx + ww, wy + wh))
        from . import edo
        edo.ship(sub, -20 + u / 0.45 * (ww + 40), 12 + math.sin(t * 2) * 2, "saucer", t, tod=tod, haze=0.4)
        img.paste(sub, (wx, wy))
    # --- sunbeam + dust (day), lamp glow (night)
    if tod in ("day", "dawn"):
        C.add_sprite(img, C.cached(("yz_beam",), _sunbeam), 0, 0)
        d = ImageDraw.Draw(img)
        for i in range(14):
            r = rng("dust", i)
            per = r.uniform(6, 10)
            v = ((t + r.uniform(0, per)) % per) / per
            k = r.uniform(0.05, 0.9)
            y = wy + wh + 6 + k * (H - wy - wh - 10)
            x = wx + k * 70 + r.uniform(0, ww + k * 40) + math.sin(t * 0.7 + i) * 4
            y += math.sin(v * 6.28) * 3
            if (i + int(t * 3)) % 4:
                d.point((x, y), fill=(255, 246, 214))
    elif tod in ("night", "storm", "dusk"):
        g = _lamp_glow(tod)
        fl = 0 if int(t * 12) % 23 else 1
        C.add_sprite(img, g, LAMP_X - 90, 32 - 90 + fl)
    # --- TV flicker
    tx, ty, tw, th = TV_BOX
    d = ImageDraw.Draw(img)
    fr = int(t * 6)
    r = rng("tv", fr)
    base_c = r.choice([(120, 170, 220), (140, 200, 150), (220, 180, 120), (200, 130, 160)])
    d.rectangle([tx, ty, tx + tw - 1, ty + th - 1], fill=base_c)
    for k in range(4):
        bx = tx + r.randint(0, tw - 6)
        by = ty + r.randint(0, th - 4)
        d.rectangle([bx, by, bx + r.randint(2, 6), by + r.randint(1, 4)], fill=shade(base_c, r.uniform(0.6, 1.3)))
    for yy in range(ty, ty + th, 2):
        d.line([(tx, yy), (tx + tw - 1, yy)], fill=shade(base_c, 0.85))
    d.point((tx + 2, ty + 1), fill=(250, 250, 250))
    if tod in ("night", "storm"):
        C.add_sprite(img, C.glow_sprite(26, base_c, 0.6), tx + tw // 2 - 26, ty + th // 2 - 26)
    # --- clock hands
    ang = (t / 60.0) * 2 * math.pi
    d.line([(127, 59), (127 + math.sin(ang) * 5, 59 - math.cos(ang) * 5)], fill=(200, 40, 40))
    d.line([(127, 59), (127 + 3, 59 - 2)], fill=(30, 30, 30))
    # --- sliding door panel (slides left into the wall)
    dx, dy_, dw, dh = DOOR_BOX
    panel = C.cached(("yz_door", tod), lambda: _door_panel(tod))
    off = int(round(clamp(door) * (dw - 3)))
    if off > 0:
        # a slice of warm corridor light when open
        lc = C.grade_color((150, 120, 100), _ig(tod))
        d.rectangle([dx + dw - off, dy_, dx + dw - 1, dy_ + dh - 11], fill=lc)
        d.rectangle([dx + dw - off, dy_ + dh - 10, dx + dw - 1, dy_ + dh - 1], fill=shade(lc, 0.7))
    img.paste(panel, (dx - off, dy_), panel)
    if off > 0:
        # wall pocket hides the panel part that slid past the frame
        pocket = C.cached(("yz_pocket", tod), lambda: C.cached(("yz_static", tod), lambda: _static(tod)).crop(
            (dx - dw - 4, dy_ - 4, dx, dy_ + dh)))
        img.paste(pocket, (dx - dw - 4, dy_ - 4))
    office_fg(img, t, tod)


def office_fg(img, t, tod="day"):
    """Low table + props, drawn over characters behind it."""
    spr, (ox, oy) = C.cached(("yz_table", tod), lambda: _table_sprite(tod))
    img.paste(spr, (ox, oy), spr)


def _desk_fg_sprite(tod):
    im = Image.new("RGBA", (W, H))
    _desk(ImageDraw.Draw(im), tod, fg=True)
    box = (DESK_X - 37, DESK_Y, DESK_X + 38, WALL_BASE_Y + 5)
    return C.grade_rgba(im.crop(box), _ig(tod)), box


def desk_fg(img, t, tod="day"):
    """Desk front over a character sitting in the chair behind it."""
    spr, box = C.cached(("yz_desk", tod), lambda: _desk_fg_sprite(tod))
    img.paste(spr, (box[0], box[1]), spr)
