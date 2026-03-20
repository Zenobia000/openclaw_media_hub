# ============================================================
# install_skill_hub.ps1 — 互動式安裝 skill_hub 擴充技能
#
# 用法：
#   .\install_skill_hub.ps1
#
# 此腳本會：
#   1. 掃描 skill_hub/ 中含 SKILL.md 的技能目錄
#   2. 顯示互動式選擇介面供使用者挑選
#   3. 將選擇的技能複製至 .openclaw/workspace/skills/
# ============================================================

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SkillHubDir = Join-Path $ScriptDir "skill_hub"
$SkillsTargetDir = Join-Path $ScriptDir ".openclaw\workspace\skills"

# ── 顏色輸出 ────────────────────────────────────────────────
function Write-Info  { param($Msg) Write-Host "[INFO]  $Msg" -ForegroundColor Blue }
function Write-Ok    { param($Msg) Write-Host "[OK]    $Msg" -ForegroundColor Green }
function Write-Warn  { param($Msg) Write-Host "[WARN]  $Msg" -ForegroundColor Yellow }

# ── UTF-8 輸出 ────────────────────────────────────────────────
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ── 檢查 skill_hub 目錄 ──────────────────────────────────────
if (-not (Test-Path $SkillHubDir)) {
    Write-Warn "skill_hub 目錄不存在，無可安裝的擴充技能。"
    exit 0
}

# ── 掃描技能 ──────────────────────────────────────────────────
$skillFiles = Get-ChildItem -Path $SkillHubDir -Recurse -Filter "SKILL.md"

if ($skillFiles.Count -eq 0) {
    Write-Warn "skill_hub 中未找到任何技能（無 SKILL.md）。"
    exit 0
}

$skillDirs = $skillFiles | ForEach-Object { $_.Directory }

# ── 解析 SKILL.md frontmatter ─────────────────────────────────
function Get-SkillMeta {
    param([string]$SkillMdPath)

    $content = Get-Content -Path $SkillMdPath -Raw
    $emoji = "📦"
    $description = "(無描述)"

    # 取得 YAML frontmatter 區塊
    if ($content -match '(?s)^---\r?\n(.+?)\r?\n---') {
        $yaml = $Matches[1]

        # 解析 emoji
        if ($yaml -match 'emoji:\s*(.+)') {
            $e = $Matches[1].Trim().Trim('"').Trim("'")
            if ($e) { $emoji = $e }
        }

        # 解析 description — block scalar（| 或 >）
        if ($yaml -match '(?m)^description:\s*[|>]\s*\r?\n((?:\s{2,}.+\r?\n?)+)') {
            $firstLine = ($Matches[1] -split '\r?\n')[0].Trim()
            if ($firstLine) { $description = $firstLine }
        }
        # 解析 description — 引號或無引號單行
        elseif ($yaml -match '(?m)^description:\s*"([^"]+)"') {
            $description = $Matches[1].Trim()
        }
        elseif ($yaml -match "(?m)^description:\s*'([^']+)'") {
            $description = $Matches[1].Trim()
        }
        elseif ($yaml -match '(?m)^description:\s*([^\r\n|>].+)') {
            $description = $Matches[1].Trim()
        }
    }

    return @{
        Emoji       = $emoji
        Description = $description
    }
}

# ── 建立技能清單 ──────────────────────────────────────────────
$skills = @()
foreach ($skillDir in $skillDirs) {
    $skillName = $skillDir.Name
    $skillMdPath = Join-Path $skillDir.FullName "SKILL.md"
    $meta = Get-SkillMeta -SkillMdPath $skillMdPath
    $installed = Test-Path (Join-Path $SkillsTargetDir $skillName)

    $skills += [PSCustomObject]@{
        Name        = $skillName
        Emoji       = $meta.Emoji
        Description = $meta.Description
        SourceDir   = $skillDir.FullName
        Installed   = $installed
    }
}

# ── 安全設定游標位置（clamp 到合法範圍）────────────────────────
function Safe-SetCursorPosition {
    param([int]$X, [int]$Y)
    $maxX = [Math]::Max(0, [Console]::BufferWidth - 1)
    $maxY = [Math]::Max(0, [Console]::BufferHeight - 1)
    $clampedX = [Math]::Max(0, [Math]::Min($X, $maxX))
    $clampedY = [Math]::Max(0, [Math]::Min($Y, $maxY))
    [Console]::SetCursorPosition($clampedX, $clampedY)
}

