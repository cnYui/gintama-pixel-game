"""s06 「日常」 — rapid manga-panel vignettes of everyday Kabukicho (18 s, music 'comedy').

The whole scene is a manga page: every vignette is a new page that slides in from the
right; its panels (2 px ink border, white gutters, dotted paper) pop / slide / split in.
Each panel's content is rendered as a normal full-frame shot (world coords) and zoomed
with fx.zoom, then masked into the panel polygon.

SHOT LIST (scene time, seconds)
 V1 其一 MADAO            0.00– 3.00  riverbank at dusk, reeds + autumn leaves in the wind,
                                      slow push-in on Hasegawa in his cardboard box.
                                      name_card 长谷川泰三 0.30; a crow flies in (1.20) and
                                      lands with a caw (1.75); its 2nd caw 「阿呆～」 (2.53)
                                      gets a snap-zoom and MADAO starts crying (gloom lines).
 V2 其二 小钢珠            3.00– 5.90  pachinko parlor: Gintoki & Hasegawa bounce on stools,
                                      「来了!!」 pops; inset LCD (3.45) 7-7-[real reel strip]
                                      decelerates, lands on a PERFECT 7 (4.40, ding, frozen
                                      「！？」) ... creeps ... clunks onto 6 (4.62 scratch),
                                      4.70 page drains to grey, both burnt-out WHITE,
                                      4.95 red stamp 「输光」 + 「所持金：0円」,
                                      5.20–5.84 both crumble into ash blown away by the wind.
 V3 其三 周一              5.90– 8.80  calendar: 「周日」 page ripped off (6.20) → 「周一 /
                                      Jump!」; 6.45 split: the holy JUMP descends in a light
                                      beam (fanfare), Gintoki kneels reaching for it, star
                                      eyes (6.90), trembling, tears of joy; 「周一＝Jump发售日」.
 V4 其四 偶像              8.80–11.80  concert: Otsu singing under swinging spotlights, notes
                                      float from her mic (name_card 寺门通 9.15) → split
                                      (9.75): Shinpachi in happi coat with light sticks
                                      「通酱～！！」, hearts, chant letters L·O·V·E on the beat.
 V5 其五 醋昆布            11.80–14.40  Yorozuya office: Kagura sits on sleeping Sadaharu
                                      chewing sukonbu; his snot bubble grows and POPS (13.35)
                                      → he jolts up, Kagura is catapulted out of frame,
                                      「？」, whistle ... she drops back (14.02) and just keeps
                                      chewing 「嚼嚼」.
 V6 其六 跟踪狂            14.40–18.00  two stacked panels: top = Otae with tea on tatami,
                                      bottom = Kondo in the crawlspace under her floor,
                                      hearts. 15.35 dark aura, 15.80 she rises with the
                                      naginata, 16.20 STAB through the floor and the panel
                                      gutter, stopping an inch from Kondo's nose (frozen,
                                      cross-eyed, jaw drop). 16.70 caption 「※以上皆为日常」,
                                      16.80 the crow flaps across the page 「阿呆～ 阿呆～」.
Characters/poses: hasegawa box/cheer/idle/sit(ash) · gintoki cheer/idle/sit(ash)/kneel
(+custom star-eye patch) · otsu sing · shinpachi otaku_cheer · kagura sukonbu(legs=sit)
· sadaharu sleep/shock/idle · otae sit/attack/thrust(naginata down) · kondo stalk/kneel.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import (Scene, Cue, W, H, seg, lerp, clamp, ease_in, ease_out, ease_in_out,
                         ease_out_back, wave, step_frame, rng)
from engine.gfx import (INK, PAL, rect, pset, shade, mix, tint, ascii_sprite, stamp_line, overlay_rect)
from engine import fx
from engine.text import draw_text, text_sprite, text_width, sfx_text, name_card
from chars import draw_char, render_sprite
from bg import common as C, yorozuya as Y

from scenes import _s06_art as A

# ------------------------------------------------------------------ timing
T1, T2, T3, T4, T5, T6, TEND = 0.0, 3.0, 5.9, 8.8, 11.8, 14.4, 18.0
TR = 0.3                       # page slide duration

# V2
T_REACH = 3.45
T_MISS = 4.62                  # third reel clunks from 7 onto 6
T_SEVEN = T_MISS - 0.22        # ... after hanging on a perfect 7 for a heartbeat
T_GREY = 4.70
T_STAMP = 4.95
T_ASH = 5.20
T_ASH_END = 5.84
# V3
T_TEAR = 6.20
T_SPLIT = 6.45
# V4
T_PULL = 9.70
# V5
T_POP = 13.35                  # Sadaharu's snot bubble bursts
# V6
T_AURA = 15.35
T_RISE = 15.80
T_STAB = 16.20
T_CAP = 16.70

FULL = [(6, 6), (W - 6, 6), (W - 6, H - 6), (6, H - 6)]


# ------------------------------------------------------------------ panel machinery
def _paper(img, ox):
    """Page paper for x >= ox (new page sliding over the old one) + edge shadow."""
    ox = int(ox)
    if ox >= W:
        return
    pap = A.paper_layer()
    if ox <= 0:
        img.paste(pap)
        return
    img.paste(pap.crop((0, 0, W - ox, H)), (ox, 0))
    for i, a in enumerate((0.55, 0.35, 0.18)):
        x = ox - 1 - i
        if 0 <= x < W:
            overlay_rect(img, x, 0, 1, H, (0, 0, 0), a)


def _shrink(poly, k=1.0):
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    out = []
    for x, y in poly:
        dx, dy = cx - x, cy - y
        L = math.hypot(dx, dy) or 1
        out.append((x + dx / L * k * 1.42, y + dy / L * k * 1.42))
    return out


def _zoom(img, k, x0, y0):
    """Nearest zoom: world box (x0, y0, W/k, H/k) -> whole canvas; tolerates boxes
    outside the canvas (filled black)."""
    w, h = W / k, H / k
    if abs(k - 1) < 1e-3 and abs(x0) < 1e-3 and abs(y0) < 1e-3:
        return
    ix0, iy0 = math.floor(x0), math.floor(y0)
    ix1, iy1 = math.ceil(x0 + w), math.ceil(y0 + h)
    sub = img.crop((ix0, iy0, ix1, iy1))
    z = sub.resize((W, H), Image.NEAREST, box=(x0 - ix0, y0 - iy0, x0 - ix0 + w, y0 - iy0 + h))
    img.paste(z)


def panel(img, poly, t, draw, cam, ox=0, oy=0, enter=None, post=None, focus=None, border=True):
    """Render `draw(canvas, t)` (world coords), zoom by cam=(k, cx, cy) so world (cx,cy)
    lands on `focus` (screen, default = panel bbox centre), mask into `poly`.
    enter = (kind, t_in, dur) with kind in 'pop' | 'right' | 'left' | 'down' | 'up'.
    post(canvas, t, to_screen) draws after the zoom, in screen space.
    Returns the final screen polygon (or None if not visible yet)."""
    sc, ex, ey = 1.0, 0.0, 0.0
    if enter:
        kind, t_in, dur = enter
        if t < t_in:
            return None
        p = seg(t, t_in, t_in + dur)
        if kind == "pop":
            sc = lerp(0.35, 1.0, ease_out_back(p))
        elif kind == "right":
            ex = (1 - ease_out(p)) * (W + 20)
        elif kind == "left":
            ex = -(1 - ease_out(p)) * (W + 20)
        elif kind == "down":
            ey = -(1 - ease_out(p)) * (H + 20)
        elif kind == "up":
            ey = (1 - ease_out(p)) * (H + 20)
    xs = [p_[0] for p_ in poly]
    ys = [p_[1] for p_ in poly]
    bcx, bcy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    fcx, fcy = focus if focus else (bcx, bcy)
    P = [((x - bcx) * sc + bcx + ox + ex, (y - bcy) * sc + bcy + oy + ey) for x, y in poly]
    F = ((fcx - bcx) * sc + bcx + ox + ex, (fcy - bcy) * sc + bcy + oy + ey)
    if max(p_[0] for p_ in P) < 0 or min(p_[0] for p_ in P) >= W:
        return P
    k, cx, cy = cam
    canvas = Image.new("RGB", (W, H), (0, 0, 0))
    draw(canvas, t)
    _zoom(canvas, k, cx - F[0] / k, cy - F[1] / k)

    def to_screen(wx, wy):          # world -> screen coords after the zoom
        return F[0] + (wx - cx) * k, F[1] + (wy - cy) * k

    if post:
        post(canvas, t, to_screen)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(P, fill=255)
    img.paste(canvas, (0, 0), mask)
    if border:
        d = ImageDraw.Draw(img)
        for ddx, ddy in ((0, 0), (1, 0), (0, 1)):
            d.polygon([(x + ddx, y + ddy) for x, y in P], outline=INK)
    return P


def _gutter(img, poly, ox=0, oy=0, grow=4):
    """Paper-coloured margin around a panel that overlaps another one."""
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    out = []
    for x, y in poly:
        dx, dy = x - cx, y - cy
        L = math.hypot(dx, dy) or 1
        out.append((x + dx / L * grow * 1.42 + ox, y + dy / L * grow * 1.42 + oy))
    ImageDraw.Draw(img).polygon(out, fill=A.PAPER)


# ------------------------------------------------------------------ V1 MADAO
V1_HX, V1_HY = 214, 150        # Hasegawa's box (feet)
V1_SUN = (150, 116)            # setting sun (world)
CROW_PERCH = (V1_HX + 16, V1_HY - 18)
# the 'crow' SFX has two caws (0.00 s and 0.78 s): the first lands with the bird,
# the second is the 「阿呆～」 beat (camera snaps in, Hasegawa starts crying)
T_CROW_IN, T_CROW_LAND = 1.20, 1.75
T_CAW = T_CROW_LAND + 0.78
T_CRY = T_CAW + 0.12


def _v1_world(c, t):
    C.sky(c, "dusk", t, horizon=112, body=False)
    C.clouds(c, t, 0, "dusk", seed=6, count=6, y0=8, y1=70)
    A.sunset_sun(c, V1_SUN[0], V1_SUN[1], 24)
    A.far_bank(c, 113, col=(150, 84, 96))
    A.sunset_river(c, 113, 32, t, V1_SUN[0])
    A.river_bank(c, t, 144)
    A.reeds(c, t, 120, 320, 147, n=12, seed=1, h=(10, 20), dark=True)
    if t < T_CRY:
        draw_char(c, "hasegawa", V1_HX, V1_HY, "box", t, expr="sad")
    else:
        # 「阿呆～」 hits home: head sinks, the tears run from under the shades
        draw_char(c, "hasegawa", V1_HX, V1_HY, "box", t, expr="cry", head_dy=2, bob=0)
    # the crow: flies in from the upper right and perches on the box
    if t >= T_CROW_IN:
        if t < T_CROW_LAND:
            k = ease_out(seg(t, T_CROW_IN, T_CROW_LAND))
            x = lerp(V1_HX + 80, CROW_PERCH[0], k)
            y = lerp(V1_HY - 60, CROW_PERCH[1], k) + wave(t, 3, 2) * (1 - k)
            A.crow(c, x, y, t, "fly", facing=-1)
        else:
            caw = ((T_CROW_LAND <= t < T_CROW_LAND + 0.35) or (T_CAW <= t < T_CAW + 0.45)) \
                and step_frame(t, 8) % 2 == 0
            A.crow(c, CROW_PERCH[0], CROW_PERCH[1] - (1 if caw else 0), t, "perch", facing=-1, caw=caw)
    A.reeds(c, t, 96, 170, 172, n=7, seed=2, h=(28, 42), dark=True)
    A.reeds(c, t, 262, 330, 174, n=6, seed=3, h=(30, 46), dark=True)
    fx.sakura(c, t, count=22, seed=61, colors=((222, 120, 50), (190, 80, 40), (240, 180, 80)),
              wind=46.0, fall=14.0)


def _v1_cam(t):
    p = ease_in_out(seg(t, T1, T2))
    snap = ease_out(seg(t, T_CAW, T_CAW + 0.18))          # comedic snap-zoom on 「阿呆～」
    k = lerp(2.0, 2.25, p) + 0.5 * snap
    return k, lerp(196, 206, p) + 14 * snap, 127 + 2 * snap


def _v1_post(c, t, S):
    if T_CAW <= t < T2:
        x, y = S(CROW_PERCH[0] + 12, CROW_PERCH[1] - 21)
        sfx_text(c, int(x), int(y), "阿呆～", t, T_CAW, 0.62, color=(240, 240, 250), size=16, angle=8)
    if t >= T_CRY:
        # gloom lines over MADAO's head
        d = ImageDraw.Draw(c)
        hx, hy = S(V1_HX, V1_HY - 27)
        n = int(7 * ease_out(seg(t, T_CRY, T_CRY + 0.2)))
        for i in range(n):
            xx = int(hx) - 15 + i * 5
            d.line([(xx, int(hy) - 8), (xx, int(hy) - 1 + (i % 3) * 3)], fill=(84, 96, 170))


def draw_v1(img, t, ox=0):
    _paper(img, ox)
    panel(img, FULL, t, _v1_world, _v1_cam(t), ox=ox, post=_v1_post, focus=(192, 100))
    A.tag(img, 10 + ox, 10, "其一 MADAO")
    if ox == 0:
        name_card(img, t, 0.3, 2.15, "hasegawa", "长谷川泰三", "MADAO（彻底没用的大叔）")


# ------------------------------------------------------------------ V2 pachinko
V2_MX, V2_FLOOR = 192, 150
V2_GX, V2_HX = 158, 227        # Gintoki / Hasegawa stool x
V2_SEAT = 143                  # draw_char y for 'sit' on the stools


_ASH_CACHE = {}


def _ash_base(cid, facing, seed):
    """'Burnt-out white' (Ashita no Joe) version of the slumped character, cached:
    (RGBA array, anchor, erosion-threshold map, flake list)."""
    key = (cid, facing, seed)
    v = _ASH_CACHE.get(key)
    if v is not None:
        return v
    spr, ax, ay = render_sprite(cid, "sit", 0.0, expr="blink", facing=facing, arm_f=4, arm_b=-4,
                                head_dy=2, bob=0, lean=1)
    a = np.asarray(spr).astype(np.float32)
    lum = a[..., :3] @ np.array([0.299, 0.587, 0.114], np.float32)
    ink = lum < 70
    g = 188 + (lum - 70).clip(0, 185) / 185 * 64          # chalky whites
    for ch, add in ((0, 0), (1, 0), (2, 6)):
        a[..., ch] = np.where(ink, 62 + add, g + add)
    op = a[..., 3] > 0
    ys, xs = np.nonzero(op)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    r = rng("ashmap", seed)
    noise = np.array([r.random() for _ in range(a.shape[0] * a.shape[1])], np.float32).reshape(a.shape[:2])
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(np.float32)
    # the wind blows to the right: the right edge and the top go first
    q = (x1 - xx) / max(1, x1 - x0)
    rr = (yy - y0) / max(1, y1 - y0)
    thr = q * 0.75 + rr * 0.55 + noise * 0.2              # 0 .. 1.5
    flakes = []
    pts = np.argwhere(op)
    for i in range(70):
        py_, px_ = pts[r.randrange(len(pts))]
        flakes.append((px_ - ax, py_ - ay, float(thr[py_, px_]), tuple(int(v_) for v_ in a[py_, px_, :3]),
                       r.uniform(40, 90), r.uniform(4, 22), r.random()))
    v = (a, ax, ay, thr, flakes)
    _ASH_CACHE[key] = v
    return v


def _ash_prog(t):
    """Erosion level 0..1.52 (everything gone at the top)."""
    return 1.52 * seg(t, T_ASH, T_ASH_END) ** 1.3


def _ash_char(c, cid, x, y, t, facing, seed):
    """White 'burnt-out' character; crumbles into ash blown to the right after T_ASH."""
    a, ax, ay, thr, flakes = _ash_base(cid, facing, seed)
    prog = _ash_prog(t)
    if prog > 0:
        a = a.copy()
        a[..., 3] = np.where(thr < prog, 0, a[..., 3])
    out = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")
    c.paste(out, (int(x - ax), int(y - ay)), out)
    if t < T_ASH:
        return
    # ash flakes break off exactly where (and when) the erosion front passes
    d = ImageDraw.Draw(c)
    span = T_ASH_END - T_ASH
    for i, (fx_, fy_, th, col, vx, vy, ph) in enumerate(flakes):
        ts = T_ASH + span * (th / 1.52) ** (1 / 1.3)
        dt = t - ts
        if dt < 0 or dt > 0.9:
            continue
        px = x + fx_ + dt * vx + dt * dt * 30
        py = y + fy_ - dt * vy + wave(t, 2, 1.5, ph)
        d.point((px, py), fill=col)
        if i % 3 == 0 and dt < 0.5:
            d.point((px + 1, py), fill=col)


def _reel_v(t):
    """Third reel position (float digit, decreasing -> the strip scrolls down):
    fast spin, slows down, lands PERFECTLY on 7 ... creeps ... clunks onto 6."""
    if t >= T_MISS:
        return 6.0
    if t >= T_SEVEN:
        return 7.0 - 0.2 * ease_in(seg(t, T_SEVEN, T_MISS))
    if t < T_REACH:
        return 16.0 + 20.0 * (T_REACH - t)
    u = (t - T_REACH) / (T_SEVEN - T_REACH)
    return 7.0 + 9.0 * (1 - u) ** 2.2


def _v2_world(c, t):
    grey = t >= T_GREY
    A.parlor_bg(c, t, lit=not grey)
    A.stool(c, V2_GX, V2_SEAT - 2, V2_FLOOR)
    A.stool(c, V2_HX, V2_SEAT - 2, V2_FLOOR)
    v = _reel_v(t)
    reels = ("7", "7", "0123456789"[int(round(v)) % 10])
    if not grey:
        if t < T_SEVEN:
            # bouncing, cheering on the stools
            e1 = "shout" if step_frame(t, 6) % 2 == 0 else "happy"
            e2 = "shout" if step_frame(t + 0.2, 6) % 2 == 0 else "happy"
            draw_char(c, "gintoki", V2_GX, V2_SEAT, "cheer", t, legs="sit", expr=e1, shadow=False)
            draw_char(c, "hasegawa", V2_HX, V2_SEAT, "cheer", t + 0.1, legs="sit", expr=e2,
                      facing=-1, shadow=False)
        elif t < T_MISS:
            # the 7 is IN! ... frozen, leaning in, holding their breath
            draw_char(c, "gintoki", V2_GX + 1, V2_SEAT, "idle", t, legs="sit", expr="shock", arm_f=100,
                      arm_b=90, lean=2, head_dx=1, shadow=False)
            draw_char(c, "hasegawa", V2_HX - 1, V2_SEAT, "idle", t, legs="sit", expr="shock", arm_f=100,
                      arm_b=90, lean=2, head_dx=1, facing=-1, shadow=False)
        else:
            draw_char(c, "gintoki", V2_GX, V2_SEAT, "shock", t, p=0.1, legs="sit", shadow=False)
            draw_char(c, "hasegawa", V2_HX, V2_SEAT, "shock", t, p=0.1, legs="sit", facing=-1, shadow=False)
        A.draw_machine(c, V2_MX, V2_FLOOR, t, reels=reels, lit=True, lamp=1.0 if t >= T_REACH else 0.0)
    else:
        A.draw_machine(c, V2_MX, V2_FLOOR, t, reels=reels, lit=False, balls=False, tray=0.0)
        fx.grayscale(c, 1.0)
        fx.grade(c, mul=(0.62, 0.62, 0.7))
        _ash_char(c, "gintoki", V2_GX, V2_SEAT, t, 1, 1)
        _ash_char(c, "hasegawa", V2_HX, V2_SEAT, t, -1, 2)
        # one lonely ball rolling away across the carpet
        bx = lerp(V2_MX + 10, V2_MX + 110, seg(t, T_GREY + 0.2, T3))
        pset(c, bx, V2_FLOOR + 3, (220, 220, 226))
        pset(c, bx + 1, V2_FLOOR + 3, (160, 160, 170))


def _v2_cam(t):
    if t < T_SEVEN:
        k = lerp(1.85, 2.1, ease_out(seg(t, T2, T_SEVEN)))
        return k, V2_MX, 116
    if t < T_MISS:                                    # hold-your-breath push-in
        k = lerp(2.1, 2.3, ease_out(seg(t, T_SEVEN, T_MISS)))
        return k, V2_MX, 114
    k = lerp(2.6, 2.2, ease_out(seg(t, T_MISS, T3)))
    return k, V2_MX, 118


def _v2_post(c, t, S):
    if t < T_MISS:
        x, y = S(V2_HX + 22, V2_SEAT - 14)
        sfx_text(c, int(x), int(y), "来了!!", t, 3.30, 0.7, size=20, angle=10)
        x, y = S(V2_GX - 12, V2_SEAT - 38)
        sfx_text(c, int(x), int(y), "来了!!", t, 3.62, 0.7, size=20, angle=-10)
        if 3.85 <= t < T_SEVEN:
            fx.speed_lines(c, t, *map(int, S(V2_MX, 104)), color=(255, 240, 200), count=26, inner=90, seed=3)
        if t >= T_SEVEN:
            x, y = S(V2_GX - 6, V2_SEAT - 45)
            sfx_text(c, int(x), int(y), "！？", t, T_SEVEN, T_MISS - T_SEVEN + 0.01, color=(255, 255, 255),
                     size=20, angle=-6, shake=0)
            x, y = S(V2_HX - 3, V2_SEAT - 18)          # MADAO's shades flash
            fx.sparkle(c, int(x), int(y), t, T_SEVEN + 0.02, size=6)
    elif t < T_GREY:
        fx.flash(c, 0.6)
    else:
        d = ImageDraw.Draw(c)
        # vertical gloom lines over both (gone once the ash blows away)
        n = int(9 * (1 - seg(t, T_ASH, T_ASH + 0.3)))
        for cx_w in (V2_GX, V2_HX):
            x, y = S(cx_w, V2_SEAT - 31)
            for i in range(n):
                xx = int(x) - 16 + i * 4
                d.line([(xx, int(y) - 6), (xx, int(y) + 8 + (i % 3) * 3)], fill=(70, 70, 96))
        if t >= T_ASH - 0.15:
            fx.motion_lines(c, t, color=(190, 190, 198), count=14, direction=1, seed=4,
                            y0=40, y1=170, speed=520)


def _v2_inset_world(c, t):
    v = _reel_v(t)
    if t < T_MISS:
        reels, k, lit = ("7", "7", v), 0, True
    else:
        reels, k, lit = ("7", "7", "6"), seg(t, T_MISS, T_MISS + 0.18), t < T_GREY
    A.lcd_closeup(c, 192, 108, t, reels, k, lit=lit, flash=0.7 if T_MISS <= t < T_MISS + 0.06 else 0,
                  hot=T_SEVEN <= t < T_MISS)
    if not lit:
        fx.grayscale(c, 1.0)


V2_INSET = [(238, 12), (372, 12), (372, 84), (222, 84)]


def draw_v2(img, t, ox=0):
    _paper(img, ox)
    panel(img, FULL, t, _v2_world, _v2_cam(t), ox=ox, post=_v2_post, focus=(192, 100))
    if t >= T_REACH:
        _gutter(img, V2_INSET, ox, grow=3) if t >= T_REACH + 0.12 else None
        panel(img, V2_INSET, t, _v2_inset_world, (1.0, 192, 108), ox=ox, enter=("pop", T_REACH, 0.2))
    A.tag(img, 10 + ox, 10, "其二 小钢珠")
    if t >= T_STAMP:
        A.stamp(img, 86 + ox, 56, t, T_STAMP, sub="")
        if t >= T_STAMP + 0.3:
            A.caption_box(img, 56 + ox, 98, "所持金：0円", size=12, anchor="mm")


# ------------------------------------------------------------------ V3 Monday = Jump day
from chars.gintoki import _head as _gin_head, HEAD_PAL as _GIN_PAL  # noqa: E402  (read-only reuse)

_SPARKLE_HEAD = None


def _sparkle_head():
    """Gintoki's head with huge shoujo-manga sparkling eyes + blush (rows 10..15)."""
    global _SPARKLE_HEAD
    if _SPARKLE_HEAD is None:
        art = _gin_head(r11="odHSSoooSSSoooSSHo",
                        r12=".oHSSwwESSSwwESSo.",
                        r13=".ohSSEEwSSSEEwSso.",
                        r14="..osbSSSSommoSbSo.",
                        r15="...oosSSSSooSsoo..")
        _SPARKLE_HEAD = ascii_sprite(art, _GIN_PAL)
    return _SPARKLE_HEAD


