# 開發者指南 (Developer Cookbook)

---

**版本:** `v1.0`
**更新日期:** `2026-01-16`
**狀態:** `Active`

---

## 1. 快速參考 (Quick Refs)

- **工作流 (Workflow)**: [100_workflow_manual.md](./100_workflow_manual.md)
- **結構範例 (Structure)**: [101_project_structure_guide.md](./101_project_structure_guide.md)
- **API 標準**: [102_api_design_standards.md](./102_api_design_standards.md)
- **審核標準 (Review)**: [106_code_review_guide.md](./106_code_review_guide.md)
- **前端規範 (Frontend)**: [103_frontend_guidelines.md](./103_frontend_guidelines.md)

## 2. 常見任務 (Common Tasks)

### 開始新功能 (Starting a New Feature)

1. **規劃 (Plan)**: 閱讀 PRD ([200_project_brief_prd.md](../VibeCoding_Templates/200_project_brief_prd.md))。
2. **規格 (Spec)**: 撰寫 BDD ([105_bdd_guide.md](./105_bdd_guide.md))、API Spec ([207_api_spec.md](../VibeCoding_Templates/207_api_spec.md)) 或 Frontend Spec ([208_frontend_specification.md](../VibeCoding_Templates/208_frontend_specification.md))。
3. **設計 (Design)**: 視需求更新架構設計 ([202_architecture_design.md](../VibeCoding_Templates/202_architecture_design.md))。

### 撰寫程式碼 (Writing Code)

- **風格 (Style)**: AI 生成內容請遵循 `900_output_style.md`。
- **測試 (Tests)**: `tests/` 的目錄結構應與 `src/` 對齊。
- **提交 (Commits)**: 使用 `type(scope): description` (例如：`feat(auth): add login`)。

### 部署 (Deployment)

- **檢查 (Check)**: 執行 `107_security_checklist.md`。
- **部署 (Deploy)**: 遵循 `108_ops_guide.md`。
