# 银魂 像素剧场 — Project Contract (read fully before working)

We are making a ~5-minute **pixel-art animated video** retelling the story of the anime
*Gintama (银魂)* in chronological order: main characters, classic scenes, gags and the
big emotional arcs. Chinese subtitles. Original chiptune music + SFX. Fan tribute work.

Everything is procedural Python (PIL + numpy) rendered to MP4 with ffmpeg.
Project root = the directory containing this file. Run all commands from the root.

## 1. Output format
* Internal canvas **384×216**, upscaled ×5 nearest-neighbour → 1920×1080, **30 fps**.
* Sprite animation is deliberately choppy: character poses step at 12 fps (`ANIM_FPS`);
  camera pans / particles / text move at the full 30 fps.
* Every scene is a **pure function of time**: `render(img, t)` must not keep state
  between frames. Randomness only via `engine.core.rng(*keys)` (deterministic).

## 2. File ownership (STRICT — parallel agents share this tree)
| path | owner |
|---|---|
| `engine/*`, `chars/rig.py`, `chars/__init__.py`, `chars/gintoki.py`, `main.py`, `preview.py`, `charsheet.py` | lead (read-only for everyone else) |
| `chars/<your_ids>.py` | the character agent assigned those ids |
| `bg/*.py` | background agent (read-only for scene agents) |
| `audio/music_a.py`, `audio/music_b.py`, `audio/sfx.py` | the audio agents |
| `scenes/sNN_*.py` (+ optional private helper `scenes/_sNN_*.py`) | the scene agent for sNN |

Never edit a file you don't own. If a shared thing is broken or missing, work around it
locally in your own file (e.g. a private helper) and **report it** in your final answer.
Put scratch/preview outputs only under `build/`.

## 3. Engine API cheat-sheet
```python
from engine.core import Scene, Cue, W, H, FPS, seg, lerp, lerp2, clamp, ease_in, ease_out, ease_in_out, \
    ease_out_back, ease_out_bounce, ease_out_elastic, wave, step_frame, quant, rng, arc, lerp_color
from engine.gfx import PAL, INK, ascii_sprite, cached_sprite, paste, rect, overlay_rect, frame_rect, line, \
    circle, ellipse, polygon, pset, stamp_line, gradient, dither_mask, shade, mix, tint, silhouette, \
    outline, flip_h, scale_nearest, rotate_nearest, set_alpha, new_sprite, fill
from engine import fx      # shake_offset, shift, zoom, flash, fade, invert, impact_frame, grade, sepia,
                           # grayscale, vignette, letterbox, speed_lines, motion_lines, comic_burst,
                           # slash_arc, burst, explosion, smoke_puff, sakura, rain, snow, embers, stars,
                           # sparkle, iris, diamond_wipe, wipe, pixelate
from engine.text import draw_text, text_width, text_sprite, wrap, sfx_text, speech_bubble, \
    name_card, chapter_card, narration, dialogue_box
from chars import draw_char, render_sprite, portrait, get_def, list_chars
```
Read the source of `engine/*.py` and `chars/rig.py` — they are short and documented.
`scenes/example_scene.py` shows the idioms (parallax street, walking char, name card,
gag hit with burst + sfx_text + shake, cues). Preview it: `python preview.py example_scene`.

### Scene class
```python
class MyScene(Scene):
    id = "s03"; title = "神乐与定春"; duration = 18.0
    music = "comedy"                      # or [(0, "tension"), (9.5, "battle")] ; None = silence
    music_vol = 0.55
    subs = [(t0, t1, "gintoki", "台词"), (t0, t1, None, "旁白")]   # rendered automatically
    def render(self, img, t): ...         # draw EVERYTHING (background, chars, fx) for time t
    def cues(self): return [Cue(2.4, "punch"), Cue(0, "rain", vol=.4, dur=10)]
SCENE = MyScene()
```
* The renderer draws `subs` on top after `render()`, then applies 0.3 s fade-in/out
  (set `fade_in`/`fade_out` to 0 to disable, e.g. for a hard cut into the next scene).
* Dialogue subs get a JRPG box (y 173–211) with name tag + animated portrait and
  auto-generated voice blips. Narration (speaker None) is centred text on a dark band.
* Subtitles type at 16 chars/s. Give each line **typing time + ≥1.3 s** reading time.
  Keep lines ≤ 34 Chinese chars (2 lines). Subtitles must not overlap in time.
