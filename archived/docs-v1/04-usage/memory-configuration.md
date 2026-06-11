# Memory System Configuration Guide

IPA Platform 三層記憶系統配置指南

**版本**: 1.0
**日期**: 2026-01-14
**Sprint**: 90 - mem0 整合完善

---

## 1. 系統概述

IPA Platform 採用三層記憶系統架構，提供從短期到長期的完整記憶管理：

```
┌─────────────────────────────────────────────────────────────┐
│                   Three-Layer Memory System                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐     │
│  │   Working    │   │   Session    │   │  Long-term   │     │
│  │   Memory     │──▶│   Memory     │──▶│   Memory     │     │
│  │   (Redis)    │   │ (PostgreSQL) │   │ (mem0+Qdrant)│     │
│  └──────────────┘   └──────────────┘   └──────────────┘     │
│       TTL: 30min        TTL: 7 days        Permanent        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.1 記憶層說明

| 層級 | 存儲 | TTL | 用途 |
|------|------|-----|------|
| **Working** | Redis | 30 分鐘 | 當前對話上下文、臨時狀態 |
| **Session** | PostgreSQL | 7 天 | 會話歷史、中期記憶 |
| **Long-term** | mem0 + Qdrant | 永久 | 用戶偏好、系統知識、最佳實踐 |

### 1.2 記憶類型

- `event_resolution` - 事件解決方案
- `user_preference` - 用戶偏好設置
- `system_knowledge` - 系統基礎設施知識
- `best_practice` - 最佳實踐和模式
- `conversation` - 對話片段
- `feedback` - 用戶回饋和修正

---

## 2. 環境配置

### 2.1 必要環境變數

在 `.env` 文件中配置以下變數：

```bash
# ===========================================
# mem0 Long-term Memory Configuration
# ===========================================

# 啟用/禁用 mem0 記憶系統
MEM0_ENABLED=true

# Qdrant 向量存儲路徑 (本地檔案系統)
QDRANT_PATH=/data/mem0/qdrant

# Qdrant 集合名稱
QDRANT_COLLECTION=ipa_memories

# 向量生成嵌入模型
EMBEDDING_MODEL=text-embedding-3-small

# 記憶提取 LLM 提供者 (anthropic 或 openai)
MEMORY_LLM_PROVIDER=anthropic

# 記憶提取 LLM 模型
MEMORY_LLM_MODEL=claude-sonnet-4-20250514

# 工作記憶 TTL (秒) - 默認 30 分鐘
WORKING_MEMORY_TTL=1800

# 會話記憶 TTL (秒) - 默認 7 天
SESSION_MEMORY_TTL=604800

# ===========================================
# API Keys (Required for mem0)
# ===========================================

# OpenAI API Key - 用於向量嵌入
OPENAI_API_KEY=<your-openai-api-key>

# Anthropic API Key - 用於記憶提取
ANTHROPIC_API_KEY=<your-anthropic-api-key>
```

### 2.2 配置說明

#### 向量存儲 (Qdrant)

mem0 使用 Qdrant 進行向量存儲。默認配置使用本地檔案系統：

```python
# 配置示例
{
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "path": "/data/mem0/qdrant",  # 本地路徑
            "collection_name": "ipa_memories",
        },
    }
}
```

**生產環境**建議使用 Qdrant Cloud 或自託管 Qdrant 服務器：

```python
# 生產配置
{
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "qdrant.example.com",
            "port": 6333,
            "collection_name": "ipa_memories",
            "api_key": "<qdrant-api-key>",
        },
    }
}
```

#### 嵌入模型

支持的嵌入模型：

| 模型 | 維度 | 成本 | 推薦場景 |
|------|------|------|----------|
| `text-embedding-3-small` | 1536 | 低 | 開發/測試 |
| `text-embedding-3-large` | 3072 | 中 | 生產環境 |
| `text-embedding-ada-002` | 1536 | 低 | 舊版兼容 |

#### LLM 提供者

mem0 使用 LLM 進行記憶提取和語義理解：

- **Anthropic (推薦)**: Claude Sonnet 4 提供優秀的記憶提取能力
- **OpenAI**: GPT-4o 也可用於記憶提取

---

## 3. API 使用

### 3.1 添加記憶

```bash
POST /api/v1/memory/add

{
    "content": "User prefers dark mode for the dashboard interface",
    "user_id": "user-123",
    "memory_type": "user_preference",
    "metadata": {
        "source": "chat",
        "importance": 0.8,
        "tags": ["ui", "preference"]
    },
    "layer": "long_term"  # optional, auto-selected if not specified
}
```

**回應:**

```json
{
    "id": "mem-abc123",
    "user_id": "user-123",
    "content": "User prefers dark mode for the dashboard interface",
    "memory_type": "user_preference",
    "layer": "long_term",
    "created_at": "2026-01-14T10:00:00Z"
}
```

### 3.2 搜索記憶

```bash
POST /api/v1/memory/search

{
    "query": "user interface preferences",
    "user_id": "user-123",
    "memory_types": ["user_preference"],
    "min_importance": 0.5,
    "limit": 10
}
```

**回應:**

```json
{
    "results": [
        {
            "id": "mem-abc123",
            "content": "User prefers dark mode for the dashboard interface",
            "memory_type": "user_preference",
            "layer": "long_term",
            "score": 0.95,
            "metadata": {...}
        }
    ],
    "total": 1,
    "query": "user interface preferences"
}
```

### 3.3 獲取用戶記憶

```bash
GET /api/v1/memory/user/{user_id}?memory_types=user_preference&layers=long_term
```

### 3.4 刪除記憶

```bash
DELETE /api/v1/memory/{memory_id}?user_id=user-123
```

### 3.5 提升記憶層級

將記憶從較低層級提升到較高層級：

```bash
POST /api/v1/memory/promote

