"""把《银魂 像素剧场》原工程里的 42 个角色烘焙成游戏用的精灵图集。

用法（在任意目录运行都行）：
    python bake_characters.py                # 全部角色
    python bake_characters.py gintoki kagura # 只烘焙指定角色

依赖：上一级的 ..\\源码（原工程，不会被修改）、Pillow、numpy；预览图里的中文标签用 Windows 自带的
simsun.ttc（原工程的字幕字体）。

输出到 ..\\角色图集\\：
    <id>\\<id>.png        图集：每行一个动作，帧在行内从左到右紧挨着；透明背景；朝右；原始像素
    <id>\\<id>.json       元数据（cell / pivot / 每个动作的行号、帧数、fps、循环或一次性）
    <id>\\头像\\*.png      表情头像和对话头像
    <id>\\<id>_预览.png    给人看的预览（2 倍放大、棋盘格底、每行标动作名）
    catalog.json、总览.png

循环动作怎么取帧：按原工程的动画帧率（12 fps）逐帧渲染，找最小周期 N（≤ 24）使第 k 帧和第 k+N 帧像素完全相同
（seamless = true）；找不到完全相同的，取“首尾差异最小”的 N（seamless = "approx"，json 里记着差异像素数）。
一次性动作（出拳、挥刀、受击……由进度 p 驱动）：p 从 0 到 1 采样 8 帧。
"""
import hashlib
import json
import os
import sys
import time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "源码")
OUT = os.path.join(ROOT, "角色图集")
sys.dont_write_bytecode = True
sys.path.insert(0, SRC)
os.chdir(SRC)

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from chars import get_def, list_chars, render_sprite, portrait  # noqa: E402
from chars.rig import POSES, CustomChar  # noqa: E402
from engine.core import ANIM_FPS  # noqa: E402
from engine.text import draw_text  # noqa: E402

FPS = ANIM_FPS            # 原工程精灵动画帧率（12）
T0K = 3                   # 从第 3 帧（0.25 s）开始取，跳过 t<0.12 s 的眨眼窗口
T0 = T0K / FPS
SAMPLE = 33               # 找周期时采样的帧数：最后一帧 t≈2.92 s，在下一次眨眼（3.1 s）之前
MAXN = 24                 # 最长循环帧数
EPS = 1e-6                # 防止 int((t*720) % 360) 这类写法因浮点误差差 1 度


def tk(k):
    """第 k 个采样帧的时间（落在 12 fps 网格上，加一点 epsilon）。"""
    return (T0K + k) / FPS + EPS
ONESHOT_N = 8             # 一次性动作的采样帧数
PAD = 1                   # 每格四周留 1 px
CANVAS = 200              # 比较帧用的对齐画布
ANCHOR = (100, 150)       # 对齐画布上的脚点


def frame(cid, pose, t, p=None, **kw):
    spr, ax, ay = render_sprite(cid, pose, t=t, p=p, **kw)
    return spr.convert("RGBA"), int(ax), int(ay)


def aligned(img, ax, ay):
    """贴到固定画布上（脚点对齐），返回 uint8 数组，用来比较两帧。"""
    can = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    can.paste(img, (ANCHOR[0] - ax, ANCHOR[1] - ay), img)
    return np.asarray(can)


def sig(img, ax, ay):
    bb = img.getbbox()
    if bb is None:
        return ("empty",)
    crop = img.crop(bb)
    return (crop.size, ax - bb[0], ay - bb[1], hashlib.sha1(crop.tobytes()).hexdigest())


