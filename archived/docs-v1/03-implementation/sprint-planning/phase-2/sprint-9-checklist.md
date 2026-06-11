# Sprint 9 Checklist: 群組協作模式 (GroupChat & Multi-turn Conversation)

**Sprint 目標**: 實現多 Agent 群組聊天和多輪對話能力，支援複雜協作場景
**週期**: Week 19-20
**總點數**: 42 點
**Phase 2 功能**: P2-F5 GroupChat + P2-F6 Multi-turn + P2-F7 Conversation Memory
**狀態**: ✅ 完成 (42/42 點)

---

## 快速驗證命令

```bash
# 驗證 GroupChat 模組
python -c "from src.domain.orchestration.groupchat import GroupChatManager; print('OK')"

# 驗證 GroupChat API
curl http://localhost:8000/api/v1/groupchat/status

# 建立群組聊天
curl -X POST http://localhost:8000/api/v1/groupchat/create \
  -H "Content-Type: application/json" \
  -d '{"name": "test-group", "agents": ["agent1", "agent2"]}'

# 運行 GroupChat 測試
cd backend && pytest tests/unit/test_groupchat*.py tests/unit/test_multiturn*.py -v
```

---

## S9-1: GroupChatManager 群組聊天管理器 (8 點) ✅

### 核心管理器 (src/domain/orchestration/groupchat/)
- [x] 創建 `manager.py`
  - [x] SpeakerSelectionMethod 枚舉
    - [x] AUTO - LLM 自動選擇
    - [x] ROUND_ROBIN - 輪流發言
    - [x] RANDOM - 隨機選擇
    - [x] MANUAL - 人工指定
    - [x] PRIORITY - 按優先級
    - [x] EXPERTISE - 按專業能力
  - [x] MessageType 枚舉
    - [x] USER - 用戶訊息
    - [x] AGENT - Agent 訊息
    - [x] SYSTEM - 系統訊息
    - [x] FUNCTION_CALL - 函數調用
    - [x] FUNCTION_RESULT - 函數結果
  - [x] GroupMessage 數據類
    - [x] id 屬性
    - [x] group_id 屬性
    - [x] sender_id 屬性
    - [x] sender_name 屬性
    - [x] content 屬性
    - [x] message_type 屬性
    - [x] timestamp 屬性
    - [x] metadata 屬性
    - [x] reply_to 屬性
  - [x] GroupChatConfig 數據類
    - [x] max_rounds 屬性
    - [x] max_messages_per_round 屬性
    - [x] speaker_selection_method 屬性
    - [x] allow_repeat_speaker 屬性
    - [x] termination_conditions 屬性
    - [x] timeout_seconds 屬性
    - [x] enable_voting 屬性
    - [x] consensus_threshold 屬性
  - [x] GroupChatState 數據類
  - [x] GroupChatManager 類
    - [x] __init__() 初始化方法
    - [x] start_conversation() 開始對話
    - [x] _execute_round() 執行一輪
    - [x] _get_agent_response() 獲取回應
    - [x] _build_context_for_agent() 構建上下文
    - [x] _should_terminate() 終止判斷
    - [x] add_message() 添加訊息
    - [x] get_transcript() 獲取記錄
    - [x] get_summary() 獲取摘要

### 終止檢查器
- [x] 創建 `termination.py`
  - [x] TerminationChecker 類
  - [x] should_terminate() 終止檢查
  - [x] add_condition() 添加條件
  - [x] 支援關鍵字終止
  - [x] 支援輪次終止
  - [x] 支援超時終止

### 驗證標準
- [x] GroupChatManager 可管理多 Agent 對話
- [x] 最大輪次限制正確
- [x] 超時處理正常
- [x] 訊息記錄完整
- [x] 終止條件正確觸發

**測試**: 69 tests passed

---

## S9-2: SpeakerSelector 發言者選擇器 (5 點) ✅