V3_GX, V3_GY = 176, 150            # Gintoki kneeling (world)
V3_JX, V3_JY = V3_GX + 17, V3_GY - 31   # the holy JUMP floats here (world)
V3_CAM_C = (V3_GX + 9, V3_GY - 20)
V3_FOCUS = (262, 104)
T_JUMP_IN = T_SPLIT + 0.08         # the JUMP descends from the heavens
T_STARS = T_SPLIT + 0.45           # star eyes pop
T_TEARS = T_SPLIT + 0.75           # tears of joy


def _v3_cal_world(c, t):
    A.wall_bg(c)
    A.calendar(c, 192, 58, t, T_TEAR)
    if T_TEAR - 0.05 <= t < T_TEAR + 0.3:
        fx.motion_lines(c, t, color=(255, 255, 255), count=10, direction=-1, seed=7, y0=40, y1=120, speed=700)


def _v3_cal_post(c, t, S):
    if t >= T_TEAR + 0.1:
        x, y = S(192 + 26, 58 + 60)
        fx.sparkle(c, int(x), int(y), t, T_TEAR + 0.1, size=7)
        x, y = S(192 - 28, 58 + 40)
        fx.sparkle(c, int(x), int(y), t, T_TEAR + 0.25, size=5)
    if t >= T_TEAR + 0.6:
        for i, (wx, wy) in enumerate(((192 + 30, 58 + 52), (192 - 30, 58 + 66), (192 + 24, 58 + 24))):
            x, y = S(wx, wy)
            sz = int(5 * max(0.0, math.sin((t * 1.4 + i * 0.37) * 2 * math.pi)))
            A.twinkle(c, int(x), int(y), sz, (255, 220, 120))
    if T_TEAR <= t < T_TEAR + 0.6:
        x, y = S(240, 70)
        sfx_text(c, int(x), int(y), "唰!", t, T_TEAR, 0.6, size=20, angle=12)


