# ============================================================
# openclaw.ps1 — OpenClaw 統一入口腳本
#
# 用法：.\openclaw.ps1 <子命令> [參數...]
#
# 子命令：
#   init                初始化 .openclaw 目錄結構與插件設定
#   check-env           檢查環境相依工具
#   fix-plugin          修復插件問題
#   install-plugins     安裝 / 管理插件
#   install-skill-hub   安裝 Skill Hub
# ============================================================

param(
    [Parameter(Position = 0)]
    [string]$Command,

    [Parameter(Position = 1, ValueFromRemainingArguments)]
    [string[]]$Rest
)

$ScriptsDir = Join-Path $PSScriptRoot "scripts"

function Show-Usage {
    Write-Host @"
用法：.\openclaw.ps1 <子命令> [參數...]

子命令：
  init                初始化 .openclaw 目錄結構與插件設定
  check-env           檢查環境相依工具
  fix-plugin          修復插件問題
  install-plugins     安裝 / 管理插件
  install-skill-hub   安裝 Skill Hub
"@
    exit 1
}

if (-not $Command) { Show-Usage }

switch ($Command) {
    'init'              { & "$ScriptsDir\init-openclaw.ps1" @Rest }
    'check-env'         { & "$ScriptsDir\check-env.ps1" @Rest }
    'fix-plugin'        { & "$ScriptsDir\fix-plugin.ps1" @Rest }
    'install-plugins'   { & "$ScriptsDir\install-plugins.ps1" @Rest }
    'install-skill-hub' { & "$ScriptsDir\install-skill-hub.ps1" @Rest }
    default {
        Write-Host "錯誤：未知的子命令 '$Command'" -ForegroundColor Red
        Write-Host ""
        Show-Usage
    }
}
