# 專案結構指南 (Project Structure Guide)

---

**版本:** `v1.0`
**更新日期:** `2026-01-16`
**狀態:** `Active`

---

## 1. 頂層結構 (Top-Level Structure)

```plaintext
root/
├── .github/          # CI/CD
├── configs/          # 環境變數與配置 (Env configs)
├── docs/             # 說明文件
├── scripts/          # 自動化腳本 (Makefiles, shell)
├── src/              # 原始碼
│   └── [app]/
├── tests/            # 測試程式 (結構與 src 對齊)
├── pyproject.toml    # 依賴管理 (Dependencies)
└── README.md
```

## 2. 後端結構 (Backend Structure - Python)

原始碼位於 `src/[app]/`，遵循 **整潔架構 (Clean Architecture)**。

```plaintext
src/[app]/
├── main.py           # 進入點 (Entry point)
├── core/             # 共用模組 (Config, Security)
├── domain/           # 業務邏輯 (Business Rules - 純 Python)
│   ├── models.py     # 實體模型 (Entities)
│   └── ports.py      # 介面定義 (Interfaces)
├── application/      # 使用案例 (Use Cases - 流程編排)
│   ├── services.py
│   └── dtos.py
└── infrastructure/   # 外部轉接器 (External Adapters)
    ├── web/          # 路由器與控制器 (Controllers/Routes)
    └── persistence/  # 資料庫儲存空間 (DB Repositories)
```

## 3. 前端結構 (Frontend Structure - React/TypeScript)

標準化 `src` 目錄結構，採用 **Feature-based** 架構。

```plaintext
src/
├── assets/      # 靜態資源 (Images, Fonts)
├── components/  # 共用組件 (Base UI)
│   ├── ui/      # 原子組件 (Button, Input)
│   └── shared/  # 複合組件 (Header, Footer)
├── features/    # 業務功能模組
│   └── [feature]/
│       ├── components/
│       ├── hooks/
│       └── api/
├── hooks/       # 全域 Custom Hooks
├── layouts/     # 頁面佈局
├── lib/         # 工具函式庫 (Utils) 與設定
├── pages/       # 路由頁面 (或 app/ )
├── services/    # API 客戶端
├── stores/      # 全域狀態
└── types/       # 全域型別
```

## 4. 命名規範 (Naming Convention)

### 通用 (General)

- **目錄 (Directories)**: `kebab-case`
- **測試 (Tests)**: 使用 `test_` 前綴 (Python) 或 `.test.tsx` (JS/TS)

### 後端 (Backend - Python)

- **文件 (Files)**: `snake_case`
- **變數/函數 (Variables/Functions)**: `snake_case`
- **類別 (Classes)**: `PascalCase`

### 前端 (Frontend - TS/React)

- **組件 (Components)**: `PascalCase` (e.g., `SubmitButton.tsx`)
- **Hook/函數 (Functions)**: `camelCase` (e.g., `useAuth`)
- **常數 (Constants)**: `UPPER_SNAKE_CASE`
