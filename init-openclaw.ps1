# ============================================================
# init-openclaw.ps1 — 初始化 .openclaw 目錄結構與插件設定
#
# 用法：.\init-openclaw.ps1
#
# 流程：
#   1. 建立 .openclaw 目錄結構
#   2. 部署技能（module_pack → workspace\skills）
#   3. 產生 openclaw.json（Gateway 設定）
#   4. 複製 .env.example → .env
#   5. 啟動 Docker Compose
#   6. 設定 API 金鑰（可多組，迴圈詢問）
#   7. 啟用語音轉文字（OpenAI Whisper）
#   8. 安裝插件（LINE / Discord）
#   9. 裝置配對
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
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $null = docker compose exec openclaw-gateway openclaw @GwArgs 2>&1
    $ErrorActionPreference = $prev
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

# ── 解析 SKILL.md frontmatter ────────────────────────────────

function Get-SkillMeta {
    param([string]$Path)
    $content = Get-Content -Path $Path -Raw
    $emoji = "📦"; $desc = "(無描述)"

    if ($content -match '(?s)^---\r?\n(.+?)\r?\n---') {
        $yaml = $Matches[1]
        if ($yaml -match 'emoji:\s*(.+)') {
            $e = $Matches[1].Trim().Trim('"').Trim("'")
            if ($e) { $emoji = $e }
        }
        # 優先處理 block scalar（| 或 >），再處理單行
        if ($yaml -match '(?m)^description:\s*[|>]\s*\r?\n((?:\s{2,}.+\r?\n?)+)') {
            $first = ($Matches[1] -split '\r?\n')[0].Trim()
            if ($first) { $desc = $first }
        }
        elseif ($yaml -match '(?m)^description:\s*"([^"]+)"')              { $desc = $Matches[1].Trim() }
        elseif ($yaml -match "(?m)^description:\s*'([^']+)'")              { $desc = $Matches[1].Trim() }
        elseif ($yaml -match '(?m)^description:\s*([^\r\n|>].+)')          { $desc = $Matches[1].Trim() }
    }
    return @{ Emoji = $emoji; Description = $desc }
}

# ── 安全設定游標位置 ─────────────────────────────────────────

function Safe-SetCursorPosition {
    param([int]$X, [int]$Y)
    $maxX = [Math]::Max(0, [Console]::BufferWidth - 1)
    $maxY = [Math]::Max(0, [Console]::BufferHeight - 1)
    [Console]::SetCursorPosition(
        [Math]::Clamp($X, 0, $maxX),
        [Math]::Clamp($Y, 0, $maxY)
    )
}

# ── 清除指定行數（從 startY 開始）────────────────────────────

function Clear-Lines {
    param([int]$StartY, [int]$Count, [int]$Width)
    for ($i = 0; $i -lt $Count; $i++) {
        Safe-SetCursorPosition -X 0 -Y ($StartY + $i)
        [Console]::Write((" " * [Math]::Min($Width, 200)))
    }
    Safe-SetCursorPosition -X 0 -Y $StartY
}

# ── 互動式技能選擇介面 ──────────────────────────────────────

