"""Pixel text: crisp CJK bitmap glyphs (SimSun embedded bitmaps at 12/16px),
brush-style title fonts, dialogue boxes, narration, name cards, onomatopoeia.
"""
import math
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from .core import W, H, clamp, seg, ease_out_back, ease_out, wave
from .gfx import INK, PAL, paste, overlay_rect, rect, frame_rect, scale_nearest, rotate_nearest, outline as sprite_outline

FONT_DIR = "C:/Windows/Fonts/"
_FONT_FILES = {
    "pixel": "simsun.ttc",       # crisp bitmap glyphs at 12 and 16 px ONLY
    "hei": "simhei.ttf",         # bold-ish sans for big SFX / titles
    "brush": "STXINGKA.TTF",     # 华文行楷 brush calligraphy (logo, chapter titles)
    "brush2": "FZSTK.TTF",       # 方正舒体
    "kai": "simkai.ttf",         # 楷体
}


@lru_cache(maxsize=64)
def font(size=12, face="pixel"):
    return ImageFont.truetype(FONT_DIR + _FONT_FILES[face], size)


def text_size(text, size=12, face="pixel"):
    f = font(size, face)
    b = f.getbbox(text)
    return b[2] - b[0], b[3] - b[1]


def text_width(text, size=12, face="pixel"):
    return int(font(size, face).getlength(text))


def _mono_draw(img):
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    return d


def draw_text(img, x, y, text, color=(255, 255, 255), size=12, face="pixel",
              outline=None, shadow=None, anchor="lt", thick=1):
    """Draw aliased text. anchor uses PIL anchors ('lt','mt','mm','rt','lb',...).
    outline: colour -> 1px (or `thick`) 8-direction outline. shadow: colour -> +1,+1 drop."""
    d = _mono_draw(img)
    f = font(size, face)
    x, y = int(round(x)), int(round(y))
    if shadow is not None:
        d.text((x + 1, y + 1), text, font=f, fill=tuple(shadow), anchor=anchor)
    if outline is not None:
        oc = tuple(outline)
        for dx in range(-thick, thick + 1):
            for dy in range(-thick, thick + 1):
                if dx or dy:
                    d.text((x + dx, y + dy), text, font=f, fill=oc, anchor=anchor)
    d.text((x, y), text, font=f, fill=tuple(color), anchor=anchor)


def text_sprite(text, color=(255, 255, 255), size=12, face="pixel", outline=None, thick=1):
    """Render text into a tight RGBA sprite (useful for scaling/rotating SFX)."""
    f = font(size, face)
    b = f.getbbox(text)
    pad = thick + 2
    w, h = b[2] - b[0] + pad * 2, b[3] - b[1] + pad * 2
    im = Image.new("RGBA", (max(1, w), max(1, h)), (0, 0, 0, 0))
    d = _mono_draw(im)
    ox, oy = pad - b[0], pad - b[1]
    if outline is not None:
        for dx in range(-thick, thick + 1):
            for dy in range(-thick, thick + 1):
                if dx or dy:
                    d.text((ox + dx, oy + dy), text, font=f, fill=tuple(outline) + (255,))
    d.text((ox, oy), text, font=f, fill=tuple(color[:3]) + (255,))
    return im


def wrap(text, max_w, size=12, face="pixel"):
    """Greedy wrap for CJK (per character) with '\n' support."""
    lines = []
    for para in text.split("\n"):
        cur = ""
        for ch in para:
            if text_width(cur + ch, size, face) > max_w and cur:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        lines.append(cur)
    return lines


# ------------------------------------------------------------------ subtitles
CPS = 16.0  # typewriter speed, characters / second


def typed(text, t, t0, cps=CPS):
    n = int(max(0.0, t - t0) * cps)
    return text[:n]


def _speaker_info(sid):
    try:
        from chars import get_def
        d = get_def(sid)
        if d is not None:
            return d.name, d.color, d
    except Exception:
        pass
    return str(sid), PAL["silver"], None