def _v3_bob(t):
    return -1 if step_frame(t, 4, 4) in (1, 2) else 0


def _v3_jit(t):
    """Trembling with joy once the stars are in his eyes (1 world px, 10 fps)."""
    return (0, 1)[step_frame(t, 10, 2)] if t >= T_STARS else 0


def _v3_jump_screen(t, S):
    x, y = S(V3_JX, V3_JY)
    drop = 1 - ease_out(seg(t, T_JUMP_IN, T_JUMP_IN + 0.45))
    return x, y - 110 * drop + 2 * math.sin(t * 3.2)


def _v3_gin_world(c, t):
    A.shoujo_bg(c, t, V3_JX, V3_JY)
    # holy light pouring down from above onto the JUMP (and onto the believer)
    open_k = ease_out(seg(t, T_JUMP_IN, T_JUMP_IN + 0.35))
    if open_k > 0:
        wbot = 30 * open_k
        A.beams(c, [((V3_JX - 5, 0), (V3_JX - 6 - wbot, V3_GY + 4), (V3_JX + 4 + wbot, V3_GY + 4),
                     (255, 232, 140)),
                    ((V3_JX + 5, 0), (V3_JX - 2 - wbot * 0.5, V3_GY + 4), (V3_JX + 8 + wbot * 0.5, V3_GY + 4),
                     (255, 246, 190))], level=0.45)
    gx = V3_GX + _v3_jit(t)
    bob = _v3_bob(t)
    reach = ease_out(seg(t, T_JUMP_IN + 0.15, T_STARS))
    grab = (0, 8, 14, 8)[step_frame(t, 8, 4)] if t >= T_STARS else 0      # grabby hands
    draw_char(c, "gintoki", gx, V3_GY, "kneel", t, legs="kneel", arm_f=lerp(20, 124, reach) + grab,
              arm_b=lerp(10, 150, reach), expr="shock" if t < T_STARS else "happy", bob=bob, head_dy=0,
              lean=1 if t >= T_STARS else 0, shadow=False)
    if t >= T_STARS:
        patch = _sparkle_head().crop((3, 11, 16, 16))
        c.paste(patch, (gx - 6 + (1 if t >= T_STARS else 0), V3_GY - 17 + bob), patch)


