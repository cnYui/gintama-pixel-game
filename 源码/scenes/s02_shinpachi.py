"""s02 新八登场 — family restaurant -> parfait tragedy -> Shimura dojo -> Shinpachi joins.

SHOT LIST (scene-local seconds, duration 21.9)
  A  0.00- 3.90  Family restaurant: wide establishing -> push-in (zoom 1.06->1.78) as
                 Shinpachi (waiter, tray) walks out of the kitchen swing door to the
                 pigs at the counter. 1.45 pig B stomps (咚, vein, shake):
                 「地球猴子！上菜慢死了！」 Shinpachi sweats. Gintoki at the counter
                 blissfully eats a chocolate parfait (hearts), ignoring everything.
  B  3.90- 5.50  CLOSE-UP (zoom 2.6): Gintoki in parfait heaven. Pig B turns to mock him,
                 4.30 raises his fist -> 4.58 SLAMS the counter (咚) -> the parfait hops
                 and hangs in SLOW MOTION (Gintoki: "！", hand reaching) -> 5.15 SPLAT
                 (啪嚓, glass + record scratch, music cuts to silence).
  C  5.50- 6.70  SILENCE tableau, slow push-in: everyone frozen; a crow glides across the
                 window 「阿～」…「呆～」 (synced to the two caws); "..." over Gintoki.
  D  6.70- 7.70  EYES: letterboxed extreme close-up, dead-fish eyes -> 7.12 sharp (shing).
  E  7.70- 9.30  THE HIT. close: Gintoki leaps off the stool, bokuto crescent 7.95 ->
                 impact frame + speed lines + 砰!!; 8.12 wide: pig B rockets into the back
                 wall 8.35 (pig-shaped hole, debris, 轰!, music back); pig A flees in the
                 foreground 「噫——！」; 8.80 the pig twinkles as a star through the hole.
  F  9.30-11.40  Manager (chef hat) SLAMS the kitchen door open (砰!), points:
                 「新八！你被开除了！」 -> 10.35 SNAP ZOOM: tray drops (哐啷), Shinpachi
                 turns to stone (gloom lines, 咔嚓).
  G 11.40-13.90  name_card 志村新八 over stone-Shinpachi while Gintoki strolls off
                 nose-picking; 12.00 TSUKKOMI close-up (speed lines, 喂!!)
                 「你给我等一下！！」 -> 12.70 two-shot: Gintoki 「？」, flicks a booger
                 13.12 that sticks on Shinpachi's glasses 13.38 (啪, vein). 13.75 wipe.
  H0 13.90-14.70 Dusk exterior: Shimura dojo gate (signboard 志村道场, lantern, sakura).
  H 14.70-17.80  Dojo interior. name_card 志村妙 14.80; 15.00 dark aura + egg 「请用～」;
                 15.80 INSERT: the charred 'fried egg' (bubbles, miasma, skull,
                 「※本品为煎蛋」); 16.36 push-in on sweating Gintoki; 16.70 he eats it
                 (嘎嘣) -> purple flash -> 17.15 falls backwards, legs up (咚!), soul leaves.
  I 17.80-21.90  Shinpachi springs up (light rays), glasses glint 18.05, points at the
                 fainted 「这个人」 18.30, raises his bokuto to the sky 18.95:
                 「我要跟着这个人，找回我的武士道！」; 20.15 music drops, JRPG box
                 「志村新八 加入了万事屋！」 + fanfare, camera pulls back.
Characters: shinpachi (waiter / waiter_walk / point / shock / idle, torso='apron'),
gintoki (sit + spoon prop, attack, jump, shoulder, walk+nosepick, eat), amanto_pig x2
(sit/laugh/bully/shock/fly), townsman v2 as the manager (+ chef hat), otae
(idle / offer_egg with dark_smile aura), passers-by (townsman/townswoman/amanto_cat).
"""
import math

from PIL import Image, ImageDraw

from engine.core import (Scene, Cue, W, H, seg, lerp, clamp, ease_in, ease_out, ease_in_out,
                         ease_out_back, wave, step_frame, rng, arc, quant)
from engine.gfx import (INK, paste, rect, overlay_rect, stamp_line, pset, set_alpha, rotate_nearest,
                        tint, scale_nearest)
from engine import fx
from engine.text import draw_text, text_width, text_sprite, sfx_text, name_card
from chars import draw_char, render_sprite, portrait
from bg import common as C
from scenes import _s02_art as A

# ------------------------------------------------------------------ timing
TA, TB, TC, TD, TE, TF, TG = 0.0, 3.90, 5.50, 6.70, 7.70, 9.30, 11.40
TH, TH2, TI, TEND = 13.90, 14.70, 17.80, 21.90
STOMP = 1.45
SWING = 4.30
KNOCK = 4.58
SPLAT = 5.15
EYES_SNAP = 7.12
LEAP = 7.70
HIT = 7.95
CRASH = 8.35
DOOR_BANG = 9.30
TRAY_DROP = 10.35
TSUKKOMI = 12.00
WIPE0, WIPE1 = 13.75, 14.05
OTAE_CARD = 14.80
AURA = 15.00
EGG_PUSH = 15.80
EGG_INS_END = 16.36
CHOMP = 16.70
PURPLE = 17.00
FALL0, FALL1 = 17.15, 17.35
GLINT = 18.05
JOIN = 20.15

SHIN_X = 192
PIGA_X, PIGB_X, GIN_X = A.STOOLS[0], 270, A.STOOLS[1]
FLOOR = A.FLOOR_Y
SPLAT_POS = (291, 167)


# ------------------------------------------------------------------ helpers
class Cam:
    """Uniform zoom about a centre (clamped so the view stays inside the canvas)."""

    def __init__(self, k=1.0, cx=W / 2, cy=H / 2):
        self.k = max(1.0, k)
        hw, hh = W / (2 * self.k), H / (2 * self.k)
        self.cx, self.cy = clamp(cx, hw, W - hw), clamp(cy, hh, H - hh)
        self.x0, self.y0 = self.cx - hw, self.cy - hh

    def apply(self, img):
        fx.zoom(img, self.k, self.cx, self.cy)

    def pt(self, x, y):
        return int(round((x - self.x0) * self.k)), int(round((y - self.y0) * self.k))


def _spr_at(img, key, x, y, anchor="bottom", alpha=1.0):
    paste(img, A.spr(key), x, y, anchor=anchor, alpha=alpha)


def _sweat(img, x, y, t, t0, period=0.9):
    """Sweat drop that slides down and re-appears."""
    if t < t0:
        return
    ph = ((t - t0) % period) / period
    _spr_at(img, "sweat", x, y + int(ph * 5), anchor="center", alpha=1 - ph * 0.6)


def _vein(img, x, y, t, t0):
    if t < t0:
        return
    k = ease_out_back(clamp((t - t0) / 0.15))
    s = A.spr("vein")
    pulse = 1 if step_frame(t, 6, 2) else 0
    if k < 1:
        s = s.resize((max(1, int(s.width * k)), max(1, int(s.height * k))), Image.NEAREST)
    paste(img, s, x, y - pulse, anchor="center")


def _hearts(img, x, y, t):
    for i in range(3):
        ph = (t * 0.9 + i / 3) % 1.0
        hx = x + i * 5 - 5 + wave(t, 1.3, 2, i * 0.3)
        hy = y - ph * 16
        _spr_at(img, "heart", int(hx), int(hy), anchor="center", alpha=1 - ph ** 2)


def _spoon_prop(img, ctx):
    h = ctx["hand_f"]
    if not h:
        return
    x, y = h
    stamp_line(img, (x - 1, y + 1), (x + 4, y - 3), 1, (214, 222, 236))
    pset(img, int(x + 4), int(y - 4), (250, 252, 255, 255))
    pset(img, int(x + 5), int(y - 4), (180, 190, 210, 255))


def _egg_hand_prop(img, ctx):
    h = ctx["hand_f"]
    if not h:
        return
    e = A.spr("egg")
    img.alpha_composite(e, (int(h[0]) - 2, int(h[1]) - 4))


def _head_top(spr):
    """(x_centre, y_top) of the topmost opaque rows of a sprite."""
    a = spr.getchannel("A")
    bb = a.getbbox()
    if not bb:
        return spr.width // 2, 0
    row = a.crop((0, bb[1], spr.width, bb[1] + 3)).getbbox()
    return (row[0] + row[2]) // 2, bb[1]


