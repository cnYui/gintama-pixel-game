"""s07 红樱篇 (Benizakura arc) — 27.8 s.

SHOT LIST (absolute scene times, seconds)
  A  0.00- 1.80  chapter card 「红樱篇」 over black, red petals drift across (gong on the slam)
  B1 1.80- 3.70  night bridge, huge moon on the horizon, letterbox. Katsura (long hair) +
                 Elizabeth walk right; a silhouetted swordsman walks left in front of the moon.
                 Stop / heartbeat (3.00) / push-in -> he vanishes (3.35) -> IMPACT FRAME (3.42,
                 black silhouettes on white) horizontal red slash through Katsura, red flash,
                 petals + hair strands.
  B2 3.70- 4.90  close-up of the empty bridge planks: a lock of long black hair drifts down
                 across the moon and lands (4.60). Red petals.
  B3 4.90- 6.20  Elizabeth alone in a drizzle, backlit by the moon, gloom; sign pops up
                 「桂先生……」 next to the lock.
  C  6.20- 9.80  red moon over Edo rooftops: Okada Nizo draws Benizakura (7.00), red tendrils
                 crawl up his arm, heartbeat pulses (7.3/7.9/8.5), slow parallax push-in.
                 name_card 冈田似藏 (7.20).  Nizo: 「红樱……还没吃饱呢。」  blade glint (9.45)
  D  9.80-15.00  BATTLE (music) — the bridge in a night thunderstorm, heavy rain.
     9.80 lightning; 10.15 both dash; 10.45 CLASH (sparks, 「铿!!」); 10.45-11.70 close
     exchange x3 (10.85/11.15/11.45); 11.70 tendrils lash, 11.85 Gintoki is cut & knocked
     back, kneels 12.15; 12.45-13.30 close-up: eyes sharpen (12.80), he rises (13.05);
     13.35 both charge and pass -> IMPACT FRAME 13.62 (giant diagonal slash);
     14.20 crack 「咔嚓!」, 14.30 lightning + Benizakura shatters, Nizo collapses (14.70).
  E1 15.00-16.00 huge full moon, the Kiheitai ship glides across it (tension music).
  E2 16.00-18.40 Takasugi sits on the ship rail smoking his kiseru, moon behind, golden
                 butterflies. name_card 高杉晋助 (16.05). 「我只是要毁掉这个腐朽的世界。」
  F1 18.40-19.25 (battle) Kiheitai deck: Harusame pirates surround Gintoki; one charges ->
                 Katsura drops from the sky and cuts him away (land 18.66); snap zoom on
                 his SHORT hair with speed lines (18.90).
  F2 19.25-23.30 back to back, pirates prowling (two feints scared off by a blade glint),
                 dark foreground mob framing the shot, slow push-in.
                 Katsura 「背后交给你了，银时。」 / Gintoki 「别拖后腿啊，假发。」
  F3 23.30-25.45 snap-zoom two-shot: Katsura whirls round and yells 「不是假发，是桂！」 at the
                 back of Gintoki's head (speed lines, vein, 「是桂!!」, shake); Gintoki picks
                 his nose, deadpan (23.84 「抠抠」, flicks it); pirates lose patience and charge
                 「杀啊——!!」 (23.98) -> both snap to guard -> double SPIN SLASH (24.34), wide ->
                 pirates fly off, two become twinkling stars (25.05/25.20).
  G  25.45-27.80 low angle: Takasugi on the upper deck in front of the moon; Katsura (with
                 Gintoki + Elizabeth) below: 「下次见面，你我就是敌人。」 -> 26.80 reverse shot:
                 Takasugi close-up filling the moon, smirks and exhales smoke (27.02).
"""
import math

from PIL import ImageDraw

from engine.core import Scene, Cue, W, H, seg, lerp, clamp, ease_in, ease_out, ease_in_out, \
    wave, step_frame, rng
from engine.gfx import INK, rect
from engine import fx
from engine.text import sfx_text, name_card, chapter_card
from chars import draw_char
from bg import common as C, edo as E
from scenes import _s07_art as A

# ------------------------------------------------------------------ timeline
B1, B2, B3, C0, D0 = 1.80, 3.70, 4.90, 6.20, 9.80
E1, E2, F1, F2, F3, G0 = 15.00, 16.00, 18.40, 19.25, 23.30, 25.45
END = 27.80

# B1 beats
STOP, BEAT1, VANISH, SLASH = 2.95, 3.00, 3.35, 3.42
LOCK_LAND = 4.60
# C beats
DRAW, HB = 7.00, (7.30, 7.90, 8.50)
# D beats
DASH1, CLASH = 10.15, 10.45
XCH = (10.85, 11.15, 11.45)
WIND, HIT, KNEEL = 11.70, 11.85, 12.15
D5, GLINT, RISE = 12.45, 12.80, 13.05
D6, CHARGE, IMPACT = 13.30, 13.35, 13.62
D7, CRACK, SHATTER, D7C, NKNEEL, NFALL = 13.95, 14.20, 14.32, 14.62, 14.64, 14.82
LIGHTNING = (9.80, SHATTER)
# F beats
F_LAND = 18.66
REVEAL = 18.90
TURN, NOSE, RUSH, SPIN = 23.30, 23.84, 23.98, 24.34
STARS = (25.05, 25.20)
FEINT, F2B = 20.30, 21.33          # a pirate feints at Katsura; cut to Gintoki's close shot
FEINTS = {3: FEINT, 0: 22.35}      # pirate slot -> time it steps in and backs off again
# G beats
G_TAKA, SMIRK = 26.80, 27.02       # cut to Takasugi's close-up; his smirk

FLOOR_BR = 152                 # bridge deck crest
MOON_B = (256, 112, 40)        # bridge-shot moon, sitting on the horizon
WHITE = (250, 246, 255)
DARK = (18, 10, 22)


def _deck(sx, cam_x=0):
    return C.bridge_deck_y(sx, cam_x, FLOOR_BR)


def _letterbox(img, amt=1.0, bar=20):
    fx.letterbox(img, amt, bar)


