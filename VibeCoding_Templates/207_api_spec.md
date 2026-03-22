# API 規格書 (API Spec) - [服務名稱]

---

**版本:** `v1.0`
**文件規格書:** `[OpenAPI URL]`

---

## 1. 概觀 (Overview)
- **傳輸協定 (Protocol)**: REST / gRPC.
- **驗證方式 (Auth)**: Bearer Token.

## 2. 端點定義 (Endpoints)

### 資源名稱: `[Name]` (例如: Users)

#### `GET /users/{id}`
- **描述**: 取得使用者詳情。
- **權限需求 (Auth)**: `user.read`
- **成功回應**: `200 OK` -> 回傳 `User` 實體。

#### `POST /users`
- **描述**: 建立使用者。
- **權限需求 (Auth)**: `user.write`
- **請求主體 (Body)**: `UserCreate` 結構。
- **成功回應**: `201 Created` -> 回傳 `User` 實體。

## 3. 資料模型 (Models)
### `User`
```json
{
  "id": "uuid",
  "name": "string",
  "email": "string"
}
```

### `UserCreate`
```json
{
  "name": "string",
  "email": "string (必填)"
}
```
