"""s05 桂与伊丽莎白 (17.8 s, music 'comedy', tod = dusk over Kabukicho).

SHOT LIST (scene-local seconds)
 S1a  0.00- 2.00  Rooftop chase, wide tracking pan (zoom 1.3, cam 85 px/s, parallax skyline).
                  Katsura (run_away, hair streaming) + Elizabeth flee right; Hijikata (katana
                  drawn, shouting) and Okita (running with bazooka) chase.  Okita stops,
                  fires at 1.20 -> shell zips over Hijikata's head (he ducks) -> roof tiles
                  explode behind Elizabeth at 1.50 (both hop).  Scorch mark keeps smoking.
                  sub: 土方「给我站住，桂！」
 S1b  2.00- 3.60  Okita close shot (zoom 2.0->2.3 push-in): lazy drawl 「假发——」, sadist face,
                  purple sadist aura; SCOPE inset 2.32-3.0 (Katsura drifts into the crosshair,
                  「锁定」 at 2.78); fires at 3.00 (muzzle flash, recoil), off-screen boom 3.35.
 S2a  3.60- 3.95  Katsura skids to a halt (record scratch, dust) and spins round.
 S2b  3.95- 5.60  REACTION CLOSE-UP: blue speed-line field, Katsura x4 pointing at camera-left,
                  BIG brush text 「不是假发」(4.02) 「是桂！」(4.38 slam, flash, shake).
                  sub: 桂「不是假发，是桂！」
 S3   5.60- 9.50  Two-shot on the ridge (zoom 1.5->1.68 push-in, sakura drifting).
                  name_card 桂小太郎 5.62 (smug pose); Elizabeth's sign 「……」 6.05 + a crow
                  flaps across the sunset (awkward beat);
                  a stray shell whizzes behind them 7.25 -> boom off-screen right 7.45 ->
                  sign flips to 「快跑」 (sweat, trembling); name_card 伊丽莎白 7.50.
                  Katsura deadpan pulls a lit bomb 7.85 「后会有期！」, throws it 8.55-9.05
                  (release 8.80, bomb arcs off frame), both dash off right in a dust cloud.
 S4   9.50-12.50  Kabukicho street below (Yorozuya behind, push-in 1.35->1.62): Gintoki strolls,
                  bomb falls (whistle) straight into his hand 10.45, 「？」 beat, SNAP zoom x3.1
                  onto his face 11.0 (shock, speed lines, sweat) sub「炸、炸弹！？」, back out:
                  panics left/right 11.75, old townsman flees, hurls it skyward 12.2.
 S5  12.50-14.20  Low-angle sky over Edo (Terminal on the right third): shell rises, bursts into
                  fireworks (gold 12.9, pink, cyan, then sparks form the kanji 「桂」 13.36);
                  Hijikata & Okita (x2, backlit silhouettes with firework rim light) watch.
                  One ember doesn't burn out: it falls back down (whistle) ...
 S6  14.20-17.80  ... BOOM on the street: black smoke clears -> soot-faced Gintoki with his
                  silver perm blown into a giant AFRO (scenes/_s05_soot.py), dazed white eyes,
                  crow 「阿呆～」, coughs smoke 15.06; 15.35 punch-in + speed lines, fists up:
                  「为什么每次倒霉的都是我啊！」; 16.1 waterfall tears + sad trombone; the last
                  spark lands on the afro 17.05 and it catches fire (he doesn't notice).
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from engine.core import (Scene, Cue, W, H, seg, lerp, clamp, ease_in, ease_out, ease_in_out,
                         ease_out_back, wave, step_frame, rng, arc)
from engine.gfx import (PAL, INK, ascii_sprite, paste, rect, overlay_rect, gradient, shade, mix,
                        silhouette, tint, pset, stamp_line, flip_h)
from engine import fx
from engine.text import draw_text, text_sprite, sfx_text, name_card, text_width
from chars import draw_char, render_sprite, get_def
from chars.rig import POSES, default_params, OX, OY
from bg import common as C, edo as E, kabukicho as K
from scenes._s05_soot import draw_soot_gintoki

try:
    from chars.katsura import draw_bomb
except Exception:  # pragma: no cover - fallback if the helper moves
    def draw_bomb(img, x, y, t, r=3, lit=True):
        x, y = int(x), int(y)
        d = ImageDraw.Draw(img)
        d.ellipse([x - r - 1, y - r - 1, x + r + 1, y + r + 1], fill=INK)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(52, 52, 70))
        if lit:
            pset(img, x + 3, y - r - 3, (255, 240, 120))

try:
    from chars.okita import _bazooka as _okita_bazooka
except Exception:  # pragma: no cover
    _okita_bazooka = None

TOD = "dusk"
ROOF_Y = 150            # feet line on the rooftop ridge
FLOOR = K.FLOOR_Y       # 160, street feet line

# shot boundaries
T_S1B, T_S2A, T_S2B, T_S3, T_S4, T_S5, T_S6, T_END = 2.0, 3.6, 3.95, 5.6, 9.5, 12.5, 14.2, 17.8


# ====================================================================== helpers
def cam1(t):
    """S1a tracking camera (world x of the screen's left edge)."""
    return 60 + 85 * t


def zpt(x, y, k, cx, cy):
    """Map a pre-zoom canvas point to screen after fx.zoom(img, k, cx, cy)."""
    return (x - (cx - W / (2 * k))) * k, (y - (cy - H / (2 * k))) * k


def rig_points(cid, pose, t, p=None, facing=1, **kw):
    """Feet-relative anchor points of a rig character (front hand, head centre).
    Mirrors compose()'s maths; used to put props (bombs...) in hands."""
    d = get_def(cid)
    fn = getattr(d, "poses", {}).get(pose) or POSES.get(pose) or POSES["idle"]
    pp = default_params()
    pp.update(pre=[], post=[], shift=(0, 0), behind=[], pose=pose)
    pp.update(getattr(d, "extra_params", {}) or {})
    fn(pp, t, p if p is not None else (t % 1.0), d)
    pp.update({k: v for k, v in kw.items() if k in pp})
    hip_y = OY - 1 - d.leg_len + pp["dy"]
    if pp["legs"] == "sit":
        hip_y = OY - 3 + pp["dy"]
    elif pp["legs"] == "kneel":
        hip_y = OY - 1 - d.leg_len + 3 + pp["dy"]
    elif pp["legs"] == "none":
        hip_y = OY - 1 + pp["dy"]
    tx = OX - d.hip[0] + pp["lean"] + pp["dx"]
    ty = hip_y - d.hip[1] + pp["bob"]
    sf = (tx + d.shoulder_f[0], ty + d.shoulder_f[1])
    a = math.radians(pp["arm_f"])
    hand = (sf[0] + math.sin(a) * d.arm_len, sf[1] + math.cos(a) * d.arm_len)
    head = (tx + d.neck[0] + pp["head_dx"], ty + d.neck[1] - 8 + pp["head_dy"])
    f = 1 if facing >= 0 else -1
    return {"hand": ((hand[0] - OX) * f, hand[1] - OY),
            "shoulder": ((sf[0] - OX) * f, sf[1] - OY),
            "head": ((head[0] - OX) * f, head[1] - OY)}


def sweat(img, x, y, col=(130, 200, 255)):
    x, y = int(x), int(y)
    rect(img, x - 1, y - 1, 3, 5, INK)
    pset(img, x, y - 2, INK)
    rect(img, x, y, 1, 3, col)
    pset(img, x, y - 1, col)


def text_spr(text, size, face="brush", color=(255, 255, 255), outline=INK, thick=2, _c={}):
    key = (text, size, face, color, outline, thick)
    s = _c.get(key)
    if s is None:
        s = text_sprite(text, color, size, face, outline=outline, thick=thick)
        _c[key] = s
    return s


def slam_text(img, t, t0, text, x, y, size, color, outline=INK, face="brush", thick=2, jitter=1):
    """Big text that slams in from 2.4x to 1x (with a little overshoot) and jitters."""
    if t < t0:
        return
    spr = text_spr(text, size, face, color, outline, thick)
    p = (t - t0) / 0.14
    if p < 1:
        k = lerp(2.4, 1.0, ease_out(p))
        spr = spr.resize((max(1, int(spr.width * k)), max(1, int(spr.height * k))), Image.NEAREST)
        a = clamp(p * 2)
    else:
        a = 1.0
    jx = int(wave(t, 14, jitter)) if jitter else 0
    jy = int(wave(t, 11, jitter, 0.3)) if jitter else 0
    paste(img, spr, x + jx, y + jy, anchor="center", alpha=a)


# ---------------------------------------------------------------- bazooka shell
_SHELL = None


def _shell_sprite():
    global _SHELL
    if _SHELL is None:
        art = """
..ooooooo...
.oyGGGGGgro.
oyyGGGGGGRRo
.oggggggrro.
..ooooooo...
"""
        _SHELL = ascii_sprite(art, {"o": INK, "G": (126, 146, 92), "g": (80, 98, 60), "y": (234, 196, 64),
                                     "R": (228, 59, 68), "r": (162, 38, 51)})
    return _SHELL


def draw_shell(img, t, t0, t1, p0, p1, lift=4, seed=0, trail=True):
    """Bazooka shell flying p0 -> p1 during [t0, t1] with flame + smoke trail."""
    if not (t0 <= t < t1):
        return None
    def pos(tt):
        k = clamp((tt - t0) / (t1 - t0))
        return (lerp(p0[0], p1[0], k), lerp(p0[1], p1[1], k) - lift * 4 * k * (1 - k))
    x, y = pos(t)
    d = 1 if p1[0] >= p0[0] else -1
    if trail:
        for i in range(1, 7):
            tt = t - i * 0.03
            if tt < t0:
                break
            sx, sy = pos(tt)
            r = 1 + i * 0.45
            c = (236, 230, 226) if i < 3 else (190, 182, 190)
            ImageDraw.Draw(img).ellipse([sx - r, sy - r, sx + r, sy + r], fill=c)
    spr = _shell_sprite()
    if d < 0:
        spr = flip_h(spr)
    # flame
    f = step_frame(t, 24, 3)
    fl = 3 + f
    fx0 = x - d * (6 + fl)
    ImageDraw.Draw(img).rectangle([min(fx0, x - d * 6), y - 1, max(fx0, x - d * 6), y + 1],
                                  fill=(255, 200, 60))
    pset(img, x - d * 7, y, (255, 255, 220))
    paste(img, spr, x, y, anchor="center")
    return x, y


def roof_blast(img, t, t0, x, y, size=22, seed=0):
    """Explosion on the tiles: fireball + flying roof tiles + dust."""
    fx.explosion(img, t, t0, x, y - 6, size=size, seed=seed)
    fx.burst(img, t, t0, x, y - 4, n=14, colors=[(96, 100, 128), (70, 72, 98), (140, 146, 170)],
             speed=(50, 130), gravity=260, life=0.9, size=(2, 3), seed=seed + 7, spread=(200, 340))


def scorch(img, t, t0, x, y, seed=0):
    """Smoking scorch mark on the ridge after a blast."""
    if t < t0:
        return
    d = ImageDraw.Draw(img)
    d.ellipse([x - 9, y - 2, x + 9, y + 3], fill=(40, 30, 40))
    d.ellipse([x - 5, y - 1, x + 5, y + 2], fill=(24, 18, 26))
    for i in range(4):
        r = rng("scorch", seed, i)
        ph = ((t - t0) * 0.9 + r.random()) % 1.0
        px = x + r.uniform(-6, 6) + ph * 6
        py = y - 2 - ph * 22
        rr = 1.5 + ph * 3
        c = (120, 108, 118) if ph < 0.6 else (92, 84, 96)
        d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=c)


