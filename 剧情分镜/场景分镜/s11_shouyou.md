# s11 松阳老师

- 时长：26.0 s（成片里 232.7–258.7 s）
- 音乐：0s → flashback、17.6s → sad、22.5s → （静音）（音量 0.6）
- 出场角色（代码里引用到的角色 id）：amanto_cat（天人(猫)）、amanto_pig（天人(猪)）、gintoki（银时）、gintoki_kid（小银时）、harusame（春雨）、katsura（桂）、katsura_kid（小桂）、naraku（奈落）、oboro（胧）、sakamoto（坂本）、shiroyasha（白夜叉）、shouyou（松阳）、takasugi（高杉）、takasugi_kid（小高杉）
- 背景（bg 模块里被调用的函数）：common：add_sprite, bayer, cherry_tree, clouds, dirt_ground, far_mountains, glow_sprite, room_wall, sky, tatami, vgradient
- 淡入 / 淡出：0.0 / 0.6 s

## 故事分镜（CONTRACT.md 第 8 节，写作时的设计意图）

**s11 松阳老师 (26 s)** `[(0,"flashback"),(~17,"sad")]` sepia flashback

Battlefield of the dead: child Gintoki sitting on corpses eating a rice ball, clutching a
sword (keep it non-graphic: silhouettes). Shouyou approaches smiling, gives him his sword:
「这把剑，是用来斩断你心中的弱小，守护你自己的灵魂的。」 name_card 吉田松阳 「松下私塾的老师」.
→ Shoukasonjuku: kids Katsura & Takasugi, Takasugi challenges Gintoki and loses; Shouyou
headbutts sleeping Gintoki (bump, laughter). → Fire: the school burns, Naraku take Shouyou;
Shouyou: 「银时，大家就拜托你了。」 → Joui war: Shiroyasha name_card 「白夜叉｜攘夷战争的传说」,
with Katsura, Takasugi and Sakamoto (name_card 坂本辰马 「快援队｜啊哈哈哈」). → Cliff:
Oboro holds Katsura & Takasugi captive; Shouyou kneels, turns, smiles: 「谢谢你。」 Gintoki
raises the sword, tears → CUT TO WHITE (no gore). Takasugi 「住手——！！」 → silence, a
single tear. → back to present-day Gintoki, eyes shadowed.

## 镜头表（场景文件开头的 SHOT LIST，场景内时间）

```text
s11 松阳老师 (26 s) — sepia flashback. music: flashback -> sad (cliff) -> silence after the cut.

SHOT LIST (scene-local seconds)
  0.00- 1.90  A1 Battlefield of the dead at dusk (old-film sepia), fading in from s10's white.
                 Pull-back reveal from circling crows / smoke columns to the field of broken
                 spears & banners; kid Gintoki sits on a dark heap of the fallen munching a rice
                 ball, sword on his shoulder. Shouyou walks in out of the low sun.
  1.90- 3.70  A2 Two-shot (x2): the kid freezes mid-chew ("!"), the rice ball rolls away, he leaps
                 down 2.25, lands 2.52 and points his blade at Shouyou (trembling). name_card 吉田松阳.
  3.70- 5.60  A3 Close-up (x3) in a god-ray: Shouyou offers his sheathed katana at chest height; 4.30
                 the kid lowers his blade, 4.55 drops it (clang 4.72), steps in, 4.88 takes the sword
                 and 5.20 pulls it upright to his chest.
                 「这把剑，是用来斩断你心中的弱小，守护你自己的灵魂的。」 2.25-5.45
  5.60- 7.85  B1 Shoukasonjuku yard (sunny, sakura). Shouyou & kid Katsura watch from the veranda.
                 Kid Takasugi 「银时！今天一定要赢你！」 charges 6.20, leaps 6.72; lazy Gintoki
                 (bokuto on shoulder) BONK 6.87 (hit-stop 0.1 s, flash, speed lines, 啪！) -> Takasugi
                 spins away, bounces down 7.40 with dizzy stars; Katsura sweat-drop.
  7.85-10.65  B2 Classroom: Katsura studies, Takasugi (bump) sulks, Gintoki sleeps (snot bubble,
                 Zzz). Shouyou creeps over 8.3-9.05 「上课睡觉可不行哦～」, dark aura, bubble pops 9.25,
                 wind-up, HEADBUTT 9.62 (咚!! speed lines, flash, desk splits): Gintoki KO'd flat
                 with a giant steaming bump; Shouyou still smiling; the other two crack up.
 10.65-11.45  C1 Night — the school burns (flames, embers, smoke). Naraku lead the bound Shouyou
                 away; the kids kneel behind a Naraku guard.
 11.45-12.55  C2 CU Shouyou stops, looks back over his shoulder (11.67) and smiles
                 「银时，大家就拜托你了。」 11.60-13.62
 12.55-13.65  C3 CU kid Gintoki crying, reaching out.
 13.65-15.65  D1 Joui war (blood-red sky, rain, amanto army + ships): Shiroyasha dashes in
                 (tracking), 14.26 slash (impact frame, lightning) — four amanto blasted away.
                 name_card 白夜叉.
 15.65-17.60  D2 Sunset ridge: the Joui four — Katsura, Shiroyasha, young Takasugi (both eyes),
                 Sakamoto laughing — light up out of silhouette. name_card 坂本辰马.
 17.60-19.40  E1 (music -> sad, letterbox) Grey cliff: Shouyou kneels (bound) at the edge, Shiroyasha
                 behind him; Oboro holds the bound Katsura & Takasugi; Naraku ranks; crows leave.
 19.40-21.15  E2 CU Shouyou turns (19.75) — the smile with tears 「谢谢你。」 19.45-21.12
 21.15-21.70  E3a Low CU Shiroyasha: the sword rises from behind his head to overhead (arms
                 drawn behind the big chibi head so the crying face stays visible), glint, tremble.
 21.70-22.15  E3b CU young Takasugi (both eyes) screams 「住手——！！」 21.45-23.13 (J-cut)
 22.15-22.50  E3c Gintoki — 22.36 the blade comes down -> 22.50 CUT TO WHITE (no gore).
 22.50-24.35  W  Silence on white; sensei's smile lingers as a faint sepia after-image, a single
                 big tear falls and lands 23.90 (bell, ripple).
 24.35-26.00  F  Present day, back in s10's sunset blade-lock with Oboro (same poses, grinding
                 sparks): close two-shot pulling back,
                 Gintoki's eyes sunk in shadow under his bangs; fade out.
```

