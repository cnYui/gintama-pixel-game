# s06 日常

- 时长：18.0 s（成片里 116.4–134.4 s）
- 音乐：comedy（音量 0.5）
- 出场角色（代码里引用到的角色 id）：gintoki（银时）、hasegawa（长谷川）、kagura（神乐）、kondo（近藤）、otae（阿妙）、otsu（阿通）、sadaharu（定春）、shinpachi（新八）
- 背景（bg 模块里被调用的函数）：common：clouds, indoor, room_wall, sky, tatami；yorozuya：office
- 淡入 / 淡出：0.3 / 0.3 s

## 故事分镜（CONTRACT.md 第 8 节，写作时的设计意图）

**s06 日常 (18 s)** `comedy` — rapid manga-panel vignettes (~3 s each), panel borders:

1 Hasegawa in a cardboard box by the river 「MADAO（彻底没用的大叔）」 name_card 长谷川泰三.
2 Pachinko: Gintoki & Hasegawa lose everything, turn grey. 3 Monday: Gintoki reading Jump,
sparkling eyes 「周一＝Jump发售日」. 4 Otsu on stage singing, Shinpachi in happi coat with
light sticks 「通酱～！」 name_card 寺门通. 5 Kagura chewing sukonbu next to sleeping
Sadaharu 「醋昆布是正义阿鲁」. 6 Kondo hiding under Otae's floor → naginata stabs through.
End caption 「※以上皆为日常」.

## 镜头表（场景文件开头的 SHOT LIST，场景内时间）

```text
s06 「日常」 — rapid manga-panel vignettes of everyday Kabukicho (18 s, music 'comedy').

The whole scene is a manga page: every vignette is a new page that slides in from the
right; its panels (2 px ink border, white gutters, dotted paper) pop / slide / split in.
Each panel's content is rendered as a normal full-frame shot (world coords) and zoomed
with fx.zoom, then masked into the panel polygon.

SHOT LIST (scene time, seconds)
 V1 其一 MADAO            0.00– 3.00  riverbank at dusk, reeds + autumn leaves in the wind,
                                      slow push-in on Hasegawa in his cardboard box.
                                      name_card 长谷川泰三 0.30; a crow flies in (1.20) and
                                      lands with a caw (1.75); its 2nd caw 「阿呆～」 (2.53)
                                      gets a snap-zoom and MADAO starts crying (gloom lines).
 V2 其二 小钢珠            3.00– 5.90  pachinko parlor: Gintoki & Hasegawa bounce on stools,
                                      「来了!!」 pops; inset LCD (3.45) 7-7-[real reel strip]
                                      decelerates, lands on a PERFECT 7 (4.40, ding, frozen
                                      「！？」) ... creeps ... clunks onto 6 (4.62 scratch),
                                      4.70 page drains to grey, both burnt-out WHITE,
                                      4.95 red stamp 「输光」 + 「所持金：0円」,
                                      5.20–5.84 both crumble into ash blown away by the wind.
 V3 其三 周一              5.90– 8.80  calendar: 「周日」 page ripped off (6.20) → 「周一 /
                                      Jump!」; 6.45 split: the holy JUMP descends in a light
                                      beam (fanfare), Gintoki kneels reaching for it, star
                                      eyes (6.90), trembling, tears of joy; 「周一＝Jump发售日」.
 V4 其四 偶像              8.80–11.80  concert: Otsu singing under swinging spotlights, notes
                                      float from her mic (name_card 寺门通 9.15) → split
                                      (9.75): Shinpachi in happi coat with light sticks
                                      「通酱～！！」, hearts, chant letters L·O·V·E on the beat.
 V5 其五 醋昆布            11.80–14.40  Yorozuya office: Kagura sits on sleeping Sadaharu
                                      chewing sukonbu; his snot bubble grows and POPS (13.35)
                                      → he jolts up, Kagura is catapulted out of frame,
                                      「？」, whistle ... she drops back (14.02) and just keeps
                                      chewing 「嚼嚼」.
 V6 其六 跟踪狂            14.40–18.00  two stacked panels: top = Otae with tea on tatami,
                                      bottom = Kondo in the crawlspace under her floor,
                                      hearts. 15.35 dark aura, 15.80 she rises with the
                                      naginata, 16.20 STAB through the floor and the panel
                                      gutter, stopping an inch from Kondo's nose (frozen,
                                      cross-eyed, jaw drop). 16.70 caption 「※以上皆为日常」,
                                      16.80 the crow flaps across the page 「阿呆～ 阿呆～」.
Characters/poses: hasegawa box/cheer/idle/sit(ash) · gintoki cheer/idle/sit(ash)/kneel
(+custom star-eye patch) · otsu sing · shinpachi otaku_cheer · kagura sukonbu(legs=sit)
· sadaharu sleep/shock/idle · otae sit/attack/thrust(naginata down) · kondo stalk/kneel.
```