def _manager(img, x, y, pose, t, p=None, facing=1, expr=None):
    spr, ax, ay = render_sprite("townsman", pose, t, p=p, expr=expr, facing=facing, variant=2)
    px, py = int(round(x - ax)), int(round(y - ay))
    from engine.gfx import overlay_rect as _ov
    _ov(img, int(x) - 6, int(y) - 1, 12, 2, (0, 0, 0), 0.25)
    img.paste(spr, (px, py), spr)
    hx, hy = _head_top(spr)
    _spr_at(img, "hat", px + hx, py + hy + 3, anchor="bottom")
    return px + hx, py + hy


def _stone_cracks(img, x, y):
    d = ImageDraw.Draw(img)
    d.line([(x - 3, y - 31), (x - 1, y - 27), (x - 4, y - 23), (x - 2, y - 19)], fill=(60, 60, 70))
    d.line([(x + 4, y - 29), (x + 2, y - 25), (x + 5, y - 22)], fill=(60, 60, 70))
    d.line([(x - 1, y - 12), (x + 2, y - 9), (x, y - 5)], fill=(60, 60, 70))


def _party_box(img, t, t0):
    """JRPG 'joined the party' system message."""
    if t < t0:
        return
    k = ease_out_back(clamp((t - t0) / 0.25))
    bw, bh = 236, 34
    x0 = W // 2 - bw // 2
    y0 = 172 + int((1 - k) * 30)
    overlay_rect(img, x0, y0, bw, bh, (12, 16, 48), 0.9)
    d = ImageDraw.Draw(img)
    d.rectangle([x0, y0, x0 + bw - 1, y0 + bh - 1], outline=(255, 255, 255))
    d.rectangle([x0 + 2, y0 + 2, x0 + bw - 3, y0 + bh - 3], outline=(90, 110, 200))
    por = portrait("shinpachi", "happy", t - t0)
    if por is not None:
        paste(img, por, x0 + 6, y0 + bh - 4 - por.height)
    tx = x0 + 50
    draw_text(img, tx, y0 + 5, "志村新八", (255, 226, 110), outline=INK)
    draw_text(img, tx + text_width("志村新八") + 4, y0 + 5, "加入了万事屋！", (255, 255, 255), outline=INK)
    draw_text(img, tx, y0 + 19, "吐槽 +99   眼镜 +1", (150, 220, 255), outline=INK)
    if int(t * 3) % 2 == 0:
        cx = x0 + bw - 12
        d.polygon([(cx, y0 + bh - 9), (cx + 5, y0 + bh - 9), (cx + 2, y0 + bh - 6)], fill=(255, 255, 255))
    # stars popping around the box
    for i in range(6):
        r = rng("party", i)
        sx = x0 + int(r.uniform(-10, bw + 10))
        sy = y0 + int(r.uniform(-12, 4))
        fx.sparkle(img, sx, sy, t, t0 + 0.05 + i * 0.12, size=3, color=(255, 240, 150))


# ------------------------------------------------------------------ restaurant world
def _window_life(img, t, crow=None):
    """Passers-by + optional crow outside the window (clipped to the glass)."""
    x0, y0, x1, y1 = A.WIN
    win = img.crop((x0, y0, x1, y1))
    walkers = (("townsman", 0, 1, 20, 10), ("townswoman", 1, -1, 17, 90), ("amanto_cat", None, 1, 24, 170),
               ("townswoman", 3, 1, 14, 230), ("townsman", 3, -1, 22, 60))
    span = (x1 - x0) + 60
    for i, (cid, var, dirn, spd, off) in enumerate(walkers):
        wx = (off + t * spd) % span - 30
        if dirn < 0:
            wx = (x1 - x0) - wx
        kw = {"variant": var} if var is not None else {}
        draw_char(win, cid, wx, 86 + (i % 2) * 3, "walk", t + i * 0.37, facing=dirn, shadow=False, **kw)
    if crow is not None:
        # the crow flies across the street BEHIND the glass (clipped to the window)
        cx, cy, key, flip = crow
        s = scale_nearest(A.spr(key), 2)
        if flip:
            s = s.transpose(Image.FLIP_LEFT_RIGHT)
        paste(win, s, int(cx) - x0, int(cy) - y0, anchor="bottom")
    img.paste(win, (x0, y0))
    ov = A.window_overlay()
    img.paste(ov, (0, 0), ov)


def rest_world(img, t, door=0.0, hole=False, crow=None, freeze=None):
    """Draw the restaurant set (background + ambient life). freeze: time to use for
    ambient animation (frozen tableau)."""
    ta = t if freeze is None else freeze
    img.paste(A.rest_bg())
    _window_life(img, ta, crow)
    A.draw_clock_hands(img, t)
    A.draw_lamps(img, ta)
    A.draw_door(img, ta, door)
    if hole:
        A.draw_hole(img, t, CRASH)


def _parfait_on_counter(img, t):
    if t < KNOCK:
        paste(img, A.spr("parfait"), A.PARFAIT_POS[0], A.PARFAIT_POS[1] + 1, anchor="bottom")


def _parfait_u(k):
    """Time-warp for the parfait's fall: quick hop, SLOW-MOTION float at the apex
    (the tragic moment), then a fast drop."""
    if k < 0.2:
        return 0.3 * ease_out(k / 0.2)
    if k < 0.74:
        return 0.3 + 0.12 * (k - 0.2) / 0.54
    return 0.42 + 0.58 * ease_in((k - 0.74) / 0.26)


def _parfait_flight(img, t):
    if not (KNOCK <= t < SPLAT):
        return
    k = seg(t, KNOCK, SPLAT)
    u = _parfait_u(k)
    x, y = arc((A.PARFAIT_POS[0], A.PARFAIT_POS[1] - 9), (SPLAT_POS[0], SPLAT_POS[1] - 6), u, 22)
    s = rotate_nearest(A.spr("parfait"), -int(u * 14) * 20)
    # slow-mo: cream / cherry-syrup flecks hanging in the air around it
    if 0.18 < k < 0.8:
        for i in range(5):
            r = rng("fleck", i)
            fx_ = x + r.uniform(-9, 9) + (k - 0.2) * r.uniform(-6, 6)
            fy_ = y + r.uniform(-10, 4) - (k - 0.2) * r.uniform(2, 6)
            pset(img, int(fx_), int(fy_), (255, 248, 236) if i % 3 else (214, 40, 56))
    paste(img, s, int(x), int(y), anchor="center")


def _splat(img, t):
    if t < SPLAT:
        return
    d = ImageDraw.Draw(img)
    x, y = SPLAT_POS
    grow = ease_out(seg(t, SPLAT, SPLAT + 0.12))
    rx, ry = 9 * grow + 1, 3 * grow + 1
    d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=(104, 58, 40), outline=INK)
    d.ellipse([x - rx * 0.6, y - ry * 0.8, x + rx * 0.3, y + ry * 0.3], fill=(255, 248, 236))
    d.ellipse([x + 2, y - 2, x + 6, y + 1], fill=(150, 92, 62))
    # glass shards
    for i, (sx, sy) in enumerate(((-11, 1), (-6, -3), (7, -3), (11, 2), (2, 3))):
        d.line([(x + sx, y + sy), (x + sx + (1 if i % 2 else -1), y + sy - 1)], fill=(190, 222, 246))
    # the cherry rolls away and stops
    rk = ease_out(seg(t, SPLAT, SPLAT + 1.1))
    cx = x + 6 + rk * 22
    cy = y + 1 - abs(math.sin(rk * math.pi * 2)) * 3 * (1 - rk)
    d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(214, 40, 56), outline=INK)
    pset(img, int(cx - 1), int(cy - 1), (255, 150, 150))
    ang = rk * 9
    d.line([(cx, cy - 2), (cx + math.sin(ang) * 3, cy - 2 - abs(math.cos(ang)) * 3)], fill=(80, 140, 60))
    # splash droplets
    fx.burst(img, t, SPLAT, x, y - 2, n=14, colors=((104, 58, 40), (255, 248, 236), (190, 222, 246)),
             speed=(30, 80), gravity=260, life=0.45, spread=(190, 350), seed=21)


