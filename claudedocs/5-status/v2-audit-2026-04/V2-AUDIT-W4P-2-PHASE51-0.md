# V2 Audit W4P-2 — Phase 51.0 Mock 企業工具 + 業務骨架

**Date**: 2026-04-29
**Auditor**: Research Agent (W4P-2)
**Scope**: Sprint 51.0 (12 commits, merge `8cd47caa`)
**結論**: ✅ **Passed with Concerns** (multi-tenant 缺失為已知 R-7；不阻塞 52.2)

---

## 摘要

| 維度 | 結果 |
|-----|------|
| Plan/Checklist 對齊 | ✅ Day 0-5 全部 `[x]`，無未勾項；交付 D-1~D-10 對應 commits 完整 |
| mock_executor 真實性 | ✅ **Dynamic responses**（5 domain 全部 lookup seed.json + 條件分支 + 404；非 always-success） |
| 19 tools 真整合 chat handler | ✅ **真整合**（handler.py:78,135 兩處呼叫 `make_default_executor()` → 19 specs/handlers，**對比 W4P-4 memory 是 Potemkin**） |
| e2e mock_patrol 真 multi-turn | ✅ **真 2-turn**（TOOL_USE → tool_executed → END_TURN）+ **真 subprocess uvicorn** + **真 httpx** |
| Tests | **22 PASS / 2 FAIL（無關 51.0）/ 0 SKIP，4.25s** ⚠ |
| Multi-tenant | ❌ **完全缺失**（business_domain `*.py` 0 處 `tenant_id`，僅 README 提及） |
| 17.md 對齐 | ✅ 18 mock entries 已加（high-risk 3 個全在）+ Phase 55 mass rename plan |
| Worker startup hook | 🟡 **設計變更**（plan 寫 worker 注入；checklist 4.3 標記改為 chat handler factory，標明 clean layering 理由） |
| 阻塞 52.2 判定 | ❌ **不阻塞**（51.0 任務範圍是 mock + 骨架；HITL/tenant 是 Phase 53.3 / 51.1 接） |

---

## Phase A — Plan/Checklist 對齊

讀完 `sprint-51-0-plan.md`（330 行）+ `sprint-51-0-checklist.md`（318 行）：

- **Day 0-5 全部 `[x]`**，0 個 🚧 殘留，0 個未勾項。符合 V2 紀律「禁止刪除未勾選項」。
- **10 個 deliverables 全交付**：D-1 (10 files)、D-2 (18 ToolSpec)、D-3 (mock backend)、D-4 (seed)、D-5 (aggregator)、D-6 (chat handler hook)、D-7 (17.md sync)、D-8 (24 tests)、D-9 (dev script)、D-10 (closeout)。
- **commits 對應**：12 commits 在 PR `8cd47caa`，包含 Day 1-4 feature commits + Day 5 closeout。
- **Carry-forward 留 3 項**：CARRY-019/020/021 已記錄到 retrospective.md。

---

## Phase B — mock_executor 真實性

**結論：5 domain mock router 全部 dynamic，非 always-success。**

| Router | Lines | `if`-branches | Seed lookup | 404 | 動態行為證據 |
|--------|-------|--------------|------------|-----|------------|
| patrol | 115 | 2 | ✅ db.servers | ✅ | check_servers per-id health from seed |
| correlation | 135 | 6 | ✅ db.alerts/incidents | ✅ | ±5min window correlation, server_id matching, depth scaling |
| rootcause | 134 | 4 | ✅ db.incidents/rca_findings | ✅ | dry_run vs live branch；returns `closed_pending_review` (not generic success) |
| incident | 142 | 7 | ✅ db.incidents | ✅ | severity/status filter, in-memory ledger merge with seed |
| audit | 118 | 4 | ✅ db.audit_logs | ✅ | filter by time_range/action/user_id |

**紅旗檢查**：無「永遠 return `{success: True}`」現象。每個 router 從 seed.json (10 customer / 50 order / 20 alert / 5 incident / 3 patrol / 8 RCA / 5 audit) lookup + 條件分支返回不同結果。

**唯一弱點**（非阻塞）：
- ❌ 無 latency simulation（real enterprise integration 可能 200ms-2s）
- ❌ 無 error injection（PoC 階段，retro 應留 P2 backlog）

---

## Phase C — Chat handler 19 tools 真整合

