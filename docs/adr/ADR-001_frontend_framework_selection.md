# 決策紀錄 (ADR-001): 前端框架選擇 — Tailwind CSS (Vanilla) vs React

---

**狀態:** `已接受 (Accepted)`
**日期:** `2026-03-23`

---

## 1. 脈絡與問題 (Context)

- **問題描述**: OpenClaw GUI 需要選擇前端技術方案。目前架構文件規劃使用 Vanilla HTML/JS + Tailwind CSS，需評估是否改用 React 框架會帶來更好的效益。
- **關鍵驅動因素 (Drivers)**:
  - **專案規模**：UI 功能有限（表單、按鈕、日誌顯示），共 6 個使用者故事。
  - **時程壓力**：總工期 5 週、116 小時，其中前端實作約 52 小時。
  - **團隊規模**：1 名前端/全端開發人員。
  - **技術約束**：PyWebView Bridge 模式，前端完全無狀態；PyInstaller 打包為單一可執行檔。
  - **維護成本**：長期可維護性與擴展性。

## 2. 方案評估 (Options)

### 方案 1: Vanilla HTML/JS + Tailwind CSS（現行方案）

- **優點 (Pros)**:
  - **零編譯流程**：HTML/JS 直接載入，無需 Node.js 工具鏈（Vite/Webpack），Tailwind 可用 CDN 或預編譯 CSS。
  - **打包簡單**：靜態檔案直接嵌入 PyInstaller，無額外 `node_modules` 依賴，產出體積小。
  - **學習門檻低**：無框架抽象層，任何會 HTML/JS 的開發者即可上手。
  - **啟動速度快**：無 Virtual DOM 開銷，頁面載入即渲染，符合 < 200ms 反應要求。
  - **與 PyWebView Bridge 天然契合**：直接呼叫 `window.pywebview.api.*`，無需額外封裝層。
  - **除錯直覺**：DOM 即所見，無框架層間接性。

- **缺點 (Cons)**:
  - **手動 DOM 操作**：狀態變化需手動更新 DOM，程式碼可能較冗長。
  - **無組件化機制**：UI 片段復用需自行實作（template literals 或 Web Components）。
  - **大規模擴展較吃力**：若未來 UI 複雜度大幅上升，維護難度會增加。

### 方案 2: React + Tailwind CSS

- **優點 (Pros)**:
  - **組件化架構**：UI 元素封裝為可復用的 Component，結構清晰。
  - **宣告式 UI**：狀態驅動渲染，減少手動 DOM 操作的 Bug。
  - **豐富生態系**：大量現成 UI 元件庫（Headless UI、Radix 等）。
  - **開發體驗 (DX)**：Hot Module Replacement (HMR)、JSX 語法提示、React DevTools。

- **缺點 (Cons)**:
  - **引入編譯工具鏈**：需 Vite 或 Webpack，增加 `node_modules`（通常 200MB+）與建置步驟。
  - **打包複雜度上升**：PyInstaller 需額外處理編譯產物的路徑與嵌入，增加 `build.py` 複雜度與除錯成本。
  - **過度工程**：本專案 UI 僅含表單、按鈕、日誌面板，無路由、無複雜狀態樹、無跨頁互動——React 的核心優勢（組件樹、狀態管理、路由）幾乎用不上。
  - **額外抽象層**：PyWebView Bridge 呼叫需包裝為 React Hook 或 Context，增加間接性。
  - **執行檔體積膨脹**：React runtime + 編譯產物使最終包體積增大。
  - **開發時程風險**：工具鏈設定、打包整合除錯可能佔去 8-12 小時（占前端工時 15-23%）。
  - **團隊適配風險**：若開發者不熟 React，學習成本直接衝擊 5 週工期。

## 3. 決策結果 (Decision)

**選中方案**: 方案 1 — Vanilla HTML/JS + Tailwind CSS

**選擇理由**:

用 Linus 的話說：**「問題的複雜度不配得上 React。」**

1. **複雜度匹配**：本專案的前端本質是「表單收集 + 按鈕觸發 + 日誌顯示」，這是一個簡單的介面層。React 解決的是「頻繁狀態變化驅動複雜 UI 更新」的問題——我們沒有這個問題。前端完全無狀態（Bridge 模式），狀態全在 Python 後端。
2. **打包零摩擦**：Vanilla 靜態檔案與 PyInstaller 天然相容，React 則需額外處理編譯產物路徑，這是已知的高風險項目（見 WBS 風險矩陣）。
3. **時程保護**：5 週工期、1 名開發者，沒有餘裕投入在框架工具鏈整合上。每一小時都應花在業務功能，而非解決 Vite + PyInstaller 的路徑衝突。
4. **YAGNI 原則**：如果未來 UI 真的複雜到需要框架，屆時再遷移的成本遠低於現在提前引入框架的沉沒成本。現階段 6 個 User Story 的 UI 用 Vanilla 實作綽綽有餘。

## 4. 後續影響 (Consequences)

- **正向影響**:
  - 前端開發可立即啟動，無需花時間設定工具鏈。
  - PyInstaller 打包流程保持簡單，降低 WBS 3.6 的風險。
  - 產出的執行檔體積更小，啟動更快。
  - 降低專案對特定框架生態的耦合，未來技術選擇更自由。

- **負向影響**:
  - 若未來 UI 需求大幅擴展（例如新增 10+ 頁面或複雜互動），可能需要重構為框架架構，屆時遷移成本約 16-24 小時。
  - 開發者需自律維持 JS 程式碼結構（建議以模組化 ES Module 組織 `app.js`，避免單一大檔案）。
  - 需自行實作簡易的 UI 更新機制（例如封裝 `renderLog()`、`updateStatus()` 等函式），避免散落的 `document.getElementById` 呼叫。
