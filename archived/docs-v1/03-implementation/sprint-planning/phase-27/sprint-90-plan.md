# Sprint 90: mem0 整合完善

## Sprint Info

| Field | Value |
|-------|-------|
| **Sprint Number** | 90 |
| **Phase** | 27 - mem0 整合完善 |
| **Duration** | 5-7 days |
| **Story Points** | 13 pts |
| **Status** | 計劃中 |
| **Priority** | 🟡 P1 高優先 |

---

## Sprint Goal

完善 mem0 整合的依賴、配置和測試，確保長期記憶系統可正常運作。

---

## Prerequisites

- Phase 26 完成（DevUI 前端）
- OpenAI API key（向量生成）
- Anthropic API key（記憶提取）

---

## User Stories

### S90-1: 添加 mem0 依賴 (1 pt)

**Description**: 將 mem0 SDK 添加到項目依賴

**Acceptance Criteria**:
- [ ] 添加 `mem0ai>=0.0.1` 到 `requirements.txt`
- [ ] `pip install -r requirements.txt` 成功
- [ ] `python -c "import mem0"` 無錯誤
- [ ] 現有測試仍然通過

**Files to Modify**:
- `backend/requirements.txt`

---

### S90-2: 環境變數配置 (2 pts)

**Description**: 完善 mem0 相關的環境變數配置

**Acceptance Criteria**:
- [ ] 更新 `.env.example` 包含所有 mem0 配置
- [ ] 更新 `types.py` 支持環境變數讀取
- [ ] 配置項包含：
  - `MEM0_ENABLED`
  - `QDRANT_PATH`
  - `QDRANT_COLLECTION`
  - `EMBEDDING_MODEL`
  - `MEMORY_LLM_PROVIDER`
  - `MEMORY_LLM_MODEL`
  - `WORKING_MEMORY_TTL`
  - `SESSION_MEMORY_TTL`
- [ ] 默認值合理

**Files to Modify**:
- `backend/.env.example`
- `backend/src/integrations/memory/types.py`

**Technical Design**:
```python
# backend/src/integrations/memory/types.py
import os
from dataclasses import dataclass, field

@dataclass
class MemoryConfig:
    """Memory system configuration."""

    # Qdrant settings
    qdrant_path: str = field(
        default_factory=lambda: os.getenv("QDRANT_PATH", "/data/mem0/qdrant")
    )
    qdrant_collection: str = field(
        default_factory=lambda: os.getenv("QDRANT_COLLECTION", "ipa_memories")
    )

    # Embedding settings
    embedding_model: str = field(
        default_factory=lambda: os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    )

    # LLM settings for memory extraction
    llm_provider: str = field(
        default_factory=lambda: os.getenv("MEMORY_LLM_PROVIDER", "anthropic")
    )
    llm_model: str = field(
        default_factory=lambda: os.getenv("MEMORY_LLM_MODEL", "claude-sonnet-4-20250514")
    )

    # TTL settings (seconds)
    working_memory_ttl: int = field(
        default_factory=lambda: int(os.getenv("WORKING_MEMORY_TTL", "1800"))
    )
    session_memory_ttl: int = field(
        default_factory=lambda: int(os.getenv("SESSION_MEMORY_TTL", "604800"))
    )

    # Feature flag
    enabled: bool = field(
        default_factory=lambda: os.getenv("MEM0_ENABLED", "true").lower() == "true"
    )
```

---

### S90-3: mem0_client.py 單元測試 (5 pts)

**Description**: 為 Mem0Client 類添加完整的單元測試

**Acceptance Criteria**:
- [ ] 測試 `initialize()` 成功場景
- [ ] 測試 `initialize()` 失敗場景
- [ ] 測試 `add_memory()` 功能
- [ ] 測試 `search_memory()` 功能
- [ ] 測試 `get_all()` 功能
- [ ] 測試 `get_memory()` 功能
- [ ] 測試 `update_memory()` 功能
- [ ] 測試 `delete_memory()` 功能
- [ ] 測試 `delete_all()` 功能
- [ ] 測試 `get_history()` 功能
- [ ] Mock 外部 API 調用
- [ ] 測試覆蓋率 > 85%

**Files to Create**:
- `backend/tests/unit/test_mem0_client.py`

---

### S90-4: Memory API 集成測試 (3 pts)

**Description**: 為 Memory API 端點添加集成測試

**Acceptance Criteria**:
- [ ] 測試 `POST /memory/add` 端點
- [ ] 測試 `POST /memory/search` 端點
- [ ] 測試 `GET /memory/user/{user_id}` 端點
- [ ] 測試 `GET /memory/{memory_id}` 端點
- [ ] 測試 `DELETE /memory/{memory_id}` 端點
- [ ] 測試 `POST /memory/promote` 端點
- [ ] 測試 `POST /memory/context` 端點
- [ ] 測試 `GET /memory/health` 端點
- [ ] 測試錯誤處理和驗證

**Files to Create**:
- `backend/tests/integration/test_memory_api.py`

---

### S90-5: 文檔更新 (2 pts)

**Description**: 更新 mem0 相關的技術文檔

**Acceptance Criteria**:
- [ ] 創建 `docs/04-usage/memory-configuration.md`
- [ ] 更新 `docs/02-architecture/technical-architecture.md`
- [ ] 包含配置說明
- [ ] 包含 API 使用示例
- [ ] 包含故障排除章節

**Files to Create/Modify**:
- `docs/04-usage/memory-configuration.md` (新增)
- `docs/02-architecture/technical-architecture.md` (更新)

---

## Definition of Done

- [ ] 所有 Stories 完成
- [ ] mem0 依賴安裝成功
- [ ] 環境變數配置完整
- [ ] 測試覆蓋率 > 85%
- [ ] 文檔完整

---

## Success Metrics

| Metric | Target |
|--------|--------|
| 依賴安裝 | 無衝突 |
| 單元測試覆蓋率 | > 85% |
| 集成測試通過率 | 100% |
| 文檔完整性 | 100% |

---

**Created**: 2026-01-13
**Story Points**: 13 pts
