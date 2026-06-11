# Sprint 執行流程指南

**版本**: v1.0.0
**創建日期**: 2025-11-20
**目的**: 確保所有 Sprint 執行與規劃保持一致

---

## 🎯 核心原則

### 唯一真相來源 (Single Source of Truth)

```
sprint-status.yaml (進度追蹤)
        ↓
sprint-planning/{sprint-N}-*.md (詳細規劃)
        ↓
architecture-designs/*.md (技術設計)
        ↓
實際代碼實現
```

**關鍵**: 所有 Sprint 執行都必須以這兩個文件為準:
1. `sprint-status.yaml` - 當前狀態和進度
2. `sprint-planning/sprint-{N}-*.md` - 詳細規劃

---

## 📋 Sprint 執行流程

### Phase 1: Sprint Planning (Sprint 開始前)

**時間**: Sprint 開始前 1-2 天

#### Step 1: 讀取 Sprint 規劃文檔

```bash
# 確認當前 Sprint
cat docs/03-implementation/sprint-status.yaml | grep "status: \"in-progress\""

# 讀取對應的規劃文檔
open archived/docs-v1/03-implementation/sprint-planning/sprint-1-core-services.md
```

**檢查內容**:
- [ ] Sprint 目標清晰嗎?
- [ ] Stories 都有明確的驗收標準嗎?
- [ ] Story Points 分配合理嗎?
- [ ] 依賴關係明確嗎?
- [ ] 技術方案清楚嗎?

#### Step 2: 確認架構設計文檔

```bash
# 檢查相關的架構設計是否完整
ls archived/docs-v1/03-implementation/architecture-designs/
```

**確認**:
- [ ] 相關模組的架構設計文檔存在
- [ ] 技術方案詳細且可行
- [ ] 與現有架構一致

#### Step 3: 更新 sprint-status.yaml

```yaml
sprints:
  sprint_1:
    status: "in-progress"  # 從 not-started 改為 in-progress
    start_date: "2025-12-09"
    # ... 其他不變
```

#### Step 4: 創建 Sprint Backlog

使用 PROMPT-02 或手動創建:

```bash
# 選項 1: 使用 PROMPT (推薦)
@PROMPT-02-NEW-SPRINT-PREP.md Sprint-1

# 選項 2: 手動準備
# 1. 分配 Stories 給團隊成員
# 2. 創建 feature branches
# 3. 設置看板 (如果使用 Jira/GitHub Projects)
```

---

### Phase 2: Sprint Execution (Sprint 進行中)

**時間**: Sprint 期間 (2 週)

#### Daily Routine

**每天開始**:
```bash
# 1. 檢查當前 Sprint 狀態
cat docs/03-implementation/sprint-status.yaml

# 2. 確認今天要做的 Story
# 3. 讀取 Story 的驗收標準
# 4. 檢查相關架構設計
```

**開發過程**:
```bash
# 1. 嚴格遵循 sprint-planning 文檔
# 2. 參考 architecture-designs 文檔
# 3. 遵循現有的代碼模式
# 4. 定期提交代碼
```

**每天結束**:
```bash
# 1. 更新 Story 狀態 (如果完成或阻塞)
# 2. 提交代碼到 feature branch
# 3. 記錄問題和決策
```

#### Story 開發流程

**Step 1: 開始 Story**

```yaml
# 更新 sprint-status.yaml
backlog:
  - id: "S1-1"
    status: "in-progress"  # 從 not-started 改為 in-progress
    assignee: "Backend Dev 1"
```

**Step 2: 遵循驗收標準**

```bash
# 讀取 Story 的驗收標準
# 範例: sprint-1-core-services.md

### S1-1: Workflow Service - Core CRUD
驗收標準:
- [ ] Create workflow API endpoint
- [ ] Read workflow API endpoint
- [ ] Update workflow API endpoint
- [ ] Delete workflow API endpoint
- [ ] Input validation with Pydantic
```

**嚴格檢查**:
- [ ] 每個驗收標準都實現了嗎?
- [ ] 技術方案遵循了嗎?
- [ ] 代碼風格一致嗎?
- [ ] 測試寫了嗎?

**Step 3: Code Review**

```bash
# 自我檢查
# - 是否遵循架構設計?
# - 是否符合驗收標準?
# - 是否有測試?
# - 是否有文檔?

# 提交 PR
git push origin feature/s1-1-workflow-crud

# 等待 Review
```

**Step 4: 完成 Story**

```yaml
# 更新 sprint-status.yaml
backlog:
  - id: "S1-1"
    status: "completed"
    completion_date: "2025-12-11"
```

```bash
# 使用 PROMPT-06 保存進度
@PROMPT-06-PROGRESS-SAVE.md Sprint-1 S1-1
```

---

### Phase 3: Sprint Review (Sprint 結束時)

**時間**: Sprint 最後一天

#### Step 1: 檢查完成情況

```bash
# 檢查所有 Stories 狀態
grep "status:" docs/03-implementation/sprint-status.yaml
```

