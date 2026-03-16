# Claude Code Skill 建置方法研究報告

> 版本：v1.0
> 最後更新：2026-03-16

---

## 1. 什麼是 Claude Code Skill

Claude Code Skill 是 Claude Code CLI 工具的可重複使用指令集。每個 Skill 是一個 Markdown 檔案，包含 YAML 前言（frontmatter）定義後設資料，以及 Markdown 本文作為 Claude 的執行指令。

Skill 讓你可以將常見工作流程封裝成一個斜線命令（如 `/calendar-booking`），使用者輸入該命令即可觸發預定義的行為。

**核心概念**：Skill = 前言後設資料 + Markdown 執行指令 + 支援檔案

---

## 2. 檔案結構

Claude Code Skill 的標準路徑為：

```
.claude/skills/<skill-name>/SKILL.md
```

完整範例：

```
.claude/
└── skills/
    ├── calendar-booking/
    │   ├── SKILL.md              ← 主檔（必要）
    │   ├── booking-rules.md      ← 支援檔案（選用）
    │   └── response-templates.md ← 支援檔案（選用）
    └── install-booking/
        └── SKILL.md
```

- 每個 Skill 目錄下必須有一個 `SKILL.md` 作為進入點
- 支援檔案放在同一目錄下，透過相對路徑引用
- 目錄名稱即為 Skill 的斜線命令名稱（如 `calendar-booking` → `/calendar-booking`）

---

## 3. YAML Frontmatter 欄位詳解

SKILL.md 開頭必須包含 YAML 前言區塊（以 `---` 包圍）：

| 欄位 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `name` | string | 是 | — | Skill 的顯示名稱，用於 `/` 選單 |
| `description` | string | 是 | — | Skill 的描述，Claude 根據此判斷是否自動觸發 |
| `argument-hint` | string | 否 | — | 在 `/` 選單中顯示的參數提示，如 `[預約需求]` |
| `disable-model-invocation` | boolean | 否 | `false` | 設為 `true` 時，Claude 不會自動觸發此 Skill，僅能手動 `/` 呼叫 |
| `user-invocable` | boolean | 否 | `true` | 設為 `false` 時，此 Skill 不出現在 `/` 選單中（僅供其他 Skill 引用） |
| `allowed-tools` | string | 否 | 全部工具 | 限制此 Skill 可使用的工具，以逗號分隔，如 `Read, Grep, Glob` |
| `model` | string | 否 | 繼承父層 | 指定此 Skill 使用的模型，如 `sonnet`、`haiku` |
| `context` | list | 否 | — | 額外注入的上下文檔案路徑 |
| `agent` | object | 否 | — | 啟用 fork agent 模式時的設定 |
| `hooks` | object | 否 | — | Skill 執行前/後的 shell hook 命令 |

### 範例前言

```yaml
---
name: calendar-booking
description: "預約管理助理 — 解析自然語言預約需求、查詢空檔、建立事件。"
argument-hint: "[預約需求，例：我想約下週三下午]"
allowed-tools: Read, Grep, Glob, Bash
---
```

---

## 4. Markdown 本文 = Claude 執行指令

前言之後的所有 Markdown 內容就是 Claude 收到的 system-level 指令。你可以在此定義：

- **角色定義**：你是誰、你的職責
- **工作流程**：逐步執行的步驟
- **限制條件**：不能做的事
- **輸出格式**：回覆模板

```markdown
---
name: example-skill
description: "範例技能"
---

你是一個專業的預約助理。

## 工作流程

1. 解析用戶的預約需求
2. 查詢可用時段
3. 推薦時段供選擇
4. 建立事件並回覆確認

## 限制

- 不能刪除現有事件
- 只能操作指定的行事曆
```

---

## 5. 動態功能

### 5.1 支援檔案引用

使用 Markdown 連結語法引用同目錄下的檔案，被引用的檔案內容會自動注入 Claude 的上下文：

