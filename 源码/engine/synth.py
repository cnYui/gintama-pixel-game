"""Tiny chiptune synth toolkit (numpy). All buffers are float32 mono at SR
unless stated; stereo buffers have shape (n, 2)."""
import math
import re

import numpy as np

SR = 44100

_NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(note):
    """'A4' / 'C#5' / 'Eb3' -> midi number."""
    m = re.fullmatch(r"([A-Ga-g])([#b]?)(-?\d)", note)
    if not m:
        raise ValueError(note)
    n = _NOTE[m.group(1).upper()] + {"#": 1, "b": -1, "": 0}[m.group(2)]
    return 12 * (int(m.group(3)) + 1) + n


def freq(note_or_midi):
    m = midi(note_or_midi) if isinstance(note_or_midi, str) else note_or_midi
    return 440.0 * 2 ** ((m - 69) / 12)


def n_samples(dur):
    return max(1, int(round(dur * SR)))


def _phase(f, dur):
    """Phase accumulator; f may be scalar or per-sample array (for sweeps/vibrato)."""
    n = n_samples(dur)
    if np.isscalar(f):
        return (np.arange(n) * (f / SR)) % 1.0
    f = np.asarray(f, np.float64)
    if len(f) != n:
        f = np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(f)), f)
    return np.cumsum(f / SR) % 1.0


def square(f, dur, duty=0.5):
    return np.where(_phase(f, dur) < duty, 1.0, -1.0).astype(np.float32)


pulse = square


def triangle(f, dur):
    ph = _phase(f, dur)
    return (4 * np.abs(ph - 0.5) - 1).astype(np.float32)


def saw(f, dur):
    return (2 * _phase(f, dur) - 1).astype(np.float32)


def sine(f, dur):
    return np.sin(2 * np.pi * _phase(f, dur)).astype(np.float32)


def noise(dur, seed=0, color=0.0):
    """White noise; color>0 low-passes it (0..0.99)."""
    r = np.random.default_rng(seed)
    x = r.uniform(-1, 1, n_samples(dur)).astype(np.float32)
    if color > 0:
        x = lowpass_k(x, 1 - color)
    return x


