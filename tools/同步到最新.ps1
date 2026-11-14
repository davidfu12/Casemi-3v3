# 同步到最新（通用版）：把本地代码完全变成 GitHub 上的最新版
# 会自动定位仓库根目录；覆盖本地改动前先备份（git stash）
# 用法：双击 tools\同步到最新.bat

param([int]$ProxyPort = 7890)

$ErrorActionPreference = 'Continue'

# ---------- 定位仓库 ----------
$dir = $PSScriptRoot
while ($dir -and -not (Test-Path (Join-Path $dir ".git"))) {
    $parent = Split-Path $dir -Parent
    if ($parent -eq $dir) { $dir = $null; break }
    $dir = $parent
}
if (-not $dir) {
    Write-Host "[FAIL] 没找到 .git，请把本文件放进仓库目录里" -ForegroundColor Red
    exit 1
}
Set-Location $dir
Write-Host "仓库：$dir" -ForegroundColor Gray

# ---------- 梯子 ----------
$listening = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
             Where-Object { $_.LocalPort -eq $ProxyPort }
if (-not $listening) {
    Write-Host "[FAIL] 梯子没开（端口 $ProxyPort）" -ForegroundColor Red
    exit 1
}
Write-Host "[OK]   梯子在线（$ProxyPort）" -ForegroundColor Green

# ---------- 代理：git 走代理，系统代理关闭 ----------
$key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
if ((Get-ItemProperty $key).ProxyEnable -ne 0) {
    Set-ItemProperty $key -Name ProxyEnable -Value 0
}
& git config --global http.proxy  "http://127.0.0.1:$ProxyPort" 2>$null
& git config --global https.proxy "http://127.0.0.1:$ProxyPort" 2>$null
Write-Host "[OK]   代理已就绪" -ForegroundColor Green

# ---------- 拉取远程信息 ----------
Write-Host "[..]   检查远程..." -ForegroundColor Cyan
& git fetch origin 2>&1 | Out-Null

$localHead  = (& git rev-parse HEAD).Trim()
$remoteHead = (& git rev-parse origin/main).Trim()

if ($localHead -eq $remoteHead) {
    Write-Host "[OK]   已经是最新版" -ForegroundColor Green
} else {
    Write-Host "[..]   远程有新提交：" -ForegroundColor Cyan
    & git log --oneline "$localHead..origin/main" 2>&1 | ForEach-Object { Write-Host "       $_" }

    $dirty = & git status --porcelain 2>$null
    if ($dirty) {
        Write-Host "[!!]   本地有未提交的修改，先备份（git stash）" -ForegroundColor Yellow
        & git stash push -m ("同步前备份 " + (Get-Date -Format 'yyyy-MM-dd HH:mm')) 2>&1 | Out-Null
        Write-Host "[OK]   已备份，恢复用：git stash pop" -ForegroundColor Green
    }

    & git reset --hard origin/main 2>&1 | ForEach-Object { Write-Host "       $_" }
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[OK]   同步完成，本地 = 远程最新版" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] 同步失败" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "当前版本：" -ForegroundColor Cyan
& git log --oneline -3 2>&1 | ForEach-Object { Write-Host "  $_" }
