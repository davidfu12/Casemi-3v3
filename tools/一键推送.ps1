# 一键推送（通用版）：拉取 → 提交 → 推送
# 放在仓库内任意位置都能用，会自动找到仓库根目录
# 用法：双击 tools\一键推送.bat，或
#     powershell -ExecutionPolicy Bypass -File tools\一键推送.ps1 -Message "改了什么"

param(
    [string]$Message = "",
    [int]$ProxyPort = 7890
)

$ErrorActionPreference = 'Continue'

# ---------- 自动定位仓库根目录 ----------
$dir = $PSScriptRoot
while ($dir -and -not (Test-Path (Join-Path $dir ".git"))) {
    $parent = Split-Path $dir -Parent
    if ($parent -eq $dir) { $dir = $null; break }
    $dir = $parent
}
if (-not $dir) {
    Write-Host "[FAIL] 没找到 .git，请把本文件放进仓库目录里再运行" -ForegroundColor Red
    exit 1
}
Set-Location $dir
Write-Host "仓库：$dir" -ForegroundColor Gray

# ---------- 梯子检查 ----------
$listening = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
             Where-Object { $_.LocalPort -eq $ProxyPort }
if (-not $listening) {
    Write-Host "[FAIL] 梯子没开（端口 $ProxyPort）" -ForegroundColor Red
    Write-Host "       先打开代理软件；如果你的端口不是 $ProxyPort，用 -ProxyPort 参数指定" -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK]   梯子在线（$ProxyPort）" -ForegroundColor Green

# ---------- 系统代理关掉（给 Booster Studio 用）----------
$key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
if ((Get-ItemProperty $key).ProxyEnable -ne 0) {
    Set-ItemProperty $key -Name ProxyEnable -Value 0
    Write-Host "[OK]   系统代理已关闭（Studio 可正常使用）" -ForegroundColor Green
}
& git config --global http.proxy  "http://127.0.0.1:$ProxyPort" 2>$null
& git config --global https.proxy "http://127.0.0.1:$ProxyPort" 2>$null

# ---------- 身份检查 ----------
$name = & git config user.name 2>$null
if (-not $name) {
    Write-Host "[!]   还没配提交身份，请先执行：" -ForegroundColor Yellow
    Write-Host '       git config user.name  "你的名字"' -ForegroundColor Yellow
    Write-Host '       git config user.email "你的邮箱"' -ForegroundColor Yellow
    exit 1
}

# ---------- 先拉 ----------
Write-Host "[..]   先同步远程（pull）..." -ForegroundColor Cyan
& git pull --rebase origin main 2>&1 | ForEach-Object { Write-Host "       $_" }
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!]   拉取失败（冲突或网络问题），已停止" -ForegroundColor Yellow
    Write-Host "       若出现 CONFLICT，手动解决冲突后再运行" -ForegroundColor Yellow
    exit 1
}

# ---------- 提交 ----------
$changes = & git status --porcelain 2>$null
if ($changes) {
    $count = ($changes | Measure-Object).Count
    if (-not $Message) { $Message = "update: " + (Get-Date -Format 'yyyy-MM-dd HH:mm') }
    & git add -A
    & git commit -m $Message | Out-Null
    Write-Host "[OK]   已提交 $count 个文件：$Message" -ForegroundColor Green
} else {
    Write-Host "[--]   没有文件改动" -ForegroundColor Yellow
}

# ---------- 推送 ----------
Write-Host "[..]   推送到 GitHub..." -ForegroundColor Cyan
& git push origin main 2>&1 | ForEach-Object { Write-Host "       $_" }
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[OK]   完成！" -ForegroundColor Green
    & git log --oneline -1
} else {
    Write-Host "[FAIL] 推送失败：检查梯子节点，或浏览器里点 Authorize" -ForegroundColor Red
    exit 1
}
