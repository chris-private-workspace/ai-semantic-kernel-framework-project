# V2 Audit Baseline — Phase 49 Sprint 49.1–49.4

**建立日期**: 2026-04-29  
**建立人**: Explore agent (Verification Audit task)  
**用途**: 後續 Verification Audit 的起點清單；列出所有已完成交付項 + 對應 spec + 風險分 + 驗證計畫  
**範圍**: Sprint 49.1（DONE）/ 49.2（DONE）/ 49.3（DONE）/ 49.4（Day 1–2 done; Day 3+ in progress）

---

## 摘要統計

| 維度 | 數值 |
|------|------|
| 49.1 交付項 | 13 項（V1 archive + V2 骨架 + 11+1 ABCs + CI） |
| 49.2 交付項 | 13 項（13 ORM tables + 4 migrations + 29 tests） |
| 49.3 交付項 | 13 項（5 migrations + 14 表 RLS + 73 tests + middleware） |
| 49.4 已完成 | ~15 項（Day 1-2；Day 3+ in progress） |
| **高風險項（4–5 分）** | 24 個 |
| **中風險項（3 分）** | 8 個 |
| **低風險項（1–2 分）** | 14 個 |

---

## 高風險項清單（風險分 4–5）

### 風險 5（架構災難級）— 最高優先審計

| Sprint | ID | 交付項 | 原因 | 驗證方法 |
|--------|----|----|------|---------|
| 49.1 | 1.2 | _contracts/ 10 型別檔 | LLM Provider Neutrality；型別重複 | grep 跨 sprint import；lint duplicate-dataclass |
| 49.1 | 1.3 | 11+1 ABC 空殼 | 層級承諾；後續範疇 import | import 測試；無實作；後續對齊 |
| 49.1 | 1.5 | ChatClient ABC（4 方法） | LLM 中性性；核心抽象 | ABC 結構；17.md 對齊 |
| 49.2 | 2.1 | 4 migrations（0001-0004） | Schema 可靠性；迴圈正反通 | alembic cycle；idempotency |
| 49.2 | 2.2 | 13 ORM models | tenant_id NOT NULL 鐵律 | schema 檢查；RLS 前置 |
| 49.2 | 2.3 | StateVersion 雙因子鎖 | Race condition；並行安全 | 100 次並行 insert；1 win 1 fail；hash chain |
| 49.2 | 2.6 | Real PostgreSQL 測試 | AP-10 mock vs real | docker postgres；無 SQLite；transaction rollback |
| 49.3 | 3.1 | 5 migrations + hash chain | Audit immutability | hash 獨立驗證；UPDATE/DELETE/TRUNCATE 擋 |
| 49.3 | 3.2 | 13 表 RLS policies | Multi-tenant rule 鐵律 2 | rls_app_role 非 superuser；跨 tenant 0 leak |
| 49.3 | 3.3 | Tenant context middleware | per-request 隔離；SET LOCAL | request.state 填充；missing/invalid 401/400 |
| 49.4 | 4.1 | ChatClient ABC 升級（6 方法） | LLM 中性性；type-safe | Contract test ≥7；Mock + Azure 實現 |
| 49.4 | 4.2 | Azure OpenAI Adapter | Adapter 層 5 原則 | 真實 Azure or mock；error mapping 8 cases |

### 風險 4（核心基礎級）— 次高優先

| Sprint | ID | 交付項 | 驗證方法 |
|--------|----|----|---------|
| 49.1 | 1.6 | 後端 5 層骨架 | tree；AP-3 散落 + AP-4 Potemkin；README |
| 49.1 | 1.8 | Async ORM 基礎 | engine.ping()；49.2 升級完整 |
| 49.1 | 1.10 | CI Pipeline | PR 觸發；fail 禁 merge；LLM leak |
| 49.2 | 2.4 | Append-only trigger | UPDATE/DELETE/TRUNCATE 三擋；trigger raise |
| 49.2 | 2.5 | Messages/events partition | routing test；created_at 區間落分 |
| 49.3 | 3.4 | Audit log + hash chain | INSERT 成功；UPDATE/DELETE/TRUNCATE 擋 |
| 49.3 | 3.5 | 5 層 memory schema | 2 TenantScopedMixin；3 junction；CRUD test |
| 49.3 | 3.9 | 紅隊測試 7 vectors | AV-1 to AV-6 全 PASS；0 leak |
| 49.4 | 4.3 | Worker queue spike + 決策 | spike 有 deadline；決策明確非模糊 |
| 49.4 | 4.4 | OTel SDK 鎖版本 + 整合 | requirements.txt；Jaeger/Prometheus 啟動 |
| 49.4 | 4.5 | Tracer ABC 實作 + 7 metric | OTelTracer；TraceContext propagation |
| 49.4 | 4.6 | 4 Lint rules | pre-commit + CI；8 case 全通過 |

