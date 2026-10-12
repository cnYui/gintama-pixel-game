"""Full build: render every scene in parallel, mix the soundtrack, mux.

    python main.py                 -> out/gintama_pixel.mp4
    python main.py s00 s01         -> only those scenes (quick partial build)
    python main.py --jobs 8
"""
import argparse
import os
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _render_one(args):
    mod_id, path = args
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from engine.render import render_scene_video
    return mod_id, render_scene_video(mod_id, path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--jobs", type=int, default=10)
    ap.add_argument("--out", default="out/gintama_pixel.mp4")
    a = ap.parse_args()
    from engine.render import load_scenes, mux, scene_modules
    from engine.audio import build_mix

    os.makedirs("build/video", exist_ok=True)
    os.makedirs("out", exist_ok=True)
    scenes = load_scenes(a.ids or None)
    ids = [s.id for s in scenes]
    total = sum(s.duration for s in scenes)
    print(f"{len(scenes)} scenes, {total:.1f}s: {ids}")
    t0 = time.time()
    jobs = [(sid, f"build/video/{sid}.mp4") for sid in ids]
    # longest scenes first for better packing
    dur = {s.id: s.duration for s in scenes}
    jobs.sort(key=lambda j: -dur[j[0]])
    with Pool(min(a.jobs, len(jobs))) as pool:
        for sid, errs in pool.imap_unordered(_render_one, jobs):
            print(f"  done {sid} errors={errs}")
    print(f"video rendered in {time.time() - t0:.1f}s")
    wav = "build/soundtrack.wav"
    build_mix(scenes, wav)
    print("audio mixed")
    mux([f"build/video/{sid}.mp4" for sid in ids], wav, a.out)
    print(f"DONE -> {a.out}  ({time.time() - t0:.1f}s)")