```markdown
請參考以下規則：
[booking-rules.md](booking-rules.md)

以下是回覆模板：
[response-templates.md](response-templates.md)
```

- 路徑相對於 SKILL.md 所在目錄
- 引用的檔案內容會在 Skill 載入時一併送入 Claude
- 適合用於：規則清單、模板、參考資料等靜態內容

### 5.2 動態注入

使用反引號包裹的 `!` 前綴命令，Skill 載入時會執行該命令並將輸出注入：

```markdown
以下是目前的商業設定：

!`cat module_pack/module_01_booking/calendar_fields.json`
```

- 命令在 Skill 載入時執行，輸出替換到該位置
- 適合用於：讀取 JSON 設定檔、取得動態資料、環境資訊
- 注意：命令執行發生在 Skill 載入階段，而非對話過程中

### 5.3 變數

| 變數 | 說明 | 範例 |
|------|------|------|
| `$ARGUMENTS` | 使用者在 `/skill-name` 後輸入的全部文字 | `/booking 下週三下午` → `$ARGUMENTS` = `下週三下午` |
| `$0` | 同 `$ARGUMENTS`，用於簡短引用 | — |
| `${CLAUDE_SKILL_DIR}` | 目前 Skill 的目錄絕對路徑 | `/home/user/project/.claude/skills/calendar-booking` |

```markdown
用戶的預約需求是：$ARGUMENTS

請讀取設定檔：
!`cat ${CLAUDE_SKILL_DIR}/../../module_pack/module_01_booking/calendar_fields.json`
```

---

## 6. Scope 層級

Claude Code Skill 有三個作用範圍：

| 層級 | 路徑 | 說明 | 適用場景 |
|------|------|------|---------|
| **Personal** | `~/.claude/skills/` | 個人層級，僅自己可用 | 個人工具、快捷操作 |
| **Project** | `<project>/.claude/skills/` | 專案層級，所有協作者共用 | 專案特定工作流程 |
| **Enterprise** | 由組織管理員設定 | 組織層級，所有成員共用 | 公司標準流程 |

**優先順序**：Enterprise > Project > Personal（同名 Skill 以高層級為準）

對於 OpenClaw 專案，我們使用 **Project** 層級（`.claude/skills/`），讓所有使用此專案的人都能存取相同的 Skill。

---

## 7. 觸發模式

### 手動觸發（`/skill-name`）

使用者在 Claude Code 中輸入斜線命令即可觸發：

```
> /calendar-booking 我想約下週三下午
```

- 出現在 Claude Code 的 `/` 自動完成選單中
- `argument-hint` 會顯示在選單中作為參數提示
- 設定 `disable-model-invocation: true` 可確保僅能手動觸發

### 自動觸發

當 `disable-model-invocation` 為 `false`（預設）時，Claude 會根據 `description` 欄位判斷用戶意圖，自動觸發匹配的 Skill。

例如，description 包含「預約」「book」「schedule」等關鍵字時，用戶說「我想約個時間」就可能自動觸發。

**建議**：對於有副作用的 Skill（如寫入資料、建立事件），建議設定 `disable-model-invocation: true` 以避免誤觸發。

---

## 8. 實作範例

### 範例 1：簡單 Skill — 程式碼審查

```markdown
---
name: code-review
description: "審查目前 git diff 的程式碼變更，提供改進建議。"
argument-hint: "[可選：關注的檔案或主題]"
allowed-tools: Read, Grep, Glob, Bash
---

你是一位資深程式碼審查員。請審查目前的程式碼變更。

## 步驟

1. 執行 `git diff` 查看所有變更
2. 逐一檢查每個變更檔案
3. 針對以下面向提供建議：
   - 程式碼品質與可讀性
   - 潛在 bug 或邊界情況
   - 效能考量
   - 安全性問題

## 輸出格式

每個問題用以下格式回報：
- **檔案**：`path/to/file.ts:行號`
- **嚴重度**：🔴 高 / 🟡 中 / 🟢 低
- **描述**：問題說明
- **建議**：改進方式
```

