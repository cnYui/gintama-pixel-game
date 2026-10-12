"""Scene preview / QA tool.

  python preview.py s03                 contact sheet (1 frame / 1.0 s) -> build/preview/s03_sheet.png
  python preview.py s03 --step 0.5      denser sheet
  python preview.py s03 --range 4 9     sheet only for 4s..9s
  python preview.py s03 --at 2.5 7      single frames at 3x -> build/preview/s03_t2.50.png ...
  python preview.py s03 --check         render every frame (no encode): errors + ms/frame
  python preview.py s03 --video         mp4 with audio -> build/preview/s03.mp4
"""
import argparse
import os
import subprocess
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw  # noqa: E402

from engine.core import W, H, FPS  # noqa: E402
from engine.render import load_scene, render_frame, render_scene_video, n_frames  # noqa: E402
from engine.text import draw_text  # noqa: E402

OUT = "build/preview"


def sheet(scene, step, cols, rng=None, scale=1):
    t0, t1 = rng if rng else (0.0, scene.duration)
    ts = []
    t = t0
    while t < t1 - 1e-6:
        ts.append(round(t, 3))
        t += step
    rows = (len(ts) + cols - 1) // cols
    cw, chh = W * scale + 4, H * scale + 4
    img = Image.new("RGB", (cols * cw, rows * chh), (40, 40, 40))
    for i, tt in enumerate(ts):
        fr = render_frame(scene, tt)
        if scale != 1:
            fr = fr.resize((W * scale, H * scale), Image.NEAREST)
        r, c = divmod(i, cols)
        img.paste(fr, (c * cw + 2, r * chh + 2))
        draw_text(img, c * cw + 4, r * chh + 4, f"{tt:.2f}s", (255, 255, 0), outline=(0, 0, 0))
    suffix = f"_{t0:g}-{t1:g}" if rng else ""
    path = f"{OUT}/{scene.id}_sheet{suffix}.png"
    img.save(path)
    print(path)


def frames_at(scene, ts, scale=3):
    for tt in ts:
        fr = render_frame(scene, tt).resize((W * scale, H * scale), Image.NEAREST)
        path = f"{OUT}/{scene.id}_t{tt:.2f}.png"
        fr.save(path)
        print(path)


def check(scene):
    nf = n_frames(scene)
    errs = 0
    t0 = time.time()
    for i in range(nf):
        try:
            render_frame(scene, i / FPS)
        except Exception:
            errs += 1
            if errs <= 3:
                print(f"frame {i} t={i / FPS:.2f} FAILED")
                traceback.print_exc()
    dt = time.time() - t0
    print(f"{scene.id}: {nf} frames, {errs} errors, {dt / nf * 1000:.1f} ms/frame, duration {scene.duration}s")
    try:
        cues = scene.cues()
        from engine import audio
        audio.load()
        unknown = sorted({c.name for c in cues if c.name not in audio.SFX_REGISTRY})
        print(f"cues: {len(cues)}; unknown sfx names: {unknown if audio.SFX_REGISTRY else '(sfx module not loaded yet)'}")
        if isinstance(scene.music, str) or scene.music is None:
            tracks = [scene.music]
        else:
            tracks = [m[1] for m in scene.music]
        unk_t = [m for m in tracks if m and m not in audio.MUSIC_REGISTRY]
        print(f"music: {tracks}; unknown tracks: {unk_t if audio.MUSIC_REGISTRY else '(music module not loaded yet)'}")
    except Exception:
        traceback.print_exc()
    return errs


def video(scene, scale=3):
    from engine.audio import build_mix
    v = f"{OUT}/{scene.id}_v.mp4"
    a = f"{OUT}/{scene.id}.wav"
    out = f"{OUT}/{scene.id}.mp4"
    render_scene_video(scene, v, scale=scale)
    build_mix([scene], a)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", v, "-i", a, "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
    os.remove(v)
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--step", type=float, default=1.0)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--range", type=float, nargs=2)
    ap.add_argument("--at", type=float, nargs="+")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--video", action="store_true")
    ap.add_argument("--scale", type=int, default=1)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    sc = load_scene(a.scene)
    if a.check:
        sys.exit(1 if check(sc) else 0)
    elif a.at:
        frames_at(sc, a.at)
    elif a.video:
        video(sc)
    else:
        sheet(sc, a.step, a.cols, a.range, a.scale)
