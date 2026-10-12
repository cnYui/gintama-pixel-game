"""s01 万事屋阿银 — Kabukicho morning, Gintoki gets kicked out over the rent.

SHOT LIST (scene-local seconds)
  A  0.00- 3.60  Kabukicho street, day. Tilt down from the Terminal/sky onto the
                 Yorozuya building while panning right; townsfolk + a pig amanto
                 stroll by. Location caption 「江户·歌舞伎町」 (0.4-2.3), pop-up tags
                 「二楼·万事屋」「一楼·登势酒馆」 (1.5 / 1.75). 2.95 push-in (zoom) into
                 the 2F window -> white flash cut.
  B1 3.60- 6.10  Office interior (match cut on the window): starts on the 「糖分」
                 frame + window, then pans/pulls back onto the right sofa: Gintoki
                 asleep, Jump over his face, snot bubble + Zzz, strawberry milk on
                 the table. name_card 坂田银时 (4.30). 5.35/5.60/5.85 stomps up the
                 stairs (咚 咚 咚, shakes, ceiling dust).
  B2 6.10- 8.40  Close on the sliding door: it SLAMS open (zoom punch, speed lines,
                 shake), Otose in the doorway, anger vein. 「银时！三个月的房租呢！」
                 Gintoki keeps snoring (bubble). 7.90 she stomps over to the sofa;
                 the camera glides into the B3 two-shot (continuous move).
  B3 8.40-11.50  Two-shot. 8.55 snot bubble POPS -> Gintoki answers from under the
                 Jump 「老太婆，下个月……一定。」 -> 10.15 second vein, room goes dark,
                 purple aura, camera creeps onto Otose, 10.36 eye glint -> 10.40
                 kick chamber (trembling hold) -> 10.90 KICK (impact frame, 咚！！,
                 shake) -> whip pan: Gintoki tumbles into the window (shrinks into
                 depth), the Jump flies off -> 11.30 glass CRASH (哐啷！).
  C1 11.50-12.60 Exterior, tight on the 2F window: it bursts, Gintoki tumbles out
                 toward camera, the camera follows him down -> 12.15 face-plant on
                 the road (dust, cracks, 咚！); two gossiping ladies jump, the pig
                 amanto freezes then bursts out laughing.
  C2 12.60-14.55 Low close-up: Otose pops up behind the balcony railing, shouting /
                 pointing down, name_card 登势婆婆 (12.75). 「没钱交房租就去干活！」
                 (line starts off-screen at 12.45 as a J-cut).
  D  14.55-19.20 Close shot on the street (Yorozuya sign on top): Gintoki twitches,
                 hops up (head bump), deadpan nose-pick 「……今天的歌舞伎町，也很和平
                 呢。」 17.00 flick -> the booger hits the laughing pig (17.22), who
                 flees -> his Jump flutters down onto his head (17.85, 啪) ->
                 awkward crow 「阿～呆～」 over a deadpan hold (18.15).
"""
import math

from PIL import Image, ImageDraw

from engine.core import (Scene, Cue, W, H, seg, lerp, clamp, ease_in, ease_out, ease_in_out,
                         ease_out_back, wave, step_frame, rng, arc)
from engine.gfx import (INK, ascii_sprite, paste, rect, overlay_rect, silhouette, outline,
                        rotate_nearest, scale_nearest)
from engine import fx
from engine.text import draw_text, text_width, sfx_text, name_card
from chars import draw_char, render_sprite
from bg import kabukicho as K, yorozuya as Y

# ------------------------------------------------------------------ timing
A0, A1 = 0.00, 3.60
B1_0, B1_1 = 3.60, 6.10
B2_0, B2_1 = 6.10, 8.40
B3_0, B3_1 = 8.40, 11.50
C0, C1_1 = 11.50, 12.60          # C1: window burst + fall
C2_1 = 14.55                     # C2: Otose on the balcony
D0, D1 = 14.55, 19.20

STOMPS = (5.35, 5.60, 5.85)
DOOR_T = 6.10
WALK0, WALK1 = 7.90, 8.40        # Otose stomps from the doorway to the sofa
BUBBLE_POP = 8.55
VEIN2_T = 10.15
GLINT_T = 10.36
CH0, CH1 = 10.40, 10.64          # kick chamber (knee up), then trembling hold
SNAP = 10.82                     # leg whips round
IMPACT = 10.90                   # foot connects
CRASH = 11.30                    # interior window shatters
LAND = 12.15                     # face-plant on the street
GETUP = 14.85
FLICK = 17.00
PIG_HIT = 17.22
PIG_RUN = 17.48
MAG_LAND = 17.85
CROW_T = 18.15

# ------------------------------------------------------------------ layout
CAM0 = K.YOROZUYA_X - W // 2                       # street cam centring the Yorozuya
WIN_W = K.YOROZUYA_WINDOW                          # 2F window (world coords)
CAMC = WIN_W[0] - 50                               # exterior cam: window on the left third
WINC = (WIN_W[0] - CAMC, WIN_W[1], WIN_W[2], WIN_W[3])   # window on screen in C/D
WINC_CX = WINC[0] + WINC[2] // 2
WINC_CY = WINC[1] + WINC[3] // 2
RAIL_TOP = K.STREET_BALCONY_Y - 9                  # balcony railing top (screen y, dy=0)

