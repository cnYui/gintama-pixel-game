"""s00 「开场」 Prologue (17.9 s) — music [(0,'prologue'), (12,'title')]

SHOT LIST (scene-local seconds)
 1  0.00- 4.10  天降  Deep space / milky way, full moon. The amanto MOTHERSHIP glides in and
                eclipses the moon; cruisers + saucers follow. Camera DESCENDS with the fleet
                (tall-sky tilt: stars -> cloud layer -> night horizon) until old Edo (castle,
                pagoda, watch-tower, lit shoji windows, NO Terminal yet) rises into frame.
                Saucers settle over the roofs, searchlight beams sweep the town.
                Narration 0.5-4.0 「二十年前，自称『天人』的外星人从天而降。」
 2a 4.10- 6.10  攘夷  Sunset battlefield (huge striped sun, smoke columns, nobori banners,
                distant armies clashing). Explosion bang on the cut; ships fire lasers
                (4.30 / 4.85 / 5.60) -> ground explosions. Tracking shot: samurai led by
                Shiroyasha charge right, Harusame/pig/cat amanto charge left; 5.30 clash,
                5.18 smash zoom (1.8x, 集中線) onto the duel, 5.48 Shiroyasha's slash
                (2-frame impact frame) launches a pirate spinning into the sky, the other
                amanto flinch; the pirate becomes a twinkling star (5.90).
 2b 6.10- 8.20  Four heroes silhouetted on a ridge against the giant sun (Sakamoto,
                Katsura, Shiroyasha, Takasugi) with rim light, torn banner, crows, embers;
                slow push-in (zoom 1.2->1.75), letterbox; they draw one by one
                (7.02 Sakamoto's pistol, 7.14 Katsura, 7.26 Takasugi drops his kiseru for
                his blade, 7.40 Shiroyasha) — each with a steel flash + 'shing'; red eye glint.
                Narration 4.3-7.9 「武士们奋起抵抗，史称『攘夷战争』。」
 3a 8.20- 9.90  Rain, lightning, 2x close-up. Field of swords + a fallen kabuto; a katana tumbles down
                in slow motion and stabs into a puddle at 9.15 (impact frame, lightning
                flash, splash, ripples, wobble), blade glint 9.5.
 3b 9.90-12.00  Rain at night: the 「废刀令」 notice board (lantern, pile of confiscated
                swords); the swordless samurai (Shiroyasha) stands under it, looks up,
                lowers his head, 11.1 turns his back on it and walks off. Slow push-in, 10.5 temple gong, fade to black 11.35-11.84;
                11.84-12.00 the 「银魂」 logo rushes at the camera over black.
                Narration 8.3-11.9 「幕府投降，废刀令颁布。武士的时代，结束了……」
 4 12.00-17.90  TITLE. 12.00 white flash + title_hit: 「银魂」 brush logo lands
                (speed lines, shockwave rings, sakura burst, shake), rotating sunburst,
                ribbon 「GINTAMA · 像素剧场」 slides in 12.30, sparkles. Day Edo skyline
                with the Terminal + flying ships, slow pan. 13.10+ the Yorozuya pop up
                onto the roof ridge: Shinpachi, Kagura (parasol), Gintoki (bokuto on
                shoulder), Sadaharu (thud 14.05, bark). GAG: 14.30 camera pushes in on
                Gintoki's deadpan nose-pick (「抠…抠…」) -> 15.05 flick, hard cut to the
                wide, booger arcs onto 「魂」 (15.38 splat, logo flinches) -> awkward
                silence, crow -> 15.85 snap zoom + 集中線: Shinpachi 「喂！」 + bubble
                「往标题上弹鼻屎？！」 while Gintoki keeps picking -> 17.05 he flicks the
                next one onto Shinpachi's glasses (「啪！」). Fade out.
"""
import math

from PIL import Image, ImageDraw

from engine.core import (Scene, Cue, W, H, seg, lerp, ease_in, ease_out, ease_in_out,
                         wave, step_frame, rng, arc)
from engine.gfx import INK, rect, overlay_rect, shade, mix, tint, pset
from engine import fx
from engine.text import sfx_text, speech_bubble
from chars import draw_char, render_sprite
from bg import common as C, edo as E

from scenes import _s00_art as A

T2, T2B, T3, T3B, T4 = 4.1, 6.1, 8.2, 9.9, 12.0
LB = 16                      # letterbox bar height for the dramatic shots


# ============================================================ shot 1: the fleet descends
def _alt(t):
    return 420.0 * (1 - ease_in_out(seg(t, 0.4, 3.3)))


def _mother(t):
    if t < 1.9:
        k = ease_out(seg(t, 0.3, 1.9))
        x, y = lerp(540, 262, k), lerp(-44, 56, k)
    else:
        k = ease_in_out(seg(t, 1.9, 3.3))
        x, y = lerp(262, 204, k), lerp(56, 28, k)
    return x + wave(t, 0.25, 2), y + wave(t, 0.4, 1.5)


_SAUCERS = (  # (t0, (x0, y0), (x1, y1)) : dive from above and hover over the town
    (1.9, (340, -30), (318, 112)),
    (2.2, (40, -30), (84, 104)),
    (2.5, (230, -30), (262, 124)),
    (2.75, (130, -30), (150, 118)),
)


def shot_descent(img, t):
    alt = _alt(t)
    pan = t * 6.0
    A.space_sky(img, alt)
    A.twinkles(img, t, alt)
    C.big_moon(img, 292, -146 + alt * 0.5, r=28)
    # far cloud deck we descend through
    C.clouds(img, t, pan, "night", seed=11, count=7, y0=int(-60 + alt * 0.8), y1=int(10 + alt * 0.8))
    # old Edo rising from below
    if alt < 140:
        A.edo_layers(img, alt, "night", pan)
    # fleet (cruisers behind, then the mothership)
    mx, my = _mother(t)
    for (dt, ox, oy, hz, fc) in ((0.25, -150, 44, 0.45, -1), (0.5, 120, 66, 0.25, -1), (0.1, -40, -26, 0.6, -1)):
        cx, cy = _mother(max(0.0, t - dt))
        E.ship(img, cx + ox, cy + oy, "cruiser", t + dt, facing=fc, tod="night", haze=hz)
    E.ship(img, mx, my, "mothership", t, tod="night", haze=0.0)
    # searchlight beams (after the fleet has arrived)
    if t > 2.85:
        on = seg(t, 2.85, 3.05)
        flick = 0.6 if (2.9 < t < 2.95) else 1.0
        for i, (off, col) in enumerate(((-26, (150, 220, 255)), (28, (255, 130, 190)))):
            tx = mx + off + math.sin(t * 1.1 + i * 2.3) * 70
            A.beam(img, mx + off * 0.6, my + 26, tx, 190, 2, 14, col, 0.16 * on * flick)
    # saucers diving then hovering
    for i, (t0, p0, p1) in enumerate(_SAUCERS):
        if t < t0:
            continue
        k = ease_out(seg(t, t0, t0 + 0.9))
        x = lerp(p0[0], p1[0], k) + wave(t, 0.5, 3, i * 0.3) * k
        y = lerp(p0[1], p1[1], k) + wave(t, 0.7, 2, i * 0.5) * k
        if k < 0.9:        # descent streak
            d = ImageDraw.Draw(img)
            d.line([(x, y - 4), (x - (p1[0] - p0[0]) * 0.08, y - 26 * (1 - k))], fill=(120, 180, 220))
        E.ship(img, x, y, "saucer", t + i, tod="night", haze=0.1)
    # near clouds whooshing past the camera mid-descent
    C.clouds(img, t * 3, pan * 2, "night", seed=12, count=4, y0=int(-120 + alt * 1.3), y1=int(-60 + alt * 1.3))
    # big saucers zooming past the lens (speed)
    for (t0, x0, x1, y0, y1) in ((1.05, 420, -80, 20, 150), (1.95, -70, 440, 150, 40)):
        if t0 <= t < t0 + 0.55:
            k = seg(t, t0, t0 + 0.55)
            E.ship(img, lerp(x0, x1, k), lerp(y0, y1, k), "saucer", t, scale=2, tod="night",
                   facing=1 if x1 > x0 else -1)
    A.vignette(img)


