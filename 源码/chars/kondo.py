"""近藤勋 Kondo Isao — Shinsengumi commander. Gorilla, stalker, good guy.

Spiky crew cut, thick brows, square stubbled jaw, broad torso and thick arms.
Extra pose: stalk (crouching behind a bush he carries around; kw bush=False to hide it).
Extra exprs: love (heart eyes + blush), peek (eyes locked on the target, sweaty blush).
"""
import math
from functools import lru_cache

from PIL import Image

from engine.core import step_frame, rng
from engine.gfx import INK, stamp_line, rect, pset
from chars import register
from chars.rig import pose_idle, _blink
from chars.hijikata import (SSGDef, SSG_TORSO_PAL, SSG_SLEEVE_F, SSG_SLEEVE_B, SSG_PANTS, SSG_SHOES,
                            SKIN, sheathed_katana, mk_head, katana_on_shoulder, resolve_expr)

HEAD_PAL = {
    "o": INK,
    "H": (100, 88, 96),     # hair shine
    "h": (50, 42, 48),      # near-black hair
    "d": (32, 26, 32),      # hair shade
    "S": (255, 214, 178),   # skin (a bit tanned)
    "s": (228, 164, 132),   # skin shade
    "u": (184, 150, 150),   # stubble
    "E": (46, 34, 34),      # eyes
    "w": (255, 255, 255),
    "m": (170, 70, 80),     # mouth
    "R": (236, 56, 90),     # hearts / tongue
    "b": (250, 140, 150),   # blush
    "T": (120, 200, 255),   # tears
    "B": (80, 120, 220),    # gloom
}

BASE = [
    "....o.o.o.o.o.....",   # 0  crew-cut spikes
    "...ohohohohoho....",   # 1
    "..ohHhHhHhhhhho...",   # 2
    ".ohHHhhhhhhhhhhho.",   # 3
    "ohHhhhhhhhhhhhhhdo",   # 4
    "ohhhhhhhhhhhhhhhdo",   # 5
    "odhhhhhhhhhhhhhhdo",   # 6
    "odhhhShhhShhhShhdo",   # 7  short spiky bangs
    "odhSSSShSSSShSSSho",   # 8
    "odSSSSSSSSSSSSSSho",   # 9  forehead
    "odSSoooSSSSoooSSho",   # 10 thick brows
    "odSSSwESSSSSwESSho",   # 11 eyes
    ".oSSSSSSSSSsSSSSo.",   # 12 nose
    ".osSSSSSSSmmSSSso.",   # 13 mouth
    ".osSSSSuSuSuSSSso.",   # 14 stubble
    "..osSSuSuSuSuSso..",   # 15 square stubbly jaw
    "...oooooooooooo...",   # 16
]


def _h(**rows):
    return mk_head(BASE, **rows)


