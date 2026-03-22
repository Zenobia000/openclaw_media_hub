# 安全性檢查清單 (Security Checklist)

---

**版本:** `v1.0`
**更新日期:** `2026-01-16`
**狀態:** `Active`

---

## 1. 核心原則 (Principles)
- **最小權限原則 (Least Privilege)**: 僅授予執行任務所需的最小權限。
- **縱深防禦 (Defense in Depth)**: 建立多層保護機制。
- **預設安全 (Secure Defaults)**: 系統預設應為最安全狀態。

## 2. 檢查清單 (Checklist)

### 資料 (Data)
- [ ] **分類**: 資料是否已分類 (公開/機密)？
- [ ] **加密**: 傳輸中 (Transit) 使用 TLS 1.2+，靜態存儲 (At rest) 使用 AES-256。
- [ ] **隱私**: 個人識別資訊 (PII) 是否已最小化並受到保護？

### 應用程式 (Application)
- [ ] **身分驗證 (AuthN)**: 強密碼策略 (bcrypt/Argon2)、多因素驗證 (MFA)。
- [ ] **授權 (AuthZ)**: 基於角色的存取控制 (RBAC)、物件層級檢查。
- [ ] **輸入驗證 (Input)**: 防止 Injection (SQLi, XSS, Cmd)，使用參數化查詢。
- [ ] **API**: 設置速率限制 (Rate limited)、輸入驗證，避免暴露過多資料。
- [ ] **依賴項 (Deps)**: 掃描並確認無已知安全性漏洞。

### 基礎設施 (Infrastructure)
- [ ] **密鑰管理 (Secrets)**: 無寫死的 (hardcoded) 密鑰。使用 Vault 或 Secrets Manager。
- [ ] **網路**: 開放端口最小化。
- [ ] **日誌 (Logging)**: 安全事件已紀錄 (不可包含敏感密鑰)。

### 合規性 (Compliance)
- [ ] **法規**: 若適用，是否滿足 GDPR/CCPA 等法規要求？

## 3. 審閱結果 (Review Outcome)
- [ ] **發現風險**: ...
- [ ] **待辦事項 (Action Items)**: ...
- [ ] **核准通過**: [ ] 是 [ ] 否