## 台词 / 旁白时间表（场景内时间）

| 开始 | 结束 | 说话者 | 台词 |
|---|---|---|---|
| 0.80 | 2.95 | 长谷川 | 纸箱……其实还挺暖和的。 |
| 3.00 | 4.76 | 银时 | 来了来了！！ |
| 6.55 | 8.70 | 银时 | Jump是男人的圣经啊！ |
| 10.00 | 11.72 | 新八 | 通酱～！！ |
| 12.00 | 14.01 | 神乐 | 醋昆布就是正义阿鲁！ |
| 14.50 | 16.66 | 近藤 | 阿妙小姐……今天也好美。 |

## 名牌 / 篇章卡（从代码里直接调用处提取，可能不全）

- 名牌 0.3s（2.15s）：hasegawa — 长谷川泰三 MADAO（彻底没用的大叔）
- 名牌 9.15s（2.3s）：otsu — 寺门通 超人气偶像｜新八是亲卫队队长

## 音效 cue（场景内时间）

| t | 音效 | 音量 | 持续 |
|---|---|---|---|
| 0.00 | river | 0.35 | 3.0 |
| 0.00 | wind | 0.35 | 3.0 |
| 0.35 | slide_up | 0.6 |  |
| 1.15 | whoosh | 0.35 |  |
| 1.75 | crow | 0.9 |  |
| 2.70 | sweat | 0.45 |  |
| 3.00 | whoosh | 0.7 |  |
| 3.12 | coin | 0.35 |  |
| 3.22 | coin | 0.35 |  |
| 3.30 | coin | 0.5 |  |
| 3.45 | coin | 0.35 |  |
| 3.45 | pop | 0.6 |  |
| 3.50 | drumroll | 0.55 | 0.9000000000000001 |
| 3.62 | coin | 0.5 |  |
| 3.80 | coin | 0.3 |  |
| 4.40 | coin | 0.6 |  |
| 4.62 | record_scratch | 0.9 |  |
| 4.70 | fail | 0.8 |  |
| 4.95 | thud | 0.9 |  |
| 5.10 | wind | 0.5 | 0.8 |
| 5.90 | whoosh | 0.7 |  |
| 6.20 | slide_up | 0.8 |  |
| 6.32 | sparkle | 0.6 |  |
| 6.45 | whoosh | 0.5 |  |
| 6.53 | fanfare | 0.55 |  |
| 6.90 | shine | 0.5 |  |
| 7.20 | sparkle | 0.4 |  |
| 8.80 | whoosh | 0.7 |  |
| 8.80 | crowd | 0.4 | 3.0 |
| 8.95 | cheer | 0.55 |  |
| 9.15 | slide_up | 0.6 |  |
| 9.75 | whoosh | 0.5 |  |
| 10.05 | cheer | 0.7 |  |
| 10.45 | pop | 0.5 |  |
| 10.65 | pop | 0.5 |  |
| 10.85 | pop | 0.5 |  |
| 11.05 | pop | 0.5 |  |
| 11.25 | applause | 0.5 |  |
| 11.80 | whoosh | 0.7 |  |
| 11.95 | eat | 0.45 | 1.4000000000000004 |
| 13.35 | pop | 0.9 |  |
| 13.40 | boing | 0.8 |  |
| 13.43 | whoosh | 0.5 |  |
| 13.48 | fall_whistle | 0.45 |  |
| 14.02 | thud | 0.9 |  |
| 14.12 | eat | 0.45 | 0.3800000000000008 |
| 14.40 | whoosh | 0.7 |  |
| 15.35 | aura | 0.7 |  |
| 15.80 | shing | 0.6 |  |
| 16.20 | stab | 1.0 |  |
| 16.22 | impact | 0.8 |  |
| 16.32 | shock | 0.6 |  |
| 16.70 | sweat | 0.6 |  |
| 16.70 | rimshot | 0.8 |  |
| 16.95 | crow | 0.8 |  |
