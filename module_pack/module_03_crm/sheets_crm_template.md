# Google Sheets CRM 模板規格

## 基本資訊

| 欄位 | 值 |
|------|-----|
| Sheet 名稱 | CRM_Pipeline |
| 模組歸屬 | module_03_crm |
| 用途 | 不用 Notion 的學員替代方案，功能等價，用 Google Sheets 管理客戶漏斗 |

---

## 欄位定義（A-K 欄）

| 欄位 | 欄位名稱 | 資料類型 | 說明 |
|------|---------|---------|------|
| A | 日期 | Date (YYYY-MM-DD) | 首次詢問日期 |
| B | 客戶名稱 | Text | 客戶姓名或公司名稱 |
| C | 聯絡方式 | Text | Email / Phone / Telegram handle |
| D | 來源管道 | Select | Telegram / Email / 表單 / 推薦 / 其他 |
| E | 需求摘要 | Text | AI 生成的 2-3 句精簡摘要 |
| F | 狀態 | Select | 新詢問 / 跟進中 / 已報價 / 已成交 / 已流失 |
| G | 優先級 | Select | 高 / 中 / 低 |
| H | 負責人 | Text | 負責跟進的團隊成員 |
| I | Follow-up 日期 | Date (YYYY-MM-DD) | 下次應跟進的日期 |
| J | 備註 | Text | 人工補充的備註 |
| K | AI 互動記錄 | Text | AI 自動填寫，每次互動追加 |

### 表頭設定

- Row 1 為表頭列，凍結第一列
- 表頭背景色：深藍（#1a237e），文字白色，粗體
- 欄寬建議：A=100, B=120, C=180, D=100, E=250, F=80, G=60, H=80, I=110, J=200, K=300

---

## 資料驗證規則

### D 欄 — 來源管道（Data Validation）

```
規則類型：List of items
選項：Telegram, Email, 表單, 推薦, 其他
顯示方式：Dropdown
無效輸入：Show warning
套用範圍：D2:D1000
```

### F 欄 — 狀態（Data Validation）

```
規則類型：List of items
選項：新詢問, 跟進中, 已報價, 已成交, 已流失
顯示方式：Dropdown
無效輸入：Reject input
套用範圍：F2:F1000
```

### G 欄 — 優先級（Data Validation）

```
規則類型：List of items
選項：高, 中, 低
顯示方式：Dropdown
無效輸入：Reject input
套用範圍：G2:G1000
```

### A 欄、I 欄 — 日期格式

```
規則類型：Date is valid date
格式：YYYY-MM-DD
套用範圍：A2:A1000, I2:I1000
```

---

## 條件格式（Conditional Formatting）

依狀態欄（F 欄）對整列標色：

| 條件 | 背景色 | 色碼 | 文字色 |
|------|--------|------|--------|
| F 欄 = "新詢問" | 淺藍 | #bbdefb | 黑色 |
| F 欄 = "跟進中" | 淺黃 | #fff9c4 | 黑色 |
| F 欄 = "已報價" | 淺橙 | #ffe0b2 | 黑色 |
| F 欄 = "已成交" | 淺綠 | #c8e6c9 | 黑色 |
| F 欄 = "已流失" | 淺灰 | #e0e0e0 | 灰色 (#757575) |

### 條件格式設定步驟

```
1. 選取 A2:K1000
2. Format → Conditional formatting
3. Custom formula is: =$F2="新詢問"
4. 設定對應背景色
5. 重複上述步驟設定其他四個狀態
6. 注意優先順序：已成交/已流失 放最上面（優先判斷）
```

### 額外條件格式

| 條件 | 效果 | 說明 |
|------|------|------|
| I 欄日期 < 今天 AND F 欄 ≠ "已成交" AND F 欄 ≠ "已流失" | 紅色粗體 | Follow-up 已逾期，需立即處理 |
| G 欄 = "高" | G 欄紅色背景 | 高優先級視覺提醒 |

---

## Google Sheets API 連接說明

### Scope 設定

```
使用 scope: https://www.googleapis.com/auth/spreadsheets
（包含 read + write，但實際操作只用 append）
```

### 寫入模式

| 操作 | API Method | 說明 |
|------|-----------|------|
| 新增紀錄 | `spreadsheets.values.append` | 在最後一列之後新增資料 |
| 讀取紀錄 | `spreadsheets.values.get` | 讀取指定範圍的資料 |
| 更新欄位 | `spreadsheets.values.update` | 更新特定儲存格（僅用於 AI 互動記錄追加） |

### 安全原則

| 規則 | 說明 |
|------|------|
| Append only | 預設只使用 append 新增，不刪除任何列 |
| 不啟用 delete 權限 | API 呼叫中不使用 `batchUpdate` 的 delete 操作 |
| 範圍限定 | 只操作 CRM_Pipeline sheet，不觸碰其他 sheet |
| 寫入確認 | 每次寫入後讀回確認資料正確 |

