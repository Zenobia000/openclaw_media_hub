# ============================================================
# init-openclaw.ps1 — 初始化 .openclaw 目錄結構與插件設定
#
# 用法：.\scripts\init-openclaw.ps1
#
# 流程：
#   1. 建立 .openclaw 目錄結構
#   2. 產生 openclaw.json（Gateway 設定）
#   3. 啟動 Docker Compose
#   4. 設定 API 金鑰（可多組，迴圈詢問）
#   5. 啟用語音轉文字（OpenAI Whisper）
#   6. 裝置配對
# ============================================================

. "$PSScriptRoot\common.ps1"

# ════════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════════

# 0. 檢查 Docker
Write-Info "檢查 Docker 是否正在執行..."
try {
    $null = cmd /c "docker info >nul 2>&1"
    if ($LASTEXITCODE -ne 0) { throw "Docker 未回應" }
    Write-Ok "Docker 已啟動"
} catch {
    Write-Err "Docker 未啟動或未安裝。請先開啟 Docker Desktop 再執行此腳本。"
    exit 1
}

# 1. 建立目錄結構
Write-Info "開始初始化 .openclaw 目錄結構..."
Write-Info "目標路徑：$OpenClawDir"

$dirs = @(
    $OpenClawDir
    Join-Path $OpenClawDir "agents\main\agent"
    Join-Path $OpenClawDir "workspace"
    Join-Path $OpenClawDir "workspace\skills"
)

foreach ($dir in $dirs) {
    $rel = $dir.Replace("$ProjectRoot\", "")
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Ok "建立目錄：$rel"
    } else {
        Write-Info "目錄已存在：$rel（略過）"
    }
}

# 2. 產生 openclaw.json
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
    Write-Ok "建立設定檔：.openclaw\openclaw.json（mode=local, bind=0.0.0.0）"
} else {
    Write-Info "設定檔已存在：.openclaw\openclaw.json（略過）"
}

Write-Host ""
Write-Ok "初始化完成！"

# 3. 啟動 Docker Compose
Write-Host ""
Write-Info "正在啟動 Docker Compose 服務..."
try {
    docker compose up -d
    if ($LASTEXITCODE -ne 0) { throw "docker compose up -d 失敗" }
    Write-Ok "Docker Compose 服務已啟動"
} catch {
    Write-Err "無法啟動 Docker Compose 服務：$_"
    exit 1
}

Write-Host ""
if (-not (Wait-Gateway -Label "等待 Gateway 啟動")) {
    Write-Err "Gateway 未就緒，請手動檢查容器狀態。"
    exit 1
}

# 4. 設定 API 金鑰（迴圈，可設定多組）
do {
    # 顯示目前已設定的 API 金鑰摘要
    Write-Host ""
    try {
        $config = Get-Content -Path $ConfigFile -Raw | ConvertFrom-Json
        if ($config.auth -and $config.auth.profiles) {
            $providers = @($config.auth.profiles.PSObject.Properties)
            if ($providers.Count -gt 0) {
                Write-Ok "目前已設定 $($providers.Count) 組 API 金鑰："
                foreach ($p in $providers) {
                    $providerName = $p.Value.provider
                    $mode         = $p.Value.mode
                    Write-Host "  • $($p.Name) （Provider: $providerName, 模式: $mode）" -ForegroundColor Cyan
                }
            } else {
                Write-Info "目前尚未設定任何 API 金鑰。"
            }
        } else {
            Write-Info "目前尚未設定任何 API 金鑰。"
        }
    } catch { }

    Write-Host ""
    if (-not (Confirm-YesNo "是否要設定 AI 模型的 API 金鑰？（如 Anthropic Claude、OpenAI 等）")) {
        break
    }

    Write-Host ""
    Write-Info "即將啟動 openclaw 內建設定精靈，請依照提示選擇 Provider 並完成設定。"
    Write-Host ""
    # 不使用 Invoke-Gateway，因為其 2>&1 會捕獲輸出導致互動式精靈無法正常顯示
    docker compose exec openclaw-gateway openclaw configure --section model
} while ($true)

