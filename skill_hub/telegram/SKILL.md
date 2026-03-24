---
name: telegram
description: |
  透過 Telegram Bot API 發送訊息。支援文字訊息、格式化（HTML/Markdown）、rate limit 處理。
  使用時機：需要透過 Telegram Bot 發送通知或訊息。
  不適用：接收訊息/webhook、群組管理、機器人指令處理、語音/圖片。
metadata:
  author: openclaw
  version: "1.0"
  openclaw:
    emoji: 📨
    requires:
      bins: ["python3"]
      env: ["TELEGRAM_BOT_TOKEN"]
---

# Telegram

透過 Telegram Bot API 發送文字訊息，支援 HTML/Markdown 格式化與 rate limit 處理。純 stdlib 實作，無外部依賴。

## 前置條件

1. 透過 BotFather 建立 Telegram Bot，取得 `TELEGRAM_BOT_TOKEN`
2. 取得目標 Chat ID（可用 `@userinfobot` 查詢）

## 發送訊息

```bash
python3 skill_hub/telegram/scripts/tg_send_message.py \
    --bot-token "$TELEGRAM_BOT_TOKEN" \
    --chat-id "987654321" \
    --message "Hello, World!"
```

參數：
- `--bot-token`（必要）：Telegram Bot Token
- `--chat-id`（必要）：目標 Chat ID
- `--message`（必要）：訊息內容
- `--parse-mode`：訊息格式，可選 `HTML`、`Markdown`、`MarkdownV2`
- `--dry-run`：僅輸出請求內容，不實際發送

### 格式化範例

```bash
# HTML 格式
python3 skill_hub/telegram/scripts/tg_send_message.py \
    --bot-token "$TELEGRAM_BOT_TOKEN" \
    --chat-id "987654321" \
    --message "<b>粗體</b> <i>斜體</i>" \
    --parse-mode HTML
```

## 錯誤處理

所有錯誤回傳：
```json
{"ok": false, "error": "錯誤描述"}
```

429 Rate Limit 回傳含 `retry_after` 秒數：
```json
{"ok": false, "error": "Rate limited. Retry after 30s", "retry_after": 30}
```

## 腳本一覽

| 腳本 | 功能 |
|------|------|
| `tg_send_message.py` | 透過 Bot API 發送文字訊息 |
