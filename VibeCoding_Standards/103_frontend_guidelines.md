# 前端開發規範 (Frontend Development Guidelines)

---

**版本:** `v1.0`
**更新日期:** `2026-01-16`
**狀態:** `Active`

---

## 1. 核心原則 (Core Principles)

- **效能優先 (Performance First)**: 核心 Web Vitals 標準 (LCP < 2.5s, CLS < 0.1, FID < 100ms)。
- **無障礙通用 (A11y)**: 遵循 WCAG 2.1 AA 標準，確保鍵盤可導航、語意化 HTML。
- **組件驅動 (Component-Driven)**: 採用原子設計 (Atomic Design) 思維，最大化重用性。
- **類型安全 (Type Safety)**: 全面使用 TypeScript，嚴禁 `any`。

## 2. 技術選型標準 (Tech Stack Standards)

| 類別                 | 標準技術                       | 備註                                          |
| :------------------- | :----------------------------- | :-------------------------------------------- |
| **框架 (Framework)** | React (Next.js or Vite)        | 視 SEO 需求選擇 Next.js (SSR) 或 Vite (SPA)。 |
| **語言 (Language)**  | TypeScript                     | 嚴格模式 (Strict Mode)。                      |
| **樣式 (Styling)**   | Tailwind CSS                   | 優先使用 Utility-first，複雜組件可搭配 CVA。  |
| **狀態 (State)**     | Zustand / TanStack Query       | Client 與 Server State 分離。                 |
| **表單 (Forms)**     | React Hook Form + Zod          | 統一驗證邏輯。                                |
| **測試 (Testing)**   | Vitest + React Testing Library | 單元測試與整合測試。                          |

## 3. 程式碼風格 (Coding Style)

- **Linting**: 必須通過 ESLint 與 Prettier 檢查。
- **Git Flow**:
  - `feat/`: 新功能
  - `fix/`: 修復 Bug
  - `refactor/`: 重構
  - `docs/`: 文件更新

## 4. 瀏覽器支援 (Browser Support)

- 支援現代瀏覽器 (Modern Browsers) 最新 2 個版本 (Chrome, Firefox, Safari, Edge)。
- 不需支援 IE。
