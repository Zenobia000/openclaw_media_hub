# ============================================================
# common.ps1 — OpenClaw 腳本共用函式庫
#
# 用法：在腳本開頭加入
#   . "$PSScriptRoot\common.ps1"
#
# 提供：
#   變數：$ProjectRoot, $OpenClawDir, $ConfigFile, $HealthUrl, $SpinChars
#   函式：Write-Info, Write-Ok, Write-Warn, Write-Err, Write-Fail,
#         Confirm-YesNo, Read-NonEmpty,
#         Invoke-Gateway, Wait-Gateway, Restart-AndWait,
#         Get-SkillMeta, Safe-SetCursorPosition, Clear-Lines,
#         Show-SkillSelector
# ============================================================

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ── 路徑常數 ─────────────────────────────────────────────────

$ProjectRoot  = Split-Path -Parent $PSScriptRoot
$OpenClawDir  = Join-Path $ProjectRoot ".openclaw"
$ConfigFile   = Join-Path $OpenClawDir "openclaw.json"
$HealthUrl    = "http://127.0.0.1:18789/healthz"
$SpinChars    = @('|', '/', '-', '\')

# 確保 docker compose 等指令使用專案根目錄
Set-Location $ProjectRoot

# ── 輸出工具 ─────────────────────────────────────────────────

function Write-Info { param($Msg) Write-Host "[INFO]  $Msg" -ForegroundColor Blue }
function Write-Ok   { param($Msg) Write-Host "[OK]    $Msg" -ForegroundColor Green }
function Write-Warn { param($Msg) Write-Host "[WARN]  $Msg" -ForegroundColor Yellow }
function Write-Err  { param($Msg) Write-Host "[ERROR] $Msg" -ForegroundColor Red }
function Write-Fail { param($Msg) Write-Host "[FAIL]  $Msg" -ForegroundColor Red }

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
        [Math]::Min([Math]::Max($X, 0), $maxX),
        [Math]::Min([Math]::Max($Y, 0), $maxY)
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
    param(
        [array]$Skills,
        [string]$Title = "OpenClaw 技能選擇工具"
    )

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

        Write-Host "◆  $Title" -ForegroundColor Cyan; $lineCount++
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
                Write-Host "◇  $Title" -ForegroundColor Cyan
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
                Write-Host "◇  $Title" -ForegroundColor DarkGray
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
