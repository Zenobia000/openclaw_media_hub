# 決策紀錄 (ADR-007): 前端多國語言支援 — 繁體中文與英文

---

**狀態:** `已接受 (Accepted)`
**日期:** `2026-03-30`

---

## 1. 脈絡與問題 (Context)

- **問題描述**: 前端 11 個 JS 檔案中有 121+ 個 UI 字串（按鈕標籤、狀態訊息、面板標題、錯誤訊息等）全部以英文硬編碼於 template literals 和 `renderXxx()` 函式呼叫中。目標使用者包含繁體中文與英文使用者，需要支援語言切換。

- **現況分析**:
  - `index.html` 靜態設定 `<html lang="en">`，無動態切換
  - 字串散佈於 `components.js`（通用元件）、`page-*.js`（頁面邏輯）、`router.js`（導航標籤）、`item-list.js`（清單操作）等 11 個檔案
  - 字串類型涵蓋：導航標籤、按鈕文字、狀態標籤、表單欄位名稱、描述文字、錯誤/成功訊息、Toast 通知
  - 無任何 i18n 基礎設施（無翻譯函式、無語系檔、無 locale 偵測）

- **關鍵驅動因素 (Drivers)**:
  - 目標受眾為台灣使用者（繁體中文為主）與國際使用者（英文）
  - 降低使用門檻：母語介面大幅降低非技術使用者的認知負擔
  - 前端為 Vanilla JS（無框架），i18n 方案必須輕量且無編譯依賴
  - PyWebView `file://` 協議限制：不使用 ES Modules，所有 JS 共享全域作用域

## 2. 方案評估 (Options)

### 方案 1: 輕量自建 `t()` 函式 + JSON 語系檔

在 `core.js` 中實作一個全域翻譯函式 `t(key)`，語系資料以 JSON 物件形式存放於獨立的語系檔案中（`locales/zh-TW.json`, `locales/en.json`），透過 `<script>` 標籤載入。

```
frontend/
├── locales/
│   ├── zh-TW.json        # 繁體中文語系檔
│   └── en.json            # 英文語系檔
└── js/
    └── core.js            # t() 函式定義於此
```

**翻譯函式設計**:
```javascript
// core.js — 語系狀態與翻譯函式
let currentLocale = {};

function t(key, params) {
  let text = currentLocale[key] || key;
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      text = text.replace(`{${k}}`, v);
    });
  }
  return text;
}

function setLocale(locale) { /* 載入對應 JSON，重新渲染當前頁面 */ }
```

**語系檔結構** (flat key):
```json
{
  "nav.dashboard": "儀表板",
  "nav.configuration": "系統設定",
  "btn.start_services": "啟動服務",
  "btn.stop_services": "停止服務",
  "status.running": "執行中",
  "status.stopped": "已停止",
  "toast.deploy_success": "技能 {name} 部署成功"
}
```

- **優點 (Pros)**:
  - 零外部依賴，完全掌控，與現有 Vanilla JS + 全域作用域架構完美相容
  - 語系檔為純 JSON，非技術人員也可協助翻譯
  - `t()` 函式極簡（< 20 行），無效能負擔
  - 支援插值參數（`{name}`, `{count}` 等動態內容）
  - PyInstaller 打包時語系檔作為靜態資源嵌入，無額外配置
  - 新增語言只需新增一個 JSON 檔案

- **缺點 (Cons)**:
  - 需手動將 11 個 JS 檔案中的硬編碼字串逐一替換為 `t()` 呼叫（一次性工作量）
  - 無內建的複數形式（pluralization）處理，需要時須自行擴充
  - 缺少翻譯管理平台整合（可接受，v1.0 僅兩種語言）

### 方案 2: 引入 i18next 輕量版（i18next-core）

使用業界主流的 i18next 函式庫（壓縮後 ~13KB），透過 CDN 引入。提供完整的 i18n 功能（命名空間、複數、巢狀 key、語系偵測等）。

- **優點 (Pros)**:
  - 業界標準，功能完整（pluralization、nesting、context、interpolation）
  - 豐富的生態系（語系偵測、快取、翻譯管理平台整合）
  - 社群維護，長期穩定

- **缺點 (Cons)**:
  - 新增外部依賴，與專案「零前端框架」方針矛盾
  - 初始化為非同步（`i18next.init()` 返回 Promise），需處理載入時序問題
  - 功能過剩：複數、巢狀、命名空間等功能在繁中/英雙語場景中幾乎用不到
  - CDN 引入需離線打包處理；若改為本機 bundle 則增加打包複雜度
  - 全域作用域下需額外處理 `i18next` 物件的初始化時機

### 方案 3: HTML `data-i18n` 屬性 + DOM 掃描替換

在 HTML 元素上標記 `data-i18n="key"`，頁面載入或切換語言時掃描 DOM 並替換文字。

- **優點 (Pros)**:
  - HTML 模板與翻譯 key 的對應關係明確
  - 適合靜態 HTML 頁面

- **缺點 (Cons)**:
  - 本專案 HTML 幾乎全由 JS 動態生成（`innerHTML` + template literals），靜態 HTML 元素極少
  - 需在每次 `innerHTML` 更新後重新掃描 DOM，效能差且容易遺漏
  - 無法處理 JS 中的字串（Toast 訊息、動態錯誤文字、status 判斷邏輯中的字串）
  - 與現有的 `renderXxx()` 元件模式嚴重不相容

