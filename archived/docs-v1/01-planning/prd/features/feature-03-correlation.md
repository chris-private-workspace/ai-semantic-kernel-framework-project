# F3. 跨系統關聯

**分類**: 整合與智能  
**優先級**: P0 (必須擁有 - 核心差異化功能)  
**開發時間**: 2 週  
**複雜度**: ⭐⭐⭐⭐ (高)  
**依賴項**: ServiceNow API, Dynamics 365 API, SharePoint API, Azure OpenAI, Redis

---

## 3.1 功能概述

**跨系統關聯**功能允許 Agent 同時查詢 **3 個外部系統** (ServiceNow, Dynamics 365, SharePoint)，並在 **<5 秒**內返回統一的「客戶 360 度視圖」。此功能利用 **並行查詢**、**Redis 緩存** 和 **LLM 驅動的關聯** 來發現跨系統數據中的隱藏模式和見解。

### 什麼是跨系統關聯?

跨系統關聯是從多個數據孤島 (ServiceNow 支援工單、Dynamics 365 銷售機會、SharePoint 文檔) 收集客戶數據，並使用 AI 來識別關係、異常和趨勢的過程。此功能消除了重複搜索的需要，並為 Agent 提供全面的上下文。

### 業務價值

- **節省時間**: 將數據收集從 10-15 分鐘減少到 <5 秒 (95% 時間節省)
- **完整上下文**: Agent 查看所有相關數據，而不僅僅是一個系統
- **AI 驅動的見解**: LLM 發現人類可能錯過的模式 (例如: "客戶有 3 個未解決的 P1 工單，但銷售團隊正在推動追加銷售")
- **優雅降級**: 即使一個或兩個系統宕機，仍返回部分結果

### 現實世界示例

```
情境: 客服 Agent 處理 VIP 客戶 "Acme Corp" 的投訴。

❌ 不使用跨系統關聯:
1. 在 ServiceNow 中搜索工單 (2 分鐘)
2. 切換到 Dynamics 365 查找銷售機會 (2 分鐘)
3. 在 SharePoint 中搜索文檔 (2 分鐘)
4. 手動關聯數據和發現見解 (5 分鐘)
總時間: 10-15 分鐘

✅ 使用跨系統關聯:
1. Agent 輸入: "Show me customer 360 view for Acme Corp"
2. 系統並行查詢所有 3 個系統 (3 秒)
3. AI 生成見解和關聯 (1 秒)
4. 顯示統一的儀表板，包含優先見解
總時間: <5 秒
```

---

## 3.2 用戶故事

### US-F3-001: 在 <5 秒內查詢客戶 360 度視圖

**作為** 客服 Agent  
**我想要** 在 <5 秒內看到客戶的完整視圖 (ServiceNow 工單 + Dynamics 365 銷售機會 + SharePoint 文檔)  
**以便** 我可以快速解決問題，而無需在多個系統之間切換

**優先級**: P0 (必須擁有)  
**開發時間**: 6 天  
**複雜度**: ⭐⭐⭐⭐ (高)

#### 驗收標準

1. **並行查詢所有 3 個系統**:
   ```python
   # 使用 asyncio.gather() 並行執行
   results = await asyncio.gather(
       query_servicenow(customer_id),
       query_dynamics365(customer_id),
       query_sharepoint(customer_id)
   )
   ```
   - 最大等待時間: 5 秒
   - 如果一個系統超時，返回其他兩個系統的結果 (優雅降級)

2. **返回統一的 JSON 響應**:
   ```json
   {
     "customer_id": "CUST-12345",
     "customer_name": "Acme Corp",
     "systems": {
       "servicenow": {
         "status": "success",
         "data": {
           "open_tickets": [
             {
               "ticket_id": "INC0012345",
               "priority": "P1",
               "subject": "Database Connection Issues",
               "created_at": "2024-01-15T10:30:00Z",
               "last_updated": "2024-01-16T14:20:00Z"
             }
           ],
           "closed_tickets_last_30_days": 5,
           "total_tickets_all_time": 23
         },
         "query_time_ms": 1200
       },
       "dynamics365": {
         "status": "success",
         "data": {
           "active_opportunities": [
             {
               "opportunity_id": "OPP-98765",
               "name": "Enterprise License Renewal",
               "value": "$250,000",
               "stage": "Proposal",
               "close_date": "2024-02-28"
             }
           ],
           "total_revenue_ytd": "$1.2M",
           "account_health": "At Risk"
         },
         "query_time_ms": 800
       },
       "sharepoint": {
         "status": "success",
         "data": {
           "recent_documents": [
             {
               "document_id": "DOC-456",
               "title": "Service Agreement 2024",
               "modified_date": "2024-01-10T09:15:00Z",
               "url": "https://acme.sharepoint.com/contracts/sa2024.pdf"
             }
           ],
           "total_documents": 47
         },
         "query_time_ms": 600
       }
     },
     "total_query_time_ms": 1200,
     "cache_hit": false
   }
   ```

3. **性能目標**:
   - P95 延遲 < 5 秒 (緩存未命中)
   - P95 延遲 < 200 毫秒 (緩存命中)
   - 緩存命中率 ≥ 60% (在穩態下)

