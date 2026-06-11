# Sprint 92: Semantic Router + LLM Classifier

## 概述

Sprint 92 專注於建立三層路由的 **Layer 2 (Semantic Router)** 和 **Layer 3 (LLM Classifier)**，完成三層路由核心架構。

## 目標

1. 整合 Aurelio Semantic Router
2. 定義 10+ 語義路由 (IT 服務場景)
3. 實現 LLMClassifier (Claude Haiku)
4. 設計多任務 Prompt (分類 + 完整度)

## Story Points: 30 點

## 前置條件

- ✅ Sprint 91 完成
- ✅ PatternMatcher 就緒
- ✅ 核心數據模型定義完成

## 任務分解

### Story 92-1: 整合 Aurelio Semantic Router (4h, P0)

**目標**: 整合 Aurelio 語義路由器，實現向量相似度匹配

**交付物**:
- `backend/src/integrations/orchestration/intent_router/semantic_router/router.py`
- `backend/src/integrations/orchestration/intent_router/semantic_router/__init__.py`

**驗收標準**:
- [ ] SemanticRouter 類實現完成
- [ ] 支援 Aurelio 向量編碼
- [ ] route() 方法返回 SemanticRouteResult
- [ ] 相似度閾值可配置 (預設 0.85)
- [ ] 延遲 < 100ms

### Story 92-2: 定義 10+ 語義路由 (4h, P0)

**目標**: 定義 IT 服務管理場景的語義路由

**交付物**:
- `backend/src/integrations/orchestration/intent_router/semantic_router/routes.py`

**路由定義**:

| 路由名稱 | 類別 | 範例語句 |
|---------|------|---------|
| incident_etl | incident | "ETL 今天跑失敗了" |
| incident_network | incident | "網路連線有問題" |
| incident_performance | incident | "系統跑得很慢" |
| request_account | request | "我需要申請新帳號" |
| request_access | request | "請幫我開通權限" |
| request_software | request | "可以幫我安裝軟體嗎" |
| change_deployment | change | "需要部署新版本" |
| change_config | change | "要修改系統設定" |
| query_status | query | "目前系統狀態如何" |
| query_report | query | "可以給我報表嗎" |

**驗收標準**:
- [ ] 至少 10 條語義路由
- [ ] 每條路由有 3-5 個範例語句
- [ ] 涵蓋 incident/request/change/query
- [ ] 測試覆蓋率 > 90%

### Story 92-3: 實現 LLMClassifier (5h, P0)

**目標**: 實現基於 Claude Haiku 的 LLM 分類器

**交付物**:
- `backend/src/integrations/orchestration/intent_router/llm_classifier/classifier.py`
- `backend/src/integrations/orchestration/intent_router/llm_classifier/__init__.py`

**驗收標準**:
- [ ] LLMClassifier 類實現完成
- [ ] 使用 Claude Haiku 模型
- [ ] classify() 方法返回 LLMClassificationResult
- [ ] 支援多任務輸出 (分類 + 完整度)
- [ ] 延遲 < 2000ms

### Story 92-4: 設計多任務 Prompt (3h, P0)

**目標**: 設計能同時輸出分類和完整度的 Prompt

**交付物**:
- `backend/src/integrations/orchestration/intent_router/llm_classifier/prompts.py`

**Prompt 結構**:

```python
CLASSIFICATION_PROMPT = """
你是一個 IT 服務管理分類專家。分析用戶輸入，返回 JSON 格式結果。

## 任務
1. 判斷意圖類別 (incident/request/change/query)
2. 判斷子意圖
3. 評估資訊完整度
4. 列出缺失的必要資訊

## 用戶輸入
{user_input}

## 輸出格式 (JSON)
{
  "intent_category": "incident|request|change|query",
  "sub_intent": "具體子意圖",
  "confidence": 0.0-1.0,
  "completeness": {
    "score": 0.0-1.0,
    "missing_fields": ["欄位1", "欄位2"]
  }
}
"""
```

**驗收標準**:
- [ ] Prompt 設計完成
- [ ] 輸出格式穩定可解析
- [ ] 測試案例覆蓋各種場景
- [ ] 錯誤處理完善

### Story 92-5: Semantic/LLM 單元測試 (4h, P0)

**目標**: 為 Semantic Router 和 LLM Classifier 編寫單元測試

**交付物**:
- `backend/tests/unit/orchestration/test_semantic_router.py`
- `backend/tests/unit/orchestration/test_llm_classifier.py`

**測試案例**:
- [ ] Semantic Router 匹配測試
- [ ] Semantic Router 相似度閾值測試
- [ ] LLM Classifier 分類測試
- [ ] LLM Classifier 完整度輸出測試
- [ ] 錯誤處理測試
- [ ] Mock 測試 (避免實際 API 調用)

## 技術設計

### SemanticRouter 類設計

```python
from semantic_router import Route, SemanticRouter as AurelioRouter

class SemanticRouter:
    def __init__(self, routes: List[Route], threshold: float = 0.85):
        self.router = AurelioRouter(routes=routes)
        self.threshold = threshold

    async def route(self, user_input: str) -> SemanticRouteResult:
        """語義路由"""
        result = self.router(user_input)

        if result.similarity >= self.threshold:
            return SemanticRouteResult(
                matched=True,
                intent_category=result.route.metadata["category"],
                sub_intent=result.route.metadata["sub_intent"],
                similarity=result.similarity,
            )

        return SemanticRouteResult(matched=False, similarity=result.similarity)
```

### LLMClassifier 類設計

```python
from anthropic import AsyncAnthropic

class LLMClassifier:
    def __init__(self, client: AsyncAnthropic, model: str = "claude-3-haiku-20240307"):
        self.client = client
        self.model = model

    async def classify(self, user_input: str) -> LLMClassificationResult:
        """LLM 分類"""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[
                {"role": "user", "content": CLASSIFICATION_PROMPT.format(user_input=user_input)}
            ]
        )

        # 解析 JSON 輸出
        result = self._parse_response(response.content[0].text)
        return LLMClassificationResult(**result)
```

## 依賴

- semantic-router >= 0.0.47 (Aurelio)
- anthropic >= 0.25.0 (Claude SDK)

## 風險

| 風險 | 緩解措施 |
|------|---------|
| Aurelio 版本相容性 | 鎖定版本，測試升級 |
| LLM 輸出不穩定 | 強化 Prompt，增加驗證 |
| API 調用成本 | 設定速率限制，快取策略 |

## 完成標準

- [ ] 所有 Story 完成
- [ ] 單元測試覆蓋率 > 90%
- [ ] Semantic Router 延遲 < 100ms
- [ ] LLM Classifier 延遲 < 2000ms
- [ ] 代碼審查通過

---

**Sprint 開始**: 2026-01-22
**Sprint 結束**: 2026-01-29
**Story Points**: 30
