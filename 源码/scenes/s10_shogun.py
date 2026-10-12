"""s10 将军暗杀篇 (18 s) — music: tension -> battle (at the ambush) -> silence (eyes).

SHOT LIST
  0.00- 1.90  A  chapter_card 「将军暗杀篇」; a flock of red-eyed crows (the Naraku omen)
                 crosses the red bar, black feathers drift.
  1.90- 6.00  B  Barber-shop gag (day interior: window w/ Terminal, mirror + reflection,
                 spinning barber pole). 1.90-3.10 wide, slow push-in: Gintoki on a stool
                 lazily snips the Shogun's chonmage; name_card 德川茂茂 (1.95-4.05).
                 2.55 Gintoki yawns 「哈啊～」 (eyes shut, scissors drift up) ->
                 3.10 SNIP! (flash, 咔嚓!, zoom punch) topknot flies, lands 3.60 (bounce).
                 3.10-4.10 Gintoki frozen & pale, sweat; 3.62 a crow flaps past the window
                 「阿呆～」. 4.10-6.00 close two-shot push-in: bald-patched Shogun, gloom
                 lines, tear; Gintoki (holding the topknot) slaps it back on crooked with
                 tape at 4.66 「啪！」 + smug thumbs-up; 5.30 it slides off 「哧溜～」, falls
                 5.62 -> waterfall tears. Gintoki 「将军家的头发……」 (4.10-6.00)
  6.00- 8.60  C  Mountain pass at dusk (letterbox, parallax pan): the escort walks —
                 Kondo, Hijikata, Shogun (still botched hair), Okita, Gintoki, Shinpachi,
                 Kagura (parasol). Crows circle. 6.85 crows cry, Naraku poof onto the ridge
                 (red eyes); 7.10-7.60 they leap down around the party; everyone draws,
                 Hijikata iai 7.75. Hijikata 「是奈落！保护将军！」 (7.10-9.05)
  8.60-11.30  D  Manga-panel battle montage: P1 top (8.60) Shinsengumi — Kondo slash,
                 Hijikata iai then a smoke break, Okita's bazooka x2 (2nd wave leaps in,
                 10.40 「轰轰！！」); P2 bottom-left (9.05) Yorozuya — Kagura's umbrella gun
                 then sukonbu, Gintoki's rising slash (victim twinkles) + a lazy swat at
                 the next one 「砰！」, Shinpachi on guard (glint); P3 bottom-right (9.45)
                 Katsura cuts then deadpans with a lit bomb, Elizabeth raises 「天诛」 and
                 clubs a ninja with it 「咚！」.
                 10.95 a giant white slash cuts all panels -> white.
 11.30-14.75  E  Sunset ridge, huge red sun, dead tree w/ crows behind Oboro (closer cam). 11.53 Oboro's needles,
                 11.75 Gintoki deflects (clang); name_card 胧 (11.80-14.00); 12.05 dash,
                 12.40 CLASH (impact frame, shockwave, crows scatter); blade-lock push-in
                 with shove beats at 13.20 (Oboro) / 14.10 (Gintoki).
                 Oboro 「你还是和那时一样，白夜叉。」 (12.50-14.75)
 14.75-18.00  F  Extreme close-up of Gintoki's eyes (silence + heartbeat): 15.00 they
                 widen, pupils shrink; 15.50 subliminal flash / 15.70-16.65 Shouyou's
                 gentle smile (drawn close-up face, sepia glow, petals, smile grows);
                 16.65 trembling eyes, tears well up; 17.15-17.55
                 white-out, holds white (fade_out=0) into s11's flashback.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import (Scene, Cue, W, H, seg, lerp, clamp, ease_in, ease_out, ease_in_out,
                         ease_out_back, wave, step_frame, rng, arc)
from engine.gfx import (INK, ascii_sprite, paste, rect, overlay_rect, gradient, stamp_line, tint,
                        flip_h, scale_nearest, rotate_nearest, set_alpha, dither_mask, outline)
from engine import fx
from engine.text import draw_text, text_width, sfx_text, name_card, chapter_card, text_sprite
from chars import draw_char, render_sprite, get_def
from chars.rig import OX, OY
from bg import common as C

FLOOR_Y = 160

# ---------------------------------------------------------------- timing
T_B, T_SNIP, T_KNOT, T_CROWB, T_CU = 1.90, 3.10, 3.60, 3.62, 4.10
T_YAWN = 2.55                                   # Gintoki yawns -> careless last snip
T_STICK, T_SLIDE, T_DROP = 4.66, 5.30, 5.62     # topknot slapped back on / slides / falls
KNOT_ON_HEAD = (207, 129)
T_C, T_APPEAR, T_LEAP, T_LANDN = 6.00, 6.85, 7.10, 7.60
T_D, T_P2, T_P3, T_CUT = 8.60, 9.05, 9.45, 10.95
T_E, T_THROW, T_DEFLECT, T_DASH, T_CLASH = 11.30, 11.53, 11.75, 12.05, 12.40
T_PUSH1, T_PUSH2 = 13.20, 14.10
T_F, T_WIDEN, T_SUB, T_SHOUYOU, T_BACK, T_WHITE = 14.75, 15.00, 15.50, 15.70, 16.65, 17.15

_CACHE = {}


def _cached(key, fn):
    v = _CACHE.get(key)
    if v is None:
        v = fn()
        _CACHE[key] = v
    return v


# ================================================================ small helpers
def hand_rel(cid, arm, lean=0, bob=0, dx=0, facing=1):
    """Front-hand offset from the feet anchor for rig chars (mirrors chars.rig.compose)."""
    d = get_def(cid)
    hip_y = OY - 1 - d.leg_len
    tx = OX - d.hip[0] + lean + dx
    ty = hip_y - d.hip[1] + bob
    sx, sy = tx + d.shoulder_f[0], ty + d.shoulder_f[1]
    a = math.radians(arm)
    rx, ry = sx + math.sin(a) * d.arm_len - OX, sy + math.cos(a) * d.arm_len - OY
    return rx * facing, ry


def zoom(img, z, cx=W / 2, cy=H / 2):
    """fx.zoom with the centre clamped so the source box stays inside the canvas."""
    if z <= 1.0005:
        return
    hw, hh = W / (2 * z), H / (2 * z)
    fx.zoom(img, z, clamp(cx, hw, W - hw), clamp(cy, hh, H - hh))


def clipped(img, box, fn):
    """Run fn(sub_img, ox, oy) on a crop of img and paste it back (hard clip)."""
    x0, y0, x1, y1 = [int(v) for v in box]
    sub = img.crop((x0, y0, x1, y1))
    fn(sub, x0, y0)
    img.paste(sub, (x0, y0))


def vig_mask(strength, color=(0, 0, 0)):
    """Cached banded vignette multiplier -> (k array, colour)."""
    def build():
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        k = np.clip((d - 0.7) / 0.7, 0, 1) * strength * 4
        # ordered dither between 4 levels (NB: fx.vignette adds bool dither_mask -> 25 % checker everywhere)
        k = (np.floor(k) + ((k - np.floor(k)) > C.bayer(H, W))) / 4
        return k[..., None].astype(np.float32)
    return _cached(("vig", strength), build)


def vignette(img, strength=0.5, color=(0, 0, 0)):
    k = vig_mask(strength)
    a = np.asarray(img).astype(np.float32)
    a = a * (1 - k) + np.array(color, np.float32) * k
    img.paste(Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGB"))


def sweat_drop(img, x, y):
    x, y = int(x), int(y)
    d = ImageDraw.Draw(img)
    d.polygon([(x, y), (x - 2, y + 3), (x - 2, y + 4), (x, y + 5), (x + 2, y + 4), (x + 2, y + 3)],
              fill=(150, 210, 255), outline=INK)
    d.point((x - 1, y + 3), fill=(255, 255, 255))


# ================================================================ crows
_CROW_PERCH = """
....kk.
...kkke
..kkkkY
.kkkkk.
kkkk...
k.k.k..
"""


def perch_crow_sprite(facing=1):
    """Small perched crow silhouette (for the dead tree)."""
    def build():
        pal = {"k": (22, 18, 32), "e": (22, 18, 32), "Y": (104, 96, 110)}
        s = ascii_sprite(_CROW_PERCH, pal)
        return flip_h(s) if facing < 0 else s
    return _cached(("perch", facing), build)


CROW_C = (20, 16, 30)
_WING_TIPS = ((-4.0, -10.0), (-6.5, -6.0), (-3.0, 8.5), (-6.0, 4.5))   # up, half, down, half


def _crow_polys(x, y, s, facing, frame):
    """Crow silhouette polygons (body, head, tail, wing) + beak + eye positions."""
    f = facing

    def P(px, py):
        return (x + px * s * f, y + py * s)
    body = [P(-4.5, -0.6), P(-2, -2.2), P(2.5, -2.3), P(4.5, -1.2), P(4.2, 0.8), P(1, 1.9), P(-3, 1.4)]
    head = [P(3.2, -3.2), P(5.6, -3.4), P(6.8, -2), P(6.2, -0.4), P(4.0, 0.2)]
    tail = [P(-4, -1.0), P(-9.5, -2.4), P(-10, -0.6), P(-9.4, 1.4), P(-4, 1.2)]
    tx, ty = _WING_TIPS[frame]
    sg = 1 if ty > 0 else -1
    wing = [P(2.2, -1.2), P(tx + 3.2, ty * 0.72), P(tx + 1.6, ty - sg * 0.4), P(tx + 0.6, ty * 0.9),
            P(tx - 0.4, ty), P(tx - 1.4, ty * 0.86), P(tx - 2.6, ty * 0.62), P(-3.0, -0.2)]
    beak = [P(6.4, -2.4), P(9.2, -1.5), P(6.4, -0.8)]
    eye = P(5.2, -2.3)
    return (body, head, tail, wing), beak, eye


def draw_crow(img, x, y, t, scale=1, facing=1, phase=0.0, red=False, rim=None, flap_fps=12):
    """Procedural flapping crow centred at (x, y); scale 1 ~ 18 px long."""
    frame = step_frame(t + phase, flap_fps) % 4
    s = 0.9 * scale
    d = ImageDraw.Draw(img)
    polys, beak, eye = _crow_polys(x, y, s, facing, frame)
    if rim:
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            for pg in polys:
                d.polygon([(px + ox, py + oy) for px, py in pg], fill=rim)
    for pg in polys:
        d.polygon(pg, fill=CROW_C)
    d.polygon(beak, fill=(96, 90, 104))
    ex, ey = int(eye[0]), int(eye[1])
    d.point((ex, ey), fill=(236, 56, 66) if red else (70, 66, 86))
    if red and s > 1.4:
        d.point((ex + (1 if facing > 0 else -1), ey), fill=(255, 120, 120))


def far_crow(d, x, y, t, phase=0.0, col=(30, 24, 40)):
    up = step_frame(t + phase, 8) % 2
    x, y = int(x), int(y)
    if up:
        d.line([(x - 3, y - 2), (x, y), (x + 3, y - 2)], fill=col)
    else:
        d.line([(x - 3, y + 1), (x - 1, y), (x + 1, y), (x + 3, y + 1)], fill=col)


def circling_crows(img, t, cx, cy, n=4, r=46, seed=0, scale=1):
    for i in range(n):
        rr = rng("circ", seed, i)
        rad = r * rr.uniform(0.6, 1.1)
        sp = rr.uniform(0.35, 0.55) * (1 if i % 2 else -1)
        a = rr.uniform(0, 6.28) + t * sp * 2 * math.pi * 0.35
        x = cx + math.cos(a) * rad
        y = cy + math.sin(a) * rad * 0.35
        facing = 1 if (-math.sin(a) * sp) > 0 else -1
        draw_crow(img, x, y, t, scale, facing, phase=i * 0.13)


# ================================================================ A: chapter card
def shot_card(img, t):
    if t < 1.0:
        draw_pass_world(img, t, 0.0)
    else:   # what the card fades out onto = the first frame of the barber shot
        draw_barber_world(img, T_B)
        zoom(img, *_barber_cam(T_B))
    chapter_card(img, t, 0.0, T_B, "将军暗杀篇", "将军上洛之路，暗杀者潜伏于山道")
    if 0.25 < t < T_B - 0.2:
        # crows cross the red bar (in front of the card)
        for i in range(9):
            r = rng("cardcrow", i)
            t0 = 0.25 + r.uniform(0, 0.6)
            sp = r.uniform(330, 440)
            x = -40 + (t - t0) * sp
            if x < -40 or x > W + 40:
                continue
            y = r.uniform(78, 140) + wave(t, 1.2, 3, r.random()) - (t - t0) * r.uniform(6, 20)
            sc = (2.2, 1.6, 1.3)[i % 3]
            draw_crow(img, x, y, t, sc, 1, phase=i * 0.21, red=True, rim=(110, 44, 64), flap_fps=16)
        # black feathers drifting down
        d = ImageDraw.Draw(img)
        for i in range(6):
            r = rng("feather", i)
            t0 = 0.6 + r.uniform(0, 0.6)
            dt = t - t0
            if dt < 0:
                continue
            x = r.uniform(40, 340) + wave(dt, 0.8, 8, r.random()) + dt * 14
            y = r.uniform(60, 110) + dt * 32
            a = wave(dt, 1.1, 0.9, r.random())
            L = 3
            x1, y1 = x + math.cos(a) * L, y + math.sin(a) * L
            d.line([(x - 1, y - 1), (x1, y1)], fill=(60, 40, 64))
            d.line([(x, y), (x1, y1)], fill=(16, 12, 22))


# ================================================================ B: barber shop
_KNOT_ART = """
..oooooooo.
.oKllKKKKKo
oKKKKKkkkko
.ooKkkkooo.
...ooo.....
"""
_KNOT_PAL = {"o": INK, "K": (62, 62, 84), "k": (40, 40, 56), "l": (110, 114, 148)}

# Laid out for a 2x wide shot centred ~(200, 113) and a 3x close-up on the two heads.
CHAIR_X, SEAT_Y = 206, 149
SHOGUN_XY = (CHAIR_X, SEAT_Y + 3)
GIN_XY = (186, 148)                 # Gintoki standing on a stool
MIRROR = (236, 86, 290, 126)
WINDOW = (108, 64, 150, 104)
POLE_X, POLE_Y0, POLE_Y1 = 158, 66, 110
WALL_Y = 146
CAM_WIDE = ((198, 112), (204, 115))   # slow pan during the wide shot (zoom 2)
CAM_CU = ((200, 129), (203, 131))     # close-up pan (zoom 3)


def _barber_static():
    im = Image.new("RGB", (W, H), (0, 0, 0))
    tod = "day_in"
    C.room_wall(im, 30, tod, 0, WALL_Y, style="plaster")
    C.wood_floor(im, WALL_Y, 0, tod)
    d = ImageDraw.Draw(im)
    wood, wood_d, wood_l = (150, 98, 60), (104, 64, 40), (190, 134, 82)
    # ---- window with a view of Edo (roofs + the Terminal)
    wx0, wy0, wx1, wy1 = WINDOW
    d.rectangle([wx0 - 4, wy0 - 4, wx1 + 4, wy1 + 4], fill=INK)
    d.rectangle([wx0 - 3, wy0 - 3, wx1 + 3, wy1 + 3], fill=wood)
    gradient(im, wx0, wy0, wx1 - wx0 + 1, wy1 - wy0 + 1, (86, 146, 216), (196, 222, 240), steps=5)
    d.ellipse([wx0 + 3, wy0 + 6, wx0 + 17, wy0 + 11], fill=(244, 248, 255))
    d.ellipse([wx0 + 9, wy0 + 4, wx0 + 21, wy0 + 9], fill=(244, 248, 255))
    tx = wx0 + 30
    d.rectangle([tx - 1, wy0 + 9, tx + 1, wy1], fill=(170, 186, 212))
    d.ellipse([tx - 8, wy0 + 6, tx + 8, wy0 + 10], fill=(190, 204, 226), outline=(140, 156, 186))
    d.rectangle([tx, wy0 + 1, tx, wy0 + 6], fill=(170, 186, 212))
    r = rng("winroofs")
    x = wx0
    while x < wx1:
        w = r.randint(8, 14)
        top = wy1 - r.randint(7, 15)
        d.rectangle([x, top, x + w, wy1], fill=(122, 118, 150))
        d.polygon([(x - 2, top), (x + w // 2, top - 4), (x + w + 2, top)], fill=(92, 88, 124))
        x += w + 2
    d.rectangle([(wx0 + wx1) // 2, wy0, (wx0 + wx1) // 2, wy1], fill=wood_d)
    d.rectangle([wx0, (wy0 + wy1) // 2, wx1, (wy0 + wy1) // 2], fill=wood_d)
    d.rectangle([wx0 - 6, wy1 + 4, wx1 + 6, wy1 + 7], fill=INK)
    d.rectangle([wx0 - 5, wy1 + 4, wx1 + 5, wy1 + 6], fill=wood_l)
    # potted plant on the sill
    d.rectangle([wx0 + 2, wy1 - 1, wx0 + 8, wy1 + 4], fill=INK)
    d.rectangle([wx0 + 3, wy1, wx0 + 7, wy1 + 3], fill=(196, 96, 60))
    for dx, dy in ((-2, -6), (1, -9), (4, -7), (6, -4), (-1, -3)):
        d.ellipse([wx0 + 4 + dx, wy1 + dy, wx0 + 7 + dx, wy1 + dy + 3], fill=(70, 140, 80), outline=INK)
    # ---- price list poster
    d.rectangle([168, 70, 184, 100], fill=INK)
    d.rectangle([169, 71, 183, 99], fill=(244, 236, 214))
    for i, col in enumerate(((60, 40, 40), (60, 40, 40), (200, 60, 60))):
        x = 180 - i * 5
        for y in range(75, 96, 3):
            d.rectangle([x, y, x + 1, y + 1], fill=col)
    # ---- mirror + counter
    mx0, my0, mx1, my1 = MIRROR
    d.rectangle([mx0 - 5, my0 - 5, mx1 + 5, my1 + 5], fill=INK)
    d.rectangle([mx0 - 4, my0 - 4, mx1 + 4, my1 + 4], fill=wood)
    d.rectangle([mx0 - 4, my0 - 4, mx1 + 4, my0 - 3], fill=wood_l)
    d.rectangle([mx0 - 1, my0 - 1, mx1 + 1, my1 + 1], fill=INK)
    gradient(im, mx0, my0, mx1 - mx0 + 1, my1 - my0 + 1, (206, 226, 238), (150, 180, 204), steps=5)
    cy0 = my1 + 6
    d.rectangle([mx0 - 10, cy0, mx1 + 10, WALL_Y], fill=INK)
    d.rectangle([mx0 - 9, cy0 + 1, mx1 + 9, WALL_Y - 1], fill=wood_d)
    d.rectangle([mx0 - 9, cy0 + 1, mx1 + 9, cy0 + 2], fill=wood_l)
    for i in range(3):
        x0 = mx0 - 5 + i * 22
        d.rectangle([x0, cy0 + 5, x0 + 18, WALL_Y - 2], outline=INK, fill=wood)
        d.rectangle([x0 + 7, cy0 + 8, x0 + 11, cy0 + 8], fill=(230, 190, 90))
    items = [((236, 90, 110), 6), ((90, 170, 220), 8), ((120, 200, 140), 5)]
    x = mx0 - 6
    for col, h in items:
        d.rectangle([x, cy0 - h, x + 4, cy0], fill=INK)
        d.rectangle([x + 1, cy0 - h + 1, x + 3, cy0 - 1], fill=col)
        d.rectangle([x + 1, cy0 - h - 2, x + 3, cy0 - h], fill=INK)
        x += 7
    d.rectangle([mx1 - 12, cy0 - 5, mx1 + 6, cy0], fill=INK)
    d.rectangle([mx1 - 11, cy0 - 4, mx1 + 5, cy0 - 1], fill=(244, 244, 250))
    d.rectangle([mx1 - 11, cy0 - 3, mx1 + 5, cy0 - 3], fill=(200, 206, 224))
    # ---- sign plaque 「理发」 above the mirror
    px0, py0, px1, py1 = 243, 62, 283, 79
    d.line([(px0 + 6, py0), (px0 + 10, py0 - 8)], fill=INK)
    d.line([(px1 - 6, py0), (px1 - 10, py0 - 8)], fill=INK)
    d.rectangle([px0, py0, px1, py1], fill=INK)
    d.rectangle([px0 + 1, py0 + 1, px1 - 1, py1 - 1], fill=(236, 226, 200))
    draw_text(im, (px0 + px1) // 2, (py0 + py1) // 2 + 1, "理发", (40, 28, 30), size=16, face="brush", anchor="mm")
    # ---- hanging paper lamp
    d.line([(204, 0), (204, 50)], fill=INK)
    d.ellipse([196, 50, 212, 64], fill=INK)
    d.ellipse([197, 51, 211, 63], fill=(255, 236, 186))
    d.rectangle([197, 57, 211, 57], fill=(236, 200, 140))
    # ---- barber pole frame (stripes animated per frame)
    d.rectangle([POLE_X - 2, POLE_Y0 - 4, POLE_X + 8, POLE_Y0], fill=INK)
    d.rectangle([POLE_X - 1, POLE_Y0 - 3, POLE_X + 7, POLE_Y0 - 1], fill=(210, 214, 230))
    d.rectangle([POLE_X - 2, POLE_Y1, POLE_X + 8, POLE_Y1 + 4], fill=INK)
    d.rectangle([POLE_X - 1, POLE_Y1 + 1, POLE_X + 7, POLE_Y1 + 3], fill=(210, 214, 230))
    d.rectangle([POLE_X - 1, POLE_Y0, POLE_X + 7, POLE_Y1], fill=INK)
    # ---- stool for Gintoki
    gx, gy = GIN_XY
    d.rectangle([gx - 9, gy, gx + 9, gy + 3], fill=INK)
    d.rectangle([gx - 8, gy + 1, gx + 8, gy + 2], fill=wood_l)
    for lx in (gx - 7, gx + 5):
        d.rectangle([lx - 1, gy + 3, lx + 2, 160], fill=INK)
        d.rectangle([lx, gy + 3, lx + 1, 159], fill=wood)
    # ---- barber chair (pedestal, seat, backrest, footrest)
    cx = CHAIR_X
    chrome, chrome_d = (214, 220, 236), (140, 150, 176)
    red, red_d, red_l = (190, 50, 58), (130, 30, 44), (236, 96, 96)
    d.ellipse([cx - 16, 155, cx + 16, 161], fill=INK)
    d.ellipse([cx - 15, 156, cx + 15, 160], fill=chrome_d)
    d.rectangle([cx - 15, 157, cx + 15, 157], fill=chrome)
    d.rectangle([cx - 4, SEAT_Y + 4, cx + 4, 157], fill=INK)
    d.rectangle([cx - 3, SEAT_Y + 4, cx + 3, 157], fill=chrome_d)
    d.rectangle([cx - 2, SEAT_Y + 4, cx - 1, 157], fill=chrome)
    bx0 = cx - 14
    d.rectangle([bx0 - 1, SEAT_Y - 16, bx0 + 6, SEAT_Y + 3], fill=INK)
    d.rectangle([bx0, SEAT_Y - 15, bx0 + 5, SEAT_Y + 2], fill=red)
    d.rectangle([bx0, SEAT_Y - 15, bx0 + 1, SEAT_Y + 2], fill=red_l)
    d.rectangle([bx0 + 4, SEAT_Y - 15, bx0 + 5, SEAT_Y + 2], fill=red_d)
    d.rectangle([cx - 14, SEAT_Y - 1, cx + 16, SEAT_Y + 5], fill=INK)
    d.rectangle([cx - 13, SEAT_Y, cx + 15, SEAT_Y + 4], fill=red)
    d.rectangle([cx - 13, SEAT_Y, cx + 15, SEAT_Y], fill=red_l)
    d.rectangle([cx - 13, SEAT_Y + 4, cx + 15, SEAT_Y + 4], fill=red_d)
    d.rectangle([cx + 12, SEAT_Y + 4, cx + 14, 154], fill=INK)
    d.rectangle([cx + 12, 152, cx + 26, 155], fill=INK)
    d.rectangle([cx + 13, 153, cx + 25, 154], fill=chrome)
    return im


def _pole_stripes():
    h, w = 80, 7
    arr = np.zeros((h, w, 3), np.uint8)
    cols = [(228, 59, 68), (250, 250, 255), (40, 90, 200), (250, 250, 255)]
    for y in range(h):
        for x in range(w):
            arr[y, x] = cols[((y + x) // 3) % 4]
    arr[:, 0] = (arr[:, 0] * 0.75).astype(np.uint8)
    arr[:, -1] = (arr[:, -1] * 0.7).astype(np.uint8)
    arr[:, 2] = np.minimum(255, arr[:, 2].astype(np.int32) + 30).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def _reflection(img, t, snipped, gin_expr):
    """Mirror reflection of the Shogun + Gintoki (tinted, clipped to the glass)."""
    mx0, my0, mx1, my1 = MIRROR

    def fn(sub, ox, oy):
        glass_c = (196, 220, 236)
        ex = ("haircut_shock" if t < T_SNIP + 0.35 else "haircut") if snipped else "blink"
        s, ax, ay = render_sprite("shigeshige", "idle", t, expr=ex, facing=-1, arm_f=40)
        s = set_alpha(tint(s, glass_c, 0.35), 0.9)
        sub.paste(s, (266 - ax - ox, 128 - ay - oy), s)
        s, ax, ay = render_sprite("gintoki", "idle", t, expr=gin_expr, facing=-1, arm_f=132, bob=0)
        s = set_alpha(tint(s, glass_c, 0.42), 0.8)
        sub.paste(s, (282 - ax - ox, 122 - ay - oy), s)
        dd = ImageDraw.Draw(sub)
        for k, wdt in ((0, 3), (10, 1)):
            x = 262 + k - ox
            dd.polygon([(x, 0), (x + wdt, 0), (x + wdt - 22, my1 - oy + 1), (x - 22, my1 - oy + 1)],
                       fill=(232, 244, 250))
    clipped(img, (mx0, my0, mx1 + 1, my1 + 1), fn)


def draw_scissors(img, x, y, ang, opn):
    """Scissors with pivot at (x, y), pointing along `ang` degrees (screen, 0 = right, 90 = up)."""
    L, Hh = 7, 3
    for col, wd in ((INK, 3), ((226, 232, 244), 1)):
        for sgn in (-1, 1):
            a = math.radians(ang + sgn * opn * 18)
            stamp_line(img, (x, y), (x + math.cos(a) * L, y - math.sin(a) * L), wd, col)
    for sgn in (-1, 1):
        a = math.radians(ang + 180 - sgn * (20 + opn * 14))
        hx, hy = x + math.cos(a) * Hh, y - math.sin(a) * Hh
        stamp_line(img, (x, y), (hx, hy), 3, INK)
        stamp_line(img, (hx, hy), (hx, hy), 2, (60, 60, 80))
    stamp_line(img, (x, y), (x, y), 1, (255, 255, 255))


def _snip_times():
    return [2.0 + 0.3 * k for k in range(4)]


def _gin_barber_expr(t):
    if t >= T_CU:
        if T_STICK <= t < T_SLIDE:
            return "smug"                  # "...perfect."
        if T_SLIDE <= t < T_SLIDE + 0.3:
            return "shock"
        return "gloom"
    if t >= T_SNIP:
        return "shock"
    if T_YAWN <= t < T_SNIP:
        return "sleep"                     # careless yawn right before the fatal snip
    return "blink" if (t % 2.3) < 0.5 else "normal"


def _gin_barber_arm(t):
    """Front-arm angle of Gintoki in the barber shot."""
    if t < T_SNIP:
        closed = any(0 <= t - ts < 0.1 for ts in _snip_times())
        return 130 + (5 if closed else 0) + 14 * ease_in_out(seg(t, T_YAWN, T_SNIP - 0.05))
    if t < T_CU:
        return 134
    # close-up: holds the topknot, winds up, slaps it back on, then a proud thumbs-up arm
    if t < T_STICK - 0.17:
        return 122 + 2 * (step_frame(t, 12) % 2)         # trembling hand, holding it up
    if t < T_STICK:
        return lerp(122, 168, ease_out(seg(t, T_STICK - 0.17, T_STICK - 0.05)))
    if t < T_STICK + 0.08:
        return 150
    if t < T_SLIDE:
        return 70
    return lerp(70, 40, seg(t, T_SLIDE, T_SLIDE + 0.3))


def _knot_pose(t):
    """(x, y, rotation) of the cut topknot during the close-up gag, or None."""
    hx, hy = hand_rel("gintoki", _gin_barber_arm(t))
    gx, gy = GIN_XY
    if t < T_STICK:
        return gx + hx + 1, gy + hy - 3, 20
    if t < T_SLIDE:
        sq = 1 - seg(t, T_STICK, T_STICK + 0.1)
        return KNOT_ON_HEAD[0], KNOT_ON_HEAD[1] - 1 + sq, -24
    k = seg(t, T_SLIDE, T_DROP)
    if t < T_DROP:            # slow, humiliating slide down the side of the head
        return lerp(KNOT_ON_HEAD[0], KNOT_ON_HEAD[0] + 9, ease_in(k)), \
            lerp(KNOT_ON_HEAD[1], KNOT_ON_HEAD[1] + 6, ease_in(k)), lerp(-24, -70, ease_in(k))
    dt = t - T_DROP
    return KNOT_ON_HEAD[0] + 9 + dt * 12, KNOT_ON_HEAD[1] + 6 + 0.5 * 320 * dt * dt, -70 - dt * 300


def draw_barber_world(img, t):
    img.paste(_cached("barber", _barber_static))
    stripes = _cached("pole", _pole_stripes)
    off = int(t * 16) % 12
    img.paste(stripes.crop((0, off, 7, off + POLE_Y1 - POLE_Y0)), (POLE_X, POLE_Y0))
    snipped = t >= T_SNIP
    gin_expr = _gin_barber_expr(t)
    _reflection(img, t, snipped, gin_expr)
    # a crow flaps past the window during the awkward silence
    if T_CROWB <= t < T_CROWB + 0.6:
        k = seg(t, T_CROWB, T_CROWB + 0.55)

        def fn(sub, ox, oy):
            draw_crow(sub, lerp(WINDOW[2] + 10, WINDOW[0] - 10, k) - ox, 80 + wave(t, 3, 2) - oy, t, 1, -1)
        clipped(img, (WINDOW[0], WINDOW[1], WINDOW[2] + 1, WINDOW[3] + 1), fn)
    # --- Gintoki on the stool, scissors raised
    closed = snipped or any(0 <= t - ts < 0.1 for ts in _snip_times())
    arm = _gin_barber_arm(t)
    gx, gy = GIN_XY
    pale = 0.35 if snipped and t < T_CU else 0.0
    draw_char(img, "gintoki", gx, gy, "idle", t, expr=gin_expr, arm_f=arm, bob=0,
              flash=pale, flash_color=(210, 226, 255), shadow=False)
    hx, hy = hand_rel("gintoki", arm)
    if t < T_CU:
        sang = 22 + 8 * seg(t, T_YAWN, T_SNIP) if not snipped else 30
        draw_scissors(img, gx + hx + 1, gy + hy - 1, sang, 0.1 if closed else 1.0)
    elif T_STICK + 0.08 <= t < T_SLIDE:
        # proud thumbs-up
        tx, ty = int(gx + hx + 1), int(gy + hy - 1)
        rect(img, tx - 2, ty - 2, 5, 5, INK)                # fist
        rect(img, tx - 1, ty - 1, 3, 3, (255, 214, 180))
        rect(img, tx - 1, ty - 6, 3, 5, INK)                # thumb up
        rect(img, tx, ty - 5, 1, 4, (255, 214, 180))
    # --- the Shogun in the chair
    sx, sy = SHOGUN_XY
    if not snipped:
        sex = "blink"
    elif t < T_SNIP + 0.35:
        sex = "haircut_shock"
    else:
        sex = "haircut"
    draw_char(img, "shigeshige", sx, sy, "sit", t, expr=sex, arm_f=40, arm_b=30, shadow=False)
    # hair clippings from each snip
    d = ImageDraw.Draw(img)
    for i, ts in enumerate(_snip_times() + [T_SNIP]):
        dt = t - ts
        if dt < 0:
            continue
        for j in range(3 if ts != T_SNIP else 6):
            r = rng("clip", i, j)
            x0, y0 = 204 + r.uniform(-3, 5), 128 + r.uniform(-1, 2)
            vx = r.uniform(-14, 14)
            y = y0 + 0.5 * 220 * dt * dt - r.uniform(10, 30) * dt
            x = x0 + vx * dt
            if y > 158:
                y = 158 + (j % 2)
                x = x0 + vx * math.sqrt(max(0.0, (158 - y0) * 2 / 220))
            d.point((int(x), int(y)), fill=(40, 40, 56))
    # --- the flying topknot
    knot = _cached("knot", lambda: ascii_sprite(_KNOT_ART, _KNOT_PAL))
    if snipped and t < T_CU:
        dt = t - T_SNIP
        if t < T_KNOT:
            k = dt / (T_KNOT - T_SNIP)
            x, y = arc((207, 127), (246, 157), k, 34)
            spr = rotate_nearest(knot, -int(dt * 1100) % 360)
        else:
            bk = seg(t, T_KNOT, T_KNOT + 0.18)
            x, y = 246 + bk * 4, 157 - 4 * math.sin(bk * math.pi)
            spr = knot
        paste(img, spr, x, y, anchor="center")
        if t >= T_KNOT:
            fx.smoke_puff(img, t, T_KNOT, 246, 159, size=5, seed=3)
    # gloom lines + a single tear in the close-up
    if t >= T_CU:
        for i, lx in enumerate((198, 202, 206, 210, 214)):
            ph = step_frame(t, 6) + i * 2
            top = 104 + (i % 2) * 4
            for yy in range(top, 124):
                off = (0, 1, 1, 0)[((yy + ph) // 2) % 4]
                d.point((lx + off, yy), fill=(70, 100, 210) if (yy - top) > 4 else (130, 160, 240))
        k = seg(t, T_CU + 0.3, T_CU + 0.9)
        if k > 0 and t < T_DROP + 0.1:
            ty = int(140 + k * 8)
            d.line([(210, 140), (210, ty)], fill=(150, 214, 255))
            d.rectangle([209, ty, 210, ty + 1], fill=(120, 196, 250))
            d.point((209, ty), fill=(230, 246, 255))
        if t >= T_DROP + 0.1:
            # waterfall tears (comedic 滝涙) once the topknot falls off again
            for ex in (203, 210):
                d.rectangle([ex - 1, 139, ex, 152], fill=(120, 196, 250))
                for yy in range(139, 152):
                    if (yy + step_frame(t, 15)) % 3 == 0:
                        d.point((ex - 1, yy), fill=(230, 246, 255))
                if step_frame(t, 10) % 2:
                    d.point((ex - 3, 150), fill=(150, 214, 255))
                    d.point((ex + 2, 149), fill=(150, 214, 255))
        # the topknot: held -> slapped back on (crooked, taped) -> slides off
        kx, ky, kr = _knot_pose(t)
        spr = rotate_nearest(knot, int(kr) % 360) if kr else knot
        paste(img, spr, kx, ky, anchor="center")
        if T_STICK <= t < T_DROP:
            ix, iy = int(kx) - 1, int(ky + 2)
            for a, b in (((-3, -2), (2, 3)), ((-3, 3), (2, -2))):     # white sticky-tape "X"
                d.line([(ix + a[0], iy + a[1]), (ix + b[0], iy + b[1])], fill=(250, 248, 236))
        if T_STICK <= t < T_STICK + 0.4:
            fx.sparkle(img, KNOT_ON_HEAD[0] + 7, KNOT_ON_HEAD[1] - 6, t, T_STICK, size=4)
    if snipped and T_SNIP + 0.35 <= t < T_CU:
        sweat_drop(img, gx + 9, gy - 30 + seg(t, T_SNIP + 0.35, T_CU) * 6)
    if t >= T_CU and not (T_STICK <= t < T_SLIDE):
        sweat_drop(img, gx + 9, gy - 28 + ((t - T_CU) * 3) % 4)


def _barber_cam(t):
    if t < T_CU:
        k = ease_in_out(seg(t, T_B, T_SNIP + 0.6))
        (ax, ay), (bx, by) = CAM_WIDE
        z, cx, cy = 2.0, lerp(ax, bx, k), lerp(ay, by, k)
        if t >= T_SNIP:
            pk = math.exp(-(t - T_SNIP) * 9)
            z += 0.45 * pk
            cx, cy = lerp(cx, 206, pk), lerp(cy, 128, pk)
        return z, cx, cy
    k = ease_in_out(seg(t, T_CU, T_C))
    (ax, ay), (bx, by) = CAM_CU
    return 3.0, lerp(ax, bx, k), lerp(ay, by, k)


def _to_screen(wx, wy, cam):
    z, cx, cy = cam
    hw, hh = W / (2 * z), H / (2 * z)
    cx, cy = clamp(cx, hw, W - hw), clamp(cy, hh, H - hh)
    return (wx - cx) * z + W / 2, (wy - cy) * z + H / 2


def shot_barber(img, t):
    draw_barber_world(img, t)
    cam = _barber_cam(t)
    zoom(img, *cam)
    if T_STICK <= t < T_STICK + 0.2:     # little zoom punch on the slap
        k = 1 - seg(t, T_STICK, T_STICK + 0.2)
        sx, sy = _to_screen(*KNOT_ON_HEAD, cam)
        zoom(img, 1 + 0.08 * k, sx, sy)
    if T_YAWN + 0.05 <= t < T_SNIP:
        gx, gy = _to_screen(GIN_XY[0] - 6, GIN_XY[1] - 40, cam)
        draw_text(img, gx - 20, gy - 8 - (t - T_YAWN) * 8, "哈啊～", (255, 255, 255), size=12, outline=INK)
    if t >= T_CU:
        overlay_rect(img, 0, 0, W, 30, (40, 50, 110), 0.22)
        sfx_text(img, 250, 38, "啪！", t, T_STICK, 0.5, size=16, angle=12)
        sfx_text(img, 256, 58, "哧溜～", t, T_SLIDE + 0.05, 0.6, color=(200, 220, 255), size=12, angle=-6)
    if T_SNIP <= t < T_SNIP + 0.1:
        fx.flash(img, 0.7 * (1 - seg(t, T_SNIP, T_SNIP + 0.1)))
    if T_SNIP <= t < T_SNIP + 0.35:
        fx.speed_lines(img, t, 214, 150, (255, 255, 255), count=30, inner=60, seed=2)
    sfx_text(img, 286, 96, "咔嚓！", t, T_SNIP, 0.75, color=(255, 255, 255), size=24, angle=-10)
    if T_CROWB + 0.05 <= t < T_CU:
        k = seg(t, T_CROWB, T_CROWB + 0.55)
        sx, sy = _to_screen(lerp(WINDOW[2] + 10, WINDOW[0] - 10, k), 80, cam)
        draw_text(img, clamp(sx - 16, 2, W - 40), sy - 26, "阿呆～", (255, 255, 255), size=12, outline=INK)
    name_card(img, t, 1.95, 2.1, "shigeshige", "德川茂茂", "第十四代将军｜老实人")


# ================================================================ C: mountain pass
_MID_P = 640
_FAR_P = 512


def _ridge_curve(w, P, base, amps, seed_ph):
    xs = np.arange(w)
    ph = xs / P * 2 * np.pi
    c = np.full(w, float(base))
    for i, (f, a) in enumerate(amps):
        c += a * np.sin(ph * f + seed_ph * (i + 1))
    return np.round(c).astype(np.int32)


def _pine(d, x, base, h, col, col_l=None):
    d.rectangle([x - 1, base - 4, x + 1, base], fill=col)
    for tier in range(3):
        ty = base - 4 - tier * h // 3
        hw = (3 - tier) * h // 7 + 2
        d.polygon([(x - hw, ty), (x, ty - h // 2), (x + hw, ty)], fill=col)
        if col_l:
            d.polygon([(x - hw + 2, ty - 1), (x, ty - h // 2 + 1), (x + 1, ty - 1)], fill=col_l)


def _pass_far():
    """Hazy far ridge with pine silhouettes (parallax 0.25)."""
    P, w = _FAR_P, _FAR_P + W
    crest = _ridge_curve(w, P, 104, ((2, 6), (5, 3), (9, 1.5)), 1.3)
    col = C.grade_color((84, 96, 120), "dusk", 0.55)
    arr = np.zeros((H, w, 4), np.uint8)
    for x in range(w):
        arr[crest[x]:, x, :3] = col
        arr[crest[x]:, x, 3] = 255
    im = Image.fromarray(arr, "RGBA")
    d = ImageDraw.Draw(im)
    r = rng("farpines")
    x = 3
    while x < P:
        h = r.randint(8, 16)
        for xx in (x, x + P):
            if xx < w:
                _pine(d, xx, int(crest[min(w - 1, xx)]) + 2, h, col)
        x += r.randint(6, 16)
    return im


def _pass_mid():
    """Rocky ridge with rim-lit crest, crevices and pines (dusk graded). Returns (img, crest)."""
    P, w = _MID_P, _MID_P + W
    crest = _ridge_curve(w, P, 120, ((2, 7), (5, 4), (13, 1.5)), 0.7)
    rim = np.array(C.grade_color((250, 170, 130), "dusk"), np.float32)
    rock_l = np.array(C.grade_color((150, 122, 112), "dusk", 0.12), np.float32)
    rock = np.array(C.grade_color((118, 96, 94), "dusk", 0.08), np.float32)
    rock_d = np.array(C.grade_color((78, 62, 70), "dusk"), np.float32)
    bz = C.bayer(H, w)
    arr = np.zeros((H, w, 4), np.uint8)
    for x in range(w):
        c = crest[x]
        yy = np.arange(c, H)
        k = np.clip((yy - c) / 34.0, 0, 1) * 2 + bz[c:, x] * 0.9 - 0.45
        band = np.clip(k, 0, 1.99).astype(int)
        col = np.where(band[:, None] == 0, rock_l, np.where(band[:, None] == 1, rock, rock_d))
        col = col.copy()
        col[:1] = rim
        if (x // 3) % 2 == 0:
            col[1:2] = rim * 0.85 + rock_l * 0.15
        arr[c:, x, :3] = col
        arr[c:, x, 3] = 255
    im = Image.fromarray(arr, "RGBA")
    d = ImageDraw.Draw(im)
    dark = tuple(int(v) for v in rock_d * 0.8)
    r = rng("crev")
    for i in range(46):
        x = r.randint(0, P - 1)
        y0 = int(crest[x]) + r.randint(3, 8)
        L = r.randint(6, 20)
        pts = [(x, y0)]
        for j in range(3):
            pts.append((pts[-1][0] + r.randint(-2, 2), pts[-1][1] + L // 3))
        for off in (0, P):
            if pts[0][0] + off < w:
                d.line([(px + off, py) for px, py in pts], fill=dark)
    pine = C.grade_color((40, 76, 60), "dusk", 0.1)
    pine_d = C.grade_color((26, 48, 44), "dusk", 0.05)
    r = rng("pines")
    x = 4
    while x < P:
        h = r.randint(12, 26)
        for xx in (x, x + P):
            if xx - 10 < w:
                _pine(d, xx, int(crest[min(w - 1, xx)]) + 3, h, pine_d, pine)
        x += r.randint(22, 60)
    return im, crest


def crest_y(sx, cam):
    _, crest = _cached("passmid", _pass_mid)
    return int(crest[int(sx + cam * 0.5) % _MID_P])


def _signpost(img, x, y, text="京都"):
    x, y = int(x), int(y)
    d = ImageDraw.Draw(img)
    wood, wood_d = (126, 84, 56), (86, 56, 40)
    d.rectangle([x - 2, y - 30, x + 2, y], fill=INK)
    d.rectangle([x - 1, y - 29, x + 1, y], fill=wood)
    d.polygon([(x - 13, y - 30), (x + 12, y - 30), (x + 17, y - 25), (x + 12, y - 20), (x - 13, y - 20)], fill=INK)
    d.polygon([(x - 12, y - 29), (x + 12, y - 29), (x + 16, y - 25), (x + 12, y - 21), (x - 12, y - 21)],
              fill=(214, 186, 140))
    draw_text(img, x - 10, y - 31, text, (60, 36, 30), size=12)
    d.rectangle([x - 12, y - 21, x + 12, y - 21], fill=wood_d)


def _stone_lantern(img, x, y):
    x, y = int(x), int(y)
    d = ImageDraw.Draw(img)
    st, st_d = (150, 140, 150), (104, 96, 112)
    for (x0, y0, x1, y1) in ((-6, -3, 6, 0), (-2, -12, 2, -3), (-5, -18, 5, -12), (-8, -21, 8, -18), (-2, -24, 2, -21)):
        d.rectangle([x + x0 - 1, y + y0 - 1, x + x1 + 1, y + y1], fill=INK)
    for (x0, y0, x1, y1) in ((-6, -3, 6, -1), (-2, -12, 2, -4), (-5, -18, 5, -13), (-8, -21, 8, -19), (-2, -24, 2, -22)):
        d.rectangle([x + x0, y + y0, x + x1, y + y1], fill=st)
    d.rectangle([x - 2, y - 17, x + 2, y - 14], fill=(255, 200, 110))
    d.rectangle([x + 3, y - 18, x + 5, y - 13], fill=st_d)


def draw_pass_world(img, t, cam):
    C.sky(img, "dusk", t, horizon=150)
    C.clouds(img, t, cam * 0.3, "dusk", seed=4, count=5, y0=8, y1=58)
    C.far_mountains(img, cam, "dusk", y=100)
    far = _cached("passfar", _pass_far)
    o = int(cam * 0.25) % _FAR_P
    c = far.crop((o, 0, o + W, H))
    img.paste(c, (0, 0), c)
    mid, _ = _cached("passmid", _pass_mid)
    o = int(cam * 0.5) % _MID_P
    c = mid.crop((o, 0, o + W, H))
    img.paste(c, (0, 0), c)
    C.dirt_ground(img, 150, cam, "dusk", grass=0.5)


PASS_PARTY = [  # id, screen x, facing after the ambush, battle pose
    ("kondo", 262, 1, "ready"),
    ("hijikata", 234, 1, "draw"),
    ("shigeshige", 204, 1, "ready"),
    ("okita", 172, -1, "ready"),
    ("gintoki", 142, -1, "ready"),
    ("shinpachi", 114, -1, "ready"),
    ("kagura", 86, -1, "ready"),
]
NARAKU_PASS = [  # ridge x, landing x (None = stays on the ridge), facing after landing
    (40, 58, 1), (78, 30, 1), (124, None, 1), (286, 294, -1), (322, 320, -1), (352, 348, -1),
    (206, None, -1),
]


def pass_cam(t):
    return 30.0 * (min(t, T_APPEAR) - T_C)


def _pass_zoom(t):
    if t < T_LANDN:
        return 1.0
    return 1.0 + 0.35 * ease_out(seg(t, T_LANDN, T_LANDN + 0.14)) + 0.1 * ease_in_out(seg(t, T_LANDN + 0.14, T_D))


def shot_pass(img, t):
    cam = pass_cam(t)
    draw_pass_world(img, t, cam)
    circling_crows(img, t, 196, 44, n=5, r=70, seed=2)
    d = ImageDraw.Draw(img)
    for i in range(6):
        r = rng("farcrow", i)
        far_crow(d, (r.uniform(0, W) + t * r.uniform(6, 14)) % W, r.uniform(20, 70), t, i * 0.3)
    # roadside props (parallax 1.0)
    _stone_lantern(img, 40 - cam, 152)
    _signpost(img, 318 - cam, 154)
    # --- Naraku on the ridge (appear in poofs) and leaping down
    for i, (rx, lx, fac) in enumerate(NARAKU_PASS):
        ta = T_APPEAR + 0.04 * i
        if t < ta:
            continue
        ry = crest_y(rx, cam) + 2
        tl = T_LEAP + 0.06 * i
        f = -1 if rx > 200 else 1
        if lx is None or t < tl:
            alpha = seg(t, ta, ta + 0.12)
            spr, ax, ay = render_sprite("naraku", "stand_guard", t + i * 0.3, expr="angry", facing=f)
            spr = set_alpha(tint(spr, (40, 28, 56), 0.5), alpha)
            img.paste(spr, (rx - ax, ry - ay), spr)
            if alpha > 0.5:
                for ex in (-4, 2):
                    xx = rx + ex * f
                    rect(img, xx - 1 if f > 0 else xx, ry - 21, 2, 1, (255, 70, 80))
            fx.smoke_puff(img, t, ta, rx, ry - 12, size=9, seed=i, color=(90, 80, 110))
        else:
            tland = tl + 0.5
            if t < tland:
                k = seg(t, tl, tland)
                x, y = arc((rx, ry), (lx, FLOOR_Y), k, 30)
                draw_char(img, "naraku", x, y, "leap", t, facing=fac, shadow=False)
            else:
                pose = "land" if t < tland + 0.12 else "ambush"
                draw_char(img, "naraku", lx, FLOOR_Y, pose, t + i * 0.2, p=seg(t, tland, tland + 0.2), facing=fac)
                fx.smoke_puff(img, t, tland, lx, FLOOR_Y, size=7, seed=10 + i)
    # --- the escort
    for j, (cid, x, fac, bpose) in enumerate(PASS_PARTY):
        tt = t + j * 0.07
        kw = {}
        expr = None
        if cid == "shigeshige":
            expr = "haircut" if (t < T_APPEAR or t > T_LANDN + 0.3) else "haircut_shock"
        if t < T_APPEAR:
            pose, facing, p = "walk", 1, None
            if cid == "kagura":
                pose = "umbrella_open"
                ph = (step_frame(tt, 12) / 12.0) * 2 * math.pi * 1.6
                kw = dict(legs="walk", leg_phase=ph, stride=2.5, lift=2.0)
            x = x + wave(t, 0.5, 1.5, j * 0.2)
        elif t < T_LANDN:
            pose, facing, p = "shock", 1 if t < T_LEAP + 0.2 else fac, seg(t, T_APPEAR, T_APPEAR + 0.5)
        else:
            facing, p, pose = fac, None, bpose
            if bpose == "draw":
                p = seg(t, T_LANDN, T_LANDN + 0.5)
        draw_char(img, cid, x, FLOOR_Y, pose, tt, p=p, expr=expr, facing=facing, **kw)
    # --- camera: pan while walking, crash zoom when the ninjas land
    dx, dy = fx.shake_offset(t, T_LEAP + 0.5, 0.3, 3, seed=5)
    zoom(img, _pass_zoom(t), 192, 128)
    fx.shift(img, dx, dy)
    if T_APPEAR <= t < T_APPEAR + 0.08:
        fx.flash(img, 0.35, (255, 60, 70))
    if T_LANDN <= t < T_LANDN + 0.3:
        fx.speed_lines(img, t, 196, 118, (255, 255, 255), count=34, inner=110, seed=6,
                       alpha=1 - seg(t, T_LANDN, T_LANDN + 0.3))
    fx.letterbox(img, 1.0, 20)


# ================================================================ D: panel montage
P1_POLY = [(0, 0), (W, 0), (W, 90), (0, 106)]
P2_POLY = [(0, 111), (203, 100), (178, H), (0, H)]
P3_POLY = [(208, 99), (W, 95), (W, H), (183, H)]


def _poly_mask(poly, key):
    def build():
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon(poly, fill=255)
        return m
    return _cached(("pmask", key), build)


def _bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def _panel(img, world, poly, key, z, cx, cy, off=(0, 0)):
    """Zoom `world` by z around (cx, cy) into the polygon's bbox and paste through its mask."""
    x0, y0, x1, y1 = _bbox(poly)
    pw, ph = x1 - x0, y1 - y0
    box = (cx - pw / (2 * z), cy - ph / (2 * z), cx + pw / (2 * z), cy + ph / (2 * z))
    part = world.resize((pw, ph), Image.NEAREST, box=box)
    mask = _poly_mask(poly, key).crop((x0, y0, x1, y1))
    img.paste(part, (x0 + int(off[0]), y0 + int(off[1])), mask)
    d = ImageDraw.Draw(img)
    pts = [(px + off[0], py + off[1]) for px, py in poly]
    d.line(pts + [pts[0]], fill=INK, width=3)


