# Story Summary Generator

當用戶請求生成 Story 摘要時，請按照以下步驟操作：

## 觸發條件
- 用戶說 "生成摘要" 或 "generate summary"
- 用戶完成一個 Story 並需要記錄
- 用戶說 "/generate-summary"

## 執行步驟

### 1. 收集信息

首先詢問或從上下文中獲取以下信息：
- **Story ID**: 格式如 S4-1, S5-2 等
- **Story Title**: Story 的標題
- **Story Points**: 點數
- **完成日期**: 預設為今天

### 2. 讀取 Sprint 規劃獲取驗收標準

從 `archived/docs-v1/03-implementation/sprint-planning/` 讀取對應的 Sprint 規劃文件，找到該 Story 的驗收標準。

### 3. 生成摘要文件

使用以下模板生成摘要：

```markdown
# {STORY_ID}: {STORY_TITLE} - 實現摘要

**Story ID**: {STORY_ID}
**標題**: {STORY_TITLE}
**Story Points**: {POINTS}
**狀態**: ✅ 已完成
**完成日期**: {DATE}

---

## 📋 驗收標準達成情況

| 驗收標準 | 狀態 | 說明 |
|---------|------|------|
| {AC_1} | ✅ | {說明} |
| {AC_2} | ✅ | {說明} |

---

## 🔧 技術實現

### 主要組件
{描述實現的主要組件}

### 關鍵代碼
{列出關鍵代碼文件和片段}

---

## 📁 代碼位置

{列出相關代碼文件路徑}

---

## 🧪 測試覆蓋

{測試文件和測試數量}

---

## 📝 備註

{任何需要注意的事項}

---

**生成日期**: {TODAY}
```

### 4. 保存文件

將文件保存到：
```
docs/03-implementation/sprint-{N}/summaries/{STORY_ID}-{title-slug}-summary.md
```

### 5. 更新 Sprint 狀態

更新 `docs/03-implementation/sprint-status.yaml` 中對應 Story 的狀態。

## 示例對話

**用戶**: 我完成了 S4-1 User Dashboard，請生成摘要

**助手**: 好的，我來為 S4-1 生成摘要。

首先讓我讀取 Sprint 4 規劃中 S4-1 的驗收標準...

[讀取文件]

根據規劃和實際實現，我生成了以下摘要：

[顯示摘要內容]

摘要已保存到: `docs/03-implementation/sprint-4/summaries/S4-1-user-dashboard-summary.md`

是否需要我進行任何修改？
