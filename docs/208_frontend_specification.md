# 前端規格書 (Frontend Specification) - OpenClaw GUI 應用程式

---

**版本:** `v1.1`
**日期:** `2026-03-26`
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
│   ├── Environment            # 環境檢查頁
│   └── Gateway               # Origin 存取控制 + 裝置配對管理 (ADR-006)
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
| **Gateway** | `view-gateway` | Gateway | Origin 存取控制、裝置配對管理 | ADR-006 |
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
  - **可捲動內容區域模式**: 當頁面內容超出 `800px` 可視範圍時（如 Configuration Step 1、Step 2），採用「固定 Action Bar + 可捲動內容區」佈局：
    ```
    main-content (flex: 1, vertical, 不捲動, 無 overflow)
    ├── scroll-area (flex: 1, overflow-y: auto, padding: 20px 24px 12px 24px)
    │   ├── Header
    │   ├── Step Indicator（如適用）
    │   └── 各內容面板（垂直排列, gap: 20px）
    └── action-bar (固定底部, padding: 16px 24px 32px 24px, border-top: 1px)
    ```
  - **Action Bar 固定規則**: Action Bar 不隨內容捲動，始終固定於主內容區底部，上方以 `1px solid border-default` 分隔線區隔
  - **捲動提示**: CSS 已定義 `.scroll-fade` class（`4px` 漸層淡出 `linear-gradient(transparent, bg-primary)`），可選擇性套用至 scroll-area 容器暗示可繼續捲動（目前未啟用）
  - **不適用頁面**: Dashboard、Environment、Configuration Step 3 等內容未溢出的頁面維持現有非捲動佈局；Deploy Skills / Install Plugins / Fix Plugins 的列表面板以獨立 `overflow-y: auto` 處理內部捲動

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
| `accent-secondary` | `#14b8a6` | 次強調色（Teal，Gateway 圖示、Quick Actions） |
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
│ [🐟] OpenClaw           │  ← Logo（圖片檔 logo.png + 品牌名）
├─────────────────────────┤
│ MAIN                    │  ← Section Label (10px, #838387, letter-spacing)
│  📊 Dashboard           │
│  ⚙️ Configuration       │
│  🖥️ Environment         │
│  🛡️ Gateway             │
├─────────────────────────┤
│ OPERATIONS              │  ← Section Label
│  🚀 Deploy Skills       │
│  🧩 Install Plugins     │
│  🔧 Fix Plugins         │
├─────────────────────────┤
│                         │  ← Spacer (flex: 1)
├─────────────────────────┤
│ OpenClaw v1.0.0         │  ← 版本資訊 (11px, #838387)
│ Docker · Windows        │  ← 環境模式 (11px, #838387, 動態)
└─────────────────────────┘
```

- **環境模式文字**（動態）: App 啟動時由 `detect_platform()` 取得 `current_mode`，Configuration Step 1 切換時即時更新
  | `deployment_mode` | 顯示文字 |
  | :--- | :--- |
  | `docker-windows` | Docker · Windows |
  | `docker-linux` | Docker · Linux/WSL2 |
  | `native-linux` | Native · Linux (systemd) |
  | `remote-ssh` | Remote · SSH |
- **連線狀態指示燈**（僅 `remote-ssh` 模式顯示，位於版本資訊上方）:
  | 狀態 | 圓點色 | 文字 | 說明 |
  | :--- | :--- | :--- | :--- |
  | Connected | `status-success` (#22c55e) | "Connected" | SSH 連線正常 |
  | Disconnected | `status-error` (#ef4444) | "Disconnected" | 未連線或連線已斷開 |
  | Connecting | `accent-secondary` (#14b8a6) | "Connecting..." | 正在建立 SSH 連線 |
  | Error | `status-error` (#ef4444) | "Connection Error" | 連線失敗（認證錯誤等） |
  - 格式：8px 圓點 + 文字 (11px, 400)，水平排列，gap 6px
  - 點擊可觸發 `get_connection_status()` 查詢最新狀態
  - 連線中斷時圓點以 pulse 動畫閃爍提示
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
   - 右側: 環境模式 StatusBadge（動態顯示當前部署模式名稱，如 "Docker" 或 "Native"）

2. **Summary Banner**
   - 全通過時: 綠色底 (`#4CAF5015`)，綠色邊框 (`#4CAF5040`)，check-circle icon
     - 標題: "All checks passed — environment is ready"
     - 描述: "X of X software checks passed · .env file verified"
   - 有失敗時: 切換為紅色/黃色樣式，顯示失敗數量
   - 右側: "Last checked: just now" 時間戳

3. **Cards Grid** — 水平排列的檢查卡片（Flexbox, gap: 16px, 自動換行 `flex-wrap: wrap`）

   卡片由 `check_env()` API 回傳動態渲染，不同部署模式回傳不同檢查項目。前端維護 icon mapping：

   ```javascript
   const CHECK_ICONS = {
     "Docker":           { icon: "container",  color: "status-info" },
     "Docker Compose":   { icon: "layers",     color: "status-info" },
     "Docker Desktop":   { icon: "activity",   color: "status-success" },
     "Docker Running":   { icon: "activity",   color: "status-success" },
     "Node.js":          { icon: "hexagon",    color: "status-success" },
     "OpenClaw CLI":     { icon: "terminal",   color: "accent-primary" },
     "jq":               { icon: "braces",     color: "accent-secondary" },
     "VS Code":          { icon: "code",       color: "status-info" },
     "ngrok":            { icon: "globe",      color: "text-muted" },
     "systemd Service":  { icon: "server",     color: "accent-secondary" },
   };
   ```

   **Docker 模式** (docker-windows / docker-linux) 顯示 5 張卡片：
   - Docker、Docker Compose、Docker Desktop/Running、VS Code、ngrok
   - 備註：Docker Compose 為獨立檢查項，實際 setup.sh 會分別驗證 `docker` 與 `docker compose version`

   **Native Linux 模式** (native-linux) 顯示 6 張卡片：
   - Node.js (≥18)、OpenClaw CLI、jq、VS Code、ngrok、systemd Service

4. **.env File Check** — 單行卡片
   - Icon: `file-text`，名稱: ".env Configuration File"
   - 描述: "Copied from .env.example — ready for configuration"
   - 右側: Verified / Missing badge

5. **Error Guidance** — 條件顯示（有失敗項目時才出現）
   - 紅色底 (`#F4433610`)，紅色邊框 (`#F4433630`)
   - alert-circle icon + 標題 "Action Required: Install [軟體名]"
   - 描述提供安裝指引（由 API 回傳的 `message` 欄位決定內容）

**Bridge API 呼叫**:

```javascript
// 觸發環境檢查（後端根據 persisted deployment_mode 決定檢查項目）
const result = await window.pywebview.api.check_env();
// 回傳: { checks: [{name, installed, version, message}], env_file: {exists, message} }
// Docker 模式回傳 5 項 checks，Native 模式回傳 6 項 checks
```

**驗收標準 (Acceptance Criteria)**:
- [ ] 點擊 "Environment" nav item 時，自動觸發環境檢查（或顯示上次結果）
- [ ] 檢查卡片數量與內容依當前部署模式動態變化
- [ ] 每個軟體以獨立 CheckCard 顯示，綠色 = 通過，紅色 = 缺失
- [ ] Summary Banner 即時反映檢查結果統計
- [ ] 缺失軟體時顯示 Error Guidance 區塊
- [ ] .env 檔案存在性獨立顯示
- [ ] Header StatusBadge 顯示當前部署模式名稱

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
   - 4 個 Radio Card（2×2 Grid，`grid-cols-2 gap-3`）：
     - **Docker Windows** (預設選中): 紅色邊框 `2px`，內有勾選圓圈（紅底白勾）
     - **Docker Linux/WSL2**: teal 邊框 `1px`，空心圓圈
     - **Native Linux (systemd)**: 灰色邊框 `1px`，空心圓圈
     - **Remote Server (SSH)**: 紫色邊框 `1px`（`#8b5cf6`），空心圓圈，icon: `cloud`
   - 每張卡片含: icon + 模式名稱 + 描述文字

4. **SSH Connection 區塊** (SectionPanel，**僅當 Deployment Mode = `remote-ssh` 時顯示**)
   - Icon: `terminal` (紫 `#8b5cf6`), 標題: "SSH Connection"
   - 描述: "Connect to your remote server via SSH"
   - 2×2 表單 Grid (`grid-cols-2 gap-4`):
     - Row 1: Host (`placeholder: 192.168.1.100`, **required**) + Port (`placeholder: 22`, type=number, default=22)
     - Row 2: Username (`placeholder: ubuntu`, **required**) + SSH Key File (`Browse` 按鈕，file picker，`placeholder: ~/.ssh/id_rsa`)
   - **驗證方式切換** (key/password toggle):
     - 預設顯示 SSH Key File 欄位，Password 欄位隱藏
     - 底部文字連結 "Use password instead" / "Use SSH key instead" 切換兩種驗證模式
     - 切換時對應欄位 show/hide（`hidden` class），互斥顯示
   - **Test Connection 按鈕** (`Button/Secondary`，帶 `wifi` icon):
     - 點擊後呼叫 `test_connection()` Bridge API
     - 按鈕右側顯示 inline 狀態 badge:
       - 測試中: `Connecting...`（橙色，帶 spinner）
       - 成功: `Connected — Ubuntu 22.04, 4 cores, 8GB`（綠色 badge）
       - 失敗: `Connection failed: reason`（紅色 badge）
   - **Next 按鈕**: 當 Deployment Mode = `remote-ssh` 時，需 SSH 測試通過（`test_connection` 成功）才啟用

5. **Gateway & Directory 區塊** (SectionPanel)
   - Icon: `globe` (teal), 標題: "Gateway & Directory"
   - 2×2 + 1×1 表單 Grid (gap: 16px):
     - Row 1: Config Directory (`placeholder: ~/.openclaw`, 對應 `OPENCLAW_CONFIG_DIR`) + Workspace Directory (`placeholder: ~/.openclaw/workspace`, 對應 `OPENCLAW_WORKSPACE_DIR`)
     - Row 2: Gateway Bind Host (`placeholder: lan`, 對應 `OPENCLAW_GATEWAY_BIND`；實際支援 5 種：`loopback` / `lan` / `auto` / `custom` / `tailnet`，v1.0 GUI 僅提供 text input，不限制值域) + Gateway Port (`placeholder: 18789`, 對應 `OPENCLAW_GATEWAY_PORT`)
     - Row 3: Bridge Port (`placeholder: 18790`, 對應 `OPENCLAW_BRIDGE_PORT`)
   - ~~Gateway Mode 欄位已移除~~：Docker/Native Linux 模式下由後端硬編碼為 `local`（`setup.sh` L128: `config set gateway.mode local`），使用者不需設定
   - **進階設定** (預設收合，點擊展開):
     - Timezone (`placeholder: Asia/Taipei`, 對應 `OPENCLAW_TZ`)
     - Docker Image (`placeholder: openclaw:local`, 對應 `OPENCLAW_IMAGE`)
     - Enable Sandbox (toggle, 對應 `OPENCLAW_SANDBOX`)

6. **Action Bar** — 底部固定，上方 `1px` 分隔線
   - 右側: "Step 1 of 3" 文字 + "Next" Button/Primary (帶 `arrow-right` icon)

**捲動行為**:
- 本頁內容（Deployment Mode + SSH Connection + Gateway & Directory）超出 `800px` 可視高度（實際內容高度約 `1124px`），採用 3.1 節定義的「固定 Action Bar + 可捲動內容區」模式
- Action Bar 固定於底部，Header 至 Gateway & Directory 區塊為可捲動範圍
- 初始載入時 Deployment Mode 與 SSH Connection 區塊完整可見，Gateway & Directory 區塊需向下捲動

> **Mockup 說明**: UI Mockup 中同時展示所有區塊（含 SSH Connection），以呈現完整 UI 結構。實作時 SSH Connection 區塊須依 Deployment Mode 條件顯示/隱藏（僅 `remote-ssh` 模式顯示）。當非 SSH 模式時，內容可能不溢出，此時 scroll-area 自然無需捲動。

**Bridge API 呼叫**:

```javascript
// 偵測目前環境類型（預設選中值 + 已持久化的模式）
const platform = await window.pywebview.api.detect_platform();
// 回傳: { os, env_type, suggested_mode, current_mode }
// current_mode: 已持久化的模式（可能為 null，表示首次使用）
// suggested_mode: 後端依 OS/環境自動建議的模式
```

**模式選擇行為**:

使用者選擇 Radio Card 後立即：
1. 呼叫 `save_config({"deployment_mode": selected_mode})` 持久化至 `{app_data}/openclaw-gui/gui-settings.json`
2. 更新前端全域狀態 `window.__currentMode`
3. 即時更新 Sidebar footer 環境模式文字

```javascript
// 持久化模式選擇
await window.pywebview.api.save_config({ deployment_mode: "docker-windows" });

// SSH 連線測試（僅 remote-ssh 模式）
const result = await window.pywebview.api.test_connection({
  host: "192.168.1.100", port: 22,
  username: "ubuntu", key_path: "~/.ssh/id_rsa"
  // 或 password auth: password: "secret"
});
// 回傳: { success: true, server_info: { os, cpu_cores, memory_gb, disk_gb } }

// SSH 連線建立（Step 1 完成後自動呼叫）
await window.pywebview.api.connect_remote({
  host: "192.168.1.100", port: 22,
  username: "ubuntu", key_path: "~/.ssh/id_rsa"
});
// 回傳: { success: true, server_info: { ... } }
```

**驗收標準**:
- [ ] Deployment Mode 四選一 Radio Card（2×2 Grid），點擊切換
- [ ] 已有 `current_mode` 時以其為預設選中；否則以 `suggested_mode` 為預設
- [ ] 切換模式後即時持久化並更新 Sidebar footer
- [ ] 選擇 "Remote Server (SSH)" 時動態顯示 SSH Connection 區塊
- [ ] SSH Connection 表單驗證：Host 與 Username 為必填
- [ ] Test Connection 按鈕顯示 inline 測試結果 badge
- [ ] 當 `remote-ssh` 模式時，Next 按鈕需 SSH 測試通過才啟用
- [ ] Gateway 欄位有合理預設值（從 Bridge 取得或硬編碼）
- [ ] 點擊 "Next" 驗證必填欄位後進入 Step 2

---

### 4.3 Configuration — Step 2: API 金鑰與服務設定

**UI 區域 (UI Zones)**:

1. **Step Indicator** — Step 1 完成（綠底勾），Step 2 Active（紅底數字），Step 3 Pending

2. **Model Providers 區塊** (SectionPanel)
   - Icon: `cpu` (紅), 標題: "Model Providers"
   - 描述: "Select providers and enter API keys — stored in .env with restricted permissions"
   - **供應商勾選清單**（水平 Flexbox, 可多選，勾選後展開對應金鑰欄位）:
     - OpenAI (`OPENAI_API_KEY`, placeholder: `sk-...`)
     - Anthropic (`ANTHROPIC_API_KEY`, placeholder: `sk-ant-...`)
     - Google Gemini (`GEMINI_API_KEY`)
     - OpenRouter (`OPENROUTER_API_KEY`)
     - Ollama (無金鑰，僅需 URL 設定)
     - 更多...（收合區，含 Amazon Bedrock, Mistral, NVIDIA, Together, ZAI, MiniMax 等）
   - 勾選的供應商下方展開:
     a. **金鑰輸入框**（帶 `lock` icon，type=password，可切換顯示/隱藏）
     b. **模型勾選清單** — 金鑰欄位下方
        - 標題行: "Available Models"（`text-xs font-medium text-gray-500`）
        - 呈現為 Flexbox wrap 的 checkbox-pill 列表（每個 pill: checkbox + 模型顯示名稱 `text-sm`）
        - 首次展開時**預設全選**
        - 動態供應商（Ollama）不顯示勾選清單，改為提示: "Models are discovered at runtime"
        - 無模型目錄的供應商（如 Amazon Bedrock）不顯示此區塊
   - **Primary Model 選取** — 所有供應商的模型勾選清單下方，`1px` 分隔線後
     - 標題: "Primary Model"（`text-xs font-medium text-gray-500`）
     - 下拉選單（`<select>`），列出所有已勾選供應商中被選取的模型
     - 選項格式: `provider/model-id`（e.g. `anthropic/claude-sonnet-4-6`）
     - 預設值: 第一個被勾選供應商的第一個模型
     - 變更 Primary 時即時更新下拉選單狀態

3. **Security Note** — 底部安全提示
   - `shield-check` icon (紅) + 文字: "All keys are stored in .env with restricted file permissions (owner-only access). Each server maintains its own independent .env configuration." (ADR-005)

5. **Action Bar** — 底部固定，上方 `1px` 分隔線
   - 左側: "Back" Button/Secondary (帶 `arrow-left` icon)
   - 右側: "Step 2 of 3" + "Next" Button/Primary (帶 `arrow-right` icon)

**捲動行為**:
- 本頁內容（Model Providers + Security Note）採用 3.1 節定義的「固定 Action Bar + 可捲動內容區」模式
- Action Bar 固定於底部，Header 至 Security Note 為可捲動範圍
- 初始載入時 Model Providers 區塊完整可見，Security Note 需向下捲動

**Bridge API 呼叫**:

```javascript
// 取得可用的供應商與管道列表（從 openclaw/extensions/ 掃描）
const providers = await window.pywebview.api.get_available_providers();
// 回傳: [{name: "openai", env_var: "OPENAI_API_KEY", placeholder: "sk-..."}, ...]

// 取得各供應商的可用模型目錄（從 MODEL_REGISTRY 讀取）
const models = await window.pywebview.api.get_provider_models();
// 回傳: {
//   "anthropic": [
//     {id: "claude-opus-4-6", name: "Claude Opus 4.6"},
//     {id: "claude-sonnet-4-6", name: "Claude Sonnet 4.6"},
//     {id: "claude-opus-4-5", name: "Claude Opus 4.5"},
//     {id: "claude-sonnet-4-5", name: "Claude Sonnet 4.5"},
//     {id: "claude-haiku-4-5", name: "Claude Haiku 4.5"}
//   ],
//   "openai": [
//     {id: "gpt-5.4", name: "GPT-5.4"},
//     {id: "gpt-5.4-pro", name: "GPT-5.4 Pro"},
//     {id: "gpt-5.4-mini", name: "GPT-5.4 Mini"},
//     {id: "gpt-5.4-nano", name: "GPT-5.4 Nano"},
//     {id: "gpt-5.2", name: "GPT-5.2"},
//     {id: "gpt-5.0", name: "GPT-5.0"}
//   ],
//   "google": [
//     {id: "gemini-3.1-pro", name: "Gemini 3.1 Pro"},
//     {id: "gemini-3.1-flash", name: "Gemini 3.1 Flash"}
//   ],
//   "ollama": [],  // 動態供應商回傳空陣列
//   ...
// }

// 載入目標機器 .env 中的既有金鑰與模型選擇（首次進入 Step 2 時呼叫）(ADR-005)
const envKeys = await window.pywebview.api.load_env_keys();
// 回傳: {
//   providers: {OPENAI_API_KEY: "sk-..."},
//   models: {
//     primary: "anthropic/claude-sonnet-4-6",
//     selected: ["anthropic/claude-opus-4-6", "anthropic/claude-sonnet-4-6", ...]
//   }
// }
// 本機模式：讀取本機 {config_dir}/.env + openclaw.json agents.defaults
// SSH 模式：透過 RemoteExecutor 讀取遠端 .env + openclaw.json

// 儲存金鑰與模型選擇（寫入目標機器的 .env + openclaw.json）(ADR-005)
await window.pywebview.api.save_keys({
  providers: {
    OPENAI_API_KEY: "sk-...",
    ANTHROPIC_API_KEY: "sk-ant-..."
  },
  model_selection: {
    primary: "anthropic/claude-sonnet-4-6",
    models: {
      "anthropic/claude-opus-4-6": {},
      "anthropic/claude-sonnet-4-6": {},
      "openai/gpt-5.4": {},
      "openai/gpt-5.4-mini": {}
    }
  }
});
// model_selection.primary → 寫入 openclaw.json agents.defaults.model.primary
// model_selection.models  → 寫入 openclaw.json agents.defaults.models（allowlist）
```

**驗收標準**:
- [ ] 進入頁面時呼叫 `get_available_providers()` / `get_available_channels()` / `get_provider_models()` 動態渲染可選項
- [ ] 金鑰欄位以密碼模式顯示（可切換顯示/隱藏）
- [ ] 勾選供應商/管道後展開對應金鑰欄位，取消勾選後收合
- [ ] 勾選供應商後，金鑰欄位下方顯示該供應商的模型勾選清單（預設全選）
- [ ] 動態供應商（Ollama）顯示提示文字而非模型勾選清單
- [ ] 底部 Primary Model 下拉選單僅列出所有已勾選供應商中被選取的模型
- [ ] Channel 區塊根據金鑰填寫狀態自動顯示 "Configured" / "Not Configured" badge
- [ ] 點擊 "Back" 回到 Step 1（保留已填資料）
- [ ] 進入 Step 2 時呼叫 `load_env_keys()` 載入既有金鑰、模型選擇與 Primary Model 並自動回填
- [ ] 點擊 "Next" 儲存金鑰至目標機器 `.env` + 模型選擇至 `openclaw.json` `agents.defaults` 後進入 Step 3

---

### 4.4 Configuration — Step 3: 初始化執行與結果

**UI 區域 (UI Zones)**:

1. **Step Indicator** — Step 1, 2 完成（綠底勾），Step 3 Active（紅底數字）

2. **Initialization Progress 面板** (左側，flex: 1)
   - Icon: `loader` (紅), 標題: "Initialization Progress"
   - 描述: "Running N steps to set up your environment"（N = 步驟數，Docker 11 / Native 8，動態帶入）
   - **Docker 模式** — 11 個 ProgressItem 垂直列表（以 `1px` 分隔線間隔）:
     1. "Validate environment" — `Checking Docker and Docker Compose availability`
     2. "Validate parameters" — `Checking required configuration values`
     3. "Create directory structure" — `~/.openclaw/identity/, agents/main/agent/, agents/main/sessions/`
     4. "Generate gateway token" — `Reading from config or generating new token`
     5. "Write environment file" — `.env with 16 variables (ports, paths, token, timezone)`
     6. "Build/Pull Docker image" — `Building openclaw:local or pulling image`（⚠️ 最耗時步驟，需進度提示）
     7. "Fix directory permissions" — `Setting ownership for container user`
     8. "Run onboarding" — `openclaw onboard --mode local --no-install-daemon`
     9. "Configure gateway" — `Set mode=local, bind, controlUi.allowedOrigins`
     10. "Start gateway" — `docker compose up -d openclaw-gateway`
     11. "Verify health" — `Health check on http://127.0.0.1:{port}/healthz`
   - **Native Linux 模式** — 8 個 ProgressItem:
     1. "Validate environment" — `Checking Node.js, OpenClaw CLI, systemd availability`
     2. "Validate parameters" — `Checking required configuration values`
     3. "Create directory structure" — `~/.openclaw/identity/, agents/main/agent/, sessions/`
     4. "Generate gateway token" — `Reading from config or generating new token`
     5. "Write environment file" — `.env with environment variables`
     6. "Configure gateway" — `Set mode=local, bind, controlUi.allowedOrigins`
     7. "Start gateway" — `systemctl start openclaw-gateway`
     8. "Verify health" — `Health check on http://127.0.0.1:{port}/healthz`
   - 狀態圖示:
     - Done: 綠底白勾圓圈 + "Done" 綠字
     - Running: 紅底白 loader 圓圈 + "Running..." 紅字
     - Pending: 灰色邊框數字圓圈 + "Pending" 灰字
     - Failed: 紅底白 `x` 圓圈 + "Failed" 紅字
   - **錯誤訊息顯示** (Failed 狀態時):
     - ProgressItem 下方展開錯誤區塊，背景 `bg-red-50 dark:bg-red-950`，圓角 `rounded-md`，`p-3 mt-2`
     - 錯誤文字: `text-sm text-red-700 dark:text-red-300`，`font-mono`，最多顯示 5 行，超出以 `overflow-y: auto max-h-[120px]` 捲動
     - 右上角「複製」按鈕: icon `copy`（`12x12`），hover 顯示 tooltip "Copy error"，點擊後 icon 切換為 `check` 持續 2 秒後恢復（不顯示文字）
     - 複製內容: 完整錯誤訊息文字（含步驟名稱前綴，例如 `[Build/Pull Docker image] error details...`）

3. **Dashboard Info 面板** (右側，固定寬度 `340px`)
   - Icon: `layout-dashboard` (teal), 標題: "Dashboard Info"
   - 提示: "Available after Gateway is ready"（Gateway ready 前欄位為 disabled）
   - Dashboard URL: 唯讀顯示 `http://127.0.0.1:18789/`
   - Access Token: 唯讀顯示 `OPENCLAW_GATEWAY_TOKEN`（遮罩 `••••••••••••••••`，附「複製」按鈕）
   - Device Pairing 區塊（分隔線後）:
     - 說明: "Open the Dashboard URL in your browser, then approve the pending device request."
     - "Approve Pending Device" Button/Secondary（帶 `smartphone` icon）

4. **Action Bar**
   - 左側: "Back" Button/Secondary
   - 右側: "Step 3 of 3" + "Initialize" Button/Primary (帶 `play` icon)
   - 初始化執行中時: "Initialize" 按鈕 disabled，顯示 loading 狀態

**Bridge API 呼叫**:

```javascript
// 啟動初始化（非同步，透過回呼更新 11 步進度）
await window.pywebview.api.initialize({
  mode: "docker-windows",
  config_dir: "~/.openclaw",           // OPENCLAW_CONFIG_DIR
  workspace_dir: "~/.openclaw/workspace", // OPENCLAW_WORKSPACE_DIR
  gateway_bind: "lan",                 // OPENCLAW_GATEWAY_BIND
  gateway_mode: "local",
  gateway_port: 18789,                 // OPENCLAW_GATEWAY_PORT
  bridge_port: 18790,                  // OPENCLAW_BRIDGE_PORT
  timezone: "Asia/Taipei",             // OPENCLAW_TZ
  docker_image: "openclaw:local"       // OPENCLAW_IMAGE
});
// 進度更新透過 Bridge 回呼: window.updateInitProgress(step, status, message, error)
// step: 1-11，對應 Initialization Progress 面板的 11 個步驟（Docker 模式）
// status: "done" | "running" | "pending" | "failed"
// error: (optional) 失敗時的完整錯誤訊息字串，供 Failed 狀態下顯示與複製
```

**驗收標準**:
- [ ] 點擊 "Initialize" 後逐步更新 ProgressItem 狀態
- [ ] 進度更新不阻塞 UI（非同步回呼）
- [ ] 全部完成後 Dashboard Info 面板啟用，顯示 URL 與 Token
- [ ] 任一步驟失敗時停止後續步驟，ProgressItem 顯示 Failed 狀態並展開錯誤區塊
- [ ] 錯誤區塊顯示完整錯誤訊息，附「複製」按鈕可將錯誤訊息複製至剪貼簿
- [ ] 複製成功後 icon 切換為 `check` 回饋，2 秒後恢復（不顯示文字）
- [ ] 錯誤區塊下方顯示 "Retry" 按鈕，點擊後從失敗步驟重新執行

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

2. **StatCards Row** — 水平排列 4 張 StatCard（Flexbox, gap: 12px, 等寬）
   - **Services**: icon `server`（`accent-primary`），數值 "X/1"，描述 "Services Running"（目前僅 Gateway），badge 依啟動/停止顯示 success/error
   - **Uptime**: icon `clock`（`accent-secondary`），數值 "Xh Xm" 或 "—"（未啟動），描述 "Uptime"，badge info
   - **Skills**: icon `zap`（`status-info`），數值 數量，描述 "Skills Deployed"，badge info
   - **Plugins**: icon `puzzle`（`accent-secondary`），數值 數量，描述 "Plugins Installed"，badge info
   - 每張卡片: `bg-card` 背景, `radius-md` 圓角, `1px solid border-default` 邊框, padding `20px`

3. **底部雙欄** — Service Control 與 Quick Actions 水平並排（Flexbox, gap: 16px, 各佔 `flex: 1`）

   **左欄: Service Control 區塊** (SectionPanel)
   - Icon: `activity`（紅）, 標題: "Service Control"
   - 描述: "Start or stop the OpenClaw service stack"
   - **服務列表**: 垂直排列各服務狀態行（`1px` 分隔線間隔）
     - 每行: 服務 icon + 服務名稱 + StatusBadge (running/stopped/error)
     - 服務列表由 `get_service_status()` API 動態回傳（目前僅 "Gateway" 一個服務）
   - **控制按鈕組** — 底部，水平排列，gap: 12px
     - 服務未啟動時:
       - Button/Primary "Start Services"（`play` icon）
     - 服務運行中時:
       - Button/Secondary "Restart Services"（`refresh-cw` icon）
       - Button/Danger "Stop Services"（`square` icon）
     - 操作進行中時: 按鈕 disabled，文字變為 "Processing..."，icon 替換為旋轉 `loader` 動畫

   **右欄: Quick Actions 區塊** (SectionPanel)
   - Icon: `compass`（`accent-secondary`）, 標題: "Quick Actions"
   - 描述: "Navigate to common tasks"
   - 3 張 Action Card **垂直排列**（Flexbox column, gap: 8px）:
     - **Environment Check**: icon `monitor`（`status-info`），標題 "Check Environment"，描述 "Verify dependencies"，點擊導航至 Environment 頁面
     - **Deploy Skills**: icon `zap`（`accent-primary`），標題 "Deploy Skills"，描述 "Manage skill modules"，點擊導航至 Deploy Skills 頁面
     - **Install Plugins**: icon `puzzle`（`accent-secondary`），標題 "Install Plugins"，描述 "Manage plugin modules"，點擊導航至 Install Plugins 頁面
   - 每張 Action Card: `bg-input` 背景, `radius-sm` 圓角, hover 時邊框變 `accent-primary` + 背景微亮, cursor pointer

**Bridge API 呼叫**:

```javascript
// 進入頁面時查詢服務狀態（後端根據 deployment_mode 決定查詢方式）
const status = await window.pywebview.api.get_service_status();
// 回傳: {
//   running: true,
//   services: [
//     {name: "gateway", status: "running"}
//   ],
//   uptime: "2h 35m",
//   skills_count: 5,
//   plugins_count: 3
// }
// Docker 模式: 透過 docker compose ps 查詢
// Native 模式: 透過 systemctl is-active 查詢

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
   - 描述: "Scanned from module_pack/ (custom modules) and openclaw/skills/ (community skills)"
   - **Tab 切換列**: 頂部，2 個 Tab:
     - "Custom Modules"（來自 `module_pack/`，自訂業務模組）
     - "Community Skills"（來自 `openclaw/skills/`，52 社群技能）
   - 當前 Tab 以 `accent-primary` 底線高亮
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
// 進入頁面時載入技能清單（掃描兩個來源）
const skills = await window.pywebview.api.list_skills();
// 回傳: [
//   {name: "google-search", emoji: "🔍", description: "Search the web using Google", installed: true, source: "community"},
//   {name: "weather", emoji: "🌤️", description: "Get weather information", installed: false, source: "community"},
//   {name: "booking", emoji: "📅", description: "Booking management module", installed: true, source: "module_pack"},
//   ...
// ]
// source: "module_pack" = 自訂業務模組, "community" = openclaw/skills/ 社群技能
// SKILL.md YAML frontmatter 提供 name, description, metadata.openclaw.emoji

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
   - 描述: "Extensions from openclaw/extensions/ — install by modifying openclaw.json plugins config"
   - **分類 Tab 列**: 頂部，4 個 Tab:
     - "Providers"（模型供應商: openai, anthropic, google, ollama, amazon-bedrock, openrouter, mistral, nvidia, together 等）
     - "Channels"（通訊管道: line, discord, telegram, slack, whatsapp, matrix, signal, msteams, zalo, irc 等）
     - "Tools"（工具: brave, perplexity, firecrawl, elevenlabs, tavily 等）
     - "Infrastructure"（基礎設施: memory-core, memory-lancedb）
   - 當前 Tab 以 `accent-secondary` 底線高亮
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
// 進入頁面時載入外掛清單（從 openclaw/extensions/ 掃描 openclaw.plugin.json）
const plugins = await window.pywebview.api.list_plugins();
// 回傳: [
//   {name: "openai", category: "provider", description: "OpenAI GPT models", installed: true, icon: "O", icon_color: "#10a37f", providers: ["openai", "openai-codex"]},
//   {name: "line", category: "channel", description: "LINE messaging integration", installed: true, icon: "L", icon_color: "#06C755", channels: ["line"]},
//   {name: "discord", category: "channel", description: "Discord bot integration", installed: false, icon: "D", icon_color: "#5865F2", channels: ["discord"]},
//   {name: "brave", category: "tool", description: "Brave Search API", installed: false, icon: "B", icon_color: "#FB542B"},
//   {name: "memory-core", category: "infrastructure", description: "Core memory system", installed: true, icon: "M", icon_color: "#838387"},
//   ...
// ]
// category 由 openclaw.plugin.json 的 providers[]/channels[] 欄位推導
// 安裝方式: 修改 openclaw.json 的 plugins.entries[id]（啟用狀態）、plugins.installs[id]（安裝紀錄）與 plugins.load.paths[]（載入路徑）

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

#### 4.7.1 Channel Init Wizard（Channel 初始化精靈）

**User Story (US-006b)**:
> 身為使用者，我想要在安裝 Channel 外掛後，透過引導式精靈完成該 Channel 的金鑰、Webhook 與存取政策設定，以便 Channel 能立即運作，不需手動編輯設定檔。

**觸發方式**:

1. **安裝後觸發**: Install Plugins 的 Progress Overlay 中，當 Channel 外掛安裝完成（allDone），在 "Done" 按鈕旁顯示 "Configure `<channel_label>`" Button/Primary（`settings` icon），點擊開啟該 Channel 的初始化精靈。僅對有定義初始化流程的 Channel 外掛顯示（由前端 `CHANNEL_INIT_REGISTRY` 判斷）。
2. **Re-entry 觸發**: 外掛列表中，已安裝且有初始化定義的 Channel 外掛行，"Installed" badge 右側顯示 "Configure" Button/Ghost（`settings` icon, 28px 高），點擊可重新進入精靈修改設定。

**UI 結構 — Modal Overlay**:

Modal 為全螢幕半透明遮罩（`position: fixed`, `inset: 0`, `z-[9998]`, `bg-black/50`），內含居中卡片（`max-w-2xl`, `bg-bg-primary`, `rounded-xl`, `shadow-2xl`, `max-h-[90vh]`, `overflow-y: auto`）:

```
+-----------------------------------------------------------+
|  [X close]                                                |
|                                                           |
|  <icon> <Channel Label> Channel Setup     [Step X of Y]  |
|                                                           |
|  Step Indicator: (1)──(2)──(3)                            |
|                                                           |
|  +-------------------------------------------------------+|
|  | SectionPanel: Step-specific content                   ||
|  |                                                       ||
|  +-------------------------------------------------------+|
|                                                           |
|  [Back]                              [Next / Save & Done] |
+-----------------------------------------------------------+
```

1. **Modal Header**
   - 左側: Channel Icon（品牌色圓形，32px）+ Channel Label + "Channel Setup"（20px, 700, `text-primary`）
   - 右側: "Step X of Y" 文字（14px, `text-muted`）+ 關閉按鈕（`x` icon, 20px, `text-muted`, hover `text-primary`）

2. **Step Indicator**
   - 水平排列，居中，與 Configuration 頁 Step Indicator 共用 `renderStepIndicator()` 元件
   - 步驟名稱由 `CHANNEL_INIT_REGISTRY[channel].steps[]` 定義
   - 完成步驟: 綠色圓 + 白色 `check` icon；當前步驟: `accent-primary` 圓 + 白色數字；未來步驟: `border-default` 圓 + `text-muted` 數字

3. **Step Content Area** — SectionPanel, padding `24px`, 內容依步驟切換

4. **Footer Action Bar**
   - 左側: "Back" Button/Ghost — Step 1 時 hidden
   - 右側:
     - Step 1~(N-1): "Next" Button/Primary（`arrow-right` icon）— 驗證通過時 enabled
     - Step N (最後): "Save & Complete" Button/Primary（`check` icon）— 儲存中顯示 spinner

---

**LINE 初始化精靈 — 步驟內容**:

**Step 1: Credentials（金鑰輸入）**

1. **Info Banner** — 藍色底 (`#3b82f610`)，藍色邊框 (`#3b82f630`)，`info` icon
   - 標題: "LINE Messaging API Credentials"
   - 描述: "You'll need a Channel Access Token and Channel Secret from the LINE Developers Console."
   - 連結文字: "Open LINE Developers Console →"（外部連結至 `https://developers.line.biz/console/`）

2. **Credential Fields** — 垂直排列, gap `16px`
   - 每個 field 結構:
     - Label（14px, 600, `text-primary`）
     - Input（type `password`, `w-full`, `h-10`, `bg-bg-input`, `border-border-default`, `rounded-lg`, `px-3`）
       - Placeholder: "Enter Channel Access Token" / "Enter Channel Secret"
       - 右側: Eye toggle icon（`eye` / `eye-off`），點擊切換明文/密碼顯示
     - **Re-entry 已有值時**: Input 顯示 masked preview（`••••••••...{後4碼}`），placeholder 改為 "Leave blank to keep current value"；該 field 不再 required

3. **Help Accordion** — 可展開/收合, 預設收合
   - Toggle 文字: "How to get these credentials?"（14px, `text-accent-secondary`, `chevron-down` icon）
   - 展開內容（Numbered List, 14px, `text-secondary`）:
     1. 前往 LINE Official Account Manager，在「聊天」設定中關閉自動回應訊息
     2. 點擊「Message API」啟用 Messaging API
     3. 前往 LINE Developers Console，選擇您的 Provider 與 Messaging API Channel
     4. 在「Basic settings」複製 Channel Secret
     5. 在「Messaging API」頁面點擊 Issue 產生 Channel Access Token

4. **驗證邏輯**:
   - 全新設定: 兩個 field 皆必填，任一為空時 "Next" disabled
   - Re-entry（has_value = true）: 空值表示保留現有值，"Next" 始終 enabled

---

**Step 2: Webhook Setup（Webhook 設定指引）**

1. **Webhook URL 卡片** — 綠色底 (`#4CAF5015`)，綠色邊框 (`#4CAF5040`)，`link` icon
   - 標題: "Your Webhook URL"
   - URL 顯示區: monospace 字型（`font-mono`, 14px, `bg-bg-tertiary`, `rounded-lg`, `p-3`），顯示後端回傳的 `template` URL（如 `https://<your-domain>/line/webhook`）
   - 右側: "Copy" Button/Ghost（`copy` icon），點擊複製 URL 至剪貼簿並 Toast "Copied!"
   - 下方附註（12px, `text-muted`）: "Replace `<your-domain>` with your public HTTPS domain or ngrok URL"
   - 若後端回傳 `local_url`（如 `http://127.0.0.1:18789/line/webhook`），額外顯示:
     - "Local URL (for testing): `http://127.0.0.1:18789/line/webhook`"（可複製）

2. **Setup Instructions** — SectionPanel, `clipboard-list` icon
   - 標題: "Setup Steps in LINE Console"
   - Numbered List（14px, `text-secondary`, 每項 padding `8px 0`, 分隔線間隔）:
     1. Open LINE Developers Console → select your Messaging API channel
     2. Go to the **Messaging API** tab
     3. Paste the Webhook URL above into the **Webhook URL** field
     4. Click **Verify** to test the connection
     5. Enable the **Use webhook** toggle
     6. Go to **Chat settings** in LINE Official Account Manager → disable **Auto-reply messages**
   - 每項可選配圖示（`external-link` for console links）

3. **此步驟為指引性質，無使用者輸入，"Next" 始終 enabled**

---

**Step 3: DM Policy & Complete（存取政策 + 儲存）**

1. **DM Policy Selector** — SectionPanel, `shield` icon
   - 標題: "Direct Message Policy"
   - 描述: "Control who can send direct messages to your LINE bot"（14px, `text-secondary`）
   - **Radio Card 列表**: 垂直排列, gap `8px`
     - 每張卡片結構（水平 Flexbox, `p-4`, `rounded-lg`, `border`, `cursor-pointer`）:
       - Radio input（16px 圓形，選中時 `accent-primary` 填充）
       - Info 區塊（flex: 1, margin-left `12px`）:
         - Policy Label（14px, 600, `text-primary`）
         - Policy Description（12px, 400, `text-secondary`）
       - 選中卡片: `border-accent-primary`（2px）, `bg-[accent-primary/5]`
       - 未選中: `border-border-default`（1px）, `bg-bg-primary`
     - 選項:
       - **Pairing (Recommended)**: "New users receive a pairing code. Messages are held until an admin approves them via `openclaw pairing approve line <CODE>`."
       - **Allowlist**: "Only users whose LINE User ID is in the allowlist can send messages. Others are silently ignored."
       - **Open**: "Any LINE user can send messages directly. No approval required."
       - **Disabled**: "Direct messages are completely disabled for this channel."
     - 預設選中: `pairing`

2. **Summary 區塊** — 灰色底 (`bg-bg-secondary`), `rounded-lg`, `p-4`, margin-top `16px`
   - 標題: "Configuration Summary"（14px, 600）
   - 列表（12px, `text-secondary`）:
     - "Channel: LINE"
     - "Credentials: Channel Access Token + Channel Secret → `.env`"
     - "DM Policy: `<selected_policy>`"
     - "Webhook: `<webhook_path>` → configure in LINE Console"
   - 每項前綴 `check-circle` icon（`text-status-success`）

3. **"Save & Complete" 按鈕**: 點擊後:
   - 按鈕變為 spinner + "Saving..."（disabled）
   - 呼叫 `save_channel_config("line", credentials, {dmPolicy: selectedPolicy})`
   - 成功: Toast "LINE channel configured successfully"（`status-success`）→ 關閉 Modal → 刷新 Install Plugins 列表
   - 失敗: Toast 顯示錯誤訊息（`status-error`），按鈕恢復 enabled

---

**Bridge API 呼叫**:

```javascript
// 開啟精靈時載入既有設定
const config = await window.pywebview.api.get_channel_config("line");
// 回傳: {
//   config: { enabled: true, dmPolicy: "pairing" },  // openclaw.json channels.line
//   credentials: {
//     LINE_CHANNEL_ACCESS_TOKEN: { has_value: true, preview: "...a1b2" },
//     LINE_CHANNEL_SECRET: { has_value: true, preview: "...x9y0" },
//   }
// }
// 全新設定時: { config: {}, credentials: { LINE_CHANNEL_ACCESS_TOKEN: { has_value: false, preview: "" }, ... } }

// 取得 Webhook URL
const webhook = await window.pywebview.api.get_webhook_url("line");
// 回傳: {
//   local_url: "http://127.0.0.1:18789/line/webhook",
//   template: "https://<your-domain>/line/webhook",
//   path: "/line/webhook",
//   note: "Use your public HTTPS domain or ngrok URL for production webhook"
// }

// 儲存 Channel 設定（金鑰 → .env，config → openclaw.json channels.line）
const result = await window.pywebview.api.save_channel_config("line",
  { LINE_CHANNEL_ACCESS_TOKEN: "token_value", LINE_CHANNEL_SECRET: "secret_value" },
  { dmPolicy: "pairing" }
);
// 回傳: { success: true, message: "Channel 'line' configured successfully" }
// Re-entry 保留現有金鑰時: credentials 中該 key 傳空字串或不傳，Backend 跳過不覆寫
```

**前端狀態管理**:

```javascript
// Channel 初始化精靈狀態
const channelInitState = {
  active: false,         // Modal 是否開啟
  channelName: null,     // "line", "discord", etc.
  step: 1,               // 當前步驟 (1-based)
  fieldValues: {},        // 金鑰欄位值 { "LINE_CHANNEL_ACCESS_TOKEN": "...", ... }
  dmPolicy: "pairing",   // 選中的 DM Policy
  saving: false,          // 儲存中
  webhookUrl: null,       // get_webhook_url() 回傳結果
  existingCredentials: {},// get_channel_config() 回傳的 credentials
  existingConfig: {},     // get_channel_config() 回傳的 config
};

// Channel 初始化 Registry（資料驅動，新增 Channel 只需新增條目）
const CHANNEL_INIT_REGISTRY = {
  line: {
    label: "LINE",
    icon: "L",
    iconColor: "#06C755",
    steps: ["Credentials", "Webhook Setup", "DM Policy"],
    fields: [
      { id: "LINE_CHANNEL_ACCESS_TOKEN", label: "Channel Access Token", type: "password", required: true },
      { id: "LINE_CHANNEL_SECRET", label: "Channel Secret", type: "password", required: true },
    ],
    webhookPath: "/line/webhook",
    webhookInstructions: [
      "Open LINE Developers Console and select your Messaging API channel",
      "Go to the Messaging API tab",
      "Paste the Webhook URL into the Webhook URL field",
      "Click Verify to test the connection",
      "Enable the Use webhook toggle",
      "In LINE Official Account Manager, go to Chat settings and disable Auto-reply messages",
    ],
    dmPolicyOptions: [
      { value: "pairing", label: "Pairing (Recommended)", desc: "New users receive a pairing code, must be approved before chatting" },
      { value: "allowlist", label: "Allowlist", desc: "Only pre-approved LINE User IDs can send messages" },
      { value: "open", label: "Open", desc: "Any LINE user can send messages directly" },
      { value: "disabled", label: "Disabled", desc: "Direct messages are disabled for this channel" },
    ],
    defaultDmPolicy: "pairing",
    consoleUrl: "https://developers.line.biz/console/",
    docsUrl: "/channels/line",
  },
  // 未來擴展: discord: { ... }, telegram: { ... }
};
```

**回呼函式**:

```javascript
// 全域函式綁定
window.openChannelInitWizard = function(channelName) { /* 開啟 Modal + 載入設定 */ };
window.closeChannelInitWizard = function() { /* 關閉 Modal + 重置 state */ };
window.channelInitNav = function(direction) { /* step +1/-1, 含 Step 1 驗證 */ };
window.saveChannelInit = function() { /* 收集資料 → save_channel_config → Toast → 關閉 */ };
window.setChannelInitDmPolicy = function(value) { /* 更新 channelInitState.dmPolicy */ };
```

**驗收標準**:
- [ ] Channel 外掛安裝完成後，Progress Overlay 顯示 "Configure `<label>`" 按鈕
- [ ] 已安裝 Channel 外掛列表行顯示 "Configure" 齒輪按鈕
- [ ] 點擊 Configure 開啟 Modal 精靈，Step Indicator 正確渲染 3 步驟
- [ ] Step 1: 金鑰欄位正確驗證（全新: 必填；Re-entry: 可為空保留現有值）
- [ ] Step 1: Eye toggle 正確切換密碼/明文顯示
- [ ] Step 1: Re-entry 時顯示 masked preview（`...後4碼`）
- [ ] Step 2: Webhook URL 正確顯示（依 gateway config 計算）
- [ ] Step 2: Copy 按鈕複製 URL 至剪貼簿
- [ ] Step 3: DM Policy Radio Cards 正確切換，預設 pairing
- [ ] Step 3: Summary 正確顯示所有設定摘要
- [ ] Save & Complete 成功: 金鑰寫入 `.env`、config 寫入 `openclaw.json` `channels.line`、Toast 成功訊息、Modal 關閉
- [ ] Save & Complete 失敗: 顯示錯誤 Toast，按鈕恢復可用
- [ ] 關閉 Modal（X 按鈕或遮罩點擊）正確重置狀態
- [ ] Deep merge: 儲存時不覆蓋 `openclaw.json` 其他區段

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
           - Warning: 黃底 "Warning" badge（`#eab308`）— reserved for future use, 目前未使用
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

### 4.9 Gateway 頁面 (ADR-006)

**進入條件**: 點擊 Sidebar MAIN 區段的 "Gateway" 項目

**頁面佈局**: 上方 Connection Info（整列）+ 下方兩欄式（左 Origin Access Control，右 Device Management）

#### 上方：Connection Info

1. **Section Panel**
   - Icon: `link` (`accent-secondary`), 標題: "Connection Info"
   - 說明: "Gateway endpoint and authentication for device pairing"

2. **Gateway URL**（唯讀）:
   - Label: "Gateway URL"
   - 顯示完整 HTTP 連結（例: `http://127.0.0.1:18789`）
   - 右側 `copy` icon 按鈕，點擊複製完整 URL 至剪貼簿

3. **Bind Mode**（下拉選單）:
   - Label: "Bind Mode"
   - `<select>` 下拉選單，選項:
     - `loopback` — 說明: "Only accessible from this machine (127.0.0.1)"
     - `lan` — 說明: "Accessible from all network interfaces (0.0.0.0)"
   - 選擇後下方顯示對應說明文字（`text-muted`, fontSize 11）
   - 變更後標記為 dirty，需點擊底部 Save 按鈕儲存

4. **Gateway Token**（遮罩顯示）:
   - Label: "Gateway Token"
   - 遮罩顯示 `••••••••••••••••` + `eye` Show/Hide 按鈕 + `copy` 複製按鈕
   - 左側 `lock` icon

5. **Control UI**（Checkbox）:
   - Label: "Control UI Enabled"
   - Checkbox + 說明: "Serve the Gateway Control UI web interface"（`text-muted`, fontSize 11）
   - 變更後標記為 dirty，需點擊底部 Save 按鈕儲存

6. **Save Settings 按鈕**: Button/Primary "Save Settings"（`save` icon），點擊呼叫 `save_gateway_settings()`
   - 僅在 Bind Mode 或 Control UI 有變更時 enabled
   - **儲存後自動重啟服務**：`save_gateway_settings()` 後端在寫入設定後，依部署模式自動重啟 Gateway 服務使變更生效：
     - **Docker** (Windows / Linux / WSL2): `docker compose restart openclaw-gateway`
     - **Native Linux** (systemd): `systemctl restart openclaw-gateway`
     - **Remote Server** (SSH): 透過 `RemoteExecutor` 在遠端執行 `systemctl restart openclaw-gateway`
   - **前端 UX 流程**：
     1. 點擊 Save Settings → 按鈕進入 loading 狀態（spinner + "Saving & Restarting..."）
     2. 後端完成設定寫入 + 服務重啟後回傳結果
     3. 成功：顯示 success toast "Settings saved. Gateway restarted."，按鈕恢復 disabled（無未儲存變更）
     4. 部分失敗（設定已寫入但重啟失敗）：顯示 warning toast "Settings saved but Gateway restart failed. Please restart manually."，按鈕恢復 disabled
     5. 失敗（設定寫入失敗）：顯示 error toast，按鈕恢復 enabled（仍有未儲存變更）

#### 左欄：Origin Access Control

1. **Section Panel** (與其他頁面一致的卡片樣式)
   - Icon: `globe` (`status-info`), 標題: "Origin Access Control"
   - 說明: "Manage which origins can access the Gateway Control UI"

2. **模式切換列**:
   - "Allow All Origins" 標題 + 'Set allowedOrigins to ["*"] — allows any origin' 說明
   - Toggle 開關（ON: `allowedOrigins: ["*"]`, OFF: 使用白名單）
   - 切換時即時更新 UI（儲存需點擊 Save Origins 按鈕）

3. **白名單編輯** (Toggle OFF 時顯示):
   - "Whitelist" 子標題
   - 已設定 origin 列表：每行顯示 `globe` icon + origin URL + `trash-2` 刪除按鈕
   - 底部: inline input (`placeholder: https://example.com`) + "Add" Button/Secondary (帶 `plus` icon, 小型)

4. **Save Origins 按鈕**: Button/Primary "Save Origins"（`save` icon），點擊呼叫 `save_allowed_origins()`

#### 右欄：Device Management

1. **Section Panel**
   - Icon: `smartphone` (`accent-primary`), 標題: "Device Management"
   - 說明: "Approve, reject, or remove paired devices"

2. **Pending Requests 區塊**:
   - "Pending Requests (N)" 子標題
   - 每個 pending device 一行：
     - `clock` icon (amber 底圓) + displayName/deviceId + remoteIp · roles
     - "Approve" Button/Primary (小型, `check` icon) + "Reject" Button/Danger (小型, `x` icon)

3. **Paired Devices 區塊** (分隔線後):
   - "Paired Devices (N)" 子標題
   - 每個 paired device 一行：
     - `smartphone` icon (green 底圓) + displayName/deviceId + remoteIp
     - 備註欄位（inline 可編輯 text input，blur 時自動儲存至 `gui-settings.json`）
     - `trash-2` 刪除按鈕

4. **Refresh 按鈕**: Button/Secondary "Refresh"（`refresh-cw` icon），位於列表底部

**Bridge API 呼叫**:

```javascript
// 讀取 Gateway 連線資訊
const info = await window.pywebview.api.get_gateway_info();
// info.data = {
//   url: "http://127.0.0.1:18789",
//   bind: "loopback",                          // "loopback" | "lan"
//   gateway_token: "...",
//   control_ui_enabled: true
// }

// 儲存 Gateway 設定（Bind Mode + Control UI）+ 自動重啟服務
const result = await window.pywebview.api.save_gateway_settings({
  bind: "lan",              // "loopback" | "lan"
  control_ui_enabled: true
});
// result.data = {
//   saved: true,
//   restarted: true,              // false 表示重啟失敗（設定已寫入）
//   restart_error: null            // 重啟失敗時包含錯誤訊息
// }

// 讀取 allowedOrigins
const origins = await window.pywebview.api.get_allowed_origins();
// origins.data = { origins: ["http://127.0.0.1:18789", ...], is_wildcard: false }

// 儲存 allowedOrigins
await window.pywebview.api.save_allowed_origins({
  origins: ["http://127.0.0.1:18789", "http://localhost:18789"],
  allow_all: false
});

// 列出所有裝置（pending + paired）
const devices = await window.pywebview.api.list_devices();
// devices.data = { pending: [...], paired: [...] }

// 拒絕 pending 裝置
await window.pywebview.api.reject_device({ request_id: "uuid-string" });

// 移除 paired 裝置
await window.pywebview.api.remove_device({ device_id: "device-id" });

// 儲存/讀取裝置備註（本地 gui-settings.json）
await window.pywebview.api.save_device_note({ device_id: "id", note: "備註" });
const notes = await window.pywebview.api.get_device_notes();
// notes.data = { notes: { "device-id-1": "辦公室桌機", "device-id-2": "測試手機" } }
```

**Acceptance Criteria**:

- [ ] Sidebar MAIN 區段顯示 Gateway 項目（`shield` icon）
- [ ] 進入頁面時自動載入 Connection Info、allowedOrigins 和裝置列表
- [ ] Gateway URL 顯示完整 HTTP 連結，可複製至剪貼簿
- [ ] Bind Mode 下拉選單切換 loopback/lan，選擇後顯示對應說明
- [ ] Gateway Token 遮罩顯示，支援 Show/Hide 與 Copy
- [ ] Control UI Enabled checkbox 控制是否啟用 Control UI
- [ ] Bind Mode 或 Control UI 變更後，Save Settings 按鈕 enabled，儲存呼叫 save_gateway_settings()
- [ ] Save Settings 儲存後自動重啟 Gateway 服務，按鈕顯示 "Saving & Restarting..." loading 狀態
- [ ] 儲存+重啟成功顯示 success toast；設定已存但重啟失敗顯示 warning toast；設定寫入失敗顯示 error toast
- [ ] Allow All Origins toggle 切換後更新 UI，點擊 Save Origins 儲存至 openclaw.json
- [ ] 白名單可新增/刪除 origin，點擊 Save Origins 後儲存
- [ ] Pending 裝置可 Approve / Reject，操作後自動刷新列表
- [ ] Paired 裝置可添加備註（blur 自動儲存）和 Remove
- [ ] Refresh 按鈕重新載入裝置列表
- [ ] 所有操作的錯誤狀態有結構化 UI 回饋

---

## 5. API 整合策略 (API Integration)

### 5.0 部署模式與後端分流 (Deployment Mode Strategy)

應用程式支援 4 種部署模式，前端選項對應 3 種後端策略：

| 前端選項 | 後端策略 | 服務控制 | Gateway CLI |
| :--- | :--- | :--- | :--- |
| Docker Windows | **Docker** | `docker compose up/down/restart` | `docker compose run --rm openclaw-cli <cmd>` |
| Docker Linux/WSL2 | **Docker** | 同上 | 同上 |
| Native Linux (systemd) | **Native** | `systemctl start/stop/restart openclaw-gateway` | `openclaw <cmd>`（直接呼叫） |
| Remote Server (SSH) | **Remote** | 透過 `RemoteExecutor` 在遠端執行 `systemctl` 指令 (**v1.0 限制：遠端僅支援 Native Linux**) | 透過 SSH 在遠端執行 `openclaw <cmd>` |

**模式持久化**: 使用者選擇的模式儲存於 `{app_data}/openclaw-gui/gui-settings.json`（如 `%APPDATA%/openclaw-gui/` 或 `~/.config/openclaw-gui/`，與 `openclaw.json` 分開），所有後端 API 自動讀取此設定決定分流邏輯，前端不需在每次 API 呼叫傳遞 mode 參數。Remote SSH 模式額外儲存 `ssh_host`, `ssh_port`, `ssh_username`, `ssh_key_path` 欄位。

**影響範圍**:
- `check_env()`: Docker 模式檢查 4 項（Docker, Docker Desktop, VS Code, ngrok），Native 模式檢查 6 項（Node.js, OpenClaw CLI, jq, VS Code, ngrok, systemd），Remote 模式透過 SSH 在遠端執行 Native 模式檢查
- `initialize()`: Step 4 服務啟動指令不同；Remote 模式透過 SSH 在遠端建立目錄、寫入 `.env`、啟動服務
- `start_service()` / `stop_service()` / `restart_service()`: 控制指令不同；Remote 模式透過 `RemoteExecutor` 路由至遠端
- `get_service_status()`: 查詢方式不同（`docker compose ps` vs `systemctl is-active`）；Remote 模式透過 SSH 查詢遠端狀態
- `deploy_skills()`: Remote 模式使用 `TransferService` 將本機 `module_pack/` 透過 SFTP 上傳至遠端
- `connect_remote()` / `disconnect_remote()` / `get_connection_status()`: 僅 Remote 模式使用，管理 SSH 連線生命週期

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

window.updateConnectionStatus = function(status, message) {
  // 更新 Sidebar 連線狀態指示燈與 SSH 連線狀態
  // status: "connected" | "disconnected" | "connecting" | "error"
  // message: 連線資訊或錯誤描述
};
```

### 5.3 錯誤處理

| 錯誤類型 | 前端處理 |
| :--- | :--- |
| `TIMEOUT` | 顯示逾時提示卡片，提供「重試」按鈕 |
| `PERMISSION` | 顯示權限不足提示（如「請以系統管理員身分執行」） |
| `NOT_FOUND` | 顯示缺失軟體提示，導引至 Environment 頁面 |
| `INTERNAL` | 顯示通用錯誤訊息卡片，提供「重試」按鈕 |
| `CONNECTION_LOST` | 頂部紅色警示條（persistent banner）："SSH connection lost — reconnecting..."；Sidebar 指示燈切換至 `error` 狀態；自動重連 3 次（指數退避 2/4/8s），失敗後顯示「Reconnect」按鈕 |
| `AUTH_FAILED` | SSH 認證失敗提示卡片："Authentication failed — please check your credentials"；導引回 Configuration Step 1 SSH Connection 表單 |
| `SFTP_TIMEOUT` | SFTP 傳輸逾時提示卡片："File transfer timed out"；提供「重試 (Retry)」與「跳過 (Skip)」兩個按鈕 |

### 5.4 Bridge API 清單

| API 方法 | 對應模組 | 回傳資料 |
| :--- | :--- | :--- |
| `check_env()` | `env_checker.py` | `{checks: [{name, installed, version, message}], env_file: {exists, message}}` |
| `detect_platform()` | `platform_utils.py` | `{os, env_type, suggested_mode, current_mode}` |
| `save_keys(keys)` | `config_manager.py` / `executor` (remote) | `{success, saved_count}` — 本機寫 .env + 模型選擇寫入 openclaw.json `agents.defaults`，SSH 模式透過 executor (ADR-005) |
| `save_config(config)` | `config_manager.py` | `{success}` |
| `initialize(params)` | `initializer.py` | 透過回呼逐步回報，最終 `{success, dashboard_url, access_token}` |
| `get_service_status()` | `service_controller.py` | `{running, services: [{name, status}], uptime, skills_count, plugins_count}` |
| `start_service()` | `service_controller.py` | `{success, message}` |
| `stop_service()` | `service_controller.py` | `{success, message}` |
| `restart_service()` | `service_controller.py` | `{success, message}` |
| `list_skills()` | `skill_manager.py` | `[{name, emoji, description, installed, source}]` |
| `deploy_skills(names)` | `skill_manager.py` | 透過回呼逐項回報，最終 `{success, deployed, failed}` |
| `remove_skills(names)` | `skill_manager.py` | 透過回呼逐項回報，最終 `{success, removed, failed}` |
| `list_plugins()` | `plugin_manager.py` | `[{name, category, description, installed, icon, icon_color}]` |
| `install_plugins(names)` | `plugin_manager.py` | 透過回呼逐項回報，最終 `{success, installed, failed}` |
| `uninstall_plugins(names)` | `plugin_manager.py` | 透過回呼逐項回報，最終 `{success, uninstalled, failed}` |
| `diagnose_plugins()` | `plugin_manager.py` | `[{name, status, issues, icon, icon_color}]` |
| `fix_plugins(names)` | `plugin_manager.py` | 透過回呼逐項回報，最終 `{success, fixed, failed}` |
| `fix_all_plugins()` | `plugin_manager.py` | 透過回呼逐項回報，最終 `{success, fixed, failed}` |
| `get_available_providers()` | `plugin_manager.py` | `[{name, env_var, placeholder}]` — 從 extensions 取得可用供應商列表 |
| `get_provider_models()` | `registries.py` | `{provider_name: [{id, name}]}` — 各供應商的可用模型目錄 |
| `load_env_keys()` | `config_manager.py` | `{providers, channels, models: {primary, selected}}` — 讀取 .env 金鑰 + openclaw.json 模型選擇 |
| `get_available_channels()` | `plugin_manager.py` | `[{name, fields: [{key, label}], icon, icon_color}]` — 從 extensions 取得可用管道列表 |
| `get_channel_config(channel_name)` | `bridge.py` / `config_manager.py` | `{config: {enabled, dmPolicy, ...}, credentials: {KEY: {has_value, preview}}}` — 讀取 Channel 既有設定（openclaw.json channels + .env 金鑰存在狀態），用於 Channel Init Wizard 回填 |
| `save_channel_config(channel_name, credentials, config)` | `bridge.py` / `config_manager.py` | `{success, message}` — 金鑰寫入 .env（chmod 600）+ config 以 deep merge 寫入 openclaw.json channels 區段。空值 credentials 跳過不覆寫（Re-entry 保留現有值） |
| `get_webhook_url(channel_name)` | `bridge.py` | `{local_url, template, path, note}` — 依 gateway config 計算 Channel Webhook URL |
| `get_openclaw_config()` | `config_manager.py` | `{meta, agents, channels, gateway, plugins, ...}` — 讀取 openclaw.json |
| `save_openclaw_config(section, data)` | `config_manager.py` | `{success}` — 寫入 openclaw.json 指定區段（deep merge） |
| `connect_remote(params)` | `ssh_connection.py` | `{success, server_info: {os, cpu_cores, memory_gb, disk_gb}}` — 建立 SSH 連線並初始化 RemoteExecutor |
| `disconnect_remote()` | `ssh_connection.py` | `{success}` — 中斷 SSH 連線並釋放資源 |
| `get_connection_status()` | `ssh_connection.py` | `{connected, status, host, uptime}` — 查詢當前 SSH 連線狀態 |
| `test_connection(params)` | `ssh_connection.py` | `{success, server_info: {os, cpu_cores, memory_gb, disk_gb}}` — 測試 SSH 連線（不持久化） |
| `get_gateway_info()` | `bridge.py` | `{url, bind, port, gateway_token, tls, has_credential, auth_label}` — 讀取 Gateway 連線資訊 (ADR-006) |
| `get_allowed_origins()` | `config_manager.py` | `{origins: string[], is_wildcard: bool}` — 讀取 gateway.controlUi.allowedOrigins (ADR-006) |
| `save_allowed_origins(params)` | `config_manager.py` | `{success}` — 寫入 allowedOrigins 至 openclaw.json，params: `{allow_all, origins}` (ADR-006) |
| `list_devices()` | `bridge.py` | `{pending: [...], paired: [...]}` — 列出所有裝置（`openclaw devices list --json`）(ADR-006) |
| `list_pending_devices()` | `bridge.py` | `{devices: [...]}` — 列出待核准裝置（Step 3 Device Pairing 用） |
| `approve_device(params)` | `bridge.py` | `{message, output}` — 核准裝置（`openclaw devices approve`）|
| `reject_device(params)` | `bridge.py` | `{message, output}` — 拒絕裝置（`openclaw devices reject`）(ADR-006) |
| `remove_device(params)` | `bridge.py` | `{message, output}` — 移除已配對裝置（`openclaw devices remove`）(ADR-006) |
| `save_device_note(params)` | `config_manager.py` | `{success}` — 儲存裝置備註至 gui-settings.json (ADR-006) |
| `get_device_notes()` | `config_manager.py` | `{device_id: note, ...}` — 讀取所有裝置備註 (ADR-006) |
