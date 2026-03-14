# OpenClaw Skill 規格：lead_capture

## 基本資訊

| 欄位 | 值 |
|------|-----|
| Skill 名稱 | `lead_capture` |
| 版本 | 1.0 |
| 模組歸屬 | module_03_crm |
| 適用情境 | B2B / B2C 客戶開發、諮詢服務、課程報名前詢問 |

---

## 功能描述

從聊天對話、表單填寫、Email 詢問中擷取客戶資訊，摘要需求，寫入 CRM（Notion 或 Google Sheets），自動標註狀態，並建立 follow-up 任務。

**核心價值**：讓每一筆潛在客戶都不漏接，從「收到訊息」到「建立 CRM 紀錄」全自動完成。

---

## 觸發條件

| 觸發來源 | 條件描述 |
|----------|---------|
| 聊天對話 | 用戶在 Telegram Bot 表達詢問意圖（例如「想了解服務」「有合作需求」「想報名」） |
| 表單填寫 | 外部表單（Google Form / Typeform）提交後透過 webhook 觸發 |
| Email 詢問 | 收到指定信箱的新郵件，主旨或內文含詢問關鍵字 |
| 轉介訊息 | 團隊成員手動轉發客戶訊息並標記 `#lead` |

---

## 輸入解析

AI 從訊息內容中自動擷取以下欄位：

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| 客戶名稱 | Text | 是 | 從對話中擷取，若無法辨識則標記「未提供」 |
| 聯絡方式 | Text | 是 | Email / Phone / Telegram handle，至少一項 |
| 需求摘要 | Rich Text | 是 | AI 根據對話內容生成 2-3 句摘要 |
| 來源管道 | Select | 是 | Telegram / Email / 表單 / 推薦 / 其他 |
| 詢問日期 | Date | 自動 | 系統自動填入收到訊息的日期 |

**擷取邏輯**：

```
1. 接收原始訊息
2. AI 分析訊息內容，提取結構化欄位
3. 缺少必填欄位時，標記為「未提供」而非回頭追問（第一版簡化）
4. 生成需求摘要（不超過 100 字）
5. 根據 lead_score_rules 計算初始評分
```

---

## 輸出

| 輸出項目 | 說明 |
|---------|------|
| CRM 紀錄建立確認 | 回傳紀錄 ID 與摘要，確認已寫入 |
| 自動指派 follow-up 日期 | 根據 lead score 規則：高分=24hr / 中分=3天 / 低分=7天 |
| 通知負責人 | 高優先級客戶即時通知指定人員 |
| 對話記錄存檔 | 原始對話內容寫入 AI 互動記錄欄位 |

**輸出範例**（回傳給操作者）：

```
已建立 CRM 紀錄：
- 客戶：王大明
- 需求：想了解企業內訓方案，團隊約 15 人，預計 Q2 執行
- 評分：高（有預算+時程）
- Follow-up：2026-03-11（明天）
- 已通知負責人：@sunny
```

---

## 依賴

| 依賴項目 | 說明 |
|---------|------|
| Notion MCP（推薦） | 使用官方 hosted MCP server，OAuth 授權，需 `read_content` + `insert_content` 權限 |
| Google Sheets API（替代） | 使用 `sheets.spreadsheets` scope，append 模式寫入 |

> **重要**：只選一個系統當主資料面（Notion 或 Sheets），不要兩個一起用。雙系統同步是維護噩夢，課堂上選一個專心做好就好。

---

## 安全限制

| 規則 | 說明 |
|------|------|
| 只做 Append | 只新增紀錄，絕不刪除既有資料 |
| 不修改核心欄位 | 建立後的客戶名稱、聯絡方式不可被 AI 覆寫 |
| 狀態只能前進 | AI 只能將狀態從「新詢問」推進，不可回退（回退需人工操作） |
| 敏感資訊處理 | 信用卡號、身分證字號等敏感資訊不寫入 CRM，僅標記「客戶有提供敏感資訊，請人工確認」 |

---

## 設計原則

1. **單一資料源**：Notion 或 Sheets 擇一，不做雙向同步
2. **寧可多建不漏接**：重複紀錄比漏掉客戶好，後續可人工合併
3. **AI 摘要而非原文**：需求摘要欄寫的是 AI 理解後的精簡版，原始對話存在 AI 互動記錄
4. **低門檻啟動**：第一版不需要完美的欄位擷取，先跑起來再迭代

---

## Skill 定義片段（OpenClaw 格式參考）

```yaml
skill:
  name: lead_capture
  description: >
    擷取客戶資訊並寫入 CRM，自動建立 follow-up 任務
  triggers:
    - type: message
      conditions:
        - intent: inquiry
        - intent: collaboration
        - intent: signup
    - type: webhook
      source: google_form
    - type: email
      mailbox: inquiry@yourdomain.com
  actions:
    - extract_lead_info
    - calculate_lead_score
    - write_to_crm
    - schedule_followup
    - notify_owner
  dependencies:
    - notion_mcp  # or google_sheets_api
  safety:
    operations: [append]
    prohibited: [delete, update_core_fields]
```

---

## 課堂提示

- 這個 Skill 是整個 CRM 模組的入口，做好這個，後面的評分和跟進才有意義
- 第一次設定時，建議先用 Telegram Bot 手動發幾則測試訊息，確認 CRM 寫入正確
- 不要一開始就想做「完美的欄位擷取」，先讓資料流通起來，再慢慢調整 prompt
