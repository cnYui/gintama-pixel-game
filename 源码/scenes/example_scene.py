"""EXAMPLE scene (not part of the final video) — shows the idioms every scene
should use. Preview:  python preview.py example_scene
"""
import math

from engine.core import Scene, Cue, W, H, seg, lerp, ease_out, ease_in_out, wave, step_frame, rng, clamp
from engine.gfx import PAL, INK, gradient, rect, overlay_rect, shade, paste, polygon
from engine import fx
from engine.text import sfx_text, name_card, speech_bubble, draw_text
from chars import draw_char


def draw_street(img, cam_x, t):
    """Kabukicho street with 3 parallax layers. cam_x = camera x offset."""
    gradient(img, 0, 0, W, 120, (70, 110, 190), (250, 170, 120), steps=7)   # dusk sky
    # far roofs (parallax 0.2)
    for i in range(-1, 12):
        x = int(i * 48 - cam_x * 0.2) % (W + 96) - 48
        h = 30 + (i * 37 % 20)
        rect(img, x, 120 - h, 44, h, (78, 70, 110))
        polygon(img, [(x - 4, 120 - h), (x + 22, 120 - h - 10), (x + 48, 120 - h)], (60, 54, 92))
    # near buildings (parallax 0.6) with glowing windows + lanterns
    for i in range(-1, 8):
        x = int(i * 80 - cam_x * 0.6) % (W + 160) - 80
        rect(img, x, 70, 74, 90, (120, 78, 56))
        rect(img, x, 70, 74, 4, INK)
        for wy in (84, 112):
            for wx in (8, 40):
                on = (i + wy // 28 + wx) % 3 != 0
                rect(img, x + wx, wy, 22, 16, (255, 214, 120) if on else (60, 40, 40))
                rect(img, x + wx + 10, wy, 1, 16, INK)
        lx, ly = x + 70, 100 + int(wave(t, 0.5, 1.5, i * 0.3))
        rect(img, lx - 3, ly, 7, 10, INK)
        rect(img, lx - 2, ly + 1, 5, 8, (228, 59, 68))
    # ground
    rect(img, 0, 160, W, 56, (96, 88, 96))
    for i in range(-1, 20):
        x = int(i * 24 - cam_x) % (W + 24) - 24
        rect(img, x, 160, 1, 56, (84, 76, 86))
    rect(img, 0, 160, W, 2, (70, 64, 74))


class Example(Scene):
    id = "sXX"
    title = "示例"
    duration = 8.0
    music = "yorozuya"
    subs = [
        (3.4, 6.2, "gintoki", "啊——好想吃草莓牛奶芭菲啊。"),
        (6.3, 7.9, None, "（这就是万事屋老板的日常。）"),
    ]

    def render(self, img, t):
        cam = lerp(0, 60, ease_in_out(seg(t, 0, 3)))
        draw_street(img, cam, t)
        # Gintoki walks in, stops, picks nose
        if t < 3:
            x = lerp(60, 190, seg(t, 0, 3))
            draw_char(img, "gintoki", x, 176, "walk", t)
        else:
            draw_char(img, "gintoki", 190, 176, "nosepick" if t < 5.5 else "talk", t)
        # gag: flying bottle hits him at 5.5s
        if 5.0 <= t < 5.5:
            k = seg(t, 5.0, 5.5)
            bx, by = lerp(W + 10, 196, k), lerp(90, 150, k)
            rect(img, int(bx), int(by), 4, 6, (120, 200, 120))
        if t >= 5.5:
            fx.burst(img, t, 5.5, 196, 150, n=12, colors=[(255, 255, 255), (255, 230, 90)], seed=1)
            sfx_text(img, 230, 120, "砰!", t, 5.5, 0.8)
        name_card(img, t, 1.0, 2.3, "gintoki", "坂田银时", "万事屋老板·天然卷")
        dx, dy = fx.shake_offset(t, 5.5, 0.35, 4)
        fx.shift(img, dx, dy)

    def cues(self):
        return [Cue(5.5, "punch"), Cue(1.0, "whoosh")]


SCENE = Example()
