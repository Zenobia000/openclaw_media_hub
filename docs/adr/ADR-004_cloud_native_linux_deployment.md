# 決策紀錄 (ADR-004): 雲端平台 Native Linux 部署 — SSH 遠端管理 Transport Layer

---

**狀態:** `提案中 (Proposed)`
**日期:** `2026-03-24`

---

## 1. 脈絡與問題 (Context)

- **問題描述**: OpenClaw GUI 目前支援兩種部署模式（Docker / Native Linux），皆假設使用者在**有桌面環境的本機**操作 PyWebView GUI。當使用者將 OpenClaw 部署至**雲端 VM**（AWS EC2、GCP Compute Engine、Azure VM、DigitalOcean Droplet 等）以 Native Linux (systemd) 模式運行時，面臨以下具體障礙：

  1. **無顯示伺服器**：雲端 VM 為 headless 環境，無 X11/Wayland，PyWebView 無法啟動。使用者無法透過 GUI 完成初始化、金鑰設定、技能部署等操作。
  2. **keyring 後端缺失**：headless Linux 通常未安裝 `gnome-keyring` 或 `libsecret`，`keyring` 套件無法正常運作，金鑰儲存機制失效。
  3. **網路綁定模型變化**：現有 `OPENCLAW_GATEWAY_BIND` 僅支援 `loopback` / `lan`，雲端部署需要綁定至 `0.0.0.0` 或指定網路介面，且需考慮防火牆規則與 HTTPS。
  4. **遠端設定難題**：使用者如何從本機電腦設定遠端伺服器的 API 金鑰、外掛、技能？目前所有操作模組（`env_checker.py`, `initializer.py`, `skill_manager.py` 等）皆假設本機存取（直接使用 `pathlib`, `shutil`, `subprocess`）。
  5. **安全模型差異**：雲端代表網路暴露，Gateway Token 認證、TLS 加密、防火牆規則成為必要項，非可選項。

- **關鍵驅動因素 (Drivers)**:
  - **實際需求**：使用者希望在雲端 VM 上運行 OpenClaw（非 Docker 模式），且不願或無法在伺服器安裝 Docker。
  - **UX 一致性**：使用者應能用同一套 GUI 管理本機與遠端部署，降低學習成本。
  - **ADR-003 延伸**：所有操作邏輯以原生 Python 實作的原則，可自然延伸為「透過抽象層同時支援本機與遠端操作」。

- **現有架構可利用的支點**:
  - `service_controller.py` 已有 Docker vs systemctl 分支，增加遠端模式為既有設計的自然延伸。
  - `config_manager.py` 金鑰儲存於本機 keyring，初始化時寫入 `.env`——此流程天然適用於遠端部署（金鑰存本機，寫入遠端 `.env`）。
  - **程式碼尚未開發**（M1 設計階段），抽象層可從一開始內建，無需事後重構。

## 2. 方案評估 (Options)

### 方案 1: Config Export + 輕量 CLI 安裝器

GUI 在本機生成所有設定檔（`openclaw.json`, `.env`, `openclaw.service` systemd unit file），匯出為 zip。使用者手動 SCP 至雲端伺服器，執行 `python3 install.py` 完成安裝。

- **優點 (Pros)**:
  - 零架構變更，GUI 核心不需修改，僅新增一個 export 功能。
  - 工時最低（約 8-12h）。
  - 安全模型簡潔：金鑰在伺服器本地輸入，不經網路傳輸。
  - `install.py` 遵循 ADR-003（純 Python 實作）。
- **缺點 (Cons)**:
  - 手動步驟多（SCP + SSH + 執行腳本），與「降低使用門檻」目標有落差。
  - 後續管理不便：技能部署、外掛安裝等操作需手動在伺服器執行，或重新 export + 傳輸。
  - 功能不對稱：雲端使用者無法使用環境檢查、服務控制等 GUI 功能。

### 方案 2: Transport Abstraction Layer + SSH 遠端管理

建立 `Executor` Protocol 抽象層，定義統一的操作介面。`LocalExecutor` 封裝 `subprocess` / `pathlib` / `shutil`（本機模式），`RemoteExecutor` 封裝 `paramiko.SSHClient` + `SFTPClient`（遠端模式）。所有後端模組透過 Executor 介面操作，不直接呼叫底層 I/O。