# ============================================================ shot 2a: sunset battle
GROUND2 = 182           # feet line in the battle shot
Z2_IN0, Z2_IN1 = T2 + 1.08, T2 + 1.20      # smash zoom onto the duel
Z2_OUT0, Z2_OUT1 = T2 + 1.47, T2 + 1.72    # release as the pirate is launched
TWINKLE = 1.80                             # (shot-local) the pirate becomes a star


def _battle_zoom(t):
    if t < Z2_IN0:
        return 1.0
    if t < Z2_IN1:
        return lerp(1.0, 1.8, ease_out(seg(t, Z2_IN0, Z2_IN1)))
    if t < Z2_OUT0:
        return lerp(1.8, 1.92, seg(t, Z2_IN1, Z2_OUT0))
    return lerp(1.92, 1.0, ease_in_out(seg(t, Z2_OUT0, Z2_OUT1)))


def _laser(img, t, t0, p0, p1, col=(255, 90, 150)):
    if not (t0 <= t < t0 + 0.16):
        return
    k = seg(t, t0, t0 + 0.05)
    x1 = lerp(p0[0], p1[0], k)
    y1 = lerp(p0[1], p1[1], k)
    d = ImageDraw.Draw(img)
    d.line([p0, (x1, y1)], fill=col, width=4)
    d.line([p0, (x1, y1)], fill=(255, 240, 250), width=2)
    d.ellipse([p0[0] - 4, p0[1] - 4, p0[0] + 4, p0[1] + 4], fill=(255, 230, 240))


def _distant_armies(img, t, u, cam):
    d = ImageDraw.Draw(img)
    for i in range(90):
        r = rng("army", i)
        side = i % 2
        y = 151 + r.randint(0, 6)
        if side == 0:
            x = 10 + r.uniform(0, 190) + 26 * u
            col = (60, 32, 44)
        else:
            x = 190 + r.uniform(0, 200) - 26 * u
            col = (46, 40, 60)
        x -= cam * 0.35
        melee = 170 - cam * 0.35 < x < 230 - cam * 0.35
        if melee:
            x += math.sin(t * 9 + i) * 2
        bob = 1 if (step_frame(t, 8) + i) % 2 else 0
        d.line([(x, y - 3 - bob), (x, y)], fill=col)
        d.point((x, y - 4 - bob), fill=col)
        if r.random() < 0.5:
            d.line([(x + (1 if side == 0 else -1), y - 2 - bob), (x + (3 if side == 0 else -3), y - 7 - bob)],
                   fill=shade(col, 1.25))
        if melee and (int(t * 12) + i) % 23 == 0:
            d.point([(x + 2, y - 5), (x + 3, y - 6)], fill=(255, 240, 150))


_SAMURAI = (  # (cid, kw, x0, speed)
    ("townsman", dict(variant=3), -10, 100),
    ("townsman", dict(variant=0), -40, 100),
    ("townsman", dict(variant=1), -70, 100),
)
_AMANTO = (  # (cid, pose, x0, speed)
    ("amanto_pig", "run", 336, 80),
    ("amanto_cat", "run", 380, 80),
    ("harusame", "charge", 424, 82),
)
_TINT = (140, 60, 70)


def _char(img, cid, x, y, pose, t, p=None, facing=1, tint_amt=0.22, expr=None, **kw):
    spr, ax, ay = render_sprite(cid, pose, t, p, expr, facing, **kw)
    if tint_amt:
        spr = tint(spr, _TINT, tint_amt)
    overlay_rect(img, int(x) - 6, int(y) - 1, 12, 2, (0, 0, 0), 0.3)
    img.paste(spr, (int(round(x - ax)), int(round(y - ay))), spr)