* **Composition rule:** while a dialogue box is visible, keep faces/feet of important
  characters above y≈168. The standard floor line is **FLOOR_Y = 160** (feet y).
* `name_card(img, t, t0, dur, cid, "坂田银时", "万事屋老板·天然卷")` — character intro
  band at the top (y=22 default). Use for each character's FIRST appearance (dur ≈ 2.2 s).
* `chapter_card(img, t, t0, dur, "红樱篇", "副标题")` — full-screen arc title (≈2 s).
* `sfx_text(img, x, y, "砰!", t, t0)` manga onomatopoeia; `fx.speed_lines` for 集中線
  reaction shots; `fx.shake_offset` + `fx.shift` for impacts; `fx.zoom(img, 2, cx, cy)`
  for close-ups (zooms the whole frame uniformly — preferred over scaling sprites).

### Characters
`draw_char(img, cid, x, y, pose, t, p=None, expr=None, facing=1, flash=0, alpha=1, rot=0, **kw)`
draws with **feet at (x, y)**. `t` drives loops; `p` (0..1) drives one-shot poses.
Standard poses (every rig character has all of them): `idle walk run run_away talk shout
point shock hit fly lie sleep attack slash_up thrust ready guard shoulder jump land sit
kneel cheer bow cry eat think arms_crossed wave punch kick` + character-specific extras
(see roster). Expressions: `normal blink talk angry shout shock happy sad cry hurt smug`
(+ extras; unknown names fall back gracefully). `render_sprite(...)` returns the RGBA
sprite if you need to transform it yourself. Chibi height ≈ 34 px; kids ≈ 26 px.

### Tools
* `python charsheet.py <id>` → `build/preview/char_<id>.png` (all poses/expressions)
* `python charsheet.py --all` → `build/preview/lineup.png`
* `python preview.py sNN [--step 0.5] [--range a b] [--scale 2]` → contact sheet PNG
* `python preview.py sNN --at 3.2 7.5` → single frames at 3× (inspect details!)
* `python preview.py sNN --check` → renders every frame, prints errors + ms/frame and
  unknown SFX/music names. Must report **0 errors** and ideally < 60 ms/frame.
* `python preview.py sNN --video` → mp4 with audio (only if audio modules exist).
Look at your PNGs with the Read tool — visual verification is mandatory.

## 4. Visual style guide
* Chibi SD proportions (big head ≈ half the height), **1 px INK outline** (`engine.gfx.INK`)
  on every sprite, 2–3 tones per material, light from top-left. No anti-aliasing,
  no gradients on sprites; dithered/banded gradients (`gfx.gradient`) are fine for skies.
* Prefer the master palette `engine.gfx.PAL`. Backgrounds slightly darker / less saturated
  than characters so characters pop. Night scenes: blue-purple palette + warm lanterns.
* Every shot should MOVE: parallax layers, camera pans/zooms, ambient particles
  (sakura, rain, embers, dust, stars), idle breathing, blinking. No dead static frames.
* Comedy grammar (Gintama!): deadpan hold → sudden impact → speed lines + sfx_text +
  shake → reaction face; characters flying off into the sky and becoming a twinkling star;
  tsukkomi with a big `point` pose; awkward-silence crow ('crow' SFX) over a blank beat.
* Drama grammar: letterbox bars, slow pans, silhouettes against a big moon/sunset,
  impact frames (`fx.impact_frame`) on decisive slashes, white flashes, sepia flashbacks.
* **No gore**: blood only as small stylised red pixel splashes; the execution in the
  flashback cuts to white.

## 5. Character roster (ids are FIXED — scenes rely on them)
Lead-made reference: **gintoki** (银时) — extras: `nosepick`, `drink` (strawberry milk),
`read` (sitting reading Jump). Weapon `bokuto`.

