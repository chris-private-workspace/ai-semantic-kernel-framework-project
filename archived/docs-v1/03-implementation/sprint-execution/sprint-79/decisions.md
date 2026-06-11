# Sprint 79 Decisions: Claude 自主規劃引擎 + mem0 整合

> **Phase 22**: Claude 自主能力與學習系統
> **日期**: 2026-01-12

---

## 架構決策

### ADR-79-1: 自主規劃引擎四階段閉環設計

**決策**: 採用「分析 → 規劃 → 執行 → 驗證」四階段閉環架構

**背景**:
- 目前 Claude 僅作為「Tool 執行者」，被動接收指令
- 需要升級為能夠自主規劃的角色
- 需要支援複雜 IT 事件的端到端處理

**方案比較**:

| 方案 | 優點 | 缺點 |
|------|------|------|
| A: 單一執行器 | 簡單 | 缺乏驗證和回饋 |
| B: 三階段（無驗證） | 較完整 | 無法學習改進 |
| C: 四階段閉環 ✅ | 完整閉環，可學習 | 較複雜 |

**選擇**: 方案 C

**理由**:
1. 閉環設計允許系統從執行結果學習
2. 驗證階段提供品質保證
3. 與 mem0 記憶系統整合，實現持續改進

---

### ADR-79-2: Extended Thinking 動態 budget_tokens

**決策**: 根據事件複雜度動態調整 Extended Thinking 的 budget_tokens

**背景**:
- Extended Thinking 需要 budget_tokens 參數
- 不同複雜度事件需要不同的思考深度
- 需要平衡成本和品質

**策略**:

| 複雜度 | budget_tokens | 使用場景 |
|--------|---------------|----------|
| simple | 4,096 | 常見問題，已知解決方案 |
| moderate | 8,192 | 標準事件，需要分析 |
| complex | 16,000 | 複雜事件，多系統影響 |
| critical | 32,000 | 關鍵事件，需要深度分析 |

**實作**:
```python
COMPLEXITY_BUDGET_TOKENS = {
    EventComplexity.SIMPLE: 4096,
    EventComplexity.MODERATE: 8192,
    EventComplexity.COMPLEX: 16000,
    EventComplexity.CRITICAL: 32000,
}
```

---

### ADR-79-3: 三層記憶架構整合

**決策**: 採用三層記憶架構整合現有 Redis/PostgreSQL 與新的 mem0

**背景**:
- 工作記憶 (Redis) - 短期，TTL 30 分鐘
- 會話記憶 (PostgreSQL) - 中期，TTL 7 天
- 長期記憶 (mem0) - 永久，向量存儲

**架構**:
```
┌─────────────────────────────────────────────────────────────┐
│                    UnifiedMemoryManager                      │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: WorkingMemory (Redis)                             │
│  - 當前會話上下文                                            │
│  - TTL: 30 分鐘                                             │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: SessionMemory (PostgreSQL)                         │
│  - 會話歷史記錄                                              │
│  - TTL: 7 天                                                │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: LongTermMemory (mem0 + Qdrant)                    │
│  - 事件處理經驗                                              │
│  - 用戶偏好                                                  │
│  - 系統知識                                                  │
│  - 永久存儲                                                  │
└─────────────────────────────────────────────────────────────┘
```

**選擇本地 Qdrant 而非雲服務**:
- 數據隱私考慮
- 避免外部依賴
- 成本控制

---

### ADR-79-4: 記憶類型分類

**決策**: 定義六種記憶類型

| 類型 | 說明 | 用途 |
|------|------|------|
| EVENT_RESOLUTION | 事件解決方案 | 學習最佳實踐 |
| USER_PREFERENCE | 用戶偏好 | 個性化服務 |
| SYSTEM_KNOWLEDGE | 系統知識 | 基礎設施資訊 |
| BEST_PRACTICE | 最佳實踐 | 標準操作流程 |
| CONVERSATION | 對話片段 | 上下文延續 |
| FEEDBACK | 用戶回饋 | 持續改進 |

---

## 技術決策

### TDR-79-1: mem0 SDK 整合方式

**決策**: 直接使用 mem0 Python SDK 而非自建向量存儲

**理由**:
1. mem0 提供開箱即用的記憶提取能力
2. 內建 LLM 支援用於語義理解
3. 減少開發時間

**配置**:
```python
from mem0 import Memory

memory = Memory(
    vector_store={
        "provider": "qdrant",
        "config": {"path": "/data/mem0/qdrant"}
    },
    embedder={
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"}
    },
    llm={
        "provider": "anthropic",
        "config": {"model": "claude-sonnet-4-20250514"}
    }
)
```

---

### TDR-79-2: 嵌入模型選擇

**決策**: 使用 OpenAI text-embedding-3-small

**比較**:

| 模型 | 維度 | 成本 | 品質 |
|------|------|------|------|
| text-embedding-ada-002 | 1536 | 低 | 良好 |
| text-embedding-3-small ✅ | 1536 | 最低 | 良好 |
| text-embedding-3-large | 3072 | 高 | 最佳 |

**選擇理由**:
- 成本效益最佳
- 1536 維度足夠支援語義搜索
- 與現有 Azure OpenAI 整合

---

### TDR-79-3: API 端點設計

**Memory API 端點**:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/memory/add` | 添加記憶 |
| GET | `/api/v1/memory/search` | 搜索記憶 |
| GET | `/api/v1/memory/user/{user_id}` | 獲取用戶記憶 |
| DELETE | `/api/v1/memory/{id}` | 刪除記憶 |

**Autonomous API 端點**:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/claude-sdk/autonomous/plan` | 生成規劃 |
| GET | `/api/v1/claude-sdk/autonomous/{id}` | 獲取規劃 |
| POST | `/api/v1/claude-sdk/autonomous/{id}/execute` | 執行規劃 (SSE) |
| DELETE | `/api/v1/claude-sdk/autonomous/{id}` | 刪除規劃 |
| GET | `/api/v1/claude-sdk/autonomous/` | 列出規劃 |
| POST | `/api/v1/claude-sdk/autonomous/estimate` | 估算資源 |
| POST | `/api/v1/claude-sdk/autonomous/{id}/verify` | 驗證結果 |

---

## 風險與緩解

| 風險 | 影響 | 機率 | 緩解措施 |
|------|------|------|---------|
| Extended Thinking 品質不穩定 | 高 | 低 | 動態 budget_tokens + 驗證階段 |
| mem0 成本超預算 | 高 | 中 | 本地 Qdrant + 批量嵌入 |
| 向量嵌入 API 限制 | 中 | 中 | 批量處理 + 緩存 |
| 記憶檢索延遲 | 中 | 低 | 索引優化 + 緩存層 |

---

**更新日期**: 2026-01-12
