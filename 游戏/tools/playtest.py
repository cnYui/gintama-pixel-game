"""自动试玩：用无头 Chromium 从标题一路玩下去，推进对话、走位、打架，截关键画面，收集控制台报错。

用法：python playtest.py [prologue|ch1|ch2|all] [--lose]      截图存到 tools/_playtest/
  all      从序章一路打到第二章结束（章末画面）
  ch1/ch2  从标题的「选择章节」进入那一章
  --lose   第一场战斗故意输一次，测「再来一次」
  --until 章节    只打到这一章为止（prologue / ch1 / ch2 … ch14），分段录屏用
  --record 目录   录屏：对话按正常速度看、全程录下画面 + 声音（另出 BGM、音效两条单独的音轨），见 tools/recorder.js
注意：Playwright 自带的 Chromium 不支持 H.264，开场视频会用 webm（或直接跳过）。
"""
import base64
import re
import functools
import http.server
import json
import os
import socketserver
import sys
import threading
import time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(HERE)
OUT = os.environ.get("PLAYTEST_OUT") or os.path.join(HERE, "_playtest")
os.makedirs(OUT, exist_ok=True)
URL = "file:///" + os.path.join(GAME, "index.html").replace("\\", "/")

STATE_JS = """() => {
  const w = G.world, u = G.ui, p = w.player, st = w.stage;
  return {
    stage: st ? st.id : null, px: p ? Math.round(p.x) : null, py: p ? Math.round(p.y) : null, pstate: p ? p.state : null,
    hp: p ? p.hp : null, busy: G.S.busy, free: w.free, combat: w.combat,
    dlg: u.dlg ? (u.dlg.name + '：' + u.dlg.pages.map(x => x.join('')).join('')) : null,
    narr: u.narr ? u.narr.lines.join('') : null, choice: u.choiceBox ? u.choiceBox.options : null,
    notice: u.notice ? (u.notice.title + u.notice.text) : null, insert: !!u.insert,
    menu: u.menu ? u.menu.title : null, chapter: !!u.chapter,
    enemies: w.enemies().map(e => [Math.round(e.x), Math.round(e.y), e.hp, e.state]),
    allies: w.allies().map(a => [a.name, a.hp, a.state, Math.round(a.x), Math.round(a.y), a.visible, a.alpha]),
    near: w.near ? w.near.label : null, boss: u.boss ? u.boss.name : null, flags: G.flags, fade: G.fadeAlpha,
    scene: G.scene ? (G.scene.name || 'other') : null, hole: !!(st && st.state.hole),
    qte: u.qte ? { type: u.qte.type, m: u.qte.m, zone: u.qte.zone, t: u.qte.t, notes: u.qte.notes, state: u.qte.state, result: u.qte.result } : null,
    runner: w.runner && p ? w.runner.obs.filter(o => !o.done).map(o => [Math.round(o.x - p.x), Math.round(o.y - p.y), o.tall || 16]) : null,
    pz: p ? Math.round(p.z) : 0, pfacing: p ? p.facing : 1,
    timer: u.timer ? Math.round(u.timer.until - w.fightT) : null,
    shots: w.shots.map(s => [Math.round(s.x - (p ? p.x : 0)), Math.round(s.y - (p ? p.y : 0)), s.dir]),
    waitKey: !!u.waitKey,
    npcs: st ? st.actors.filter(a => a.talk && a.visible && !a.remove).map(a => [a.label || a.name, Math.round(a.x), Math.round(a.y)]) : [],
    dbg: G.dbg ? G.dbg.shot : null,
    ddone: u.dlg ? (u.dlg.shown >= u.dlg.pages[u.dlg.page].join('').length) : (u.narr ? u.narr.shown >= u.narr.lines.join('').length : true),
    dpage: u.dlg ? u.dlg.page : -1,
    dlen: u.dlg ? u.dlg.pages[u.dlg.page].join('').length : (u.narr ? u.narr.lines.join('').length : 0),
    nauto: u.narr ? !!u.narr.auto : false,
    x0: st ? st.x0 : null, x1: st ? st.x1 : null,
    ctitle: (G.lastChapter != null && G.CHAPTERS && G.CHAPTERS[G.lastChapter]) ? G.CHAPTERS[G.lastChapter].title : null,
  };
}"""


def chapter_of(stage):
    """地图 id → 第几章：war_pro = 序章（0）；其余都以 _chN（可带 b）结尾。认不出来返回 None。"""
    if not stage:
        return None
    if stage == "war_pro":
        return 0
    m = re.search(r"_ch(\d+)b?$", stage)
    return int(m.group(1)) if m else None


