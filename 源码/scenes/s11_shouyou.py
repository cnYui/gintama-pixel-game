"""s11 松阳老师 (26 s) — sepia flashback. music: flashback -> sad (cliff) -> silence after the cut.

SHOT LIST (scene-local seconds)
  0.00- 1.90  A1 Battlefield of the dead at dusk (old-film sepia), fading in from s10's white.
                 Pull-back reveal from circling crows / smoke columns to the field of broken
                 spears & banners; kid Gintoki sits on a dark heap of the fallen munching a rice
                 ball, sword on his shoulder. Shouyou walks in out of the low sun.
  1.90- 3.70  A2 Two-shot (x2): the kid freezes mid-chew ("!"), the rice ball rolls away, he leaps
                 down 2.25, lands 2.52 and points his blade at Shouyou (trembling). name_card 吉田松阳.
  3.70- 5.60  A3 Close-up (x3) in a god-ray: Shouyou offers his sheathed katana at chest height; 4.30
                 the kid lowers his blade, 4.55 drops it (clang 4.72), steps in, 4.88 takes the sword
                 and 5.20 pulls it upright to his chest.
                 「这把剑，是用来斩断你心中的弱小，守护你自己的灵魂的。」 2.25-5.45
  5.60- 7.85  B1 Shoukasonjuku yard (sunny, sakura). Shouyou & kid Katsura watch from the veranda.
                 Kid Takasugi 「银时！今天一定要赢你！」 charges 6.20, leaps 6.72; lazy Gintoki
                 (bokuto on shoulder) BONK 6.87 (hit-stop 0.1 s, flash, speed lines, 啪！) -> Takasugi
                 spins away, bounces down 7.40 with dizzy stars; Katsura sweat-drop.
  7.85-10.65  B2 Classroom: Katsura studies, Takasugi (bump) sulks, Gintoki sleeps (snot bubble,
                 Zzz). Shouyou creeps over 8.3-9.05 「上课睡觉可不行哦～」, dark aura, bubble pops 9.25,
                 wind-up, HEADBUTT 9.62 (咚!! speed lines, flash, desk splits): Gintoki KO'd flat
                 with a giant steaming bump; Shouyou still smiling; the other two crack up.
 10.65-11.45  C1 Night — the school burns (flames, embers, smoke). Naraku lead the bound Shouyou
                 away; the kids kneel behind a Naraku guard.
 11.45-12.55  C2 CU Shouyou stops, looks back over his shoulder (11.67) and smiles
                 「银时，大家就拜托你了。」 11.60-13.62
 12.55-13.65  C3 CU kid Gintoki crying, reaching out.
 13.65-15.65  D1 Joui war (blood-red sky, rain, amanto army + ships): Shiroyasha dashes in
                 (tracking), 14.26 slash (impact frame, lightning) — four amanto blasted away.
                 name_card 白夜叉.
 15.65-17.60  D2 Sunset ridge: the Joui four — Katsura, Shiroyasha, young Takasugi (both eyes),
                 Sakamoto laughing — light up out of silhouette. name_card 坂本辰马.
 17.60-19.40  E1 (music -> sad, letterbox) Grey cliff: Shouyou kneels (bound) at the edge, Shiroyasha
                 behind him; Oboro holds the bound Katsura & Takasugi; Naraku ranks; crows leave.
 19.40-21.15  E2 CU Shouyou turns (19.75) — the smile with tears 「谢谢你。」 19.45-21.12
 21.15-21.70  E3a Low CU Shiroyasha: the sword rises from behind his head to overhead (arms
                 drawn behind the big chibi head so the crying face stays visible), glint, tremble.
 21.70-22.15  E3b CU young Takasugi (both eyes) screams 「住手——！！」 21.45-23.13 (J-cut)
 22.15-22.50  E3c Gintoki — 22.36 the blade comes down -> 22.50 CUT TO WHITE (no gore).
 22.50-24.35  W  Silence on white; sensei's smile lingers as a faint sepia after-image, a single
                 big tear falls and lands 23.90 (bell, ripple).
 24.35-26.00  F  Present day, back in s10's sunset blade-lock with Oboro (same poses, grinding
                 sparks): close two-shot pulling back,
                 Gintoki's eyes sunk in shadow under his bangs; fade out.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import (Scene, Cue, W, H, seg, lerp, clamp, ease_in, ease_out, ease_in_out,
                         step_frame, rng, arc)
from engine.gfx import INK, rect, overlay_rect
from engine import fx
from engine.text import draw_text, sfx_text, name_card
from chars import draw_char, get_def
from chars.rig import OX, OY
from bg import common as C
from scenes import _s11_art as A

# ---------------------------------------------------------------- timing
T_A2, T_A3 = 1.90, 3.70
T_JUMP, T_LANDK = 2.25, 2.52                   # kid notices ("!") -> leaps off the heap
T_GIVE, T_TAKE, T_HUG = 4.88, 5.04, 5.20       # sword handed over -> kid pulls it to his chest
T_B1, T_BONK, T_B2, T_HB = 5.60, 6.87, 7.85, 9.62
HITSTOP = 0.1
T_C1, T_C2, T_C3 = 10.65, 11.45, 12.55
T_D1, T_SLASH, T_D2 = 13.65, 14.26, 15.65
T_E1, T_E2, T_TURN, T_E3, T_E3B, T_E3C = 17.60, 19.40, 19.75, 21.15, 21.70, 22.15
T_FALL = 22.36
T_WHITE, T_TEAR, T_F = 22.50, 23.90, 24.35
DUR = 26.0

CUTS = (T_B1, T_B2, T_C1, T_D1, T_D2)          # memory-flash cuts


# ================================================================ helpers
def view(img, k, cx, cy):
    """Zoom the finished world frame about (cx, cy) (clamped so no border shows).
    Returns the world->screen mapping."""
    hw, hh = W / (2 * k), H / (2 * k)
    cx = clamp(cx, hw, W - hw)
    cy = clamp(cy, hh, H - hh)
    if k > 1.001:
        fx.zoom(img, k, cx, cy)
    return lambda x, y: ((x - cx) * k + W / 2, (y - cy) * k + H / 2)


def hand_rel(cid, arm, lean=0, bob=0, facing=1):
    """Front-hand offset from the feet anchor for standing rig characters."""
    d = get_def(cid)
    hip_y = OY - 1 - d.leg_len
    tx = OX - d.hip[0] + lean
    ty = hip_y - d.hip[1] + bob
    sx, sy = tx + d.shoulder_f[0], ty + d.shoulder_f[1]
    a = math.radians(arm)
    hx, hy = sx + math.sin(a) * d.arm_len, sy + math.cos(a) * d.arm_len
    return (hx - OX) * facing, hy - OY


def tremble(t, amp=1, fps=15):
    return (0, amp, 0, -amp)[step_frame(t, fps, 4)]


def _shake(img, t, t0, dur, amp):
    dx, dy = fx.shake_offset(t, t0, dur, amp, seed=int(t0 * 10))
    fx.shift(img, dx, dy)


def _vig_arr():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    k = np.clip((d - 0.55) / 0.75, 0, 1) * 0.62
    k = np.floor(k * 4 + C.bayer(H, W) * 0.999) / 4
    return (1 - k)[..., None].astype(np.float32)


_VIG = _vig_arr()
_LUM = np.array([0.299, 0.587, 0.114], np.float32)


def flashback_grade(img, t, amount):
    """Old-film memory look: sepia + contrast, dark dithered vignette, flicker,
    grain, the odd scratch."""
    a = np.asarray(img).astype(np.float32)
    g = a @ _LUM
    sep = np.stack([g * 1.06 + 24, g * 0.93 + 12, g * 0.70 + 4], -1)
    a = a * (1 - amount) + sep * amount
    a = (a - 118) * 1.12 + 116
    f = step_frame(t, 12)
    fl = 1.0 + 0.025 * math.sin(f * 2.1) + (0.035 if f % 13 == 0 else 0.0)
    a *= _VIG * fl
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB"))
    d = ImageDraw.Draw(img)
    r = rng("grain", f)
    for _ in range(60):
        x, y = r.randrange(W), r.randrange(H)
        d.point((x, y), fill=(226, 208, 178) if r.random() < 0.5 else (60, 46, 38))
    if r.random() < 0.18:
        x = r.randrange(30, W - 30)
        y0 = r.randrange(0, H // 2)
        d.line([(x, y0), (x + r.choice((-1, 0, 1)), y0 + r.randrange(30, 120))], fill=(208, 190, 160))
    if r.random() < 0.12:
        x, y = r.randrange(W), r.randrange(H)
        d.ellipse([x, y, x + 2, y + 1], fill=(40, 30, 26))


# ================================================================ shot A: battlefield
MOUND_X, MOUND_BOT = 282, 168
KID_SEAT = (280, 143)
KID_LAND = 250


def shot_A(img, t, ov):
    if t < T_A2:
        u = ease_in_out(seg(t, 0.0, 1.75))
        cam = lerp(0, 30, ease_in_out(seg(t, 0, T_A2)))
        k, cx, cy = lerp(1.45, 1.0, u), lerp(246, 192, u), lerp(78, 108, u)
    elif t < T_A3:
        cam = 30
        k, cx, cy = 2.0, 194 + (t - T_A2) * 2.5, 131
    else:
        cam = 30
        k = lerp(2.75, 3.0, ease_out(seg(t, T_A3, T_B1)))
        cx, cy = 199, 139
    A.battlefield(img, t, cam)
    A.crows_circling(img, t, n=6, seed=1, cx=230 - cam * 0.2, cy=46, rx=110, ry=18)
    ms = A.mound_sprite()
    mx = MOUND_X - cam
    img.paste(ms, (int(mx - ms.width // 2), MOUND_BOT - ms.height), ms)
    A.crow_sit(img, mx + 37, MOUND_BOT - 29, -1, t, seed=2)

    kx = KID_SEAT[0] - cam
    if t < T_A2:
        # Shouyou walks in out of the sun; the kid munches on the heap
        sx = lerp(38, 122, seg(t, 0.35, T_A2)) - cam
        draw_char(img, "shouyou", sx, 160, "walk", t, facing=1)
        draw_char(img, "gintoki_kid", kx, KID_SEAT[1], "eat", t, facing=-1, shadow=False)
    elif t < T_A3:
        sx = 198 - cam
        draw_char(img, "shouyou", sx, 160, "smile", t, facing=1)
        if t < T_JUMP:
            # freeze mid-chew: "!" -> the rice ball slips from his hand
            draw_char(img, "gintoki_kid", kx, KID_SEAT[1] + (1 if t < 1.97 else 0), "eat", 1.9, facing=-1,
                      expr="shock", shadow=False)
        elif t < T_LANDK:
            u = seg(t, T_JUMP, T_LANDK)
            x, y = arc((kx, KID_SEAT[1]), (KID_LAND - cam, 160), u, 16)
            draw_char(img, "gintoki_kid", x, y, "jump", t, facing=-1, expr="angry", weapon=110, shadow=False)
        else:
            fx.smoke_puff(img, t, T_LANDK, KID_LAND - cam, 160, size=7, seed=3, color=(150, 120, 110))
            draw_char(img, "gintoki_kid", KID_LAND - cam + tremble(t, 1, 10), 160, "ready", t, facing=-1,
                      expr="angry")
        # the dropped rice ball rolls down the heap
        if t >= T_JUMP:
            u = seg(t, T_JUMP, T_JUMP + 0.45)
            rx, ry = arc((kx - 4, KID_SEAT[1] - 8), (kx - 22, 160), u, 6)
            A.rice_ball(img, rx, ry)
    else:
        # god-ray onto the two of them
        A.light_shaft(img, 150, 34, 160, 90, 0, 172, (255, 236, 196), 0.17, t)
        sx = 206 - cam
        kx0 = 254 - cam
        kid_x = kx0 if t < 4.55 else lerp(kx0, kx0 - 12, ease_out(seg(t, 4.55, 4.85)))
        sh_arm = (38, 32)                              # offering the sword with both hands, chest height
        shx, shy = hand_rel("shouyou", sh_arm[0])
        s_hand = (sx + shx, 160 + shy)
        if t < T_TAKE:
            draw_char(img, "shouyou", sx, 160, "idle", t, facing=1, expr="smile", arm_f=sh_arm[0], arm_b=sh_arm[1],
                      sheathed=False)
        elif t < T_TAKE + 0.25:
            u = ease_out(seg(t, T_TAKE, T_TAKE + 0.25))
            draw_char(img, "shouyou", sx, 160, "idle", t, facing=1, expr="smile", arm_f=lerp(sh_arm[0], 30, u),
                      arm_b=lerp(sh_arm[1], 20, u), sheathed=False)
        else:
            draw_char(img, "shouyou", sx, 160, "smile", t, facing=1, sheathed=False)
        k_arm = 70
        khx, khy = hand_rel("gintoki_kid", k_arm, facing=-1)
        if t < 4.30:
            draw_char(img, "gintoki_kid", kid_x + tremble(t, 1, 10), 160, "ready", t, facing=-1, expr="angry")
        elif t < 4.55:
            draw_char(img, "gintoki_kid", kid_x, 160, "ready", t, facing=-1, expr="shock",
                      weapon=-62, arm_f=22, legs="stand")
        elif t < 4.85:
            draw_char(img, "gintoki_kid", kid_x, 160, "walk", t, facing=-1, expr="sad", sheathed=False)
        elif t < T_HUG:
            draw_char(img, "gintoki_kid", kid_x, 160, "idle", t, facing=-1, expr="sad", props=[], sheathed=False,
                      arm_f=k_arm, arm_b=k_arm - 6)
        else:
            draw_char(img, "gintoki_kid", kid_x, 160, "idle", t, facing=-1, expr="blink" if t < T_HUG + 0.1 else None)
        # the sword: in sensei's hands -> slides into the kid's -> pulled upright to his chest
        k_hand = (kid_x + khx, 160 + khy)
        if t < T_GIVE:
            A.sheathed_sword(img, s_hand[0] + 3, s_hand[1] - 1, 0, 22)
            fx.sparkle(img, int(s_hand[0] + 10), int(s_hand[1] - 2), t, 3.95, 4)
        elif t < T_TAKE:
            u = ease_in_out(seg(t, T_GIVE, T_TAKE))
            A.sheathed_sword(img, lerp(s_hand[0] + 3, k_hand[0] - 6, u), lerp(s_hand[1] - 1, k_hand[1] - 1, u), 0, 22)
        elif t < T_HUG:
            u = ease_out(seg(t, T_TAKE, T_HUG))
            A.sheathed_sword(img, lerp(k_hand[0] - 6, k_hand[0] - 1, u), lerp(k_hand[1] - 1, k_hand[1] + 1, u),
                             lerp(0, 90, u), 22)
        if T_HUG <= t < T_HUG + 0.6:
            fx.sparkle(img, int(kid_x - 3), int(140), t, T_HUG, 5)
        # the dropped blade
        if t >= 4.55:
            u = seg(t, 4.55, 4.72)
            bx = lerp(kx0 - 8, kx0 - 3, u)
            if u < 1:
                A.blade_on_ground(img, bx, lerp(150, 160, ease_in(u)), ang=lerp(-70, 8, u))
            else:
                A.blade_on_ground(img, bx, 161, ang=8)
                fx.burst(img, t, 4.72, bx, 160, n=6, colors=[(255, 250, 220)], speed=(20, 50), gravity=120,
                         life=0.3, seed=7)
        A.light_motes(img, t, (120, 60, 300, 170), n=22, seed=5)
    A.scatter(img, cam, t)
    to_s = view(img, k, cx, cy)
    if T_A2 <= t < T_JUMP + 0.1:
        ex, ey = to_s(kx - 2, KID_SEAT[1] - 30)
        ov.append(lambda im: sfx_text(im, int(ex), int(ey), "!", t, 1.94, T_JUMP + 0.1 - 1.94, size=22, angle=-6,
                                      shake=0))
    ov.append(lambda im: name_card(im, t, 1.95, 2.2, "shouyou", "吉田松阳", "松下私塾的老师"))
    return 0.74


# ================================================================ shot B1: the yard duel
GX_B1 = 284


def shot_B1(img, t, ov):
    A.yard(img, t)
    # veranda watchers
    draw_char(img, "shouyou", 152, 138, "sit", t, facing=1, shadow=False)
    kat_expr = None
    if T_BONK <= t < T_BONK + 0.35:
        kat_expr = "shock"
    elif t >= T_BONK + 0.35:
        kat_expr = "blink" if (t % 1.2) < 0.15 else "normal"
    draw_char(img, "katsura_kid", 206, 138, "sit", t, facing=1, expr=kat_expr, shadow=False)
    if t >= T_BONK + 0.3:
        A.sweat_drop(img, 214, 118 + int(seg(t, T_BONK + 0.3, T_BONK + 0.9) * 3))
    if 6.2 <= t < 6.8:
        fx.motion_lines(img, t, color=(255, 250, 235), count=14, direction=-1, seed=4, y0=128, y1=164,
                        speed=700, length=(14, 40))
    # Takasugi
    if t < 6.2:
        draw_char(img, "takasugi_kid", 128, 160, "ready", t, facing=1, expr="shout",
                  dy=-2 if step_frame(t, 6, 2) else 0)
    elif t < 6.72:
        u = ease_in(seg(t, 6.2, 6.72))
        x = lerp(128, 240, u)
        draw_char(img, "takasugi_kid", x, 160, "run", t, facing=1, expr="shout", weapon=125, arm_f=165)
        if step_frame(t, 8, 2) == 0:
            fx.smoke_puff(img, t, t - 0.05, x - 6, 160, size=4, seed=int(t * 8), color=(200, 184, 150))
    elif t < T_BONK:
        u = seg(t, 6.72, T_BONK)
        x, y = arc((240, 160), (262, 157), u, 12)
        draw_char(img, "takasugi_kid", x, y, "jump", t, facing=1, expr="shout", weapon=100, arm_f=170)
    elif t < T_BONK + HITSTOP:
        # hit-stop: frozen at the contact point, flashing white
        draw_char(img, "takasugi_kid", 262, 150, "hit", t, p=0.3, facing=1, expr="hurt", shadow=False,
                  flash=0.85 if step_frame(t, 30) % 2 == 0 else 0.3)
    elif t < 7.4:
        u = seg(t, T_BONK + HITSTOP, 7.4)
        x, y = arc((262, 150), (160, 162), u, 30)
        draw_char(img, "takasugi_kid", x, y, "fly", t, facing=1, shadow=False, rot=int(u * 540) // 45 * 45)
        if step_frame(t, 15, 2) == 0:
            fx.sparkle(img, int(x + 6), int(y - 20), t, t - 0.03, 3, (255, 240, 170))
    else:
        fx.smoke_puff(img, t, 7.4, 160, 162, size=9, seed=9, color=(210, 192, 160))
        bounce = int(4 * (1 - ease_out(seg(t, 7.4, 7.55)))) if t < 7.55 else 0
        draw_char(img, "takasugi_kid", 160, 170 - bounce, "lie", t, facing=-1, expr="hurt", shadow=False)
        A.dizzy_stars(img, 168, 152, t)
        A.bump(img, 171, 157, 2 + (1 if t > 7.5 else 0))
    # Gintoki: lazy, bokuto on the shoulder -> one lazy swing
    if t < 6.72:
        draw_char(img, "gintoki_kid", GX_B1, 160, "shoulder", t, facing=-1, weapon_kind="bokuto",
                  expr="blink" if (t % 1.3) < 0.12 else "normal")
    elif t < 7.15 + HITSTOP:
        if t < T_BONK:            # quick wind-up, then the swing meets his head mid-arc
            pp = 0.35 * seg(t, 6.72, 6.80) + 0.1 * seg(t, 6.80, T_BONK)
        else:
            pp = 0.45 + 0.55 * seg(t, T_BONK + HITSTOP, 7.15 + HITSTOP)
        draw_char(img, "gintoki_kid", GX_B1, 160, "attack", t, p=pp, facing=-1,
                  weapon_kind="bokuto", expr="normal")
    else:
        draw_char(img, "gintoki_kid", GX_B1, 160, "shoulder", t, facing=-1, weapon_kind="bokuto",
                  expr="blink" if (t % 1.4) < 0.12 else "normal")
    fx.burst(img, t, T_BONK, 264, 140, n=16, colors=[(255, 255, 255), (255, 236, 150)], speed=(50, 130),
             gravity=60, life=0.45, seed=12)
    k = 1.55 + 0.1 * ease_in_out(seg(t, T_B1, T_BONK))
    cxx = 208
    if t >= T_BONK:
        pk = 1 - ease_out(seg(t, T_BONK, T_BONK + 0.45))
        k += 0.3 * pk
        cxx += 40 * pk
    to_s = view(img, k, cxx, 129)
    bx, by = to_s(266, 128)
    if T_BONK <= t < T_BONK + 0.2:
        ov.append(lambda im: fx.speed_lines(im, t, int(bx), int(by) + 10, color=(255, 250, 236), count=22,
                                            inner=46, seed=3, thickness=1))
    if T_BONK <= t < T_BONK + 0.034:
        ov.append(lambda im: fx.flash(im, 0.55))
    ov.append(lambda im: sfx_text(im, int(bx), int(by) - 16, "啪!", t, T_BONK, 0.75, size=26))
    ov.append(lambda im: _shake(im, t, T_BONK, 0.3, 4))
    return 0.62


# ================================================================ shot B2: headbutt
KAT_X, TAKA_X, GIN_X = 98, 166, 266
SEAT_Y = 158


def _sensei(img, *a, **k):
    """Shouyou in class: no sword at the hip."""
    k.setdefault("sheathed", False)
    return draw_char(img, "shouyou", *a, **k)


def shot_B2(img, t, ov):
    A.classroom(img, t)
    after = t >= T_HB
    laugh = t >= T_HB + 0.25
    bob = -1 if step_frame(t, 8, 2) else 0
    if laugh:
        draw_char(img, "katsura_kid", KAT_X, SEAT_Y + bob, "sit", t, facing=1, expr="happy", arm_f=150,
                  shadow=False)
        draw_char(img, "takasugi_kid", TAKA_X, SEAT_Y - bob, "sit", t, facing=1, expr="happy", arm_f=95,
                  shadow=False)
    else:
        draw_char(img, "katsura_kid", KAT_X, SEAT_Y, "sit", t, facing=-1,
                  arm_f=62 + (6 if step_frame(t, 4, 2) else 0), expr="shock" if after else None, shadow=False)
        draw_char(img, "takasugi_kid", TAKA_X, SEAT_Y, "sit", t, facing=-1, expr="shock" if after else "angry",
                  shadow=False)
    A.desk(img, KAT_X - 13, SEAT_Y - 1, props="books")
    A.desk(img, TAKA_X - 13, SEAT_Y - 1, props="paper")
    A.bump(img, TAKA_X + (1 if laugh else -1), SEAT_Y - 21, 2)
    # Gintoki
    if t < 9.8:
        crushed = t >= T_HB
        draw_char(img, "gintoki_kid", GIN_X, SEAT_Y + (2 if crushed else 0), "sit", t, facing=-1,
                  expr="hurt" if crushed else "sleep", head_dy=3 if crushed else 1, arm_f=70, shadow=False)
        if not crushed:
            A.desk(img, GIN_X - 13, SEAT_Y - 1)
        if t < 9.25:
            r = 1.5 + 2.5 * (0.5 + 0.5 * math.sin((t - T_B2) * 2 * math.pi * 0.8))
            A.snot_bubble(img, GIN_X - 9, SEAT_Y - 11, int(round(r)))
            A.zzz(img, GIN_X + 2, SEAT_Y - 26, t)
        else:
            fx.burst(img, t, 9.25, GIN_X - 9, SEAT_Y - 11, n=6, colors=[(196, 232, 255)], speed=(20, 40),
                     gravity=40, life=0.25, seed=21)
    else:
        # KO'd flat on the tatami with a giant steaming bump
        tw = 1 if step_frame(t, 6, 2) and t < 10.2 else 0
        draw_char(img, "gintoki_kid", GIN_X + 2, SEAT_Y + 9, "lie", t, facing=-1, expr="hurt", shadow=False,
                  sheathed=False, legs="spread", dy=-tw)
        hx, hy = GIN_X + 10, SEAT_Y - 9
        A.bump(img, hx, hy - 3, 6)
        for i in range(3):
            v = ((t * 1.3 + i / 3) % 1.0)
            A.rect(img, int(hx - 2 + i * 2 + math.sin(v * 6 + i) * 1.5), int(hy - 10 - v * 12), 1, 2,
                   (250, 250, 250))
        A.dizzy_stars(img, hx - 2, hy - 4, t, r=7)
    if after:
        u = seg(t, T_HB, T_HB + 0.33)
        if u < 1:
            xl, yl = arc((GIN_X - 18, SEAT_Y - 1), (GIN_X - 40, SEAT_Y), u, 22)
            xr, yr = arc((GIN_X - 8, SEAT_Y - 1), (GIN_X + 32, SEAT_Y + 1), u, 26)
            A.desk(img, xl, yl, piece="L", rot=int(u * 200))
            A.desk(img, xr, yr, piece="R", rot=-int(u * 260))
        else:
            A.desk(img, GIN_X - 40, SEAT_Y, piece="L", rot=40)
            A.desk(img, GIN_X + 32, SEAT_Y + 1, piece="R", rot=-80)
        fx.smoke_puff(img, t, T_HB + 0.04, GIN_X - 2, SEAT_Y - 4, size=22, seed=31, color=(230, 220, 198),
                      life=0.55)
        fx.burst(img, t, T_HB, GIN_X - 4, SEAT_Y - 6, n=18, colors=[(210, 190, 120), (160, 130, 80)],
                 speed=(50, 130), gravity=260, life=0.6, seed=32)
    # Shouyou
    # Shouyou: creeps over smiling -> dark aura -> wind-up -> HEADBUTT -> straightens up, still smiling
    sp = dict(facing=1)
    if t < 8.3:
        sx_, pose = 205, "smile"
    elif t < 9.05:
        sx_, pose = lerp(205, 238, seg(t, 8.3, 9.05)), "walk"
        sp["expr"] = "smile"
    elif t < 9.25:
        sx_, pose = 238, "smile"
    elif t < 9.55:
        sx_, pose = 238, "headbutt"
        sp["p"] = lerp(0, 0.35, seg(t, 9.25, 9.55))
    elif t < T_HB:
        u = seg(t, 9.55, T_HB)
        sx_, pose = lerp(238, 250, u), "headbutt"
        sp.update(p=lerp(0.35, 0.5, u), rot=-int(40 * u))
    elif t < 9.95:
        sx_, pose = 250, "headbutt"
        sp.update(p=lerp(0.5, 0.85, seg(t, T_HB, 9.95)), rot=-40)
    elif t < 10.15:
        u = ease_out(seg(t, 9.95, 10.15))
        sx_, pose = lerp(250, 240, u), "smile"
        sp["rot"] = -int(40 * (1 - u))
    else:
        sx_, pose = 240, "smile"
    if 9.05 <= t < 9.58:
        A.dark_aura(img, "shouyou", sx_, SEAT_Y + 2, pose, t, amt=seg(t, 9.05, 9.2), sheathed=False,
                    **{k: v for k, v in sp.items() if k != "expr"})
    _sensei(img, sx_, SEAT_Y + 2, pose, t, **sp)
    if T_HB <= t < 9.95:
        fx.sparkle(img, 262, SEAT_Y - 16, t, T_HB - 0.05, 6, (255, 250, 200))
    elif t >= 10.15:
        fx.sparkle(img, 247, SEAT_Y - 26, t, 10.2, 3)
    # camera
    if t < 9.2:
        k, cx, cy = 1.8, lerp(176, 200, ease_in_out(seg(t, T_B2, 9.2))), 127
    elif t < 9.95:
        u = ease_in_out(seg(t, 9.2, 9.55))
        k, cx, cy = lerp(1.8, 2.25, u), lerp(200, 250, u), lerp(127, 132, u)
        if t >= T_HB:
            k += 0.2 * (1 - ease_out(seg(t, T_HB, T_HB + 0.3)))
    else:
        u = ease_in_out(seg(t, 9.95, 10.35))
        k, cx, cy = lerp(2.25, 1.62, u), lerp(250, 188, u), lerp(132, 129, u)
    to_s = view(img, k, cx, cy)
    if T_HB <= t < T_HB + 0.16:
        sx, sy = to_s(GIN_X - 8, SEAT_Y - 12)
        ov.append(lambda im: fx.speed_lines(im, t, int(sx), int(sy), color=(255, 250, 236), count=26,
                                            inner=70, seed=5, thickness=1))
    if T_HB <= t < T_HB + 0.067:
        ov.insert(0, lambda im: fx.impact_frame(im, color_hi=(255, 248, 232), color_lo=(40, 28, 24)))
    ov.append(lambda im: sfx_text(im, 250, 60, "咚!!", t, T_HB, 0.8, size=30, angle=6))
    ov.append(lambda im: _laughs(im, t, to_s))
    ov.append(lambda im: _shake(im, t, T_HB, 0.4, 6))
    return 0.6


def _laughs(img, t, to_s):
    if t < T_HB + 0.35:
        return
    for i, (x, y) in enumerate(((KAT_X + 2, SEAT_Y - 32), (TAKA_X + 4, SEAT_Y - 32))):
        f = step_frame(t + i * 0.2, 5)
        sx, sy = to_s(x, y)
        if not (14 <= sx <= W - 30):          # laugher is off-screen in the push-in
            continue
        draw_text(img, sx + (f % 2) * 3 - 10, sy - (f % 3) * 2, "哈哈" if f % 2 else "哈哈哈", (255, 244, 214),
                  outline=(60, 40, 30))


# ================================================================ shot C: fire
def shot_C(img, t, ov):
    A.burning_school(img, t)
    walking = t < T_C2
    u = seg(t, T_C1, T_C2)
    lx, sx, bx = lerp(238, 254, u), lerp(212, 228, u), lerp(186, 202, u)
    if walking:
        draw_char(img, "naraku", bx, 160, "walk", t, facing=1)
        draw_char(img, "shouyou", sx, 160, "walk", t, facing=1, expr="normal", arm_f=-35, arm_b=-35)
        draw_char(img, "naraku", lx, 160, "walk", t + 0.3, facing=1)
    else:
        draw_char(img, "naraku", bx, 160, "idle", t, facing=1)
        turned = t >= T_C2 + 0.22             # stops... then looks back over his shoulder
        draw_char(img, "shouyou", sx, 160, "idle", t, facing=-1 if turned else 1,
                  expr=("blink" if t < T_C2 + 0.3 else "smile") if turned else "normal", arm_f=-35, arm_b=-35)
        if turned:
            fx.sparkle(img, int(sx - 8), 132, t, T_C2 + 0.3, 4, (255, 236, 190))
        draw_char(img, "naraku", lx, 160, "idle", t, facing=1)
    A.rope_bind(img, sx, 160, kneel=False)
    d = ImageDraw.Draw(img)
    d.line([(sx + 7, 151), (lx - 5, 148)], fill=(150, 116, 74))
    # the guard and the kids
    draw_char(img, "naraku", 128, 160, "ready", t, facing=-1)
    draw_char(img, "takasugi_kid", 40, 160, "kneel", t, facing=1, expr="angry")
    draw_char(img, "katsura_kid", 62, 160, "kneel", t, facing=1, expr="cry")
    reach = 95 + 6 * math.sin(t * 7)
    draw_char(img, "gintoki_kid", 86, 160, "kneel", t, facing=1, expr="cry", arm_f=reach, sheathed=False)
    if t >= T_C3:
        for i in range(2):
            v = ((t * 1.4 + i * 0.5) % 1.0)
            A.tear_drop(img, 89 + i * 3, 147 + v * 10)
    fx.embers(img, t, count=46, seed=3, rise=34, area=(0, 20, W, 170))
    if t < T_C2:
        view(img, 1.0 + 0.04 * u, 192, 112)
    elif t < T_C3:
        view(img, lerp(2.45, 2.7, ease_out(seg(t, T_C2, T_C3))), sx - 2, 134)
    else:
        view(img, lerp(2.6, 2.85, ease_out(seg(t, T_C3, T_D1))), 84, 140)
    if t >= T_C2:
        ov.append(lambda im: fx.embers(im, t, count=18, seed=8, rise=40, area=(0, 20, W, 180),
                                       colors=((255, 214, 150), (255, 170, 90))))
    return 0.45


# ================================================================ shot D1: Joui war
ENEMIES = [(266, "harusame"), (290, "amanto_pig"), (314, "harusame"), (338, "amanto_cat")]


def shot_D1(img, t, ov):
    cam = lerp(0, 50, ease_out(seg(t, T_D1, 14.3)))
    bolt = 0.0
    if T_SLASH <= t < T_SLASH + 0.25:
        bolt = 0.7 * (1 - seg(t, T_SLASH, T_SLASH + 0.25))
    A.joui_field(img, t, cam, flash=bolt)
    SX = 196
    if t < 14.1:
        u = ease_in(seg(t, T_D1, 14.1))
        x = lerp(40, SX, u)
        fx.motion_lines(img, t, color=(236, 220, 210), count=16, direction=-1, seed=6, y0=110, y1=168,
                        speed=900, length=(20, 60))
        draw_char(img, "shiroyasha", x, 160, "run", t, facing=1)
        if step_frame(t, 10, 2) == 0:
            fx.smoke_puff(img, t, t - 0.04, x - 8, 160, size=5, seed=int(t * 10), color=(120, 100, 96))
    elif t < 14.55:
        draw_char(img, "shiroyasha", SX, 160, "attack", t, p=seg(t, 14.1, 14.55), facing=1)
    else:
        draw_char(img, "shiroyasha", SX, 160, "battle_idle", t, facing=1, expr="angry")
    for i, (wx, cid) in enumerate(ENEMIES):
        x0 = wx - cam
        t0 = T_SLASH + i * 0.03
        if t < t0:
            draw_char(img, cid, x0, 160, "ready", t + i * 0.2, facing=-1)
        else:
            dt = t - t0
            land = 0.6 + i * 0.05
            if dt < land:
                x = x0 + dt * (70 + i * 30)
                y = 160 - dt * (200 - i * 20) + 0.5 * 560 * dt * dt
                draw_char(img, cid, x, min(y, 166), "fly", t + i, facing=-1, shadow=False)
            else:
                x = x0 + land * (70 + i * 30)
                fx.smoke_puff(img, t, t0 + land, x, 168, size=8, seed=40 + i, color=(110, 96, 96))
                draw_char(img, cid, x, 176, "lie", t, facing=-1, shadow=False)
    fx.burst(img, t, T_SLASH, 236, 140, n=20, colors=[(255, 255, 255), (255, 230, 200)], speed=(60, 160),
             gravity=100, life=0.4, seed=15)
    fx.rain(img, t, count=80, seed=2, color=(176, 160, 170), speed=420, slant=0.3)
    # tracking camera: follows the dash, then frames the slash
    if t < 14.1:
        xr = lerp(40, SX, ease_in(seg(t, T_D1, 14.1)))
        k, cx = 1.55, min(236, max(130, xr + 70))
    else:
        k, cx = 1.55, 236
    if t >= T_SLASH:
        k += 0.1 * (1 - ease_out(seg(t, T_SLASH, T_SLASH + 0.4)))
    to_s = view(img, k, cx, 128)
    ox, oy = to_s(206, 150)
    ov.append(lambda im: _slash_fx(im, t, ox, oy, k))
    ov.append(lambda im: name_card(im, t, 13.72, 1.9, "gintoki", "白夜叉", "攘夷战争的传说"))
    ov.append(lambda im: _shake(im, t, T_SLASH, 0.35, 5))
    return 0.5


def _slash_fx(img, t, ox, oy, k):
    if T_SLASH - 0.04 <= t < T_SLASH + 0.3:
        p = seg(t, T_SLASH - 0.04, T_SLASH + 0.14)
        fx.slash_arc(img, ox, oy, 58 * k, -150, 30, p * 1.25, (255, 255, 255), 7)
        fx.slash_arc(img, ox, oy, 50 * k, -150, 30, p * 1.25, (255, 236, 200), 3)
    if T_SLASH <= t < T_SLASH + 0.07:
        fx.impact_frame(img, color_hi=(255, 248, 232), color_lo=(28, 20, 22))
    elif T_SLASH + 0.07 <= t < T_SLASH + 0.25:
        fx.flash(img, 0.5 * (1 - seg(t, T_SLASH + 0.07, T_SLASH + 0.25)))


# ================================================================ shot D2: the Joui four
def shot_D2(img, t, ov):
    A.ridge(img, t)
    A.banner(img, 120, 152, t, h=48, cw=11, ch=28, col=(222, 214, 196), mon=(170, 50, 50), lean=-2, seed=1)
    A.banner(img, 290, 152, t, h=42, cw=10, ch=24, col=(150, 60, 56), mon=(220, 200, 150), lean=3, seed=2.5)
    lit = ease_in_out(seg(t, 15.95, 16.55))
    fl = lerp(0.9, 0.18, lit)
    dark = (38, 22, 34)
    draw_char(img, "katsura", 152, 150, "arms_crossed", t, facing=1, flash=fl, flash_color=dark)
    draw_char(img, "shiroyasha", 186, 150, "shoulder", t, facing=1, flash=fl, flash_color=dark)
    A.draw_takasugi_young(img, 220, 150, "idle", t, facing=1, flash=fl, flash_color=dark)
    draw_char(img, "sakamoto", 255, 150, "laugh", t, facing=1, flash=fl, flash_color=dark, ha=lit > 0.5)
    for i in range(3):
        A.crow_fly(img, 150 + (t - T_D2) * 30 + i * 12, 92 + i * 5 - (t - T_D2) * 6, t, 1, i * 0.3)
    k = lerp(1.45, 1.62, ease_out(seg(t, T_D2, T_E1)))
    view(img, k, 204, 125)
    ov.append(lambda im: name_card(im, t, 15.72, 1.85, "sakamoto", "坂本辰马", "快援队｜啊哈哈哈"))
    return 0.55


# ================================================================ shot E: the cliff
SHO_X, GIN_E_X, KAT_E_X, TAK_E_X, OBO_X = 74, 114, 248, 276, 306


def _cliff_world(img, t, gin_pose="battle_idle", gin_p=None, gin_expr="sad", sho_facing=-1, sho_expr="normal",
                 taka_expr="angry", kat_expr="sad", gin_dx=0, gin_kw=None, gin_under=None):
    A.cliff(img, t)
    tree = (196, 152)
    A.dead_tree(img, tree[0], tree[1], 0.9)
    perch = [(tree[0] - 22, tree[1] - 58), (tree[0] + 18, tree[1] - 64), (tree[0] + 4, tree[1] - 76)]
    for i, (px, py) in enumerate(perch):
        t0 = 17.95 + i * 0.12
        if t < t0:
            A.crow_sit(img, px, py, -1 if i % 2 else 1, t, seed=i)
        else:
            dt = t - t0
            A.crow_fly(img, px - dt * 60 - i * 4, py - dt * 40 + math.sin(dt * 6 + i) * 3, t, -1, i * 0.2)
    haze = (170, 166, 170)
    for i, x in enumerate((328, 350, 372)):
        draw_char(img, "naraku", x, 150, "stand_guard", t + i * 0.4, facing=-1, flash=0.38, flash_color=haze)
    draw_char(img, "oboro", OBO_X, 160, "ready", t, facing=-1, expr="normal", weapon=-38, arm_f=58)
    draw_char(img, "katsura", KAT_E_X, 160, "kneel", t, facing=-1, expr=kat_expr, arm_f=-25, arm_b=-25)
    A.rope_bind(img, KAT_E_X, 160)
    A.draw_takasugi_young(img, TAK_E_X, 160, "kneel", t, facing=-1, expr=taka_expr, arm_f=-25, arm_b=-25)
    A.rope_bind(img, TAK_E_X, 160)
    # sensei kneels at the edge, hands bound behind his back, his sword taken
    draw_char(img, "shouyou", SHO_X, 160, "kneel", t, facing=sho_facing, expr=sho_expr, hide_arm_f=True,
              arm_b=-22, sheathed=False)
    A.rope_bind(img, SHO_X, 160)
    if gin_under:
        gin_under(img)
    draw_char(img, "shiroyasha", GIN_E_X + gin_dx, 160, gin_pose, t, p=gin_p, facing=-1, expr=gin_expr,
              **(gin_kw or {}))


def overhead_sword(img, x, y, facing, r, fall=0.0, glint=-1.0):
    """Chibi 'sword raised overhead': the arms rise from BEHIND the big head so the
    face stays visible; the gauntlets + katana show above the hair.
    r 0..1: the grip rises from behind the shoulder (hasso) to straight overhead.
    fall 0..1: the blade swings forward and down. glint 0..1: light running up the blade.
    Angles are in facing space: 90 = up, 0 = forward, 180 = backward."""
    back = -facing
    if fall <= 0:
        ru = ease_out(r)
        gx, gy = x + back * lerp(8, 1, ru), y - lerp(22, 46, ru)
        a_f = lerp(112, 96, ru)
    else:
        fu = ease_in(fall)
        gx, gy = x + back * lerp(1, -12, fu), y - lerp(46, 22, fu)
        a_f = lerp(96, -35, fu)
    a = math.radians(a_f)
    vx, vy = math.cos(a) * facing, -math.sin(a)
    L = 21
    tip = (gx + vx * L, gy + vy * L)
    pommel = (gx - vx * 6, gy - vy * 6)
    # arms: white sleeves rising from behind the head to the grip
    for sx in (-6, 6):
        A.stamp_line(img, (x + sx, y - 25), (gx - vx * 2.5, gy - vy * 2.5), 5, INK)
    for sx in (-6, 6):
        A.stamp_line(img, (x + sx, y - 25), (gx - vx * 2.5, gy - vy * 2.5), 3, (236, 238, 248))
        A.stamp_line(img, (x + sx + 1, y - 25), (gx - vx * 2.5 + 1, gy - vy * 2.5), 1, (196, 204, 226))
    # katana
    A.stamp_line(img, pommel, tip, 4, INK)
    A.stamp_line(img, (gx + vx * 2, gy + vy * 2), tip, 2, (214, 224, 238))
    A.stamp_line(img, (gx + vx * 3, gy + vy * 3), tip, 1, (255, 255, 255))
    A.stamp_line(img, pommel, (gx + vx, gy + vy), 2, (48, 40, 60))
    tx_, ty_ = gx + vx * 2, gy + vy * 2
    A.stamp_line(img, (tx_ + vy * 2.5, ty_ - vx * 2.5), (tx_ - vy * 2.5, ty_ + vx * 2.5), 2, (230, 180, 60))
    for k in (-1.0, -4.0):                            # two steel gauntlets on the grip
        px, py = gx + vx * k, gy + vy * k
        A.rect(img, int(px) - 2, int(py) - 2, 5, 5, INK)
        A.rect(img, int(px) - 1, int(py) - 1, 3, 3, (160, 168, 194))
        A.rect(img, int(px) - 1, int(py) - 1, 1, 1, (220, 226, 240))
    if 0 <= glint <= 1:                               # a cold glint slides up the blade
        g = lerp(3, L, glint)
        px, py = gx + vx * g, gy + vy * g
        A.rect(img, int(px) - 1, int(py), 3, 1, (255, 255, 255))
        A.rect(img, int(px), int(py) - 1, 1, 3, (255, 255, 255))
    if fall > 0.15:
        fx.slash_arc(img, gx, gy, L - 2, 90, 210 if facing < 0 else -30, fall * 1.2, (255, 255, 255), 3)
    return tip


def _gin_tears(img, t, x):
    for i in range(3):
        v = ((t * 1.7 + i / 3) % 1.0)
        A.tear_drop(img, x - 4 - i, 142 + v * 14)


def shot_E(img, t, ov):
    if t < T_E2:
        _cliff_world(img, t)
        u = ease_in_out(seg(t, T_E1, T_E2))
        view(img, lerp(1.0, 1.22, u), lerp(196, 168, u), lerp(112, 122, u))
        ov.append(lambda im: fx.fade(im, 1 - seg(t, T_E1, T_E1 + 0.35)))
        return 0.78
    if t < T_E3:
        turned = t >= T_TURN
        _cliff_world(img, t, sho_facing=1 if turned else -1, sho_expr="cry" if turned else "normal",
                     gin_expr="shock" if T_TURN <= t < T_TURN + 0.5 else "sad")
        A.light_motes(img, t, (20, 100, 140, 170), n=24, seed=8)
        if turned:
            fx.sparkle(img, SHO_X + 9, 136, t, T_TURN + 0.1, 4, (255, 246, 214))
        view(img, lerp(3.05, 3.25, ease_out(seg(t, T_E2, T_E3))), SHO_X + 6, 141)
        return 0.78
    if t < T_E3B or t >= T_E3C:
        # the sword rises from behind his head to overhead, trembling; at T_FALL it comes down
        if t < T_E3B:
            r = seg(t, T_E3, T_E3 + 0.4)
            dx = tremble(t, 1, 12) if t > T_E3 + 0.45 else 0
        elif t < T_FALL:
            r = 1.0
            dx = tremble(t, 1, 20)
        else:
            r, dx = 1.0, 0
        fall = seg(t, T_FALL, T_WHITE) if t >= T_FALL else 0.0
        glint = seg(t, T_E3 + 0.4, T_E3 + 0.55) if t < T_E3B else -1.0
        kw = dict(hide_arm_f=True, hide_arm_b=True, sheathed=False, weapon=None)
        behind = fall < 0.3
        under = (lambda im: overhead_sword(im, GIN_E_X + dx, 160, -1, r, fall, glint)) if behind else None
        _cliff_world(img, t, gin_pose="idle", gin_expr="cry", sho_facing=1, sho_expr="cry", gin_dx=dx,
                     gin_kw=kw, gin_under=under)
        if not behind:
            overhead_sword(img, GIN_E_X + dx, 160, -1, r, fall)
        _gin_tears(img, t, GIN_E_X + dx)
        if T_E3 + 0.4 <= t < T_E3 + 0.75:
            fx.sparkle(img, GIN_E_X + dx - 1, 160 - 66, t, T_E3 + 0.45, 5)
        k = 2.9 + (0.25 * seg(t, T_E3C, T_WHITE) if t >= T_E3C else 0.12 * seg(t, T_E3, T_E3B))
        view(img, k, GIN_E_X - 6, 126)
        if t >= T_FALL:
            ov.append(lambda im: fx.flash(im, seg(t, T_FALL, T_WHITE) ** 0.7 * 0.95))
        return 0.78
    # E3b: Takasugi screams
    _cliff_world(img, t, gin_pose="idle", gin_expr="cry", sho_facing=1, sho_expr="cry",
                 taka_expr="shout", kat_expr="shock",
                 gin_kw=dict(hide_arm_f=True, hide_arm_b=True, sheathed=False, weapon=None))
    k = lerp(3.0, 3.35, ease_out(seg(t, T_E3B, T_E3C)))
    to_s = view(img, k, TAK_E_X - 4, 144)
    sx, sy = to_s(TAK_E_X, 140)
    ov.append(lambda im: fx.speed_lines(im, t, int(sx), int(sy), color=(40, 30, 36), count=46, inner=78,
                                        seed=9 + step_frame(t, 15)))
    ov.append(lambda im: _shake(im, t, T_E3B, 0.4, 3))
    return 0.78


# ================================================================ white + tear
_AFTER = {}


def _after_image():
    """The last thing he saw (sensei's smile with tears) burned into the white:
    a deterministic render of the E2 close-up, cached."""
    a = _AFTER.get("a")
    if a is None:
        im = Image.new("RGB", (W, H))
        t0 = 20.6
        _cliff_world(im, t0, sho_facing=1, sho_expr="cry")
        view(im, 3.2, SHO_X + 6, 141)
        flashback_grade(im, t0, 0.78)
        a = np.asarray(im).astype(np.float32)
        _AFTER["a"] = a
    return a


_GHOST_INK = np.array([0.62, 0.5, 0.42], np.float32)          # sepia tone of the ghost's lines


def shot_white(img, t, ov):
    k = ease_in_out(seg(t, 23.2, 24.2))
    col = np.array([lerp(255, c, k) for c in (244, 238, 226)], np.float32)
    ga = 0.55 * ease_in_out(seg(t, 22.62, 23.15)) * (1 - ease_in_out(seg(t, 23.3, 23.95)))
    base = np.empty((H, W, 3), np.float32)
    base[...] = col
    if ga > 0.01:
        aft = _after_image()
        drift = int(round((t - 22.6) * 3))            # slow drift upward
        aft = np.roll(aft, -drift, axis=0)
        # multiply-blend: the white stays white, the figures' lines ghost through
        lum = aft @ _LUM
        m = np.clip((lum - 60.0) / 110.0, 0, 1)[..., None]          # sky -> 1 (white), lines -> 0
        mul = _GHOST_INK + (1 - _GHOST_INK) * m
        base = base * (1 - ga + ga * mul)
    img.paste(Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB"))
    colt = tuple(int(c) for c in col)
    TX = 192
    if 23.3 <= t < T_TEAR:
        dt = max(0.0, t - 23.5)
        y = 34 + 0.5 * 760 * dt * dt
        if t < 23.5:       # the drop gathers
            s = seg(t, 23.3, 23.5)
            A.big_tear(img, TX, 34, 2 if s < 0.5 else 3)
        else:
            A.big_tear(img, TX, min(y, 150), 3)
    elif t >= T_TEAR:
        dt = t - T_TEAR
        d = ImageDraw.Draw(img)
        for j in range(3):
            rr = (dt - j * 0.14) * 80
            if rr > 1:
                a = clamp(1 - rr / 90)
                c = tuple(int(lerp(bg, cc, a)) for bg, cc in zip(colt, (120, 172, 226)))
                d.ellipse([TX - rr, 150 - rr * 0.2, TX + rr, 150 + rr * 0.2], outline=c)
        fx.burst(img, t, T_TEAR, TX, 149, n=8, colors=[(120, 172, 226), (170, 210, 245)], speed=(30, 60),
                 gravity=200, life=0.4, spread=(200, 340), size=(1, 2), seed=50)
    return 0.0


# ================================================================ shot F: present
GIN_F, OBO_F = 196, 238            # s10's blade-lock positions (contact ~ (216, 143))


def shot_F(img, t, ov):
    A.present(img, t)
    A.dead_tree(img, 70, 158, 1.0)
    A.crow_sit(img, 50, 98, 1, t, seed=3)
    for i in range(3):
        A.crow_fly(img, 330 - (t - T_F) * 26 + i * 16, 58 + i * 7, t, -1, i * 0.3)
    # back in s10's blade-lock: bokuto vs katana, grinding; Gintoki's eyes lost in shadow
    j = 1 if step_frame(t, 12) % 2 else 0
    draw_char(img, "oboro", OBO_F + j, 160, "ready", t, facing=-1, expr="normal", arm_f=86, weapon=8,
              legs="lunge", lean=3, arm_b=40, bob=0)
    A.draw_shadowed(img, "gintoki", GIN_F - j, 160, "ready", t, facing=1, rows=(56, 63), soft=3, k=0.24,
                    arm_f=86, weapon=16, legs="lunge", lean=3, arm_b=40, bob=0, expr="angry")
    cx_, cy_ = 216, 143
    kk = int((t - T_F) * 8)
    fx.burst(img, t, T_F + kk / 8.0 + 0.001, cx_, cy_, n=5, colors=[(255, 250, 200), (255, 190, 80)],
             speed=(30, 80), gravity=180, life=0.3, seed=80 + kk)
    if int(t * 20) % 2:
        A.rect(img, cx_ - 1, cy_ - 1, 3, 3, (255, 255, 230))
    fx.embers(img, t, count=22, seed=12, rise=12, area=(110, 70, 300, 170),
              colors=((255, 200, 140), (255, 170, 110), (255, 230, 190)))
    k = lerp(3.2, 2.75, ease_in_out(seg(t, T_F, DUR)))
    view(img, k, lerp(200, 208, seg(t, T_F, DUR)), 137)
    ov.append(lambda im: fx.flash(im, 1 - seg(t, T_F, T_F + 0.3)))
    return 0.0


# ================================================================ scene
class ShouyouScene(Scene):
    id = "s11"
    title = "松阳老师"
    duration = DUR
    music = [(0.0, "flashback"), (T_E1, "sad"), (T_WHITE, None)]
    music_vol = 0.6
    fade_in = 0.0            # s10 ends on a held white frame; we fade in from white ourselves
    fade_out = 0.6
    subs = [
        (2.25, 5.45, "shouyou", "这把剑，是用来斩断你心中的弱小，守护你自己的灵魂的。"),
        (5.68, 7.80, "takasugi_kid", "银时！今天一定要赢你！"),
        (8.00, 9.98, "shouyou", "上课睡觉可不行哦～"),
        (11.60, 13.62, "shouyou", "银时，大家就拜托你了。"),
        (19.45, 21.12, "shouyou", "谢谢你。"),
        (21.45, 23.13, A.TAKASUGI_YOUNG_SPK, "住手——！！"),
    ]

    def render(self, img, t):
        ov = []
        if t < T_B1:
            sep = shot_A(img, t, ov)
        elif t < T_B2:
            sep = shot_B1(img, t, ov)
        elif t < T_C1:
            sep = shot_B2(img, t, ov)
        elif t < T_D1:
            sep = shot_C(img, t, ov)
        elif t < T_D2:
            sep = shot_D1(img, t, ov)
        elif t < T_E1:
            sep = shot_D2(img, t, ov)
        elif t < T_WHITE:
            sep = shot_E(img, t, ov)
        elif t < T_F:
            sep = shot_white(img, t, ov)
        else:
            sep = shot_F(img, t, ov)
        if sep > 0:
            flashback_grade(img, t, sep)
        for f in ov:
            f(img)
        if T_E1 <= t < T_WHITE or t >= T_F:
            fx.letterbox(img, 1.0, 20)
        if t < 0.9:                          # out of s10's white
            fx.flash(img, 1 - ease_in_out(seg(t, 0.0, 0.9)))
        for tc in CUTS:                      # memory-flash cuts
            if tc <= t < tc + 0.2:
                fx.flash(img, 0.85 * (1 - seg(t, tc, tc + 0.2)))

    def cues(self):
        return [
            # A battlefield
            Cue(0.0, "wind", vol=0.45, dur=5.6),
            Cue(0.45, "crow", vol=0.45),
            Cue(1.25, "crow", vol=0.35, pitch=1.12),
            Cue(0.35, "footsteps", vol=0.3, dur=1.55),
            Cue(1.95, "whoosh", vol=0.4),
            Cue(0.9, "eat", vol=0.22, dur=0.95),
            Cue(1.96, "shock", vol=0.55),
            Cue(T_JUMP, "jump", vol=0.6),
            Cue(T_JUMP + 0.3, "pop", vol=0.25),
            Cue(T_LANDK, "land", vol=0.6),
            Cue(T_LANDK + 0.03, "shing", vol=0.6),
            Cue(3.95, "shine", vol=0.5),
            Cue(4.72, "clang", vol=0.55),
            Cue(T_GIVE, "whoosh", vol=0.25),
            Cue(T_HUG, "sparkle", vol=0.4),
            # B1 yard
            Cue(T_B1, "whoosh", vol=0.35),
            Cue(6.20, "dash", vol=0.6),
            Cue(6.72, "jump", vol=0.5),
            Cue(6.80, "whoosh", vol=0.6),
            Cue(T_BONK, "punch", vol=0.9),
            Cue(T_BONK, "hit", vol=0.5),
            Cue(7.25, "sweat", vol=0.45),
            Cue(7.40, "thud", vol=0.6),
            Cue(7.45, "dizzy", vol=0.55),
            # B2 classroom
            Cue(T_B2, "whoosh", vol=0.3),
            Cue(8.05, "footsteps", vol=0.28, dur=1.0),
            Cue(9.25, "pop", vol=0.55),
            Cue(9.05, "aura", vol=0.45),
            Cue(9.50, "whoosh", vol=0.7),
            Cue(T_HB, "punch_big", vol=1.0),
            Cue(T_HB, "impact", vol=0.7),
            Cue(T_HB + 0.02, "crash", vol=0.55),
            Cue(T_HB + 0.12, "boing", vol=0.55),
            Cue(T_HB + 0.33, "thud", vol=0.5),
            Cue(9.95, "sting_comedy", vol=0.55),
            Cue(10.2, "sparkle", vol=0.3),
            # C fire
            Cue(T_C1, "fire", vol=0.6, dur=3.0),
            Cue(T_C1, "sting_dramatic", vol=0.45),
            Cue(T_C1, "footsteps", vol=0.25, dur=0.8),
            Cue(T_C2 + 0.22, "sparkle", vol=0.25),
            Cue(12.55, "heartbeat", vol=0.4),
            # D1 Joui war
            Cue(T_D1, "rain", vol=0.4, dur=2.0),
            Cue(T_D1, "battle", vol=0.5, dur=2.0),
            Cue(T_D1 + 0.02, "thunder", vol=0.45),
            Cue(13.72, "whoosh", vol=0.35),
            Cue(13.75, "dash", vol=0.7),
            Cue(T_SLASH - 0.03, "slash_big", vol=0.9),
            Cue(T_SLASH, "impact", vol=0.7),
            Cue(T_SLASH + 0.02, "thunder", vol=0.5),
            Cue(T_SLASH + 0.05, "hit", vol=0.5),
            Cue(T_SLASH + 0.12, "hit", vol=0.45, pitch=0.85),
            Cue(T_SLASH + 0.63, "thud", vol=0.5),
            Cue(T_SLASH + 0.78, "thud", vol=0.45, pitch=0.9),
            # D2 ridge
            Cue(T_D2, "wind", vol=0.4, dur=1.95),
            Cue(15.72, "whoosh", vol=0.35),
            Cue(16.0, "shine", vol=0.45),
            # E cliff
            Cue(T_E1, "wind", vol=0.5, dur=4.9),
            Cue(17.95, "crow", vol=0.5),
            Cue(18.15, "crow", vol=0.4, pitch=0.9),
            Cue(T_TURN, "sparkle", vol=0.3),
            Cue(T_E3, "shing", vol=0.5),
            Cue(T_E3 + 0.05, "heartbeat", vol=0.7),
            Cue(T_E3 + 0.45, "shine", vol=0.45),
            Cue(T_E3B, "heartbeat", vol=0.75),
            Cue(T_E3C, "heartbeat", vol=0.8),
            Cue(T_FALL, "whoosh", vol=0.6),
            Cue(T_WHITE - 0.02, "slash_big", vol=0.7),
            # white + tear, present
            Cue(T_TEAR, "bell", vol=0.5),
            Cue(T_F, "wind", vol=0.5, dur=1.65),
            Cue(T_F + 0.05, "clang", vol=0.35, pitch=0.8),
            Cue(24.7, "crow", vol=0.3),
        ]


SCENE = ShouyouScene()
