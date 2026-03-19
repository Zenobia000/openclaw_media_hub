# ============================================================
# init-openclaw.ps1 — 初始化專案內 .openclaw 目錄結構
#
# 用法：
#   .\init-openclaw.ps1
#
# 此腳本會：
#   1. 建立 .openclaw 目錄結構
#   1-1. 部署技能（從 module_pack 複製至 workspace\skills）
#   2. 產生 openclaw.json (Gateway 設定)
#   3. 複製 .env.example → .env（若不存在）
#   4. 啟動 Docker Compose 服務
#   5. 使用 openclaw configure 設定 API 金鑰
#   6. 安裝 LINE 插件 (@openclaw/line)
# ============================================================

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$OpenClawDir = Join-Path $ScriptDir ".openclaw"

# ── 顏色輸出 ────────────────────────────────────────────────
function Write-Info  { param($Msg) Write-Host "[INFO]  $Msg" -ForegroundColor Blue }
function Write-Ok    { param($Msg) Write-Host "[OK]    $Msg" -ForegroundColor Green }
function Write-Warn  { param($Msg) Write-Host "[WARN]  $Msg" -ForegroundColor Yellow }

# ── 主流程 ──────────────────────────────────────────────────

# 0. 檢查 Docker 是否正在執行
Write-Info "檢查 Docker 是否正在執行..."
try {
    $null = cmd /c "docker info >nul 2>&1"
    if ($LASTEXITCODE -ne 0) {
        throw "Docker 未回應"
    }
    Write-Ok "Docker 已啟動"
} catch {
    Write-Host "[ERROR] Docker 未啟動或未安裝。請先開啟 Docker Desktop 再執行此腳本。" -ForegroundColor Red
    exit 1
}

Write-Info "開始初始化 .openclaw 目錄結構..."
Write-Info "目標路徑：$OpenClawDir"

# 1. 建立目錄結構
$dirs = @(
    $OpenClawDir
    Join-Path $OpenClawDir "agents\main\agent"
    Join-Path $OpenClawDir "workspace"
    Join-Path $OpenClawDir "workspace\skills"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        $rel = $dir.Replace("$ScriptDir\", "")
        Write-Ok "建立目錄：$rel"
    } else {
        $rel = $dir.Replace("$ScriptDir\", "")
        Write-Info "目錄已存在：$rel（略過）"
    }
}

# 1-1. 部署技能：掃描 module_pack 中含 SKILL.md 的目錄，複製至 workspace\skills
$modulePackDir = Join-Path $ScriptDir "module_pack"
$skillsTargetDir = Join-Path $OpenClawDir "workspace\skills"

if (Test-Path $modulePackDir) {
    Write-Info "掃描 module_pack 中的技能..."
    $skillDirs = Get-ChildItem -Path $modulePackDir -Recurse -Filter "SKILL.md" | ForEach-Object { $_.Directory }

    foreach ($skillDir in $skillDirs) {
        $skillName = $skillDir.Name
        $targetDir = Join-Path $skillsTargetDir $skillName

        if (Test-Path $targetDir) {
            Write-Info "技能已存在：$skillName（略過）"
        } else {
            Copy-Item -Path $skillDir.FullName -Destination $targetDir -Recurse
            Write-Ok "部署技能：$skillName → .openclaw\workspace\skills\$skillName"
        }
    }
} else {
    Write-Warn "module_pack 目錄不存在，略過技能部署。"
}

# 2. 產生 openclaw.json（若不存在）
$configFile = Join-Path $OpenClawDir "openclaw.json"
if (-not (Test-Path $configFile)) {
    @'
{
  "gateway": {
    "mode": "local",
    "bind": "custom",
    "customBindHost": "0.0.0.0"
  }
}
'@ | Set-Content -Path $configFile -Encoding UTF8
    Write-Ok "建立設定檔：.openclaw\openclaw.json（mode=local, bind=0.0.0.0）"
} else {
    Write-Info "設定檔已存在：.openclaw\openclaw.json（略過）"
}

Write-Host ""
Write-Ok "初始化完成！"

# 4. 複製 .env.example → .env（若不存在）
$envExample = Join-Path $ScriptDir ".env.example"
$envFile = Join-Path $ScriptDir ".env"
if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item -Path $envExample -Destination $envFile
        Write-Ok "已從 .env.example 複製建立 .env"
    } else {
        Write-Warn ".env.example 不存在，請手動建立 .env 檔案。"
    }
} else {
    Write-Info ".env 已存在（略過複製）"
}