4. **API 端點**:
   ```python
   @app.post("/api/correlation/customer-360")
   async def get_customer_360(request: Customer360Request):
       """
       並行查詢所有系統並返回統一視圖。
       
       Args:
           customer_id: 客戶 ID
           force_refresh: 如果為 True，繞過緩存
       
       Returns:
           Customer360Response 包含來自所有系統的數據
       """
       pass
   ```

5. **UI 顯示**:
   ```
   ┌─────────────────────────────────────────────────────────────────┐
   │  客戶 360 度視圖: Acme Corp (CUST-12345)                         │
   ├─────────────────────────────────────────────────────────────────┤
   │                                                                 │
   │  📊 ServiceNow                        查詢時間: 1.2 秒          │
   │  ├─ 未解決工單: 1                                               │
   │  │  └─ INC0012345 [P1] Database Connection Issues               │
   │  └─ 過去 30 天已解決: 5 個工單                                  │
   │                                                                 │
   │  💼 Dynamics 365                      查詢時間: 0.8 秒          │
   │  ├─ 活躍銷售機會: 1                                             │
   │  │  └─ OPP-98765 Enterprise License Renewal ($250K)             │
   │  └─ 賬戶健康: ⚠️ 有風險                                         │
   │                                                                 │
   │  📄 SharePoint                        查詢時間: 0.6 秒          │
   │  └─ 最近文檔: Service Agreement 2024 (修改於 2024-01-10)       │
   │                                                                 │
   │  ⏱️ 總查詢時間: 1.2 秒                                          │
   │  🔄 緩存狀態: 未命中                                            │
   │                                                                 │
   │  [🔄 刷新]  [💾 保存視圖]                                       │
   └─────────────────────────────────────────────────────────────────┘
   ```

6. **錯誤處理**:
   - 如果所有 3 個系統都失敗: 返回 503 錯誤
   - 如果 1-2 個系統失敗: 返回部分結果 + 警告
   - 超時: 每個系統 5 秒超時後繼續

7. **緩存策略**:
   - 使用 Redis 緩存客戶 360 度響應 (TTL: 1 天)
   - 緩存鍵: `customer_360:{customer_id}`
   - 如果請求中 `force_refresh=true`，繞過緩存

#### 完成定義 (Definition of Done)

- [ ] 實現 `CrossSystemCorrelationAgent` 類
- [ ] 為所有 3 個系統創建適配器 (ServiceNowAdapter, Dynamics365Adapter, SharePointAdapter)
- [ ] 實現 Redis 緩存，TTL 為 1 天
- [ ] 為並行查詢編寫單元測試
- [ ] 為部分失敗場景編寫集成測試
- [ ] 使用 50 個並發請求進行負載測試
- [ ] 在 Postman 中記錄 API

---

### US-F3-002: AI 驅動的關聯和見解

**作為** 客服經理  
**我想要** 查看跨系統數據的 AI 生成的見解 (例如: "客戶有 3 個未解決的 P1 工單，但銷售正在推動續約")  
**以便** 我可以做出數據驅動的決策並發現隱藏的風險

**優先級**: P0 (必須擁有)  
**開發時間**: 4 天  
**複雜度**: ⭐⭐⭐⭐ (高)

#### 驗收標準

1. **在查詢後調用 LLM**:
   ```python
   async def _generate_insights(self, customer_data: dict) -> List[str]:
       """
       使用 GPT-4o 分析跨系統數據並生成見解。
       
       Returns:
           見解列表 (例如: ["High churn risk: 3 P1 tickets + contract expiring"])
       """
       prompt = f"""
       分析以下客戶數據並識別關鍵見解、風險和機會:

       客戶: {customer_data['customer_name']}

       ServiceNow 數據:
       - 未解決工單: {customer_data['systems']['servicenow']['data']['open_tickets']}
       - 過去 30 天已解決工單: {customer_data['systems']['servicenow']['data']['closed_tickets_last_30_days']}

       Dynamics 365 數據:
       - 活躍銷售機會: {customer_data['systems']['dynamics365']['data']['active_opportunities']}
       - 賬戶健康: {customer_data['systems']['dynamics365']['data']['account_health']}

       SharePoint 數據:
       - 最近文檔: {customer_data['systems']['sharepoint']['data']['recent_documents']}

       提供 3-5 個可操作的見解，重點關注:
       1. 流失風險指標
       2. 追加銷售機會
       3. 異常模式
       4. 跨系統關聯

       以簡潔、項目符號格式返回見解。
       """

       response = await openai.ChatCompletion.acreate(
           model="gpt-4o",
           messages=[{"role": "user", "content": prompt}],
           max_tokens=500,
           temperature=0.3
       )
       return response['choices'][0]['message']['content'].split('\n')
   ```

2. **見解類型**:
   - **模式**: "客戶在過去 30 天內平均每週創建 2 個工單"
   - **異常**: "異常: 支援工單激增 300% (上週 6 個 vs 通常 2 個)"
   - **關聯**: "流失風險: 3 個未解決的 P1 工單 + 合同在 2 個月後到期"
   - **時間線**: "客戶自 2024 年 1 月起活動減少 40%"
   - **建議**: "建議: 在續約談判前安排執行業務審查"

