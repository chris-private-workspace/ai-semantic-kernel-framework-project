# V2 Audit W3-0 — Carryover P1 狀態驗證

**Audit 日期**: 2026-05-01
**範圍**: W1+W2 audit 留下 8 項 P1 在後續 5 sprint（49.4 / 50.1 / 50.2 / 51.0 / 51.1 / 51.2）的處理狀態
**結論**: ❌ **Process Failure** — 8 項中 7 項完全未被任何後續 sprint plan/checklist 引用，多數仍是 W1+W2 audit 當下的狀態

---

## 摘要

- 8 項 P1 中：✅ Fixed **0** / 🟡 Scheduled **0** / 🟠 Acknowledged **1** / ❌ Dropped **7**
- 修復率（✅+🟡）：**0/8 = 0%**（理想 ≥ 75%）
- ❌ Dropped 中含關鍵 P1（W1-3 #1 verify_audit_chain）：**是**
- Process 評估：**Failure** — audit findings 未回流到 sprint planning，全部 8 項 P1 沒有任何 sprint plan 把它們列為 deliverable

> **註**：sprint 49.4 確實有 "AC-8: 49.3 carryover 5 項全清"，但那是 49.3 的 carryover（pg_partman / app_role guide / tool_calls FK / state_snapshots TRUNCATE / .ini lint），與 W1+W2 audit 8 項 P1 完全無交集。

---

## 8 項詳細狀態

| # | P1 項 | Phase A 代碼狀態 | Phase B Sprint Reference | Phase C 標籤 |
|---|-------|----------------|------------------------|------------|
| 1 | verify_audit_chain.py + cron | `backend/scripts/` 整個目錄不存在；grep `verify_audit_chain` / `recompute.*hash` / `walk.*chain` 全部 0 hit | 6 個後續 sprint plan/checklist 全部 0 hit；retrospective 全部 0 hit | ❌ **Dropped** |
| 2 | JWT 替換 X-Tenant-Id | `platform_layer/middleware/tenant_context.py` 仍 `HEADER_NAME = "X-Tenant-Id"`；`api/main.py` docstring 自承「JWT extraction (replaces X-Tenant-Id header in 49.5+)」 | 50.1 / 50.2 / 51.0-2 plan 全部 0 hit；49.4 plan 沒提；只有 49.4 retrospective 提到「Middleware required X-Tenant-Id」（運維問題，非 JWT 替換） | ❌ **Dropped** |
| 3 | 刪 `backend/src/middleware/tenant.py` | 檔案仍存在，內容仍是 49.1 stub，第 6 行明寫「Sprint 49.2 implements」（過期 3 個 sprint 未刪也未實作） | 6 個後續 sprint 全部 0 hit | ❌ **Dropped** |
| 4 | `adapters/azure_openai/tests/test_integration.py` | `backend/src/adapters/azure_openai/tests/` 目錄不存在；`backend/**/test_integration*` 0 hit | 6 個後續 sprint 全部 0 hit | ❌ **Dropped** |
| 5 | CI lint scope 擴大 | `.github/workflows/backend-ci.yml` 第 106 行仍只 lint `src/agent_harness/ src/infrastructure/`；`business_domain/`, `platform_layer/`, `api/` 仍未含 | 6 個後續 sprint 全部 0 hit | ❌ **Dropped** |
| 6 | requirements.txt 清理 Celery + 加 temporalio | `backend/requirements.txt` 第 27 行仍 `celery>=5.4,<6.0`；`temporalio` 0 hit | Phase 50/51 全部 0 hit；49.4 checklist 第 76 行有 `experimental/spike-celery/` 標籤但 requirements 未更動 | ❌ **Dropped** |
| 7 | Worker 目錄統一 | **二元並存惡化**：`platform_layer/workers/` 只有 README.md + `__init__.py`（規劃位置，空殼）；`runtime/workers/agent_loop_worker.py` + `queue_backend.py`（真實作）— AP-3 萌芽未解 | 6 個後續 sprint 全部 0 hit | ❌ **Dropped** |
| 8 | AgentLoopWorker 命名/警告 | Class 名仍是 `AgentLoopWorker`（未 rename）；**但** docstring 第 5 / 12-22 / 39-40 行已有「Phase 49.4 stub」「NOT in scope this sprint」「DEPRECATED-IN: 53.1」明確警告 — 部分滿足 P1（警告有，rename 無） | 49.4 retrospective 第 24 行確認「AgentLoopWorker stub (retry + cancellation + pluggable handler) ✅」；50.2 retrospective 第 177 行提及未來整合 | 🟠 **Acknowledged** (docstring 有警告但無 rename + 無 sprint 安排修正) |

---

## Process 紅旗分析

### 紅旗 1：被 drop 的 P1 中含最高風險項

**W1-3 #1 verify_audit_chain.py 完全 Dropped**。這是 W1 audit 評最高風險的項目（audit_log hash chain 寫了但無 verify 程式 = 偽合規），現在 5 sprint 過去仍 0 行代碼、0 plan reference、0 retrospective 提及。如此關鍵的合規項被靜默 drop = audit process 對最高風險項都失效。

