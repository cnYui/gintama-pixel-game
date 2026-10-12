"""Sound-effect library for 银魂 像素剧场 (all names from CONTRACT.md section 6).

Every effect is a zero-arg function registered with @sfx(name) that returns a
float32 buffer at SR (mono, or (n, 2) stereo for wide ambiences / big hits).
One-shots are normalised to peak ~0.8, loops to ~0.5.  Loops are built to be
*exactly* periodic (circular filtering, circular event placement, integer
oscillator cycles), so the mixer can tile them without seams.

Style: retro chiptune + anime comedy.  Everything is deterministic (seeded
numpy generators derived from engine.core.stable_hash) and vectorised.
"""
import math

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.signal import butter, fftconvolve, lfilter, resample_poly, sosfilt

from engine.audio import sfx
from engine.core import stable_hash
from engine.synth import *  # noqa: F401,F403  (SR, n_samples, freq, ...)
from engine.synth import SR, freq, n_samples

TAU = 2.0 * math.pi
NYQ = SR / 2


# =================================================================== helpers
def _n(d):
    return n_samples(d)


def _t(n):
    return np.arange(int(n), dtype=np.float64) / SR


def _rng(*key):
    return np.random.default_rng(stable_hash("sfx", *key))


def _wn(n, *key):
    return _rng(*key).uniform(-1.0, 1.0, int(n))


def _snh(n, period, *key):
    """Sample-and-hold ('NES') noise."""
    n = int(n)
    v = _rng(*key).uniform(-1.0, 1.0, n // period + 2)
    return np.repeat(v, period)[:n]


def _norm(x):
    m = float(np.max(np.abs(x))) if len(x) else 0.0
    return x / m if m > 1e-12 else x


def _nrms(x, r=0.3):
    s = float(np.sqrt(np.mean(np.square(x)))) if len(x) else 0.0
    return x * (r / s) if s > 1e-12 else x


_SOS = {}


def _sos(kind, f, order):
    key = (kind, f, order)
    if key not in _SOS:
        _SOS[key] = butter(order, f, btype=kind, fs=SR, output="sos")
    return _SOS[key]


def _lp(x, fc, order=2):
    return sosfilt(_sos("lowpass", min(float(fc), NYQ * 0.95), order), x, axis=0)


def _hp(x, fc, order=2):
    return sosfilt(_sos("highpass", float(fc), order), x, axis=0)


def _bp(x, lo, hi, order=2):
    return sosfilt(_sos("bandpass", (float(lo), min(float(hi), NYQ * 0.95)), order), x, axis=0)


def _cyc(f, n, sr=SR):
    """Accumulated cycles (unwrapped phase / 2pi), starting at 0."""
    n = int(n)
    if np.isscalar(f):
        return np.arange(n) * (float(f) / sr)
    f = np.asarray(f, np.float64)
    if len(f) != n:
        f = np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(f)), f)
    c = np.cumsum(f) / sr
    return c - c[0]


def _sin(f, n, ph=0.0):
    return np.sin(TAU * (_cyc(f, n) + ph))


def _tri(f, n):
    p = (_cyc(f, n) + 0.25) % 1.0
    return 4.0 * np.abs(p - 0.5) - 1.0


def _blep(p, dt):
    """PolyBLEP residual for a unit step at phase 0 (p in [0,1), dt = f/sr)."""
    out = np.zeros_like(p)
    a = p < dt
    u = p[a] / dt[a]
    out[a] = u + u - u * u - 1.0
    b = p > 1.0 - dt
    u = (p[b] - 1.0) / dt[b]
    out[b] = u * u + u + u + 1.0
    return out


def _osc(kind, f, n, duty=0.5, os=4):
    """Band-limited square/saw: PolyBLEP at os x rate, then decimated."""
    n = int(n)
    m = n * os
    if np.isscalar(f):
        fo = np.full(m, float(f))
    else:
        f = np.asarray(f, np.float64)
        if len(f) != n:
            f = np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(f)), f)
        fo = np.repeat(f, os) if os > 1 else f
    dt = np.clip(fo / (SR * os), 1e-9, 0.5)
    p = _cyc(fo, m, SR * os) % 1.0
    if kind == "sqr":
        x = np.where(p < duty, 1.0, -1.0) + _blep(p, dt) - _blep((p - duty) % 1.0, dt)
        x -= (2 * duty - 1)
    else:
        x = 2.0 * p - 1.0 - _blep(p, dt)
    if os > 1:
        x = resample_poly(x, 1, os)[:n]
    return x


def _sqr(f, n, duty=0.5, os=4):
    return _osc("sqr", f, n, duty, os)


def _saw(f, n, os=4):
    return _osc("saw", f, n, 0.5, os)


def _exp(n, tau):
    return np.exp(-_t(n) / tau)


def _att(n, a):
    return np.clip(_t(n) / max(a, 1e-6), 0.0, 1.0)


def _ad(n, a, tau):
    t = _t(n)
    return np.clip(t / max(a, 1e-6), 0, 1) * np.exp(-np.maximum(t - a, 0) / tau)


def _pts(n, pts):
    return np.interp(_t(n), [p[0] for p in pts], [p[1] for p in pts])


def _glide(n, f0, f1, tau):
    return f1 + (f0 - f1) * _exp(n, tau)


def _xs(n, f0, f1, T=None):
    """Exponential sweep f0->f1 over T seconds (then hold)."""
    t = _t(n)
    T = T or max(t[-1], 1e-6)
    return f0 * (f1 / f0) ** np.clip(t / T, 0, 1)


def _buf(dur, ch=1):
    return np.zeros(_n(dur)) if ch == 1 else np.zeros((_n(dur), ch))


def _at(dst, src, t0, g=1.0):
    i = int(round(t0 * SR))
    if i < 0:
        src, i = src[-i:], 0
    m = min(len(src), len(dst) - i)
    if m > 0:
        dst[i:i + m] += g * src[:m]


def _atw(dst, src, t0, g=1.0):
    """Circular add (for loops): wraps past the end back to the start."""
    L = len(dst)
    i = int(round(t0 * SR)) % L
    src = g * src
    pos = 0
    while pos < len(src):
        m = min(len(src) - pos, L - i)
        dst[i:i + m] += src[pos:pos + m]
        pos += m
        i = 0


def _swoosh(n, f, bw, *key):
    """Noise band of width ~2*bw centred on (possibly moving) frequency f."""
    base = _nrms(_lp(_wn(n, *key), bw, 2), 0.35)
    return base * np.cos(TAU * _cyc(f, n)) * 1.4


def _ring(n, freqs, amps, taus, a=0.0008, key=("ring",)):
    """Sum of decaying sine partials (bells, metal)."""
    t = _t(n)
    r = _rng(*key)
    out = np.zeros(int(n))
    for f, am, tau in zip(freqs, amps, taus):
        if f >= NYQ * 0.9:
            continue
        out += am * np.sin(TAU * f * t + r.uniform(0, TAU)) * np.exp(-t / tau)
    return out * _att(n, a)


def _thump(n, f0, f1, ftau, atau, a=0.001):
    return _sin(_glide(n, f0, f1, ftau), n) * _ad(n, a, atau)