def _hitspark(img, t, t0, x, y, seed, col=(255, 240, 150)):
    fx.burst(img, t, t0, x, y, n=12, colors=[(255, 255, 255), col, (228, 59, 68)],
             speed=(40, 110), gravity=60, life=0.35, size=(1, 2), seed=seed)
    if 0 <= t - t0 < 0.1:
        fx.comic_burst(img, x, y, 9, 4, 8, color=(255, 255, 255))


def _flyer(img, t, t0, x0, y0, vx, vy, seed, facing=1, g=260):
    dt = t - t0
    x, y = x0 + vx * dt, y0 + vy * dt + 0.5 * g * dt * dt
    pose = "hit" if dt < 0.12 else "fly"
    draw_char(img, "naraku", x, y, pose, t + seed, p=seg(dt, 0, 0.12), facing=facing,
              flash=0.8 if dt < 0.06 else 0, shadow=False)


def _leaper(img, t, t0, t1, p0, p1, facing, seed):
    """A Naraku ninja leaping in along an arc (p0 -> p1, landing at t1), then crouching."""
    if t < t0:
        return
    if t < t1:
        x, y = arc(p0, p1, seg(t, t0, t1), 24)
        draw_char(img, "naraku", x, y, "leap", t + seed, facing=facing, shadow=False)
    else:
        draw_char(img, "naraku", p1[0], p1[1], "land" if t < t1 + 0.1 else "ambush", t + seed,
                  p=seg(t, t1, t1 + 0.2), facing=facing)
        fx.smoke_puff(img, t, t1, p1[0], p1[1], size=6, seed=seed)