**確認**:
- [ ] 所有 P0 Stories 完成了嗎?
- [ ] 有哪些 Stories 未完成?
- [ ] 未完成的原因是什麼?

#### Step 2: 生成 Sprint 報告

```bash
# 使用 PROMPT-06
@PROMPT-06-PROGRESS-SAVE.md Sprint-1 complete
```

**報告包含**:
- Sprint 目標達成情況
- 完成的 Stories 列表
- 技術實現要點
- 遇到的問題和解決方案
- 代碼統計
- 經驗教訓

#### Step 3: Sprint Retrospective

**回顧問題**:
1. 什麼做得好? (Keep)
2. 什麼可以改進? (Improve)
3. 什麼要開始做? (Start)
4. 什麼要停止做? (Stop)

**更新流程**:
- 根據 Retrospective 更新執行流程
- 調整 Sprint 規劃模板
- 改進開發實踐

---

## 🔄 如何確保執行與規劃一致?

### 1. 使用 Checklist

每個 Story 開發前:

```markdown
## Story 開始 Checklist

- [ ] 已讀取 sprint-planning 文檔中的 Story 描述
- [ ] 已理解驗收標準
- [ ] 已檢查依賴關係 (依賴的 Stories 完成了嗎?)
- [ ] 已讀取相關的架構設計文檔
- [ ] 已檢查 sprint-status.yaml 中的 Story 信息
- [ ] 已創建 feature branch
- [ ] 已在 sprint-status.yaml 標記為 in-progress
```

每個 Story 完成前:

```markdown
## Story 完成 Checklist

- [ ] 所有驗收標準都滿足
- [ ] 代碼已 Code Review
- [ ] 測試已通過
- [ ] 文檔已更新
- [ ] 已更新 sprint-status.yaml
- [ ] 已創建 Story 實現總結 (如果是複雜 Story)
- [ ] 已運行 PROMPT-06 保存進度
```

### 2. 每日同步檢查

**每天開始前**:
```bash
# 執行每日檢查腳本
./scripts/daily-check.sh

# 內容:
# 1. 檢查 sprint-status.yaml 是否更新
# 2. 檢查當前 in-progress 的 Stories
# 3. 提醒今天的計劃
```

**每天結束前**:
```bash
# 執行每日總結腳本
./scripts/daily-summary.sh

# 內容:
# 1. 更新 sprint-status.yaml
# 2. 提交代碼
# 3. 記錄問題
```

### 3. Story 狀態嚴格管理

**狀態轉換規則**:

```
not-started → in-progress → completed
                ↓
              blocked → in-progress → completed
```

**規則**:
- 一次只能有 **1-2 個 Stories 為 in-progress** (防止 WIP 過高)
- **必須** 完成當前 Story 才能開始新的 Story
- 如果 **blocked**,必須記錄原因和解決方案

### 4. 定期對齊檢查

**每週一次** (Mid-Sprint Check):

```bash
# 執行中期檢查
@PROMPT-04-SPRINT-DEVELOPMENT.md check-alignment
```

**檢查項目**:
- [ ] 當前進度是否符合預期?
- [ ] 是否有偏離 Sprint 規劃的情況?
- [ ] 是否有未預期的問題?
- [ ] 是否需要調整計劃?

---

## 🚨 常見偏離情況和處理

### 情況 1: 實現與設計文檔不一致

**症狀**: 代碼實現與 architecture-designs 文檔不同

**原因**:
- 開發者沒有讀設計文檔
- 設計文檔過時
- 技術方案臨時變更

**處理**:
```bash
# 選項 A: 更新代碼以符合設計 (推薦)
# - 重構代碼
# - 遵循設計文檔

# 選項 B: 更新設計文檔 (如果有充分理由)
# - 記錄變更原因
# - 更新設計文檔
# - 通知團隊
# - Tech Lead 審查
```

### 情況 2: Story 超出預期範圍

**症狀**: Story 實現了規劃之外的功能

**原因**:
- 開發者添加了 "Nice to have" 功能
- 對驗收標準理解有誤

**處理**:
```bash
# 1. 停止額外功能開發
# 2. 回到驗收標準
# 3. 移除非必要代碼
# 4. 將額外功能記錄為技術債務或新 Story
```

### 情況 3: 驗收標準不清晰

**症狀**: 不確定 Story 是否完成

**原因**:
- Sprint 規劃文檔描述不夠詳細
- 技術方案模糊

**處理**:
```bash
# 1. 立即與 Product Owner 或 Tech Lead 溝通
# 2. 澄清驗收標準
# 3. 更新 sprint-planning 文檔
# 4. 繼續開發
```

### 情況 4: sprint-status.yaml 未更新

**症狀**: Story 已完成但狀態還是 in-progress

**原因**:
- 忘記更新
- 不知道要更新

**處理**:
```bash
# 1. 立即更新 sprint-status.yaml
# 2. 設置每日提醒
# 3. 使用 PROMPT-06 自動更新
```

---

## 📚 文檔優先級

### 執行 Sprint 時的閱讀順序

