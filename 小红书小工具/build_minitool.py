r"""把银魂游戏打成小红书小工具 zip（<10MB）；加 --web 则打成公网版（dist-web/：index.html + v<时间戳>/）。只读 游戏\ 下的原文件，输出到 小红书小工具\dist 和 yinhun-minitool.zip。

做的事：
  1. 只拷运行时用到的文件（data.js 引用的素材 + 代码里硬写路径的素材）
  2. PNG → WebP 无损（规范允许 .webp；视觉上与原图逐像素一致）
  3. 音频重编码为单声道低码率 mp3（音乐 40kbps/32kHz，音效 48kbps/32kHz）
  4. 开场视频只留 mp4（取 dist-compressed 里已压好的 640x360 版）
  5. 代码补丁（只改容器不允许的东西）：
       - engine/touch.js  去掉全屏（requestFullscreen 被容器禁用）→ 全屏按钮自动隐藏
       - main.js          预加载正则认 .webp
       - story/stages.js  硬写的 3 个图片路径 .png → .webp
       - data.js          图片路径 .png → .webp；去掉 webm 视频
  6. 用 zip 打包，index.html 在根目录
"""
import io, json, os, re, shutil, subprocess, sys, zipfile
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

G = r'D:\CodeWorkSpace\gintama-pixel-game\游戏'
HERE = os.path.dirname(os.path.abspath(__file__))
PROBE = '--audio-probe' in sys.argv   # 声音探针版 = 无声版 + 页面一加载就用 WebAudio 播放 base64 内嵌的标题曲（验证容器能不能出声），输出到 dist-probe / yinhun-minitool-audioprobe.zip
AUDIO = '--audio' in sys.argv         # 带声音版：音频不当 mp3 文件放（平台不收），改成 base64 写进 audio/*.js，运行时 WebAudio 解码播放（web_extras/audio_web.js 替换 G.audio）；加 --release 去掉左下角调试状态条
SILENT = '--silent' in sys.argv or PROBE or AUDIO      # 无声版：小红书只允许 jpg/css/gif/svg/png/js/jpeg/json/html/woff2/webp/woff，mp3/mp4 会部署失败
WEB = '--web' in sys.argv             # 公网版（aaccx.pw/gintama/）：音频 / 视频照常带上；入口页在根目录，其余放进版本号目录；不打 zip
PACK = SILENT or WEB or '--pack' in sys.argv   # 小红书限制 zip 内文件数 ≤200：图片转 base64 data URI 写进少量 pack/pNN.js
VER = 'v' + __import__('datetime').datetime.now().strftime('%Y%m%d-%H%M%S')
WEB_ROOT = os.path.join(HERE, 'dist-web')
OUT = os.path.join(WEB_ROOT, VER) if WEB else os.path.join(HERE, 'dist-probe' if PROBE else 'dist-audio' if AUDIO else 'dist-silent' if SILENT else 'dist')
ZIP = os.path.join(HERE, 'yinhun-minitool-audioprobe.zip' if PROBE else 'yinhun-minitool-audio.zip' if AUDIO else 'yinhun-minitool-silent.zip' if SILENT else 'yinhun-minitool.zip')
DC = os.path.join(G, 'dist-compressed')          # 取已压好的 mp4

def rd(p): return open(p, encoding='utf-8').read()
def wr(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'w', encoding='utf-8', newline='\n').write(s)

if WEB and os.path.exists(WEB_ROOT): shutil.rmtree(WEB_ROOT)          # dist-web 里只留当前这一版
if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)

# ---------- data.js
src = rd(os.path.join(G, 'data.js'))
assert src.startswith('window.GAME_DATA = ') and src.rstrip().endswith(';')
data = json.loads(src[len('window.GAME_DATA = '):].strip().rstrip(';'))

png_refs, mp3_refs = set(), set()
def walk(o):
    if isinstance(o, str):
        if o.lower().endswith('.png') and o.startswith('assets/'): png_refs.add(o)
        elif o.lower().endswith('.mp3') and o.startswith('assets/'): mp3_refs.add(o)
    elif isinstance(o, list): [walk(v) for v in o]
    elif isinstance(o, dict): [walk(v) for v in o.values()]
walk(data)
# 代码里硬写的图片路径（data.js 没登记，原来压缩版漏了 war/tent.png）
for f in ['story/stages.js']:
    for m in re.finditer(r"['\"](assets/[^'\"]+\.png)['\"]", rd(os.path.join(G, f))): png_refs.add(m.group(1))