def _gin_eating(img, t, expr="happy", frozen_arm=None):
    f = step_frame(t, 3, 2)
    arm = frozen_arm if frozen_arm is not None else (150 if f else 84)
    e = expr
    if expr == "happy" and f:
        e = "talk"
    draw_char(img, "gintoki", GIN_X, A.SEAT_Y, "sit", t, facing=-1, expr=e, arm_f=arm, arm_b=40,
              props=[_spoon_prop])


# ------------------------------------------------------------------ shots
def shot_a(img, t):
    k0 = ease_in_out(seg(t, 0.15, 1.55))
    k = lerp(1.06, 1.72, k0) + 0.06 * seg(t, 1.55, TB)
    cam = Cam(k, lerp(168, 250, k0), lerp(106, 128, k0))
    flap = 0.0
    if t < 0.9:
        flap = abs(math.cos(t * 13)) * math.exp(-t * 3.2) * 0.8 + (0.8 if t < 0.12 else 0)
    rest_world(img, t, door=min(0.95, flap))
    # pig A on his stool (faces left toward Shinpachi)
    if t < 2.0:
        draw_char(img, "amanto_pig", PIGA_X, A.SEAT_Y, "sit", t, facing=-1, expr="smug")
    else:
        draw_char(img, "amanto_pig", PIGA_X, A.SEAT_Y, "laugh", t, facing=-1, legs="sit")
    # pig B standing in front of the counter
    if t < STOMP:
        draw_char(img, "amanto_pig", PIGB_X, FLOOR, "arms_crossed", t, facing=-1)
    elif t < 3.7:
        dx = -3 * ease_out(seg(t, STOMP, STOMP + 0.08))
        draw_char(img, "amanto_pig", PIGB_X + dx, FLOOR, "bully", t, facing=-1)
        _vein(img, PIGB_X - 4 + int(dx), FLOOR - 30, t, STOMP)
    else:
        draw_char(img, "amanto_pig", PIGB_X, FLOOR, "laugh", t, facing=-1)
    _parfait_on_counter(img, t)
    _gin_eating(img, t)
    _hearts(img, GIN_X - 2, A.SEAT_Y - 30, t)
    # Shinpachi: walks out of the kitchen with the tray
    if t < 1.3:
        k2 = seg(t, 0.0, 1.3)
        x = lerp(A.DOOR_CX + 4, SHIN_X, ease_out(k2))
        draw_char(img, "shinpachi", x, FLOOR, "waiter_walk", t)
    else:
        e = "shock" if STOMP <= t < 2.2 else ("sad" if t >= 2.2 else None)
        dy = -2 if STOMP <= t < STOMP + 0.1 else 0
        draw_char(img, "shinpachi", SHIN_X, FLOOR + dy, "waiter", t, expr=e)
        if t >= STOMP:
            _sweat(img, SHIN_X + 7, FLOOR - 30, t, STOMP + 0.1)
    if STOMP <= t < STOMP + 0.5:
        fx.smoke_puff(img, t, STOMP, PIGB_X - 4, FLOOR, size=6, seed=3)
    cam.apply(img)
    if STOMP <= t < STOMP + 0.6:
        sx, sy = cam.pt(PIGB_X - 22, FLOOR - 40)
        sfx_text(img, sx, sy, "咚！", t, STOMP, 0.6, size=22)
    dx, dy = fx.shake_offset(t, STOMP, 0.25, 3, seed=1)
    fx.shift(img, dx, dy)


def shot_b(img, t):
    fall = ease_in_out(seg(t, KNOCK, SPLAT + 0.1))
    cam = Cam(2.6, lerp(279, 283, fall), lerp(128, 140, fall))
    rest_world(img, t)
    # pig B: laugh, then the fateful backswing
    # pig B turns to mock Gintoki, raises his fist and SLAMS the counter
    if t < SWING:
        draw_char(img, "amanto_pig", PIGB_X, FLOOR, "laugh", t, facing=1)
    else:
        if t < KNOCK - 0.08:
            arm_f = lerp(95, 178, ease_out(seg(t, SWING, KNOCK - 0.08)))
        else:
            arm_f = lerp(178, 104, ease_in(seg(t, KNOCK - 0.08, KNOCK)))
        draw_char(img, "amanto_pig", PIGB_X, FLOOR, "laugh", t, facing=1, arm_f=arm_f, lean=1 if t >= KNOCK else 0,
                  expr="shout" if t >= KNOCK - 0.08 else None)
        if KNOCK - 0.08 <= t < KNOCK + 0.2:
            fx.slash_arc(img, PIGB_X + 4, FLOOR - 15, 9, -80, 10, seg(t, KNOCK - 0.08, KNOCK + 0.12) * 1.3,
                         (255, 255, 255), 2)
    _parfait_on_counter(img, t)
    if t < KNOCK:
        _gin_eating(img, t, expr="happy")
        for i in range(3):
            fx.sparkle(img, GIN_X - 12 + i * 9, A.SEAT_Y - 32 + (i % 2) * 5, t, TB + 0.05 + i * 0.22,
                       size=3, color=(255, 240, 160))
        _hearts(img, GIN_X - 2, A.SEAT_Y - 30, t)
    elif t < SPLAT:
        # frozen mid-bite, spoon still up, hand reaching after the falling parfait
        reach = ease_out(seg(t, KNOCK + 0.05, KNOCK + 0.2))
        _gin_eating(img, t, expr="shock", frozen_arm=int(lerp(84, 118, reach)))
    else:
        _gin_eating(img, t, expr="normal", frozen_arm=118)
    _parfait_flight(img, t)
    _splat(img, t)
    if KNOCK <= t < KNOCK + 0.3:
        fx.burst(img, t, KNOCK, PIGB_X + 11, A.COUNTER_TOP + 2, n=10,
                 colors=((255, 255, 255), (255, 240, 180)), speed=(30, 80), gravity=0, life=0.25, seed=5)
    cam.apply(img)
    if KNOCK <= t < KNOCK + 0.45:
        # left of the pig so it never covers the flying parfait
        sx, sy = cam.pt(PIGB_X - 16, A.COUNTER_TOP - 22)
        sfx_text(img, sx, sy, "咚！", t, KNOCK, 0.45, size=20, angle=-12)
    if KNOCK + 0.06 <= t < SPLAT:
        sx, sy = cam.pt(GIN_X + 9, A.SEAT_Y - 40)
        sfx_text(img, sx, sy, "！", t, KNOCK + 0.06, SPLAT - KNOCK - 0.06 + 0.01, size=30,
                 color=(255, 255, 255), angle=6, shake=0)
    if t >= SPLAT:
        sx, sy = cam.pt(SPLAT_POS[0] - 12, SPLAT_POS[1] - 16)
        sfx_text(img, sx, sy, "啪嚓", t, SPLAT, 0.7, size=18, color=(255, 255, 255), angle=10)
    dx, dy = fx.shake_offset(t, SPLAT, 0.2, 2, seed=2)
    fx.shift(img, dx, dy)


CAW_T = TC + 0.12
CAW2_T = CAW_T + 0.60          # 'crow' SFX: 2nd caw at 0.78 s, played at pitch 1.3 -> 0.6 s


def _crow_pos(t):
    """Crow gliding right->left across the window view during the silence."""
    u = seg(t, TC, TD + 0.1)
    x = lerp(A.WIN[2] + 12, 186, u)
    y = 84 + wave(t, 1.6, 2) - u * 4
    return x, y


