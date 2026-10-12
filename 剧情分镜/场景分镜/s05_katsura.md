# s05 桂与伊丽莎白

- 时长：17.8 s（成片里 98.6–116.4 s）
- 音乐：comedy（音量 0.5）
- 出场角色（代码里引用到的角色 id）：elizabeth（伊丽莎白）、gintoki（银时）、hijikata（土方）、katsura（桂）、okita（冲田）、townsman（路人）
- 背景（bg 模块里被调用的函数）：common：add_sprite, glow_sprite；edo：roof_walk, skyline；kabukicho：street
- 淡入 / 淡出：0.3 / 0.3 s

## 故事分镜（CONTRACT.md 第 8 节，写作时的设计意图）

**s05 桂与伊丽莎白 (16 s)** `comedy`

Rooftop chase: Katsura (+Elizabeth waddling) fleeing, Hijikata & Okita chasing, bazooka
shells behind. Okita 「假发——」 → Katsura turns, speed lines: 「不是假发，是桂！」 (make this
line BIG). name_card 桂小太郎 「攘夷志士｜逃跑的小太郎·天然呆」; Elizabeth holds sign
「……」 then 「快跑」, name_card 伊丽莎白 「谜之生物｜只用牌子说话」. → Katsura throws a lit
bomb; Gintoki walking below catches it, panics, throws it up → explosion in the sky like
fireworks. Gintoki (soot): 「为什么每次倒霉的都是我啊！」

## 镜头表（场景文件开头的 SHOT LIST，场景内时间）

```text
s05 桂与伊丽莎白 (17.8 s, music 'comedy', tod = dusk over Kabukicho).

SHOT LIST (scene-local seconds)
 S1a  0.00- 2.00  Rooftop chase, wide tracking pan (zoom 1.3, cam 85 px/s, parallax skyline).
                  Katsura (run_away, hair streaming) + Elizabeth flee right; Hijikata (katana
                  drawn, shouting) and Okita (running with bazooka) chase.  Okita stops,
                  fires at 1.20 -> shell zips over Hijikata's head (he ducks) -> roof tiles
                  explode behind Elizabeth at 1.50 (both hop).  Scorch mark keeps smoking.
                  sub: 土方「给我站住，桂！」
 S1b  2.00- 3.60  Okita close shot (zoom 2.0->2.3 push-in): lazy drawl 「假发——」, sadist face,
                  purple sadist aura; SCOPE inset 2.32-3.0 (Katsura drifts into the crosshair,
                  「锁定」 at 2.78); fires at 3.00 (muzzle flash, recoil), off-screen boom 3.35.
 S2a  3.60- 3.95  Katsura skids to a halt (record scratch, dust) and spins round.
 S2b  3.95- 5.60  REACTION CLOSE-UP: blue speed-line field, Katsura x4 pointing at camera-left,
                  BIG brush text 「不是假发」(4.02) 「是桂！」(4.38 slam, flash, shake).
                  sub: 桂「不是假发，是桂！」
 S3   5.60- 9.50  Two-shot on the ridge (zoom 1.5->1.68 push-in, sakura drifting).
                  name_card 桂小太郎 5.62 (smug pose); Elizabeth's sign 「……」 6.05 + a crow
                  flaps across the sunset (awkward beat);
                  a stray shell whizzes behind them 7.25 -> boom off-screen right 7.45 ->
                  sign flips to 「快跑」 (sweat, trembling); name_card 伊丽莎白 7.50.
                  Katsura deadpan pulls a lit bomb 7.85 「后会有期！」, throws it 8.55-9.05
                  (release 8.80, bomb arcs off frame), both dash off right in a dust cloud.
 S4   9.50-12.50  Kabukicho street below (Yorozuya behind, push-in 1.35->1.62): Gintoki strolls,
                  bomb falls (whistle) straight into his hand 10.45, 「？」 beat, SNAP zoom x3.1
                  onto his face 11.0 (shock, speed lines, sweat) sub「炸、炸弹！？」, back out:
                  panics left/right 11.75, old townsman flees, hurls it skyward 12.2.
 S5  12.50-14.20  Low-angle sky over Edo (Terminal on the right third): shell rises, bursts into
                  fireworks (gold 12.9, pink, cyan, then sparks form the kanji 「桂」 13.36);
                  Hijikata & Okita (x2, backlit silhouettes with firework rim light) watch.
                  One ember doesn't burn out: it falls back down (whistle) ...
 S6  14.20-17.80  ... BOOM on the street: black smoke clears -> soot-faced Gintoki with his
                  silver perm blown into a giant AFRO (scenes/_s05_soot.py), dazed white eyes,
                  crow 「阿呆～」, coughs smoke 15.06; 15.35 punch-in + speed lines, fists up:
                  「为什么每次倒霉的都是我啊！」; 16.1 waterfall tears + sad trombone; the last
                  spark lands on the afro 17.05 and it catches fire (he doesn't notice).
```