for f in ['main.js'] + [f'engine/{x}' for x in os.listdir(os.path.join(G, 'engine'))] + [f'story/{x}' for x in os.listdir(os.path.join(G, 'story'))]:
    if f.endswith('.js'):
        for m in re.finditer(r"['\"](assets/[^'\"]+\.(?:png|mp3))['\"]", rd(os.path.join(G, f))):
            (png_refs if m.group(1).endswith('.png') else mp3_refs).add(m.group(1))
print(f'图片 {len(png_refs)} 张，音频 {len(mp3_refs)} 个')

def retarget(o):
    if isinstance(o, str): return re.sub(r'\.png$', '.webp', o, flags=re.I) if o.startswith('assets/') else o
    if isinstance(o, list): return [retarget(v) for v in o]
    if isinstance(o, dict): return {k: retarget(v) for k, v in o.items() if not (k == 'webm' and isinstance(v, str))}
    return o
data2 = retarget(data)
audio_refs = []
if SILENT:
    if AUDIO:      # 带声音版：登记保留，素材走 base64 分包（见下面“音频打包”）；视频仍然进不去
        if '--no-title-song' in sys.argv: data2['audio']['music'].pop('title_song', None)
        audio_refs = sorted({v for grp in data2['audio'].values() for v in grp.values() if isinstance(v, str)})
    else:
        data2['audio'] = {k: {} for k in data.get('audio', {})}
    data2['video'] = {}; mp3_refs.clear()
if WEB:
    if '--no-title-song' in sys.argv:       # 默认带标题曲（用户决定：放在自己的服务器上，用原文件）；想去掉就加这个参数
        data2['audio']['music'].pop('title_song', None)
    mp3_refs = {v for grp in data2['audio'].values() for v in grp.values() if isinstance(v, str)}
wr(os.path.join(OUT, 'data.js'), 'window.GAME_DATA = ' + json.dumps(data2, ensure_ascii=False, separators=(',', ':')) + ';\n')

# ---------- 代码（带补丁）
def patch(rel, subs):
    s = rd(os.path.join(G, rel))
    for pat, rep, cnt in subs:
        s, n = re.subn(pat, rep, s)
        assert n == cnt, f'{rel}: 补丁 {pat!r} 命中 {n} 次，应为 {cnt}'
    wr(os.path.join(OUT, rel), s)

patch('main.js', [(r"/\\\.png\$/i\.test\(o\)", r"/\\.(png|webp)$/i.test(o)", 1)])
patch('story/stages.js', [(r"(assets/[^'\"]+)\.png", r"\1.webp", 3)])
patch('engine/core.js', [(r"im = new Image\(\); im\.src = src;", "im = new Image(); im.src = (window.PACK && window.PACK[src]) || src;", 1)] if PACK else [])
patch('engine/touch.js', [] if WEB else [(r"const reqFs = de\.requestFullscreen \|\| de\.webkitRequestFullscreen;",
                           "const reqFs = null;       // 小红书小工具容器禁用 requestFullscreen：置空后下面会自动隐藏全屏按钮", 1)]
      + ([(re.escape('if (primed || !T.ios || !G.D.audio) return;'), 'if (primed || !T.ios || !G.D.audio || G.audio.web) return;', 1)] if AUDIO else []))   # 带声音版：iOS 的 blob 静音 wav 预热会被容器 CSP 拦，用不着了
# Chrome 61（Android 8.1 出厂 WebView）兼容：官方文档要求 ES2017；es2017_check.js 扫出来的写法在这里改成等价的老写法
COMPAT = {'script.js': [(re.escape('G.world.player?.cid'), '(G.world.player && G.world.player.cid)', 1)]}
for f in os.listdir(os.path.join(G, 'engine')):
    if f.endswith('.js') and f not in ('touch.js', 'core.js'): patch(f'engine/{f}', COMPAT.get(f, []))
for f in os.listdir(os.path.join(G, 'story')):
    if f.endswith('.js') and f != 'stages.js': patch(f'story/{f}', [])

