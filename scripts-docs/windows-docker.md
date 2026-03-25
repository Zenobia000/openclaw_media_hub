# Windows Docker — OpenClaw 指令手冊

> 來源腳本：`common.ps1`, `check-env-docker.ps1`, `init-openclaw-docker.ps1`, `deploy-skills-docker.ps1`, `install-plugins-docker.ps1`, `install-skill-hub-docker.ps1`, `fix-plugin-docker.ps1`

---

## 共用變數

| 變數名稱 | 值 | 說明 |
| :--- | :--- | :--- |
| `$OpenClawDir` | `Join-Path $ProjectRoot ".openclaw"` | 主設定目錄 |
| `$ConfigFile` | `Join-Path $OpenClawDir "openclaw.json"` | 主設定檔 |
| `$HealthUrl` | `http://127.0.0.1:18789/healthz` | Gateway 健康檢查端點 |

---

## 閘道操作 (Gateway)

| 系統名稱 | 動作描述 | 指令語法 | 參數說明 |
| :--- | :--- | :--- | :--- |
| Gateway | 執行任意 openclaw CLI 指令 | `docker compose exec openclaw-gateway openclaw @GwArgs` | `@GwArgs`：任意 openclaw 子指令與旗標 |
| Gateway | 啟動所有服務 | `docker compose up -d` | `-d`：背景模式 |
| Gateway | 重啟所有服務 | `docker compose restart` | — |
| Gateway | 健康檢查 | `Invoke-RestMethod -Uri "http://127.0.0.1:18789/healthz" -TimeoutSec 2` | `-TimeoutSec 2` |

## 初始化 (Init)

| 系統名稱 | 動作描述 | 指令語法 | 參數說明 |
| :--- | :--- | :--- | :--- |
| Init | 建立目錄結構 | `New-Item -ItemType Directory "$OpenClawDir\agents\main\agent"` | 建立 `.openclaw/agents/main/agent` |
| Init | 建立目錄結構 | `New-Item -ItemType Directory "$OpenClawDir\workspace\skills"` | 建立 `.openclaw/workspace/skills` |
| Init | 產生初始設定檔 | 寫入 `$ConfigFile`：`{"gateway":{"mode":"local","bind":"custom","customBindHost":"0.0.0.0"}}` | 路徑：`.openclaw/openclaw.json` |
| Init | 設定 API Key | `docker compose exec openclaw-gateway openclaw configure --section model` | `--section model`：僅設定模型區段 |
| Init | 列出配對請求 | `docker compose exec openclaw-gateway openclaw devices list 2>&1` | — |
| Init | 核准裝置配對 | `docker compose exec openclaw-gateway openclaw devices approve $Id` | `$Id`：裝置 UUID |
| Init | 寫入語音轉文字設定 | 寫入 `$ConfigFile` 的 `.tools.media.audio` 區段 | `enabled`, `language:"zh"`, `model:"whisper-1"`, `provider:"openai"`, `echoTranscript:true` |
| Init | 讀取 Dashboard Token | 讀取 `$ConfigFile` 的 `.gateway.auth.token` | — |
| Init | 讀取 Auth Profiles | 讀取 `$OpenClawDir\agents\main\agent\auth-profiles.json` | 偵測 OpenAI provider |

## 外掛安裝 (Plugins)

| 系統名稱 | 動作描述 | 指令語法 | 參數說明 |
| :--- | :--- | :--- | :--- |
| Plugin | 安裝 LINE 外掛 | `docker compose exec openclaw-gateway openclaw plugins install @openclaw/line` | 套件：`@openclaw/line` |
| Plugin | 安裝 Discord 外掛 | `docker compose exec openclaw-gateway openclaw plugins install @openclaw/discord` | 套件：`@openclaw/discord` |
| Plugin | 核准頻道配對 | `docker compose exec openclaw-gateway openclaw pairing approve $Channel $code` | `$Channel`：`line` 或 `discord`；`$code`：配對碼 |
| Plugin | 寫入 LINE 頻道設定 | 寫入 `$ConfigFile` 的 `.channels.line` | `enabled`, `channelAccessToken`, `channelSecret`, `dmPolicy:"open"` |
| Plugin | 寫入 Discord 頻道設定 | 寫入 `$ConfigFile` 的 `.channels.discord` | `enabled`, `token`, `groupPolicy:"allowlist"`, `dmPolicy:"open"`, `streaming:"off"` |

## 外掛修復 (Fix Plugin)

| 系統名稱 | 動作描述 | 指令語法 | 參數說明 |
| :--- | :--- | :--- | :--- |
| Fix | 執行診斷 | `docker compose exec openclaw-gateway openclaw doctor 2>&1` | — |
| Fix | 自動修復 | `docker compose exec openclaw-gateway openclaw doctor --fix 2>&1` | `--fix`：自動修復模式 |
| Fix | 移除外掛設定 | 修改 `$ConfigFile`：刪除 `.plugins.entries.<plugin>`, `.plugins.installs.<plugin>`，從 `.plugins.load.paths` 移除 `"/app/extensions/$PluginName"` | `$PluginName`：外掛名稱 |

## 技能部署 (Skills)

| 系統名稱 | 動作描述 | 指令語法 | 參數說明 |
| :--- | :--- | :--- | :--- |
| Skill | 部署技能 | `Copy-Item -Path $s.SourceDir -Destination $targetDir -Recurse` | 來源：`module_pack/<skill>/`；目標：`.openclaw\workspace\skills\<skill>/` |
| Skill | 移除技能 | `Remove-Item -Path $targetDir -Recurse -Force` | 目標：`.openclaw\workspace\skills\<skill>/` |
| Skill Hub | 部署社群技能 | `Copy-Item -Path $s.SourceDir -Destination $targetDir -Recurse` | 來源：`skill_hub/<skill>/`；目標：`.openclaw\workspace\skills\<skill>/` |
| Skill Hub | 移除社群技能 | `Remove-Item -Path $targetDir -Recurse -Force` | 目標：`.openclaw\workspace\skills\<skill>/` |

## 端點與 URL

| 系統名稱 | 動作描述 | 指令語法 | 參數說明 |
| :--- | :--- | :--- | :--- |
| Endpoint | Gateway Dashboard | `http://127.0.0.1:18789/` | — |
| Endpoint | 健康檢查 | `http://127.0.0.1:18789/healthz` | 預期回應：`{"ok":true}` |
| Endpoint | ngrok Tunnel 資訊 | `http://127.0.0.1:4040/api/tunnels` | — |
| Endpoint | LINE Webhook | `$ngrokUrl/line/webhook` | 透過 ngrok 公開 URL |
