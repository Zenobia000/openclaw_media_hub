# 維運指南 (Operations Guide)

---

**版本:** `v1.0`
**更新日期:** `2026-01-16`
**狀態:** `Active`

---

## 1. 架構規範 (Architecture)
- **環境**: Dev -> Staging -> Prod。
- **組件**: LB -> App -> DB + Cache。
- **監控**: 健康檢查 (Health checks) + 告警 (Alerts)。

## 2. CI/CD 流水線 (Pipeline)
- **建置 (Build)**: 編譯、單元測試、產生物品 (Artifacts)。
- **測試 (Test)**: 在 Staging 環境進行整合性測試 (Integration)/E2E。
- **部署 (Deploy)**: 生產環境採 藍綠部署 (Blue-Green) 或 滾動更新 (Rolling update)。

## 3. 部署檢查清單 (Deployment Checklist)
- [ ] 程式碼已核准且測試通過。
- [ ] 安全性掃描無異常。
- [ ] 資料庫遷移指令 (DB Migrations) 已就緒。
- [ ] 回滾計畫 (Rollback Plan) 已就緒。

## 4. 監控指標 (Monitoring)
- **指標 (Metrics)**: 延遲 (<500ms)、錯誤率 (<0.1%)、CPU/Mem 使用率。
- **告警 (Alerts)**: 嚴重 (Critical - 簡訊/電話)、警告 (Warning - Slack)。

## 5. 回滾機制 (Rollback)
- **觸發條件**: 錯誤率飆高或健康檢查失敗。
- **行動**: 立即回退至前一個穩定版本 (previous artifact)。

## 6. 基礎設施即程式碼 (IaC)
- 使用 Terraform 管理基礎設施。
- 使用 K8s/Docker 進行容器編排 (Orchestration)。
- **密鑰管理**: 透過 Secrets Manager 或 Vault 注入。
