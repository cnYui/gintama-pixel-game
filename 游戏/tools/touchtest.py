# -*- coding: utf-8 -*-
"""触屏操作自测：用 Chromium 模拟手机横屏（有触摸、dpr 3），真的去点、去按住方向盘，看游戏有没有照着动。

    python tools/touchtest.py                  # 默认 844×390（常见安卓 / iPhone 横屏）
    python tools/touchtest.py 640 360          # 换屏幕尺寸（16:9 的小手机，按钮会压在画面上）
    python tools/touchtest.py --shots 目录      # 顺便把关键画面存成 png（默认存到系统临时目录）

每一步打印 OK / FAIL；有 FAIL 或页面报错，最后退出码是 1。
测的是：触屏自动显示、点菜单选项、对话 / 菜单 / 连按小游戏时按钮自动收起、方向盘按住走路和滑动换向、多指（方向盘 + 攻击）、
选项框直接点、战斗里 J / K / L、暂停菜单里点选项（含“按键大小”）、提示和名牌不打架、竖屏时的“请横过来”提示、
按键淡出、接键盘收起、冒充 iPhone 时的声音点播。游戏本身的剧情 / 战斗平衡不在这里测（那是 playtest.py 的事）。
"""
import functools
import http.server
import json
import os
import socketserver
import sys
import tempfile
import threading
import time

from playwright.sync_api import sync_playwright

GAME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0.0.0 Mobile Safari/537.36")

IOS_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
          "Version/17.0 Mobile/15E148 Safari/604.1")

fails = []
errors = []


def check(name, ok, detail=""):
    print(("  OK   " if ok else "  FAIL ") + name + (("  " + str(detail)) if detail != "" else ""))
    if not ok:
        fails.append(name)


class Fingers:
    """用 CDP 发多指触摸：每根手指一个编号，touchEnd 带的是“还按着的”手指。"""

    def __init__(self, ctx, page):
        self.cdp = ctx.new_cdp_session(page)
        self.pts = {}

    def _send(self, typ):
        pts = [{"x": x, "y": y, "id": i} for i, (x, y) in self.pts.items()]
        self.cdp.send("Input.dispatchTouchEvent", {"type": typ, "touchPoints": pts})

    def down(self, i, x, y):
        self.pts[i] = (x, y)
        self._send("touchStart")

    def move(self, i, x, y):
        self.pts[i] = (x, y)
        self._send("touchMove")

    def up(self, i):
        self.pts.pop(i, None)
        self._send("touchEnd")

    def tap(self, x, y, i=9, hold=0.06):
        self.down(i, x, y)
        time.sleep(hold)
        self.up(i)


