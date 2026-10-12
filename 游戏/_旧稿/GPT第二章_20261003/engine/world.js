// 世界：地图（场景）、角色、玩家操作、敌人 AI、战斗判定、镜头、互动与触发区
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
  G.MOVES = { COMBO, AIR, E_SLASH, E_PUNCH, E_HEAVY };

  // ---------------------------------------------------------------- 角色
  class Actor {
    constructor(cid, x, y, o = {}) {
      this.cid = cid;
      this.atlas = G.atlas(cid);
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
      this.state = 'idle'; this.stateT = 0;
      this.speed = o.speed || 72;
      this.flash = 0; this.alpha = 1; this.visible = o.visible !== false; this.shadow = o.shadow !== false;
      this.talk = o.talk || null;
      this.label = o.label || null;
      this.emote = null;
      this.hitList = new Set();
      this.invuln = 0; this.cool = G.rand(0.6, 1.4); this.laneOff = G.rand(-5, 5); this.range = o.range || 25;
      this.boss = !!o.boss; this.moves = o.moves || [E_SLASH]; this.dead = false; this.remove = false;
      this.hold = false;   // 剧情里摆好的姿势，不被自动切回 idle
      this.rot = 0;
    }
    play(name, o = {}) {
      if (this.anim !== name || o.restart) { this.anim = name; this.animT = 0; }
      this.animSpeed = o.speed || 1;
    }
    get a() { return this.atlas.anim(this.anim); }
    frameIndex() {
      const a = this.a;
      const n = Math.floor(this.animT * a.fps * this.animSpeed + 1e-6);
      return a.kind === 'loop' ? n % a.frames : Math.min(n, a.frames - 1);
    }
    animDone() { const a = this.a; return a.kind !== 'loop' && this.animT * a.fps * this.animSpeed >= a.frames; }
    headY() { return this.y - this.z - (this.atlas.py - 4) * this.scale; }
    draw(g, camX, camY) {
      if (!this.visible) return;
      const sx = Math.round(this.x - camX), sy = Math.round(this.y - camY);
      if (this.shadow && this.alpha > 0.3 && this.state !== 'dead') {
        const sw = Math.round(12 * this.scale);
        g.fillStyle = 'rgba(0,0,0,0.25)';
        g.fillRect(sx - (sw >> 1), sy - 1, sw, 2);
      }
      const blink = this.invuln > 0 && this.team === 'player' && Math.floor(G.time * 20) % 2 === 0;
      this.atlas.draw(g, this.anim, this.frameIndex(), sx, sy - Math.round(this.z), {
        flip: this.facing < 0, scale: this.scale, alpha: blink ? 0.45 : this.alpha, flash: this.flash, rot: this.rot,
      });
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

    setStage(def, o = {}) {
      const st = new Stage(def);
      this.stage = st;
      G.fx.clear();
      if (o.player) {
        const p = o.player;
        p.x = o.x == null ? p.x : o.x;
        p.y = o.y == null ? p.y : o.y;
        p.z = 0; p.vx = 0; p.state = 'idle';
        st.add(p);
      }
      for (const n of def.npcs || []) {
        if (n.cond && !n.cond()) continue;
        st.add(new Actor(n.cid, n.x, n.y, n));
      }
      this.focus = null;
      this.snapCamera();
      return st;
    },
    enemies() { return this.stage ? this.stage.actors.filter((a) => a.team === 'enemy' && !a.dead && !a.remove) : []; },
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
      a.play(spec.anim, { restart: true, speed: spec.fps / a.atlas.anim(spec.anim).fps });
      if (a.team === 'player') a.x += a.facing * 2;
      G.audio.sfx('whoosh', 0.3, G.rand(1.0, 1.2));
    },
    updateAttack(a) {
      const spec = a.atk;
      const f = a.frameIndex();
      if (f >= spec.active[0] && f <= spec.active[1]) this.hitCheck(a, spec);
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
      const sc = att.scale || 1;
      for (const t of this.stage.actors) {
        if (t === att || t.remove || t.dead || t.team === 'npc' || t.team === att.team) continue;
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
      t.hp -= spec.dmg;
      t.flash = 1;
      if (t.team === 'player' || t.team === 'ally') t.invuln = 0.55;
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
        t.dead = true; t.state = 'dead'; t.stateT = 0;
        t.play('fly');
        t.vx = att.facing * (t.boss ? 90 : 130);
        t.vz = t.boss ? 170 : 240;
        G.audio.sfx('fly_away', 0.8);
        if (t.boss) { G.hitStop = 0.3; G.shake(4, 0.5); G.flash(0.3, 0.8); G.fx.word('咔嚓!', t.x, t.y - 40); }
      } else {
        t.state = 'down'; t.stateT = 0;
        t.play('hit', { restart: true, speed: 1.6 });
        t.vx = att.facing * 90;
        G.audio.sfx('thud', 0.8);
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
          if (mx) p.facing = mx;
          this.move(p, mx * p.speed * dt, my * p.speed * 0.5 * dt);
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

    updateAlly(a, dt) {
      const p = this.player;
      if (a.state === 'down') {
        if (a.stateT > 1.2) { a.state = 'idle'; a.hp = a.maxHp; a.play(a.idleAnim); }
        return;
      }
      if (a.state === 'hurt') { this.move(a, a.vx * dt, 0); a.vx *= Math.pow(0.002, dt); if (a.stateT > 0.3) a.state = 'idle'; return; }
      if (a.state === 'attack') { this.updateAttack(a); return; }
      const target = this.enemies().sort((x, y) => Math.abs(x.x - a.x) - Math.abs(y.x - a.x))[0];
      if (!target) { a.play(a.idleAnim); return; }
      const dx = target.x - a.x, dy = target.y - a.y;
      a.facing = dx >= 0 ? 1 : -1;
      if (Math.abs(dy) > 7 || Math.abs(dx) > 34) {
        const d = Math.max(1, Math.hypot(dx, dy)); this.move(a, dx / d * 46 * dt, dy / d * 36 * dt); a.play('walk');
      } else if (a.cool <= 0) {
        a.cool = 1.0; this.startAttack(a, { anim: 'attack', fps: 18, active: [2, 4], dmg: 5, reach: [1, 28], kb: 26, sfx: 'slash' });
      } else { a.cool -= dt; a.play(a.idleAnim); }
      if (a.hp <= 0) { a.hp = 1; a.state = 'down'; a.stateT = 0; a.play('hit', { restart: true }); }
      if (p && Math.abs(a.x - p.x) > 150) { a.x = p.x - p.facing * 48; a.y = p.y + 4; }
    },

    // ---------------- 敌人
    updateEnemy(e, dt) {
      const p = this.player;
      switch (e.state) {
        case 'dead':
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
      e.cool -= dt;
      if (Math.random() < dt * 0.4) e.laneOff = G.rand(-6, 6);
      const side = e.x < p.x ? -1 : 1;
      const sc = e.scale;
      const tx = p.x + side * e.range * sc;
      const ty = G.clamp(p.y + e.laneOff * (e.cool > 0 ? 1 : 0), this.stage.yMin, this.stage.yMax);
      const dx = tx - e.x, dy = ty - e.y;
      e.facing = p.x > e.x ? 1 : -1;
      const dist = Math.hypot(dx, dy * 1.6);
      if (dist > 3) {
        const sp = e.speed * (e.cool > 0 && Math.abs(p.x - e.x) < 60 ? 0.55 : 1);
        this.move(e, (dx / dist) * sp * dt, ((dy * 1.6) / dist) * sp * 0.6 * dt);
        e.play('walk');
      } else e.play(e.idleAnim);
      const inRange = Math.abs(p.x - e.x) < (e.range + 9) * sc && Math.abs(p.y - e.y) < 7 * sc;
      if (e.cool <= 0 && this.tokens() < this.maxTokens) {
        if (e.boss && Math.abs(p.x - e.x) > 70 && Math.abs(p.y - e.y) < 10 && Math.random() < 0.5) {
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
      if (st.office) {
        if (st.door < st.doorTarget) st.door = Math.min(st.doorTarget, st.door + dt * 2.4);
        if (st.door > st.doorTarget) st.door = Math.max(st.doorTarget, st.door - dt * 2.4);
      }
      for (const a of st.actors) {
        a.animT += dt; a.stateT += dt;
        if (a.flash > 0) a.flash = Math.max(0, a.flash - dt * 7);
        if (a.invuln > 0) a.invuln -= dt;
        if (a.emote) { a.emote.t -= dt; if (a.emote.t <= 0) a.emote = null; }
        if (a.script) { a.script(dt); continue; }
        if (a === this.player) this.updatePlayer(a, dt);
        else if (a.team === 'ally') this.updateAlly(a, dt);
        else if (a.team === 'enemy') this.updateEnemy(a, dt);
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
                if (!a.noTurn && !a.remove) a.facing = old;
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
        if (dx < 26 && dy < 14 && dx + dy * 1.5 < bd) { bd = dx + dy * 1.5; best = { actor: a, label: a.label || a.name, x: a.x, top: a.headY() }; }
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
    draw(g) {
      const st = this.stage;
      if (!st) return;
      let sx = 0, sy = 0;
      if (G.shakeT > 0) { sx = Math.round(G.rand(-1, 1) * G.shakeMag); sy = Math.round(G.rand(-1, 1) * G.shakeMag * 0.6); }
      const camX = Math.round(st.camX) - sx, camY = st.camY - sy;
      const t = st.t;
      if (st.bg) st.bg.draw(g, camX, t);
      else if (st.office) {
        const o = st.office;
        const im = st.door > 0.01 ? o.door[Math.round(st.door * (o.door.length - 1))] : o.amb[Math.floor(t * o.amb_fps) % o.amb.length];
        g.drawImage(G.image(im), -sx, -sy);
      }
      // 道具 + 角色按脚点 y 排序
      const items = [];
      for (const p of st.props) if (!p.hidden) items.push({ y: p.depth == null ? p.y : p.depth, prop: p });
      for (const a of st.actors) items.push({ y: a.y + (a.state === 'dead' ? 1000 : 0), actor: a });
      items.sort((a, b) => a.y - b.y);
      for (const it of items) {
        if (it.actor) it.actor.draw(g, camX, camY);
        else drawProp(g, it.prop, camX, camY, t);
      }
      if (st.bg) st.bg.drawFg(g, camX, t);
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