## 台词 / 旁白时间表（场景内时间）

| 开始 | 结束 | 说话者 | 台词 |
|---|---|---|---|
| 0.25 | 2.00 | 土方 | 给我站住，桂！ |
| 2.05 | 3.60 | 冲田 | 假发—— |
| 3.95 | 5.75 | 桂 | 不是假发，是桂！ |
| 7.88 | 9.50 | 桂 | 后会有期！ |
| 10.80 | 12.48 | 银时 | 炸、炸弹！？ |
| 15.10 | 17.72 | 银时 | 为什么每次倒霉的都是我啊！ |

## 名牌 / 篇章卡（从代码里直接调用处提取，可能不全）

- 名牌 5.62s（2s）：katsura — 桂小太郎 攘夷志士｜逃跑的小太郎·天然呆
- 名牌 7.5s（2s）：elizabeth — 伊丽莎白 谜之生物｜只用牌子说话

## 音效 cue（场景内时间）

| t | 音效 | 音量 | 持续 |
|---|---|---|---|
| 0.00 | run | 0.45 | 2.0 |
| 0.00 | wind | 0.2 | 5.6 |
| 0.35 | vein | 0.5 |  |
| 1.20 | bazooka | 1.0 |  |
| 1.22 | whoosh | 0.6 |  |
| 1.50 | explosion_small | 1.0 |  |
| 1.52 | jump | 0.5 |  |
| 1.88 | land | 0.4 |  |
| 2.00 | run | 0.25 | 1.6 |
| 2.34 | blip | 0.5 |  |
| 2.78 | blip | 0.6 |  |
| 2.86 | blip | 0.6 |  |
| 3.00 | bazooka | 1.0 |  |
| 3.02 | whoosh | 0.6 |  |
| 3.35 | explosion_small | 0.5 |  |
| 3.61 | record_scratch | 1.0 |  |
| 3.80 | whoosh | 0.5 |  |
| 3.95 | shine | 0.5 |  |
| 4.02 | impact | 0.7 |  |
| 4.38 | punch_big | 1.0 |  |
| 4.40 | impact | 0.8 |  |
| 5.62 | slide_up | 0.4 |  |
| 6.05 | pop | 1.0 |  |
| 6.40 | crow | 1.0 |  |
| 7.25 | whoosh | 0.7 |  |
| 7.45 | explosion_small | 0.7 |  |
| 7.48 | pop | 1.0 |  |
| 7.50 | slide_up | 0.35 |  |
| 7.52 | sweat | 0.6 |  |
| 7.85 | bomb_fuse | 0.7 |  |
| 8.80 | whoosh | 0.7 |  |
| 9.05 | dash | 1.0 |  |
| 9.50 | crowd | 0.25 | 3.0 |
| 9.50 | footsteps | 0.35 | 0.7 |
| 9.75 | fall_whistle | 0.7 |  |
| 10.45 | pop | 1.0 |  |
| 10.47 | slap | 0.4 |  |
| 10.55 | bomb_fuse | 0.6 |  |
| 11.00 | shock | 1.0 |  |
| 11.05 | sweat | 0.6 |  |
| 11.75 | run | 0.5 | 0.45 |
| 12.22 | whoosh | 1.0 |  |
| 12.50 | slide_up | 0.7 |  |
| 12.90 | explosion | 1.0 |  |
| 12.98 | fall_whistle | 0.55 |  |
| 13.08 | explosion_small | 0.6 |  |
| 13.15 | cheer | 0.45 |  |
| 13.22 | explosion_small | 0.6 |  |
| 13.36 | explosion_small | 0.5 |  |
| 13.40 | sparkle | 1.0 |  |
| 13.72 | pop | 0.5 |  |
| 13.86 | pop | 0.5 |  |
| 14.20 | explosion | 1.0 |  |
| 14.50 | crow | 1.0 |  |
| 15.06 | cough | 1.0 |  |
| 15.35 | impact | 0.6 |  |
| 15.36 | vein | 0.5 |  |
| 16.10 | fail | 0.55 |  |
| 17.05 | pop | 0.6 |  |
| 17.07 | fire | 0.35 | 0.73 |
