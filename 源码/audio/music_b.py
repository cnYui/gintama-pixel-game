"""audio/music_b.py -- composer B.

Tracks: tension, battle, yoshiwara, flashback, sad, epic.
All melodies and progressions are original compositions.

Palette (shared with composer A): NES-style band-limited pulse leads
(12.5 / 25 / 50 % duty), stepped triangle bass, noise drums, plus soft
sine/triangle bells, pads, taiko / koto / shamisen colours.

Every track is a seamless loop made of whole bars: notes are rendered into
a buffer one bar (+ echo / reverb tail) longer than the loop and the tail is
folded back onto the start, so the last bar rings into bar 1.  The harmony
of every last bar leads back into bar 1.
"""
import math
from fractions import Fraction

import numpy as np
from scipy.ndimage import maximum_filter1d
from scipy.signal import butter, lfilter

from engine.audio import track
from engine.core import rng
from engine.synth import SR, midi, n_samples

TAU = 2.0 * math.pi
STEMS = {}          # debug: track -> {part: (rms, A-weighted active rms)} (Song.mix)
ANALYZE = False     # set True (verify script) to measure A-weighted stem levels


# ======================================================================= DSP
def _nrng(*keys):
    return np.random.default_rng(rng("music_b", *keys).getrandbits(32))


def _noise(n, *keys):
    return _nrng(*keys).uniform(-1.0, 1.0, int(n))


def _hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


_BA = {}


def _filt(x, fc, kind="low", order=2):
    fc = float(min(max(fc, 10.0), SR * 0.45))
    key = (int(fc), kind, order)
    if key not in _BA:
        _BA[key] = butter(order, fc / (SR / 2.0), btype=kind)
    b, a = _BA[key]
    return lfilter(b, a, x, axis=0)


def _t(dur):
    n = n_samples(dur)
    return n, np.arange(n) / SR


def _phase(f, n):
    if np.isscalar(f):
        dt = f / SR
        return (np.arange(n) * dt) % 1.0, np.full(n, dt)
    dt = np.asarray(f, np.float64)[:n] / SR
    return np.cumsum(dt) % 1.0, dt


def _blep(t, dt):
    y = np.zeros_like(t)
    m = t < dt
    if m.any():
        x = t[m] / dt[m]
        y[m] = x + x - x * x - 1.0
    m = t > 1.0 - dt
    if m.any():
        x = (t[m] - 1.0) / dt[m]
        y[m] = x * x + x + x + 1.0
    return y


def _pulse(f, n, duty=0.5, bl=True):
    """Band-limited (polyBLEP) pulse, DC removed. bl=False: naive (dark pads/drones)."""
    ph, dt = _phase(f, n)
    y = np.where(ph < duty, 1.0, -1.0)
    if bl:
        y += _blep(ph, dt)
        y -= _blep((ph - duty) % 1.0, dt)
    return y - (2.0 * duty - 1.0)


def _tri(f, n, steps=0.0):
    ph, _ = _phase(f, n)
    y = 4.0 * np.abs(((ph + 0.25) % 1.0) - 0.5) - 1.0
    if steps:
        y = np.round(y * steps) / steps          # NES 4-bit stepped triangle
    return y


def _sin(f, n):
    ph, _ = _phase(f, n)
    return np.sin(TAU * ph)


def _env(ng, a=0.005, d=0.1, s=0.7, r=0.08):
    """Gate-length ADS + release tail appended (len = gate + release)."""
    ng = max(1, int(ng))
    A = max(1, int(a * SR))
    tau = max(1.0, d * SR / 3.0)
    R = max(2, int(r * SR))
    t = np.arange(ng, dtype=np.float64)
    e = np.where(t < A, t / A, s + (1.0 - s) * np.exp(-(t - A) / tau))
    rel = e[-1] * (1.0 - np.arange(R) / R) ** 2
    return np.concatenate([e, rel])


def _fade_end(y, ms=15):
    k = min(len(y), int(ms * SR / 1000))
    if k > 1:
        y[-k:] *= np.linspace(1.0, 0.0, k)
    return y


def _pan(x, p):
    a = (p + 1.0) * math.pi / 4.0
    return np.stack([x * math.cos(a), x * math.sin(a)], 1) * math.sqrt(2.0)


def _echo(x, d, fb, wet, pan=0.0, taps=7):
    """Ping-pong echo of a mono signal -> stereo (first repeat opposite side)."""
    n = len(x)
    out = np.zeros((n, 2))
    g = wet
    first = 1 if pan < 0 else 0
    for i in range(1, taps + 1):
        s = d * i
        if s >= n or g < 0.01:
            break
        ch = first if i % 2 else 1 - first
        out[s:, ch] += x[: n - s] * g * 0.8
        out[s:, 1 - ch] += x[: n - s] * g * 0.2
        g *= fb
    return _filt(out, 4200)


def _comb(x, D, fb, damp):
    z = x.copy()
    b, a = [1.0 - damp], [1.0, -damp]
    zi = np.zeros(1)
    n = len(x)
    for k in range(D, n, D):
        blk, zi = lfilter(b, a, z[k - D:k], zi=zi)
        m = min(D, n - k)
        z[k:k + m] += fb * blk[:m]
    return z


def _allpass(x, D, g=0.5):
    buf = x.copy()
    n = len(x)
    for k in range(D, n, D):
        m = min(D, n - k)
        buf[k:k + m] += g * buf[k - D:k - D + m]
    y = -x.copy()
    y[D:] += buf[:-D]
    return y


def _reverb(x, fb=0.84, damp=0.3):
    """Small Freeverb-style plate (block-vectorised). mono in -> stereo out."""
    x = _filt(x, 220, "high")
    outs = []
    for sp in (0, 23):
        acc = np.zeros(len(x))
        for D in (1116, 1188, 1277, 1356, 1422, 1491):
            acc += _comb(x, D + sp, fb, damp)
        for D in (556, 441, 341, 225):
            acc = _allpass(acc, D + sp)
        outs.append(acc)
    return _filt(np.stack(outs, 1) / 6.0, 5200)


def _aweight(x):
    from scipy.signal import bilinear
    f1, f2, f3, f4 = 20.598997, 107.65265, 737.86223, 12194.217
    num = [(TAU * f4) ** 2 * 10 ** (1.9997 / 20), 0, 0, 0, 0]
    den = np.polymul([1, 2 * TAU * f4, (TAU * f4) ** 2], [1, 2 * TAU * f1, (TAU * f1) ** 2])
    den = np.polymul(np.polymul(den, [1, TAU * f3]), [1, TAU * f2])
    b, a = bilinear(num, den, SR)
    return lfilter(b, a, x, axis=0)


def _active_rms(x):
    """RMS over 50 ms windows that are within 30 dB of the loudest window."""
    w = int(0.05 * SR)
    n = len(x) // w
    if n == 0:
        return 0.0
    e = np.mean(x[: n * w].reshape(n, -1) ** 2, axis=1)
    act = e > e.max() * 1e-3
    return float(np.sqrt(e[act].mean())) if act.any() else 0.0


def _limit(y, thr, win=0.01):
    """Look-ahead peak limiter, circular (keeps the loop seamless)."""
    n = len(y)
    a = np.max(np.abs(y), axis=1)
    w = max(3, int(win * SR)) | 1
    h = w // 2
    p = 2 * w
    ac = np.concatenate([a[-p:], a, a[:p]])
    g = np.minimum(1.0, thr / np.maximum(ac, 1e-9))
    g = -maximum_filter1d(-g, size=2 * w + 1)
    c = np.concatenate([[0.0], np.cumsum(g)])
    idx = np.arange(p, p + n)
    gs = (c[idx + h + 1] - c[idx - h]) / w
    return y * gs[:, None]


def _master(y, rms_t=0.16, peak=0.84):
    y = y - y.mean(axis=0)
    for _ in range(6):
        r = float(np.sqrt(np.mean(y ** 2)))
        y = y * (rms_t / max(r, 1e-9))
        if float(np.max(np.abs(y))) <= peak:
            break
        y = _limit(y, peak * 0.97)
    pk = float(np.max(np.abs(y)))
    if pk > peak:
        y = y * (peak / pk)
    return y.astype(np.float32)


# ================================================================ instruments
def i_pulse(duty=0.5, a=0.006, d=0.12, s=0.7, r=0.08, vib=0.0, vrate=5.5,
            vdelay=0.2, gain=0.3, scoop=0.0):
    def f(m, dur, vel=1.0, bend=0.0):
        env = _env(n_samples(dur), a, d, s, r)
        n = len(env)
        t = np.arange(n) / SR
        fr = np.full(n, _hz(m))
        if vib:
            ramp = np.clip((t - vdelay) / 0.3, 0.0, 1.0)
            fr *= 1.0 + vib * ramp * np.sin(TAU * vrate * t)
        b = bend or scoop
        if b:
            fr *= 2.0 ** (-b / 12.0 * np.exp(-t / 0.045))
        return _pulse(fr, n, duty) * env * (gain * vel)
    return f


def i_tri(a=0.004, d=0.1, s=0.85, r=0.06, gain=0.5, steps=7.5, vib=0.0):
    def f(m, dur, vel=1.0, bend=0.0):
        env = _env(n_samples(dur), a, d, s, r)
        n = len(env)
        fr = _hz(m)
        if vib:
            t = np.arange(n) / SR
            fr = fr * (1.0 + vib * np.clip((t - 0.25) / 0.4, 0, 1) * np.sin(TAU * 5.0 * t))
        return _tri(fr, n, steps) * env * (gain * vel)
    return f