def world_p1(t):
    """Shinsengumi panel (scenery scrolling fast): Kondo, Hijikata's iai, Okita's bazooka x2."""
    u = t - T_D
    im = Image.new("RGB", (W, H))
    cam = 160 + u * 240
    draw_pass_world(im, t, cam)
    fx.motion_lines(im, t, (255, 236, 210), count=14, direction=-1, seed=3, y0=90, y1=150, speed=700)
    # Kondo slashes the ninja behind him (one clean swing, then stance)
    if u < 0.32:
        draw_char(im, "naraku", 118, FLOOR_Y, "attack", t, p=0.3, facing=1)
    else:
        _flyer(im, t, T_D + 0.32, 118, FLOOR_Y, -120, -160, 1, facing=1)
        _hitspark(im, t, T_D + 0.32, 128, 142, 1)
    if u < 0.75:
        draw_char(im, "kondo", 150, FLOOR_Y, "attack", t, p=seg(u, 0.05, 0.75), facing=-1)
    else:
        draw_char(im, "kondo", 150, FLOOR_Y, "ready", t, facing=-1)
    # Hijikata: iai draw, then a cool smoke break while Okita blows things up
    if u < 1.0:
        draw_char(im, "hijikata", 186, FLOOR_Y, "draw", t, p=seg(u, 0.0, 0.5), facing=1)
    else:
        draw_char(im, "hijikata", 186, FLOOR_Y, "smoke", t - T_D, facing=1)
    if u < 0.2:
        draw_char(im, "naraku", 236, FLOOR_Y, "ready", t, facing=-1)
    else:
        _flyer(im, t, T_D + 0.2, 236, FLOOR_Y, 150, -190, 2, facing=-1)
        _hitspark(im, t, T_D + 0.2, 230, 142, 2)
    # second wave leaps in from the right ...
    _l1, _l2 = T_D + 1.15, T_D + 1.22
    te2 = T_D + 1.80
    if t < te2:
        _leaper(im, t, _l1, _l1 + 0.35, (350, 70), (270, FLOOR_Y), -1, 11)
        _leaper(im, t, _l2, _l2 + 0.35, (380, 84), (306, FLOOR_Y), -1, 12)
    # ... Okita's bazooka (twice)
    p_okita = seg(u, 0.0, 0.8) if u < 1.3 else seg(u, 1.4, 2.2)
    draw_char(im, "okita", 214, FLOOR_Y, "bazooka", t, p=p_okita, facing=1)
    te = T_D + 0.45
    if t < te:
        draw_char(im, "naraku", 296, FLOOR_Y, "ready", t, facing=-1)
    elif t < te + 1.0:
        _flyer(im, t, te, 296, FLOOR_Y - 4, 60, -260, 3, facing=-1, g=300)
    fx.explosion(im, t, te, 296, 146, size=22, seed=4)
    if te <= t < te + 0.6:
        sfx_text(im, 300, 112, "轰！", t, te, 0.6, size=16, angle=8)
    if t >= te2:
        _flyer(im, t, te2, 270, FLOOR_Y - 4, 40, -300, 13, facing=-1, g=300)
        _flyer(im, t, te2 + 0.03, 306, FLOOR_Y - 4, 120, -240, 14, facing=-1, g=300)
        fx.explosion(im, t, te2, 288, 146, size=30, seed=5)
        sfx_text(im, 290, 104, "轰轰！！", t, te2, 0.7, size=16, angle=-6)
    return im