def _rain(img, t, heavy=1.0, seed=0):
    n = int(130 * heavy)
    fx.rain(img, t, count=n, seed=seed, color=(118, 130, 184), speed=430, slant=0.28, length=7)
    fx.rain(img, t + 0.37, count=n // 3, seed=seed + 1, color=(186, 196, 236), speed=560, slant=0.3, length=10)


def _drizzle(img, t, seed=5):
    fx.rain(img, t, count=45, seed=seed, color=(110, 118, 160), speed=260, slant=0.18, length=5)


def _pulse(t, beats, decay=0.28):
    v = 0.0
    for b in beats:
        if t >= b:
            v = max(v, math.exp(-(t - b) / decay * 3))
    return v


def _night_far(img, t, moon, clouds_seed=5, river=True, cloud_band=(20, 64)):
    """Crisp far layers for the bridge close-ups: sky, moon, clouds, river."""
    C.sky(img, "night", t, horizon=150, body=False)
    C.big_moon(img, *moon)
    C.clouds(img, t, 0, "night", seed=clouds_seed, count=4, y0=cloud_band[0], y1=cloud_band[1])
    if river:
        C.river(img, 150, 66, t, "night", 0, reflect_x=moon[0])


# ================================================================== shots
def bridge_bg(img, t, cam_x, tod="night"):
    if tod == "storm":        # dark night thunderstorm (no moon)
        C.sky(img, "night", t, horizon=150, body=False, stars=False)
        C.clouds(img, t, cam_x, "night", seed=4, count=9, y0=0, y1=56, speed=5.0)
        C.far_mountains(img, cam_x, "night", 150)
        C.river(img, 150, 66, t, "night", cam_x, reflect=False)
        C.bridge(img, cam_x, FLOOR_BR, "night")
        fx.grade(img, (0.8, 0.86, 1.0), (2, 4, 10))
        return
    C.sky(img, tod, t, horizon=150, body=False)
    C.big_moon(img, MOON_B[0], MOON_B[1], MOON_B[2])
    C.clouds(img, t, cam_x, tod, seed=5, count=5, y0=26, y1=72)
    C.river(img, 150, 66, t, tod, cam_x, reflect_x=MOON_B[0])
    C.bridge(img, cam_x, FLOOR_BR, tod)


# ------------------------------------------------------------------ A + B1 night bridge ambush
def shot_b1(img, t):
    cam_x = lerp(-26, 6, ease_in_out(seg(t, B1 - 0.2, 3.3)))
    kw = seg(t, B1 - 0.2, STOP)
    kx, ex, nx = lerp(114, 172, kw), lerp(66, 124, kw), lerp(336, 262, kw)
    impact = SLASH <= t < SLASH + 0.1

    def feet(wx):
        sx = wx - cam_x
        return sx, _deck(sx, cam_x)

    if impact:
        # anime impact frame: black silhouettes on white, black moon
        img.paste(WHITE, (0, 0, W, H))
        d = ImageDraw.Draw(img)
        mx, my, mr = MOON_B
        d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=DARK)
        lay = A.new_layer()
        C.bridge(lay, cam_x, FLOOR_BR, "night")
        draw_char(lay, "elizabeth", *feet(ex), "shock", t, p=0.1, shadow=False)
        draw_char(lay, "katsura", *feet(kx), "idle", t, expr="shock", shadow=False)
        draw_char(lay, "okada_nizo", *feet(148), "attack", t, p=0.95, facing=-1, shadow=False)
        sil = A.silhouette_layer(lay, DARK)
        img.paste(sil, (0, 0), sil)
        d.rectangle([0, 150, W, H], fill=DARK)
        d.rectangle([0, 150, W, 152], fill=WHITE)
    else:
        bridge_bg(img, t, cam_x)
        # Elizabeth (a step behind)
        if t < STOP:
            draw_char(img, "elizabeth", *feet(ex), "walk", t)
        elif t < SLASH:
            draw_char(img, "elizabeth", *feet(ex), "idle", t)
        else:
            draw_char(img, "elizabeth", *feet(ex), "shock", t, p=seg(t, SLASH, SLASH + 1))
        # Katsura (long hair)
        if t < STOP:
            draw_char(img, "katsura", *feet(kx), "walk", t)
        elif t < SLASH:
            draw_char(img, "katsura", *feet(kx), "idle", t, expr="determined")
        else:
            draw_char(img, "katsura", *feet(kx), "idle", t, expr="shock", bob=0)
        # the mysterious swordsman: a backlit silhouette in front of the moon
        if t < STOP:
            A.draw_shadow_char(img, "okada_nizo", *feet(nx), "walk", t, facing=-1, rim_dir=1)
        elif t < VANISH:
            A.draw_shadow_char(img, "okada_nizo", *feet(nx), "idle", t, facing=-1, rim_dir=1)
        elif t < SLASH:
            u = seg(t, VANISH, SLASH)             # a blur streak across the bridge
            sx, sy = feet(lerp(262, 148, ease_in(u)))
            rect(img, int(sx), sy - 22, int(262 - cam_x - sx), 2, (220, 200, 230))
            rect(img, int(sx), sy - 14, int(262 - cam_x - sx), 1, (200, 40, 60))
        else:
            A.draw_shadow_char(img, "okada_nizo", *feet(148), "attack", t, p=0.95, facing=-1, rim_dir=1)
    # camera: slight push during the standoff
    # camera: slow creep while they walk, then a tense push-in on the standoff
    k = lerp(1.2, 1.32, seg(t, B1, STOP)) + 0.33 * ease_in_out(seg(t, STOP, VANISH))
    ccx = lerp(196, 206, ease_in_out(seg(t, STOP, VANISH)))
    if impact:                                   # camera jolts in on the impact frame
        cam = A.zoom_at(img, 2.0, kx - cam_x - 8, 134)
    else:
        cam = A.zoom_at(img, k, ccx, 128 + 4 * seg(t, STOP, VANISH))
    ksx, ksy = A.to_screen(cam, kx - cam_x, _deck(kx - cam_x, cam_x) - 22)
    if impact:
        A.diag_slash(img, (-10, ksy + 3), (W + 10, ksy - 3), width=4, color=(200, 20, 44), edge=None)
    elif t >= SLASH:
        u = seg(t, SLASH + 0.1, B2)
        fx.flash(img, 0.5 * (1 - u), (190, 20, 44))
        rect(img, 0, int(ksy), W, int(3 * (1 - u)) + 1, (255, 236, 240))
        fx.burst(img, t, SLASH + 0.1, ksx, ksy, n=16, colors=A.RED_PETALS, speed=(30, 90), gravity=30,
                 life=0.9, size=(1, 2), seed=7, spread=(-160, 20))
        fx.burst(img, t, SLASH + 0.1, ksx - 4, ksy - 2, n=10, colors=[(42, 42, 68), (60, 62, 94)],
                 speed=(20, 60), gravity=40, life=0.9, size=(1, 1), seed=8)
    if BEAT1 <= t < VANISH:
        fx.vignette(img, 0.4 * seg(t, BEAT1, VANISH))
    if not impact:
        A.red_petals(img, t, count=8, seed=2)
    _letterbox(img)


# ------------------------------------------------------------------ B2 the lock of hair
LOCK_X = 166          # screen x on the bridge (cam_x = 6)


def _lock_state(t):
    dy = _deck(LOCK_X, 6)
    k = seg(t, B2, LOCK_LAND)
    if k < 1:
        lt = t - B2
        x = LOCK_X + math.sin(lt * 3.3) * 6 + lt * 3
        y = lerp(100, dy - 6, ease_in_out(k) * 0.3 + k * 0.7)
        ang = 34 * math.sin(lt * 3.3 + 1.2)
        return x, y, ang
    return LOCK_X + 3.6, dy - 4, 84