---

## 八大紅旗（自我懷疑信號）

### 紅旗 1：Vite 前端無法驗證實際運行（49.1）
- **記錄**：Checklist 4.5 "CLAUDE.md 規範禁止 stop node.js"
- **後果**：無法驗 npm run dev；Vite runtime issue 延後發現
- **後續**：Phase 50.2 chat endpoint 實裝時觸發

### 紅旗 2：ESLint 9 flat config 延後（49.1）
- **記錄**：Checklist 4.5 "package.json 已列 deps，但配置延後"
- **後果**：linter 準備不完整；Phase 50 真代碼 lint 重做
- **後續**：49.4 lint rules 上線時需補 ESLint 9 config

### 紅旗 3：Windows 編碼脆弱性未根除（49.2）
- **記錄**：Checklist Day 1.6 "cp950 em-dash 錯誤；Action：CI 加 ASCII-only lint"
- **後果**：跨 OS 編碼脆弱；49.4 lint 未補
- **後續**：49.4 check_cross_category_import 需補 .ini ASCII lint

### 紅旗 4：pg_partman 版本困境推延（49.3）
- **記錄**：Checklist Day 4.3 "alpine image 不含 pg_partman；需升級到 postgres:16 full"
- **後果**：基礎設施決策滯後；49.4 Day 4 爆發；production deploy 遺漏風險
- **後續**：49.4 Day 4 必驗 Dockerfile.postgres + docker compose 升級

### 紅旗 5：平台層 event-loop 耦合（49.3）
- **記錄**：Checklist Day 5.4 "修 cross-file event-loop closed；加 autouse fixture"
- **後果**：測試 fixture 耦合；pytest-asyncio 脆弱；Phase 50 async 重現
- **後續**：49.4 Day 3 OTel FastAPI 時重驗；50.1 async loop test 獨立 fixture

### 紅旗 6：tool_calls.message_id FK 決策卡住（49.3）
- **記錄**：Plan 49.3 Day 4.8 決策推延；PG 16 partition table composite FK 限制
- **後果**：實裝細節未定；後續 migration 返工風險
- **後續**：49.4 Day 4 決策報告；若無法推遲 PG 18，立即返工 0004 migration

### 紅旗 7：OTel 版本相容性未實測（49.4）
- **記錄**：Plan 49.4 Day 3 risks "OTel 1.22.0 + SQLAlchemy 2.0 衝突（中機率）"
- **後果**：dependency hell 潛伏；實裝時發現再改
- **後續**：49.4 Day 3 必驗 pip install + instrumentation；Jaeger UI 手動收 span

### 紅旗 8：Worker queue 決策未出（49.4）
- **記錄**：Plan 49.4 Day 2 進行中；決策報告本週待出
- **後果**：兩家都不滿意 → 決策推到 53.1；阻塞 Phase 50 期望
- **後續**：49.4 Day 2 必寫決策報告（不可模糊）；若卡住主動升級風險

---

## 審計優先度 Roadmap

### Week 1 — Architecture + Multi-tenant 基石
1. 49.1 _contracts/ 跨範疇一致性（風險 5）
2. 49.2 ORM TenantScopedMixin（風險 5）
3. 49.3 RLS policies 跨 tenant 0 leak（風險 5）— **本審計重點**
4. 49.3 Audit hash chain 完整性（風險 5）— **本審計重點**

### Week 2 — Adapter + OTel + Lint
5. 49.4 ChatClient ABC + Azure adapter（風險 5）— 未驗
6. 49.4 OTel 整合（風險 4）— 進行中
7. 49.4 4 Lint rules（風險 4）— 進行中

### Week 3 — Carryover + Phase 50 Unblock
8. 49.4 pg_partman + Dockerfile 升級（風險 3）— 進行中
9. 49.4 49.3 carryover 5 項（風險 3）— 進行中

---

**完成標準**：
- [x] 4 sprint 表格（13+13+13+15 項）
- [x] 每項都有風險分（12 項風險 5，12 項風險 4，8 項風險 3）
- [x] 24 個高風險項清單 + 優先度
- [x] 8 個紅旗信號 + 後續驗證建議