def i_soft(a=0.12, d=0.4, s=0.85, r=0.5, gain=0.3, vib=0.004):
    """Sine + triangle 'strings / ocarina' voice for counter-lines."""
    def f(m, dur, vel=1.0, bend=0.0):
        env = _env(n_samples(dur), a, d, s, r)
        n = len(env)
        t = np.arange(n) / SR
        fr = _hz(m) * (1.0 + vib * np.clip((t - 0.3) / 0.5, 0, 1) * np.sin(TAU * 4.8 * t))
        return (0.7 * _sin(fr, n) + 0.45 * _tri(fr, n)) * env * (gain * vel)
    return f


def i_bell(parts=((1.0, 1.0, 2.0), (2.0, 0.15, 5.0), (5.93, 0.1, 16.0)),
           ring=1.8, gain=0.3, detune=0.0, click=0.0):
    def f(m, dur, vel=1.0, bend=0.0):
        n, t = _t(max(dur + 0.1, ring))
        hz = _hz(m)
        x = np.zeros(n)
        for ratio, amp, dec in parts:
            if hz * ratio < 15000:
                x += amp * np.sin(TAU * hz * ratio * t) * np.exp(-dec * t)
        if detune:
            x += 0.22 * np.sin(TAU * hz * (1 + detune) * t) * np.exp(-parts[0][2] * t)
        x *= np.minimum(1.0, t / 0.0015)
        if click:
            k = int(0.004 * SR)
            x[:k] += _filt(_noise(k, "bellclick", m), 3000, "high") * np.linspace(1, 0, k) * click
        return _fade_end(x, 40) * (gain * vel)
    return f


def i_koto(gain=0.3):
    parts = ((1.0, 1.0, 2.4), (2.004, 0.55, 3.8), (3.009, 0.32, 5.6),
             (4.016, 0.2, 7.5), (5.025, 0.1, 10.0), (6.03, 0.05, 13.0))

    def f(m, dur, vel=1.0, bend=0.0):
        n, t = _t(max(1.5, dur))
        hz = _hz(m)
        fr = hz * (1.0 + 0.004 * np.exp(-t / 0.03))
        if bend:  # oshide: press string, pitch rises from below after the pluck
            fr = fr * 2.0 ** (-bend / 12.0 * (1.0 - np.clip((t - 0.12) / 0.15, 0, 1)))
        ph = np.cumsum(fr) / SR
        x = np.zeros(n)
        for ratio, amp, dec in parts:
            if hz * ratio < 15000:
                x += amp * np.sin(TAU * ratio * ph) * np.exp(-dec * t)
        k = int(0.006 * SR)
        x[:k] += _filt(_noise(k, "koto", m), 2500, "high") * np.linspace(1, 0, k) * 0.5
        x *= np.minimum(1.0, t / 0.0008)
        return _fade_end(x, 40) * (gain * vel)
    return f


def i_shamisen(gain=0.3):
    def f(m, dur, vel=1.0, bend=0.0):
        n, t = _t(min(max(dur * 1.3, 0.4), 1.2))
        hz = _hz(m)
        fr = hz * (1.0 + 0.022 * np.exp(-t / 0.012))           # bachi strike: sharp, settles
        if bend:                                                  # suri-age slide into the note
            fr = fr * 2.0 ** (-bend / 12.0 * (1.0 - np.clip(t / 0.09, 0, 1)))
        x = _pulse(fr, n, 0.21)
        bright = _filt(x, 4200) * np.exp(-t * 15.0)
        body = _filt(x, 1100) * np.exp(-t * 4.5)
        nz = _noise(n, "sham", m)
        buzz = _filt(nz, 2500) * (x > 0) * np.exp(-t * 22.0) * 0.25     # sawari rasp
        k = int(0.005 * SR)
        click = np.zeros(n)
        click[:k] = _filt(nz[:k], 2000, "high") * np.linspace(1, 0, k) * 0.8
        y = 0.55 * bright + 0.75 * body + buzz + click
        y *= np.minimum(1.0, t / 0.0007)
        return _fade_end(y, 25) * (gain * vel)
    return f


def i_flute(gain=0.3, vib=0.009):
    """Breathy shakuhachi-like voice (scoops into notes, delayed vibrato)."""
    def f(m, dur, vel=1.0, bend=0.0):
        env = _env(n_samples(dur), 0.07, 0.3, 0.82, 0.18)
        n = len(env)
        t = np.arange(n) / SR
        b = bend if bend else 0.4
        fr = _hz(m) * 2.0 ** (-b / 12.0 * np.exp(-t / 0.07))
        ramp = np.clip((t - 0.35) / 0.4, 0.0, 1.0)
        fr = fr * (1.0 + vib * ramp * np.sin(TAU * 5.0 * t))
        ph = np.cumsum(fr) / SR
        tone = np.sin(TAU * ph) + 0.22 * np.sin(2 * TAU * ph) + 0.07 * np.sin(3 * TAU * ph)
        br = _filt(_filt(_noise(n, "flute", m), 3200), 500, "high")
        breath = br * (0.25 + 0.9 * np.exp(-t / 0.1)) * 0.22
        return (tone + breath) * env * (gain * vel)
    return f


def i_pad(gain=0.12, a=0.35, r=0.9, duty=0.5, det=0.004):
    def f(m, dur, vel=1.0, bend=0.0):
        env = _env(n_samples(dur), a, 0.6, 0.85, r)
        n = len(env)
        hz = _hz(m)
        y = 0.45 * _pulse(hz * (1 + det), n, duty, False) \
            + 0.45 * _pulse(hz * (1 - det), n, duty, False) + 0.6 * _sin(hz, n)
        return y * env * (gain * vel)
    return f


def i_drone(gain=0.3, a=1.2, r=2.0):
    def f(m, dur, vel=1.0, bend=0.0):
        env = _env(n_samples(dur), a, 1.0, 1.0, r)
        n = len(env)
        t = np.arange(n) / SR
        hz = _hz(m)
        y = _tri(hz * 1.0015, n) + _tri(hz * 0.9985, n) + 0.35 * _pulse(hz * 2.0, n, 0.5, False)
        lfo = 0.78 + 0.22 * np.sin(TAU * 0.21 * t - 1.3)
        return y * env * lfo * (gain * vel)
    return f


# ===================================================================== drums
def _metal(n):
    ph = np.arange(n) / SR
    y = np.zeros(n)
    for fq in (205.3, 304.4, 369.6, 522.7, 540.0, 800.0):
        y += np.sign(np.sin(TAU * fq * 1.7 * ph))
    return y / 6.0


def d_kick(f0=160.0, f1=46.0, dur=0.34, k=7.5, click=0.4, key=0):
    n, t = _t(dur)
    fr = f1 + (f0 - f1) * np.exp(-t / 0.03)
    body = np.sin(TAU * np.cumsum(fr) / SR) * np.exp(-k * t)
    cl = _filt(_noise(n, "kick", key), 3500) * np.exp(-t * 260) * click
    return _fade_end(np.tanh(1.3 * (body + cl)), 10)


def d_snare(tone=185.0, dur=0.26, k=13.0, nz=0.8, key=0):
    n, t = _t(dur)
    w = _filt(_filt(_noise(n, "snare", key), 1500, "high"), 9000)
    fr = tone * (1.0 + 0.35 * np.exp(-t / 0.01))
    body = np.sin(TAU * np.cumsum(fr) / SR) * np.exp(-t * 22)
    y = w * np.exp(-k * t) * nz * 1.4 + 0.6 * body
    return _fade_end(y * np.minimum(1, t / 0.0008), 10)


def d_hat(dur=0.06, k=65.0, key=0):
    n, t = _t(dur)
    y = 0.5 * _metal(n) + 0.6 * _noise(n, "hat", key)
    y = _filt(y, 7000, "high") * np.exp(-k * t)
    return _fade_end(y, 5) * 0.8


def d_ohat(dur=0.4, key=0):
    return d_hat(dur, 9.0, key + 17)


def d_crash(dur=2.2, key=0):
    n, t = _t(dur)
    y = 0.35 * _metal(n) + 0.8 * _noise(n, "crash", key)
    y = _filt(y, 3800, "high") * (0.7 * np.exp(-t * 2.4) + 0.3 * np.exp(-t * 10))
    return _fade_end(y * np.minimum(1, t / 0.0015), 60) * 0.8


def d_tom(f=110.0, dur=0.42, k=7.5, key=0):
    n, t = _t(dur)
    fr = f * (1.0 + 0.45 * np.exp(-t / 0.04))
    body = np.sin(TAU * np.cumsum(fr) / SR) * np.exp(-k * t)
    thud = _filt(_noise(n, "tom", key), 900) * np.exp(-t * 40) * 0.5
    return _fade_end(np.tanh(1.2 * (body + thud)), 10)


def d_taiko(f=62.0, dur=1.1, key=0):
    n, t = _t(dur)
    fr = f * (1.0 + 0.5 * np.exp(-t / 0.02))
    ph = np.cumsum(fr) / SR
    body = (np.sin(TAU * ph) * np.exp(-4.8 * t) + 0.35 * np.sin(TAU * 1.593 * ph) * np.exp(-9 * t)
            + 0.18 * np.sin(TAU * 2.135 * ph) * np.exp(-14 * t))
    skin = _filt(_filt(_noise(n, "taiko", key), 1800), 300, "high") * np.exp(-45 * t) * 0.5
    y = (body + skin) * np.minimum(1, t / 0.002)
    return _fade_end(np.tanh(1.2 * y), 30)


def d_ka(key=0):
    n, t = _t(0.09)
    bp = _filt(_filt(_noise(n, "ka", key), 4500), 1500, "high")
    y = bp * np.exp(-t * 110) * 0.7 + np.sin(TAU * 1350 * t) * np.exp(-t * 85) * 0.5 \
        + np.sin(TAU * 2210 * t) * np.exp(-t * 120) * 0.25
    return _fade_end(y, 5)


