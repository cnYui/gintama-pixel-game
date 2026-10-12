export const meta = {
  name: 'gintama-pixel-video',
  description: 'Build characters, backgrounds, music/SFX, then 15 story scenes (implement + independent review/fix) for the Gintama pixel video',
  phases: [
    { title: 'Assets', detail: '6 character agents + background library' },
    { title: 'Audio', detail: '2 composers + SFX designer' },
    { title: 'Char QA', detail: 'consistency pass over all characters' },
    { title: 'Scenes', detail: 'one implementer per scene' },
    { title: 'Review', detail: 'independent critic+fixer per scene' },
  ],
}

const ROOT_WIN = 'C:\\Users\\yui\\AppData\\Roaming\\Claude\\scratch-workspaces\\955dbf55-b1fe-49c6-ac59-972ff2e7f6b1\\fd33c576-e552-48b9-b406-8dc43e0afecb\\scratch-2026-09-25-336c0d\\gintama_pixel'
const ROOT = '/c/Users/yui/AppData/Roaming/Claude/scratch-workspaces/955dbf55-b1fe-49c6-ac59-972ff2e7f6b1/fd33c576-e552-48b9-b406-8dc43e0afecb/scratch-2026-09-25-336c0d/gintama_pixel'

const PRE = `You are a member of a team producing a ~5-minute pixel-art animated video retelling the anime 银魂 (Gintama) in story order.
Project root (Windows path): ${ROOT_WIN}
In the Bash tool (Git Bash) ALWAYS start each command with: cd "${ROOT}" && ...   (python 3.12 with PIL/numpy/scipy and ffmpeg are on PATH). With Read/Write/Edit tools use the Windows absolute path.
FIRST read CONTRACT.md in full — it defines the APIs, style guide, file ownership, character ids, SFX/music names and the full storyboard.
Obey file ownership strictly: many other agents are editing OTHER files in the same tree at the same time. Never modify files you don't own; work around problems locally and report them. Put temporary/preview outputs under build/ in a subfolder named after your task (build/preview/ is fine for the provided tools).
Render code must be deterministic (use engine.core.rng, never the global random state).
Visual verification is mandatory: render PNGs and LOOK at them with the Read tool; iterate until the result is genuinely good, not just error-free.
Your final message is consumed programmatically by the lead: keep it short (limit given below) — what you made, exact names/APIs, and any problems with shared files.`

const CHAR_COMMON = `Write ONE file per character: chars/<id>.py that calls register(...) (see chars/gintoki.py, the reference, and chars/rig.py: ChibiDef params, POSES, draw_weapon kinds, CustomChar base for non-humanoids).
Requirements:
- Match the reference style exactly: same scale (adult head ≈18x17, torso ≈14x12, legs 7 → ≈34 px tall; kids head ≈15x14, torso ≈10x9, legs 5 → ≈26 px), 1px INK outline, 2–3 tones per material, light from top-left.
- Each character must be instantly recognisable at this tiny size by silhouette, hair shape/colour and signature feature. Faithful to the anime designs.
- Expressions: at least normal blink talk angry shout shock happy sad cry hurt smug (+ required extras). Use a BASE row list + per-expression row overrides like gintoki.py so all expressions stay aligned.
- Implement every required extra pose BY EXACT NAME (CONTRACT §5 roster) — reuse standard pose functions + props (small drawing callbacks using ctx['hand_f'], ctx['head'], ctx['torso'] etc.). Also make sure all standard poses look right (weapon in hand for attack/ready/guard/shoulder; sheathed weapon at the hip when not in hand if the character carries one).
- Set name (the short Chinese display name from the roster), color (name-tag colour, must be readable under white text with an ink outline), voice (0.65 deep male … 1.0 normal … 1.35 girl/child), desc (one-line Chinese description).
- Weapons: rig kinds bokuto, katana, umbrella, umbrella_open, bazooka, kunai, naginata, kiseru, benizakura, staff (or draw your own in a prop).
- Custom renderers (CustomChar subclass): support the pose names listed for them + reasonable fallbacks for other standard names (never crash), facing right, feet anchor, animate with t (12 fps stepping), cache static sprites; provide head(expr) for the dialogue portrait.
Verification loop (mandatory): "python charsheet.py <id>" for every id and view build/preview/char_<id>.png; also write a zoom script under build/<your task>/ rendering key poses/expressions at 5-6x next to gintoki and look closely; "python charsheet.py --all" → build/preview/lineup.png for side-by-side consistency. Fix anything off (misaligned heads, broken limbs, unreadable faces, wrong colours, inconsistent scale). Do at least 2 improvement passes.
Final answer limit: 150 words.`

