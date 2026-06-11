# Sprint 33: 差異化功能驗證與收尾

**Sprint 目標**: 解決所有 P2 級別問題，驗證差異化功能，準備 UAT
**總點數**: 22 Story Points
**優先級**: 🟡 HIGH

---

## 問題背景

根據 Phase 1-5 架構審計和 PRD 符合度分析，發現以下需要驗證的差異化功能：

### 差異化功能 1: 跨系統智能關聯 (PRD F3)

```
原始需求 (PRD):
  「跨系統智能關聯」- Parallel query 3 systems + AI analysis
  - 自動關聯 ServiceNow + Dynamics 365 + SharePoint 數據
  - 統一視圖展示客戶 360 度信息
  - LLM 智能分析（發現重複問題模式）

當前狀態:
  - ✅ API 路由存在: /api/v1/connectors/*, /api/v1/routing/*
  - ✅ Domain Service: domain/connectors/servicenow.py
  - ⚠️ 未見完整的跨系統關聯查詢實現
  - ⚠️ 未見 LLM 分析引擎
```

### 差異化功能 2: 主動巡檢模式 (PRD 決策 27)

```
原始需求 (Product Brief):
  - Agent 自動定時巡檢（每天 9:00）
  - 主動發現潛在問題（服務器異常、性能下降）
  - 差異化: 傳統 RPA 只能被動執行，我們提供主動預防

當前狀態:
  - ✅ n8n Cron 觸發機制存在
  - ✅ Triggers API 完整
  - ⚠️ 未見 Agent 「主動決策」的實現（只是定時調用）
  - ⚠️ 未見預測分析引擎
```

### 差異化功能 3: 前端 UI 完成度 (PRD F13)

```
原始需求 (PRD):
  - Modern Web UI - React 18 + TypeScript
  - 不能簡化（決策 20: 不可妥協功能）

當前狀態:
  - ✅ 框架搭建完成
  - ⚠️ 具體頁面完成度未知
  - ⚠️ 22 個 API 路由是否都有 UI 頁面？
```

---

## Story 清單

### S33-1: 跨系統智能關聯功能驗證 (8 pts)

**優先級**: 🟡 P2 - MEDIUM
**類型**: 驗證/增強
**影響範圍**: `backend/src/domain/connectors/`, `api/v1/routing/`

#### 任務清單

1. **審計現有 Connector 實現**
   ```bash
   # 檢查現有連接器
   ls backend/src/domain/connectors/
   # 預期: servicenow.py, dynamics.py, sharepoint.py
   ```

2. **驗證並行查詢能力**
   ```python
   # 檢查是否支持並行查詢
   async def query_all_systems(customer_id: str) -> Dict:
       results = await asyncio.gather(
           servicenow_connector.query(customer_id),
           dynamics_connector.query(customer_id),
           sharepoint_connector.query(customer_id),
       )
       return aggregate_results(results)
   ```

3. **驗證 LLM 分析引擎**
   - 檢查是否有模式識別功能
   - 檢查是否有智能關聯分析

4. **創建演示場景**
   ```yaml
   場景: 客戶 360 度視圖
   輸入: customer_id = "CUST-001"
   預期輸出:
     - ServiceNow: 最近 10 個工單
     - Dynamics: 客戶資料 + 購買歷史
     - SharePoint: 相關文檔列表
     - AI 分析: 發現的模式和建議
   ```

5. **記錄功能差距**
   - 如果功能不完整，記錄缺失項
   - 評估補充實現的工作量

#### 驗收標準
- [ ] 跨系統查詢功能驗證完成
- [ ] LLM 分析功能驗證完成
- [ ] 演示場景可運行
- [ ] 功能差距文檔完成

---

### S33-2: 主動巡檢模式評估 (6 pts)

**優先級**: 🟡 P2 - MEDIUM
**類型**: 評估/增強
**影響範圍**: `backend/src/domain/triggers/`, `api/v1/triggers/`

#### 任務清單

1. **區分「被動」vs「主動」巡檢**
   ```
   被動巡檢 (目前實現):
   - Cron 觸發 → 執行固定腳本 → 報告結果
   - 無智能決策

   主動巡檢 (PRD 期望):
   - 分析歷史數據 → 預測異常 → 主動告警
   - Agent 自主決策何時和如何巡檢
   ```

2. **評估現有觸發機制**
   ```python
   # 檢查 triggers 實現
   # backend/src/domain/triggers/webhook.py
   # backend/src/domain/triggers/scheduler.py

   # 是否支持:
   # - 動態調整觸發頻率？
   # - 基於條件的觸發？
   # - 預測性觸發？
   ```

3. **評估需求真實性**
   - 與 stakeholder 確認「主動決策」需求
   - 確認 MVP 是否需要預測分析

4. **制定增強方案 (如需要)**
   ```python
   # 如果需要增強，可考慮:
   class ProactiveInspectionAgent:
       async def analyze_patterns(self, history: List[Event]) -> Prediction:
           """分析歷史事件，預測潛在問題"""
           pass

       async def decide_inspection_timing(self) -> datetime:
           """智能決定巡檢時間"""
           pass

       async def generate_recommendations(self) -> List[Recommendation]:
           """生成主動建議"""
           pass
   ```

#### 驗收標準
- [ ] 現有觸發機制評估完成
- [ ] 「主動」vs「被動」差距分析完成
- [ ] 需求確認文檔完成
- [ ] 增強方案 (如需要) 制定完成

---

### S33-3: 前端 UI 完成度審計 (5 pts)