def _v3_gin_post(c, t, S):
    bob = _v3_bob(t)
    gx = V3_GX + _v3_jit(t) + 1
    jx, jy = _v3_jump_screen(t, S)
    # radiance around the JUMP
    if t >= T_JUMP_IN + 0.3:
        for i in range(6):
            a = t * 1.3 + i * math.pi / 3
            rr = 30 + 3 * math.sin(t * 5 + i)
            s = int(2 + 3 * max(0.0, math.sin((t * 1.9 + i * 0.29) * 2 * math.pi)))
            A.twinkle(c, int(jx + math.cos(a) * rr), int(jy + math.sin(a) * rr * 0.8), s, (255, 250, 210))
    A.jump_mag(c, jx, jy, t)
    if t >= T_STARS:
        # kira-kira star eyes (pop in bigger, then pulse)
        pop = 1 - ease_out(seg(t, T_STARS, T_STARS + 0.15))
        for i, wx in enumerate((gx - 2.5, gx + 3.5)):
            x, y = S(wx, V3_GY - 15.5 + bob)
            pulse = 1 if step_frame(t, 6, 2) else 0
            A.star(c, x, y, 7 + pulse + 6 * pop, rot=math.sin(t * 3 + i) * 0.25)
    # tears of joy squirting sideways
    for side, wx in ((-1, gx - 5.5), (1, gx + 6.5)):
        x, y = S(wx, V3_GY - 14 + bob)
        A.tears_spray(c, x, y, t, T_TEARS, side, seed=int(side > 0))
    for i in range(6):
        r = rng("v3spk", i)
        x = r.uniform(150, W - 20)
        y = r.uniform(40, H - 50)
        s = int(3 * max(0.0, math.sin((t * r.uniform(1, 2) + r.random()) * 2 * math.pi)))
        A.twinkle(c, int(x), int(y), s, (255, 255, 230))
    if T_STARS <= t < T_STARS + 0.7:
        x, y = S(gx - 17, V3_GY - 30)
        sfx_text(c, int(x), int(y), "闪!", t, T_STARS, 0.7, size=16, angle=-12, color=(255, 240, 120))


