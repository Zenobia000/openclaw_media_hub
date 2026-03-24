# 前端規格書 (Frontend Specification) - OpenClaw GUI 應用程式

---

**版本:** `v1.0`
**日期:** `2026-03-24`
**狀態:** `Draft`
**依據:** `202_architecture_design.md v2.0`, `200_project_brief_prd.md v2.0`, `pencil-new.pen UI Mockup`

---

## 1. 概觀 (Overview)

### 1.1 技術決策 (Tech Decisions)

- **Framework**: Vanilla HTML/JS/CSS（無前端框架），PyWebView 載入本機靜態檔案
- **Styling**: Tailwind CSS（CDN 引入，無編譯流程）
- **State**: 前端完全無狀態，所有資料由 Python Bridge API 即時提供
- **Icons**: Lucide Icons（SVG icon set，與 Mockup 一致）
- **Font**: Inter（Google Fonts CDN，權重 400/500/600/700/800）
- **Deploy**: PyInstaller 打包為單一執行檔，前端靜態資源嵌入

### 1.2 核心依賴 (Key Dependencies)

| 依賴 | 引入方式 | 用途 |
| :--- | :--- | :--- |
| Tailwind CSS | CDN `<script>` | 樣式框架，支援 Dark Mode 與自訂 Design Tokens |
| Lucide Icons | CDN / 本機 bundle | 圖示庫（sidebar nav、狀態 badge、表單 icon） |
| Inter Font | Google Fonts CDN | 全域字型 |

> **注意**: 打包為離線版本時，需將 CDN 資源下載至 `frontend/` 目錄，確保無網路環境下可用。

---

## 2. 資訊架構 (Information Architecture)

### 2.1 網站地圖 (Sitemap)

```
Root (SPA - Single Page Application)
├── [MAIN]
│   ├── Dashboard              # 總覽頁（服務狀態、統計數據）
│   ├── Configuration          # 系統初始化精靈（3 步驟）
│   │   ├── Step 1: 環境與目錄設定
│   │   ├── Step 2: API 金鑰與服務設定
│   │   └── Step 3: 初始化執行與結果
│   └── Environment            # 環境檢查頁
└── [OPERATIONS]
    ├── Deploy Skills          # 技能部署
    ├── Install Plugins        # 外掛安裝
    └── Fix Plugins            # 外掛修復
```

### 2.2 路由表 (Route Table)

應用程式為 **單頁應用 (SPA)**，透過 JavaScript View 切換實現頁面導航，不使用 URL hash 或 history API（PyWebView 環境限制）。

| 頁面名稱 | View ID | 對應 Sidebar 項目 | 核心功能 | User Story |
| :--- | :--- | :--- | :--- | :--- |
| **Dashboard** | `view-dashboard` | Dashboard | 服務狀態總覽、快速操作入口 | US-003 |
| **Configuration** | `view-configuration` | Configuration | 3 步驟初始化精靈 | US-002 |
| **Environment** | `view-environment` | Environment | 系統依賴檢查 | US-001 |
| **Deploy Skills** | `view-deploy-skills` | Deploy Skills | 技能模組勾選部署 | US-005 |
| **Install Plugins** | `view-install-plugins` | Install Plugins | 外掛模組勾選安裝 | US-006 |
| **Fix Plugins** | `view-fix-plugins` | Fix Plugins | 外掛診斷與修復 | — |

---

## 3. 視覺與佈局 (Design & Layout)

### 3.1 版面配置 (Layout Strategy)

- **整體佈局**: 固定側邊欄 + 彈性主內容區（水平 Flexbox）
  - **Sidebar**: 固定寬度 `260px`，全高，左側
  - **Main Content**: `flex: 1`，`padding: 32px`，垂直 Flexbox，`gap: 24px`
- **視窗尺寸**: 固定 `1280 × 800`（PyWebView 視窗，不支援 RWD）
- **捲動**: 主內容區垂直捲動，Sidebar 不捲動

### 3.2 Design Tokens

以下 Design Tokens 對應 Tailwind CSS 自訂變數，透過 `tailwind.config` 擴展：

#### 色彩 (Colors)

| Token 名稱 | Hex 值 | 用途 |
| :--- | :--- | :--- |
| `bg-primary` | `#0e1015` | 頁面主背景、Sidebar 背景 |
| `bg-card` | `#161920` | 卡片、表單區塊背景 |
| `bg-input` | `#1e2028` | 輸入框背景 |
| `border-default` | `#1e2028` | 預設邊框、分隔線 |
| `text-primary` | `#f4f4f5` | 主要文字（標題、內容） |
| `text-secondary` | `#d4d4d8` | 次要文字（描述、副標題） |
| `text-muted` | `#838387` | 淡化文字（佔位符、版本資訊） |
| `accent-primary` | `#ff5c5c` | 主強調色（品牌紅、Active 狀態、主按鈕） |
| `accent-secondary` | `#14b8a6` | 次強調色（Teal，Gateway/DB 圖示） |
| `status-success` | `#22c55e` | 成功狀態（綠色，通過/已安裝） |
| `status-error` | `#ef4444` | 錯誤狀態（紅色，缺失/失敗） |
| `status-info` | `#3b82f6` | 資訊狀態（藍色，Docker/VS Code 圖示） |
| `text-on-accent` | `#FFFFFF` | 強調色上的文字（按鈕文字） |

#### 圓角 (Border Radius)

| Token 名稱 | 值 | 用途 |
| :--- | :--- | :--- |
| `radius-sm` | `6px` | 按鈕、輸入框、Nav Item |
| `radius-md` | `10px` | 卡片、表單區塊 |

