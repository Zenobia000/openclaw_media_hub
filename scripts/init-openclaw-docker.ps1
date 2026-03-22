# ============================================================
# init-openclaw-docker.ps1 — 初始化 OpenClaw 環境 (Docker)
#
# 用法：.\scripts\init-openclaw-docker.ps1
#
# 流程：
#   1. 檢查 Docker
#   2. 建立目錄結構與設定檔
#   3. 啟動 Docker Compose
#   4. 設定 API 金鑰（可多組）
#   5. 語音轉文字（偵測 OpenAI 金鑰自動啟用）
#   6. Dashboard 連線資訊與裝置配對
# ============================================================

. "$PSScriptRoot\common.ps1"

# ── 輔助函式 ──────────────────────────────────────────────────

# 讀取 openclaw.json
function Read-Config {
    Get-Content -Path $ConfigFile -Raw | ConvertFrom-Json
}

# 寫入 openclaw.json
function Save-Config {
    param($Data)
    $Data | ConvertTo-Json -Depth 10 | Set-Content -Path $ConfigFile -Encoding UTF8
}

# 建立或覆寫 PSObject 屬性（相容 PowerShell 5.1）
function Set-JsonProp {
    param([PSObject]$Obj, [string]$Name, $Value, [switch]$OnlyIfMissing)
    if ($Obj.PSObject.Properties[$Name]) {
        if (-not $OnlyIfMissing) { $Obj.$Name = $Value }
    } else {
        $Obj | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
    }
}

# 顯示裝置配對手動指令
function Show-PairingHint {
    param([string]$Id)
    if ($Id) {
        Write-Host "  docker compose exec openclaw-gateway openclaw devices approve $Id" -ForegroundColor Yellow
    } else {
        Write-Host "  docker compose exec openclaw-gateway openclaw devices list" -ForegroundColor Yellow
        Write-Host "  docker compose exec openclaw-gateway openclaw devices approve <ID>" -ForegroundColor Yellow
    }
}

# ── 1. 檢查 Docker ───────────────────────────────────────────

Write-Info "檢查 Docker..."
try {
    $null = docker info 2>&1
    if ($LASTEXITCODE -ne 0) { throw }
    Write-Ok "Docker 已啟動"
} catch {
    Write-Err "Docker 未啟動或未安裝，請先開啟 Docker Desktop。"
    exit 1
}

# ── 2. 建立目錄結構與設定檔 ───────────────────────────────────

Write-Info "初始化 .openclaw 目錄..."

# 若 .openclaw 存在但不是目錄（例如誤建為檔案），先移除
if ((Test-Path $OpenClawDir) -and -not (Test-Path $OpenClawDir -PathType Container)) {
    Write-Warn ".openclaw 存在但不是目錄，將其移除後重新建立。"
    Remove-Item -Path $OpenClawDir -Force
}

foreach ($dir in @(
    "$OpenClawDir\agents\main\agent"
    "$OpenClawDir\workspace\skills"
)) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Ok "建立目錄：$($dir.Replace("$ProjectRoot\", ''))"
    }
}

if (-not (Test-Path $ConfigFile)) {
    @'
{
  "gateway": {
    "mode": "local",
    "bind": "custom",
    "customBindHost": "0.0.0.0"
  }
}
'@ | Set-Content -Path $ConfigFile -Encoding UTF8
    Write-Ok "建立 openclaw.json"
}

Write-Host ""
Write-Ok "初始化完成"

# ── 3. 啟動 Docker Compose ───────────────────────────────────

Write-Host ""
Write-Info "啟動 Docker Compose..."
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Err "Docker Compose 啟動失敗"
    exit 1
}
Write-Ok "Docker Compose 已啟動"

Write-Host ""
if (-not (Wait-Gateway -Label "等待 Gateway 啟動")) {
    Write-Err "Gateway 未就緒，請檢查容器狀態。"
    exit 1
}

# ── 4. 設定 API 金鑰 ─────────────────────────────────────────

