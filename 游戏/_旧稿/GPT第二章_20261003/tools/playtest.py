"""自动试玩：用无头 Chromium 从标题一路玩到第一章结束，推进对话、走位、打架，截关键画面，收集控制台报错。

用法：python playtest.py [prologue|ch1|ch2|all] [--lose]      截图存到 tools/_playtest/
注意：Playwright 自带的 Chromium 不支持 H.264，开场视频会直接跳过（真浏览器里正常播放）。
"""
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(HERE)
OUT = os.path.join(HERE, "_playtest")
os.makedirs(OUT, exist_ok=True)
URL = "file:///" + os.path.join(GAME, "index.html").replace("\\", "/")

STATE_JS = """() => {
  const w = G.world, u = G.ui, p = w.player, st = w.stage;
  return {
    stage: st ? st.id : null, px: p ? Math.round(p.x) : null, py: p ? Math.round(p.y) : null, pstate: p ? p.state : null,
    hp: p ? p.hp : null, busy: G.S.busy, free: w.free, combat: w.combat,
    dlg: u.dlg ? (u.dlg.name + '：' + u.dlg.pages.map(x => x.join('')).join('')) : null,
    narr: u.narr ? u.narr.lines.join('') : null, choice: u.choiceBox ? u.choiceBox.options : null,
    menu: u.menu ? u.menu.title : null, chapter: !!u.chapter, video: !!(G.scene && G.scene.t !== undefined && !G.scene.update.toString().includes('openPause') && G.scene !== G.worldScene && G.scene.draw.toString().includes('跳过')),
    enemies: w.enemies().map(e => [Math.round(e.x), Math.round(e.y), e.hp, e.state]),
    near: w.near ? w.near.label : null, boss: u.boss ? u.boss.name : null, flags: G.flags, fade: G.fadeAlpha,
    scene: G.scene === G.worldScene ? 'world' : (G.scene && G.scene.draw.toString().includes('第一章　完') ? 'end' : (G.scene && G.scene.draw.toString().includes('游 戏 版') ? 'title' : 'other')),
  };
}"""


class Tester:
    def __init__(self, page, lose=False):
        self.page = page
        self.lose = lose
        self.shots = 0
        self.log = []
        self.lines = []
        self.lost_once = False
        self.boss_shot = False

    def st(self):
        return self.page.evaluate(STATE_JS)

    def shot(self, name):
        self.shots += 1
        p = os.path.join(OUT, f"{self.shots:02d}_{name}.png")
        self.page.screenshot(path=p)
        self.log.append(p)

    def key(self, k, hold=0.05):
        self.page.keyboard.down(k)
        time.sleep(hold)
        self.page.keyboard.up(k)

    def advance(self, timeout=60, stop=None):
        """把对话 / 旁白 / 选项 / 篇章卡一路按掉，直到玩家能动（或 stop() 为真）。"""
        t0 = time.time()
        while time.time() - t0 < timeout:
            s = self.st()
            if stop and stop(s):
                return s
            if s["dlg"] and (not self.lines or self.lines[-1] != s["dlg"]):
                self.lines.append(s["dlg"])
            if s["menu"]:
                self.key("Enter")
            elif s["dlg"] or s["narr"] or s["choice"]:
                self.key("Enter")
                time.sleep(0.12)
            elif s["scene"] == "world" and s["free"] and not s["busy"] and s["stage"] and not stop:
                return s
            elif s["scene"] == "end":
                return s
            time.sleep(0.08)
        return self.st()

    def walk_to(self, x, y=None, timeout=20):
        t0 = time.time()
        while time.time() - t0 < timeout:
            s = self.st()
            if not s["free"] or s["busy"]:
                return s
            dx = x - s["px"]
            dy = 0 if y is None else y - s["py"]
            if abs(dx) <= 3 and abs(dy) <= 3:
                for k in ("ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"):
                    self.page.keyboard.up(k)
                return s
            self.page.keyboard.down("ArrowRight") if dx > 3 else self.page.keyboard.up("ArrowRight")
            self.page.keyboard.down("ArrowLeft") if dx < -3 else self.page.keyboard.up("ArrowLeft")
            self.page.keyboard.down("ArrowDown") if dy > 3 else self.page.keyboard.up("ArrowDown")
            self.page.keyboard.down("ArrowUp") if dy < -3 else self.page.keyboard.up("ArrowUp")
            time.sleep(0.05)
        for k in ("ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"):
            self.page.keyboard.up(k)
        return self.st()

    def use(self, x, y):
        self.walk_to(x, y)
        for _ in range(4):
            time.sleep(0.2)
            self.key("Enter")
            time.sleep(0.3)
            s = self.st()
            if s["busy"] or s["dlg"]:
                break
        return self.advance()

    def use_near(self, label=None, timeout=20):
        t0 = time.time()
        while time.time() - t0 < timeout:
            s = self.st()
            if s["near"] and (label is None or s["near"] == label):
                self.key("Enter")
                return self.advance(timeout=60)
            if not s["free"] or s["busy"]:
                self.key("Enter")
                time.sleep(0.12)
            else:
                time.sleep(0.05)
        return self.st()

    def fight(self, timeout=150, shot_name=None):
        """简单的自动战斗：贴近最近的敌人、对齐纵深、连按 J。"""
        t0 = time.time()
        shot_done = False
        while time.time() - t0 < timeout:
            s = self.st()
            if s["menu"]:
                self.shot("lost_menu")
                self.lost_once = True
                self.key("Enter")
                time.sleep(1.0)
                continue
            if s["dlg"] or s["narr"]:
                self.key("Enter")
                time.sleep(0.12)
                continue
            if not s["combat"]:
                if s["free"] and not s["busy"]:
                    return s
                if s["busy"] and not s["enemies"] and time.time() - t0 > 3:
                    return s
                time.sleep(0.1)
                continue
            if self.lose and not self.lost_once:
                time.sleep(0.2)
                continue
            if s.get("boss") and not self.boss_shot:
                self.boss_shot = True
                self.shot("boss")
            es = s["enemies"]
            if not es:
                time.sleep(0.1)
                continue
            ex, ey = min(es, key=lambda e: abs(e[0] - s["px"]) + abs(e[1] - s["py"]))[:2]
            dx, dy = ex - s["px"], ey - s["py"]
            for k in ("ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"):
                self.page.keyboard.up(k)
            if abs(dy) > 3:
                self.key("ArrowDown" if dy > 0 else "ArrowUp", 0.06)
            if abs(dx) > 26:
                self.key("ArrowRight" if dx > 0 else "ArrowLeft", 0.08)
            else:
                if (dx > 0) != (True):
                    pass
                self.key("ArrowRight" if dx > 0 else "ArrowLeft", 0.02)
                for _ in range(3):
                    self.key("j", 0.03)
                    time.sleep(0.07)
            if shot_name and not shot_done and time.time() - t0 > 4:
                self.shot(shot_name)
                shot_done = True
            time.sleep(0.03)
        return self.st()


