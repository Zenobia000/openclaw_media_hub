# OpenClaw GUI

> PyWebView Bridge 桌面應用程式，圖形化介面取代命令列腳本。

## 環境需求

- **Python** >= 3.11
- **uv** (Python 套件管理工具)
- **Docker Desktop** (Windows) 或 **Docker Engine + Compose** (Linux)

## 快速開始

### 1. 安裝依賴

```bash
uv sync
```

### 2. 啟動應用程式

```bash
uv run python -m src.main
```

啟動後將開啟 1280x800 桌面視窗，前端透過 PyWebView Bridge 與 Python 後端通訊。

### 3. 執行測試

```bash
uv run pytest
```

### 4. 程式碼檢查

```bash
uv run python -m py_compile src/main.py
uv run python -m py_compile src/bridge.py
```

## 專案結構

```
src/
├── main.py                  # PyWebView 入口點
├── bridge.py                # Python Bridge API
├── executor.py              # Executor Protocol + CommandResult
├── local_executor.py        # 本機操作 (subprocess/pathlib/shutil)
├── remote_executor.py       # SSH 遠端操作 (paramiko)
├── ssh_connection.py        # SSH 連線管理
├── transfer_service.py      # 跨本機/遠端檔案傳輸
└── frontend/                # 前端靜態資源
    ├── index.html           # SPA 主頁面 (Sidebar + 6 Views)
    ├── css/styles.css       # 自訂樣式 (NavItem, Checkbox, Scrollbar)
    ├── js/app.js            # SPA 路由 + UI 元件 + Bridge 整合
    └── img/logo.png         # 品牌 Logo
```

### 前端架構

- **Framework**: Vanilla HTML/JS/CSS (無前端框架)
- **Styling**: Tailwind CSS (CDN) + 14 Design Tokens
- **Icons**: Lucide Icons (CDN)
- **Font**: Inter (Google Fonts)
- **State**: 前端完全無狀態，所有資料由 Python Bridge API 即時提供

### SPA 頁面

| View ID | 頁面 | 功能 |
| :--- | :--- | :--- |
| `dashboard` | Dashboard | 服務狀態總覽、啟停控制 |
| `configuration` | Configuration | 3 步驟初始化精靈 |
| `environment` | Environment | 系統依賴檢查 |
| `deploy-skills` | Deploy Skills | 技能模組部署 |
| `install-plugins` | Install Plugins | 外掛模組安裝 |
| `fix-plugins` | Fix Plugins | 外掛診斷修復 |

### 共用 UI 元件

| 函式 | 用途 |
| :--- | :--- |
| `renderButton()` | Primary / Secondary / Danger 按鈕 |
| `renderInput()` | 表單輸入框 (含 label, icon, password toggle) |
| `renderStatusBadge()` | 狀態徽章 (success/error/warning/info) |
| `renderStatCard()` | 統計數據卡片 |
| `renderCheckCard()` | 環境檢查卡片 |
| `renderSectionPanel()` | 區塊面板 (icon + 標題 + 描述 + 內容) |
| `renderStepIndicator()` | 步驟進度指示器 |
| `renderProgressItem()` | 進度項目 (done/running/pending/failed) |

## 技術棧

| 項目 | 選擇 | 用途 |
| :--- | :--- | :--- |
| 桌面框架 | PyWebView | Web 技術 + Python 結合 |
| 前端樣式 | Tailwind CSS | 自訂 Design Tokens |
| 套件管理 | uv | 版本管理 + 依賴鎖定 |
| 打包工具 | PyInstaller | 單一執行檔部署 |
| 金鑰儲存 | keyring | 跨平台安全儲存 |
| SSH 連線 | paramiko | 遠端操作 |

---

## 參考資訊

### 建議硬體規格需求表

| 規格項目         | **Windows (主流開發)**                     | **macOS (設計與前端)**                        | **Linux (伺服器/引擎)**                    |
| :--------------- | :----------------------------------------- | :-------------------------------------------- | :----------------------------------------- |
| **處理器 (CPU)** | **Intel i5 / Ryzen 5** <br>(等級以上)      | **Apple M1 / M2 / M3** <br>(或 Intel i5 等級) | **Intel i3 / 輕量級 ARM** <br>(等級以上)   |
| **記憶體 (RAM)** | **8GB** (最低限制) <br>**16GB** (建議配置) | **8GB** (最低限制) <br>**16GB** (建議配置)    | **1GB** (最低限制) <br>**4GB+** (建議配置) |
| **儲存空間**     | **30GB SSD** 可用空間                      | **30GB SSD** 可用空間                         | **10GB** (視容器數量而定)                  |
| **作業系統**     | Windows 10 / 11 <br>(需支援 WSL 2)         | macOS Ventura <br>(或更新版本)                | Ubuntu 22.04+ <br>(或各類 Server 版)       |
| **部署成本**     | **中 (授權與硬體)**                        | **高 (硬體成本)**                             | **低 (開源且資源省)**                      |

### 主流 AI 模型核心能力與費用對比表

| 模型名稱           | 核心定位 (Key Value) | 費用模式 (精確金額)                                                                  | 最佳應用場景                          |
| :----------------- | :------------------- | :----------------------------------------------------------------------------------- | :------------------------------------ |
| **Kimi K2.5**      | **Agent 專化推理**   | API：**$0.56 / $2.95** (每百萬 tokens 入/出) <br>訂閱：約 **$15 USD/月** (Code Plan) | 中文自動化工作流、長鏈條任務執行      |
| **Claude 4.5**     | **邏輯代碼頂峰**     | API：**$3 / $15** (每百萬 tokens 入/出) <br>訂閱：**$20 USD/月** (Pro 方案)          | 複雜軟體架構開發、高精度自動化專案    |
| **MiniMax m2.5**   | **極致性價比**       | API：**$0.3 / $1.2** (每百萬 tokens 入/出) <br>訂閱：約 **$10 USD/月** (Starter)     | 預算敏感型 Agent 專案、大規模文本生成 |
| **GPT-5.1**        | **通用型王者**       | API：**$1.25 / $10** (每百萬 tokens 入/出) <br>訂閱：**$20 USD/月** (Plus 方案)      | 企業級穩定助手、全能型 AI 應用        |
| **Gemini 2.5 Pro** | **超大上下文**       | API：**$1.25 / $10** (每百萬 tokens 入/出) <br>訂閱：**NT$650/月** (Advanced 方案)   | 萬卷文檔分析、Google 生態系深度整合   |

### 演示功能

- 分析確認郵件意圖，哪些是可以直接回、需要詢問
- 整理郵件，增加標籤
- CRM 完成