def world_p2(t):
    """Yorozuya panel: orange speed-line background."""
    u = t - T_P2
    im = Image.new("RGB", (W, H), (236, 120, 60))
    fx.speed_lines(im, t, 130, 128, (255, 200, 120), count=46, inner=30, seed=7)
    rect(im, 0, FLOOR_Y + 1, W, 3, (170, 70, 40))
    # Kagura's umbrella gun on the left ninja ... then a bored sukonbu break
    if u < 0.9:
        draw_char(im, "kagura", 100, FLOOR_Y, "umbrella_shoot", t, facing=-1)
        kx = 80 - u * 8
        draw_char(im, "naraku", kx, FLOOR_Y, "hit", t, p=0.3 + 0.1 * (step_frame(t, 12) % 2), facing=1,
                  flash=0.45 if step_frame(t, 15) % 3 == 0 else 0)
        d = ImageDraw.Draw(im)
        for i in range(3):
            r = rng("bullet", i, step_frame(t, 15))
            yy = 142 + r.randint(-4, 3)
            d.line([(kx + 6, yy), (86, 146 + r.randint(-1, 1))], fill=(255, 250, 180))
            fx.sparkle(im, int(kx + 4), int(yy), t, t - 0.05, size=2)
    else:
        draw_char(im, "naraku", 76, FLOOR_Y, "lie", t, facing=1)
        draw_char(im, "kagura", 100, FLOOR_Y, "sukonbu", t, facing=-1)
    # Shinpachi on guard (glasses glint!)
    draw_char(im, "shinpachi", 124, FLOOR_Y, "ready", t, facing=1)
    for tg in (T_P2 + 0.5, T_P2 + 1.45):
        fx.sparkle(im, 128, 136, t, tg, size=4)
    # Gintoki: rising slash -> the ninja becomes a star; then a lazy swat at the next one
    th, tc = T_P2 + 0.22, T_P2 + 1.33
    if u < 0.8:
        draw_char(im, "gintoki", 146, FLOOR_Y, "slash_up", t, p=seg(u, 0.1, 0.55), facing=1)
    elif T_P2 + 1.1 <= t < T_P2 + 1.6:
        draw_char(im, "gintoki", 146, FLOOR_Y, "attack", t, p=seg(t, T_P2 + 1.1, T_P2 + 1.6), facing=1)
    else:
        draw_char(im, "gintoki", 146, FLOOR_Y, "shoulder", t, facing=1)
    if t < th:
        draw_char(im, "naraku", 168, FLOOR_Y, "attack", t, p=0.2, facing=-1)
    elif t < th + 0.5:
        _flyer(im, t, th, 166, FLOOR_Y, 10, -330, 5, facing=-1, g=120)
        _hitspark(im, t, th, 164, 138, 5)
    fx.sparkle(im, 162, 100, t, T_P2 + 0.72, size=5, color=(255, 250, 200))     # ...kira!
    if t < tc:
        _leaper(im, t, T_P2 + 0.95, T_P2 + 1.2, (230, 96), (170, FLOOR_Y), -1, 21)
    else:
        _flyer(im, t, tc, 170, FLOOR_Y - 2, 190, -140, 22, facing=-1)
        _hitspark(im, t, tc, 164, 140, 22)
        sfx_text(im, 176, 112, "砰！", t, tc, 0.5, size=16, angle=10)
    return im


