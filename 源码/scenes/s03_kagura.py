"""s03 神乐与定春 (18 s, music 'comedy').

SHOT LIST (scene-local seconds)
A  0.00-4.90  NIGHT KABUKICHO STREET
   0.00-1.40  tracking shot (zoom 1.5): Gintoki putters along on his scooter picking his nose,
              headlight beam on the road; Kagura sprints in from the right.
   1.40       CRASH: 2-frame punch-in impact frame (paper / negative), then burst + 「咚!!」;
              Kagura spins high through the air; the scooter is left dented and smoking.
   2.15       she lands flat (thud + dust).  2.25-2.60 awkward silence, a crow flaps past.
   2.50-2.75  she springs up and hops right into his face.
   2.75-4.90  CUT close two-shot (zoom 2.1, slow push): Kagura's tsukkomi point with speed
              lines, Gintoki trembling/sweating.  sub 「喂！你撞到人了阿鲁！」  name_card 神乐.
B  4.90-7.90  SAME STREET, new set-up
   4.90-5.45  wide (zoom 1.35): three yakuza (suits + shades) charge in, 「站住!!」.
   5.45-5.85  extreme CU (zoom 3): Kagura levels her umbrella on a red speed-line field, glint.
   5.85-6.95  wide: UMBRELLA MACHINE GUN - muzzle flashes, tracers, flying casings, the thugs
              dance; 「哒哒哒哒!!」; 6.75 last blast sends them flying off-screen.
   6.95-7.90  CU (zoom 2.1): Gintoki peeking out from behind his scooter, trembling; Kagura
              blows the smoke off the tip.  sub 「这丫头……是怪物吗！？」
C  7.90-11.70 YOROZUYA OFFICE (night)
   7.90-8.75  medium (zoom 1.9) on Kagura inhaling rice; empty bowls fly onto a tower.
   8.75-9.75  medium (zoom 1.8) on Gintoki & Shinpachi: 「！？」, the wobbling tower grows out
              of the top of the frame.  sub 「再来一碗阿鲁！」
   9.75-11.70 insert (zoom 3.6-4.2) on the gama-guchi: it pops open, coins sprout wings and
              flutter off; 10.85 pull back: both cry under gloom lines, a moth 「空……」.
D  11.70-15.40 KABUKICHO STREET (next day)
   11.70-12.55 low CU (zoom 2.2): cardboard box 「请收养」 wiggles, Kagura pokes it, 「？」.
              narration 「第二天——」
   12.55-13.30 the box bursts: SADAHARU leaps out (way too big for it), camera snaps back to a
              group shot (zoom 1.55); name_card 定春; Gintoki & Shinpachi jump.
   13.30-15.40 Gintoki strolls up to pat him 「乖～」, red glint... CHOMP (13.65, punch-in +
              speed lines): Sadaharu rears up with Gintoki's head in his jaws, legs flailing,
              pixel blood, 「咔嚓!!」 「嚼」; Kagura cheers.  sub 「就叫你『定春』阿鲁！」
E  15.40-18.00 YOROZUYA FRONT at dusk, balcony (zoom 1.7)
   15.40-15.95 the team drops onto the balcony one by one (landings, dust, Sadaharu's thud).
   15.95      flash + speed lines + red band + brush text 「万事屋，集结！」 (zoom punch):
              Shinpachi on guard, Kagura under her parasol, Gintoki deadpan picking his nose.
   17.15      Sadaharu chomps Gintoki's head again and rears up with him (legs flailing).  fade.

Characters/poses: gintoki (nosepick/sit/shock/kneel/walk/idle/run/land/jump, expr cry),
kagura (run/fly/lie/jump/point/ready/umbrella_shoot/eat/kneel/cheer/umbrella_open/land),
shinpachi (sit/shock/cry/point/ready/land/jump), sadaharu (idle/jump/bite/sit),
private yakuza thugs + props in scenes/_s03_props.py.
"""
import math

from PIL import Image, ImageDraw, ImageChops, ImageOps

from engine.core import (Scene, Cue, W, H, seg, lerp, clamp, ease_in, ease_out, ease_in_out,
                         ease_out_back, wave, step_frame, rng, arc)
from engine.gfx import INK, rect, overlay_rect, pset, shade, silhouette
from engine import fx
from engine.text import sfx_text, name_card, text_sprite
from chars import draw_char, render_sprite, get_def
from bg import kabukicho as K, yorozuya as Y
from scenes import _s03_props as P

FLOOR = 160

# ---------------------------------------------------------------- timeline
B0, C0, D0, E0, END = 4.90, 7.90, 11.70, 15.40, 18.0

A_HIT, A_LAND, A_SPRING, A_CU = 1.40, 2.15, 2.50, 2.75
SX_HIT = 650                     # world x of the scooter at impact
KX_HIT = SX_HIT + 24             # Kagura at impact
KX_LAND = KX_HIT + 106           # where she crashes down
SKID = 18
SX_STOP = SX_HIT + SKID
KX_FACE = SX_STOP + 36           # she hops right into Gintoki's face

B_CU, B_FIRE, B_BLAST, B_GIN = 5.45, 5.85, 6.75, 6.95
CAM_B = 572
B_SCOOT = 100                    # scooter screen x in B
B_KAG = 170
B_THUGS = [(262, 5.05), (290, 5.15), (318, 5.25)]      # (stop x, arrival time)

C_SWITCH, C_WALLET = 8.75, 9.75
D_POP, D_WIDE, BITE_T = 12.55, 13.30, 13.55
E_TEXT, E_CHOMP = 15.95, 17.15


# ---------------------------------------------------------------- helpers
def zoom_view(img, k, cx, cy):
    """fx.zoom with the view clamped inside the canvas; returns the centre used."""
    if abs(k - 1) < 1e-3:
        return W / 2, H / 2
    hw, hh = W / (2 * k), H / (2 * k)
    cx, cy = clamp(cx, hw, W - hw), clamp(cy, hh, H - hh)
    fx.zoom(img, k, cx, cy)
    return cx, cy


def to_screen(x, y, k, c):
    return int((x - c[0]) * k + W / 2), int((y - c[1]) * k + H / 2)


def intro_card(img, t, t0, dur, cid, tag, title, desc):
    """name_card() whose small caption is a latin tag ('KAGURA') instead of repeating the
    Chinese name (the engine prints def.name next to the title -> '神乐 神乐')."""
    name_card(img, t, t0, dur, tag, title, desc, color=get_def(cid).color)


def rider(img, x, y, pose, t, **kw):
    """Gintoki sitting on the scooter whose ground point is (x, y)."""
    kw.setdefault("legs", "sit")
    draw_char(img, "gintoki", x + P.SC_SEAT[0], y + P.SC_SEAT[1], pose, t, shadow=False, **kw)


_BITE_MASK = {}


def _bite_mask(size, facing):
    key = (size, facing)
    m = _BITE_MASK.get(key)
    if m is None:
        w, h = size
        m = Image.new("L", size, 0)
        box = (45, 12, 76, 47)
        if facing < 0:
            box = (w - 1 - box[2], box[1], w - 1 - box[0], box[3])
        ImageDraw.Draw(m).ellipse(box, fill=255)
        _BITE_MASK[key] = m
    return m


def _rot_point(px, py, cx, cy, deg):
    """Where (px, py) lands after a PIL rotate(deg) (visually counter-clockwise) about (cx, cy)."""
    a = math.radians(deg)
    dx, dy = px - cx, py - cy
    return cx + dx * math.cos(a) + dy * math.sin(a), cy - dx * math.sin(a) + dy * math.cos(a)


def maw_pos(x, y, facing, tilt=0.0):
    mx, my = x + 22 * facing, y - 27
    if tilt:
        mx, my = _rot_point(mx, my, x - 14 * facing, y - 1, tilt * facing)
    return mx, my


