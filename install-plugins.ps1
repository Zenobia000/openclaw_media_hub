# ============================================================
# install-plugins.ps1 — 安裝與設定 OpenClaw 插件 (LINE / Discord)
#
# 用法：.\install-plugins.ps1
#
# 流程：
#   1. 安裝 LINE 插件
#   2. 安裝 Discord 插件
# ============================================================

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ScriptDir    = Split-Path -Parent $MyInvocation.MyCommand.Definition
$OpenClawDir  = Join-Path $ScriptDir ".openclaw"
$ConfigFile   = Join-Path $OpenClawDir "openclaw.json"
$HealthUrl    = "http://127.0.0.1:18789/healthz"
$SpinChars    = @('|', '/', '-', '\')

# ── 輸出工具 ─────────────────────────────────────────────────

function Write-Info  { param($Msg) Write-Host "[INFO]  $Msg" -ForegroundColor Blue }
function Write-Ok    { param($Msg) Write-Host "[OK]    $Msg" -ForegroundColor Green }
function Write-Warn  { param($Msg) Write-Host "[WARN]  $Msg" -ForegroundColor Yellow }
function Write-Err   { param($Msg) Write-Host "[ERROR] $Msg" -ForegroundColor Red }

# ── Y/n 確認提示 ─────────────────────────────────────────────

function Confirm-YesNo {
    param([string]$Prompt)
    $answer = Read-Host "$Prompt (Y/n)"
    return ($answer -ne 'n' -and $answer -ne 'N')
}

# ── 非空輸入提示（支援 n 略過）────────────────────────────────

function Read-NonEmpty {
    param([string]$Prompt)
    do {
        $value = Read-Host $Prompt
        if ([string]::IsNullOrWhiteSpace($value)) {
            Write-Warn "不可空白，請重新輸入或輸入 n 略過。"
        }
    } while ([string]::IsNullOrWhiteSpace($value))
    return $value
}

# ── 執行 Gateway CLI 指令 ────────────────────────────────────

function Invoke-Gateway {
    param([string[]]$GwArgs)
    $null = docker compose exec openclaw-gateway openclaw @GwArgs 2>&1
    return ($LASTEXITCODE -eq 0)
}

# ── 等待 Gateway 就緒（含 spinner）───────────────────────────

function Wait-Gateway {
    param(
        [string]$Label = "等待 Gateway 就緒",
        [int]$Timeout  = 30
    )
    Write-Host -NoNewline "[INFO]  $Label... " -ForegroundColor Blue
    for ($i = 0; $i -lt $Timeout; $i++) {
        Write-Host -NoNewline "`b$($SpinChars[$i % 4])" -ForegroundColor Cyan
        try {
            $health = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 2 -ErrorAction Stop
            if ($health.ok -eq $true) {
                Write-Host "`b "
                Write-Ok "$Label — 完成（${i} 秒）"
                return $true
            }
        } catch { }
        Start-Sleep -Seconds 1
    }
    Write-Host "`b "
    Write-Warn "$Label — 逾時（${Timeout} 秒）"
    return $false
}

# ── 重啟 Docker Compose 並等待就緒 ───────────────────────────

function Restart-AndWait {
    param([string]$Reason = "套用設定")
    Write-Host ""
    Write-Info "正在重新啟動服務以${Reason}..."
    try {
        docker compose restart
        if ($LASTEXITCODE -ne 0) { throw "docker compose restart 失敗" }
        Write-Ok "服務已重新啟動"
    } catch {
        Write-Err "無法重新啟動服務：$_"
        return $false
    }
    Write-Host ""
    return (Wait-Gateway -Label "等待 Gateway 重新就緒")
}

# ── 寫入頻道設定到 openclaw.json ─────────────────────────────

function Set-ChannelConfig {
    param(
        [string]$Channel,
        [PSCustomObject]$Settings
    )
    try {
        $config = Get-Content -Path $ConfigFile -Raw | ConvertFrom-Json
        if (-not $config.PSObject.Properties['channels']) {
            $config | Add-Member -MemberType NoteProperty -Name 'channels' -Value ([PSCustomObject]@{})
        }
        if ($config.channels.PSObject.Properties[$Channel]) {
            $config.channels.$Channel = $Settings
        } else {
            $config.channels | Add-Member -MemberType NoteProperty -Name $Channel -Value $Settings
        }
        $config | ConvertTo-Json -Depth 10 | Set-Content -Path $ConfigFile -Encoding UTF8
        Write-Ok "$Channel 設定已寫入 .openclaw\openclaw.json"
        return $true
    } catch {
        Write-Err "無法寫入 ${Channel} 設定：$_"
        return $false
    }
}

# ── 插件安裝完整流程（安裝 → 設定 → 重啟 → 配對）─────────────

function Install-Plugin {
    param(
        [string]$Name,              # 顯示名稱（LINE / Discord）
        [string]$Package,           # 插件套件名（@openclaw/line）
        [string]$Channel,           # 頻道鍵名（line / discord）
        [hashtable]$CredentialPrompts, # @{ "欄位名" = "提示文字" }
        [scriptblock]$BuildConfig   # 接收 credentials hashtable，回傳 PSCustomObject
    )

    Write-Host ""
    if (-not (Confirm-YesNo "是否要安裝 $Name 插件？")) {
        Write-Info "略過 $Name 插件安裝。您可稍後手動執行："
        Write-Host "  docker compose exec openclaw-gateway openclaw plugins install $Package" -ForegroundColor Yellow
        return
    }

    # 安裝插件
    Write-Info "正在安裝 $Name 插件 ($Package)..."
    if (-not (Invoke-Gateway plugins, install, $Package)) {
        Write-Warn "$Name 插件安裝失敗。您可稍後手動執行："
        Write-Host "  docker compose exec openclaw-gateway openclaw plugins install $Package" -ForegroundColor Yellow
    } else {
        Write-Ok "$Name 插件安裝完成"
    }

    # 收集憑證
    Write-Host ""
    Write-Info "設定 $Name 資訊..."
    $creds = @{}
    foreach ($entry in $CredentialPrompts.GetEnumerator()) {
        $creds[$entry.Key] = Read-Host $entry.Value
    }

    # 檢查是否有空值
    $hasEmpty = $creds.Values | Where-Object { [string]::IsNullOrWhiteSpace($_) }
    if ($hasEmpty) {
        Write-Warn "部分欄位為空，略過設定。您可稍後手動編輯 .openclaw\openclaw.json"
    } else {
        $settings = & $BuildConfig $creds
        Set-ChannelConfig -Channel $Channel -Settings $settings
    }

    # 重啟以套用插件設定
    $ready = Restart-AndWait -Reason "套用 $Name 插件設定"

    # ngrok（僅 LINE 需要）
    if ($Channel -eq 'line') {
        Start-NgrokTunnel
    }

    # 配對流程
    Write-Host ""
    Write-Info "$Name 配對流程："
    Write-Host "  1. 傳送任意訊息給 $Name Bot" -ForegroundColor Cyan
    Write-Host "  2. Bot 會回傳一組配對碼" -ForegroundColor Cyan
    Write-Host ""
    $code = Read-NonEmpty "取得配對碼後輸入（輸入 n 略過）"

    if ($code -ne 'n' -and $code -ne 'N') {
        Write-Info "正在執行 $Name 配對審批..."
        if (Invoke-Gateway pairing, approve, $Channel, $code) {
            Write-Ok "$Name 配對完成！"
        } else {
            Write-Err "$Name 配對失敗，請手動執行："
            Write-Host "  docker compose exec openclaw-gateway openclaw pairing approve $Channel <配對碼>" -ForegroundColor Yellow
        }
    } else {
        Write-Info "略過 $Name 配對。您可稍後手動執行："
        Write-Host "  docker compose exec openclaw-gateway openclaw pairing approve $Channel <配對碼>" -ForegroundColor Yellow
    }
}

# ── 啟動 ngrok tunnel ────────────────────────────────────────

function Start-NgrokTunnel {
    Write-Host ""
    Write-Info "LINE Webhook 需要公開 HTTPS URL，正在檢查 ngrok..."

    if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
        Write-Err "未偵測到 ngrok。請先安裝：https://ngrok.com/download"
        Write-Host "  安裝後執行 'ngrok config add-authtoken <你的token>' 完成設定" -ForegroundColor Yellow
        return
    }

    # 檢查是否已有 tunnel
    $ngrokUrl = $null
    try {
        $api = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3 -ErrorAction Stop
        $existing = $api.tunnels | Where-Object { $_.config.addr -match "18789" -and $_.proto -eq "https" } | Select-Object -First 1
        if ($existing) { $ngrokUrl = $existing.public_url; Write-Info "偵測到已存在的 tunnel：$ngrokUrl" }
    } catch { }

    if (-not $ngrokUrl) {
        Write-Info "正在背景啟動 ngrok http 18789..."
        Start-Process ngrok -ArgumentList "http", "18789" -WindowStyle Minimized
        for ($i = 0; $i -lt 10; $i++) {
            Start-Sleep -Seconds 2
            try {
                $api = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3 -ErrorAction Stop
                $tunnel = $api.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1
                if ($tunnel) { $ngrokUrl = $tunnel.public_url; break }
            } catch { }
        }
        if ($ngrokUrl) { Write-Ok "ngrok tunnel 已啟動" }
        else { Write-Err "ngrok 未在 20 秒內就緒，請手動執行 'ngrok http 18789'"; return }
    }

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
    Write-Host "  1. 開啟 https://developers.line.biz/console/" -ForegroundColor Cyan
    Write-Host "  2. 選擇 Provider → Channel → Messaging API settings" -ForegroundColor Cyan
    Write-Host "  3. 貼上 Webhook URL，開啟 Use webhook，點擊 Verify" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "完成上述設定後，按 Enter 繼續"

    # ── Webhook 驗證結果檢查迴圈 ──
    $verified = $false
    while (-not $verified) {
        Write-Host ""
        Write-Info "正在檢查 Webhook 驗證結果..."

        $latestReq = $null
        try {
            $inspectData = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/requests/http" -TimeoutSec 5 -ErrorAction Stop
            $latestReq = $inspectData.requests |
                Where-Object { $_.request.uri -match "/line/webhook" } |
                Select-Object -First 1
        } catch { }

        if (-not $latestReq) {
            Write-Warn "未偵測到 Webhook 驗證請求。"
            Write-Info "如果您已在 LINE Console 完成驗證且顯示成功，可直接繼續。"
            if (-not (Confirm-YesNo "是否重新檢查？")) { $verified = $true }
            continue
        }

        # 解析 HTTP 狀態碼（支援 "401 Unauthorized" 或純數字）
        $statusRaw = "$($latestReq.response.status)"
        if ($statusRaw -match '(\d{3})') { $statusCode = [int]$Matches[1] } else { $statusCode = 0 }

        if ($statusCode -eq 200) {
            Write-Ok "LINE Webhook 驗證成功！"
            $verified = $true

        } elseif ($statusCode -eq 401) {
            Write-Err "LINE Webhook 驗證失敗：$statusRaw"
            Write-Host ""
            Write-Warn "這通常表示 Channel Access Token 或 Channel Secret 設定不正確。"
            Write-Warn "請確認您在 LINE Developers Console 複製的是正確的值。"
            Write-Host ""
            Write-Host "  1. 重新輸入 LINE 憑證並重試驗證" -ForegroundColor Cyan
            Write-Host "  2. 略過驗證，繼續後續流程" -ForegroundColor Cyan
            Write-Host ""
            $choice = Read-Host "請選擇 (1/2)"

            if ($choice -eq '1') {
                $newToken  = Read-Host "請重新輸入 Channel Access Token"
                $newSecret = Read-Host "請重新輸入 Channel Secret"

                if ([string]::IsNullOrWhiteSpace($newToken) -or [string]::IsNullOrWhiteSpace($newSecret)) {
                    Write-Warn "憑證不可為空，請重試。"
                    continue
                }

                $settings = [PSCustomObject]@{
                    enabled            = $true
                    channelAccessToken = $newToken
                    channelSecret      = $newSecret
                    dmPolicy           = "open"
                }
                Set-ChannelConfig -Channel "line" -Settings $settings
                if (-not (Restart-AndWait -Reason "套用新的 LINE 憑證")) {
                    Write-Err "Gateway 未就緒，請手動檢查容器狀態。"
                    $verified = $true
                    continue
                }
                Write-Host ""
                Write-Info "請再次至 LINE Developers Console 點擊 Verify 按鈕"
                Read-Host "驗證後按 Enter 繼續"
            } else {
                Write-Info "略過 Webhook 驗證。"
                $verified = $true
            }

        } else {
            Write-Err "LINE Webhook 驗證失敗：HTTP $statusCode"
            Write-Warn "請檢查 Gateway 服務是否正常運作。"
            if (-not (Confirm-YesNo "是否重試？")) { $verified = $true }
        }
    }
}

# ════════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════════

Write-Host ""
Write-Info "開始安裝與設定 OpenClaw 插件..."

# LINE 插件
Install-Plugin `
    -Name "LINE" `
    -Package "@openclaw/line" `
    -Channel "line" `
    -CredentialPrompts ([ordered]@{
        channelAccessToken = "請輸入 Channel Access Token"
        channelSecret      = "請輸入 Channel Secret"
    }) `
    -BuildConfig {
        param($c)
        [PSCustomObject]@{
            enabled            = $true
            channelAccessToken = $c.channelAccessToken
            channelSecret      = $c.channelSecret
            dmPolicy           = "open"
        }
    }

# Discord 插件
Install-Plugin `
    -Name "Discord" `
    -Package "@openclaw/discord" `
    -Channel "discord" `
    -CredentialPrompts ([ordered]@{
        token = "請輸入 Discord Bot Token"
    }) `
    -BuildConfig {
        param($c)
        [PSCustomObject]@{
            enabled     = $true
            token       = $c.token
            groupPolicy = "allowlist"
            dmPolicy    = "open"
            streaming   = "off"
        }
    }

Write-Host ""
Write-Ok "插件安裝與設定流程結束！"
