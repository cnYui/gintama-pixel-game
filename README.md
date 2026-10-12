# 银魂 像素剧场 · 游戏版（独立项目目录）

2026-10-08 从 `D:\大疆\游戏素材\银魂\` 复制出来的独立目录，放在 `D:\CodeWorkSpace\` 下，目录结构保持和原来一样，所以构建脚本（`游戏\tools\build_assets.py`）不用改路径就能用。原目录没有动。

```text
gintama-pixel-game\
  游戏\          网页 2D 剧情打斗游戏（序章到终章 15 章，含手机 / 平板触屏版）——入口 游戏\index.html，说明 游戏\README.md
  源码\          原视频工程（Python，build_assets 导出资源时要用）
  角色图集\      角色图集（build_assets 的 chars 步骤要用）
  音频\          原工程的音乐 / 音效（build_assets 的 audio 步骤要用，324 MB）
  剧情分镜\      原片逐场景的分镜（设计参考）
  烘焙脚本\      角色图集的烘焙脚本
  README_素材库说明.md   原素材库根目录的说明
```

## 常用命令（在 `游戏\` 里）

```text
双击 index.html                                  电脑上玩
双击 手机试玩.bat                                 手机玩：开局域网小服务器，手机同一 Wi-Fi 打开印出来的网址
python tools\touchtest.py                        触屏自测（模拟手机横屏，58 项）
python tools\playtest.py prologue                键盘自动试玩（all / chN 通关测试）
python tools\build_assets.py font data           改了中文字符串后重建字库和 data.js
```

## 没复制过来的

- `录屏素材\`（约 10 GB 的实况录像、宣传片、长视频素材）：属于视频制作，留在 `D:\大疆\游戏素材\银魂\录屏素材\`。
- `会话备份\`（249 MB 的原会话导出）：留在原处。
- 游戏里 `tools\record_all.py` / `join_chunks.py` / `make_clips.py` 这些录屏转 mp4 的脚本也带过来了，但录出来的东西要自己指定输出目录（别写回这里）。

## 注意

- 这是**复制**，不是移动：两边各一份，以后在这里改的不会同步回 `D:\大疆`，反过来也一样。
- 角色是《银魂》同人形象（原作：空知英秋），标题曲是商业歌曲的翻弹，只适合本机自用；公开发布（放到网上）前要先解决授权。

## GitHub 仓库（公开）里没有的东西

仓库是公开的，下面这些只在本机，由 `.gitignore` 排除：

- 所有音频 / 视频（`音频\`、`游戏\assets\audio\`、`游戏\assets\video\`、`_tmp_audio_test\`）：含标题曲（商业歌曲翻弹）。克隆下来的游戏没有声音和开场动画，需要自己补文件。
- 原片画面类的参考图：`游戏\docs\章节素材调研\`、`剧情分镜\分镜图\`。
- 服务器部署细节：`小红书小工具\mac-setup\`、`deploy_mac.sh`、`docs\ai\context\20261008-银魂公网部署.md`。
- 构建产物和打包文件（`dist*`、`*.zip`、`_tmp`、`_skill` 等）。

仓库里的角色图集是《银魂》同人像素形象（原作：空知英秋），没有授予任何许可。