def shot_b2(img, t):
    _night_far(img, t, (262, 98, 60), clouds_seed=6)
    lay = A.new_layer()
    C.bridge(lay, 6, FLOOR_BR, "night")
    x, y, ang = _lock_state(t)
    A.red_petals(lay, t, count=5, seed=31, area=(110, 96, 230, 150), wind=10, fall=9)
    A.hair_lock(lay, x, y, ang)
    if t >= LOCK_LAND:
        fx.smoke_puff(lay, t, LOCK_LAND, x, y + 4, size=5, seed=3, color=(120, 116, 150), life=0.5)
    A.zoom_layer(img, lay, lerp(2.6, 2.4, seg(t, B2, B3)), 150, 132)
    A.red_petals(img, t, count=12, seed=33, wind=18, fall=22)
    _letterbox(img)


# ------------------------------------------------------------------ B3 Elizabeth alone
def shot_b3(img, t):
    _night_far(img, t, (78, 70, 46), clouds_seed=7, cloud_band=(10, 40))
    lay = A.new_layer()
    C.bridge(lay, 6, FLOOR_BR, "night")
    x, y, ang = _lock_state(t)
    A.hair_lock(lay, x, y, ang)
    sx = 118
    sy = _deck(sx, 6)
    if t < 5.05:
        draw_char(lay, "elizabeth", sx, sy, "sad", t, shadow=False)
    else:
        draw_char(lay, "elizabeth", sx, sy, "sign", t, p=seg(t, 5.05, 6.05), expr="sad", sign="桂先生……",
                  shadow=False)
    A.zoom_layer(img, lay, lerp(2.3, 2.45, ease_in_out(seg(t, B3, C0))), 156, 124)
    _drizzle(img, t)
    fx.vignette(img, 0.35)
    _letterbox(img)


# ------------------------------------------------------------------ C Okada Nizo / Benizakura
NIZO_C = (224, 160)


def shot_c(img, t):
    k = lerp(1.6, 2.4, ease_in_out(seg(t, C0, D0)))
    cam_x = 1150 + (t - C0) * 6
    C.sky(img, "night", t, horizon=150, body=False)
    C.big_moon(img, 214, 94, 54, tint=(255, 150, 140))
    C.clouds(img, t, 0, "night", seed=9, count=5, y0=10, y1=60, speed=2.0)
    mid = A.new_layer()
    E.skyline(mid, cam_x, t, "night", ships=False, sky=False, near=False, dy=38)
    A.zoom_layer(img, mid, 1 + (k - 1) * 0.3, 214, 130)
    near = A.new_layer()
    E.roof_walk(near, cam_x, 160, t, "night")
    pulse = _pulse(t, HB)
    nx, ny = NIZO_C
    if t < DRAW:
        draw_char(near, "okada_nizo", nx, ny, "idle", t, facing=-1, shadow=False)
    else:
        g = ease_out(seg(t, DRAW, 8.4))
        draw_char(near, "okada_nizo", nx, ny, "benizakura", t, facing=-1, grow=g, shadow=False,
                  expr="evil" if t >= 8.15 else None, flash=0.35 * pulse, flash_color=(255, 40, 60))
        fx.embers(near, t, count=26, seed=4, colors=((255, 70, 80), (200, 30, 50), (255, 160, 150)),
                  rise=22, area=(nx - 50, ny - 60, nx + 40, ny + 4))
    cam = A.zoom_layer(img, near, k, nx + 2, 138)
    fx.grade(img, (1.08, 0.84, 0.88), (8, 0, 2))
    _drizzle(img, t, seed=6)
    if pulse > 0:
        fx.flash(img, 0.22 * pulse, (160, 0, 24))
    fx.vignette(img, 0.5, (30, 0, 8))
    if t >= DRAW:
        fx.burst(img, t, DRAW, *A.to_screen(cam, nx - 12, ny - 12), n=14,
                 colors=[(255, 220, 220), (255, 80, 90)], speed=(40, 110), gravity=60, life=0.5, seed=12)
    if t >= 9.40:
        tx, ty = A.to_screen(cam, nx - 22, ny - 4)
        fx.sparkle(img, int(tx), int(ty), t, 9.45, size=7, color=(255, 230, 230))
    _letterbox(img, bar=16)
    A.name_card_tag(img, t, 7.20, 2.30, (170, 40, 60), "冈田似藏", "人斩｜妖刀红樱", tag="似藏", side="left")


# ------------------------------------------------------------------ D the fight in the rain
def _gx_d(t):
    """Gintoki world x during the fight."""
    if t < DASH1:
        return 116
    if t < CLASH:
        return lerp(116, 174, ease_in(seg(t, DASH1, CLASH)))
    if t < HIT:
        push = 0
        for i, b in enumerate(XCH):
            if b - 0.05 <= t < b + 0.25:
                push = (-4 if i == 0 else 3) * (1 - seg(t, b, b + 0.25))
        return 174 + push
    if t < KNEEL:
        return lerp(174, 140, ease_out(seg(t, HIT, KNEEL)))
    if t < CHARGE:
        return 140
    if t < IMPACT:
        return lerp(140, 252, ease_in_out(seg(t, CHARGE, IMPACT)))
    return 252


def _nx_d(t):
    if t < DASH1:
        return 268
    if t < CLASH:
        return lerp(268, 210, ease_in(seg(t, DASH1, CLASH)))
    if t < CHARGE:
        push = 0
        for i, b in enumerate(XCH):
            if b - 0.05 <= t < b + 0.25:
                push = (4 if i == 1 else -2) * (1 - seg(t, b, b + 0.25))
        if t >= WIND:
            push -= 8 * ease_out(seg(t, WIND, HIT))
        return 210 + push
    if t < IMPACT:
        return lerp(202, 124, ease_in_out(seg(t, CHARGE, IMPACT)))
    return 124