{
    "memory_id": "mem-abc123",
    "user_id": "user-123",
    "from_layer": "session",
    "to_layer": "long_term"
}
```

### 3.6 獲取上下文記憶

獲取與當前對話相關的記憶：

```bash
POST /api/v1/memory/context

{
    "user_id": "user-123",
    "session_id": "session-456",
    "query": "current task context",
    "limit": 10
}
```

### 3.7 健康檢查

```bash
GET /api/v1/memory/health
```

**回應:**

```json
{
    "status": "healthy",
    "mem0_initialized": true,
    "redis_connected": true,
    "embedding_service": true,
    "details": {
        "qdrant_path": "/data/mem0/qdrant",
        "embedding_model": "text-embedding-3-small",
        "working_memory_enabled": true
    }
}
```

---

## 4. Python SDK 使用

### 4.1 初始化客戶端

```python
from src.integrations.memory import Mem0Client, MemoryConfig

# 使用默認配置 (從環境變數)
client = Mem0Client()

# 使用自定義配置
config = MemoryConfig(
    qdrant_path="/custom/path",
    qdrant_collection="my_memories",
    embedding_model="text-embedding-3-large",
)
client = Mem0Client(config=config)

# 初始化連接
await client.initialize()
```

### 4.2 記憶操作

```python
from src.integrations.memory import (
    MemoryMetadata,
    MemorySearchQuery,
    MemoryType,
)

# 添加記憶
record = await client.add_memory(
    content="User prefers dark mode",
    user_id="user-123",
    memory_type=MemoryType.USER_PREFERENCE,
    metadata=MemoryMetadata(
        source="chat",
        importance=0.8,
        tags=["ui", "preference"],
    ),
)

# 搜索記憶
query = MemorySearchQuery(
    query="user preferences",
    user_id="user-123",
    limit=10,
)
results = await client.search_memory(query)

# 獲取所有記憶
memories = await client.get_all(
    user_id="user-123",
    memory_types=[MemoryType.USER_PREFERENCE],
)

# 更新記憶
updated = await client.update_memory(
    memory_id="mem-123",
    content="User now prefers light mode",
)

# 刪除記憶
success = await client.delete_memory("mem-123")

# 關閉連接
await client.close()
```

---

## 5. 故障排除

### 5.1 常見問題

#### mem0 初始化失敗

**症狀**: `ImportError: No module named 'mem0'`

**解決方案**:
```bash
pip install mem0ai
```

#### Qdrant 連接失敗

**症狀**: `Failed to connect to Qdrant`

**檢查**:
1. 確認 `QDRANT_PATH` 目錄存在且可寫入
2. 確認沒有其他進程佔用相同目錄
3. 檢查磁碟空間

#### OpenAI API 錯誤

**症狀**: `AuthenticationError: Invalid API key`

**解決方案**:
1. 確認 `OPENAI_API_KEY` 環境變數已設置
2. 驗證 API key 有效性
3. 檢查 API 配額

#### 記憶搜索無結果

**可能原因**:
1. 向量索引尚未建立 - 首次添加記憶後需等待索引完成
2. 查詢與記憶內容語義不匹配
3. 過濾條件過於嚴格

**解決方案**:
1. 降低 `min_importance` 閾值
2. 擴大 `memory_types` 過濾範圍
3. 使用更通用的查詢詞彙

### 5.2 性能調優

#### 優化搜索性能

```python
# 限制搜索範圍
query = MemorySearchQuery(
    query="specific query",
    user_id="user-123",
    memory_types=[MemoryType.USER_PREFERENCE],  # 縮小範圍
    limit=5,  # 減少返回數量
)
```

#### 批量操作

```python
# 使用批量刪除而非逐一刪除
await client.delete_all(user_id="user-123")
```

### 5.3 監控

檢查系統健康狀態：

```bash
curl http://localhost:8000/api/v1/memory/health
```

監控指標：
- `mem0_initialized`: mem0 客戶端是否初始化
- `redis_connected`: Redis 連接狀態 (工作記憶)
- `embedding_service`: 嵌入服務是否可用

---

## 6. 最佳實踐

### 6.1 記憶類型選擇

| 場景 | 推薦類型 | 說明 |
|------|----------|------|
| 用戶 UI 偏好 | `user_preference` | 持久化用戶設置 |
| 問題解決方案 | `event_resolution` | 記錄問題處理經驗 |
| 系統配置知識 | `system_knowledge` | 基礎設施相關知識 |
| 開發最佳實踐 | `best_practice` | 代碼風格、設計模式 |
| 對話上下文 | `conversation` | 短期對話歷史 |
| 用戶反饋 | `feedback` | 修正和改進建議 |

### 6.2 重要性評分

- **0.9-1.0**: 關鍵業務邏輯、安全相關
- **0.7-0.9**: 用戶核心偏好、重要決策
- **0.5-0.7**: 一般偏好、常規知識
- **0.3-0.5**: 輔助信息、上下文
- **0.0-0.3**: 臨時信息、可丟棄

### 6.3 層級選擇策略

```
重要性 > 0.8 → long_term
重要性 0.5-0.8 → session
重要性 < 0.5 → working
```

---

**相關文檔**:
- [Technical Architecture](../02-architecture/technical-architecture.md)
- [API Reference](../api/memory-api-reference.md)
- [Sprint 90 Plan](../03-implementation/sprint-planning/phase-27/sprint-90-plan.md)
