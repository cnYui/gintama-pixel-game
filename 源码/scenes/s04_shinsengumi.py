"""s04 真选组 (21.6 s) — music 'shinsengumi'.

SHOT LIST
 A   0.00– 2.50  屯所 gate: opens close on the waving 诚 flag, pulls back + tilts down to the gate
                 「真选组屯所」; Yamazaki secretly practising badminton. Narration.
 B   2.50– 6.50  Kabukicho sweets shop: Otae eats dango; Kondo's bush hops up behind her (name
                 card 近藤勋) → 「！」 she turns, world darkens, dark aura 杀气 → super punch
                 (2-tone impact frame, speed lines, 砰！！); a passer-by stares.
 B2  6.50– 8.00  Wide shot of the aftermath, tilt up as Kondo tumbles into the sky → kira star 「闪～☆」.
 C1  8.00– 9.50  Food-show insert: giant mayo bottle builds a mountain; banner 「土方特制盖饭」.
 C2  9.50–12.00  Canteen: Hijikata smoking beside the glittering mayo mountain (name card 土方十四郎).
 D  12.00–15.30  Pan to napping Okita → snap punch-in: eye-mask flips off, sadist eyes + glint
                 (name card 冲田总悟) → poof: bazooka, creepy grin → fires.
 E  15.30–17.75  Whip-pan with the shell → BOOM → smoke clears on afro Hijikata, 阿呆～ crow over
                 the silence → he leaps onto the table, pointing, red lines 「总悟你这混蛋！！」.
 E2 17.75–18.60  Okita looks away, whistling innocently.
 F  18.60–21.60  Courtyard + giant 诚 flag: Kondo drops back from the sky (bump), pose (iai draw,
                 katana on shoulder, bazooka), title 「真选组」; Okita's laser dot lands on the afro 「喂！」.
"""
import math

import numpy as np
from PIL import Image

from engine.core import (Scene, Cue, W, H, seg, lerp, clamp, ease_in, ease_out, ease_in_out,
                         ease_out_back, wave, step_frame, rng)
from engine.gfx import INK, rect, overlay_rect, paste, silhouette
from engine import fx
from engine.text import sfx_text, name_card, text_sprite, draw_text
from chars import draw_char, render_sprite
from bg import common as C, kabukicho as K, edo as E
from scenes import _s04_art as A

try:                                   # Kondo's own bush art (read-only use of chars/kondo.py)
    from chars.kondo import _bush as _kondo_bush
except Exception:                      # pragma: no cover - fallback if the helper moves
    _kondo_bush = None

# ------------------------------------------------------------------ shot boundaries
T_B, T_C1, T_C2, T_D, T_E, T_E2, T_F, T_END = 2.5, 8.0, 9.5, 12.0, 15.3, 17.75, 18.6, 21.6

# B: street
B_CAM = 258                   # street cam_x (sweets shop 甘味处 right of centre)
OTAE_X = 226
HOPS = ((3.1, 112, 138), (3.7, 138, 165), (4.3, 165, 192))
T_TURN, T_AURA, T_WIND, T_HIT = 4.9, 5.2, 5.5, 6.0
T_SKY = 6.5
T_STAR = 7.25
STAR_POS = (96, 30)

# C/D/E: canteen (world coords)
HIJ_X, HIJ_SIT_Y, HIJ_STAND_Y = 140, 151, 158
BOWL_X = 160
PILE_W, PILE_H, PILE_T = 14, 22, 4
OKI_X, OKI_NAP_X = 404, 424
FACE_X, FACE_Y = OKI_NAP_X - 7, 150         # Okita's face while napping (close-up centre)
T_PAN_END = 12.45
T_WAKE, T_MASK, T_POOF, T_FIRE = 12.85, 13.05, 13.45, 15.1
T_GRIN = 14.35
T_BOOM = T_E + 0.15
T_CLEAR = T_BOOM + 0.5                      # smoke gone -> deadpan afro hold
T_CROW = T_CLEAR + 0.02
T_RISE = 16.55
ROCKET_Y0 = 147

# F: courtyard
F_WX, F_WY = 192, 138
T_LAND, T_POSE = T_F + 0.55, T_F + 0.85
T_AIM = T_POSE + 1.0                         # Okita quietly re-aims at Hijikata (end gag)


class Cam:
    """world -> canvas offset (ox, oy), then fx.zoom by k about canvas centre."""

    def __init__(self, wx, wy, k=1.0):
        self.k = k
        self.ox, self.oy = int(round(wx - W / 2)), int(round(wy - H / 2))

    def c(self, x, y):
        return x - self.ox, y - self.oy

    def s(self, x, y):
        cx, cy = self.c(x, y)
        return (cx - W / 2) * self.k + W / 2, (cy - H / 2) * self.k + H / 2

    def apply(self, img):
        fx.zoom(img, self.k, W / 2, H / 2)


class ZCam(Cam):
    """No world offset (street drawn by cam_x); zoom k about canvas point (zx, zy)."""

    def __init__(self, k, zx, zy):
        self.k, self.ox, self.oy = k, 0, 0
        hw, hh = W / (2 * k), H / (2 * k)          # keep the zoom box inside the canvas
        self.zx, self.zy = clamp(zx, hw, W - hw), clamp(zy, hh, H - hh)

    def s(self, x, y):
        return ((x - (self.zx - W / (2 * self.k))) * self.k, (y - (self.zy - H / (2 * self.k))) * self.k)

    def apply(self, img):
        fx.zoom(img, self.k, self.zx, self.zy)


def _shake(img, t, t0, dur, amp, seed=0):
    dx, dy = fx.shake_offset(t, t0, dur, amp, seed=seed)
    fx.shift(img, dx, dy)


