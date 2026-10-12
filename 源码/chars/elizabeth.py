"""伊丽莎白 Elizabeth — Katsura's mysterious pet: a tall white duck/ghost blob
with a big yellow bill, round staring eyes and little yellow feet. Speaks only
through a signboard.

Custom renderer (facing right, feet anchor, 12 fps stepping, cached sprites).
Poses: idle, walk (waddle), run, run_away, sign (kw sign="文字"; with p given the
board pops up during p 0..0.25), sad, talk (= sign when sign= given, else beak
flap), shout, shock, hit, fly, lie, sleep, jump, land, sit, kneel, cheer, bow,
cry, wave, attack/slash_up/thrust/punch/ready/guard/shoulder (swings the
signboard like a club), + any other name falls back to idle.
Expressions: normal blink talk angry determined shout shock happy sad cry hurt smug.
"""
import math

from PIL import Image

from engine.core import step_frame, clamp, lerp, ease_out, ease_out_back, ease_in_out, ANIM_FPS
from engine.gfx import INK, ascii_sprite, stamp_line, rect, pset
from engine.text import draw_text, text_width
from chars import register
from chars.rig import CustomChar

PAL = {
    "o": INK,
    "W": (250, 250, 255),   # body white
    "w": (212, 216, 232),   # shade
    "g": (168, 174, 198),   # deep shade
    "k": (20, 18, 30),      # pupil
    "Y": (255, 214, 70),    # bill
    "L": (255, 244, 170),   # bill shine
    "y": (228, 160, 40),    # bill shade
    "r": (190, 90, 60),     # inside of the bill
    "T": (120, 200, 255),   # tears
    "B": (90, 120, 220),    # gloom lines
    "p": (250, 150, 150),   # blush
    "s": (140, 210, 255),   # sweat
}

# 22 x 35 body, facing right. Rows 5-9 eyes, 10-14 bill.
BODY = [
    "......ooooooooo.......",   # 0
    "....ooWWWWWWWWWoo.....",   # 1
    "...oWWWWWWWWWWWWWo....",   # 2
    "..oWWWWWWWWWWWWWWwo...",   # 3
    ".oWWWWWooooWWooooWwo..",   # 4  big round eyes
    ".oWWWWoWWWWooWWWWowo..",   # 5
    ".oWWWWoWWkkooWWkkowo..",   # 6
    ".oWWWWoWWkkooWWkkowo..",   # 7
    ".oWWWWoWWWWooWWWWowo..",   # 8
    ".oWWWWWooooWWooooWwo..",   # 9
    ".oWWWWooooooooooooooo.",   # 10 bill
    ".oWWWoYLLYYYYYYYYYYYYo",   # 11
    ".oWWWoYYYYYYYYYYYYYYYo",   # 12
    ".oWWWoyoooooooooooooo.",   # 13 mouth line
    ".oWWWWoyyyyyyyyyyyyo..",   # 14
    ".oWWWWWooooooooooooo..",   # 15
    ".oWWWWWWWWWWWWWWWWwo..",   # 16
    "oWWWWWWWWWWWWWWWWWwo..",   # 17
    "oWWWWWWWWWWWWWWWWWwwo.",   # 18
    "oWWWWWWWWWWWWWWWWWwwo.",   # 19
    "oWWWWWWWWWWWWWWWWWwwo.",   # 20
    "oWWWWWWWWWWWWWWWWWwwo.",   # 21
    "oWWWWWWWWWWWWWWWWWwwo.",   # 22
    "oWWWWWWWWWWWWWWWWwwwo.",   # 23
    "owWWWWWWWWWWWWWWWwwwo.",   # 24
    "owWWWWWWWWWWWWWWWwwwo.",   # 25
    "owWWWWWWWWWWWWWWwwwwo.",   # 26
    "owWWWWWWWWWWWWWWwwwwo.",   # 27
    "owwWWWWWWWWWWWWwwwwgo.",   # 28
    "owwWWWWWWWWWWWWwwwwgo.",   # 29
    "owwwWWWWWWWWWWwwwwggo.",   # 30
    "owwwwWWWWWWWwwwwwwggo.",   # 31
    "owwwwwwwwwwwwwwwwgggo.",   # 32
    "owgwwwgwwwwgwwwwgggo..",   # 33 hem folds
    ".oooo.oooo.ooooo.oo...",   # 34 wavy hem
]