def run(which="all", lose=False):
    errors = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        page = b.new_page(viewport={"width": 1152, "height": 648})
        page.on("console", lambda m: errors.append(f"[{m.type}] {m.text}") if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: errors.append(f"[pageerror] {e}"))
        page.goto(URL)
        page.wait_for_function("() => window.G && G.scene && G.f12", timeout=30000)
        time.sleep(1.0)
        T = Tester(page, lose)
        T.shot("title")
        if which in ("all", "prologue"):
            T.key("Enter")
            time.sleep(1.0)
            # 视频（无头浏览器里会因为编码不支持直接跳过）→ 篇章卡 → 营地开场对话
            time.sleep(3.0)
            T.shot("video")
            T.advance(stop=lambda s: s["stage"] == "war_pro" and s["dlg"])
            T.shot("prologue_dialog")
            s = T.advance()
            T.shot("prologue_free")
            T.use(206, 176)          # 桂
            T.use(306, 190)          # 坂本
            T.use(172, 190)          # 篝火
            T.shot("prologue_talk_done")
            T.walk_to(500, 180)
            T.advance(stop=lambda s: s["combat"])
            T.fight(shot_name="battle1")
            T.advance()
            T.walk_to(930, 180)
            T.advance(stop=lambda s: s["combat"])
            T.fight(shot_name="battle2_boss", timeout=200)
            T.advance(timeout=40, stop=lambda s: s["stage"] == "office_ch1" or s["scene"] == "end")
            T.shot("after_prologue")
        if which == "ch1":
            T.key("ArrowDown")
            time.sleep(0.2)
            T.key("Enter")
            time.sleep(1.0)
        if which in ("all", "ch1"):
            T.advance(timeout=60, stop=lambda s: s["stage"] == "office_ch1" and s["dlg"])
            T.shot("office_wake")
            T.advance()
            T.shot("office_free")
            T.use(108, 172)          # 沙发（字条）
            T.use(36, 176)           # 电视
            T.use(142, 168)          # 「糖分」→ 私房钱
            T.shot("office_money")
            T.walk_to(338, 168)
            T.key("Enter")
            time.sleep(0.4)
            T.advance(timeout=60, stop=lambda s: s["choice"])
            T.shot("office_choice")
            T.key("ArrowDown"); T.key("ArrowDown")
            T.advance(timeout=60)
            T.shot("street_landed")
            T.use(340, 172)          # 登势
            T.use(156, 186)          # 路人（洞爷湖）
            T.shot("street_talk")
            T.walk_to(470, 176)
            T.advance(stop=lambda s: s["combat"])
            T.fight(shot_name="street_fight", timeout=200)
            T.advance(timeout=60)
            time.sleep(2.2)
            T.shot("ending")
        if which == "ch2":
            # 标题第三项：第二章；进入后先与服务员交互，再走到右侧触发战斗。
            T.key("ArrowDown"); time.sleep(0.25); T.key("ArrowDown"); time.sleep(0.25); T.key("Enter")
            T.advance(timeout=60, stop=lambda s: s["stage"] == "restaurant_ch2")
            if T.st().get("stage") != "restaurant_ch2":
                T.log.append("ch2_start_failed:" + json.dumps(T.st(), ensure_ascii=False))
                return
            T.advance(); T.walk_to(178, 150); T.use_near("服务员新八")
            T.walk_to(300, 160); T.advance(stop=lambda s: s["combat"])
            T.fight(timeout=180, shot_name="ch2_restaurant_boss")
            T.advance(timeout=60)
            T.walk_to(550, 176); T.advance(timeout=30)
            T.walk_to(300, 176); T.use_near("借条")
            # 借条先选错，再选对。
            T.key("ArrowDown"); T.key("Enter"); T.advance(timeout=20)
            T.use_near("借条"); T.fight(timeout=200, shot_name="ch2_dojo_boss")
            T.advance(timeout=60); T.use_near("阿妙"); T.key("Enter"); T.advance(timeout=60)
            T.shot("ch2_ending")
        print(json.dumps({"errors": errors[:40], "shots": T.log, "dialog_lines": len(T.lines)}, ensure_ascii=False, indent=1))
        with open(os.path.join(OUT, "dialog_seen.txt"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(T.lines))
        b.close()


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "all"
    run(which, lose="--lose" in sys.argv)
