# 決策紀錄 (ADR-002): Python 套件與環境管理工具選擇 — uv vs pip/venv vs Poetry

---

**狀態:** `已接受 (Accepted)`
**日期:** `2026-03-23`

---

## 1. 脈絡與問題 (Context)

- **問題描述**: 專案需要一套 Python 環境與套件管理方案，涵蓋：Python 版本管理、虛擬環境建立、依賴安裝與鎖定、開發/生產環境一致性。目前 `requirements.txt` + `pip` + `venv` 為預設方案，需評估是否有更現代且高效的替代工具。
- **關鍵驅動因素 (Drivers)**:
  - **開發效率**：環境建置與依賴安裝速度直接影響開發迭代節奏。
  - **跨平台一致性**：Windows 10/11 與 Linux 需一致的環境管理體驗。
  - **可重現性**：lock file 機制確保所有環境安裝相同版本的依賴。
  - **簡潔性**：工具鏈越少越好，減少開發者認知負擔。
  - **PyInstaller 相容**：打包流程需與套件管理工具無縫整合。

## 2. 方案評估 (Options)

### 方案 1: pip + venv + requirements.txt（傳統方案）

- **優點 (Pros)**:
  - Python 內建，零額外安裝。
  - 社群文件最豐富，幾乎所有教學都以此為基礎。
  - PyInstaller 整合經驗成熟。

- **缺點 (Cons)**:
  - 無原生 lock file 機制，依賴解析不確定（`pip freeze` 僅為快照，非真正鎖定）。
  - 虛擬環境建立與啟動步驟繁瑣（`python -m venv .venv && source .venv/bin/activate`）。
  - 依賴安裝速度慢（純 Python 實作，無平行下載）。
  - Python 版本管理需額外工具（pyenv/pyenv-win），跨平台體驗不一致。
  - 無法區分開發依賴與生產依賴（需手動維護多個 requirements 檔案）。

### 方案 2: Poetry

- **優點 (Pros)**:
  - `pyproject.toml` + `poetry.lock` 提供完整的依賴鎖定。
  - 區分開發/生產依賴（`[tool.poetry.group.dev.dependencies]`）。
  - 內建虛擬環境管理。

- **缺點 (Cons)**:
  - 安裝速度仍為 Python 等級，大型專案解析慢。
  - 不管理 Python 版本本身，仍需搭配 pyenv。
  - 與 PyInstaller 整合需額外配置（需匯出 requirements.txt 或自訂 hook）。
  - 工具本身安裝流程較重（pipx 或官方 installer）。
  - 解析器偶有相容性問題，社群反饋兩極。

### 方案 3: uv

- **優點 (Pros)**:
  - **極速**：Rust 實作，依賴解析與安裝速度比 pip 快 10-100 倍。
  - **All-in-one**：單一工具涵蓋 Python 版本管理（`uv python`）、虛擬環境（`uv venv`）、依賴安裝（`uv pip`）、專案管理（`uv init/add/lock/sync`）。
  - **Lock file**：`uv.lock` 提供跨平台確定性鎖定，格式為人類可讀。
  - **pyproject.toml 原生支援**：符合 PEP 621 標準，不鎖定特定工具。
  - **跨平台一致**：Windows/Linux/macOS 行為一致，單一二進位安裝。
  - **pip 相容**：`uv pip install -r requirements.txt` 可無痛遷移既有專案。
  - **輕量**：單一靜態連結二進位，無 Python 依賴（不像 Poetry 需 Python 執行時期）。

- **缺點 (Cons)**:
  - 相對較新的工具（2024 年發佈），社群生態仍在成長中。
  - 部分進階功能（如 workspace）仍在快速迭代。
  - PyInstaller 整合文件較少，需自行驗證流程。

## 3. 決策結果 (Decision)

**選中方案**: 方案 3 — uv

**選擇理由**:

1. **一個工具解決所有問題**：uv 統一了 Python 版本管理 + 虛擬環境 + 依賴管理，取代 pyenv + venv + pip 三件套。工具鏈越少，出錯的介面越少。
2. **速度即生產力**：Rust 實作的安裝速度在反覆迭代（PyInstaller 測試打包）時節省大量等待時間。
3. **確定性建置**：`uv.lock` 確保 Windows 與 Linux 開發環境完全一致，直接解決跨平台依賴不同步的隱患。
4. **遷移成本極低**：既有 `requirements.txt` 可直接匯入（`uv add -r requirements.txt`），`pyproject.toml` 符合 PEP 621 標準，不被工具綁架。
5. **簡潔**：單一二進位、單一指令入口，符合專案「簡潔執念」哲學。

## 4. 後續影響 (Consequences)

- **正向影響**:
  - 開發環境建置從「安裝 Python + 建 venv + pip install」簡化為 `uv sync` 一條指令。
  - `uv.lock` 取代 `requirements.txt`，依賴管理更精確（仍可透過 `uv export` 產生 `requirements.txt` 供 PyInstaller 使用）。
  - 新開發者 onboarding 流程大幅簡化：安裝 uv → `uv sync` → 完成。
  - Python 版本透過 `uv python pin` 統一管理，避免「在我機器上可以跑」問題。

- **負向影響**:
  - 團隊成員需學習 uv 指令（學習曲線低，與 pip 指令高度相似）。
  - PyInstaller 打包流程需驗證與 uv 虛擬環境的相容性（風險低，uv venv 結構與標準 venv 一致）。
  - 若 uv 未來發展方向偏離，可無痛退回 pip（因 `pyproject.toml` 為標準格式）。