def dialogue_box(img, t, t0, t1, speaker, text, pos="bottom", portrait=True):
    """JRPG dialogue box with name tag, typewriter text, blinking cursor and an
    optional animated portrait popping out on the left."""
    fin = seg(t, t0, t0 + 0.12)
    fout = 1 - seg(t, t1 - 0.12, t1)
    vis = min(fin, fout)
    if vis <= 0:
        return
    name, color, cdef = _speaker_info(speaker)
    bx, bw, bh = 6, W - 12, 38
    by = H - bh - 5 if pos == "bottom" else 5
    by += int((1 - vis) * 8) * (1 if pos == "bottom" else -1)
    has_p = False
    port = None
    if portrait and cdef is not None:
        try:
            from chars import portrait as get_portrait
            talking = (t - t0) * CPS < len(text)
            port = get_portrait(speaker, expr=None, t=t - t0, talking=talking)
            has_p = port is not None
        except Exception:
            port = None
    overlay_rect(img, bx, by, bw, bh, (16, 14, 30), 0.82 * vis + 0.1)
    frame_rect(img, bx, by, bw, bh, (236, 232, 255))
    frame_rect(img, bx + 1, by + 1, bw - 2, bh - 2, (70, 66, 110))
    tx = bx + 8
    if has_p:
        pw, ph = port.size
        px = bx + 4
        py = by + bh - ph - 3
        rect(img, px - 1, max(by + 3, py) - 1, pw + 2, by + bh - 3 - max(by + 3, py) + 2, (40, 36, 70))
        paste(img, port, px, py)
        tx = bx + pw + 10
    # name tag
    nw = text_width(name) + 10
    rect(img, tx - 3, by - 7, nw, 13, INK)
    rect(img, tx - 2, by - 6, nw - 2, 11, color)
    draw_text(img, tx + 2, by - 5, name, (255, 255, 255), outline=INK)
    shown = typed(text, t, t0 + 0.08)
    lines = wrap(shown, bx + bw - tx - 8)
    for i, ln in enumerate(lines[:2]):
        draw_text(img, tx, by + 8 + i * 14, ln, (255, 255, 255), shadow=(60, 50, 90))
    if len(shown) >= len(text) and int(t * 3) % 2 == 0:
        cx, cy = bx + bw - 10, by + bh - 8
        rect(img, cx, cy, 5, 1, (255, 255, 255))
        rect(img, cx + 1, cy + 1, 3, 1, (255, 255, 255))
        rect(img, cx + 2, cy + 2, 1, 1, (255, 255, 255))


