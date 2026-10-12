"""把 playtest.py --record 录下来的东西转成方便二次剪辑的文件。

用法：python tools/make_recording.py <录制目录> <输出目录>
  录制目录里有 full.webm（画面 + 混好的声音）、bgm.webm（只有背景音乐 + 开场动画原声）、sfx.webm（只有音效）、
  run.json（playtest 写的结果，里面的 marks 是每章、过场动画、片尾从第几秒开始）。
输出：
  全程实录_1080p60.mp4   画面最近邻放大 5 倍（384×216 → 1920×1080，像素不糊）+ 混好的声音；章节嵌在文件里，播放器能直接跳章
  BGM_背景音乐.wav        只有背景音乐（48 kHz 16 bit）
  音效.wav                只有音效
  章节时间点.txt          每章 / 过场动画 / 片尾从第几分第几秒开始（剪辑时好找）
三条都从同一时刻开录，拖进剪辑软件都对齐到 0 秒就是同步的。
"""
import json
import os
import subprocess
import sys


def ff(*args):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args]
    print(" ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def hms(t, frac=False):
    s = "%02d:%02d:%02d" % (t // 3600, t % 3600 // 60, t % 60)
    return s + (".%d" % (t * 10 % 10) if frac else "")


def main(src, dst):
    os.makedirs(dst, exist_ok=True)
    run = json.load(open(os.path.join(src, "run.json"), encoding="utf-8"))
    marks = run.get("marks") or []
    # 音频补齐到从 0 秒开始，三条才严格对齐
    sync = "aresample=async=1:first_pts=0"
    bgm = os.path.join(dst, "BGM_背景音乐.wav")
    ff("-i", os.path.join(src, "bgm.webm"), "-vn", "-af", sync, "-ar", "48000", "-c:a", "pcm_s16le", bgm)
    ff("-i", os.path.join(src, "sfx.webm"), "-vn", "-af", sync, "-ar", "48000", "-c:a", "pcm_s16le", os.path.join(dst, "音效.wav"))
    # 章节（标题 / 每章 / 片尾）写成 ffmetadata，嵌进 mp4（浏览器录的 webm 头里没有时长，总长从转好的 wav 读）
    meta = os.path.join(src, "chapters.ffmeta")
    chaps = [m for m in marks if m[2] in ("title", "chapter", "end")]
    total = duration(bgm)
    with open(meta, "w", encoding="utf-8") as fh:
        fh.write(";FFMETADATA1\n")
        for i, (t, label, _) in enumerate(chaps):
            end = chaps[i + 1][0] if i + 1 < len(chaps) else max(total, t + 1)
            fh.write("[CHAPTER]\nTIMEBASE=1/1000\nSTART=%d\nEND=%d\ntitle=%s\n" % (t * 1000, end * 1000, label))
    ff("-i", os.path.join(src, "full.webm"), "-i", meta, "-map", "0:v", "-map", "0:a", "-map_metadata", "1", "-map_chapters", "1",
       "-vf", "scale=1920:1080:flags=neighbor", "-r", "60", "-fps_mode", "cfr",
       "-c:v", "libx264", "-preset", "faster", "-crf", "16", "-pix_fmt", "yuv420p",
       "-af", sync, "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", os.path.join(dst, "全程实录_1080p60.mp4"))
    with open(os.path.join(dst, "章节时间点.txt"), "w", encoding="utf-8") as fh:
        fh.write("时间点从开录那一刻（= 视频和两条音轨的 0 秒）算起。缩进的是章节里的过场动画。\n\n")
        for t, label, kind in marks:
            fh.write("%s  %s%s\n" % (hms(t, frac=True), "    " if kind == "video" else "", label))
    print("done:", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
