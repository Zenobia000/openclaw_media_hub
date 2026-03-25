# 決策紀錄 (ADR-005): 廢棄 keyring，統一以 .env 檔案儲存 API 金鑰

---

**狀態:** `已接受 (Accepted)`
**日期:** `2026-03-25`

---

## 1. 脈絡與問題 (Context)

- **問題描述**: ADR-004 引入 SSH 遠端管理後，使用者可從一台本機 GUI 透過 SSH 管理多台遠端伺服器。現有的 `keyring`（系統安全儲存）金鑰管理策略與此多機場景產生三個根本衝突：

  1. **keyring 為 flat namespace**：`save_keys()` 以 `openclaw-gui / openai_api_key` 儲存，全域唯一。當多台伺服器需要不同 API key 時，後存覆蓋先存，無法區分。
  2. **API key 未寫入目標 `.env`**：`_step_write_env()` 只寫基礎設施變數（PORT, IMAGE 等），不寫 API key。架構文件 (202 §5) 明確描述「金鑰儲存於本機 keyring，初始化時寫入遠端 `.env`」，但此步驟從未實作。
  3. **`load_env_keys()` 只讀本機**：使用 `config_manager.read_env()` 讀取本機 `.env`，SSH 模式下無法讀取遠端伺服器的既有金鑰設定。

- **核心矛盾**：無論是否使用 keyring，API 金鑰最終都必須以明文出現在 `.env` 檔案中，供 Docker Compose (`env_file`) 或 systemd (`EnvironmentFile`) 讀取。keyring 僅為中間暫存層，未增加實際安全性：
  - **本機 Docker 模式**：`.env` 與 keyring 在同一台機器上，加密形同虛設。
  - **SSH 遠端模式**：遠端 `.env` 始終為明文，keyring 只保護了不需要保存金鑰的本機 GUI 電腦。

- **關鍵驅動因素 (Drivers)**:
  - 多機管理為真實使用場景（ADR-004 已確立）
  - 架構簡潔性：消除不增加實際安全價值的中間層（Good Taste）
  - 消除 keyring 在 headless Linux 上的依賴問題（`gnome-keyring` / `libsecret` 常缺失）
  - 消除 keyring 與 `.env` 之間的 key 大小寫轉換問題（`collectStep2Keys()` 用 `.toLowerCase()` 存入 keyring，`.env` 需要大寫）

## 2. 方案評估 (Options)

### 方案 1: 只用 .env（廢棄 keyring）

`.env` 為每台伺服器的唯一金鑰儲存。`save_keys()` 直接寫入目標機器的 `.env`，`load_env_keys()` 從目標機器的 `.env` 讀取。

```
使用者填寫 API Key → save_keys() → 目標機器 {config_dir}/.env
重新連線 → load_env_keys() → 讀取目標機器 .env → 回填 Step 2 表單
```

- **優點 (Pros)**: 一份 `.env` = 一台伺服器的完整設定，多機自然運作。架構最簡潔，無大小寫轉換、無 flat namespace 問題。移除 headless Linux 的 keyring 後端依賴。
- **缺點 (Cons)**: 金鑰以明文儲存於 `.env`，需依賴檔案權限（`chmod 600`）保護。需更新 CLAUDE.md、ADR-004、202、208 的安全規範描述。

### 方案 2: 保留 keyring + 補 .env 寫入

維持 keyring 儲存，補上「初始化時從 keyring 讀取 API key 寫入 .env」的缺口。keyring 作為暫存區，`.env` 為每台伺服器的 truth。

- **優點 (Pros)**: 不需改動安全規範文件。本機 GUI 電腦上金鑰有加密保護。
- **缺點 (Cons)**: 架構複雜度高（雙重儲存 + 同步）。flat namespace 問題未解決（多機切換時 keyring 被覆蓋）。大小寫轉換問題仍存在。keyring 的「安全」為假象（金鑰最終仍進入明文 `.env`）。

### 方案 3: 混合模式（本機 keyring + 遠端 .env）

本機 Docker 模式使用 keyring，SSH 遠端模式直接寫遠端 `.env`。

- **優點 (Pros)**: 本機模式保持加密儲存。
- **缺點 (Cons)**: 兩套路徑，需按模式分流。本機 Docker 模式的 keyring 加密仍無意義（同機器上的 `.env` 仍為明文）。增加維護與測試複雜度。

## 3. 決策結果 (Decision)

**選中方案**: 方案 1 — 只用 .env（廢棄 keyring）

**選擇理由**: keyring 作為中間層不增加實際安全價值（金鑰最終必須出現在 `.env` 明文中），卻引入了 flat namespace、大小寫轉換、headless 依賴等複雜度。廢棄 keyring 後，`.env` 成為每台伺服器的唯一 source of truth，多機管理場景自然運作，架構回歸簡潔。

**安全補償措施**:
- `.env` 檔案權限設為 `600`（僅 owner 可讀寫）
- GUI 寫入 `.env` 後立即設定權限（本機 `os.chmod()`，遠端 `executor.run_command(["chmod", "600", path])`）
- 前端 Security Note 更新為說明 `.env` 檔案權限保護機制

## 4. 後續影響 (Consequences)

- **正向影響**:
  - 架構簡化：消除 keyring ↔ .env 雙重儲存與同步邏輯
  - 多機管理自然運作：每台伺服器各有獨立 `.env`
  - 移除 `keyring` Python 套件依賴（或降級為 optional）
  - 消除 headless Linux 的 `gnome-keyring` / `libsecret` 依賴問題
  - 消除 key 大小寫轉換問題
  - `load_env_keys()` + `save_keys()` 統一讀寫 `.env`，資料流清晰
- **負向影響**:
  - 金鑰以明文儲存於 `.env`，安全性依賴檔案系統權限
  - 需更新多份文件的安全規範描述（CLAUDE.md, 202, 208, ADR-004）
  - 需重構 `config_manager.py`（移除 keyring 相關方法）、`bridge.py`（save_keys/load_env_keys 改寫 .env）
- **需更新的文件**:
  - `CLAUDE.md`：安全規範中 keyring 相關描述改為 .env + 檔案權限
  - `docs/202_architecture_design.md`：§2 NFR 安全性、§5 金鑰儲存資料流
  - `docs/208_frontend_specification.md`：§4.3 Step 2 Security Note、Bridge API 說明
  - `docs/adr/ADR-004_cloud_native_linux_deployment.md`：§keyring Fallback 策略更新引用