def _fighter_poses(t):
    # ---- Nizo
    npose, np_, nkw = "benizakura", None, {}
    if DASH1 <= t < CLASH:
        npose, np_ = "thrust", 0.2
    elif CLASH <= t < WIND:
        npose = "ready"
        if t < CLASH + 0.25:
            npose, np_ = "attack", 0.5
        for i, b in enumerate(XCH):
            if b - 0.22 <= t < b + 0.12:
                if i == 1:
                    npose, np_ = "guard", None
                else:
                    npose, np_ = "attack", lerp(0.25, 0.62, seg(t, b - 0.22, b))
    elif WIND <= t < CHARGE:
        if t < HIT + 0.3:
            npose, np_ = "attack", lerp(0.2, 0.62, seg(t, WIND, HIT))
    elif CHARGE <= t < IMPACT:
        npose, np_ = "thrust", 0.3
    elif t >= IMPACT:
        npose, np_ = "attack", 1.0
        if t >= SHATTER:
            nkw["weapon"] = None
        if t >= NKNEEL:
            npose, np_ = ("kneel", None) if t < NFALL else ("lie", None)
            nkw = {}
    # his blind eyes snap open as Benizakura shatters (no comedic X-eyes on this beat)
    nexpr = "evil" if t < IMPACT else ("determined" if t < SHATTER else "open_eyes" if t < NKNEEL else "sad")
    # ---- Gintoki
    gpose, gp, gexpr, gflash, gkw = "ready", None, "determined", 0.0, {}
    if CLASH <= t < WIND:
        if t < CLASH + 0.25:
            gpose, gp = "attack", 0.5
        for i, b in enumerate(XCH):
            if b - 0.22 <= t < b + 0.12:
                if i == 0:
                    gpose, gp = "guard", None
                elif i == 1:
                    gpose, gp = "attack", lerp(0.25, 0.62, seg(t, b - 0.22, b))
                else:
                    gpose, gp = "slash_up", seg(t, b - 0.22, b + 0.1)
    elif WIND <= t < HIT:
        gpose = "guard"
    elif HIT <= t < KNEEL:
        gpose, gp, gexpr = "hit", seg(t, HIT, KNEEL), "sad"      # pained, not comedic X-eyes
        gflash = 1.0 if t < HIT + 0.07 else 0.0
    elif KNEEL <= t < RISE:
        # down on one knee, leaning on the planted bokuto; eyes sharpen at GLINT
        gpose, gexpr = "kneel", ("sad" if t < GLINT else "angry")
        gkw = {"weapon": -38, "arm_f": 62, "sheathed": False}
    elif t >= IMPACT:
        gpose, gp = "attack", 1.0
        if t >= 14.75:
            gpose, gp, gexpr = "idle", None, "normal"
    return (npose, np_, nkw, nexpr), (gpose, gp, gexpr, gflash, gkw)


def _fighters(img, t, cam_x=0, sil=False):
    gx, nx = _gx_d(t), _nx_d(t)
    gy, ny = _deck(gx, cam_x), _deck(nx, cam_x)
    (npose, np_, nkw, nexpr), (gpose, gp, gexpr, gflash, gkw) = _fighter_poses(t)
    gcol, ncol = (176, 206, 255), (255, 84, 96)          # ghost tints: silver-blue vs Benizakura red
    if not sil:
        if DASH1 <= t < CLASH:
            A.afterimages(img, "gintoki", 116 - cam_x, gx - cam_x, gy, "ready", t, facing=1, tint_col=gcol)
            A.afterimages(img, "okada_nizo", 268 - cam_x, nx - cam_x, ny, "thrust", t, p=0.2, facing=-1,
                          tint_col=ncol)
        if CHARGE <= t < IMPACT:
            A.afterimages(img, "gintoki", 140 - cam_x, gx - cam_x, gy, "ready", t, facing=1, n=4, tint_col=gcol)
            A.afterimages(img, "okada_nizo", 202 - cam_x, nx - cam_x, ny, "thrust", t, p=0.3, facing=-1, n=4,
                          tint_col=ncol)
    draw_char(img, "okada_nizo", nx - cam_x, ny, npose, t, p=np_, expr=nexpr, facing=-1, shadow=not sil, **nkw)
    draw_char(img, "gintoki", gx - cam_x, gy, gpose, t, p=gp, expr=gexpr, facing=1, flash=gflash, shadow=not sil,
              **gkw)
    if not sil and KNEEL <= t < RISE:                  # stylised cut on his cheek (no gore)
        wx, wy = gx - cam_x, gy - 13
        d = ImageDraw.Draw(img)
        d.line([(wx - 2, wy - 2), (wx + 1, wy + 1)], fill=(210, 30, 52))
        d.point((wx - 1, wy - 2), fill=(255, 110, 120))
    if WIND <= t < HIT + 0.3 and not sil:      # Benizakura tendrils lash out at Gintoki
        grow = ease_out(seg(t, WIND, HIT)) * (1 - seg(t, HIT + 0.05, HIT + 0.3))
        A.tendrils(img, nx - cam_x - 5, ny - 18, gx - cam_x + 4, gy - 20, t, n=3, amp=4, grow=grow, seed=2)
    return gx, gy, nx, ny


def _d_camera(t):
    if t < CLASH:
        return lerp(1.5, 1.7, seg(t, D0, CLASH)), 192, 128
    if t < WIND:
        dx, dy = fx.shake_offset(t, CLASH, 0.3, 3, seed=1)
        return 2.4, 192 + dx * 0.5, 134 + dy * 0.5
    if t < D5:
        return lerp(2.1, 1.8, ease_out(seg(t, WIND, KNEEL))), 176, 134
    if t < D6:
        return lerp(3.3, 3.6, seg(t, D5, D6)), 140, _deck(140) - 20
    if t < D7:
        return 1.5, 190, 128
    if t < CRACK:
        return 1.7, 188, 134
    if t < D7C:                                  # close on the blade as it breaks
        return lerp(2.8, 3.1, seg(t, CRACK, D7C)), 116, _deck(124) - 18
    return lerp(1.8, 1.95, ease_in_out(seg(t, D7C, E1))), 188, 134


