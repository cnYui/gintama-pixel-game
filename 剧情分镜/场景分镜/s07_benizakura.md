# s07 红樱篇

- 时长：27.8 s（成片里 134.4–162.2 s）
- 音乐：0s → tension、9.8s → battle、15s → tension、18.4s → battle、25.45s → tension（音量 0.55）
- 出场角色（代码里引用到的角色 id）：elizabeth（伊丽莎白）、gintoki（银时）、harusame（春雨）、katsura（桂）、katsura_short（桂）、okada_nizo（冈田似藏）、takasugi（高杉）
- 背景（bg 模块里被调用的函数）：common：big_moon, bridge, bridge_deck_y, clouds, far_mountains, grade_color, lantern, river, sky, wood_floor；edo：roof_walk, ship, skyline
- 淡入 / 淡出：0.3 / 0.3 s

## 故事分镜（CONTRACT.md 第 8 节，写作时的设计意图）

**s07 红樱篇 (26 s)** `[(0,"tension"),(~10,"battle")]` chapter_card 「红樱篇」

Night bridge: a mysterious swordsman cuts at Katsura — only a lock of long hair falls;
Elizabeth sign 「桂先生……」. → Okada Nizo reveals Benizakura: red tendrils crawl up his
arm; name_card 冈田似藏 「人斩｜妖刀红樱」. → Gintoki vs Nizo in the rain: clashes, sparks,
Gintoki wounded → final slash breaks the Benizakura blade (impact frame). → Kiheitai ship,
huge full moon: Takasugi on the rail with his pipe, name_card 高杉晋助 「鬼兵队总督｜
最危险的男人」 「我只是要毁掉这个腐朽的世界。」 → Katsura alive with SHORT hair among
Harusame pirates; Katsura & Gintoki back to back: 「背后交给你了，银时。」「别拖后腿啊，
假发。」「不是假发，是桂！」 → spin slash, pirates fly. → Katsura to Takasugi: 「下次见面，
你我就是敌人。」

## 镜头表（场景文件开头的 SHOT LIST，场景内时间）

```text
s07 红樱篇 (Benizakura arc) — 27.8 s.

SHOT LIST (absolute scene times, seconds)
  A  0.00- 1.80  chapter card 「红樱篇」 over black, red petals drift across (gong on the slam)
  B1 1.80- 3.70  night bridge, huge moon on the horizon, letterbox. Katsura (long hair) +
                 Elizabeth walk right; a silhouetted swordsman walks left in front of the moon.
                 Stop / heartbeat (3.00) / push-in -> he vanishes (3.35) -> IMPACT FRAME (3.42,
                 black silhouettes on white) horizontal red slash through Katsura, red flash,
                 petals + hair strands.
  B2 3.70- 4.90  close-up of the empty bridge planks: a lock of long black hair drifts down
                 across the moon and lands (4.60). Red petals.
  B3 4.90- 6.20  Elizabeth alone in a drizzle, backlit by the moon, gloom; sign pops up
                 「桂先生……」 next to the lock.
  C  6.20- 9.80  red moon over Edo rooftops: Okada Nizo draws Benizakura (7.00), red tendrils
                 crawl up his arm, heartbeat pulses (7.3/7.9/8.5), slow parallax push-in.
                 name_card 冈田似藏 (7.20).  Nizo: 「红樱……还没吃饱呢。」  blade glint (9.45)
  D  9.80-15.00  BATTLE (music) — the bridge in a night thunderstorm, heavy rain.
     9.80 lightning; 10.15 both dash; 10.45 CLASH (sparks, 「铿!!」); 10.45-11.70 close
     exchange x3 (10.85/11.15/11.45); 11.70 tendrils lash, 11.85 Gintoki is cut & knocked
     back, kneels 12.15; 12.45-13.30 close-up: eyes sharpen (12.80), he rises (13.05);
     13.35 both charge and pass -> IMPACT FRAME 13.62 (giant diagonal slash);
     14.20 crack 「咔嚓!」, 14.30 lightning + Benizakura shatters, Nizo collapses (14.70).
  E1 15.00-16.00 huge full moon, the Kiheitai ship glides across it (tension music).
  E2 16.00-18.40 Takasugi sits on the ship rail smoking his kiseru, moon behind, golden
                 butterflies. name_card 高杉晋助 (16.05). 「我只是要毁掉这个腐朽的世界。」
  F1 18.40-19.25 (battle) Kiheitai deck: Harusame pirates surround Gintoki; one charges ->
                 Katsura drops from the sky and cuts him away (land 18.66); snap zoom on
                 his SHORT hair with speed lines (18.90).
  F2 19.25-23.30 back to back, pirates prowling (two feints scared off by a blade glint),
                 dark foreground mob framing the shot, slow push-in.
                 Katsura 「背后交给你了，银时。」 / Gintoki 「别拖后腿啊，假发。」
  F3 23.30-25.45 snap-zoom two-shot: Katsura whirls round and yells 「不是假发，是桂！」 at the
                 back of Gintoki's head (speed lines, vein, 「是桂!!」, shake); Gintoki picks
                 his nose, deadpan (23.84 「抠抠」, flicks it); pirates lose patience and charge
                 「杀啊——!!」 (23.98) -> both snap to guard -> double SPIN SLASH (24.34), wide ->
                 pirates fly off, two become twinkling stars (25.05/25.20).
  G  25.45-27.80 low angle: Takasugi on the upper deck in front of the moon; Katsura (with
                 Gintoki + Elizabeth) below: 「下次见面，你我就是敌人。」 -> 26.80 reverse shot:
                 Takasugi close-up filling the moon, smirks and exhales smoke (27.02).
```