# 5. 啟動 Docker Compose 服務
Write-Host ""
Write-Info "正在啟動 Docker Compose 服務..."
try {
    docker compose up -d
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose up -d 失敗"
    }
    Write-Ok "Docker Compose 服務已啟動"
} catch {
    Write-Host "[ERROR] 無法啟動 Docker Compose 服務：$_" -ForegroundColor Red
    exit 1
}

# 6. 等待 Gateway 啟動並讀取自動產生的 Token
Write-Host ""
$spinChars = @('|', '/', '-', '\')
$spinIdx = 0
$maxWait = 30
$waited = 0
$gatewayReady = $false
Write-Host -NoNewline "[INFO]  等待 Gateway 啟動... " -ForegroundColor Blue
while ($waited -lt $maxWait) {
    Write-Host -NoNewline "`b$($spinChars[$spinIdx % 4])" -ForegroundColor Cyan
    $spinIdx++
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:18789/healthz" -TimeoutSec 2 -ErrorAction Stop
        if ($health.ok -eq $true) { $gatewayReady = $true; break }
    } catch { }
    Start-Sleep -Seconds 1
    $waited += 1
}
Write-Host "`b " # 清除 spinner 字元

if (-not $gatewayReady) {
    Write-Host "[ERROR] Gateway 未在 ${maxWait} 秒內就緒，請手動檢查容器狀態。" -ForegroundColor Red
    exit 1
}
Write-Ok "Gateway 已就緒（${waited} 秒）"

# 7. 使用 openclaw 內建設定精靈配置 API 金鑰（auth-profiles.json）
$authFile = Join-Path $OpenClawDir "agents\main\agent\auth-profiles.json"
$needAuth = $true
if (Test-Path $authFile) {
    $currentAuth = Get-Content -Path $authFile -Raw
    if ($currentAuth -notmatch "YOUR_API_KEY_HERE" -and $currentAuth -match '"token"\s*:\s*"sk-') {
        Write-Info "auth-profiles.json 已設定 API 金鑰（略過）"
        $needAuth = $false
    }
}

if ($needAuth) {
    Write-Host ""
    $doConfig = Read-Host "是否要現在設定 Claude API 金鑰？(Y/n)"
    if ($doConfig -ne 'n' -and $doConfig -ne 'N') {
        Write-Host ""
        Write-Info "即將啟動 openclaw 內建設定精靈..."
        Write-Info "請依照精靈提示完成 Model / API 金鑰設定。"
        Write-Host ""
        docker compose exec openclaw-gateway openclaw configure --section model
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "API 金鑰設定完成"
        } else {
            Write-Warn "設定精靈未正常完成。您可稍後手動執行："
            Write-Host "  docker compose exec openclaw-gateway openclaw configure --section model" -ForegroundColor Yellow
        }
    } else {
        Write-Warn "略過金鑰設定。您可稍後執行以下指令完成設定："
        Write-Host "  docker compose exec openclaw-gateway openclaw configure --section model" -ForegroundColor Yellow
    }
}

# 重新啟動 Docker 服務並等待
Write-Host ""
Write-Info "正在重新啟動 Docker Compose 服務以套用設定..."
try {
    docker compose restart
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose restart 失敗"
    }
    Write-Ok "Docker Compose 服務已重新啟動"
} catch {
    Write-Host "[ERROR] 無法重新啟動 Docker Compose 服務：$_" -ForegroundColor Red
    exit 1
}

Write-Host ""
$spinChars = @('|', '/', '-', '\')
$spinIdx = 0
$maxWait = 30
$waited = 0
$gatewayReady = $false
Write-Host -NoNewline "[INFO]  等待 Gateway 重新啟動... " -ForegroundColor Blue
while ($waited -lt $maxWait) {
    Write-Host -NoNewline "`b$($spinChars[$spinIdx % 4])" -ForegroundColor Cyan
    $spinIdx++
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:18789/healthz" -TimeoutSec 2 -ErrorAction Stop
        if ($health.ok -eq $true) { $gatewayReady = $true; break }
    } catch { }
    Start-Sleep -Seconds 1
    $waited += 1
}
Write-Host "`b " # 清除 spinner 字元