def draw_bite(img, x, y, t, p, facing, victim=None, tilt=0.0):
    """Sadaharu biting: dog body, then the victim, then the dog's head over the victim's head.
    tilt (deg) rears the dog up about its hind feet. victim(mx, my) gets the maw position."""
    spr, ax, ay = render_sprite("sadaharu", "bite", t, p, None, facing)
    mask = ImageChops.multiply(spr.getchannel("A"), _bite_mask(spr.size, facing))
    if tilt:
        pad = 30
        big = Image.new("RGBA", (spr.width + 2 * pad, spr.height + 2 * pad), (0, 0, 0, 0))
        big.paste(spr, (pad, pad))
        bm = Image.new("L", big.size, 0)
        bm.paste(mask, (pad, pad))
        piv = (ax + pad - 14 * facing, ay + pad - 1)          # hind feet
        spr = big.rotate(tilt * facing, resample=Image.NEAREST, center=piv)
        mask = bm.rotate(tilt * facing, resample=Image.NEAREST, center=piv)
        ax, ay = ax + pad, ay + pad
    px, py = int(round(x - ax)), int(round(y - ay))
    if tilt:                                     # reared up: only the hind feet touch the ground
        overlay_rect(img, int(x - 8 * facing) - 15, y - 1, 30, 2, (0, 0, 0), 0.25)
    else:
        overlay_rect(img, x - 22, y - 1, 44, 2, (0, 0, 0), 0.25)
    img.paste(spr, (px, py), spr)
    if victim:
        victim(*maw_pos(x, y, facing, tilt))
    img.paste(spr, (px, py), mask)


def dangling_gintoki(img, mx, my, t, swing=-22, wob=7):
    """Gintoki hanging by the head from a maw at (mx, my): body swung out (swing deg, PIL CCW),
    legs + arms flailing. The sprite rotates about 14 px above the feet, so the feet anchor is
    placed such that the HEAD centre (22.5 px above the feet) stays in the maw."""
    th = swing + wob * math.sin(t * 13)
    r = math.radians(th)
    x = mx + 8.5 * math.sin(r)
    y = my + 14 + 8.5 * math.cos(r)
    draw_char(img, "gintoki", x, y, "run", t * 2.6, facing=1, shadow=False,
              arm_f=130 + 40 * math.sin(t * 26), arm_b=150 + 40 * math.cos(t * 23), rot=int(th))


def blood_drops(img, x, y, t, t0, seed=0, n=5, fall=26):
    """Stylised little red pixel drops dribbling from a bite (no gore)."""
    if t < t0:
        return
    for i in range(n):
        r = rng("blood", seed, i)
        period = r.uniform(0.35, 0.6)
        ph = ((t - t0) + r.uniform(0, period)) % period / period
        dx = r.uniform(-7, 7)
        yy = y + ph * ph * fall
        c = (214, 40, 56) if i % 2 else (160, 24, 44)
        rect(img, int(x + dx), int(yy), 1, 2, c)


def big_text(img, t, t0, text, x, y, size=34, color=(255, 236, 110), angle=-4):
    if t < t0:
        return
    p = t - t0
    spr = text_sprite(text, color, size, "brush", outline=INK, thick=2)
    k = 1.0
    if p < 0.14:
        k = lerp(2.4, 1.0, ease_out(p / 0.14))
    elif p < 0.26:
        k = 1.0 + 0.06 * math.sin((p - 0.14) / 0.12 * math.pi)
    if k != 1.0:
        spr = spr.resize((int(spr.width * k), int(spr.height * k)), Image.NEAREST)
    if angle:
        spr = spr.rotate(angle, resample=Image.NEAREST, expand=True)
    img.paste(spr, (int(x - spr.width / 2), int(y - spr.height / 2)), spr)


# ================================================================= shot A
A_ZOOM, A_CY = 1.5, 124


def scooter_x(t):
    if t < A_HIT:
        return SX_HIT - 125 * (A_HIT - t)
    return SX_HIT + SKID * ease_out(seg(t, A_HIT, A_HIT + 0.35))


def cam_a(t):
    if t < A_HIT:
        return scooter_x(t) - 150
    return SX_HIT - 150 + 40 * ease_in_out(seg(t, A_HIT, A_LAND))


def headlight(img, x, y, on=1.0):
    hx, hy = x + P.SC_LIGHT[0], y + P.SC_LIGHT[1]
    P.light_cone(img, [(hx, hy - 1), (hx + 86, hy - 14), (hx + 104, y + 2), (hx + 8, y + 2)],
                 (70, 62, 30), 0.55 * on)
    P.light_cone(img, [(hx + 10, y - 2), (hx + 60, y - 5), (hx + 96, y + 2), (hx + 14, y + 3)],
                 (80, 70, 36), 0.6 * on)


def scooter_damage(img, x, y, t, t0):
    """After the crash: dented, cracked front + a wisp of smoke (Kagura is fine, the SCOOTER isn't)."""
    if t < t0:
        return
    d = ImageDraw.Draw(img)
    sx0, sy0 = int(x) - P.SC_W // 2, int(y) - P.SC_H + 1
    # crumpled leg-shield + smashed headlight
    d.line([(sx0 + 30, sy0 + 5), (sx0 + 28, sy0 + 9), (sx0 + 31, sy0 + 12), (sx0 + 29, sy0 + 16)], fill=INK)
    rect(img, sx0 + 32, sy0 + 6, 3, 3, (70, 66, 80))
    pset(img, sx0 + 33, sy0 + 7, (160, 156, 120))
    # smoke wisps rising from the nose
    for i in range(4):
        ph = ((t - t0) * 1.3 + i / 4) % 1.0
        px = x + 13 + ph * 4 + math.sin(t * 3 + i * 2) * 2
        py = y - 20 - ph * 20
        r = 0.8 + ph * 2.4
        col = shade((120, 118, 138), 1.0 - ph * 0.25)
        d.ellipse([px - r, py - r, px + r, py + r], fill=col)


def draw_a_actors(dst, t, cam, sil=False):
    """Scooter + Gintoki + Kagura of the wide shot (also used for the impact-frame silhouettes)."""
    sx = scooter_x(t) - cam
    if t < A_HIT:
        P.draw_scooter(dst, sx, FLOOR, t)
        rider(dst, sx, FLOOR, "nosepick", t, arm_b=72)
    else:
        P.draw_scooter(dst, sx, FLOOR, t, moving=False)
        if not sil:
            scooter_damage(dst, sx, FLOOR, t, A_HIT + 0.3)
        lurch = 2 if t < A_HIT + 0.15 else 0
        if t < A_LAND:
            rider(dst, sx + lurch, FLOOR, "shock", t, p=seg(t, A_HIT, A_HIT + 1))
        else:
            rider(dst, sx, FLOOR, "sit", t, expr="shock", arm_f=72, arm_b=70)
    if t < A_HIT:
        kx = KX_HIT + 55 * (A_HIT - t) - cam
        if kx < W + 20:
            draw_char(dst, "kagura", kx, FLOOR, "run", t, facing=-1, expr="shout", shadow=not sil)
    elif t < A_LAND:
        k = seg(t, A_HIT, A_LAND)
        x, y = arc((KX_HIT, FLOOR), (KX_LAND, FLOOR), k, 64)
        if k < 0.9 and not sil:
            overlay_rect(dst, int(x - cam) - 6, FLOOR - 1, 12, 2, (0, 0, 0), 0.25 * (1 - k))
        draw_char(dst, "kagura", x - cam, y, "fly", t * 1.3, facing=-1, shadow=False)
    elif t < A_SPRING:
        draw_char(dst, "kagura", KX_LAND - cam, FLOOR + 11, "lie", t, facing=-1, shadow=False)
    else:
        k = seg(t, A_SPRING, A_CU)
        x, y = arc((KX_LAND, FLOOR), (KX_FACE, FLOOR), k, 34)
        draw_char(dst, "kagura", x - cam, y, "jump", t, facing=-1, expr="angry")


