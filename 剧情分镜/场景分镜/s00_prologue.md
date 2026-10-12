# s00 开场

- 时长：17.9 s（成片里 0.0–17.9 s）
- 音乐：0s → prologue、12s → title、15.38s → （静音）、15.85s → title（音量 0.6）
- 出场角色（代码里引用到的角色 id）：amanto_cat（天人(猫)）、amanto_pig（天人(猪)）、gintoki（银时）、harusame（春雨）、kagura（神乐）、katsura（桂）、sadaharu（定春）、sakamoto（坂本）、shinpachi（新八）、shiroyasha（白夜叉）、takasugi（高杉）、townsman（路人）
- 背景（bg 模块里被调用的函数）：common：add_sprite, bayer, big_moon, clouds, dirt_ground, far_mountains, glow_sprite, grade_rgba, lantern, light_up, lit_amount, sky, stone_street, vgradient；edo：roof_walk, ship, skyline
- 淡入 / 淡出：0.4 / 0.3 s

## 故事分镜（CONTRACT.md 第 8 节，写作时的设计意图）

**s00 开场 Prologue (16 s)** music `[(0,"prologue"),(12,"title")]`

Starfield → UFO/spaceship fleet descends over old Edo (castle, rooftops) — narration
「二十年前，自称『天人』的外星人从天而降。」 → sunset battlefield, samurai silhouettes vs
alien ships — 「武士们奋起抵抗，史称『攘夷战争』。」 → rain, a katana falls/drops, a notice
board 「废刀令」 — 「幕府投降，废刀令颁布。武士的时代，结束了……」 → at 12.0 s white flash +
`title_hit`: big brush logo 「银魂」 slams in (shockwave, sakura burst, sparkle) with
「GINTAMA · 像素剧场」, Edo skyline with the Terminal tower and flying ships behind.

## 镜头表（场景文件开头的 SHOT LIST，场景内时间）

```text
s00 「开场」 Prologue (17.9 s) — music [(0,'prologue'), (12,'title')]

SHOT LIST (scene-local seconds)
 1  0.00- 4.10  天降  Deep space / milky way, full moon. The amanto MOTHERSHIP glides in and
                eclipses the moon; cruisers + saucers follow. Camera DESCENDS with the fleet
                (tall-sky tilt: stars -> cloud layer -> night horizon) until old Edo (castle,
                pagoda, watch-tower, lit shoji windows, NO Terminal yet) rises into frame.
                Saucers settle over the roofs, searchlight beams sweep the town.
                Narration 0.5-4.0 「二十年前，自称『天人』的外星人从天而降。」
 2a 4.10- 6.10  攘夷  Sunset battlefield (huge striped sun, smoke columns, nobori banners,
                distant armies clashing). Explosion bang on the cut; ships fire lasers
                (4.30 / 4.85 / 5.60) -> ground explosions. Tracking shot: samurai led by
                Shiroyasha charge right, Harusame/pig/cat amanto charge left; 5.30 clash,
                5.18 smash zoom (1.8x, 集中線) onto the duel, 5.48 Shiroyasha's slash
                (2-frame impact frame) launches a pirate spinning into the sky, the other
                amanto flinch; the pirate becomes a twinkling star (5.90).
 2b 6.10- 8.20  Four heroes silhouetted on a ridge against the giant sun (Sakamoto,
                Katsura, Shiroyasha, Takasugi) with rim light, torn banner, crows, embers;
                slow push-in (zoom 1.2->1.75), letterbox; they draw one by one
                (7.02 Sakamoto's pistol, 7.14 Katsura, 7.26 Takasugi drops his kiseru for
                his blade, 7.40 Shiroyasha) — each with a steel flash + 'shing'; red eye glint.
                Narration 4.3-7.9 「武士们奋起抵抗，史称『攘夷战争』。」
 3a 8.20- 9.90  Rain, lightning, 2x close-up. Field of swords + a fallen kabuto; a katana tumbles down
                in slow motion and stabs into a puddle at 9.15 (impact frame, lightning
                flash, splash, ripples, wobble), blade glint 9.5.
 3b 9.90-12.00  Rain at night: the 「废刀令」 notice board (lantern, pile of confiscated
                swords); the swordless samurai (Shiroyasha) stands under it, looks up,
                lowers his head, 11.1 turns his back on it and walks off. Slow push-in, 10.5 temple gong, fade to black 11.35-11.84;
                11.84-12.00 the 「银魂」 logo rushes at the camera over black.
                Narration 8.3-11.9 「幕府投降，废刀令颁布。武士的时代，结束了……」
 4 12.00-17.90  TITLE. 12.00 white flash + title_hit: 「银魂」 brush logo lands
                (speed lines, shockwave rings, sakura burst, shake), rotating sunburst,
                ribbon 「GINTAMA · 像素剧场」 slides in 12.30, sparkles. Day Edo skyline
                with the Terminal + flying ships, slow pan. 13.10+ the Yorozuya pop up
                onto the roof ridge: Shinpachi, Kagura (parasol), Gintoki (bokuto on
                shoulder), Sadaharu (thud 14.05, bark). GAG: 14.30 camera pushes in on
                Gintoki's deadpan nose-pick (「抠…抠…」) -> 15.05 flick, hard cut to the
                wide, booger arcs onto 「魂」 (15.38 splat, logo flinches) -> awkward
                silence, crow -> 15.85 snap zoom + 集中線: Shinpachi 「喂！」 + bubble
                「往标题上弹鼻屎？！」 while Gintoki keeps picking -> 17.05 he flicks the
                next one onto Shinpachi's glasses (「啪！」). Fade out.
```

