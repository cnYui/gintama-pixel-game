# s09 吉原炎上篇

- 时长：29.5 s（成片里 185.2–214.7 s）
- 音乐：0s → yoshiwara、12.75s → battle、21.2s → epic（音量 0.55）
- 出场角色（代码里引用到的角色 id）：gintoki（银时）、hinowa（日轮）、housen（凤仙）、kamui（神威）、seita（晴太）、townsman（路人）、townswoman（路人）、tsukuyo（月咏）
- 背景（bg 模块里被调用的函数）：common：add_sprite, bayer, cherry_tree, glow_sprite, grade_rgba, lantern, light_up, stone_street, tatami, vgradient, wood_floor
- 淡入 / 淡出：0.3 / 0.3 s

## 故事分镜（CONTRACT.md 第 8 节，写作时的设计意图）

**s09 吉原炎上篇 (28 s)** `[(0,"yoshiwara"),(~11,"battle"),(~21,"epic")]` chapter_card 「吉原炎上篇」

Underground Yoshiwara: lanterns, iron ceiling, no sky. Seita wants to see his mother.
Tsukuyo name_card 「百华首领｜死神太夫」 「吉原没有太阳。」 → Hinowa in her tower, name_card
日轮 「吉原的太阳」. → Kamui on a roof, name_card 神威 「春雨第七师团团长｜神乐的哥哥」
「我只对强者感兴趣。」 → Housen, name_card 夜王凤仙 「吉原之主｜夜兔之王」. Gintoki is
smashed through walls, rises bloody: 「我的剑，是用来守护该守护的东西的。」 → the ceiling
opens: SUNLIGHT floods Yoshiwara (big light shafts). Housen weakens in the sun, Gintoki's
final strike. Housen looks up: 「太阳……原来是这么温暖的东西。」 crumbles into dust. →
Seita and Hinowa reunited in the sunlight, sakura.

## 镜头表（场景文件开头的 SHOT LIST，场景内时间）

```text
s09 吉原炎上篇 (29.5 s) — underground Yoshiwara, the Night King, the sun.

SHOT LIST (scene-local seconds)
  0.00- 1.90  chapter card 「吉原炎上篇」 over the iron lid (establishing starts beneath)
  S1  0.00- 5.45  tilt DOWN from the riveted iron ceiling to the lantern street; crowd;
                  Seita runs in; push-in on him while he speaks. name_card 晴太 3.4
  S2  5.45- 8.10  medium: rooftop glint -> kunai thunks at Seita's toes (咚! / !! hop,
                  sweat) -> Tsukuyo drops from the roof, lands, kiseru. name_card 月咏 6.0
  S3  8.10-10.45  tilt UP Hinowa's tower -> push-in to the round window (Hinowa).
  S4 10.45-12.75  rooftop: Kamui sitting; 11.90 CUT close-up, eyes open (red flash,
                  dark-red focus lines).
  S5 12.75-15.00  throne room dark, eyes glint -> 13.10 gong, whip pull-back to the
                  full giant with red aura. name_card 夜王凤仙 13.3 (music -> battle)
  S6 15.00-16.55  corridor: haymaker, custom impact frame 15.36 (black/red, white
                  silhouettes), Gintoki tumbles through three thick walls (chunks).
  S7 16.55-19.70  street: bursts out of a facade, lands, rises bloody (bokuto glint),
                  Housen's silhouette in the hole.
  S8a 19.70-20.65 control room: Tsukuyo shoves, Seita dangles off the lever handle;
                  slam 20.25 (咔嚓!!), gears spin, Seita cheers.
  S8b 20.65-21.95 looking up: the lid opens, SUN + rays (music -> epic 21.2), white-out.
  S9  21.95-24.20 sunlit street: Housen scorched; Gintoki crouches and launches;
                  22.50-22.93 insert: his rim-lit silhouette crosses the sun; dive,
                  impact frame 23.02, 斩!!, Housen falls to his knees.
  S10 24.20-26.60 close on Housen's upturned face in the light, pull back as he
                  crumbles into dust while Gintoki watches.
  S11 26.60-29.50 sakura: Seita runs into Hinowa's arms (hearts); pan to Gintoki
                  face-down 「……糖分……」 + Tsukuyo's sweat drop + crow.
```

## 台词 / 旁白时间表（场景内时间）