### 紅旗 2：Sprint planning 完全未引用 W1+W2 audit findings

W1 audit 完成於 ~04-22，W2 完成於 04-29。最早可進入的 sprint 是 49.4（已開始）和之後 50.1/50.2/51.0/51.1/51.2。這 6 個 sprint 的 plan + checklist grep 8 項 P1 關鍵字（`verify_audit_chain` / `JWT` / `X-Tenant-Id` / `temporalio` / `test_integration` / `business_domain.*lint` / `carryover` / `W1-` / `W2-`）— **Phase 50 / Phase 51 全 0 hit**。49.4 的 carryover AC 是 49.3 的，與 audit 無關。**Audit findings 從未進入 sprint planning pipeline**。

### 紅旗 3：Retrospective 未誠實列 carryover

49.4 retrospective 用 ✅ 標記 "AgentLoopWorker stub" 而沒提 W2-2 #8 的 rename / prominent warning 是 P1 修補項。50.1 / 50.2 / 51.0 / 51.1 / 51.2 retrospective grep W1/W2 關鍵字 0 hit。retrospective 在描述「做完了什麼」，沒有「audit 給我們的功課還欠多少」段落。

### 紅旗 4：雙目錄並存惡化（W2-2 #7）

W2 audit 指出「workers/ 兩處並存萌芽」是 AP-3 (cross-directory scattering) 早期警訊。5 sprint 過去：`platform_layer/workers/` 仍是空殼（只有 README + `__init__.py`），`runtime/workers/` 仍是實作位置。**沒有合併也沒有正式 deprecation**，問題從「萌芽」變「定型」。

---

## 緊急修補建議

按優先序：

### 必修（Phase 52.x 結束前）

1. **W1-3 #1 verify_audit_chain.py**（合規最高風險；2-3 days effort）— 在 Phase 52.1 之內或之後立刻起 `sprint-52-X-audit-carryover` mini-sprint。沒有 verify 程式 = 寫了 hash chain 等於沒寫。
2. **W1-2 #2 JWT 替換**（安全；1-2 days）— 已過自承的 49.5 deadline，Phase 52 不能再拖；dev-only header 在 production 是 P0 risk。
3. **W1-2 #3 刪 stub middleware**（< 1 hour）— 這個是免費的：直接刪 + grep 確認無 import 引用。沒理由不做。
4. **W2-1 #5 CI lint scope**（< 1 hour）— 改 backend-ci.yml 第 106 行加 `src/business_domain/ src/platform_layer/ src/api/`，今天就能完成。

### 建議（Phase 53+ 也可）

5. **W2-1 #4 test_integration.py**（1 day）— 與 50.1 / 50.2 adapter 變動配套
6. **W2-2 #6 requirements 清理**（30 min）— 與 Phase 53.1 Temporal 落地一起做
7. **W2-2 #7 Worker 目錄統一**（半天）— Phase 53.1 Temporal 落地時不能再拖，否則 AP-3 定型
8. **W2-2 #8 AgentLoopWorker rename**（1 hour）— Phase 53.1 一起 rename + grep update

---

## 對 Audit Process 本身的建議

1. **Audit 結束時必須開 carryover ticket**：W1+W2 audit summary 寫了 P1 但沒在 sprint backlog / GitHub issues / `claudedocs/4-changes/` 開對應 ticket，導致它們僅存於 audit 文件本身、不會出現在 sprint planning 視野中。下次 audit 結束 SOP 必含「為每項 P1 建 ticket 並指派到具體 sprint」。
2. **Sprint plan 強制 carryover section**：Sprint plan template 加入「Audit Carryover」必填區，列出當前未完成的 audit P1 + 本 sprint 是否處理（接 / 推遲 / 不適用）。49.4 plan 有 AC-8 處理 49.3 carryover 是好做法 — 應推廣到所有 audit findings。
3. **Retrospective 加「audit debt」段落**：50.1+ retrospective 缺「audit debt 清單」，導致每 sprint 結束 audit findings 再 drift 一輪。
4. **Audit 自身定期 re-verify**：本次 W3-0 就是這個機制；應每 2-3 sprint 跑一次（防止 drift > 6 sprint 累積）。

---

## 阻塞 Phase 52+ 啟動?

⚠️ **部分阻塞** — 8 項 P1 整體不是直接技術阻塞，但 **W1-3 #1 verify_audit_chain** 是合規 P0：若 Phase 52 結束前不修，所有 audit_log 的「不可篡改」聲明都是空話；若 Phase 55 進 canary / SaaS Stage 1 還沒修，會被合規評審直接擋下。**W1-2 #2 JWT 替換** 同樣是 production 必修，再拖違反「server-side first」第一原則。

建議：在進入 Phase 52.2 之前，先用半個 sprint（~3 day mini-sprint）清掉「必修 4 項」（W1-3 #1 / W1-2 #2 / W1-2 #3 / W2-1 #5），總計約 4-5 工作天，剩下 4 項排入 Phase 53.1。
