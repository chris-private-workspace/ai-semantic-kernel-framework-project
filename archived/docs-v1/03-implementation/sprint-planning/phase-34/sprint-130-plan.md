# Sprint 130: Correlation/RootCause 真實資料連接

## 概述

Sprint 130 將 Correlation（事件關聯分析）和 RootCause（根因分析）模組從硬編碼/偽造資料遷移到真實事件資料源，使可觀測性模組能產出有意義的分析結果。

## 目標

1. Correlation 模組連接真實事件來源（OTel、Application Insights）
2. RootCause 模組連接真實歷史案例庫
3. 移除硬編碼/偽造資料返回
4. 建立事件資料管線

## Story Points: 20 點

## 前置條件

- ⬜ Sprint 128-129 完成
- ⬜ Azure Monitor / Application Insights 可存取
- ⬜ OTel 資料已開始收集（Phase 33 Sprint 122）

## 任務分解

### Story 130-1: Correlation 真實資料 (3 天, P2)

**現狀問題**:
- `src/integrations/correlation/` 返回完全偽造的關聯資料
- 無真實事件來源連接

**遷移方案**:
- 連接 Azure Monitor / Application Insights API
- 從 OTel traces/metrics 提取關聯事件
- 基於時間窗口和服務名稱進行真實關聯

**交付物**:
- `src/integrations/correlation/data_source.py` — 真實資料來源
- `src/integrations/correlation/event_collector.py` — 事件收集器
- 移除偽造資料生成代碼

### Story 130-2: RootCause 真實案例庫 (3 天, P2)

**現狀問題**:
- `src/integrations/rootcause/analyzer.py` 返回硬編碼 2 個 HistoricalCase
- 無真實歷史案例來源

**遷移方案**:
- 建立 PostgreSQL 案例表（歷史事件 + 解決方案）
- 從 ServiceNow 已關閉 Incident 匯入歷史案例
- LLM 輔助案例匹配（語義相似度）

**交付物**:
- `src/integrations/rootcause/case_repository.py` — 案例儲存庫
- `src/integrations/rootcause/case_matcher.py` — 案例匹配引擎
- Alembic migration（案例表）
- 移除硬編碼 HistoricalCase

### Story 130-3: 測試與驗證 (1 天, P2)

**測試範圍**:

| 測試 | 範圍 |
|------|------|
| `test_correlation_data_source.py` | 真實資料來源 |
| `test_event_collector.py` | 事件收集與關聯 |
| `test_case_repository.py` | 案例 CRUD |
| `test_case_matcher.py` | 語義案例匹配 |

## 依賴

- 改善提案 Phase D P2: Correlation/RootCause 真實資料
- Azure Monitor API 存取權限
- Phase 33 OTel 基礎設施