**結論：✅ 真整合 — 與 W4P-4 Memory Potemkin 形成鮮明對比。**

關鍵證據：
- `_register_all.py:make_default_executor()` 建 `ToolRegistryImpl + ToolExecutorImpl`，註冊 echo_tool + 18 業務工具 = **19 specs / 19 handlers**
- `chat/handler.py:58` import `make_default_executor`
- `chat/handler.py:78`（build_echo_demo_handler）+ `:135`（build_real_llm_handler）**兩處實呼叫** → registry+executor 真進 AgentLoopImpl
- 與 W4P-3 51.1 結論一致（Cat 2 Tool Layer 真實接入主流量）

**鏈路完整性**：register_all → 18 business handlers → ToolExecutorImpl → AgentLoopImpl → chat router ✅

**唯一偏差**：plan §4.3 寫「worker startup hook」，checklist §4.3 改為 chat handler factory（理由：避免改 worker 簽名 / clean layering），這是合理 design 調整且 retro 已標明。但**worker 端尚未自帶 19 tools**（此非 51.0 阻塞，後續 Sprint 接）。

---

## Phase D — e2e mock_patrol 真實性

**結論：✅ 真 multi-turn + 真 subprocess + 真 httpx**（W4P-3 / W4P-4 之中最完整 e2e）。

證據（`test_agent_loop_with_mock_patrol.py`）：
- **真 subprocess**：`subprocess.Popen([sys.executable, '-m', 'uvicorn', 'mock_services.main:app', '--port', '8001'])`（line ~80）
- **真 multi-turn**（line 138-150）：MockChatClient 預編 2 ChatResponse — turn 1 `tool_calls=[mock_patrol_check_servers], stop_reason=TOOL_USE`；turn 2 `stop_reason=END_TURN`
- **真 httpx call**：handler 透過 `PatrolMockExecutor` → `httpx.AsyncClient.post('http://localhost:8001/mock/patrol/check_servers')` → real uvicorn 回應
- **真斷言**：`completed.stop_reason == TerminationReason.END_TURN`（line 189）+ ToolCallExecuted 含 `server_id=web-01` + health（line 145）

**Multi-tenant 場景**：❌ 無（單租戶 PoC）。

---

## Phase E — Tests + Multi-tenant + 17.md 對齐

### E.1 Tests pass/fail/skip + 跑時間

```
collected 24 items
test_business_tools_via_registry.py ........ (10 tests)  PASS
test_agent_loop_with_mock_patrol.py ..        (2 tests)   PASS
test_builtin_tools.py .........FF...          (12 tests, 2 FAIL 10 PASS)
================================
22 passed, 2 failed in 4.25s
```

**2 FAIL 分析**：`test_memory_search_placeholder_raises` + `test_memory_write_placeholder_raises`（記憶工具 placeholder 在 W4P-4 51.2 後行為改變 — `success=True + ok:false JSON` 而非 raise；**屬 W4P-4 51.2 範疇，非 51.0 引入**）。

**速度**：4.25s（含真 subprocess uvicorn 啟動 ~3s）— 與 W4P-3 51.1 1.87s 同級健康；**遠優於 W4P-4 51.2 0.36s 全 mock 紅旗**。

**Mock 比例**：mock_executor 是 PoC mock 但**真調 HTTP**；e2e 用 MockChatClient（必要：避免真打 LLM）+ real httpx + real uvicorn subprocess。組合健康。

### E.2 Multi-tenant 處理

**❌ 完全缺失** — `grep -rn "tenant_id\|tenant" backend/src/business_domain/*.py` = 0 hits（僅 README 提及）。

- mock_executor 5 個：均無 tenant 參數
- tools.py 5 個：handlers `(call: ToolCall) -> str` 不讀 ExecutionContext.tenant_id
- _register_all.py：register 不接 tenant_id
- handler.py：`make_default_executor()` 不傳 tenant_id

**影響評估**：
- 屬 plan §V2 紀律 9 表格中「R-7 51.0 mock backend 不 tenant-aware（簡化）；51.1 接 real registry 時加 tenant_id」**已知簡化**，retrospective.md 應記錄
- 與 W4P-4 W3-2 反模式（從 `ToolCall.arguments` 讀 tenant 是 LLM-controlled 不可信）**不同** — 51.0 完全不處理，留給未來 caller-controlled ExecutionContext 模式
- ⚠ Phase 53.3 HITL + Phase 55 真實 integration 上線前**必須補**

