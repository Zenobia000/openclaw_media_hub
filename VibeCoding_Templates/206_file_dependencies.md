# 檔案依賴關係 (File Dependencies)

---

**版本:** `v1.0`
**狀態:** `[草案 / 執行中]`

---

## 1. 概觀 (Overview)
確保依賴結構健康，呈現有向無環圖 (DAG)。

## 2. 核心原則 (Core Principles)
- **DIP (相依反轉原則)**: 依賴於抽象而非實作。
- **ADP (無環依賴原則)**: 嚴禁循環依賴。
- **SDP (穩定依賴原則)**: 朝向穩定的模組進行依賴。

## 3. 分層架構 (Layered Architecture)
`Presentation -> Application -> Domain <- Infrastructure`

## 4. 依賴規範 (Dependency Rules)
1. **單向性**: 上層依賴於下層。
2. **反轉性**: Infrastructure 層實作 Domain 層定義的介面。
3. **無循環**: 嚴格遵守 DAG。

## 5. 模組定義 (Modules)
- **API**: 提供端點 (Endpoints)。
- **Services**: 處理業務邏輯。
- **Domain**: 定義實體 (Entities)。
- **Infra**: 處理資料庫或外部操作。

## 6. 外部依賴 (External Deps)
| 程式庫 (Lib) | 版本 | 用途 |
| :--- | :--- | :--- |
| `FastAPI` | 0.109+ | Web 框架 |
| `Pydantic` | 2.x | 資料驗證 (Validation) |
