# ============================================================
# init-openclaw.ps1 — 初始化專案內 .openclaw 目錄結構
#
# 用法：
#   .\init-openclaw.ps1
#
# 此腳本會：
#   1. 建立 .openclaw 目錄結構
#   2. 產生 openclaw.json (Gateway 設定)
#   3. 產生 auth-profiles.json 範本
# ============================================================

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$OpenClawDir = Join-Path $ScriptDir ".openclaw"

# ── 顏色輸出 ────────────────────────────────────────────────
function Write-Info  { param($Msg) Write-Host "[INFO]  $Msg" -ForegroundColor Blue }
function Write-Ok    { param($Msg) Write-Host "[OK]    $Msg" -ForegroundColor Green }
function Write-Warn  { param($Msg) Write-Host "[WARN]  $Msg" -ForegroundColor Yellow }

# ── 主流程 ──────────────────────────────────────────────────
Write-Info "開始初始化 .openclaw 目錄結構..."
Write-Info "目標路徑：$OpenClawDir"

# 1. 建立目錄結構
$dirs = @(
    $OpenClawDir
    Join-Path $OpenClawDir "agents\main\agent"
    Join-Path $OpenClawDir "workspace"
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

# 2. 產生 openclaw.json（若不存在）
$configFile = Join-Path $OpenClawDir "openclaw.json"
if (-not (Test-Path $configFile)) {
    @'
{
  "gateway": {
    "mode": "local"
  }
}
'@ | Set-Content -Path $configFile -Encoding UTF8
    Write-Ok "建立設定檔：.openclaw\openclaw.json（mode=local）"
} else {
    Write-Info "設定檔已存在：.openclaw\openclaw.json（略過）"
}

# 3. 產生 auth-profiles.json（若不存在）
$authFile = Join-Path $OpenClawDir "agents\main\agent\auth-profiles.json"
if (-not (Test-Path $authFile)) {
    @'
{
  "anthropic": {
    "apiKey": "YOUR_API_KEY_HERE"
  }
}
'@ | Set-Content -Path $authFile -Encoding UTF8
    Write-Ok "建立認證檔範本：.openclaw\agents\main\agent\auth-profiles.json"
    Write-Warn "請編輯上述檔案，填入您的 Anthropic API Key"
} else {
    Write-Info "認證檔已存在：.openclaw\agents\main\agent\auth-profiles.json（略過）"
}

# 4. 顯示目錄結構
Write-Host ""
Write-Info "目錄結構："
Get-ChildItem -Path $OpenClawDir -Recurse | ForEach-Object {
    $rel = $_.FullName.Replace("$OpenClawDir\", "")
    $depth = ($rel.ToCharArray() | Where-Object { $_ -eq '\' }).Count
    $indent = "  " * $depth
    $icon = if ($_.PSIsContainer) { "[D]" } else { "[F]" }
    Write-Host "  $indent$icon $($_.Name)"
}

Write-Host ""
Write-Ok "初始化完成！"
Write-Info "下一步：編輯 auth-profiles.json 填入 API Key，然後執行 docker compose up -d"