3. **見解 JSON 格式**:
   ```json
   {
     "insights": [
       {
         "type": "risk",
         "severity": "high",
         "title": "High Churn Risk",
         "description": "Customer has 3 open P1 tickets + contract expiring in 2 months",
         "confidence": 0.85
       },
       {
         "type": "opportunity",
         "severity": "medium",
         "title": "Upsell Opportunity",
         "description": "Customer viewing Enterprise features but on Standard plan",
         "confidence": 0.70
       }
     ]
   }
   ```

4. **UI 顯示**:
   ```
   ┌─────────────────────────────────────────────────────────────────┐
   │  🤖 AI 見解 (由 GPT-4o 提供支持)                                │
   ├─────────────────────────────────────────────────────────────────┤
   │                                                                 │
   │  🚨 高流失風險 (置信度: 85%)                                    │
   │  └─ 客戶有 3 個未解決的 P1 工單 + 合同在 2 個月後到期           │
   │                                                                 │
   │  💡 追加銷售機會 (置信度: 70%)                                  │
   │  └─ 客戶正在查看企業版功能，但使用的是標準版計劃               │
   │                                                                 │
   │  📊 異常模式 (置信度: 90%)                                      │
   │  └─ 支援工單激增 300% (上週 6 個 vs 通常 2 個)                 │
   │                                                                 │
   │  [📥 導出見解]  [📧 發送給團隊]                                │
   └─────────────────────────────────────────────────────────────────┘
   ```

5. **性能目標**:
   - LLM 推理時間: < 2 秒
   - 總端到端時間 (查詢 + 見解): < 7 秒

6. **成本控制**:
   - 使用 GPT-4o (更便宜，更快)
   - 限制輸出為 500 個 token
   - 緩存見解 1 天

#### 完成定義 (Definition of Done)

- [ ] 實現 `_generate_insights()` 方法
- [ ] 創建 LLM 提示模板，包含結構化輸出
- [ ] 為見解生成編寫單元測試
- [ ] 驗證見解質量 (手動審查 10 個真實客戶)
- [ ] 為 LLM 成本 + 延遲設置監控

---

### US-F3-003: 部分結果的優雅降級

**作為** 客服 Agent  
**我想要** 即使一個或兩個系統宕機也能看到部分結果  
**以便** 我仍然可以幫助客戶，而不會被完全阻止

**優先級**: P0 (必須擁有)  
**開發時間**: 2 天  
**複雜度**: ⭐⭐⭐ (中)

#### 驗收標準

1. **部分失敗響應**:
   ```json
   {
     "customer_id": "CUST-12345",
     "systems": {
       "servicenow": {
         "status": "success",
         "data": { /* ... */ }
       },
       "dynamics365": {
         "status": "error",
         "error": "Connection timeout after 5 seconds",
         "query_time_ms": 5000
       },
       "sharepoint": {
         "status": "success",
         "data": { /* ... */ }
       }
     },
     "warnings": [
       "Dynamics 365 query failed. Showing partial results from 2/3 systems."
     ]
   }
   ```

2. **錯誤處理矩陣**:

   | 成功系統 | 行為 | HTTP 狀態碼 |
   |---|---|---|
   | 3/3 | 返回完整結果 | 200 OK |
   | 2/3 | 返回部分結果 + 警告 | 200 OK |
   | 1/3 | 返回部分結果 + 警告 | 200 OK |
   | 0/3 | 返回錯誤 | 503 Service Unavailable |

3. **UI 顯示 (部分失敗)**:
   ```
   ┌─────────────────────────────────────────────────────────────────┐
   │  ⚠️ 部分結果 (2/3 系統可用)                                     │
   ├─────────────────────────────────────────────────────────────────┤
   │                                                                 │
   │  📊 ServiceNow                        ✅ 成功                   │
   │  └─ 未解決工單: 1                                               │
   │                                                                 │
   │  💼 Dynamics 365                      ❌ 不可用                 │
   │  └─ 錯誤: 5 秒後連接超時                                        │
   │                                                                 │
   │  📄 SharePoint                        ✅ 成功                   │
   │  └─ 最近文檔: Service Agreement 2024                            │
   │                                                                 │
   │  [🔄 重試 Dynamics 365]  [📧 通知 IT]                          │
   └─────────────────────────────────────────────────────────────────┘
   ```

4. **重試邏輯**:
   - 如果系統失敗，在 UI 中顯示「重試」按鈕
   - 允許用戶僅重新查詢失敗的系統

5. **日誌記錄和警報**:
   - 記錄所有部分失敗到 Application Insights
   - 如果任何系統的失敗率 > 10%，觸發警報

#### 完成定義 (Definition of Done)

- [ ] 實現 try-catch 包裝器用於每個系統查詢
- [ ] 為所有部分失敗場景編寫測試
- [ ] 驗證 UI 正確顯示警告
- [ ] 設置失敗率監控和警報

---

### US-F3-004: 使用 Redis 的智能緩存

**作為** 平台工程師  
**我想要** 緩存客戶 360 度響應以減少外部 API 調用  
**以便** 我可以降低成本並提高響應時間

**優先級**: P1 (應該擁有)  
**開發時間**: 2 天  
**複雜度**: ⭐⭐⭐ (中)

