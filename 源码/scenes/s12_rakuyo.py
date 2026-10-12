"""s12 洛阳决战·离别 (Rakuyo decisive battle / farewell) — 19.0 s.

SHOT LIST (scene-local seconds)
  A   0.00- 1.75  chapter card 「洛阳决战篇」 over the rain planet; thunder flash on the slam.
  B1  1.75- 2.55  Rakuyo ruins in the rain (crashed battleship, broken pagodas), slow pan.
                  Kagura (L) and Kamui (R) face off; lightning 1.92; crouch 2.24; DASH 2.36.
  B2  2.55- 3.42  close: umbrella tips CLASH 2.58 -> impact frame, shockwave rings, rain blasted
                  outward, 「锵!!」. Exchanges: 2.88 punch/guard, 3.06 kick/guard 「砰!」,
                  3.24 overhead bind (umbrellas cross in an X, grinding sparks).
  B3  3.42- 3.92  split-screen face-off: Kagura's glare | Kamui's smile -> eyes OPEN 3.62.
  B4  3.92- 4.42  both leap; a shadow grows between them, fall whistle; Umibozu plummets in.
  C   4.42- 6.10  LANDING: impact frame, crater, siblings blown apart. 「够了！」 (4.60),
                  push-in, name_card 星海坊主 4.85 (latin tag, 2.2 s).
  C2  6.10- 7.50  GAG close two-shot: raindrops 'ting' off the bald dome (叮! 叮! 叮叮叮,
                  accelerating), Kagura deadpan + sweat drop + 「……」, Umibozu's anger vein 7.16.
  D1  7.50- 9.90  Kagura close-up in the rain (letterbox), Kamui as a dark foreground
                  silhouette; she points: 「我一定会把哥哥带回家阿鲁！」, then a slow push-in.
  D2  9.90-11.70  (music -> sad) Kamui's gentle smile... turns, opens his umbrella (10.45),
                  walks off into the mist; camera pulls back: Kagura steps after him and
                  reaches out, Umibozu watching behind her; far lightning 11.05.
  E1 11.70-13.50  white-in: Edo harbour at dawn, the Shinsengumi ship (诚 sail) lifts off. Narration.
  E2 13.50-16.40  on deck: Hijikata lights a cigarette (13.68), exhales a smoke stream;
                  pull back to the stern: Kondo bawling (wind-blown tear streams), Okita napping
                  with his eye-mask. Hijikata 「……我们会回来的。」
  E3 16.40-19.00  the dock: Otae under a cherry tree watches the ship rise into the sunrise;
                  「阿妙小姐～～！」 bubble from the ship; she waves; the ship twinkles like a star.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import Scene, Cue, W, H, seg, lerp, clamp, ease_in, ease_out, ease_in_out, \
    ease_out_back, wave, step_frame, rng, arc
from engine.gfx import INK, rect, overlay_rect, pset, shade
from engine import fx
from engine.text import sfx_text, name_card, chapter_card, speech_bubble, draw_text
from chars import draw_char, render_sprite, get_def
from bg import common as C, edo as E
from scenes import _s12_art as A

# ------------------------------------------------------------------ timeline
B0, RUN, B2, CLASH = 1.75, 2.36, 2.55, 2.58
XCH = (2.88, 3.06, 3.24)
B3, EYES, B4, WHISTLE, DROP, LAND = 3.42, 3.62, 3.92, 3.98, 4.30, 4.42
SHOUT, PUSH0, PUSH1, CARD = 4.60, 4.90, 5.40, 4.85
GAG = 6.10                                   # hard cut: close two-shot, the bald-head gag
TINGS = (6.30, 6.58, 6.86, 6.95, 7.04)      # raindrops 'ting' off the dome (accelerating)
DOTS, VEIN = 6.62, 7.16                      # Kagura's deadpan '……' bubble / dad's anger vein
D1, POINT = 7.50, 7.75
D2, TURN, WALK = 9.90, 10.45, 10.65
FAR_BOLT, STEP = 11.05, 10.95                # far lightning / Kagura steps after him
E1, E2 = 11.70, 13.50
LIGHT, LIT, PULL = 13.68, 14.05, 14.25
E3, BUBBLE, TWINKLE = 16.40, 16.65, 17.95
END = 19.00

FLOOR = 160
KAG_X, KAM_X, UMI_X = 120, 262, 192        # positions after the landing


# ------------------------------------------------------------------ helpers
def actor(img, cid, x, y, pose="idle", t=0.0, p=None, expr=None, facing=1, alpha=1.0,
          refl=True, shadow=True, flash=0.0, rot=0, ground=FLOOR, **kw):
    """draw_char + a wet-ground reflection (flipped, tinted, fading)."""
    spr, ax, ay = render_sprite(cid, pose, t, p, expr, facing, flash, (255, 255, 255), alpha, 1, rot, **kw)
    x, y = int(round(x)), int(round(y))
    if refl and y >= ground - 2:
        a = np.asarray(spr).copy()
        a = a[::-1]
        h = a.shape[0]
        top = y - (h - 1 - ay)
        rows = np.arange(h, dtype=np.float32) - (h - 1 - ay)
        k = np.clip(1 - rows / 20.0, 0, 1) * 0.42
        a[..., :3] = (a[..., :3] * 0.45 + np.array([38, 50, 64], np.float32) * 0.55).astype(np.uint8)
        a[..., 3] = (a[..., 3] * k[:, None]).astype(np.uint8)
        a[: max(0, h - 1 - ay + 1)] = 0
        ref = Image.fromarray(a, "RGBA")
        img.paste(ref, (x - ax, top + 1), ref)
    if shadow and alpha > 0.3 and y >= ground - 2:
        overlay_rect(img, x - 6, y - 1, 12, 2, (0, 0, 0), 0.3)
    img.paste(spr, (x - ax, y - ay), spr)
    return spr, x - ax, y - ay


def find_px(spr, colors):
    """First (x, y) of any of the colours in an RGBA sprite, or None."""
    a = np.asarray(spr)
    for c in colors:
        m = (a[..., 0] == c[0]) & (a[..., 1] == c[1]) & (a[..., 2] == c[2]) & (a[..., 3] > 0)
        ys, xs = np.nonzero(m)
        if len(xs):
            return int(xs.mean()), int(ys.min())
    return None


def letterbox(img, bar=13):
    img.paste((0, 0, 0), (0, 0, W, bar))
    img.paste((0, 0, 0), (0, H - bar, W, H))


def shock_ring(img, t, t0, x, y, r0=6, speed=260, life=0.35, flat=0.32, color=(236, 244, 255), width=2):
    dt = t - t0
    if not (0 <= dt < life):
        return
    r = r0 + speed * dt
    d = ImageDraw.Draw(img)
    k = dt / life
    col = color if k < 0.5 else (150, 170, 196)
    d.ellipse([x - r, y - r * flat, x + r, y + r * flat], outline=col, width=width if k < 0.6 else 1)


def blast_rain(img, t, t0, x, y, life=0.35, n=44, seed=0):
    """Raindrops blown outward by a shockwave (short radial streaks)."""
    dt = t - t0
    if not (0 <= dt < life):
        return
    d = ImageDraw.Draw(img)
    for i in range(n):
        r = rng("blast", seed, i)
        a = r.uniform(0, 2 * math.pi)
        dist = r.uniform(8, 30) + dt * r.uniform(300, 520)
        L = r.uniform(4, 9)
        px, py = x + math.cos(a) * dist, y + math.sin(a) * dist * 0.7
        qx, qy = x + math.cos(a) * (dist + L), y + math.sin(a) * (dist + L) * 0.7
        d.line([(px, py), (qx, qy)], fill=(200, 214, 236) if i % 3 else (255, 255, 255))


def sparks(img, t, t0, x, y, seed=0, n=14, life=0.3, big=False):
    fx.burst(img, t, t0, x, y, n=n, colors=[(255, 255, 255), (255, 236, 150), (255, 190, 90)],
             speed=(60, 170 if big else 120), gravity=120, life=life, size=(1, 2), seed=seed)
    dt = t - t0
    if 0 <= dt < 0.08:
        fx.comic_burst(img, x, y, 9 if big else 6, 3, spikes=8, color=(255, 250, 220), outline=(255, 200, 90),
                       rot=seed)


def water_crown(img, t, t0, x, y, seed=0, n=40, speed=(80, 210), life=0.8):
    fx.burst(img, t, t0, x, y, n=n, colors=[(190, 210, 232), (236, 244, 255), (130, 152, 180)],
             speed=speed, gravity=420, life=life, size=(1, 2), seed=seed, spread=(195, 345))


def speed_bg(img, t, cx, cy, seed=0, color=(98, 112, 126), count=40, inner=26):
    fx.speed_lines(img, t, cx, cy, color=color, count=count, inner=inner, seed=seed, thickness=1.5)


# ================================================================== A: chapter card
def shot_a(img, t):
    A.rakuyo(img, t, -30, dark=0.4)
    A.rain_layer(img, t, 1.0)
    chapter_card(img, t, 0.0, B0, "洛阳决战篇", "雨之星·夜兔的血脉")
    if t >= 0.1:
        fx.rain(img, t, count=60, seed=3, color=(150, 160, 190), speed=460, slant=0.3, length=8)
    fl = A.lightning_amt(t, 0.36)
    if fl:
        fx.flash(img, fl * 0.18, (220, 228, 255))


# ================================================================== B1: face-off & dash
def shot_b1(img, t):
    u = ease_in_out(seg(t, B0, B2))
    cam = lerp(-26, -6, u)
    fl = A.lightning_amt(t, 1.92)
    A.rakuyo(img, t, cam, flash=fl, bolt_x=236, bolt_seed=1)
    A.ground_splashes(img, t)
    # positions (world = screen x + cam handled only by bg; chars stay in world coords)
    if t < RUN:
        kx, mx = 128, 256
        crouch = seg(t, 2.22, RUN)
        if crouch > 0:
            actor(img, "kagura", kx, FLOOR, "land", t, p=0.1, expr="angry", facing=1)
            actor(img, "kamui", mx, FLOOR, "land", t, p=0.1, expr="smile", facing=-1)
        else:
            actor(img, "kagura", kx, FLOOR, "ready", t, expr="angry", facing=1)
            actor(img, "kamui", mx, FLOOR, "ready", t, facing=-1)
    else:
        k = ease_in(seg(t, RUN, B2 + 0.02))
        kx, mx = lerp(128, 160, k), lerp(256, 224, k)
        fx.motion_lines(img, t, color=(120, 136, 150), count=14, direction=1, seed=4, y0=118, y1=162)
        actor(img, "kagura", kx, FLOOR, "run", t, facing=1)
        actor(img, "kamui", mx, FLOOR, "run", t, facing=-1)
        fx.smoke_puff(img, t, RUN, 124, FLOOR - 1, size=7, seed=1, color=(150, 166, 184), life=0.4)
        fx.smoke_puff(img, t, RUN, 260, FLOOR - 1, size=7, seed=2, color=(150, 166, 184), life=0.4)
    if fl > 0.8:      # lightning: silhouettes against the bright sky
        fx.flash(img, 0.25, (210, 220, 255))
    A.zoom_at(img, 1.5, lerp(186, 194, u), 128, W / 2, H / 2 + 6)
    A.rain_layer(img, t, 1.1)


# ================================================================== B2: clash
def _clash_positions(t):
    """(kagura x, pose, p, expr), (kamui x, pose, p, expr), contact point."""
    if t < XCH[0] - 0.06:
        j = int(wave(t, 14, 1.2)) if t > CLASH else 0
        return (166 + j, "thrust", 1.0, "shout"), (219 + j, "thrust", 1.0, "open_eyes"), (192, 139)
    if t < XCH[1] - 0.05:
        k = seg(t, XCH[0] - 0.06, XCH[0])
        return ((170, "guard", 0.5, "angry"), (lerp(219, 197, k), "punch", seg(t, XCH[0] - 0.06, XCH[0] + 0.1), None),
                (183, 138))
    if t < XCH[2] - 0.06:
        k = seg(t, XCH[1] - 0.05, XCH[1])
        return ((lerp(170, 176, k), "kick", seg(t, XCH[1] - 0.05, XCH[1] + 0.1), None),
                (lerp(197, 204, k), "guard", 0.5, "smile"), (193, 150))
    # overhead bind: both swing down, the umbrellas CROSS in an X above the midpoint and grind
    k = seg(t, XCH[2] - 0.1, XCH[2])
    j = int(wave(t, 16, 1.2)) if t > XCH[2] else 0
    return ((lerp(176, 172, k) + j, "attack", lerp(0.28, 0.46, k), "shout"),
            (lerp(204, 212, k) + j, "attack", lerp(0.28, 0.46, k), None), (192, 137))


def shot_b2(img, t):
    fl = 0.0
    A.rakuyo(img, t, -6)
    A.ground_splashes(img, t, seed=2)
    if t >= CLASH:
        speed_bg(img, t, 192, 136, seed=int(t * 4), color=(92, 106, 120))
    (kx, kp, kpp, ke), (mx, mp, mpp, me), (cx, cy) = _clash_positions(t)
    actor(img, "kagura", kx, FLOOR, kp, t, p=kpp, expr=ke, facing=1)
    actor(img, "kamui", mx, FLOOR, mp, t, p=mpp, expr=me, facing=-1)
    # impact fx
    shock_ring(img, t, CLASH, 192, 140, speed=300, flat=0.9, life=0.3)
    shock_ring(img, t, CLASH + 0.07, 192, 140, speed=260, flat=0.9, life=0.3, width=1)
    shock_ring(img, t, CLASH, 192, FLOOR + 1, speed=320, flat=0.18, life=0.45)
    water_crown(img, t, CLASH, 192, FLOOR, seed=3, n=36)
    sparks(img, t, CLASH, 192, 139, seed=1, n=18, big=True)
    if CLASH <= t < XCH[0] - 0.06:
        sparks(img, t, CLASH + 0.12 + int((t - CLASH) * 10) / 10, 192, 139, seed=int(t * 10), n=6, life=0.2)
    for i, tx in enumerate(XCH):
        pts = [(184, 137), (194, 149), (192, 137)][i]
        sparks(img, t, tx, pts[0], pts[1], seed=10 + i, n=12, big=i == 2)
    if 0 <= t - XCH[2] < 0.3:
        shock_ring(img, t, XCH[2], 192, 137, speed=220, flat=0.8, life=0.25, width=1)
        shock_ring(img, t, XCH[2], 192, FLOOR + 1, speed=260, flat=0.18, life=0.3, width=1)
    if t >= XCH[2] + 0.05:     # grinding bind: a steady trickle of sparks at the crossing
        tk = XCH[2] + 0.05 + int((t - XCH[2] - 0.05) * 12) / 12
        sparks(img, t, tk, 192, 137, seed=int(t * 12), n=5, life=0.16)
    # camera
    zk = 2.1 + 0.25 * ease_out(seg(t, CLASH, CLASH + 0.25)) - 0.2 * seg(t, CLASH + 0.25, B3)
    sx, sy = fx.shake_offset(t, CLASH, 0.35, 3, seed=1)
    for i, tx in enumerate(XCH):
        ox, oy = fx.shake_offset(t, tx, 0.14, 2, seed=5 + i)
        sx, sy = sx + ox, sy + oy
    to = A.zoom_at(img, zk, 192, 136, W / 2, H / 2 - 2)
    blast_rain(img, t, CLASH, W / 2, H / 2, seed=2)
    A.rain_layer(img, t, 1.0)
    if CLASH <= t < CLASH + 0.07:
        fx.impact_frame(img, (250, 250, 255), (14, 12, 24), threshold=90)
    if XCH[2] <= t < XCH[2] + 0.04:
        fx.flash(img, 0.5)
    X, Y = to(192, 139)
    sfx_text(img, int(X + 46), int(Y - 46), "锵!!", t, CLASH + 0.05, 0.6, color=(255, 255, 255), size=26, angle=10)
    sfx_text(img, int(X - 60), int(Y - 30), "砰!", t, XCH[1], 0.4, size=18, angle=-12)
    fx.shift(img, sx, sy)


# ================================================================== B3: split face-off
def _panel(t, who):
    im = Image.new("RGB", (W, H))
    A.rakuyo(im, t, -60 if who == "kagura" else 40, dark=0.2)
    if who == "kagura":
        overlay_rect(im, 0, 0, W, H, (150, 30, 40), 0.35)
        fx.speed_lines(im, t, 100, 128, color=(196, 70, 70), count=34, inner=46, seed=7, thickness=1.2)
        actor(im, "kagura", 150, FLOOR, "ready", t, expr="angry", facing=1, refl=False)
        A.zoom_at(im, 5.2, 151, 131, 112, 96)
    else:
        overlay_rect(im, 0, 0, W, H, (40, 50, 140), 0.35)
        fx.speed_lines(im, t, 290, 128, color=(90, 110, 200), count=34, inner=46, seed=8, thickness=1.2)
        e = "open_eyes" if t >= EYES else "smile"
        actor(im, "kamui", 240, FLOOR, "ready", t, expr=e, facing=-1, refl=False)
        A.zoom_at(im, 5.2, 239, 131, 282, 100)
    fx.rain(im, t, count=70, seed=11 if who == "kagura" else 12, color=(160, 170, 196), speed=480, slant=0.3,
            length=10)
    return im


def shot_b3(img, t):
    k = ease_out(seg(t, B3, B3 + 0.12))
    left = _panel(t, "kagura")
    right = _panel(t, "kamui")
    img.paste((0, 0, 0), (0, 0, W, H))
    # slanted divider from (212, 0) to (172, H)
    offl = int(-(1 - k) * 230)
    offr = int((1 - k) * 230)
    mask_l = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask_l).polygon([(0, 0), (210 + offl, 0), (170 + offl, H), (0, H)], fill=255)
    mask_r = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask_r).polygon([(214 + offr, 0), (W, 0), (W, H), (174 + offr, H)], fill=255)
    sl = Image.new("RGB", (W, H))
    sl.paste(left, (offl, 0))
    sr = Image.new("RGB", (W, H))
    sr.paste(right, (offr, 0))
    img.paste(sl, (0, 0), mask_l)
    img.paste(sr, (0, 0), mask_r)
    d = ImageDraw.Draw(img)
    d.line([(212 + offr, 0), (172 + offr, H)], fill=INK, width=5)
    d.line([(212 + offr, 0), (172 + offr, H)], fill=(255, 255, 255), width=2)
    if t >= EYES and t < EYES + 0.06:
        fx.flash(img, 0.35, (180, 210, 255))
    if EYES <= t < EYES + 0.5:
        fx.sparkle(img, 300, 88, t, EYES, size=9, color=(220, 240, 255))
        fx.sparkle(img, 260, 88, t, EYES + 0.05, size=6, color=(220, 240, 255))
    dx, dy = fx.shake_offset(t, EYES, 0.2, 2, seed=9)
    fx.shift(img, dx, dy)


# ================================================================== B4 + C: leap, landing, 够了
def _umi_y(t):
    return lerp(-60, FLOOR, ease_in(seg(t, DROP, LAND)))


def shot_b4c(img, t):
    fl = A.lightning_amt(t, LAND - 0.02) * 0.6
    A.rakuyo(img, t, 0, flash=fl)
    A.ground_splashes(img, t, seed=3)
    d = ImageDraw.Draw(img)
    # crater (after landing)
    if t >= LAND:
        d.ellipse([UMI_X - 26, FLOOR - 3, UMI_X + 26, FLOOR + 5], fill=(28, 32, 42))
        d.ellipse([UMI_X - 22, FLOOR - 2, UMI_X + 22, FLOOR + 3], fill=(40, 46, 58))
        for i in range(7):
            r = rng("crack", i)
            a = r.uniform(-math.pi, 0) if i % 2 else r.uniform(0, math.pi)
            L = r.uniform(24, 46)
            x1, y1 = UMI_X + math.cos(a) * L, FLOOR + 1 + math.sin(a) * L * 0.22
            xm, ym = UMI_X + math.cos(a + 0.2) * L * 0.5, FLOOR + 1 + math.sin(a + 0.2) * L * 0.11
            d.line([(UMI_X + math.cos(a) * 20, FLOOR + 1 + math.sin(a) * 4), (xm, ym), (x1, y1)], fill=(24, 26, 36))
    # speed lines behind Umibozu's shout
    if SHOUT <= t < 5.35:
        speed_bg(img, t, UMI_X, 138, seed=3, color=(120, 134, 148), count=44, inner=22)
    elif B4 <= t < LAND:
        pass
    # ---- the shadow of the falling father
    if WHISTLE <= t < LAND:
        k = seg(t, WHISTLE, LAND)
        rw = 3 + 18 * k * k
        overlay_rect(img, int(UMI_X - rw), FLOOR - 2, int(rw * 2), 4, (0, 0, 0), 0.25 + 0.35 * k)
    # ---- siblings
    if t < LAND:
        k = seg(t, B4, LAND + 0.05)
        kx, ky = arc((150, FLOOR), (181, FLOOR - 36), k, 26)
        mx, my = arc((236, FLOOR), (203, FLOOR - 36), k, 26)
        pk = "jump" if k < 0.45 else "attack"
        pp = None if pk == "jump" else lerp(0.05, 0.3, seg(k, 0.45, 1))
        actor(img, "kagura", kx, ky, pk, t, p=pp, expr="shout", facing=1)
        actor(img, "kamui", mx, my, pk, t, p=pp, facing=-1)
        if t < B4 + 0.1:
            fx.smoke_puff(img, t, B4, 150, FLOOR - 1, 7, seed=4, color=(150, 166, 184), life=0.4)
            fx.smoke_puff(img, t, B4, 236, FLOOR - 1, 7, seed=5, color=(150, 166, 184), life=0.4)
    else:
        # Kagura: blown back to the left, skids
        if t < 4.78:
            k = seg(t, LAND, 4.78)
            x, y = arc((181, FLOOR - 36), (KAG_X + 6, FLOOR), k, 14)
            actor(img, "kagura", x, y, "hit", t, p=k, facing=1, rot=int(-20 * (1 - k)))
        elif t < 5.05:
            x = lerp(KAG_X + 6, KAG_X, ease_out(seg(t, 4.78, 5.0)))
            actor(img, "kagura", x, FLOOR, "land", t, p=seg(t, 4.78, 5.05), expr="angry", facing=1)
        elif t < 5.9:
            actor(img, "kagura", KAG_X, FLOOR, "shock", t, p=seg(t, 5.05, 5.9), facing=1)
        else:
            actor(img, "kagura", KAG_X, FLOOR, "idle", t, expr="deadpan", facing=1)
        # Kamui: backflip, lands light as a cat
        if t < 4.8:
            k = seg(t, LAND, 4.8)
            x, y = arc((203, FLOOR - 36), (KAM_X, FLOOR), k, 22)
            actor(img, "kamui", x, y, "jump", t, facing=-1, rot=int(-360 * ease_out(k)) % 360)
        elif t < 5.0:
            actor(img, "kamui", KAM_X, FLOOR, "land", t, p=seg(t, 4.8, 5.0), facing=-1)
        else:
            actor(img, "kamui", KAM_X, FLOOR, "idle", t, expr="smug" if t < 6.0 else "normal", facing=-1)
        fx.smoke_puff(img, t, 4.78, KAG_X + 4, FLOOR - 1, 8, seed=6, color=(150, 166, 184), life=0.5)
        fx.smoke_puff(img, t, 4.80, KAM_X, FLOOR - 1, 6, seed=7, color=(150, 166, 184), life=0.4)
        water_crown(img, t, 4.78, KAG_X + 6, FLOOR, seed=8, n=14, speed=(40, 100), life=0.5)
    # ---- Umibozu
    if t >= DROP:
        uy = _umi_y(t)
        if t < LAND:
            # falling: vertical streaks above him
            for i in range(6):
                xx = UMI_X - 8 + i * 3
                d.line([(xx, uy - 70), (xx, uy - 36 - (i % 3) * 6)], fill=(200, 214, 236))
            actor(img, "umibozu", UMI_X, uy, "jump", t, expr="angry", facing=1, refl=False, shadow=False)
        elif t < SHOUT:
            actor(img, "umibozu", UMI_X, FLOOR, "land", t, p=0.1, expr="angry", facing=1)
        else:
            actor(img, "umibozu", UMI_X, FLOOR, "stop", t, facing=1)
    # landing fx (world)
    shock_ring(img, t, LAND, UMI_X, FLOOR + 1, speed=380, flat=0.2, life=0.5)
    shock_ring(img, t, LAND + 0.05, UMI_X, 136, speed=320, flat=0.9, life=0.3)
    water_crown(img, t, LAND, UMI_X, FLOOR, seed=11, n=56, speed=(100, 260), life=0.9)
    fx.burst(img, t, LAND, UMI_X, FLOOR - 2, n=16, colors=[(70, 76, 88), (100, 108, 120)], speed=(60, 160),
             gravity=380, life=0.8, size=(1, 3), seed=12, spread=(200, 340))
    for i in range(5):
        fx.smoke_puff(img, t, LAND + 0.02 * i, UMI_X - 30 + i * 15, FLOOR - 2, size=10, seed=20 + i,
                      color=(126, 138, 152), life=0.8)
    # ---- camera
    if t < LAND:
        zk, fx_, fy_ = lerp(1.6, 1.75, seg(t, B4, LAND)), 192, 122
    else:
        u = ease_in_out(seg(t, PUSH0, PUSH1))
        zk = lerp(1.55, 2.05, u) + 0.12 * seg(t, PUSH1, GAG)
        fx_, fy_ = UMI_X, lerp(126, 137, u)
    sy_scr = lerp(H / 2, 112, ease_in_out(seg(t, PUSH0, PUSH1)))
    to = A.zoom_at(img, zk, fx_, fy_, W / 2, sy_scr)
    blast_rain(img, t, LAND, *to(UMI_X, FLOOR - 10), seed=5, n=60)
    A.rain_layer(img, t, 1.0)
    if LAND <= t < LAND + 0.06:
        fx.impact_frame(img, (250, 250, 255), (14, 12, 24), threshold=96)
    elif LAND + 0.06 <= t < LAND + 0.25:
        fx.flash(img, 0.5 * (1 - seg(t, LAND + 0.06, LAND + 0.25)))
    X, Y = to(UMI_X, FLOOR - 86)
    sfx_text(img, int(X), int(Y), "咚——!!", t, LAND + 0.04, 0.55, color=(255, 240, 200), size=28, angle=-6)
    dx, dy = fx.shake_offset(t, LAND, 0.45, 5, seed=3)
    ex, ey = fx.shake_offset(t, SHOUT, 0.3, 2, seed=4)
    fx.shift(img, dx + ex, dy + ey)
    umi_card(img, t)


def umi_card(img, t):
    # latin caption tag instead of the registry name (which would repeat 星海坊主 twice on the band)
    name_card(img, t, CARD, 2.2, "UMIBOZU", "星海坊主", "最强的宇宙猎人｜神乐的秃头老爸", side="right",
              color=get_def("umibozu").color)


# ================================================================== C2: the bald-head gag (close two-shot)
def _dome(t):
    """World position of the shiny top of Umibozu's head (he stands at UMI_X in 'stop')."""
    spr, ax, ay = render_sprite("umibozu", "stop", t, None, "normal", 1)
    pos = A.cached("umi_dome", lambda: find_px(spr, [(255, 250, 240)]))
    if not pos:
        return UMI_X, FLOOR - 36
    return UMI_X - ax + pos[0] + 1, FLOOR - ay + pos[1] + 1


