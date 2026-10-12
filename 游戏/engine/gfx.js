// 画图：宋体点阵字、角色图集、视差背景、特效粒子、UI 小部件
'use strict';
(function () {
  const G = window.G;

  // ---------------------------------------------------------------- 点阵字（原片字幕同款：宋体 12 / 16 px 位图）
  class Font {
    constructor(size) {
      const m = G.D.font[String(size)];
      this.size = size;
      this.img = G.image(m.image);
      this.lh = m.lh;
      this.glyphs = m.glyphs;
      this.cache = {};
      this.missing = new Set();
    }
    tinted(color) {
      let c = this.cache[color];
      if (!c && G.ready(this.img)) {
        c = document.createElement('canvas');
        c.width = this.img.width;
        c.height = this.img.height;
        const x = c.getContext('2d');
        x.drawImage(this.img, 0, 0);
        x.globalCompositeOperation = 'source-in';
        x.fillStyle = color;
        x.fillRect(0, 0, c.width, c.height);
        this.cache[color] = c;
      }
      return c;
    }
    adv(ch) {
      const gl = this.glyphs[ch];
      if (gl) return gl[2];
      return ch.charCodeAt(0) < 128 ? this.size / 2 : this.size;
    }
    width(str) { let w = 0; for (const ch of str) w += this.adv(ch); return w; }
    raw(g, str, x, y, color) {
      const atlas = this.tinted(color);
      if (!atlas) return;
      let cx = Math.round(x);
      const cy = Math.round(y);
      for (const ch of str) {
        const gl = this.glyphs[ch];
        if (gl) g.drawImage(atlas, gl[0], gl[1], gl[2], this.lh, cx, cy, gl[2], this.lh);
        else if (ch !== ' ') {
          if (!this.missing.has(ch)) { this.missing.add(ch); console.warn('字库里没有：', ch, '（重跑 tools/build_assets.py font data）'); }
          g.fillStyle = color;
          g.font = `${this.size}px SimSun, serif`;
          g.textBaseline = 'top';
          g.fillText(ch, cx, cy);
        }
        cx += this.adv(ch);
      }
    }
    draw(g, str, x, y, color = '#fff', o = {}) {
      str = String(str);
      if (o.align === 'center') x -= this.width(str) / 2;
      else if (o.align === 'right') x -= this.width(str);
      x = Math.round(x);
      if (o.shadow) this.raw(g, str, x + 1, y + 1, o.shadow);
      if (o.outline) {
        for (const [dx, dy] of [[-1, 0], [1, 0], [0, -1], [0, 1], [-1, -1], [1, -1], [-1, 1], [1, 1]]) this.raw(g, str, x + dx, y + dy, o.outline);
      }
      this.raw(g, str, x, y, color);
    }
    wrap(str, maxW) {
      const lines = [];
      for (const para of String(str).split('\n')) {
        let line = '';
        let w = 0;
        for (const ch of para) {
          const a = this.adv(ch);
          if (w + a > maxW && line) {
            if ('，。、！？…」』）～—'.includes(ch)) { line += ch; w += a; continue; }   // 行首不放标点
            lines.push(line);
            line = '';
            w = 0;
          }
          line += ch;
          w += a;
        }
        lines.push(line);
      }
      return lines;
    }
  }
  G.Font = Font;
  G.initFonts = () => { G.f12 = new Font(12); G.f16 = new Font(16); };

  // ---------------------------------------------------------------- 角色图集
  class Atlas {
    constructor(cid) {
      const m = G.D.chars[cid];
      if (!m) throw new Error('没有这个角色图集：' + cid);
      this.id = cid;
      this.m = m;
      this.img = G.image(m.image);
      this.cw = m.cell[0];
      this.ch = m.cell[1];
      this.px = m.pivot[0];
      this.py = m.pivot[1];
      this.white = null;
      this.tints = {};
    }
    has(name) { return !!(this.m.animations[name] || (this.m.aliases && this.m.aliases[name])); }
    anim(name) {
      const A = this.m.animations;
      if (A[name]) return A[name];
      const al = this.m.aliases && this.m.aliases[name];
      if (al && A[al]) return A[al];
      return A.idle || Object.values(A)[0];
    }
    whiteImg() {
      if (!this.white && G.ready(this.img)) {
        const c = document.createElement('canvas');
        c.width = this.img.width;
        c.height = this.img.height;
        const x = c.getContext('2d');
        x.drawImage(this.img, 0, 0);
        x.globalCompositeOperation = 'source-in';
        x.fillStyle = '#fff';
        x.fillRect(0, 0, c.width, c.height);
        this.white = c;
      }
      return this.white;
    }
    // 单色剪影（染色用：石化的灰、吃了煎蛋的紫、黄昏的橘）
    tintImg(color) {
      let c = this.tints[color];
      if (!c && G.ready(this.img)) {
        c = document.createElement('canvas');
        c.width = this.img.width;
        c.height = this.img.height;
        const x = c.getContext('2d');
        x.drawImage(this.img, 0, 0);
        x.globalCompositeOperation = 'source-in';
        x.fillStyle = color;
        x.fillRect(0, 0, c.width, c.height);
        this.tints[color] = c;
      }
      return c;
    }
    // (x, y) = 脚点在画面上的位置；o.tint = { color, k }：往这个颜色染 k（原片 draw_char 的 flash_color）
    draw(g, animName, frame, x, y, o = {}) {
      const a = this.anim(animName);
      if (!a || !G.ready(this.img)) return;
      const f = G.clamp(frame | 0, 0, a.frames - 1);
      const sx = f * this.cw;
      const sy = a.row * this.ch;
      const sc = o.scale || 1;
      g.save();
      g.translate(Math.round(x), Math.round(y));
      if (o.rot) g.rotate(o.rot);
      g.scale(o.flip ? -sc : sc, sc);
      if (o.alpha != null) g.globalAlpha = o.alpha;
      g.drawImage(this.img, sx, sy, this.cw, this.ch, -this.px, -this.py, this.cw, this.ch);
      if (o.tint && o.tint.k > 0) {
        const w = this.tintImg(o.tint.color);
        if (w) {
          g.globalAlpha = (o.alpha == null ? 1 : o.alpha) * Math.min(1, o.tint.k);
          g.drawImage(w, sx, sy, this.cw, this.ch, -this.px, -this.py, this.cw, this.ch);
        }
      }
      if (o.flash > 0) {
        const w = this.whiteImg();
        if (w) {
          g.globalAlpha = (o.alpha == null ? 1 : o.alpha) * Math.min(1, o.flash);
          g.drawImage(w, sx, sy, this.cw, this.ch, -this.px, -this.py, this.cw, this.ch);
        }
      }
      g.restore();
    }
  }
  G._atlases = {};
  G.atlas = (cid) => G._atlases[cid] || (G._atlases[cid] = new Atlas(cid));
  // 对话头像：先找表情，再退到 normal / 默认对话头像；配色变体用本体的头像
  G.head = (cid, expr) => {
    let m = G.D.chars[cid];
    if ((!m || !Object.keys(m.heads || {}).length) && cid.includes('__')) m = G.D.chars[cid.split('__')[0]];
    if (!m) return null;
    const h = m.heads || {};
    const src = h[expr] || h['portrait_' + expr] || h.normal || h.portrait_default || Object.values(h)[0];
    return src ? G.image(src) : null;
  };

  // ---------------------------------------------------------------- 像素线（不抗锯齿）
  G.pxLine = (g, x0, y0, x1, y1, color) => {
    g.fillStyle = color;
    x0 = Math.round(x0); y0 = Math.round(y0); x1 = Math.round(x1); y1 = Math.round(y1);
    const dx = Math.abs(x1 - x0), sx = x0 < x1 ? 1 : -1, dy = -Math.abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
    let err = dx + dy;
    for (let i = 0; i < 2000; i++) {
      g.fillRect(x0, y0, 1, 1);
      if (x0 === x1 && y0 === y1) break;
      const e2 = 2 * err;
      if (e2 >= dy) { err += dy; x0 += sx; }
      if (e2 <= dx) { err += dx; y0 += sy; }
    }
  };

  // ---------------------------------------------------------------- 视差背景（照原工程 bg 模块的图层顺序和公式）
  class Background {
    constructor(spec) {
      this.spec = spec || {};
      this.layers = this.spec.layers || [];
      this.fg = this.spec.fg || [];
    }
    // st = 当前地图（Stage）：门开多少、墙上有没有洞、窗外的乌鸦……这些剧情状态在 st.door / st.state 里
    draw(g, camX, t, st) { for (const L of this.layers) this.layer(g, L, camX, t, st); }
    // 前景：电线杆（原作里镜头扫过的）默认半透明，免得挡住打架的人；樱花等前景按 L.alpha 画
    drawFg(g, camX, t, st) {
      for (const L of this.fg) { g.globalAlpha = L.alpha == null ? 0.5 : L.alpha; this.layer(g, L, camX, t, st); }
      g.globalAlpha = 1;
    }
    screenX(wx, camX, period) { let s = G.mod(wx - camX, period); if (s >= G.W + 40) s -= period; return Math.floor(s); }
    layer(g, L, camX, t, st) {
      if (L.key && !(st && st.state[L.key])) return;     // 带 key 的图层：剧情打开了才画（墙洞、光束、樱花）
      switch (L.type) {
        case 'static': g.drawImage(G.image(L.image), 0, 0); break;
        case 'clouds':
          for (const c of L.clouds) {
            const x = G.mod(c.x0 + t * c.vx - camX * c.k, L.span) - 100;
            g.drawImage(G.image(c.image), Math.floor(x), c.y);
          }
          break;
        case 'terminal': {
          const sx = Math.floor(G.mod((L.cx != null ? L.cx : 192) - camX * L.k + 258, 900) - 258);
          const x0 = sx - Math.floor(L.w / 2), y0 = 150 + (L.dy || 0) - L.h + 12;
          g.drawImage(G.image(L.image), x0, y0);
          const on = (t * 1.3) % 1 < 0.5;
          for (const [bx, by] of [[0, 0], [-50, 46], [50, 46], [-22, 100], [22, 100]]) {
            if (on === bx < 0) continue;
            g.fillStyle = 'rgb(255,70,60)'; g.fillRect(sx + bx, y0 + by, 1, 1);
            if (L.side_px) { g.fillStyle = 'rgb(150,40,50)'; g.fillRect(sx + bx - 1, y0 + by, 1, 1); g.fillRect(sx + bx + 1, y0 + by, 1, 1); }
          }
          break;
        }
        case 'wrap': {   // L.vx：自己按时间滚动（列车、警车：人站着不动，风景往后跑）；L.blend = 'lighter' 相加混合（夜里的灯光）
          const im = G.image(L.image);
          if (!G.ready(im)) break;
          if (L.blend) g.globalCompositeOperation = L.blend;
          const o = G.mod(Math.floor(camX * L.k + t * (L.vx || 0) * (st && st.state.speed != null ? st.state.speed : 1)), L.period);
          const h = L.h || im.height;
          const sh = Math.min(h, im.height);
          if (o + G.W <= im.width) g.drawImage(im, o, 0, G.W, sh, 0, L.y, G.W, sh);
          else {   // 图不够宽（周期 = 图宽）：分两段接上
            const w1 = im.width - o;
            g.drawImage(im, o, 0, w1, sh, 0, L.y, w1, sh);
            g.drawImage(im, 0, 0, G.W - w1, sh, w1, L.y, G.W - w1, sh);
          }
          if (L.blend) g.globalCompositeOperation = 'source-over';
          break;
        }
        case 'reflect': {   // 雨天路面：店面底部倒过来、一行行晃着画在路上（同原片 _wet_reflection）
          const im = G.image(L.image);
          if (!G.ready(im)) break;
          const o0 = G.mod(Math.floor(camX), L.period);
          for (let y = 0; y < L.n; y++) {
            const a = L.alpha * (1 - y / L.n);
            if (a <= 0.02) continue;
            const off = Math.round(Math.sin(t * 7 + y * 0.9) * (1 + y * 0.06));
            const sy = L.base - 1 - y;
            g.globalAlpha = a;
            const o = G.mod(o0 - off, L.period);
            if (o + G.W <= im.width) g.drawImage(im, o, sy, G.W, 1, 0, L.base + 4 + y, G.W, 1);
            else { const w1 = im.width - o; g.drawImage(im, o, sy, w1, 1, 0, L.base + 4 + y, w1, 1); g.drawImage(im, 0, sy, G.W - w1, 1, w1, L.base + 4 + y, G.W - w1, 1); }
          }
          g.globalAlpha = 1;
          break;
        }
        case 'rows': {
          const im = G.image(L.image);
          if (!G.ready(im)) break;
          const v = t * (L.vx || 0) * (st && st.state.speed != null ? st.state.speed : 1);
          for (const [r0, r1] of L.rows) {
            const f = 1 + (0.55 * ((r0 + r1) / 2)) / Math.max(1, L.h);
            const o = G.mod(Math.floor((camX + v) * f), L.period);
            g.drawImage(im, o, r0, G.W, r1 - r0, 0, L.y + r0, G.W, r1 - r0);
          }
          break;
        }
        case 'rain': {   // 下雨：斜线雨丝 + 地面溅起的水花（原片 rain_layer / ground_splashes 的感觉）
          const n = L.n || 70, slant = L.slant == null ? 0.3 : L.slant, len = L.len || 7, spd = L.speed || 420;
          if (!L._p) { const rnd = G.prng(L.seed || 9); L._p = Array.from({ length: n }, () => [rnd() * (G.W + 80), rnd() * G.H, 0.7 + rnd() * 0.6]); }
          g.fillStyle = L.color || 'rgba(190,205,235,0.55)';
          for (const [x0, y0, f] of L._p) {
            const y = G.mod(y0 + t * spd * f, G.H + 20) - 10;
            const x = G.mod(x0 - t * spd * f * slant - camX * 0.2, G.W + 80) - 40;
            for (let i = 0; i < len; i++) g.fillRect(Math.round(x - i * slant), Math.round(y - i), 1, 1);
          }
          if (L.ground) {   // 地上的小水花
            const rnd = G.prng(Math.floor(t * 12) + 3);
            g.fillStyle = L.splash || 'rgba(200,215,240,0.6)';
            for (let i = 0; i < (L.splashes || 14); i++) {
              const sx = Math.floor(rnd() * G.W), sy = Math.floor(L.ground[0] + rnd() * (L.ground[1] - L.ground[0]));
              g.fillRect(sx - 1, sy, 1, 1); g.fillRect(sx + 1, sy, 1, 1); g.fillRect(sx, sy - 1, 1, 1);
            }
          }
          break;
        }
        case 'tint': {   // 整屏罩一层颜色（夜里、黄昏、阳光）：st.state[key] 可以改透明度
          const a = st && L.key ? st.state[L.key] : L.alpha;
          g.globalAlpha = typeof a === 'number' ? a : L.alpha == null ? 0.3 : L.alpha;
          g.fillStyle = L.color; g.fillRect(0, 0, G.W, G.H);
          g.globalAlpha = 1;
          break;
        }
        case 'lanterns':
          for (const it of L.items) {
            const s = this.screenX(it.x, camX, L.period);
            if (s <= -20 || s >= G.W + 20) continue;
            const ang = Math.sin(t * 2 * Math.PI * 0.32 + s * 0.071);
            const dx = Math.round(ang * (it.size === 1 ? 1.4 : 2.2));
            const len = L.string * it.size;
            G.pxLine(g, s, it.y, s + dx, it.y + len, G.rgb(L.color));
            if (it.glow) {   // 夜里点亮的灯笼：光晕相加混合
              g.globalCompositeOperation = 'lighter';
              g.drawImage(G.image(it.glow.image), s + dx - it.glow.rad, it.y + len + Math.floor((it.h || 11) / 2) - it.glow.rad);
              g.globalCompositeOperation = 'source-over';
            }
            g.drawImage(G.image(it.image), s + dx - Math.floor(it.w / 2), it.y + len);
          }
          break;
        case 'flags':
          L.items.forEach((it, i) => {
            const s = this.screenX(it.x, camX, L.period);
            if (s <= -20 || s >= G.W + 20) return;
            const pc = G.rgb(L.pole);
            G.pxLine(g, s, it.y - 3, s, L.base + 1, pc);
            G.pxLine(g, s, it.y - 2, s + 13, it.y - 2, pc);
            g.drawImage(G.image(it.frames[Math.floor(t * 5 + i) % 4]), s + 1, it.y);
          });
          break;
        case 'poles': {
          const col = G.rgb(L.col), hi = G.rgb(L.hi);
          for (let k = -1; k < 3; k++) {
            const x = G.mod(Math.trunc(k * L.period + 300 - camX * L.k), L.period * 2) - 60;
            if (x > -20 && x < G.W + 20) {
              g.fillStyle = col; g.fillRect(x - 5, 0, 11, G.H);
              g.fillStyle = hi; g.fillRect(x - 5, 0, 1, G.H);
              g.fillStyle = col; g.fillRect(x - 16, 10, 33, 4); g.fillRect(x - 14, 26, 29, 3);
            }
          }
          break;
        }
        case 'edo_ships':  // 江户天上的飞船（原片 E._ambient_ships）：固定镜头的地图用
          for (const it of L.items) {
            const x = G.mod(it.x0 + t * it.vx - camX * it.k, L.span) - 120, y = it.y + 2 * Math.sin(0.9 * t + it.i);
            g.drawImage(G.image(it.image), Math.round(x - it.w / 2), Math.round(y - it.h / 2));
          }
          break;
        case 'birds': {    // 远处的小鸟（原片 A.birds）：两帧的「V」
          const rnd = G.prng((L.seed || 1) * 7919);
          g.fillStyle = 'rgb(60,60,80)';
          for (let i = 0; i < L.n; i++) {
            const u0 = rnd(), u1 = 0.8 + rnd() * 0.4, u2 = rnd() * 20 - 10;
            const x = Math.round(G.mod(u0 * (G.W + 60) + t * L.speed * u1, G.W + 60) - 30), y = Math.round(L.y + u2 + 2 * Math.sin(2 * t + i));
            const d = Math.floor(t * 6 + i) % 2 ? -1 : 1;
            g.fillRect(x - 2, y + d, 1, 1); g.fillRect(x - 1, y, 1, 1); g.fillRect(x, y, 1, 1); g.fillRect(x + 1, y, 1, 1); g.fillRect(x + 2, y + d, 1, 1);
          }
          break;
        }
        case 'steam': {    // 冒热气（原片 A.steam）
          const rnd = G.prng((L.seed || 1) * 131);
          g.fillStyle = 'rgba(236,236,240,0.85)';
          for (let i = 0; i < (L.n || 6); i++) {
            const u = rnd(), v = rnd() * 6 - 3, ph = G.mod(0.9 * t + u, 1);
            if (ph >= 0.85) continue;
            g.beginPath(); g.arc(L.x + v + 2 * Math.sin(3 * t + i) - camX, L.y - ph * (L.h || 6) * 2.5, 1 + 2.5 * ph, 0, Math.PI * 2); g.fill();
          }
          break;
        }
        case 'dust': {     // 阳光里飘的灰尘（原片 A.sunbeams 的光点）
          g.fillStyle = 'rgb(255,250,226)';
          const rnd = G.prng(17), f = Math.floor(t * 6);
          for (const bx of L.beams) {
            for (let k = 0; k < 7; k++) {
              const u = rnd(), v = -8 + rnd() * 24, sp = 0.5 + rnd();
              if ((f + k) % 4 === 0) continue;
              const ph = G.mod(0.05 * t * sp + u, 1), y = 30 + 120 * ph, x = bx + 18 + 0.47 * (y - 20) + v + 3 * Math.sin(t + k);
              g.fillRect(Math.round(x - camX), Math.round(y), 1, 1);
            }
          }
          break;
        }
        case 'ships':
          L.items.forEach((s, i) => {
            const x = G.mod(i * 150 + 30 - t * (1.5 + i * 0.7) - camX * 0.06, G.W + 240) - 120;
            g.drawImage(G.image(s.image), Math.floor(x), 16 + i * 12 + Math.round(Math.sin(t * 0.7 + i) * 1.5));
          });
          break;
        case 'smoke': {
          const n = L.frames.length;
          const f = Math.floor(t * L.fps);
          for (const [wx, base] of [[150, 150], [560, 148], [980, 150], [1380, 149]]) {
            const sx = Math.floor(wx - camX * 0.3);
            if (sx < -80 || sx > G.W + 40) continue;
            g.drawImage(G.image(L.frames[G.mod(f + wx, n)]), sx - 20, base - 136);
          }
          break;
        }
        // ---- 下面是第二章加的（固定镜头的房间；x 都是世界坐标，单屏地图里就是屏幕坐标）
        case 'image': {
          if (L.blend) g.globalCompositeOperation = L.blend;
          if (L.flicker) g.globalAlpha = Math.max(0, Math.min(1, L.flicker[0] + L.flicker[1] * Math.sin(L.flicker[2] * t)));
          else if (L.alpha != null && L.type === 'image' && L.blend) g.globalAlpha = L.alpha;
          g.drawImage(G.image(L.image), L.screen ? L.x : Math.round(L.x - camX * (L.k == null ? 1 : L.k) + t * (L.vx || 0)), L.y);
          if (L.blend) g.globalCompositeOperation = 'source-over';
          g.globalAlpha = 1;
          break;
        }
        case 'lanternString': {   // 一串灯笼（每 period 像素重复）：摆动 + 夜里相加的光晕（同原片 lantern_string）
          for (const it of L.items) {
            const s0 = G.mod(it.x - camX, L.period);
            for (const s of [s0 - L.period, s0, s0 + L.period]) {
              if (s <= -10 || s >= G.W + 10) continue;
              const xi = Math.trunc(s), yi = Math.trunc(it.y);
              const dx = Math.round(Math.sin(t * 2 * Math.PI * L.freq + xi * 0.071) * 0.8 * L.amp);
              G.pxLine(g, xi, yi, xi + dx, yi + L.string, G.rgb(L.color));
              if (L.glow && it.glow) {
                const lv = Math.round(Math.min(1, 0.9 + 0.1 * Math.sin(13 * t + xi)) * 4) / 4;
                g.save(); g.globalCompositeOperation = 'lighter'; g.globalAlpha = lv;
                g.drawImage(G.image(it.glow), xi + dx - 14, yi - 3); g.restore();
              }
              g.drawImage(G.image(it.image), xi + dx - 4, yi + L.string);
            }
          }
          break;
        }
        case 'embers': {   // 吉原的火星：往上飘、左右晃、一闪一闪
          const [x0, y0, x1, y1] = L.area || [0, 0, G.W, G.H], w = x1 - x0, h = y1 - y0, f = Math.floor(t * 10);
          L.items.forEach(([uy, v, ux, ph], i) => {
            if ((f + i) % 5 === 0) return;
            const y = y1 - G.mod(uy * h + t * L.rise * v, h), x = x0 + G.mod(ux * w + 8 * Math.sin(2 * Math.PI * (0.5 * t + ph)), w);
            g.fillStyle = G.rgb(L.colors[i % L.colors.length]); g.fillRect(Math.round(x), Math.round(y), 1, 1);
          });
          break;
        }
        case 'glow': {     // 相加的光晕（纸灯笼）：flicker = 原片 0.85 + 0.15·sin13t·sin7.3t 的闪动
          const a = (L.alpha == null ? 1 : L.alpha) * (L.flicker ? 0.85 + 0.15 * Math.sin(t * 13) * Math.sin(t * 7.3) : 1);
          g.save(); g.globalCompositeOperation = 'lighter'; g.globalAlpha = Math.max(0, Math.min(1, a));
          g.drawImage(G.image(L.image), Math.round(L.x - camX * (L.k == null ? 1 : L.k)), L.y);
          g.restore();
          break;
        }
        case 'shaftmotes': {   // 月光光柱里的灰尘（伊东的房间）
          g.fillStyle = 'rgb(200,210,250)';
          const f = Math.floor(t * 6 + 1e-6);
          L.items.forEach(([sp, ph0, dx], i) => {
            if ((i + f) % 4 === 0) return;
            const ph = G.mod(t * sp + ph0, 1);
            g.fillRect(Math.round(112 + ph * 60 + dx - camX), Math.round(40 + ph * 120 + Math.sin(t + i) * 3), 1, 1);
          });
          break;
        }
        case 'mlines': {   // 速度线（列车、警车飞驰时横着划过去的线）
          g.fillStyle = G.rgb(L.color);
          for (let i = 0; i < L.count; i++) {
            const rnd = G.prng((L.seed || 1) * 131 + i * 7);
            const y = Math.round(L.y0 + rnd() * (L.y1 - L.y0)), len = Math.round(L.len[0] + rnd() * (L.len[1] - L.len[0])), x0 = rnd() * 2000;
            const x = G.mod(x0 - t * L.speed * (0.7 + rnd() * 0.6), G.W + len + 60) - len - 20;
            g.fillRect(Math.round(x), y, len, 1);
          }
          break;
        }
        case 'windmotes': {    // 风里飘的光点（夕阳的原野）
          const [x0, y0, x1, y1] = L.area;
          g.fillStyle = G.rgb(L.color);
          L.items.forEach(([spf, ux, uy], i) => {
            const x = Math.round(x1 - G.mod(ux + t * L.speed * spf, x1 - x0 + 20) + 10), y = Math.round(y0 + G.mod(uy + Math.sin(t * 2 + i) * 6, y1 - y0));
            g.fillRect(x, y, i % 3 === 0 ? 3 : 1, 1);
          });
          break;
        }
        case 'roof': {     // 可以走的屋脊：横向重复 + 下面补一块颜色
          this.layer(g, Object.assign({}, L, { type: 'wrap' }), camX, t, st);
          g.fillStyle = G.rgb(L.below); g.fillRect(0, L.y + L.h, G.W, G.H - L.y - L.h);
          break;
        }
        case 'fleet': {    // 天人舰队：暗色罩子 + 远处的船 + 母舰（+ 光柱）+ 近一点的船；st.state.armada = 舰队浓度 0..1
          const FL = this.spec.fleet, d = st && st.state.armada != null ? st.state.armada : 1;
          if (!FL || d <= 0) break;
          const lvl = Math.round(d * 4) / 4;
          if (lvl > 0) g.drawImage(G.image(FL.overlays[lvl === 1 ? '1.0' : String(lvl)]), 0, 0);
          const ship = (s, x, y) => { const im = G.image(s.image); if (G.ready(im)) g.drawImage(im, Math.round(x - s.w / 2), Math.round(y - s.h / 2)); };
          FL.far.slice(0, Math.floor(26 * d)).forEach((s, i) => ship(s, G.mod(s.x0 - t * s.spx - camX * 0.08, 544) - 80, s.y + 1.5 * Math.sin(0.5 * t + i)));
          const m = FL.mothership, mx = 192 - 0.05 * camX + 6 * Math.sin(0.15 * t), my = 18 + 2 * Math.sin(0.4 * t) - 30 * (1 - d);
          ship(m, mx, my);
          if (d > 0.5) { g.fillStyle = `rgba(255,90,130,${(0.08 + 0.06 * (0.5 + 0.5 * Math.sin(1.3 * t))).toFixed(3)})`; g.fillRect(Math.floor(mx) - 6, Math.floor(my) + 30, 12, 216); }
          FL.mid.slice(0, Math.floor(7 * d)).forEach((s, i) => ship(s, G.mod(s.x0 - t * s.spx - camX * 0.2, 644) - 130, s.y));
          break;
        }
        case 'gulls': {    // 海鸥（两帧的「V」，从右往左飞）
          const [x0, y0, x1, y1] = L.area, span = x1 - x0 + 40;
          g.fillStyle = G.rgb(L.color);
          L.items.forEach(([sp, xo, yy, ph], i) => {
            const x = Math.round(G.mod(xo + t * sp, span) + x0 - 20), y = Math.round(yy + Math.sin(1.3 * t + i) * 3);
            const up = Math.floor((t + ph) * 6) % 2 === 0;
            const pts = up ? [[-2, -1], [-1, 0], [0, 1], [1, 0], [2, -1]] : [[-2, 1], [-1, 0], [0, 1], [1, 0], [2, 1]];
            for (const [dx, dy] of pts) g.fillRect(x + dx, y + dy, 1, 1);
          });
          break;
        }
        case 'stars': {    // 会眨眼的星星（同原片 C.sky 的星表）：[x, y, 速度, 相位, 大星, 颜色]
          const [sx, sy] = L.skip || [-99, -99];
          for (const [x, y, sp, ph, big, c] of L.items) {
            if (Math.abs(x - sx) < 14 && Math.abs(y - sy) < 14) continue;
            const tw = Math.sin(t * sp + ph);
            if (tw < -0.55) continue;
            const k = L.dim * (tw < 0.2 ? 0.65 : 1);
            g.fillStyle = `rgb(${Math.floor(c[0] * k)},${Math.floor(c[1] * k)},${Math.floor(c[2] * k)})`;
            g.fillRect(x, y, 1, 1);
            if (big && tw > 0.5) {
              const k2 = 0.5 * L.dim;
              g.fillStyle = `rgb(${Math.floor(c[0] * k2)},${Math.floor(c[1] * k2)},${Math.floor(c[2] * k2)})`;
              g.fillRect(x - 1, y, 1, 1); g.fillRect(x + 1, y, 1, 1); g.fillRect(x, y - 1, 1, 1); g.fillRect(x, y + 1, 1, 1);
            }
          }
          break;
        }
        case 'river': {    // 河面：底图 + 闪动的波纹 + 月亮的倒影（同原片 C.river）
          const y = L.y;
          g.drawImage(G.image(L.image), 0, y);
          for (const [dyy, ln, spd, ph, x0, bs, par] of L.dashes) {
            const x = Math.trunc(G.mod(x0 + t * spd - camX * par, G.W + 40) - 20);
            const bl = Math.sin(t * bs + ph);
            if (bl > 0.1) g.fillStyle = G.rgb(bl > 0.55 ? L.hi : L.mid);
            else if (bl < -0.6) g.fillStyle = G.rgb(L.lo);
            else continue;
            g.fillRect(x, y + dyy, ln + 1, 1);
          }
          if (L.reflect_x != null) {
            g.fillStyle = G.rgb(L.rc || L.refl);
            for (let k = 0; k < (L.h >> 1); k++) {
              const yy = y + 3 + k * 2;
              if (yy >= y + L.h) break;
              const half = 1 + Math.floor(k * 0.35) + Math.floor(Math.abs(Math.sin(t * 3 + k)) * 2);
              if (Math.sin(t * 4 + k * 1.7) > -0.4) { const xo = Math.trunc(Math.sin(t * 2 + k) * 1.5); g.fillRect(L.reflect_x - half + xo, yy, 2 * half + 1, 1); }
            }
          }
          break;
        }
        case 'frames': {   // 循环帧（吊灯、吊扇）；k = 视差，blend = 'lighter' 相加
          const f = G.mod(Math.floor(t * L.fps + 1e-6), L.frames.length);
          if (L.blend) g.globalCompositeOperation = L.blend;
          g.drawImage(G.image(L.frames[f]), Math.round(L.x - camX * (L.k == null ? 1 : L.k)), L.y);
          if (L.blend) g.globalCompositeOperation = 'source-over';
          break;
        }
        case 'clock': {    // 秒针（原片 draw_clock_hands：每秒跳一格）
          const a = Math.floor(t + 1e-6) * Math.PI / 30 - Math.PI / 2;
          const x = Math.round(L.x - camX);
          G.pxLine(g, x, L.y, x + Math.round(Math.cos(a) * L.len), L.y + Math.round(Math.sin(a) * L.len), G.rgb(L.color));
          g.fillStyle = G.rgb(L.ink); g.fillRect(x, L.y, 1, 1);
          break;
        }
        case 'walkers': {  // 窗外走过的路人（原片 _window_life），乌鸦也画在窗里
          const [x0, y0, x1, y1] = L.clip;
          const ox = Math.round(x0 - camX);
          g.save();
          g.beginPath(); g.rect(ox, y0, x1 - x0, y1 - y0); g.clip();
          const span = x1 - x0 + 60;
          L.items.forEach(([cid, dir, spd, off], i) => {
            let wx = G.mod(off + t * spd, span) - 30;
            if (dir < 0) wx = x1 - x0 - wx;
            const at = G.atlas(cid), a = at.anim('walk');
            at.draw(g, 'walk', Math.floor((t + i * 0.37) * a.fps + 1e-6) % a.frames, ox + wx, y0 + L.base_y + (i % 2) * 3, { flip: dir < 0 });
          });
          const c = st && st.state.crow;   // { image 或 frames + fps, x, y（脚底）, flip }
          if (c) {
            const im = G.image(c.frames ? c.frames[Math.floor(t * (c.fps || 8)) % c.frames.length] : c.image);
            if (G.ready(im)) {
              g.translate(Math.round(c.x - camX), Math.round(c.y));
              if (c.flip) g.scale(-1, 1);
              g.drawImage(im, -Math.floor(im.width / 2), -im.height);
            }
          }
          g.restore();
          break;
        }
        case 'door': {     // 厨房门：st.door 0 = 关，1 = 全开（全开时炉火和蒸汽会动）
          const d = st ? st.door : 0;
          const src = d >= 0.99 ? L.open[G.mod(Math.floor(t * L.fps + 1e-6), L.open.length)]
            : L.steps[Math.min(L.steps.length - 1, Math.round(d * (L.steps.length - 1)))];
          g.drawImage(G.image(src), Math.round(L.x - camX), L.y);
          break;
        }
        case 'hole': g.drawImage(G.image(L.image), Math.round(L.x - camX), L.y); break;
        case 'lantern': {  // 一盏灯笼：绳子 + 摆动 + 黄昏的光晕（相加混合，同原片 add_sprite）
          const dx = Math.round(Math.sin(t * 2 * Math.PI * L.freq + L.x * 0.071) * L.amp);
          const x = Math.round(L.x - camX);
          G.pxLine(g, x, L.y, x + dx, L.y + L.string, G.rgb(L.color));
          const px = x + dx - Math.floor(L.w / 2), py = L.y + L.string;
          if (L.glow) {
            g.globalCompositeOperation = 'lighter';
            g.drawImage(G.image(L.glow.image), px + Math.floor(L.w / 2) - L.glow.rad, py + Math.floor(L.h / 2) - L.glow.rad);
            g.globalCompositeOperation = 'source-over';
          }
          g.drawImage(G.image(L.image), px, py);
          break;
        }
        case 'tree': {     // 樱花树：树冠三帧摆动 + 飘落的花瓣（同原片 cherry_tree）
          const sw = Math.sin(t * 2 * Math.PI * L.freq + L.x * 0.05);
          const k = sw < -0.45 ? 0 : sw > 0.45 ? 2 : 1;
          const ox = Math.round(L.x - L.ax - camX), oy = L.y - L.ay;
          g.drawImage(G.image(L.frames[k]), ox, oy);
          L.petals.forEach(([per, off, cx, cy], i) => {
            const u = G.mod(t + off, per) / per;
            const px = Math.floor(ox + cx + u * 34 + Math.sin(u * 9 + i) * 4), py = Math.floor(oy + cy + u * (L.ay - cy));
            g.fillStyle = G.rgb(L.pc[i % 2]);
            if (Math.floor(t * 8 + i) % 2) g.fillRect(px, py, 2, 1); else g.fillRect(px, py, 1, 2);
          });
          break;
        }
        case 'motes': {    // 道场里的飘尘（同原片 _dojo_motes）
          g.fillStyle = G.rgb(L.color);
          const f = Math.floor(t * 6 + 1e-6);
          L.items.forEach(([x0, vx, y0, vy], i) => {
            if ((f + i) % 4 === 0) return;
            g.fillRect(Math.floor(G.mod(x0 + t * vx, G.W) - camX), Math.floor(G.mod(y0 - t * vy, 140) + 20), 1, 1);
          });
          break;
        }
        case 'rays': {     // 从一点放射出来的光束：st.state.rays = { x, y, amount }（新八下决心）；或者图层自带 x / y（屯所中庭，常亮）
          const R = L.x != null ? { x: L.x, y: L.y, amount: 1 } : st.state.rays;
          if (!R || !(R.amount > 0)) break;
          const n = L.n || 10, len = L.len || 420, rot = t * (L.speed != null ? L.speed : 0.22), cx = R.x - camX, cy = R.y;
          g.globalAlpha = L.alpha != null ? (Array.isArray(L.alpha) ? L.alpha[st && st.state.raysHi ? 1 : 0] : L.alpha) : Math.min(1, 0.2 * R.amount);
          g.fillStyle = G.rgb(L.color);
          g.beginPath();
          for (let i = 0; i < n; i++) {
            const a0 = rot + (i * 2 * Math.PI) / n, a1 = a0 + (Math.PI / n) * (L.width || 0.55);
            g.moveTo(cx, cy);
            g.lineTo(cx + Math.cos(a0) * len, cy + Math.sin(a0) * len);
            g.lineTo(cx + Math.cos(a1) * len, cy + Math.sin(a1) * len);
            g.closePath();
          }
          g.fill();
          g.globalAlpha = 1;
          break;
        }
        case 'sakura': {   // 满屏飘的樱花瓣（同原片 fx.sakura 的感觉）
          if (!L._p) {
            const rnd = G.prng(L.seed || 1);
            L._p = Array.from({ length: L.n }, () => ({
              x: rnd() * (G.W + 40), y: rnd() * G.H, v: L.fall * (0.6 + rnd() * 0.8), w: L.wind * (0.6 + rnd() * 0.8),
              ph: rnd() * 6.28, c: Math.floor(rnd() * 3),
            }));
          }
          const cols = ['#ffb7c5', '#ffd6e0', '#f08caa'];
          for (const p of L._p) {
            const x = Math.floor(G.mod(p.x + t * p.w + Math.sin(t * 1.3 + p.ph) * 6, G.W + 40) - 20);
            const y = Math.floor(G.mod(p.y + t * p.v, G.H + 10) - 5);
            g.fillStyle = cols[p.c];
            if (Math.floor(t * 6 + p.ph) % 2) g.fillRect(x, y, 2, 1); else g.fillRect(x, y, 1, 2);
          }
          break;
        }
        case 'kstreet': {  // 两年后的歌舞伎町（终章）：L.tod / L.dy / L.frame；st.state.tod / wet 可以改，st.state.mix = { tod, wet, k } 叠一层别的天气
          const SD = G.D.bg.ch14_street, S0 = st ? st.state : {};
          const tod = S0.tod || L.tod, wet = S0.wet != null ? S0.wet : null, dy = L.dy || 0;
          kstreet(g, SD, SD[tod], camX, t, dy, wet, L.frame);
          const mx = S0.mix;
          if (mx && mx.k > 0) {
            const B = kbuf();
            B.x.clearRect(0, 0, G.W, G.H);
            kstreet(B.x, SD, SD[mx.tod], camX, t, dy, mx.wet != null ? mx.wet : null, L.frame);
            g.globalAlpha = Math.min(1, mx.k); g.drawImage(B.c, 0, 0); g.globalAlpha = 1;
          }
          break;
        }
        case 'kstreet_rail': {   // 万事屋门口那个镜头：二楼的栏杆盖在阳台上的人前面
          const SD = G.D.bg.ch14_street, tod = (st && st.state.tod) || 'storm', F = SD.common.front;
          const rail = G.image(SD.common[`front_rail_${tod === 'storm' ? 'storm' : 'day'}`]);
          if (G.ready(rail)) g.drawImage(rail, F.rail_xy[0], F.rail_xy[1]);
          break;
        }
        default: break;
      }
    }
  }
  G.Background = Background;

  // ---------------------------------------------------------------- 终章的歌舞伎町（原片 kabukicho.street，照调研 s14.md 的 compose() 逐项翻过来）
  const keyOf = (v) => (Number.isInteger(v) ? v.toFixed(1) : String(v));      // Python 的 str(1.0) = '1.0'
  const shade = (c, k) => `rgb(${c.slice(0, 3).map((v) => Math.floor(G.clamp(v * k, 0, 255))).join(',')})`;
  let KBUF = null;
  function kbuf() {
    if (!KBUF) { const c = Object.assign(document.createElement('canvas'), { width: G.W, height: G.H }); KBUF = { c, x: c.getContext('2d') }; KBUF.x.imageSmoothingEnabled = false; }
    return KBUF;
  }
  function kship(g, D, file, kind, x, y, t, facing, haze) {
    const spr = G.image(file);
    if (!G.ready(spr)) return;
    const x0 = Math.round(x - spr.width / 2), y0 = Math.round(y - spr.height / 2);
    if (x0 > G.W || y0 > G.H || x0 + spr.width < 0 || y0 + spr.height < 0) return;
    g.drawImage(spr, x0, y0);
    const meta = D.ships[kind], wv = spr.width, fade = 1 - Math.round(haze * 100) / 100 * 0.6;
    const P = (px, py) => { const sx = px + 1; return [x0 + (facing < 0 ? wv - 1 - sx : sx), y0 + py + 1]; };
    for (const [lx, ly, c, ph] of meta.lights) {
      const v = Math.sin((t * 2.2 + ph) * 2 * Math.PI);
      if (v > -0.2) { const [px, py] = P(lx, ly); g.fillStyle = shade(c, (v > 0.5 ? 1 : 0.6) * fade); g.fillRect(px, py, 1, 1); }
    }
    for (const [ex, ey, eh] of meta.engines) {
      const [px, py] = P(ex, ey);
      if (kind === 'saucer') {
        const k = 0.5 + 0.5 * Math.sin(t * 5), rr = Math.trunc(eh * (0.8 + 0.3 * k));
        const gl = G.image(D.glow[`saucer|${rr + 3}|${keyOf(Math.round((0.5 + 0.5 * k) * 10) / 10)}`]);
        if (G.ready(gl)) { g.save(); g.globalCompositeOperation = 'lighter'; g.drawImage(gl, px - rr - 3, py - rr - 3); g.restore(); }
        continue;
      }
      const fl = 2 + Math.trunc(G.mod(t * 20 + ex, 3));
      g.fillStyle = shade([255, 150, 60], fade);
      if (facing > 0) { g.fillRect(px - fl, py - 1, fl, 2); g.fillStyle = shade([255, 236, 150], fade); g.fillRect(px - (fl >> 1), py, fl >> 1, 1); }
      else g.fillRect(px + 1, py - 1, fl, 2);
    }
  }
  // 雷：一个 4.2 秒的窗口里最多一道闪电（表是导出来的），返回 [亮度, 闪电的折线]
  G.stormFlash = (t) => {
    const L = G.D.bg.ch14_street.common.lightning, n = L.strikes.length, tt = G.mod(t, n * L.window), k = Math.floor(tt / L.window);
    let best = 0;
    for (const kk of [k - 1, k]) {
      const s = L.strikes[G.mod(kk, n)], dt = tt - (s.t0 - (kk < 0 ? L.window * n : 0));
      if (dt >= 0 && dt < 0.4) best = Math.max(best, L.seq[Math.min(5, Math.floor(dt * 15))]);
    }
    return [best, L.strikes[G.mod(k, n)].bolt];
  };
  function kstreet(g, SD, m, camX, t, dy, wet, frame) {
    const D = SD.common, V = m['dy' + dy], W = G.W, img = G.image;
    if (!G.ready(img(V.sky))) return;
    g.drawImage(img(V.sky), 0, 0);
    if (m.stars) {
      for (const [x, y, sp, ph, big, c] of m.stars.items) {
        const tw = Math.sin(t * sp + ph);
        if (tw < -0.55) continue;
        g.fillStyle = shade(c, m.stars.dim * (tw < 0.2 ? 0.65 : 1)); g.fillRect(x, y, 1, 1);
        if (big && tw > 0.5) { g.fillStyle = shade(c, 0.5 * m.stars.dim); g.fillRect(x - 1, y, 1, 1); g.fillRect(x + 1, y, 1, 1); g.fillRect(x, y - 1, 1, 1); g.fillRect(x, y + 1, 1, 1); }
      }
    }
    if (m.tod === 'storm') {        // 天空的闪光 + 闪电（紧跟在天空后面画）
      const [f, bolt] = G.stormFlash(t);
      if (f > 0) {
        g.globalAlpha = f * 0.8; g.drawImage(img(V.flash), 0, 0); g.globalAlpha = 1;
        if (f > 0.6) {
          g.lineJoin = 'miter';
          for (const [w, c] of [[3, 'rgb(170,180,255)'], [1, 'rgb(250,250,255)']]) {
            g.strokeStyle = c; g.lineWidth = w; g.beginPath();
            bolt.forEach(([bx, by], i) => (i ? g.lineTo(bx + 0.5, by + 0.5) : g.moveTo(bx + 0.5, by + 0.5)));
            g.stroke();
          }
        }
      }
    }
    const cl = V.clouds;
    for (const c of cl.items) g.drawImage(img(c.image), Math.trunc(G.mod(c.x0 + t * c.vx - camX * 0.5 * c.k0, cl.span) - 100), c.y);
    // 远处的航站楼（视差 0.08）+ 闪烁的灯 + 两架来回的穿梭机
    const T = m.terminal, ts = img(T.image);
    if (G.ready(ts)) {
      const sx = Math.trunc(G.mod(W / 2 - camX * T.k + 258, 900) - 258), x0 = sx - Math.floor(ts.width / 2), y0 = 150 + dy - ts.height + 12;
      g.drawImage(ts, x0, y0);
      const on = G.mod(t * 1.3, 1) < 0.5;
      for (const [bx, by] of [[0, 0], [-50, 46], [50, 46], [-22, 100], [22, 100]]) {
        if (on !== (bx < 0)) {
          g.fillStyle = 'rgb(255,70,60)'; g.fillRect(sx + bx, y0 + by, 1, 1);
          if (T.side_pixels) { g.fillStyle = 'rgb(150,40,50)'; g.fillRect(sx + bx - 1, y0 + by, 1, 1); g.fillRect(sx + bx + 1, y0 + by, 1, 1); }
        }
      }
      for (let k = 0; k < 2; k++) {
        const u = G.mod(t + k * 4.5, 9) / 9, side = k === 0 ? 1 : -1;
        kship(g, D, T.shuttle[String(-side)], 'shuttle', sx + side * (54 + Math.abs(u - 0.5) * 2 * 150), y0 + (44 - Math.abs(u - 0.5) * 2 * 30 + k * 6), t, -side, 0.35);
      }
    }
    const wrap = (L, y) => { const im = img(L.image); if (G.ready(im)) g.drawImage(im, G.mod(Math.floor(camX * L.k), L.period), 0, W, im.height, 0, y, W, im.height); };
    wrap(m.back, dy);
    kship(g, D, m.saucer, 'saucer', G.mod(t * 7 - camX * 0.3, W + 120) - 60, 16 + dy + Math.sin(t) * 2, t, 1, 0.45);
    for (let k = 0; k < 3; k++) {       // 悬浮车（14×8，程序画的）
      const x = Math.floor(G.mod(k * 181 + t * (9 + k * 4) * (k % 2 === 0 ? 1 : -1) - camX * 0.4, W + 60) - 30), y = 30 + k * 7 + dy;
      g.fillStyle = G.rgb(m.car.body); g.fillRect(x, y + 2, 14, 4);
      g.fillStyle = G.rgb(m.car.dk); g.fillRect(x + 3, y, 8, 3);
      g.fillStyle = 'rgb(190,230,250)'; g.fillRect(x + 5, y + 1, 1, 1); g.fillRect(x + 8, y + 1, 1, 1);
      g.fillStyle = G.mod(t * 12, 2) < 1 ? 'rgb(120,230,255)' : 'rgb(80,170,220)'; g.fillRect(x + 2, y + 7, 10, 1);
      if (m.car.headlight) { g.fillStyle = 'rgb(255,250,200)'; g.fillRect(x + 13, y + 3, 1, 1); }
    }
    wrap(m.mid, dy);
    wrap(m.facade, dy);
    const R = V.road, road = img(R.image);
    if (G.ready(road)) {
      for (const [r0, r1] of R.rows) {      // 透视的石板路：越往下滚得越快
        const f = 1 + (0.55 * ((r0 + r1) / 2)) / Math.max(1, R.h);
        g.drawImage(road, G.mod(Math.floor(camX * f), 192), r0, W, r1 - r0, 0, R.y + r0, W, r1 - r0);
      }
    }
    const gt = img(m.gutter);
    if (G.ready(gt)) g.drawImage(gt, G.mod(Math.floor(camX), 16), 0, W, 4, 0, D.base + dy, W, 4);
    if (wet == null ? m.tod === 'storm' : wet) {    // 湿的路面：店面倒过来映在石板上，一行行晃
      const top = D.base + dy, n = 34;
      for (let yy = 0; yy < n; yy++) {
        const a = 0.42 * (1 - yy / n);
        if (a <= 0.02) continue;
        g.globalAlpha = a;
        g.drawImage(g.canvas, 0, top - 1 - yy, W, 1, Math.round(Math.sin(t * 7 + yy * 0.9) * (1 + yy * 0.06)), top + 4 + yy, W, 1);
      }
      g.globalAlpha = 1;
    }
    if (m.pool) {       // 路面上暖色的灯光（相加）
      const pool = img(m.pool);
      if (G.ready(pool)) { g.save(); g.globalCompositeOperation = 'lighter'; g.drawImage(pool, G.mod(Math.floor(camX), D.period), 0, W, pool.height, 0, D.base + 1 + dy, W, pool.height); g.restore(); }
    }
    // ---- 街上的小东西：霓虹闪、灯泡、门帘、灯笼、旗子、蒸汽
    const P = D.period, sxOf = (wx) => { const s = G.mod(wx - camX, P); return s < W + 40 ? s : s - P; };
    if (m.lit > 0.2 && m.unlit) {
      const unlit = img(m.unlit), fr = Math.floor(t * 15);
      D.neon.forEach(([x0, y0, x1, y1, rel], i) => {
        const sx = sxOf(x0);
        if (sx > W || sx + (x1 - x0) < 0 || fr % 3 === 0) return;
        if (G.prng(i * 7919 + Math.floor(fr / 4) * 31 + 5)() > rel && G.ready(unlit)) g.drawImage(unlit, G.mod(x0, P), y0, x1 - x0 + 1, y1 - y0 + 1, Math.floor(sx), y0 + dy, x1 - x0 + 1, y1 - y0 + 1);
      });
    }
    g.fillStyle = 'rgb(255,250,190)';
    D.bulbs.forEach(([bx, by], i) => { const sx = sxOf(bx); if (sx >= -2 && sx < W + 2 && (Math.floor(i / 2) + Math.floor(t * 10)) % 3 === 0) g.fillRect(Math.floor(sx), by + dy, 1, 1); });
    D.noren.forEach(([x0, y0, x1, y1], i) => {
      const sx = Math.floor(sxOf(x0));
      if (sx > W || sx + (x1 - x0) < 0) return;
      const s = Math.sin(t * 2.6 + i * 1.7), off = s > 0.35 ? 1 : s < -0.35 ? -1 : 0;
      if (off) g.drawImage(g.canvas, sx, y1 - 3 + dy, x1 - x0 + 1, 4, sx + off, y1 - 3 + dy, x1 - x0 + 1, 4);
    });
    for (const Ln of m.lanterns) {
      const sx = sxOf(Ln.x);
      if (!(sx > -20 && sx < W + 20)) continue;
      const spr = img(Ln.image);
      if (!G.ready(spr)) continue;
      const ang = Math.sin(t * 2 * Math.PI * 0.32 + sx * 0.071), ddx = Math.round(ang * (Ln.size === 1 ? 1.4 : 2.2)), y = Ln.y + dy, ls = 4 * Ln.size;
      G.pxLine(g, sx, y, sx + ddx, y + ls, 'rgb(40,30,34)');
      const px = Math.floor(sx + ddx - Math.floor(spr.width / 2)), py = Math.floor(y + ls);
      if (Ln.glow) {
        const s = Math.round(Math.min(1, m.lit * (0.9 + 0.1 * Math.sin(t * 13 + sx))) * 4) / 4, gl = G.image(Ln.glow[keyOf(s)]);
        if (G.ready(gl)) { g.save(); g.globalCompositeOperation = 'lighter'; g.drawImage(gl, px + Math.floor(spr.width / 2) - Ln.rad, py + Math.floor(spr.height / 2) - Ln.rad); g.restore(); }
      }
      g.drawImage(spr, px, py);
    }
    const Fl = m.flags;
    Fl.items.forEach((fl, i) => {
      const sx = Math.floor(sxOf(fl.x));
      if (!(sx > -20 && sx < W + 20)) return;
      g.fillStyle = G.rgb(Fl.pole);
      g.fillRect(sx, fl.y - 3 + dy, 1, D.base + 1 - fl.y + 4); g.fillRect(sx, fl.y - 2 + dy, 14, 1);
      g.drawImage(img(fl.frames[Math.floor(t * 5 + i) % 4]), sx + 1, fl.y + dy);
    });
    m.smoke.forEach((s, i) => {       // 小吃摊的蒸汽（6 团，3 秒一轮）
      const sx = sxOf(s.x);
      if (!(sx > -30 && sx < W + 10)) return;
      for (let k = 0; k < 6; k++) {
        const u = G.mod(t / 3 + k / 6, 1);
        if (u > 0.85 || (k + Math.floor(t * 4)) % 5 === 0) continue;
        const x = sx + Math.sin(u * 5 + i + k) * 3 + u * 16, y = s.y + dy - u * 34, r = 1.5 + u * 5;
        g.fillStyle = `rgb(${s.c.map((v, j) => Math.floor(v + (s.c2[j] - v) * u * 0.6)).join(',')})`;
        g.beginPath(); g.ellipse(x, y, r, r, 0, 0, Math.PI * 2); g.fill();
      }
    });
    if (frame) {         // 万事屋门口那个镜头：电线杆、电线、「歌舞伎町」的招牌
      const fr = G.image(D[`front_frame_${m.tod === 'storm' ? 'storm' : 'day'}`]);
      if (G.ready(fr)) g.drawImage(fr, 0, 0);
    }
  }

  // ---------------------------------------------------------------- 特效（世界坐标）
  G.fx = {
    list: [],
    clear() { this.list = []; },
    add(p) { this.list.push(Object.assign({ t: 0, life: 0.5 }, p)); },
    spark(x, y, color = '#fff', n = 7) {
      for (let i = 0; i < n; i++) {
        const a = G.rand(0, Math.PI * 2), v = G.rand(40, 110);
        this.add({ kind: 'px', x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 20, color, life: G.rand(0.15, 0.35), g: 160 });
      }
      this.add({ kind: 'ring', x, y, life: 0.16, color });
    },
    dust(x, y, n = 6) {
      for (let i = 0; i < n; i++) this.add({ kind: 'puff', x: x + G.rand(-8, 8), y: y - G.rand(0, 3), vx: G.rand(-25, 25), vy: G.rand(-14, -4), r: G.rand(2, 4), life: G.rand(0.35, 0.6), color: '200,190,170' });
    },
    word(word, x, y, life = 0.7) {
      const w = G.D.ui && G.D.ui.sfx[word];
      if (w) this.add({ kind: 'word', img: w.image, ox: w.ox, oy: w.oy, x, y, life });
    },
    star(sx) { this.add({ kind: 'star', sx, life: 1.4, screen: true }); },
    // 小图粒子（爱心、汗滴、青筋……）：o = { vx, vy, life, fade, pulse }
    img(src, x, y, o = {}) { this.add(Object.assign({ kind: 'img', img: src, x, y, vx: 0, vy: 0, life: 0.8 }, o)); },
    // 飘字（「阿～」「噫——！」「这个人」）：o = { vy, life, color, outline, size, bob }
    text(str, x, y, o = {}) { this.add(Object.assign({ kind: 'text', str, x, y, vx: 0, vy: 0, life: 1.0 }, o)); },
    // 一闪的星光（原片 fx.sparkle）
    twinkle(x, y, size = 5, color = '#fff', life = 0.45) { this.add({ kind: 'twinkle', x, y, size, color, life }); },
    // 碎屑：多色像素，带重力
    debris(x, y, colors, n = 16, speed = [40, 120], grav = 260, life = 0.8) {
      for (let i = 0; i < n; i++) {
        const a = G.rand(0, Math.PI * 2), v = G.rand(speed[0], speed[1]);
        this.add({ kind: 'px', x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 40, color: G.pick(colors), life: G.rand(life * 0.5, life), g: grav });
      }
    },
    // 屏幕坐标：集中线（原片 fx.speed_lines，每秒重新随机 15 次）和「ガーン」的竖线
    speedLines(cx, cy, o = {}) { this.add(Object.assign({ kind: 'speed', screen: true, cx, cy, count: 44, inner: 60, color: '#fff', life: 0.7, seed: Math.floor(G.rand(1, 9999)) }, o)); },
    gloom(cx, o = {}) { this.add(Object.assign({ kind: 'gloom', screen: true, cx, life: 1.2 }, o)); },
    update(dt) {
      this.list = this.list.filter((p) => {
        p.t += dt;
        if (p.vx != null) { p.x += p.vx * dt; p.y += p.vy * dt; if (p.g) p.vy += p.g * dt; }
        return p.t < p.life;
      });
    },
    draw(g, camX, camY, screenOnly) {
      for (const p of this.list) {
        if (!!p.screen !== !!screenOnly) continue;
        const k = p.t / p.life;
        const x = Math.round((p.x || 0) - camX), y = Math.round((p.y || 0) - camY);
        switch (p.kind) {
          case 'px': g.fillStyle = p.color; g.fillRect(x, y, 2, 2); break;
          case 'ring': {
            g.strokeStyle = p.color; g.globalAlpha = 1 - k; g.lineWidth = 1;
            g.beginPath(); g.arc(x + 0.5, y + 0.5, 3 + k * 12, 0, Math.PI * 2); g.stroke(); g.globalAlpha = 1; break;
          }
          case 'puff':
            g.fillStyle = `rgba(${p.color},${0.55 * (1 - k)})`;
            g.fillRect(Math.round(x - p.r * (1 + k)), Math.round(y - p.r * (1 + k) * 0.6), Math.round(p.r * 2 * (1 + k)), Math.round(p.r * (1 + k) * 1.2));
            break;
          case 'word': {
            const im = G.image(p.img);
            const s = k < 0.15 ? 0.6 + (k / 0.15) * 0.6 : 1.2 - Math.min(0.2, (k - 0.15) * 0.6);
            g.globalAlpha = k > 0.75 ? (1 - k) / 0.25 : 1;
            const w = im.width * s, h = im.height * s;
            g.drawImage(im, Math.round(x - w / 2), Math.round(y - h / 2 - k * 6), Math.round(w), Math.round(h));
            g.globalAlpha = 1;
            break;
          }
          case 'star': {   // 被打飞的天人变成天边的星星（银魂经典）
            const tw = Math.sin(p.t * 22) > 0;
            const sx = Math.round(p.sx), sy = p.sy || 22;
            g.fillStyle = tw ? '#fff8c0' : '#ffe060';
            g.fillRect(sx, sy - 3, 1, 7); g.fillRect(sx - 3, sy, 7, 1);
            if (tw) { g.fillRect(sx - 1, sy - 1, 3, 3); }
            break;
          }
          case 'img': {
            const im = G.image(p.img);
            if (!G.ready(im)) break;
            g.globalAlpha = p.fade ? Math.max(0, 1 - k * k) : 1;
            const bump = p.pulse ? Math.floor(p.t * 6) % 2 : 0;
            g.drawImage(im, Math.round(x - im.width / 2), Math.round(y - im.height / 2) - bump);
            g.globalAlpha = 1;
            break;
          }
          case 'text': {
            g.globalAlpha = k > 0.8 ? (1 - k) / 0.2 : 1;
            const f = p.size === 16 ? G.f16 : G.f12;
            const bob = p.bob ? Math.round(Math.sin(p.t * 6) * p.bob) : 0;
            f.draw(g, p.str, x, y + bob, p.color || '#fff', { align: 'center', outline: p.outline || '#140c18' });
            g.globalAlpha = 1;
            break;
          }
          case 'twinkle': {
            const s = Math.round(Math.sin(Math.min(1, k) * Math.PI) * p.size);
            if (s > 0) {
              g.fillStyle = p.color;
              g.fillRect(x - s, y, 2 * s + 1, 1); g.fillRect(x, y - s, 1, 2 * s + 1);
              if (s > 2) g.fillRect(x - 1, y - 1, 3, 3);
            }
            break;
          }
          case 'speed': {
            const rnd = G.prng(p.seed + Math.floor(p.t * 15));
            const R = 460;
            g.fillStyle = p.color;
            g.beginPath();
            for (let i = 0; i < p.count; i++) {
              const a = rnd() * Math.PI * 2, ri = p.inner + rnd() * 40, w = (0.012 + rnd() * 0.018) * 2;
              g.moveTo(p.cx + Math.cos(a) * ri, p.cy + Math.sin(a) * ri);
              g.lineTo(p.cx + Math.cos(a - w) * R, p.cy + Math.sin(a - w) * R);
              g.lineTo(p.cx + Math.cos(a + w) * R, p.cy + Math.sin(a + w) * R);
              g.closePath();
            }
            g.fill();
            break;
          }
          case 'gloom': {
            const kk = G.ease.out(Math.min(1, p.t / 0.35));
            const rnd = G.prng(77);
            for (let i = 0; i < 22; i++) {
              const gx = Math.floor(p.cx - 100 + rnd() * 204), len = Math.floor((30 + rnd() * 90) * kk), w = [1, 2, 2, 3][Math.floor(rnd() * 4)];
              g.fillStyle = `rgba(36,30,84,${(0.3 + rnd() * 0.25) * Math.min(1, (p.life - p.t) * 4)})`;
              g.fillRect(gx, 0, w, len);
            }
            break;
          }
          default: break;
        }
      }
    },
  };

  // ---------------------------------------------------------------- UI 小部件
  G.box = (g, x, y, w, h, o = {}) => {
    g.fillStyle = o.fill || 'rgba(14,16,28,0.92)';
    g.fillRect(x, y, w, h);
    g.fillStyle = o.border || '#e8dcc0';
    g.fillRect(x, y, w, 1); g.fillRect(x, y + h - 1, w, 1); g.fillRect(x, y, 1, h); g.fillRect(x + w - 1, y, 1, h);
    g.fillStyle = o.inner || 'rgba(232,220,192,0.25)';
    g.fillRect(x + 2, y + 2, w - 4, 1); g.fillRect(x + 2, y + h - 3, w - 4, 1);
  };
  G.bar = (g, x, y, w, h, k, col = '#e04848', back = '#2a2030') => {
    g.fillStyle = '#0c0a14'; g.fillRect(x - 1, y - 1, w + 2, h + 2);
    g.fillStyle = back; g.fillRect(x, y, w, h);
    g.fillStyle = col; g.fillRect(x, y, Math.round(w * G.clamp(k, 0, 1)), h);
    g.fillStyle = 'rgba(255,255,255,0.35)'; g.fillRect(x, y, Math.round(w * G.clamp(k, 0, 1)), 1);
  };
})();