- **優點 (Pros)**:
  - **架構乾淨**：消除「本機 vs 遠端」的特殊情況於 transport 層，上層模組無需感知執行位置（Good Taste）。
  - **從頭內建**：程式碼尚未開發，所有模組可從一開始針對 Executor 介面撰寫，無需事後重構。
  - **單一應用程式**：GUI 即為唯一管理介面，本機與遠端使用相同 UI 體驗。
  - **可測試**：Executor 為 Protocol，可輕易 mock 進行單元測試。
  - **keyring 自然解決**：金鑰存本機 keyring（不變），初始化時透過 `RemoteExecutor` 寫入遠端 `.env`，與 Docker 模式的 `.env` 注入機制一致。
- **缺點 (Cons)**:
  - 增加約 30h 工時（因從頭內建，無重構成本；若事後加入則需 48h）。
  - 新增 `paramiko` 依賴（成熟套件，純 Python，與 PyInstaller 相容）。
  - SSH 連線穩定性需處理：重連機制、心跳、逾時。
  - 跨本機/遠端的檔案傳輸（技能部署：本機 `module_pack/` → 遠端 `~/.openclaw/workspace/skills/`）需額外 `TransferService`。
  - SFTP 無原生 `copytree`，遞迴上傳需手動實作。

### 方案 3: Remote Agent（遠端代理）

在遠端伺服器部署一支輕量 Python agent，GUI 透過 SSH tunnel（port forwarding）與 agent 通訊。Agent 在遠端本機執行所有操作，暴露與 Bridge 相同的 API。

- **優點 (Pros)**:
  - 後端模組無需任何修改（agent 在遠端本機執行，`pathlib` / `subprocess` 直接可用）。
  - 通訊可透過 SSH tunnel 加密。
- **缺點 (Cons)**:
  - **部署 bootstrap 問題**：agent 本身需要先被部署到伺服器（需 SCP + SSH），形成雞生蛋問題。
  - **雙碼庫維護**：agent API 必須與 GUI Bridge API 保持同步，版本漂移風險高。
  - **破壞單一執行檔承諾**：agent 為第二個可交付物，需獨立打包與分發。
  - **keyring 仍不可用**：agent 在 headless 環境執行，keyring 問題未解決。
  - **技能部署仍需跨機器傳輸**：`module_pack/` 在本機，目標在遠端，agent 無法獨立完成。
  - 工時估算 40-50h，且架構複雜度最高。

## 3. 決策結果 (Decision)

**選中方案**: 方案 2 — Transport Abstraction Layer + SSH 遠端管理

**選擇理由**:

### Linus 三問

1. **是真問題嗎？** 是。雲端 VM headless 環境跑不了 PyWebView 是真實的技術限制，不是假想威脅。
2. **有更簡單的方法嗎？** 方案 1 更簡單但犧牲 UX。方案 2 在程式碼尚未開發的前提下，是最佳的成本/效益平衡——從頭內建 Executor 的成本（~30h）遠低於事後重構（~48h）。
3. **會破壞現有功能嗎？** 不會。`LocalExecutor` 完整封裝現有行為，桌面 GUI 的本機模式零影響。

### 核心洞察

**將「本機 vs 遠端」的特殊情況轉化為正常情況。** Executor Protocol 讓上層模組不需要知道操作發生在哪裡——這正是 Good Taste 的體現。與 ADR-003 消除「Windows 腳本 vs Linux 腳本」的特殊情況是同一個設計哲學。

### 實作設計

#### Executor Protocol

```python
class Executor(Protocol):
    async def run_command(self, args: list[str], timeout: int = 300,
                          on_output: Callable[[str], None] | None = None) -> CommandResult: ...
    async def read_file(self, path: str) -> bytes: ...
    async def write_file(self, path: str, data: bytes) -> None: ...
    async def mkdir(self, path: str, parents: bool = True) -> None: ...
    async def copy_tree(self, src: str, dst: str) -> None: ...
    async def remove_tree(self, path: str) -> None: ...
    async def file_exists(self, path: str) -> bool: ...
    async def list_dir(self, path: str) -> list[str]: ...
    async def which(self, name: str) -> str | None: ...
```

#### 新增模組

| 模組 | 職責 |
| :--- | :--- |
| `executor.py` | `Executor` Protocol 定義 + `CommandResult` dataclass |
| `local_executor.py` | 封裝 `subprocess`, `pathlib`, `shutil` |
| `remote_executor.py` | 封裝 `paramiko.SSHClient` + `SFTPClient` |
| `ssh_connection.py` | SSH 連線管理（連線/斷線/重連/心跳/狀態） |
| `transfer_service.py` | 跨本機/遠端檔案傳輸（技能部署用） |

#### 模組影響分析

