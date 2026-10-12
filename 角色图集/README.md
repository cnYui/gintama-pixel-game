# 银魂 角色图集（游戏用精灵图集）

48 个目录（42 个角色 + 路人 6 种配色），13124 帧，约 9 MB。`总览.png` 是全员合影，`catalog.json` 是索引。**双击 `查看器.html`** 可以浏览所有角色和动作（选角色、选动作、朝左、放大、显示格子和脚点；勾“全部动作”一眼看完一个角色的全部动作；数据内嵌，不用起服务器，要和角色目录放在一起）。每个角色一个目录：

```text
<id>\
  <id>.png        图集：每行一个动作，帧在行内从左到右紧挨着；透明背景；朝右；原始像素（没放大）
  <id>.json       元数据
  头像\*.png       表情头像（normal / angry / shout / smug …）和对话头像（portrait_*），原始像素
  <id>_预览.png    给人看的：2 倍放大、棋盘格底、每行标动作名和帧数
```

## `<id>.json`

```jsonc
{
  "id": "gintoki", "name": "银时", "work": "银魂",
  "image": "gintoki.png",
  "cell": [53, 50],        // 每一格的宽高（全角色所有帧里以脚点为基准的最大外接范围 + 四周 1 px）
  "pivot": [19, 40],       // 脚点在格内的坐标（距格左上角）。游戏里把它对准角色脚下的地面点
  "facing": "right",       // 图是朝右画的；向左用水平镜像
  "animations": {
    "walk":  {"row": 1, "frames": 15, "fps": 12, "kind": "loop", "seamless": "approx", "loop_error_px": 4.2},
    "attack": {"row": 12, "frames": 8, "fps": 12, "kind": "oneshot"},
    "guard": {"row": 16, "frames": 1, "fps": 12, "kind": "static"}
  },
  "aliases": {"battle_idle": "idle"},   // 这些动作和另一个动作的帧完全相同，没重复存
  "expressions": ["normal", "angry", "..."],
  "variants": {}, "source": {...}, "notes": "..."
}
```

- 帧 `i` 在图集里的位置：`x = i * cell[0]`，`y = row * cell[1]`，大小 `cell`。
- **kind**：`loop` 循环播放；`oneshot` 播一遍停在最后一帧（出拳、挥刀、受击、落地……）；`static` 一帧。
- **seamless**：`true` = 首尾像素完全衔接；`"approx"` = 差一点点相位（`loop_error_px` 是首尾平均差异的像素数，一般肉眼看不出）；`false` = 没找到周期，截了 12 帧。
- 一次性动作的 8 帧是动作进度 0 → 1 均匀采样；`xxx_loop` 是该动作的循环版（定春、伊丽莎白这类自定义角色才有，如 `attack_loop`）。
- 眨眼没烘焙进循环里（取帧时跳过了眨眼窗口）；要眨眼就在游戏里切 `头像` 或自己叠。

## 怎么用

**HTML canvas（10 行）**

```js
const meta = await (await fetch('gintoki/gintoki.json')).json();
const img = new Image(); img.src = 'gintoki/' + meta.image; await img.decode();
function draw(ctx, anim, t, x, y, flip = false, scale = 4) {      // t = 动作开始后的秒数
  const a = meta.animations[anim], [cw, ch] = meta.cell, [px, py] = meta.pivot;
  const n = Math.floor(t * a.fps);
  const f = a.kind === 'loop' ? n % a.frames : Math.min(n, a.frames - 1);
  ctx.imageSmoothingEnabled = false;
  ctx.save(); ctx.translate(x, y); ctx.scale(flip ? -scale : scale, scale);
  ctx.drawImage(img, f * cw, a.row * ch, cw, ch, -px, -py, cw, ch);
  ctx.restore();
}
```

**Phaser**：`this.load.spritesheet(id, png, {frameWidth: cw, frameHeight: ch})`，每个动作用 `this.anims.create({key, frames: generateFrameNumbers(id, {start: row * maxFrames, end: row * maxFrames + frames - 1}), frameRate: fps, repeat: loop ? -1 : 0})`（`maxFrames` = 图集宽 ÷ `cell[0]`；原点设成 `pivot / cell`）。

**Godot / Unity**：按 `cell` 切格，一行 = 一个动画，帧率取 `fps`，轴心取 `pivot`。放大请用最近邻（关闭平滑），整数倍。

## 说明

- 原工程画布 384×216，放大 5 倍到 1080p；所以游戏里的角色约 34 px 高（小孩 26 px，定春、凤仙约 50 px），放大 4–5 倍最还原。
- 定春、伊丽莎白是自定义渲染器（非人形骨架），只支持自己的几个动作，其余标准动作名在 `aliases` 里退到相近动作（如定春的 `bite` 就是 `attack`）。
- 伊丽莎白的 `sign` 动作牌子上是默认的“……”；牌子上的字是运行时参数 `sign="文字"`，要别的字得回源码里渲染（`render_sprite('elizabeth', 'sign', sign='快跑')`）。
- 重新烘焙：`python ..\烘焙脚本\bake_characters.py`（全部），或带角色 id（如 `gintoki townsman@2`）。
