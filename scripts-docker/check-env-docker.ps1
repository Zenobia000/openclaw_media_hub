# ============================================================
# check-env-docker.ps1 — 環境檢查腳本 (Docker)
#
# 用法：.\scripts-docker\check-env-docker.ps1
#
# 此腳本會檢查以下項目：
#   1. Docker
#   2. VS Code
#   3. ngrok
#   4. 複製 .env.example → .env（若 .env 不存在）
# ============================================================

. "$PSScriptRoot\common.ps1"
$ErrorActionPreference = "Continue"  # 環境檢查時不中斷

$allPassed = $true

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  OpenClaw 環境檢查工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. 檢查 Docker ───────────────────────────────────────────
Write-Info "檢查 Docker..."
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Docker 已安裝 — $dockerVersion"

        # 進一步檢查 Docker 是否正在執行
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "Docker Desktop 正在執行"
        } else {
            Write-Fail "Docker 已安裝但未啟動，請開啟 Docker Desktop"
            $allPassed = $false
        }
    } else {
        throw "Docker 未安裝"
    }
} catch {
    Write-Fail "Docker 未安裝。請參考 1.軟體安裝指引\1.Docker軟體 進行安裝。"
    $allPassed = $false
}

Write-Host ""

# ── 2. 檢查 VS Code ──────────────────────────────────────────
Write-Info "檢查 VS Code..."
try {
    # 1. 先檢查指令是否存在於系統中
    if (-not (Get-Command "code" -ErrorAction SilentlyContinue)) {
        throw "找不到 code 指令"
    }

    # 2. 執行指令並只取第一行，移除錯誤導向以避免干擾
    $codeVersion = code --version | Select-Object -First 1

    # 3. 檢查輸出是否包含版本號格式 (例如數字與點)
    if ($codeVersion -match '\d+\.\d+\.\d+') {
        Write-Host "[OK] VS Code 已安裝 — 版本 $codeVersion" -ForegroundColor Green
    } else {
        throw "無法辨識版本資訊"
    }
} catch {
    Write-Host "[FAIL] VS Code 未安裝。請參考 1.軟體安裝指引\2.VS Code軟體 進行安裝。" -ForegroundColor Red
    $allPassed = $false
}

Write-Host ""

# ── 3. 檢查 ngrok ────────────────────────────────────────────
Write-Info "檢查 ngrok..."
try {
    $ngrokVersion = ngrok version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "ngrok 已安裝 — $ngrokVersion"
    } else {
        throw "ngrok 未安裝"
    }
} catch {
    Write-Fail "ngrok 未安裝。請參考 1.軟體安裝指引\3.ngrok軟體 進行安裝。"
    $allPassed = $false
}

# ── 4. 複製 .env.example → .env ────────────────────────────────
Write-Host ""
Write-Info "檢查 .env 檔案..."
$envExample = Join-Path $ProjectRoot ".env.example"
$envFile    = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item -Path $envExample -Destination $envFile
        Write-Ok "已從 .env.example 複製建立 .env"
    } else {
        Write-Fail ".env.example 不存在，請手動建立 .env 檔案。"
        $allPassed = $false
    }
} else {
    Write-Ok ".env 已存在"
}

# ── 結果摘要 ──────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($allPassed) {
    Write-Ok "所有軟體皆已安裝，環境準備就緒！"
} else {
    Write-Fail "部分軟體缺少或未啟動，請依照上方提示完成安裝。"
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