class Tester:
    def __init__(self, page, lose=False, watch=False):
        self.page = page
        self.lose = lose
        self.watch = watch          # 录屏模式：对话等字打完、留出读的时间再翻页；不截图
        self.tmul = 4 if watch else 1
        self._wkey, self._wdone, self._seen = None, None, {}
        self.shots = 0
        self.log = []
        self.lines = []
        self.lost_once = False
        self.boss_shot = False
        self.taken = set()
        self.trace = []
        self.marks = []             # 录屏的时间点 [秒, 名字, 类型]：title / chapter / video / end
        self._card, self._scene, self._combat = False, None, False
        self._idle_t, self._talked, self._exploring = None, set(), False
        self.chap = None            # 当前路线是第几章：地图换成别的章节，这一步立刻结束（不然会一路空等到下一章）
        self.t_start = time.time()

    def st(self):
        s = self.page.evaluate(STATE_JS)
        # 记下每次换地图的时间（看哪一段卡得久）
        if s.get("stage") != getattr(self, "_last_stage", "?"):
            self._last_stage = s.get("stage")
            self.trace.append("%6.1fs %s" % (time.time() - self.t_start, s.get("stage")))
        # 篇章卡出现 = 新的一章；过场动画、全剧终画面也记一笔
        if s.get("chapter") and not self._card and s.get("ctitle"):
            if not any(m[1] == s["ctitle"] for m in self.marks):
                self.mark(s["ctitle"], "chapter")
        if s.get("scene") != self._scene and s.get("scene") in ("video", "end"):
            self.mark("过场动画" if s["scene"] == "video" else "全剧终画面", s["scene"])
        # 战斗开始 / 结束（剪打斗片段用）
        if bool(s.get("combat")) != self._combat:
            self._combat = bool(s.get("combat"))
            self.mark(("战斗：" + s["boss"]) if (self._combat and s.get("boss")) else ("战斗" if self._combat else "战斗结束"),
                      "fight" if self._combat else "fight_end")
        self._card, self._scene = bool(s.get("chapter")), s.get("scene")
        return s

    def chap_changed(self, s):
        c = chapter_of(s.get("stage"))
        return self.chap is not None and c is not None and c != self.chap

    def mark(self, label, kind):
        self.marks.append([round(time.time() - self.t_start, 2), label, kind])

    def wait(self, secs):
        """等一会儿，期间照常读状态（篇章卡、过场动画的时间点才记得准）。"""
        t0 = time.time()
        while time.time() - t0 < secs:
            self.st()
            time.sleep(0.1)

    def shot(self, name):
        if self.watch:
            return
        self.shots += 1
        p = os.path.join(OUT, f"{self.shots:02d}_{name}.png")
        self.page.screenshot(path=p)
        self.log.append(p)

    def shot_once(self, name):
        if name not in self.taken:
            self.taken.add(name)
            self.shot(name)

    def dbg_shot(self, s):
        """剧情里用 G.dbg = { shot: 名字 } 标出来的画面（没有台词的镜头），每个名字截一次。"""
        if s.get("dbg"):
            self.shot_once(s["dbg"])

    def can_skip(self, s):
        """录屏模式：这一页字打完以后，按字数留出读的时间才按（会自己消失的旁白不按）。平时直接按。"""
        if not self.watch:
            return True
        if s["narr"] and s.get("nauto"):
            return False
        key = (s["dlg"], s["narr"], s["notice"], s.get("dpage"))
        now = time.time()
        if key != self._wkey:
            self._wkey, self._wdone = key, None
        if not s.get("ddone", True):
            return False
        if self._wdone is None:
            self._wdone = now
        need = 2.4 if s["notice"] else min(3.6, 1.0 + 0.08 * (s.get("dlen") or 10))
        return now - self._wdone >= need

    def lingered(self, what, val, secs):
        """录屏模式：选项、菜单、按一下继续这类，先停一会儿让人看清再按。"""
        if not self.watch:
            return True
        k = (what, json.dumps(val, ensure_ascii=False))
        t = self._seen.setdefault(k, time.time())
        if time.time() - t >= secs:
            self._seen.pop(k, None)
            return True
        return False

    def idle(self, secs):
        """原地等着（录屏时别用 time.sleep 干等：要一直和页面打交道，录下来的数据块才会及时写盘）。"""
        t0 = time.time()
        while time.time() - t0 < secs:
            self.page.evaluate("1")
            time.sleep(0.2)

    def key(self, k, hold=0.05):
        self.page.keyboard.down(k)
        time.sleep(hold)
        self.page.keyboard.up(k)

    def release(self):
        for k in ("ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"):
            self.page.keyboard.up(k)

    def special(self, s):
        """按键小游戏和自动卷轴：自动按。处理了返回 True。"""
        if s.get("waitKey") and not s.get("dlg") and not s.get("qte"):
            if not self.lingered("waitKey", s.get("stage"), 1.2):
                return True
            time.sleep(0.3)
            self.key("Enter", 0.03)
            time.sleep(0.2)
            return True
        q = s.get("qte")
        if q and q.get("result") is None:
            if q["type"] == "mash":
                self.key("Enter", 0.02)
            elif q["type"] == "timing":
                z, m = q["zone"], q.get("m") or 0
                if z[0] + 0.02 <= m <= z[1] - 0.02:
                    self.key("Enter", 0.02)
                    time.sleep(0.25)
            elif q["type"] == "rhythm":
                for nt, stt in zip(q["notes"], q["state"]):
                    if stt == 0 and abs(q["t"] - nt) < 0.07:
                        self.key("Enter", 0.02)
                        break
            return True
        if s.get("runner") is not None:
            for dx, dy, tall in s["runner"]:
                if 6 < dx < 36 and abs(dy) < 10 and s.get("pz", 0) == 0:
                    self.key("k", 0.04)
                    break
            return True
        return False

    def advance(self, timeout=90, stop=None, choose=None, shots=None):
        """把对话 / 旁白 / 选项 / 系统框一路按掉，直到玩家能动（或 stop(s) 为真）。
        choose(options) -> 选第几个（按几下 ↓）；shots = {台词里的字: 截图名}。"""
        t0 = time.time()
        timeout *= self.tmul
        while time.time() - t0 < timeout:
            s = self.st()
            self.dbg_shot(s)
            if stop and stop(s):
                return s
            if self.chap_changed(s):
                return s
            if self.special(s):
                time.sleep(0.02)
                continue
            if s["dlg"] and (not self.lines or self.lines[-1] != s["dlg"]):
                self.lines.append(s["dlg"])
                for k, name in (shots or {}).items():
                    if k in s["dlg"]:
                        time.sleep(0.5)
                        self.shot_once(name)
            if s["menu"]:
                if self.lingered("menu", s["menu"], 1.5):
                    self.key("Enter")
            elif s["choice"]:
                if self.lingered("choice", s["choice"], 1.8):
                    n = choose(s["choice"]) if choose else 0
                    for _ in range(n):
                        self.key("ArrowDown")
                        time.sleep(0.25 if self.watch else 0.08)
                    self.key("Enter")
                    time.sleep(0.2)
            elif s["dlg"] or s["narr"] or s["notice"]:
                if self.can_skip(s):
                    self.key("Enter")
                    time.sleep(0.12)
            elif s["scene"] == "world" and s["free"] and not s["busy"] and s["stage"] and not stop:
                return s
            elif s["scene"] == "end":
                return s
            # 玩家闲着、游戏在等人动、路线又还在等一个不会自己来的事件：像人一样去聊天、往右走（录屏时不会空等几分钟）
            idle = (stop is not None and not self._exploring and s["scene"] == "world" and s["free"] and not s["busy"] and s["stage"]
                    and not s["combat"] and s["runner"] is None and not s["insert"]
                    and not (s["dlg"] or s["narr"] or s["notice"] or s["choice"] or s["menu"] or s["qte"] or s["chapter"]))
            if not idle:
                self._idle_t = None
            elif self._idle_t is None:
                self._idle_t = time.time()
            elif time.time() - self._idle_t > (7 if self.watch else 5):
                self._idle_t = None
                self.explore(s)
            time.sleep(0.08)
        self.log.append("advance_timeout:" + json.dumps(self.st(), ensure_ascii=False)[:1600])
        return self.st()

    def explore(self, s):
        """去和这张地图里还没聊过的 NPC 说话（近的先聊）；聊完了就往右走一段，走到头折回来。"""
        self._exploring = True
        try:
            stage = s["stage"]
            todo = sorted([t for t in s["npcs"] if (stage, t[0]) not in self._talked], key=lambda t: abs(t[1] - s["px"]))
            if todo:
                name = todo[0][0]
                self._talked.add((stage, name))
                self.log.append("explore_talk:%s@%s" % (name, stage))
                self.use_npc(name)
            else:
                x0, x1 = s.get("x0") or 0, s.get("x1") or 400
                tx = s["px"] + 150
                if tx > x1 - 14:
                    tx = x0 + 14
                self.log.append("explore_walk:%d@%s" % (tx, stage))
                self.walk_to(tx, None, timeout=12)
        finally:
            self._exploring = False

    def walk_to(self, x, y=None, timeout=25):
        t0 = time.time()
        timeout *= self.tmul
        while time.time() - t0 < timeout:
            s = self.st()
            if not s["free"] or s["busy"] or self.chap_changed(s):
                self.release()
                return s
            dx = x - s["px"]
            dy = 0 if y is None else y - s["py"]
            if abs(dx) <= 3 and abs(dy) <= 3:
                self.release()
                return s
            self.page.keyboard.down("ArrowRight") if dx > 3 else self.page.keyboard.up("ArrowRight")
            self.page.keyboard.down("ArrowLeft") if dx < -3 else self.page.keyboard.up("ArrowLeft")
            self.page.keyboard.down("ArrowDown") if dy > 3 else self.page.keyboard.up("ArrowDown")
            self.page.keyboard.down("ArrowUp") if dy < -3 else self.page.keyboard.up("ArrowUp")
            time.sleep(0.04)
        self.release()
        return self.st()

    def use(self, x, y, label=None, **kw):
        """走到 (x, y)，等头顶出现这个名字的提示再按 Enter，然后把剧情按完。"""
        self.walk_to(x, y)
        for _ in range(30):
            s = self.st()
            if s["busy"] or s["dlg"]:
                break
            if s["near"] and (label is None or s["near"] == label):
                self.key("Enter")
                time.sleep(0.3)
                continue
            time.sleep(0.1)
        return self.advance(**kw)

    def fight(self, timeout=200, shot_name=None, shots=None, choose=None):
        """简单的自动战斗：贴近最近的敌人、对齐纵深、连按 J。战斗结束后的剧情也一并按掉。"""
        t0 = time.time()
        timeout *= self.tmul
        shot_done = False
        while time.time() - t0 < timeout:
            s = self.st()
            self.dbg_shot(s)
            if s["scene"] == "end" or self.chap_changed(s):
                return s
            if s["menu"]:
                if not self.lingered("menu", s["menu"], 1.5):
                    time.sleep(0.1)
                    continue
                self.shot("lost_menu")
                self.lost_once = True
                self.key("Enter")
                time.sleep(1.0)
                continue
            if s["choice"]:
                return s
            if self.special(s):
                time.sleep(0.02)
                continue
            if s["dlg"] or s["narr"] or s["notice"]:
                if s["dlg"] and (not self.lines or self.lines[-1] != s["dlg"]):
                    self.lines.append(s["dlg"])
                    for k, name in (shots or {}).items():
                        if k in s["dlg"]:
                            time.sleep(0.5)
                            self.shot_once(name)
                if self.can_skip(s):
                    self.key("Enter")
                    time.sleep(0.12)
                else:
                    time.sleep(0.08)
                continue
            if not s["combat"]:
                if s["free"] and not s["busy"]:
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
            if s.get("timer") is not None and es and len(es) == 1 and es[0][2] >= 900:
                # 撑时间的那种（打不动的敌人在扫射）：面朝它按住防御，偶尔上下挪
                ex = es[0][0]
                want = 1 if ex > s["px"] else -1
                if s.get("pfacing") != want:
                    self.page.keyboard.up("l")
                    self.key("ArrowRight" if want > 0 else "ArrowLeft", 0.03)
                self.page.keyboard.down("l")
                time.sleep(0.15)
                continue
            self.page.keyboard.up("l")
            if not es:
                time.sleep(0.1)
                continue
            ex, ey = min(es, key=lambda e: abs(e[0] - s["px"]) + abs(e[1] - s["py"]))[:2]
            dx, dy = ex - s["px"], ey - s["py"]
            self.release()
            if abs(dy) > 3:
                self.key("ArrowDown" if dy > 0 else "ArrowUp", 0.06)
            if abs(dx) > 26:
                self.key("ArrowRight" if dx > 0 else "ArrowLeft", 0.08)
            else:
                self.key("ArrowRight" if dx > 0 else "ArrowLeft", 0.02)
                for _ in range(3):
                    self.key("j", 0.03)
                    time.sleep(0.07)
            if shot_name and not shot_done and time.time() - t0 > 4:
                self.shot(shot_name)
                shot_done = True
            time.sleep(0.03)
        self.log.append("fight_timeout:" + json.dumps(self.st(), ensure_ascii=False)[:1600])
        return self.st()

    def use_npc(self, label, **kw):
        """走到这个名字的 NPC 旁边搭话（位置从游戏里读）。提示不是它（旁边别人更近、或者它还在走）就重新读位置、贴近一点再试。"""
        def where():
            for name, x, y in self.st()["npcs"]:
                if name == label:
                    return x, y
            return None
        if not where():
            self.log.append("npc_missing:" + label)
            return self.st()
        for dx in (-18, -8, 8, -18):
            pos = where()
            if not pos:
                break
            x, y = pos
            self.walk_to(x + dx, y + (2 if dx == -18 else 0))
            for _ in range(15):
                s = self.st()
                if s["busy"] or s["dlg"]:
                    return self.advance(**kw)
                if s["near"] == label:
                    self.key("Enter")
                    time.sleep(0.3)
                    return self.advance(**kw)
                time.sleep(0.1)
        self.log.append("npc_not_near:" + label)
        return self.advance(**kw)

    def pick_chapter(self, idx):
        """标题：选择章节 → 第 idx 章。"""
        self.key("ArrowDown")
        time.sleep(0.2)
        self.key("Enter")
        time.sleep(0.4)
        for _ in range(idx):
            self.key("ArrowDown")
            time.sleep(0.15)
        self.shot_once("title_chapters")
        self.key("Enter")
        time.sleep(1.0)


