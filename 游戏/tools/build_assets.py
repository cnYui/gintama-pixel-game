"""《银魂 像素剧场 · 游戏版》资源构建：把原工程（..\\..\\源码）和角色图集（..\\..\\角色图集）导出成网页游戏能用的资源。

用法（在任意目录）：
    python build_assets.py                 # 全部（不含视频）
    python build_assets.py chars bg ui     # 只做某几项：chars bg ui audio video font data
    python build_assets.py video           # 开场动画（渲染约 1 分钟）

输出：..\\assets\\...  和  ..\\data.js（window.GAME_DATA，所有元数据内嵌，双击 index.html 就能跑，不用服务器）
改了剧情台词（story\\*.js）后要重跑 `font data`：字体图集只收台词里出现过的字。
"""
import glob
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(HERE)
WORK = os.path.dirname(GAME)                      # ...\游戏素材\银魂
SRC = os.path.join(WORK, "源码")
ATLAS = os.path.join(WORK, "角色图集")
AUDIO_SRC = os.path.join(WORK, "音频")
ASSETS = os.path.join(GAME, "assets")
META = os.path.join(HERE, "_meta")               # 各步骤的元数据，最后由 data 步骤合成 data.js

sys.dont_write_bytecode = True
sys.path.insert(0, SRC)
os.chdir(SRC)

from PIL import Image, ImageDraw, ImageFont  # noqa: E402
import numpy as np  # noqa: E402

from engine.core import W, H  # noqa: E402


def out(*p):
    path = os.path.join(ASSETS, *p)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def rel(path):
    return os.path.relpath(path, GAME).replace("\\", "/")


def save_meta(name, obj):
    os.makedirs(META, exist_ok=True)
    with open(os.path.join(META, name + ".json"), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False)


def crop_rgba(im):
    """裁到不透明区域，返回 (图, 左上角偏移)。"""
    bb = im.getbbox()
    if bb is None:
        return None, (0, 0)
    return im.crop(bb), (bb[0], bb[1])


def rgba_canvas(w=W, h=H):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


# ============================================================== 角色
def build_chars():
    dst = os.path.join(ASSETS, "chars")
    os.makedirs(dst, exist_ok=True)
    meta = {}
    for jp in sorted(glob.glob(os.path.join(ATLAS, "*", "*.json"))):
        m = json.load(open(jp, encoding="utf-8"))
        cid = m["id"]
        d = os.path.dirname(jp)
        shutil.copy2(os.path.join(d, m["image"]), os.path.join(dst, f"{cid}.png"))
        heads = {}
        hd = os.path.join(d, "头像")
        if os.path.isdir(hd):
            os.makedirs(os.path.join(dst, f"{cid}_heads"), exist_ok=True)
            for hp in glob.glob(os.path.join(hd, "*.png")):
                name = os.path.splitext(os.path.basename(hp))[0]
                shutil.copy2(hp, os.path.join(dst, f"{cid}_heads", f"{name}.png"))
                heads[name] = f"assets/chars/{cid}_heads/{name}.png"
        meta[cid] = dict(name=m["name"], image=f"assets/chars/{cid}.png", cell=m["cell"], pivot=m["pivot"],
                         animations=m["animations"], aliases=m.get("aliases", {}), heads=heads)
    # 章节素材调研里直接烘好的角色（assets/chars/s11/*.json 这种，格式同图集库）；有 <id>_heads 文件夹就当头像
    for jp in sorted(glob.glob(os.path.join(dst, "s*", "*.json"))):
        m = json.load(open(jp, encoding="utf-8"))
        cid, d = m["id"], os.path.dirname(jp)
        sub = os.path.basename(d)
        heads = {}
        hd = os.path.join(d, f"{cid}_heads")
        if os.path.isdir(hd):
            for hp in glob.glob(os.path.join(hd, "*.png")):
                name = os.path.splitext(os.path.basename(hp))[0]
                heads[name] = f"assets/chars/{sub}/{cid}_heads/{name}.png"
        meta[cid] = dict(name=m.get("name", cid), image=f"assets/chars/{sub}/{m['image']}", cell=m["cell"], pivot=m["pivot"],
                         animations=m["animations"], aliases=m.get("aliases", {}), heads=heads)
    derive_chef(meta)
    # 角色的说话音高（原工程 voice 参数），用于打字音
    from chars import get_def
    for cid in meta:
        d = get_def(cid.split("__")[0])
        meta[cid]["voice"] = getattr(d, "voice", 1.0) if d else 1.0
    save_meta("chars", meta)
    print(f"chars: {len(meta)}")


