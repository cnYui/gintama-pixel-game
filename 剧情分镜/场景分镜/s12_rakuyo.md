# s12 洛阳决战·离别

- 时长：19.0 s（成片里 258.7–277.7 s）
- 音乐：0s → battle、9.9s → sad（音量 0.55）
- 出场角色（代码里引用到的角色 id）：hijikata（土方）、kagura（神乐）、kamui（神威）、kondo（近藤）、okita（冲田）、otae（阿妙）、umibozu（星海坊主）
- 背景（bg 模块里被调用的函数）：common：add_sprite, bayer, cherry_tree, clouds, glow_sprite, grade_rgba, river, sky, stone_street, vgradient, wood_floor；edo：skyline
- 淡入 / 淡出：0.3 / 0.3 s

## 故事分镜（CONTRACT.md 第 8 节，写作时的设计意图）

**s12 洛阳决战·离别 (18 s)** `[(0,"battle"),(~9,"sad")]` chapter_card 「洛阳决战篇」

Rain on planet Rakuyo: Kagura vs Kamui umbrella clash (shockwaves), Umibozu drops in
「够了！」 name_card 星海坊主 「最强的宇宙猎人｜神乐的秃头老爸」. Kagura: 「我一定会把哥哥
带回家阿鲁！」 Kamui smiles and leaves. → Shinsengumi farewell: a ship leaves Edo at dawn;
Kondo, Hijikata, Okita on deck; Hijikata lights a cigarette 「……我们会回来的。」 Otae on
the dock watching.

## 镜头表（场景文件开头的 SHOT LIST，场景内时间）

```text
s12 洛阳决战·离别 (Rakuyo decisive battle / farewell) — 19.0 s.

SHOT LIST (scene-local seconds)
  A   0.00- 1.75  chapter card 「洛阳决战篇」 over the rain planet; thunder flash on the slam.
  B1  1.75- 2.55  Rakuyo ruins in the rain (crashed battleship, broken pagodas), slow pan.
                  Kagura (L) and Kamui (R) face off; lightning 1.92; crouch 2.24; DASH 2.36.
  B2  2.55- 3.42  close: umbrella tips CLASH 2.58 -> impact frame, shockwave rings, rain blasted
                  outward, 「锵!!」. Exchanges: 2.88 punch/guard, 3.06 kick/guard 「砰!」,
                  3.24 overhead bind (umbrellas cross in an X, grinding sparks).
  B3  3.42- 3.92  split-screen face-off: Kagura's glare | Kamui's smile -> eyes OPEN 3.62.
  B4  3.92- 4.42  both leap; a shadow grows between them, fall whistle; Umibozu plummets in.
  C   4.42- 6.10  LANDING: impact frame, crater, siblings blown apart. 「够了！」 (4.60),
                  push-in, name_card 星海坊主 4.85 (latin tag, 2.2 s).
  C2  6.10- 7.50  GAG close two-shot: raindrops 'ting' off the bald dome (叮! 叮! 叮叮叮,
                  accelerating), Kagura deadpan + sweat drop + 「……」, Umibozu's anger vein 7.16.
  D1  7.50- 9.90  Kagura close-up in the rain (letterbox), Kamui as a dark foreground
                  silhouette; she points: 「我一定会把哥哥带回家阿鲁！」, then a slow push-in.
  D2  9.90-11.70  (music -> sad) Kamui's gentle smile... turns, opens his umbrella (10.45),
                  walks off into the mist; camera pulls back: Kagura steps after him and
                  reaches out, Umibozu watching behind her; far lightning 11.05.
  E1 11.70-13.50  white-in: Edo harbour at dawn, the Shinsengumi ship (诚 sail) lifts off. Narration.
  E2 13.50-16.40  on deck: Hijikata lights a cigarette (13.68), exhales a smoke stream;
                  pull back to the stern: Kondo bawling (wind-blown tear streams), Okita napping
                  with his eye-mask. Hijikata 「……我们会回来的。」
  E3 16.40-19.00  the dock: Otae under a cherry tree watches the ship rise into the sunrise;
                  「阿妙小姐～～！」 bubble from the ship; she waves; the ship twinkles like a star.
```