def route_prologue(T):
    T.key("Enter")
    T.mark("序章　白夜叉", "chapter")
    # 视频（无头浏览器里会用 webm 或直接跳过）→ 篇章卡 → 营地开场对话
    T.wait(4.0)
    T.shot("video")
    T.advance(stop=lambda s: s["stage"] == "war_pro" and s["dlg"])
    T.shot("prologue_dialog")
    T.advance()
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


def route_ch1(T):
    T.advance(timeout=60, stop=lambda s: s["stage"] == "office_ch1" and (s["dlg"] or (s["free"] and not s["busy"])))
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
    T.advance(timeout=60, choose=lambda o: 2)
    T.shot("street_landed")
    T.use(340, 172)          # 登势
    T.use(156, 186)          # 路人（洞爷湖）
    T.shot("street_talk")
    T.walk_to(470, 176)
    T.advance(stop=lambda s: s["combat"])
    T.fight(shot_name="street_fight", timeout=200)
    T.advance(timeout=60, stop=lambda s: s["stage"] == "restaurant_ch2" or s["scene"] == "end")
    time.sleep(0.5)
    T.shot("ch1_ending")


def route_ch2(T):
    shots = {
        "人生的意义": "ch2_parfait", "阿～": "ch2_crow", "糖尿病": "ch2_after_eyes", "你被开除了": "ch2_fired",
        "工资里扣": "ch2_stone", "你给我等一下": "ch2_tsukkomi", "我叫志村新八": "ch2_street",
        "钱准备好了吗": "ch2_gate", "承蒙你们照顾": "ch2_otae", "这里就是志村道场": "ch2_dojo",
        "黑洞": "ch2_egg_insert", "好吃到说不出话": "ch2_fainted", "找回我的武士道": "ch2_vow", "晚饭还有很多": "ch2_join",
    }
    picked = {"iou": 0}

    def choose(opts):
        if "利息每日三成" in opts:          # 借条：先答错一次，再答对
            picked["iou"] += 1
            T.shot_once("ch2_iou_choice")
            return 0 if picked["iou"] == 1 else opts.index("利息每日三成")
        if "不吃" in opts:                  # 煎蛋：选「不吃」（阿妙的那条分支）
            T.shot_once("ch2_egg_choice")
            return opts.index("不吃")
        return 0

    T.advance(timeout=60, stop=lambda s: s["stage"] == "restaurant_ch2" and s["free"] and not s["busy"], shots=shots)
    T.shot("ch2_restaurant")
    T.use(162, 174, "服务员", shots=shots)          # 点单
    T.use(304, 166, "空凳子", shots=shots, stop=lambda s: s["insert"] or s["combat"])
    if T.st()["insert"]:
        time.sleep(0.5)
        T.shot("ch2_eyes")
    T.advance(timeout=60, stop=lambda s: s["combat"], shots=shots)
    T.fight(timeout=200, shot_name="ch2_restaurant_fight", shots=shots)
    s = T.st()
    if s["stage"] == "street_ch2":
        T.shot("ch2_street_free")
        T.use(356, 176, "登势", shots=shots)
        T.walk_to(1100, 180, timeout=40)
    T.advance(timeout=60, stop=lambda s: s["stage"] == "dojo_gate_ch2" and s["free"] and not s["busy"], shots=shots)
    T.shot("ch2_gate_free")
    T.use(292, 182, "讨债头目", shots=shots)        # 还没看借条
    T.use(164, 172, "借条", shots=shots)
    T.use(292, 182, "讨债头目", shots=shots, choose=choose, stop=lambda s: s["combat"])
    T.fight(timeout=240, shot_name="ch2_gate_fight", shots=shots)
    T.advance(timeout=60, stop=lambda s: s["stage"] == "dojo_ch2" and s["free"] and not s["busy"], shots=shots)
    T.shot("ch2_dojo_free")
    T.use(299, 170, "挂轴", shots=shots)
    T.use(150, 170, "坐垫", shots=shots, choose=choose,
          stop=lambda s: s["notice"] is not None or s["scene"] == "end")
    if T.st()["notice"]:
        time.sleep(0.6)
        T.shot("ch2_notice")
    # 停在章末画面，或者下一章开始的时候
    T.advance(timeout=60, shots=shots, stop=lambda s: s["scene"] == "end" or s["stage"] not in (None, "dojo_ch2"))
    time.sleep(1.0)
    T.shot("ch2_end")