# ── 互動式選擇介面 ───────────────────────────────────────────
function Show-SkillSelector {
    param([array]$Skills)

    $selected = New-Object bool[] $Skills.Count
    for ($i = 0; $i -lt $Skills.Count; $i++) {
        $selected[$i] = [bool]$Skills[$i].Installed
    }
    $cursor = 0
    $search = ""
    $lastLineCount = 0

    # 預先確保有足夠的空行，避免後續繪製時發生捲動
    $requiredLines = $Skills.Count + 6  # 標題 + 搜尋欄 + 技能數 + 提示 + 空行等
    $availableLines = [Console]::BufferHeight - [Console]::CursorTop - 1
    if ($availableLines -lt $requiredLines) {
        # 輸出空行迫使終端先捲動，騰出空間
        $linesToScroll = $requiredLines - $availableLines
        for ($p = 0; $p -lt $linesToScroll; $p++) {
            Write-Host ""
        }
    }

    # 記錄起始 Y 座標，用於重繪
    $startY = [Console]::CursorTop
    try { $width = [Console]::WindowWidth } catch { $width = 80 }

    while ($true) {
        # ── 計算篩選結果 ──
        $filtered = @()
        for ($i = 0; $i -lt $Skills.Count; $i++) {
            if ([string]::IsNullOrEmpty($search) -or
                $Skills[$i].Name -like "*$search*" -or
                $Skills[$i].Description -like "*$search*") {
                $filtered += $i
            }
        }

        # 限制 cursor 範圍
        if ($filtered.Count -eq 0) {
            $cursor = 0
        } elseif ($cursor -ge $filtered.Count) {
            $cursor = $filtered.Count - 1
        }

        # 計算已選數量
        $selCount = ($selected | Where-Object { $_ }).Count

        # ── 重繪 ──
        [Console]::CursorVisible = $false
        try { $width = [Console]::WindowWidth } catch { $width = 80 }

        # 清除上一次繪製的所有行
        for ($cl = 0; $cl -lt $lastLineCount; $cl++) {
            Safe-SetCursorPosition -X 0 -Y ($startY + $cl)
            [Console]::Write((" " * [Math]::Min($width, 200)))
        }
        Safe-SetCursorPosition -X 0 -Y $startY

        $lineCount = 0

        # 標題
        Write-Host "◆  OpenClaw Skill Hub 安裝工具" -ForegroundColor Cyan
        $lineCount++

        Write-Host "│"
        $lineCount++

        # 搜尋欄
        Write-Host "│  搜尋: " -NoNewline -ForegroundColor White
        Write-Host "$search" -NoNewline -ForegroundColor Yellow
        Write-Host "_"
        $lineCount++

        # 技能列表
        for ($fi = 0; $fi -lt $filtered.Count; $fi++) {
            $idx = $filtered[$fi]
            $s = $Skills[$idx]
            $check = if ($selected[$idx]) { "◼" } else { "◻" }
            $tag = if ($s.Installed) { " (已安裝)" } else { "" }
            $desc = $s.Description
            if ($desc.Length -gt 50) { $desc = $desc.Substring(0, 47) + "..." }
            $line = "$check $($s.Emoji) $($s.Name) — $desc$tag"

            if ($fi -eq $cursor) {
                $color = "Cyan"
            } elseif ($s.Installed) {
                $color = "DarkGray"
            } else {
                $color = "White"
            }

            Write-Host "│  $line" -ForegroundColor $color
            $lineCount++
        }

        if ($filtered.Count -eq 0) {
            Write-Host "│  （無符合的技能）" -ForegroundColor DarkGray
            $lineCount++
        }

        Write-Host "│"
        $lineCount++

        # 操作提示
        $hint = "│  ↑/↓ 移動 • Space/Tab: 選取 • Enter: 確認 • Ctrl+A: 全選 • Esc: 取消"
        if ($selCount -gt 0) { 
            $hint += "  (已選 $selCount 個)" 
        } else {
            $hint += "  (未選擇任何技能)"
        }
        Write-Host $hint -ForegroundColor DarkGray
        $lineCount++

        $lastLineCount = $lineCount

        # 重新校正 startY：如果內容導致終端捲動，CursorTop 會改變
        $currentBottom = [Console]::CursorTop
        $expectedBottom = $startY + $lineCount
        if ($currentBottom -lt $expectedBottom) {
            # 發生了捲動，調整 startY
            $startY = $currentBottom - $lineCount
            if ($startY -lt 0) { $startY = 0 }
        }

        # ── 讀取按鍵 ──
        [Console]::CursorVisible = $true
        $key = [Console]::ReadKey($true)

        switch ($key.Key) {
            'UpArrow' {
                if ($cursor -gt 0) { $cursor-- }
            }
            'DownArrow' {
                if ($filtered.Count -gt 0 -and $cursor -lt $filtered.Count - 1) { $cursor++ }
            }
            { $_ -eq 'Tab' -or $_ -eq 'Spacebar' } {
                if ($filtered.Count -gt 0) {
                    $idx = $filtered[$cursor]
                    $selected[$idx] = -not $selected[$idx]
                }
            }
            'Enter' {
                $result = @()
                for ($i = 0; $i -lt $Skills.Count; $i++) {
                    if ($selected[$i]) { $result += $i }
                }

                # 最終畫面：替換為摘要
                [Console]::CursorVisible = $false
                for ($cl = 0; $cl -lt $lastLineCount; $cl++) {
                    Safe-SetCursorPosition -X 0 -Y ($startY + $cl)
                    [Console]::Write((" " * [Math]::Min($width, 200)))
                }
                Safe-SetCursorPosition -X 0 -Y $startY

                Write-Host "◇  OpenClaw Skill Hub 安裝工具" -ForegroundColor Cyan
                if ($result.Count -gt 0) {
                    $names = ($result | ForEach-Object { "$($Skills[$_].Emoji) $($Skills[$_].Name)" }) -join ", "
                    Write-Host "│  已選擇: $names" -ForegroundColor Green
                } else {
                    Write-Host "│  未選擇任何技能" -ForegroundColor DarkGray
                }
                Write-Host ""
                [Console]::CursorVisible = $true
                return ,@($result)
            }
            'Escape' {
                # 最終畫面：取消
                [Console]::CursorVisible = $false
                for ($cl = 0; $cl -lt $lastLineCount; $cl++) {
                    Safe-SetCursorPosition -X 0 -Y ($startY + $cl)
                    [Console]::Write((" " * [Math]::Min($width, 200)))
                }
                Safe-SetCursorPosition -X 0 -Y $startY

                Write-Host "◇  OpenClaw Skill Hub 安裝工具" -ForegroundColor DarkGray
                Write-Host "│  已取消" -ForegroundColor DarkGray
                Write-Host ""
                [Console]::CursorVisible = $true
                return $null
            }
            'Backspace' {
                if ($search.Length -gt 0) {
                    $search = $search.Substring(0, $search.Length - 1)
                }
            }
            default {
                # Ctrl+A：全選/全取消（作用於目前篩選結果）
                if ($key.Modifiers -band [ConsoleModifiers]::Control -and $key.Key -eq 'A') {
                    $anyUnselected = $false
                    foreach ($fi in $filtered) {
                        if (-not $selected[$fi]) { $anyUnselected = $true; break }
                    }
                    foreach ($fi in $filtered) {
                        $selected[$fi] = $anyUnselected
                    }
                }
                # 一般字元：加入搜尋
                elseif ($key.KeyChar -and -not [char]::IsControl($key.KeyChar) -and
                        -not ($key.Modifiers -band [ConsoleModifiers]::Alt)) {
                    $search += $key.KeyChar
                }
            }
        }
    }
}