#### 驗收標準

1. **Redis 緩存實現**:
   ```python
   class CrossSystemCorrelationAgent:
       def __init__(self):
           self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
           self.cache_ttl = 86400  # 1 天

       async def get_customer_360_view(self, customer_id: str, force_refresh: bool = False):
           cache_key = f"customer_360:{customer_id}"

           # 檢查緩存 (除非 force_refresh=True)
           if not force_refresh:
               cached_data = self.redis.get(cache_key)
               if cached_data:
                   return json.loads(cached_data)

           # 緩存未命中: 查詢所有系統
           data = await self._query_all_systems(customer_id)

           # 保存到緩存
           self.redis.setex(cache_key, self.cache_ttl, json.dumps(data))

           return data
   ```

2. **緩存統計端點**:
   ```python
   @app.get("/api/correlation/cache/stats")
   async def get_cache_stats():
       """
       返回緩存命中率和大小。
       """
       total_requests = redis.get("cache:total_requests") or 0
       cache_hits = redis.get("cache:hits") or 0
       hit_rate = cache_hits / total_requests if total_requests > 0 else 0

       return {
           "total_requests": total_requests,
           "cache_hits": cache_hits,
           "cache_misses": total_requests - cache_hits,
           "hit_rate": hit_rate,
           "cache_size_mb": redis.info("memory")["used_memory"] / 1024 / 1024
       }
   ```

3. **緩存失效**:
   ```python
   @app.delete("/api/correlation/cache/{customer_id}")
   async def invalidate_cache(customer_id: str):
       """
       手動使特定客戶的緩存失效。
       """
       cache_key = f"customer_360:{customer_id}"
       redis.delete(cache_key)
       return {"message": f"Cache invalidated for {customer_id}"}
   ```

4. **緩存監控儀表板**:
   ```
   ┌─────────────────────────────────────────────────────────────────┐
   │  📊 緩存統計                                                     │
   ├─────────────────────────────────────────────────────────────────┤
   │                                                                 │
   │  總請求數: 1,234                                                │
   │  緩存命中數: 789                                                │
   │  緩存未命中數: 445                                              │
   │  命中率: 64%                                                    │
   │  緩存大小: 12.5 MB                                              │
   │                                                                 │
   │  🎯 目標命中率: ≥60%                                            │
   │  ✅ 狀態: 達到目標                                              │
   │                                                                 │
   │  [🗑️ 清除所有緩存]  [📊 查看詳細指標]                          │
   └─────────────────────────────────────────────────────────────────┘
   ```

5. **性能目標**:
   - 緩存命中響應時間: < 200 毫秒
   - 緩存命中率: ≥ 60% (穩態)

#### 完成定義 (Definition of Done)

- [ ] 實現 Redis 緩存，TTL 為 1 天
- [ ] 創建緩存統計端點
- [ ] 實現緩存失效端點
- [ ] 為緩存邏輯編寫單元測試
- [ ] 設置緩存命中率監控

---

## 3.3 技術實現

### CrossSystemCorrelationAgent 類

