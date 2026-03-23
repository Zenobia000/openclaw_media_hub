# 決策紀錄 (ADR-003): 廢棄 Shell 腳本，改以原生 Python 實作所有操作邏輯

---

**狀態:** `已接受 (Accepted)`
**日期:** `2026-03-23`

---

## 1. 脈絡與問題 (Context)

- **問題描述**: 現有架構透過 Python subprocess 呼叫 `scripts/` 下的 Shell 腳本 (`.ps1` / `.sh`) 執行所有操作（環境檢查、初始化、技能部署、外掛安裝、服務啟停等）。前端透過 terminal 元件即時顯示腳本的 stdout/stderr 原始輸出。此設計存在以下痛點：
  1. **雙倍維護成本**：每個功能需維護 PowerShell (Windows) 與 Bash (Linux) 兩套腳本，邏輯重複但語法完全不同。
  2. **使用者體驗差**：前端呈現原始 terminal 日誌，一般使用者無法理解，違背「降低使用門檻」的目標。
  3. **不必要的間接性**：腳本邏輯（偵測軟體、操作目錄/檔案、讀寫 JSON、呼叫 docker CLI）全部可由 Python 直接完成，subprocess 呼叫 shell 是多餘的中間層。
  4. **錯誤處理困難**：shell 腳本的 exit code 與 stderr 語義不統一，Python 端難以對錯誤做結構化分類與 UI 呈現。
  5. **打包複雜度增加**：PyInstaller 需額外將 shell 腳本打包進執行檔，且 Windows 使用者需額外啟用 PowerShell 執行政策。

- **關鍵驅動因素 (Drivers)**:
  - **UX 優先**：降低使用者操作門檻，以結構化 UI（進度條、狀態卡片、表單）取代 terminal 輸出。
  - **可維護性**：統一為單一語言 (Python)，消除跨平台腳本的維護負擔。
  - **簡潔性**：消除 subprocess → shell 這層不必要的間接層。

## 2. 方案評估 (Options)

### 方案 1: 維持現狀（subprocess 呼叫 Shell 腳本）

- **優點 (Pros)**: 既有腳本已可運作，不需重寫；腳本可獨立於 GUI 在命令列使用。
- **缺點 (Cons)**: 雙倍維護成本 (`.ps1` + `.sh`)；前端只能呈現原始 terminal 輸出，UX 差；腳本中的互動式操作（`Read-Host`、`ReadKey`）無法在 GUI 中使用；錯誤處理不結構化；打包增加複雜度。

### 方案 2: 廢棄 Shell 腳本，所有操作邏輯以原生 Python 實作

- **優點 (Pros)**:
  - 統一為 Python 單一語言，消除跨平台腳本維護。
  - Python 原生跨平台：`shutil.which()` 取代 `Get-Command`/`which`、`pathlib` 取代路徑操作、`json` 取代 `ConvertFrom-Json`。
  - 前端可用結構化 UI（進度條、勾選清單、狀態徽章）取代 terminal，大幅提升 UX。
  - 錯誤處理結構化：Python exception → 明確的錯誤類型 → 前端呈現友善訊息。
  - PyInstaller 打包更簡潔，不需處理額外腳本檔案。
  - Docker CLI、systemctl 等少數仍需 subprocess 的呼叫，可在 Python 中精確控制參數與輸出解析。
- **缺點 (Cons)**:
  - 需要投入時間將現有腳本邏輯移植為 Python 程式碼。
  - 腳本將無法在 GUI 外獨立使用（但 GUI 本身即為取代命令列的產物，此為預期行為）。

## 3. 決策結果 (Decision)

**選中方案**: 方案 2 — 廢棄 Shell 腳本，所有操作邏輯以原生 Python 實作

**選擇理由**:

1. **消除特殊情況** (Good Taste)：不再需要根據 OS 選擇 `.ps1` 或 `.sh`，Python 本身即跨平台，`platform_utils.py` 中的 `resolve_script()` / `build_command()` 等腳本路由邏輯可完全消除。
2. **不破壞使用者空間**：GUI 就是新的使用者空間，腳本是舊的介面。GUI 完整覆蓋所有腳本功能即滿足此原則。
3. **實用主義**：腳本邏輯並不複雜（軟體偵測、目錄建立、JSON 讀寫、docker CLI 呼叫），Python 實作更簡潔且可測試。
4. **UX 飛躍**：前端從 terminal 日誌升級為結構化 UI，降低使用門檻是專案核心目標。

### 實作策略

| 腳本功能 | Python 實作方式 | 前端 UI |
| :--- | :--- | :--- |
| **環境檢查** (check-env) | `shutil.which()` 偵測 Docker/VS Code/ngrok；`subprocess.run()` 取版本號 | 狀態卡片列表（綠/紅徽章） |
| **初始化** (init) | `pathlib` 建立目錄、`json` 讀寫 config、`subprocess` 呼叫 `docker compose` | 步驟精靈 (wizard) 含表單 |
| **API 金鑰設定** | `keyring` 安全儲存、`json` 寫入 config | 表單輸入欄位 |
| **服務啟停** | `subprocess.run(["docker", "compose", "up/down"])` 或 systemctl | 開關按鈕 + 狀態指示 |
| **技能部署** (deploy-skills) | `pathlib` 掃描目錄、解析 SKILL.md、`shutil.copytree/rmtree` | 勾選清單 + 進度指示 |
| **外掛安裝** (install-plugins) | 同技能部署模式 | 勾選清單 + 進度指示 |
| **修復插件** (fix-plugin) | Python 邏輯判斷 + 必要時 `subprocess` 呼叫 docker exec | 狀態診斷 + 一鍵修復按鈕 |

### 仍需 subprocess 的場景

以下操作本質上需呼叫外部程式，仍使用 `subprocess`，但直接在 Python 中控制：
- `docker compose up -d` / `docker compose down` / `docker compose exec`
- `systemctl start/stop`（Linux native）
- `docker info` / `docker --version`（版本偵測）

差異在於：不再呼叫整個 shell 腳本，而是在 Python 中精確呼叫單一指令，並結構化解析輸出。

## 4. 後續影響 (Consequences)

- **正向影響**:
  - 維護成本降低：從「Python + PowerShell + Bash」三語言降為「純 Python」。
  - UX 大幅提升：使用者看到友善的 UI 元件而非 terminal 日誌。
  - 可測試性提升：Python 函式可直接撰寫單元測試，不需模擬 shell 環境。
  - 打包更簡潔：PyInstaller 只需打包 Python 程式碼。
  - 錯誤處理結構化：明確的 exception 類型映射至 UI 友善訊息。
- **負向影響**:
  - 需投入開發時間移植現有腳本邏輯（約 16-20h）。
  - `scripts/` 目錄保留但標記為 deprecated，供命令列使用者過渡。
  - 前端 terminal 元件廢棄，需重新設計各功能的 UI 頁面。
- **需更新的文件**:
  - `CLAUDE.md`：移除「禁止修改 scripts/」規則，更新架構描述。
  - `202_architecture_design.md`：更新資料流與組件設計。
  - `200_project_brief_prd.md`：更新範圍定義（移除「不修改 scripts」限制）。
  - `201_wbs_plan.md`：調整工作包與工時估算。