def nes_noise(dur, period=8, seed=1):
    """Crunchy 'NES' noise: sample-and-hold white noise."""
    r = np.random.default_rng(seed)
    n = n_samples(dur)
    vals = r.uniform(-1, 1, n // period + 2).astype(np.float32)
    return np.repeat(vals, period)[:n]


def sweep(f0, f1, dur, curve="exp"):
    n = n_samples(dur)
    t = np.linspace(0, 1, n)
    if curve == "exp" and f0 > 0 and f1 > 0:
        return f0 * (f1 / f0) ** t
    return f0 + (f1 - f0) * t


def vibrato(f, dur, rate=5.5, depth=0.012):
    n = n_samples(dur)
    t = np.arange(n) / SR
    return f * (1 + depth * np.sin(2 * np.pi * rate * t))


# ------------------------------------------------------------------ envelopes
def adsr(n, a=0.005, d=0.05, s=0.7, r=0.05, sr=SR):
    n = int(n)
    A, D, R = int(a * sr), int(d * sr), int(r * sr)
    S = max(0, n - A - D - R)
    env = np.concatenate([
        np.linspace(0, 1, max(A, 1), endpoint=False),
        np.linspace(1, s, max(D, 1), endpoint=False),
        np.full(S, s),
        np.linspace(s, 0, max(R, 1)),
    ]).astype(np.float32)
    if len(env) < n:
        env = np.pad(env, (0, n - len(env)))
    return env[:n]


def decay(n, k=6.0):
    """Exponential decay envelope over n samples (k = speed)."""
    t = np.linspace(0, 1, int(n), dtype=np.float32)
    return np.exp(-k * t).astype(np.float32)


def apply_env(x, env):
    return (x * env[: len(x)]).astype(np.float32)


# ------------------------------------------------------------------ filters/fx
def lowpass_k(x, k):
    """One-pole lowpass with coefficient k in (0,1]; smaller = darker."""
    y = np.empty_like(x)
    acc = 0.0
    # vectorised via scipy-free recursive loop in chunks (fast enough for SFX/music)
    for i in range(len(x)):
        acc += k * (x[i] - acc)
        y[i] = acc
    return y


def lowpass(x, cutoff):
    k = 1 - math.exp(-2 * math.pi * cutoff / SR)
    return _iir1(x, k)


def highpass(x, cutoff):
    return (x - lowpass(x, cutoff)).astype(np.float32)


def _iir1(x, k):
    # fast one-pole using scipy if present, else python loop
    try:
        from scipy.signal import lfilter
        return lfilter([k], [1, -(1 - k)], x).astype(np.float32)
    except Exception:
        return lowpass_k(x.astype(np.float32), k)


def delay(x, time=0.25, feedback=0.35, mix=0.3, taps=4):
    d = n_samples(time)
    out = x.astype(np.float32).copy()
    g = mix
    for i in range(1, taps + 1):
        if d * i >= len(out):
            break
        out[d * i:] += x[: len(out) - d * i] * g
        g *= feedback
    return out


def bitcrush(x, bits=6):
    q = 2 ** (bits - 1)
    return (np.round(x * q) / q).astype(np.float32)


# ------------------------------------------------------------------ mixing
def pad_to(x, n):
    if len(x) >= n:
        return x[:n]
    if x.ndim == 2:
        return np.pad(x, ((0, n - len(x)), (0, 0)))
    return np.pad(x, (0, n - len(x)))


def mix(*bufs):
    bufs = [b for b in bufs if b is not None and len(b)]
    if not bufs:
        return np.zeros(1, np.float32)
    n = max(len(b) for b in bufs)
    stereo = any(b.ndim == 2 for b in bufs)
    out = np.zeros((n, 2) if stereo else n, np.float32)
    for b in bufs:
        if stereo and b.ndim == 1:
            b = np.stack([b, b], 1)
        out[: len(b)] += b
    return out


def place(dst, src, at_sample, gain=1.0):
    """Add src into dst starting at at_sample (clipped to dst length)."""
    if at_sample >= len(dst):
        return
    if at_sample < 0:
        src = src[-at_sample:]
        at_sample = 0
    n = min(len(src), len(dst) - at_sample)
    if n <= 0:
        return
    if dst.ndim == 2 and src.ndim == 1:
        dst[at_sample:at_sample + n] += (src[:n] * gain)[:, None]
    else:
        dst[at_sample:at_sample + n] += src[:n] * gain


def stereo(x, pan=0.0):
    """Mono -> stereo with constant-power pan (-1 left .. 1 right)."""
    if x.ndim == 2:
        return x
    a = (pan + 1) * math.pi / 4
    return np.stack([x * math.cos(a), x * math.sin(a)], 1).astype(np.float32) * 1.4142


def resample(x, ratio):
    """Pitch-shift by resampling (ratio>1 = higher & shorter)."""
    if abs(ratio - 1) < 1e-4:
        return x
    n = max(1, int(len(x) / ratio))
    src = np.linspace(0, len(x) - 1, n)
    if x.ndim == 2:
        return np.stack([np.interp(src, np.arange(len(x)), x[:, c]) for c in range(2)], 1).astype(np.float32)
    return np.interp(src, np.arange(len(x)), x).astype(np.float32)


def normalize(x, peak=0.9):
    m = float(np.max(np.abs(x))) if len(x) else 0
    return (x * (peak / m)).astype(np.float32) if m > 1e-9 else x


def soft_clip(x, drive=1.0):
    return np.tanh(x * drive).astype(np.float32)


# ------------------------------------------------------------------ sequencing
def parse_seq(s):
    """'C5:1 E5:.5 G5:.5 R:1 [C4,E4,G4]:2' -> list of (notes|None, beats).
    '-' extends previous note (tie), R = rest."""
    out = []
    for tok in s.split():
        name, _, dur = tok.partition(":")
        beats = float(dur) if dur else 1.0
        if name in ("R", "r", "_"):
            out.append((None, beats))
        elif name == "-" and out:
            n, b = out[-1]
            out[-1] = (n, b + beats)
        elif name.startswith("["):
            out.append((name.strip("[]").split(","), beats))
        else:
            out.append(([name], beats))
    return out


def render_seq(seq, bpm, instrument, gain=1.0, total_beats=None):
    """Render a parsed/str sequence with instrument(freq_hz, dur_s) -> mono buf."""
    if isinstance(seq, str):
        seq = parse_seq(seq)
    spb = 60.0 / bpm
    beats = sum(b for _, b in seq) if total_beats is None else total_beats
    out = np.zeros(n_samples(beats * spb) + SR, np.float32)
    pos = 0.0
    for notes, b in seq:
        dur = b * spb
        if notes:
            for nm in notes:
                buf = instrument(freq(nm), dur)
                place(out, buf * gain, n_samples(pos))
        pos += dur
    return out[: n_samples(beats * spb)]


# ------------------------------------------------------------------ instruments
def inst_pulse(duty=0.5, a=0.004, d=0.08, s=0.55, r=0.04, vib=0.0):
    def f(hz, dur):
        fr = vibrato(hz, dur, depth=vib) if vib else hz
        x = square(fr, dur, duty)
        return apply_env(x, adsr(len(x), a, d, s, min(r, dur * 0.4))) * 0.25
    return f


def inst_tri(a=0.003, d=0.05, s=0.9, r=0.03):
    def f(hz, dur):
        x = triangle(hz, dur)
        return apply_env(x, adsr(len(x), a, d, s, min(r, dur * 0.4))) * 0.4
    return f


def inst_pluck(duty=0.25, k=5.0):
    def f(hz, dur):
        x = square(hz, dur, duty)
        return apply_env(x, decay(len(x), k)) * 0.25
    return f


def kick(dur=0.18):
    f = sweep(150, 40, dur)
    x = sine(f, dur)
    return apply_env(x, decay(len(x), 8)) * 0.9


def snare(dur=0.16, seed=3):
    x = nes_noise(dur, 3, seed) * 0.6 + triangle(190, dur) * 0.3
    return apply_env(x, decay(len(x), 10)) * 0.5


def hat(dur=0.05, seed=5, open_=False):
    x = highpass(noise(dur if not open_ else 0.2, seed), 6000)
    return apply_env(x, decay(len(x), 25 if not open_ else 8)) * 0.3


def drum_pattern(pattern, bpm, bars=1, steps_per_beat=4):
    """pattern: dict name->'x...x...' strings (one char per step); names in
    kick/snare/hat/ohat. Returns mono buffer for `bars` repetitions."""
    spb = 60.0 / bpm / steps_per_beat
    L = max(len(v) for v in pattern.values())
    out = np.zeros(n_samples(L * spb * bars) + SR // 2, np.float32)
    gens = {"kick": kick(), "snare": snare(), "hat": hat(), "ohat": hat(open_=True)}
    for b in range(bars):
        for name, pat in pattern.items():
            g = gens[name]
            for i, ch in enumerate(pat):
                if ch in "xX":
                    place(out, g * (1.0 if ch == "X" else 0.75), n_samples((b * L + i) * spb))
    return out[: n_samples(L * spb * bars)]
