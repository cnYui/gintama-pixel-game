"""把《银魂 像素剧场》的剧情分镜从原工程代码里导出来（不渲染视频）。

输出（都在本脚本所在目录）：
    storyboard.json     机器可读：每个场景的时长、起止时间、音乐、台词、音效、角色、背景、镜头表原文
    分镜总表.md          一页总表 + 每个场景的摘要
    场景分镜\\sNN_*.md    每个场景一份：故事分镜（CONTRACT.md 第 8 节）、镜头表（场景文件开头的 SHOT LIST）、
                         台词时间表、音效 cue、出场角色、用到的背景函数

数据来源：..\\源码\\scenes\\*.py（模块 docstring = 镜头表；SCENE.subs / cues() / music = 台词、音效、音乐）和
..\\源码\\CONTRACT.md（故事分镜）。用法：python export_storyboard.py
"""
import importlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "源码")
sys.dont_write_bytecode = True
sys.path.insert(0, SRC)
os.chdir(SRC)

from chars import get_def, list_chars  # noqa: E402
from engine.core import FPS, W, H  # noqa: E402
from engine.render import scene_modules  # noqa: E402


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def contract_scenes():
    """CONTRACT.md 第 8 节：按 **sNN 标题 (时长)** 切块。"""
    txt = read(os.path.join(SRC, "CONTRACT.md"))
    start = txt.find("## 8. STORYBOARD")
    body = txt[start:] if start >= 0 else txt
    blocks, cur = {}, None
    for line in body.splitlines():
        m = re.match(r"^\*\*(s\d\d) (.+?)\*\*\s*(.*)$", line)
        if m:
            cur = m.group(1)
            blocks[cur] = dict(heading=f"{m.group(1)} {m.group(2)}", music_note=m.group(3).strip(), lines=[])
        elif cur:
            blocks[cur]["lines"].append(line)
    for b in blocks.values():
        b["text"] = "\n".join(b.pop("lines")).strip()
    head = body.split("\n**s00", 1)[0] if "\n**s00" in body else ""
    return blocks, head.strip()


def scene_sources(mod_name):
    """场景文件 + 它的私有辅助文件（_sNN_*.py）的源码。"""
    nn = mod_name.split("_")[0]  # s03
    texts = [read(os.path.join(SRC, "scenes", mod_name + ".py"))]
    for fn in sorted(os.listdir(os.path.join(SRC, "scenes"))):
        if fn.startswith("_" + nn + "_") and fn.endswith(".py"):
            texts.append(read(os.path.join(SRC, "scenes", fn)))
    return "\n".join(texts)


def bg_usage(src):
    aliases = {}
    for m in re.finditer(r"^from bg import (.+)$", src, re.M):
        for part in m.group(1).split(","):
            part = part.strip()
            if " as " in part:
                mod, al = [x.strip() for x in part.split(" as ")]
            else:
                mod, al = part, part
            aliases[al] = mod
    used = {}
    for al, mod in aliases.items():
        funcs = sorted(set(re.findall(rf"\b{re.escape(al)}\.([A-Za-z_]\w*)\s*\(", src)))
        used[mod] = funcs
    return used


def cards(src):
    out = {"name_card": [], "chapter_card": []}
    for m in re.finditer(r"name_card\(\s*img\s*,\s*t\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([\"'])(\w+)\3\s*,\s*([\"'])(.+?)\5(?:\s*,\s*([\"'])(.*?)\7)?", src):
        out["name_card"].append(dict(t0=float(m.group(1)), dur=float(m.group(2)), id=m.group(4), title=m.group(6), desc=m.group(8) or ""))
    for m in re.finditer(r"chapter_card\(\s*img\s*,\s*t\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([\"'])(.+?)\3(?:\s*,\s*([\"'])(.*?)\5)?", src):
        out["chapter_card"].append(dict(t0=float(m.group(1)), dur=float(m.group(2)), title=m.group(4), sub=m.group(6) or ""))
    return out


