# OpenClaw Skill 建置方法研究報告

> 版本：v1.0
> 最後更新：2026-03-16

---

## 1. OpenClaw Skill 架構概述

OpenClaw Skill 是 OpenClaw 平台的自動化工作單元。每個 Skill 封裝一個完整的業務流程（如預約管理、Email 分類、CRM 寫入），由 OpenClaw 的對話引擎根據用戶意圖觸發。

**設計哲學**：學員填表單、講師用 Claude Code 部署、OpenClaw 執行。學員永遠不需要接觸技術檔案。

---

## 2. 三層架構

OpenClaw Skill 採用嚴格的三層分離設計：

```
設定層（Config）         邏輯層（Skill Spec）        表現層（Prompt）
*_fields.json    →    *_skill.md             →    *_prompt.md

商業欄位               功能規格                     使用者看到的回覆
只有學員需要填的        10 大章節                    System Prompt
不含技術參數           定義觸發、流程、限制           回覆模板 + 邊界處理
```

### 各層職責

| 層級 | 檔案命名慣例 | 維護者 | 內容 |
|------|-------------|--------|------|
| **設定層** | `*_fields.json` | 學員（透過表單） | 商業欄位：店名、營業時間、服務項目 |
| **邏輯層** | `*_skill.md` | 講師 / 開發者 | Skill 規格書：觸發條件、工作流程、API 依賴、安全限制 |
| **表現層** | `*_prompt.md` | 講師 / 開發者 | Prompt 模板：System Prompt、回覆格式、邊界處理 |

### 為什麼要三層分離？

1. **學員只碰設定層**：改 JSON 欄位，不碰 Markdown
2. **邏輯和表現獨立迭代**：改流程不影響回覆格式，改回覆格式不影響流程
3. **Claude Code 可自動化**：讀取設定層 → 更新邏輯層和表現層的 placeholder

---

## 3. 目錄命名規範

```
module_pack/
├── module_pack_spec.md                    ← 模組包總規格書
├── config/                                ← 全域設定
│   ├── business_profile_form.md           ← 學員商業設定表單
│   └── best_practices.md                  ← 最佳實務指南
├── module_01_booking/                     ← 預約模組
│   ├── calendar_booking_skill.md          ← 邏輯層
│   ├── calendar_confirmation_prompt.md    ← 表現層
│   └── calendar_fields.json              ← 設定層
├── module_02_email/                       ← Email 收發模組
│   ├── email_triage_skill.md
│   ├── email_reply_draft_skill.md
│   ├── reply_style_claude.md
│   └── gmail_scope_minimal.json
├── module_03_crm/                         ← CRM 模組
│   ├── lead_capture_skill.md
│   ├── lead_score_rules.md
│   ├── notion_crm_database_template.md
│   └── sheets_crm_template.md
├── module_04_customer_service/            ← 客服模組
│   ├── faq_responder_skill.md
│   ├── escalation_rules.md
│   └── channel_setup_guide.md
├── module_05_report/                      ← 日報週報模組
│   ├── daily_brief_skill.md
│   ├── weekly_report_skill.md
│   ├── report_prompt_pack.md
│   └── report_output_schema.json
├── module_06_notification/                ← 通知模組
│   ├── scheduled_notify_skill.md
│   ├── notification_rules.md
│   └── cron_config_template.md
└── troubleshooting/                       ← 故障排除 SOP
    └── troubleshooting_sop.md
```

### 命名規則

- **目錄**：`module_XX_<category>/`，XX 為兩位數編號
- **設定檔**：`<功能>_fields.json` — 只含商業欄位
- **規格檔**：`<功能>_skill.md` — 完整 Skill 規格
- **模板檔**：`<功能>_prompt.md` — Prompt 模板與回覆格式
- **輔助檔**：描述性名稱，如 `escalation_rules.md`、`lead_score_rules.md`

---

## 4. Skill 規格文件 10 大章節詳解

以 `calendar_booking_skill.md` 為範例，每個 Skill 規格文件包含以下 10 個章節：

### Section 1：基本資訊

定義 Skill 的身份識別資訊。

| 欄位 | 說明 | 範例 |
|------|------|------|
| Skill Name | Skill 的內部名稱 | `calendar_booking` |
| Skill ID | 全域唯一識別碼 | `mod01_calendar_booking` |
| Category | 功能分類 | Scheduling / Booking |
| Status | 版本狀態 | v1 — 最小可行版 |
| Author | 作者 | Sunny Data Science |

### Section 2：功能描述