def find_period(arrs):
    """返回 (N, seamless, 首尾平均差异像素数)。

    先找像素完全相同的最小周期；没有就看各个 N 的“第 k 帧与第 k+N 帧”平均差异，取差异不超过
    max(15 像素, 2 倍最小差异) 的最小 N（循环 14 帧比 23 帧好用，差一点点相位肉眼看不出）；
    最小差异也超过 120 像素的，认为没有周期，取 12 帧并标 seamless=False。
    """
    n = len(arrs)
    scores = {}
    for N in range(1, MAXN + 1):
        diffs = [int(np.count_nonzero((arrs[k] != arrs[k + N]).any(axis=2))) for k in range(0, n - N)]
        score = sum(diffs) / len(diffs)
        if score == 0:
            return N, True, 0.0
        scores[N] = score
    best = min(scores.values())
    if best > 120:
        return 12, False, scores[12]
    thr = max(15.0, 2 * best)
    N = min(k for k, v in scores.items() if v <= thr)
    return N, "approx", scores[N]


P_TESTS = (0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0)


def p_dependent(cid, pose, kw):
    keys = {sig(*frame(cid, pose, tk(0), p=p, **kw)) for p in P_TESTS}
    return len(keys) > 1


def bake_pose(cid, pose, kw):
    """返回 list of dict(name, kind, frames=[(img,ax,ay)...], fps, seamless, loop_error)。"""
    out = []
    pdep = p_dependent(cid, pose, kw)
    d = get_def(cid)
    if pdep:
        frames = [frame(cid, pose, tk(k), p=k / (ONESHOT_N - 1), **kw) for k in range(ONESHOT_N)]
        out.append(dict(name=pose, kind="oneshot", frames=frames, fps=FPS))
        if not isinstance(d, CustomChar):
            return out          # 人形骨架：p=None 时 p 只是随时间 0→1 循环，没有额外信息
    # 循环采样（p=None）
    frames = [frame(cid, pose, tk(k), p=None, **kw) for k in range(SAMPLE)]
    arrs = [aligned(*f) for f in frames]
    N, seam, score = find_period(arrs)
    if seam is True and N == 1:
        out.append(dict(name=pose if not pdep else pose + "_loop", kind="static", frames=frames[:1], fps=FPS))
    else:
        entry = dict(name=pose if not pdep else pose + "_loop", kind="loop", frames=frames[:N], fps=FPS, seamless=seam)
        if seam == "approx":
            entry["loop_error_px"] = round(score, 1)
        out.append(entry)
    return out


def set_key(entry):
    return hashlib.sha1(json.dumps([sig(*f) for f in entry["frames"]]).encode()).hexdigest()


