---
name: install-booking
description: "安裝預約模組 — 讀取學員商業設定表單，自動更新 calendar_fields.json 和所有預約模組設定。"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash
---

# 安裝預約模組

你是 OpenClaw 的模組安裝助理。你的任務是讀取學員的商業設定表單，自動更新預約模組的所有設定檔。

## 安裝步驟

### Step 1：讀取商業設定表單

讀取 `module_pack/config/business_profile_form.md`，提取以下資訊：

**從 Section 1（基本資訊）提取：**
- 公司/個人名稱 → 對應 `business_name`

**從 Section 3（預約設定）提取：**
- 可預約時段 — 週幾 → 對應 `available_days`
- 可預約時段 — 時間 → 對應 `available_hours`
- 預約時長 → 對應 `default_duration_minutes`
- 預約緩衝時間 → 對應 `booking_buffer_minutes`
- 預約確認訊息格式 → 用於更新確認模板

### Step 2：驗證表單內容

檢查以下欄位是否已填寫（非空白、非預設的 `（填入）` placeholder）：

- [ ] 公司/個人名稱
- [ ] 可預約時段 — 週幾
- [ ] 可預約時段 — 時間
- [ ] 預約時長

如果有未填寫的必要欄位，**停止安裝**，列出缺少的欄位並請學員先完成填寫。

### Step 3：轉換格式

將表單中的自然語言轉換為 JSON 格式：

**週幾轉換規則：**
| 表單填寫 | JSON 值 |
|----------|---------|
| 週一 / 星期一 / Monday | `"Mon"` |
| 週二 / 星期二 / Tuesday | `"Tue"` |
| 週三 / 星期三 / Wednesday | `"Wed"` |
| 週四 / 星期四 / Thursday | `"Thu"` |
| 週五 / 星期五 / Friday | `"Fri"` |
| 週六 / 星期六 / Saturday | `"Sat"` |
| 週日 / 星期日 / Sunday | `"Sun"` |

**時間轉換規則：**
- `10:00-17:00` → `"start": "10:00", "end": "17:00"`
- `上午10點到下午5點` → `"start": "10:00", "end": "17:00"`

**時長轉換規則：**
- `30min` / `30 分鐘` → `30`
- `60min` / `1 小時` → `60`
- `90min` / `1.5 小時` → `90`

### Step 4：更新 calendar_fields.json

讀取 `module_pack/module_01_booking/calendar_fields.json`，更新以下欄位：

```json
{
  "business_name": "<從表單提取>",
  "available_days": ["<轉換後的週幾陣列>"],
  "available_hours": {
    "start": "<轉換後的開始時間>",
    "end": "<轉換後的結束時間>"
  },
  "default_duration_minutes": <轉換後的時長數字>,
  "booking_buffer_minutes": <轉換後的緩衝時間數字>
}
```

不修改以下欄位（保持原值）：
- `calendar_id` — 需要另外設定 Google Calendar
- `event_title_format` — 使用預設格式（會自動帶入 business_name）
- `timezone` — 預設 `Asia/Taipei`
- `notification_target` — 預設 `telegram`
- `confirmation_language` — 預設 `zh-TW`

### Step 5：更新確認模板（如有自訂）

如果學員在表單 Section 3 的「預約確認訊息格式」有填寫自訂內容（非使用預設模板），則更新 `module_pack/module_01_booking/calendar_confirmation_prompt.md` 中 Section 2.2 的確認模板。

如果學員選擇使用預設模板，則不修改確認模板。

### Step 6：產出安裝確認報告

安裝完成後，輸出以下格式的確認報告：

```
========================================
  預約模組安裝確認報告
========================================

商業資訊：
  公司名稱：{business_name}

預約設定：
  可預約日：{available_days}
  營業時段：{available_hours.start} - {available_hours.end}
  預約時長：{default_duration_minutes} 分鐘
  緩衝時間：{booking_buffer_minutes} 分鐘

修改的檔案：
  ✅ module_pack/module_01_booking/calendar_fields.json
  [如有修改] ✅ module_pack/module_01_booking/calendar_confirmation_prompt.md

未修改的設定（使用預設值）：
  - calendar_id: primary
  - timezone: Asia/Taipei
  - confirmation_language: zh-TW
  - event_title_format: {business_name} - {client_name} 預約

下一步：
  1. 設定 Google Calendar API 授權
  2. 測試預約流程：在 OpenClaw 中說「我想約下週三下午」
  3. 確認事件是否正確建立在 Google Calendar 中

========================================
```

## 注意事項

- **不修改 Skill 規格檔**（`calendar_booking_skill.md`）— 那是邏輯層，不應被安裝命令改動
- **不修改 API 相關設定** — OAuth 和 API Key 需另外設定
- **備份原始檔案** — 更新前先讀取並顯示原始值，讓學員確認
- **一次只處理一個模組** — 不要在安裝預約模組時修改其他模組的檔案