#### 字型 (Typography)

| 用途 | Font | Size | Weight | Color |
| :--- | :--- | :--- | :--- | :--- |
| 頁面標題 | Inter | 24-26px | 700 | `text-primary` |
| 頁面副標題 | Inter | 14px | 400 | `text-secondary` |
| 區塊標題 | Inter | 16px | 600 | `text-primary` |
| 區塊描述 | Inter | 13px | 400 | `text-secondary` |
| 表單 Label | Inter | 12px | 500 | `text-secondary` |
| 表單 Input | Inter | 14px | 400 | `text-primary` / `text-muted`(placeholder) |
| 按鈕文字 | Inter | 14px | 500-600 | 依按鈕類型 |
| Badge 文字 | Inter | 11-12px | 500-600 | 依狀態色 |
| 版本資訊 | Inter | 11px | 400 | `text-muted` |
| Nav Section Label | Inter | 10-11px | 600-700 | `text-muted`，`letter-spacing: 0.5-1.2px` |

### 3.3 關鍵 UI 元件 (Key UI Components)

| 元件名稱 | 功能描述 | Props / Variants |
| :--- | :--- | :--- |
| **Button/Primary** | 主要操作按鈕（紅底白字） | `icon` (Lucide name), `label` (文字), `disabled` |
| **Button/Secondary** | 次要操作按鈕（卡片底+邊框） | `icon`, `label`, `disabled` |
| **Button/Danger** | 危險操作按鈕（紅底白字，用於停止等） | `icon`, `label`, `disabled` |
| **Input** | 表單輸入框（含 label + icon + placeholder） | `label`, `icon`, `placeholder`, `type` (text/password), `value`, `error` |
| **NavItem** | 側邊欄導航項目（未選中） | `icon` (Lucide name), `label`, `onClick` |
| **NavItem/Active** | 側邊欄導航項目（選中，紅色高亮底） | `icon`, `label` |
| **StatusBadge** | 狀態徽章（圓點 + 文字） | `status` (success/error/warning/info), `text` |
| **StatCard** | 統計卡片（icon + badge + 數值 + 描述） | `icon`, `value`, `label`, `status` |
| **CheckCard** | 環境檢查卡片（icon + name + version + badge） | `icon`, `iconColor`, `name`, `version`, `status` (installed/running/not-found) |
| **SectionPanel** | 表單區塊面板（icon + 標題 + 描述 + 內容） | `icon`, `iconColor`, `title`, `description`, `children` |
| **StepIndicator** | 步驟進度指示器（圓形編號 + 標題 + 連接線） | `steps[]`, `currentStep`, `completedSteps[]` |
| **ProgressItem** | 初始化進度項目（icon + 名稱 + 描述 + 狀態） | `name`, `description`, `status` (done/running/pending) |

### 3.4 Sidebar 結構

```
┌─────────────────────────┐
│ [OC] OpenClaw           │  ← Logo（紅底白字 OC + 品牌名）
├─────────────────────────┤
│ MAIN                    │  ← Section Label (10px, #838387, letter-spacing)
│  📊 Dashboard           │
│  ⚙️ Configuration       │
│  🖥️ Environment         │
├─────────────────────────┤
│ OPERATIONS              │  ← Section Label
│  🚀 Deploy Skills       │
│  🧩 Install Plugins     │
│  🔧 Fix Plugins         │
├─────────────────────────┤
│                         │  ← Spacer (flex: 1)
├─────────────────────────┤
│ OpenClaw v1.0.0         │  ← 版本資訊 (11px, #838387)
│ Docker · Windows 11     │  ← 環境資訊 (11px, #838387)
└─────────────────────────┘
```

- **Active 狀態**: 背景 `#1f1318`，邊框 `#ff5c5c30`，icon 變 `accent-primary`，文字變 `text-primary` + `font-weight: 600`
- **Hover 狀態**: 背景微亮（`bg-card` 色調）
- **Sidebar 邊框**: 右側 `1px solid border-default`

---

## 4. 頁面功能規格 (Page Specifications)

### 4.1 Environment（環境檢查頁）

**User Story (US-001)**:
> 身為使用者，我想要在 UI 上檢查系統是否符合最低規格，以便知道我的環境是否能順利安裝與執行 OpenClaw。

**UI 區域 (UI Zones)**:

1. **Header**
   - 標題: "Environment Check"（24px, 700）
   - 副標題: "Verify system dependencies and runtime environment"（14px, 400）
   - 右側: 環境 StatusBadge（顯示 Docker 環境類型）

2. **Summary Banner**
   - 全通過時: 綠色底 (`#4CAF5015`)，綠色邊框 (`#4CAF5040`)，check-circle icon
     - 標題: "All checks passed — environment is ready"
     - 描述: "X of X software checks passed · .env file verified"
   - 有失敗時: 切換為紅色/黃色樣式，顯示失敗數量
   - 右側: "Last checked: just now" 時間戳

3. **Cards Grid** — 水平排列的檢查卡片（Flexbox, gap: 16px, 等寬）
   - **Docker**: icon `container` (藍), 版本號, Installed badge
   - **Docker Desktop**: icon `activity` (綠), Running/Stopped badge
   - **VS Code**: icon `code` (藍), 版本號, Installed badge
   - **ngrok**: icon `globe`, 版本號或 "Not installed" 紅色提示, Not Found badge

4. **.env File Check** — 單行卡片
   - Icon: `file-text`，名稱: ".env Configuration File"
   - 描述: "Copied from .env.example — ready for configuration"
   - 右側: Verified / Missing badge