## 台词 / 旁白时间表（场景内时间）

| 开始 | 结束 | 说话者 | 台词 |
|---|---|---|---|
| 4.60 | 6.10 | 星海坊主 | 够了！ |
| 7.55 | 9.88 | 神乐 | 我一定会把哥哥带回家阿鲁！ |
| 11.72 | 14.22 | 旁白 | 被解散的真选组，在黎明时分离开了江户。 |
| 14.26 | 16.35 | 土方 | ……我们会回来的。 |

## 音效 cue（场景内时间）

| t | 音效 | 音量 | 持续 |
|---|---|---|---|
| 0.00 | rain | 0.55 | 11.6 |
| 0.00 | wind | 0.25 | 11.7 |
| 0.05 | sting_dramatic | 0.7 |  |
| 0.36 | thunder | 0.8 |  |
| 0.40 | gong | 0.5 |  |
| 1.92 | thunder | 0.9 |  |
| 2.24 | charge | 0.4 |  |
| 2.36 | dash | 1.0 |  |
| 2.38 | run | 0.4 | 0.2 |
| 2.58 | clang | 1.0 |  |
| 2.58 | impact | 1.0 |  |
| 2.60 | punch_big | 0.7 |  |
| 2.63 | explosion_small | 0.4 |  |
| 2.88 | punch | 0.8 |  |
| 2.89 | clang | 0.6 |  |
| 3.06 | kick | 1.0 |  |
| 3.07 | clang | 0.5 |  |
| 3.24 | clang | 1.0 |  |
| 3.24 | slash_big | 0.6 |  |
| 3.42 | whoosh | 0.7 |  |
| 3.62 | shing | 0.8 |  |
| 3.62 | heartbeat | 0.7 |  |
| 3.92 | jump | 0.7 |  |
| 3.95 | jump | 0.6 |  |
| 3.98 | fall_whistle | 0.9 |  |
| 4.42 | impact | 1.0 |  |
| 4.42 | explosion | 0.7 |  |
| 4.43 | land | 1.0 |  |
| 4.45 | crash | 0.5 |  |
| 4.46 | whoosh | 0.6 |  |
| 4.60 | vein | 0.6 |  |
| 4.78 | land | 0.6 |  |
| 4.80 | land | 0.5 |  |
| 4.85 | whoosh | 0.5 |  |
| 5.05 | shock | 0.5 |  |
| 6.30 | bell | 0.45 |  |
| 6.58 | bell | 0.45 |  |
| 6.62 | sweat | 0.5 |  |
| 6.86 | bell | 0.3 |  |
| 6.95 | bell | 0.3 |  |
| 7.04 | bell | 0.3 |  |
| 7.16 | vein | 0.8 |  |
| 7.75 | whoosh | 0.4 |  |
| 10.45 | whoosh | 0.6 |  |
| 10.47 | pop | 0.5 |  |
| 10.65 | footsteps | 0.35 | 1.049999999999999 |
| 10.95 | footsteps | 0.25 | 0.4 |
| 11.05 | thunder | 0.45 |  |
| 11.70 | shine | 0.4 |  |
| 11.70 | river | 0.35 | 1.8000000000000007 |
| 11.70 | engine_hum | 0.45 | 4.699999999999999 |
| 11.70 | wind | 0.3 | 7.300000000000001 |
| 12.00 | bell | 0.3 |  |
| 13.68 | pop | 0.45 |  |
| 13.70 | fire | 0.3 | 0.370000000000001 |
| 14.35 | whoosh | 0.3 |  |
| 16.40 | river | 0.4 | 2.6000000000000014 |
| 16.65 | blip | 0.4 |  |
| 17.95 | twinkle | 1.0 |  |