def _vein(img, x, y, s):
    """Manga anger mark (four red arcs) centred at (x, y), half-size s."""
    d = ImageDraw.Draw(img)
    g = 2                                   # each arm is an 'L' whose corner points at the centre
    for w, col in ((4, INK), (2, (236, 52, 60))):
        for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            pts = [(x + sx * s, y + sy * g), (x + sx * g, y + sy * g), (x + sx * g, y + sy * s)]
            d.line(pts, fill=col, width=w)


def _sweat(img, x, y):
    d = ImageDraw.Draw(img)
    d.polygon([(x, y - 12), (x - 7, y + 1), (x - 5, y + 6), (x, y + 8), (x + 5, y + 6), (x + 7, y + 1)], fill=INK)
    d.polygon([(x, y - 9), (x - 5, y + 1), (x - 3, y + 5), (x + 3, y + 5), (x + 5, y + 1)], fill=(150, 210, 255))
    d.line([(x - 2, y - 1), (x - 2, y + 2)], fill=(255, 255, 255), width=2)


def shot_gag(img, t):
    A.rakuyo(img, t, 0)
    A.ground_splashes(img, t, seed=3)
    d = ImageDraw.Draw(img)
    d.ellipse([UMI_X - 26, FLOOR - 3, UMI_X + 26, FLOOR + 5], fill=(28, 32, 42))       # the crater
    d.ellipse([UMI_X - 22, FLOOR - 2, UMI_X + 22, FLOOR + 3], fill=(40, 46, 58))
    mad = t >= VEIN
    actor(img, "kagura", KAG_X, FLOOR, "idle", t, expr="deadpan", facing=1)
    actor(img, "umibozu", UMI_X, FLOOR, "stop", t, expr="angry" if mad else "normal", facing=1,
          flash=0.0)
    # camera: close two-shot, creeping in
    u = ease_in_out(seg(t, GAG, D1))
    zk = lerp(3.0, 3.3, u)
    to = A.zoom_at(img, zk, 158, 134, W / 2, H / 2 + 10)
    A.rain_layer(img, t, 0.9, seed=7)
    hx, hy = to(*_dome(t))
    hx, hy = int(hx), int(hy)
    dd = ImageDraw.Draw(img)
    for i, tt in enumerate(TINGS):
        fall = 0.12 if i < 2 else 0.07
        if tt - fall <= t < tt:                           # the drop falling onto the dome
            yy = lerp(hy - 70, hy - 3, seg(t, tt - fall, tt))
            dd.line([(hx - 1, yy - 12), (hx - 1, yy)], fill=INK, width=4)
            dd.line([(hx - 1, yy - 11), (hx - 1, yy - 1)], fill=(210, 232, 255), width=2)
        if tt <= t < tt + 0.45:
            fx.burst(img, t, tt, hx, hy - 2, n=8, colors=[(220, 236, 255), (255, 255, 255)],
                     speed=(60, 120), gravity=420, life=0.35, seed=40 + i, spread=(200, 340))
            _glint(img, hx, hy - 1, t, tt, 12 if i < 2 else 8)
    # onomatopoeia: two slow 'ting's, then a rapid triple
    # (all kept below y~76 so the name card never covers them)
    sfx_text(img, hx - 58, hy - 12, "叮!", t, TINGS[0], 0.42, color=(236, 248, 255), size=20, angle=10, shake=0)
    sfx_text(img, hx + 50, hy - 8, "叮!", t, TINGS[1], 0.34, color=(236, 248, 255), size=20, angle=-10, shake=0)
    for i, (ox, oy) in enumerate(((-40, -28), (64, 18), (-64, 14))):
        sfx_text(img, hx + ox, hy + oy, "叮", t, TINGS[2 + i], D1 - TINGS[2 + i], color=(236, 248, 255),
                 size=16, angle=(-14, 6, 12)[i], shake=0)
    # Kagura's deadpan: sweat drop + '……'
    kx, ky = to(KAG_X, FLOOR - 30)
    if t >= DOTS - 0.1:
        _sweat(img, int(kx + 40), int(ky + 12 + min(8, (t - DOTS + 0.1) * 10)))
    if t >= DOTS:
        speech_bubble(img, int(kx + 8), int(ky - 12), "……", t, DOTS, tail=(0, 1), size=14, typewriter=False)
    # ...and the old man finally snaps
    if mad:
        s = 5 if step_frame(t, 8) % 2 else 7
        _vein(img, hx + 26, hy + 4, s)
    dx, dy = fx.shake_offset(t, VEIN, 0.25, 3, seed=13)
    fx.shift(img, dx, dy)
    umi_card(img, t)


