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
    # 角色的说话音高（原工程 voice 参数），用于打字音
    from chars import get_def
    for cid in meta:
        d = get_def(cid.split("__")[0])
        meta[cid]["voice"] = getattr(d, "voice", 1.0) if d else 1.0
    save_meta("chars", meta)
    print(f"chars: {len(meta)}")


# ============================================================== 背景
def build_bg():
    from bg import common as C, kabukicho as K, edo as E, yorozuya as Y
    from bg._draw import graded_layer
    from engine.core import rng
    import scenes._s00_art as A
    import scenes._s02_art as S02
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

    term = C.cached(("terminal", tod), lambda: E._terminal_layer(tod))
    term.save(out("bg", "street", "terminal.png"))
    back = graded_layer(("kabuki_back",), K._back_row, tod, depth=0.45, glow_radius=2, glow_strength=0.35)
    back.save(out("bg", "street", "back.png"))
    mid = graded_layer(("kabuki_mid",), K._mid_row, tod, depth=0.22, glow_radius=2, glow_strength=0.45)
    mid.save(out("bg", "street", "mid.png"))
    fac = K._facade(tod)
    fac.save(out("bg", "street", "facade.png"))
    road_h = H - K.BASE_Y
    strip, rows = C.cached(("stone", road_h, tod), lambda: C._stone_strip(road_h, tod))
    strip.save(out("bg", "street", "road.png"))
    gut = C.cached(("kabuki_gutter", tod), lambda: K._gutter_strip(tod))
    gut.save(out("bg", "street", "gutter.png"))
    K._dyn()
    dyn = K._DYN
    lanterns = []
    for i, (lx, ly, col, size, txt) in enumerate(dyn["lanterns"]):
        spr = C.cached(("lantern", tuple(col[:3]), size, False, txt), lambda: C._lantern_sprite(col, size, False, txt))
        p = out("bg", "street", f"lantern{i}.png")
        spr.save(p)
        lanterns.append(dict(x=lx, y=ly, size=size, image=rel(p), w=spr.width))
    flags = []
    pole_c = C.grade_color((70, 60, 56), tod)
    for i, (fx, fy, col, text, tcol) in enumerate(dyn["flags"]):
        frames = C.cached(("kflag", i, tod), lambda: K._flag_frames(col, text, tcol, tod))
        ps = []
        for k, fr in enumerate(frames):
            p = out("bg", "street", f"flag{i}_{k}.png")
            fr.save(p)
            ps.append(rel(p))
        flags.append(dict(x=fx, y=fy, frames=ps))
    stages["street"] = dict(
        period=K.STREET_W, floor=K.FLOOR_Y, base=K.BASE_Y,
        yorozuya=dict(x=K.YOROZUYA_X, window=K.YOROZUYA_WINDOW, door=K.YOROZUYA_DOOR, updoor=K.YOROZUYA_UPDOOR,
                      stairs=K.STAIRS, balcony_y=K.STREET_BALCONY_Y),
        layout=[list(x) for x in K._LAYOUT],
        layers=[
            dict(type="static", image="assets/bg/street/sky.png"),
            export_clouds("street", tod, seed=11, count=6, y0=2, y1=40, cam_mul=0.5),
            dict(type="terminal", image="assets/bg/street/terminal.png", w=term.width, h=term.height, k=0.08),
            dict(type="wrap", image="assets/bg/street/back.png", period=1024, k=0.3, y=0),
            dict(type="wrap", image="assets/bg/street/mid.png", period=896, k=0.55, y=0),
            dict(type="wrap", image="assets/bg/street/facade.png", period=K.STREET_W, k=1.0, y=0),
            dict(type="rows", image="assets/bg/street/road.png", period=192, y=K.BASE_Y, h=road_h, rows=[list(r) for r in rows]),
            dict(type="wrap", image="assets/bg/street/gutter.png", period=16, k=1.0, y=K.BASE_Y, h=4),
            dict(type="lanterns", period=K.STREET_W, items=lanterns, string=4, color=[40, 30, 34]),
            dict(type="flags", period=K.STREET_W, items=flags, base=K.BASE_Y, pole=list(pole_c)),
        ],
        fg=[dict(type="poles", period=520, k=1.5, col=list(C.grade_color((34, 30, 40), tod)), hi=list(C.grade_color((60, 56, 66), tod)))],
    )

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

    # 第二章：家庭餐厅、道场门口与道场内。把原工程的整屏画面直接烘焙，
    # 这样 file:// 模式不需要加载 Python 或额外的运行时依赖。
    rest = S02.rest_bg().convert("RGBA")
    rest.alpha_composite(S02.window_overlay())
    S02.draw_lamps(rest, 0.0); S02.draw_clock_hands(rest, 0.0)
    rest.save(out("bg", "restaurant", "base.png"))
    dojo = Image.new("RGB", (W, H)); dojo.paste(S02.dojo_bg())
    dojo.save(out("bg", "dojo", "base.png"))
    gate_back = S02.gate_back(); gate_back.save(out("bg", "dojo_gate", "back.png"))
    gate_front = S02.gate_front(); gate_front.save(out("bg", "dojo_gate", "front.png"))
    eye = S02.eye_band(True); eye.save(out("bg", "insert_eye.png"))
    egg = S02.egg_insert_bg().convert("RGBA"); eb = S02.egg_big(); egg.alpha_composite(eb, (112, 62)); sk = S02.skull(); egg.alpha_composite(sk, (166, 28)); egg.convert("RGB").save(out("bg", "insert_egg.png"))
    parfait = Image.new("RGB", (W, H)); parfait.paste(S02.rest_bg()); pbig = S02.parfait_big(2); parfait.paste(pbig, ((W-pbig.width)//2, 54), pbig); parfait.save(out("bg", "insert_parfait.png"))
    stages["restaurant"] = dict(layers=[dict(type="static", image="assets/bg/restaurant/base.png")])
    stages["dojo"] = dict(layers=[dict(type="static", image="assets/bg/dojo/base.png")])
    stages["dojo_gate"] = dict(layers=[dict(type="static", image="assets/bg/dojo_gate/back.png"), dict(type="static", image="assets/bg/dojo_gate/front.png")])
    stages["insert_eye"] = dict(layers=[dict(type="static", image="assets/bg/insert_eye.png")])
    stages["insert_egg"] = dict(layers=[dict(type="static", image="assets/bg/insert_egg.png")])
    stages["insert_parfait"] = dict(layers=[dict(type="static", image="assets/bg/insert_parfait.png")])
    save_meta("bg", stages)
    print("bg: street / office / war / title / restaurant / dojo")


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
SFX_WORDS = ["砰!", "咚!", "铿!!", "啪!", "嗖!", "咔嚓!", "抠…抠…", "哈!", "喝!", "呜哇!", "唰!", "嘎嘣!", "轰!"]


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
    for cid, (title, desc) in NAME_CARDS.items():
        im = rgba_canvas()
        T.name_card(im, 1.2, 0.0, 2.4, cid, title, desc)
        spr, (x, y) = crop_rgba(im)
        p = out("ui", f"namecard_{cid}.png")
        spr.save(p)
        nc[cid] = dict(image=rel(p), x=x, y=y, w=spr.width, h=spr.height)
    ui["namecards"] = nc
    ch = {}
    for key, (big, small) in CHAPTERS.items():
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
    ui["sfx"] = sfx
    save_meta("ui", ui)
    print(f"ui: logo, {len(nc)} name cards, {len(ch)} chapter cards, {len(sfx)} sfx words")


# ============================================================== 音频（wav → mp3）
MUSIC = ["title", "prologue", "battle", "yorozuya", "comedy", "tension", "ending", "epic", "sad"]
SFX = ["blip", "punch", "punch_big", "hit", "kick", "slash", "slash_big", "clang", "whoosh", "jump", "land", "thud",
       "crow", "twinkle", "fly_away", "door", "door_bang", "shock", "sweat", "sting_comedy", "sting_dramatic", "cheer",
       "title_hit", "coin", "crash", "explosion", "gong", "record_scratch", "rimshot", "pop", "dash", "shing", "impact",
       "fanfare", "boing", "fail", "vein", "dizzy", "slap", "sparkle", "heartbeat", "aura", "charge", "bell_shop", "cash",
       "glass", "fall_whistle"]


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