def shot_c(img, t):
    k = ease_in_out(seg(t, TC, TD))
    cam = Cam(lerp(1.72, 2.1, k), lerp(262, 272, k), lerp(108, 118, k))
    frz = SPLAT
    cxw, cyw = _crow_pos(t)
    crow = (cxw, cyw, "crow%d" % step_frame(t, 8, 2), True)
    rest_world(img, t, crow=crow, freeze=frz)
    draw_char(img, "amanto_pig", PIGA_X, A.SEAT_Y, "laugh", frz, facing=-1, legs="sit")
    draw_char(img, "amanto_pig", PIGB_X, FLOOR, "laugh", frz, facing=1, arm_f=104, lean=1)
    draw_char(img, "gintoki", GIN_X, A.SEAT_Y, "sit", frz, facing=-1, expr="normal", arm_f=118, arm_b=40,
              props=[_spoon_prop])
    _splat(img, t)
    cam.apply(img)
    # "……" over Gintoki's blank face: dots appear one by one
    if t > CAW_T + 0.15:
        n = min(3, int((t - CAW_T - 0.15) / 0.2) + 1)
        gx, gy = cam.pt(GIN_X - 8, A.SEAT_Y - 42)
        for i in range(n):
            rect(img, gx + i * 8 - 1, gy - 1, 6, 6, INK)
            rect(img, gx + i * 8, gy, 4, 4, (255, 255, 255))
    # 阿～ ... 呆～ trailing behind the crow, in sync with the two caws
    for tt, word, dx in ((CAW_T, "阿～", 12), (CAW2_T, "呆～", 12)):
        if t >= tt:
            cx, cy = _crow_pos(tt + 0.15)
            bx, by = cam.pt(cx + dx, cy - 2)
            a = 1 - seg(t, TD - 0.12, TD)
            s = ease_out_back(clamp((t - tt) / 0.15))
            spr = text_sprite(word, (255, 255, 255), 12, outline=INK)
            if s < 1:
                spr = spr.resize((max(1, int(spr.width * s)), max(1, int(spr.height * s))), Image.NEAREST)
            paste(img, spr, bx, by - int((t - tt) * 10), anchor="center", alpha=a)


def shot_d(img, t):
    img.paste((8, 6, 14), (0, 0, W, H))
    serious = t >= EYES_SNAP
    band = A.eye_band(serious)
    drift = int(lerp(-6, 6, seg(t, TD, TE)))
    by = 68
    if serious:
        dx, dy = fx.shake_offset(t, EYES_SNAP, 0.25, 2, seed=4)
    else:
        dx, dy = 0, 0
    img.paste(band, (drift + dx, by + dy))
    if serious:
        # speed streaks in the black bars
        fx.motion_lines(img, t, color=(120, 30, 40), count=10, direction=-1, seed=7, y0=6, y1=62, speed=700)
        fx.motion_lines(img, t, color=(120, 30, 40), count=10, direction=1, seed=8, y0=154, y1=210, speed=700)
        for ex in (62, 130):
            gx = drift + dx + (ex + (1 if ex > 96 else -1)) * 2 + (4 if ex > 96 else -4)
            fx.sparkle(img, gx, by + dy + 42, t, EYES_SNAP + 0.02, size=7, color=(255, 255, 255))
    rect(img, 0, by - 2, W, 1, (200, 190, 210))
    rect(img, 0, by + band.height + 1, W, 1, (200, 190, 210))
    if EYES_SNAP <= t < EYES_SNAP + 0.1:
        fx.flash(img, 1 - seg(t, EYES_SNAP, EYES_SNAP + 0.1))


E_CUT = HIT + 0.17
FLEE = CRASH + 0.12
TWINKLE = CRASH + 0.45


def _pig_a_flee(t):
    k = t - FLEE
    if k < 0.12:
        x, y = arc((PIGA_X, A.SEAT_Y), (PIGA_X - 8, FLOOR + 20), k / 0.12, 6)
        return x, y
    return PIGA_X - 8 - (k - 0.12) * 260, FLOOR + 20


def _pig_flight_pos(k):
    ke = ease_in(k) * 0.35 + k * 0.65
    x, y = arc((PIGB_X, FLOOR - 4), (A.HOLE[0], A.HOLE[1] + 12), ke, 26)
    return x, y, lerp(1.0, 0.85, ke)


def shot_e(img, t):
    close = t < E_CUT
    cam = Cam(2.0, 280, 132) if close else Cam(1.4, 192, 118)
    rest_world(img, t, hole=t >= CRASH)
    # pig A: shock, then flees (hops off the stool and runs off screen-left in the foreground)
    if t < FLEE:
        draw_char(img, "amanto_pig", PIGA_X, A.SEAT_Y, "shock", t, p=seg(t, HIT, HIT + 0.5), facing=1, legs="sit")
    # pig B
    if t < LEAP + 0.12:
        draw_char(img, "amanto_pig", PIGB_X, FLOOR, "laugh", t, facing=1)
    elif t < HIT:
        draw_char(img, "amanto_pig", PIGB_X, FLOOR, "shock", t, p=seg(t, LEAP + 0.12, HIT), facing=1)
    elif t < CRASH:
        k = seg(t, HIT, CRASH)
        for i in ((3, 2, 1, 0) if not close else (0,)):
            kk = clamp(k - i * 0.07)
            if kk <= 0 and i:
                continue
            x, y, sc = _pig_flight_pos(kk)
            draw_char(img, "amanto_pig", x, y, "fly", t - i * 0.03, facing=-1, scale=sc, shadow=False,
                      alpha=1.0 if i == 0 else 0.28, flash=0.6 if (i == 0 and t < HIT + 0.08) else 0)
    # Gintoki
    gx = GIN_X - 12
    if t < LEAP + 0.15:
        k = seg(t, LEAP, LEAP + 0.15)
        x, y = arc((GIN_X, A.SEAT_Y), (gx, FLOOR), k, 10)
        draw_char(img, "gintoki", x, y, "jump", t, facing=-1, expr="angry")
    elif t < HIT + 0.7:
        p = lerp(0.25, 1.0, seg(t, LEAP + 0.15, LEAP + 0.6))
        draw_char(img, "gintoki", gx, FLOOR, "attack", t, p=p, facing=-1, expr="angry")
    else:
        draw_char(img, "gintoki", gx, FLOOR, "shoulder", t, facing=-1, expr="normal")
    # Shinpachi
    draw_char(img, "shinpachi", SHIN_X, FLOOR, "shock", t, p=seg(t, HIT, HIT + 0.6), torso="apron")
    if t >= HIT + 0.2:
        _sweat(img, SHIN_X + 7, FLOOR - 30, t, HIT + 0.2)
    _splat(img, max(t, SPLAT + 2))
    # the bokuto swing: a white crescent from overhead down to the left
    if HIT - 0.07 <= t < HIT + 0.3:
        fx.slash_arc(img, gx - 3, FLOOR - 17, 17, -50, -215, seg(t, HIT - 0.07, HIT + 0.12) * 1.35,
                     (255, 255, 255), 4)
    # pig A flees in the FOREGROUND (drawn last = closest to camera)
    if t >= FLEE:
        for i in range(3):
            fx.smoke_puff(img, t, FLEE + 0.12 + i * 0.12, *_pig_a_flee(FLEE + 0.12 + i * 0.12), size=4,
                          seed=34 + i, life=0.35)
        if t < FLEE + 0.5:
            fx.smoke_puff(img, t, FLEE, PIGA_X, FLOOR, size=7, seed=33)
        fxp, fyp = _pig_a_flee(t)
        draw_char(img, "amanto_pig", fxp, fyp, "run_away", t, facing=-1, expr="cry")
    if t >= CRASH:
        fx.burst(img, t, CRASH, A.HOLE[0], A.HOLE[1], n=26,
                 colors=((250, 242, 222), (200, 186, 160), (120, 100, 90)), speed=(40, 140), gravity=260,
                 life=0.9, size=(1, 3), seed=31)
        fx.smoke_puff(img, t, CRASH, A.HOLE[0], A.HOLE[1] + 6, size=16, seed=32, color=(236, 228, 214), life=1.0)
        for i in range(6):
            r = rng("dust", i)
            ph = ((t - CRASH) * r.uniform(0.8, 1.3) + r.random()) % 1.0
            pset(img, A.HOLE[0] + int(r.uniform(-10, 10)), A.HOLE[1] + 16 + int(ph * 50), (236, 228, 214))
        # ...and through the pig-shaped hole he becomes a twinkling star in the sky
        fx.sparkle(img, A.HOLE[0] + 5, A.HOLE[1] - 1, t, TWINKLE, size=6, color=(255, 214, 60))
    cam.apply(img)
    if close and HIT <= t:
        sx, sy = cam.pt(PIGB_X, FLOOR - 20)
        fx.speed_lines(img, t, sx, sy, color=(255, 255, 255), count=44, inner=60, seed=9)
        sx, sy = cam.pt(PIGB_X + 30, FLOOR - 56)
        sfx_text(img, sx, sy, "砰！！", t, HIT, 0.5, size=34, angle=8)
    if t >= CRASH:
        sx, sy = cam.pt(A.HOLE[0] + 32, A.HOLE[1] - 20)
        sfx_text(img, sx, sy, "轰！", t, CRASH, 0.8, size=26, color=(255, 140, 60), angle=8)
    if not close and FLEE <= t < FLEE + 0.7:
        px_, py_ = _pig_a_flee(t)
        sx, sy = cam.pt(px_ - 4, py_ - 44)
        draw_text(img, sx, sy, "噫——！", (255, 255, 255), outline=INK)
    if HIT <= t < HIT + 2 / 30:
        fx.impact_frame(img)
    elif HIT + 2 / 30 <= t < HIT + 0.16:
        fx.flash(img, 0.6 * (1 - seg(t, HIT + 2 / 30, HIT + 0.16)))
    dx, dy = fx.shake_offset(t, HIT, 0.2, 4, seed=5)
    dx2, dy2 = fx.shake_offset(t, CRASH, 0.4, 4, seed=6)
    fx.shift(img, dx + dx2, dy + dy2)


