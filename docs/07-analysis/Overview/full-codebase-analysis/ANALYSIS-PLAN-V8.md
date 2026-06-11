# IPA Platform V8 全面 Codebase 分析計劃

> **目標**: 產生 2 份 V8 報告（對標 V7 格式），基於對整個 codebase 的完整內容分析
> **輸出文件**:
> 1. `MAF-Claude-Hybrid-Architecture-V8.md` — 11 層架構深度分析（對標 V7 1,724 行）
> 2. `MAF-Features-Architecture-Mapping-V8.md` — 功能架構映射指南（對標 V7 860 行）
> **輸出位置**: `docs/07-analysis/Overview/full-codebase-analysis/`

---

## 一、V7 的方法論 vs V8 的方法論

### V7 方法（2026-02-11）
- 5 個分析 Agent + 3 個交叉驗證 Agent
- 基於 Phase 29 完成時的代碼庫（611 .py, 203 .tsx/.ts）
- 已知限制：Windows/MSYS2 環境導致 LOC 低估、部分問題後續已修復

### V8 方法（2026-03-15）— 本次分析
- **Phase 1: 結構掃描**（已完成）— 3 個 AST 腳本 100% 檔案覆蓋
- **Phase 2: 規劃文件閱讀** — 讀取 34 個 Phase 的 sprint-planning + sprint-execution，建立「計劃 vs 實際」對照表
- **Phase 3: 源代碼全文閱讀** — Agent Team 分批全文閱讀每個檔案的業務邏輯（非抽樣）
- **Phase 4: 交叉驗證** — 3 個驗證 Agent 對 Phase 3 結果進行挑戰和確認
- **Phase 5: 報告撰寫** — 彙整為 V8 格式的 2 份報告

---

## 二、代碼庫範圍（基於 AST 掃描精確數據）

| 層級 | 路徑 | 檔案數 | 代碼行 | 分析策略 |
|------|------|--------|--------|----------|
| API Layer | backend/src/api/v1/ | 143 | 34,496 | 3 Agents (每個 ~48 files) |
| Domain Layer | backend/src/domain/ | 107 | 33,544 | 3 Agents (每個 ~36 files) |
| Integration: agent_framework | backend/src/integrations/agent_framework/ | 57 | 28,248 | 2 Agents |
| Integration: hybrid | backend/src/integrations/hybrid/ | 73 | 18,152 | 2 Agents |
| Integration: orchestration | backend/src/integrations/orchestration/ | 54 | 15,570 | 2 Agents |
| Integration: claude_sdk | backend/src/integrations/claude_sdk/ | 47 | 11,625 | 1 Agent |
| Integration: mcp | backend/src/integrations/mcp/ | 73 | 17,000 | 2 Agents |
| Integration: ag_ui | backend/src/integrations/ag_ui/ | 24 | 7,554 | 1 Agent |
| Integration: 其他 8 模組 | backend/src/integrations/{swarm,patrol,...} | 64 | ~14,298 | 1 Agent |
| Core + Infrastructure | backend/src/core/ + infrastructure/ | 68 | ~12,145 | 1 Agent |
| Frontend: Pages | frontend/src/pages/ | 40 | ~10,467 | 1 Agent |
| Frontend: Components | frontend/src/components/ | 137 | ~18,538 | 2 Agents |
| Frontend: Hooks + API + Stores | frontend/src/hooks/ + api/ + store*/ | 28 | ~7,309 | 1 Agent |
| Frontend: Types + Utils | frontend/src/types/ + utils/ + lib/ | 9 | ~1,000 | 與上合併 |
| **Total** | | **939+** | **~235,099** | **~22 Agents** |

### Sprint 規劃文件
| 路徑 | 預估檔案數 | 分析策略 |
|------|-----------|----------|
| archived/docs-v1/03-implementation/sprint-planning/ (34 phases) | ~140+ | 2 Agents 分批讀取 |
| archived/docs-v1/03-implementation/sprint-execution/ | ~100+ | 1 Agent 讀取關鍵 sprint |

---

## 三、每個 Agent 的具體任務

### 源代碼 Agent 的標準指令

每個源代碼 Agent 必須對其負責的每個檔案做以下分析：

1. **函數/方法清單**: 列出每個函數，標記其業務邏輯（做什麼）
2. **實現完整度**: 不是看有沒有代碼，而是看邏輯是否完整（有沒有 TODO、hardcoded return、mock fallback）
3. **依賴關係**: 這個模組依賴了誰？誰依賴了它？（import 分析 + 調用分析）
4. **數據流**: 數據從哪裡來、到哪裡去（DB? Redis? InMemory? Mock?）
5. **與 Sprint 計劃對照**: 這個模組對應哪個 Sprint/Phase？計劃中的功能是否都實現了？
6. **問題識別**: 找出真正的問題（mock in production、missing validation、broken chain、dead code）

