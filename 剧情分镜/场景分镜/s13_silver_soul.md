# s13 银之魂篇

- 时长：32.5 s（成片里 277.7–310.2 s）
- 音乐：0s → epic、18.95s → sad、23.75s → epic（音量 0.55）
- 出场角色（代码里引用到的角色 id）：catherine（凯瑟琳）、elizabeth（伊丽莎白）、gintoki（银时）、gintoki_kid（小银时）、hasegawa（长谷川）、hijikata（土方）、kagura（神乐）、kamui（神威）、katsura（桂）、katsura_kid（小桂）、kondo（近藤）、naraku（奈落）、okita（冲田）、otae（阿妙）、otose（登势）、sadaharu（定春）、sakamoto（坂本）、shinpachi（新八）、shouyou（松阳）、takasugi（高杉）、takasugi_kid（小高杉）、tama（小玉）、tsukuyo（月咏）、umibozu（星海坊主）、utsuro（虚）
- 背景（bg 模块里被调用的函数）：common：add_sprite, bayer, clouds, glow_sprite, sky；edo：roof_walk, ship, ship_size, skyline
- 淡入 / 淡出：0.3 / 0.6 s

## 故事分镜（CONTRACT.md 第 8 节，写作时的设计意图）

**s13 银之魂篇 (32 s)** `epic` (switch to `sad` for Takasugi's death, back to `epic` for the

final strike) chapter_card 「银之魂篇」
Alien armada darkens the sky over Edo; Utsuro appears, name_card 虚 「不死之身｜松阳的另一面」
「我即是虚。」 → EVERYONE ASSEMBLES montage on the rooftops (fast cuts, big text
「全江户，集结！」): Shinsengumi return, Katsura + Elizabeth army, Tsukuyo, Otae with
naginata, Otose/Catherine/Tama, Hasegawa, Sakamoto's ship, the Yato family (Kagura, Kamui,
Umibozu), Sadaharu. → Gintoki & Takasugi back to back vs Utsuro. Takasugi is mortally
wounded; dies in Gintoki's arms: 「银时……剩下的，交给你了。」 → dawn: Gintoki's final strike
(impact frame), Utsuro shatters into light; Shouyou's gentle face: 「……谢谢。你们都长大了呢。」
→ sunrise over Edo.

## 镜头表（场景文件开头的 SHOT LIST，场景内时间）