def shot_d(img, t):
    impact = IMPACT <= t < IMPACT + 0.1
    k, cx, cy = _d_camera(t)
    if impact:
        img.paste(WHITE, (0, 0, W, H))
        lay = A.new_layer()
        C.bridge(lay, 0, FLOOR_BR, "night")
        _fighters(lay, t, 0, sil=True)
        s = A.silhouette_layer(lay, DARK)
        img.paste(s, (0, 0), s)
        ImageDraw.Draw(img).rectangle([0, 158, W, H], fill=DARK)
        cam = A.zoom_at(img, k, cx, cy)
        A.diag_slash(img, (20, 30), (W - 20, 190), width=8, color=DARK, edge=None)
        A.diag_slash(img, (40, 44), (W - 40, 176), width=3, color=(210, 20, 44), edge=None)
        dx, dy = fx.shake_offset(t, IMPACT, 0.4, 5, seed=136)
        fx.shift(img, dx, dy, fill=WHITE)
        return
    bridge_bg(img, t, 0, "storm")
    for i, t0 in enumerate(LIGHTNING):
        if A.lightning_amount(t, t0) > 0.5:
            A.bolt(img, i, x=(96, 196)[i], y1=(140, 104)[i])
    gx, gy, nx, ny = _fighters(img, t, 0)
    clash_pt = ((gx + nx) / 2, (gy + ny) / 2 - 17)
    for i, b in enumerate((CLASH,) + XCH):      # sparks at every blade contact
        fx.burst(img, t, b, clash_pt[0], clash_pt[1], n=16 if i == 0 else 10,
                 colors=[(255, 255, 255), (255, 230, 90), (255, 140, 60)], speed=(50, 150),
                 gravity=200, life=0.45, size=(1, 2), seed=40 + i)
    # the cut: a stylised red splash; water spray when he lands on his knee
    fx.burst(img, t, HIT, gx + 2, gy - 20, n=7, colors=[(228, 40, 60), (170, 20, 40)], speed=(30, 70),
             gravity=160, life=0.4, size=(1, 1), seed=51, spread=(180, 260))
    fx.burst(img, t, KNEEL, gx, gy, n=12, colors=[(170, 190, 230), (220, 230, 250)], speed=(30, 80),
             gravity=220, life=0.5, size=(1, 1), seed=52, spread=(190, 350))
    blade = (124 - 14, _deck(124) - 9)
    if t >= SHATTER:
        A.shards(img, t, SHATTER, *blade, n=16, seed=3, dirx=-1, life=1.0)
        fx.burst(img, t, SHATTER, *blade, n=12, colors=[(255, 90, 100), (255, 220, 220)],
                 speed=(40, 120), gravity=120, life=0.6, seed=53)
    elif t >= CRACK:
        d = ImageDraw.Draw(img)
        d.line([(blade[0] - 2, blade[1] - 2), (blade[0] + 1, blade[1] + 1), (blade[0], blade[1] + 3)],
               fill=(255, 255, 255))
    if t >= NFALL:
        fx.smoke_puff(img, t, NFALL, 124, _deck(124), size=8, seed=9, color=(120, 126, 160))
    cam = A.zoom_at(img, k, cx, cy)

    if CLASH <= t < WIND:
        fx.motion_lines(img, t, color=(96, 106, 150), count=16, seed=3, y0=40, y1=180, speed=700)
    if CHARGE <= t < IMPACT:
        fx.motion_lines(img, t, color=(200, 210, 240), count=26, seed=4, y0=30, y1=190, speed=1100)
    _rain(img, t, 1.0 if (t < D5 or t >= D6) else 1.3)
    A.rain_splashes(img, t, A.to_screen(cam, 0, 150)[1], min(H - 2, A.to_screen(cam, 0, 164)[1]), count=30, seed=1)
    a = max(A.lightning_amount(t, t0) for t0 in LIGHTNING)
    if a > 0:
        fx.flash(img, 0.4 * a, (220, 226, 255))
    # clash callouts
    if CLASH <= t < CLASH + 0.1:
        fx.flash(img, 0.6 * (1 - seg(t, CLASH, CLASH + 0.1)))
    sfx_text(img, 196, 56, "铿!!", t, CLASH, 0.5, color=(255, 240, 200), size=28, angle=-10)
    for i, b in enumerate(XCH):
        if b <= t < b + 0.06:
            fx.flash(img, 0.3)
        sfx_text(img, (96, 292, 196)[i], (76, 64, 48)[i], ("锵!", "铿!", "锵锵!")[i], t, b, 0.35,
                 color=(255, 240, 200), size=20, angle=(-12, 10, -6)[i])
    if HIT <= t < HIT + 0.08:
        fx.flash(img, 0.5, (255, 60, 70))
    if GLINT <= t < RISE:
        ex, ey = A.to_screen(cam, 144, _deck(140) - 15)
        fx.sparkle(img, int(ex), int(ey), t, GLINT, size=9, color=(255, 255, 255))
    if IMPACT + 0.1 <= t < D7 + 0.25:           # the slash trail lingers, fading
        u = seg(t, IMPACT + 0.1, D7 + 0.25)
        A.diag_slash(img, (lerp(20, 220, u), lerp(30, 130, u)), (W - 20, 190), width=max(1, int(5 * (1 - u))),
                     color=(255, 255, 255), edge=None)
        fx.flash(img, 0.35 * (1 - u))
    if CRACK <= t < D7C:
        sfx_text(img, 200, 52, "咔嚓!!", t, CRACK, D7C - CRACK + 0.05, color=(255, 90, 100), size=30, angle=8)
    dx, dy = 0, 0
    for t0, dur, amp in ((CLASH, 0.35, 4), (XCH[2], 0.2, 2), (HIT, 0.3, 4), (SHATTER, 0.3, 4), (NFALL, 0.2, 2)):
        ddx, ddy = fx.shake_offset(t, t0, dur, amp, seed=int(t0 * 10))
        dx, dy = dx + ddx, dy + ddy
    fx.shift(img, dx, dy)


# ------------------------------------------------------------------ E Kiheitai ship + Takasugi
def shot_e1(img, t):
    lt = t - E1
    C.sky(img, "night", t, horizon=170, body=False)
    C.big_moon(img, 192, 100, 58)
    E.ship(img, 340 - lt * 14, 58, "pirate", t, facing=-1, tod="night", haze=0.5)
    E.ship(img, 40 + lt * 8, 150, "cruiser", t, tod="night", haze=0.6)
    C.clouds(img, t * 2.5, 0, "night", seed=21, count=6, y0=40, y1=150)
    E.ship(img, lerp(262, 206, ease_out(seg(t, E1 - 0.2, E2 + 0.4))), 118 + wave(t, 0.5, 1.5), "kiheitai", t,
           facing=-1, tod="night")
    A.zoom_at(img, lerp(1.0, 1.1, seg(t, E1, E2)), 200, 110)
    _letterbox(img)


TAKA_E = (262, 160)


def shot_e2(img, t):
    lt = t - E2
    cam_x = lt * 4
    k = lerp(2.1, 2.4, ease_in_out(seg(t, E2, F1)))
    C.sky(img, "night", t, horizon=150, body=False)
    C.big_moon(img, 214, 84, 60)
    C.clouds(img, t, cam_x, "night", seed=13, count=6, y0=10, y1=110, speed=2.0)
    E.ship(img, 60 - lt * 6, 126, "pirate", t, facing=-1, tod="night", haze=0.55)
    near = A.new_layer()
    A.long_rail(near, TAKA_E[1] - 14, cam_x)
    A.hull(near, TAKA_E[1], cam_x, t)
    texpr = "smug" if t >= 17.75 else None       # a thin smirk on 「腐朽的世界」
    draw_char(near, "takasugi", TAKA_E[0], TAKA_E[1], "sit_rail", t, facing=-1, rail=False, shadow=False,
              expr=texpr)
    A.pipe_smoke(near, 249, 131, t, n=8, rise=12, drift=-8, seed=1, color=(150, 144, 182))     # kiseru smoke curling in the wind
    for i in range(3):
        r = rng("s07bf", i)
        bx = TAKA_E[0] + r.uniform(-40, 30) + wave(t, 0.23 + i * 0.05, 18, r.random())
        by = 112 + r.uniform(-16, 16) + wave(t, 0.4 + i * 0.07, 7, r.random())
        A.butterfly(near, bx, by, t, phase=i * 0.3)
    # the whole ship rides a slow swell against the still moon
    A.zoom_layer(img, near, k, 254 + wave(t, 0.21, 1.5), 128 + wave(t, 0.33, 2.2))
    fx.vignette(img, 0.35)
    _letterbox(img, bar=14)
    name_card(img, t, 16.05, 2.30, "takasugi", "高杉晋助", "鬼兵队总督｜最危险的男人", side="left")


