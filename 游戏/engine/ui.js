// 游戏内 UI：对话框（头像 + 名牌 + 打字音）、选项、旁白、角色名牌、篇章卡、提示、血条、菜单
'use strict';
(function () {
  const G = window.G;
  const CPS = 22;            // 每秒打几个字
  const BOX = { x: 6, y: 170, w: 372, h: 42 };

  const ui = (G.ui = {
    dlg: null,
    choiceBox: null,
    narr: null,
    cards: [],
    chapter: null,
    hints: [],
    menu: null,
    boss: null,
    hud: false,
    letterbox: 0, letterboxTarget: 0,
    insert: null,       // 全屏特写（盖住世界，对话框照样画在上面）：{ draw(g, t), t }
    notice: null,       // JRPG 式系统提示（「志村新八 加入了万事屋！」）
    qte: null,          // 按键小游戏：连按 / 看准时机 / 跟着节拍
    timer: null,        // 战斗计时（「天亮还有 30 秒」）：{ label, until }

    reset() {
      this.dlg = null; this.choiceBox = null; this.narr = null; this.cards = []; this.chapter = null;
      this.hints = []; this.menu = null; this.boss = null; this.hud = false; this.letterbox = 0; this.letterboxTarget = 0;
      this.insert = null; this.notice = null; this.qte = null; this.timer = null;
    },
    blocking() { return !!(this.dlg || this.choiceBox || this.narr || this.chapter || this.menu || this.notice || this.qte); },
    // 按键小游戏（返回 Promise）：
    //   { type: 'mash', label, need, time, decay }               连按 J / Enter 把槽打满
    //   { type: 'timing', label, speed, zone: [a, b], tries }    指针来回走，停在亮区里按
    //   { type: 'rhythm', label, notes: [秒…], window, travel }  音符走到线上时按，结果 = { hits, total }
    startQte(o) {
      return new Promise((res) => {
        this.qte = Object.assign({ t: 0, res, v: 0, result: null, endT: 0, judged: [], tries: 1, misses: 0 }, o);
        if (o.type === 'rhythm') this.qte.state = o.notes.map(() => 0);   // 0 = 还没到，1 = 打中，-1 = 漏了
      });
    },

    // ---------------- 对话
    say(who, text, o = {}) {
      const meta = who && G.D.chars[who];
      const name = o.name || (G.NAMES && G.NAMES[who]) || (meta ? meta.name : who || '');
      const lines = G.f12.wrap(text, who ? 318 : 352);
      const pages = [];
      for (let i = 0; i < lines.length; i += 2) pages.push(lines.slice(i, i + 2));
      return new Promise((res) => {
        this.dlg = { who, name, expr: o.expr, pages, page: 0, shown: 0, voice: (meta && meta.voice) || 1, res, t: 0, color: o.color };
        if (o.sfx) G.audio.sfx(o.sfx);
      });
    },
    choice(options, title) {
      return new Promise((res) => { this.choiceBox = { options, idx: 0, res, title }; G.audio.sfx('pop', 0.5); });
    },
    narrate(text, o = {}) {
      return new Promise((res) => {
        this.narr = { lines: G.f12.wrap(text, 330), t: 0, shown: 0, res, auto: o.auto, top: !!o.top, onBlack: !!o.onBlack };
      });
    },
    nameCard(cid) {
      const c = G.D.ui.namecards[cid];
      if (c) this.cards.push(Object.assign({ t: 0, dur: 2.6 }, c));
    },
    chapterCard(key) {
      const src = G.D.ui.chapters[key];
      return new Promise((res) => { this.chapter = { img: G.image(src), t: 0, dur: 2.8, res }; G.audio.sfx('gong', 0.7); });
    },
    hint(text, dur = 4.5) { this.hints = [{ text, t: 0, dur }]; },
    // o = { who, expr, title, text, sub }：底部弹出的系统框，按确认关掉
    showNotice(o) {
      return new Promise((res) => { this.notice = Object.assign({ t: 0, res }, o); });
    },
    openMenu(title, options, o = {}) {
      return new Promise((res) => { this.menu = Object.assign({ title, options, idx: 0, res }, o); });
    },

    // 手机上提示放在上面，名牌也从上面滑进来：名牌在的时候提示先等着（不计时、不画），名牌走了再出来
    hintHeld() { return !!(G.touch && G.touch.on && this.cards.length); },

    // ---------------- 每帧
    update(dt) {
      const I = G.input;
      this.letterbox += (this.letterboxTarget - this.letterbox) * Math.min(1, dt * 6);
      if (this.insert) this.insert.t += dt;
      for (const c of this.cards) c.t += dt;
      this.cards = this.cards.filter((c) => c.t < c.dur);
      if (!this.hintHeld()) for (const h of this.hints) h.t += dt;
      this.hints = this.hints.filter((h) => h.t < h.dur);
      if (this.menu) {
        const m = this.menu;
        if (I.tap) {      // 触屏 / 鼠标：点中某一项 = 选中并确认（点击本身已经给了确认）；点在菜单外 = 取消（有取消项的话）；点在别处 = 不算
          const L = this.menuLayout(m), t = I.tap;
          const row = Math.floor((t.y - (L.oy - 2)) / 18);
          const inBox = t.x >= L.x && t.x <= L.x + L.w && t.y >= L.y && t.y <= L.y + L.h;
          if (inBox && row >= 0 && row < m.options.length) m.idx = row;
          else {
            I.consume('ok');
            if (!inBox && m.escIndex != null) { const r = m.res; this.menu = null; G.audio.sfx('pop', 0.5); r(m.escIndex); return; }
          }
        }
        if (I.hit('up')) { m.idx = (m.idx + m.options.length - 1) % m.options.length; G.audio.sfx('blip', 0.5, 1.4); }
        if (I.hit('down')) { m.idx = (m.idx + 1) % m.options.length; G.audio.sfx('blip', 0.5, 1.4); }
        if (I.okHit()) { I.consumeOk(); const r = m.res, i = m.idx; this.menu = null; G.audio.sfx('pop', 0.6); r(i); }
        else if (I.hit('pause') && m.escIndex != null) { I.consume('pause'); const r = m.res; this.menu = null; r(m.escIndex); }
        return;
      }
      if (this.chapter) {
        this.chapter.t += dt;
        if (this.chapter.t >= this.chapter.dur) { const r = this.chapter.res; this.chapter = null; r(); }
        return;
      }
      if (this.notice) {
        const n = this.notice;
        n.t += dt;
        if (n.t > 0.6 && I.okHit()) { I.consumeOk(); const r = n.res; this.notice = null; G.audio.sfx('pop', 0.5); r(); }
        return;
      }
      if (this.qte) { this.updateQte(dt); return; }
      if (this.choiceBox) {
        const c = this.choiceBox;
        if (I.tap) {      // 同上：点中某一项 = 选中并确认，点在别处不算
          const L = this.choiceLayout(c), t = I.tap;
          const row = Math.floor((t.y - (L.y + 3)) / 16);
          if (t.x >= L.x - 4 && t.x <= L.x + L.w + 4 && row >= 0 && row < c.options.length) c.idx = row;
          else I.consume('ok');
        }
        if (I.hit('up')) { c.idx = (c.idx + c.options.length - 1) % c.options.length; G.audio.sfx('blip', 0.5, 1.4); }
        if (I.hit('down')) { c.idx = (c.idx + 1) % c.options.length; G.audio.sfx('blip', 0.5, 1.4); }
        if (I.okHit()) { I.consumeOk(); const r = c.res, i = c.idx; this.choiceBox = null; G.audio.sfx('pop', 0.6); r(i); }
        return;
      }
      if (this.dlg) {
        const d = this.dlg;
        d.t += dt;
        const page = d.pages[d.page];
        const total = page.join('').length;
        if (d.shown < total) {
          const before = Math.floor(d.shown);
          d.shown = Math.min(total, d.shown + CPS * dt);
          if (d.who && Math.floor(d.shown) !== before && before % 2 === 0) G.audio.sfx('blip', 0.32, d.voice * G.rand(0.94, 1.06));
          if (I.okHit() && d.t > 0.08) { I.consumeOk(); d.shown = total; }
        } else if (I.okHit()) {
          I.consumeOk();
          if (d.page < d.pages.length - 1) { d.page++; d.shown = 0; d.t = 0; }
          else { const r = d.res; this.dlg = null; r(); }
        }
        return;
      }
      if (this.narr) {
        const n = this.narr;
        n.t += dt;
        const total = n.lines.join('').length;
        n.shown = Math.min(total, n.shown + CPS * 0.8 * dt);
        if (I.okHit() && n.t > 0.15) {
          I.consumeOk();
          if (n.shown < total) n.shown = total;
          else { const r = n.res; this.narr = null; r(); }
        } else if (n.auto && n.t > n.auto) { const r = n.res; this.narr = null; r(); }
      }
    },

    // ---------------- 画（世界之上、黑幕之下）
    draw(g) {
      if (this.insert) this.insert.draw(g, this.insert.t);
      if (this.letterbox > 0.5) {
        const h = Math.round(this.letterbox);
        g.fillStyle = '#000'; g.fillRect(0, 0, G.W, h); g.fillRect(0, G.H - h, G.W, h);
      }
      if (this.hud) this.drawHud(g);
      for (const c of this.cards) {
        const k = c.t < 0.3 ? G.ease.out(c.t / 0.3) : c.t > c.dur - 0.3 ? G.ease.out((c.dur - c.t) / 0.3) : 1;
        const left = c.x + (c.w || 0) / 2 < G.W / 2;      // 左边的名牌从左边滑进来
        const x = Math.round(G.lerp(left ? -(c.w || 260) - 4 : G.W + 4, c.x, k));
        const ci = G.image(c.image);
        if (G.ready(ci)) g.drawImage(ci, x, c.y);     // 缺图也不能让整个画面卡死
      }
      for (const h of this.hints) {
        if (this.hintHeld()) continue;
        const a = Math.min(1, h.t * 4, (h.dur - h.t) * 3);
        g.globalAlpha = Math.max(0, a);
        const tc = G.touch && G.touch.on;     // 手机：下面两边是方向盘和按钮，提示改放上面（血条、同伴条、计时的下面），宽度躲开右上角的暂停 / 全屏钮
        const lines = G.f12.wrap(h.text, tc ? Math.max(200, Math.min(344, 2 * (G.touch.safe.sys - 6 - G.W / 2))) : 344);
        const w = Math.max(...lines.map((l) => G.f12.width(l))) + 16;
        const hh = lines.length * 14 + 6;
        const y = tc ? 30 + (this.hud ? G.world.allies().length * 14 : 0) + (this.hud && this.timer && G.touch.safe.sys < G.W - 2 ? 17 : 0)
          : this.dlg || this.choiceBox ? 30 : G.H - hh - 6;   // 平时放底部，免得挡住血条和名牌
        G.box(g, Math.round((G.W - w) / 2), y, w, hh, { fill: 'rgba(20,18,30,0.86)', border: '#ffd34a' });
        lines.forEach((l, i) => G.f12.draw(g, l, G.W / 2, y + 4 + i * 14, '#fff', { align: 'center' }));
        g.globalAlpha = 1;
      }
      if (this.narr && !this.narr.onBlack) this.drawNarr(g);
      if (this.dlg) this.drawDialog(g);
      if (this.choiceBox) this.drawChoice(g);
      if (this.notice) this.drawNotice(g);
      if (this.qte) this.drawQte(g);
      if (this.chapter) {
        const c = this.chapter;
        const a = Math.min(1, c.t / 0.35, (c.dur - c.t) / 0.35);
        g.globalAlpha = Math.max(0, a);
        if (G.ready(c.img)) g.drawImage(c.img, 0, 0);
        g.globalAlpha = 1;
      }
    },
    // 画在黑幕之上（旁白黑场、菜单）
    drawTop(g) {
      if (this.narr && this.narr.onBlack) this.drawNarr(g);
      if (this.menu) this.drawMenu(g);
    },
    drawNarr(g) {
      const n = this.narr;
      const lh = 16;
      const y0 = n.top ? 24 : n.onBlack ? Math.round(G.H / 2 - (n.lines.length * lh) / 2) : 96;
      if (!n.onBlack) { g.fillStyle = 'rgba(10,8,16,0.72)'; g.fillRect(0, y0 - 6, G.W, n.lines.length * lh + 10); }
      let left = Math.floor(n.shown);
      n.lines.forEach((line, i) => {
        const part = line.slice(0, Math.max(0, left));
        left -= line.length;
        G.f12.draw(g, part, Math.round(G.W / 2 - G.f12.width(line) / 2), y0 + i * lh, '#fff4d6', { outline: '#140c18' });
      });
    },
    drawDialog(g) {
      const d = this.dlg;
      const b = BOX;
      G.box(g, b.x, b.y, b.w, b.h);
      let tx = b.x + 10;
      if (d.who) {
        const img = G.head(d.who, d.expr);
        const fx = b.x + 4, fy = b.y + 4, fw = 36, fh = 34;
        g.fillStyle = '#2c2a3e'; g.fillRect(fx, fy, fw, fh);
        g.fillStyle = '#4a4660'; g.fillRect(fx, fy, fw, 1);
        if (img && G.ready(img)) {
          // 原片的对话头像就是小人头像放大 2 倍；放不下的部分裁掉（底边对齐）
          const s = img.width * 2 <= 48 && img.height * 2 <= 48 ? 2 : 1;
          const w = img.width * s, h = img.height * s;
          g.save();
          g.beginPath(); g.rect(fx, fy, fw, fh); g.clip();
          g.drawImage(img, fx + Math.round((fw - w) / 2), fy + fh - h + (s === 2 ? 4 : 0), w, h);
          g.restore();
        }
        tx = b.x + 46;
      }
      if (d.name) {
        const w = G.f12.width(d.name) + 12;
        G.box(g, b.x + 2, b.y - 14, w, 15, { fill: d.color || '#7a2a2e', border: '#f0d9a0', inner: 'rgba(255,255,255,0.12)' });
        G.f12.draw(g, d.name, b.x + 8, b.y - 12, '#fff8e8');
      }
      const page = d.pages[d.page];
      let left = Math.floor(d.shown);
      page.forEach((line, i) => {
        const part = line.slice(0, Math.max(0, left));
        left -= line.length;
        G.f12.draw(g, part, tx, b.y + 7 + i * 16, '#fff');
      });
      if (d.shown >= page.join('').length && Math.floor(G.realTime * 3) % 2 === 0) G.f12.draw(g, '▼', b.x + b.w - 14, b.y + b.h - 14, '#ffd34a');
    },
    choiceLayout(c) {
      const w = Math.max(...c.options.map((o) => G.f12.width(o))) + 26;
      const h = c.options.length * 16 + 10;
      const x = G.touch && G.touch.on ? Math.min(G.W - w - 8, G.touch.safe.r - w - 6) : G.W - w - 8;     // 手机：躲开右下角的按钮
      return { x, y: BOX.y - h - 4, w, h };
    },
    menuLayout(m) {
      const w = Math.max(G.f16.width(m.title || ''), ...m.options.map((o) => G.f12.width(o) + 30)) + 40;
      const h = (m.title ? 30 : 10) + m.options.length * 18 + (m.note ? 18 : 0) + 8;
      const x = Math.round((G.W - w) / 2), y = Math.round((G.H - h) / 2);
      return { x, y, w, h, oy: y + (m.title ? 32 : 10) };
    },
    drawChoice(g) {
      const c = this.choiceBox;
      const { x, y, w, h } = this.choiceLayout(c);
      G.box(g, x, y, w, h, { border: '#ffd34a' });
      c.options.forEach((o, i) => {
        const sel = i === c.idx;
        if (sel) { g.fillStyle = 'rgba(255,211,74,0.18)'; g.fillRect(x + 3, y + 4 + i * 16, w - 6, 15); }
        G.f12.draw(g, sel ? '►' : ' ', x + 6, y + 6 + i * 16, '#ffd34a');
        G.f12.draw(g, o, x + 18, y + 6 + i * 16, sel ? '#fff' : '#bdb6c8');
      });
    },
    drawMenu(g) {
      const m = this.menu;
      g.fillStyle = 'rgba(0,0,0,0.55)'; g.fillRect(0, 0, G.W, G.H);
      const { x, y, w, h, oy } = this.menuLayout(m);
      G.box(g, x, y, w, h, { border: '#ffd34a' });
      if (m.title) G.f16.draw(g, m.title, G.W / 2, y + 8, '#ffe9a8', { align: 'center', outline: '#1a1020' });
      m.options.forEach((o, i) => {
        const sel = i === m.idx;
        if (sel) { g.fillStyle = 'rgba(255,211,74,0.18)'; g.fillRect(x + 6, oy + i * 18 - 2, w - 12, 16); }
        G.f12.draw(g, (sel ? '► ' : '  ') + o, x + 18, oy + i * 18, sel ? '#fff' : '#bdb6c8');
      });
      if (m.note) G.f12.draw(g, m.note, G.W / 2, oy + m.options.length * 18 + 4, '#9a93a8', { align: 'center' });
    },
    // ---------------- 按键小游戏
    updateQte(dt) {
      const q = this.qte, I = G.input;
      q.t += dt;
      if (q.result != null) {   // 显示结果一小会儿再结束
        q.endT += dt;
        if (q.endT > 0.7) { const r = q.res, out = q.result; this.qte = null; r(out); }
        return;
      }
      const press = I.okHit();
      if (press) I.consumeOk();
      if (q.type === 'mash') {
        q.v = Math.max(0, q.v - (q.decay || 2.5) * dt);
        if (press) { q.v += 1; G.audio.sfx('blip', 0.35, 1.0 + q.v / q.need); }
        if (q.v >= q.need) { q.result = true; G.audio.sfx('sparkle', 0.7); }
        else if (q.t >= q.time) { q.result = false; G.audio.sfx('fail', 0.5); }
      } else if (q.type === 'timing') {
        const ph = (q.t * (q.speed || 1.2)) % 2, m = ph < 1 ? ph : 2 - ph;
        q.m = m;
        if (press) {
          if (m >= q.zone[0] && m <= q.zone[1]) { q.result = true; G.audio.sfx('shing', 0.7); }
          else if (--q.tries <= 0) { q.result = false; G.audio.sfx('fail', 0.5); }
          else G.audio.sfx('clang', 0.4);
        }
        if (q.limit && q.t > q.limit && q.result == null) { q.result = false; G.audio.sfx('fail', 0.5); }
      } else if (q.type === 'rhythm') {
        const win = q.window || 0.16;
        if (press) {
          let best = -1, bd = 1e9;
          q.notes.forEach((nt, i) => { if (q.state[i] === 0 && Math.abs(q.t - nt) < bd) { bd = Math.abs(q.t - nt); best = i; } });
          if (best >= 0 && bd <= win) { q.state[best] = 1; q.judged.push({ t: q.t, ok: true }); G.audio.sfx('pop', 0.6, 1.3); }
          else { q.judged.push({ t: q.t, ok: false }); G.audio.sfx('blip', 0.3, 0.6); }
        }
        q.notes.forEach((nt, i) => { if (q.state[i] === 0 && q.t - nt > win) { q.state[i] = -1; q.judged.push({ t: q.t, ok: false }); } });
        if (q.t > q.notes[q.notes.length - 1] + 0.8) {
          const hits = q.state.filter((s) => s === 1).length;
          q.result = { hits, total: q.notes.length };
          G.audio.sfx(hits >= q.notes.length * (q.pass || 0.6) ? 'cheer' : 'fail', 0.6);
        }
      }
    },
    drawQte(g) {
      const q = this.qte;
      const bw = 220, x0 = Math.round(G.W / 2 - bw / 2), y0 = 132;
      G.box(g, x0, y0, bw, 40, { fill: 'rgba(14,16,28,0.88)', border: '#ffd34a' });
      G.f12.draw(g, q.label || '', G.W / 2, y0 + 4, '#ffe9a8', { align: 'center' });
      if (q.type === 'mash') {
        G.bar(g, x0 + 12, y0 + 22, bw - 24, 6, q.v / q.need, '#ffb03a');
        G.bar(g, x0 + 12, y0 + 32, bw - 24, 1, 1 - q.t / q.time, '#8a8498');
      } else if (q.type === 'timing') {
        const bx = x0 + 12, bwid = bw - 24, by = y0 + 22;
        g.fillStyle = '#2a2030'; g.fillRect(bx, by, bwid, 8);
        g.fillStyle = '#ffd34a'; g.fillRect(bx + Math.round(q.zone[0] * bwid), by, Math.round((q.zone[1] - q.zone[0]) * bwid), 8);
        const mx = bx + Math.round((q.m || 0) * bwid);
        g.fillStyle = '#fff'; g.fillRect(mx - 1, by - 3, 3, 14);
      } else if (q.type === 'rhythm') {
        const lx = x0 + 30, by = y0 + 26, travel = q.travel || 1.6;
        g.fillStyle = '#2a2030'; g.fillRect(x0 + 8, by - 5, bw - 16, 11);
        g.fillStyle = '#ffd34a'; g.fillRect(lx, by - 7, 2, 15);
        q.notes.forEach((nt, i) => {
          if (q.state[i] !== 0) return;
          const x = lx + Math.round(((nt - q.t) / travel) * (bw - 50));
          if (x < x0 + 6 || x > x0 + bw - 8) return;
          g.fillStyle = '#ff9ec0'; g.fillRect(x - 3, by - 3, 7, 7);
          g.fillStyle = '#fff'; g.fillRect(x - 1, by - 1, 3, 3);
        });
        const last = q.judged[q.judged.length - 1];
        if (last && q.t - last.t < 0.35) G.f12.draw(g, last.ok ? '好！' : '……', lx - 2, y0 - 12, last.ok ? '#ffe14a' : '#9a93a8', { align: 'center', outline: '#140c18' });
        G.f12.draw(g, `${q.state.filter((s) => s === 1).length} / ${q.notes.length}`, x0 + bw - 12, y0 + 4, '#cfe8ff', { align: 'right' });
      }
      if (q.result != null) {
        const ok = q.result === true || (q.result && q.result.hits != null && q.result.hits >= q.result.total * (q.pass || 0.6));
        G.f16.draw(g, ok ? '成功！' : '失败……', G.W / 2, y0 - 22, ok ? '#ffe14a' : '#cfc8dc', { align: 'center', outline: '#140c18' });
      }
    },
    // 原片 s02 的「加入了万事屋」框：底部居中，弹出来，头像 + 两行字 + 周围冒小星星
    drawNotice(g) {
      const n = this.notice;
      const k = G.ease.outBack(Math.min(1, n.t / 0.25));
      const bw = 236, bh = 34, x0 = Math.round(G.W / 2 - bw / 2), y0 = 172 + Math.round((1 - k) * 30);
      g.fillStyle = 'rgba(12,16,48,0.9)'; g.fillRect(x0, y0, bw, bh);
      g.fillStyle = '#fff';
      g.fillRect(x0, y0, bw, 1); g.fillRect(x0, y0 + bh - 1, bw, 1); g.fillRect(x0, y0, 1, bh); g.fillRect(x0 + bw - 1, y0, 1, bh);
      g.fillStyle = '#5a6ec8';
      g.fillRect(x0 + 2, y0 + 2, bw - 4, 1); g.fillRect(x0 + 2, y0 + bh - 3, bw - 4, 1); g.fillRect(x0 + 2, y0 + 2, 1, bh - 4); g.fillRect(x0 + bw - 3, y0 + 2, 1, bh - 4);
      const img = n.who && G.head(n.who, n.expr || 'happy');
      if (img && G.ready(img)) {
        g.save(); g.beginPath(); g.rect(x0 + 4, y0 + 3, 40, bh - 6); g.clip();
        g.drawImage(img, x0 + 6, y0 + bh - 4 - img.height * 2 + 6, img.width * 2, img.height * 2);
        g.restore();
      }
      const tx = x0 + 50;
      G.f12.draw(g, n.title || '', tx, y0 + 5, '#ffe26e', { outline: '#140c18' });
      G.f12.draw(g, n.text || '', tx + G.f12.width(n.title || '') + 4, y0 + 5, '#fff', { outline: '#140c18' });
      if (n.sub) G.f12.draw(g, n.sub, tx, y0 + 19, '#96dcff', { outline: '#140c18' });
      if (n.t > 0.6 && Math.floor(G.realTime * 3) % 2 === 0) G.f12.draw(g, '▼', x0 + bw - 14, y0 + bh - 14, '#fff');
      const rnd = G.prng(31);
      for (let i = 0; i < 6; i++) {
        const sx = x0 + Math.floor(rnd() * (bw + 20) - 10), sy = y0 + Math.floor(rnd() * 16 - 12), t0 = 0.05 + i * 0.12;
        const kk = (n.t - t0) / 0.45;
        if (kk <= 0 || kk >= 1) continue;
        const s = Math.round(Math.sin(kk * Math.PI) * 3);
        g.fillStyle = '#fff096'; g.fillRect(sx - s, sy, 2 * s + 1, 1); g.fillRect(sx, sy - s, 1, 2 * s + 1);
      }
    },
    drawHud(g) {
      const p = G.world.player;
      if (p) {
        G.box(g, 4, 4, 112, 20, { fill: 'rgba(14,16,28,0.8)' });
        const img = G.head(p.cid, p.hp / p.maxHp < 0.3 ? 'hurt' : 'normal');
        if (img && G.ready(img)) g.drawImage(img, 6, 5 + Math.max(0, 18 - img.height), Math.min(img.width, 20), Math.min(img.height, 18));
        G.f12.draw(g, p.name, 28, 6, '#fff');
        const k = p.hp / p.maxHp;
        G.bar(g, 28, 19, 82, 3, k, k < 0.3 ? '#ff6040' : '#e8c440');
      }
      // 同伴的小血条（倒地时显示「倒地」，过一会儿自己爬起来）
      G.world.allies().forEach((a, i) => {
        const y = 27 + i * 14;
        G.box(g, 4, y, 112, 12, { fill: 'rgba(14,16,28,0.72)', inner: 'rgba(0,0,0,0)' });
        G.f12.draw(g, a.name, 8, y, a.state === 'down' ? '#8a8498' : '#cfe8ff');
        const bx = Math.max(46, 12 + G.f12.width(a.name));      // 名字长就把血条往右挪
        if (a.state === 'down') G.f12.draw(g, '倒地', Math.max(60, bx), y, '#ff9a8a');
        else G.bar(g, bx, y + 5, Math.max(16, 110 - bx), 2, a.hp / a.maxHp, '#7ac8ff');
      });
      if (this.timer) {   // 计时（撑到天亮之类）
        const left = Math.max(0, Math.ceil(this.timer.until - G.world.fightT));
        const ty = G.touch && G.touch.on && G.touch.safe.sys < G.W - 2 ? 30 : 4;      // 手机：暂停 / 全屏钮压在画面右上角时，计时放到它们下面
        G.box(g, G.W - 118, ty, 114, 15, { fill: 'rgba(14,16,28,0.8)' });
        G.f12.draw(g, `${this.timer.label}${left} 秒`, G.W - 61, ty + 1, left <= 5 ? '#ffd34a' : '#fff', { align: 'center' });
      }
      const b = this.boss;
      if (b && !b.remove) {
        const w = 150, x = Math.round((G.W - w) / 2);
        G.f12.draw(g, b.name, G.W / 2, 6, '#ffd0d0', { align: 'center', outline: '#200810' });
        G.bar(g, x, 21, w, 4, b.hp / b.maxHp, '#e83040');
      }
    },
  });
})();