H_BODY = len(BODY)


def _mk(**rows):
    r = list(BODY)
    for k, v in rows.items():
        i = int(k[1:])
        assert len(v) == len(BODY[i]), (k, v, len(v), len(BODY[i]))
        r[i] = v
    return "\n".join(r)


_PL = ".oWWWWWWWWWWWWWWWWwo.."
_EYE_T = ".oWWWWWooooWWooooWwo.."
_EYE_S = ".oWWWWoWWWWooWWWWowo.."
_LID = ".oWWWWoooooooooooowo.."
EXPRS = {
    "normal": _mk(),
    "blink": _mk(r4=_PL, r5=_PL, r6=_PL, r7=".oWWWWWooooWWooooWwo..", r8=_PL, r9=_PL),
    "talk": _mk(r13=".oWWWoyrrrrrrrrrrrrro.", r14=".oWWWWorrrrrrrrrrrro..",
                r15=".oWWWWoyyyyyyyyyyyyo..", r16=".oWWWWWooooooooooooo.."),
    "angry": _mk(r4=_PL, r5=_LID, r6=".oWWWWoWWkkooWWkkowo..", r8=_EYE_S),
    "shock": _mk(r6=_EYE_S, r7=".oWWWWoWWkWooWWkWowo..", r8=_EYE_S,
                 r13=".oWWWoyrrrrrrrrrrrrro.", r14=".oWWWWoooooooooooooo.."),
    "happy": _mk(r4=_PL, r5=_PL, r6=_EYE_T, r7=_EYE_S,
                 r8=".oWWWWWppWWWWppWWWwo..", r9=_PL),
    "sad": _mk(r4=_PL, r5=_PL, r6=_LID, r7=_EYE_S, r8=".oWWWWoWWkkooWWkkowo..", r9=_EYE_T),
    "cry": _mk(r4=_PL, r5=_PL, r6=_LID, r7=".oWWWWoTTkkooTTkkowo..",
               r8=".oWWWWoTTTTooTTTTowo..", r9=".oWWWWWooTTWWooTTWwo..",
               r16=".oWWWWWWWWWWWWWWWWwo..".replace("WWWWWWWW", "TWWWWWWT", 1)),
    "hurt": _mk(r5=".oWWWWokWWkookWWkowo..", r6=".oWWWWoWkkWooWkkWowo..",
                r7=".oWWWWoWkkWooWkkWowo..", r8=".oWWWWokWWkookWWkowo.."),
    "smug": _mk(r4=_PL, r5=_PL, r6=_LID, r7=".oWWWWoWWkkooWWkkowo..", r8=_EYE_S),
}
EXPRS["determined"] = EXPRS["angry"]
EXPRS["shout"] = _mk(r4=_PL, r5=_LID, r6=".oWWWWoWWkkooWWkkowo..", r8=_EYE_S,
                     r12=".oWWWoYYYYYYYYYYYYYYYo", r13=".oWWWoyrrrrrrrrrrrrro.",
                     r14=".oWWWWorrrrrrrrrrrro..", r15=".oWWWWorrrrrrrrrrrro..",
                     r16=".oWWWWoyyyyyyyyyyyyo..", r17="oWWWWWWooooooooooooo..")
FALLBACK = {"laugh": "happy", "scared": "shock", "dizzy": "hurt", "sleep": "blink",
            "serious": "angry", "cool": "normal", "gloom": "sad", "deadpan": "normal",
            "evil": "smug", "blush": "happy"}

_cache = {}


def _body(expr):
    e = expr or "normal"
    if e not in EXPRS:
        e = FALLBACK.get(e, "normal")
    s = _cache.get(("body", e))
    if s is None:
        s = ascii_sprite(EXPRS[e], PAL)
        _cache[("body", e)] = s
    return s


def _board(text):
    """White signboard sprite with black 12px text."""
    key = ("board", text)
    s = _cache.get(key)
    if s is None:
        tw = max(text_width(text, 12), 8) if text else 8
        w, h = tw + 8, 17
        s = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        rect(s, 0, 0, w, h, INK)
        rect(s, 1, 1, w - 2, h - 2, (252, 252, 246))
        rect(s, 1, h - 3, w - 2, 2, (214, 212, 204))
        rect(s, 1, 1, w - 2, 1, (255, 255, 255))
        if text:
            draw_text(s, 4, 3, text, INK, size=12)
        _cache[key] = s
    return s


