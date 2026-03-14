# 故障排除 SOP

> 按模組分類的故障排除標準作業程序。
> 每個問題依照：**症狀描述 → 可能原因 → 排除步驟 → 預防措施** 四階段處理。

---

## 通用問題

### OpenClaw 無法啟動

**症狀描述：** 執行 `docker-compose up` 後，OpenClaw 服務未正常啟動或立即退出。

**可能原因：**
- Docker daemon 未運行
- Port 被其他服務佔用（預設 8080）
- docker-compose.yml 設定錯誤
- Image 下載失敗

**排除步驟：**
1. 確認 Docker 正在運行：`docker info`
2. 查看容器日誌：`docker-compose logs openclaw`
3. 檢查 port 佔用：`lsof -i :8080` 或 `netstat -tlnp | grep 8080`
4. 嘗試重新啟動：`docker-compose down && docker-compose up -d`
5. 若 image 有問題：`docker-compose pull && docker-compose up -d`

**預防措施：**
- 開課前確認 Docker 已啟動
- 預先拉取所有 image：`docker-compose pull`
- 預留替代 port 設定

---

### Claude Code 連線失敗

**症狀描述：** Claude Code 無法連接到 Anthropic API，出現 connection error 或 authentication error。

**可能原因：**
- API Key 未設定或已過期
- 網路連線問題（防火牆、VPN）
- Anthropic 訂閱狀態異常
- API endpoint 設定錯誤

**排除步驟：**
1. 確認 API Key 已設定：`echo $ANTHROPIC_API_KEY | head -c 10`（只顯示前 10 字元）
2. 測試網路連線：`curl -s https://api.anthropic.com/v1/messages -w "%{http_code}" -o /dev/null`
3. 確認訂閱狀態：登入 https://console.anthropic.com 查看帳號
4. 重新設定 API Key：`export ANTHROPIC_API_KEY="sk-ant-..."`

**預防措施：**
- 課前一天確認 API Key 有效
- 準備備用 API Key
- 確認教室網路不擋 Anthropic API

---

### API 額度不足

**症狀描述：** 收到 rate limit 或 quota exceeded 錯誤訊息。

**可能原因：**
- 月度使用額度已達上限
- 每分鐘請求數超過限制
- 帳號方案限制

**排除步驟：**
1. 登入 Anthropic Console 查看用量：https://console.anthropic.com/usage
2. 登入 Google Cloud Console 查看 API 用量（如使用 Google 服務）
3. 檢查是否有異常的高頻請求：`docker-compose logs | grep -i "rate limit"`
4. 暫停排程任務以降低使用量

**預防措施：**
- 設定 usage alert（Anthropic Console → Settings → Usage alerts）
- 在 Google Cloud Console 設定預算警報
- 課程使用獨立帳號，與個人/公司帳號分開
- 課堂上先用小量測試，確認正常後再開排程

---

### 權限被拒

**症狀描述：** API 呼叫返回 403 Forbidden 或 insufficient permissions 錯誤。

**可能原因：**
- OAuth scopes 不足
- Token 過期未更新
- 目標資源（行事曆、Sheet、Notion DB）的共用設定不正確

**排除步驟：**
1. 確認錯誤訊息中的 scope 需求
2. 重新執行授權流程，確保勾選所有需要的 scopes
3. 檢查 OAuth token 是否過期：查看 token 檔案的時間戳
4. 確認目標資源已共用給服務帳號

**預防措施：**
- 授權時一次勾選所有需要的 scopes
- 設定 token 自動更新機制
- 課前用 checklist 確認所有權限

---

## Module 01：預約

### Calendar 事件沒建立

**症狀描述：** 執行預約流程後，Google Calendar 上沒有出現新事件。

**可能原因：**
- Calendar ID 設定錯誤
- API scope 不包含 `calendar.events`
- 時區設定不一致
- MCP 連線中斷

**排除步驟：**
1. 確認 Calendar ID：到 Google Calendar → 設定 → 整合 → Calendar ID
2. 檢查 API scope：確認包含 `https://www.googleapis.com/auth/calendar.events`
3. 檢查時區設定：確認 skill config 中的 timezone 與 Google Calendar 一致
4. 測試 MCP 連線：在 Claude Code 中執行簡單的 Calendar 查詢
5. 查看 OpenClaw 日誌：`docker-compose logs | grep -i calendar`