if (-not $gatewayReady) {
    Write-Host "[ERROR] Gateway 未在 ${maxWait} 秒內重新就緒，請手動檢查容器狀態。" -ForegroundColor Red
    exit 1
}
Write-Ok "Gateway 已重新就緒（${waited} 秒）"

# 讀取 openclaw.json 中自動產生的 Token（稍後在裝置配對前顯示）
Write-Host ""
Write-Info "正在讀取 Dashboard Token..."
$dashboardToken = $null
try {
    $config = Get-Content -Path $configFile -Raw | ConvertFrom-Json
    $dashboardToken = $config.gateway.auth.token
    if ([string]::IsNullOrWhiteSpace($dashboardToken)) {
        throw "設定檔中未找到 token"
    }
    Write-Ok "Dashboard Token 已取得"
} catch {
    Write-Host "[ERROR] 無法讀取 Token：$_" -ForegroundColor Red
    Write-Warn "您可手動查看 .openclaw\openclaw.json 中的 gateway.auth.token 欄位。"
}

# 8. 安裝與設定 LINE 插件
Write-Host ""
$doLine = Read-Host "是否要安裝 LINE 插件？(Y/n)"
if ($doLine -ne 'n' -and $doLine -ne 'N') {

    # 8-1. 安裝插件
    Write-Info "正在安裝 LINE 插件 (@openclaw/line)..."
    try {
        docker compose exec openclaw-gateway openclaw plugins install @openclaw/line
        if ($LASTEXITCODE -ne 0) {
            throw "插件安裝失敗"
        }
        Write-Ok "LINE 插件安裝完成"
    } catch {
        Write-Warn "LINE 插件安裝失敗：$_"
        Write-Warn "您可稍後手動執行："
        Write-Host "  docker compose exec openclaw-gateway openclaw plugins install @openclaw/line" -ForegroundColor Yellow
    }

    # 8-2. 設定 LINE Channel Access Token / Secret
    Write-Host ""
    Write-Info "設定 LINE Channel 資訊..."
    Write-Info "請從 LINE Developers Console 取得以下資訊："
    Write-Host "  https://developers.line.biz/console/" -ForegroundColor Cyan
    Write-Host ""
    $lineToken  = Read-Host "請輸入 Channel Access Token"
    $lineSecret = Read-Host "請輸入 Channel Secret"

    if (-not [string]::IsNullOrWhiteSpace($lineToken) -and -not [string]::IsNullOrWhiteSpace($lineSecret)) {
        try {
            $config = Get-Content -Path $configFile -Raw | ConvertFrom-Json

            # 確保 channels 物件存在
            if (-not $config.PSObject.Properties['channels']) {
                $config | Add-Member -MemberType NoteProperty -Name 'channels' -Value ([PSCustomObject]@{})
            }

            # 寫入 line 設定
            $lineConfig = [PSCustomObject]@{
                enabled            = $true
                channelAccessToken = $lineToken
                channelSecret      = $lineSecret
                dmPolicy           = "pairing"
            }

            if ($config.channels.PSObject.Properties['line']) {
                $config.channels.line = $lineConfig
            } else {
                $config.channels | Add-Member -MemberType NoteProperty -Name 'line' -Value $lineConfig
            }

            $config | ConvertTo-Json -Depth 10 | Set-Content -Path $configFile -Encoding UTF8
            Write-Ok "LINE 設定已寫入 .openclaw\openclaw.json"
        } catch {
            Write-Host "[ERROR] 無法寫入 LINE 設定：$_" -ForegroundColor Red
        }
    } else {
        Write-Warn "Token 或 Secret 為空，略過設定。您可稍後手動編輯 .openclaw\openclaw.json"
    }

    # 8-3. 重啟服務以套用 LINE 插件設定（必須在 Webhook 驗證之前完成）
    Write-Host ""
    Write-Info "正在重新啟動服務以套用 LINE 插件設定..."
    try {
        docker compose restart
        if ($LASTEXITCODE -ne 0) { throw "docker compose restart 失敗" }
        Write-Ok "服務已重新啟動"
    } catch {
        Write-Host "[ERROR] 無法重新啟動服務：$_" -ForegroundColor Red
    }

    # 等待 Gateway 就緒
    $spinChars = @('|', '/', '-', '\')
    $spinIdx = 0
    $maxWait = 30
    $waited = 0
    $gatewayReady = $false
    Write-Host -NoNewline "[INFO]  等待 Gateway 就緒... " -ForegroundColor Blue
    while ($waited -lt $maxWait) {
        Write-Host -NoNewline "`b$($spinChars[$spinIdx % 4])" -ForegroundColor Cyan
        $spinIdx++
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:18789/healthz" -TimeoutSec 2 -ErrorAction Stop
            if ($health.ok -eq $true) { $gatewayReady = $true; break }
        } catch { }
        Start-Sleep -Seconds 1
        $waited += 1
    }
    Write-Host "`b "
    if ($gatewayReady) {
        Write-Ok "Gateway 已就緒（${waited} 秒）"
    } else {
        Write-Warn "Gateway 未在 ${maxWait} 秒內就緒，LINE Webhook 驗證可能會失敗。"
    }

    # 8-4. 啟動 ngrok tunnel（LINE webhook 需要公開 HTTPS URL）
    Write-Host ""
    Write-Info "LINE Webhook 需要公開 HTTPS URL，正在啟動 ngrok tunnel..."

    # 檢查 ngrok 是否已安裝
    $ngrokCmd = Get-Command ngrok -ErrorAction SilentlyContinue
    if (-not $ngrokCmd) {
        Write-Host "[ERROR] 未偵測到 ngrok。請先安裝 ngrok：" -ForegroundColor Red
        Write-Host "  https://ngrok.com/download" -ForegroundColor Yellow
        Write-Host "  安裝後執行 'ngrok config add-authtoken <你的token>' 完成設定" -ForegroundColor Yellow
        Write-Host ""
        Write-Warn "略過 ngrok 啟動。LINE Webhook 將無法運作，配對流程需待 ngrok 設定完成後再執行。"
    } else {
        # 檢查是否已有 ngrok 在監聽 18789
        $ngrokUrl = $null
        try {
            $ngrokApi = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3 -ErrorAction Stop
            $existing = $ngrokApi.tunnels | Where-Object { $_.config.addr -match "18789" -and $_.proto -eq "https" } | Select-Object -First 1
            if ($existing) {
                $ngrokUrl = $existing.public_url
                Write-Info "偵測到已存在的 ngrok tunnel：$ngrokUrl"
            }
        } catch { }

        if (-not $ngrokUrl) {
            Write-Info "正在背景啟動 ngrok http 18789 ..."
            Start-Process ngrok -ArgumentList "http", "18789" -WindowStyle Minimized
            # 等待 ngrok 就緒
            $ngrokReady = $false
            for ($i = 0; $i -lt 10; $i++) {
                Start-Sleep -Seconds 2
                try {
                    $ngrokApi = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3 -ErrorAction Stop
                    $tunnel = $ngrokApi.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1
                    if ($tunnel) {
                        $ngrokUrl = $tunnel.public_url
                        $ngrokReady = $true
                        break
                    }
                } catch { }
            }

            if ($ngrokReady) {
                Write-Ok "ngrok tunnel 已啟動"
            } else {
                Write-Host "[ERROR] ngrok 未在 20 秒內就緒，請手動執行 'ngrok http 18789' 並重試。" -ForegroundColor Red
            }
        }

        if ($ngrokUrl) {
            $webhookUrl = "$ngrokUrl/line/webhook"
            Write-Host ""
            Write-Host "============================================================" -ForegroundColor Green
            Write-Host "  LINE Webhook URL（請複製）" -ForegroundColor Green
            Write-Host "============================================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "  $webhookUrl" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "============================================================" -ForegroundColor Green
            Write-Host ""
            Write-Info "請至 LINE Developers Console 設定 Webhook URL："
            Write-Host ""
            Write-Host "  1. 開啟 https://developers.line.biz/console/" -ForegroundColor Cyan
            Write-Host "  2. 選擇你的 Provider → 選擇你的 Channel" -ForegroundColor Cyan
            Write-Host "  3. 進入 Messaging API settings" -ForegroundColor Cyan
            Write-Host "  4. 找到 Webhook URL，貼上上方網址" -ForegroundColor Cyan
            Write-Host "  5. 開啟 Use webhook 開關" -ForegroundColor Cyan
            Write-Host "  6. 點擊 Verify 確認連線成功" -ForegroundColor Cyan
            Write-Host ""
            Read-Host "完成上述設定後，按 Enter 繼續"
        }
    }

    # 8-5. LINE 配對流程
    Write-Host ""
    Write-Info "LINE 配對流程："
    Write-Host "  1. 透過 LINE 傳送任意訊息給你的 Bot" -ForegroundColor Cyan
    Write-Host "  2. Bot 會回傳一組配對碼" -ForegroundColor Cyan
    Write-Host ""
    do {
        $doLinePair = Read-Host "請先傳送 LINE 訊息給 Bot，取得配對碼後輸入配對碼（輸入 n 略過）"
        if ([string]::IsNullOrWhiteSpace($doLinePair)) {
            Write-Warn "請輸入配對碼或輸入 n 略過，不可空白。"
        }
    } while ([string]::IsNullOrWhiteSpace($doLinePair))

    if ($doLinePair -ne 'n' -and $doLinePair -ne 'N') {
        Write-Info "正在執行 LINE 配對審批..."
        docker compose exec openclaw-gateway openclaw pairing approve line $doLinePair 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "LINE 配對完成！"
        } else {
            Write-Host "[ERROR] LINE 配對失敗，請手動執行：" -ForegroundColor Red
            Write-Host "  docker compose exec openclaw-gateway openclaw pairing approve line <配對碼>" -ForegroundColor Yellow
        }
    } else {
        Write-Info "略過 LINE 配對。您可稍後手動執行："
        Write-Host "  docker compose exec openclaw-gateway openclaw pairing approve line <配對碼>" -ForegroundColor Yellow
    }

} else {
    Write-Info "略過 LINE 插件安裝。您可稍後手動執行："
    Write-Host "  docker compose exec openclaw-gateway openclaw plugins install @openclaw/line" -ForegroundColor Yellow
}