def narration(img, t, t0, t1, text, pos="bottom", color=(255, 244, 214)):
    """Narration line: centred outlined text with a soft dark band, typewriter."""
    vis = min(seg(t, t0, t0 + 0.2), 1 - seg(t, t1 - 0.25, t1))
    if vis <= 0:
        return
    full = wrap(text, W - 40)
    shown = typed(text, t, t0, cps=CPS * 1.1)
    lines = wrap(shown, W - 40)
    n = len(full)
    band_h = n * 15 + 8
    y0 = H - band_h - 6 if pos == "bottom" else 6
    overlay_rect(img, 0, y0, W, band_h, (0, 0, 0), 0.45 * vis)
    for i, ln in enumerate(lines):
        draw_text(img, W // 2 - text_width(full[i]) // 2, y0 + 4 + i * 15, ln, color, outline=INK)


def draw_subs(img, t, subs, pos="bottom"):
    """Called by the renderer after scene.render(): draws active subtitles."""
    for sub in subs:
        t0, t1, spk, text = sub[:4]
        if t0 <= t < t1:
            if spk is None:
                narration(img, t, t0, t1, text, pos)
            else:
                dialogue_box(img, t, t0, t1, spk, text, pos)


# ------------------------------------------------------------------ callouts
def sfx_text(img, x, y, text, t, t0, dur=0.8, color=(255, 226, 60), outline=(20, 10, 30),
             size=24, face="hei", angle=-8, shake=1):
    """Manga onomatopoeia (e.g. 'ドーン', '砰!') that pops in with overshoot."""
    if not (t0 <= t < t0 + dur):
        return
    p = (t - t0) / dur
    s = ease_out_back(min(1.0, p / 0.25)) if p < 0.25 else 1.0
    spr = text_sprite(text, color, size, face, outline=outline, thick=2)
    if s != 1.0:
        spr = spr.resize((max(1, int(spr.width * s)), max(1, int(spr.height * s))), Image.NEAREST)
    if angle:
        spr = rotate_nearest(spr, angle)
    jx = int(wave(t, 18, shake)) if shake else 0
    a = 1 - seg(p, 0.8, 1.0)
    paste(img, spr, x + jx, y, anchor="center", alpha=a)


def speech_bubble(img, x, y, text, t=0.0, t0=0.0, tail=(0, 1), color=(255, 255, 255),
                  text_color=INK, typewriter=True, size=12, max_w=150):
    """Comic speech bubble whose tail points at (x, y). tail=(dx,dy) direction
    from bubble to speaker; bubble is placed above-right by default."""
    shown = typed(text, t, t0) if typewriter else text
    if t < t0:
        return
    lines = wrap(text, max_w, size)
    tw = max(text_width(l, size) for l in lines)
    th = len(lines) * (size + 3)
    bw, bh = tw + 10, th + 7
    bx = int(x - bw // 2 - tail[0] * 10)
    by = int(y - bh - 8) if tail[1] > 0 else int(y + 8)
    bx = max(2, min(W - bw - 2, bx))
    by = max(2, min(H - bh - 2, by))
    d = ImageDraw.Draw(img)
    # tail
    tip = (x, y)
    base = (min(max(x, bx + 6), bx + bw - 8), by + bh - 1 if tail[1] > 0 else by)
    d.polygon([tip, (base[0] - 3, base[1]), (base[0] + 3, base[1])], fill=tuple(color), outline=tuple(INK))
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=4, fill=tuple(color), outline=tuple(INK))
    d.line([(base[0] - 2, base[1]), (base[0] + 2, base[1])], fill=tuple(color))
    shown_lines = wrap(shown, max_w, size) if typewriter else lines
    for i, ln in enumerate(shown_lines):
        draw_text(img, bx + 5, by + 4 + i * (size + 3), ln, text_color, size=size)


def name_card(img, t, t0, dur, char_id, title, desc="", side="right", color=None, y=22):
    """Anime-style character introduction card: a slanted colour band slides in
    with a big name and a gag description line. y = top of the band (default
    near the top of the screen so it never covers the characters)."""
    if not (t0 <= t < t0 + dur):
        return
    p = t - t0
    name, ccol, cdef = _speaker_info(char_id)
    color = color or ccol
    slide = ease_out(seg(p, 0, 0.3)) * (1 - ease_out(seg(p, dur - 0.25, dur)))
    bh = 50
    y0 = y
    d = ImageDraw.Draw(img)
    off = int((1 - slide) * (W + 40))
    if side == "right":
        xs = 150 + off
        d.polygon([(xs, y0), (W + 5, y0), (W + 5, y0 + bh), (xs - 16, y0 + bh)], fill=tuple(INK))
        d.polygon([(xs + 3, y0 + 3), (W + 5, y0 + 3), (W + 5, y0 + bh - 3), (xs - 13, y0 + bh - 3)], fill=tuple(color))
        d.polygon([(xs + 8, y0 + bh - 12), (W + 5, y0 + bh - 12), (W + 5, y0 + bh - 3), (xs - 13 + 4, y0 + bh - 3)], fill=tuple(INK))
        tx = xs + 8
    else:
        xe = W - 150 - off
        d.polygon([(-5, y0), (xe + 16, y0), (xe, y0 + bh), (-5, y0 + bh)], fill=tuple(INK))
        d.polygon([(-5, y0 + 3), (xe + 13, y0 + 3), (xe - 3, y0 + bh - 3), (-5, y0 + bh - 3)], fill=tuple(color))
        d.polygon([(-5, y0 + bh - 12), (xe + 1, y0 + bh - 12), (xe - 3, y0 + bh - 3), (-5, y0 + bh - 3)], fill=tuple(INK))
        tx = 12 - off
    draw_text(img, tx, y0 + 6, title, (255, 255, 255), size=16, outline=INK)
    if desc:
        shown = typed(desc, t, t0 + 0.35, cps=24)
        draw_text(img, tx + 2, y0 + bh - 12 + 0, shown, (255, 236, 150), size=12)
    # small caption with name in latin-ish tag
    draw_text(img, tx + text_width(title, 16) + 8, y0 + 10, name, (30, 24, 40), size=12)


def chapter_card(img, t, t0, dur, big, small="", bg=(20, 16, 28), accent=(228, 59, 68)):
    """Full-screen chapter title (e.g. '红樱篇'), brush font, ink splash bar."""
    if not (t0 <= t < t0 + dur):
        return
    p = t - t0
    a = min(seg(p, 0, 0.15), 1 - seg(p, dur - 0.2, dur))
    overlay_rect(img, 0, 0, W, H, bg, a)
    bar = ease_out(seg(p, 0.05, 0.4))
    bw = int(W * 0.8 * bar)
    rect(img, W // 2 - bw // 2, H // 2 - 26, bw, 52, accent) if a > 0.5 else None
    rect(img, W // 2 - bw // 2, H // 2 - 22, bw, 2, (20, 10, 20)) if a > 0.5 else None
    if p > 0.2 and a > 0.5:
        s = min(1.0, (p - 0.2) / 0.2)
        spr = text_sprite(big, (255, 255, 255), 40, "brush", outline=INK, thick=2)
        if s < 1:
            k = 1 + (1 - s) * 1.5
            spr = spr.resize((int(spr.width * k), int(spr.height * k)), Image.NEAREST)
        paste(img, spr, W // 2, H // 2 - 2, anchor="center")
    if small and p > 0.5 and a > 0.5:
        draw_text(img, W // 2, H // 2 + 36, typed(small, t, t0 + 0.5, 24), (255, 235, 200),
                  anchor="mt", outline=INK)