def impact_panel(img, t, cam):
    """Clean 2-frame anime impact frame: flat paper/ink, radial lines, pure silhouettes."""
    first = t < A_HIT + 1 / 30
    paper, ink, accent = (250, 246, 232), (14, 10, 20), (214, 40, 56)
    bg, fg = (paper, ink) if first else (ink, paper)
    img.paste(bg, (0, 0, W, H))
    ix, iy = KX_HIT - cam - 6, FLOOR - 16
    fx.speed_lines(img, t, ix, iy, color=accent if not first else ink, count=70, inner=26, seed=41)
    fx.comic_burst(img, ix, iy, 26, 9, 14, color=accent, outline=accent, rot=0.3)
    sx = scooter_x(t) - cam
    gin = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    P.draw_scooter(gin, sx, FLOOR, t, moving=False)
    rider(gin, sx + 2, FLOOR, "shock", t, p=0.05)
    kag = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    k = 0.1 + seg(t, A_HIT, A_HIT + 2 / 30) * 0.08
    x, y = arc((KX_HIT, FLOOR), (KX_LAND, FLOOR), k, 64)
    draw_char(kag, "kagura", x - cam + 8, y - 4, "fly", 0.05, facing=-1, shadow=False, expr="hurt")
    for layer in (gin, kag):
        rim = silhouette(layer, accent if first else paper)
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-2, 0), (2, 0)):
            img.paste(rim, (ox, oy), layer)
        if first:                                   # frame 1: full colour on paper
            img.paste(layer, (0, 0), layer)
        else:                                       # frame 2: negative
            neg = Image.merge("RGBA", ImageOps.invert(layer.convert("RGB")).split() + (layer.getchannel("A"),))
            img.paste(neg, (0, 0), layer)


def shot_a(img, t):
    cam = cam_a(t)
    if t >= A_CU:
        K.street(img, cam, t, "night")
        return shot_a_cu(img, t, cam)
    impact = A_HIT <= t < A_HIT + 2 / 30
    if impact:
        impact_panel(img, t, cam)
    else:
        K.street(img, cam, t, "night")
        sx = scooter_x(t) - cam
        if t < A_HIT + 0.3:                          # exhaust puffs
            for i in range(6):
                te = A_HIT - 0.1 - i * 0.22
                if te < t:
                    fx.smoke_puff(img, t, te, sx - 20 - (t - te) * 40, FLOOR - 4, size=4, seed=i,
                                  color=(110, 110, 140), life=0.5)
        headlight(img, sx, FLOOR, 1.0 if t < A_HIT or step_frame(t, 10) % 3 else 0.35)
        if A_HIT <= t < A_HIT + 0.6:                 # skid dust
            for i in range(3):
                fx.smoke_puff(img, t, A_HIT + i * 0.08, sx - 10 + i * 6, FLOOR - 1, size=6, seed=10 + i,
                              color=(150, 146, 170), life=0.5)
        if A_LAND <= t < A_SPRING:
            fx.smoke_puff(img, t, A_LAND, KX_LAND - cam, FLOOR - 1, size=10, seed=3,
                          color=(150, 146, 176), life=0.4)
        draw_a_actors(img, t, cam)
        if A_LAND <= t and t > 2.2:
            P.sweat_drop(img, sx - 14, FLOOR - 44 + (t - 2.2) * 10)
        # the awkward-silence crow flaps past the lit windows
        if 2.18 <= t < 2.75:
            k = seg(t, 2.18, 2.75)
            P.draw_crow(img, lerp(318, 120, k), 70 + wave(t, 3, 2), t)
        ix, iy = KX_HIT - cam - 6, FLOOR - 16
        if A_HIT <= t < A_HIT + 0.22:
            fx.comic_burst(img, ix, iy, 22 - (t - A_HIT) * 30, 10, 12, color=(255, 236, 120), rot=t * 3)
        fx.burst(img, t, A_HIT, ix, iy, n=18, colors=[(255, 255, 255), (255, 220, 90)], speed=(60, 150),
                 seed=7, life=0.5)
    # camera (the impact frames punch in hard on the collision)
    if impact:
        c = zoom_view(img, 2.6, KX_HIT - cam - 12, FLOOR - 22)
    else:
        c = zoom_view(img, A_ZOOM, 192, A_CY)
    dx, dy = fx.shake_offset(t, A_HIT, 0.4, 5, seed=1)
    ex, ey = fx.shake_offset(t, A_LAND, 0.2, 3, seed=2)
    fx.shift(img, dx + ex, dy + ey, fill=(14, 10, 20))
    sx_, sy_ = to_screen(KX_HIT - cam + 30, 96, A_ZOOM, c)
    sfx_text(img, sx_, sy_, "咚!!", t, A_HIT, 0.8, size=32, angle=-10)
    if 2.3 <= t < 2.75:
        gx, gy = to_screen(scooter_x(t) - cam - 8, FLOOR - 50, A_ZOOM, c)
        sfx_text(img, gx, gy, "……", t, 2.3, 0.45, size=16, color=(255, 255, 255), angle=0, shake=0)


def shot_a_cu(img, t, cam):
    sx = SX_STOP - cam
    kx = KX_FACE - cam
    p = t - A_CU
    if p < 0.5:
        fx.speed_lines(img, t, kx + 2, FLOOR - 20, color=(230, 230, 255), seed=3, inner=30,
                       alpha=1 - p * 1.4)
    headlight(img, sx, FLOOR, 0.8 if step_frame(t, 10) % 4 else 0.3)
    P.draw_scooter(img, sx, FLOOR, t, moving=False)
    scooter_damage(img, sx, FLOOR, t, A_HIT + 0.3)
    tremble = 1 if step_frame(t, 15) % 2 else 0
    if p < 0.4:
        rider(img, sx, FLOOR, "shock", t, p=p)
    else:
        rider(img, sx - tremble, FLOOR, "sit", t, expr="shock", arm_f=72, arm_b=70)
    # Kagura: lunges into his face, then stomps angrily while ranting
    lean = -4 * ease_out(seg(t, A_CU, A_CU + 0.15)) + 4 * ease_in_out(seg(t, 4.3, 4.6))
    hop = 0
    if t >= 3.5:
        ph = ((t - 3.5) / 0.34) % 1.0
        hop = -3 * math.sin(math.pi * min(1.0, ph / 0.5)) if ph < 0.5 else 0
        tl = 3.5 + math.floor((t - 3.5) / 0.34) * 0.34 + 0.17
        fx.smoke_puff(img, t, tl, kx + lean, FLOOR - 1, size=4, seed=int(tl * 10), color=(150, 146, 176),
                      life=0.25)
    draw_char(img, "kagura", kx + lean, FLOOR + hop, "point", t, p=seg(t, A_CU, A_CU + 0.8), facing=-1,
              expr="shout" if step_frame(t, 6) % 2 else "angry", shadow=hop == 0)
    for i, t0 in enumerate((3.2, 3.9, 4.5)):
        if t0 <= t < t0 + 0.7:
            P.sweat_drop(img, sx - 16 + i * 3, FLOOR - 46 + (t - t0) * 14)
    if p > 0.2:
        P.vein_mark(img, kx + lean - 9, FLOOR - 29 + hop, t)
    k = lerp(2.1, 2.25, ease_in_out(seg(t, A_CU, B0)))
    zoom_view(img, k, sx + 32, 133)
    dx, dy = fx.shake_offset(t, A_CU, 0.25, 3, seed=4)
    fx.shift(img, dx, dy)
    intro_card(img, t, 2.85, 2.05, "kagura", "KAGURA", "神乐", "夜兔族少女｜怪力·大胃王·『阿鲁』")


