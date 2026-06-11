# Sprint 100 技術決策

## 決策記錄

### D100-1: Swarm 數據模型設計

**日期**: 2026-01-29

**決策**: 使用 Python dataclasses 搭配自定義序列化方法

**原因**:
1. Dataclasses 提供簡潔的語法和自動生成的 `__init__`、`__repr__`
2. 自定義 `to_dict()` / `from_dict()` 方法提供靈活的序列化控制
3. 與 Pydantic schemas 分離，保持領域模型和 API 模型的獨立性
4. 支援 datetime 和 enum 的正確序列化

**替代方案**:
- 直接使用 Pydantic BaseModel - 但會導致領域模型與 API 耦合
- 使用 TypedDict - 缺乏方法支持和驗證

---

### D100-2: SwarmTracker 線程安全策略

**日期**: 2026-01-29

**決策**: 使用 `threading.RLock` (可重入鎖)

**原因**:
1. RLock 允許同一線程多次獲取鎖，避免死鎖
2. Swarm 操作可能涉及多層嵌套調用
3. 性能影響可接受（單機場景）

**替代方案**:
- 使用 asyncio.Lock - 但 SwarmTracker 設計為同步 API
- 使用 Redis 分佈式鎖 - 過於複雜，留待未來擴展

---

### D100-3: Worker 狀態機設計

**日期**: 2026-01-29

**決策**: 使用狀態 enum 和隱式狀態轉換

**狀態流轉**:
```
pending → running → thinking ⇄ tool_calling → completed
                  ↘                         ↗
                    ────→ failed ←──────────
```

**原因**:
1. 狀態轉換由操作方法隱式觸發（如 add_worker_thinking → THINKING）
2. 不需要顯式狀態機，減少複雜度
3. 狀態轉換在 tracker 方法中集中管理

---

### D100-4: API 端點設計

**日期**: 2026-01-29

**決策**: 採用 RESTful 資源導向設計

**端點結構**:
```
GET /api/v1/swarm/{swarm_id}                    # Swarm 狀態
GET /api/v1/swarm/{swarm_id}/workers            # Workers 列表
GET /api/v1/swarm/{swarm_id}/workers/{worker_id} # Worker 詳情
```

**原因**:
1. 符合 RESTful 最佳實踐
2. 與現有 API 風格一致
3. 支援細粒度的資源訪問

**未來擴展**:
- SSE endpoint: `/api/v1/swarm/{swarm_id}/events` (Sprint 101)

---

### D100-5: 全局 SwarmTracker 實例管理

**日期**: 2026-01-29

**決策**: 使用模組級全局變量搭配 getter/setter 函數

**實現**:
```python
_swarm_tracker: Optional[SwarmTracker] = None

def get_swarm_tracker() -> SwarmTracker:
    global _swarm_tracker
    if _swarm_tracker is None:
        _swarm_tracker = SwarmTracker()
    return _swarm_tracker

def set_swarm_tracker(tracker: SwarmTracker) -> None:
    global _swarm_tracker
    _swarm_tracker = tracker
```

**原因**:
1. 簡單直接，符合專案現有模式
2. 支援測試時注入 mock tracker
3. 延遲初始化，避免模組導入時的副作用

---

### D100-6: Swarm 與 ClaudeCoordinator 整合策略

**日期**: 2026-01-29

**決策**: 使用 Hook 模式進行松耦合整合

**Hook 方法**:
- `on_coordination_started()`
- `on_subtask_started()`
- `on_subtask_progress()`
- `on_tool_call()`
- `on_thinking()`
- `on_subtask_completed()`
- `on_coordination_completed()`

**原因**:
1. ClaudeCoordinator 不需要知道 Swarm 的具體實現
2. SwarmIntegration 可以獨立測試
3. 未來可以輕鬆替換或擴展整合層

---

## 技術債務

### TD100-1: Redis 支持 (低優先級)

**描述**: SwarmTracker 目前只支持內存存儲，不支持 Redis

**影響**: 單機限制，重啟後狀態丟失

**計劃**: 評估後決定是否在 Phase 29 後期添加

---

### TD100-2: Swarm 持久化 (低優先級)

**描述**: Swarm 狀態未持久化到數據庫

**影響**: 歷史 Swarm 數據無法查詢

**計劃**: 根據需求在未來 Sprint 添加

---

## 參考文檔

- Sprint 100 計劃: `docs/03-implementation/sprint-planning/phase-29/sprint-100-plan.md`
- Sprint 100 檢查清單: `docs/03-implementation/sprint-planning/phase-29/sprint-100-checklist.md`
- API 參考: `docs/api/swarm-api-reference.md`