| 現有模組 | 影響程度 | 改動說明 |
| :--- | :--- | :--- |
| `env_checker.py` | 中 | `shutil.which()` → `executor.which()`；`subprocess.run()` → `executor.run_command()` |
| `initializer.py` | 高 | `pathlib` 操作 → `executor.mkdir()` / `executor.write_file()`；`subprocess` → `executor.run_command()`；Health check URL 需支援遠端 IP |
| `skill_manager.py` | 高 | 目錄掃描 → `executor.list_dir()`；SKILL.md 讀取 → `executor.read_file()`；部署 → `transfer_service.upload_tree()`（本機 → 遠端） |
| `plugin_manager.py` | 中 | 外掛掃描維持本機（讀 `openclaw/extensions/`）；config 寫入 → `executor.read_file()` + `executor.write_file()`（遠端 `openclaw.json`） |
| `service_controller.py` | 低 | `subprocess.run()` → `executor.run_command()`。最單純的改動。 |
| `config_manager.py` | 高 | 分離為本機 config（`gui-settings.json`, keyring）與遠端 config（`openclaw.json`, `.env`）。遠端操作透過 executor。 |
| `bridge.py` | 中 | 新增 `connect_remote()`, `disconnect_remote()`, `get_connection_status()` API。根據連線狀態選擇 executor。 |

#### keyring Fallback 策略

1. 金鑰儲存於**本機** keyring（不變，與現有設計一致）。
2. `initializer.py` 初始化遠端伺服器時，從本機 keyring 讀取金鑰，透過 `RemoteExecutor.write_file()` 寫入遠端 `.env`（設定 `chmod 600`）。
3. 遠端 systemd service 透過 `EnvironmentFile=~/.openclaw/.env` 注入環境變數。
4. 此機制與 Docker 模式的 `.env` 注入完全一致——消除特殊情況。

#### SSH 連線管理

- 支援 SSH key 認證（私鑰路徑存於 `gui-settings.json`）與密碼認證。
- 連線狀態顯示於 UI sidebar（已連線/未連線/連線中）。
- 自動重連機制：操作失敗時嘗試重建 SSH 連線，最多重試 3 次。
- 心跳機制：每 30 秒發送 keepalive，偵測連線中斷。
- 長時間操作（`docker pull`, `docker compose up`）透過 `on_output` callback 串流輸出至前端，避免 SSH channel 閒置逾時。

#### 前端擴展

- Configuration Step 1 新增「Remote Server (SSH)」部署模式選項。
- 選擇遠端模式後顯示 SSH 連線表單（host、port、username、key file path）。
- Sidebar 新增連線狀態指示燈。
- 所有操作頁面（環境檢查、技能部署等）在遠端模式下正常運作，無 UI 差異。

#### 工時估算

| 階段 | 內容 | 工時 |
| :--- | :--- | :--- |
| Transport Layer | `executor.py` + `local_executor.py` + `remote_executor.py` + `ssh_connection.py` + `transfer_service.py` | 17h |
| Bridge 擴展 | 連線管理 API + executor 選擇邏輯 | 3h |
| 前端 | SSH 連線 UI + 狀態指示 | 4h |
| 測試 | Mock executor 單元測試 + SSH 整合測試 | 6h |
| **合計** | | **30h** |

> 因程式碼尚未開發，後端模組直接針對 Executor 介面撰寫（非事後重構），故模組適配成本為 0。

## 4. 後續影響 (Consequences)

- **正向影響**:
  - 架構天然支援本機/遠端雙模式，上層模組無需感知執行位置。
  - Executor Protocol 提升可測試性（mock 取代真實 I/O）。
  - 單一應用程式、單一 UI，使用者學習成本最低。
  - keyring → `.env` 的金鑰注入機制與 Docker 模式一致，無額外安全模型。
  - 為未來更多遠端管理場景（多伺服器管理、叢集部署）奠定基礎。
- **負向影響**:
  - 專案總工時增加約 30h（從 ~152h 增至 ~182h）。
  - 新增 `paramiko` 依賴，PyInstaller 打包體積略增。
  - SSH 連線錯誤處理增加整體複雜度（重連、逾時、network partition）。
  - SFTP 遞迴操作（upload_tree / remove_tree）需手動實作，paramiko 無原生支援。
- **需更新的文件**:
  - `202_architecture_design.md`：新增 Executor 組件、SSH 連線管理、遠端部署資料流。
  - `208_frontend_specification.md`：新增 SSH 連線 UI 規格。
  - `201_wbs_plan.md`：新增 Transport Layer 工作包與工時。
  - `CLAUDE.md`：專案結構新增 `executor.py`, `local_executor.py`, `remote_executor.py`, `ssh_connection.py`, `transfer_service.py`。
