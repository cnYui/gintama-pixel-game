# s08 真选组动乱篇

- 时长：23.0 s（成片里 162.2–185.2 s）
- 音乐：0s → tension、8.8s → battle、19.15s → （静音）、20.25s → sad（音量 0.55）
- 出场角色（代码里引用到的角色 id）：gintoki（银时）、hijikata（土方）、ito（伊东）、kagura（神乐）、kondo（近藤）、okita（冲田）、shinpachi（新八）、toshi（托西）、yamazaki（山崎）
- 背景（bg 模块里被调用的函数）：common：add_sprite, big_moon, clouds, far_mountains, glow_sprite, room_wall, sky, tatami, vgradient
- 淡入 / 淡出：0.3 / 0.3 s

## 故事分镜（CONTRACT.md 第 8 节，写作时的设计意图）

**s08 真选组动乱篇 (22 s)** `[(0,"tension"),(~9,"battle")]` chapter_card 「真选组动乱篇」

Cursed sword: Hijikata becomes the timid otaku Toshi (dogeza, anime figure) name_card
托西 「被妖刀诅咒的宅男人格」. → Ito (glasses glint) schemes 「近藤局长……该退场了。」
name_card 伊东鸭太郎 「参谋｜野心家」. → Speeding train battle: traitors vs Kondo, Okita
slicing through a carriage, Yorozuya racing alongside in a police car. → Hijikata breaks
the curse (aura): 「我是……真选组副长——土方十四郎！！」 → final duel at sunset, Ito falls,
smiling: 「……谢谢。」

## 镜头表（场景文件开头的 SHOT LIST，场景内时间）

```text
s08 真选组动乱篇 (23 s) — the Shinsengumi Crisis arc.

SHOT LIST (scene-local seconds; every time below is a named constant)
 0.00- 1.90  CHAPTER CARD 「真选组动乱篇」 over shot A (sting).
 A  1.90- 6.00  Shinsengumi HQ, night. Hijikata grips the cursed sword (tag 「妖刀·村麻纱」):
               purple aura, room goes violet, accelerating heartbeat push-in with
               zoom throbs (2.0 / 2.5 / 2.85) while Yamazaki munches anpan, oblivious.
               3.10 POOF -> snap zoom-out: Toshi in dogeza banging his forehead
               (「咚!」 3.35 / 4.10), Yamazaki drops his anpan (shock). name_card 托西 3.6.
               4.60 Toshi stands cradling an idol figure, pink moe sparkles, push-in;
               Yamazaki's burnt-out 「……」 + crow at 5.1.
 B  6.00- 8.80  Ito's dark room, round moon window, moonlight shaft.  Ito (cold stare)
               slow push-in; red-eyed rebel silhouettes fade in behind him (6.8).
               name_card 伊东鸭太郎 6.2.  7.45 CUT close-up (letterbox): glasses push ->
               big glint 7.8.
 C1 8.80-11.50  Dusk, speeding train: camera pans from the locomotive back to the
               carriage; Okita on the roof.  9.80 he leaps, 9.90 slash streak along the
               carriage, 10.05 hit-stop flash 「斩!!」, 10.15 the roof is blown away,
               rebels fly out, Okita drops in; Kondo shock -> tears of joy 「总悟～!!」.
 C2 11.50-13.60 Road beside the tracks: the Yorozuya police car screeches into frame
               (Gintoki driving, Shinpachi + Toshi in the back, siren), Kagura on the
               roof machine-gunning rebels off the train roof (hits 12.30 / 13.00).
 D  13.60-17.20 Train roof, dusk wind.  A rebel's slash knocks Toshi's figure away, it
               shatters (14.55).  Gloom push-in, purple wisps... 14.95 FLASH: blue
               aura, Toshi -> HIJIKATA (Toshi's ghost floats away waving), iai draw
               (hit 15.36, 「斩!」), rebel flies; shout pose, katana on the shoulder.
 E1 17.20-20.25 Sunset duel (letterbox, rim-lit silhouettes against a huge sun, train
               wreck smoking).  17.95 split-screen EYE CUT-IN (Hijikata / Ito, lens
               glint), 18.60 dash, 19.15 cross -> impact frame, music cuts; 19.85 Ito's
               sword drops, he kneels.
 E2 20.25-23.00 Warm push-in on Ito kneeling, smiling at the sun 「……谢谢。」, a tear,
               golden motes; Hijikata's back, smoking; Ito closes his eyes (22.0).
```

