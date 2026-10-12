# s14 尾声

- 时长：24.0 s（成片里 310.2–334.2 s）
- 音乐：0s → （静音）、5.4s → ending（音量 0.7）
- 出场角色（代码里引用到的角色 id）：amanto_pig（天人(猪)）、catherine（凯瑟琳）、elizabeth（伊丽莎白）、gintoki（银时）、hasegawa（长谷川）、hijikata（土方）、kagura（神乐）、kamui（神威）、katsura（桂）、kondo（近藤）、okita（冲田）、otae（阿妙）、otose（登势）、otsu（阿通）、sadaharu（定春）、sakamoto（坂本）、seita（晴太）、shigeshige（茂茂）、shinpachi（新八）、tama（小玉）、townsman（路人）、townswoman（路人）、tsukuyo（月咏）、umibozu（星海坊主）、yamazaki（山崎）
- 背景（bg 模块里被调用的函数）：common：bayer, cherry_tree, clouds, dirt_ground, far_mountains, river, sky, storm_flash；kabukicho：stairs_y, street, yorozuya_front, yorozuya_front_fg；yorozuya：desk_fg, office, office_fg
- 淡入 / 淡出：0.3 / 0.35 s

## 故事分镜（CONTRACT.md 第 8 节，写作时的设计意图）

**s14 尾声 (22 s)** `ending`

「两年后……」 Kabukicho rebuilt; Shinpachi & Kagura keep the Yorozuya. A hooded wanderer in
the rain → hood off: Gintoki 「我回来了。」 → Kagura dropkick, Shinpachi 「你到底跑哪去了！！」
→ chaos resumes (quick cuts): Otae punches Kondo into a star, Okita bazookas Hijikata,
Katsura 「不是假发，是桂！」, Sadaharu chomps Gintoki. → A giant 「完」 stamp slams down;
Gintoki kicks it away 「才不会完呢！」 → all characters parade across the screen as credits
「原作：空知英秋《银魂》｜本片为同人像素致敬作品」 → 「感谢观看」 with Gintoki reading Jump.

## 镜头表（场景文件开头的 SHOT LIST，场景内时间）

```text
s14 尾声 Epilogue (24 s; music: rain-only silence -> 'ending' at the hood-off reveal).

SHOT LIST (scene-local seconds)
 A   0.00- 2.60  Yorozuya front in the RAIN (storm), slow push-in. Kagura (parasol, wistful)
                 and Shinpachi wait on the balcony. Brush title 「两年后……」, lightning 2.10.
                 narration「歌舞伎町重建，新八和神乐守着万事屋。」
 B1  2.60- 3.50  Extreme close-up (zoom 4.6->4.2) tracking the boots through a rain puddle
                 (reflection, ripples, splashes 2.88/3.22), tilt up the cloak to the hood:
                 red eyes glint 3.30.
 B2  3.50- 4.80  Wide street in the rain: the hooded wanderer walks in and stops under the
                 balcony; Shinpachi notices 「！」 (4.35), Kagura turns.
 B3a 4.80- 6.50  Close-up push-in (2.3->2.7): lightning 5.05, hand grabs the hood, pulls it
                 back 5.15-5.40 -> silver perm pops out (sparkle) = GINTOKI. Rain stops, clouds
                 break (storm->day crossfade + light shafts). Music 'ending' starts 5.40.
                 sub 银时「我回来了。」
 B3b 6.50- 7.20  Reaction: Kagura & Shinpachi on the balcony, tears welling; Kagura crouches.
 C1  7.20- 8.60  Street (day, wet road, zoom 1.5): Kagura leaps off the balcony 「银酱——！！」,
                 DROPKICK 7.85 (smash-zoom 2.4, 2-frame ink/red silhouette impact frame, speed
                 lines, 砰!!) -> Gintoki pinwheels left into a pile of rain barrels 8.12
                 (哐当!!, barrels fly) and ends upside-down; the cloak flutters down;
                 Shinpachi runs down the stairs.
 C2  8.60-10.60  Medium (zoom 2.2->2.4): Gintoki flat on the road (dizzy stars), Kagura
                 bawling behind him; Shinpachi skids in, huge tsukkomi point 8.75 (speed
                 lines, tears). sub 新八「你到底跑哪去了！！」 -> 9.72 Gintoki lifts a limp
                 hand 「……哟。」 -> 10.05 Shinpachi's anger vein.
 D   10.60-15.95 "Everyday life is back" quick cuts (white pop on each cut, corner caption
                 「日常·回归中」):
  D1 10.60-11.75 Street: Kondo peeks from his bush -> Otae super punch 11.00 -> camera tilts up
                 after the spinning gorilla -> twinkle star in the sky 11.42.
  D2 11.75-12.90 Riverbank under a cherry tree: Okita fires the bazooka 12.00 at smoking
                 Hijikata -> BOOM 12.08 -> soot + afro, 「总悟——！！」.
  D3 12.90-14.93 Rotating sunburst close-up: 「假发～」 bubble from off-screen, Katsura whips
                 round 13.05 (x3), 「不是假发」 13.18 / 「是桂！」 slam 13.40; Elizabeth pops up
                 with sign 「没错」 13.95.  sub 桂「不是假发，是桂！」
  D4 14.93-15.95 Yorozuya front: Gintoki waves at his dog, Sadaharu lunges and CHOMPS his
                 head 15.08 (zoom punch), lifts him - arms flailing, legs kicking; Kagura
                 cheers, Shinpachi sweats.
 E   15.95-19.00 Freeze-frame (grey) -> giant red hanko 「完」 slams 16.12 -> crow, silence ->
                 thumps 16.85/17.00 -> Gintoki KICKS the stamp away 17.12 (colour returns), it
                 twinkles off as a star 17.62; Gintoki points up (zoom 2.6).
                 sub 银时「才不会完呢！」
 F   19.00-21.90 Dusk Kabukicho, camera tracks along a two-row PARADE of the whole cast
                 (Kagura riding Sadaharu, Gintoki reading Jump at the tail); credits
                 「原作：空知英秋《银魂》」「本片为同人像素致敬作品」.
 G   21.90-24.00 Yorozuya office at dusk: Gintoki reads Jump on the sofa, Kagura & Sadaharu
                 asleep, Shinpachi in the boss chair; 「感谢观看」; he glances at camera 23.05,
                 push-in + iris closes on Gintoki (23.3-23.92).
```