def shot_battle(img, t):
    u = t - T2
    cam = 30 * u
    C.sky(img, "dusk", t, horizon=150, body=False)
    A.sun(img, int(282 - cam * 0.08), 114, 36)
    C.clouds(img, t, cam, "dusk", seed=5, count=5, y0=4, y1=60)
    # ships in the sky
    px_, py_ = 296 - cam * 0.3 + wave(t, 0.3, 3), 50 + wave(t, 0.5, 2)
    E.ship(img, 118 - cam * 0.25 - u * 5, 26, "cruiser", t, facing=-1, tod="dusk", haze=0.45)
    E.ship(img, px_, py_, "pirate", t, facing=-1, tod="dusk", haze=0.15)
    cr_x, cr_y = 70 - cam * 0.3 + u * 8, 70 + wave(t, 0.4, 2)
    E.ship(img, cr_x, cr_y, "cruiser", t + 1, facing=-1, tod="dusk", haze=0.2)
    C.far_mountains(img, cam, "dusk", y=132)
    A.smoke_column(img, t, 58 - cam * 0.5, 150, 110, 1, width=9)
    A.smoke_column(img, t, 250 - cam * 0.5, 152, 90, 2, width=7)
    A.smoke_column(img, t, 352 - cam * 0.5, 150, 120, 3, width=10)
    C.dirt_ground(img, 150, cam, "dusk", grass=0.35)
    overlay_rect(img, 0, 150, W, 66, (120, 40, 60), 0.18)
    _distant_armies(img, t, u, cam)
    # mid banners
    for i, (bx, h) in enumerate(((20, 40), (140, 34), (262, 44), (410, 38))):
        A.nobori(img, bx - cam, 170, t, h=h, seed=i, mark=(170, 30, 40) if i % 2 else (40, 60, 150), torn=i == 2)
    # lasers -> explosions (world coords, drawn behind the runners)
    shots = ((4.30, (px_ - 40, py_ + 10), 250, 168), (4.85, (cr_x - 36, cr_y + 4), 120, 170),
             (5.60, (px_ - 40, py_ + 10), 336, 166))
    for i, (t0, p0, wx, gy) in enumerate(shots):
        _laser(img, t, t0, p0, (wx - cam, gy))
        fx.explosion(img, t, t0 + 0.12, wx - cam, gy - 6, size=22, seed=10 + i)
        fx.smoke_puff(img, t, t0 + 0.4, wx - cam, gy, size=10, seed=20 + i, color=(90, 70, 80), life=1.2)
    fx.explosion(img, t, T2, 64 - cam, 172, size=34, seed=3)
    # --- runners
    for i, (cid, kw, x0, sp) in enumerate(_SAMURAI):
        x = x0 + sp * u - cam
        _char(img, cid, x, GROUND2, "run", t + i * 0.13, weapon=70, weapon_kind="katana", arm_f=130,
              expr="shout", **kw)
    # lead: Shiroyasha
    clash = 1.2
    if u < clash:
        sx = 30 + 125 * u
        _char(img, "shiroyasha", sx - cam, GROUND2, "run", t)
    elif u < clash + 0.45:
        sx = 30 + 125 * clash
        _char(img, "shiroyasha", sx - cam, GROUND2, "attack", t, p=seg(u, clash, clash + 0.45))
    else:
        sx = 30 + 125 * clash
        _char(img, "shiroyasha", sx - cam, GROUND2, "ready", t)
    # amanto side
    flinch = clash + 0.3
    for i, (cid, pose, x0, sp) in enumerate(_AMANTO):
        uu = min(u, flinch)
        x = x0 - sp * uu - cam
        if u < flinch:
            _char(img, cid, x, GROUND2, pose, t + i * 0.17, facing=-1, weapon=60, weapon_kind="katana")
        else:
            _char(img, cid, x, GROUND2, "shock", t, p=seg(u, flinch, flinch + 1), facing=-1)
    # the pirate who meets the blade: launched into the sky -> twinkling star
    hit = clash + 0.18
    ax0 = 300 - 85 * min(u, clash)
    if u < hit:
        _char(img, "harusame", ax0 - cam, GROUND2, "charge", t, facing=-1)
    else:
        k = u - hit
        fx_x = ax0 + 230 * k
        fx_y = GROUND2 - 480 * k + 60 * k * k
        if fx_y > -30:
            _char(img, "harusame", fx_x - cam, fx_y, "fly", t, facing=-1, tint_amt=0.1, rot=int(k * 900) % 360)
    # clash sparks / slash
    tc = T2 + hit
    fx.burst(img, t, tc, 186 - cam + 10, GROUND2 - 16, n=22, colors=((255, 255, 255), (255, 230, 90), (255, 150, 60)),
             speed=(60, 170), gravity=120, life=0.5, seed=7)
    if tc <= t < tc + 0.14:
        fx.slash_arc(img, 186 - cam + 6, GROUND2 - 16, 22, -110, 40, seg(t, tc - 0.04, tc + 0.1) * 1.3, width=4)
    # foreground banner silhouettes + embers
    for i, (bx, h) in enumerate(((-16, 92), (446, 96))):
        A.nobori(img, bx - cam * 1.5, H + 4, t, h=h, seed=i + 5, dark=(34, 16, 26))
    fx.embers(img, t, count=26, seed=2, area=(0, 60, W, H))
    # smash zoom on the duel: push in as the two meet, hold through the slash,
    # release as the pirate is launched
    z = _battle_zoom(t)
    zc = (190 - 30 * (clash + 0.1), GROUND2 - 22)
    A.zoom(img, z, *zc)
    if Z2_IN1 <= t < Z2_OUT0:        # 集中線 while the camera is tight on the duel
        fx.speed_lines(img, t, 192, 120, color=(255, 236, 214), count=34, inner=96, seed=21, alpha=0.8)
    if tc <= t < tc + IMPACT:        # 2-frame impact frame on the decisive slash
        fx.impact_frame(img, color_hi=(255, 244, 228), color_lo=(40, 10, 26), threshold=120)
    else:
        fx.flash(img, 0.35 * (1 - seg(t, tc + IMPACT, tc + 0.25)) if t >= tc else 0)
        A.vignette(img)
    # the launched pirate becomes a twinkling star
    fx.sparkle(img, 238, 12, t, T2 + TWINKLE, size=6, color=(255, 250, 220))
    dx, dy = fx.shake_offset(t, T2, 0.35, 4, seed=1)
    ex, ey = fx.shake_offset(t, tc, 0.3, 4, seed=2)
    fx.shift(img, dx + ex, dy + ey)
    fx.flash(img, 1 - seg(t, T2, T2 + 0.22))


# ============================================================ shot 2b: four heroes
# (cid, x, facing, pose before the draw, pose after, draw time, extra kw after the draw)
# The four stand calmly (Takasugi smoking his kiseru), then draw one after another
# (left -> right, Shiroyasha last) — each with a steel glint and a 'shing'.
_HEROES = (
    ("sakamoto", 126, 1, "idle", "shoot", 7.02, dict(p=0.5)),
    ("katsura", 164, 1, "idle", "ready", 7.14, {}),
    ("takasugi", 256, 1, "smoke", "ready", 7.26, {}),
    ("shiroyasha", 215, 1, "stand", "battle_idle", 7.40, {}),
)
DRAW_FLASH = 0.07
HERO_ZC = (196, 124)


def _ridge(x):
    return 150 + ((x - 192) / 150.0) ** 2 * 30


def _hill(img, t):
    d = ImageDraw.Draw(img)
    pts = [(x, _ridge(x)) for x in range(-4, W + 8, 4)]
    d.polygon(pts + [(W + 8, H), (-4, H)], fill=(24, 12, 24))
    d.line(pts, fill=(64, 26, 40))
    # grass tufts swaying in the wind
    for i in range(70):
        r = rng("tuft", i)
        x = r.uniform(0, W)
        y = _ridge(x)
        h = r.randint(2, 5)
        sw = math.sin(t * 5 + x * 0.1) * 1.5 + 1
        d.line([(x, y), (x + sw, y - h)], fill=(40, 18, 32))


