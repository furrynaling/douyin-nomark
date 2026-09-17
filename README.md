<h1 align="center">dnmark</h1>

<p align="center"><b>抖音无水印下载器 · 视频 + 图文 · 纯标准库 · 无需登录</b></p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/依赖-零-green" alt="Zero Dependency">
  <img src="https://img.shields.io/badge/平台-Linux%20%7C%20macOS%20%7C%20Termux%20%7C%20Windows-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

> 把抖音分享链接丢进来，直接拿无水印原片（视频 mp4 / 图文全部原图 + 打包 zip）。
> **不需要 cookie、不需要登录、不依赖任何第三方解析站**——直接走抖音官方接口的 `play_addr`（无水印源）。

---

## 目录

- [为什么又造一个轮子](#为什么又造一个轮子)
- [特性](#特性)
- [快速开始](#快速开始)
- [用法](#用法)
- [输出说明](#输出说明)
- [常见问题](#常见问题)
- [它是怎么工作的](#它是怎么工作的)
- [免责声明](#免责声明)

---

## 为什么又造一个轮子

| 现有方案 | 实测问题 |
|:---|:---|
| 在线"抖音去水印"网站 | 2026 年大面积 502/522/超时，大部分已死；还有的偷偷塞广告、要你先看视频 |
| `yt-dlp` | 抖音提取器要求「新鲜 cookie」（`Fresh cookies ... are needed`），喂 ttwid 也不行 |
| 各种批量下载器 | 要装浏览器内核 / 要抓包拿签名 / 要付费会员 |
| **dnmark** | **零依赖、零登录、一条命令**，视频和图文都能扒，还顺手给你拼好预览图 |

## 特性

- 🎬 **视频**：无水印 mp4，自动挑清晰度高的镜像（1080p/720p）
- 🖼 **图文**：多图作品全部原图下载 + 自动打包 `zip` + 生成 4×N 拼图预览（装了 ffmpeg 才有拼图）
- 🪶 **零依赖**：只用 Python 标准库，**连 curl 都不用**，Termux 上 `pkg install python` 就能跑
- 🔓 **无需登录 / 无需 cookie**：自动申请游客态 `ttwid`
- 🤖 **`--json` 输出**：方便接进你自己的脚本、机器人、AI Agent
- 🩺 **`--doctor` 自检**：一键看网络、ttwid、接口是否正常
- 📁 **跨平台路径**：默认存到各平台的下载目录，不硬编码 `/root`

## 快速开始

### 一键安装（Linux / macOS / Termux）

```bash
curl -fsSL https://raw.githubusercontent.com/furrynaling/douyin-nomark/main/install.sh | bash
```

### Windows（PowerShell）

```powershell
irm https://raw.githubusercontent.com/furrynaling/douyin-nomark/main/install.ps1 | iex
```

### 手动安装

```bash
git clone https://github.com/furrynaling/douyin-nomark.git
cp douyin-nomark/scripts/dnmark.py ~/.local/bin/dnmark
chmod +x ~/.local/bin/dnmark
```

### 依赖要求

**只需要 Python 3.7+**（Windows 10/11 自带 `python` 命令即可，或从 python.org 装）。
`ffmpeg` 可选——只有"图文拼图预览"用它，没装也不影响下载。

## 用法

```bash
# 最简单：把抖音分享的整段文本（不用删广告词）粘进去
dnmark "0.05 复制打开抖音，看看【XXX的作品】… https://v.douyin.com/xxxxxx/"

# 指定保存目录
dnmark -o ~/Videos "https://v.douyin.com/xxxxxx/"

# 机器可读输出（做机器人/自动化用）
dnmark --json "https://v.douyin.com/xxxxxx/"

# 图文不要 zip / 不要拼图
dnmark --no-zip --no-sheet "https://v.douyin.com/xxxxxx/"

# 自检
dnmark --doctor
dnmark -v
```

## 输出说明

```
视频：
  视频：2.01 MB  720p
    文件： ~/Downloads/douyin-nomark/作者-标题.mp4

图文：
  图文作品：共 34 张，成功 34 张
    目录： ~/Downloads/douyin-nomark/作者-标题/
    打包： ~/Downloads/douyin-nomark/作者-标题.zip
    拼图： ~/Downloads/douyin-nomark/作者-标题/_sheet_01.jpg
```

**怎么确认是无水印的**：脚本只取 `video.play_addr` / `play_addr_h264` / `play_addr_265` / `bit_rate[].play_addr`，
这些 URL 里**没有** `watermark=1`，也**没有** `logo_name=`；
带水印的 `video.download_addr` 一律不用。图文的 `images[].url_list`（`tplv-dy-aweme-images`）同理，
带水印的 `download_url_list`（`tplv-dy-water`）不碰。

## 常见问题

**Q：会不会哪天突然不能用？**
会。抖音接口大约每年都会改一次签名/字段。`dnmark` 用的接口链路和排查方法都写在
[references/如何维护.md](references/如何维护.md) 里，接口变了照着改十分钟就能修好。

**Q：需要登录吗？要 cookie 吗？**
都不需要。只申请一个游客态 `ttwid`（免费、自动、缓存在 `~/.cache/douyin-nomark/`）。

**Q：提示 ttwid 过期 / 拿不到数据？**
删掉缓存重试即可：`rm -rf ~/.cache/douyin-nomark`。脚本内部也会自动重取一次。

**Q：能批量下整个主页吗？**
本工具只处理**单个作品链接**。批量请在外层用脚本循环调用 `dnmark --json`。

**Q：会不会下载到有水印的版本？**
不会，见上面「输出说明」的判定规则。

## 它是怎么工作的

```
分享短链 v.douyin.com/xxxx  →  跟随 302 拿到 aweme_id
        ↓
申请游客态 ttwid（POST ttwid.bytedance.com/ttwid/union/register/）
        ↓
官方接口 /aweme/v1/web/aweme/detail/?aweme_id=… （带 UA + Referer + ttwid）
        ↓
视频 → video.play_addr[*].url_list      （无水印）
图文 → images[*].url_list               （无水印）
```

细节、字段对照表、接口变更时的排查步骤：[references/如何维护.md](references/如何维护.md)

## 免责声明

本工具仅供**个人学习、技术研究与个人内容备份**使用。请勿用于侵犯他人著作权、商业牟利或任何违法用途。
下载内容版权归原作者所有，转载/二次使用请获得作者授权。使用本工具产生的任何后果由使用者自行承担。

## License

[MIT](LICENSE) © 2026 furrynaling
