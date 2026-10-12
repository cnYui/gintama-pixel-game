# 子代理：char-qa（阶段：Char QA）

- 原文件：`agent-a2e7241aa49f7f13e.jsonl`（5.2 MB，636 行）
- 时间（UTC+9）：09-25 21:35:05 → 09-25 22:02:45

## 任务书（主会话派给它的第一条消息）

You are a member of a team producing a ~5-minute pixel-art animated video retelling the anime 银魂 (Gintama) in story order.
  Project root (Windows path): C:\Users\yui\AppData\Roaming\Claude\scratch-workspaces\955dbf55-b1fe-49c6-ac59-972ff2e7f6b1\fd33c576-e552-48b9-b406-8dc43e0afecb\scratch-2026-09-25-336c0d\gintama_pixel
  In the Bash tool (Git Bash) ALWAYS start each command with: cd "/c/Users/yui/AppData/Roaming/Claude/scratch-workspaces/955dbf55-b1fe-49c6-ac59-972ff2e7f6b1/fd33c576-e552-48b9-b406-8dc43e0afecb/scratch-2026-09-25-336c0d/gintama_pixel" && ...   (python 3.12 with PIL/numpy/scipy and ffmpeg are on PATH). With Read/Write/Edit tools use the Windows absolute path.
  FIRST read CONTRACT.md in full — it defines the APIs, style guide, file ownership, character ids, SFX/music names and the full storyboard.
  Obey file ownership strictly: many other agents are editing OTHER files in the same tree at the same time. Never modify files you don't own; work around problems locally and report them. Put temporary/preview outputs under build/ in a subfolder named after your task (build/preview/ is fine for the provided tools).
  Render code must be deterministic (use engine.core.rng, never the global random state).
  Visual verification is mandatory: render PNGs and LOOK at them with the Read tool; iterate until the result is genuinely good, not just error-free.
  Your final message is consumed programmatically by the lead: keep it short (limit given below) — what you made, exact names/APIs, and any problems with shared files.
  
  TASK: character consistency QA across ALL characters. You may edit any chars/*.py EXCEPT chars/rig.py, chars/__init__.py and chars/gintoki.py. Scene agents are using these characters RIGHT NOW, so NEVER rename ids, remove poses/expressions or change call signatures — only improve art/palettes/proportions and fix bugs (keep each edit atomic: write the whole file in one Write).
  1. "python charsheet.py --all" → view build/preview/lineup.png; "python charsheet.py <id>" for every id → view each sheet; zoom into suspicious ones at 5x with your own script under build/charqa/.
  2. Check: consistent scale (adults ≈34 px, kids ≈26 px, housen/sadaharu big), 1px INK outlines everywhere, consistent palette/shading/light direction, recognisability and canon accuracy (hair colours, signature features per CONTRACT §5), every standard pose renders without errors or broken/detached limbs, all required extra poses/expressions exist and look right, name/color/voice sensible, name-tag colours readable.
  3. Fix issues directly; re-verify.
  Final answer limit: 150 words.

## 最终报告（它的最后一条回复）

No broken poses were found in any of the 42 characters: every standard pose and required extra renders without errors, all required poses and expressions exist, and scale and outlines are consistent. I fixed nine files. `s09` still renders correctly with Housen's new kneel.

**Fixes (no ids, poses or signatures changed):**
- `sadaharu.py`, `housen.py`: rotation in `fly`/`hit` and Housen's long umbrella in `thrust` no longer clip. Sprites are padded and the returned anchor is (64,90) for Sadaharu and (66,98) for Housen.
- `housen.py`: `kneel` now actually kneels (it used to look like a wide stance). Name colour is lighter.
- `kagura.py`: `sit`/`kneel` now show legs, and the umbrella on her back no longer pokes through the floor.
- `shiroyasha.py`: headband tails were redrawn; they read as a "7".
- `kamui.py`: the `open_eyes` brow is no longer a flat bar across the face.
- `takasugi.py`, `takasugi_kid.py`: darker purple hair. `sakamoto.py`: darker, closer to canon.
- `utsuro.py`, `naraku.py`: lighter name colours so the name on the name card is readable.

**For lead (`rig.py`):** `lie`/`sleep` don't sit on the floor. Characters float up to 6 px (seita, tama, townsfolk) or sink up to 6 px (housen, shiroyasha). The rotated sprite needs to be moved so its lowest pixel lands on the floor line.

My QA scripts are in `build/charqa/`.
