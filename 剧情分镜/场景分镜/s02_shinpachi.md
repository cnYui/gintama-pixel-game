# s02 新八登场

- 时长：21.9 s（成片里 37.1–59.0 s）
- 音乐：0s → comedy、5.15s → （静音）、8.35s → comedy、20.15s → （静音）（音量 0.55）
- 出场角色（代码里引用到的角色 id）：amanto_cat（天人(猫)）、amanto_pig（天人(猪)）、gintoki（银时）、otae（阿妙）、shinpachi（新八）、townsman（路人）、townswoman（路人）
- 背景（bg 模块里被调用的函数）：common：cherry_tree, clouds, far_mountains, grade_rgba, lantern, room_wall, sky, wood_floor；kabukicho：street
- 淡入 / 淡出：0.3 / 0.3 s

## 故事分镜（CONTRACT.md 第 8 节，写作时的设计意图）

**s02 新八登场 (20 s)** `comedy`

Family restaurant: Shinpachi as waiter carrying a tray, pig-faced amanto customers bully
him 「地球猴子！上菜慢死了！」. Gintoki at the counter with a chocolate parfait. The amanto
knocks the parfait over → silence (crow) → Gintoki's eyes turn serious → one bokuto hit,
amanto flies through the wall (impact, speed lines). → Manager: 「新八！你被开除了！」
name_card 志村新八 「吐槽担当｜本体是眼镜」. Shinpachi's huge tsukkomi at Gintoki
「你给我等一下！！」. → Shimura dojo: Otae smiles with a dark aura, name_card 志村妙
「新八的姐姐｜笑容可怕·暗黑料理」, offers a charred black egg 「请用～」 → Gintoki faints.
→ Shinpachi, determined: 「我要跟着这个人，找回我的武士道！」 → joins Yorozuya.

## 镜头表（场景文件开头的 SHOT LIST，场景内时间）

```text
s02 新八登场 — family restaurant -> parfait tragedy -> Shimura dojo -> Shinpachi joins.

SHOT LIST (scene-local seconds, duration 21.9)
  A  0.00- 3.90  Family restaurant: wide establishing -> push-in (zoom 1.06->1.78) as
                 Shinpachi (waiter, tray) walks out of the kitchen swing door to the
                 pigs at the counter. 1.45 pig B stomps (咚, vein, shake):
                 「地球猴子！上菜慢死了！」 Shinpachi sweats. Gintoki at the counter
                 blissfully eats a chocolate parfait (hearts), ignoring everything.
  B  3.90- 5.50  CLOSE-UP (zoom 2.6): Gintoki in parfait heaven. Pig B turns to mock him,
                 4.30 raises his fist -> 4.58 SLAMS the counter (咚) -> the parfait hops
                 and hangs in SLOW MOTION (Gintoki: "！", hand reaching) -> 5.15 SPLAT
                 (啪嚓, glass + record scratch, music cuts to silence).
  C  5.50- 6.70  SILENCE tableau, slow push-in: everyone frozen; a crow glides across the
                 window 「阿～」…「呆～」 (synced to the two caws); "..." over Gintoki.
  D  6.70- 7.70  EYES: letterboxed extreme close-up, dead-fish eyes -> 7.12 sharp (shing).
  E  7.70- 9.30  THE HIT. close: Gintoki leaps off the stool, bokuto crescent 7.95 ->
                 impact frame + speed lines + 砰!!; 8.12 wide: pig B rockets into the back
                 wall 8.35 (pig-shaped hole, debris, 轰!, music back); pig A flees in the
                 foreground 「噫——！」; 8.80 the pig twinkles as a star through the hole.
  F  9.30-11.40  Manager (chef hat) SLAMS the kitchen door open (砰!), points:
                 「新八！你被开除了！」 -> 10.35 SNAP ZOOM: tray drops (哐啷), Shinpachi
                 turns to stone (gloom lines, 咔嚓).
  G 11.40-13.90  name_card 志村新八 over stone-Shinpachi while Gintoki strolls off
                 nose-picking; 12.00 TSUKKOMI close-up (speed lines, 喂!!)
                 「你给我等一下！！」 -> 12.70 two-shot: Gintoki 「？」, flicks a booger
                 13.12 that sticks on Shinpachi's glasses 13.38 (啪, vein). 13.75 wipe.
  H0 13.90-14.70 Dusk exterior: Shimura dojo gate (signboard 志村道场, lantern, sakura).
  H 14.70-17.80  Dojo interior. name_card 志村妙 14.80; 15.00 dark aura + egg 「请用～」;
                 15.80 INSERT: the charred 'fried egg' (bubbles, miasma, skull,
                 「※本品为煎蛋」); 16.36 push-in on sweating Gintoki; 16.70 he eats it
                 (嘎嘣) -> purple flash -> 17.15 falls backwards, legs up (咚!), soul leaves.
  I 17.80-21.90  Shinpachi springs up (light rays), glasses glint 18.05, points at the
                 fainted 「这个人」 18.30, raises his bokuto to the sky 18.95:
                 「我要跟着这个人，找回我的武士道！」; 20.15 music drops, JRPG box
                 「志村新八 加入了万事屋！」 + fanfare, camera pulls back.
Characters: shinpachi (waiter / waiter_walk / point / shock / idle, torso='apron'),
gintoki (sit + spoon prop, attack, jump, shoulder, walk+nosepick, eat), amanto_pig x2
(sit/laugh/bully/shock/fly), townsman v2 as the manager (+ chef hat), otae
(idle / offer_egg with dark_smile aura), passers-by (townsman/townswoman/amanto_cat).
```

