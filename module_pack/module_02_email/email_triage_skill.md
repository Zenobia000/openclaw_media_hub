# OpenClaw Skill 規格：email_triage

> 模組：Module 02 — Email 收發模組
> 版本：v1.0
> 最後更新：2026-03-10

---

## 1. 基本資訊

| 欄位 | 值 |
|------|-----|
| **Skill Name** | `email_triage` |
| **Skill ID** | `mod02_email_triage` |
| **Category** | Email / Communication |
| **Status** | v1 — 最小可行版 |
| **Author** | Sunny Data Science |

---

## 2. 功能描述

> **重要提醒**：讀信分類必須使用 Gmail API 或 n8n Gmail node，Resend 無法讀取現有 Gmail 信箱。Resend 只負責「發信」，不具備「讀信」功能。本 Skill 處理的是「讀信 + 分類」，因此只能透過 Gmail API 或 n8n Gmail node 實作。

讀取 Gmail 收件匣中的未讀郵件，由 AI 為每封信產生摘要，自動分類並標註優先級，輸出結構化的分類清單供用戶快速掌握收件狀態。

### 完整流程

```
觸發（定時 / 手動）
  │
  ▼
Step 1：連線 Gmail API — 取得未讀郵件清單
  │
  ▼
Step 2：逐封讀取 — 取得寄件人、主旨、內文（前 500 字）
  │
  ▼
Step 3：AI 摘要 — 每封信產生 1-2 句摘要
  │
  ▼
Step 4：分類 — 歸入預設分類（詢價/售後/預約/垃圾/其他）
  │
  ▼
Step 5：優先級標註 — 高/中/低
  │
  ▼
Step 6：輸出結果 — 結構化清單回覆用戶
  │
  ▼
Step 7（可選）：加標籤 — 在 Gmail 中加上對應 Label
```

---

## 3. 觸發條件

### 定時觸發

- 預設：每小時執行一次
- 可調整頻率：每 30 分鐘 / 每 2 小時 / 每日早上 9 點
- 定時觸發時，結果推送到通知面（Telegram / LINE）

### 手動觸發

用戶在 OpenClaw 中說出以下關鍵字時觸發：

- 繁體中文：`看信`、`收信`、`信箱`、`有沒有新信`、`整理信箱`、`信件摘要`
- 英文：`check email`、`inbox`、`email summary`、`triage`

### 觸發參數

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `max_emails` | integer | 20 | 單次最多處理幾封信 |
| `unread_only` | boolean | true | 是否只處理未讀信件 |
| `time_range` | string | `24h` | 往回查看的時間範圍 |

---

## 4. 分類規則

### 預設分類

| 分類 | Label 名稱 | 判斷依據 | 預設優先級 |
|------|-----------|---------|-----------|
| **詢價** | `AI/Inquiry` | 提到價格、報價、費用、方案、多少錢 | 高 |
| **售後** | `AI/Support` | 提到問題、故障、退貨、退款、不滿意、投訴 | 高 |
| **預約** | `AI/Booking` | 提到預約、約時間、排時間、見面 | 中 |
| **垃圾** | `AI/Spam` | 廣告、推銷、未訂閱的電子報、明顯垃圾信 | 低 |
| **其他** | `AI/Other` | 不屬於以上任何分類 | 中 |

### 優先級判斷

| 優先級 | 條件 |
|--------|------|
| **高** | 詢價信、售後投訴、VIP 客戶（如在 CRM 中有紀錄）、緊急關鍵字（急、ASAP、urgent） |
| **中** | 預約請求、一般業務往來、合作邀約 |
| **低** | 電子報、通知型郵件、廣告、垃圾信 |

### 自訂分類

學員可在客製版中新增分類規則：

```json
{
  "custom_categories": [
    {
      "name": "合作邀約",
      "label": "AI/Partnership",
      "keywords": ["合作", "partnership", "邀約", "提案"],
      "default_priority": "中"
    }
  ]
}
```

---

## 5. 輸出格式

### 摘要清單（回覆給用戶）

```
收件匣摘要（過去 24 小時，共 8 封新信）

【高優先】
1. [詢價] 王小明 <wang@example.com>
   主旨：請問網站設計方案報價
   摘要：詢問企業形象網站設計費用，預算約 5-10 萬，希望本月內完成。
   建議動作：回覆報價 → 說「幫我回這封」

2. [售後] 李大華 <lee@example.com>
   主旨：上次購買的商品有瑕疵
   摘要：反映產品包裝破損，要求換貨或退款，語氣急切。
   建議動作：優先處理 → 說「幫我回這封」

【中優先】
3. [預約] 張美玲 <chang@example.com>
   主旨：想約下週見面討論
   摘要：希望下週三或四下午見面，討論年度行銷計畫。
   建議動作：轉預約模組 → 說「幫她約時間」

【低優先】
4-8. [垃圾/其他] 共 5 封 — 廣告 3 封、系統通知 2 封
```

### 結構化資料（供其他 Skill 使用）

