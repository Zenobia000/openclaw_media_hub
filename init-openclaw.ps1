# ============================================================
# init-openclaw.ps1 — 初始化專案內 .openclaw 目錄結構
#
# 用法：
#   .\init-openclaw.ps1
#
# 此腳本會：
#   1. 建立 .openclaw 目錄結構
#   1-1. 部署技能（從 module_pack 複製至 workspace\skills）
#   2. 產生 openclaw.json (Gateway 設定)
#   3. 產生 auth-profiles.json 範本
#   4. 複製 .env.example → .env（若不存在）
#   5. 啟動 Docker Compose 服務
# ============================================================

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$OpenClawDir = Join-Path $ScriptDir ".openclaw"

# ── 顏色輸出 ────────────────────────────────────────────────
function Write-Info  { param($Msg) Write-Host "[INFO]  $Msg" -ForegroundColor Blue }
function Write-Ok    { param($Msg) Write-Host "[OK]    $Msg" -ForegroundColor Green }
function Write-Warn  { param($Msg) Write-Host "[WARN]  $Msg" -ForegroundColor Yellow }

# ── 主流程 ──────────────────────────────────────────────────

# 0. 檢查 Docker 是否正在執行
Write-Info "檢查 Docker 是否正在執行..."
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker 未回應"
    }
    Write-Ok "Docker 已啟動"
} catch {
    Write-Host "[ERROR] Docker 未啟動或未安裝。請先開啟 Docker Desktop 再執行此腳本。" -ForegroundColor Red
    exit 1
}

Write-Info "開始初始化 .openclaw 目錄結構..."
Write-Info "目標路徑：$OpenClawDir"

