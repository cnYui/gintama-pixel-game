# s03 神乐与定春

- 时长：18.0 s（成片里 59.0–77.0 s）
- 音乐：comedy（音量 0.55）
- 出场角色（代码里引用到的角色 id）：gintoki（银时）、kagura（神乐）、sadaharu（定春）、shinpachi（新八）
- 背景（bg 模块里被调用的函数）：kabukicho：street, yorozuya_front, yorozuya_front_fg；yorozuya：office
- 淡入 / 淡出：0.3 / 0.3 s

## 故事分镜（CONTRACT.md 第 8 节，写作时的设计意图）

**s03 神乐与定春 (18 s)** `comedy`

Night: Gintoki on his scooter hits a girl (`crash`) — Kagura springs up unharmed:
「你撞到人了阿鲁！」 name_card 神乐 「夜兔族少女｜怪力·大胃王·『阿鲁』」. → She shoots
yakuza grunts with her umbrella gun (muzzle flashes). → Yorozuya table: rice bowls stack
into a tower, Gintoki+Shinpachi horrified, coins fly away from the wallet. → A box 「请收养」
: giant dog Sadaharu, name_card 定春 「巨型犬｜爱咬银时的头」, bites Gintoki's head
(`chomp`, legs flailing). → Group pose on the Yorozuya balcony, speed lines, big text
「万事屋，集结！」.

## 镜头表（场景文件开头的 SHOT LIST，场景内时间）

```text
s03 神乐与定春 (18 s, music 'comedy').

SHOT LIST (scene-local seconds)
A  0.00-4.90  NIGHT KABUKICHO STREET
   0.00-1.40  tracking shot (zoom 1.5): Gintoki putters along on his scooter picking his nose,
              headlight beam on the road; Kagura sprints in from the right.
   1.40       CRASH: 2-frame punch-in impact frame (paper / negative), then burst + 「咚!!」;
              Kagura spins high through the air; the scooter is left dented and smoking.
   2.15       she lands flat (thud + dust).  2.25-2.60 awkward silence, a crow flaps past.
   2.50-2.75  she springs up and hops right into his face.
   2.75-4.90  CUT close two-shot (zoom 2.1, slow push): Kagura's tsukkomi point with speed
              lines, Gintoki trembling/sweating.  sub 「喂！你撞到人了阿鲁！」  name_card 神乐.
B  4.90-7.90  SAME STREET, new set-up
   4.90-5.45  wide (zoom 1.35): three yakuza (suits + shades) charge in, 「站住!!」.
   5.45-5.85  extreme CU (zoom 3): Kagura levels her umbrella on a red speed-line field, glint.
   5.85-6.95  wide: UMBRELLA MACHINE GUN - muzzle flashes, tracers, flying casings, the thugs
              dance; 「哒哒哒哒!!」; 6.75 last blast sends them flying off-screen.
   6.95-7.90  CU (zoom 2.1): Gintoki peeking out from behind his scooter, trembling; Kagura
              blows the smoke off the tip.  sub 「这丫头……是怪物吗！？」
C  7.90-11.70 YOROZUYA OFFICE (night)
   7.90-8.75  medium (zoom 1.9) on Kagura inhaling rice; empty bowls fly onto a tower.
   8.75-9.75  medium (zoom 1.8) on Gintoki & Shinpachi: 「！？」, the wobbling tower grows out
              of the top of the frame.  sub 「再来一碗阿鲁！」
   9.75-11.70 insert (zoom 3.6-4.2) on the gama-guchi: it pops open, coins sprout wings and
              flutter off; 10.85 pull back: both cry under gloom lines, a moth 「空……」.
D  11.70-15.40 KABUKICHO STREET (next day)
   11.70-12.55 low CU (zoom 2.2): cardboard box 「请收养」 wiggles, Kagura pokes it, 「？」.
              narration 「第二天——」
   12.55-13.30 the box bursts: SADAHARU leaps out (way too big for it), camera snaps back to a
              group shot (zoom 1.55); name_card 定春; Gintoki & Shinpachi jump.
   13.30-15.40 Gintoki strolls up to pat him 「乖～」, red glint... CHOMP (13.65, punch-in +
              speed lines): Sadaharu rears up with Gintoki's head in his jaws, legs flailing,
              pixel blood, 「咔嚓!!」 「嚼」; Kagura cheers.  sub 「就叫你『定春』阿鲁！」
E  15.40-18.00 YOROZUYA FRONT at dusk, balcony (zoom 1.7)
   15.40-15.95 the team drops onto the balcony one by one (landings, dust, Sadaharu's thud).
   15.95      flash + speed lines + red band + brush text 「万事屋，集结！」 (zoom punch):
              Shinpachi on guard, Kagura under her parasol, Gintoki deadpan picking his nose.
   17.15      Sadaharu chomps Gintoki's head again and rears up with him (legs flailing).  fade.

Characters/poses: gintoki (nosepick/sit/shock/kneel/walk/idle/run/land/jump, expr cry),
kagura (run/fly/lie/jump/point/ready/umbrella_shoot/eat/kneel/cheer/umbrella_open/land),
shinpachi (sit/shock/cry/point/ready/land/jump), sadaharu (idle/jump/bite/sit),
private yakuza thugs + props in scenes/_s03_props.py.
```

