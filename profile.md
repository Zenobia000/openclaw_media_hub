# OpenClaw 技能設定檔 (Profile)

請在「您的設定值」欄位中填寫您的專屬資訊。此檔案彙總了行事曆預約、郵件分類、郵件回覆與客戶管理等技能所需的基本設定（已排除所有 API 金鑰設定）。填寫完成後，您可以一次性將這些資料套用至各個技能中。

## 1. 通用設定 (全域共用)

| 欄位名稱 (Key)          | 說明              | 狀態     | 預設值        | 您的設定值 (請於此填寫) |
| ----------------------- | ----------------- | -------- | ------------- | ----------------------- |
| `business_name`         | 商家或工作室名稱  | **必填** | -             |                         |
| `business_email`        | 商業/對外聯絡信箱 | **必填** | -             |                         |
| `timezone`              | 營運時區          | 選填     | `Asia/Taipei` |                         |
| `confirmation_language` | 回覆/確認訊息語言 | 選填     | `zh-TW`       |                         |

---

## 2. 行事曆預約 (calendar-booking)

| 欄位名稱 (Key)             | 說明                      | 狀態 | 預設值                    | 您的設定值 |
| -------------------------- | ------------------------- | ---- | ------------------------- | ---------- |
| `available_days`           | 可預約服務日              | 選填 | `Mon, Tue, Wed, Thu, Fri` |            |
| `available_hours`          | 每天服務時段              | 選填 | `09:00 - 18:00`           |            |
| `default_duration_minutes` | 每次預約的預設時長 (分鐘) | 選填 | `60`                      |            |
| `booking_buffer_minutes`   | 遲到容許緩衝時間 (分鐘)   | 選填 | `15`                      |            |

---

## 3. 郵件處理 (email-triage & email-reply-draft)

| 欄位名稱 (Key)      | 說明                                   | 狀態     | 預設值        | 您的設定值 |
| ------------------- | -------------------------------------- | -------- | ------------- | ---------- |
| `max_emails`        | 每次最多讀取/分類幾封信                | 選填     | `20`          |            |
| `time_range`        | 檢閱多久以內的信件                     | 選填     | `24h`         |            |
| `sender_name`       | 回信署名名稱 (如：Sunny)               | **必填** | -             |            |
| `business_phone`    | 聯絡電話 (簽名檔用)                    | 選填     | -             |            |
| `business_website`  | 網站網址 (簽名檔用)                    | 選填     | -             |            |
| `tone`              | 回信口吻 (formal/semi-formal/friendly) | 選填     | `semi-formal` |            |
| `send_method`       | 發信方式 (resend/gmail_draft)          | 選填     | `resend`      |            |
| `resend.from_name`  | Resend 發信人名稱 (若選用 resend)      | 視設定   | -             |            |
| `resend.from_email` | Resend 發信信箱 (若選用 resend)        | 視設定   | -             |            |
| `resend.reply_to`   | Resend 回覆信箱 (若選用 resend)        | 視設定   | -             |            |

---

## 4. 客戶管理 (lead-capture)

| 欄位名稱 (Key)          | 說明                                    | 狀態     | 預設值         | 您的設定值 |
| ----------------------- | --------------------------------------- | -------- | -------------- | ---------- |
| `backend_type`          | CRM 系統 (notion 或 sheets)             | **必填** | -              |            |
| `default_owner`         | 預設客戶負責人                          | 選填     | -              |            |
| `notion.database_name`  | Notion 資料庫名稱 (若選用 notion)       | 選填     | `客戶管理 CRM` |            |
| `sheets.spreadsheet_id` | Google Sheets 試算表 ID (若選用 sheets) | 視設定   | -              |            |