def _feet(img, x, y, t, mode="stand", ph=0.0):
    """Two little yellow duck feet under the hem. (x, y) = centre bottom."""
    Y, y2 = PAL["Y"], PAL["y"]
    offs = [(-5, 0), (3, 0)]
    if mode == "walk":
        a = math.sin(ph)
        offs = [(-5 + a * 2, -max(0, a) * 2), (3 - a * 2, -max(0, -a) * 2)]
    elif mode == "run":
        a = math.sin(ph)
        offs = [(-5 + a * 3, -max(0, a) * 3), (3 - a * 3, -max(0, -a) * 3)]
    elif mode == "dangle":
        offs = [(-5, 1), (3, 2)]
    elif mode == "back":
        offs = [(-5, 0)]
    for i, (dx, dy) in enumerate(offs):
        fx, fy = int(round(x + dx)), int(round(y + dy))
        rect(img, fx - 1, fy - 3, 7, 4, INK)
        rect(img, fx, fy - 2, 5, 2, Y if i else y2)
        pset(img, fx + 4, fy - 3, INK)
        pset(img, fx, fy - 1, y2 if i else (200, 130, 30))


def _hand(img, x, y):
    x, y = int(round(x)), int(round(y))
    rect(img, x - 2, y - 2, 5, 5, INK)
    rect(img, x - 1, y - 1, 3, 3, PAL["W"])
    pset(img, x + 1, y + 1, PAL["w"])


def _shear(spr, s):
    """Lean the body: top rows shift by s px (waddle / run lean)."""
    if not s:
        return spr
    h = spr.height
    out = Image.new("RGBA", (spr.width + 4, h), (0, 0, 0, 0))
    for y in range(h):
        dx = int(round(s * (h - 1 - y) / (h - 1))) + 2
        out.paste(spr.crop((0, y, spr.width, y + 1)), (dx, y))
    return out


CW, CH = 180, 110
AX, AY = 60, 100


