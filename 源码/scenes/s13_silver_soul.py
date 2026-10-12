"""s13 银之魂篇 (32.5 s) — music: epic -> sad (Takasugi falls) -> epic (dawn strike).

SHOT LIST
  0.00- 2.00  A  chapter_card 「银之魂篇」; a mothership silhouette creeps down over the
                 card, armada silhouettes cross below, red embers rise.
  2.00- 4.60  B  Edo at night: a colossal mothership sinks over the city (red lights,
                 pulsing core), its shadow darkens Edo while the armada gathers; camera
                 pulls back from its belly to the whole city, searchlights sweep.
                 Narration (2.25-4.50).
  4.60- 5.90  C1 Rooftop: crows scatter, dark wisps spiral in and Utsuro materialises
                 (regen aura, glowing eyes); slow push-in. name_card 虚 (5.35-7.55).
  5.90- 7.60  C2 Bust close-up of Utsuro on a blood-dark backdrop: eyes closed ->
                 6.20 they open blazing red (glint). 「我即是虚。」 (5.85-7.58)
  7.60-13.45  D  ASSEMBLY montage, one rooftop per group, fast cuts with flash
                 transitions, speed lines + slam-in group labels:
                 7.60 真选组 · 8.25 攘夷志士 · 8.90 最强女子 · 9.55 登势酒馆 ·
                 10.20 MADAO gag (1.35 s: record scratch, colour drains, glint,
                 「我、我也来了……」, crow caws 「阿呆～」, sweat drop) ·
                 11.55 快援队 · 12.20 夜兔一族 · 12.85 万事屋 (Sadaharu + Shinpachi).
 13.45-15.50  W  Wide: everyone lands on two roof ridges under the armada;
                 13.85 「全江户，集结！」 slams in, the front row hops (rally).
 15.50-17.50  E1 Gintoki & Takasugi back to back, Naraku creeping in. 「别拖后腿啊，银时。」
 17.50-18.10  E2a Both dash at Utsuro: X-slash -> he just regenerates, smiling.
 18.10-18.55  E2b Utsuro's thrust lunges at Gintoki; Takasugi shoves him aside.
 18.55-19.40  E2c red impact frame (big silhouettes, blade through Takasugi); grey
                 stagger; 18.95 Gintoki shouting close-up 「高杉——！！」 -> music 'sad'.
 19.40-20.65  F  Ash falling: Gintoki kneels, cradling Takasugi, who reaches up.
                 「银时……剩下的，交给你了。」 (19.55-22.10)
 20.65-21.55  FB sepia flash of 松下村塾: kid Takasugi challenges kid Gintoki, kid
                 Katsura watches, Shouyou smiles.
 21.55-23.05  FC closer: last smile (22.15), the hand drops (22.45), colour drains.
 23.05-23.50  F2 Gintoki's bust, eyes in shadow, one tear falls.
 23.50-24.20  G1 He lays Takasugi down and rises; first light; Utsuro waits.
 24.20-24.90  G1b Eye-strip extreme close-up: shadowed -> 24.45 eyes blaze.
 24.90-25.80  G2 Dawn: both dash, 25.45 they pass — impact frame, giant slash line.
 25.80-26.60  G3 Frozen hold back to back (closer); glowing cracks spread over Utsuro.
 26.60-27.80  G4 Utsuro shatters into rising light; the light gathers into Shouyou.
 27.80-29.50  G4b Close-up: Shouyou smiles in the sunrise; 28.90 dissolves into light.
                 「……谢谢。你们都长大了呢。」 (27.05-29.45)
 29.50-32.50  H  Sunrise over Edo: armada retreats; Shinpachi, Gintoki, Kagura and
                 Sadaharu on a rooftop; a purple butterfly (Takasugi's motif) flutters
                 past Gintoki up into the sun. Narration (29.85-32.10).
"""
import math

from PIL import Image, ImageDraw

from engine.core import (Scene, Cue, W, H, seg, lerp, clamp, ease_in, ease_out, ease_in_out,
                         ease_out_back, wave, step_frame, rng, arc)
from engine.gfx import INK, paste, rect, overlay_rect, gradient, shade, tint, scale_nearest, outline
from engine import fx
from engine.text import draw_text, sfx_text, name_card, chapter_card, speech_bubble
from chars import draw_char, render_sprite
from bg import common as C, edo as E
from scenes import _s13_art as A

FLOOR = 160
DUR = 32.5

# ---------------------------------------------------------------- timing
T_B = 2.00
T_C1, T_NC, T_C2, T_OPEN = 4.60, 5.35, 5.90, 6.20
T_D = 7.60
CUTS = [(7.60, "ssg"), (8.25, "joui"), (8.90, "women"), (9.55, "otose"), (10.20, "madao"),
        (11.55, "kaien"), (12.20, "yato"), (12.85, "yorozuya")]
T_W, T_SLAM = 13.45, 13.85
T_E1 = 15.50
T_E2, T_X, T_E2B, T_IMP, T_SHOCK = 17.50, 17.80, 18.10, 18.55, 18.95
T_F, T_FB, T_FC, T_SMILE, T_DROP, T_F2 = 19.40, 20.65, 21.55, 22.15, 22.45, 23.05
T_G1, T_EYE, T_GLARE = 23.50, 24.20, 24.45
T_G2, T_DASH, T_STRIKE = 24.90, 24.95, 25.45
T_G3, T_CRACK, T_SHAT, T_FACE, T_G4B, T_FADE = 25.80, 26.05, 26.60, 26.95, 27.80, 28.90
T_H = 29.50

_CACHE = {}


def _cached(key, fn):
    v = _CACHE.get(key)
    if v is None:
        v = fn()
        _CACHE[key] = v
    return v


def _grad(key, top, bot, steps=8):
    def build():
        im = Image.new("RGB", (W, H))
        gradient(im, 0, 0, W, H, top, bot, steps=steps)
        return im
    return _cached(("grad", key), build)