### 範例 2：帶動態注入 — 部署檢查

```markdown
---
name: deploy-check
description: "部署前環境檢查 — 驗證所有環境變數與服務狀態。"
disable-model-invocation: true
allowed-tools: Read, Bash
---

你是部署前檢查助理。請驗證以下項目。

## 目前環境設定

!`cat .env | grep -v "^#" | grep -v "^$"`

## 目前 Docker 服務狀態

!`docker compose ps 2>/dev/null || echo "Docker Compose 未運行"`

## 檢查項目

1. 確認所有必要的環境變數已設定（不為空）
2. 確認 Docker 服務全部為 running 狀態
3. 確認 API 端點可連線
4. 產出檢查報告，標示通過/未通過項目
```

### 範例 3：帶 Fork Agent — 平行研究

```markdown
---
name: research
description: "針對技術問題進行平行研究，彙整為結構化報告。"
argument-hint: "[研究主題]"
agent:
  type: fork
  count: 3
allowed-tools: Read, Grep, Glob, WebSearch, WebFetch
---

你是一位技術研究員。用戶想研究：$ARGUMENTS

## 工作方式

你將被 fork 成 3 個平行 agent：
1. Agent 1：搜尋官方文件與 API 文檔
2. Agent 2：搜尋社群討論、部落格、Stack Overflow
3. Agent 3：搜尋程式碼範例與最佳實踐

## 輸出格式

每個 agent 產出後，合併為一份報告：
- **摘要**：一段話總結
- **關鍵發現**：3-5 個重點
- **程式碼範例**：可直接使用的範例
- **參考連結**：來源列表
```

---

## 9. Claude Code Skill 與 OpenClaw Skill 比較對照表

| 面向 | Claude Code Skill | OpenClaw Skill |
|------|-------------------|----------------|
| **定義格式** | 單一 SKILL.md（Markdown + YAML 前言） | 三層架構：`*_fields.json` + `*_skill.md` + `*_prompt.md` |
| **存放位置** | `.claude/skills/<name>/SKILL.md` | `module_pack/module_XX_<category>/` |
| **觸發方式** | `/skill-name` 斜線命令或自動觸發 | 透過 OpenClaw 對話意圖辨識 |
| **設定方式** | 直接在 SKILL.md 中撰寫指令 | JSON 設定檔分離商業欄位與技術參數 |
| **動態功能** | `!`command`` 動態注入、檔案引用 | 由 OpenClaw runtime 處理參數注入 |
| **變數系統** | `$ARGUMENTS`、`${CLAUDE_SKILL_DIR}` | JSON 欄位 + prompt placeholder `{variable}` |
| **執行環境** | Claude Code CLI（本地終端機） | OpenClaw 平台（Docker 容器） |
| **適用對象** | 開發者、講師（Vibe Coding） | 終端使用者（學員、客戶） |
| **權限控制** | `allowed-tools` 限制工具存取 | API Scope 白名單 + 最小權限 |
| **安裝方式** | 放入 `.claude/skills/` 目錄即可 | `/install-xxx` 命令自動設定 |
| **生態系** | 專案內部共享 | ClawHub 市集（需白名單審核） |
| **協作角色** | 講師用來建置和維護模組 | 學員透過 OpenClaw 入口使用 |

### 兩者如何協作

```
Claude Code Skill（講師端）         OpenClaw Skill（學員端）
        │                                    │
  /install-booking                    對話：「我想約時間」
        │                                    │
        ▼                                    ▼
  讀取表單 → 更新 JSON              OpenClaw 辨識意圖
  → 更新 Prompt 模板                → 呼叫 calendar_booking skill
  → 產出確認報告                    → 查空檔 → 建事件 → 回覆
```

Claude Code Skill 是**建置工具**（講師用），OpenClaw Skill 是**執行工具**（學員用）。兩者互補而非競爭。
