"""原片各场景里用到、但普通动作表（bake_characters.py）里没有的角色画法，补烘成图集。

两种：
  1. 场景私有的角色（比如 s03 的黑道打手 YAKUZA，定义在 scenes/_s03_props.py 里）：注册以后照 bake_characters 的做法
     整套烘焙（所有标准动作 + 头像），游戏里能当敌人用。
  2. 带参数的特殊动作（骑小绵羊时挖鼻孔、被定春叼着乱晃……）：按原片的参数单独渲染，存成「<角色>__<场景>」图集，
     对话头像沿用本体的。

用法：python bake_scene_extras.py [s03 s04 ...]     不写就全部；输出到 ..\\角色图集\\<id>\\（格式同 bake_characters）
"""
import json
import math
import os
import sys

import bake_characters as B          # 设好了 sys.path / chdir 到 ..\源码
from PIL import Image, ImageChops, ImageDraw

from chars import register, render_sprite, get_def  # noqa: E402

OUT = B.OUT


def lerp(a, b, k):
    return a + (b - a) * k


# ------------------------------------------------------------------ 打包（同 bake_characters 的格子规则）
def pack(out_id, name, rows, base=None):
    """rows: [(动作名, kind, fps, [(img, ax, ay), ...])] → 写 <id>.png / <id>.json。"""
    L = R = U = D = 0
    for *_, frs in rows:
        for im, ax, ay in frs:
            bb = im.getbbox()
            if bb is None:
                continue
            L, R, U, D = max(L, ax - bb[0]), max(R, bb[2] - ax), max(U, ay - bb[1]), max(D, bb[3] - ay)
    L, R, U, D = L + B.PAD, R + B.PAD, U + B.PAD, D + B.PAD
    cw, ch = L + R, U + D
    atlas = Image.new("RGBA", (max(len(r[3]) for r in rows) * cw, len(rows) * ch), (0, 0, 0, 0))
    anims = {}
    for row, (n, kind, fps, frs) in enumerate(rows):
        for i, (im, ax, ay) in enumerate(frs):
            atlas.paste(im, (i * cw + L - ax, row * ch + U - ay), im)
        anims[n] = dict(row=row, frames=len(frs), fps=fps, kind=kind)
    odir = os.path.join(OUT, out_id)
    os.makedirs(odir, exist_ok=True)
    atlas.save(os.path.join(odir, f"{out_id}.png"))
    meta = dict(id=out_id, name=name, work="银魂", image=f"{out_id}.png", cell=[cw, ch], pivot=[L, U], facing="right",
                animations=anims, aliases={}, expressions=[],
                variants=({"base": base, "说明": f"原片场景里的特殊动作；头像看 {base} 目录"} if base else {}),
                source=dict(project="gintama_pixel", call="见 烘焙脚本/bake_scene_extras.py"))
    with open(os.path.join(odir, f"{out_id}.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    print(f"  {out_id}: {len(rows)} 个动作，格子 {cw}x{ch}")
    return meta


def baked(cid, pose, name, **kw):
    """照 bake_characters 的取帧规则烘一个动作（带渲染参数）。"""
    return [(name + e["name"][len(pose):], e["kind"], e["fps"], e["frames"]) for e in B.bake_pose(cid, pose, kw)]


def explicit(cid, pose, name, specs, kind="oneshot", fps=12):
    """手挑的几帧：specs = [dict(t=, p=, expr=, **kwargs)]。"""
    frs = []
    for s in map(dict, specs):
        t, p, expr = s.pop("t", 0.25), s.pop("p", None), s.pop("expr", None)
        spr, ax, ay = render_sprite(cid, pose, t, p, expr, 1, **s)
        frs.append((spr.convert("RGBA"), int(ax), int(ay)))
    return [(name, kind, fps, frs)]


# ------------------------------------------------------------------ s03 神乐与定春
def s03():
    from scenes import _s03_props as P
    for d in P.YAKUZA:                    # 黑道打手：私有角色，整套烘焙（能当敌人打）
        register(d)
        r = B.bake_one(d.id)
        print(f"  {d.id}: {r.get('animations')} 个动作" + (f"，错误 {r['errors']}" if r.get("errors") else ""))
    pack("gintoki__s03", "银时（s03 特殊动作）", base="gintoki", rows=(
        baked("gintoki", "nosepick", "scooter_nosepick", legs="sit", arm_b=72)
        + baked("gintoki", "shock", "sit_shock", legs="sit")
        + baked("gintoki", "sit", "sit_shocked", expr="shock", arm_f=72, arm_b=70)
        + baked("gintoki", "sit", "sit_cry_wallet", expr="cry", arm_f=100, arm_b=60)
        + explicit("gintoki", "kneel", "cower", [dict(expr="shock", arm_f=110, arm_b=120), dict(expr="shock", arm_f=125, arm_b=115)], "loop", 8)
        + explicit("gintoki", "run", "dangle", [dict(t=k / 12 * 2.6, arm_f=130 + 40 * math.sin(k / 12 * 26),
                                                     arm_b=150 + 40 * math.cos(k / 12 * 23)) for k in range(12)], "loop")))
    pack("kagura__s03", "神乐（s03 特殊动作）", base="kagura", rows=(
        baked("kagura", "ready", "aim", weapon=8, arm_f=90)
        + baked("kagura", "ready", "blow_smoke", weapon=82, arm_f=60, arm_b=-10, expr="smug")
        + explicit("kagura", "kneel", "poke", [dict(arm_f=78, arm_b=20), dict(arm_f=88, arm_b=20)], "loop", 6)))
    pack("shinpachi__s03", "新八（s03 特殊动作）", base="shinpachi", rows=(
        baked("shinpachi", "shock", "sit_shock", legs="sit") + baked("shinpachi", "cry", "sit_cry", legs="sit")))
    # 定春咬人：咬住时的「上颚」叠层（和 bite / bite_loop 同格同脚点，画在被咬的人上面）
    ad = os.path.join(OUT, "sadaharu")
    m = json.load(open(os.path.join(ad, "sadaharu.json"), encoding="utf-8"))
    at = Image.open(os.path.join(ad, m["image"])).convert("RGBA")
    (cw, ch), (px, py) = m["cell"], m["pivot"]
    mask = Image.new("L", (cw, ch))
    ImageDraw.Draw(mask).ellipse((45 + px - 38, 12 + py - 64, 76 + px - 38, 47 + py - 64), fill=255)
    rows = []
    for n in ("bite", "bite_loop"):
        a = m["animations"][n]
        frs = []
        for i in range(a["frames"]):
            c = at.crop((i * cw, a["row"] * ch, (i + 1) * cw, (a["row"] + 1) * ch))
            c.putalpha(ImageChops.multiply(c.getchannel("A"), mask))
            frs.append((c, px, py))
        rows.append((n + "_head", a["kind"], a["fps"], frs))
    pack("sadaharu__bitehead", "定春（咬人时的上颚叠层）", base="sadaharu", rows=rows)


# ------------------------------------------------------------------ s05 桂与伊丽莎白
def _on_canvas(fn, w=200, h=160, fx=100, fy=124):
    """原片里直接画到画面上的角色（带地面阴影的那种）：画到透明画布上，脚点 (fx, fy)。"""
    cv = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fn(cv, fx, fy)
    return (cv, fx, fy)


def s05():
    import scenes.s05_katsura as S5
    import scenes._s05_soot as SOOT
    from engine.core import step_frame
    noop = lambda *a, **k: None  # noqa: E731
    S5.overlay_rect = SOOT.overlay_rect = noop     # 地面阴影只能画在 RGB 上；游戏里角色自己有影子

    def soot(name, t0, t1, kind, kw_fn, expr_fn, fps=12):
        n = int(round((t1 - t0) * fps))
        frs = [_on_canvas(lambda cv, x, y, t=t0 + i / fps + 1e-4: SOOT.draw_soot_gintoki(cv, x, y, "idle", t, expr=expr_fn(t), **kw_fn(t)))
               for i in range(n)]
        return [(name, kind, fps, frs)]

    def rs(cid, pose, name, ts, fps, kind="loop", p=None, expr_fn=None, kw_fn=None):
        frs = []
        for t in ts:
            spr, ax, ay = render_sprite(cid, pose, t, p, expr_fn(t) if expr_fn else None, 1, **(kw_fn(t) if kw_fn else {}))
            frs.append((spr.convert("RGBA"), int(ax), int(ay)))
        return [(name, kind, fps, frs)]

    B4 = [k / 4 + 1e-4 for k in range(4)]
    T12 = [k / 12 + 1e-4 for k in range(23)]
    # 满脸黑灰 + 爆炸头的银时（原片 _s05_soot；参数照 s05 的 S6 镜头）
    pack("gintoki__s05", "银时（s05 黑灰爆炸头 + 接炸弹）", base="gintoki", rows=(
        soot("soot_daze", 14.55, 15.05 - 0.1 / 12, "loop",
             lambda t: dict(arm_f=24, arm_b=-24, bob=0, lean=(1 if step_frame(t, 5) % 2 else -1)),
             lambda t: "blink" if 14.93 <= t < 15.02 else "shock")
        + soot("soot_cough", 15.05, 15.35, "loop", lambda t: dict(arm_f=40, arm_b=-10, bob=-1 if t < 15.14 else 0, head_dy=1),
               lambda t: "talk")
        + soot("soot_shout", 15.35, 16.10, "loop",
               lambda t: dict(arm_f=122 + 16 * math.sin(t * 34), arm_b=-132 - 16 * math.sin(t * 34), lean=-1,
                              bob=-1 if step_frame(t, 10) % 2 == 0 else 0, legs="spread"),
               lambda t: "yell" if step_frame(t, 10) % 2 == 0 else "shout")
        + soot("soot_wail", 16.10, 17.10, "loop",
               lambda t: dict(arm_f=8, arm_b=-8, bob=-1 if step_frame(t, 10) % 2 else 0, head_dx=step_frame(t, 10) % 2, lean=0),
               lambda t: "wail" if step_frame(t, 6) % 3 else "cry")
        + rs("gintoki", "idle", "catch", [0.0, 0.05, 0.10, 0.15], 20, "oneshot",
             kw_fn=lambda t: dict(arm_f=lerp(12, 100, 1 - (1 - t / 0.15) ** 3)), expr_fn=lambda t: "normal")
        + rs("gintoki", "idle", "hold_bomb", B4, 4, kw_fn=lambda t: dict(arm_f=100), expr_fn=lambda t: "normal")
        + rs("gintoki", "idle", "hold_bomb_shock", B4, 4, kw_fn=lambda t: dict(arm_f=100), expr_fn=lambda t: "shock")
        + rs("gintoki", "idle", "throw_up", B4, 4, kw_fn=lambda t: dict(arm_f=158, arm_b=-40, lean=-1), expr_fn=lambda t: "shout")))
    pack("katsura__s05", "桂（s05 特殊动作）", base="katsura", rows=(
        rs("katsura", "land", "skid", [0.0], 1, "static", p=0.5, expr_fn=lambda t: "determined",
           kw_fn=lambda t: dict(lean=-3, legs="lunge", arm_f=60, arm_b=120))
        + rs("katsura", "idle", "smug_arm", B4, 4, expr_fn=lambda t: "smug", kw_fn=lambda t: dict(arm_f=118, arm_b=-20))
        + rs("katsura", "idle", "angry_turn", B4, 4, expr_fn=lambda t: "angry", kw_fn=lambda t: dict(arm_f=40))
        + rs("katsura", "idle", "idle_shock", B4, 4, expr_fn=lambda t: "shock")))
    okita_run = [_on_canvas(lambda cv, x, y, t=k / 12 + 1e-4: S5.okita_run_bazooka(cv, x, y, t)) for k in range(23)]
    pack("okita__s05", "冲田（s05 扛着火箭筒跑 / 抖S脸瞄准）", base="okita", rows=(
        [("run_bazooka", "loop", 12, okita_run)]
        + rs("okita", "bazooka", "bazooka_sadist", B4, 4, p=0.3, expr_fn=lambda t: "sadist")))
    pack("hijikata__s05", "土方（s05 拔刀追 / 闪避）", base="hijikata", rows=(
        rs("hijikata", "run", "run_katana", T12, 12, expr_fn=lambda t: "shout" if step_frame(t, 10) % 2 == 0 else "angry",
           kw_fn=lambda t: dict(weapon=14, arm_f=82))
        + rs("hijikata", "run", "duck", T12[:6], 12, "oneshot", expr_fn=lambda t: "shock",
             kw_fn=lambda t: dict(weapon=150, arm_f=160, bob=3))))


# ------------------------------------------------------------------ s04 真选组
def s04():
    from scenes import _s04_art as A, s04_shinsengumi as S

    def timed(cid, pose, name, n, **kw):    # 周期超过 24 帧的动作（近藤蹲草丛、土方抽烟、冲田午睡）：按 12 fps 逐帧取
        frs = []
        for k in range(n):
            spr, ax, ay = render_sprite(cid, pose, k / 12 + 1e-6, None, None, 1, **kw)
            frs.append((spr.convert("RGBA"), int(ax), int(ay)))
        return [(name, "loop", 12, frs)]
    wake = []
    for a in (40, 13, 0):                      # 眼罩掀开、抖S的眼睛（去掉睡觉的 Z）
        spr, ax, ay = render_sprite("okita", "nap", 13.1, None, "sadist", 1, tilt=a)
        wake.append((S._no_zz(spr).convert("RGBA"), int(ax), int(ay)))
    pack("otae__s04", "阿妙（s04 吃团子 / 杀气）", base="otae", rows=(
        baked("otae", "eat", "eat_dango", props=[A.dango_prop]) + baked("otae", "idle", "idle_open", expr="open")
        + baked("otae", "idle", "idle_dark", expr="dark_smile") + baked("otae", "idle", "idle_happy", expr="happy")))
    pack("kondo__s04", "近藤（s04 蹲草丛跟踪 / 被打飞）", base="kondo", rows=(
        timed("kondo", "stalk", "stalk", 53) + baked("kondo", "shock", "shock_shock", expr="shock")
        + baked("kondo", "shock", "shock_cry", expr="cry") + baked("kondo", "fly", "fly_cry", expr="cry")
        + baked("kondo", "land", "land_hurt", expr="hurt") + baked("kondo", "shoulder", "shoulder_smug", expr="smug")))
    pack("hijikata__s04", "土方（s04 坐着抽烟 / 爆炸头）", base="hijikata", rows=(
        timed("hijikata", "smoke", "smoke_sit", 29, legs="sit")
        + baked("hijikata", "idle", "sit_afro", expr="afro", legs="sit") + baked("hijikata", "jump", "jump_afro", expr="afro")
        + baked("hijikata", "point", "point_afro", expr="afro") + baked("hijikata", "idle", "idle_afro", expr="afro")
        + baked("hijikata", "draw", "draw_afro", expr="afro") + baked("hijikata", "walk", "walk_afro", expr="afro")
        + baked("hijikata", "attack", "attack_afro", expr="afro") + baked("hijikata", "hit", "hit_afro", expr="afro")))
    pack("okita__s04", "冲田（s04 午睡 / 醒来 / 抖S瞄准）", base="okita", rows=(
        timed("okita", "nap", "nap", 40) + [("nap_wake", "oneshot", 30, wake)]
        + baked("okita", "bazooka", "bazooka_aim_sadist", expr="sadist")))


# ------------------------------------------------------------------ s06 日常（六个小短篇）
def s06():
    import scenes.s06_daily as S6
    from engine.core import step_frame, ease_out, seg

    def ts(t0, t1, fps):
        return [t0 + i / fps + 1e-4 for i in range(int(round((t1 - t0) * fps)))]

    def rs(cid, pose, name, times, fps, kind="loop", p=None, expr_fn=None, kw_fn=None, post=None):
        frs = []
        for t in times:
            spr, ax, ay = render_sprite(cid, pose, t, p(t) if callable(p) else p, expr_fn(t) if expr_fn else None, 1,
                                        **(kw_fn(t) if kw_fn else {}))
            spr = spr.convert("RGBA")
            if post:
                spr = post(spr.copy(), int(ax), int(ay), t)
            frs.append((spr, int(ax), int(ay)))
        return [(name, kind, fps, frs)]

    def v3_kw(t):                              # 跪在 Jump 面前：手慢慢举起来，然后抓抓抓
        reach = ease_out(seg(t, S6.T_JUMP_IN + 0.15, S6.T_STARS))
        grab = (0, 8, 14, 8)[step_frame(t, 8, 4)] if t >= S6.T_STARS else 0
        return dict(legs="kneel", arm_f=lerp(20, 124, reach) + grab, arm_b=lerp(10, 150, reach), bob=S6._v3_bob(t), head_dy=0,
                    lean=1 if t >= S6.T_STARS else 0)

    def star_patch(spr, ax, ay, t):            # 星星眼
        if t >= S6.T_STARS:
            spr.alpha_composite(S6._sparkle_head().crop((3, 11, 16, 16)), (ax - 6 + 1, ay - 17 + S6._v3_bob(t)))
        return spr
    pack("gintoki__s06", "银时（s06 坐着打小钢珠 / 跪拜 Jump）", base="gintoki", rows=(
        rs("gintoki", "cheer", "cheer_sit", ts(3.0, 4.0, 12), 12, kw_fn=lambda t: dict(legs="sit"),
           expr_fn=lambda t: "shout" if step_frame(t, 6) % 2 == 0 else "happy")
        + rs("gintoki", "idle", "frozen_sit", ts(0, 1, 4), 4, expr_fn=lambda t: "shock",
             kw_fn=lambda t: dict(legs="sit", arm_f=100, arm_b=90, lean=2, head_dx=1))
        + rs("gintoki", "shock", "shock_sit", ts(4.62, 4.70, 12), 12, "static", p=0.1, kw_fn=lambda t: dict(legs="sit"))
        + rs("gintoki", "idle", "blank_sit", ts(0, 1, 4), 4, expr_fn=lambda t: "blink",
             kw_fn=lambda t: dict(legs="sit", arm_f=4, arm_b=-4, head_dy=2, bob=0, lean=1))
        + rs("gintoki", "kneel", "kneel_reach", ts(S6.T_JUMP_IN, S6.T_STARS, 12), 12, "oneshot", expr_fn=lambda t: "shock", kw_fn=v3_kw)
        + rs("gintoki", "kneel", "kneel_stars", ts(7.0, 8.0, 12), 12, expr_fn=lambda t: "happy", kw_fn=v3_kw, post=star_patch)))
    pack("hasegawa__s06", "长谷川（s06 纸箱里哭 / 打小钢珠）", base="hasegawa", rows=(
        rs("hasegawa", "box", "box_cry", ts(0, 4 / 3, 3), 3, expr_fn=lambda t: "cry", kw_fn=lambda t: dict(head_dy=2, bob=0))
        + rs("hasegawa", "cheer", "cheer_sit", ts(3.1, 4.1, 12), 12, kw_fn=lambda t: dict(legs="sit"),
             expr_fn=lambda t: "shout" if step_frame(t + 0.1, 6) % 2 == 0 else "happy")
        + rs("hasegawa", "idle", "frozen_sit", ts(0, 1, 4), 4, expr_fn=lambda t: "shock",
             kw_fn=lambda t: dict(legs="sit", arm_f=100, arm_b=90, lean=2, head_dx=1))
        + rs("hasegawa", "shock", "shock_sit", ts(4.62, 4.70, 12), 12, "static", p=0.1, kw_fn=lambda t: dict(legs="sit"))
        + rs("hasegawa", "idle", "blank_sit", ts(0, 1, 4), 4, expr_fn=lambda t: "blink",
             kw_fn=lambda t: dict(legs="sit", arm_f=4, arm_b=-4, head_dy=2, bob=0, lean=1))))
    pack("kagura__s06", "神乐（s06 坐着嚼醋昆布）", base="kagura", rows=(
        rs("kagura", "sukonbu", "sukonbu_sit", ts(0, 1, 6), 6, kw_fn=lambda t: dict(legs="sit"))))
    pack("sadaharu__s06", "定春（s06 被压到）", base="sadaharu", rows=(
        rs("sadaharu", "idle", "idle_hurt", ts(0, 1, 12), 12, expr_fn=lambda t: "hurt")))
    pack("otae__s06", "阿妙（s06 坐着的杀气 / 薙刀往下刺）", base="otae", rows=(
        rs("otae", "sit", "sit_dark", ts(0, 1, 12), 12, expr_fn=lambda t: "dark_smile")
        + rs("otae", "attack", "rise_dark", [S6.T_RISE + k * 0.1 for k in range(5)], 12, "oneshot",
             p=lambda t: 0.12 + 0.2 * seg(t, S6.T_RISE, S6.T_STAB), expr_fn=lambda t: "dark_smile")
        + rs("otae", "thrust", "stab_down", ts(0, 1, 12), 12, p=1.0, expr_fn=lambda t: "dark_smile",
             kw_fn=lambda t: dict(weapon=-90, arm_f=30, arm_b=20, lean=3))))
    pack("kondo__s06", "近藤（s06 地板下 / 吓僵）", base="kondo", rows=(
        rs("kondo", "stalk", "stalk_nobush", ts(S6.T6, S6.T_STAB, 12), 12, kw_fn=lambda t: dict(bush=False, arm_f=40, arm_b=160))
        + rs("kondo", "kneel", "frozen", ts(S6.T_STAB, S6.T_STAB + 0.5, 12), 12, expr_fn=lambda t: "shock",
             kw_fn=lambda t: dict(legs="kneel", arm_f=14, arm_b=-18, lean=-1, head_dx=int(math.sin(t * 50)), head_dy=0))))


# ------------------------------------------------------------------ s07 红樱篇
def s07():
    from scenes import _s07_art as A

    def tk(k):                                 # 同 bake_characters 的取帧网格（0.25 s 起，12 fps）
        return (3 + k) / 12 + 1e-6

    def fr(cid, pose, k, p=None, expr=None, **kw):
        spr, ax, ay = render_sprite(cid, pose, tk(k), p, expr, 1, **kw)
        return spr.convert("RGBA"), int(ax), int(ay)

    def shadow(f, rim_dir, **kw):              # 逆光剪影（轮廓光朝左；游戏里朝左站时翻过来，光就朝右）
        spr, ax, ay = f
        return A.shadowed(spr, rim_dir=rim_dir, **kw).convert("RGBA"), ax, ay

    def loop(name, n, fn):
        return (name, "loop" if n > 1 else "static", 12, [fn(k) for k in range(n)])

    def oneshot(name, fn, n=8):
        return (name, "oneshot", 12, [fn(k, k / (n - 1)) for k in range(n)])
    pack("okada_nizo__s07", "冈田似藏（s07 红樱 / 逆光 / 断刀）", base="okada_nizo", rows=[
        oneshot("benizakura_grow", lambda k, p: fr("okada_nizo", "benizakura", k, grow=p)),
        loop("benizakura", 12, lambda k: fr("okada_nizo", "benizakura", k)),
        loop("shadow_walk", 15, lambda k: shadow(fr("okada_nizo", "walk", k), -1)),
        loop("shadow_idle", 12, lambda k: shadow(fr("okada_nizo", "idle", k), -1)),
        loop("shadow_attack95", 1, lambda k: shadow(fr("okada_nizo", "attack", k, p=0.95), -1)),
        oneshot("thrust_evil", lambda k, p: fr("okada_nizo", "thrust", k, p=p, expr="evil")),
        oneshot("attack_evil", lambda k, p: fr("okada_nizo", "attack", k, p=p, expr="evil")),
        loop("ready_evil", 6, lambda k: fr("okada_nizo", "ready", k, expr="evil")),
        loop("guard_evil", 1, lambda k: fr("okada_nizo", "guard", k, expr="evil")),
        loop("attack_end", 1, lambda k: fr("okada_nizo", "attack", k, p=1.0, expr="determined")),
        loop("attack_broken", 1, lambda k: fr("okada_nizo", "attack", k, p=1.0, expr="open_eyes", weapon=None)),
        loop("lie_sad", 1, lambda k: fr("okada_nizo", "lie", k, expr="sad"))])
    pack("gintoki__s07", "银时（s07 受伤跪地 / 挖鼻孔）", base="gintoki", rows=[
        oneshot("hit_sad", lambda k, p: fr("gintoki", "hit", k, p=p, expr="sad")),
        loop("kneel_bokuto_sad", 1, lambda k: fr("gintoki", "kneel", k, expr="sad", weapon=-38, arm_f=62, sheathed=False)),
        loop("kneel_bokuto_angry", 1, lambda k: fr("gintoki", "kneel", k, expr="angry", weapon=-38, arm_f=62, sheathed=False)),
        loop("guard_determined", 1, lambda k: fr("gintoki", "guard", k, expr="determined")),
        loop("ready_smug", 6, lambda k: fr("gintoki", "ready", k, expr="smug")),
        loop("ready_angry", 6, lambda k: fr("gintoki", "ready", k, expr="angry")),
        loop("nosepick_normal", 12, lambda k: fr("gintoki", "nosepick", k, expr="normal")),
        loop("idle_smug", 12, lambda k: fr("gintoki", "idle", k, expr="smug"))])
    pack("elizabeth__s07", "伊丽莎白（s07「桂先生……」）", base="elizabeth", rows=[
        oneshot("sign_katsura", lambda k, p: fr("elizabeth", "sign", k, p=p, expr="sad", sign="桂先生……")),
        loop("sign_katsura_loop", 6, lambda k: fr("elizabeth", "sign", k, expr="sad", sign="桂先生……"))])
    pack("katsura_short__s07", "短发的桂（s07）", base="katsura_short", rows=[
        loop("ready_determined", 6, lambda k: fr("katsura_short", "ready", k, expr="determined")),
        loop("idle_determined", 12, lambda k: fr("katsura_short", "idle", k, expr="determined"))])
    pack("takasugi__s07", "高杉（s07 坐在船舷上抽烟）", base="takasugi", rows=[
        loop("sit_rail_norail", 24, lambda k: fr("takasugi", "sit_rail", k, rail=False)),
        loop("sit_rail_norail_smug", 24, lambda k: fr("takasugi", "sit_rail", k, rail=False, expr="smug")),
        loop("smoke_smug", 12, lambda k: fr("takasugi", "smoke", k, expr="smug"))])
    pack("harusame__s07", "春雨海盗（s07 冲锋 / 前景剪影）", base="harusame", rows=[
        loop("fgsil_idle", 12, lambda k: shadow(fr("harusame", "idle", k), 1, body=(12, 10, 22), rim=(96, 80, 132))),
        loop("charge_angry", 23, lambda k: fr("harusame", "charge", k, expr="angry"))])


# ------------------------------------------------------------------ s08 真选组动乱篇
def s08():
    from scenes import _s08_kit as K

    def tk(k):
        return (3 + k) / 12 + 1e-6

    def fig(who, pose, k, p=None, expr=None, t=None, **kw):     # 同原片 K.draw_fig 贴上去之前的样子（不带光晕）
        tint_c, sil, rim, side, keep = kw.pop("tint_c", None), kw.pop("sil", None), kw.pop("rim", None), kw.pop("rim_side", 1), kw.pop("keep", None)
        spr, ax, ay = K.fig_sprite(who, pose, tk(k) if t is None else t, p, expr, 1, 0.0, (255, 255, 255), 0, kw.pop("variant", 0), **kw)
        if sil is not None:
            spr = K.sil_rim(spr, sil, rim, side, keep)
        return spr.convert("RGBA"), int(ax), int(ay)

    def loop(name, n, fn):
        return (name, "loop" if n > 1 else "static", 12, [fn(k) for k in range(n)])
    # 叛军小兵：原片 K.GRUNTS 四种发型，注册后用官方烘焙整套烘（能当敌人打）
    for d in K.GRUNTS:
        register(d)
        r = B.bake_one(d.id)
        print(f"  {d.id}: {r.get('animations')} 个动作" + (f"，错误 {r['errors']}" if r.get("errors") else ""))
    pack("hijikata__s08", "土方（s08 破除诅咒）", base="hijikata", rows=[
        loop("guard_shock", 1, lambda k: fig("hijikata", "guard", k, expr="shock")),
        loop("ready_shout", 6, lambda k: fig("hijikata", "ready", k, expr="shout")),
        loop("shoulder_angry", 12, lambda k: fig("hijikata", "shoulder", k, expr="angry"))])
    pack("ito__s08", "伊东（s08 冷眼 / 推眼镜 / 跪地微笑）", base="ito", rows=[
        loop("idle_cold", 12, lambda k: fig("ito", "idle", k, expr="cold")),
        ("glasses_push", "oneshot", 12, [fig("ito", "glasses_push", 0, t=k / 12 + 1e-6) for k in range(20)]),
        loop("kneel_smile", 1, lambda k: fig("ito", "kneel", k, expr="smile", head_dy=1, sheathed=False)),
        loop("kneel_sleep", 1, lambda k: fig("ito", "kneel", k, expr="sleep", head_dy=2, sheathed=False))])
    pack("toshi__s08", "托西（s08）", base="toshi", rows=[loop("idle_gloom", 12, lambda k: fig("toshi", "idle", k, expr="gloom"))])
    pack("yamazaki__s08", "山崎（s08 啃红豆面包 / 呆住）", base="yamazaki", rows=[
        ("anpan", "loop", 12, [fig("yamazaki", "anpan", 0, t=k / 12 + 1e-6) for k in range(54)]),
        loop("idle_dead", 12, lambda k: fig("yamazaki", "idle", k, expr="dead"))])
    pack("kagura__s08", "神乐（s08 车顶上扫射）", base="kagura", rows=[
        loop("umbrella_shoot_aim", 8, lambda k: fig("kagura", "umbrella_shoot", k, weapon=26, arm_f=112)),
        loop("ready_aim", 6, lambda k: fig("kagura", "ready", k, weapon=26, arm_f=112, expr="determined"))])
    pack("grunt__s08", "叛军（s08 剪影）", base="s08_grunt0", rows=[
        loop("kneel_sil_redeyes", 1, lambda k: fig("grunt", "kneel", k, sil=(12, 10, 20), keep={K.G_EYE: (255, 40, 40)}))])


# ------------------------------------------------------------------ s09 吉原炎上篇
def s09():
    T = [(3 + k) / 12 for k in range(16)]

    def bake(name, cid, pose, frames, kind="loop", **kw):
        frs = []
        for t, p, ex in frames:
            spr, ax, ay = render_sprite(cid, pose, t, p, kw.get("expr"), 1, **{k: v for k, v in dict(kw, **ex).items() if k != "expr"})
            frs.append((spr.convert("RGBA"), int(ax), int(ay)))
        return [(name, kind, 12, frs)]
    pack("kamui__s09", "神威（s09 睁眼）", base="kamui", rows=bake("sit_open_eyes", "kamui", "sit", [(t, None, {}) for t in T[:12]], expr="open_eyes"))
    pack("housen__s09", "凤仙（s09 说话 / 被太阳灼伤）", base="housen", rows=(
        bake("idle_talk", "housen", "idle", [(t, None, {}) for t in T], expr="talk")
        + bake("idle_smug", "housen", "idle", [(t, None, {}) for t in T], expr="smug")
        + bake("shock_hurt", "housen", "shock", [(t, 0.5, {}) for t in T[:6]], expr="hurt")))
    pack("gintoki__s09", "银时（s09 受伤跪地 / 蹲下蓄力）", base="gintoki", rows=(
        bake("kneel_hurt", "gintoki", "kneel", [(T[0], None, {})], "static", expr="hurt")
        + bake("crouch", "gintoki", "land", [(T[0], 0.1, {})], "static", expr="angry", dy=2)))
    pack("seita__s09", "晴太（s09 难过 / 吊在拉杆上）", base="seita", rows=(
        bake("idle_sad", "seita", "idle", [(t, None, {}) for t in T[:12]], expr="sad")
        + bake("dangle", "seita", "jump", [(0, None, dict(dy=0)), (0, None, dict(dy=-1))], expr="shout", arm_f=172, arm_b=160)))
    pack("tsukuyo__s09", "月咏（s09 推拉杆）", base="tsukuyo", rows=bake("shove", "tsukuyo", "punch", [(T[0], 1.0, {})], "static", expr="determined", arm_f=100, arm_b=94, lean=3))


# ------------------------------------------------------------------ s10 将军暗杀篇
def s10():
    from engine.gfx import tint
    T = [(3 + k) / 12 for k in range(16)]
    ONE = [(3 / 12, k / 7, {}) for k in range(8)]

    def bake(name, cid, pose, frames, kind="loop", post=None, **kw):
        frs = []
        for t, p, ex in frames:
            args = dict(kw, **ex)
            expr = args.pop("expr", None)
            spr, ax, ay = render_sprite(cid, pose, t, p, expr, 1, **args)
            spr = spr.convert("RGBA")
            if post:
                spr = post(spr)
            frs.append((spr, int(ax), int(ay)))
        return [(name, kind, 12, frs)]
    pack("shigeshige__s10", "茂茂（s10 发型被剪坏）", base="shigeshige", rows=(
        bake("sit_blink", "shigeshige", "sit", [(t, None, {}) for t in T[:12]], expr="blink", arm_f=40, arm_b=30)
        + bake("sit_haircut", "shigeshige", "sit", [(t, None, {}) for t in T[:12]], expr="haircut", arm_f=40, arm_b=30)
        + bake("sit_haircut_shock", "shigeshige", "sit", [(t, None, {}) for t in T[:12]], expr="haircut_shock", arm_f=40, arm_b=30)
        + bake("walk_haircut", "shigeshige", "walk", [(k / 12, None, {}) for k in range(15)], expr="haircut")
        + bake("idle_haircut", "shigeshige", "idle", [(t, None, {}) for t in T[:12]], expr="haircut")
        + bake("shock_haircut", "shigeshige", "shock", [(t, 0.6, {}) for t in T[:6]], expr="haircut_shock")))
    pack("gintoki__s10", "银时（s10 理发 / 冲刺 / 刀锋相抵）", base="gintoki", rows=(
        bake("barber_snip", "gintoki", "idle", [(T[0], None, dict(arm_f=a)) for a in (130, 135, 130, 135)], expr="normal", bob=0)
        + bake("barber_sleepy", "gintoki", "idle", [(T[0], None, dict(arm_f=a)) for a in (140, 144)], expr="sleep", bob=0)
        + bake("barber_shock", "gintoki", "idle", [(T[0], None, dict(arm_f=134))], "static", expr="shock", bob=0)
        + bake("barber_hold", "gintoki", "idle", [(T[0], None, dict(arm_f=a)) for a in (122, 124)], expr="gloom", bob=0)
        + bake("barber_slap", "gintoki", "idle", [(T[0], None, dict(arm_f=a)) for a in (168, 150)], "oneshot", expr="normal", bob=0)
        + bake("thumbs_smug", "gintoki", "idle", [(T[0], None, dict(arm_f=70))], "static", expr="smug", bob=0)
        + bake("dash_blade", "gintoki", "run", [(k / 12, None, {}) for k in range(12)], weapon=10, arm_f=70)
        + bake("bladelock", "gintoki", "ready", [(T[0], None, dict(expr=e)) for e in ("angry", "hurt", "shout")], "loop",
               arm_f=86, weapon=16, legs="lunge", lean=3, arm_b=40, bob=0)))
    pack("kagura__s10", "神乐（s10 撑着伞走路）", base="kagura", rows=bake(
        "parasol_walk", "kagura", "umbrella_open", [(k / 12, None, dict(leg_phase=k / 12 * 2 * math.pi * 1.6)) for k in range(15)],
        legs="walk", stride=2.5, lift=2.0))
    pack("naraku__s10", "奈落（s10 山脊上的剪影）", base="naraku", rows=bake(
        "ridge", "naraku", "stand_guard", [(t, None, {}) for t in T], post=lambda s: tint(s, (40, 28, 56), 0.5), expr="angry"))
    pack("elizabeth__s10", "伊丽莎白（s10「天诛」）", base="elizabeth", rows=(
        bake("sign_tenchu", "elizabeth", "sign", ONE, "oneshot", sign="天诛")
        + bake("club_tenchu", "elizabeth", "attack", ONE, "oneshot", sign="天诛")))
    pack("oboro__s10", "胧（s10）", base="oboro", rows=(
        bake("idle_cold_smile", "oboro", "idle", [(t, None, {}) for t in T[:12]], expr="cold_smile")
        + bake("ready_angry", "oboro", "ready", [(t, None, {}) for t in T[:6]], expr="angry")
        + bake("bladelock", "oboro", "ready", [(T[0], None, {})], "static", expr="cold_smile", arm_f=86, weapon=8, legs="lunge", lean=3, arm_b=40, bob=0)))


SCENES = {"s03": s03, "s04": s04, "s05": s05, "s06": s06, "s07": s07, "s08": s08, "s09": s09, "s10": s10}

if __name__ == "__main__":
    todo = sys.argv[1:] or list(SCENES)
    for s in todo:
        print(s)
        SCENES[s]()