5. **Error Guidance** — 條件顯示（有失敗項目時才出現）
   - 紅色底 (`#F4433610`)，紅色邊框 (`#F4433630`)
   - alert-circle icon + 標題 "Action Required: Install [軟體名]"
   - 描述提供安裝指引

**Bridge API 呼叫**:

```javascript
// 觸發環境檢查
const result = await window.pywebview.api.check_env();
// 回傳: { checks: [{name, installed, version, message}], env_file: {exists, message} }
```

**驗收標準 (Acceptance Criteria)**:
- [ ] 點擊 "Environment" nav item 時，自動觸發環境檢查（或顯示上次結果）
- [ ] 每個軟體以獨立 CheckCard 顯示，綠色 = 通過，紅色 = 缺失
- [ ] Summary Banner 即時反映檢查結果統計
- [ ] 缺失軟體時顯示 Error Guidance 區塊
- [ ] .env 檔案存在性獨立顯示

---

### 4.2 Configuration — Step 1: 環境與目錄設定

**User Story (US-002)**:
> 身為使用者，我想要透過介面填寫金鑰與各項設定，以便輕鬆完成系統初始化。

**UI 區域 (UI Zones)**:

1. **Header**
   - 標題: "System Initialization"（26px, 700）
   - 副標題: "Set up your OpenClaw environment step by step"

2. **Step Indicator** — 水平 3 步驟指示器
   - Step 1: "Environment" — **Active**（紅底數字圓圈，粗體標題）
   - Step 2: "API Keys" — Pending（邊框數字圓圈，灰色標題）
   - Step 3: "Initialize" — Pending
   - 步驟間以 `2px` 橫線連接（完成=綠色，未完成=`border-default`）

3. **Deployment Mode 區塊** (SectionPanel)
   - Icon: `monitor` (紅), 標題: "Deployment Mode"
   - 3 個 Radio Card 水平排列：
     - **Docker Windows** (預設選中): 紅色邊框 `2px`，內有勾選圓圈（紅底白勾）
     - **Docker Linux/WSL2**: teal 邊框 `1px`，空心圓圈
     - **Native Linux (systemd)**: 灰色邊框 `1px`，空心圓圈
   - 每張卡片含: icon + 模式名稱 + 描述文字

4. **Gateway & Directory 區塊** (SectionPanel)
   - Icon: `globe` (teal), 標題: "Gateway & Directory"
   - 2×2 表單 Grid (gap: 16px):
     - Row 1: Working Directory (`placeholder: .openclaw`) + Gateway Bind Host (`placeholder: 0.0.0.0`)
     - Row 2: Gateway Mode (`placeholder: local`) + Gateway Port (`placeholder: 18789`)

5. **Action Bar** — 底部固定，上方 `1px` 分隔線
   - 右側: "Step 1 of 3" 文字 + "Next" Button/Primary (帶 `arrow-right` icon)

**Bridge API 呼叫**:

```javascript
// 偵測目前環境類型（預設選中值）
const platform = await window.pywebview.api.detect_platform();
// 回傳: { os, env_type, suggested_mode }
```

**驗收標準**:
- [ ] Deployment Mode 三選一 Radio Card，點擊切換
- [ ] Gateway 欄位有合理預設值（從 Bridge 取得或硬編碼）
- [ ] 點擊 "Next" 驗證必填欄位後進入 Step 2

---

### 4.3 Configuration — Step 2: API 金鑰與服務設定

**UI 區域 (UI Zones)**:

1. **Step Indicator** — Step 1 完成（綠底勾），Step 2 Active（紅底數字），Step 3 Pending

2. **API Keys & Tokens 區塊** (SectionPanel)
   - Icon: `key-round` (紅), 標題: "API Keys & Tokens"
   - 描述: "Enter your API credentials — stored securely via system keyring"
   - 2×2 表單 Grid:
     - Row 1: LINE Channel Access Token + LINE Channel Secret
     - Row 2: Discord Bot Token + OpenAI API Key (`placeholder: sk-...`)
   - 所有輸入框帶 `lock` icon，type=password

3. **Database & Services 區塊** (SectionPanel)
   - Icon: `database` (teal), 標題: "Database & Services"
   - 1×2 表單 Grid:
     - Database URL (`placeholder: postgresql://localhost:5432/openclaw`)
     - Redis URL (`placeholder: redis://localhost:6379`)

4. **Channel Plugins 區塊** (SectionPanel)
   - Icon: `message-circle` (藍), 標題: "Channel Plugins"
   - 描述: "LINE and Discord plugin credentials for messaging integration"
   - 2 行 Channel Row（帶品牌 icon + 名稱 + 描述 + Configured badge）:
     - LINE: 綠底 "L" icon (`#06C755`)，描述 "Channel Access Token + Secret configured above · Webhook URL via ngrok"
     - Discord: 紫底 "D" icon (`#5865F2`)，描述 "Bot Token configured above · DM policy: open, Group: allowlist"

5. **Security Note** — 底部安全提示
   - `shield-check` icon (紅) + 文字: "All keys are encrypted and stored securely using your operating system's credential manager (DPAPI / libsecret). Keys are never written to plain text files."

6. **Action Bar**
   - 左側: "Back" Button/Secondary (帶 `arrow-left` icon)
   - 右側: "Step 2 of 3" + "Next" Button/Primary (帶 `arrow-right` icon)

**Bridge API 呼叫**:

```javascript
// 儲存金鑰（逐一或批次）
await window.pywebview.api.save_keys({
  line_channel_access_token: "...",
  line_channel_secret: "...",
  discord_bot_token: "...",
  openai_api_key: "..."
});

// 儲存服務設定
await window.pywebview.api.save_config({
  database_url: "...",
  redis_url: "..."
});
```