## 台词 / 旁白时间表（场景内时间）

| 开始 | 结束 | 说话者 | 台词 |
|---|---|---|---|
| 2.75 | 4.85 | 神乐 | 喂！你撞到人了阿鲁！ |
| 5.80 | 7.88 | 银时 | 这丫头……是怪物吗！？ |
| 7.94 | 9.76 | 神乐 | 再来一碗阿鲁！ |
| 9.80 | 11.68 | 新八 | 我们的伙食费啊！ |
| 11.72 | 13.32 | 旁白 | 第二天—— |
| 13.36 | 15.38 | 神乐 | 就叫你『定春』阿鲁！ |

## 音效 cue（场景内时间）

| t | 音效 | 音量 | 持续 |
|---|---|---|---|
| 0.00 | night | 0.35 | 7.9 |
| 0.00 | scooter | 0.7 | 1.45 |
| 1.40 | crash | 1.0 |  |
| 1.42 | punch_big | 0.8 |  |
| 1.48 | fly_away | 0.6 |  |
| 2.15 | thud | 0.9 |  |
| 2.30 | crow | 0.7 |  |
| 2.50 | jump | 0.8 |  |
| 2.75 | land | 0.8 |  |
| 2.77 | shock | 0.6 |  |
| 2.85 | whoosh | 0.5 |  |
| 3.20 | sweat | 0.5 |  |
| 4.90 | run | 0.6 | 0.4 |
| 5.00 | slide_up | 0.4 |  |
| 5.45 | charge | 0.5 |  |
| 5.62 | shing | 0.9 |  |
| 5.85 | machinegun | 0.9 |  |
| 6.00 | hit | 0.5 |  |
| 6.25 | hit | 0.5 |  |
| 6.30 | machinegun | 0.9 |  |
| 6.50 | hit | 0.5 |  |
| 6.75 | gunshot | 1.0 |  |
| 6.76 | explosion_small | 0.7 |  |
| 6.85 | fly_away | 0.7 |  |
| 7.05 | sweat | 0.5 |  |
| 7.90 | eat | 0.6 | 1.8499999999999996 |
| 8.75 | shock | 0.7 |  |
| 9.40 | gulp | 0.8 |  |
| 9.75 | slide_down | 0.6 |  |
| 10.00 | pop | 0.6 |  |
| 10.10 | twinkle | 0.45 |  |
| 10.35 | fly_away | 0.35 |  |
| 11.00 | fail | 0.7 |  |
| 11.70 | crowd | 0.25 | 3.700000000000001 |
| 11.95 | squeak | 0.6 |  |
| 12.30 | squeak | 0.6 |  |
| 12.55 | pop | 0.8 |  |
| 12.58 | boing | 0.9 |  |
| 12.70 | shock | 0.7 |  |
| 12.72 | whoosh | 0.5 |  |
| 12.87 | thud | 0.8 |  |
| 12.95 | bark | 0.9 |  |
| 13.40 | shine | 0.5 |  |
| 13.65 | chomp | 1.0 |  |
| 13.67 | punch_big | 0.6 |  |
| 13.95 | shock | 0.5 |  |
| 14.25 | chomp | 0.75 |  |
| 14.75 | chomp | 0.75 |  |
| 15.25 | chomp | 0.75 |  |
| 15.40 | whoosh | 0.6 |  |
| 15.56 | land | 0.7 |  |
| 15.68 | land | 0.7 |  |
| 15.78 | land | 0.7 |  |
| 15.88 | thud | 1.0 |  |
| 15.95 | title_hit | 0.9 |  |
| 15.97 | impact | 0.6 |  |
| 16.15 | shine | 0.6 |  |
| 16.60 | bark | 0.6 |  |
| 17.25 | chomp | 1.0 |  |
| 17.40 | rimshot | 0.7 |  |
