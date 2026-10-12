"""Audio registry + final mixer.

audio/sfx.py registers sound effects:     @sfx("slash") def _(): return mono_or_stereo_buffer
audio/music.py registers music tracks:     @track("battle") def _(): return stereo_buffer (seamless loop)

The mixer lays out every scene back-to-back, plays the music timeline with
crossfades, ducks music under dialogue, drops SFX cues, and auto-generates
typewriter 'blip' voices for dialogue subtitles.
"""
import importlib
import math
import traceback
import wave

import numpy as np

from .core import FPS
from .synth import SR, n_samples, place, stereo, resample, soft_clip, pad_to

SFX_REGISTRY = {}
SFX_LOOP = set()
MUSIC_REGISTRY = {}
_cache_sfx = {}
_cache_music = {}
_loaded = False


def sfx(name, loop=False):
    def deco(fn):
        SFX_REGISTRY[name] = fn
        if loop:
            SFX_LOOP.add(name)
        return fn
    return deco


def track(name):
    def deco(fn):
        MUSIC_REGISTRY[name] = fn
        return fn
    return deco


def load():
    global _loaded
    if _loaded:
        return
    _loaded = True
    for mod in ("audio.sfx", "audio.music"):
        try:
            importlib.import_module(mod)
        except ModuleNotFoundError as e:
            print(f"[audio] {mod} not found ({e})")
        except Exception:
            print(f"[audio] failed to import {mod}")
            traceback.print_exc()


def get_sfx(name):
    load()
    if name not in _cache_sfx:
        fn = SFX_REGISTRY.get(name)
        if fn is None:
            print(f"[audio] WARNING unknown sfx {name!r}")
            _cache_sfx[name] = None
        else:
            buf = np.asarray(fn(), np.float32)
            _cache_sfx[name] = buf
    return _cache_sfx[name]


def get_track(name):
    load()
    if name not in _cache_music:
        fn = MUSIC_REGISTRY.get(name)
        if fn is None:
            print(f"[audio] WARNING unknown music track {name!r}")
            _cache_music[name] = None
        else:
            buf = np.asarray(fn(), np.float32)
            if buf.ndim == 1:
                buf = np.stack([buf, buf], 1)
            _cache_music[name] = buf
    return _cache_music[name]


def _loop_to(buf, n, offset=0):
    if buf is None or len(buf) == 0:
        return np.zeros((n, 2), np.float32)
    reps = (offset + n) // len(buf) + 2
    tiled = np.concatenate([buf] * reps, 0)
    return tiled[offset:offset + n]


def _fade(n, fin, fout):
    env = np.ones(n, np.float32)
    a, b = min(n, n_samples(fin)) if fin > 0 else 0, min(n, n_samples(fout)) if fout > 0 else 0
    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    if b > 0:
        env[n - b:] *= np.linspace(1, 0, b)
    return env


def _music_events(scenes, starts):
    ev = []
    for sc, st in zip(scenes, starts):
        m = sc.music
        vol = getattr(sc, "music_vol", 0.55)
        if isinstance(m, (list, tuple)) and m and isinstance(m[0], (list, tuple)):
            if m[0][0] > 0:
                ev.append((st, "__keep__", vol))
            for tt, tr in m:
                ev.append((st + tt, tr, vol))
        else:
            ev.append((st, m, vol))
    return ev


