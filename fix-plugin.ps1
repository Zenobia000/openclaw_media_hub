# ============================================================
# fix-plugin.ps1 — 修復指定插件路徑不存在的問題（通用型）
#
# 用法：
#   .\fix-plugin.ps1 <plugin_name> [plugin_name2 ...]
#   .\fix-plugin.ps1 notion
#   .\fix-plugin.ps1 notion slack google-calendar
#   .\fix-plugin.ps1 -List                          # 列出已安裝的插件
#   .\fix-plugin.ps1 -DryRun notion                 # 預覽變更但不實際修改
#
# 此腳本會：
#   1. 從 openclaw.json 移除指定插件的設定
#   2. 重啟容器以套用修正
#   3. 執行 openclaw doctor 驗證設定
# ============================================================

param(
    [Parameter(Position = 0, ValueFromRemainingArguments)]
    [string[]]$PluginNames,

    [switch]$List,
    [switch]$DryRun,
    [switch]$SkipRestart
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ConfigFile = Join-Path $ScriptDir ".openclaw\openclaw.json"

# -- 顏色輸出 -------------------------------------------------
function Write-Info  { param($Msg) Write-Host "[INFO]  $Msg" -ForegroundColor Blue }
function Write-Ok    { param($Msg) Write-Host "[OK]    $Msg" -ForegroundColor Green }
function Write-Warn  { param($Msg) Write-Host "[WARN]  $Msg" -ForegroundColor Yellow }
function Write-Err   { param($Msg) Write-Host "[ERROR] $Msg" -ForegroundColor Red }

# -- 檢查設定檔 -----------------------------------------------
if (-not (Test-Path $ConfigFile)) {
    Write-Err "找不到設定檔：$ConfigFile"
    exit 1
}

Write-Info "讀取設定檔：$ConfigFile"
$config = Get-Content -Path $ConfigFile -Raw | ConvertFrom-Json

# -- -List：列出已安裝的插件後結束 ------------------------------
if ($List) {
    Write-Host ""
    Write-Host "=== 已安裝的插件 ===" -ForegroundColor Cyan

    $found = $false

    if ($config.PSObject.Properties['plugins'] -and
        $config.plugins.PSObject.Properties['entries']) {
        Write-Host "  [entries]" -ForegroundColor DarkGray
        foreach ($prop in $config.plugins.entries.PSObject.Properties) {
            Write-Host "    - $($prop.Name)" -ForegroundColor White
            $found = $true
        }
    }

    if ($config.PSObject.Properties['plugins'] -and
        $config.plugins.PSObject.Properties['installs']) {
        Write-Host "  [installs]" -ForegroundColor DarkGray
        foreach ($prop in $config.plugins.installs.PSObject.Properties) {
            Write-Host "    - $($prop.Name)" -ForegroundColor White
            $found = $true
        }
    }

    if ($config.PSObject.Properties['plugins'] -and
        $config.plugins.PSObject.Properties['load'] -and
        $config.plugins.load.PSObject.Properties['paths']) {
        Write-Host "  [load.paths]" -ForegroundColor DarkGray
        foreach ($p in $config.plugins.load.paths) {
            Write-Host "    - $p" -ForegroundColor White
            $found = $true
        }
    }

    if (-not $found) {
        Write-Info "未發現任何插件設定。"
    }

    Write-Host ""
    exit 0
}

# -- 檢查參數 -------------------------------------------------
if (-not $PluginNames -or $PluginNames.Count -eq 0) {
    Write-Err "請提供至少一個插件名稱。用法：.\fix-plugin.ps1 <plugin_name> [...]"
    Write-Info "使用 -List 查看已安裝的插件。"
    exit 1
}

if ($DryRun) {
    Write-Warn "=== DryRun 模式：僅預覽變更，不會實際修改檔案 ==="
    Write-Host ""
}

# -- 逐一移除指定插件 ------------------------------------------
$totalModified = $false

foreach ($PluginName in $PluginNames) {
    $pluginModified = $false
    Write-Host ""
    Write-Host "--- 處理插件：$PluginName ---" -ForegroundColor Cyan

    # 1. 移除 plugins.load.paths 中的 /app/extensions/<plugin>
    $targetPath = "/app/extensions/$PluginName"
    if ($config.PSObject.Properties['plugins'] -and
        $config.plugins.PSObject.Properties['load'] -and
        $config.plugins.load.PSObject.Properties['paths']) {

        $paths = @($config.plugins.load.paths)
        $newPaths = @($paths | Where-Object { $_ -ne $targetPath })

        if ($newPaths.Count -lt $paths.Count) {
            if (-not $DryRun) { $config.plugins.load.paths = $newPaths }
            Write-Ok "已從 plugins.load.paths 移除 $targetPath"
            $pluginModified = $true
        } else {
            Write-Info "plugins.load.paths 中未包含 $targetPath（略過）"
        }
    }

    # 2. 移除 plugins.entries.<plugin>
    if ($config.PSObject.Properties['plugins'] -and
        $config.plugins.PSObject.Properties['entries'] -and
        $config.plugins.entries.PSObject.Properties[$PluginName]) {

        if (-not $DryRun) { $config.plugins.entries.PSObject.Properties.Remove($PluginName) }
        Write-Ok "已移除 plugins.entries.$PluginName"
        $pluginModified = $true
    } else {
        Write-Info "plugins.entries 中無 $PluginName 項目（略過）"
    }

    # 3. 移除 plugins.installs.<plugin>
    if ($config.PSObject.Properties['plugins'] -and
        $config.plugins.PSObject.Properties['installs'] -and
        $config.plugins.installs.PSObject.Properties[$PluginName]) {

        if (-not $DryRun) { $config.plugins.installs.PSObject.Properties.Remove($PluginName) }
        Write-Ok "已移除 plugins.installs.$PluginName"
        $pluginModified = $true
    } else {
        Write-Info "plugins.installs 中無 $PluginName 項目（略過）"
    }

    if (-not $pluginModified) {
        Write-Info "插件 $PluginName 無需修改。"
    }

    $totalModified = $totalModified -or $pluginModified
}

# -- 寫回設定檔 ------------------------------------------------
Write-Host ""
if ($totalModified -and -not $DryRun) {
    $config | ConvertTo-Json -Depth 10 | Set-Content -Path $ConfigFile -Encoding UTF8
    Write-Ok "設定檔已更新：$ConfigFile"
} elseif ($DryRun) {
    Write-Warn "DryRun 模式，設定檔未修改。"
} else {
    Write-Info "設定檔無需修改。"
    exit 0
}

# -- 重啟容器 --------------------------------------------------
if ($SkipRestart) {
    Write-Info "已跳過容器重啟（-SkipRestart）。"
} elseif (-not $DryRun) {
    Write-Host ""
    Write-Info "正在重新啟動容器以套用修正..."
    try {
        docker compose restart
        if ($LASTEXITCODE -ne 0) { throw "docker compose restart 失敗" }
        Write-Ok "容器已重新啟動"
    } catch {
        Write-Err "無法重新啟動容器：$_"
        exit 1
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

    if (-not $gatewayReady) {
        Write-Err "Gateway 未在 ${maxWait} 秒內就緒，請手動檢查容器狀態。"
        exit 1
    }
    Write-Ok "Gateway 已就緒（${waited} 秒）"

    # 執行 openclaw doctor 驗證
    Write-Host ""
    Write-Info "執行 openclaw doctor 驗證設定..."
    docker compose exec openclaw-gateway openclaw doctor 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "openclaw doctor 驗證通過！"
    } else {
        Write-Warn "doctor 仍回報問題，嘗試自動修復..."
        docker compose exec openclaw-gateway openclaw doctor --fix 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "openclaw doctor --fix 修復完成！"
        } else {
            Write-Err "自動修復失敗，請手動檢查。"
        }
    }
}

Write-Host ""
Write-Ok "修復流程完成！"
