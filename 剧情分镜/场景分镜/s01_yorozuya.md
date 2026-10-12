# s01 万事屋阿银

- 时长：19.2 s（成片里 17.9–37.1 s）
- 音乐：0s → yorozuya、17.95s → （静音）（音量 0.5）
- 出场角色（代码里引用到的角色 id）：amanto_pig（天人(猪)）、gintoki（银时）、otose（登势）、townsman（路人）、townswoman（路人）
- 背景（bg 模块里被调用的函数）：kabukicho：street, street_fg；yorozuya：office, office_fg
- 淡入 / 淡出：0.3 / 0.3 s

## 故事分镜（CONTRACT.md 第 8 节，写作时的设计意图）

**s01 万事屋阿银 (18 s)** `yorozuya`

Kabukicho street (day) establishing: Otose's snack bar downstairs, 「万事屋银酱」 sign
upstairs, townsfolk + an amanto passing. → Interior: Gintoki asleep on the sofa, Jump over
his face, strawberry milk on the table, 「糖分」 frame on the wall. name_card 坂田银时
「万事屋老板｜天然卷·甜党·死鱼眼」. → Otose slams the door open 「银时！三个月的房租呢！」 /
Gintoki 「老太婆，下个月……一定。」 → Otose's kick: Gintoki flies out of the window, lands
on the street (dust, `thud`), name_card 登势 「楼下酒馆老板娘（房东）」. → He gets up,
deadpan nose-pick 「……今天的歌舞伎町，也很和平呢。」

## 镜头表（场景文件开头的 SHOT LIST，场景内时间）

```text
s01 万事屋阿银 — Kabukicho morning, Gintoki gets kicked out over the rent.

SHOT LIST (scene-local seconds)
  A  0.00- 3.60  Kabukicho street, day. Tilt down from the Terminal/sky onto the
                 Yorozuya building while panning right; townsfolk + a pig amanto
                 stroll by. Location caption 「江户·歌舞伎町」 (0.4-2.3), pop-up tags
                 「二楼·万事屋」「一楼·登势酒馆」 (1.5 / 1.75). 2.95 push-in (zoom) into
                 the 2F window -> white flash cut.
  B1 3.60- 6.10  Office interior (match cut on the window): starts on the 「糖分」
                 frame + window, then pans/pulls back onto the right sofa: Gintoki
                 asleep, Jump over his face, snot bubble + Zzz, strawberry milk on
                 the table. name_card 坂田银时 (4.30). 5.35/5.60/5.85 stomps up the
                 stairs (咚 咚 咚, shakes, ceiling dust).
  B2 6.10- 8.40  Close on the sliding door: it SLAMS open (zoom punch, speed lines,
                 shake), Otose in the doorway, anger vein. 「银时！三个月的房租呢！」
                 Gintoki keeps snoring (bubble). 7.90 she stomps over to the sofa;
                 the camera glides into the B3 two-shot (continuous move).
  B3 8.40-11.50  Two-shot. 8.55 snot bubble POPS -> Gintoki answers from under the
                 Jump 「老太婆，下个月……一定。」 -> 10.15 second vein, room goes dark,
                 purple aura, camera creeps onto Otose, 10.36 eye glint -> 10.40
                 kick chamber (trembling hold) -> 10.90 KICK (impact frame, 咚！！,
                 shake) -> whip pan: Gintoki tumbles into the window (shrinks into
                 depth), the Jump flies off -> 11.30 glass CRASH (哐啷！).
  C1 11.50-12.60 Exterior, tight on the 2F window: it bursts, Gintoki tumbles out
                 toward camera, the camera follows him down -> 12.15 face-plant on
                 the road (dust, cracks, 咚！); two gossiping ladies jump, the pig
                 amanto freezes then bursts out laughing.
  C2 12.60-14.55 Low close-up: Otose pops up behind the balcony railing, shouting /
                 pointing down, name_card 登势婆婆 (12.75). 「没钱交房租就去干活！」
                 (line starts off-screen at 12.45 as a J-cut).
  D  14.55-19.20 Close shot on the street (Yorozuya sign on top): Gintoki twitches,
                 hops up (head bump), deadpan nose-pick 「……今天的歌舞伎町，也很和平
                 呢。」 17.00 flick -> the booger hits the laughing pig (17.22), who
                 flees -> his Jump flutters down onto his head (17.85, 啪) ->
                 awkward crow 「阿～呆～」 over a deadpan hold (18.15).
```

## 台词 / 旁白时间表（场景内时间）

| 开始 | 结束 | 说话者 | 台词 |
|---|---|---|---|
| 6.22 | 8.34 | 登势 | 银时！三个月的房租呢！ |
| 8.62 | 10.62 | 银时 | 老太婆，下个月……一定。 |
| 12.45 | 14.55 | 登势 | 没钱交房租就去干活！ |
| 15.25 | 17.70 | 银时 | ……今天的歌舞伎町，也很和平呢。 |

## 音效 cue（场景内时间）

| t | 音效 | 音量 | 持续 |
|---|---|---|---|
| 0.00 | crowd | 0.3 | 3.6 |
| 1.50 | pop | 0.5 |  |
| 1.75 | pop | 0.5 |  |
| 2.95 | whoosh | 0.7 |  |
| 4.30 | whoosh | 0.4 |  |
| 5.35 | thud | 0.4 |  |
| 5.60 | thud | 0.5 |  |
| 5.85 | thud | 0.6 |  |
| 6.10 | door_bang | 1.0 |  |
| 6.25 | vein | 0.7 |  |
| 7.90 | footsteps | 0.5 | 0.5 |
| 8.55 | pop | 0.7 |  |
| 9.40 | aura | 0.55 |  |
| 10.15 | vein | 0.8 |  |
| 10.36 | sparkle | 0.6 |  |
| 10.72 | whoosh | 0.75 |  |
| 10.90 | kick | 1.0 |  |
| 10.90 | impact | 0.6 |  |
| 10.94 | fly_away | 0.6 |  |
| 11.30 | glass | 1.0 |  |
| 11.50 | crowd | 0.3 | 7.699999999999999 |
| 11.52 | glass | 0.45 |  |
| 11.55 | fall_whistle | 0.55 |  |
| 12.15 | thud | 1.0 |  |
| 12.15 | impact | 0.5 |  |
| 12.25 | shock | 0.4 |  |
| 12.60 | vein | 0.6 |  |
| 15.10 | land | 0.6 |  |
| 17.00 | pop | 0.6 |  |
| 17.22 | squeak | 0.6 |  |
| 17.24 | shock | 0.5 |  |
| 17.48 | dash | 0.5 |  |
| 17.85 | slap | 0.7 |  |
| 18.15 | crow | 0.8 |  |