# ── 執行選擇 ─────────────────────────────────────────────────
$selectedIndices = Show-SkillSelector -Skills $skills

# 處理取消或未選擇
if ($null -eq $selectedIndices) {
    exit 0
}

# ── 確保目標目錄存在 ──────────────────────────────────────────
if (-not (Test-Path $SkillsTargetDir)) {
    New-Item -ItemType Directory -Path $SkillsTargetDir -Force | Out-Null
    Write-Ok "建立目錄：.openclaw\workspace\skills"
}

# ── 安裝與移除技能 ──────────────────────────────────────────────────
$countInstalled = 0
$countRemoved = 0
$countSkipped = 0

for ($i = 0; $i -lt $skills.Count; $i++) {
    $s = $skills[$i]
    $isSelected = $selectedIndices -contains $i
    $targetDir = Join-Path $SkillsTargetDir $s.Name

    if ($isSelected -and -not $s.Installed) {
        Copy-Item -Path $s.SourceDir -Destination $targetDir -Recurse
        Write-Ok "安裝技能：$($s.Emoji) $($s.Name) → .openclaw\workspace\skills\$($s.Name)"
        $countInstalled++
    } elseif (-not $isSelected -and $s.Installed) {
        if (Test-Path $targetDir) {
            Remove-Item -Path $targetDir -Recurse -Force
            Write-Ok "移除技能：$($s.Emoji) $($s.Name)"
            $countRemoved++
        }
    } else {
        $countSkipped++
    }
}

# ── 摘要 ──────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Ok "處理完成！新安裝 $countInstalled 個，移除 $countRemoved 個，略過 $countSkipped 個。"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
