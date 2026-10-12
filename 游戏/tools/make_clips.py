"""从 playtest.py --record 的录像里剪出素材片段（二次剪辑用）。

用法：python tools/make_clips.py 片段表.json 输出目录
片段表：[{"src": "录制目录", "start": "1:26", "end": "2:43", "name": "02_序章_白夜叉之战", "note": "说明"}, ...]
  start / end 写秒数或 分:秒（可带小数）。
每个片段出三个文件，都从同一时刻开始，拖进剪辑软件对齐 0 秒就是同步的：
  名字.mp4        画面最近邻放大 5 倍（384×216 → 1920×1080，像素不糊）、60 帧 + 混好的声音（BGM + 音效）
  名字_BGM.wav    只有背景音乐（48 kHz 16 bit）
  名字_音效.wav   只有音效
另外写一份 片段说明.txt。
"""
import json
import os
import subprocess
import sys


def secs(v):
    if isinstance(v, (int, float)):
        return float(v)
    parts = [float(x) for x in str(v).split(":")]
    t = 0.0
    for x in parts:
        t = t * 60 + x
    return t


def ff(*args):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args]
    print(" ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def audio_offset(src):
    """full.webm 里声音比画面晚开始多少秒（0.03–0.08）。
    三个录制器同时开录，但时间各从“收到的第一份数据”算起：full 从第一帧画面算，声音晚到这么多；
    bgm / sfx 只有声音，从第一份声音算。所以 bgm / sfx 的 0 秒 = full 的这一刻，剪的时候要往回挪。"""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=start_time",
                          "-of", "csv=p=0", os.path.join(src, "full.webm")], capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def cut_wav(webm, a, b, dst):
    """按 full 的时间轴剪 [a, b]（a、b 已经减过偏移）；开头不够的补静音，长度严格是 b - a。"""
    lead = max(0.0, -a)
    af = ("adelay=%d:all=1," % round(lead * 1000) if lead else "") + "apad"
    ff("-ss", "%.3f" % max(0.0, a), "-i", webm, "-vn", "-af", af, "-t", "%.3f" % (b - a),
       "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", dst)


def main(table, dst):
    clips = json.load(open(table, encoding="utf-8"))
    os.makedirs(dst, exist_ok=True)
    lines = ["每个片段三个文件：mp4（画面 + 混好的声音）、_BGM.wav（只有背景音乐）、_音效.wav（只有音效）。",
             "三个文件从同一时刻开始，拖进剪辑软件都对齐到 0 秒就是同步的。画面是游戏原画 384×216 最近邻放大 5 倍到 1920×1080，60 帧。", ""]
    for c in clips:
        a, b = secs(c["start"]), secs(c["end"])
        src, name = c["src"], c["name"]
        off = audio_offset(src)
        wavs = [os.path.join(dst, "%s_%s.wav" % (name, label)) for label in ("BGM", "音效")]
        for k, w in zip(("bgm", "sfx"), wavs):
            cut_wav(os.path.join(src, k + ".webm"), a - off, b - off, w)
        # mp4 的声音 = 这两条 wav 相加（浏览器里的混音也是两路直接相加），三个文件严格是同一份声音
        ff("-ss", "%.3f" % a, "-to", "%.3f" % b, "-i", os.path.join(src, "full.webm"), "-i", wavs[0], "-i", wavs[1],
           "-filter_complex", "[0:v]scale=1920:1080:flags=neighbor[v];[1:a][2:a]amix=inputs=2:normalize=0[a]",
           "-map", "[v]", "-map", "[a]", "-r", "60", "-fps_mode", "cfr",
           "-c:v", "libx264", "-preset", "faster", "-crf", "16", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", os.path.join(dst, name + ".mp4"))
        lines.append("%s（%d 秒）%s" % (name, round(b - a), ("：" + c["note"]) if c.get("note") else ""))
    with open(os.path.join(dst, "片段说明.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("done:", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