def _v3_cam(t):
    k = lerp(2.9, 3.1, ease_in_out(seg(t, T_SPLIT, T4)))
    return k, V3_CAM_C[0], V3_CAM_C[1]


V3_CAL_FULL = FULL
V3_CAL_SPLIT = [(6, 6), (152, 6), (134, 210), (6, 210)]
V3_GIN = [(158, 6), (378, 6), (378, 210), (140, 210)]


def draw_v3(img, t, ox=0):
    _paper(img, ox)
    k = ease_out(seg(t, T_SPLIT, T_SPLIT + 0.28))
    poly = [(lerp(a[0], b[0], k), lerp(a[1], b[1], k)) for a, b in zip(V3_CAL_FULL, V3_CAL_SPLIT)]
    kc = lerp(1.6, 1.3, k)
    fxs = sum(p[0] for p in poly) / 4
    panel(img, poly, t, _v3_cal_world, (kc, 192, 99), ox=ox, post=_v3_cal_post, focus=(fxs, 102))
    if t >= T_SPLIT:
        panel(img, V3_GIN, t, _v3_gin_world, _v3_cam(t), ox=ox,
              enter=("right", T_SPLIT, 0.28), post=_v3_gin_post, focus=V3_FOCUS)
        if t >= T_SPLIT + 0.3:
            A.caption_box(img, 262 + ox, 26, "周一＝Jump发售日", size=16, anchor="mm")
    A.tag(img, 10 + ox, 10, "其三 周一")


# ------------------------------------------------------------------ V4 Otsu concert
V4_OX, V4_SX, V4_SY = 150, 264, 150     # Otsu x (stage), Shinpachi feet
T_SPLIT4 = 9.75
V4_OTSU_SPLIT = [(6, 6), (246, 6), (212, 210), (6, 210)]
V4_SHIN = [(252, 6), (378, 6), (378, 210), (218, 210)]


def _v4_world(c, t):
    A.stage_bg(c, t)
    sw = math.sin(t * 1.6)
    A.beams(c, [((20, 0), (V4_OX - 26 + sw * 10, A.STAGE_Y + 2), (V4_OX + 18 + sw * 10, A.STAGE_Y + 2),
                 (255, 200, 240)),
                ((364, 0), (V4_OX - 14 - sw * 12, A.STAGE_Y + 2), (V4_OX + 30 - sw * 12, A.STAGE_Y + 2),
                 (200, 230, 255)),
                ((192, 0), (60 + 80 * math.sin(t * 2.1), H), (100 + 80 * math.sin(t * 2.1), H), (255, 120, 200)),
                ((192, 0), (290 - 80 * math.sin(t * 1.7), H), (330 - 80 * math.sin(t * 1.7), H), (120, 220, 255))],
            level=0.3)
    draw_char(c, "otsu", V4_OX, A.STAGE_Y, "sing", t)
    A.crowd(c, t, A.STAGE_Y + 30, 16, 4, seed=1)
    A.crowd(c, t, A.STAGE_Y + 42, 12, 5, seed=2, skip=(V4_SX - 18, V4_SX + 16))
    draw_char(c, "shinpachi", V4_SX, V4_SY, "otaku_cheer", t, facing=-1)
    A.crowd(c, t, 188, 9, 7, seed=3, skip=(V4_SX - 26, V4_SX + 26))
    fx.sakura(c, t, count=34, seed=44, colors=((255, 90, 160), (90, 200, 255), (255, 230, 90), (140, 255, 140)),
              wind=8.0, fall=26.0, area=(0, 0, W, 170))


_NOTE_COLS = ((255, 140, 205), (130, 220, 255), (255, 232, 110), (170, 255, 150))


def _v4_otsu_post(c, t, S):
    for i, (wx, wy) in enumerate(((V4_OX - 20, 86), (V4_OX + 22, 80), (V4_OX - 8, 70))):
        x, y = S(wx, wy)
        s = int(4 * max(0.0, math.sin((t * 1.3 + i * 0.33) * 2 * math.pi)))
        A.twinkle(c, int(x), int(y), s, (255, 250, 200))
    # music notes floating out of her mic
    mx, my = S(V4_OX + 8, A.STAGE_Y - 26)
    for i in range(5):
        ph = ((t - T4) * 0.75 + i / 5) % 1.0
        if t - T4 < ph / 0.75:
            continue
        x = mx + 6 + ph * 34 + math.sin(ph * 9 + i) * 5
        y = my - 4 - ph * 58
        if ph < 0.85:
            A.note(c, x, y, _NOTE_COLS[i % 4], double=i % 2 == 1)


V4_LOVE = [(10.45, "L", 0), (10.65, "O", 1), (10.85, "V", 2), (11.05, "E", 3)]


def _v4_shin_post(c, t, S):
    # hearts bubbling up from the fan-club captain
    for i in range(4):
        ph = ((t - T_SPLIT4) * 0.9 + i * 0.25) % 1.0
        if t < T_SPLIT4 + i * 0.2:
            continue
        x, y = S(V4_SX - 12 + i * 7 + math.sin(ph * 6 + i) * 3, V4_SY - 30 - ph * 26)
        A.heart(c, int(x), int(y), (255, 90, 150) if i % 2 else (255, 150, 190))
    # the fan-club chant, one letter per beat: L・O・V・E
    for t0, ch, i in V4_LOVE:
        if t >= t0:
            beat = 1 if step_frame(t, 4.4, 2) == i % 2 else 0
            sfx_text(c, 360, 90 + i * 21 - beat, ch, t, t0, T5 + 0.2 - t0, color=(240, 70, 150),
                     outline=(255, 255, 255), size=20, angle=(-8, 6, -6, 8)[i], shake=0)