## 台词 / 旁白时间表（场景内时间）

| 开始 | 结束 | 说话者 | 台词 |
|---|---|---|---|
| 2.25 | 5.45 | 松阳 | 这把剑，是用来斩断你心中的弱小，守护你自己的灵魂的。 |
| 5.68 | 7.80 | 小高杉 | 银时！今天一定要赢你！ |
| 8.00 | 9.98 | 松阳 | 上课睡觉可不行哦～ |
| 11.60 | 13.62 | 松阳 | 银时，大家就拜托你了。 |
| 19.45 | 21.12 | 松阳 | 谢谢你。 |
| 21.45 | 23.13 | 高杉 | 住手——！！ |

## 音效 cue（场景内时间）

| t | 音效 | 音量 | 持续 |
|---|---|---|---|
| 0.00 | wind | 0.45 | 5.6 |
| 0.35 | footsteps | 0.3 | 1.55 |
| 0.45 | crow | 0.45 |  |
| 0.90 | eat | 0.22 | 0.95 |
| 1.25 | crow | 0.35 |  |
| 1.95 | whoosh | 0.4 |  |
| 1.96 | shock | 0.55 |  |
| 2.25 | jump | 0.6 |  |
| 2.52 | land | 0.6 |  |
| 2.55 | pop | 0.25 |  |
| 2.55 | shing | 0.6 |  |
| 3.95 | shine | 0.5 |  |
| 4.72 | clang | 0.55 |  |
| 4.88 | whoosh | 0.25 |  |
| 5.20 | sparkle | 0.4 |  |
| 5.60 | whoosh | 0.35 |  |
| 6.20 | dash | 0.6 |  |
| 6.72 | jump | 0.5 |  |
| 6.80 | whoosh | 0.6 |  |
| 6.87 | punch | 0.9 |  |
| 6.87 | hit | 0.5 |  |
| 7.25 | sweat | 0.45 |  |
| 7.40 | thud | 0.6 |  |
| 7.45 | dizzy | 0.55 |  |
| 7.85 | whoosh | 0.3 |  |
| 8.05 | footsteps | 0.28 | 1.0 |
| 9.05 | aura | 0.45 |  |
| 9.25 | pop | 0.55 |  |
| 9.50 | whoosh | 0.7 |  |
| 9.62 | punch_big | 1.0 |  |
| 9.62 | impact | 0.7 |  |
| 9.64 | crash | 0.55 |  |
| 9.74 | boing | 0.55 |  |
| 9.95 | thud | 0.5 |  |
| 9.95 | sting_comedy | 0.55 |  |
| 10.20 | sparkle | 0.3 |  |
| 10.65 | fire | 0.6 | 3.0 |
| 10.65 | sting_dramatic | 0.45 |  |
| 10.65 | footsteps | 0.25 | 0.8 |
| 11.67 | sparkle | 0.25 |  |
| 12.55 | heartbeat | 0.4 |  |
| 13.65 | rain | 0.4 | 2.0 |
| 13.65 | battle | 0.5 | 2.0 |
| 13.67 | thunder | 0.45 |  |
| 13.72 | whoosh | 0.35 |  |
| 13.75 | dash | 0.7 |  |
| 14.23 | slash_big | 0.9 |  |
| 14.26 | impact | 0.7 |  |
| 14.28 | thunder | 0.5 |  |
| 14.31 | hit | 0.5 |  |
| 14.38 | hit | 0.45 |  |
| 14.89 | thud | 0.5 |  |
| 15.04 | thud | 0.45 |  |
| 15.65 | wind | 0.4 | 1.95 |
| 15.72 | whoosh | 0.35 |  |
| 16.00 | shine | 0.45 |  |
| 17.60 | wind | 0.5 | 4.9 |
| 17.95 | crow | 0.5 |  |
| 18.15 | crow | 0.4 |  |
| 19.75 | sparkle | 0.3 |  |
| 21.15 | shing | 0.5 |  |
| 21.20 | heartbeat | 0.7 |  |
| 21.60 | shine | 0.45 |  |
| 21.70 | heartbeat | 0.75 |  |
| 22.15 | heartbeat | 0.8 |  |
| 22.36 | whoosh | 0.6 |  |
| 22.48 | slash_big | 0.7 |  |
| 23.90 | bell | 0.5 |  |
| 24.35 | wind | 0.5 | 1.65 |
| 24.40 | clang | 0.35 |  |
| 24.70 | crow | 0.3 |  |
