# OpenClaw GUI

PyWebView Bridge 桌面應用程式，為 OpenClaw 提供圖形化操作介面。

## 環境需求

- [uv](https://docs.astral.sh/uv/) >= 0.8
- Python 3.12（由 uv 自動管理）
- Windows 10/11 或主流 Linux 發行版

## 快速開始

### 1. 安裝依賴

```bash
uv sync
```

此命令會：

- 依據 `.python-version` 自動下載 Python 3.12（若系統未安裝）
- 建立 `.venv/` 虛擬環境
- 安裝所有 production 與 dev 依賴
- 產生 `uv.lock` 鎖定檔

### 2. 啟動應用程式

```bash
uv run python -m src.main
```

啟動後會開啟 PyWebView 桌面視窗，載入 `src/frontend/index.html`。

### 3. 執行測試

```bash
uv run pytest
```

### 4. 程式碼檢查

```bash
uv run ruff check src/ tests/
```

自動修正：

```bash
uv run ruff check --fix src/ tests/
```

## 專案結構

```
openclaw_media_hub/
├── src/                        # GUI 應用程式原始碼
│   ├── main.py                 # PyWebView 入口點
│   ├── bridge.py               # Python Bridge API
│   ├── process_manager.py      # Subprocess 非同步管理
│   ├── config_manager.py       # 設定與金鑰管理 (keyring)
│   ├── platform_utils.py       # 跨平台偵測工具
│   └── frontend/               # 前端靜態資源
│       ├── index.html
│       ├── css/styles.css
│       └── js/app.js
├── tests/                      # 測試目錄
├── scripts/                    # OpenClaw 操作腳本（不修改）
├── docs/                       # 專案文件
├── pyproject.toml              # 專案設定與依賴宣告 (PEP 621)
├── uv.lock                    # 依賴鎖定檔（須提交至版控）
└── .python-version             # Python 版本固定為 3.12
```

## 技術棧

| 項目 | 選擇 | 用途 |
|---|---|---|
| 桌面框架 | PyWebView | 輕量級 GUI，Web 技術 + Python 結合 |
| 前端樣式 | Tailwind CSS | 現代化 UI 樣式 |
| 套件管理 | uv | Python 版本 + 虛擬環境 + 依賴鎖定 |
| 打包工具 | PyInstaller | 編譯為獨立執行檔 |
| 金鑰儲存 | keyring | 跨平台安全儲存 |
| Lint | Ruff | 程式碼風格與品質檢查 |

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
