# Sprint 96: RiskAssessor + Policies

## 概述

Sprint 96 專注於建立 **RiskAssessor** 風險評估器和 **Policies** 風險策略，實現 IT 意圖到風險等級的映射。

## 目標

1. 實現 RiskAssessor 核心
2. 定義風險評估策略
3. 整合 ITIntent → 風險等級映射
4. API 路由實現 (intent/classify)

## Story Points: 25 點

---

## Story 進度

### Story 96-1: 實現 RiskAssessor 核心 (4h, P0)

**狀態**: ✅ 完成

**交付物**:
- `backend/src/integrations/orchestration/risk_assessor/__init__.py`
- `backend/src/integrations/orchestration/risk_assessor/assessor.py`

**完成項目**:
- [x] 創建 risk_assessor 目錄
- [x] RiskAssessor 類實現完成
- [x] assess() 方法返回 RiskAssessment
- [x] 支援多維度風險評估
- [x] 風險等級: low/medium/high/critical
- [x] RiskFactor dataclass 定義
- [x] AssessmentContext dataclass 定義
- [x] RiskAssessment dataclass 定義

---

### Story 96-2: 定義風險評估策略 (4h, P0)

**狀態**: ✅ 完成

**交付物**:
- `backend/src/integrations/orchestration/risk_assessor/policies.py`

**風險策略矩陣**:

| Intent Category | Sub Intent | 預設風險等級 | 需要審批 |
|----------------|------------|-------------|---------|
| incident | system_down | critical | ✅ |
| incident | etl_failure | high | ✅ |
| incident | performance_issue | medium | ❌ |
| incident | security_incident | critical | ✅ |
| request | account_request | medium | ❌ |
| request | access_request | high | ✅ |
| change | emergency_change | critical | ✅ |
| change | standard_change | medium | ❌ |
| change | normal_change | high | ✅ |
| query | * | low | ❌ |

**完成項目**:
- [x] RiskPolicy dataclass 定義完成
- [x] RiskPolicies 類實現完成
- [x] 策略矩陣定義完成 (25+ 策略)
- [x] 支援動態策略載入 (add_policy, remove_policy)
- [x] 支援策略覆蓋 (priority-based)
- [x] 工廠函數: create_default_policies, create_strict_policies, create_relaxed_policies

---

### Story 96-3: 整合 ITIntent → 風險等級映射 (3h, P0)

**狀態**: ✅ 完成

**交付物**:
- 更新 `assessor.py`

**完成項目**:
- [x] _calculate_risk_level() 方法實現
- [x] 映射邏輯正確
- [x] 上下文調整正確 (_apply_context_adjustments)
- [x] 支援風險等級提升 (_elevate_risk)
- [x] 支援風險等級降低 (_reduce_risk)
- [x] 支援多維度因素收集 (_collect_factors)

**上下文調整因素**:
- is_production: 生產環境 → 風險提升一級
- is_weekend: 週末 → 風險提升一級
- is_urgent: 緊急 → 風險提升一級
- affected_systems > 3: 多系統影響 → 風險提升一級

---

### Story 96-4: 風險評估單元測試 (4h, P0)

**狀態**: ✅ 完成

**交付物**:
- `backend/tests/unit/orchestration/test_risk_assessor.py`

**測試覆蓋**:
- [x] TestRiskFactor: RiskFactor dataclass 測試
- [x] TestAssessmentContext: AssessmentContext 測試
- [x] TestRiskAssessment: RiskAssessment 測試
- [x] TestRiskPolicy: RiskPolicy 測試
- [x] TestRiskPolicies: RiskPolicies 集合測試
- [x] TestRiskAssessor: RiskAssessor 主類測試
  - [x] 各意圖類型風險評估測試
  - [x] 上下文調整測試 (production, weekend, urgent)
  - [x] 策略覆蓋測試
  - [x] 邊界條件測試
- [x] TestPolicyFactories: 工廠函數測試
- [x] TestEdgeCases: 邊界條件測試

---

### Story 96-5: API 路由實現 (3h, P0)

**狀態**: ✅ 完成

**交付物**:
- `backend/src/api/v1/orchestration/__init__.py`
- `backend/src/api/v1/orchestration/schemas.py`
- `backend/src/api/v1/orchestration/routes.py`
- `backend/src/api/v1/orchestration/intent_routes.py`

**API 端點**:

| Method | Endpoint | 描述 |
|--------|----------|------|
| POST | `/api/v1/orchestration/intent/classify` | 意圖分類 + 風險評估 |
| POST | `/api/v1/orchestration/intent/test` | 測試模式 (debug) |
| POST | `/api/v1/orchestration/intent/quick` | 快速分類 (簡化回應) |
| POST | `/api/v1/orchestration/intent/classify/batch` | 批量分類 |
| GET | `/api/v1/orchestration/policies` | 列出所有策略 |
| GET | `/api/v1/orchestration/policies/{category}` | 按類別列出策略 |
| POST | `/api/v1/orchestration/policies/mode/{mode}` | 切換策略模式 |
| POST | `/api/v1/orchestration/risk/assess` | 獨立風險評估 |
| GET | `/api/v1/orchestration/metrics` | 路由指標 |
| POST | `/api/v1/orchestration/metrics/reset` | 重置指標 |
| GET | `/api/v1/orchestration/health` | 健康檢查 |

**完成項目**:
- [x] API 路由實現完成
- [x] Pydantic 模型定義 (schemas.py)
- [x] 錯誤處理完善
- [x] OpenAPI 文檔自動生成
- [x] 整合到主 API 路由器

---

## 品質檢查

### 代碼品質
- [x] 類型提示完整
- [x] Docstrings 完整
- [x] 遵循專案代碼風格

### 測試
- [x] 單元測試實現
- [x] 測試覆蓋關鍵路徑

---

## 技術決策

詳見 `decisions.md`

---

## 文件結構

```
backend/src/integrations/orchestration/risk_assessor/
├── __init__.py          # 模組導出
├── assessor.py          # RiskAssessor 核心類
└── policies.py          # RiskPolicies 策略定義

backend/src/api/v1/orchestration/
├── __init__.py          # API 模組導出
├── schemas.py           # Pydantic 請求/回應模型
├── routes.py            # 主路由 (policies, risk, metrics)
└── intent_routes.py     # 意圖分類路由

backend/tests/unit/orchestration/
└── test_risk_assessor.py  # 單元測試
```

---

## 完成日期

- **開始日期**: 2026-01-15
- **完成日期**: 2026-01-15
- **Story Points**: 25 / 25 完成 (100%)