def world_p3(t):
    """Katsura + Elizabeth panel: indigo with motion streaks."""
    u = t - T_P3
    im = Image.new("RGB", (W, H), (46, 44, 104))
    fx.motion_lines(im, t, (120, 130, 220), count=30, direction=1, seed=9, y0=80, y1=170, speed=900)
    rect(im, 0, FLOOR_Y + 1, W, 3, (30, 28, 70))
    # Katsura cuts the ninja on the left, then deadpans with a lit bomb
    tk = T_P3 + 0.27
    if u < 0.95:
        draw_char(im, "katsura", 168, FLOOR_Y, "attack", t, p=seg(u, 0.05, 0.6), facing=-1)
    else:
        draw_char(im, "katsura", 168, FLOOR_Y, "bomb", t, facing=-1)
    if t < tk:
        draw_char(im, "naraku", 142, FLOOR_Y, "ready", t, facing=1)
    else:
        _flyer(im, t, tk, 142, FLOOR_Y, -170, -150, 6, facing=1)
        _hitspark(im, t, tk, 148, 140, 6)
    # Elizabeth raises 「天诛」 (readable), then clubs a ninja with it
    tel = T_P3 + 0.84
    if u < 0.62:
        draw_char(im, "elizabeth", 204, FLOOR_Y, "sign", t, p=seg(u, 0.02, 0.4), facing=1, sign="天诛")
    elif u < 1.15:
        draw_char(im, "elizabeth", 204, FLOOR_Y, "attack", t, p=seg(u, 0.62, 1.1), facing=1, sign="天诛")
    else:
        draw_char(im, "elizabeth", 204, FLOOR_Y, "sign", t, p=seg(u, 1.15, 1.45), facing=1, sign="天诛")
    if t < tel:
        draw_char(im, "naraku", 234, FLOOR_Y, "ready", t, facing=-1)
    else:
        _flyer(im, t, tel, 234, FLOOR_Y, 190, -120, 7, facing=-1)
        _hitspark(im, t, tel, 228, 136, 7)
    if tel <= t < tel + 0.6:
        sfx_text(im, 236, 106, "咚！", t, tel, 0.6, size=16, angle=-10)
    return im


