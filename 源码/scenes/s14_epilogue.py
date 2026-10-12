"""s14 尾声 Epilogue (24 s; music: rain-only silence -> 'ending' at the hood-off reveal).

SHOT LIST (scene-local seconds)
 A   0.00- 2.60  Yorozuya front in the RAIN (storm), slow push-in. Kagura (parasol, wistful)
                 and Shinpachi wait on the balcony. Brush title 「两年后……」, lightning 2.10.
                 narration「歌舞伎町重建，新八和神乐守着万事屋。」
 B1  2.60- 3.50  Extreme close-up (zoom 4.6->4.2) tracking the boots through a rain puddle
                 (reflection, ripples, splashes 2.88/3.22), tilt up the cloak to the hood:
                 red eyes glint 3.30.
 B2  3.50- 4.80  Wide street in the rain: the hooded wanderer walks in and stops under the
                 balcony; Shinpachi notices 「！」 (4.35), Kagura turns.
 B3a 4.80- 6.50  Close-up push-in (2.3->2.7): lightning 5.05, hand grabs the hood, pulls it
                 back 5.15-5.40 -> silver perm pops out (sparkle) = GINTOKI. Rain stops, clouds
                 break (storm->day crossfade + light shafts). Music 'ending' starts 5.40.
                 sub 银时「我回来了。」
 B3b 6.50- 7.20  Reaction: Kagura & Shinpachi on the balcony, tears welling; Kagura crouches.
 C1  7.20- 8.60  Street (day, wet road, zoom 1.5): Kagura leaps off the balcony 「银酱——！！」,
                 DROPKICK 7.85 (smash-zoom 2.4, 2-frame ink/red silhouette impact frame, speed
                 lines, 砰!!) -> Gintoki pinwheels left into a pile of rain barrels 8.12
                 (哐当!!, barrels fly) and ends upside-down; the cloak flutters down;
                 Shinpachi runs down the stairs.
 C2  8.60-10.60  Medium (zoom 2.2->2.4): Gintoki flat on the road (dizzy stars), Kagura
                 bawling behind him; Shinpachi skids in, huge tsukkomi point 8.75 (speed
                 lines, tears). sub 新八「你到底跑哪去了！！」 -> 9.72 Gintoki lifts a limp
                 hand 「……哟。」 -> 10.05 Shinpachi's anger vein.
 D   10.60-15.95 "Everyday life is back" quick cuts (white pop on each cut, corner caption
                 「日常·回归中」):
  D1 10.60-11.75 Street: Kondo peeks from his bush -> Otae super punch 11.00 -> camera tilts up
                 after the spinning gorilla -> twinkle star in the sky 11.42.
  D2 11.75-12.90 Riverbank under a cherry tree: Okita fires the bazooka 12.00 at smoking
                 Hijikata -> BOOM 12.08 -> soot + afro, 「总悟——！！」.
  D3 12.90-14.93 Rotating sunburst close-up: 「假发～」 bubble from off-screen, Katsura whips
                 round 13.05 (x3), 「不是假发」 13.18 / 「是桂！」 slam 13.40; Elizabeth pops up
                 with sign 「没错」 13.95.  sub 桂「不是假发，是桂！」
  D4 14.93-15.95 Yorozuya front: Gintoki waves at his dog, Sadaharu lunges and CHOMPS his
                 head 15.08 (zoom punch), lifts him - arms flailing, legs kicking; Kagura
                 cheers, Shinpachi sweats.
 E   15.95-19.00 Freeze-frame (grey) -> giant red hanko 「完」 slams 16.12 -> crow, silence ->
                 thumps 16.85/17.00 -> Gintoki KICKS the stamp away 17.12 (colour returns), it
                 twinkles off as a star 17.62; Gintoki points up (zoom 2.6).
                 sub 银时「才不会完呢！」
 F   19.00-21.90 Dusk Kabukicho, camera tracks along a two-row PARADE of the whole cast
                 (Kagura riding Sadaharu, Gintoki reading Jump at the tail); credits
                 「原作：空知英秋《银魂》」「本片为同人像素致敬作品」.
 G   21.90-24.00 Yorozuya office at dusk: Gintoki reads Jump on the sofa, Kagura & Sadaharu
                 asleep, Shinpachi in the boss chair; 「感谢观看」; he glances at camera 23.05,
                 push-in + iris closes on Gintoki (23.3-23.92).
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import (Scene, Cue, W, H, seg, lerp, clamp, ease_in, ease_out, ease_in_out,
                         ease_out_back, wave, step_frame, rng, arc)
from engine.gfx import (PAL, INK, paste, rect, overlay_rect, gradient, shade, tint, set_alpha,
                        rotate_nearest, scale_nearest, flip_h, stamp_line, pset, silhouette)
from engine import fx
from engine.text import draw_text, text_width, text_sprite, sfx_text, speech_bubble
from chars import draw_char, render_sprite, get_def
from bg import common as C, kabukicho as K, yorozuya as Y
from scenes import _s14_art as A

# ---------------------------------------------------------------- shot times
T_B1, T_B2, T_B3, T_B3B = 2.60, 3.50, 4.80, 6.50
T_C1, T_C2 = 7.20, 8.60
T_D1, T_D2, T_D3, T_D4 = 10.60, 11.75, 12.90, 14.93
T_E, T_F, T_G, T_END = 15.95, 19.00, 21.90, 24.00

T_LIGHT = (2.10, 5.05)             # C.storm_flash bolts inside the rainy part
T_HOOD0, T_HOOD1 = 5.15, 5.40      # hood pulled back
T_CLEAR0, T_CLEAR1 = 5.45, 6.40    # storm -> day crossfade
T_LEAP, T_KICK = 7.25, 7.85        # Kagura launch / dropkick impact
T_CRASH = 8.12                     # Gintoki ploughs into the barrel pile
T_TSUK = 8.75
T_PUNCH = 11.00                    # Otae
T_STAR1 = 11.42
T_FIRE, T_BOOM = 12.00, 12.08      # Okita
T_TURN, T_ZURA, T_KATSURA = 13.05, 13.18, 13.40
T_ELI = 13.90                      # Elizabeth pops up with her 「没错」 sign
T_STAMP = 16.12
T_BOOT = 17.12
T_STAR2 = 17.62

YX = K.YOROZUYA_X                  # 370
FLOOR = K.FLOOR_Y                  # 160
BAL_Y = K.STREET_BALCONY_Y         # 84 (street) ; K.BALCONY_Y = 120 (front shot)
FRONT_FLOOR = K.FRONT_FLOOR_Y      # 196


# ---------------------------------------------------------------- helpers
def zc(k, cx, cy):
    """Clamp a zoom centre so the zoom box stays inside the canvas."""
    hw, hh = W / (2 * k), H / (2 * k)
    return clamp(cx, hw, W - hw), clamp(cy, hh, H - hh)


def zoom(img, k, cx, cy):
    if k <= 1.001:
        return W / 2, H / 2
    cx, cy = zc(k, cx, cy)
    fx.zoom(img, k, cx, cy)
    return cx, cy


def scr(x, y, k, c):
    """World point -> screen point after zoom(k) about the clamped centre c."""
    if k <= 1.001:
        return x, y
    return W / 2 + (x - c[0]) * k, H / 2 + (y - c[1]) * k


def blink_expr(t, base, seed=0.0, period=3.3):
    return "blink" if ((t + seed) % period) < 0.12 else base


def railing_strip(img, cam):
    """Copy the balcony railing (street coords) so it can be re-pasted over characters."""
    x0 = int(max(0, K.BALCONY_X0 - cam))
    x1 = int(min(W, K.BALCONY_X1 - cam))
    if x1 <= x0:
        return None
    return img.crop((x0, 73, x1, 88)), x0


def paste_strip(img, st):
    if st is not None:
        img.paste(st[0], (st[1], 73))


def street_blend(img, cam, t, tod_a, tod_b, k, wet=None):
    """Street in tod_a crossfaded to tod_b by k (0..1)."""
    if k <= 0:
        K.street(img, int(cam), t, tod_a, wet=wet)
        return
    if k >= 1:
        K.street(img, int(cam), t, tod_b, wet=wet)
        return
    a = Image.new("RGB", (W, H))
    K.street(a, int(cam), t, tod_a, wet=wet)
    K.street(img, int(cam), t, tod_b, wet=wet)
    img.paste(Image.blend(a, img, k))


_SHAFT = {}


def light_shafts(img, amount, t, color=(255, 236, 190)):
    """Diagonal dithered sun shafts from the top-left (clouds breaking)."""
    if amount <= 0:
        return
    m = _SHAFT.get("m")
    if m is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        u = xx - yy * 0.55
        band = np.zeros((H, W), np.float32)
        for c0, w0, s in ((20, 22, 1.0), (80, 10, 0.7), (130, 30, 0.9), (215, 14, 0.6), (270, 24, 0.5)):
            band = np.maximum(band, s * np.clip(1 - np.abs(u - c0) / w0, 0, 1))
        band *= np.clip(1.2 - yy / H, 0, 1)
        _SHAFT["m"] = m = band
    k = amount * (0.85 + 0.15 * math.sin(t * 2.3))
    dm = C.bayer(H, W) if hasattr(C, "bayer") else None
    a = np.asarray(img).astype(np.float32)
    lv = np.floor(m * k * 3 + (dm if dm is not None else 0.5)) / 3 * 0.22
    a = a + (np.array(color, np.float32) - a) * lv[..., None]
    img.paste(Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGB"))


def exclaim(img, x, y, t, t0, text="!", color=(255, 60, 60), size=16):
    if t < t0:
        return
    k = ease_out_back(seg(t, t0, t0 + 0.15))
    spr = A.brush_text(text, size, color, INK, 2 if size > 16 else 1, "hei")
    if k < 1:
        spr = spr.resize((max(1, int(spr.width * k)), max(1, int(spr.height * k))), Image.NEAREST)
    paste(img, spr, x, y, anchor="bottom")


def sweat(img, x, y, t, t0=0.0):
    ph = (t - t0) * 3 % 1.0
    yy = int(y + ph * 5)
    rect(img, x, yy, 2, 3, INK)
    pset(img, x, yy + 3, INK)
    pset(img, x, yy + 1, (170, 220, 255))


def tear_stream(img, x, y, t, direction=1, seed=0):
    """Comedic anime tear fountains (little arcs of blue drops)."""
    d = ImageDraw.Draw(img)
    for i in range(7):
        ph = ((t * 3.0) + i / 7) % 1.0
        px = x + direction * ph * 10
        py = y - 2 * math.sin(ph * math.pi) + ph * ph * 6
        c = (150, 210, 255) if i % 2 else (220, 245, 255)
        d.rectangle([px, py, px + 1, py + 1], fill=c)


def dizzy_stars(img, x, y, t, r=7):
    """Three little stars circling a knocked-out head (INK-backed so they read on white hair)."""
    d = ImageDraw.Draw(img)
    for i in range(3):
        a = t * 5 + i * 2 * math.pi / 3
        px, py = int(x + math.cos(a) * r), int(y + math.sin(a) * r * 0.35)
        c = (255, 230, 90) if i != 1 else (255, 255, 255)
        d.rectangle([px - 2, py - 1, px + 2, py + 1], fill=INK)
        d.rectangle([px - 1, py - 2, px + 1, py + 2], fill=INK)
        d.line([(px - 1, py), (px + 1, py)], fill=c)
        d.line([(px, py - 1), (px, py + 1)], fill=c)


def twinkle_star(img, x, y, t, t0, dur=0.6, size=7):
    """Something launched into the sky ends as a twinkling star (outlined so it reads
    on any sky)."""
    if not (t0 <= t < t0 + dur):
        return
    p = (t - t0) / dur
    pop = ease_out_back(min(1.0, p * 5))
    s = max(2, int(size * pop * (0.75 + 0.25 * math.sin(t * 40))))
    d = ImageDraw.Draw(img)
    s2 = max(1, s // 2)
    for (w, col) in ((3, INK), (1, (255, 236, 120))):
        d.line([(x - s, y), (x + s, y)], fill=col, width=w)
        d.line([(x, y - s), (x, y + s)], fill=col, width=w)
    for (w, col) in ((3, INK), (1, (255, 200, 90))):
        d.line([(x - s2, y - s2), (x + s2, y + s2)], fill=col, width=w)
        d.line([(x - s2, y + s2), (x + s2, y - s2)], fill=col, width=w)
    d.rectangle([x - 2, y - 2, x + 2, y + 2], fill=INK)
    d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=(255, 255, 255))
    # a few glitter pixels drifting off
    for i in range(5):
        r = rng("glit", i, int(t0 * 10))
        a = r.uniform(0, 6.28)
        rr = (t - t0) * r.uniform(20, 45)
        pset(img, x + math.cos(a) * rr, y + math.sin(a) * rr, (255, 250, 210))


def corner_caption(img, t):
    """Variety-show corner label shown during the chaos montage."""
    if not (T_D1 <= t < T_E):
        return
    k = ease_out(seg(t, T_D1, T_D1 + 0.2))
    x = int(-110 + 116 * k)
    d = ImageDraw.Draw(img)
    d.polygon([(x - 2, 4), (x + 104, 4), (x + 96, 22), (x - 2, 22)], fill=INK)
    d.polygon([(x, 6), (x + 100, 6), (x + 93, 20), (x, 20)], fill=(228, 59, 68))
    draw_text(img, x + 6, 7, "日常·回归中", (255, 255, 255), outline=INK)
    if step_frame(t, 3) % 2 == 0:
        rect(img, x + 82, 10, 5, 5, (255, 236, 120))


# ============================================================ SHOT A — 两年后 (rain)
def shot_a(img, t):
    K.yorozuya_front(img, t, "storm")
    by = K.BALCONY_Y
    draw_char(img, "kagura", 150, by, "umbrella_open", t, facing=1, expr=blink_expr(t, "sad", 0.7))
    draw_char(img, "shinpachi", 196, by, "idle", t, facing=-1, expr=blink_expr(t, "sad", 1.9))
    K.yorozuya_front_fg(img, t, "storm")
    fx.rain(img, t, count=120, seed=4, color=(150, 166, 206), speed=420, slant=0.2, length=7)
    k = 1.0 + 0.14 * ease_in_out(seg(t, 0, T_B1))
    zoom(img, k, 180, 112)
    fx.flash(img, C.storm_flash(t) * 0.4, (220, 230, 255))
    fx.rain(img, t, count=30, seed=9, color=(190, 205, 235), speed=560, slant=0.2, length=11)
    # title
    a = seg(t, 0.25, 0.8)
    if a > 0:
        spr = A.brush_text("两年后……", 34, (255, 244, 222), INK, 2)
        dy = int((1 - ease_out(a)) * 6)
        overlay_rect(img, 0, 16, W, 44, (8, 8, 20), 0.35 * a)
        paste(img, spr, W // 2, 36 - dy, anchor="center", alpha=a)
        if a >= 1:
            s2 = "—  TWO YEARS LATER  —"
            draw_text(img, W // 2 - text_width(s2) // 2, 52, s2, (200, 210, 235), outline=INK)


# ============================================================ SHOT B1 — puddle
B1_CAM = YX - W // 2 - 150
PUDDLE = (198, 163, 24, 5)         # cx, cy, rx, ry (screen == world, static cam)
B1_X0, B1_V = 166.0, 30.0          # wanderer x at T_B1, walking speed


def _puddle_mask():
    m = A_CACHE.get("pmask")
    if m is None:
        m = Image.new("L", (W, H), 0)
        cx, cy, rx, ry = PUDDLE
        ImageDraw.Draw(m).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
        A_CACHE["pmask"] = m
    return m


A_CACHE = {}


def shot_b1(img, t):
    lt = t - T_B1
    K.street(img, B1_CAM, t, "storm")
    cx, cy, rx, ry = PUDDLE
    d = ImageDraw.Draw(img)
    d.ellipse([cx - rx - 1, cy - ry - 1, cx + rx + 1, cy + ry + 1], fill=(52, 56, 74))
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(70, 80, 110))
    d.arc([cx - rx + 2, cy - ry + 1, cx + rx - 2, cy + ry - 1], 200, 330, fill=(130, 146, 180))
    x = B1_X0 + B1_V * lt
    spr, ax, ay = A.hooded_gintoki("walk", t, 0.0)
    # reflection in the puddle (upside-down wanderer, tinted by the water)
    refl = spr.transpose(Image.FLIP_TOP_BOTTOM)
    refl = tint(refl, (80, 96, 140), 0.35)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lay.paste(refl, (int(x - ax), int(FLOOR + 1 - (refl.height - 1 - ay))))
    al = np.minimum(np.asarray(lay)[..., 3], (np.asarray(_puddle_mask()).astype(np.uint16) * 3 // 4))
    lay.putalpha(Image.fromarray(al.astype(np.uint8), "L"))
    img.paste(lay, (0, 0), lay)
    # rain ripples on the puddle
    for i in range(4):
        r = rng("ripple", i, int(t * 4))
        px_ = cx + r.uniform(-rx + 4, rx - 4)
        py_ = cy + r.uniform(-ry + 1, ry - 1)
        ph = (t * 4) % 1.0
        rr = 1 + ph * 4
        d.ellipse([px_ - rr, py_ - rr * 0.35, px_ + rr, py_ + rr * 0.35], outline=(150, 166, 200))
    sp0 = (int(x - ax), int(FLOOR - ay))
    img.paste(spr, sp0, spr)
    for ts, sx in B1_SPLASH:
        fx.burst(img, t, ts, int(B1_X0 + B1_V * (ts - T_B1)) + sx, FLOOR, n=14,
                 colors=[(200, 214, 245), (150, 170, 215)], speed=(20, 55), gravity=260, life=0.4,
                 spread=(195, 345), seed=int(ts * 10))
        if ts <= t < ts + 0.5:      # splash ring
            rr = 2 + (t - ts) * 26
            fxx = B1_X0 + B1_V * (ts - T_B1) + sx
            d.ellipse([fxx - rr, FLOOR + 1 - rr * 0.25, fxx + rr, FLOOR + 1 + rr * 0.25],
                      outline=(170, 186, 220))
    # extreme close-up that tracks the wanderer: boots splashing through the puddle,
    # then a slow tilt up the cloak to the two red eyes glinting in the hood's shadow
    k = lerp(4.6, 4.2, seg(t, T_B1, T_B2))
    tilt = ease_in_out(seg(t, 2.98, 3.36))
    cy = lerp(FLOOR + 6, FLOOR - 22, tilt)
    c = zoom(img, k, x + 6, cy)
    fx.flash(img, C.storm_flash(t) * 0.3, (220, 230, 255))
    fx.rain(img, t, count=50, seed=11, color=(170, 184, 220), speed=620, slant=0.15, length=12)
    fx.vignette(img, 0.25 + 0.25 * tilt, (6, 6, 16))
    if t >= B1_GLINT:
        for ex, ey in A.eye_points(spr):
            gx, gy = scr(sp0[0] + ex + 0.5, sp0[1] + ey + 0.5, k, c)
            twinkle_eye(img, int(gx), int(gy), t, B1_GLINT)


B1_GLINT = 3.30


def twinkle_eye(img, x, y, t, t0):
    """Red 'kira' glint on a glowing eye (grows, holds, fades)."""
    p = (t - t0) / 0.22
    if p < 0:
        return
    s = int(round(16 * math.sin(min(1.0, p) * math.pi / 2) * (1.0 if p < 1.4 else 0.6)))
    d = ImageDraw.Draw(img)
    if s > 0:
        d.line([(x - s, y), (x + s, y)], fill=(230, 40, 50), width=3)
        d.line([(x - s - 4, y), (x + s + 4, y)], fill=(255, 110, 110))
        d.line([(x, y - s // 2), (x, y + s // 2)], fill=(255, 110, 110))
        d.line([(x - s // 2, y), (x + s // 2, y)], fill=(255, 240, 240))
    d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=(255, 245, 245))


B1_SPLASH = ((2.88, 4), (3.22, 2))


# ============================================================ SHOT B2 — wide rain
def b2_cam(t):
    return 150 + 22 * ease_out(seg(t, T_B2, T_B3))


def shot_b2(img, t):
    cam = b2_cam(t)
    K.street(img, int(cam), t, "storm")
    draw_pile_static(img, int(cam))
    st = railing_strip(img, int(cam))
    # balcony: Shinpachi notices at 4.35
    sx, kx = 362 - cam, 398 - cam
    if t < 4.35:
        draw_char(img, "shinpachi", sx, BAL_Y, "idle", t, facing=-1, expr=blink_expr(t, "sad"))
    else:
        draw_char(img, "shinpachi", sx, BAL_Y, "shock", t, p=seg(t, 4.35, 5.0), facing=-1)
    draw_char(img, "kagura", kx, BAL_Y, "umbrella_open", t, facing=1 if t < 4.5 else -1,
              expr=blink_expr(t, "sad") if t < 4.5 else "shock")
    paste_strip(img, st)
    # the wanderer
    wx = lerp(282, 314, seg(t, T_B2, 4.45))
    pose = "walk" if t < 4.45 else "idle"
    A.draw_hooded(img, wx - cam, FLOOR, pose, t, 0.0, facing=1)
    fx.rain(img, t, count=110, seed=5, color=(150, 166, 206), speed=420, slant=0.2, length=7)
    k = 1.12 + 0.06 * seg(t, T_B2, T_B3)
    c = zoom(img, k, 200, 116)
    exclaim(img, *[int(v) for v in scr(sx, BAL_Y - 36, k, c)], t, 4.35, "！", size=22)
    if t >= 4.55:
        exclaim(img, *[int(v) for v in scr(kx, BAL_Y - 36, k, c)], t, 4.55, "!?", (255, 200, 60), size=22)
    gx_, gy_ = scr(sx + 3, BAL_Y - 22, k, c)
    fx.sparkle(img, int(gx_), int(gy_), t, 4.36, size=6)          # glasses glint
    fx.flash(img, C.storm_flash(t) * 0.4, (220, 230, 255))


# ============================================================ SHOT B3 — hood off
B3_CAM = 172
GIN_WX = 314


def hood_state(t):
    if t < T_HOOD0:
        return 0.0, None
    if t < T_HOOD1:
        k = seg(t, T_HOOD0, T_HOOD1)
        return (0.25 if k < 0.5 else 0.45), (150 if k < 0.5 else 170)
    return 1.0, None


def shot_b3a(img, t):
    clear = seg(t, T_CLEAR0, T_CLEAR1)
    street_blend(img, B3_CAM, t, "storm", "day", ease_in_out(clear), wet=True)
    draw_pile_static(img, B3_CAM)
    x = GIN_WX - B3_CAM
    hood, arm = hood_state(t)
    expr = None
    if t >= T_HOOD1:
        expr = blink_expr(t, "normal", 0.4) if t < 6.2 else "smug"
    A.draw_hooded(img, x, FLOOR, "idle", t, hood, facing=1, arm=arm, expr=expr)
    # hair 'poof' when the perm springs free
    if t >= T_HOOD1:
        fx.burst(img, t, T_HOOD1, x + 1, FLOOR - 30, n=10, colors=[(255, 255, 255), (220, 226, 245)],
                 speed=(20, 50), gravity=-10, life=0.35, seed=51)
    k = lerp(2.3, 2.7, ease_in_out(seg(t, T_B3, T_B3B)))
    if t >= T_HOOD1:     # little zoom punch as the silver perm springs free
        k += 0.28 * (1 - ease_out(seg(t, T_HOOD1, T_HOOD1 + 0.35)))
    # keep his feet above the dialogue box (y 173+) once 「我回来了。」 appears
    c = zoom(img, k, x + 2, lerp(FLOOR - 25, FLOOR - 18, ease_in_out(seg(t, 5.2, 5.5))))
    light_shafts(img, ease_in_out(clear) * 0.9, t)
    n = int(80 * (1 - clear))
    if n > 0:
        fx.rain(img, t, count=n, seed=6, color=(170, 184, 220), speed=600, slant=0.18, length=12)
    fx.flash(img, C.storm_flash(t) * 0.35 * (1 - clear), (225, 235, 255))
    if t >= T_HOOD1:
        hx, hy = scr(x - 2, FLOOR - 36, k, c)
        fx.sparkle(img, int(hx), int(hy), t, T_HOOD1 + 0.02, size=9)
        fx.sparkle(img, int(hx) + 26, int(hy) + 10, t, T_HOOD1 + 0.18, size=6)


def shot_b3b(img, t):
    street_blend(img, B3_CAM, t, "storm", "day", 1.0, wet=True)
    st = railing_strip(img, B3_CAM)
    sx, kx = 362 - B3_CAM, 396 - B3_CAM
    draw_char(img, "shinpachi", sx, BAL_Y, "cry", t, facing=-1)
    if t < 6.95:
        draw_char(img, "kagura", kx, BAL_Y, "idle", t, facing=-1, expr="cry", arm_f=20)
    else:
        draw_char(img, "kagura", kx, BAL_Y, "land", t, p=0.1, facing=-1, expr="determined")
    paste_strip(img, st)
    k = lerp(2.3, 2.5, seg(t, T_B3B, T_C1))
    c = zoom(img, k, (sx + kx) / 2, BAL_Y - 16)
    light_shafts(img, 0.9, t)
    # glistening tears
    for cx_, ph in ((sx, 0.0), (kx, 0.3)):
        px, py = scr(cx_ - 4, BAL_Y - 22, k, c)
        fx.sparkle(img, int(px), int(py), t, T_B3B + 0.1 + ph, size=4)
    if t >= 6.95:
        hx, hy = scr(kx, BAL_Y - 36, k, c)
        exclaim(img, int(hx), int(hy), t, 6.95, "！", (255, 90, 70))


# ============================================================ SHOT C1 — dropkick
C1_CAM = 160
K_START = (398 - C1_CAM, BAL_Y)
GIN_C1 = (GIN_WX - C1_CAM, FLOOR)            # (154, 160)
K_HIT = (GIN_C1[0] + 30, FLOOR - 22)


def kagura_c1(t):
    """(x, y, pose, p, facing) of Kagura during the dropkick shot."""
    if t < T_LEAP:
        return K_START[0], K_START[1], "land", 0.1, -1
    if t < T_KICK:
        k = seg(t, T_LEAP, T_KICK)
        e = ease_in(k) * 0.7 + k * 0.3
        x = lerp(K_START[0], K_HIT[0], e)
        y = lerp(K_START[1], K_HIT[1], e) - 16 * math.sin(math.pi * min(1.0, k * 1.15))
        return x, y, "dropkick", lerp(0.15, 0.75, k), -1
    if t < T_KICK + 0.07:
        return K_HIT[0], K_HIT[1], "dropkick", 0.75, -1
    if t < 8.05:
        k = seg(t, T_KICK + 0.07, 8.05)
        x, y = arc(K_HIT, (190, FLOOR), k, 22)
        return x, y, "jump", None, -1
    return 190, FLOOR, ("land" if t < 8.2 else "shout"), seg(t, 8.05, 8.3), -1


def shinpachi_c1(t):
    """Shinpachi runs along the balcony, down the outside stairs, onto the street."""
    (xb, yb), (xt, yt) = K.STAIRS                       # bottom (382,152), top (440,84)
    t0, t1, t2, t3 = 7.35, 7.70, 8.30, 8.60
    if t < t0:
        return 362, BAL_Y, "shock", 1
    if t < t1:
        return lerp(362, xt - 2, seg(t, t0, t1)), BAL_Y, "run", 1
    if t < t2:
        wx = lerp(xt - 2, xb, seg(t, t1, t2))
        y = K.stairs_y(wx)
        return wx, (y if y is not None else BAL_Y), "run", -1
    return lerp(xb, 372, seg(t, t2, t3)), FLOOR, "run", -1


def shot_c1(img, t):
    K.street(img, C1_CAM, t, "day", wet=True)
    st = railing_strip(img, C1_CAM)
    sx, sy, spose, sf = shinpachi_c1(t)
    on_balcony = sy == BAL_Y and sx < K.BALCONY_X1 - 2
    if on_balcony:
        draw_char(img, "shinpachi", sx - C1_CAM, sy, spose, t, p=0.6, facing=sf,
                  expr="shock" if spose == "shock" else None)
    kx, ky, kpose, kp, kf = kagura_c1(t)
    if t < T_LEAP:
        draw_char(img, "kagura", kx, ky, kpose, t, p=kp, facing=kf, expr="determined")
    paste_strip(img, st)
    if not on_balcony:
        draw_char(img, "shinpachi", sx - C1_CAM, sy, spose, t, facing=sf, expr="shock")
    # Gintoki
    gx, gy = GIN_C1
    if t < T_KICK:
        expr = "shock" if t >= 7.62 else "normal"
        A.draw_hooded(img, gx, gy, "idle", t, 1.0, facing=1, expr=expr)
        if t >= 7.62:
            sweat(img, gx + 9, gy - 34, t, 7.62)
    else:
        # the cloak comes off and flutters down where he stood
        cl = seg(t, T_KICK, 8.5)
        clx = gx - 34 * ease_out(cl) + wave(t, 2.2, 4)
        cly = lerp(gy - 22, gy - 2, ease_in(cl)) - 8 * math.sin(cl * math.pi)
        if cl < 1:
            A.draw_cloth(img, clx, cly, t, wave(t, 1.6, 35), 1.0)
        else:
            A.draw_cloth(img, gx - 34, gy, t, 0, lying=True)
    draw_pile(img, t)
    if t >= T_KICK:
        if t < T_CRASH:
            # spinning like a pinwheel across the street...
            k = seg(t, T_KICK, T_CRASH)
            fx_, fy_ = arc((gx - 4, gy - 16), (PILE_X + 2, gy - 4), k, 10)
            draw_char(img, "gintoki", fx_, fy_, "fly", t * 2.2, shadow=False)
        else:
            # ...and ends upside-down in the barrels, legs twitching
            tw = 0.245 if step_frame(t, 8) % 2 else 0.255
            if t >= 8.45:
                tw = 0.25
            draw_char(img, "gintoki", PILE_X + 1, FLOOR - 25, "fly", tw, expr="hurt", shadow=False)
    # Kagura in the air / landed
    if t >= T_LEAP:
        draw_char(img, "kagura", kx, ky, kpose, t, p=kp, facing=kf, shadow=ky > FLOOR - 4,
                  expr="shout" if kpose in ("dropkick", "shout") else None)
    if T_LEAP <= t < T_KICK:
        fx.motion_lines(img, t, color=(255, 255, 255), count=6, direction=1, seed=21,
                        y0=int(ky) - 30, y1=int(ky) - 4, speed=700, length=(10, 26))
    if t >= 8.05:
        fx.smoke_puff(img, t, 8.05, 190, FLOOR, size=10, seed=7)
    fx.burst(img, t, T_KICK, K_HIT[0] - 6, K_HIT[1] - 8, n=18,
             colors=[(255, 255, 255), (255, 230, 90)], speed=(60, 160), gravity=80, life=0.45, seed=31)
    for i in range(4):   # last drops falling from the eaves
        r = rng("drip", i)
        x = r.randint(90, 330)
        y = (t * 120 + r.uniform(0, 60)) % 60 + 92
        pset(img, x, y, (170, 190, 230))
    # ---- camera
    k = C1_ZOOM[0] + 0.05 * seg(t, T_C1, T_C2)
    zx, zy = C1_ZOOM[1], C1_ZOOM[2]
    if t >= T_KICK:      # smash-zoom onto the impact, easing back out to catch the crash
        sm = ease_in_out(1 - seg(t, T_KICK + 0.08, T_CRASH + 0.06))
        k = lerp(k, 2.4, sm)
        zx, zy = lerp(zx, K_HIT[0] - 4, sm), lerp(zy, K_HIT[1] - 4, sm)
    c = zoom(img, k, zx, zy)
    # the crash into the barrel pile
    px, py = scr(PILE_X, FLOOR - 8, k, c)
    fx.smoke_puff(img, t, T_CRASH, int(px), int(py) + 6, size=20, seed=3)
    fx.smoke_puff(img, t, T_CRASH + 0.05, int(px) + 16, int(py) + 12, size=14, seed=4)
    fx.burst(img, t, T_CRASH, int(px), int(py), n=14, colors=[A.BR_L, A.BR_D, (255, 255, 255)],
             speed=(60, 150), gravity=320, life=0.5, size=(1, 3), seed=33, spread=(190, 350))
    sfx_text(img, int(px) + 12, int(py) - 72, "哐当！！", t, T_CRASH, 0.6, size=24, angle=-12,
             color=(255, 255, 255))
    if T_LEAP <= t < 7.95:
        spr = A.rotated("银酱——！！", 24, (255, 120, 70), 6)
        jx = int(wave(t, 14, 1))
        k_in = ease_out_back(seg(t, T_LEAP, T_LEAP + 0.12))
        if k_in < 0.999:
            spr = spr.resize((max(1, int(spr.width * k_in)), max(1, int(spr.height * k_in))),
                             Image.NEAREST)
        paste(img, spr, 118 + jx, 34, anchor="center", alpha=1 - seg(t, 7.8, 7.95))
    hx, hy = scr(K_HIT[0], K_HIT[1], k, c)
    sfx_text(img, int(hx) - 20, int(hy) - 40, "砰！！", t, T_KICK + 0.07, 0.4, size=30, angle=10)
    # impact frame (2 frames: ink silhouettes on white, then white on black) + speed lines
    if T_KICK <= t < T_KICK + 0.07:
        impact_c1(img, t, k, c)
    elif T_KICK + 0.07 <= t < T_KICK + 0.2:
        fx.speed_lines(img, t, int(hx), int(hy) - 8, (255, 255, 255), count=44, inner=60, seed=8)
    dx, dy = fx.shake_offset(t, T_KICK, 0.35, 5, seed=1)
    dx2, dy2 = fx.shake_offset(t, T_CRASH, 0.25, 3, seed=2)
    fx.shift(img, dx + dx2, dy + dy2)


C1_ZOOM = (1.5, 196, 118)

# a pile of rain barrels by the bookshop - the dropkick's landing zone
PILE_X = 108
PILE = ((-6, 0, 0), (7, 0, 1), (1, -13, 0))          # (dx, dy, variant) bottom-left, bottom-right, top
PILE_V = ((-70, -150, -540), (60, -190, 620), (-10, -260, 900))   # vx, vy, spin deg/s


def draw_pile_static(img, cam):
    """The same barrel pile seen from another camera (street cam offset)."""
    for dx, dy, v in PILE:
        paste(img, A.barrel_sprite(v), PILE_X + C1_CAM - cam + dx, FLOOR + dy + 1, anchor="bottom")


def draw_pile(img, t):
    for (dx, dy, v), (vx, vy, spin) in zip(PILE, PILE_V):
        spr = A.barrel_sprite(v)
        x0, y0 = PILE_X + dx, FLOOR + dy
        if t < T_CRASH:
            paste(img, spr, x0, y0 + 1, anchor="bottom")
            continue
        dt = t - T_CRASH
        g = 520.0
        # time when it hits the floor again (y measured at the barrel's bottom)
        disc = vy * vy - 2 * g * (y0 - FLOOR)
        t_land = (-vy + math.sqrt(max(0.0, disc))) / g
        if dt < t_land:
            x = x0 + vx * dt
            y = y0 + vy * dt + 0.5 * g * dt * dt
            rs = rotate_nearest(spr, spin * dt)
            paste(img, rs, x, y - spr.height // 2, anchor="center")
        else:                                  # rolled onto its side
            x = x0 + vx * t_land + vx * 0.25 * min(0.3, dt - t_land)
            rs = rotate_nearest(spr, 90 if vx < 0 else -90)
            paste(img, rs, x, FLOOR + 1, anchor="bottom")


def impact_c1(img, t, k, c):
    second = t >= T_KICK + 0.034
    bgc, ink = ((12, 10, 18), (255, 255, 255)) if second else ((255, 255, 255), (12, 10, 18))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gspr, gax, gay = A.hooded_gintoki("idle", t, 1.0, expr="shock")
    lay.paste(silhouette(gspr, ink), (GIN_C1[0] - gax, GIN_C1[1] - gay), gspr)
    kspr, kax, kay = render_sprite("kagura", "dropkick", t, p=0.75, facing=-1)
    lay.paste(silhouette(kspr, (228, 40, 56)), (int(K_HIT[0] - kax), int(K_HIT[1] - kay)), kspr)
    if k > 1.001:
        hw, hh = W / (2 * k), H / (2 * k)
        lay = lay.resize((W, H), Image.NEAREST, box=(c[0] - hw, c[1] - hh, c[0] + hw, c[1] + hh))
    img.paste(bgc, (0, 0, W, H))
    img.paste(lay, (0, 0), lay)
    hx, hy = scr(K_HIT[0], K_HIT[1], k, c)
    fx.speed_lines(img, t, int(hx), int(hy) - 6, ink, count=54, inner=70, seed=18)


# ============================================================ SHOT C2 — tsukkomi
C2_CAM = 20
GIN_C2 = (176, FLOOR)
T_YO = 9.72                        # Gintoki lifts a limp hand: 「……哟。」
T_VEIN = 10.05                     # ...and Shinpachi's anger vein pops


def shot_c2(img, t):
    K.street(img, C2_CAM, t, "day", wet=True)
    gx, gy = GIN_C2
    # Kagura kneels behind him, bawling (drawn first so he stays readable in front)
    kx, ky = gx + 8, gy - 8
    kpose = "shout" if (t % 0.9) < 0.55 else "cry"
    draw_char(img, "kagura", kx, ky, kpose, t, facing=-1, expr="cry", shadow=False)
    # Gintoki flat on his back, twitching; at T_YO a limp hand goes up
    arm = 170
    if t >= T_YO:
        arm = lerp(170, 90, ease_out_back(seg(t, T_YO, T_YO + 0.18)))
    jit = 1 if (t < T_YO and step_frame(t, 10) % 3 == 0) else 0
    draw_char(img, "gintoki", gx, gy - jit, "lie", t, arm_f=arm,
              expr="hurt" if t < T_YO else "normal")
    # Shinpachi skids in and delivers the tsukkomi
    if t < T_TSUK:
        sx = lerp(296, 228, ease_out(seg(t, T_C2, T_TSUK)))
        draw_char(img, "shinpachi", sx, FLOOR, "run", t, facing=-1, expr="shock")
        fx.smoke_puff(img, t, T_C2 + 0.05, int(sx) + 6, FLOOR, size=6, seed=12)
    else:
        sx = 228
        p = seg(t, T_TSUK, T_TSUK + 0.4)
        expr = "shout" if step_frame(t, 8) % 2 == 0 else "cry"
        if t >= T_VEIN:
            expr = "angry" if step_frame(t, 8) % 2 == 0 else "shout"
        tremble = int(wave(t, 22, 1)) if t >= T_VEIN else 0
        draw_char(img, "shinpachi", sx + tremble, FLOOR, "point", t, p=p, facing=-1, expr=expr)
    k = lerp(2.2, 2.4, ease_in_out(seg(t, T_C2, T_D1)))
    c = zoom(img, k, 199, 136)
    # dizzy stars over Gintoki's head (head is on the left of the lying sprite)
    hx, hy = scr(gx - 10, gy - 16, k, c)
    if t < T_YO:
        dizzy_stars(img, hx, hy, t, r=int(4 * k))
    # Kagura's tear fountains
    kex, key = scr(kx - 3, ky - 17, k, c)
    tear_stream(img, kex, key, t, direction=-1)
    tear_stream(img, kex + 7, key, t + 0.2, direction=1)
    if t >= T_TSUK:
        ex, ey = scr(sx - 6, FLOOR - 24, k, c)
        tear_stream(img, ex, ey, t, direction=1)
        tear_stream(img, ex - 8, ey, t + 0.17, direction=-1)
        if t < T_TSUK + 0.55:
            fx.speed_lines(img, t, int(ex) - 30, int(ey), (255, 255, 255), count=46, inner=96, seed=13)
        fx.flash(img, 0.35 * (1 - seg(t, T_TSUK, T_TSUK + 0.12)))
        sfx_text(img, int(ex) + 30, int(ey) - 34, "！！", t, T_TSUK, 0.9, size=28, angle=-10,
                 color=(255, 90, 80))
    if t >= T_YO:
        bx, by = scr(gx - 12, gy - 20, k, c)
        speech_bubble(img, int(bx), int(by), "……哟。", t, T_YO, tail=(0, 1), typewriter=False)
    if t >= T_VEIN:
        vx, vy = scr(sx + 3, FLOOR - 31, k, c)
        A.anger_vein(img, int(vx), int(vy), t, T_VEIN, size=10)
    dx, dy = fx.shake_offset(t, T_TSUK, 0.25, 3, seed=5)
    dx2, dy2 = fx.shake_offset(t, T_VEIN, 0.15, 2, seed=15)
    fx.shift(img, dx + dx2, dy + dy2)


# ============================================================ SHOT D1 — Otae x Kondo
D1_CAM = YX + 430
KONDO_SKY = (262, 12)          # world point where Kondo becomes a star


def kondo_path(pk, kx):
    e = pk * 0.35 + ease_in_out(pk) * 0.65
    return lerp(kx, KONDO_SKY[0], e), lerp(FLOOR - 6, KONDO_SKY[1], e)


def shot_d1(img, t):
    K.street(img, D1_CAM, t, "day")
    ox, kx = 176, 232
    if t < 10.78:
        draw_char(img, "otae", ox, FLOOR, "idle", t, facing=-1, expr="dark_smile")
    else:
        draw_char(img, "otae", ox, FLOOR, "super_punch", t, p=seg(t, 10.78, 11.24) , facing=1)
    if t < T_PUNCH:
        draw_char(img, "kondo", kx, FLOOR, "stalk", t, facing=-1)
    else:
        # launch into the sky (the camera tilts up after him)
        pk = seg(t, T_PUNCH, T_STAR1)
        px_, py_ = kondo_path(pk, kx)
        if pk < 1:
            fs, fax, fay = render_sprite("kondo", "fly", t, expr="hurt")
            s = lerp(1.0, 0.3, ease_in(pk))
            if s < 0.99:
                fs = fs.resize((max(1, int(fs.width * s)), max(1, int(fs.height * s))), Image.NEAREST)
                fax, fay = fax * s, fay * s
            img.paste(fs, (int(px_ - fax), int(py_ - fay)), fs)
        # the bush he hid behind stays, still shaking
        bush = _kondo_bush()
        if bush is not None:
            jx = int(wave(t, 12, 1.5 * (1 - seg(t, T_PUNCH, T_PUNCH + 0.6))))
            paste(img, bush, kx + jx, FLOOR, anchor="bottom")
    k = lerp(1.95, 2.05, seg(t, T_D1, T_D2))
    cy = 130
    if t >= T_PUNCH:     # tilt up, keeping the flying gorilla in frame
        cy = min(130, kondo_path(seg(t, T_PUNCH, T_STAR1), kx)[1] + 30)
    c = zoom(img, k, 206, cy)
    if t >= T_PUNCH:
        hx, hy = scr(kx - 4, FLOOR - 20, k, c)
        fx.burst(img, t, T_PUNCH, int(hx), int(hy), n=16, colors=[(255, 255, 255), (255, 200, 220)],
                 speed=(60, 150), gravity=60, life=0.4, seed=41)
        sfx_text(img, int(hx) + 10, int(hy) - 34, "砰！！", t, T_PUNCH, 0.55, size=26, angle=-12)
        fx.flash(img, 0.4 * (1 - seg(t, T_PUNCH, T_PUNCH + 0.1)))
    sx, sy = scr(KONDO_SKY[0], KONDO_SKY[1], k, c)
    twinkle_star(img, int(sx), int(sy), t, T_STAR1, dur=T_D2 - T_STAR1, size=10)
    dx, dy = fx.shake_offset(t, T_PUNCH, 0.3, 4, seed=6)
    fx.shift(img, dx, dy)


def _kondo_bush():
    b = A_CACHE.get("bush")
    if b is None:
        try:
            from chars.kondo import _bush
            b = _bush(0)
        except Exception:
            b = None
        A_CACHE["bush"] = b
    return b


# ============================================================ SHOT D2 — Okita x Hijikata
def d2_bg(img, t):
    C.sky(img, "day", t, horizon=118)
    C.clouds(img, t, 0, "day", seed=3, count=5, y0=8, y1=60)
    C.far_mountains(img, 0, "day", y=112)
    C.river(img, 112, 24, t, "day")
    C.dirt_ground(img, 136, 0, "day", grass=0.8)
    C.cherry_tree(img, 128, 140, t, scale=1, tod="day")


def shot_d2(img, t):
    d2_bg(img, t)
    hx, ox = 150, 300
    gy = 176
    if t < T_BOOM:
        draw_char(img, "hijikata", hx, gy, "smoke", t, facing=1)
    p = seg(t, T_D2, T_FIRE) * 0.5 if t < T_FIRE else 0.5 + 0.5 * seg(t, T_FIRE, 12.6)
    draw_char(img, "okita", ox, gy, "bazooka", t, p=p, facing=-1)
    # shell
    if T_FIRE <= t < T_BOOM:
        k = seg(t, T_FIRE, T_BOOM)
        x0, y0 = ox - 26, gy - 24
        sx_, sy_ = lerp(x0, hx + 6, k), lerp(y0, gy - 18, k)
        d = ImageDraw.Draw(img)
        d.line([(sx_, sy_), (sx_ + 30, sy_ - 2)], fill=(230, 230, 230))
        d.rectangle([sx_ - 3, sy_ - 2, sx_ + 3, sy_ + 1], fill=INK)
        d.rectangle([sx_ - 2, sy_ - 1, sx_ + 2, sy_], fill=(90, 110, 80))
    fx.explosion(img, t, T_BOOM, hx + 2, gy - 18, size=34, seed=61)
    if t >= 12.34:     # soot-black afro emerges from the smoke
        draw_char(img, "hijikata", hx, gy, "shock" if t < 12.5 else "idle", t, p=0.9, facing=1,
                  expr="afro")
    if t >= 12.34:
        for i in range(3):   # smoke wisps from the afro
            ph = (t * 1.5 + i / 3) % 1.0
            pset(img, hx - 4 + i * 4 + int(wave(t, 2, 1.5, i)), gy - 40 - ph * 14, (150, 150, 160))
    k = lerp(1.75, 1.85, seg(t, T_D2, T_D3))
    c = zoom(img, k, 216, 146)
    fx.sakura(img, t, count=14, seed=5)
    if t >= T_BOOM:
        px, py = scr(hx, gy - 50, k, c)
        sfx_text(img, int(px) + 8, int(py) - 6, "轰！！", t, T_BOOM, 0.5, size=28, angle=8,
                 color=(255, 170, 60))
        fx.flash(img, 0.5 * (1 - seg(t, T_BOOM, T_BOOM + 0.12)), (255, 240, 200))
    if t >= 12.5:
        px, py = scr(hx, gy - 46, k, c)
        spr = A.rotated("总悟——！！", 16, (255, 255, 255), -6, "hei", 2)
        paste(img, spr, int(px) + 4 + int(wave(t, 16, 1)), int(py) - 8, anchor="center")
        px, py = scr(ox - 4, gy - 44, k, c)
        if t >= 12.62:
            draw_text(img, int(px), int(py) - int(wave(t, 2, 2)), "♪", (255, 255, 255), outline=INK)
    dx, dy = fx.shake_offset(t, T_BOOM, 0.4, 5, seed=7)
    fx.shift(img, dx, dy)


# ============================================================ SHOT D3 — 不是假发，是桂！
def sunburst(img, t, c1=(255, 176, 60), c2=(255, 214, 110), cx=268, cy=110, n=18):
    img.paste(c1, (0, 0, W, H))
    d = ImageDraw.Draw(img)
    rot = t * 0.6
    R = 460
    for i in range(n):
        a0 = rot + i * 2 * math.pi / n
        a1 = a0 + math.pi / n
        d.polygon([(cx, cy), (cx + math.cos(a0) * R, cy + math.sin(a0) * R),
                   (cx + math.cos(a1) * R, cy + math.sin(a1) * R)], fill=c2)


def shot_d3(img, t):
    sunburst(img, t)
    fx.speed_lines(img, t, 268, 120, (255, 250, 230), count=36, inner=110, seed=17, thickness=1)
    turned = t >= T_TURN
    kx, ky = 292, 198
    if not turned:
        spr, ax, ay = render_sprite("katsura", "idle", t, facing=1, scale=3, expr="normal")
        img.paste(spr, (int(kx - ax), int(ky - ay)), spr)
    else:
        p = seg(t, T_TURN, T_TURN + 0.35)
        spr, ax, ay = render_sprite("katsura", "point", t, p=p, facing=-1, scale=3,
                                    expr="shout" if step_frame(t, 8) % 2 == 0 else "angry")
        jx = int(wave(t, 18, 1)) if t >= T_KATSURA else 0
        img.paste(spr, (int(kx - ax + jx), int(ky - ay)), spr)
        if t < T_TURN + 0.12:
            fx.motion_lines(img, t, (255, 255, 255), count=10, direction=1, seed=3, y0=100, y1=200)
    # the call from off-screen
    if T_D3 <= t < T_TURN + 0.1:
        speech_bubble(img, 4, 74, "假发～", t, T_D3, tail=(-1, 1), max_w=80, typewriter=False,
                      size=16)
    # BIG text
    if t >= T_ZURA:
        k = ease_out_back(seg(t, T_ZURA, T_ZURA + 0.12))
        spr = A.rotated("不是假发", 30, (255, 255, 255), 4)
        if k < 1:
            spr = spr.resize((max(1, int(spr.width * k)), max(1, int(spr.height * k))), Image.NEAREST)
        paste(img, spr, 168, 34, anchor="center")
    if t >= T_KATSURA:
        k = seg(t, T_KATSURA, T_KATSURA + 0.08)
        s = lerp(2.2, 1.0, ease_in(k))
        spr = A.rotated("是桂！", 48, (230, 40, 50), 6, "brush", 3)
        if s != 1:
            spr = spr.resize((int(spr.width * s), int(spr.height * s)), Image.NEAREST)
        paste(img, spr, 176 + int(wave(t, 20, 1)), 84, anchor="center")
        fx.flash(img, 0.6 * (1 - seg(t, T_KATSURA, T_KATSURA + 0.12)))
    # Elizabeth pops up bottom-left (in front of the text) with a chorus sign (facing right so the text reads)
    if t >= T_ELI:
        # she hops up from below the frame edge and lands above the dialogue box
        k = seg(t, T_ELI, T_ELI + 0.22)
        es, eax, eay = render_sprite("elizabeth", "sign", t, p=0.3 + 0.7 * k, facing=1, scale=2,
                                     sign="没错")
        ey = 250 - 82 * ease_out_back(k)
        img.paste(es, (int(34 - eax), int(ey - eay)), es)

    dx, dy = fx.shake_offset(t, T_KATSURA, 0.35, 5, seed=9)
    fx.shift(img, dx, dy, fill=(255, 176, 60))


# ============================================================ SHOT D4 — Sadaharu chomp
D4_ZOOM = (2.15, 214, 166)
SADA_X = 246
GIN_D4X = 221
T_SNAP = 15.08                     # jaws slam shut on the perm
T_CHEW = 15.12                     # chew loop origin (bites land at T_CHEW + 0.25 + 0.5n)


def d4_world(img, t):
    K.yorozuya_front(img, t, "day")
    fy = FRONT_FLOOR
    draw_char(img, "kagura", 156, fy, "cheer", t, facing=1)
    sh = "shock" if t >= T_SNAP else "idle"
    draw_char(img, "shinpachi", 182, fy, sh, t, p=seg(t, T_SNAP, T_SNAP + 0.3), facing=1,
              expr="shock" if t >= T_SNAP else None)
    # Sadaharu lunges in from the right
    sx = lerp(272, SADA_X, ease_in(seg(t, 14.95, T_SNAP)))
    if t < T_SNAP:
        # Gintoki strolls up to greet his dog - "哟，定春～"
        gx = lerp(GIN_D4X - 10, GIN_D4X, ease_out(seg(t, T_D4, 15.0)))
        draw_char(img, "gintoki", gx, fy, "wave", t, facing=1, expr="happy")
        draw_char(img, "sadaharu", sx, fy, "bite", t, p=0.34 * seg(t, T_D4, T_SNAP), facing=-1)
    else:
        # head swallowed: arms flailing, legs kicking
        ff = step_frame(t, 12)
        arm_f = 150 + 45 * math.sin(t * 38)
        arm_b = 200 + 45 * math.sin(t * 38 + 2)
        # yanked into the maw and lifted a little off the ground
        lift = 2 + 6 * ease_out(seg(t, T_SNAP, T_SNAP + 0.15))
        overlay_rect(img, GIN_D4X - 4, fy - 1, 14, 2, (0, 0, 0), 0.25)
        draw_char(img, "gintoki", GIN_D4X + 3, fy - lift - (1 if ff % 2 else 0), "run_away", t, facing=1,
                  arm_f=arm_f, arm_b=arm_b, legs="jump" if ff % 4 < 2 else "spread", shadow=False)
        if t < T_CHEW:
            draw_char(img, "sadaharu", sx, fy, "bite", t, p=0.4, facing=-1)
        else:
            draw_char(img, "sadaharu", sx, fy, "bite", t - T_CHEW, facing=-1)
    return sx


def shot_d4(img, t):
    sx = d4_world(img, t)
    k, cx, cy = D4_ZOOM
    k += 0.25 * (1 - ease_out(seg(t, T_SNAP, T_SNAP + 0.25))) if t >= T_SNAP else 0
    c = zoom(img, k, cx, cy)
    mx, my = sx - 22, FRONT_FLOOR - 27                     # maw (facing left)
    px, py = scr(mx, my, k, c)
    if t >= T_SNAP:
        fx.burst(img, t, T_SNAP, int(px), int(py), n=12, colors=[(200, 230, 255), (255, 255, 255)],
                 speed=(50, 120), gravity=240, life=0.4, seed=81)
        fx.flash(img, 0.35 * (1 - seg(t, T_SNAP, T_SNAP + 0.1)))
    sfx_text(img, int(px) - 30, int(py) - 44, "嚼！", t, T_SNAP, 0.5, size=22, angle=-10)
    sfx_text(img, int(px) + 28, int(py) - 52, "嚼嚼！", t, 15.40, 0.55, size=22, angle=8)
    # panic sweat off the flailing body, and Shinpachi's cold sweat
    bx, by = scr(GIN_D4X, FRONT_FLOOR - 16, k, c)
    if t >= T_SNAP:
        sweat(img, int(bx) - 16, int(by) - 6, t)
        sweat(img, int(bx) + 14, int(by) - 10, t + 0.4)
    wx, wy = scr(182, FRONT_FLOOR - 36, k, c)
    sweat(img, int(wx) + 12, int(wy), t)
    dx, dy = fx.shake_offset(t, T_SNAP, 0.25, 4, seed=19)
    fx.shift(img, dx, dy)


# ============================================================ SHOT E — 完
def frozen(t_freeze=15.90):
    f = A_CACHE.get("freeze")
    if f is None:
        f = Image.new("RGB", (W, H))
        shot_d4(f, t_freeze)
        fx.grayscale(f, 0.85)
        fx.grade(f, (0.92, 0.9, 0.86), (10, 8, 4))
        A_CACHE["freeze"] = f
    return f


def shot_e(img, t):
    if t < T_BOOT:
        img.paste(frozen())
        if t < T_STAMP - 0.1:
            fx.flash(img, 0.5 * (1 - seg(t, T_E, T_E + 0.1)))
        # crow flies across during the awkward silence
        if 16.25 <= t < 17.1:
            k = seg(t, 16.25, 17.1)
            cs = scale_nearest(A.crow_sprite(step_frame(t, 8, 2)), 2)
            paste(img, cs, int(lerp(W + 10, -40, k)), int(30 + wave(t, 1.3, 4)))
        stamp = A.stamp_sprite(1 if t >= 16.85 else 0)
        if t >= T_STAMP - 0.1:
            k = seg(t, T_STAMP - 0.1, T_STAMP)
            s = lerp(2.6, 1.0, ease_in(k))
            spr = stamp
            if s != 1:
                spr = spr.resize((int(stamp.width * s), int(stamp.height * s)), Image.NEAREST)
            spr = rotate_nearest(spr, -9)
            jx = jy = 0
            if 16.85 <= t < T_BOOT:
                jx, jy = int(wave(t, 22, 2)), -abs(int(wave(t, 11, 3)))
            paste(img, spr, W // 2 + jx, H // 2 - 6 + jy, anchor="center", alpha=0.6 + 0.4 * k)
            fx.burst(img, t, T_STAMP, W // 2, H // 2, n=22, colors=[(208, 36, 48), (160, 20, 40)],
                     speed=(90, 200), gravity=40, life=0.4, size=(1, 3), seed=71)
        for tt in (16.85, 17.0):
            sfx_text(img, W // 2 + (20 if tt > 16.9 else -24), H - 34, "咚", t, tt, 0.25, size=18,
                     color=(255, 255, 255), angle=0)
        dx, dy = fx.shake_offset(t, T_STAMP, 0.35, 6, seed=11)
        fx.shift(img, dx, dy)
        return
    # --- live again: Gintoki boots the stamp away
    K.yorozuya_front(img, t, "day")
    fy = FRONT_FLOOR
    draw_char(img, "kagura", 140, fy, "cheer", t, facing=1)
    draw_char(img, "shinpachi", 160, fy, "cheer", t + 0.2, facing=1, expr="happy")
    draw_char(img, "sadaharu", 240, fy, "bark" if t > 17.5 else "shock", t, p=0.6, facing=-1)
    gx = 190
    if t < 17.5:
        draw_char(img, "gintoki", gx, fy, "kick", t, p=seg(t, T_BOOT - 0.05, T_BOOT + 0.15), rot=22,
                  expr="shout")
    else:
        # lands, then jabs a finger at the sky where the stamp twinkled away
        expr = "shout" if step_frame(t, 8) % 2 == 0 else "angry"
        hop = int(3 * (1 - ease_out(seg(t, 17.5, 17.62))))
        draw_char(img, "gintoki", gx, fy - hop, "point", t, p=1.0, expr=expr,
                  arm_f=lerp(80, 122, ease_out_back(seg(t, 17.5, 17.7))), arm_b=-25)
    # drool dripping from his perm
    for i in range(3):
        ph = (t * 1.4 + i * 0.33) % 1.0
        pset(img, gx - 5 + i * 5, fy - 34 + ph * 10, (180, 230, 255))
    k = lerp(2.55, 2.8, ease_in_out(seg(t, 17.5, T_F)))
    c = zoom(img, k, 192, 190)
    if t < T_BOOT + 0.45:
        fx.speed_lines(img, t, 200, 60, (255, 236, 120), count=44, inner=80, seed=23)
    elif 17.5 <= t < 18.1:
        hx, hy = scr(gx, fy - 26, k, c)
        fx.speed_lines(img, t, int(hx), int(hy), (255, 255, 255), count=40, inner=70, seed=29)
    # the stamp flies off, spinning, and becomes a star
    ks = seg(t, T_BOOT, T_STAR2)
    if ks < 1:
        stamp = A.stamp_sprite(1)
        s = lerp(1.0, 0.12, ease_in(ks))
        spr = stamp.resize((max(1, int(stamp.width * s)), max(1, int(stamp.height * s))), Image.NEAREST)
        spr = rotate_nearest(spr, -9 - 900 * ks)
        paste(img, spr, int(lerp(W // 2, 336, ease_out(ks))), int(lerp(H // 2 - 6, 24, ease_out(ks))),
              anchor="center")
    twinkle_star(img, 336, 24, t, T_STAR2, dur=0.9, size=9)
    sfx_text(img, 236, 70, "嘭！！", t, T_BOOT, 0.5, size=28, angle=-14)
    fx.flash(img, 0.55 * (1 - seg(t, T_BOOT, T_BOOT + 0.1)))
    dx, dy = fx.shake_offset(t, T_BOOT, 0.35, 5, seed=13)
    fx.shift(img, dx, dy)


# ============================================================ SHOT F — parade credits
def _gin_jump_prop():
    try:
        from chars.gintoki import _jump_prop
        return _jump_prop
    except Exception:
        return None


PARADE_FRONT = [("shinpachi", 0), ("SADA", 0), ("otae", 0), ("kondo", 0), ("hijikata", 0),
                ("okita", 0), ("katsura", 0), ("elizabeth", 0), ("hasegawa", 0), ("otose", 0),
                ("catherine", 0), ("tama", 0), ("GIN", 0)]
PARADE_BACK = [("yamazaki", 0), ("otsu", 0), ("sakamoto", 0), ("tsukuyo", 0), ("seita", 0),
               ("kamui", 0), ("umibozu", 0), ("shigeshige", 0), ("townswoman", 1), ("townsman", 2),
               ("amanto_pig", 0)]


def _layout(row, x0, gap):
    out, x = [], x0
    for cid, v in row:
        w = 52 if cid == "SADA" else gap
        out.append((cid, v, x + (w - gap) / 2))
        x += w
    return out


FRONT_POS = _layout(PARADE_FRONT, 0, 29)
BACK_POS = _layout(PARADE_BACK, 14, 30)
WALK = 30.0
F_CAM0, F_PAN = YX - W // 2 - 40, 95.0


def shot_f(img, t):
    lt = t - T_F
    cam = F_CAM0 + F_PAN * lt
    K.street(img, int(cam), t, "dusk")
    base = 130 - (F_PAN + WALK) * lt           # screen x of the parade head
    jp = _gin_jump_prop()
    for rows, gy, sd in ((BACK_POS, 158, 0.0), (FRONT_POS, 184, 0.37)):
        for i, (cid, v, off) in enumerate(rows):
            x = base + off
            if x < -40 or x > W + 40:
                continue
            tt = t + i * 0.13 + sd
            if cid == "SADA":
                draw_char(img, "sadaharu", x, gy, "walk", tt, facing=-1)
                draw_char(img, "kagura", x + 2, gy - 30 - (step_frame(tt, 6, 2)), "cheer", tt,
                          facing=-1, shadow=False)
            elif cid == "GIN":
                if jp is not None:
                    draw_char(img, "gintoki", x, gy, "walk", tt, facing=-1, props=[jp], arm_f=130,
                              arm_b=100, expr=blink_expr(t, "normal"))
                else:
                    draw_char(img, "gintoki", x, gy, "walk", tt, facing=-1)
            elif cid == "kondo":
                draw_char(img, "kondo", x, gy, "walk", tt, facing=-1, expr="love")
            elif cid in ("townsman", "townswoman"):
                draw_char(img, cid, x, gy, "walk", tt, facing=-1, variant=v)
            else:
                draw_char(img, cid, x, gy, "walk", tt, facing=-1)
    zoom(img, 1.22, 192, 146)
    fx.sakura(img, t, count=20, seed=8, colors=((255, 200, 170), (255, 225, 200), (250, 160, 150)))
    # credits band
    a = seg(t, T_F + 0.1, T_F + 0.4)
    if a > 0:
        overlay_rect(img, 0, 6, W, 46, (14, 8, 24), 0.55 * a)
        rect(img, 0, 6, W, 1, (255, 200, 120))
        rect(img, 0, 51, W, 1, (255, 200, 120))
        s1 = "原作：空知英秋《银魂》"
        dy = int((1 - ease_out(a)) * 6)
        draw_text(img, W // 2 - text_width(s1, 16) // 2, 11 - dy, s1, (255, 240, 210), size=16,
                  outline=INK)
    a2 = seg(t, T_F + 0.45, T_F + 0.75)
    if a2 > 0:
        s2 = "本片为同人像素致敬作品"
        dy = int((1 - ease_out(a2)) * 5)
        draw_text(img, W // 2 - text_width(s2) // 2, 33 + dy, s2, (255, 214, 150), outline=INK)
    fx.sparkle(img, 60, 20, t, T_F + 0.2, size=5, color=(255, 230, 160))
    fx.sparkle(img, 322, 38, t, T_F + 0.6, size=4, color=(255, 230, 160))


# ============================================================ SHOT G — 感谢观看
def shot_g(img, t):
    Y.office(img, t, "dusk")
    # Shinpachi keeps the boss chair warm (two years of running the shop)
    draw_char(img, "shinpachi", Y.DESK_X + 6, Y.DESK_SEAT_Y, "sit", t, facing=-1,
              expr=blink_expr(t, "normal", 1.1))
    Y.desk_fg(img, t, "dusk")
    gexpr = blink_expr(t, "normal", 0.5, 2.7) if t < 23.05 else "smug"
    draw_char(img, "gintoki", Y.SOFA_L_X + 2, Y.SOFA_SEAT_Y, "read", t, facing=1, expr=gexpr)
    draw_char(img, "kagura", Y.SOFA_R_X, Y.SOFA_LIE_Y, "sleep", t, facing=-1)
    Y.office_fg(img, t, "dusk")
    draw_char(img, "sadaharu", 276, 196, "sleep", t, facing=-1)
    k0 = lerp(1.3, 1.4, ease_in_out(seg(t, T_G, 23.0)))
    pz = ease_in_out(seg(t, 23.0, 23.85))
    k = lerp(k0, 2.2, pz)
    c = zoom(img, k, lerp(176, Y.SOFA_L_X + 6, pz), lerp(150, Y.SOFA_SEAT_Y - 14, pz))
    gx, gy = scr(Y.SOFA_L_X + 4, Y.SOFA_SEAT_Y - 22, k, c)
    if t >= 23.05:
        ex, ey = scr(Y.SOFA_L_X + 8, Y.SOFA_SEAT_Y - 20, k, c)
        fx.sparkle(img, int(ex), int(ey), t, 23.08, size=5)
    ip = ease_in(seg(t, 23.3, 23.92))
    if ip > 0:
        fx.iris(img, min(0.93, ip), int(gx), int(gy))
        if ip > 0.92:
            fx.iris(img, 1.0, int(gx), int(gy))
    # title
    a = seg(t, T_G + 0.15, T_G + 0.5)
    if a > 0:
        overlay_rect(img, 0, 12, W, 70, (20, 10, 26), 0.5 * a)
        rect(img, 0, 12, W, 1, (255, 200, 120))
        rect(img, 0, 81, W, 1, (255, 200, 120))
        s = ease_out_back(a)
        spr = A.brush_text("感谢观看", 36, (255, 232, 170), INK, 2)
        if s < 0.999:
            spr = spr.resize((max(1, int(spr.width * s)), max(1, int(spr.height * s))), Image.NEAREST)
        paste(img, spr, W // 2, 34, anchor="center")
    a2 = seg(t, T_G + 0.5, T_G + 0.8)
    if a2 > 0:
        s3 = "THANK YOU FOR WATCHING"
        draw_text(img, W // 2 - text_width(s3) // 2, 56 - int((1 - a2) * 4), s3, (230, 220, 255),
                  outline=INK)
        s4 = "银魂 · 像素剧场"
        if t >= T_G + 0.9:
            draw_text(img, W // 2 - text_width(s4) // 2, 70, s4, (255, 190, 150), outline=INK)
    fx.sparkle(img, 96, 26, t, T_G + 0.4, size=5, color=(255, 240, 190))
    fx.sparkle(img, 290, 44, t, T_G + 0.7, size=4, color=(255, 240, 190))
    fx.sparkle(img, 262, 18, t, T_G + 1.1, size=5, color=(255, 240, 190))


# ============================================================ scene
SHOTS = [
    (0.0, shot_a), (T_B1, shot_b1), (T_B2, shot_b2), (T_B3, shot_b3a), (T_B3B, shot_b3b),
    (T_C1, shot_c1), (T_C2, shot_c2), (T_D1, shot_d1), (T_D2, shot_d2), (T_D3, shot_d3),
    (T_D4, shot_d4), (T_E, shot_e), (T_F, shot_f), (T_G, shot_g),
]


class Epilogue(Scene):
    id = "s14"
    title = "尾声"
    duration = T_END
    music = [(0.0, None), (T_HOOD1, "ending")]
    music_vol = 0.7
    fade_in = 0.3
    fade_out = 0.35
    subs = [
        (0.25, 2.58, None, "歌舞伎町重建，新八和神乐守着万事屋。"),
        (5.50, 7.20, "gintoki", "我回来了。"),
        (8.64, 10.60, "shinpachi", "你到底跑哪去了！！"),
        (T_TURN, T_D4, "katsura", "不是假发，是桂！"),
        (17.22, 19.00, "gintoki", "才不会完呢！"),
    ]

    def render(self, img, t):
        fn = SHOTS[0][1]
        for t0, f in SHOTS:
            if t >= t0:
                fn = f
        fn(img, t)
        for tc in (T_D1, T_D2, T_D4):      # white pop on each montage cut
            if tc <= t < tc + 0.1:
                fx.flash(img, 0.45 * (1 - seg(t, tc, tc + 0.1)))
        corner_caption(img, t)

    def cues(self):
        c = [
            Cue(0.0, "rain", vol=0.8, dur=6.9),
            Cue(T_LIGHT[0] + 0.12, "thunder", vol=0.7),
            Cue(T_LIGHT[1] + 0.1, "thunder", vol=0.8),
            Cue(T_B1, "footsteps", vol=0.35, dur=1.9),
            Cue(B1_SPLASH[0][0], "land", vol=0.4, pitch=1.5),
            Cue(B1_SPLASH[1][0], "land", vol=0.35, pitch=1.6),
            Cue(B1_GLINT, "shing", vol=0.5),
            Cue(4.35, "shock", vol=0.6),
            Cue(T_HOOD0, "whoosh", vol=0.5, pitch=1.2),
            Cue(T_HOOD1, "shine", vol=0.8),
            Cue(T_HOOD1 + 0.05, "sparkle", vol=0.5),
            Cue(6.95, "charge", vol=0.4, pitch=1.4),
            Cue(T_LEAP, "jump", vol=0.8),
            Cue(T_LEAP + 0.25, "whoosh", vol=0.6),
            Cue(7.35, "run", vol=0.35, dur=1.3),
            Cue(7.62, "sweat", vol=0.5),
            Cue(T_KICK, "punch_big", vol=1.0),
            Cue(T_KICK, "impact", vol=0.7),
            Cue(T_KICK + 0.04, "fly_away", vol=0.7),
            Cue(8.05, "land", vol=0.6),
            Cue(T_CRASH, "crash", vol=0.9),
            Cue(T_CRASH + 0.04, "thud", vol=0.6),
            Cue(T_C2 + 0.05, "dizzy", vol=0.4),
            Cue(T_TSUK, "shock", vol=0.7),
            Cue(T_YO, "pop", vol=0.4, pitch=0.8),
            Cue(T_VEIN, "vein", vol=0.7),
            Cue(T_D1, "slide_up", vol=0.4),
            Cue(10.78, "whoosh", vol=0.6),
            Cue(T_PUNCH, "punch_big", vol=1.0),
            Cue(T_PUNCH + 0.03, "fly_away", vol=0.7),
            Cue(T_STAR1, "twinkle", vol=0.8),
            Cue(T_FIRE, "bazooka", vol=0.9),
            Cue(T_BOOM, "explosion", vol=1.0),
            Cue(12.45, "cough", vol=0.6),
            Cue(T_TURN - 0.03, "record_scratch", vol=0.6),
            Cue(T_TURN + 0.02, "whoosh", vol=0.5),
            Cue(T_ZURA, "pop", vol=0.6),
            Cue(T_KATSURA, "impact", vol=0.9),
            Cue(T_ELI + 0.12, "pop", vol=0.6, pitch=1.3),
            Cue(T_SNAP, "chomp", vol=1.0),
            Cue(T_SNAP, "impact", vol=0.5),
            Cue(T_CHEW + 0.25, "chomp", vol=0.8),
            Cue(T_CHEW + 0.75, "chomp", vol=0.8),
            Cue(T_SNAP + 0.1, "shock", vol=0.5),
            Cue(T_E, "record_scratch", vol=0.8),
            Cue(T_STAMP, "impact", vol=1.0),
            Cue(T_STAMP, "gong", vol=0.8),
            Cue(16.40, "crow", vol=0.8),
            Cue(16.85, "thud", vol=0.6),
            Cue(17.00, "thud", vol=0.7),
            Cue(T_BOOT, "kick", vol=1.0),
            Cue(T_BOOT, "crash", vol=0.6),
            Cue(T_BOOT + 0.03, "fly_away", vol=0.7),
            Cue(T_STAR2, "twinkle", vol=0.8),
            Cue(17.55, "bark", vol=0.5),
            Cue(T_F + 0.1, "sparkle", vol=0.5),
            Cue(T_F, "crowd", vol=0.2, dur=2.9),
            Cue(T_F + 0.05, "cheer", vol=0.35),
            Cue(T_G + 0.15, "shine", vol=0.6),
            Cue(23.25, "slide_down", vol=0.4),
        ]
        return c


SCENE = Epilogue()
