"""把 playtest.py --record 录下来的 webm（浏览器录的，Windows 播放器 / 剪辑软件不好开）转成 mp4，直接能看。

用法：python tools/webm_to_mp4.py <录制目录> [输出.mp4]
  录制目录里要有 full.webm（画面 + 混好的声音）；有 run.json 就按里面的 marks 嵌章节，没有就按画面里的篇章卡认章节。
输出：全程实录_1080p60.mp4（384×216 最近邻放大 5 倍到 1920×1080，像素不糊；60 帧；AAC 192k；章节嵌在文件里）
      + 章节时间点.txt
BGM / 音效那两条（bgm.webm、sfx.webm）不动；要 wav 用 make_recording.py。
"""
import io
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(os.path.dirname(HERE), "assets", "ui")
CARDS = ["prologue"] + ["ch%d" % i for i in range(1, 15)]
NAMES = ["序章　白夜叉", "第一章　万事屋阿银", "第二章　新八登场", "第三章　神乐与定春", "第四章　真选组", "第五章　桂与伊丽莎白",
         "第六章　日常", "第七章　红樱篇", "第八章　真选组动乱篇", "第九章　吉原炎上篇", "第十章　将军暗杀篇", "第十一章　松阳老师",
         "第十二章　洛阳决战·离别", "第十三章　银之魂篇", "终章　两年后"]


def run(*args, **kw):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args]
    print(" ".join(cmd), flush=True)
    return subprocess.run(cmd, check=True, **kw)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def marks_from_run_json(path):
    """run.json 的 marks：标题 / 每章 / 片尾（过场动画、战斗不进章节）。"""
    marks = json.load(open(path, encoding="utf-8")).get("marks") or []
    return [(t, label) for t, label, kind in marks if kind in ("title", "chapter", "end")]


def marks_from_cards(webm, fps=5, w=96, h=54, thr=8.0):
    """没有 run.json：每秒取 5 帧，和 15 张篇章卡图比（96×54 灰度），卡片淡入 0.35 秒，所以起点 = 第一次认出来 − 0.4 秒。"""
    cards = []
    for key in CARDS:
        im = Image.open(os.path.join(UI, "chapter_%s.png" % key)).convert("L").resize((w, h), Image.BOX)
        cards.append(np.asarray(im, np.float32))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", webm, "-vf", "fps=%d,scale=%d:%d:flags=area" % (fps, w, h),
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
    marks, last = [(0.0, "标题画面")], {}
    for i, fr in enumerate(frames):
        d = [float(np.abs(fr - c).mean()) for c in cards]
        k = int(np.argmin(d))
        if d[k] < thr:
            t = i / fps
            if k not in last or t - last[k] > 6:             # 同一张卡片连续出现 2.8 秒，只记第一次
                marks.append((max(0.0, t - 0.4), NAMES[k]))
            last[k] = t
    return marks


def main(src, out=None):
    webm = os.path.join(src, "full.webm")
    out = out or os.path.join(src, "全程实录_1080p60.mp4")
    run_json = os.path.join(src, "run.json")
    marks = marks_from_run_json(run_json) if os.path.exists(run_json) else marks_from_cards(webm)
    tmp = out[:-4] + ".tmp.mp4"
    # 声音补齐到从 0 秒开始（浏览器录的声音比画面晚开 0.07 秒左右）；画面恒定 60 帧
    run("-i", webm, "-vf", "scale=1920:1080:flags=neighbor", "-r", "60", "-fps_mode", "cfr",
        "-c:v", "libx264", "-preset", "faster", "-crf", "18", "-pix_fmt", "yuv420p",
        "-af", "aresample=async=1:first_pts=0", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp)
    total = duration(tmp)
    meta = out[:-4] + ".ffmeta"
    with open(meta, "w", encoding="utf-8") as fh:
        fh.write(";FFMETADATA1\n")
        for i, (t, label) in enumerate(marks):
            end = marks[i + 1][0] if i + 1 < len(marks) else total
            fh.write("[CHAPTER]\nTIMEBASE=1/1000\nSTART=%d\nEND=%d\ntitle=%s\n" % (t * 1000, max(end, t + 0.1) * 1000, label))
    run("-i", tmp, "-i", meta, "-map", "0", "-map_metadata", "1", "-map_chapters", "1", "-c", "copy", "-movflags", "+faststart", out)
    os.remove(tmp)
    os.remove(meta)
    with open(os.path.join(os.path.dirname(out), "章节时间点.txt"), "w", encoding="utf-8") as fh:
        fh.write("时间点从视频的 0 秒算起（章节也嵌在 mp4 里，播放器里能直接跳）。\n\n")
        for t, label in marks:
            fh.write("%02d:%02d:%04.1f  %s\n" % (t // 3600, t % 3600 // 60, t % 60, label))
        fh.write("%02d:%02d:%04.1f  （结束）\n" % (total // 3600, total % 3600 // 60, total % 60))
    print("done:", out, "%.1f s" % total, flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