GX, GY = Y.SOFA_R_X + 3, Y.SOFA_LIE_Y              # sleeping Gintoki (right sofa)
OX3, OY3 = 327, 154                                # Otose beside the sofa (B3)
OX3_KICK = 321                                     # ... steps in for the kick
IWIN = Y.WINDOW_BOX
IWIN_C = (IWIN[0] + IWIN[2] // 2, IWIN[1] + IWIN[3] // 2 + 2)
LAND_X, LAND_Y = 178, 162                          # street landing spot (screen, cam CAMC)
BACK = 156                                         # background walking lane feet y
PIG_X_D = 238                                      # where the pig stands laughing in D
GOSSIP = ((104, 0, 1), (120, 2, -1))               # (x, variant, facing) — no grey hair (≠ Otose)

# ------------------------------------------------------------------ small sprites
_SP = {
    "o": INK, "R": (228, 59, 68), "W": (255, 255, 255), "Y": (250, 210, 70),
    "y": (214, 170, 50), "S": (255, 214, 180), "H": (70, 56, 60), "B": (70, 130, 210),
    "G": (99, 199, 77), "P": (240, 236, 226),
}
MAG = ascii_sprite("""
oooooooooooo
oRRRRRRRRRRo
oRWWRWWRWWRo
oRRRRRRRRRRo
oYYYYYYYYYYo
oYSSSYYYBBYo
oYSHHSYYBBYo
oYSSSSYYYBYo
oYYSSYYYYYYo
oYYYYYYYGGYo
oYGGYYYYGGYo
oYYYYYYYYYYo
oPPPPPPPPPPo
oooooooooooo
""", _SP)
MAG_TENT = ascii_sprite("""
.........o.........
........oPo........
.......oBPYo.......
......oBBPYYo......
.....oBWBPRRYo.....
....oBBBBPRWRYo....
...oWBBBBPYRRYYo...
..oBBBWBBPYYYSYYo..
.oPPPPPPPPPPPPPPPo.
ooooooooooooooooooo
""", _SP)
VEIN = outline(ascii_sprite("""
..R.R..
.RR.RR.
RR...RR
.......
RR...RR
.RR.RR.
..R.R..
""", {"R": (240, 50, 60)}))
BUMP = ascii_sprite("""
..ooooo..
.oSSSWSo.
oSSSSSSSo
osSSSSSso
""", {"o": INK, "S": (255, 196, 170), "s": (232, 158, 140), "W": (255, 250, 240)})
ZED = outline(ascii_sprite("""
ZZZZ
..Z.
.Z..
ZZZZ
""", {"Z": (200, 226, 255)}))
CROW = [ascii_sprite(a, {"o": (20, 18, 26), "y": (70, 64, 60)}) for a in ("""
o..........o
.oo......oo.
..ooo..ooo..
.yoooooooo..
....oooo....
""", """
............
.yoooooooo..
..ooooooooo.
.oo..oo..oo.
o..........o
""")]
BOOGER_C = (150, 206, 96)


# ------------------------------------------------------------------ helpers
def _cam(img, k, cx, cy):
    """Zoom the whole frame about (cx, cy) (clamped so the view stays inside)."""
    hw, hh = W / (2.0 * k), H / (2.0 * k)
    cx = clamp(cx, hw, W - hw)
    cy = clamp(cy, hh, H - hh)
    fx.zoom(img, k, cx, cy)
    return k, cx, cy


def _scr(cam, x, y):
    k, cx, cy = cam
    return (x - cx) * k + W / 2.0, (y - cy) * k + H / 2.0


def _shake(img, t, t0, dur, amp, seed=0):
    dx, dy = fx.shake_offset(t, t0, dur, amp, seed=seed)
    if dx or dy:
        src = img.copy()
        img.paste(src, (dx, dy))       # smear edges instead of black bars


def _walk_x(t, t0, x0, speed):
    return x0 + speed * (t - t0)


def _bbox(cid, pose, t, p=None, facing=1, **kw):
    spr, ax, ay = render_sprite(cid, pose, t, p, facing=facing, **kw)
    return spr.getbbox(), ax, ay


def _vein(img, x, y, t, t0, big=False):
    """Anger mark popping in at t0 and pulsing."""
    if t < t0:
        return
    k = ease_out_back(clamp((t - t0) / 0.15))
    if k < 0.95:
        n = max(3, int(VEIN.width * k))
        spr = VEIN.resize((n, n), Image.NEAREST)
    else:
        spr = VEIN
    pulse = 1 if (big and step_frame(t, 8) % 2) else 0
    paste(img, spr, x, y - pulse, anchor="center")


def _zzz(img, x, y, t, seed=0):
    for i in range(3):
        per = 1.5
        u = ((t + i * per / 3 + seed) % per) / per
        zx = x + u * 10 + wave(t, 1.3, 1.5, i * 0.3)
        zy = y - u * 16
        s = 1 if u < 0.45 else 2
        spr = ZED if s == 1 else scale_nearest(ZED, 1.5)
        if u < 0.85:
            paste(img, spr, zx, zy, anchor="center")


def _snot_bubble(img, t, pop_t=None):
    """鼻提灯: the classic sleeping snot bubble, peeking out above the Jump.
    It breathes in and out; if pop_t is given it swells and pops there."""
    bx, by = GX - 11, GY - 21                    # just above the Jump's top edge (his nose)
    if pop_t is not None and t >= pop_t:
        q = t - pop_t
        if q < 0.18:                             # pop: ring of droplets
            d = ImageDraw.Draw(img)
            r = 6 + q * 40
            for i in range(8):
                a = i * math.pi / 4 + 0.3
                d.point((bx + math.cos(a) * r, by - 5 + math.sin(a) * r * 0.8), fill=(200, 230, 255))
        return
    breath = 0.5 - 0.5 * math.cos((t % 1.6) / 1.6 * 2 * math.pi)
    r = 1.5 + 3.5 * breath
    if pop_t is not None:                        # swelling just before popping
        r = lerp(r, 7.5, ease_in(seg(t, pop_t - 0.5, pop_t)))
    r = int(round(r))
    cy = by - r + 1
    d = ImageDraw.Draw(img)
    d.ellipse([bx - r, cy - r, bx + r, cy + r], fill=(186, 222, 246), outline=(120, 170, 210))
    if r >= 3:
        d.point((bx - r // 2, cy - r // 2), fill=(255, 255, 255))
        d.point((bx - r // 2 + 1, cy - r // 2), fill=(255, 255, 255))


def _aura(img, cid, x, y, pose, t, p=None, facing=1, color=(120, 40, 160), **kw):
    """Dark 'killing intent' aura: flickering silhouette halo behind the sprite."""
    spr, ax, ay = render_sprite(cid, pose, t, p, facing=facing, **kw)
    sil = silhouette(spr, color)
    f = step_frame(t, 12, 3)
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (-1, -3 - f), (1, -2 - f % 2), (0, 1)):
        img.paste(sil, (int(x - ax + dx), int(y - ay + dy)), sil)


def _crack(img, cx, cy, r, seed, hole_color=None):
    """Broken glass: jagged hole + radiating crack lines."""
    rr = rng("crack", seed)
    pts = []
    n = 11
    for i in range(n):
        a = i / n * 2 * math.pi
        d = r * rr.uniform(0.55, 1.0)
        pts.append((cx + math.cos(a) * d, cy + math.sin(a) * d * 0.85))
    dr = ImageDraw.Draw(img)
    if hole_color:
        dr.polygon(pts, fill=hole_color)
    dr.polygon(pts, outline=(236, 246, 255))
    for i in range(0, n, 2):
        a = i / n * 2 * math.pi + rr.uniform(-0.2, 0.2)
        L = r * rr.uniform(0.7, 1.4)
        x0, y0 = pts[i]
        dr.line([(x0, y0), (x0 + math.cos(a) * L * 0.6, y0 + math.sin(a) * L * 0.5)], fill=(210, 230, 250))


def _glass_burst(img, t, t0, x, y, seed, spread=(0, 360), speed=(40, 120), n=26):
    fx.burst(img, t, t0, x, y, n=n, colors=[(236, 248, 255), (170, 214, 240), (120, 170, 210)],
             speed=speed, gravity=260, life=0.8, size=(1, 3), seed=seed, spread=spread)


def _mag_flat(img, x, y, ang):
    spr = rotate_nearest(MAG, ang)
    paste(img, spr, x, y, anchor="center")


def _flyer(img, x, y, t, scale, trail_pts=(), facing=1):
    """Gintoki tumbling through the air (with fading after-images)."""
    for i, (tx, ty, ts, tt) in enumerate(trail_pts):
        draw_char(img, "gintoki", tx, ty, "fly", tt, facing=facing, scale=ts, alpha=0.35 - i * 0.12,
                  shadow=False)
    draw_char(img, "gintoki", x, y, "fly", t, facing=facing, scale=scale, shadow=False)


# ------------------------------------------------------------------ overlays (screen space)
def _location_caption(img, t, t0=0.4, t1=2.3):
    if not (t0 <= t < t1):
        return
    a = ease_out(seg(t, t0, t0 + 0.35))
    b = 1 - ease_in(seg(t, t1 - 0.3, t1))
    k = min(a, b)
    x = int(lerp(-150, 10, k))
    overlay_rect(img, x - 10, 170, 172, 36, (10, 8, 16), 0.55 * k)
    rect(img, x, 174, 3, 28, (228, 59, 68))
    draw_text(img, x + 9, 172, "江户·歌舞伎町", (255, 255, 255), size=22, face="brush", outline=INK)
    draw_text(img, x + 10, 194, "EDO · KABUKICHO", (255, 214, 140), size=12)


def _tag(img, t, t0, t1, bx, by, text, tip):
    """Info tag with a leader line to `tip` (pops in, pops out)."""
    if not (t0 <= t < t1):
        return
    s = ease_out_back(clamp((t - t0) / 0.2)) * (1 - ease_in(seg(t, t1 - 0.15, t1)))
    if s <= 0.1:
        return
    tw = text_width(text) + 10
    th = 16
    cx, cy = bx + tw / 2, by + th / 2
    w2, h2 = tw * s / 2, th * s / 2
    d = ImageDraw.Draw(img)
    if s > 0.6:
        d.line([(bx + 4, by + th - 1), tip], fill=INK, width=3)
        d.line([(bx + 4, by + th - 1), tip], fill=(255, 236, 120))
        d.rectangle([tip[0] - 1, tip[1] - 1, tip[0] + 1, tip[1] + 1], fill=(255, 236, 120), outline=INK)
    d.rectangle([cx - w2 - 1, cy - h2 - 1, cx + w2, cy + h2], fill=INK)
    d.rectangle([cx - w2, cy - h2, cx + w2 - 1, cy + h2 - 1], fill=(255, 250, 236))
    if s > 0.95:
        rect(img, bx, by, 3, th, (228, 59, 68))
        draw_text(img, bx + 6, by + 2, text, INK)


# ------------------------------------------------------------------ shot A: street establishing
def _walkers_a(img, t, cam, dy):
    def sx(wx):
        return wx - cam
    # townsman (topknot) strolling right, front lane
    x = _walk_x(t, 0, CAM0 - 40, 21)
    draw_char(img, "townsman", sx(x), 162 + dy, "walk", t, facing=1, variant=0)
    # townswoman walking left, back lane
    x = _walk_x(t, 0, CAM0 + 290, -18)
    draw_char(img, "townswoman", sx(x), BACK + dy, "walk", t + 0.3, facing=-1, variant=1)
    # worker in the back lane walking right
    x = _walk_x(t, 0, CAM0 + 120, 16)
    draw_char(img, "townsman", sx(x), BACK - 1 + dy, "walk", t + 0.6, facing=1, variant=3)
    # pig-faced amanto swaggering left, front lane
    x = _walk_x(t, 0, CAM0 + 420, -30)
    draw_char(img, "amanto_pig", sx(x), 163 + dy, "walk", t + 0.1, facing=-1)


def shot_a(img, t):
    tilt = ease_in_out(seg(t, 0.0, 1.5))
    dy = int(round(lerp(62, 0, tilt)))     # K.street crashes for dy > 63 (shared bg bug)
    cam = lerp(CAM0 - 70, CAM0, ease_in_out(seg(t, 0.0, 1.8)))
    K.street(img, cam, t, "day", dy=dy)
    _walkers_a(img, t, cam, dy)
    K.street_fg(img, cam, t, "day")
    # push-in into the Yorozuya window
    wx = WIN_W[0] + WIN_W[2] / 2 - cam
    wy = WIN_W[1] + WIN_W[3] / 2 + dy
    pk = ease_in(seg(t, 2.95, A1))
    if pk > 0:
        _cam(img, 1 + 2.8 * pk, wx, wy)
        if pk > 0.3:
            fx.speed_lines(img, t, W // 2, H // 2, (255, 255, 255), count=36, inner=110 - 60 * pk,
                           seed=3, alpha=0.6 * pk, thickness=1)
    _location_caption(img, t)
    _tag(img, t, 1.50, 2.90, 226, 36 + dy, "二楼·万事屋（啥活都接）", (K._YX0 + 100 - cam, 62 + dy))
    dgx = K.YOROZUYA_DOOR[0] + K.YOROZUYA_DOOR[2] - cam
    _tag(img, t, 1.75, 2.90, 238, 122 + dy, "一楼·登势酒馆（房东）", (dgx - 4, 118 + dy))
    fx.flash(img, ease_in(seg(t, A1 - 0.15, A1)) * 0.7)


# ------------------------------------------------------------------ shot B: office
def _sleeping_gintoki(img, t, talking=False, mag=True):
    draw_char(img, "gintoki", GX, GY, "sleep", t, shadow=False)
    if mag:
        if talking:
            bob = -1 if step_frame(t, 8) % 2 == 0 else 0
        else:
            bob = -1 if step_frame(t, 2) % 2 else 0
        # open Jump covering the face (rotated with his lying head)
        paste(img, rotate_nearest(MAG, 90), GX - 8, GY - 14 + bob, anchor="center")


def _mag_face_pos():
    return GX - 8, GY - 16


def _office_zzz(img, t):
    mx, my = _mag_face_pos()
    _zzz(img, mx + 8, my - 8, t)


def _b1_cam(t):
    """Match cut on the window with the 「糖分」 frame above it, then pan/pull back
    onto the sleeping Gintoki."""
    k = lerp(2.45, 2.3, ease_out(seg(t, B1_0, 3.95)))
    cx, cy = 192.0, 56.0
    u = ease_in_out(seg(t, 3.95, 4.75))
    k = lerp(k, 1.7, u) + 0.06 * seg(t, 4.75, B1_1)
    cx = lerp(cx, 268, u)
    cy = lerp(cy, 118, u)
    return k, cx, cy


def shot_b1(img, t):
    Y.office(img, t, "day")
    _sleeping_gintoki(img, t)
    Y.office_fg(img, t, "day")
    _snot_bubble(img, t)
    _office_zzz(img, t)
    # ceiling dust shaken loose by the stomps
    for i, st in enumerate(STOMPS):
        fx.burst(img, t, st, 300 + i * 18, 14, n=8, colors=[(200, 190, 170), (150, 140, 120)],
                 speed=(5, 20), gravity=120, life=0.9, size=(1, 1), seed=40 + i, spread=(60, 120))
    cam = _cam(img, *_b1_cam(t))
    for i, st in enumerate(STOMPS):
        _shake(img, t, st, 0.15, 1 + i, seed=10 + i)
    dx, dy = _scr(cam, Y.DOOR_X, Y.DOOR_BOX[1] + 10)
    for i, st in enumerate(STOMPS):
        sfx_text(img, dx - 14 + i * 12, dy + 16 - i * 12, "咚", t, st, dur=0.55, size=16 + i * 4,
                 color=(255, 240, 200), angle=8 - i * 8)
    fx.flash(img, 0.7 * (1 - seg(t, B1_0, B1_0 + 0.18)))
    name_card(img, t, 4.30, B1_1 - 4.30, "gintoki", "坂田银时", "万事屋老板｜天然卷·甜党·死鱼眼")


def _b3_cam(t):
    """Two-shot on sofa + Otose; creeps onto Otose as her anger builds, whips
    left to the window after the kick."""
    k, cx, cy = 2.2, 296.0, 127.0
    k += 0.06 * ease_in_out(seg(t, B3_0, VEIN2_T))
    if t >= VEIN2_T:
        u = ease_in_out(seg(t, VEIN2_T, SNAP))
        k = lerp(k, 2.75, u)
        cx = lerp(cx, 312, u)
        cy = lerp(cy, 124, u)
    if t >= IMPACT:
        k += 0.25 * (1 - seg(t, IMPACT, IMPACT + 0.1))          # zoom punch on contact
        u = ease_out(seg(t, IMPACT + 0.06, CRASH))
        k = lerp(k, 1.5, u)
        cx = lerp(cx, 214, u)
        cy = lerp(cy, 90, u)
    return k, cx, cy


def _b2_cam(t):
    k = 2.1 + 0.32 * (1 - ease_out(seg(t, DOOR_T, DOOR_T + 0.35)))   # slam: zoom punch
    k += 0.08 * seg(t, DOOR_T + 0.35, WALK0)
    cx, cy = 300.0, 116.0
    u = ease_in_out(seg(t, WALK0, B2_1))            # glide into the B3 two-shot
    k0, cx0, cy0 = _b3_cam(B3_0)
    return lerp(k, k0, u), lerp(cx, cx0, u), lerp(cy, cy0, u)


def shot_b2(img, t):
    door = ease_out(seg(t, DOOR_T, DOOR_T + 0.09))
    Y.office(img, t, "day", door=door)
    _sleeping_gintoki(img, t)
    Y.office_fg(img, t, "day")
    _snot_bubble(img, t)
    _office_zzz(img, t)
    ox, oy = Y.DOOR_X, Y.DOOR_FEET_Y
    hx, hy = ox, oy - 26
    sl = 1 - seg(t, DOOR_T + 0.35, DOOR_T + 0.7)
    if sl > 0:
        fx.speed_lines(img, t, hx, hy, (255, 255, 255), count=20, inner=38, seed=5, alpha=sl, thickness=1)
    fx.burst(img, t, DOOR_T, Y.DOOR_BOX[0] + 2, Y.DOOR_BOX[1] + 2, n=10,
             colors=[(210, 200, 180), (160, 150, 130)], speed=(10, 40), gravity=140, life=0.8,
             size=(1, 1), seed=21, spread=(40, 160))
    if t < DOOR_T + 0.3:
        draw_char(img, "otose", ox, oy, "punch", t, p=seg(t, DOOR_T - 0.02, DOOR_T + 0.2), facing=-1)
        vx, vy = ox - 6, oy - 30
    elif t < 7.25:
        draw_char(img, "otose", ox, oy, "shout", t, facing=-1)
        vx, vy = ox - 6, oy - 30
    elif t < WALK0:
        draw_char(img, "otose", ox, oy, "point", t, p=seg(t, 7.25, 7.6), facing=-1)
        vx, vy = ox - 6, oy - 30
    else:
        # stomps out of the doorway to the sofa, puffing her cigarette
        u = seg(t, WALK0, B2_1)
        x, y = lerp(ox, OX3, u), lerp(oy, OY3, u)
        draw_char(img, "otose", x, y, "walk", t, facing=-1, expr="angry")
        vx, vy = x - 7, y - 30
    _vein(img, vx, vy, t, 6.25)
    _cam(img, *_b2_cam(t))
    _shake(img, t, DOOR_T, 0.4, 3, seed=2)
    sfx_text(img, 250, 70, "砰！！", t, DOOR_T, dur=0.75, size=26, angle=10)


def _kick_p(t):
    """Otose 'kick' progress: chamber, trembling hold, snap, follow-through."""
    if t < CH0:
        return 0.0
    if t < CH1:
        return 0.34 * ease_out(seg(t, CH0, CH1))
    if t < SNAP:
        return 0.34
    if t < IMPACT:
        return lerp(0.36, 0.5, seg(t, SNAP, IMPACT))
    return lerp(0.5, 1.0, ease_out(seg(t, IMPACT, IMPACT + 0.5)))


def shot_b3(img, t):
    Y.office(img, t, "day")
    # ---- Gintoki
    kicked = t >= IMPACT
    if not kicked:
        talking = 8.62 <= t < 9.40
        _sleeping_gintoki(img, t, talking=talking)
    Y.office_fg(img, t, "day")
    if not kicked:
        _snot_bubble(img, t, pop_t=BUBBLE_POP)
        if t < BUBBLE_POP:
            _office_zzz(img, t)
    # ---- the room darkens around Otose's killing intent
    dark = ease_out(seg(t, VEIN2_T, VEIN2_T + 0.3)) * (1 - seg(t, IMPACT, IMPACT + 0.12))
    if dark > 0:
        fx.grade(img, mul=(1 - 0.5 * dark, 1 - 0.56 * dark, 1 - 0.34 * dark))
    # ---- Otose
    if t < VEIN2_T:
        draw_char(img, "otose", OX3, OY3, "smoke", t - B3_0 + 0.9, facing=-1)
        ex, ey = OX3, OY3
    elif t < CH0:
        _aura(img, "otose", OX3, OY3, "idle", t, facing=-1, expr="angry")
        draw_char(img, "otose", OX3, OY3, "idle", t, facing=-1, expr="angry")
        ex, ey = OX3, OY3
    else:
        p = _kick_p(t)
        x = lerp(OX3, OX3_KICK, ease_out(seg(t, CH0, CH1)))       # steps in
        if CH1 <= t < SNAP:
            x += 1 if step_frame(t, 24) % 2 else 0                  # trembling power-up
        if t < IMPACT + 0.2:
            _aura(img, "otose", x, OY3, "kick", t, p=p, facing=-1)
        draw_char(img, "otose", x, OY3, "kick", t, p=p, facing=-1)
        ex, ey = x, OY3
    # anticipation: evil glint in Otose's eye before the kick
    fx.sparkle(img, int(ex) - 5, ey - 21, t, GLINT_T, size=6, color=(255, 255, 255))
    _vein(img, ex - 7, ey - 30, t, B3_0 - 0.1)
    _vein(img, ex + 6, ey - 34, t, VEIN2_T, big=True)
    # ---- impact + flight
    if IMPACT <= t < IMPACT + 0.12:
        fx.comic_burst(img, GX + 14, GY - 8, 16, 7, spikes=10, color=(255, 240, 120), rot=t * 3)
    if kicked:
        # the Jump magazine pops off and tumbles out of frame (it comes back in D)
        q = seg(t, IMPACT, IMPACT + 0.5)
        if q < 1:
            mx, my = arc((GX - 8, GY - 14), (250, 10), q, 40)
            _mag_flat(img, mx, my, int(t * 900) % 360)
        p = seg(t, IMPACT, CRASH)
        if p < 1:
            def pos(pp):
                x, y = arc((GX, GY - 4), (IWIN_C[0], IWIN_C[1] + 10), ease_in(pp) * 0.4 + pp * 0.6, 14)
                return x, y, lerp(1.0, 0.45, ease_in(pp))
            x, y, s = pos(p)
            tf = t - IMPACT + 0.125                 # 'fly' spin phase: horizontal at contact
            trail = []
            for back in (0.1, 0.2):
                if p - back > 0:
                    tx, ty, ts = pos(p - back)
                    trail.append((tx, ty, ts, tf - back * 0.4))
            _flyer(img, x, y, tf, s, trail, facing=1)
    if t >= CRASH:
        _crack(img, IWIN_C[0] - 2, IWIN_C[1] - 4, 11, seed=1)
        _glass_burst(img, t, CRASH, IWIN_C[0], IWIN_C[1] - 4, seed=7, n=22)
    # ---- camera
    cam = _cam(img, *_b3_cam(t))
    if IMPACT + 0.05 <= t < CRASH:
        fx.motion_lines(img, t, color=(255, 255, 255), count=14, direction=1, seed=4,
                        y0=20, y1=160, speed=1400, length=(30, 80))
    if IMPACT <= t < IMPACT + 0.07:
        fx.impact_frame(img, color_hi=(255, 250, 235), color_lo=(24, 16, 40))
    elif IMPACT + 0.07 <= t < IMPACT + 0.2:
        fx.flash(img, 0.6 * (1 - seg(t, IMPACT + 0.07, IMPACT + 0.2)))
    _shake(img, t, IMPACT, 0.45, 6, seed=4)
    _shake(img, t, CRASH, 0.25, 3, seed=6)
    sx, sy = _scr(cam, GX + 14, GY - 8)
    sfx_text(img, sx + 6, sy - 36, "咚！！", t, IMPACT, dur=0.42, size=32, angle=-12)
    wx, wy = _scr(cam, IWIN_C[0], IWIN[1])
    sfx_text(img, wx + 62, wy + 26, "哐啷！", t, CRASH, dur=0.6, size=24, color=(200, 236, 255), angle=8)


# ------------------------------------------------------------------ shot C/D: street aftermath
def _broken_window_ext(img, t):
    _crack(img, WINC_CX, WINC_CY, 9, seed=3, hole_color=(36, 30, 40))


def _bump(img, x, y, t):
    """Swollen bump on Gintoki's head; x,y = top of hair."""
    paste(img, BUMP, x, y + 2, anchor="bottom")


def _gossips(img, t, react_t=LAND):
    """Two townswomen chatting; they jump at the landing, then whisper about it."""
    for i, (x, v, f0) in enumerate(GOSSIP):
        if t < react_t:
            draw_char(img, "townswoman", x, BACK, "gossip", t + i * 0.4, facing=f0, variant=v)
        elif t < react_t + 0.7:
            u = seg(t, react_t, react_t + 0.35)
            hop = int(round(5 * math.sin(math.pi * u))) if u < 1 else 0
            draw_char(img, "townswoman", x, BACK - hop, "shock", t, p=seg(t, react_t, react_t + 0.7),
                      facing=1, variant=v)
        else:
            draw_char(img, "townswoman", x, BACK, "gossip", t + i * 0.4, facing=1 if i == 0 else -1,
                      variant=v)


def _pig_c1(img, t):
    """Pig amanto strolls in, freezes at the crash, then bursts out laughing."""
    x0, v = 262, -24
    if t < LAND:
        draw_char(img, "amanto_pig", _walk_x(t, C0, x0, v), BACK + 1, "walk", t, facing=-1)
        return None
    x = _walk_x(LAND, C0, x0, v)
    if t < LAND + 0.22:
        draw_char(img, "amanto_pig", x, BACK + 1, "shock", t, p=seg(t, LAND, LAND + 0.22), facing=-1)
    else:
        draw_char(img, "amanto_pig", x, BACK + 1, "laugh", t, facing=-1)
    return x


def _lying_gintoki(img, t, x=LAND_X, y=LAND_Y):
    bb, ax, ay = _bbox("gintoki", "lie", t, facing=-1)
    draw_char(img, "gintoki", x, y, "lie", t, facing=-1)
    if bb:
        # head is at the right end of the lying sprite
        paste(img, rotate_nearest(BUMP, -90), x - ax + bb[2], y - ay + (bb[1] + bb[3]) // 2 - 5)


def _road_cracks(img, t):
    if t < LAND:
        return
    d = ImageDraw.Draw(img)
    c = (70, 66, 74)
    for (x0, y0, x1, y1) in ((-14, 1, -22, 4), (-14, 1, -6, 3), (8, 1, 18, 4), (8, 1, 14, -1), (18, 4, 24, 5)):
        d.line([(LAND_X + x0, LAND_Y + y0), (LAND_X + x1, LAND_Y + y1)], fill=c)


def _c1_cam(t):
    u = ease_in_out(seg(t, C0 + 0.05, LAND))
    k = lerp(2.4, 1.4, u)
    cx = lerp(84, 150, u)
    cy = lerp(64, 122, u)
    k += 0.1 * ease_out(seg(t, LAND, C1_1))
    return k, cx, cy


def shot_c1(img, t):
    K.street(img, CAMC, t, "day", dy=0)
    _broken_window_ext(img, t)
    _gossips(img, t)
    pig_x = _pig_c1(img, t)
    _road_cracks(img, t)
    _glass_burst(img, t, C0, WINC_CX + 4, WINC_CY, seed=11, spread=(-80, 70), speed=(40, 150), n=34)
    if t < LAND:
        p = seg(t, C0, LAND)

        def pos(pp):
            x, y = arc((WINC_CX, WINC_CY + 6), (LAND_X, LAND_Y - 4), pp, 26)
            return x, y, lerp(0.7, 1.0, pp)
        x, y, s = pos(p)
        trail = []
        for back in (0.08, 0.16):
            if p - back > 0:
                tx, ty, ts = pos(p - back)
                trail.append((tx, ty, ts, t - back * 0.5))
        _flyer(img, x, y, t, s, trail, facing=1)
    else:
        b = seg(t, LAND, LAND + 0.28)
        bounce = -int(round(6 * math.sin(math.pi * b))) if b < 1 else 0
        _lying_gintoki(img, t, y=LAND_Y + bounce)
        fx.smoke_puff(img, t, LAND, LAND_X, LAND_Y - 2, size=16, seed=5, color=(200, 196, 190), life=0.9)
        fx.burst(img, t, LAND, LAND_X, LAND_Y - 3, n=14, colors=[(150, 146, 150), (110, 104, 110)],
                 speed=(30, 80), gravity=240, life=0.6, size=(1, 2), seed=9, spread=(190, 350))
        if t < LAND + 0.1:
            fx.comic_burst(img, LAND_X, LAND_Y - 6, 22, 10, spikes=12, color=(255, 236, 140), rot=0.3)
    cam = _cam(img, *_c1_cam(t))
    _shake(img, t, LAND, 0.4, 5, seed=8)
    lx, ly = _scr(cam, LAND_X, LAND_Y - 20)
    sfx_text(img, lx + 22, ly - 16, "咚！", t, LAND, dur=0.6, size=28, angle=-10)
    if pig_x is not None and t >= LAND + 0.22:
        px, py = _scr(cam, pig_x, BACK - 34)
        sfx_text(img, px - 6, py - 22, "噗哈哈", t, LAND + 0.22, dur=0.6, size=16,
                 color=(255, 200, 210), angle=6)


def _otose_balcony(img, t, t0):
    """Otose pops up behind the balcony railing (cropped at the rail top)."""
    h = ease_out_back(clamp((t - t0) / 0.25))
    x = WINC_CX + 4
    y = K.STREET_BALCONY_Y + int((1 - h) * 22)
    if t < 13.45:
        spr, ax, ay = render_sprite("otose", "shout", t, facing=1)
    else:
        spr, ax, ay = render_sprite("otose", "point", t, p=seg(t, 13.45, 13.7), facing=1, expr="shout")
    cut = RAIL_TOP - (y - ay)                       # rows above the railing top
    if cut > 0:
        part = spr.crop((0, 0, spr.width, min(spr.height, cut)))
        img.paste(part, (int(x - ax), int(y - ay)), part)
    _vein(img, x + 6, y - 31, t, t0 + 0.2, big=True)
    return x, y


def shot_c2(img, t):
    K.street(img, CAMC, t, "day", dy=0)
    _broken_window_ext(img, t)
    ox, oy = _otose_balcony(img, t, C1_1)
    # cigarette smoke curling up from the angry landlady
    for i in range(3):
        u = ((t * 0.9 + i / 3.0) % 1.0)
        sx = ox + 9 + wave(t + i, 0.9, 2) + u * 4
        sy = oy - 26 - u * 20
        r = 1 + int(u * 2)
        overlay_rect(img, sx - r, sy - r, 2 * r, 2 * r, (230, 230, 236), 0.55 * (1 - u))
    k = lerp(2.0, 2.1, ease_in_out(seg(t, C1_1, C2_1)))
    cam = _cam(img, k, 120, 79)            # Otose + the 万事屋银酱 sign, both above the dialogue box
    hx, hy = _scr(cam, ox, oy - 26)
    sl = 1 - seg(t, C1_1 + 0.45, C1_1 + 0.8)
    if sl > 0:
        fx.speed_lines(img, t, hx, hy, (255, 255, 255), count=16, inner=52, seed=15, alpha=sl, thickness=1)
    _shake(img, t, C1_1 + 0.1, 0.35, 2, seed=16)
    name_card(img, t, 12.68, C2_1 - 12.68, "otose", "登势婆婆", "楼下酒馆老板娘（房东）")


def _gintoki_d(img, t):
    """Getting up + deadpan nose-pick; returns head-top point for the bump / magazine."""
    if t < GETUP:
        tw = 1 if step_frame(t, 10) % 3 == 0 else 0
        _lying_gintoki(img, t, x=LAND_X + tw)
        return None
    if t < GETUP + 0.25:
        u = seg(t, GETUP, GETUP + 0.25)
        y = LAND_Y - int(round(12 * math.sin(math.pi * u)))
        pose, p, kw = "jump", None, {}
    elif t < GETUP + 0.5:
        y, pose, p, kw = LAND_Y, "land", seg(t, GETUP + 0.25, GETUP + 0.5), {}
    elif t < FLICK + 0.25:
        y, pose, p, kw = LAND_Y, "nosepick", None, {}
    else:
        blink = (t - FLICK) % 1.7 < 0.1
        y, pose, p, kw = LAND_Y, "idle", None, {"expr": "blink" if blink else "normal"}
    draw_char(img, "gintoki", LAND_X, y, pose, t, p=p, facing=1, **kw)
    bb, ax, ay = _bbox("gintoki", pose, t, p=p, facing=1, **kw)
    top = (LAND_X - ax + (bb[0] + bb[2]) // 2, y - ay + bb[1]) if bb else (LAND_X, y - 34)
    _bump(img, top[0] - 2, top[1], t)
    return top


def _pig_d(img, t):
    """Keeps laughing at Gintoki until the booger hits him, then flees."""
    x, y = PIG_X_D, BACK + 1
    if t < PIG_HIT:
        draw_char(img, "amanto_pig", x, y, "laugh", t, facing=-1)
        return x, y, "laugh"
    if t < PIG_RUN:
        draw_char(img, "amanto_pig", x, y, "shock", t, p=seg(t, PIG_HIT, PIG_HIT + 0.2), facing=-1)
        # the booger stuck on his snout
        rect(img, x - 6, y - 21, 2, 2, BOOGER_C)
        return x, y, "shock"
    x = x + 110 * (t - PIG_RUN) ** 1.2
    if x < W + 40:
        draw_char(img, "amanto_pig", x, y, "run_away", t, facing=1)
        fx.smoke_puff(img, t, PIG_RUN, PIG_X_D - 4, y - 2, size=8, seed=31, color=(210, 206, 200), life=0.5)
    return x, y, "run"


def _d_cam(t):
    u = seg(t, D0, D1)
    k, cx, cy = lerp(2.0, 2.1, ease_in_out(u)), lerp(158, 164, u), 136.0
    u2 = ease_in_out(seg(t, MAG_LAND + 0.2, D1))   # deadpan push-in for the crow beat
    return lerp(k, 2.6, u2), lerp(cx, 200, u2), lerp(cy, 128, u2)


def shot_d(img, t):
    K.street(img, CAMC, t, "day", dy=0)
    _gossips(img, t, react_t=-10)
    _road_cracks(img, t)
    pig = _pig_d(img, t)
    fx.smoke_puff(img, t, GETUP + 0.25, LAND_X, LAND_Y - 1, size=9, seed=12, color=(210, 206, 200), life=0.5)
    top = _gintoki_d(img, t)
    # booger flick -> straight onto the laughing pig's snout
    if top and FLICK <= t < PIG_HIT:
        q = seg(t, FLICK, PIG_HIT)
        bx, by = arc((top[0] + 5, top[1] + 12), (PIG_X_D - 5, BACK - 20), q, 14)
        rect(img, int(bx), int(by), 2, 2, BOOGER_C)
    # the Jump flutters down onto his head
    if top:
        if MAG_LAND - 0.45 <= t < MAG_LAND:
            q = seg(t, MAG_LAND - 0.45, MAG_LAND)
            mx = top[0] + 1 + wave(t, 2.2, 8) * (1 - q)
            my = lerp(top[1] - 58, top[1] - 5, ease_in(q))
            _mag_flat(img, mx, my, int(wave(t, 2.2, 40)) + 90)
        elif t >= MAG_LAND:
            sq = 1 if t < MAG_LAND + 0.08 else 0
            paste(img, MAG_TENT, top[0] + 1, top[1] + 7 + sq, anchor="bottom")
    # awkward crow crossing the sky
    crow = None
    if t >= CROW_T:
        q = (t - CROW_T) / 1.25
        crow = (lerp(272, 110, q), 94 + wave(t, 1.2, 2.5))
        paste(img, CROW[step_frame(t, 7, 2)], crow[0], crow[1], anchor="center")
    cam = _cam(img, *_d_cam(t))
    if top:
        hx, hy = _scr(cam, top[0], top[1])
        sfx_text(img, hx + 30, hy - 8, "啪", t, MAG_LAND, dur=0.6, size=22, color=(255, 236, 120), angle=-6)
        nx, ny = _scr(cam, top[0] + 6, top[1] + 12)
        sfx_text(img, nx + 12, ny - 12, "弹", t, FLICK, dur=0.4, size=12, color=(200, 240, 160), angle=10,
                 shake=0)
    if t < D0 + 0.9:
        px, py = _scr(cam, PIG_X_D, BACK - 34)
        sfx_text(img, px - 10, py - 30, "噗哈哈哈", t, D0, dur=0.9, size=16, color=(255, 200, 210), angle=6)
    if pig[2] == "shock":
        px, py = _scr(cam, pig[0], pig[1] - 34)
        sfx_text(img, px + 4, py - 6, "！？", t, PIG_HIT, dur=PIG_RUN - PIG_HIT + 0.05, size=20,
                 color=(255, 255, 255), angle=8)
    if crow and t >= CROW_T + 0.15:
        cx_, cy_ = _scr(cam, crow[0], crow[1])
        draw_text(img, cx_ - 8, cy_ + 12, "阿～呆～", (240, 240, 250), size=16, outline=INK)
    _shake(img, t, MAG_LAND, 0.12, 1, seed=13)


# ------------------------------------------------------------------ scene
class Yorozuya(Scene):
    id = "s01"
    title = "万事屋阿银"
    duration = D1
    music = [(0.0, "yorozuya"), (MAG_LAND + 0.1, None)]   # music drops out for the crow beat
    music_vol = 0.5
    subs = [
        (6.22, 8.34, "otose", "银时！三个月的房租呢！"),
        (8.62, 10.62, "gintoki", "老太婆，下个月……一定。"),
        (12.45, 14.55, "otose", "没钱交房租就去干活！"),
        (15.25, 17.70, "gintoki", "……今天的歌舞伎町，也很和平呢。"),
    ]

    def render(self, img, t):
        if t < A1:
            shot_a(img, t)
        elif t < B1_1:
            shot_b1(img, t)
        elif t < B2_1:
            shot_b2(img, t)
        elif t < B3_1:
            shot_b3(img, t)
        elif t < C1_1:
            shot_c1(img, t)
        elif t < C2_1:
            shot_c2(img, t)
        else:
            shot_d(img, t)

    def cues(self):
        return [
            Cue(0.0, "crowd", vol=0.3, dur=A1),
            Cue(1.50, "pop", vol=0.5),
            Cue(1.75, "pop", vol=0.5, pitch=1.15),
            Cue(2.95, "whoosh", vol=0.7),
            Cue(4.30, "whoosh", vol=0.4, pitch=1.3),
            Cue(STOMPS[0], "thud", vol=0.4),
            Cue(STOMPS[1], "thud", vol=0.5),
            Cue(STOMPS[2], "thud", vol=0.6),
            Cue(DOOR_T, "door_bang"),
            Cue(6.25, "vein", vol=0.7),
            Cue(WALK0, "footsteps", vol=0.5, dur=WALK1 - WALK0),
            Cue(BUBBLE_POP, "pop", vol=0.7, pitch=0.9),
            Cue(VEIN2_T, "vein", vol=0.8),
            Cue(IMPACT - 1.5, "aura", vol=0.55),       # 1.5 s swell that peaks on the kick
            Cue(GLINT_T, "sparkle", vol=0.6),
            Cue(SNAP - 0.1, "whoosh", vol=0.75),      # whoosh peaks ~0.2 s in -> on contact
            Cue(IMPACT, "kick"),
            Cue(IMPACT, "impact", vol=0.6),
            Cue(IMPACT + 0.04, "fly_away", vol=0.6),
            Cue(CRASH, "glass"),
            Cue(C0, "crowd", vol=0.3, dur=D1 - C0),
            Cue(C0 + 0.02, "glass", vol=0.45, pitch=1.2),
            Cue(C0 + 0.05, "fall_whistle", vol=0.55),
            Cue(LAND, "thud"),
            Cue(LAND, "impact", vol=0.5),
            Cue(LAND + 0.1, "shock", vol=0.4),
            Cue(C1_1, "vein", vol=0.6, pitch=0.9),
            Cue(GETUP + 0.25, "land", vol=0.6),
            Cue(FLICK, "pop", vol=0.6, pitch=1.3),
            Cue(PIG_HIT, "squeak", vol=0.6),
            Cue(PIG_HIT + 0.02, "shock", vol=0.5),
            Cue(PIG_RUN, "dash", vol=0.5),
            Cue(MAG_LAND, "slap", vol=0.7),
            Cue(CROW_T, "crow", vol=0.8),
        ]


SCENE = Yorozuya()