def checker(w, h, s=8):
    a = np.zeros((h, w, 3), np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    m = ((xx // s) + (yy // s)) % 2 == 0
    a[m] = (74, 94, 114)
    a[~m] = (66, 84, 104)
    return Image.fromarray(a, "RGB")


VARIANT_CHARS = ("townsman", "townswoman")   # 路人有 4 种配色：variant=0..3（0 是默认，1..3 另存成 <id>__v1..3）
KW_VARIANTS = {"apron": {"torso": "apron"}}   # 其他外观变体：shinpachi@apron = 新八系着围裙（家庭餐厅打工）


def bake_one(spec):
    """spec = 角色 id，或 'townsman@2'（带配色变体）。"""
    t_start = time.time()
    cid, _, var = spec.partition("@")
    out_id = (f"{cid}__v{var}" if var.isdigit() else f"{cid}__{var}") if var else cid
    d = get_def(cid)
    errors = []
    extras = [p for p in (getattr(d, "poses", None) or {}) if p not in POSES]
    # 非人形角色（定春、伊丽莎白）：自己的动作名排前面，标准名多半是退回到它们的别名
    pose_names = (extras + list(POSES)) if isinstance(d, CustomChar) else (list(POSES) + extras)
    kw = ({"variant": int(var)} if var.isdigit() else dict(KW_VARIANTS[var])) if var else {}
    baked, seen, aliases = [], {}, {}
    for pose in pose_names:
        try:
            entries = bake_pose(cid, pose, kw)
        except Exception as ex:  # noqa: BLE001
            errors.append(f"{pose}: {type(ex).__name__}: {ex}")
            continue
        for e in entries:
            k = set_key(e)
            if k in seen and e["name"] != "idle":
                aliases[e["name"]] = seen[k]
                continue
            seen.setdefault(k, e["name"])
            baked.append(e)
    if not baked:
        return dict(id=out_id, error="; ".join(errors) or "no frames")

    # 统一格子：以脚点为基准取全体最大外接范围
    L = R = U = D = 0
    for e in baked:
        for img, ax, ay in e["frames"]:
            bb = img.getbbox()
            if bb is None:
                continue
            L = max(L, ax - bb[0])
            R = max(R, bb[2] - ax)
            U = max(U, ay - bb[1])
            D = max(D, bb[3] - ay)
    L, R, U, D = L + PAD, R + PAD, U + PAD, D + PAD
    cw, ch = L + R, U + D
    maxf = max(len(e["frames"]) for e in baked)
    atlas = Image.new("RGBA", (maxf * cw, len(baked) * ch), (0, 0, 0, 0))
    anims = {}
    for row, e in enumerate(baked):
        for i, (img, ax, ay) in enumerate(e["frames"]):
            atlas.paste(img, (i * cw + L - ax, row * ch + U - ay), img)
        a = dict(row=row, frames=len(e["frames"]), fps=e["fps"], kind=e["kind"])
        if "seamless" in e:
            a["seamless"] = e["seamless"]
        if "loop_error_px" in e:
            a["loop_error_px"] = e["loop_error_px"]
        anims[e["name"]] = a

    odir = os.path.join(OUT, out_id)
    os.makedirs(os.path.join(odir), exist_ok=True)
    atlas.save(os.path.join(odir, f"{out_id}.png"))

    # 头像（配色变体不再重复导出）
    hdir = os.path.join(odir, "头像")
    expressions = []
    heads = {}
    if var:
        pass
    elif getattr(d, "heads_art", None):
        for e in d.heads_art:
            try:
                heads[e] = d.head(e)
            except Exception as ex:  # noqa: BLE001
                errors.append(f"head {e}: {ex}")
    elif not isinstance(d, CustomChar):
        pass
    if getattr(d, "portraits_art", None) and not var:
        for e in d.portraits_art:
            try:
                heads["portrait_" + e] = d.portrait(e)
            except Exception as ex:  # noqa: BLE001
                errors.append(f"portrait {e}: {ex}")
    try:
        pt = portrait(cid, "normal") if not var else None
        if pt is not None and not any(k.startswith("portrait_") for k in heads):
            heads["portrait_default"] = pt
    except Exception as ex:  # noqa: BLE001
        errors.append(f"portrait: {ex}")
    for name, im in heads.items():
        if im is None:
            continue
        os.makedirs(hdir, exist_ok=True)
        im.convert("RGBA").save(os.path.join(hdir, f"{name}.png"))
        expressions.append(name)

    disp = d.name + ((f"（配色 {var}）" if var.isdigit() else f"（{var}）") if var else "")
    meta = dict(
        id=out_id, name=disp, work="银魂",
        image=f"{out_id}.png", cell=[cw, ch], pivot=[L, U], facing="right",
        animations=anims, aliases=aliases, expressions=expressions,
        variants=({"kw": kw, "base": cid, "说明": "同一个角色的另一种外观（%s）；头像和表情看 %s 目录" % (kw, cid)} if var
                  else ({"配色变体": [f"{cid}__v{n}" for n in (1, 2, 3)]} if cid in VARIANT_CHARS else {})),
        source=dict(project="gintama_pixel",
                    call="chars.render_sprite(cid, pose, t=T0+k/12, p=None 或 k/7%s)；脚点 = 渲染函数返回的 (ax, ay)" % (f", **{kw}" if var else ""),
                    rig="chars/rig.py（人形骨架）" if not isinstance(d, CustomChar) else "自定义渲染器（非人形）"),
        notes="朝右；向左用水平镜像。原工程画布 384×216，放大 5 倍到 1080p，所以游戏里整数倍放大（最近邻）最还原。",
    )
    if errors:
        meta["errors"] = errors
    with open(os.path.join(odir, f"{out_id}.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)

    # 预览图（2 倍）
    S = 2
    gut = 120
    prev = checker(gut + maxf * cw * S, len(baked) * ch * S + 24)
    prev = prev.convert("RGBA")
    big = atlas.resize((atlas.width * S, atlas.height * S), Image.NEAREST)
    prev.paste(big, (gut, 24), big)
    draw_text(prev, 4, 4, f"{out_id} / {disp}   cell={cw}x{ch}  pivot=({L},{U})", (255, 255, 255), outline=(0, 0, 0))
    for row, e in enumerate(baked):
        label = f"{e['name']} ({len(e['frames'])}f)"
        draw_text(prev, 4, 24 + row * ch * S + 4, label, (255, 255, 200), outline=(0, 0, 0))
    prev.convert("RGB").save(os.path.join(odir, f"{out_id}_预览.png"))
    return dict(id=out_id, name=disp, cell=[cw, ch], pivot=[L, U], animations=len(anims), frames=sum(a["frames"] for a in anims.values()),
                aliases=len(aliases), expressions=len(expressions), errors=errors, seconds=round(time.time() - t_start, 1),
                atlas=[atlas.width, atlas.height])


def lineup(ids):
    per, cw_, ch_, S = 12, 64, 76, 3
    rows = (len(ids) + per - 1) // per
    img = Image.new("RGB", (per * cw_, rows * ch_), (90, 110, 130))
    for i, cid in enumerate(ids):
        r, c = divmod(i, per)
        try:
            spr, ax, ay = frame(cid, "idle", tk(0))
            x = c * cw_ + cw_ // 2 - ax
            y = r * ch_ + ch_ - 18 - ay
            img.paste(spr, (x, y), spr)
        except Exception:  # noqa: BLE001
            pass
    img = img.resize((img.width * S, img.height * S), Image.NEAREST)
    for i, cid in enumerate(ids):
        r, c = divmod(i, per)
        name = get_def(cid).name
        draw_text(img, (c * cw_) * S + 4, (r * ch_ + ch_ - 14) * S, f"{name[:4]}", (255, 255, 255), outline=(0, 0, 0))
    img.save(os.path.join(OUT, "总览.png"))


if __name__ == "__main__":
    ids = sys.argv[1:] or (list_chars() + [f"{c}@{n}" for c in VARIANT_CHARS for n in (1, 2, 3)] + ["shinpachi@apron"])
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    with Pool(4) as pool:
        results = pool.map(bake_one, ids, chunksize=1)
    ok = [r for r in results if "error" not in r]
    bad = [r for r in results if "error" in r]
    if not sys.argv[1:]:
        catalog = []
        for r in ok:
            with open(os.path.join(OUT, r["id"], f"{r['id']}.json"), encoding="utf-8") as fh:
                m = json.load(fh)
            catalog.append(dict(id=m["id"], name=m["name"], atlas=f"{m['id']}/{m['image']}", json=f"{m['id']}/{m['id']}.json",
                                cell=m["cell"], pivot=m["pivot"], animation_count=len(m["animations"]),
                                animations=list(m["animations"].keys()), expressions=m["expressions"]))
        with open(os.path.join(OUT, "catalog.json"), "w", encoding="utf-8") as fh:
            json.dump(dict(work="银魂", count=len(catalog), characters=catalog), fh, ensure_ascii=False, indent=2)
        lineup([r["id"] for r in ok if "__v" not in r["id"]])
    print(f"baked {len(ok)} / {len(ids)} characters in {time.time() - t0:.0f}s")
    for r in ok:
        flag = f"  ERR[{len(r['errors'])}]" if r["errors"] else ""
        print(f"  {r['id']:14s} {r['name']:6s} cell={r['cell']} anims={r['animations']:3d} frames={r['frames']:4d} alias={r['aliases']:2d} heads={r['expressions']:2d}{flag}")
    for r in bad:
        print("  FAILED", r)
