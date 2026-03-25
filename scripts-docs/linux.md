# Linux Native — OpenClaw 指令手冊

> 來源腳本：`common-native.sh`, `check-env-native.sh`, `init-openclaw-native.sh`, `deploy-skills-native.sh`, `install-plugins-native.sh`, `fix-plugin-native.sh`

---

## 共用變數

| 變數名稱 | 值 | 說明 |
| :--- | :--- | :--- |
| `OPENCLAW_DIR` | `"$PROJECT_ROOT/.openclaw"` | 主設定目錄 |
| `CONFIG_FILE` | `"$OPENCLAW_DIR/openclaw.json"` | 主設定檔 |
| `HEALTH_URL` | `http://127.0.0.1:18789/healthz` | Gateway 健康檢查端點 |
| `SERVICE_NAME` | `openclaw-gateway` | systemd 服務名稱 |

---

## 閘道操作 (Gateway)

| 系統名稱 | 動作描述 | 指令語法 | 參數說明 |
| :--- | :--- | :--- | :--- |
| Gateway | 執行任意 openclaw CLI 指令 | `openclaw "$@"` | `"$@"`：任意 openclaw 子指令與旗標 |
| Gateway | 啟動服務 (systemd) | `sudo systemctl start openclaw-gateway` | 服務：`openclaw-gateway` |
| Gateway | 啟動服務 (備援) | `openclaw gateway &` | 背景模式執行，當 systemd 無法使用時 |
| Gateway | 重啟服務 | `sudo systemctl restart openclaw-gateway` | 服務：`openclaw-gateway` |
| Gateway | 健康檢查 | `curl -sf --max-time 2 "$HEALTH_URL"` | `-sf`：靜默+失敗不輸出；`--max-time 2`：逾時 2 秒 |
| Gateway | 檢查服務狀態 | `systemctl is-active openclaw-gateway` | 服務：`openclaw-gateway` |

## 環境檢查 (Check Env)

| 系統名稱 | 動作描述 | 指令語法 | 參數說明 |
| :--- | :--- | :--- | :--- |
| Check | 檢查 CLI 版本 | `openclaw --version` | `--version`：顯示版本號 |
| Check | 檢查服務單元是否存在 | `systemctl list-unit-files openclaw-gateway.service` | 服務：`openclaw-gateway.service` |
| Check | 檢查服務是否執行中 | `systemctl is-active openclaw-gateway` | 服務：`openclaw-gateway` |

## 初始化 (Init)

| 系統名稱 | 動作描述 | 指令語法 | 參數說明 |
| :--- | :--- | :--- | :--- |
| Init | 檢查 CLI 是否存在 | `command -v openclaw` | — |
| Init | 建立目錄結構 | `mkdir -p "$OPENCLAW_DIR/agents/main/agent" "$OPENCLAW_DIR/workspace/skills"` | 建立 `.openclaw/` 子目錄 |
| Init | 產生初始設定檔 | 寫入 `$CONFIG_FILE`：`{"gateway":{"mode":"local","bind":"custom","customBindHost":"0.0.0.0"}}` | 路徑：`.openclaw/openclaw.json` |
| Init | 設定 API Key | `openclaw configure --section model` | `--section model`：僅設定模型區段 |
| Init | 列出配對請求 | `openclaw devices list 2>&1` | — |
| Init | 核准裝置配對 | `openclaw devices approve $request_id` | `$request_id`：裝置 UUID |
| Init | 寫入語音轉文字設定 | 透過 jq 寫入 `$CONFIG_FILE` 的 `.tools.media.audio` 區段 | `enabled`, `language:"zh"`, `model:"whisper-1"`, `provider:"openai"`, `echoTranscript:true` |
| Init | 讀取 Dashboard Token | 透過 jq 讀取 `$CONFIG_FILE` 的 `.gateway.auth.token` | — |
| Init | 讀取 Auth Profiles | 讀取 `$OPENCLAW_DIR/agents/main/agent/auth-profiles.json` | 透過 jq 偵測 OpenAI provider |

## 外掛安裝 (Plugins)

| 系統名稱 | 動作描述 | 指令語法 | 參數說明 |
| :--- | :--- | :--- | :--- |
| Plugin | 安裝 LINE 外掛 | `openclaw plugins install @openclaw/line` | 套件：`@openclaw/line` |
| Plugin | 安裝 Discord 外掛 | `openclaw plugins install @openclaw/discord` | 套件：`@openclaw/discord` |
| Plugin | 核准頻道配對 | `openclaw pairing approve $channel $code` | `$channel`：`line` 或 `discord`；`$code`：配對碼 |
| Plugin | 寫入 LINE 頻道設定 | 透過 jq 寫入 `$CONFIG_FILE` 的 `.channels.line` | `enabled`, `channelAccessToken`, `channelSecret`, `dmPolicy:"open"` |
| Plugin | 寫入 Discord 頻道設定 | 透過 jq 寫入 `$CONFIG_FILE` 的 `.channels.discord` | `enabled`, `token`, `groupPolicy:"allowlist"`, `dmPolicy:"open"`, `streaming:"off"` |

## 外掛修復 (Fix Plugin)

| 系統名稱 | 動作描述 | 指令語法 | 參數說明 |
| :--- | :--- | :--- | :--- |
| Fix | 執行診斷 | `openclaw doctor 2>&1` | — |
| Fix | 自動修復 | `openclaw doctor --fix 2>&1` | `--fix`：自動修復模式 |
| Fix | 移除外掛設定 | 透過 jq 修改 `$CONFIG_FILE`：刪除 `.plugins.entries.<plugin>`, `.plugins.installs.<plugin>`，從 `.plugins.load.paths` 移除匹配 `/<plugin_name>` 結尾的路徑 | `$plugin_name`：外掛名稱；路徑為自動偵測（非硬編碼 `/app/extensions/`） |

## 技能部署 (Skills)

| 系統名稱 | 動作描述 | 指令語法 | 參數說明 |
| :--- | :--- | :--- | :--- |
| Skill | 部署技能 | `cp -r "${SKILL_SOURCES[$i]}" "$target_dir"` | 來源：`module_pack/<skill>/`；目標：`.openclaw/workspace/skills/<skill>/` |
| Skill | 移除技能 | `rm -rf "$target_dir"` | 目標：`.openclaw/workspace/skills/<skill>/` |

## 端點與 URL

| 系統名稱 | 動作描述 | 指令語法 | 參數說明 |
| :--- | :--- | :--- | :--- |
| Endpoint | Gateway Dashboard | `http://127.0.0.1:18789/` | — |
| Endpoint | 健康檢查 | `http://127.0.0.1:18789/healthz` | 預期回應：`{"ok":true}` |
| Endpoint | ngrok Tunnel 資訊 | `http://127.0.0.1:4040/api/tunnels` | — |
| Endpoint | LINE Webhook | `$ngrokUrl/line/webhook` | 透過 ngrok 公開 URL |