const CHAR_GROUPS = [
  { key: 'A', ids: 'shinpachi, kagura, sadaharu, otae, otose, hasegawa',
    notes: `Canon look notes: shinpachi — short black hair, round glasses (his identity; add a glint), white kimono top + light-blue hakama, plain earnest face. kagura — vermilion/orange hair in two buns covered by small china-style bun covers, blue eyes, red qipao-style top with gold trim, loose pants, purple umbrella (it is also a gun). sadaharu — ENORMOUS fluffy white dog (~50x40 px), red eyebrow-like markings, droopy ears, black nose; bite pose with big jaws. otae — brown hair high ponytail, pink kimono, closed-eye sweet smile; dark_smile expression with a dark purple aura/shadowed eyes. otose — old lady, grey hair bun, dark purple kimono, cigarette, stern. hasegawa — ALWAYS sunglasses, stubble, messy dark hair, shabby beige clothes, sad sack posture.` },
  { key: 'B', ids: 'kondo, hijikata, toshi, okita, yamazaki, ito',
    notes: `Shinsengumi uniform: black jacket with gold/yellow trim and buttons, white cravat, black pants, katana at the hip. kondo — spiky short dark hair, stubble chin, square jaw, big friendly gorilla vibe; stalk pose with a bush prop he hides behind. hijikata — black hair with sharp V-shaped bangs, intense narrow eyes (dark blue-grey pupils), cigarette always in mouth (smoke wisps), mayo pose squeezing a mayonnaise bottle, afro expression = big black afro + soot face after an explosion. toshi — same uniform/face as hijikata but droopy timid eyes, sweat drops, slouched; beg (dogeza) and figure (holding a tiny anime figurine). okita — sandy light-brown hair, red-brown eyes, innocent pretty face with a sadistic smile; bazooka pose aiming a bazooka on the shoulder; nap = lying with a red eye-mask that has cartoon eyes drawn on it. yamazaki — plain dark hair, plain face, anpan (eating a bun), badminton (swinging a racket). ito — light brown hair, rectangular glasses (glint), cold look, pale grey/white long coat over the uniform.` },
  { key: 'C', ids: 'katsura, katsura_short, elizabeth, takasugi, sakamoto, shiroyasha',
    notes: `katsura — very long straight black hair to the waist, serious pretty face, dark blue kimono with a white/beige haori; bomb pose holding a round black bomb with a lit sparking fuse. katsura_short — same outfit, hair cut short at the neck (after Benizakura). elizabeth — white duck/penguin-like blob creature (like a ghost in a sheet) with a yellow beak, big round eyes, small yellow feet; sign pose holds a white signboard showing kw sign text (render with engine.text 12px pixel font, black text); waddle walk. takasugi — dark purple hair, white bandage covering his LEFT eye, flamboyant purple kimono with golden butterfly pattern, kiseru pipe, cold smirk; sit_rail pose sitting on a ship railing. sakamoto — messy curly dark-brown hair, sunglasses, red/crimson coat over kimono, big open laugh (laugh pose "AHAHAHA"), shoot pose with a pistol. shiroyasha — war-era young Gintoki: silver hair, white haori/coat over light armour, real katana, grim determined face.` },
  { key: 'D', ids: 'shouyou, gintoki_kid, katsura_kid, takasugi_kid, okada_nizo, tsukuyo, hinowa, seita',
    notes: `shouyou — long light-brown hair tied loosely low at the back, gentle closed-eye smile, pale green/beige kimono + haori, katana; headbutt pose (lunging head forward), smile. Kids ≈26 px: gintoki_kid — messy silver hair, ragged dirty kimono, clutching a big katana; eat pose with a rice ball. katsura_kid — long black ponytail, school kimono, bokuto. takasugi_kid — dark purple hair, BOTH eyes visible, school kimono, bokuto, fierce. okada_nizo — shaved head with stubble, blind closed eyes, dark kimono; benizakura pose: arm wrapped/pulsing with red organic tendrils, red sword. tsukuyo — blonde hair up with kanzashi, scars on forehead and cheek, black short kimono with purple accents, kunai (throw_kunai pose), kiseru (smoke pose). hinowa — elegant oiran: black hair in an elaborate hairdo with many kanzashi, red/gold kimono, gentle smile; she cannot walk: sit pose seated (wheelchair or cushion prop). seita — small boy, short dark hair, simple kimono; push pose (pushing forward, e.g. a wheelchair).` },
  { key: 'E', ids: 'housen, kamui, umibozu, oboro, utsuro, shigeshige',
    notes: `housen — HUGE old Yato king (~50 px tall; bigger head/torso art and longer limbs via ChibiDef params), long white hair and white beard/mustache, pale skin, black cloak/robe, umbrella, fierce; crumble pose (hint of dust flaking). kamui — vermilion/orange hair in a long braid, ahoge, closed-eye smile (expr smile default-ish), open_eyes expression (scary blue eyes), dark navy china outfit, umbrella. umibozu — shiny bald head with ONE long hair strand, goggles on forehead, mustache, dark cloak, umbrella. oboro — grey/white hair, facial scars, black Naraku robes with a crow emblem, cold eyes; needle pose throwing needles. utsuro — Shouyou's face but eerie: long dark hair, glowing red eyes, black robes; regen pose (dark wisps). shigeshige — shogun: chonmage topknot, thick earnest eyebrows, serious face, formal blue kamishimo with winged shoulders; bow pose.` },
  { key: 'F', ids: 'otsu, catherine, tama, amanto_pig, amanto_cat, naraku, harusame, townsman, townswoman',
    notes: `otsu — idol Terakado Tsuu: twin tails, flashy pink/black idol outfit, microphone; sing pose. catherine — cat-eared amanto maid, grey hair, sly face, dark kimono + apron. tama — robot maid, long green hair, green kimono + white apron, blank robotic eyes. amanto_pig — pig-faced alien thug (snout, tusks), armour; amanto_cat — cat-faced alien thug. naraku — Tendoshu assassin: big bamboo kasa hat hiding the face, black robes, crow-feather motif, katana (or staff). harusame — space-pirate grunt: reptile/fish-like face, armour. townsman / townswoman — Edo commoners for crowds; support kw variant=0..3 that swaps palettes (subclass ChibiDef and override render; ChibiDef.render ignores unknown kw by default, so pop 'variant' yourself; cache per variant).` },
]