# ---------- 图片 → WebP 无损
import base64
def conv(r):
    im = Image.open(os.path.join(G, r)).convert('RGBA')
    rel = re.sub(r'\.png$', '.webp', r, flags=re.I)
    if PACK:
        cp = os.path.join(HERE, '_tmp', 'webp_cache', rel)          # 缓存：原 png 没变就不重转
        if os.path.exists(cp) and os.path.getmtime(cp) > os.path.getmtime(os.path.join(G, r)):
            return rel, open(cp, 'rb').read()
        b = io.BytesIO(); im.save(b, 'WEBP', lossless=True, quality=100, method=6)
        os.makedirs(os.path.dirname(cp), exist_ok=True); open(cp, 'wb').write(b.getvalue())
        return rel, b.getvalue()
    out = os.path.join(OUT, rel); os.makedirs(os.path.dirname(out), exist_ok=True)
    im.save(out, 'WEBP', lossless=True, quality=100, method=6)
    return rel, os.path.getsize(out)
with ThreadPoolExecutor(8) as ex: conv_res = list(ex.map(conv, sorted(png_refs)))
if PACK:
    img_bytes = sum(len(b) for _, b in conv_res)
    packs, cur, cur_len = [], {}, 0
    for rel, b in conv_res:
        uri = 'data:image/webp;base64,' + base64.b64encode(b).decode('ascii')
        cur[rel] = uri; cur_len += len(uri)
        if cur_len > 400_000: packs.append(cur); cur, cur_len = {}, 0
    if cur: packs.append(cur)
    for n, d in enumerate(packs):
        wr(os.path.join(OUT, f'pack/p{n:02d}.js'), 'window.PACK=window.PACK||{};Object.assign(window.PACK,' + json.dumps(d, ensure_ascii=False, separators=(',', ':')) + ');\n')
    html = rd(os.path.join(G, 'index.html')); tags = ''.join(f'<script src="pack/p{n:02d}.js"></script>\n' for n in range(len(packs)))
    assert '<script src="data.js"></script>' in html
    if PROBE:      # 标题曲 → 单声道 32kHz 40kbps mp3 → base64 文本；探针脚本放在所有 pack 之前，页面一加载就开始解码 / 播放
        mp3 = os.path.join(HERE, '_tmp', 'audio_probe.mp3'); os.makedirs(os.path.dirname(mp3), exist_ok=True)
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', os.path.join(G, 'assets', 'audio', 'user', 'title_song.mp3'), '-vn', '-ac', '1', '-ar', '32000',
                        '-codec:a', 'libmp3lame', '-b:a', '40k', mp3], check=True)
        b64 = base64.b64encode(open(mp3, 'rb').read()).decode('ascii')
        wr(os.path.join(OUT, 'probe/audio_data.js'), 'window.__AUDIO_PROBE_B64="' + b64 + '";\n')
        wr(os.path.join(OUT, 'probe/audio_probe.js'), rd(os.path.join(HERE, 'web_extras', 'audio_probe.js')))
        tags = '<script src="probe/audio_data.js"></script>\n<script src="probe/audio_probe.js"></script>\n' + tags
        print(f'声音探针: mp3 {os.path.getsize(mp3)/1e6:.2f} MB → base64 js {len(b64)/1e6:.2f} MB')
    html = html.replace('<script src="data.js"></script>', tags + '<script src="data.js"></script>', 1)
    if AUDIO:      # manifest + 新音频引擎紧跟 core.js（要在 touch.js / main.js 之前把 G.audio 换掉）
        core_tag = '<script src="engine/core.js"></script>'
        assert html.count(core_tag) == 1
        html = html.replace(core_tag, core_tag + '\n<script src="audio/manifest.js"></script>\n<script src="engine/audio_web.js"></script>', 1)
    wr(os.path.join(OUT, 'index.html'), html)
    print(f'图片内嵌: {len(packs)} 个 pack 文件')
else:
    img_bytes = sum(b for _, b in conv_res)
    shutil.copy2(os.path.join(G, 'index.html'), os.path.join(OUT, 'index.html'))
print(f'WebP {img_bytes/1e6:.2f} MB')

# ---------- 音频
ORIGINAL_MP3 = {'assets/audio/user/title_song.mp3'}
def enc(r):
    br = 48 if '/sfx/' in r else 40
    out = os.path.join(OUT, r); os.makedirs(os.path.dirname(out), exist_ok=True)
    if WEB and r in ORIGINAL_MP3:           # 标题曲用原文件（160kbps 立体声 48kHz），不重新压缩
        shutil.copy2(os.path.join(G, r), out); return os.path.getsize(out)
    if WEB and os.path.exists(os.path.join(DC, r)):
        shutil.copy2(os.path.join(DC, r), out); return os.path.getsize(out)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', os.path.join(G, r), '-vn', '-ac', '1', '-ar', '32000', '-codec:a', 'libmp3lame', '-b:a', f'{br}k', out], check=True)
    return os.path.getsize(out)
