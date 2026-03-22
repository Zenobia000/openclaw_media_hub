# 程式碼審閱指南 (Code Review Guide)

---

**版本:** `v1.0`
**更新日期:** `2026-01-16`
**狀態:** `Active`

---

## 1. 審閱流程 (Process)
1. **前置準備 (Prequel)**: 測試必須通過，且已完成自我檢查 (Self-Review)。
2. **正式審閱 (Review)**: 需獲得同儕核准 (Peer approval)。
3. **合併 (Merge)**: CI 檢查必須為綠燈。

## 2. 檢查清單 (Checklist)
- **程式品質**: 易讀嗎？好維護嗎？風格一致嗎？
- **架構設計**: 符合 SOLID 原則？職責是否有正確分離？
- **邏輯正確**: 有無明顯 Bugs？是否有處理邊緣案例 (Edge cases)？
- **安全性**: 輸入是否已驗證？有無洩漏密鑰 (Secrets)？
- **測試覆蓋**: 是否涵蓋了關鍵路徑 (Critical paths)？

## 3. 重構時機 (Refactoring Triggers)
- **程式碼異味 (Code Smells)**: 重複程式碼、過長的方法、魔法數字 (Magic numbers)。
- **建議行動**:
  - 提取方法/變數 (Extract Method/Variable)。
  - 簡化條件邏輯。
  - 重新命名以明確表達意圖。

## 4. 審閱禮儀 (Review Etiquette)
- 給予建設性的意見。
- 區分「阻礙性問題 (Blocking)」與「小建議 (Nitpicks)」。
  - **Blocking**: 安全性風險、邏輯 Errors。
  - **Nitpick**: 格式微調、命名偏好。
