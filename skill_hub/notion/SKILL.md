---
name: notion
description: |
  透過 Notion API 建立 Page。支援任意 database 結構，properties 由呼叫端定義。
  使用時機：需要透過 Notion API 新增資料頁面至 database。
  不適用：查詢/更新/刪除 Notion 頁面、管理 database 結構、Notion MCP 操作。
metadata:
  author: openclaw
  version: "1.0"
  openclaw:
    emoji: 📝
    requires:
      bins: ["python3"]
---

# Notion

透過 Notion API 在指定 database 建立 Page。純 stdlib 實作，無外部依賴。

## 前置條件

1. 在 [Notion Integrations](https://www.notion.so/my-integrations) 建立 Internal Integration
2. 取得 Integration Token（`ntn_` 開頭）
3. 在目標 database 頁面「Connections」中加入此 Integration

## 建立 Page

```bash
python3 skill_hub/notion/scripts/notion_create_page.py \
    --token "ntn_xxx" \
    --database-id "DATABASE_ID" \
    --properties '{"Name":{"title":[{"text":{"content":"項目名稱"}}]},"Status":{"select":{"name":"Active"}}}'
```

參數：
- `--token`（必要）：Notion Integration Token
- `--database-id`（必要）：目標 Notion 資料庫 ID
- `--properties`（必要）：完整的 Notion properties JSON，格式遵循 [Notion API Create a page](https://developers.notion.com/reference/post-page) 的 properties 規格
- `--dry-run`：僅輸出請求內容，不實際建立

### Properties 格式範例

```json
{
  "標題欄位": {
    "title": [{"text": {"content": "內容"}}]
  },
  "文字欄位": {
    "rich_text": [{"text": {"content": "內容"}}]
  },
  "選項欄位": {
    "select": {"name": "選項值"}
  },
  "日期欄位": {
    "date": {"start": "2026-03-18"}
  }
}
```

## 錯誤處理

錯誤時回傳：
```json
{"ok": false, "error": "Notion API error 400: ..."}
```

常見錯誤：
- `401`：Token 無效或已過期
- `404`：Database ID 不存在或 Integration 無權限
- `400`：Properties 格式不符合 database schema

## 腳本一覽

| 腳本 | 功能 |
|------|------|
| `notion_create_page.py` | 在 Notion database 建立 Page |