# 9. 裝置配對（Device Pairing）
#    bind=0.0.0.0 時，從主機連入的流量經 Docker bridge（非 loopback），
#    Gateway 會要求 device pairing 審批。
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
Write-Info "裝置配對流程（Device Pairing）"
Write-Info "由於 Gateway 綁定 0.0.0.0，瀏覽器首次連線需要配對審批。"
Write-Info "請在瀏覽器開啟上方 URL，並使用 Token 登入。"
Write-Host ""
$doPair = Read-Host "是否要現在進行裝置配對？(Y/n)"
if ($doPair -ne 'n' -and $doPair -ne 'N') {
    Write-Info "等待瀏覽器連線產生配對請求..."
    $maxPairWait = 60
    $pairWaited = 0
    $requestId = $null

    while ($pairWaited -lt $maxPairWait) {
        $listOutput = docker compose exec openclaw-gateway openclaw devices list 2>&1 | Out-String
        # 從輸出中提取 Pending 區塊的 Request ID（UUID 格式）
        if ($listOutput -match "Pending \((\d+)\)") {
            $pendingCount = [int]$Matches[1]
            if ($pendingCount -gt 0 -and $listOutput -match "([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})") {
                $requestId = $Matches[1]
                break
            }
        }
        Start-Sleep -Seconds 3
        $pairWaited += 3
        if ($pairWaited % 15 -eq 0) {
            Write-Info "仍在等待瀏覽器連線... （已等待 ${pairWaited} 秒）"
        }
    }

    if ($requestId) {
        Write-Info "偵測到配對請求：$requestId"
        docker compose exec openclaw-gateway openclaw devices approve $requestId 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "裝置配對完成！請重新整理瀏覽器頁面。"
        } else {
            Write-Host "[ERROR] 配對審批失敗，請手動執行：" -ForegroundColor Red
            Write-Host "  docker compose exec openclaw-gateway openclaw devices approve $requestId" -ForegroundColor Yellow
        }
    } else {
        Write-Warn "等待逾時，未偵測到配對請求。"
        Write-Warn "您可稍後手動執行以下指令完成配對："
        Write-Host "  docker compose exec openclaw-gateway openclaw devices list" -ForegroundColor Yellow
        Write-Host "  docker compose exec openclaw-gateway openclaw devices approve <Request ID>" -ForegroundColor Yellow
    }
} else {
    Write-Info "略過裝置配對。您可稍後手動執行："
    Write-Host "  docker compose exec openclaw-gateway openclaw devices list" -ForegroundColor Yellow
    Write-Host "  docker compose exec openclaw-gateway openclaw devices approve <Request ID>" -ForegroundColor Yellow
}
