# BDD 指南 (BDD Guide)

---

**版本:** `v1.0`
**更新日期:** `2026-01-16`
**狀態:** `Active`

---

## 1. 核心原則 (Principles)

1. **對話優先**: 在寫程式前先達成共識。
2. **由外而內 (Outside-In)**: 從使用者行為推導至系統實作。
3. **通用語言 (Ubiquitous Language)**: 保持術語一致。

## 2. Gherkin 語法

- `Feature`: 高階功能描述 (Epic)。
- `Scenario`: 具體的測試情境。
- `Given`: 初始脈絡/前置條件 (Arrange)。
- `When`: 事件/動作 (Act)。
- `Then`: 預期結果 (Assert)。
- `Background`: 共用的 `Given`。
- `Scenario Outline` + `Examples`: 資料驅動測試。

## 3. 範本 (Template)

**路徑:** `docs/bdd/[feature_name].md`

```gherkin
Feature: 使用者身分驗證 (User Authentication)

  Background:
    Given 我是訪客
    And 我在 "/login" 頁面

  @smoke
  Scenario: 登入成功
    When 我輸入 "user@example.com" 與 "pass123"
    Then 我應該被導入 "/dashboard"

  @edge
  Scenario Outline: 欄位檢核
    When 我輸入 "<email>"
    Then 我看到錯誤訊息 "<msg>"

    Examples:
      | email | msg |
      |       | 必填 |
```

## 4. 最佳實踐 (Best Practices)

- **原子性 (Atomic)**: 一個情境只描述一種行為。
- **宣告式 (Declarative)**: 描述狀態 (如 `Then 我看到儀表板`)，而非實作細節 (如 `Then 驗證網址`)。
- **避免 UI 細節**: 不要寫「點擊藍色按鈕」。

## 5. AI 提示詞規則 (AI Prompt Rule)

**提示詞**: "根據 PRD 為 [模組名稱] 撰寫 BDD 情境。"
**規則**:

1. 路徑: `docs/bdd/[feature].md`
2. 關鍵字: 維持英文 (`Feature`, `Given`...)
3. 內容: 繁體中文 (或專案語言)
