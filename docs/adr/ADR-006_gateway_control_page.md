# 決策紀錄 (ADR-006): Gateway 控制頁面 — Origin 存取控制與裝置配對管理

---

**狀態:** `已接受 (Accepted)`
**日期:** `2026-03-25`

---

## 1. 脈絡與問題 (Context)

- **問題描述**: 初始化完成後，使用者面臨兩個管理需求無法透過 GUI 完成：

  1. **Origin 存取控制**：Gateway 的 `controlUi.allowedOrigins` 決定哪些 Origin 可存取 Control UI（Dashboard）。Docker 模式下，Gateway 容器看到的連線來自 Docker bridge 網路（非 loopback），loopback fallback 不生效，必須依靠 `allowedOrigins` 白名單。目前只能手動編輯 `openclaw.json` 來調整此設定。
  2. **裝置配對管理**：Gateway 使用 Device Pairing 機制進行身份驗證。`openclaw devices` CLI 提供 7 個子指令（list, approve, reject, remove, clear, rotate, revoke），但 GUI 只在初始化 Step 3 提供了基礎的 approve 功能，缺乏完整的裝置生命週期管理。

- **附加需求 — 裝置備註**：OpenClaw server 的 `displayName` 為唯讀（配對時由 client 設定，無 rename API）。使用者需要為裝置添加備註以便識別，必須在 GUI 本地儲存。

- **關鍵驅動因素 (Drivers)**:
  - 降低使用門檻：GUI 應覆蓋所有常用管理操作，避免使用者回到 CLI
  - Docker 模式下的 Origin 問題為真實痛點（已觸發 bug）
  - 裝置管理為日常維運必要操作（新增裝置、移除離線裝置）
  - 簡潔性：一個頁面集中所有 Gateway 相關設定

## 2. 方案評估 (Options)

### 方案 1: 新增獨立 "Gateway" 頁面（Sidebar MAIN 區段）

在 Sidebar MAIN 區段（Dashboard / Configuration / Environment）新增 "Gateway" 頁面入口，頁面包含 Origin Access Control 和 Device Management 兩個區塊。

- **優點 (Pros)**: 功能獨立，不汙染既有頁面。可持續擴展（未來加入 token rotate/revoke 等進階功能）。符合 SPA 頁面劃分慣例。
- **缺點 (Cons)**: 新增一個頁面入口，需修改 Sidebar 元件與路由。

### 方案 2: 併入 Dashboard 頁面的子區塊

在現有 Dashboard 頁面下方新增 "Gateway Settings" 和 "Device Management" 區塊。

- **優點 (Pros)**: 不新增頁面，Dashboard 成為集中管理面板。
- **缺點 (Cons)**: Dashboard 已有服務狀態、快速操作等區塊，再加兩個大區塊會過度擁擠。違反「一個頁面做一件事」原則。

### 方案 3: 放在 Configuration Step 3 的延伸

在初始化 Step 3 完成後，原地展開 Gateway 設定與裝置管理。

- **優點 (Pros)**: 流程連貫，初始化完直接設定。
- **缺點 (Cons)**: Configuration 是一次性精靈，不適合放日常維運功能。使用者不會為了管理裝置而重新進入初始化流程。

## 3. 決策結果 (Decision)

**選中方案**: 方案 1 — 新增獨立 "Gateway" 頁面

**選擇理由**: Gateway 的 Origin 存取控制和裝置管理是初始化後的持續維運操作，性質不同於一次性的初始化精靈（Configuration）或即時狀態監控（Dashboard）。獨立頁面保持每個頁面職責單一，也為未來的 token rotate/revoke 等進階功能預留空間。

### 實作策略

#### 頁面結構

| 區塊 | 功能 | 資料來源 |
|:---|:---|:---|
| Origin Access Control | 全域允許 (`*`) / 白名單切換 + 白名單編輯 | `openclaw.json` → `gateway.controlUi.allowedOrigins` |
| Device Management — Pending | 待核准裝置列表 + Approve / Reject | `openclaw devices list --json` → `pending[]` |
| Device Management — Paired | 已配對裝置列表 + 備註 + Remove | `openclaw devices list --json` → `paired[]` |

#### Bridge API 新增方法

| 方法 | 功能 | 實作方式 |
|:---|:---|:---|
| `get_allowed_origins()` | 讀取 allowedOrigins | `config_manager.read_openclaw_config()` |
| `save_allowed_origins(params)` | 寫入 allowedOrigins | `config_manager.write_openclaw_config()` |
| `list_devices()` | 列出所有裝置（pending + paired） | `_build_openclaw_cmd(["devices", "list", "--json"])` |
| `reject_device(params)` | 拒絕 pending 裝置 | `_build_openclaw_cmd(["devices", "reject", requestId])` |
| `remove_device(params)` | 移除 paired 裝置 | `_build_openclaw_cmd(["devices", "remove", deviceId])` |
| `save_device_note(params)` | 儲存裝置備註 | `gui-settings.json` → `device_notes` |
| `get_device_notes()` | 讀取裝置備註 | `gui-settings.json` → `device_notes` |

#### 裝置備註儲存

由於 OpenClaw server 無 displayName 修改 API，備註存於 GUI 本地設定：

```json
// gui-settings.json
{
  "device_notes": {
    "device-id-abc": "辦公室桌機",
    "device-id-xyz": "測試用手機"
  }
}
```

## 4. 後續影響 (Consequences)

- **正向影響**:
  - GUI 完整覆蓋 Gateway Origin 和裝置管理的常用操作
  - 消除 Docker 模式下 Origin 設定的手動編輯需求
  - 裝置備註提升多裝置環境的可辨識性
  - 為 token rotate/revoke 等進階功能預留擴展空間
- **負向影響**:
  - 裝置備註僅存於本地 GUI 設定，換機器或重裝後需重新標記
  - 新增一個 Sidebar 入口，需同步更新 pencil 設計文件與前端規格書
- **需更新的文件**:
  - `docs/208_frontend_specification.md`：新增 §5.x Gateway 頁面規格
  - `docs/pencil-new.pen`：新增 Gateway 頁面設計 mockup
  - `docs/202_architecture_design.md`：L3 元件圖新增 Gateway 頁面