def _glint(img, x, y, t, t0, size):
    """Chunky 4-point glint with an ink rim (reads on any background)."""
    p = (t - t0) * 4
    if p < 0 or p > 2:
        return
    s = int(size * math.sin(min(math.pi, p * math.pi / 2)))
    if s <= 0:
        return
    d = ImageDraw.Draw(img)
    d.polygon([(x - s, y), (x - 1, y - 1), (x, y - s), (x + 1, y - 1), (x + s, y), (x + 1, y + 1), (x, y + s),
               (x - 1, y + 1)], fill=(255, 255, 255), outline=(120, 170, 230))
    d.point((x, y), fill=(255, 255, 255))


# ================================================================== D1: Kagura's vow
def shot_d1(img, t):
    A.rakuyo(img, t, -90, dark=0.18)
    A.ground_splashes(img, t, seed=4)
    typing = t < D1 + 0.9
    if t < POINT:
        actor(img, "kagura", 150, FLOOR, "idle", t, expr="determined", facing=1)
    elif t < D1 + 1.5:
        e = ("shout" if step_frame(t, 7) % 2 == 0 else "determined") if typing else "determined"
        actor(img, "kagura", 150, FLOOR, "point", t, p=seg(t, POINT, POINT + 0.6), expr=e, facing=1)
    else:
        actor(img, "kagura", 150, FLOOR, "idle", t, expr="determined", facing=1)
    # slow drift, then a push-in on her face once the vow has been said
    u = ease_in_out(seg(t, D1, D2))
    v = ease_in_out(seg(t, D1 + 1.3, D2))
    A.zoom_at(img, lerp(3.0, 3.15, u) + 0.4 * v, 152, lerp(138, 134, v), 146, lerp(92, 96, v))
    if POINT <= t < POINT + 0.25:          # the point lands with a little shock ring around her
        fx.speed_lines(img, t, 146, 90, color=(120, 134, 150), count=30, inner=70, seed=21, thickness=1)
    # over-the-shoulder: Kamui, dark and out of focus in the right foreground
    spr, ax, ay = render_sprite("kamui", "idle", t, None, "normal", -1)
    sil = _silhouette(spr, keep=0.2).resize((spr.width * 4, spr.height * 4), Image.NEAREST)
    sx = 344 + int(wave(t, 0.2, 2.0)) - int(10 * u)
    img.paste(sil, (sx - ax * 4, 104 - (ay - 26) * 4), sil)
    A.rain_layer(img, t, 1.2, seed=5)
    fx.vignette(img, 0.4)
    letterbox(img)