# ====================================================================== A: gate
def shot_gate(img, t):
    # close on the waving 诚 flag, then pull back + tilt down onto the gate
    k = ease_in_out(seg(t, 0.55, 2.0))
    dy = int(round(46 * (1 - k)))
    E.skyline(img, 0, t, "day", ships=True, near=False, dy=dy)
    A.birds(img, t, seed=4, n=3, y=26 + dy // 2)
    C.stone_street(img, 160 + dy, 0, "day")
    g = A.gate_layer()
    img.paste(g, (0, dy), g)
    A.draw_flag(img, 319, 10 + dy, t, w=44, h=30, size=20, amp=2.0)
    # Yamazaki secretly practising badminton (hits at 0.45 + 0.9 n)
    p = (t % 0.9) / 0.9
    draw_char(img, "yamazaki", 92, 160 + dy, "badminton", t, p=p)
    fx.sakura(img, t, count=10, seed=4, wind=30, fall=14)
    z0 = 2.5 - 0.15 * seg(t, 0.0, 0.55)
    z = lerp(z0, 1.0, k) + 0.05 * ease_in_out(seg(t, 2.0, T_B))
    ZCam(z, lerp(343, 192, k), lerp(64, 116, k)).apply(img)


# ====================================================================== B: stalking
def _bush_pos(t):
    x, off = HOPS[0][1], 0.0
    for (th, a, b) in HOPS:
        if t >= th + 0.24:
            x = b
        elif t >= th:
            k = (t - th) / 0.24
            x = lerp(a, b, k)
            off = -6 * 4 * k * (1 - k)
            break
    return x, off


def _b_cam(t):
    if t < T_TURN:
        k = ease_in_out(seg(t, T_B, T_TURN))
        return ZCam(lerp(1.7, 1.85, k), lerp(176, 204, k), 132)
    if t < T_HIT + 0.1:
        k = ease_out(seg(t, T_TURN, T_TURN + 0.15))
        return ZCam(lerp(1.85, 2.0, k), lerp(204, 208, k), lerp(132, 134, k))
    k = ease_out(seg(t, T_HIT + 0.1, T_SKY))
    return ZCam(lerp(2.0, 1.8, k), lerp(208, 200, k), lerp(134, 128, k))


def _silhouette(img, cid, x, y, pose, t, color, **kw):
    spr, ax, ay = render_sprite(cid, pose, t, **kw)
    paste(img, silhouette(spr, color), int(round(x - ax)), int(round(y - ay)))


def _townsman(img, t):
    """Passer-by: strolls in, stops to stare at the bush, flinches at the punch."""
    tx = min(124.0, 40 + 30 * (t - T_B))
    if tx < 124:
        draw_char(img, "townsman", tx, 156, "walk", t, variant=1)
    elif t < T_HIT:
        draw_char(img, "townsman", tx, 156, "idle", t, variant=1, expr="blink" if t % 1.3 < 0.1 else "normal")
        if t > 5.4:
            A.sweat(img, tx + 8, 124)
    elif t < T_HIT + 0.6:
        draw_char(img, "townsman", tx, 156, "shock", t, p=seg(t, T_HIT, T_HIT + 0.6), variant=1)
    else:
        draw_char(img, "townsman", tx, 156, "idle", t, expr="shock", variant=1)


def shot_street(img, t):
    cam = _b_cam(t)
    kx, hop = _bush_pos(t)
    if T_HIT <= t < T_HIT + 0.1:
        # ---- custom 2-tone impact frame: black void, white silhouettes, red punch flare
        img.paste((16, 10, 22), (0, 0, W, H))
        cx, cy = kx + 6, 140
        fx.speed_lines(img, t, cx, cy, (255, 255, 255), count=40, inner=10, seed=5)
        fx.comic_burst(img, cx + 4, cy, 16, 8, spikes=10, color=(228, 40, 56), outline=(255, 255, 255))
        _silhouette(img, "otae", OTAE_X, 160, "super_punch", t, (255, 255, 255), p=0.5, facing=-1)
        _silhouette(img, "kondo", kx - 3, 156, "hit", t, (255, 255, 255), p=0.7, facing=1)
        cam.apply(img)
        sx, sy = cam.s(kx - 16, 112)
        sfx_text(img, int(sx), int(sy), "砰！！", t, T_HIT, 0.75, size=30, angle=10)
        return
    K.street(img, B_CAM, t, "day")
    if T_AURA <= t < T_HIT:                      # the world darkens around Otae's aura
        overlay_rect(img, 0, 0, W, H, (34, 10, 50), 0.55 * ease_out(seg(t, T_AURA, T_AURA + 0.3)))
    _townsman(img, t)
    # ---- Otae (happily eating dango at the sweets shop until she notices)
    if t < T_TURN:
        draw_char(img, "otae", OTAE_X, 160, "eat", t, facing=1, props=[A.dango_prop])
    elif t < T_AURA:
        draw_char(img, "otae", OTAE_X, 160, "idle", t, facing=-1, expr="open")
    elif t < T_WIND:
        draw_char(img, "otae", OTAE_X, 160, "idle", t, facing=-1, expr="dark_smile")
    else:
        if t < T_HIT - 0.1:
            p = 0.35 * ease_out(seg(t, T_WIND, T_HIT - 0.1))
        elif t < T_HIT:
            p = lerp(0.35, 0.5, seg(t, T_HIT - 0.1, T_HIT))
        else:
            p = lerp(0.5, 1.0, seg(t, T_HIT, T_SKY))
        draw_char(img, "otae", OTAE_X, 160, "super_punch", t, p=p, facing=-1)
    # ---- Kondo
    if t < T_TURN:
        draw_char(img, "kondo", kx, 160 + hop, "stalk", t)
    elif t < T_HIT:
        pk = seg(t, T_TURN, T_TURN + 0.5)
        ex = "shock" if t < T_WIND else "cry"
        draw_char(img, "kondo", kx, 160, "shock", t, p=pk, expr=ex, shadow=False)
        _draw_bush(img, kx, 160, t, rustle=True)
        if t > T_TURN + 0.1:
            A.sweat(img, kx + 10, 126 + (step_frame(t, 8, 2)))
        if t > T_WIND:
            A.sweat(img, kx - 9, 130)
    else:
        _draw_bush(img, kx, 160, t, rustle=False)
        k = ease_out(seg(t, T_HIT + 0.1, T_HIT + 0.3))
        if k < 1:                       # blasted up-left out of frame
            x, y = lerp(kx - 3, kx - 90, k), lerp(152, 40, k)
            for i in range(1, 4):       # afterimages
                kk = max(0.0, k - i * 0.12)
                overlay_rect(img, int(lerp(kx - 3, kx - 90, kk)) - 4, int(lerp(152, 40, kk)) - 20, 8, 16,
                             (255, 255, 255), 0.25)
            draw_char(img, "kondo", x, y, "fly", t, shadow=False)
        fx.burst(img, t, T_HIT, kx + 2, 146, n=18, colors=[(104, 186, 82), (58, 132, 64), (34, 88, 52)],
                 speed=(30, 110), gravity=120, life=1.1, size=(1, 3), seed=41, spread=(180, 360))
    # ---- camera + screen-space fx
    cam.apply(img)
    if T_HIT + 0.1 <= t < T_HIT + 0.4:
        sx, sy = cam.s(kx + 4, 138)
        fx.speed_lines(img, t, sx, sy, (255, 255, 255), count=40, inner=56, seed=4,
                       alpha=1 - seg(t, T_HIT + 0.25, T_HIT + 0.4))
    sx2, sy2 = cam.s(kx - 16, 112)
    sfx_text(img, int(sx2), int(sy2), "砰！！", t, T_HIT, 0.75, size=30, angle=10)
    if T_HIT - 0.03 <= t < T_HIT:
        fx.flash(img, 0.7)
    if T_TURN <= t < T_AURA + 0.1:
        sx, sy = cam.s(OTAE_X, 114)
        sfx_text(img, int(sx), int(sy), "！", t, T_TURN, T_AURA + 0.1 - T_TURN, color=(255, 255, 255),
                 size=24, angle=0, shake=0)
        kx2, ky2 = cam.s(kx + 2, 112)
        sfx_text(img, int(kx2), int(ky2), "！？", t, T_TURN + 0.08, T_AURA + 0.1 - T_TURN - 0.08,
                 color=(120, 200, 255), size=18, angle=8, shake=0)
    if T_AURA <= t < T_WIND + 0.3:
        ax, ay = cam.s(OTAE_X + 22, 104)
        sfx_text(img, int(ax), int(ay), "杀气", t, T_AURA, 0.7, color=(214, 150, 255), size=18, angle=-6)
    _shake(img, t, T_HIT + 0.1, 0.4, 5, seed=4)
    name_card(img, t, 2.95, 2.2, "kondo", "近藤勋", "局长｜大猩猩·跟踪狂")


def _sky_path(t):
    """Screen position, scale and spin of Kondo shooting off into the sky (sky shot)."""
    p = seg(t, T_SKY, T_STAR)
    q = 1 - (1 - p) ** 2
    x = lerp(196, STAR_POS[0], q) - 26 * math.sin(math.pi * q)
    y = lerp(118, STAR_POS[1], q)
    return x, y, lerp(1.45, 0.22, q)


def _sky_dy(t):
    # dy capped at 60: kabukicho.street -> stone_street crashes when its strip height < 2 (dy >= 63)
    return int(round(60 * ease_in_out(seg(t, T_SKY + 0.05, T_STAR + 0.1))))


def shot_sky(img, t):
    """Wide shot of the street aftermath, then tilt up following Kondo until he becomes a star."""
    dy = _sky_dy(t)
    K.street(img, B_CAM, t, "day", dy=dy)
    A.birds(img, t, seed=7, n=4, y=40)
    # ---- aftermath below: the bush, the staring passer-by, Otae all smiles again
    draw_char(img, "townsman", 124, 156 + dy, "idle", t, expr="shock", variant=1)
    _draw_bush(img, HOPS[-1][2], 160 + dy, t, rustle=False)
    if t < T_SKY + 0.4:
        draw_char(img, "otae", OTAE_X, 160 + dy, "super_punch", t, p=1.0, facing=-1)
    else:
        draw_char(img, "otae", OTAE_X, 160 + dy, "idle", t, facing=-1, expr="happy")
    fx.burst(img, t, T_SKY - 0.5, HOPS[-1][2] + 2, 146 + dy, n=18,
             colors=[(104, 186, 82), (58, 132, 64), (34, 88, 52)], speed=(30, 110), gravity=120,
             life=1.1, size=(1, 3), seed=41, spread=(180, 360))
    if t < T_STAR:
        x, y, sc = _sky_path(t)
        for i in range(1, 7):                          # spiral dust trail
            te = t - i * 0.04
            if te >= T_SKY:
                px, py, ps = _sky_path(te)
                rr = max(1, int(3 * ps))
                overlay_rect(img, int(px) - rr, int(py) - 12 * ps - rr, 2 * rr, 2 * rr, (255, 255, 255),
                             0.55 - i * 0.07)
        spin = -45 * step_frame(t - T_SKY, 15)          # tumbling end over end
        draw_char(img, "kondo", x, y, "fly", t, scale=sc, rot=spin, shadow=False, expr="cry")
        if sc > 0.7:                                   # comic tears flying off
            for i in range(3):
                ph = ((t * 4 + i / 3) % 1.0)
                pset_x = x + (12 + ph * 16) * (1 if i % 2 else -1) * sc
                pset_y = y - 16 * sc - ph * 6
                rect(img, int(pset_x), int(pset_y), 2, 2, (120, 200, 255))
    A.kira_burst(img, STAR_POS[0], STAR_POS[1], t, T_STAR)
    A.twinkle_star(img, STAR_POS[0], STAR_POS[1], t, T_STAR, dur=T_C1 - T_STAR + 0.05, size=12)
    fx.sparkle(img, STAR_POS[0] + 9, STAR_POS[1] + 8, t, T_STAR + 0.2, size=3)
    fx.sparkle(img, STAR_POS[0] - 8, STAR_POS[1] - 5, t, T_STAR + 0.35, size=2)
    cam = ZCam(1.0 + 0.12 * ease_out(seg(t, T_STAR - 0.2, T_C1)), STAR_POS[0] + 50, 70)
    cam.apply(img)
    sx, sy = cam.s(STAR_POS[0] + 34, STAR_POS[1] + 12)
    sfx_text(img, int(sx), int(sy), "闪～☆", t, T_STAR + 0.08, T_C1 - T_STAR - 0.08,
             color=(255, 250, 200), size=16, angle=-8, shake=0)


def _draw_bush(img, kx, y, t, rustle):
    if _kondo_bush is None:
        rect(img, kx - 13, y - 16, 30, 16, (58, 132, 64))
        return
    b = _kondo_bush(step_frame(t, 8, 2) if rustle else 0)
    img.paste(b, (int(kx - 13), int(y - b.height)), b)


# ====================================================================== C1: mayo insert
def shot_mayo_insert(img, t):
    A.sunburst(img, 192, 150, t)
    for i in range(10):                             # drifting sparkles
        r = rng("s04ins", i)
        x = (r.uniform(0, W) + t * 12) % W
        y = r.uniform(10, 150)
        fx.sparkle(img, int(x), int(y), (t + r.random()) % 0.5, 0.0, size=3, color=(255, 240, 200))
    img.paste((150, 100, 64), (0, 184, W, H))
    rect(img, 0, 184, W, 2, (190, 134, 90))
    for x in range(-20, W, 64):
        rect(img, x + (int(t * 0) % 64), 194, 44, 1, (126, 82, 52))
    A.big_bowl(img, 192, 164)
    rev = ease_in_out(seg(t, T_C1 + 0.05, 9.0))
    top = A.mayo_pile(img, 192, 161, 106, 98, 11, reveal=max(0.02, rev))
    nozzle = min(118, top - 12) if rev < 1 else 50
    nozzle -= 220 * ease_in(seg(t, 9.02, 9.32))
    if rev < 1:
        A.mayo_stream(img, 192, nozzle + 1, top + 2, t)
    A.big_bottle(img, 192, int(nozzle), t, squeeze=rev < 1)
    if t > 9.0:
        for i, (sx, sy) in enumerate(((150, 90), (236, 70), (212, 130), (160, 128), (196, 50))):
            fx.sparkle(img, sx, sy, t, 9.0 + i * 0.08, size=5)
    # food-show banner
    if t >= 8.55:
        p = seg(t, 8.55, 8.7)
        spr = _banner()
        s = 1 + (1 - ease_out(p)) * 1.6
        if s != 1:
            spr = spr.resize((int(spr.width * s), int(spr.height * s)), Image.NEAREST)
        paste(img, spr, 192, 198, anchor="center")
        _shake(img, t, 8.55, 0.2, 3, seed=8)


_BANNER = None


def _banner():
    global _BANNER
    if _BANNER is None:
        txt = text_sprite("土方特制盖饭", (255, 255, 255), 20, "hei", outline=INK, thick=2)
        w, h = txt.width + 36, 30
        spr = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        from PIL import ImageDraw
        d = ImageDraw.Draw(spr)
        d.polygon([(0, 2), (w - 1, 2), (w - 9, h // 2), (w - 1, h - 3), (0, h - 3), (8, h // 2)],
                  fill=(200, 36, 48, 255), outline=INK + (255,))
        d.line([(10, 5), (w - 12, 5)], fill=(254, 204, 80, 255))
        d.line([(10, h - 6), (w - 12, h - 6)], fill=(254, 204, 80, 255))
        spr.alpha_composite(txt, (w // 2 - txt.width // 2, h // 2 - txt.height // 2))
        _BANNER = spr
    return _BANNER


# ====================================================================== canteen world
def _canteen(img, cam, t):
    ox, oy = cam.ox, cam.oy
    C.room_wall(img, ox, "day_in", -oy, 136 - oy, "shoji")
    # fixed strip height: bg.common._wood_strip crashes for h % 12 == 11 (71, 83, 95, 107...)
    C.wood_floor(img, 136 - oy, ox, "day_in", h=112)
    dec = A.canteen_decor()
    x0 = int(round(ox))
    c = dec.crop((x0, int(round(oy)), x0 + W, int(round(oy)) + H))
    img.paste(c, (0, 0), c)
    A.steam(img, 256 + 25 - ox, 106 - oy, t, seed=1, h=6)
    A.sunbeams(img, ox, oy, t)
    # zabuton for the napping Okita
    zx, zy = cam.c(OKI_NAP_X - 22, 160)
    rect(img, zx - 1, zy - 4, 20, 5, INK)
    rect(img, zx, zy - 3, 18, 3, (170, 60, 70))
    rect(img, zx, zy - 3, 18, 1, (206, 96, 100))


T_STOMP = 0.16          # rise-local time when Hijikata's feet slam onto the table top


def _bowl_and_pile(img, cam, t, afro, hop=0.0):
    bx, by = cam.c(BOWL_X, A.TABLE_TOP)
    by -= hop
    A.small_bowl(img, bx, by, 16, charred=afro)
    A.mayo_pile(img, bx, by - 6, PILE_W, PILE_H, PILE_T, charred=afro, t=t)
    cx, cy = cam.c(118, A.TABLE_TOP)
    A.tea_cup(img, cx, cy - hop * 0.6)


def _hijikata_block(img, cam, t, afro=False, rise=None):
    """Hijikata seated behind the table + bowl with the mayo mountain; with `rise`
    (seconds since he snapped) he leaps up onto the table and points at Sougo."""
    hx, hy = cam.c(HIJ_X, HIJ_SIT_Y)
    if rise is None:
        if afro:
            draw_char(img, "hijikata", hx, hy, "idle", t, expr="afro", legs="sit", shadow=False)
        else:
            draw_char(img, "hijikata", hx, hy, "smoke", t, legs="sit", shadow=False)
        A.table_fg(img, cam.ox, cam.oy)
        _bowl_and_pile(img, cam, t, afro)
        return
    A.table_fg(img, cam.ox, cam.oy)
    hop = 6 * math.sin(math.pi * seg(rise, T_STOMP, T_STOMP + 0.22))       # everything jumps on the stomp
    _bowl_and_pile(img, cam, t, afro, hop)
    sx, sy = cam.c(HIJ_X - 4, A.TABLE_TOP + 1)
    if rise < T_STOMP:                                                  # leap onto the table
        k = rise / T_STOMP
        x = lerp(hx, sx, k)
        y = lerp(hy, sy, k) - 16 * math.sin(math.pi * k)
        draw_char(img, "hijikata", x, y, "jump", t, p=k, expr="afro", shadow=False)
    else:
        p = lerp(0.1, 1.0, ease_out(seg(rise, T_STOMP, T_STOMP + 0.12)))
        mad = 2 * step_frame(t, 10, 2) if rise > T_STOMP + 0.3 else 0      # hopping mad
        draw_char(img, "hijikata", sx, sy - mad, "point", t, p=p, expr="afro", shadow=False)


def _canteen_cam(t):
    if t < T_D:                                     # C2: slow push on Hijikata
        return Cam(154, 130, lerp(2.3, 2.42, ease_in_out(seg(t, T_C2, T_D))))
    if t < T_WAKE:                                  # D: pan to the napping Okita
        k = ease_in_out(seg(t, T_D, T_PAN_END))
        return Cam(lerp(154, 400, k), lerp(130, 136, k), lerp(2.42, 2.0, k) + 0.1 * seg(t, T_PAN_END, T_WAKE))
    if t < T_POOF:                                  # snap punch-in on his face: the eye-mask comes off
        q = ease_out(seg(t, T_WAKE, T_WAKE + 0.1))
        return Cam(lerp(400, FACE_X + 3, q), lerp(136, FACE_Y, q),
                   lerp(2.1, 4.4, q) + 0.25 * seg(t, T_WAKE + 0.1, T_POOF))
    if t < T_E:                                     # bazooka up, slow push while he takes aim
        return Cam(400, 136, 2.0 + 0.3 * ease_in_out(seg(t, T_POOF + 0.1, T_FIRE)))
    if t < T_E2:                                    # E: whip back with the shell, punch-in on the rise
        k = ease_in_out(seg(t, T_E, T_BOOM))
        z = lerp(2.3, 2.0, k) + 0.14 * ease_in_out(seg(t, T_CLEAR, T_RISE))   # creeping push in the silence
        wx, wy = lerp(400, 156, k), 136
        if t >= T_RISE:
            q = ease_out(seg(t, T_RISE, T_RISE + 0.12))
            z = lerp(2.14, 2.6, q)
            wx, wy = lerp(156, 150, q), lerp(136, 128, q)
        return Cam(wx, wy, z)
    return Cam(404, 134, 2.2)                       # E2: Okita whistling


_ZZ_COLS = ((236, 244, 255), (60, 70, 110))      # the floating 'Z's of chars/okita.render_nap


def _no_zz(spr):
    """Okita's nap sprite without the sleep Z's (he is awake now)."""
    a = np.array(spr)
    m = np.zeros(a.shape[:2], bool)
    for c in _ZZ_COLS:
        m |= (a[..., 0] == c[0]) & (a[..., 1] == c[1]) & (a[..., 2] == c[2])
    a[m, 3] = 0
    return Image.fromarray(a, "RGBA")


def _rocket_x(t):
    return lerp(OKI_X - 26, HIJ_X + 12, ease_in(seg(t, T_FIRE, T_BOOM)))


def _rocket_y(t):
    return lerp(ROCKET_Y0, 139, seg(t, T_FIRE, T_BOOM))


def shot_canteen(img, t):
    cam = _canteen_cam(t)
    _canteen(img, cam, t)
    angry = t >= T_RISE and t < T_E2
    if angry:                                        # red concentration background
        overlay_rect(img, 0, 0, W, H, (150, 20, 30), 0.45)
        hx, hy = cam.c(HIJ_X, 128)
        fx.speed_lines(img, t, hx, hy, (90, 10, 20), count=50, inner=20, seed=9)
    # ---- Okita
    if t < T_E:
        if t < T_POOF:
            nx, ny = cam.c(OKI_NAP_X, 160)
            if t < T_MASK:
                draw_char(img, "okita", nx, ny, "nap", t, shadow=False)
            else:                                     # mask off: he lifts his head, sadist eyes
                tilt = int(lerp(40, 0, ease_out(seg(t, T_MASK, T_MASK + 0.1))))
                spr, ax, ay = render_sprite("okita", "nap", t, expr="sadist", tilt=tilt)
                paste(img, _no_zz(spr), int(round(nx - ax)), int(round(ny - ay)))
            if T_MASK <= t < T_MASK + 0.35:           # the eye-mask flips up and away
                k = (t - T_MASK) / 0.35
                mx, my = int(nx - 10 - 3 * k), int(ny - 11 - 14 * ease_out(k))
                rect(img, mx - 1, my - 1, 10, 5, INK)
                rect(img, mx, my, 8, 3, (206, 44, 56))
                rect(img, mx + 1, my + 1, 2, 1, (255, 255, 255))
                rect(img, mx + 5, my + 1, 2, 1, (255, 255, 255))
            if t >= T_MASK:                           # sadistic glint in the eye
                fx.sparkle(img, int(nx + 2), int(ny - 12), t, T_MASK + 0.06, size=3)
        else:
            px, py = cam.c(OKI_X, 160)
            p = 0.5 * seg(t, T_POOF, T_FIRE) if t < T_FIRE else lerp(0.5, 1.0, seg(t, T_FIRE, T_FIRE + 0.5))
            ex = "sadist" if t >= T_GRIN else None     # the creepy grin before he pulls the trigger
            draw_char(img, "okita", px, py, "bazooka", t, p=p, facing=-1, expr=ex)
            fx.smoke_puff(img, t, T_POOF, px, py - 10, size=14, seed=3, life=0.45)
            fx.sparkle(img, int(px - 20), int(py - 17), t, T_GRIN + 0.1, size=4)
    elif t >= T_E2:
        px, py = cam.c(OKI_X, 160)
        draw_char(img, "okita", px, py, "bazooka", t, p=0.3, facing=1, expr="smug")
        for i in range(4):                           # innocent whistling
            ph = ((t - T_E2) * 1.3 + i * 0.25) % 1.0
            if (t - T_E2) * 1.3 < i * 0.25:
                continue
            nx = px - 8 - ph * 14 - i * 2
            ny = py - 24 - ph * 26
            A.note(img, nx, ny + math.sin(ph * 9) * 1.5)
    # ---- Hijikata
    if t < T_BOOM:
        _hijikata_block(img, cam, t)
        if t < T_D:                                  # the mayo mountain glitters
            for i, (dx, dy) in enumerate(((3, 117), (-5, 128), (6, 134), (-2, 121))):
                sx, sy = cam.c(BOWL_X + dx, dy)
                fx.sparkle(img, int(sx), int(sy), t, 9.9 + i * 0.55, size=3)
    elif t < T_RISE:
        _hijikata_block(img, cam, t, afro=True)
    elif t < T_E2:
        _hijikata_block(img, cam, t, afro=True, rise=t - T_RISE)
        if t - T_RISE >= T_STOMP:
            vx, vy = cam.c(HIJ_X + 6, 112)
            if step_frame(t, 6, 2):
                A.vein(img, vx, vy, 1)
            else:
                A.vein(img, vx + 1, vy - 1, 1)
    # ---- rocket + explosion + smoke (canvas space)
    if T_FIRE <= t < T_BOOM:
        pts = []
        for i in range(16):
            te = T_FIRE + i * 0.02
            if te <= t:
                pts.append((*cam.c(_rocket_x(te) + 10, _rocket_y(te)), te))
        A.trail(img, pts, t, life=0.45)
        rx, ry = cam.c(_rocket_x(t), _rocket_y(t))
        A.rocket(img, rx, ry, t, facing=-1)
    if T_BOOM <= t < T_BOOM + 1.0:
        bx, by = cam.c(HIJ_X + 6, 136)
        if t < T_BOOM + 0.4:                        # fireball (cut short under the smoke)
            fx.explosion(img, t, T_BOOM, bx, by, size=30, seed=12, smoke=False)
        k = seg(t, T_BOOM + 0.1, T_CLEAR + 0.05)
        if T_BOOM + 0.1 < t and k < 1:              # billowing smoke that clears on the afro
            from PIL import ImageDraw
            d = ImageDraw.Draw(img)
            for i in range(14):
                r = rng("s04smoke", i)
                a = r.uniform(0, 2 * math.pi)
                dist = r.uniform(0, 12) + 14 * ease_out(k) * r.uniform(0.6, 1.2)
                px = bx + math.cos(a) * dist
                py = by + math.sin(a) * dist * 0.6 - k * 8
                rad = (7 + 5 * r.random()) * (1 - k) ** 0.8
                if rad > 0.6:
                    c = ((110, 102, 110), (140, 134, 142), (170, 166, 174))[i % 3]
                    d.ellipse([px - rad, py - rad, px + rad, py + rad], fill=c)
    # motion lines during the pans
    if T_D + 0.04 <= t < T_PAN_END - 0.04:
        fx.motion_lines(img, t, (255, 250, 236), count=14, direction=-1, seed=2, speed=1400)
    if T_E <= t < T_BOOM - 0.03:
        fx.motion_lines(img, t, (255, 250, 236), count=16, direction=1, seed=3, speed=1600)
    cam.apply(img)
    # ---- screen-space fx
    if T_BOOM <= t < T_BOOM + 0.06:
        fx.flash(img, 0.9)
    elif T_BOOM + 0.06 <= t < T_BOOM + 0.12:
        fx.impact_frame(img, color_hi=(255, 240, 200), color_lo=(60, 20, 20))
    sfx_text(img, 206, 70, "轰！！", t, T_BOOM + 0.02, 0.5, color=(255, 140, 40), size=32, angle=-6)
    _shake(img, t, T_BOOM, 0.6, 6, seed=12)
    if angry:
        _shake(img, t, T_RISE, 1.0, 3, seed=13)
        sfx_text(img, 300, 58, "怒", t, T_RISE + 0.05, 1.0, color=(255, 60, 60), size=34, angle=8)
    if T_FIRE <= t < T_FIRE + 0.05:
        fx.flash(img, 0.35, (255, 240, 180))
    if T_WAKE <= t < T_POOF:                         # sadist close-up: dark purple vignette
        fx.vignette(img, 0.6 * ease_out(seg(t, T_WAKE, T_MASK + 0.1)), (40, 8, 56))
        if t < T_WAKE + 0.12:
            fx.speed_lines(img, t, W // 2, H // 2, (255, 255, 255), count=30, inner=70, seed=31,
                           alpha=1 - seg(t, T_WAKE + 0.04, T_WAKE + 0.12))
    if T_CROW <= t < T_RISE:                         # awkward silence: 阿呆～ crow flies past
        k = seg(t, T_CROW, T_RISE - 0.02)
        cx = lerp(W + 16, -60, k)
        cy = 40 + 3 * math.sin(k * 9)
        A.crow(img, cx, cy, t, s=3)
        draw_text(img, cx + 32, cy - 8, "阿呆～", (40, 32, 44), size=16, outline=(255, 255, 255))
    # name cards
    name_card(img, t, 9.62, 2.2, "hijikata", "土方十四郎", "鬼之副长｜蛋黄酱狂魔")
    name_card(img, t, T_MASK + 0.05, T_E - T_MASK - 0.05, "okita", "冲田总悟", "一番队队长｜抖S王子",
              side="left")


# ====================================================================== F: final pose
def shot_pose(img, t):
    zoom = 2.0 + 0.12 * ease_in_out(seg(t, T_POSE, T_END))
    cam = Cam(F_WX, F_WY, zoom)
    ox, oy = cam.ox, cam.oy
    C.sky(img, "day", t, horizon=int(150 - oy))
    C.clouds(img, t, 0, "day", seed=6, count=6, y0=0, y1=60)
    E.skyline(img, 40, t, "day", ships=True, sky=False, near=False, dy=int(-oy + 4))
    A.light_rays(img, *cam.c(200, 60), t, alpha=0.16 if t >= T_POSE else 0.08)
    ws = A.wall_strip()
    img.paste(ws, (0, int(round(124 - oy))), ws)
    C.dirt_ground(img, int(round(158 - oy)), 0, "day", grass=0.3)
    # big 诚 flag on a tall pole behind the trio
    px, py = cam.c(142, 88)
    A.draw_flag(img, int(px), int(py), t, w=98, h=52, size=40, amp=3.0, pole_h=76,
                face="brush", speed=8.0, k=0.16)
    if T_POSE <= t < T_POSE + 0.45:                  # pose burst behind the characters
        cx, cy = cam.c(192, 136)
        fx.speed_lines(img, t, cx, cy, (255, 255, 240), count=40, inner=26, seed=21,
                       alpha=1 - seg(t, T_POSE + 0.2, T_POSE + 0.45))
    # ---- Hijikata (afro, still sooty) — iai draw on the pose
    hx, hy = cam.c(150, 160)
    if t < T_POSE:
        draw_char(img, "hijikata", hx, hy, "idle", t, facing=-1, expr="afro")
    else:
        draw_char(img, "hijikata", hx, hy, "draw", t, p=min(1.0, seg(t, T_POSE, T_POSE + 0.9)),
                  facing=-1, expr="afro")
    # ---- Okita — bazooka; after the pose he quietly turns it on Hijikata again
    kx, ky = cam.c(236, 160)
    if t < T_POSE:
        draw_char(img, "okita", kx, ky, "idle", t, facing=1)
    elif t < T_AIM:
        draw_char(img, "okita", kx, ky, "bazooka", t, p=0.2, facing=1)
    else:
        draw_char(img, "okita", kx, ky, "bazooka", t, p=0.45, facing=-1, expr="sadist")
        if t >= T_AIM + 0.4:                         # Hijikata notices
            A.sweat(img, *cam.c(162, 124))
    # ---- Kondo falls back from the sky
    gx, gy = cam.c(192, 160)
    if t < T_LAND:
        k = seg(t, T_F, T_LAND) ** 2
        y = lerp(gy - 96, gy, k)
        sw = int(4 + 10 * k)                         # growing drop shadow
        overlay_rect(img, int(gx) - sw // 2, int(gy) - 1, sw, 2, (40, 30, 20), 0.5)
        draw_char(img, "kondo", gx, y, "fly", t, shadow=False)
    elif t < T_POSE:
        draw_char(img, "kondo", gx, gy, "land", t, p=seg(t, T_LAND, T_POSE), expr="hurt")
        A.bump(img, int(gx) + 1, int(gy) - 32)
    else:
        draw_char(img, "kondo", gx, gy, "shoulder", t, facing=1, expr="smug")
        A.bump(img, int(gx) + 1, int(gy) - 32)
    fx.smoke_puff(img, t, T_LAND, gx - 8, gy - 2, size=10, seed=5, color=(214, 196, 164))
    fx.smoke_puff(img, t, T_LAND, gx + 8, gy - 2, size=10, seed=6, color=(214, 196, 164))
    fx.sakura(img, t, count=14, seed=8, wind=60, fall=10)
    cam.apply(img)
    # ---- screen-space
    if T_POSE <= t < T_POSE + 0.07:
        fx.flash(img, 0.8)
    for i, (sx, sy) in enumerate(((60, 60), (330, 40), (300, 120), (90, 130), (200, 24))):
        fx.sparkle(img, sx, sy, t, T_POSE + 0.3 + i * 0.22, size=5)
        fx.sparkle(img, sx + 10, sy + 20, t, T_POSE + 1.3 + i * 0.2, size=3)
    if t >= T_POSE + 0.05:
        p = seg(t, T_POSE + 0.05, T_POSE + 0.2)
        spr = _title()
        s = 1 + (1 - ease_out(p)) * 2.0
        if s != 1:
            spr = spr.resize((int(spr.width * s), int(spr.height * s)), Image.NEAREST)
        paste(img, spr, W // 2, 177, anchor="center")
        if t > T_POSE + 0.35:
            draw_text(img, W // 2, 205, "江户特别武装警察", (255, 236, 150), size=12, outline=INK,
                      anchor="mm")
    if t >= T_AIM + 0.15:                            # laser sight creeping onto the afro
        mx, my = cam.s(213, 143)
        tx_, ty_ = cam.s(151, 131)
        reach = ease_out(seg(t, T_AIM + 0.15, T_AIM + 0.4))
        n = int(40 * reach)
        for i in range(n):
            f = i / 40
            c = (255, 50, 50) if (i + step_frame(t, 12)) % 4 < 3 else (255, 236, 236)
            rect(img, int(lerp(mx, tx_, f)), int(lerp(my, ty_, f)), 2, 1, c)
        if reach >= 1:
            r = 2 if step_frame(t, 8, 2) else 3
            rect(img, int(tx_) - r, int(ty_) - r, 2 * r + 1, 2 * r + 1, (255, 40, 40))
            rect(img, int(tx_) - 1, int(ty_) - 1, 3, 3, (255, 220, 220))
    if t >= T_AIM + 0.4:                             # 「喂！」 Hijikata spots the red dot
        sx, sy = cam.s(140, 110)
        sfx_text(img, int(sx), int(sy), "喂！", t, T_AIM + 0.4, 2.0, color=(255, 255, 255), size=16,
                 angle=10, shake=0)
    _shake(img, t, T_LAND, 0.3, 4, seed=5)
    _shake(img, t, T_POSE + 0.05, 0.25, 3, seed=6)


_TITLE = None


def _title():
    global _TITLE
    if _TITLE is None:
        red = text_sprite("真选组", (200, 30, 44), 40, "brush", outline=INK, thick=2)
        top = text_sprite("真选组", (255, 255, 255), 40, "brush", outline=INK, thick=2)
        spr = Image.new("RGBA", (red.width + 3, red.height + 3), (0, 0, 0, 0))
        spr.alpha_composite(red, (3, 3))
        spr.alpha_composite(top, (0, 0))
        _TITLE = spr
    return _TITLE


# ====================================================================== scene
class Shinsengumi(Scene):
    id = "s04"
    title = "真选组"
    duration = T_END
    music = "shinsengumi"
    music_vol = 0.55
    subs = [
        (0.30, 2.35, None, "江户的武装警察「真选组」"),
        (2.85, 4.90, "kondo", "阿妙小姐今天也好美啊～"),
        (5.00, 6.95, "otae", "跟踪狂给我去死吧～"),
        (9.80, 11.85, "hijikata", "蛋黄酱，就是正义。"),
        (13.30, 15.28, "okita", "土方先生，去死吧。"),
        (16.62, 18.56, "hijikata", "总悟你这混蛋！！"),
    ]

    def render(self, img, t):
        if t < T_B:
            shot_gate(img, t)
        elif t < T_SKY:
            shot_street(img, t)
        elif t < T_C1:
            shot_sky(img, t)
        elif t < T_C2:
            shot_mayo_insert(img, t)
        elif t < T_F:
            shot_canteen(img, t)
        else:
            shot_pose(img, t)

    def cues(self):
        c = [
            # A gate
            Cue(0.0, "wind", vol=0.22, dur=2.5),
            Cue(0.45, "pop", vol=0.3, pitch=1.3), Cue(1.35, "pop", vol=0.3, pitch=1.3),
            Cue(2.25, "pop", vol=0.3, pitch=1.3),
            # B street
            Cue(2.5, "crowd", vol=0.22, dur=5.5),
            Cue(2.95, "whoosh", vol=0.4),
            Cue(3.1, "squeak", vol=0.35, pitch=1.2), Cue(3.7, "squeak", vol=0.35, pitch=1.3),
            Cue(4.3, "squeak", vol=0.35, pitch=1.4),
            Cue(T_TURN, "shock", vol=0.7),
            Cue(T_AURA, "aura", vol=0.7),
            Cue(T_WIND, "sweat", vol=0.5),
            Cue(T_HIT - 0.1, "whoosh", vol=0.6),
            Cue(T_HIT, "punch_big", vol=1.0), Cue(T_HIT, "impact", vol=0.7),
            Cue(T_HIT + 0.1, "fly_away", vol=0.8),
            Cue(T_SKY, "whoosh", vol=0.5, pitch=0.8),
            Cue(T_STAR, "twinkle", vol=0.8),
            # C1 insert
            Cue(8.05, "slide_up", vol=0.6),
            Cue(8.55, "shine", vol=0.7),
            Cue(9.02, "sparkle", vol=0.6),
            # C2 / D canteen
            Cue(9.62, "whoosh", vol=0.35),
            Cue(T_D, "whoosh", vol=0.5),
            Cue(T_WAKE, "whoosh", vol=0.55, pitch=1.4),
            Cue(T_MASK, "shine", vol=0.7),
            Cue(T_MASK + 0.05, "whoosh", vol=0.3),
            Cue(T_POOF, "pop", vol=0.6),
            Cue(T_POOF + 0.1, "charge", vol=0.45),
            Cue(T_GRIN + 0.1, "shine", vol=0.5, pitch=0.8),
            Cue(T_FIRE, "bazooka", vol=0.9),
            # E boom
            Cue(T_E, "whoosh", vol=0.7, pitch=1.2),
            Cue(T_BOOM, "explosion", vol=1.0),
            Cue(T_CROW, "crow", vol=0.7),
            Cue(T_RISE, "jump", vol=0.6),
            Cue(T_RISE + T_STOMP, "thud", vol=0.8), Cue(T_RISE + T_STOMP, "vein", vol=0.8),
            Cue(T_RISE + T_STOMP, "impact", vol=0.5),
            # E2 whistle
            Cue(T_E2 + 0.08, "blip", vol=0.4, pitch=2.2), Cue(T_E2 + 0.27, "blip", vol=0.4, pitch=2.6),
            Cue(T_E2 + 0.46, "blip", vol=0.4, pitch=2.4), Cue(T_E2 + 0.65, "blip", vol=0.4, pitch=2.9),
            # F pose
            Cue(T_F, "wind", vol=0.3, dur=3.0),
            Cue(T_F, "fall_whistle", vol=0.7),
            Cue(T_LAND, "thud", vol=0.9),
            Cue(T_POSE, "sting_dramatic", vol=0.8),
            Cue(T_POSE + 0.05, "impact", vol=0.5),
            Cue(T_POSE + 0.3, "shing", vol=0.6),
            Cue(T_POSE + 0.6, "sparkle", vol=0.5),
            Cue(T_AIM + 0.15, "laser", vol=0.25, pitch=1.4),
            Cue(T_AIM + 0.4, "shock", vol=0.5), Cue(T_AIM + 0.45, "sweat", vol=0.6),
        ]
        return c


SCENE = Shinsengumi()