**驗收標準**:
- [ ] 金鑰欄位以密碼模式顯示（可切換顯示/隱藏）
- [ ] Channel Plugins 區塊根據上方金鑰填寫狀態自動顯示 "Configured" / "Not Configured" badge
- [ ] 點擊 "Back" 回到 Step 1（保留已填資料）
- [ ] 點擊 "Next" 儲存金鑰至 keyring 後進入 Step 3

---

### 4.4 Configuration — Step 3: 初始化執行與結果

**UI 區域 (UI Zones)**:

1. **Step Indicator** — Step 1, 2 完成（綠底勾），Step 3 Active（紅底數字）

2. **Initialization Progress 面板** (左側，flex: 1)
   - Icon: `loader` (紅), 標題: "Initialization Progress"
   - 描述: "Running 6 steps to set up your environment"
   - 6 個 ProgressItem 垂直列表（以 `1px` 分隔線間隔）:
     1. "Create directory structure" — `.openclaw/agents/main/agent/, workspace/skills/`
     2. "Generate openclaw.json" — `Gateway config: mode=local, bind=0.0.0.0`
     3. "Store API keys via keyring" — `6 credentials saved to system credential manager`
     4. "Start Docker Compose" — `docker compose up -d`
     5. "Wait for Gateway ready" — `Health check on http://127.0.0.1:18789`
     6. "Configure speech-to-text" — `Auto-enable whisper if OpenAI key detected`
   - 狀態圖示:
     - Done: 綠底白勾圓圈 + "Done" 綠字
     - Running: 紅底白 loader 圓圈 + "Running..." 紅字
     - Pending: 灰色邊框數字圓圈 + "Pending" 灰字

3. **Dashboard Info 面板** (右側，固定寬度 `340px`)
   - Icon: `layout-dashboard` (teal), 標題: "Dashboard Info"
   - 提示: "Available after Gateway is ready"（Gateway ready 前欄位為 disabled）
   - Dashboard URL: 唯讀顯示 `http://127.0.0.1:18789/`
   - Access Token: 唯讀顯示（遮罩 `••••••••••••••••`）
   - Device Pairing 區塊（分隔線後）:
     - 說明: "Open the Dashboard URL in your browser, then approve the pending device request."
     - "Approve Pending Device" Button/Secondary（帶 `smartphone` icon）

4. **Action Bar**
   - 左側: "Back" Button/Secondary
   - 右側: "Step 3 of 3" + "Initialize" Button/Primary (帶 `play` icon)
   - 初始化執行中時: "Initialize" 按鈕 disabled，顯示 loading 狀態

**Bridge API 呼叫**:

```javascript
// 啟動初始化（非同步，透過回呼更新進度）
await window.pywebview.api.initialize({
  mode: "docker-windows",
  working_dir: ".openclaw",
  gateway_bind: "0.0.0.0",
  gateway_mode: "local",
  gateway_port: 18789
});
// 進度更新透過 Bridge 回呼: window.updateInitProgress(step, status, message)
```

**驗收標準**:
- [ ] 點擊 "Initialize" 後逐步更新 ProgressItem 狀態
- [ ] 進度更新不阻塞 UI（非同步回呼）
- [ ] 全部完成後 Dashboard Info 面板啟用，顯示 URL 與 Token
- [ ] 任一步驟失敗時停止後續步驟，顯示錯誤訊息與 "Retry" 按鈕

---

### 4.5 Dashboard（總覽頁）

**User Story (US-003)**:
> 身為使用者，我想要有清楚的啟動與停止按鈕，以便輕鬆管理 OpenClaw 服務狀態。

**UI 區域 (UI Zones)**:

1. **Header**
   - 標題: "Dashboard"（24px, 700）
   - 副標題: "Monitor and control your OpenClaw services"（14px, 400）
   - 右側: 服務狀態 StatusBadge
     - Running 時: 綠色圓點 + "Running" 綠字（`status-success`）
     - Stopped 時: 紅色圓點 + "Stopped" 紅字（`status-error`）

2. **StatCards Row** — 水平排列 4 張 StatCard（Flexbox, gap: 16px, 等寬）
   - **Services**: icon `server`（`accent-primary`），數值 "X/X"，描述 "Services Running"，badge 依全部啟動/部分啟動顯示 success/warning
   - **Uptime**: icon `clock`（`accent-secondary`），數值 "Xh Xm" 或 "—"（未啟動），描述 "Uptime"，badge info
   - **Skills**: icon `zap`（`status-info`），數值 數量，描述 "Skills Deployed"，badge info
   - **Plugins**: icon `puzzle`（`accent-secondary`），數值 數量，描述 "Plugins Installed"，badge info
   - 每張卡片: `bg-card` 背景, `radius-md` 圓角, `1px solid border-default` 邊框, padding `20px`

3. **Service Control 區塊** (SectionPanel)
   - Icon: `activity`（紅）, 標題: "Service Control"
   - 描述: "Start or stop the OpenClaw service stack"
   - **服務列表**: 垂直排列各服務狀態行（`1px` 分隔線間隔）
     - 每行: 服務 icon + 服務名稱（如 "Gateway", "Database", "Redis"）+ StatusBadge (running/stopped/error)
   - **控制按鈕組** — 底部，水平排列，gap: 12px
     - 服務未啟動時:
       - Button/Primary "Start Services"（`play` icon）
     - 服務運行中時:
       - Button/Secondary "Restart Services"（`refresh-cw` icon）
       - Button/Danger "Stop Services"（`square` icon）
     - 操作進行中時: 按鈕 disabled，文字變為 "Starting..." / "Stopping..."，icon 替換為旋轉 `loader` 動畫