# 1. 建立目錄結構
$dirs = @(
    $OpenClawDir
    Join-Path $OpenClawDir "agents\main\agent"
    Join-Path $OpenClawDir "workspace"
    Join-Path $OpenClawDir "workspace\skills"
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

# 1-1. 部署技能：掃描 module_pack 中含 SKILL.md 的目錄，複製至 workspace\skills
$modulePackDir = Join-Path $ScriptDir "module_pack"
$skillsTargetDir = Join-Path $OpenClawDir "workspace\skills"

if (Test-Path $modulePackDir) {
    Write-Info "掃描 module_pack 中的技能..."
    $skillDirs = Get-ChildItem -Path $modulePackDir -Recurse -Filter "SKILL.md" | ForEach-Object { $_.Directory }

    foreach ($skillDir in $skillDirs) {
        $skillName = $skillDir.Name
        $targetDir = Join-Path $skillsTargetDir $skillName

        if (Test-Path $targetDir) {
            Write-Info "技能已存在：$skillName（略過）"
        } else {
            Copy-Item -Path $skillDir.FullName -Destination $targetDir -Recurse
            Write-Ok "部署技能：$skillName → .openclaw\workspace\skills\$skillName"
        }
    }
} else {
    Write-Warn "module_pack 目錄不存在，略過技能部署。"
}

# 2. 產生 openclaw.json（若不存在）
$configFile = Join-Path $OpenClawDir "openclaw.json"
if (-not (Test-Path $configFile)) {
    @'
{
  "gateway": {
    "mode": "local",
    "bind": "custom",
    "customBindHost": "0.0.0.0"
  }
}
'@ | Set-Content -Path $configFile -Encoding UTF8
    Write-Ok "建立設定檔：.openclaw\openclaw.json（mode=local, bind=0.0.0.0）"
} else {
    Write-Info "設定檔已存在：.openclaw\openclaw.json（略過）"
}

# 3. 產生 auth-profiles.json（若不存在）
$authFile = Join-Path $OpenClawDir "agents\main\agent\auth-profiles.json"
if (-not (Test-Path $authFile)) {
    @'
{
  "profiles": {
    "anthropic:manual": {
      "type": "token",
      "provider": "anthropic",
      "token": "YOUR_API_KEY_HERE"
    }
  }
}
'@ | Set-Content -Path $authFile -Encoding UTF8
    Write-Ok "建立認證檔範本：.openclaw\agents\main\agent\auth-profiles.json"
} else {
    Write-Info "認證檔已存在：.openclaw\agents\main\agent\auth-profiles.json（略過）"
}

# 3-1. 詢問使用者是否要新增 Claude API 金鑰
Write-Host ""
$addKey = Read-Host "是否要現在設定 Claude API 金鑰？(Y/n)"
if ($addKey -ne 'n' -and $addKey -ne 'N') {
    Write-Host ""
    Write-Info "請在另一個終端機視窗中執行以下指令來取得金鑰："
    Write-Host ""
    Write-Host "  claude setup-token" -ForegroundColor Cyan
    Write-Host ""
    Write-Info "取得金鑰後，請貼上至下方輸入框（金鑰通常以 sk-ant-oat01- 開頭）："
    Write-Host ""
    $apiKey = Read-Host "請貼上您的 Claude API 金鑰"

    if ([string]::IsNullOrWhiteSpace($apiKey)) {
        Write-Warn "未輸入金鑰，auth-profiles.json 維持預設值。您可稍後手動編輯。"
    } else {
        $authContent = @{
            profiles = @{
                "anthropic:manual" = @{
                    type     = "token"
                    provider = "anthropic"
                    token    = $apiKey.Trim()
                }
            }
        } | ConvertTo-Json -Depth 4
        $authContent | Set-Content -Path $authFile -Encoding UTF8
        Write-Ok "已將 API 金鑰寫入 auth-profiles.json"
    }
} else {
    Write-Warn "略過金鑰設定。您可稍後編輯 auth-profiles.json 填入 API Key。"
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
# 檢查 auth-profiles.json 是否仍為預設值
$currentAuth = Get-Content -Path $authFile -Raw
if ($currentAuth -match "YOUR_API_KEY_HERE") {
    Write-Warn "auth-profiles.json 仍為預設值，請稍後手動填入 API Key。"
}

# 5. 複製 .env.example → .env（若不存在）
$envExample = Join-Path $ScriptDir ".env.example"
$envFile = Join-Path $ScriptDir ".env"
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

# 6. 啟動 Docker Compose 服務
Write-Host ""
Write-Info "正在啟動 Docker Compose 服務..."
try {
    docker compose up -d
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose up -d 失敗"
    }
    Write-Ok "Docker Compose 服務已啟動"
} catch {
    Write-Host "[ERROR] 無法啟動 Docker Compose 服務：$_" -ForegroundColor Red
    exit 1
}

# 7. 等待 Gateway 啟動並讀取自動產生的 Token
Write-Host ""
$spinChars = @('|', '/', '-', '\')
$spinIdx = 0
$maxWait = 30
$waited = 0
$gatewayReady = $false
Write-Host -NoNewline "[INFO]  等待 Gateway 啟動... " -ForegroundColor Blue
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
Write-Host "`b " # 清除 spinner 字元

if (-not $gatewayReady) {
    Write-Host "[ERROR] Gateway 未在 ${maxWait} 秒內就緒，請手動檢查容器狀態。" -ForegroundColor Red
    exit 1
}
Write-Ok "Gateway 已就緒（${waited} 秒）"

# 讀取 openclaw.json 中自動產生的 Token
Write-Host ""
Write-Info "正在讀取 Dashboard Token..."
try {
    $config = Get-Content -Path $configFile -Raw | ConvertFrom-Json
    $token = $config.gateway.auth.token
    if ([string]::IsNullOrWhiteSpace($token)) {
        throw "設定檔中未找到 token"
    }
    Write-Ok "Dashboard 連線資訊："
    Write-Host ""
    Write-Host "  URL  : http://127.0.0.1:18789/" -ForegroundColor Cyan
    Write-Host "  Token: $token" -ForegroundColor Cyan
    Write-Host ""
    Write-Info "請在瀏覽器開啟上方 URL，並使用 Token 登入。"
} catch {
    Write-Host "[ERROR] 無法讀取 Token：$_" -ForegroundColor Red
    Write-Warn "您可手動查看 .openclaw\openclaw.json 中的 gateway.auth.token 欄位。"
}

# 8. 裝置配對（Device Pairing）
#    bind=0.0.0.0 時，從主機連入的流量經 Docker bridge（非 loopback），
#    Gateway 會要求 device pairing 審批。
Write-Host ""
Write-Info "裝置配對流程（Device Pairing）"
Write-Info "由於 Gateway 綁定 0.0.0.0，瀏覽器首次連線需要配對審批。"
Write-Host ""
$doPair = Read-Host "是否要現在進行裝置配對？請先用瀏覽器開啟 http://127.0.0.1:18789/ 再輸入 Y (Y/n)"
if ($doPair -ne 'n' -and $doPair -ne 'N') {
    Write-Info "等待瀏覽器連線產生配對請求..."
    $maxPairWait = 60
    $pairWaited = 0
    $requestId = $null

    while ($pairWaited -lt $maxPairWait) {
        $listOutput = docker compose exec openclaw-gateway openclaw devices list 2>&1 | Out-String
        # 從輸出中提取 Pending 區塊的 Request ID（UUID 格式）
        if ($listOutput -match "Pending \((\d+)\)") {
            $pendingCount = [int]$Matches[1]
            if ($pendingCount -gt 0 -and $listOutput -match "([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})") {
                $requestId = $Matches[1]
                break
            }
        }
        Start-Sleep -Seconds 3
        $pairWaited += 3
        if ($pairWaited % 15 -eq 0) {
            Write-Info "仍在等待瀏覽器連線... （已等待 ${pairWaited} 秒）"
        }
    }

    if ($requestId) {
        Write-Info "偵測到配對請求：$requestId"
        docker compose exec openclaw-gateway openclaw devices approve $requestId 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "裝置配對完成！請重新整理瀏覽器頁面。"
        } else {
            Write-Host "[ERROR] 配對審批失敗，請手動執行：" -ForegroundColor Red
            Write-Host "  docker compose exec openclaw-gateway openclaw devices approve $requestId" -ForegroundColor Yellow
        }
    } else {
        Write-Warn "等待逾時，未偵測到配對請求。"
        Write-Warn "您可稍後手動執行以下指令完成配對："
        Write-Host "  docker compose exec openclaw-gateway openclaw devices list" -ForegroundColor Yellow
        Write-Host "  docker compose exec openclaw-gateway openclaw devices approve <Request ID>" -ForegroundColor Yellow
    }
} else {
    Write-Info "略過裝置配對。您可稍後手動執行："
    Write-Host "  docker compose exec openclaw-gateway openclaw devices list" -ForegroundColor Yellow
    Write-Host "  docker compose exec openclaw-gateway openclaw devices approve <Request ID>" -ForegroundColor Yellow
}
