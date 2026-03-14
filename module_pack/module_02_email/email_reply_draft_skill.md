# OpenClaw Skill 規格：email_reply_draft

> 模組：Module 02 — Email 收發模組
> 版本：v1.0
> 最後更新：2026-03-10

---

## 1. 基本資訊

| 欄位 | 值 |
|------|-----|
| **Skill Name** | `email_reply_draft` |
| **Skill ID** | `mod02_email_reply_draft` |
| **Category** | Email / Communication |
| **Status** | v1 — 最小可行版 |
| **Author** | Sunny Data Science |
| **依賴 Skill** | `email_triage`（取得分類結果） |

---

## 2. 功能描述

根據 `email_triage` 的分類結果，為用戶指定的郵件草擬回覆內容，透過 **Resend（首選）** 或 **Gmail Draft（備選）** 發送/存檔。用戶確認後才能送出。

### 核心原則

> **Confirm-first：AI 只草擬內容，人工確認後才送。絕不自動寄信。**

### 發信方案：Resend（首選）

Resend 是專為開發者設計的 Email API，設定極簡、與 Claude 原生整合。

#### 為什麼首選 Resend

- **設定極簡**：註冊帳號 → 取得 API Key → 完成，無需設定 OAuth、Google Cloud Console
- **官方 MCP Server**：[github.com/resend/mcp-send-email](https://github.com/resend/mcp-send-email) — Claude 可直接呼叫
- **Claude Code 整合**：[resend.com/claude-code](https://resend.com/claude-code) — 官方整合指南
- **免費額度充足**：100 封/天、3,000 封/月
- **功能完整**：支援 HTML、純文字、附件、CC/BCC

#### Resend 發信流程

```
用戶：「幫我回這封信」（指定某封已分類的郵件）
  │
  ▼
Step 1：取得原信 — 從 email_triage 結果中找到對應郵件
  │
  ▼
Step 2：載入風格 — 讀取 reply_style_claude.md 中的回信規範
  │
  ▼
Step 3：載入分類模板 — 根據郵件分類選用對應回信模板
  │
  ▼
Step 4：草擬回覆 — AI 根據原信內容 + 風格 + 模板生成回覆
  │
  ▼
Step 5：預覽 — 將草稿內容展示給用戶
  │
  ▼
Step 6：用戶確認 — 用戶可選擇「直接寄出」「修改後寄」「重寫」
  │
  ▼
Step 7：透過 Resend API 寄出 — 呼叫 Resend MCP Server 發送郵件
  │
  ▼
Step 8：寄出確認 — 告知用戶信件已成功寄出
```

### 備選方案：Gmail Draft

適合想從原有 Gmail 帳號回信的學員。信件存為草稿，用戶到 Gmail 手動送出。

#### Gmail Draft 流程

```
用戶：「幫我回這封信」（指定某封已分類的郵件）
  │
  ▼
Step 1-6：（同 Resend 方案的 Step 1-6）
  │
  ▼
Step 7：存為 Draft — 呼叫 Gmail API 建立 Draft
  │
  ▼
Step 8：回覆確認 — 告知用戶 Draft 已建立，提醒去 Gmail 確認送出
```

### Resend vs Gmail Draft 對比

| 比較項目 | Resend（首選） | Gmail Draft（備選） |
|----------|---------------|-------------------|
| **設定難度** | 極低：註冊 → API Key → 完成 | 中等：需設定 Google Cloud Console + OAuth |
| **發信方式** | 確認後直接寄出 | 存為草稿，需手動到 Gmail 送出 |
| **寄件人地址** | `noreply@your-domain.resend.app` 或自訂網域 | 你的 Gmail 地址 |
| **收件人回信** | 透過 Reply-To 導回你的真實信箱 | 直接回到你的 Gmail |
| **Claude 整合** | 原生 MCP Server，零額外設定 | 需自行串接 Gmail API |
| **免費額度** | 100 封/天、3,000 封/月 | 無限制（Gmail 本身有每日寄信上限 500 封） |
| **適合對象** | 零基礎學員、想快速上手 | 在意寄件人地址必須是 Gmail 的學員 |
| **附件支援** | 支援 | 支援 |

---

## 3. 觸發條件

### 單封處理

用戶指定某封信並要求回覆：

- 「幫我回這封信」
- 「回覆第 1 封」（對應 triage 清單的編號）
- 「幫我回王小明那封」
- "reply to this email"、"draft a reply"

### 批量處理

用戶要求批量處理多封信：

- 「把高優先的都幫我回」
- 「幫我回所有詢價信」
- "reply to all inquiries"

批量處理時，每封信獨立產生 Draft，每封都需要用戶確認。

---

## 4. 輸入參數

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `email_id` | string | 是（單封）| triage 結果中的 email_id |
| `category` | string | 是（批量）| 要處理的分類（如 "inquiry"） |
| `tone_override` | string | 否 | 臨時覆蓋回信口吻（如「用正式一點的語氣」） |
| `additional_context` | string | 否 | 用戶補充的回覆方向（如「報價 5 萬」「跟他說下週再處理」） |

---

## 5. 輸出

### 草稿預覽（回覆給用戶）

```
以下是我為您草擬的回覆：

---
收件人：王小明 <wang@example.com>
主旨：Re: 請問網站設計方案報價
---

王先生您好，

感謝您的來信詢問。關於企業形象網站設計方案，我們提供以下服務：

[此處根據分類模板生成內容]

如有任何問題，歡迎隨時與我們聯繫。

祝好
{business_name}
{signature}
---

這樣可以嗎？
- 說「OK」→ 我直接存為草稿
- 說「改一下，[修改內容]」→ 我幫您修改後再存
- 說「重寫」→ 我重新草擬
```

### 存檔確認

```
草稿已存入您的 Gmail！

您可以在 Gmail 的「草稿」資料夾中找到這封信，確認內容後手動送出。

Gmail 草稿連結：https://mail.google.com/mail/#drafts
```

---

## 6. API 依賴

### 方案 A：Resend（首選）

| API | 用途 | 設定方式 |
|-----|------|---------|
| Resend API | 發送郵件 | 註冊 → API Key → 設定 MCP Server |
| Gmail API (`gmail.readonly`) | 讀取原信內容（供草擬回覆參考） | OAuth 授權 |

- Resend MCP Server：[github.com/resend/mcp-send-email](https://github.com/resend/mcp-send-email)
- Claude Code 整合：[resend.com/claude-code](https://resend.com/claude-code)

### 方案 B：Gmail Draft（備選）

| API | Scope | 用途 | 權限等級 |
|-----|-------|------|---------|
| Gmail API | `gmail.compose` | 建立 Draft | 寫入（僅 Draft） |
| Gmail API | `gmail.readonly` | 讀取原信內容（如需補充上下文） | 唯讀 |

### 明確不使用的 Scope（Gmail 方案）

| Scope | 理由 |
|-------|------|
| `gmail.send` | **Confirm-first 原則**：人工確認後才能送出，系統絕不自動寄信 |
| `gmail.modify` | 不修改原信（不標已讀、不封存、不刪除） |

---

## 7. 安全限制

### 硬性限制（不可變更）

1. **Confirm-first 鐵律**：無論使用 Resend 或 Gmail Draft，系統都必須經過用戶確認才能發送/存檔。這是本模組最核心的安全設計，任何版本都不可繞過。
2. **不自動送信**：即使批量處理，每封郵件都需要用戶逐封確認後才能寄出（Resend）或存入草稿（Gmail Draft）。
3. **不刪除原信**：回覆後不會刪除、封存、或移動原始郵件。
4. **不修改原信**：不會將原信標為已讀或加任何標籤（標籤由 triage 模組處理）。

### 內容安全

1. **不捏造資訊**：如果沒有價目表，回覆中不會編造價格。
2. **不承諾時程**：除非用戶明確指示，否則不在回覆中承諾任何時間。
3. **不透露內部資訊**：回覆內容不會包含內部流程、成本結構、或其他敏感資訊。
4. **簽名檔固定**：使用 `reply_style_claude.md` 中定義的簽名檔，不自行生成。

---

## 8. 第一版範圍（v1 Scope）

### 包含

- 單封信草擬回覆
- 批量草擬（按分類）
- Resend 發信（首選方案）
- 存為 Gmail Draft（備選方案）
- 預覽 + 確認流程
- 根據分類套用不同回信模板
- 用戶可補充回覆方向

### 不包含（v2 再做）

- 自動送信（永遠不做 — 即使使用 Resend 也必須經過用戶確認，這是設計原則不是功能限制）
- 附件處理（v2，如自動附上報價單 PDF）
- 多輪郵件串追蹤（v2，根據整個對話串生成回覆）
- 回覆排程（v2，設定時間自動送出 Draft）
- 多帳號支援（v2）
- 回覆品質學習（v2，根據用戶修改記錄優化未來回覆）

---

## 9. 錯誤處理

| 錯誤情況 | 回應策略 |
|----------|---------|
| 找不到指定的郵件 | 告知用戶郵件不存在或已被刪除，請重新執行 triage |
| Resend 發送失敗 | 嘗試降級為 Gmail Draft；若也失敗，將草擬內容以文字形式回覆用戶 |
| Gmail Draft 建立失敗 | 將草擬內容以文字形式回覆用戶，讓用戶可手動複製貼上 |
| Gmail API 授權過期 | 提示用戶重新授權 |
| 原信內容為空 | 告知用戶原信無內容，詢問是否仍要回覆 |
| 用戶未提供回覆方向且分類為「其他」 | 詢問用戶想回什麼，不自行猜測 |

---

## 10. 與其他模組的協作

| 協作模組 | 協作方式 |
|----------|---------|
| `email_triage` | 從 triage 結果取得郵件 ID、分類、摘要 |
| `crm_append`（模組 3） | 回覆後將互動紀錄寫入 CRM |
| `calendar_booking`（模組 1） | 如果郵件分類為「預約」，可轉交預約模組處理 |
| `notification`（模組 6） | Draft 建立後可推送通知提醒用戶去確認 |
