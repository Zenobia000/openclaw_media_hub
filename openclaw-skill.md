# OpenClaw Skill 建置需求與規格文件

> **版本**: 1.0  
> **日期**: 2026-03-17  
> **狀態**: 初版

---

## 目錄

1. [概述](#1-概述)
2. [Skill 是什麼](#2-skill-是什麼)
3. [目錄結構規格](#3-目錄結構規格)
4. [SKILL.md 規格](#4-skillmd-規格)
5. [Bundled Resources 規格](#5-bundled-resources-規格)
6. [設計原則](#6-設計原則)
7. [建置流程](#7-建置流程)
8. [命名規範](#8-命名規範)
9. [Metadata 擴充欄位](#9-metadata-擴充欄位)
10. [打包與發佈](#10-打包與發佈)
11. [範例 Skill 結構](#11-範例-skill-結構)
12. [檢查清單](#12-檢查清單)

---

## 1. 概述

OpenClaw Skill 是模組化、自包含的知識與工具套件，用於擴展 OpenClaw Agent 的能力。每個 Skill 相當於一份針對特定領域的「上手指南」，將通用 Agent 轉化為具備專業程序知識的特化 Agent。

**本文件目的**：提供完整的 Skill 建置需求與規格，作為開發新 Skill 的參考標準。

---

## 2. Skill 是什麼

### 2.1 Skill 提供的能力

| 類型           | 說明                                  | 範例                        |
| -------------- | ------------------------------------- | --------------------------- |
| **專業工作流** | 特定領域的多步驟程序                  | PDF 編輯、GitHub Issue 處理 |
| **工具整合**   | 特定 CLI / API 的操作指引             | `gh` CLI、Notion API        |
| **領域知識**   | 公司/產品特有的知識、Schema、業務邏輯 | BigQuery Schema、品牌指南   |
| **捆綁資源**   | 腳本、參考文件、範本資產              | Python 腳本、HTML 模板      |

### 2.2 運作機制（三層漸進載入）

```
Level 1: Metadata（name + description）  → 始終在 context 中（~100 words）
Level 2: SKILL.md body                    → 觸發後才載入（< 5k words）
Level 3: Bundled resources                → 按需載入（無上限）
```

Agent 僅在 **description 匹配使用者意圖** 時才載入 SKILL.md body，再視需要載入 scripts / references / assets。

---

## 3. 目錄結構規格

```
skill-name/                    # 目錄名 = skill 名稱（小寫 + 連字號）
├── SKILL.md                   # [必要] 前置 YAML + Markdown 指引
├── scripts/                   # [選填] 可執行腳本（Python / Bash 等）
│   └── rotate_pdf.py
├── references/                # [選填] 參考文件，按需載入 context
│   └── schema.md
└── assets/                    # [選填] 輸出用資產（模板、圖片、字型等）
    └── template/
```

### 3.1 禁止包含的檔案

| 不要建立              | 原因                             |
| --------------------- | -------------------------------- |
| README.md             | Skill 不需使用者文件             |
| INSTALLATION_GUIDE.md | 安裝由 metadata 處理             |
| CHANGELOG.md          | 不需版本紀錄                     |
| QUICK_REFERENCE.md    | 資訊應在 SKILL.md 或 references/ |

---

## 4. SKILL.md 規格

### 4.1 YAML Frontmatter（必要）

```yaml
---
name: skill-name # [必要] 與目錄名一致
description: > # [必要] 觸發描述 — 決定何時使用
  簡要說明做什麼 + 具體觸發條件。
  包含所有「何時使用」的資訊。
  body 載入前 Agent 只看得到這裡。
---
```

**description 寫作要點**：

- 說明 Skill 做什麼（功能）
- 說明何時使用（觸發條件）
- 說明何時不用（排除條件）
- 所有 "When to Use" 資訊都放這裡，**不要放在 body 中**

**選填 metadata 欄位**（OpenClaw 擴充，放在 frontmatter 或獨立 `metadata:` 區塊中）：

```yaml
homepage: https://example.com
metadata:
  openclaw:
    emoji: "🔧"
    os: ["darwin", "linux"] # 限定作業系統
    requires:
      bins: ["tool-name"] # 必須存在的 CLI
      anyBins: ["tool-a", "tool-b"] # 其中一個存在即可
      env: ["API_KEY"] # 必須有的環境變數
      config: ["channels.slack"] # 必須有的 OpenClaw config
    primaryEnv: "API_KEY" # 主要環境變數（用於設定引導）
    install: # 安裝指引
      - id: "brew"
        kind: "brew"
        formula: "tool-name"
        bins: ["tool-name"]
        label: "Install tool (brew)"
```

### 4.2 Markdown Body

- 使用**祈使語氣**撰寫（"Extract text..." 而非 "You should extract text..."）
- 控制在 **500 行以內**
- 只寫 Agent 不知道的資訊；假設 Agent 已經很聰明
- 大量細節拆分到 `references/` 中

### 4.3 Body 組織模式

| 模式                     | 適用場景         | 結構                                                 |
| ------------------------ | ---------------- | ---------------------------------------------------- |
| **Workflow-Based**       | 有明確步驟的流程 | Overview → Decision Tree → Step 1 → Step 2           |
| **Task-Based**           | 提供多種操作     | Overview → Quick Start → Task 1 → Task 2             |
| **Reference/Guidelines** | 標準或規範       | Overview → Guidelines → Specifications               |
| **Capabilities-Based**   | 多功能整合       | Overview → Core Capabilities → Feature 1 → Feature 2 |

---

## 5. Bundled Resources 規格

### 5.1 scripts/（腳本）

- **用途**：需要確定性結果、或同樣程式碼重複撰寫的任務
- **特性**：Token 高效、可不載入 context 直接執行
- **要求**：建立後必須實際執行測試
- **範例**：`scripts/rotate_pdf.py`、`scripts/deploy.sh`

### 5.2 references/（參考文件）

- **用途**：Agent 工作時按需查閱的文件
- **特性**：保持 SKILL.md 精簡，僅需要時載入
- **要求**：
  - 超過 100 行時，頂部加目錄
  - 超過 10k words 時，在 SKILL.md 中提供 grep 搜尋模式
  - 與 SKILL.md **不重複**：詳細資訊放 references，核心流程放 SKILL.md
  - 只保持一層深度（從 SKILL.md 直接連結）
- **範例**：`references/api_docs.md`、`references/schema.md`

### 5.3 assets/（資產）

- **用途**：不載入 context，用於最終輸出的檔案
- **範例**：`assets/logo.png`、`assets/template.pptx`、`assets/frontend-template/`

---

## 6. 設計原則

### 6.1 精簡為王

Context window 是共用資源。每一段文字都要問：

- Agent 是否真的需要這個解釋？
- 這段的 token 成本是否值得？

**偏好簡潔範例而非冗長解釋。**

### 6.2 適當的自由度

| 自由度 | 形式              | 適用場景                     |
| ------ | ----------------- | ---------------------------- |
| **高** | 文字指引          | 多種方法都可、需依情境判斷   |
| **中** | 偽碼 / 帶參數腳本 | 有偏好模式但允許變化         |
| **低** | 具體腳本、少參數  | 操作脆弱、需一致性、特定順序 |

### 6.3 漸進揭露

```
SKILL.md 引用 → references/aws.md     （使用者選 AWS 才載入）
SKILL.md 引用 → references/gcp.md     （使用者選 GCP 才載入）
SKILL.md 引用 → references/azure.md   （使用者選 Azure 才載入）
```

**永遠在 SKILL.md 中清楚描述每個 reference 檔案的存在與載入時機。**

---

## 7. 建置流程

### Step 1：理解需求（釐清具體使用範例）

- Skill 支援哪些功能？
- 使用者會怎麼觸發？（具體句子）
- 有哪些邊界條件或排除場景？

### Step 2：規劃可複用內容

分析每個使用範例，識別：

- 哪些程式碼會重複撰寫 → `scripts/`
- 哪些知識需要按需查閱 → `references/`
- 哪些檔案用於輸出 → `assets/`

### Step 3：初始化 Skill

```bash
# 從 skill-creator 的 scripts 目錄執行
python3 /app/skills/skill-creator/scripts/init_skill.py <skill-name> \
  --path <output-directory> \
  [--resources scripts,references,assets] \
  [--examples]
```

### Step 4：編輯實作

1. 先實作 scripts / references / assets
2. 測試所有腳本（至少代表性樣本）
3. 撰寫 SKILL.md（frontmatter + body）
4. 刪除不需要的 placeholder 檔案

### Step 5：打包

```bash
python3 /app/skills/skill-creator/scripts/package_skill.py <path/to/skill-folder> [output-dir]
```

打包器自動驗證：

- YAML frontmatter 格式與必要欄位
- 命名規範與目錄結構
- description 完整性與品質
- 檔案組織與資源引用
- **拒絕 symlinks**

產出 `<skill-name>.skill` 檔（本質為 `.zip`）。

### Step 6：迭代

實際使用 → 發現問題 → 改進 → 重新打包。

---

## 8. 命名規範

| 規則                     | 範例                                 |
| ------------------------ | ------------------------------------ |
| 僅小寫字母、數字、連字號 | `pdf-editor` ✅ / `PDF_Editor` ❌    |
| 64 字元以內              | —                                    |
| 動詞導向，描述動作       | `gh-address-comments`                |
| 工具前綴增加辨識度       | `nano-pdf`、`openai-whisper`         |
| 目錄名 = skill name      | `weather/SKILL.md` → `name: weather` |

---

## 9. Metadata 擴充欄位

OpenClaw 透過 `metadata.openclaw` 提供以下擴充能力：

| 欄位               | 類型     | 說明                                               |
| ------------------ | -------- | -------------------------------------------------- |
| `emoji`            | string   | Skill 識別 emoji                                   |
| `os`               | string[] | 限定 OS：`darwin`, `linux`, `win32`                |
| `requires.bins`    | string[] | 所有必須存在的 CLI                                 |
| `requires.anyBins` | string[] | 至少一個存在的 CLI                                 |
| `requires.env`     | string[] | 必須設定的環境變數                                 |
| `requires.config`  | string[] | 必須存在的 OpenClaw config 路徑                    |
| `primaryEnv`       | string   | 主要環境變數（設定引導用）                         |
| `install`          | object[] | 安裝指引（kind: brew / node / go / uv / download） |
| `skillKey`         | string   | 自訂 skill key（若與 name 不同）                   |

### Install 物件結構

```yaml
- id: "brew" # 唯一識別
  kind: "brew" # 安裝方式：brew | node | go | uv | download
  formula: "tool-name" # brew formula / npm package / go module
  bins: ["tool-name"] # 安裝後產生的執行檔
  label: "Install tool (brew)" # 人類可讀說明
  # download 專用欄位：
  url: "https://..."
  archive: "tar.bz2"
  extract: true
  stripComponents: 1
```

---

## 10. 打包與發佈

### 10.1 打包格式

- `.skill` 檔案 = ZIP 格式，副檔名為 `.skill`
- 包含完整目錄結構
- 不允許 symlinks

### 10.2 發佈管道

- **ClawHub**（`clawhub.com`）：官方 Skill 市集
  - `clawhub publish <path/to/skill-folder>` 發佈
  - `clawhub install <skill-name>` 安裝
  - `clawhub update` 更新已安裝 Skill

### 10.3 本機安裝

Skill 安裝至 `/app/skills/<skill-name>/` 或使用者自訂路徑。

---

## 11. 範例 Skill 結構

### 範例 A：CLI 工具整合（weather）

```
weather/
├── SKILL.md
```

```yaml
---
name: weather
description: "Get current weather and forecasts via wttr.in or Open-Meteo.
  Use when: user asks about weather, temperature, or forecasts for any location.
  NOT for: historical weather data, severe weather alerts, or detailed meteorological analysis.
  No API key needed."
homepage: https://wttr.in/:help
metadata: { "openclaw": { "emoji": "☔", "requires": { "bins": ["curl"] } } }
---
```

### 範例 B：帶腳本的多功能 Skill

```
pdf-editor/
├── SKILL.md
├── scripts/
│   ├── rotate_pdf.py
│   └── merge_pdf.py
└── references/
    └── api_reference.md
```

### 範例 C：多域參考文件 Skill

```
bigquery/
├── SKILL.md
└── references/
    ├── finance.md
    ├── sales.md
    ├── product.md
    └── marketing.md
```

### 範例 D：帶資產模板的 Skill

```
frontend-webapp-builder/
├── SKILL.md
└── assets/
    └── hello-world/
        ├── index.html
        ├── style.css
        └── app.js
```

---

## 12. 檢查清單

建置完成前，逐項確認：

### 結構

- [ ] 目錄名符合命名規範（小寫 + 連字號 + ≤64 字元）
- [ ] `SKILL.md` 存在且位於根目錄
- [ ] 無多餘文件（README.md, CHANGELOG.md 等）
- [ ] 無 symlinks

### Frontmatter

- [ ] `name` 與目錄名一致
- [ ] `description` 包含功能說明 + 觸發條件 + 排除條件
- [ ] 無多餘自訂 YAML 欄位（僅 `name`, `description`, 選填 `homepage`, `metadata`）

### Body

- [ ] ≤ 500 行
- [ ] 使用祈使語氣
- [ ] 不重複 description 中已有的 "When to Use" 資訊
- [ ] 每個 references 檔案都在 body 中被引用並說明載入時機
- [ ] 僅包含 Agent 不會自然知道的資訊

### Resources

- [ ] 所有 scripts 已實際測試
- [ ] references 超過 100 行有目錄
- [ ] references 與 SKILL.md 無重複內容
- [ ] assets 僅包含輸出用檔案

### 打包

- [ ] `package_skill.py` 驗證通過
- [ ] 產出的 `.skill` 檔可正常使用

---

_文件完成。如需建置特定 Skill，可依此規格開始開發。_