def d_clack(key=0):
    """Hyoshigi (kabuki wooden clappers)."""
    n, t = _t(0.3)
    y = np.zeros(n)
    for fq, a, k in ((2150, 1.0, 32), (3390, 0.6, 40), (5230, 0.3, 55), (1180, 0.25, 38)):
        y += a * np.sin(TAU * fq * t) * np.exp(-k * t)
    y += _filt(_noise(n, "clack", key), 3000, "high") * np.exp(-t * 700) * 0.8
    return _fade_end(y * 0.6, 10)


def d_tick(f=2600.0, key=0):
    n, t = _t(0.04)
    y = np.sin(TAU * f * t) * np.exp(-t * 200) + \
        _filt(_noise(n, "tick", key), 4000, "high") * np.exp(-t * 900) * 0.4
    return _fade_end(y, 5)


def d_heart(gap=0.19):
    n, t = _t(0.75)

    def thump(t0, f0, f1, k, amp):
        on = t >= t0
        tt = np.clip(t - t0, 0.0, None)
        fr = (f1 + (f0 - f1) * np.exp(-tt / 0.025)) * on
        ph = np.cumsum(fr) / SR
        return np.sin(TAU * ph) * np.exp(-k * tt) * on * amp * np.minimum(1.0, tt / 0.004)
    y = thump(0.0, 95, 48, 15, 1.0) + thump(gap, 105, 56, 19, 0.7)
    return _fade_end(np.tanh(1.8 * y) / np.tanh(1.8), 20)


def d_boom(key=0):
    n, t = _t(2.6)
    fr = 34.0 + 60.0 * np.exp(-t / 0.06)
    body = np.sin(TAU * np.cumsum(fr) / SR) * np.exp(-2.2 * t)
    nz = _noise(n, "boom", key)
    rum = _filt(nz, 180) * np.exp(-3.0 * t) * 2.0
    hit = _filt(nz, 1500) * np.exp(-t * 30) * 0.5
    return _fade_end(np.tanh(1.5 * (body + rum + hit)) * 0.9, 80)


def d_riser(dur, key=0):
    n, t = _t(dur)
    p = t / dur
    y = _filt(_noise(n, "riser", key), 900, "high") * p ** 2.2 * 0.5
    fr = 220.0 * 8.0 ** p
    y += np.sin(TAU * np.cumsum(fr) / SR) * p ** 2 * 0.15
    return _fade_end(y, 20)


def d_revcrash(dur, key=0):
    c = d_crash(dur + 0.3, key)[: n_samples(dur)][::-1].copy()
    return _fade_end(c, 8)


def d_shaker(key=0):
    n, t = _t(0.08)
    env = np.where(t < 0.012, t / 0.012, np.exp(-(t - 0.012) * 60))
    return _filt(_noise(n, "shaker", key), 5000, "high") * env * 0.6


_VEL = {"X": 1.0, "x": 0.68, "o": 0.42}


# ============================================================== note parsing
def _parse(text):
    """'C5:1 E5:.5@.8 R:1 [C4,E4]:2 - :1 D5~1:2' -> [(midis|None, beats, vel, bend)].
    @v = velocity, ~b = scoop/bend into the note from b semitones below, '-' = tie."""
    out = []
    for tok in text.split():
        name, _, rest = tok.partition(":")
        vel = 1.0
        if "@" in rest:
            rest, v = rest.split("@")
            vel = float(v)
        beats = float(Fraction(rest)) if rest else 1.0
        bend = 0.0
        if "~" in name:
            name, bs = name.split("~")
            bend = float(bs) if bs else 1.0
        if name in ("R", "r", "_"):
            out.append((None, beats, vel, 0.0))
        elif name == "-":
            ms, b, v, bd = out[-1]
            out[-1] = (ms, b + beats, v, bd)
        elif name.startswith("["):
            out.append(([midi(x) for x in name.strip("[]").split(",")], beats, vel, bend))
        else:
            out.append(([midi(name)], beats, vel, bend))
    return out


def _beats(text):
    return sum(b for _, b, _, _ in _parse(text))


_PCN = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_Q = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "maj7": (0, 4, 7, 11),
      "m7": (0, 3, 7, 10), "sus4": (0, 5, 7), "sus2": (0, 2, 7), "7sus4": (0, 5, 7, 10),
      "dim": (0, 3, 6), "m7b5": (0, 3, 6, 10), "7b9": (0, 4, 7, 10, 13), "add9": (0, 4, 7, 14),
      "5": (0, 7), "6": (0, 4, 7, 9), "m6": (0, 3, 7, 9), "aug": (0, 4, 8)}


def _pc(s):
    v = _PCN[s[0]]
    for ch in s[1:]:
        v += 1 if ch == "#" else -1 if ch == "b" else 0
    return v % 12


def _chord(sym):
    """'F#m7/C#' -> (pitch classes, bass pc, root pc)."""
    body, _, bass = sym.partition("/")
    k = 2 if len(body) > 1 and body[1] in "#b" else 1
    root = _pc(body[:k])
    pcs = [(root + i) % 12 for i in _Q[body[k:]]]
    return pcs, (_pc(bass) if bass else root), root


def _near(pc, center):
    m = center + ((pc - center) % 12)
    return m - 12 if m - center >= 6 else m


def _voice(sym, center, n=None):
    pcs = _chord(sym)[0]
    if n:
        pcs = pcs[:n]
    return sorted(set(_near(p, center) for p in pcs))


def _bass(sym, center):
    return _near(_chord(sym)[1], center)


def _prog(bars, bpb, start=0.0):
    """['Am', 'C D', ...] (one entry per bar; several symbols split the bar) ->
    [(beat, dur, sym)]."""
    out, b = [], start
    for entry in bars:
        syms = entry.split()
        d = bpb / len(syms)
        for s in syms:
            out.append((b, d, s))
            b += d
    return out


def _chord_at(prog, beat):
    cur = prog[0][2]
    for b, _, s in prog:
        if b <= beat + 1e-6:
            cur = s
        else:
            break
    return cur


def _harm_fn(prog, scale):
    """Twin-lead harmony under a melody: chord tone a 3rd below (a 4th under chord
    roots), diatonic 3rd below for passing tones."""
    sc = set(p % 12 for p in scale)

    def h(m, beat):
        pcs = _chord(_chord_at(prog, beat))[0]
        if m % 12 in pcs:                 # chord tone: 3rd below, or the chord 5th under a root
            for d in (3, 4, 5):
                if (m - d) % 12 in pcs:
                    return m - d
        for d in (3, 4):                  # passing tone: diatonic 3rd below
            if (m - d) % 12 in sc:
                return m - d
        return m - 3
    return h


# ====================================================================== song
class Song:
    def __init__(self, bpm, bars, bpb=4, tail=4.0):
        self.bpm, self.bars, self.bpb = bpm, bars, bpb
        self.spb = 60.0 / bpm
        self.beats = bars * bpb
        self.L = int(round(self.beats * self.spb * SR))
        self.N = self.L + max(int(tail * SR), int(round(bpb * self.spb * SR)))
        self.parts = {}
        self._cache = {}

    def smp(self, beat):
        return int(round(beat * self.spb * SR))

    def put(self, part, buf, beat, gain=1.0):
        dst = self.parts.get(part)
        if dst is None:
            dst = self.parts[part] = np.zeros(self.N)
        i = self.smp(beat)
        if i < 0:
            buf, i = buf[-i:], 0
        m = min(len(buf), self.N - i)
        if m > 0:
            dst[i:i + m] += buf[:m] * gain

    def note(self, part, inst, m, beat, beats, vel=1.0, bend=0.0):
        dur = beats * self.spb
        key = (inst, m, n_samples(dur), bend)          # instruments are linear in vel
        buf = self._cache.get(key)
        if buf is None:
            buf = self._cache[key] = inst(m, dur, 1.0, bend)
        self.put(part, buf, beat, vel)

    def seq(self, part, inst, text, beat, tr=0, vel=1.0, legato=0.94, harm=None):
        for ms, b, v, bend in _parse(text):
            if ms:
                for m in ms:
                    mm = m + tr
                    if harm is not None:
                        mm = harm(mm, beat)
                    self.note(part, inst, mm, beat, b * legato, v * vel, bend)
            beat += b
        return beat

    def pat(self, part, buf, pattern, beat, steps=4, gain=1.0):
        for i, ch in enumerate(pattern):
            v = _VEL.get(ch)
            if v:
                self.put(part, buf, beat + i / steps, v * gain)

    def arp(self, part, inst, prog, b0, b1, pattern, step, center, vel=1.0,
            n=None, legato=0.9, accent=None, tr=0):
        for cb, cd, sym in prog:
            s, e = max(cb, b0), min(cb + cd, b1)
            if e <= s + 1e-6:
                continue
            v = _voice(sym, center, n)
            tones = v + [x + 12 for x in v]
            k, t = 0, s
            while t < e - 1e-6:
                m = tones[pattern[k % len(pattern)] % len(tones)] + tr
                acc = accent[k % len(accent)] if accent else 1.0
                self.note(part, inst, m, t, step * legato, vel * acc)
                t += step
                k += 1

    def bassline(self, part, inst, prog, b0, b1, style="oct8", center=40, vel=1.0, tr=0):
        segs = [(i, c) for i, c in enumerate(prog) if b0 - 1e-6 <= c[0] < b1 - 1e-6]
        for i, (cb, cd, sym) in segs:
            r = _bass(sym, center) + tr
            nsym = prog[(i + 1) % len(prog)][2]
            nx = _bass(nsym, center) + tr
            appr = None if nx == r else (nx - 1 if nx > r else nx + 1)
            notes = []
            if style == "oct8":
                notes = [(r if j % 2 == 0 else r + 12, 0.5) for j in range(int(round(cd * 2)))]
                if appr is not None:
                    notes[-1] = (appr, 0.5)
            elif style == "drive8":
                notes = [(r, 0.5)] * int(round(cd * 2))
                if appr is not None:
                    notes[-1] = (appr, 0.5)
            elif style == "gallop":
                for j in range(int(round(cd))):
                    notes += [(r, 0.5), (r, 0.25), (r + 12, 0.25)]
                if appr is not None:
                    notes[-2:] = [(appr, 0.5)]
            elif style == "whole":
                notes = [(r, cd)]
            elif style == "half":
                h = cd / 2.0
                notes = [(r, h), (r + 12 if cd >= 4 else r, h)]
            elif style == "pulse":       # root on the beat + approach 8th
                notes = [(r, 1.0)] * int(round(cd))
                if appr is not None:
                    notes[-1:] = [(r, 0.5), (appr, 0.5)]
            t = cb
            leg = 0.97 if style in ("whole", "half") else 0.88
            for m, d in notes:
                self.note(part, inst, m, t, d * leg, vel)
                t += d

    def mix(self, name, spec, rev=(0.84, 0.3, 0.3), rms=0.16, peak=0.84):
        out = np.zeros((self.N, 2))
        send = np.zeros(self.N)
        stems = {}
        for pname, cfg in spec.items():
            x = self.parts.get(pname)
            if x is None:
                continue
            x = x * cfg.get("gain", 1.0)
            if cfg.get("hp"):
                x = _filt(x, cfg["hp"], "high")
            if cfg.get("lp"):
                x = _filt(x, cfg["lp"])
            st = _pan(x, cfg.get("pan", 0.0))
            if cfg.get("echo"):
                eb, fb, wet = cfg["echo"]
                st = st + _echo(x, self.smp(eb), fb, wet, cfg.get("pan", 0.0))
            out += st
            if cfg.get("rev"):
                send += x * cfg["rev"]
            if ANALYZE:
                stems[pname] = _active_rms(_aweight(st[: self.L].mean(axis=1)))
        if send.any():
            wet = _reverb(send, rev[0], rev[1]) * rev[2]
            if ANALYZE:
                stems["~reverb"] = _active_rms(_aweight(wet[: self.L].mean(axis=1)))
            out += wet
        y = out[: self.L].copy()
        k = self.L
        while k < self.N:                      # fold the tail onto the start
            seg = out[k:k + self.L]
            y[: len(seg)] += seg
            k += self.L
        STEMS[name] = stems
        return _master(y, rms, peak)