const BG_PROMPT = `${PRE}

TASK: build the shared background library in bg/ (you own bg/*.py). ~10 scene agents will import it right after you finish, so make it beautiful and document it well.
Create:
1. bg/common.py — sky(img, tod, t) for tod in 'day','dusk','night','dawn','storm' (banded + dithered gradients, sun/moon, stars at night); clouds(img, t, cam_x=0, tod='day', seed=0); big_moon(img, x, y, r); far_mountains(img, cam_x, tod, y); river(img, y, h, t, tod) (animated water shimmer); bridge(img, cam_x, y, tod) (wooden arched Japanese bridge with railings); cherry_tree(img, x, y, t, scale=1) (swaying, petals); lantern(img, x, y, t, color=red) (paper chochin, swaying, glow halo at night); a few ground helpers (stone street, wooden floor, tatami).
2. bg/kabukicho.py — street(img, cam_x, t, tod='day'): long horizontally scrolling Kabukicho street (wraps seamlessly, world width STREET_W) with: the Otose snack-bar building (ground floor noren/sign 「登势」 snack) with the Yorozuya on the second floor (big sign 「万事屋银酱」, balcony, outside wooden staircase), other shops with noren curtains, signboards, lanterns, power poles/wires, amanto-era touches (neon signs, a hovering car/ship far away). Constants: YOROZUYA_X (world x of that building's centre), FLOOR_Y = 160 (feet line on the street). Also yorozuya_front(img, t, tod) — a framed establishing shot of the building front, with BALCONY_Y (feet line on the balcony, for group poses) and constants for where the window and door are.
3. bg/yorozuya.py — office(img, t, tod='day'): Yorozuya office interior: back wall with the framed calligraphy 「糖分」, window showing the sky for tod, Gintoki's desk + chair centre-back, two sofas facing each other with a low table in front (strawberry-milk carton on it), TV, stack of Jump magazines, sliding door (shoji) at the right; constants FLOOR_Y, SOFA_L_X, SOFA_R_X, SOFA_SEAT_Y, DESK_X, DOOR_X, WINDOW_BOX. Optional office_fg(img, t) foreground layer (e.g. table front) to draw over characters sitting behind it.
4. bg/edo.py — skyline(img, cam_x, t, tod='day', ships=True): Edo panorama — layers of traditional tiled rooftops, Edo castle, and the enormous 'Terminal' spaceport tower (tall futuristic tower in the centre) with alien spaceships drifting; ship(img, x, y, kind, t, scale=1) for reuse (≥3 kinds: small saucer, long cruiser, giant mothership); fleet(img, t, density=1.0, cam_x=0) — an ominous alien armada darkening the sky (final arc).
Quality bar: detailed yet readable at 384x216, clear depth (≥3 parallax layers, atmospheric perspective: far = bluer/lighter/less contrast), ambient animation (lanterns swaying, flags, smoke, windows flicker, ships drifting). Backgrounds a bit darker/less saturated than characters so characters pop. Use the INK outline sparingly on big shapes.
Performance: pre-render static layers once (module-level cache keyed by params) then paste with offsets per frame — each call must cost < 8 ms (measure it).
Verify: write build/bg/demo.py rendering every function for every tod (and several cam_x) into PNGs, plus a few characters drawn at FLOOR_Y with chars.draw_char to check scale (a character is ~34 px tall; doors should be ~42 px tall). LOOK at them and iterate for beauty (≥2 passes).
Final answer limit: 200 words — list every public function/constant with its signature.`