function Show-SkillSelector {
    param([array]$Skills)

    $selected = [bool[]]($Skills | ForEach-Object { [bool]$_.Installed })
    $cursor = 0; $search = ""; $lastLineCount = 0

    # 預留空間避免捲動
    $requiredLines = $Skills.Count + 6
    $available = [Console]::BufferHeight - [Console]::CursorTop - 1
    if ($available -lt $requiredLines) {
        1..($requiredLines - $available) | ForEach-Object { Write-Host "" }
    }

    $startY = [Console]::CursorTop
    try { $width = [Console]::WindowWidth } catch { $width = 80 }

    while ($true) {
        # 篩選符合搜尋的技能索引
        $filtered = @()
        for ($i = 0; $i -lt $Skills.Count; $i++) {
            if ([string]::IsNullOrEmpty($search) -or
                $Skills[$i].Name -like "*$search*" -or
                $Skills[$i].Description -like "*$search*") {
                $filtered += $i
            }
        }

        # 限制游標範圍
        if ($filtered.Count -eq 0) { $cursor = 0 }
        elseif ($cursor -ge $filtered.Count) { $cursor = $filtered.Count - 1 }

        $selCount = ($selected | Where-Object { $_ }).Count

        # ── 繪製 UI ──
        [Console]::CursorVisible = $false
        try { $width = [Console]::WindowWidth } catch { $width = 80 }
        Clear-Lines -StartY $startY -Count $lastLineCount -Width $width

        $lineCount = 0

        Write-Host "◆  OpenClaw 初始安裝技能工具" -ForegroundColor Cyan; $lineCount++
        Write-Host "│"; $lineCount++

        Write-Host "│  搜尋: " -NoNewline -ForegroundColor White
        Write-Host "$search" -NoNewline -ForegroundColor Yellow
        Write-Host "_"; $lineCount++

        foreach ($fi in 0..([Math]::Max(0, $filtered.Count - 1))) {
            if ($filtered.Count -eq 0) { break }
            $idx = $filtered[$fi]
            $s = $Skills[$idx]
            $check = if ($selected[$idx]) { "◼" } else { "◻" }
            $tag = if ($s.Installed) { " (已安裝)" } else { "" }
            $desc = if ($s.Description.Length -gt 50) { $s.Description.Substring(0, 47) + "..." } else { $s.Description }
            $color = if ($fi -eq $cursor) { "Cyan" } elseif ($s.Installed) { "DarkGray" } else { "White" }
            Write-Host "│  $check $($s.Emoji) $($s.Name) — $desc$tag" -ForegroundColor $color
            $lineCount++
        }

        if ($filtered.Count -eq 0) {
            Write-Host "│  （無符合的技能）" -ForegroundColor DarkGray; $lineCount++
        }

        Write-Host "│"; $lineCount++

        $status = if ($selCount -gt 0) { "(已選 $selCount 個)" } else { "(未選擇任何技能)" }
        Write-Host "│  ↑/↓ 移動 • Space/Tab: 選取 • Enter: 確認 • Ctrl+A: 全選 • Esc: 取消  $status" -ForegroundColor DarkGray
        $lineCount++

        $lastLineCount = $lineCount

        # 校正捲動偏移
        $currentBottom = [Console]::CursorTop
        if ($currentBottom -lt ($startY + $lineCount)) {
            $startY = [Math]::Max(0, $currentBottom - $lineCount)
        }

        # ── 按鍵處理 ──
        [Console]::CursorVisible = $true
        $key = [Console]::ReadKey($true)

        switch ($key.Key) {
            'UpArrow'   { if ($cursor -gt 0) { $cursor-- } }
            'DownArrow' { if ($filtered.Count -gt 0 -and $cursor -lt $filtered.Count - 1) { $cursor++ } }
            { $_ -eq 'Tab' -or $_ -eq 'Spacebar' } {
                if ($filtered.Count -gt 0) { $selected[$filtered[$cursor]] = -not $selected[$filtered[$cursor]] }
            }
            'Enter' {
                $result = @(0..($Skills.Count - 1) | Where-Object { $selected[$_] })
                [Console]::CursorVisible = $false
                Clear-Lines -StartY $startY -Count $lastLineCount -Width $width
                Write-Host "◇  OpenClaw 初始安裝技能工具" -ForegroundColor Cyan
                if ($result.Count -gt 0) {
                    $names = ($result | ForEach-Object { "$($Skills[$_].Emoji) $($Skills[$_].Name)" }) -join ", "
                    Write-Host "│  已選擇: $names" -ForegroundColor Green
                } else {
                    Write-Host "│  未選擇任何技能" -ForegroundColor DarkGray
                }
                Write-Host ""; [Console]::CursorVisible = $true
                return ,@($result)
            }
            'Escape' {
                [Console]::CursorVisible = $false
                Clear-Lines -StartY $startY -Count $lastLineCount -Width $width
                Write-Host "◇  OpenClaw 初始安裝技能工具" -ForegroundColor DarkGray
                Write-Host "│  已取消" -ForegroundColor DarkGray
                Write-Host ""; [Console]::CursorVisible = $true
                return $null
            }
            'Backspace' {
                if ($search.Length -gt 0) { $search = $search.Substring(0, $search.Length - 1) }
            }
            default {
                if ($key.Modifiers -band [ConsoleModifiers]::Control -and $key.Key -eq 'A') {
                    $allSelected = -not ($filtered | Where-Object { -not $selected[$_] })
                    foreach ($fi in $filtered) { $selected[$fi] = -not $allSelected }
                }
                elseif ($key.KeyChar -and -not [char]::IsControl($key.KeyChar) -and
                        -not ($key.Modifiers -band [ConsoleModifiers]::Alt)) {
                    $search += $key.KeyChar
                }
            }
        }
    }
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
    $rel = $dir.Replace("$ScriptDir\", "")
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Ok "建立目錄：$rel"
    } else {
        Write-Info "目錄已存在：$rel（略過）"
    }
}