# ================================================================= shot B
def thug_x(i, t):
    x_stop, t_arr = B_THUGS[i]
    if t < t_arr:
        return lerp(x_stop + 150, x_stop, ease_out(seg(t, B0 + i * 0.1, t_arr)))
    if t < B_FIRE:
        return x_stop
    return x_stop + 22 * ease_out(seg(t, B_FIRE, B_BLAST))


def draw_thugs(img, t):
    for i, d in enumerate(P.YAKUZA):
        x = thug_x(i, t)
        _, t_arr = B_THUGS[i]
        if t < t_arr:
            P.draw_def(img, d, x, FLOOR, "run", t + i * 0.2, facing=-1, weapon=50, expr="shout")
        elif t < B_FIRE:
            P.draw_def(img, d, x, FLOOR, "ready", t + i * 0.3, facing=-1, expr="shout")
        elif t < B_BLAST:
            f = step_frame(t + i * 0.07, 15)
            jx = (f % 3) - 1
            if f % 4 < 2:
                P.draw_def(img, d, x + jx, FLOOR, "hit", t, p=0.15 + 0.2 * (f % 2), facing=-1,
                           flash=0.7 if f % 2 else 0.0)
            else:
                P.draw_def(img, d, x + jx, FLOOR - (f % 2), "shock", t, p=0.5, facing=-1, expr="hurt")
        else:
            k = seg(t, B_BLAST + i * 0.04, B_BLAST + 0.6 + i * 0.04)
            if k < 1:
                fxx = lerp(x, x + 170 + i * 30, ease_in(k) * 0.3 + k * 0.7)
                fy = FLOOR - 190 * k * (1.2 - k * 0.6) - i * 8 * k
                P.draw_def(img, d, fxx, fy, "fly", t * 1.4 + i, facing=-1, rot=int(t * 900 + i * 90) % 360)


def muzzle(t):
    lean = -1 if step_frame(t, 12) % 2 == 0 else 0
    return B_KAG + 27 + lean, FLOOR - 10


def cowering_gintoki(img, t, arm_f=110, arm_b=120):
    """Gintoki hiding BEHIND the (dented, smoking) scooter: only his head + hands peek over the seat."""
    shiver = 1 if step_frame(t, 15) % 2 else 0
    draw_char(img, "gintoki", B_SCOOT - 8 + shiver, FLOOR - 7, "kneel", t, expr="shock",
              arm_f=arm_f, arm_b=arm_b, shadow=False)
    P.draw_scooter(img, B_SCOOT, FLOOR, t, moving=False)
    scooter_damage(img, B_SCOOT, FLOOR, t, A_HIT + 0.3)
    # little tremble marks beside his head
    if step_frame(t, 10) % 2:
        d = ImageDraw.Draw(img)
        for sgn in (-1, 1):
            bx = B_SCOOT - 8 + sgn * 11
            d.line([(bx, FLOOR - 33), (bx + sgn, FLOOR - 31), (bx, FLOOR - 29)], fill=(220, 220, 240))


def shot_b(img, t):
    if B_CU <= t < B_FIRE:
        return shot_b_cu(img, t)
    if t >= B_GIN:
        return shot_b_gin(img, t)
    K.street(img, CAM_B + 10 * ease_out(seg(t, B0, B_CU)), t, "night")
    cowering_gintoki(img, t)
    headlight(img, B_SCOOT, FLOOR, 0.7)
    draw_thugs(img, t)
    firing = B_FIRE <= t < B_BLAST
    mx, my = muzzle(t)
    if t < B_CU:
        pose = "idle" if t < 5.2 else "ready"
        draw_char(img, "kagura", B_KAG, FLOOR, pose, t, facing=1,
                  expr="determined" if t > 5.15 else "normal")
    else:
        draw_char(img, "kagura", B_KAG, FLOOR, "umbrella_shoot" if firing else "ready", t,
                  facing=1, weapon=2 if firing else 8, arm_f=90)
        if firing:
            f30 = step_frame(t, 30)
            if f30 % 2 == 0:                    # muzzle flash + a warm light pool on the street
                P.light_cone(img, [(mx - 30, FLOOR + 2), (mx - 10, FLOOR - 26), (mx + 40, FLOOR - 26),
                                   (mx + 60, FLOOR + 2)], (90, 70, 20), 0.5)
                fx.comic_burst(img, mx + 4, my, 7 + f30 % 4, 2, 7, color=(255, 236, 140),
                               outline=(255, 150, 50), rot=f30 * 0.7)
                rect(img, mx + 2, my - 1, 4, 3, (255, 255, 240))
            r = rng("tracer", f30)
            d = ImageDraw.Draw(img)
            for j in range(5):
                i = r.randrange(3)
                tx = thug_x(i, t) + r.uniform(-5, 5)
                ty = FLOOR - r.uniform(6, 26)
                u = r.uniform(0.05, 0.75)
                p0 = (lerp(mx, tx, u), lerp(my, ty, u))
                p1 = (lerp(mx, tx, u + 0.2), lerp(my, ty, u + 0.2))
                d.line([p0, p1], fill=(255, 200, 80), width=2)
                d.line([(lerp(p0[0], p1[0], 0.4), lerp(p0[1], p1[1], 0.4)), p1], fill=(255, 255, 230), width=1)
                if r.random() < 0.7:
                    pset(img, tx + r.randint(-2, 2), ty + r.randint(-2, 2), (255, 255, 200))
                    pset(img, tx + r.randint(-3, 3), ty + r.randint(-3, 3), (255, 200, 80))
            for i in range(24):                 # ejected casings
                te = B_FIRE + i * 0.04
                dt = t - te
                if 0 <= dt < 0.7:
                    rr = rng("casing", i)
                    vx, vy = -rr.uniform(25, 60), -rr.uniform(60, 110)
                    cx = B_KAG + 10 + vx * dt
                    cy = min(FLOOR - 1, FLOOR - 16 + vy * dt + 300 * dt * dt)
                    rect(img, int(cx), int(cy), 2 if (int(dt * 20) % 2) else 1, 1, (240, 190, 70))
        elif t >= B_BLAST:
            fx.smoke_puff(img, t, B_BLAST, mx + 6, my, size=10, seed=5, color=(200, 200, 214), life=0.5)
            fx.burst(img, t, B_BLAST, 292, FLOOR - 16, n=20, colors=[(255, 240, 150), (255, 150, 60)],
                     speed=(70, 180), seed=9, life=0.45)
            if t < B_BLAST + 0.12:
                fx.comic_burst(img, mx + 6, my, 16, 7, 10, color=(255, 230, 110))
    # camera
    z = 1.35
    c = zoom_view(img, z, 205, 124)
    if t >= B_FIRE:
        dx, dy = fx.shake_offset(t, B_FIRE, B_BLAST - B_FIRE + 0.1, 2, freq=40, seed=5)
        ex, ey = fx.shake_offset(t, B_BLAST, 0.3, 5, seed=6)
        fx.shift(img, dx + ex, dy + ey)
        sfx_text(img, 240, 46, "哒哒哒哒!!", t, B_FIRE + 0.05, B_BLAST - B_FIRE, size=26, angle=-6)
        if B_BLAST <= t < B_BLAST + 0.06:
            fx.flash(img, 0.6)
        if t >= B_BLAST:
            bx, by = to_screen(mx + 10, my - 14, z, c)
            sfx_text(img, bx, by, "轰!", t, B_BLAST, 0.5, size=22, angle=8)
    if 5.0 <= t < 5.45:
        tx, ty = to_screen(300, 106, z, c)
        sfx_text(img, tx, ty, "站住!!", t, 5.0, 0.45, size=16, color=(255, 255, 255), angle=6)


