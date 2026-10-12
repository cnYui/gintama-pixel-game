"""第三章到终章的布景导出（build_assets.py 的 bg / ui 步骤会调用这里）。

每章一个函数 chN(stages, c)：c 是 build_assets 传进来的工具（out / rel / crop_rgba / rgba_canvas / export_clouds / W / H），
往 stages 里加这一章的地图（图层写法见 engine/gfx.js 的 Background.layer）和小道具。
NAME_CARDS / CHAPTERS 会并进 build_assets 的名牌和篇章卡（名牌的键可以写「角色@别名」）。
"""
import math

from PIL import Image, ImageDraw

NAME_CARDS = {}
CHAPTERS = {}
TEXTS = {}      # 大字图：键 → dict(text, size, face('brush' / 'brush2' / 'hei' / 'kai'), color, outline, thick, angle)
SFX = {}        # 拟声字（G.fx.word 用）：字 → dict(color, size, outline, angle)，并进 build_assets 的 SFX_STYLED


def build_all(stages, c):
    for fn in CHAPTER_FUNCS:
        fn(stages, c)


def _tools(c):
    out, rel = c["out"], c["rel"]

    def save(img, *p):
        path = out("bg", *p)
        img.save(path)
        return rel(path)

    def crop(im):
        bb = im.getbbox()
        return im.crop(bb), bb[0], bb[1]

    def grab(fn, folder, name, anchor=(192, 160)):
        """在透明画布上按锚点画一个小道具，裁好；返回 image + 相对锚点的偏移 ox/oy + 宽高。"""
        cv = Image.new("RGBA", (c["W"], c["H"]), (0, 0, 0, 0))
        fn(cv, *anchor)
        spr, x, y = crop(cv)
        return dict(image=save(spr, folder, name), ox=x - anchor[0], oy=y - anchor[1], w=spr.width, h=spr.height)

    def grab_add(fn, folder, name, anchor=(150, 160)):
        """只能画在 RGB 上的效果（光锥等）：黑底画好，存成相加混合用的图。"""
        cv = Image.new("RGB", (c["W"], c["H"]))
        fn(cv, *anchor)
        spr, x, y = crop(cv)
        return dict(image=save(spr, folder, name), ox=x - anchor[0], oy=y - anchor[1], w=spr.width, h=spr.height, blend="lighter")

    def sprite(im, folder, name):
        return dict(image=save(im, folder, name), w=im.width, h=im.height)
    return save, crop, grab, grab_add, sprite


# ============================================================== 第三章：神乐与定春（原片 s03）
CHAPTERS["ch3"] = ("第三章", "神乐与定春")
NAME_CARDS["kagura"] = ("神乐", "夜兔族少女｜怪力·大胃王·『阿鲁』", "KAGURA")
NAME_CARDS["sadaharu"] = ("定春", "巨型犬｜爱咬银时的头", "SADAHARU")
TEXTS["yorozuya_assemble"] = dict(text="万事屋，集结！", size=32, face="brush", color=(255, 236, 110), outline=(24, 20, 37), thick=2, angle=-4)
SFX.update({
    "站住!!": dict(color=(255, 255, 255), size=16, angle=6),
    "哒哒哒哒!!": dict(size=26, angle=-6),
    "扒!": dict(color=(255, 255, 255), size=20, angle=10),
    "！？": dict(color=(255, 255, 255), size=28, angle=0),
    "空……": dict(color=(200, 210, 255), size=20, angle=0),
    "嘭!!": dict(size=28, angle=8),
    "乖～": dict(color=(255, 255, 255), size=14, angle=-6),
    "咔嚓!!": dict(color=(255, 90, 90), size=28, angle=12),
    "嚼": dict(color=(255, 120, 120), size=18, angle=10),
})


