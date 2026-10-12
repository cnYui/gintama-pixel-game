# 子代理：backgrounds（阶段：Assets）

- 原文件：`agent-a4f6f1fb8f4fb6056.jsonl`（6.0 MB，328 行）
- 时间（UTC+9）：09-25 20:51:32 → 09-25 21:35:05

## 任务书（主会话派给它的第一条消息）

You are a member of a team producing a ~5-minute pixel-art animated video retelling the anime 银魂 (Gintama) in story order.
  Project root (Windows path): C:\Users\yui\AppData\Roaming\Claude\scratch-workspaces\955dbf55-b1fe-49c6-ac59-972ff2e7f6b1\fd33c576-e552-48b9-b406-8dc43e0afecb\scratch-2026-09-25-336c0d\gintama_pixel
  In the Bash tool (Git Bash) ALWAYS start each command with: cd "/c/Users/yui/AppData/Roaming/Claude/scratch-workspaces/955dbf55-b1fe-49c6-ac59-972ff2e7f6b1/fd33c576-e552-48b9-b406-8dc43e0afecb/scratch-2026-09-25-336c0d/gintama_pixel" && ...   (python 3.12 with PIL/numpy/scipy and ffmpeg are on PATH). With Read/Write/Edit tools use the Windows absolute path.
  FIRST read CONTRACT.md in full — it defines the APIs, style guide, file ownership, character ids, SFX/music names and the full storyboard.
  Obey file ownership strictly: many other agents are editing OTHER files in the same tree at the same time. Never modify files you don't own; work around problems locally and report them. Put temporary/preview outputs under build/ in a subfolder named after your task (build/preview/ is fine for the provided tools).
  Render code must be deterministic (use engine.core.rng, never the global random state).
  Visual verification is mandatory: render PNGs and LOOK at them with the Read tool; iterate until the result is genuinely good, not just error-free.
  Your final message is consumed programmatically by the lead: keep it short (limit given below) — what you made, exact names/APIs, and any problems with shared files.
  
  TASK: build the shared background library in bg/ (you own bg/*.py). ~10 scene agents will import it right after you finish, so make it beautiful and document it well.
  Create:
  1. bg/common.py — sky(img, tod, t) for tod in 'day','dusk','night','dawn','storm' (banded + dithered gradients, sun/moon, stars at night); clouds(img, t, cam_x=0, tod='day', seed=0); big_moon(img, x, y, r); far_mountains(img, cam_x, tod, y); river(img, y, h, t, tod) (animated water shimmer); bridge(img, cam_x, y, tod) (wooden arched Japanese bridge with railings); cherry_tree(img, x, y, t, scale=1) (swaying, petals); lantern(img, x, y, t, color=red) (paper chochin, swaying, glow halo at night); a few ground helpers (stone street, wooden floor, tatami).
  2. bg/kabukicho.py — street(img, cam_x, t, tod='day'): long horizontally scrolling Kabukicho street (wraps seamlessly, world width STREET_W) with: the Otose snack-bar building (ground floor noren/sign 「登势」 snack) with the Yorozuya on the second floor (big sign 「万事屋银酱」, balcony, outside wooden staircase), other shops with noren curtains, signboards, lanterns, power poles/wires, amanto-era touches (neon signs, a hovering car/ship far away). Constants: YOROZUYA_X (world x of that building's centre), FLOOR_Y = 160 (feet line on the street). Also yorozuya_front(img, t, tod) — a framed establishing shot of the building front, with BALCONY_Y (feet line on the balcony, for group poses) and constants for where the window and door are.
  3. bg/yorozuya.py — office(img, t, tod='day'): Yorozuya office interior: back wall with the framed calligraphy 「糖分」, window showing the sky for tod, Gintoki's desk + chair centre-back, two sofas facing each other with a low table in front (strawberry-milk carton on it), TV, stack of Jump magazines, sliding door (shoji) at the right; constants FLOOR_Y, SOFA_L_X, SOFA_R_X, SOFA_SEAT_Y, DESK_X, DOOR_X, WINDOW_BOX. Optional office_fg(img, t) foreground layer (e.g. table front) to draw over characters sitting behind it.
  4. bg/edo.py — skyline(img, cam_x, t, tod='day', ships=True): Edo panorama — layers of traditional tiled rooftops, Edo castle, and the enormous 'Terminal' spaceport tower (tall futuristic tower in the centre) with alien spaceships drifting; ship(img, x, y, kind, t, scale=1) for reuse (≥3 kinds: small saucer, long cruiser, giant mothership); fleet(img, t, density=1.0, cam_x=0) — an ominous alien armada darkening the sky (final arc).
  Quality bar: detailed yet readable at 384x216, clear depth (≥3 parallax layers, atmospheric perspective: far = bluer/lighter/less contrast), ambient animation (lanterns swaying, flags, smoke, windows flicker, ships drifting). Backgrounds a bit darker/less saturated than characters so characters pop. Use the INK outline sparingly on big shapes.
  Performance: pre-render static layers once (module-level cache keyed by params) then paste with offsets per frame — each call must cost < 8 ms (measure it).
  Verify: write build/bg/demo.py rendering every function for every tod (and several cam_x) into PNGs, plus a few characters drawn at FLOOR_Y with chars.draw_char to check scale (a character is ~34 px tall; doors should be ~42 px tall). LOOK at them and iterate for beauty (≥2 passes).
  Final answer limit: 200 words — list every public function/constant with its signature.

## 最终报告（它的最后一条回复）

The background library is finished in `bg/`, with the full API in each module's docstring. Every call measures 0.1–4 ms in isolation, under the 8 ms limit. Demo sheets are at `build/bg/demo_<tod>.png` (`python build/bg/demo.py`); I checked them for all 5 tods and several cam_x.

`tod` is `'day'|'dusk'|'night'|'dawn'|'storm'` (`C.TODS`). `C.indoor(tod)` gives warm lamp-lit grades for rooms.

**bg.common**
- `sky(img,tod,t,horizon=150,body=True)`, `storm_flash(t)`, `clouds(img,t,cam_x=0,tod,seed=0)`, `big_moon(img,x,y,r=28)`, `far_mountains(img,cam_x,tod,y)`
- `river(img,y,h,t,tod,cam_x=0,reflect_x=None)`, `bridge(img,cam_x,y,tod,style='wood'|'red')`, `bridge_deck_y(sx,cam_x,y)`
- `cherry_tree(img,x,y,t,scale=1,tod)`, `lantern(img,x,y,t,color=RED,tod='day',glow=None,size=1,text=None)`: pass `tod`, or it won't glow
- Ground/walls: `stone_street`, `wood_floor`, `tatami`, `dirt_ground` (all `(img,y,cam_x,tod)`), `room_wall(img,cam_x,tod,y0,y1,style)`

**bg.kabukicho** (cam_x = world x of the screen's left edge)
- `street(img,cam_x,t,tod,dy=0,wet=None)`, `street_fg`, `yorozuya_front(img,t,tod)`, `yorozuya_front_fg`
- Constants: `STREET_W`, `FLOOR_Y=160`, `YOROZUYA_X/_WINDOW/_DOOR/_UPDOOR`, `STREET_BALCONY_Y=84`, `stairs_y(wx)`, `BALCONY_Y=120`, `FRONT_FLOOR_Y=196`, `FRONT_WINDOW/_DOOR`

**bg.yorozuya**
- `office(img,t,tod,door=0..1)`, `office_fg`, `desk_fg`
- Constants: `SOFA_L_X/_R_X`, `SOFA_SEAT_Y=153`, `DESK_X`, `DESK_SEAT_Y`, `DOOR_X`, `DOOR_FEET_Y`, `WINDOW_BOX`

**bg.edo**
- `skyline(img,cam_x,t,tod,ships=True,armada=0,near=True)`, `terminal`, `ship(img,x,y,kind,t,scale=1,facing=1)` (6 kinds), `fleet(img,t,density,cam_x)`, `roof_walk(img,cam_x,y,t,tod)`

Shared-file problem: `chars/ito.py` fails to import (AssertionError in hijikata `mk_head`, row `r12` is 19 chars, expected 18).
