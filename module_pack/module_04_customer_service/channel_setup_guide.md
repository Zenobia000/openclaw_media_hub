# OpenClaw Channel 設定指南

## 基本資訊

| 欄位 | 值 |
|------|-----|
| 文件名稱 | channel_setup_guide |
| 模組歸屬 | module_04_customer_service |
| 用途 | 指導學員設定 OpenClaw 的 Telegram Bot Channel，作為客服入口 |

---

## 推薦入門設定：Telegram Bot（DM 模式）

### 為什麼選 Telegram？

| 優勢 | 說明 |
|------|------|
| 零成本 | Bot 建立免費，API 免費，無訊息量限制 |
| 設定簡單 | 10 分鐘內可完成 Bot 建立與 token 取得 |
| OpenClaw 原生支援 | OpenClaw 對 Telegram 的整合最成熟 |
| 開發者友善 | API 文件完整，除錯容易 |
| 跨平台 | 客戶端支援 iOS / Android / Desktop / Web |

### 為什麼先用單一入口？

| 原因 | 說明 |
|------|------|
| 降低複雜度 | 一個入口就是一套邏輯，多入口就是多套邏輯 + 同步問題 |
| 避免跨平台同步 | 不同平台的訊息格式、限制、API 都不同，同步是工程難題 |
| 集中驗證 | 先在一個管道上跑通所有流程，確認 OK 再擴展 |
| OpenClaw 限制 | Telegram topic routing 與 streaming 功能仍在調整中，DM 模式最穩定 |

> 一個做得好的 Telegram Bot，比三個半成品的多平台客服有用得多。

---

## Telegram Bot 建立步驟

### Step 1：透過 BotFather 建立 Bot

```
1. 在 Telegram 搜尋 @BotFather
2. 發送 /newbot
3. 輸入 Bot 名稱（顯示名稱，例如「桑尼AI助手」）
4. 輸入 Bot username（必須以 bot 結尾，例如 sunny_ai_assistant_bot）
5. BotFather 回覆 Bot Token（格式：123456789:ABCdefGHIjklMNOpqrsTUVwxyz）
6. 妥善保存 Token，不可外洩
```

### Step 2：Bot 基本設定

透過 BotFather 進行以下設定：

```
/setdescription - 設定 Bot 簡介（客戶看到 Bot 時的介紹文字）
範例：「您好！我是桑尼的 AI 助手，可以回答常見問題、記錄您的需求。有任何問題歡迎直接發訊息。」

/setabouttext - 設定 About 資訊
範例：「桑尼資料科學 AI 客服助手 | 24/7 在線 | 服務時間：週一至週五 09:00-18:00」

/setuserpic - 上傳 Bot 頭像（建議使用品牌 logo）

/setcommands - 設定指令選單
start - 開始對話
help - 查看幫助
contact - 聯繫真人客服
```

### Step 3：OpenClaw docker-compose 設定

在 OpenClaw 的 `docker-compose.yml` 中加入 Telegram channel 設定：

```yaml
services:
  openclaw:
    # ... 其他設定 ...
    environment:
      # Telegram Channel 設定
      TELEGRAM_BOT_TOKEN: "${TELEGRAM_BOT_TOKEN}"
      TELEGRAM_CHANNEL_TYPE: "dm"  # DM 模式，不使用 group/topic

      # 通知設定（升級時通知負責人）
      TELEGRAM_NOTIFY_CHAT_ID: "${NOTIFY_CHAT_ID}"  # 負責人的 Telegram ID
```

### Step 4：設定環境變數

在 `.env` 檔案中：

```bash
# Telegram Bot Token（從 BotFather 取得）
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# 負責人 Telegram Chat ID（用於升級通知）
# 取得方式：向 @userinfobot 發送訊息，取得自己的 ID
NOTIFY_CHAT_ID=987654321
```

> 注意：`.env` 必須加入 `.gitignore`，Token 絕不可進版本控制。

### Step 5：啟動與驗證

```bash
# 啟動 OpenClaw
docker-compose up -d

# 檢查日誌確認 Telegram 連線成功
docker-compose logs -f openclaw | grep -i telegram

# 預期看到：
# Telegram bot connected: @sunny_ai_assistant_bot
# Listening for DM messages...
```

### Step 6：測試

```
1. 用自己的 Telegram 帳號搜尋剛建立的 Bot
2. 點選 Start 或發送 /start
3. 發送一則測試訊息：「你們提供什麼服務？」
4. 確認 Bot 有正確回覆（來自 FAQ 知識庫）
5. 發送一則應升級的訊息：「想詢問報價」
6. 確認 Bot 回覆轉人工訊息，並確認負責人收到通知
7. 檢查 CRM 是否有新紀錄
```

---

## System Prompt 設定

### System Prompt 位置

在 OpenClaw 的設定中（通常是 `config/system_prompt.md` 或管理介面）。

### System Prompt 範本

