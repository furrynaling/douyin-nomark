#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dnmark —— 抖音无水印下载器（视频 / 图文）
零依赖：只用 Python 标准库（urllib / hashlib / zipfile），不需要 curl、不需要浏览器 cookie、不需要登录。

    dnmark "<粘贴的分享文本或链接>"
    dnmark --doctor        # 自检：网络、ttwid、接口是否正常
    dnmark -v              # 版本

原理见 references/如何维护.md：短链 → aweme_id → 游客态 ttwid → 官方 detail 接口 → play_addr(无水印源)
"""

import argparse
import json
import os
import platform
import re
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile

VERSION = "1.0.0"
NAME = "dnmark"
AUTHOR = "furrynaling"
HOMEPAGE = "https://github.com/furrynaling/douyin-nomark"

UA_DESKTOP = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
UA_MOBILE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
             "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
TTWID_URL = "https://ttwid.bytedance.com/ttwid/union/register/"
TTWID_BODY = (b'{"region":"cn","aid":1768,"needFid":false,"service":"www.ixigua.com",'
              b'"migrate_info":{"ticket":"","source":"node"},"cbUrlProtocol":"https","union":true}')


# ---------------------------------------------------------------- paths
def _home():
    return os.path.expanduser("~")


def default_out_dir():
    """跨平台默认目录：Linux/macOS/Termux → ~/Downloads/douyin-nomark，Windows → 用户下载目录"""
    if platform.system() == "Windows":
        base = os.path.join(os.environ.get("USERPROFILE", _home()), "Downloads")
    else:
        base = os.path.join(_home(), "Downloads")
    return os.path.join(base, "douyin-nomark")


def cache_dir():
    if platform.system() == "Windows":
        base = os.environ.get("LOCALAPPDATA", _home())
    else:
        base = os.path.join(_home(), ".cache")
    d = os.path.join(base, "douyin-nomark")
    os.makedirs(d, exist_ok=True)
    return d


# ---------------------------------------------------------------- http
def http(url, headers=None, data=None, timeout=30, binary=False, max_bytes=None):
    h = {"User-Agent": UA_DESKTOP, "Accept-Language": "zh-CN,zh;q=0.9", "Accept-Encoding": "identity"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(max_bytes) if max_bytes else r.read()
        return raw if binary else raw.decode("utf-8", "replace")


def http_download(url, dest, headers=None, timeout=120):
    """流式下载到文件，返回字节数"""
    h = {"User-Agent": UA_DESKTOP, "Referer": "https://www.douyin.com/", "Accept-Encoding": "identity"}
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h)
    n = 0
    with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(262144)
            if not chunk:
                break
            f.write(chunk)
            n += len(chunk)
    return n


def get_ttwid(refresh=False):
    path = os.path.join(cache_dir(), "ttwid")
    if not refresh and os.path.exists(path):
        v = open(path).read().strip()
        if v:
            return v
    req = urllib.request.Request(TTWID_URL, data=TTWID_BODY, method="POST", headers={
        "Content-Type": "application/json", "User-Agent": UA_DESKTOP})
    with urllib.request.urlopen(req, timeout=25) as r:
        # ttwid 在 Set-Cookie 里
        for k, v in r.headers.items():
            if k.lower() == "set-cookie":
                m = re.search(r"ttwid=([^;]+);", v)
                if m:
                    open(path, "w").write(m.group(1))
                    return m.group(1)
    raise RuntimeError("拿不到游客态 ttwid（可能是网络问题）")


# ---------------------------------------------------------------- 解析
def parse_aweme_id(text):
    m = re.search(r"https?://[^\s\u4e00-\u9fff]+", text)
    if not m:
        raise ValueError("没找到链接。请粘贴抖音分享的整段文本或链接。")
    url = m.group(0).rstrip("/").rstrip("。,.，")
    m1 = re.search(r"/(?:video|note|share/video|share/note)/(\d{6,})", url)
    if m1:
        return m1.group(1), ("note" if "note" in url else "video")
    # 短链：跟随 302，拿 location
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA_MOBILE})
        with urllib.request.urlopen(req, timeout=25) as r:
            final = r.geturl()
    except urllib.error.HTTPError as e:
        final = e.headers.get("Location", "")
    except Exception:
        final = ""
    m2 = re.search(r"/(video|note)/(\d{6,})", final) or re.search(r"(\d{15,})", final)
    if m2:
        gid = m2.group(m2.lastindex)
        return gid, ("note" if "note" in final else "video")
    raise ValueError("解析 aweme_id 失败：%s" % url)


def fetch_detail(aweme_id, kind="video"):
    last = None
    for refresh in (False, True):          # ttwid 过期时自动重取一次
        ttwid = get_ttwid(refresh=refresh)
        api = ("https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=%s"
               "&device_platform=webapp&aid=6383&channel=channel_pc_web" % aweme_id)
        try:
            body = http(api, headers={"Referer": "https://www.douyin.com/%s/%s" % (kind, aweme_id),
                                      "Cookie": "ttwid=" + ttwid}, timeout=30)
            det = json.loads(body).get("aweme_detail")
            if det:
                return det
            last = "接口返回空（可能被风控）"
        except Exception as e:              # noqa
            last = "%s: %s" % (type(e).__name__, e)
    raise RuntimeError("拿不到作品数据（%s）。可先跑 `%s --doctor` 自检；接口若已变更请提 issue。" % (last, NAME))


def safe_name(s, limit=60):
    s = re.sub(r'[\\/:*?"<>|\n\r\t]', "", s or "")
    s = re.sub(r"[\U0001F000-\U0001FAFF\u2190-\u21FF\u2600-\u27BF\uFE0F\u200D]", "", s)
    return (re.sub(r"\s+", " ", s).strip()[:limit] or "douyin")


# ---------------------------------------------------------------- 下载
def pick_best_video(det, out_dir, name, want_res=720):
    vid = det.get("video") or {}
    pool = []
    for key in ("play_addr", "play_addr_h264", "play_addr_265"):
        pool += (vid.get(key) or {}).get("url_list") or []
    for br in (vid.get("bit_rate") or []):
        pool += (br.get("play_addr") or {}).get("url_list") or []
    urls = [u for u in dict.fromkeys(pool) if "watermark=1" not in u and "logo_name" not in u]
    if not urls:
        raise RuntimeError("没拿到无水印播放地址")
    path = os.path.join(out_dir, name + ".mp4")
    best = (0, None, "")
    for i, u in enumerate(urls[:8]):
        tmp = os.path.join(cache_dir(), "try_%d.mp4" % i)
        try:
            n = http_download(u, tmp)
        except Exception:
            continue
        res = 0
        if shutil_which("ffprobe"):
            try:
                out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                                      "-show_entries", "stream=height", "-of", "csv=p=0", tmp],
                                     capture_output=True, text=True, timeout=20).stdout.strip()
                res = int(out or 0)
            except Exception:
                res = 0
        if n > best[0]:
            best = (n, tmp, res)
        if res >= want_res:
            break
    if not best[1]:
        raise RuntimeError("所有镜像都下载失败，请稍后重试")
    os.replace(best[1], path)
    return path, best[0], best[2]


def download_images(det, aweme_id, out_dir, name, do_zip=True, do_sheet=True):
    imgs = det.get("images") or []
    folder = os.path.join(out_dir, name)
    os.makedirs(folder, exist_ok=True)
    ok = 0
    for i, it in enumerate(imgs, 1):
        urls = [u for u in (it.get("url_list") or []) if ".jpeg" in u or ".jpg" in u] \
            or (it.get("url_list") or [])
        dst = os.path.join(folder, "%02d.jpg" % i)
        for u in urls:
            try:
                n = http_download(u, dst)
                if n > 10000:
                    ok += 1
                    break
            except Exception:
                continue
    zpath = None
    if do_zip and ok:
        zpath = folder + ".zip"
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(os.listdir(folder)):
                z.write(os.path.join(folder, f), f)
    sheets = []
    if do_sheet and ok and shutil_which("ffmpeg"):
        sheets = make_sheets(folder)
    return folder, zpath, sheets, ok


def make_sheets(folder, per_sheet=12, cols=4, width=560):
    """把图片拼成 4xN 总览图，方便一屏看完/喂给 AI 看"""
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".png", ".webp")))
    if not files:
        return []
    import glob
    tiles = "4x%d" % max(1, min(per_sheet // cols, len(files) // cols or 1))
    out = os.path.join(folder, "_sheet_%02d.jpg")
    cmd = ["ffmpeg", "-v", "error", "-y", "-pattern_type", "glob", "-i", "*.jpg",
           "-vf", "scale=%d:-1,tile=%s" % (width, tiles), "-q:v", "3",
           out.replace("%02d", "%02d")]
    try:
        subprocess.run(cmd, cwd=folder, timeout=180)
    except Exception:
        return []
    return sorted(os.path.join(folder, f) for f in os.listdir(folder) if f.startswith("_sheet_"))


def shutil_which(cmd):
    for p in os.environ.get("PATH", "").split(os.pathsep):
        f = os.path.join(p, cmd)
        if os.path.isfile(f) and os.access(f, os.X_OK):
            return f
    return None


# ---------------------------------------------------------------- 命令
def cmd_doctor():
    print("%s v%s 自检" % (NAME, VERSION))
    print("  Python      ", sys.version.split()[0], "|", platform.system(), platform.machine())
    print("  ffmpeg      ", shutil_which("ffmpeg") or "未安装（仅影响'拼图预览'，下载功能不受影响）")
    try:
        t = get_ttwid(refresh=True)
        print("  ttwid       ", "OK（%s...）" % t[:18])
    except Exception as e:
        print("  ttwid       ", "失败：", e)
        return 1
    try:
        raw = http("https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=1"
                   "&device_platform=webapp&aid=6383&channel=channel_pc_web",
                   headers={"Referer": "https://www.douyin.com/", "Cookie": "ttwid=" + get_ttwid()},
                   timeout=25)
        json.loads(raw)
        print("  详情接口    ", "OK（接口可达，返回结构正常）")
        return 0
    except Exception as e:
        print("  详情接口    ", "失败：", e)
        return 1


def cmd_download(link, out_dir, as_json, do_zip, do_sheet):
    aweme_id, kind = parse_aweme_id(link)
    det = fetch_detail(aweme_id, kind)
    author = safe_name((det.get("author") or {}).get("nickname") or "douyin", 24)
    desc = safe_name(det.get("desc") or aweme_id)
    os.makedirs(out_dir, exist_ok=True)
    result = {"ok": True, "aweme_id": aweme_id, "author": author,
              "desc": det.get("desc"), "out_dir": out_dir}
    if det.get("images"):
        folder, zpath, sheets, ok = download_images(det, aweme_id, out_dir,
                                                    "%s-%s" % (author, desc), do_zip, do_sheet)
        result.update({"type": "images", "count": len(det["images"]), "downloaded": ok,
                       "path": folder, "zip": zpath, "sheets": sheets})
        if not as_json:
            print("图文作品：共 %d 张，成功 %d 张" % (len(det["images"]), ok))
            print("  目录：", folder)
            if zpath:
                print("  打包：", zpath)
            for s in sheets:
                print("  拼图：", s)
    else:
        path, size, res = pick_best_video(det, out_dir, "%s-%s" % (author, desc))
        result.update({"type": "video", "path": path, "size_mb": round(size / 1048576, 2),
                       "height": res or None})
        if not as_json:
            print("视频：%.2f MB%s" % (size / 1048576, "  %dp" % res if res else ""))
            print("  文件：", path)
            print("  （无水印源：play_addr / bit_rate，未使用带 logo_name 的 download_addr）")
    if as_json:
        print(json.dumps(result, ensure_ascii=False))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog=NAME, description="抖音无水印下载器（视频/图文，零依赖，无需登录）")
    ap.add_argument("link", nargs="*", help="抖音分享文本或链接")
    ap.add_argument("-o", "--out", default=default_out_dir(), help="保存目录（默认 ~/Downloads/douyin-nomark）")
    ap.add_argument("--json", action="store_true", help="输出 JSON，便于脚本调用")
    ap.add_argument("--no-zip", action="store_true", help="图文不打包 zip")
    ap.add_argument("--no-sheet", action="store_true", help="图文不生成拼图预览")
    ap.add_argument("--doctor", action="store_true", help="自检网络/接口")
    ap.add_argument("-v", "--version", action="version", version="%s v%s" % (NAME, VERSION))
    a = ap.parse_args(argv)

    if a.doctor:
        return cmd_doctor()
    if not a.link:
        ap.print_help()
        print("\n用法示例：%s \"0.05 复制打开抖音… https://v.douyin.com/xxxxxx/\"" % NAME)
        return 2
    try:
        return cmd_download(" ".join(a.link), os.path.expanduser(a.out), a.json, not a.no_zip, not a.no_sheet)
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        if a.json:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        else:
            print("❌ 失败：%s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