```python
import asyncio
import json
import redis
from typing import Dict, List, Optional
from dataclasses import dataclass
import openai

@dataclass
class SystemQueryResult:
    """單個系統查詢的結果。"""
    system_name: str
    status: str  # "success" 或 "error"
    data: Optional[Dict] = None
    error: Optional[str] = None
    query_time_ms: int = 0

class CrossSystemCorrelationAgent:
    """
    跨多個外部系統查詢數據並生成 AI 見解的 Agent。
    
    功能:
    - 並行查詢 ServiceNow, Dynamics 365, SharePoint
    - 使用 Redis 緩存結果以提高性能
    - 使用 GPT-4o 生成跨系統見解
    - 一個或多個系統失敗時的優雅降級
    """

    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.cache_ttl = 86400  # 1 天
        self.system_timeout = 5  # 每個系統 5 秒超時

        # 外部系統適配器
        self.servicenow_adapter = ServiceNowAdapter()
        self.dynamics365_adapter = Dynamics365Adapter()
        self.sharepoint_adapter = SharePointAdapter()

    async def get_customer_360_view(
        self,
        customer_id: str,
        force_refresh: bool = False
    ) -> Dict:
        """
        獲取客戶的 360 度視圖，包含來自所有系統的數據。

        Args:
            customer_id: 客戶 ID
            force_refresh: 如果為 True，繞過緩存

        Returns:
            包含來自所有系統的數據 + AI 見解的字典
        """
        cache_key = f"customer_360:{customer_id}"

        # 檢查緩存 (除非 force_refresh=True)
        if not force_refresh:
            cached_data = self.redis.get(cache_key)
            if cached_data:
                self._increment_cache_hit()
                return json.loads(cached_data)

        self._increment_cache_miss()

        # 緩存未命中: 並行查詢所有系統
        system_results = await self._query_all_systems(customer_id)

        # 檢查是否所有系統都失敗
        successful_systems = [r for r in system_results if r.status == "success"]
        if len(successful_systems) == 0:
            raise Exception("All systems failed. Cannot return customer 360 view.")

        # 生成 AI 見解
        insights = await self._generate_insights(customer_id, system_results)

        # 構建響應
        response = {
            "customer_id": customer_id,
            "customer_name": self._get_customer_name(system_results),
            "systems": {r.system_name: self._format_system_result(r) for r in system_results},
            "insights": insights,
            "total_query_time_ms": max([r.query_time_ms for r in system_results]),
            "cache_hit": False,
            "warnings": self._generate_warnings(system_results)
        }

        # 保存到緩存 (僅當至少 2 個系統成功時)
        if len(successful_systems) >= 2:
            self.redis.setex(cache_key, self.cache_ttl, json.dumps(response))

        return response

    async def _query_all_systems(self, customer_id: str) -> List[SystemQueryResult]:
        """
        並行查詢所有外部系統。

        Returns:
            SystemQueryResult 對象列表
        """
        tasks = [
            self._query_servicenow(customer_id),
            self._query_dynamics365(customer_id),
            self._query_sharepoint(customer_id)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 將異常轉換為 SystemQueryResult 對象
        return [
            r if isinstance(r, SystemQueryResult) else SystemQueryResult(
                system_name="unknown",
                status="error",
                error=str(r)
            )
            for r in results
        ]

    async def _query_servicenow(self, customer_id: str) -> SystemQueryResult:
        """查詢 ServiceNow 以獲取支援工單。"""
        start_time = asyncio.get_event_loop().time()
        try:
            async with asyncio.timeout(self.system_timeout):
                data = await self.servicenow_adapter.get_tickets(customer_id)
                query_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
                return SystemQueryResult(
                    system_name="servicenow",
                    status="success",
                    data=data,
                    query_time_ms=query_time_ms
                )
        except asyncio.TimeoutError:
            return SystemQueryResult(
                system_name="servicenow",
                status="error",
                error="Connection timeout after 5 seconds",
                query_time_ms=5000
            )
        except Exception as e:
            return SystemQueryResult(
                system_name="servicenow",
                status="error",
                error=str(e),
                query_time_ms=int((asyncio.get_event_loop().time() - start_time) * 1000)
            )

    async def _query_dynamics365(self, customer_id: str) -> SystemQueryResult:
        """查詢 Dynamics 365 以獲取銷售機會。"""
        start_time = asyncio.get_event_loop().time()
        try:
            async with asyncio.timeout(self.system_timeout):
                data = await self.dynamics365_adapter.get_opportunities(customer_id)
                query_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
                return SystemQueryResult(
                    system_name="dynamics365",
                    status="success",
                    data=data,
                    query_time_ms=query_time_ms
                )
        except asyncio.TimeoutError:
            return SystemQueryResult(
                system_name="dynamics365",
                status="error",
                error="Connection timeout after 5 seconds",
                query_time_ms=5000
            )
        except Exception as e:
            return SystemQueryResult(
                system_name="dynamics365",
                status="error",
                error=str(e),
                query_time_ms=int((asyncio.get_event_loop().time() - start_time) * 1000)
            )

    async def _query_sharepoint(self, customer_id: str) -> SystemQueryResult:
        """查詢 SharePoint 以獲取文檔。"""
        start_time = asyncio.get_event_loop().time()
        try:
            async with asyncio.timeout(self.system_timeout):
                data = await self.sharepoint_adapter.get_documents(customer_id)
                query_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
                return SystemQueryResult(
                    system_name="sharepoint",
                    status="success",
                    data=data,
                    query_time_ms=query_time_ms
                )
        except asyncio.TimeoutError:
            return SystemQueryResult(
                system_name="sharepoint",
                status="error",
                error="Connection timeout after 5 seconds",
                query_time_ms=5000
            )
        except Exception as e:
            return SystemQueryResult(
                system_name="sharepoint",
                status="error",
                error=str(e),
                query_time_ms=int((asyncio.get_event_loop().time() - start_time) * 1000)
            )

    async def _generate_insights(
        self,
        customer_id: str,
        system_results: List[SystemQueryResult]
    ) -> List[Dict]:
        """
        使用 GPT-4o 分析跨系統數據並生成見解。

        Returns:
            見解字典列表
        """
        # 僅使用成功的系統結果
        successful_results = [r for r in system_results if r.status == "success"]
        if len(successful_results) == 0:
            return []

        # 構建提示
        prompt = self._build_insights_prompt(customer_id, successful_results)

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )

            insights_text = response['choices'][0]['message']['content']
            return self._parse_insights(insights_text)

        except Exception as e:
            # 如果 LLM 失敗，返回空列表
            print(f"Failed to generate insights: {e}")
            return []

    def _build_insights_prompt(
        self,
        customer_id: str,
        system_results: List[SystemQueryResult]
    ) -> str:
        """構建 LLM 的提示以生成見解。"""
        prompt_parts = [
            f"分析以下客戶數據並識別關鍵見解、風險和機會:\n",
            f"客戶 ID: {customer_id}\n"
        ]

        for result in system_results:
            prompt_parts.append(f"\n{result.system_name.upper()} 數據:")
            prompt_parts.append(json.dumps(result.data, indent=2))

        prompt_parts.append("""
        提供 3-5 個可操作的見解，重點關注:
        1. 流失風險指標
        2. 追加銷售機會
        3. 異常模式
        4. 跨系統關聯

        以以下 JSON 格式返回見解:
        [
          {
            "type": "risk|opportunity|anomaly",
            "severity": "high|medium|low",
            "title": "簡短標題",
            "description": "詳細描述",
            "confidence": 0.0-1.0
          }
        ]
        """)

        return "".join(prompt_parts)

    def _parse_insights(self, insights_text: str) -> List[Dict]:
        """解析 LLM 響應為結構化見解。"""
        try:
            # 嘗試將響應解析為 JSON
            return json.loads(insights_text)
        except json.JSONDecodeError:
            # 如果失敗，返回純文本見解
            return [
                {
                    "type": "info",
                    "severity": "medium",
                    "title": "General Insights",
                    "description": insights_text,
                    "confidence": 0.5
                }
            ]

    def _format_system_result(self, result: SystemQueryResult) -> Dict:
        """將 SystemQueryResult 格式化為 API 響應格式。"""
        if result.status == "success":
            return {
                "status": "success",
                "data": result.data,
                "query_time_ms": result.query_time_ms
            }
        else:
            return {
                "status": "error",
                "error": result.error,
                "query_time_ms": result.query_time_ms
            }

    def _generate_warnings(self, system_results: List[SystemQueryResult]) -> List[str]:
        """如果任何系統失敗，生成警告消息。"""
        failed_systems = [r for r in system_results if r.status == "error"]
        if len(failed_systems) == 0:
            return []

        failed_names = [r.system_name for r in failed_systems]
        return [
            f"{', '.join(failed_names)} query failed. Showing partial results from {len(system_results) - len(failed_systems)}/{len(system_results)} systems."
        ]

    def _get_customer_name(self, system_results: List[SystemQueryResult]) -> str:
        """從任何成功的系統結果中提取客戶名稱。"""
        for result in system_results:
            if result.status == "success" and result.data:
                # 嘗試從數據中提取名稱
                if "customer_name" in result.data:
                    return result.data["customer_name"]
        return "Unknown Customer"

    def _increment_cache_hit(self):
        """增加緩存命中計數器。"""
        self.redis.incr("cache:total_requests")
        self.redis.incr("cache:hits")

    def _increment_cache_miss(self):
        """增加緩存未命中計數器。"""
        self.redis.incr("cache:total_requests")

    async def invalidate_cache(self, customer_id: str):
        """手動使特定客戶的緩存失效。"""
        cache_key = f"customer_360:{customer_id}"
        self.redis.delete(cache_key)

    def get_cache_stats(self) -> Dict:
        """獲取緩存統計信息。"""
        total_requests = int(self.redis.get("cache:total_requests") or 0)
        cache_hits = int(self.redis.get("cache:hits") or 0)
        hit_rate = cache_hits / total_requests if total_requests > 0 else 0

        return {
            "total_requests": total_requests,
            "cache_hits": cache_hits,
            "cache_misses": total_requests - cache_hits,
            "hit_rate": hit_rate,
            "cache_size_mb": self.redis.info("memory")["used_memory"] / 1024 / 1024
        }
```