```markdown
你是 [品牌名稱] 的 AI 客服助手。

## 你的職責
- 回答客戶的常見問題（根據知識庫）
- 記錄客戶的需求與聯絡資訊
- 超出你能力範圍的問題，轉交給真人同仁

## 你的個性
- 友善、專業、簡潔
- 使用「您」稱呼客戶
- 不過度熱情，不使用太多驚嘆號
- 誠實：不確定的事情就說不確定

## 你絕對不可以做的事
- 不可以編造答案
- 不可以報價格（除非知識庫有明確價目）
- 不可以承諾交付時間
- 不可以處理退款或客訴（要轉人工）
- 不可以透露內部流程或系統架構

## 回覆格式
- 回覆控制在 200 字以內
- 先回答問題，再提供下一步建議
- 結尾可詢問「還有其他問題嗎？」

## 工作時間
- 服務時間：週一至週五 09:00-18:00（台灣時間）
- 非工作時間：告知客戶人工將於上班時間回覆
```

### 人格設計建議

| 面向 | 建議 | 避免 |
|------|------|------|
| 稱呼 | 「您好」「感謝您」 | 「親」「寶」「大大」 |
| 語氣 | 專業溫和 | 過度熱情、冷漠生硬 |
| 回覆長度 | 50-200 字 | 過短（感覺敷衍）、過長（客戶不看） |
| 表情符號 | 不使用或極少使用 | 大量 emoji |
| 結構 | 分段、用列表 | 一大段文字 |
| 不確定時 | 「讓我幫您轉接專人」 | 猜測或編造答案 |

> 人格設計應符合品牌調性。技術公司偏專業簡潔，生活品牌可以稍微親切。課堂上建議先用專業風格，後續再依回饋調整。

---

## 第一版不建議做的

| 功能 | 不建議的原因 | 什麼時候再做 |
|------|------------|------------|
| 多群組廣播 | 需要管理群組權限、訊息格式差異、容易被封鎖 | 確認 DM 客服穩定後，有明確廣播需求時 |
| Telegram topic 派送 | OpenClaw 的 topic routing 功能仍在調整，穩定性不足 | 等 OpenClaw 官方公告 topic 功能穩定 |
| 多平台同時上線 | 每多一個平台就多一倍維護成本，且跨平台對話同步是難題 | 單一平台跑順後，依客戶分佈決定下一個平台 |
| Inline Mode | Telegram inline 模式（在其他聊天中呼叫 Bot）增加複雜度 | 有明確使用場景時 |
| 支付功能 | Telegram Bot Payment API 需額外設定支付提供商 | 有明確的自動化收款需求時 |

---

## 未來擴展路徑

當 Telegram DM 客服穩定運行後，可按以下順序擴展：

### Phase 1：Telegram 深化（1-2 個月後）

```
Telegram DM（現在）
    ↓
Telegram Group Bot（在特定群組中回答問題）
    ↓
Telegram Topic Routing（等 OpenClaw 支援穩定後）
```

### Phase 2：第二平台（3-6 個月後）

根據客戶分佈選擇：

| 平台 | 適合場景 | 設定複雜度 |
|------|---------|----------|
| Discord | 技術社群、遊戲相關、開發者客戶 | 中 |
| LINE | 台灣 B2C 客戶、年齡層偏高的受眾 | 高（需 LINE Official Account） |
| WhatsApp | 國際客戶、東南亞市場 | 高（需 Business API） |

### Phase 3：全通路整合（6-12 個月後）

```
所有平台的訊息 → 統一 CRM 紀錄
                → 統一知識庫
                → 統一升級流程
                → 跨平台對話歷史
```

> 每個 Phase 之間的前提：上一個 Phase 已經穩定運行至少 1 個月，且有明確的擴展需求。不要因為「感覺應該要有」就急著擴展。

---

## 常見問題排除

### Bot 沒有回覆

```
檢查清單：
1. docker-compose logs 是否有錯誤？
2. TELEGRAM_BOT_TOKEN 是否正確？
3. Bot 是否被 Telegram 封鎖？（重新向 BotFather 確認狀態）
4. 防火牆是否阻擋了 Telegram API（api.telegram.org）？
5. OpenClaw 服務是否正常運行？
```

### Bot 回覆但內容不對

```
檢查清單：
1. System Prompt 是否正確設定？
2. 知識庫檔案是否在正確路徑？
3. 知識庫格式是否正確（Markdown Q&A）？
4. 是否有多個 Skill 搶同一個 trigger？
```

### 升級通知沒收到

```
檢查清單：
1. NOTIFY_CHAT_ID 是否正確？
2. 負責人是否已向 Bot 發送過 /start？（Telegram 要求先互動才能收到訊息）
3. 升級規則是否正確觸發？（檢查 CRM 記錄）
4. 通知管道設定是否正確（Telegram / Email）？
```

---

## 課堂提示

- 整個設定過程大約 20-30 分鐘，課堂上可以現場完成
- 最容易卡住的地方：拿到 Token 後忘記存、Chat ID 填錯
- Bot 名稱取好一點，這是客戶第一印象
- System Prompt 是客服品質的基礎，花 10 分鐘認真寫，比花 1 小時調其他設定更有效
- 上線前用自己的帳號測完整流程（FAQ 回覆 + 升級轉人工 + CRM 記錄），三個都通過才算完成
