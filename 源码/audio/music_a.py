"""Composer A: prologue, title, yorozuya, comedy, shinsengumi, ending.

All melodies are ORIGINAL. NES-like palette: band-limited pulse leads
(12.5/25/50 % duty), stepped-triangle bass, noise drums, plus soft bells/pads,
light stereo width and ping-pong echoes.

Every track is a seamless loop made of whole bars: the song is rendered with an
extra tail which is folded back onto the start (so echoes / releases / bell
rings of the last bar continue into bar 1), sustained drones are generated
phase-continuously over the loop, and the master limiter works circularly.
Harmony at the end of each loop leads back into bar 1.

  prologue    D minor (+ Phrygian Eb colour), 70 bpm, 16 bars (54.9 s)
  title       D major/mixolydian, 150 bpm, 24 bars (38.4 s); beat 0 = BIG hit
  yorozuya    F major swing jazz-funk, 110 bpm, 16 bars (34.9 s)
  comedy      C major oom-pah, 132 bpm, 24 bars (43.6 s)
  shinsengumi E minor march, 120 bpm, 20 bars (40.0 s)
  ending      G major, 120 bpm, 24 bars (48.0 s)
"""
import math
import re

import numpy as np
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from scipy.signal import butter, sosfilt

from engine.audio import track
from engine.core import rng
from engine.synth import SR, midi as _note_midi

TARGET_RMS = 0.16
PEAK = 0.85
STATS = {}          # track name -> max limiter gain reduction (dB), for verification


# ====================================================================== basics
def _nprng(*keys):
    return np.random.default_rng(rng("music_a", *keys).getrandbits(63))


def m2f(m):
    if np.isscalar(m):
        return 440.0 * 2.0 ** ((float(m) - 69.0) / 12.0)
    return 440.0 * np.exp2((np.asarray(m, np.float64) - 69.0) / 12.0)


_SOS = {}


def _sos(kind, f1, f2=None, order=2):
    key = (kind, round(float(f1), 2), None if f2 is None else round(float(f2), 2), order)
    s = _SOS.get(key)
    if s is None:
        ny = SR / 2.0
        if kind == "bandpass":
            wn = [max(f1, 10.0) / ny, min(f2, ny * 0.95) / ny]
        else:
            wn = min(max(f1, 5.0), ny * 0.95) / ny
        s = _SOS[key] = butter(order, wn, btype=kind, output="sos")
    return s


def lp(x, fc, order=2):
    return sosfilt(_sos("lowpass", fc, order=order), x, axis=0).astype(np.float32)


def hp(x, fc, order=2):
    return sosfilt(_sos("highpass", fc, order=order), x, axis=0).astype(np.float32)


def bp(x, f1, f2, order=2):
    return sosfilt(_sos("bandpass", f1, f2, order), x, axis=0).astype(np.float32)


def _circ(fn, y, pre=None):
    """Apply a causal filter to a loop as if it had been looping forever."""
    m = min(len(y), pre or SR)
    return fn(np.concatenate([y[-m:], y], 0))[m:]


def _place(dst, src, at):
    if at >= len(dst):
        return
    if at < 0:
        src = src[-at:]
        at = 0
    n = min(len(src), len(dst) - at)
    if n > 0:
        dst[at:at + n] += src[:n]


def _fadeout(y, ms=6.0):
    y = np.asarray(y, np.float32)
    k = min(len(y), int(ms * SR / 1000))
    if k > 1:
        y[-k:] *= np.linspace(1.0, 0.0, k, dtype=np.float32)
    return y


# ================================================================ oscillators
def _phase(f, n, ph0=0.0):
    """-> (dt, phase); dt stays scalar for constant frequency (fast path)."""
    if np.isscalar(f):
        dt = float(f) / SR
        return dt, (ph0 + np.arange(n) * dt) % 1.0
    dt = np.asarray(f, np.float64) / SR
    ph = np.cumsum(dt)
    ph -= dt[0] - ph0
    return dt, ph % 1.0


def _blep(t, dt):
    out = np.zeros_like(t)
    sc = np.isscalar(dt)
    m = np.flatnonzero(t < dt)
    if len(m):
        x = t[m] / (dt if sc else dt[m])
        out[m] = x + x - x * x - 1.0
    m = np.flatnonzero(t > 1.0 - dt)
    if len(m):
        x = (t[m] - 1.0) / (dt if sc else dt[m])
        out[m] = x * x + x + x + 1.0
    return out


def osc_pulse(f, n, duty=0.5, ph0=0.0):
    """Band-limited (polyBLEP) pulse, DC removed."""
    dt, ph = _phase(f, n, ph0)
    y = np.where(ph < duty, 1.0, -1.0)
    y += _blep(ph, dt)
    y -= _blep((ph - duty) % 1.0, dt)
    return y - (2.0 * duty - 1.0)


def osc_tri(f, n, steps=0, ph0=0.0):
    _, ph = _phase(f, n, ph0)
    y = 4.0 * np.abs(ph - 0.5) - 1.0
    if steps:
        h = (steps - 1) / 2.0
        y = np.round((y + 1.0) * h) / h - 1.0
    return y


def osc_sine(f, n, ph0=0.0):
    _, ph = _phase(f, n, ph0)
    return np.sin(2 * np.pi * ph)


def _env(ng, n, a, d, s, r):
    a, d, r = max(a, 1e-4), max(d, 1e-4), max(r, 1e-4)
    env = np.empty(n)
    na = min(int(a * SR), ng, n)
    env[:na] = np.arange(na) / (a * SR)
    if ng > na:
        td = np.arange(ng - na) / SR
        env[na:ng] = s + (1 - s) * np.exp(-td / d) if s < 1 else 1.0
    tg = ng / SR
    lg = tg / a if tg < a else s + (1 - s) * math.exp(-(tg - a) / d)
    if n > ng:
        u = np.minimum(np.arange(n - ng) / (r * SR), 1.0)
        env[ng:] = lg * (1.0 - u) ** 2
    return env


def I(**kw):
    """Instrument definition."""
    d = dict(wave="pulse", duty=0.5, a=0.004, d=0.12, s=0.6, r=0.06, gain=0.25,
             vib=0.0, vib_rate=5.5, vib_delay=0.2, glide=0.07, scoop=1.5, gate=0.92,
             steps=0, detune=7.0, sweep=0.0, sweep_t=0.02, lpf=None, hpf=None,
             partials=None, strike=0.0)
    d.update(kw)
    return d


TEMPLE = [(0.5, .45, .30), (1.0, 1.0, .65), (1.0045, .75, .70), (2.0, .40, 1.1),
          (2.42, .28, 1.7), (2.98, .22, 2.3), (4.07, .13, 3.4), (5.40, .07, 5.0)]
GLOCK = [(1.0, 1.0, 2.4), (2.76, .30, 6.0), (5.40, .10, 11.0), (8.93, .04, 16.0)]


def _synth(inst, m, ng, vel, prev=None, scoop=False):
    w = inst["wave"]
    r = inst["r"]
    n = ng + int(r * SR) + 1
    t = np.arange(n) / SR
    glide = prev is not None and prev != m
    if glide or scoop or inst["sweep"] or (inst["vib"] and n / SR > inst["vib_delay"]):
        dev = np.zeros(n)                      # pitch deviation in semitones
        if glide:
            dev += (prev - m) * np.exp(-t / (inst["glide"] / 3.0))
        if scoop:
            dev -= inst["scoop"] * np.exp(-t / 0.035)
        if inst["sweep"]:
            dev += inst["sweep"] * np.exp(-t / inst["sweep_t"])
        if inst["vib"]:
            ramp = np.clip((t - inst["vib_delay"]) / 0.3, 0.0, 1.0)
            dev += inst["vib"] * ramp * np.sin(2 * np.pi * inst["vib_rate"] * t)
        f = m2f(m) * np.exp2(dev / 12.0)
    else:
        f = m2f(m)
    if w == "pulse":
        y = osc_pulse(f, n, inst["duty"])
    elif w == "tri":
        y = osc_tri(f, n, inst["steps"])
    elif w == "sine":
        y = osc_sine(f, n)
    elif w == "pad":
        c = 2 ** (inst["detune"] / 1200.0)
        y = 0.5 * osc_tri(f * c, n) + 0.5 * osc_tri(f / c, n, ph0=0.37) + 0.2 * osc_sine(f * 2, n)
    elif w == "bell":
        y = np.zeros(n)
        for j, (ratio, amp, k) in enumerate(inst["partials"]):
            nk = min(n, int(9.0 / k * SR))       # stop once the partial is < -78 dB
            fk = f * ratio if np.isscalar(f) else f[:nk] * ratio
            y[:nk] += amp * np.exp(-k * t[:nk]) * osc_sine(fk, nk, ph0=0.13 * j)
        if inst["strike"]:
            nz = _nprng("strike", int(m * 100)).uniform(-1, 1, n)
            y += inst["strike"] * lp(nz, 1200) * np.exp(-t * 70)
    else:
        raise ValueError(w)
    env = _env(ng, n, inst["a"], inst["d"], inst["s"], r)
    return (y * env * (vel * inst["gain"])).astype(np.float32)


# ======================================================================= drums
def _tt(n):
    return np.arange(n) / SR


def k_kick(r, f0=150.0, f1=46.0, dur=0.3, decay=9.0, click=0.35):
    n = int(dur * SR)
    t = _tt(n)
    f = f1 + (f0 - f1) * np.exp(-t * 32)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * decay)
    cl = lp(r.uniform(-1, 1, n), 3000) * np.exp(-t * 300) * click
    return _fadeout(body + cl)


