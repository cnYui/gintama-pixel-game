"""把分段录屏（record_all.py 的输出）拼成一条 1080p60 mp4：每段裁到篇章卡那一刻接上，章节嵌进文件。

用法：python tools/join_chunks.py <录制根目录> <输出.mp4>
  每段目录里要有 full.webm 和 run.json；段名按字母序拼（A_ B_ C_ D_）。
  段与段的接口：上一段在下一章篇章卡出现时停（playtest 的 --until 会等到那一刻），下一段从自己的篇章卡开始；
  这里再按 run.json 里的篇章卡时间点裁一次，保证不重不漏。
  画面 384×216 最近邻放大 5 倍到 1920×1080，60 帧，AAC 192k；中间的分段 mp4 拼完就删。
"""
import json
import os
import subprocess
import sys


def run(*args):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args]
    print(" ".join(cmd)[:240], flush=True)
    subprocess.run(cmd, check=True)


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                capture_output=True, text=True).stdout.strip())


def main(root, out):
    chunks = sorted(d for d in os.listdir(root) if not d.startswith("_") and os.path.exists(os.path.join(root, d, "run.json")))   # _ 开头的是旧版 / 中间文件
    runs = [json.load(open(os.path.join(root, d, "run.json"), encoding="utf-8")) for d in chunks]
    chap = [[(t, label) for t, label, kind in r["marks"] if kind == "chapter"] for r in runs]
    work = os.path.join(root, "_拼接中间文件")
    os.makedirs(work, exist_ok=True)
    parts, marks, offset = [], [], 0.0
    for i, d in enumerate(chunks):
        # 起点：第一段从 0（带标题画面），后面的从自己的篇章卡；终点：下一段的第一章篇章卡在这一段里出现的时刻
        start = 0.0 if i == 0 else chap[i][0][0]
        end = None
        if i + 1 < len(chunks):
            nxt = chap[i + 1][0][1]
            hit = [t for t, label in chap[i] if label == nxt]
            end = hit[0] if hit else None
        part = os.path.join(work, "%02d.mp4" % i)
        cmd = ["-ss", "%.3f" % start] + (["-to", "%.3f" % end] if end else []) + ["-i", os.path.join(root, d, "full.webm"),
               "-vf", "scale=1920:1080:flags=neighbor", "-r", "60", "-fps_mode", "cfr",
               "-c:v", "libx264", "-preset", "faster", "-crf", "18", "-pix_fmt", "yuv420p",
               "-af", "aresample=async=1:first_pts=0", "-c:a", "aac", "-b:a", "192k", part]
        run(*cmd)
        dur = duration(part)
        if i == 0:
            marks.append((0.0, "标题画面"))
        for t, label, kind in runs[i]["marks"]:
            if kind in ("chapter", "end") and t >= start - 0.01 and (end is None or t < end - 0.01):
                marks.append((offset + t - start, label if kind == "chapter" else "全剧终画面"))
        parts.append(part)
        print("[%s] 裁 %.1f–%s  → %.1f 秒" % (d, start, "%.1f" % end if end else "结尾", dur), flush=True)
        offset += dur
    lst = os.path.join(work, "list.txt")
    with open(lst, "w", encoding="utf-8") as fh:
        for p in parts:
            fh.write("file '%s'\n" % p.replace("\\", "/"))
    meta = os.path.join(work, "chapters.ffmeta")
    with open(meta, "w", encoding="utf-8") as fh:
        fh.write(";FFMETADATA1\n")
        for k, (t, label) in enumerate(marks):
            e = marks[k + 1][0] if k + 1 < len(marks) else offset
            fh.write("[CHAPTER]\nTIMEBASE=1/1000\nSTART=%d\nEND=%d\ntitle=%s\n" % (t * 1000, max(e, t + 0.1) * 1000, label))
    run("-f", "concat", "-safe", "0", "-i", lst, "-i", meta, "-map", "0", "-map_metadata", "1", "-map_chapters", "1", "-c", "copy",
        "-movflags", "+faststart", out)
    with open(os.path.join(os.path.dirname(out), "章节时间点.txt"), "w", encoding="utf-8") as fh:
        fh.write("时间点从视频的 0 秒算起（章节也嵌在 mp4 里，播放器里能直接跳）。\n\n")
        for t, label in marks:
            fh.write("%02d:%02d:%04.1f  %s\n" % (t // 3600, t % 3600 // 60, t % 60, label))
        fh.write("%02d:%02d:%04.1f  （结束）\n" % (offset // 3600, offset % 3600 // 60, offset % 60))
    for p in parts + [lst, meta]:
        os.remove(p)
    os.rmdir(work)
    print("done:", out, "%.1f 秒" % duration(out), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
