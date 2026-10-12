// 剧情脚本 API：await S.say(...) / S.walk(...) / S.fight(...) 这样一句句写剧情
'use strict';
(function () {
  const G = window.G;
  G.flags = {};

  const S = (G.S = {
    busy: false,
    get flags() { return G.flags; },

    // 跑一段剧情（同一时间只跑一段；跑的时候玩家不能动，跑完交还操作）
    async run(fn, o = {}) {
      while (this.busy) await G.wait(0.05);
      this.busy = true;
      const W = G.world;
      W.free = false;
      const runId = G.runId;
      try { await fn(this); } catch (e) { console.error(e); }
      if (runId !== G.runId) return;
      this.busy = false;
      if (o.keepLocked !== true && W.stage) W.free = true;
    },

    // ---------------- 小工具
    actor(a) { return typeof a === 'string' ? (a === 'player' ? G.world.player : G.world.stage.find(a)) : a; },
    get player() { return G.world.player; },
    wait: (sec) => G.wait(sec),
    until: (fn) => G.until(fn),
    free(on = true) { G.world.free = on; },
    sfx(name, vol = 1, rate = 1) { G.audio.sfx(name, vol, rate); },
    music(name, fade) { G.audio.music(name, fade); },
    stopMusic(fade) { G.audio.stopMusic(fade); },
    shake(mag = 2, dur = 0.25) { G.shake(mag, dur); },
    flash(dur = 0.25, peak = 1, color) { G.flash(dur, peak, color); },
    impact(frames = 2) { G.impactT = frames / 60; },     // 冲击帧（黑白两色）
    fadeOut(dur = 0.5) { return G.fade(1, dur); },
    fadeIn(dur = 0.5) { return G.fade(0, dur); },
    hint(text, dur) { G.ui.hint(text, dur); },
    nameCard(cid) { G.ui.nameCard(cid); },
    chapterCard(key) { return G.ui.chapterCard(key); },
    notice(o) { return G.ui.showNotice(o); },
    letterbox(on) { G.ui.letterboxTarget = on ? 16 : 0; },
    insert(fn) { G.ui.insert = fn ? { draw: fn, t: 0 } : null; },   // 全屏特写：fn(g, t)，null 关掉
    emote(a, text, dur = 1.0, color) { a = this.actor(a); if (a) a.emote = { text, t: dur, color }; },
    word(word, a, dy = -34) { a = this.actor(a); G.fx.word(word, a.x, a.y - a.z + dy); },
    state(key, val) { const st = G.world.stage; if (st) st.state[key] = val; },   // 地图的画面状态（墙洞、乌鸦……）
    door(open, o = {}) {
      const st = G.world.stage;
      if (!st) return;
      st.doorTarget = open ? 1 : 0;
      if (o.instant) st.door = st.doorTarget;
    },
    camera(x) {   // 数字 = 镜头左边的世界 x；角色 = 跟着它；null = 跟玩家
      const st = G.world.stage;
      if (x == null) { st.camTarget = null; G.world.focus = null; }
      else if (typeof x === 'number') { st.camTarget = x; }
      else { st.camTarget = null; G.world.focus = this.actor(x); }
    },
    face(a, dir) {
      a = this.actor(a);
      if (typeof dir === 'number') a.facing = dir;
      else { const b = this.actor(dir); if (b) a.facing = b.x > a.x ? 1 : -1; }
    },
    spawn(cid, x, y, o = {}) {
      const a = new G.Actor(cid, x, y, o);
      G.world.stage.add(a);
      return a;
    },
    remove(a) { a = this.actor(a); if (a) a.remove = true; },
    // 同伴跟着谁走（null = 不跟了，站着不动）
    follow(a, target = 'player') { a = this.actor(a); if (a) { a.follow = target ? this.actor(target) : null; a.hold = false; } },
    // 剧情里的小道具：{ image, x, y, z, rot, ax, ay, depth } 或 { type: 'rects' | 'text', ... }
    prop(o) {
      const p = Object.assign({ type: 'sprite', x: 0, y: 0, z: 0, rot: 0, alpha: 1, scale: 1 }, o);
      G.world.stage.props.push(p);
      return p;
    },
    unprop(p) { const st = G.world.stage; if (st && p) st.props = st.props.filter((q) => q !== p); },
    // 逐帧动画：fn(k, dt)，k 从 0 走到 1，dur 秒后结束
    animate(dur, fn) { return new Promise((res) => G.world.anims.push({ t: 0, dur: Math.max(1e-4, dur), fn, res })); },
    // 按键小游戏（见 ui.startQte）：连按、看准时机、跟着节拍
    mash(o) { return G.ui.startQte(Object.assign({ type: 'mash', label: '连按 J！', need: 18, time: 4, decay: 2.5 }, o)); },
    timing(o) { return G.ui.startQte(Object.assign({ type: 'timing', label: '看准时机按 J！', speed: 1.1, zone: [0.42, 0.58], tries: 1 }, o)); },
    rhythm(o) { return G.ui.startQte(Object.assign({ type: 'rhythm', label: '跟着节拍按 J！', window: 0.16, travel: 1.6 }, o)); },
    filter(f) { G.screenFilter = f || null; },                  // 整屏滤镜，比如 'sepia(0.85)'
    // 镜头推近 / 拉回：k 倍，对准世界坐标 (x, y)（可以传角色 + dy），dur 秒缓动过去；k = 1 回到正常
    zoom(k, x, y, dur = 0.3) {
      const W = G.world;
      if (x && typeof x === 'object') { const a = this.actor(x); x = a.x; y = a.y - a.z + (y || -24); }
      const z0 = W.zoom || { k: 1, x: x != null ? x : 0, y: y != null ? y : 0 };
      const to = { k, x: x != null ? x : z0.x, y: y != null ? y : z0.y };
      if (dur <= 0) { W.zoom = k > 1.001 ? to : null; return Promise.resolve(); }
      const from = Object.assign({}, z0);
      return this.animate(dur, (u) => {
        const e = u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
        W.zoom = { k: G.lerp(from.k, to.k, e), x: G.lerp(from.x, to.x, e), y: G.lerp(from.y, to.y, e) };
        if (u >= 1 && k <= 1.001) W.zoom = null;
      });
    },
    lightning() { G.flash(0.3, 0.85, '#e4ebff'); G.audio.sfx('thunder', 0.8); },
    // 换主角（第十一章的小银时、第十二章的神乐……）：新角色站到原来主角的位置，原来的主角从地图上拿掉（o.keep 则留下当 NPC）
    setPlayer(cid, o = {}) {
      const W = G.world, old = W.player;
      const p = new G.Actor(cid, o.x != null ? o.x : old ? old.x : 100, o.y != null ? o.y : old ? old.y : 180, {
        id: 'player', team: 'player', hp: o.hp || 100, speed: o.speed || 72, facing: o.facing || (old ? old.facing : 1),
        name: o.name || (G.NAMES && G.NAMES[cid]) || G.D.chars[cid].name,
      });
      if (old && W.stage) {
        if (o.keep) { old.id = o.keep; old.team = 'npc'; old.hold = false; old.state = 'idle'; }
        else old.remove = true;
      }
      if (W.stage) W.stage.add(p);
      W.player = p;
      return p;
    },
    // 自动卷轴：镜头自己往前走（camX 每秒 speed 像素，走到 endX 结束），K 跳过障碍，↑↓ 换位置。
    //   obstacles = [{ x, y, w, h（前后判定半宽）, tall（跳多高能躲过）, dmg, prop（画法，同 S.prop） }]
    //   o.ride = 载具（同 Actor.ride）；o.onTick(dt, t) 每帧回调（放炮弹之类）；输了从头再来
    async runner(o) {
      const W = G.world, st = W.stage, p = W.player;
      const cam0 = o.cam0 != null ? o.cam0 : st.camX;
      for (let attempt = 0; ; attempt++) {
        const obs = (o.obstacles || []).map((ob) => Object.assign({ done: false }, ob));
        const props = obs.map((ob) => (ob.prop ? this.prop(Object.assign({ x: ob.x, y: ob.y }, ob.prop)) : null));
        st.camX = cam0; st.camTarget = cam0; W.focus = null;
        p.runner = true; p.rx = o.rx || 110; p.x = cam0 + p.rx; p.y = o.y || p.y; p.z = 0; p.state = 'idle'; p.hold = false;
        p.hp = p.maxHp; p.invuln = 0; p.ride = o.ride || null;
        G.ui.hud = true;
        if (attempt > 0) await G.fade(0, 0.4);
        W.free = true;
        let t = 0, lost = false, finished = false;
        const tick = (dt) => {
          t += dt;
          st.camTarget = Math.min(o.endX, st.camTarget + (o.speed || 90) * dt);
          if (st.camTarget >= o.endX && st.camX >= o.endX - 2) { finished = true; return true; }
          if (o.onTick) o.onTick(dt, t, obs);
          if (p.hp <= 0) { p.hp = 0; lost = true; return true; }      // onTick 里自己算的伤害（炮弹之类）
          for (const ob of obs) {
            if (ob.done || p.invuln > 0) continue;
            if (Math.abs(p.x - ob.x) < (ob.w || 16) / 2 + 5 && Math.abs(p.y - ob.y) < (ob.h || 8) && p.z < (ob.tall || 16)) {
              ob.done = !ob.solid;
              p.hp -= ob.dmg || 15; p.invuln = 1.0; p.flash = 1;
              G.shake(3, 0.25); G.audio.sfx(ob.sfx || 'thud', 0.9); G.fx.word(ob.word || '咚!', p.x, p.y - 40);
              G.fx.dust(p.x, p.y, 6);
              if (p.hp <= 0) { p.hp = 0; lost = true; return true; }
            }
          }
          return false;
        };
        W.ticks.push(tick);
        W.runner = { obs };     // 给自动测试看的（障碍还剩哪些）
        await G.until(() => lost || finished);
        W.runner = null;
        W.free = false;
        props.forEach((pr) => pr && this.unprop(pr));
        if (finished) break;
        p.state = 'down'; p.play('hit', { restart: true });
        await G.wait(1.0);
        const r = await G.ui.openMenu(`${p.name}倒下了……`, ['再来一次', '回到标题'], { note: '输了就从这一段重新开始' });
        if (r === 1) { G.goTitle(); return new Promise(() => {}); }
        await G.fade(1, 0.3);
      }
      p.runner = false; p.rx = null;
      st.camTarget = null;
      G.ui.hud = false;
      p.hp = p.maxHp;
    },

    // ---------------- 说话
    async say(who, text, o = {}) {
      const st = G.world.stage;
      const tk = this.talker;
      const a = o.actor ? this.actor(o.actor)
        : st && (st.find(who === G.world.player?.cid ? 'player' : who) || (tk && who && tk.cid.split('__')[0] === who ? tk : null));
      const speaker = a || (who === (G.world.player && G.world.player.cid) ? G.world.player : null);
      let talked = false;
      if (speaker && !speaker.hold && !speaker.script && speaker.atlas.has('talk') && speaker.state !== 'attack' && speaker.state !== 'walk') {
        speaker.play('talk'); talked = true;
        if (speaker === G.world.player) speaker.hold = true;
      }
      await G.ui.say(who, text, o);
      if (talked && !speaker.remove) {
        if (speaker.anim === 'talk') speaker.play(speaker.idleAnim);
        if (speaker === G.world.player) speaker.hold = false;
      }
    },
    narrate(text, o) { return G.ui.narrate(text, o); },
    choice(options, title) { return G.ui.choice(options, title); },

    // ---------------- 动作
    walk(a, x, y, o = {}) {
      a = this.actor(a);
      return new Promise((res) => {
        const speed = o.speed || Math.min(a.speed, 64);
        const ty = y == null ? a.y : y;
        a.hold = false;
        a.state = 'idle';
        a.script = (dt) => {
          const dx = x - a.x, dy = ty - a.y, d = Math.hypot(dx, dy);
          if (d < 1) {
            a.x = x; a.y = ty; a.script = null; a.state = 'idle';
            a.play(o.endAnim || a.idleAnim);
            if (o.face) a.facing = o.face;
            res();
            return;
          }
          const step = Math.min(d, speed * dt);
          a.x += (dx / d) * step; a.y += (dy / d) * step;
          if (Math.abs(dx) > 0.5 && !o.backward) a.facing = dx > 0 ? 1 : -1;
          a.play(o.anim || 'walk', { speed: o.animSpeed || 1 });
        };
      });
    },
    // 抛物线（被踢飞、跳下来）
    arc(a, x, y, height, dur, o = {}) {
      a = this.actor(a);
      return new Promise((res) => {
        const x0 = a.x, y0 = a.y, z0 = a.z, z1 = o.z1 || 0;
        let t = 0;
        a.hold = true;
        a.script = (dt) => {
          t += dt;
          const k = Math.min(1, t / dur);
          a.x = G.lerp(x0, x, k); a.y = G.lerp(y0, y, k);
          a.z = G.lerp(z0, z1, k) + 4 * height * k * (1 - k);
          a.play(o.anim || 'fly');
          if (k >= 1) { a.script = null; res(); }
        };
      });
    },
    // 摆姿势：o.freeze = 定格在第几帧；o.y / o.x 顺便挪位置
    pose(a, anim, o = {}) {
      a = this.actor(a); a.hold = true; a.state = 'idle';
      a.play(anim, { restart: o.restart, speed: o.speed });
      if (o.freeze != null) a.frozen = o.freeze;
      if (o.y != null) a.y = o.y;
      if (o.x != null) a.x = o.x;
    },
    unpose(a, o = {}) {
      a = this.actor(a); a.hold = false; a.state = 'idle'; a.frozen = null; a.rot = 0;
      if (o.y != null) a.y = o.y;
      if (o.x != null) a.x = o.x;
      a.play(a.idleAnim);
    },
    async act(a, anim, o = {}) {
      a = this.actor(a);
      a.hold = true;
      a.play(anim, { restart: true, speed: o.speed || 1 });
      await G.until(() => a.animDone() || a.remove);
      if (!o.keep) { a.hold = false; a.play(a.idleAnim); }
    },
    // 换地图。o.carry = 跟着一起过去的人（id 或角色），放在玩家身后
    async setStage(id, o = {}) {
      const def = typeof id === 'string' ? G.STAGES[id] : id;
      const carry = (o.carry || []).map((c) => this.actor(c)).filter(Boolean);
      if (o.fade !== false) await G.fade(1, 0.35);
      G.world.zoom = null;
      G.world.setStage(def, { player: G.world.player, x: o.x, y: o.y, carry });
      if (o.facing) { G.world.player.facing = o.facing; carry.forEach((c) => { c.facing = o.facing; c.x = G.world.player.x - o.facing * 28; }); }
      if (def.music && o.music !== false) G.audio.music(def.music);
      if (o.fade !== false) await G.fade(0, 0.4);
    },

    // ---------------- 战斗：一波波打；输了弹“再来一次”，从这场战斗重新开始
    //   spec.allies  = 一起打的同伴（id），战斗时变成 'ally'，打完变回普通 NPC（照样跟着走）
    //   spec.endWhen = 剧情喊停的条件（比如头目血量见底，换阿妙出场收拾），成立就算赢
    //   敌人可选：minHp（打不死，留一口气）、koTo / onKo（被打飞的落点和落地后的剧情，比如打穿墙）
    //   spec.vip     = 要护送的人（id）：不出手，敌人会去打他，他倒下也算输
    //   spec.events  = [{ when: (t) => 条件（t = 这场打了几秒）, run: async (S) => 剧情 }]：中途停下来演一段再接着打
    //   spec.timer   = { label: '天亮还有 ', until: 秒 }：右上角倒计时（配合 endWhen 用）
    //   spec.reinforce = { every: 秒, max: 同时最多几个, make: (i) => 敌人写法 }：打的过程中不断有人从两边冲进来
    async fight(spec) {
      const W = G.world, st = W.stage, p = W.player;
      const prevMusic = G.audio.name;
      st.lock = { x0: spec.arena[0], x1: spec.arena[1] };
      st.camTarget = null; W.focus = null;
      if (spec.music !== null) G.audio.music(spec.music || 'battle', 0.5);
      G.ui.hud = true;
      const startX = G.clamp(p.x, spec.arena[0] + 40, spec.arena[1] - 40), startY = p.y;
      const allies = (spec.allies || []).map((id) => this.actor(id)).filter(Boolean);
      for (const a of allies) { a.team = 'ally'; a.script = null; a.hold = false; a.focus = null; a.maxHp = spec.allyHp || a.maxHp || 60; }
      const vip = spec.vip ? this.actor(spec.vip) : null;
      const vipPos = vip ? [vip.x, vip.y] : null;
      if (vip) Object.assign(vip, { team: 'ally', vip: true, script: null, hold: false, maxHp: spec.vipHp || 80 });
      const evs = (spec.events || []).map((e) => Object.assign({}, e));
      let ended = false;
      for (let attempt = 0; ; attempt++) {
        p.hp = p.maxHp; p.state = 'idle'; p.hold = false; p.invuln = 0; p.z = 0; p.vz = 0; p.script = null;
        for (const a of allies) {
          a.hp = a.maxHp; a.state = 'idle'; a.invuln = 0; a.z = 0; a.vx = 0; a.cool = 0.6; a.play(a.idleAnim);
          if (attempt > 0) { a.x = G.clamp(startX - 30, spec.arena[0] + 12, spec.arena[1] - 12); a.y = startY; }
        }
        if (vip) { vip.hp = vip.maxHp; vip.state = 'idle'; vip.invuln = 0; vip.x = vipPos[0]; vip.y = vipPos[1]; }
        evs.forEach((e) => { e.fired = false; });
        W.fightT = 0;
        if (spec.timer) G.ui.timer = Object.assign({}, spec.timer);
        if (attempt > 0) { p.x = startX; p.y = startY; p.facing = 1; W.snapCamera(); await G.fade(0, 0.4); }
        let lost = false;
        // 增援：每隔几秒从场地边上冲进来一个
        let rf = null;
        if (spec.reinforce) {
          let acc = 0, n = 0;
          rf = (dt) => {
            if (!W.combat) return false;
            acc += dt;
            if (acc < spec.reinforce.every || W.enemies().length >= spec.reinforce.max) return false;
            acc = 0;
            const e = spec.reinforce.make(n++);
            if (!e) return false;
            const left = n % 2 === 0;
            const x = left ? spec.arena[0] - 16 : spec.arena[1] + 16, y = G.rand(st.yMin + 4, st.yMax - 4);
            const a = new G.Actor(e.cid, x, y, { id: e.id || `rf${n}`, name: e.name, facing: left ? 1 : -1 });
            Object.assign(a, {
              team: 'enemy', maxHp: e.hp || 24, hp: e.hp || 24, scale: e.scale || 1, speed: e.speed || 50, range: e.range || 25,
              ranged: e.ranged || 0, moves: (e.moves || ['E_SLASH']).map((m) => G.MOVES[m]), cool: 1.0, idleAnim: 'idle',
            });
            st.add(a);
            a.x += left ? 22 : -22;
            return false;
          };
          const myRf = rf;
          W.ticks.push((dt) => (rf !== myRf ? true : rf(dt)));
        }
        for (let wi = 0; wi < spec.waves.length && !lost && !ended; wi++) {
          const wave = spec.waves[wi];
          const spawned = [];
          const walkIns = [];
          const [ax0, ax1] = spec.arena;
          wave.forEach((e, i) => {
            let a = e.actor ? this.actor(e.actor) : null;
            if (a && attempt > 0 && a.team === 'enemy') a = null;   // 重来时原地的那批已经被打飞了，重新生成
            const sideK = e.side || (i % 2 === 1 ? 'left' : 'right'), k = spawned.length;
            const x = sideK === 'left' ? ax0 - 20 - k * 14 : ax1 + 20 + k * 14;
            const y = e.y != null ? e.y : G.rand(st.yMin + 4, st.yMax - 4);
            if (!a && e._obj && attempt > 0) {
              // 剧情指定的那个人（e.actor）：重来时还用原来那个角色对象，打完以后的剧情里拿着的引用才不会落空
              a = e._obj;
              Object.assign(a, { remove: false, dead: false, x, y, z: 0, vx: 0, vz: 0, alpha: 1, visible: true, facing: sideK === 'left' ? 1 : -1 });
              if (!st.actors.includes(a)) st.add(a);
              walkIns.push([a, sideK === 'left' ? ax0 + 34 + k * 16 : ax1 - 34 - k * 16, y]);
            }
            if (!a) {
              // 新来的敌人从场地边缘外走进来
              a = new G.Actor(e.cid, x, y, { id: e.id || e.actor, name: e.name, facing: sideK === 'left' ? 1 : -1 });
              st.add(a);
              walkIns.push([a, sideK === 'left' ? ax0 + 34 + k * 16 : ax1 - 34 - k * 16, y]);
            }
            if (e.actor && attempt === 0) e._obj = a;
            Object.assign(a, {
              team: 'enemy', maxHp: e.hp || 30, hp: e.hp || 30, name: e.name || a.name, scale: e.scale || 1, boss: !!e.boss,
              speed: e.speed || 46, range: e.range || 25, moves: (e.moves || ['E_SLASH']).map((m) => G.MOVES[m]),
              state: 'idle', hold: false, script: null, dead: false, cool: G.rand(0.8, 1.6), idleAnim: e.idle || 'idle',
              frozen: null, rot: 0, tint: null, follow: null, focus: null, focusT: 0, ranged: e.ranged || 0, noCharge: !!e.noCharge,
              minHp: e.minHp || 0, koTo: e.koTo || null, onKo: e.onKo || null, koFly: null, koImpact: !!e.koImpact,
              dmgMul: e.dmgMul || null,
            });
            a.play(a.idleAnim);
            spawned.push(a);
            if (e.boss) G.ui.boss = a;
          });
          W.combat = false; W.free = false;
          if (walkIns.length) await Promise.all(walkIns.map(([a, x, y]) => this.walk(a, x, y, { speed: 80 })));
          for (const a of spawned) a.facing = p.x > a.x ? 1 : -1;
          if (spec.onWave) await spec.onWave(this, wi, spawned, attempt);
          W.combat = true; W.free = true;
          const down = () => p.state === 'down' || (vip && vip.state === 'down');
          for (;;) {
            let ev = null;
            await G.until(() => {
              if (W.enemies().length === 0 && !spec.survive) return true;
              if (down() || (spec.endWhen && spec.endWhen())) return true;
              ev = evs.find((e) => !e.fired && e.when(W.fightT));
              return !!ev;
            });
            if (!ev) break;
            // 剧情事件：停手、演一段、接着打
            ev.fired = true;
            W.combat = false; W.free = false;
            for (const e of W.enemies()) if (e.state !== 'hurt') { e.state = 'idle'; e.play(e.idleAnim); e.emote = null; }
            if (p.state !== 'jump') { p.state = 'idle'; p.play(p.idleAnim); }
            await ev.run(this, W.enemies(), attempt);
            W.combat = true; W.free = true;
          }
          if (down()) lost = true;
          else if (spec.endWhen && spec.endWhen()) ended = true;
        }
        rf = null;
        G.ui.timer = null;
        if (!lost) break;
        if (vip && vip.state === 'down' && p.state !== 'down') { p.state = 'down'; p.play('hit', { restart: true }); }
        W.free = false;
        await G.wait(1.3);
        W.combat = false;
        G.ui.boss = null;
        for (const e of st.actors) if (e.team === 'enemy') e.remove = true;
        W.shots = [];
        const who = vip && vip.state === 'down' ? vip.name : p.name;
        const r = await G.ui.openMenu(`${who}倒下了……`, ['再来一次', '回到标题'], { note: '输了就从这场战斗重新开始' });
        if (r === 1) { G.goTitle(); return new Promise(() => {}); }
        await G.fade(1, 0.3);
      }
      if (ended) {
        // 剧情喊停：马上收手，剩下的敌人站着不动，交给后面的剧情
        W.combat = false; W.free = false;
        for (const e of W.enemies()) { if (e.state !== 'hurt') e.state = 'idle'; e.play('idle'); e.emote = null; }
        if (p.state !== 'hurt' && p.state !== 'jump') { p.state = 'idle'; p.play(p.idleAnim); }
        await G.wait(0.4);
      } else await G.wait(1.0);
      W.combat = false; W.free = false;
      W.shots = [];
      st.lock = null;
      G.ui.hud = false; G.ui.boss = null; G.ui.timer = null;
      G.ui.hints = [];        // 打之前的提示别留到后面的剧情里（有对话时提示会跳到上面）
      p.hp = p.maxHp;
      if (p.state === 'attack' || p.state === 'guard') { p.state = 'idle'; p.play(p.idleAnim); }
      for (const a of allies) {
        a.team = 'npc'; a.hp = a.maxHp; a.focus = null; a.invuln = 0;
        if (a.state === 'down' || a.state === 'attack' || a.state === 'hurt') { a.state = 'idle'; a.play(a.idleAnim); }
      }
      if (vip) { vip.team = 'npc'; vip.vip = false; vip.hp = vip.maxHp; if (vip.state !== 'idle') { vip.state = 'idle'; vip.play(vip.idleAnim); } }
      if (spec.after !== null) G.audio.music(spec.after || prevMusic || 'yorozuya', 1.0);
    },

    // ---------------- 过场视频（原片 s00 那两段）
    video(name) {
      return new Promise((res) => {
        const v = G.D.video && G.D.video[name];
        if (!v) { res(); return; }
        const el = document.createElement('video');
        el.src = v.webm && el.canPlayType('video/webm; codecs="vp9, opus"') ? v.webm : v.src;
        el.playsInline = true;
        el.preload = 'auto';
        const prev = G.scene, prevFade = G.fadeAlpha;
        let done = false;
        const finish = () => {
          if (done) return;
          done = true;
          el.pause();
          G.fadeAlpha = prevFade;
          G.setScene(prev);
          res();
        };
        const scene = {
          name: 'video',
          t: 0,
          update(dt) {
            this.t += dt;
            if (this.t > 0.6 && (G.input.okHit() || G.input.hit('pause'))) finish();
          },
          draw(g) {
            if (el.readyState >= 2) g.drawImage(el, 0, 0, G.W, G.H);
            if (this.t < 4) G.f12.draw(g, G.touch && G.touch.on ? '点屏幕跳过' : 'Enter 跳过', G.W - 6, G.H - 15, 'rgba(255,255,255,0.55)', { align: 'right' });
          },
        };
        el.addEventListener('ended', finish, { once: true });
        el.addEventListener('error', finish, { once: true });
        G.audio.stopMusic(0.3);
        G.fadeAlpha = 0;   // 前面淡出留下的黑幕会整个盖住视频（序章结尾那段原来只有声音、画面全黑），放完再还原
        G.setScene(scene);
        el.play().catch(() => { el.muted = true; el.play().catch(finish); });
      });
    },
  });
})();
