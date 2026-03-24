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

### 4.5 Dashboard（總覽頁）⬜ 待設計

**User Story (US-003)**:
> 身為使用者，我想要有清楚的啟動與停止按鈕，以便輕鬆管理 OpenClaw 服務狀態。

**預定 UI 區域**:

1. **Header**: 標題 "Dashboard" + 服務狀態 StatusBadge (Running/Stopped)
2. **StatCards Row**: 水平排列 StatCard 元件
   - Services Running (X/X)
   - Uptime
   - Skills Deployed (數量)
   - Plugins Installed (數量)
3. **Service Control**: 啟動/停止按鈕組
   - 服務未啟動: Button/Primary "Start Service" (play icon)
   - 服務運行中: Button/Danger "Stop Service" (square icon)
4. **Quick Actions**: 快速導航至其他功能的卡片或連結

**Bridge API 呼叫**:

```javascript
const status = await window.pywebview.api.get_service_status();
// 回傳: { running, services: [{name, status}], uptime }

await window.pywebview.api.start_service();
await window.pywebview.api.stop_service();
```

**驗收標準**:
- [ ] 進入頁面時自動查詢服務狀態
- [ ] 啟動/停止按鈕依服務狀態切換
- [ ] 操作結果即時更新 StatCards 與 StatusBadge
- [ ] 操作進行中按鈕 disabled 並顯示 loading

---

### 4.6 Deploy Skills（技能部署）⬜ 待設計

**User Story (US-005)**:
> 身為使用者，我想要透過介面一鍵部署技能模組，以便不需手動在命令列操作。

**預定 UI 區域**:

1. **Header**: 標題 "Deploy Skills" + 已部署數量 badge
2. **Skills Checklist**: 勾選清單
   - 每項: checkbox + emoji + 技能名稱 + 描述 + installed badge
   - 資料來源: `module_pack/` 目錄掃描 + SKILL.md frontmatter 解析
3. **Action Bar**: "Deploy Selected" Button/Primary + "Remove Selected" Button/Danger
4. **Progress Feedback**: 部署進度（逐項更新狀態）

**Bridge API 呼叫**:

```javascript
const skills = await window.pywebview.api.list_skills();
// 回傳: [{name, emoji, description, installed}]

const result = await window.pywebview.api.deploy_skills(["skill-a", "skill-b"]);
// 進度回呼: window.updateDeployProgress(skillName, status)
```

**驗收標準**:
- [ ] 列出所有可用技能，已安裝的預設勾選
- [ ] 勾選後點擊 "Deploy" 執行部署，進度即時更新
- [ ] 部署完成後刷新清單狀態

---

### 4.7 Install Plugins（外掛安裝）⬜ 待設計

**User Story (US-006)**:
> 身為使用者，我想要透過介面安裝外掛模組，以便不需手動在命令列操作。

**預定 UI 區域**:

1. **Header**: 標題 "Install Plugins" + 已安裝數量 badge
2. **Plugins Checklist**: 勾選清單（結構同 Deploy Skills）
   - 每項: checkbox + 外掛名稱 + 描述 + installed badge
3. **Action Bar**: "Install Selected" Button/Primary
4. **Progress Feedback**: 安裝進度

**Bridge API 呼叫**:

```javascript
const plugins = await window.pywebview.api.list_plugins();
// 回傳: [{name, description, installed}]

const result = await window.pywebview.api.install_plugins(["plugin-a"]);
```

**驗收標準**:
- [ ] 列出所有可用外掛，已安裝的預設勾選
- [ ] 安裝完成後刷新清單狀態

---

### 4.8 Fix Plugins（外掛修復）⬜ 待設計

**預定 UI 區域**:

1. **Header**: 標題 "Fix Plugins"
2. **Diagnostic Report**: 診斷結果卡片列表
   - 每項: 外掛名稱 + 狀態 (healthy/broken) + 問題描述
3. **Action**: "Run Diagnostics" Button/Secondary + "Fix All" Button/Primary
4. **Result Feedback**: 修復結果摘要

**Bridge API 呼叫**:

```javascript
const report = await window.pywebview.api.diagnose_plugins();
// 回傳: [{name, status, issues: [string]}]

const result = await window.pywebview.api.fix_plugins(["plugin-a"]);
```

**驗收標準**:
- [ ] 進入頁面時自動執行診斷
- [ ] 有問題的外掛顯示修復按鈕
- [ ] 修復完成後重新執行診斷確認結果

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
  // 更新對應 ProgressItem 的 UI 狀態
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
| `get_service_status()` | `service_controller.py` | `{running, services: [{name, status}], uptime}` |
| `start_service()` | `service_controller.py` | `{success, message}` |
| `stop_service()` | `service_controller.py` | `{success, message}` |
| `list_skills()` | `skill_manager.py` | `[{name, emoji, description, installed}]` |
| `deploy_skills(names)` | `skill_manager.py` | 透過回呼逐項回報，最終 `{success, deployed, failed}` |
| `list_plugins()` | `plugin_manager.py` | `[{name, description, installed}]` |
| `install_plugins(names)` | `plugin_manager.py` | `{success, installed, failed}` |
| `diagnose_plugins()` | `plugin_manager.py` | `[{name, status, issues}]` |
| `fix_plugins(names)` | `plugin_manager.py` | `{success, fixed, failed}` |