def draw_v4(img, t, ox=0):
    _paper(img, ox)
    k = ease_out(seg(t, T_SPLIT4, T_SPLIT4 + 0.3))
    poly = [(lerp(a[0], b[0], k), lerp(a[1], b[1], k)) for a, b in zip(FULL, V4_OTSU_SPLIT)]
    fxs = lerp(192, 118, k)
    ko = lerp(2.2, 2.0, k)
    panel(img, poly, t, _v4_world, (ko, V4_OX + 2, 96 + wave(t, 0.4, 1.0)), ox=ox, post=_v4_otsu_post,
          focus=(fxs, 104))
    if t >= T_SPLIT4:
        panel(img, V4_SHIN, t, _v4_world, (2.2, V4_SX - 2, 136), ox=ox, enter=("up", T_SPLIT4, 0.3),
              post=_v4_shin_post, focus=(308, 132))
    A.tag(img, 10 + ox, 10, "其四 偶像")
    if ox == 0:
        name_card(img, t, 9.15, 2.3, "otsu", "寺门通", "超人气偶像｜新八是亲卫队队长")


# ------------------------------------------------------------------ V5 Kagura & Sadaharu
V5_DX, V5_DY = 160, 164        # Sadaharu feet anchor
V5_KX = 156                    # Kagura x (sitting on his back)
V5_KY_SLEEP = 147              # her feet y while he lies asleep
V5_KY_STAND = 135              # ... once he is standing
V5_KY_SKY = 30                 # launched: far above the frame
T_JOLT = T_POP + 0.05          # Sadaharu jolts awake -> Kagura is catapulted
T_GONE = T_JOLT + 0.18         # she has left the frame
T_FALL = 13.86                 # she drops back in ...
T_LAND = 14.02                 # ... lands on his back, STILL chewing


def _v5_kagura_y(t):
    if t < T_JOLT:
        return V5_KY_SLEEP
    if t < T_FALL:
        return lerp(V5_KY_SLEEP, V5_KY_SKY, ease_out(seg(t, T_JOLT, T_GONE)))
    if t < T_LAND:
        return lerp(V5_KY_SKY, V5_KY_STAND, ease_in(seg(t, T_FALL, T_LAND)))
    return V5_KY_STAND + (2 if t < T_LAND + 0.08 else 0)


def _v5_world(c, t):
    Y.office(c, t, "dusk")
    nx, ny = V5_DX + 20, V5_DY - 11
    if t < T_JOLT:
        draw_char(c, "sadaharu", V5_DX, V5_DY, "sleep", t)
    elif t < T_JOLT + 0.3:
        draw_char(c, "sadaharu", V5_DX, V5_DY, "shock", t, p=seg(t, T_JOLT, T_JOLT + 0.3))
    else:
        squash = 2 if T_LAND <= t < T_LAND + 0.1 else 0
        e = "hurt" if T_LAND <= t < T_LAND + 0.25 else ("blink" if (t % 1.3) < 0.12 else "normal")
        draw_char(c, "sadaharu", V5_DX, V5_DY + squash, "idle", t, expr=e)
    # snot bubble from his nose: breathes bigger and bigger ... pop
    if t < T_POP:
        g = seg(t, T5 + 0.3, T_POP)
        r = 1 + 6.5 * g + (0.6 + g) * math.sin(t * 5.0)
        if r > 1.2:
            d = ImageDraw.Draw(c)
            bx, by = nx + r * 0.9, ny + 1 - r * 0.2
            d.ellipse([bx - r, by - r, bx + r, by + r], fill=(196, 226, 250), outline=(90, 130, 170))
            pset(c, bx - r * 0.45, by - r * 0.45, (255, 255, 255))
    else:
        fx.burst(c, t, T_POP, nx + 6, ny, n=16, colors=((210, 235, 255), (255, 255, 255), (150, 200, 240)),
                 speed=(30, 70), gravity=90, life=0.4, seed=5)
    ky = _v5_kagura_y(t)
    if T_JOLT <= t < T_GONE + 0.05 or T_FALL <= t < T_LAND:
        # vertical speed streaks along her flight path
        d = ImageDraw.Draw(c)
        for i in range(5):
            xx = V5_KX - 8 + i * 4
            top = ky + (4 if t < T_FALL else -30)
            d.line([(xx, top), (xx, top + 14 + (i % 2) * 6)], fill=(255, 250, 230))
    draw_char(c, "kagura", V5_KX, ky, "sukonbu", t, legs="sit", shadow=False)
    if t >= T_LAND:
        fx.smoke_puff(c, t, T_LAND, V5_DX - 16, V5_DY, size=7, seed=51)
        fx.smoke_puff(c, t, T_LAND, V5_DX + 18, V5_DY, size=7, seed=52)


def _v5_cam(t):
    k0 = lerp(2.4, 2.8, ease_in_out(seg(t, T5, T_POP)))
    cx0 = lerp(162, 168, seg(t, T5, T_POP))
    j = ease_out(seg(t, T_JOLT, T_JOLT + 0.14))       # snap zoom-out when he jumps up
    return lerp(k0, 2.1, j), lerp(cx0, 166, j), lerp(146, 131, j)


def _v5_post(c, t, S):
    if T_POP <= t < T_POP + 0.6:
        x, y = S(V5_DX + 30, V5_DY - 24)
        sfx_text(c, int(x), int(y), "啪!", t, T_POP, 0.6, size=24, angle=-10)
    if T_JOLT <= t < T_JOLT + 0.5:
        x, y = S(V5_KX - 22, V5_KY_SLEEP - 20)
        sfx_text(c, int(x), int(y), "嘣!", t, T_JOLT, 0.5, size=22, angle=10, color=(255, 255, 255))
    if T_GONE + 0.05 <= t < T_LAND:
        x, y = S(V5_DX + 22, V5_DY - 50)
        sfx_text(c, int(x), int(y), "？", t, T_GONE + 0.05, T_LAND - T_GONE - 0.05, size=20, angle=0,
                 color=(255, 255, 255), shake=0)
    if t >= T_LAND + 0.1:
        x, y = S(V5_KX - 26, V5_KY_STAND - 18)
        sfx_text(c, int(x), int(y), "嚼嚼", t, T_LAND + 0.1, T6 + 0.3 - T_LAND, size=16, angle=-6,
                 color=(255, 255, 255), shake=0)


def draw_v5(img, t, ox=0):
    _paper(img, ox)
    panel(img, FULL, t, _v5_world, _v5_cam(t), ox=ox, post=_v5_post, focus=(192, 104))
    A.tag(img, 10 + ox, 10, "其五 醋昆布")


# ------------------------------------------------------------------ V6 Kondo under the floor
V6_TOP = [(6, 6), (W - 6, 6), (W - 6, 90), (6, 98)]
V6_BOT = [(6, 104), (W - 6, 96), (W - 6, H - 6), (6, H - 6)]
V6_OX, V6_OY = 170, 146        # Otae feet (top panel world)
V6_TCAM = (2.0, 176, 124)
V6_TFOCUS = (192, 52)
STAB_SX = V6_TFOCUS[0] + (V6_OX + 9 - V6_TCAM[1]) * V6_TCAM[0]   # screen x of the blade
V6_KX, V6_KY = 150, A.DIRT_Y   # Kondo kneeling (bottom panel world)
_KB = 2.4
V6_BCAM = (_KB, V6_KX + 9.5 - (STAB_SX - 5 - 192) / _KB, 117.5)
V6_BFOCUS = (192, 136)
STAB_BX = V6_BCAM[1] + (STAB_SX - V6_BFOCUS[0]) / _KB             # blade x in bottom world