const SFX_PROMPT = `${PRE}

TASK: sound designer. Implement EVERY sound effect named in CONTRACT.md §6 in audio/sfx.py (you own only that file).
API: from engine.audio import sfx ; from engine.synth import *  (read engine/synth.py and engine/audio.py). Register with @sfx("name") (or @sfx("name", loop=True) for the loop list) on a zero-arg function returning a mono float32 numpy array (stereo (n,2) allowed) at SR=44100. The mixer caches results and pitch-shifts by resampling (cue pitch), so generate at a natural pitch.
Style: retro/chiptune + anime-comedy flavoured, punchy and clean. Guidelines: blip = the dialogue voice (very short ~40 ms square blip ~520 Hz, fast decay; it is resampled per character so keep it neutral); type = soft typewriter tick for narration; punch/punch_big = comic impacts with bass thump (big one with sub-drop + noise crack); slap = sharp tsukkomi smack; slash = sword whoosh + metallic ring; slash_big heavier; clang = metal clash with bright ringing partials; shing = sword unsheath shimmer; explosion = big boom (noise + low sweep + crackle tail ~1.5 s); bazooka = fire thump + whoosh; fly_away = rising whistle that fades (someone launched into the sky); twinkle = high 'kira~' sparkle when they become a star; fall_whistle = descending whistle; fail = sad trombone 'wah-wah-wah-waaah'; crow = awkward-silence crow 'kaa… kaa' (synthesised caw: formant-ish noisy square with pitch drop); chomp = dog bite crunch; bark = big dog woof; shock = anime shock sting; vein = anger-mark pop; title_hit = massive logo slam (crash + low chord stab + shimmer, 2 s); sting_dramatic = 'dun dun DUNN'; fanfare = short victory jingle; impact = deep cinematic boom; aura = rising power-up whoosh; shine = holy chime pad (sunlight); heartbeat = lub-dub. Loops (seamless, 2–6 s each): rain, wind, crowd (murmur), fire (crackle), river, night (crickets), battle (distant clashes & shouts-like noise), scooter (putt-putt engine), train (chug + clack), engine_hum (spaceship drone), footsteps, run, drumroll, eat (munching).
Loudness: one-shots peak ≈ 0.8; loops quieter (peak ≈ 0.5). No DC offset, no clicks (short fades at ends; loops must wrap seamlessly).
Performance: generating ALL sfx must take < 20 s total (vectorised numpy; scipy.signal.lfilter available).
Verify: write build/sfx/check.py that imports audio.sfx, confirms every CONTRACT name is registered (and loop flags right), generates each, checks dtype/NaN/peak/duration/DC and loop seams, writes WAVs to build/sfx/, and prints a table. Fix until clean.
Final answer limit: 120 words.`