# ================================================================== D2: Kamui leaves
def shot_d2(img, t):
    fl = A.lightning_amt(t, FAR_BOLT) * 0.55
    A.rakuyo(img, t, 0, flash=fl, bolt_x=330, bolt_seed=3)
    A.ground_splashes(img, t, seed=5)
    # Umibozu watching; Kagura takes a few steps after her brother and reaches out
    actor(img, "umibozu", KAG_X - 28, FLOOR, "idle", t, expr="sad", facing=1)
    reach_t = STEP + 0.36
    if t < STEP:
        actor(img, "kagura", KAG_X, FLOOR, "idle", t, expr="sad", facing=1)
    elif t < reach_t:
        x = lerp(KAG_X, KAG_X + 16, ease_out(seg(t, STEP, reach_t)))
        actor(img, "kagura", x, FLOOR, "walk", t, expr="sad", facing=1)
    else:
        actor(img, "kagura", KAG_X + 16, FLOOR, "point", t, p=0.25 * seg(t, reach_t, reach_t + 0.15), expr="sad",
              facing=1)
    # Kamui
    if t < TURN:
        actor(img, "kamui", KAM_X, FLOOR, "idle", t, expr="smile", facing=-1)
    elif t < WALK:
        actor(img, "kamui", KAM_X, FLOOR, "umbrella_open", t, facing=1)
        fx.smoke_puff(img, t, TURN, KAM_X + 1, FLOOR - 40, size=8, seed=9, color=(160, 150, 200), life=0.35)
    else:
        x = KAM_X + (t - WALK) * 46
        al = 1 - 0.8 * seg(t, FAR_BOLT - 0.1, E1)
        actor(img, "kamui", x, FLOOR, "walk", t, facing=1, alpha=al, arm_f=150, weapon=95,
              weapon_kind="umbrella_open", sheathed=False)
    if t >= WALK:
        mist = A.cached("d2mist", lambda: _mist_patch())
        k = seg(t, WALK, E1)
        img.paste(mist, (int(KAM_X + 30 + 30 * k), 100), mist)
    # camera: hold the smile close-up, then pull back fast enough that Kagura is in frame when she reaches
    u = ease_in_out(seg(t, TURN + 0.1, STEP + 0.2))
    zk = lerp(2.7, 1.45, u) - 0.05 * seg(t, STEP + 0.2, E1)
    fx_ = lerp(KAM_X, 200, u)
    fy_ = lerp(138, 128, u)
    A.zoom_at(img, zk, fx_, fy_, lerp(206, W / 2, u), lerp(104, H / 2, u))
    A.rain_layer(img, t, 1.0, seed=6)
    if TURN <= t < TURN + 0.05:
        fx.flash(img, 0.12)
    letterbox(img)