def _gloom(img, t, t0):
    """Anime 'gaan' shock: dark vertical lines raining down over the top of the frame."""
    if t < t0:
        return
    k = ease_out(seg(t, t0, t0 + 0.35))
    for i in range(22):
        r = rng("gloom", i)
        x = int(r.uniform(96, 300))
        L = int(r.uniform(30, 120) * k)
        w = r.choice((1, 2, 2, 3))
        if L > 0:
            overlay_rect(img, x, 0, w, L, (36, 30, 84), r.uniform(0.3, 0.55))


def shot_f(img, t):
    if t < TRAY_DROP:
        cam = Cam(1.7, 116, 126)
    else:   # snap zoom onto the petrified Shinpachi
        k = ease_out(seg(t, TRAY_DROP, TRAY_DROP + 0.12))
        cam = Cam(lerp(1.7, 2.4, k) + 0.04 * seg(t, TRAY_DROP, TG), lerp(116, SHIN_X - 8, k), lerp(126, 139, k))
    door = 0.0 if t < DOOR_BANG else 1.0
    rest_world(img, t, door=door, hole=True)
    # manager storms out
    if t < DOOR_BANG + 0.3:
        k = ease_out(seg(t, DOOR_BANG, DOOR_BANG + 0.3))
        mx, my = lerp(A.DOOR_CX, 70, k), lerp(A.WALL_BASE + 2, FLOOR, k)
        hx, hy = _manager(img, mx, my, "walk", t, expr="angry")
    elif t < DOOR_BANG + 0.6:
        hx, hy = _manager(img, 70, FLOOR, "point", t, p=seg(t, DOOR_BANG + 0.3, DOOR_BANG + 0.6))
    else:
        hx, hy = _manager(img, 70, FLOOR, "shout", t)
    _vein(img, hx + 9, hy + 4, t, DOOR_BANG + 0.1)
    if t >= DOOR_BANG + 0.3:
        for i in range(2):
            fx.smoke_puff(img, t, DOOR_BANG + 0.3 + i * 0.45, hx + (i * 6 - 3), hy - 4, size=5, seed=40 + i,
                          color=(240, 240, 240), life=0.5)
    # Shinpachi: shock -> tray drops -> stone
    if t < TRAY_DROP:
        draw_char(img, "shinpachi", SHIN_X, FLOOR, "waiter", t, expr="shock", facing=-1)
        _sweat(img, SHIN_X - 8, FLOOR - 30, t, DOOR_BANG + 0.2)
    else:
        draw_char(img, "shinpachi", SHIN_X, FLOOR, "shock", TRAY_DROP + 0.05, p=0.3, facing=-1, torso="apron",
                  flash=0.55, flash_color=(150, 150, 164), expr="gloom")
        if t >= TRAY_DROP + 0.12:
            _stone_cracks(img, SHIN_X, FLOOR)
        # tray falls and clatters
        k = seg(t, TRAY_DROP, TRAY_DROP + 0.25)
        tx = SHIN_X - 12 - k * 4
        ty = lerp(FLOOR - 16, FLOOR + 2, ease_in(k))
        if t > TRAY_DROP + 0.25:
            b = seg(t, TRAY_DROP + 0.25, TRAY_DROP + 0.45)
            ty = FLOOR + 2 - math.sin(b * math.pi) * 3
        tr = rotate_nearest(A.spr("tray"), int(lerp(0, 25, k)) if t < TRAY_DROP + 0.25 else 0)
        paste(img, tr, int(tx), int(ty), anchor="bottom")
        if t < TRAY_DROP + 0.25:
            paste(img, A.spr("parfait"), int(tx + 6), int(ty - 4 - k * 2), anchor="bottom")
        else:
            fx.burst(img, t, TRAY_DROP + 0.25, int(tx), FLOOR, n=10, colors=((190, 222, 246), (255, 255, 255)),
                     speed=(30, 70), gravity=240, life=0.4, spread=(200, 340), seed=44)
    _splat(img, SPLAT + 3)
    cam.apply(img)
    if DOOR_BANG <= t < DOOR_BANG + 0.6:
        sx, sy = cam.pt(A.DOOR_CX + 22, A.DOOR[1] + 6)
        sfx_text(img, sx, sy, "砰！", t, DOOR_BANG, 0.6, size=24)
    if t >= TRAY_DROP + 0.25:
        sx, sy = cam.pt(SHIN_X - 30, FLOOR - 6)
        sfx_text(img, sx, sy, "哐啷", t, TRAY_DROP + 0.25, 0.7, size=18, color=(255, 255, 255), angle=-4)
    if t >= TRAY_DROP:
        _gloom(img, t, TRAY_DROP)
        if TRAY_DROP <= t < TRAY_DROP + 0.08:
            fx.flash(img, 0.7, (200, 200, 230))
    if t >= TRAY_DROP + 0.12:
        sx, sy = cam.pt(SHIN_X + 22, FLOOR - 40)
        sfx_text(img, sx, sy, "咔嚓", t, TRAY_DROP + 0.12, TG - TRAY_DROP - 0.12, size=20,
                 color=(214, 214, 226), angle=10, shake=0)
    dx, dy = fx.shake_offset(t, DOOR_BANG, 0.3, 3, seed=7)
    dx2, dy2 = fx.shake_offset(t, TRAY_DROP, 0.2, 2, seed=8)
    dx, dy = dx + dx2, dy + dy2
    fx.shift(img, dx, dy)


G_TWO = TSUKKOMI + 0.7
FLICK = G_TWO + 0.42           # Gintoki flicks his booger at the tsukkomi...
BOOGER_HIT = FLICK + 0.26      # ...and it sticks on Shinpachi's glasses
GIN_G = 330


def _booger_pos(t):
    k = seg(t, FLICK, BOOGER_HIT)
    return arc((GIN_G - 5, FLOOR - 26), (SHIN_X + 8, FLOOR - 24), k, 10)