def _fin(x, peak=0.8, fout=0.02, fin=0.0008, trim=True, hpf=20.0, thr=0.0015):
    """Finish a one-shot: DC-block, trim silence, click-free fades, normalise."""
    x = np.asarray(x, np.float64)
    x = sosfilt(_sos("highpass", hpf, 1), x, axis=0)
    if trim:
        a = np.abs(x) if x.ndim == 1 else np.max(np.abs(x), axis=1)
        idx = np.nonzero(a > a.max() * thr)[0]
        if len(idx):
            x = x[: min(len(x), idx[-1] + _n(0.03))]
    n = len(x)
    env = np.ones(n)
    ni, nf = min(_n(fin), n // 4), min(_n(fout), n // 2)
    if ni > 0:
        env[:ni] = np.sin(np.linspace(0, math.pi / 2, ni)) ** 2
    if nf > 0:
        env[n - nf:] *= np.cos(np.linspace(0, math.pi / 2, nf)) ** 2
    x = x * (env if x.ndim == 1 else env[:, None])
    # zero the mean with a smooth bump (keeps the ends at exactly zero)
    w = np.hanning(n) if n > 4 else np.ones(n)
    if x.ndim == 1:
        x = x - (x.mean() / max(w.mean(), 1e-9)) * w
    else:
        x = x - (x.mean(axis=0) / max(w.mean(), 1e-9))[None, :] * w[:, None]
    m = float(np.max(np.abs(x)))
    if m > 1e-9:
        x = x * (peak / m)
    return x.astype(np.float32)


# ---- loop helpers (exactly periodic constructions)
def _cf(fn, x):
    """Circular filtering: filter 3 tiled copies, keep the last -> periodic."""
    L = len(x)
    y = fn(np.concatenate([x, x, x], axis=0))
    return y[2 * L:]


def _pmod(L, npts, *key, lo=0.0, hi=1.0):
    """Periodic smooth random curve over L samples (npts control points)."""
    v = _rng(*key).uniform(lo, hi, npts)
    xp = np.linspace(0, L, npts + 1)
    cs = CubicSpline(xp, np.append(v, v[0]), bc_type="periodic")
    return cs(np.arange(L))


def _pfreq(f):
    """Scale a frequency contour so it completes an integer number of cycles."""
    c = float(np.sum(f)) / SR
    return f * (max(1, round(c)) / c)


def _cconv(imp, k):
    """Circular convolution of an impulse train with a short kernel."""
    L = len(imp)
    y = fftconvolve(imp, k)
    out = y[:L].copy()
    tail = y[L:]
    while len(tail):
        m = min(len(tail), L)
        out[:m] += tail[:m]
        tail = tail[m:]
    return out


def _lfin(x, peak=0.5):
    x = np.asarray(x, np.float64)
    x = x - x.mean(axis=0)
    m = float(np.max(np.abs(x)))
    if m > 1e-9:
        x = x * (peak / m)
    return x.astype(np.float32)


def _st(l, r):
    return np.stack([l, r], 1)


# =================================================================== voices / UI
@sfx("blip")
def s_blip():
    n = _n(0.045)
    x = _sqr(520, n, 0.5) * _att(n, 0.0015) * _exp(n, 0.016)
    x = _lp(x, 6000, 1)
    return _fin(x, fout=0.006, trim=False)


@sfx("type")
def s_type():
    n = _n(0.05)
    click = _nrms(_bp(_wn(n, "type"), 1800, 6500)) * _exp(n, 0.0045)
    thock = _thump(n, 480, 300, 0.01, 0.010, 0.0005)
    return _fin(click * 0.8 + thock * 0.55, fout=0.008)


# =================================================================== impacts
@sfx("punch")
def s_punch():
    n = _n(0.4)
    body = _thump(n, 180, 50, 0.035, 0.075, 0.0008)
    crack = _nrms(_bp(_wn(n, "punch"), 700, 5000)) * _exp(n, 0.012)
    crunch = _sqr(_glide(n, 340, 90, 0.03), n) * _exp(n, 0.03) * 0.3
    x = np.tanh(1.7 * (body * 1.0 + crack * 0.6 + crunch))
    return _fin(x)


@sfx("punch_big")
def s_punch_big():
    n = _n(1.0)
    sub = _thump(n, 140, 30, 0.10, 0.30, 0.002)
    body = _thump(n, 300, 70, 0.03, 0.07)
    crack = _nrms(_hp(_wn(n, "pb", 1), 1200)) * _exp(n, 0.018)
    crunch = _nrms(_bp(_snh(n, 6, "pb", 2), 300, 3000)) * _exp(n, 0.07)
    tail = _nrms(_lp(_wn(n, "pb", 3), 900)) * _ad(n, 0.01, 0.25)
    x = sub * 1.1 + body * 0.8 + crack * 0.7 + crunch * 0.45 + tail * 0.18
    return _fin(np.tanh(2.0 * x))


@sfx("hit")
def s_hit():
    n = _n(0.3)
    sq = _sqr(_glide(n, 620, 110, 0.05), n) * _exp(n, 0.06)
    nz = _nrms(_bp(_snh(n, 4, "hit"), 500, 6000)) * _exp(n, 0.035)
    th = _thump(n, 160, 55, 0.04, 0.07)
    return _fin(np.tanh(1.5 * (sq * 0.35 + nz * 0.5 + th * 0.8)))


@sfx("kick")
def s_kick():
    x = _buf(0.45)
    m = _n(0.08)
    sw = _swoosh(m, _xs(m, 900, 3200), 700, "kick", 1) * (_t(m) / 0.08) ** 2
    _at(x, sw * 0.45, 0.0)
    k = _n(0.37)
    imp = _thump(k, 170, 45, 0.03, 0.09) + _nrms(_bp(_wn(k, "kick", 2), 900, 4000)) * _exp(k, 0.014) * 0.6
    _at(x, imp, 0.075)
    return _fin(np.tanh(1.6 * x))


@sfx("slap")
def s_slap():
    n = _n(0.26)
    w = _nrms(_bp(_wn(n, "slap"), 1500, 9000))
    crack = w * _exp(n, 0.009)
    crack2 = np.zeros(n)
    _at(crack2, w[: _n(0.03)] * _exp(_n(0.03), 0.004), 0.004, 0.55)
    body = _thump(n, 320, 180, 0.02, 0.025) * 0.45
    x = crack + crack2 + body
    room = np.zeros(n)
    _at(room, x, 0.023, 0.22)
    _at(room, x, 0.047, 0.10)
    x = x + _lp(room, 3500)
    return _fin(np.tanh(1.4 * x))


@sfx("thud")
def s_thud():
    n = _n(0.5)
    body = _thump(n, 115, 42, 0.06, 0.11, 0.003)
    dirt = _nrms(_lp(_wn(n, "thud"), 500)) * _ad(n, 0.002, 0.05)
    return _fin(np.tanh(1.5 * (body + dirt * 0.5)))


@sfx("land")
def s_land():
    n = _n(0.3)
    th = _thump(n, 150, 55, 0.025, 0.055)
    puff = _nrms(_lp(_wn(n, "land"), 1200)) * _ad(n, 0.003, 0.05)
    dust = _nrms(_hp(_wn(n, "land", 2), 3000)) * _ad(n, 0.01, 0.07)
    return _fin(np.tanh(1.3 * (th + puff * 0.45 + dust * 0.12)))


@sfx("impact")
def s_impact():
    n = _n(2.5)
    sub = _thump(n, 72, 26, 0.45, 0.75, 0.004)
    thump = _thump(n, 170, 50, 0.03, 0.08)
    dark = _nrms(_lp(_wn(n, "imp", 1), 260)) * _ad(n, 0.006, 0.6)
    bright = _nrms(_bp(_wn(n, "imp", 2), 400, 4000)) * _exp(n, 0.035)
    rumble = _nrms(_lp(_wn(n, "imp", 3), 110)) * _ad(n, 0.05, 1.0)
    x = sub * 1.0 + thump * 0.6 + dark * 0.55 + bright * 0.35 + rumble * 0.35
    return _fin(np.tanh(1.8 * x), fout=0.1)


@sfx("heartbeat")
def s_heartbeat():
    x = _buf(0.9)
    for t0, f, g in ((0.0, 62, 1.0), (0.24, 54, 0.72)):
        k = _n(0.35)
        b = _thump(k, f * 1.5, f, 0.015, 0.075, 0.003)
        b += _nrms(_lp(_wn(k, "hb", t0), 160)) * _ad(k, 0.002, 0.03) * 0.25
        _at(x, b, t0, g)
    x = _lp(x, 320)
    return _fin(np.tanh(1.3 * x), trim=False, fout=0.05)


# =================================================================== crashes / breakage
@sfx("crash")
def s_crash():
    n = _n(1.3)
    bang = _nrms(_lp(_wn(n, "cr", 1), 3000)) * _exp(n, 0.10)
    hiss = _nrms(_hp(_wn(n, "cr", 2), 2500)) * _ad(n, 0.002, 0.28)
    thump = _thump(n, 130, 40, 0.05, 0.15)
    metal = _ring(n, [410, 1130, 1790, 2650, 3480, 5020], [.5, .45, .4, .3, .25, .15],
                  [.25, .2, .3, .15, .12, .08], key=("crash",))
    x = bang * 0.8 + hiss * 0.35 + thump * 0.9 + metal * 0.5
    r = _rng("crash-debris")
    for i in range(16):
        t0 = 0.06 + r.uniform(0, 0.85) ** 1.4
        k = _n(0.04)
        d = _nrms(_bp(_wn(k, "deb", i), 1500, 7000)) * _exp(k, r.uniform(0.004, 0.012))
        d += _ring(k, [r.uniform(1500, 5000)], [0.8], [0.02], key=("deb", i))
        _at(x, d, t0, 0.5 * (1 - t0 / 1.1))
    return _fin(np.tanh(1.6 * x), fout=0.08)


@sfx("glass")
def s_glass():
    n = _n(1.2)
    x = _nrms(_hp(_wn(n, "gl"), 3000)) * _exp(n, 0.05) * 0.7
    x += _thump(n, 400, 200, 0.02, 0.02) * 0.3
    r = _rng("glass-tinkle")
    for i in range(46):
        t0 = r.exponential(0.18)
        if t0 > 0.95:
            t0 = r.uniform(0, 0.95)
        k = _n(0.2)
        f = r.uniform(2500, 9500)
        tk = _ring(k, [f, f * 2.76], [1.0, 0.35], [r.uniform(0.02, 0.07)] * 2, key=("gt", i))
        _at(x, tk, t0, r.uniform(0.2, 0.7) * (1 - t0))
    return _fin(x, fout=0.08)


@sfx("door")
def s_door():
    n = _n(0.62)
    roll_mod = 0.6 + 0.4 * np.abs(_lp(_snh(n, _n(1 / 40), "door", 1), 60))
    roll_mod = roll_mod / roll_mod.max()
    roll = (_nrms(_lp(_wn(n, "door", 2), 700)) + _nrms(_bp(_wn(n, "door", 3), 150, 500)) * 0.7) * roll_mod
    roll *= _pts(n, [(0, 0), (0.05, 1), (0.45, 0.9), (0.5, 0.0), (1, 0)])
    x = roll * 0.5
    k = _n(0.12)
    knock = _ring(k, [200, 430, 910], [1, .6, .3], [.02, .015, .01], key=("door",))
    knock += _nrms(_bp(_wn(k, "door", 4), 300, 2000)) * _exp(k, 0.01) * 0.6
    _at(x, knock, 0.48, 0.9)
    return _fin(x)


@sfx("door_bang")
def s_door_bang():
    x = _buf(0.85)
    m = _n(0.11)
    slide = _nrms(_bp(_wn(m, "db", 1), 200, 3000)) * _pts(m, [(0, 0), (0.03, 1), (0.11, 1)])
    _at(x, slide, 0.0, 0.35)
    k = _n(0.75)
    bang = _thump(k, 160, 90, 0.03, 0.12)
    bang += _ring(k, [210, 470, 1030], [.7, .45, .3], [.07, .05, .025], key=("db",))
    bang += _nrms(_bp(_wn(k, "db", 2), 200, 3000)) * _exp(k, 0.03) * 0.8
    rattle = _nrms(_bp(_snh(k, 3, "db", 3), 1800, 4500)) * np.abs(_sin(23, k)) * _ad(k, 0.02, 0.12)
    bang += rattle * 0.25
    _at(x, bang, 0.095)
    return _fin(np.tanh(1.8 * x))


# =================================================================== blades / weapons
@sfx("whoosh")
def s_whoosh():
    n = _n(0.5)
    T = 0.46
    f = np.interp(_t(n), [0, T * 0.45, T], [350, 2300, 550])
    env = np.sin(np.pi * np.clip(_t(n) / T, 0, 1)) ** 1.6
    x = _swoosh(n, f, 900, "wh", 1) + _swoosh(n, f * 0.45, 300, "wh", 2) * 0.6
    return _fin(x * env)


@sfx("dash")
def s_dash():
    n = _n(0.34)
    env = _pts(n, [(0, 0), (0.015, 1), (0.1, 0.7), (0.3, 0)])
    x = _swoosh(n, _xs(n, 500, 5500, 0.2), 1500, "dash") * env
    zip_ = _sqr(_xs(n, 300, 1300, 0.08), n, 0.25) * _ad(n, 0.002, 0.03) * 0.25
    return _fin(x + zip_)


@sfx("slash")
def s_slash():
    x = _buf(0.75)
    m = _n(0.16)
    env = np.sin(np.pi * _t(m) / 0.16) ** 2
    _at(x, _swoosh(m, _xs(m, 700, 4500), 900, "sl") * env, 0.0, 0.8)
    k = _n(0.62)
    ring = _ring(k, [2150, 2154, 3420, 5110, 6730], [.6, .22, .35, .25, .15],
                 [.35, .35, .25, .15, .1], key=("slash",))
    tick = _nrms(_hp(_wn(k, "sl", 2), 3000)) * _exp(k, 0.003)
    _at(x, ring * 0.55 + tick * 0.6, 0.10)
    return _fin(x, fout=0.05)


@sfx("slash_big")
def s_slash_big():
    x = _buf(1.5)
    m = _n(0.28)
    env = np.sin(np.pi * _t(m) / 0.28) ** 1.5
    w = _swoosh(m, _xs(m, 300, 3200), 1200, "slb", 1) + _swoosh(m, _xs(m, 150, 900), 300, "slb", 2) * 0.7
    _at(x, w * env, 0.0, 0.9)
    k = _n(1.25)
    boom = _thump(k, 115, 35, 0.08, 0.2)
    crack = _nrms(_hp(_wn(k, "slb", 3), 1500)) * _exp(k, 0.02)
    ring = _ring(k, [1240, 1243, 1980, 3100, 4460, 6020], [.6, .25, .4, .3, .2, .12],
                 [.9, .9, .6, .4, .25, .15], key=("slashbig",))
    shimmer = _nrms(_bp(_wn(k, "slb", 4), 2000, 8000)) * _ad(k, 0.005, 0.3)
    _at(x, boom * 0.9 + crack * 0.7 + ring * 0.5 + shimmer * 0.12, 0.22)
    return _fin(np.tanh(1.3 * x), fout=0.1)


@sfx("clang")
def s_clang():
    n = _n(1.4)
    f0, f1 = 830.0, 1115.0
    ratios = [1, 1.004, 2.76, 2.767, 5.40, 8.93, 13.34]
    amps = [.6, .25, .55, .25, .35, .22, .12]
    taus = [.9, .9, .6, .6, .35, .2, .12]
    ring = _ring(n, [f0 * r for r in ratios], amps, taus, key=("clang", 1))
    ring += _ring(n, [f1 * r for r in ratios], [a * 0.7 for a in amps], [t * 0.8 for t in taus], key=("clang", 2))
    crack = _nrms(_hp(_wn(n, "clang"), 2000)) * _exp(n, 0.012)
    thunk = _nrms(_bp(_wn(n, "clang", 3), 400, 1500)) * _exp(n, 0.03)
    return _fin(np.tanh(1.2 * (crack * 0.9 + ring * 0.55 + thunk * 0.35)), fout=0.1)


@sfx("shing")
def s_shing():
    n = _n(1.05)
    t = _t(n)
    scrape = _swoosh(n, _xs(n, 2000, 7000, 0.35), 1500, "shing")
    scrape *= _pts(n, [(0, 0), (0.03, 1), (0.3, 0.8), (0.45, 0), (2, 0)])
    parts = [2960, 2968, 4440, 5920, 7400]
    ring = sum(a * np.sin(TAU * f * t) for f, a in zip(parts, [1, .8, .6, .4, .25]))
    ring *= _pts(n, [(0, 0), (0.12, 0.4), (0.3, 1.0), (2, 1)]) * np.exp(-np.maximum(t - 0.3, 0) / 0.3)
    ring *= 0.8 + 0.2 * np.sin(TAU * 14 * t)
    return _fin(scrape * 0.5 + ring * 0.3, fout=0.1)


@sfx("stab")
def s_stab():
    x = _buf(0.35)
    m = _n(0.075)
    _at(x, _swoosh(m, _xs(m, 1500, 5000), 1000, "stab") * np.sin(np.pi * _t(m) / 0.075) ** 2, 0.0, 0.6)
    k = _n(0.28)
    thunk = _thump(k, 230, 90, 0.03, 0.06) + _nrms(_bp(_wn(k, "stab", 2), 300, 1500)) * _exp(k, 0.02) * 0.6
    _at(x, thunk, 0.06)
    return _fin(np.tanh(1.5 * x))


def _shot(n, key, boom_f=140):
    crack = _wn(n, "shot", key) * _exp(n, 0.006)
    boom = _thump(n, boom_f, 45, 0.03, 0.08, 0.0005)
    body = _nrms(_lp(_wn(n, "shot", key, 2), 1800)) * _exp(n, 0.05)
    return crack * 1.0 + boom * 0.9 + body * 0.5


@sfx("gunshot")
def s_gunshot():
    n = _n(0.9)
    x = _shot(n, 0)
    x += _nrms(_lp(_wn(n, "gun", 3), 700)) * _ad(n, 0.005, 0.25) * 0.22
    echo = np.zeros(n)
    _at(echo, x, 0.12, 0.25)
    _at(echo, x, 0.26, 0.12)
    x = x + _lp(echo, 1500)
    return _fin(np.tanh(2.5 * x), fout=0.08)


@sfx("machinegun")
def s_machinegun():
    x = _buf(1.4)
    r = _rng("mg")
    for i in range(14):
        k = _n(0.12)
        s = _shot(k, 10 + i, boom_f=r.uniform(120, 170))
        s += _nrms(_bp(_snh(k, 5, "mg", i), 400, 5000)) * _exp(k, 0.02) * 0.5
        _at(x, s, i * 0.068 + r.uniform(0, 0.006), r.uniform(0.8, 1.0))
    n = len(x)
    tail = _nrms(_lp(_wn(n, "mg", 99), 800)) * _pts(n, [(0, 0), (0.1, 1), (0.95, 1), (1.4, 0)]) * 0.12
    return _fin(np.tanh(2.2 * (x + tail)), fout=0.1)


@sfx("bazooka")
def s_bazooka():
    n = _n(1.6)
    thump = _thump(n, 95, 32, 0.12, 0.3, 0.002)
    blast = _nrms(_lp(_wn(n, "bz", 1), 1400)) * _exp(n, 0.07) + _nrms(_hp(_wn(n, "bz", 2), 3000)) * _exp(n, 0.02) * 0.4
    env = _pts(n, [(0, 0), (0.06, 1), (1.5, 0)]) ** 1.3
    whoosh = _swoosh(n, _xs(n, 1500, 450, 1.3), 700, "bz", 3) * env
    hiss = _nrms(_bp(_wn(n, "bz", 4), 3000, 9000)) * env
    x = thump * 1.0 + blast * 0.8 + whoosh * 0.55 + hiss * 0.18
    return _fin(np.tanh(1.8 * x), fout=0.1)


@sfx("laser")
def s_laser():
    n = _n(0.34)
    f = _xs(n, 2200, 280, 0.18)
    x = (_sqr(f, n) * 0.6 + _sin(f, n) * 0.4) * _ad(n, 0.001, 0.08)
    echo = np.zeros(n)
    _at(echo, x, 0.06, 0.3)
    _at(echo, x, 0.12, 0.12)
    return _fin(x + echo)


# =================================================================== explosions
def _boom(dur, key, f0, tau_roar, n_crackle, crackle_end):
    n = _n(dur)
    boom = _thump(n, f0, 24, tau_roar * 0.6, tau_roar, 0.004)
    bright = _nrms(_hp(_wn(n, key, 1), 800)) * _exp(n, 0.08)
    dark = _nrms(_lp(_wn(n, key, 2), 350)) * _ad(n, 0.01, tau_roar)
    mid = _nrms(_bp(_snh(n, 8, key, 3), 150, 2500)) * _exp(n, tau_roar * 0.4)
    x = boom * 1.0 + bright * 0.55 + dark * 1.0 + mid * 0.4
    r = _rng(key, "crackle")
    crk = np.zeros(n)
    for i in range(n_crackle):
        t0 = 0.12 + (crackle_end - 0.12) * r.beta(1.2, 2.2)
        k = _n(0.012)
        p = _nrms(_hp(_wn(k, key, "p", i), 2500)) * _exp(k, r.uniform(0.0015, 0.004))
        _at(crk, p, t0, r.exponential(0.5) * (1 - t0 / (crackle_end + 0.2)))
    return x, crk


@sfx("explosion")
def s_explosion():
    x, crk = _boom(1.9, "expl", 95, 0.55, 70, 1.6)
    x = np.tanh(2.2 * x) + crk * 0.35
    return _fin(x, fout=0.15)


@sfx("explosion_small")
def s_explosion_small():
    x, crk = _boom(0.85, "expls", 150, 0.2, 18, 0.65)
    x = np.tanh(2.0 * x) + crk * 0.3
    return _fin(x, fout=0.08)


@sfx("bomb_fuse")
def s_bomb_fuse():
    n = _n(2.0)
    hiss = _nrms(_bp(_wn(n, "fuse"), 2500, 10000))
    flick = 0.55 + 0.45 * np.abs(_lp(_snh(n, 400, "fuse", 2), 80)) / 0.7
    x = hiss * np.clip(flick, 0, 1.3) * 0.5
    r = _rng("fuse-pops")
    for i in range(42):
        k = _n(0.01)
        p = _nrms(_hp(_wn(k, "fp", i), 1500)) * _exp(k, 0.0015)
        _at(x, p, r.uniform(0, 1.95), r.uniform(0.3, 1.0))
    x *= _pts(n, [(0, 0), (0.04, 1), (1.9, 1), (2.0, 0)])
    return _fin(x, trim=False, fout=0.05)


@sfx("thunder")
def s_thunder():
    n = _n(3.4)
    t = _t(n)
    flick = np.clip(0.4 + 0.8 * np.abs(_snh(n, _n(0.018), "thu", 1)), 0, 1)
    crack = _nrms(_hp(_wn(n, "thu", 2), 1000)) * _ad(n, 0.002, 0.15) * flick
    rum_mod = 0.6 + 0.4 * _lp(_snh(n, _n(0.12), "thu", 3), 6) / 0.5
    rumble = _nrms(_lp(_wn(n, "thu", 4), 180)) * _pts(n, [(0, 0), (0.15, 0.6), (0.35, 1.0), (3.4, 0)]) ** 1.3 * rum_mod
    mid = _nrms(_lp(_wn(n, "thu", 5), 900)) * _ad(n, 0.01, 0.5)
    boom = _thump(n, 60, 30, 0.3, 0.6, 0.02)
    x = crack * 0.7 + rumble * 0.9 + mid * 0.35 + boom * 0.5
    return _fin(np.tanh(1.6 * x), fout=0.2)


# =================================================================== cartoon motion
@sfx("jump")
def s_jump():
    n = _n(0.22)
    x = _sqr(_xs(n, 240, 880, 0.16), n, 0.25) * _ad(n, 0.002, 0.09)
    return _fin(x)


@sfx("fly_away")
def s_fly_away():
    n = _n(1.8)
    t = _t(n)
    m = _n(0.25)
    x = np.zeros(n)
    _at(x, _swoosh(m, _xs(m, 600, 3200), 900, "fly") * np.sin(np.pi * _t(m) / 0.25) ** 2, 0.0, 0.3)
    depth = 0.012 + 0.03 * (t / 1.8)
    f = 600 * 4.6 ** np.clip(t / 1.6, 0, 1) * (1 + depth * np.sin(TAU * 8.5 * t))
    tone = _sin(f, n) * 0.8 + _tri(f, n) * 0.25
    env = _pts(n, [(0, 0), (0.06, 1), (0.5, 0.8), (1.78, 0)]) ** 1.5
    x += tone * env * 0.7
    return _fin(x, fout=0.05)


@sfx("twinkle")
def s_twinkle():
    x = _buf(1.1)
    t_all = _t(len(x))

    def ping(f, dur, tau, key):
        k = _n(dur)
        tt = _t(k)
        return (np.sin(TAU * f * tt) + 0.35 * np.sin(TAU * f * 2.0 * tt) + 0.12 * np.sin(TAU * f * 2.76 * tt)) \
            * _ad(k, 0.001, tau)

    _at(x, ping(2349.3, 0.8, 0.10, 1), 0.0, 0.8)      # ki
    _at(x, ping(3136.0, 1.0, 0.30, 2), 0.075, 1.0)    # ra~
    for i, (tt, f) in enumerate([(0.16, 2637.0), (0.22, 3951.1), (0.28, 3136.0), (0.34, 4698.6), (0.42, 5274.0)]):
        _at(x, ping(f, 0.5, 0.08, 10 + i), tt, 0.35 - 0.04 * i)
    shim = _nrms(_hp(_wn(len(x), "tw"), 6000)) * _pts(len(x), [(0, 0), (0.1, 1), (0.8, 0)])
    x += shim * 0.06
    x *= 0.8 + 0.2 * np.sin(TAU * 18 * t_all)
    return _fin(x, fout=0.08)


@sfx("fall_whistle")
def s_fall_whistle():
    n = _n(1.4)
    t = _t(n)
    f = _xs(n, 2400, 450, 1.35) * (1 + 0.01 * np.sin(TAU * 6 * t))
    x = (_sin(f, n) + _tri(f, n) * 0.15) * _pts(n, [(0, 0), (0.05, 0.9), (1.2, 1.0), (1.4, 0)])
    x += _nrms(_bp(_wn(n, "fw"), 2000, 6000)) * 0.02
    return _fin(x, peak=0.72, fout=0.06)


@sfx("boing")
def s_boing():
    n = _n(0.7)
    t = _t(n)
    base = 110 * (1 + 1.2 * (1 - np.exp(-t / 0.08)))
    f = base * (1 + 0.35 * np.sin(TAU * 14 * t) * np.exp(-t / 0.25))
    x = (_tri(f, n) * 0.7 + _sqr(f, n) * 0.3)
    x = _lp(x, 2500) * _ad(n, 0.003, 0.25)
    return _fin(x)


@sfx("slide_up")
def s_slide_up():
    return _slide(420, 1700, "su")


@sfx("slide_down")
def s_slide_down():
    return _slide(1700, 420, "sd")


def _slide(f0, f1, key):
    n = _n(0.6)
    t = _t(n)
    u = np.clip(t / 0.52, 0, 1)
    u = u * u * (3 - 2 * u)
    f = f0 * (f1 / f0) ** u * (1 + 0.015 * np.sin(TAU * 6 * t))
    x = _sin(f, n) + 0.08 * _sin(2 * f, n)
    x += _nrms(_hp(_wn(n, key), 2000)) * 0.05
    return _fin(x * _pts(n, [(0, 0), (0.02, 1), (0.54, 1), (0.6, 0)]), peak=0.72, trim=False, fout=0.02)


@sfx("pop")
def s_pop():
    n = _n(0.09)
    x = _sin(_xs(n, 350, 1500, 0.03), n) * _ad(n, 0.0005, 0.018)
    x += _nrms(_hp(_wn(n, "pop"), 2000)) * _exp(n, 0.0015) * 0.4
    return _fin(x, fout=0.01)


@sfx("squeak")
def s_squeak():
    n = _n(0.22)
    t = _t(n)
    f = np.interp(t, [0, 0.06, 0.22], [1300, 1900, 1600]) * (1 + 0.03 * np.sin(TAU * 30 * t))
    x = _bp(_sqr(f, n, 0.2), 1000, 5000)
    return _fin(x * _pts(n, [(0, 0), (0.01, 1), (0.17, 0.8), (0.22, 0)]), trim=False)


@sfx("record_scratch")
def s_record_scratch():
    """Vinyl scratch: a 'music' source read back-and-forth at varying speed."""
    ns = _n(1.5)
    src = sum(_saw(f, ns, os=1) for f in (110.0, 164.8, 220.0, 277.2)) * 0.3
    src += _nrms(_bp(_wn(ns, "rsc-src"), 300, 3000)) * 0.6
    n = _n(0.42)
    t = _t(n)
    rate = np.zeros(n)
    for t0, t1, pk in ((0.0, 0.13, 4.0), (0.15, 0.30, -5.0), (0.31, 0.40, 3.0)):
        m = (t >= t0) & (t < t1)
        rate[m] += pk * np.sin(np.pi * (t[m] - t0) / (t1 - t0))
    pos = 0.7 * SR + np.cumsum(rate)
    y = np.interp(pos, np.arange(ns), src)
    y *= np.clip(np.abs(rate) / 3.0, 0, 1) ** 0.6
    return _fin(_bp(y, 300, 6000))


# =================================================================== mouth / body
@sfx("chomp")
def s_chomp():
    x = _buf(0.4)
    k = _n(0.35)
    _at(x, _thump(k, 190, 60, 0.03, 0.06), 0.0, 0.9)
    teeth = _nrms(_hp(_wn(_n(0.01), "chomp", 1), 2500)) * _exp(_n(0.01), 0.0015)
    _at(x, teeth, 0.0, 0.8)
    for i, (t0, g) in enumerate([(0.0, 1.0), (0.035, 0.8), (0.08, 0.6), (0.13, 0.35)]):
        m = _n(0.06)
        c = _nrms(_bp(_snh(m, 3, "chomp", i), 800, 6000)) * _ad(m, 0.001, 0.012)
        _at(x, c, t0, g * 0.8)
    return _fin(np.tanh(1.5 * x))


@sfx("gulp")
def s_gulp():
    x = _buf(0.36)
    m = _n(0.07)
    _at(x, _sin(_xs(m, 700, 250), m) * _ad(m, 0.002, 0.025), 0.0, 0.6)
    k = _n(0.2)
    f = _xs(k, 180, 440, 0.09)
    bl = (_sin(f, k) + 0.3 * _sin(2 * f, k)) * np.sin(np.pi * np.clip(_t(k) / 0.14, 0, 1)) ** 1.5
    _at(x, _lp(bl, 1500), 0.08, 1.0)
    click = _nrms(_bp(_wn(_n(0.01), "gulp"), 800, 3000)) * _exp(_n(0.01), 0.002)
    _at(x, click, 0.075, 0.3)
    return _fin(x)


@sfx("cough")
def s_cough():
    x = _buf(0.8)
    for i, (t0, g) in enumerate([(0.0, 1.0), (0.27, 0.8), (0.5, 0.45)]):
        k = _n(0.25)
        nz = _wn(k, "cough", i)
        s = _nrms(_bp(nz, 400, 900)) + _nrms(_bp(nz, 1200, 2500)) * 0.6
        s += _lp(_saw(150 - 10 * i, k, os=1), 1000) * 0.4
        s *= _pts(k, [(0, 0), (0.008, 1), (0.05, 0.6), (0.2, 0), (1, 0)])
        _at(x, s, t0, g)
    return _fin(np.tanh(1.2 * x))


@sfx("bark")
def s_bark():
    n = _n(0.46)
    t = _t(n)
    f0 = np.interp(t, [0, 0.03, 0.3], [150, 195, 110])
    v = _saw(f0, n) * (1 + 0.3 * np.sin(TAU * 37 * t))
    voice = _bp(v, 380, 750) * 1.0 + _bp(v, 950, 1500) * 0.6 + _bp(v, 2200, 3100) * 0.2
    voice = _nrms(voice)
    attack = _nrms(_bp(_wn(n, "bark"), 500, 3000)) * _exp(n, 0.02)
    sub = _thump(n, 120, 70, 0.05, 0.08)
    env = _pts(n, [(0, 0), (0.012, 1), (0.1, 0.85), (0.3, 0.12), (0.44, 0)])
    x = voice * env + attack * 0.4 + sub * 0.4
    return _fin(np.tanh(1.6 * x))


def _caw(dur, f0, f1, key):
    n = _n(dur)
    t = _t(n)
    f = np.interp(t, [0, 0.04, dur], [f0 * 1.06, f0, f1])
    src = _sqr(f, n, 0.35) * 0.7 + _wn(n, "caw", key) * 0.5
    src *= 0.7 + 0.3 * np.sin(TAU * 55 * t)
    y = _bp(src, 700, 1300) + _bp(src, 1600, 2600) * 0.8 + _bp(src, 3000, 4000) * 0.2
    return _nrms(y) * _pts(n, [(0, 0), (0.03, 1), (dur * 0.6, 0.8), (dur, 0)])


@sfx("crow")
def s_crow():
    x = _buf(1.9)
    _at(x, _caw(0.38, 620, 470, 1), 0.0, 1.0)
    _at(x, _caw(0.42, 580, 420, 2), 0.78, 0.8)
    echo = np.zeros(len(x))
    _at(echo, x, 0.18, 0.25)
    _at(echo, x, 0.36, 0.1)
    return _fin(x + _lp(echo, 2000), fout=0.05)


@sfx("sweat")
def s_sweat():
    x = _buf(0.5)
    m = _n(0.12)
    _at(x, _sin(_xs(m, 900, 2200, 0.03), m) * _ad(m, 0.0008, 0.04), 0.0, 1.0)
    k = _n(0.32)
    tt = _t(k)
    f = _xs(k, 1400, 700, 0.3)
    _at(x, (_sin(f, k) + 0.3 * _tri(f, k)) * np.clip(tt / 0.03, 0, 1) * (1 - tt / 0.32) ** 2, 0.08, 0.3)
    return _fin(x)


@sfx("vein")
def s_vein():
    x = _buf(0.2)
    m = _n(0.06)
    _at(x, _sqr(_xs(m, 800, 2600, 0.02), m) * _ad(m, 0.0005, 0.02), 0.0, 0.8)
    _at(x, _sqr(_xs(m, 2400, 3600, 0.015), m) * _ad(m, 0.0005, 0.015), 0.05, 0.6)
    k = _n(0.1)
    _at(x, _thump(k, 250, 120, 0.01, 0.02), 0.0, 0.5)
    _at(x, _nrms(_hp(_wn(_n(0.008), "vein"), 2000)) * _exp(_n(0.008), 0.0015), 0.0, 0.5)
    return _fin(x)


@sfx("dizzy")
def s_dizzy():
    n = _n(1.45)
    x = np.zeros(n)
    k = _n(0.09)
    tt = _t(k)
    fch = np.interp(tt, [0, 0.03, 0.09], [2500, 3600, 2400])
    chirp = _tri(fch, k) * np.sin(np.pi * tt / 0.09)
    for i, t0 in enumerate([0.0, 0.11, 0.45, 0.56, 0.9, 1.01]):
        _at(x, chirp, t0, 0.9 if i % 2 == 0 else 0.7)
    t = _t(n)
    x += _tri(300 + 60 * np.sin(TAU * 3 * t), n) * 0.05
    x *= _pts(n, [(0, 1), (1.0, 0.8), (1.45, 0)])
    return _fin(_lp(x, 7000), fout=0.05)


# =================================================================== reactions / stingers
@sfx("shock")
def s_shock():
    n = _n(1.15)
    t = _t(n)
    hit = _thump(n, 130, 45, 0.04, 0.25) + _nrms(_bp(_wn(n, "shock"), 500, 5000)) * _exp(n, 0.02) * 0.5
    bend = 1 - 0.03 * np.clip((t - 0.25) / 0.8, 0, 1)
    chord = sum(_saw(freq(m) * bend, n) for m in ("C3", "F#3", "B3", "F4"))
    chord = _lp(chord, 900) + (chord - _lp(chord, 900)) * _exp(n, 0.08)
    chord *= _ad(n, 0.004, 0.5)
    zing = _sin(2093.0 * bend, n) * (0.6 + 0.4 * np.sin(TAU * 20 * t)) * _ad(n, 0.01, 0.35)
    x = hit * 0.8 + _nrms(chord) * 0.6 + zing * 0.18
    return _fin(np.tanh(1.6 * x), fout=0.08)


def _pinghi(f, dur, tau):
    k = _n(dur)
    tt = _t(k)
    return (np.sin(TAU * f * tt) + 0.3 * np.sin(TAU * 2 * f * tt)) * _ad(k, 0.001, tau)


@sfx("sparkle")
def s_sparkle():
    x = _buf(0.95)
    r = _rng("sparkle")
    notes = [freq(m) for m in ("C7", "D7", "E7", "G7", "A7", "C8")]
    times = np.sort(r.uniform(0, 0.62, 22))
    for i, t0 in enumerate(times):
        f = notes[r.integers(len(notes))] * r.uniform(0.995, 1.005)
        _at(x, _pinghi(f, 0.3, r.uniform(0.05, 0.14)), t0, r.uniform(0.4, 1.0) * (1 - t0 / 1.0))
    x += _nrms(_hp(_wn(len(x), "sp"), 7000)) * _pts(len(x), [(0, 0), (0.1, 1), (0.75, 0)]) * 0.08
    return _fin(x, fout=0.06)


@sfx("rimshot")
def s_rimshot():
    x = _buf(1.45)

    def tom(f0):
        k = _n(0.45)
        return _thump(k, f0 * 1.5, f0, 0.02, 0.12) + _nrms(_bp(_wn(k, "tom", f0), 200, 2000)) * _exp(k, 0.03) * 0.3

    k = _n(0.45)
    snare = _nrms(_bp(_wn(k, "rs", 1), 1000, 6000)) * _exp(k, 0.07) + _tri(190, k) * _exp(k, 0.05) * 0.5
    _at(x, snare * 0.8 + tom(175) * 0.6, 0.0)
    _at(x, tom(130), 0.17, 0.9)
    k = _n(1.05)
    cym = _nrms(_hp(_wn(k, "rs", 2), 5000)) * _ad(k, 0.002, 0.35) + _nrms(_bp(_wn(k, "rs", 3), 3000, 9000)) * _exp(k, 0.6) * 0.3
    kick = _thump(k, 120, 45, 0.03, 0.12)
    snare2 = _nrms(_bp(_wn(k, "rs", 4), 1000, 6000)) * _exp(k, 0.06)
    _at(x, cym * 0.6 + kick * 0.8 + snare2 * 0.5, 0.40)
    return _fin(np.tanh(1.2 * x), fout=0.1)


def _xylo(f, dur=0.35, tau=0.08):
    k = _n(dur)
    tt = _t(k)
    return (np.sin(TAU * f * tt) + 0.3 * np.sin(TAU * 3.93 * f * tt) * np.exp(-tt / 0.02)) * _ad(k, 0.0008, tau)


@sfx("sting_comedy")
def s_sting_comedy():
    x = _buf(1.1)
    for i, m in enumerate(("C6", "G5", "E5", "C5")):
        _at(x, _xylo(freq(m)), i * 0.075, 0.7)
    k = _n(0.75)
    t = _t(k)
    base = 82 * (1 + 0.9 * (1 - np.exp(-t / 0.06)))
    f = base * (1 + 0.25 * np.sin(TAU * 11 * t) * np.exp(-t / 0.3))
    b = _lp(_tri(f, k) * 0.6 + _sqr(f, k) * 0.4, 1800) * _ad(k, 0.004, 0.3)
    _at(x, b, 0.32, 1.0)
    return _fin(x, fout=0.06)


def _brassy(freqs, n, bright_tau=0.08, cutoff=900):
    ch = sum(_saw(f, n) + 0.6 * _saw(f * 1.003, n) for f in freqs)
    return _lp(ch, cutoff) + (ch - _lp(ch, cutoff)) * _exp(n, bright_tau)


@sfx("sting_dramatic")
def s_sting_dramatic():
    x = _buf(2.7)

    def timp(f, dur, g):
        k = _n(dur)
        return (_thump(k, f * 1.25, f, 0.02, 0.4) + _nrms(_lp(_wn(k, "timp", f), 600)) * _exp(k, 0.05) * 0.4) * g

    cm = [freq(m) for m in ("C3", "Eb3", "G3", "C4")]
    for t0 in (0.0, 0.32):
        k = _n(0.3)
        s = _nrms(_brassy(cm, k)) * _pts(k, [(0, 0), (0.008, 1), (0.2, 0.7), (0.3, 0)])
        _at(x, s, t0, 0.7)
        _at(x, timp(65.4, 0.3, 0.8), t0)
    k = _n(1.95)
    tt = _t(k)
    fin = [freq(m) for m in ("B2", "D3", "F3", "Ab3", "B3")]
    s = _nrms(_brassy(fin, k, 0.2, 1100)) * _ad(k, 0.01, 0.9) * (0.85 + 0.15 * np.sin(TAU * 9 * tt))
    _at(x, s, 0.72, 1.0)
    _at(x, timp(61.7, 1.4, 1.1), 0.72)
    cym = _nrms(_hp(_wn(k, "sd", 1), 4000)) * _ad(k, 0.003, 0.6)
    _at(x, cym, 0.72, 0.3)
    return _fin(np.tanh(1.4 * x), fout=0.15)


@sfx("fail")
def s_fail():
    """Sad trombone: wah-wah-wah-waaaah (additive brass with a 'wah' mute)."""
    notes = [("D4", 0.40), ("C#4", 0.40), ("C4", 0.40), ("B3", 1.45)]
    x = _buf(2.9)
    pos = 0.0
    for i, (m, dur) in enumerate(notes):
        k = _n(dur)
        tt = _t(k)
        f0 = freq(m)
        scoop = 1 - 0.025 * np.exp(-tt / 0.04)
        vib = 1 + (0.025 * np.clip((tt - 0.25) / 0.6, 0, 1) * np.sin(TAU * 5.5 * tt) if i == 3 else 0)
        f = f0 * scoop * vib
        if i < 3:
            bright = 0.25 + 0.7 * np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 1.2
            env = _pts(k, [(0, 0), (0.03, 1), (dur - 0.06, 0.9), (dur, 0)])
        else:
            bright = np.interp(tt, [0, 0.12, dur], [0.3, 0.95, 0.15])
            env = _pts(k, [(0, 0), (0.03, 1), (0.5, 0.95), (dur, 0)])
        ph = _cyc(f, k)
        tone = np.zeros(k)
        for h in range(1, 18):
            if h * f0 > 12000:
                break
            tone += np.sin(TAU * h * ph) / h * np.exp(-(h - 1) * (1.15 - bright) * 0.9)
        breath = _nrms(_bp(_wn(k, "fail", i), 500, 2000)) * 0.03
        _at(x, (tone + breath) * env, pos, 1.0 if i < 3 else 1.1)
        pos += dur + 0.03
    return _fin(x, fout=0.08)


@sfx("fanfare")
def s_fanfare():
    """Short original victory jingle (chiptune: 2 pulses + triangle bass + drums)."""
    tr = 0.125
    lead = [("G4", 0, tr), ("C5", tr, tr), ("E5", 2 * tr, tr), ("G5", 3 * tr, 0.36),
            ("E5", 0.75, 0.17), ("G5", 0.9375, 0.17), ("C6", 1.125, 0.95)]
    harm = [("E4", 0, tr), ("G4", tr, tr), ("C5", 2 * tr, tr), ("E5", 3 * tr, 0.36),
            ("C5", 0.75, 0.17), ("E5", 0.9375, 0.17), ("G5", 1.125, 0.95)]
    bass = [("C3", 0, 0.36), ("G2", 3 * tr, 0.36), ("F2", 0.75, 0.36), ("C3", 1.125, 0.9)]
    x = _buf(2.35)

    def note(m, dur, duty, g, vib=False, kind="sqr"):
        k = _n(dur)
        tt = _t(k)
        f = freq(m) * (1 + (0.012 * np.clip((tt - 0.2) / 0.3, 0, 1) * np.sin(TAU * 6 * tt) if vib else 0))
        w = _sqr(f, k, duty) if kind == "sqr" else _tri(f, k)
        return w * _pts(k, [(0, 0), (0.004, 1), (0.06, 0.75), (dur - 0.04, 0.65), (dur, 0)]) * g

    for m, t0, d in lead:
        _at(x, note(m, d, 0.5, 0.45, d > 0.5), t0)
    for m, t0, d in harm:
        _at(x, note(m, d, 0.25, 0.25, d > 0.5), t0)
    for m, t0, d in bass:
        _at(x, note(m, d, 0.5, 0.6, False, "tri"), t0)
    for t0, g in ((3 * tr, 0.6), (0.75, 0.4), (0.9375, 0.4), (1.125, 0.8)):
        k = _n(0.2)
        sn = _nrms(_bp(_snh(k, 3, "ff", t0), 1000, 7000)) * _exp(k, 0.05) + _thump(k, 140, 50, 0.03, 0.08)
        _at(x, sn, t0, 0.25 * g)
    k = _n(1.1)
    _at(x, _nrms(_hp(_wn(k, "ff", "cym"), 4500)) * _ad(k, 0.002, 0.45), 1.125, 0.18)
    return _fin(_lp(x, 9000), fout=0.12)


@sfx("title_hit")
def s_title_hit():
    """Massive logo slam: sub boom + taiko + brass chord stab + crash + rising shimmer (stereo)."""
    n = _n(2.4)
    t = _t(n)
    sub = _thump(n, 82, 30, 0.25, 0.6, 0.002)
    taiko = _thump(n, 160, 70, 0.03, 0.2) + _nrms(_lp(_wn(n, "th", 1), 1500)) * _exp(n, 0.03) * 0.6
    chord_f = [freq(m) for m in ("C2", "G2", "C3", "E3", "G3", "C4")]
    stab = sum(_saw(f, n) + 0.5 * _sqr(f * 1.004, n, 0.25) for f in chord_f)
    stab = _lp(stab, 800) + (stab - _lp(stab, 800)) * _exp(n, 0.15)
    stab = _nrms(stab) * _ad(n, 0.004, 0.8)
    mono = np.tanh(1.5 * (sub * 1.0 + taiko * 0.7 + stab * 0.7))
    out = np.stack([mono, mono], 1)
    for c in range(2):
        crash = _nrms(_hp(_wn(n, "th", "cr", c), 3500)) * _ad(n, 0.002, 0.7)
        crash += _nrms(_bp(_wn(n, "th", "cr2", c), 6000, 12000)) * _exp(n, 1.2) * 0.3
        out[:, c] += crash * 0.35
    notes = [freq(m) for m in ("C6", "E6", "G6", "C7", "E7", "G7", "C8")]
    for i, f in enumerate(notes):
        p = _pinghi(f, 0.9, 0.35)
        c = i % 2
        tmp = np.zeros(n)
        _at(tmp, p, 0.15 + i * 0.2, 0.22 - 0.015 * i)
        out[:, c] += tmp
        out[:, 1 - c] += tmp * 0.45
    return _fin(out, fout=0.2)


# =================================================================== bells / chimes / money
@sfx("bell")
def s_bell():
    """Bright rin/altar bell 'chiiin' (also great as a comedic 'chiin')."""
    n = _n(2.8)
    f0 = 1180.0
    ratios = [1.0, 1.0022, 2.71, 2.715, 5.15, 8.2]
    amps = [1.0, 0.45, 0.5, 0.25, 0.25, 0.1]
    taus = [1.6, 1.6, 0.9, 0.9, 0.4, 0.2]
    x = _ring(n, [f0 * r for r in ratios], amps, taus, key=("bell",))
    x += _nrms(_hp(_wn(n, "bell"), 3000)) * _exp(n, 0.003) * 0.3
    return _fin(x, fout=0.25, trim=False)


@sfx("gong")
def s_gong():
    """Deep temple bell 'gooon' with slow beating."""
    n = _n(3.6)
    f0 = 98.0
    ratios = [1.0, 1.007, 2.02, 2.76, 2.77, 3.4, 4.1, 5.3, 6.5]
    amps = [1.0, 0.9, 0.6, 0.5, 0.45, 0.35, 0.25, 0.15, 0.1]
    taus = [2.5, 2.5, 1.8, 1.4, 1.4, 1.0, 0.8, 0.5, 0.35]
    x = _ring(n, [f0 * r for r in ratios], amps, taus, a=0.004, key=("gong",))
    x += _thump(n, 90, 60, 0.02, 0.06) * 0.6
    x += _nrms(_lp(_wn(n, "gong"), 900)) * _exp(n, 0.02) * 0.3
    return _fin(np.tanh(1.3 * x), fout=0.3, trim=False)


@sfx("bell_shop")
def s_bell_shop():
    """Shop-entrance bells 'karan-koron'."""
    x = _buf(1.3)
    bells = [(1760.0, [1, 2.4, 3.9]), (2217.0, [1, 2.35, 3.8])]
    for i, (t0, b, g) in enumerate([(0.0, 0, 1.0), (0.11, 1, 0.85), (0.25, 0, 0.6), (0.42, 1, 0.4)]):
        f, rr = bells[b]
        k = _n(0.85)
        _at(x, _ring(k, [f * r for r in rr], [1, .4, .2], [.35, .15, .08], key=("bs", i)), t0, g)
    return _fin(x, fout=0.1)


@sfx("coin")
def s_coin():
    x = _buf(0.5)
    k1 = _n(0.075)
    _at(x, _sqr(987.77, k1) * _pts(k1, [(0, 0), (0.002, 1), (0.075, 0.9)]), 0.0, 0.6)
    k2 = _n(0.42)
    _at(x, _sqr(1318.5, k2) * _ad(k2, 0.001, 0.14), 0.07, 0.6)
    return _fin(_lp(x, 9000), fout=0.03)


@sfx("cash")
def s_cash():
    x = _buf(1.2)
    for i, t0 in enumerate((0.0, 0.028, 0.055)):
        k = _n(0.02)
        _at(x, _nrms(_hp(_wn(k, "cash", i), 1500)) * _exp(k, 0.003), t0, 0.6)
    m = _n(0.18)
    slide = _nrms(_bp(_snh(m, 5, "cash", 9), 600, 3000)) * np.sin(np.pi * _t(m) / 0.18)
    _at(x, slide, 0.08, 0.25)
    k = _n(1.0)
    ding = _ring(k, [2350, 2353, 4700, 6480], [1, .35, .3, .2], [.5, .5, .3, .15], key=("cash",))
    _at(x, ding, 0.12, 0.8)
    _at(x, _thump(_n(0.1), 200, 100, 0.01, 0.02), 0.26, 0.4)
    return _fin(x, fout=0.1)


@sfx("shine")
def s_shine():
    """Holy chime pad for sunlight (stereo, wide, Cmaj9 + sparkles)."""
    n = _n(3.2)
    t = _t(n)
    env = _pts(n, [(0, 0), (0.7, 1), (2.2, 0.75), (3.2, 0)])
    env = np.sin(np.pi / 2 * env) ** 2
    out = np.zeros((n, 2))
    chord = [freq(m) for m in ("C5", "E5", "G5", "B5", "D6", "G6")]
    for i, f in enumerate(chord):
        for c, det in ((0, -0.6), (1, 0.6)):
            out[:, c] += (np.sin(TAU * (f + det) * t + i) + 0.2 * np.sin(TAU * 2 * (f + det) * t)) / (1 + 0.15 * i)
    out *= env[:, None] * 0.25
    r = _rng("shine")
    notes = [freq(m) for m in ("C7", "E7", "G7", "B7", "D7")]
    for i in range(18):
        t0 = r.uniform(0.3, 2.5)
        p = _pinghi(notes[r.integers(len(notes))], 0.5, r.uniform(0.08, 0.2))
        pan = r.uniform(0, 1)
        tmp = np.zeros(n)
        _at(tmp, p, t0, 0.18)
        out[:, 0] += tmp * (1 - pan)
        out[:, 1] += tmp * pan
    for c in range(2):
        out[:, c] += _nrms(_hp(_wn(n, "shine", c), 6000)) * env * 0.03
    return _fin(out, fout=0.2, trim=False)


@sfx("aura")
def s_aura():
    n = _n(1.95)
    t = _t(n)
    rise = np.clip(t / 1.6, 0, 1)
    env = rise ** 1.5 * np.where(t < 1.6, 1.0, np.exp(-(t - 1.6) / 0.08))
    whoosh = _swoosh(n, _xs(n, 200, 3500, 1.6), 1200, "aura")
    rate = 6 + 22 * rise
    trem = 0.6 + 0.4 * np.sin(TAU * _cyc(rate, n))
    buzz = _lp(_saw(_xs(n, 70, 280, 1.6), n), 1800) * trem
    sub = _sin(_xs(n, 45, 90, 1.6), n)
    x = (whoosh * 0.6 + buzz * 0.5 + sub * 0.3) * env
    k = _n(0.35)
    burst = _nrms(_hp(_wn(k, "aura", 2), 2000)) * _exp(k, 0.08)
    _at(x, burst, 1.58, 0.35)
    return _fin(x, fout=0.05)


@sfx("charge")
def s_charge():
    n = _n(1.4)
    t = _t(n)
    f = _xs(n, 180, 1400, 1.25)
    rate = np.interp(t, [0, 1.25], [8, 40])
    trem = 0.55 + 0.45 * np.sin(TAU * _cyc(rate, n))
    x = (_sqr(f, n, 0.25) * 0.45 + _sin(f * 0.5, n) * 0.4) * trem
    x += _nrms(_hp(_wn(n, "charge"), 5000)) * np.clip(t / 1.25, 0, 1) ** 2 * 0.15
    env = np.clip(t / 1.25, 0, 1) ** 0.7 * np.where(t < 1.25, 1.0, np.exp(-(t - 1.25) / 0.04))
    return _fin(x * env, fout=0.03)


# =================================================================== crowd one-shots
def _voices(n, count, key, lo, hi, glide=0.0, vib=(4.5, 7.0), onset=0.25, os=1, rel=None):
    """Sum of voiced saw 'people' (pitch contours) -> (sumL, sumR)."""
    r = _rng("voices", key)
    t = _t(n)
    L = np.zeros(n)
    R = np.zeros(n)
    for i in range(count):
        f0 = r.uniform(lo, hi)
        vr = r.uniform(*vib)
        f = f0 * (1 + glide * (1 - np.exp(-t / r.uniform(0.08, 0.2)))) * (1 + 0.02 * np.sin(TAU * vr * t + r.uniform(0, 6)))
        v = _saw(f, n, os=os)
        o = r.uniform(0, onset)
        e = np.clip((t - o) / 0.08, 0, 1)
        if rel is not None:
            end = r.uniform(*rel)
            e *= np.clip((end - t) / 0.35, 0, 1)
        v *= e * r.uniform(0.5, 1.0)
        pan = r.uniform(0.15, 0.85)
        L += v * (1 - pan)
        R += v * pan
    return L, R


def _vowel_a(x):
    return _bp(x, 650, 1100) * 1.0 + _bp(x, 1150, 1800) * 0.6 + _bp(x, 2400, 3200) * 0.25


@sfx("cheer")
def s_cheer():
    n = _n(2.4)
    L, R = _voices(n, 28, "cheer", 140, 420, glide=0.18, onset=0.25, rel=(1.4, 2.1))
    out = np.zeros((n, 2))
    env = _pts(n, [(0, 0), (0.15, 1), (1.3, 0.9), (2.4, 0)])
    for c, v in enumerate((L, R)):
        y = _nrms(_vowel_a(v)) + _nrms(_bp(_wn(n, "cheer", c), 400, 4000)) * 0.35
        out[:, c] = y * env
    r = _rng("cheer-whistle")
    for i in range(2):
        k = _n(0.45)
        f = np.interp(_t(k), [0, 0.1, 0.45], [2200, 2900, 2600])
        w = _sin(f, k) * _pts(k, [(0, 0), (0.03, 1), (0.35, 0.8), (0.45, 0)]) * 0.12
        tmp = np.zeros(n)
        _at(tmp, w, r.uniform(0.3, 1.1))
        out[:, i] += tmp
    return _fin(out, fout=0.1)


@sfx("applause")
def s_applause():
    n = _n(3.0)
    env = _pts(n, [(0, 0), (0.25, 1), (2.0, 0.85), (3.0, 0)])
    out = np.zeros((n, 2))
    for c in range(2):
        r = _rng("clap", c)
        acc = np.zeros(n)
        for kk in range(4):
            imp = np.zeros(n)
            cnt = 45 * 3
            pos = r.integers(0, n, cnt)
            imp[pos] += r.uniform(0.3, 1.0, cnt)
            m = _n(0.03)
            lo = 700 + 400 * kk
            kern = _nrms(_bp(_wn(m, "clapk", c, kk), lo, lo * 4.5)) * _exp(m, r.uniform(0.004, 0.007))
            acc += fftconvolve(imp, kern)[:n]
        out[:, c] = acc * env
    return _fin(np.tanh(1.8 * _norm(out)), fout=0.15)


# =================================================================== LOOPS
def _dur_loop(sec):
    return _n(sec)


@sfx("rain", loop=True)
def s_rain():
    L = _dur_loop(4.0)
    out = np.zeros((L, 2))
    for c in range(2):
        w = _wn(L, "rain", c)
        bed = _nrms(_cf(lambda x: _bp(x, 400, 7000), w))
        rum = _nrms(_cf(lambda x: _lp(x, 300), _wn(L, "rain", "r", c))) * 0.35
        hiss = _nrms(_cf(lambda x: _hp(x, 5000), _wn(L, "rain", "h", c))) * 0.2
        mod = _pmod(L, 12, "rain", "m", c, lo=0.8, hi=1.0)
        r = _rng("rain-drops", c)
        imp = np.zeros(L)
        cnt = int(4.0 * 70)
        imp[r.integers(0, L, cnt)] += r.exponential(0.4, cnt)
        kern = _ring(_n(0.02), [3300 + 400 * c], [1.0], [0.003], key=("rk", c)) + _nrms(_hp(_wn(_n(0.02), "rk", c), 2000)) * _exp(_n(0.02), 0.002)
        drops = _cconv(imp, kern)
        imp2 = np.zeros(L)
        cnt2 = int(4.0 * 8)
        imp2[r.integers(0, L, cnt2)] += r.uniform(0.5, 1.0, cnt2)
        k2 = _nrms(_bp(_wn(_n(0.05), "rs", c), 1000, 4000)) * _exp(_n(0.05), 0.01)
        splash = _cconv(imp2, k2)
        out[:, c] = (bed + rum + hiss) * mod + _nrms(drops) * 0.12 + _nrms(splash) * 0.1
    return _lfin(out)


@sfx("wind", loop=True)
def s_wind():
    L = _dur_loop(6.0)
    out = np.zeros((L, 2))
    for c in range(2):
        fc = _pmod(L, 6, "wind", "f", c, lo=350, hi=900)
        base = _nrms(_cf(lambda x: _lp(x, 220, 2), _wn(L, "wind", c)), 0.35)
        car = np.cos(TAU * _cyc(_pfreq(fc), L))
        band = base * car
        low = _nrms(_cf(lambda x: _lp(x, 400), _wn(L, "wind", "l", c))) * 0.6
        gust = _pmod(L, 5, "wind", "g", c, lo=0.35, hi=1.0)
        wf = _pfreq(_pmod(L, 4, "wind", "wf", c, lo=850, hi=1250))
        whistle = np.sin(TAU * _cyc(wf, L)) * gust ** 3 * 0.05
        out[:, c] = (band * 1.0 + low) * gust + whistle
    return _lfin(np.tanh(1.4 * _norm(out)))


def _pvoices(L, count, key, lo, hi, rate, pause_rate, vowel_fns, loud=(0.5, 1.0)):
    """Periodic babbling voices for loops -> (L, 2)."""
    r = _rng("pv", key)
    groups = [[np.zeros(L), np.zeros(L)] for _ in vowel_fns]
    for i in range(count):
        f0 = r.uniform(lo, hi)
        contour = _pmod(L, max(3, int(L / SR * 2)), "pv", key, i, "f", lo=0.85, hi=1.15)
        f = _pfreq(f0 * contour)
        v = 2.0 * (_cyc(f, L) % 1.0) - 1.0
        syl = np.clip(_pmod(L, int(L / SR * rate), "pv", key, i, "s", lo=-0.6, hi=1.2), 0, 1) ** 1.5
        talk = np.clip(_pmod(L, max(2, int(L / SR * pause_rate)), "pv", key, i, "p", lo=-0.3, hi=1.3), 0, 1)
        v *= syl * talk * r.uniform(*loud)
        pan = r.uniform(0.1, 0.9)
        g = groups[r.integers(len(vowel_fns))]
        g[0] += v * (1 - pan)
        g[1] += v * pan
    out = np.zeros((L, 2))
    for (gl, gr), fn in zip(groups, vowel_fns):
        out[:, 0] += _cf(fn, gl)
        out[:, 1] += _cf(fn, gr)
    return out


_VOWELS = [
    lambda x: _bp(x, 600, 1100) + _bp(x, 1100, 1700) * 0.6,       # a
    lambda x: _bp(x, 350, 650) + _bp(x, 1900, 2600) * 0.5,        # i/e
    lambda x: _bp(x, 380, 750) + _bp(x, 750, 1100) * 0.6,         # o/u
]


@sfx("crowd", loop=True)
def s_crowd():
    L = _dur_loop(5.0)
    v = _pvoices(L, 22, "crowd", 100, 280, 4.5, 0.6, _VOWELS)
    out = np.zeros((L, 2))
    for c in range(2):
        out[:, c] = _nrms(v[:, c])
        mod = _pmod(L, 10, "crowd", "n", c, lo=0.6, hi=1.0)
        out[:, c] += _nrms(_cf(lambda x: _bp(x, 300, 3000), _wn(L, "crowd", c))) * 0.3 * mod
        out[:, c] = _cf(lambda x: _lp(x, 2800), out[:, c])
    return _lfin(out)


@sfx("fire", loop=True)
def s_fire():
    L = _dur_loop(4.0)
    out = np.zeros((L, 2))
    for c in range(2):
        roar = _nrms(_cf(lambda x: _lp(x, 500), _wn(L, "fire", c))) * _pmod(L, 12, "fire", "m", c, lo=0.6, hi=1.0)
        hiss = _nrms(_cf(lambda x: _bp(x, 1000, 4000), _wn(L, "fire", "h", c))) * _pmod(L, 30, "fire", "hm", c, lo=0.2, hi=1.0) * 0.15
        r = _rng("fire-crackle", c)
        imp = np.zeros(L)
        cnt = int(4.0 * 28)
        imp[r.integers(0, L, cnt)] += np.minimum(r.pareto(2.5, cnt) + 0.3, 1.6)
        m = _n(0.006)
        k = _nrms(_hp(_wn(m, "fk", c), 1500)) * _exp(m, 0.0012)
        crk = _cconv(imp, k)
        imp2 = np.zeros(L)
        cnt2 = int(4.0 * 3)
        imp2[r.integers(0, L, cnt2)] += r.uniform(0.6, 1.0, cnt2)
        m2 = _n(0.04)
        k2 = _nrms(_bp(_wn(m2, "fp", c), 400, 1500)) * _exp(m2, 0.008)
        pops = _cconv(imp2, k2)
        out[:, c] = roar * 0.8 + hiss * 1.3 + _nrms(crk) * 0.3 + _nrms(pops) * 0.2
    return _lfin(np.tanh(1.6 * _norm(out)))


@sfx("river", loop=True)
def s_river():
    L = _dur_loop(5.0)
    out = np.zeros((L, 2))
    for c in range(2):
        bed = _nrms(_cf(lambda x: _bp(x, 200, 2500), _wn(L, "river", c))) * _pmod(L, 40, "river", "m", c, lo=0.6, hi=1.0)
        low = _nrms(_cf(lambda x: _lp(x, 150), _wn(L, "river", "l", c))) * 0.3
        bub = np.zeros(L)
        r = _rng("river-bub", c)
        for i in range(220):
            k = _n(0.03)
            f0 = r.uniform(400, 1400)
            tt = _t(k)
            b = np.sin(TAU * _cyc(f0 * (1 + 1.5 * tt / 0.02), k)) * _ad(k, 0.001, r.uniform(0.006, 0.018))
            _atw(bub, b, r.uniform(0, 5.0), r.uniform(0.2, 1.0))
        out[:, c] = bed * 0.6 + low + _nrms(bub) * 0.22
    return _lfin(out)


@sfx("night", loop=True)
def s_night():
    L = _dur_loop(4.0)
    out = np.zeros((L, 2))
    crickets = [  # carrier Hz, chirp period s, pan, gain, pulses
        (4200.0, 0.5, 0.2, 1.0, 3),
        (4700.0, 0.8, 0.8, 0.8, 4),
        (5100.0, 4.0 / 6, 0.5, 0.45, 3),
    ]
    t = _t(L)
    for j, (fc, per, pan, g, pulses) in enumerate(crickets):
        gate = np.zeros(L)
        pk = _n(0.016)
        pulse = np.hanning(pk)
        for i in range(int(round(4.0 / per))):
            for p in range(pulses):
                _atw(gate, pulse, 0.07 * j + i * per + p * 0.024, 1.0 - 0.1 * p)
        car = np.sin(TAU * fc * t) * (1 + 0.15 * np.sin(TAU * 2 * fc * t))
        s = car * gate * g
        if j == 2:
            s = _cf(lambda x: _lp(x, 4500), s)
        out[:, 0] += s * (1 - pan)
        out[:, 1] += s * pan
    for c in range(2):
        out[:, c] += _nrms(_cf(lambda x: _lp(x, 700), _wn(L, "night", c))) * 0.06 * _pmod(L, 4, "night", c, lo=0.5, hi=1.0)
    return _lfin(out)


@sfx("battle", loop=True)
def s_battle():
    L = _dur_loop(6.0)
    v = _pvoices(L, 26, "battle", 120, 300, 1.5, 0.5, _VOWELS[:1] + _VOWELS[2:], loud=(0.6, 1.0))
    out = np.zeros((L, 2))
    for c in range(2):
        out[:, c] = _nrms(v[:, c]) * 0.7
        out[:, c] += _nrms(_cf(lambda x: _bp(x, 300, 2500), _wn(L, "battle", c))) * 0.35 * _pmod(L, 12, "battle", "m", c, lo=0.5, hi=1.0)
    r = _rng("battle-clash")
    ev = np.zeros((L, 2))
    for i in range(16):
        k = _n(0.45)
        f0 = r.uniform(700, 1400)
        cl = _ring(k, [f0, f0 * 2.76, f0 * 5.4], [1, .6, .3], [.22, .15, .08], key=("bc", i))
        cl += _nrms(_hp(_wn(k, "bc", i), 2000)) * _exp(k, 0.01) * 0.8
        tmp = np.zeros(L)
        _atw(tmp, cl, r.uniform(0, 6.0), r.uniform(0.3, 0.7))
        pan = r.uniform(0.1, 0.9)
        ev[:, 0] += tmp * (1 - pan)
        ev[:, 1] += tmp * pan
    for i in range(6):
        k = _n(0.5)
        th = _thump(k, 100, 40, 0.05, 0.12) + _nrms(_lp(_wn(k, "bt", i), 500)) * _exp(k, 0.08) * 0.5
        tmp = np.zeros(L)
        _atw(tmp, th, r.uniform(0, 6.0), r.uniform(0.4, 0.8))
        pan = r.uniform(0.2, 0.8)
        ev[:, 0] += tmp * (1 - pan)
        ev[:, 1] += tmp * pan
    for i in range(3):
        k = _n(0.7)
        f = np.interp(_t(k), [0, 0.15, 0.7], [170, 250, 200]) * r.uniform(0.85, 1.2)
        cry = _nrms(_VOWELS[0](_saw(f, k, os=1))) * _pts(k, [(0, 0), (0.06, 1), (0.5, 0.8), (0.7, 0)])
        tmp = np.zeros(L)
        _atw(tmp, cry, r.uniform(0, 6.0), 0.35)
        pan = r.uniform(0.2, 0.8)
        ev[:, 0] += tmp * (1 - pan)
        ev[:, 1] += tmp * pan
    for c in range(2):
        out[:, c] += _cf(lambda x: _lp(x, 5000), ev[:, c]) * 0.5
    return _lfin(out)


@sfx("scooter", loop=True)
def s_scooter():
    L = _dur_loop(2.0)
    x = np.zeros(L)
    r = _rng("scooter")
    nf = 46
    for i in range(nf):
        k = _n(0.05)
        fire = _nrms(_lp(_wn(k, "sc", i), 900)) * _exp(k, 0.006) + _sin(95, k) * _exp(k, 0.01) * 0.8
        _atw(x, fire, (i + r.uniform(-0.08, 0.08)) * 2.0 / nf, (1.0 if i % 2 == 0 else 0.8) * r.uniform(0.85, 1.0))
    t = _t(L)
    whine = _cf(lambda y: _lp(y, 1500), 2.0 * ((230.0 * t) % 1.0) - 1.0) * 0.08
    rattle = _nrms(_cf(lambda y: _bp(y, 2000, 5000), _snh(L, 4, "sc-r"))) * 0.04 * (0.6 + 0.4 * np.sin(TAU * 23 * t))
    x = _cf(lambda y: _lp(y, 3000), x) + whine + rattle
    return _lfin(np.tanh(1.3 * _norm(x)))


@sfx("train", loop=True)
def s_train():
    L = _dur_loop(2.4)
    x = np.zeros(L)
    acc = [1.0, 0.55, 0.8, 0.55]
    for i in range(8):
        k = _n(0.28)
        ch = _nrms(_bp(_wn(k, "tr", i), 300, 2500)) * _ad(k, 0.01, 0.07) + _nrms(_lp(_wn(k, "trl", i), 300)) * _ad(k, 0.01, 0.06) * 0.6
        _atw(x, ch, i * 0.3, acc[i % 4] * 0.6)
    for t0 in (0.0, 0.14, 1.2, 1.34):
        k = _n(0.12)
        cl = _nrms(_hp(_wn(k, "cl", t0), 1500)) * _exp(k, 0.004) + _ring(k, [1250, 2900], [0.8, 0.4], [0.03, 0.015], key=("cl", t0))
        cl += _thump(k, 110, 70, 0.01, 0.03) * 0.7
        _atw(x, cl, t0 + 0.07, 0.9)
    rum = _nrms(_cf(lambda y: _lp(y, 180), _wn(L, "tr-rum"))) * 0.35
    sq = _nrms(_cf(lambda y: _bp(y, 1000, 3000), _wn(L, "tr-sq"))) * 0.05
    return _lfin(np.tanh(1.8 * _norm(x + rum + sq)))


@sfx("engine_hum", loop=True)
def s_engine_hum():
    L = _dur_loop(4.0)
    t = _t(L)
    out = np.zeros((L, 2))
    sets = [(41.25, 41.5, 61.75, 82.5, 123.75), (41.0, 41.75, 62.0, 82.25, 124.0)]
    for c, fs in enumerate(sets):
        saws = sum((2.0 * ((f * t) % 1.0) - 1.0) * a for f, a in zip(fs, (1.0, 0.9, 0.5, 0.45, 0.25)))
        body = _cf(lambda y: _lp(y, 600), saws)
        sub = np.sin(TAU * 41.25 * t) * 0.6
        am = 0.85 + 0.15 * np.sin(TAU * t / 4.0 + c) * (0.9 + 0.1 * np.sin(TAU * 0.75 * t))
        hiss = _nrms(_cf(lambda y: _bp(y, 2000, 6000), _wn(L, "eh", c))) * 0.035
        whine = np.sin(TAU * (660.0 + 0.25 * c) * t) * 0.025 * (0.7 + 0.3 * np.sin(TAU * 0.5 * t))
        out[:, c] = (_nrms(body) * 0.8 + sub) * am + hiss + whine
    return _lfin(out)


def _step(k, key, hard=1.0):
    th = _thump(k, 90 + 30 * hard, 55, 0.02, 0.025 + 0.01 * hard)
    heel = _nrms(_bp(_wn(k, "st", key), 150, 1200)) * _ad(k, 0.001, 0.018)
    scuff = np.zeros(k)
    m = _n(0.05)
    _at(scuff, _nrms(_bp(_wn(m, "sc", key), 900, 4000)) * _ad(m, 0.003, 0.014), 0.045, 0.4)
    return th * 0.7 + heel * 0.8 + scuff


@sfx("footsteps", loop=True)
def s_footsteps():
    L = _dur_loop(2.0)
    x = np.zeros(L)
    r = _rng("steps")
    for i in range(4):
        s = _step(_n(0.14), i)
        if i % 2:
            s = _lp(s, 3000)
        _atw(x, s, i * 0.5 + r.uniform(-0.01, 0.01), (1.0 if i % 2 == 0 else 0.85) * r.uniform(0.9, 1.0))
    return _lfin(x)


@sfx("run", loop=True)
def s_run():
    L = _dur_loop(2.16)
    x = np.zeros(L)
    r = _rng("run")
    for i in range(12):
        s = _step(_n(0.1), 50 + i, hard=1.6)
        _atw(x, s, i * 0.18 + r.uniform(-0.006, 0.006), (1.0 if i % 2 == 0 else 0.85) * r.uniform(0.9, 1.0))
    t = _t(L)
    rustle = _nrms(_cf(lambda y: _bp(y, 1500, 6000), _wn(L, "run-cloth"))) * (0.5 + 0.5 * np.sin(TAU * t / 0.36)) ** 2 * 0.06
    return _lfin(x + rustle)


@sfx("drumroll", loop=True)
def s_drumroll():
    L = _dur_loop(2.0)
    x = np.zeros(L)
    r = _rng("roll")
    for i in range(52):
        k = _n(0.12)
        s = _nrms(_bp(_wn(k, "dr", i), 1500, 8000)) * _ad(k, 0.0008, 0.025) + _tri(200, k) * _exp(k, 0.015) * 0.3
        _atw(x, s, i * 2.0 / 52, (1.0 if i % 2 == 0 else 0.85) * r.uniform(0.85, 1.0))
    wires = _nrms(_cf(lambda y: _hp(y, 3000), _wn(L, "dr-w"))) * 0.15
    return _lfin(x + wires)


@sfx("eat", loop=True)
def s_eat():
    L = _dur_loop(2.4)
    x = np.zeros(L)
    r = _rng("eat")
    for i in range(8):
        t0 = i * 0.3 + r.uniform(-0.015, 0.015)
        k = _n(0.2)
        munch = np.zeros(k)
        for j in range(3):
            m = _n(0.04)
            c = _nrms(_bp(_snh(m, 3, "eat", i, j), 1000, 5000)) * _ad(m, 0.001, 0.01)
            _at(munch, c, j * r.uniform(0.018, 0.03), (1.0, 0.7, 0.45)[j])
        munch += _nrms(_lp(_wn(k, "eat-w", i), 600)) * _ad(k, 0.005, 0.04) * 0.5
        munch += _thump(k, 130, 90, 0.01, 0.02) * 0.3
        _atw(x, munch, t0, r.uniform(0.75, 1.0))
        if i % 2 == 1:
            k2 = _n(0.12)
            f = np.interp(_t(k2), [0, 0.12], [210, 180])
            nom = _lp(_saw(f, k2, os=1), 700) * np.sin(np.pi * _t(k2) / 0.12) ** 2
            _atw(x, _nrms(nom) * 0.25, t0 + 0.12)
    return _lfin(x)
