"""生成压缩后的运行时素材目录，保留原始游戏文件不变。"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist-compressed"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def runtime_refs() -> set[str]:
    raw = (ROOT / "data.js").read_text(encoding="utf-8")
    data = json.loads(raw[len("window.GAME_DATA = ") :].strip().rstrip(";"))
    refs: set[str] = set()

    def walk(value: object) -> None:
        if isinstance(value, str) and re.search(r"\.(png|mp3|mp4|webm|json|woff2?)$", value, re.I):
            if not value.startswith(("http", "data:")):
                refs.add(value)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)

    walk(data)
    return refs


def optimize_png(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        rgba = image.convert("RGBA")
        colors = rgba.getcolors(maxcolors=257)
        if colors is not None and len(colors) <= 256:
            rgba = rgba.quantize(colors=256, method=Image.Quantize.FASTOCTREE).convert("RGBA")
        rgba.save(target, format="PNG", optimize=True)


def compress_audio(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    # 标题曲保留较高码率，其余音乐和音效优先压缩体积。
    bitrate = "64k" if source.name == "title_song.mp3" else "64k"
    sample_rate = "44100" if source.name == "title_song.mp3" else "32000"
    run(["ffmpeg", "-y", "-i", str(source), "-ac", "1", "-ar", sample_rate, "-b:a", bitrate, str(target)])


def compress_video(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix.lower() == ".mp4":
        run(["ffmpeg", "-y", "-i", str(source), "-vf", "scale=640:-2", "-c:v", "libx264", "-crf", "30", "-preset", "slow", "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart", str(target)])
    else:
        run(["ffmpeg", "-y", "-i", str(source), "-vf", "scale=640:-2", "-c:v", "libvpx-vp9", "-crf", "38", "-b:v", "0", "-c:a", "libopus", "-b:a", "48k", str(target)])


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for relative in sorted(runtime_refs()):
        source = ROOT / relative
        target = OUT / relative
        if not source.exists():
            raise FileNotFoundError(source)
        suffix = source.suffix.lower()
        if suffix == ".png":
            optimize_png(source, target)
        elif suffix == ".mp3":
            compress_audio(source, target)
        elif suffix in {".mp4", ".webm"}:
            compress_video(source, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for name in ["index.html", "main.js", "data.js"]:
        shutil.copy2(ROOT / name, OUT / name)
    for directory in ["engine", "story"]:
        shutil.copytree(ROOT / directory, OUT / directory)
    print(f"输出: {OUT}")


if __name__ == "__main__":
    main()
