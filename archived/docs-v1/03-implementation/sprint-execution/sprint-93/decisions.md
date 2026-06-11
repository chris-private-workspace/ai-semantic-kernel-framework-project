# Sprint 93 技術決策記錄

## 決策列表

### D93-1: BusinessIntentRouter 架構設計

**決策**: 採用三層降級路由架構

**選項**:
1. 三層降級路由 (Pattern → Semantic → LLM) (選擇)
2. 並行路由 + 最佳結果選擇
3. 單層 LLM 分類

**選擇**: 選項 1

**理由**:
- 效能優化：Pattern (< 10ms) > Semantic (< 100ms) > LLM (< 2000ms)
- 成本控制：優先使用低成本層級，LLM 作為最後手段
- 可預測性：Pattern 規則結果確定，適合高頻場景
- 彈性：各層閾值可獨立配置

---

### D93-2: CompletenessChecker 整合位置

**決策**: 在 BusinessIntentRouter 內整合完整度檢查

**選項**:
1. 在 Router 內 `_build_decision()` 時檢查 (選擇)
2. 作為獨立後處理步驟
3. 每層路由各自檢查

**選擇**: 選項 1

**理由**:
- 統一輸出：RoutingDecision 包含完整度資訊
- 減少調用：一次路由返回完整結果
- 簡化整合：下游組件只需處理 RoutingDecision
- 維護性：完整度邏輯集中管理

---

### D93-3: 完整度規則配置方式

**決策**: 使用 Python dataclass 定義規則，支援 YAML 配置覆蓋

**選項**:
1. Python dataclass + YAML 覆蓋 (選擇)
2. 純 YAML 配置
3. 純代碼定義
4. 資料庫儲存

**選擇**: 選項 1

**理由**:
- 類型安全：dataclass 提供 IDE 支援和類型檢查
- 靈活性：YAML 可覆蓋預設值，無需修改代碼
- 預設合理：內建預設規則，開箱即用
- 易於測試：Python 定義方便單元測試

---

### D93-4: 欄位提取策略

**決策**: 使用關鍵字匹配 + 正則表達式提取

**選項**:
1. 關鍵字 + 正則 (選擇)
2. 純 LLM 提取
3. NER 命名實體識別
4. 結構化表單解析

**選擇**: 選項 1

**理由**:
- 效能：無需額外 API 調用
- 準確度：IT 領域關鍵字明確
- 成本：零額外成本
- 延遲：幾乎不增加處理時間

---

### D93-5: 閾值配置策略

**決策**: 環境變數配置，支援執行時調整

**配置**:
| 閾值 | 環境變數 | 預設值 | 範圍 |
|------|---------|--------|------|
| Pattern 置信度 | `PATTERN_CONFIDENCE_THRESHOLD` | 0.90 | 0.80-0.99 |
| Semantic 相似度 | `SEMANTIC_SIMILARITY_THRESHOLD` | 0.85 | 0.70-0.95 |
| Incident 完整度 | `COMPLETENESS_INCIDENT_THRESHOLD` | 0.60 | 0.40-0.80 |
| Request 完整度 | `COMPLETENESS_REQUEST_THRESHOLD` | 0.60 | 0.40-0.80 |
| Change 完整度 | `COMPLETENESS_CHANGE_THRESHOLD` | 0.70 | 0.50-0.90 |
| Query 完整度 | `COMPLETENESS_QUERY_THRESHOLD` | 0.50 | 0.30-0.70 |

**理由**:
- 運維友好：無需重新部署即可調整
- 監控支援：可根據生產數據調整
- 環境區分：開發/測試/生產可用不同閾值

---

### D93-6: 風險等級判定邏輯

**決策**: 基於意圖類型 + 關鍵字組合判定

**規則**:
| 意圖 | 關鍵字 | 風險等級 |
|------|--------|---------|
| Incident | 緊急、嚴重、生產 | CRITICAL |
| Incident | 影響、無法 | HIGH |
| Change | 生產、資料庫 | HIGH |
| Change | 部署、更新 | MEDIUM |
| Request | 帳號、權限 | MEDIUM |
| Query | * | LOW |

**理由**:
- 業務對齊：反映 IT 服務管理實際風險
- 可審計：規則明確，易於解釋
- 可擴展：新規則可輕鬆添加

---

### D93-7: 工作流類型映射

**決策**: 根據意圖類型和複雜度自動選擇工作流

**映射**:
| 意圖 | 子意圖 | 工作流類型 |
|------|--------|-----------|
| Incident | system_unavailable | MAGENTIC |
| Incident | etl_failure | SEQUENTIAL |
| Change | release_deployment | MAGENTIC |
| Change | configuration_update | SEQUENTIAL |
| Request | account_creation | SIMPLE |
| Query | * | SIMPLE |

**理由**:
- 資源優化：簡單任務不需複雜工作流
- 使用者體驗：匹配任務複雜度
- 可配置：映射可透過配置調整

---

**創建日期**: 2026-01-15
**更新日期**: 2026-01-15
