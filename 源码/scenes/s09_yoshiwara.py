"""s09 吉原炎上篇 (29.5 s) — underground Yoshiwara, the Night King, the sun.

SHOT LIST (scene-local seconds)
  0.00- 1.90  chapter card 「吉原炎上篇」 over the iron lid (establishing starts beneath)
  S1  0.00- 5.45  tilt DOWN from the riveted iron ceiling to the lantern street; crowd;
                  Seita runs in; push-in on him while he speaks. name_card 晴太 3.4
  S2  5.45- 8.10  medium: rooftop glint -> kunai thunks at Seita's toes (咚! / !! hop,
                  sweat) -> Tsukuyo drops from the roof, lands, kiseru. name_card 月咏 6.0
  S3  8.10-10.45  tilt UP Hinowa's tower -> push-in to the round window (Hinowa).
  S4 10.45-12.75  rooftop: Kamui sitting; 11.90 CUT close-up, eyes open (red flash,
                  dark-red focus lines).
  S5 12.75-15.00  throne room dark, eyes glint -> 13.10 gong, whip pull-back to the
                  full giant with red aura. name_card 夜王凤仙 13.3 (music -> battle)
  S6 15.00-16.55  corridor: haymaker, custom impact frame 15.36 (black/red, white
                  silhouettes), Gintoki tumbles through three thick walls (chunks).
  S7 16.55-19.70  street: bursts out of a facade, lands, rises bloody (bokuto glint),
                  Housen's silhouette in the hole.
  S8a 19.70-20.65 control room: Tsukuyo shoves, Seita dangles off the lever handle;
                  slam 20.25 (咔嚓!!), gears spin, Seita cheers.
  S8b 20.65-21.95 looking up: the lid opens, SUN + rays (music -> epic 21.2), white-out.
  S9  21.95-24.20 sunlit street: Housen scorched; Gintoki crouches and launches;
                  22.50-22.93 insert: his rim-lit silhouette crosses the sun; dive,
                  impact frame 23.02, 斩!!, Housen falls to his knees.
  S10 24.20-26.60 close on Housen's upturned face in the light, pull back as he
                  crumbles into dust while Gintoki watches.
  S11 26.60-29.50 sakura: Seita runs into Hinowa's arms (hearts); pan to Gintoki
                  face-down 「……糖分……」 + Tsukuyo's sweat drop + crow.
"""
import math

from PIL import Image, ImageDraw

from engine.core import (Scene, Cue, W, H, seg, lerp, clamp, ease_in, ease_out, ease_in_out,
                         ease_out_back, wave, step_frame, rng, arc)
from engine.gfx import INK, PAL, rect, overlay_rect, stamp_line, polygon, shade, outline, scale_nearest
from engine import fx
from engine.text import sfx_text, name_card, chapter_card, speech_bubble, draw_text
from chars import draw_char, render_sprite
from bg import common as C
from scenes import _s09_bg as B

FLOOR = 160
NIGHT_DIM = (34, 26, 56)


# ------------------------------------------------------------------ helpers
def zoom_at(img, k, px, py, sx, sy):
    """Zoom by k so that canvas point (px, py) lands on screen point (sx, sy).
    Returns a function mapping pre-zoom canvas coords to post-zoom screen coords."""
    if abs(k - 1) < 1e-3:
        return lambda x, y: (x, y)
    hw, hh = W / (2 * k), H / (2 * k)
    cx = clamp(px - sx / k + hw, hw, W - hw)
    cy = clamp(py - sy / k + hh, hh, H - hh)
    fx.zoom(img, k, cx, cy)
    return lambda x, y: ((x - (cx - hw)) * k, (y - (cy - hh)) * k)


def crowd(img, t, cam_x, tilt, n=6, seed=0, mode="night", y=158):
    """Dimmed townsfolk strolling both ways (background extras)."""
    for i in range(n):
        r = rng("s09crowd", seed, i)
        cid = "townsman" if r.random() < 0.55 else "townswoman"
        v = r.randrange(4)
        sp = r.uniform(12, 24) * (1 if r.random() < 0.5 else -1)
        span = W + 120
        x = (r.uniform(0, span) + sp * t - cam_x) % span - 60
        dim = 0.62 if mode == "night" else 0.1
        draw_char(img, cid, x, y + tilt - (i % 2), "walk", t + i * 0.37, facing=1 if sp > 0 else -1,
                  flash=dim, flash_color=NIGHT_DIM if mode == "night" else (255, 240, 200), variant=v)


def embers(img, t, seed=0, count=26, area=(0, 20, W, 170)):
    fx.embers(img, t, count=count, seed=seed, rise=10.0, area=area,
              colors=((255, 190, 110), (255, 140, 90), (255, 230, 170)))


def kunai_stuck(img, x, y, wob=0.0, ang=-60, k=1.0):
    """A kunai with its tip at (x, y), pointing along `ang` degrees (screen,
    -60 = stuck in the ground leaning right). k scales it."""
    a = math.radians(ang + wob)
    vx, vy = math.cos(a), -math.sin(a)
    tip = (x, y)
    hilt = (x - vx * 8 * k, y - vy * 8 * k)
    end = (x - vx * 13 * k, y - vy * 13 * k)
    w = 3 if k < 1.3 else 4
    stamp_line(img, tip, hilt, w, INK)
    stamp_line(img, (x - vx * 1, y - vy * 1), hilt, w - 2, (220, 226, 240))
    stamp_line(img, (x - vx * 2, y - vy * 2), (x - vx * 5 * k, y - vy * 5 * k), 1, (255, 255, 255))
    stamp_line(img, hilt, end, 3, INK)
    stamp_line(img, hilt, end, 1, (60, 40, 60))
    d = ImageDraw.Draw(img)
    rr = 2 * k
    ex, ey = end[0] - vx * rr, end[1] - vy * rr
    d.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], outline=INK)


def heart(img, x, y, c=(255, 110, 140)):
    pts = [".xx.xx.", "xxxxxxx", "xxxxxxx", ".xxxxx.", "..xxx..", "...x..."]
    d = ImageDraw.Draw(img)
    for j, row in enumerate(pts):
        for i, ch in enumerate(row):
            if ch == "x":
                d.point((int(x) - 3 + i, int(y) - 3 + j), fill=c)


def blood_trickle(img, x, y, facing=1, k=1.0):
    """Small stylised red trickle on Gintoki's forehead (feet at x, y)."""
    if k <= 0:
        return
    red = (206, 36, 52)
    L = int(round(2 + 5 * k))
    fx_ = x + 3 * facing
    for j in range(L):
        img.putpixel((int(fx_), int(y - 26 + j)), red) if 0 <= fx_ < W and 0 <= y - 26 + j < H else None
    for (dx, dy) in ((1, -25), (-5, -24)):
        px, py = int(x + dx * facing), int(y + dy)
        if 0 <= px < W and 0 <= py < H:
            img.putpixel((px, py), red)