**預防措施：**
- 安裝時使用 `/install-booking` 自動設定 Calendar ID
- 統一使用 `Asia/Taipei` 時區
- 每次課前執行一次測試預約

---

### 時間衝突沒偵測到

**症狀描述：** 同一時段被重複預約，系統沒有發出衝突警告。

**可能原因：**
- freebusy query 設定未啟用
- 查詢的 Calendar ID 與建立事件的 Calendar ID 不同
- 時區轉換錯誤導致比對失敗

**排除步驟：**
1. 確認 freebusy query 有被呼叫：查看日誌中是否有 freebusy 相關記錄
2. 確認查詢與建立使用同一個 Calendar ID
3. 手動執行 freebusy query 測試，確認返回值是否正確
4. 檢查時區轉換邏輯

**預防措施：**
- 在 skill config 中明確設定 freebusy 為 enabled
- 所有時間統一用 ISO 8601 格式含時區
- 建立預約前強制執行衝突檢查

---

### 確認訊息沒送出

**症狀描述：** 預約建立成功但客戶沒收到確認訊息。

**可能原因：**
- 通知管道未設定（Telegram bot 未連線或 Email 未授權）
- 確認訊息模板為空
- 客戶聯絡資訊缺失

**排除步驟：**
1. 確認通知管道設定：檢查 `business_profile_form.md` 中的通知設定
2. 確認訊息模板存在且格式正確
3. 檢查客戶資料中是否有有效的聯絡方式
4. 查看通知模組日誌：`docker-compose logs | grep -i notify`

**預防措施：**
- 安裝時確認通知管道已連通
- 設定預設確認訊息模板
- 預約流程中強制要求填寫聯絡方式

---

## Module 02：Email

### 無法讀取信件

**症狀描述：** Email 模組無法存取 Gmail 收件匣，返回授權錯誤。

**可能原因：**
- Gmail API 未啟用
- OAuth scopes 不包含 `gmail.readonly`
- Token 過期
- Google 帳號安全設定阻擋

**排除步驟：**
1. 確認 Gmail API 已啟用：Google Cloud Console → APIs & Services → Gmail API
2. 確認 OAuth scopes 包含 `https://www.googleapis.com/auth/gmail.readonly`
3. 刪除舊 token 並重新授權：移除 token 檔案後重新執行授權流程
4. 檢查 Google 帳號是否有「不安全應用程式」的阻擋通知
5. 查看日誌：`docker-compose logs | grep -i gmail`

**預防措施：**
- 使用 `/install-email` 自動設定所有 Gmail 權限
- 課前確認 token 有效
- 使用 Google Workspace 帳號避免安全設定問題

---

### Draft 沒出現

**症狀描述：** 系統說已建立草稿，但 Gmail 草稿匣中找不到。

**可能原因：**
- OAuth scopes 不包含 `gmail.compose`
- Draft 建立 API 呼叫失敗但未正確回報錯誤
- 瀏覽器快取導致草稿匣未更新

**排除步驟：**
1. 確認 OAuth scopes 包含 `https://www.googleapis.com/auth/gmail.compose`
2. 查看 API 回應日誌，確認 Draft ID 是否有返回
3. 重新整理 Gmail 頁面或用 Gmail API 直接查詢草稿列表
4. 重新授權，確保包含 compose scope

**預防措施：**
- 授權時一次勾選 `gmail.readonly` + `gmail.compose`
- 建立 Draft 後立即查詢確認
- 保留 API 回應日誌用於除錯

---

### 分類不準確

**症狀描述：** Email 自動分類結果與預期不符，重要信件被歸錯類。

**可能原因：**
- `email_triage_skill` 的分類規則 prompt 不夠精確
- 分類關鍵字設定不完整
- 信件內容與預設類別不匹配

**排除步驟：**
1. 查看分類日誌，確認 AI 的分類依據
2. 調整 `business_profile_form.md` 中的分類規則與關鍵字
3. 在 email triage skill 的 prompt 中增加更多範例
4. 針對被誤分的信件類型新增專門的分類規則

**預防措施：**
- 先用 10 封信手動驗證分類準確度
- 定期更新分類關鍵字
- 設定「未分類」作為預設類別，避免強制歸類

---

## Module 03：CRM

### Notion 寫入失敗

**症狀描述：** 嘗試將客戶資料寫入 Notion Database 時失敗。