def shot_g(img, t):
    if t < TSUKKOMI:
        cam = Cam(1.5, 244, 128)
    elif t < G_TWO:
        k = ease_out_back(seg(t, TSUKKOMI, TSUKKOMI + 0.15))
        cam = Cam(lerp(2.0, 2.4, k), 204, 136)
    else:
        cam = Cam(lerp(1.6, 1.68, seg(t, G_TWO, TH)), 262, 130)
    rest_world(img, t, door=1.0, hole=True)
    _splat(img, SPLAT + 3)
    # Gintoki strolls away, picking his nose; looks back at the tsukkomi and flicks a booger
    if t < TSUKKOMI + 0.1:
        gx = lerp(GIN_X - 12, GIN_G, seg(t, TG, TSUKKOMI + 0.1))
        draw_char(img, "gintoki", gx, FLOOR, "walk", t, arm_f=165, expr="normal")
    elif t < FLICK:
        draw_char(img, "gintoki", GIN_G, FLOOR, "nosepick", t, facing=-1, arm_f=165)
        _sweat(img, GIN_G - 8, FLOOR - 32, t, G_TWO + 0.3, period=1.2)
    elif t < FLICK + 0.2:
        draw_char(img, "gintoki", GIN_G, FLOOR, "nosepick", t, facing=-1, arm_f=112, expr="smug")
    else:
        draw_char(img, "gintoki", GIN_G, FLOOR, "idle", t, facing=-1, expr="smug")
    # Shinpachi
    if t < TSUKKOMI:
        draw_char(img, "shinpachi", SHIN_X, FLOOR, "shock", TRAY_DROP + 0.05, p=0.3, facing=-1, torso="apron",
                  flash=0.55, flash_color=(150, 150, 164), expr="gloom")
        _stone_cracks(img, SHIN_X, FLOOR)
        lx = 150 + (t - TG) * 30
        pset(img, int(lx), int(90 + (t - TG) * 20 + wave(t, 2, 2)), (236, 228, 214))
    else:
        p = seg(t, TSUKKOMI, TSUKKOMI + 0.4)
        jit = (step_frame(t, 12) % 2) if t >= G_TWO else 0          # trembling tsukkomi finger
        e = "shock" if BOOGER_HIT <= t < BOOGER_HIT + 0.25 else ("angry" if t >= BOOGER_HIT else None)
        draw_char(img, "shinpachi", SHIN_X + 4 + jit, FLOOR, "point", t, p=p, torso="apron", expr=e)
        if t < TSUKKOMI + 0.3:
            fx.smoke_puff(img, t, TSUKKOMI, SHIN_X, FLOOR, size=7, seed=50)
        if t >= BOOGER_HIT:
            bx, by = SHIN_X + 8, FLOOR - 24
            rect(img, bx - 1, by - 1, 3, 3, INK)
            pset(img, bx, by, (178, 200, 110))
            _vein(img, SHIN_X + 12, FLOOR - 33, t, BOOGER_HIT + 0.12)
            for i in range(2):
                fx.smoke_puff(img, t, BOOGER_HIT + 0.2 + i * 0.3, SHIN_X + 2 + i * 5, FLOOR - 36, size=4,
                              seed=52 + i, color=(250, 250, 250), life=0.45)
    if FLICK <= t < BOOGER_HIT:
        bx, by = _booger_pos(t)
        rect(img, int(bx) - 1, int(by) - 1, 3, 3, INK)
        pset(img, int(bx), int(by), (178, 200, 110))
    cam.apply(img)
    if TSUKKOMI <= t < G_TWO:
        sx, sy = cam.pt(SHIN_X + 4, FLOOR - 24)
        fx.speed_lines(img, t, sx, sy, color=(255, 255, 255), count=46, inner=70, seed=11)
        # screen-space, left of his head: never collides with the name card band (x>134, y 22-72)
        sfx_text(img, 70, 104, "喂！！", t, TSUKKOMI, G_TWO - TSUKKOMI, size=34, color=(255, 255, 255),
                 outline=(30, 60, 150), angle=-10)
    if G_TWO <= t < FLICK:
        qx, qy = cam.pt(GIN_G, FLOOR - 42)
        k = ease_out_back(clamp((t - G_TWO - 0.1) / 0.2))
        if k > 0:
            q = text_sprite("？", (255, 255, 255), 16, outline=INK)
            q = q.resize((max(1, int(q.width * k)), max(1, int(q.height * k))), Image.NEAREST)
            paste(img, q, qx, qy, anchor="center")
    if FLICK <= t < FLICK + 0.3:
        fx.sparkle(img, *cam.pt(GIN_G - 6, FLOOR - 26), t, FLICK, size=4, color=(255, 255, 255))
    if t >= BOOGER_HIT:
        sx, sy = cam.pt(SHIN_X + 22, FLOOR - 40)
        sfx_text(img, sx, sy, "啪", t, BOOGER_HIT, TH - BOOGER_HIT, size=16, color=(255, 255, 255), angle=12)
    name_card(img, t, TG + 0.05, 2.2, "shinpachi", "志村新八", "吐槽担当｜本体是眼镜", side="right")
    dx, dy = fx.shake_offset(t, TSUKKOMI, 0.3, 4, seed=12)
    fx.shift(img, dx, dy)


# ------------------------------------------------------------------ dojo
OTAE_X = 182
GIN_DX = 150
SHIN_DX = 104


def _dojo_motes(img, t, n=18):
    for i in range(n):
        r = rng("mote", i)
        x = (r.uniform(0, W) + t * r.uniform(3, 8)) % W
        y = (r.uniform(30, 160) - t * r.uniform(2, 5)) % 140 + 20
        if (step_frame(t, 6) + i) % 4:
            pset(img, int(x), int(y), (255, 230, 180))


def _gin_fallen_sprite(tint_k=0.14):
    spr, ax, ay = render_sprite("gintoki", "sit", FALL0, expr="hurt", flash=tint_k, flash_color=(120, 60, 170),
                                arm_f=170, arm_b=170)
    return spr, ax, ay


def _gin_dojo(img, t):
    """Gintoki in the dojo: sits, sweats, eats the egg, turns purple, falls, soul."""
    if t < CHOMP:
        e = "shock" if t >= EGG_PUSH else ("normal" if t < AURA + 0.3 else "sad")
        draw_char(img, "gintoki", GIN_DX, FLOOR, "sit", t, expr=e)
        if t >= EGG_PUSH:
            _sweat(img, GIN_DX + 10, FLOOR - 26, t, EGG_PUSH, 0.6)
            _sweat(img, GIN_DX - 9, FLOOR - 22, t, EGG_PUSH + 0.3, 0.7)
        return
    if t < FALL0:
        purple = 0.35 * seg(t, PURPLE, PURPLE + 0.15)
        f = step_frame(t, 8, 2)
        e = "talk" if (t < PURPLE and f) else ("shock" if t >= PURPLE else "happy")
        props = [_egg_hand_prop] if t < CHOMP + 0.2 else []
        draw_char(img, "gintoki", GIN_DX, FLOOR, "sit", t, expr=e, arm_f=150 if t < PURPLE else 60,
                  flash=purple, flash_color=(120, 60, 170), props=props,
                  head_dx=int(wave(t, 12, 1)) if t >= PURPLE else 0)
        return
    # fall backwards (rotate about the hip), legs up
    k = ease_in(seg(t, FALL0, FALL1))
    spr, ax, ay = _gin_fallen_sprite()
    spr = spr.rotate(90 * k, resample=Image.NEAREST, center=(ax, ay - 2))
    img.paste(spr, (int(GIN_DX - ax), int(FLOOR - ay + 3 * k)), spr)


def _soul(img, t, x, y, t0):
    if t < t0:
        return
    k = seg(t, t0, t0 + 0.6)
    sy = y - 4 - k * 18 - wave(t, 0.8, 2)
    sx = x + wave(t, 0.6, 3)
    d = ImageDraw.Draw(img)
    d.line([(x, y), (sx, sy + 8)], fill=(200, 210, 240))
    paste(img, A.spr("soul"), int(sx), int(sy), anchor="center", alpha=0.85)


def dojo_world(img, t):
    img.paste(A.dojo_bg())
    _dojo_motes(img, t)


def shot_h0(img, t):
    """Dusk exterior: the Shimura dojo gate; Shinpachi leads Gintoki home."""
    k = seg(t, TH, TH2)
    cam = Cam(lerp(1.18, 1.34, ease_in_out(k)), lerp(190, 206, k), lerp(114, 110, k))
    img.paste(A.gate_back())
    C.clouds(img, t, 0, "dusk", seed=4, count=5, y0=6, y1=60)
    f = A.gate_front()
    img.paste(f, (0, 0), f)
    C.lantern(img, 132, 76, t, tod="dusk")
    C.cherry_tree(img, 322, 158, t, tod="dusk")
    sx = lerp(92, 150, k)
    draw_char(img, "shinpachi", sx, 163, "walk", t, expr="sad", flash=0.12, flash_color=(255, 170, 120))
    draw_char(img, "gintoki", sx - 28, 163, "walk", t + 0.2, arm_f=165, flash=0.12, flash_color=(255, 170, 120))
    cam.apply(img)
    fx.sakura(img, t, count=10, seed=8, wind=18, fall=10)