def _top_to_screen(wx, wy, ox=0):
    k, cx, cy = V6_TCAM
    return V6_TFOCUS[0] + (wx - cx) * k + ox, V6_TFOCUS[1] + (wy - cy) * k


def _bot_to_screen(wx, wy, ox=0):
    k, cx, cy = V6_BCAM
    return V6_BFOCUS[0] + (wx - cx) * k + ox, V6_BFOCUS[1] + (wy - cy) * k


def _v6_top_world(c, t):
    tod = C.indoor("day")
    C.room_wall(c, 0, tod, 0, 136, "fusuma")
    C.tatami(c, 136, 0, tod)
    A.teacup(c, V6_OX + 14, V6_OY, t, steam=t < T_RISE)
    floor = c.crop((0, V6_OY + 1, W, H))
    if t < T_AURA:
        draw_char(c, "otae", V6_OX, V6_OY, "sit", t)
    elif t < T_RISE:
        draw_char(c, "otae", V6_OX, V6_OY, "sit", t, expr="dark_smile")
    elif t < T_STAB:
        p = 0.12 + 0.2 * seg(t, T_RISE, T_STAB)
        draw_char(c, "otae", V6_OX, V6_OY, "attack", t, p=p, expr="dark_smile")
    else:
        draw_char(c, "otae", V6_OX, V6_OY, "thrust", t, p=1.0, weapon=-90, arm_f=30, arm_b=20,
                  lean=3, expr="dark_smile")
        c.paste(floor, (0, V6_OY + 1))          # the blade disappears into the floor
        sx = V6_OX + 9
        fx.burst(c, t, T_STAB, sx, V6_OY + 1, n=10, colors=((200, 180, 110), (150, 120, 70)),
                 speed=(20, 60), gravity=200, life=0.5, seed=8, spread=(200, 340))
        pset(c, sx - 1, V6_OY + 1, INK)
        pset(c, sx + 1, V6_OY + 1, INK)


def _v6_top_post(c, t, S):
    if T_AURA <= t < T_STAB:
        for i in range(3):
            x, y = S(V6_OX + 16 + i * 9, V6_OY - 34 + i * 6)
            sfx_text(c, int(x), int(y), "ゴ", t, T_AURA + i * 0.12, T_STAB - T_AURA - i * 0.12,
                     color=(170, 110, 210), outline=(40, 16, 50), size=16, angle=-8, shake=1)


def _v6_bot_world(c, t):
    A.crawlspace(c, t, gap_xs=(STAB_BX - 1, STAB_BX + 44, STAB_BX - 70, STAB_BX + 96))
    if t < T_STAB:
        draw_char(c, "kondo", V6_KX, V6_KY, "stalk", t, bush=False, arm_f=40, arm_b=160)
    else:
        # frozen stiff, leaning away from the blade, trembling
        jx = int(math.sin(t * 50))
        draw_char(c, "kondo", V6_KX, V6_KY, "kneel", t, legs="kneel", arm_f=14, arm_b=-18, lean=-1,
                  head_dx=jx, head_dy=0, expr="shock")
        fx.burst(c, t, T_STAB, STAB_BX, A.JOIST_Y, n=12, colors=((150, 110, 70), (96, 64, 44)),
                 speed=(20, 60), gravity=220, life=0.6, seed=9, spread=(20, 160))


def _v6_bot_post(c, t, S):
    if t >= T_STAB:
        d = ImageDraw.Draw(c)
        # face drains: blue vertical lines on the forehead, popping eyes, sweat drops
        jx = int(math.sin(t * 50))
        hx, hy = S(V6_KX + 0.5 + jx, V6_KY - 21.5)
        for i in range(6):
            xx = int(hx) - 14 + i * 5
            d.line([(xx, int(hy)), (xx, int(hy) + 5 + (i % 2) * 3)], fill=(90, 110, 210))
        for i, ex in enumerate((V6_KX - 3 + jx, V6_KX + 4.5 + jx)):
            x, y = S(ex, V6_KY - 17.5)
            x, y = int(x), int(y)
            d.ellipse([x - 3, y - 6, x + 3, y + 5], fill=(255, 255, 255), outline=INK)
            px = x + 1 if i == 0 else x - 2          # cross-eyed, staring at the blade tip
            d.rectangle([px, y - 1, px + 1, y + 1], fill=INK)
        # jaw drop
        mx, my = S(V6_KX + 1 + jx, V6_KY - 15)
        mx, my = int(mx), int(my)
        d.ellipse([mx - 3, my - 2, mx + 3, my + 6], fill=(60, 16, 30), outline=INK)
        d.rectangle([mx - 1, my + 3, mx + 1, my + 4], fill=(220, 80, 100))
        A.sweat(c, int(hx) - 26, int(hy) + 2, 2)
        A.sweat(c, int(hx) - 30, int(hy) + 18, 1)
        if t < T_STAB + 0.8:
            fx.speed_lines(c, t, int(hx), int(hy) + 10, color=(255, 255, 255), count=30, inner=46, seed=11)
    if T_STAB <= t < T_STAB + 0.7:
        x, y = S(STAB_BX + 22, V6_KY - 24)
        sfx_text(c, int(x), int(y), "咚!!", t, T_STAB, 0.48, size=22, angle=-12)


def draw_v6(img, t, ox=0):
    _paper(img, ox)
    panel(img, V6_TOP, t, _v6_top_world, V6_TCAM, ox=ox, post=_v6_top_post, focus=V6_TFOCUS)
    panel(img, V6_BOT, t, _v6_bot_world, V6_BCAM, ox=ox, post=_v6_bot_post, focus=V6_BFOCUS)
    if t >= T_STAB:
        # the naginata shaft breaks through the gutter between the two panels
        sx, sy = _top_to_screen(V6_OX + 9, V6_OY + 2, ox)
        k = ease_out(seg(t, T_STAB, T_STAB + 0.06))
        _, tip_y = _bot_to_screen(0, V6_KY - 17)
        tip = (sx, lerp(sy, tip_y, k))
        A.naginata_line(img, (sx, sy), tip, blade=18)
    A.tag(img, 10 + ox, 10, "其六 跟踪狂")
    if t >= T_CROW6_IN:
        # the awkward-silence crow flaps across the page (callback to 其一)
        def crow_pos(tt):
            k = seg(tt, T_CROW6_IN, T_CROW6_IN + 1.1)
            return lerp(W + 24, 20, k) + ox, 22 + wave(tt, 1.6, 3)
        cx_, cy_ = crow_pos(t)
        caws = ((T_CROW6_CAW, 16), (T_CROW6_CAW + 0.78, 14))
        caw = any(tc <= t < tc + 0.3 for tc, _ in caws) and step_frame(t, 8) % 2 == 0
        A.crow_big(img, cx_, cy_, t, caw=caw)
        for tc, sz in caws:
            if tc <= t < tc + 0.6:
                qx, qy = crow_pos(tc)               # the call stays where it was cawed
                sfx_text(img, int(qx + 6), int(qy + 20), "阿呆～", t, tc, 0.6, color=(240, 240, 250),
                         size=sz, angle=6)
    if t >= T_CAP:
        p = t - T_CAP
        s = lerp(1.8, 1.0, ease_out(clamp(p / 0.14)))
        spr = _caption_sprite()
        if s != 1.0:
            spr = spr.resize((int(spr.width * s), int(spr.height * s)), Image.NEAREST)
        img.paste(spr, (int(300 + ox - spr.width / 2), int(100 - spr.height / 2)), spr)