def route_ch3(T):
    shots = {"你撞到人了": "ch3_kagura", "少废话": "ch3_umbrella", "找到了": "ch3_yakuza", "再来一碗": "ch3_bowls",
             "伙食费": "ch3_wallet", "第二天": "ch3_morning", "怪兽": "ch3_sadaharu", "湿": "ch3_after_bite",
             "大胃王和一条": "ch3_balcony", "集结阿鲁": "ch3_assemble"}
    T.advance(timeout=60, stop=lambda s: s["stage"] == "street_night_ch3" and s["runner"] is not None, shots=shots)
    time.sleep(2.0)
    T.shot("ch3_runner")
    T.advance(timeout=90, stop=lambda s: s["combat"], shots=shots)
    T.fight(timeout=120, shot_name="ch3_dodge", shots=shots)          # 撑过神乐的扫射 → 剧情 → 黑道战
    s = T.st()
    if s["combat"] or (s["busy"] and not s["free"]):
        T.advance(timeout=60, stop=lambda s: s["combat"], shots=shots)
        T.fight(timeout=200, shot_name="ch3_yakuza_fight", shots=shots)
    T.advance(timeout=90, stop=lambda s: s["stage"] == "office_night_ch3" and s["free"] and not s["busy"], shots=shots)
    T.shot("ch3_office_free")
    T.use(318, 172, "雨伞", shots=shots)
    T.use(192, 180, "神乐", shots=shots)
    T.use(96, 172, "沙发", shots=shots, stop=lambda s: s["stage"] == "street_ch3" and s["free"] and not s["busy"])
    T.advance(timeout=60, stop=lambda s: s["stage"] == "street_ch3" and s["free"] and not s["busy"], shots=shots)
    T.shot("ch3_street_morning")
    T.use(508, 182, "纸箱", shots=shots)
    T.advance(timeout=90, shots=shots)
    time.sleep(1.5)
    T.shot("ch3_end")


