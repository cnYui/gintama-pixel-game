# s04 真选组

- 时长：21.6 s（成片里 77.0–98.6 s）
- 音乐：shinsengumi（音量 0.55）
- 出场角色（代码里引用到的角色 id）：hijikata（土方）、kondo（近藤）、okita（冲田）、otae（阿妙）、townsman（路人）、yamazaki（山崎）
- 背景（bg 模块里被调用的函数）：common：clouds, dirt_ground, grade_rgba, room_wall, sky, stone_street, wood_floor；kabukicho：street；edo：skyline
- 淡入 / 淡出：0.3 / 0.3 s

## 故事分镜（CONTRACT.md 第 8 节，写作时的设计意图）

**s04 真选组 (20 s)** `shinsengumi`

Shinsengumi HQ gate 「真选组屯所」. → Kondo hiding in a bush stalking Otae at a shop;
she notices → super punch → Kondo flies into the sky and becomes a twinkling star.
name_card 近藤勋 「局长｜大猩猩·跟踪狂」. → Canteen: Hijikata squeezes a mountain of
mayonnaise on rice 「土方特制盖饭」, smoking. name_card 土方十四郎 「鬼之副长｜蛋黄酱狂魔」
→ Okita naps with an eye-mask, wakes, bazooka 「土方先生，去死吧。」 → BOOM → Hijikata
afro + soot 「总悟你这混蛋！！」 name_card 冲田总悟 「一番队队长｜抖S王子」. → the three
pose in front of the flag 「诚」.

## 镜头表（场景文件开头的 SHOT LIST，场景内时间）

```text
s04 真选组 (21.6 s) — music 'shinsengumi'.

SHOT LIST
 A   0.00– 2.50  屯所 gate: opens close on the waving 诚 flag, pulls back + tilts down to the gate
                 「真选组屯所」; Yamazaki secretly practising badminton. Narration.
 B   2.50– 6.50  Kabukicho sweets shop: Otae eats dango; Kondo's bush hops up behind her (name
                 card 近藤勋) → 「！」 she turns, world darkens, dark aura 杀气 → super punch
                 (2-tone impact frame, speed lines, 砰！！); a passer-by stares.
 B2  6.50– 8.00  Wide shot of the aftermath, tilt up as Kondo tumbles into the sky → kira star 「闪～☆」.
 C1  8.00– 9.50  Food-show insert: giant mayo bottle builds a mountain; banner 「土方特制盖饭」.
 C2  9.50–12.00  Canteen: Hijikata smoking beside the glittering mayo mountain (name card 土方十四郎).
 D  12.00–15.30  Pan to napping Okita → snap punch-in: eye-mask flips off, sadist eyes + glint
                 (name card 冲田总悟) → poof: bazooka, creepy grin → fires.
 E  15.30–17.75  Whip-pan with the shell → BOOM → smoke clears on afro Hijikata, 阿呆～ crow over
                 the silence → he leaps onto the table, pointing, red lines 「总悟你这混蛋！！」.
 E2 17.75–18.60  Okita looks away, whistling innocently.
 F  18.60–21.60  Courtyard + giant 诚 flag: Kondo drops back from the sky (bump), pose (iai draw,
                 katana on shoulder, bazooka), title 「真选组」; Okita's laser dot lands on the afro 「喂！」.
```

## 台词 / 旁白时间表（场景内时间）

| 开始 | 结束 | 说话者 | 台词 |
|---|---|---|---|
| 0.30 | 2.35 | 旁白 | 江户的武装警察「真选组」 |
| 2.85 | 4.90 | 近藤 | 阿妙小姐今天也好美啊～ |
| 5.00 | 6.95 | 阿妙 | 跟踪狂给我去死吧～ |
| 9.80 | 11.85 | 土方 | 蛋黄酱，就是正义。 |
| 13.30 | 15.28 | 冲田 | 土方先生，去死吧。 |
| 16.62 | 18.56 | 土方 | 总悟你这混蛋！！ |

## 名牌 / 篇章卡（从代码里直接调用处提取，可能不全）

- 名牌 2.95s（2.2s）：kondo — 近藤勋 局长｜大猩猩·跟踪狂
- 名牌 9.62s（2.2s）：hijikata — 土方十四郎 鬼之副长｜蛋黄酱狂魔

## 音效 cue（场景内时间）

| t | 音效 | 音量 | 持续 |
|---|---|---|---|
| 0.00 | wind | 0.22 | 2.5 |
| 0.45 | pop | 0.3 |  |
| 1.35 | pop | 0.3 |  |
| 2.25 | pop | 0.3 |  |
| 2.50 | crowd | 0.22 | 5.5 |
| 2.95 | whoosh | 0.4 |  |
| 3.10 | squeak | 0.35 |  |
| 3.70 | squeak | 0.35 |  |
| 4.30 | squeak | 0.35 |  |
| 4.90 | shock | 0.7 |  |
| 5.20 | aura | 0.7 |  |
| 5.50 | sweat | 0.5 |  |
| 5.90 | whoosh | 0.6 |  |
| 6.00 | punch_big | 1.0 |  |
| 6.00 | impact | 0.7 |  |
| 6.10 | fly_away | 0.8 |  |
| 6.50 | whoosh | 0.5 |  |
| 7.25 | twinkle | 0.8 |  |
| 8.05 | slide_up | 0.6 |  |
| 8.55 | shine | 0.7 |  |
| 9.02 | sparkle | 0.6 |  |
| 9.62 | whoosh | 0.35 |  |
| 12.00 | whoosh | 0.5 |  |
| 12.85 | whoosh | 0.55 |  |
| 13.05 | shine | 0.7 |  |
| 13.10 | whoosh | 0.3 |  |
| 13.45 | pop | 0.6 |  |
| 13.55 | charge | 0.45 |  |
| 14.45 | shine | 0.5 |  |
| 15.10 | bazooka | 0.9 |  |
| 15.30 | whoosh | 0.7 |  |
| 15.45 | explosion | 1.0 |  |
| 15.97 | crow | 0.7 |  |
| 16.55 | jump | 0.6 |  |
| 16.71 | thud | 0.8 |  |
| 16.71 | vein | 0.8 |  |
| 16.71 | impact | 0.5 |  |
| 17.83 | blip | 0.4 |  |
| 18.02 | blip | 0.4 |  |
| 18.21 | blip | 0.4 |  |
| 18.40 | blip | 0.4 |  |
| 18.60 | wind | 0.3 | 3.0 |
| 18.60 | fall_whistle | 0.7 |  |
| 19.15 | thud | 0.9 |  |
| 19.45 | sting_dramatic | 0.8 |  |
| 19.50 | impact | 0.5 |  |
| 19.75 | shing | 0.6 |  |
| 20.05 | sparkle | 0.5 |  |
| 20.60 | laser | 0.25 |  |
| 20.85 | shock | 0.5 |  |
| 20.90 | sweat | 0.6 |  |
