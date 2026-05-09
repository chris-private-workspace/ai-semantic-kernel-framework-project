# 範疇邊界與跨範疇導入規則

**Purpose**: 定義 11+1 範疇的歸屬與跨範疇 import 紀律，防止反模式 AP-3（Cross-Directory Scattering）。

**Category**: Framework / Infrastructure
**Created**: 2026-04-28
**Last Modified**: 2026-04-28
**Status**: Active

**Modification History**:
- 2026-04-28: Initial creation from V2 規劃文件 01-eleven-categories-spec.md + 02-architecture-design.md

---

## 為什麼需要此規則

V1 教訓：Guardrails 散落 6 處（core/security / orchestration/hitl / orchestration/risk_assessor / orchestration/audit / claude_sdk/hooks / agent_framework/acl），導致：
- 跨目錄相互不知對方存在
- 重複實作（多個 audit logger）
- 修改一處遺漏另一處

V2 強制：**同一範疇代碼必須歸屬於單一目錄**，禁止散落。

---

## 11+1 範疇對照表

| # | 範疇名稱 | 目錄路徑 | Owner 範疇 | 所屬 Phase |
|---|---------|---------|----------|----------|
| 1 | Orchestrator Loop (TAO/ReAct) | `agent_harness/orchestrator_loop/` | 1 | 50.1 |
| 2 | Tool Layer | `agent_harness/tools/` | 2 | 51.1 |
| 3 | Memory（5 層 × 3 時間軸） | `agent_harness/memory/` | 3 | 51.2 |
| 4 | Context Mgmt（Compaction / Caching） | `agent_harness/context_mgmt/` | 4 | 52.1 |
| 5 | Prompt Construction | `agent_harness/prompt_builder/` | 5 | 52.2 |
| 6 | Output Parsing | `agent_harness/output_parser/` | 6 | 50.1 |
| 7 | State Mgmt（Checkpoint / Time-travel） | `agent_harness/state_mgmt/` | 7 | 53.1 |
| 8 | Error Handling（4 類 + Retry） | `agent_harness/error_handling/` | 8 | 53.2 |
| 9 | Guardrails & Safety（含 Tripwire） | `agent_harness/guardrails/` | 9 | 53.3 |
| 10 | Verification Loops（Self-correction） | `agent_harness/verification/` | 10 | 54.1 |
| 11 | Subagent Orchestration（4 模式） | `agent_harness/subagent/` | 11 | 54.2 |
| **12** | **Observability / Tracing（cross-cutting）** | **`agent_harness/observability/`** | **12** | **49.4+** |

---

## 歸屬鐵律

### Rule 1：每個檔案必須明確歸屬一個範疇

```python
# ✅ 正確：檔案 header 明確指出範疇
"""
File: agent_harness/memory/layers/user_memory.py
Category: 範疇 3 (Memory)
"""

# ❌ 禁止：跨範疇「共用」目錄
agent_harness/common/approval.py  # ← 「approval」應該在 governance/ 或由 HITL 中央化 own
agent_harness/shared/audit.py     # ← 「audit」應該在平台層，不該在 agent_harness 下
```

### Rule 2：跨範疇 import 規則（三層清單）

#### ✅ 允許的 import

1. **從 `_contracts/` import 型別**
   ```python
   # 任何範疇可從此 import，不違反依賴
   from agent_harness._contracts import ToolSpec, Message, LoopState
   ```

2. **從 owner 範疇的 `__init__.py` import 公開介面**
   ```python
   # 範疇 1 可 import 範疇 2 的公開工具 API
   from agent_harness.tools import ToolRegistry, ToolExecutor

   # 但必須是明確 owner 的公開接口（`__init__.py` re-export）
   ```

3. **經 17.md 核准的跨範疇 ABC 呼叫**
   ```python
   # 範疇 1 Loop 呼叫範疇 6 OutputParser
   response = await self.output_parser.parse(llm_response)  # owner: 17.md §2.1

   # 範疇 4 Compactor 透過 prompt hint 影響範疇 11（非直接呼叫）
   # 規則見 17.md §7.1
   ```

#### ❌ 禁止的 import

1. **直接 reach into 他人私有模組**
   ```python
   # ❌ 禁止：範疇 8 直接存取範疇 7 的私有狀態
   from agent_harness.state_mgmt.snapshot_store import SnapshotStore

   # ✅ 正確：透過 Checkpointer ABC
   from agent_harness.state_mgmt import Checkpointer
   ```

2. **在他人範疇內定義屬於自己的型別**
   ```python
   # ❌ 禁止：範疇 11 在 tools/ 下定義 SubagentCall tool
   # agent_harness/tools/subagent_tools.py  ← 這違反 single-source rule

   # ✅ 正確：範疇 11 own 此 tool，在 agent_harness/subagent/ 定義後註冊到 registry
   # agent_harness/subagent/tools.py 定義 → register_subagent_tools(registry)
   ```

3. **循環依賴**
   ```python
   # ❌ 禁止
   # 範疇 A import 範疇 B import 範疇 A
   ```

---

## Single-Source 法則

跨範疇 dataclass / ABC / 工具 / 事件只能在 **owner 處定義一次**。

### 型別 Owner 表（from 17.md §1.1）