const MUSIC_COMMON = `API: from engine.audio import track ; from engine.synth import *  (read engine/synth.py: oscillators, envelopes, parse_seq/render_seq, instruments inst_pulse/inst_tri/inst_pluck, drums kick/snare/hat/drum_pattern, delay, lowpass/highpass, stereo, mix, normalize). Each track: @track("name") on a zero-arg function returning a stereo float32 array (n,2) — a SEAMLESS LOOP 30–60 s long made of whole bars (render one extra bar of tail and fold it back onto the start; make the harmony at the end lead back into bar 1).
Sound palette (shared with the other composer so the soundtrack is coherent): NES-like — 2 pulse leads (duty 12.5/25/50%), triangle bass, noise drums, plus optional soft sine/triangle bells and pads, light stereo width (pan leads slightly, delay() echoes). Gentle lowpass on pulses (~6–8 kHz) so it is never harsh.
Musicality matters most: real chord progressions, memorable ORIGINAL melodies with phrasing (call & response, motifs that develop), counter-melodies, walking/syncopated bass, drum fills at phrase ends, A/B sections with dynamics. Do NOT reproduce any existing song's melody (no real Gintama OP/ED themes) — all original.
Loudness: every track RMS ≈ 0.14–0.18 and peak ≤ 0.85 (normalize at the end) so tracks sit at the same level.
Performance: generating all your tracks must take < 60 s total (vectorise; avoid per-sample Python loops over whole tracks; scipy.signal.lfilter is available).
Verify: a script under your build subfolder that imports your module, generates each track, checks shape/dtype/NaN/RMS/peak/duration and loop-seam continuity (RMS of last vs first 50 ms, no click), writes WAVs, and prints a summary. You cannot listen, so reason carefully about theory (keys, voice leading, rhythm, tempo) and double-check note tables.
Final answer limit: 120 words — per track: key, bpm, length, structure in one line.`

const MUSIC_A = `${PRE}

TASK: composer A. Write audio/music_a.py (you own only that file; audio/music.py already imports it). Tracks:
- prologue: ominous & sparse, 70 bpm, D minor; low triangle drones, distant temple-bell tolls, a lonely pulse lament melody, wind-like filtered-noise swells; grand and mysterious (s00 uses its first 12 s, then the title track takes over).
- title: HEROIC and punchy, 150 bpm; beat 0 is a BIG hit (noise crash + low octave chord stab) because it syncs with the logo slam; then a driving chiptune rock anthem with a catchy lead hook, energetic drums (only ~4–6 s are heard under the logo, then it crossfades — so make the first 6 s the most exciting part).
- yorozuya: laid-back funky everyday theme (Gintama's lazy Kabukicho vibe), 110 bpm, swing, syncopated bass, jazzy 7th chords, slidey lead.
- comedy: bouncy silly theme, 132 bpm, staccato plucks, oom-pah bass, playful chromatic runs, woodblock-ish percussion.
- shinsengumi: cool minor-key march, 120 bpm, snare rolls, taiko-like kicks, determined heroic lead.
- ending: warm nostalgic upbeat, 120 bpm, major key, bittersweet singable melody (final-episode credits feel), gentle arpeggios; 40–60 s.
${MUSIC_COMMON}`

const MUSIC_B = `${PRE}

TASK: composer B. Write audio/music_b.py (you own only that file; audio/music.py already imports it). Tracks:
- tension: dark suspense ~80 bpm; low drone + heartbeat-like bass pulses, dissonant minor-2nd stabs, sparse glassy high notes, slowly building.
- battle: fast driving minor, 165 bpm; 16th-note arpeggios, aggressive lead, pounding drums, a lift/modulation in the second half.
- yoshiwara: Japanese in/miyako-bushi pentatonic, shamisen-like plucks (short decaying pulses with a little pitch bend), koto arpeggios, slow taiko; mysterious lantern-lit night district.
- flashback: music-box nostalgia, 72 bpm, sine/triangle bells with delay, simple innocent major melody with a hint of sadness.
- sad: deeply emotional slow melody, 66 bpm, minor → relative major lift, vibrato pulse lead, sustained triangle bass, soft pads.
- epic: final-battle anthem, 150 bpm, heroic major key, rising progressions, big drums, counter-melodies, key change for the climax; 40–60 s.
${MUSIC_COMMON}`

