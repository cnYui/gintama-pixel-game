"""Render a character sheet PNG for visual QA.

    python charsheet.py gintoki            -> build/preview/char_gintoki.png
    python charsheet.py gintoki kagura     -> several
    python charsheet.py --all              -> every registered character (lineup)

Row 1: expressions (heads x3). Row 2+: every pose at 4 time steps (x3).
"""
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, ".")
from chars import get_def, list_chars, render_sprite, portrait  # noqa: E402
from chars.rig import POSES  # noqa: E402
from engine.text import draw_text  # noqa: E402

EXPRS = ["normal", "blink", "talk", "angry", "shout", "shock", "happy", "sad", "cry", "hurt", "smug"]
ONE_SHOT = {"attack", "slash_up", "thrust", "hit", "point", "shock", "punch", "kick", "land"}
K = 3


def sheet(cid):
    d = get_def(cid)
    extra = list(getattr(d, 'poses', {}) or {})
    poses = list(POSES) + [p for p in extra if p not in POSES]
    cell = 64
    cols = 8
    rows = 2 + len(poses) // 2 + 1
    img = Image.new("RGB", (cols * cell, rows * cell + 20), (70, 90, 110))
    dr = ImageDraw.Draw(img)
    for x in range(0, img.width, 8):
        for y in range(20, img.height, 8):
            if (x // 8 + y // 8) % 2:
                dr.rectangle([x, y, x + 7, y + 7], fill=(78, 98, 118))
    draw_text(img, 2, 2, f"{cid} / {d.name}  poses={len(poses)}", (255, 255, 255))
    # expressions + portrait
    for i, e in enumerate(EXPRS[:cols]):
        try:
            h = d.head(e)
            img.paste(h, (i * cell + 4, 24), h)
            draw_text(img, i * cell + 4, 24 + h.height + 1, e, (255, 255, 200))
        except Exception as ex:
            draw_text(img, i * cell + 4, 24, "ERR", (255, 80, 80))
    y0 = 20 + cell
    for i, e in enumerate(EXPRS[cols:] + ["__portrait__"]):
        if e == "__portrait__":
            pt = portrait(cid, "normal")
            if pt is not None:
                img.paste(pt, (i * cell + 4, y0 + 2), pt)
            continue
        try:
            h = d.head(e)
            img.paste(h, (i * cell + 4, y0 + 4), h)
            draw_text(img, i * cell + 4, y0 + 4 + h.height + 1, e, (255, 255, 200))
        except Exception:
            pass
    # poses: each pose gets 4 frames in half a row
    y0 = 20 + cell * 2
    for n, pose in enumerate(poses):
        r, c = divmod(n, 2)
        for k in range(4):
            t = k * 0.13
            p = k / 3.0 if pose in ONE_SHOT else None
            try:
                spr, ax, ay = render_sprite(cid, pose, t=t, p=p)
                x = (c * 4 + k) * cell + cell // 2
                y = y0 + r * cell + cell - 6
                img.paste(spr, (x - ax, y - ay), spr)
            except Exception as ex:
                draw_text(img, (c * 4 + k) * cell + 2, y0 + r * cell + 20, "ERR", (255, 80, 80))
                print(pose, ex)
        draw_text(img, c * 4 * cell + 2, y0 + r * cell + 2, pose, (255, 255, 255), outline=(0, 0, 0))
    img = img.resize((img.width * K // 2, img.height * K // 2), Image.NEAREST)
    out = f"build/preview/char_{cid}.png"
    img.save(out)
    print(out)


def lineup():
    ids = list_chars()
    per = 12
    rows = (len(ids) + per - 1) // per
    img = Image.new("RGB", (per * 40, rows * 70), (90, 110, 130))
    for i, cid in enumerate(ids):
        r, c = divmod(i, per)
        try:
            spr, ax, ay = render_sprite(cid, "idle", t=0.0)
            img.paste(spr, (c * 40 + 20 - ax, r * 70 + 56 - ay), spr)
        except Exception as ex:
            print(cid, ex)
        draw_text(img, c * 40 + 2, r * 70 + 58, get_def(cid).name[:3], (255, 255, 255), outline=(0, 0, 0))
    img = img.resize((img.width * 3, img.height * 3), Image.NEAREST)
    img.save("build/preview/lineup.png")
    print("build/preview/lineup.png")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args == ["--all"]:
        lineup()
    else:
        for a in args:
            sheet(a)
