# s10 将军暗杀篇

- 时长：18.0 s（成片里 214.7–232.7 s）
- 音乐：0s → tension、6.85s → battle、14.75s → （静音）（音量 0.55）
- 出场角色（代码里引用到的角色 id）：elizabeth（伊丽莎白）、gintoki（银时）、hijikata（土方）、kagura（神乐）、katsura（桂）、kondo（近藤）、naraku（奈落）、oboro（胧）、okita（冲田）、shigeshige（茂茂）、shinpachi（新八）
- 背景（bg 模块里被调用的函数）：common：bayer, clouds, dirt_ground, far_mountains, grade_color, room_wall, sky, wood_floor
- 淡入 / 淡出：0.3 / 0.0 s

## 故事分镜（CONTRACT.md 第 8 节，写作时的设计意图）

**s10 将军暗杀篇 (18 s)** `[(0,"tension"),(~6,"battle")]` chapter_card 「将军暗杀篇」

Quick gag: Shogun Shigeshige, name_card 德川茂茂 「第十四代将军｜老实人」, sincerely
suffering some silly mishap (e.g. a bad haircut) 「将军家的头发……」. → Mountain pass,
escort: Naraku ninjas (kasa hats, crows) ambush; everyone fights — Shinsengumi, Yorozuya,
Katsura. → Oboro, name_card 胧 「天照院奈落首领」, vs Gintoki: 「你还是和那时一样，白夜叉。」
→ Gintoki's eyes widen — flash of a gentle smile (sensei) → white out into the flashback.

## 镜头表（场景文件开头的 SHOT LIST，场景内时间）

```text
s10 将军暗杀篇 (18 s) — music: tension -> battle (at the ambush) -> silence (eyes).

SHOT LIST
  0.00- 1.90  A  chapter_card 「将军暗杀篇」; a flock of red-eyed crows (the Naraku omen)
                 crosses the red bar, black feathers drift.
  1.90- 6.00  B  Barber-shop gag (day interior: window w/ Terminal, mirror + reflection,
                 spinning barber pole). 1.90-3.10 wide, slow push-in: Gintoki on a stool
                 lazily snips the Shogun's chonmage; name_card 德川茂茂 (1.95-4.05).
                 2.55 Gintoki yawns 「哈啊～」 (eyes shut, scissors drift up) ->
                 3.10 SNIP! (flash, 咔嚓!, zoom punch) topknot flies, lands 3.60 (bounce).
                 3.10-4.10 Gintoki frozen & pale, sweat; 3.62 a crow flaps past the window
                 「阿呆～」. 4.10-6.00 close two-shot push-in: bald-patched Shogun, gloom
                 lines, tear; Gintoki (holding the topknot) slaps it back on crooked with
                 tape at 4.66 「啪！」 + smug thumbs-up; 5.30 it slides off 「哧溜～」, falls
                 5.62 -> waterfall tears. Gintoki 「将军家的头发……」 (4.10-6.00)
  6.00- 8.60  C  Mountain pass at dusk (letterbox, parallax pan): the escort walks —
                 Kondo, Hijikata, Shogun (still botched hair), Okita, Gintoki, Shinpachi,
                 Kagura (parasol). Crows circle. 6.85 crows cry, Naraku poof onto the ridge
                 (red eyes); 7.10-7.60 they leap down around the party; everyone draws,
                 Hijikata iai 7.75. Hijikata 「是奈落！保护将军！」 (7.10-9.05)
  8.60-11.30  D  Manga-panel battle montage: P1 top (8.60) Shinsengumi — Kondo slash,
                 Hijikata iai then a smoke break, Okita's bazooka x2 (2nd wave leaps in,
                 10.40 「轰轰！！」); P2 bottom-left (9.05) Yorozuya — Kagura's umbrella gun
                 then sukonbu, Gintoki's rising slash (victim twinkles) + a lazy swat at
                 the next one 「砰！」, Shinpachi on guard (glint); P3 bottom-right (9.45)
                 Katsura cuts then deadpans with a lit bomb, Elizabeth raises 「天诛」 and
                 clubs a ninja with it 「咚！」.
                 10.95 a giant white slash cuts all panels -> white.
 11.30-14.75  E  Sunset ridge, huge red sun, dead tree w/ crows behind Oboro (closer cam). 11.53 Oboro's needles,
                 11.75 Gintoki deflects (clang); name_card 胧 (11.80-14.00); 12.05 dash,
                 12.40 CLASH (impact frame, shockwave, crows scatter); blade-lock push-in
                 with shove beats at 13.20 (Oboro) / 14.10 (Gintoki).
                 Oboro 「你还是和那时一样，白夜叉。」 (12.50-14.75)
 14.75-18.00  F  Extreme close-up of Gintoki's eyes (silence + heartbeat): 15.00 they
                 widen, pupils shrink; 15.50 subliminal flash / 15.70-16.65 Shouyou's
                 gentle smile (drawn close-up face, sepia glow, petals, smile grows);
                 16.65 trembling eyes, tears well up; 17.15-17.55
                 white-out, holds white (fade_out=0) into s11's flashback.
```