def ch3(stages, c):
    from bg import common as C, kabukicho as K, yorozuya as Y
    from engine.gfx import INK, rect, pset
    from scenes import _s03_props as P, s03_kagura as S3
    save, crop, grab, grab_add, sprite = _tools(c)
    W, H = c["W"], c["H"]

    # 夜里的大街（第一段：骑小绵羊回家、撞上神乐、打黑道）
    c["export_street"]("street_night", "night")
    # 夜里的事务所：环境帧取 t = 5.0–6.75（窗外的飞碟这段时间不在，循环不会跳）
    amb = []
    for k in range(8):
        im = Image.new("RGB", (W, H))
        Y.office(im, 5.0 + k * 0.25, "night")
        amb.append(save(im, "office_night", f"amb{k}.png"))
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    Y.office_fg(fg, 0, "night")
    stages["office_night"] = dict(amb=amb, amb_fps=4, door=amb[:1], fg=save(fg, "office_night", "fg.png"))
    # 万事屋门口（黄昏）= 往下挪 36 px 的大街，镜头固定在 _FCAM；加上电线杆 / 电线 / 「歌舞伎町」牌，阳台栏杆是前景
    c["export_street"]("front_dusk", "dusk", dy=K.FRONT_DY)
    fr = stages["front_dusk"]
    a, b = Image.new("RGB", (W, H)), Image.new("RGB", (W, H))
    K.street(a, K._FCAM, 0.0, "dusk", dy=K.FRONT_DY)
    K.yorozuya_front(b, 0.0, "dusk")
    import numpy as np
    ov = Image.fromarray(np.dstack([np.asarray(b), (np.asarray(a) != np.asarray(b)).any(2).astype(np.uint8) * 255]), "RGBA")
    spr, x, y = crop(ov)
    fr["layers"].append(dict(type="image", image=save(spr, "front_dusk", "front_overlay.png"), x=x + K._FCAM, y=y))
    rail = C.cached(("kabuki_rail", "dusk"), lambda: K._railing_sprite("dusk"))
    fr["fg"] = [dict(type="image", image=save(rail, "front_dusk", "railing_fg.png"), x=K._YX0, y=K.FRONT_DY, alpha=1)]
    fr.update(camX=K._FCAM, balcony_y=K.BALCONY_Y)

    # 小道具
    sp = {}
    sp["scooter"] = dict(frames=[save(P.scooter_sprite(f), "ch3", f"scooter{f}.png") for f in (0, 1)], ax=22, ay=27,
                         seat=-P.SC_SEAT[1], dx=P.SC_SEAT[0])

    def dent(cv, x, y):              # 撞坏的小绵羊（同 s03_kagura.scooter_damage 的静态部分）
        P.draw_scooter(cv, x, y, 0, moving=False)
        sx0, sy0 = int(x) - P.SC_W // 2, int(y) - P.SC_H + 1
        ImageDraw.Draw(cv).line([(sx0 + 30, sy0 + 5), (sx0 + 28, sy0 + 9), (sx0 + 31, sy0 + 12), (sx0 + 29, sy0 + 16)], fill=INK)
        rect(cv, sx0 + 32, sy0 + 6, 3, 3, (70, 66, 80))
        pset(cv, sx0 + 33, sy0 + 7, (160, 156, 120))
    sp["scooter_down"] = grab(dent, "ch3", "scooter_dented.png")
    sp["headlight"] = grab_add(lambda cv, x, y: S3.headlight(cv, x, y, 1.0), "ch3", "headlight.png")
    sp["coin"] = dict(frames=[grab(lambda cv, x, y, f=f: P.draw_coin(cv, x, y, f / 10 + 1e-3), "ch3", f"coin{f}.png")["image"] for f in (0, 1)])
    sp["moth"] = dict(frames=[grab(lambda cv, x, y, f=f: P.draw_moth(cv, x, y, f / 12 + 1e-3), "ch3", f"moth{f}.png")["image"] for f in (0, 1)])
    for k, im in (("bowl", P.bowl_sprite(False)), ("small_bowl", P.small_bowl_sprite()),
                  ("wallet_closed", P.wallet_sprite(False)), ("wallet_open", P.wallet_sprite(True))):
        sp[k] = sprite(im, "ch3", k + ".png")
    # 纸箱「请收养」：后片 + 前片合成一张（关着 / 打开）
    for key, fl in (("box", 0.0), ("box_open", 1.0)):
        cv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        P.draw_box_back(cv, 192, 160, fl)
        P.draw_box_front(cv, 192, 160, fl)
        spr, x, y = crop(cv)
        sp[key] = dict(image=save(spr, "ch3", key + ".png"), w=spr.width, h=spr.height, ox=x - 192, oy=y - 160)
    # 夜路上的障碍：木箱、垃圾桶（自己画，按夜里调色）
    crate = Image.new("RGBA", (16, 15), (0, 0, 0, 0))
    d = ImageDraw.Draw(crate)
    d.rectangle([0, 0, 15, 14], fill=(150, 104, 62, 255), outline=INK + (255,))
    for yy in (4, 9):
        d.line([(1, yy), (14, yy)], fill=(112, 76, 46, 255))
    d.line([(1, 1), (14, 13)], fill=(112, 76, 46, 255))
    bin_ = Image.new("RGBA", (12, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(bin_)
    d.rectangle([1, 3, 10, 15], fill=(120, 130, 140, 255), outline=INK + (255,))
    d.rectangle([0, 1, 11, 3], fill=(150, 160, 170, 255), outline=INK + (255,))
    for xx in (4, 7):
        d.line([(xx, 5), (xx, 13)], fill=(96, 104, 114, 255))
    sp["crate"] = sprite(C.grade_rgba(crate, "night"), "ch3", "crate.png")
    sp["bin"] = sprite(C.grade_rgba(bin_, "night"), "ch3", "bin.png")
    # 神乐收起来的伞（靠在事务所墙边）：紫色伞面、灰色伞尖、弯把手
    um = Image.new("RGBA", (9, 38), (0, 0, 0, 0))
    d = ImageDraw.Draw(um)
    o = INK + (255,)
    d.polygon([(4, 6), (7, 12), (6, 30), (2, 30), (1, 12)], fill=(150, 96, 178, 255), outline=o)
    d.line([(3, 9), (3, 29)], fill=(112, 66, 140, 255))
    d.line([(5, 10), (5, 28)], fill=(186, 140, 210, 255))
    d.line([(4, 30), (4, 37)], fill=(84, 80, 96, 255))             # 伞尖
    d.line([(4, 1), (4, 6)], fill=(60, 56, 70, 255))               # 伞柄
    d.arc([1, 0, 7, 6], 180, 360, fill=(60, 56, 70, 255))          # 弯把手
    sp["umbrella"] = sprite(um, "ch3", "umbrella.png")
    stages["ch3"] = sp


# ============================================================== 第五章：桂与伊丽莎白（原片 s05）
CHAPTERS["ch5"] = ("第五章", "桂与伊丽莎白")
NAME_CARDS["katsura@s05"] = ("桂小太郎", "攘夷志士｜逃跑的小太郎·天然呆", "KATSURA")
NAME_CARDS["elizabeth"] = ("伊丽莎白", "谜之生物｜只用牌子说话", "ELIZABETH")
TEXTS["zura_1"] = dict(text="不是假发", size=34, face="brush", color=(255, 255, 255), outline=(24, 20, 37), thick=2)
TEXTS["zura_2"] = dict(text="是桂！", size=60, face="brush", color=(255, 226, 70), outline=(150, 20, 40), thick=3)
SFX.update({
    "咻——": dict(color=(255, 255, 255), size=18),
    "嘎——!": dict(color=(255, 255, 255), size=20, angle=6),
    "嗤嗤…": dict(color=(255, 230, 150), size=14),
    "轰!!": dict(color=(255, 200, 70), size=24, angle=-12),
    "轰!!!": dict(color=(255, 200, 70), size=40, angle=-10),
    "嘿咻!": dict(color=(255, 255, 255), size=18, angle=-8),
    "咚——!": dict(color=(255, 240, 180), size=20, angle=-6),
    "咳": dict(color=(230, 230, 236), size=18, angle=-8),
    "阿呆～": dict(color=(255, 255, 255), size=14, angle=6),
    "啵": dict(color=(255, 200, 80), size=16, angle=10),
    "锁定": dict(color=(255, 90, 90), size=12),
    "？": dict(color=(255, 255, 255), size=24),
})


def ch5(stages, c):
    from bg import common as C, edo as E
    from bg._draw import graded_layer
    from chars import render_sprite
    from chars.katsura import draw_bomb
    from engine.gfx import INK
    import numpy as np
    import scenes.s05_katsura as S5
    save, crop, grab, grab_add, sprite = _tools(c)
    W, H = c["W"], c["H"]
    tod = "dusk"

    # ---- 江户屋顶（横版跑酷）：9 层视差，可走的屋脊在 y = 150，屋顶条每 512 px 重复，多长都行
    sky = Image.new("RGB", (W, H))
    C.sky(sky, tod, 0.0, horizon=150, stars=False)
    far_m, near_m = C.cached(("mtn", tod), lambda: C._mountain_layers(tod))
    term = C.cached(("terminal", tod), lambda: E._terminal_layer(tod))
    lay = {"far_city": graded_layer(("edo_far",), E._far_city, tod, depth=0.5, glow_radius=2, glow_strength=0.3),
           "castle": graded_layer(("edo_castle",), E._castle_layer, tod, depth=0.32),
           "mid_city": graded_layer(("edo_mid",), E._mid_city, tod, depth=0.18, glow_radius=3, glow_strength=0.45),
           "near_roofs": graded_layer(("edo_near",), E._near_roofs, tod, depth=0.0, glow_radius=3, glow_strength=0.5),
           "roof_walk": graded_layer(("roofwalk",), E._walk_layer, tod, depth=0.0, glow_radius=3, glow_strength=0.5)}
    f = {k: save(v, "roof_dusk", k + ".png") for k, v in lay.items() if k != "near_roofs"}
    stages["roof_dusk"] = dict(floor=150, layers=[
        dict(type="static", image=save(sky, "roof_dusk", "sky.png")),
        c["export_clouds"]("roof_dusk", tod, seed=3, count=6, y0=4, y1=70, cam_mul=1.0),
        dict(type="wrap", image=save(far_m, "roof_dusk", "mtn_far.png"), period=768, k=0.05, y=68),
        dict(type="wrap", image=save(near_m, "roof_dusk", "mtn_near.png"), period=768, k=0.12, y=68),
        dict(type="terminal", image=save(term, "roof_dusk", "terminal.png"), w=term.width, h=term.height, k=0.1),
        dict(type="wrap", image=f["far_city"], period=896, k=0.25, y=0),
        dict(type="wrap", image=f["castle"], period=1536, k=0.4, y=0),
        dict(type="wrap", image=f["mid_city"], period=1024, k=0.6, y=0),
        dict(type="wrap", image=f["roof_walk"], period=512, k=1.0, y=150 - 30)])

    # ---- 黄昏的大街（同白天大街的做法）
    c["export_street"]("street_dusk", "dusk")

    # ---- 烟花的天空（原片 S5：低机位，镜头固定在 cam = -1010）：天空 + 云 + 一张城市叠层
    sky5 = Image.new("RGB", (W, H))
    C.sky(sky5, tod, 0.0, horizon=186, stars=False)
    city = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    def put(im, sx, y):
        city.alpha_composite(im.crop((sx, 0, sx + W, im.height)), (0, y))
    put(far_m, int(-1010 * 0.05) % 768, 104)
    put(near_m, int(-1010 * 0.12) % 768, 104)
    city.alpha_composite(term, (293 - term.width // 2, 150 + 36 - term.height + 12))
    for k, p, kk in (("far_city", 896, 0.25), ("castle", 1536, 0.4), ("mid_city", 1024, 0.6), ("near_roofs", 768, 1.0)):
        put(lay[k], math.floor(-1010 * kk) % p, 36)
    put(lay["roof_walk"], 40, 208 - 30)
    stages["fw_sky"] = dict(camX=-1010, layers=[
        dict(type="static", image=save(sky5, "fw_sky", "sky.png")),
        c["export_clouds"]("fw_sky", tod, seed=3, count=6, y0=4, y1=106, cam_mul=1.0),
        dict(type="image", image=save(city, "fw_sky", "city.png"), x=-1010, y=0)])

    # ---- 小道具
    sp = {"closeup_bg": save(S5._closeup_bg(), "ch5", "closeup_bg.png"), "shell": sprite(S5._shell_sprite(), "ch5", "shell.png")}
    crow = []
    for k in range(2):
        S5._CROW.clear()
        cv = Image.new("RGBA", (40, 20), (0, 0, 0, 0))
        S5.crow(cv, 20, 10, k / 8 + 1e-4, facing=1)
        crow.append(save(cv.crop(cv.getbbox()), "ch5", f"crow{k}.png"))
    sp["crow"] = dict(frames=crow, fps=8)
    bomb = []
    for k in range(12):                       # 炸弹中心在 (7, 11)；导火线的火花每 1/12 秒变一次
        cv = Image.new("RGBA", (16, 18), (0, 0, 0, 0))
        draw_bomb(cv, 7, 11, k / 12 + 1e-4)
        bomb.append(save(cv, "ch5", f"bomb{k}.png"))
    sp["bomb"] = dict(frames=bomb, fps=12, ax=7, ay=11)
    flames = []
    for k in range(3):                        # 爆炸头上着的小火苗：底部锚点 (12, 22)
        cv = Image.new("RGB", (24, 26), (255, 0, 255))
        S5.afro_flame(cv, 12, 22, 5.0 + k / 12 + 1e-4, 0.0)
        a = np.asarray(cv).copy()
        key = (a[..., 0] == 255) & (a[..., 1] == 0) & (a[..., 2] == 255)
        flames.append(save(Image.fromarray(np.dstack([a, np.where(key, 0, 255).astype(np.uint8)]), "RGBA"), "ch5", f"afro_flame{k}.png"))
    sp["afro_flame"] = dict(frames=flames, fps=12, ax=12, ay=22)

    def scope_ring(locked, r):                 # 冲田的瞄准镜（原片 scope_inset 的外圈，缩小成跑酷里的准星）
        cv = Image.new("RGBA", (2 * r + 7, 2 * r + 7), (0, 0, 0, 0))
        d = ImageDraw.Draw(cv)
        cx = cy = r + 3
        col = (255, 70, 70) if locked else (210, 255, 200)
        d.line([(cx - r + 3, cy), (cx - 3, cy)], fill=col)
        d.line([(cx + 3, cy), (cx + r - 3, cy)], fill=col)
        d.line([(cx, cy - r + 3), (cx, cy - 3)], fill=col)
        d.line([(cx, cy + 3), (cx, cy + r - 3)], fill=col)
        d.ellipse([cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1], outline=INK, width=3)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(98, 118, 72) if not locked else (150, 40, 40), width=1)
        return cv
    for k, lk in (("scope_green", False), ("scope_red", True)):
        im = scope_ring(lk, 13)
        sp[k] = dict(image=save(im, "ch5", k + ".png"), w=im.width, h=im.height)
    # 屋顶之间的缝：往下看是黑漆漆的小巷（几扇亮着的窗）
    gap = Image.new("RGBA", (24, 70), (0, 0, 0, 0))
    d = ImageDraw.Draw(gap)
    d.rectangle([1, 0, 22, 69], fill=(26, 20, 38, 255))
    for yy, xx, col in ((14, 5, (196, 150, 92)), (14, 15, (150, 112, 74)), (36, 9, (196, 150, 92)), (52, 4, (120, 92, 70))):
        d.rectangle([xx, yy, xx + 3, yy + 2], fill=col + (255,))
    for x0 in (0, 23):
        d.line([(x0, 0), (x0, 69)], fill=INK + (255,))
    d.rectangle([0, 0, 2, 3], fill=(96, 100, 128, 255))
    d.rectangle([21, 0, 23, 3], fill=(96, 100, 128, 255))
    sp["gap"] = sprite(gap, "ch5", "roof_gap.png")
    sp["glyph_kei"] = [[round(x, 1), round(y, 1)] for x, y in S5._glyph_points("桂")]
    # 烟花下的逆光剪影（冲田、土方，放大 2 倍）：暗色身体 + 白色轮廓光（游戏里按烟花的颜色染）
    def backlit_frames(cid, pose, ts, p, folder):
        out_b, out_r, piv = [], [], None
        for i, t in enumerate(ts):
            spr, ax, ay = render_sprite(cid, pose, t, p, None, -1, scale=2)
            spr = spr.convert("RGBA")
            body = S5.backlit(spr, (0, 0, 0), 0.0)
            a = np.asarray(spr)
            op = a[..., 3] > 0
            rgb = a[..., :3].astype(np.float32)
            smoke = op & (np.abs(rgb[..., 0] - rgb[..., 1]) < 14) & (rgb[..., 2] >= rgb[..., 0]) & (rgb[..., 0] > 150)
            edge = np.zeros_like(op)
            for k in (1, 2):
                up = np.zeros_like(op); up[k:, :] = op[:-k, :]
                lf = np.zeros_like(op); lf[:, k:] = op[:, :-k]
                edge |= op & (~up | ~lf)
            edge &= ~smoke
            m = np.zeros(a.shape, np.uint8)
            m[edge] = (255, 255, 255, 255)
            out_b.append(save(body, folder, f"{cid}_body{i}.png"))
            out_r.append(save(Image.fromarray(m, "RGBA"), folder, f"{cid}_rim{i}.png"))
            piv = (int(ax), int(ay))
        return dict(body=out_b, rim=out_r, ax=piv[0], ay=piv[1])
    sp["sil_okita"] = dict(backlit_frames("okita", "bazooka", [k / 4 + 1e-4 for k in range(4)], 0.2, "ch5_sil"), fps=4)
    sp["sil_hijikata"] = dict(backlit_frames("hijikata", "smoke", [12.5 + k / 12 + 1e-4 for k in range(21)], None, "ch5_sil"), fps=12)
    stages["ch5"] = sp


# ============================================================== 第四章：真选组（原片 s04）
CHAPTERS["ch4"] = ("第四章", "真选组")
NAME_CARDS["kondo"] = ("近藤勋", "局长｜大猩猩·跟踪狂", "KONDO")
NAME_CARDS["hijikata"] = ("土方十四郎", "鬼之副长｜蛋黄酱狂魔", "HIJIKATA")
NAME_CARDS["okita"] = ("冲田总悟", "一番队队长｜抖S王子", "OKITA", "left")
SFX.update({
    "杀气": dict(color=(214, 150, 255), size=18, angle=-6),
    "闪～☆": dict(color=(255, 250, 200), size=16, angle=-8),
    "怒": dict(color=(255, 60, 60), size=34, angle=8),
    "喂！": dict(color=(255, 255, 255), size=16, angle=10),
    "！": dict(color=(255, 255, 255), size=24),
})


def _matte(draw, W, H, size=None):
    """画到 RGB 上的东西 → 准确的 RGBA（黑底、白底各画一次反解透明度）。透明画布上直接画会出错（见 s04 调研）。"""
    import numpy as np
    size = size or (W, H)
    a = Image.new("RGB", size, (0, 0, 0)); draw(a)
    b = Image.new("RGB", size, (255, 255, 255)); draw(b)
    a, b = np.asarray(a).astype(np.int32), np.asarray(b).astype(np.int32)
    al = np.clip(255 - (b - a).max(axis=2), 0, 255)
    return Image.fromarray(np.dstack([np.clip(a * 255 // np.maximum(al, 1)[..., None], 0, 255), al]).astype(np.uint8), "RGBA")


def ch4(stages, c):
    from bg import common as C, edo as E
    from bg._draw import graded_layer, paste_layer
    from chars.hijikata import sweat_drop
    from chars.kondo import _bush
    from engine.core import rng
    from engine.gfx import INK
    from scenes import _s04_art as A, s04_shinsengumi as S
    save, crop, _grab, _grab_add, sprite = _tools(c)
    W, H = c["W"], c["H"]
    matte = lambda draw, size=None: _matte(draw, W, H, size)  # noqa: E731

    def sky(folder, horizon):
        im = Image.new("RGB", (W, H)); C.sky(im, "day", 0.0, horizon=horizon)
        return dict(type="static", image=save(im, folder, "sky.png"))
    PLAN = (("saucer", 42, 9, 0.2, 0.25, False), ("saucer", 66, -6, 0.3, 0.15, False), ("cruiser", 16, 3.5, 0.12, 0.5, True),
            ("shuttle", 84, -14, 0.35, 0.1, False), ("cruiser", 34, -2.2, 0.08, 0.62, True))

    def ships(folder, far, cam_x, dy):
        items = []
        for i, (kind, y, v, k, hz, f) in enumerate(PLAN):
            if f != far:
                continue
            s = E._ship_sprite(kind, 1, 1 if v > 0 else -1, "day", hz)
            items.append(dict(i=i, image=save(s, folder, f"ship{i}.png"), w=s.width, h=s.height, x0=round(i * 157 - cam_x * k, 2), y=y + dy, vx=v, k=k))
        return dict(type="edo_ships", span=W + 240, items=items)

    def skyline(folder, cam_x, dy):           # 固定镜头的江户天际线（远山、飞船、航站楼、远处的城、江户城）
        far = graded_layer(("edo_far",), E._far_city, "day", depth=0.5, glow_radius=2, glow_strength=0.3)
        cas = graded_layer(("edo_castle",), E._castle_layer, "day", depth=0.32)
        mid = graded_layer(("edo_mid",), E._mid_city, "day", depth=0.18, glow_radius=3, glow_strength=0.45)
        term = C.cached(("terminal", "day"), lambda: E._terminal_layer("day"))
        return [dict(type="image", x=0, y=0, image=save(matte(lambda im: C.far_mountains(im, cam_x, "day", 138 + dy)), folder, "mountains.png")),
                ships(folder, True, cam_x, dy),
                dict(type="terminal", image=save(term, folder, "terminal.png"), w=term.width, h=term.height, k=0.1, dy=dy,
                     cx=E.TERMINAL_SX - cam_x * 0.1, side_px=False),
                dict(type="image", x=0, y=0, image=save(matte(lambda im: paste_layer(im, far, 896, cam_x * 0.25, dy)), folder, "far_city.png")),
                ships(folder, False, cam_x, dy),
                dict(type="image", x=0, y=0, image=save(matte(lambda im: (paste_layer(im, cas, 1536, cam_x * 0.4, dy),
                                                                          paste_layer(im, mid, 1024, cam_x * 0.6, dy))), folder, "castle_mid.png"))]

    def flag(folder, n, px, py, **kw):         # 诚字旗：12 fps，n 帧正好是整数个波动周期，循环不跳
        ims = [matte(lambda im, k=k: A.draw_flag(im, 60, 40, k / 12 + 1e-6, **kw), size=(240, 160)) for k in range(n)]
        bb = [f(i.getbbox()[j] for i in ims) for j, f in enumerate((min, min, max, max))]
        return dict(type="frames", x=px - 60 + bb[0], y=py - 40 + bb[1], fps=12,
                    frames=[save(im.crop(bb), folder, f"flag{k}.png") for k, im in enumerate(ims)])

    def clouds(folder, seed, count, y0, y1):
        return c["export_clouds"](folder, "day", seed=seed, count=count, y0=y0, y1=y1, cam_mul=1.0)

    # ---- 屯所大门（固定镜头，脚点 y 160）
    gl = A.gate_layer()
    stages["hq_gate"] = dict(floor=160, layers=[sky("hq_gate", 150), clouds("hq_gate", 3, 6, 4, 70)] + skyline("hq_gate", 0, 0) + [
        dict(type="birds", n=3, seed=4, y=26, speed=26.0),
        dict(type="image", x=0, y=0, image=save(matte(lambda im: (C.stone_street(im, 160, 0, "day"), im.paste(gl, (0, 0), gl))), "hq_gate", "street_gate.png")),
        flag("hq_gate", 58, 319, 10, w=44, h=30, size=20, amp=2.0)], fg=[dict(type="sakura", n=10, seed=4, wind=30, fall=14, alpha=1)])
    # ---- 食堂（640 宽，镜头 0..256）
    raw = C.cached(("roomwall_raw", "shoji", 136), lambda: C._room_wall_strip("shoji", 136))
    floor_, rows = C.cached(("wood", 112, "day_in"), lambda: C._wood_strip(112, "day_in"))
    beams = Image.new("RGBA", (A.CANTEEN_W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(beams)
    for bx in (60, 250, 420, 560):
        d.polygon([(bx, 20), (bx + 26, 20), (bx + 96, 170), (bx + 60, 170)], fill=(255, 244, 210, 34))
    zx = S.OKI_NAP_X - 22                     # 冲田午睡的红坐垫
    d.rectangle([zx - 1, 156, zx + 18, 160], fill=INK + (255,)); d.rectangle([zx, 157, zx + 17, 159], fill=(170, 60, 70, 255))
    d.rectangle([zx, 157, zx + 17, 157], fill=(206, 96, 100, 255))
    stages["canteen"] = dict(floor=160, layers=[
        dict(type="wrap", image=save(C.grade_rgba(raw[0], "day_in"), "canteen", "wall.png"), period=192, k=1.0, y=0),
        dict(type="rows", image=save(floor_, "canteen", "floor.png"), period=192, y=136, h=112, rows=[list(r) for r in rows]),
        dict(type="image", x=0, y=0, image=save(A.canteen_decor(), "canteen", "decor.png")),
        dict(type="steam", x=281, y=106, n=6, seed=1, h=6),
        dict(type="image", x=0, y=0, image=save(beams, "canteen", "beams_zabuton.png")),
        dict(type="dust", beams=[60, 250, 420, 560])])
    # ---- 中庭（巨大的诚字旗，固定镜头）
    ws = A.wall_strip()
    stages["courtyard"] = dict(floor=160, layers=[sky("courtyard", 150), clouds("courtyard", 6, 6, 0, 60)] + skyline("courtyard", 40, 4) + [
        dict(type="rays", x=200, y=60, n=14, speed=0.12, len=500, width=0.7, alpha=[0.08, 0.16], color=[255, 250, 230]),
        dict(type="image", x=0, y=0, image=save(matte(lambda im: (im.paste(ws, (0, 124), ws), C.dirt_ground(im, 158, 0, "day", grass=0.3))),
                                                "courtyard", "wall_ground.png")),
        flag("courtyard", 66, 142, 88, w=98, h=52, size=40, amp=3.0, pole_h=76, face="brush", speed=8.0, k=0.16)],
        fg=[dict(type="sakura", n=14, seed=8, wind=60, fall=10, alpha=1)])

    # ---- 小道具（JS：drawImage(img, x + ox, y + oy)）
    def grab(fn, name, anchor=(192, 120)):
        cv = matte(lambda im: fn(im, *anchor))
        spr, x, y = crop(cv)
        return dict(image=save(spr, "ch4", name), ox=x - anchor[0], oy=y - anchor[1], w=spr.width, h=spr.height)
    sp = dict(note=grab(lambda im, x, y: A.note(im, x, y), "note.png"), vein=grab(lambda im, x, y: A.vein(im, x, y, 1), "vein.png"),
              bump=grab(lambda im, x, y: A.bump(im, x, y), "bump.png"), sweat=grab(lambda im, x, y: sweat_drop(im, x, y), "sweat.png"),
              tea_cup=grab(lambda im, x, y: A.tea_cup(im, x, y), "tea_cup.png"),
              table=grab(lambda im, x, y: A.table_fg(im, 0, 0), "table.png", anchor=(0, 0)),
              pile_clean=grab(lambda im, x, y: A.mayo_pile(im, x, y, 14, 22, 4), "pile_clean.png"),
              pile_charred=[grab(lambda im, x, y, k=k: A.mayo_pile(im, x, y, 14, 22, 4, charred=True, t=k / 12), f"pile_charred{k}.png") for k in range(15)],
              big_bowl=grab(lambda im, x, y: A.big_bowl(im, x, y), "big_bowl.png", anchor=(192, 164)),
              pile_reveal=[grab(lambda im, x, y, k=k: A.mayo_pile(im, x, y, 106, 98, 11, reveal=max(0.02, k / 23)), f"pile_reveal{k}.png",
                                anchor=(192, 161)) for k in range(24)],
              bottle=[grab(lambda im, x, y, sq=sq, k=k: A.big_bottle(im, x, y, k / 6 + 1e-3, squeeze=sq), f"bottle_{int(sq)}{k}.png", anchor=(192, 118))
                      for sq, k in ((True, 0), (True, 1), (False, 0))],
              banner=dict(image=save(S._banner(), "ch4", "banner.png"), cx=192, cy=198),
              title=dict(image=save(S._title(), "ch4", "title.png"), cx=192, cy=177))
    for ch in (False, True):
        sp[f"small_bowl_{int(ch)}"] = grab(lambda im, x, y, ch=ch: A.small_bowl(im, x, y, 16, charred=ch), f"small_bowl_{int(ch)}.png")
    for f in (0, 1):
        b = _bush(f)
        sp[f"bush{f}"] = dict(image=save(b, "ch4", f"bush{f}.png"), ox=-13, oy=-19, w=b.width, h=b.height)
        sp[f"rocket{f}"] = grab(lambda im, x, y, f=f: A.rocket(im, x, y, f / 15 + 1e-3, facing=-1), f"rocket{f}.png")
        sp[f"crow{f}"] = grab(lambda im, x, y, f=f: A.crow(im, x, y, f / 8 + 1e-3, s=3), f"crow{f}.png")
    stages["ch4"] = sp


# ============================================================== 第六章：日常（原片 s06：六个漫画格小短篇）
CHAPTERS["ch6"] = ("第六章", "日常")
NAME_CARDS["hasegawa"] = ("长谷川泰三", "MADAO（彻底没用的大叔）", "HASEGAWA")
NAME_CARDS["otsu"] = ("寺门通", "超人气偶像｜新八是亲卫队队长", "OTSU")
SFX.update({
    "来了!!": dict(size=20, angle=10),
    "唰!": dict(size=20, angle=12),
    "闪!": dict(color=(255, 240, 120), size=16, angle=-12),
    "啪!": dict(size=24, angle=-10),
    "嘣!": dict(color=(255, 255, 255), size=22, angle=10),
    "嚼嚼": dict(color=(255, 255, 255), size=16, angle=-6),
    "ゴ": dict(color=(170, 110, 210), outline=(40, 16, 50), size=16, angle=-8),
    "咚!!": dict(size=22, angle=-12),
    "L": dict(color=(240, 70, 150), outline=(255, 255, 255), size=20, angle=-8),
    "O": dict(color=(240, 70, 150), outline=(255, 255, 255), size=20, angle=6),
    "V": dict(color=(240, 70, 150), outline=(255, 255, 255), size=20, angle=-6),
    "E": dict(color=(240, 70, 150), outline=(255, 255, 255), size=20, angle=8),
})


def ch6(stages, c):
    from bg import common as C, yorozuya as Y
    from PIL import ImageDraw
    import scenes._s06_art as A
    import scenes.s06_daily as S6
    out, rel, W, H = c["out"], c["rel"], c["W"], c["H"]

    def save(im, *p):
        path = out("bg", "daily", *p)
        im.save(path)
        return rel(path)

    def loop(name, n, fps, draw, box):
        """Bake a periodic animation as n RGBA frames: draw(canvas, t) on transparent, crop to box."""
        fr = []
        for k in range(n):
            cv = Image.new("RGBA", (W, H))
            draw(cv, k / fps + 1e-4)
            fr.append(save(cv.crop(box), f"{name}{k}.png"))
        return dict(type="frames", frames=fr, fps=fps, x=box[0], y=box[1])

    sp = {"paper": save(A.paper_layer(), "paper.png"), "caption_daily": save(S6._caption_sprite(), "cap_daily.png")}
    for i, tg in enumerate(("其一 MADAO", "其二 小钢珠", "其三 周一", "其四 偶像", "其五 醋昆布", "其六 跟踪狂")):
        cv = Image.new("RGBA", (120, 20))
        A.tag(cv, 0, 0, tg)
        sp[f"tag{i + 1}"] = save(cv.crop(cv.getbbox()), f"tag{i + 1}.png")      # paste at page (10, 10)
    dummy = Image.new("RGB", (W, H))

    # ---- V1 riverbank (dusk). Procedural extras (reeds, river shimmer, leaves) are driven by data in the brief.
    sky = Image.new("RGB", (W, H))
    C.sky(sky, "dusk", 0.0, horizon=112, body=False, stars=False)
    A.sunset_sun(dummy, 150, 116, 24)
    A.far_bank(dummy, 113, col=(150, 84, 96))
    A.sunset_river(dummy, 113, 32, 0.0, 150)
    A.river_bank(dummy, 0.0, 144)
    stages["daily_v1"] = dict(layers=[
        dict(type="static", image=save(sky, "v1_sky.png")),
        c["export_clouds"]("daily/v1", "dusk", seed=6, count=6, y0=8, y1=70, cam_mul=0.0),
        dict(type="image", image=save(A._CACHE[("sun", 24)], "v1_sun.png"), x=116, y=82),
        dict(type="image", image=save(A._CACHE[("farbank", (150, 84, 96))], "v1_farbank.png"), x=0, y=73),
        dict(type="image", image=save(A._CACHE[("sriver", 32)], "v1_river.png"), x=0, y=113),
        dict(type="image", image=save(A._CACHE[("bank", 144)], "v1_bank.png"), x=0, y=0)],
        hasegawa=[214, 150], crow_perch=[230, 132])

    # ---- V2 pachinko parlor
    A.parlor_bg(dummy, 0.0)
    m = A.machine_sprite()

    def lamp(cv, t):                                   # siren + frame bulbs of the big machine (lit, lamp on)
        A.draw_machine(cv, 192, 150, t, reels=(), lit=True, balls=False, tray=0.0, lamp=1.0)
    stages["daily_v2"] = dict(layers=[
        dict(type="static", image=save(A._CACHE["parlor"], "v2_parlor.png")),
        loop("v2_parlor_lights", 20, 8, lambda cv, t: A.parlor_bg(cv, t, lit=True), (0, 92, W, 104)),
        dict(type="image", image=save(m, "v2_machine.png"), x=192 - 23, y=150 - m.height),
        loop("v2_machine_lamp", 6, 12, lamp, (167, 60, 217, 79))],
        machine=[192, 150], stools=[[158, 141, 150], [227, 141, 150]], seat_y=143)
    cv = Image.new("RGBA", (16, 14))
    A.stool(cv, 8, 2, 12)
    sp["stool"] = save(cv, "stool.png")                # paste at (x-8, top-2)
    for nm, col in (("red", None), ("blur", (90, 90, 120)), ("unlit", (120, 120, 120))):
        st = Image.new("RGBA", (34, 480))                 # reel strip: digit n centred at y = n*40 + 22 (0..9, then 0,1 again)
        for n in range(12):
            ch = "0123456789"[n % 10]
            spr = A._big_digit(ch, col or ((228, 40, 60) if ch == "7" else (60, 90, 200)))
            st.alpha_composite(spr, (17 - spr.width // 2, n * 40 + 22 - spr.height // 2))
        sp[f"reel_{nm}"] = save(st, f"reel_{nm}.png")
    A.stamp(dummy, 86, 56, 5.5, 4.95, sub="")
    sp["stamp"] = save(A._CACHE[("stamp", "输光", "", (214, 36, 50))], "stamp.png")    # centre (86,56), rotated 12deg

    # ---- V3 calendar panel + shoujo panel
    A.wall_bg(dummy)
    A.shoujo_bg(dummy, 0.0, S6.V3_JX, S6.V3_JY)
    A.jump_mag(dummy, 100, 100, 0.0)
    for nm, t in (("calendar_sun", 6.0), ("calendar_mon", 7.5)):
        cv = Image.new("RGBA", (W, H))
        A.calendar(cv, 192, 58, t, S6.T_TEAR)
        sp[nm] = dict(image=save(cv.crop(cv.getbbox()), nm + ".png"), x=cv.getbbox()[0], y=cv.getbbox()[1])
    sp.update(cal_page_sun=save(A.cal_page("sun"), "cal_page_sun.png"), jump=save(A._CACHE["jumpmag"], "jump.png"),
              star_eye_patch=save(S6._sparkle_head().crop((3, 11, 16, 16)), "star_eye_patch.png"))
    stages["daily_v3_cal"] = dict(layers=[dict(type="static", image=save(A._CACHE[("wall", (230, 214, 182))], "v3_wall.png"))])
    stages["daily_v3_gin"] = dict(layers=[dict(type="static", image=save(A._CACHE["shoujo"], "v3_shoujo.png"))],
                                  jump=[S6.V3_JX, S6.V3_JY], gintoki=[S6.V3_GX, S6.V3_GY])

    # ---- V4 concert stage: base + three exact light loops (bulbs 4 f @10, truss lamps 8 f @10, footlights 9 f @10)
    A.stage_bg(dummy, 0.0)
    base = A._CACHE["stage"]

    def lights(which):
        def draw(cv, t):
            full = Image.new("RGB", (W, H))
            A.stage_bg(full, t)
            diff = Image.new("RGBA", (W, H))
            fa, ba = full.load(), base.load()
            boxes = {"bulbs": [(43, 29, 342, 31), (43, 32, 44, 118), (341, 32, 342, 118)],
                     "truss": [(41, 56, 352, 61)], "foot": [(40, 124, 354, 127)]}[which]
            for (x0, y0, x1, y1) in boxes:
                for y in range(y0, y1):
                    for x in range(x0, x1):
                        diff.putpixel((x, y), fa[x, y] + (255,))
            cv.alpha_composite(diff)
        return draw
    stages["daily_v4"] = dict(layers=[
        dict(type="static", image=save(base, "v4_stage.png")),
        loop("v4_bulbs", 4, 10, lights("bulbs"), (43, 29, 342, 118)),
        loop("v4_truss", 8, 10, lights("truss"), (41, 56, 352, 61)),
        loop("v4_foot", 9, 10, lights("foot"), (40, 124, 354, 127))],
        otsu=[S6.V4_OX, A.STAGE_Y], shinpachi=[S6.V4_SX, S6.V4_SY])
    for i, col in enumerate(S6._NOTE_COLS):
        for dbl in (False, True):
            A.note(dummy, 0, 0, col, dbl)
            sp[f"note{i}{'d' if dbl else 's'}"] = save(A._CACHE[("note", col, dbl)], f"note{i}{'d' if dbl else 's'}.png")

    # ---- V5 Yorozuya office at DUSK: static (+ lamp glow, closed door, hour hand, low table: the scene draws
    #      Sadaharu/Kagura AFTER Y.office(), so the table is part of the base here) + TV flicker loop + minute hand
    from PIL import ImageDraw
    st = C.cached(("yz_static", "dusk"), lambda: Y._static("dusk")).copy()
    C.add_sprite(st, Y._lamp_glow("dusk"), Y.LAMP_X - 90, 32 - 90)
    tbl, (tx, ty) = C.cached(("yz_table", "dusk"), lambda: Y._table_sprite("dusk"))
    door = C.cached(("yz_door", "dusk"), lambda: Y._door_panel("dusk"))
    st.paste(door, (Y.DOOR_BOX[0], Y.DOOR_BOX[1]), door)
    ImageDraw.Draw(st).line([(127, 59), (130, 57)], fill=(30, 30, 30))
    st.paste(tbl, (tx, ty), tbl)
    x0, y0, tw, th = Y.TV_BOX

    def tv(cv, t):
        full = Image.new("RGB", (W, H))
        Y.office(full, t, "dusk")
        cv.paste(full.crop((x0, y0, x0 + tw + 1, y0 + th + 1)), (x0, y0))     # flicker blocks spill 1 px right/down
    stages["daily_v5"] = dict(layers=[
        dict(type="static", image=save(st, "v5_office.png")),
        loop("v5_tv", 12, 6, tv, (x0, y0, x0 + tw + 1, y0 + th + 1)),
        dict(type="clock", x=127, y=59, len=5, color=[200, 40, 40], ink=[30, 30, 30])],
        sadaharu=[S6.V5_DX, S6.V5_DY], kagura_x=S6.V5_KX, kagura_y=[S6.V5_KY_SLEEP, S6.V5_KY_STAND])

    # ---- V6 Otae's room (top) + crawlspace (bottom)
    room = Image.new("RGB", (W, H))
    C.room_wall(room, 0, C.indoor("day"), 0, 136, "fusuma")
    C.tatami(room, 136, 0, C.indoor("day"))
    gaps = (S6.STAB_BX - 1, S6.STAB_BX + 44, S6.STAB_BX - 70, S6.STAB_BX + 96)
    A.crawlspace(dummy, 0.0, gaps)
    stages["daily_v6_room"] = dict(layers=[dict(type="static", image=save(room, "v6_room.png")),
                                           loop("v6_teacup", 6, 6, lambda cv, t: A.teacup(cv, 184, 146, t), (178, 133, 190, 147))],
                                   floor_overlay=dict(image=save(room.crop((0, 147, W, H)), "v6_floor.png"), x=0, y=147),
                                   otae=[S6.V6_OX, S6.V6_OY])
    stages["daily_v6_crawl"] = dict(layers=[dict(type="static", image=save(A._CACHE["crawl"], "v6_crawl.png"))],
                                    gap_xs=list(gaps), kondo=[S6.V6_KX, S6.V6_KY], joist_y=A.JOIST_Y, dirt_y=A.DIRT_Y)
    for f in range(4):
        for caw in (False, True):
            cv = Image.new("RGBA", (40, 34))
            A.crow_big(cv, 22, 17, f / 8 + 1e-4, caw=caw)
            sp[f"crow_big{f}{'c' if caw else ''}"] = save(cv, f"crow_big{f}{'c' if caw else ''}.png")   # centre (22,17)
    stages["daily_props"] = sp


# ============================================================== 第七章：红樱篇（原片 s07）
CHAPTERS["ch7"] = ("第七章", "红樱篇")
NAME_CARDS["okada_nizo"] = ("冈田似藏", "人斩｜妖刀红樱", "NIZO", "left")
NAME_CARDS["takasugi"] = ("高杉晋助", "鬼兵队总督｜最危险的男人", "TAKASUGI", "left")
SFX.update({
    "铿!!": dict(color=(255, 240, 200), size=28, angle=-10),
    "锵!": dict(color=(255, 240, 200), size=20, angle=-12),
    "铿!": dict(color=(255, 240, 200), size=20, angle=10),
    "是桂!!": dict(color=(255, 255, 255), outline=(190, 20, 40), size=32, angle=-10),
    "抠抠": dict(color=(200, 200, 214), outline=(40, 36, 60), size=16, angle=6),
    "杀啊——!!": dict(color=(150, 230, 170), outline=(20, 40, 30), size=20),
    "唰!!": dict(color=(255, 255, 255), size=28, angle=-6),
})


def _night_kit(c):
    """夜景用的几样导出：天空渐变、星表、云、河面、月亮（s07 / s08 的调研里测过和原片一致）。"""
    import numpy as np
    from bg import common as C
    from engine.core import rng
    from engine.gfx import mix
    save = _tools(c)[0]
    W, H = c["W"], c["H"]

    def grade_fn(mul, add):
        def g(x):
            if isinstance(x, tuple):
                return tuple(int(v) for v in np.clip(np.array(x[:3], np.float32) * mul + add, 0, 255))
            a = np.asarray(x).astype(np.float32)
            a[..., :3] = np.clip(a[..., :3] * np.array(mul, np.float32) + np.array(add, np.float32), 0, 255)
            return Image.fromarray(a.astype(np.uint8), x.mode)
        return g

    def sky(tod, horizon):
        im = Image.new("RGB", (W, H))
        C.sky(im, tod, 0.0, horizon=horizon, body=False, stars=False)
        return im

    def stars(tod, horizon):
        n = {"night": 80, "dusk": 18, "dawn": 14}[tod]
        ymax = {"night": int(horizon * 0.8), "dusk": 40, "dawn": 36}[tod]
        lst = C.cached(("stars", tod, ymax), lambda: C._star_list(7, n, ymax))
        return dict(type="stars", dim=1.0 if tod == "night" else 0.55, skip=list(C.tod_info(tod)["sun"]),
                    items=[[x, y, round(sp, 6), round(ph, 6), bool(big), list(cc)] for (x, y, sp, ph, big, cc) in lst])

    def clouds(folder, tod, seed, count, y0, y1, speed=1.0, tscale=1.0, grade=None):
        span, lst = W + 200, []
        for i in range(count):
            r = rng("cloud", seed, i)
            depth = r.uniform(0.25, 1.0)
            w = int(26 + 50 * depth * r.uniform(0.7, 1.2))
            h = int(max(7, w * r.uniform(0.22, 0.32)))
            fade = (1 - depth) * 0.45
            spr = C.cached(("cloud", seed, i, tod, w, h), lambda: C._cloud_sprite(seed, i, tod, w, h, fade))
            if grade:
                spr = grade(spr)
            y = int(y0 + (y1 - y0) * (1 - depth) * r.uniform(0.5, 1.0) + r.uniform(0, (y1 - y0) * 0.4))
            k = 0.04 + 0.16 * depth
            x0 = r.uniform(0, span)
            lst.append(dict(image=save(spr, folder, f"cloud{i}.png"), x0=round(x0, 4), y=y,
                            vx=round((2.0 + 5.0 * depth) * speed * tscale, 5), k=round(k, 5)))
        return dict(type="clouds", span=span, clouds=lst)

    def river(folder, y, h, tod, reflect_x=None, grade=None):
        g = grade or (lambda v: v)
        base = C.cached(("river", h, tod), lambda: C._river_base(h, tod))
        hi = (150, 160, 210) if tod == "night" else C.grade_color((210, 234, 246), tod)
        lo = C.grade_color((30, 56, 86), tod)
        mid = mix(hi, lo, 0.5)
        dashes = C.cached(("rivdash", h), lambda: C._river_dashes(h))
        return dict(type="river", image=save(g(base), folder, "river_base.png"), y=y, h=h, hi=list(g(tuple(hi))),
                    mid=list(g(tuple(mid))), lo=list(g(tuple(lo))), rc=list(g((236, 232, 200))), reflect_x=reflect_x,
                    dashes=[[a, b, round(cc, 6), round(d, 6), round(e, 6), round(f, 6), round(q, 6)] for (a, b, cc, d, e, f, q) in dashes])

    def moon(folder, name, x, y, r, tint=None):
        spr = C.cached(("moon", int(r), tint), lambda: C._moon_sprite(int(r), tint))
        return dict(type="image", image=save(spr, folder, name), x=int(x) - spr.width // 2, y=int(y) - spr.height // 2, k=0.0)
    return grade_fn, sky, stars, clouds, river, moon


def ch7(stages, c):
    from bg import common as C, edo as E
    from bg._draw import graded_layer
    from engine.gfx import mix, rotate_nearest
    from scenes import _s07_art as A, s07_benizakura as S
    save, crop, grab, grab_add, sprite = _tools(c)
    grade_fn, sky, stars, clouds, river, moon = _night_kit(c)
    W, H = c["W"], c["H"]
    tod = "night"
    # ---- 月夜的桥（B1）：桥面脚点 y 152，拱高 9 px
    br = C.cached(("bridge", tod, "wood"), lambda: C._bridge_sprite(tod, "wood"))
    stages["bridge_night"] = dict(layers=[
        dict(type="static", image=save(sky(tod, 150), "bridge_night", "sky.png")), stars(tod, 150),
        moon("bridge_night", "moon.png", *S.MOON_B), clouds("bridge_night", tod, 5, 5, 26, 72),
        river("bridge_night", 150, 66, tod, reflect_x=S.MOON_B[0]),
        dict(type="image", image=save(br, "bridge_night", "bridge.png"), x=int(W / 2 - C.BRIDGE_SPAN / 2), y=S.FLOOR_BR - C._BR_TOP, k=1.0)])
    # ---- 雷雨中的桥（D）：整体偏冷的调色 + 闪电 + 雨
    g = grade_fn((0.8, 0.86, 1.0), (2, 4, 10))
    far, near = C.cached(("mtn", tod), lambda: C._mountain_layers(tod))
    top = 150 + 40 - far.height
    bolts = []
    for i, (x, y1) in enumerate(((96, 140), (196, 104))):
        cv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        A.bolt(cv, i, x=x, y1=y1)
        spr, bx, by = crop(cv)
        bolts.append(dict(image=save(spr, "bridge_storm", f"bolt{i}.png"), x=bx, y=by))
    stages["bridge_storm"] = dict(layers=[
        dict(type="static", image=save(g(sky(tod, 150)), "bridge_storm", "sky.png")),
        clouds("bridge_storm", tod, 4, 9, 0, 56, speed=5.0, grade=g),
        dict(type="wrap", image=save(g(far), "bridge_storm", "mtn_far.png"), period=768, k=0.05, y=top),
        dict(type="wrap", image=save(g(near), "bridge_storm", "mtn_near.png"), period=768, k=0.12, y=top),
        river("bridge_storm", 150, 66, tod, grade=g),
        dict(type="image", image=save(g(br), "bridge_storm", "bridge.png"), x=-68, y=132, k=1.0)],
        fg=[dict(type="rain", n=110, slant=0.25, len=9, speed=520, ground=[150, 168], splashes=20, color="rgba(180,196,232,0.55)", alpha=1)],
        bolts=bolts)
    # ---- 红月下的江户屋顶（C）：屋脊脚点 y 160
    dy = 38
    mtop = 138 + dy + 40 - far.height
    term = C.cached(("terminal", tod), lambda: E._terminal_layer(tod))
    farc = graded_layer(("edo_far",), E._far_city, tod, depth=0.5, glow_radius=2, glow_strength=0.3)
    cas = graded_layer(("edo_castle",), E._castle_layer, tod, depth=0.32)
    mid_ = graded_layer(("edo_mid",), E._mid_city, tod, depth=0.18, glow_radius=3, glow_strength=0.45)
    walk = graded_layer(("roofwalk",), E._walk_layer, tod, depth=0.0, glow_radius=3, glow_strength=0.5)
    stages["roofs_red"] = dict(layers=[
        dict(type="static", image=save(sky(tod, 150), "roofs_red", "sky.png")), stars(tod, 150),
        moon("roofs_red", "moon_red.png", 214, 94, 54, tint=(255, 150, 140)), clouds("roofs_red", tod, 9, 5, 10, 60, speed=2.0),
        dict(type="wrap", image=save(far, "roofs_red", "mtn_far.png"), period=768, k=0.05, y=mtop),
        dict(type="wrap", image=save(near, "roofs_red", "mtn_near.png"), period=768, k=0.12, y=mtop),
        dict(type="terminal", image=save(term, "roofs_red", "terminal.png"), w=term.width, h=term.height, k=0.1, dy=dy, side_px=True),
        dict(type="wrap", image=save(farc, "roofs_red", "far_city.png"), period=896, k=0.25, y=dy),
        dict(type="wrap", image=save(cas, "roofs_red", "castle.png"), period=1536, k=0.4, y=dy),
        dict(type="wrap", image=save(mid_, "roofs_red", "mid_city.png"), period=1024, k=0.6, y=dy),
        dict(type="wrap", image=save(walk, "roofs_red", "roof_walk.png"), period=512, k=1.0, y=160 - 30)])
    # ---- 满月和鬼兵队的船（E1）：船在剧情里画
    stages["ship_moon"] = dict(layers=[
        dict(type="static", image=save(sky(tod, 170), "ship_moon", "sky.png")), stars(tod, 170),
        moon("ship_moon", "moon.png", 192, 100, 58), clouds("ship_moon", tod, 21, 6, 40, 150, tscale=2.5)])
    sp = {}
    for kind, hz, fc in (("pirate", 0.5, -1), ("cruiser", 0.6, 1), ("kiheitai", 0.0, -1)):
        sp["ship_" + kind] = sprite(E._ship_sprite(kind, 1, fc, tod, hz), "ch7", f"ship_{kind}.png")
    # ---- 船舷（E2：高杉坐在船舷上抽烟，背后是满月）
    rail = A.cached(("rail",), A._rail_strip)
    hull = A.cached(("hull",), A._hull_strip)
    y_rail = S.TAKA_E[1] - 14
    stages["ship_side"] = dict(layers=[
        dict(type="static", image=save(sky(tod, 170), "ship_side", "sky.png")), stars(tod, 170),
        moon("ship_side", "moon.png", 250, 92, 58), clouds("ship_side", tod, 21, 6, 40, 150),
        dict(type="wrap", image=save(rail.crop((6, 0, rail.width, rail.height)), "ship_side", "rail.png"), period=6, k=1.0, y=y_rail - 1),
        dict(type="wrap", image=save(hull.crop((24, 0, hull.width, hull.height)), "ship_side", "hull.png"), period=48, k=1.0, y=S.TAKA_E[1])],
        seat=list(S.TAKA_E))

    # ---- 鬼兵队的甲板（F：主甲板 / G：高杉站在上层甲板）
    def deck_front(mast_x=230, right=True, upper=False):
        from engine.gfx import rect
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        A.far_city(lay, 0, 140, "night")
        A.rigging(lay, mast_x, -10, 128, 132, right=right)
        mast = A.cached(("mast",), A._mast_sprite)
        lay.paste(mast, (int(mast_x) - 45, -10), mast)
        A.long_rail(lay, 131, 0)
        rect(lay, 0, 146, W, 6, (44, 30, 36))
        rect(lay, 0, 146, W, 1, (70, 50, 52))
        C.wood_floor(lay, 152, 0, "night")
        lans = []
        for side, ex in (((-1, -20), (1, W + 20)) if right else ((-1, -20),)):
            pts = [(mast_x + (ex - mast_x) * i / 8, 26 - 6 * i / 8 + math.sin(i / 8 * math.pi) * 18) for i in range(9)]
            ImageDraw.Draw(lay).line(pts, fill=(34, 26, 32))
            lans += [(mast_x + (ex - mast_x) * u, 26 - 6 * u + math.sin(u * math.pi) * 18, C.RED if side < 0 else C.YELLOW, 1.6)
                     for u in (0.3, 0.6, 0.88)]
        if upper:
            orig = C.lantern
            try:
                C.lantern = lambda *a, **k: None
                A.upper_deck(lay, 236, S.TAKA_G[1], 0.0, 0)
            finally:
                C.lantern = orig
            lans += [(248, S.TAKA_G[1] + 6, C.RED, 1.0), (316, S.TAKA_G[1] + 6, C.RED, 1.0)]
        return lay, lans
    for key, mn, mast_x, right, upper in (("deck_f", (300, 46, 22), 230, True, False), ("deck_g", (300, 72, 38), 150, False, True)):
        front, lans = deck_front(mast_x, right, upper)
        layers = [dict(type="static", image=save(sky(tod, 150), key, "sky.png")), stars(tod, 150), moon(key, "moon.png", *mn),
                  clouds(key, tod, 11, 6, 10, 70, speed=2.5), dict(type="static", image=save(front, key, "front.png"))]
        for x, y, col, swing in lans:
            nm = "red" if col == C.RED else "yellow"
            spr = C._lantern_sprite(col, 1, True, None)
            glow = C.glow_sprite(14, mix(col, (255, 200, 120), 0.55), 1.0)
            layers.append(dict(type="lantern", x=round(x), y=round(y), string=4, amp=swing * 1.4, freq=0.32, color=[40, 30, 34],
                               image=save(spr, key, f"lantern_{nm}.png"), w=spr.width, h=spr.height,
                               glow=dict(image=save(glow, key, f"lantern_glow_{nm}.png"), rad=14)))
        stages[key] = dict(layers=layers, floor=160, upper_top=S.TAKA_G[1] if upper else None)
    # ---- 小道具：断发（转好的几张）、蝴蝶、青筋
    base = A._hair_lock()
    sp["hair"] = {str(k * 6): save(rotate_nearest(base, k * 6), "ch7", f"hair_{k * 6}.png") for k in list(range(-6, 6)) + [14]}
    bf = []
    for i in range(3):
        cv = Image.new("RGBA", (5, 4), (0, 0, 0, 0))
        A.butterfly(cv, 2, 2, (i + 0.01) / 8)
        bf.append(save(cv, "ch7", f"butterfly{i}.png"))
    sp["butterfly"] = dict(frames=bf, fps=8)
    sp["vein"] = save(A.cached(("vein",), A._vein_sprite), "ch7", "vein.png")
    stages["ch7"] = sp


# ============================================================== 第八章：真选组动乱篇（原片 s08）
CHAPTERS["ch8"] = ("第八章", "真选组动乱篇")
NAME_CARDS["toshi"] = ("托西", "妖刀村麻纱附身的副长｜宅男", "TOSHI")
NAME_CARDS["ito"] = ("伊东鸭太郎", "真选组参谋｜野心家", "ITO")
SFX.update({
    "斩!!": dict(color=(255, 255, 255), outline=(20, 40, 90), size=30, angle=-6),
    "斩!": dict(color=(255, 255, 255), outline=(20, 40, 90), size=24, angle=8),
    "吱——!!": dict(color=(255, 255, 255), outline=(40, 20, 40), size=16, angle=-8),
    "哒哒哒!": dict(color=(255, 230, 90), size=16, angle=8),
    "噗!": dict(color=(255, 200, 240), size=22, angle=-6),
})


def ch8(stages, c):
    from bg import common as C
    from chars import render_sprite
    from engine.core import rng
    from engine.gfx import rect
    from scenes import _s08_kit as K, s08_mayo_crisis as S
    save, crop, grab, grab_add, sprite = _tools(c)
    grade_fn, sky, stars, clouds, river, moon = _night_kit(c)
    W, H = c["W"], c["H"]

    def andon(folder, x, y, strength):           # 纸灯笼：闪动的暖光（相加）+ 灯笼本体
        full = C.glow_sprite(26, (120, 80, 30), 1.0)
        body = Image.new("RGBA", (13, 26), (0, 0, 0, 0))
        add = C.add_sprite
        C.add_sprite = lambda *a, **k: None
        try:
            K.andon(body, 6, 26, 0.0)
        finally:
            C.add_sprite = add
        return [dict(type="glow", image=save(full, folder, "andon_glow.png"), x=int(x) - 26, y=int(y) - 16 - 26, alpha=strength, flicker=True),
                dict(type="image", image=save(body, folder, "andon.png"), x=int(x) - 6, y=int(y) - 26)]
    # ---- 屯所的房间（夜）：隔扇、榻榻米、「诚」字挂轴、纸灯笼
    base = Image.new("RGB", (W, H))
    C.room_wall(base, 0, "night_in", 0, 136, "fusuma")
    C.tatami(base, 136, 0, "night_in")
    K.makoto_scroll(base, 150, 50, 0.0)
    stages["hq_room"] = dict(layers=[dict(type="static", image=save(base, "hq_room", "base.png"))] + andon("hq_room", 272, 160, 1.0))
    # ---- 伊东的房间：圆窗、月光、光柱里的灰尘
    motes = []
    for i in range(18):
        r = rng("mdust", i)
        motes.append([round(r.uniform(0.05, 0.12), 6), round(r.random(), 6), round(r.uniform(-20, 20), 6)])
    stages["ito_room"] = dict(layers=[dict(type="static", image=save(K.ito_room_bg(), "ito_room", "base.png"))] + andon("ito_room", 34, 160, 0.8)
                              + [dict(type="shaftmotes", items=motes)])

    # ---- 黄昏、飞驰中的背景（按时间往后跑）：天空 + 星星 + 云 + 远山
    def backdrop(f, horizon, mt_y, mt_speed):
        tod = "dusk"
        sk = Image.new("RGB", (W, H))
        C.sky(sk, tod, 0.0, horizon=horizon, body=True, stars=False)
        far, near = C.cached(("mtn", tod), lambda: C._mountain_layers(tod))
        top = mt_y + 40 - far.height
        cl = clouds(f, tod, 0, 6, 6, 70)
        for cc in cl["clouds"]:                    # 原片 cam_x = 45·t：云也跟着往后跑
            cc["vx"] = round(cc["vx"] - cc["k"] * 45.0, 5)
        return [dict(type="static", image=save(sk, f, "sky.png")), stars(tod, horizon), cl,
                dict(type="wrap", image=save(far, f, "mtn_far.png"), period=768, k=0.0, vx=mt_speed * 0.05, y=top),
                dict(type="wrap", image=save(near, f, "mtn_near.png"), period=768, k=0.0, vx=mt_speed * 0.12, y=top)]
    # ---- 铁路边的公路（C2）：远处的列车 + 路堤 + 公路
    upper, lower = K.carriage_parts()
    strip = Image.new("RGBA", (750 + W, K.CAR_H), (0, 0, 0, 0))
    for i, s in enumerate((2, 3, 4, 2, 3)):
        cc = K.full_lit_carriage(s)
        strip.paste(cc, (i * 250, 0), cc)
    road = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    top = S.T2_TOP + K.CAR_H
    rect(road, 0, top + 4, W, S.ROAD_Y - (top + 4), (104, 78, 80))
    rect(road, 0, top + 3, W, 2, (170, 160, 170))
    rect(road, 0, S.ROAD_Y, W, H - S.ROAD_Y, (74, 64, 86))
    rect(road, 0, S.ROAD_Y, W, 2, (200, 190, 200))
    rect(road, 0, S.ROAD_Y + 2, W, 3, (56, 48, 66))
    r2 = rng("asph", 0)
    for i in range(40):
        rect(road, r2.randint(0, W), r2.randint(S.ROAD_Y + 6, H), r2.randint(6, 26), 1, (64, 56, 76))
    dash = Image.new("RGBA", (64 + W, 3), (0, 0, 0, 0))
    for k in range(0, 64 + W, 64):
        rect(dash, k, 0, 30, 3, (230, 224, 200))
    stages["road"] = dict(layers=backdrop("road", 126, 104, 500) + [
        dict(type="wrap", image=save(strip, "road", "far_train.png"), period=750, k=0.0, vx=36, y=S.T2_TOP),
        dict(type="static", image=save(road, "road", "road.png")),
        dict(type="wrap", image=save(dash, "road", "lane_dash.png"), period=64, k=0.0, vx=570, y=S.ROAD_Y + 30),
        dict(type="mlines", color=[250, 200, 170], count=8, seed=9, y0=10, y1=40, speed=1300, len=[20, 50])],
        train_roof_y=S.T2_TOP + K.ROOF_Y)
    # 警车（银时开车、新八和托西在后座、神乐在车顶上开枪）：一整张图，4 帧（轮子 + 警灯）
    car = K.police_car_sprite()
    MT = 64
    frames = []
    for k in range(4):
        t = k / 8 + 1e-6
        cv = Image.new("RGBA", (car.width + 24, car.height + MT), (0, 0, 0, 0))
        fy = MT + 43

        def put(cid, pose, x, y, **kw):
            spr, ax, ay = render_sprite(cid, pose, t, None, kw.pop("expr", None), 1, **kw)
            spr = spr.convert("RGBA")
            cv.alpha_composite(spr, (int(x - ax), int(y - ay)))
        put("shinpachi", "shout", 58, fy)
        put("toshi", "figure", 78, fy + 1)
        put("gintoki", "idle", 110, fy, expr="angry")
        cv.alpha_composite(car, (0, MT))
        add = C.add_sprite
        C.add_sprite = lambda *a, **kk: None
        try:
            body = Image.new("RGBA", cv.size, (0, 0, 0, 0))
            K.car_wheels(body, 0, MT, t * 1.5)
            K.siren_glow(body, 85, MT + 4, t)
        finally:
            C.add_sprite = add
        cv.alpha_composite(body)
        put("kagura", "umbrella_shoot", 64, MT + 8, weapon=26, arm_f=112)
        frames.append(save(cv, "ch8", f"police_car{k}.png"))
    sp = {"police_car": dict(frames=frames, fps=8, w=car.width + 24, h=car.height + MT, top=MT)}
    # ---- 列车车顶（D）：背景往后跑 + 车顶 + 速度线
    roof = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    S.roof_top(roof, 0.0)
    stages["train_roof"] = dict(layers=backdrop("train_roof", 170, 158, 700) + [
        dict(type="mlines", color=[255, 214, 190], count=16, seed=11, y0=20, y1=140, speed=1500, len=[20, 70]),
        dict(type="static", image=save(roof, "train_roof", "roof_top.png"))], floor=S.D_FLOOR)
    # ---- 夕阳的原野（E）：巨大的夕阳、冒烟的列车残骸、风里的光点
    from engine.gfx import circle
    per, n = 1 / 0.35, 40
    smoke = []
    for k in range(n):
        cv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        tt = k * per / n
        for kk in range(7):
            ph = ((tt * 0.35) + kk / 7) % 1.0
            for j, (sx, sy) in enumerate(((300, 108), (352, 110))):
                circle(cv, int(sx - ph * 30 + math.sin(ph * 6 + kk) * 3), int(sy - ph * 70), int(3 + ph * 9),
                       (70 - int(ph * 20), 30, 50) if j == 0 else (84, 36, 56))
        smoke.append(save(cv.crop((250, 20, 384, 125)), "sunset", f"smoke{k}.png"))
    wm = []
    for i in range(30):
        r = rng("mote", 3, i)
        wm.append([round(r.uniform(0.6, 1.4), 6), round(r.uniform(0, W), 6), round(r.uniform(0, 140), 6)])
    stages["sunset"] = dict(layers=[dict(type="static", image=save(K.sunset_bg(), "sunset", "base.png")),
                                    dict(type="frames", frames=smoke, fps=n / per, x=250, y=20),
                                    dict(type="windmotes", items=wm, speed=140, color=[255, 190, 120], area=[0, 30, W, 170])],
                            floor=S.E_FLOOR, sun=[K.SUN_X, K.SUN_Y, K.SUN_R])
    stages["ch8"] = sp


# ============================================================== 第九章：吉原炎上篇（原片 s09）
CHAPTERS["ch9"] = ("第九章", "吉原炎上篇")
NAME_CARDS["seita"] = ("晴太", "吉原长大的少年｜想见娘亲", "SEITA", "left")
NAME_CARDS["tsukuyo"] = ("月咏", "百华首领｜死神太夫", "TSUKUYO")
NAME_CARDS["hinowa"] = ("日轮", "吉原的太阳｜传说中的花魁", "HINOWA", "left")
NAME_CARDS["kamui"] = ("神威", "春雨第七师团团长｜神乐的哥哥", "KAMUI")
NAME_CARDS["housen"] = ("夜王凤仙", "吉原之主｜夜兔之王", "HOUSEN", "left")
SFX.update({
    "!!": dict(color=(255, 240, 120), size=24),
    "轰隆!!": dict(size=26, angle=-8),
    "嘿——!!": dict(color=(255, 255, 255), size=20, angle=6),
})


def ch9(stages, c):
    from bg import common as C
    from engine.core import rng, lerp
    from engine.gfx import INK, overlay_rect, shade
    from scenes import _s09_bg as B
    import scenes.s09_yoshiwara as S9
    save, crop, grab, grab_add, sprite = _tools(c)
    W, H = c["W"], c["H"]
    LANT = {C.RED: "red", C.PINK: "pink", C.YELLOW: "yellow"}
    # ---- 吉原大街（夜 / 天顶打开后的阳光）：游戏坐标 = 原片 x + 256，镜头 0..712
    for mode in ("night", "sun"):
        tod = "day" if mode == "sun" else "night"
        lit = mode != "sun"
        f = "yoshi_" + mode
        bd = Image.new("RGB", (W, H))
        bd.paste(B.backdrop(mode), (0, B.BACK_WY))
        old = B.CEIL_W
        B.CEIL_W = 768
        try:
            ceil = B.graded(("ceil_wide", 768), B._build_ceiling, mode, glow_radius=4, glow_strength=0.7).copy()
        finally:
            B.CEIL_W = old
        ceil.paste(B.ceiling_layer(mode), (0, 0))
        road, rows = C.cached(("stone", 64, tod), lambda: C._stone_strip(64, tod))
        wire = Image.new("RGBA", (300 + W, 12), (0, 0, 0, 0))
        dw = ImageDraw.Draw(wire)
        for x0 in (-4, 296, 596):
            dw.line([(x0 + i * 10, 2 + 8 * math.sin(math.pi * i * 10 / 300)) for i in range(31)], fill=((30, 24, 34) if lit else (70, 54, 50)) + (255,))
        L = [dict(type="static", image=save(bd, f, "backdrop.png")),
             dict(type="wrap", image=save(ceil.crop((0, 210, 768, 250)), f, "ceiling_band.png"), k=0.5, y=0, period=768 - W),
             dict(type="wrap", image=save(B.far_layer(mode).crop((101, 0, 760, 150)), f, "far.png"), k=0.35, y=10, period=659 - W),
             dict(type="wrap", image=save(B.mid_layer(mode).crop((4, 0, 1100, 124)), f, "mid.png"), k=1.0, y=32, period=1096 - W),
             dict(type="rows", image=save(road, f, "road.png"), period=192, y=152, h=64, rows=[list(r) for r in rows])]
        if lit:
            L.append(dict(type="image", image=save(B.cached(("spill",), B._build_spill), f, "spill.png"), x=0, y=152, screen=True, blend="lighter"))
        L.append(dict(type="wrap", image=save(wire, f, "wire.png"), k=1.0, y=56, period=300))
        imgs = {}
        for col, nm in LANT.items():
            imgs[nm] = dict(image=save(C._lantern_sprite(col, 1, lit, None), f, f"lantern_{nm}.png"))
            if lit:
                imgs[nm]["glow"] = save(C.glow_sprite(14, C.mix(col, (255, 200, 120), 0.55), 1.0), f, f"lantern_{nm}_glow.png")
        items = [dict(x=(296 + 22 * i) % 300, y=round(58 + 8 * math.sin(math.pi * i * 22 / 300), 3), **imgs[LANT[B._LANT_COLS[(i + 1) % 4]]])
                 for i in range(1, 13)]
        L.append(dict(type="lanternString", period=300, string=4, amp=1.4, freq=0.32, color=[40, 30, 34], glow=lit, items=items))
        stages[f] = dict(layers=L, floor=160)
    # ---- 日轮的塔（从街上往上看）
    top = Image.new("RGB", (W, H))
    B.street(top, 190, 0, tilt=117, mode="night", leaves_open=0.0, lanterns=False)
    tw = B.tower("night")
    ring = B.window_ring("night")
    stages["tower_night"] = dict(layers=[dict(type="static", image=save(top, "tower_night", "street_up.png")),
                                         dict(type="image", image=save(tw, "tower_night", "tower.png"), x=97, y=14)],
                                 window=[192, 84], ring=dict(image=save(ring, "tower_night", "ring.png"), x=192 - 25, y=84 - 25))
    # ---- 神威的屋顶（单屏）
    base = Image.new("RGB", (W, H))
    B.street(base, 120, 0, tilt=38, mode="night", lanterns=False)
    rfg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rfg.paste(B.roof_fg("night"), (-60, 150 - B.ROOF_RIDGE))
    stages["yoshi_roof"] = dict(layers=[dict(type="static", image=save(base, "yoshi_roof", "base.png")),
                                        dict(type="glow", image=save(C.glow_sprite(64, (255, 120, 70), 0.9), "yoshi_roof", "glow64.png"), x=35, y=16, alpha=1, k=0),
                                        dict(type="image", image=save(B.big_lantern("night"), "yoshi_roof", "big_lantern.png"), x=70, y=42, k=0),
                                        dict(type="static", image=save(rfg, "yoshi_roof", "roof_fg.png")),
                                        dict(type="glow", image=save(C.glow_sprite(90, (255, 110, 60), 0.6), "yoshi_roof", "glow90.png"), x=9, y=100, alpha=1, k=0)])
    # ---- 王座间（凤仙站着；两盏纸灯笼；整个房间可以暗下来）
    th = Image.new("RGB", (W, H))
    th.paste(B.graded(("throne",), B._build_throne, "night_in"), (0, 0))
    C.tatami(th, 150, 0, "night_in")
    lamp = Image.new("RGBA", (13, 29), (0, 0, 0, 0))
    d = ImageDraw.Draw(lamp)
    d.rectangle([0, 0, 12, 22], fill=INK); d.rectangle([1, 1, 11, 17], fill=(255, 226, 170)); d.line([(1, 9), (11, 9)], fill=(180, 120, 70))
    d.rectangle([0, 18, 12, 22], fill=(60, 40, 34)); d.line([(1, 22), (1, 28)], fill=INK); d.line([(11, 22), (11, 28)], fill=INK)
    lp = save(lamp, "throne", "andon.png")
    gl = save(C.glow_sprite(26, (255, 170, 90), 1.0), "throne", "andon_glow.png")
    stages["throne"] = dict(layers=[dict(type="static", image=save(th, "throne", "base.png"))]
                            + [dict(type="glow", image=gl, x=x - 26, y=110, alpha=1, flicker=True, k=0) for x in (64, 320)]
                            + [dict(type="image", image=lp, x=x - 6, y=128, k=0) for x in (64, 320)])
    # ---- 走廊（凤仙一拳把银时打穿三道隔扇）
    stages["corridor"] = dict(layers=[
        dict(type="wrap", image=save(B.graded(("corridor",), B._build_corridor, "night_in", glow_radius=3, glow_strength=0.5), "corridor", "wall.png"), k=1.0, y=0, period=1152),
        dict(type="image", image=save(C.cached(("wood", 64, "night_in"), lambda: C._wood_strip(64, "night_in"))[0], "corridor", "floor.png"), x=0, y=152, k=0)])
    sp = {}
    for nm, br, sd in (("intact", 0, 0), ("broken0", 1, 0), ("broken1", 1, 1), ("broken2", 1, 2)):
        cv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        B.partition(cv, 100, br, sd)
        sp["partition_" + nm] = save(cv.crop((87, 20, 114, 160)), "ch9", f"partition_{nm}.png")
    # ---- 控制室（解谜：齿轮和拉杆）
    cb = Image.new("RGB", (W, H), (26, 20, 32))
    cr = B.ceiling_layer("night_in").crop((20, 0, 20 + W, H))
    cb.paste(cr, (0, 0), cr)
    overlay_rect(cb, 0, 0, W, H, (20, 12, 24), 0.3)
    d = ImageDraw.Draw(cb)
    for y, col in ((30, (110, 84, 70)), (44, (96, 74, 64))):
        d.rectangle([0, y, W, y + 7], fill=col, outline=INK); d.line([(0, y + 1), (W, y + 1)], fill=shade(col, 1.4))
        for x in range(20, W, 90):
            d.rectangle([x, y - 2, x + 5, y + 9], fill=shade(col, 0.7), outline=INK)
    fl = Image.new("RGBA", (W, 56), (34, 30, 42, 255))
    d = ImageDraw.Draw(fl)
    for x in range(0, W, 6):
        d.line([(x, 1), (x, 56)], fill=(22, 20, 30))
    d.line([(0, 0), (W, 0)], fill=(80, 76, 96))
    stages["control"] = dict(layers=[dict(type="static", image=save(cb, "control", "back.png"))], floor_img=save(fl, "control", "floor.png"))
    sp["gear_big"] = sprite(B.gear(46, 12), "ch9", "gear_big.png")
    sp["gear_small"] = sprite(B.gear(30, 8), "ch9", "gear_small.png")
    sp["alarm_glow"] = save(C.glow_sprite(26, (255, 60, 40), 1.0), "ch9", "alarm_glow.png")
    for on in (True, False):
        s = Image.new("RGBA", (13, 14), (0, 0, 0, 0))
        d = ImageDraw.Draw(s)
        d.rectangle([0, 0, 12, 4], fill=(60, 60, 70), outline=INK)
        d.ellipse([2, 4, 10, 13], fill=(255, 90, 60) if on else (120, 40, 40), outline=INK)
        sp["alarm_" + ("on" if on else "off")] = save(s, "ch9", f"alarm_{'on' if on else 'off'}.png")
    lb = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lb)
    x, y = 190, 144
    d.rectangle([172, 140, 208, 160], fill=(70, 72, 88), outline=INK); d.line([(173, 141), (207, 141)], fill=(130, 134, 150))
    d.rectangle([176, 149, 204, 157], fill=(150, 120, 50))
    for i in range(-14, 6, 6):
        d.polygon([(x + i, 157), (x + i + 3, 157), (x + i + 6, 149), (x + i + 3, 149)], fill=(40, 34, 40))
    sp["lever_base"] = save(lb.crop((172, 140, 209, 161)), "ch9", "lever_base.png")
    arms = []
    for k, ang in enumerate(range(0, 68, 2)):
        cv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(cv)
        a = math.radians(ang)
        tx, ty = x + math.sin(a) * 30, y - math.cos(a) * 30
        d.line([(x, y), (tx, ty)], fill=INK, width=7); d.line([(x, y), (tx, ty)], fill=(170, 160, 150), width=4)
        d.ellipse([tx - 7, ty - 7, tx + 7, ty + 7], fill=B.LAC, outline=INK); d.ellipse([tx - 4, ty - 5, tx, ty - 1], fill=B.LAC_L)
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(200, 170, 80), outline=INK)
        arms.append(save(cv.crop((180, 106, 228, 152)), "ch9", f"lever{ang}.png"))
    sp["lever_arms"] = arms
    # ---- 天顶打开（往上看）
    sp["hatch_sky"] = save(B.cached(("hsky",), B._build_hatch_sky), "ch9", "hatch_sky.png")
    for mode in ("night", "sun"):
        sp[f"ceiling_{mode}"] = save(B.ceiling_layer(mode), "ch9", f"ceiling_{mode}.png")
        sp[f"leaf_left_{mode}"] = save(B.leaf(-1, mode), "ch9", f"leaf_left_{mode}.png")
        sp[f"leaf_right_{mode}"] = save(B.leaf(1, mode), "ch9", f"leaf_right_{mode}.png")
    # ---- 小道具：墙上的洞、碎石
    cv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    r = rng("s09hole")
    cx, cy = S9.HOLE
    pts = []
    for i in range(16):
        rr = r.uniform(0.8, 1.15)
        pts.append((cx + math.cos(i / 16 * 2 * math.pi) * 26 * rr, cy + math.sin(i / 16 * 2 * math.pi) * 22 * rr))
    d.polygon([(px + (2 if px > cx else -2), py + (2 if py > cy else -2)) for px, py in pts], fill=(24, 16, 20))
    d.polygon(pts, fill=(250, 196, 120))
    d.polygon([(cx + (px - cx) * 0.7, cy + (py - cy) * 0.7 + 3) for px, py in pts], fill=(255, 226, 170))
    for i in range(0, 16, 2):
        d.line([pts[i], (pts[i][0] + r.uniform(-5, 5), pts[i][1] + r.uniform(-5, 5))], fill=(120, 70, 50), width=2)
    bb = cv.getbbox()
    sp["hole"] = dict(image=save(cv.crop(bb), "ch9", "facade_hole.png"), ox=bb[0] - cx, oy=bb[1] - cy)
    cv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    S9.rubble(cv, 222, 162)
    bb = cv.getbbox()
    sp["rubble"] = dict(image=save(cv.crop(bb), "ch9", "rubble.png"), ox=bb[0] - 222, oy=bb[1] - 162)
    # ---- 特效参数：阳光柱、飘尘、火星
    sh = {}
    for nm, (ox, oy, n, seed, spr, al) in {"S9": (90, -150, 7, 1, (-0.05, 0.62), 0.30), "S10": (330, -140, 6, 2, (-0.6, 0.1), 0.36),
                                          "S11": (150, -150, 6, 3, (-0.05, 0.62), 0.26)}.items():
        r = rng("shaft", seed)
        sh[nm] = dict(ox=ox, oy=oy, alpha=al, shafts=[[lerp(spr[0], spr[1], (i + 0.5) / n) + r.uniform(-0.04, 0.04), r.uniform(0.018, 0.045)] for i in range(n)])
    sp["shafts"] = sh
    sp["embers"] = {nm: [[q.random(), q.uniform(0.6, 1.5), q.random(), q.random()] for q in (rng("ember", seed, i) for i in range(cnt))]
                    for nm, (seed, cnt) in {"S1": (1, 22), "S3": (3, 30), "S5": (5, 22)}.items()}
    stages["ch9"] = sp


# ============================================================== 第十章：将军暗杀篇（原片 s10）
CHAPTERS["ch10"] = ("第十章", "将军暗杀篇")
NAME_CARDS["shigeshige"] = ("德川茂茂", "第十四代将军｜老实人", "SHIGESHIGE")
NAME_CARDS["oboro"] = ("胧", "天照院奈落首领", "OBORO")
SFX.update({
    "咔嚓！": dict(color=(255, 255, 255), size=24, angle=-10),
    "啪！": dict(size=16, angle=12),
    "哧溜～": dict(color=(200, 220, 255), size=12, angle=-6),
    "锵！": dict(size=16, angle=10),
    "铿——！！": dict(color=(255, 255, 255), size=24, angle=8),
    "轰！": dict(size=16, angle=8),
    "咚！": dict(size=16, angle=-10),
    "砰！": dict(size=16, angle=10),
})


def ch10(stages, c):
    from bg import common as C
    from engine.core import rng
    import scenes.s10_shogun as S10
    save, crop, grab, grab_add, sprite = _tools(c)
    grade_fn, sky, stars, clouds, river, moon = _night_kit(c)
    W, H = c["W"], c["H"]
    tod = "dusk"
    # ---- 黄昏的山道（护送，往右一直走）
    sk = Image.new("RGB", (W, H))
    C.sky(sk, tod, 0.0, horizon=150, stars=False)
    cl = clouds("pass", tod, 4, 5, 8, 58)
    for cc in cl["clouds"]:
        cc["k"] = round(cc["k"] * 0.3, 5)
    far, near = C.cached(("mtn", tod), lambda: C._mountain_layers(tod))
    mid, crest = S10._cached("passmid", S10._pass_mid)
    ground, rows = C.cached(("dirt", 66, tod, 0.5), lambda: C._dirt_strip(66, tod, 0.5))
    lan = Image.new("RGBA", (24, 30), (0, 0, 0, 0))
    S10._stone_lantern(lan, 12, 27)
    post = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    S10._signpost(post, 15, 36)
    st = stars(tod, 150)
    stages["pass"] = dict(layers=[dict(type="static", image=save(sk, "pass", "sky.png")), st, cl,
        dict(type="wrap", image=save(far, "pass", "mtn_far.png"), k=0.05, period=768, y=30),
        dict(type="wrap", image=save(near, "pass", "mtn_near.png"), k=0.12, period=768, y=30),
        dict(type="wrap", image=save(S10._cached("passfar", S10._pass_far), "pass", "ridge_far.png"), k=0.25, period=512, y=0),
        dict(type="wrap", image=save(mid, "pass", "ridge_mid.png"), k=0.5, period=640, y=0),
        dict(type="rows", image=save(ground, "pass", "ground.png"), period=192, y=150, h=66, rows=[list(q) for q in rows]),
        dict(type="image", image=save(lan, "pass", "stone_lantern.png"), x=40 - 12, y=152 - 27),
        dict(type="image", image=save(post, "pass", "signpost_kyoto.png"), x=1500 - 15, y=154 - 36)],
        crest=[int(v) for v in crest[:640]])
    # ---- 理发店（白天，单屏）
    stages["barber"] = dict(layers=[dict(type="static", image=save(S10._cached("barber", S10._barber_static), "barber", "base.png"))])
    sp = {"pole": save(S10._cached("pole", S10._pole_stripes), "ch10", "pole_stripes.png"),
          "topknot": save(S10.ascii_sprite(S10._KNOT_ART, S10._KNOT_PAL), "ch10", "topknot.png")}
    # ---- 夕阳下的山脊（和胧对决）
    tufts = [[int(q.uniform(0, W)), int(q.uniform(163, 176)), q.random()] for q in (rng("tuft", i) for i in range(16))]
    stages["duel_ridge"] = dict(layers=[dict(type="static", image=save(S10._cached("ridge", S10._ridge_static), "duel_ridge", "base.png"))],
                                fg=[dict(type="sakura", n=18, seed=31, wind=90, fall=16, alpha=1)], tufts=tufts, perch=[list(p) for p in S10.TREE_CROWS])
    for f in (1, -1):
        sp["perch_" + ("r" if f > 0 else "l")] = save(S10.perch_crow_sprite(f), "ch10", f"perch_crow_{'r' if f > 0 else 'l'}.png")
    R = 15
    frames = []
    for fr in range(4):                       # 乌鸦：翅膀上 / 半 / 下 / 半，中心 (R, R)
        cv = Image.new("RGBA", (2 * R, 2 * R), (0, 0, 0, 0))
        S10.draw_crow(cv, R, R, fr / 12 + 1e-6, 1, 1)
        frames.append(save(cv, "ch10", f"crow{fr}.png"))
    sp["crow"] = dict(frames=frames, r=R)
    sp["circling"] = [[70 * q.uniform(0.6, 1.1), q.uniform(0.35, 0.55) * (1 if i % 2 else -1), q.uniform(0, 6.28)]
                      for i, q in enumerate(rng("circ", 2, i) for i in range(5))]
    # ---- 特写：死鱼眼 → 瞪大 → 老师的笑脸 → 含泪（逐张渲染好的画面）
    for nm, t in (("eyes_lazy", 14.80), ("eyes_wide", 15.40), ("eyes_wide_tears", 17.05), ("sensei_smile", 16.30)):
        im = Image.new("RGB", (W, H))
        S10.shot_eyes(im, t)
        sp[nm] = save(im, "ch10", f"{nm}.png")
    stages["ch10"] = sp


# ============================================================== 第十一章：松阳老师（原片 s11，泛黄的回忆）
CHAPTERS["ch11"] = ("第十一章", "松阳老师")
NAME_CARDS["shouyou"] = ("吉田松阳", "松下私塾的老师", "SHOUYOU")
NAME_CARDS["shiroyasha"] = ("白夜叉", "攘夷战争的传说", "SHIROYASHA")
NAME_CARDS["sakamoto"] = ("坂本辰马", "快援队｜啊哈哈哈", "SAKAMOTO", "left")
SFX.update({"啪!!": dict(size=26, angle=-8), "住手——！！": dict(color=(255, 255, 255), size=24, angle=-4)})


def ch11(stages, c):
    """直接用调研里测过的导出脚本（docs/章节素材调研/test_s11）：图片写进 assets/bg|props|chars|ui|fx/s11。"""
    import importlib
    import json as _json
    import os as _os
    import sys as _sys
    game = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    test = _os.path.join(game, "docs", "章节素材调研", "test_s11")
    cwd = _os.getcwd()
    _sys.path.insert(0, test)
    try:
        import h11
        h11.OUT = game
        E11 = importlib.import_module("export_s11")
        E11.OUT = game
        for name in ("battlefield", "yard", "classroom", "fire", "joui", "ridge", "cliff", "present"):
            stages["s11_" + name] = getattr(E11, "set_" + name)()
        P11 = importlib.import_module("props_s11")           # 跑一遍：道具、角色、名牌、拟声字、泛黄用的暗角
        meta_path = _os.path.join(game, "s11_props.json")
        meta = _json.load(open(meta_path, encoding="utf-8"))
        _os.remove(meta_path)
        rel = lambda *p: "/".join(("assets",) + p)                        # noqa: E731
        stages["ch11"] = dict(props=meta["props"], vignette=rel("fx", "s11", "vignette.png"), after=rel("fx", "s11", "after_mul.png"))
        del P11
    finally:
        _sys.path.remove(test)
        _os.chdir(cwd)


# ============================================================== 第十二章：洛阳决战·离别（原片 s12）
CHAPTERS["ch12"] = ("第十二章", "洛阳决战·离别")
NAME_CARDS["umibozu"] = ("星海坊主", "传说中的宇宙最强掠夺者｜神乐的爸爸", "UMIBOZU")
SFX.update({"锵!!": dict(size=24, angle=10), "砰!": dict(size=18, angle=-12), "咚——!!": dict(size=26, angle=-6),
            "叮!": dict(color=(255, 255, 255), size=16, angle=10), "叮": dict(color=(255, 255, 255), size=12, angle=-14)})


def ch12(stages, c):
    """同第十一章：直接用调研里测过的导出脚本（docs/章节素材调研/test_s12）。"""
    import importlib
    import json as _json
    import os as _os
    import sys as _sys
    game = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    test = _os.path.join(game, "docs", "章节素材调研", "test_s12")
    cwd = _os.getcwd()
    _sys.path.insert(0, test)
    try:
        import h12
        h12.OUT = game
        E12 = importlib.import_module("export_s12")
        E12.OUT = game
        for name in ("rakuyo", "harbour", "deck", "dock"):
            stages["s12_" + name] = getattr(E12, "set_" + name)()
        importlib.import_module("props_s12")
        meta_path = _os.path.join(game, "s12_props.json")
        meta = _json.load(open(meta_path, encoding="utf-8"))
        _os.remove(meta_path)
        stages["ch12"] = dict(props=meta["props"], anchors=meta.get("anchors", {}))
    finally:
        _sys.path.remove(test)
        _os.chdir(cwd)


# ============================================================== 第十三章：银之魂篇（原片 s13）
CHAPTERS["ch13"] = ("第十三章", "银之魂篇")
NAME_CARDS["utsuro"] = ("虚", "不死之身｜松阳的另一面", "UTSURO")
SFX.update({"高杉——！！": dict(color=(214, 28, 48), size=26, angle=-6), "啪！": dict(color=(255, 240, 200), size=16, angle=-10)})


def ch13(stages, c):
    """江户屋顶（天人舰队压在头上）：夜 / 黎明两套图层（调研 s13.md 的配方）；调研里已经烘好的角色和道具直接拷进来。"""
    import glob as _glob
    import json as _json
    import os as _os
    import shutil as _sh
    from bg import common as C, edo as E
    from bg._draw import graded_layer
    from engine.core import rng
    save, crop, grab, grab_add, sprite = _tools(c)
    W, H = c["W"], c["H"]
    game = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    test = _os.path.join(game, "docs", "章节素材调研", "test_s13", "out")
    # 角色（s13_extra：一张图集里放了好几个人的特殊动作）、道具
    dch = _os.path.join(game, "assets", "chars", "s13")
    _os.makedirs(dch, exist_ok=True)
    for f in ("s13_extra.png", "s13_extra.json"):
        _sh.copy2(_os.path.join(test, "chars", f), _os.path.join(dch, f))
    dpr = _os.path.join(game, "assets", "props", "s13")
    _os.makedirs(dpr, exist_ok=True)
    for f in _glob.glob(_os.path.join(test, "props", "*.png")):
        _sh.copy2(f, dpr)
    meta = _json.load(open(_os.path.join(test, "props", "props.json"), encoding="utf-8"))
    props = {}
    for k, v in meta.items():
        name = k if k.endswith(".png") else k + ".png"
        # 说明文字不进数据（有的说明以 .png 结尾，加载器会当成图片去找）
        props[name[:-4]] = dict({kk: vv for kk, vv in v.items() if kk not in ("note", "place", "use")}, image="assets/props/s13/" + name)
    stages["ch13"] = dict(props=props)
    ships = {}

    def ship(kind, facing, tod, haze, scale=1):
        hz = round(haze, 2)
        k = f"{kind}_s{scale}_f{facing}_{tod}_h{int(hz * 100)}"
        if k not in ships:
            spr = C.cached(("ship", kind, scale, facing, tod, hz), lambda: E._ship_sprite(kind, scale, facing, tod, hz))
            ships[k] = dict(image=save(spr, "ch13", "ships", k + ".png"), w=spr.width, h=spr.height)
        return ships[k]

    def stack(tod, body=True):
        sky = Image.new("RGB", (W, H))
        C.sky(sky, tod, 0.0, horizon=150, body=body, stars=False)
        L = [dict(type="static", image=save(sky, "ch13", tod, f"sky{'' if body else '_nobody'}.png"))]
        n, ymax = (80, 120) if tod == "night" else (14, 36)
        sun = C.tod_info(tod)["sun"]
        L.append(dict(type="stars", dim=1.0 if tod == "night" else 0.55, skip=list(sun), items=[
            [x, y, sp, ph, big, list(cc)] for x, y, sp, ph, big, cc in C.cached(("stars", tod, ymax), lambda: C._star_list(7, n, ymax))]))
        cl = []
        for i in range(6):
            r = rng("cloud", 3, i)
            depth = r.uniform(0.25, 1.0)
            w = int(26 + 50 * depth * r.uniform(0.7, 1.2))
            h = int(max(7, w * r.uniform(0.22, 0.32)))
            spr = C.cached(("cloud", 3, i, tod, w, h), lambda: C._cloud_sprite(3, i, tod, w, h, (1 - depth) * 0.45))
            y = int(4 + 66 * (1 - depth) * r.uniform(0.5, 1.0) + r.uniform(0, 66 * 0.4))
            cl.append(dict(image=save(spr, "ch13", tod, f"cloud{i}.png"), x0=r.uniform(0, W + 200), y=y, vx=2.0 + 5.0 * depth, k=0.04 + 0.16 * depth))
        L.append(dict(type="clouds", span=W + 200, clouds=cl))
        far, near = C.cached(("mtn", tod), lambda: C._mountain_layers(tod))
        L += [dict(type="wrap", image=save(far, "ch13", tod, "mtn_far.png"), period=768, k=0.05, y=68),
              dict(type="wrap", image=save(near, "ch13", tod, "mtn_near.png"), period=768, k=0.12, y=68), dict(type="fleet", key="armada")]
        term = C.cached(("terminal", tod), lambda: E._terminal_layer(tod))
        L.append(dict(type="terminal", image=save(term, "ch13", tod, "terminal.png"), w=term.width, h=term.height, k=0.1, side_px=tod == "night"))
        for name, key, fn, depth, gr, gs, P, k in (
                ("far", ("edo_far",), E._far_city, 0.5, 2, 0.3, 896, 0.25), ("castle", ("edo_castle",), E._castle_layer, 0.32, 3, 0.5, 1536, 0.4),
                ("mid", ("edo_mid",), E._mid_city, 0.18, 3, 0.45, 1024, 0.6)):
            lay = graded_layer(key, fn, tod, depth=depth) if name == "castle" else graded_layer(key, fn, tod, depth=depth, glow_radius=gr, glow_strength=gs)
            L.append(dict(type="wrap", image=save(lay, "ch13", tod, name + ".png"), period=P, k=k, y=0))
        rw = graded_layer(("roofwalk",), E._walk_layer, tod, depth=0.0, glow_radius=3, glow_strength=0.5)
        L.append(dict(type="roof", image=save(rw, "ch13", tod, "roofwalk.png"), period=512, k=1.0, y=160 - 30, h=110,
                      below=list(C.grade_color((40, 36, 48), tod))))
        return L
    fleet = dict(overlays={}, far=[], mid=[])
    for lvl in (0.25, 0.5, 0.75, 1.0):
        fleet["overlays"][str(lvl)] = save(C.cached(("fleetdark", lvl), lambda: E._dark_overlay(lvl)), "ch13", "fleet", f"dark_{lvl}.png")
    for i in range(26):
        r = rng("fleetfar", i)
        kind = r.choice(("cruiser", "saucer", "cruiser", "pirate"))
        fleet["far"].append(dict(spx=r.uniform(3, 7), x0=r.uniform(0, W + 160), y=r.uniform(58, 118), **ship(kind, -1, "night", 0.72)))
    for i in range(7):
        r = rng("fleetmid", i)
        kind = r.choice(("cruiser", "pirate", "cruiser"))
        fleet["mid"].append(dict(spx=r.uniform(6, 10), x0=r.uniform(0, W + 260), y=r.uniform(62, 128), **ship(kind, -1, "night", 0.3)))
    fleet["mothership"] = ship("mothership", 1, "night", 0.1)
    fx = {}
    from scenes import _s13_art as A
    A.fire_glow(Image.new("RGB", (W, H)), 0.0, 100, 150, 1.0)
    fx["fire"] = dict(image=save(A._CACHE[("fireglow", 100, 150)], "ch13", "fx", "fire_100.png"), y=100)
    for r in (16,):
        disc = Image.new("RGBA", (2 * r + 3, 2 * r + 3), (0, 0, 0, 0))
        d = ImageDraw.Draw(disc)
        cc = r + 1
        d.ellipse([cc - r - 1, cc - r - 1, cc + r + 1, cc + r + 1], fill=(255, 196, 130, 255))
        d.ellipse([cc - r, cc - r, cc + r, cc + r], fill=(255, 238, 190, 255))
        d.ellipse([cc - r + 3, cc - r + 3, cc + r - 5, cc + r - 5], fill=(255, 252, 232, 255))
        fx["sun"] = dict(disc=save(disc, "ch13", "fx", f"sun{r}_disc.png"), disc_off=-(r + 1),
                         glow=save(C.glow_sprite(r * 3, (255, 170, 110), 1.0), "ch13", "fx", f"sun{r}_glow.png"), glow_off=-3 * r)
    stages["ch13_night"] = dict(layers=stack("night"), fleet=fleet, fx=fx)
    stages["ch13_dawn"] = dict(layers=stack("dawn", body=False), fleet=fleet, fx=fx)


# ============================================================== 终章：两年后（原片 s14 尾声）
CHAPTERS["ch14"] = ("终章", "两年后")


def ch14(stages, c):
    """两年后的歌舞伎町（雨 / 雨后 / 黄昏，外加万事屋门口那个镜头）、河堤、黄昏的事务所。
    调研 s14.md 里已经导出并逐像素核对过的文件（test_s14/out）直接拷进来；街道的画法在 gfx.js 的 kstreet 图层。"""
    import json as _json
    import os as _os
    import shutil as _sh
    game = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    test = _os.path.join(game, "docs", "章节素材调研", "test_s14", "out")
    bg = _os.path.join(game, "assets", "bg", "ch14")
    for sub in ("street", "riverbank", "office"):
        _sh.copytree(_os.path.join(test, sub), _os.path.join(bg, sub), dirs_exist_ok=True)

    def prefix(v, base):      # JSON 里所有 .png 路径前面加上游戏里的目录（说明文字不要）
        if isinstance(v, dict):
            return {k: prefix(x, base) for k, x in v.items() if k != "note"}
        if isinstance(v, list):
            return [prefix(x, base) for x in v]
        if isinstance(v, str) and v.endswith(".png"):
            return base + v
        return v
    street = _json.load(open(_os.path.join(test, "street", "street.json"), encoding="utf-8"))
    stages["ch14_street"] = prefix(street, "assets/bg/ch14/street/")
    for tod in ("storm", "day", "dusk"):
        stages[f"ch14_{tod}"] = dict(layers=[dict(type="kstreet", tod=tod)])
    stages["ch14_front"] = dict(layers=[dict(type="kstreet", tod="storm", dy=36, frame=True)], fg=[dict(type="kstreet_rail", alpha=1)])
    # 河堤（冲田轰土方）：天空 → 云 → 远山 → 河 → 地面 → 樱花树
    rb = _json.load(open(_os.path.join(test, "riverbank", "riverbank.json"), encoding="utf-8"))
    P = lambda n: "assets/bg/ch14/" + n
    rv, hi, lo = rb["river"], rb["river"]["hi"], rb["river"]["lo"]
    stages["ch14_river"] = dict(layers=[
        dict(type="static", image=P("riverbank/sky.png")),
        dict(type="clouds", span=rb["clouds"]["span"], clouds=[dict(image=P(x["image"]), x0=x["x0"], y=x["y"], vx=x["vx"], k=0) for x in rb["clouds"]["items"]]),
        dict(type="wrap", image=P("riverbank/mountains.png"), period=384, k=0, y=42),
        dict(type="river", image=P("riverbank/river_base.png"), y=rv["y"], h=rv["h"], dashes=rb["dashes"], hi=hi, lo=lo,
             mid=[int(a + (b - a) * 0.5) for a, b in zip(hi, lo)], reflect_x=rv["reflect_x"], rc=rv["reflect_c"]),
        dict(type="wrap", image=P("riverbank/ground.png"), period=384, k=0, y=136),
        dict(type="tree", frames=[P(f"riverbank/tree{k}.png") for k in range(3)], **rb["tree"]),
    ])
    # 黄昏的事务所（8 帧环境动画，4 fps）+ 前景的桌子
    amb = [P(f"office/dusk_amb{k}.png") for k in range(8)]
    stages["ch14_office"] = dict(amb=amb, amb_fps=4, door=[amb[0]])
    # 角色：斗篷银时、终章的特殊动作
    dch = _os.path.join(game, "assets", "chars", "s14")
    _os.makedirs(dch, exist_ok=True)
    for f in ("gintoki_hooded.png", "s14_extra.png", "s14_extra.json"):
        _sh.copy2(_os.path.join(test, "chars", f), _os.path.join(dch, f))
    stale = _os.path.join(dch, "gintoki_hooded.json")
    if _os.path.exists(stale):
        _os.remove(stale)
    # 斗篷银时同一张图集用两次：兜帽戴着（旅人）/ 摘了兜帽（还披着斗篷）；idle / walk / run 指到对应的那几行，玩家就能直接操控
    hood = _json.load(open(_os.path.join(test, "chars", "gintoki_hooded.json"), encoding="utf-8"))
    hood.pop("eyes", None)
    for cid, name, al in (("gintoki__hooded", "斗篷旅人", dict(idle="idle_hood", walk="walk_hood", run="run_hood", talk="idle_hood")),
                          ("gintoki__cloak", "银时", dict(idle="idle_cloak", walk="walk_cloak", run="walk_cloak", talk="idle_cloak"))):
        m = dict(hood, id=cid, name=name, aliases=al)
        _json.dump(m, open(_os.path.join(dch, cid + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
    # 道具 + 冲击帧 / 定格帧（键不带 .png；office/ 下的前景也放进来）
    dpr = _os.path.join(game, "assets", "props", "s14")
    _os.makedirs(dpr, exist_ok=True)
    meta = _json.load(open(_os.path.join(test, "props", "props.json"), encoding="utf-8"))
    props = {}
    for k, v in meta.items():
        folder, name = k.split("/", 1)
        if folder not in ("props", "frames", "office") or folder == "office" and "fg" not in name:
            continue
        sub = "" if folder == "props" else folder + "/"
        _os.makedirs(_os.path.join(dpr, sub), exist_ok=True)
        _sh.copy2(_os.path.join(test, folder, name), _os.path.join(dpr, sub, name))
        props[name[:-4]] = dict({kk: vv for kk, vv in v.items() if kk not in ("note", "pop")}, image=f"assets/props/s14/{sub}{name}")
    # 雨后的光柱：原片按遮罩逐像素调色，这里先烘成 (255,236,190) + 分三档的透明度（4×4 抖动），JS 里再整体乘 0.22·k
    m = Image.open(_os.path.join(test, "props", "light_shafts_mask.png")).convert("L")
    bay = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
    sh = Image.new("RGBA", m.size, (255, 236, 190, 0))
    mp, sp = m.load(), sh.load()
    for y in range(m.height):
        for x in range(m.width):
            lv = min(3, int(mp[x, y] / 255 * 3 + bay[y % 4][x % 4] / 16))
            if lv:
                sp[x, y] = (255, 236, 190, int(lv / 3 * 255))
    sh.save(_os.path.join(dpr, "light_shafts.png"))
    props["light_shafts"] = dict(w=m.width, h=m.height, image="assets/props/s14/light_shafts.png")
    stages["ch14"] = dict(props=props)


CHAPTER_FUNCS = [ch3, ch4, ch5, ch6, ch7, ch8, ch9, ch10, ch11, ch12, ch13, ch14]
