"""整部游戏分段录屏：四段，每段一个目录，录完立刻查帧率和空等；有问题的段可以单独重录。

用法：python tools/record_all.py <输出目录> [--only A,C]
  A 序章～第三章 / B 第四～第七章 / C 第八～第十章 / D 第十一章～终章
  每段在 <输出目录>\\<段名>\\ 里留下 full.webm / bgm.webm / sfx.webm / run.json（见 playtest.py --record）。
  录的时候别跑重活（渲染、转码）：浏览器抢不到 CPU，游戏会掉帧甚至慢放。
拼成一条 mp4：python tools/join_chunks.py <输出目录> <输出.mp4>
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CHUNKS = [
    ("A", "all", "ch3", "A_序章到第三章"),
    ("B", "ch4", "ch7", "B_第四到第七章"),
    ("C", "ch8", "ch10", "C_第八到第十章"),
    ("D", "ch11", "ch14", "D_第十一章到终章"),
]


def frame_report(webm):
    """视频帧时间戳：总时长、每 5 秒的帧率低于 50 的窗口、超过 0.5 秒的空档。"""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time", "-of", "csv=p=0", webm],
                         capture_output=True, text=True).stdout.split()
    ts = sorted(float(x.strip(",")) for x in out if x.strip(","))
    if not ts:
        return {"duration": 0, "slow_windows": [], "gaps": []}
    n_win = int(ts[-1] // 5) + 1
    cnt = [0] * n_win
    for t in ts:
        cnt[int(t // 5)] += 1
    slow = [(i * 5, round(c / 5)) for i, c in enumerate(cnt[:-1]) if c / 5 < 50]
    gaps = [(round(a, 1), round(b - a, 1)) for a, b in zip(ts, ts[1:]) if b - a > 0.5]
    return {"duration": round(ts[-1], 1), "slow_windows": slow, "gaps": gaps}


def check(d):
    rj = os.path.join(d, "run.json")
    if not os.path.exists(rj):
        return {"ok": False, "why": "没有 run.json（录制没跑完）"}
    run = json.load(open(rj, encoding="utf-8"))
    notes = run.get("notes", [])
    timeouts = [n[:60] for n in notes if n.startswith(("advance_timeout", "fight_timeout"))]
    explores = [n for n in notes if n.startswith("explore_")]
    fr = frame_report(os.path.join(d, "full.webm"))
    bad = []
    if run.get("errors"):
        bad.append("控制台有 %d 条报错" % len(run["errors"]))
    if timeouts:
        bad.append("%d 次超时" % len(timeouts))
    if fr["gaps"]:
        bad.append("画面有 %d 处空档 > 0.5 秒" % len(fr["gaps"]))
    if len(fr["slow_windows"]) > 2:
        bad.append("%d 个 5 秒窗口帧率 < 50" % len(fr["slow_windows"]))
    return {"ok": not bad, "why": "；".join(bad), "duration": fr["duration"], "slow": fr["slow_windows"][:8], "gaps": fr["gaps"][:5],
            "timeouts": timeouts, "explores": len(explores), "lines": run.get("dialog_lines")}


def main():
    out = sys.argv[1]
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
    os.makedirs(out, exist_ok=True)
    results = {}
    for key, which, until, name in CHUNKS:
        if only and key not in only:
            continue
        d = os.path.join(out, name)
        os.makedirs(d, exist_ok=True)
        t0 = time.time()
        print("[%s] %s 开录 %s" % (key, name, time.strftime("%H:%M:%S")), flush=True)
        with open(os.path.join(d, "playtest.log"), "w", encoding="utf-8") as lg:
            subprocess.run([sys.executable, os.path.join(HERE, "playtest.py"), which, "--until", until, "--record", d],
                           stdout=lg, stderr=lg, env=dict(os.environ, PLAYTEST_OUT=os.path.join(d, "_shots")))
        r = check(d)
        results[key] = r
        print("[%s] 用了 %.1f 分钟  %s" % (key, (time.time() - t0) / 60, json.dumps(r, ensure_ascii=False)), flush=True)
    print("== 汇总 ==", flush=True)
    for k, r in results.items():
        print(k, "OK" if r["ok"] else "要重录：" + r["why"], r.get("duration"), flush=True)


if __name__ == "__main__":
    main()