| 型別 | Owner 文件 | Owner 位置 |
|-----|----------|---------|
| `ChatResponse` / `Message` | 10-server-side-philosophy.md | adapters/_base/chat_client.py（引用） |
| `ToolSpec` / `ToolCall` | 01-eleven-categories-spec.md 範疇 2 | agent_harness/tools/spec.py |
| `LoopState` | 01-eleven-categories-spec.md 範疇 7 | agent_harness/state_mgmt/state.py |
| `LoopEvent` | 01-eleven-categories-spec.md 範疇 1 | agent_harness/_contracts/events.py |
| `MemoryHint` | 01-eleven-categories-spec.md 範疇 3 | agent_harness/memory/types.py |
| `VerificationResult` | 01-eleven-categories-spec.md 範疇 10 | agent_harness/verification/types.py |
| `SubagentBudget` | 01-eleven-categories-spec.md 範疇 11 | agent_harness/subagent/types.py |
| `ApprovalRequest` | 01-eleven-categories-spec.md §HITL | agent_harness/_contracts/hitl.py |

### 範例

✅ **正確**：
```python
# 範疇 6 (output_parser) 使用 ChatResponse
from agent_harness._contracts.chat import ChatResponse

class OutputParser:
    def parse(self, response: ChatResponse) -> ParsedOutput: ...
```

❌ **錯誤**：
```python
# 範疇 6 重新定義 ChatResponse
@dataclass
class ChatResponse:  # ← 違反 single-source rule
    model: str
    content: str
```

---

## 跨範疇 Lint 規則（Phase 49.4+ CI 強制）

### Lint 1：禁止重複定義型別

```bash
$ duplicate-type-checker backend/src/agent_harness/
ERROR: ToolSpec defined in 2+ places:
  - agent_harness/tools/spec.py:15
  - agent_harness/subagent/tools.py:42  ← 衝突！
FIX: Remove duplicate, import from agent_harness.tools instead.
```

### Lint 2：禁止跨範疇私有 import

```bash
$ cross-category-import-check backend/src/agent_harness/
WARNING: orchestrator_loop/loop.py imports from state_mgmt.snapshot_store (private)
  Line 23: from agent_harness.state_mgmt.snapshot_store import SnapshotStore
FIX: Use public interface from agent_harness.state_mgmt.__init__
```

### Lint 3：禁止代碼散落

```bash
$ category-scatter-check backend/src/agent_harness/
ERROR: "approval" keyword found in multiple categories:
  - tools/approval.py (should be governance/)
  - orchestrator_loop/approval_check.py (should be governance/)
FIX: Consolidate all approval logic in one owner category.
```

---

## 平台級與業務領域歸屬

### 平台層（不屬於 11+1 範疇）

```
backend/src/
├── platform/governance/         # HITL / Risk / Audit / Compliance（跨切面）
├── platform/identity/           # Auth / RBAC / Multi-tenancy（跨切面）
├── platform/observability/      # 範疇 12 實作位置（cross-cutting ABC）
└── platform/workers/            # 執行平面
```

**Rule**：平台層可被任意上層 import；自身不依賴 agent_harness 業務邏輯。

### 業務領域層

```
backend/src/business_domain/
├── patrol/                      # 巡檢業務
├── correlation/                 # 關聯分析
├── rootcause/                   # 根因分析
├── audit/                       # 業務稽核（區別於 governance.audit）
└── incident/                    # 事件管理
```

**Rule**：業務層呼叫 agent_harness，**不反向被呼叫**。

---

## 衝突解法

### 場景 1：「此邏輯屬於哪個範疇？」

按優先級檢查：
1. **17.md Contract 表** — 型別已登記？按 owner 所屬範疇
2. **依賴順序** — 「被誰用最多」的範疇 own 它
3. **功能內聚** — 與哪個範疇概念最相關

範例：`request_approval()` tool 屬於誰？
- 範疇 2 (Tools) 呼叫？
- 範疇 9 (Guardrails) 觸發？
- **解答**：17.md §3.1 指明 owner = **§HITL 中央化**（不是範疇 2，也不是 9）

### 場景 2：「A 和 B 都想定義同一型別」

1. 檢查 17.md §1 — 若已登記，使用現有 owner
2. 若未登記，須協議由**主要呼叫者**範疇 own 此型別
3. **不允許**平行定義，必須透過 PR 同時更新 17.md §1

---

## 檢查清單（Code Review）

- [ ] 新檔案有 `Category: 範疇 X` 標籤
- [ ] 新 import 是否在允許清單 1-3？
- [ ] 是否違反 lint 規則 1-3？
- [ ] 跨範疇型別是否已在 17.md 登記？
- [ ] 若新增跨範疇型別，是否同步更新 17.md？

---

## 違規後果

| 違規 | 後果 | 修復時間 |
|-----|------|--------|
| 直接 import 他人私有模組 | CI lint fail | 15 min |
| 重複定義型別 | Merge 前通知 + 必須聯合修正 | 1-2 hours |
| 代碼散落 5+ 個目錄 | Architecture review 拒絕 | 重做 |

---

## 引用

- **01-eleven-categories-spec.md** — 11+1 範疇完整定義與 Owner 對應
- **02-architecture-design.md** — §約束 2「範疇間依賴」/ §約束 3「Adapter 層強制」
- **04-anti-patterns.md** — AP-3 Cross-Directory Scattering / AP-6 Hybrid Bridge Debt
- **17-cross-category-interfaces.md** — §1.1 single-source 型別表 / §2.1 ABC 表 / §3.1 工具註冊表
- **CLAUDE.md** — §Code Standards 與 §V2 11+1 範疇

---

**維護責任**：Code reviewer @ 每個 PR；CI lint 於 Phase 49.4 自動強制。
