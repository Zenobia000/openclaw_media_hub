# ============================================================
# install-skill-hub-docker.ps1 — 互動式安裝 skill_hub 擴充技能 (Docker)
#
# 用法：.\scripts-docker\install-skill-hub-docker.ps1
#
# 此腳本會：
#   1. 掃描 skill_hub/ 中含 SKILL.md 的技能目錄
#   2. 顯示互動式選擇介面供使用者挑選
#   3. 將選擇的技能複製至 .openclaw/workspace/skills/
# ============================================================

. "$PSScriptRoot\common.ps1"

$SkillHubDir     = Join-Path $ProjectRoot "skill_hub"
$SkillsTargetDir = Join-Path $OpenClawDir "workspace\skills"

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

# ── 建立技能清單 ──────────────────────────────────────────────
$skills = @()
foreach ($skillDir in $skillDirs) {
    $skillName = $skillDir.Name
    $skillMdPath = Join-Path $skillDir.FullName "SKILL.md"
    $meta = Get-SkillMeta -Path $skillMdPath
    $installed = Test-Path (Join-Path $SkillsTargetDir $skillName)

    $skills += [PSCustomObject]@{
        Name        = $skillName
        Emoji       = $meta.Emoji
        Description = $meta.Description
        SourceDir   = $skillDir.FullName
        Installed   = $installed
    }
}

# ── 執行選擇 ─────────────────────────────────────────────────
$selectedIndices = Show-SkillSelector -Skills $skills -Title "OpenClaw Skill Hub 安裝工具"

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