## 3. 決策結果 (Decision)

**選中方案**: 方案 1 — 輕量自建 `t()` 函式 + JSON 語系檔

**選擇理由**: 本專案前端為 Vanilla JS、全域作用域、`file://` 協議，且僅需支援繁中/英兩種語言。方案 1 零依賴、與現有架構完美契合、實作量可控。方案 2 功能過剩且引入不必要的外部依賴；方案 3 與 JS 動態渲染模式根本不相容。

### 實作策略

#### 3.1 語系檔結構

```
frontend/
├── locales/
│   ├── zh-TW.json         # 繁體中文（預設語言）
│   └── en.json             # 英文
```

**Key 命名慣例** — flat dot-notation，前綴對應模組：

| 前綴 | 範圍 | 範例 |
|:---|:---|:---|
| `nav.*` | Sidebar 導航 | `nav.dashboard`, `nav.deploy_skills` |
| `btn.*` | 按鈕標籤 | `btn.start`, `btn.stop`, `btn.deploy` |
| `status.*` | 狀態標籤 | `status.running`, `status.stopped` |
| `dashboard.*` | Dashboard 頁面 | `dashboard.title`, `dashboard.service_control` |
| `config.*` | Configuration 頁面 | `config.step1_title`, `config.mode_docker` |
| `env.*` | Environment 頁面 | `env.title`, `env.check_all` |
| `gateway.*` | Gateway 頁面 | `gateway.title`, `gateway.origin_control` |
| `skills.*` | Deploy Skills 頁面 | `skills.title`, `skills.deploy_btn` |
| `plugins.*` | Install/Fix Plugins | `plugins.title`, `plugins.install_btn` |
| `common.*` | 跨頁面共用 | `common.loading`, `common.error`, `common.retry` |
| `toast.*` | Toast 通知訊息 | `toast.deploy_success`, `toast.connection_failed` |

#### 3.2 翻譯函式 API

```javascript
// 定義於 core.js（載入順序 #1，所有後續 JS 皆可呼叫）

t(key)                    // 基本翻譯：t("btn.start") → "啟動服務"
t(key, { name, count })   // 插值：t("toast.deploy_success", { name: "天氣" }) → "技能「天氣」部署成功"
```

#### 3.3 語言偵測與切換

| 優先順序 | 來源 | 說明 |
|:---|:---|:---|
| 1 | `gui-settings.json` → `locale` | 使用者手動選擇的語言（持久化） |
| 2 | `navigator.language` | 瀏覽器 / OS 語系偵測 |
| 3 | `zh-TW` | 預設 fallback（目標受眾為台灣使用者） |

**切換機制**:
- Sidebar 底部或設定區域提供語言切換（下拉選單或圖示按鈕）
- 切換後透過 Bridge API 將偏好寫入 `gui-settings.json`
- 呼叫 `setLocale()` 載入新語系檔並重新渲染當前頁面（利用現有的 `registerPage` 生命週期鉤子觸發 `render()`）

#### 3.4 載入時序

```
<script> locales/zh-TW.json (預設語系，同步載入)
<script> js/core.js          — t() 可用
<script> js/router.js
...
<script> js/bootstrap.js     — initApp() 中依 gui-settings 切換語系
```

語系 JSON 以 `<script>` 標籤載入為全域變數（例如 `window.__locale_zhTW = {...}`），避免非同步 `fetch()` 在 `file://` 協議下的 CORS 問題。

#### 3.5 遷移步驟

1. 建立 `locales/en.json`，以現有英文字串為基底，建立完整 key-value 映射
2. 建立 `locales/zh-TW.json`，翻譯所有 key
3. 在 `core.js` 實作 `t()`, `setLocale()` 函式
4. 逐檔替換硬編碼字串為 `t()` 呼叫（11 個 JS 檔案）
5. `index.html` 新增語系檔 `<script>` 引入
6. `bootstrap.js` 的 `initApp()` 中加入語系初始化邏輯
7. 新增語言切換 UI 元件

#### 3.6 Bridge API 新增

| 方法 | 功能 | 實作方式 |
|:---|:---|:---|
| `get_locale()` | 讀取使用者語言偏好 | `gui-settings.json` → `locale` |
| `save_locale(params)` | 儲存使用者語言偏好 | 寫入 `gui-settings.json` → `locale` |

## 4. 後續影響 (Consequences)

- **正向影響**:
  - 台灣使用者可使用繁體中文介面，大幅降低認知門檻
  - 國際使用者保有英文介面
  - 語系架構可擴展：未來新增語言只需新增一個 JSON 檔案
  - 零外部依賴，不增加打包複雜度
  - `t()` 函式集中管理所有 UI 字串，提升字串一致性與可維護性
- **負向影響**:
  - 一次性遷移工作量：11 個 JS 檔案、121+ 個字串需逐一替換
  - 語系檔需人工維護同步（可透過 CI 腳本檢查 key 一致性緩解）
  - 切換語言時需重新渲染當前頁面（利用既有的頁面生命週期，影響可忽略）
- **需更新的文件**:
  - `docs/208_frontend_specification.md`：§1.1 新增 i18n 技術決策、§1.2 新增 locales 目錄與載入順序
  - `CLAUDE.md`：專案結構新增 `locales/` 目錄說明
  - `docs/202_architecture_design.md`：L3 元件新增 i18n 模組描述