## 台词 / 旁白时间表（场景内时间）

| 开始 | 结束 | 说话者 | 台词 |
|---|---|---|---|
| 0.25 | 2.58 | 旁白 | 歌舞伎町重建，新八和神乐守着万事屋。 |
| 5.50 | 7.20 | 银时 | 我回来了。 |
| 8.64 | 10.60 | 新八 | 你到底跑哪去了！！ |
| 13.05 | 14.93 | 桂 | 不是假发，是桂！ |
| 17.22 | 19.00 | 银时 | 才不会完呢！ |

## 音效 cue（场景内时间）

| t | 音效 | 音量 | 持续 |
|---|---|---|---|
| 0.00 | rain | 0.8 | 6.9 |
| 2.22 | thunder | 0.7 |  |
| 2.60 | footsteps | 0.35 | 1.9 |
| 2.88 | land | 0.4 |  |
| 3.22 | land | 0.35 |  |
| 3.30 | shing | 0.5 |  |
| 4.35 | shock | 0.6 |  |
| 5.15 | thunder | 0.8 |  |
| 5.15 | whoosh | 0.5 |  |
| 5.40 | shine | 0.8 |  |
| 5.45 | sparkle | 0.5 |  |
| 6.95 | charge | 0.4 |  |
| 7.25 | jump | 0.8 |  |
| 7.35 | run | 0.35 | 1.3 |
| 7.50 | whoosh | 0.6 |  |
| 7.62 | sweat | 0.5 |  |
| 7.85 | punch_big | 1.0 |  |
| 7.85 | impact | 0.7 |  |
| 7.89 | fly_away | 0.7 |  |
| 8.05 | land | 0.6 |  |
| 8.12 | crash | 0.9 |  |
| 8.16 | thud | 0.6 |  |
| 8.65 | dizzy | 0.4 |  |
| 8.75 | shock | 0.7 |  |
| 9.72 | pop | 0.4 |  |
| 10.05 | vein | 0.7 |  |
| 10.60 | slide_up | 0.4 |  |
| 10.78 | whoosh | 0.6 |  |
| 11.00 | punch_big | 1.0 |  |
| 11.03 | fly_away | 0.7 |  |
| 11.42 | twinkle | 0.8 |  |
| 12.00 | bazooka | 0.9 |  |
| 12.08 | explosion | 1.0 |  |
| 12.45 | cough | 0.6 |  |
| 13.02 | record_scratch | 0.6 |  |
| 13.07 | whoosh | 0.5 |  |
| 13.18 | pop | 0.6 |  |
| 13.40 | impact | 0.9 |  |
| 14.02 | pop | 0.6 |  |
| 15.08 | chomp | 1.0 |  |
| 15.08 | impact | 0.5 |  |
| 15.18 | shock | 0.5 |  |
| 15.37 | chomp | 0.8 |  |
| 15.87 | chomp | 0.8 |  |
| 15.95 | record_scratch | 0.8 |  |
| 16.12 | impact | 1.0 |  |
| 16.12 | gong | 0.8 |  |
| 16.40 | crow | 0.8 |  |
| 16.85 | thud | 0.6 |  |
| 17.00 | thud | 0.7 |  |
| 17.12 | kick | 1.0 |  |
| 17.12 | crash | 0.6 |  |
| 17.15 | fly_away | 0.7 |  |
| 17.55 | bark | 0.5 |  |
| 17.62 | twinkle | 0.8 |  |
| 19.00 | crowd | 0.2 | 2.9 |
| 19.05 | cheer | 0.35 |  |
| 19.10 | sparkle | 0.5 |  |
| 22.05 | shine | 0.6 |  |
| 23.25 | slide_down | 0.4 |  |
