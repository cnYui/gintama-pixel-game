"""电脑端真实操控验收：进第一章，推进对话到能自由走动，然后用 W A S D 真的走，看角色坐标变化；再用 Esc 开暂停菜单。
用法: URL=https://aaccx.pw/gintama/ python keyboard_play.py     （默认测公网）"""
import io, os, sys
from playwright.sync_api import sync_playwright
from PIL import Image

URL = os.environ.get('URL') or 'https://aaccx.pw/gintama/'
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_tmp'); os.makedirs(TMP, exist_ok=True)
POS = "() => { const p = G.world && G.world.player; return p ? { x: +p.x.toFixed(1), y: +p.y.toFixed(1), state: p.state } : null; }"
FREE = "() => !!(G.world && G.world.player && G.world.free && !G.ui.dlg && !G.ui.narr && !G.ui.menu && !G.ui.choiceBox && !G.ui.chapter && !G.ui.notice && G.scene && G.scene.name === 'world' && !G.world.combat)"
results = []
def check(name, ok, detail=''):
    results.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome', args=['--autoplay-policy=no-user-gesture-required'])
    ctx = b.new_context(viewport={'width': 1280, 'height': 720}); pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(URL, timeout=120000)
    pg.wait_for_function("() => window.G && G.scene && G.scene.name === 'title'", timeout=120000)
    check('进入时手机按键是隐藏的', pg.evaluate("() => getComputedStyle(document.getElementById('tc')).display") == 'none')
    pg.keyboard.press('ArrowDown'); pg.wait_for_timeout(200); pg.keyboard.press('Enter'); pg.wait_for_timeout(500)       # 选择章节
    pg.keyboard.press('ArrowDown'); pg.wait_for_timeout(200); pg.keyboard.press('Enter')                                   # 第一章
    n = 0
    for n in range(200):
        pg.wait_for_timeout(350)
        if pg.evaluate(FREE): break
        pg.keyboard.press('Enter')
    free = pg.evaluate(FREE)
    check('键盘推进对话 → 进入可以自由走动的状态', free, f'按了 {n} 次 Enter, stage={pg.evaluate("() => G.world.stage && G.world.stage.id")}')
    if free:
        Image.open(io.BytesIO(pg.screenshot())).convert('RGB').save(os.path.join(TMP, 'keyboard_play.png'))
        a = pg.evaluate(POS)
        pg.keyboard.down('d'); pg.wait_for_timeout(700); pg.keyboard.up('d'); pg.wait_for_timeout(150)
        b1 = pg.evaluate(POS)
        check('按住 D：角色向右走', b1['x'] > a['x'] + 5, f'x {a["x"]} → {b1["x"]}')
        pg.keyboard.down('a'); pg.wait_for_timeout(700); pg.keyboard.up('a'); pg.wait_for_timeout(150)
        c = pg.evaluate(POS)
        check('按住 A：角色向左走', c['x'] < b1['x'] - 5, f'x {b1["x"]} → {c["x"]}')
        pg.keyboard.down('w'); pg.wait_for_timeout(500); pg.keyboard.up('w'); pg.wait_for_timeout(150)
        d = pg.evaluate(POS)
        pg.keyboard.down('s'); pg.wait_for_timeout(500); pg.keyboard.up('s'); pg.wait_for_timeout(150)
        e = pg.evaluate(POS)
        check('按住 W / S：角色在纵深方向前后走', d['y'] != c['y'] and e['y'] != d['y'] and (d['y'] - c['y']) * (e['y'] - d['y']) < 0, f'y {c["y"]} → {d["y"]} → {e["y"]}')
        pg.keyboard.press('Escape'); pg.wait_for_timeout(500)
        menu = pg.evaluate("() => G.ui.menu ? G.ui.menu.title : null")
        check('Esc 打开暂停菜单（手机按键仍隐藏）', menu == '暂停' and pg.evaluate("() => getComputedStyle(document.getElementById('tc')).display") == 'none', str(menu))
        pg.keyboard.press('s'); pg.wait_for_timeout(150); pg.keyboard.press('Enter'); pg.wait_for_timeout(600)       # S 往下选"操作说明"
        help_open = pg.evaluate("() => G.ui.menu ? G.ui.menu.title : null")
        check('W / S + Enter 能在菜单里选择（打开"操作说明"）', help_open == '操作说明', str(help_open))
        info = pg.evaluate("() => { const m = G.ui.menu; if (!m) return null; return { keys: Object.keys(m), opts: m.opts || m.options || m.list || m.items || null, title: m.title }; }")
        print('   菜单对象:', info)
        Image.open(io.BytesIO(pg.screenshot())).convert('RGB').save(os.path.join(TMP, 'keyboard_help.png'))
        txt = ' | '.join(info['opts']) if info and info.get('opts') else ''
        check('操作说明是键盘版（不是手机版）', 'A S D' in txt.replace('W ', 'W') or 'W A S D' in txt, txt[:160])
    check('没有页面报错', not errs, str(errs[:2]))
    b.close()
print('总结:', '全部通过' if all(results) else f'有 {results.count(False)} 项失败 / 共 {len(results)} 项')