T_CROW6_IN = 16.80
T_CROW6_CAW = 16.95            # 'crow' SFX caws at +0.00 and +0.78


_CAP = None


def _caption_sprite():
    global _CAP
    if _CAP is None:
        txt = text_sprite("※以上皆为日常", (255, 255, 255), 16, "pixel")
        w, h = txt.width + 18, txt.height + 12
        im = Image.new("RGBA", (w + 4, h + 4), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle([3, 3, w + 3, h + 3], fill=(0, 0, 0, 120))
        d.rectangle([0, 0, w - 1, h - 1], fill=INK, outline=(255, 255, 255))
        d.rectangle([2, 2, w - 3, h - 3], outline=(90, 80, 110))
        im.alpha_composite(txt, (9, 6))
        _CAP = im.rotate(-3, resample=Image.NEAREST, expand=True)
    return _CAP


# ------------------------------------------------------------------ scene
PAGES = [(T1, draw_v1), (T2, draw_v2), (T3, draw_v3), (T4, draw_v4), (T5, draw_v5), (T6, draw_v6)]


class Daily(Scene):
    id = "s06"
    title = "日常"
    duration = TEND
    music = "comedy"
    music_vol = 0.5
    subs = [
        (0.80, 2.95, "hasegawa", "纸箱……其实还挺暖和的。"),
        (3.00, 4.76, "gintoki", "来了来了！！"),
        (6.55, 8.70, "gintoki", "Jump是男人的圣经啊！"),
        (10.00, 11.72, "shinpachi", "通酱～！！"),
        (12.00, 14.01, "kagura", "醋昆布就是正义阿鲁！"),
        (14.50, 16.66, "kondo", "阿妙小姐……今天也好美。"),
    ]

    def render(self, img, t):
        idx = 0
        for i, (t0, _) in enumerate(PAGES):
            if t >= t0:
                idx = i
        t0, fn = PAGES[idx]
        if idx > 0 and t < t0 + TR:
            PAGES[idx - 1][1](img, t, 0)
            p = seg(t, t0, t0 + TR)
            fn(img, t, int(round((W + 8) * (1 - ease_out(p)))))
        else:
            fn(img, t, 0)
        # page shakes on the big beats
        dx, dy = fx.shake_offset(t, T_MISS, 0.25, 3, seed=1)
        ex, ey = fx.shake_offset(t, T_STAMP, 0.3, 4, seed=2)
        gx, gy = fx.shake_offset(t, T_STAB, 0.45, 5, seed=3)
        hx, hy = fx.shake_offset(t, T_CAP, 0.2, 2, seed=4)
        lx, ly = fx.shake_offset(t, T_LAND, 0.2, 3, seed=5)
        fx.shift(img, dx + ex + gx + hx + lx, dy + ey + gy + hy + ly, fill=A.PAPER)

    def cues(self):
        return [
            # V1 riverbank
            Cue(0.0, "river", vol=0.35, dur=3.0),
            Cue(0.0, "wind", vol=0.35, dur=3.0),
            Cue(0.35, "slide_up", vol=0.6),
            Cue(1.15, "whoosh", vol=0.35),
            Cue(T_CROW_LAND, "crow", vol=0.9),        # 2nd caw lands exactly on T_CAW
            Cue(T_CRY + 0.05, "sweat", vol=0.45),
            # V2 pachinko
            Cue(T2, "whoosh", vol=0.7),
            Cue(3.12, "coin", vol=0.35, pitch=1.3),
            Cue(3.22, "coin", vol=0.35, pitch=1.5),
            Cue(3.30, "coin", vol=0.5),
            Cue(3.45, "coin", vol=0.35, pitch=1.4),
            Cue(3.62, "coin", vol=0.5, pitch=1.2),
            Cue(3.80, "coin", vol=0.3, pitch=1.6),
            Cue(T_REACH, "pop", vol=0.6),
            Cue(T_REACH + 0.05, "drumroll", vol=0.55, dur=T_SEVEN - T_REACH - 0.05),
            Cue(T_SEVEN, "coin", vol=0.6, pitch=1.8),           # ding: 7-7-7?!
            Cue(T_MISS, "record_scratch", vol=0.9),
            Cue(T_GREY, "fail", vol=0.8),
            Cue(T_STAMP, "thud", vol=0.9),
            Cue(T_ASH - 0.1, "wind", vol=0.5, dur=0.8),
            # V3 Monday
            Cue(T3, "whoosh", vol=0.7),
            Cue(T_TEAR, "slide_up", vol=0.8),
            Cue(T_TEAR + 0.12, "sparkle", vol=0.6),
            Cue(T_SPLIT, "whoosh", vol=0.5),
            Cue(T_JUMP_IN, "fanfare", vol=0.55),                # the holy JUMP descends
            Cue(T_STARS, "shine", vol=0.5),
            Cue(T_TEARS, "sparkle", vol=0.4, pitch=1.2),
            # V4 concert
            Cue(T4, "whoosh", vol=0.7),
            Cue(T4, "crowd", vol=0.4, dur=3.0),
            Cue(8.95, "cheer", vol=0.55),
            Cue(9.15, "slide_up", vol=0.6),
            Cue(T_SPLIT4, "whoosh", vol=0.5),
            Cue(T_SPLIT4 + 0.3, "cheer", vol=0.7),
        ] + [Cue(t0, "pop", vol=0.5, pitch=1.0 + 0.15 * i) for t0, _, i in V4_LOVE] + [
            Cue(11.25, "applause", vol=0.5),
            # V5 sukonbu
            Cue(T5, "whoosh", vol=0.7),
            Cue(11.95, "eat", vol=0.45, dur=T_POP - 11.95),
            Cue(T_POP, "pop", vol=0.9),
            Cue(T_JOLT, "boing", vol=0.8),
            Cue(T_JOLT + 0.03, "whoosh", vol=0.5, pitch=1.3),
            Cue(T_LAND - 0.54, "fall_whistle", vol=0.45, pitch=2.6),
            Cue(T_LAND, "thud", vol=0.9),
            Cue(T_LAND + 0.1, "eat", vol=0.45, dur=T6 - T_LAND),
            # V6 Kondo under the floor
            Cue(T6, "whoosh", vol=0.7),
            Cue(T_AURA, "aura", vol=0.7),
            Cue(T_RISE, "shing", vol=0.6),
            Cue(T_STAB, "stab", vol=1.0),
            Cue(T_STAB + 0.02, "impact", vol=0.8),
            Cue(T_STAB + 0.12, "shock", vol=0.6),
            Cue(T_STAB + 0.5, "sweat", vol=0.6),
            Cue(T_CAP, "rimshot", vol=0.8),
            Cue(T_CROW6_CAW, "crow", vol=0.8),
        ]


SCENE = Daily()