用自然語言描述 Skill 的完整功能，並附上流程圖：

```
用戶：「我想約下週三下午」
  → Step 1：解析意圖
  → Step 2：提取參數
  → Step 3：查詢空檔
  → Step 4：推薦時段
  → Step 5：用戶確認
  → Step 6：建立事件
  → Step 7：回覆確認
  → Step 8：寫入 CRM
```

### Section 3：觸發條件

定義三種觸發邏輯：

1. **關鍵字觸發**：明確的觸發詞列表（支援多語言）
   - 繁中：`預約`、`約時間`、`排時間`
   - 英文：`book`、`schedule`、`appointment`
2. **意圖觸發**：AI 判斷用戶意圖為「安排時間」時觸發
3. **不觸發的情況**：明確列出不應觸發的場景（避免誤觸發）

### Section 4：輸入參數

定義 Skill 接收的所有參數：

| 欄位 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `date` | string/date | 否 | — | 自然語言日期 |
| `time` | string/time | 否 | — | 模糊時間表達 |
| `duration` | integer | 否 | 設定檔預設值 | 預約時長（分鐘） |

附帶**參數解析規則**：缺少哪個參數時如何處理。

### Section 5：輸出

定義成功回應的格式和寫入 CRM 的資料結構。包含：
- 確認訊息的欄位與範例
- CRM 寫入的 JSON 結構

### Section 6：API 依賴

列出所有使用的 API 及其 Scope：

| API | Scope | 用途 | 權限等級 |
|-----|-------|------|---------|
| Google Calendar API | `calendar.events.readonly` | 查詢空檔 | 唯讀 |
| Google Calendar API | `calendar.events` | 建立事件 | 寫入 |

同時列出**明確不使用的 Scope** 及理由，落實最小權限原則。

### Section 7：安全限制

分為兩類：

- **硬性限制**（不可變更）：如「只能建立事件、不能刪除」
- **軟性限制**（可在客製版調整）：如「每日預約上限」

### Section 8：第一版範圍（v1 Scope）

明確列出 v1 包含和不包含的功能，避免範圍蔓延：

- **包含**：解析日期、查空檔、建事件、回覆確認、寫入 CRM
- **不包含**（v2 再做）：改期、取消、多人同步、重複預約、自動提醒

### Section 9：錯誤處理

逐一列出可能的錯誤情況及對應的回應策略：

| 錯誤情況 | 回應策略 |
|----------|---------|
| 時間已被佔用 | 列出最近 3 個可用時段 |
| 日期不在營業日 | 告知營業日，推薦最近營業日 |
| API 連線失敗 | 告知稍後再試，記錄錯誤 |

### Section 10：設定檔依賴

指向該 Skill 依賴的 JSON 設定檔，確保設定與邏輯的連結明確。

---

## 5. Config JSON 設計模式

### 核心原則：只含商業欄位，不含技術參數

```json
{
  "business_name": "",
  "calendar_id": "primary",
  "available_days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
  "available_hours": {
    "start": "09:00",
    "end": "18:00"
  },
  "default_duration_minutes": 60,
  "booking_buffer_minutes": 15,
  "event_title_format": "{business_name} - {client_name} 預約",
  "timezone": "Asia/Taipei",
  "notification_target": "telegram",
  "confirmation_language": "zh-TW"
}
```

### 設計規則

| 規則 | 說明 | 正確範例 | 錯誤範例 |
|------|------|---------|---------|
| 只有商業欄位 | 不暴露 API Key、endpoint 等技術細節 | `"business_name": ""` | `"api_key": "sk-xxx"` |
| 欄位名稱自解釋 | 不需要額外說明 | `"available_days"` | `"param_1"` |
| 有合理預設值 | 減少必填項 | `"default_duration_minutes": 60` | `"duration": null` |
| 使用 placeholder 格式 | 方便 Prompt 模板注入 | `"{business_name} - {client_name}"` | 寫死的字串 |

### 設定檔與其他層的關係

```
calendar_fields.json（設定層）
    │
    ├──→ calendar_booking_skill.md 引用預設值
    │    「時長未指定：使用 default_duration_minutes」
    │
    └──→ calendar_confirmation_prompt.md 引用 placeholder
         「你是 {business_name} 的預約助理」
```

---

## 6. Prompt 模板設計模式

### 6.1 System Prompt

定義 AI 助理的角色和行為準則：

