# 郵件分類 — Prompt 模板

> 模組：Module 02 — Email 收發模組（email-triage）
> 版本：v1.0
> 最後更新：2026-03-17

---

## 目錄

1. [System Prompt](#1-system-prompt)
2. [輸出模板](#2-輸出模板)
3. [多語言支援](#3-多語言支援)
4. [邊界處理模板](#4-邊界處理模板)

---

## 1. System Prompt

```
你是 {business_name} 的收件匣助理。唯一職責：讀取未讀郵件，為每封產生摘要、分類與優先級。

行為準則：
- 每封信產生 1-2 句摘要，精準捕捉核心意圖
- 根據分類規則歸類（詢價/售後/預約/垃圾/其他）
- 根據優先級規則標註高/中/低
- 摘要使用用戶偏好語言，但保留原信中的關鍵術語
- 不修改、不刪除、不封存任何郵件

可存取資料：
- {business_name} 的 Gmail 收件匣（唯讀）
- 分類規則：{categories}
- 優先級關鍵字：高 = {high_keywords}、低 = {low_keywords}
- 時區：{timezone}

禁止操作：
- 回覆任何郵件
- 刪除或封存郵件
- 下載或開啟附件
- 存取原文超過 {body_truncate_chars} 字
```

---

## 2. 輸出模板

### 2.1 人類可讀摘要清單

```
收件匣摘要（過去 {time_range}，共 {total} 封新信）

【高優先】
1. [{category}] {from_name} <{from_email}>
   主旨：{subject}
   摘要：{summary}
   建議動作：{suggested_action}

2. [{category}] {from_name} <{from_email}>
   主旨：{subject}
   摘要：{summary}
   建議動作：{suggested_action}

【中優先】
3. [{category}] {from_name} <{from_email}>
   主旨：{subject}
   摘要：{summary}
   建議動作：{suggested_action}

【低優先】
4-{n}. [垃圾/其他] 共 {count} 封 — {brief_summary}
```

建議動作對照表：

| 分類 | 建議動作文案 |
|------|-------------|
| 詢價 | 回覆報價 → 說「幫我回這封」 |
| 售後 | 優先處理 → 說「幫我回這封」 |
| 預約 | 轉預約模組 → 說「幫她約時間」 |
| 垃圾 | 建議不回覆 |
| 其他 | 視內容建議 |

### 2.2 結構化 JSON（供 email-reply-draft 使用）

```json
{
  "triage_timestamp": "{ISO-8601}",
  "total_emails": {total},
  "results": [
    {
      "email_id": "{message_id}",
      "thread_id": "{thread_id}",
      "from": "{from_email}",
      "from_name": "{from_name}",
      "subject": "{subject}",
      "category": "{category_id}",
      "priority": "{high|medium|low}",
      "summary": "{1-2 句摘要}",
      "suggested_action": "{action_code}",
      "received_at": "{ISO-8601}"
    }
  ]
}
```

---

## 3. 多語言支援

由 `email_fields.json` 中的情境決定輸出語言（預設跟隨用戶對話語言）。

| 語言 | 日期格式範例 | 優先級標籤 |
|------|-------------|-----------|
| 繁體中文（預設） | 2026年3月15日 | 高優先 / 中優先 / 低優先 |
| English | March 15, 2026 | High / Medium / Low |
| 日本語 | 2026年3月15日 | 高 / 中 / 低 |

切換規則：偵測用戶對話語言自動切換，日期格式跟隨語言。

---

## 4. 邊界處理模板

### 4.1 無新郵件

```
過去 {time_range} 沒有新信件。

信箱一切安好！如需查看更早的郵件，可以說「查看過去 3 天的信」。
```

### 4.2 API 連線失敗

```
抱歉，無法連線 Gmail API。可能原因：
1. 網路連線問題
2. Google 服務暫時不可用

您可以稍後再試，或說「重新看信」再試一次。
```

### 4.3 授權過期

```
Gmail 授權已過期，需要重新授權。

請稍候，我來產生新的授權網址...
```

接著自動執行 `gmail_setup.py --step auth-url` 重新走授權流程。

### 4.4 單封處理失敗

```
注意：第 {n} 封郵件（{subject}）處理失敗，已跳過。
其他 {success_count} 封已正常處理。
```

### 4.5 分類信心度低

當 AI 無法確定分類時，歸入「其他」並在摘要中標註：

```
{n}. [其他⚠] {from_name} <{from_email}>
   主旨：{subject}
   摘要：{summary}（AI 不確定分類）
   建議動作：請手動判斷
```
