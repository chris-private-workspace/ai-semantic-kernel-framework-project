# Sprint 95: InputGateway + SourceHandlers

## 概述

Sprint 95 專注於建立 **InputGateway** 輸入閘道和 **SourceHandlers** 來源處理器，實現系統來源的簡化處理路徑。

## 目標

1. 實現 InputGateway 主類 - 來源識別和分流
2. 實現 BaseSourceHandler 抽象基類
3. 實現 ServiceNowHandler (映射表 + Pattern)
4. 實現 PrometheusHandler (告警處理)
5. 實現 UserInputHandler (完整三層路由)
6. 實現 SchemaValidator (結構驗證)

## Story Points: 25 點

---

## Story 進度

### Story 95-1: 實現 InputGateway 主類 (3h, P0)

**狀態**: ✅ 完成

**交付物**:
- `backend/src/integrations/orchestration/input_gateway/__init__.py`
- `backend/src/integrations/orchestration/input_gateway/gateway.py`
- `backend/src/integrations/orchestration/input_gateway/models.py`

**完成項目**:
- [x] InputGateway 類實現完成
- [x] process() 方法根據來源分流
- [x] 系統來源 → SourceHandler
- [x] 用戶來源 → BusinessIntentRouter
- [x] IncomingRequest 數據模型

---

### Story 95-2: 實現 BaseSourceHandler (2h, P0)

**狀態**: ✅ 完成

**交付物**:
- `backend/src/integrations/orchestration/input_gateway/source_handlers/__init__.py`
- `backend/src/integrations/orchestration/input_gateway/source_handlers/base_handler.py`

**完成項目**:
- [x] BaseSourceHandler ABC 定義完成
- [x] process() 抽象方法定義
- [x] 通用輔助方法實現 (build_routing_decision, extract_metadata)

---

### Story 95-3: 實現 ServiceNowHandler (4h, P0)

**狀態**: ✅ 完成

**交付物**:
- `backend/src/integrations/orchestration/input_gateway/source_handlers/servicenow_handler.py`

**映射表覆蓋**:
| ServiceNow Category | IT Intent | Sub Intent |
|--------------------|-----------|------------|
| incident/hardware | incident | hardware_failure |
| incident/software | incident | software_issue |
| incident/network | incident | network_failure |
| incident/database | incident | database_issue |
| incident/security | incident | security_incident |
| request/account | request | account_request |
| request/access | request | access_request |
| request/software | request | software_request |
| request/hardware | request | hardware_request |
| change/standard | change | standard_change |
| change/emergency | change | emergency_change |
| change/normal | change | normal_change |

**完成項目**:
- [x] ServiceNowHandler 類實現完成
- [x] 映射表定義完成 (12 種場景)
- [x] 當 subcategory 不足時使用 PatternMatcher
- [x] 跳過 Semantic Router 和 LLM Classifier
- [x] 延遲 < 10ms

---

### Story 95-4: 實現 PrometheusHandler (3h, P1)

**狀態**: ✅ 完成

**交付物**:
- `backend/src/integrations/orchestration/input_gateway/source_handlers/prometheus_handler.py`

**告警映射覆蓋**:
| Alert Name Pattern | IT Intent | Sub Intent |
|-------------------|-----------|------------|
| `*high_cpu*` | incident | performance_issue |
| `*high_memory*`, `*memory_*` | incident | memory_issue |
| `*disk_*`, `*storage_*` | incident | disk_issue |
| `*_down*`, `*unavailable*` | incident | service_down |
| `*latency*`, `*slow*` | incident | latency_issue |
| `*error_rate*`, `*5xx*` | incident | error_rate_issue |
| `*certificate*`, `*ssl*` | incident | certificate_issue |
| `*network*`, `*connection*` | incident | network_issue |

**完成項目**:
- [x] PrometheusHandler 類實現完成
- [x] 告警名稱模式匹配 (8 種場景)
- [x] 告警標籤提取
- [x] 嚴重性到風險等級映射
- [x] 延遲 < 10ms

---

### Story 95-5: 實現 UserInputHandler (2h, P0)

**狀態**: ✅ 完成

**交付物**:
- `backend/src/integrations/orchestration/input_gateway/source_handlers/user_input_handler.py`

**完成項目**:
- [x] UserInputHandler 類實現完成
- [x] 調用完整三層路由 (BusinessIntentRouter)
- [x] 格式標準化
- [x] 元數據增強

---

### Story 95-6: 實現 SchemaValidator (3h, P0)

**狀態**: ✅ 完成

**交付物**:
- `backend/src/integrations/orchestration/input_gateway/schema_validator.py`

**支援 Schema**:
- ServiceNow Webhook Schema
- Prometheus Alertmanager Schema
- User Input Schema (可選)

**完成項目**:
- [x] SchemaValidator 類實現完成
- [x] 支援 ServiceNow Schema
- [x] 支援 Prometheus Schema
- [x] 驗證錯誤有明確訊息
- [x] ValidationError 異常類

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

## 完成日期

- **開始日期**: 2026-01-15
- **完成日期**: 2026-01-15
- **Story Points**: 25 / 25 完成 (100%)