def shot_panels(img, t):
    img.paste((14, 8, 16), (0, 0, W, H))
    fx.speed_lines(img, t, W // 2, H // 2, (120, 20, 36), count=40, inner=40, seed=11)
    k1 = ease_out(seg(t, T_D, T_D + 0.16))
    _panel(img, world_p1(t), P1_POLY, "p1", 1.5, 216, 128, off=(-(1 - k1) * W, 0))
    if t >= T_P2:
        k2 = ease_out(seg(t, T_P2, T_P2 + 0.16))
        _panel(img, world_p2(t), P2_POLY, "p2", 1.45, 126, 128, off=(0, (1 - k2) * 130))
    if t >= T_P3:
        k3 = ease_out(seg(t, T_P3, T_P3 + 0.16))
        _panel(img, world_p3(t), P3_POLY, "p3", 1.6, 190, 128, off=((1 - k3) * 220, 0))
    # entry shakes
    dx, dy = 0, 0
    for i, tt in enumerate((T_D, T_P2, T_P3, T_P3 + 0.84, T_D + 1.80, T_P2 + 1.33)):
        ox, oy = fx.shake_offset(t, tt + 0.1, 0.18, 3, seed=20 + i)
        dx, dy = dx + ox, dy + oy
    fx.shift(img, dx, dy, (14, 8, 16))
    # the giant slash that ends the montage
    if t >= T_CUT:
        k = ease_out(seg(t, T_CUT, T_CUT + 0.12))
        ax, ay, bx, by = W + 30, -30, -30, H + 30
        ex, ey = lerp(ax, bx, k), lerp(ay, by, k)
        th = 3 + 9 * seg(t, T_CUT + 0.05, T_CUT + 0.2)
        nx, ny = 0.49, 0.87
        d = ImageDraw.Draw(img)
        d.polygon([(ax - nx * th, ay - ny * th), (ex - nx * 2, ey - ny * 2), (ex + nx * 2, ey + ny * 2),
                   (ax + nx * th, ay + ny * th)], fill=(255, 255, 255))
        fx.flash(img, ease_in(seg(t, T_CUT + 0.12, T_E - 0.04)))


# ================================================================ E: sunset duel
SUN = (208, 100, 54)
TREE_MX = 384 - 4          # the dead tree is drawn mirrored: x -> TREE_MX - x


def _ridge_static():
    im = Image.new("RGB", (W, H))
    C.sky(im, "dusk", 0.0, horizon=150, body=False, stars=False)
    sx, sy, r = SUN
    # dithered halo rings + banded sun disc (top bright -> bottom red)
    a = np.asarray(im).copy()
    yy, xx = np.mgrid[0:H, 0:W]
    dist = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2)
    for rr, col, lv in ((r + 16, (250, 150, 110), 0.35), (r + 8, (252, 170, 110), 0.6)):
        a[(dist <= rr) & dither_mask(W, H, lv)] = col
    bands = [(255, 214, 130), (254, 180, 100), (248, 136, 86), (232, 92, 80)]
    band = np.clip((yy - (sy - r)) / (2 * r) * 4 + dither_mask(W, H, 0.5) * 0.9 - 0.45, 0, 3.99).astype(int)
    for i, col in enumerate(bands):
        a[(dist <= r) & (band == i)] = col
    im = Image.fromarray(a, "RGB")
    d = ImageDraw.Draw(im)
    # long thin cloud streaks across the sun
    for y, x0, x1 in ((96, 120, 300), (104, 150, 260), (111, 90, 230), (88, 210, 330)):
        d.rectangle([x0, y, x1, y + 1], fill=(120, 60, 100))
        d.rectangle([x0 + 10, y + 2, x1 - 20, y + 2], fill=(150, 76, 110))
    C.far_mountains(im, 140, "dusk", y=122)
    C.dirt_ground(im, 150, 40, "dusk", grass=0.7)
    # dead tree silhouette (right, behind Oboro) - mirrored about TREE_MX
    tc = (34, 22, 38)
    d = ImageDraw.Draw(im)
    M = lambda x: TREE_MX - x
    d.polygon([(M(30), 156), (M(46), 156), (M(42), 120), (M(40), 84), (M(36), 84), (M(35), 120)], fill=tc)
    for (x0, y0, x1, y1, w) in ((39, 100, 66, 80, 3), (38, 92, 18, 70, 3), (40, 86, 50, 60, 2), (60, 83, 76, 76, 2),
                                (24, 76, 14, 66, 1), (47, 70, 58, 56, 1), (38, 118, 60, 108, 2)):
        d.line([(M(x0), y0), (M(x1), y1)], fill=tc, width=w)
    # boulders
    for bx, by, bw, bh in ((70, 156, 40, 16), (44, 158, 30, 10), (384, 160, 26, 12)):
        d.ellipse([bx - bw // 2, by - bh, bx + bw // 2, by + bh // 2], fill=(58, 40, 60))
        d.ellipse([bx - bw // 2 + 3, by - bh + 1, bx + bw // 2 - 8, by - bh + 5], fill=(92, 62, 84))
    return im


TREE_CROWS = [(TREE_MX - 66, 79), (TREE_MX - 19, 69), (TREE_MX - 50, 59), (TREE_MX - 74, 75)]


def draw_duel_world(img, t):
    img.paste(_cached("ridge", _ridge_static))
    d = ImageDraw.Draw(img)
    for i in range(5):
        r = rng("dfar", i)
        far_crow(d, (r.uniform(0, W) + t * r.uniform(5, 12)) % W, r.uniform(20, 60), t, i * 0.37)
    # crows on the dead tree (scatter at the clash)
    for i, (cx, cy) in enumerate(TREE_CROWS):
        if t < T_CLASH:
            spr = perch_crow_sprite(1 if i % 2 else -1)
            paste(img, spr, cx, cy + (1 if step_frame(t + i * 0.2, 3) % 5 == 0 else 0), anchor="bottom")
        else:
            dt = t - T_CLASH - i * 0.04
            if dt < 0:
                continue
            r = rng("scat", i)
            vx, vy = r.uniform(-60, 90), r.uniform(-90, -50)
            x, y = cx + vx * dt, cy - 3 + vy * dt
            if -20 < x < W + 20 and y > -20:
                draw_crow(img, x, y, t, 1, 1 if vx > 0 else -1, phase=i * 0.1, flap_fps=16)
    # wind: blowing leaves + swaying grass tufts
    fx.sakura(img, t, count=18, seed=31, colors=((236, 110, 60), (200, 70, 60), (250, 170, 90)),
              wind=90, fall=16, area=(0, 60, W, 170))
    for i in range(16):
        r = rng("tuft", i)
        x = int(r.uniform(0, W))
        y = int(r.uniform(163, 176))
        sw = 1 if step_frame(t + r.random(), 5) % 2 else 0
        col = (72, 60, 70)
        d.line([(x, y), (x + 1 + sw, y - 4)], fill=col)
        d.line([(x + 2, y), (x + 3 + sw, y - 3)], fill=col)


def shot_duel(img, t):
    draw_duel_world(img, t)
    GX0, OX0 = 150, 282
    GXL, OXL = 196, 238
    # blade-lock push beats: Oboro shoves (13.2), Gintoki shoves back (14.1)
    po = int(round(-4 * ease_out(seg(t, T_PUSH1, T_PUSH1 + 0.12)) + 6 * ease_out(seg(t, T_PUSH2, T_PUSH2 + 0.12))))
    contact = (216 + (po if t >= T_CLASH else 0), 143)
    # ---------------- Oboro
    if t < T_THROW:
        draw_char(img, "oboro", OX0, FLOOR_Y, "needle", t, p=lerp(0.0, 0.42, seg(t, T_E, T_THROW)), facing=-1)
    elif t < T_DASH + 0.05:
        if t < T_DEFLECT + 0.15:
            draw_char(img, "oboro", OX0, FLOOR_Y, "idle", t, facing=-1, arm_f=85, arm_b=-30, legs="lunge", lean=2)
        else:
            draw_char(img, "oboro", OX0, FLOOR_Y, "idle", t, facing=-1, expr="cold_smile")
    elif t < T_CLASH:
        k = ease_in(seg(t, T_DASH + 0.05, T_CLASH))
        draw_char(img, "oboro", lerp(OX0, OXL, k), FLOOR_Y, "ready", t, facing=-1, expr="angry")
    else:
        j = 1 if step_frame(t, 12) % 2 else 0
        draw_char(img, "oboro", OXL + j + po, FLOOR_Y, "ready", t, facing=-1, expr="cold_smile",
                  arm_f=86, weapon=8, legs="lunge", lean=3, arm_b=40, bob=0)
    # ---------------- Gintoki
    if t < T_THROW + 0.05:
        draw_char(img, "gintoki", GX0, FLOOR_Y, "ready", t, facing=1, expr="angry")
    elif t < T_DEFLECT + 0.25:
        draw_char(img, "gintoki", GX0, FLOOR_Y, "guard", t, facing=1)
    elif t < T_DASH:
        draw_char(img, "gintoki", GX0, FLOOR_Y, "ready", t, facing=1, expr="angry")
    elif t < T_CLASH:
        k = ease_in(seg(t, T_DASH, T_CLASH))
        gx = lerp(GX0, GXL, k)
        draw_char(img, "gintoki", gx, FLOOR_Y, "run", t, facing=1, weapon=10, arm_f=70)
        fx.motion_lines(img, t, (255, 230, 200), count=8, direction=-1, seed=4, y0=128, y1=156,
                        speed=600, length=(10, 30))
    else:
        j = 1 if step_frame(t, 12) % 2 else 0
        gex = "shout" if T_PUSH2 <= t < T_PUSH2 + 0.4 else ("hurt" if T_PUSH1 <= t < T_PUSH1 + 0.35 else "angry")
        draw_char(img, "gintoki", GXL - j + po, FLOOR_Y, "ready", t, facing=1, expr=gex,
                  arm_f=86, weapon=16, legs="lunge", lean=3, arm_b=40, bob=0)
    # ---------------- needles
    hx, hy = hand_rel("oboro", 85, lean=2, facing=-1)
    src = (OX0 + hx, FLOOR_Y + hy)
    dst = (GX0 + 14, FLOOR_Y - 18)
    if T_THROW <= t < T_DEFLECT:
        k = seg(t, T_THROW, T_DEFLECT)
        d = ImageDraw.Draw(img)
        for i, dy in enumerate((-4, 0, 4)):
            x = lerp(src[0], dst[0], k)
            y = lerp(src[1], dst[1] + dy * 0.5, k) + dy * (1 - k)
            d.line([(x, y), (x + 9, y)], fill=(236, 240, 250))
            d.line([(x + 9, y), (x + 16, y)], fill=(120, 126, 150))
    if T_DEFLECT <= t < T_DEFLECT + 0.7:
        dt = t - T_DEFLECT
        for i in range(3):
            r = rng("defl", i)
            vx, vy = r.uniform(20, 70), r.uniform(-150, -90)
            x = dst[0] + vx * dt
            y = dst[1] + vy * dt + 0.5 * 500 * dt * dt
            if y > FLOOR_Y + 2:
                y = FLOOR_Y + 2
                a = 1.2
            else:
                a = dt * 20 + i
            stamp_line(img, (x, y), (x + math.cos(a) * 4, y - math.sin(a) * 4), 1, (236, 240, 250))
        _hitspark(img, t, T_DEFLECT, dst[0], dst[1], 40)
    # ---------------- clash
    if t >= T_CLASH:
        dt = t - T_CLASH
        if dt < 0.5:
            rr = 6 + dt * 260
            ImageDraw.Draw(img).ellipse([contact[0] - rr, contact[1] - rr * 0.6, contact[0] + rr, contact[1] + rr * 0.6],
                                        outline=(255, 244, 220), width=2 if dt < 0.25 else 1)
        fx.smoke_puff(img, t, T_CLASH, GXL - 4, FLOOR_Y, size=10, seed=41)
        fx.smoke_puff(img, t, T_CLASH, OXL + 4, FLOOR_Y, size=10, seed=42)
        fx.burst(img, t, T_CLASH, contact[0], contact[1], n=22, colors=[(255, 255, 255), (255, 230, 120), (255, 160, 60)],
                 speed=(60, 170), gravity=200, life=0.6, size=(1, 2), seed=43)
        # continuous grinding sparks
        k = int(dt * 8)
        fx.burst(img, t, T_CLASH + k / 8.0 + 0.001, contact[0], contact[1], n=6,
                 colors=[(255, 250, 200), (255, 190, 80)], speed=(30, 80), gravity=180, life=0.3, seed=50 + k)
        if int(t * 20) % 2:
            rect(img, contact[0] - 1, contact[1] - 1, 3, 3, (255, 255, 230))
        for i, tp in enumerate((T_PUSH1, T_PUSH2)):
            fx.burst(img, t, tp, contact[0], contact[1], n=14, colors=[(255, 255, 255), (255, 220, 110)],
                     speed=(50, 140), gravity=200, life=0.45, size=(1, 2), seed=60 + i)
    # ---------------- camera
    z = lerp(1.18, 1.36, ease_out(seg(t, T_E, T_DASH))) + 0.1 * ease_in(seg(t, T_DASH, T_CLASH))
    cx, cy = 216, 124
    if t >= T_CLASH:
        z = 1.5 + 0.75 * ease_in_out(seg(t, T_CLASH + 0.07, T_F))
        cx, cy = lerp(216, contact[0], seg(t, T_CLASH, T_CLASH + 0.6)), lerp(124, 134, seg(t, T_CLASH, T_CLASH + 0.6))
    zoom(img, z, cx, cy)
    sdx, sdy = fx.shake_offset(t, T_CLASH, 0.45, 5, seed=9)
    for i, tp in enumerate((T_PUSH1, T_PUSH2)):
        ox, oy = fx.shake_offset(t, tp, 0.2, 2, seed=70 + i)
        sdx, sdy = sdx + ox, sdy + oy
    ddx, ddy = fx.shake_offset(t, T_DEFLECT, 0.15, 2, seed=8)
    fx.shift(img, sdx + ddx, sdy + ddy)
    if t >= T_CLASH:
        vignette(img, 0.4, (30, 10, 20))
    if T_CLASH <= t < T_CLASH + 0.07:
        fx.impact_frame(img, (255, 250, 240), (20, 10, 20), threshold=120)
    elif T_CLASH + 0.07 <= t < T_CLASH + 0.2:
        fx.flash(img, 0.5 * (1 - seg(t, T_CLASH + 0.07, T_CLASH + 0.2)))
    if t < T_E + 0.25:
        fx.flash(img, 1 - seg(t, T_E, T_E + 0.25))
    sfx_text(img, 128, 78, "锵！", t, T_DEFLECT, 0.55, size=16, angle=10)
    sfx_text(img, 104, 92, "铿——！！", t, T_CLASH, 0.8, color=(255, 255, 255), size=24, angle=8)
    fx.letterbox(img, 1.0, 18)
    name_card(img, t, 11.80, 2.2, "oboro", "胧", "天照院奈落首领", side="right", y=24)


# ================================================================ F: eyes / sensei
EYE_Y0, EYE_Y1 = 46, 170
SKIN, SKIN_S, SKIN_D = (255, 216, 184), (234, 170, 140), (206, 140, 118)
HAIR_H, HAIR_M, HAIR_D = (238, 240, 250), (196, 202, 224), (146, 152, 188)
EYES = ((108, -1), (276, 1))          # centre x, side (-1 = screen-left eye)
EYE_CY = 118


def _hair_strands():
    r = rng("bangs")
    out = []
    x = -10
    while x < W + 10:
        w = r.randint(22, 40)
        L = r.randint(14, 30)
        if 150 < x < 234:
            L = r.randint(36, 48)       # long central strands between the eyes
        out.append((x, w, L, r.uniform(-6, 6)))
        x += int(w * 0.7)
    return out


def _face_base():
    """Static skin layer: hair shadow gradient on the forehead, side shading, nose."""
    y0, y1 = EYE_Y0, EYE_Y1
    yy, xx = np.mgrid[y0:y1, 0:W].astype(np.float32)
    arr = np.empty((y1 - y0, W, 3), np.float32)
    arr[:] = SKIN
    bz = C.bayer(y1 - y0, W)
    shadow = np.clip((100 - yy) / 40.0, 0, 1)
    arr[bz < shadow] = SKIN_S
    arr[(bz < shadow - 0.55)] = SKIN_D
    side = np.clip((np.abs(xx - W / 2) - 160) / 30.0, 0, 1)
    arr[bz < side] = SKIN_S
    arr[(np.abs(xx - 197) < 1) & (yy > 142) & (yy < 158)] = SKIN_S
    arr[(np.abs(xx - 194) < 4) & (np.abs(yy - 159) < 1)] = SKIN_D
    return arr, yy, xx


def draw_eyes(img, t, widen, tremble):
    base, yy, xx = _cached("facebase", _face_base)
    arr = base.copy()
    jit = 0
    if tremble > 0:
        r = rng("trem", step_frame(t, 24))
        jit = r.choice((-1, 0, 1)) if tremble > 0.3 else 0
    cy = EYE_CY
    for cx, s in EYES:
        rx = 42.0
        dx = (xx - cx) / rx
        ax = np.abs(dx)
        f = np.clip(1 - dx * dx, 0, 1)
        top_h = lerp(13, 22, widen)
        bot_h = lerp(10, 13, widen)
        tilt = s * dx * lerp(3.5, 1.5, widen)          # outer corners slightly higher
        top = cy - top_h * f ** 0.7 - tilt
        bot = cy + bot_h * f ** 0.9 - tilt * 0.3
        inside = (ax <= 1) & (yy >= top) & (yy <= bot)
        arr[inside] = (250, 250, 252)
        arr[inside & (yy < top + 4)] = (206, 206, 228)
        icx = cx + 6 * s * 0 + 6 + jit
        icy = cy + 1 + lerp(1.5, 0, widen)
        ri = lerp(14.0, 7.5, widen)
        rp = lerp(5.5, 1.6, widen)
        di = np.sqrt((xx - icx) ** 2 + (yy - icy) ** 2)
        iris = inside & (di <= ri)
        arr[iris] = (150, 36, 58)
        arr[iris & (yy > icy + ri * 0.2)] = (186, 60, 82)
        arr[iris & (yy > icy + ri * 0.55)] = (214, 96, 104)
        arr[iris & (yy < icy - ri * 0.35)] = (104, 22, 42)
        arr[iris & (di > ri - 1.7)] = (80, 14, 32)
        arr[inside & (di <= rp)] = (30, 6, 18)
        if widen < 0.6:
            hl = inside & (np.abs(xx - (icx - ri * 0.45)) < 2.5) & (np.abs(yy - (icy - ri * 0.3)) < 1.6)
            arr[hl] = (255, 255, 255)
            arr[inside & (np.abs(xx - (icx + ri * 0.4)) < 1) & (np.abs(yy - (icy + ri * 0.45)) < 1)] = (255, 220, 220)
        else:
            arr[inside & (np.abs(xx - (icx - 2)) < 1) & (np.abs(yy - (icy - 3)) < 1)] = (255, 255, 255)
        # lazy upper lid (dead-fish eyes) covering the top of the eye
        lid = top + (bot - top) * lerp(0.44, 0.0, widen)
        arr[inside & (yy < lid)] = (246, 196, 164)
        thick = lerp(2.6, 2.0, widen)
        arr[(ax <= 1.05) & (yy >= lid - thick) & (yy <= lid + 1.0)] = INK
        # outer-corner lash flick
        ox = cx + s * rx
        flick = (np.abs(xx - (ox + s * 2)) < 3) & (yy > lid - 4) & (yy < lid + 1) & ((xx - ox) * s > -2)
        arr[flick & (yy - (cy - 2) < 3)] = INK
        arr[(ax <= 0.85) & (np.abs(yy - (top - 5 - widen * 4)) < 0.8)] = SKIN_D     # crease
        arr[(ax <= 0.9) & (np.abs(yy - bot - 0.5) < 0.8)] = (190, 116, 106)          # lower lid
        arr[(ax <= 0.6) & (np.abs(yy - bot - 5) < 0.6) & (widen < 0.5)] = SKIN_S     # tired bags
    img.paste(Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGB"), (0, EYE_Y0))
    d = ImageDraw.Draw(img)
    # brows (half hidden by the bangs), raised when the eyes widen
    for cx, s in EYES:
        by = 88 - widen * 8
        inner, outer = cx - s * 32, cx + s * 30
        lift = widen * 4                               # worried: inner ends rise
        pts_top = [(inner, by - lift), (cx - s * 10, by - 3 - lift * 0.6), (cx + s * 12, by - 3), (outer, by + 1)]
        pts_bot = [(outer, by + 2), (cx + s * 12, by), (cx - s * 10, by + 1 - lift * 0.6), (inner, by + 4 - lift)]
        d.polygon(pts_top + pts_bot, fill=HAIR_M, outline=INK)
        d.line(pts_top[:3], fill=HAIR_H)
    # bangs + their shadow
    sway = wave(t, 0.7, 1.5)
    y0 = EYE_Y0
    for x, w, L, lean in _cached("bangs", _hair_strands):
        tipx = x + w / 2 + lean + sway
        d.polygon([(x, y0), (x + w, y0), (tipx + 3, y0 + L + 5)], fill=SKIN_D)
    for x, w, L, lean in _cached("bangs", _hair_strands):
        tipx = x + w / 2 + lean + sway
        d.polygon([(x, y0), (x + w, y0), (tipx, y0 + L)], fill=HAIR_M, outline=INK)
        d.polygon([(x + 3, y0), (x + w * 0.55, y0), (tipx - 1, y0 + L - 5)], fill=HAIR_H)
        d.line([(x + w - 3, y0 + 2), (tipx + 1, y0 + L - 3)], fill=HAIR_D)
    rect(img, 0, y0, W, 6, HAIR_M)
    rect(img, 0, y0 + 2, W, 2, HAIR_H)


S_HI, S_HL, S_HM, S_HD = (246, 228, 190), (222, 194, 150), (184, 150, 108), (134, 100, 72)
S_SK, S_SK_S, S_SK_D = (255, 224, 196), (242, 190, 160), (218, 156, 132)
S_CX = 192


def _sensei_hw(y):
    """Half-width of Shouyou's face at canvas row y (round, gentle jaw; chin ~y 158)."""
    if y < 104:
        return 58.0
    k = (y - 104) / 55.0
    return 0.0 if k >= 1 else 58.0 * (1 - k ** 2.3) ** 0.55


def _sensei_layer():
    """Static RGBA close-up of Shouyou's gentle smile (canvas coords)."""
    cx = S_CX
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # back hair mass + neck + collar
    d.polygon([(cx - 74, 30), (cx + 74, 30), (cx + 90, 110), (cx + 86, H), (cx - 86, H), (cx - 90, 110)],
              fill=S_HD, outline=INK)
    d.rectangle([cx - 15, 140, cx + 15, H], fill=S_SK_S)
    d.polygon([(cx - 15, 146), (cx + 15, 146), (cx + 15, 153), (cx, 162), (cx - 15, 153)], fill=S_SK_D)
    for s in (-1, 1):   # beige kimono inner lapel + sage-green haori
        d.polygon([(cx + s * 16, 158), (cx + s * 4, 190), (cx + s * 30, 216), (cx + s * 64, 216), (cx + s * 60, 162)],
                  fill=(250, 242, 220), outline=INK)
        d.polygon([(cx + s * 30, 160), (cx + s * 16, 196), (cx + s * 40, 216), (cx + s * 96, 216), (cx + s * 88, 164)],
                  fill=(196, 216, 174), outline=INK)
        d.line([(cx + s * 32, 166), (cx + s * 22, 192)], fill=(156, 180, 138))
    # face (numpy mask, dithered shading)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    hw = np.array([_sensei_hw(y) for y in range(H)], np.float32)[:, None]
    face = (ys >= 56) & (np.abs(xs - cx) <= hw) & (hw > 0)
    bz = C.bayer(H, W)
    a = np.asarray(im).copy()
    col = np.zeros((H, W, 3), np.float32)
    col[:] = S_SK
    edge = np.clip((np.abs(xs - cx) - (hw - 12)) / 12.0, 0, 1)
    col[bz < edge] = S_SK_S
    top = np.clip((94 - ys) / 20.0, 0, 1)                       # shadow under the bangs
    col[bz < top] = S_SK_S
    col[bz < top - 0.6] = S_SK_D
    blush = (((xs - (cx - 38)) / 10) ** 2 + ((ys - 111) / 3.5) ** 2 <= 1) | \
            (((xs - (cx + 38)) / 10) ** 2 + ((ys - 111) / 3.5) ** 2 <= 1)
    col[blush & (bz < 0.55)] = (252, 176, 164)
    # jaw outline (lower half only; the upper edge hides under the hair)
    inner = np.zeros_like(face)
    inner[1:-1, 1:-1] = face[1:-1, 1:-1] & face[2:, 1:-1] & face[1:-1, 2:] & face[1:-1, :-2]
    rim = face & ~inner & (ys > 100)
    a[face, :3] = col[face].astype(np.uint8)
    a[face, 3] = 255
    a[rim, :3] = INK
    im = Image.fromarray(a, "RGBA")
    d = ImageDraw.Draw(im)
    # brows: soft, slightly raised in the middle
    for s in (-1, 1):
        pts = [(cx + s * (14 + 30 * k), 86 - 3 * math.sin(math.pi * k) + 2 * k) for k in np.linspace(0, 1, 9)]
        d.line(pts, fill=S_HM, width=2)
    # closed-eye smile arcs  ^ ^
    for s in (-1, 1):
        ex = cx + s * 29
        pts = [(ex + dx, 101 - 5.5 * (1 - (dx / 14.0) ** 2)) for dx in np.linspace(-14, 14, 15)]
        d.line(pts, fill=INK, width=2)
        d.line([(ex + s * 14, 101), (ex + s * 17, 103)], fill=INK, width=1)        # lash flick
        d.line([(ex - 9, 104), (ex + 9, 104)], fill=S_SK_S)                        # soft lower crease
    # nose + gentle smile
    d.point((cx + 2, 115), fill=S_SK_D)
    d.point((cx + 2, 116), fill=S_SK_D)
    d.point((cx + 1, 117), fill=(196, 132, 116))
    # side locks in front of the face edges
    for s in (-1, 1):
        lock = [(cx + s * 88, 40), (cx + s * 56, 40), (cx + s * 50, 96), (cx + s * 52, 140), (cx + s * 60, 176),
                (cx + s * 70, 200), (cx + s * 86, 196), (cx + s * 90, 150), (cx + s * 92, 100)]
        d.polygon(lock, fill=S_HL, outline=INK)
        d.line([(cx + s * 54, 60), (cx + s * 52, 110), (cx + s * 56, 150), (cx + s * 64, 180)], fill=S_HM, width=2)
        d.line([(cx + s * 74, 56), (cx + s * 72, 120), (cx + s * 76, 170)], fill=S_HI)
        d.line([(cx + s * 84, 70), (cx + s * 86, 140)], fill=S_HM)
    # bangs, parted in the middle (forehead peeks through the part)
    strands = [  # (base inner x, base outer x, tip x, tip y) for the left side; mirrored for the right
        (2, 30, 22, 82), (22, 50, 44, 90), (44, 70, 64, 98), (64, 90, 86, 108)]
    for s in (-1, 1):
        for i, (bi, bo, tx, ty) in enumerate(strands):
            mid_in = (cx + s * (bi + tx) * 0.5 - s * 2, (40 + ty) * 0.5 + 6)
            poly = [(cx + s * bi, 40), mid_in, (cx + s * tx, ty), (cx + s * (bo + 4), (40 + ty) * 0.5), (cx + s * bo, 40)]
            d.polygon(poly, fill=S_HL, outline=INK)
            d.line([(cx + s * (bi + 6), 44), (cx + s * (tx - 2), ty - 8)], fill=S_HI)
            d.line([(cx + s * (bo - 3), 46), (cx + s * (tx + 1), ty - 4)], fill=S_HM)
    # little strand crossing the part + crown highlight ring
    d.polygon([(cx - 6, 40), (cx + 8, 40), (cx + 3, 66)], fill=S_HL, outline=INK)
    for s in (-1, 1):
        d.arc([cx - 70, 30, cx + 70, 70], 200 if s < 0 else 290, 250 if s < 0 else 340, fill=S_HI, width=2)
    return im


def _sensei_mouth(img, t, cx, oy):
    """The smile grows a little while we look at him."""
    k = ease_in_out(seg(t, T_SHOUYOU + 0.15, T_SHOUYOU + 0.6))
    d = ImageDraw.Draw(img)
    w = 8
    depth = lerp(1.6, 2.8, k)
    pts = [(cx + dx, oy + 129 + depth * (1 - (dx / w) ** 2)) for dx in np.linspace(-w, w, 9)]
    d.line(pts, fill=(150, 70, 74))
    d.point((cx - w - 1, oy + 128 - int(k)), fill=(150, 70, 74))
    d.point((cx + w + 1, oy + 128 - int(k)), fill=(150, 70, 74))


def draw_sensei(img, t):
    y0, y1 = EYE_Y0, EYE_Y1
    gradient(img, 0, y0, W, y1 - y0, (255, 246, 222), (238, 204, 158), steps=6)
    d = ImageDraw.Draw(img)
    cx, cy = 192, y0 - 30
    for i in range(10):
        a = math.radians(i * 36 + (t - T_SHOUYOU) * 14)
        w = math.radians(7)
        R = 400
        d.polygon([(cx, cy), (cx + math.cos(a - w) * R, cy + math.sin(a - w) * R),
                   (cx + math.cos(a + w) * R, cy + math.sin(a + w) * R)], fill=(255, 250, 236))
    layer = _cached("sensei", _sensei_layer)
    oy = int(round(2 - seg(t, T_SUB, T_BACK) * 4))          # slow upward drift
    img.paste(layer, (0, oy), layer)
    _sensei_mouth(img, t, S_CX, oy)
    fx.sakura(img, t, count=24, seed=17, wind=14, fall=20, area=(0, y0, W, y1))
    zoom(img, 1.0 + 0.05 * seg(t, T_SUB, T_BACK), W / 2, (y0 + y1) / 2)
    fx.sepia(img, 0.25)


def shot_eyes(img, t):
    img.paste((0, 0, 0), (0, 0, W, H))
    show_sensei = (T_SUB <= t < T_SUB + 0.067) or (T_SHOUYOU <= t < T_BACK)
    if show_sensei:
        draw_sensei(img, t)
        if t >= T_SHOUYOU:
            fx.flash(img, 0.6 * (1 - seg(t, T_SHOUYOU, T_SHOUYOU + 0.25)) + 0.6 * seg(t, T_BACK - 0.15, T_BACK))
        vignette(img, 0.5, (255, 250, 236))
    else:
        widen = ease_out(seg(t, T_WIDEN, T_WIDEN + 0.1))
        tremble = seg(t, T_WIDEN + 0.1, T_WIDEN + 0.3)
        draw_eyes(img, t, widen, tremble)
        if t >= T_WIDEN:
            sweat_drop(img, 344, 92 + min(22, (t - T_WIDEN) * 9))
        if t >= T_BACK:
            # tears welling up along the lower lids after the flash of sensei
            k = ease_out(seg(t, T_BACK, T_BACK + 0.35))
            d = ImageDraw.Draw(img)
            for cx, s in EYES:
                pts = []
                for dx in range(-34, 35, 2):
                    f = max(0.0, 1 - (dx / 42.0) ** 2)
                    pts.append((cx + dx, EYE_CY + 13 * f ** 0.9 - s * dx / 42.0 * 0.45 - 1 - k))
                d.line(pts, fill=(176, 222, 255), width=2 if k > 0.5 else 1)
                if step_frame(t, 8) % 2:
                    d.point((cx - 14, int(EYE_CY + 11 - k)), fill=(255, 255, 255))
                    d.point((cx + 18, int(EYE_CY + 10 - k)), fill=(255, 255, 255))
        z = 1.0
        for hb in (T_F + 0.05, T_WIDEN, T_BACK + 0.02):     # heartbeat zoom punches
            if hb <= t < hb + 0.25:
                z += 0.07 * (1 - seg(t, hb, hb + 0.25))
        zoom(img, z, W // 2, EYE_CY)
        if T_WIDEN <= t < T_WIDEN + 0.12:
            fx.flash(img, 0.5 * (1 - seg(t, T_WIDEN, T_WIDEN + 0.12)))
        if t >= T_BACK:
            vignette(img, 0.35, (60, 10, 20))
    # letterbox: black bands outside the eye strip
    img.paste((0, 0, 0), (0, 0, W, EYE_Y0))
    img.paste((0, 0, 0), (0, EYE_Y1, W, H))
    if t >= T_WHITE:
        fx.flash(img, ease_in_out(seg(t, T_WHITE, T_WHITE + 0.4)))


# ================================================================ scene
class ShogunAssassination(Scene):
    id = "s10"
    title = "将军暗杀篇"
    duration = 18.0
    music = [(0.0, "tension"), (T_APPEAR, "battle"), (T_F, None)]
    music_vol = 0.55
    fade_in = 0.3
    fade_out = 0.0          # ends on a held white frame (white-out into s11's flashback)
    subs = [
        (4.10, 6.00, "gintoki", "将军家的头发……"),
        (7.10, 9.05, "hijikata", "是奈落！保护将军！"),
        (12.50, 14.75, "oboro", "你还是和那时一样，白夜叉。"),
    ]

    def render(self, img, t):
        if t < T_B:
            shot_card(img, t)
        elif t < T_C:
            shot_barber(img, t)
        elif t < T_D:
            shot_pass(img, t)
        elif t < T_E:
            shot_panels(img, t)
        elif t < T_F:
            shot_duel(img, t)
        else:
            shot_eyes(img, t)

    def cues(self):
        c = [
            Cue(0.05, "sting_dramatic", vol=0.7),
            Cue(0.45, "whoosh", vol=0.35, pitch=0.8),
            Cue(0.55, "crow", vol=0.6),
            Cue(0.95, "crow", vol=0.45, pitch=1.15),
            # barber shop
            Cue(1.93, "bell_shop", vol=0.4),
        ]
        c += [Cue(ts, "slash", vol=0.16, pitch=2.2) for ts in _snip_times()]
        c += [
            Cue(T_SNIP, "slash", vol=0.7, pitch=1.5),
            Cue(T_SNIP + 0.01, "pop", vol=0.8),
            Cue(T_SNIP + 0.08, "shock", vol=0.6),
            Cue(T_KNOT, "thud", vol=0.35, pitch=1.7),
            Cue(T_CROWB, "crow", vol=0.8),
            Cue(T_SNIP + 0.4, "sweat", vol=0.5),
            Cue(T_STICK, "slap", vol=0.7),
            Cue(T_STICK + 0.06, "sparkle", vol=0.45),
            Cue(T_SLIDE, "slide_down", vol=0.5),
            Cue(T_DROP + 0.08, "fail", vol=0.55),
            # mountain pass
            Cue(T_C, "wind", vol=0.35, dur=T_D - T_C + 0.2),
            Cue(T_C, "footsteps", vol=0.3, dur=T_APPEAR - T_C),
            Cue(T_APPEAR - 0.05, "crow", vol=0.8),
            Cue(T_APPEAR + 0.12, "crow", vol=0.55, pitch=0.85),
            Cue(T_APPEAR, "shing", vol=0.45, pitch=0.8),
            Cue(T_APPEAR + 0.05, "whoosh", vol=0.4, pitch=1.3),
            Cue(T_LEAP, "whoosh", vol=0.7),
            Cue(T_LEAP + 0.5, "land", vol=0.7),
            Cue(T_LEAP + 0.62, "land", vol=0.5, pitch=1.15),
            Cue(T_LEAP + 0.8, "land", vol=0.4, pitch=0.9),
            Cue(T_LANDN + 0.18, "shing", vol=0.8),
            # montage
            Cue(T_D, "battle", vol=0.35, dur=T_CUT - T_D),
            Cue(T_D, "slash", vol=0.5, pitch=0.8),
            Cue(T_D + 0.2, "slash", vol=0.8),
            Cue(T_D + 0.2, "hit", vol=0.6),
            Cue(T_D + 0.32, "slash", vol=0.6, pitch=0.9),
            Cue(T_D + 0.36, "bazooka", vol=0.8),
            Cue(T_D + 0.45, "explosion", vol=0.8),
            Cue(T_P2, "whoosh", vol=0.6),
            Cue(T_P2 + 0.05, "machinegun", vol=0.5),
            Cue(T_P2 + 0.22, "slash_big", vol=0.6),
            Cue(T_P2 + 0.22, "hit", vol=0.6),
            Cue(T_P2 + 0.74, "twinkle", vol=0.5),
            Cue(T_P2 + 0.95, "whoosh", vol=0.4, pitch=1.3),
            Cue(T_P2 + 1.30, "whoosh", vol=0.5, pitch=0.9),
            Cue(T_P2 + 1.33, "punch", vol=0.7),
            Cue(T_P3, "whoosh", vol=0.6, pitch=1.2),
            Cue(T_P3 + 0.06, "pop", vol=0.4),
            Cue(T_P3 + 0.27, "slash", vol=0.8),
            Cue(T_P3 + 0.27, "hit", vol=0.5),
            Cue(T_P3 + 0.84, "punch_big", vol=0.8),
            Cue(T_P3 + 0.95, "bomb_fuse", vol=0.35),
            # second wave in the Shinsengumi panel
            Cue(T_D + 1.15, "whoosh", vol=0.4, pitch=1.2),
            Cue(T_D + 1.50, "land", vol=0.4),
            Cue(T_D + 1.71, "bazooka", vol=0.7),
            Cue(T_D + 1.80, "explosion", vol=0.85),
            Cue(T_CUT, "slash_big", vol=0.9),
            # duel
            Cue(T_E, "wind", vol=0.4, dur=T_F - T_E),
            Cue(T_E + 0.05, "crow", vol=0.5, pitch=0.9),
            Cue(T_THROW, "whoosh", vol=0.5, pitch=1.6),
            Cue(T_DEFLECT, "clang", vol=0.8),
            Cue(T_DASH, "dash", vol=0.7),
            Cue(T_CLASH, "clang", vol=1.0),
            Cue(T_CLASH, "impact", vol=0.9),
            Cue(T_CLASH + 0.08, "crow", vol=0.6, pitch=1.1),
            Cue(T_CLASH + 0.1, "fly_away", vol=0.3),
            Cue(T_PUSH1, "clang", vol=0.45, pitch=1.2),
            Cue(T_PUSH1 + 0.02, "shing", vol=0.3, pitch=1.3),
            Cue(T_PUSH2, "clang", vol=0.6, pitch=0.9),
            Cue(T_PUSH2 + 0.02, "shing", vol=0.35, pitch=1.2),
            # eyes / sensei / white-out
            Cue(T_F + 0.05, "heartbeat", vol=0.8),
            Cue(T_WIDEN, "heartbeat", vol=1.0),
            Cue(T_WIDEN, "shock", vol=0.5, pitch=0.8),
            Cue(T_SUB, "shine", vol=0.5),
            Cue(T_SHOUYOU, "bell", vol=0.45),
            Cue(T_BACK + 0.02, "heartbeat", vol=0.9),
            Cue(T_WHITE, "shine", vol=0.7, pitch=0.8),
        ]
        return c


SCENE = ShogunAssassination()