**可能原因：**
- Notion MCP 連線中斷
- OAuth token 過期
- Database ID 設定錯誤
- 欄位名稱或類型不匹配

**排除步驟：**
1. 測試 Notion MCP 連線：在 Claude Code 中執行簡單的 Notion 查詢
2. 確認 OAuth token 有效：重新授權 Notion integration
3. 確認 Database ID：Notion 頁面 URL 中的 32 字元 ID
4. 確認欄位名稱完全一致（注意大小寫與空格）
5. 查看日誌：`docker-compose logs | grep -i notion`

**預防措施：**
- 使用 `/install-crm` 自動設定 Database ID 與欄位對應
- Notion integration 授權時確保包含目標 Database
- 建立測試用的 Database 做驗證

---

### Sheets 寫入失敗

**症狀描述：** 嘗試將客戶資料寫入 Google Sheets 時失敗。

**可能原因：**
- Google Sheets API 授權問題
- Sheet ID 設定錯誤
- 欄位對應不正確（寫入的欄位順序或名稱有誤）
- Sheet 已滿或被保護

**排除步驟：**
1. 確認 Google Sheets API 已啟用
2. 確認 Sheet ID：從 Google Sheets URL 中取得
3. 確認欄位對應：檢查 skill config 中的欄位順序是否與 Sheet 一致
4. 確認 Sheet 未設定保護範圍
5. 手動在 Sheet 中新增一行測試

**預防措施：**
- 使用 `/install-crm` 自動設定 Sheet ID 與欄位
- 不要在 CRM Sheet 上設定保護範圍
- 定期備份 Sheet 資料

---

### Lead 重複建立

**症狀描述：** 同一位客戶在 CRM 中出現多筆重複記錄。

**可能原因：**
- 重複偵測規則未啟用
- 偵測欄位設定不正確（例如用姓名而非 Email 比對）
- 客戶資料格式不一致（例如電話號碼格式不同）

**排除步驟：**
1. 確認重複偵測規則已啟用：檢查 CRM skill config
2. 確認偵測欄位設定為 Email（最可靠的唯一識別欄位）
3. 手動搜尋重複記錄並合併
4. 調整資料格式標準化規則

**預防措施：**
- 以 Email 作為主要重複偵測欄位
- 寫入前自動執行重複檢查
- 定期執行重複記錄清理

---

## Module 04：客服

### Bot 不回覆

**症狀描述：** 在 Telegram 發訊息給 Bot，但 Bot 沒有任何回應。

**可能原因：**
- Telegram Bot Token 設定錯誤
- Channel / Chat ID 設定錯誤
- OpenClaw 容器未運行
- Webhook 未正確設定

