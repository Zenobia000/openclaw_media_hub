# 模組規格與測試案例 (Module Spec & Test Cases)

---

**版本:** `v1.0`
**狀態:** `[草案 / 已核准]`

---

## 1. 模組名稱: [Name]

**相關 BDD**: [連結至 .md 文件]

## 2. 函式名稱: [Name]

**功能描述**: [此函式具體要做什麼？]

### 契約式設計 (Design by Contract - DbC)

- **前置條件 (Preconditions)**:
  1. `arg1` > 0
  2. `arg2` 不可為 null
- **後置條件 (Postconditions)**:
  1. 回傳值必須為 X。
  2. 狀態 Y 必須已更新。
- **不變量 (Invariants)**:
  1. 總額 (Total) 永遠不可為負數。

## 3. 測試案例 (TDD)

### TC-01: 正向流程 (Happy Path)

- **準備 (Arrange)**: 初始化物件。
- **執行 (Act)**: 呼叫方法。
- **斷言 (Assert)**: 檢查結果是否正確。

### TC-02: 邊緣案例 (Edge Case)

- **描述**: [案例描述]
- **斷言 (Assert)**: [預期行為]