```
你是 {business_name} 的預約助理。你的唯一職責是協助客戶預約時間。

你的行為準則：
- 友善、簡潔、專業
- 一次只問一個問題
- 確認資訊時用條列格式
- 絕不回答與預約無關的問題
- 所有時間以 {timezone} 為準

你可以存取的資料：
- 營業日：{available_days}
- 營業時段：{available_hours.start} - {available_hours.end}

你不能做的事：
- 刪除或修改已存在的行事曆事件
- 存取指定行事曆以外的日曆
- 在營業時段外建立預約
```

### 6.2 回覆模板

每種回覆情境都有對應模板，使用 `{variable}` placeholder：

- **推薦時段模板**：列出可用時段供選擇
- **預約確認模板**：事件建立後的確認訊息
- **預約前確認模板**：建立前的最終確認

### 6.3 多語言支援

由 `confirmation_language` 欄位控制：

| 語言代碼 | 語言 | 日期格式 |
|----------|------|---------|
| `zh-TW` | 繁體中文（預設） | 2026年3月15日 |
| `zh-CN` | 簡體中文 | 2026年3月15日 |
| `en` | English | March 15, 2026 |
| `ja` | 日本語 | 2026年3月15日 |

切換邏輯：
1. 優先使用 `confirmation_language` 設定值
2. 如用戶以其他語言對話，自動切換
3. 日期格式跟隨語言設定

### 6.4 邊界處理模板（8 種情境）

每個邊界情境都有專用模板：

| # | 情境 | 處理方式 |
|---|------|---------|
| 4.1 | 時間衝突 | 列出最接近的替代時段 |
| 4.2 | 整天滿檔 | 推薦最近可用日期 |
| 4.3 | 非營業日 | 告知營業日，推薦最近營業日 |
| 4.4 | 非營業時段 | 告知營業時段，列出可用時段 |
| 4.5 | 缺日期 | 引導提供日期 |
| 4.6 | 缺時間 | 列出該日可用時段 |
| 4.7 | 缺姓名 | 詢問姓名 |
| 4.8 | API 錯誤 | 提供替代方案（稍後重試/電話預約/記錄需求） |

---

## 7. 模組間協作

### 跨模組引用範例

預約模組（Module 01）完成預約後，自動寫入 CRM（Module 03）：

```
calendar_booking_skill.md → Step 8：寫入 CRM
    │
    └──→ 呼叫 Module 03 的 lead_capture_skill
         → 將預約紀錄 append 到 Notion / Google Sheets
```

### 協作原則

1. **單向依賴**：模組間的呼叫是單向的，避免循環依賴
2. **資料格式約定**：跨模組傳遞的資料使用 JSON 結構
3. **失敗隔離**：模組 A 呼叫模組 B 失敗時，模組 A 仍應完成自己的核心功能

---

## 8. `/install-xxx` 安裝命令模式

每個模組都有對應的安裝命令，在 Claude Code 中以 Skill 形式實作：

### 流程

```
學員填寫 business_profile_form.md
          │
          ▼
講師執行 /install-booking
          │
          ▼
Claude Code 讀取表單的 Section 3（預約設定）
          │
          ▼
自動更新：
├── calendar_fields.json（商業欄位）
├── calendar_confirmation_prompt.md（placeholder 替換）
└── 其他相關設定
          │
          ▼
產出安裝確認報告
```

### 安裝命令清單

| 命令 | 讀取表單區段 | 更新的檔案 |
|------|-------------|-----------|
| `/install-booking` | Section 3：預約設定 | `calendar_fields.json` |
| `/install-email` | Section 4：Email 設定 | `gmail_scope_minimal.json`、`reply_style_claude.md` |
| `/install-crm` | Section 5：CRM 設定 | CRM 模板、欄位定義 |
| `/install-customer-service` | Section 2：客服設定 | FAQ 知識庫、轉派規則 |
| `/install-report` | Section 6：報告設定 | 報告模板、排程設定 |
| `/install-notify` | Section 7：通知設定 | 通知管道、靜默時段 |

### 安裝確認報告格式

每個 `/install-xxx` 命令完成後都會產出確認報告：

```
=== 預約模組安裝確認 ===
修改的檔案：
  ✅ calendar_fields.json — business_name: "桑尼工作室"
  ✅ calendar_fields.json — available_days: ["Mon", "Wed", "Fri"]
  ✅ calendar_fields.json — available_hours: 10:00-17:00
  ✅ calendar_fields.json — default_duration_minutes: 60
設定值驗證：全部通過
下一步：測試預約流程
```

---

## 9. 安全模型

### 9.1 白名單原則