HEADS = {
    "normal": _h(),
    "blink": _h(r11="odSSSooSSSSSooSSho"),
    "talk": _h(r13=".osSSSSSSSooSSSso.", r14=".osSSSSuSmmuSSSso."),
    "angry": _h(r9="odSSoSSSSSSSSoSSho", r10="odSSSooSSSSooSSSho",
                r11="odSSSwESSSSEwSSSho", r13=".osSSSSSSmmmmSSso."),
    "shout": _h(r9="odSSoSSSSSSSSoSSho", r10="odSSSooSSSSooSSSho",
                r11="odSSSwESSSSEwSSSho", r13=".osSSSSSSooooSSso.",
                r14=".osSSSSuSomRmoSso.", r15="..osSSuSSoooSso..."),
    "shock": _h(r9="odSSoooSSSSoooSSho", r10="odSSSSSSSSSSSSSSho",
                r11="odSSowwoSSowwoSSho", r12=".oSSSooSSSSooSSSo.",
                r13=".osSSSSSSSooSSSso."),
    "happy": _h(r10="odSSSoSSSSSSoSSSho", r11="odSSoSoSSSSoSoSSho",
                r12=".oSbbSSSSSSSSbbSo.", r13=".osSSSSSoooooSSso.",
                r14=".osSSSSSowwwoSsso.", r15="..osSSuSSSoooSso.."),
    "sad": _h(r9="odSSSSoSSSSoSSSSho", r10="odSSooSSSSSSooSSho",
              r13=".osSSSSSSSooSSSso.", r14=".osSSSSuSoSSoSSso."),
    "cry": _h(r9="odSSSSoSSSSoSSSSho", r10="odSSooSSSSSSooSSho",
              r11="odSSSooSSSSSooSSho", r12=".oSSSTTSSSSSTTSSo.",
              r13=".osSSTTSSSooTTSso.", r14=".osSSTTuSomoTTSso.",
              r15="..osuTTSSoooTTo..."),
    "hurt": _h(r10="odSSoSoSSSSoSoSSho", r11="odSSSoSSSSSSoSSSho",
               r12=".oSSoSoSSSSoSoSSo.", r13=".osSSSSSSSooSSSso."),
    "smug": _h(r10="odSSSSSSSSSSSSSSho", r11="odSSoooSSSSoooSSho",
               r12=".oSSSwESSSSwESSSo.", r13=".osSSSSSSmmmSSSso."),
    "sleep": _h(r11="odSSSooSSSSSooSSho", r13=".osSSSSSSSSoSSSso."),
    "love": _h(r10="odSSRSRSSSSRSRSSho", r11="odSSRRRSSSSRRRSSho",
               r12=".oSbbRbSSSSbRbbSo.", r13=".osSSSSSSSooSSSso."),
    "peek": _h(r10="odSSSooSSSSSooSSho", r11="odSSSSwESSSSSwESho",
               r12=".oSbbSSSSSSSSbbSo.", r13=".osSSSSSSSmmSSSso."),
    "gloom": _h(r8="odhBSSShSBSShSBSho", r9="odSBSSBSSSBSSBSSho"),
}

TORSO = """
.....oooooo.....
....okWWWWKo....
..ookkYWWwYKoo..
.okkKKYWWwYKKjo.
.okKKKKYWwYKKjo.
.okKKKKKYwYKKjo.
.okKKKKKKYKKKjo.
.okKKKKKKYKKKjo.
.okKKKKKKyKKKjo.
.okKKKKKKYKKKjo.
.okKKKKKKYKKKjo.
.oyYYYYYYYYYYyo.
..oooooooooooo..
"""


# ------------------------------------------------------------------ the bush
LEAF = (58, 132, 64)
LEAF_L = (104, 186, 82)
LEAF_D = (34, 88, 52)


@lru_cache(maxsize=4)
def _bush(frame):
    """Leafy round bush, 30x19, two rustle frames. Returns RGBA."""
    Wb, Hb = 30, 19
    img = Image.new("RGBA", (Wb, Hb), (0, 0, 0, 0))
    blobs = [(6, 12, 6), (14, 9, 8), (23, 12, 6.5), (10, 14, 5), (19, 14, 5.5), (14, 5, 4.5)]
    if frame:
        blobs = [(x + (1 if i in (1, 5) else 0), y - (1 if i == 5 else 0), r) for i, (x, y, r) in enumerate(blobs)]
    inside = {}
    for y in range(Hb):
        for x in range(Wb):
            for (bx, by, br) in blobs:
                dx, dy = x - bx, y - by
                if dx * dx + dy * dy <= br * br and y <= Hb - 2:
                    # shade within the blob: light top-left, dark bottom-right
                    k = (dx - dy * 1.2) / br
                    inside[(x, y)] = max(inside.get((x, y), -9), -dx / br - dy / br)
                    break
    for (x, y), k in inside.items():
        if k > 0.8:
            c = LEAF_L
        elif k < -0.6:
            c = LEAF_D
        else:
            c = LEAF
        img.putpixel((x, y), c + (255,))
    # leaf texture: little light/dark ticks
    r = rng("kondo_bush", frame)
    for _ in range(38):
        x, y = r.randrange(Wb), r.randrange(Hb)
        if (x, y) in inside and (x + 1, y) in inside:
            img.putpixel((x, y), (LEAF_L if r.random() < 0.55 else LEAF_D) + (255,))
    # outline
    out = img.copy()
    for y in range(Hb):
        for x in range(Wb):
            if (x, y) in inside:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, y + dy) in inside:
                    out.putpixel((x, y), INK + (255,))
                    break
    # flat bottom on the ground
    for x in range(Wb):
        if out.getpixel((x, Hb - 2))[3]:
            out.putpixel((x, Hb - 1), INK + (255,))
    return out


