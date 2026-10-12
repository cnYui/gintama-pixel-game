"""s08 真选组动乱篇 (23 s) — the Shinsengumi Crisis arc.

SHOT LIST (scene-local seconds; every time below is a named constant)
 0.00- 1.90  CHAPTER CARD 「真选组动乱篇」 over shot A (sting).
 A  1.90- 6.00  Shinsengumi HQ, night. Hijikata grips the cursed sword (tag 「妖刀·村麻纱」):
               purple aura, room goes violet, accelerating heartbeat push-in with
               zoom throbs (2.0 / 2.5 / 2.85) while Yamazaki munches anpan, oblivious.
               3.10 POOF -> snap zoom-out: Toshi in dogeza banging his forehead
               (「咚!」 3.35 / 4.10), Yamazaki drops his anpan (shock). name_card 托西 3.6.
               4.60 Toshi stands cradling an idol figure, pink moe sparkles, push-in;
               Yamazaki's burnt-out 「……」 + crow at 5.1.
 B  6.00- 8.80  Ito's dark room, round moon window, moonlight shaft.  Ito (cold stare)
               slow push-in; red-eyed rebel silhouettes fade in behind him (6.8).
               name_card 伊东鸭太郎 6.2.  7.45 CUT close-up (letterbox): glasses push ->
               big glint 7.8.
 C1 8.80-11.50  Dusk, speeding train: camera pans from the locomotive back to the
               carriage; Okita on the roof.  9.80 he leaps, 9.90 slash streak along the
               carriage, 10.05 hit-stop flash 「斩!!」, 10.15 the roof is blown away,
               rebels fly out, Okita drops in; Kondo shock -> tears of joy 「总悟～!!」.
 C2 11.50-13.60 Road beside the tracks: the Yorozuya police car screeches into frame
               (Gintoki driving, Shinpachi + Toshi in the back, siren), Kagura on the
               roof machine-gunning rebels off the train roof (hits 12.30 / 13.00).
 D  13.60-17.20 Train roof, dusk wind.  A rebel's slash knocks Toshi's figure away, it
               shatters (14.55).  Gloom push-in, purple wisps... 14.95 FLASH: blue
               aura, Toshi -> HIJIKATA (Toshi's ghost floats away waving), iai draw
               (hit 15.36, 「斩!」), rebel flies; shout pose, katana on the shoulder.
 E1 17.20-20.25 Sunset duel (letterbox, rim-lit silhouettes against a huge sun, train
               wreck smoking).  17.95 split-screen EYE CUT-IN (Hijikata / Ito, lens
               glint), 18.60 dash, 19.15 cross -> impact frame, music cuts; 19.85 Ito's
               sword drops, he kneels.
 E2 20.25-23.00 Warm push-in on Ito kneeling, smiling at the sun 「……谢谢。」, a tear,
               golden motes; Hijikata's back, smoking; Ito closes his eyes (22.0).
"""
import math

from engine.core import (Scene, Cue, W, H, seg, lerp, clamp, ease_in, ease_out, ease_in_out,
                         ease_out_back, wave, step_frame, rng)
from engine.gfx import INK, rect, overlay_rect, pset, shade, line, circle, fill, flip_h, tint
from engine import fx
from engine.text import sfx_text, name_card, chapter_card, speech_bubble, draw_text, text_width
from PIL import Image

from chars import draw_char, get_def
from chars.yamazaki import _anpan
from chars.toshi import _figure
from bg import common as C
from scenes import _s08_kit as K

# ------------------------------------------------------------------ timing
CARD_END = 1.9
# A: curse -> Toshi
A_HB = (2.0, 2.5, 2.85)                 # heartbeats (zoom throbs)
A_SHOCK, A_POOF = 2.5, 3.1
A_BANGS = (A_POOF + 0.25, A_POOF + 1.0)  # dogeza forehead hits (beg pose bow cycle 0.75 s)
A_FIG, A_END = 4.6, 6.0
# B: Ito
B0 = A_END
B_REBELS, B_CLOSE, B_GLINT, B_END = B0 + 0.8, B0 + 1.45, B0 + 1.8, B0 + 2.8
# C1: train (all relative to C0)
C0 = B_END
C_PAN, C_JUMP, C_SLASH, C_CUT, C_FLY = C0 + 0.8, C0 + 1.0, C0 + 1.1, C0 + 1.25, C0 + 1.35
C_CRY, C_END = C0 + 1.85, C0 + 2.7
# C2: police car
C2_0 = C_END
C2_HITS = (C2_0 + 0.8, C2_0 + 1.5)
C2_SHOOT = ((C2_0 + 0.4, C2_0 + 0.9), (C2_0 + 1.05, C2_0 + 1.6))
C2_END = C2_0 + 2.1
# D: awakening
D0 = C2_END
D_KNOCK, D_BREAK, D_BURST, D_DRAW, D_HIT = D0 + 0.5, D0 + 0.95, D0 + 1.35, D0 + 1.45, D0 + 1.76
D_END = D0 + 3.6
# E: sunset duel
E0 = D_END
E_EYES = E0 + 0.75
E_DASH = E_EYES + 0.65
E_CROSS = E_DASH + 0.55
E_DROP, E_CLOSE = E_CROSS + 0.7, E_CROSS + 1.1
E_SLEEP = E_CLOSE + 1.75
END = E_CLOSE + 2.75

PURPLE = ((255, 150, 255), (200, 80, 230), (130, 40, 170))
BLUE = ((255, 255, 255), (170, 225, 255), (90, 160, 255), (60, 100, 220))


def zclamp(z, cx, cy):
    z = max(1.0, z)
    hw, hh = W / (2 * z), H / (2 * z)
    return z, clamp(cx, hw, W - hw), clamp(cy, hh, H - hh)


def zoom(img, z, cx, cy):
    """fx.zoom with the centre clamped so the crop box stays inside the canvas."""
    z, cx, cy = zclamp(z, cx, cy)
    fx.zoom(img, z, cx, cy)
    return z, cx, cy


def proj(x, y, z, cx, cy):
    z, cx, cy = zclamp(z, cx, cy)
    return (x - cx) * z + W / 2, (y - cy) * z + H / 2


# ================================================================== shot A
def tag(img, x, y, text, bg=(40, 8, 52), fg=(246, 206, 255), edge=(200, 90, 240)):
    """Small manga caption tag (pixel font) with a 1px coloured frame; (x, y) = top-left."""
    w = text_width(text) + 8
    rect(img, x - 1, y - 1, w + 2, 16, INK)
    rect(img, x, y, w, 14, bg)
    rect(img, x, y, w, 1, edge)
    rect(img, x, y + 13, w, 1, edge)
    draw_text(img, x + 4, y + 1, text, fg)


def throb(t, beats, amp=0.09, dur=0.16):
    """Zoom kick that decays after each heartbeat."""
    z = 0.0
    for b in beats:
        if b <= t < b + dur:
            z += amp * (1 - (t - b) / dur) ** 2
    return z


