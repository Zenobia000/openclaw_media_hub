# WBS 開發計劃 (WBS Plan) - OpenClaw GUI 應用程式

---

**版本:** `v3.0`
**更新:** `2026-03-24`
**作者:** `[專案經理 / 開發人員]`
**審核:** `[TL / 審核人員]`
**狀態:** `規劃中`

---

## 目錄

- [1. 專案總覽](#1-專案總覽)
- [2. WBS 結構總覽](#2-wbs-結構總覽)
- [3. 詳細任務分解](#3-詳細任務分解)
- [4. 進度摘要](#4-進度摘要)
- [5. 風險與議題](#5-風險與議題)
- [6. 品質與里程碑](#6-品質與里程碑)

---

## 1. 專案總覽

### 基本資訊

| 項目         | 內容                                |
| :----------- | :---------------------------------- |
| **專案名稱** | OpenClaw GUI 應用程式               |
| **專案經理** | 未定                                |
| **技術主導** | 未定                                |
| **專案狀態** | 設計中 (A2 階段)                    |
| **資源配置** | 預計配置 1 名前端/全端開發、1 名 QA |
| **總工期**   | 約 7 週 (2026-03-23 ～ 2026-05-08)，182h |
| **預計交付** | 2026-05-08 (Production Release)     |

### 角色與職責

| 角色    | 負責人 | 職責概述                                                               | 週工時 |
| :------ | :----- | :--------------------------------------------------------------------- | :----- |
| **PM**  | 待定   | 專案進度追蹤、需求確認與溝通、風險控管                                 | 10h    |
| **DEV** | 待定   | 架構設計、前後端實作 (PyWebView, PyInstaller, UI)、Python 原生操作邏輯 | 30h    |
| **QA**  | 待定   | 測試計劃與案例撰寫、功能驗證測試、發布前檢查                           | 5h     |

---

## 2. WBS 結構總覽

### 樹狀結構

```text
1.0 啟動與規劃 (Inception & Planning)
├── 1.1 撰寫 Project Brief & PRD
└── 1.2 撰寫 WBS 開發計劃

2.0 方案設計與架構 (Design & Architecture)
├── 2.1 建立架構設計與 ADR
├── 2.2 設計 UI Mockup (Wireframes)
├── 2.3 撰寫前端規格書
├── 2.4 設計 Bridge API Spec
└── 2.5 QA 測試計劃與案例撰寫

3.0 實作建置 (Construction)
├── 3.15 Transport Layer — ADR-004 ★ 基礎層，最先開發
│   ├── 3.15.1 executor.py Protocol + CommandResult
│   ├── 3.15.2 local_executor.py
│   ├── 3.15.3 remote_executor.py + paramiko
│   ├── 3.15.4 ssh_connection.py
│   └── 3.15.5 transfer_service.py
├── 3.1 專案環境初始化
├── 3.2 前端共用 UI 元件與佈局
│   ├── 3.2.1 Design Tokens
│   ├── 3.2.2 佈局框架 (Sidebar + Main Content)
│   ├── 3.2.3 Sidebar 元件 (含連線狀態指示燈，原 3.16.2 合併)
│   ├── 3.2.4 SPA 路由機制
│   ├── 3.2.5 基礎元件 (Button, Input, Badge, Card)
│   └── 3.2.6 複合元件 (SectionPanel, StepIndicator, ProgressItem, CheckCard)
├── 3.3 後端基礎模組
│   ├── 3.3.1 platform_utils.py
│   ├── 3.3.2 process_manager.py
│   ├── 3.3.3 bridge.py 骨架
│   └── 3.3.4 bridge.py SSH 連線管理 API (依賴 3.15.1~3.15.4)
├── 3.4 環境檢查 (US-001)
│   ├── 3.4.1~4 後端 env_checker.py + Bridge API + 測試
│   └── 3.4.5~8 前端 Environment 頁面
├── 3.5 設定管理模組
│   ├── 3.5.1 gui-settings.json
│   ├── 3.5.2 keyring 整合
│   ├── 3.5.3 openclaw.json 讀寫
│   ├── 3.5.4 .env 管理
│   ├── 3.5.5 Bridge API
│   ├── 3.5.6 單元測試
│   └── 3.5.7 SSH 連線設定管理
├── 3.6 Configuration Step 1 — 環境與目錄設定
│   ├── 3.6.1 detect_platform() API
│   ├── 3.6.2 StepIndicator 整合
│   ├── 3.6.3 Deployment Mode Radio Cards (含 SSH Radio Card，原 3.16.1 合併)
│   ├── 3.6.4 Gateway & Directory 表單
│   ├── 3.6.5 Action Bar + 驗證
│   ├── 3.6.6 SSH Connection 區塊（條件顯示）
│   ├── 3.6.7 SSH Connection 連線驗證
│   └── 3.16.3 Bridge API SSH 連線管理 (隨 Step 1 整合)
├── 3.7 Configuration Step 2 — API 金鑰與服務設定
│   ├── 3.7.1~2 Bridge API (providers/channels)
│   ├── 3.7.3 Model Providers 區塊
│   ├── 3.7.4 Channels 區塊
│   ├── 3.7.5 Tools 區塊
│   ├── 3.7.6 Security Note + Action Bar
│   └── 3.7.7 步驟間資料保留
├── 3.8 Configuration Step 3 — 初始化執行
│   ├── 3.8.1~11 後端 initializer.py (10 步 + Native 分支)
│   ├── 3.8.12 Bridge API + 進度回呼 + 測試
│   └── 3.8.13~15 前端 Step 3 頁面
├── 3.9 Dashboard 與服務控制 (US-003)
│   ├── 3.9.1~4 後端 service_controller.py + Bridge API + 測試
│   └── 3.9.5~9 前端 Dashboard 頁面
├── 3.10 技能部署 (US-005)
│   ├── 3.10.1~4 後端 skill_manager.py + Bridge API + 測試
│   └── 3.10.5~7 前端 Deploy Skills 頁面
├── 3.11 外掛安裝 (US-006)
│   ├── 3.11.1~3 後端 plugin_manager.py + Bridge API + 測試
│   └── 3.11.4~6 前端 Install Plugins 頁面
├── 3.12 外掛修復
│   ├── 3.12.1~2 後端診斷/修復邏輯 + Bridge API
│   └── 3.12.3~4 前端 Fix Plugins 頁面
├── 3.13 PyInstaller 打包 (US-004)
│   ├── 3.13.1 build.py 配置
│   ├── 3.13.2 CDN 資源離線化
│   ├── 3.13.3 Windows 打包測試
│   ├── 3.13.4 Linux 打包測試
│   └── 3.13.5 打包問題修復
├── 3.14 QA 功能驗證測試
│   ├── 3.14.1~5 各 User Story 端到端驗證
│   ├── 3.14.6 跨頁面整合測試
│   └── 3.14.7 US-007 SSH 遠端管理端到端驗證
├── [3.16 已拆散合併: 3.16.1→3.6.3, 3.16.2→3.2.3, 3.16.3→3.6]
└── 3.17 SSH 整合測試
    ├── 3.17.1 Mock Executor 單元測試
    ├── 3.17.2 SSH 連線整合測試
    └── 3.17.3 端到端遠端操作驗證

4.0 發佈上線 (Release)
├── 4.1 封閉測試與回饋收集
├── 4.2 Bug 修復與 Security Checklist
├── 4.3 撰寫使用者操作手冊
└── 4.4 正式發佈
```

### 週度排程總覽

| 週次 | 日期 | 主要工作 |
| :--- | :--- | :--- |
| Week 1 | 03/22 - 03/28 | Phase 1 ✅ + Phase 2 設計（架構✅、Mockup🔄、前端規格書✅、API Spec、QA 計劃） |
| Week 2 | 03/29 - 04/04 | **3.15.1 Executor Protocol + 3.15.2 LocalExecutor** + 3.2 前端 UI 元件(含 Sidebar 連線指示燈) + 3.3.1~3.3.3 後端基礎 + 3.4 環境檢查後端 |
| Week 3 | 04/05 - 04/11 | Track A: 3.5 Config Manager + 3.4 環境檢查前端 ‖ Track B: **3.15.3 RemoteExecutor + 3.15.4 ssh_connection** |
| Week 4 | 04/12 - 04/18 | 3.15.5 transfer_service + 3.3.4 bridge SSH APIs + 3.6 Config Step 1(含 SSH 表單) + 3.16.3 SSH Bridge 整合 + 3.7 Config Step 2 |
| Week 5 | 04/19 - 04/25 | 3.8 Initializer (後端+前端 Step 3) + 3.9 Dashboard 後端 + 3.10 技能部署後端 |
| Week 6 | 04/26 - 05/01 | 3.10 前端 + 3.9 Dashboard 前端 + 3.11 外掛安裝 + 3.12 外掛修復 + 3.13 PyInstaller (部分) |
| Week 7 | 05/02 - 05/08 | 3.13 打包測試 + 3.17 SSH 整合測試 + 3.14 QA 驗證 + Phase 4 發佈上線 |

### 工作包統計

| WBS 模組           | 預估工時 | 開始日期   | 結束日期   | 狀態      | 備註 |
| :----------------- | :------- | :--------- | :--------- | :-------- | :--- |
| 1.0 啟動與規劃     | 8h       | 2026-03-22 | 2026-03-23 | ✅ 完成   | |
| 2.0 方案設計與架構 | 24h      | 2026-03-22 | 2026-03-28 | 🔄 進行中 | |
| 3.15 Transport Layer | 17h    | 2026-03-29 | 2026-04-12 | ⬜ 未開始 | ★ 基礎層，最先開發 |
| 3.1 專案環境初始化 | 8h       | 2026-03-23 | 2026-03-23 | ✅ 完成   | |
| 3.2 前端 UI 元件   | 11h      | 2026-03-29 | 2026-04-01 | ⬜ 未開始 | +1h (合併 3.16.2) |
| 3.3 後端基礎模組   | 7h       | 2026-03-30 | 2026-04-12 | ⬜ 未開始 | 3.3.4 在 3.15.4 之後 |
| 3.4 環境檢查       | 8h       | 2026-04-02 | 2026-04-07 | ⬜ 未開始 | |
| 3.5 設定管理模組   | 9h       | 2026-04-05 | 2026-04-08 | ⬜ 未開始 | |
| 3.6 Config Step 1  | 9.5h     | 2026-04-12 | 2026-04-15 | ⬜ 未開始 | +1.5h (合併 3.16.1) |
| 3.16.3 SSH Bridge  | 1.5h     | 2026-04-15 | 2026-04-16 | ⬜ 未開始 | 隨 3.6 整合 |
| 3.7 Config Step 2  | 10h      | 2026-04-16 | 2026-04-18 | ⬜ 未開始 | |
| 3.8 Initializer    | 16h      | 2026-04-19 | 2026-04-24 | ⬜ 未開始 | 延後至 3.5 完成後 |
| 3.9 Dashboard      | 12h      | 2026-04-23 | 2026-04-28 | ⬜ 未開始 | |
| 3.10 技能部署      | 10h      | 2026-04-24 | 2026-04-27 | ⬜ 未開始 | |
| 3.11 外掛安裝      | 10h      | 2026-04-28 | 2026-04-30 | ⬜ 未開始 | |
| 3.12 外掛修復      | 6h       | 2026-04-30 | 2026-05-01 | ⬜ 未開始 | |
| 3.13 PyInstaller   | 8h       | 2026-04-30 | 2026-05-03 | ⬜ 未開始 | |
| 3.14 QA 驗證       | 10h      | 2026-05-03 | 2026-05-06 | ⬜ 未開始 | |
| 3.17 SSH 整合測試  | 6h       | 2026-05-02 | 2026-05-04 | ⬜ 未開始 | |
| 3.16 SSH 前端整合  | ~~4h~~   | —          | —          | 已合併    | 拆入 3.2.3, 3.6.3, 3.16.3 |
| 4.0 發佈上線       | 16h      | 2026-05-05 | 2026-05-08 | ⬜ 未開始 | |
| **總計**           | **182h** | **2026-03-22** | **2026-05-08** | **🔄 進行中** | |

**狀態:** ✅ 完成 | 🔄 進行中 | ⏳ 計劃中 | ⬜ 未開始

**狀態:** ✅ 完成 | 🔄 進行中 | ⏳ 計劃中 | ⬜ 未開始

---

## 3. 詳細任務分解

### 1.0 啟動與規劃

| ID  | 任務                     | 負責人 | 工時 | 狀態    | 開始日 | 完成日 | 備註                          |
| :-- | :----------------------- | :----- | :--- | :------ | :----- | :----- | :---------------------------- |
| 1.1 | 撰寫 Project Brief & PRD | PM     | 4h   | ✅ 完成 | 03/22  | 03/22  | 產出 200_project_brief_prd.md |
| 1.2 | 撰寫 WBS 開發計劃        | PM     | 4h   | ✅ 完成 | 03/22  | 03/23  | 產出 201_wbs_plan.md          |

### 2.0 方案設計與架構

| ID  | 任務                                                     | 負責人 | 工時 | 狀態      | 開始日 | 完成日 | 備註                                     |
| :-- | :------------------------------------------------------- | :----- | :--- | :-------- | :----- | :----- | :--------------------------------------- |
| 2.1 | 建立架構設計與 ADR (ADR-001/002/003)                     | DEV    | 6h   | ✅ 完成   | 03/22  | 03/23  | 產出 202_architecture_design.md          |
| 2.2 | 設計 UI Mockup (Wireframes)                              | DEV/PM | 6h   | 🔄 進行中 | 03/23  | 03/27  | pencil-new.pen 設計中                    |
| 2.3 | 撰寫前端規格書                                           | DEV    | 4h   | ✅ 完成   | 03/24  | 03/24  | 產出 208_frontend_specification.md       |
| 2.4 | Bridge API Spec（17+ API 方法、回傳格式、錯誤類型定義）  | DEV    | 4h   | ⬜ 未開始 | 03/27  | 03/28  | 基於 208 前端規格 §5.4 API 清單整理      |
| 2.5 | QA 測試計劃與案例撰寫                                    | QA     | 4h   | ⬜ 未開始 | 03/27  | 03/28  | 依 US-001~006 + Fix Plugins 撰寫測試案例 |

### 3.0 實作建置

#### 3.1 專案環境初始化 (8h) ✅

| ID    | 任務                                                   | 負責人 | 工時 | 狀態    | 開始日 | 完成日 | 備註                              |
| :---- | :----------------------------------------------------- | :----- | :--- | :------ | :----- | :----- | :-------------------------------- |
| 3.1.1 | uv init + pyproject.toml + Python 3.12 虛擬環境        | DEV    | 2h   | ✅ 完成 | 03/23  | 03/23  | ADR-002 uv 套件管理               |
| 3.1.2 | src/ 模組骨架（main.py, bridge.py, 各模組空檔）        | DEV    | 2h   | ✅ 完成 | 03/23  | 03/23  |                                   |
| 3.1.3 | PyWebView 最小可執行視窗 + Bridge 註冊機制             | DEV    | 2h   | ✅ 完成 | 03/23  | 03/23  |                                   |
| 3.1.4 | frontend/ 靜態資源結構（index.html, css/, js/）+ Tailwind CDN 引入 | DEV | 2h | ✅ 完成 | 03/23 | 03/23 | ADR-001 Tailwind CSS |

#### 3.2 前端共用 UI 元件與佈局 (11h, 含合併 3.16.2)

| ID    | 任務                                                                                          | 負責人 | 工時 | 狀態      | 開始日 | 完成日 | 備註                              |
| :---- | :-------------------------------------------------------------------------------------------- | :----- | :--- | :-------- | :----- | :----- | :-------------------------------- |
| 3.2.1 | Tailwind Design Tokens 設定（色彩 12 tokens、圓角 2 tokens、字型 10 種用途）                  | DEV    | 2h   | ⬜ 未開始 | 03/29  | 03/29  | 208 §3.2，tailwind.config 擴展   |
| 3.2.2 | 整體佈局框架：Sidebar (260px 固定) + Main Content (flex:1, padding 32px) + 捲動策略            | DEV    | 2h   | ⬜ 未開始 | 03/29  | 03/30  | 視窗 1280×800，不支援 RWD        |
| 3.2.3 | Sidebar 元件：Logo + NavItem/Active/Hover 狀態 + Section Labels (MAIN/OPERATIONS) + 版本資訊 + 環境模式動態文字 + **連線狀態指示燈**（綠點 Connected / 紅點 Disconnected / 橙點 Connecting，預設顯示本機模式）| DEV | 3h | ⬜ 未開始 | 03/30 | 03/31 | 208 §3.4 + **合併原 3.16.2** |
| 3.2.4 | SPA 路由機制：6 個 View ID 切換 (dashboard/configuration/environment/deploy-skills/install-plugins/fix-plugins) + NavItem 導航綁定 | DEV | 1h | ⬜ 未開始 | 03/31 | 03/31 | 無 URL hash，JS View 切換 |
| 3.2.5 | 共用元件：Button (Primary/Secondary/Danger + icon + disabled + loading)、Input (label + icon + placeholder + password toggle)、StatusBadge (4 狀態)、StatCard | DEV | 2h | ⬜ 未開始 | 03/31 | 04/01 | 208 §3.3 |
| 3.2.6 | 共用元件：SectionPanel (icon + 標題 + 描述 + children)、StepIndicator (3 步驟)、ProgressItem (done/running/pending/failed)、CheckCard | DEV | 1h | ⬜ 未開始 | 04/01 | 04/01 | 208 §3.3 |

#### 3.3 後端基礎模組 (7h)

| ID    | 任務                                                                                                            | 負責人 | 工時 | 狀態      | 開始日 | 完成日 | 備註                          |
| :---- | :-------------------------------------------------------------------------------------------------------------- | :----- | :--- | :-------- | :----- | :----- | :---------------------------- |
| 3.3.1 | platform_utils.py：OS 偵測 (win/linux) + Docker/Native 環境偵測 + deployment_mode 邏輯                          | DEV    | 2h   | ⬜ 未開始 | 03/30  | 03/31  | shutil.which + platform       |
| 3.3.2 | process_manager.py：非同步 subprocess 封裝（list 形式、可設定 timeout、graceful shutdown、stdout/stderr 捕獲）   | DEV    | 2h   | ⬜ 未開始 | 03/31  | 04/01  | 禁 shell=True (ADR-003)       |
| 3.3.3 | bridge.py 骨架：Bridge 類別 + 統一回傳格式 `{success, data/error}` + 錯誤類型映射 (TIMEOUT/PERMISSION/NOT_FOUND/INTERNAL) + 進度回呼機制 (evaluate_js) + Executor 注入點 | DEV | 2h | ⬜ 未開始 | 04/01 | 04/02 | 208 §5.1~5.3 |
| 3.3.4 | bridge.py SSH 連線管理 API：`connect_remote()`, `disconnect_remote()`, `get_connection_status()`, `test_connection()` + executor 選擇邏輯（依連線狀態自動切換 LocalExecutor / RemoteExecutor） | DEV | 1h | ⬜ 未開始 | 04/12 | 04/12 | ADR-004，**依賴 3.15.1~3.15.4 完成** |

#### 3.4 環境檢查 — US-001 (8h)

> **排程變更說明**：後端 (3.4.1~4) 在 Week 2 完成（3.15.2 LocalExecutor 之後），前端 (3.4.5~8) 在 Week 3 與 Config Manager 平行開發。所有檢查透過 `Executor.which()` / `Executor.run_command()` 執行。

| ID    | 任務                                                                                           | 負責人 | 工時  | 狀態      | 開始日 | 完成日 | 備註                                    |
| :---- | :--------------------------------------------------------------------------------------------- | :----- | :---- | :-------- | :----- | :----- | :-------------------------------------- |
| 3.4.1 | env_checker.py：Docker 模式 5 項檢查（Docker, Docker Compose, Docker Desktop/Running, VS Code, ngrok） | DEV | 2h | ⬜ 未開始 | 04/02 | 04/02 | 透過 Executor.which() + Executor.run_command() |
| 3.4.2 | env_checker.py：Native Linux 模式 6 項檢查（Node.js≥18, OpenClaw CLI, jq, VS Code, ngrok, systemd Service） | DEV | 1h | ⬜ 未開始 | 04/02 | 04/03 | |
| 3.4.3 | env_checker.py：.env 檔案存在性檢查 + Bridge API `check_env()` 整合                            | DEV    | 0.5h  | ⬜ 未開始 | 04/03  | 04/03  | 回傳 `{checks, env_file}`              |
| 3.4.4 | env_checker 單元測試                                                                           | DEV    | 0.5h  | ⬜ 未開始 | 04/03  | 04/03  | 透過 Mock Executor 測試                 |
| 3.4.5 | 前端 Environment：Header (標題+副標題) + 環境模式 StatusBadge + Summary Banner（全通過綠/有失敗紅 兩種狀態） | DEV | 1h | ⬜ 未開始 | 04/05 | 04/05 | 208 §4.1，Week 3 |
| 3.4.6 | 前端 Environment：CheckCards Grid（CHECK_ICONS mapping 10 種軟體 + 依部署模式動態渲染不同卡片數：Docker 5 張 / Native 6 張） | DEV | 1.5h | ⬜ 未開始 | 04/05 | 04/06 | Flexbox + flex-wrap |
| 3.4.7 | 前端 Environment：.env File Check 單行卡片 (Verified/Missing badge) + Error Guidance 條件顯示區塊 | DEV | 0.5h | ⬜ 未開始 | 04/06 | 04/06 | 有失敗項目時顯示安裝指引 |
| 3.4.8 | 前端 Environment：進入頁面自動觸發 `check_env()` + "Last checked" 時間戳                        | DEV    | 1h    | ⬜ 未開始 | 04/06  | 04/07  |                                         |

#### 3.5 設定管理模組 (9h)

> **排程變更說明**：移至 Week 3 Track A，與 RemoteExecutor 平行開發。檔案 I/O 操作透過 Executor 介面。

| ID    | 任務                                                                                                        | 負責人 | 工時 | 狀態      | 開始日 | 完成日 | 備註                                       |
| :---- | :---------------------------------------------------------------------------------------------------------- | :----- | :--- | :-------- | :----- | :----- | :----------------------------------------- |
| 3.5.1 | config_manager.py：gui-settings.json 讀寫（deployment_mode 持久化，路徑 `{project_root}/.openclaw/`）       | DEV    | 1h   | ⬜ 未開始 | 04/05  | 04/05  | 與 openclaw.json 分開                      |
| 3.5.2 | config_manager.py：keyring 整合 — 金鑰安全儲存/讀取/刪除（Windows DPAPI + Linux libsecret）                  | DEV    | 2h   | ⬜ 未開始 | 04/05  | 04/06  | 禁止明文儲存                               |
| 3.5.3 | config_manager.py：openclaw.json 讀寫 — deep merge 策略、寫入前備份 (.bak)、sections 操作 (meta/agents/channels/gateway/plugins/tools/commands) | DEV | 2h | ⬜ 未開始 | 04/06 | 04/07 | 多層巢狀 JSON，需確保不破壞既有設定 |
| 3.5.4 | config_manager.py：.env 檔案管理 — 16+ 環境變數 upsert 邏輯（讀取、新增、更新、保留未列變數）               | DEV    | 1h   | ⬜ 未開始 | 04/07  | 04/07  | 202 §8 環境變數清單                        |
| 3.5.5 | Bridge API：`save_config()`, `save_keys()`, `get_openclaw_config()`, `save_openclaw_config(section, data)`  | DEV    | 1h   | ⬜ 未開始 | 04/07  | 04/08  |                                            |
| 3.5.6 | config_manager 單元測試（keyring mock、JSON deep merge、.env upsert 邊界情況）                              | DEV    | 1h   | ⬜ 未開始 | 04/08  | 04/08  |                                            |
| 3.5.7 | config_manager.py：SSH 連線設定管理 — `gui-settings.json` 新增 `ssh_host`, `ssh_port`, `ssh_username`, `ssh_key_path` 欄位讀寫 + SSH 私鑰路徑驗證 | DEV | 1h | ⬜ 未開始 | 04/08 | 04/08 | ADR-004 |

#### 3.6 Configuration Step 1 — 環境與目錄設定 (9.5h, 含合併 3.16.1)

> **排程變更說明**：移至 Week 4，在 3.15.1~3.15.4 + 3.5 Config Manager 完成後開發。SSH Radio Card (原 3.16.1) 合併入 3.6.3，4 張 Radio Card 一起做。

| ID    | 任務                                                                                                         | 負責人 | 工時  | 狀態      | 開始日 | 完成日 | 備註                            |
| :---- | :----------------------------------------------------------------------------------------------------------- | :----- | :---- | :-------- | :----- | :----- | :------------------------------ |
| 3.6.1 | Bridge API `detect_platform()`：回傳 `{os, env_type, suggested_mode, current_mode}`                          | DEV    | 1h    | ⬜ 未開始 | 04/12  | 04/12  | 依賴 3.3.1 + 3.5.1             |
| 3.6.2 | 前端 StepIndicator 整合（3 步驟：Active 紅底/Completed 綠底勾/Pending 灰色邊框，2px 橫線連接）               | DEV    | 1h    | ⬜ 未開始 | 04/12  | 04/13  | 208 §4.2                       |
| 3.6.3 | 前端 Deployment Mode 區塊：4 張 Radio Card (Docker Windows/Docker Linux/Native Linux/**Remote Server SSH**) + 點擊即時 `save_config()` 持久化 + Sidebar footer 環境文字更新 | DEV | 3.5h | ⬜ 未開始 | 04/13 | 04/14 | **合併原 3.16.1** SSH Radio Card + 連線表單，4 張卡一起做 |
| 3.6.4 | 前端 Gateway & Directory 區塊：3×2 表單 Grid (config_dir/workspace_dir/bind/mode/port/bridge_port) + 進階設定收合區 (timezone/docker_image/sandbox toggle) | DEV | 1.5h | ⬜ 未開始 | 04/14 | 04/14 | 預設值從 Bridge 或硬編碼 |
| 3.6.5 | 前端 Action Bar："Step 1 of 3" 文字 + "Next" Button/Primary (arrow-right icon) + 必填欄位驗證               | DEV    | 0.5h  | ⬜ 未開始 | 04/14  | 04/15  |                                 |
| 3.6.6 | 前端 SSH Connection 區塊（條件顯示）：選擇「Remote Server (SSH)」後展開 SSH 連線表單（SectionPanel: host/port/username/key file path 4 欄位 + Test Connection 按鈕 + 連線狀態回饋） | DEV | 1.5h | ⬜ 未開始 | 04/15 | 04/15 | ADR-004，僅 remote-ssh 模式顯示 |
| 3.6.7 | 前端 SSH Connection 連線驗證：點擊 Test Connection 呼叫 `test_connection()` API + 成功/失敗狀態顯示 + Next 按鈕需連線成功才啟用 | DEV | 0.5h | ⬜ 未開始 | 04/15 | 04/15 | |

#### 3.7 Configuration Step 2 — API 金鑰與服務設定 (10h)

| ID    | 任務                                                                                                          | 負責人 | 工時  | 狀態      | 開始日 | 完成日 | 備註                                          |
| :---- | :------------------------------------------------------------------------------------------------------------ | :----- | :---- | :-------- | :----- | :----- | :-------------------------------------------- |
| 3.7.1 | Bridge API `get_available_providers()`：掃描 openclaw/extensions/ 取得供應商列表 `[{name, env_var, placeholder}]` | DEV | 1.5h | ⬜ 未開始 | 04/16 | 04/16 | 讀取 openclaw.plugin.json |
| 3.7.2 | Bridge API `get_available_channels()`：掃描 openclaw/extensions/ 取得管道列表 `[{name, fields, icon, icon_color}]` | DEV | 1.5h | ⬜ 未開始 | 04/16 | 04/17 | 欄位定義含 key + label |
| 3.7.3 | 前端 Model Providers 區塊：供應商勾選清單 (OpenAI/Anthropic/Gemini/OpenRouter/Ollama + 更多收合區) + 勾選後動態展開金鑰輸入框 (password mode + 顯示/隱藏切換) | DEV | 2h | ⬜ 未開始 | 04/17 | 04/17 | 208 §4.3 |
| 3.7.4 | 前端 Channels 區塊：管道勾選清單 (LINE/Discord/Telegram/Slack/WhatsApp + 更多收合區) + 品牌色 icon + 動態展開多欄位 + Configured/Not Configured badge | DEV | 2h | ⬜ 未開始 | 04/17 | 04/18 | 208 §4.3 |
| 3.7.5 | 前端 Tools 區塊（預設收合）：Brave/Perplexity/Firecrawl/ElevenLabs/Deepgram 金鑰輸入                         | DEV    | 1h    | ⬜ 未開始 | 04/18  | 04/18  |                                               |
| 3.7.6 | 前端 Security Note (shield-check icon + 加密說明) + Action Bar (Back/Next) + `save_keys()` 至 keyring 流程   | DEV    | 1h    | ⬜ 未開始 | 04/18  | 04/18  |                                               |
| 3.7.7 | 步驟間資料保留：Step 1↔2↔3 切換時保留已填資料（前端記憶體快取機制）                                           | DEV    | 1h    | ⬜ 未開始 | 04/18  | 04/18  |                                               |

#### 3.8 Configuration Step 3 — 初始化執行與結果 (16h)

> **排程變更說明**：延至 Week 5，在 Config Manager (3.5) 與 Config Step 1+2 (3.6, 3.7) 穩定後開發。所有操作透過 Executor 介面，天然支援 SSH 遠端模式。

| ID     | 任務                                                                                                       | 負責人 | 工時  | 狀態      | 開始日 | 完成日 | 備註                              |
| :----- | :--------------------------------------------------------------------------------------------------------- | :----- | :---- | :-------- | :----- | :----- | :-------------------------------- |
| 3.8.1  | initializer.py Step 1：驗證 Docker + Docker Compose 可用性                                                 | DEV    | 1h    | ⬜ 未開始 | 04/19  | 04/19  | 透過 Executor.run_command()       |
| 3.8.2  | initializer.py Step 2：驗證/設定環境變數（OPENCLAW_CONFIG_DIR 等）                                          | DEV    | 1h    | ⬜ 未開始 | 04/19  | 04/19  |                                   |
| 3.8.3  | initializer.py Step 3：建立目錄結構（identity/, agents/main/agent/, agents/main/sessions/, workspace/）     | DEV    | 1h    | ⬜ 未開始 | 04/19  | 04/20  | 透過 Executor.mkdir()             |
| 3.8.4  | initializer.py Step 4：Gateway Token 解析/產生（讀 openclaw.json → 讀 .env → `secrets.token_hex(32)` 產生） | DEV | 1h | ⬜ 未開始 | 04/20 | 04/20 | 依賴 3.5.3 |
| 3.8.5  | initializer.py Step 5：寫入 .env（16+ 環境變數 upsert，含 ports, paths, token, timezone）                   | DEV    | 1h    | ⬜ 未開始 | 04/20  | 04/20  | 依賴 3.5.4                        |
| 3.8.6  | initializer.py Step 6：Build/Pull Docker Image（最耗時步驟，需進度提示）                                    | DEV    | 1.5h  | ⬜ 未開始 | 04/20  | 04/21  | ⚠️ 效能關注點                      |
| 3.8.7  | initializer.py Step 7：修正資料目錄權限（chown container user）                                             | DEV    | 0.5h  | ⬜ 未開始 | 04/21  | 04/21  |                                   |
| 3.8.8  | initializer.py Step 8：Onboarding（`docker compose run --rm openclaw-cli onboard --mode local --no-install-daemon`） | DEV | 1h | ⬜ 未開始 | 04/21 | 04/21 | |
| 3.8.9  | initializer.py Step 9：同步 Gateway 設定（gateway.mode=local, bind, controlUi.allowedOrigins）              | DEV    | 1h    | ⬜ 未開始 | 04/21  | 04/22  | 寫入 openclaw.json                |
| 3.8.10 | initializer.py Step 10+11：啟動 Gateway（`docker compose up -d openclaw-gateway`）+ Health Check（`/healthz`） | DEV | 1h | ⬜ 未開始 | 04/22 | 04/22 | |
| 3.8.11 | initializer.py：Native Linux 模式分支（Step 1 驗證 Node.js/CLI/systemd、略過 Step 5/6/7、Step 9 用 systemctl） | DEV | 1h | ⬜ 未開始 | 04/22 | 04/22 | |
| 3.8.12 | Bridge API `initialize()` + 非同步進度回呼 (`window.updateInitProgress(step, status, message)`) + 單元測試  | DEV    | 2h    | ⬜ 未開始 | 04/22  | 04/23  | 208 §5.2                          |
| 3.8.13 | 前端 Step 3：Initialization Progress 面板（Docker 10 個 / Native 8 個 ProgressItem + Done/Running/Pending 狀態切換） | DEV | 1.5h | ⬜ 未開始 | 04/23 | 04/23 | 208 §4.4 |
| 3.8.14 | 前端 Step 3：Dashboard Info 面板（Dashboard URL 唯讀 + Access Token 遮罩/複製 + Device Pairing 區塊）— Gateway ready 前 disabled | DEV | 1h | ⬜ 未開始 | 04/23 | 04/24 | 固定寬度 340px |
| 3.8.15 | 前端 Step 3：Action Bar (Back + Initialize) + Initialize 按鈕 loading 狀態 + 失敗 Retry                     | DEV    | 0.5h  | ⬜ 未開始 | 04/24  | 04/24  |                                   |

#### 3.9 Dashboard 與服務控制 — US-003 (12h)

> **排程變更說明**：後端 (3.9.1~4) Week 5 與 Initializer 平行，前端 (3.9.5~9) Week 6。透過 Executor 介面操作服務控制。

| ID    | 任務                                                                                                          | 負責人 | 工時  | 狀態      | 開始日 | 完成日 | 備註                                   |
| :---- | :------------------------------------------------------------------------------------------------------------ | :----- | :---- | :-------- | :----- | :----- | :------------------------------------- |
| 3.9.1 | service_controller.py：Docker 模式 — `docker compose up -d` / `down` / `restart` + `docker compose ps` 狀態查詢 | DEV | 2h | ⬜ 未開始 | 04/23 | 04/23 | 透過 Executor.run_command() |
| 3.9.2 | service_controller.py：Native Linux 模式 — `systemctl start/stop/restart/is-active openclaw-gateway`          | DEV    | 1h    | ⬜ 未開始 | 04/23  | 04/24  |                                        |
| 3.9.3 | Bridge API：`get_service_status()`, `start_service()`, `stop_service()`, `restart_service()`                  | DEV    | 1h    | ⬜ 未開始 | 04/24  | 04/24  | 回傳 `{running, services, uptime, skills_count, plugins_count}` |
| 3.9.4 | service_controller 單元測試                                                                                   | DEV    | 1h    | ⬜ 未開始 | 04/24  | 04/24  |                                        |
| 3.9.5 | 前端 Dashboard：Header (標題+副標題) + 服務狀態 StatusBadge（Running 綠 / Stopped 紅 動態切換）               | DEV    | 1h    | ⬜ 未開始 | 04/26  | 04/26  | 208 §4.5，Week 6                       |
| 3.9.6 | 前端 Dashboard：4 張 StatCards（Services X/1 + Uptime Xh Xm + Skills 數量 + Plugins 數量）水平等寬排列       | DEV    | 1.5h  | ⬜ 未開始 | 04/26  | 04/27  | bg-card + radius-md + 邊框             |
| 3.9.7 | 前端 Dashboard：Service Control 區塊（服務列表 + StatusBadge + Start/Restart/Stop 按鈕組 + 操作中 disabled + loading 動畫） | DEV | 2h | ⬜ 未開始 | 04/27 | 04/27 | 按鈕依服務狀態動態切換 |
| 3.9.8 | 前端 Dashboard：Quick Actions 區塊（3 張 Action Card: Environment Check / Deploy Skills / Install Plugins + 點擊導航） | DEV | 1h | ⬜ 未開始 | 04/27 | 04/28 | hover 邊框變 accent-primary |
| 3.9.9 | 前端 Dashboard：狀態輪詢機制（每 10 秒 `get_service_status()` + 離開頁面停止輪詢）                            | DEV    | 0.5h  | ⬜ 未開始 | 04/28  | 04/28  | setInterval / clearInterval            |

#### 3.10 技能部署 — US-005 (10h)

> **排程變更說明**：後端 (3.10.1~4) Week 5 與 Dashboard 後端平行，前端 (3.10.5~7) Week 6。透過 Executor.copy_tree()/remove_tree() 操作，遠端模式使用 transfer_service (3.15.5，已在 Week 4 完成)。

| ID     | 任務                                                                                                         | 負責人 | 工時  | 狀態      | 開始日 | 完成日 | 備註                                   |
| :----- | :----------------------------------------------------------------------------------------------------------- | :----- | :---- | :-------- | :----- | :----- | :------------------------------------- |
| 3.10.1 | skill_manager.py：掃描 `module_pack/`（自訂業務模組）+ `openclaw/skills/`（55+ 社群技能）目錄                 | DEV    | 1.5h  | ⬜ 未開始 | 04/24  | 04/25  | 透過 Executor.list_dir() 遞迴掃描      |
| 3.10.2 | skill_manager.py：SKILL.md YAML frontmatter 解析（name, description, homepage, metadata.openclaw.emoji/requires） | DEV | 1.5h | ⬜ 未開始 | 04/25 | 04/25 | PyYAML 解析 |
| 3.10.3 | skill_manager.py：部署邏輯 (Executor.copy_tree → `~/.openclaw/workspace/skills/`) + 移除邏輯 (Executor.remove_tree) + 已部署偵測 | DEV | 1h | ⬜ 未開始 | 04/25 | 04/25 | 遠端模式用 transfer_service |
| 3.10.4 | Bridge API：`list_skills()`, `deploy_skills(names)`, `remove_skills(names)` + 進度回呼 (`window.updateDeployProgress`) + 單元測試 | DEV | 1.5h | ⬜ 未開始 | 04/25 | 04/26 | |
| 3.10.5 | 前端 Deploy Skills：Header + Summary Banner (X of Y deployed / No skills yet) + deployed badge               | DEV    | 1h    | ⬜ 未開始 | 04/26  | 04/26  | 208 §4.6，Week 6                       |
| 3.10.6 | 前端 Deploy Skills：Tab 切換 (Custom Modules / Community Skills) + Select All checkbox + 技能勾選清單（checkbox + emoji + name + description + Deployed/Available badge + hover） | DEV | 1.5h | ⬜ 未開始 | 04/26 | 04/27 | 已部署預設勾選 |
| 3.10.7 | 前端 Deploy Skills：Progress Overlay（逐項 ProgressItem 狀態更新）+ Action Bar (已選數量 + Deploy/Remove 按鈕 + disabled 邏輯) | DEV | 1.5h | ⬜ 未開始 | 04/27 | 04/27 | Remove 需確認提示 |

#### 3.11 外掛安裝 — US-006 (10h)

| ID     | 任務                                                                                                          | 負責人 | 工時  | 狀態      | 開始日 | 完成日 | 備註                                   |
| :----- | :------------------------------------------------------------------------------------------------------------ | :----- | :---- | :-------- | :----- | :----- | :------------------------------------- |
| 3.11.1 | plugin_manager.py：掃描 `openclaw/extensions/` + 讀取 `openclaw.plugin.json`（id, channels[], providers[], providerAuthEnvVars, configSchema） | DEV | 2h | ⬜ 未開始 | 04/28 | 04/28 | 透過 Executor.read_file() |
| 3.11.2 | plugin_manager.py：外掛分類邏輯（Providers / Channels / Tools / Infrastructure）+ 安裝邏輯（修改 `openclaw.json` 的 `plugins.load.paths[]` + `plugins.installs`） | DEV | 2h | ⬜ 未開始 | 04/28 | 04/29 | config-driven，非檔案複製 |
| 3.11.3 | plugin_manager.py：解除安裝邏輯（反向修改 openclaw.json）+ Bridge API (`list_plugins()`, `install_plugins()`, `uninstall_plugins()`) + 進度回呼 + 單元測試 | DEV | 1.5h | ⬜ 未開始 | 04/29 | 04/29 | |
| 3.11.4 | 前端 Install Plugins：Header + Summary Banner (X of Y installed / No plugins yet) + installed badge           | DEV    | 1h    | ⬜ 未開始 | 04/29  | 04/30  | 208 §4.7                               |
| 3.11.5 | 前端 Install Plugins：4 分類 Tab (Providers/Channels/Tools/Infrastructure) + Select All + 外掛勾選清單（品牌色圓形 icon + name + description + Installed/Available badge + hover） | DEV | 2h | ⬜ 未開始 | 04/30 | 04/30 | 已安裝預設勾選 |
| 3.11.6 | 前端 Install Plugins：Progress Overlay + Action Bar (已選數量 + Install/Uninstall 按鈕 + disabled 邏輯)       | DEV    | 1.5h  | ⬜ 未開始 | 04/30  | 04/30  | Uninstall 需確認提示                    |

#### 3.12 外掛修復 (6h)

| ID     | 任務                                                                                                           | 負責人 | 工時  | 狀態      | 開始日 | 完成日 | 備註                           |
| :----- | :------------------------------------------------------------------------------------------------------------- | :----- | :---- | :-------- | :----- | :----- | :----------------------------- |
| 3.12.1 | plugin_manager.py：診斷邏輯（設定檔存在性、目錄完整性、Docker container 健康度檢查）                            | DEV    | 2h    | ⬜ 未開始 | 04/30  | 04/30  |                                |
| 3.12.2 | plugin_manager.py：修復邏輯（重建設定檔、修正目錄、重啟容器）+ Bridge API (`diagnose_plugins()`, `fix_plugins()`, `fix_all_plugins()`) + 進度回呼 | DEV | 1.5h | ⬜ 未開始 | 04/30 | 05/01 | |
| 3.12.3 | 前端 Fix Plugins：Header (Run Diagnostics 按鈕) + Summary Banner (健康綠/有問題紅/診斷中藍 三種狀態 + Last checked) + Diagnostic Report 區塊（外掛列表 + Issues 清單 + Healthy/Broken/Warning badge + 個別 Fix 按鈕） | DEV | 2h | ⬜ 未開始 | 05/01 | 05/01 | 208 §4.8 |
| 3.12.4 | 前端 Fix Plugins：Fix Progress Overlay + Action Bar (Fix All 按鈕) + 修復完成後自動重新診斷                     | DEV    | 0.5h  | ⬜ 未開始 | 05/01  | 05/01  |                                |

#### 3.13 PyInstaller 打包 — US-004 (8h)

| ID     | 任務                                                                                                          | 負責人 | 工時 | 狀態      | 開始日 | 完成日 | 備註                       |
| :----- | :------------------------------------------------------------------------------------------------------------ | :----- | :--- | :-------- | :----- | :----- | :------------------------- |
| 3.13.1 | build.py：PyInstaller spec 配置（frontend/ 靜態資源嵌入、data files 設定、icon 設定）                          | DEV    | 2h   | ⬜ 未開始 | 04/30  | 04/30  | Week 6，與 3.12 並行       |
| 3.13.2 | CDN 資源離線化：下載 Tailwind CSS + Lucide Icons + Inter Font 至 frontend/（確保無網路環境可用）               | DEV    | 1h   | ⬜ 未開始 | 04/30  | 05/01  | 208 §1.2 注意事項           |
| 3.13.3 | Windows 打包測試：單一 .exe 產出 + 啟動驗證 + 功能冒煙測試                                                     | DEV    | 2h   | ⬜ 未開始 | 05/02  | 05/02  | Week 7                     |
| 3.13.4 | Linux 打包測試：單一可執行檔產出 + 啟動驗證                                                                     | DEV    | 2h   | ⬜ 未開始 | 05/02  | 05/03  |                            |
| 3.13.5 | 打包問題修復（hidden imports、路徑修正、資源定位、keyring backend 打包）                                        | DEV    | 1h   | ⬜ 未開始 | 05/03  | 05/03  |                            |

#### 3.14 QA 功能驗證測試 (10h)

| ID     | 任務                                                                                          | 負責人 | 工時  | 狀態      | 開始日 | 完成日 | 備註                  |
| :----- | :-------------------------------------------------------------------------------------------- | :----- | :---- | :-------- | :----- | :----- | :-------------------- |
| 3.14.1 | US-001 驗證：環境檢查端到端測試（Docker + Native 兩種模式，各軟體偵測+版本+狀態卡片渲染）      | QA     | 1.5h  | ⬜ 未開始 | 05/03  | 05/03  | Week 7                |
| 3.14.2 | US-002 驗證：Configuration 3 步驟端到端測試（模式選擇 → 表單填寫 → keyring 儲存 → 初始化 10 步 → Health Check 通過） | QA | 2h | ⬜ 未開始 | 05/03 | 05/04 | 最複雜的使用者流程 |
| 3.14.3 | US-003 驗證：Dashboard 服務啟停端到端測試（StatCards 更新 + Start/Stop/Restart + 狀態輪詢）     | QA     | 1h    | ⬜ 未開始 | 05/04  | 05/04  |                       |
| 3.14.4 | US-005 驗證：技能部署/移除端到端測試（兩個來源 Tab 切換 + Select All + 部署/移除 + Progress）   | QA     | 1h    | ⬜ 未開始 | 05/04  | 05/05  |                       |
| 3.14.5 | US-006 驗證：外掛安裝/解除安裝端到端測試（4 分類 Tab + 安裝/解除 + Progress + openclaw.json 驗證） | QA  | 1h    | ⬜ 未開始 | 05/05  | 05/05  |                       |
| 3.14.6 | Fix Plugins 驗證 + 跨頁面整合測試（Sidebar 導航正確、模式切換影響各頁面行為、步驟間資料保留）   | QA     | 1.5h  | ⬜ 未開始 | 05/05  | 05/05  |                       |
| 3.14.7 | US-007 驗證：SSH 遠端管理端到端測試（Remote Server 模式選擇 → SSH 連線 → 遠端環境檢查 → 遠端初始化 → 技能跨機器部署） | QA | 2h | ⬜ 未開始 | 05/05 | 05/06 | ADR-004 |

#### 3.15 Transport Layer — ADR-004 (17h) ★ 基礎層，最先開發

> **排程變更說明**：Executor Protocol + LocalExecutor 提前至 Week 2 第一天，作為所有後端模組的基礎介面。RemoteExecutor + ssh_connection 在 Week 3 與 Config Manager 平行開發。transfer_service 在 Week 4 技能部署之前完成。

| ID     | 任務                                                                                                          | 負責人 | 工時  | 狀態      | 開始日 | 完成日 | 備註                                   |
| :----- | :------------------------------------------------------------------------------------------------------------ | :----- | :---- | :-------- | :----- | :----- | :------------------------------------- |
| 3.15.1 | executor.py：`Executor` Protocol 定義（9 個抽象方法：run_command, read_file, write_file, mkdir, copy_tree, remove_tree, file_exists, list_dir, which）+ `CommandResult` dataclass (exit_code, stdout, stderr) | DEV | 2h | ⬜ 未開始 | 03/29 | 03/29 | ★ Week 2 第一天，ADR-004 核心介面 |
| 3.15.2 | local_executor.py：`LocalExecutor` 實作 — 封裝 `subprocess.run()` (list 形式), `pathlib`, `shutil.which()`, `shutil.copytree/rmtree` | DEV | 3h | ⬜ 未開始 | 03/29 | 03/30 | ★ Week 2，所有後端模組透過此操作 |
| 3.15.3 | remote_executor.py：`RemoteExecutor` 實作 — 封裝 `paramiko.SSHClient.exec_command()` + `SFTPClient` (read/write/mkdir/remove) + SFTP 遞迴 copy_tree/remove_tree 手動實作 + `which` 透過 `command -v` | DEV | 6h | ⬜ 未開始 | 04/05 | 04/09 | Week 3 Track B，與 3.5 平行 |
| 3.15.4 | ssh_connection.py：SSH 連線管理 — 連線建立（key/password auth）、斷線、自動重連（失敗重試 3 次）、心跳（30 秒 keepalive）、連線狀態列舉 (connected/disconnected/connecting/error) | DEV | 4h | ⬜ 未開始 | 04/09 | 04/11 | Week 3 Track B，連線狀態推播至前端 |
| 3.15.5 | transfer_service.py：跨本機/遠端檔案傳輸服務 — `upload_tree(local_src, remote_dst)` 用於技能部署（本機 module_pack/ → 遠端 skills/）、進度回呼支援 | DEV | 2h | ⬜ 未開始 | 04/12 | 04/12 | Week 4，在 3.10 技能部署之前 |

#### 3.16 SSH 前端整合 — 已拆散合併

> **排程變更說明**：3.16 作為獨立工作包取消，其子任務合併至對應的功能模組：
> - **3.16.1** (SSH Radio Card + 連線表單, 1.5h) → **合併入 3.6.3** Deployment Mode Radio Cards
> - **3.16.2** (Sidebar 連線狀態指示燈, 1h) → **合併入 3.2.3** Sidebar 元件
> - **3.16.3** (Bridge API SSH 連線管理, 1.5h) → 保留獨立，排在 3.6 之後 (Week 4)

| ID     | 任務                                                                                                          | 負責人 | 工時  | 狀態      | 開始日 | 完成日 | 備註                                   |
| :----- | :------------------------------------------------------------------------------------------------------------ | :----- | :---- | :-------- | :----- | :----- | :------------------------------------- |
| 3.16.1 | ~~前端：Configuration Step 1 第 4 張 Radio Card~~ | — | 1.5h | 已合併 | — | — | → 合併入 3.6.3 |
| 3.16.2 | ~~前端：Sidebar footer 連線狀態指示燈~~ | — | 1h | 已合併 | — | — | → 合併入 3.2.3 |
| 3.16.3 | Bridge API 整合：前端呼叫 `connect_remote()` / `disconnect_remote()` / `get_connection_status()` / `test_connection()` + 連線狀態變更回呼 `window.updateConnectionStatus(status)` | DEV | 1.5h | ⬜ 未開始 | 04/15 | 04/16 | 隨 3.6 Config Step 1 整合 |

#### 3.17 SSH 整合測試 (6h)

| ID     | 任務                                                                                                          | 負責人 | 工時  | 狀態      | 開始日 | 完成日 | 備註                                   |
| :----- | :------------------------------------------------------------------------------------------------------------ | :----- | :---- | :-------- | :----- | :----- | :------------------------------------- |
| 3.17.1 | Mock Executor 單元測試：LocalExecutor 與 RemoteExecutor 的 9 個方法各自驗證 + CommandResult 邊界情況 | QA/DEV | 2h | ⬜ 未開始 | 05/02 | 05/03 | Week 7，與打包測試並行 |
| 3.17.2 | SSH 連線整合測試：連線建立/斷線/重連/心跳/逾時/認證失敗等場景 + ssh_connection.py 狀態機驗證 | QA/DEV | 2h | ⬜ 未開始 | 05/03 | 05/04 | 需測試用 SSH 伺服器 |
| 3.17.3 | 端到端遠端操作驗證：US-007 驗收 — 遠端環境檢查 + 遠端初始化 + 遠端技能部署（含 upload_tree）+ 遠端服務控制 | QA | 2h | ⬜ 未開始 | 05/04 | 05/04 | 最複雜的整合場景 |

### 4.0 發佈上線

| ID  | 任務                                                                                             | 負責人 | 工時 | 狀態      | 開始日 | 完成日 | 備註                             |
| :-- | :----------------------------------------------------------------------------------------------- | :----- | :--- | :-------- | :----- | :----- | :------------------------------- |
| 4.1 | 封閉測試（內部使用者測試 + 回饋收集）                                                            | DEV/QA | 4h   | ⬜ 未開始 | 05/05  | 05/06  |                                  |
| 4.2 | Bug 修復 + Security Checklist 驗證（keyring 明文檢查、命令注入防護、loopback 網路、graceful shutdown、**SSH 連線安全**） | DEV | 4h | ⬜ 未開始 | 05/06 | 05/07 | |
| 4.3 | 撰寫使用者操作手冊                                                                               | PM/DEV | 4h   | ⬜ 未開始 | 05/07  | 05/08  | 更新專案手冊（含 SSH 遠端管理章節） |
| 4.4 | 正式發佈（Release tag + 執行檔上傳 + 公告）                                                      | PM/DEV | 4h   | ⬜ 未開始 | 05/08  | 05/08  |                                  |

---

## 4. 進度摘要

### 整體進度

階段 1 (Inception & Planning) 已完成。階段 2 (Design & Architecture) 進行中，架構設計與 ADR 已完成（含 ADR-003 廢棄 Shell 腳本、ADR-004 SSH 遠端管理 Transport Layer），前端規格書已完成，正進行 UI Mockup 設計。階段 3 (Construction) 的 3.1 專案環境初始化已完成。

**v3.0 排程重構重點**：修正依賴倒置問題 — Executor Protocol (3.15.1) + LocalExecutor (3.15.2) 提前至 Week 2 第一天作為所有後端模組的基礎；3.16 SSH 前端整合拆散合併至對應功能模組；所有後端模組從第一天就透過 Executor 介面開發，避免後期重構。

### 週度進度

#### Week 1 (03/22 ～ 03/28) - 專案啟動與設計

- **已完成**:
  - `200_project_brief_prd.md` 建立與確認。
  - `201_wbs_plan.md` 建立與確認。
  - `202_architecture_design.md` 架構設計完成。
  - `208_frontend_specification.md` 前端規格書完成。
  - `ADR-001` 前端框架選擇決策：維持 Vanilla HTML/JS + Tailwind CSS，不採用 React。
  - `ADR-002` 套件管理選擇決策：使用 uv。
  - `ADR-003` 廢棄 Shell 腳本，改以原生 Python 實作。
  - `ADR-004` SSH 遠端管理 Transport Layer 提案（Proposed）。
- **已完成 (補充)**:
  - `3.1` 專案環境初始化：uv init (Python 3.12)、pyproject.toml 設定、src/ 模組骨架、PyWebView 最小可執行入口、tests/ 目錄、uv sync 依賴安裝與 lock file 產生。
  - `201_wbs_plan.md` v3.0 排程重構：修正依賴倒置（Executor Protocol 提前至 Week 2）、3.16 合併拆散、任務優先級重排。
- **進行中**:
  - UI Mockup 設計 (`pencil-new.pen`)。
- **計劃中**:
  - Bridge API Spec 設計 (2.4)。
  - QA 測試案例撰寫 (2.5)。

---

## 5. 風險與議題

### 風險管控矩陣

| 風險項目                                             | 影響度 | 可能性 | 緩解措施                                                                                      | 負責人 |
| :--------------------------------------------------- | :----- | :----- | :-------------------------------------------------------------------------------------------- | :----- |
| **PyWebView 與結構化 UI 更新的效能瓶頸**             | 中     | 低     | ADR-003 改用結構化 JSON 回傳取代 stdout 串流，DOM 更新頻率大幅降低，風險已緩解。              | DEV    |
| **PyInstaller 打包跨平台檔案遇到的依賴問題**         | 高     | 高     | 在開發早期建立 CI/CD 或本地打包腳本，隨時驗證打包後的執行檔。                                 | DEV    |
| **Docker-compose 與 Systemctl 在不同環境的權限問題** | 中     | 高     | 確保 GUI 應用程式執行時會檢查權限，並在 UI 上給予友善的錯誤提示（如「請以系統管理員執行」）。 | DEV    |
| **金鑰安全儲存的跨平台相容性**                       | 中     | 中     | 使用 Python `keyring` 套件統一介面，開發初期驗證 Windows/Linux 各環境的整合。                 | DEV    |
| **openclaw.json 結構複雜性**                         | 高     | 中     | `openclaw.json` 為多層巢狀 JSON 結構（agents, channels, gateway, plugins, tools, commands），GUI 寫入邏輯需確保不破壞既有設定。緩解：讀取後 deep merge，寫入前備份（利用 openclaw 自身 `.bak` 機制）。 | DEV    |
| **SSH 連線穩定性與網路中斷** (ADR-004)               | 高     | 中     | `ssh_connection.py` 實作自動重連機制（失敗重試 3 次，間隔 2/4/8 秒指數退避）、30 秒心跳 keepalive 偵測中斷、長時間操作透過 `on_output` callback 串流避免 channel 閒置逾時。前端顯示連線狀態指示燈即時回饋。 | DEV    |
| **SFTP 大檔案傳輸效能** (ADR-004)                    | 中     | 低     | 技能部署上傳可能涉及大量小檔案遞迴傳輸（SFTP 無原生 copytree），效能較本機 shutil 慢。緩解：提供傳輸進度回呼、限制單次上傳檔案數量、未來可考慮 tar + pipe 優化。 | DEV    |

### 待決事項

| ID | 議題 | 狀態 | 備註 |
| :- | :--- | :--- | :--- |
| OQ-1 | GUI 是否需支援 `openclaw channels login`（WhatsApp QR 登入）和 `channels add`（Telegram/Discord token 新增）的等價功能？ | 🟡 待決議 | 決議後追加至 WBS，預估 +8h |

---

## 6. 品質與里程碑

### 關鍵里程碑

| 里程碑                                              | 預定日期   | Gate Criteria                                              | 狀態      |
| :-------------------------------------------------- | :--------- | :--------------------------------------------------------- | :-------- |
| **M1: PRD + WBS 完成 (Gate 1)**                     | 2026-03-24 | PRD 與 WBS 核准                                           | ✅ 完成   |
| **M2: 架構設計 + UI Mockup + 前端規格書 (Gate 2)**  | 2026-03-28 | 設計文件全部核准，API Spec 定稿                            | 🔄 進行中 |
| **M3: 核心功能開發完成 (Gate 3)**                    | 2026-04-18 | Transport Layer + 前端 UI 元件 + 環境檢查 + Config Manager + Config Step 1+2 + SSH 連線整合 端到端可用 | ⬜ 未開始 |
| **M4: 全功能開發 + 打包測試 (Gate 4)**               | 2026-05-01 | 所有 US (含 US-007 SSH) 實作完成、所有後端模組透過 Executor 介面運作 | ⬜ 未開始 |
| **M5: 應用程式正式發佈上線 (Launch)**                | 2026-05-08 | PyInstaller 打包成功、QA 驗證通過、封閉測試通過、Bug 修復完成、文件就緒 | ⬜ 未開始 |

### 品質指標

- **測試覆蓋率**: 主力業務邏輯（Python 操作模組）需達 80%。
- **穩定性**: PyInstaller 打包出的檔案，在 Windows/Linux 原生環境啟動不可直接閃退，崩潰率 (Crash Rate) < 1%。
- **流暢度**: 操作進度回饋延遲 < 500ms，不會造成整個 UI 凍結。
- **安全性**: Security Checklist — keyring 金鑰儲存驗證、命令注入防護 (list 形式 subprocess)、loopback 網路隔離、graceful shutdown。