def build_mix(scenes, out_path, blips=True, duck=0.6):
    """Render the complete soundtrack for `scenes` (in order) to a WAV file."""
    load()
    from .text import CPS
    starts, t = [], 0.0
    for sc in scenes:
        starts.append(t)
        t += sc.duration
    total = n_samples(t) + SR
    master = np.zeros((total, 2), np.float32)
    music_bus = np.zeros((total, 2), np.float32)

    # ---- music timeline -------------------------------------------------
    ev = _music_events(scenes, starts)
    segs = []  # [start_t, track, vols(list of (t,vol))]
    cur = None
    for (et, tr, vol) in ev:
        if tr == "__keep__":
            if cur:
                cur[2].append((et, vol))
            continue
        if cur and cur[1] == tr:
            cur[2].append((et, vol))
            continue
        if cur:
            cur[3] = et
        cur = [et, tr, [(et, vol)], None]
        segs.append(cur)
    if cur:
        cur[3] = t
    for s0, tr, vols, s1 in segs:
        if tr is None:
            continue
        buf = get_track(tr)
        if buf is None:
            continue
        fout = 0.6
        n = n_samples(s1 - s0 + fout)
        x = _loop_to(buf, n)
        env = _fade(n, 0.08, fout)
        # per-scene volume envelope (smooth steps)
        vt = np.array([v[0] - s0 for v in vols] + [s1 - s0 + 10])
        vv = np.array([v[1] for v in vols] + [vols[-1][1]])
        times = np.arange(n) / SR
        idx = np.searchsorted(vt, times, side="right") - 1
        gain = vv[np.clip(idx, 0, len(vv) - 1)].astype(np.float32)
        # smooth 150ms
        k = n_samples(0.15)
        if len(gain) > k:
            c = np.cumsum(np.concatenate([[0], gain]))
            sm = (c[k:] - c[:-k]) / k
            gain[k - 1:] = sm
        x = x * (env * gain)[:, None]
        place(music_bus, x, n_samples(s0))

    # ---- dialogue ducking + blips ---------------------------------------
    duck_env = np.ones(total, np.float32)
    for sc, st in zip(scenes, starts):
        for sub in getattr(sc, "subs", []):
            t0, t1, spk, text = sub[:4]
            if spk is not None:
                a, b = n_samples(st + t0), n_samples(st + t1)
                duck_env[a:b] = duck
            if blips:
                voice = 1.0
                if spk is not None:
                    try:
                        from chars import get_def
                        d = get_def(spk)
                        voice = d.voice if d is not None else 1.0
                    except Exception:
                        pass
                name = "blip" if spk is not None else "type"
                every = 2 if spk is not None else 3
                vol = 0.30 if spk is not None else 0.10
                g = get_sfx(name)
                if g is None:
                    continue
                t_start = t0 + (0.08 if spk is not None else 0.0)
                cps = CPS if spk is not None else CPS * 1.1
                for i, ch in enumerate(text):
                    if i % every or ch in " ，。！？…、,.!?~—「」『』()（）\n":
                        continue
                    tt = t_start + i / cps
                    if tt >= t1 - 0.1:
                        break
                    jitter = 1.0 + 0.06 * math.sin(i * 12.9898)
                    buf = resample(g, voice * jitter)
                    place(master, stereo(buf) * vol, n_samples(st + tt))
    k = n_samples(0.12)
    c = np.cumsum(np.concatenate([[0], duck_env]))
    duck_s = duck_env.copy()
    duck_s[k - 1:] = (c[k:] - c[:-k]) / k
    master += music_bus * duck_s[:, None]

    # ---- sfx cues -------------------------------------------------------
    for sc, st in zip(scenes, starts):
        try:
            cues = sc.cues() or []
        except Exception:
            traceback.print_exc()
            cues = []
        for cue in cues:
            g = get_sfx(cue.name)
            if g is None:
                continue
            buf = resample(g, cue.pitch) if cue.pitch != 1.0 else g
            if cue.name in SFX_LOOP and cue.dur:
                n = n_samples(cue.dur)
                if buf.ndim == 1:
                    buf = np.stack([buf, buf], 1)
                buf = _loop_to(buf, n) * _fade(n, 0.3, 0.5)[:, None]
            place(master, stereo(buf, cue.pan) * cue.vol, n_samples(st + cue.time))

    master = master[: n_samples(t)]
    peak = float(np.max(np.abs(master))) or 1.0
    master = soft_clip(master * (0.95 / max(peak, 0.95)) * 1.1) * 0.93
    write_wav(out_path, master)
    return out_path


def write_wav(path, stereo_buf):
    x = np.clip(stereo_buf, -1, 1)
    pcm = (x * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