with ThreadPoolExecutor(8) as ex: aud_bytes = sum(ex.map(enc, sorted(mp3_refs)))
print(f'音频 {aud_bytes/1e6:.2f} MB')

# ---------- 音频打包（--audio）：转成单声道 32kHz mp3 → base64 → audio/*.js（音效约 700KB 一包，每首音乐一包）+ audio/manifest.js（路径 → 包）
if AUDIO:
    def _arg(name, default):
        for a in sys.argv:
            if a.startswith(name + '='): return int(a.split('=', 1)[1])
        return default
    MUSIC_KBPS, SFX_KBPS, TITLE_KBPS = _arg('--music-kbps', 48), _arg('--sfx-kbps', 48), _arg('--title-kbps', 40)   # 官方 Skill 1.7.0 性能预算：单条 Base64 解码后 > 1 MiB 视为“大 Base64”；标题曲 187 秒，48kbps = 1.07 MiB 超了，40kbps = 0.89 MiB
    ACACHE = os.path.join(HERE, '_tmp', 'audio_cache')
    def enc_audio(r):
        kb = SFX_KBPS if '/sfx/' in r else TITLE_KBPS if r.endswith('title_song.mp3') else MUSIC_KBPS
        src, cp = os.path.join(G, r), os.path.join(ACACHE, f'{kb}k', r)
        if not (os.path.exists(cp) and os.path.getmtime(cp) > os.path.getmtime(src)):
            os.makedirs(os.path.dirname(cp), exist_ok=True)
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', src, '-vn', '-ac', '1', '-ar', '32000', '-codec:a', 'libmp3lame', '-b:a', f'{kb}k', cp], check=True)
        return r, open(cp, 'rb').read()
    with ThreadPoolExecutor(8) as ex: enc_res = dict(ex.map(enc_audio, audio_refs))
    manifest = {}
    def write_pack(file, items):
        wr(os.path.join(OUT, file), 'window.APACK=window.APACK||{};Object.assign(window.APACK,' +
           json.dumps({k: base64.b64encode(v).decode('ascii') for k, v in items.items()}, separators=(',', ':')) + ');\n')
        for k in items: manifest[k] = file
    cur, n, i = {}, 0, 0
    for r in sorted(k for k in enc_res if '/sfx/' in k):
        cur[r] = enc_res[r]; n += len(enc_res[r])
        if n > 700_000: write_pack(f'audio/s{i:02d}.js', cur); cur, n, i = {}, 0, i + 1
    if cur: write_pack(f'audio/s{i:02d}.js', cur)
    for r in sorted(k for k in enc_res if '/sfx/' not in k):
        write_pack('audio/m_' + os.path.splitext(os.path.basename(r))[0] + '.js', {r: enc_res[r]})
    wr(os.path.join(OUT, 'audio/manifest.js'), ('' if '--release' in sys.argv else 'window.AUDIO_DEBUG=1;\n') + 'window.AUDIO_MANIFEST=' + json.dumps(manifest, separators=(',', ':')) + ';\n')
    # 所有音频包都要写成 index.html 里的静态 <script>：小红书容器里 load 之后运行时 createElement('script') 插入的脚本会加载失败（jojo 被驳回的真正原因）
    ih = rd(os.path.join(OUT, 'index.html')); mt = '<script src="audio/manifest.js"></script>'
    assert ih.count(mt) == 1
    wr(os.path.join(OUT, 'index.html'), ih.replace(mt, mt + ''.join(f'\n<script src="{f}"></script>' for f in sorted(set(manifest.values()))), 1))
    shutil.copy2(os.path.join(HERE, 'web_extras', 'audio_web.js'), os.path.join(OUT, 'engine', 'audio_web.js'))
    print(f'音频打包: {len(enc_res)} 个 mp3（音乐 {MUSIC_KBPS}kbps / 音效 {SFX_KBPS}kbps，单声道 32kHz）= {sum(map(len, enc_res.values()))/1e6:.2f} MB → {len(set(manifest.values()))} 个 js 包')