```text
s13 银之魂篇 (32.5 s) — music: epic -> sad (Takasugi falls) -> epic (dawn strike).

SHOT LIST
  0.00- 2.00  A  chapter_card 「银之魂篇」; a mothership silhouette creeps down over the
                 card, armada silhouettes cross below, red embers rise.
  2.00- 4.60  B  Edo at night: a colossal mothership sinks over the city (red lights,
                 pulsing core), its shadow darkens Edo while the armada gathers; camera
                 pulls back from its belly to the whole city, searchlights sweep.
                 Narration (2.25-4.50).
  4.60- 5.90  C1 Rooftop: crows scatter, dark wisps spiral in and Utsuro materialises
                 (regen aura, glowing eyes); slow push-in. name_card 虚 (5.35-7.55).
  5.90- 7.60  C2 Bust close-up of Utsuro on a blood-dark backdrop: eyes closed ->
                 6.20 they open blazing red (glint). 「我即是虚。」 (5.85-7.58)
  7.60-13.45  D  ASSEMBLY montage, one rooftop per group, fast cuts with flash
                 transitions, speed lines + slam-in group labels:
                 7.60 真选组 · 8.25 攘夷志士 · 8.90 最强女子 · 9.55 登势酒馆 ·
                 10.20 MADAO gag (1.35 s: record scratch, colour drains, glint,
                 「我、我也来了……」, crow caws 「阿呆～」, sweat drop) ·
                 11.55 快援队 · 12.20 夜兔一族 · 12.85 万事屋 (Sadaharu + Shinpachi).
 13.45-15.50  W  Wide: everyone lands on two roof ridges under the armada;
                 13.85 「全江户，集结！」 slams in, the front row hops (rally).
 15.50-17.50  E1 Gintoki & Takasugi back to back, Naraku creeping in. 「别拖后腿啊，银时。」
 17.50-18.10  E2a Both dash at Utsuro: X-slash -> he just regenerates, smiling.
 18.10-18.55  E2b Utsuro's thrust lunges at Gintoki; Takasugi shoves him aside.
 18.55-19.40  E2c red impact frame (big silhouettes, blade through Takasugi); grey
                 stagger; 18.95 Gintoki shouting close-up 「高杉——！！」 -> music 'sad'.
 19.40-20.65  F  Ash falling: Gintoki kneels, cradling Takasugi, who reaches up.
                 「银时……剩下的，交给你了。」 (19.55-22.10)
 20.65-21.55  FB sepia flash of 松下村塾: kid Takasugi challenges kid Gintoki, kid
                 Katsura watches, Shouyou smiles.
 21.55-23.05  FC closer: last smile (22.15), the hand drops (22.45), colour drains.
 23.05-23.50  F2 Gintoki's bust, eyes in shadow, one tear falls.
 23.50-24.20  G1 He lays Takasugi down and rises; first light; Utsuro waits.
 24.20-24.90  G1b Eye-strip extreme close-up: shadowed -> 24.45 eyes blaze.
 24.90-25.80  G2 Dawn: both dash, 25.45 they pass — impact frame, giant slash line.
 25.80-26.60  G3 Frozen hold back to back (closer); glowing cracks spread over Utsuro.
 26.60-27.80  G4 Utsuro shatters into rising light; the light gathers into Shouyou.
 27.80-29.50  G4b Close-up: Shouyou smiles in the sunrise; 28.90 dissolves into light.
                 「……谢谢。你们都长大了呢。」 (27.05-29.45)
 29.50-32.50  H  Sunrise over Edo: armada retreats; Shinpachi, Gintoki, Kagura and
                 Sadaharu on a rooftop; a purple butterfly (Takasugi's motif) flutters
                 past Gintoki up into the sun. Narration (29.85-32.10).
```

## 台词 / 旁白时间表（场景内时间）

| 开始 | 结束 | 说话者 | 台词 |
|---|---|---|---|
| 2.25 | 4.50 | 旁白 | 天人舰队，遮蔽了江户的天空。 |
| 5.85 | 7.58 | 虚 | 我即是虚。 |
| 15.50 | 17.48 | 高杉 | 别拖后腿啊，银时。 |
| 19.55 | 22.10 | 高杉 | 银时……剩下的，交给你了。 |
| 27.05 | 29.45 | 松阳 | ……谢谢。你们都长大了呢。 |
| 29.85 | 32.10 | 旁白 | 长夜过去，江户迎来了黎明。 |

## 音效 cue（场景内时间）