class Elizabeth(CustomChar):
    poses = {k: None for k in (
        "idle walk run run_away sign sad talk shout shock hit fly lie sleep jump land sit "
        "kneel cheer bow cry wave attack slash_up thrust punch ready guard shoulder").split()}

    def head(self, expr="normal"):
        """Portrait crop: eyes + bill (22 x 17)."""
        key = ("head", expr)
        s = _cache.get(key)
        if s is None:
            s = _body(expr).crop((0, 0, 22, 17))
            _cache[key] = s
        return s

    def render(self, pose="idle", t=0.0, p=None, expr=None, **kw):
        tq = step_frame(t, ANIM_FPS) / ANIM_FPS
        f4 = step_frame(t, 4)
        blink = (t % 3.4) < 0.12
        e = "blink" if blink else "normal"
        dy = 0          # body lift
        shear = 0
        feet = "stand"
        ph = 0.0
        rot = 0
        sign = kw.get("sign")
        board = None          # (text, pop 0..1, mode)
        hand = None
        extra = []            # extra overlays: callables(img, bx, by)
        squash = 0

        if pose == "walk":
            ph = tq * 2 * math.pi * 1.6
            shear = 1 if math.sin(ph) > 0 else -1
            dy = -1 if math.cos(ph * 2) > 0 else 0
            feet = "walk"
        elif pose in ("run", "run_away"):
            ph = tq * 2 * math.pi * 2.8
            shear = 3
            dy = -2 if math.sin(ph * 2) > 0 else 0
            feet = "run"
            if pose == "run_away":
                e = "shock"
                extra.append(("sweat", None))
        elif pose == "sign" or (pose == "talk" and sign is not None):
            dy = -1 if f4 % 2 else 0
            pop = 1.0 if p is None else ease_out_back(clamp(p / 0.25))
            board = (sign if sign is not None else "……", pop, "hold")
        elif pose == "talk":
            e = "talk" if step_frame(t, 8) % 2 == 0 else "normal"
            dy = -1 if f4 % 2 else 0
        elif pose == "shout":
            e = "shout" if step_frame(t, 10) % 2 == 0 else "angry"
            shear = 1
            dy = -1 if step_frame(t, 10) % 2 == 0 else 0
        elif pose == "sad":
            e = "sad"
            squash = 1
            shear = -1
            extra.append(("gloom", None))
        elif pose == "cry":
            e = "cry"
            dy = -1 if step_frame(t, 10) % 2 else 0
        elif pose == "shock":
            pp_ = 0.0 if p is None else p
            e = "shock"
            dy = -int(5 * math.sin(clamp(pp_ * 5) * math.pi)) if pp_ < 0.2 else 0
            shear = int(math.sin(t * 50) * 1)
            extra.append(("sweat", None))
            feet = "dangle" if dy < 0 else "stand"
        elif pose == "hit":
            pp_ = 0.5 if p is None else p
            rot = int(25 * ease_out(clamp(pp_ * 2)))
            e = "hurt"
            feet = "dangle"
        elif pose == "fly":
            rot = int((t * 720) % 360)
            e = "hurt"
            feet = "dangle"
        elif pose in ("lie", "sleep"):
            rot = 90
            e = "hurt" if pose == "lie" else "blink"
            if pose == "sleep":
                extra.append(("zzz", None))
        elif pose == "jump":
            e = "angry"
            feet = "dangle"
            shear = 1
        elif pose == "land":
            pp_ = 0.0 if p is None else p
            squash = 2 if pp_ < 0.3 else 0
        elif pose in ("sit", "kneel"):
            squash = 2
            feet = "none"
            e = e if pose == "sit" else "sad"
        elif pose == "cheer":
            f = step_frame(t, 8, 2)
            dy = -3 if f else 0
            feet = "dangle" if f else "stand"
            e = "happy"
            hand = "up"
        elif pose == "wave":
            e = "happy"
            hand = "wave"
        elif pose == "bow":
            shear = 3
            squash = 1
            e = "blink"
        elif pose == "kick":
            # gag: a hairy middle-aged man's leg shoots out from under the sheet
            pp_ = (t % 1.0) if p is None else p
            e = "angry"
            shear = -2
            dy = -2
            feet = "back"
            extra.append(("leg", ease_out(clamp(pp_ * 3))))
        elif pose == "point":
            pp_ = (t % 1.0) if p is None else p
            e = "shout" if step_frame(t, 8) % 2 == 0 else "angry"
            shear = 1
            hand = ("point", ease_out_back(clamp(pp_ * 4)))
        elif pose == "think":
            hand = "think"
        elif pose in ("attack", "slash_up", "thrust", "punch", "ready", "guard", "shoulder"):
            pp_ = (t % 1.0) if p is None else p
            e = "angry"
            if pose in ("ready", "guard", "shoulder"):
                ang = {"ready": 60, "guard": 95, "shoulder": 150}[pose]
                dy = -1 if f4 % 2 else 0
            elif pose == "slash_up":
                ang = lerp(-40, 120, ease_in_out(clamp(pp_ / 0.5)))
            elif pose in ("thrust", "punch"):
                ang = 5
                shear = int(lerp(-1, 3, ease_out(clamp(pp_ * 3))))
            else:
                if pp_ < 0.35:
                    ang = lerp(60, 150, ease_out(pp_ / 0.35))
                elif pp_ < 0.55:
                    ang = lerp(150, -30, ease_in_out((pp_ - 0.35) / 0.2))
                    shear = 2
                else:
                    ang = -30
                    shear = 2
            board = (sign if sign is not None else "", 1.0, ("club", ang))
        # ---------------- compose
        spr = _body(expr or e)
        if squash:
            spr = spr.resize((spr.width + squash, spr.height - squash * 2), Image.NEAREST)
        spr = _shear(spr, shear)
        img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        bw, bh = spr.size
        bx = AX - bw // 2 + (1 if shear else 0)
        foot_h = 2 if feet != "none" else 0
        by = AY - foot_h - bh + dy
        if feet != "none":
            _feet(img, AX, AY + (dy if feet == "dangle" else 0), t, feet, ph)
        img.alpha_composite(spr, (bx, by))
        top = by
        right = bx + bw - 2
        if board:
            text, pop, mode = board
            b = _board(text)
            if mode == "hold":
                hx, hy = right + 3, by + 21
                sx = hx + 1
                btop = by - 11 + int((1 - pop) * 24)
                bl = right - 1
                # stick
                stamp_line(img, (sx, btop + b.height - 1), (sx, hy + 2), 3, INK)
                stamp_line(img, (sx, btop + b.height - 1), (sx, hy + 2), 1, (170, 120, 70))
                img.alpha_composite(b, (bl, btop))
                _hand(img, sx, hy)
            else:   # club swing: board on a stick, rotated
                ang = mode[1]
                hx, hy = right - 2, by + 20
                a = math.radians(ang)
                vx, vy = math.cos(a), -math.sin(a)
                L = 10
                tip = (hx + vx * L, hy + vy * L)
                stamp_line(img, (hx, hy), tip, 3, INK)
                stamp_line(img, (hx, hy), tip, 1, (170, 120, 70))
                small = b if b.width <= 20 else b
                rb = small.rotate(ang - 90, resample=Image.NEAREST, expand=True)
                img.alpha_composite(rb, (int(tip[0] + vx * rb.width * 0.3 - rb.width / 2),
                                         int(tip[1] + vy * rb.height * 0.3 - rb.height / 2)))
                _hand(img, hx, hy)
        if hand == "up":
            _hand(img, right + 1, by + 10 + (step_frame(t, 8) % 2))
            _hand(img, bx + 1, by + 10 + (1 - step_frame(t, 8) % 2))
        elif hand == "wave":
            _hand(img, right + 2 + (step_frame(t, 6) % 2), by + 13)
        elif hand == "think":
            _hand(img, right, by + 16)
        elif isinstance(hand, tuple) and hand[0] == "point":
            k = hand[1]
            ex = right - 1 + 7 * k
            stamp_line(img, (right - 2, by + 18), (ex, by + 17), 4, INK)
            stamp_line(img, (right - 2, by + 18), (ex, by + 17), 2, PAL["W"])
            _hand(img, ex, by + 17)
        for kind, _ in extra:
            if kind == "sweat":
                sx, sy = bx + 3, by + 2 + (step_frame(t, 6) % 3)
                rect(img, sx - 1, sy - 1, 3, 5, INK)
                rect(img, sx, sy, 1, 3, PAL["s"])
            elif kind == "gloom":
                for i in range(3):
                    gx = bx + 4 + i * 4
                    for j in range(4):
                        if (j + step_frame(t, 4)) % 4 != 3:
                            pset(img, gx, by + 1 + j * 2, PAL["B"])
            elif kind == "leg":
                k = _
                hx0, hy0 = AX + 3, AY - 4 + dy
                fx, fy = hx0 + 6 + 13 * k, hy0 + 1 - 8 * k
                skin, hair = (255, 204, 170), (70, 50, 40)
                stamp_line(img, (hx0, hy0), (fx, fy), 6, INK)
                stamp_line(img, (hx0, hy0), (fx, fy), 4, skin)
                for i in range(1, 5):                      # leg hair
                    q = i / 5.0
                    pset(img, hx0 + (fx - hx0) * q, hy0 + (fy - hy0) * q - 1, hair)
                    if i % 2:
                        pset(img, hx0 + (fx - hx0) * q + 1, hy0 + (fy - hy0) * q, hair)
                rect(img, int(fx) - 1, int(fy) - 3, 5, 6, INK)   # bare foot
                rect(img, int(fx), int(fy) - 2, 3, 4, skin)
                pset(img, fx + 2, fy - 2, (236, 170, 140))
                img.alpha_composite(spr, (bx, by))            # sheet stays over the thigh
            elif kind == "zzz":
                zy = by - 4 - (step_frame(t, 3) % 3) * 2
                draw_text(img, right + 2, zy - 10, "z", (230, 230, 255), size=12, outline=INK)
        if rot:
            img = img.rotate(rot, resample=Image.NEAREST, center=(AX, AY - 17))
            if rot == 90:
                bb = img.getbbox()
                if bb:
                    img = img.transform(img.size, Image.AFFINE, (1, 0, 0, 0, 1, bb[3] - AY),
                                        resample=Image.NEAREST)
        return img, AX, AY


ELIZABETH = register(Elizabeth(
    "elizabeth", "伊丽莎白", (206, 144, 36), voice=0.66,
    desc="桂的宠物（？）。白色鸭子般的谜之生物，从不开口，只举牌子说话。据说里面是个大叔。",
))