# ================================================================ A: chapter card
def overlay_chapter(img, t):
    chapter_card(img, t, 0.0, T_B, "银之魂篇", "最终章·江户最漫长的一夜")
    a = min(seg(t, 0, 0.15), 1 - seg(t, T_B - 0.2, T_B))
    if a < 0.5:
        return
    sil = A.ship_silhouette("mothership", 1, (52, 30, 62))
    rim = A.ship_silhouette("mothership", 1, (150, 36, 60))
    y = lerp(-sil.height + 8, -sil.height + 44, ease_out(seg(t, 0, T_B)))
    x0 = W // 2 - sil.width // 2
    paste(img, rim, x0, int(y) + 2)
    paste(img, sil, x0, int(y))
    C.add_sprite(img, C.glow_sprite(22, (255, 60, 90), 0.6 + 0.3 * math.sin(t * 5)), W // 2 - 22,
                 int(y) + sil.height - 30)
    d = ImageDraw.Draw(img)
    for i in range(9):
        lx = x0 + 14 + i * (sil.width - 28) / 8
        on = (step_frame(t, 6) + i) % 3 != 0
        if on:
            yy0 = int(y) + sil.height - 12
            d.rectangle([int(lx), yy0, int(lx) + 1, yy0 + 1], fill=(255, 70, 90))
    for i, (kind, yy, sp, xx) in enumerate((("cruiser", 186, 22, 420), ("pirate", 198, 16, 250),
                                             ("cruiser", 178, 12, 120), ("saucer", 170, 30, 330))):
        s2 = A.ship_silhouette(kind, 1, (34, 26, 50))
        x = (xx - t * sp) % (W + s2.width + 40) - s2.width - 20
        paste(img, s2, int(x), yy - s2.height // 2)
        rect(img, int(x) + 4, yy, 2, 1, (255, 80, 80) if step_frame(t, 4) % 2 else (120, 40, 50))
    fx.embers(img, t, count=26, seed=2, area=(0, 162, W, H),
              colors=((255, 90, 60), (255, 150, 80), (200, 40, 50)))


# ================================================================ B: armada
def shot_B(img, t):
    tt = max(t, T_B - 0.3)
    dens = lerp(0.4, 1.0, ease_in_out(seg(tt, T_B - 0.3, T_B + 1.5)))
    dy = int(round(lerp(14, 0, ease_in_out(seg(tt, T_B - 0.2, T_C1 - 0.4)))))
    cam = lerp(-50, -10, seg(tt, T_B - 0.3, T_C1))
    A.edo_bg(img, t, cam, "night", armada=dens, near=True, dy=dy)
    # the colossal mothership sinks over the city and its shadow swallows Edo
    shadow = ease_in_out(seg(tt, T_B, T_C1 - 0.2))
    overlay_rect(img, 0, 0, W, H, (18, 6, 26), 0.32 * shadow)
    mb = lerp(40, 66, ease_out(seg(tt, T_B - 0.3, T_C1)))
    mx = W / 2 + 40 - cam * 0.04
    _, mh = E.ship_size("mothership", 2)
    E.ship(img, mx, mb - mh / 2, "mothership", t, scale=2, tod="night", haze=0.05)
    A.searchlights(img, t, base_y=146 + dy)
    # reveal: start on the mothership's glowing belly, pull back to the whole city
    z = lerp(1.9, 1.0, ease_in_out(seg(tt, T_B - 0.1, T_B + 1.9)))
    A.zoom(img, z, mx, 40)
    dx, dy2 = fx.shake_offset(t, T_B + 0.1, 1.6, amp=2, freq=18, seed=3)
    fx.shift(img, dx, dy2)


# ================================================================ C: Utsuro
def shot_C1(img, t):
    u = t - T_C1
    cam = 140 + u * 5
    A.edo_bg(img, t, cam, "night", 1.0)
    A.fire_glow(img, t, 100, 150, 0.6)
    E.roof_walk(img, cam, FLOOR, t, "night")
    ux, uy = 160, 142
    # a murder of crows bursts away
    for i in range(10):
        r = rng("c1crow", i)
        a = r.uniform(-2.9, -0.25)
        v = r.uniform(70, 140)
        d = u - r.uniform(0, 0.12)
        if d < 0:
            continue
        cx, cy = ux + math.cos(a) * v * d, uy - 6 + math.sin(a) * v * d - 14 * d
        A.crow(img, cx, cy, t, i, facing=1 if math.cos(a) > 0 else -1)
    # dark wisps spiral in
    dd = ImageDraw.Draw(img)
    for i in range(18):
        r = rng("c1wisp", i)
        k = ease_in(seg(u, r.uniform(0, 0.15), 0.6))
        if k >= 1:
            continue
        ang = r.uniform(0, 6.28) + u * 5
        rad = r.uniform(34, 70) * (1 - k)
        for j in range(3):
            aa = ang - j * 0.18
            x, y = int(ux + math.cos(aa) * rad), int(uy + math.sin(aa) * rad * 0.7)
            c = ((120, 50, 140), (80, 30, 100), (50, 20, 70))[j]
            dd.rectangle([x, y, x + (1 if j else 2) - 1, y + (1 if j else 2) - 1], fill=c)
    fx.burst(img, t, T_C1 + 0.6, ux, uy, n=22, colors=[(140, 60, 160), (60, 20, 80), (255, 70, 90)],
             speed=(30, 90), gravity=-20, life=0.7, size=(1, 2), seed=41)
    form = seg(u, 0.3, 0.8)
    if form > 0:
        draw_char(img, "utsuro", ux, FLOOR, "regen", t, flash=1 - form, flash_color=(10, 4, 16),
                  alpha=min(1.0, form * 2.5), facing=1)
    z = lerp(1.95, 2.25, ease_in_out(seg(t, T_C1, T_C2)))
    A.zoom(img, z, ux, 134)
    fx.embers(img, t, 22, seed=13, colors=((255, 80, 70), (180, 40, 60), (255, 150, 90)))


def shot_C2(img, t):
    u = t - T_C2
    img.paste(_grad("c2", (58, 10, 30), (10, 6, 18), 7))
    C.add_sprite(img, C.glow_sprite(70, (170, 30, 60), 0.9), 100 - 70, 110 - 70)
    fx.embers(img, t, 30, seed=21, colors=((255, 70, 80), (130, 30, 60), (200, 60, 90)), rise=24)
    # drifting black feathers
    d = ImageDraw.Draw(img)
    for i in range(7):
        r = rng("c2feather", i)
        x = (r.uniform(0, W) + t * 10 + wave(t, 0.4, 8, r.random())) % W
        y = (r.uniform(0, H) + t * 16) % (H + 10) - 5
        sw = step_frame(t + i * 0.1, 4, 2)
        d.line([(x, y), (x + 3, y + (1 if sw else -1))], fill=(14, 10, 20))
        d.point((x + 1, y + 1 if sw else y - 1), fill=(40, 30, 50))
    expr = "blink" if u < T_OPEN - T_C2 else "glow"
    bob = 1 if step_frame(t, 2) % 2 else 0
    res = A.bust(img, "utsuro", t, expr, cx=100, top=76 + bob, k=4, facing=1, pose="idle", crop=0.7)
    if res and u >= T_OPEN - T_C2:
        x0, y0, k, bb = res
        for ex in (x0 + 34, x0 + 58):
            fx.sparkle(img, ex, y0 + 50, t, T_OPEN, size=7, color=(255, 150, 150))
    z = lerp(1.0, 1.08, ease_in_out(seg(t, T_C2, T_D)))
    A.zoom(img, z, 100, 120)
    if u >= T_OPEN - T_C2:
        fx.flash(img, 0.5 * (1 - seg(t, T_OPEN, T_OPEN + 0.15)), (255, 60, 80))


# ================================================================ D: montage
def cut_bg(img, t, cam, tint_col, lines_col, cx=192, cy=134, lines=0.35):
    A.edo_bg(img, t, cam, "night", 1.0)
    E.roof_walk(img, cam, FLOOR, t, "night")
    overlay_rect(img, 0, 0, W, H, tint_col, 0.18)
    if lines_col:
        A.soft_speed_lines(img, t, cx, cy, lines_col, lines, count=40, inner=56, seed=int(cam))


def drop(img, cid, x, u, tl, pose, t, p=None, facing=1, fall=0.14, h0=90, y=FLOOR, hop=0, **kw):
    """Character drops in from above and lands at local time tl."""
    if u < tl - fall:
        return
    if u < tl:
        k = seg(u, tl - fall, tl)
        yy = y - h0 * (1 - ease_in(k))
        draw_char(img, cid, x, yy, "jump", t, facing=facing, shadow=False, **{k2: v for k2, v in kw.items() if k2 != "expr"})
    elif u < tl + 0.08:
        draw_char(img, cid, x, y, "land", t, p=seg(u, tl, tl + 0.08), facing=facing,
                  **{k2: v for k2, v in kw.items() if k2 != "expr"})
    else:
        draw_char(img, cid, x, y - hop, pose, t, p=p, facing=facing, shadow=hop < 2, **kw)


def dust(img, t, t_abs, x, y=FLOOR, size=7, seed=0):
    fx.smoke_puff(img, t, t_abs, x - 5, y - 1, size=size, seed=seed, color=(150, 146, 170))
    fx.smoke_puff(img, t, t_abs, x + 5, y - 1, size=size, seed=seed + 1, color=(120, 116, 140))


def cut_ssg(img, t, u, dur, t0):
    cut_bg(img, t, 40, (30, 40, 100), (130, 150, 230))
    A.makoto_flag(img, 126, FLOOR, t)
    drop(img, "hijikata", 164, u, 0.10, "draw", t, p=0.3 + 0.7 * seg(u, 0.2, 0.5))
    drop(img, "kondo", 194, u, 0.14, "ready", t)
    drop(img, "okita", 228, u, 0.18, "bazooka", t, p=0.2)
    for i, (x, tl) in enumerate(((164, 0.10), (194, 0.14), (228, 0.18))):
        dust(img, t, t0 + tl, x, seed=10 + i * 2)
    A.zoom(img, lerp(1.7, 1.82, u / dur), 194, 134)
    A.group_label(img, u - 0.04, "真选组", "近藤·土方·冲田", (40, 52, 120))


def cut_joui(img, t, u, dur, t0):
    cut_bg(img, t, 270, (30, 60, 150), (150, 190, 255))
    for i, (x, s) in enumerate(((100, "桂先生"), (146, "攘夷"), (234, "天诛"), (274, "天诛"))):
        draw_char(img, "elizabeth", x, FLOOR, "sign", t + i * 0.23, p=seg(u, 0.04 + i * 0.05, 0.34 + i * 0.05),
                  facing=1, sign=s)
    drop(img, "katsura", 197, u, 0.12, "ready", t)
    dust(img, t, t0 + 0.12, 197, seed=20)
    A.zoom(img, lerp(1.5, 1.6, u / dur), 196, 128)
    A.group_label(img, u - 0.04, "攘夷志士", "桂小太郎＆伊丽莎白军团", (36, 70, 160))


def cut_women(img, t, u, dur, t0):
    cut_bg(img, t, 620, (120, 30, 100), (255, 160, 220))
    drop(img, "otae", 164, u, 0.10, "ready", t, expr="dark_smile")
    drop(img, "tsukuyo", 214, u, 0.14, "throw_kunai", t, p=seg(u, 0.18, 0.55))
    dust(img, t, t0 + 0.10, 164, seed=30)
    dust(img, t, t0 + 0.14, 214, seed=32)
    A.zoom(img, lerp(1.75, 1.85, u / dur), 190, 134)
    A.group_label(img, u - 0.04, "最强女子", "月咏·阿妙", (140, 36, 110))


def cut_otose(img, t, u, dur, t0):
    cut_bg(img, t, 760, (150, 90, 30), (255, 214, 150))
    draw_char(img, "catherine", 160, FLOOR, "point", t, p=seg(u, 0.1, 0.35))
    draw_char(img, "otose", 193, FLOOR, "smoke", t + 0.6)
    draw_char(img, "tama", 227, FLOOR, "mop_shoot", t)
    z = lerp(1.45, 1.8, ease_out(clamp(u / dur)))
    A.zoom(img, z, 194, 134)
    A.group_label(img, u - 0.04, "登势酒馆", "登势·凯瑟琳·小玉", (150, 92, 36))


def cut_madao(img, t, u, dur, t0):
    """The montage screeches to a halt: MADAO in his box. Nobody reacts; a crow does."""
    cut_bg(img, t, 980, (60, 60, 70), None)
    fx.grayscale(img, 0.55)
    sad = u > 0.95
    draw_char(img, "hasegawa", 194, FLOOR, "box", t, expr="cry" if sad else "sad")
    # the awkward crow crosses the frame (drawn pre-zoom so it's big enough to read)
    z = lerp(1.8, 1.95, u / dur)
    A.zoom(img, z, 194, 136)
    fx.sparkle(img, 186, 104, t, t0 + 0.14, size=6)
    if u > 0.22:
        speech_bubble(img, 206, 92, "我、我也来了……", t, t0 + 0.22, tail=(-1, 1), max_w=120, typewriter=False)
    # the awkward crow flaps across behind him: 「阿呆～」
    ck = seg(u, 0.5, dur)
    if 0 < ck < 1:
        cx, cy = lerp(W + 10, -40, ck), 40 + wave(t, 2, 3)
        A.crow(img, cx, cy, t, 3, facing=-1, s=3, rim=(150, 150, 160))
        sfx_text(img, int(cx) + 12, int(cy) - 12, "阿呆～", t, t0 + 0.62, dur=0.66, color=(236, 236, 240),
                 size=16, angle=6, shake=0)
    if sad:
        # a fat sweat drop slides down beside his head
        k = seg(u, 0.95, dur)
        A.sweat_drop(img, 222, lerp(90, 100, ease_out(k)))
    A.group_label(img, u - 0.04, "MADAO", "长谷川泰三（也来了）", (80, 80, 92))


def cut_kaien(img, t, u, dur, t0):
    cut_bg(img, t, 1200, (130, 30, 30), (255, 150, 130), cy=110)
    k = ease_out(seg(u, 0.0, 0.42))
    sx, sy = lerp(-80, 214, k), 92 + wave(t, 0.8, 2)
    bx, by = A.kaien_ship(img, sx, sy, t)
    draw_char(img, "sakamoto", bx - 4, by, "laugh", t, shadow=False)
    if u < 0.42:
        fx.motion_lines(img, t, (255, 220, 200), count=10, direction=-1, seed=7, y0=60, y1=130, speed=700)
    A.zoom(img, 1.3, 214, 108)
    A.group_label(img, u - 0.04, "快援队", "坂本辰马", (170, 40, 40))


def cut_yato(img, t, u, dur, t0):
    cut_bg(img, t, 1420, (160, 56, 30), (255, 180, 120))
    tl = 0.14
    if u >= tl:
        r = (u - tl) * 260
        if r < 150:
            dd = ImageDraw.Draw(img)
            dd.ellipse([194 - r, FLOOR - r * 0.18, 194 + r, FLOOR + r * 0.18], outline=(255, 230, 190), width=2)
    drop(img, "kagura", 160, u, tl, "umbrella_shoot", t, h0=110)
    drop(img, "kamui", 194, u, tl, "ready", t, h0=110)
    drop(img, "umibozu", 228, u, tl, "umbrella_open", t, h0=110)
    for i, x in enumerate((160, 194, 228)):
        dust(img, t, t0 + tl, x, size=9, seed=40 + i * 2)
    fx.burst(img, t, t0 + tl, 194, FLOOR - 2, n=18, colors=[(120, 110, 130), (80, 70, 90)],
             speed=(40, 110), gravity=260, life=0.5, spread=(200, 340), seed=44)
    A.zoom(img, lerp(1.7, 1.8, u / dur), 194, 132)
    dx, dy = fx.shake_offset(t, t0 + tl, 0.3, amp=3, seed=45)
    fx.shift(img, dx, dy)
    A.group_label(img, u - 0.04, "夜兔一族", "神乐·神威·星海坊主", (190, 60, 36))


def cut_yorozuya(img, t, u, dur, t0):
    cut_bg(img, t, 1650, (60, 90, 160), (200, 230, 255))
    tl = 0.28
    if u < tl:
        x, y = arc((30, FLOOR), (196, FLOOR), ease_out(u / tl), 36)
        pose = "run"
    else:
        x, y = 196, FLOOR
        pose = "bark" if u > tl + 0.06 else "land"
    # Shinpachi rides on Sadaharu's back
    draw_char(img, "sadaharu", x, y, pose, t, p=None if pose != "land" else seg(u, tl, tl + 0.06))
    draw_char(img, "shinpachi", x - 6, y - 30 + (1 if pose == "run" and step_frame(t, 8) % 2 else 0),
              "ready", t, shadow=False)
    dust(img, t, t0 + tl, 196, size=10, seed=50)
    A.zoom(img, lerp(1.55, 1.65, u / dur), 190, 128)
    A.group_label(img, u - 0.04, "万事屋", "新八·定春", (60, 100, 170))


CUT_FN = {"ssg": cut_ssg, "joui": cut_joui, "women": cut_women, "otose": cut_otose, "madao": cut_madao,
          "kaien": cut_kaien, "yato": cut_yato, "yorozuya": cut_yorozuya}


def shot_D(img, t):
    for i, (t0, key) in enumerate(CUTS):
        t1 = CUTS[i + 1][0] if i + 1 < len(CUTS) else T_W
        if t0 <= t < t1:
            u = t - t0
            CUT_FN[key](img, t, u, t1 - t0, t0)
            if u < 0.07:
                fx.flash(img, 0.8 * (1 - u / 0.07))
            return


# ================================================================ W: 全江户，集结！
BACK = [("elizabeth", 26, 1, "sign", {"sign": "天诛"}), ("hasegawa", 54, 1, "idle", {}),
        ("otose", 82, 1, "smoke", {}), ("catherine", 108, 1, "idle", {}), ("tama", 134, 1, "idle", {}),
        ("kamui", 250, -1, "ready", {}), ("umibozu", 278, -1, "idle", {}), ("sakamoto", 306, -1, "laugh", {}),
        ("elizabeth", 330, 1, "sign", {"sign": "攘夷"}), ("elizabeth", 360, 1, "sign", {"sign": "天诛"})]
FRONT = [("okita", 34, 1, "bazooka", {"p": 0.2}), ("hijikata", 62, 1, "ready", {}), ("kondo", 90, 1, "ready", {}),
         ("katsura", 118, 1, "ready", {}), ("shinpachi", 150, 1, "ready", {}), ("gintoki", 192, 1, "ready", {}),
         ("kagura", 230, -1, "umbrella_open", {}), ("sadaharu", 270, -1, "idle", {}), ("otae", 312, -1, "ready", {}),
         ("tsukuyo", 346, -1, "arms_crossed", {})]


def shot_W(img, t):
    u = t - T_W
    cam = lerp(70, 96, u / (T_E1 - T_W))
    A.edo_bg(img, t, cam, "night", 1.0)
    A.fire_glow(img, t, 100, 150, 0.5)
    E.roof_walk(img, cam * 0.8, 118, t, "night")
    for i, (cid, x, f, pose, kw) in enumerate(BACK):
        kw = dict(kw)
        p = kw.pop("p", None)
        hop = int(round(3 * math.sin(math.pi * seg(t, T_SLAM + 0.08 + i * 0.025, T_SLAM + 0.3 + i * 0.025))))
        drop(img, cid, x, u, 0.08 + (i % 5) * 0.05, pose, t + i * 0.17, p=p, facing=f, y=118, h0=60, fall=0.1,
             hop=hop, flash=0.28, flash_color=(34, 26, 64), **kw)
    E.roof_walk(img, cam, 166, t, "night")
    for i, (cid, x, f, pose, kw) in enumerate(FRONT):
        kw = dict(kw)
        p = kw.pop("p", None)
        tl = 0.1 + (abs(i - 5) * 0.045)
        # rally: the whole front row hops when the title slams (centre first, outwards)
        ts = T_SLAM + 0.05 + abs(i - 5) * 0.03
        hop = int(round(4 * math.sin(math.pi * seg(t, ts, ts + 0.24))))
        drop(img, cid, x, u, tl, pose, t + i * 0.13, p=p, facing=f, y=166, h0=70, fall=0.1, hop=hop, **kw)
        dust(img, t, T_W + tl, x, y=166, size=5, seed=60 + i * 2)
    z = lerp(1.0, 1.16, ease_in_out(seg(t, T_SLAM + 0.3, T_E1)))
    A.zoom(img, z, 192, 128)
    A.slam_text(img, t, T_SLAM, "全江户，集结！", W // 2, 36, size=42)
    if t >= T_SLAM:
        fx.flash(img, 0.6 * (1 - seg(t, T_SLAM, T_SLAM + 0.15)))
    dx, dy = fx.shake_offset(t, T_SLAM, 0.45, amp=4, seed=61)
    fx.shift(img, dx, dy)


# ================================================================ E: back to back / Takasugi
def battle_bg(img, t, cam, glow=0.9):
    A.edo_bg(img, t, cam, "night", 1.0)
    A.fire_glow(img, t, 96, 150, glow)
    E.roof_walk(img, cam, FLOOR, t, "night")


T_ATK = T_E1 + 1.05          # the Naraku rush in from both sides ...
T_CUT = T_E1 + 1.25          # ... and are cut down in one mirrored slash


def shot_E1(img, t):
    u = t - T_E1
    battle_bg(img, t, 60 + u * 5)
    for i, (x, f) in enumerate(((88, 1), (116, 1), (268, -1), (296, -1))):
        if t < T_ATK:            # the ring tightens
            xx = x + ease_in_out(seg(t, T_E1, T_ATK)) * 8 * f + wave(t, 0.5, 1.5, x * 0.01)
            draw_char(img, "naraku", xx, FLOOR, "ready", t + x * 0.013, facing=f,
                      flash=0.45, flash_color=(16, 10, 26))
        elif t < T_CUT:          # rush
            k = ease_in(seg(t, T_ATK, T_CUT))
            draw_char(img, "naraku", x + (8 + 34 * k) * f, FLOOR, "attack", t, p=0.1 + 0.25 * k, facing=f,
                      flash=0.45, flash_color=(16, 10, 26))
        else:                    # blown away
            k2 = seg(t, T_CUT, T_CUT + 0.45 + i % 2 * 0.1)
            dist = (70 + (1 - i % 2) * 30) * ease_out(k2)
            hgt = (26 + i * 3) * math.sin(math.pi * k2)
            xx, yy = x + 42 * f - dist * f, FLOOR - hgt
            if k2 < 1:
                draw_char(img, "naraku", xx, yy, "fly", t + i * 0.1, facing=f, shadow=False,
                          flash=0.8 if t < T_CUT + 0.06 else 0.45,
                          flash_color=(255, 255, 255) if t < T_CUT + 0.06 else (16, 10, 26))
            else:
                draw_char(img, "naraku", xx, FLOOR, "lie", t, facing=f, flash=0.45, flash_color=(16, 10, 26))
    if t < T_CUT - 0.08:
        draw_char(img, "gintoki", 181, FLOOR, "ready", t, facing=-1)
        draw_char(img, "takasugi", 204, FLOOR, "ready", t + 0.2, facing=1)
    else:
        p = 0.35 + 0.65 * seg(t, T_CUT - 0.08, T_CUT + 0.12)
        draw_char(img, "gintoki", 181, FLOOR, "attack", t, p=p, facing=-1)
        draw_char(img, "takasugi", 204, FLOOR, "attack", t, p=p, facing=1)
    for sx, sd in ((150, 1), (236, 2)):
        fx.burst(img, t, T_CUT, sx, 140, n=10, colors=[(255, 255, 255), (200, 200, 230)], speed=(40, 100),
                 gravity=80, life=0.35, size=(1, 2), seed=120 + sd)
    z = lerp(1.6, 1.85, ease_in_out(seg(t, T_E1, T_E2)))
    A.zoom(img, z, 192, 134)
    fx.sparkle(img, 108, 116, t, T_E1 + 0.1, size=5)
    fx.sparkle(img, 280, 116, t, T_E1 + 0.18, size=5)
    fx.embers(img, t, 30, seed=5, area=(0, 40, W, H))
    if T_CUT <= t < T_CUT + 0.1:
        fx.flash(img, 0.55 * (1 - seg(t, T_CUT, T_CUT + 0.1)))
    dx, dy = fx.shake_offset(t, T_CUT, 0.3, amp=3, seed=121)
    fx.shift(img, dx, dy)
    fx.letterbox(img, 1.0, 12)


def shot_E2a(img, t):
    battle_bg(img, t, 100)
    ux = 252
    gx = lerp(118, 224, ease_out(seg(t, T_E2, T_E2 + 0.2)))
    kx = lerp(90, 204, ease_out(seg(t, T_E2 + 0.03, T_E2 + 0.24)))
    if t < T_E2 + 0.22:
        fx.motion_lines(img, t, (220, 210, 240), count=12, direction=-1, seed=71, y0=110, y1=165, speed=800)
    # Utsuro: waits -> is cut (red flash) -> regenerates, smiling
    if t < T_X:
        draw_char(img, "utsuro", ux, FLOOR, "idle", t, facing=-1, expr="smile")
    elif t < T_X + 0.1:
        draw_char(img, "utsuro", ux + 2, FLOOR, "hit", t, p=0.25, facing=-1, flash=0.7, flash_color=(255, 60, 80))
    else:
        draw_char(img, "utsuro", ux, FLOOR, "regen", t, facing=-1, expr="smile")
    if t < T_E2 + 0.18:
        draw_char(img, "takasugi", kx, FLOOR, "run", t, facing=1)
        draw_char(img, "gintoki", gx, FLOOR, "run", t, facing=1)
    else:
        draw_char(img, "takasugi", kx, FLOOR, "slash_up", t, p=seg(t, T_E2 + 0.2, T_X + 0.2), facing=1)
        draw_char(img, "gintoki", gx, FLOOR, "attack", t, p=0.25 + 0.75 * seg(t, T_E2 + 0.18, T_X + 0.25), facing=1)
    A.x_slash(img, ux, 140, t, T_X, size=16)
    fx.burst(img, t, T_X, ux, 140, n=14, colors=[(255, 255, 255), (255, 120, 130)], speed=(40, 110),
             gravity=60, life=0.35, seed=73)
    A.zoom(img, 1.6, 210, 134)
    dx, dy = fx.shake_offset(t, T_X, 0.3, amp=4, seed=72)
    fx.shift(img, dx, dy)
    fx.letterbox(img, 1.0, 12)


def _e2b_frame(img, t, lines=False):
    battle_bg(img, t, 110, 1.0)
    if lines:
        fx.motion_lines(img, t, (255, 220, 230), count=14, direction=-1, seed=81, y0=120, y1=160, speed=900)
    lunge = ease_in(seg(t, T_E2B + 0.16, T_IMP - 0.04))
    ux = lerp(280, 252, lunge)
    gx = lerp(214, 188, ease_out(seg(t, T_E2B + 0.2, T_IMP)))
    kx = lerp(192, 226, ease_out(seg(t, T_E2B + 0.12, T_IMP - 0.06)))
    shoved = t > T_E2B + 0.2

    def gin():
        draw_char(img, "gintoki", gx, FLOOR, "hit" if shoved else "attack", t, p=0.35 if shoved else 1.0,
                  facing=1, expr="shock" if shoved else None)

    # Takasugi runs up behind him, shoves him clear and braces in his place
    if not shoved:
        draw_char(img, "takasugi", kx, FLOOR, "run", t, facing=1, expr="determined")
        gin()
    else:
        gin()
        if t < T_IMP - 0.12:
            draw_char(img, "takasugi", kx, FLOOR, "run", t, facing=1, expr="determined")
        else:
            draw_char(img, "takasugi", kx, FLOOR, "guard", t, facing=1, expr="determined", arm_b=-70)
    draw_char(img, "utsuro", ux, FLOOR, "thrust", t, p=seg(t, T_E2B, T_E2B + 0.3), facing=-1, expr="glow")
    return ux


def shot_E2b(img, t):
    _e2b_frame(img, t, lines=t > T_E2B + 0.15)
    A.zoom(img, lerp(1.9, 2.2, seg(t, T_E2B, T_IMP)), 226, 134)
    fx.letterbox(img, 1.0, 12)


def shot_E2c(img, t):
    if t < T_IMP + 0.13:
        # stylised red impact frame: black silhouettes, the blade runs clean through him
        img.paste((226, 34, 54), (0, 0, W, H))
        fx.speed_lines(img, t, 190, 120, color=(20, 8, 16), count=56, inner=78, seed=95)
        ink, rim = (14, 8, 14), (255, 236, 236)
        TX, UX, FY = 170, 268, 204
        tk, tax, tay, _ = A.sil_sprite("takasugi", "hit", T_IMP, 0.2, "hurt", 1, 3, ink, sheathed=False)
        uk, uax, uay, blade = A.sil_sprite("utsuro", "thrust", T_IMP, 0.5, "glow", -1, 3, ink,
                                           keep=A.BLADE_COLS, keep_color=(255, 255, 255),
                                           glow=A.UTSURO_EYES, glow_color=(255, 250, 200))
        paste(img, outline(tk, rim), TX - tax - 1, FY - tay - 1)
        d = ImageDraw.Draw(img)
        if blade:
            bx0, bx1, by = blade
            yb = FY - uay + by
            hand = UX - uax + bx1
            tip = TX - 44
            d.line([(tip, yb), (hand, yb)], fill=INK, width=5)
            d.line([(tip, yb), (hand, yb)], fill=(255, 255, 255), width=3)
            d.polygon([(tip - 6, yb), (tip, yb - 2), (tip, yb + 2)], fill=(255, 255, 255), outline=INK)
            # a few stylised red drops fly off his back
            for i in range(6):
                r = rng("e2cdrop", i)
                px, py = tip + r.uniform(4, 30), yb + r.uniform(-14, 10)
                sz = 2 if i % 2 else 3
                d.rectangle([px, py, px + sz, py + sz], fill=(120, 0, 16))
        paste(img, outline(uk, rim), UX - uax - 1, FY - uay - 1)
        rect(img, 0, 0, W, 12, (0, 0, 0))
        rect(img, 0, H - 12, W, 12, (0, 0, 0))
        return
    if t < T_SHOCK:
        u = t - (T_IMP + 0.13)
        battle_bg(img, T_IMP, 110, 1.0)
        draw_char(img, "gintoki", 188, FLOOR, "hit", T_IMP, p=0.4, facing=1, expr="shock")
        draw_char(img, "takasugi", 226 - u * 10, FLOOR, "hit", T_IMP, p=0.15 + u * 0.8, facing=1, expr="hurt")
        draw_char(img, "utsuro", 252, FLOOR, "thrust", T_IMP, p=0.5, facing=-1, expr="glow")
        fx.burst(img, t, T_IMP + 0.13, 222, 142, n=7, colors=[(200, 30, 50), (150, 20, 40)],
                 speed=(10, 40), gravity=120, life=0.5, size=(1, 1), seed=91)
        A.zoom(img, 2.3 + u * 0.4, 220, 136)
        fx.grayscale(img, 0.7)
        fx.grade(img, (1.1, 0.8, 0.8), (10, 0, 0))
        fx.flash(img, 0.8 * (1 - seg(t, T_IMP + 0.13, T_IMP + 0.3)))
        fx.letterbox(img, 1.0, 12)
        return
    # Gintoki shock close-up
    img.paste((250, 246, 240), (0, 0, W, H))
    fx.speed_lines(img, t, 150, 110, color=(24, 20, 37), count=60, inner=74, seed=93)
    A.head_big(img, "gintoki", "shout", 140 + int(wave(t, 14, 1)), 112, 6)
    A.zoom(img, lerp(1.0, 1.08, seg(t, T_SHOCK, T_F)), 140, 110)
    sfx_text(img, 286, 70, "高杉——！！", t, T_SHOCK + 0.06, dur=0.5, color=(214, 28, 48),
             outline=INK, size=28, face="brush", angle=-6, shake=2)


# ================================================================ F: in Gintoki's arms
PIETA_X = 206


def pieta(img, t, ex, arm, gex="sad", g_head=2):
    """Gintoki kneels (facing left), his arm behind the fallen Takasugi, whose
    upper body is cradled up against him."""
    gx = PIETA_X
    breath = 1 if step_frame(t, 2) % 2 else 0
    overlay_rect(img, gx - 60, FLOOR - 1, 72, 2, (0, 0, 0), 0.3)
    draw_char(img, "gintoki", gx, FLOOR, "kneel", t, facing=-1, expr=gex, arm_f=80, arm_b=40,
              head_dy=g_head + breath, weapon=None, shadow=False)
    spr, ax, ay = render_sprite("takasugi", "idle", 0.0, None, ex, -1, rot=62, sheathed=False,
                                arm_f=arm, arm_b=-20, legs="stand", bob=0)
    spr = spr.crop(spr.getbbox())
    paste(img, spr, gx - 6 - spr.width, FLOOR - spr.height + 1 + (breath if ex != "sleep" else 0))


def _tk_expr(t):
    if t < T_F + 0.2:
        return "hurt"
    if t < T_F + 0.95:
        return "talk" if step_frame(t, 7) % 2 == 0 else "sad"
    if t < T_SMILE:
        return "blink" if (t % 1.7) < 0.14 else "sad"
    if t < T_DROP:
        return "happy"
    return "sleep"


def _tk_arm(t):
    """His hand rises weakly toward Gintoki's face ... and falls."""
    arm = lerp(20, 150, ease_in_out(seg(t, T_F + 0.3, T_FB)))
    if t >= T_DROP:
        arm = lerp(150, -70, ease_in(seg(t, T_DROP, T_DROP + 0.14)))
    return arm


def shot_F(img, t):
    battle_bg(img, t, 150, 0.5)
    C.add_sprite(img, C.glow_sprite(34, (255, 140, 90), 0.35), PIETA_X - 18 - 34, 146 - 34)
    pieta(img, t, _tk_expr(t), _tk_arm(t))
    z = lerp(2.6, 2.8, ease_in_out(seg(t, T_F, T_FB)))
    A.zoom(img, z, PIETA_X - 18, 144)
    fx.grayscale(img, 0.35)
    A.ash(img, t, 50, seed=3)
    fx.letterbox(img, 1.0, 22)


def shot_FB(img, t):
    """Sepia flash of the old days at Shoka Sonjuku."""
    u = t - T_FB
    A.dojo_bg(img, t)
    draw_char(img, "katsura_kid", 116, 150, "sit", t, facing=1)
    draw_char(img, "shouyou", 266, 146, "smile", t, facing=-1)
    clash = T_FB + 0.24
    k = ease_out(seg(t, T_FB, clash))
    tx, gx = lerp(140, 172, k), lerp(236, 206, k)
    if t < clash:
        draw_char(img, "takasugi_kid", tx, 152, "run", t, facing=1, expr="angry")
        draw_char(img, "gintoki_kid", gx, 152, "idle", t, facing=-1, expr="blink", weapon_kind="bokuto", weapon=-30)
    else:
        draw_char(img, "takasugi_kid", tx, 152, "attack", t, p=0.45, facing=1, expr="shout")
        draw_char(img, "gintoki_kid", gx, 152, "guard", t, facing=-1, expr="normal", weapon_kind="bokuto")
        fx.burst(img, t, clash, 189, 134, n=10, colors=[(255, 250, 220), (230, 200, 140)], speed=(30, 80),
                 gravity=90, life=0.4, size=(1, 1), seed=111)
    fx.sakura(img, t, count=12, seed=17, wind=22, fall=16)
    A.zoom(img, lerp(1.62, 1.75, seg(t, T_FB, T_FC)), 190, 128)
    if t >= clash:
        sfx_text(img, 146, 74, "啪！", t, clash, dur=0.5, color=(255, 240, 200), size=16, angle=-10, shake=1)
    fx.sepia(img, 0.9)
    fx.vignette(img, 0.7, (60, 40, 20))
    fx.flash(img, max(1 - u / 0.12, seg(t, T_FC - 0.1, T_FC)) * 0.9, (255, 248, 230))
    fx.letterbox(img, 1.0, 22)


def shot_FC(img, t):
    battle_bg(img, t, 150, 0.5)
    C.add_sprite(img, C.glow_sprite(34, (255, 140, 90), 0.35), PIETA_X - 18 - 34, 146 - 34)
    gex = "shock" if T_DROP <= t < T_DROP + 0.25 else "sad"
    g_head = 2 if t < T_DROP + 0.25 else 3
    pieta(img, t, _tk_expr(t), _tk_arm(t), gex=gex, g_head=g_head)
    z = lerp(3.1, 3.35, ease_in_out(seg(t, T_FC, T_F2)))
    A.zoom(img, z, PIETA_X - 14, 142)
    fx.grayscale(img, 0.35 + 0.4 * seg(t, T_DROP, T_DROP + 0.25))
    A.ash(img, t, 50, seed=3)
    fx.letterbox(img, 1.0, 22)


def shot_F2(img, t):
    u = t - T_F2
    img.paste(_grad("f2", (30, 28, 46), (12, 10, 20), 6))
    A.ash(img, t, 40, seed=4, color=(120, 118, 134))
    C.add_sprite(img, C.glow_sprite(64, (90, 80, 140), 0.5), 192 - 64, 96 - 64)
    bs = A.bust_shadow("gintoki", "sad", 5, crop=0.8, facing=-1, pose="kneel", fade_bottom=0.62,
                       weapon=None, sheathed=False, arm_f=6, arm_b=4)
    x0, y0 = 192 - bs.width // 2, 44 + (1 if step_frame(t, 2) % 2 else 0)
    paste(img, bs, x0, y0)
    # a single tear escapes from under the shadow
    ty = y0 + 13 * 5 + ease_in(seg(u, 0.1, 0.42)) * 34
    ex = x0 + bs.width - 1 - (5 * 5 + 3)         # mirrored (facing left) eye column
    if u > 0.08:
        rect(img, ex, int(ty), 3, 5, (150, 210, 255))
        rect(img, ex, int(ty), 1, 2, (255, 255, 255))
    fx.letterbox(img, 1.0, 22)


# ================================================================ G: dawn / final strike
def dawn_bg(img, t, cam, sun_y, armada=0.5, sun_x=292, rays=0):
    C.sky(img, "dawn", t, horizon=150, body=False)
    if rays > 0:
        A.light_rays(img, sun_x, sun_y, t, alpha=rays)
    A.sun(img, sun_x, int(sun_y), 15, t)
    C.clouds(img, t, cam, "dawn", seed=3, count=6, y0=4, y1=70)
    E.skyline(img, cam, t, "dawn", sky=False, armada=armada, near=False)


def shot_G1(img, t):
    u = t - T_G1
    A.edo_blend(img, t, 150, lerp(0.2, 0.7, seg(t, T_G1, T_EYE)), armada=1.0, roof_y=FLOOR)
    ls, _, _ = render_sprite("takasugi", "lie", t, None, "sleep", 1, sheathed=False, arm_f=175)
    ls = ls.crop(ls.getbbox())
    overlay_rect(img, 150 - ls.width // 2, FLOOR - 1, ls.width, 2, (0, 0, 0), 0.25)
    paste(img, ls, 150 - ls.width // 2, FLOOR - ls.height + 1)
    if u < 0.3:
        draw_char(img, "gintoki", 190, FLOOR, "kneel", t, facing=1, expr="sad")
    else:
        draw_char(img, "gintoki", 190, FLOOR, "idle", t, facing=1, expr="sad", weapon=-60, arm_f=20)
    draw_char(img, "utsuro", 322, FLOOR, "regen", t, facing=-1)
    A.zoom(img, lerp(1.4, 1.5, u / 0.7), 232, 130)
    A.ash(img, t, 30, seed=5, color=(200, 180, 190))
    fx.letterbox(img, 1.0, 22)


def shot_G1b(img, t):
    img.paste(_grad("g1b", (60, 14, 24), (20, 8, 16), 6))
    if t >= T_GLARE:
        A.soft_speed_lines(img, t, 192, 108, (255, 120, 110), 0.6, count=50, inner=40, seed=5)
    glare = t >= T_GLARE
    if not glare:
        hs = A.head_shadow("gintoki", "sad", 6)
        paste(img, hs, 192, 88, anchor="center")
    else:
        A.head_big(img, "gintoki", "angry", 192, 88, 6)
        fx.sparkle(img, 162, 104, t, T_GLARE, size=10, color=(255, 230, 230))
        fx.sparkle(img, 224, 104, t, T_GLARE + 0.03, size=10, color=(255, 230, 230))
        fx.flash(img, 0.6 * (1 - seg(t, T_GLARE, T_GLARE + 0.12)))
    img.paste((0, 0, 0), (0, 0, W, 80))
    img.paste((0, 0, 0), (0, 136, W, H))
    rect(img, 0, 80, W, 1, (140, 30, 40))
    rect(img, 0, 135, W, 1, (140, 30, 40))


def _strike_pos(t):
    k1 = ease_in(seg(t, T_DASH, T_STRIKE))
    k2 = ease_out(seg(t, T_STRIKE, T_STRIKE + 0.3))
    gx = lerp(80, 214, k1) + (262 - 214) * k2
    ux = lerp(306, 170, k1) - (170 - 122) * k2
    return gx, ux


def shot_G2(img, t):
    dawn_bg(img, t, 0, 152, armada=0.5)
    E.roof_walk(img, 0, FLOOR, t, "dawn")
    if T_DASH <= t < T_STRIKE:
        fx.motion_lines(img, t, (255, 240, 230), count=16, direction=1, seed=101, y0=110, y1=170, speed=900)
    gx, ux = _strike_pos(t)
    if t < T_STRIKE - 0.1:
        draw_char(img, "gintoki", gx, FLOOR, "run" if t >= T_DASH else "ready", t, facing=1, expr="angry")
        draw_char(img, "utsuro", ux, FLOOR, "run" if t >= T_DASH else "ready", t, facing=-1, expr="glow")
    else:
        p = 0.35 + 0.65 * seg(t, T_STRIKE - 0.1, T_STRIKE + 0.15)
        draw_char(img, "gintoki", gx, FLOOR, "attack", t, p=p, facing=1, expr="angry")
        draw_char(img, "utsuro", ux, FLOOR, "attack", t, p=p, facing=-1, expr="glow")
    if t < T_STRIKE + 0.1:
        z = lerp(1.0, 1.9, ease_in(seg(t, T_DASH, T_STRIKE)))
        A.zoom(img, z, 192, 138)
    if T_STRIKE <= t < T_STRIKE + 0.1:
        # impact frame: big black silhouettes, back to back, on white with radial lines
        wc = (250, 248, 240)
        img.paste(wc, (0, 0, W, H))
        fx.speed_lines(img, t, 196, 132, color=INK, count=56, inner=128, seed=103)
        uk, uax, uay, _ = A.sil_sprite("utsuro", "attack", T_STRIKE, 0.8, "glow", -1, 3, INK,
                                       glow=A.UTSURO_EYES, glow_color=(230, 30, 50))
        gk, gax, gay, _ = A.sil_sprite("gintoki", "attack", T_STRIKE, 0.8, "angry", 1, 3, INK)
        paste(img, outline(outline(uk, wc), wc), 112 - uax - 2, 188 - uay - 2)
        paste(img, outline(outline(gk, wc), wc), 276 - gax - 2, 188 - gay - 2)
    if T_STRIKE <= t < T_STRIKE + 0.3:
        k = seg(t, T_STRIKE, T_STRIKE + 0.3)
        wd = int(10 * (1 - k)) + 1
        d = ImageDraw.Draw(img)
        d.line([(-10, 196), (W + 10, 64)], fill=INK, width=wd + 4)
        d.line([(-10, 196), (W + 10, 64)], fill=(255, 255, 255), width=wd)
    if T_STRIKE + 0.1 <= t:
        fx.flash(img, 0.9 * (1 - seg(t, T_STRIKE + 0.1, T_G3 + 0.1)))
    dx, dy = fx.shake_offset(t, T_STRIKE, 0.35, amp=5, seed=102)
    fx.shift(img, dx, dy)
    fx.letterbox(img, 1.0, 22)


def _sun_y(t):
    return lerp(152, 110, ease_out(seg(t, T_CRACK, T_H + 2.0)))


def utsuro_frozen():
    return render_sprite("utsuro", "idle", 0.5, None, "smile", -1)


def shot_G3(img, t):
    sy = _sun_y(t)
    dawn_bg(img, t, 0, sy, armada=0.5, rays=int(30 * seg(t, T_CRACK + 0.3, T_SHAT)))
    E.roof_walk(img, 0, FLOOR, t, "dawn")
    draw_char(img, "gintoki", 262, FLOOR, "attack", T_STRIKE + 0.4, p=1.0, facing=1, expr="angry")
    spr, ax, ay = utsuro_frozen()
    p = seg(t, T_CRACK, T_SHAT)
    jit = (1 if step_frame(t, 20) % 2 else -1) if p > 0.5 else 0
    x0, y0 = 122 - ax + jit, FLOOR - ay
    paste(img, spr, x0, y0)
    bb = spr.getbbox()
    if t >= T_CRACK:
        A.cracks(img, x0 + bb[0], y0 + bb[1], bb[2] - bb[0], bb[3] - bb[1], p, seed=7, n=6, step=1.8,
                 halo=(255, 170, 90), clip=(spr, x0, y0))
        C.add_sprite(img, C.glow_sprite(22, (255, 220, 170), round(0.2 + 0.5 * p, 1)), 122 - 22, FLOOR - 16 - 22)
    A.zoom(img, lerp(1.5, 1.72, ease_in_out(seg(t, T_G3, T_SHAT))), 192, 134)
    A.motes(img, t, 16, seed=3)
    fx.letterbox(img, 1.0, 22)


def shot_G4(img, t):
    """Utsuro shatters; the light gathers into Shouyou's gentle ghost."""
    u = t - T_SHAT
    sy = _sun_y(t)
    dawn_bg(img, t, 0, sy, armada=lerp(0.5, 0.0, seg(t, T_SHAT + 0.4, T_H - 0.2)),
            rays=int(lerp(30, 46, seg(t, T_SHAT, T_H))))
    E.roof_walk(img, 0, FLOOR, t, "dawn")
    a = seg(t, T_FACE, T_FACE + 0.45)
    look = "normal" if T_FACE <= t < T_FACE + 0.5 else "sad" if t < T_FACE else \
        "blink" if (t % 1.3) < 0.12 else "sad"
    draw_char(img, "gintoki", 262, FLOOR, "idle", t, facing=-1, expr=look, weapon=-60, arm_f=15)
    if a > 0:
        C.add_sprite(img, C.glow_sprite(30, (255, 220, 170), round(0.8 * a, 1)), 122 - 30, FLOOR - 18 - 30)
    spr, ax, ay = utsuro_frozen()
    A.shatter(img, spr, "utsuro_smile", 122 - ax, FLOOR - ay, t, T_SHAT, pull=(122, 128))
    if a > 0:
        # the gathered light takes Shouyou's shape (drawn over the motes)
        draw_char(img, "shouyou", 122, FLOOR, "smile", t, facing=1, alpha=0.95 * a,
                  flash=0.45 - 0.3 * seg(t, T_FACE + 0.45, T_G4B), flash_color=(255, 240, 210), shadow=False)
    if u < 0.2:
        fx.flash(img, 0.6 * (1 - u / 0.2), (255, 244, 220))
    z = lerp(1.72, 1.3, ease_in_out(seg(t, T_SHAT, T_G4B)))
    A.zoom(img, z, 190, 136)
    A.motes(img, t, 30, seed=4)
    fx.letterbox(img, 1.0, 22)


def shot_G4b(img, t):
    """Close-up: Shouyou smiles in the sunrise, then dissolves into light."""
    sy = _sun_y(t)
    dawn_bg(img, t, 0, sy, armada=lerp(0.5, 0.0, seg(t, T_SHAT + 0.4, T_H - 0.2)), rays=48)
    A.zoom(img, lerp(1.55, 1.7, seg(t, T_G4B, T_H)), 262, 118)
    A.motes(img, t, 36, seed=6)
    bs = A.bust_sprite("shouyou", 0.5, "smile", k=4, facing=1, crop=0.76, fade_bottom=0.8,
                       tint_col=(255, 236, 206), tint_amt=0.12)
    x0 = 124 - bs.width // 2
    y0 = 30 + int(round(wave(t, 0.6, 1.5)))
    C.add_sprite(img, C.glow_sprite(56, (255, 214, 170), 0.8), 124 - 56, 80 - 56)
    if t < T_FADE:
        paste(img, bs, x0, y0, alpha=min(1.0, seg(t, T_G4B, T_G4B + 0.2) + 0.6))
    else:
        A.shatter(img, bs, "shouyou_bust", x0, y0, t, T_FADE)
    fx.letterbox(img, 1.0 - seg(t, T_H - 0.5, T_H), 22)


# ================================================================ H: sunrise over Edo
def shot_H(img, t):
    u = t - T_H
    cam = lerp(0, 26, u / 3.0)
    sy = _sun_y(t)
    C.sky(img, "dawn", t, horizon=150, body=False)
    A.light_rays(img, 300, sy, t, alpha=38)
    A.sun(img, 300, int(sy), 16, t)
    C.clouds(img, t, cam, "dawn", seed=3, count=6, y0=4, y1=70)
    # the armada withdraws into the dawn sky
    for i, (kind, x0, y0, sp) in enumerate((("cruiser", 60, 60, 1.0), ("pirate", 150, 40, 0.8),
                                             ("cruiser", 240, 52, 1.2), ("saucer", 330, 34, 0.9),
                                             ("mothership", 192, 10, 0.5))):
        yy = y0 - (u + 0.8) * 14 * sp
        haze = round(min(0.9, 0.45 + u * 0.12), 2)
        E.ship(img, x0 - cam * 0.1 - u * 6 * sp, yy, kind, t, facing=-1, tod="dawn", haze=haze)
    E.skyline(img, cam, t, "dawn", sky=False, ships=False, armada=0.0, near=False)
    E.roof_walk(img, cam, 168, t, "dawn")
    # a purple butterfly (Takasugi's motif) circles Gintoki, then flies off into the sun
    draw_char(img, "shinpachi", 122, 168, "idle", t, facing=1)
    draw_char(img, "gintoki", 150, 168, "idle", t + 0.3, facing=1,
              expr="blink" if (t % 2.3) < 0.12 else "normal")
    draw_char(img, "kagura", 178, 168, "umbrella_open", t, facing=1)
    draw_char(img, "sadaharu", 218, 168, "sit", t, facing=1)
    for j in range(5, -1, -1):
        bx, by = _butterfly_pos(t - j * 0.06, sy)
        if bx is None:
            continue
        if j == 0:
            A.butterfly(img, bx, by, t, seed=1)
        elif (step_frame(t, 15) + j) % 2 == 0:
            rect(img, int(bx) - 1, int(by) + 2, 1, 1, (255, 226, 140) if j < 3 else (255, 246, 210))
    fx.sparkle(img, 125, 147, t, T_H + 1.6, size=4)          # Shinpachi's glasses glint
    z = lerp(1.14, 1.0, ease_out(seg(t, T_H, DUR)))
    A.zoom(img, z, 176, 132)
    A.motes(img, t, 34, seed=9)
    fx.sakura(img, t, count=10, seed=13, wind=18, fall=10)


def _butterfly_pos(t, sy):
    """Hover around Gintoki's head, then rise toward the sun."""
    t0, t1, t2 = T_H + 0.3, T_H + 1.4, DUR - 0.1
    if t < t0 or t >= t2:
        return None, None
    if t < t1:
        k = (t - t0) / (t1 - t0)
        a = k * 5.0
        return 150 + 14 * math.sin(a) - 10 * (1 - k), 122 + 5 * math.cos(a * 1.3) + 16 * (1 - k)
    k = ease_in_out((t - t1) / (t2 - t1))
    return lerp(150 + 14 * math.sin(5.0), 300, k) + 6 * math.sin(k * 12),         lerp(122 + 5 * math.cos(6.5), sy + 4, k) + 4 * math.sin(k * 19)


# ================================================================ scene
class SilverSoul(Scene):
    id = "s13"
    title = "银之魂篇"
    duration = DUR
    music = [(0.0, "epic"), (T_SHOCK, "sad"), (T_G1 + 0.25, "epic")]
    music_vol = 0.55
    fade_in = 0.3
    fade_out = 0.6
    subs = [
        (2.25, 4.50, None, "天人舰队，遮蔽了江户的天空。"),
        (5.85, 7.58, "utsuro", "我即是虚。"),
        (T_E1, T_E1 + 1.98, "takasugi", "别拖后腿啊，银时。"),
        (T_F + 0.15, T_SMILE - 0.05, "takasugi", "银时……剩下的，交给你了。"),
        (T_FACE + 0.1, T_H - 0.05, "shouyou", "……谢谢。你们都长大了呢。"),
        (T_H + 0.35, DUR - 0.4, None, "长夜过去，江户迎来了黎明。"),
    ]

    def render(self, img, t):
        if t < T_C1:
            shot_B(img, t)
            if t < T_B:
                overlay_chapter(img, t)
        elif t < T_C2:
            shot_C1(img, t)
        elif t < T_D:
            shot_C2(img, t)
        elif t < T_W:
            shot_D(img, t)
        elif t < T_E1:
            shot_W(img, t)
        elif t < T_E2:
            shot_E1(img, t)
        elif t < T_E2B:
            shot_E2a(img, t)
        elif t < T_IMP:
            shot_E2b(img, t)
        elif t < T_F:
            shot_E2c(img, t)
        elif t < T_FB:
            shot_F(img, t)
        elif t < T_FC:
            shot_FB(img, t)
        elif t < T_F2:
            shot_FC(img, t)
        elif t < T_G1:
            shot_F2(img, t)
        elif t < T_EYE:
            shot_G1(img, t)
        elif t < T_G2:
            shot_G1b(img, t)
        elif t < T_G3:
            shot_G2(img, t)
        elif t < T_SHAT:
            shot_G3(img, t)
        elif t < T_G4B:
            shot_G4(img, t)
        elif t < T_H:
            shot_G4b(img, t)
        else:
            shot_H(img, t)
        if T_C1 <= t < T_D:
            name_card(img, t, T_NC, 2.2, "utsuro", "虚", "不死之身｜松阳的另一面", side="right")

    def cues(self):
        m = dict(CUTS_BY_KEY)
        c = [
            # A / B — the armada
            Cue(0.15, "gong", vol=0.8),
            Cue(0.10, "engine_hum", vol=0.45, dur=4.5),
            Cue(0.30, "wind", vol=0.3, dur=4.3),
            Cue(2.10, "thunder", vol=0.55),
            Cue(2.60, "engine_hum", vol=0.35, dur=2.0),
            # C — Utsuro
            Cue(4.60, "crow", vol=0.8), Cue(4.62, "whoosh", vol=0.5),
            Cue(4.75, "aura", vol=0.8), Cue(5.15, "sting_dramatic", vol=0.8),
            Cue(5.35, "whoosh", vol=0.35), Cue(5.95, "heartbeat", vol=0.6),
            Cue(T_OPEN, "shine", vol=0.7),
            # D — montage
            Cue(m["ssg"], "whoosh", vol=0.6), Cue(m["ssg"] + 0.10, "land", vol=0.6),
            Cue(m["ssg"] + 0.14, "land", vol=0.5), Cue(m["ssg"] + 0.18, "land", vol=0.5),
            Cue(m["ssg"] + 0.24, "shing", vol=0.7),
            Cue(m["joui"], "whoosh", vol=0.6), Cue(m["joui"] + 0.05, "pop", vol=0.5),
            Cue(m["joui"] + 0.10, "pop", vol=0.5), Cue(m["joui"] + 0.12, "land", vol=0.6),
            Cue(m["joui"] + 0.15, "pop", vol=0.5), Cue(m["joui"] + 0.20, "pop", vol=0.5),
            Cue(m["women"], "whoosh", vol=0.6), Cue(m["women"] + 0.10, "land", vol=0.5),
            Cue(m["women"] + 0.14, "land", vol=0.5), Cue(m["women"] + 0.15, "aura", vol=0.5),
            Cue(m["women"] + 0.35, "slash", vol=0.6),
            Cue(m["otose"], "whoosh", vol=0.6), Cue(m["otose"] + 0.05, "machinegun", vol=0.45),
            Cue(m["otose"] + 0.40, "machinegun", vol=0.35),
            Cue(m["madao"], "record_scratch", vol=0.7), Cue(m["madao"] + 0.14, "shine", vol=0.55),
            Cue(m["madao"] + 0.22, "pop", vol=0.5), Cue(m["madao"] + 0.60, "crow", vol=0.9),
            Cue(m["madao"] + 0.95, "sweat", vol=0.6),
            Cue(m["kaien"], "whoosh", vol=0.6), Cue(m["kaien"] + 0.01, "engine_hum", vol=0.5, dur=0.65),
            Cue(m["yato"], "whoosh", vol=0.6), Cue(m["yato"] + 0.14, "land", vol=0.8),
            Cue(m["yato"] + 0.15, "impact", vol=0.7), Cue(m["yato"] + 0.22, "machinegun", vol=0.5),
            Cue(m["yorozuya"], "whoosh", vol=0.6), Cue(m["yorozuya"] + 0.02, "jump", vol=0.6),
            Cue(m["yorozuya"] + 0.28, "land", vol=0.7), Cue(m["yorozuya"] + 0.35, "bark", vol=0.8),
            # W — everyone assembles
            Cue(T_W, "whoosh", vol=0.6), Cue(T_W + 0.10, "land", vol=0.5), Cue(T_W + 0.17, "land", vol=0.5),
            Cue(T_W + 0.25, "land", vol=0.5), Cue(T_W + 0.33, "land", vol=0.5),
            Cue(T_SLAM, "title_hit", vol=0.9), Cue(T_SLAM + 0.05, "cheer", vol=0.7),
            Cue(T_SLAM + 0.05, "crowd", vol=0.4, dur=1.6),
            # E — back to back, Takasugi falls
            Cue(T_E1 + 0.10, "shing", vol=0.7), Cue(T_E1, "wind", vol=0.35, dur=T_F - T_E1),
            Cue(T_E1, "fire", vol=0.22, dur=T_F - T_E1),
            Cue(T_ATK, "whoosh", vol=0.5), Cue(T_CUT - 0.02, "slash_big", vol=0.8), Cue(T_CUT, "hit", vol=0.6),
            Cue(T_CUT + 0.03, "hit", vol=0.5), Cue(T_CUT + 0.5, "thud", vol=0.4), Cue(T_CUT + 0.6, "thud", vol=0.35),
            Cue(T_E2, "dash", vol=0.7), Cue(T_X, "slash_big", vol=0.9), Cue(T_X + 0.02, "hit", vol=0.6),
            Cue(T_X + 0.10, "aura", vol=0.6),
            Cue(T_E2B + 0.02, "whoosh", vol=0.6), Cue(T_E2B + 0.18, "dash", vol=0.6),
            Cue(T_IMP, "impact", vol=1.0), Cue(T_IMP + 0.01, "stab", vol=0.5),
            Cue(T_SHOCK, "shock", vol=0.8),
            # F — in his arms, the old days, the end
            Cue(T_F + 0.10, "heartbeat", vol=0.7), Cue(T_F, "wind", vol=0.28, dur=T_G1 - T_F),
            Cue(T_FB, "twinkle", vol=0.45), Cue(T_FB + 0.24, "hit", vol=0.35),
            Cue(T_FC + 0.10, "heartbeat", vol=0.55), Cue(T_SMILE, "heartbeat", vol=0.35),
            Cue(T_DROP, "thud", vol=0.25),
            # G — dawn, final strike
            Cue(T_G1 + 0.3, "whoosh", vol=0.35),
            Cue(T_GLARE, "shing", vol=0.9), Cue(T_GLARE + 0.02, "shine", vol=0.6),
            Cue(T_DASH, "dash", vol=0.8), Cue(T_DASH + 0.05, "charge", vol=0.5),
            Cue(T_STRIKE, "slash_big", vol=1.0), Cue(T_STRIKE + 0.01, "impact", vol=1.0),
            Cue(T_CRACK, "glass", vol=0.45), Cue(T_CRACK + 0.28, "glass", vol=0.55),
            Cue(T_SHAT, "glass", vol=0.8), Cue(T_SHAT + 0.02, "sparkle", vol=0.7),
            Cue(T_FACE + 0.05, "shine", vol=0.6), Cue(T_G4B + 0.05, "twinkle", vol=0.5),
            Cue(T_FADE, "sparkle", vol=0.5), Cue(T_FADE + 0.1, "bell", vol=0.4),
            # H — sunrise
            Cue(T_H, "wind", vol=0.3, dur=DUR - T_H), Cue(T_H + 0.1, "bell", vol=0.45),
            Cue(T_H + 1.6, "twinkle", vol=0.3), Cue(DUR - 1.2, "sparkle", vol=0.3),
        ]
        return c


CUTS_BY_KEY = [(k, t0) for t0, k in CUTS]

SCENE = SilverSoul()