| t | 音效 | 音量 | 持续 |
|---|---|---|---|
| 0.10 | engine_hum | 0.45 | 4.5 |
| 0.15 | gong | 0.8 |  |
| 0.30 | wind | 0.3 | 4.3 |
| 2.10 | thunder | 0.55 |  |
| 2.60 | engine_hum | 0.35 | 2.0 |
| 4.60 | crow | 0.8 |  |
| 4.62 | whoosh | 0.5 |  |
| 4.75 | aura | 0.8 |  |
| 5.15 | sting_dramatic | 0.8 |  |
| 5.35 | whoosh | 0.35 |  |
| 5.95 | heartbeat | 0.6 |  |
| 6.20 | shine | 0.7 |  |
| 7.60 | whoosh | 0.6 |  |
| 7.70 | land | 0.6 |  |
| 7.74 | land | 0.5 |  |
| 7.78 | land | 0.5 |  |
| 7.84 | shing | 0.7 |  |
| 8.25 | whoosh | 0.6 |  |
| 8.30 | pop | 0.5 |  |
| 8.35 | pop | 0.5 |  |
| 8.37 | land | 0.6 |  |
| 8.40 | pop | 0.5 |  |
| 8.45 | pop | 0.5 |  |
| 8.90 | whoosh | 0.6 |  |
| 9.00 | land | 0.5 |  |
| 9.04 | land | 0.5 |  |
| 9.05 | aura | 0.5 |  |
| 9.25 | slash | 0.6 |  |
| 9.55 | whoosh | 0.6 |  |
| 9.60 | machinegun | 0.45 |  |
| 9.95 | machinegun | 0.35 |  |
| 10.20 | record_scratch | 0.7 |  |
| 10.34 | shine | 0.55 |  |
| 10.42 | pop | 0.5 |  |
| 10.80 | crow | 0.9 |  |
| 11.15 | sweat | 0.6 |  |
| 11.55 | whoosh | 0.6 |  |
| 11.56 | engine_hum | 0.5 | 0.65 |
| 12.20 | whoosh | 0.6 |  |
| 12.34 | land | 0.8 |  |
| 12.35 | impact | 0.7 |  |
| 12.42 | machinegun | 0.5 |  |
| 12.85 | whoosh | 0.6 |  |
| 12.87 | jump | 0.6 |  |
| 13.13 | land | 0.7 |  |
| 13.20 | bark | 0.8 |  |
| 13.45 | whoosh | 0.6 |  |
| 13.55 | land | 0.5 |  |
| 13.62 | land | 0.5 |  |
| 13.70 | land | 0.5 |  |
| 13.78 | land | 0.5 |  |
| 13.85 | title_hit | 0.9 |  |
| 13.90 | cheer | 0.7 |  |
| 13.90 | crowd | 0.4 | 1.6 |
| 15.50 | wind | 0.35 | 3.8999999999999986 |
| 15.50 | fire | 0.22 | 3.8999999999999986 |
| 15.60 | shing | 0.7 |  |
| 16.55 | whoosh | 0.5 |  |
| 16.73 | slash_big | 0.8 |  |
| 16.75 | hit | 0.6 |  |
| 16.78 | hit | 0.5 |  |
| 17.25 | thud | 0.4 |  |
| 17.35 | thud | 0.35 |  |
| 17.50 | dash | 0.7 |  |
| 17.80 | slash_big | 0.9 |  |
| 17.82 | hit | 0.6 |  |
| 17.90 | aura | 0.6 |  |
| 18.12 | whoosh | 0.6 |  |
| 18.28 | dash | 0.6 |  |
| 18.55 | impact | 1.0 |  |
| 18.56 | stab | 0.5 |  |
| 18.95 | shock | 0.8 |  |
| 19.40 | wind | 0.28 | 4.100000000000001 |
| 19.50 | heartbeat | 0.7 |  |
| 20.65 | twinkle | 0.45 |  |
| 20.89 | hit | 0.35 |  |
| 21.65 | heartbeat | 0.55 |  |
| 22.15 | heartbeat | 0.35 |  |
| 22.45 | thud | 0.25 |  |
| 23.80 | whoosh | 0.35 |  |
| 24.45 | shing | 0.9 |  |
| 24.47 | shine | 0.6 |  |
| 24.95 | dash | 0.8 |  |
| 25.00 | charge | 0.5 |  |
| 25.45 | slash_big | 1.0 |  |
| 25.46 | impact | 1.0 |  |
| 26.05 | glass | 0.45 |  |
| 26.33 | glass | 0.55 |  |
| 26.60 | glass | 0.8 |  |
| 26.62 | sparkle | 0.7 |  |
| 27.00 | shine | 0.6 |  |
| 27.85 | twinkle | 0.5 |  |
| 28.90 | sparkle | 0.5 |  |
| 29.00 | bell | 0.4 |  |
| 29.50 | wind | 0.3 | 3.0 |
| 29.60 | bell | 0.45 |  |
| 31.10 | twinkle | 0.3 |  |
| 31.30 | sparkle | 0.3 |  |