do {
    Write-Host ""

    # 顯示已設定的金鑰摘要
    $keyCount = 0
    try {
        $profiles = @((Read-Config).auth.profiles.PSObject.Properties)
        $keyCount = $profiles.Count
    } catch { }

    if ($keyCount -gt 0) {
        Write-Ok "已設定 $keyCount 組 API 金鑰："
        foreach ($p in $profiles) {
            Write-Host "  * $($p.Name)（$($p.Value.provider), $($p.Value.mode)）" -ForegroundColor Cyan
        }
    } else {
        Write-Info "尚未設定 API 金鑰。"
    }

    Write-Host ""
    if (-not (Confirm-YesNo "是否要設定 API 金鑰？")) { break }

    Write-Host ""
    Write-Info "啟動設定精靈..."
    Write-Host ""
    # 不使用 Invoke-Gateway，其 2>&1 會導致互動式精靈無法正常顯示
    docker compose exec openclaw-gateway openclaw configure --section model
} while ($true)

# ── 5. 語音轉文字（偵測 OpenAI 金鑰自動啟用）─────────────────

Write-Host ""
$authFile = Join-Path $OpenClawDir "agents\main\agent\auth-profiles.json"
$openaiProfile = $null
if (Test-Path $authFile) {
    $openaiProfile = (Get-Content $authFile -Raw | ConvertFrom-Json).profiles.PSObject.Properties |
        Where-Object { $_.Value.provider -eq "openai" } |
        Select-Object -First 1 -ExpandProperty Name
}

if ($openaiProfile) {
    Write-Info "偵測到 OpenAI profile：$openaiProfile，啟用語音轉文字..."
    try {
        $config = Read-Config
        Set-JsonProp $config 'tools' ([PSCustomObject]@{}) -OnlyIfMissing
        Set-JsonProp $config.tools 'media' ([PSCustomObject]@{
            audio = [PSCustomObject]@{
                enabled        = $true
                language       = "zh"
                models         = @([PSCustomObject]@{
                    provider = "openai"
                    model    = "whisper-1"
                    profile  = $openaiProfile
                })
                echoTranscript = $true
            }
        })
        Save-Config $config
        Write-Ok "語音轉文字已啟用（profile=$openaiProfile）"
    } catch {
        Write-Err "語音設定寫入失敗：$_"
    }
} else {
    Write-Info "未偵測到 OpenAI 金鑰，略過語音轉文字。"
}

# 重啟套用設定
if (-not (Restart-AndWait -Reason "套用設定")) {
    Write-Err "Gateway 未就緒，請檢查容器狀態。"
    exit 1
}

# ── 6. Dashboard 連線資訊與裝置配對 ──────────────────────────

Write-Host ""
$token = $null
try {
    $token = (Read-Config).gateway.auth.token
    if ([string]::IsNullOrWhiteSpace($token)) { $token = $null }
} catch { }

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Dashboard 連線資訊" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
if ($token) {
    Write-Host ""
    Write-Host "  URL  : http://127.0.0.1:18789/" -ForegroundColor Cyan
    Write-Host "  Token: $token" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Warn "Token 未取得，請查看 openclaw.json 的 gateway.auth.token。"
    Write-Host ""
}
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Info "Gateway 綁定 0.0.0.0，瀏覽器首次連線需配對審批。"
Write-Host ""

if (Confirm-YesNo "是否要進行裝置配對？") {
    Write-Info "等待瀏覽器連線..."
    $requestId = $null
    for ($w = 0; $w -lt 60; $w += 3) {
        $output = docker compose exec openclaw-gateway openclaw devices list 2>&1 | Out-String
        if ($output -match "Pending \((\d+)\)" -and [int]$Matches[1] -gt 0) {
            if ($output -match "([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})") {
                $requestId = $Matches[1]; break
            }
        }
        Start-Sleep -Seconds 3
        if ($w % 15 -eq 0 -and $w -gt 0) { Write-Info "等待中...（${w} 秒）" }
    }

    if ($requestId) {
        Write-Info "配對請求：$requestId"
        if (Invoke-Gateway devices, approve, $requestId) {
            Write-Ok "配對完成！請重新整理瀏覽器。"
        } else {
            Write-Err "配對失敗，請手動執行："
            Show-PairingHint $requestId
        }
    } else {
        Write-Warn "等待逾時，請手動執行："
        Show-PairingHint
    }
} else {
    Write-Info "略過配對。稍後可手動執行："
    Show-PairingHint
}