def shot_heroes(img, t):
    u = t - T2B
    C.sky(img, "dusk", t, horizon=160, body=False)
    A.sun(img, 192, 126, 58)
    C.clouds(img, t * 2, 0, "dusk", seed=8, count=4, y0=70, y1=96)
    C.far_mountains(img, 0, "dusk", y=136)
    A.smoke_column(img, t, 60, 150, 90, 7, color=(60, 30, 50), width=8)
    A.smoke_column(img, t, 320, 150, 100, 8, color=(60, 30, 50), width=9)
    A.crows(img, t, T2B, 100, 86, 34, -3, n=3, color=(30, 12, 26), seed=1)
    _hill(img, t)
    A.nobori(img, 112, int(_ridge(112)), t, h=52, seed=3, torn=True, dark=(24, 12, 24))
    glints = []
    for (cid, x, fc, pose0, pose1, td, kw) in _HEROES:
        y = _ridge(x) + 1
        if t < td:
            spr, ax, ay = render_sprite(cid, pose0, t, None, None, fc)
        else:
            kw2 = dict(kw)
            p = kw2.pop("p", None)
            spr, ax, ay = render_sprite(cid, pose1, t, p, None, fc, **kw2)
        sil = A.backlit(spr, dark=(34, 14, 34), amount=0.7, rim=(255, 160, 90), rim_top=(255, 214, 140))
        if td <= t < td + DRAW_FLASH:          # steel flash as the blade leaves the scabbard
            sil = tint(sil, (255, 236, 200), 0.35)
        A.paste_feet(img, sil, ax, ay, x, y)
        if cid == "sakamoto":
            glints.append((x + 17 * fc, y - 16, td, 4))
        elif cid == "shiroyasha":
            glints.append((x + 17 * fc, y - 5, td, 6))
        else:
            glints.append((x + 24 * fc, y - 21, td, 4))
    # Shiroyasha's red eye glint once his blade is out
    sx, sy = 215, _ridge(215) + 1
    if t >= 7.4 and int(t * 6) % 5 != 0:
        ImageDraw.Draw(img).point((sx + 3, sy - 21), fill=(255, 40, 60))
    fx.embers(img, t, count=34, seed=4, area=(0, 70, W, H), colors=((255, 190, 90), (255, 120, 60), (255, 230, 170)))
    k = lerp(1.2, 1.75, ease_out(seg(t, T2B, T3)))
    zc = HERO_ZC
    A.zoom(img, k, *zc)
    for (gx, gy, td, sz) in glints:          # sparkles drawn in screen space (crisp)
        px, py = A.zoom_map(k, zc[0], zc[1], gx, gy)
        fx.sparkle(img, int(px), int(py), t, td, size=sz, color=(255, 255, 230))
    A.vignette(img)
    fx.letterbox(img, 1, LB)


# ============================================================ shot 3a: the sword falls
def _storm_bg():
    img = Image.new("RGB", (W, H))
    arr = C.vgradient(118, W, [(0, (14, 16, 26)), (0.6, (36, 40, 56)), (1.0, (64, 68, 88))], bands=10)
    img.paste(Image.fromarray(arr, "RGB"), (0, 0))
    d = ImageDraw.Draw(img)
    # distant hills
    r = rng("s3hills")
    pts = [(x, 112 + math.sin(x * 0.03) * 4 + math.sin(x * 0.11) * 2) for x in range(0, W + 8, 4)]
    d.polygon(pts + [(W, 130), (0, 130)], fill=(30, 32, 44))
    # mud field
    g = C.vgradient(H - 116, W, [(0, (38, 36, 46)), (1, (22, 20, 28))], bands=8)
    img.paste(Image.fromarray(g, "RGB"), (0, 116))
    # puddles reflecting the sky
    for i in range(14):
        cx, cy = r.uniform(0, W), r.uniform(130, 210)
        rw = r.uniform(8, 30) * (0.5 + (cy - 120) / 90)
        d.ellipse([cx - rw, cy - rw * 0.18, cx + rw, cy + rw * 0.18], fill=(56, 60, 80))
        d.line([(cx - rw * 0.6, cy - 1), (cx + rw * 0.2, cy - 1)], fill=(80, 86, 108))
    # the big puddle where the sword lands (+ a fallen kabuto helmet beside it)
    d.ellipse([164, 162, 250, 176], fill=(58, 62, 84))
    d.line([(174, 165), (222, 165)], fill=(88, 94, 118))
    # fallen kabuto helmet half-sunk in the mud (dome, neck guard, golden kuwagata horns)
    d.polygon([(124, 159), (152, 159), (156, 166), (120, 166)], fill=(38, 38, 50), outline=(18, 16, 26))
    d.line([(123, 162), (153, 162)], fill=(84, 64, 90))
    d.pieslice([127, 146, 149, 168], 180, 360, fill=(54, 52, 66), outline=(18, 16, 26))
    d.arc([130, 149, 146, 165], 200, 250, fill=(96, 98, 118))
    for hx in (131, 135, 139, 143):
        d.point((hx, 153), fill=(90, 92, 110))
    d.line([(138, 152), (131, 139)], fill=(196, 164, 76), width=2)
    d.line([(138, 152), (145, 139)], fill=(150, 124, 58), width=2)
    d.rectangle([136, 151, 140, 155], fill=(196, 164, 76))
    return img


def _bolt(img, t, t0, x0, seed):
    if not (t0 <= t < t0 + 0.12):
        return
    r = rng("bolt", seed)
    d = ImageDraw.Draw(img)
    x, y = x0, 0
    pts = [(x, y)]
    while y < 112:
        y += r.randint(6, 12)
        x += r.randint(-7, 7)
        pts.append((x, y))
    d.line(pts, fill=(230, 236, 255), width=2)
    d.line(pts, fill=(255, 255, 255), width=1)


LAND = 9.15
IMPACT = 0.067                 # impact-frame length (2 frames)
TIP = (206, 169)
Z3, Z3C = 2.0, (206, 138)     # close-up: the whole shot is framed through a 2x zoom


def shot_sword(img, t):
    u = t - T3
    img.paste(A.cached("storm_bg", _storm_bg))
    A.sword_field(img, 96, u * 5)
    # lightning in the distance at the cut and on the impact
    FL2 = LAND + IMPACT
    fl = max(0.0, 1 - seg(t, T3, T3 + 0.3)) * 0.55 + (max(0.0, 1 - seg(t, FL2, FL2 + 0.45)) * 0.7 if t >= FL2 else 0)
    _bolt(img, t, T3, 262, 1)
    _bolt(img, t, LAND + IMPACT, 146, 2)
    fx.rain(img, t, count=60, seed=3, color=(80, 90, 120), speed=220, slant=0.3, length=4)
    # ripples on the landing puddle
    for k in range(3):
        t0 = LAND + k * 0.18
        if t0 <= t < t0 + 0.9:
            q = seg(t, t0, t0 + 0.9)
            rr = 4 + 44 * ease_out(q)
            col = mix((150, 160, 190), (58, 62, 84), q)
            ImageDraw.Draw(img).ellipse([TIP[0] - rr, TIP[1] - 2 - rr * 0.16, TIP[0] + rr, TIP[1] - 2 + rr * 0.16], outline=col)
    # the katana (slow-motion tumble; position = blade centre)
    land_ang = -78
    lr = math.radians(land_ang)
    land_c = (TIP[0] - math.cos(lr) * 29, TIP[1] + math.sin(lr) * 29)
    if t < LAND:
        k = seg(t, T3 + 0.05, LAND)
        ang = lerp(150, land_ang, k ** 0.8)
        cy = lerp(80, land_c[1], k ** 1.5)
        cx = lerp(172, land_c[0], k)
    else:
        dt = t - LAND
        ang = land_ang + 7 * math.sin(dt * 38) * math.exp(-dt * 4.5)
        rad = math.radians(ang)
        cx, cy = TIP[0] - math.cos(rad) * 29, TIP[1] + math.sin(rad) * 29
    rad = math.radians(ang)
    ux, uy = math.cos(rad), -math.sin(rad)
    spr = A.katana_sprite(ang)
    if t < LAND:      # motion streaks behind the falling blade
        d = ImageDraw.Draw(img)
        for j in (-8, -2, 5):
            d.line([(cx + j, cy - 10), (cx + j - 2, cy - 30)], fill=(96, 106, 136))
    img.paste(spr, (int(cx - spr.width / 2), int(cy - spr.height / 2)), spr)
    if t >= LAND:     # mud lip over the buried tip
        d = ImageDraw.Draw(img)
        d.ellipse([TIP[0] - 6, TIP[1] - 4, TIP[0] + 5, TIP[1] + 1], fill=(40, 38, 50))
        d.line([(TIP[0] - 5, TIP[1] - 4), (TIP[0] + 3, TIP[1] - 4)], fill=(88, 94, 118))
        fx.burst(img, t, LAND, TIP[0], TIP[1] - 3, n=30, colors=((170, 180, 210), (90, 80, 86), (220, 228, 250)),
                 speed=(30, 90), gravity=240, life=0.7, size=(1, 2), seed=11, spread=(200, 340))
        fx.sparkle(img, int(cx - ux * 6), int(cy - uy * 6), t, 9.55, size=5)
    A.splashes(img, t, 122, 190, n=24, seed=1)
    A.zoom(img, Z3, *Z3C)
    fx.rain(img, t, count=90, seed=4, color=(130, 142, 180), speed=520, slant=0.3, length=10)
    if LAND <= t < LAND + IMPACT:      # 2-frame anime impact frame, then the lightning flash
        fx.impact_frame(img, color_hi=(255, 255, 255), color_lo=(16, 14, 26), threshold=70)
    else:
        fx.flash(img, fl, (210, 216, 255))
        A.vignette(img)
    dx, dy = fx.shake_offset(t, LAND, 0.3, 3, seed=5)
    fx.shift(img, dx, dy)
    fx.letterbox(img, 1, LB)