def steam(img, t, x, y, spread=14, seed=0, n=8, color=(236, 232, 226)):
    """Wisps of smoke rising from a sun-scorched body."""
    d = ImageDraw.Draw(img)
    for i in range(n):
        r = rng("steam", seed, i)
        u = (t * r.uniform(0.7, 1.2) + r.random()) % 1.0
        px = x + r.uniform(-spread, spread) + math.sin(u * 5 + i) * 3
        py = y - u * 28
        rr = 1 + int(u * 3)
        if u < 0.85:
            d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=color if u < 0.5 else shade(color, 0.85))


def aura(img, t, cx, base_y, h, w, seed=0, colors=((120, 20, 40), (190, 40, 56), (255, 90, 80))):
    """Flickering flame-tongue aura around a figure (drawn behind it)."""
    d = ImageDraw.Draw(img)
    for layer, col in enumerate(colors):
        sc = 1 - layer * 0.22
        pts = []
        n = 11
        for i in range(n + 1):
            u = i / n
            x = cx + (u - 0.5) * w * sc
            flick = rng("aura", seed, layer, i, step_frame(t, 12)).uniform(0.75, 1.15)
            top = base_y - h * sc * flick * (0.55 + 0.45 * math.sin(u * math.pi))
            pts.append((x, top))
            if i < n:
                xm = x + w * sc / n / 2
                pts.append((xm, base_y - h * sc * 0.55 * (0.4 + 0.6 * math.sin(u * math.pi))))
        # taper toward the feet (flame body, not a box)
        pts += [(cx + w * sc / 2, base_y - h * 0.25), (cx + w * sc * 0.22, base_y),
                (cx - w * sc * 0.22, base_y), (cx - w * sc / 2, base_y - h * 0.25)]
        d.polygon(pts, fill=col)


def debris(img, t, t0, x, y, seed=0, n=18, spread=(-70, 70), speed=(60, 170)):
    fx.burst(img, t, t0, x, y, n=n, colors=[(236, 226, 200), (150, 100, 70), (200, 180, 150), (90, 60, 50)],
             speed=speed, gravity=260, life=0.9, size=(1, 3), seed=seed, spread=spread)


# ------------------------------------------------------------------ shots
def shot1(img, t):
    """Establishing tilt-down + Seita runs in."""
    tilt = lerp(205, 0, ease_in_out(seg(t, 1.75, 3.45)))
    cam = lerp(0, 34, ease_out(seg(t, 1.75, 5.45)))
    B.street(img, cam, t, tilt=tilt, mode="night")
    crowd(img, t, cam, tilt, n=5, seed=1)
    # Seita runs in and stops, looking toward the tower
    if t < 3.0:
        pass
    elif t < 3.9:
        k = seg(t, 3.0, 3.9)
        draw_char(img, "seita", lerp(-20, 150, ease_out(k)), FLOOR + tilt, "run", t)
    else:
        f = step_frame(t, 8) % 2
        pose = "talk" if t < 5.2 else "idle"
        draw_char(img, "seita", 150, FLOOR + tilt, pose, t, expr=("shout" if f else "determined") if t < 4.75 else None)
        if t < 4.2:
            fx.smoke_puff(img, t, 3.9, 146, FLOOR + tilt - 2, size=6, seed=4)
    embers(img, t, seed=1, count=22)
    # push in on the boy while he speaks (feet stay above the dialogue box)
    k = lerp(1.0, 1.65, ease_in_out(seg(t, 3.9, 5.45)))
    zoom_at(img, k, 150, 160, lerp(150, 176, seg(k, 1.0, 1.65)), 166)


S2_KUNAI = 5.68     # kunai thunks between Seita's toes
S2_DROP = 5.85      # Tsukuyo jumps off the roof
S2_LAND = 6.02


def shot2(img, t):
    """Medium shot: glint -> kunai gag -> Tsukuyo drops in."""
    cam = lerp(30, 38, seg(t, 5.45, 8.1))
    B.street(img, cam, t, tilt=0, mode="night")
    crowd(img, t, cam, 0, n=3, seed=2, y=155)
    sx = 180 - cam          # Seita screen x
    tx = sx + 50            # Tsukuyo landing x
    gx_, gy_ = tx + 34, 84  # where the kunai is thrown from (a rooftop, top right)
    # kunai
    kx, ky = sx + 8, FLOOR + 1
    # Seita (drawn before the kunai so the blade stays visible at his toes)
    if t < S2_KUNAI:
        draw_char(img, "seita", sx, FLOOR, "idle", t, expr="determined")
    elif t < S2_KUNAI + 0.62:
        u = t - S2_KUNAI
        hop = -int(round(11 * math.sin(math.pi * clamp(u / 0.3)))) if u < 0.3 else 0
        draw_char(img, "seita", sx - 2 * clamp(u / 0.3), FLOOR + hop, "shock", t, p=u / 0.62, facing=1,
                  shadow=hop > -3)
    else:
        f = step_frame(t, 12) % 2
        draw_char(img, "seita", sx - 2 + (f if t < 7.0 else 0), FLOOR, "idle", t,
                  expr="sad" if t > 7.0 else "shock")
        # sweat drop sliding down his temple
        d = ImageDraw.Draw(img)
        yy = FLOOR - 24 + int(min(5, (t - S2_KUNAI - 0.62) * 3))
        d.ellipse([sx - 10, yy, sx - 8, yy + 3], fill=(140, 200, 255), outline=(60, 110, 200))
    # glint on the rooftop, then the kunai streaks down
    fx.sparkle(img, gx_, gy_, t, S2_KUNAI - 0.2, size=5, color=(255, 255, 230))
    if S2_KUNAI - 0.08 <= t < S2_KUNAI:
        k = seg(t, S2_KUNAI - 0.08, S2_KUNAI)
        x0, y0 = lerp(gx_, kx, k), lerp(gy_, ky, k)
        ang = math.degrees(math.atan2(-(ky - gy_), kx - gx_))
        ImageDraw.Draw(img).line([(x0, y0), (lerp(gx_, kx, max(0, k - 0.6)), lerp(gy_, ky, max(0, k - 0.6)))],
                                 fill=(230, 236, 255), width=1)
        kunai_stuck(img, x0, y0, 0, ang=ang, k=1.3)
    if t >= S2_KUNAI:
        u = t - S2_KUNAI
        wob = 14 * math.sin(u * 60) * max(0, 1 - u * 3)
        kunai_stuck(img, kx, ky, wob, ang=-128, k=1.3)
        fx.burst(img, t, S2_KUNAI, kx, ky, n=12, colors=[(255, 250, 200), (200, 190, 180)], speed=(30, 90),
                 gravity=150, life=0.35, seed=21, spread=(180, 360))
    # Tsukuyo drops from the rooftop
    if S2_DROP <= t < S2_LAND:
        k = ease_in(seg(t, S2_DROP, S2_LAND))
        draw_char(img, "tsukuyo", lerp(gx_ - 6, tx, k), lerp(gy_ - 10, FLOOR, k), "jump", t, facing=-1, shadow=False)
    elif t >= S2_LAND:
        if t < S2_LAND + 0.2:
            draw_char(img, "tsukuyo", tx, FLOOR, "land", t, p=(t - S2_LAND) / 0.2, facing=-1, expr="determined")
        else:
            draw_char(img, "tsukuyo", tx, FLOOR, "smoke", t, facing=-1)
        fx.smoke_puff(img, t, S2_LAND, tx, FLOOR - 1, size=12, seed=7, color=(180, 170, 200))
    embers(img, t, seed=2, count=16)
    bump = 0.14 * (1 - ease_out(seg(t, S2_KUNAI, S2_KUNAI + 0.25))) if t >= S2_KUNAI else 0
    k = 1.9 + bump + 0.12 * ease_in_out(seg(t, 6.4, 8.1))
    zm = zoom_at(img, k, (sx + tx) / 2 + 4, FLOOR, 192, 164)
    if S2_KUNAI <= t < S2_KUNAI + 0.45:
        x_, y_ = zm(sx, FLOOR - 40)
        sfx_text(img, int(x_), int(y_), "!!", t, S2_KUNAI + 0.02, dur=0.45, size=24, angle=0,
                 color=(255, 240, 120))
        x_, y_ = zm(kx + 12, ky - 6)
        sfx_text(img, int(x_), int(y_), "咚!", t, S2_KUNAI, dur=0.4, size=16, angle=-10)
    dx, dy = fx.shake_offset(t, S2_KUNAI, 0.18, 2, seed=22)
    ddx, ddy = fx.shake_offset(t, S2_LAND, 0.15, 2, seed=23)
    fx.shift(img, dx + ddx, dy + ddy)


