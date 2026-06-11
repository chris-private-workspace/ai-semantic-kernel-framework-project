# Sprint 128: LLMClassifier Mock→Real + MAF Anti-Corruption Layer

## 概述

Sprint 128 啟動 Phase 34 P2，將三層路由的 Layer 3（LLMClassifier）從 Mock 遷移到真實 LLM 調用，並建立 MAF Anti-Corruption Layer 以隔離 Microsoft Agent Framework preview API 變更的影響。

## 目標

1. LLMClassifier 從 Mock 遷移到真實 Claude/Azure OpenAI 調用
2. 建立 MAF Anti-Corruption Layer（ACL）
3. 三層路由覆蓋率從 90% 提升到 99%+
4. MAF API 變更風險隔離

## Story Points: 25 點

## 前置條件

- ⬜ Phase 34 P1 完成（Sprint 124-127）
- ⬜ LLM API Key 配置就緒（Claude + Azure OpenAI）
- ⬜ MAF 最新 preview 版本確認

## 任務分解

### Story 128-1: LLMClassifier Mock→Real (3 天, P2)

**目標**: 將 LLMClassifier 從返回 Mock 結果遷移到真實 LLM 調用

**現狀**:
- `src/integrations/orchestration/intent_router/llm_classifier/classifier.py`
- 目前預設使用 MockLLMClassifier，返回硬編碼分類結果
- PatternMatcher（Layer 1）和 SemanticRouter（Layer 2）已是真實實現

**遷移方案**:
```python
# 遷移前
class LLMClassifier:
    async def classify(self, text: str) -> ClassificationResult:
        return self._mock_classify(text)  # 硬編碼

# 遷移後
class LLMClassifier:
    async def classify(self, text: str) -> ClassificationResult:
        response = await self._llm_client.chat(
            messages=[{"role": "system", "content": CLASSIFICATION_PROMPT},
                      {"role": "user", "content": text}],
            response_format=ClassificationResult
        )
        return response
```

**交付物**:
- 真實 LLM 調用實現（Claude Haiku 為主，Azure OpenAI fallback）
- 分類 Prompt 模板（ITIntentCategory 完整映射）
- 結果快取機制（相似查詢不重複調用）
- 降級策略（LLM 不可用時 fallback 到 Mock）

### Story 128-2: MAF Anti-Corruption Layer (2 天, P2)

**目標**: 建立 ACL 隔離 MAF preview API 變更影響

**交付物**:
- `src/integrations/agent_framework/acl/` — Anti-Corruption Layer
- 穩定的內部介面定義
- MAF API 版本適配器

**ACL 架構**:
```
IPA 內部代碼
  → ACL Interface（穩定）
    → MAF Adapter（隨 MAF 版本變化）
      → agent_framework 套件
```

**檔案結構**:
```
src/integrations/agent_framework/acl/
├── __init__.py
├── interfaces.py          # 穩定的內部介面
├── adapter.py             # MAF API 適配器
├── version_detector.py    # MAF 版本偵測
└── migration_guide.py     # 版本遷移指南
```

### Story 128-3: 測試與驗證 (2 天, P2)

**測試範圍**:

| 測試 | 範圍 |
|------|------|
| `test_llm_classifier_real.py` | 真實 LLM 分類（Mock LLM client） |
| `test_classification_prompt.py` | Prompt 正確性與格式 |
| `test_llm_cache.py` | 分類結果快取 |
| `test_llm_fallback.py` | LLM 不可用降級 |
| `test_acl_interfaces.py` | ACL 介面穩定性 |
| `test_acl_adapter.py` | MAF 適配器 |
| `test_three_layer_routing.py` | 三層路由端到端（全真實） |

## 風險

| 風險 | 影響 | 緩解 |
|------|------|------|
| LLM API 延遲 | Layer 3 回應慢 | 快取 + 超時設定 |
| LLM 分類不準確 | 路由錯誤 | Prompt 調優 + 評估集 |
| MAF breaking change | Builder 中斷 | ACL 隔離 |

## 依賴

- 改善提案 Phase D P2: LLMClassifier Mock→Real + MAF ACL
- LLM API 配置（環境變數）