| agent | id | name (display) | look / notes | required extra poses / exprs |
|---|---|---|---|---|
| A | shinpachi | 新八 | black hair, glasses (glint!), white kimono top + blue hakama | `waiter` (carry tray), `otaku_cheer` (waving light sticks, happi coat), weapon bokuto |
| A | kagura | 神乐 | vermilion hair in two buns (china-style covers), red qipao, purple umbrella | weapon `umbrella`; `umbrella_shoot`, `umbrella_open` (parasol overhead), `dropkick`, `sukonbu` (chewing) |
| A | sadaharu | 定春 | GIANT white dog (~50×40 px), custom renderer, red eyebrow markings | `idle walk run sit sleep bite bark` (bite = jaws open/close) |
| A | otae | 阿妙 | ponytail brown hair, pink kimono, sweet smile with dark aura | expr `dark_smile`; `super_punch`, `offer_egg` (plate of charred black egg), weapon `naginata` |
| A | otose | 登势 | old lady, grey bun, dark kimono, cigarette | `smoke`, `kick` |
| A | hasegawa | 长谷川 | MADAO: sunglasses, stubble, shabby clothes | `box` (sitting in cardboard box), `depressed` |
| B | kondo | 近藤 | gorilla-ish, stubble, Shinsengumi black uniform (gold trim) | `stalk` (crouching behind a bush prop), weapon katana |
| B | hijikata | 土方 | black V-bangs, sharp eyes, cigarette, Shinsengumi uniform | weapon katana; `smoke`, `mayo` (squeezing mayonnaise bottle), `draw` (iai draw), expr `afro` (soot + afro after explosion) |
| B | toshi | 托西 | Hijikata cursed into a timid otaku (same uniform, droopy eyes, sweat) | `beg` (dogeza), `figure` (holding anime figure) |
| B | okita | 冲田 | light brown hair, boyish sadist smile, uniform | weapon katana; `bazooka` (aim bazooka on shoulder), `nap` (lying with eye-mask) |
| B | yamazaki | 山崎 | plain spy guy | `anpan`, `badminton` |
| B | ito | 伊东 | glasses, cold, white-ish coat over uniform | weapon katana; `glasses_push` |
| C | katsura | 桂 | long straight black hair, blue kimono + white haori | weapon katana; `bomb` (holding round bomb w/ lit fuse), `run_away` |
| C | katsura_short | 桂(短发) | same but hair cut short (Benizakura arc) | weapon katana |
| C | elizabeth | 伊丽莎白 | white duck-ghost blob with beak, feet; custom renderer | `idle walk run`, `sign` (holds a signboard; kw `sign="文字"`), `sad` |
| C | takasugi | 高杉 | dark purple hair, bandage over left eye, flamboyant purple kimono w/ gold butterflies, kiseru pipe | weapon katana; `smoke` (kiseru), `sit_rail` |
| C | sakamoto | 坂本 | messy curly black hair, sunglasses, red coat | weapon katana; `laugh` (AHAHAHA), `shoot` (pistol) |
| C | shiroyasha | 白夜叉 | war-time Gintoki: white haori/armour, headband, real katana | weapon katana; expr determined default |
| D | shouyou | 松阳 | long light-brown hair tied low, gentle closed-eye smile, pale green/beige kimono | weapon katana; `headbutt`, `smile` |
| D | gintoki_kid | 小银时 | child ~26 px, ragged clothes, silver hair, big sword | `eat` (rice ball), weapon katana |
| D | katsura_kid | 小桂 | child, long black hair, school kimono | weapon bokuto |
| D | takasugi_kid | 小高杉 | child, dark hair, both eyes, school kimono | weapon bokuto |
| D | okada_nizo | 冈田似藏 | shaved head, blind (closed eyes), dark kimono | weapon `benizakura`; `benizakura` (arm wrapped by red tendrils) |
| D | tsukuyo | 月咏 | blonde hair up, scar across face, black kimono, kunai | weapon `kunai`; `throw_kunai`, `smoke` |
| D | hinowa | 日轮 | courtesan, big hairdo w/ kanzashi, elegant kimono; cannot walk | `sit` (in wheelchair/seated), `smile` |
| D | seita | 晴太 | small boy ~26 px | `run`, `cry`, `push` |
| E | housen | 凤仙 | HUGE (~50 px) old Yato king, white hair/beard, black cloak, umbrella | weapon umbrella; `crumble` hint pose, `punch` |
| E | kamui | 神威 | vermilion braid, ahoge, closed-eye smile, dark china outfit, umbrella | weapon umbrella; expr `smile`, `open_eyes` (scary) |
| E | umibozu | 星海坊主 | bald with ONE hair strand, cloak, goggles, umbrella | weapon umbrella |
| E | oboro | 胧 | grey hair, scarred, black Naraku robes | weapon katana; `needle` (throwing needles) |
| E | utsuro | 虚 | Shouyou's face but cold red eyes, long dark hair, black robes | weapon katana; `regen` |
| E | shigeshige | 茂茂 | shogun: topknot, formal kamishimo, earnest face | `bow` |
| F | otsu | 阿通 | idol: twin tails, flashy outfit, mic | `sing` |
| F | catherine | 凯瑟琳 | cat-eared amanto maid | — |
| F | tama | 小玉 | robot maid, green hair | — |
| F | amanto_pig | 天人(猪) | pig-faced alien thug | weapon katana |
| F | amanto_cat | 天人(猫) | cat-eared alien thug | weapon katana |
| F | naraku | 奈落 | ninja with bamboo kasa hat, black robes, crow motif | weapon katana |
| F | harusame | 春雨 | space-pirate grunt (reptile face, armour) | weapon katana |
| F | townsman / townswoman | 路人 | Edo townsfolk for crowds (a few palette variants via kw `variant=0..3`) | — |

