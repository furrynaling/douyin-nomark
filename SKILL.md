---
name: dnmark-douyin-download
description: 用 dnmark 下载抖音无水印视频/图文（个人内容备份用）。当用户发来 v.douyin.com 分享链接、要求"去水印/下载抖音视频/保存图文"时使用。支持视频 mp4、图文原图+zip+拼图预览、--json 机器可读输出。零依赖、无需登录。
metadata:
  version: "1.0.0"
  homepage: https://github.com/furrynaling/douyin-nomark
---

# 抖音无水印下载（dnmark）

## 何时用

- 用户消息里出现 `v.douyin.com/xxxx` 分享链接
- 用户说「把这个视频下载下来」「去水印」「保存这条图文」

## 安装

```bash
curl -fsSL https://raw.githubusercontent.com/furrynaling/douyin-nomark/main/install.sh | bash
```

## 用

```bash
# 视频 / 图文（自动判断类型）
dnmark "0.05 复制打开抖音… https://v.douyin.com/xxxxxx/"

# 机器可读（做机器人/自动化时用这个）
dnmark --json "<链接>"

# 自检排错
dnmark --doctor
```

## 输出

- 视频 → `<作者>-<标题>.mp4`（默认 `~/Downloads/douyin-nomark/`）
- 图文 → 目录（`01.jpg`…）+ 同名 `.zip` + `_sheet_01.jpg` 拼图预览（需 ffmpeg）
- 默认目录可用 `-o` 改；缓存（ttwid）在 `~/.cache/douyin-nomark/`

## 接进 Agent 工作流

拿到 `--json` 里的 `path` / `sheets` 之后，可以继续做内容分析：

1. **视频**：`ffmpeg -i x.mp4 -vf fps=1/2,scale=640:-1 /tmp/f/v_%02d.png` 抽帧
2. **图文**：直接用工具生成的 `_sheet_*.jpg`（4×N 拼图，格序左→右、上→下）
3. 把帧图/拼图交给视觉模型描述内容
4. **文字用 OCR 更准**：`tesseract 01.jpg - -l chi_sim+eng --psm 6`

## 注意

- 仅支持**单个作品链接**；批量请在外层循环调用
- 接口偶发变更时的排查：见 `references/如何维护.md`
- 版权：下载内容版权归原作者，仅个人备份/学习用，别商用、别二次发布
- 抖音接口需要带 `Referer` + ttwid，`yt-dlp` 那条路是走不通的（会报 Fresh cookies needed）
