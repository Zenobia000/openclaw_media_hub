# 前端規格書 (Frontend Specification) - [專案名稱]

---

**版本:** `v1.0`
**日期:** `YYYY-MM-DD`
**狀態:** `[Draft / Review / Approved]`

---

## 1. 概觀 (Overview)

### 1.1 技術決策 (Tech Decisions)
- **Framework**: [Next.js / Vite]
- **Styling**: [Tailwind CSS]
- **State**: [Zustand / Context]
- **Deploy**: [Vercel / Docker]

### 1.2 核心依賴 (Key Dependencies)
- `dependency-name` (vX.X): 用途描述

---

## 2. 資訊架構 (Information Architecture)

### 2.1 網站地圖 (Sitemap)

```
Root (/)
├── [Page A]
│   └── [Sub-page A1]
└── [Page B]
```

### 2.2 路由表 (Route Table)

| 頁面名稱 | 路由路徑 | 對應元件/檔案 | 權限 (Auth) | 核心功能 |
| :--- | :--- | :--- | :--- | :--- |
| **首頁** | `/` | `HomePage.tsx` | Public | 登入入口、功能概覽 |
| **儀表板** | `/dashboard` | `Dashboard.tsx` | Private | 數據總覽 |

---

## 3. 視覺與佈局 (Design & Layout)

### 3.1 版面配置 (Layout Strategy)

- **Desktop**: [描述桌機版佈局，例如：側邊欄導航 + 頂部 Header + 內容區]
- **Mobile**: [描述手機版佈局，例如：底部 Tab Bar + 抽屜式選單]
- **RWD 斷點**: `sm: 640px`, `md: 768px`, `lg: 1024px`

### 3.2 關鍵 UI 元件 (Key UI Components)

| 元件名稱 | 功能描述 | 狀態 (Props/Variants) |
| :--- | :--- | :--- |
| **NavBar** | 全域導航列 | `userLoggedIn`, `activeTab` |
| **DataGrid** | 通用數據表格 | `loading`, `data`, `pagination` |

---

## 4. 頁面功能規格 (Page Specifications)

### 4.1 [頁面 A 名稱]

**使用者故事 (User Story)**:
> 身為 [角色], 我想要 [行動], 以便 [目標]。

**UI 區域 (UI Zones)**:
1.  **Header**: [元素與互動]
2.  **Body**: [元素與互動]
3.  **Footer**: [元素與互動]

**驗收標準 (Acceptance Criteria)**:
- [ ] 載入時顯示 Skeleton。
- [ ] 成功後顯示數據列表。
- [ ] 錯誤時顯示 Toast 提示。

### 4.2 [頁面 B 名稱]

*(依此類推)*

---

## 5. API 整合策略 (API Integration)

- **Client**: [Axios / Fetch]
- **Data Features**:
  - Auth Token 處理方式: [Cookies / LocalStorage]
  - 錯誤攔截 (Interceptor): 統一處理 401/403/500 錯誤。
  - Caching 策略: [React Query 設定]