def k_snare(r, dur=0.2, tone=185.0, decay=17.0, bright=8000.0, noise=0.85):
    n = int(dur * SR)
    t = _tt(n)
    nz = np.repeat(r.uniform(-1, 1, n // 2 + 1), 2)[:n]         # NES-ish crunch
    nz = bp(nz, 1100, bright) * np.exp(-t * decay) * noise
    body = osc_tri(tone * (1 + 0.6 * np.exp(-t * 60)), n) * np.exp(-t * 28) * 0.55
    return _fadeout(nz * 1.6 + body)


def k_hat(r, open_=False):
    dur = 0.36 if open_ else 0.06
    n = int(dur * SR)
    t = _tt(n)
    x = hp(r.uniform(-1, 1, n), 7000)
    return _fadeout(x * np.exp(-t * (8 if open_ else 65)) * 0.9)


def k_crash(r, dur=2.4):
    n = int(dur * SR)
    t = _tt(n)
    x = r.uniform(-1, 1, n)
    x2 = np.repeat(r.uniform(-1, 1, n // 2 + 1), 2)[:n]
    y = hp(x, 3500) * (0.55 * np.exp(-t * 1.6) + 0.45 * np.exp(-t * 7.0)) * 1.3
    y += bp(x2, 1500, 6000) * np.exp(-t * 4.0) * 0.45
    y *= np.clip(t / 0.002, 0, 1)
    return _fadeout(y)


def k_tom(r, f):
    n = int(0.4 * SR)
    t = _tt(n)
    fr = f * (1 + 0.5 * np.exp(-t * 25))
    body = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 8)
    nz = lp(r.uniform(-1, 1, n), 2500) * np.exp(-t * 40) * 0.3
    return _fadeout(body + nz)


def k_taiko(r, f0=100.0, f1=52.0, dur=1.2, decay=3.8):
    n = int(dur * SR)
    t = _tt(n)
    f = f1 + (f0 - f1) * np.exp(-t * 20)
    ph = np.cumsum(f) / SR
    body = np.sin(2 * np.pi * ph) * np.exp(-t * decay)
    body2 = np.sin(2 * np.pi * ph * 1.58) * np.exp(-t * decay * 2.2) * 0.35
    skin = lp(r.uniform(-1, 1, n), 900) * np.exp(-t * 30) * 0.8
    return _fadeout((body + body2 + skin) * 0.9)


def k_block(r, f):
    n = int(0.14 * SR)
    t = _tt(n)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t * 55) + 0.45 * np.sin(2 * np.pi * 2.72 * f * t) * np.exp(-t * 90)
    y += hp(r.uniform(-1, 1, n), 2000) * np.exp(-t * 400) * 0.3
    return _fadeout(y * 0.8)


def k_shaker(r):
    n = int(0.09 * SR)
    t = _tt(n)
    x = bp(r.uniform(-1, 1, n), 5000, 12000)
    env = np.minimum(t / 0.012, 1.0) * np.exp(-np.maximum(t - 0.012, 0) * 50)
    return _fadeout(x * env)


def k_clap(r):
    n = int(0.25 * SR)
    t = _tt(n)
    x = bp(r.uniform(-1, 1, n), 900, 3500)
    env = np.zeros(n)
    for d in (0.0, 0.009, 0.018):
        env += np.where(t >= d, np.exp(-(t - d) * 180), 0.0)
    env += np.where(t >= 0.027, np.exp(-(t - 0.027) * 22), 0.0) * 0.8
    return _fadeout(x * env * 1.3)


# ===================================================================== parsing
_TOK = re.compile(r"^([~/]*)(R|r|-|\[[^\]]+\]|[A-Ga-g][#b]?-?\d)(?::([0-9.]+))?([!?']*)$")


def S(text, bar=1, vel=0.8, bpb=4, check=True):
    """Melody DSL. Bars separated by '|' (each must sum to bpb beats).
    Token: [~ glide][/ scoop]NOTE[:beats][! accent][? soft][' staccato];
    R = rest, - = tie previous note, [C4,E4] = chord."""
    ev = []
    pos = (bar - 1) * bpb
    for bi, part in enumerate(text.split("|")):
        toks = part.split()
        start = pos
        for tok in toks:
            mt = _TOK.match(tok)
            if not mt:
                raise ValueError(f"bad token {tok!r}")
            mods, name, dur, fl = mt.groups()
            d = float(dur) if dur else 1.0
            if name in ("R", "r"):
                pass
            elif name == "-":
                ev[-1]["d"] += d
            else:
                if name.startswith("["):
                    m = [_note_midi(x) for x in name[1:-1].split(",")]
                else:
                    m = _note_midi(name)
                v = vel
                if "!" in fl:
                    v = min(1.0, vel * 1.2)
                if "?" in fl:
                    v = vel * 0.6
                e = dict(b=pos, d=d, m=m, v=v, gl="~" in mods, sc="/" in mods)
                if "'" in fl:
                    e["gate"] = 0.45
                ev.append(e)
            pos += d
        if check and toks and abs(pos - start - bpb) > 1e-6:
            raise ValueError(f"bar {bar + bi}: {pos - start} beats in {part.strip()!r}")
    return ev


_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_ACC = {"#": 1, "b": -1, "": 0}
_QUAL = {
    "": (0, 4, 7), "m": (0, 3, 7), "5": (0, 7), "7": (0, 4, 7, 10), "maj7": (0, 4, 7, 11),
    "m7": (0, 3, 7, 10), "6": (0, 4, 7, 9), "m6": (0, 3, 7, 9), "sus4": (0, 5, 7),
    "7sus4": (0, 5, 7, 10), "dim": (0, 3, 6), "add9": (0, 4, 7, 14), "9": (0, 4, 7, 10, 14),
    "7b9": (0, 4, 7, 10, 13), "m9": (0, 3, 7, 10, 14), "maj9": (0, 4, 7, 11, 14),
}


def _parse_chord(sym):
    main, _, bass = sym.partition("/")
    mt = re.fullmatch(r"([A-G])([#b]?)(.*)", main)
    root = (_PC[mt.group(1)] + _ACC[mt.group(2)]) % 12
    ivs = _QUAL[mt.group(3)]
    bpc = root
    if bass:
        mb = re.fullmatch(r"([A-G])([#b]?)", bass)
        bpc = (_PC[mb.group(1)] + _ACC[mb.group(2)]) % 12
    return root, ivs, bpc


def CH(text, bar=1, bpb=4):
    """Chord chart: 'Dm | Am7 D7 | Bb:1 C:3' (chords in a bar share it equally
    unless given :beats)."""
    out = []
    for bi, part in enumerate(text.split("|")):
        toks = part.split()
        base = (bar - 1 + bi) * bpb
        fixed = [float(t.split(":")[1]) for t in toks if ":" in t]
        free = [t for t in toks if ":" not in t]
        share = (bpb - sum(fixed)) / len(free) if free else 0.0
        pos = base
        for tok in toks:
            sym, _, d = tok.partition(":")
            d = float(d) if d else share
            root, ivs, bpc = _parse_chord(sym)
            out.append(dict(b=pos, d=d, root=root, ivs=ivs, bass=bpc, sym=sym))
            pos += d
        if abs(pos - base - bpb) > 1e-6:
            raise ValueError(f"chord bar {bar + bi}: {part!r}")
    return out


def _pcs(c):
    return {(c["root"] + iv) % 12 for iv in c["ivs"]}


def chord_at(chs, beat):
    for c in chs:
        if c["b"] - 1e-6 <= beat < c["b"] + c["d"] - 1e-6:
            return c
    return chs[-1]


def _evsub(ev, b0, b1):
    return [dict(e) for e in ev if b0 - 1e-6 <= e["b"] < b1 - 1e-6]


def _tr(ev, st):
    out = []
    for e in ev:
        e = dict(e)
        e["m"] = [x + st for x in e["m"]] if isinstance(e["m"], list) else e["m"] + st
        out.append(e)
    return out


def _shape(ev, fn):
    for e in ev:
        e["v"] *= fn(e["b"])
    return ev


# ================================================================== generators
def _voicings(chs, lo, hi, drop_root=False, maxn=4):
    out, prev = [], None
    for c in chs:
        pcs = list(dict.fromkeys((c["root"] + iv) % 12 for iv in c["ivs"]))
        if drop_root and len(pcs) >= 4:
            pcs = pcs[1:]
        pcs = pcs[:maxn]
        best, bs = None, 1e9
        for j in range(len(pcs)):
            rot = pcs[j:] + pcs[:j]
            v = [lo + (rot[0] - lo) % 12]
            for pc in rot[1:]:
                v.append(v[-1] + ((pc - v[-1]) % 12 or 12))
            if v[-1] > hi:
                continue
            if prev is None:
                sc = abs(np.mean(v) - (lo + hi) / 2)
            else:
                sc = abs(np.mean(v) - np.mean(prev)) + 0.3 * abs(v[-1] - prev[-1])
            if sc < bs:
                best, bs = v, sc
        if best is None:
            best = [lo + (pcs[0] - lo) % 12]
            for pc in pcs[1:]:
                best.append(best[-1] + ((pc - best[-1]) % 12 or 12))
        out.append(best)
        prev = best
    return out


def _inrange(chs, b0, b1):
    return [(i, c) for i, c in enumerate(chs) if b0 - 1e-6 <= c["b"] < b1 - 1e-6]


def _bassline(chs, pats, lo=36, vel=0.9, b0=0, b1=1e9):
    """pats: {chord_len_beats: [(offset, dur, degree, vel)]}; degrees: R root, 8 octave, 5 fifth
    above, W fifth above/below (whichever is nearer the next root), 3, 7, A chromatic approach
    to the next root from the side of the previous note, a approach from above."""
    ev = []
    for i, c in _inrange(chs, b0, b1):
        nx = chs[(i + 1) % len(chs)]
        root = lo + (c["bass"] - lo) % 12
        nroot = lo + (nx["bass"] - lo) % 12          # where the next root will actually sound
        pat = pats.get(c["d"], pats.get(0))
        last = root
        third = 3 if 3 in c["ivs"] else 4
        sev = 10 if 10 in c["ivs"] else (11 if 11 in c["ivs"] else 12)
        for off, dur, deg, v in pat:
            if off >= c["d"] - 1e-6:
                continue
            if deg == "R":
                m = root
            elif deg == "8":
                m = root + 12
            elif deg == "5":
                m = root + (c["root"] + 7 - root) % 12
            elif deg == "W":
                up = root + (c["root"] + 7 - root) % 12
                m = up if abs(up - nroot) <= abs(up - 12 - nroot) else up - 12
            elif deg == "3":
                m = root + (c["root"] + third - root) % 12
            elif deg == "7":
                m = root + ((c["root"] + sev - root) % 12 or 12)
            elif deg == "A":
                m = nroot + 1 if last > nroot else nroot - 1
                if m == last:                        # would repeat: enclose from the other side
                    m = 2 * nroot - m
            elif deg == "a":
                m = nroot + 1
            else:
                raise ValueError(deg)
            ev.append(dict(b=c["b"] + off, d=min(dur, c["d"] - off), m=m, v=vel * v))
            last = m
    return ev


def _arp(chs, pattern, step, lo, n, vel, gate=0.7, b0=0, b1=1e9, accent=None):
    ev, prev = [], None
    for _, c in _inrange(chs, b0, b1):
        pcs = _pcs(c)
        root = lo + (c["root"] - lo) % 12
        if prev is not None and root - 12 >= lo - 5 and abs(root - 12 - prev) < abs(root - prev):
            root -= 12                                # stay in the same register band
        prev = root
        tones, m = [root], root + 1
        while len(tones) < n:
            if m % 12 in pcs:
                tones.append(m)
            m += 1
        k, b = 0, c["b"]
        while b < c["b"] + c["d"] - 1e-6:
            a = accent[k % len(accent)] if accent else 1.0
            ev.append(dict(b=b, d=step, m=tones[pattern[k % len(pattern)] % n], v=vel * a, gate=gate))
            b += step
            k += 1
    return ev


def _comp(chs, rhythm, lo, hi, vel, b0=0, b1=1e9, drop_root=False, maxn=4):
    sel = _inrange(chs, b0, b1)
    vs = _voicings([c for _, c in sel], lo, hi, drop_root, maxn)
    ev = []
    for (_, c), v in zip(sel, vs):
        pat = rhythm.get(c["d"], rhythm.get(0))
        if pat == "hold":
            ev.append(dict(b=c["b"], d=c["d"], m=list(v), v=vel))
            continue
        for off, dur, vv in pat:
            if off < c["d"] - 1e-6:
                ev.append(dict(b=c["b"] + off, d=dur, m=list(v), v=vel * vv))
    return ev


def _power(chs, rhythm, lo, vel, b0=0, b1=1e9):
    ev = []
    for _, c in _inrange(chs, b0, b1):
        root = lo + (c["root"] - lo) % 12
        pat = rhythm.get(c["d"], rhythm.get(0))
        for off, dur, vv in pat:
            if off < c["d"] - 1e-6:
                ev.append(dict(b=c["b"] + off, d=dur, m=[root, root + 7, root + 12], v=vel * vv))
    return ev


_TIER = {3: 0, 4: 0, 8: 0, 9: 0, 5: 1, 7: 2}


def _harmony(mel, chs, min_dur=0.4, vel=0.7):
    """Second voice: a consonant chord tone 3-9 semitones below each melody note
    (3rds/6ths first, then 4th, then 5th), choosing the one nearest the previous
    harmony note for smooth voice-leading."""
    ev, prev = [], None
    for e in sorted(mel, key=lambda e: e["b"]):
        if isinstance(e["m"], list) or e["d"] < min_dur - 1e-6:
            continue
        pcs = _pcs(chord_at(chs, e["b"]))
        cands = []
        for iv, tier in _TIER.items():
            m = e["m"] - iv
            if m % 12 in pcs:
                near = abs(m - prev) if prev is not None else (0 if iv in (3, 4) else 1)
                cands.append((tier, near, m))
        if cands:
            m = min(cands)[2]
            ev.append(dict(e, m=m, v=e["v"] * vel, gl=False, sc=False))
            prev = m
    return ev


def pat(p, bar, steps=4, bpb=4, off=0.0):
    """Drum step pattern for one bar: X=1 x=.75 o=.45 g=.28, r=2x32nd roll."""
    hits = []
    base = (bar - 1) * bpb + off
    for i, ch in enumerate(p.replace(" ", "")):
        b = base + i / steps
        if ch == ".":
            continue
        if ch == "r":
            hits += [(b, 0.5), (b + 0.5 / steps, 0.6)]
        else:
            hits.append((b, {"X": 1.0, "x": 0.75, "o": 0.45, "g": 0.28}[ch]))
    return hits


def pats(p, bars, **kw):
    out = []
    for b in bars:
        out += pat(p, b, **kw)
    return out


def roll(b0, b1, v0, v1, step=0.125, curve=1.5):
    n = int(round((b1 - b0) / step))
    return [(b0 + i * step, v0 + (v1 - v0) * (i / max(n - 1, 1)) ** curve) for i in range(n)]


# ======================================================================== song
class Song:
    def __init__(self, name, bpm, bars, swing=0.5, tail=4.0, bpb=4):
        self.name, self.bpm, self.bpb = name, bpm, bpb
        self.spb = 60.0 / bpm
        self.beats = bars * bpb
        self.L = int(round(self.beats * self.spb * SR))
        self.N = self.L + int(tail * SR)
        self.bus = np.zeros((self.N, 2), np.float32)
        self.swing = swing

    def r(self, *keys):
        return _nprng(self.name, *keys)

    def warp(self, b):
        if self.swing == 0.5:
            return b
        i = math.floor(b + 1e-9)
        f = b - i
        s = self.swing
        return i + (f * 2 * s if f <= 0.5 else s + (f - 0.5) * 2 * (1 - s))

    def smp(self, b):
        return int(round(self.warp(b) * self.spb * SR))

    def _echo(self, x, beats, fb, mix, taps=5, lpf=3200):
        d = int(round(beats * self.spb * SR))
        src = lp(x, lpf)
        out = np.zeros((len(x), 2), np.float32)
        g = mix
        for i in range(1, taps + 1):
            if d * i >= len(x):
                break
            ch = 1 if i % 2 else 0
            out[d * i:, ch] += src[:len(x) - d * i] * g
            out[d * i:, 1 - ch] += src[:len(x) - d * i] * (g * 0.3)
            g *= fb
        return out

    def add(self, x, pan=0.0, gain=1.0, echo=None):
        x = np.asarray(x, np.float32)
        if x.ndim == 1:
            a = (pan + 1) * math.pi / 4
            st = np.stack([x * math.cos(a), x * math.sin(a)], 1) * (1.4142 * gain)
            if echo:
                st += self._echo(x, *echo) * gain
        else:
            st = x * gain
        _place(self.bus, st.astype(np.float32), 0)

    def voice(self, ev, inst, pan=0.0, gain=1.0, echo=None, key="v"):
        out = np.zeros(self.N, np.float32)
        rr = self.r("voice", key)
        prev = None
        for e in sorted(ev, key=lambda e: e["b"]):
            ms = e["m"] if isinstance(e["m"], (list, tuple)) else [e["m"]]
            s0, s1 = self.smp(e["b"]), self.smp(e["b"] + e["d"])
            ng = max(int((s1 - s0) * e.get("gate", inst["gate"])), 32)
            v = e["v"] * (1.0 + 0.04 * rr.uniform(-1, 1))
            for m in ms:
                pv = prev if (e.get("gl") and len(ms) == 1) else None
                _place(out, _synth(inst, m, ng, v, pv, e.get("sc", False)), s0)
            prev = ms[-1]
        if inst["lpf"]:
            out = lp(out, inst["lpf"])
        if inst["hpf"]:
            out = hp(out, inst["hpf"])
        self.add(out, pan, gain, echo)

    def hits(self, smp, hs, pan=0.0, gain=1.0, echo=None):
        buf = np.zeros(self.N, np.float32)
        for b, v in hs:
            _place(buf, smp * v, self.smp(b))
        self.add(buf, pan, gain, echo)

    # ---- special layers
    def drone(self, notes, pts, lpf=1500, trem=(6, 0.07)):
        """Phase-continuous pedal over the whole loop (exact integer cycles)."""
        L = self.L
        n = np.arange(L)
        secs = L / SR
        y = np.zeros(L)
        for m, amp in notes:
            k = max(1, round(float(m2f(m)) * secs))
            ph = (n * (k / L)) % 1.0
            y += amp * (4.0 * np.abs(ph - 0.5) - 1.0)
        y *= 1.0 + trem[1] * np.sin(2 * np.pi * trem[0] * n / L)
        env = np.interp(n, [self.smp(b) for b, _ in pts], [v for _, v in pts])
        y = _circ(lambda z: lp(z, lpf), (y * env).astype(np.float32))
        st = np.stack([y, y], 1)
        self.bus[:L] += st

    def wind(self, b0, beats, vel, key, lo=250.0, hi=2200.0):
        s0 = self.smp(b0)
        n = self.smp(b0 + beats) - s0
        r = self.r("wind", key)
        u = np.linspace(0, 1, n)
        arch = np.sin(np.pi * u)
        env = arch ** 2 * (1 + 0.25 * np.sin(2 * np.pi * u * beats * 0.37 + key))
        center = lo * (hi / lo) ** (arch ** 1.5)
        bands = lo * (hi / lo) ** np.linspace(0, 1, 5)
        out = np.zeros((n, 2), np.float32)
        for ch in (0, 1):
            x = r.uniform(-1, 1, n)
            for fc in bands:
                wgt = np.exp(-(np.log(center / fc) / 0.45) ** 2)
                out[:, ch] += bp(x, fc / 1.3, fc * 1.3) * wgt
        out *= (env * vel)[:, None]
        _place(self.bus, out, s0)

    def riser(self, b0, b1, vel, key):
        s0 = self.smp(b0)
        n = self.smp(b1) - s0
        u = np.linspace(0, 1, n)
        x = self.r("riser", key).uniform(-1, 1, n)
        y = bp(x, 300, 1500) * (1 - u) ** 2 + bp(x, 1500, 5000) * 2 * u * (1 - u) + hp(x, 5000) * u ** 2
        y *= u ** 2.5 * vel
        _place(self.bus, np.stack([y, y * 0.9], 1).astype(np.float32), s0)

    def whistle(self, b0, beats, m0, m1, vel, pan=0.0):
        n = self.smp(b0 + beats) - self.smp(b0)
        t = _tt(n)
        u = t / t[-1]
        pitch = m0 + (m1 - m0) * u ** 0.7 + 0.35 * np.sin(2 * np.pi * 7 * t)
        y = osc_sine(m2f(pitch), n) * np.minimum(t / 0.02, 1) * np.clip((t[-1] - t) / 0.05, 0, 1)
        buf = np.zeros(self.N, np.float32)
        _place(buf, (y * vel).astype(np.float32), self.smp(b0))
        self.add(buf, pan)

    def boing(self, b0, m, vel, pan=0.0, dur=0.6):
        n = int(dur * SR)
        t = _tt(n)
        pitch = m + 2.5 * np.exp(-t * 5) * np.sin(2 * np.pi * 13 * t) + 3 * np.exp(-t * 40)
        y = osc_tri(m2f(pitch), n) * np.exp(-t * 4) * np.minimum(t / 0.005, 1)
        buf = np.zeros(self.N, np.float32)
        _place(buf, _fadeout(y * vel), self.smp(b0))
        self.add(buf, pan)

    # ---- master
    def finish(self):
        L = self.L
        y = self.bus[:L].astype(np.float64)
        tail = self.bus[L:].astype(np.float64)
        k = min(len(tail), L)
        y[:k] += tail[:k]
        y = _circ(lambda z: sosfilt(_sos("highpass", 28.0), z, axis=0), y)
        gr, first = 1.0, None
        for _ in range(4):
            rms = math.sqrt(float(np.mean(y ** 2)))
            y *= TARGET_RMS / max(rms, 1e-9)
            if first is None:
                a = np.max(np.abs(y), axis=1)
                first = float(np.mean(a > 0.83 * 1.12)) * 100    # % samples needing >1 dB GR
            y, g = _limit(y, 0.83)
            gr = min(gr, g)
        pk = float(np.max(np.abs(y)))
        if pk > PEAK:
            y *= PEAK / pk
        STATS[self.name] = (20 * math.log10(max(gr, 1e-6)), first)
        return y.astype(np.float32)


def _limit(y, thr, win=0.010):
    a = np.max(np.abs(y), axis=1)
    g = np.minimum(1.0, thr / np.maximum(a, 1e-9))
    w = int(win * SR)
    g = minimum_filter1d(g, size=2 * w + 1, mode="wrap")
    g = uniform_filter1d(g, size=w + 1, mode="wrap")
    return y * g[:, None], float(g.min())


# ============================================================ shared presets
def _kit(sg):
    r = sg.r
    return dict(kick=k_kick(r("kick")), snare=k_snare(r("snare")), hat=k_hat(r("hat")),
                ohat=k_hat(r("ohat"), True), crash=k_crash(r("crash")), crash2=k_crash(r("crash2")))


# ================================================================== PROLOGUE
@track("prologue")
def prologue():
    """D minor (Phrygian Eb colour), 70 bpm, 16 bars. Bar 1 bell+drone+wind;
    bars 2-4 lonely lament; beats 12-14 roll/riser -> ARRIVAL at beat 14 (=12.0 s,
    the title-logo slam in s00); bars 5-8 lament with counter-line; bars 9-12
    grand climax (taiko, arps, octave doubling); bars 13-16 thinning, A7 -> Dm."""
    sg = Song("prologue", 70, 16, tail=9.0)
    chs = CH("Dm | Dm | Bb | A7:2 D5:2 | Dm | Gm | Eb | A | Dm | Bb | C | A7 | Dm | Gm | Eb | A7")

    sg.drone([(38, .30), (45, .13), (26, .16)],
             [(0, .85), (12, .95), (14, 1.0), (18, .55), (46, .5), (50, .8), (64, .85)])

    mel = (S("R:4 | /D5:1.5 C5:.5 A4:2 | Bb4:.5 A4:.5 G4:.5 F4:.5 G4:2 "
             "| Bb4:.5 A4:.5 Bb4:.5 C#5:.5 D5:2!", 1, vel=.72)
           + S("R:1 F5:.5 E5:.5 D5:1 A4:1 | Bb4:1.5 A4:.5 G4:1 D5:1 | Eb5:1.5 D5:.5 Bb4:1 G4:1 "
               "| A4:3 R:1", 5, vel=.8)
           + S("/D5:1 F5:1 A5:1.5 G5:.5 | F5:1.5 D5:.5 Bb4:1 C5:1 | D5:.5 E5:.5 G5:1.5 F5:.5 E5:1 "
               "| C#5:1 E5:1 A5:1 G5:1", 9, vel=.95)
           + S("/F5:2 E5:1 D5:1 | D5:1.5 Bb4:.5 G4:2 | G4:1 Bb4:1 Eb5:1 D5:1 | A4:1 Bb4:1 A4:2", 13, vel=.74))
    lament = I(wave="pulse", duty=.25, a=.05, d=.4, s=.75, r=.3, gain=.26, vib=.16, vib_rate=5.0,
               vib_delay=.3, gate=.97, lpf=2800)
    sg.voice(mel, lament, pan=-.12, echo=(.75, .42, .36), key="lead")
    sg.voice(_tr(_evsub(mel, 32, 48), -12),
             I(wave="pulse", duty=.5, a=.06, d=.4, s=.7, r=.3, gain=.10, gate=.97, lpf=1500),
             pan=.2, key="dbl")

    ctr = S("A3:2 D4:2 | D4:2 Bb3:2 | G3:2 Bb3:2 | C#4:2 E4:2 | F4:2 A4:2 | D4:2 F4:2 | E4:2 G4:2 "
            "| E4:2 C#4:2 | A4:2 F4:2 | Bb3:2 D4:2 | Bb3:2 G3:2 | E4:2 C#4:2", 5, vel=.6)
    _shape(ctr, lambda b: 1.3 if 32 <= b < 48 else 1.0)
    sg.voice(ctr, I(wave="pulse", duty=.25, a=.25, d=.6, s=.8, r=.5, gain=.13, gate=.98, lpf=1700),
             pan=.35, echo=(1.0, .3, .2), key="ctr")

    bass = S("D2:4 | G2:4 | Eb2:4 | A1:2 A2:2 | D2:1.5 A1:.5 D2:2 | Bb1:1.5 F2:.5 Bb1:2 "
             "| C2:1.5 G2:.5 C2:2 | A1:1.5 E2:.5 A1:1 C#2:1 | D2:4 | G1:4 | Eb2:4 | A1:4", 5, vel=.85)
    sg.voice(bass, I(wave="tri", a=.03, d=.5, s=.85, r=.25, gain=.40, gate=.97, steps=16, lpf=2500),
             key="bass")

    pad = _comp(chs, {0: "hold"}, 50, 64, .7, b0=8)
    sg.voice(pad, I(wave="pad", a=.9, d=1.0, s=1.0, r=1.2, gain=.075, gate=1.0, lpf=1800), key="pad")

    arp = _arp(chs, [0, 1, 2, 3, 4, 3, 2, 1], .5, 62, 5, .5, gate=.9, b0=32, b1=48)
    sg.voice(arp, I(wave="pulse", duty=.125, a=.003, d=.35, s=0, r=.2, gain=.10, lpf=4000),
             pan=-.4, echo=(.75, .35, .3), key="arp")

    bell = I(wave="bell", a=.002, d=10, s=1, r=.5, gain=.22, gate=1.0, partials=TEMPLE, strike=.25,
             lpf=3500)
    bl = [dict(b=b, d=8, m=m, v=v) for b, m, v in
          [(0, 50, 1.0), (8, 50, .5), (14, 50, 1.0), (14, 38, .55), (24, 50, .55), (32, 50, .8),
           (48, 50, .75), (56, 50, .5)]]
    sg.voice(bl, bell, pan=.15, echo=(1.0, .3, .25), key="bell")

    big = k_taiko(sg.r("taiko"))
    small = k_taiko(sg.r("taiko2"), f0=190, f1=120, dur=.5, decay=8)
    sg.hits(big, [(0, .55), (14, 1.0), (20, .4), (24, .4), (28, .45), (32, .8), (34, .5), (36, .75),
                  (38, .5), (40, .8), (42, .5), (44, .8), (46, .55), (48, .9), (56, .45)], gain=.55)
    sg.hits(small, roll(12, 14, .12, .75, .25) + roll(47, 48, .3, .7, .25) + roll(62, 64, .06, .35, .25)
            + [(35.5, .35), (43.5, .35)], gain=.45)
    sg.hits(k_kick(sg.r("sub"), f0=75, f1=37, dur=2.8, decay=1.6, click=0), [(14, 1.0), (48, .6)], gain=.5)
    sg.hits(lp(k_crash(sg.r("gong")), 3000), [(14, .5), (48, .3)], gain=.4)
    sg.riser(12, 14, .45, 1)
    sg.riser(46.5, 48, .22, 2)
    sg.riser(61, 64, .18, 3)
    for b0, beats, v, k in [(0, 11, .5, 1), (22, 10, .4, 2), (38, 8, .28, 3), (50, 18, .45, 4)]:
        sg.wind(b0, beats, v, k)
    return sg.finish()


# ===================================================================== TITLE
_HOOK_A = ("A4:.75 D5:.25 F#5:.5 E5:.5 D5:.5 A5:1.5 | G4:.75 C5:.25 E5:.5 D5:.5 C5:.5 G5:1.5 "
           "| B4:.75 D5:.25 G5:.5 F#5:.5 G5:.5 B5:1.5 | C#6:.75 B5:.25 A5:.5 G5:.5 F#5:.5 E5:1.5")
_HOOK_B = ("A4:.75 D5:.25 F#5:.5 E5:.5 D5:.5 A5:1.5 | G4:.75 C5:.25 E5:.5 G5:.5 A5:.5 C6:1.5 "
           "| F5:.5 D5:.5 Bb4:.5 D5:.5 E5:.5 G5:.5 C6:.5 C#6:.5")
_TITLE_B = ("B5:1.5 A5:.5 F#5:1 D5:1 | E5:1.5 F#5:.5 G5:1 B5:1 | A5:1 G5:.5 F#5:.5 E5:.5 F#5:.5 D5:1 "
            "| E5:2.5 E5:.5 F#5:.5 G5:.5 | F#5:1.5 E5:.5 D5:1 F#5:1 | G5:1.5 A5:.5 B5:1 D6:1 "
            "| E6:1.5 D6:.5 B5:1 G5:1 | A5:2! R:2")


@track("title")
def title():
    """D major (mixolydian bVII/bVI), 150 bpm, 24 bars. Bar 1: BIG HIT on beat 0
    (crash + boom + low D octave stab) then Bb-C stabs; bars 2-9 hook (fanfare
    'da-DA da da da DAAA' cell, antecedent/consequent, Bb-C-D cadence); bars 10-17
    B section (Bm-G-D-A, half-time then build + snare fill); bars 18-24 hook with
    harmony + 16th arps; bar 24 Bb-C leads back into the bar-1 hit."""
    sg = Song("title", 150, 24, tail=4.0)
    chs = CH("D:2 Bb:1 C:1 | D | C | G | A | D | C | Bb C | D | Bm | G | D | A | Bm | G | Em | A "
             "| D | C | G | A | D | C | Bb C")
    lead = (S("D6:1.5! R:.5 D6:.75' R:.25 E6:.75' R:.25", 1, vel=.95)
            + S(_HOOK_A, 2, vel=.9) + S(_HOOK_B, 6, vel=.9) + S("D6:2.5! R:1.5", 9, vel=.95)
            + S(_TITLE_B, 10, vel=.85) + S(_HOOK_A, 18, vel=.95) + S(_HOOK_B, 22, vel=.95))
    sg.voice(lead, I(wave="pulse", duty=.25, a=.004, d=.12, s=.7, r=.06, gain=.25, vib=.12,
                     vib_rate=6, vib_delay=.2, gate=.9, lpf=7000),
             pan=-.12, echo=(.75, .3, .22), key="lead")
    har = _harmony(_evsub(lead, 20, 36) + _evsub(lead, 52, 96), chs, min_dur=.45)
    sg.voice(har, I(wave="pulse", duty=.5, a=.004, d=.12, s=.6, r=.06, gain=.13, gate=.9, lpf=5000),
             pan=.3, key="har")
    sg.voice(_tr(_evsub(lead, 36, 52), -12),
             I(wave="pulse", duty=.5, a=.004, d=.15, s=.6, r=.06, gain=.11, gate=.9, lpf=3500),
             pan=.25, key="dbl")

    # rhythm section: 8th-note power-chord chugs (hooks), sustained power chords (B, first half)
    eighths = {4: [(k * .5, .34, (1.0, .6, .8, .6)[k % 4]) for k in range(8)],
               2: [(k * .5, .34, (1.0, .6, .8, .6)[k % 4]) for k in range(4)]}
    chug = _power(chs, eighths, 45, 1.0, b0=4, b1=36) + _power(chs, eighths, 45, 1.0, b0=52, b1=96)
    sg.voice(chug, I(wave="pulse", duty=.5, a=.002, d=.08, s=.3, r=.03, gain=.075, gate=.8, lpf=2600),
             pan=.35, key="chug")
    sust = _power(chs, {4: [(0, 3.9, 1.0)]}, 45, 1.0, b0=36, b1=52)
    sg.voice(sust, I(wave="pulse", duty=.5, a=.01, d=.5, s=.6, r=.2, gain=.06, gate=.97, lpf=2000),
             pan=-.3, key="sust")
    stab = [dict(b=0, d=1.5, m=[50, 57, 62, 66, 69], v=1.0), dict(b=2, d=.75, m=[46, 53, 58, 62, 65], v=.9),
            dict(b=3, d=.75, m=[48, 55, 60, 64, 67], v=.95)]
    sg.voice(stab, I(wave="pulse", duty=.5, a=.002, d=.35, s=.25, r=.15, gain=.075, gate=.95, lpf=4000),
             echo=(.75, .3, .2), key="stab")
    arps = _arp(chs, [0, 1, 2, 3], .25, 62, 4, .55, gate=.6, b0=36, b1=96,
                accent=[1, .7, .8, .7])
    sg.voice(arps, I(wave="pulse", duty=.125, a=.002, d=.09, s=.2, r=.03, gain=.07, lpf=6000),
             pan=.45, key="arp")

    bass = S("D2:1.5! R:.5 Bb1:.75 R:.25 C2:.75 R:.25", 1, vel=1.0)
    pat8 = {4: [(k * .5, .42, "8" if k in (2, 6) else ("5" if k == 7 else "R"), 1.0 if k % 2 == 0 else .75)
                for k in range(8)],
            2: [(k * .5, .42, "8" if k == 2 else "R", 1.0 if k % 2 == 0 else .75) for k in range(4)]}
    pat_half = {4: [(0, 1.4, "R", 1), (1.5, .45, "R", .75), (2, .9, "8", .85), (3, .45, "W", .75),
                    (3.5, .45, "A", .8)]}
    bass += (_bassline(chs, pat8, 36, b0=4, b1=36) + _bassline(chs, pat_half, 36, b0=36, b1=52)
             + _bassline(chs, pat8, 36, b0=52, b1=96))
    sg.voice(bass, I(wave="tri", a=.003, d=.1, s=.85, r=.04, gain=.40, gate=.9, steps=16, lpf=4000),
             key="bass")

    # drums
    kt = _kit(sg)
    toms = {k: k_tom(sg.r("tom", k), f) for k, f in (("h", 220), ("m", 165), ("l", 120))}
    K, SN, HH, OH, CR, TM = [], [], [], [], [], []
    K += [(0, 1.0), (2, .9), (3, .9)]
    SN += [(0, 1.0), (2, .85), (3, .9)]
    TM += [(3.5, "h", .8), (3.75, "l", .9)]
    CR += [(0, 1.0)]
    hook_bars = list(range(2, 10)) + list(range(18, 25))
    for bar in range(2, 25):
        b0 = (bar - 1) * 4
        if bar in hook_bars or bar in (14, 15, 16):
            K += pat("X.....x.X.x.....", bar)
            SN += pat("....X.......X...", bar)
            HH += pat("X.x.X.x.X.x.X.x." if bar < 18 else "XxxxXxxxXxxxXxxx", bar)
            if bar % 2 == 1:
                OH += [(b0 + 3.5, .7)]
        elif bar in (10, 11, 12, 13):
            K += pat("X.........x.....", bar)
            SN += pat("........X.......", bar)
            HH += pat("x.x.x.x.x.x.x.x.", bar)
        if bar in (2, 6, 10, 14, 18, 22):
            CR += [(b0, .9 if bar != 10 else .7)]
    # fills
    SN += pat("..............xx", 5) + pat("..............xx", 13)
    K = [h for h in K if not (32 <= h[0] < 36)] + pat("X.......", 9)
    SN = [h for h in SN if not (32 <= h[0] < 36)] + [(32 + 1, 1.0), (35.5, .8), (35.75, 1.0)]
    TM += [(34, "h", .8), (34.25, "h", .7), (34.5, "m", .85), (34.75, "m", .75), (35, "l", .9), (35.25, "l", .8)]
    K = [h for h in K if not (64 <= h[0] < 68)] + [(64, 1.0), (65.5, .8)]
    SN = [h for h in SN if not (64 <= h[0] < 68)] + roll(65.5, 68, .3, 1.0, .25, 1.2)
    CR += [(64, .8)]
    SN = [h for h in SN if not (92 <= h[0] < 96)] + pat("....X.....x.xXXX", 24)
    sg.hits(kt["kick"], K, gain=.42)
    sg.hits(kt["snare"], SN, gain=.38)
    sg.hits(kt["hat"], HH, pan=.25, gain=.13)
    sg.hits(kt["ohat"], OH, pan=.25, gain=.12)
    sg.hits(kt["crash"], CR, pan=-.35, gain=.24)
    sg.hits(kt["crash2"], [(0, 1.0)], pan=.45, gain=.26)
    for k in "hml":
        sg.hits(toms[k], [(b, v) for b, kk, v in TM if kk == k], pan={"h": -.3, "m": 0, "l": .3}[k], gain=.45)
    sg.hits(k_taiko(sg.r("boom"), f0=90, f1=40, dur=1.6, decay=2.5), [(0, 1.0)], gain=.6)
    sg.riser(94, 96, .15, 5)
    return sg.finish()


# ================================================================== YOROZUYA
@track("yorozuya")
def yorozuya():
    """F major lazy jazz-funk, 110 bpm, swung 8ths, 16 bars: A (I-iii-VI7-ii-V)
    x2 with lead/response call & answer, B on IV (Bbmaj7 Bbm7-Eb7 Am7 D7) with
    counter-line, turnaround Gm7-C7 -> Fmaj7. Slidey pulse lead (scoops/glides,
    bluesy b3), rootless 7th-chord comping, syncopated walking bass."""
    sg = Song("yorozuya", 110, 16, swing=.62, tail=4.0)
    chs = CH("Fmaj7 | Am7 D7 | Gm7 | C7 | Fmaj7 | Am7 D7 | Gm7 C7 | F6 F7 | Bbmaj7 | Bbm7 Eb7 | Am7 | D7 "
             "| Gm7 | C7 | Fmaj7 D7 | Gm7 C7")
    lead = S("R:.5 C5:.5 D5:.5 /F5:1.5 E5:.5 C5:.5 | D5:.5 C5:.5 A4:1 R:.5 F#4:.5 A4:.5 C5:.5 "
             "| Bb4:1.5 A4:.5 G4:.5 F4:.5 Ab4:.5 ~A4:.5 | Bb4:.5 A4:.5 G4:1 R:2 "
             "| R:.5 C5:.5 D5:.5 /F5:1.5 G5:.5 A5:.5 | ~G5:.5 E5:.5 C5:1 R:.5 D5:.5 F#5:.5 A5:.5 "
             "| G5:1 F5:.5 D5:.5 E5:.5 C5:.5 Bb4:.5 G4:.5 | A4:2 R:2 "
             "| D5:1.5 C5:.5 D5:.5 F5:1 A5:.5 | /Ab5:1.5 F5:.5 G5:1 Db5:1 | C5:1.5 E5:.5 G5:1 E5:1 "
             "| F#5:1.5 E5:.5 D5:.5 C5:.5 A4:1 "
             "| Bb4:.5 D5:.5 F5:1.5 E5:.5 D5:1 | E5:1 G5:.5 Bb5:1 A5:.5 G5:1 | A5:1.5 F5:.5 F#5:1 C5:1 "
             "| Bb4:1 A4:.5 G4:.5 E4:.5 G4:.5 Bb4:.5 C5:.5", 1, vel=.8)
    _shape(lead, lambda b: 1.08 if b >= 32 else 1.0)
    sg.voice(lead, I(wave="pulse", duty=.25, a=.012, d=.25, s=.72, r=.1, gain=.26, vib=.2, vib_rate=5.2,
                     vib_delay=.22, glide=.09, scoop=2.0, gate=.9, lpf=3600),
             pan=-.15, echo=(.75, .3, .22), key="lead")
    resp = S("R:2 C6:.5 Bb5:.5 G5:.5 E5:.5", 4, vel=.7) + S("R:2 A5:.5 C6:.5 Eb6:.5 ~D6:.5", 8, vel=.7)
    sg.voice(resp, I(wave="pulse", duty=.125, a=.006, d=.18, s=.5, r=.08, gain=.2, vib=.15, gate=.85,
                     glide=.08, lpf=5000),
             pan=.4, echo=(.75, .35, .3), key="resp")
    ctr = S("F4:2 A4:2 | Ab4:2 G4:2 | G4:2 E4:2 | F#4:2 C4:2 | F4:2 D4:2 | E4:2 G4:2 | A4:2 F#4:2 "
            "| F4:2 E4:2", 9, vel=.6)
    sg.voice(ctr, I(wave="pulse", duty=.5, a=.12, d=.5, s=.8, r=.3, gain=.1, gate=.97, lpf=1400),
             pan=.4, key="ctr")

    comp_r = {4: [(.5, .4, .85), (1.5, .3, .6), (2.5, .8, .75)], 2: [(.5, .4, .85), (1.5, .35, .65)]}
    comp = _comp(chs, comp_r, 53, 67, .8, drop_root=True)
    sg.voice(comp, I(wave="pulse", duty=.5, a=.004, d=.15, s=.35, r=.08, gain=.06, gate=.9, lpf=2200),
             pan=-.35, key="comp")
    bpat = {4: [(0, .9, "R", 1), (1.5, .45, "R", .7), (2, .45, "5", .85), (3, .45, "W", .75), (3.5, .45, "A", .8)],
            2: [(0, .9, "R", 1), (1, .45, "W", .7), (1.5, .45, "A", .8)]}
    sg.voice(_bassline(chs, bpat, 36), I(wave="tri", a=.004, d=.2, s=.7, r=.05, gain=.44, gate=.9,
                                         steps=16, lpf=3000), key="bass")

    kt = _kit(sg)
    K, SN, HH, OH = [], [], [], []
    for bar in range(1, 17):
        K += pat("X.....x...x.....", bar)
        SN += pat("....x.......x.g.", bar)
        HH += pat("x.o.x.o.x.o.x.o.", bar)
        if bar in (4, 12):
            OH += [((bar - 1) * 4 + 3.5, .6)]
    SN = [h for h in SN if not (28 <= h[0] < 32 or 60 <= h[0] < 64)]
    SN += pat("....x...x.x.x.X.", 8) + pat("....x...x.o.x.X.", 16)
    sg.hits(kt["kick"], K, gain=.5)
    sg.hits(k_snare(sg.r("sn2"), tone=210, decay=22, bright=6500), SN, gain=.3)
    sg.hits(kt["hat"], HH, pan=.3, gain=.11)
    sg.hits(kt["ohat"], OH, pan=.3, gain=.09)
    sg.hits(k_shaker(sg.r("shk")), pats("..x...x...x...x.", range(1, 17)), pan=-.4, gain=.06)
    sg.hits(kt["crash"], [(0, .6), (32, .5)], pan=-.3, gain=.22)
    return sg.finish()


# ==================================================================== COMEDY
_COM_A = ("C5:.5 R:.5 E5:.5 R:.5 D#5:.25 E5:.25 G5:.5 R:1 | C#5:.5 R:.5 E5:.5 R:.5 D5:.25 E5:.25 G5:.5 R:1 "
          "| D5:.5 R:.5 F5:.5 R:.5 G#5:.25 A5:.25 C6:.5 R:1 "
          "| B5:.5 A5:.5 G5:.5 F5:.5 E5:.5 D5:.5 C#5:.25 D5:.25 B4:.5 "
          "| C5:.5 R:.5 E5:.5 R:.5 D#5:.25 E5:.25 G5:.5 R:1 | C#6:.5 R:.5 A5:.5 R:.5 A#5:.25 B5:.25 C#6:.5 R:1 "
          "| D6:.5 A5:.5 F5:.5 D5:.5 F5:.5 G5:.5 B5:.5 D6:.5")
_COM_B = ("A4:.5 R:.5 C5:.5 R:.5 E5:.5 D#5:.5 E5:.5 R:.5 | G#4:.5 R:.5 B4:.5 R:.5 D5:.5 C#5:.5 D5:.5 R:.5 "
          "| A4:.5 R:.5 C5:.5 R:.5 E5:.5 F5:.5 E5:.5 C5:.5 | B4:.5 R:.5 G#4:.5 R:.5 E4:1 R:1 "
          "| A4:.5 C5:.5 F5:1 E5:.5 D#5:.5 E5:1 | G5:.5 E5:.5 C5:.5 E5:.5 G5:1 R:1 "
          "| F#5:.5 A5:.5 C6:.5 A5:.5 F#5:.5 D5:.5 E5:.5 F#5:.5 "
          "| G5:.5 R:.5 G5:.5 R:.5 G5:.25 F#5:.25 F5:.25 E5:.25 D#5:.25 D5:.25 C#5:.25 D5:.25")


@track("comedy")
def comedy():
    """C major bouncy oom-pah, 132 bpm, 24 bars: A (C A7 Dm G7, staccato hops
    with chromatic grace notes, temple-block answers, slide whistle), B sneaky
    tiptoe in A minor (staccato walking bass, chromatic run down in bar 16),
    A' with parallel-third harmony + claps; bar 24 chromatic run up into bar 1."""
    sg = Song("comedy", 132, 24, tail=4.0)
    chs = CH("C | A7 | Dm | G7 | C | A7 | Dm G7 | C | Am | E7 | Am | E7 | F | C/E | D7 | G7 "
             "| C | A7 | Dm | G7 | C | A7 | Dm G7 | C G7")
    lead = (S(_COM_A, 1, vel=.85) + S("C6:.5 R:.5 G5:.5 R:.5 C5:.5 R:1.5", 8, vel=.85)
            + S(_COM_B, 9, vel=.72)
            + S(_COM_A, 17, vel=.9) + S("C6:.5 R:.5 G5:.5 R:.5 G4:.25 G#4:.25 A4:.25 A#4:.25 B4:.5 R:.5", 24, vel=.9))
    pluck = I(wave="pulse", duty=.25, a=.004, d=.11, s=.12, r=.04, gain=.27, gate=.7, lpf=7000)
    sg.voice(_evsub(lead, 0, 32) + _evsub(lead, 64, 96), pluck, pan=-.15, echo=(.5, .25, .18), key="lead")
    sg.voice(_evsub(lead, 32, 64), I(wave="pulse", duty=.125, a=.003, d=.09, s=.1, r=.04, gain=.3, gate=.6,
                                     lpf=6000), pan=-.1, echo=(.75, .3, .25), key="leadB")
    har = _harmony(_evsub(lead, 64, 96), chs, min_dur=.5, vel=.65)
    sg.voice(har, I(wave="pulse", duty=.5, a=.003, d=.1, s=.12, r=.04, gain=.17, gate=.7, lpf=4500),
             pan=.35, key="har")

    oom = {4: [(0, .6, "R", 1), (2, .6, "5", .85)], 2: [(0, .6, "R", 1)]}
    walk = {4: [(0, .4, "R", .9), (1, .4, "3", .7), (2, .4, "5", .8), (3, .4, "3", .7)]}
    bass = _bassline(chs, oom, 36, b0=0, b1=32) + _bassline(chs, walk, 36, b0=32, b1=64) \
        + _bassline(chs, oom, 36, b0=64, b1=96)
    sg.voice(bass, I(wave="tri", a=.004, d=.12, s=.6, r=.04, gain=.40, gate=.8, steps=16, lpf=3500), key="bass")
    pah = {4: [(1, .3, 1.0), (3, .3, .9)], 2: [(1, .3, 1.0)]}
    comp = _comp(chs, pah, 55, 67, .8)
    _shape(comp, lambda b: .6 if 32 <= b < 64 else 1.0)
    sg.voice(comp, I(wave="pulse", duty=.5, a=.002, d=.07, s=.1, r=.03, gain=.065, gate=.8, lpf=3500),
             pan=.3, key="pah")

    kt = _kit(sg)
    blk = {"h": k_block(sg.r("bh"), 980), "l": k_block(sg.r("bl"), 690)}
    K, SN, SH, BH, BL, CL = [], [], [], [], [], []
    for bar in range(1, 25):
        if 9 <= bar <= 16:
            K += pat("X...............", bar)
            BL += pat("....x.......x...", bar)
            SH += pat("..x...x...x...x.", bar)
        else:
            K += pat("X.......x.......", bar)
            SN += pat("....x.......x...", bar)
            SH += pat("x.x.x.x.x.x.x.x." if bar < 17 else "xoxoxoxoxoxoxoxo", bar)
            if bar >= 17:
                CL += pat("....x.......x...", bar)
    resp = {1: "hl", 2: "lh", 3: "hhl", 5: "hl"}
    for base in (0, 16):
        for bar, seq in resp.items():
            b0 = (base + bar - 1) * 4 + 3
            steps = [0, .5] if len(seq) == 2 else [0, .25, .5]
            for s, k in zip(steps, seq):
                (BH if k == "h" else BL).append((b0 + s, .8))
    SN = [h for h in SN if not (60 <= h[0] < 64 or 92 <= h[0] < 96)]
    SN += roll(62, 64, .3, .9, .25, 1.0) + roll(94, 96, .3, 1.0, .25, 1.0)
    toms = [k_tom(sg.r("t", i), f) for i, f in enumerate((260, 200, 150, 110))]
    for i, b in enumerate((30.5, 30.75, 31, 31.25)):
        sg.hits(toms[i], [(b, .8)], pan=(-.3, -.1, .1, .3)[i], gain=.4)
    sg.hits(kt["kick"], K + [(31.5, .8)], gain=.30)
    sg.hits(k_snare(sg.r("sn2"), tone=220, decay=26, bright=7000), SN, gain=.24)
    sg.hits(k_shaker(sg.r("shk")), SH, pan=.35, gain=.10)
    sg.hits(blk["h"], BH, pan=-.4, gain=.3)
    sg.hits(blk["l"], BL, pan=.4, gain=.3)
    sg.hits(k_clap(sg.r("clap")), CL, pan=-.1, gain=.2)
    sg.hits(kt["crash"], [(0, .7), (64, .8), (80, .5)], pan=-.3, gain=.24)
    sg.whistle(23, .9, 72, 86, .12, pan=.3)
    sg.whistle(87, .9, 72, 86, .12, pan=-.3)
    sg.whistle(31.5, .45, 84, 72, .09, pan=.2)
    sg.boing(46, 57, .3, pan=.2)
    return sg.finish()


# =============================================================== SHINSENGUMI
_SHIN_A = ("E5:.75 E5:.25 B4:.5 E5:.5 G5:1 F#5:.5 E5:.5 | G5:.75 G5:.25 E5:.5 G5:.5 C6:1 B5:.5 A5:.5 "
           "| A5:.75 A5:.25 E5:.5 A5:.5 C6:.5 B5:.5 A5:.5 G5:.5 | F#5:1.5 E5:.25 D#5:.25 B4:1 R:1 "
           "| E5:.75 E5:.25 B4:.5 E5:.5 G5:1 A5:.5 B5:.5 | C6:1.5 B5:.5 A5:.5 G5:.5 E5:1 "
           "| A5:.75 G5:.25 F#5:.5 E5:.5 D#5:.75 E5:.25 F#5:.5 A5:.5 | B5:1 G5:.5 F#5:.5 E5:2")
_SHIN_B = ("B5:1.5 A5:.5 G5:1 D5:1 | F#5:1.5 E5:.5 D5:1 A5:1 | G5:1.5 A5:.5 B5:1 C6:1 | B5:2 A5:1 F#5:1 "
           "| D6:1.5 C6:.5 B5:1 G5:1 | A5:1.5 B5:.5 A5:1 F#5:1 | E5:.75 F#5:.25 G5:.5 A5:.5 B5:.75 C6:.25 D6:1 "
           "| D#6:1.5 B5:.5 F#5:1 A5:1")


@track("shinsengumi")
def shinsengumi():
    """E minor march, 120 bpm, 20 bars: intro (taiko + horn stabs, then B7 snare
    roll + bugle call), A theme (dotted march rhythm, Em C Am B7), B heroic lift in
    G (G D C B7) with harmony + pad, tag Em -> B7 taiko fill -> bar 1."""
    sg = Song("shinsengumi", 120, 20, tail=4.0)
    chs = CH("Em | B7 | Em | C | Am | B7 | Em | C | Am B7 | Em | G | D | C | B7 | G | D | C D | B7 | Em | B7")
    lead = (S("B4:.75 B4:.25 B4:.5 E5:.5 F#5:1 D#5:1", 2, vel=.8)
            + S(_SHIN_A, 3, vel=.88) + S(_SHIN_B, 11, vel=.92)
            + S("G5:.75 G5:.25 F#5:.5 E5:.5 B4:1 E5:1 | F#5:2! R:2", 19, vel=.88))
    sg.voice(lead, I(wave="pulse", duty=.25, a=.004, d=.1, s=.75, r=.06, gain=.25, vib=.12, vib_delay=.2,
                     gate=.88, lpf=7000), pan=-.12, echo=(.75, .3, .2), key="lead")
    har = _harmony(_evsub(lead, 24, 40) + _evsub(lead, 40, 72) + _evsub(lead, 72, 76), chs, min_dur=.45)
    sg.voice(har, I(wave="pulse", duty=.5, a=.004, d=.12, s=.6, r=.06, gain=.13, gate=.88, lpf=4500),
             pan=.3, key="har")

    horn = I(wave="pulse", duty=.5, a=.006, d=.25, s=.45, r=.1, gain=.075, gate=.9, lpf=1800)
    stabs = [dict(b=0, d=1.0, m=[52, 59, 64], v=1.0), dict(b=1.5, d=.4, m=[52, 59, 64], v=.8),
             dict(b=2, d=1.5, m=[52, 59, 64], v=.95)]
    stabs += _power(chs, {4: [(0, .5, 1.0)], 2: [(0, .5, .9)]}, 47, .9, b0=8, b1=40)
    stabs += _power(chs, {4: [(0, .5, 1.0)]}, 47, .9, b0=72, b1=80)
    sg.voice(stabs, horn, pan=.2, key="horn")
    pad = _comp(chs, {0: "hold"}, 55, 69, .8, b0=40, b1=72)
    sg.voice(pad, I(wave="pad", a=.25, d=1.0, s=.9, r=.4, gain=.07, gate=1.0, lpf=2200), pan=-.2, key="pad")

    pat_a = {4: [(0, .8, "R", 1), (1, .8, "5", .8), (2, .8, "8", .9), (3, .8, "W", .85)],
             2: [(0, .8, "R", 1), (1, .8, "W", .85)]}
    pat8 = {4: [(k * .5, .42, "8" if k in (2, 6) else "R", 1.0 if k % 2 == 0 else .75) for k in range(8)],
            2: [(k * .5, .42, "8" if k == 2 else "R", 1.0 if k % 2 == 0 else .75) for k in range(4)]}
    intro = [dict(b=k * .5, d=.42, m=40, v=.5 + .5 * k / 7) for k in range(8)]
    intro += [dict(b=4 + k * .5, d=.42, m=35 if k % 4 else 47, v=.6 + .4 * k / 7) for k in range(8)]
    bass = intro + _bassline(chs, pat_a, 35, b0=8, b1=40) + _bassline(chs, pat8, 35, b0=40, b1=72) \
        + _bassline(chs, pat_a, 35, b0=72, b1=80)
    sg.voice(bass, I(wave="tri", a=.003, d=.12, s=.8, r=.04, gain=.42, gate=.85, steps=16, lpf=3500), key="bass")

    kt = _kit(sg)
    taiko = k_taiko(sg.r("taiko"), f0=110, f1=58, dur=.9, decay=4.5)
    K, SN, TK, HH, CR = [], [], [], [], []
    TK += pat("X.....x.X.......", 1) + pat("X.......X...x.X.", 2)
    SN += roll(3, 4, .12, .35, .125) + roll(4, 8, .15, 1.0, .125, 1.6)
    for bar in range(3, 21):
        if 11 <= bar <= 18:
            TK += pat("X...x...X...x...", bar)
            SN += pat("X.xxX.x.X.xxXrX.", bar)
            HH += pat("x.x.x.x.x.x.x.x.", bar)
            K += pat("X...x...X...x...", bar)
        else:
            TK += pat("X.......X.......", bar)
            SN += pat("X.xoX.x.X.xoXrX.", bar)
            K += pat("x...x...x...x...", bar)
    for bar, snp, tkp in [(6, "X.xoX.x.X.rrXXXX", None), (10, "X.xoX.x.X...rrrr", "X.......X.X.XXXX"),
                          (18, "X.xxX.x.rrrrrrrr", None), (20, "X.......X.X.XXXX", "X.......X.X.XXXX")]:
        b0 = (bar - 1) * 4
        SN = [h for h in SN if not (b0 <= h[0] < b0 + 4)] + pat(snp, bar)
        if tkp:
            TK = [h for h in TK if not (b0 <= h[0] < b0 + 4)] + pat(tkp, bar)
    CR += [(8, 1.0), (24, .7), (40, .9), (56, .7), (72, .8)]
    sg.hits(taiko, TK, gain=.38)
    sg.hits(kt["kick"], K, gain=.26)
    sg.hits(k_snare(sg.r("sn2"), tone=200, decay=20, bright=9000), SN, pan=-.1, gain=.34)
    sg.hits(kt["hat"], HH, pan=.3, gain=.1)
    sg.hits(kt["crash"], CR, pan=-.3, gain=.26)
    sg.hits(kt["crash2"], [(8, .8), (40, .7)], pan=.4, gain=.22)
    return sg.finish()


# ==================================================================== ENDING
_END_VERSE = ("R:.5 D5:.5 G5:.5 F#5:.5 E5:.5 D5:1.5 | R:.5 B4:.5 E5:.5 D5:.5 B4:.5 G4:1.5 "
              "| R:.5 C5:.5 E5:.5 G5:.5 B5:1 A5:.5 G5:.5 | F#5:1.5 E5:.5 D5:1 D5:.5 E5:.5")
_END_CHORUS = ("G5:1 G5:.5 A5:.5 B5:1 G5:1 | A5:1.5 G5:.5 F#5:1 D5:1 | F#5:1 F#5:.5 G5:.5 A5:1 F#5:.5 E5:.5 "
               "| D5:1.5 E5:.5 B4:2 | C5:.5 E5:.5 A5:1.5 G5:.5 E5:1 | F#5:1 A5:.5 D6:1.5 C6:1 "
               "| B5:1.5 A5:.5 G5:1 D5:1 | E5:.5 G#5:.5 B5:1.5 A5:.5 G#5:1")
_END_BRIDGE = "A5:1.5 G5:.5 E5:1 C5:1 | D5:1.5 E5:.5 F#5:1 A5:1 | G5:1.5 A5:.5 B5:1 C6:1 | D6:2 C6:1 A5:1"
_END_CHORUS2 = ("G5:1 G5:.5 A5:.5 B5:1 G5:1 | A5:1.5 G5:.5 F#5:1 D5:1 | F#5:1 A5:1 G#5:1 B5:1 "
                "| C6:1.5 B5:.5 A5:1 F#5:1 | G5:3 R:1 | R:1 F5:.5 E5:.5 D5:1 B4:1")


@track("ending")
def ending():
    """G major, 120 bpm, 24 bars: intro (music-box bell previews the chorus
    motif over Cmaj7-D), verse (G Em7 Cmaj7 D), chorus on the IV-V-iii-vi
    'royal road' (Cmaj7 D Bm7 Em7 Am7 D7 G E7), bridge (Am7 Bm7 Cmaj7 Dsus4-D),
    last chorus with bell descant, cadence G then Dm7-G7 back into Cmaj7."""
    sg = Song("ending", 120, 24, tail=4.0)
    chs = CH("Cmaj7 | D | G | Em7 | Cmaj7 | D | Cmaj7 | D | Bm7 | Em7 | Am7 | D7 | G | E7 "
             "| Am7 | Bm7 | Cmaj7 | Dsus4 D | Cmaj7 | D | Bm7 E7 | Am7 D | G | Dm7 G7")
    lead = (S(_END_VERSE, 3, vel=.72) + S(_END_CHORUS, 7, vel=.86) + S(_END_BRIDGE, 15, vel=.8)
            + S(_END_CHORUS2, 19, vel=.9))
    sg.voice(lead, I(wave="pulse", duty=.5, a=.015, d=.3, s=.7, r=.12, gain=.24, vib=.13, vib_rate=5.0,
                     vib_delay=.25, gate=.93, lpf=4200), pan=-.12, echo=(.75, .3, .25), key="lead")
    har = _harmony(_evsub(lead, 24, 56) + _evsub(lead, 72, 88), chs, min_dur=.45)
    sg.voice(har, I(wave="pulse", duty=.25, a=.015, d=.3, s=.6, r=.12, gain=.11, gate=.93, lpf=3500),
             pan=.3, key="har")
    bells = S("G5:1 G5:.5 A5:.5 B5:2 | A5:1.5 G5:.5 F#5:2", 1, vel=.8) \
        + S("E6:4 | F#6:4 | D6:2 D6:2 | E6:2 D6:2", 19, vel=.55)
    sg.voice(bells, I(wave="bell", a=.002, d=10, s=1, r=.3, gain=.2, gate=1.0, partials=GLOCK, lpf=7000),
             pan=.2, echo=(.75, .35, .3), key="bell")

    arp = _arp(chs, [0, 1, 2, 3, 4, 3, 2, 1], .5, 55, 5, .6, gate=.8, b0=0, b1=56) \
        + _arp(chs, [0, 2, 1, 3, 2, 4, 3, 1], .5, 55, 5, .6, gate=.8, b0=56, b1=72) \
        + _arp(chs, [0, 1, 2, 3, 4, 3, 2, 1], .5, 55, 5, .6, gate=.8, b0=72, b1=96)
    sg.voice(arp, I(wave="pulse", duty=.125, a=.003, d=.28, s=.05, r=.1, gain=.085, lpf=5000),
             pan=.35, echo=(.75, .25, .2), key="arp")
    pad = _comp(chs, {0: "hold"}, 52, 67, .8)
    _shape(pad, lambda b: 1.3 if (b < 8 or 56 <= b < 72) else 1.0)
    sg.voice(pad, I(wave="pad", a=.3, d=1.0, s=.9, r=.5, gain=.06, gate=1.0, lpf=2000), pan=-.25, key="pad")

    bpat = {4: [(0, 1.4, "R", 1), (1.5, .45, "R", .75), (2, .9, "5", .85), (3, .45, "W", .7), (3.5, .45, "A", .8)],
            2: [(0, .9, "R", 1), (1, .45, "W", .8), (1.5, .45, "A", .75)]}
    bass = _bassline(chs, {4: [(0, 1.9, "R", .8), (2, 1.9, "5", .7)]}, 36, b0=0, b1=8) \
        + _bassline(chs, bpat, 36, b0=8, b1=96)
    sg.voice(bass, I(wave="tri", a=.004, d=.2, s=.8, r=.06, gain=.42, gate=.9, steps=16, lpf=3000), key="bass")

    kt = _kit(sg)
    K, SN, HH, SH, CR = [], [], [], [], []
    for bar in range(1, 25):
        SH += pat("xoxoxoxoxoxoxoxo", bar)
        if bar <= 2:
            continue
        if bar <= 6:
            K += pat("X.......X.......", bar)
            SN += pat("....o.......o...", bar)
            HH += pat("x.x.x.x.x.x.x.x.", bar)
        elif 15 <= bar <= 17:
            K += pat("X.......X.......", bar)
            SN += pat("........x.......", bar)
            HH += pat("x...x...x...x...", bar)
        elif bar == 23:
            K += pat("X.......X.......", bar)
            HH += pat("x.x.x.x.x.x.x.x.", bar)
        elif bar == 24:
            K += pat("X.......", bar)
            SN += pat("....o.......o.oo", bar)
            HH += pat("x.x.x.x.x.x.....", bar)
        else:
            K += pat("X......xX.......", bar)
            SN += pat("....X.......X...", bar)
            HH += pat("x.x.x.x.x.x.x.x.", bar)
    for bar, snp in [(6, "....o.......xxxx"), (14, "....X.....x.XxXx"), (18, "X...X...XxXxXXXX")]:
        b0 = (bar - 1) * 4
        SN = [h for h in SN if not (b0 <= h[0] < b0 + 4)] + pat(snp, bar)
    CR += [(24, .8), (40, .5), (72, .8), (88, .5)]
    sg.hits(kt["kick"], K, gain=.45)
    sg.hits(k_snare(sg.r("sn2"), tone=200, decay=20, bright=7000), SN, gain=.26)
    sg.hits(k_clap(sg.r("clap")), [h for h in SN if h[1] >= .9], pan=.1, gain=.12)
    sg.hits(kt["hat"], HH, pan=.3, gain=.09)
    sg.hits(k_shaker(sg.r("shk")), SH, pan=-.35, gain=.05)
    sg.hits(kt["crash"], CR, pan=-.3, gain=.2)
    return sg.finish()