# ------------------------------------------------------------------ F the Harusame brawl on deck
GIN_F, KAT_F = 186, 208
PIRATES = [  # (x, facing, pose, charge-to x, fly vx, fly vy)
    (96, 1, "idle", 150, -210, -170),
    (126, 1, "laugh", 166, -90, -520),
    (262, -1, "idle", 232, 90, -540),
    (290, -1, "laugh", 250, 230, -190),
    (320, -1, "idle", 272, 260, -120),
]
BACK_PIRATES = [(52, 1), (150, 1), (236, -1), (344, -1)]
R1 = (256, 226)   # the pirate Katsura cuts down on landing


def _pirate_xy(i, t):
    x0, fc, pose, xc, vx, vy = PIRATES[i]
    sway = 3 * math.sin(t * 1.3 + i * 1.7) + 2 * math.sin(t * 0.7 + i)     # prowling
    if t < RUSH:
        tf = FEINTS.get(i)
        if tf is not None and tf <= t < tf + 0.6:     # steps in, sees the blade glint, backs off
            u = seg(t, tf, tf + 0.6)
            return x0 + sway + fc * 16 * math.sin(math.pi * u), 160, ("charge" if u < 0.45 else "shock"), None
        return x0 + sway, 160, pose, None
    if t < SPIN:
        return lerp(x0 + sway, xc, ease_in(seg(t, RUSH, SPIN))), 160, "charge", None
    dt = t - (SPIN + 0.04)
    if dt < 0:
        return xc, 160, "charge", None
    return xc + vx * dt, 160 + vy * dt + 0.5 * 420 * dt * dt, "fly", dt


TWO_SHOT = (197, 136)          # centre of the Katsura/Gintoki gag close-up


def _f_camera(t):
    if t < REVEAL:
        return 1.25, 200, 128
    if t < F2:
        return lerp(2.6, 3.0, seg(t, REVEAL, F2)), KAT_F - 2, 138
    if t < F2B:
        return lerp(1.45, 1.75, ease_in_out(seg(t, F2, F2B))), 197, 134
    if t < TURN:
        return lerp(2.3, 2.45, seg(t, F2B, TURN)), 186, 138
    if t < SPIN:               # snap zoom + punch-in on the tsukkomi, then hold on the deadpan
        punch = 0.45 * (1 - ease_out(seg(t, TURN, TURN + 0.14)))
        return 3.15 + punch + 0.12 * seg(t, TURN, SPIN), TWO_SHOT[0], TWO_SHOT[1]
    return lerp(1.7, 1.25, ease_out(seg(t, SPIN, SPIN + 0.35))), 197, 130