## 6. Sound effects (exact names; `audio/sfx.py` implements ALL of them)
One-shots: `blip type punch punch_big hit kick slap thud crash glass slash slash_big clang
shing stab gunshot machinegun bazooka explosion explosion_small bomb_fuse whoosh jump land
dash fly_away twinkle fall_whistle boing fail record_scratch pop squeak chomp gulp rimshot
sparkle shock sweat vein dizzy cough bark crow impact heartbeat bell gong thunder shine
aura charge laser door door_bang bell_shop coin cash cheer applause sting_dramatic
sting_comedy slide_up slide_down fanfare title_hit`
Loops (use `Cue(t, name, dur=seconds)`): `rain wind crowd fire river night battle scooter
train engine_hum footsteps run drumroll eat`

## 7. Music tracks (exact names)
`prologue` (ominous, sparse, 70 bpm) · `title` (starts with a BIG hit on beat 0, then heroic
upbeat, 150 bpm) · `yorozuya` (laid-back funky everyday theme, 110 bpm) · `comedy` (bouncy,
silly, 132 bpm) · `shinsengumi` (cool minor-key march, 120 bpm) · `tension` (dark suspense,
drone + heartbeat bass) · `battle` (fast driving minor, 165 bpm) · `yoshiwara` (Japanese
pentatonic, shamisen-like plucks, mysterious night) · `flashback` (music-box nostalgia, slow)
· `sad` (emotional slow melody) · `epic` (final-battle anthem, major, 150 bpm) · `ending`
(warm nostalgic upbeat, 120 bpm). All original compositions; seamless loops 30–60 s.

## 8. STORYBOARD (≈5 min, strictly chronological). Durations may flex ±2 s.
Dialogue below is guidance — keep the meaning, trim for timing. Mark each character's
first appearance with a name_card. Each scene should have ≥3 distinct shots/angles.

**s00 开场 Prologue (16 s)** music `[(0,"prologue"),(12,"title")]`
Starfield → UFO/spaceship fleet descends over old Edo (castle, rooftops) — narration
「二十年前，自称『天人』的外星人从天而降。」 → sunset battlefield, samurai silhouettes vs
alien ships — 「武士们奋起抵抗，史称『攘夷战争』。」 → rain, a katana falls/drops, a notice
board 「废刀令」 — 「幕府投降，废刀令颁布。武士的时代，结束了……」 → at 12.0 s white flash +
`title_hit`: big brush logo 「银魂」 slams in (shockwave, sakura burst, sparkle) with
「GINTAMA · 像素剧场」, Edo skyline with the Terminal tower and flying ships behind.

**s01 万事屋阿银 (18 s)** `yorozuya`
Kabukicho street (day) establishing: Otose's snack bar downstairs, 「万事屋银酱」 sign
upstairs, townsfolk + an amanto passing. → Interior: Gintoki asleep on the sofa, Jump over
his face, strawberry milk on the table, 「糖分」 frame on the wall. name_card 坂田银时
「万事屋老板｜天然卷·甜党·死鱼眼」. → Otose slams the door open 「银时！三个月的房租呢！」 /
Gintoki 「老太婆，下个月……一定。」 → Otose's kick: Gintoki flies out of the window, lands
on the street (dust, `thud`), name_card 登势 「楼下酒馆老板娘（房东）」. → He gets up,
deadpan nose-pick 「……今天的歌舞伎町，也很和平呢。」

