# API 設計標準 (API Design Standards)

---

**版本:** `v1.0`
**更新日期:** `2026-01-16`
**狀態:** `Active`

---

## 1. 核心標準 (Core Standards)
- **設計風格**: RESTful, Resource-oriented.
- **格式**: JSON (`application/json`), 字元集使用 UTF-8。
- **日期與時間**: ISO 8601 UTC 格式 (`YYYY-MM-DDThh:mm:ssZ`)。
- **命名規範**: 
  - URL Resources: 使用 `kebab-case` (例如 `/user-profiles`)
  - JSON Fields: 使用 `snake_case` (例如 `user_id`)

## 2. 標頭 (Headers)
- **請求 (Request)**: `Authorization: Bearer <token>`, `X-Request-ID`。
- **回應 (Response)**: `X-Request-ID`。

## 3. 行為規範 (Behavior)
- **分頁 (Pagination)**: 建議使用 Cursor-based (`limit`, `starting_after`)。
- **排序 (Sorting)**: `sort_by=field` 或 `sort_by=-field` (遞減)。
- **篩選 (Filtering)**: `?status=active`。
- **安全性**: 限定 HTTPS (TLS 1.2+)。

## 4. 錯誤處理 (Error Handling)
**回應格式**:
```json
{
  "error": {
    "code": "resource_not_found",
    "message": "User not found",
    "request_id": "123-abc"
  }
}
```

## 5. 版本控管 (Versioning)
- **策略**: 於 URL 路徑中定義 (例如 `/v1/...`)。
- **毀滅性變更 (Breaking Changes)**: 必須發佈新的主版本號。
- **非毀滅性變更**: 允許在現有版本中新增欄位或資源。