def shot_f(img, t):
    A.deck_world(img, t, 0, ships=False)
    # background mob (darker, by the rail)
    for j, (bx, fc) in enumerate(BACK_PIRATES):
        pose = "idle" if (j + int(t * 1.2)) % 3 else "laugh"
        if t >= SPIN + 0.1 or TURN + 0.1 <= t < RUSH:
            pose = "shock"
        draw_char(img, "harusame", bx + 2 * math.sin(t * 1.1 + j), 152, pose, t + j * 0.3, facing=fc,
                  flash=0.6, flash_color=(22, 20, 44))
    fx.embers(img, t, count=18, seed=11, colors=((255, 170, 70), (255, 110, 50), (255, 230, 150)), rise=16,
              area=(0, 60, W, 160))
    # ---- pirates of the ring
    for i in range(len(PIRATES)):
        x, y, pose, dt = _pirate_xy(i, t)
        fc = PIRATES[i][1]
        if dt is not None:
            if -40 < y and -40 < x < W + 40:
                draw_char(img, "harusame", x, y, "fly", t, facing=fc, shadow=False,
                          flash=0.55 if dt < 0.04 else 0)
        elif not (t < F2 and i == 2):        # slot 2 is R1 during the opening beat
            shocked = (TURN + 0.1 <= t < RUSH and pose != "charge") or pose == "shock"
            draw_char(img, "harusame", x, y, "shock" if shocked else pose, t + i * 0.21,
                      p=0.5 if shocked else None, facing=fc, expr="angry" if pose == "charge" else None)
    # R1 charges Gintoki and gets cut down by the falling Katsura
    if t < F2:
        if t < F_LAND:
            x = lerp(R1[0], R1[1], ease_in(seg(t, F1 + 0.05, F_LAND)))
            draw_char(img, "harusame", x, 160, "charge", t, facing=-1)
        else:
            dt = t - F_LAND
            draw_char(img, "harusame", R1[1] + 240 * dt, 160 - 260 * dt + 0.5 * 380 * dt * dt, "fly", t,
                      facing=-1, shadow=False, flash=0.8 if dt < 0.05 else 0)
    # ---- heroes
    gpose, gp, gexpr, gfc = "ready", None, None, -1
    kpose, kp, kexpr, kfc = "ready", None, None, 1
    kx, ky = KAT_F, 160
    if t < F_LAND:
        u = seg(t, F1 + 0.02, F_LAND)
        ky = lerp(-30, 160, ease_in(u))
        kpose, kp = "attack", lerp(0.2, 0.5, u)
        A.fall_streaks(img, kx, ky, t, seed=1)
    elif t < F_LAND + 0.25:
        kpose, kp = "attack", lerp(0.5, 1.0, seg(t, F_LAND, F_LAND + 0.25))
    if F_LAND + 0.2 <= t < F2:
        kexpr = "determined"                      # cool reveal
    if F1 <= t < F2 and t >= F_LAND + 0.1:
        gexpr = "shock"
    talk = step_frame(t, 8) % 2 == 0
    if 19.30 <= t < 20.2:
        kexpr = "talk" if talk else "determined"
    if 21.35 <= t < 22.3:
        gexpr = "talk" if talk else "smug"
    elif 22.3 <= t < TURN:
        gexpr = "smug"
    if TURN <= t < SPIN:
        # Katsura whips round and yells at the back of Gintoki's head; Gintoki couldn't care less
        kpose, kfc, kexpr = "shout", -1, "shout"
        gpose, gexpr = "nosepick", ("blink" if NOSE <= t < NOSE + 0.12 else "normal")
        if t >= RUSH + 0.12:                      # ...until the pirates charge: both snap to guard
            kpose, kfc, kexpr = "ready", 1, "determined"
            gpose, gexpr = "ready", "angry"
    elif t >= SPIN:
        sp = lerp(0.35, 1.0, seg(t, SPIN, SPIN + 0.25))
        kpose, kp, gpose, gp = "attack", sp, "attack", sp
        if t >= SPIN + 0.5:
            gpose, gp, gexpr = "idle", None, "smug"
            kpose, kp = "ready", None
    draw_char(img, "gintoki", GIN_F, 160, gpose, t, p=gp, expr=gexpr, facing=gfc)
    draw_char(img, "katsura_short", kx, ky, kpose, t, p=kp, expr=kexpr, facing=kfc, shadow=ky > 150)
    if t >= F_LAND:
        fx.smoke_puff(img, t, F_LAND, kx, 160, size=10, seed=21, color=(170, 160, 170))
        fx.burst(img, t, F_LAND, R1[1] - 4, 144, n=12, colors=[(255, 255, 255), (255, 230, 90)], speed=(50, 130),
                 gravity=160, life=0.4, seed=22)
    if SPIN <= t < SPIN + 0.5:                   # the double spin slash
        u = seg(t, SPIN, SPIN + 0.24) * 1.4
        cx = (GIN_F + KAT_F) / 2
        A.spin_ring(img, cx, 143, 62, 14, u, a0=-90, width=3)
        A.spin_ring(img, cx, 134, 48, 10, u * 0.92, a0=90, color=(255, 250, 230), glow=(255, 190, 120), width=2)
    if NOSE + 0.1 <= t < RUSH + 0.1:             # the flicked booger arcs away
        u = seg(t, NOSE + 0.1, RUSH + 0.1)
        ImageDraw.Draw(img).point((GIN_F - 6 - 26 * u, 131 - 14 * u + 30 * u * u), fill=(170, 210, 120))

    cam = A.zoom_at(img, *_f_camera(t))
    # ---- screen-space overlays
    if F2 <= t < TURN:                            # dark foreground mob framing the two-shot
        A.fg_silhouette(img, "harusame", 24 + 4 * math.sin(t * 1.4), 212 + 2 * math.sin(t * 2.1), "idle", t,
                        scale=3, facing=1)
        A.fg_silhouette(img, "harusame", W - 22 + 4 * math.sin(t * 1.2 + 2), 214 + 2 * math.sin(t * 1.8 + 1),
                        "laugh", t + 0.4, scale=3, facing=-1)
    if REVEAL <= t < F2:
        fx.speed_lines(img, t, *A.to_screen(cam, KAT_F, 128), color=(255, 255, 255), count=40, inner=62, seed=5)
        hx, hy = A.to_screen(cam, KAT_F + 5, 124)
        fx.sparkle(img, int(hx), int(hy), t, REVEAL + 0.05, size=8)
    for i, tf in FEINTS.items():                  # the heroes' blades glint -> the pirate backs off
        if tf + 0.2 <= t < tf + 0.7:
            bx = KAT_F + 17 if PIRATES[i][1] < 0 else GIN_F - 17
            gx_, gy_ = A.to_screen(cam, bx, 146)
            fx.sparkle(img, int(gx_), int(gy_), t, tf + 0.22, size=8)
    if TURN <= t < NOSE:                          # the tsukkomi: speed lines, vein, shake, big callout
        fx.speed_lines(img, t, *A.to_screen(cam, KAT_F, 134), color=(20, 16, 34), count=50, inner=78, seed=6)
        vx, vy = A.to_screen(cam, KAT_F + 3, 124)
        A.vein(img, vx, vy)
        sfx_text(img, 300, 62, "是桂!!", t, TURN + 0.03, NOSE - TURN - 0.02, color=(255, 255, 255),
                 outline=(190, 20, 40), size=32, angle=-10, shake=2)
    if NOSE <= t < RUSH + 0.1:                    # ...and the deadpan reaction
        sfx_text(img, 84, 64, "抠抠", t, NOSE, RUSH + 0.1 - NOSE, color=(200, 200, 214), outline=(40, 36, 60),
                 size=16, angle=6, shake=0)
    if RUSH <= t < SPIN:
        fx.speed_lines(img, t, *A.to_screen(cam, 197, 134), color=(236, 236, 250), count=34, inner=96, seed=7,
                       thickness=1)
        sfx_text(img, 192, 40, "杀啊——!!", t, RUSH, SPIN - RUSH, color=(150, 230, 170), outline=(20, 40, 30),
                 size=20, angle=0, shake=2)
    if SPIN <= t < SPIN + 0.12:
        fx.flash(img, 0.6 * (1 - seg(t, SPIN, SPIN + 0.12)))
    sfx_text(img, 192, 50, "唰!!", t, SPIN, 0.7, color=(255, 255, 255), size=28, angle=-6)
    for i, (tt0, sx) in enumerate(zip(STARS, (132, 262))):   # pirates -> twinkling stars
        fx.sparkle(img, sx, 26 + i * 6, t, tt0, size=6, color=(255, 250, 200))
    dx, dy = fx.shake_offset(t, SPIN, 0.45, 5, seed=3)
    ddx, ddy = fx.shake_offset(t, F_LAND, 0.25, 3, seed=4)
    tdx, tdy = fx.shake_offset(t, TURN + 0.03, 0.3, 3, seed=5)
    fx.shift(img, dx + ddx + tdx, dy + ddy + tdy)


# ------------------------------------------------------------------ G "next time, we are enemies"
TAKA_G = (300, 108)


def shot_g(img, t):
    A.deck_world(img, t, 0, moon=(TAKA_G[0], 72, 38), ships=False, mast_x=150, right=False)
    A.upper_deck(img, 236, TAKA_G[1], t, 0)
    texpr = "smug" if t >= SMIRK else None
    draw_char(img, "takasugi", TAKA_G[0], TAKA_G[1], "smoke", t, facing=-1, expr=texpr)
    for i in range(2):
        r = rng("s07bfg", i)
        A.butterfly(img, TAKA_G[0] + r.uniform(-30, 20) + wave(t, 0.3 + i * 0.1, 14, r.random()),
                    92 + wave(t, 0.5, 6, r.random()), t, phase=i * 0.4)
    # below: Elizabeth, Gintoki and Katsura (short hair) look up at him
    draw_char(img, "elizabeth", 102, 160, "idle", t)
    draw_char(img, "gintoki", 136, 160, "arms_crossed", t)
    talk = G0 + 0.1 <= t < G0 + 0.9 and step_frame(t, 8) % 2 == 0
    draw_char(img, "katsura_short", 170, 160, "idle", t, expr="talk" if talk else "determined")
    A.pipe_smoke(img, TAKA_G[0] - 13, TAKA_G[1] - 22, t, n=7, rise=10, drift=-6, seed=2, color=(150, 144, 182))
    if t >= SMIRK:          # a slow exhale as he smirks
        fx.smoke_puff(img, t, SMIRK, TAKA_G[0] - 12, TAKA_G[1] - 20, size=7, seed=5, color=(170, 164, 196), life=1.0)
    if t < G_TAKA:          # low wide angle: the three below, Takasugi above against the moon
        u = ease_in_out(seg(t, G0, G_TAKA))
        A.zoom_at(img, lerp(1.2, 1.3, u), lerp(212, 218, u), lerp(122, 116, u))
    else:                   # reverse shot: Takasugi's close-up, moon filling the frame
        u = ease_out(seg(t, G_TAKA, END))
        A.zoom_at(img, lerp(3.0, 3.3, u), TAKA_G[0] - 4, TAKA_G[1] - 22)
    fx.vignette(img, 0.35)
    _letterbox(img, bar=14)