def derive_chef(meta):
    """第二章的店长 = 路人配色 2 + 原片 s02 的厨师帽。帽子贴法同 s02_shinpachi._manager（帽子底边压在头顶下 3 px）；
    格子往上加高 8 px 放帽子，脚点跟着下移。头像用 townsman 的。"""
    import scenes._s02_art as A
    src = meta.get("townsman__v2")
    if not src:
        return
    im = Image.open(os.path.join(GAME, src["image"])).convert("RGBA")
    cw, ch = src["cell"]
    pad = 8
    hat = A.spr("hat")
    res = Image.new("RGBA", (im.width, (im.height // ch) * (ch + pad)), (0, 0, 0, 0))
    for r in range(im.height // ch):
        for f in range(im.width // cw):
            cell = im.crop((f * cw, r * ch, (f + 1) * cw, (r + 1) * ch))
            a = cell.getchannel("A")
            bb = a.getbbox()
            big = Image.new("RGBA", (cw, ch + pad), (0, 0, 0, 0))
            big.paste(cell, (0, pad))
            if bb:
                row = a.crop((0, bb[1], cw, bb[1] + 3)).getbbox()
                hx = (row[0] + row[2]) // 2
                big.alpha_composite(hat, (max(0, hx - hat.width // 2), max(0, pad + bb[1] + 3 - hat.height)))
            res.paste(big, (f * cw, r * (ch + pad)))
    p = os.path.join(ASSETS, "chars", "townsman__chef.png")
    res.save(p)
    m = dict(src)
    m.update(name="店长", image=rel(p), cell=[cw, ch + pad], pivot=[src["pivot"][0], src["pivot"][1] + pad], heads={})
    meta["townsman__chef"] = m


# ============================================================== 背景
def build_bg():
    from bg import common as C, kabukicho as K, edo as E, yorozuya as Y
    from bg._draw import graded_layer
    from engine.core import rng
    import scenes._s00_art as A
    stages = {}

    # ---------------- 歌舞伎町大街（白天），按原 street() 的图层顺序导出
    tod = "day"
    sky = Image.new("RGB", (W, H))
    C.sky(sky, tod, 0.0, horizon=150)
    sky.save(out("bg", "street", "sky.png"))

    def export_clouds(folder, tod, seed, count, y0, y1, cam_mul, speed=1.0):
        span = W + 200
        lst = []
        for i in range(count):
            r = rng("cloud", seed, i)
            depth = r.uniform(0.25, 1.0)
            w = int(26 + 50 * depth * r.uniform(0.7, 1.2))
            h = int(max(7, w * r.uniform(0.22, 0.32)))
            fade = (1 - depth) * 0.45
            spr = C.cached(("cloud", seed, i, tod, w, h), lambda: C._cloud_sprite(seed, i, tod, w, h, fade))
            y = int(y0 + (y1 - y0) * (1 - depth) * r.uniform(0.5, 1.0) + r.uniform(0, (y1 - y0) * 0.4))
            vx = (2.0 + 5.0 * depth) * speed
            x0 = r.uniform(0, span)
            p = out("bg", folder, f"cloud{i}.png")
            spr.save(p)
            lst.append(dict(image=rel(p), x0=round(x0, 2), y=y, vx=vx, k=round((0.04 + 0.16 * depth) * cam_mul, 4)))
        return dict(type="clouds", span=span, clouds=lst)

    # 歌舞伎町大街：按 tod（day / dusk / night / storm）导出一套图层；wet = 雨天路面的倒影；
    # dy = 整条街往下挪（万事屋门口的近景 yorozuya_front 就是 dy=36 的大街）
    def export_street(key, tod, wet=False, dy=0):
        folder = key
        if key != "street":
            sky = Image.new("RGB", (W, H))
            C.sky(sky, tod, 0.0, horizon=150 + dy)
            sky.save(out("bg", folder, "sky.png"))
        term = C.cached(("terminal", tod), lambda: E._terminal_layer(tod))
        term.save(out("bg", folder, "terminal.png"))
        back = graded_layer(("kabuki_back",), K._back_row, tod, depth=0.45, glow_radius=2, glow_strength=0.35)
        back.save(out("bg", folder, "back.png"))
        mid = graded_layer(("kabuki_mid",), K._mid_row, tod, depth=0.22, glow_radius=2, glow_strength=0.45)
        mid.save(out("bg", folder, "mid.png"))
        fac = K._facade(tod)
        fac.save(out("bg", folder, "facade.png"))
        road_h = H - K.BASE_Y - dy
        strip, rows = C.cached(("stone", road_h, tod), lambda: C._stone_strip(road_h, tod))
        strip.save(out("bg", folder, "road.png"))
        gut = C.cached(("kabuki_gutter", tod), lambda: K._gutter_strip(tod))
        gut.save(out("bg", folder, "gutter.png"))
        K._dyn()
        dyn = K._DYN
        lit = C.lit_amount(tod)
        lanterns = []
        for i, (lx, ly, col, size, txt) in enumerate(dyn["lanterns"]):
            on = lit > 0.25
            spr = C.cached(("lantern", tuple(col[:3]), size, on, txt), lambda: C._lantern_sprite(col, size, on, txt))
            p = out("bg", folder, f"lantern{i}.png")
            spr.save(p)
            item = dict(x=lx, y=ly + dy, size=size, image=rel(p), w=spr.width, h=spr.height)
            if lit > 0:   # 夜里 / 黄昏：灯笼的光晕（相加混合）
                rad = int(11 * size + 3)
                gs = C.glow_sprite(rad, C.mix(col, (255, 200, 120), 0.55), round(min(1.0, lit * 0.95) * 4) / 4)
                pg = out("bg", folder, f"lantern{i}_glow.png")
                gs.save(pg)
                item["glow"] = dict(image=rel(pg), rad=rad)
            lanterns.append(item)
        flags = []
        pole_c = C.grade_color((70, 60, 56), tod)
        for i, (fx, fy, col, text, tcol) in enumerate(dyn["flags"]):
            frames = C.cached(("kflag", i, tod), lambda: K._flag_frames(col, text, tcol, tod))
            ps = []
            for k, fr in enumerate(frames):
                p = out("bg", folder, f"flag{i}_{k}.png")
                fr.save(p)
                ps.append(rel(p))
            flags.append(dict(x=fx, y=fy + dy, frames=ps))
        layers = [
            dict(type="static", image=f"assets/bg/{folder}/sky.png"),
            export_clouds(folder, tod, seed=11, count=6, y0=2, y1=40 + dy, cam_mul=0.5),
            dict(type="terminal", image=f"assets/bg/{folder}/terminal.png", w=term.width, h=term.height, k=0.08, dy=dy,
                 side_px=tod in ("night", "storm", "dusk")),
            dict(type="wrap", image=f"assets/bg/{folder}/back.png", period=1024, k=0.3, y=dy),
            dict(type="wrap", image=f"assets/bg/{folder}/mid.png", period=896, k=0.55, y=dy),
            dict(type="wrap", image=f"assets/bg/{folder}/facade.png", period=K.STREET_W, k=1.0, y=dy),
            dict(type="rows", image=f"assets/bg/{folder}/road.png", period=192, y=K.BASE_Y + dy, h=road_h, rows=[list(r) for r in rows]),
            dict(type="wrap", image=f"assets/bg/{folder}/gutter.png", period=16, k=1.0, y=K.BASE_Y + dy, h=4),
        ]
        if wet:      # 雨天：路面上店面的倒影（同 kabukicho._wet_reflection，JS 里逐行画）
            layers.append(dict(type="reflect", image=f"assets/bg/{folder}/facade.png", period=K.STREET_W, base=K.BASE_Y + dy, n=34, alpha=0.42))
        if lit > 0.2:   # 店面洒到路上的暖光（相加混合）
            pool = C.cached(("kabuki_pool", tod), lambda: K._light_pool(tod))
            pp = out("bg", folder, "light_pool.png")
            pool.save(pp)
            layers.append(dict(type="wrap", image=rel(pp), period=K.STREET_W, k=1.0, y=K.BASE_Y + 1 + dy, blend="lighter"))
        layers += [
            dict(type="lanterns", period=K.STREET_W, items=lanterns, string=4, color=[40, 30, 34]),
            dict(type="flags", period=K.STREET_W, items=flags, base=K.BASE_Y + dy, pole=list(pole_c)),
        ]
        stages[key] = dict(
            period=K.STREET_W, floor=K.FLOOR_Y + dy, base=K.BASE_Y + dy, tod=tod, dy=dy,
            yorozuya=dict(x=K.YOROZUYA_X, window=K.YOROZUYA_WINDOW, door=K.YOROZUYA_DOOR, updoor=K.YOROZUYA_UPDOOR,
                          stairs=K.STAIRS, balcony_y=K.STREET_BALCONY_Y),
            layout=[list(x) for x in K._LAYOUT],
            layers=layers,
            fg=[dict(type="poles", period=520, k=1.5, col=list(C.grade_color((34, 30, 40), tod)), hi=list(C.grade_color((60, 56, 66), tod)))],
        )

    export_street("street", "day")

    # ---------------- 万事屋办公室（固定镜头）：环境动画帧 + 拉门帧 + 前景桌子
    amb = []
    for k in range(8):
        im = Image.new("RGB", (W, H))
        Y.office(im, k * 0.25, "day", 0.0)
        p = out("bg", "office", f"amb{k}.png")
        im.save(p)
        amb.append(rel(p))
    door = []
    for k in range(7):
        im = Image.new("RGB", (W, H))
        Y.office(im, 0.0, "day", k / 6)
        p = out("bg", "office", f"door{k}.png")
        im.save(p)
        door.append(rel(p))
    fg = rgba_canvas()
    Y.office_fg(fg, 0.0, "day")
    fg.save(out("bg", "office", "fg.png"))
    stages["office"] = dict(amb=amb, amb_fps=4, door=door, fg="assets/bg/office/fg.png",
                            floor=Y.FLOOR_Y, wall_base=Y.WALL_BASE_Y, sofa_seat_y=Y.SOFA_SEAT_Y, sofa_lie_y=Y.SOFA_LIE_Y,
                            milk=list(Y.MILK_POS), door_box=list(Y.DOOR_BOX), door_x=Y.DOOR_X, door_feet_y=Y.DOOR_FEET_Y,
                            window_box=list(Y.WINDOW_BOX), tv_box=list(Y.TV_BOX),
                            sofa_l_x=getattr(Y, "SOFA_L_X", 96), sofa_r_x=getattr(Y, "SOFA_R_X", 290),
                            table_x=getattr(Y, "TABLE_X", 192), table_y=getattr(Y, "TABLE_Y", 148),
                            desk_x=getattr(Y, "DESK_X", 192), desk_y=getattr(Y, "DESK_Y", 118))

    # ---------------- 攘夷战争的战场（黄昏）：自己用原工程的零件拼
    tod = "dusk"
    sky = Image.new("RGB", (W, H))
    C.sky(sky, tod, 0.0, horizon=146, body=False)
    A.sun(sky, 262, 104, 34)
    sky.save(out("bg", "war", "sky.png"))
    far, near = C.cached(("mtn", tod), lambda: C._mountain_layers(tod))
    far.save(out("bg", "war", "mtn_far.png"))
    near.save(out("bg", "war", "mtn_near.png"))
    mtn_y = 146 + 40 - far.height
    dirt_h = H - 148
    dstrip, drows = C.cached(("dirt", dirt_h, tod, 0.3), lambda: C._dirt_strip(dirt_h, tod, 0.3))
    dstrip.save(out("bg", "war", "ground.png"))
    sw = A.cached("swordfield", A._sword_field)
    sw.save(out("bg", "war", "swordfield.png"))
    # 远处的天人战舰（剪影）
    ships = []
    for i, (kind, sc) in enumerate((("cruiser", 1), ("pirate", 1), ("cruiser", 1), ("mothership", 1))):
        im = rgba_canvas(W * 2, H)
        try:
            E.ship(im, W, H // 2, kind, 0.0, scale=sc, tod=tod, haze=0.55)
        except Exception as ex:  # noqa: BLE001
            print("ship", kind, ex)
            continue
        spr, _ = crop_rgba(im)
        if spr is None:
            continue
        p = out("bg", "war", f"ship{i}.png")
        spr.save(p)
        ships.append(dict(image=rel(p), w=spr.width, h=spr.height, kind=kind))
    # 浓烟柱（循环帧，周期 1/0.18 s，取 24 帧）
    smoke = []
    per = 1 / 0.18
    for k in range(24):
        im = rgba_canvas(80, 140)
        A.smoke_column(im, k * per / 24, 20, 136, 110, 1, width=9)
        p = out("bg", "war", f"smoke{k}.png")
        im.save(p)
        smoke.append(rel(p))
    # 战旗（白底红纹 = 攘夷志士；紫底 = 天人）
    banners = {}
    for name, col, mark, torn in (("joui", (236, 226, 204), (160, 30, 40), False),
                                  ("joui_torn", (220, 208, 186), (150, 30, 40), True),
                                  ("amanto", (96, 70, 120), (230, 200, 90), False)):
        frs = []
        for k in range(8):
            im = rgba_canvas(40, 70)
            A.nobori(im, 8, 66, k / 8 * (2 * math.pi / 7), h=56, color=col, mark=mark, seed=3, torn=torn)
            p = out("bg", "war", f"nobori_{name}{k}.png")
            im.save(p)
            frs.append(rel(p))
        banners[name] = dict(frames=frs, ax=8, ay=66, fps=8)
    # 营帐（自己画的，配色跟着黄昏走）
    tent = Image.new("RGBA", (68, 42), (0, 0, 0, 0))
    td = ImageDraw.Draw(tent)
    ink = (24, 20, 37, 255)
    apex, left, right = (34, 3), (3, 40), (65, 40)
    td.polygon([apex, left, right], fill=(196, 178, 146, 255))
    td.polygon([apex, (34, 40), right], fill=(156, 138, 110, 255))
    td.line([(20, 22), (12, 40)], fill=(160, 142, 114, 255))
    td.line([(48, 22), (56, 40)], fill=(128, 112, 90, 255))
    td.polygon([(34, 15), (25, 40), (43, 40)], fill=(54, 40, 46, 255))
    for a, b in ((apex, left), (apex, right), (left, right), ((34, 15), (25, 40)), ((34, 15), (43, 40))):
        td.line([a, b], fill=ink)
    td.line([(34, 0), (34, 3)], fill=(80, 60, 50, 255))
    C.grade_rgba(tent, tod, 0.0).save(out("bg", "war", "tent.png"))
    stages["war"] = dict(
        layers=[
            dict(type="static", image="assets/bg/war/sky.png"),
            export_clouds("war", tod, seed=5, count=6, y0=8, y1=70, cam_mul=0.4, speed=0.6),
            dict(type="ships", items=ships),
            dict(type="wrap", image="assets/bg/war/mtn_far.png", period=768, k=0.05, y=mtn_y),
            dict(type="wrap", image="assets/bg/war/mtn_near.png", period=768, k=0.12, y=mtn_y),
            dict(type="smoke", frames=smoke, fps=24 / per),
            dict(type="wrap", image="assets/bg/war/swordfield.png", period=80, k=0.75, y=148 - sw.height + 6),
            dict(type="rows", image="assets/bg/war/ground.png", period=192, y=148, h=dirt_h, rows=[list(r) for r in drows]),
        ],
        banners=banners,
    )

    # ---------------- 标题背景：白天的江户全景（带 Terminal）
    im = Image.new("RGB", (W, H))
    E.skyline(im, 0, 0.0, "day")
    im.save(out("bg", "title_skyline.png"))
    stages["title"] = dict(image="assets/bg/title_skyline.png")

    build_bg_ch2(stages, export_clouds)
    # 第三章到终章：每章一个函数，在 bg_chapters.py
    import bg_chapters
    bg_chapters.build_all(stages, dict(out=out, rel=rel, crop_rgba=crop_rgba, rgba_canvas=rgba_canvas,
                                       export_clouds=export_clouds, export_street=export_street, W=W, H=H))
    save_meta("bg", stages)
    print("bg: " + " / ".join(stages))


# ============================================================== 第二章：家庭餐厅、志村道场门口（黄昏）、道场里
def build_bg_ch2(stages, export_clouds):
    """三张都是固定镜头的单屏地图。底图和会动的零件分开导出，会动的部分由 engine/gfx.js 的图层类型
    照原片 s02 的公式画：吊灯摆动、吊扇、秒针、窗外行人和乌鸦、厨房门、墙洞、灯笼、樱花树、飘尘、光束。
    另外导出过场用的特写（死鱼眼 / 认真的眼睛、暗黑煎蛋）和小道具（芭菲、托盘、灵魂、借条……）。"""
    from bg import common as C
    from engine.core import rng
    from engine.gfx import INK, scale_nearest
    import scenes._s02_art as A
    import scenes.s02_shinpachi as S2

    def save(img, *p):
        path = out("bg", *p)
        img.save(path)
        return rel(path)

    def save_crop(img, *p):
        spr, (x, y) = crop_rgba(img)
        return dict(image=save(spr, *p), x=x, y=y, w=spr.width, h=spr.height)

    # ---------------- 家庭餐厅（白天）
    base = A.rest_bg().copy()
    d = ImageDraw.Draw(base)
    cx, cy, _ = A.CLOCK
    a_h = math.radians(-60 + 90)          # 时针不动（同 draw_clock_hands），画进底图；秒针在 JS 里走
    d.line([(cx, cy), (cx + math.cos(a_h - math.pi / 2) * 4, cy + math.sin(a_h - math.pi / 2) * 4)], fill=INK, width=1)
    layers = [dict(type="static", image=save(base, "restaurant", "base.png"))]
    # 窗外的行人（原片 _window_life：只露出上半身）；乌鸦由剧情放进 stage.state.crow
    layers.append(dict(type="walkers", clip=list(A.WIN), base_y=86, items=[
        ["townsman", 1, 20, 10], ["townswoman__v1", -1, 17, 90], ["amanto_cat", 1, 24, 170],
        ["townswoman__v3", 1, 14, 230], ["townsman__v3", -1, 22, 60]]))
    layers.append(dict(type="image", **save_crop(A.window_overlay(), "restaurant", "window_overlay.png")))
    # 吊灯：周期 1/0.23 s 的摆动取 8 帧；吊扇：10 fps 三帧
    per, n = 1 / 0.23, 8
    cvs = []
    for k in range(n):
        cv = rgba_canvas()
        A.draw_lamps(cv, k * per / n)
        cvs.append(cv)
    for i, lx in enumerate(A.LAMPS):
        box = (lx - 10, 10, lx + 11, 38)
        layers.append(dict(type="frames", x=box[0], y=box[1], fps=n / per,
                           frames=[save(cv.crop(box), "restaurant", f"lamp{i}_{k}.png") for k, cv in enumerate(cvs)]))
    fan = []
    for k in range(3):
        cv = rgba_canvas()
        A.draw_lamps(cv, k / 10 + 1e-3)
        fan.append(save(cv.crop((A.FAN_X - 16, 10, A.FAN_X + 17, 19)), "restaurant", f"fan{k}.png"))
    layers.append(dict(type="frames", x=A.FAN_X - 16, y=10, fps=10, frames=fan))
    layers.append(dict(type="clock", x=cx, y=cy, len=7, color=[210, 50, 50], ink=list(INK)))
    # 厨房门：开到一半的几档 + 全开时的厨房（炉火、蒸汽 8 帧）；开合程度由 stage.door 决定
    box = (A.DOOR[0] - 6, A.DOOR[1] - 2, A.DOOR[0] + A.DOOR[2] + 3, A.DOOR[1] + A.DOOR[3] + 2)
    steps, opened = [], []
    for k, ok in enumerate((0.0, 0.25, 0.5, 0.75, 0.95)):
        cv = rgba_canvas()
        A.draw_door(cv, 0.0, ok)
        steps.append(save(cv.crop(box), "restaurant", f"door{k}.png"))
    for k in range(8):
        cv = rgba_canvas()
        A.draw_door(cv, k / 8 / 0.9, 1.0)
        opened.append(save(cv.crop(box), "restaurant", f"door_open{k}.png"))
    layers.append(dict(type="door", x=box[0], y=box[1], steps=steps, open=opened, fps=8 * 0.9))
    # 猪形墙洞：stage.state.hole 为真才画
    cv = rgba_canvas()
    A.draw_hole(cv, 0.0, 0.0)
    layers.append(dict(type="hole", key="hole", **save_crop(cv, "restaurant", "hole.png")))
    stages["restaurant"] = dict(layers=layers, floor=A.FLOOR_Y, wall_base=A.WALL_BASE, door=list(A.DOOR), win=list(A.WIN),
                                hole=list(A.HOLE), counter=list(A.COUNTER), counter_top=A.COUNTER_TOP,
                                stools=list(A.STOOLS), seat_y=A.SEAT_Y, parfait=list(A.PARFAIT_POS),
                                splat=list(S2.SPLAT_POS))

    # ---------------- 志村道场门口（黄昏）
    tod = A.GATE_TOD
    layers = [dict(type="static", image=save(A.gate_back(), "dojo_gate", "back.png")),
              export_clouds("dojo_gate", tod, seed=4, count=5, y0=6, y1=60, cam_mul=0.0),
              dict(type="static", image=save(A.gate_front(), "dojo_gate", "front.png"))]
    g = C.lit_amount(tod)
    spr = C._lantern_sprite(C.RED, 1, g > 0.25, None)
    rad = 14
    glow = C.glow_sprite(rad, C.mix(C.RED, (255, 200, 120), 0.55), round(min(1.0, g * 0.9) * 4) / 4)
    layers.append(dict(type="lantern", x=132, y=76, string=4, amp=1.4, freq=0.32, color=[40, 30, 34],
                       image=save(spr, "dojo_gate", "lantern.png"), w=spr.width, h=spr.height,
                       glow=dict(image=save(glow, "dojo_gate", "lantern_glow.png"), rad=rad)))
    frames, (bx, by), clusters = C.cached(("tree", 1.0, tod), lambda: C._tree_frames(1, tod))
    petals = []
    for i in range(9):                    # 同 cherry_tree 里飘落的花瓣
        r = rng("petal", 322, i)
        p_per = r.uniform(3.5, 6.0)
        p_off = r.uniform(0, p_per)
        pcx, pcy, _ = clusters[r.randrange(len(clusters))]
        petals.append([round(p_per, 4), round(p_off, 4), float(pcx), float(pcy)])
    layers.append(dict(type="tree", x=322, y=158, ax=int(bx), ay=int(by), freq=0.35,
                       frames=[save(f, "dojo_gate", f"tree{k}.png") for k, f in enumerate(frames)], petals=petals,
                       pc=[list(C.grade_color(c, tod)) for c in ((255, 206, 222), (240, 150, 184))]))
    stages["dojo_gate"] = dict(layers=layers, fg=[dict(type="sakura", n=10, seed=8, wind=18, fall=10, alpha=1)],
                               gate_cx=A.GATE_CX)

    # ---------------- 道场里（夕阳从拉门照进来）
    motes = []
    for i in range(18):                   # 同 s02_shinpachi._dojo_motes
        r = rng("mote", i)
        motes.append([round(r.uniform(0, W), 2), round(r.uniform(3, 8), 3), round(r.uniform(30, 160), 2), round(r.uniform(2, 5), 3)])
    stages["dojo"] = dict(layers=[dict(type="static", image=save(A.dojo_bg(), "dojo", "base.png")),
                                  dict(type="motes", items=motes, color=[255, 230, 180]),
                                  dict(type="rays", key="rays", n=10, color=[255, 214, 150])],
                          fg=[dict(type="sakura", key="sakura", n=30, seed=3, wind=26, fall=14, alpha=1)],
                          floor=A.FLOOR_Y)

    # ---------------- 过场特写和小道具
    sp = {}
    for key in ("parfait", "heart", "vein", "sweat", "hat", "soul", "tray", "egg"):
        s = A.spr(key)
        sp[key] = dict(image=save(s, "ch2", f"{key}.png"), w=s.width, h=s.height)
    for key in ("crow0", "crow1", "perch0", "perch1"):      # 隔着窗户看到的乌鸦：原片放大 2 倍
        s = scale_nearest(A.spr(key), 2)
        sp[key] = dict(image=save(s, "ch2", f"{key}.png"), w=s.width, h=s.height)
    cv = rgba_canvas()
    S2._splat(cv, S2.SPLAT + 3)           # 摔在地上的芭菲（樱桃已经滚到头）
    sp["splat"] = save_crop(cv, "ch2", "splat.png")
    sp["eyes_dead"] = save(A.eye_band(False), "ch2", "eyes_dead.png")
    sp["eyes_hot"] = save(A.eye_band(True), "ch2", "eyes_hot.png")
    sp["egg_bg"] = save(A.egg_insert_bg(), "ch2", "egg_bg.png")
    for key, s in (("egg_big", A.egg_big()), ("skull", A.skull())):
        sp[key] = dict(image=save(s, "ch2", f"{key}.png"), w=s.width, h=s.height)
    sp["plate"] = list(A.PLATE_C)
    # 借条：自己画的小纸片（贴在道场门上），配色跟黄昏走
    iou = Image.new("RGBA", (13, 17), (0, 0, 0, 0))
    d = ImageDraw.Draw(iou)
    d.rectangle([0, 0, 12, 16], fill=(244, 238, 220, 255), outline=tuple(INK) + (255,))
    for yy in (3, 6, 9):
        d.line([(3, yy), (9, yy)], fill=(70, 60, 60, 255))
    d.line([(3, 12), (6, 12)], fill=(70, 60, 60, 255))
    d.rectangle([8, 11, 10, 13], fill=(200, 40, 40, 255))
    iou = C.grade_rgba(iou, tod)
    sp["iou"] = dict(image=save(iou, "ch2", "iou.png"), w=iou.width, h=iou.height)
    stages["ch2"] = sp


# ============================================================== UI（logo、名牌、篇章卡、拟声字）
NAME_CARDS = {
    "shiroyasha": ("坂田银时", "攘夷志士｜人称「白夜叉」"),
    "katsura": ("桂小太郎", "攘夷志士｜不是假发，是桂"),
    "sakamoto": ("坂本辰马", "攘夷志士｜啊哈哈哈"),
    "gintoki": ("坂田银时", "万事屋老板｜天然卷·甜党·死鱼眼"),
    "otose": ("登势", "楼下酒馆老板娘（房东）"),
    "shinpachi": ("志村新八", "吐槽担当｜本体是眼镜"),
    "otae": ("志村妙", "新八的姐姐｜笑容可怕·暗黑料理"),
}
CHAPTERS = {"prologue": ("序章", "白夜叉"), "ch1": ("第一章", "万事屋阿银"), "ch2": ("第二章", "新八登场")}
SFX_WORDS = ["砰!", "咚!", "铿!!", "啪!", "嗖!", "咔嚓!", "抠…抠…", "哈!", "喝!", "呜哇!", "唰!"]
# 第二章的拟声字：照原片 s02 里 sfx_text 的大小、颜色、描边、角度
SFX_STYLED = {
    "啪嚓": dict(color=(255, 255, 255), size=18, angle=10),
    "砰!!": dict(size=34, angle=8),
    "轰!": dict(color=(255, 140, 60), size=26, angle=8),
    "哐啷": dict(color=(255, 255, 255), size=18, angle=-4),
    "咔嚓": dict(color=(214, 214, 226), size=20, angle=10),
    "喂!!": dict(color=(255, 255, 255), outline=(30, 60, 150), size=34, angle=-10),
    "啪": dict(color=(255, 255, 255), size=16, angle=12),
    "嘎嘣": dict(color=(255, 255, 255), size=18, angle=0),
}


def build_ui():
    import scenes._s00_art as A
    from engine import text as T
    ui = {}
    p = out("ui", "logo.png")
    A.logo().save(p)
    ui["logo"] = rel(p)
    p = out("ui", "ribbon.png")
    A.ribbon().save(p)
    ui["ribbon"] = rel(p)
    nc = {}
    import bg_chapters
    cards = dict(NAME_CARDS, **bg_chapters.NAME_CARDS)
    chapters = dict(CHAPTERS, **bg_chapters.CHAPTERS)
    from chars import get_def
    for cid, val in cards.items():
        title, desc = val[0], val[1]
        base = cid.split("@")[0]
        im = rgba_canvas()
        # 键可以写成「角色@别名」：同一个人在不同章节用不同的名牌（颜色按角色）。
        # 第三个值 = 名字旁边的小字（原片用拉丁字母标注，比如 KAGURA；不写就是角色名，标题和角色名一样时会显示两遍）
        if len(val) > 2:
            T.name_card(im, 1.2, 0.0, 2.4, val[2], title, desc, color=get_def(base).color,
                        side=val[3] if len(val) > 3 else "right")      # 第四个值 = 名牌从哪边滑进来
        else:
            T.name_card(im, 1.2, 0.0, 2.4, base, title, desc)
        spr, (x, y) = crop_rgba(im)
        p = out("ui", f"namecard_{cid.replace('@', '_')}.png")
        spr.save(p)
        nc[cid] = dict(image=rel(p), x=x, y=y, w=spr.width, h=spr.height)
    ui["namecards"] = nc
    ch = {}
    for key, (big, small) in chapters.items():
        im = Image.new("RGB", (W, H))
        T.chapter_card(im, 1.0, 0.0, 2.0, big, small)
        p = out("ui", f"chapter_{key}.png")
        im.save(p)
        ch[key] = rel(p)
    ui["chapters"] = ch
    sfx = {}
    for i, word in enumerate(SFX_WORDS):
        im = rgba_canvas()
        T.sfx_text(im, 192, 108, word, 0.35, 0.0)
        spr, (x, y) = crop_rgba(im)
        if spr is None:
            continue
        p = out("ui", f"sfx{i}.png")
        spr.save(p)
        sfx[word] = dict(image=rel(p), ox=x - 192, oy=y - 108)
    from engine.gfx import rotate_nearest
    for j, (word, st) in enumerate(dict(SFX_STYLED, **bg_chapters.SFX).items()):
        spr = T.text_sprite(word, st.get("color", (255, 226, 60)), st.get("size", 24), "hei",
                            outline=st.get("outline", (20, 10, 30)), thick=2)
        if st.get("angle"):
            spr = rotate_nearest(spr, st["angle"])
        p = out("ui", f"sfx_s{j}.png")
        spr.save(p)
        sfx[word] = dict(image=rel(p), ox=-(spr.width // 2), oy=-(spr.height // 2))
    ui["sfx"] = sfx
    # 大字（毛笔字横幅「万事屋，集结！」「两年后……」之类）：键 → { text, size, face, color, outline, thick, angle }
    tx = {}
    for key, st in bg_chapters.TEXTS.items():
        spr = T.text_sprite(st["text"], st.get("color", (255, 255, 255)), st.get("size", 24), st.get("face", "brush"),
                            outline=st.get("outline", (20, 10, 30)), thick=st.get("thick", 2))
        if st.get("angle"):
            spr = rotate_nearest(spr, st["angle"])
        p = out("ui", f"text_{key}.png")
        spr.save(p)
        tx[key] = dict(image=rel(p), w=spr.width, h=spr.height)
    ui["texts"] = tx
    save_meta("ui", ui)
    print(f"ui: logo, {len(nc)} name cards, {len(ch)} chapter cards, {len(sfx)} sfx words")


# ============================================================== 音频（wav → mp3）
MUSIC = ["title", "prologue", "battle", "yorozuya", "comedy", "tension", "ending", "epic", "sad",
         "shinsengumi", "yoshiwara", "flashback"]
SFX = ["blip", "punch", "punch_big", "hit", "kick", "slash", "slash_big", "clang", "whoosh", "jump", "land", "thud",
       "crow", "twinkle", "fly_away", "door", "door_bang", "shock", "sweat", "sting_comedy", "sting_dramatic", "cheer",
       "title_hit", "coin", "crash", "explosion", "gong", "record_scratch", "rimshot", "pop", "dash", "shing", "impact",
       "fanfare", "boing", "fail", "vein", "dizzy", "slap", "sparkle", "heartbeat", "aura", "charge", "bell_shop", "cash",
       "glass", "fall_whistle",
       # 第二章（原片 s02 的音效）
       "crowd", "footsteps", "slide_up", "chomp", "gulp", "wind", "bell", "shine",
       # 第三章到终章
       "gunshot", "machinegun", "bazooka", "bomb_fuse", "explosion_small", "scooter", "engine_hum", "bark", "eat",
       "applause", "drumroll", "train", "rain", "thunder", "laser", "river", "night", "cough", "fire", "run",
       "slide_down", "stab", "squeak", "type"]


def ffmpeg(*args):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-600:])


def build_audio():
    music_dirs = [os.path.join(AUDIO_SRC, "音乐_a"), os.path.join(AUDIO_SRC, "音乐_b")]
    meta = {"music": {}, "sfx": {}}
    for name in MUSIC:
        src = next((os.path.join(d, name + ".wav") for d in music_dirs if os.path.exists(os.path.join(d, name + ".wav"))), None)
        if not src:
            print("  missing music", name)
            continue
        p = out("audio", "music", name + ".mp3")
        if not os.path.exists(p) or os.path.getmtime(p) < os.path.getmtime(src):
            ffmpeg("-i", src, "-c:a", "libmp3lame", "-b:a", "128k", p)
        meta["music"][name] = rel(p)
    for name in SFX:
        src = os.path.join(AUDIO_SRC, "音效", name + ".wav")
        if not os.path.exists(src):
            print("  missing sfx", name)
            continue
        p = out("audio", "sfx", name + ".mp3")
        if not os.path.exists(p) or os.path.getmtime(p) < os.path.getmtime(src):
            ffmpeg("-i", src, "-c:a", "libmp3lame", "-b:a", "128k", p)
        meta["sfx"][name] = rel(p)
    # 用户自己提供的曲子（assets/audio/user/*.mp3，构建时不覆盖），按文件名当曲名
    for up in sorted(glob.glob(os.path.join(ASSETS, "audio", "user", "*.mp3"))):
        meta["music"][os.path.splitext(os.path.basename(up))[0]] = rel(up)
    save_meta("audio", meta)
    print(f"audio: {len(meta['music'])} music, {len(meta['sfx'])} sfx")


# ============================================================== 开场动画（原 s00，两段）
VIDEO_CUTS = [("s00a", 0.0, 8.2), ("s00b", 8.2, None)]


def build_video():
    from engine.render import load_scene, render_frame
    from engine.audio import build_mix
    from engine.core import FPS
    sc = load_scene("s00")
    wav = os.path.join(HERE, "_tmp_s00.wav")
    build_mix([sc], wav)
    meta = {}
    for name, a, b in VIDEO_CUTS:
        b = sc.duration if b is None else b
        n = int(round((b - a) * FPS))
        p = out("video", name + ".mp4")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W * 2}x{H * 2}",
               "-r", str(FPS), "-i", "-", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", wav,
               "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
               "-tune", "animation", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest", p]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(n):
            fr = render_frame(sc, a + i / FPS).resize((W * 2, H * 2), Image.NEAREST)
            proc.stdin.write(fr.tobytes())
        proc.stdin.close()
        proc.wait()
        pw = out("video", name + ".webm")
        ffmpeg("-i", p, "-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0", "-deadline", "good", "-cpu-used", "4",
               "-row-mt", "1", "-c:a", "libopus", "-b:a", "128k", pw)
        meta[name] = dict(src=rel(p), webm=rel(pw), duration=round(b - a, 3))
        print(f"video {name}: {n} frames")
    os.remove(wav)
    save_meta("video", meta)


# ============================================================== 字体（宋体点阵，只收台词里出现的字）
def collect_text():
    chars = set()
    for pat in ("story/*.js", "engine/*.js", "main.js"):
        for f in glob.glob(os.path.join(GAME, pat)):
            src = open(f, encoding="utf-8").read()
            for m in re.finditer(r"(['\"`])((?:\\.|(?!\1).)*)\1", src):
                chars.update(m.group(2))
    chars.update(" !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~")
    chars.update("…—「」『』（）！？，。、：；“”‘’·～＋－×÷■□▼▲►◄★☆♪")
    chars.add("　")                       # 全角空格（菜单里用来对齐）
    return sorted(c for c in chars if (c.isprintable() or c == "　") and c not in "\n\r\t")


def build_font():
    chars = collect_text()
    meta = {}
    for size in (12, 16):
        f = ImageFont.truetype("C:/Windows/Fonts/simsun.ttc", size)
        asc, desc = f.getmetrics()
        lh = asc + desc
        cols = 64
        cell = size + 1
        rows = (len(chars) + cols - 1) // cols
        atlas = Image.new("RGBA", (cols * cell, rows * (lh + 1)), (0, 0, 0, 0))
        d = ImageDraw.Draw(atlas)
        d.fontmode = "1"
        glyphs = {}
        for i, ch in enumerate(chars):
            r, c = divmod(i, cols)
            x, y = c * cell, r * (lh + 1)
            adv = int(round(f.getlength(ch))) or size // 2
            d.text((x, y + asc), ch, font=f, fill=(255, 255, 255, 255), anchor="ls")
            glyphs[ch] = [x, y, adv]
        p = out("font", f"simsun{size}.png")
        atlas.save(p)
        meta[str(size)] = dict(image=rel(p), lh=lh, asc=asc, glyphs=glyphs)
    save_meta("font", meta)
    print(f"font: {len(chars)} glyphs x 2 sizes")


# ============================================================== data.js
def build_data():
    data = {}
    for name in ("chars", "bg", "ui", "audio", "video", "font"):
        p = os.path.join(META, name + ".json")
        if os.path.exists(p):
            data[name] = json.load(open(p, encoding="utf-8"))
        else:
            print("  (no meta for", name, ")")
    js = "window.GAME_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    with open(os.path.join(GAME, "data.js"), "w", encoding="utf-8") as fh:
        fh.write(js)
    print(f"data.js: {len(js) / 1024:.0f} KB")


STEPS = dict(chars=build_chars, bg=build_bg, ui=build_ui, audio=build_audio, video=build_video, font=build_font, data=build_data)

if __name__ == "__main__":
    todo = sys.argv[1:] or ["chars", "bg", "ui", "audio", "font", "data"]
    for s in todo:
        t0 = time.time()
        STEPS[s]()
        print(f"  [{s}] {time.time() - t0:.1f}s")
