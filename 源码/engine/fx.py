"""Screen effects & particles. Everything is an analytic function of time so a
frame can be rendered in isolation (no simulation state)."""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageOps

from .core import W, H, clamp, seg, rng, wave, ease_out, lerp
from .gfx import INK, PAL, overlay_rect, dither_mask, shade

# ------------------------------------------------------------------ camera
def shake_offset(t, t0, dur, amp=3, freq=30, seed=0):
    """(dx, dy) camera shake that decays over `dur` seconds after t0."""
    if not (t0 <= t < t0 + dur):
        return 0, 0
    k = 1 - (t - t0) / dur
    r = rng("shake", seed, int((t - t0) * freq))
    return int(round(r.uniform(-1, 1) * amp * k)), int(round(r.uniform(-1, 1) * amp * k))


def shift(img, dx, dy, fill=(0, 0, 0)):
    """Shift the whole canvas in place (apply shake after drawing the world)."""
    if dx == 0 and dy == 0:
        return
    src = img.copy()
    img.paste(tuple(fill[:3]), (0, 0, W, H))
    img.paste(src, (int(dx), int(dy)))


def zoom(img, k, cx=W // 2, cy=H // 2):
    """Nearest-neighbour zoom of the whole canvas about (cx, cy), in place."""
    if abs(k - 1) < 1e-3:
        return
    w, h = W / k, H / k
    box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    z = img.resize((W, H), Image.NEAREST, box=box)
    img.paste(z)


# ------------------------------------------------------------------ overlays
def flash(img, amount, color=(255, 255, 255)):
    if amount > 0:
        overlay_rect(img, 0, 0, W, H, color, clamp(amount))


def fade(img, amount, color=(0, 0, 0)):
    flash(img, amount, color)


def invert(img):
    img.paste(ImageOps.invert(img))


def impact_frame(img, color_hi=(255, 255, 255), color_lo=(12, 10, 18), threshold=110):
    """Anime 'impact frame': 2-tone high contrast version of the current frame."""
    g = np.asarray(img.convert("L"))
    m = g > threshold
    out = np.empty((H, W, 3), np.uint8)
    out[m] = color_lo
    out[~m] = color_hi
    img.paste(Image.fromarray(out, "RGB"))


def grade(img, mul=(1, 1, 1), add=(0, 0, 0)):
    a = np.asarray(img).astype(np.float32)
    a = a * np.array(mul, np.float32) + np.array(add, np.float32)
    img.paste(Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGB"))


def sepia(img, amount=1.0):
    """Flashback tint. amount 0..1"""
    if amount <= 0:
        return
    a = np.asarray(img).astype(np.float32)
    g = a @ np.array([0.299, 0.587, 0.114], np.float32)
    sep = np.stack([g * 1.07 + 20, g * 0.95 + 8, g * 0.72], -1)
    a = a * (1 - amount) + sep * amount
    img.paste(Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGB"))


def grayscale(img, amount=1.0):
    a = np.asarray(img).astype(np.float32)
    g = (a @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
    a = a * (1 - amount) + g * amount
    img.paste(Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGB"))


def vignette(img, strength=0.5, color=(0, 0, 0)):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    k = np.clip((d - 0.6) / 0.8, 0, 1) * strength
    # quantise to 4 levels + dither -> stays pixel-y
    k = np.floor(k * 4 + dither_mask(W, H, 0.5)) / 4
    a = np.asarray(img).astype(np.float32)
    a = a * (1 - k[..., None]) + np.array(color, np.float32) * k[..., None]
    img.paste(Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGB"))


def letterbox(img, amount=1.0, bar=22):
    """Cinematic black bars (amount animates 0..1)."""
    h = int(bar * clamp(amount))
    if h > 0:
        img.paste((0, 0, 0), (0, 0, W, h))
        img.paste((0, 0, 0), (0, H - h, W, H))


# ------------------------------------------------------------------ manga lines
def speed_lines(img, t, cx=W // 2, cy=H // 2, color=(255, 255, 255), count=48,
                inner=70, seed=0, alpha=1.0, thickness=2):
    """Radial concentration lines (集中線), re-randomised 15x per second."""
    r = rng("speed", seed, int(t * 15))
    d = ImageDraw.Draw(img)
    R = math.hypot(W, H)
    for i in range(count):
        if r.random() > alpha:
            continue
        a = r.uniform(0, 2 * math.pi)
        ri = inner + r.uniform(0, 40)
        w = r.uniform(0.012, 0.03) * thickness
        p1 = (cx + math.cos(a - w) * R, cy + math.sin(a - w) * R)
        p2 = (cx + math.cos(a + w) * R, cy + math.sin(a + w) * R)
        p0 = (cx + math.cos(a) * ri, cy + math.sin(a) * ri)
        d.polygon([p0, p1, p2], fill=tuple(color))


def motion_lines(img, t, color=(255, 255, 255), count=22, direction=-1, seed=0,
                 y0=0, y1=H, speed=900, length=(20, 70)):
    """Horizontal speed streaks for dashes/chases. direction -1 = streaks move left."""
    d = ImageDraw.Draw(img)
    for i in range(count):
        r = rng("mline", seed, i)
        y = int(r.uniform(y0, y1))
        L = r.uniform(*length)
        span = W + L + 40
        x = (r.uniform(0, span) + t * speed * r.uniform(0.7, 1.3)) % span - L
        if direction < 0:
            x = W - x
        d.line([(x, y), (x + L, y)], fill=tuple(color), width=1)


def comic_burst(img, cx, cy, r_out, r_in, spikes=12, color=(255, 230, 80), outline=INK, rot=0.0):
    pts = []
    for i in range(spikes * 2):
        a = rot + i * math.pi / spikes
        rr = r_out if i % 2 == 0 else r_in
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    ImageDraw.Draw(img).polygon(pts, fill=tuple(color), outline=tuple(outline))


def slash_arc(img, cx, cy, radius, a0, a1, p, color=(255, 255, 255), width=3):
    """White crescent slash trail sweeping from angle a0 to a1 (degrees,
    screen-space, 0 = right, 90 = down). p = sweep progress 0..1 (fades after 1)."""
    if p <= 0:
        return
    d = ImageDraw.Draw(img)
    head = a0 + (a1 - a0) * min(1.0, p)
    tail = a0 + (a1 - a0) * max(0.0, min(1.0, (p - 0.35) * 1.6))
    n = 18
    for i in range(n):
        k = i / (n - 1)
        a = math.radians(tail + (head - tail) * k)
        wd = max(1, int(width * k))
        x, y = cx + math.cos(a) * radius, cy + math.sin(a) * radius
        d.ellipse([x - wd / 2, y - wd / 2, x + wd / 2, y + wd / 2], fill=tuple(color))


# ------------------------------------------------------------------ particles
def burst(img, t, t0, x, y, n=16, colors=((255, 255, 255),), speed=(40, 120),
          gravity=160.0, life=0.7, size=(1, 2), seed=0, spread=(0, 360), drag=0.0):
    """Analytic particle burst emitted at t0 from (x, y)."""
    dt = t - t0
    if dt < 0 or dt > life * 1.4:
        return
    d = ImageDraw.Draw(img)
    for i in range(n):
        r = rng("burst", seed, i)
        L = life * r.uniform(0.6, 1.4)
        if dt > L:
            continue
        a = math.radians(r.uniform(*spread))
        v = r.uniform(*speed)
        vx, vy = math.cos(a) * v, math.sin(a) * v
        if drag:
            f = (1 - math.exp(-drag * dt)) / drag
            px, py = x + vx * f, y + vy * f + 0.5 * gravity * dt * dt
        else:
            px, py = x + vx * dt, y + vy * dt + 0.5 * gravity * dt * dt
        s = int(round(r.uniform(*size) * (1 - dt / L * 0.5)))
        c = colors[i % len(colors)]
        if s <= 1:
            d.point((int(px), int(py)), fill=tuple(c))
        else:
            d.rectangle([int(px), int(py), int(px) + s - 1, int(py) + s - 1], fill=tuple(c))


def explosion(img, t, t0, x, y, size=30, seed=0, smoke=True):
    """Chunky pixel explosion: flash ring, fire balls, smoke puffs, debris."""
    dt = t - t0
    if dt < 0 or dt > 1.6:
        return
    d = ImageDraw.Draw(img)
    fire = [(255, 255, 230), (255, 230, 90), (254, 174, 52), (247, 118, 34), (228, 59, 68)]
    smoke_c = [(90, 80, 90), (60, 54, 66), (120, 110, 115)]
    if smoke:
        for i in range(10):
            r = rng("exs", seed, i)
            a = r.uniform(0, 2 * math.pi)
            dist = size * (0.3 + 0.9 * ease_out(clamp(dt / 1.2))) * r.uniform(0.5, 1.0)
            px = x + math.cos(a) * dist
            py = y + math.sin(a) * dist * 0.7 - dt * 18
            rad = size * 0.35 * r.uniform(0.6, 1.2) * (1 - clamp((dt - 0.6) / 1.0))
            if rad > 0.5 and dt > 0.15:
                c = smoke_c[i % 3]
                d.ellipse([px - rad, py - rad, px + rad, py + rad], fill=c)
    if dt < 0.7:
        k = dt / 0.7
        for i in range(8):
            r = rng("exf", seed, i)
            a = r.uniform(0, 2 * math.pi)
            dist = size * 0.6 * ease_out(k) * r.uniform(0.2, 1.0)
            px, py = x + math.cos(a) * dist, y + math.sin(a) * dist * 0.8
            rad = size * 0.4 * r.uniform(0.6, 1.1) * (1 - k)
            ci = min(len(fire) - 1, int(k * len(fire) + r.uniform(0, 1.5)))
            d.ellipse([px - rad, py - rad, px + rad, py + rad], fill=fire[ci])
        core = size * 0.5 * (1 - k) * (1 + 0.3 * math.sin(dt * 60))
        if core > 0.5:
            d.ellipse([x - core, y - core, x + core, y + core], fill=fire[0])
    if dt < 0.12:
        rr = size * (0.5 + dt * 8)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(255, 255, 255), width=2)
    burst(img, t, t0, x, y, n=14, colors=[(255, 220, 120), (90, 80, 90), (40, 30, 40)],
          speed=(60, 170), gravity=220, life=0.9, size=(1, 3), seed=seed + 99)


def smoke_puff(img, t, t0, x, y, size=8, seed=0, color=(210, 210, 220), life=0.8):
    """Small 'poof' (landing dust, disappearing, running start)."""
    dt = t - t0
    if dt < 0 or dt > life:
        return
    d = ImageDraw.Draw(img)
    k = dt / life
    for i in range(6):
        r = rng("puff", seed, i)
        a = r.uniform(0, 2 * math.pi)
        dist = size * ease_out(k) * r.uniform(0.5, 1.2)
        px, py = x + math.cos(a) * dist, y + math.sin(a) * dist * 0.5 - k * 4
        rad = size * 0.45 * (1 - k) * r.uniform(0.7, 1.2)
        if rad > 0.4:
            d.ellipse([px - rad, py - rad, px + rad, py + rad], fill=tuple(color))


# ------------------------------------------------------------------ ambience
def sakura(img, t, count=26, seed=0, colors=((255, 183, 197), (255, 214, 224), (240, 140, 170)),
           wind=22.0, fall=18.0, area=(0, 0, W, H)):
    x0, y0, x1, y1 = area
    ww, hh = x1 - x0, y1 - y0
    d = ImageDraw.Draw(img)
    for i in range(count):
        r = rng("sakura", seed, i)
        sp = r.uniform(0.7, 1.3)
        x = (r.uniform(0, ww) + t * wind * sp + wave(t, 0.4 * sp, 6, r.random())) % (ww + 10) + x0 - 5
        y = (r.uniform(0, hh) + t * fall * sp) % (hh + 10) + y0 - 5
        c = colors[i % len(colors)]
        ph = int((t * 6 * sp + i) % 4)
        if ph in (0, 2):
            d.rectangle([x, y, x + 1, y], fill=c)
        else:
            d.rectangle([x, y, x, y + 1], fill=c)
        if i % 3 == 0:
            d.point((x + 1, y + 1), fill=c)


def rain(img, t, count=90, seed=0, color=(150, 170, 220), speed=380.0, slant=0.25, length=6):
    d = ImageDraw.Draw(img)
    for i in range(count):
        r = rng("rain", seed, i)
        sp = speed * r.uniform(0.8, 1.2)
        y = (r.uniform(0, H + 40) + t * sp) % (H + 40) - 20
        x = (r.uniform(0, W + 60) - y * slant) % (W + 60) - 30
        d.line([(x, y), (x + slant * length, y + length)], fill=tuple(color))


def snow(img, t, count=60, seed=0, color=(240, 244, 255), speed=22.0):
    d = ImageDraw.Draw(img)
    for i in range(count):
        r = rng("snow", seed, i)
        y = (r.uniform(0, H) + t * speed * r.uniform(0.6, 1.4)) % (H + 4) - 2
        x = (r.uniform(0, W) + wave(t, 0.3, 5, r.random())) % W
        if i % 4 == 0:
            d.rectangle([x, y, x + 1, y + 1], fill=tuple(color))
        else:
            d.point((x, y), fill=tuple(color))


def embers(img, t, count=30, seed=0, colors=((255, 200, 80), (255, 120, 40), (255, 240, 180)),
           rise=30.0, area=(0, 0, W, H)):
    x0, y0, x1, y1 = area
    d = ImageDraw.Draw(img)
    for i in range(count):
        r = rng("ember", seed, i)
        hh = y1 - y0
        y = y1 - (r.uniform(0, hh) + t * rise * r.uniform(0.6, 1.5)) % hh
        x = x0 + (r.uniform(0, x1 - x0) + wave(t, 0.5, 8, r.random())) % (x1 - x0)
        if (int(t * 10) + i) % 5:
            d.point((x, y), fill=tuple(colors[i % len(colors)]))


def stars(img, t, count=70, seed=0, area=(0, 0, W, 120), colors=((255, 255, 255), (200, 210, 255), (255, 240, 200))):
    x0, y0, x1, y1 = area
    d = ImageDraw.Draw(img)
    for i in range(count):
        r = rng("star", seed, i)
        x, y = r.randint(x0, x1 - 1), r.randint(y0, y1 - 1)
        tw = math.sin(t * r.uniform(1, 4) + r.uniform(0, 6.28))
        c = colors[i % len(colors)]
        if tw > -0.3:
            d.point((x, y), fill=c)
            if r.random() < 0.12 and tw > 0.7:
                d.point((x - 1, y), fill=shade(c, 0.6))
                d.point((x + 1, y), fill=shade(c, 0.6))
                d.point((x, y - 1), fill=shade(c, 0.6))
                d.point((x, y + 1), fill=shade(c, 0.6))


def sparkle(img, x, y, t, t0=0.0, size=4, color=(255, 255, 255)):
    """4-point twinkle star (e.g. 'kira!' on glasses, blades, a character flying off)."""
    p = (t - t0) * 4
    if p < 0 or p > 2:
        return
    s = int(size * math.sin(min(math.pi, p * math.pi / 2)))
    if s <= 0:
        return
    d = ImageDraw.Draw(img)
    d.line([(x - s, y), (x + s, y)], fill=tuple(color))
    d.line([(x, y - s), (x, y + s)], fill=tuple(color))
    if s > 2:
        d.point((x - 1, y - 1), fill=tuple(color))
        d.point((x + 1, y + 1), fill=tuple(color))
        d.point((x + 1, y - 1), fill=tuple(color))
        d.point((x - 1, y + 1), fill=tuple(color))


# ------------------------------------------------------------------ transitions
def iris(img, p, cx=W // 2, cy=H // 2, color=(0, 0, 0)):
    """Iris wipe. p=0 fully open, p=1 fully closed (circle shrinks to cx,cy)."""
    if p <= 0:
        return
    R = math.hypot(max(cx, W - cx), max(cy, H - cy)) + 2
    r = R * (1 - clamp(p))
    mask = Image.new("L", (W, H), 255)
    ImageDraw.Draw(mask).ellipse([cx - r, cy - r, cx + r, cy + r], fill=0)
    img.paste(tuple(color), (0, 0, W, H), mask)


def diamond_wipe(img, p, color=(0, 0, 0), cell=16, direction=1):
    """Retro diamond-tile transition. p 0..1 (1 = fully covered)."""
    if p <= 0:
        return
    d = ImageDraw.Draw(img)
    cols, rows = W // cell + 2, H // cell + 2
    for j in range(rows):
        for i in range(cols):
            delay = (i if direction > 0 else cols - i) / cols * 0.6
            k = clamp((p - delay) / 0.4)
            if k <= 0:
                continue
            cx, cy = i * cell, j * cell
            r = k * cell
            d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=tuple(color))


def wipe(img, p, color=(0, 0, 0), direction="left", slant=30):
    """Slanted hard wipe (manga panel style)."""
    if p <= 0:
        return
    x = -slant + (W + slant * 2) * clamp(p)
    if direction == "left":
        pts = [(0, 0), (x + slant, 0), (x, H), (0, H)]
    else:
        xr = W - x
        pts = [(W, 0), (xr - slant, 0), (xr, H), (W, H)]
    ImageDraw.Draw(img).polygon(pts, fill=tuple(color))


def pixelate(img, block):
    """Mosaic transition (block px)."""
    if block <= 1:
        return
    small = img.resize((max(1, W // block), max(1, H // block)), Image.NEAREST)
    img.paste(small.resize((W, H), Image.NEAREST))