---

## 3.4 API 端點

### 1. 獲取客戶 360 度視圖

```python
@app.post("/api/correlation/customer-360")
async def get_customer_360(request: Customer360Request):
    """
    並行查詢所有系統並返回統一的客戶視圖。

    Args:
        customer_id: 客戶 ID
        force_refresh: 如果為 True，繞過緩存

    Returns:
        Customer360Response 包含來自所有系統的數據 + AI 見解
    """
    agent = CrossSystemCorrelationAgent()
    try:
        response = await agent.get_customer_360_view(
            customer_id=request.customer_id,
            force_refresh=request.force_refresh
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
```

**請求體**:
```json
{
  "customer_id": "CUST-12345",
  "force_refresh": false
}
```

**響應**:
```json
{
  "customer_id": "CUST-12345",
  "customer_name": "Acme Corp",
  "systems": {
    "servicenow": { /* ... */ },
    "dynamics365": { /* ... */ },
    "sharepoint": { /* ... */ }
  },
  "insights": [
    {
      "type": "risk",
      "severity": "high",
      "title": "High Churn Risk",
      "description": "Customer has 3 open P1 tickets + contract expiring in 2 months",
      "confidence": 0.85
    }
  ],
  "total_query_time_ms": 1200,
  "cache_hit": false,
  "warnings": []
}
```

---

### 2. 使緩存失效

```python
@app.delete("/api/correlation/cache/{customer_id}")
async def invalidate_cache(customer_id: str):
    """
    手動使特定客戶的緩存失效。
    """
    agent = CrossSystemCorrelationAgent()
    await agent.invalidate_cache(customer_id)
    return {"message": f"Cache invalidated for {customer_id}"}
```

---

### 3. 獲取緩存統計信息

```python
@app.get("/api/correlation/cache/stats")
async def get_cache_stats():
    """
    返回緩存命中率和大小。
    """
    agent = CrossSystemCorrelationAgent()
    return agent.get_cache_stats()
```

**響應**:
```json
{
  "total_requests": 1234,
  "cache_hits": 789,
  "cache_misses": 445,
  "hit_rate": 0.64,
  "cache_size_mb": 12.5
}
```

---

## 3.5 外部系統適配器