def route_ch5(T):
    shots = {"企鹅": "ch5_eliz", "好久不见": "ch5_katsura", "给我站住": "ch5_hijikata", "假发——": "ch5_okita_aim",
             "不是假发，是桂": "ch5_zura", "快跑": "ch5_run_sign", "天然卷交给我": "ch5_before_fight",
             "后会有期": "ch5_bomb", "圆圆的": "ch5_catch", "炸、炸弹": "ch5_bomb_zoom", "桂」字的烟花": "ch5_fireworks",
             "火星掉下去": "ch5_ember", "倒霉的都是我": "ch5_soot"}
    T.advance(timeout=60, stop=lambda s: s["stage"] == "street_dusk_ch5" and s["free"] and not s["busy"], shots=shots)
    T.shot("ch5_street")
    T.use(470, 174, "告示板", shots=shots)
    T.use(584, 180, "谜之生物", shots=shots, stop=lambda s: s["runner"] is not None)
    time.sleep(3.0)
    T.shot("ch5_roof")
    time.sleep(1.5)
    T.shot("ch5_roof_aim")
    T.advance(timeout=90, stop=lambda s: s["combat"], shots=shots)
    T.fight(timeout=120, shot_name="ch5_fight", shots=shots)
    T.advance(timeout=150, shots=shots, stop=lambda s: s["scene"] == "end" or s["stage"] not in (None, "roofs_ch5", "street_dusk_ch5b", "fw_sky_ch5"))
    time.sleep(1.0)
    T.shot("ch5_end")


def route_ch4(T):
    shots = {"诚": "ch4_flag", "趁副长不在": "ch4_yamazaki", "暗处看着我": "ch4_otae", "阿妙小姐今天也好美": "ch4_kondo",
             "跟踪狂给我去死吧": "ch4_dark", "煎蛋改天": "ch4_after_punch", "提出决斗": "ch4_duel", "丢人现眼": "ch4_hq_arrive",
             "监察的山崎": "ch4_hq", "蛋黄酱，就是正义": "ch4_mayo", "梦到土方先生": "ch4_okita_wake", "去死吧。": "ch4_bazooka",
             "总悟你这混蛋": "ch4_afro", "蛋黄酱和火药": "ch4_courtyard", "喂！总悟": "ch4_laser"}
    T.advance(timeout=60, stop=lambda s: s["stage"] == "street_ch4" and s["free"] and not s["busy"], shots=shots)
    T.shot("ch4_street")
    T.use(468, 178, "阿妙", shots=shots)
    bx = {"b1": 384, "b2": 600, "b3": 768}[T.st()["flags"].get("kondoAt", "b1")]
    T.use(bx - 14, 176, "草丛", shots=shots, stop=lambda s: s["combat"])
    T.fight(timeout=200, shot_name="ch4_duel_fight", shots=shots)
    T.advance(timeout=60, stop=lambda s: s["stage"] == "hq_ch4" and s["free"] and not s["busy"], shots=shots)
    T.use(92, 180, "山崎", shots=shots)
    T.use(192, 168, "进屯所", shots=shots)
    T.advance(timeout=30, stop=lambda s: s["stage"] == "canteen_ch4" and s["free"] and not s["busy"], shots=shots)
    T.shot("ch4_canteen")
    T.use(140, 168, "土方", shots=shots, choose=lambda o: 1)
    T.use(410, 168, "睡觉的人", shots=shots, stop=lambda s: s["combat"])
    T.fight(timeout=120, shot_name="ch4_bazooka_fight", shots=shots)
    T.advance(timeout=90, shots=shots, stop=lambda s: s["scene"] == "end" or s["stage"] not in (None, "canteen_ch4", "courtyard_ch4"))
    time.sleep(1.0)
    T.shot("ch4_end")


def route_ch6(T):
    shots = {"住在纸箱里": "ch6_madao", "纸箱……其实还挺暖和": "ch6_madao_cry", "手气一定不错": "ch6_pachinko", "动过手脚": "ch6_lose",
             "今天是星期几": "ch6_calendar", "二十五号": "ch6_monday", "男人的圣经": "ch6_jump", "跟着通酱": "ch6_otsu",
             "跟着节拍": "ch6_shinpachi", "通酱～！！": "ch6_love", "最棒的零食": "ch6_kagura", "就是正义阿鲁": "ch6_sukonbu",
             "今天也好美": "ch6_kondo", "…………": "ch6_stab"}
    T.advance(timeout=200, shots=shots, stop=lambda s: s["scene"] == "end" or s["stage"] not in (None, "daily_ch6"))
    time.sleep(1.0)
    T.shot("ch6_end")


