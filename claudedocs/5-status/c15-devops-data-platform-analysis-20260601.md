# C-15 深度分析:DevOps IaC / multi-region / DR + Data platform

**Purpose**: 盤點 DevOps(IaC / 部署 / DR / multi-region)+ Data platform(Outbox / billing 雙扣 / analytics)的 repo 真實狀態。**重大校正:盤點「無 Terraform」措辭誤導 —— `infra/` 有完整 Bicep IaC(5 模組);真正缺的是 DR 自動化 / multi-region / Outbox 實作 / analytics。** 本檔為 research 分析(非 sprint plan)。
**Category**: DevOps / Infrastructure / Data architecture
**Scope**: C 區研究分析 / C-15
**Created**: 2026-06-01
**Status**: Active(analysis;infra 最佳實踐須外部查證)

**Modification History (newest-first)**:
- 2026-06-01: Initial creation — C-15 DevOps/Data(Workflow 蒐證 + 主 session 親驗 infra/ Bicep 存在 + outbox 0 實作)

**Related**:
- `integration-progress-20260531.md` §15 + §132(C-15 來源;其「無 Terraform」措辭本檔校正)
- `enterprise-saas-gap-analysis-20260508.md`(Top 10 gaps:#8 IaC、#10 Outbox)
- `docs/03-implementation/agent-harness-planning/13-deployment-and-devops.md`
- `cat8-errorbudget-redis-wiring-analysis`(B-7,billing 同屬 cost 正確性議題)

---

## 0. 一句話結論

> **IaC 不是「無」** —— `infra/` 有完整 Bicep(main.bicep + deploy.sh + 5 模組 + parameters,親驗),盤點 §132「無 Terraform」措辭誤導(正確說法:有 Bicep、無 Terraform、無 Helm/Pulumi)。**真正的缺口**是:① `deploy-production.yml` 故意 disabled(Azure 未 provision)② DR 自動化 / multi-region / WAL = 0 ③ **Outbox 完全未實作**(只有 schema 設計)→ billing 雙扣風險 ④ analytics/data warehouse = 0%。

---

## 1. ✅ IaC 存在(校正盤點「無 Terraform」措辭,親驗)

親驗 `ls infra/`:
```
infra/main.bicep + deploy.sh + modules/ + parameters/
modules/: app-service.bicep, container-registry.bicep, database.bicep, monitoring.bicep, redis.bicep
```
| 事實 | 證據 |
|------|------|
| **Bicep IaC 完整**(5 模組,target Azure App Service + ACR + Flexible Postgres + Redis)| `infra/main.bicep` + `infra/modules/*.bicep`(親驗 5 檔)|
| Terraform 只在 archive | `archived/v1-phase1-48/infrastructure/terraform/`(V1,非 active)|
| 無 Helm / Pulumi | `13-deployment-and-devops.md:839` Helm 標 Phase 56+;Glob helm/pulumi → 0 |

> **校正**:盤點 §132「~30%,無 Terraform」→ 應為「有 Bicep IaC(未驗證部署過),無 Terraform/Helm,deploy pipeline disabled」。「無 Terraform」字面真,但暗示「無 IaC」是誤導 —— **有 IaC,只是 Bicep 不是 Terraform**。

---

## 2. 部署管線:故意 disabled(親驗)

| 事實 | 證據 |
|------|------|
| `deploy-production.yml` 存在但 **push trigger 註解掉**,只剩 `workflow_dispatch` | `.github/workflows/deploy-production.yml`(AD-CI-6)|
| 原因:Azure App Service / ACR 未 provision + GitHub Secrets 未設 | 同上 :5-19 |
| active CI:backend-ci / frontend-ci / e2e-tests / lint / playwright / lighthouse / **e2e-real-llm-smoke** | `ls .github/workflows/`(親驗 8 檔)|
| docker-compose.dev.yml 是唯一 active 部署機制 | `docker-compose.dev.yml` |

> 註:`e2e-real-llm-smoke.yml` 即 C-11 的 real-LLM gate(此處印證它確實 active)。

---

## 3. DR / multi-region:文件有、實作 0(親驗)

| 項 | 狀態 | 證據 |
|----|------|------|
| DR 計畫(RPO 1h / RTO 4h、quarterly drill)| 📄 文件 only | `13-deployment-and-devops.md:919-938` |
| Backup 自動化腳本 | ❌ 0(`scripts/` 只有 mvp-validation.sh)| gap-analysis:287「0 backup automation; DR drill 從未執行」|
| WAL streaming / read replica / multi-region | ❌ 0 | `grep multi.region\|WAL backend/src` → 0;gap-analysis:288 |
| Bicep 是否曾成功部署 | ❓ 無證據 | deploy-production disabled;repo 無部署紀錄 |

---

## 4. 🔴 Outbox 完全未實作 → billing 雙扣風險(親驗)

| 事實 | 證據 |
|------|------|
| Outbox 表**只有 schema 設計**(設計文件)| `09-db-schema-design.md:1002-1029` |
| **無 outbox migration**(0011 是 approvals_status_check,非 outbox)| 親驗 `git ls-files \| grep outbox` → 0;`grep outbox migrations` → 0 |
| **無 outbox worker** | 親驗 `git ls-files \| grep outbox` → 0 backend 檔 |
| cost_ledger 雙扣風險:`record_llm_call` 在 SSE observer 的 bare try/except,**無交易包住 LLM call + ledger write** | `router.py:402-427`(best-effort,catch 後靜默跳過)|
| ledger 用 `db.flush()` 非 commit,依賴 session 交易,**未與 LLM 完成事件原子耦合** | `cost_ledger.py:161-183` |
| gap analysis 列為 Gap #10:「Stripe billing 雙扣/漏扣風險」| gap-analysis:72,106,294 |

> **雙扣/漏扣機制**:cost_ledger write 與 LLM call 不在同一交易 → ① LLM 成功但 ledger write 例外被 catch → **漏扣** ② 重試/部分失敗無 idempotency key → 潛在**雙扣**。Outbox pattern 正是解這個(transactional outbox + idempotent worker),但**完全未實作**。
> 註:此與 B-7(budget 跨實例)、B-8(judge token 漏記)同屬「cost 正確性」家族 —— real-LLM 上線前的 billing 完整性是一組相關債。

---

## 5. Analytics / Data platform:0%(親驗)

| 項 | 狀態 | 證據 |
|----|------|------|
| Analytics / data warehouse / CDC / dbt / BI | ❌ 0% | gap-analysis:292「無 CDC/warehouse/dbt/BI」|
| Data quality(OpenLineage/DataHub/contract tests)| ❌ 0/0 | gap-analysis:297 |
| Product analytics(Amplitude/Mixpanel/PostHog)| ❌ 0(只有 Cat 12 telemetry)| gap-analysis:330 |
| `19-data-platform-architecture.md` 規劃文件 | ❌ 未建 | gap-analysis:135,440 |

---

## 6. 🔴 需外部查證(infra 最佳實踐,本檔不捏造)

1. **Outbox + SQLAlchemy async**:flush-then-commit 是否足夠原子,還是需顯式 SAVEPOINT/BEGIN 與業務事件配對。
2. **Azure Postgres Flexible Server** 內建 backup/geo-redundancy 是否滿足 RPO 1h/RTO 4h(可能不需自寫腳本)。
3. **Multi-region Azure App Service** pattern(Traffic Manager vs Front Door vs regional stamp)。
4. **EU CRA** SBOM/Cosign/Trivy 確切技術義務(與 C-14 重疊,須法務+官方)。

---

## 7. 給決策的最短建議(優先序)

| # | 項 | 嚴重度 | 建議 |
|---|----|:---:|------|
| 1 | **cost_ledger 雙扣/漏扣** | 🔴 高(real-LLM 上線即真金白銀)| 與 B-7/B-8 合為「billing 正確性」spike:idempotency key + 交易耦合;Outbox 是完整解但可分階段 |
| 2 | Outbox 實作 | 🟡 中 | schema 已設計;建 migration + worker(thin spike,非預寫文件)|
| 3 | DR 自動化 / backup | 🟡 中 | 先查 §6.2 Azure 內建能力,可能不需自寫;DR drill 至少跑 1 次 |
| 4 | deploy-production 啟用 | 🟡 中 | 需 Azure provision + Secrets(同 C-11 前提)|
| 5 | analytics / data platform | 🟢 低 | 0% 但非當前阻塞;`19-data-platform-architecture.md` 待 thin spike |

| 校正項 | 結論 |
|--------|------|
| 盤點 §132「無 Terraform」 | ⚠️ 誤導 —— 有 Bicep IaC,無 Terraform/Helm;建議改措辭(改盤點需授權)|
| IaC 真實狀態 | Bicep 完整(未驗部署)、pipeline disabled、DR/multi-region/Outbox/analytics 缺 |

> 不需 code(分析層)。最高槓桿:**cost_ledger 雙扣/漏扣**(real-LLM 上線即真實財務風險),建議與 B-7/B-8 合為一個「billing 正確性」工作束。