## 台词 / 旁白时间表（场景内时间）

| 开始 | 结束 | 说话者 | 台词 |
|---|---|---|---|
| 3.30 | 5.80 | 托西 | 对不起！我马上去买炒面面包！ |
| 6.45 | 8.70 | 伊东 | 近藤局长……该退场了。 |
| 8.95 | 11.30 | 旁白 | 伊东叛变！列车上的近藤陷入重围—— |
| 11.50 | 13.60 | 银时 | 这委托，万事屋接下了！ |
| 14.65 | 17.20 | 土方 | 我是……真选组副长——土方十四郎！！ |
| 20.65 | 22.60 | 伊东 | ……谢谢。 |

## 音效 cue（场景内时间）

| t | 音效 | 音量 | 持续 |
|---|---|---|---|
| 0.15 | sting_dramatic | 0.8 |  |
| 1.70 | aura | 0.7 |  |
| 2.00 | heartbeat | 0.8 |  |
| 2.15 | chomp | 0.35 |  |
| 2.50 | heartbeat | 0.95 |  |
| 2.85 | heartbeat | 1.0 |  |
| 2.90 | shock | 0.4 |  |
| 3.10 | pop | 1.0 |  |
| 3.10 | boing | 0.6 |  |
| 3.20 | shock | 0.7 |  |
| 3.35 | thud | 0.6 |  |
| 3.55 | sweat | 0.5 |  |
| 3.65 | squeak | 0.5 |  |
| 4.10 | thud | 0.6 |  |
| 4.60 | sparkle | 0.8 |  |
| 5.10 | crow | 0.7 |  |
| 6.00 | night | 0.35 | 2.8 |
| 6.05 | heartbeat | 0.6 |  |
| 6.80 | aura | 0.45 |  |
| 7.45 | impact | 0.5 |  |
| 7.80 | shine | 1.0 |  |
| 8.80 | train | 0.8 | 2.75 |
| 8.80 | wind | 0.35 | 2.75 |
| 9.05 | whoosh | 0.6 |  |
| 9.80 | jump | 1.0 |  |
| 9.90 | slash_big | 1.0 |  |
| 10.05 | impact | 1.0 |  |
| 10.15 | crash | 1.0 |  |
| 10.17 | fly_away | 0.7 |  |
| 10.20 | hit | 1.0 |  |
| 10.25 | hit | 1.0 |  |
| 10.29 | land | 0.7 |  |
| 10.30 | punch | 0.8 |  |
| 10.65 | shock | 0.6 |  |
| 11.38 | whoosh | 0.5 |  |
| 11.50 | engine_hum | 0.7 | 2.1 |
| 11.50 | dash | 0.7 |  |
| 11.80 | whoosh | 0.5 |  |
| 11.90 | machinegun | 1.0 |  |
| 12.05 | land | 0.6 |  |
| 12.30 | hit | 1.0 |  |
| 12.34 | clang | 0.6 |  |
| 12.55 | machinegun | 1.0 |  |
| 13.00 | hit | 1.0 |  |
| 13.05 | fly_away | 0.7 |  |
| 13.60 | wind | 0.55 | 3.6 |
| 13.65 | dash | 0.7 |  |
| 14.05 | slash | 1.0 |  |
| 14.12 | shock | 0.6 |  |
| 14.55 | glass | 1.0 |  |
| 14.65 | heartbeat | 0.9 |  |
| 14.80 | charge | 0.6 |  |
| 14.95 | aura | 1.0 |  |
| 14.95 | impact | 1.0 |  |
| 15.15 | twinkle | 0.35 |  |
| 15.28 | shing | 1.0 |  |
| 15.36 | slash_big | 1.0 |  |
| 15.38 | hit | 1.0 |  |
| 15.42 | fly_away | 0.6 |  |
| 17.20 | wind | 0.7 | 5.800000000000001 |
| 17.95 | whoosh | 0.5 |  |
| 18.19 | shing | 0.6 |  |
| 18.33 | shine | 0.8 |  |
| 18.60 | dash | 1.0 |  |
| 19.15 | slash_big | 1.0 |  |
| 19.15 | impact | 1.0 |  |
| 19.97 | thud | 0.6 |  |
| 20.03 | clang | 0.5 |  |
| 20.65 | bell | 0.3 |  |