def route_ch7(T):
    shots = {"夜里的江户": "ch7_bridge", "桂先生……": "ch7_sign", "就是这座桥": "ch7_investigate", "这是假发的头发": "ch7_hair",
             "还没吃饱呢": "ch7_nizo", "红樱会喜欢": "ch7_storm", "吃人的刀": "ch7_kneel", "刀断了": "ch7_broken",
             "腐朽的世界": "ch7_takasugi", "长发呢": "ch7_katsura", "背后交给你了": "ch7_back", "不是假发，是桂": "ch7_zura",
             "你我就是敌人": "ch7_enemy"}
    T.advance(timeout=90, stop=lambda s: s["stage"] == "bridge_night_ch7" and s["free"] and not s["busy"], shots=shots)
    T.shot("ch7_bridge_free")
    T.use(210, 156, "伊丽莎白", shots=shots)
    T.use(150, 156, "桥板", shots=shots)
    T.walk_to(360, 154, timeout=20)
    T.advance(timeout=90, stop=lambda s: s["combat"], shots=shots)
    T.fight(timeout=240, shot_name="ch7_nizo_fight", shots=shots)
    T.advance(timeout=120, stop=lambda s: s["combat"], shots=shots)
    T.fight(timeout=240, shot_name="ch7_deck_fight", shots=shots)
    T.advance(timeout=90, shots=shots, stop=lambda s: s["scene"] == "end" or s["stage"] not in (None, "deck_f_ch7", "deck_g_ch7"))
    time.sleep(1.0)
    T.shot("ch7_end")


def route_ch8(T):
    shots = {"妖刀·村麻纱": "ch8_curse", "炒面面包": "ch8_toshi", "变成这副样子": "ch8_hq", "限量版": "ch8_figure",
             "该退场了": "ch8_ito", "这委托，万事屋接下了": "ch8_car", "跳上车顶": "ch8_jump", "通酱的手办": "ch8_figure_broken",
             "土方十四郎！！": "ch8_hijikata", "从来都不认同我": "ch8_duel", "……谢谢": "ch8_thanks"}
    T.advance(timeout=90, stop=lambda s: s["stage"] == "hq_room_ch8" and s["free"] and not s["busy"], shots=shots)
    T.shot("ch8_hq_free")
    T.use(208, 176, "托西", shots=shots)
    T.use(284, 178, "山崎", shots=shots)
    T.use(104, 180, "近藤", shots=shots, stop=lambda s: s["combat"])
    T.advance(timeout=120, stop=lambda s: s["combat"], shots=shots)
    T.fight(timeout=300, shot_name="ch8_roof_fight", shots=shots)
    T.advance(timeout=90, stop=lambda s: s["combat"], shots=shots)
    T.fight(timeout=240, shot_name="ch8_duel_fight", shots=shots)
    T.advance(timeout=90, shots=shots, stop=lambda s: s["scene"] == "end" or s["stage"] not in (None, "sunset_ch8"))
    time.sleep(1.0)
    T.shot("ch8_end")


def route_ch9(T):
    shots = {"铁做的天顶": "ch9_street", "我想见娘": "ch9_seita", "没有太阳": "ch9_tsukuyo", "被囚禁在高塔": "ch9_tower",
             "只对强者感兴趣": "ch9_kamui", "只属于我一人": "ch9_housen", "来砸锁的": "ch9_corridor", "该守护的东西": "ch9_street_hole",
             "控制天顶的机关室": "ch9_control", "开顶之序": "ch9_plate", "天顶在动": "ch9_lever", "现在属于所有人": "ch9_sun",
             "这么温暖的东西": "ch9_crumble", "你长这么大了": "ch9_reunion", "糖分": "ch9_sugar"}
    T.advance(timeout=90, stop=lambda s: s["stage"] == "yoshi_night_ch9" and s["free"] and not s["busy"], shots=shots)
    T.use_npc("晴太", shots=shots)
    T.use_npc("月咏", shots=shots, stop=lambda s: s["combat"])
    T.advance(timeout=120, stop=lambda s: s["combat"], shots=shots)
    T.fight(timeout=120, shot_name="ch9_corridor_fight", shots=shots)
    T.advance(timeout=120, stop=lambda s: s["stage"] == "control_ch9" and s["free"] and not s["busy"], shots=shots)
    T.shot("ch9_control_free")
    T.use(113, 170, "铭牌", shots=shots)
    T.use(44, 170, "左边的齿轮", shots=shots)
    T.use(262, 170, "大齿轮", shots=shots)
    T.use(196, 170, "拉杆", shots=shots, stop=lambda s: s["combat"])
    T.advance(timeout=120, stop=lambda s: s["combat"], shots=shots)
    T.fight(timeout=400, shot_name="ch9_sun_fight", shots=shots)
    T.advance(timeout=120, shots=shots, stop=lambda s: s["scene"] == "end" or s["stage"] not in (None, "yoshi_sun_ch9"))
    time.sleep(1.0)
    T.shot("ch9_end")


def route_ch10(T):
    shots = {"看店的委托": "ch10_barber", "和平时一样": "ch10_shogun", "哈啊": "ch10_yawn", "将军家的头发": "ch10_knot",
             "完美": "ch10_tape", "下次，也拜托你了": "ch10_slide", "最新流行的发型": "ch10_pass", "是奈落": "ch10_naraku",
             "今天是休息日": "ch10_katsura", "一直在看着我们": "ch10_after", "白夜叉。": "ch10_oboro", "和那时一样": "ch10_lock"}
    T.advance(timeout=150, stop=lambda s: s["stage"] == "pass_ch10" and s["free"] and not s["busy"], shots=shots, choose=lambda o: 0)
    T.shot("ch10_pass_free")
    T.walk_to(760, 180, timeout=30)
    T.advance(timeout=90, stop=lambda s: s["combat"], shots=shots)
    T.fight(timeout=300, shot_name="ch10_naraku_fight", shots=shots)
    T.advance(timeout=120, stop=lambda s: s["combat"], shots=shots)
    T.fight(timeout=300, shot_name="ch10_oboro_fight", shots=shots)
    T.advance(timeout=120, shots=shots, stop=lambda s: s["scene"] == "end" or s["stage"] not in (None, "duel_ch10"))
    time.sleep(1.0)
    T.shot("ch10_end")


