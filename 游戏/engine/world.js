// 世界：地图（场景）、角色、玩家操作、同伴 / 敌人 AI、战斗判定、镜头、互动与触发区
'use strict';
(function () {
  const G = window.G;

  // 出招表（fps = 播放速度；active = 有判定的帧；reach = 身前判定距离）
  const COMBO = [
    { anim: 'attack', fps: 26, active: [3, 4], dmg: 8, reach: [2, 31], kb: 34, sfx: 'slash' },
    { anim: 'slash_up', fps: 26, active: [1, 3], dmg: 8, reach: [2, 29], kb: 34, sfx: 'slash' },
    { anim: 'thrust', fps: 22, active: [1, 3], dmg: 14, reach: [2, 39], kb: 140, sfx: 'slash_big', heavy: true, word: true },
  ];
  const AIR = { anim: 'attack', fps: 30, active: [3, 5], dmg: 10, reach: [-4, 30], kb: 70, sfx: 'slash' };
  const E_SLASH = { anim: 'attack', fps: 15, active: [3, 4], dmg: 9, reach: [2, 29], kb: 80, sfx: 'slash' };
  const E_PUNCH = { anim: 'punch', fps: 15, active: [2, 4], dmg: 7, reach: [2, 23], kb: 60, sfx: 'punch' };
  const E_HEAVY = { anim: 'attack', fps: 12, active: [3, 4], dmg: 16, reach: [2, 34], kb: 150, sfx: 'slash_big', heavy: true, word: true };
  // 同伴（新八）的木刀：比银时弱，主要是帮忙牵制
  const A_SLASH = { anim: 'attack', fps: 20, active: [3, 4], dmg: 6, reach: [2, 30], kb: 40, sfx: 'slash' };
  const A_UP = { anim: 'slash_up', fps: 20, active: [1, 3], dmg: 6, reach: [2, 28], kb: 40, sfx: 'slash' };
  // 远程：出招到第 fire 帧时射出 shot（子弹、火箭筒、苦无……），shot 的写法见 W.shoot
  // （动作名在角色图集里没有时，自动退回 attack）
  const E_GUN = { anim: 'umbrella_shoot', fps: 14, active: [99, 99], fire: [2, 4, 6], shot: { kind: 'bullet', speed: 260, dmg: 4, kb: 30 } };
  const E_BAZOOKA = { anim: 'bazooka', fps: 10, active: [99, 99], fire: [3], shot: { kind: 'rocket', speed: 170, dmg: 14, kb: 120, explode: 30 } };
  const E_KUNAI = { anim: 'throw_kunai', fps: 14, active: [99, 99], fire: [3], shot: { kind: 'kunai', speed: 230, dmg: 7, kb: 40 } };
  const E_NEEDLE = { anim: 'needle', fps: 14, active: [99, 99], fire: [2, 4], shot: { kind: 'kunai', speed: 300, dmg: 6, kb: 30, spread: 4 } };
  const E_PISTOL = { anim: 'shoot', fps: 12, active: [99, 99], fire: [3], shot: { kind: 'bullet', speed: 300, dmg: 6, kb: 40 } };
  G.MOVES = { COMBO, AIR, E_SLASH, E_PUNCH, E_HEAVY, A_SLASH, A_UP, E_GUN, E_BAZOOKA, E_KUNAI, E_NEEDLE, E_PISTOL };

  // 阵营：玩家和同伴是一边（互相打不到）
  const side = (a) => (a.team === 'player' || a.team === 'ally' ? 'good' : a.team);

  // ---------------------------------------------------------------- 角色
  class Actor {
    constructor(cid, x, y, o = {}) {
      this.cid = cid;
      this.atlas = G.atlas(cid);
      if (o.alt) this.alt = o.alt.filter((id) => G.D.chars[id]).map((id) => G.atlas(id));   // 原片特殊动作的附加图集
      this.id = o.id || cid;
      this.name = o.name || G.D.chars[cid].name;
      this.x = x; this.y = y; this.z = 0;
      this.vx = 0; this.vz = 0;
      this.facing = o.facing || 1;
      this.scale = o.scale || 1;
      this.team = o.team || 'npc';
      this.maxHp = this.hp = o.hp || 100;
      this.idleAnim = o.anim || 'idle';
      this.anim = this.idleAnim; this.animT = G.rand(0, 2); this.animSpeed = 1;
      this.frozen = null;  // 定格在第几帧（石化）
      this.state = 'idle'; this.stateT = 0;
      this.speed = o.speed || 72;
      this.flash = 0; this.alpha = 1; this.visible = o.visible !== false; this.shadow = o.shadow !== false;
      this.tint = o.tint || null;   // { color, k }：染色（石化的灰、吃了煎蛋的紫）
      this.talk = o.talk || null;
      this.label = o.label || null;
      this.talkRy = o.talkRy || 14;   // 能搭话的前后距离（坐在桌子后面的人要大一点）
      this.emote = null;
      this.hitList = new Set();
      this.invuln = 0; this.cool = G.rand(0.6, 1.4); this.laneOff = G.rand(-5, 5); this.range = o.range || 25;
      this.boss = !!o.boss; this.moves = o.moves || [E_SLASH]; this.dead = false; this.remove = false;
      this.hold = false;   // 剧情里摆好的姿势，不被自动切回 idle
      this.rot = 0;
      this.follow = null;  // 地图上跟着谁走（同伴）
      this.focus = null; this.focusT = 0;   // 敌人：现在盯着谁打
    }
    play(name, o = {}) {
      if (this.anim !== name || o.restart) { this.anim = name; this.animT = 0; this.frozen = null; }
      this.animSpeed = o.speed || 1;
    }
    // 附加图集（原片场景里的特殊动作，比如 gintoki__s03 的「骑小绵羊挖鼻孔」）：本体没有的动作到这里找
    atlasFor(name) {
      if (this.alt) for (const at of this.alt) if (at.has(name)) return at;     // 附加图集优先（同名动作用原片那一版，比如多帧的蹲草丛）
      return this.atlas;
    }
    get a() { return this.atlasFor(this.anim).anim(this.anim); }
    frameIndex() {
      const a = this.a;
      if (this.frozen != null) return Math.min(this.frozen, a.frames - 1);
      const n = Math.floor(this.animT * a.fps * this.animSpeed + 1e-6);
      return a.kind === 'loop' ? n % a.frames : Math.min(n, a.frames - 1);
    }
    animDone() { const a = this.a; return a.kind !== 'loop' && this.animT * a.fps * this.animSpeed >= a.frames; }
    headY() { return this.y - this.z - (this.atlas.py - 4) * this.scale; }
    draw(g, camX, camY) {
      if (!this.visible) return;
      const sx = Math.round(this.x - camX), sy = Math.round(this.y - camY);
      if (this.shadow && this.alpha > 0.3 && this.state !== 'dead' && !this.rot) {
        const sw = Math.round(12 * this.scale);
        g.fillStyle = 'rgba(0,0,0,0.25)';
        g.fillRect(sx - (sw >> 1), sy - 1, sw, 2);
      }
      const blink = this.invuln > 0 && (this.team === 'player' || this.team === 'ally') && Math.floor(G.time * 20) % 2 === 0;
      // 骑着 / 坐着的载具（小绵羊、警车）：ride = { frames | image, fps, ax, ay, seat（人抬高几像素）, front（盖在人前面的图） }
      const r = this.ride;
      const rideImg = (src) => {
        const im = G.image(src);
        if (!G.ready(im)) return;
        g.save(); g.translate(sx, sy - Math.round(this.z)); if (this.facing < 0) g.scale(-1, 1);
        g.drawImage(im, -r.ax, -r.ay); g.restore();
      };
      if (r) rideImg(r.frames ? r.frames[Math.floor(G.time * (r.fps || 8)) % r.frames.length] : r.image);
      this.atlasFor(this.anim).draw(g, this.anim, this.frameIndex(), sx + (r && r.dx ? r.dx * this.facing : 0), sy - Math.round(this.z) - (r ? r.seat || 0 : 0), {
        flip: this.facing < 0, scale: this.scale, alpha: blink ? 0.45 : this.alpha, flash: this.flash, rot: this.rot, tint: this.tint,
      });
      if (r && r.front) rideImg(r.front);
      if (r && r.light) {   // 车灯：相加混合的光锥
        const im = G.image(r.light.image);
        if (G.ready(im)) {
          g.save(); g.globalCompositeOperation = 'lighter'; g.translate(sx, sy - Math.round(this.z)); if (this.facing < 0) g.scale(-1, 1);
          g.drawImage(im, r.light.ox, r.light.oy); g.restore();
        }
      }
    }
  }
  G.Actor = Actor;

  // ---------------------------------------------------------------- 地图
  class Stage {
    constructor(def) {
      this.def = def;
      this.id = def.id;
      this.kind = def.kind || 'layers';
      const spec = G.D.bg[def.bg];
      this.bg = this.kind === 'layers' ? new G.Background(spec) : null;
      this.office = this.kind === 'office' ? spec : null;
      this.x0 = def.x0 == null ? 0 : def.x0;
      this.x1 = def.x1 == null ? G.W : def.x1;
      this.yMin = def.yMin == null ? 158 : def.yMin;
      this.yMax = def.yMax == null ? 198 : def.yMax;
      this.actors = [];
      this.props = (def.props || []).map((p) => Object.assign({}, p));
      this.hotspots = (def.hotspots || []).map((h) => Object.assign({}, h));
      this.triggers = (def.triggers || []).map((t) => Object.assign({ fired: false }, t));
      this.obstacles = def.obstacles || [];
      this.camX = def.camX || 0;
      this.camY = 0;
      this.lock = null;
      this.t = 0;
      this.door = 0; this.doorTarget = 0;
      this.state = Object.assign({}, def.state || {});   // 剧情改的画面状态（墙洞、窗外的乌鸦、光束……）
    }
    add(a) { this.actors.push(a); return a; }
    find(id) { return this.actors.find((a) => a.id === id && !a.remove); }
    bounds() { return this.lock ? [this.lock.x0 + 10, this.lock.x1 - 10] : [this.x0 + 8, this.x1 - 8]; }
  }
  G.Stage = Stage;

  // ---------------------------------------------------------------- 世界
  const W = (G.world = {
    stage: null,
    player: null,
    free: false,        // 玩家能不能动
    combat: false,      // 战斗中（能出招、敌人会打）
    focus: null,        // 镜头跟谁（默认玩家）
    near: null,         // 当前能互动的对象
    maxTokens: 2,       // 同时最多几个敌人出手
    anims: [],          // S.animate 的逐帧回调
    ticks: [],          // 每帧都要跑的回调（自动卷轴、战斗里的增援）：fn(dt)，返回 true 就移除
    shots: [],          // 飞行道具（子弹、火箭筒、苦无……）
    fightT: 0,          // 这场战斗打了几秒（剧情事件、计时用）

    setStage(def, o = {}) {
      const st = new Stage(def);
      this.stage = st;
      this.shots = [];
      G.fx.clear();
      const p = o.player;
      if (p) {
        p.x = o.x == null ? p.x : o.x;
        p.y = o.y == null ? p.y : o.y;
        p.z = 0; p.vx = 0; p.state = 'idle';
        st.add(p);
      }
      for (const n of def.npcs || []) {
        if (n.cond && !n.cond()) continue;
        st.add(new Actor(n.cid, n.x, n.y, n));
      }
      // 跟着换地图的人（同伴）：放在玩家身后
      (o.carry || []).forEach((a, i) => {
        a.script = null; a.state = 'idle'; a.z = 0; a.vx = 0; a.remove = false; a.hold = false;
        if (p) { a.x = p.x - (p.facing || 1) * (28 + i * 20); a.y = G.clamp(p.y - 6, st.yMin, st.yMax); }
        a.facing = p ? p.facing : a.facing;
        a.play(a.idleAnim);
        st.add(a);
      });
      this.focus = null;
      this.snapCamera();
      return st;
    },
    enemies() { return this.stage ? this.stage.actors.filter((a) => a.team === 'enemy' && !a.dead && !a.remove) : []; },
    allies() { return this.stage ? this.stage.actors.filter((a) => a.team === 'ally' && !a.remove) : []; },
    tokens() { return this.enemies().filter((e) => e.state === 'windup' || e.state === 'attack' || e.state === 'charge').length; },

    move(a, dx, dy, free) {
      const st = this.stage;
      let nx = a.x + dx;
      let ny = G.clamp(a.y + dy, st.yMin, st.yMax);
      if (!free) {
        const [lo, hi] = st.bounds();
        if (a.x >= lo && a.x <= hi) nx = G.clamp(nx, lo, hi);
        else if (a.x < lo) nx = Math.max(nx, a.x);
        else nx = Math.min(nx, a.x);
      }
      for (const ob of st.obstacles) {
        if (nx > ob.x0 && nx < ob.x1 && ny > ob.y0 && ny < ob.y1) {
          const wasX = a.x > ob.x0 && a.x < ob.x1, wasY = a.y > ob.y0 && a.y < ob.y1;
          if (!wasX) nx = a.x; else if (!wasY) ny = a.y; else { nx = a.x; ny = a.y; }
        }
      }
      a.x = nx; a.y = ny;
    },

    // ---------------- 出招
    startAttack(a, spec, combo = -1) {
      a.state = 'attack'; a.stateT = 0; a.atk = spec; a.combo = combo; a.buffer = false;
      a.hitList.clear();
      a.fired = new Set();
      const anim = a.atlas.has(spec.anim) ? spec.anim : 'attack';
      a.play(anim, { restart: true, speed: spec.fps / a.atlas.anim(anim).fps });
      if (a.team === 'player') a.x += a.facing * 2;
      if (!spec.fire) G.audio.sfx('whoosh', 0.3, G.rand(1.0, 1.2));
    },
    updateAttack(a) {
      const spec = a.atk;
      const f = a.frameIndex();
      if (f >= spec.active[0] && f <= spec.active[1]) this.hitCheck(a, spec);
      if (spec.fire) for (const ff of spec.fire) if (f >= ff && !a.fired.has(ff)) { a.fired.add(ff); this.shoot(a, spec.shot); }
      if (a.team === 'player' && G.input.hit('attack')) a.buffer = true;
      if (a.animDone() || a.stateT > 1.4) {
        if (a.team === 'player' && a.buffer && a.combo >= 0 && a.combo < COMBO.length - 1 && this.free) this.startAttack(a, COMBO[a.combo + 1], a.combo + 1);
        else {
          a.state = 'idle'; a.atk = null;
          if (a.team === 'enemy') a.cool = a.boss ? G.rand(0.7, 1.2) : G.rand(1.0, 1.9);
        }
      }
    },
    hitCheck(att, spec) {
      const sc = att.scale || 1, s0 = side(att);
      for (const t of this.stage.actors) {
        if (t === att || t.remove || t.dead || t.team === 'npc' || side(t) === s0) continue;
        if (att.hitList.has(t) || t.invuln > 0 || t.state === 'down') continue;
        const dx = (t.x - att.x) * att.facing;
        if (dx < spec.reach[0] * sc - 3 || dx > spec.reach[1] * sc + 3) continue;
        if (Math.abs(t.y - att.y) > 8 * Math.max(sc, t.scale)) continue;
        if (Math.abs(t.z - att.z) > 26) continue;
        att.hitList.add(t);
        this.hit(att, t, spec);
      }
    },
    hit(att, t, spec) {
      const cx = (att.x + t.x) / 2, cy = t.y - t.z - 16 * t.scale;
      const guarding = t.state === 'guard' && G.sign(att.x - t.x) === t.facing;
      if (guarding) {
        G.audio.sfx('clang', 0.8, G.rand(0.95, 1.1));
        G.fx.spark(cx, cy, '#cfe8ff', 5);
        t.vx = att.facing * 70;
        G.hitStop = 0.04;
        return;
      }
      const mul = t.dmgMul ? t.dmgMul(t) : 1;          // 伤害倍率（凤仙：在阳光里才打得动）
      if (mul <= 0.01) {
        G.audio.sfx('clang', 0.6, 0.8);
        G.fx.spark(cx, cy, '#d8d0ff', 4);
        if (Math.random() < 0.4) G.fx.text('……没用', t.x, t.y - 50 * t.scale, { vy: -12, life: 0.7, color: '#d8d0ff' });
        G.hitStop = 0.03;
        return;
      }
      t.hp -= Math.max(1, Math.round(spec.dmg * mul));
      if (t.minHp && t.hp < t.minHp) t.hp = t.minHp;   // 剧情要留一口气的（讨债头目要留给阿妙收拾）
      t.flash = 1;
      if (t.team === 'player') t.invuln = 0.55;
      else if (t.team === 'ally') t.invuln = 0.4;
      G.hitStop = spec.heavy ? 0.09 : 0.05;
      G.shake(spec.heavy ? 3 : 1.5, 0.15);
      G.audio.sfx(spec.sfx || 'hit', 0.8, G.rand(0.95, 1.08));
      G.audio.sfx(t.team === 'player' ? 'punch' : 'hit', 0.55, G.rand(0.9, 1.1));
      G.fx.spark(cx, cy, '#fff4c0', 7);
      if (spec.word || Math.random() < 0.15) G.fx.word(G.pick(['砰!', '咚!', '唰!']), cx, cy - 12);
      if (t.hp <= 0) { t.hp = 0; this.ko(t, att); return; }
      t.state = 'hurt'; t.stateT = 0; t.atk = null;
      t.play('hit', { restart: true, speed: 2.4 });
      t.vx = att.facing * spec.kb;
      t.facing = -att.facing;
      if (t.team === 'enemy') t.cool = Math.max(t.cool, 0.5);
    },
    ko(t, att) {
      if (t.team === 'enemy') {
        t.dead = true; t.state = 'dead'; t.stateT = 0; t.koFly = null;
        t.play('fly');
        t.vx = att.facing * (t.boss ? 90 : 130);
        t.vz = t.boss ? 170 : 240;
        G.audio.sfx('fly_away', 0.8);
        if (t.boss) { G.hitStop = 0.3; G.shake(4, 0.5); G.flash(0.3, 0.8); G.fx.word('咔嚓!', t.x, t.y - 40); }
        if (t.koImpact) {   // 原片的冲击帧 + 集中线（第二章打飞猪头那一下）
          G.impactT = 3 / 60;
          G.fx.speedLines(Math.round(t.x - this.stage.camX), Math.round(t.y - 20), { count: 44, inner: 60, life: 0.5 });
          G.fx.word('砰!!', t.x + 30 * att.facing, t.y - 56);
          G.audio.sfx('impact', 0.7);
          G.audio.sfx('punch_big', 1.0);
        }
      } else {
        t.state = 'down'; t.stateT = 0;
        t.play('hit', { restart: true, speed: 1.6 });
        t.vx = att.facing * 90;
        G.audio.sfx('thud', 0.8);
      }
    },

    // ---------------- 飞行道具
    // shot = { kind: 'bullet' | 'rocket' | 'kunai' | 'img', speed, dmg, kb, explode（爆炸半径）, image, life, arc（抛物线初速）, spread }
    shoot(a, shot, o = {}) {
      const dir = o.dir || a.facing;
      const sc = a.scale || 1;
      const s = Object.assign({ t: 0, life: 2.4, side: side(a) }, shot, {
        x: a.x + dir * 14 * sc, y: a.y, z: (o.z != null ? o.z : 18) * sc, vx: dir * (shot.speed || 200), vz: shot.arc || 0,
        dir, owner: a,
      });
      if (shot.spread) s.y += G.rand(-shot.spread, shot.spread);
      this.shots.push(s);
      if (s.kind === 'bullet') { G.audio.sfx('gunshot', 0.35, G.rand(0.95, 1.15)); G.fx.spark(s.x, s.y - s.z, '#fff6a0', 3); }
      else if (s.kind === 'rocket') G.audio.sfx('bazooka', 0.7);
      else G.audio.sfx('whoosh', 0.35, 1.4);
      return s;
    },
    explode(s) {
      const r = s.explode;
      G.audio.sfx('explosion', 0.9);
      G.shake(4, 0.35);
      G.fx.debris(s.x, s.y - Math.max(4, s.z), ['#ffd040', '#ff8a2a', '#ff4a20', '#584848'], 22, [40, 150], 120, 0.7);
      G.fx.dust(s.x, s.y, 12);
      G.fx.word('轰!', s.x, s.y - 30, 0.8);
      for (const t of this.stage.actors) {
        if (t.remove || t.dead || t.team === 'npc' || side(t) === s.side || t.invuln > 0 || t.state === 'down') continue;
        if (Math.abs(t.x - s.x) < r && Math.abs(t.y - s.y) < r * 0.5) {
          this.hit({ x: s.x - s.dir * 6, facing: G.sign(t.x - s.x) || s.dir, team: s.side, scale: 1 }, t, { dmg: s.dmg, kb: s.kb, sfx: 'explosion_small', heavy: true });
          if (!t.dead) { t.tint = { color: 'rgb(40,32,30)', k: 0.6 }; t.sootT = 1.4; }   // 炸得一脸黑
        }
      }
    },
    updateShots(dt) {
      if (!this.shots.length) return;
      for (const s of this.shots) {
        s.t += dt;
        s.x += s.vx * dt;
        if (s.vz || s.arc) { s.z += s.vz * dt; s.vz -= 420 * dt; }
        if (s.kind === 'rocket' && Math.floor(s.t * 30) % 2 === 0) G.fx.add({ kind: 'puff', x: s.x - s.dir * 8, y: s.y - s.z, vx: 0, vy: -6, r: 2, life: 0.35, color: '200,200,200' });
        let done = s.t > s.life || s.x < this.stage.camX - 60 || s.x > this.stage.camX + G.W + 60;
        if (!done && s.arc && s.z <= 0) { if (s.explode) this.explode(s); done = true; }   // 扔出去的炸弹：落地就炸
        if (!done) {
          for (const t of this.stage.actors) {
            if (t.remove || t.dead || t.team === 'npc' || side(t) === s.side || t.state === 'down') continue;
            if (Math.abs(t.x - s.x) > 8 * t.scale || Math.abs(t.y - s.y) > 7 * t.scale) continue;
            if (Math.abs(t.z + 16 * t.scale - s.z) > 18 * t.scale) continue;   // 跳起来就躲过去了
            if (t.invuln > 0) continue;
            const guarding = t.state === 'guard' && G.sign(s.x - t.x) === t.facing;
            if (guarding) {
              G.audio.sfx('clang', 0.7, G.rand(1.1, 1.3)); G.fx.spark(s.x, s.y - s.z, '#cfe8ff', 4);
              if (s.explode) this.explode(s);
            } else if (s.explode) this.explode(s);
            else this.hit({ x: s.x - s.dir * 6, facing: s.dir, team: s.side, scale: 1 }, t, { dmg: s.dmg, kb: s.kb, sfx: 'hit' });
            done = true;
            break;
          }
        }
        s.dead = done;
      }
      this.shots = this.shots.filter((s) => !s.dead);
    },
    drawShot(g, s, camX, camY) {
      const x = Math.round(s.x - camX), y = Math.round(s.y - camY - s.z);
      switch (s.kind) {
        case 'bullet': g.fillStyle = '#fff6a0'; g.fillRect(x - 2, y, 4, 1); g.fillStyle = 'rgba(255,220,120,0.5)'; g.fillRect(x - 2 - s.dir * 4, y, 4, 1); break;
        case 'kunai': g.fillStyle = '#c8ccd8'; g.fillRect(x - 3, y, 6, 1); g.fillStyle = '#383040'; g.fillRect(x - 3 - s.dir * 2, y, 2, 1); break;
        case 'rocket':
        case 'img': {
          const im = s.image && G.image(s.image);
          if (im && G.ready(im)) {
            g.save(); g.translate(x, y); if (s.dir < 0) g.scale(-1, 1);
            g.drawImage(im, -Math.floor(im.width / 2), -Math.floor(im.height / 2)); g.restore();
          } else { g.fillStyle = '#585c68'; g.fillRect(x - 5, y - 1, 10, 3); g.fillStyle = '#ff9a2a'; g.fillRect(x - 5 - s.dir * 3, y, 3, 1); }
          break;
        }
        default: break;
      }
    },

    // ---------------- 玩家
    updatePlayer(p, dt) {
      const I = G.input;
      const can = this.free;
      const axis = () => {
        let mx = 0, my = 0;
        if (can) {
          if (I.isDown('left')) mx -= 1;
          if (I.isDown('right')) mx += 1;
          if (I.isDown('up')) my -= 1;
          if (I.isDown('down')) my += 1;
        }
        return [mx, my];
      };
      switch (p.state) {
        case 'idle':
        case 'walk': {
          if (p.hold) break;
          const [mx, my] = axis();
          if (p.runner) {   // 自动卷轴：镜头自己往前走，左右键只是在画面里前后挪
            p.rx = G.clamp((p.rx == null ? 120 : p.rx) + mx * p.speed * 0.8 * dt, 40, 280);
            p.x = this.stage.camX + p.rx;
            p.facing = 1;
            this.move(p, 0, my * p.speed * 0.7 * dt, true);
            p.play(p.ride ? (p.rideAnim || 'sit') : 'run');
            if (can && I.hit('jump')) { p.state = 'jump'; p.vz = 165; p.air = false; p.play('jump'); G.audio.sfx('jump', 0.5); }
            break;
          }
          if (mx || my) {
            p.state = 'walk';
            if (mx) p.facing = mx;
            const k = mx && my ? 0.8 : 1;
            this.move(p, mx * p.speed * k * dt, my * p.speed * 0.62 * k * dt);
            p.play('walk');
          } else { p.state = 'idle'; p.play(p.idleAnim); }
          if (!can) break;
          if (this.combat && I.hit('attack')) this.startAttack(p, COMBO[0], 0);
          else if (I.hit('jump')) { p.state = 'jump'; p.vz = this.combat ? 175 : 150; p.air = false; p.play('jump'); G.audio.sfx('jump', 0.5); }
          else if (this.combat && I.isDown('guard')) { p.state = 'guard'; p.play('guard'); }
          break;
        }
        case 'attack': this.updateAttack(p); break;
        case 'jump': {
          const [mx, my] = axis();
          if (p.runner) {
            p.rx = G.clamp((p.rx == null ? 120 : p.rx) + mx * p.speed * 0.8 * dt, 40, 280);
            p.x = this.stage.camX + p.rx;
            this.move(p, 0, my * p.speed * 0.4 * dt, true);
          } else {
            if (mx) p.facing = mx;
            this.move(p, mx * p.speed * dt, my * p.speed * 0.5 * dt);
          }
          p.z += p.vz * dt;
          p.vz -= 560 * dt;
          if (can && this.combat && I.hit('attack') && !p.air) {
            p.air = true; p.atk = AIR; p.hitList.clear();
            p.play('attack', { restart: true, speed: AIR.fps / p.atlas.anim('attack').fps });
            G.audio.sfx('whoosh', 0.35, 1.2);
          }
          if (p.air) { const f = p.frameIndex(); if (f >= AIR.active[0] && f <= AIR.active[1]) this.hitCheck(p, AIR); }
          if (p.z <= 0) {
            p.z = 0; p.vz = 0; p.state = 'idle'; p.air = false; p.atk = null;
            G.fx.dust(p.x, p.y, 4);
            G.audio.sfx('land', 0.45);
          }
          break;
        }
        case 'guard':
          if (!can || !I.isDown('guard')) { p.state = 'idle'; break; }
          p.play('guard');
          if (I.hit('left')) p.facing = -1;
          if (I.hit('right')) p.facing = 1;
          this.move(p, p.vx * dt, 0); p.vx *= Math.pow(0.002, dt);
          break;
        case 'hurt':
          this.move(p, p.vx * dt, 0);
          p.vx *= Math.pow(0.002, dt);
          if (p.stateT > 0.3) p.state = 'idle';
          break;
        case 'down':
          this.move(p, p.vx * dt, 0);
          p.vx *= Math.pow(0.002, dt);
          if (p.animDone() && p.anim === 'hit') p.play('lie');
          break;
        default: break;
      }
    },

    // ---------------- 同伴：平时跟在身后走，战斗里自己找敌人打；被打倒过一会儿自己爬起来（不会死）
    updateFollow(a, dt) {
      const f = a.follow;
      if (!f || f.remove || a.hold) {
        if (a.state === 'walk') { a.state = 'idle'; a.play(a.idleAnim); }
        return;
      }
      const behind = f.facing || 1;
      const tx = f.x - behind * 28, ty = G.clamp(f.y - 6, this.stage.yMin, this.stage.yMax);
      const dx = tx - a.x, dy = ty - a.y, d = Math.hypot(dx, dy);
      if (Math.abs(f.x - a.x) > 220) { a.x = tx; a.y = ty; return; }   // 被甩太远（换地图、过场）直接跟上
      if (d > (a.state === 'walk' ? 3 : 16)) {
        const step = Math.min(d, Math.min(f.speed * 1.15, Math.max(30, d * 2.4)) * dt);
        a.x += (dx / d) * step; a.y += (dy / d) * step;
        if (Math.abs(dx) > 1) a.facing = dx > 0 ? 1 : -1;
        a.state = 'walk'; a.play('walk');
      } else {
        if (a.state === 'walk') { a.state = 'idle'; a.play(a.idleAnim); }
        if (Math.abs(f.x - a.x) > 3) a.facing = f.x > a.x ? 1 : -1;
      }
    },
    updateAlly(a, dt) {
      if (!this.combat) { if (a.state === 'attack') a.state = 'idle'; this.updateFollow(a, dt); return; }
      if (a.vip) {   // 护送目标（将军）：不出手，挨打缩一下；倒下就算输
        if (a.state === 'hurt') { this.move(a, a.vx * dt, 0); a.vx *= Math.pow(0.002, dt); if (a.stateT > 0.35) a.state = 'idle'; return; }
        if (a.state === 'down') { if (a.animDone() && a.anim === 'hit') a.play('lie'); return; }
        a.play(a.vipAnim || 'shock');
        return;
      }
      switch (a.state) {
        case 'down':
          this.move(a, a.vx * dt, 0);
          a.vx *= Math.pow(0.002, dt);
          if (a.animDone() && a.anim === 'hit') a.play('lie');
          if (a.stateT > 2.2) {
            a.state = 'idle'; a.hp = Math.max(1, Math.round(a.maxHp * 0.6)); a.invuln = 1.0;
            a.play(a.idleAnim); G.fx.dust(a.x, a.y, 5); G.audio.sfx('land', 0.4);
            a.emote = { text: '!', t: 0.5 };
          }
          return;
        case 'hurt':
          this.move(a, a.vx * dt, 0);
          a.vx *= Math.pow(0.002, dt);
          if (a.stateT > 0.35) a.state = 'idle';
          return;
        case 'attack': this.updateAttack(a); return;
        default: break;
      }
      a.cool -= dt;
      const es = this.enemies();
      if (!es.length) { a.play(a.idleAnim); return; }
      let tg = a.focus;
      a.focusT -= dt;
      if (!tg || tg.dead || tg.remove || tg.team !== 'enemy' || a.focusT <= 0) {
        tg = a.focus = es.reduce((b, e) => (Math.abs(e.x - a.x) + Math.abs(e.y - a.y) < Math.abs(b.x - a.x) + Math.abs(b.y - a.y) ? e : b));
        a.focusT = G.rand(1.5, 3);
      }
      const sideX = a.x < tg.x ? -1 : 1;
      const keep = a.ranged || 22;                 // 远程的同伴（神乐的雨伞机枪）站开一点打
      const dx = tg.x + sideX * keep * tg.scale - a.x, dy = tg.y - a.y;
      const dist = Math.hypot(dx, dy * 1.6);
      a.facing = tg.x > a.x ? 1 : -1;
      if (dist > 4) {
        this.move(a, (dx / dist) * (a.allySpeed || 58) * dt, ((dy * 1.6) / dist) * (a.allySpeed || 58) * 0.6 * dt);
        a.state = 'walk'; a.play('walk');
      } else { a.state = 'idle'; a.play(a.idleAnim); }
      const reach = a.ranged ? a.ranged + 50 : 32;
      if (a.cool <= 0 && Math.abs(tg.x - a.x) < reach * tg.scale && Math.abs(tg.y - a.y) < (a.ranged ? 9 : 7)) {
        a.cool = a.ranged ? G.rand(1.4, 2.0) : G.rand(0.9, 1.5);
        this.startAttack(a, G.pick(a.allyMoves || [A_SLASH, A_UP]));
      }
    },

    // ---------------- 敌人
    // 盯谁打：Boss 只盯玩家；小兵有时去打同伴（同伴倒地就换回玩家）
    pickTarget(e, dt) {
      const p = this.player;
      if (e.boss) return p;
      const f = e.focus;
      e.focusT -= dt;
      const ok = f && !f.remove && (f === p || (f.team === 'ally' && f.state !== 'down'));
      if (ok && e.focusT > 0) return f;
      const al = this.allies().filter((a) => a.state !== 'down');
      const vip = al.find((a) => a.vip);
      e.focus = vip && Math.random() < 0.45 ? vip : al.length && Math.random() < 0.4 ? G.pick(al) : p;
      e.focusT = G.rand(2.5, 4.5);
      return e.focus;
    },
    updateEnemy(e, dt) {
      const p = this.player;
      switch (e.state) {
        case 'dead':
          if (e.koTo) {   // 剧情指定的落点（打穿墙）：抛物线飞过去，落点上执行 onKo
            const K = e.koFly || (e.koFly = { x0: e.x, y0: e.y, z0: e.z, s0: e.scale, t: 0 });
            K.t += dt;
            const k = Math.min(1, K.t / (e.koTo.dur || 0.42));
            const ke = k * 0.65 + k * k * k * 0.35;
            e.x = G.lerp(K.x0, e.koTo.x, ke); e.y = G.lerp(K.y0, e.koTo.y, ke);
            e.z = G.lerp(K.z0, e.koTo.z, ke) + 4 * (e.koTo.arc || 26) * ke * (1 - ke);
            e.scale = G.lerp(K.s0, K.s0 * 0.85, ke);
            e.play('fly');
            if (k >= 1) { e.remove = true; if (e.onKo) e.onKo(e); }
            return;
          }
          e.x += e.vx * dt; e.z += e.vz * dt;
          if (e.y - e.z - this.stage.camY < -30 || e.stateT > 2.5) {
            e.remove = true;
            G.fx.star(G.clamp(e.x - this.stage.camX, 12, G.W - 12));
            G.audio.sfx('twinkle', 0.7);
          }
          return;
        case 'hurt':
          this.move(e, e.vx * dt, 0);
          e.vx *= Math.pow(0.003, dt);
          if (e.stateT > 0.36) e.state = 'idle';
          return;
        case 'attack': this.updateAttack(e); return;
        case 'windup':
          e.play('ready');
          if (e.stateT > e.windup) this.startAttack(e, e.nextMove);
          return;
        case 'charge': {
          if (e.stateT < 0.5) { e.play('ready'); e.flash = (Math.floor(e.stateT * 16) % 2) * 0.6; return; }
          e.play('run');
          this.move(e, e.facing * 190 * dt, 0);
          this.hitCheck(e, E_HEAVY);
          const [lo, hi] = this.stage.bounds();
          if (e.stateT > 1.4 || e.x <= lo || e.x >= hi) { e.state = 'idle'; e.cool = 1.2; e.hitList.clear(); }
          return;
        }
        default: break;
      }
      if (!this.combat || !p || p.state === 'down') { e.play(e.idleAnim); return; }
      const tg = this.pickTarget(e, dt);
      e.cool -= dt;
      if (Math.random() < dt * 0.4) e.laneOff = G.rand(-6, 6);
      const sideX = e.x < tg.x ? -1 : 1;
      const sc = e.scale;
      const keep = e.ranged || e.range;          // 远程的敌人（e.ranged = 站开多远）不贴身
      const tx = tg.x + sideX * keep * sc;
      const ty = G.clamp(tg.y + e.laneOff * (e.cool > 0 && !e.ranged ? 1 : 0), this.stage.yMin, this.stage.yMax);
      const dx = tx - e.x, dy = ty - e.y;
      e.facing = tg.x > e.x ? 1 : -1;
      const dist = Math.hypot(dx, dy * 1.6);
      if (dist > 3) {
        const sp = e.speed * (e.cool > 0 && Math.abs(tg.x - e.x) < 60 ? 0.55 : 1);
        this.move(e, (dx / dist) * sp * dt, ((dy * 1.6) / dist) * sp * 0.6 * dt);
        e.play('walk');
      } else e.play(e.idleAnim);
      const inRange = e.ranged
        ? Math.abs(tg.x - e.x) < (e.ranged + 50) * sc && Math.abs(tg.y - e.y) < 9 * sc
        : Math.abs(tg.x - e.x) < (e.range + 9) * sc && Math.abs(tg.y - e.y) < 7 * sc;
      if (e.cool <= 0 && this.tokens() < this.maxTokens) {
        if (e.boss && !e.ranged && !e.noCharge && Math.abs(p.x - e.x) > 70 && Math.abs(p.y - e.y) < 10 && Math.random() < 0.5) {
          e.state = 'charge'; e.stateT = 0; e.emote = { text: '!!', t: 0.5 };
          G.audio.sfx('charge', 0.7);
          return;
        }
        if (inRange) {
          e.state = 'windup'; e.stateT = 0;
          e.windup = e.boss ? 0.5 : G.rand(0.32, 0.5);
          e.nextMove = G.pick(e.moves);
          e.emote = { text: '!', t: e.windup };
        }
      }
    },

    // ---------------- 每帧
    update(dt) {
      const st = this.stage;
      if (!st) return;
      st.t += dt;
      if (st.door < st.doorTarget) st.door = Math.min(st.doorTarget, st.door + dt * 2.4);
      if (st.door > st.doorTarget) st.door = Math.max(st.doorTarget, st.door - dt * 2.4);
      if (this.anims.length) {
        this.anims = this.anims.filter((an) => {
          an.t += dt;
          const k = Math.min(1, an.t / an.dur);
          an.fn(k, dt);
          if (k >= 1) { an.res(); return false; }
          return true;
        });
      }
      if (this.combat) this.fightT += dt;
      if (this.ticks.length) this.ticks = this.ticks.filter((fn) => !fn(dt));
      for (const a of st.actors) {
        a.animT += dt; a.stateT += dt;
        if (a.flash > 0) a.flash = Math.max(0, a.flash - dt * 7);
        if (a.invuln > 0) a.invuln -= dt;
        if (a.sootT > 0) { a.sootT -= dt; if (a.sootT <= 0) a.tint = null; }
        if (a.emote) { a.emote.t -= dt; if (a.emote.t <= 0) a.emote = null; }
        if (a.script) { a.script(dt); continue; }
        if (a === this.player) this.updatePlayer(a, dt);
        else if (a.team === 'ally') this.updateAlly(a, dt);
        else if (a.team === 'enemy') this.updateEnemy(a, dt);
        else if (a.follow) this.updateFollow(a, dt);
      }
      // 敌人之间别叠在一起
      const es = this.enemies();
      for (let i = 0; i < es.length; i++) {
        for (let j = i + 1; j < es.length; j++) {
          const a = es[i], b = es[j];
          if (Math.abs(a.x - b.x) < 12 && Math.abs(a.y - b.y) < 6) {
            const s = a.x < b.x ? -1 : 1;
            a.x += s * 20 * dt; b.x -= s * 20 * dt;
          }
        }
      }
      st.actors = st.actors.filter((a) => !a.remove);
      this.updateShots(dt);
      // 触发区、互动
      const p = this.player;
      this.near = null;
      if (p && this.free && !G.S.busy && !this.combat && p.state !== 'down') {
        for (const tr of st.triggers) {
          if (tr.fired) continue;
          if (tr.cond && !tr.cond()) continue;
          const inX = p.x >= tr.x0 && p.x <= tr.x1;
          const inY = tr.y0 == null || (p.y >= tr.y0 && p.y <= tr.y1);
          if (inX && inY) { if (tr.once !== false) tr.fired = true; G.S.run(tr.run); break; }
        }
        if (!G.S.busy) {
          this.near = this.findNear();
          if (this.near && G.input.hit('ok')) {
            G.input.consumeOk();
            const n = this.near;
            if (n.actor) {
              p.facing = n.actor.x > p.x ? 1 : -1;
              const a = n.actor;
              G.S.run(async (S) => {
                const old = a.facing;
                if (!a.noTurn) a.facing = p.x > a.x ? 1 : -1;
                S.talker = a;
                await a.talk(S, a);
                S.talker = null;
                if (!a.noTurn && !a.remove && !a.follow) a.facing = old;
              });
            } else G.S.run(n.hot.use);
          }
        }
      }
      G.fx.update(dt);
      this.updateCamera(dt);
    },
    findNear() {
      const p = this.player, st = this.stage;
      let best = null, bd = 1e9;
      for (const a of st.actors) {
        if (a === p || !a.talk || a.remove || !a.visible || a.team === 'enemy') continue;
        const dx = Math.abs(a.x - p.x), dy = Math.abs(a.y - p.y);
        if (dx < 26 && dy < a.talkRy && dx + dy * 1.5 < bd) { bd = dx + dy * 1.5; best = { actor: a, label: a.label || a.name, x: a.x, top: a.headY() }; }
      }
      for (const h of st.hotspots) {
        if (h.hidden || (h.cond && !h.cond())) continue;
        const dx = Math.abs(h.x - p.x), dy = Math.abs(h.y - p.y);
        if (dx < (h.r || 18) && dy < (h.ry || 14) && dx + dy * 1.5 < bd) { bd = dx + dy * 1.5; best = { hot: h, label: h.label, x: h.lx == null ? h.x : h.lx, top: h.ly == null ? h.y - 40 : h.ly }; }
      }
      return best;
    },
    snapCamera() { this.updateCamera(1, true); },
    updateCamera(dt, snap) {
      const st = this.stage;
      const f = this.focus || this.player;
      let target = st.camX;
      if (f) target = f.x - G.W / 2 + (f === this.player ? f.facing * 18 : 0);
      if (st.camTarget != null) target = st.camTarget;
      const lo = st.lock ? st.lock.x0 : st.x0;
      const hi = Math.max(lo, (st.lock ? st.lock.x1 : st.x1) - G.W);
      target = G.clamp(target, lo, hi);
      st.camX = snap ? target : st.camX + (target - st.camX) * Math.min(1, dt * 5);
    },

    // ---------------- 画
    // 镜头推近：this.zoom = { k, x, y }（世界坐标的中心点）。先画到缓冲画布，再放大贴上来（原片的 fx.zoom）
    draw(g) {
      const z = this.zoom, st = this.stage;
      if (!st || !z || z.k <= 1.001) { this.drawScene(g); return; }
      const buf = this.zbuf || (this.zbuf = Object.assign(document.createElement('canvas'), { width: G.W, height: G.H }));
      const b = buf.getContext('2d');
      b.imageSmoothingEnabled = false;
      b.clearRect(0, 0, G.W, G.H);
      this.drawScene(b);
      const w = G.W / z.k, h = G.H / z.k;
      const cx = G.clamp(z.x - Math.round(st.camX), w / 2, G.W - w / 2), cy = G.clamp(z.y - st.camY, h / 2, G.H - h / 2);
      g.imageSmoothingEnabled = false;
      g.drawImage(buf, cx - w / 2, cy - h / 2, w, h, 0, 0, G.W, G.H);
    },
    drawScene(g) {
      const st = this.stage;
      if (!st) return;
      let sx = 0, sy = 0;
      if (G.shakeT > 0) { sx = Math.round(G.rand(-1, 1) * G.shakeMag); sy = Math.round(G.rand(-1, 1) * G.shakeMag * 0.6); }
      const camX = Math.round(st.camX) - sx, camY = st.camY - sy;
      const t = st.t;
      if (st.bg) st.bg.draw(g, camX, t, st);
      else if (st.office) {
        const o = st.office;
        const im = st.door > 0.01 ? o.door[Math.round(st.door * (o.door.length - 1))] : o.amb[Math.floor(t * o.amb_fps) % o.amb.length];
        g.drawImage(G.image(im), -sx, -sy);
      }
      // 道具 + 角色按脚点 y 排序
      const items = [];
      for (const p of st.props) if (!p.hidden) items.push({ y: p.depth == null ? p.y : p.depth, prop: p });
      for (const a of st.actors) items.push({ y: a.y + (a.state === 'dead' ? 1000 : 0), actor: a });
      for (const s of this.shots) items.push({ y: s.y + 0.5, shot: s });
      items.sort((a, b) => a.y - b.y);
      for (const it of items) {
        if (it.actor) it.actor.draw(g, camX, camY);
        else if (it.shot) this.drawShot(g, it.shot, camX, camY);
        else drawProp(g, it.prop, camX, camY, t);
      }
      if (st.bg) st.bg.drawFg(g, camX, t, st);
      G.fx.draw(g, camX, camY, false);
      // 头顶：表情、敌人血条、互动提示
      for (const a of st.actors) {
        const hx = Math.round(a.x - camX), hy = Math.round(a.headY() - camY);
        if (a.emote && a.visible) {
          const bounce = Math.round(Math.abs(Math.sin(a.emote.t * 9)) * 2);
          G.f16.draw(g, a.emote.text, hx, hy - 16 - bounce, a.emote.color || '#ffe14a', { align: 'center', outline: '#1a1020' });
        }
        if (a.team === 'enemy' && !a.dead && this.combat && !a.boss) G.bar(g, hx - 10, hy - 5, 20, 2, a.hp / a.maxHp, '#ff5050');
      }
      if (this.near && this.free && !G.S.busy) {
        const n = this.near;
        const bx = Math.round(n.x - camX), by = Math.round(n.top - camY) - 14 - Math.round(Math.abs(Math.sin(G.realTime * 4)) * 2);
        const label = n.label || '';
        const w = G.f12.width(label) + 18;
        G.box(g, bx - (w >> 1), by - 2, w, 15, { fill: 'rgba(14,16,28,0.85)' });
        G.f12.draw(g, '▼', bx - (w >> 1) + 3, by, '#ffd34a');
        G.f12.draw(g, label, bx - (w >> 1) + 15, by, '#fff');
      }
      G.fx.draw(g, 0, 0, true);
    },
  });

  // ---------------------------------------------------------------- 道具
  function drawProp(g, p, camX, camY, t) {
    const x = Math.round(p.x - camX), y = Math.round(p.y - camY);
    switch (p.type) {
      case 'image': {
        const im = G.image(p.image);
        if (p.screen) g.drawImage(im, p.sx || 0, p.sy || 0);
        else g.drawImage(im, x - (p.ax || 0), y - (p.ay || 0));
        break;
      }
      case 'sprite': {   // 剧情里会动的小道具（芭菲、托盘、借条……）：可以转、可以抬高（z）
        const im = G.image(p.image);
        if (!G.ready(im)) break;
        const ax = p.ax != null ? p.ax : im.width / 2, ay = p.ay != null ? p.ay : im.height;
        g.save();
        g.translate(x, Math.round(y - (p.z || 0)));
        if (p.rot) g.rotate(p.rot);
        const sc = p.scale || 1;
        g.scale(p.flip ? -sc : sc, sc);
        if (p.alpha != null) g.globalAlpha = p.alpha;
        g.drawImage(im, -Math.round(ax), -Math.round(ay));
        g.restore();
        break;
      }
      case 'rects': {    // 几个色块拼的小东西（鼻屎、碎片）
        for (const [dx, dy, w, h, c] of p.rects) { g.fillStyle = c; g.fillRect(x + dx, Math.round(y - (p.z || 0)) + dy, w, h); }
        break;
      }
      case 'text': {
        const f = p.size === 16 ? G.f16 : G.f12;
        const bob = p.bob ? Math.round(Math.sin(t * 6) * p.bob) : 0;
        f.draw(g, p.text, x, y + bob, p.color || '#fff', { align: 'center', outline: p.outline || '#140c18' });
        break;
      }
      case 'custom': p.draw(g, x, y, t); break;   // 剧情自己画的东西（灵魂出窍……）
      case 'sign': {     // 举着的牌子（伊丽莎白只用牌子说话）：白底黑字，下面一根竿
        const lines = String(p.text).split('\n');
        const w = Math.max(p.minW || 0, Math.max(...lines.map((l) => G.f12.width(l))) + 8), h = Math.max(p.minH || 0, lines.length * 13 + 5);
        const bx = x - (w >> 1), by = Math.round(y - (p.z || 0)) - h;
        if (p.pole !== false) { g.fillStyle = '#7a5a3a'; g.fillRect(x, by + h, 2, p.pole || 10); }
        g.fillStyle = '#1a1424'; g.fillRect(bx - 1, by - 1, w + 2, h + 2);
        g.fillStyle = '#fbfaf2'; g.fillRect(bx, by, w, h);
        const ty = by + Math.floor((h - lines.length * 13 + 1) / 2);
        lines.forEach((l, i) => G.f12.draw(g, l, x, ty + i * 13, '#1a1424', { align: 'center' }));
        break;
      }
      case 'banner': {
        const b = G.D.bg.war.banners[p.kind || 'joui'];
        const f = Math.floor(t * b.fps + (p.phase || 0)) % b.frames.length;
        g.drawImage(G.image(b.frames[f]), x - b.ax, y - b.ay);
        break;
      }
      case 'campfire': {
        g.fillStyle = 'rgba(255,170,80,0.10)';
        g.beginPath(); g.ellipse(x, y - 4, 26, 9, 0, 0, Math.PI * 2); g.fill();
        g.fillStyle = '#3a2418'; g.fillRect(x - 8, y - 2, 16, 3); g.fillStyle = '#5a3a26'; g.fillRect(x - 6, y - 3, 12, 2);
        for (let i = 0; i < 6; i++) {
          const ph = t * 9 + i * 1.7;
          const h = 5 + Math.round((Math.sin(ph) + 1) * 3) + (i % 3 === 1 ? 4 : 0);
          const fx = x - 5 + i * 2;
          g.fillStyle = i % 2 ? '#ff9a2e' : '#ffcf4a';
          g.fillRect(fx, y - 3 - h, 2, h);
          g.fillStyle = '#ff5a24';
          g.fillRect(fx, y - 3 - Math.round(h * 0.45), 2, Math.round(h * 0.45));
        }
        for (let i = 0; i < 3; i++) {
          const k = (t * 0.7 + i / 3) % 1;
          g.fillStyle = `rgba(255,${200 - k * 120},80,${1 - k})`;
          g.fillRect(x - 2 + Math.round(Math.sin(t * 3 + i * 2) * 4), y - 12 - Math.round(k * 26), 1, 1);
        }
        break;
      }
      default: break;
    }
  }
})();