### 輸出格式

每個 Agent 必須輸出：
```markdown
## [模組名稱]

### 檔案清單
| 檔案 | 行數 | 主要類/函數 | 業務邏輯摘要 | 完整度 | 問題 |

### 依賴關係圖
- 依賴: [列出]
- 被依賴: [列出]

### 數據流分析
- 數據來源: DB / Redis / Mock / LLM API / ...
- 數據去向: API Response / SSE Stream / DB / ...

### 對應 Sprint
- Phase X, Sprint Y: [計劃的功能] → [實際實現狀態]

### 發現的問題
1. [問題描述 + 嚴重度 + 證據]
```

---

## 四、交叉驗證策略

3 個交叉驗證 Agent：

1. **E2E Flow Validator** — 追蹤 5 條主要用戶旅程的完整鏈路（Frontend → API → Domain → Integration → DB/LLM），每個環節確認代碼能否實際連通
2. **Plan vs Reality Validator** — 對照 Sprint 計劃文件和實際代碼，找出「計劃了但沒實現」和「實現了但沒計劃」的差異
3. **Issue Deduplication Validator** — 彙整所有 Agent 發現的問題，去重、分類、排序

---

## 五、報告結構（V8 對標 V7）

### 報告 1: MAF-Claude-Hybrid-Architecture-V8.md

```
1. 實現狀態總覽（各層 + 已知問題表）
2. 執行摘要
3. 11 層架構逐層分析
   - 每層: 檔案數、LOC、類/函數數、實現率
   - 每層: 關鍵組件清單 + 業務邏輯摘要
   - 每層: 數據流分析
   - 每層: 問題清單
4. 端到端流程分析（更新 V7 的 37 條路徑）
5. 並行處理架構
6. 安全架構（含 Sprint 111 更新）
7. Checkpoint 系統分析
8. 與 V7 差異對照
```

### 報告 2: MAF-Features-Architecture-Mapping-V8.md

```
1. 64+ 功能驗證結果
2. 按能力類別統計
3. 每個功能的詳細映射:
   - 功能描述
   - 對應 Sprint/Phase
   - 實現檔案清單 + 代碼行數
   - 實現狀態（✅完整/⚠️部分/❌缺失）
   - 業務邏輯摘要
   - 依賴關係
   - 問題清單
4. V7 → V8 變更記錄
```

---

## 六、執行順序

```
Phase 1: 結構掃描 ✅ 已完成（3 個 AST 腳本，精確數據已在 scripts/analysis/）

Phase 2: Sprint 規劃文件閱讀
  ├── Task 2.1: 讀取 Phase 1-17 的 sprint planning
  ├── Task 2.2: 讀取 Phase 18-34 的 sprint planning
  └── Task 2.3: 讀取關鍵 sprint execution 記錄

Phase 3: 源代碼全文閱讀（Agent Team，~22 Agents 並行）
  ├── Team A: Backend API Layer (3 Agents)
  ├── Team B: Backend Domain Layer (3 Agents)
  ├── Team C: Backend Integration Layer (11 Agents)
  ├── Team D: Backend Core + Infra (1 Agent)
  ├── Team E: Frontend (4 Agents)
  └── 每個 Agent 輸出標準格式的分析摘要到指定檔案

Phase 4: 交叉驗證（3 Agents）
  ├── Task 4.1: E2E Flow Validator
  ├── Task 4.2: Plan vs Reality Validator
  └── Task 4.3: Issue Deduplication Validator

Phase 5: 報告撰寫
  ├── Task 5.1: 撰寫 MAF-Claude-Hybrid-Architecture-V8.md
  └── Task 5.2: 撰寫 MAF-Features-Architecture-Mapping-V8.md
```

---

## 七、限制與誠實聲明

### 能做到的
- ✅ 每個檔案被至少一個 Agent 全文閱讀
- ✅ 每個函數的業務邏輯被摘要
- ✅ 依賴關係被追蹤
- ✅ Sprint 計劃與實際代碼對照
- ✅ 問題被識別並分類

### 做不到的
- ❌ 無法執行代碼或運行測試（只能靜態分析）
- ❌ 無法驗證 LLM API 是否真正連通（需要 API Key）
- ❌ Agent 理解代碼的深度有上限（複雜的多層回調、異步狀態機等可能被簡化）
- ❌ 939 個檔案由 ~22 個 Agent 分批讀取，每個 Agent 的 context window 有限，可能無法看到跨模組的全局關係（靠交叉驗證 Agent 補充）

---

**本規劃文件**: `docs/07-analysis/Overview/full-codebase-analysis/ANALYSIS-PLAN-V8.md`
**預計產出**: 2 份 V8 報告 + 22+ 個模組分析摘要 + 3 個驗證報告
