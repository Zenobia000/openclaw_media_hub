# OpenClaw Media Hub — Linux 前置需求清單

在新電腦上執行初始化腳本前，請依照此清單確認環境。

執行 `./check-env.sh` 可自動檢查大部分項目。

---

## 必要套件

以下為腳本執行的**硬性依賴**，缺一不可。

| 套件 | 用途 | 安裝指令 | 驗證指令 |
|------|------|----------|----------|
| **bash 4.0+** | 腳本執行環境 | 系統內建 | `bash --version` |
| **Docker Engine** | 容器執行環境 | [官方文件](https://docs.docker.com/engine/install/) | `docker --version` |
| **Docker Compose v2** | 服務編排 | Docker Engine 內建 | `docker compose version` |
| **jq** | JSON 解析與操作 | `sudo apt install -y jq` | `jq --version` |
| **curl** | HTTP 請求（健康檢查等） | `sudo apt install -y curl` | `curl --version` |

### 一鍵安裝（Ubuntu/Debian）

```bash
sudo apt update && sudo apt install -y jq curl
```

Docker 請依照官方文件安裝：https://docs.docker.com/engine/install/

---

## 選配套件

以下為特定功能使用，缺少時腳本會跳過對應步驟。

| 套件 | 用途 | 安裝方式 | 驗證指令 |
|------|------|----------|----------|
| **ngrok** | LINE Webhook 公開 HTTPS 通道 | [ngrok.com/download](https://ngrok.com/download) | `ngrok version` |
| **VS Code** | 開發編輯器（僅 check-env 檢查） | [code.visualstudio.com](https://code.visualstudio.com/) | `code --version` |

### ngrok 設定

安裝後需設定 auth token：
```bash
ngrok config add-authtoken <your-token>
```

---

## 環境需求

| 項目 | 需求 |
|------|------|
| **作業系統** | Linux（Ubuntu 20.04+ / Debian 11+ 建議）或 WSL2 |
| **終端機** | 支援 ANSI 色碼與互動式 TTY |
| **Docker 狀態** | 執行前須確保 Docker daemon 已啟動（`sudo systemctl start docker`） |
| **使用者權限** | 當前使用者須在 `docker` 群組（免 sudo 執行 docker）|
| **網路** | 需要存取 localhost:18789（Gateway）及 localhost:4040（ngrok，選配）|

### Docker 使用者群組設定

```bash
sudo usermod -aG docker $USER
# 重新登入或執行：
newgrp docker
```

---

## 環境變數（選配）

以下環境變數可在 `.env` 中自訂，皆有預設值：

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `OPENCLAW_IMAGE` | `openclaw:local` | Docker image 名稱 |
| `OPENCLAW_CONFIG_DIR` | `./.openclaw` | 設定檔目錄 |
| `OPENCLAW_WORKSPACE_DIR` | `./.openclaw/workspace` | 工作區目錄 |
| `OPENCLAW_GATEWAY_BIND` | `lan` | Gateway 綁定模式 |

---

## 快速驗證

在新電腦上安裝完成後，依序執行：

```bash
# 1. 驗證必要套件
bash --version | head -1
docker --version
docker compose version
jq --version
curl --version | head -1

# 2. 驗證 Docker 可用
docker info > /dev/null 2>&1 && echo "Docker OK" || echo "Docker 未啟動"

# 3. 執行環境檢查腳本
./check-env.sh

# 4. 開始初始化
./init-openclaw.sh
```

---

## 腳本與依賴對照

| 腳本 | 必要依賴 | 選配依賴 |
|------|----------|----------|
| `check-env.sh` | bash, docker | code, ngrok |
| `fix-plugin.sh` | bash, docker, jq, curl | — |
| `install_skill_hub.sh` | bash | — |
| `init-openclaw.sh` | bash, docker, jq, curl | ngrok |