# 2. 部署技能
$modulePackDir   = Join-Path $ScriptDir "module_pack"
$skillsTargetDir = Join-Path $OpenClawDir "workspace\skills"

if (Test-Path $modulePackDir) {
    Write-Info "掃描 module_pack 中的技能..."
    $skillFiles = Get-ChildItem -Path $modulePackDir -Recurse -Filter "SKILL.md"

    if ($skillFiles.Count -eq 0) {
        Write-Info "module_pack 中未找到任何技能。"
    } else {
        $skills = $skillFiles | ForEach-Object {
            $meta = Get-SkillMeta -Path $_.FullName
            [PSCustomObject]@{
                Name        = $_.Directory.Name
                Emoji       = $meta.Emoji
                Description = $meta.Description
                SourceDir   = $_.Directory.FullName
                Installed   = Test-Path (Join-Path $skillsTargetDir $_.Directory.Name)
            }
        }

        $selectedIndices = Show-SkillSelector -Skills $skills

        if ($null -ne $selectedIndices) {
            $installed = 0; $removed = 0; $skipped = 0
            for ($i = 0; $i -lt $skills.Count; $i++) {
                $s = $skills[$i]
                $isSelected = $selectedIndices -contains $i
                $targetDir  = Join-Path $skillsTargetDir $s.Name

                if ($isSelected -and -not $s.Installed) {
                    Copy-Item -Path $s.SourceDir -Destination $targetDir -Recurse
                    Write-Ok "部署技能：$($s.Emoji) $($s.Name)"
                    $installed++
                } elseif (-not $isSelected -and $s.Installed) {
                    Remove-Item -Path $targetDir -Recurse -Force
                    Write-Ok "移除技能：$($s.Emoji) $($s.Name)"
                    $removed++
                } else {
                    $skipped++
                }
            }
            Write-Info "技能處理完成！新部署 $installed 個，移除 $removed 個，略過 $skipped 個。"
        } else {
            Write-Info "已取消任務，無更動。"
        }
    }
} else {
    Write-Warn "module_pack 目錄不存在，略過技能部署。"
}

# 3. 產生 openclaw.json
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

# 4. 複製 .env.example → .env
$envExample = Join-Path $ScriptDir ".env.example"
$envFile    = Join-Path $ScriptDir ".env"
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

# 5. 啟動 Docker Compose
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

# 6. 等待 Gateway 就緒
Write-Host ""
if (-not (Wait-Gateway -Label "等待 Gateway 啟動")) {
    Write-Err "Gateway 未就緒，請手動檢查容器狀態。"
    exit 1
}

# 7. 設定 API 金鑰（迴圈，可設定多組）
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

# 7b. 語音轉文字功能（需要 OpenAI API 金鑰）
Write-Host ""
Write-Info "語音轉文字功能可將語音訊息自動轉為文字（使用 OpenAI Whisper）。"
if (Confirm-YesNo "是否要啟用語音轉文字功能？（需要已設定 OpenAI API 金鑰）") {
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
                    profile  = "openai:default"
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
        Write-Ok "語音轉文字功能已啟用（language=zh, model=whisper-1）"
    } catch {
        Write-Err "無法寫入語音設定：$_"
    }
} else {
    Write-Info "略過語音轉文字功能。您可稍後手動編輯 .openclaw\openclaw.json 的 tools.media.audio 區段。"
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

# 8. 安裝插件

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

# 9. 裝置配對
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