### 選擇器實現 (src/domain/orchestration/groupchat/)
- [x] 創建 `speaker_selector.py`
  - [x] SpeakerSelector 類
  - [x] select_next() 選擇下一位發言者
  - [x] _select_auto() 自動選擇（LLM）
  - [x] _select_round_robin() 輪流選擇
  - [x] _select_random() 隨機選擇
  - [x] _select_manual() 人工選擇
  - [x] _select_by_priority() 優先級選擇
  - [x] _select_by_expertise() 專業能力選擇
  - [x] _build_selection_prompt() 構建選擇提示
  - [x] _parse_selection_response() 解析選擇結果

### 專業能力匹配
- [x] 創建 `expertise_matcher.py`
  - [x] ExpertiseMatcher 類
  - [x] match_expertise() 匹配專業能力
  - [x] calculate_relevance() 計算相關性
  - [x] get_best_agent() 獲取最佳 Agent

### 驗證標準
- [x] 所有選擇策略正確運作
- [x] AUTO 模式 LLM 選擇合理
- [x] ROUND_ROBIN 順序正確
- [x] EXPERTISE 匹配準確
- [x] 不重複發言控制正常

**測試**: 54 tests passed

---

## S9-3: MultiTurnSessionManager 多輪對話管理器 (8 點) ✅

### 會話管理 (src/domain/orchestration/multiturn/)
- [x] 創建 `session_manager.py`
  - [x] SessionStatus 枚舉
    - [x] ACTIVE - 活躍中
    - [x] PAUSED - 暫停
    - [x] COMPLETED - 完成
    - [x] EXPIRED - 過期
  - [x] MultiTurnSession 數據類
    - [x] session_id 屬性
    - [x] user_id 屬性
    - [x] agent_ids 屬性
    - [x] status 屬性
    - [x] context 屬性
    - [x] history 屬性
    - [x] created_at 屬性
    - [x] last_activity 屬性
  - [x] MultiTurnSessionManager 類
    - [x] create_session() 創建會話
    - [x] get_session() 獲取會話
    - [x] update_session() 更新會話
    - [x] close_session() 關閉會話
    - [x] resume_session() 恢復會話
    - [x] list_active_sessions() 列出活躍會話

### 輪次追蹤
- [x] 創建 `turn_tracker.py`
  - [x] TurnTracker 類
  - [x] start_turn() 開始輪次
  - [x] end_turn() 結束輪次
  - [x] get_current_turn() 獲取當前輪次
  - [x] get_turn_history() 獲取輪次歷史

### 上下文維護
- [x] 創建 `context_manager.py`
  - [x] SessionContextManager 類
  - [x] update_context() 更新上下文
  - [x] get_context() 獲取上下文
  - [x] merge_context() 合併上下文
  - [x] clear_context() 清除上下文

### 驗證標準
- [x] 會話創建和管理正常
- [x] 多輪次追蹤準確
- [x] 上下文在輪次間保持
- [x] 會話恢復正常
- [x] 過期會話正確處理

**測試**: 62 tests passed

---

## S9-4: ConversationMemoryStore 對話記憶存儲 (8 點) ✅

### 記憶存儲 (src/domain/orchestration/memory/)
- [x] 創建 `base.py` - 抽象基類
- [x] 創建 `models.py` - 數據模型
  - [x] SessionStatus 枚舉
  - [x] MessageRecord 數據類
  - [x] ConversationTurn 數據類
  - [x] ConversationSession 數據類
- [x] 創建 `in_memory.py` - 記憶體實現
  - [x] InMemoryConversationMemoryStore 類
  - [x] add_message() 添加訊息
  - [x] get_messages() 獲取訊息
  - [x] save_session() 保存會話
  - [x] load_session() 載入會話
  - [x] save_turn() 保存輪次
  - [x] search_by_content() 內容搜索
- [x] 創建 `redis_store.py` - Redis 實現
  - [x] RedisConversationMemoryStore 類
  - [x] TTL 支援
- [x] 創建 `postgres_store.py` - PostgreSQL 實現
  - [x] PostgresConversationMemoryStore 類
  - [x] SQL 查詢實現