def _silhouette(spr, col=(12, 14, 24), rim=(88, 102, 132), keep=0.26):
    a = np.asarray(spr).copy()
    m = a[..., 3] > 0
    a[..., :3] = (a[..., :3].astype(np.float32) * keep + np.array(col, np.float32) * (1 - keep)).astype(np.uint8)
    edge = np.zeros_like(m)
    edge[:, 1:] |= ~m[:, :-1]
    edge[:, 0] = True
    edge[1:, :] |= ~m[:-1, :]
    rimm = m & edge
    a[rimm, 0], a[rimm, 1], a[rimm, 2] = rim
    return Image.fromarray(a, "RGBA")


def _mist_patch():
    w, h = 120, 64
    arr = np.zeros((h, w, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = 110, 124, 134
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a = np.clip(1 - np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)), 0, 1) * 0.5
    q = np.floor(a * 8 + C.bayer(h, w)) / 8
    arr[..., 3] = (np.clip(q, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


# ================================================================== E1: harbour at dawn
def shot_e1(img, t):
    u = ease_in_out(seg(t, E1, E2))
    cam = lerp(-6, 22, u)
    E.skyline(img, cam, t, "dawn", ships=True, near=False)
    C.river(img, 172, 44, t, "dawn", cam)
    lift = seg(t, E1 + 0.2, E2)
    sy = lerp(146, 118, ease_in_out(lift))
    sx = 292 - cam + lerp(0, 10, lift)
    # thruster ripples on the water under the ship
    d = ImageDraw.Draw(img)
    for i in range(3):
        k = ((t * 2.2 + i / 3) % 1.0)
        rw = 6 + k * 34
        d.ellipse([sx - rw, 186 - rw * 0.12, sx + rw, 186 + rw * 0.12], outline=(255, 236, 222) if k < 0.6 else (220, 190, 196))
    A.pier(img, 236 - cam, 180, t)
    A.draw_ship(img, sx, sy, t, lift=0.7 + 0.5 * lift)
    A.gulls(img, t, n=5, seed=1, area=(0, 30, W, 100))
    A.zoom_at(img, lerp(1.06, 1.14, u), 250, 132)
    k = 1 - seg(t, E1, E1 + 0.35)
    if k > 0:
        fx.flash(img, k * 0.85, (255, 244, 230))


# ================================================================== E2: deck / cigarette
HJ_X, KD_X, OK_X = 196, 140, 252
DECK_CAM = 720          # puts the Terminal tower behind Kondo


def _tears(img, x, y, t, seed=0):
    """Kondo's comedic wind-blown tear streams flowing LEFT from his eyes."""
    d = ImageDraw.Draw(img)
    for s, (ex, ey) in enumerate(((x - 3, y), (x + 3, y))):
        for i in range(16):
            k = i / 15
            px = ex - i * 1.6
            py = ey + 1 + math.sin(t * 18 + i * 0.7 + s) * 1.2 * k + k * k * 4
            c = (150, 210, 255) if (i + step_frame(t, 12)) % 4 else (230, 246, 255)
            d.point((px, py), fill=c)
            if i < 8:
                d.point((px, py + 1), fill=(110, 180, 240))


_BAYER4 = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def _dither_disc(img, cx, cy, r, a, col=(238, 234, 240), edge=(204, 198, 214)):
    """Soft pixel smoke blob: ordered-dither coverage a (0..1), shaded lower-right rim."""
    if a <= 0 or r < 0.5:
        return
    px = img.load()
    ir = int(math.ceil(r))
    cx_i, cy_i = int(round(cx)), int(round(cy))
    for yy in range(-ir, ir + 1):
        for xx in range(-ir, ir + 1):
            dd = xx * xx + yy * yy
            if dd > r * r:
                continue
            X, Y = cx_i + xx, cy_i + yy
            if not (0 <= X < W and 0 <= Y < H):
                continue
            if (_BAYER4[Y % 4][X % 4] + 0.5) / 16 > a:
                continue
            px[X, Y] = edge if (dd > (r - 1.2) ** 2 and xx + yy > 0) else col


def _smoke(img, t, t0, x, y, n=8, spacing=0.05, life=1.0, grow=4.0, drift=30):
    for i in range(n):
        age = t - (t0 + i * spacing)
        if not (0 <= age < life):
            continue
        k = age / life
        px = x - age * drift - i * 0.6
        py = y - age * 9 + math.sin(age * 7 + i * 1.3) * 1.2
        _dither_disc(img, px, py, 0.8 + grow * math.sqrt(k), (1 - k) ** 1.2 * 0.95)


def _wisp(img, t, x, y):
    """Thin cigarette smoke curling up and bending left in the wind."""
    for i in range(7):
        age = ((t * 1.6 + i / 7) % 1.0)
        px = x - age * 10 + math.sin(t * 5 + age * 9) * 1.1
        py = y - age * 9
        if (_BAYER4[int(py) % 4][int(px) % 4] + 0.5) / 16 < (1 - age) * 0.9:
            pset(img, int(px), int(py), (226, 222, 232))


def shot_e2(img, t):
    u = ease_in_out(seg(t, E2, E3))
    A.deck(img, t, lerp(-34, 8, u), cam=DECK_CAM)
    # stern flag pole
    d = ImageDraw.Draw(img)
    d.line([(290, 80), (290, 150)], fill=INK, width=3)
    d.line([(290, 80), (290, 150)], fill=(150, 98, 66), width=1)
    A.draw_flag(img, 289, 82, t, 40, 24, big=True, fps=12)
    # characters
    actor(img, "kondo", KD_X, FLOOR, "cry", t, facing=-1, refl=False)
    if t >= PULL - 0.2:
        _tears(img, KD_X - 3, FLOOR - 25, t)
    # Okita couldn't care less: napping on the deck with his eye-mask (Kondo bawls, Hijikata broods)
    actor(img, "okita", OK_X, FLOOR, "nap", t, facing=-1, refl=False)
    EXH = LIT + 0.3
    if t < LIT:
        spr, x0, y0 = actor(img, "hijikata", HJ_X, FLOOR, "idle", t, expr="blink", facing=-1, refl=False,
                            arm_f=152, arm_b=-10)
    elif t < EXH:
        spr, x0, y0 = actor(img, "hijikata", HJ_X, FLOOR, "idle", t, expr="inhale", facing=-1, refl=False,
                            arm_f=lerp(152, 12, seg(t, LIT, EXH - 0.05)), arm_b=-10)
    elif t < EXH + 0.75:
        spr, x0, y0 = actor(img, "hijikata", HJ_X, FLOOR, "idle", t, expr="exhale", facing=-1, refl=False)
    else:
        spr, x0, y0 = actor(img, "hijikata", HJ_X, FLOOR, "idle", t, facing=-1, refl=False)
    # lighter flame + warm glow
    ember = A.cached("hj_ember", lambda: find_px(render_sprite("hijikata", "idle", 0.5, None, "normal", -1)[0],
                                                   [(255, 92, 44)]))
    if ember:
        ex, ey = x0 + ember[0], y0 + ember[1]
        if LIGHT - 0.12 <= t < LIT:
            lit = t >= LIGHT
            d.rectangle([ex - 1, ey + 1, ex + 1, ey + 4], fill=INK)             # lighter
            d.rectangle([ex, ey + 1, ex, ey + 3], fill=(200, 206, 220))
            if lit:
                f = step_frame(t, 15, 3)
                C.add_sprite(img, C.glow_sprite(9, (255, 130, 40), 0.7), ex - 9, ey - 11)
                d.polygon([(ex - 2, ey), (ex, ey - 6 - f), (ex + 2, ey)], fill=(255, 150, 50))
                d.polygon([(ex - 1, ey), (ex, ey - 4 - f // 2), (ex + 1, ey)], fill=(255, 244, 180))
            elif step_frame(t, 30) % 2:
                pset(img, ex, ey - 1, (255, 240, 200))                         # flint spark
        if LIT <= t < EXH - 0.05:
            C.add_sprite(img, C.glow_sprite(5, (255, 120, 40), 0.7), ex - 5, ey - 5)
        # exhale: a long stream of dithered smoke puffs carried off to the left by the wind,
        # then a thin wisp curling from the cigarette tip
        if t >= EXH:
            _smoke(img, t, EXH, ex - 2, ey + 1, n=9, spacing=0.05, life=1.1, grow=4.5, drift=34)
        if t >= LIT + 0.1:
            _wisp(img, t, ex - 1, ey - 1)
    A.wind_streaks(img, t, n=8, seed=3, y0=70, y1=150)
    # camera: close-up on the lighter -> pull back to the trio
    k = ease_in_out(seg(t, PULL, PULL + 1.0))
    zk = lerp(5.0, 2.05, k)
    fx_ = lerp(HJ_X - 3, 196, k)
    fy_ = lerp(135, 126, k)
    A.zoom_at(img, zk, fx_, fy_, W / 2, lerp(100, 96, k))
    if E2 <= t < E2 + 0.05:
        fx.flash(img, 0.2)


# ================================================================== E3: the dock
OT_X = 268
E3B = E3 + 1.2
SUN = (118, 122)


def _dock_world(img, t):
    C.sky(img, "dawn", t, horizon=150, body=False)
    C.clouds(img, t, 0, "dawn", seed=14, count=6, y0=6, y1=74, speed=1.5)
    A.sunrise(img, t, *SUN)
    C.river(img, 142, 74, t, "dawn", reflect_x=SUN[0])
    A.gulls(img, t, n=4, seed=3, area=(150, 50, W, 110), color=(96, 70, 104), speed=-18)
    A.embankment(img, 322, 158)
    C.cherry_tree(img, 346, 162, t, scale=1, tod="dawn")
    A.pier(img, 170, 160, t)


def _ship_path(t):
    k = ease_in_out(seg(t, E3 - 0.4, TWINKLE))
    return lerp(214, 136, k), lerp(106, 80, k) - wave(t, 0.5, 1.2), lerp(0.40, 0.18, k)


def shot_e3(img, t):
    _dock_world(img, t)
    if t < E3B:
        sx, sy, sc = _ship_path(t)
        sil = A.ship_silhouette(sc)
        img.paste(sil, (int(sx - sil.width / 2), int(sy - sil.height / 2)), sil)
        actor(img, "otae", OT_X, FLOOR, "idle", t, expr="open", facing=-1, refl=False)
        fx.sakura(img, t, count=16, seed=4, wind=-24, fall=16, area=(160, 60, W, 180))
        u = ease_in_out(seg(t, E3, E3B))
        to = A.zoom_at(img, lerp(1.2, 1.28, u), 212, 118)
        if BUBBLE <= t:
            X, Y = to(sx + 2, sy + 5)
            speech_bubble(img, int(X), int(Y), "阿妙小姐～～！", t, BUBBLE, tail=(0, -1))
    else:
        if t < E3B + 0.2:
            actor(img, "otae", OT_X, FLOOR, "idle", t, expr="open", facing=-1, refl=False)
        elif t < E3B + 0.85:
            actor(img, "otae", OT_X, FLOOR, "wave", t, facing=-1, refl=False)
        else:
            actor(img, "otae", OT_X, FLOOR, "idle", t, expr="normal", facing=-1, refl=False)
        u = ease_in_out(seg(t, E3B, END))
        A.zoom_at(img, lerp(2.5, 2.7, u), OT_X - 2, 138, 262, 112)
        # warm sunlight from the left + the far-away ship becoming a star
        C.add_sprite(img, C.glow_sprite(110, (255, 150, 100), 0.35), -170, 10)
        k = seg(t, E3B, TWINKLE)
        px, py = lerp(150, 126, k), lerp(58, 46, k)
        if t < TWINKLE + 0.05:
            sil = A.ship_silhouette(0.12)
            img.paste(sil, (int(px - sil.width / 2), int(py - sil.height / 2)), sil)
            if t < TWINKLE - 0.03:
                speech_bubble(img, int(px), int(py + 5), "阿妙小姐～～！", t, BUBBLE, tail=(0, -1))
        else:
            C.add_sprite(img, C.glow_sprite(12, (255, 220, 170), 0.8 * (1 - seg(t, TWINKLE, TWINKLE + 0.6))),
                         int(px) - 12, int(py) - 12)
            _glint(img, int(px), int(py), t, TWINKLE, 13)
            _glint(img, int(px), int(py), t, TWINKLE + 0.42, 7)
            if t >= TWINKLE + 0.85 and step_frame(t, 3) % 2 == 0:
                pset(img, int(px), int(py), (255, 250, 230))
        fx.sakura(img, t, count=26, seed=5, wind=-26, fall=18)
    letterbox(img, 14)


# ================================================================== scene
class Rakuyo(Scene):
    id = "s12"
    title = "洛阳决战·离别"
    duration = END
    music = [(0, "battle"), (D2, "sad")]
    music_vol = 0.55
    subs = [
        (SHOUT, GAG, "umibozu", "够了！"),
        (D1 + 0.05, D2 - 0.02, "kagura", "我一定会把哥哥带回家阿鲁！"),
        (E1 + 0.02, PULL - 0.03, None, "被解散的真选组，在黎明时分离开了江户。"),
        (PULL + 0.01, E3 - 0.05, "hijikata", "……我们会回来的。"),
    ]

    def render(self, img, t):
        if t < B0:
            shot_a(img, t)
        elif t < B2:
            shot_b1(img, t)
        elif t < B3:
            shot_b2(img, t)
        elif t < B4:
            shot_b3(img, t)
        elif t < GAG:
            shot_b4c(img, t)
        elif t < D1:
            shot_gag(img, t)
        elif t < D2:
            shot_d1(img, t)
        elif t < E1:
            shot_d2(img, t)
        elif t < E2:
            shot_e1(img, t)
        elif t < E3:
            shot_e2(img, t)
        else:
            shot_e3(img, t)

    def cues(self):
        return [
            # ambience
            Cue(0.0, "rain", vol=0.55, dur=E1 - 0.1),
            Cue(0.0, "wind", vol=0.25, dur=E1),
            # A
            Cue(0.05, "sting_dramatic", vol=0.7),
            Cue(0.36, "thunder", vol=0.8),
            Cue(0.40, "gong", vol=0.5),
            # B1
            Cue(1.92, "thunder", vol=0.9),
            Cue(2.24, "charge", vol=0.4),
            Cue(RUN, "dash"),
            Cue(RUN + 0.02, "run", vol=0.4, dur=0.2),
            # B2
            Cue(CLASH, "clang"), Cue(CLASH, "impact"), Cue(CLASH + 0.02, "punch_big", vol=0.7),
            Cue(CLASH + 0.05, "explosion_small", vol=0.4),
            Cue(XCH[0], "punch", vol=0.8), Cue(XCH[0] + 0.01, "clang", vol=0.6, pitch=1.2),
            Cue(XCH[1], "kick"), Cue(XCH[1] + 0.01, "clang", vol=0.5, pitch=0.9),
            Cue(XCH[2], "clang", pitch=1.05), Cue(XCH[2], "slash_big", vol=0.6),
            # B3
            Cue(B3, "whoosh", vol=0.7),
            Cue(EYES, "shing", vol=0.8), Cue(EYES, "heartbeat", vol=0.7),
            # B4 / C
            Cue(B4, "jump", vol=0.7), Cue(B4 + 0.03, "jump", vol=0.6, pitch=1.15),
            Cue(WHISTLE, "fall_whistle", vol=0.9),
            Cue(LAND, "impact"), Cue(LAND, "explosion", vol=0.7), Cue(LAND + 0.01, "land"),
            Cue(LAND + 0.03, "crash", vol=0.5),
            Cue(4.46, "whoosh", vol=0.6),
            Cue(4.78, "land", vol=0.6), Cue(4.80, "land", vol=0.5, pitch=1.2),
            Cue(SHOUT, "vein", vol=0.6),
            Cue(CARD, "whoosh", vol=0.5),
            Cue(5.05, "shock", vol=0.5),
            # C2 gag: 'chiin' x2, then a rapid triple, then the anger vein
            Cue(TINGS[0], "bell", vol=0.45, pitch=1.6), Cue(TINGS[1], "bell", vol=0.45, pitch=1.8),
            Cue(TINGS[2], "bell", vol=0.3, pitch=2.1), Cue(TINGS[3], "bell", vol=0.3, pitch=2.2),
            Cue(TINGS[4], "bell", vol=0.3, pitch=2.35),
            Cue(DOTS, "sweat", vol=0.5),
            Cue(VEIN, "vein", vol=0.8),
            # D
            Cue(POINT, "whoosh", vol=0.4, pitch=1.3),
            Cue(TURN, "whoosh", vol=0.6), Cue(TURN + 0.02, "pop", vol=0.5),
            Cue(WALK, "footsteps", vol=0.35, dur=E1 - WALK),
            Cue(STEP, "footsteps", vol=0.25, dur=0.4),
            Cue(FAR_BOLT, "thunder", vol=0.45),
            # E1 harbour
            Cue(E1, "shine", vol=0.4, pitch=0.8),
            Cue(E1, "river", vol=0.35, dur=E2 - E1),
            Cue(E1, "engine_hum", vol=0.45, dur=E3 - E1),
            Cue(E1, "wind", vol=0.3, dur=END - E1),
            Cue(E1 + 0.3, "bell", vol=0.3),
            # E2 deck
            Cue(LIGHT, "pop", vol=0.45, pitch=1.8),
            Cue(LIGHT + 0.02, "fire", vol=0.3, dur=LIT - LIGHT),
            Cue(LIT + 0.3, "whoosh", vol=0.3, pitch=0.6),
            # E3 dock
            Cue(E3, "river", vol=0.4, dur=END - E3),
            Cue(BUBBLE, "blip", vol=0.4),
            Cue(TWINKLE, "twinkle"),
        ]


SCENE = Rakuyo()