**優先級**: 🟡 P2 - MEDIUM
**類型**: 審計
**影響範圍**: `frontend/src/pages/`

#### 任務清單

1. **統計前端頁面覆蓋**
   ```bash
   ls frontend/src/pages/
   # 預期頁面:
   # - Dashboard.tsx
   # - Workflows.tsx
   # - Agents.tsx
   # - Executions.tsx
   # - Templates.tsx
   # - Analytics.tsx
   # - Settings.tsx
   ```

2. **對比 API 路由覆蓋**
   ```
   22 個 API 模組 vs 前端頁面:

   核心功能 (必須有 UI):
   - agents/ → Agents.tsx ✅/❌
   - workflows/ → Workflows.tsx ✅/❌
   - executions/ → Executions.tsx ✅/❌
   - templates/ → Templates.tsx ✅/❌
   - dashboard/ → Dashboard.tsx ✅/❌

   管理功能 (需要 UI):
   - groupchat/ → GroupChat.tsx ✅/❌
   - handoff/ → Handoff.tsx ✅/❌
   - planning/ → Planning.tsx ✅/❌

   設定功能 (需要 UI):
   - connectors/ → Settings/Connectors.tsx ✅/❌
   - triggers/ → Settings/Triggers.tsx ✅/❌
   - notifications/ → Settings/Notifications.tsx ✅/❌
   ```

3. **評估頁面完成度**
   - 每個頁面的功能完成度
   - 關鍵互動是否實現

4. **制定 UI 補充計劃 (如需要)**
   - 列出缺失頁面
   - 估算開發工作量

#### 驗收標準
- [ ] 前端頁面清單完成
- [ ] API 覆蓋對比完成
- [ ] 完成度評估報告完成
- [ ] UI 補充計劃 (如需要) 完成

---

### S33-4: UAT 準備和文檔更新 (3 pts)

**優先級**: 🟡 P2 - MEDIUM
**類型**: 文檔
**影響範圍**: `docs/`

#### 任務清單

1. **更新架構文檔**
   ```
   更新文件:
   - docs/02-architecture/technical-architecture.md
   - CLAUDE.md
   - docs/bmm-workflow-status.yaml
   ```

2. **創建 UAT 測試計劃**
   ```markdown
   # UAT 測試計劃

   ## 測試場景

   ### 場景 1: 基本工作流執行
   - 創建簡單順序工作流
   - 執行並驗證結果

   ### 場景 2: Human-in-the-Loop
   - 創建需要審批的工作流
   - 驗證審批流程

   ### 場景 3: 跨系統查詢
   - 查詢客戶 360 度視圖
   - 驗證數據整合

   ### 場景 4: 前端操作
   - 驗證所有 UI 頁面
   - 驗證關鍵操作流程
   ```

3. **創建部署檢查清單**
   ```markdown
   # 生產部署檢查清單

   ## 環境準備
   - [ ] Azure 資源配置
   - [ ] 數據庫遷移
   - [ ] Redis 配置
   - [ ] 環境變量設置

   ## 安全檢查
   - [ ] API 認證配置
   - [ ] 敏感數據加密
   - [ ] 日誌脫敏

   ## 監控配置
   - [ ] 健康檢查端點
   - [ ] 日誌收集
   - [ ] 告警設置
   ```

4. **更新 Phase 6 完成狀態**
   - 更新 bmm-workflow-status.yaml
   - 記錄 Phase 6 完成

#### 驗收標準
- [ ] 架構文檔更新完成
- [ ] UAT 測試計劃完成
- [ ] 部署檢查清單完成
- [ ] Phase 6 狀態更新

---

## 輸出文檔

### 差異化功能驗證報告

```markdown
# 差異化功能驗證報告

## 1. 跨系統智能關聯
- 狀態: [完整/部分/未實現]
- 已實現功能: [列表]
- 缺失功能: [列表]
- 建議: [下一步行動]

## 2. 主動巡檢模式
- 狀態: [完整/部分/未實現]
- 已實現功能: [列表]
- 缺失功能: [列表]
- 建議: [下一步行動]

## 3. 前端 UI 覆蓋
- 覆蓋率: X/22 API 模組
- 已完成頁面: [列表]
- 缺失頁面: [列表]
- 建議: [下一步行動]

## 4. 結論
- UAT 就緒度: [就緒/需補充]
- 建議行動: [列表]
```

---

## 風險與緩解

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| 差異化功能不完整 | 中 | 中 | 與 stakeholder 確認優先級 |
| 前端缺失關鍵頁面 | 中 | 高 | 快速原型開發 |
| UAT 準備不足 | 低 | 中 | 提前準備測試數據 |

---

## 驗證命令

```bash
# 檢查前端頁面
ls frontend/src/pages/

# 驗證 Connector 實現
ls backend/src/domain/connectors/

# 運行完整測試套件
pytest tests/ -v --tb=short

# 生成覆蓋報告
pytest tests/ --cov=backend/src --cov-report=html
```

---

## 完成定義

- [ ] 所有 S33 Story 完成
- [ ] 差異化功能驗證報告完成
- [ ] 前端 UI 審計完成
- [ ] UAT 測試計劃完成
- [ ] 部署檢查清單完成
- [ ] Phase 6 完成狀態更新

---

## Phase 6 完成後預期狀態

```
架構符合度:        89% → 95%+
官方 API 集中度:   77.8% → 90%+
Domain 遷移進度:   50.7% → 95%+
前端 UI 覆蓋:      未知 → 已審計
差異化功能:        未驗證 → 已驗證
UAT 準備:          未準備 → 就緒
```