# =================================================================== TENSION
@track("tension")
def tension():
    """D minor/phrygian, 80 bpm, 16 bars (48 s).
    1-4 boom, drone pedal, slow heartbeat, ticking clock, glass bells hinting the
    A-Bb-A motif, minor-2nd stabs creep in | 5-12 lead motif (call) answered by
    glass bells (response), Dm-Bb-Gm-Eb-Dm-Bb-Eb-A7b9 | 13-16 climax: motif an octave
    up, heartbeat every beat, toms, riser + reverse cymbal into the bar-1 boom."""
    S = Song(80, 16, tail=5.0)
    bars = ["Dm", "Dm", "Bb/D", "A/D", "Dm", "Bb", "Gm", "Eb",
            "Dm", "Bb", "Eb", "A7b9", "Dm", "Bb", "Eb", "A7b9"]

    drone = i_drone(0.3)
    S.note("drone", drone, midi("D2"), 0, 16)
    S.note("drone", drone, midi("A2"), 0, 16, vel=0.45)
    dr2 = i_drone(0.3, a=0.5, r=1.2)
    for b in range(4, 16):
        r = _bass(bars[b], 40)
        S.note("drone", dr2, r, b * 4, 4, vel=0.85)
        S.note("drone", dr2, r + 7, b * 4, 4, vel=0.35)

    # heartbeat-like bass pulses (lub-dub): half-time, then every beat
    hb = i_tri(a=0.003, d=0.16, s=0.0, r=0.05, gain=0.6)
    heart = d_heart(gap=0.25 * S.spb)
    for b in range(16):
        r = _bass(bars[b], 45)
        beats = [0, 2] if b < 8 else [0, 1, 2, 3]
        v = (0.75, 0.8, 0.9, 1.0)[b // 4]
        for bt in beats:
            S.note("hbass", hb, r, b * 4 + bt, 0.22, v)
            S.note("hbass", hb, r, b * 4 + bt + 0.25, 0.18, v * 0.6)
            S.put("heart", heart, b * 4 + bt, v)

    # glassy bells: motif hints, then answers to the lead
    glass = i_bell(parts=((1.0, 1.0, 1.1), (2.76, 0.28, 3.5), (5.4, 0.12, 7.0), (8.93, 0.05, 12.0)),
                   ring=3.0, gain=0.22, detune=0.0015)
    G = [(0, 1.0, "A5"), (0, 2.0, "Bb5"), (0, 3.0, "A5"), (1, 2.5, "D6"),
         (2, 1.0, "D6"), (2, 2.0, "Eb6"), (2, 3.0, "D6"), (3, 0.5, "C#6"), (3, 2.0, "E6"),
         (3, 3.0, "Bb5"),
         (5, 0.5, "F6"), (5, 1.25, "D6"), (5, 2.0, "Bb5"), (5, 3.0, "A5"),
         (7, 0.5, "G6"), (7, 1.25, "Eb6"), (7, 2.0, "Bb5"), (7, 3.0, "D6"),
         (9, 0.5, "F6"), (9, 1.25, "D6"), (9, 2.0, "Bb5"), (9, 3.0, "A5"),
         (11, 0.5, "G6"), (11, 1.25, "E6"), (11, 2.0, "C#6"), (11, 2.75, "Bb5"), (11, 3.5, "A5"),
         (13, 0.5, "F6"), (13, 2.0, "D6"), (15, 0.5, "G6"), (15, 2.0, "E6"), (15, 3.0, "C#6")]
    for b, bt, nm in G:
        S.note("glass", glass, midi(nm), b * 4 + bt, 1.0, 0.95 if b < 4 else 0.7)

    # dissonant minor-2nd stabs (root + b9), getting denser
    stab = i_pulse(duty=0.125, a=0.002, d=0.2, s=0.0, r=0.05, gain=0.3)
    ST = [(2, 3.5), (3, 1.5), (3, 3.5), (5, 3.5), (6, 1.5), (7, 3.5), (8, 1.5), (8, 3.5),
          (9, 3.5), (10, 1.5), (10, 3.5), (11, 1.5), (11, 3.5), (12, 1.5), (12, 3.5),
          (13, 1.5), (13, 2.5), (13, 3.5), (14, 1.5), (14, 3.5), (15, 0.5), (15, 1.5),
          (15, 2.5), (15, 3.0), (15, 3.5)]
    for b, bt in ST:
        r = _near(_chord(bars[b])[2], 70)
        v = 0.7 if b < 4 else 0.85 if b < 12 else 1.0
        S.note("stab", stab, r, b * 4 + bt, 0.3, v)
        S.note("stab", stab, r + 1, b * 4 + bt, 0.3, v)

    # ticking clock (tick-tock panned), quarters -> 8ths -> 8ths + 16th pickups
    th, tl = d_tick(3300, 1), d_tick(2400, 2)
    for b in range(16):
        step = 1.0 if b < 4 else 0.5
        v = 0.55 if b < 4 else 0.6 if b < 12 else 0.65
        for k in range(int(4 / step)):
            t = b * 4 + k * step
            S.put("tickL" if k % 2 == 0 else "tickR", th if k % 2 == 0 else tl, t, v)
            if b >= 12 and k % 4 == 3:
                S.put("tickR", tl, t + 0.25, v * 0.6)

    # dark pad
    pad = i_pad(gain=0.12, a=0.8, r=1.5, duty=0.5)
    for b in range(16):
        for m in _voice(bars[b], 58):
            S.note("pad", pad, m, b * 4, 4, 0.65 if b < 4 else 0.75 if b < 12 else 0.9)

    # lead: motif (bars 5-12) and climax (13-16)
    lead = i_pulse(duty=0.25, a=0.04, d=0.3, s=0.7, r=0.25, vib=0.008, vdelay=0.35, gain=0.3)
    MEL = ("R:1 A4:1 Bb4:1 A4:1 F4:3 R:1 "
           "R:1 G4:1 A4:1 Bb4:1 G4:3 R:1 "
           "R:1 D5:1 Eb5:1 D5:1 Bb4:2 A4:1 F4:1 "
           "G4:1 Bb4:1 Eb5:2 C#5:2 Bb4:1 A4:1")
    CLIMAX = "A5:1 Bb5:1 A5:1 F5:1 D5:2 F5:1 D5:1 Eb5:1 G5:1 Bb5:1 Eb6:1 C#6:1.5 Bb5:.5 A5:1 G5:1"
    assert _beats(MEL) == 32 and _beats(CLIMAX) == 16
    S.seq("lead", lead, MEL, 16)
    S.seq("lead", lead, CLIMAX, 48)
    S.seq("lead2", i_tri(a=0.05, d=0.3, s=0.8, r=0.3, gain=0.45, steps=0), CLIMAX, 48, tr=-12)

    # percussion build + loop transition
    S.put("perc", d_boom(), 0, 1.0)
    for b in range(12, 16):
        S.pat("perc", d_tom(70, 0.6, 5.0), "X.......x.......", b * 4, gain=0.55)
    S.pat("perc", d_tom(95, 0.4), "........X.x.xxXX", 60, gain=0.45)
    S.put("fx", d_riser(4 * S.spb), 60, 0.6)
    S.put("fx", d_revcrash(1.6), 64 - 1.6 / S.spb, 0.5)

    spec = {
        "drone": dict(gain=0.5, lp=700),
        "hbass": dict(gain=1.1, lp=1400),
        "heart": dict(gain=0.7, lp=900),
        "glass": dict(gain=0.8, pan=0.3, echo=(0.75, 0.45, 0.4), rev=0.6),
        "stab": dict(gain=0.85, pan=-0.35, lp=5000, echo=(0.75, 0.4, 0.35), rev=0.4),
        "tickL": dict(gain=0.2, pan=-0.5),
        "tickR": dict(gain=0.2, pan=0.5),
        "pad": dict(gain=0.6, lp=1300, rev=0.3),
        "lead": dict(gain=0.85, pan=-0.15, lp=3200, echo=(0.75, 0.35, 0.25), rev=0.35),
        "lead2": dict(gain=0.35, lp=1500),
        "perc": dict(gain=0.8, rev=0.2),
        "fx": dict(gain=0.5, hp=300, rev=0.2),
    }
    return S.mix("tension", spec, rev=(0.88, 0.35, 0.18))


# ==================================================================== BATTLE
@track("battle")
def battle():
    """E minor -> F# minor lift, 165 bpm, 32 bars (46.5 s).
    1-4 riff intro | 5-12 A theme | 13-16 call&response B, C#7 pivot |
    17-24 A' up a whole step with twin-lead harmony | 25-28 B' |
    29-32 turnaround riff C-D-Bsus4-B7 + tom fill back to Em."""
    S = Song(165, 32, tail=3.0)
    bars = ["Em", "C", "D", "B",
            "Em", "C", "D", "B", "Em", "C", "Am D", "B7",
            "Am", "Em", "C D", "C#7",
            "F#m", "D", "E", "C#", "F#m", "D", "Bm E", "C#7",
            "Bm", "F#m", "D", "E",
            "C", "D", "Bsus4", "B7"]
    prog = _prog(bars, 4)

    lead = i_pulse(duty=0.25, a=0.004, d=0.12, s=0.75, r=0.06, vib=0.012, vdelay=0.16, gain=0.3)
    harm = i_pulse(duty=0.5, a=0.004, d=0.12, s=0.7, r=0.06, vib=0.01, vdelay=0.18, gain=0.24)
    cnt = i_pulse(duty=0.5, a=0.004, d=0.1, s=0.65, r=0.05, gain=0.26)
    arp = i_pulse(duty=0.125, a=0.002, d=0.09, s=0.25, r=0.03, gain=0.22)
    stab = i_pulse(duty=0.25, a=0.002, d=0.15, s=0.45, r=0.04, gain=0.2)
    bass = i_tri(a=0.003, d=0.08, s=0.9, r=0.03, gain=0.6)

    A_MEL = ("B4:.5 E5:1 F#5:.5 G5:1 F#5:.5 E5:.5 "
             "G5:1.5 E5:.5 C5:1 E5:1 "
             "F#5:1 A5:1 D5:1 F#5:.5 G5:.5 "
             "F#5:2 D#5:1 B4:1 "
             "B4:.5 E5:1 F#5:.5 G5:1 A5:.5 B5:.5 "
             "C6:1.5 B5:.5 G5:1 E5:1 "
             "A5:1 E5:.5 C5:.5 D5:1 F#5:1 "
             "B5:1.5 A5:.5 G5:.5 F#5:.5 D#5:1")
    B_LEAD = ("E5:.5 E5:.5 A5:1 R:2 "
              "G5:.5 G5:.5 B5:1 R:2 "
              "C6:.5 B5:.5 G5:.5 E5:.5 D6:.5 C6:.5 A5:.5 F#5:.5 "
              "G#5:1 F5:.5 G#5:.5 C#6:2")
    B_CNT = ("R:2 C5:.5 B4:.5 A4:1 "
             "R:2 E5:.5 D5:.5 B4:1 "
             "G4:2 A4:2 "
             "F4:1 G#4:1 B4:2")
    B2_LEAD = ("F#5:.5 F#5:.5 B5:1 R:2 "
               "A5:.5 A5:.5 C#6:1 R:2 "
               "D6:.5 C#6:.5 A5:.5 F#5:.5 A5:.5 B5:.5 C#6:.5 D6:.5 "
               "B5:1.5 G#5:.5 E5:1 B4:1")
    B2_CNT = ("R:2 D5:.5 C#5:.5 B4:1 "
              "R:2 F#5:.5 E5:.5 C#5:1 "
              "A4:2 F#4:2 "
              "G#4:2 B4:2")
    T_LEAD = ("E5:.5 G5:.5 C6:1 B5:.5 G5:.5 E5:1 "
              "F#5:.5 A5:.5 D6:1 C6:.5 A5:.5 F#5:1 "
              "E5:1.5 F#5:.5 B5:2 "
              "A5:.5 G5:.5 F#5:.5 E5:.5 D#5:2")
    assert _beats(A_MEL) == 32 and _beats(B_LEAD) == 16 and _beats(B_CNT) == 16
    assert _beats(B2_LEAD) == 16 and _beats(B2_CNT) == 16 and _beats(T_LEAD) == 16

    S.seq("lead", lead, "R:2 F#5:.5 G5:.5 A5:1 B5:1.5 A5:.5 F#5:1 D#5:1", 8)
    S.seq("lead", lead, A_MEL, 16)
    S.seq("lead", lead, B_LEAD, 48)
    S.seq("cnt", cnt, B_CNT, 48)
    S.seq("lead", lead, A_MEL, 64, tr=2)
    fsm = [_pc(x) for x in ("F#", "G#", "A", "B", "C#", "D", "E")]
    S.seq("harm", harm, A_MEL, 64, tr=2, harm=_harm_fn(prog, fsm))
    S.seq("lead", lead, B2_LEAD, 96)
    S.seq("cnt", cnt, B2_CNT, 96)
    S.seq("lead", lead, T_LEAD, 112)

    # riff stabs (intro + turnaround), 3-3-4-2-4 syncopation
    hits = [(0, 0.5), (0.75, 0.5), (1.5, 0.75), (2.5, 0.5), (3.0, 0.75)]
    for b in list(range(0, 4)) + list(range(28, 32)):
        sym = bars[b]
        for bt, d in hits:
            for m in _voice(sym, 62, 3):
                S.note("stab", stab, m, b * 4 + bt, d, 1.0 if bt == 0 else 0.8)
            S.note("bass", bass, _bass(sym, 40), b * 4 + bt, d * 0.9, 1.0)
        # riff fill-in 8ths between stabs on the bass
        S.note("bass", bass, _bass(sym, 40) + 12, b * 4 + 3.75, 0.2, 0.7)

    # 16th arpeggios
    P = [0, 1, 2, 3, 2, 1]
    S.arp("arp", arp, prog, 0, 16, P, 0.5, 64, vel=0.8)
    S.arp("arp", arp, prog, 16, 64, P, 0.25, 64, vel=0.9, accent=[1, .6, .75, .6])
    S.arp("arp", arp, prog, 64, 112, P, 0.25, 64, vel=1.0, accent=[1, .6, .75, .6])
    S.arp("arp", arp, prog, 112, 128, P, 0.5, 64, vel=0.8)

    # bass
    S.bassline("bass", bass, prog, 16, 48, "oct8", 40)
    S.bassline("bass", bass, prog, 48, 64, "gallop", 40)
    S.bassline("bass", bass, prog, 64, 96, "oct8", 40)
    S.bassline("bass", bass, prog, 96, 112, "gallop", 40)

    # drums
    K, SN, H, OH = d_kick(), d_snare(), d_hat(), d_ohat()
    CR = d_crash()
    TH, TM, TL = d_tom(190), d_tom(140), d_tom(100)
    for b in range(32):
        bt = b * 4
        fill = b in (3, 11, 15, 23, 27, 31)
        if b < 4 or b >= 28:
            S.pat("kick", K, "X..X..X...X.X...", bt)
            S.pat("snare", SN, "....X.......X...", bt)
            S.pat("hat", H, "x.x.x.x.x.x.x.x.", bt)
        elif 12 <= b < 16 or 24 <= b < 28:
            S.pat("kick", K, "X.x.X.x.X.x.X.x.", bt)
            S.pat("snare", SN, "....X.......X..x", bt)
            S.pat("hat", H, "xoxoXoxoxoxoXoxo", bt)
        else:
            S.pat("kick", K, "X.....x.X.x.....", bt)
            S.pat("snare", SN, "....X.......X...", bt)
            S.pat("hat", H, "x.X.x.X.x.X.x.X.", bt)
            if b >= 16:
                S.pat("hat", OH, "..x...x...x...x.", bt, gain=0.6)
        if fill:
            if b in (15, 31):
                S.pat("tom", TH, "........XX......", bt)
                S.pat("tom", TM, "..........XX....", bt)
                S.pat("tom", TL, "............XX..", bt)
                S.pat("snare", SN, "..............XX", bt)
            else:
                S.pat("snare", SN, "............XxXX", bt, gain=0.9)
                S.pat("tom", TM, "..............x.", bt)
    for b in (0, 4, 8, 12, 16, 20, 24, 28):
        S.put("crash", CR, b * 4, 1.0)

    spec = {
        "lead": dict(gain=1.0, pan=-0.15, lp=7000, echo=(0.75, 0.3, 0.16), rev=0.18),
        "harm": dict(gain=0.8, pan=0.25, lp=6000, rev=0.15),
        "cnt": dict(gain=0.8, pan=0.3, lp=6000, echo=(0.5, 0.3, 0.12), rev=0.15),
        "arp": dict(gain=0.8, pan=0.4, lp=6500, rev=0.1),
        "stab": dict(gain=0.6, pan=-0.2, lp=6000, rev=0.1),
        "bass": dict(gain=1.0, lp=3000),
        "kick": dict(gain=0.75),
        "snare": dict(gain=0.62, rev=0.18),
        "hat": dict(gain=0.8, pan=0.25),
        "tom": dict(gain=0.7, rev=0.15),
        "crash": dict(gain=0.4, pan=-0.2),
    }
    return S.mix("battle", spec, rev=(0.8, 0.35, 0.3))


# ================================================================= YOSHIWARA
@track("yoshiwara")
def yoshiwara():
    """D 'in' / miyako-bushi scale (D Eb G A Bb), 80 bpm, 16 bars (48 s).
    1-4 hyoshigi clack, shamisen theme over a plucked ostinato, slow taiko |
    5-8 theme variant + breathy flute counter-line, 'ka' rim, koto accents |
    9-12 flute melody over the ostinato, koto rolls | 13-16 koto solo (oshide
    bends) over the ostinato, taiko roll, A -> D cadence back to bar 1."""
    S = Song(80, 16, tail=4.0)
    roots = ["D", "D", "G", "A", "D", "D", "G", "Eb", "Bb", "A", "G", "Eb", "D", "D", "Bb", "A"]
    sham = i_shamisen(0.34)
    sham2 = i_shamisen(0.26)
    koto = i_koto(0.26)
    flute = i_flute(0.3)

    O_D1 = "D3:.5 A3:.5 D4:.5 A3:.5 D3:.5 A3:.5 Eb4:.5 D4:.5"
    O_D2 = "D3:.5 A3:.5 D4:.5 A3:.5 G3:.5 A3:.5 Bb3:.5 A3:.5"
    O_BB = "D3:.5 Bb3:.5 D4:.5 Bb3:.5 D3:.5 Bb3:.5 Eb4:.5 D4:.5"
    O_A = "A2:.5 A3:.5 D4:.5 Eb4~1:.5 D4:.5 A3:.5 G3:.5 Eb3:.5"
    O_BB2 = "Bb2:.5 D3:.5 G3:.5 D3:.5 Bb2:.5 D3:.5 A3:.5 G3:.5"
    O_A2 = "A2:.5 D3:.5 Eb3:.5 D3:.5 A2:.5 D3:.5 G3:.5 D3:.5"
    O_G = "G2:.5 D3:.5 G3:.5 D3:.5 G2:.5 D3:.5 A3:.5 G3:.5"
    O_EB = "Eb3:.5 Bb3:.5 Eb4:.5 Bb3:.5 Eb3:.5 Bb3:.5 D4:.5 Bb3:.5"
    O_SP = "D3:1 A3:.5@.6 A3:.5@.5 D3:1 A3:.5@.6 D4:.5@.5"
    OST = [O_D1, O_D2, O_G, O_A, O_SP, O_SP, O_G, O_EB,
           O_BB2, O_A2, O_G, O_EB, O_D1, O_D2, O_BB, O_A]
    MEL1 = ("D5~1:1 Bb4:.5 A4:.5 G4:1 A4:1 "
            "Bb4:.5 A4:.5 G4:.5 Eb4:.5 D4~1:2 "
            "G4:.5 A4:.5 Bb4:1 D5:.5 Eb5:.5 D5:1 "
            "Bb4:.5 A4:.5 G4:1 A4~2:2")
    MEL2 = ("D5~1:1 Bb4:.5 A4:.5 G4:1 A4:1 "
            "Bb4:.5 A4:.5 G4:.5 Eb4:.5 D4~1:2 "
            "G4:.5 A4:.5 Bb4:.5 D5:.5 Eb5~1:1 D5:.5 Bb4:.5 "
            "A4:1 G4:.5 A4:.5 Bb4:.5 A4:.5 Eb4:1")
    FLUTE2 = "A5~1:4 G5:2 D5:2 Bb5~1:2 A5:2 G5:2 Eb5:1.5 D5:.5"
    FLUTE = ("A5~1:2 G5:.5 A5:.5 Bb5:1 "
             "A5:2.5 G5:.5 Eb5:.5 D5:.5 "
             "G5~1:1.5 A5:.5 Bb5:1 D6:1 "
             "Eb6~1:2 D6:.5 Bb5:.5 A5:.5 G5:.5")
    KOTO = ("D5:.5 D5:.5 Eb5~1:.5 D5:.5 A4:1 Bb4:.5 A4:.5 "
            "G4:.5 A4:.5 Bb4:.5 A4:.5 D4:2 "
            "G4:.5 A4:.5 Bb4:1 D5:.5 Eb5:.5 G5~2:1 "
            "A5:1 G5:.5 Eb5:.5 D5:.5 Bb4:.5 A4:1")
    for s in (MEL1, MEL2, FLUTE, FLUTE2, KOTO):
        assert _beats(s) == 16, s

    for b, o in enumerate(OST):
        S.seq("sham2", sham2, o, b * 4, vel=0.75 if o == O_SP else 0.88)
    S.seq("sham", sham, MEL1, 0)
    S.seq("sham", sham, MEL2, 16)
    S.seq("flute", flute, FLUTE2, 16, vel=0.6, legato=0.98)
    S.seq("flute", flute, FLUTE, 32, legato=0.98)
    S.seq("koto", koto, KOTO, 48, vel=1.1)

    # koto sweeps, rolls and accents
    up = "D4:.25 Eb4:.25 G4:.25 A4:.25 Bb4:.25 D5:.25 Eb5:.25 G5:.25"
    down = "G5:.25 Eb5:.25 D5:.25 Bb4:.25 A4:.25 G4:.25 Eb4:.25 D4:.25"
    S.seq("koto", koto, up, 14, vel=0.8)
    S.seq("koto", koto, down, 30, vel=0.75)
    S.seq("koto", koto, up, 46, vel=0.85)
    rolls = {8: ("Bb3", "D4", "A4"), 9: ("A3", "D4", "Eb4"), 10: ("G3", "D4", "A4"),
             11: ("Eb4", "G4", "Bb4")}
    for b, ns in rolls.items():
        for off, vel in ((0.0, 0.8), (2.5, 0.6)):
            for j, nm in enumerate(ns):
                S.note("koto", koto, midi(nm), b * 4 + off + j * 0.08, 1.0, vel)
    for b, bt, nm in ((1, 3.0, "D5"), (5, 3.0, "A4~1"), (6, 2.5, "Bb4")):
        S.seq("koto", koto, nm + ":1", b * 4 + bt, vel=0.55)

    # bass + drone
    tb = i_tri(a=0.004, d=0.35, s=0.35, r=0.2, gain=0.55)
    for b, r in enumerate(roots):
        m = _near(_pc(r), 40)
        S.note("bass", tb, m, b * 4, 1.5, 0.9)
        S.note("bass", tb, m, b * 4 + 2.5, 1.5, 0.65)
    dr = i_drone(0.25, a=1.5, r=2.5)
    for b0 in (0, 32):
        S.note("drone", dr, midi("D3"), b0, 32, 0.8)
        S.note("drone", dr, midi("A3"), b0, 32, 0.45)

    # taiko, ka, clappers, chimes
    TK, TKL, KA, CL = d_taiko(62), d_taiko(48, 1.4, 3), d_ka(), d_clack()
    for b in range(16):
        bt = b * 4
        if b < 4:
            S.pat("taiko", TK, "X.......x......." if b < 3 else "X.......x...x.x.", bt)
        elif b < 8:
            S.pat("taiko", TK, "X.....x.X......." if b < 7 else "X.....x.X...x.xx", bt)
            S.pat("ka", KA, "....x.......x...", bt)
        elif b < 12:
            S.pat("taiko", TK, "X.....x.x...X..." if b < 11 else "X.....x.X.x.X.XX", bt)
            S.pat("ka", KA, "..x...x...x...x.", bt)
        else:
            S.pat("taiko", TK, "X...x.x.X...x..." if b < 15 else "X.......x.x.xxXX", bt)
            S.pat("ka", KA, "....x.......x..x", bt)
    for b in (0, 8):
        S.put("taiko", TKL, b * 4, 1.0)
    S.put("clack", CL, 0, 1.0)
    S.put("clack", CL, 0.4, 0.8)
    S.put("clack", CL, 32, 0.8)
    S.put("clack", CL, 63.0, 0.4)
    S.put("clack", CL, 63.5, 0.55)
    chime = i_bell(parts=((1.0, 1.0, 1.4), (2.7, 0.3, 4.0), (5.2, 0.12, 8.0)), ring=2.5, gain=0.18)
    for b, bt, nm in ((1, 1.5, "A6"), (2, 3.0, "D7"), (5, 2.0, "G6"), (7, 0.5, "A6"),
                      (10, 1.0, "D7"), (13, 2.5, "Bb6"), (14, 0.5, "A6")):
        S.note("chime", chime, midi(nm), b * 4 + bt, 1.0, 0.7)

    spec = {
        "sham": dict(gain=1.0, pan=-0.2, lp=6000, rev=0.22),
        "sham2": dict(gain=0.8, pan=0.2, lp=5000, rev=0.15),
        "flute": dict(gain=0.7, pan=-0.05, lp=5000, echo=(0.75, 0.3, 0.2), rev=0.4),
        "koto": dict(gain=0.8, pan=0.3, lp=7000, echo=(0.5, 0.25, 0.12), rev=0.3),
        "bass": dict(gain=0.75, lp=900),
        "drone": dict(gain=0.4, lp=600),
        "taiko": dict(gain=0.5, rev=0.25),
        "ka": dict(gain=0.35, pan=0.3, rev=0.2),
        "clack": dict(gain=0.38, pan=-0.1, rev=0.35),
        "chime": dict(gain=0.9, pan=0.5, rev=0.5),
    }
    return S.mix("yoshiwara", spec, rev=(0.86, 0.3, 0.2))


# ================================================================= FLASHBACK
@track("flashback")
def flashback():
    """F major, 72 bpm, 3/4, 16 bars (40 s). Music box.
    A (1-8): melody in falling dotted sequences over a descending bass
    F-C/E-Dm-Am/C-Bb-F/A-Gm7-C7 | A' (9-16): same tune reaching higher, a
    lamenting inner line (A-G-F-E-D-Db-C-Bb) and the borrowed Bbm, C7 back to F."""
    S = Song(72, 16, bpb=3, tail=5.0)
    bars = ["F", "C/E", "Dm", "Am/C", "Bb", "F/A", "Gm7", "C7",
            "F", "C/E", "Dm", "Am/C", "Bb", "Bbm", "F/C", "C7"]
    prog = _prog(bars, 3)
    MEL = ("A5:1.5 G5:.5 F5:1 G5:1.5 F5:.5 E5:1 F5:1.5 E5:.5 D5:1 C5:1 E5:1 A5:1 "
           "D6:1.5 C6:.5 Bb5:1 C6:1.5 Bb5:.5 A5:1 Bb5:1.5 A5:.5 G5:1 E5:1 G5:1 Bb5:1 "
           "A5:1.5 G5:.5 F5:1 G5:1.5 F5:.5 E5:1 F5:1.5 E5:.5 D5:1 E5:1 A5:1 C6:1 "
           "F6:1.5 D6:.5 Bb5:1 Db6:1.5 C6:.5 Bb5:1 A5:1.5 G5:.5 F5:1 E5:1.5 F5:.5 G5:1")
    CNT = "A4:3 G4:3 F4:3 E4:3 D5:3 Db5:3 C5:3 Bb4:3"
    assert _beats(MEL) == 48 and _beats(CNT) == 24

    box = i_bell(parts=((1.0, 1.0, 1.9), (2.0, 0.12, 5.0), (3.0, 0.05, 8.0), (5.93, 0.1, 16.0)),
                 ring=2.2, gain=0.3, detune=0.0012, click=0.25)
    box_lo = i_bell(parts=((1.0, 1.0, 2.4), (2.0, 0.1, 6.0), (5.93, 0.06, 18.0)),
                    ring=1.8, gain=0.24, detune=0.001, click=0.15)
    glock = i_bell(parts=((1.0, 1.0, 1.2), (2.76, 0.2, 5.0), (5.4, 0.08, 10.0)), ring=2.5, gain=0.12)
    S.seq("mel", box, MEL, 0, legato=1.0)

    # accompaniment: quarter-note broken chords, then flowing 8ths
    for i, (cb, cd, sym) in enumerate(prog):
        b = _bass(sym, 49)
        v = _voice(sym, 64, 3)
        if i < 4:
            S.note("acc", box_lo, b, cb, 1, 0.9)
            S.note("acc", box_lo, v[1], cb + 1, 1, 0.6)
            S.note("acc", box_lo, v[2], cb + 2, 1, 0.6)
        else:
            for j, m in enumerate([b, v[0], v[1], v[2], v[1], v[0]]):
                S.note("acc", box_lo, m, cb + j * 0.5, 0.5, 0.95 if j == 0 else 0.55)

    S.seq("cnt", i_soft(a=0.25, d=0.5, s=0.8, r=0.7, gain=0.28), CNT, 24, legato=1.0)
    padi = i_soft(a=0.6, d=0.8, s=0.8, r=1.0, gain=0.1, vib=0.0)
    tb = i_tri(a=0.05, d=0.4, s=0.7, r=0.5, gain=0.45, steps=0)
    for cb, cd, sym in prog[8:]:
        for m in _voice(sym, 57, 3):
            S.note("pad", padi, m, cb, cd, 0.8)
        S.note("bass", tb, _bass(sym, 37), cb, cd * 0.97, 0.8)
    for bar, nm in ((8, "A6"), (10, "F6"), (12, "F7"), (14, "A6")):
        S.note("glock", glock, midi(nm), bar * 3, 1, 0.8)

    spec = {
        "mel": dict(gain=1.0, pan=0.1, echo=(0.75, 0.35, 0.28), rev=0.35),
        "acc": dict(gain=1.1, pan=-0.2, lp=6000, rev=0.25),
        "cnt": dict(gain=1.3, pan=-0.3, lp=4000, rev=0.3),
        "pad": dict(gain=1.2, lp=1400, rev=0.3),
        "bass": dict(gain=0.4, lp=500),
        "glock": dict(gain=1.2, pan=0.45, echo=(0.75, 0.35, 0.3), rev=0.5),
    }
    return S.mix("flashback", spec, rev=(0.88, 0.25, 0.2))


# ======================================================================= SAD
@track("sad")
def sad():
    """A minor -> C major lift, 66 bpm, 16 bars (58.2 s).
    A (1-8): vibrato pulse melody, sighing motif E-D-C-B-C, Am-F-C-G-Dm7-Am/C-F-Gsus4 |
    B (9-16): relative-major lift C-G/B-Am-Em/G-F-C/E-Dm7-E7sus4-E7 with octave
    doubling, 8th arpeggios and a counter-line in 10ths; E7 falls back to Am."""
    S = Song(66, 16, tail=5.0)
    bars = ["Am", "F", "C", "G", "Dm7", "Am/C", "F", "Gsus4 G",
            "C", "G/B", "Am", "Em/G", "F", "C/E", "Dm7", "E7sus4 E7"]
    prog = _prog(bars, 4)
    MEL = ("E5:1.5 D5:.5 C5:.5 B4:.5 C5:1 "
           "A4:2 G4:.5 A4:.5 C5:1 "
           "E5:1.5 D5:.5 C5:.5 D5:.5 E5:1 "
           "D5:3 R:1 "
           "F5:1.5 E5:.5 D5:.5 C5:.5 D5:1 "
           "C5:2 B4:.5 A4:.5 E5:1 "
           "A5:1.5 G5:.5 F5:.5 E5:.5 F5:1 "
           "D5:2 C5:1 B4:1 "
           "E5:1 G5:1 C6:1.5 B5:.5 "
           "B5:2 A5:.5 G5:.5 D5:1 "
           "C6:1.5 B5:.5 A5:1 E5:1 "
           "G5:1.5 A5:.5 B5:1 D6:1 "
           "E6:1.5 D6:.5 C6:1 A5:1 "
           "G5:2 E5:1 G5:1 "
           "F5:1.5 E5:.5 D5:.5 C5:.5 D5:1 "
           "E5:2 D5:1 B4:1")
    assert _beats(MEL) == 64
    B_HALF = MEL.split("E5:1 G5:1 C6:1.5", 1)
    B_TXT = "E5:1 G5:1 C6:1.5" + B_HALF[1]

    lead = i_pulse(duty=0.5, a=0.035, d=0.35, s=0.8, r=0.3, vib=0.012, vrate=5.2,
                   vdelay=0.22, gain=0.3)
    low = i_pulse(duty=0.25, a=0.04, d=0.35, s=0.75, r=0.3, vib=0.008, vdelay=0.3, gain=0.2)
    S.seq("lead", lead, MEL, 0, legato=0.97)
    S.seq("low", low, B_TXT, 32, tr=-12, legato=0.97)

    cnt = i_tri(a=0.12, d=0.4, s=0.85, r=0.4, gain=0.42, steps=0, vib=0.006)
    S.seq("cnt", cnt, "A4:4 R:4 R:4 R:2 B4:1 A4:.5 G4:.5", 0, legato=1.0, vel=0.8)
    S.seq("cnt", cnt, "F4:4 E4:4 F4:2 A4:2 G4:4", 16, legato=1.0, vel=0.85)
    S.seq("cnt", cnt, "E5:4 D5:4 C5:4 B4:4 A4:4 G4:4 F4:4 A4:2 G#4:2", 32, legato=1.0)

    pad = i_pad(gain=0.12, a=0.5, r=1.0, duty=0.5)
    for cb, cd, sym in prog:
        for m in _voice(sym, 57):
            S.note("pad", pad, m, cb, cd, 0.75 if cb < 32 else 0.9)

    bass = i_tri(a=0.03, d=0.3, s=0.9, r=0.35, gain=0.55)
    S.bassline("bass", bass, prog, 0, 32, "whole", 43)
    S.bassline("bass", bass, prog, 32, 64, "half", 43)

    pl = i_tri(a=0.003, d=0.5, s=0.0, r=0.2, gain=0.4, steps=0)
    S.arp("arp", pl, prog, 16, 32, [0, 1, 2, 1], 1.0, 64, vel=0.6, n=3, legato=1.2)
    S.arp("arp", pl, prog, 32, 64, [0, 1, 2, 1, 3, 2, 1, 2], 0.5, 64, vel=0.75, n=3, legato=1.4)

    S.put("perc", d_revcrash(2.0), 32 - 2.0 / S.spb, 0.35)
    S.put("perc", d_crash(3.0), 32, 0.3)
    S.put("perc", d_revcrash(1.5), 48 - 1.5 / S.spb, 0.25)
    kk = d_kick(110, 42, 0.5, 5.0, 0.1)
    for b in range(8, 16):
        S.pat("perc", kk, "X.......x.......", b * 4, gain=0.35)

    spec = {
        "lead": dict(gain=1.0, pan=-0.1, lp=3400, echo=(0.75, 0.3, 0.22), rev=0.4),
        "low": dict(gain=0.55, pan=0.15, lp=2500, rev=0.2),
        "cnt": dict(gain=0.6, pan=0.3, lp=3000, rev=0.3),
        "pad": dict(gain=0.75, lp=1500, rev=0.35),
        "bass": dict(gain=0.55, lp=900),
        "arp": dict(gain=0.9, pan=0.35, lp=4000, rev=0.3),
        "perc": dict(gain=0.6, rev=0.3),
    }
    return S.mix("sad", spec, rev=(0.88, 0.3, 0.2))


# ====================================================================== EPIC
@track("epic")
def epic():
    """D major -> E major climax, 150 bpm, 32 bars (51.2 s).
    1-4 fanfare intro D-D-Bb-C | 5-12 anthem A theme | 13-20 rising build
    G-A-F#m-Bm-G-A-F#m7-Bsus4/B, counter-line climbing | 21-28 A theme up a whole
    step (E) with harmony, counter-melody, taiko | 29-32 C-D-G-A7 turnaround."""
    S = Song(150, 32, tail=3.0)
    bars = ["D", "D", "Bb", "C",
            "D", "A/C#", "Bm", "G", "D/F#", "G", "Em7", "Asus4 A",
            "G", "A", "F#m", "Bm", "G", "A", "F#m7", "Bsus4 B B B",
            "E", "B/D#", "C#m", "A", "E/G#", "A", "F#m7", "Bsus4 B",
            "C", "D", "G", "A7"]
    prog = _prog(bars, 4)
    INTRO = ("D5:1/3 D5:1/3 D5:1/3 A5:2 F#5:1 "
             "G5:.5 F#5:.5 E5:.5 F#5:.5 D5:2 "
             "D5:1/3 F5:1/3 Bb5:1/3 D6:2 C6:.5 Bb5:.5 "
             "C6:1 G5:1 E5:1 G5:.5 E5:.5")
    A = ("A4:1 D5:1.5 E5:.5 F#5:1 "
         "E5:1.5 D5:.5 C#5:1 A4:1 "
         "B4:1 D5:1.5 E5:.5 F#5:1 "
         "G5:2 F#5:.5 E5:.5 D5:1 "
         "A5:1.5 F#5:.5 D5:1 A5:1 "
         "B5:1.5 G5:.5 D5:1 B5:1 "
         "D6:1.5 B5:.5 G5:.5 A5:.5 B5:1 "
         "A5:1.5 D5:.5 C#5:1 E5:1")
    B = ("D5:.5 D5:.5 G5:1 F#5:.5 G5:.5 A5:1 "
         "A5:2 E5:1 C#5:1 "
         "C#5:.5 C#5:.5 F#5:1 E5:.5 F#5:.5 A5:1 "
         "B5:2 F#5:1 D5:1 "
         "D5:.5 D5:.5 G5:1 A5:.5 B5:.5 D6:1 "
         "C#6:2 A5:1 E5:1 "
         "A5:1 C#6:1 B5:.5 A5:.5 F#5:1 "
         "E5:1 D#5:1 F#5:.5 E5:.5 D#5:.5 C#5:.5")
    T = ("E5:1/3 E5:1/3 E5:1/3 G5:2 C6:1 "
         "F#5:1/3 F#5:1/3 F#5:1/3 A5:2 D6:1 "
         "D6:1.5 B5:.5 G5:1 B5:1 "
         "A5:1 G5:1 E5:1 C#5:1")
    CNT_B = "B3:4 C#4:4 C#4:4 D4:4 D4:4 E4:4 E4:4 D#4:2 F#4:2"
    CNT_A2 = "B4:2 G#4:2 F#4:2 A4:2 G#4:2 E4:2 E4:2 C#5:2 B4:2 E5:2 C#5:2 E5:2 E5:2 C#5:2 B4:4"
    for s, n in ((INTRO, 16), (A, 32), (B, 32), (T, 16), (CNT_B, 32), (CNT_A2, 32)):
        assert abs(_beats(s) - n) < 1e-9, s

    lead = i_pulse(duty=0.5, a=0.005, d=0.15, s=0.8, r=0.08, vib=0.012, vdelay=0.18, gain=0.3)
    lead2 = i_pulse(duty=0.25, a=0.005, d=0.15, s=0.75, r=0.08, vib=0.01, vdelay=0.2, gain=0.22)
    cnt = i_pulse(duty=0.5, a=0.02, d=0.3, s=0.7, r=0.12, vib=0.006, gain=0.22)
    arp = i_pulse(duty=0.125, a=0.002, d=0.09, s=0.25, r=0.03, gain=0.22)
    stab = i_pulse(duty=0.25, a=0.003, d=0.2, s=0.55, r=0.06, gain=0.2)
    bass = i_tri(a=0.003, d=0.08, s=0.9, r=0.03, gain=0.6)

    S.seq("lead", lead, INTRO, 0)
    S.seq("lead", lead, A, 16)
    S.seq("lead", lead, B, 48)
    S.seq("cnt", cnt, CNT_B, 48, legato=0.98)
    S.seq("lead", lead, A, 80, tr=2)
    emaj = [_pc(x) for x in ("E", "F#", "G#", "A", "B", "C#", "D#")]
    S.seq("harm", lead2, A, 80, tr=2, harm=_harm_fn(prog, emaj))
    S.seq("cnt", cnt, CNT_A2, 80, legato=0.98)
    S.seq("lead", lead, T, 112)

    # brass stabs (intro + turnaround)
    hits = [(0, 1.5), (1.5, 1.0), (2.5, 0.5), (3.0, 1.0)]
    for b in list(range(0, 4)) + list(range(28, 32)):
        v = _voice(bars[b], 62, 3)
        r = _bass(bars[b], 38)
        for bt, d in hits:
            for m in v:
                S.note("stab", stab, m, b * 4 + bt, d * 0.85, 1.0 if bt == 0 else 0.75)
            S.note("bass", bass, r if bt in (0, 2.5) else r + 12, b * 4 + bt, d * 0.85)

    S.arp("arp", arp, prog, 16, 48, [0, 1, 2, 3, 2, 1], 0.5, 66, vel=0.8)
    S.arp("arp", arp, prog, 48, 80, [0, 1, 2, 3, 2, 1], 0.25, 66, vel=0.85, accent=[1, .6, .75, .6])
    S.arp("arp", arp, prog, 80, 112, [0, 1, 2, 3, 2, 1], 0.25, 68, vel=0.95, accent=[1, .6, .75, .6])

    S.bassline("bass", bass, prog, 16, 48, "oct8", 40)
    S.bassline("bass", bass, prog, 48, 80, "drive8", 40)
    S.bassline("bass", bass, prog, 80, 112, "oct8", 40)

    K, SN, H, OH = d_kick(140, 42, 0.45, 6.0, 0.5), d_snare(170, 0.32, 10.0), d_hat(), d_ohat()
    CR = d_crash(2.6, 5)
    TH, TM, TL = d_tom(170), d_tom(125), d_tom(90)
    BOOM = d_taiko(50, 1.3, 9)
    for b in range(32):
        bt = b * 4
        if b < 4 or b >= 28:
            S.pat("kick", K, "X...X...X...X..." if b not in (3, 31) else "X...X...........", bt)
            S.pat("snare", SN, "....X.......X...", bt)
            S.pat("tom", TL, "..x.......x.....", bt)
            S.pat("hat", OH, "..x...x...x...x.", bt, gain=0.6)
            if b in (3, 31):
                S.pat("tom", TH, "........XxXx....", bt)
                S.pat("tom", TM, "............XxXx", bt)
                S.pat("snare", SN, "..............XX", bt, gain=0.8)
        elif b < 12:
            S.pat("kick", K, "X.....x.X.......", bt)
            S.pat("snare", SN, "....X.......X...", bt)
            S.pat("hat", H, "x.x.x.x.x.x.x.x.", bt)
            if b == 11:
                S.pat("snare", SN, "............XxXX", bt)
        elif b < 20:
            S.pat("kick", K, "X...X...X...X...", bt)
            S.pat("snare", SN, "....X.......X..." if b < 16 else "....X.......X.x.", bt)
            S.pat("hat", H, "xoxoxoxoxoxoxoxo", bt)
            if b == 19:
                S.pat("snare", SN, "x.x.x.x.xxxxXXXX", bt, gain=0.85)
                S.pat("tom", TL, "X.......X.......", bt)
        else:
            S.pat("kick", K, "X.x.X...X.x.X...", bt)
            S.pat("snare", SN, "....X.......X...", bt)
            S.pat("hat", OH, "..x...x...x...x.", bt, gain=0.7)
            S.pat("hat", H, "x.x.x.x.x.x.x.x.", bt, gain=0.7)
            if b == 27:
                S.pat("tom", TH, "........XX......", bt)
                S.pat("tom", TM, "..........XX....", bt)
                S.pat("tom", TL, "............XXXX", bt)
    for b in (0, 4, 8, 12, 16, 20, 22, 24, 26, 28):
        S.put("crash", CR, b * 4, 1.0)
    for b in (0, 20, 24, 28):
        S.put("tom", BOOM, b * 4, 1.0)

    spec = {
        "lead": dict(gain=1.0, pan=-0.12, lp=6500, echo=(0.75, 0.3, 0.15), rev=0.2),
        "harm": dict(gain=0.95, pan=0.25, lp=6000, rev=0.18),
        "cnt": dict(gain=0.75, pan=0.3, lp=3500, rev=0.25),
        "arp": dict(gain=1.2, pan=0.4, lp=6500, rev=0.1),
        "stab": dict(gain=0.7, pan=-0.25, lp=5500, rev=0.2),
        "bass": dict(gain=1.0, lp=3000),
        "kick": dict(gain=0.8),
        "snare": dict(gain=0.62, rev=0.3),
        "hat": dict(gain=0.9, pan=0.25),
        "tom": dict(gain=0.75, rev=0.25),
        "crash": dict(gain=0.45, pan=-0.2),
    }
    return S.mix("epic", spec, rev=(0.84, 0.3, 0.3))