## 台词 / 旁白时间表（场景内时间）

| 开始 | 结束 | 说话者 | 台词 |
|---|---|---|---|
| 4.10 | 6.00 | 银时 | 将军家的头发…… |
| 7.10 | 9.05 | 土方 | 是奈落！保护将军！ |
| 12.50 | 14.75 | 胧 | 你还是和那时一样，白夜叉。 |

## 名牌 / 篇章卡（从代码里直接调用处提取，可能不全）

- 名牌 1.95s（2.1s）：shigeshige — 德川茂茂 第十四代将军｜老实人
- 名牌 11.8s（2.2s）：oboro — 胧 天照院奈落首领

## 音效 cue（场景内时间）

| t | 音效 | 音量 | 持续 |
|---|---|---|---|
| 0.05 | sting_dramatic | 0.7 |  |
| 0.45 | whoosh | 0.35 |  |
| 0.55 | crow | 0.6 |  |
| 0.95 | crow | 0.45 |  |
| 1.93 | bell_shop | 0.4 |  |
| 2.00 | slash | 0.16 |  |
| 2.30 | slash | 0.16 |  |
| 2.60 | slash | 0.16 |  |
| 2.90 | slash | 0.16 |  |
| 3.10 | slash | 0.7 |  |
| 3.11 | pop | 0.8 |  |
| 3.18 | shock | 0.6 |  |
| 3.50 | sweat | 0.5 |  |
| 3.60 | thud | 0.35 |  |
| 3.62 | crow | 0.8 |  |
| 4.66 | slap | 0.7 |  |
| 4.72 | sparkle | 0.45 |  |
| 5.30 | slide_down | 0.5 |  |
| 5.70 | fail | 0.55 |  |
| 6.00 | wind | 0.35 | 2.8 |
| 6.00 | footsteps | 0.3 | 0.8499999999999996 |
| 6.80 | crow | 0.8 |  |
| 6.85 | shing | 0.45 |  |
| 6.90 | whoosh | 0.4 |  |
| 6.97 | crow | 0.55 |  |
| 7.10 | whoosh | 0.7 |  |
| 7.60 | land | 0.7 |  |
| 7.72 | land | 0.5 |  |
| 7.78 | shing | 0.8 |  |
| 7.90 | land | 0.4 |  |
| 8.60 | battle | 0.35 | 2.3499999999999996 |
| 8.60 | slash | 0.5 |  |
| 8.80 | slash | 0.8 |  |
| 8.80 | hit | 0.6 |  |
| 8.92 | slash | 0.6 |  |
| 8.96 | bazooka | 0.8 |  |
| 9.05 | explosion | 0.8 |  |
| 9.05 | whoosh | 0.6 |  |
| 9.10 | machinegun | 0.5 |  |
| 9.27 | slash_big | 0.6 |  |
| 9.27 | hit | 0.6 |  |
| 9.45 | whoosh | 0.6 |  |
| 9.51 | pop | 0.4 |  |
| 9.72 | slash | 0.8 |  |
| 9.72 | hit | 0.5 |  |
| 9.75 | whoosh | 0.4 |  |
| 9.79 | twinkle | 0.5 |  |
| 10.00 | whoosh | 0.4 |  |
| 10.10 | land | 0.4 |  |
| 10.29 | punch_big | 0.8 |  |
| 10.31 | bazooka | 0.7 |  |
| 10.35 | whoosh | 0.5 |  |
| 10.38 | punch | 0.7 |  |
| 10.40 | bomb_fuse | 0.35 |  |
| 10.40 | explosion | 0.85 |  |
| 10.95 | slash_big | 0.9 |  |
| 11.30 | wind | 0.4 | 3.4499999999999993 |
| 11.35 | crow | 0.5 |  |
| 11.53 | whoosh | 0.5 |  |
| 11.75 | clang | 0.8 |  |
| 12.05 | dash | 0.7 |  |
| 12.40 | clang | 1.0 |  |
| 12.40 | impact | 0.9 |  |
| 12.48 | crow | 0.6 |  |
| 12.50 | fly_away | 0.3 |  |
| 13.20 | clang | 0.45 |  |
| 13.22 | shing | 0.3 |  |
| 14.10 | clang | 0.6 |  |
| 14.12 | shing | 0.35 |  |
| 14.80 | heartbeat | 0.8 |  |
| 15.00 | heartbeat | 1.0 |  |
| 15.00 | shock | 0.5 |  |
| 15.50 | shine | 0.5 |  |
| 15.70 | bell | 0.45 |  |
| 16.67 | heartbeat | 0.9 |  |
| 17.15 | shine | 0.7 |  |