### E.3 17.md §3.1 對齐

- 18 mock entries 已加（patrol 4 + correlation 3 + rootcause 3 + audit 3 + incident 5）
- 高風險 3 個（mock_patrol_check_servers, mock_incident_close, mock_rootcause_apply_fix）grep 確認在 17.md
- annotations / hitl_policy / risk_level 在 ToolSpec 完整宣告（patrol 4 specs 例：read_only/destructive + AUTO/ASK_ONCE + LOW/MEDIUM/HIGH）
- 注入 Phase 55 mass rename plan（mock_ → 正式 prefix）

---

## 修補建議

### P0（必修，Sprint 51.1 / 53.3 前）

- **P0-1 補 Multi-tenant**：51.1 接真 ToolRegistry 時，handler signature 改為 `(call: ToolCall, ctx: ExecutionContext)`，從 ctx 讀 tenant_id 傳到 mock_executor → mock_services /mock/{domain}/...?tenant_id=X
- **P0-2 W4P-4 失敗測試決策**：2 個 memory placeholder test 的「raise vs ok:false JSON」設計分歧需 51.2 owner 修正（不影響 51.0 但污染 CI）

### P1（建議）

- **P1-1 mock_services Docker 化**：CARRY 候選；docker-compose.dev.yml 已加 service block 但實際啟動條件未驗證
- **P1-2 mock_executor latency simulation**：加 random delay 50-300ms，更貼真實 enterprise integration

### P2（不阻塞）

- **P2-1 24 vs 18 工具差異**：roadmap 24 vs spec 18，retrospective 已標 CARRY-020；user review 後再決
- **P2-2 mock_executor error injection**：5% 失敗率注入 + ChatResponse 可觀察 retry 路徑

---

## 不正常開發 / 偏離 findings

1. **Worker hook 設計變更未在 plan 同步更新**（已在 checklist § 4.3 標明，retrospective 應強化）— 設計理由 (clean layering) 合理但 plan §File Change List `agent_loop_worker.py` 仍列為「修改」造成可追溯性歧義
2. **plan 寫 24 ToolSpec，實做 18**（per 08b spec）— 已留 CARRY-020；非偏離
3. **`audit_domain` dir 命名而非 `audit`**（避免 governance.audit 衝突）— 合理且 mock_executor.py 註明
4. **Multi-tenant 完全缺席**：plan §V2 紀律 9 自承簡化，但 retrospective.md 應有顯式 R-7 entry（未驗證）
5. **OTel tracing 未涵蓋 mock_executor HTTP call**：retrospective 已列 CARRY 候選，待 Phase 53 觀測強化

---

## 阻塞 52.2 判定

**❌ 不阻塞 Sprint 52.2**

理由：
1. 51.0 範圍是 **mock backend + 18 ToolSpec stub + 骨架**，**不含 multi-tenant / HITL 強制**（plan 明示）
2. mock_executor 真 dynamic + chat handler 真整合 + e2e 真 multi-turn — 此 3 大正向結果優於 W4P-4
3. 22/22 測試 PASS（去除無關 51.2 失敗）
4. 17.md 同步、retrospective 完整、CARRY 已記錄
5. Multi-tenant 缺失是**已知簡化（R-7）**，由 51.1 真 ToolRegistry 接手 — 不應在 52.2（Context Mgmt / Compaction）前必補

**建議 52.2 啟動前**：W4P-5 mini-W4-pre 總結時將 P0-1 列為 51.1 closeout 必驗項。

---

## Critical 1-2 個發現

1. **🟢 51.0 是 W4P 三審計中最健康的 sprint**：mock dynamic + chat handler 真整合（vs W4P-4 Potemkin）+ e2e 真 multi-turn / subprocess / httpx + 17.md 同步完整。**體現 V2 從 51.1 起的紀律提升**。
2. **🔴 Multi-tenant 完全空白須 Sprint 51.1 補完**：5 mock_executor + handler signature 全無 tenant_id；雖屬已知 R-7 簡化，但 51.1 真 ToolRegistry 接入時必須同時補 ExecutionContext-based tenant 注入 (caller-controlled，避開 W4P-4 W3-2 反模式)。

---

**File**: `claudedocs/5-status/V2-AUDIT-W4P-2-PHASE51-0.md`