## 台词 / 旁白时间表（场景内时间）

| 开始 | 结束 | 说话者 | 台词 |
|---|---|---|---|
| 0.50 | 4.00 | 旁白 | 二十年前，自称『天人』的外星人从天而降。 |
| 4.30 | 7.90 | 旁白 | 武士们奋起抵抗，史称『攘夷战争』。 |
| 8.30 | 11.90 | 旁白 | 幕府投降，废刀令颁布。武士的时代，结束了…… |

## 音效 cue（场景内时间）

| t | 音效 | 音量 | 持续 |
|---|---|---|---|
| 0.00 | engine_hum | 0.45 | 4.1 |
| 0.00 | wind | 0.25 | 4.1 |
| 0.50 | heartbeat | 0.35 |  |
| 1.05 | whoosh | 0.5 |  |
| 1.30 | heartbeat | 0.3 |  |
| 1.95 | whoosh | 0.5 |  |
| 2.20 | whoosh | 0.3 |  |
| 2.50 | whoosh | 0.3 |  |
| 2.85 | laser | 0.35 |  |
| 3.00 | aura | 0.3 |  |
| 4.10 | explosion | 0.9 |  |
| 4.10 | battle | 0.45 | 2.0 |
| 4.10 | crowd | 0.3 | 2.0 |
| 4.30 | laser | 0.5 |  |
| 4.42 | explosion_small | 0.7 |  |
| 4.85 | laser | 0.5 |  |
| 4.97 | explosion | 0.6 |  |
| 5.18 | whoosh | 0.45 |  |
| 5.30 | dash | 0.4 |  |
| 5.44 | slash_big | 0.8 |  |
| 5.48 | clang | 0.6 |  |
| 5.48 | impact | 0.55 |  |
| 5.50 | hit | 0.6 |  |
| 5.52 | fly_away | 0.45 |  |
| 5.60 | laser | 0.45 |  |
| 5.60 | shock | 0.3 |  |
| 5.72 | explosion_small | 0.6 |  |
| 5.90 | twinkle | 0.4 |  |
| 6.10 | wind | 0.55 | 2.1 |
| 6.10 | fire | 0.25 | 2.1 |
| 7.02 | shing | 0.4 |  |
| 7.14 | shing | 0.5 |  |
| 7.26 | shing | 0.6000000000000001 |  |
| 7.40 | shing | 0.7000000000000001 |  |
| 7.40 | sting_dramatic | 0.35 |  |
| 8.20 | rain | 0.55 | 3.55 |
| 8.20 | thunder | 0.55 |  |
| 8.45 | whoosh | 0.35 |  |
| 9.15 | stab | 0.9 |  |
| 9.15 | clang | 0.35 |  |
| 9.21 | thunder | 0.9 |  |
| 9.55 | shing | 0.35 |  |
| 9.98 | thunder | 0.35 |  |
| 10.50 | gong | 0.6 |  |
| 11.10 | footsteps | 0.3 | 0.8 |
| 11.82 | whoosh | 0.5 |  |
| 12.00 | title_hit | 1.0 |  |
| 12.00 | impact | 0.5 |  |
| 12.30 | whoosh | 0.4 |  |
| 12.35 | sparkle | 0.5 |  |
| 13.10 | jump | 0.5 |  |
| 13.22 | jump | 0.5 |  |
| 13.36 | jump | 0.5 |  |
| 13.52 | land | 0.45 |  |
| 13.55 | jump | 0.5 |  |
| 13.64 | land | 0.45 |  |
| 13.78 | land | 0.45 |  |
| 13.85 | sparkle | 0.45 |  |
| 14.05 | thud | 0.8 |  |
| 14.14 | bark | 0.45 |  |
| 14.30 | whoosh | 0.25 |  |
| 15.05 | pop | 0.55 |  |
| 15.07 | whoosh | 0.25 |  |
| 15.38 | slap | 0.35 |  |
| 15.40 | squeak | 0.4 |  |
| 15.42 | record_scratch | 0.55 |  |
| 15.48 | crow | 0.5 |  |
| 15.85 | vein | 0.6 |  |
| 15.85 | impact | 0.4 |  |
| 16.00 | blip | 0.22 |  |
| 16.06 | blip | 0.22 |  |
| 16.12 | blip | 0.22 |  |
| 16.19 | blip | 0.22 |  |
| 16.25 | blip | 0.22 |  |
| 16.31 | blip | 0.22 |  |
| 16.38 | blip | 0.22 |  |
| 16.44 | blip | 0.22 |  |
| 16.50 | blip | 0.22 |  |
| 17.05 | pop | 0.5 |  |
| 17.25 | slap | 0.5 |  |
| 17.28 | shock | 0.45 |  |