def pose_stalk(pp, t, p, d):
    """Crouching behind a bush, peeking over it at his beloved Otae (hearts)."""
    cyc = t % 2.2
    peek = cyc < 1.7
    f = step_frame(t, 6, 2)
    pp["legs"] = "kneel"
    pp["lean"] = 1
    pp["arm_f"] = 150
    pp["arm_b"] = 140
    pp["dy"] = -2 if peek else 0
    pp["bob"] = (-1 if f else 0) if peek else 3

    def late(pp):                      # arms/sheath hidden only while the bush is there
        b = bool(pp.get("bush", True))
        pp["hide_arm_f"] = pp["hide_arm_b"] = b
        pp["sheathed"] = not b
    pp["late"] = [late]
    pp["expr"] = ("love" if (t % 4.4) < 2.2 else "peek") if peek else "blink"

    def bush(img, ctx, peek=peek):
        from chars.rig import OX, OY
        has_bush = ctx["params"].get("bush", True)
        if has_bush:
            b = _bush(step_frame(ctx["t"], 4, 2) if peek else 0)
            bx, by = OX - 13, OY - b.height
            img.alpha_composite(b, (bx, by))
        # meaty hands gripping the top of the bush
        if peek:
            for hx in ((OX + 1, OX + 8) if has_bush else ()):
                rect(img, hx - 2, by, 5, 4, INK)
                rect(img, hx - 1, by + 1, 3, 2, SKIN)
                pset(img, hx + 1, by + 2, (228, 164, 132))
            # floating hearts
            X, Y, _, _ = ctx["head"]
            for k in range(2):
                ph = ((ctx["t"] + k * 0.6) % 1.2) / 1.2
                hx = int(X) + 18 + k * 4 + int(math.sin(ph * 6 + k) * 1.5)
                hy = int(Y) + 4 - int(ph * 10)
                if ph < 0.85:
                    _heart(img, hx, hy)
    pp["props"] = [bush]


def _heart(img, x, y, col=(236, 56, 90)):
    for (dx, dy) in ((0, 0), (2, 0), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (0, 2), (1, 2), (2, 2), (1, 3)):
        pset(img, x + dx, y + dy, col)
    pset(img, x, y, (255, 150, 170))


def gorilla(pp, pose, t, p, d):
    """Kondo stands like a friendly gorilla: arms held a little away from the body."""
    if pose in ("idle", "talk", "walk", "think", "sit"):
        pp["arm_b"] -= 6
        if pose in ("idle", "walk"):
            pp["arm_f"] += 6


KONDO = register(SSGDef(
    id="kondo", name="近藤", color=(150, 96, 60), voice=0.68,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=SSG_TORSO_PAL,
    neck=(8, 2), hip=(8, 10), shoulder_f=(12, 3), shoulder_b=(3, 3),
    arm_len=8, arm_w=3, sleeve_f=SSG_SLEEVE_F, sleeve_b=SSG_SLEEVE_B, sleeve_frac=0.8,
    hand=SKIN,
    leg_len=7, leg_w=4, leg_gap=5, pants=SSG_PANTS, shoes=SSG_SHOES,
    weapon="katana", weapon_len=18, sheathed=sheathed_katana,
    poses={"stalk": pose_stalk, "shoulder": katana_on_shoulder},
    tweak=gorilla,
    extra_params={"bush": True},
    desc="真选组局长。刺猬头、胡茬、方下巴的『大猩猩』，阿妙的跟踪狂，却是最有人望的老大。",
))
