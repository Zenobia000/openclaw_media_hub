# **Docker**

Docker 是可選的。僅當您需要容器化網關或驗證 Docker 流程​​時才使用它。

## [**號**](https://docs.openclaw.ai/install/docker#is-docker-right-for-me)

## **Docker適合我嗎？**

- 是的：您需要一個隔離的、一次性的閘道環境，或想在主機上執行 OpenClaw 而無需本機安裝。
- 不：你是在自己的機器上運行，只是想追求最快的開發循環。請使用正常的安裝流程。
- 沙箱說明：代理沙箱也使用 Docker，但它不需要整個網關在 Docker 中運作。請參閱[沙箱部分](https://docs.openclaw.ai/gateway/sandboxing)。

本指南涵蓋以下內容：

- 容器化網關（Docker 中的完整 OpenClaw）
- 每個會話的代理沙箱（主機網關 \+ Docker 隔離的代理工具）

沙盒詳情：[沙盒](https://docs.openclaw.ai/gateway/sandboxing)

## [**號**](https://docs.openclaw.ai/install/docker#requirements)

## **要求**

- Docker Desktop（或 Docker Engine）+ Docker Compose v2
- 鏡像建置至少需要 2 GB 記憶體（pnpm install在 1 GB 記憶體的主機上可能會因記憶體不足而終止，退出代碼為 137）。
- 足夠的磁碟空間來存放鏡像和日誌
- 如果運行在 VPS/公共主機上，請檢查 [網路暴露的安全加固措施](https://docs.openclaw.ai/gateway/security#04-network-exposure-bind--port--firewall)，特別是 DockerDOCKER-USER防火牆策略。

## [**號**](https://docs.openclaw.ai/install/docker#containerized-gateway-docker-compose)

## **容器化網關（Docker Compose）**

### [**號**](https://docs.openclaw.ai/install/docker#quick-start-recommended)

### **快速入門（推薦）**

此處的 Docker 預設設定假定使用綁定模式（lan/ loopback），而不是主機別名。請使用綁定模式值gateway.bind（例如lan或loopback），而不是主機別名，例如 0.0.0.0或localhost。

從倉庫根目錄：

./docker-setup.sh

這段腳本：

- 在本機上建置網關映像（如果OPENCLAW_IMAGE已設置，則拉取遠端鏡像）
- 運行新用戶引導程式
- 列印可選的提供者設定提示
- 透過 Docker Compose 啟動網關
- 產生網關令牌並將其寫入.env

可選環境變數：

- OPENCLAW_IMAGE— 使用遠端鏡像而不是在本地建置（例如ghcr.io/openclaw/openclaw:latest）
- OPENCLAW_DOCKER_APT_PACKAGES— 在建置過程中安裝額外的 apt 軟體包
- OPENCLAW_EXTENSIONS— 在建置時預先安裝擴充依賴項（擴充名稱以空格分隔，例如diagnostics-otel matrix）
- OPENCLAW_EXTRA_MOUNTS— 新增額外的主機綁定掛載點
- OPENCLAW_HOME_VOLUME— 儲存/home/node在命名磁碟區中
- OPENCLAW_SANDBOX— 選擇加入 Docker 閘道沙箱引導。只有顯式的真值才能啟用此功能：1，，，trueyeson
- OPENCLAW_INSTALL_DOCKER_CLI— 為本機映像建置傳遞建置參數（1在映像中安裝 Docker CLI）。本機建置docker-setup.sh時會自動設定此項目。OPENCLAW_SANDBOX=1
- OPENCLAW_DOCKER_SOCKET— 覆寫 Docker 套接字路徑（預設值：DOCKER_HOST=unix://...path，否則/var/run/docker.sock）
- OPENCLAW_ALLOW_INSECURE_PRIVATE_WS=1— break-glass：允許 CLI/新客戶端路徑使用受信任的私有網路 ws://目標（預設僅限環回）
- OPENCLAW_BROWSER_DISABLE_GRAPHICS_FLAGS=0—當需要 WebGL/3D 相容性時\--disable-3d-apis，停用容器瀏覽器強化標誌 。\--disable-software-rasterizer--disable-gpu
- OPENCLAW_BROWSER_DISABLE_EXTENSIONS=0— 當瀏覽器流程需要時，請保持擴充功能啟用狀態（預設情況下，在沙盒瀏覽器中停用擴充功能）。
- OPENCLAW_BROWSER_RENDERER_PROCESS_LIMIT=\<N\>— 設定 Chromium 渲染器程序限制；設定為0true 可跳過該標誌並使用 Chromium 預設行為。

結束後：

- http://127.0.0.1:18789/在瀏覽器中開啟。
- 將令牌貼到控制介面（設定 → 令牌）中。
- 需要再次取得 URL？運行docker compose run \--rm openclaw-cli dashboard \--no-open.

### [**號**](https://docs.openclaw.ai/install/docker#enable-agent-sandbox-for-docker-gateway-opt-in)

### **為 Docker 網關啟用代理沙箱（選購）**

docker-setup.sh也可以引導agents.defaults.sandbox.\*Docker 部署。

啟用方式：

export OPENCLAW_SANDBOX\=1  
./docker-setup.sh

自訂套接字路徑（例如無根 Docker）：

export OPENCLAW_SANDBOX\=1  
export OPENCLAW_DOCKER_SOCKET\=/run/user/1000/docker.sock  
./docker-setup.sh

筆記：

- 腳本docker.sock只有在沙盒環境滿足所有先決條件後才會掛載。
- 如果沙箱設定無法完成，腳本將重置 agents.defaults.sandbox.mode以off避免在重新運行時出現過時/損壞的沙箱配置。
- 如果Dockerfile.sandbox缺少該參數，腳本將列印警告並繼續運行；如果需要，openclaw-sandbox:bookworm-slim請使用該參數進行建置scripts/sandbox-setup.sh。
- 對於非本機OPENCLAW_IMAGE值，映像必須已經包含用於沙箱執行的 Docker CLI 支援。

### [**號**](https://docs.openclaw.ai/install/docker#automation/ci-non-interactive-no-tty-noise)

### **自動化/CI（非互動式，無TTY噪音）**

對於腳本和 CI，請使用以下命令停用 Compose 偽 TTY 分配\-T：

docker compose run \-T \--rm openclaw-cli gateway probe  
docker compose run \-T \--rm openclaw-cli devices list \--json

如果您的自動化流程不會匯出任何 Claude 會話變量，則預設情況下，未設定這些變數的值將解析為空值，docker-compose.yml以避免重複出現「變數未設定」警告。

### [**號**](https://docs.openclaw.ai/install/docker#shared-network-security-note-cli-+-gateway)

### **共享網路安全注意事項（CLI \+ 網關）**

openclaw-cli使用此功能可讓 CLI 命令可靠地透過 Dockernetwork_mode: "service:openclaw-gateway"連接到網關。127.0.0.1

請將此視為共享信任邊界：回環綁定並不能隔離這兩個容器。如果需要更強的隔離，請從單獨的容器/主機網路路徑執行命令，而不是從捆綁的openclaw-cli服務執行。

為了降低 CLI 進程受損時的影響，compose 配置會刪除 NET_RAW/NET_ADMIN並no-new-privileges啟用openclaw-cli。

它會將 config/workspace 寫入主機：

- \~/.openclaw/
- \~/.openclaw/workspace

在 VPS 上運行？請查看[Hetzner（Docker VPS）](https://docs.openclaw.ai/install/hetzner)。

### [**號**](https://docs.openclaw.ai/install/docker#use-a-remote-image-skip-local-build)

### **使用遠端鏡像（跳過本機建置）**

官方預裝鏡像發佈在：

- [GitHub 容器註冊表包](https://github.com/openclaw/openclaw/pkgs/container/openclaw)

使用映像名稱ghcr.io/openclaw/openclaw（不要使用名稱相似的 Docker Hub 映像）。

常用標籤：

- main— 最新版本main
- \<version\>— 發布標籤建置（例如2026.2.26）
- latest— 最新穩定版本標籤

### [**號**](https://docs.openclaw.ai/install/docker#base-image-metadata)

### **基礎影像元數據**

目前主要的 Docker 映像使用：

- node:24-bookworm

Docker 映像現在會發佈 OCI 基礎映像註解（sha256 就是一個例子，它指向該標籤的固定多架構清單清單）：

- org.opencontainers.image.base.name=docker.io/library/node:24-bookworm
- org.opencontainers.image.base.digest=sha256:3a09aa6354567619221ef6c45a5051b671f953f0a1924d1f819ffb236e520e6b
- org.opencontainers.image.source=https://github.com/openclaw/openclaw
- org.opencontainers.image.url=https://openclaw.ai
- org.opencontainers.image.documentation=https://docs.openclaw.ai/install/docker
- org.opencontainers.image.licenses=MIT
- org.opencontainers.image.title=OpenClaw
- org.opencontainers.image.description=OpenClaw gateway and CLI runtime container image
- org.opencontainers.image.revision=\<git-sha\>
- org.opencontainers.image.version=\<tag-or-main\>
- org.opencontainers.image.created=\<rfc3339 timestamp\>

參考資料：[OCI影像標註](https://github.com/opencontainers/image-spec/blob/main/annotations.md)

發布背景：此儲存庫的標記歷史記錄已在 v2026.2.222026 年及更早的版本中使用 Bookworm 標籤（例如v2026.2.21，v2026.2.9）。

預設情況下，安裝腳本會從原始碼建立鏡像。若要改為拉取預先建置鏡像，請OPENCLAW_IMAGE在執行腳本之前進行設定：

export OPENCLAW_IMAGE\="ghcr.io/openclaw/openclaw:latest"  
./docker-setup.sh

腳本偵測到這OPENCLAW_IMAGE不是預設值openclaw:local，並執行該腳本docker pull代替預設值docker build。其他所有操作（註冊、網關啟動、令牌產生）都以相同的方式進行。

docker-setup.shdocker-compose.yml由於使用了本地文件和輔助文件，因此仍然從倉庫根目錄運行 。OPENCLAW_IMAGE跳過了本機鏡像建置時間；它不會取代 compose/setup 工作流程。

### [**號**](https://docs.openclaw.ai/install/docker#shell-helpers-optional)

### **Shell 輔助函數（可選）**

為了更輕鬆地進行日常 Docker 管理，請安裝ClawDock：

mkdir \-p \~/.clawdock && curl \-sL https://raw.githubusercontent.com/openclaw/openclaw/main/scripts/shell-helpers/clawdock-helpers.sh \-o \~/.clawdock/clawdock-helpers.sh

加到你的 shell 配置（zsh）：

echo 'source \~/.clawdock/clawdock-helpers.sh' \>\> \~/.zshrc && source \~/.zshrc

然後使用clawdock-start，，，等等。運行clawdock-stop所有命令。clawdock-dashboardclawdock-help

詳情請參閱[ClawDockHelper README文件。](https://github.com/openclaw/openclaw/blob/main/scripts/shell-helpers/README.md)

### [**號**](https://docs.openclaw.ai/install/docker#manual-flow-compose)

### **手動流程（編寫）**

docker build \-t openclaw:local \-f Dockerfile .  
docker compose run \--rm openclaw-cli onboard  
docker compose up \-d openclaw-gateway

注意：請docker compose ...從倉庫根目錄運作。如果您啟用了 \`configure\` OPENCLAW_EXTRA_MOUNTS或 \` configure\` OPENCLAW_HOME_VOLUME，設定腳本會寫入 \`configure\` docker-compose.extra.yml；在其他位置執行 Compose 時，請包含此腳本：

docker compose \-f docker-compose.yml \-f docker-compose.extra.yml \<command\>

### [**號**](https://docs.openclaw.ai/install/docker#control-ui-token-+-pairing-docker)

### **控制 UI 令牌 \+ 配對（Docker）**

如果看到“未授權”或“已斷開連接 (1008)：需要配對”，請取得新的控制面板連結並批准瀏覽器設備：

docker compose run \--rm openclaw-cli dashboard \--no-open  
docker compose run \--rm openclaw-cli devices list  
docker compose run \--rm openclaw-cli devices approve \<requestId\>

更多詳情：[儀錶板](https://docs.openclaw.ai/web/dashboard)、[設備](https://docs.openclaw.ai/cli/devices)。

### [**號**](https://docs.openclaw.ai/install/docker#extra-mounts-optional)

### **額外安裝支架（選購）**

如果您想要將額外的主機目錄掛載到容器中，請 OPENCLAW_EXTRA_MOUNTS在運行之前進行設定docker-setup.sh。此命令接受以逗號分隔的 Docker 綁定掛載列表，並 透過產生檔案將它們套用到容器openclaw-gateway和主機上。openclaw-clidocker-compose.extra.yml

例子：

export OPENCLAW_EXTRA_MOUNTS\="$HOME/.codex:/home/node/.codex:ro,$HOME/github:/home/node/github:rw"  
./docker-setup.sh

筆記：

- 路徑必須與 macOS/Windows 上的 Docker Desktop 共用。
- 每條輸入內容不得source:target\[:options\]包含空格、製表符或換行符。
- 如果進行了編輯OPENCLAW_EXTRA_MOUNTS，請重新運行docker-setup.sh以重新產生額外的 compose 檔案。
- docker-compose.extra.yml已自動生成，請勿手動編輯。

### [**號**](https://docs.openclaw.ai/install/docker#persist-the-entire-container-home-optional)

### **持久化整個容器主目錄（可選）**

如果希望/home/node在容器重建後仍能保留配置，請透過 \`docker volume\` 設定命名磁碟區OPENCLAW_HOME_VOLUME。這將建立一個 Docker 磁碟區並將其掛載到 \`/ etc /home/node/docker ... OPENCLAW_EXTRA_MOUNTS

例子：

export OPENCLAW_HOME_VOLUME\="openclaw_home"  
./docker-setup.sh

您可以將此與額外的支架結合使用：

export OPENCLAW_HOME_VOLUME\="openclaw_home"  
export OPENCLAW_EXTRA_MOUNTS\="$HOME/.codex:/home/node/.codex:ro,$HOME/github:/home/node/github:rw"  
./docker-setup.sh

筆記：

- 卷名稱必須匹配^\[A-Za-z0-9\]\[A-Za-z0-9\_.-\]\*$。
- 如果更改了OPENCLAW_HOME_VOLUME，請重新運行docker-setup.sh以重新產生額外的 compose 檔案。
- 指定的磁碟區會一直存在，直到使用 . 刪除為止docker volume rm \<name\>。

### [**號**](https://docs.openclaw.ai/install/docker#install-extra-apt-packages-optional)

### **安裝額外的apt軟體包（可選）**

如果鏡像中需要係統軟體包（例如建置工具或媒體庫），請OPENCLAW_DOCKER_APT_PACKAGES在運行前進行設定docker-setup.sh。這樣會在鏡像建置過程中安裝這些軟體包，即使容器被刪除，它們也會保留下來。

例子：

export OPENCLAW_DOCKER_APT_PACKAGES\="ffmpeg build-essential"  
./docker-setup.sh

筆記：

- 它接受以空格分隔的 apt 軟體包名稱清單。
- 如果進行了更改OPENCLAW_DOCKER_APT_PACKAGES，請重新運行docker-setup.sh以重建映像。

### [**號**](https://docs.openclaw.ai/install/docker#pre-install-extension-dependencies-optional)

### **預安裝擴充相依性（可選）**

具有自身相依性的擴充功能package.json（例如diagnostics-otel，matrix） msteams會在首次載入時安裝其 npm 依賴項。若要將這些依賴項打包到鏡像中，請OPENCLAW_EXTENSIONS在運行之前進行設定docker-setup.sh：

export OPENCLAW_EXTENSIONS\="diagnostics-otel matrix"  
./docker-setup.sh

或直接建置時：

docker build \--build-arg OPENCLAW_EXTENSIONS="diagnostics-otel matrix" .

筆記：

- 這接受以空格分隔的擴展目錄名稱列表（在extensions/）。
- 只有帶有擴展名的擴展程序package.json才會受到影響；沒有擴展名的輕量級插件將被忽略。
- 如果進行了更改OPENCLAW_EXTENSIONS，請重新運行docker-setup.sh以重建映像。

### [**號**](https://docs.openclaw.ai/install/docker#power-user-/-full-featured-container-opt-in)

### **進階使用者/全功能容器（選購）**

預設的 Docker 映像以安全性為先，並以非 rootnode 使用者身分執行。這雖然縮小了攻擊面，但也意味著：

- 運轉時不安裝任何系統軟體包。
- 預設不支援自製軟體
- 沒有捆綁 Chromium/Playwright 瀏覽器

如果您想要功能更全面的容器，請使用這些可選旋鈕：

1. 持久化保存/home/node，以便瀏覽器下載內容和工具快取能夠保留下來：

export OPENCLAW_HOME_VOLUME\="openclaw_home"  
./docker-setup.sh

2. 將系統依賴項嵌入鏡像中（可重複+持久）：

export OPENCLAW_DOCKER_APT_PACKAGES\="git curl jq"  
./docker-setup.sh

3. 安裝 Playwright 瀏覽器時無需進行任何變更npx（避免 npm 覆蓋衝突）：

docker compose run \--rm openclaw-cli \\  
 node /app/node_modules/playwright-core/cli.js install chromium

如果需要 Playwright 安裝系統依賴項，請使用 \`--build-image\` 重新建構鏡像， OPENCLAW_DOCKER_APT_PACKAGES而不是\--with-deps在執行時使用。

4. Persist Playwright 瀏覽器下載：

- 設定PLAYWRIGHT_BROWSERS_PATH=/home/node/.cache/ms-playwright於 docker-compose.yml。
- 確保/home/node透過以下方式持久化OPENCLAW_HOME_VOLUME，或 /home/node/.cache/ms-playwright透過以下方式掛載OPENCLAW_EXTRA_MOUNTS。

### [**號**](https://docs.openclaw.ai/install/docker#permissions-+-eacces)

### **權限 \+ EACCES**

該鏡像以node用戶 ID 1000 運作。如果您看到權限錯誤 /home/node/.openclaw，請確保您的主機綁定掛載點的擁有者是使用者 ID 1000。

範例（Linux 主機）：

sudo chown \-R 1000:1000 /path/to/openclaw-config /path/to/openclaw-workspace

如果為了方便而選擇以 root 使用者身分執行，則需要接受由此帶來的安全隱患。

### [**號**](https://docs.openclaw.ai/install/docker#faster-rebuilds-recommended)

### **更快的重建速度（建議）**

為了加快重建速度，請將 Dockerfile 排序，以便快取依賴層。這樣可以避免pnpm install在 lockfile 發生變更時重新執行：

FROM node:24-bookworm

\# Install Bun (required for build scripts)  
RUN curl \-fsSL https://bun.sh/install | bash  
ENV PATH="/root/.bun/bin:${PATH}"

RUN corepack enable

WORKDIR /app

\# Cache dependencies unless package metadata changes  
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./  
COPY ui/package.json ./ui/package.json  
COPY scripts ./scripts

RUN pnpm install \--frozen-lockfile

COPY . .  
RUN pnpm build  
RUN pnpm ui:install  
RUN pnpm ui:build

ENV NODE_ENV=production

CMD \["node","dist/index.js"\]

### [**號**](https://docs.openclaw.ai/install/docker#channel-setup-optional)

### **頻道設定（可選）**

使用 CLI 容器設定通道，然後根據需要重新啟動網關。

WhatsApp（二維碼）：

docker compose run \--rm openclaw-cli channels login

Telegram（機器人代幣）：

docker compose run \--rm openclaw-cli channels add \--channel telegram \--token "\<token\>"

Discord（機器人代幣）：

docker compose run \--rm openclaw-cli channels add \--channel discord \--token "\<token\>"

文件：[WhatsApp](https://docs.openclaw.ai/channels/whatsapp)、[Telegram](https://docs.openclaw.ai/channels/telegram)、[Discord](https://docs.openclaw.ai/channels/discord)

### [**號**](https://docs.openclaw.ai/install/docker#openai-codex-oauth-headless-docker)

### **OpenAI Codex OAuth（無頭 Docker）**

如果在精靈中選擇 OpenAI Codex OAuth，它會開啟一個瀏覽器 URL 並嘗試擷取回呼http://127.0.0.1:1455/auth/callback。在 Docker 或無頭環境中，該回呼可能會顯示瀏覽器錯誤。複製重定向到的完整 URL，並將其貼上回精靈以完成身份驗證。

### [**號**](https://docs.openclaw.ai/install/docker#health-checks)

### **健康檢查**

容器探測端點（無需身份驗證）：

curl \-fsS http://127.0.0.1:18789/healthz  
curl \-fsS http://127.0.0.1:18789/readyz

別名：/health和/ready。

/healthz是對「網關進程是否已啟動」的淺層存活探測。 /readyz在啟動寬限期內保持就緒狀態，然後503僅當所需的受管通道在寬限期結束後仍然斷開連接或稍後斷開連接時才變為就緒狀態。

Docker 映像內建了一個後台HEALTHCHECKping 功能/healthz。簡單來說：Docker 會持續檢查 OpenClaw 是否仍回應。如果檢查持續失敗，Docker 會將容器標記為已停止回應unhealthy，則編排系統（例如 Docker Compose 重新啟動策略、Swarm、Kubernetes 等）可以自動重新啟動或取代該容器。

已驗證的深度健康快照（網關 \+ 通道）：

docker compose exec openclaw-gateway node dist/index.js health \--token "$OPENCLAW_GATEWAY_TOKEN"

### [**號**](https://docs.openclaw.ai/install/docker#e2e-smoke-test-docker)

### **端對端冒煙測試（Docker）**

scripts/e2e/onboard-docker.sh

### [**號**](https://docs.openclaw.ai/install/docker#qr-import-smoke-test-docker)

### **QR導入冒煙測試（Docker）**

pnpm test:docker:qr

### [**號**](https://docs.openclaw.ai/install/docker#lan-vs-loopback-docker-compose)

### **LAN 與環回（Docker Compose）**

docker-setup.sh預設情況OPENCLAW_GATEWAY_BIND=lan下，主機存取可以 http://127.0.0.1:18789透過 Docker 連接埠發布實作。

- lan（預設）：主機瀏覽器 \+ 主機 CLI 可以存取已發佈的網關連接埠。
- loopback只有容器網路命名空間內的程序才能直接存取網關；主機發布的連接埠存取可能會失敗。

安裝腳本也會gateway.mode=local在設定完成後鎖定，因此 Docker CLI 指令預設以本機回環位址為目標。

舊版配置說明：使用綁定模式值（gateway.bind/ lan/ loopback/ custom/ tailnet）auto，而非主機別名（0.0.0.0，，，，127.0.0.1） 。localhost::::1

如果Docker CLI 指令出現錯誤Gateway target: ws://172.x.x.x:18789或重複出現錯誤，請執行：pairing required

docker compose run \--rm openclaw-cli config set gateway.mode local  
docker compose run \--rm openclaw-cli config set gateway.bind lan  
docker compose run \--rm openclaw-cli devices list \--url ws://127.0.0.1:18789

### [**號**](https://docs.openclaw.ai/install/docker#notes)

### **筆記**

- 網關綁定預設用於lan容器（OPENCLAW_GATEWAY_BIND）。
- Dockerfile CMD 使用\--allow-unconfigured；即使掛載了配置但未gateway.mode掛載， localDocker 仍會啟動。重寫 CMD 以強制執行此保護。
- 網關容器是會話的真實來源（\~/.openclaw/agents/\<agentId\>/sessions/）。

### [**號**](https://docs.openclaw.ai/install/docker#storage-model)

### **儲存模型**

- 持久性主機資料： Docker Compose 綁定掛載OPENCLAW_CONFIG_DIR到/home/node/.openclaw和OPENCLAW_WORKSPACE_DIR，/home/node/.openclaw/workspace因此這些路徑在容器替換後仍然存在。
- 臨時沙箱 tmpfs：啟用後agents.defaults.sandbox，沙箱容器將使用tmpfs、/tmp和/var/tmp。/run這些掛載點與頂層 Compose 堆疊分離，並隨沙箱容器一起消失。
- 磁碟成長熱點：檢視media/、agents/\<agentId\>/sessions/sessions.json轉錄 JSONL 檔案、cron/runs/\*.jsonl以及捲動檔案日誌（位於/tmp/openclaw/（或您配置的logging.file）。如果您還在 Docker 之外執行 macOS 應用程序，其服務日誌又會單獨列出：\~/.openclaw/logs/gateway.log、\~/.openclaw/logs/gateway.err.log和/tmp/openclaw/openclaw-gateway.log。

## [**號**](https://docs.openclaw.ai/install/docker#agent-sandbox-host-gateway-+-docker-tools)

## **代理沙箱（主機網關 \+ Docker 工具）**

深入探討：[沙盒](https://docs.openclaw.ai/gateway/sandboxing)

### [**號**](https://docs.openclaw.ai/install/docker#what-it-does)

### **它的作用**

agents.defaults.sandbox啟用此功能後，非主會話將在 Docker 容器內執行工具。網關仍然保留在您的主機上，但工具的執行是隔離的：

- 範圍："agent"預設（每個代理程式一個容器+工作區）
- 範圍："session"針對每個會話的隔離
- 每個作用域的工作區資料夾都掛載在/workspace
- 可選代理工作區存取權限（agents.defaults.sandbox.workspaceAccess）
- 允許/拒絕工具策略（拒絕獲勝）
- 入站媒體會被複製到活動沙盒工作區（media/inbound/\*），以便工具可以讀取它（使用workspaceAccess: "rw"，它會進入代理工作區）。

警告：scope: "shared"停用跨會話隔離。所有會話共享同一個容器和同一個工作區。

### [**號**](https://docs.openclaw.ai/install/docker#per-agent-sandbox-profiles-multi-agent)

### **每個智能體沙箱設定檔（多智能體）**

如果使用多代理路由，每個代理程式都可以覆蓋沙箱和工具設定： agents.list\[\].sandbox以及agents.list\[\].tools（加上agents.list\[\].tools.sandbox.tools）。這允許您在一個網關中運行混合存取等級：

- 完全存取權限（個人代理）
- 只讀工具 \+ 唯讀工作區（家庭/工作代理）
- 無檔案系統/shell工具（公共代理）

有關範例、優先順序和故障排除，請參閱[多代理沙箱和工具。](https://docs.openclaw.ai/tools/multi-agent-sandbox-tools)

### [**號**](https://docs.openclaw.ai/install/docker#default-behavior)

### **預設行為**

- 影像：openclaw-sandbox:bookworm-slim
- 每個代理人一個容器
- 代理工作區存取權限：（workspaceAccess: "none"預設）使用\~/.openclaw/sandboxes
  - "ro"將沙箱工作區保持在 \[此處應填寫具體位置\] /workspace，並將代理工作區以唯讀方式掛載到\[此處應填寫具體位置\] /agent（禁用write/ edit/ apply_patch）。
  - "rw"以讀寫模式掛載代理工作區/workspace
- 自動修剪：閒置時間超過 24 小時或年齡超過 7 天
- 網路：none預設為啟用（如果需要出口流量，請明確選擇啟用）
  - host已被屏蔽。
  - container:\<id\>預設情況下被阻止（命名空間連接風險）。
- 預設允許：，，，，，，，，，，，execprocessreadwriteeditsessions_listsessions_historysessions_sendsessions_spawnsession_status
- 預設拒絕browser：，，，，，，canvasnodescrondiscordgateway

### [**號**](https://docs.openclaw.ai/install/docker#enable-sandboxing)

### **啟用沙盒**

如果您打算在 中安裝軟體包setupCommand，請注意：

- 預設docker.network值為"none"（無出口）。
- docker.network: "host"已被屏蔽。
- docker.network: "container:\<id\>"預設被阻止。
- 緊急停止功能：agents.defaults.sandbox.docker.dangerouslyAllowContainerNamespaceJoin: true。
- readOnlyRoot: true阻止軟體包安裝。
- user必須以 root 使用者身分執行apt-get（可省略user或設定）。除非容器最近使用user: "0:0"過（約 5 分鐘內），否則OpenClaw 會在容器（或 Docker 配置）變更時自動重新建立容器。熱容器會記錄一條包含確切指令的警告日誌。setupCommandopenclaw sandbox recreate ...

{  
 agents: {  
 defaults: {  
 sandbox: {  
 mode: "non-main", // off | non-main | all  
 scope: "agent", // session | agent | shared (agent is default)  
 workspaceAccess: "none", // none | ro | rw  
 workspaceRoot: "\~/.openclaw/sandboxes",  
 docker: {  
 image: "openclaw-sandbox:bookworm-slim",  
 workdir: "/workspace",  
 readOnlyRoot: true,  
 tmpfs: \["/tmp", "/var/tmp", "/run"\],  
 network: "none",  
 user: "1000:1000",  
 capDrop: \["ALL"\],  
 env: { LANG: "C.UTF-8" },  
 setupCommand: "apt-get update && apt-get install \-y git curl jq",  
 pidsLimit: 256,  
 memory: "1g",  
 memorySwap: "2g",  
 cpus: 1,  
 ulimits: {  
 nofile: { soft: 1024, hard: 2048 },  
 nproc: 256,  
 },  
 seccompProfile: "/path/to/seccomp.json",  
 apparmorProfile: "openclaw-sandbox",  
 dns: \["1.1.1.1", "8.8.8.8"\],  
 extraHosts: \["internal.service:10.0.0.5"\],  
 },  
 prune: {  
 idleHours: 24, // 0 disables idle pruning  
 maxAgeDays: 7, // 0 disables max-age pruning  
 },  
 },  
 },  
 },  
 tools: {  
 sandbox: {  
 tools: {  
 allow: \[  
 "exec",  
 "process",  
 "read",  
 "write",  
 "edit",  
 "sessions_list",  
 "sessions_history",  
 "sessions_send",  
 "sessions_spawn",  
 "session_status",  
 \],  
 deny: \["browser", "canvas", "nodes", "cron", "discord", "gateway"\],  
 },  
 },  
 },  
}

硬化旋鈕位於agents.defaults.sandbox.docker： network，，，，，，，，，，，（僅限破碎 玻璃） 。還userpidsLimitmemorymemorySwapcpusulimitsseccompProfileapparmorProfilednsextraHostsdangerouslyAllowContainerNamespaceJoin

多代理：agents.defaults.sandbox.{docker,browser,prune}.\*透過以下方式覆寫每個代理程式（當/為時agents.list\[\].sandbox.{docker,browser,prune}.\* 忽略）。agents.defaults.sandbox.scopeagents.list\[\].sandbox.scope"shared"

### [**號**](https://docs.openclaw.ai/install/docker#build-the-default-sandbox-image)

### **建立預設沙箱鏡像**

scripts/sandbox-setup.sh

這是openclaw-sandbox:bookworm-slim使用.建構的Dockerfile.sandbox。

### [**號**](https://docs.openclaw.ai/install/docker#sandbox-common-image-optional)

### **沙盒通用鏡像（可選）**

如果您想要一個包含常用建置工具（Node、Go、Rust 等）的沙箱鏡像，請建立通用鏡像：

scripts/sandbox-common-setup.sh

這會建構一個系統openclaw-sandbox-common:bookworm-slim。使用方法如下：

{  
 agents: {  
 defaults: {  
 sandbox: { docker: { image: "openclaw-sandbox-common:bookworm-slim" } },  
 },  
 },  
}

### [**號**](https://docs.openclaw.ai/install/docker#sandbox-browser-image)

### **沙盒瀏覽器圖像**

若要在沙箱內運行瀏覽器工具，請建立瀏覽器鏡像：

scripts/sandbox-browser-setup.sh

這是openclaw-sandbox-browser:bookworm-slim使用 Dockerfile.sandbox-browser. 建構的。容器運行 Chromium，啟用了 CDP 和一個可選的 noVNC 觀察器（透過 Xvfb 進行 headful）。

筆記：

- Headful（Xvfb）相比 headless 減少了機器人阻塞。
- 仍然可以透過設定使用無頭模式agents.defaults.sandbox.browser.headless=true。
- 無需完整的桌面環境（GNOME）；Xvfb 提供顯示功能。
- 瀏覽器容器預設使用專用的 Docker 網路（openclaw-sandbox-browser）而不是全域網路bridge。
- 可選擇性地agents.defaults.sandbox.browser.cdpSourceRange透過 CIDR 限制容器邊緣 CDP 入口（例如172.21.0.1/32）。
- noVNC 觀察者存取預設受密碼保護；OpenClaw 提供了一個有效期很短的觀察者令牌 URL，該 URL 提供本機引導頁面並將密碼保存在 URL 片段中（而不是 URL 查詢中）。
- 瀏覽器容器啟動預設設定對於共用/容器工作負載而言較為保守，包括：
  - \--remote-debugging-address=127.0.0.1
  - \--remote-debugging-port=\<derived from OPENCLAW_BROWSER_CDP_PORT\>
  - \--user-data-dir=${HOME}/.chrome
  - \--no-first-run
  - \--no-default-browser-check
  - \--disable-3d-apis
  - \--disable-software-rasterizer
  - \--disable-gpu
  - \--disable-dev-shm-usage
  - \--disable-background-networking
  - \--disable-features=TranslateUI
  - \--disable-breakpad
  - \--disable-crash-reporter
  - \--metrics-recording-only
  - \--renderer-process-limit=2
  - \--no-zygote
  - \--disable-extensions
  - 如果agents.defaults.sandbox.browser.noSandbox已設置，\--no-sandbox則 \--disable-setuid-sandbox也會附加。
  - 以上三個圖形強化標誌是可選的。如果您的工作負載需要 WebGL/3D，請OPENCLAW_BROWSER_DISABLE_GRAPHICS_FLAGS=0設定不使用 \--disable-3d-apis、\--disable-software-rasterizer和\--disable-gpu。
  - 擴充功能的行為由以下方式控制\--disable-extensions，並且可以透過以下方式停用（啟用擴充功能）OPENCLAW_BROWSER_DISABLE_EXTENSIONS=0：對於依賴擴充功能的頁面或擴充功能較多的工作流程。
  - \--renderer-process-limit=2也可以透過以下方式配置 OPENCLAW_BROWSER_RENDERER_PROCESS_LIMIT；設定0後，當需要調整瀏覽器並發性時，Chromium 可以選擇其預設進程限制。

預設情況下，捆綁鏡像中會套用預設值。如果您需要不同的 Chromium 標誌，請使用自訂瀏覽器鏡像並提供您自己的入口點。

使用配置：

{  
 agents: {  
 defaults: {  
 sandbox: {  
 browser: { enabled: true },  
 },  
 },  
 },  
}

自訂瀏覽器圖片：

{  
 agents: {  
 defaults: {  
 sandbox: { browser: { image: "my-openclaw-browser" } },  
 },  
 },  
}

啟用後，代理將接收：

- 沙盒瀏覽器控制 URL（用於該browser工具）
- noVNC URL（如果已啟用且 headless=false）

請注意：如果您為工具設定了允許列表，請新增browser（並從拒絕清單中移除）該工具，否則該工具仍將被封鎖。清理規則（agents.defaults.sandbox.prune）也適用於瀏覽器容器。

### [**號**](https://docs.openclaw.ai/install/docker#custom-sandbox-image)

### **自訂沙盒圖像**

建立您自己的鏡像並將配置指向該鏡像：

docker build \-t my-openclaw-sbx \-f Dockerfile.sandbox .

{  
 agents: {  
 defaults: {  
 sandbox: { docker: { image: "my-openclaw-sbx" } },  
 },  
 },  
}

### [**號**](https://docs.openclaw.ai/install/docker#tool-policy-allow/deny)

### **工具策略（允許/拒絕）**

- deny戰勝allow。
- 如果allow為空：所有工具（除 deny 外）均可使用。
- 如果allow非空：只有其中的工具allow可用（不包括 deny）。

### [**號**](https://docs.openclaw.ai/install/docker#pruning-strategy)

### **剪枝策略**

兩個旋鈕：

- prune.idleHours移除 X 小時內未使用的容器（0 \= 停用）
- prune.maxAgeDays：移除超過 X 天的容器（0 \= 停用）

例子：

- 保持繁忙的會話，但限制會話時長： idleHours: 24，maxAgeDays: 7
- 切勿修剪 idleHours: 0：maxAgeDays: 0

### [**號**](https://docs.openclaw.ai/install/docker#security-notes)

### **安全票據**

- 硬牆僅適用於工具（exec/read/write/edit/apply_patch）。
- 預設情況下，僅限主機使用的工具（例如瀏覽器/相機/畫布）會被封鎖。
- 允許browser在沙箱中運作會破壞隔離性（瀏覽器在主機上執行）。

## [**號**](https://docs.openclaw.ai/install/docker#troubleshooting)

## **故障排除**

- 圖片缺失：使用[scripts/sandbox-setup.sh](https://github.com/openclaw/openclaw/blob/main/scripts/sandbox-setup.sh)或設定建置agents.defaults.sandbox.docker.image。
- 容器未運行：它將根據每個會話的需求自動建立。
- 沙盒中的權限錯誤：請將其設定docker.user為與已掛載工作區所有權相符的 UID:GID（或變更工作區資料夾的擁有權）。
- 未找到自訂工具：OpenClaw 使用sh \-lc登入 shell 執行命令，這會載入某些資源/etc/profile並可能重設 PATH 環境變數。請設定docker.env.PATH自訂工具路徑以將其新增至路徑/custom/bin:/usr/local/share/npm-global/bin（例如 \`/etc/openclaw/tools/\`），或/etc/profile.d/在 Dockerfile 中新增腳本。