### API 呼叫範例

**Append 新紀錄**：
```
POST https://sheets.googleapis.com/v4/spreadsheets/{spreadsheetId}/values/CRM_Pipeline!A:K:append
?valueInputOption=USER_ENTERED

Body:
{
  "values": [
    [
      "2026-03-10",
      "王大明",
      "wang@example.com",
      "Telegram",
      "詢問企業內訓方案，15 人團隊，Q2 執行",
      "新詢問",
      "高",
      "Sunny",
      "2026-03-11",
      "",
      "[2026-03-10 14:30] 首次詢問，需求明確，已建立紀錄"
    ]
  ]
}
```

---

## Dashboard Sheet — 漏斗統計面板

在同一份 Spreadsheet 中建立第二個 Sheet，命名為 `Dashboard`。

### 漏斗統計區塊

| 儲存格 | 公式 | 說明 |
|--------|------|------|
| B2 | `=COUNTIF(CRM_Pipeline!F:F,"新詢問")` | 新詢問數量 |
| B3 | `=COUNTIF(CRM_Pipeline!F:F,"跟進中")` | 跟進中數量 |
| B4 | `=COUNTIF(CRM_Pipeline!F:F,"已報價")` | 已報價數量 |
| B5 | `=COUNTIF(CRM_Pipeline!F:F,"已成交")` | 已成交數量 |
| B6 | `=COUNTIF(CRM_Pipeline!F:F,"已流失")` | 已流失數量 |
| B7 | `=COUNTA(CRM_Pipeline!B2:B)-COUNTBLANK(CRM_Pipeline!B2:B)` | 總客戶數 |

### 本月統計區塊

| 儲存格 | 公式 | 說明 |
|--------|------|------|
| D2 | `=COUNTIFS(CRM_Pipeline!A:A,">="&DATE(YEAR(TODAY()),MONTH(TODAY()),1),CRM_Pipeline!A:A,"<="&EOMONTH(TODAY(),0))` | 本月新詢問總數 |
| D3 | `=COUNTIFS(CRM_Pipeline!A:A,">="&DATE(YEAR(TODAY()),MONTH(TODAY()),1),CRM_Pipeline!F:F,"已成交")` | 本月成交數 |
| D4 | `=IF(D2>0, D3/D2, 0)` | 本月轉換率 |

### 來源管道統計

| 儲存格 | 公式 | 說明 |
|--------|------|------|
| F2 | `=COUNTIF(CRM_Pipeline!D:D,"Telegram")` | Telegram 來源數 |
| F3 | `=COUNTIF(CRM_Pipeline!D:D,"Email")` | Email 來源數 |
| F4 | `=COUNTIF(CRM_Pipeline!D:D,"表單")` | 表單來源數 |
| F5 | `=COUNTIF(CRM_Pipeline!D:D,"推薦")` | 推薦來源數 |
| F6 | `=COUNTIF(CRM_Pipeline!D:D,"其他")` | 其他來源數 |

### 逾期 Follow-up 清單

```
=QUERY(CRM_Pipeline!A:K,
  "SELECT B, C, E, F, I
   WHERE I < date '"&TEXT(TODAY(),"yyyy-MM-dd")&"'
   AND F <> '已成交'
   AND F <> '已流失'
   ORDER BY I ASC",
  1)
```

此查詢列出所有 Follow-up 日期已過但尚未結案的客戶，按逾期天數排序。

### Dashboard 視覺化建議

- 漏斗統計用橫條圖（Bar Chart），各狀態對應顏色與條件格式一致
- 來源管道用圓餅圖（Pie Chart）
- 轉換率用大字顯示（格式化為百分比，字號 24pt）
- 逾期清單放在下方，紅色標題提醒

---

## 建立步驟

1. 建立新的 Google Spreadsheet
2. 將第一個 Sheet 重新命名為 `CRM_Pipeline`
3. 在 Row 1 設定表頭（A-K 欄）
4. 設定資料驗證（下拉選單）
5. 設定條件格式（依狀態標色）
6. 建立第二個 Sheet `Dashboard`，貼上統計公式
7. 建立圖表
8. 設定 Google Sheets API 連接
9. 用 `lead_capture` Skill 發送測試紀錄

---

## 課堂提示

- Google Sheets 的優勢是零成本、團隊都會用、公式彈性大
- 劣勢是大量資料（>1000 筆）時效能會下降，屆時再考慮遷移
- Dashboard 不需要很花俏，能看到「各階段幾個人」和「本月轉換率」就夠了
- 建議課堂上直接複製模板，改成自己的業務欄位，20 分鐘內可完成