**排除步驟：**
1. 確認 Bot Token 有效：`curl https://api.telegram.org/bot<TOKEN>/getMe`
2. 確認 OpenClaw 正在運行：`docker ps | grep openclaw`
3. 確認 Webhook URL 正確：`curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
4. 查看 OpenClaw 日誌：`docker-compose logs | grep -i telegram`
5. 嘗試重啟服務：`docker-compose restart`

**預防措施：**
- 安裝後立即發一條測試訊息確認 Bot 運作
- 設定 health check 定期確認 Bot 存活
- 保存 Bot Token 在安全位置（環境變數，非程式碼中）

---

### FAQ 回答不相關

**症狀描述：** 客戶問的問題有在 FAQ 中，但 Bot 回答的內容不相關或品質很差。

**可能原因：**
- 知識庫（FAQ）內容不夠詳細
- Prompt 中的指令不夠明確
- FAQ 的 Q 寫法與客戶實際問法差異太大

**排除步驟：**
1. 查看 Bot 實際收到的訊息與回應日誌
2. 對照 FAQ 內容，確認問題是否有被涵蓋
3. 更新 FAQ 的問題寫法，加入客戶常用的說法
4. 在 prompt 中加入更明確的匹配指令（例如：「如果客戶問到類似以下問題...」）

**預防措施：**
- FAQ 的 Q 至少寫 2-3 種不同問法
- 定期收集客戶實際問題更新 FAQ
- 設定 fallback 回覆：「感謝您的訊息，我將轉給真人客服為您處理」

---

### 升級通知沒送

**症狀描述：** 客戶問題超出 Bot 處理範圍，但沒有通知真人客服。

**可能原因：**
- 通知對象未設定
- `escalation_rules` 設定中的觸發條件不正確
- 通知管道（Telegram/Email）連線中斷

**排除步驟：**
1. 確認通知對象設定：檢查 `business_profile_form.md` 中的通知接收對象
2. 確認 escalation rules 的觸發條件
3. 手動觸發一次升級通知測試
4. 檢查通知管道連線狀態

**預防措施：**
- 安裝時必須設定至少一個通知接收者
- 設定多層升級機制（例：5 分鐘無回應 → 通知第二人）
- 每週測試一次升級通知流程

---

## Module 05：報告

### 報告沒自動生成

**症狀描述：** 設定了每日報告但到了指定時間沒有收到。

**可能原因：**
- Cron 排程設定錯誤
- OpenClaw 的排程功能未啟用
- 容器在排程時間未運行
- 時區設定不一致

**排除步驟：**
1. 確認排程設定：檢查 cron expression 是否正確
2. 確認 OpenClaw 排程功能狀態：`docker-compose logs | grep -i cron`
3. 確認容器運行時間涵蓋排程時間：`docker ps --format "{{.Names}} {{.Status}}"`
4. 確認時區：容器內的時區是否與預期一致
5. 手動觸發報告生成測試

**預防措施：**
- 使用 `/install-report` 自動設定排程
- 容器設定 `restart: unless-stopped` 確保持續運行
- 設定排程執行日誌，方便追蹤

---

### 報告內容為空

**症狀描述：** 報告有生成但內容是空的或只有標題框架。

**可能原因：**
- 資料來源無法存取
- `web-search-skill` 未正常運行
- 搜尋關鍵字設定不當，找不到相關內容
- API 額度不足導致搜尋失敗

**排除步驟：**
1. 手動測試 web search skill：執行一次搜尋確認有結果
2. 確認搜尋關鍵字設定：檢查 report config 中的主題和關鍵字
3. 檢查 API 額度：確認 Anthropic 和搜尋 API 都有餘額
4. 查看報告生成日誌，找出在哪個步驟失敗

**預防措施：**
- 設定多個資料來源作為備援
- 搜尋關鍵字定期更新
- 報告生成失敗時發送通知

---

### 格式不對

**症狀描述：** 報告有內容但格式混亂，不符合預期的輸出格式。

**可能原因：**
- `report_output_schema.json` 定義有誤
- Prompt 模板中的格式指令不夠明確
- AI 模型輸出超出預期長度

**排除步驟：**
1. 檢查 `report_output_schema.json` 的 schema 定義
2. 檢查 prompt 模板中的格式要求
3. 調整 prompt 加入更嚴格的格式指令（例如：markdown heading 層級、字數限制）
4. 測試不同的 prompt 版本

**預防措施：**
- 在 prompt 中加入明確的格式範例
- 設定 output 最大長度限制
- 保留一份「好的報告」範例作為 few-shot reference

---

## Module 06：通知

### 通知沒收到

**症狀描述：** 系統應該發送的通知（預約確認、升級警告、報告等）沒有收到。

**可能原因：**
- 通知管道設定錯誤
- 目前在靜默時段
- Telegram Bot 離線
- Email 被歸入垃圾信

**排除步驟：**
1. 確認通知管道設定：檢查 `business_profile_form.md` 中的通知設定
2. 確認目前時間是否在靜默時段內
3. 確認 Telegram Bot 運作：發一條測試訊息
4. 檢查 Email 垃圾信匣
5. 查看通知模組日誌：`docker-compose logs | grep -i notify`

**預防措施：**
- 安裝後立即測試所有通知管道
- 靜默時段設定後發一條確認通知
- 將通知寄件者加入 Email 白名單

---

### 重複通知

**症狀描述：** 同一件事收到多次通知。

**可能原因：**
- 已知的 OpenClaw cron issue：排程任務重複觸發
- 多個模組同時觸發同一通知
- 容器重啟後排程重複註冊

**排除步驟：**
1. 查看通知日誌，確認重複的時間間隔
2. 檢查 cron 排程是否有重複註冊：`docker-compose logs | grep -i schedule`
3. 降低排程頻率（例：從每分鐘改為每 5 分鐘）
4. 如果是 known issue，改用手動觸發替代自動排程

**預防措施：**
- 通知系統加入 deduplication 機制（相同事件 ID 不重複發送）
- 使用較長的排程間隔
- 重啟容器後檢查排程註冊狀態

---

### 紀錄沒寫入

**症狀描述：** 通知有成功發送，但 CRM 中沒有對應的互動紀錄。

**可能原因：**
- CRM 連線中斷
- 寫入權限不足
- 紀錄寫入的欄位對應錯誤

**排除步驟：**
1. 確認 CRM 連線：手動執行一次 CRM 寫入測試
2. 確認寫入權限：檢查 OAuth scopes
3. 確認欄位對應：檢查通知模組的 CRM 欄位設定
4. 查看日誌中是否有 CRM 寫入相關的錯誤訊息

**預防措施：**
- 通知發送與 CRM 寫入設計為同一交易，一起成功或一起失敗
- CRM 連線中斷時將紀錄暫存，恢復後補寫
- 定期比對通知日誌與 CRM 紀錄

---

## 緊急處理

### AI 行為失控（亂回覆/亂發信）

**症狀描述：** AI 開始回覆不相關的內容、發送非預期的 Email、或做出其他非預期行為。

**可能原因：**
- Prompt injection（惡意使用者透過訊息注入指令）
- Skill 設定被意外修改
- System prompt 被覆蓋

**立即處理（30 秒內完成）：**
1. **立即停止 OpenClaw 容器：** `docker-compose stop`
2. 不要嘗試修復——先停止一切
3. 確認已停止：`docker ps` 確認沒有運行中的容器

**事後排查：**
1. 查看日誌找出異常開始的時間點：`docker-compose logs --since="1h"`
2. 檢查 skill 設定是否被修改：`git diff` 檢查所有設定檔
3. 檢查 system prompt 是否被覆蓋
4. 確認沒有未授權的 skill 被安裝
5. 修復後在隔離環境測試，確認正常再重新上線

**預防措施：**
- 遵守權限最小化原則（見 `best_practices.md` 第 4 點）
- Email 先走 Draft 不走 Auto-send
- 設定 rate limit 限制 AI 每小時最大操作次數
- 使用版本控制追蹤所有設定檔變更

---

### API Key 洩露

**症狀描述：** 發現 API Key 出現在不應該出現的地方（公開 repo、日誌、截圖等）。

**可能原因：**
- API Key 被寫在程式碼中而非環境變數
- docker-compose.yml 被意外推送到公開 repo
- 日誌中輸出了包含 API Key 的錯誤訊息

**立即處理（5 分鐘內完成）：**
1. **立即 Revoke 被洩露的 Key：**
   - Anthropic：https://console.anthropic.com/settings/keys → 刪除該 Key
   - Google：https://console.cloud.google.com/apis/credentials → 刪除該 Key
2. **重新生成新的 Key**
3. **更新所有使用該 Key 的環境變數**
4. **重啟所有服務：** `docker-compose down && docker-compose up -d`

**事後排查：**
1. 檢查洩露的 Key 是否有異常使用紀錄
2. 確認 docker-compose.yml 中的環境變數是否使用 `.env` 檔案
3. 確認 `.env` 是否在 `.gitignore` 中
4. 檢查所有日誌設定，確保不會輸出敏感資訊

**預防措施：**
- API Key 永遠放在 `.env` 檔案中，透過 `docker-compose.yml` 的 `env_file` 引用
- `.env` 必須在 `.gitignore` 中
- 定期 rotate API Key（每 90 天）
- 使用 git 的 pre-commit hook 防止提交敏感資訊

---

### 費用暴增

**症狀描述：** API 使用費用突然大幅增加。

**可能原因：**
- 排程任務頻率過高
- AI 進入無限迴圈
- 惡意使用者大量觸發 API 呼叫
- 未設定 rate limit

**立即處理：**
1. **暫停所有排程任務：** `docker-compose stop`
2. 登入各 API 平台查看用量明細
3. 找出異常用量的來源（哪個 API、哪個時間段）

**事後排查：**
1. 分析日誌找出高頻呼叫的來源
2. 檢查 cron 排程設定是否合理
3. 檢查是否有迴圈呼叫（A 觸發 B、B 觸發 A）
4. 確認 rate limit 設定

**預防措施：**
- 設定每日 API 呼叫上限
- 設定費用警報（Anthropic Console、Google Cloud Billing）
- 排程任務使用合理的間隔（最低 5 分鐘）
- 監控 API 使用趨勢，異常時自動暫停
- 課堂帳號與正式帳號完全分開
