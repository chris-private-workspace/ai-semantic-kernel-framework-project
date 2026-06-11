# PROMPT-02: NEW TASK PREPARATION
# 新開發任務準備

> **用途**: 準備開始新的開發任務,理解需求和技術背景
> **變數**: `{TASK_ID}` 或任務描述
> **預估時間**: 3-5 分鐘
> **版本**: v3.0.0

---

## 🔤 變數定義

```yaml
{TASK_ID}:
  描述: 任務標識符或任務描述
  格式: 自由格式，可以是功能名稱、Bug ID、或任務描述
  範例:
    - "add-user-profile-api"
    - "fix-login-redirect"
    - "optimize-database-queries"
    - "implement F5 learning feature"
```

---

## 🎯 執行步驟

### Step 1: 理解任務背景

```yaml
讀取相關文檔:
  - docs/03-implementation/sprint-planning/README.md (功能總覽)
  - docs/01-planning/prd/prd-main.md (產品需求)
  - CLAUDE.md (開發指南)

確定任務類型:
  - 新功能開發 (Feature)
  - Bug 修復 (Bugfix)
  - 性能優化 (Optimization)
  - 代碼重構 (Refactor)
  - 文檔更新 (Documentation)
```

### Step 2: 識別相關代碼

```yaml
搜索策略:
  - 使用 Grep 搜索相關關鍵字
  - 使用 Glob 查找相關文件
  - 閱讀相關模組的代碼結構

後端代碼目錄:
  - backend/src/api/v1/     # API 路由
  - backend/src/domain/     # 業務邏輯
  - backend/src/infrastructure/  # 基礎設施

前端代碼目錄:
  - frontend/src/pages/     # 頁面組件
  - frontend/src/components/ # UI 組件
  - frontend/src/services/  # API 服務
```

### Step 3: 讀取技術架構文檔

```yaml
文件路徑:
  - docs/02-architecture/technical-architecture.md
  - docs/02-architecture/technical-architecture-part2.md

關注:
  - 與任務相關的架構設計
  - 技術選型決策
  - 接口規範
  - 數據模型
```

### Step 4: 檢查依賴項

```yaml
依賴檢查:
  - 相關 API 是否已實現
  - 相關數據模型是否存在
  - 相關 UI 組件是否可用
  - 測試環境是否準備好

輸出依賴檢查結果:
  ✅ 用戶 API 已就緒
  ✅ 數據庫模型已存在
  ⚠️ 前端組件需要創建
  ❌ 需要先完成認證模組
```

---

## 📤 輸出格式

```markdown
# 任務準備報告: {TASK_ID}

**生成時間**: {TIMESTAMP}
**生成者**: AI Assistant (PROMPT-02)

---

## 📊 任務基本信息

| 項目 | 內容 |
|------|------|
| **任務 ID** | {TASK_ID} |
| **任務類型** | {TASK_TYPE} (Feature/Bugfix/Optimization/Refactor) |
| **複雜度** | {COMPLEXITY} (Low/Medium/High) |
| **預估工作量** | {EFFORT_ESTIMATE} |
| **優先級** | {PRIORITY} |

---

## 📋 需求摘要

### 任務描述
{TASK_DESCRIPTION}

### 驗收標準
1. {ACCEPTANCE_CRITERIA_1}
2. {ACCEPTANCE_CRITERIA_2}
3. {ACCEPTANCE_CRITERIA_3}

### 功能要求
- {FUNCTIONAL_REQUIREMENT_1}
- {FUNCTIONAL_REQUIREMENT_2}

### 非功能要求
- {NON_FUNCTIONAL_REQUIREMENT_1}
- {NON_FUNCTIONAL_REQUIREMENT_2}

---

## 🔧 技術背景

### 相關代碼位置
- **API**: `backend/src/api/v1/{module}/routes.py`
- **業務邏輯**: `backend/src/domain/{module}/service.py`
- **前端頁面**: `frontend/src/pages/{module}/`

### 相關架構組件
- **組件**: {COMPONENT_NAME}
- **技術棧**: {TECH_STACK}
- **接口**: {API_INTERFACE}

### 技術參考文檔
- [技術架構](../../docs/02-architecture/technical-architecture.md)
- [Sprint 計劃總覽](../../docs/03-implementation/sprint-planning/README.md)
- [PRD 功能規格](../../docs/01-planning/prd/prd-main.md)

---

## ⚠️ 依賴項檢查

{DEPENDENCY_CHECK_RESULTS}

---

## ✅ 準備檢查清單

環境準備:
- [ ] 本地開發環境已啟動 (docker-compose up -d)
- [ ] 後端 API 運行正常 (localhost:8000)
- [ ] 前端開發服務器運行正常 (localhost:3000)
- [ ] 相關文檔已閱讀

依賴確認:
- [ ] 相關 API 接口已就緒
- [ ] 相關數據模型已存在
- [ ] 測試環境已準備

代碼準備:
- [ ] 創建 feature branch
- [ ] 了解相關代碼位置
- [ ] 熟悉現有代碼模式

---

## 🚀 下一步行動

1. ✅ 任務準備完成,可以開始開發
2. ⏭️ 執行 `@PROMPT-04-SPRINT-DEVELOPMENT.md {TASK_ID}`
3. 📋 或查看技術文檔進行深入研究

---

## 📚 相關資源

- [技術架構](../../docs/02-architecture/technical-architecture.md)
- [開發指南](../../docs/03-implementation/local-development-guide.md)
- [CLAUDE.md](../../CLAUDE.md)

---

**生成工具**: PROMPT-02
**版本**: v3.0.0
```

---

## 💡 使用範例

```bash
# 準備開發新功能
用戶: "@PROMPT-02-NEW-SPRINT-PREP.md implement-user-profile"

AI 執行:
1. 讀取 PRD 和架構文檔
2. 識別相關代碼位置
3. 檢查依賴項
4. 生成準備報告

輸出:
---
📋 任務準備完成

任務: implement-user-profile
類型: Feature
複雜度: Medium

需求摘要:
- 創建用戶個人資料 API
- 支持頭像上傳
- 支持基本信息編輯

相關代碼:
- API: backend/src/api/v1/users/
- 前端: frontend/src/pages/profile/

依賴檢查:
✅ 用戶認證 API 已就緒
✅ 文件上傳服務已實現
⚠️ 需要創建前端頁面

準備就緒: ✅
下一步: @PROMPT-04 implement-user-profile
---
```

---

## 🔗 相關文檔

- [AI Assistant Instructions](../AI-ASSISTANT-INSTRUCTIONS.md)
- [PROMPT-04: Development](./PROMPT-04-SPRINT-DEVELOPMENT.md)
- [Sprint Planning README](../../docs/03-implementation/sprint-planning/README.md)

---

**版本**: v3.0.0
**更新日期**: 2025-12-01
