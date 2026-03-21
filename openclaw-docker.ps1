# ============================================================
# openclaw-docker.ps1 — OpenClaw 統一入口腳本 (Docker)
#
# 用法：.\openclaw-docker.ps1 <子命令> [參數...]
#
# 子命令：
#   init                初始化 .openclaw 目錄結構與插件設定
#   check-env           檢查環境相依工具
#   fix-plugin          修復插件問題
#   deploy-skills       部署技能（module_pack → workspace\skills）
#   install-plugins     安裝 / 管理插件
#   install-skill-hub   安裝 Skill Hub
# ============================================================

param(
    [Parameter(Position = 0)]
    [string]$Command,

    [Parameter(Position = 1, ValueFromRemainingArguments)]
    [string[]]$Rest
)

$ScriptsDir = Join-Path $PSScriptRoot "scripts-docker"

function Show-Usage {
    Write-Host @"
用法：.\openclaw-docker.ps1 <子命令> [參數...]

子命令：
  init                初始化 .openclaw 目錄結構與插件設定
  deploy-skills       部署技能（module_pack → workspace\skills）
  check-env           檢查環境相依工具
  fix-plugin          修復插件問題
  install-plugins     安裝 / 管理插件
  install-skill-hub   安裝 Skill Hub
"@
    exit 1
}

if (-not $Command) { Show-Usage }

switch ($Command) {
    'init'              { & "$ScriptsDir\init-openclaw-docker.ps1" @Rest }
    'deploy-skills'     { & "$ScriptsDir\deploy-skills-docker.ps1" @Rest }
    'check-env'         { & "$ScriptsDir\check-env-docker.ps1" @Rest }
    'fix-plugin'        { & "$ScriptsDir\fix-plugin-docker.ps1" @Rest }
    'install-plugins'   { & "$ScriptsDir\install-plugins-docker.ps1" @Rest }
    'install-skill-hub' { & "$ScriptsDir\install-skill-hub-docker.ps1" @Rest }
    default {
        Write-Host "錯誤：未知的子命令 '$Command'" -ForegroundColor Red
        Write-Host ""
        Show-Usage
    }
}