def shot_a(img, t, ui):
    # camera: accelerating heartbeat push-in on the cursed sword, POOF snaps back wide,
    # then a slow push onto the dogeza and a moe push-in on Toshi's figure.
    if t < A_POOF:
        k = ease_in(seg(t, 1.7, A_POOF))
        z = lerp(1.7, 2.35, k) + throb(t, A_HB)
        cx, cy = lerp(180, 188, k), lerp(128, 131, k)
    elif t < A_FIG:
        k = ease_out(seg(t, A_POOF, A_FIG))
        z, cx, cy = lerp(1.5, 1.72, k), lerp(166, 170, k), 133
    else:
        k = ease_in_out(seg(t, A_FIG, A_END))
        z, cx, cy = lerp(1.72, 2.1, k), lerp(170, 182, k), lerp(133, 134, k)
    # room
    C.room_wall(img, 0, "night_in", 0, 136, "fusuma")
    C.tatami(img, 136, 0, "night_in")
    K.makoto_scroll(img, 150, 50, t)
    K.andon(img, 272, 160, t)
    curse = seg(t, 1.6, A_POOF - 0.2) if t < A_POOF else 0.0
    if curse > 0:
        fx.grade(img, mul=(1 - 0.4 * curse, 1 - 0.55 * curse, 1 - 0.15 * curse))
    HX = 200
    # ---- Yamazaki (left)
    YX = 124
    if t < A_POOF + 0.05:
        draw_char(img, "yamazaki", YX, 160, "anpan", t)
    elif t < A_FIG:
        draw_char(img, "yamazaki", YX, 160, "shock", t, p=seg(t, A_POOF + 0.05, A_POOF + 1.0))
    else:
        draw_char(img, "yamazaki", YX, 160, "idle", t, expr="dead")
    # flying anpan
    if A_POOF + 0.05 <= t < A_FIG + 2:
        u = t - (A_POOF + 0.05)
        if u < 0.45:
            ax, ay = lerp(YX + 10, YX + 26, u / 0.45), 138 - 30 * math.sin(u / 0.45 * math.pi) + 18 * (u / 0.45)
        else:
            b = u - 0.45
            ax = YX + 26 + min(b, 0.3) * 20
            ay = 156 - (abs(math.sin(min(b, 0.3) / 0.3 * math.pi)) * 5 if b < 0.3 else 0)
        _anpan(img, int(ax), int(ay), 1)
    # ---- Hijikata -> Toshi
    if t < A_POOF:
        k = seg(t, 1.6, A_POOF - 0.2)
        jit = int(wave(t, 15, 1.0 + (1.0 if t > A_HB[2] else 0.0))) if t > A_SHOCK else 0
        K.aura(img, t, HX, 160, w=26, h=40 + 12 * k, cols=PURPLE, n=int(20 + 34 * k), seed=3)
        gr = 1 + (step_frame(t, 12) % 2)
        K.draw_fig(img, "hijikata", HX + jit, 160, "guard", t,
                   expr="angry" if t < A_SHOCK else "shock",
                   glow=((150, 40, 200), gr, (230, 120, 255)), flash=0.15 + 0.1 * math.sin(t * 20),
                   flash_color=(200, 90, 255))
        K.aura(img, t, HX, 160, w=26, h=40 + 12 * k, cols=PURPLE, n=int(20 + 34 * k), seed=3, front=True)
    elif t < A_FIG:
        draw_char(img, "toshi", HX + 4, 160, "beg", t - A_POOF)
        for i, tb in enumerate(A_BANGS):          # dust from the forehead hits
            fx.smoke_puff(img, t, tb, HX + 22, 159, size=7, seed=30 + i, color=(200, 180, 150), life=0.4)
    else:
        # moe sparkle glow behind him
        g = C.glow_sprite(34, (90, 30, 60), 0.9)
        C.add_sprite(img, g, HX - g.width // 2, 138 - g.height // 2)
        draw_char(img, "toshi", HX, 160, "figure", t)
        for i in range(8):
            r = rng("moe", i)
            ph = ((t - A_FIG) * r.uniform(0.6, 1.1) + r.random()) % 1.0
            x = HX + r.uniform(-30, 30)
            y = 150 - ph * 50
            s = 1 if ph > 0.6 else 2
            K.glint_star(img, x, y, s, (255, 200, 230) if i % 2 else (255, 255, 255))
    # poof
    if A_POOF <= t < A_POOF + 0.8:
        fx.smoke_puff(img, t, A_POOF, HX, 146, size=24, seed=8, color=(230, 190, 250), life=0.5)
        fx.smoke_puff(img, t, A_POOF, HX, 140, size=16, seed=9, color=(255, 230, 255), life=0.4)
    zoom(img, z, cx, cy)
    if A_POOF <= t < A_POOF + 0.15:
        fx.flash(img, 0.6 * (1 - seg(t, A_POOF, A_POOF + 0.15)), (255, 220, 255))
    if t < A_POOF:
        fx.vignette(img, 0.55 * seg(t, 1.9, A_POOF), (30, 0, 40))
    dx, dy = fx.shake_offset(t, A_POOF, 0.35, 4, seed=1)
    if t < A_POOF:
        dx, dy = fx.shake_offset(t, A_SHOCK, A_POOF - A_SHOCK, 1, seed=2)
    for i, tb in enumerate(A_BANGS):
        if tb <= t < tb + 0.12:
            dx, dy = fx.shake_offset(t, tb, 0.12, 2, seed=40 + i)
    fx.shift(img, dx, dy)
    # ---- UI (screen space)
    sx, sy = proj(HX, 118, z, cx, cy)
    if t < A_POOF:
        # what the sword is -- the whole arc hinges on it
        if t >= 2.05:
            bx, by = proj(HX + 8, 128, z, cx, cy)          # blade tip
            bx, by = int(bx), int(by)
            tag(img, bx + 16, by - 22, "妖刀·村麻纱")
            line(img, (bx + 3, by - 2), (bx + 15, by - 14), (40, 8, 52), 3)
            line(img, (bx + 3, by - 2), (bx + 15, by - 14), (220, 120, 255))
        yx, yy = proj(YX, 128, z, cx, cy)
        sfx_text(img, int(yx) - 16, int(yy) - 18, "吧唧", t, 2.15, 0.6, color=(240, 226, 200),
                 size=12, angle=-8, outline=(40, 30, 40))
        for i, hb in enumerate(A_HB):
            sfx_text(img, int(sx) + (-62, -44, -54)[i], int(sy) + (-10, 12, -28)[i], ("咚…", "咚…", "咚!!")[i],
                     t, hb, 0.42, color=(236, 170, 255), outline=(40, 0, 50), size=(16, 20, 26)[i],
                     angle=(-6, 6, -4)[i])
    else:
        sfx_text(img, int(sx) - 44, int(sy) - 22, "噗咻～", t, A_POOF, 0.5, color=(255, 190, 240), size=20, angle=-10)
        for i, tb in enumerate(A_BANGS):
            bx, by = proj(HX + 24, 146, z, cx, cy)
            sfx_text(img, int(bx) + 6 * i, int(by) - 6, "咚!", t, tb, 0.4, color=(255, 240, 200), size=16,
                     angle=(8, -8)[i])
    if t >= A_FIG + 0.5:
        yx, yy = proj(YX, 124, z, cx, cy)
        speech_bubble(img, int(yx) + 4, int(yy) - 2, "……", t, A_FIG + 0.5, tail=(0, 1), max_w=40)
    ui.append(("name", A_POOF + 0.5, 2.2, "toshi", "托西", "被妖刀诅咒的宅男人格", "right"))


# ================================================================== shot B
REBELS = [(234, 0), (260, 1), (286, 2), (312, 3)]


def shot_b(img, t, ui):
    img.paste(K.ito_room_bg())
    IX = 180
    K.andon(img, 34, 160, t, 0.8)
    # dust motes in the moonlight shaft
    for i in range(18):
        r = rng("mdust", i)
        ph = (t * r.uniform(0.05, 0.12) + r.random()) % 1.0
        x = 112 + (ph * 60) + r.uniform(-20, 20)
        y = 40 + ph * 120 + math.sin(t + i) * 3
        if (i + step_frame(t, 6)) % 4:
            pset(img, x, y, (200, 210, 250))
    # rebels in the dark
    a = seg(t, B_REBELS, B_REBELS + 0.5)
    if a > 0:
        for i, (rx, v) in enumerate(REBELS):
            blink = ((t + i * 0.7) % 2.3) < 0.1
            K.draw_fig(img, "grunt", rx, 150, "kneel", t + i, variant=v, facing=-1, shadow=False,
                       sil=(12, 10, 20), keep=None if blink else {K.G_EYE: (255, 40, 40)},
                       alpha=a)
    # Ito
    if t < B_CLOSE:
        K.draw_fig(img, "ito", IX, 160, "idle", t, expr="blink" if (t % 2.6) < 0.12 else "cold",
                   facing=-1, tint_c=((90, 90, 170), 0.18))
    else:
        K.draw_fig(img, "ito", IX, 160, "glasses_push", t - B_CLOSE, facing=-1,
                   tint_c=((90, 90, 170), 0.12))
    # camera
    if t < B_CLOSE:
        k = ease_in_out(seg(t, B0, B_CLOSE))
        z, cx, cy = lerp(1.6, 1.95, k), lerp(170, 190, k), lerp(123, 131, k)
    else:
        k = ease_out(seg(t, B_CLOSE, B_END))
        z, cx, cy = lerp(2.6, 2.95, k), IX - 4, 139
    zoom(img, z, cx, cy)
    if t >= B_CLOSE:
        fx.vignette(img, 0.4 + 0.3 * clamp(1 - abs(t - B_GLINT - 0.1) * 3), (40, 0, 14))
        # big glint on the lens
        u = t - B_GLINT
        if 0 <= u < 0.45:
            lx, ly = proj(IX - 4, 141, z, cx, cy)
            s = int(4 + 16 * math.sin(clamp(u / 0.45) * math.pi))
            K.glint_star(img, lx, ly, s)
        fx.letterbox(img, seg(t, B_CLOSE, B_CLOSE + 0.2), 20)
    ui.append(("name", B0 + 0.2, 2.2, "ito", "伊东鸭太郎", "参谋｜野心家", "right"))


# ================================================================== shot C1 (train)
TR_TOP = 92                     # carriage sprite top (screen, cam 0)
CAR_X = 64                      # main carriage left x (train coords)
LOCO_X = CAR_X + K.CAR_W + 10
LEFT_X = CAR_X - K.CAR_W - 10
FLOOR_T = 143                   # feet inside the carriage (they stand on the seats)
RAIL_Y = TR_TOP + K.CAR_H + 4   # 168
WIRE_Y = 78
IN_GRUNTS = [(100, 0, 1), (136, 1, 1), (222, 2, -1), (252, 3, -1)]
KONDO_X = 180
OKITA_X = 250


def _mid_band():
    """Wrapping strip of dusk silhouettes (trees, farmhouses) — parallax layer."""
    from PIL import Image, ImageDraw
    P, Hh = 640, 56
    im = Image.new("RGBA", (P, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = rng("midband")
    col, col2 = (104, 58, 86), (84, 44, 72)
    x = 0
    while x < P:
        kind = r.random()
        if kind < 0.55:
            rr = r.randint(7, 13)
            cxx = x + rr
            d.ellipse([cxx - rr, Hh - 8 - 2 * rr, cxx + rr, Hh - 8], fill=col)
            d.rectangle([cxx - 1, Hh - 10, cxx + 1, Hh], fill=col2)
            x += 2 * rr + r.randint(0, 10)
        elif kind < 0.8:
            w = r.randint(22, 34)
            h = r.randint(10, 16)
            d.rectangle([x, Hh - h, x + w, Hh], fill=col2)
            d.polygon([(x - 3, Hh - h), (x + w // 2, Hh - h - 9), (x + w + 3, Hh - h)], fill=col)
            if r.random() < 0.7:
                d.rectangle([x + 5, Hh - h + 4, x + 9, Hh - h + 7], fill=(255, 196, 110))
            x += w + r.randint(6, 18)
        else:
            x += r.randint(10, 30)
    d.rectangle([0, Hh - 6, P, Hh], fill=col2)
    return im


def mid_band(img, t, speed, y):
    band = K.cached("midband", _mid_band)
    off = int(t * speed) % band.width
    img.paste(band, (-off, y), band)
    img.paste(band, (band.width - off, y), band)


def track(img, t, y, speed=720):
    """Rails + blurred gravel/sleepers rushing past (y = rail top)."""
    rect(img, 0, y, W, H - y, (92, 70, 78))
    rect(img, 0, y + 6, W, 3, (70, 52, 60))
    f = step_frame(t, 30)
    r = rng("gravel", f)
    for i in range(70):
        gx = r.randint(0, W)
        gy = y + 2 + r.randint(0, H - y - 2)
        L = r.randint(8, 30)
        rect(img, gx, gy, L, 1, (74, 56, 64) if i % 2 else (116, 92, 96))
    rect(img, 0, y, W, 2, (170, 164, 176))
    rect(img, 0, y + 2, W, 1, (60, 50, 60))
    # grass verge streaks
    for i in range(24):
        gx = r.randint(0, W)
        rect(img, gx, y + 12 + r.randint(0, 10), r.randint(10, 26), 1, (70, 96, 70))


def dusk_backdrop(img, t, horizon=150, mt_y=146, mt_speed=900, band_y=112, band_speed=420):
    C.sky(img, "dusk", t, horizon=horizon)
    C.clouds(img, t, cam_x=t * 45, tod="dusk", count=6, y1=70)
    C.far_mountains(img, t * mt_speed, "dusk", y=mt_y)
    if band_y is not None:
        mid_band(img, t, band_speed, band_y)


def train_car(img, x, y, t, seed=0):
    spr = K.full_lit_carriage(seed)
    img.paste(spr, (int(x), int(y)), spr)
    K.bogies(img, int(x), int(y) + K.CAR_H, t)


def bellows(img, x, y):
    rect(img, x, y + 14, 10, 46, INK)
    for k in range(0, 46, 3):
        rect(img, x + 1, y + 15 + k, 8, 2, (40, 38, 50) if (k // 3) % 2 else (64, 62, 76))


def shot_c1(img, t, ui):
    cam = lerp(190, 0, ease_in_out(seg(t, C0, C_PAN)))
    dusk_backdrop(img, t)
    # catenary poles (behind the train) + wire
    for k in range(-1, 4):
        px = (k * 150 - t * 720) % 600 - 60
        rect(img, int(px), WIRE_Y - 10, 3, RAIL_Y - WIRE_Y + 10, (46, 30, 54))
        rect(img, int(px), WIRE_Y - 6, 18, 2, (46, 30, 54))
    rect(img, 0, WIRE_Y, W, 1, (40, 28, 46))
    track(img, t, RAIL_Y)
    bob = [1 if step_frame(t + ph, 12) % 4 == 0 else 0 for ph in (0, 0.13, 0.27)]
    # left carriage
    train_car(img, LEFT_X - cam, TR_TOP + bob[0], t, seed=1)
    bellows(img, LEFT_X + K.CAR_W - cam, TR_TOP + bob[0])
    bellows(img, CAR_X + K.CAR_W - cam, TR_TOP + bob[1])
    # locomotive + pantograph + headlight beam
    lx = LOCO_X - cam
    loco = K.loco_sprite()
    K.pantograph(img, int(lx) + 104, TR_TOP + K.ROOF_Y - 2 + bob[2], WIRE_Y, t)
    img.paste(loco, (int(lx), TR_TOP + bob[2]), loco)
    K.bogies(img, int(lx) - 20, TR_TOP + K.CAR_H + bob[2], t)
    if lx + 206 < W + 60:
        hx, hy = lx + 206, TR_TOP + K.CUT_Y + 16
        for i in range(0, 90, 2):
            w = 2 + i * 0.35
            if (i // 2) % 2 == 0:
                overlay_rect(img, int(hx + i), int(hy - w / 2), 2, int(w), (255, 240, 170), 0.35 * (1 - i / 90))
    # ---- main carriage
    mx, my = CAR_X - cam, TR_TOP + bob[1]
    upper, lower = K.carriage_parts()
    u = t - C_FLY
    if t < C_CUT:
        img.paste(K.interior_sprite(), (int(mx) + 1, my + K.ROOF_Y + 8))
    # passengers
    fy = FLOOR_T + bob[1]
    if t < C_FLY + 0.02:
        for gx, v, fc in IN_GRUNTS:
            K.draw_fig(img, "grunt", gx - cam, fy, "ready", t + v * 0.3, variant=v, facing=fc, shadow=False)
    if t < C_CUT:
        draw_char(img, "kondo", KONDO_X - cam, fy, "ready", t, expr="angry", shadow=False)
    elif t < C_CRY:
        draw_char(img, "kondo", KONDO_X - cam, fy, "shock", t, p=seg(t, C_CUT, C_CRY), shadow=False)
    else:
        draw_char(img, "kondo", KONDO_X - cam, fy, "cry", t, shadow=False)
    # Okita inside after the drop
    if t >= C_FLY:
        dv = seg(t, C_FLY, C_FLY + 0.14)
        oy = lerp(40, fy, ease_in(dv))
        if dv < 1:
            draw_char(img, "okita", OKITA_X - cam, oy, "jump", t, facing=-1, shadow=False)
        elif t < C_FLY + 0.4:
            draw_char(img, "okita", OKITA_X - cam, fy, "land", t, p=seg(t, C_FLY + 0.14, C_FLY + 0.4),
                      facing=-1, shadow=False)
        else:
            draw_char(img, "okita", OKITA_X - cam, fy, "shoulder", t, facing=-1, expr="sadist", shadow=False)
    # upper part of the carriage: intact, then blown away
    if t < C_FLY:
        off = 1 if t >= C_CUT else 0
        img.paste(upper, (int(mx) + off, my), upper)
    elif u < 0.9:
        ang = u * 34
        spr = upper.rotate(ang, resample=0, expand=True)
        dx = -(u ** 2) * 760 - u * 80
        dy = -ease_out(clamp(u / 0.35)) * 34 + max(0.0, u - 0.35) ** 2 * 60
        cxp = mx + K.CAR_W / 2 + dx
        cyp = my + K.CUT_Y / 2 + dy
        img.paste(spr, (int(cxp - spr.width / 2), int(cyp - spr.height / 2)), spr)
    img.paste(lower, (int(mx), my + K.CUT_Y), lower)
    K.bogies(img, int(mx), my + K.CAR_H, t)
    # Okita on the roof before the slash
    if t < C_SLASH:
        oy = TR_TOP + K.ROOF_Y + bob[1]
        if t < C_JUMP:
            draw_char(img, "okita", OKITA_X + 16 - cam, oy, "shoulder", t, facing=-1, expr="sadist")
        else:
            jy = oy - (t - C_JUMP) * 700
            draw_char(img, "okita", OKITA_X + 16 - cam, jy, "jump", t, facing=-1, shadow=False)
    # rebels blown out of the carriage
    if t >= C_FLY:
        for i, (gx, v, fc) in enumerate(IN_GRUNTS):
            uu = u - i * 0.04
            if uu < 0:
                continue
            vx = -300 - i * 60
            vy = -260 - (i % 2) * 80
            x = gx - cam + vx * uu
            y = fy + vy * uu + 420 * uu * uu
            if -40 < x < W + 40 and y > -40:
                K.draw_fig(img, "grunt", x, y, "fly", t + i * 0.2, variant=v, facing=fc, shadow=False)
    # slash streak
    cut_y = my + K.CUT_Y
    if C_SLASH <= t < C_FLY + 0.1:
        head = lerp(W + 10, mx - 10, seg(t, C_SLASH, C_SLASH + 0.12))
        x0, x1 = int(head), W + 10
        if t < C_FLY:
            rect(img, x0, cut_y - 2, x1 - x0, 5, (150, 210, 255))
            rect(img, x0, cut_y - 1, x1 - x0, 3, (255, 255, 255))
        else:
            rect(img, x0, cut_y, x1 - x0, 1, (255, 255, 255))
        if t < C_CUT:
            fx.burst(img, t, C_SLASH, int(head), cut_y, n=10, colors=[(255, 255, 255), (170, 220, 255)],
                     speed=(40, 120), life=0.25, seed=int(t * 30))
    if C_CUT <= t < C_FLY + 0.3:
        fx.burst(img, t, C_FLY, int(mx + K.CAR_W / 2), cut_y, n=24,
                 colors=[(255, 240, 200), (90, 120, 120), (200, 200, 210)], speed=(60, 200), life=0.7, seed=41)
    # foreground pole whoosh (only while establishing / after the reveal)
    for tp in (C0 + 0.25, C0 + 2.58):
        if tp <= t < tp + 0.1:
            px = lerp(W + 20, -30, seg(t, tp, tp + 0.1))
            rect(img, int(px), 0, 9, H, (26, 16, 30))
            rect(img, int(px) + 1, 0, 2, H, (60, 40, 60))
    fx.motion_lines(img, t, color=(255, 214, 190), count=10, direction=-1, seed=8, y0=20, y1=70,
                    speed=1400, length=(20, 60))
    # camera
    k = ease_in_out(seg(t, C0 + 1.5, C0 + 2.4))
    z, zcx, zcy = zoom(img, lerp(1.0, 1.4, k), lerp(196, 214, k), lerp(124, 126, k))
    if C_CUT <= t < C_FLY:
        fx.flash(img, 0.55 * (1 - seg(t, C_CUT, C_FLY)))
    dx, dy = fx.shake_offset(t, C_CUT, 0.4, 4, seed=5)
    if t < C_CUT:
        dx, dy = fx.shake_offset(t, C0, 3.0, 1, freq=12, seed=6)
    fx.shift(img, dx, dy)
    sfx_text(img, 192, 60, "斩!!", t, C_CUT, 0.8, color=(255, 255, 255), outline=(20, 40, 90), size=30, angle=-6)
    if t >= C_CRY:
        kx, ky = proj(KONDO_X - cam, fy - 40, z, zcx, zcy)
        sfx_text(img, int(kx), int(ky), "总悟～!!", t, C_CRY, 0.85, color=(255, 230, 120), size=14, angle=4)


# ================================================================== shot C2 (police car)
T2_TOP = 70                     # background train (sits higher = farther away)
CARX, CARY = 104, 104
ROAD_Y = 153


def shot_c2(img, t, ui):
    lt = t - C2_0
    dusk_backdrop(img, t, horizon=126, mt_y=104, mt_speed=500, band_y=None)
    # embankment
    rect(img, 0, T2_TOP + K.CAR_H + 4, W, ROAD_Y - (T2_TOP + K.CAR_H + 4), (104, 78, 80))
    rect(img, 0, T2_TOP + K.CAR_H + 3, W, 2, (170, 160, 170))
    f = step_frame(t, 30)
    r = rng("emb", f)
    for i in range(12):
        rect(img, r.randint(0, W), r.randint(T2_TOP + K.CAR_H + 6, ROAD_Y - 1), r.randint(6, 20), 1,
             (84, 64, 70) if i % 2 else (126, 100, 96))
    # background train (hazed), drifting back slowly
    tx = 30 - lt * 36
    for i in range(3):
        x = tx + i * (K.CAR_W + 10) - (K.CAR_W + 10)
        train_car(img, x, T2_TOP, t, seed=2 + i)
    overlay_rect(img, 0, T2_TOP, W, K.CAR_H + 4, (230, 140, 120), 0.18)
    # rebels on the train roof
    roof_y = T2_TOP + K.ROOF_Y
    targets = [(tx + 250, C2_HITS[0], 1), (tx + 316, C2_HITS[1], 3)]
    for i, (gx, th, v) in enumerate(targets):
        if t < th:
            K.draw_fig(img, "grunt", gx, roof_y, "ready", t + i * 0.4, variant=v, facing=-1, shadow=False,
                       expr="shout" if step_frame(t, 6) % 3 == 0 else None)
        elif t < th + 0.12:
            K.draw_fig(img, "grunt", gx, roof_y, "hit", t, p=seg(t, th, th + 0.12), variant=v, facing=-1,
                       flash=0.6, shadow=False)
        else:
            uu = t - th - 0.12
            K.draw_fig(img, "grunt", gx + 120 * uu, roof_y - 260 * uu + 300 * uu * uu, "fly", t, variant=v,
                       facing=-1, shadow=False)
        fx.burst(img, t, th, int(gx), roof_y - 16, n=14, colors=[(255, 250, 180), (255, 180, 60)],
                 speed=(40, 120), life=0.4, seed=60 + i)
    # road
    rect(img, 0, ROAD_Y, W, H - ROAD_Y, (74, 64, 86))
    rect(img, 0, ROAD_Y, W, 2, (200, 190, 200))
    rect(img, 0, ROAD_Y + 2, W, 3, (56, 48, 66))
    off = (t * 570) % 64
    for k in range(-1, 8):
        x = k * 64 - off
        rect(img, int(x), ROAD_Y + 30, 30, 3, (230, 224, 200))
    r2 = rng("asph", f)
    for i in range(40):
        rect(img, r2.randint(0, W), r2.randint(ROAD_Y + 6, H), r2.randint(6, 26), 1, (64, 56, 76))
    # ---- car + crew: screeches in from the left, then jostles while racing the train
    ent = ease_out(seg(lt, 0.0, 0.45))
    cxp = int(lerp(-190, CARX, ent) + 5 * math.sin(max(0.0, lt - 0.45) * 3.2))
    bob = -1 if step_frame(t, 12) % 3 == 0 else 0
    if lt < 0.55:
        bob -= int(3 * math.sin(seg(lt, 0.3, 0.55) * math.pi))     # hop as it lands on the road
    cy = CARY + bob
    # exhaust puffs
    for k in range(4):
        t0 = math.floor((t - k * 0.13) / 0.52) * 0.52 + k * 0.13
        fx.smoke_puff(img, t, t0, cxp - 2, cy + 44, size=6, seed=k + int(t0 * 10), color=(170, 160, 170), life=0.5)
    fy = cy + 43
    talking = lt < 1.2
    draw_char(img, "gintoki", cxp + 110, fy, "talk" if talking else "idle", t,
              expr=None if talking else "angry", shadow=False)
    draw_char(img, "shinpachi", cxp + 58, fy, "shout", t, shadow=False)
    draw_char(img, "toshi", cxp + 78, fy + 1, "figure", t, shadow=False)
    car = K.police_car_sprite()
    img.paste(car, (cxp, cy), car)
    K.car_wheels(img, cxp, cy, t)
    K.siren_glow(img, cxp + 85, cy + 4, t)
    # Kagura on the roof, machine-gunning the rebels
    shooting = any(a <= t < b for a, b in C2_SHOOT)
    kx, ky = cxp + 64, cy + 8
    if shooting:
        draw_char(img, "kagura", kx, ky, "umbrella_shoot", t, weapon=26, arm_f=112, shadow=False)
    else:
        draw_char(img, "kagura", kx, ky, "ready", t, weapon=26, arm_f=112, expr="determined", shadow=False)
    if shooting:
        tgt = targets[0] if t < C2_SHOOT[1][0] else targets[1]
        sx0, sy0 = kx + 20, ky - 28
        sx1, sy1 = tgt[0], roof_y - 16
        for k in range(4):
            ph = ((t * 7) + k / 4) % 1.0
            px, py = lerp(sx0, sx1, ph), lerp(sy0, sy1, ph)
            ex, ey = lerp(sx0, sx1, max(0, ph - 0.06)), lerp(sy0, sy1, max(0, ph - 0.06))
            line(img, (ex, ey), (px, py), (255, 240, 150))
        if step_frame(t, 15) % 2 == 0:
            K.glint_star(img, sx0, sy0, 3, (255, 250, 200))
    # tyre smoke on the entrance + dust from the wheels
    if lt < 0.9:
        for k in range(3):
            fx.smoke_puff(img, t, C2_0 + 0.3 + k * 0.08, CARX + 30 - k * 10, CARY + 56, size=10,
                          seed=50 + k, color=(190, 180, 186), life=0.55)
    for k in range(6):
        rr = rng("dust2", k, step_frame(t, 15))
        pset(img, cxp + 20 - rr.randint(0, 30), cy + 56 - rr.randint(0, 4), (150, 130, 140))
    fx.motion_lines(img, t, color=(250, 200, 170), count=8, direction=-1, seed=9, y0=10, y1=40,
                    speed=1300, length=(20, 50))
    k = ease_in_out(seg(t, C2_0, C2_END))
    z, zcx, zcy = zoom(img, lerp(1.26, 1.34, k), lerp(196, 204, k), 118)
    dx, dy = fx.shake_offset(t, C2_0, 2.1, 1, freq=15, seed=7)
    if C2_0 + 0.3 <= t < C2_0 + 0.6:
        dx, dy = fx.shake_offset(t, C2_0 + 0.3, 0.3, 3, seed=8)
    fx.shift(img, dx, dy)
    sfx_text(img, 70, 84, "吱——!!", t, C2_0 + 0.3, 0.55, color=(255, 255, 255), outline=(40, 20, 40), size=16, angle=-8)
    for th, (gx, _, _) in zip(C2_HITS, targets):
        sx, sy = proj(gx - 30, roof_y - 14, z, zcx, zcy)
        sfx_text(img, int(sx), int(sy), "哒哒哒!", t, th - 0.35, 0.6, color=(255, 230, 90), size=16, angle=8)


# ================================================================== shot D (awakening)
D_FLOOR = 150


def roof_top(img, t):
    """Train roof seen from the side, close (feet at D_FLOOR)."""
    y = D_FLOOR
    rect(img, 0, y - 1, W, 1, INK)
    rect(img, 0, y, W, 2, K.T_ROOF_L)
    rect(img, 0, y + 2, W, 4, K.T_ROOF)
    rect(img, 0, y + 6, W, 2, K.T_ROOF_D)
    rect(img, 0, y + 8, W, 2, K.T_FRAME)
    rect(img, 0, y + 10, W, H - y - 10, K.T_BODY)
    rect(img, 0, y + 12, W, 1, K.T_CREAM_D)
    for wx in range(8, W, 24):
        rect(img, wx - 1, y + 16, 22, 24, INK)
        rect(img, wx, y + 17, 20, 22, (206, 150, 98))
        rect(img, wx, y + 29, 20, 10, (150, 56, 58))
    for vx in (40, 150, 290):
        rect(img, vx - 1, y - 5, 16, 5, INK)
        rect(img, vx, y - 4, 14, 4, K.T_ROOF)
        rect(img, vx, y - 4, 14, 1, K.T_ROOF_L)


def shot_d(img, t, ui):
    TX, GX0 = 176, 232
    burst = t >= D_BURST
    dark = seg(t, D_BREAK, D_BURST) if not burst else 1 - seg(t, D_BURST, D_BURST + 1.2) * 0.6
    dusk_backdrop(img, t, horizon=170, mt_y=158, mt_speed=700, band_y=None)
    fx.motion_lines(img, t, color=(255, 214, 190), count=16, direction=-1, seed=11, y0=20, y1=140,
                    speed=1500, length=(20, 70))
    if dark > 0:
        fx.grade(img, mul=(1 - 0.5 * dark, 1 - 0.45 * dark, 1 - 0.25 * dark))
    if burst:
        g = C.glow_sprite(60, (40, 80, 160), 1.0 - 0.5 * seg(t, D_BURST, D_END))
        C.add_sprite(img, g, TX - g.width // 2, 128 - g.height // 2)
    roof_top(img, t)
    # --- rebel
    if t < D0 + 0.25:
        gx = lerp(270, GX0, seg(t, D0, D0 + 0.25))
        K.draw_fig(img, "grunt", gx, D_FLOOR, "run", t, variant=2, facing=-1)
    elif t < D0 + 0.75:
        K.draw_fig(img, "grunt", GX0, D_FLOOR, "attack", t, p=seg(t, D0 + 0.25, D0 + 0.75), variant=2, facing=-1)
    elif t < D_DRAW:
        K.draw_fig(img, "grunt", GX0, D_FLOOR, "ready", t, variant=2, facing=-1, expr="happy")
    elif t < D_HIT:
        K.draw_fig(img, "grunt", GX0, D_FLOOR, "attack", t, p=0.3 * seg(t, D_DRAW, D_HIT), variant=2,
                   facing=-1, expr="shout")
    else:
        uu = t - D_HIT
        if uu < 0.8:
            K.draw_fig(img, "grunt", GX0 + 20 + 240 * uu, D_FLOOR - 40 - 320 * uu + 200 * uu * uu, "fly", t,
                       variant=2, facing=-1, shadow=False, flash=0.5 if uu < 0.08 else 0)
    # --- the figure
    if D_KNOCK <= t < D_BREAK:
        k = seg(t, D_KNOCK, D_BREAK)
        fx_, fy_ = lerp(TX + 8, TX + 30, k), lerp(126, D_FLOOR, k) - 26 * math.sin(k * math.pi)
        _figure(img, int(fx_), int(fy_), t)
    elif t >= D_BREAK:
        # broken figure pieces on the roof
        bx = TX + 30
        rect(img, bx - 4, D_FLOOR - 2, 9, 2, (190, 196, 214))
        rect(img, bx - 4, D_FLOOR - 1, 9, 1, (130, 136, 160))
        for i, (ddx, ddy, c) in enumerate(((-7, -1, (255, 120, 170)), (6, -1, (70, 214, 200)), (9, 0, (255, 224, 200)),
                                          (-10, 0, (255, 120, 170)), (2, -3, (70, 214, 200)))):
            rect(img, bx + ddx, D_FLOOR - 1 + ddy, 2, 1, c)
        fx.burst(img, t, D_BREAK, bx, D_FLOOR - 4, n=16, colors=[(255, 120, 170), (70, 214, 200), (255, 255, 255)],
                 speed=(30, 90), gravity=260, life=0.5, seed=77)
    # --- Toshi -> Hijikata
    if not burst:
        if t < D_KNOCK:
            draw_char(img, "toshi", TX, D_FLOOR, "figure", t)
        elif t < D_BREAK:
            draw_char(img, "toshi", TX, D_FLOOR, "shock", t, p=seg(t, D_KNOCK, D_BREAK))
        else:
            k = seg(t, D_BREAK + 0.1, D_BURST)
            if k > 0:
                K.aura(img, t, TX, D_FLOOR, w=18, h=30 * k + 8, cols=PURPLE, n=int(8 + 22 * k), seed=5)
            draw_char(img, "toshi", TX, D_FLOOR, "idle", t, expr="gloom" if t < D_BURST - 0.12 else "angry")
    else:
        fade = 1 - 0.6 * seg(t, D_BURST + 0.6, D_END)
        n = int(60 * fade)
        # the otaku personality leaves: a translucent Toshi floats up, waving goodbye
        gk = seg(t, D_BURST + 0.3, D_BURST + 1.9)
        if 0 < gk < 1:
            gxx = TX - 26 - 10 * gk + math.sin(gk * 9) * 2
            gyy = D_FLOOR - 6 - 44 * ease_out(gk)
            K.draw_fig(img, "toshi", gxx, gyy, "wave", t, expr="happy", shadow=False,
                       tint_c=((255, 214, 246), 0.45), alpha=0.8 * (1 - gk ** 2))
            if step_frame(t, 10) % 2:
                K.glint_star(img, gxx + 10, gyy - 30, 2, (255, 220, 250))
        K.aura(img, t, TX, D_FLOOR, w=30, h=58 * fade + 10, cols=BLUE, n=n, seed=6, speed=2.2)
        gl = ((110, 180, 255), 2, (220, 240, 255)) if step_frame(t, 12) % 2 else ((80, 140, 255), 1)
        if t < D0 + 2.15:
            p = seg(t, D_DRAW, D_DRAW + 0.7)
            pose, kw = ("draw", dict(p=p)) if t >= D_DRAW else ("guard", dict(expr="shout"))
        elif t < D0 + 3.0:
            pose, kw = "ready", dict(expr="shout" if step_frame(t, 8) % 3 else "angry")
        else:
            pose, kw = "shoulder", dict(expr="angry")
        K.draw_fig(img, "hijikata", TX, D_FLOOR, pose, t, glow=gl,
                   flash=0.8 * (1 - seg(t, D_BURST, D_BURST + 0.25)), **kw)
        K.aura(img, t, TX, D_FLOOR, w=30, h=58 * fade + 10, cols=BLUE, n=n, seed=6, speed=2.2, front=True)
        if D_HIT - 0.03 <= t < D_HIT + 0.25:
            fx.slash_arc(img, GX0 + 4, D_FLOOR - 18, 22, 200, 340, seg(t, D_HIT - 0.03, D_HIT + 0.2) * 1.6,
                         (255, 255, 255), 4)
    # --- camera
    if t < D_BREAK:
        z, cx, cy = 1.7, 205, 128
    elif t < D_BURST:
        k = ease_in_out(seg(t, D_BREAK, D_BURST))
        z, cx, cy = lerp(1.7, 2.4, k), lerp(205, 178, k), lerp(128, 132, k)
    elif t < D0 + 2.15:
        z, cx, cy = 1.8, 196, 126
    else:
        k = ease_in_out(seg(t, D0 + 2.15, D_END))
        z, cx, cy = lerp(1.8, 2.15, k), lerp(196, 184, k), lerp(126, 128, k)
    zoom(img, z, cx, cy)
    if D_BURST <= t < D_BURST + 0.45:
        sx, sy = proj(TX, D_FLOOR - 18, z, cx, cy)
        fx.speed_lines(img, t, int(sx), int(sy), color=(200, 230, 255), count=40, inner=46, seed=12)
    if burst:
        fx.flash(img, 0.9 * (1 - seg(t, D_BURST, D_BURST + 0.3)), (230, 245, 255))
    if D_HIT <= t < D_HIT + 0.1:
        fx.flash(img, 0.45, (255, 255, 255))
    dx, dy = fx.shake_offset(t, D_BURST, 0.5, 5, seed=13)
    if D_HIT <= t < D_HIT + 0.3:
        dx, dy = fx.shake_offset(t, D_HIT, 0.3, 4, seed=14)
    fx.shift(img, dx, dy)
    fx.letterbox(img, seg(t, D_BURST, D_BURST + 0.2), 12)
    # UI
    bx, by = proj(TX + 30, D_FLOOR - 14, z, cx, cy)
    sfx_text(img, int(bx), int(by) + 10, "啪嚓", t, D_BREAK, 0.5, color=(255, 170, 200), size=16, angle=-10)
    gx, gy = proj(GX0 + 10, D_FLOOR - 30, z, cx, cy)
    sfx_text(img, int(gx), int(gy), "斩!", t, D_HIT, 0.7, color=(255, 255, 255), outline=(20, 40, 110), size=28)
    if D_BURST <= t < D_BURST + 0.6:
        sfx_text(img, 58, 44, "轰!!", t, D_BURST, 0.6, color=(170, 225, 255), outline=(10, 30, 80), size=30, angle=-10)


# ================================================================== shot E (sunset duel)
HJ0, IT0 = 104, 280
E_FLOOR = 156
TEAR_XY = (148, 142)            # under Ito's right lens in E2 (kneel, head_dy 0)
DARK = (22, 8, 22)
RIM = (255, 170, 100)


def sunset_world(img, t):
    img.paste(K.sunset_bg())
    # wreck smoke
    for k in range(7):
        ph = ((t * 0.35) + k / 7) % 1.0
        for j, (sx, sy) in enumerate(((300, 108), (352, 110))):
            x = sx + ph * -30 + math.sin(ph * 6 + k) * 3
            y = sy - ph * 70
            r = 3 + ph * 9
            c = (70 - int(ph * 20), 30, 50) if j == 0 else (84, 36, 56)
            from engine.gfx import circle
            circle(img, int(x), int(y), int(r), c)
    K.wind_motes(img, t, count=30, seed=3, col=(255, 190, 120), area=(0, 30, W, 170), speed=140)


EYE_SCALE, EYE_ROWS = 8, (7, 16)       # head rows 7..15 (bangs, eyes, mouth) x8 -> 144x72


def eye_strip(who, expr, flip=False):
    def mk():
        h = get_def(who).head(expr)
        c = h.crop((0, EYE_ROWS[0], h.width, EYE_ROWS[1]))
        c = c.resize((c.width * EYE_SCALE, c.height * EYE_SCALE), Image.NEAREST)
        c = tint(c, (255, 140, 80), 0.12)
        return flip_h(c) if flip else c
    return K.cached(("eyes", who, expr, flip), mk)


def eye_cutin(img, t):
    """Split-screen duel cut-in: Hijikata's eyes (top, from the left) vs Ito's glasses
    (bottom, from the right), wind streaks, a glint on each."""
    u = t - E_EYES
    fill(img, (0, 0, 0))
    bands = ((24, 104), (112, 192))
    for (y0, y1), col, col2 in zip(bands, ((96, 26, 50), (70, 20, 52)), ((150, 50, 60), (120, 40, 80))):
        rect(img, 0, y0, W, y1 - y0, col)
        for i in range(10):                              # sunset haze bands
            r = rng("eyeband", y0, i)
            rect(img, 0, y0 + r.randint(0, y1 - y0 - 1), W, 1, col2)
    sw = 18 * EYE_SCALE
    oy = (80 - (EYE_ROWS[1] - EYE_ROWS[0]) * EYE_SCALE) // 2
    # top: Hijikata slides in from the left
    k1 = ease_out(seg(u, 0.0, 0.12))
    hx = int(lerp(-sw, 60, k1) + 10 * u)
    s = eye_strip("hijikata", "normal")
    img.paste(s, (hx, bands[0][0] + oy), s)
    # bottom: Ito slides in from the right; lenses flash white at the glint
    k2 = ease_out(seg(u, 0.06, 0.18))
    ix = int(lerp(W, W - 60 - sw, k2) - 10 * u)
    ex = "glint" if 0.38 <= u < 0.56 else "cold"
    s = eye_strip("ito", ex, flip=True)
    img.paste(s, (ix, bands[1][0] + oy), s)
    fx.motion_lines(img, t, color=(255, 190, 150), count=7, direction=-1, seed=71, y0=26, y1=102,
                    speed=900, length=(30, 90))
    fx.motion_lines(img, t, color=(230, 150, 190), count=7, direction=1, seed=72, y0=114, y1=190,
                    speed=900, length=(30, 90))
    if 0.24 <= u < 0.5:                                  # Hijikata's eye gleams first...
        K.glint_star(img, hx + 102, bands[0][0] + oy + 44, int(3 + 9 * math.sin(seg(u, 0.24, 0.5) * math.pi)))
    if 0.38 <= u < 0.62:                                 # ...then Ito's lens
        K.glint_star(img, ix + 40, bands[1][0] + oy + 42, int(3 + 12 * math.sin(seg(u, 0.38, 0.62) * math.pi)))
    fx.letterbox(img, 1.0, 22)


def shot_e(img, t, ui):
    if E_EYES <= t < E_DASH:
        eye_cutin(img, t)
        return
    sunset_world(img, t)
    close = t >= E_CLOSE
    if not close:
        # ---- E1 wide silhouettes
        kd = ease_in(seg(t, E_DASH, E_CROSS - 0.05))
        hx, ix = lerp(HJ0, 262, kd), lerp(IT0, 122, kd)
        if t < E_DASH:
            hp, ip, kwh, kwi = "ready", "ready", {}, {}
        elif t < E_CROSS - 0.05:
            hp, ip, kwh, kwi = "run", "run", {}, {}
        elif t < E_CROSS + 0.15:
            hp, ip = "attack", "attack"
            kwh = kwi = dict(p=0.45 + 0.15 * seg(t, E_CROSS - 0.05, E_CROSS + 0.15))
        else:
            hp, ip = "attack", "attack"
            kwh = kwi = dict(p=0.97)
        impact = E_CROSS <= t < E_CROSS + 0.16
        sil = dict(sil=DARK, rim=RIM, shadow=False)
        if impact:
            # anime impact frame: paper-white world, ink-black silhouettes and sun ring
            fill(img, (255, 250, 240))
            circle(img, K.SUN_X, K.SUN_Y, K.SUN_R, None, (20, 6, 20))
            circle(img, K.SUN_X, K.SUN_Y, K.SUN_R - 1, None, (20, 6, 20))
            rect(img, 0, K.HORIZON_E, W, 2, (20, 6, 20))
            sil = dict(sil=(20, 6, 20), rim=None, shadow=False)
        if t >= E_DROP + 0.1:
            hp, kwh = "idle", {}
        # Hijikata faces right, Ito faces left; after the cross they have their backs to each other
        K.draw_fig(img, "hijikata", hx, E_FLOOR, hp, t, facing=1, rim_side=1 if t < E_CROSS else -1, **kwh, **sil)
        if t < E_DROP:
            K.draw_fig(img, "ito", ix, E_FLOOR, ip, t, facing=-1, rim_side=-1 if t < E_CROSS else 1, **kwi, **sil)
        else:
            K.draw_fig(img, "ito", ix, E_FLOOR, "kneel", t, facing=-1, rim_side=1, expr="smile", **sil)
            # his sword falling / stuck in the ground
            k = seg(t, E_DROP, E_DROP + 0.18)
            sx, sy = ix - 14 - 8 * k, lerp(E_FLOOR - 20, E_FLOOR - 8, ease_in(k))
            ang = lerp(-20, -60, k)
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            line(img, (sx - ca * 10, sy + sa * 10), (sx + ca * 8, sy - sa * 8), DARK, 2)
            line(img, (sx - ca * 10, sy + sa * 10 - 1), (sx + ca * 8, sy - sa * 8 - 1), RIM, 1)
        if E_DASH <= t < E_CROSS:
            for x0, dirn in ((hx, -1), (ix, 1)):
                for i in range(4):
                    yy = E_FLOOR - 6 - i * 7
                    rect(img, int(x0 + dirn * (10 + i * 3)), yy, 14, 1, RIM)
            fx.burst(img, t, E_DASH, HJ0, E_FLOOR - 2, n=10, colors=[(90, 40, 60)], speed=(20, 60), life=0.5, seed=21)
            fx.burst(img, t, E_DASH, IT0, E_FLOOR - 2, n=10, colors=[(90, 40, 60)], speed=(20, 60), life=0.5, seed=22)
        if not impact:
            K.grass_tips(img, t, E_FLOOR + 6, col=(30, 10, 26), seed=1, dens=2, hmax=8)
            K.grass_tips(img, t + 0.3, H - 20, col=(14, 4, 14), seed=2, dens=3, hmax=14)
        # camera
        if t < E_DASH:
            z = lerp(1.45, 1.6, ease_in_out(seg(t, E0, E_EYES)))
        elif t < E_CROSS + 0.15:
            z = 1.6
        else:
            z = lerp(1.6, 1.5, ease_out(seg(t, E_CROSS + 0.15, E_CLOSE)))
        zoom(img, z, 192, 128)
        if impact:
            line(img, (20, 190), (364, 30), (20, 6, 20), 7)
            line(img, (20, 190), (364, 30), (228, 40, 50), 3)
        elif E_CROSS + 0.16 <= t < E_CROSS + 0.4:
            fx.flash(img, 0.5 * (1 - seg(t, E_CROSS + 0.16, E_CROSS + 0.4)), (255, 230, 200))
        dx, dy = fx.shake_offset(t, E_CROSS, 0.4, 3, seed=31)
        fx.shift(img, dx, dy)
        fx.letterbox(img, ease_out(seg(t, D_END, D_END + 0.4)), 22)
    else:
        # ---- E2 warm push-in on Ito
        IX, HX = 150, 226
        warm = ((255, 150, 90), 0.28)
        # light rays from the sun
        K.sun_rays(img, t)
        closed = t >= E_SLEEP
        K.draw_fig(img, "hijikata", HX, E_FLOOR, "idle", t, facing=1, sil=(34, 12, 30), rim=RIM, rim_side=-1,
                   shadow=False)
        # his smoke curling up in the wind
        for i in range(16):
            ph = ((t * 0.5) + i / 16) % 1.0
            x = HX + 6 - ph * 26 + math.sin(ph * 7 + t * 1.5) * 2.5
            y = E_FLOOR - 24 - ph * 34
            c = (240, 214, 200) if ph < 0.5 else (200, 150, 150)
            pset(img, x, y, c)
            if ph < 0.35:
                pset(img, x + 1, y, c)
        hd = 2 if closed else 1
        K.draw_fig(img, "ito", IX, E_FLOOR, "kneel", t, facing=1, expr="sleep" if closed else "smile",
                   tint_c=warm, head_dy=hd, sheathed=False, shadow=False)
        # a single tear under the glasses
        tk = seg(t, E_CLOSE + 1.0, E_CLOSE + 2.3)
        if 0 < tk < 1:
            ty = TEAR_XY[1] + hd + int(4 * ease_in(tk))
            pset(img, TEAR_XY[0], ty, (190, 235, 255))
            if tk < 0.8:
                pset(img, TEAR_XY[0], ty - 1, (120, 190, 240))
        fx.embers(img, t, count=26, seed=4, colors=((255, 230, 150), (255, 200, 120), (255, 255, 220)),
                  rise=12, area=(80, 40, 280, 170))
        K.grass_tips(img, t, E_FLOOR + 3, col=(40, 14, 30), seed=5, dens=2, hmax=6)
        k = ease_in_out(seg(t, E_CLOSE, END))
        z, cx, cy = lerp(2.1, 2.75, k), lerp(172, 160, k), lerp(134, 137, k)
        zoom(img, z, cx, cy)
        fx.letterbox(img, 1.0, 22)


# ================================================================== scene
class MayoCrisis(Scene):
    id = "s08"
    title = "真选组动乱篇"
    duration = END
    music = [(0, "tension"), (C0, "battle"), (E_CROSS, None), (E_CLOSE, "sad")]
    music_vol = 0.55
    subs = [
        (A_POOF + 0.2, A_END - 0.2, "toshi", "对不起！我马上去买炒面面包！"),
        (B0 + 0.45, B_END - 0.1, "ito", "近藤局长……该退场了。"),
        (C0 + 0.15, C_END - 0.2, None, "伊东叛变！列车上的近藤陷入重围——"),
        (C2_0, C2_END, "gintoki", "这委托，万事屋接下了！"),
        (D0 + 1.05, D_END, "hijikata", "我是……真选组副长——土方十四郎！！"),
        (E_CLOSE + 0.4, E_CLOSE + 2.35, "ito", "……谢谢。"),
    ]

    def render(self, img, t):
        ui = []
        if t < A_END:
            shot_a(img, t, ui)
        elif t < B_END:
            shot_b(img, t, ui)
        elif t < C_END:
            shot_c1(img, t, ui)
        elif t < C2_END:
            shot_c2(img, t, ui)
        elif t < D_END:
            shot_d(img, t, ui)
        else:
            shot_e(img, t, ui)
        for kind, t0, dur, cid, title, desc, side in ui:
            name_card(img, t, t0, dur, cid, title, desc, side=side)
        chapter_card(img, t, 0.0, CARD_END, "真选组动乱篇", "妖刀·叛乱·鬼之副长")

    def cues(self):
        c = [
            Cue(0.15, "sting_dramatic", vol=0.8),
            # A: cursed sword -> Toshi
            Cue(1.7, "aura", vol=0.7), Cue(2.15, "chomp", vol=0.35),
            Cue(A_HB[0], "heartbeat", vol=0.8), Cue(A_HB[1], "heartbeat", vol=0.95),
            Cue(A_HB[2], "heartbeat", vol=1.0), Cue(A_HB[2] + 0.05, "shock", vol=0.4),
            Cue(A_POOF, "pop"), Cue(A_POOF, "boing", vol=0.6),
            Cue(A_POOF + 0.1, "shock", vol=0.7),
            Cue(A_BANGS[0], "thud", vol=0.6), Cue(A_BANGS[1], "thud", vol=0.6),
            Cue(A_POOF + 0.45, "sweat", vol=0.5), Cue(A_POOF + 0.55, "squeak", vol=0.5),
            Cue(A_FIG, "sparkle", vol=0.8), Cue(A_FIG + 0.5, "crow", vol=0.7),
            # B: Ito
            Cue(B0, "night", vol=0.35, dur=2.8), Cue(B0 + 0.05, "heartbeat", vol=0.6),
            Cue(B_REBELS, "aura", vol=0.45), Cue(B_CLOSE, "impact", vol=0.5), Cue(B_GLINT, "shine"),
            # C1: train
            Cue(C0, "train", vol=0.8, dur=2.75), Cue(C0, "wind", vol=0.35, dur=2.75),
            Cue(C0 + 0.25, "whoosh", vol=0.6), Cue(C_JUMP, "jump"), Cue(C_SLASH, "slash_big"),
            Cue(C_CUT, "impact"), Cue(C_FLY, "crash"), Cue(C_FLY + 0.02, "fly_away", vol=0.7),
            Cue(C_FLY + 0.05, "hit"), Cue(C_FLY + 0.1, "hit", pitch=1.15), Cue(C_FLY + 0.15, "punch", vol=0.8),
            Cue(C_FLY + 0.14, "land", vol=0.7), Cue(C_CRY, "shock", vol=0.6), Cue(C0 + 2.58, "whoosh", vol=0.5),
            # C2: police car
            Cue(C2_0, "engine_hum", vol=0.7, dur=2.1), Cue(C2_0, "dash", vol=0.7),
            Cue(C2_0 + 0.3, "whoosh", vol=0.5), Cue(C2_0 + 0.55, "land", vol=0.6),
            Cue(C2_SHOOT[0][0], "machinegun"), Cue(C2_HITS[0], "hit"), Cue(C2_HITS[0] + 0.04, "clang", vol=0.6),
            Cue(C2_SHOOT[1][0], "machinegun"), Cue(C2_HITS[1], "hit"), Cue(C2_HITS[1] + 0.05, "fly_away", vol=0.7),
            # D: awakening
            Cue(D0, "wind", vol=0.55, dur=3.6), Cue(D0 + 0.05, "dash", vol=0.7), Cue(D_KNOCK - 0.05, "slash"),
            Cue(D_KNOCK + 0.02, "shock", vol=0.6), Cue(D_BREAK, "glass"), Cue(D0 + 1.05, "heartbeat", vol=0.9),
            Cue(D_BURST - 0.15, "charge", vol=0.6), Cue(D_BURST, "aura"), Cue(D_BURST, "impact"),
            Cue(D_BURST + 0.2, "twinkle", vol=0.35),
            Cue(D_HIT - 0.08, "shing"), Cue(D_HIT, "slash_big"), Cue(D_HIT + 0.02, "hit"),
            Cue(D_HIT + 0.06, "fly_away", vol=0.6),
            # E: sunset duel
            Cue(E0, "wind", vol=0.7, dur=END - E0), Cue(E_EYES, "whoosh", vol=0.5),
            Cue(E_EYES + 0.24, "shing", vol=0.6), Cue(E_EYES + 0.38, "shine", vol=0.8),
            Cue(E_DASH, "dash"), Cue(E_CROSS, "slash_big"),
            Cue(E_CROSS, "impact"), Cue(E_DROP + 0.18, "clang", vol=0.5), Cue(E_DROP + 0.12, "thud", vol=0.6),
            Cue(E_CLOSE + 0.4, "bell", vol=0.3),
        ]
        return c


SCENE = MayoCrisis()