const QA_PROMPT = `${PRE}

TASK: character consistency QA across ALL characters. You may edit any chars/*.py EXCEPT chars/rig.py, chars/__init__.py and chars/gintoki.py. Scene agents are using these characters RIGHT NOW, so NEVER rename ids, remove poses/expressions or change call signatures — only improve art/palettes/proportions and fix bugs (keep each edit atomic: write the whole file in one Write).
1. "python charsheet.py --all" → view build/preview/lineup.png; "python charsheet.py <id>" for every id → view each sheet; zoom into suspicious ones at 5x with your own script under build/charqa/.
2. Check: consistent scale (adults ≈34 px, kids ≈26 px, housen/sadaharu big), 1px INK outlines everywhere, consistent palette/shading/light direction, recognisability and canon accuracy (hair colours, signature features per CONTRACT §5), every standard pose renders without errors or broken/detached limbs, all required extra poses/expressions exist and look right, name/color/voice sensible, name-tag colours readable.
3. Fix issues directly; re-verify.
Final answer limit: 150 words.`

const SCENES = [
  { id: 's00', slug: 'prologue', title: '开场', dur: 16 },
  { id: 's01', slug: 'yorozuya', title: '万事屋阿银', dur: 18 },
  { id: 's02', slug: 'shinpachi', title: '新八登场', dur: 20 },
  { id: 's03', slug: 'kagura', title: '神乐与定春', dur: 18 },
  { id: 's04', slug: 'shinsengumi', title: '真选组', dur: 20 },
  { id: 's05', slug: 'katsura', title: '桂与伊丽莎白', dur: 16 },
  { id: 's06', slug: 'daily', title: '日常', dur: 18 },
  { id: 's07', slug: 'benizakura', title: '红樱篇', dur: 26 },
  { id: 's08', slug: 'mayo_crisis', title: '真选组动乱篇', dur: 22 },
  { id: 's09', slug: 'yoshiwara', title: '吉原炎上篇', dur: 28 },
  { id: 's10', slug: 'shogun', title: '将军暗杀篇', dur: 18 },
  { id: 's11', slug: 'shouyou', title: '松阳老师', dur: 26 },
  { id: 's12', slug: 'rakuyo', title: '洛阳决战·离别', dur: 18 },
  { id: 's13', slug: 'silver_soul', title: '银之魂篇', dur: 32 },
  { id: 's14', slug: 'epilogue', title: '尾声', dur: 22 },
]

function scenePrompt(s, i) {
  const prev = i > 0 ? `${SCENES[i - 1].id} ${SCENES[i - 1].title}` : '(none — this opens the video)'
  const next = i < SCENES.length - 1 ? `${SCENES[i + 1].id} ${SCENES[i + 1].title}` : '(none — this ends the video)'
  return `${PRE}

TASK: implement scene ${s.id} 「${s.title}」 (${s.dur} s) as scenes/${s.id}_${s.slug}.py (you own this file and optional private helpers scenes/_${s.id}_*.py). Its storyboard is in CONTRACT.md §8 under **${s.id}**. Previous scene: ${prev}; next scene: ${next} (other agents write them in parallel — keep continuity: same characters, shared bg library, consistent look).
Assets available now: characters in chars/*.py (ls chars; READ the file of every character you use to learn exact extra pose names, weapons, expressions; view build/preview/lineup.png and build/preview/char_<id>.png — run "python charsheet.py <id>" if missing), shared backgrounds in bg/*.py (read their docstrings), engine in engine/*.py, idioms in scenes/example_scene.py. Scene-specific backgrounds/props you draw yourself in your own file(s). Music/SFX modules may still be in progress — just use the exact names from CONTRACT §6/§7.
Direction goals — the user asked for: 动画好看、有趣、场景丰富 (beautiful animation, funny, rich variety of scenes):
- ≥3 distinct shots/locations/camera setups; cinematic camera (pans, push-ins via fx.zoom, parallax), cuts timed to the beats; never a dead static frame — always something moving (idle breathing, particles, ambient animation).
- Comedy lands: anticipation → hold → impact (speed lines, sfx_text, shake, flash) → reaction face. Drama breathes: slower pacing, letterbox, silhouettes, dramatic lighting, impact frames.
- Faithful to Gintama canon (looks, relationships, catchphrases). Characters must be readable: big enough, clearly staged, not hidden behind the dialogue box (keep them above y≈168 while a dialogue box shows) or name cards.
- All subtitles in Chinese via self.subs, timing rules in CONTRACT §3 (typing 16 chars/s + ≥1.3 s reading, no overlaps); name_card on each character's first appearance in the video (per storyboard); SFX Cues precisely synced with on-screen events (every hit/explosion/door/jump/landing/whoosh gets a cue; ambience loops with dur); music per storyboard.
- Performance < 60 ms/frame average (cache static layers at module level).
Process: 1) write a shot list with exact timings as a comment at the top of the file; 2) implement; 3) "python preview.py ${s.id} --check" → 0 errors; 4) contact sheets "python preview.py ${s.id} --step 0.5" (use --range to split long scenes) and "--at" 3x close-ups of every key moment — LOOK at them; 5) fix composition/timing problems and polish; repeat 4–5 at least twice.
Final answer limit: 200 words — shot list with time ranges, characters/poses used, any problems in shared files (chars/bg/engine) you had to work around.`
}