## 台词 / 旁白时间表（场景内时间）

| 开始 | 结束 | 说话者 | 台词 |
|---|---|---|---|
| 1.50 | 3.70 | 天人(猪) | 地球猴子！上菜慢死了！ |
| 9.40 | 11.36 | 店长 | 新八！你被开除了！ |
| 12.00 | 13.90 | 新八 | 你给我等一下！！ |
| 15.10 | 16.70 | 阿妙 | 请用～ |
| 17.85 | 20.15 | 新八 | 我要跟着这个人，找回我的武士道！ |

## 音效 cue（场景内时间）

| t | 音效 | 音量 | 持续 |
|---|---|---|---|
| 0.00 | crowd | 0.22 | 5.3 |
| 0.00 | footsteps | 0.35 | 1.3 |
| 0.02 | door | 0.45 |  |
| 1.45 | thud | 0.9 |  |
| 1.47 | vein | 0.7 |  |
| 1.62 | sweat | 0.6 |  |
| 3.95 | sparkle | 0.5 |  |
| 4.30 | whoosh | 0.4 |  |
| 4.50 | whoosh | 0.6 |  |
| 4.58 | thud | 0.8 |  |
| 4.60 | hit | 0.4 |  |
| 4.64 | slide_up | 0.35 |  |
| 5.15 | glass | 0.9 |  |
| 5.18 | record_scratch | 0.9 |  |
| 5.62 | crow | 0.8 |  |
| 6.70 | sting_dramatic | 0.8 |  |
| 7.12 | shing | 0.9 |  |
| 7.70 | jump | 0.7 |  |
| 7.85 | land | 0.4 |  |
| 7.88 | whoosh | 0.7 |  |
| 7.95 | punch_big | 1.0 |  |
| 7.95 | impact | 0.7 |  |
| 8.00 | fly_away | 0.6 |  |
| 8.35 | crash | 1.0 |  |
| 8.37 | thud | 0.6 |  |
| 8.47 | dash | 0.6 |  |
| 8.75 | crowd | 0.18 | 5.050000000000001 |
| 8.80 | twinkle | 0.7 |  |
| 9.30 | door_bang | 1.0 |  |
| 9.42 | vein | 0.7 |  |
| 10.35 | shock | 0.8 |  |
| 10.47 | glass | 0.35 |  |
| 10.60 | clang | 0.7 |  |
| 10.63 | glass | 0.4 |  |
| 10.80 | clang | 0.3 |  |
| 11.45 | whoosh | 0.5 |  |
| 12.00 | slap | 1.0 |  |
| 12.02 | shock | 0.5 |  |
| 13.12 | pop | 0.6 |  |
| 13.38 | slap | 0.45 |  |
| 13.50 | vein | 0.6 |  |
| 13.75 | whoosh | 0.6 |  |
| 13.90 | wind | 0.2 | 7.999999999999998 |
| 13.95 | footsteps | 0.3 | 0.699999999999999 |
| 13.98 | bell | 0.5 |  |
| 14.80 | whoosh | 0.45 |  |
| 15.00 | aura | 0.9 |  |
| 15.80 | heartbeat | 0.8 |  |
| 16.36 | sweat | 0.7 |  |
| 16.70 | chomp | 0.9 |  |
| 16.92 | gulp | 0.8 |  |
| 17.00 | shock | 0.7 |  |
| 17.35 | thud | 0.9 |  |
| 17.43 | fail | 0.55 |  |
| 17.80 | jump | 0.6 |  |
| 17.85 | shine | 0.5 |  |
| 18.00 | land | 0.5 |  |
| 18.05 | sparkle | 0.8 |  |
| 18.30 | whoosh | 0.4 |  |
| 18.95 | shing | 0.7 |  |
| 20.15 | fanfare | 0.9 |  |