### 驗證標準
- [x] 訊息正確存儲和檢索
- [x] 3 種存儲後端可用 (InMemory, Redis, PostgreSQL)
- [x] 會話記憶隔離
- [x] 內容搜索功能正常

**測試**: 51 tests passed

---

## S9-5: VotingManager 投票管理器 (5 點) ✅

### 投票機制 (src/domain/orchestration/groupchat/)
- [x] 創建 `voting.py`
  - [x] VoteType 枚舉
    - [x] APPROVE_REJECT - 批准/拒絕
    - [x] MULTIPLE_CHOICE - 多選
    - [x] RANKING - 排序
    - [x] WEIGHTED - 加權
    - [x] SCORE - 評分
  - [x] VoteResult 枚舉
  - [x] VotingSessionStatus 枚舉
  - [x] Vote 數據類
    - [x] vote_id 屬性
    - [x] voter_id 屬性
    - [x] voter_name 屬性
    - [x] choice 屬性
    - [x] weight 屬性
    - [x] timestamp 屬性
    - [x] reason 屬性
  - [x] VotingSession 數據類
    - [x] session_id 屬性
    - [x] group_id 屬性
    - [x] topic 屬性
    - [x] description 屬性
    - [x] vote_type 屬性
    - [x] options 屬性
    - [x] votes 屬性
    - [x] status 屬性
    - [x] result 屬性
  - [x] VotingManager 類
    - [x] create_session() 創建投票
    - [x] cast_vote() 投票
    - [x] change_vote() 更改投票
    - [x] withdraw_vote() 撤回投票
    - [x] close_session() 關閉投票
    - [x] cancel_session() 取消投票
    - [x] calculate_result() 計算結果
    - [x] get_statistics() 獲取統計

### 驗證標準
- [x] 5 種投票類型正確運作
- [x] 投票結果計算準確
- [x] 加權投票權重正確
- [x] 投票狀態追蹤完整
- [x] 法定人數檢查正確

**測試**: 54 tests passed

---

## S9-6: GroupChat API 路由 (8 點) ✅

### API 路由 (src/api/v1/groupchat/)
- [x] 創建 `routes.py`
  - [x] POST /groupchat/ - 創建群組
  - [x] GET /groupchat/ - 列出群組
  - [x] GET /groupchat/{id} - 獲取群組信息
  - [x] PATCH /groupchat/{id}/config - 更新配置
  - [x] POST /groupchat/{id}/agents/{agent_id} - 添加 Agent
  - [x] DELETE /groupchat/{id}/agents/{agent_id} - 移除 Agent
  - [x] POST /groupchat/{id}/start - 開始對話
  - [x] POST /groupchat/{id}/message - 發送訊息
  - [x] GET /groupchat/{id}/messages - 獲取訊息
  - [x] GET /groupchat/{id}/transcript - 獲取對話記錄
  - [x] GET /groupchat/{id}/summary - 獲取摘要
  - [x] POST /groupchat/{id}/terminate - 終止對話
  - [x] DELETE /groupchat/{id} - 刪除群組

### 多輪對話 API
- [x] Sessions API (整合在 routes.py)
  - [x] POST /groupchat/sessions/ - 創建會話
  - [x] GET /groupchat/sessions/ - 列出會話
  - [x] GET /groupchat/sessions/{id} - 獲取會話
  - [x] POST /groupchat/sessions/{id}/turns - 執行輪次
  - [x] GET /groupchat/sessions/{id}/history - 獲取歷史
  - [x] PATCH /groupchat/sessions/{id}/context - 更新上下文
  - [x] POST /groupchat/sessions/{id}/close - 關閉會話
  - [x] DELETE /groupchat/sessions/{id} - 刪除會話