4. **Quick Actions 區塊** (SectionPanel)
   - Icon: `compass`（`accent-secondary`）, 標題: "Quick Actions"
   - 描述: "Navigate to common tasks"
   - 3 張 Action Card 水平排列（Flexbox, gap: 16px, 等寬）:
     - **Environment Check**: icon `monitor`（`status-info`），標題 "Check Environment"，描述 "Verify dependencies"，點擊導航至 Environment 頁面
     - **Deploy Skills**: icon `zap`（`accent-primary`），標題 "Deploy Skills"，描述 "Manage skill modules"，點擊導航至 Deploy Skills 頁面
     - **Install Plugins**: icon `puzzle`（`accent-secondary`），標題 "Install Plugins"，描述 "Manage plugin modules"，點擊導航至 Install Plugins 頁面
   - 每張 Action Card: `bg-input` 背景, `radius-sm` 圓角, hover 時邊框變 `accent-primary` + 背景微亮, cursor pointer

**Bridge API 呼叫**:

```javascript
// 進入頁面時查詢服務狀態
const status = await window.pywebview.api.get_service_status();
// 回傳: {
//   running: true,
//   services: [
//     {name: "gateway", status: "running"},
//     {name: "database", status: "running"},
//     {name: "redis", status: "running"}
//   ],
//   uptime: "2h 35m",
//   skills_count: 5,
//   plugins_count: 3
// }

// 啟動服務
await window.pywebview.api.start_service();
// 回傳: { success: true, message: "All services started" }

// 停止服務
await window.pywebview.api.stop_service();
// 回傳: { success: true, message: "All services stopped" }

// 重啟服務
await window.pywebview.api.restart_service();
// 回傳: { success: true, message: "All services restarted" }
```

**狀態輪詢**:

Dashboard 進入後每 10 秒自動呼叫 `get_service_status()` 更新狀態，離開頁面時停止輪詢：

```javascript
let pollTimer = null;

function startPolling() {
  pollTimer = setInterval(async () => {
    const status = await window.pywebview.api.get_service_status();
    updateDashboardUI(status);
  }, 10000);
}

function stopPolling() {
  if (pollTimer) clearInterval(pollTimer);
}
```

**驗收標準**:
- [ ] 進入頁面時自動查詢服務狀態並渲染 StatCards
- [ ] 服務運行中顯示綠色 "Running" badge，未啟動顯示紅色 "Stopped" badge
- [ ] 啟動/停止/重啟按鈕依服務狀態動態切換
- [ ] 操作進行中按鈕 disabled 並顯示 loading 動畫
- [ ] 操作完成後自動刷新所有 StatCards 與服務列表
- [ ] Quick Actions 卡片點擊正確導航至對應頁面
- [ ] 每 10 秒自動輪詢服務狀態，離開頁面時停止輪詢

---

### 4.6 Deploy Skills（技能部署）

**User Story (US-005)**:
> 身為使用者，我想要透過介面一鍵部署技能模組，以便不需手動在命令列操作。

**UI 區域 (UI Zones)**:

1. **Header**
   - 標題: "Deploy Skills"（24px, 700）
   - 副標題: "Select and deploy skill modules to your OpenClaw instance"（14px, 400）
   - 右側: 已部署數量 badge — "X deployed" StatusBadge（`status-success` 色調）

2. **Summary Banner**
   - 有已部署技能時: 綠色底 (`#4CAF5015`)，綠色邊框 (`#4CAF5040`)，`check-circle` icon
     - 標題: "X of Y skills deployed"
     - 描述: "Select skills below to deploy or remove"
   - 無已部署技能時: 藍色底 (`#3b82f610`)，藍色邊框 (`#3b82f630`)，`info` icon
     - 標題: "No skills deployed yet"
     - 描述: "Select skills below and click Deploy to get started"

3. **Skills Checklist 區塊** (SectionPanel)
   - Icon: `zap`（`accent-primary`）, 標題: "Available Skills"
   - 描述: "Scanned from module_pack/ directory"
   - **Select All 列**: 頂部，checkbox + "Select All" 文字 + 底部 `1px` 分隔線
   - **技能列表**: 垂直排列，每項以 `1px` 分隔線間隔，padding `14px 16px`
     - 每行結構（水平 Flexbox, align-items: center）:
       - **Checkbox**: 16px 方框，勾選時紅底白勾（`accent-primary`），未勾選時 `border-default` 邊框
       - **Emoji**: 技能 emoji（16px），margin-left `12px`
       - **Info 區塊**（flex: 1, margin-left `12px`）:
         - 技能名稱（14px, 600, `text-primary`）
         - 技能描述（12px, 400, `text-secondary`），單行截斷 `text-overflow: ellipsis`
       - **Status Badge**:
         - 已部署: 綠底 "Deployed" badge（`status-success`）
         - 未部署: 灰底 "Available" badge（`text-muted`）
     - **Hover 效果**: 行背景變 `bg-input`
     - 已部署技能預設勾選

4. **Progress Overlay** — 條件顯示（部署/移除進行中時覆蓋技能列表）
   - 半透明背景覆蓋清單區域
   - 垂直排列 ProgressItem（結構同 Configuration Step 3）:
     - 每項: 技能 emoji + 技能名稱 + 狀態描述 + 狀態圖示
     - Done: 綠底白勾 + "Deployed" / "Removed" 綠字
     - Running: 紅底白 loader + "Deploying..." / "Removing..." 紅字
     - Pending: 灰色邊框 + "Pending" 灰字
     - Failed: 紅底白 `x` + "Failed: [error message]" 紅字