def shot_b_cu(img, t):
    K.street(img, CAM_B + 10, t, "night")
    fx.grade(img, (0.45, 0.22, 0.26), (40, 6, 12))
    fx.speed_lines(img, t, B_KAG + 6, FLOOR - 18, color=(255, 150, 110), seed=8, count=56, inner=28)
    k = seg(t, B_CU, B_CU + 0.18)
    draw_char(img, "kagura", B_KAG, FLOOR, "ready", t, facing=1, weapon=lerp(80, 2, ease_out(k)),
              arm_f=lerp(140, 88, ease_out(k)), arm_b=70, expr="determined")
    z = lerp(3.4, 3.0, ease_out(seg(t, B_CU, B_FIRE)))
    c = zoom_view(img, z, B_KAG + 12, FLOOR - 16)
    tx, ty = to_screen(B_KAG + 27, FLOOR - 10, z, c)
    fx.sparkle(img, tx, ty, t, 5.62, size=12)
    fx.sparkle(img, tx - 1, ty, t, 5.66, size=7, color=(255, 240, 180))


def shot_b_gin(img, t):
    K.street(img, CAM_B + 10, t, "night")
    cowering_gintoki(img, t, arm_f=125, arm_b=115)
    # Kagura blowing the smoke off her umbrella tip
    draw_char(img, "kagura", B_KAG, FLOOR, "ready", t, facing=1, weapon=82, arm_f=60, arm_b=-10,
              expr="smug" if step_frame(t, 3) % 3 else "blink")
    tipx, tipy = B_KAG + 11, FLOOR - 24
    d = ImageDraw.Draw(img)
    for i in range(5):
        ph = ((t - B_GIN) * 0.9 + i / 5) % 1.0
        sx = tipx + wave(t + i, 0.9, 2 + ph * 3) + ph * 4
        sy = tipy - ph * 22
        rr = 0.5 + ph * 2.0
        col = shade((210, 210, 226), 1 - ph * 0.4)
        d.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=col)
    gx = B_SCOOT - 8
    for i, t0 in enumerate((7.05, 7.45)):
        if t0 <= t < t0 + 0.6:
            P.sweat_drop(img, gx + 11 + i * 2, FLOOR - 40 + (t - t0) * 12)
    k = lerp(2.1, 2.25, ease_in_out(seg(t, B_GIN, C0)))
    zoom_view(img, k, (gx + B_KAG) / 2 + 2, 133)


# ================================================================= shot C
TOWER_X = 168                 # bowl tower base centre on the low table
KAG_C = Y.SOFA_L_X + 4
GIN_C, SHIN_C = Y.SOFA_R_X - 10, Y.SOFA_R_X + 14
C_B0, C_DT, C_MAX = C0 + 0.15, 0.085, 22


def n_bowls(t):
    return min(C_MAX, 2 + int(max(0.0, t - C_B0) / C_DT))


def bowl_pos(i, t):
    wob = math.sin(t * 5.0 + i * 0.45) * (i / 16.0) ** 2 * 4.0
    return TOWER_X + wob, Y.TABLE_Y - 5 - i * 5