def _egg_insert(img, t):
    """INSERT: extreme close-up of the 'fried egg' -- a charred lump of dark matter,
    bubbling, purple miasma (with a skull) rising off it."""
    img.paste(A.egg_insert_bg())
    k = seg(t, EGG_PUSH, EGG_INS_END)
    fx.speed_lines(img, t, 192, 112, color=(118, 64, 146), count=34, inner=96, seed=70)
    cx, cy = A.PLATE_C
    egg = A.egg_big()
    ey = cy + 2 + int(wave(t, 5, 1))
    # miasma columns rising off the egg (kept below the name-card band, y > 74)
    for c, (bx, ph) in enumerate(((cx - 22, 0.0), (cx + 2, 0.4), (cx + 24, 0.8))):
        for i in range(12):
            y = ey - 30 - i * 3.5 - ((t * 30) % 3.5)
            if y < 76:
                break
            amp = 2 + i * 0.6
            x = bx + math.sin(y * 0.12 - t * 8 + ph * 6) * amp
            col = (196, 120, 236) if (i + c + step_frame(t, 12)) % 3 else (120, 56, 160)
            sz = 4 if i < 6 else 3
            rect(img, int(x) - sz // 2, int(y), sz, sz, col)
    sk = A.skull()
    paste(img, sk, cx - 46 + int(wave(t, 1.3, 3)), int(100 - k * 8 + wave(t, 2.1, 2)), anchor="center")
    paste(img, egg, cx, ey, anchor="bottom")
    # bubbles swelling and popping on the crust
    for i in range(5):
        r = rng("bub", i)
        bx = cx + int(r.uniform(-28, 28))
        by = ey - int(r.uniform(10, 30))
        ph = ((t - EGG_PUSH) * r.uniform(2.2, 3.2) + r.random()) % 1.0
        if ph < 0.8:
            rr = 1 + ph * 4
            ImageDraw.Draw(img).ellipse([bx - rr, by - rr, bx + rr, by + rr], fill=(60, 40, 70),
                                         outline=(170, 80, 214))
        elif ph < 0.95:
            for dx_, dy_ in ((-4, -2), (4, -2), (0, -5), (-3, 2), (3, 2)):
                pset(img, bx + dx_, by + dy_, (190, 120, 230))
    draw_text(img, 14, 22, "※本品为煎蛋", (255, 236, 150), size=12, outline=INK)
    fx.vignette(img, 0.35)


def shot_h(img, t):
    if EGG_PUSH <= t < EGG_INS_END:
        _egg_insert(img, t)
        name_card(img, t, OTAE_CARD, 2.2, "otae", "志村妙", "新八的姐姐｜笑容可怕·暗黑料理", side="right")
        return
    if t < EGG_PUSH:
        cam = Cam(lerp(2.0, 2.1, seg(t, TH2, EGG_PUSH)), 148, 132)
    elif t < CHOMP:     # back from the insert: push in on Gintoki, drenched in sweat
        k = ease_out(seg(t, EGG_INS_END, CHOMP))
        cam = Cam(lerp(2.5, 2.8, k), lerp(160, 158, k), 146)
    else:
        cam = Cam(1.95, 150, 130)
    dojo_world(img, t)
    draw_char(img, "shinpachi", SHIN_DX, FLOOR, "sit", t, expr="sad" if t >= AURA + 0.2 else None)
    if t >= AURA + 0.2:
        _sweat(img, SHIN_DX + 8, FLOOR - 26, t, AURA + 0.3, 1.0)
    _gin_dojo(img, t)
    # Otae
    if t < AURA:
        draw_char(img, "otae", OTAE_X, FLOOR, "idle", t, facing=-1)
    elif t < CHOMP:
        draw_char(img, "otae", OTAE_X - 2, FLOOR, "offer_egg", t, facing=-1, expr="dark_smile")
    else:
        draw_char(img, "otae", OTAE_X - 2, FLOOR, "idle", t, facing=-1, expr="dark_smile")
    if t >= FALL1:
        fx.smoke_puff(img, t, FALL1, GIN_DX - 8, FLOOR - 2, size=10, seed=60)
        _soul(img, t, GIN_DX - 14, FLOOR - 10, FALL1 + 0.05)
    if AURA <= t < AURA + 0.4:
        fx.burst(img, t, AURA, OTAE_X, FLOOR - 20, n=12, colors=((150, 80, 180), (84, 40, 110)),
                 speed=(20, 60), gravity=-40, life=0.4, seed=61)
    cam.apply(img)
    if t >= CHOMP:
        sx, sy = cam.pt(GIN_DX + 16, FLOOR - 40)
        sfx_text(img, sx, sy, "嘎嘣", t, CHOMP, 0.5, size=18, color=(255, 255, 255))
    if t >= FALL1:
        sx, sy = cam.pt(GIN_DX - 26, FLOOR - 34)
        sfx_text(img, sx, sy, "咚！", t, FALL1, 0.6, size=22)
    if PURPLE <= t < PURPLE + 0.1:
        fx.flash(img, 0.5 * (1 - seg(t, PURPLE, PURPLE + 0.1)), (170, 90, 220))
    name_card(img, t, OTAE_CARD, 2.2, "otae", "志村妙", "新八的姐姐｜笑容可怕·暗黑料理", side="right")
    dx, dy = fx.shake_offset(t, FALL1, 0.2, 2, seed=13)
    fx.shift(img, dx, dy)


def _rays(img, cx, cy, t, amount, color=(255, 214, 150), n=10):
    if amount <= 0:
        return
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    R = 420
    rot = t * 0.22
    for i in range(n):
        a0 = rot + i * 2 * math.pi / n
        a1 = a0 + math.pi / n * 0.55
        d.polygon([(cx, cy), (cx + math.cos(a0) * R, cy + math.sin(a0) * R),
                   (cx + math.cos(a1) * R, cy + math.sin(a1) * R)], fill=int(255 * 0.2 * amount))
    img.paste(Image.new("RGB", (W, H), color), (0, 0), mask)


RISE1 = TI + 0.2
POINT0 = 18.30                 # "我要跟着这个人" -> points at the fainted 'this man'
FIST0 = 18.95                  # "找回我的武士道！" -> raises his bokuto to the sky
I_KEYS = ((TI, 2.3, 122, 146), (POINT0, 2.3, 122, 146), (POINT0 + 0.35, 2.15, 136, 146),
          (FIST0, 2.15, 136, 146), (FIST0 + 0.4, 2.6, 118, 142), (JOIN, 2.62, 118, 142),
          (TEND, 1.5, 150, 130))


def _i_cam(t):
    for (t0, k0, x0, y0), (t1, k1, x1, y1) in zip(I_KEYS, I_KEYS[1:]):
        if t < t1:
            u = ease_in_out(seg(t, t0, t1))
            return Cam(lerp(k0, k1, u), lerp(x0, x1, u), lerp(y0, y1, u))
    return Cam(*I_KEYS[-1][1:])


def shot_i(img, t):
    cam = _i_cam(t)
    dojo_world(img, t)
    sx = SHIN_DX + 4
    _rays(img, sx, FLOOR - 24, t, seg(t, TI, TI + 0.5) * (1 + 0.7 * seg(t, FIST0, FIST0 + 0.3)))
    # fainted Gintoki + soul (continuity from H); one leg twitches now and then
    spr, ax, ay = _gin_fallen_sprite()
    spr = spr.rotate(90, resample=Image.NEAREST, center=(ax, ay - 2))
    tw = 1 if (t % 1.3) < 0.1 else 0
    img.paste(spr, (int(GIN_DX - ax), int(FLOOR - ay + 3 - tw)), spr)
    _soul(img, t, GIN_DX - 14, FLOOR - 10, TI - 1.0)
    draw_char(img, "otae", OTAE_X - 2, FLOOR, "idle", t, facing=-1)
    # Shinpachi: springs up -> pushes his glasses (glint) -> points at 'this man' -> bokuto to the sky
    if t < RISE1:
        k = seg(t, TI, RISE1)
        draw_char(img, "shinpachi", sx, FLOOR - math.sin(k * math.pi) * 10, "jump", t, expr="determined")
    elif t < POINT0:
        e = "glint" if GLINT <= t < GLINT + 0.3 else "determined"
        draw_char(img, "shinpachi", sx, FLOOR, "idle", t, expr=e, arm_f=138, arm_b=-20, legs="spread")
    elif t < FIST0:
        draw_char(img, "shinpachi", sx, FLOOR, "point", t, p=seg(t, POINT0, POINT0 + 0.3), expr="determined")
    else:
        hop = -3 if t < FIST0 + 0.1 else 0
        f = step_frame(t, 4, 4)
        draw_char(img, "shinpachi", sx, FLOOR + hop, "idle", t, expr="determined",
                  arm_f=150 + (2 if f in (1, 2) else 0), arm_b=-30, legs="spread", weapon=68, sheathed=False)
    if RISE1 <= t < RISE1 + 0.4:
        fx.smoke_puff(img, t, RISE1, sx, FLOOR, size=6, seed=80, color=(236, 220, 200), life=0.4)
    cam.apply(img)
    fx.sakura(img, t, count=22 + int(14 * seg(t, FIST0, FIST0 + 0.5)), seed=3, wind=26, fall=14)
    gx, gy = cam.pt(sx + 3, FLOOR - 22)
    fx.sparkle(img, gx, gy, t, GLINT, size=9, color=(255, 255, 255))
    if t >= FIST0:
        fx_, fy_ = cam.pt(sx + 10, FLOOR - 41)      # tip of the raised bokuto
        fx.sparkle(img, fx_, fy_, t, FIST0 + 0.05, size=11, color=(255, 246, 190))
        fx.burst(img, t, FIST0, fx_, fy_, n=14, colors=((255, 240, 170), (255, 255, 255)), speed=(60, 140),
                 gravity=0, life=0.45, seed=81)
    if POINT0 + 0.1 <= t < FIST0 + 0.3:
        # the 'this man' he vows to follow: fainted, soul leaving his mouth
        bob = int(wave(t, 3, 1.5))
        ax_, ay_ = cam.pt(GIN_DX + 8, FLOOR - 37)
        draw_text(img, ax_, ay_ + bob, "这个人", (255, 255, 255), outline=INK, anchor="mm")
        draw_text(img, ax_, ay_ + 13 + bob, "↓", (255, 226, 60), outline=INK, anchor="mm")
    for i in range(5):
        r = rng("tw", i)
        fx.sparkle(img, int(r.uniform(20, W - 20)), int(r.uniform(20, 120)), t, TI + 0.3 + i * 0.5 + r.random() * 0.3,
                   size=3, color=(255, 236, 170))
    _party_box(img, t, JOIN)


# ------------------------------------------------------------------ scene
class Shinpachi(Scene):
    id = "s02"
    title = "新八登场"
    duration = TEND
    music = [(0.0, "comedy"), (SPLAT, None), (CRASH, "comedy"), (JOIN, None)]   # JRPG jingle plays solo
    music_vol = 0.55
    subs = [
        (1.50, 3.70, "amanto_pig", "地球猴子！上菜慢死了！"),
        (9.40, 11.36, "店长", "新八！你被开除了！"),
        (12.00, 13.90, "shinpachi", "你给我等一下！！"),
        (15.10, 16.70, "otae", "请用～"),
        (17.85, 20.15, "shinpachi", "我要跟着这个人，找回我的武士道！"),
    ]

    def render(self, img, t):
        if t < TB:
            shot_a(img, t)
        elif t < TC:
            shot_b(img, t)
        elif t < TD:
            shot_c(img, t)
        elif t < TE:
            shot_d(img, t)
        elif t < TF:
            shot_e(img, t)
        elif t < TG:
            shot_f(img, t)
        elif t < TH:
            shot_g(img, t)
            if t >= WIPE0:
                fx.wipe(img, seg(t, WIPE0, TH), color=INK, direction="left")
        elif t < TH2:
            shot_h0(img, t)
            if t < WIPE1:
                fx.wipe(img, 1 - seg(t, TH, WIPE1), color=INK, direction="right")
        elif t < TI:
            shot_h(img, t)
        else:
            shot_i(img, t)

    def cues(self):
        return [
            Cue(0.0, "crowd", vol=0.22, dur=5.3),
            Cue(0.0, "footsteps", vol=0.35, dur=1.3),
            Cue(0.02, "door", vol=0.45),
            Cue(STOMP, "thud", vol=0.9),
            Cue(STOMP + 0.02, "vein", vol=0.7),
            Cue(1.62, "sweat", vol=0.6),
            Cue(TB + 0.05, "sparkle", vol=0.5),
            Cue(SWING, "whoosh", vol=0.4, pitch=0.8),
            Cue(KNOCK - 0.08, "whoosh", vol=0.6),
            Cue(KNOCK, "thud", vol=0.8),
            Cue(KNOCK + 0.02, "hit", vol=0.4, pitch=1.3),
            Cue(KNOCK + 0.06, "slide_up", vol=0.35),
            Cue(SPLAT, "glass", vol=0.9),
            Cue(SPLAT + 0.03, "record_scratch", vol=0.9),
            Cue(CAW_T, "crow", vol=0.8, pitch=1.3),
            Cue(TD, "sting_dramatic", vol=0.8),
            Cue(EYES_SNAP, "shing", vol=0.9),
            Cue(LEAP, "jump", vol=0.7),
            Cue(HIT - 0.07, "whoosh", vol=0.7),
            Cue(LEAP + 0.15, "land", vol=0.4),
            Cue(FLEE, "dash", vol=0.6),
            Cue(HIT, "punch_big", vol=1.0),
            Cue(HIT, "impact", vol=0.7),
            Cue(HIT + 0.05, "fly_away", vol=0.6),
            Cue(CRASH, "crash", vol=1.0),
            Cue(CRASH + 0.02, "thud", vol=0.6),
            Cue(TWINKLE, "twinkle", vol=0.7),
            Cue(CRASH + 0.4, "crowd", vol=0.18, dur=TH - CRASH - 0.5),
            Cue(DOOR_BANG, "door_bang", vol=1.0),
            Cue(DOOR_BANG + 0.12, "vein", vol=0.7),
            Cue(TRAY_DROP, "shock", vol=0.8),
            Cue(TRAY_DROP + 0.12, "glass", vol=0.35, pitch=0.6),
            Cue(TRAY_DROP + 0.25, "clang", vol=0.7),
            Cue(TRAY_DROP + 0.45, "clang", vol=0.3, pitch=1.25),
            Cue(TRAY_DROP + 0.28, "glass", vol=0.4, pitch=1.3),
            Cue(TG + 0.05, "whoosh", vol=0.5),
            Cue(TSUKKOMI, "slap", vol=1.0),
            Cue(TSUKKOMI + 0.02, "shock", vol=0.5),
            Cue(FLICK, "pop", vol=0.6),
            Cue(BOOGER_HIT, "slap", vol=0.45, pitch=1.6),
            Cue(BOOGER_HIT + 0.12, "vein", vol=0.6),
            Cue(WIPE0, "whoosh", vol=0.6),
            Cue(TH, "wind", vol=0.2, dur=TEND - TH),
            Cue(OTAE_CARD, "whoosh", vol=0.45),
            Cue(TH + 0.08, "bell", vol=0.5),
            Cue(TH + 0.05, "footsteps", vol=0.3, dur=TH2 - TH - 0.1),
            Cue(AURA, "aura", vol=0.9),
            Cue(EGG_PUSH, "heartbeat", vol=0.8),
            Cue(EGG_INS_END, "sweat", vol=0.7),
            Cue(CHOMP, "chomp", vol=0.9),
            Cue(CHOMP + 0.22, "gulp", vol=0.8),
            Cue(PURPLE, "shock", vol=0.7),
            Cue(FALL1, "thud", vol=0.9),
            Cue(FALL1 + 0.08, "fail", vol=0.55, pitch=1.35),
            Cue(TI, "jump", vol=0.6),
            Cue(TI + 0.05, "shine", vol=0.5),
            Cue(RISE1, "land", vol=0.5),
            Cue(GLINT, "sparkle", vol=0.8),
            Cue(POINT0, "whoosh", vol=0.4),
            Cue(FIST0, "shing", vol=0.7),
            Cue(JOIN, "fanfare", vol=0.9, pitch=1.1),     # ~1.8 s: ends right at the scene cut
        ]


SCENE = Shinpachi()