# ============================================================ shot 3b: 废刀令
def _street_bg():
    img = Image.new("RGB", (W, H))
    arr = C.vgradient(124, W, [(0, (12, 14, 24)), (0.7, (30, 34, 50)), (1.0, (44, 48, 66))], bands=10)
    img.paste(Image.fromarray(arr, "RGB"), (0, 0))
    d = ImageDraw.Draw(img)
    r = rng("s3broofs")
    # far roofs silhouette with a few dim windows
    x = -10
    while x < W + 20:
        w = r.randint(30, 56)
        top = r.randint(96, 108)
        d.polygon([(x - 4, top + 8), (x + 6, top), (x + w - 6, top), (x + w + 4, top + 8)], fill=(26, 28, 40))
        d.rectangle([x, top + 8, x + w, 124], fill=(30, 32, 44))
        if r.random() < 0.5:
            wx = x + r.randint(6, w - 10)
            d.rectangle([wx, top + 12, wx + 3, top + 15], fill=(120, 96, 70))
        x += w + r.randint(-4, 2)
    # tsuiji wall (plaster + tiled cap) across the square
    d.rectangle([0, 124, W, 150], fill=(70, 72, 90))
    for xx in range(0, W, 42):
        d.rectangle([xx, 124, xx + 2, 150], fill=(54, 56, 72))
    d.rectangle([0, 118, W, 124], fill=(40, 42, 58))
    for xx in range(0, W, 4):
        d.point((xx, 119), fill=(60, 64, 82))
    d.line([(0, 124), (W, 124)], fill=(26, 26, 38))
    d.rectangle([0, 146, W, 150], fill=(56, 58, 74))
    return img


BOARD_X = 158         # where the samurai stands reading the order