function reviewPrompt(s, impl) {
  return `${PRE}

TASK: you are the independent REVIEWER and FIXER for scene ${s.id} 「${s.title}」 (scenes/${s.id}_*.py and its private helpers; the implementer has finished and you now own these files). Storyboard: CONTRACT.md §8 **${s.id}** (target ${s.dur} s ±2).
Implementer's summary: <<<${(impl || '(no summary)').slice(0, 1800)}>>>
Review with fresh, critical eyes — as a demanding anime director AND a Gintama fan. The user wants: 动画好看、有趣、场景丰富.
1. Render: "python preview.py ${s.id} --check", contact sheets with --step 0.5 (split with --range for readability), and --at 3x frames for every beat. LOOK carefully.
2. Find concrete problems: story beats missing/wrong vs storyboard or canon; characters unrecognisable, wrong ids/poses/expressions; gags that don't land (no anticipation/impact/reaction); dead static stretches > 1.5 s; unclear staging (who is where; action too tiny to read); characters covered by the dialogue box or name cards; text overflow/overlap; subtitles too short to read (typing 16 chars/s + ≥1.3 s) or overlapping; visual glitches (magenta error frames, clipped sprites, z-order errors, flicker, jarring pops); missing SFX cues or cues out of sync with the visuals; unknown SFX/music names (--check lists them now that audio exists); missing name cards; > 60 ms/frame; wrong duration.
3. FIX every problem directly in the file(s) — improve rather than rewrite, unless something is truly broken — then re-render and verify again. Raise the quality noticeably: richer motion, better timing, stronger comedic/dramatic punch.
Final answer limit: 150 words — fixes made and anything still imperfect.`
}

// ---- Audio (runs alongside everything; awaited at the end)
const audioPromise = parallel([
  () => agent(MUSIC_A, { label: 'music:A', phase: 'Audio' }),
  () => agent(MUSIC_B, { label: 'music:B', phase: 'Audio' }),
  () => agent(SFX_PROMPT, { label: 'sfx', phase: 'Audio' }),
])

// ---- Characters + backgrounds (barrier: every scene needs them)
phase('Assets')
const assets = await parallel([
  ...CHAR_GROUPS.map(g => () => agent(`${PRE}\n\nTASK: create the pixel-art chibi characters: ${g.ids} (roster rows in CONTRACT.md §5).\n${g.notes}\n${CHAR_COMMON}`, { label: `chars:${g.key}`, phase: 'Assets' })),
  () => agent(BG_PROMPT, { label: 'backgrounds', phase: 'Assets' }),
])
log(`assets done: ${assets.filter(Boolean).length}/${assets.length}`)

// ---- Character QA runs concurrently with the scenes
const qaPromise = agent(QA_PROMPT, { label: 'char-qa', phase: 'Char QA' })

// ---- Scenes: implement -> independent review+fix (pipelined per scene)
const scenes = await pipeline(
  SCENES,
  (s, _orig, i) => agent(scenePrompt(s, i), { label: `scene:${s.id}`, phase: 'Scenes' }),
  (impl, s) => agent(reviewPrompt(s, impl), { label: `review:${s.id}`, phase: 'Review' })
    .then(r => ({ id: s.id, impl, review: r })),
)

const qa = await qaPromise
const audio = await audioPromise
return { assets, qa, audio, scenes }