# ---------------------------------------------------------------- fireworks
FW_GOLD = ((255, 255, 230), (255, 230, 120), (254, 174, 52), (180, 90, 30))
FW_PINK = ((255, 240, 250), (255, 150, 190), (230, 80, 140), (130, 40, 90))
FW_CYAN = ((240, 255, 255), (140, 230, 255), (60, 160, 240), (30, 70, 140))
FW_GREEN = ((245, 255, 230), (180, 250, 120), (90, 200, 80), (40, 100, 50))
FW_VIOLET = ((250, 240, 255), (210, 160, 255), (150, 90, 230), (70, 40, 120))


def firework(img, t, t0, x, y, R=40, cols=FW_GOLD, n=28, seed=0, life=1.5, grav=22.0):
    """Chrysanthemum burst: radial comets with fading trails, then crackle."""
    dt = t - t0
    if dt < 0 or dt > life:
        return
    d = ImageDraw.Draw(img)
    if dt < 0.1:
        rr = 3 + dt * 60
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=cols[0])
    fade = dt / life

    def pos(tt, ang, sp):
        k = 1 - math.exp(-tt * 4.0)
        return x + math.cos(ang) * sp * k, y + math.sin(ang) * sp * k + grav * tt * tt

    for i in range(n):
        r = rng("fw", seed, i)
        ang = 2 * math.pi * (i + r.uniform(-0.25, 0.25)) / n
        sp = R * r.uniform(0.8, 1.05)
        prev = None
        for j in range(5):
            tt = dt - j * 0.04
            if tt < 0:
                break
            px, py = pos(tt, ang, sp)
            ci = min(3, j + int(fade * 2.5))
            c = cols[ci]
            if fade > 0.72 and (step_frame(t, 20) + i + j) % 3 == 0:
                prev = None
                continue                       # crackle / flicker out
            if prev is not None and fade < 0.6:
                d.line([prev, (px, py)], fill=c)   # streaky petals
            if j == 0 and fade < 0.5:
                d.rectangle([px, py, px + 1, py + 1], fill=cols[0] if fade < 0.2 else c)
            else:
                d.point((px, py), fill=c)
            prev = (px, py)


_GLYPH_PTS = {}


def _glyph_points(ch):
    """Lit pixels of the 16px bitmap glyph (1px strokes -> clean dot-matrix sparks)."""
    pts = _GLYPH_PTS.get(ch)
    if pts is None:
        spr = text_sprite(ch, (255, 255, 255), 16, "pixel")
        a = np.asarray(spr)[..., 3] > 0
        h, w = a.shape
        ys, xs = np.nonzero(a)
        cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
        pts = [(float(x - cx), float(y - cy)) for y, x in zip(ys.tolist(), xs.tolist())]
        _GLYPH_PTS[ch] = pts
    return pts