def shot_board(img, t):
    u = t - T3B
    img.paste(A.cached("street_bg", _street_bg))
    C.stone_street(img, 150, 0, "storm", h=H - 150)
    overlay_rect(img, 0, 150, W, H - 150, (20, 22, 40), 0.35)
    # board + lantern
    bx, by = 252, 176
    board = A.notice_board()
    img.paste(board, (bx - board.width // 2, by - board.height), board)
    pile = A.sword_pile()
    img.paste(pile, (bx - 36, by - pile.height + 3), pile)
    # street lantern behind the samurai (rim-lights him from the left)
    lx = 118
    d = ImageDraw.Draw(img)
    d.line([(lx, 176), (lx, 92)], fill=(40, 30, 30), width=2)
    d.line([(lx, 93), (lx + 10, 93)], fill=(40, 30, 30), width=2)
    flick = 0.85 + 0.15 * math.sin(t * 23) * math.sin(t * 7)
    C.add_sprite(img, C.glow_sprite(38, (255, 170, 90), round(flick, 1)), lx + 10 - 38, 108 - 38)
    C.lantern(img, lx + 10, 94, t, color=C.RED, tod="storm", glow=0.9, size=2, swing=2.0)
    # warm reflection of the lantern on the wet stones
    for k in range(6):
        yy = 180 + k * 5
        wv = int(math.sin(t * 6 + k) * 2)
        overlay_rect(img, lx + 6 + wv, yy, 8 - k, 2, (255, 170, 90), 0.4 - k * 0.05)
    # the samurai — swordless now — stands right under the order, looks up at it,
    # lowers his head, then turns his back on it and walks off into the rain
    turn = 11.1
    if t < turn:
        x, fc, pose = BOARD_X, 1, "stand"
        hd = -1 if t < 10.75 else 1
    else:
        x, fc, pose, hd = BOARD_X - 26 * (t - turn), -1, "walk", 1
    spr, ax, ay = render_sprite("shiroyasha", pose, t, None, "sad", fc, weapon=None, sheathed=False,
                                head_dy=hd)
    sil = A.backlit(spr, dark=(26, 28, 50), amount=0.6, rim=(255, 176, 110), rim_top=(200, 166, 150),
                    sides=(-1,))
    overlay_rect(img, int(x) - 7, 175, 14, 2, (0, 0, 0), 0.35)
    A.paste_feet(img, sil, ax, ay, x, 176)
    fx.rain(img, t, count=70, seed=7, color=(100, 110, 150), speed=300, slant=0.28, length=5)
    A.splashes(img, t, 152, 200, n=30, seed=2)
    fx.flash(img, 0.5 * (1 - seg(t, T3B + 0.08, T3B + 0.4)) if t >= T3B + 0.08 else 0, (200, 210, 255))
    k = lerp(1.45, 1.62, ease_in_out(seg(t, T3B, T4)))
    A.zoom(img, k, 222, 130)
    fx.rain(img, t, count=60, seed=8, color=(150, 160, 200), speed=560, slant=0.28, length=11)
    A.vignette(img)
    fx.fade(img, ease_in(seg(t, 11.35, 11.84)))
    fx.letterbox(img, 1, LB)




# ============================================================ shot 4: TITLE
LOGO_C = (192, 74)
ROOF_Y = 202
_CAST = (  # (cid, x, t_jump, final pose)
    ("shinpachi", 144, 13.10, "idle"),
    ("kagura", 240, 13.22, "umbrella_open"),
    ("gintoki", 192, 13.36, "shoulder"),
)
JUMP_DUR = 0.42
SADA_T, SADA_X = 13.55, 306          # heavy leap, THUD at SADA_T + 0.5
GLINT_T = 13.85                      # Shinpachi's glasses glint
BARK_T = 14.12
PICK0 = 14.30                        # camera pushes in on Gintoki: deadpan nose-pick
FLICK = 15.05                        # the flick (hard cut back to the wide)
SPLAT = 15.38                        # booger lands on 「魂」
CROW_T = 15.48                       # awkward silence
TSUKKOMI = 15.85                     # Shinpachi: snap zoom + 「喂！！」
BUBBLE_T = 16.0
BUBBLE = "往标题上弹鼻屎？！"
FLICK2 = FLICK + 2.0                 # ...and he flicks the next one at Shinpachi
HIT2 = FLICK2 + 0.2
END = 17.9
PAN_T0, PAN_V = 13.1, 7.0            # slow pan of the roof line


def _jump_y(t, t0, dur=JUMP_DUR, apex=64, y_from=262):
    k = seg(t, t0, t0 + dur)
    return lerp(y_from, ROOF_Y, k) - 4 * apex * k * (1 - k)


def _drift(t):
    return PAN_V * (t - PAN_T0)


TITLE_CAM = -19190       # skyline offset: castle on the left, Terminal on the right of the logo
SLAM = 0.16              # the logo flies in over black during the last SLAM s before T4


def _logo_scale(t):
    if t < T4:
        return lerp(3.4, 1.0, ease_in(seg(t, T4 - SLAM, T4)))
    u = t - T4
    if u < 0.16:
        return 1.0 + 0.08 * math.sin(seg(u, 0.0, 0.16) * math.pi)      # squash-bounce on impact
    return 1.0


def _logo_jolt(t):
    """The logo flinches when the booger hits it."""
    if SPLAT <= t < SPLAT + 0.2:
        return (1 if int((t - SPLAT) * 30) % 2 == 0 else -1), 1 if t < SPLAT + 0.07 else 0
    return 0, 0


def _draw_logo(img, t, bob=0):
    lg = A.logo()
    s = _logo_scale(t)
    spr = lg if s == 1.0 else lg.resize((int(lg.width * s), int(lg.height * s)), Image.NEAREST)
    jx, jy = _logo_jolt(t)
    img.paste(spr, (LOGO_C[0] - spr.width // 2 + jx, LOGO_C[1] - spr.height // 2 + bob + jy), spr)


def slam_in(img, t):
    """Pre-impact: the logo rushes toward the camera over the black fade."""
    k = seg(t, T4 - SLAM, T4)
    fx.speed_lines(img, t, LOGO_C[0], LOGO_C[1], color=(200, 200, 220), count=30, inner=int(150 - 80 * k),
                   seed=4, alpha=0.4 + 0.5 * k)
    _draw_logo(img, t)


def _title_cam(t):
    """(zoom, cx, cy) of the title camera, in world coordinates."""
    dr = _drift(t)
    if PICK0 <= t < FLICK:               # push in on Gintoki's deadpan face
        k = ease_in_out(seg(t, PICK0, PICK0 + 0.35))
        return lerp(1.0, 2.2, k), lerp(192, 192 - dr, k), lerp(108, ROOF_Y - 22, k)
    if t >= TSUKKOMI:                    # snap zoom for the tsukkomi (logo + booger still in frame)
        k = ease_out(seg(t, TSUKKOMI, TSUKKOMI + 0.08))
        z = lerp(1.0, 2.3, k) + 0.06 * seg(t, TSUKKOMI, END)
        return z, lerp(192, 168 - dr, k), lerp(108, 172, k)
    return 1.0, 192, 108


def _booger(img, x, y, splat=False):
    x, y = int(x), int(y)
    if not splat:
        rect(img, x - 2, y - 2, 5, 5, INK)
        rect(img, x - 1, y - 1, 3, 3, (160, 214, 96))
        pset(img, x - 1, y - 1, (220, 250, 170))
        return
    rect(img, x - 2, y - 1, 6, 4, INK)
    rect(img, x - 1, y - 2, 4, 6, INK)
    rect(img, x - 1, y, 4, 2, (150, 204, 88))
    rect(img, x, y - 1, 2, 4, (150, 204, 88))
    pset(img, x, y, (220, 250, 170))


def _gin_pick_t(t):
    """Nose-pick loop time so that the flick frame (frame 4 of 6 @6fps) lands on FLICK."""
    return max(0.0, t - FLICK + 4 / 6.0)


def shot_title(img, t):
    u = t - T4
    cam = TITLE_CAM + 7.0 * u
    C.sky(img, "day", t, horizon=150)
    A.rays(img, t, LOGO_C[0], LOGO_C[1] + 6, alpha=0.24 * seg(t, T4 + 0.05, T4 + 0.5))
    C.clouds(img, t, cam, "day", seed=3, count=6, y0=4, y1=70)
    E.skyline(img, cam, t, "day", ships=True, sky=False, near=True)
    E.roof_walk(img, cam, ROOF_Y, t, "day")
    drift = _drift(t)
    # awkward-silence crow crossing the sky after the splat
    if CROW_T <= t < CROW_T + 1.6:
        A.big_crow(img, 352 - 90 * (t - CROW_T), 30 + 6 * (t - CROW_T), t)
    # speed lines + shockwave rings from the impact
    if u < 0.35:
        fx.speed_lines(img, t, LOGO_C[0], LOGO_C[1], color=(255, 255, 255), count=40, inner=60,
                       seed=9, alpha=1 - seg(u, 0.1, 0.35))
    for (t0, col) in ((T4, (255, 255, 255)), (T4 + 0.08, (255, 214, 224))):
        if t0 <= t < t0 + 0.5:
            q = seg(t, t0, t0 + 0.5)
            rr = 30 + 250 * ease_out(q)
            wd = max(1, int(4 * (1 - q)))
            ImageDraw.Draw(img).ellipse([LOGO_C[0] - rr, LOGO_C[1] - rr * 0.55, LOGO_C[0] + rr, LOGO_C[1] + rr * 0.55],
                                        outline=col, width=wd)
    # --- the Yorozuya pop up onto the roof ridge below the logo
    for (cid, x0, tj, pose) in _CAST:
        if t < tj:
            continue
        x = x0 - drift
        if t < tj + JUMP_DUR:
            draw_char(img, cid, x, _jump_y(t, tj), "jump", t, shadow=False)
            continue
        tl = t - (tj + JUMP_DUR)
        if tl < 0.2:
            draw_char(img, cid, x, ROOF_Y, "land", t, p=tl / 0.2)
        elif cid == "gintoki":
            if t < PICK0:
                draw_char(img, cid, x, ROOF_Y, "shoulder", t)
            else:                         # deadpan pick -> flick -> keeps picking through the tsukkomi
                draw_char(img, cid, x, ROOF_Y, "nosepick", _gin_pick_t(t))
        elif cid == "shinpachi":
            if t >= HIT2:
                draw_char(img, cid, x, ROOF_Y, "shock", t, p=seg(t, HIT2, HIT2 + 0.5))
                _booger(img, x + 2, ROOF_Y - 23, splat=True)
            elif t >= TSUKKOMI:
                draw_char(img, cid, x, ROOF_Y, "point", t, p=seg(t, TSUKKOMI, TSUKKOMI + 0.6))
            elif t >= SPLAT + 0.1:
                draw_char(img, cid, x, ROOF_Y, "shock", t, p=seg(t, SPLAT + 0.1, TSUKKOMI))
            elif GLINT_T - 0.05 <= t < GLINT_T + 0.4:
                draw_char(img, cid, x, ROOF_Y, "idle", t, expr="glint")
            else:
                draw_char(img, cid, x, ROOF_Y, "idle", t)
        else:
            draw_char(img, cid, x, ROOF_Y, pose, t, expr="shock" if t >= SPLAT + 0.1 else None)
        fx.smoke_puff(img, t, tj + JUMP_DUR, x, ROOF_Y, size=7, seed=x0, color=(230, 230, 240), life=0.5)
    # Sadaharu: heavy leap from the street, THUD
    if t >= SADA_T:
        x = SADA_X - drift
        if t < SADA_T + 0.5:
            draw_char(img, "sadaharu", x, _jump_y(t, SADA_T, 0.5, apex=58, y_from=290), "run", t, facing=-1,
                      shadow=False)
        else:
            draw_char(img, "sadaharu", x, ROOF_Y, "bark" if BARK_T <= t < BARK_T + 0.3 else "sit", t, facing=-1)
            fx.smoke_puff(img, t, SADA_T + 0.5, x, ROOF_Y, size=14, seed=5, color=(230, 230, 240), life=0.6)
    # Shinpachi's glasses glint
    fx.sparkle(img, 144 - _drift(GLINT_T) + 3, ROOF_Y - 22, t, GLINT_T, size=4)
    # --- the logo
    bob = int(round(wave(t, 0.5, 1.5))) if u > 0.6 else 0
    _draw_logo(img, t, bob)
    # booger flicked onto the logo (the gag)
    if t >= FLICK:
        gx = 192 - _drift(FLICK) + 5
        p0, p1 = (gx, ROOF_Y - 26), (LOGO_C[0] + 50, LOGO_C[1] + 6)
        k = seg(t, FLICK, SPLAT)
        if k < 1:
            d = ImageDraw.Draw(img)
            for j, dk in enumerate((0.12, 0.06)):        # little motion trail
                tx, ty = arc(p0, p1, max(0.0, k - dk), 40)
                d.point((int(tx) + 1, int(ty) + 1), fill=(150, 204, 88) if j else (110, 150, 70))
            bx, by = arc(p0, p1, k, 40)
            bx, by = int(bx), int(by)
            rect(img, bx - 2, by - 2, 5, 5, INK)
            rect(img, bx - 1, by - 1, 3, 3, (160, 214, 96))
            pset(img, bx - 1, by - 1, (220, 250, 170))
        else:      # splat, stuck on 「魂」 for good
            jx, jy = _logo_jolt(t)
            bx, by = int(p1[0]) + jx, int(p1[1]) + bob + jy
            rect(img, bx - 2, by - 1, 6, 4, INK)
            rect(img, bx - 1, by - 2, 4, 6, INK)
            rect(img, bx - 1, by, 4, 2, (150, 204, 88))
            rect(img, bx, by - 1, 2, 4, (150, 204, 88))
            rect(img, bx, by, 1, 1, (220, 250, 170))
            fx.burst(img, t, SPLAT, bx, by, n=8, colors=((170, 220, 110),), speed=(20, 50),
                     gravity=60, life=0.35, seed=3)
    # second booger: straight at Shinpachi's glasses
    if FLICK2 <= t < HIT2:
        q = seg(t, FLICK2, HIT2)
        bx, by = arc((192 - drift + 3, ROOF_Y - 26), (144 - drift + 2, ROOF_Y - 23), q, 8)
        _booger(img, int(bx), int(by))
    # ribbon
    rb = A.ribbon()
    rk = ease_out(seg(t, T4 + 0.3, T4 + 0.6))
    rx = int(lerp(W + 20, LOGO_C[0] - rb.width // 2, rk))
    img.paste(rb, (rx, LOGO_C[1] + 50 + bob), rb)
    # sparkles on the logo
    for (sx, sy, t0, sz) in ((-72, -30, 12.35, 7), (78, -18, 12.95, 6), (-20, 36, 13.6, 5), (60, 28, 14.1, 6),
                             (-80, 8, 16.6, 5)):
        fx.sparkle(img, LOGO_C[0] + sx, LOGO_C[1] + sy + bob, t, t0, size=sz)
    # sakura: burst from the logo, then drifting petals
    fx.burst(img, t, T4, LOGO_C[0], LOGO_C[1], n=56,
             colors=((255, 183, 197), (255, 214, 224), (240, 140, 170), (255, 255, 255)),
             speed=(90, 280), gravity=50, life=1.6, size=(1, 3), seed=12, drag=1.6)
    n_pet = int(34 * seg(t, T4 + 0.3, T4 + 1.0))
    if n_pet:
        fx.sakura(img, t, count=n_pet, seed=3, wind=30, fall=22)
    # --- camera (push-in on Gintoki, snap zoom for the tsukkomi)
    z, zcx, zcy = _title_cam(t)
    A.zoom(img, z, zcx, zcy)

    def scr(x, y):
        return A.zoom_map(z, zcx, zcy, x, y)
    # screen-space callouts
    if PICK0 + 0.3 <= t < FLICK:
        hx, hy = scr(192 - drift + 12, ROOF_Y - 36)
        sfx_text(img, int(hx) + 16, int(hy) - 4, "抠…抠…", t, PICK0 + 0.3, dur=FLICK - PICK0 - 0.3, size=14,
                 color=(255, 255, 255), angle=-6, shake=0)
    if t >= SPLAT:
        sx_, sy_ = scr(LOGO_C[0] + 50, LOGO_C[1] + 6)
        sfx_text(img, int(sx_) + 22, int(sy_) - 12, "啪叽", t, SPLAT, dur=0.6, size=14,
                 color=(170, 230, 110), angle=12)
    if t >= HIT2:
        hx2, hy2 = scr(144 - drift, ROOF_Y - 24)
        sfx_text(img, int(hx2) + 34, int(hy2) - 2, "啪！", t, HIT2, dur=END - HIT2, size=18,
                 color=(170, 230, 110), angle=-14)
    if t >= TSUKKOMI:
        fx.speed_lines(img, t, W // 2, 132, color=(255, 255, 255), count=40, inner=112, seed=13,
                       alpha=0.85 * (1 - 0.5 * seg(t, TSUKKOMI + 0.5, TSUKKOMI + 1.2)))
        px_, py_ = scr(144 - drift, ROOF_Y - 34)          # Shinpachi's head on screen
        sfx_text(img, int(px_) - 52, int(py_) - 4, "喂！", t, TSUKKOMI, dur=END - TSUKKOMI, size=30,
                 angle=-10, shake=1)
        speech_bubble(img, int(px_) + 6, int(py_) - 3, BUBBLE, t, BUBBLE_T, tail=(-2, 1))
    # impact
    dx, dy = fx.shake_offset(t, T4, 0.45, 5, seed=6)
    ex, ey = fx.shake_offset(t, SADA_T + 0.5, 0.25, 2, seed=7)
    tx_, ty_ = fx.shake_offset(t, TSUKKOMI, 0.25, 3, seed=8)
    fx.shift(img, dx + ex + tx_, dy + ey + ty_)
    fx.flash(img, 1 - ease_out(seg(t, T4, T4 + 0.35)))
    fx.flash(img, 0.5 * (1 - seg(t, TSUKKOMI, TSUKKOMI + 0.12)) if t >= TSUKKOMI else 0)


# ============================================================ scene
class Prologue(Scene):
    id = "s00"
    title = "开场"
    duration = END
    # the title theme stops dead on the splat (record scratch + crow in the silence) and
    # slams back in — big hit on beat 0 — with Shinpachi's 「喂！」
    music = [(0, "prologue"), (12.0, "title"), (SPLAT, None), (TSUKKOMI, "title")]
    music_vol = 0.6
    fade_in = 0.4
    fade_out = 0.3
    subs = [
        (0.5, 4.0, None, "二十年前，自称『天人』的外星人从天而降。"),
        (4.3, 7.9, None, "武士们奋起抵抗，史称『攘夷战争』。"),
        (8.3, 11.9, None, "幕府投降，废刀令颁布。武士的时代，结束了……"),
    ]

    def render(self, img, t):
        if t < T2:
            shot_descent(img, t)
        elif t < T2B:
            shot_battle(img, t)
        elif t < T3:
            shot_heroes(img, t)
        elif t < T3B:
            shot_sword(img, t)
        elif t < T4:
            shot_board(img, t)
            if t >= T4 - SLAM:
                slam_in(img, t)
        else:
            shot_title(img, t)

    def cues(self):
        return [
            # 1 descent
            Cue(0.0, "engine_hum", vol=0.45, dur=4.1),
            Cue(0.0, "wind", vol=0.25, dur=4.1),
            Cue(0.5, "heartbeat", vol=0.35),
            Cue(1.3, "heartbeat", vol=0.3),
            Cue(1.05, "whoosh", vol=0.5, pitch=0.8, pan=-0.4),
            Cue(1.95, "whoosh", vol=0.5, pitch=0.9, pan=0.4),
            Cue(2.5, "whoosh", vol=0.3, pitch=0.6, pan=0.3),
            Cue(2.2, "whoosh", vol=0.3, pitch=0.55, pan=-0.5),
            Cue(2.85, "laser", vol=0.35, pitch=0.6),
            Cue(3.0, "aura", vol=0.3),
            # 2a battle
            Cue(T2, "explosion", vol=0.9),
            Cue(T2, "battle", vol=0.45, dur=2.0),
            Cue(T2, "crowd", vol=0.3, dur=2.0),
            Cue(4.30, "laser", vol=0.5),
            Cue(4.42, "explosion_small", vol=0.7, pan=0.3),
            Cue(4.85, "laser", vol=0.5),
            Cue(4.97, "explosion", vol=0.6, pan=-0.3),
            Cue(Z2_IN0, "whoosh", vol=0.45, pitch=1.2),
            Cue(5.30, "dash", vol=0.4),
            Cue(5.44, "slash_big", vol=0.8),
            Cue(5.48, "clang", vol=0.6),
            Cue(5.48, "impact", vol=0.55),
            Cue(5.50, "hit", vol=0.6),
            Cue(5.52, "fly_away", vol=0.45),
            Cue(5.60, "laser", vol=0.45),
            Cue(5.72, "explosion_small", vol=0.6, pan=0.5),
            Cue(5.60, "shock", vol=0.3),
            Cue(T2 + TWINKLE, "twinkle", vol=0.4),
            # 2b heroes (each blade leaves its scabbard)
            Cue(T2B, "wind", vol=0.55, dur=2.1),
            Cue(T2B, "fire", vol=0.25, dur=2.1),
        ] + [Cue(h[5], "shing", vol=0.4 + 0.1 * i, pitch=1.15 - 0.08 * i) for i, h in enumerate(_HEROES)] + [
            Cue(7.40, "sting_dramatic", vol=0.35),
            # 3a sword
            Cue(T3, "rain", vol=0.55, dur=3.55),
            Cue(T3, "thunder", vol=0.55),
            Cue(8.45, "whoosh", vol=0.35, pitch=0.6),
            Cue(LAND, "stab", vol=0.9),
            Cue(LAND, "clang", vol=0.35, pitch=0.8),
            Cue(LAND + 0.06, "thunder", vol=0.9),
            Cue(9.55, "shing", vol=0.35, pitch=1.2),
            # 3b board
            Cue(T3B + 0.08, "thunder", vol=0.35),
            Cue(10.5, "gong", vol=0.6),
            Cue(11.1, "footsteps", vol=0.3, dur=0.8),
            # 4 title
            Cue(T4 - SLAM - 0.02, "whoosh", vol=0.5, pitch=0.7),
            Cue(T4, "title_hit", vol=1.0),
            Cue(T4, "impact", vol=0.5),
            Cue(12.30, "whoosh", vol=0.4, pitch=1.3),
            Cue(12.35, "sparkle", vol=0.5),
        ] + [Cue(tj, "jump", vol=0.5, pitch=pt) for (_, _, tj, _), pt in zip(_CAST, (1.0, 1.15, 0.9))] + [
            Cue(tj + JUMP_DUR, "land", vol=0.45) for (_, _, tj, _) in _CAST] + [
            Cue(SADA_T, "jump", vol=0.5, pitch=0.6),
            Cue(SADA_T + 0.5, "thud", vol=0.8),
            Cue(GLINT_T, "sparkle", vol=0.45, pitch=1.2),
            Cue(BARK_T + 0.02, "bark", vol=0.45),
            Cue(PICK0, "whoosh", vol=0.25, pitch=0.8),
            Cue(FLICK, "pop", vol=0.55, pitch=1.4),
            Cue(FLICK + 0.02, "whoosh", vol=0.25, pitch=1.8),
            Cue(SPLAT, "slap", vol=0.35, pitch=1.4),
            Cue(SPLAT + 0.02, "squeak", vol=0.4),
            Cue(SPLAT + 0.04, "record_scratch", vol=0.55),
            Cue(CROW_T, "crow", vol=0.5),
            Cue(TSUKKOMI, "vein", vol=0.6),
            Cue(TSUKKOMI, "impact", vol=0.4),
            Cue(FLICK2, "pop", vol=0.5, pitch=1.5),
            Cue(HIT2, "slap", vol=0.5, pitch=1.3),
            Cue(HIT2 + 0.03, "shock", vol=0.45),
        ] + [Cue(BUBBLE_T + i / 16.0, "blip", vol=0.22, pitch=1.3 + 0.05 * (i % 3)) for i in range(len(BUBBLE))]


SCENE = Prologue()