**s02 新八登场 (20 s)** `comedy`
Family restaurant: Shinpachi as waiter carrying a tray, pig-faced amanto customers bully
him 「地球猴子！上菜慢死了！」. Gintoki at the counter with a chocolate parfait. The amanto
knocks the parfait over → silence (crow) → Gintoki's eyes turn serious → one bokuto hit,
amanto flies through the wall (impact, speed lines). → Manager: 「新八！你被开除了！」
name_card 志村新八 「吐槽担当｜本体是眼镜」. Shinpachi's huge tsukkomi at Gintoki
「你给我等一下！！」. → Shimura dojo: Otae smiles with a dark aura, name_card 志村妙
「新八的姐姐｜笑容可怕·暗黑料理」, offers a charred black egg 「请用～」 → Gintoki faints.
→ Shinpachi, determined: 「我要跟着这个人，找回我的武士道！」 → joins Yorozuya.

**s03 神乐与定春 (18 s)** `comedy`
Night: Gintoki on his scooter hits a girl (`crash`) — Kagura springs up unharmed:
「你撞到人了阿鲁！」 name_card 神乐 「夜兔族少女｜怪力·大胃王·『阿鲁』」. → She shoots
yakuza grunts with her umbrella gun (muzzle flashes). → Yorozuya table: rice bowls stack
into a tower, Gintoki+Shinpachi horrified, coins fly away from the wallet. → A box 「请收养」
: giant dog Sadaharu, name_card 定春 「巨型犬｜爱咬银时的头」, bites Gintoki's head
(`chomp`, legs flailing). → Group pose on the Yorozuya balcony, speed lines, big text
「万事屋，集结！」.

**s04 真选组 (20 s)** `shinsengumi`
Shinsengumi HQ gate 「真选组屯所」. → Kondo hiding in a bush stalking Otae at a shop;
she notices → super punch → Kondo flies into the sky and becomes a twinkling star.
name_card 近藤勋 「局长｜大猩猩·跟踪狂」. → Canteen: Hijikata squeezes a mountain of
mayonnaise on rice 「土方特制盖饭」, smoking. name_card 土方十四郎 「鬼之副长｜蛋黄酱狂魔」
→ Okita naps with an eye-mask, wakes, bazooka 「土方先生，去死吧。」 → BOOM → Hijikata
afro + soot 「总悟你这混蛋！！」 name_card 冲田总悟 「一番队队长｜抖S王子」. → the three
pose in front of the flag 「诚」.

**s05 桂与伊丽莎白 (16 s)** `comedy`
Rooftop chase: Katsura (+Elizabeth waddling) fleeing, Hijikata & Okita chasing, bazooka
shells behind. Okita 「假发——」 → Katsura turns, speed lines: 「不是假发，是桂！」 (make this
line BIG). name_card 桂小太郎 「攘夷志士｜逃跑的小太郎·天然呆」; Elizabeth holds sign
「……」 then 「快跑」, name_card 伊丽莎白 「谜之生物｜只用牌子说话」. → Katsura throws a lit
bomb; Gintoki walking below catches it, panics, throws it up → explosion in the sky like
fireworks. Gintoki (soot): 「为什么每次倒霉的都是我啊！」

**s06 日常 (18 s)** `comedy` — rapid manga-panel vignettes (~3 s each), panel borders:
1 Hasegawa in a cardboard box by the river 「MADAO（彻底没用的大叔）」 name_card 长谷川泰三.
2 Pachinko: Gintoki & Hasegawa lose everything, turn grey. 3 Monday: Gintoki reading Jump,
sparkling eyes 「周一＝Jump发售日」. 4 Otsu on stage singing, Shinpachi in happi coat with
light sticks 「通酱～！」 name_card 寺门通. 5 Kagura chewing sukonbu next to sleeping
Sadaharu 「醋昆布是正义阿鲁」. 6 Kondo hiding under Otae's floor → naginata stabs through.
End caption 「※以上皆为日常」.

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

**s08 真选组动乱篇 (22 s)** `[(0,"tension"),(~9,"battle")]` chapter_card 「真选组动乱篇」
Cursed sword: Hijikata becomes the timid otaku Toshi (dogeza, anime figure) name_card
托西 「被妖刀诅咒的宅男人格」. → Ito (glasses glint) schemes 「近藤局长……该退场了。」
name_card 伊东鸭太郎 「参谋｜野心家」. → Speeding train battle: traitors vs Kondo, Okita
slicing through a carriage, Yorozuya racing alongside in a police car. → Hijikata breaks
the curse (aura): 「我是……真选组副长——土方十四郎！！」 → final duel at sunset, Ito falls,
smiling: 「……谢谢。」

