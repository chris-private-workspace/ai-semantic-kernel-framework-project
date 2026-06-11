# Sprint 20 代碼狀態分析

**分析日期**: 2025-12-06
**分析範圍**: GroupChat 相關代碼

---

## 執行摘要

### 發現

**API 層存在雙重路徑問題**:
1. **原始路由** (lines 96-434): 使用 `domain.orchestration.groupchat.GroupChatManager`
2. **適配器路由** (lines 1061-1303): 使用 `integrations.agent_framework.builders.GroupChatBuilderAdapter`

**適配器缺少的功能**:
1. `EXPERTISE` 選擇策略 (含 ExpertiseMatcher)
2. `PRIORITY` 選擇策略
3. 投票系統 (Voting)

---

## 詳細分析

### 1. GroupChatBuilderAdapter (已存在)

**位置**: `backend/src/integrations/agent_framework/builders/groupchat.py`
**行數**: 1,276 行

**✅ 已正確使用官方 API**:
```python
from agent_framework import (
    GroupChatBuilder,
    GroupChatDirective,
    ManagerSelectionResponse,
)

# __init__ 中:
self._builder = GroupChatBuilder()
```

**當前支持的選擇方法** (5 種):
| 方法 | 狀態 |
|------|------|
| AUTO | ✅ 已實現 |
| ROUND_ROBIN | ✅ 已實現 |
| RANDOM | ✅ 已實現 |
| MANUAL | ✅ 已實現 |
| CUSTOM | ✅ 已實現 |

**缺少的選擇方法** (需要從 domain 層整合):
| 方法 | Domain 位置 | 說明 |
|------|------------|------|
| PRIORITY | `speaker_selector.py:219` | 按優先級選擇 |
| EXPERTISE | `speaker_selector.py:291` | 專業能力匹配 |

---

### 2. Domain 層 GroupChat 模組

**位置**: `backend/src/domain/orchestration/groupchat/`

| 文件 | 行數 | 主要功能 |
|------|------|----------|
| `manager.py` | ~600 | GroupChatManager 主類 |
| `speaker_selector.py` | 852 | 6 種選擇策略 + ExpertiseMatcher |
| `termination.py` | ~300 | 終止條件邏輯 |
| `voting.py` | ~400 | 投票系統 |
| `__init__.py` | ~50 | 模組導出 |

**總計**: ~2,200 行

---

### 3. API 路由分析

**位置**: `backend/src/api/v1/groupchat/routes.py`
**總行數**: 1,303 行

#### 原始路由 (使用 Domain 層) - 需要遷移

| 端點 | 行號 | 說明 |
|------|------|------|
| `POST /` | 96 | 創建群組聊天 |
| `GET /` | 144 | 列出群組聊天 |
| `GET /{group_id}` | 172 | 獲取詳情 |
| `PATCH /{group_id}/config` | 195 | 更新配置 |
| `POST /{group_id}/agents/{agent_id}` | 220 | 添加 Agent |
| `DELETE /{group_id}/agents/{agent_id}` | 243 | 移除 Agent |
| `POST /{group_id}/start` | 256 | 開始對話 |
| `POST /{group_id}/message` | 281 | 發送訊息 |
| `GET /{group_id}/messages` | 316 | 獲取訊息 |
| `GET /{group_id}/transcript` | 346 | 獲取記錄 |
| `GET /{group_id}/summary` | 367 | 獲取摘要 |
| `POST /{group_id}/terminate` | 401 | 終止對話 |
| `DELETE /{group_id}` | 423 | 刪除對話 |

#### 適配器路由 (已使用適配器) - 保留

| 端點 | 行號 | 說明 |
|------|------|------|
| `POST /adapter/` | 1061 | 創建適配器 |
| `GET /adapter/` | 1120 | 列出適配器 |
| `GET /adapter/{adapter_id}` | 1142 | 獲取適配器 |
| `POST /adapter/{adapter_id}/run` | 1163 | 執行適配器 |
| `POST /adapter/{adapter_id}/participants` | 1212 | 添加參與者 |
| `DELETE /adapter/{adapter_id}/participants/{name}` | 1236 | 移除參與者 |
| `DELETE /adapter/{adapter_id}` | 1253 | 刪除適配器 |

---

## Sprint 20 Story 影響分析

### S20-2: 整合 SpeakerSelector (8 pts)

**需要添加到適配器**:
1. `SpeakerSelectionMethod.PRIORITY` 枚舉值
2. `SpeakerSelectionMethod.EXPERTISE` 枚舉值
3. `create_priority_selector()` 函數
4. `create_expertise_selector()` 函數 (整合 ExpertiseMatcher)

**可保留為內部依賴**:
- `ExpertiseMatcher` 類 (複雜邏輯，不需重寫)

### S20-3: 整合 Termination 條件 (5 pts)

**當前適配器已有**:
- `max_rounds` 支持
- `termination_condition` 函數支持

**需要驗證/添加**:
- 關鍵詞終止
- 共識達成終止
- 超時終止

### S20-4: Voting 系統擴展 (5 pts)

**需要創建**: `GroupChatVotingAdapter` 類
- 繼承 `GroupChatBuilderAdapter`
- 整合 `domain/orchestration/groupchat/voting.py` 邏輯

### S20-1: API 路由重構 (8 pts)

**需要遷移的路由**: 13 個端點
**策略**: 修改原始路由使用 `GroupChatBuilderAdapter`，保留 `/adapter/` 路由作為進階 API

### S20-5: 測試遷移 (5 pts)

**需要創建**:
- `tests/unit/test_groupchat_adapter.py`
- `tests/unit/test_groupchat_voting_adapter.py`
- 更新 `tests/integration/test_groupchat_api.py`

### S20-6: 標記 Deprecated (3 pts)

**需要標記**:
- `domain/orchestration/groupchat/__init__.py`

---

## 建議執行順序

1. **S20-2**: 先完善適配器的選擇策略 (添加 PRIORITY, EXPERTISE)
2. **S20-3**: 驗證/完善終止條件
3. **S20-4**: 創建投票適配器擴展
4. **S20-1**: 遷移 API 路由
5. **S20-5**: 更新測試
6. **S20-6**: 標記舊代碼

---

## 風險評估

| 風險 | 等級 | 緩解措施 |
|------|------|----------|
| API 響應格式變更 | 中 | 保持相同的 Response Schema |
| 功能缺失 | 低 | 逐項驗證每個功能 |
| 測試覆蓋不足 | 中 | 詳細測試計劃 |

---

**分析完成**: 2025-12-06
**下一步**: 開始 S20-2 實現
