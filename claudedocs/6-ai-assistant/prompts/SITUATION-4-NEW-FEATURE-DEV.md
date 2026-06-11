# 🆕 情況4: 新功能開發

> **使用時機**: 對話進行中，正在開發全新功能
> **目標**: 系統化開發，符合架構標準
> **適用場景**: Epic Story 實施, 新模組開發

---

## 📋 Prompt 模板

```markdown
我正在開發新功能: [功能名稱]

根據: [Epic X Story X.X / 用戶需求 / 設計文檔]

請幫我:

1. 建立功能規劃目錄
   - 在 claudedocs/1-planning/features/ 建立 FEAT-XXX-[功能名稱] 目錄
   - 建立 01-requirements.md (需求規格)
   - 建立 02-technical-design.md (技術設計)
   - 建立 03-implementation-plan.md (實施計劃)
   - 建立 04-progress.md (進度追蹤)

2. 確認規劃文檔
   - 閱讀 archived/docs-v1/03-implementation/sprint-execution/[相關 Sprint]
   - 確認驗收標準

3. 系統化開發
   - 後端: Domain 模型 → Service → API → 測試
   - 使用 TodoWrite 追蹤進度

4. 遵循最佳實踐
   - 參考現有實現模式
   - 撰寫單元測試

5. 記錄開發過程
   - 更新 04-progress.md
   - 記錄技術決策

請用中文溝通。
```

---

## 🤖 AI 執行流程

### Phase 0: 規劃準備 (必須先執行)

```bash
# 1. 確認功能編號（查看現有 FEAT 編號）
Bash: ls claudedocs/1-planning/features/

# 2. 建立功能目錄結構
Bash: mkdir -p claudedocs/1-planning/features/FEAT-XXX-功能名稱

# 3. 建立規劃文檔
Write: claudedocs/1-planning/features/FEAT-XXX-功能名稱/01-requirements.md
Write: claudedocs/1-planning/features/FEAT-XXX-功能名稱/02-technical-design.md
Write: claudedocs/1-planning/features/FEAT-XXX-功能名稱/03-implementation-plan.md
Write: claudedocs/1-planning/features/FEAT-XXX-功能名稱/04-progress.md
```

**功能目錄結構範例：**
```
claudedocs/1-planning/features/
├── FEAT-001-agent-management/
│   ├── 01-requirements.md      # 需求規格
│   ├── 02-technical-design.md  # 技術設計
│   ├── 03-implementation-plan.md # 實施計劃
│   └── 04-progress.md          # 進度追蹤
├── FEAT-002-workflow-engine/
│   └── ...
└── FEAT-003-新功能/
    └── ...
```

**文檔內容指引：**

| 文檔 | 內容 |
|------|------|
| `01-requirements.md` | 功能概述、用戶需求、功能需求、驗收標準 |
| `02-technical-design.md` | 數據模型、API 設計、組件設計、技術架構 |
| `03-implementation-plan.md` | 開發階段、任務分解、依賴關係 |
| `04-progress.md` | 開發日誌、完成狀態、問題記錄、測試結果 |

---

### Phase 1: 後端開發

```bash
# 1. Domain Layer (業務邏輯)
Write: backend/src/domain/{module}/models.py
Write: backend/src/domain/{module}/service.py
Write: backend/src/domain/{module}/__init__.py

# 2. API Layer (HTTP 路由)
Write: backend/src/api/v1/{module}/schemas.py
Write: backend/src/api/v1/{module}/routes.py
Write: backend/src/api/v1/{module}/__init__.py
Edit: backend/src/api/v1/__init__.py (合併 router)

# 3. Infrastructure Layer (如需數據庫)
Edit: backend/src/infrastructure/database/models/{module}.py
Write: backend/src/infrastructure/database/repositories/{module}_repository.py

# 4. 更新進度
Edit: claudedocs/1-planning/features/FEAT-XXX/04-progress.md
TodoWrite: 標記後端任務完成
```

### Phase 2: 測試開發