# 5. 語音轉文字功能（偵測到 OpenAI API 金鑰時自動啟用）
Write-Host ""
$authProfilesFile = Join-Path $OpenClawDir "agents\main\agent\auth-profiles.json"
$openaiProfile = $null
if (Test-Path $authProfilesFile) {
    $authProfiles = Get-Content -Path $authProfilesFile -Raw | ConvertFrom-Json
    $openaiProfile = $authProfiles.profiles.PSObject.Properties |
        Where-Object { $_.Value.provider -eq "openai" } |
        Select-Object -First 1 -ExpandProperty Name
}
if (-not [string]::IsNullOrWhiteSpace($openaiProfile)) {
    Write-Info "偵測到 OpenAI profile：$openaiProfile，自動啟用語音轉文字功能..."
    try {
        $config = Get-Content -Path $ConfigFile -Raw | ConvertFrom-Json
        if (-not $config.PSObject.Properties['tools']) {
            $config | Add-Member -MemberType NoteProperty -Name 'tools' -Value ([PSCustomObject]@{})
        }
        $audioConfig = [PSCustomObject]@{
            enabled        = $true
            language        = "zh"
            models          = @(
                [PSCustomObject]@{
                    provider = "openai"
                    model    = "whisper-1"
                    profile  = $openaiProfile
                }
            )
            echoTranscript = $true
        }
        $mediaConfig = [PSCustomObject]@{ audio = $audioConfig }
        if ($config.tools.PSObject.Properties['media']) {
            $config.tools.media = $mediaConfig
        } else {
            $config.tools | Add-Member -MemberType NoteProperty -Name 'media' -Value $mediaConfig
        }
        $config | ConvertTo-Json -Depth 10 | Set-Content -Path $ConfigFile -Encoding UTF8
        Write-Ok "語音轉文字功能已啟用（language=zh, model=whisper-1, profile=$openaiProfile）"
    } catch {
        Write-Err "無法寫入語音設定：$_"
    }
} else {
    Write-Info "未偵測到 OpenAI API 金鑰，略過語音轉文字功能。"
}

# 重啟以套用設定
if (-not (Restart-AndWait -Reason "套用設定")) {
    Write-Err "Gateway 未就緒，請手動檢查容器狀態。"
    exit 1
}

# 讀取 Dashboard Token
Write-Host ""
Write-Info "正在讀取 Dashboard Token..."
$dashboardToken = $null
try {
    $config = Get-Content -Path $ConfigFile -Raw | ConvertFrom-Json
    $dashboardToken = $config.gateway.auth.token
    if ([string]::IsNullOrWhiteSpace($dashboardToken)) { throw "未找到 token" }
    Write-Ok "Dashboard Token 已取得"
} catch {
    Write-Err "無法讀取 Token：$_"
    Write-Warn "您可手動查看 .openclaw\openclaw.json 中的 gateway.auth.token 欄位。"
}


# 6. 裝置配對
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Dashboard 連線資訊" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
if ($dashboardToken) {
    Write-Host ""
    Write-Host "  URL  : http://127.0.0.1:18789/" -ForegroundColor Cyan
    Write-Host "  Token: $dashboardToken" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Warn "  Token 未取得，請手動查看 .openclaw\openclaw.json 中的 gateway.auth.token 欄位。"
    Write-Host ""
}
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Info "裝置配對流程 — 由於 Gateway 綁定 0.0.0.0，瀏覽器首次連線需配對審批。"
Write-Info "請在瀏覽器開啟上方 URL，並使用 Token 登入。"
Write-Host ""

if (Confirm-YesNo "是否要現在進行裝置配對？") {
    Write-Info "等待瀏覽器連線產生配對請求..."
    $requestId = $null
    for ($w = 0; $w -lt 60; $w += 3) {
        $listOutput = docker compose exec openclaw-gateway openclaw devices list 2>&1 | Out-String
        if ($listOutput -match "Pending \((\d+)\)" -and [int]$Matches[1] -gt 0) {
            if ($listOutput -match "([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})") {
                $requestId = $Matches[1]; break
            }
        }
        Start-Sleep -Seconds 3
        if ($w % 15 -eq 0 -and $w -gt 0) { Write-Info "仍在等待瀏覽器連線...（已等待 ${w} 秒）" }
    }

    if ($requestId) {
        Write-Info "偵測到配對請求：$requestId"
        if (Invoke-Gateway devices, approve, $requestId) {
            Write-Ok "裝置配對完成！請重新整理瀏覽器頁面。"
        } else {
            Write-Err "配對審批失敗，請手動執行："
            Write-Host "  docker compose exec openclaw-gateway openclaw devices approve $requestId" -ForegroundColor Yellow
        }
    } else {
        Write-Warn "等待逾時，未偵測到配對請求。您可稍後手動執行："
        Write-Host "  docker compose exec openclaw-gateway openclaw devices list" -ForegroundColor Yellow
        Write-Host "  docker compose exec openclaw-gateway openclaw devices approve <Request ID>" -ForegroundColor Yellow
    }
} else {
    Write-Info "略過裝置配對。您可稍後手動執行："
    Write-Host "  docker compose exec openclaw-gateway openclaw devices list" -ForegroundColor Yellow
    Write-Host "  docker compose exec openclaw-gateway openclaw devices approve <Request ID>" -ForegroundColor Yellow
}