**s09 吉原炎上篇 (28 s)** `[(0,"yoshiwara"),(~11,"battle"),(~21,"epic")]` chapter_card 「吉原炎上篇」
Underground Yoshiwara: lanterns, iron ceiling, no sky. Seita wants to see his mother.
Tsukuyo name_card 「百华首领｜死神太夫」 「吉原没有太阳。」 → Hinowa in her tower, name_card
日轮 「吉原的太阳」. → Kamui on a roof, name_card 神威 「春雨第七师团团长｜神乐的哥哥」
「我只对强者感兴趣。」 → Housen, name_card 夜王凤仙 「吉原之主｜夜兔之王」. Gintoki is
smashed through walls, rises bloody: 「我的剑，是用来守护该守护的东西的。」 → the ceiling
opens: SUNLIGHT floods Yoshiwara (big light shafts). Housen weakens in the sun, Gintoki's
final strike. Housen looks up: 「太阳……原来是这么温暖的东西。」 crumbles into dust. →
Seita and Hinowa reunited in the sunlight, sakura.

**s10 将军暗杀篇 (18 s)** `[(0,"tension"),(~6,"battle")]` chapter_card 「将军暗杀篇」
Quick gag: Shogun Shigeshige, name_card 德川茂茂 「第十四代将军｜老实人」, sincerely
suffering some silly mishap (e.g. a bad haircut) 「将军家的头发……」. → Mountain pass,
escort: Naraku ninjas (kasa hats, crows) ambush; everyone fights — Shinsengumi, Yorozuya,
Katsura. → Oboro, name_card 胧 「天照院奈落首领」, vs Gintoki: 「你还是和那时一样，白夜叉。」
→ Gintoki's eyes widen — flash of a gentle smile (sensei) → white out into the flashback.

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

**s12 洛阳决战·离别 (18 s)** `[(0,"battle"),(~9,"sad")]` chapter_card 「洛阳决战篇」
Rain on planet Rakuyo: Kagura vs Kamui umbrella clash (shockwaves), Umibozu drops in
「够了！」 name_card 星海坊主 「最强的宇宙猎人｜神乐的秃头老爸」. Kagura: 「我一定会把哥哥
带回家阿鲁！」 Kamui smiles and leaves. → Shinsengumi farewell: a ship leaves Edo at dawn;
Kondo, Hijikata, Okita on deck; Hijikata lights a cigarette 「……我们会回来的。」 Otae on
the dock watching.

**s13 银之魂篇 (32 s)** `epic` (switch to `sad` for Takasugi's death, back to `epic` for the
final strike) chapter_card 「银之魂篇」
Alien armada darkens the sky over Edo; Utsuro appears, name_card 虚 「不死之身｜松阳的另一面」
「我即是虚。」 → EVERYONE ASSEMBLES montage on the rooftops (fast cuts, big text
「全江户，集结！」): Shinsengumi return, Katsura + Elizabeth army, Tsukuyo, Otae with
naginata, Otose/Catherine/Tama, Hasegawa, Sakamoto's ship, the Yato family (Kagura, Kamui,
Umibozu), Sadaharu. → Gintoki & Takasugi back to back vs Utsuro. Takasugi is mortally
wounded; dies in Gintoki's arms: 「银时……剩下的，交给你了。」 → dawn: Gintoki's final strike
(impact frame), Utsuro shatters into light; Shouyou's gentle face: 「……谢谢。你们都长大了呢。」
→ sunrise over Edo.

**s14 尾声 (22 s)** `ending`
「两年后……」 Kabukicho rebuilt; Shinpachi & Kagura keep the Yorozuya. A hooded wanderer in
the rain → hood off: Gintoki 「我回来了。」 → Kagura dropkick, Shinpachi 「你到底跑哪去了！！」
→ chaos resumes (quick cuts): Otae punches Kondo into a star, Okita bazookas Hijikata,
Katsura 「不是假发，是桂！」, Sadaharu chomps Gintoki. → A giant 「完」 stamp slams down;
Gintoki kicks it away 「才不会完呢！」 → all characters parade across the screen as credits
「原作：空知英秋《银魂》｜本片为同人像素致敬作品」 → 「感谢观看」 with Gintoki reading Jump.