5. **Action Bar** — 底部固定，上方 `1px` 分隔線
   - 左側: 已選數量文字 "X skills selected"（14px, `text-secondary`）
   - 右側（水平排列, gap: 12px）:
     - Button/Danger "Remove Selected"（`trash-2` icon）— 僅當已勾選的項目中有「已部署」的技能時 enabled
     - Button/Primary "Deploy Selected"（`upload` icon）— 僅當已勾選的項目中有「未部署」的技能時 enabled
   - 操作進行中時: 兩個按鈕均 disabled

**Bridge API 呼叫**:

```javascript
// 進入頁面時載入技能清單
const skills = await window.pywebview.api.list_skills();
// 回傳: [
//   {name: "google-search", emoji: "🔍", description: "Search the web using Google", installed: true},
//   {name: "weather", emoji: "🌤️", description: "Get weather information", installed: false},
//   ...
// ]

// 部署選取的技能（非同步，透過回呼更新進度）
const result = await window.pywebview.api.deploy_skills(["weather", "calculator"]);
// 進度回呼: window.updateDeployProgress(skillName, status, message)
// 最終回傳: { success: true, deployed: ["weather", "calculator"], failed: [] }

// 移除選取的技能
const result = await window.pywebview.api.remove_skills(["google-search"]);
// 進度回呼: window.updateDeployProgress(skillName, status, message)
// 最終回傳: { success: true, removed: ["google-search"], failed: [] }
```

**驗收標準**:
- [ ] 進入頁面時自動載入技能清單，已部署的預設勾選並顯示 "Deployed" badge
- [ ] "Select All" checkbox 正確切換全選/全不選
- [ ] 勾選後 Action Bar 即時更新已選數量與按鈕啟用狀態
- [ ] 點擊 "Deploy Selected" 顯示 Progress Overlay，逐項更新部署狀態
- [ ] 點擊 "Remove Selected" 顯示確認提示後執行移除
- [ ] 部署/移除完成後自動刷新技能清單狀態
- [ ] 任一技能部署失敗時顯示錯誤訊息，其餘技能繼續執行

---

### 4.7 Install Plugins（外掛安裝）

**User Story (US-006)**:
> 身為使用者，我想要透過介面安裝外掛模組，以便不需手動在命令列操作。

**UI 區域 (UI Zones)**:

1. **Header**
   - 標題: "Install Plugins"（24px, 700）
   - 副標題: "Select and install plugin modules for OpenClaw"（14px, 400）
   - 右側: 已安裝數量 badge — "X installed" StatusBadge（`status-success` 色調）

2. **Summary Banner**
   - 有已安裝外掛時: 綠色底 (`#4CAF5015`)，綠色邊框 (`#4CAF5040`)，`check-circle` icon
     - 標題: "X of Y plugins installed"
     - 描述: "Select plugins below to install or uninstall"
   - 無已安裝外掛時: 藍色底 (`#3b82f610`)，藍色邊框 (`#3b82f630`)，`info` icon
     - 標題: "No plugins installed yet"
     - 描述: "Select plugins below and click Install to get started"

3. **Plugins Checklist 區塊** (SectionPanel)
   - Icon: `puzzle`（`accent-secondary`）, 標題: "Available Plugins"
   - 描述: "Messaging and integration plugins for OpenClaw"
   - **Select All 列**: 頂部，checkbox + "Select All" 文字 + 底部 `1px` 分隔線
   - **外掛列表**: 垂直排列，每項以 `1px` 分隔線間隔，padding `14px 16px`
     - 每行結構（水平 Flexbox, align-items: center）:
       - **Checkbox**: 16px 方框，勾選時紅底白勾（`accent-primary`），未勾選時 `border-default` 邊框
       - **Plugin Icon**: 品牌色圓形圖示（24px 圓，帶品牌縮寫字母），margin-left `12px`
         - LINE: 綠底 "L" icon（`#06C755`）
         - Discord: 紫底 "D" icon（`#5865F2`）
         - 其他外掛: 灰底首字母
       - **Info 區塊**（flex: 1, margin-left `12px`）:
         - 外掛名稱（14px, 600, `text-primary`）
         - 外掛描述（12px, 400, `text-secondary`），單行截斷
       - **Status Badge**:
         - 已安裝: 綠底 "Installed" badge（`status-success`）
         - 未安裝: 灰底 "Available" badge（`text-muted`）
     - **Hover 效果**: 行背景變 `bg-input`
     - 已安裝外掛預設勾選

4. **Progress Overlay** — 條件顯示（安裝/解除安裝進行中時覆蓋外掛列表）
   - 結構同 Deploy Skills 的 Progress Overlay
   - 每項: plugin icon + 外掛名稱 + 狀態描述 + 狀態圖示
     - Done: 綠底白勾 + "Installed" / "Uninstalled"
     - Running: 紅底白 loader + "Installing..." / "Uninstalling..."
     - Pending: 灰色邊框 + "Pending"
     - Failed: 紅底白 `x` + "Failed: [error message]"

5. **Action Bar** — 底部固定，上方 `1px` 分隔線
   - 左側: 已選數量文字 "X plugins selected"（14px, `text-secondary`）
   - 右側（水平排列, gap: 12px）:
     - Button/Danger "Uninstall Selected"（`trash-2` icon）— 僅當已勾選的項目中有「已安裝」的外掛時 enabled
     - Button/Primary "Install Selected"（`download` icon）— 僅當已勾選的項目中有「未安裝」的外掛時 enabled
   - 操作進行中時: 兩個按鈕均 disabled