# ================================================================== scene
class Benizakura(Scene):
    id = "s07"
    title = "红樱篇"
    duration = END
    music = [(0, "tension"), (D0, "battle"), (E1, "tension"), (F1, "battle"), (G0, "tension")]
    music_vol = 0.55
    subs = [
        (7.80, 9.80, "okada_nizo", "红樱……还没吃饱呢。"),
        (16.10, 18.40, "takasugi", "我只是要毁掉这个腐朽的世界。"),
        (19.30, 21.30, "katsura_short", "背后交给你了，银时。"),
        (21.35, 23.30, "gintoki", "别拖后腿啊，假发。"),
        (23.35, 25.40, "katsura_short", "不是假发，是桂！"),
        (25.52, 27.75, "katsura_short", "下次见面，你我就是敌人。"),
    ]

    def render(self, img, t):
        if t < B2:
            shot_b1(img, t)
        elif t < B3:
            shot_b2(img, t)
        elif t < C0:
            shot_b3(img, t)
        elif t < D0:
            shot_c(img, t)
        elif t < E1:
            shot_d(img, t)
        elif t < E2:
            shot_e1(img, t)
        elif t < F1:
            shot_e2(img, t)
        elif t < G0:
            shot_f(img, t)
        else:
            shot_g(img, t)
        if t < B1:
            chapter_card(img, t, 0.0, B1, "红樱篇", "月夜·人斩·妖刀")
            if t >= 0.35:
                A.red_petals(img, t, count=22, seed=1, wind=34, fall=20)

    def cues(self):
        return [
            # A chapter card
            Cue(0.05, "sting_dramatic", vol=0.8),
            Cue(0.40, "gong", vol=0.7),
            Cue(0.0, "night", vol=0.45, dur=6.2),
            Cue(1.6, "river", vol=0.3, dur=4.6),
            Cue(1.6, "wind", vol=0.35, dur=8.2),
            # B1 ambush
            Cue(BEAT1, "heartbeat", vol=0.9),
            Cue(VANISH, "dash", vol=0.8),
            Cue(SLASH, "slash_big"),
            Cue(SLASH + 0.02, "impact", vol=0.7),
            # B2 / B3
            Cue(B2 + 0.1, "whoosh", vol=0.25, pitch=0.6),
            Cue(LOCK_LAND, "thud", vol=0.2, pitch=1.4),
            Cue(B3, "rain", vol=0.3, dur=4.9),
            Cue(5.05, "pop", vol=0.45),
            # C Benizakura
            Cue(DRAW, "shing"),
            Cue(DRAW + 0.05, "aura", vol=0.8),
            Cue(HB[0], "heartbeat"), Cue(HB[1], "heartbeat"), Cue(HB[2], "heartbeat"),
            Cue(7.20, "whoosh", vol=0.5),
            Cue(9.45, "shine", vol=0.8),
            # D fight
            Cue(D0, "thunder"),
            Cue(D0, "rain", vol=0.85, dur=E1 - D0),
            Cue(DASH1, "dash"),
            Cue(CLASH, "clang"), Cue(CLASH, "impact", vol=0.8),
            Cue(XCH[0], "clang", vol=0.8, pitch=1.1),
            Cue(XCH[1], "clang", vol=0.8, pitch=0.92),
            Cue(XCH[2], "clang", vol=0.9, pitch=1.05),
            Cue(WIND, "whoosh", vol=0.7, pitch=0.8),
            Cue(HIT, "slash"), Cue(HIT + 0.02, "hit"),
            Cue(KNEEL, "thud", vol=0.8),
            Cue(GLINT, "shine"),
            Cue(CHARGE, "dash"),
            Cue(IMPACT, "slash_big"), Cue(IMPACT, "impact"),
            Cue(CRACK, "glass", vol=0.6, pitch=1.3),
            Cue(SHATTER, "glass"), Cue(SHATTER, "thunder", vol=0.8), Cue(SHATTER + 0.02, "shing", vol=0.6),
            Cue(NFALL, "thud"),
            # E Kiheitai ship / Takasugi
            Cue(E1, "wind", vol=0.55, dur=F1 - E1),
            Cue(E1, "engine_hum", vol=0.35, dur=1.0),
            Cue(16.05, "whoosh", vol=0.5),
            # F deck brawl
            Cue(F1, "battle", vol=0.3, dur=G0 - F1),
            Cue(F1 + 0.02, "whoosh", vol=0.7),
            Cue(F_LAND - 0.02, "slash"), Cue(F_LAND, "land"), Cue(F_LAND + 0.01, "hit"),
            Cue(F_LAND + 0.05, "fly_away", vol=0.7),
            Cue(REVEAL, "shine"),
            Cue(FEINT, "dash", vol=0.4), Cue(FEINT + 0.22, "shine", vol=0.7),
            Cue(FEINTS[0], "dash", vol=0.35), Cue(FEINTS[0] + 0.22, "shine", vol=0.6, pitch=1.15),
            Cue(TURN, "whoosh", vol=0.55, pitch=1.3),
            Cue(TURN + 0.04, "vein"),
            Cue(TURN + 0.04, "punch", vol=0.45),
            Cue(TURN + 0.06, "shock", vol=0.6),
            Cue(NOSE + 0.02, "squeak", vol=0.3, pitch=0.8),
            Cue(NOSE + 0.12, "pop", vol=0.35, pitch=1.4),
            Cue(RUSH, "run", vol=0.5, dur=SPIN - RUSH),
            Cue(RUSH + 0.02, "charge", vol=0.35),
            Cue(SPIN, "slash_big"), Cue(SPIN + 0.02, "whoosh"),
            Cue(SPIN + 0.06, "punch_big", vol=0.8),
            Cue(SPIN + 0.1, "fly_away"),
            Cue(STARS[0], "twinkle"), Cue(STARS[1], "twinkle", pitch=1.2),
            # G
            Cue(G0, "wind", vol=0.5, dur=END - G0),
            Cue(G_TAKA, "whoosh", vol=0.3, pitch=0.7),
            Cue(SMIRK, "sting_dramatic", vol=0.55),
        ]


SCENE = Benizakura()