```json
{
  "triage_timestamp": "2026-03-10T09:00:00+08:00",
  "total_emails": 8,
  "results": [
    {
      "email_id": "msg_abc123",
      "from": "wang@example.com",
      "from_name": "王小明",
      "subject": "請問網站設計方案報價",
      "category": "inquiry",
      "priority": "high",
      "summary": "詢問企業形象網站設計費用，預算約 5-10 萬，希望本月內完成。",
      "suggested_action": "reply_with_quote",
      "received_at": "2026-03-10T08:15:00+08:00"
    }
  ]
}
```

---

## 6. API 依賴

| API | Scope | 用途 | 權限等級 |
|-----|-------|------|---------|
| Gmail API | `gmail.readonly` | 讀取收件匣、取得郵件內容 | 唯讀 |
| Gmail API | `gmail.labels` | 新增/套用 AI 分類標籤 | 標籤操作 |

### 明確不使用的 Scope

| Scope | 理由 |
|-------|------|
| `gmail.send` | 本 Skill 只讀不寫，寄信由 `email_reply_draft` 處理 |
| `gmail.modify` | 不自動封存、不自動刪除 |
| `gmail.settings.basic` | 不建立自動篩選規則 |

---

## 7. 安全限制

### 硬性限制

1. **只讀不寫**：本 Skill 不會修改、刪除、封存、或移動任何郵件
2. **只加標籤**：唯一的寫入操作是在郵件上加 AI 分類標籤
3. **內文截斷**：只讀取每封信的前 500 字，不處理完整長信
4. **附件不讀**：不下載、不開啟、不解析任何附件
5. **不存原文**：AI 摘要後不保留郵件原文，只保留摘要

### 隱私保護

- 郵件內文只在 AI 處理時暫存於記憶體，不寫入磁碟
- 分類結果中只包含摘要，不包含完整內文
- CRM 中只記錄寄件人、主旨、分類、優先級，不記錄內文

---

## 8. 第一版範圍（v1 Scope）

### 包含

- 讀取未讀郵件
- AI 摘要（每封 1-2 句）
- 五類分類（詢價/售後/預約/垃圾/其他）
- 三級優先（高/中/低）
- Gmail Label 標註
- 結構化清單輸出

### 不包含（v2 再做）

- 自訂分類規則（v2）
- VIP 客戶自動識別（v2，需串 CRM）
- 自動轉派（v2，如預約類自動觸發預約模組）
- 郵件串追蹤（v2，追蹤同一封信的來回）
- 附件解析（v2）
- 多帳號支援（v2）

---

## 9. 錯誤處理

| 錯誤情況 | 回應策略 |
|----------|---------|
| Gmail API 連線失敗 | 告知用戶稍後再試，記錄錯誤 |
| 授權過期 | 提示用戶重新授權，提供授權連結 |
| 單封信處理失敗 | 跳過該封，繼續處理其他信，在結果中標註「處理失敗」 |
| 無新郵件 | 回覆「過去 {time_range} 沒有新信件」 |
| 分類信心度低 | 歸入「其他」類，標註「AI 不確定」 |

---

## 10. 替代方案：n8n Gmail Trigger Node

對於零基礎學員，可使用 **n8n Gmail Trigger node** 替代直接呼叫 Gmail API：

### 為什麼推薦 n8n

| 比較項目 | Gmail API 直接串接 | n8n Gmail Trigger Node |
|----------|-------------------|----------------------|
| OAuth 設定 | 需自行在 Google Cloud Console 建立專案、設定 OAuth 同意畫面 | n8n 已封裝 OAuth 流程，學員只需點擊「授權」按鈕 |
| 技術門檻 | 需了解 API 呼叫、Token 管理 | 零程式碼，拖拉式設定 |
| 適合對象 | 有技術背景的學員 | 零基礎學員 |
| 彈性 | 完全自訂 | 受限於 n8n node 提供的參數 |

### n8n 實作方式

```
n8n Gmail Trigger Node（監聽新信）
  │
  ▼
n8n AI Node（Claude / GPT）— 執行摘要 + 分類 + 優先級判斷
  │
  ▼
n8n Gmail Node — 為郵件加上對應 Label
  │
  ▼
n8n 輸出 — 將分類結果推送到 Telegram / LINE / Webhook
```

### 設定步驟

1. 在 n8n 中新增 **Gmail Trigger** node
2. 點擊「Connect」按鈕，登入 Google 帳號並授權（不需進 Google Cloud Console）
3. 設定觸發條件：`Label = INBOX`、`Read Status = Unread`
4. 串接 **AI Agent** node，貼入本 Skill 的分類規則作為 System Prompt
5. 串接 **Gmail** node 加 Label
6. 測試並啟用 Workflow

### 注意事項

- n8n Gmail Trigger node 需要 n8n 實例持續運行（建議使用 n8n Cloud 或自架 Docker）
- 免費版 n8n Cloud 有執行次數限制
- 如需更細緻的控制（如自訂 Token 管理、錯誤重試），建議回歸 Gmail API 方案