- 只安裝本課程提供的 Skill，不從 ClawHub 安裝未審核的第三方 Skill
- 每個 Skill 的 API Scope 必須明確列出且最小化
- 課程提供的每個 Skill 都附帶安全審查文件

### 9.2 最小權限

| 服務 | 第一版權限 | 明確不開的權限 | 理由 |
|------|-----------|---------------|------|
| Gmail | readonly + compose | send, modify, settings | Draft-first，人工確認再寄 |
| Calendar | events.insert | events.delete, bulk update | 只建立，不刪不批量改 |
| Sheets/Notion | append | delete, bulk update | 只新增，不刪不批量改 |
| Telegram | sendMessage | 管理群組、踢人 | 只推送，不管理 |

### 9.3 Draft-first 原則

所有對外動作都必須經過人工確認：

```
AI 草擬 → 用戶預覽 → 用戶確認 → 才執行
```

- Email：先建草稿，確認後才寄出
- 預約：先列出時段，確認後才建立事件
- CRM：資料先預覽，確認後才寫入

### 9.4 權限升級檢查清單

開放更高權限前，學員必須確認：

- [ ] 我理解這個權限允許 AI 做什麼
- [ ] 我知道最壞情況會發生什麼
- [ ] 我有辦法在出問題時立即停止
- [ ] 我已經在安全環境測試過

---

## 10. 附錄：現有所有 OpenClaw Skill 檔案清單

### Module 01 — 預約模組

| 檔案 | 類型 | 說明 |
|------|------|------|
| `module_01_booking/calendar_booking_skill.md` | 邏輯層 | 預約 Skill 完整規格 |
| `module_01_booking/calendar_confirmation_prompt.md` | 表現層 | 確認訊息 Prompt 模板 |
| `module_01_booking/calendar_fields.json` | 設定層 | 預約商業欄位設定 |

### Module 02 — Email 收發模組

| 檔案 | 類型 | 說明 |
|------|------|------|
| `module_02_email/email_triage_skill.md` | 邏輯層 | Email 分類 Skill |
| `module_02_email/email_reply_draft_skill.md` | 邏輯層 | Email 回覆草稿 Skill |
| `module_02_email/reply_style_claude.md` | 表現層 | 回覆風格設定 |
| `module_02_email/gmail_scope_minimal.json` | 設定層 | Gmail API 權限範圍 |

### Module 03 — CRM 模組

| 檔案 | 類型 | 說明 |
|------|------|------|
| `module_03_crm/lead_capture_skill.md` | 邏輯層 | Lead 擷取 Skill |
| `module_03_crm/lead_score_rules.md` | 輔助 | Lead 評分規則 |
| `module_03_crm/notion_crm_database_template.md` | 模板 | Notion CRM 模板 |
| `module_03_crm/sheets_crm_template.md` | 模板 | Google Sheets CRM 模板 |

### Module 04 — 客服模組

| 檔案 | 類型 | 說明 |
|------|------|------|
| `module_04_customer_service/faq_responder_skill.md` | 邏輯層 | FAQ 自動回覆 Skill |
| `module_04_customer_service/escalation_rules.md` | 輔助 | 轉派規則 |
| `module_04_customer_service/channel_setup_guide.md` | 輔助 | 通道設定指南 |

### Module 05 — 日報週報模組

| 檔案 | 類型 | 說明 |
|------|------|------|
| `module_05_report/daily_brief_skill.md` | 邏輯層 | 每日簡報 Skill |
| `module_05_report/weekly_report_skill.md` | 邏輯層 | 週報 Skill |
| `module_05_report/report_prompt_pack.md` | 表現層 | 報告 Prompt 模板包 |
| `module_05_report/report_output_schema.json` | 設定層 | 報告輸出結構定義 |

### Module 06 — 通知模組

| 檔案 | 類型 | 說明 |
|------|------|------|
| `module_06_notification/scheduled_notify_skill.md` | 邏輯層 | 排程通知 Skill |
| `module_06_notification/notification_rules.md` | 輔助 | 通知規則 |
| `module_06_notification/cron_config_template.md` | 模板 | Cron 排程設定模板 |

### 全域設定

| 檔案 | 類型 | 說明 |
|------|------|------|
| `config/business_profile_form.md` | 表單 | 學員商業設定表單 |
| `config/best_practices.md` | 文件 | 五大最佳實務指南 |
| `module_pack_spec.md` | 文件 | 模組包總規格書 |
| `troubleshooting/troubleshooting_sop.md` | SOP | 故障排除標準作業程序 |