def route_ch11(T):
    shots = {"死人饭团": "ch11_battlefield", "这把剑，是用来斩断": "ch11_sword", "今天一定要赢你": "ch11_takasugi",
             "明天我要睡午觉": "ch11_spar_end", "学而时习之": "ch11_class", "上课睡觉可不行": "ch11_headbutt",
             "大家就拜托你了": "ch11_fire", "白夜叉」": "ch11_joui", "好天气啊": "ch11_ridge", "谢谢你。": "ch11_cliff",
             "住手": "ch11_stop", "……老师。": "ch11_present"}
    T.advance(timeout=120, stop=lambda s: s["stage"] == "yard_ch11" and s["free"] and not s["busy"], shots=shots)
    T.shot("ch11_yard")
    T.use_npc("小桂", shots=shots)
    T.use_npc("小高杉", shots=shots, stop=lambda s: s["combat"])
    T.fight(timeout=120, shot_name="ch11_spar", shots=shots)
    T.advance(timeout=150, stop=lambda s: s["combat"], shots=shots)
    T.fight(timeout=240, shot_name="ch11_joui_fight", shots=shots)
    T.advance(timeout=150, shots=shots, stop=lambda s: s["scene"] == "end" or s["stage"] not in (None, "joui_ch11", "ridge_ch11", "cliff_ch11", "present_ch11"))
    time.sleep(1.0)
    T.shot("ch11_end")


def route_ch12(T):
    shots = {"还在追我吗": "ch12_rakuyo", "够了！": "ch12_umibozu", "别盯着爸爸的头": "ch12_bald", "带回家阿鲁": "ch12_promise",
             "……哥哥。": "ch12_farewell", "黎明时分离开了江户": "ch12_dock", "我们会回来的": "ch12_deck", "路上小心": "ch12_otae"}
    T.advance(timeout=90, stop=lambda s: s["combat"], shots=shots)
    T.fight(timeout=300, shot_name="ch12_kamui_fight", shots=shots)
    T.advance(timeout=150, stop=lambda s: s["stage"] == "dock_ch12" and s["free"] and not s["busy"], shots=shots)
    T.shot("ch12_dock_free")
    for who in ("近藤", "土方", "冲田", "阿妙"):
        T.use_npc(who, shots=shots)
    T.advance(timeout=150, shots=shots, stop=lambda s: s["scene"] == "end" or s["stage"] not in (None, "dock_ch12", "deck_ch12", "harbour_ch12"))
    time.sleep(1.0)
    T.shot("ch12_end")


def route_ch13(T):
    shots = {"我即是虚": "ch13_utsuro", "真选组，参上": "ch13_ssg", "攘夷志士的危机": "ch13_joui", "顺便逮捕": "ch13_seg1_wide",
             "一个都别想走": "ch13_women", "可不能让外人欺负": "ch13_otose", "回纸箱里": "ch13_madao_after", "送货上门": "ch13_kaien",
             "全家出动": "ch13_yato", "万事屋，到齐了": "ch13_yorozuya", "别拖后腿": "ch13_back", "我不会死": "ch13_xslash",
             "交给你了": "ch13_pieta", "天，亮了": "ch13_dawn", "你们都长大了": "ch13_shouyou", "回家吧": "ch13_sunrise"}

    def choose(opts):
        return opts.index("神乐") if "神乐" in opts else 0        # 第三段换神乐来打（测换人）

    T.advance(timeout=90, stop=lambda s: s["stage"] == "roofs_ch13" and s["free"] and not s["busy"], shots=shots)
    T.shot("ch13_free")
    T.walk_to(340, 170, timeout=30)
    T.advance(timeout=90, stop=lambda s: s["combat"], shots=shots)
    T.fight(timeout=200, shot_name="ch13_seg1_fight", shots=shots)
    T.use_npc("桂", shots=shots)
    T.walk_to(820, 170, timeout=40)
    T.advance(timeout=90, stop=lambda s: s["combat"], shots=shots)
    T.fight(timeout=200, shot_name="ch13_seg2_fight", shots=shots)
    T.use_npc("纸箱", shots=shots)
    T.walk_to(1300, 170, timeout=40)
    T.advance(timeout=120, stop=lambda s: s["combat"], shots=shots, choose=choose)
    T.fight(timeout=200, shot_name="ch13_seg3_fight", shots=shots, choose=choose)
    T.use_npc("神乐", shots=shots)
    T.walk_to(1770, 170, timeout=40)
    T.advance(timeout=90, stop=lambda s: s["combat"], shots=shots)
    T.fight(timeout=600, shot_name="ch13_final_fight", shots=shots)          # 背靠背 → 虚两个阶段 → 结尾，一路打到底
    T.advance(timeout=150, shots=shots, stop=lambda s: s["scene"] == "end" or s["stage"] not in (None, "roofs_ch13"))
    time.sleep(1.0)
    T.shot("ch13_end")


