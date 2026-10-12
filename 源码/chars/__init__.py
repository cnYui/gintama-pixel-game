"""Character registry.

Every module in this package (except rig.py) is imported automatically and
must call register(def) for each character it defines. Scenes use:

    from chars import draw_char, portrait, get_def
    draw_char(img, 'gintoki', x, y, pose='walk', t=t, facing=1)

x, y = FEET position (bottom-centre) on the 384x216 canvas.
"""
import importlib
import math
import os
import pkgutil
import traceback

from PIL import Image

from engine.core import step_frame, clamp
from engine.gfx import paste, flip_h, tint, set_alpha, scale_nearest, rotate_nearest

_REGISTRY = {}
_LOADED = False


def register(cdef):
    _REGISTRY[cdef.id] = cdef
    return cdef


def _load_all():
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    pkg_dir = os.path.dirname(__file__)
    for m in sorted(pkgutil.iter_modules([pkg_dir]), key=lambda m: m.name):
        if m.name in ("rig",) or m.name.startswith("_"):
            continue
        try:
            importlib.import_module(f"chars.{m.name}")
        except Exception:
            print(f"[chars] failed to import chars.{m.name}:")
            traceback.print_exc()


def get_def(cid):
    _load_all()
    return _REGISTRY.get(cid)


def list_chars():
    _load_all()
    return sorted(_REGISTRY)


def render_sprite(cid, pose="idle", t=0.0, p=None, expr=None, facing=1, flash=0.0,
                  flash_color=(255, 255, 255), alpha=1.0, scale=1, rot=0, **kw):
    """Return (sprite RGBA, anchor_x, anchor_y) for the character."""
    d = get_def(cid)
    if d is None:
        raise KeyError(f"unknown character {cid!r}; known: {list_chars()}")
    spr, ax, ay = d.render(pose=pose, t=t, p=p, expr=expr, **kw)
    if rot:
        spr = spr.rotate(rot, resample=Image.NEAREST, center=(ax, ay - 14))
    if facing < 0:
        spr = flip_h(spr)
        ax = spr.width - 1 - ax
    if flash > 0:
        spr = tint(spr, flash_color, clamp(flash))
    if scale != 1:
        spr = scale_nearest(spr, scale)
        ax, ay = ax * scale, ay * scale
    if alpha < 1:
        spr = set_alpha(spr, alpha)
    return spr, ax, ay


def draw_char(img, cid, x, y, pose="idle", t=0.0, p=None, expr=None, facing=1, flash=0.0,
              flash_color=(255, 255, 255), alpha=1.0, scale=1, rot=0, shadow=True, **kw):
    """Draw a character with feet at (x, y). Returns the sprite's bbox on canvas.

    pose   : any standard pose (see chars.rig.POSES) or a character-specific one
    t      : scene-local time (drives looping animation)
    p      : 0..1 progress for one-shot poses (attack, hit, point, shock, punch...)
    expr   : force a head expression ('normal','blink','talk','angry','shout',
             'shock','happy','sad','cry','hurt','smug','determined', ...)
    facing : 1 = right, -1 = left
    flash  : 0..1 tint toward flash_color (hit flash)
    shadow : draw a small ground shadow ellipse
    kw     : any pose param override (e.g. weapon=None, bob=0, dy=-5)
    """
    spr, ax, ay = render_sprite(cid, pose, t, p, expr, facing, flash, flash_color, alpha, scale, rot, **kw)
    x, y = int(round(x)), int(round(y))
    if shadow and alpha > 0.3:
        from engine.gfx import overlay_rect
        sw = 12 * scale
        overlay_rect(img, x - sw // 2, y - 1, sw, 2, (0, 0, 0), 0.25)
    px, py = x - ax, y - ay
    img.paste(spr, (int(px), int(py)), spr)
    return (px, py, spr.width, spr.height)


def portrait(cid, expr=None, t=0.0, talking=False):
    """Dialogue portrait (RGBA). Uses the def's portrait art if present, else
    the chibi head scaled x2. Animates blink + mouth flaps when talking."""
    d = get_def(cid)
    if d is None:
        return None
    if hasattr(d, "portrait_fn"):
        return d.portrait_fn(expr, t, talking)
    e = expr or "normal"
    if talking and step_frame(t, 8) % 2 == 0:
        e = "talk" if expr in (None, "normal") else e
    elif expr is None and (t % 3.1) < 0.12:
        e = "blink"
    p = d.portrait(e) if getattr(d, "portraits_art", None) else None
    if p is not None:
        return p
    try:
        h = d.head(e)
    except Exception:
        return None
    return scale_nearest(h, 2)