def sfx_text_small(img, x, y, text, t, t0):
    sfx_text(img, x, y, text, t, t0, dur=0.55, size=16, angle=0, color=(255, 240, 120))


def hinowa_in_window(img, t, wx, wy, mode="night"):
    """Hinowa (bust, in her wheelchair) seen through the round window."""
    wr = B.TOWER_WIN[2]
    s = 2 * wr + 1
    win = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    # warm room behind her
    dw = ImageDraw.Draw(win)
    dw.rectangle([0, 0, s, s], fill=(250, 196, 128, 255) if mode == "night" else (255, 226, 170, 255))
    dw.rectangle([0, s - 12, s, s], fill=(196, 120, 80, 255))
    for x in range(3, s, 8):
        dw.line([(x, 0), (x, s - 13)], fill=(236, 170, 110, 255))
    spr, ax, ay = render_sprite("hinowa", "smile", t, expr=("sad" if (t % 3.3) > 0.15 else "blink"), facing=-1)
    win.alpha_composite(spr, (int(wr - ax + 2), int(s + 16 - ay)))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, s - 1, s - 1], fill=255)
    img.paste(win.convert("RGB"), (int(wx - wr), int(wy - wr)), mask)
    ring = B.window_ring(mode)
    img.paste(ring, (int(wx - ring.width // 2), int(wy - ring.height // 2)), ring)


def shot3(img, t):
    """Hinowa's tower: tilt up, push in on the round window."""
    v = ease_in_out(seg(t, 8.1, 8.9))
    wx, wy = B.tower_scene(img, t, v)
    hinowa_in_window(img, t, wx, wy)
    embers(img, t, seed=3, count=30, area=(0, 0, W, H))
    z = ease_in_out(seg(t, 8.85, 10.1))
    zoom_at(img, lerp(1.0, 2.4, z), wx, wy, lerp(wx, 272, z), lerp(wy, 106, z))


def shot4(img, t):
    """Kamui on the rooftop, then the eyes open."""
    cam = lerp(0, 14, seg(t, 10.45, 12.75))
    close = t >= 11.9
    B.roof_scene(img, t, cam)
    kx = 244 - cam
    if not close:
        draw_char(img, "kamui", kx, 151, "sit", t, expr="normal", shadow=False)
        embers(img, t, seed=4, count=24)
        k = lerp(1.55, 2.0, ease_in_out(seg(t, 10.45, 11.9)))
        zoom_at(img, k, kx, 132, 236, 120)
    else:
        draw_char(img, "kamui", kx, 151, "sit", t, expr="open_eyes", shadow=False)
        embers(img, t, seed=4, count=24)
        kk = lerp(3.6, 3.2, ease_out(seg(t, 11.9, 12.75)))
        zm = zoom_at(img, kk, kx + 1, 126, 196, 98)
        fx.grade(img, (1.05, 0.72, 0.78), (18, 0, 6))
        fx.vignette(img, 0.7)
        if t < 12.3:   # the killing intent hits like a wall
            fx.speed_lines(img, t, cx=196, cy=100, color=(60, 6, 16), count=40, inner=64, seed=41,
                           alpha=1 - 0.6 * seg(t, 12.05, 12.3))
            if t < 11.96:
                fx.flash(img, 0.55, (255, 60, 60))
        ex, ey = zm(kx + 4, 134)
        fx.sparkle(img, int(ex), int(ey), t, 11.93, size=7, color=(200, 230, 255))


def housen_eyes(img, x, y, scale, facing, t, t0, size=4):
    for dx in (-3, 3):
        ex = int(x + dx * scale * facing - (1 if facing < 0 else 0))
        ey = int(y - 35 * scale)
        fx.sparkle(img, ex, ey, t, t0, size=size, color=(170, 225, 255))


def shot5(img, t):
    """Throne room: eyes in the dark -> the Night King."""
    light = ease_out(seg(t, 13.1, 13.45))
    B.throne(img, t, light=max(0.08, light))
    hx, hy = 256, 166
    if light > 0:
        aura(img, t, hx - 2, hy, 118 * (0.6 + 0.4 * light), 100, seed=5)
        g = C.glow_sprite(70, (200, 40, 50), round(light * 0.8 * 4) / 4)
        C.add_sprite(img, g, hx - 70, hy - 60 - 70)
    talking = 12.88 <= t < 13.7
    expr = ("talk" if step_frame(t, 8) % 2 == 0 else "normal") if talking else ("smug" if t > 14.2 else "normal")
    draw_char(img, "housen", hx, hy, "idle", t, expr=expr, facing=-1, scale=2,
              flash=(1 - light) * 0.85, flash_color=(10, 6, 16))
    fx.embers(img, t, count=22, seed=5, rise=18, area=(150, 40, 360, 170),
              colors=((255, 90, 70), (255, 160, 90), (200, 40, 60)))
    # eyes glint in the dark, again when the lights flare
    if t < 13.3:
        housen_eyes(img, hx, hy, 2, -1, t, 12.8, size=5)
        housen_eyes(img, hx, hy, 2, -1, t, 13.25, size=3)
    if t < 13.45:   # whip pull-back on the gong (done before the name card lands)
        u = ease_out(seg(t, 13.1, 13.45))
        k = lerp(2.4, 1.0, u)
        zoom_at(img, k, hx, hy - 70, lerp(210, hx, u), lerp(92, hy - 70, u))
    else:   # slow push that keeps his feet above the dialogue box
        zoom_at(img, 1 + 0.12 * ease_in_out(seg(t, 13.45, 15.0)), hx, hy - 2, hx - 10, hy - 2)
    if 13.1 <= t < 13.22:
        fx.flash(img, 1 - seg(t, 13.1, 13.22), (255, 120, 100))
    dx, dy = fx.shake_offset(t, 13.1, 0.4, 3, seed=5)
    fx.shift(img, dx, dy)


# S6 constants
S6_HIT = 15.36
S6_GX0 = 178
S6_SPEED = 620.0
S6_WALLS = (330, 520, 710)


def s6_gx(t):
    if t < S6_HIT:
        return S6_GX0
    return S6_GX0 + (t - S6_HIT) * S6_SPEED


def s6_wall_time(wx):
    return S6_HIT + (wx - S6_GX0) / S6_SPEED


S6_FLY_Y = 136     # Gintoki's feet y while airborne (body centre ~ the wall holes)


def s6_rot(t):
    """Blown back head-first, tumbling once more through every wall."""
    r = 50 + 6 * math.sin(t * 35)
    for wx in S6_WALLS:
        tb = s6_wall_time(wx)
        r += 360 * ease_out(seg(t, tb, tb + 0.2))
    return int(r) % 360


def s6_housen_p(t):
    if t < 15.3:
        return seg(t, 15.0, 15.3) * 0.3
    return 0.3 + seg(t, 15.3, 15.38) * 0.15 + seg(t, 15.38, 16.0) * 0.3


def shot6(img, t):
    """Housen's haymaker sends Gintoki through three walls."""
    gx = s6_gx(t)
    cam = max(0.0, gx - 150)
    B.corridor(img, cam, t)
    # Housen
    draw_char(img, "housen", 112 - cam, FLOOR, "punch", t, p=s6_housen_p(t), scale=1.3)
    # walls (drawn before Gintoki; the smashed ones already show their hole)
    for i, wx in enumerate(S6_WALLS):
        tb = s6_wall_time(wx)
        B.partition(img, wx - cam, 1 if t >= tb else 0, seed=i)
    if t < S6_HIT:
        wob = int(round(math.sin(t * 50))) if t > 15.15 else 0      # bracing, trembling
        draw_char(img, "gintoki", gx - cam + wob, FLOOR, "guard", t, facing=-1, expr="angry")
        if t > 15.12:
            fx.sparkle(img, int(112 - cam + 10), int(FLOOR - 58), t, 15.12, size=5, color=(170, 225, 255))
    else:
        k = ease_out(seg(t, S6_HIT, S6_HIT + 0.1))
        fl = max(0.0, 1 - (t - S6_HIT) * 6)
        draw_char(img, "gintoki", gx - cam, lerp(FLOOR, S6_FLY_Y, k), "hit", t, p=1.0, facing=-1,
                  rot=int(lerp(0, s6_rot(t), k)), shadow=False, flash=fl)
        fx.motion_lines(img, t, color=(255, 240, 210), count=18, direction=-1, seed=6, y0=40, y1=156,
                        speed=1400, length=(30, 90))
    for i, wx in enumerate(S6_WALLS):
        tb = s6_wall_time(wx)
        if t >= tb:
            B.chunks(img, t, tb, wx - cam + 6, B.PART_HOLE[0], seed=60 + i, n=16)
            for j, (ox, oy) in enumerate(((-14, -14), (-12, 16), (20, 4))):
                fx.smoke_puff(img, t, tb, wx - cam + ox, B.PART_HOLE[0] + oy, size=9, seed=62 + i * 3 + j,
                              color=(236, 226, 206), life=0.45)
    u = ease_in_out(seg(t, S6_HIT, S6_HIT + 0.25))
    ax = lerp(145 - cam, gx - cam, u)
    zk = lerp(1.55, 1.7, ease_in(seg(t, 15.0, S6_HIT))) if t < S6_HIT else lerp(1.7, 1.55, u)
    zmap = zoom_at(img, zk, ax, 126, lerp(192, 160, u), 116)
    for i, wx in enumerate(S6_WALLS):
        tb = s6_wall_time(wx)
        if t >= tb:
            px_, py_ = ((230, 50), (300, 78), (236, 58))[i]
            sfx_text(img, px_, py_, "轰!", t, tb, dur=0.45, size=28, angle=(-10, 8, -6)[i])
    if S6_HIT + 0.07 <= t < S6_HIT + 0.3:
        cx_, cy_ = zmap(gx - cam, 124)
        fx.speed_lines(img, t, cx=cx_, cy=cy_, color=(255, 255, 255), count=36, inner=60, seed=6,
                       alpha=1 - seg(t, S6_HIT + 0.15, S6_HIT + 0.3))
    if S6_HIT <= t < S6_HIT + 0.07:
        s6_impact(img, t, cam, zmap)
    dx, dy = fx.shake_offset(t, S6_HIT, 0.35, 5, seed=6)
    for i, wx in enumerate(S6_WALLS):
        ddx, ddy = fx.shake_offset(t, s6_wall_time(wx), 0.2, 3, seed=61 + i)
        dx, dy = dx + ddx, dy + ddy
    fx.shift(img, dx, dy)


def s6_impact(img, t, cam, zmap):
    """Impact frame for the haymaker (the engine's 2-tone threshold turns the
    bright corridor to mush): black void, red focus lines, white silhouettes
    and a shock ring at the fist."""
    img.paste((16, 6, 14), (0, 0, W, H))
    cx_, cy_ = S6_GX0 - cam - 7, 126
    fx.speed_lines(img, t, cx=cx_, cy=cy_, color=(206, 30, 52), count=46, inner=24, seed=66)
    draw_char(img, "housen", 112 - cam, FLOOR, "punch", t, p=s6_housen_p(t), scale=1.3, flash=1.0,
              flash_color=(255, 255, 255), shadow=False)
    draw_char(img, "gintoki", s6_gx(t) - cam + 2, FLOOR - 3, "hit", t, p=0.4, facing=-1, flash=1.0,
              flash_color=(255, 255, 255), shadow=False)
    d = ImageDraw.Draw(img)
    for r, wd in ((9 + (t - S6_HIT) * 260, 2), (16 + (t - S6_HIT) * 400, 1)):
        d.ellipse([cx_ - r * 0.6, cy_ - r, cx_ + r * 0.6, cy_ + r], outline=(255, 255, 255), width=wd)
    zoom_at(img, 1.7, 145 - cam, 126, 192, 116)


S7_CAM = 300
HOLE = (138, 124)          # centre of the smashed facade hole (screen)


def facade_hole(img, t, sun=False):
    r = rng("s09hole")
    cx, cy = HOLE
    pts = []
    for i in range(16):
        a = i / 16 * 2 * math.pi
        rr = r.uniform(0.8, 1.15)
        pts.append((cx + math.cos(a) * 26 * rr, cy + math.sin(a) * 22 * rr))
    d = ImageDraw.Draw(img)
    d.polygon([(x + (2 if x > cx else -2), y + (2 if y > cy else -2)) for x, y in pts], fill=(24, 16, 20))
    d.polygon(pts, fill=(250, 196, 120))
    inner = [(cx + (x - cx) * 0.7, cy + (y - cy) * 0.7 + 3) for x, y in pts]
    d.polygon(inner, fill=(255, 226, 170))
    for i in range(0, 16, 2):
        x, y = pts[i]
        d.line([(x, y), (x + r.uniform(-5, 5), y + r.uniform(-5, 5))], fill=(120, 70, 50), width=2)
    g = C.glow_sprite(40, (255, 170, 90), 0.8)
    C.add_sprite(img, g, cx - 40, cy - 40)


def rubble(img, x, y):
    d = ImageDraw.Draw(img)
    r = rng("rubble")
    for i in range(14):
        px = x + r.uniform(-26, 26)
        py = y - r.uniform(0, 5)
        w = r.randint(3, 8)
        c = [(120, 80, 60), (200, 186, 160), (90, 60, 50), (150, 110, 80)][i % 4]
        d.polygon([(px, py), (px + w, py - r.randint(1, 4)), (px + w + 1, py + 2), (px, py + 2)], fill=c, outline=INK)


def shot7(img, t):
    """Burst out of the facade, land in rubble, rise bloody."""
    B.street(img, S7_CAM, t, tilt=0, mode="night")
    facade_hole(img, t)
    gl = 222   # landing x
    # Housen silhouette appears in the hole
    if t >= 18.1:
        a = seg(t, 18.1, 18.7)
        draw_char(img, "housen", HOLE[0] + 4, HOLE[1] + 26, "idle", t, facing=1, shadow=False,
                  flash=1.0, flash_color=(20, 10, 18), alpha=a)
        if a > 0.6:
            for dx in (-2, 4):
                img.putpixel((HOLE[0] + 4 + dx, HOLE[1] + 26 - 35), (170, 225, 255))
    rubble(img, gl, FLOOR + 2)
    if t < 16.85:
        k = seg(t, 16.55, 16.85)
        x, y = arc((HOLE[0] + 10, HOLE[1] + 10), (gl, FLOOR), k, 26)
        draw_char(img, "gintoki", x, y, "fly", t, shadow=False)
    elif t < 17.15:
        draw_char(img, "gintoki", gl, FLOOR, "lie", t, expr="hurt")
    elif t < 17.45:
        draw_char(img, "gintoki", gl, FLOOR, "kneel", t, expr="hurt", facing=-1)
        blood_trickle(img, gl, FLOOR + 4, -1, seg(t, 17.15, 17.45))
    else:
        draw_char(img, "gintoki", gl, FLOOR, "ready", t, facing=-1, expr="angry")
        blood_trickle(img, gl, FLOOR, -1, 1.0)
        fx.sparkle(img, gl - 21, FLOOR - 22, t, 17.5, size=5, color=(255, 255, 240))    # bokuto glint
    debris(img, t, 16.55, HOLE[0] + 10, HOLE[1], seed=70, n=30, spread=(-50, 40), speed=(80, 220))
    fx.smoke_puff(img, t, 16.85, gl, FLOOR - 2, size=20, seed=71, color=(150, 136, 150), life=1.1)
    fx.smoke_puff(img, t, 16.55, HOLE[0] + 6, HOLE[1] + 6, size=24, seed=72, color=(170, 150, 150), life=1.0)
    # drifting dust in the wind
    fx.snow(img, t, count=26, seed=7, color=(170, 150, 150), speed=10)
    embers(img, t, seed=7, count=14)
    z = ease_in_out(seg(t, 16.95, 19.2))
    zoom_at(img, lerp(1.0, 1.9, z), 180, 136, 192, lerp(136, 112, z))
    fx.letterbox(img, ease_out(seg(t, 16.95, 17.4)), bar=20)
    if 16.55 <= t < 16.6:
        fx.flash(img, 0.7, (255, 220, 170))
    dx, dy = fx.shake_offset(t, 16.55, 0.3, 4, seed=7)
    ddx, ddy = fx.shake_offset(t, 16.85, 0.25, 3, seed=8)
    fx.shift(img, dx + ddx, dy + ddy)
    if 16.55 <= t < 17.1:
        sfx_text(img, 150, 60, "轰隆!!", t, 16.55, dur=0.55, size=26)


T8A, T8B, T9, T10, T11, T_END = 19.70, 20.65, 21.95, 24.20, 26.60, 29.50
S8_SLAM = 20.25                  # the lever slams home
S9_HIT = T9 + 1.07               # final strike (impact frame)


def shot8a(img, t):
    """Seita + Tsukuyo heave the lid lever over: Tsukuyo shoves the shaft,
    little Seita hangs off the handle with his whole weight."""
    spin = 0 if t < S8_SLAM else (t - S8_SLAM) ** 2 * 500
    B.control_room(img, t, spin)
    if t < S8_SLAM - 0.1:        # straining: the lever creeps and shudders
        ang = lerp(2, 20, ease_in_out(seg(t, T8A, S8_SLAM - 0.1))) + math.sin(t * 70) * 1.5
    else:                        # ...then gives way all at once
        ang = lerp(20, 66, ease_in(seg(t, S8_SLAM - 0.1, S8_SLAM)))
        ang += 4 * math.sin((t - S8_SLAM) * 40) * max(0.0, 1 - (t - S8_SLAM) * 4) if t >= S8_SLAM else 0
    px, py = 190, 144
    hx_, hy_ = B.lever(img, px, py, ang, L=30, floor=FLOOR)
    a = math.radians(ang)
    # Tsukuyo shoves the shaft from the left
    sx_ = px + math.sin(a) * 12
    tsx = sx_ - 13 if t < S8_SLAM else lerp(px + math.sin(math.radians(20)) * 12 - 13, px - 12,
                                            ease_out(seg(t, S8_SLAM - 0.1, S8_SLAM + 0.1)))
    draw_char(img, "tsukuyo", tsx, FLOOR, "punch", t, p=1.0, expr="shout" if t < S8_SLAM else "determined",
              arm_f=100, arm_b=94, lean=3)
    # Seita dangles off the handle (legs kicking) and rides it down, then cheers
    if t < S8_SLAM + 0.05:
        kick = step_frame(t, 12) % 2
        draw_char(img, "seita", hx_ + 4, min(FLOOR, hy_ + 25), "jump", t, expr="shout", shadow=False,
                  arm_f=172, arm_b=160, dy=-kick)
        if t < S8_SLAM:
            d = ImageDraw.Draw(img)
            yy = int(hy_ + 4 + (t * 20) % 5)
            d.ellipse([hx_ + 11, yy, hx_ + 13, yy + 3], fill=(140, 200, 255), outline=(60, 110, 200))
    else:
        draw_char(img, "seita", hx_ + 6, FLOOR, "cheer", t)
    if t >= S8_SLAM:
        fx.burst(img, t, S8_SLAM, px + 10, py - 2, n=16, colors=[(255, 230, 120), (255, 255, 255)],
                 speed=(40, 130), gravity=200, life=0.4, seed=81)
        fx.smoke_puff(img, t, S8_SLAM, 336, 140, size=16, seed=82, color=(220, 220, 230), life=0.5)
    zoom_at(img, lerp(2.4, 2.55, seg(t, T8A, T8B)), 196, 136, 192, 122)
    if t >= S8_SLAM:
        sfx_text(img, 292, 54, "咔嚓!!", t, S8_SLAM, dur=0.4, size=30)
    elif t > T8A + 0.08:
        sfx_text(img, 104, 56, "嘿——!!", t, T8A + 0.08, dur=S8_SLAM - T8A - 0.08, size=20, angle=6,
                 color=(255, 255, 255))
    dx, dy = fx.shake_offset(t, S8_SLAM, 0.3, 3, seed=8)
    fx.shift(img, dx, dy)


def shot8b(img, t):
    """Looking up: the lid opens, the SUN."""
    t = t - (T8B - 20.35)        # authored on the original 20.35 origin
    open_k = ease_in_out(seg(t, 20.62, 21.35))
    sun_k = ease_out(seg(t, 20.8, 21.5))
    rum = fx.shake_offset(t, 20.35, 1.2, 2, freq=24, seed=9)
    cx, cy = B.up_view(img, t, open_k, sun_k, dy=rum[1])
    hx, hy, hw, hh = B.HATCH
    # light leaking through the seam before it opens
    if t < 20.7:
        k = seg(t, 20.4, 20.62)
        if k > 0:
            d = ImageDraw.Draw(img)
            d.line([(cx, cy - hh // 2 + 2), (cx, cy + hh // 2 - 3)], fill=(255, 250, 200), width=1 + int(k * 2))
            B.shafts(img, [([(cx - 1, cy - 48), (cx + 1, cy - 48), (cx + 30, H + 20), (cx - 30, H + 20)], 0.35 * k)])
    # dust falling from the seams
    fx.burst(img, t, 20.4, cx, cy + 40, n=40, colors=[(200, 190, 180), (150, 140, 140)], speed=(10, 60),
             gravity=120, life=1.2, seed=90, spread=(30, 150))
    B.radial_rays(img, t, cx, cy + 2, open_k * 1.1)
    B.dust_motes(img, t, count=30, seed=9, color=(255, 250, 220))
    wf = seg(t, 21.3, 21.65)
    fx.flash(img, ease_in(wf), (255, 252, 236))


def sun_insert(img, t):
    """Low angle through the open lid: Gintoki's silhouette leaps across the sun."""
    r = t - T9
    cx, cy = B.up_view(img, t, 1.0, 1.0)
    zoom_at(img, 2.0, cx, cy + 4, 192, 104)
    B.radial_rays(img, t * 2.5, 192, 104, 1.25, n=16, seed=3)
    u = seg(r, 0.55, 0.98)
    x = lerp(150, 226, u)
    y = lerp(236, 122, ease_out(u))
    # back-lit silhouette with a thin warm rim so it pops against the sun
    spr, ax, ay = render_sprite("gintoki", "slash_up", t, p=0.62, flash=1.0, flash_color=(24, 14, 22),
                                rot=int(lerp(-16, 10, u)))
    spr = scale_nearest(outline(spr, (255, 236, 190)), 2)
    img.paste(spr, (int(x - (ax + 1) * 2), int(y - (ay + 1) * 2)), spr)
    fx.sparkle(img, int(x + 12), int(y - 76), t, T9 + 0.62, size=9, color=(255, 255, 255))
    if r < 0.6:
        fx.flash(img, 0.7 * (1 - seg(r, 0.55, 0.62)), (255, 252, 236))


def shot9(img, t):
    """Sun floods the street; Gintoki's final strike."""
    r = t - T9
    if 0.55 <= r < 0.98:
        sun_insert(img, t)
        return
    B.street(img, 250, t, tilt=0, mode="sun", leaves_open=1.0)
    B.sun_shafts(img, t, 1.0, ox=90, oy=-150, n=7, seed=1, alpha=0.3)
    hx = 240
    hit = S9_HIT
    # Housen: scorched by the sun, shielding his eyes, staggering
    if t < hit:
        sway = int(round(2 * math.sin(r * 9)))
        draw_char(img, "housen", hx + sway, FLOOR, "shock", t, p=0.5, expr="hurt", facing=-1, scale=1.3)
        steam(img, t, hx, FLOOR - 58, spread=14, seed=1, n=12)
    elif t < hit + 0.58:
        draw_char(img, "housen", hx + 4 * seg(t, hit, hit + 0.28), FLOOR, "hit", t, p=seg(t, hit, hit + 0.38),
                  facing=-1, scale=1.3, flash=max(0, 1 - (t - hit) * 5))
        steam(img, t, hx, FLOOR - 50, spread=16, seed=2, n=12)
    else:
        draw_char(img, "housen", hx + 4, FLOOR, "kneel", t, facing=-1, scale=1.3)
        steam(img, t, hx + 4, FLOOR - 44, spread=14, seed=3, n=12)
        fx.smoke_puff(img, t, hit + 0.58, hx + 4, FLOOR - 1, size=14, seed=91, color=(230, 220, 200))
    # Gintoki
    if r < 0.35:
        draw_char(img, "gintoki", 96, FLOOR, "ready", t, expr="angry")
        blood_trickle(img, 96, FLOOR, 1)
    elif r < 0.42:                                   # crouch...
        draw_char(img, "gintoki", 96, FLOOR, "land", t, p=0.1, expr="angry", dy=2)
        blood_trickle(img, 96, FLOOR + 3, 1)
    elif r < 0.55:                                   # ...and launch straight up
        k = ease_in(seg(r, 0.42, 0.55))
        draw_char(img, "gintoki", 96 + 20 * k, lerp(FLOOR, -10, k), "jump", t, shadow=False)
        fx.smoke_puff(img, t, T9 + 0.42, 96, FLOOR - 2, size=12, seed=92, color=(236, 226, 206))
        d = ImageDraw.Draw(img)
        for i, ox in enumerate((-6, 0, 6)):
            d.line([(96 + ox + 20 * k, lerp(FLOOR, -10, k) + 4), (96 + ox, FLOOR - 4 - 10 * i)],
                   fill=(255, 255, 240))
    elif t < hit:                                    # dive out of the sun
        k = seg(r, 0.98, 1.07)
        x, y = lerp(206, 258, k), lerp(40, 148, k)
        d = ImageDraw.Draw(img)
        for ox in (-3, 3):
            d.line([(x + ox, y - 20), (206 + ox - 20, 40 - 60)], fill=(255, 255, 240))
        draw_char(img, "gintoki", x, y, "attack", t, p=lerp(0.33, 0.5, k), shadow=False)
    elif t < hit + 0.15:
        k2 = seg(t, hit, hit + 0.15)
        draw_char(img, "gintoki", lerp(262, 318, ease_out(k2)), lerp(150, FLOOR, k2), "attack", t,
                  p=lerp(0.55, 0.62, k2), shadow=False)
    else:
        draw_char(img, "gintoki", 318, FLOOR, "attack", t, p=0.9, expr="angry")
        fx.smoke_puff(img, t, hit + 0.15, 318, FLOOR - 2, size=10, seed=93, color=(236, 226, 206))
    if t >= hit:
        fx.slash_arc(img, hx - 4, FLOOR - 40, 34, -120, 70, (t - hit) / 0.18, (255, 255, 255), 4)
        fx.burst(img, t, hit, hx, FLOOR - 40, n=26, colors=[(255, 255, 255), (255, 236, 160)],
                 speed=(80, 220), gravity=60, life=0.5, seed=94)
    B.dust_motes(img, t, count=34, seed=10, color=(255, 246, 210))
    if hit <= t < hit + 0.07:
        impact_silhouettes(img, t, hx)
    else:
        zoom_at(img, 1.35, 196, 120, 192, 112)
        if hit + 0.07 <= t < hit + 0.3:
            fx.flash(img, 0.75 * (1 - seg(t, hit + 0.07, hit + 0.3)))
        if hit + 0.07 <= t < hit + 0.5:
            sfx_text(img, 150, 58, "斩!!", t, hit + 0.07, dur=0.45, size=32, angle=-12, color=(255, 70, 70))
    if r < 0.3:
        fx.flash(img, 1 - ease_out(seg(r, 0.0, 0.3)), (255, 252, 236))
    dx, dy = fx.shake_offset(t, hit, 0.4, 5, seed=9)
    fx.shift(img, dx, dy)


def impact_silhouettes(img, t, hx):
    """Anime impact frame: white void + red focus lines, black silhouettes,
    a white slash cutting through the Night King."""
    img.paste((250, 246, 236), (0, 0, W, H))
    fx.speed_lines(img, t, cx=hx, cy=FLOOR - 40, color=(214, 40, 56), count=44, inner=56, seed=95)
    draw_char(img, "housen", hx - 4, FLOOR, "hit", t, p=0.35, facing=-1, scale=1.3, flash=1.0,
              flash_color=INK, shadow=False)
    draw_char(img, "gintoki", 300, FLOOR - 4, "attack", t, p=0.7, flash=1.0, flash_color=INK, shadow=False)
    d = ImageDraw.Draw(img)
    d.polygon([(hx - 46, FLOOR - 92), (hx - 40, FLOOR - 96), (hx + 44, FLOOR - 4), (hx + 38, FLOOR)],
              fill=(255, 255, 255))
    d.line([(hx - 60, FLOOR - 108), (hx + 58, FLOOR + 8)], fill=(214, 40, 56), width=1)
    zoom_at(img, 1.35, 196, 120, 192, 112)


def shot10(img, t):
    """Housen, face turned up to the sun, crumbles into dust."""
    r = t - T10
    B.street(img, 200, t, tilt=0, mode="sun", leaves_open=1.0, lanterns=False)
    fx.grade(img, (0.78, 0.74, 0.7), (10, 6, 0))
    B.sun_shafts(img, t, 1.0, ox=330, oy=-140, spread=(-0.6, 0.1), n=6, seed=2, alpha=0.36)
    # Gintoki watching, bokuto on the shoulder
    draw_char(img, "gintoki", 70, FLOOR, "shoulder", t, facing=1)
    if r < 1.2:
        p = lerp(0.08, 0.35, seg(r, 0.0, 1.2))
    else:
        p = lerp(0.35, 1.0, ease_in_out(seg(r, 1.2, 2.3)))
    if p < 0.999:
        draw_char(img, "housen", 214, 164, "crumble", t, p=p, facing=1, scale=2, shadow=False)
    # his dust rises into the light
    if r > 1.2:
        B.dust_motes(img, t, count=int(10 + 40 * seg(r, 1.2, 2.0)), seed=13, area=(196, 40, 300, 150),
                     color=(255, 250, 226), rise=26)
    B.dust_motes(img, t, count=40, seed=11, area=(120, 10, 330, 170), color=(255, 244, 214), rise=14)
    u = ease_in_out(seg(r, 1.2, 2.05))
    k = lerp(lerp(1.85, 1.72, seg(r, 0, 1.2)), 1.08, u)
    zoom_at(img, k, lerp(212, 180, u), lerp(104, 110, u), 192, lerp(88, 106, u))
    if r > 2.15:
        fx.sparkle(img, 262, 30, t, T10 + 2.15, size=6, color=(255, 255, 240))
    fx.vignette(img, 0.45, (40, 24, 10))
    fx.letterbox(img, 1.0, bar=18)


def shot11(img, t):
    """Reunion in the sunlight, then the punchline."""
    r = t - T11
    B.street(img, 120, t, tilt=0, mode="sun", leaves_open=1.0)
    C.cherry_tree(img, 368, FLOOR - 2, t, scale=1, tod="day")
    B.sun_shafts(img, t, 1.0, ox=150, oy=-150, n=6, seed=3, alpha=0.26)
    hx = 196
    # Gintoki flat out + Tsukuyo smoking over him
    draw_char(img, "gintoki", 308, FLOOR + 1, "lie", t, expr="hurt")
    draw_char(img, "tsukuyo", 334, FLOOR, "smoke", t, facing=-1)
    draw_char(img, "hinowa", hx, FLOOR, "smile", t, facing=-1)
    if r < 0.5:
        k = seg(r, 0.0, 0.5)
        draw_char(img, "seita", lerp(120, hx - 12, ease_out(k)), FLOOR, "run", t)
    else:
        draw_char(img, "seita", hx - 12, FLOOR, "cry", t)
        for i in range(3):
            t0 = T11 + 0.6 + i * 0.35
            if t >= t0:
                u = ((t - t0) % 1.2) / 1.2
                heart(img, hx - 8 + i * 7 + math.sin(u * 8) * 2, FLOOR - 36 - u * 22)
    if r >= 2.3:                      # Tsukuyo's deadpan sweat drop
        d = ImageDraw.Draw(img)
        yy = FLOOR - 36 + int(min(3, (r - 2.3) * 8))
        d.ellipse([338, yy, 340, yy + 3], fill=(140, 200, 255), outline=(60, 110, 200))
    fx.sakura(img, t, count=34, seed=4, wind=16, fall=16)
    B.dust_motes(img, t, count=20, seed=12, color=(255, 246, 214))
    u = ease_in_out(seg(r, 1.45, 1.85))
    zmap = zoom_at(img, lerp(2.0, 1.85, u), lerp(hx - 6, 314, u), 152, 192, 158)
    if r >= 1.85:
        bx, by = zmap(296, FLOOR - 10)
        speech_bubble(img, int(bx), int(by), "……糖分……", t, T11 + 1.85, tail=(0, 1))


SHOTS = [
    (0.0, 5.45, shot1), (5.45, 8.10, shot2), (8.10, 10.45, shot3), (10.45, 12.75, shot4),
    (12.75, 15.0, shot5), (15.0, 16.55, shot6), (16.55, T8A, shot7), (T8A, T8B, shot8a),
    (T8B, T9, shot8b), (T9, T10, shot9), (T10, T11, shot10), (T11, T_END + 0.01, shot11),
]


class Yoshiwara(Scene):
    id = "s09"
    title = "吉原炎上篇"
    duration = T_END
    music = [(0, "yoshiwara"), (12.75, "battle"), (T8B + 0.55, "epic")]
    music_vol = 0.55
    subs = [
        (3.30, 5.45, "seita", "我想见娘……哪怕一面也好！"),
        (5.95, 8.10, "tsukuyo", "死心吧。吉原……没有太阳。"),
        (8.20, 10.40, None, "晴太的母亲，被囚禁在高塔之上。"),
        (10.50, 12.65, "kamui", "我只对强者感兴趣。"),
        (12.80, 15.00, "housen", "吉原的太阳，只属于我一人。"),
        (17.20, 19.70, "gintoki", "我的剑，是用来守护该守护的东西的。"),
        (T10 + 0.05, T11 - 0.05, "housen", "太阳……原来是这么温暖的东西。"),
        (T11 + 0.15, T11 + 2.15, None, "吉原，终于迎来了太阳。"),
    ]

    def render(self, img, t):
        for t0, t1, fn in SHOTS:
            if t0 <= t < t1:
                fn(img, t)
                break
        # overlays (not zoomed)
        chapter_card(img, t, 0.0, 1.9, "吉原炎上篇", "——没有太阳的地下花街")
        name_card(img, t, 3.40, 2.05, "seita", "晴太", "吉原长大的少年｜想见娘亲", side="left")
        name_card(img, t, 6.0, 2.1, "tsukuyo", "月咏", "百华首领｜死神太夫")
        name_card(img, t, 8.75, 1.70, "hinowa", "日轮", "吉原的太阳｜传说中的花魁", side="left")
        name_card(img, t, 10.55, 2.15, "kamui", "神威", "春雨第七师团团长｜神乐的哥哥")
        name_card(img, t, 13.3, 1.7, "housen", "夜王凤仙", "吉原之主｜夜兔之王", side="left")

    def cues(self):
        c = [
            Cue(0.05, "gong", vol=0.8),
            Cue(0.0, "night", vol=0.35, dur=15.0),
            Cue(1.8, "crowd", vol=0.22, dur=6.3),
            Cue(1.8, "whoosh", vol=0.35, pitch=0.6),
            Cue(3.0, "run", vol=0.5, dur=0.9),
            Cue(3.9, "slide_down", vol=0.35),
            Cue(3.4, "whoosh", vol=0.5),
            # S2
            Cue(S2_KUNAI - 0.2, "shine", vol=0.5, pitch=1.3),
            Cue(S2_KUNAI - 0.09, "whoosh", vol=0.7),
            Cue(S2_KUNAI, "stab"),
            Cue(S2_KUNAI + 0.02, "shock", vol=0.8),
            Cue(S2_DROP, "whoosh", vol=0.6, pitch=0.8),
            Cue(S2_LAND, "land"),
            Cue(6.0, "whoosh", vol=0.4),
            # S3
            Cue(8.15, "bell", vol=0.45),
            Cue(8.75, "whoosh", vol=0.4),
            Cue(9.2, "sparkle", vol=0.4),
            # S4
            Cue(10.45, "wind", vol=0.4, dur=2.3),
            Cue(10.55, "whoosh", vol=0.4),
            Cue(11.9, "shine"),
            Cue(11.9, "sting_dramatic", vol=0.8),
            # S5
            Cue(12.8, "shine", vol=0.7, pitch=0.7),
            Cue(12.8, "heartbeat", vol=0.7),
            Cue(13.1, "gong"),
            Cue(13.1, "aura"),
            Cue(13.15, "fire", vol=0.35, dur=1.85),
            Cue(13.3, "whoosh", vol=0.4),
            # S6
            Cue(15.05, "charge", vol=0.6),
            Cue(15.3, "whoosh"),
            Cue(S6_HIT, "punch_big"),
            Cue(S6_HIT, "impact"),
            Cue(S6_HIT + 0.05, "fly_away", vol=0.6),
        ]
        for wx in S6_WALLS:
            c.append(Cue(s6_wall_time(wx), "crash"))
        c += [
            # S7
            Cue(16.55, "crash"),
            Cue(16.55, "explosion_small", vol=0.7),
            Cue(16.85, "thud"),
            Cue(17.15, "wind", vol=0.35, dur=2.5),
            Cue(17.5, "shing", vol=0.6),
            Cue(18.15, "heartbeat", vol=0.6),
            # S8a lever
            Cue(T8A + 0.02, "squeak", vol=0.5, pitch=0.6),
            Cue(T8A + 0.1, "sweat", vol=0.5),
            Cue(S8_SLAM - 0.1, "whoosh", vol=0.6),
            Cue(S8_SLAM, "clang"),
            Cue(S8_SLAM + 0.02, "impact", vol=0.6),
            Cue(S8_SLAM + 0.05, "engine_hum", vol=0.6, dur=1.6),
            Cue(S8_SLAM + 0.25, "cheer", vol=0.35),
            # S8b the lid (authored at 20.35, shifted)
            Cue(T8B + 0.05, "thunder", vol=0.6),
            Cue(T8B + 0.27, "slide_up", vol=0.7),
            Cue(T8B + 0.55, "shine"),
            Cue(T8B + 0.95, "sparkle"),
            # S9 final strike
            Cue(T9 + 0.05, "fire", vol=0.3, dur=1.0),
            Cue(T9 + 0.42, "jump"),
            Cue(T9 + 0.55, "shine", vol=0.8, pitch=0.8),
            Cue(T9 + 0.95, "whoosh"),
            Cue(S9_HIT, "slash_big"),
            Cue(S9_HIT, "impact"),
            Cue(S9_HIT + 0.15, "land"),
            Cue(S9_HIT + 0.58, "thud"),
            # S10
            Cue(T10, "wind", vol=0.3, dur=T11 - T10),
            Cue(T10 + 1.2, "sparkle", vol=0.5),
            Cue(T10 + 2.15, "twinkle", vol=0.5),
            # S11
            Cue(T11, "run", vol=0.45, dur=0.5),
            Cue(T11 + 0.6, "sparkle", vol=0.5),
            Cue(T11 + 1.85, "pop", vol=0.6),
            Cue(T11 + 2.3, "crow", vol=0.5),
        ]
        return c


SCENE = Yoshiwara()
