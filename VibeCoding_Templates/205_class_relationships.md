# 類別關係圖 (Class Relationships)

---

**版本:** `v1.0`
**狀態:** `[草案 / 執行中]`

---

## 1. 概觀 (Overview)
定義類別 (Classes) 或組件 (Components) 的靜態結構。

## 2. 核心類別圖 (Core Class Diagram)
`[請從高階關係圖開始繪製]`

## 3. 角色與職責 (Roles)
| 類別 (Class) | 職責 (Responsibility) | 所屬模組 (Module) |
| :--- | :--- | :--- |
| `Service` | 處理業務邏輯。 | `services` |
| `Repo` | 資料存取 (Data Access)。 | `repositories` |
| `Model` | 資料結構定義。 | `models` |

## 4. 設計模式 (Patterns)
- **相依注入 (Dependency Injection)**: Service 層依賴於介面 (Interfaces)。
- **工廠模式 (Factory)**: 用於建立複雜物件。

## 5. 技術棧 (Tech Stack)
- **語言**: Python 3.11+
- **框架**: FastAPI
- **ORM**: SQLAlchemy 2.0
