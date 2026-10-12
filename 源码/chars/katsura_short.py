"""桂小太郎（短发） — Katsura after the Benizakura arc: hair cut short at the neck.
Same outfit / poses as chars/katsura.py (bomb, bomb_throw, run_away...), weapon katana.
"""
from chars import register
from chars.rig import ChibiDef, POSES, pose_run, pose_idle
from chars.katsura import (HEADS as LONG_HEADS, HEAD_PAL, TORSO, TORSO_PAL, KATSURA_SHEATH,
                           pose_bomb, pose_bomb_throw)

# short cut: the side locks end at the jaw with a slightly ragged (sword-cut) edge


def _shorten(art):
    rows = art.split("\n")
    r15 = rows[15]
    rows[15] = "ohHh" + r15[4:14] + "hHho"
    rows[16] = ".oooooooooooooooo."
    return "\n".join(rows)


HEADS = {k: _shorten(v) for k, v in LONG_HEADS.items()}


def pose_run_away_s(pp, t, p, d):
    pose_run(pp, t, p, d)
    pp["lean"] = 3
    pp["expr"] = "determined"


KATSURA_SHORT = register(ChibiDef(
    id="katsura_short", name="桂", color=(58, 84, 160), voice=0.92,
    heads=HEADS, head_pal=HEAD_PAL,
    torso=TORSO, torso_pal=TORSO_PAL,
    neck=(7, 2), hip=(7, 9), shoulder_f=(10, 3), shoulder_b=(3, 3),
    arm_len=7, arm_w=2, sleeve_f=(240, 236, 222), sleeve_b=(186, 180, 160), sleeve_frac=0.7,
    hand=(255, 220, 190),
    leg_len=7, leg_w=3, leg_gap=4, pants=(48, 58, 100), shoes=(34, 30, 40),
    weapon="katana", weapon_len=17, sheathed=KATSURA_SHEATH,
    poses={"bomb": pose_bomb, "bomb_throw": pose_bomb_throw, "run_away": pose_run_away_s},
    desc="红樱篇后的桂：长发被人斩削断，改为短发。与银时背靠背迎战春雨。",
))
