"""Core constants, timing/easing helpers and the Scene base class.

Every scene is a PURE FUNCTION of time: render(img, t) must draw the same
picture for the same t, with no state carried between frames. Use
rng(...) (deterministic) instead of the random module's global state.
"""
import math
import random
import zlib

W, H = 384, 216          # internal pixel canvas
SCALE = 5                # output = 1920x1080 (nearest-neighbour upscale)
FPS = 30                 # output frame rate
ANIM_FPS = 12            # default "pixel animation" frame rate for sprites


# ---------------------------------------------------------------- math utils
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def lerp2(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def lerp_color(c1, c2, t):
    t = clamp(t)
    return tuple(int(round(c1[i] + (c2[i] - c1[i]) * t)) for i in range(len(c1)))


def seg(t, t0, t1):
    """Normalised progress of t through [t0, t1], clamped to 0..1."""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return clamp((t - t0) / (t1 - t0))


def active(t, t0, t1):
    return t0 <= t < t1


def ease_in(x):
    return x * x * x


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    return 4 * x * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out_back(x, s=1.70158):
    x = x - 1
    return x * x * ((s + 1) * x + s) + 1


def ease_out_elastic(x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi) / 3) + 1


def ease_out_bounce(x):
    n1, d1 = 7.5625, 2.75
    if x < 1 / d1:
        return n1 * x * x
    if x < 2 / d1:
        x -= 1.5 / d1
        return n1 * x * x + 0.75
    if x < 2.5 / d1:
        x -= 2.25 / d1
        return n1 * x * x + 0.9375
    x -= 2.625 / d1
    return n1 * x * x + 0.984375


def wave(t, freq=1.0, amp=1.0, phase=0.0):
    return math.sin((t * freq + phase) * 2 * math.pi) * amp


def step_frame(t, fps=ANIM_FPS, n=None):
    """Integer animation frame for time t (optionally modulo n)."""
    f = int(math.floor(t * fps + 1e-6))
    return f % n if n else f


def quant(t, fps=ANIM_FPS):
    """Quantise time to the pixel-animation frame grid (gives choppy retro motion)."""
    return math.floor(t * fps + 1e-6) / fps


def ipos(x, y):
    return int(round(x)), int(round(y))


def stable_hash(*keys):
    return zlib.crc32(repr(keys).encode("utf-8")) & 0xFFFFFFFF


def rng(*keys):
    """Deterministic RNG seeded from arbitrary keys (never use global random)."""
    return random.Random(stable_hash(*keys))


def arc(p0, p1, t, height):
    """Point on a parabolic jump arc from p0 to p1 with apex `height` px above."""
    x = lerp(p0[0], p1[0], t)
    y = lerp(p0[1], p1[1], t) - 4 * height * t * (1 - t)
    return x, y


# ---------------------------------------------------------------- data types
class Cue:
    """A sound-effect trigger at scene-local time `time` (seconds).
    dur: for looping ambience SFX (e.g. 'rain', 'crowd', 'wind', 'fire'),
         how long to keep it playing (seconds); ignored for one-shots."""
    __slots__ = ("time", "name", "vol", "pitch", "pan", "dur")

    def __init__(self, time, name, vol=1.0, pitch=1.0, pan=0.0, dur=None):
        self.time, self.name, self.vol, self.pitch, self.pan, self.dur = time, name, vol, pitch, pan, dur

    def __repr__(self):
        return f"Cue({self.time:.2f}, {self.name!r}, vol={self.vol}, pitch={self.pitch})"


class Scene:
    """Base class. Subclass it in scenes/sNN_xxx.py and expose SCENE = MyScene().

    Attributes
    ----------
    id        : 'sNN'
    title     : human readable title (Chinese)
    duration  : seconds
    music     : track name | None | list of (t, track_or_None) switch points
    music_vol : 0..1 relative loudness of the music in this scene
    subs      : list of (t0, t1, speaker_id_or_None, text)
                speaker None  -> narration style (centred outlined text)
                speaker 'id'  -> dialogue box with name tag (+portrait)
    subs_pos  : 'bottom' | 'top'
    fade_in / fade_out : automatic fade from/to black (seconds, 0 to disable)
    """

    id = "s00"
    title = ""
    duration = 10.0
    music = None
    music_vol = 0.55
    subs = []
    subs_pos = "bottom"
    fade_in = 0.3
    fade_out = 0.3

    def render(self, img, t):  # pragma: no cover - abstract
        raise NotImplementedError

    def cues(self):
        return []