## 台词 / 旁白时间表（场景内时间）

| 开始 | 结束 | 说话者 | 台词 |
|---|---|---|---|
| 7.80 | 9.80 | 冈田似藏 | 红樱……还没吃饱呢。 |
| 16.10 | 18.40 | 高杉 | 我只是要毁掉这个腐朽的世界。 |
| 19.30 | 21.30 | 桂 | 背后交给你了，银时。 |
| 21.35 | 23.30 | 银时 | 别拖后腿啊，假发。 |
| 23.35 | 25.40 | 桂 | 不是假发，是桂！ |
| 25.52 | 27.75 | 桂 | 下次见面，你我就是敌人。 |

## 名牌 / 篇章卡（从代码里直接调用处提取，可能不全）

- 名牌 16.05s（2.3s）：takasugi — 高杉晋助 鬼兵队总督｜最危险的男人

## 音效 cue（场景内时间）

| t | 音效 | 音量 | 持续 |
|---|---|---|---|
| 0.00 | night | 0.45 | 6.2 |
| 0.05 | sting_dramatic | 0.8 |  |
| 0.40 | gong | 0.7 |  |
| 1.60 | river | 0.3 | 4.6 |
| 1.60 | wind | 0.35 | 8.2 |
| 3.00 | heartbeat | 0.9 |  |
| 3.35 | dash | 0.8 |  |
| 3.42 | slash_big | 1.0 |  |
| 3.44 | impact | 0.7 |  |
| 3.80 | whoosh | 0.25 |  |
| 4.60 | thud | 0.2 |  |
| 4.90 | rain | 0.3 | 4.9 |
| 5.05 | pop | 0.45 |  |
| 7.00 | shing | 1.0 |  |
| 7.05 | aura | 0.8 |  |
| 7.20 | whoosh | 0.5 |  |
| 7.30 | heartbeat | 1.0 |  |
| 7.90 | heartbeat | 1.0 |  |
| 8.50 | heartbeat | 1.0 |  |
| 9.45 | shine | 0.8 |  |
| 9.80 | thunder | 1.0 |  |
| 9.80 | rain | 0.85 | 5.199999999999999 |
| 10.15 | dash | 1.0 |  |
| 10.45 | clang | 1.0 |  |
| 10.45 | impact | 0.8 |  |
| 10.85 | clang | 0.8 |  |
| 11.15 | clang | 0.8 |  |
| 11.45 | clang | 0.9 |  |
| 11.70 | whoosh | 0.7 |  |
| 11.85 | slash | 1.0 |  |
| 11.87 | hit | 1.0 |  |
| 12.15 | thud | 0.8 |  |
| 12.80 | shine | 1.0 |  |
| 13.35 | dash | 1.0 |  |
| 13.62 | slash_big | 1.0 |  |
| 13.62 | impact | 1.0 |  |
| 14.20 | glass | 0.6 |  |
| 14.32 | glass | 1.0 |  |
| 14.32 | thunder | 0.8 |  |
| 14.34 | shing | 0.6 |  |
| 14.82 | thud | 1.0 |  |
| 15.00 | wind | 0.55 | 3.3999999999999986 |
| 15.00 | engine_hum | 0.35 | 1.0 |
| 16.05 | whoosh | 0.5 |  |
| 18.40 | battle | 0.3 | 7.050000000000001 |
| 18.42 | whoosh | 0.7 |  |
| 18.64 | slash | 1.0 |  |
| 18.66 | land | 1.0 |  |
| 18.67 | hit | 1.0 |  |
| 18.71 | fly_away | 0.7 |  |
| 18.90 | shine | 1.0 |  |
| 20.30 | dash | 0.4 |  |
| 20.52 | shine | 0.7 |  |
| 22.35 | dash | 0.35 |  |
| 22.57 | shine | 0.6 |  |
| 23.30 | whoosh | 0.55 |  |
| 23.34 | vein | 1.0 |  |
| 23.34 | punch | 0.45 |  |
| 23.36 | shock | 0.6 |  |
| 23.86 | squeak | 0.3 |  |
| 23.96 | pop | 0.35 |  |
| 23.98 | run | 0.5 | 0.35999999999999943 |
| 24.00 | charge | 0.35 |  |
| 24.34 | slash_big | 1.0 |  |
| 24.36 | whoosh | 1.0 |  |
| 24.40 | punch_big | 0.8 |  |
| 24.44 | fly_away | 1.0 |  |
| 25.05 | twinkle | 1.0 |  |
| 25.20 | twinkle | 1.0 |  |
| 25.45 | wind | 0.5 | 2.3500000000000014 |
| 26.80 | whoosh | 0.3 |  |
| 27.02 | sting_dramatic | 0.55 |  |