### 投票 API
- [x] Voting API (整合在 routes.py)
  - [x] POST /groupchat/voting/ - 創建投票
  - [x] GET /groupchat/voting/ - 列出投票
  - [x] GET /groupchat/voting/{id} - 獲取投票
  - [x] POST /groupchat/voting/{id}/vote - 投票
  - [x] PATCH /groupchat/voting/{id}/vote/{voter_id} - 更改投票
  - [x] DELETE /groupchat/voting/{id}/vote/{voter_id} - 撤回投票
  - [x] GET /groupchat/voting/{id}/votes - 獲取所有投票
  - [x] POST /groupchat/voting/{id}/calculate - 計算結果
  - [x] GET /groupchat/voting/{id}/statistics - 獲取統計
  - [x] POST /groupchat/voting/{id}/close - 關閉投票
  - [x] POST /groupchat/voting/{id}/cancel - 取消投票
  - [x] DELETE /groupchat/voting/{id} - 刪除投票

### 請求/響應 Schema
- [x] 創建 `schemas.py`
  - [x] CreateGroupChatRequest
  - [x] GroupChatResponse
  - [x] GroupChatConfigUpdate
  - [x] SendMessageRequest
  - [x] MessageResponse
  - [x] ConversationResultResponse
  - [x] GroupChatSummaryResponse
  - [x] CreateSessionRequest
  - [x] SessionResponse
  - [x] ExecuteTurnRequest
  - [x] TurnResponse
  - [x] SessionHistoryResponse
  - [x] CreateVotingSessionRequest
  - [x] CastVoteRequest
  - [x] VoteResponse
  - [x] VotingSessionResponse
  - [x] VotingResultResponse
  - [x] VotingStatisticsResponse

### WebSocket 支援
- [x] WebSocket endpoint (/groupchat/{id}/ws)
  - [x] 實時訊息推送
  - [x] 對話狀態通知

### 驗證標準
- [x] 所有 API 端點可用
- [x] WebSocket 端點可用
- [x] 錯誤處理完善

**測試**: 37 tests passed

---

## 測試完成 ✅

### 單元測試
- [x] test_groupchat_manager.py (69 tests)
- [x] test_speaker_selector.py (54 tests)
- [x] test_multiturn_session.py (62 tests)
- [x] test_conversation_memory.py (51 tests)
- [x] test_voting_manager.py (54 tests)
- [x] test_groupchat_api.py (37 tests)

### 覆蓋率
- [x] 總測試數: 327 tests
- [x] 所有測試通過

---

## Sprint 完成標準

### 必須完成 (Must Have)
- [x] GroupChatManager 可管理多 Agent 對話
- [x] 6 種發言者選擇策略可用
- [x] 多輪對話上下文保持
- [x] 對話記憶存儲和檢索
- [x] 測試覆蓋率 >= 85%

### 應該完成 (Should Have)
- [x] 投票機制完整
- [x] WebSocket 實時更新
- [x] 完整 API 路由

### 可以延後 (Could Have)
- [ ] 進階共識算法
- [ ] 對話摘要優化

---

## 依賴確認

### 前置 Sprint
- [x] Sprint 7 完成 - 並行執行基礎設施
- [x] Sprint 8 完成 - Agent 協作協議

### 外部依賴
- [x] Redis 會話存儲 (可選)
- [x] WebSocket 支援配置
- [x] LLM 服務（發言者選擇，可選）

---

## Sprint 9 完成統計

| Story | 點數 | 狀態 | 測試數 |
|-------|------|------|--------|
| S9-1: GroupChatManager | 8 | ✅ | 69 |
| S9-2: SpeakerSelector | 5 | ✅ | 54 |
| S9-3: MultiTurnSessionManager | 8 | ✅ | 62 |
| S9-4: ConversationMemoryStore | 8 | ✅ | 51 |
| S9-5: VotingManager | 5 | ✅ | 54 |
| S9-6: GroupChat API | 8 | ✅ | 37 |
| **總計** | **42** | **✅ 完成** | **327** |

---

## 相關連結

- [Sprint 9 Plan](./sprint-9-plan.md) - 詳細計劃
- [Sprint 9 Progress](../../sprint-execution/sprint-9/progress.md) - 執行進度
- [Phase 2 Overview](./README.md) - Phase 2 概述
- [Sprint 8 Checklist](./sprint-8-checklist.md) - 前置 Sprint
- [Sprint 10 Plan](./sprint-10-plan.md) - 後續 Sprint
