# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-09-17

### 新增
- 抖音**视频**无水印下载：自动在 `play_addr` / `play_addr_h264` / `play_addr_265` / `bit_rate` 多个镜像里挑清晰度最高的（优先 ≥720p）
- 抖音**图文**下载：全部原图 + 自动打包 `zip` + 生成 4×N 拼图预览（检测到 ffmpeg 时）
- **零依赖**实现：只用 Python 标准库（`urllib` / `hashlib` / `zipfile`），不需要 curl
- **游客态 ttwid 自动申请**并缓存，无需登录、无需 cookie、无需第三方解析站
- `--doctor` 自检：Python 版本、ffmpeg、ttwid、详情接口连通性
- `--json` 机器可读输出，方便接入脚本 / 机器人 / AI Agent
- 跨平台：Linux / macOS / Termux / Windows，默认输出目录走各平台下载目录，不硬编码路径
- 一键安装：`install.sh`（Linux/macOS/Termux）、`install.ps1`（Windows）
- `references/如何维护.md`：完整接口链路、字段对照表、失效排查步骤、自测清单