def glow(img, x, y, radius, color, strength=0.8):
    """Additive soft (dithered) halo, e.g. around a firework burst."""
    if strength <= 0.02:
        return
    g = C.glow_sprite(int(radius), tuple(int(c * strength) for c in color), 1.0)
    C.add_sprite(img, g, int(x - g.width // 2), int(y - g.height // 2))


def glyph_firework(img, t, t0, x, y, ch="桂", cols=FW_GOLD, life=1.6, seed=5, spacing=4):
    """Sparks that fly out from the centre and settle into a kanji, twinkle, then droop."""
    dt = t - t0
    if dt < 0 or dt > life:
        return
    d = ImageDraw.Draw(img)
    if dt < 0.1:
        rr = 4 + dt * 70
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=cols[0])
    k = ease_out(clamp(dt / 0.35))
    droop = max(0.0, dt - 1.0)
    for i, (gx, gy) in enumerate(_glyph_points(ch)):
        r = rng("gfw", seed, i)
        tx_, ty_ = gx * spacing, gy * spacing
        px = x + tx_ * k + r.uniform(-0.6, 0.6) * droop * 10
        py = y + ty_ * k + 34 * droop * droop * r.uniform(0.6, 1.4)
        if dt > 1.15 and (step_frame(t, 16) + i) % 3 == 0:
            continue
        tw = (step_frame(t, 12) + i * 7) % 11
        c = cols[0] if tw == 0 else (cols[1] if dt < 0.95 else cols[2])
        if dt < 0.35:                      # streak toward the target
            qx, qy = x + tx_ * k * 0.6, y + ty_ * k * 0.6
            d.line([(qx, qy), (px, py)], fill=cols[2])
        if 0.35 < dt < 0.95 and tw == 0:
            d.rectangle([px - 1, py, px + 1, py], fill=c)
            d.rectangle([px, py - 1, px, py + 1], fill=c)
        elif dt < 0.95:
            d.rectangle([px, py, px + 1, py + 1], fill=c)
        else:
            d.point((px, py), fill=c)


# ---------------------------------------------------------------- soot
# (soot-covered afro Gintoki lives in scenes/_s05_soot.py)


def draw_elizabeth_sign(img, x, y, t, p, text, facing=1, expr=None):
    """Elizabeth's sign pose; un-mirrors the board when she faces left (the shared
    renderer flips the whole sprite, text included)."""
    spr, ax, ay = render_sprite("elizabeth", "sign", t, p, expr, facing, sign=text)
    if facing < 0:
        a = np.asarray(spr)
        fill = (a[..., 0] == 252) & (a[..., 1] == 252) & (a[..., 2] == 246) & (a[..., 3] > 0)
        if fill.any():
            ys, xs = np.nonzero(fill)
            x0, x1 = xs.min() - 1, xs.max() + 2
            y0, y1 = ys.min() - 2, ys.max() + 4
            spr = spr.copy()
            reg = spr.crop((x0, y0, x1, y1)).transpose(Image.FLIP_LEFT_RIGHT)
            spr.paste(reg, (x0, y0))
    overlay_rect(img, int(x) - 6, int(y) - 1, 12, 2, (0, 0, 0), 0.25)
    img.paste(spr, (int(round(x - ax)), int(round(y - ay))), spr)


# ---------------------------------------------------------------- misc props
_CROW = {}


def crow(img, x, y, t, facing=-1, scale=1):
    f = step_frame(t, 8, 2)
    key = (f, facing, scale)
    s = _CROW.get(key)
    if s is None:
        arts = ["""
o..........o
oo........oo
.ooo....ooo.
..ooooooooo.
....ooooooyo
.....oo.....
""", """
............
....oooooo..
..oooooooooo
.ooo.oo.oyoo
oo...oo.....
o...........
"""]
        s = ascii_sprite(arts[f], {"o": (20, 16, 26), "y": (230, 190, 60)})
        s = s if facing > 0 else flip_h(s)
        if scale != 1:
            s = s.resize((s.width * scale, s.height * scale), Image.NEAREST)
        _CROW[key] = s
    paste(img, s, x, y, anchor="center")


def question(img, x, y, t, t0, dur=0.6):
    """Pop-in '？' above a head."""
    if not (t0 <= t < t0 + dur):
        return
    p = (t - t0) / dur
    s = ease_out_back(clamp(p / 0.25))
    spr = text_spr("？", 24, "hei", (255, 255, 255), INK, 2)
    if s < 0.99:
        spr = spr.resize((max(1, int(spr.width * s)), max(1, int(spr.height * s))), Image.NEAREST)
    paste(img, spr, x, y - int(wave(t, 3, 1)), anchor="bottom")


def okita_run_bazooka(img, x, y, t, facing=1):
    """Okita running with his bazooka on the shoulder (run pose + the pose's tube)."""
    spr, ax, ay = render_sprite("okita", "run", t)
    if _okita_bazooka is not None:
        spr = spr.copy()
        rp = rig_points("okita", "run", t)
        sx, sy = rp["shoulder"]
        _okita_bazooka(spr, int(ax + sx), int(ay + sy), t, -1)
        hx, hy = rp["hand"]
        stamp_line(spr, (ax + hx, ay + hy), (ax + hx, ay + hy), 4, INK)
        stamp_line(spr, (ax + hx, ay + hy), (ax + hx, ay + hy), 3, (255, 218, 186))
    if facing < 0:
        spr = flip_h(spr)
        ax = spr.width - 1 - ax
    overlay_rect(img, int(x) - 6, int(y) - 1, 12, 2, (0, 0, 0), 0.25)
    img.paste(spr, (int(round(x - ax)), int(round(y - ay))), spr)


def roof_bg(img, cam_x, t, y=ROOF_Y):
    E.skyline(img, cam_x, t, TOD, near=False)
    E.roof_walk(img, cam_x, y, t, TOD)


# ====================================================================== shots
def shot_s1a(img, t):
    cam = cam1(t)
    roof_bg(img, cam, t)
    # world-anchored stuff
    W1 = 205 + cam1(1.5)                           # impact point of shell 1
    scorch(img, t, 1.62, W1 - cam, ROOF_Y, seed=1)
    # --- Okita: runs, stops 0.85-1.55 to fire, then sprints to catch up
    if t < 0.85:
        ox = 80
        okita_run_bazooka(img, ox, ROOF_Y, t)
    elif t < 1.55:
        ox = 80 + cam1(0.85) - cam
        draw_char(img, "okita", ox, ROOF_Y, "bazooka", t, p=clamp((t - 0.85) / 0.7))
    else:
        ox = lerp(80 + cam1(0.85) - cam1(1.55), 72, ease_out(seg(t, 1.55, 2.0)))
        okita_run_bazooka(img, ox, ROOF_Y, t)
    # --- Hijikata: katana drawn, yelling; ducks when the shell zips over
    hx = lerp(126, 146, seg(t, 0, 2))
    duck = 1.26 <= t < 1.5
    if 0.3 <= t < 2.05:
        he = "shout" if step_frame(t, 10) % 2 == 0 else "angry"
    else:
        he = "angry"
    if duck:
        draw_char(img, "hijikata", hx, ROOF_Y, "run", t, expr="shock", weapon=150, arm_f=160, bob=3)
    else:
        draw_char(img, "hijikata", hx, ROOF_Y, "run", t, expr=he, weapon=14, arm_f=82)
    # --- the fleeing duo (hop over the blast)
    hop_k = seg(t, 1.48, 1.86)
    hop = 4 * hop_k * (1 - hop_k)
    ey = ROOF_Y - 15 * hop
    ky = ROOF_Y - 11 * seg(t, 1.52, 1.9) * (1 - seg(t, 1.52, 1.9)) * 4
    draw_char(img, "elizabeth", 234 + wave(t, 1.3, 2), ey, "run_away" if hop > 0 else "run", t)
    draw_char(img, "katsura", 272 + wave(t, 0.9, 2, 0.4), ky, "run_away", t)
    # --- shell 1: muzzle -> roof behind Elizabeth
    m0 = (80 + cam1(0.85) - cam1(1.2) + 22, ROOF_Y - 13)
    s = draw_shell(img, t, 1.2, 1.5, (m0[0] + cam1(1.2) - cam, m0[1]),
                   (W1 - cam, ROOF_Y - 3), lift=10, seed=1)
    roof_blast(img, t, 1.5, W1 - cam, ROOF_Y, size=22, seed=11)
    fx.smoke_puff(img, t, 1.86, 234, ROOF_Y, size=6, seed=2)
    fx.smoke_puff(img, t, 1.9, 272, ROOF_Y, size=6, seed=3)
    # --- camera
    k, cx, cy = 1.3, 176, 122
    fx.zoom(img, k, cx, cy)
    fx.motion_lines(img, t, color=(255, 214, 190), count=7, direction=-1, seed=5,
                    y0=40, y1=120, speed=700, length=(14, 40))
    sx, sy = zpt(W1 - cam, ROOF_Y - 20, k, cx, cy)
    sfx_text(img, int(sx), int(sy) - 10, "轰!", t, 1.5, 0.7, size=22, color=(255, 200, 70))
    dx, dy = fx.shake_offset(t, 1.5, 0.35, 4, seed=1)
    fx.shift(img, dx, dy)


_MASKS = {}


def _circle_mask(r):
    m = _MASKS.get(r)
    if m is None:
        m = Image.new("L", (2 * r + 1, 2 * r + 1), 0)
        ImageDraw.Draw(m).ellipse([0, 0, 2 * r, 2 * r], fill=255)
        _MASKS[r] = m
    return m


def scope_inset(img, t, t0, t1, cx, cy, R=50, t_lock=None):
    """Okita's bazooka scope (picture-in-picture): the fleeing Katsura drifts into
    the crosshair and gets locked on."""
    if not (t0 <= t < t1):
        return
    r = int(R * ease_out_back(seg(t, t0, t0 + 0.16)) * (1 - ease_in(seg(t, t1 - 0.07, t1))))
    if r < 4:
        return
    t_lock = t_lock or (t0 + 0.45)
    sub = Image.new("RGB", (W, H))
    cam = cam1(1.0) + 85 * (t - t0)          # keeps running along the same ridge
    roof_bg(sub, cam, t)
    draw_char(sub, "elizabeth", 236 + wave(t, 1.3, 2), ROOF_Y, "run", t)
    draw_char(sub, "katsura", 272, ROOF_Y, "run_away", t)
    lk = ease_out(seg(t, t0, t_lock))
    fx_ = 272 - 34 * (1 - lk) + wave(t, 2.3, 3 * (1 - lk)) + 2
    fy_ = ROOF_Y - 26 + 16 * (1 - lk) + wave(t, 1.7, 2 * (1 - lk), 0.3)
    fx.zoom(sub, 2.6, fx_, fy_)
    crop = sub.crop((W // 2 - r, H // 2 - r, W // 2 + r + 1, H // 2 + r + 1))
    tint_c = (70, 150, 80) if t < t_lock else (170, 60, 60)
    crop = Image.blend(crop, Image.new("RGB", crop.size, tint_c), 0.18)
    img.paste(crop, (int(cx - r), int(cy - r)), _circle_mask(r))
    d = ImageDraw.Draw(img)
    locked = t >= t_lock
    col = (255, 70, 70) if locked else (210, 255, 200)
    d.line([(cx - r + 4, cy), (cx - 5, cy)], fill=col)
    d.line([(cx + 5, cy), (cx + r - 4, cy)], fill=col)
    d.line([(cx, cy - r + 4), (cx, cy - 5)], fill=col)
    d.line([(cx, cy + 5), (cx, cy + r - 4)], fill=col)
    for i in (-2, -1, 1, 2):                                   # range ticks
        d.line([(cx + i * r // 3, cy - 2), (cx + i * r // 3, cy + 2)], fill=col)
    if locked:
        rr = int(12 - 5 * ease_out(seg(t, t_lock, t_lock + 0.15)))
        d.rectangle([cx - rr, cy - rr, cx + rr, cy + rr], outline=col)
    d.ellipse([cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2], outline=INK, width=4)
    d.ellipse([cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1], outline=(98, 118, 72), width=2)
    if locked and step_frame(t, 8) % 2 == 0:
        draw_text(img, int(cx), int(cy + r - 16), "锁定", (255, 90, 90), size=12, anchor="mt", outline=INK)


def shot_s1b(img, t):
    roof_bg(img, 470 + 6 * (t - T_S1B), t)
    p = clamp((t - 2.0) / 2.0)
    ox = 150
    # sadistic calm: the aura creeps in while he drawls 「假发——」
    if 2.35 <= t < 3.3:
        a = seg(t, 2.35, 2.7) * (1 - seg(t, 3.05, 3.3))
        f = step_frame(t, 12)
        for i in range(9):
            r_ = rng("aura", i)
            ax_ = ox - 16 + i * 4 + r_.randint(-1, 1)
            ph = (f * 0.23 + r_.random()) % 1.0
            h_ = int((10 + 16 * r_.random()) * a)
            if h_ > 1:
                y1 = ROOF_Y - 8 - ph * 10
                stamp_line(img, (ax_, y1), (ax_ + (1 if (f + i) % 2 else -1), y1 - h_), 2, (96, 52, 132))
    draw_char(img, "okita", ox, ROOF_Y, "bazooka", t, p=p, expr="sadist" if 2.45 <= t < 3.0 else None)
    # shell leaving to the right -> distant blast on the far roofs
    draw_shell(img, t, 3.0, 3.16, (ox + 22, ROOF_Y - 13), (ox + 150, ROOF_Y - 17), lift=2, seed=2)
    glow(img, 246, 128, 22, (255, 170, 80), 0.9 * (1 - seg(t, 3.35, 3.6)) if t >= 3.35 else 0)
    fx.explosion(img, t, 3.35, 246, 128, size=9, seed=21)
    k = lerp(2.0, 2.3, ease_in_out(seg(t, T_S1B, T_S2A)))
    cx, cy = 176, 128
    fx.zoom(img, k, cx, cy)
    scope_inset(img, t, 2.32, 3.0, 296, 76, R=50, t_lock=2.78)
    if t >= 3.0:
        sx, sy = zpt(ox + 30, ROOF_Y - 26, k, cx, cy)
        sfx_text(img, int(sx) + 30, int(sy) - 4, "咻——", t, 3.0, 0.5, size=18, color=(255, 255, 255), angle=0)
    dx, dy = fx.shake_offset(t, 3.0, 0.2, 2, seed=2)
    dx2, dy2 = fx.shake_offset(t, 3.35, 0.25, 2, seed=3)
    fx.shift(img, dx + dx2, dy + dy2)


def shot_s2a(img, t):
    u = t - T_S2A
    v = 85 * min(u, 0.25) - 85 * min(u, 0.25) ** 2 / 0.5
    roof_bg(img, 900 + v, t)
    kx = 200
    if t < 3.8:
        draw_char(img, "katsura", kx, ROOF_Y, "land", t, p=0.5, expr="determined", lean=-3,
                  legs="lunge", arm_f=60, arm_b=120)
        for i, t0 in enumerate((3.61, 3.66, 3.71, 3.76)):
            fx.smoke_puff(img, t, t0, kx - 8 - i * 3, ROOF_Y - 1, size=5, seed=20 + i,
                          color=(226, 214, 214))
    else:
        draw_char(img, "katsura", kx, ROOF_Y, "idle", t, expr="angry", facing=-1, arm_f=40)
        fx.smoke_puff(img, t, 3.8, kx, ROOF_Y - 2, size=7, seed=30, color=(226, 214, 214))
    k, cx, cy = 1.9, 204, 124
    fx.zoom(img, k, cx, cy)
    if t < 3.8:
        sfx_text(img, 250, 70, "嘎——!", t, 3.61, 0.3, size=20, color=(255, 255, 255), angle=6)
    else:
        # whip-turn arc
        fx.slash_arc(img, 200, 110, 34, 200, 340, seg(t, 3.8, 3.93) * 1.4, (255, 255, 255), 2)


_BG2 = {}


def _closeup_bg():
    s = _BG2.get(0)
    if s is None:
        s = Image.new("RGB", (W, H))
        gradient(s, 0, 0, W, H, (26, 40, 110), (84, 120, 220), steps=7)
        _BG2[0] = s
    return s


def shot_s2b(img, t):
    img.paste(_closeup_bg())
    fcx, fcy = 298, 84
    fx.speed_lines(img, t, fcx, fcy, color=(210, 226, 255), count=56, inner=70, seed=7, thickness=2)
    fx.speed_lines(img, t + 0.37, fcx, fcy, color=(255, 255, 255), count=26, inner=86, seed=8, thickness=1)
    p = clamp((t - T_S2B) / 1.2)
    spr, ax, ay = render_sprite("katsura", "point", t, p, None, -1, scale=4)
    jx = int(wave(t, 9, 1)) if t > 4.38 else 0
    img.paste(spr, (int(306 - ax + jx), int(190 - ay)), spr)
    # slam flash
    fx.flash(img, 0.7 * (1 - seg(t, 4.38, 4.55)) if t >= 4.38 else 0)
    fx.flash(img, 0.5 * (1 - seg(t, T_S2B, T_S2B + 0.12)) if t >= T_S2B else 0)
    # BIG line
    slam_text(img, t, 4.02, "不是假发", 104, 58, 34, (255, 255, 255), INK, thick=2)
    slam_text(img, t, 4.38, "是桂！", 112, 116, 60, (255, 226, 70), (150, 20, 40), thick=3, jitter=2)
    dx, dy = fx.shake_offset(t, 4.02, 0.2, 3, seed=4)
    dx2, dy2 = fx.shake_offset(t, 4.38, 0.45, 6, seed=5)
    fx.shift(img, dx + dx2, dy + dy2, fill=(26, 40, 110))


def shot_s3(img, t):
    roof_bg(img, 700 + 3 * (t - T_S3), t)
    kx, ex = 160, 232
    # stray shell behind them + off-screen blast debris flying in from the right
    draw_shell(img, t, 7.25, 7.45, (60, 106), (330, 112), lift=3, seed=3)
    fx.burst(img, t, 7.45, 316, 132, n=12, colors=[(96, 100, 128), (140, 146, 170), (70, 72, 98)],
             speed=(60, 140), gravity=240, life=0.9, size=(2, 3), seed=41, spread=(170, 250))
    if t < 9.05:
        # ---- Katsura
        if t < 7.45:
            # self-satisfied pose for his name card, hair fluttering in the wind
            draw_char(img, "katsura", kx, ROOF_Y, "idle", t, expr="smug", facing=-1,
                      arm_f=118 if t < 6.0 else 60, arm_b=-20)
        elif t < 7.85:
            ke = "shock" if t < 7.62 else ("normal" if (t % 3.1) > 0.12 else "blink")
            draw_char(img, "katsura", kx, ROOF_Y, "idle", t, expr=ke, facing=-1)
        elif t < 8.55:
            draw_char(img, "katsura", kx, ROOF_Y, "bomb", t, facing=-1)
        else:
            draw_char(img, "katsura", kx, ROOF_Y, "bomb_throw", t, p=clamp((t - 8.55) / 0.5), facing=-1)
        # ---- Elizabeth
        if t < 6.05:
            draw_char(img, "elizabeth", ex, ROOF_Y, "idle", t, facing=-1)
        elif t < 7.47:
            draw_elizabeth_sign(img, ex, ROOF_Y, t, clamp((t - 6.05) / 1.2), "……", facing=-1)
        else:
            jit = int(wave(t, 16, 1))
            draw_elizabeth_sign(img, ex + jit, ROOF_Y, t, clamp((t - 7.47) / 1.2), "快跑",
                                facing=-1, expr="shock")
            if step_frame(t, 6) % 2 == 0:
                sweat(img, ex + 13, ROOF_Y - 32 + step_frame(t, 6, 3))
    else:
        # dash off right in a dust cloud
        u = t - 9.05
        draw_char(img, "katsura", kx + 520 * u * u + 120 * u, ROOF_Y, "run_away", t)
        draw_char(img, "elizabeth", ex + 480 * u * u + 90 * u, ROOF_Y, "run_away", t)
        fx.smoke_puff(img, t, 9.05, kx, ROOF_Y - 4, size=12, seed=50, color=(236, 226, 222), life=0.5)
        fx.smoke_puff(img, t, 9.07, ex, ROOF_Y - 6, size=13, seed=51, color=(236, 226, 222), life=0.5)
    # thrown bomb arcing away up-left (released at p=0.5 -> 8.80)
    if 8.78 <= t < 9.3:
        rp = rig_points("katsura", "bomb_throw", t, p=0.47, facing=-1)
        hx, hy = kx + rp["hand"][0], ROOF_Y + rp["hand"][1]
        k = seg(t, 8.78, 9.2)
        bx, by = arc((hx, hy - 2), (hx - 150, hy - 34), k, 16)
        draw_bomb(img, bx, by, t)
        for i in range(1, 4):                           # fuse sparks trailing behind
            qx, qy = arc((hx, hy - 2), (hx - 150, hy - 34), max(0.0, k - i * 0.03), 16)
            pset(img, qx + 2, qy - 4, (255, 230, 150))
    # the stray shell blows up just past the right edge of the frame
    glow(img, 318, 132, 30, (255, 170, 80), 0.9 * (1 - seg(t, 7.45, 7.8)) if t >= 7.45 else 0)
    fx.explosion(img, t, 7.45, 318, 132, size=22, seed=42, smoke=False)
    for i, (t0, dx_, sz) in enumerate(((7.6, -4, 9), (7.7, 6, 11), (7.85, -8, 8))):
        fx.smoke_puff(img, t, t0, 318 + dx_, 124 - i * 4, size=sz, seed=60 + i,
                      color=(150, 136, 150), life=1.1)
    # awkward-silence crow flaps across while the sign says 「……」
    if 6.15 <= t < 7.3:
        u = seg(t, 6.15, 7.3)
        crow(img, int(lerp(W - 60, 30, u)), int(97 + wave(t, 2.0, 1.5)), t, facing=-1)
    fx.sakura(img, t, count=10, seed=3, wind=30, fall=14, area=(0, 20, W, 170))
    k = lerp(1.5, 1.68, ease_in_out(seg(t, T_S3, T_S4)))
    cx, cy = 196, 116
    fx.zoom(img, k, cx, cy)
    sx, sy = zpt(kx, ROOF_Y - 40, k, cx, cy)
    if 7.85 <= t < 8.5:
        sfx_text(img, int(sx) - 6, int(sy) - 8, "嗤嗤…", t, 7.9, 0.6, size=14, color=(255, 230, 150), angle=0)
    if 7.45 <= t < 8.0:
        sfx_text(img, W - 44, 92, "轰!!", t, 7.45, 0.55, size=24, color=(255, 200, 70), angle=-12)
    name_card(img, t, 5.62, 2.0, "katsura", "桂小太郎", "攘夷志士｜逃跑的小太郎·天然呆", side="right", y=18)
    name_card(img, t, 7.50, 2.0, "elizabeth", "伊丽莎白", "谜之生物｜只用牌子说话", side="left", y=18)
    dx, dy = fx.shake_offset(t, 7.45, 0.3, 3, seed=6)
    fx.shift(img, dx, dy)


def _gintoki_street(img, t, cam):
    K.street(img, cam, t, TOD)


def shot_s4(img, t):
    cam = K.YOROZUYA_X - 200 + 6 * (t - T_S4)
    _gintoki_street(img, t, cam)
    gx = 196
    # old townsman strolling left, then flees
    if t < 11.75:
        tx = lerp(318, 262, seg(t, T_S4, 11.75))
        draw_char(img, "townsman", tx, FLOOR, "walk", t, facing=-1, variant=2)
    else:
        u = t - 11.75
        draw_char(img, "townsman", 262 + 190 * u, FLOOR, "flee", t, variant=2)
    # --- Gintoki
    bomb_at = None
    if t < 10.2:
        x = lerp(128, gx, seg(t, T_S4, 10.2))
        draw_char(img, "gintoki", x, FLOOR, "walk", t)
    elif t < 11.0:
        catch = seg(t, 10.2, 10.35)
        arm = lerp(12, 100, ease_out(catch))
        draw_char(img, "gintoki", gx, FLOOR, "idle", t, arm_f=arm, expr="normal" if t < 10.9 else "blink")
        rp = rig_points("gintoki", "idle", t, arm_f=arm)
        if t >= 10.45:
            bounce = -2 if t < 10.52 else 0
            bomb_at = (gx + rp["hand"][0] + 1, FLOOR + rp["hand"][1] - 3 + bounce)
    elif t < 11.75:
        draw_char(img, "gintoki", gx, FLOOR, "shock", t, p=seg(t, 11.0, 11.75))
        rp = rig_points("gintoki", "shock", t, p=seg(t, 11.0, 11.75))
        bomb_at = (gx + rp["hand"][0] + 1, FLOOR + rp["hand"][1] - 4)
    elif t < 12.2:
        u = t - 11.75
        ph = u * 2 * math.pi * 2.2
        x = gx + 24 * math.sin(ph)
        fac = 1 if math.cos(ph) >= 0 else -1
        draw_char(img, "gintoki", x, FLOOR, "run_away", t, facing=fac)
        rp = rig_points("gintoki", "run_away", t, facing=fac)
        bomb_at = (x + rp["hand"][0], FLOOR + rp["hand"][1] - 4)
        if step_frame(t, 8) % 2 == 0:
            sweat(img, x - 9 * fac, FLOOR - 36)
    else:
        u = t - 12.2
        draw_char(img, "gintoki", gx, FLOOR, "idle", t, arm_f=158, arm_b=-40, expr="shout", lean=-1)
        rp = rig_points("gintoki", "idle", t, arm_f=158)
        hx, hy = gx + rp["hand"][0], FLOOR + rp["hand"][1]
        if u < 0.04:
            bomb_at = (hx, hy - 4)
        else:
            draw_bomb(img, hx, hy - 4 - 900 * (u - 0.04), t)
            for i in range(1, 5):
                pset(img, hx + 3, hy - 4 - 900 * (u - 0.04) + i * 9, (255, 230, 150))
    # falling bomb
    if 9.85 <= t < 10.45:
        rp = rig_points("gintoki", "idle", t, arm_f=100)
        tx_, ty_ = gx + rp["hand"][0] + 1, FLOOR + rp["hand"][1] - 3
        k = ease_in(seg(t, 9.85, 10.45))
        by = lerp(20, ty_, k)
        draw_bomb(img, tx_ + 6 * (1 - k), by, t)
        for i in range(1, 4):
            pset(img, tx_ + 6 * (1 - k) + 2, by - 5 - i * 5, (255, 230, 150))
    if bomb_at:
        draw_bomb(img, bomb_at[0], bomb_at[1], t)
    # camera
    snap = 11.0 <= t < 11.75
    if snap:
        k = lerp(3.8, 3.1, ease_out(seg(t, 11.0, 11.15)))
        cx, cy = gx + 3, FLOOR - 13
    elif t < 11.0:                       # slow push-in while he strolls / catches
        k = lerp(1.35, 1.62, ease_in_out(seg(t, T_S4, 11.0)))
        cx, cy = lerp(196, 198, seg(t, T_S4, 11.0)), lerp(116, 124, seg(t, T_S4, 11.0))
    else:
        k = lerp(1.62, 1.95, ease_out(seg(t, 11.75, 11.9)))          # closer for the panic
        cx, cy = 200, lerp(124, 126, seg(t, 11.75, 11.9))
    fx.zoom(img, k, cx, cy)
    if snap:
        fcx, fcy = zpt(gx + 1, FLOOR - 22, k, cx, cy)
        fx.speed_lines(img, t, int(fcx), int(fcy), color=(255, 255, 255), count=44, inner=84, seed=9)
        if step_frame(t, 6) % 2 == 0:
            sweat(img, fcx - 38, fcy - 26)
            sweat(img, fcx + 40, fcy - 14)
        sfx_text(img, int(fcx) + 84, int(fcy) - 44, "！？", t, 11.0, 0.75, size=30, color=(255, 90, 90), angle=8)
        fx.flash(img, 0.6 * (1 - seg(t, 11.0, 11.1)))
    else:
        hx, hy = zpt(gx + 2, FLOOR - 37, k, cx, cy)
        question(img, int(hx), int(hy), t, 10.52, 0.48)
        if 10.45 <= t < 10.8:
            bx, by = zpt(gx + 12, FLOOR - 24, k, cx, cy)
            sfx_text(img, int(bx) + 14, int(by) - 8, "啪", t, 10.45, 0.4, size=14, color=(255, 255, 255), angle=-10)
        if t >= 12.2:
            sfx_text(img, 250, 60, "嘿咻!", t, 12.2, 0.3, size=18, color=(255, 255, 255), angle=-8)


FW_MAIN = (170, 66)       # where the bomb bursts in S5 (open sky left of the Terminal)


def backlit(spr, rim, amount=1.0, px=2):
    """Backlit figure: body sunk into a dark violet (details faintly visible),
    cigarette smoke kept pale, and a px-thick rim light on the top/left edges."""
    a = np.asarray(spr).copy()
    op = a[..., 3] > 0
    rgb = a[..., :3].astype(np.float32)
    dark = np.array((36, 24, 54), np.float32)
    out_rgb = rgb * 0.2 + dark * 0.8
    smoke = op & (np.abs(rgb[..., 0] - rgb[..., 1]) < 14) & (rgb[..., 2] >= rgb[..., 0]) & (rgb[..., 0] > 150)
    out_rgb[smoke] = rgb[smoke] * 0.65 + dark * 0.35
    edge = np.zeros_like(op)
    for k in range(1, px + 1):
        up = np.zeros_like(op)
        up[k:, :] = op[:-k, :]
        lf = np.zeros_like(op)
        lf[:, k:] = op[:, :-k]
        edge |= op & (~up | ~lf)
    edge &= ~smoke
    rc = np.array([lerp(120, rim[0], amount), lerp(90, rim[1], amount), lerp(140, rim[2], amount)], np.float32)
    out_rgb[edge] = rc
    out = a.copy()
    out[..., :3] = out_rgb.clip(0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def shot_s5(img, t):
    cam = -1010 + 10 * (t - T_S5)            # Terminal pushed to the right third
    E.skyline(img, cam, t, TOD, dy=36)
    mx, my = FW_MAIN
    # accumulated firework glow on the sky
    flashes = [(12.9, FW_GOLD[1], 0.28), (13.08, FW_PINK[1], 0.16), (13.22, FW_CYAN[1], 0.16),
               (13.36, FW_GOLD[1], 0.22)]
    for t0, col, a in flashes:
        if t0 <= t < t0 + 0.35:
            overlay_rect(img, 0, 0, W, 150, col, a * (1 - seg(t, t0, t0 + 0.35)))
    # rising shell (comet with a sparkling tail)
    if T_S5 <= t < 12.9:
        k = ease_out(seg(t, T_S5, 12.9))
        bx, by = mx - 6 + 6 * k, lerp(216, my, k)
        for i in range(1, 10):
            kk = ease_out(seg(t - i * 0.025, T_S5, 12.9))
            jx = rng("tail", i, step_frame(t, 20)).randint(-1, 1)
            pset(img, mx - 6 + 6 * kk + jx + 3, lerp(216, my, kk) + 3, FW_GOLD[min(3, i // 3)])
        draw_bomb(img, bx, by, t)
    bursts = ((12.9, mx, my, FW_GOLD[1], 46), (13.08, 62, 44, FW_PINK[1], 34),
              (13.22, 262, 40, FW_CYAN[1], 34), (13.36, 142, 54, FW_GOLD[1], 46))
    for t0, x0, y0, col, rad in bursts:
        if t >= t0:
            glow(img, x0, y0, rad, col, 0.55 * (1 - seg(t, t0, t0 + 0.7)))
    fx.explosion(img, t, 12.9, mx, my, size=16, seed=70, smoke=False)
    firework(img, t, 12.9, mx, my, R=66, cols=FW_GOLD, n=40, seed=1, life=1.3)
    firework(img, t, 13.08, 62, 44, R=42, cols=FW_PINK, n=30, seed=2, life=1.1)
    firework(img, t, 13.22, 262, 40, R=44, cols=FW_CYAN, n=30, seed=3, life=0.9)
    glyph_firework(img, t, 13.36, 142, 54, "桂", FW_GOLD, life=1.2, spacing=4)
    firework(img, t, 13.72, 330, 28, R=26, cols=FW_GREEN, n=20, seed=4, life=0.5)
    firework(img, t, 13.86, 250, 96, R=22, cols=FW_VIOLET, n=18, seed=6, life=0.4)
    # foreground: Hijikata & Okita on a near roof, backlit, flickering with the burst colours
    E.roof_walk(img, 40 + 4 * (t - T_S5), 208, t, TOD)
    lit, lc = 0.0, FW_GOLD[1]
    for t0, col, a in flashes:
        if t >= t0:
            v = 1 - seg(t, t0, t0 + 0.5)
            if v > lit:
                lit, lc = v, col
    for cid, x, pose, p_ in (("okita", 262, "bazooka", 0.2), ("hijikata", 330, "smoke", None)):
        spr, ax, ay = render_sprite(cid, pose, t, p_, None, -1, scale=2)
        spr = backlit(spr, lc, 0.35 + 0.65 * lit)
        img.paste(spr, (int(x - ax), int(209 - ay)), spr)
    # Hijikata's cigarette still glows in the dark
    pset(img, 318, 175, (255, 120, 60))
    pset(img, 317, 175, (255, 200, 120))
    # one ember did NOT burn out ... it is falling back down (whistle)
    if 13.0 <= t < T_S6:
        kk = (t - 13.0) / (T_S6 - 13.0)
        ex, ey = lerp(mx, 196, kk), my + 150 * kk * kk
        d = ImageDraw.Draw(img)
        for i in range(1, 12):
            k2 = max(0.0, kk - i * 0.016)
            q = (lerp(mx, 196, k2), my + 150 * k2 * k2)
            d.rectangle([q[0], q[1], q[0] + (1 if i < 5 else 0), q[1]], fill=FW_GOLD[min(3, i // 3)])
        glow(img, ex, ey, 7, (255, 170, 80), 0.7)
        d.ellipse([ex - 2, ey - 2, ex + 2, ey + 2], fill=(254, 174, 52))
        d.rectangle([ex - 1, ey - 1, ex + 1, ey + 1], fill=(255, 250, 210))
        if step_frame(t, 12) % 2:
            fx.sparkle(img, int(ex), int(ey), t, t - 0.05, 4, (255, 240, 170))
    sfx_text(img, mx + 58, my + 44, "咚——!", t, 12.9, 0.6, size=20, color=(255, 240, 180), angle=-6)
    fx.flash(img, 0.5 * (1 - seg(t, 12.9, 13.02)) if t >= 12.9 else 0)
    dx, dy = fx.shake_offset(t, 12.9, 0.3, 3, seed=7)
    fx.shift(img, dx, dy)


def afro_flame(img, x, y, t, t0):
    """A little flame that catches on top of the afro (x, y = base, pre-zoom)."""
    if t < t0:
        return
    g = ease_out_back(seg(t, t0, t0 + 0.18))
    f = step_frame(t, 12, 3)
    h = (6 + (f % 2) * 2) * g
    lean = (f - 1) * 1.0
    d = ImageDraw.Draw(img)
    d.polygon([(x - 4 * g, y + 1), (x - 3 * g, y - h * 0.45), (x + lean, y - h), (x + 3 * g, y - h * 0.4),
               (x + 4 * g, y + 1)], fill=(247, 118, 34), outline=INK)
    d.polygon([(x - 2 * g, y), (x + lean * 0.5, y - h * 0.62), (x + 2 * g, y)], fill=(255, 226, 90))
    pset(img, x, y - 1, (255, 255, 220))
    for i in range(2):                                  # little smoke curls
        ph = ((t - t0) * 1.6 + i * 0.5) % 1.0
        r = 0.8 + ph * 1.8
        px, py = x + lean + wave(ph, 1.0, 2, i * 0.3), y - h - 2 - ph * 12
        d.ellipse([px - r, py - r, px + r, py + r], fill=(120, 112, 124))


def waterfall_tears(img, eyes, t, amp=1.0):
    """Anime waterfall tears gushing sideways from both eyes (pre-zoom coords)."""
    d = ImageDraw.Draw(img)
    f = step_frame(t, 16)
    for side, (ex, ey) in zip((-1, 1), eyes):
        prev = None
        for j in range(14):
            u = j / 13.0
            px = ex + side * (1 + u * 15 * amp)            # gushes out sideways, then falls
            py = ey + u * u * 25 * amp
            if prev is not None and (j + f) % 4 != 0:
                d.line([prev, (px, py)], fill=(120, 200, 255), width=2)
                if (j + f) % 4 == 1:
                    pset(img, px, py - 1, (235, 250, 255))
            prev = (px, py)
        # splashes where the streams hit the ground
        if amp > 0.9:
            for q in range(3):
                if (f + q + (side > 0)) % 2 == 0:
                    pset(img, ex + side * (15 + q * 2), ey + 24 - q * 2 - (f % 2), (170, 225, 255))


T_SHOUT, T_CRY, T_FIRE = 15.35, 16.1, 17.05


def s6_cam(t):
    k = lerp(2.5, 2.72, ease_in_out(seg(t, T_S6, T_SHOUT)))
    cy = 139
    if T_SHOUT <= t < T_CRY + 0.3:
        punch = ease_out_back(seg(t, T_SHOUT, T_SHOUT + 0.16)) * (1 - ease_in_out(seg(t, T_CRY, T_CRY + 0.3)))
        k += 0.45 * punch
        cy -= 3 * punch
    elif t >= T_CRY + 0.3:
        k = lerp(2.72, 2.9, ease_out(seg(t, T_CRY + 0.3, T_END)))
    return k, 198, cy


def shot_s6(img, t):
    cam = K.YOROZUYA_X - 200 + 6 * (T_S6 - T_S4) + 2 * (t - T_S6)
    _gintoki_street(img, t, cam)
    gx = 196
    f10 = step_frame(t, 10)
    # ---------------- Gintoki: dazed -> cough -> shout at the sky -> waterfall tears
    if t < 15.05:
        expr = "blink" if 14.93 <= t < 15.02 else "shock"
        kw = dict(arm_f=24, arm_b=-24, bob=0, lean=(1 if step_frame(t, 5) % 2 else -1) if t >= 14.55 else 0)
    elif t < T_SHOUT:
        expr = "talk"
        kw = dict(arm_f=40, arm_b=-10, bob=-1 if t < 15.14 else 0, head_dy=1)
    elif t < T_CRY:
        expr = "yell" if f10 % 2 == 0 else "shout"
        sh = math.sin(t * 34)
        kw = dict(arm_f=122 + 16 * sh, arm_b=-132 - 16 * sh, lean=-1, bob=-1 if f10 % 2 == 0 else 0,
                  legs="spread")
    else:
        expr = "wail" if step_frame(t, 6) % 3 else "cry"
        kw = dict(arm_f=8, arm_b=-8, bob=-1 if f10 % 2 else 0, head_dx=(f10 % 2), lean=0)
    info = draw_soot_gintoki(img, gx, FLOOR, "idle", t, expr=expr, **kw)
    top = info["top"] if info else (gx, FLOOR - 48)
    # the afro keeps smoking
    d = ImageDraw.Draw(img)
    for i in range(3):
        ph = ((t - T_S6) * 0.8 + i / 3) % 1.0
        r = 1 + ph * 3
        px = top[0] - 8 + i * 7 + ph * 5
        py = top[1] + 2 - ph * 20
        c = (130, 124, 136) if ph < 0.6 else (100, 94, 108)
        d.ellipse([px - r, py - r, px + r, py + r], fill=c)
    # cough: a puff of black smoke from the mouth
    if info:
        mx, my = info["head"][0] + 2, info["eyes"][0][1] + 3
        fx.smoke_puff(img, t, 15.06, mx + 3, my, size=7, seed=60, color=(70, 64, 76), life=0.7)
    if t >= T_CRY and info:
        waterfall_tears(img, info["eyes"], t, amp=clamp((t - T_CRY) / 0.2))
    # falling glitter from the fireworks
    for i in range(16):
        r = rng("glit", i)
        yy = (r.uniform(-60, 140) + (t - T_S6) * r.uniform(18, 30)) % 150
        xx = r.uniform(90, 300) + wave(t, 0.7, 3, r.random())
        if (step_frame(t, 10) + i) % 4:
            pset(img, xx, yy + 40, (FW_GOLD[1], FW_PINK[1], FW_CYAN[1])[i % 3])
    # the very last spark drifts down ... and sets the afro on fire (he doesn't notice)
    if 16.75 <= t < T_FIRE:
        kk = seg(t, 16.75, T_FIRE)
        sx = top[0] + 3 + wave(t, 2.5, 3) * (1 - kk)
        sy = lerp(88, top[1] + 1, kk)
        pset(img, sx, sy, (255, 250, 200))
        pset(img, sx, sy - 1, (255, 200, 80))
        pset(img, sx - 1, sy - 2, (254, 174, 52))
    afro_flame(img, top[0] + 3, top[1] + 2, t, T_FIRE)
    # ---------------- camera
    k, cx, cy = s6_cam(t)
    fx.zoom(img, k, cx, cy)
    u = t - T_S6
    if T_SHOUT <= t < T_CRY:
        hx, hy = zpt(gx, FLOOR - 30, k, cx, cy)
        fx.speed_lines(img, t, int(hx), int(hy), color=(255, 255, 255), count=44, inner=96, seed=13)
    # blast that lands on him (the stray firework) + black smoke clearing
    if u < 0.85:
        d = ImageDraw.Draw(img)
        for i in range(16):
            r = rng("smk", i)
            a = r.uniform(0, 2 * math.pi)
            dist = r.uniform(0, 60) + max(0.0, u - 0.12) * 170
            px = W / 2 + math.cos(a) * dist
            py = H / 2 - 16 + math.sin(a) * dist * 0.7 + u * 20
            rad = r.uniform(24, 42) * (1 - u / 0.85)
            if rad > 1:
                c = (44, 40, 50) if i % 2 else (66, 60, 72)
                d.ellipse([px - rad, py - rad, px + rad, py + rad], fill=c)
    fx.explosion(img, t, T_S6, W // 2, H // 2 - 20, size=64, seed=81, smoke=False)
    fx.flash(img, 0.85 * (1 - seg(t, T_S6, T_S6 + 0.14)), (255, 236, 190))
    sfx_text(img, 108, 52, "轰!!", t, T_S6, 0.5, size=40, color=(255, 200, 70), angle=-10)
    if 15.06 <= t < 15.5:
        fx_, fy_ = zpt(gx + 10, FLOOR - 30, k, cx, cy)
        sfx_text(img, int(fx_) + 22, int(fy_) - 12, "咳", t, 15.06, 0.44, size=18, color=(230, 230, 236), angle=-8)
    # crow crossing the sky: 「阿呆～」
    if 14.45 <= t < 15.6:
        uu = seg(t, 14.45, 15.6)
        crx, cry = int(lerp(W + 20, -30, uu)), int(30 + wave(t, 1.5, 4))
        crow(img, crx, cry, t, scale=2)
        if 14.75 <= t < 15.45:
            sfx_text(img, crx + 26, cry + 14, "阿呆～", t, 14.75, 0.7, size=14, color=(255, 255, 255), angle=6)
    if T_FIRE <= t < T_FIRE + 0.5:
        fx_, fy_ = zpt(top[0] + 3, top[1], k, cx, cy)
        sfx_text(img, int(fx_) + 18, int(fy_) - 4, "啵", t, T_FIRE, 0.5, size=16, color=(255, 200, 80), angle=10)
    dx, dy = fx.shake_offset(t, T_S6, 0.45, 5, seed=8)
    dx2, dy2 = fx.shake_offset(t, T_SHOUT, 0.35, 3, seed=9)
    fx.shift(img, dx + dx2, dy + dy2)


# ====================================================================== scene
class S05Katsura(Scene):
    id = "s05"
    title = "桂与伊丽莎白"
    duration = T_END
    music = "comedy"
    music_vol = 0.5
    subs = [
        (0.25, 2.00, "hijikata", "给我站住，桂！"),
        (2.05, 3.60, "okita", "假发——"),
        (3.95, 5.75, "katsura", "不是假发，是桂！"),
        (7.88, 9.50, "katsura", "后会有期！"),
        (10.80, 12.48, "gintoki", "炸、炸弹！？"),
        (15.10, 17.72, "gintoki", "为什么每次倒霉的都是我啊！"),
    ]

    def render(self, img, t):
        if t < T_S1B:
            shot_s1a(img, t)
        elif t < T_S2A:
            shot_s1b(img, t)
        elif t < T_S2B:
            shot_s2a(img, t)
        elif t < T_S3:
            shot_s2b(img, t)
        elif t < T_S4:
            shot_s3(img, t)
        elif t < T_S5:
            shot_s4(img, t)
        elif t < T_S6:
            shot_s5(img, t)
        else:
            shot_s6(img, t)

    def cues(self):
        return [
            # S1a chase
            Cue(0.0, "run", vol=0.45, dur=2.0),
            Cue(0.0, "wind", vol=0.2, dur=5.6),
            Cue(0.35, "vein", vol=0.5),
            Cue(1.20, "bazooka"),
            Cue(1.22, "whoosh", vol=0.6),
            Cue(1.50, "explosion_small"),
            Cue(1.52, "jump", vol=0.5),
            Cue(1.88, "land", vol=0.4),
            # S1b Okita
            Cue(2.0, "run", vol=0.25, dur=1.6),
            Cue(2.34, "blip", vol=0.5),
            Cue(2.78, "blip", vol=0.6),
            Cue(2.86, "blip", vol=0.6),
            Cue(3.00, "bazooka"),
            Cue(3.02, "whoosh", vol=0.6, pan=0.4),
            Cue(3.35, "explosion_small", vol=0.5, pan=0.7),
            # S2 turn + catchphrase
            Cue(3.61, "record_scratch"),
            Cue(3.80, "whoosh", vol=0.5),
            Cue(3.95, "shine", vol=0.5),
            Cue(4.02, "impact", vol=0.7),
            Cue(4.38, "punch_big"),
            Cue(4.40, "impact", vol=0.8),
            # S3 intros, signs, bomb
            Cue(5.62, "slide_up", vol=0.4),
            Cue(6.05, "pop"),
            Cue(6.40, "crow"),
            Cue(7.25, "whoosh", vol=0.7),
            Cue(7.45, "explosion_small", vol=0.7, pan=0.7),
            Cue(7.48, "pop"),
            Cue(7.52, "sweat", vol=0.6),
            Cue(7.50, "slide_up", vol=0.35),
            Cue(7.85, "bomb_fuse", vol=0.7),
            Cue(8.80, "whoosh", vol=0.7),
            Cue(9.05, "dash"),
            # S4 street
            Cue(9.5, "crowd", vol=0.25, dur=3.0),
            Cue(9.5, "footsteps", vol=0.35, dur=0.7),
            Cue(9.75, "fall_whistle", vol=0.7),
            Cue(10.45, "pop"),
            Cue(10.47, "slap", vol=0.4),
            Cue(10.55, "bomb_fuse", vol=0.6),
            Cue(11.00, "shock"),
            Cue(11.05, "sweat", vol=0.6),
            Cue(11.75, "run", vol=0.5, dur=0.45),
            Cue(12.22, "whoosh"),
            # S5 fireworks
            Cue(12.5, "slide_up", vol=0.7),
            Cue(12.9, "explosion"),
            Cue(13.08, "explosion_small", vol=0.6, pan=-0.5),
            Cue(13.15, "cheer", vol=0.45),
            Cue(13.22, "explosion_small", vol=0.6, pan=0.5),
            Cue(13.36, "explosion_small", vol=0.5),
            Cue(13.40, "sparkle"),
            Cue(12.98, "fall_whistle", vol=0.55),
            Cue(13.72, "pop", vol=0.5, pan=-0.6),
            Cue(13.86, "pop", vol=0.5, pan=0.6),
            # S6 the stray ember lands on Gintoki
            Cue(14.20, "explosion"),
            Cue(14.50, "crow"),
            Cue(15.06, "cough"),
            Cue(15.35, "impact", vol=0.6),
            Cue(15.36, "vein", vol=0.5),
            Cue(16.10, "fail", vol=0.55, pitch=1.4),
            Cue(17.05, "pop", vol=0.6),
            Cue(17.07, "fire", vol=0.35, dur=0.73),
        ]


SCENE = S05Katsura()