### ServiceNowAdapter

```python
class ServiceNowAdapter:
    """
    ServiceNow REST API 的適配器。
    
    文檔: https://developer.servicenow.com/dev.do#!/reference/api/tokyo/rest
    """

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.auth = (username, password)

    async def get_tickets(self, customer_id: str) -> Dict:
        """
        獲取客戶的所有支援工單。

        Returns:
            包含未解決工單、已解決工單等的字典
        """
        async with httpx.AsyncClient() as client:
            # 查詢未解決工單
            open_tickets_response = await client.get(
                f"{self.base_url}/api/now/table/incident",
                params={
                    "sysparm_query": f"caller_id={customer_id}^active=true",
                    "sysparm_limit": 100
                },
                auth=self.auth
            )
            open_tickets = open_tickets_response.json()["result"]

            # 查詢過去 30 天已解決的工單
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            closed_tickets_response = await client.get(
                f"{self.base_url}/api/now/table/incident",
                params={
                    "sysparm_query": f"caller_id={customer_id}^active=false^closed_at>={thirty_days_ago}",
                    "sysparm_limit": 100
                },
                auth=self.auth
            )
            closed_tickets = closed_tickets_response.json()["result"]

            return {
                "open_tickets": [
                    {
                        "ticket_id": t["number"],
                        "priority": t["priority"],
                        "subject": t["short_description"],
                        "created_at": t["sys_created_on"],
                        "last_updated": t["sys_updated_on"]
                    }
                    for t in open_tickets
                ],
                "closed_tickets_last_30_days": len(closed_tickets),
                "total_tickets_all_time": len(open_tickets) + len(closed_tickets)
            }
```

---

### Dynamics365Adapter

```python
class Dynamics365Adapter:
    """
    Dynamics 365 Web API 的適配器。
    
    文檔: https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/overview
    """

    def __init__(self, base_url: str, access_token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0"
        }

    async def get_opportunities(self, customer_id: str) -> Dict:
        """
        獲取客戶的所有銷售機會。

        Returns:
            包含活躍銷售機會、收入等的字典
        """
        async with httpx.AsyncClient() as client:
            # 查詢活躍銷售機會
            opportunities_response = await client.get(
                f"{self.base_url}/api/data/v9.2/opportunities",
                params={
                    "$filter": f"_customerid_value eq {customer_id} and statecode eq 0",
                    "$select": "opportunityid,name,estimatedvalue,stepname,estimatedclosedate"
                },
                headers=self.headers
            )
            opportunities = opportunities_response.json()["value"]

            return {
                "active_opportunities": [
                    {
                        "opportunity_id": o["opportunityid"],
                        "name": o["name"],
                        "value": f"${o['estimatedvalue']:,.0f}",
                        "stage": o["stepname"],
                        "close_date": o["estimatedclosedate"]
                    }
                    for o in opportunities
                ],
                "total_revenue_ytd": "$1.2M",  # 這需要單獨的查詢
                "account_health": "At Risk"  # 這需要自定義邏輯
            }
```

---

### SharePointAdapter

```python
class SharePointAdapter:
    """
    SharePoint REST API 的適配器。
    
    文檔: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/get-to-know-the-sharepoint-rest-service
    """

    def __init__(self, site_url: str, access_token: str):
        self.site_url = site_url
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json;odata=verbose"
        }

    async def get_documents(self, customer_id: str) -> Dict:
        """
        獲取與客戶相關的所有文檔。

        Returns:
            包含最近文檔的字典
        """
        async with httpx.AsyncClient() as client:
            # 查詢文檔庫
            documents_response = await client.get(
                f"{self.site_url}/_api/web/lists/getbytitle('Documents')/items",
                params={
                    "$filter": f"Customer_ID eq '{customer_id}'",
                    "$select": "ID,Title,Modified,FileRef",
                    "$orderby": "Modified desc",
                    "$top": 10
                },
                headers=self.headers
            )
            documents = documents_response.json()["d"]["results"]

            return {
                "recent_documents": [
                    {
                        "document_id": f"DOC-{d['ID']}",
                        "title": d["Title"],
                        "modified_date": d["Modified"],
                        "url": f"{self.site_url}{d['FileRef']}"
                    }
                    for d in documents
                ],
                "total_documents": len(documents)
            }
```

---

## 3.6 非功能需求 (NFR)

| NFR | 目標 | 衡量標準 |
|---|---|---|
| **性能** | P95 延遲 < 5 秒 (緩存未命中) | Application Insights |
| **性能** | P95 延遲 < 200 毫秒 (緩存命中) | Application Insights |
| **可擴展性** | 支援 50+ 個並發查詢 | 負載測試 |
| **可靠性** | 99.9% 正常運行時間 (即使外部系統宕機) | 正常運行時間監控 |
| **緩存** | 緩存命中率 ≥ 60% | Redis 指標 |
| **成本** | LLM 成本 < $0.05/查詢 | Azure OpenAI 計費 |
| **成本** | 外部 API 成本 < $0.10/查詢 | ServiceNow/Dynamics 365 計費 |

---

## 3.7 測試策略