def draw_tower(img, t):
    n = n_bowls(t)
    bs = P.bowl_sprite(False)
    for i in range(n):
        x, y = bowl_pos(i, t)
        img.paste(bs, (int(x - P.BOWL_W // 2), int(y)), bs)
    if n < C_MAX:                               # the next bowl in flight
        tn = C_B0 + (n - 1) * C_DT
        k = seg(t, tn, tn + C_DT)
        tx, ty = bowl_pos(n, t)
        x, y = arc((KAG_C + 10, Y.SOFA_SEAT_Y - 12), (tx, ty), k, 18)
        img.paste(bs, (int(x - P.BOWL_W // 2), int(y)), bs)


def shot_c(img, t):
    if t >= C_WALLET:
        return shot_c_wallet(img, t)
    Y.office(img, t, "night")
    te = t * 1.8
    f = step_frame(te, 6, 2)
    draw_char(img, "kagura", KAG_C, Y.SOFA_SEAT_Y, "eat", te, facing=1)
    hx, hy = (KAG_C + 6, Y.SOFA_SEAT_Y - 13) if f else (KAG_C + 9, Y.SOFA_SEAT_Y - 9)
    sb = P.small_bowl_sprite()
    img.paste(sb, (hx - 4, hy - 3), sb)
    if f:
        tb = math.floor(t * 3.6) / 3.6
        fx.burst(img, t, tb, KAG_C + 9, Y.SOFA_SEAT_Y - 19, n=7, colors=[(255, 255, 255)],
                 speed=(20, 60), gravity=200, life=0.4, seed=int(t * 3.6), spread=(-160, -20))
    draw_tower(img, t)
    for cid, x, dl in (("gintoki", GIN_C, 0.0), ("shinpachi", SHIN_C, 0.08)):
        if t < C_SWITCH + dl:
            draw_char(img, cid, x, Y.SOFA_SEAT_Y, "sit", t, facing=-1, expr="normal")
        else:
            draw_char(img, cid, x, Y.SOFA_SEAT_Y, "shock", t, p=seg(t, C_SWITCH + dl, C_SWITCH + 1 + dl),
                      facing=-1, legs="sit")
    if t >= C_SWITCH:
        for i, t0 in enumerate((9.05, 9.3)):
            if t0 <= t < t0 + 0.6:
                P.sweat_drop(img, GIN_C - 11 + i * 24, Y.SOFA_SEAT_Y - 36 + (t - t0) * 12)
    if t < C_SWITCH:
        z = lerp(2.3, 2.5, ease_out(seg(t, C0, C_SWITCH)))
        c = zoom_view(img, z, 132, 132)
    else:
        z = lerp(1.8, 1.9, seg(t, C_SWITCH, C_WALLET))
        c = zoom_view(img, z, 240, 128)
        if t < C_SWITCH + 0.5:                       # 集中線 on the two stunned faces
            sx_, sy_ = to_screen((GIN_C + SHIN_C) / 2, Y.SOFA_SEAT_Y - 20, z, c)
            fx.speed_lines(img, t, sx_, sy_, color=(255, 255, 255), seed=17, count=34, inner=64,
                           alpha=1 - seg(t, C_SWITCH, C_SWITCH + 0.5))
        dx, dy = fx.shake_offset(t, C_SWITCH, 0.2, 2, seed=14)
        fx.shift(img, dx, dy)
        qx, qy = to_screen((GIN_C + SHIN_C) / 2, Y.SOFA_SEAT_Y - 44, z, c)
        sfx_text(img, qx, qy - 4, "！？", t, C_SWITCH + 0.02, 0.9, size=28, color=(255, 255, 255), angle=0)
    if t < C_SWITCH:
        kx, ky = to_screen(KAG_C + 20, Y.SOFA_SEAT_Y - 44, z, c)
        for i, t0 in enumerate((8.0, 8.25, 8.5)):
            sfx_text(img, kx + (i % 2) * 30 - 6, ky - i * 8 + 6, "扒!", t, t0, 0.3, size=20,
                     color=(255, 255, 255), angle=10 - i * 10)


C_OPEN, C_PULL = C_WALLET + 0.25, 10.85


def shot_c_wallet(img, t):
    """Insert on the gama-guchi: it opens, the coins sprout wings and flutter off... then pull back
    to reveal Gintoki & Shinpachi weeping under gloom lines while a lone moth flies out."""
    Y.office(img, t, "night")
    fx.grade(img, (0.62, 0.66, 0.9), (0, 0, 10))
    P.tate_lines(img, 236, 60, 350, 132, t, color=(54, 62, 130), gap=3)
    wx, wy = GIN_C - 19, Y.SOFA_SEAT_Y - 11         # held out at arm's length (facing left)
    draw_char(img, "gintoki", GIN_C, Y.SOFA_SEAT_Y, "sit", t, facing=-1, expr="cry", arm_f=100, arm_b=60)
    draw_char(img, "shinpachi", SHIN_C, Y.SOFA_SEAT_Y, "cry", t, facing=-1, legs="sit")
    opened = t >= C_OPEN
    ws = P.wallet_sprite(opened)
    jig = 1 if (C_OPEN <= t < C_OPEN + 0.12 and step_frame(t, 20) % 2) else 0
    img.paste(ws, (wx - ws.width // 2, wy - ws.height + 2 - jig), ws)
    top = wy - ws.height + 7
    for i in range(4):                               # coins sprout wings and escape one by one
        t0 = C_OPEN + 0.1 + i * 0.2
        u = (t - t0) / 1.2
        if 0 <= u < 1:
            x = wx - 2 + i * 2 - (26 + i * 9) * u + math.sin(u * 9 + i) * 4
            y = top - 3 - 62 * ease_in(u) - 16 * u
            P.draw_coin(img, x, y, t, seed=i)
            if u < 0.08:
                fx.sparkle(img, int(x), int(y), t, t0, size=4, color=(255, 240, 160))
    t0 = C_PULL + 0.15
    if t >= t0:                                      # ...then only a moth
        u = (t - t0) / 0.9
        P.draw_moth(img, wx + math.sin(u * 8) * 5 - 6 * u, top - 3 - 24 * min(u, 1.2), t)
    if t >= C_PULL:
        for cx_ in (GIN_C, SHIN_C):                  # tears streaming
            for j in range(3):
                ph = ((t * 2.2) + j / 3) % 1
                pset(img, cx_ - 5 - (j % 2) * 5, Y.SOFA_SEAT_Y - 23 + ph * 7, (130, 200, 255))
    # camera: tight insert on the purse, then pull back to the two sad faces
    if t < C_PULL:
        k = ease_out(seg(t, C_WALLET, C_WALLET + 0.3))
        z = lerp(4.2, 3.6, k)
        c = zoom_view(img, z, wx + 8, lerp(wy - 4, wy - 10, ease_in_out(seg(t, C_OPEN, C_PULL))))
    else:
        k = ease_in_out(seg(t, C_PULL, C_PULL + 0.35))
        z = lerp(3.6, 2.7, k)
        c = zoom_view(img, z, lerp(wx + 8, GIN_C + 6, k), lerp(wy - 10, 134, k))
    if C_OPEN <= t < C_OPEN + 0.5:
        px_, py_ = to_screen(wx - 12, wy - 16, z, c)
        sfx_text(img, px_, py_, "啪!", t, C_OPEN, 0.5, size=22, color=(255, 255, 255), angle=-10)
    if t >= t0:
        mx_, my_ = to_screen(wx - 22, wy - 22, z, c)
        sfx_text(img, mx_, my_, "空……", t, t0 + 0.1, 0.75, size=20, color=(200, 210, 255), angle=0, shake=0)


# ================================================================= shot D
CAM_D = K.YOROZUYA_X - W // 2 + 20
BOX_X = 262
SADA_X = 214                 # where Sadaharu lands after leaping out of the box
MAW = (SADA_X - 22, FLOOR - 27)
GIN_D0, SHIN_D, KAG_D = 146, 116, 300


D_CHOMP = BITE_T + 0.1          # the jaws snap shut
D_TILT = 26                     # Sadaharu rears up this much (deg) with Gintoki in his mouth


def gin_d_x(t):
    return lerp(GIN_D0, MAW[0] - 6, ease_in_out(seg(t, 12.95, 13.33)))


def d_tilt(t):
    k = ease_out(seg(t, D_CHOMP, D_CHOMP + 0.22))
    return D_TILT * k + 2.5 * k * math.sin((t - D_CHOMP) * 11)


def shot_d(img, t):
    K.street(img, CAM_D, t, "day")
    flap = ease_out(seg(t, D_POP, D_POP + 0.12))
    wig = 0
    if t < D_POP:
        for w0 in (11.95, 12.3):
            if w0 <= t < w0 + 0.16:
                wig = 1 if step_frame(t, 20) % 2 else -1
    # Shinpachi
    if t < 12.7:
        draw_char(img, "shinpachi", SHIN_D, FLOOR, "idle", t)
    elif t < D_CHOMP + 0.05:
        draw_char(img, "shinpachi", SHIN_D, FLOOR, "shock", t, p=seg(t, 12.7, 13.7))
    else:
        draw_char(img, "shinpachi", SHIN_D, FLOOR, "point", t, p=seg(t, D_CHOMP + 0.05, D_CHOMP + 0.6),
                  expr="shout")
    # the box (back part) + Sadaharu inside / leaping out
    P.draw_box_back(img, BOX_X + wig, FLOOR, flap)
    if t < D_POP:
        if t > 12.2:                                 # a tuft of white fur peeks out
            d = ImageDraw.Draw(img)
            d.ellipse([BOX_X - 4, FLOOR - 27, BOX_X + 4, FLOOR - 21], fill=(240, 242, 252), outline=INK)
        P.draw_box_front(img, BOX_X + wig, FLOOR, flap)
    else:
        P.draw_box_front(img, BOX_X, FLOOR, flap)
    leap = seg(t, D_POP, D_POP + 0.32)
    gin_bitten = t >= D_CHOMP
    if D_POP <= t < D_POP + 0.32:
        x, y = arc((BOX_X, FLOOR - 4), (SADA_X, FLOOR), leap, 38)
        draw_char(img, "sadaharu", x, y, "jump", t, facing=-1, expr="happy", shadow=False)
    # Gintoki (not yet bitten)
    if t < D_CHOMP:
        gx = gin_d_x(t)
        if t < 12.7:
            draw_char(img, "gintoki", gx, FLOOR, "nosepick", t)
        elif t < 12.95:
            draw_char(img, "gintoki", gx, FLOOR, "shock", t, p=seg(t, 12.7, 13.2))
        elif t < 13.33:
            draw_char(img, "gintoki", gx, FLOOR, "walk", t, expr="normal")
        else:                                        # cocky: reaches up to pat the big doggy
            reach = ease_out(seg(t, 13.33, 13.5))
            draw_char(img, "gintoki", gx, FLOOR, "idle", t, arm_f=lerp(20, 155, reach), arm_b=-10,
                      expr="smug" if t < BITE_T else "shock")
    if t >= D_POP + 0.32:
        if t < BITE_T:
            draw_char(img, "sadaharu", SADA_X, FLOOR, "idle", t, facing=-1,
                      expr="happy" if t < 13.05 else ("normal" if t < 13.4 else "angry"))
            if t >= 13.4:                            # predatory glint in his eye
                fx.sparkle(img, SADA_X - 25, FLOOR - 36, t, 13.4, size=5, color=(255, 90, 90))
        elif not gin_bitten:
            draw_char(img, "sadaharu", SADA_X, FLOOR, "bite", t, p=0.1 + 0.3 * seg(t, BITE_T, D_CHOMP),
                      facing=-1, shadow=False)
        else:
            bp = seg(t, BITE_T, BITE_T + 0.3)
            tilt = d_tilt(t)
            mx, my = maw_pos(SADA_X, FLOOR, -1, tilt)
            draw_bite(img, SADA_X, FLOOR, t, bp if bp < 1 else None, -1,
                      lambda x_, y_: dangling_gintoki(img, x_, y_ - 1, t, swing=-40, wob=10), tilt=tilt)
            blood_drops(img, mx, my + 8, t, D_CHOMP + 0.05, seed=1, fall=26)
    if D_POP <= t < D_POP + 0.5:                     # box-burst dust
        fx.smoke_puff(img, t, D_POP, BOX_X, FLOOR - 28, size=14, seed=21, color=(236, 228, 214), life=0.45)
    if t >= D_POP + 0.32:
        fx.smoke_puff(img, t, D_POP + 0.32, SADA_X, FLOOR - 2, size=12, seed=22, color=(226, 220, 210), life=0.45)
    # Kagura
    if t < D_POP:
        poke = step_frame(t, 6) % 2 if t < 12.2 else 0
        draw_char(img, "kagura", KAG_D - 10, FLOOR, "kneel", t, facing=-1, arm_f=78 + poke * 10,
                  arm_b=20, expr="shock" if 11.95 <= t < 12.1 else "normal")
    elif t < 12.75:
        k = seg(t, D_POP, 12.75)
        draw_char(img, "kagura", KAG_D - 10 + 10 * k, FLOOR - 10 * math.sin(math.pi * k),
                  "jump", t, facing=-1, expr="happy")
    else:
        draw_char(img, "kagura", KAG_D, FLOOR, "cheer", t, facing=-1)
        for i in range(3):                           # sparkles of joy
            tt = 12.8 + i * 0.37
            ph = (t - tt) % 1.1
            fx.sparkle(img, KAG_D - 12 + i * 11, FLOOR - 34 - i * 5, tt + ph, tt, size=3,
                       color=(255, 230, 140))
    # camera
    if t < D_POP:
        z, cx, cy = lerp(2.2, 2.35, seg(t, D0, D_POP)), BOX_X + 12, 140
    else:
        k = ease_out(seg(t, D_POP + 0.03, D_POP + 0.38))
        z = lerp(2.2, 1.55, k)
        cx, cy = lerp(BOX_X + 12, 208, k), lerp(140, 128, k)
        if t >= D_WIDE:
            k2 = ease_in_out(seg(t, D_WIDE, E0))
            z = lerp(1.55, 1.72, k2)
            cx, cy = lerp(208, 205, k2), lerp(128, 128, k2)
            # CHOMP punch-in on the maw, easing back out
            pk = ease_out(seg(t, D_CHOMP, D_CHOMP + 0.07)) * (1 - ease_in_out(seg(t, D_CHOMP + 0.25, D_CHOMP + 0.8)))
            z += 0.5 * pk
            cx, cy = lerp(cx, MAW[0] + 8, pk), lerp(cy, MAW[1] - 2, pk)
    c = zoom_view(img, z, cx, cy)
    if D_CHOMP <= t < D_CHOMP + 0.45:                # 集中線 around the bite
        mx0, my0 = to_screen(*maw_pos(SADA_X, FLOOR, -1, d_tilt(t)), z, c)
        fx.speed_lines(img, t, mx0, my0 + 8, color=(255, 255, 255), seed=19, count=40, inner=64,
                       alpha=1 - seg(t, D_CHOMP, D_CHOMP + 0.45))
    if D_CHOMP <= t < D_CHOMP + 1 / 30:
        fx.flash(img, 0.55)
    dx, dy = fx.shake_offset(t, D_POP + 0.03, 0.3, 4, seed=11)
    ex, ey = fx.shake_offset(t, D_POP + 0.32, 0.2, 3, seed=13)
    gx_, gy_ = fx.shake_offset(t, D_CHOMP, 0.4, 4, seed=12)
    fx.shift(img, dx + ex + gx_, dy + ey + gy_)
    if 12.25 <= t < D_POP:
        qx, qy = to_screen(KAG_D - 10, FLOOR - 34, z, c)
        sfx_text(img, qx, qy, "？", t, 12.25, 0.3, size=24, color=(255, 255, 255), angle=0)
    bx, by = to_screen(BOX_X, FLOOR - 40, z, c)
    sfx_text(img, bx + 10, by, "嘭!!", t, D_POP + 0.03, 0.6, size=28, angle=8)
    if 13.36 <= t < BITE_T + 0.05:                   # Gintoki, cocky: "good boy~"
        gx0, gy0 = to_screen(gin_d_x(t) - 4, FLOOR - 42, z, c)
        sfx_text(img, gx0, gy0, "乖～", t, 13.36, BITE_T + 0.05 - 13.36, size=14, color=(255, 255, 255),
                 angle=-6, shake=0)
    if t >= D_CHOMP:
        mw = maw_pos(SADA_X, FLOOR, -1, d_tilt(t))
        mx, my = to_screen(mw[0] - 34, mw[1] - 2, z, c)
        sfx_text(img, mx, my, "咔嚓!!", t, D_CHOMP, 0.9, size=28, color=(255, 90, 90), angle=12)
        hx, hy = to_screen(mw[0] + 28, mw[1] - 12, z, c)
        for i, tc in enumerate((14.25, 14.75, 15.25)):
            sfx_text(img, hx + (i % 2) * 18, hy - (i % 2) * 8, "嚼",
                     t, tc, 0.35, size=18, color=(255, 120, 120), angle=10 - i * 8)
    intro_card(img, t, 12.72, 2.2, "sadaharu", "SADAHARU", "定春", "巨型犬｜爱咬银时的头")


# ================================================================= shot E
BY = K.BALCONY_Y
E_POS = {"shinpachi": 136, "kagura": 162, "gintoki": 200, "sadaharu": 244}
E_DROP = {"gintoki": 15.30, "shinpachi": 15.42, "kagura": 15.52, "sadaharu": 15.62}
E_FALL = 0.26
E_FINAL = {
    "shinpachi": dict(pose="ready", facing=1, expr="determined"),
    "kagura": dict(pose="umbrella_open", facing=1),
    "gintoki": dict(pose="nosepick", facing=-1),     # deadpan while the others pose
}


def drop_y(cid, t):
    t0 = E_DROP[cid]
    k = seg(t, t0, t0 + E_FALL)
    return lerp(22, BY, k * k), k


def draw_member(img, cid, t):
    y, k = drop_y(cid, t)
    x = E_POS[cid]
    f = E_FINAL[cid]
    if k <= 0:
        return
    if k < 1:
        draw_char(img, cid, x, y, "jump", t, facing=f["facing"], shadow=False)
        return
    tl = t - (E_DROP[cid] + E_FALL)
    if tl < 0.14:
        draw_char(img, cid, x, BY, "land", t, p=tl / 0.3, facing=f["facing"])
        return
    kw = {"expr": f["expr"]} if "expr" in f else {}
    draw_char(img, cid, x, BY, f["pose"], t, facing=f["facing"], **kw)


def shot_e(img, t):
    K.yorozuya_front(img, t, "dusk")
    if t >= E_TEXT:
        fx.speed_lines(img, t, 192, 100, color=(255, 236, 200), seed=21, count=40, inner=70, alpha=0.85)
    chomp = t >= E_CHOMP
    for cid in ("shinpachi", "kagura", "gintoki"):
        if cid == "gintoki" and chomp:
            continue
        draw_member(img, cid, t)
    # Sadaharu
    sy, sk = drop_y("sadaharu", t)
    sx = E_POS["sadaharu"]
    if chomp:
        lunge = ease_out(seg(t, E_CHOMP, E_CHOMP + 0.12))
        gx = E_POS["gintoki"]
        dog_x = lerp(sx, gx + 22, lunge)
        dog_y = BY
        bp = seg(t, E_CHOMP, E_CHOMP + 0.3)
        if t < E_CHOMP + 0.1:
            draw_member(img, "gintoki", t)
            draw_char(img, "sadaharu", dog_x, dog_y, "bite", t, p=0.1 + 0.3 * seg(t, E_CHOMP, E_CHOMP + 0.1),
                      facing=-1, shadow=False)
        else:
            k = ease_out(seg(t, E_CHOMP + 0.1, E_CHOMP + 0.3))
            tilt = 22 * k + 2.5 * k * math.sin((t - E_CHOMP) * 11)
            mx, my = maw_pos(dog_x, dog_y, -1, tilt)
            draw_bite(img, dog_x, dog_y, t, bp if bp < 1 else None, -1,
                      lambda x_, y_: dangling_gintoki(img, x_, y_ - 1, t, swing=-40, wob=10), tilt=tilt)
            blood_drops(img, mx, my + 8, t, E_CHOMP + 0.15, seed=2, n=4, fall=18)
    elif 0 < sk < 1:
        draw_char(img, "sadaharu", sx, sy, "jump", t, facing=-1, shadow=False)
    elif sk >= 1:
        draw_char(img, "sadaharu", sx, BY, "sit", t, facing=-1, expr="happy")
    K.yorozuya_front_fg(img, t, "dusk")
    for i, cid in enumerate(("gintoki", "shinpachi", "kagura", "sadaharu")):     # landing dust
        tl = E_DROP[cid] + E_FALL
        fx.smoke_puff(img, t, tl, E_POS[cid], BY - 2, size=12 if cid == "sadaharu" else 7,
                      seed=40 + i, color=(250, 220, 200), life=0.45)
    if t >= E_TEXT:                                   # sparkles once assembled
        for i in range(6):
            r = rng("esp", i)
            tt = E_TEXT + 0.1 + r.uniform(0, 0.5)
            if t >= tt:
                ph = (t - tt) % 0.8
                fx.sparkle(img, int(r.uniform(124, 262)), int(r.uniform(72, 108)), tt + ph, tt, size=4,
                           color=(255, 244, 190))
    # camera: group shot + punch-in on the title hit
    z = 1.7
    if t >= E_TEXT:
        z += 0.14 * ease_out(seg(t, E_TEXT, E_TEXT + 0.12)) - 0.08 * ease_in_out(seg(t, E_TEXT + 0.12, E_TEXT + 0.6))
        z += 0.05 * ease_in_out(seg(t, E_TEXT + 0.6, END))
    c = zoom_view(img, z, 192, lerp(82, 97, ease_in_out(seg(t, E0, E_TEXT))))
    dx, dy = fx.shake_offset(t, E_DROP["sadaharu"] + E_FALL, 0.25, 3, seed=31)
    ex, ey = fx.shake_offset(t, E_TEXT, 0.3, 4, seed=32)
    gx_, gy_ = fx.shake_offset(t, E_CHOMP + 0.1, 0.25, 3, seed=33)
    fx.shift(img, dx + ex + gx_, dy + ey + gy_)
    if t >= E_TEXT:                                   # red band + big brush text
        k = ease_out(seg(t, E_TEXT, E_TEXT + 0.15))
        band_w = int((W + 40) * k)
        d = ImageDraw.Draw(img)
        y0 = 158
        d.polygon([(-10, y0 + 6), (band_w - 10, y0 - 2), (band_w - 10, y0 + 34), (-10, y0 + 40)], fill=INK)
        d.polygon([(-10, y0 + 9), (band_w - 10, y0 + 1), (band_w - 10, y0 + 31), (-10, y0 + 37)],
                  fill=(200, 46, 56))
        big_text(img, t, E_TEXT, "万事屋，集结！", 192, y0 + 17, size=32)
    if E_TEXT <= t < E_TEXT + 0.1:
        fx.flash(img, 0.7 * (1 - (t - E_TEXT) / 0.1))
    if t >= E_CHOMP + 0.1:
        bx, by = to_screen(E_POS["gintoki"] - 16, BY - 56, z, c)
        sfx_text(img, bx, by, "咔嚓!", t, E_CHOMP + 0.1, 0.75, size=24, color=(255, 90, 90), angle=12)


# ================================================================= scene
class Kagura(Scene):
    id = "s03"
    title = "神乐与定春"
    duration = END
    music = "comedy"
    music_vol = 0.55
    subs = [
        (2.75, 4.85, "kagura", "喂！你撞到人了阿鲁！"),
        (5.80, 7.88, "gintoki", "这丫头……是怪物吗！？"),
        (7.94, 9.76, "kagura", "再来一碗阿鲁！"),
        (9.80, 11.68, "shinpachi", "我们的伙食费啊！"),
        (11.72, 13.32, None, "第二天——"),
        (13.36, 15.38, "kagura", "就叫你『定春』阿鲁！"),
    ]

    def render(self, img, t):
        if t < B0:
            shot_a(img, t)
        elif t < C0:
            shot_b(img, t)
        elif t < D0:
            shot_c(img, t)
        elif t < E0:
            shot_d(img, t)
        else:
            shot_e(img, t)

    def cues(self):
        c = [
            # A - night street
            Cue(0.0, "night", vol=0.35, dur=C0),
            Cue(0.0, "scooter", vol=0.7, dur=A_HIT + 0.05),
            Cue(A_HIT, "crash", vol=1.0),
            Cue(A_HIT + 0.02, "punch_big", vol=0.8),
            Cue(A_HIT + 0.08, "fly_away", vol=0.6),
            Cue(A_LAND, "thud", vol=0.9),
            Cue(2.30, "crow", vol=0.7),
            Cue(A_SPRING, "jump", vol=0.8),
            Cue(A_CU, "land", vol=0.8),
            Cue(A_CU + 0.02, "shock", vol=0.6),
            Cue(2.85, "whoosh", vol=0.5),
            Cue(3.20, "sweat", vol=0.5),
            # B - yakuza vs umbrella gun
            Cue(B0, "run", vol=0.6, dur=0.4),
            Cue(5.00, "slide_up", vol=0.4),
            Cue(B_CU, "charge", vol=0.5),
            Cue(5.62, "shing", vol=0.9),
            Cue(B_FIRE, "machinegun", vol=0.9),
            Cue(B_FIRE + 0.45, "machinegun", vol=0.9),
            Cue(6.00, "hit", vol=0.5), Cue(6.25, "hit", vol=0.5), Cue(6.5, "hit", vol=0.5),
            Cue(B_BLAST, "gunshot", vol=1.0),
            Cue(B_BLAST + 0.01, "explosion_small", vol=0.7),
            Cue(B_BLAST + 0.1, "fly_away", vol=0.7),
            Cue(7.05, "sweat", vol=0.5),
            # C - office
            Cue(C0, "eat", vol=0.6, dur=C_WALLET - C0),
            Cue(C_SWITCH, "shock", vol=0.7),
            Cue(9.40, "gulp", vol=0.8),
            Cue(C_WALLET, "slide_down", vol=0.6),
            Cue(C_OPEN, "pop", vol=0.6),
            Cue(C_OPEN + 0.1, "twinkle", vol=0.45),
            Cue(C_OPEN + 0.35, "fly_away", vol=0.35),
            Cue(C_PULL + 0.15, "fail", vol=0.7),
            # D - Sadaharu
            Cue(D0, "crowd", vol=0.25, dur=E0 - D0),
            Cue(11.95, "squeak", vol=0.6), Cue(12.30, "squeak", vol=0.6, pitch=1.2),
            Cue(D_POP, "pop", vol=0.8),
            Cue(D_POP + 0.03, "boing", vol=0.9),
            Cue(D_POP + 0.32, "thud", vol=0.8),
            Cue(12.70, "shock", vol=0.7),
            Cue(12.72, "whoosh", vol=0.5),
            Cue(12.95, "bark", vol=0.9),
            Cue(13.40, "shine", vol=0.5),
            Cue(D_CHOMP, "chomp", vol=1.0),
            Cue(D_CHOMP + 0.02, "punch_big", vol=0.6),
            Cue(D_CHOMP + 0.3, "shock", vol=0.5),
            # E - assemble
            Cue(E0, "whoosh", vol=0.6),
        ]
        # chomps synced to the looping jaw (it snaps shut when floor(t*8) % 4 == 2)
        for tc in (14.25, 14.75, 15.25):
            c.append(Cue(tc, "chomp", vol=0.75))
        for cid in ("gintoki", "shinpachi", "kagura"):
            c.append(Cue(E_DROP[cid] + E_FALL, "land", vol=0.7))
        c += [
            Cue(E_DROP["sadaharu"] + E_FALL, "thud", vol=1.0),
            Cue(E_TEXT, "title_hit", vol=0.9),
            Cue(E_TEXT + 0.02, "impact", vol=0.6),
            Cue(E_TEXT + 0.2, "shine", vol=0.6),
            Cue(16.60, "bark", vol=0.6),
            Cue(E_CHOMP + 0.1, "chomp", vol=1.0),
            Cue(17.40, "rimshot", vol=0.7),
        ]
        return c


SCENE = Kagura()
