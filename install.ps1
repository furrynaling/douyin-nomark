# dnmark 一键安装脚本（Windows PowerShell）
# 用法：irm https://raw.githubusercontent.com/furrynaling/douyin-nomark/main/install.ps1 | iex

$ErrorActionPreference = "Stop"
$Repo    = "furrynaling/douyin-nomark"
$Raw     = "https://raw.githubusercontent.com/$Repo/main/scripts/dnmark.py"
$Install = Join-Path $env:LOCALAPPDATA "dnmark"

Write-Host "==> dnmark 安装中…"

# 1. 检查 python
$py = (Get-Command python -ErrorAction SilentlyContinue) ?? (Get-Command py -ErrorAction SilentlyContinue)
if (-not $py) {
    Write-Host "❌ 没找到 Python。请先从 https://www.python.org/downloads/ 安装（勾选 Add to PATH），再重跑本脚本。" -ForegroundColor Red
    exit 1
}
Write-Host "    Python OK"

# 2. 安装目录 + 下载
New-Item -ItemType Directory -Force -Path $Install | Out-Null
Invoke-WebRequest -Uri $Raw -OutFile (Join-Path $Install "dnmark.py") -UseBasicParsing
Write-Host "    已下载到 $Install"

# 3. 生成 dnmark.cmd 包装器
$Cmd = Join-Path $Install "dnmark.cmd"
@"
@echo off
python "$Install\dnmark.py" %*
"@ | Set-Content -Path $Cmd -Encoding ASCII

# 4. 加入用户 PATH
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$Install*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$Install", "User")
    Write-Host "    已把 $Install 加入用户 PATH（新开一个终端生效）"
}
$env:Path = "$env:Path;$Install"

# 5. 验证
Write-Host "==> 验证"
& python (Join-Path $Install "dnmark.py") -v

Write-Host ""
Write-Host "✅ 安装完成：$Cmd" -ForegroundColor Green
Write-Host "TO：furrynaling · https://github.com/$Repo"
Write-Host '输入 dnmark "<抖音分享链接>" 开始使用'
