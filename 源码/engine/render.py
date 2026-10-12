"""Frame rendering + ffmpeg encoding."""
import importlib
import os
import pkgutil
import subprocess
import sys
import time
import traceback

from PIL import Image

from .core import W, H, FPS, SCALE, clamp
from .text import draw_subs
from .fx import fade

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def scene_modules():
    d = os.path.join(ROOT, "scenes")
    mods = [m.name for m in pkgutil.iter_modules([d]) if m.name[:1] == "s" and m.name[1:3].isdigit()]
    return sorted(mods)


def load_scene(sid):
    """sid: 's03' or full module name 's03_kagura'."""
    for m in scene_modules():
        if m == sid or m.split("_")[0] == sid:
            mod = importlib.import_module(f"scenes.{m}")
            return mod.SCENE
    try:
        return importlib.import_module(f"scenes.{sid}").SCENE
    except ModuleNotFoundError:
        pass
    raise KeyError(f"no scene {sid!r}; have {scene_modules()}")


def load_scenes(ids=None):
    out = []
    for m in scene_modules():
        if ids and m.split("_")[0] not in ids and m not in ids:
            continue
        mod = importlib.import_module(f"scenes.{m}")
        out.append(mod.SCENE)
    return out


def n_frames(scene):
    return int(round(scene.duration * FPS))


def render_frame(scene, t, subs=True):
    img = Image.new("RGB", (W, H), (0, 0, 0))
    scene.render(img, t)
    if img.size != (W, H) or img.mode != "RGB":
        img = img.convert("RGB").resize((W, H), Image.NEAREST)
    if subs and getattr(scene, "subs", None):
        draw_subs(img, t, scene.subs, getattr(scene, "subs_pos", "bottom"))
    fi, fo = getattr(scene, "fade_in", 0.3), getattr(scene, "fade_out", 0.3)
    if fi and t < fi:
        fade(img, 1 - t / fi)
    if fo and t > scene.duration - fo:
        fade(img, clamp((t - (scene.duration - fo)) / fo))
    return img


def ffmpeg_writer(path, scale=SCALE, fps=FPS, crf=16, preset="medium"):
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
        "-vf", f"scale={W * scale}:{H * scale}:flags=neighbor",
        "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
        "-tune", "animation", "-threads", "3", "-x264-params", "rc-lookahead=20", path,
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def render_scene_video(sid, path, scale=SCALE, strict=False):
    scene = load_scene(sid) if isinstance(sid, str) else sid
    nf = n_frames(scene)
    proc = ffmpeg_writer(path, scale)
    t0 = time.time()
    errors = 0
    for i in range(nf):
        t = i / FPS
        try:
            img = render_frame(scene, t)
        except Exception:
            errors += 1
            if strict:
                proc.stdin.close()
                proc.wait()
                raise
            if errors <= 3:
                print(f"[render] {scene.id} frame {i} (t={t:.2f}) failed:")
                traceback.print_exc()
            img = Image.new("RGB", (W, H), (255, 0, 255))
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    proc.wait()
    dt = time.time() - t0
    print(f"[render] {scene.id} {nf} frames in {dt:.1f}s -> {path} (errors={errors})")
    return errors


def mux(video_paths, audio_path, out_path):
    lst = out_path + ".txt"
    with open(lst, "w", encoding="utf-8") as f:
        for v in video_paths:
            f.write(f"file '{os.path.abspath(v).replace(os.sep, '/')}'\n")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst]
    if audio_path:
        cmd += ["-i", audio_path, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "copy", "-movflags", "+faststart", out_path]
    subprocess.run(cmd, check=True)
    os.remove(lst)
    return out_path
