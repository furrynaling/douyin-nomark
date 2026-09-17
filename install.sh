#!/bin/bash
# dnmark 一键安装脚本（Linux / macOS / Termux）
set -e

REPO="furrynaling/douyin-nomark"
RAW="https://raw.githubusercontent.com/${REPO}/main/scripts/dnmark.py"
GITHUB="https://github.com/${REPO}"

echo "==> dnmark 安装中…"

# 1. 环境检查
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ 没找到 python3。请先安装："
    echo "   Debian/Ubuntu : sudo apt install -y python3"
    echo "   CentOS/RHEL   : sudo yum install -y python3"
    echo "   macOS         : brew install python3"
    echo "   Termux        : pkg install -y python"
    exit 1
fi
PYV=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')
echo "    Python $PYV ✓"

# 2. 下载到临时文件（用 mktemp，Termux 无标准 /tmp 也能用）
TMP="$(mktemp -t dnmark.XXXXXX)" || exit 1
trap 'rm -f "$TMP"' EXIT
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$RAW" -o "$TMP"
elif command -v wget >/dev/null 2>&1; then
    wget -qO "$TMP" "$RAW"
else
    python3 - "$RAW" "$TMP" <<'PY'
import sys, urllib.request
req = urllib.request.Request(sys.argv[1], headers={"User-Agent": "dnmark-installer/1.0"})
open(sys.argv[2], "wb").write(urllib.request.urlopen(req, timeout=30).read())
PY
fi
[ -s "$TMP" ] || { echo "❌ 下载失败（网络？）"; exit 1; }

# 3. 选择安装目录
if [ -n "$PREFIX" ] && [ -d "$PREFIX/bin" ]; then          # Termux
    DEST="$PREFIX/bin"
elif [ -w /usr/local/bin ] && [ "$(id -u)" = "0" ]; then   # 有 root 的 Linux
    DEST="/usr/local/bin"
else
    DEST="$HOME/.local/bin"
    mkdir -p "$DEST"
fi
install -m 755 "$TMP" "$DEST/dnmark" 2>/dev/null || cp "$TMP" "$DEST/dnmark" && chmod 755 "$DEST/dnmark"

# 4. 确保在 PATH 里（非 root 用户）
case ":$PATH:" in
    *":$DEST:"*) ;;
    *)
        for RC in "$HOME/.bashrc" "$HOME/.zshrc"; do
            [ -f "$RC" ] && ! grep -q "$DEST" "$RC" && echo "export PATH=\"$DEST:\$PATH\"" >> "$RC"
        done
        export PATH="$DEST:$PATH"
        echo "   已把 $DEST 加进 PATH（新开终端或 source ~/.bashrc 生效）"
        ;;
esac

# 5. 验证
echo "==> 验证"
"$DEST/dnmark" -v || { echo "❌ 安装后无法运行，请提 issue：$GITHUB/issues"; exit 1; }

echo ""
echo "✅ 安装完成：$DEST/dnmark"
echo "TO：furrynaling · $GITHUB"
echo "输入 dnmark \"<抖音分享链接>\" 开始使用"