**第一優先級** (必讀):
1. `sprint-status.yaml` - 當前狀態
2. `sprint-planning/sprint-{N}-*.md` - 詳細規劃

**第二優先級** (開發前讀):
3. `architecture-designs/{相關模組}-design.md` - 技術設計

**第三優先級** (參考):
4. `implementation-guides/*.md` - 實現指南
5. 已完成的 Story 總結 - 參考範例

**第四優先級** (可選):
6. 其他架構文檔 - 了解全局

---

## 🎯 成功標準

### Sprint 執行成功的標誌

**進度方面**:
- [ ] 所有 P0 Stories 完成
- [ ] 80%+ P1 Stories 完成
- [ ] sprint-status.yaml 實時更新

**質量方面**:
- [ ] 代碼符合架構設計
- [ ] 所有驗收標準滿足
- [ ] 測試覆蓋率達標 (80%+)
- [ ] Code Review 通過

**文檔方面**:
- [ ] 複雜 Story 有實現總結
- [ ] 技術決策有記錄
- [ ] Sprint 報告已生成

**團隊方面**:
- [ ] 沒有重大偏離規劃的情況
- [ ] 團隊對進度有共識
- [ ] Retrospective 有建設性反饋

---

## 🛠️ 工具和腳本

### 推薦的輔助腳本

**1. Sprint 狀態檢查**

```bash
# scripts/check-sprint-status.sh
#!/bin/bash

echo "=== Current Sprint Status ==="
grep -A 5 "status: \"in-progress\"" docs/03-implementation/sprint-status.yaml

echo "\n=== In Progress Stories ==="
grep -B 2 "status: \"in-progress\"" docs/03-implementation/sprint-status.yaml | grep "id:"

echo "\n=== Completed Stories Today ==="
grep "completion_date: \"$(date +%Y-%m-%d)\"" docs/03-implementation/sprint-status.yaml
```

**2. Story 對齊檢查**

```bash
# scripts/check-story-alignment.sh
#!/bin/bash

STORY_ID=$1

echo "=== Checking Story: $STORY_ID ==="

# 檢查 sprint-status.yaml
echo "\n1. sprint-status.yaml:"
grep -A 10 "id: \"$STORY_ID\"" docs/03-implementation/sprint-status.yaml

# 檢查 sprint-planning 文檔
echo "\n2. Sprint Planning:"
grep -A 20 "$STORY_ID" archived/docs-v1/03-implementation/sprint-planning/sprint-*.md

# 檢查是否有對應的 Summary
echo "\n3. Story Summary:"
ls docs/03-implementation/*$STORY_ID*.md 2>/dev/null || echo "No summary found"
```

**3. 每日提醒**

```bash
# scripts/daily-reminder.sh
#!/bin/bash

echo "📋 Daily Development Checklist:"
echo ""
echo "開始工作前:"
echo "  [ ] 檢查 sprint-status.yaml"
echo "  [ ] 確認今天的 Story"
echo "  [ ] 讀取驗收標準"
echo ""
echo "開發過程中:"
echo "  [ ] 遵循架構設計"
echo "  [ ] 寫測試"
echo "  [ ] 定期提交"
echo ""
echo "結束工作前:"
echo "  [ ] 更新 sprint-status.yaml"
echo "  [ ] Push 代碼"
echo "  [ ] 記錄問題"
```

---

## 📖 參考文檔

### 相關 Prompts

- `PROMPT-02-NEW-SPRINT-PREP.md` - Sprint 準備
- `PROMPT-04-SPRINT-DEVELOPMENT.md` - Sprint 開發
- `PROMPT-06-PROGRESS-SAVE.md` - 進度保存
- `PROMPT-08-CODE-REVIEW.md` - Code Review

### 相關文檔

- `README.md` - 文檔索引
- `sprint-status.yaml` - 進度追蹤主文件
- `sprint-planning/` - Sprint 規劃文檔目錄

---

## ✅ 快速參考

### Sprint 開始時

```bash
# 1. 讀取規劃
open archived/docs-v1/03-implementation/sprint-planning/sprint-1-core-services.md

# 2. 檢查架構
ls archived/docs-v1/03-implementation/architecture-designs/

# 3. 更新狀態
# Edit sprint-status.yaml: status: "in-progress"

# 4. 運行準備腳本
@PROMPT-02-NEW-SPRINT-PREP.md Sprint-1
```

### 開發 Story 時

```bash
# 1. 讀取 Story 描述和驗收標準
# 2. 檢查相關架構設計
# 3. 開始開發
# 4. 定期對照驗收標準
# 5. 完成後運行 PROMPT-06
```

### Sprint 結束時

```bash
# 1. 檢查所有 Stories
# 2. 生成 Sprint 報告
@PROMPT-06-PROGRESS-SAVE.md Sprint-1 complete

# 3. Sprint Retrospective
# 4. 準備下個 Sprint
```

---

**維護者**: Tech Lead
**版本**: v1.0.0
**最後更新**: 2025-11-20
