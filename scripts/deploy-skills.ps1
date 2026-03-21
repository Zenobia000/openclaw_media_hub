# ============================================================
# deploy-skills.ps1 — 部署技能（module_pack → workspace\skills）
#
# 用法：.\scripts\deploy-skills.ps1
#
# 掃描 module_pack 目錄中的技能（透過 SKILL.md），提供互動式
# 選擇介面讓使用者勾選要部署或移除的技能。
# ============================================================

. "$PSScriptRoot\common.ps1"

# ════════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════════

$modulePackDir   = Join-Path $ProjectRoot "module_pack"
$skillsTargetDir = Join-Path $OpenClawDir "workspace\skills"

# 確保目標目錄存在
if (-not (Test-Path $skillsTargetDir)) {
    New-Item -ItemType Directory -Path $skillsTargetDir -Force | Out-Null
    Write-Ok "建立目錄：.openclaw\workspace\skills"
}

if (-not (Test-Path $modulePackDir)) {
    Write-Warn "module_pack 目錄不存在，略過技能部署。"
    exit 0
}

Write-Info "掃描 module_pack 中的技能..."
$skillFiles = Get-ChildItem -Path $modulePackDir -Recurse -Filter "SKILL.md"

if ($skillFiles.Count -eq 0) {
    Write-Info "module_pack 中未找到任何技能。"
    exit 0
}

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

$selectedIndices = Show-SkillSelector -Skills $skills -Title "OpenClaw 技能部署工具"

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