def route_ch14(T):
    shots = {"今天也没有回来": "ch14_balcony", "两年前那一仗": "ch14_aunt", "我回来了": "ch14_home", "你到底跑哪去了": "ch14_tsukkomi_line",
             "两年的份": "ch14_kagura", "欢迎回来阿鲁": "ch14_welcome", "利滚利": "ch14_otose", "请稍等一下": "ch14_otae",
             "新学的烟花": "ch14_okita", "不是假发，是桂": "ch14_zura_line", "好久不见了啊": "ch14_sada", "才不会完呢！": "ch14_kick_line"}
    T.advance(timeout=90, stop=lambda s: s["stage"] == "street_ch14" and s["free"] and not s["busy"], shots=shots)
    T.shot("ch14_rain_free")
    T.use_npc("躲雨的大婶", shots=shots)
    # 往右走：水洼特写、「我回来了」都会打断走路（游戏忙的时候 walk_to 直接返回），一直走到打起来为止
    for _ in range(8):
        T.walk_to(320, 164, timeout=40)
        s = T.advance(timeout=60, shots=shots,
                      stop=lambda s: s["combat"] or s["stage"] != "street_ch14" or (s["free"] and not s["busy"]))
        if s["combat"] or s["stage"] != "street_ch14":
            break
    T.fight(timeout=200, shot_name="ch14_kagura_fight", shots=shots)
    T.advance(timeout=90, stop=lambda s: s["stage"] == "town_ch14" and s["free"] and not s["busy"], shots=shots)
    T.shot("ch14_town")
    for who in ("登势", "桂", "冲田", "阿妙"):
        T.use_npc(who, shots=shots)
        T.advance(timeout=60, stop=lambda s: s["stage"] == "town_ch14" and s["free"] and not s["busy"], shots=shots)
    T.walk_to(360, 166, timeout=40)
    T.advance(timeout=200, shots=shots, stop=lambda s: s["scene"] == "end")
    time.sleep(1.0)
    T.shot("ch14_end")


ROUTES = {"ch2": route_ch2, "ch3": route_ch3, "ch4": route_ch4, "ch5": route_ch5, "ch6": route_ch6, "ch7": route_ch7, "ch8": route_ch8, "ch9": route_ch9, "ch10": route_ch10, "ch11": route_ch11, "ch12": route_ch12, "ch13": route_ch13, "ch14": route_ch14}
ORDER = ["ch2", "ch3", "ch4", "ch5", "ch6", "ch7", "ch8", "ch9", "ch10", "ch11", "ch12", "ch13", "ch14"]


def run(which="all", lose=False, record=None, until=None):
    """record = 目录：录屏模式。用 http 打开游戏（file:// 下画布和音频算跨域，录不出来），384×216 原尺寸录画面，
    同时录 full.webm（画面 + 混好的声音）、bgm.webm（只有背景音乐和开场动画原声）、sfx.webm（只有音效）。"""
    errors = []
    url, srv, files = URL, None, {}
    if record:
        os.makedirs(record, exist_ok=True)

        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a):
                pass
        srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=GAME))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
        files = {k: open(os.path.join(record, f"{k}.webm"), "wb") for k in ("full", "bgm", "sfx")}
    with sync_playwright() as pw:
        b = pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        page = b.new_page(viewport={"width": 384, "height": 216} if record else {"width": 1152, "height": 648})
        page.on("console", lambda m: errors.append(f"[{m.type}] {m.text}") if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: errors.append(f"[pageerror] {e}"))
        if record:
            page.expose_function("__recSave", lambda k, b64: files[k].write(base64.b64decode(b64)))
        page.goto(url)
        page.wait_for_function("() => window.G && G.scene && G.f12", timeout=60000)
        time.sleep(1.0)
        T = Tester(page, lose, watch=bool(record))
        if record:
            page.add_script_tag(path=os.path.join(HERE, "recorder.js"))
            T.t_start, T.trace = time.time(), []      # 时间点从开录这一刻算
            T.mark("标题画面", "title")
            T.idle(6.0)                      # 标题画面停几秒
        T.shot("title")
        # 从哪一章开始，就一路打到最后一章（游戏本身也是这样接着往下走）
        if which in ("all", "prologue"):
            T.chap = 0
            route_prologue(T)
        if which == "ch1":
            T.pick_chapter(1)
        if which in ("all", "ch1") and until != "prologue":
            T.chap = 1
            route_ch1(T)
        start = ORDER.index(which) if which in ORDER else 0
        if which in ORDER:
            T.pick_chapter(2 + start)
        if which in ["all", "ch1"] + ORDER and until not in ("prologue", "ch1"):
            for key in ORDER[start:]:
                print("[route] %s start  t=%.0fs" % (key, time.time() - T.t_start), file=sys.stderr, flush=True)
                T.chap = int(key[2:])
                ROUTES[key](T)
                print("[route] %s done   t=%.0fs  until=%r" % (key, time.time() - T.t_start, until), file=sys.stderr, flush=True)
                if T.st()["scene"] == "end" or key == until:
                    break
        if record and until and until in ORDER and until != ORDER[-1]:
            # 分段录屏：等到下一章的篇章卡出现再停，这样两段正好能在篇章卡那一刻接起来
            T.advance(timeout=60, stop=lambda s: s["chapter"] or s["scene"] == "end")
            T.idle(0.3)
        elif record:
            T.idle(6.0)                      # 章末画面停一会儿
            page.evaluate("() => window.__recStop()")
            for _ in range(600):
                if page.evaluate("() => window.__recPending") == 0:
                    break
                time.sleep(0.2)
        result = {"errors": errors[:40], "shots": len(T.log), "notes": [x for x in T.log if not x.endswith(".png")],
                  "dialog_lines": len(T.lines), "trace": T.trace, "marks": T.marks, "final": T.st()}
        print(json.dumps(result, ensure_ascii=False, indent=1))
        if record:
            with open(os.path.join(record, "run.json"), "w", encoding="utf-8") as fh:
                json.dump(result, fh, ensure_ascii=False, indent=1)
        with open(os.path.join(record or OUT, "dialog_seen.txt"), "w", encoding="utf-8") as fh:
            fh.write(chr(10).join(T.lines))
        b.close()
    for f in files.values():
        f.close()
    if srv:
        srv.shutdown()


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "all"
    rec = sys.argv[sys.argv.index("--record") + 1] if "--record" in sys.argv else None
    until = sys.argv[sys.argv.index("--until") + 1] if "--until" in sys.argv else None
    run(which, lose="--lose" in sys.argv, record=rec, until=until)
