# Story 摘要生成指南

本文檔說明如何在完成 Story 後生成標準化的實現摘要。

---

## 📋 摘要的目的

1. **知識保存** - 記錄實現細節，便於後續維護
2. **團隊溝通** - 讓團隊成員了解實現方式
3. **追溯性** - 提供代碼和設計決策的追溯
4. **新人入職** - 幫助新成員快速了解系統

---

## 🔧 生成方式

### 方式 1: Python 腳本 (推薦)

```bash
# 交互式模式
python scripts/generate_story_summary.py --interactive

# 命令行模式
python scripts/generate_story_summary.py \
  --story S4-1 \
  --title "User Dashboard" \
  --points 5

# 指定狀態
python scripts/generate_story_summary.py \
  --story S4-2 \
  --title "API Refactor" \
  --points 3 \
  --status "🔄 進行中"
```

### 方式 2: Claude AI 助手

在與 Claude 對話時使用：

```
/generate-summary
```

或直接說：
```
請為 S4-1 User Dashboard (5 points) 生成摘要
```

### 方式 3: 手動創建

1. 複製模板: `scripts/templates/story-summary-template.md`
2. 重命名為: `{STORY_ID}-{title-slug}-summary.md`
3. 放入: `docs/03-implementation/sprint-{N}/summaries/`
4. 填寫內容

---

## 📝 摘要內容結構

每個摘要應包含以下章節：

### 1. 基本信息 (必填)
```markdown
**Story ID**: S4-1
**標題**: User Dashboard
**Story Points**: 5
**狀態**: ✅ 已完成
**完成日期**: 2025-11-26
```

### 2. 驗收標準達成 (必填)
```markdown
| 驗收標準 | 狀態 | 說明 |
|---------|------|------|
| Dashboard 頁面完成 | ✅ | React 組件實現 |
| 數據 API 整合 | ✅ | REST API 調用 |
```

### 3. 技術實現 (必填)
- 主要組件說明
- 關鍵代碼片段
- API 端點 (如適用)

### 4. 代碼位置 (必填)
```markdown
backend/src/
├── api/v1/dashboard/
│   └── routes.py
frontend/src/
├── pages/Dashboard/
│   └── index.tsx
```

### 5. 測試覆蓋 (必填)
```markdown
| 測試文件 | 測試數量 | 狀態 |
|---------|---------|------|
| test_dashboard.py | 15 | ✅ |
```

### 6. 備註 (選填)
- 特殊實現考慮
- 已知限制
- 未來改進建議

---

## 📁 文件命名規範

### 格式
```
{STORY_ID}-{title-slug}-summary.md
```

### 示例
| Story | 標題 | 文件名 |
|-------|------|--------|
| S4-1 | User Dashboard | S4-1-user-dashboard-summary.md |
| S4-2 | API Refactor | S4-2-api-refactor-summary.md |
| S5-1 | E2E Tests | S5-1-e2e-tests-summary.md |

---

## 📂 目錄結構

```
docs/03-implementation/
├── sprint-0/
│   ├── README.md              # Sprint 概覽
│   ├── summaries/             # Story 摘要
│   │   ├── S0-1-xxx-summary.md
│   │   └── S0-2-xxx-summary.md
│   ├── issues/                # 問題記錄
│   └── decisions/             # 技術決策 (ADR)
├── sprint-1/
│   ├── README.md
│   └── summaries/
├── sprint-2/
├── sprint-3/
├── sprint-4/
└── sprint-5/
```

---

## ⏰ 何時生成摘要

### 必須生成
- Story 完成並通過 Code Review 後
- Story 狀態更新為 "completed" 時

### 建議生成
- 複雜實現完成後立即記錄
- Sprint Review 前確保所有摘要完成

---

## ✅ 檢查清單

生成摘要後，請確認：

- [ ] 基本信息準確
- [ ] 所有驗收標準已列出
- [ ] 技術實現描述清楚
- [ ] 代碼位置正確
- [ ] 測試數量和狀態正確
- [ ] 文件保存到正確位置
- [ ] Sprint README.md 已更新連結

---

## 🔗 相關資源

- [摘要模板](../../scripts/templates/story-summary-template.md)
- [生成腳本](../../scripts/generate_story_summary.py)
- [Sprint 狀態追蹤](sprint-status.yaml)
- [AI 助手指令](../../claudedocs/AI-ASSISTANT-INSTRUCTIONS.md)

---

**最後更新**: 2025-11-26