def main():
    args = sys.argv[1:]
    shots = os.path.join(tempfile.gettempdir(), "gintama_touchtest")
    if "--shots" in args:
        k = args.index("--shots")
        shots = args[k + 1]
        del args[k:k + 2]
    W, H = (int(args[0]), int(args[1])) if len(args) >= 2 else (844, 390)
    os.makedirs(shots, exist_ok=True)

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=GAME))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/index.html"

    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        ctx = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=3, is_mobile=True, has_touch=True, user_agent=UA)
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        page.on("console", lambda m: errors.append("console." + m.type + ": " + m.text) if m.type == "error" else None)
        fing = Fingers(ctx, page)
        ev = page.evaluate

        def shot(name):
            page.screenshot(path=os.path.join(shots, name + ".png"))

        def rect(sel):
            return ev("(s) => { const r = document.querySelector(s).getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }", sel)

        def center(sel):
            x, y, w, h = rect(sel)
            return x + w / 2, y + h / 2

        def game_to_css(gx, gy):
            r = ev("() => { const r = G.screen.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }")
            return r[0] + gx * r[2] / 384, r[1] + gy * r[3] / 216

        def has(sel, cls):
            return ev("([s, c]) => document.querySelector(s).classList.contains(c)", [sel, cls])

        def state():
            return ev("""() => ({ scene: G.scene && G.scene.name, ctx: G.touch.ctx, free: !!(G.world && G.world.free), combat: !!(G.world && G.world.combat),
                dlg: !!G.ui.dlg, narr: !!G.ui.narr, menu: !!G.ui.menu, chapter: !!G.ui.chapter,
                px: G.world && G.world.player ? Math.round(G.world.player.x * 10) / 10 : null,
                py: G.world && G.world.player ? Math.round(G.world.player.y * 10) / 10 : null,
                pstate: G.world && G.world.player ? G.world.player.state : null,
                down: Object.keys(G.input.down).filter(k => G.input.down[k]) })""")

        print(f"== 手机横屏 {W}×{H}，dpr 3")
        page.goto(url)
        page.wait_for_function("window.G && G.scene && G.scene.name === 'title'", timeout=60000)
        time.sleep(0.5)

        # ---------------------------------------------------------------- 自动显示、尺寸
        info = ev("() => ({ on: G.touch.on, ctx: G.touch.ctx, b: parseFloat(getComputedStyle(document.getElementById('tc')).getPropertyValue('--b')), scale: G.scale })")
        check("触屏设备自动显示按键", info["on"] and has("body", "tc-on"), info)
        check("标题页：方向盘 + J + E 亮着、K / L 藏起来", (not has("#tc-pad", "tc-off")) and (not has(".tc-j", "tc-off")) and has(".tc-k", "tc-off") and has(".tc-l", "tc-off"))
        check("标题页：暂停钮藏着", has("#tc-pause", "tc-off"))
        # 按钮没有跑出屏幕
        for sel in ("#tc-pad", ".tc-j", ".tc-k", ".tc-l", ".tc-e", "#tc-pause", "#tc-full"):
            x, y, w, h = rect(sel)
            check(f"{sel} 在屏幕里", x >= -0.5 and y >= -0.5 and x + w <= W + 0.5 and y + h <= H + 0.5, [round(v) for v in (x, y, w, h)])
        shot("01_title")
        time.sleep(2.6)
        check("手离开屏幕 2.5 秒后按键淡下去", has("body", "tc-idle"))
        shot("01b_idle")

        # ---------------------------------------------------------------- 点菜单选项
        # 选择章节 → 再点“返回”
        fing.tap(*game_to_css(192, 152 + 18))
        time.sleep(0.4)
        check("一碰屏幕按键又亮起来", not has("body", "tc-idle"))
        check("点“选择章节”进了章节列表", ev("() => G.scene.mode") == "chapters")
        shot("02_chapters")
        # 章节列表里，用方向盘按住 ↓ 能连续往下走（自动连发）
        px, py = center("#tc-pad")
        R = rect("#tc-pad")[2] / 2
        i0 = ev("() => G.scene.idx")
        fing.down(1, px, py + R * 0.7)
        time.sleep(1.4)
        i1 = ev("() => G.scene.idx")
        fing.up(1)
        check("章节列表里按住方向盘 ↓ 会连着往下走", i1 - i0 >= 4, f"{i0} → {i1}")
        # 点第一行回到顶部（章节行：y=42+k*15）
        ev("() => { G.scene.idx = 0; }")
        time.sleep(0.2)
        fing.tap(*game_to_css(192, 42 + 15 * 3 + 6))
        time.sleep(0.2)
        started = ev("() => G.scene.name")
        check("点章节列表里的某一行直接进那一章", started == "world", started)
        # 从头来：回标题，点“从序章开始”
        ev("() => G.goTitle()")
        time.sleep(0.5)
        fing.tap(*game_to_css(192, 152))
        t0 = time.time()
        while time.time() - t0 < 5 and ev("() => G.scene.name") == "title":
            time.sleep(0.1)
        check("点“从序章开始”开始游戏（先是开场动画）", ev("() => G.scene.name") in ("world", "video"), ev("() => G.scene.name"))

        # ---------------------------------------------------------------- 过场 / 对话：按钮自动收起，点屏幕任意处继续
        saw_story = False
        cx, cy = game_to_css(192, 100)
        t0 = time.time()
        while time.time() - t0 < 90:
            s = state()
            if s["ctx"] == "story":
                if not saw_story:
                    saw_story = True
                    time.sleep(0.4)
                    check("对话 / 旁白 / 视频时：方向盘和 J K L E 都收起来（不挡字）", all(has(x, "tc-off") for x in ("#tc-pad", ".tc-j", ".tc-k", ".tc-l", ".tc-e")))
                    check("对话时暂停钮还在", not has("#tc-pause", "tc-off"))
                fing.tap(cx, cy)      # 点画面中央 = 继续
                time.sleep(0.35)
                continue
            if s["free"] and s["ctx"] == "explore" and s["scene"] == "world" and not s["chapter"]:
                break
            time.sleep(0.25)
        s = state()
        check("点屏幕能把过场 / 对话推进到能自由走动", s["free"] and s["ctx"] == "explore", s)
        check("自由走动：方向盘 + K + E 亮，J / L 暗着", (not has("#tc-pad", "tc-off")) and (not has(".tc-k", "tc-dim")) and has(".tc-j", "tc-dim") and has(".tc-l", "tc-dim"))
        shot("03_explore")
        # 手机上提示放在上面，名牌也从上面滑进来：名牌在的时候提示先等着，名牌走了再计时
        ev("() => { G.ui.hint('测试提示', 9); G.ui.nameCard('katsura'); }")
        time.sleep(1.0)
        t_held = ev("() => G.ui.hints[0].t")
        time.sleep(2.2)
        t_after = ev("() => G.ui.hints[0].t")
        check("手机：名牌滑进来时提示先等着，名牌走了再计时", t_held < 0.1 and t_after > 0.4, [round(t_held, 2), round(t_after, 2)])
        st = ev("() => ({ safe: G.touch.safe, ty: G.ui.hints[0] ? 1 : 0 })")
        check("按键压到画面的范围有算出来（左盘 / 右钮 / 右上钮）", 0 <= st["safe"]["l"] <= 384 and 0 <= st["safe"]["r"] <= 384 and st["safe"]["l"] < st["safe"]["r"], st["safe"])
        # 选项框：方向盘 + J / E 亮，K / L 收起；直接点第二项
        ev("() => { window.__r = null; G.ui.choice(['第一章', '第二章', '第三章']).then((r) => { window.__r = r; }); }")
        time.sleep(0.5)
        check("选项框出来：方向盘 + J / E 亮、K / L 收起", state()["ctx"] == "menu" and has(".tc-k", "tc-off") and has(".tc-l", "tc-off") and not has("#tc-pad", "tc-off"), state()["ctx"])
        shot("03b_choice")
        L = ev("() => G.ui.choiceLayout(G.ui.choiceBox)")
        fing.tap(*game_to_css(L["x"] + L["w"] / 2, L["y"] + 3 + 16 * 1 + 8))
        time.sleep(0.4)
        check("点选项框第二项 = 选中并确认", ev("() => window.__r") == 1, ev("() => window.__r"))
        # 连按小游戏：方向盘收起、只留 J / E，点 J 连按
        ev("() => { window.__q = null; G.ui.startQte({ type: 'mash', label: '连按 J！', need: 4, time: 6, decay: 0.5 }).then((r) => { window.__q = r; }); }")
        time.sleep(0.4)
        check("连按小游戏：方向盘、K、L 收起，只留 J / E", state()["ctx"] == "qte" and has("#tc-pad", "tc-off") and has(".tc-k", "tc-off") and not has(".tc-j", "tc-off") and not has(".tc-e", "tc-off"), state()["ctx"])
        shot("03c_qte")
        qx, qy = center(".tc-j")
        for _ in range(8):
            fing.tap(qx, qy, hold=0.04)
            time.sleep(0.1)
        time.sleep(1.2)
        check("连点 J 把连按槽打满", ev("() => window.__q") is True, ev("() => window.__q"))

        # ---------------------------------------------------------------- 方向盘按住走路
        px0 = state()["px"]
        pc = center("#tc-pad")
        R = rect("#tc-pad")[2] / 2
        fing.down(1, pc[0] + R * 0.7, pc[1])
        time.sleep(0.15)
        mid = state()
        check("按住方向盘右边：→ 键按下", "right" in mid["down"] and "left" not in mid["down"], mid["down"])
        check("方向盘的箭头亮了", has("#tc-pad .arr[data-d=right]", "on"))
        time.sleep(0.9)
        px1 = state()["px"]
        shot("04_walk_right")
        fing.up(1)
        time.sleep(0.15)
        check("按住 1 秒，角色往右走了", px1 - px0 > 20, f"{px0} → {px1}")
        check("手指抬起后按键都松开", state()["down"] == [], state()["down"])
        # 斜向：右下
        py0 = state()["py"]
        fing.down(1, pc[0] + R * 0.55, pc[1] + R * 0.55)
        time.sleep(0.15)
        d = state()["down"]
        check("按住右下：→ 和 ↓ 同时按下", "right" in d and "down" in d, d)
        fing.move(1, pc[0] - R * 0.65, pc[1])
        time.sleep(0.15)
        d = state()["down"]
        check("手指滑到左边：换成 ←（→ ↓ 松开）", d == ["left"], d)
        fing.up(1)
        # 多指：方向盘按住 + 跳（K）
        jx, jy = center(".tc-k")
        fing.down(1, pc[0] + R * 0.7, pc[1])
        time.sleep(0.1)
        fing.down(2, jx, jy)
        time.sleep(0.12)
        ms = state()
        check("多指：一边按住方向盘一边按 K，两个都生效", "right" in ms["down"] and ("jump" in ms["down"] or ms["pstate"] == "jump"), ms)
        fing.up(2)
        time.sleep(0.8)
        fing.up(1)

        # ---------------------------------------------------------------- 走到战斗
        ex, ey = center(".tc-e")
        # 靠近调查点按 E：先走到篝火（x=172,y=188）附近，再点 E
        t0 = time.time()
        while time.time() - t0 < 20:
            s = state()
            if s["px"] is not None and abs(s["px"] - 172) < 14 and abs(s["py"] - 188) < 12:
                break
            dx, dy = 172 - s["px"], 188 - s["py"]
            fing.up(1) if 1 in fing.pts else None
            tx = pc[0] + (R * 0.7 if dx > 8 else -R * 0.7 if dx < -8 else 0)
            ty = pc[1] + (R * 0.7 if dy > 6 else -R * 0.7 if dy < -6 else 0)
            if tx == pc[0] and ty == pc[1]:
                break
            fing.down(1, tx, ty)
            time.sleep(0.25)
        fing.up(1) if 1 in fing.pts else None
        time.sleep(0.3)
        near = ev("() => !!G.world.near")
        check("走到篝火边：E 钮开始跳动提醒", near and has(".tc-e", "pulse"), near)
        shot("05_near_hotspot")
        fing.tap(ex, ey)
        time.sleep(0.5)
        check("点 E 开始调查（出现对话、按钮收起）", state()["ctx"] == "story", state())
        for _ in range(6):
            fing.tap(cx, cy)
            time.sleep(0.4)
            if state()["ctx"] != "story":
                break
        check("点屏幕把调查对话推进完", state()["ctx"] == "explore", state()["ctx"])

        # 一路往右走进战斗
        t0 = time.time()
        while time.time() - t0 < 60:
            s = state()
            if s["combat"]:
                break
            if s["ctx"] == "story":
                if 1 in fing.pts:
                    fing.up(1)
                fing.tap(cx, cy)
                time.sleep(0.35)
                continue
            if 1 not in fing.pts:
                fing.down(1, pc[0] + R * 0.7, pc[1])
            time.sleep(0.2)
        if 1 in fing.pts:
            fing.up(1)
        time.sleep(0.4)
        s = state()
        check("走过 x=486 触发第一场战斗", s["combat"], s)
        # 等战斗真的开始（对话说完）
        t0 = time.time()
        while time.time() - t0 < 30:
            s = state()
            if s["combat"] and s["ctx"] == "combat" and s["free"]:
                break
            if s["ctx"] == "story":
                fing.tap(cx, cy)
            time.sleep(0.35)
        s = state()
        check("战斗中：方向盘 + J + K + L 全亮", s["ctx"] == "combat" and all(not has(x, "tc-off") and not has(x, "tc-dim") for x in ("#tc-pad", ".tc-j", ".tc-k", ".tc-l")), s)
        shot("06_combat")

        # ---------------------------------------------------------------- 战斗里的 J / K / L
        jx, jy = center(".tc-j")
        kx, ky = center(".tc-k")
        lx, ly = center(".tc-l")
        fing.tap(jx, jy)
        time.sleep(0.08)
        check("点 J：角色出招", state()["pstate"] == "attack", state()["pstate"])
        time.sleep(0.9)
        fing.tap(kx, ky)
        time.sleep(0.1)
        check("点 K：角色起跳", state()["pstate"] == "jump", state()["pstate"])
        time.sleep(1.0)
        fing.down(3, lx, ly)
        time.sleep(0.2)
        st = state()
        check("按住 L：角色举刀防御", st["pstate"] == "guard" and "guard" in st["down"], st)
        shot("07_guard")
        fing.up(3)
        time.sleep(0.2)
        check("松开 L：不再防御", state()["pstate"] != "guard", state()["pstate"])
        # 连点 J 三下（三连击）：不要丢点击
        n = 0
        for _ in range(3):
            fing.tap(jx, jy, hold=0.04)
            time.sleep(0.12)
            n += 1
        time.sleep(0.2)
        check("连点 J 不丢点击（状态是出招中或刚出完）", state()["pstate"] in ("attack", "idle", "walk"), state()["pstate"])

        # ---------------------------------------------------------------- 暂停菜单：点 ⏸ → 点“操作说明” → 点菜单外回到游戏
        px_, py_ = center("#tc-pause")
        fing.tap(px_, py_)
        time.sleep(0.4)
        check("点暂停钮打开暂停菜单", state()["menu"] and state()["ctx"] == "menu", state())
        shot("08_pause")
        # 菜单中间那几行：暂停菜单居中，第 2 项“操作说明”
        r = ev("() => { const L = G.ui.menuLayout(G.ui.menu); return [L.x, L.oy, L.w]; }")
        fing.tap(*game_to_css(192, r[1] + 18 * 1 + 7))
        time.sleep(0.4)
        check("点“操作说明”打开说明页（触屏版文字）", ev("() => G.ui.menu && G.ui.menu.title") == "操作说明" and "方向盘" in ev("() => G.ui.menu.options.join('')"), ev("() => G.ui.menu && G.ui.menu.options"))
        shot("09_help")
        fing.tap(*game_to_css(10, 10))       # 点菜单外
        time.sleep(0.4)
        check("点说明页外面回到暂停菜单", ev("() => G.ui.menu && G.ui.menu.title") == "暂停", ev("() => G.ui.menu && G.ui.menu.title"))
        # 暂停菜单里的“按键大小”：中 → 大 → 小 → 中，按钮跟着变
        bsz = lambda: ev("() => parseFloat(getComputedStyle(document.getElementById('tc')).getPropertyValue('--b'))")
        names, sizes = [], []
        for _ in range(3):
            row = ev("() => { const L = G.ui.menuLayout(G.ui.menu); return L.oy; }")
            fing.tap(*game_to_css(192, row + 18 * 2 + 7))
            time.sleep(0.35)
            names.append(ev("() => G.ui.menu && G.ui.menu.options[2]"))
            sizes.append(bsz())
        check("暂停菜单有“按键大小”，点一下换一档（大 → 小 → 中）", names == ["按键大小：大", "按键大小：小", "按键大小：中"] and sizes[0] > sizes[2] > sizes[1], [names, sizes])
        check("换完大小还停在暂停菜单里", ev("() => G.ui.menu && G.ui.menu.title") == "暂停")
        fing.tap(*game_to_css(10, 10))
        time.sleep(0.4)
        check("再点菜单外 = 继续游戏", not state()["menu"], state())

        # ---------------------------------------------------------------- 竖屏：请横过来
        page.set_viewport_size({"width": H, "height": W})
        time.sleep(0.6)
        check("竖屏：出现“请横过来”提示、游戏停住", has("body", "tc-portrait") and ev("() => !!G.suspended"))
        shot("10_portrait")
        t1 = ev("() => G.time")
        time.sleep(0.5)
        check("竖屏时游戏时间不走", abs(ev("() => G.time") - t1) < 0.01)
        page.set_viewport_size({"width": W, "height": H})
        time.sleep(0.6)
        check("转回横屏：提示消失、游戏继续", (not has("body", "tc-portrait")) and not ev("() => !!G.suspended"))

        # ---------------------------------------------------------------- 电脑键盘：接上键盘就收起按键，再碰屏幕又出来
        page.keyboard.press("ArrowRight")
        time.sleep(0.2)
        check("按实体键盘：屏幕按键收起", not ev("() => G.touch.on"))
        fing.tap(*game_to_css(192, 100))
        time.sleep(0.3)
        check("再碰屏幕：屏幕按键回来", ev("() => G.touch.on"))

        # ---------------------------------------------------------------- iPhone（只是把浏览器标识换成 iPhone，走一遍 iOS 的声音点播流程；真机上的声音没法在这里测）
        print("== 冒充 iPhone：声音点播")
        ctx2 = b.new_context(viewport={"width": 852, "height": 393}, device_scale_factor=3, is_mobile=True, has_touch=True, user_agent=IOS_UA)
        p2 = ctx2.new_page()
        p2.on("pageerror", lambda e: errors.append("ios pageerror: " + str(e)))
        p2.on("console", lambda m: errors.append("ios console." + m.type + ": " + m.text) if m.type == "error" else None)
        f2 = Fingers(ctx2, p2)
        p2.goto(url)
        p2.wait_for_function("window.G && G.scene && G.scene.name === 'title'", timeout=60000)
        time.sleep(0.5)
        check("识别成 iOS", p2.evaluate("() => G.touch.ios"))
        r = p2.evaluate("() => { const r = G.screen.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }")
        f2.tap(r[0] + 192 * r[2] / 384, r[1] + 170 * r[3] / 216)       # 手指抬起一次
        time.sleep(1.2)
        n_pool, n_sfx = p2.evaluate("() => [Object.keys(G.audio.pools).length, Object.keys(G.D.audio.sfx).length]")
        check("第一次触摸后，音效全部预先点播（每个音效一个元素）", n_pool == n_sfx, f"{n_pool}/{n_sfx}")
        check("音乐换成点过的元素，标题曲接着放", p2.evaluate("() => G.audio.music.toString().includes('slots') && !!G.audio.el && !G.audio.el.paused"))
        p2.evaluate("() => G.audio.music('battle', 0.2)")
        time.sleep(0.6)
        p2.evaluate("() => G.audio.music('comedy', 0.2)")
        time.sleep(0.6)
        check("换曲：新的在放、旧的停了", p2.evaluate("() => G.audio.el.src.endsWith('comedy.mp3') && !G.audio.el.paused"))
        ctx2.close()
        b.close()

    print()
    if errors:
        print("页面报错 / console.error：")
        for e in errors[:20]:
            print("  ", e)
    print(f"截图在 {shots}")
    ok = not fails and not errors
    print("全部通过" if ok else f"有 {len(fails)} 项 FAIL，{len(errors)} 条页面报错")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