| 开始 | 结束 | 说话者 | 台词 |
|---|---|---|---|
| 3.30 | 5.45 | 晴太 | 我想见娘……哪怕一面也好！ |
| 5.95 | 8.10 | 月咏 | 死心吧。吉原……没有太阳。 |
| 8.20 | 10.40 | 旁白 | 晴太的母亲，被囚禁在高塔之上。 |
| 10.50 | 12.65 | 神威 | 我只对强者感兴趣。 |
| 12.80 | 15.00 | 凤仙 | 吉原的太阳，只属于我一人。 |
| 17.20 | 19.70 | 银时 | 我的剑，是用来守护该守护的东西的。 |
| 24.25 | 26.55 | 凤仙 | 太阳……原来是这么温暖的东西。 |
| 26.75 | 28.75 | 旁白 | 吉原，终于迎来了太阳。 |

## 名牌 / 篇章卡（从代码里直接调用处提取，可能不全）

- 名牌 3.4s（2.05s）：seita — 晴太 吉原长大的少年｜想见娘亲
- 名牌 6s（2.1s）：tsukuyo — 月咏 百华首领｜死神太夫
- 名牌 8.75s（1.7s）：hinowa — 日轮 吉原的太阳｜传说中的花魁
- 名牌 10.55s（2.15s）：kamui — 神威 春雨第七师团团长｜神乐的哥哥
- 名牌 13.3s（1.7s）：housen — 夜王凤仙 吉原之主｜夜兔之王
- 篇章卡 0s（1.9s）：吉原炎上篇 ——没有太阳的地下花街

## 音效 cue（场景内时间）

| t | 音效 | 音量 | 持续 |
|---|---|---|---|
| 0.00 | night | 0.35 | 15.0 |
| 0.05 | gong | 0.8 |  |
| 1.80 | crowd | 0.22 | 6.3 |
| 1.80 | whoosh | 0.35 |  |
| 3.00 | run | 0.5 | 0.9 |
| 3.40 | whoosh | 0.5 |  |
| 3.90 | slide_down | 0.35 |  |
| 5.48 | shine | 0.5 |  |
| 5.59 | whoosh | 0.7 |  |
| 5.68 | stab | 1.0 |  |
| 5.70 | shock | 0.8 |  |
| 5.85 | whoosh | 0.6 |  |
| 6.00 | whoosh | 0.4 |  |
| 6.02 | land | 1.0 |  |
| 8.15 | bell | 0.45 |  |
| 8.75 | whoosh | 0.4 |  |
| 9.20 | sparkle | 0.4 |  |
| 10.45 | wind | 0.4 | 2.3 |
| 10.55 | whoosh | 0.4 |  |
| 11.90 | shine | 1.0 |  |
| 11.90 | sting_dramatic | 0.8 |  |
| 12.80 | shine | 0.7 |  |
| 12.80 | heartbeat | 0.7 |  |
| 13.10 | gong | 1.0 |  |
| 13.10 | aura | 1.0 |  |
| 13.15 | fire | 0.35 | 1.85 |
| 13.30 | whoosh | 0.4 |  |
| 15.05 | charge | 0.6 |  |
| 15.30 | whoosh | 1.0 |  |
| 15.36 | punch_big | 1.0 |  |
| 15.36 | impact | 1.0 |  |
| 15.41 | fly_away | 0.6 |  |
| 15.61 | crash | 1.0 |  |
| 15.91 | crash | 1.0 |  |
| 16.22 | crash | 1.0 |  |
| 16.55 | crash | 1.0 |  |
| 16.55 | explosion_small | 0.7 |  |
| 16.85 | thud | 1.0 |  |
| 17.15 | wind | 0.35 | 2.5 |
| 17.50 | shing | 0.6 |  |
| 18.15 | heartbeat | 0.6 |  |
| 19.72 | squeak | 0.5 |  |
| 19.80 | sweat | 0.5 |  |
| 20.15 | whoosh | 0.6 |  |
| 20.25 | clang | 1.0 |  |
| 20.27 | impact | 0.6 |  |
| 20.30 | engine_hum | 0.6 | 1.6 |
| 20.50 | cheer | 0.35 |  |
| 20.70 | thunder | 0.6 |  |
| 20.92 | slide_up | 0.7 |  |
| 21.20 | shine | 1.0 |  |
| 21.60 | sparkle | 1.0 |  |
| 22.00 | fire | 0.3 | 1.0 |
| 22.37 | jump | 1.0 |  |
| 22.50 | shine | 0.8 |  |
| 22.90 | whoosh | 1.0 |  |
| 23.02 | slash_big | 1.0 |  |
| 23.02 | impact | 1.0 |  |
| 23.17 | land | 1.0 |  |
| 23.60 | thud | 1.0 |  |
| 24.20 | wind | 0.3 | 2.400000000000002 |
| 25.40 | sparkle | 0.5 |  |
| 26.35 | twinkle | 0.5 |  |
| 26.60 | run | 0.45 | 0.5 |
| 27.20 | sparkle | 0.5 |  |
| 28.45 | pop | 0.6 |  |
| 28.90 | crow | 0.5 |  |