**Bridge API 呼叫**:

```javascript
// 進入頁面時載入外掛清單
const plugins = await window.pywebview.api.list_plugins();
// 回傳: [
//   {name: "line-bot", description: "LINE messaging bot integration", installed: true, icon: "L", icon_color: "#06C755"},
//   {name: "discord-bot", description: "Discord bot integration", installed: false, icon: "D", icon_color: "#5865F2"},
//   ...
// ]

// 安裝選取的外掛（非同步，透過回呼更新進度）
const result = await window.pywebview.api.install_plugins(["discord-bot"]);
// 進度回呼: window.updatePluginProgress(pluginName, status, message)
// 最終回傳: { success: true, installed: ["discord-bot"], failed: [] }

// 解除安裝選取的外掛
const result = await window.pywebview.api.uninstall_plugins(["line-bot"]);
// 進度回呼: window.updatePluginProgress(pluginName, status, message)
// 最終回傳: { success: true, uninstalled: ["line-bot"], failed: [] }
```

**驗收標準**:
- [ ] 進入頁面時自動載入外掛清單，已安裝的預設勾選並顯示 "Installed" badge
- [ ] "Select All" checkbox 正確切換全選/全不選
- [ ] 勾選後 Action Bar 即時更新已選數量與按鈕啟用狀態
- [ ] 點擊 "Install Selected" 顯示 Progress Overlay，逐項更新安裝狀態
- [ ] 點擊 "Uninstall Selected" 顯示確認提示後執行解除安裝
- [ ] 安裝/解除安裝完成後自動刷新外掛清單狀態
- [ ] 任一外掛安裝失敗時顯示錯誤訊息，其餘外掛繼續執行

---

### 4.8 Fix Plugins（外掛修復）

**User Story**:
> 身為使用者，我想要透過介面診斷並修復有問題的外掛，以便不需手動排查命令列錯誤訊息。

**UI 區域 (UI Zones)**:

1. **Header**
   - 標題: "Fix Plugins"（24px, 700）
   - 副標題: "Diagnose and repair plugin issues"（14px, 400）
   - 右側: Button/Secondary "Run Diagnostics"（`scan` icon）— 手動觸發重新診斷

2. **Summary Banner** — 依診斷結果動態切換
   - 全部健康時: 綠色底 (`#4CAF5015`)，綠色邊框 (`#4CAF5040`)，`check-circle` icon
     - 標題: "All plugins are healthy"
     - 描述: "X plugins diagnosed — no issues found"
   - 有問題時: 紅色底 (`#F4433610`)，紅色邊框 (`#F4433630`)，`alert-triangle` icon
     - 標題: "X plugin(s) need attention"
     - 描述: "Issues detected — click Fix All or fix individually"
   - 診斷中: 藍色底 (`#3b82f610`)，藍色邊框 (`#3b82f630`)，旋轉 `loader` icon
     - 標題: "Running diagnostics..."
     - 描述: "Checking plugin health and configuration"
   - 右側: "Last checked: just now / X minutes ago" 時間戳（12px, `text-muted`）

3. **Diagnostic Report 區塊** (SectionPanel)
   - Icon: `stethoscope`（`accent-primary`）, 標題: "Diagnostic Report"
   - 描述: "Health status of installed plugins"
   - **外掛診斷列表**: 垂直排列，每項以 `1px` 分隔線間隔，padding `16px`
     - 每行結構（垂直 Flexbox）:
       - **上方列**（水平 Flexbox, align-items: center）:
         - Plugin Icon: 品牌色圓形圖示（同 Install Plugins 頁面）
         - 外掛名稱（14px, 600, `text-primary`），margin-left `12px`
         - StatusBadge（margin-left auto）:
           - Healthy: 綠底 "Healthy" badge（`status-success`）
           - Broken: 紅底 "Broken" badge（`status-error`）
           - Warning: 黃底 "Warning" badge（`#eab308`）
       - **下方列** — 僅在有問題時顯示（margin-top `10px`, padding-left `36px`）:
         - **Issues 清單**: 垂直排列，每項帶 `alert-circle` icon（12px, `status-error`）+ 問題描述文字（13px, `text-secondary`）
           - 例: "Missing configuration file: line-bot.json"
           - 例: "Plugin directory not found in workspace"
           - 例: "Docker container unhealthy: line-bot-service"
         - **Fix 按鈕**: Button/Secondary "Fix"（`wrench` icon, 小尺寸），右對齊，margin-top `8px`
     - **Hover 效果**: 行背景變 `bg-input`

4. **Fix Progress Overlay** — 條件顯示（修復進行中時覆蓋診斷列表）
   - 半透明背景覆蓋列表區域
   - 垂直排列 ProgressItem:
     - 每項: plugin icon + 外掛名稱 + 修復描述 + 狀態圖示
     - Done: 綠底白勾 + "Fixed" 綠字
     - Running: 紅底白 loader + "Fixing..." 紅字
     - Pending: 灰色邊框 + "Pending" 灰字
     - Failed: 紅底白 `x` + "Fix failed: [error message]" 紅字

5. **Action Bar** — 底部固定，上方 `1px` 分隔線
   - 左側: 診斷摘要文字 "X healthy · Y broken"（14px, `text-secondary`）
   - 右側:
     - Button/Primary "Fix All"（`wrench` icon）— 僅在有 broken 外掛時 enabled
   - 修復進行中時: 按鈕 disabled，文字變為 "Fixing..."

**Bridge API 呼叫**:

```javascript
// 進入頁面時自動執行診斷
const report = await window.pywebview.api.diagnose_plugins();
// 回傳: [
//   {name: "line-bot", status: "healthy", issues: [], icon: "L", icon_color: "#06C755"},
//   {name: "discord-bot", status: "broken", issues: [
//     "Missing configuration file: discord-bot.json",
//     "Docker container unhealthy: discord-bot-service"
//   ], icon: "D", icon_color: "#5865F2"}
// ]

// 修復單一外掛
const result = await window.pywebview.api.fix_plugins(["discord-bot"]);
// 進度回呼: window.updateFixProgress(pluginName, status, message)
// 最終回傳: { success: true, fixed: ["discord-bot"], failed: [] }

// 修復全部有問題的外掛
const result = await window.pywebview.api.fix_all_plugins();
// 進度回呼: window.updateFixProgress(pluginName, status, message)
// 最終回傳: { success: true, fixed: ["discord-bot"], failed: [] }
```

**驗收標準**:
- [ ] 進入頁面時自動執行診斷，診斷中顯示 loading 狀態
- [ ] 健康外掛顯示綠色 "Healthy" badge，問題外掛顯示紅色 "Broken" badge
- [ ] 有問題的外掛展開 Issues 清單，列出每個具體問題
- [ ] 每個 broken 外掛有獨立 "Fix" 按鈕可單獨修復
- [ ] "Fix All" 按鈕一次修復所有 broken 外掛，顯示 Progress Overlay
- [ ] 修復完成後自動重新執行診斷確認結果
- [ ] "Run Diagnostics" 按鈕可手動觸發重新診斷
- [ ] 修復失敗時顯示具體錯誤訊息，不影響其他外掛的修復流程

---

## 5. API 整合策略 (API Integration)

### 5.1 通訊機制

- **Client**: PyWebView Bridge — `window.pywebview.api.<method>()`
- **協定**: 同步 JavaScript → Python 呼叫，Python 端以 `threading` 非同步執行耗時操作
- **回傳格式**: 所有 API 回傳結構化 JSON，統一格式:

```javascript
// 成功
{ success: true, data: { ... } }

// 失敗
{ success: false, error: { type: "TIMEOUT" | "PERMISSION" | "NOT_FOUND" | "INTERNAL", message: "..." } }
```

### 5.2 非同步進度回呼

耗時操作（初始化、部署、安裝）透過 Bridge 反向呼叫前端 JavaScript 函式更新進度：

```python
# Python 端（bridge.py）
window.evaluate_js(f"window.updateInitProgress('{step}', '{status}', '{message}')")
```

```javascript
// 前端全域回呼函式
window.updateInitProgress = function(step, status, message) {
  // 更新 Configuration Step 3 的 ProgressItem 狀態
};

window.updateDeployProgress = function(skillName, status, message) {
  // 更新 Deploy Skills 的 Progress Overlay 狀態
};

window.updatePluginProgress = function(pluginName, status, message) {
  // 更新 Install Plugins 的 Progress Overlay 狀態
};

window.updateFixProgress = function(pluginName, status, message) {
  // 更新 Fix Plugins 的 Fix Progress Overlay 狀態
};
```

### 5.3 錯誤處理

| 錯誤類型 | 前端處理 |
| :--- | :--- |
| `TIMEOUT` | 顯示逾時提示卡片，提供「重試」按鈕 |
| `PERMISSION` | 顯示權限不足提示（如「請以系統管理員身分執行」） |
| `NOT_FOUND` | 顯示缺失軟體提示，導引至 Environment 頁面 |
| `INTERNAL` | 顯示通用錯誤訊息卡片，提供「重試」按鈕 |

### 5.4 Bridge API 清單

| API 方法 | 對應模組 | 回傳資料 |
| :--- | :--- | :--- |
| `check_env()` | `env_checker.py` | `{checks: [{name, installed, version, message}], env_file: {exists, message}}` |
| `detect_platform()` | `platform_utils.py` | `{os, env_type, suggested_mode}` |
| `save_keys(keys)` | `config_manager.py` | `{success, saved_count}` |
| `save_config(config)` | `config_manager.py` | `{success}` |
| `initialize(params)` | `initializer.py` | 透過回呼逐步回報，最終 `{success, dashboard_url, access_token}` |
| `get_service_status()` | `service_controller.py` | `{running, services: [{name, status}], uptime, skills_count, plugins_count}` |
| `start_service()` | `service_controller.py` | `{success, message}` |
| `stop_service()` | `service_controller.py` | `{success, message}` |
| `restart_service()` | `service_controller.py` | `{success, message}` |
| `list_skills()` | `skill_manager.py` | `[{name, emoji, description, installed}]` |
| `deploy_skills(names)` | `skill_manager.py` | 透過回呼逐項回報，最終 `{success, deployed, failed}` |
| `remove_skills(names)` | `skill_manager.py` | 透過回呼逐項回報，最終 `{success, removed, failed}` |
| `list_plugins()` | `plugin_manager.py` | `[{name, description, installed, icon, icon_color}]` |
| `install_plugins(names)` | `plugin_manager.py` | 透過回呼逐項回報，最終 `{success, installed, failed}` |
| `uninstall_plugins(names)` | `plugin_manager.py` | 透過回呼逐項回報，最終 `{success, uninstalled, failed}` |
| `diagnose_plugins()` | `plugin_manager.py` | `[{name, status, issues, icon, icon_color}]` |
| `fix_plugins(names)` | `plugin_manager.py` | 透過回呼逐項回報，最終 `{success, fixed, failed}` |
| `fix_all_plugins()` | `plugin_manager.py` | 透過回呼逐項回報，最終 `{success, fixed, failed}` |