def spk_name(s):
    if not s:
        return None
    d = get_def(s)
    return d.name if d else s


def main():
    ids = set(list_chars())
    contract, contract_head = contract_scenes()
    scenes = []
    t_cursor = 0.0
    for mod_name in scene_modules():
        mod = importlib.import_module(f"scenes.{mod_name}")
        sc = mod.SCENE
        src = scene_sources(mod_name)
        lits = set(re.findall(r"[\"']([a-z_]+)[\"']", src))
        chars_used = sorted(lits & ids)
        subs = [dict(t0=round(a, 2), t1=round(b, 2), speaker=s, speaker_name=spk_name(s), text=x) for a, b, s, x in (sc.subs or [])]
        try:
            cues = [dict(t=round(c.time, 2), name=c.name, vol=c.vol, pitch=c.pitch, dur=c.dur) for c in sc.cues()]
        except Exception as ex:  # noqa: BLE001
            cues = []
            print("cues failed", mod_name, ex)
        music = sc.music
        if isinstance(music, (list, tuple)):
            music = [dict(t=m[0], track=m[1]) for m in music]
        cs = contract.get(sc.id) or contract.get(mod_name.split("_")[0]) or {}
        entry = dict(
            id=sc.id, module=mod_name, title=sc.title, start=round(t_cursor, 2), duration=sc.duration, end=round(t_cursor + sc.duration, 2),
            music=music, music_vol=sc.music_vol, subs_pos=getattr(sc, "subs_pos", "bottom"),
            fade_in=getattr(sc, "fade_in", None), fade_out=getattr(sc, "fade_out", None),
            characters=[dict(id=c, name=spk_name(c)) for c in chars_used],
            backgrounds=bg_usage(src), cards=cards(src),
            subs=subs, sfx_cues=cues,
            shot_list=(mod.__doc__ or "").strip(),
            contract_storyboard=dict(heading=cs.get("heading"), music_note=cs.get("music_note"), text=cs.get("text")),
        )
        scenes.append(entry)
        t_cursor += sc.duration
    total = round(t_cursor, 2)
    data = dict(work="银魂 像素剧场", canvas=[W, H], fps=FPS, total_duration=total, scene_count=len(scenes),
                note="start/end 是在成片里的时间（场景首尾相接，不含淡入淡出重叠）；subs 的 t0/t1、cues 的 t 是场景内时间（秒）。",
                contract_header=contract_head, scenes=scenes)
    with open(os.path.join(HERE, "storyboard.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)

    # ---- 每个场景一份
    os.makedirs(os.path.join(HERE, "场景分镜"), exist_ok=True)
    for e in scenes:
        md = [f"# {e['id']} {e['title']}", ""]
        md.append(f"- 时长：{e['duration']} s（成片里 {e['start']:.1f}–{e['end']:.1f} s）")
        mus = e["music"]
        if isinstance(mus, list):
            mus = "、".join(f"{m['t']:g}s → {m['track'] or '（静音）'}" for m in mus)
        md.append(f"- 音乐：{mus}（音量 {e['music_vol']}）")
        md.append("- 出场角色（代码里引用到的角色 id）：" + "、".join(f"{c['id']}（{c['name']}）" for c in e["characters"]))
        bgs = "；".join(f"{mod}：{', '.join(fs) if fs else '—'}" for mod, fs in e["backgrounds"].items())
        md.append(f"- 背景（bg 模块里被调用的函数）：{bgs or '—'}")
        md.append(f"- 淡入 / 淡出：{e['fade_in']} / {e['fade_out']} s")
        md.append("")
        cs = e["contract_storyboard"]
        if cs.get("text"):
            md += ["## 故事分镜（CONTRACT.md 第 8 节，写作时的设计意图）", "", f"**{cs['heading']}** {cs.get('music_note') or ''}", "", cs["text"], ""]
        md += ["## 镜头表（场景文件开头的 SHOT LIST，场景内时间）", "", "```text", e["shot_list"], "```", ""]
        if e["subs"]:
            md += ["## 台词 / 旁白时间表（场景内时间）", "", "| 开始 | 结束 | 说话者 | 台词 |", "|---|---|---|---|"]
            for s in e["subs"]:
                md.append(f"| {s['t0']:.2f} | {s['t1']:.2f} | {s['speaker_name'] or '旁白'} | {s['text']} |")
            md.append("")
        if e["cards"]["name_card"] or e["cards"]["chapter_card"]:
            md += ["## 名牌 / 篇章卡（从代码里直接调用处提取，可能不全）", ""]
            for c in e["cards"]["name_card"]:
                md.append(f"- 名牌 {c['t0']:g}s（{c['dur']:g}s）：{c['id']} — {c['title']} {c['desc']}")
            for c in e["cards"]["chapter_card"]:
                md.append(f"- 篇章卡 {c['t0']:g}s（{c['dur']:g}s）：{c['title']} {c['sub']}")
            md.append("")
        if e["sfx_cues"]:
            md += ["## 音效 cue（场景内时间）", "", "| t | 音效 | 音量 | 持续 |", "|---|---|---|---|"]
            for c in sorted(e["sfx_cues"], key=lambda c: c["t"]):
                md.append(f"| {c['t']:.2f} | {c['name']} | {c['vol']} | {c['dur'] if c['dur'] else ''} |")
            md.append("")
        with open(os.path.join(HERE, "场景分镜", f"{e['module']}.md"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(md))

    # ---- 总表
    def mfmt(m):
        if isinstance(m, list):
            return " → ".join((x["track"] or "（静音）") for x in m)
        return m or "—"

    md = ["# 《银魂 像素剧场》分镜总表", "",
          f"全片 {total:.1f} s（{int(total // 60)}:{total % 60:04.1f}），{len(scenes)} 个场景，内部画布 {W}×{H}（放大 5 倍到 1920×1080），{FPS} fps。",
          "",
          "怎么读：每个场景 = 一个故事段落 = 日后游戏里的一关 / 一章。每个场景的详细分镜（故事意图 + 逐镜头的镜头表 + 台词 + 音效）在 `场景分镜\\` 下；机器可读版是 `storyboard.json`。",
          "",
          "| 场景 | 标题 | 成片时间 | 时长 | 音乐 | 出场角色 | 台词条数 | 音效数 |",
          "|---|---|---|---|---|---|---|---|"]
    for e in scenes:
        chars = "、".join(c["name"] for c in e["characters"][:10]) + ("…" if len(e["characters"]) > 10 else "")
        md.append(f"| [{e['id']}](场景分镜/{e['module']}.md) | {e['title']} | {e['start']:.0f}–{e['end']:.0f} s | {e['duration']:g} s | {mfmt(e['music'])} | {chars} | {len(e['subs'])} | {len(e['sfx_cues'])} |")
    md += ["", "## 分镜前言（CONTRACT.md 第 8 节开头）", "", contract_head, "",
           "全局约定（输出格式、引擎 API、画面规范、角色表、音乐 / 音效名）见 [CONTRACT_原文.md](CONTRACT_原文.md)。", ""]
    with open(os.path.join(HERE, "分镜总表.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))
    with open(os.path.join(HERE, "CONTRACT_原文.md"), "w", encoding="utf-8") as fh:
        fh.write(read(os.path.join(SRC, "CONTRACT.md")))
    print(f"{len(scenes)} scenes, total {total:.1f}s")
    for e in scenes:
        print(f"  {e['id']} {e['title']:10s} {e['start']:6.1f}-{e['end']:6.1f}  subs={len(e['subs']):2d} cues={len(e['sfx_cues']):3d} chars={len(e['characters']):2d} shotlist={len(e['shot_list'])}c contract={'Y' if e['contract_storyboard'].get('text') else 'N'}")


if __name__ == "__main__":
    main()