### 單元測試

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_query_all_systems_success():
    """測試所有 3 個系統成功返回數據。"""
    agent = CrossSystemCorrelationAgent()

    # 模擬適配器
    agent.servicenow_adapter.get_tickets = AsyncMock(return_value={"open_tickets": []})
    agent.dynamics365_adapter.get_opportunities = AsyncMock(return_value={"active_opportunities": []})
    agent.sharepoint_adapter.get_documents = AsyncMock(return_value={"recent_documents": []})

    results = await agent._query_all_systems("CUST-123")

    assert len(results) == 3
    assert all(r.status == "success" for r in results)

@pytest.mark.asyncio
async def test_query_partial_failure():
    """測試一個系統失敗時的優雅降級。"""
    agent = CrossSystemCorrelationAgent()

    # 模擬 ServiceNow 成功, Dynamics 365 失敗, SharePoint 成功
    agent.servicenow_adapter.get_tickets = AsyncMock(return_value={"open_tickets": []})
    agent.dynamics365_adapter.get_opportunities = AsyncMock(side_effect=Exception("Connection error"))
    agent.sharepoint_adapter.get_documents = AsyncMock(return_value={"recent_documents": []})

    results = await agent._query_all_systems("CUST-123")

    assert len(results) == 3
    assert results[0].status == "success"  # ServiceNow
    assert results[1].status == "error"  # Dynamics 365
    assert results[2].status == "success"  # SharePoint

@pytest.mark.asyncio
async def test_cache_hit():
    """測試緩存命中返回緩存數據。"""
    agent = CrossSystemCorrelationAgent()

    # 預填充緩存
    cached_data = {"customer_id": "CUST-123", "cache_hit": True}
    agent.redis.setex("customer_360:CUST-123", 86400, json.dumps(cached_data))

    result = await agent.get_customer_360_view("CUST-123")

    assert result["cache_hit"] is True
    assert result["customer_id"] == "CUST-123"

@pytest.mark.asyncio
async def test_insights_generation():
    """測試 AI 見解生成。"""
    agent = CrossSystemCorrelationAgent()

    system_results = [
        SystemQueryResult(
            system_name="servicenow",
            status="success",
            data={"open_tickets": [{"priority": "P1"}]}
        )
    ]

    with patch("openai.ChatCompletion.acreate") as mock_openai:
        mock_openai.return_value = {
            "choices": [{"message": {"content": '[{"type": "risk", "title": "High churn risk"}]'}}]
        }

        insights = await agent._generate_insights("CUST-123", system_results)

        assert len(insights) > 0
        assert insights[0]["type"] == "risk"
```

---

### 集成測試

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_end_to_end_customer_360():
    """測試端到端的客戶 360 度視圖查詢。"""
    agent = CrossSystemCorrelationAgent()

    response = await agent.get_customer_360_view("CUST-12345")

    assert response["customer_id"] == "CUST-12345"
    assert "systems" in response
    assert "insights" in response
    assert response["total_query_time_ms"] < 5000  # < 5 秒
```

---

### 負載測試

```python
import asyncio
from locust import HttpUser, task, between

class CustomerCorrelationUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_customer_360(self):
        self.client.post("/api/correlation/customer-360", json={
            "customer_id": "CUST-12345",
            "force_refresh": False
        })

# 運行: locust -f locustfile.py --host=http://localhost:8000
# 目標: 50 個並發用戶, P95 < 5 秒
```

---

## 3.8 風險和緩解

| 風險 | 概率 | 影響 | 緩解策略 |
|---|---|---|---|
| **外部 API 速率限制** | 中 | 高 | 實現 Redis 緩存 (TTL: 1 天) 以減少 API 調用 |
| **系統不可用** | 中 | 中 | 實現優雅降級 (返回部分結果) |
| **LLM 成本/速度** | 低 | 中 | 使用 GPT-4o (更便宜, 更快), 限制 token 為 500 |
| **緩存失效** | 低 | 低 | 提供手動緩存失效端點 |

---

## 3.9 未來增強 (Post-MVP)

1. **實時緩存失效**: 當外部系統中的數據更改時使緩存失效
2. **更多系統**: 添加更多外部系統 (Salesforce, Zendesk, Jira)
3. **預測分析**: 使用 ML 預測客戶流失風險
4. **自定義儀表板**: 允許用戶創建自定義的客戶 360 度視圖
5. **導出到 PDF**: 導出客戶 360 度視圖為 PDF 報告
6. **Webhook 通知**: 當檢測到高風險見解時發送警報
7. **歷史趨勢**: 顯示客戶健康隨時間變化的圖表

---

## 3.10 附錄

### 相關文檔

- ServiceNow REST API: https://developer.servicenow.com/dev.do#!/reference/api/tokyo/rest
- Dynamics 365 Web API: https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/overview
- SharePoint REST API: https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/get-to-know-the-sharepoint-rest-service
- Redis 緩存最佳實踐: https://redis.io/docs/manual/patterns/

### 術語表

- **Customer 360 View**: 客戶數據的統一視圖，包含來自所有系統的信息
- **Graceful Degradation**: 即使一個或多個系統失敗也能返回部分結果
- **Cross-System Correlation**: 識別不同系統數據之間的關係
- **Cache Hit Rate**: 從緩存而不是外部 API 提供的請求百分比