```bash
# 1. 單元測試
Write: backend/tests/unit/domain/test_{module}_service.py
Write: backend/tests/unit/api/v1/test_{module}_routes.py

# 2. 運行測試
Bash: cd backend && pytest tests/unit/domain/test_{module}_service.py -v
Bash: cd backend && pytest tests/unit/api/v1/test_{module}_routes.py -v

# 3. 代碼品質
Bash: cd backend && black src/domain/{module}/ src/api/v1/{module}/
Bash: cd backend && isort src/domain/{module}/ src/api/v1/{module}/
Bash: cd backend && flake8 src/domain/{module}/ src/api/v1/{module}/

# 4. 更新進度
Edit: claudedocs/1-planning/features/FEAT-XXX/04-progress.md
TodoWrite: 標記測試任務完成
```

### Phase 3: 整合驗證

```bash
# 1. 運行完整測試
Bash: cd backend && pytest tests/unit/ -k "{module}" -v

# 2. 類型檢查
Bash: cd backend && mypy src/domain/{module}/ src/api/v1/{module}/

# 3. 記錄測試結果
Edit: claudedocs/1-planning/features/FEAT-XXX/04-progress.md
```

---

## 📐 開發標準 Checklist

### 規劃階段
- [ ] 功能目錄已建立 (FEAT-XXX-功能名稱/)
- [ ] 01-requirements.md 已完成
- [ ] 02-technical-design.md 已完成
- [ ] 03-implementation-plan.md 已完成
- [ ] 04-progress.md 已初始化

### 後端標準
- [ ] Domain 模型遵循命名規範
- [ ] Service 包含業務邏輯驗證
- [ ] API 使用 Pydantic 驗證
- [ ] 錯誤處理完整
- [ ] 單元測試覆蓋率 >80%

### 代碼品質
- [ ] Black 格式化通過
- [ ] isort 排序通過
- [ ] Flake8 無錯誤
- [ ] mypy 類型檢查通過 (如可能)
- [ ] 註解完整 (複雜邏輯)

---

## 📁 功能文檔模板

### 01-requirements.md 模板
```markdown
# FEAT-XXX: [功能名稱]

> **建立日期**: YYYY-MM-DD
> **狀態**: 📋 設計中 / 🚧 開發中 / ✅ 完成
> **優先級**: High / Medium / Low

## 1. 功能概述
### 1.1 背景
### 1.2 目標

## 2. 功能需求
### 2.1 用戶故事
### 2.2 功能列表

## 3. 驗收標準
### 3.1 功能驗收
### 3.2 技術驗收

## 4. 相關文檔
```

### 04-progress.md 模板
```markdown
# FEAT-XXX: [功能名稱] - 開發進度

## 📊 整體進度
- [ ] Phase 0: 規劃準備
- [ ] Phase 1: 後端開發
- [ ] Phase 2: 測試開發
- [ ] Phase 3: 整合驗證

## 📝 開發日誌

### YYYY-MM-DD
- 完成項目:
- 遇到問題:
- 下一步:

## 🐛 問題追蹤
| 問題 | 狀態 | 解決方案 |
|------|------|----------|

## ✅ 測試結果
```

---

## ✅ 驗收標準

新功能開發完成後，應該確認:

1. **功能完整**
   - 所有需求都已實現
   - 代碼符合 IPA Platform 架構模式

2. **測試通過**
   - 單元測試全部通過
   - 測試覆蓋主要場景

3. **代碼品質**
   - Black 格式化通過
   - Flake8 無錯誤
   - 無明顯的安全問題

4. **文檔更新**
   - FEAT 進度文檔更新
   - TodoWrite 狀態更新

---

## 🔗 相關文檔

### 開發流程指引
- [情況1: 專案入門](./SITUATION-1-PROJECT-ONBOARDING.md)
- [情況2: 開發前準備](./SITUATION-2-FEATURE-DEV-PREP.md)
- [情況3: 舊功能進階/修正](./SITUATION-3-FEATURE-ENHANCEMENT.md)
- [情況5: 保存進度](./SITUATION-5-SAVE-PROGRESS.md)

---

**維護者**: AI 助手 + 開發團隊
**最後更新**: 2025-12-27
**版本**: 2.0