# ---------- 视频（只留 mp4；无声版没有）
for v in data2.get('video', {}).values():
    p = v['src']; os.makedirs(os.path.dirname(os.path.join(OUT, p)), exist_ok=True)
    shutil.copy2(os.path.join(DC, p), os.path.join(OUT, p))

# ---------- 竖屏容器：整体旋转 90° 显示（小红书小工具永远竖屏）
sys.path.insert(0, HERE)
import rotate_patch
rotate_patch.apply(OUT, web=WEB)
print('已应用竖屏旋转补丁')

# ---------- 公网版收尾：入口页放根目录并加 <base href=版本目录/>（所有相对路径照旧，资源全在 v<时间戳>/ 下，可长期缓存）
if WEB:
    html = rd(os.path.join(OUT, 'index.html'))
    assert html.count('<meta charset="utf-8">') == 1
    html = html.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<base href="' + VER + '/">', 1)
    wr(os.path.join(WEB_ROOT, 'index.html'), html); os.remove(os.path.join(OUT, 'index.html'))
    from collections import Counter
    allf = [os.path.join(dp, f) for dp, _, fs in os.walk(WEB_ROOT) for f in fs]
    sz = Counter(); cnt = Counter()
    for f in allf: e = os.path.splitext(f)[1]; sz[e] += os.path.getsize(f); cnt[e] += 1
    print(f'公网版 {VER}: {len(allf)} 个文件, {sum(sz.values())/1e6:.2f} MB; ' + ', '.join(f'{e} {cnt[e]}个 {sz[e]/1e6:.2f}MB' for e in sorted(sz)))
    sys.exit(0)

# ---------- 容器闸门：小红书容器里 load 之后运行时插入的 <script src> 会加载失败（jojo 的 loadScript 失败）。成品里任何 js 出现 createElement('script') 都不出包
_dyn = []
for dp, _, fs in os.walk(OUT):
    for f in fs:
        if f.endswith('.js') and re.search(r'createElement\(\s*[\'"]script[\'"]\s*\)', open(os.path.join(dp, f), encoding='utf-8', errors='ignore').read(3_000_000)):
            _dyn.append(os.path.relpath(os.path.join(dp, f), OUT))
if _dyn: sys.exit('!! 这些文件里有运行时插入 <script> 的写法，在小红书容器里会失败：' + ', '.join(_dyn))

# ---------- 兼容闸门：Chrome 61 / ES2017 解析不了的语法 = 老安卓上整个脚本报错、游戏起不来 → 直接不出包
chk = subprocess.run(['node', os.path.join(HERE, 'es2017_check.js'), OUT], capture_output=True, text=True, encoding='utf-8')
print(chk.stdout.strip().splitlines()[-1] if chk.stdout.strip() else chk.stderr.strip())
if chk.returncode != 0:
    print(chk.stdout, chk.stderr); sys.exit('!! es2017_check 发现 Chrome 61 解析不了的语法，已停止打包（见上面 [语法] 行）')

# ---------- 打 zip：index.html 在根目录，已压缩过的格式用 stored
STORED = ('.webp', '.mp3', '.mp4')
LIMIT_FILES = 200
if os.path.exists(ZIP): os.remove(ZIP)
files = []
for dp, _, fs in os.walk(OUT):
    for f in fs: files.append(os.path.relpath(os.path.join(dp, f), OUT).replace('\\', '/'))
files.sort(key=lambda x: (x != 'index.html', x))
with zipfile.ZipFile(ZIP, 'w') as z:
    for rel in files:
        z.write(os.path.join(OUT, rel), rel, compress_type=zipfile.ZIP_STORED if rel.lower().endswith(STORED) else zipfile.ZIP_DEFLATED, compresslevel=None if rel.lower().endswith(STORED) else 9)
zs = os.path.getsize(ZIP)
from collections import Counter
print(f'文件数 {len(files)} / 上限 {LIMIT_FILES} → ' + ('OK' if len(files) <= LIMIT_FILES else '超了'))
print('文件类型:', dict(Counter(os.path.splitext(f)[1] for f in files)), f'共 {len(files)} 个')
print(f'zip: {zs} 字节 = {zs/1e6:.2f} MB ({zs/1048576:.2f} MiB)，上限 10MB → ' + ('OK' if zs < 10_000_000 else '超了'))
