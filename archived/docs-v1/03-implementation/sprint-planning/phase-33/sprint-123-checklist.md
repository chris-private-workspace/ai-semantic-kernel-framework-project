# Sprint 123 Checklist: 測試覆蓋率 + 品質衝刺

## 開發任務

### Story 123-1: 測試覆蓋 — Orchestration 模組
- [ ] 建立 `backend/tests/unit/orchestration/` 目錄
- [ ] 編寫 `test_business_intent_router.py`
  - [ ] 測試 Pattern match 優先於 Semantic routing
  - [ ] 測試三層回退鏈（Pattern → Semantic → LLM）
  - [ ] 測試未知意圖返回預設處理
  - [ ] 測試路由快取命中 / 未命中
  - [ ] 測試並發路由請求
- [ ] 編寫 `test_pattern_matcher.py`
  - [ ] 測試規則匹配正確性
  - [ ] 測試優先級排序
  - [ ] 測試正則表達式匹配
  - [ ] 測試空輸入處理
  - [ ] 測試大量規則性能
- [ ] 編寫 `test_semantic_router.py`
  - [ ] 測試向量相似度搜索（Mock embedding）
  - [ ] 測試閾值過濾
  - [ ] 測試 top-k 結果返回
  - [ ] 測試空索引處理
- [ ] 編寫 `test_llm_classifier.py`
  - [ ] 測試分類結果解析
  - [ ] 測試 LLM 返回格式異常處理
  - [ ] 測試 LLM 超時處理
  - [ ] 測試 Mock vs Real LLM 切換
- [ ] 編寫 `test_dialog_manager.py`
  - [ ] 測試多輪對話上下文保持
  - [ ] 測試會話建立和銷毀
  - [ ] 測試會話超時清理
  - [ ] 測試並發會話隔離
- [ ] 建立 `backend/tests/integration/orchestration/` 目錄
- [ ] 編寫 `test_routing_api.py`
  - [ ] 測試路由 API 端點完整流程
  - [ ] 測試不同意圖類型的路由結果
  - [ ] 測試 API 錯誤處理（400, 404, 500）
- [ ] 編寫 `test_execute_with_routing.py`
  - [ ] 測試端到端路由→執行流程
  - [ ] 測試各框架（MAF, Claude SDK, Swarm）路由
  - [ ] 測試執行失敗的錯誤傳播

### Story 123-2: 測試覆蓋 — Auth 模組
- [ ] 建立 `backend/tests/unit/auth/` 目錄
- [ ] 編寫 `test_jwt_middleware.py`
  - [ ] 測試有效 Token 通過驗證
  - [ ] 測試過期 Token 被拒絕（401）
  - [ ] 測試格式錯誤的 Token 被拒絕（401）
  - [ ] 測試缺少 Token 的請求被拒絕（401）
  - [ ] 測試 Token 中的 claims 正確提取
  - [ ] 測試 Token 簽名驗證
- [ ] 編寫 `test_role_based_access.py`
  - [ ] 測試 Admin 角色可訪問管理端點
  - [ ] 測試普通用戶不能訪問管理端點（403）
  - [ ] 測試多角色用戶的權限聚合
  - [ ] 測試未知角色的處理
- [ ] 編寫 `test_rate_limiting.py`
  - [ ] 測試超過限流閾值後返回 429
  - [ ] 測試時間窗口過後限流重置
  - [ ] 測試不同端點的限流配置
  - [ ] 測試白名單 IP 不受限流
- [ ] 編寫 `test_session_management.py`
  - [ ] 測試 Session 建立
  - [ ] 測試 Session 銷毀
  - [ ] 測試 Session 過期自動清理
  - [ ] 測試 Session 資料隔離（多用戶）
- [ ] 建立 `backend/tests/integration/auth/` 目錄
- [ ] 編寫 `test_auth_flow.py`
  - [ ] 測試完整登入流程
  - [ ] 測試登出流程
  - [ ] 測試認證 + 授權組合場景
  - [ ] 測試認證錯誤 response 格式

### Story 123-3: 測試覆蓋 — MCP 模組
- [ ] 建立 `backend/tests/unit/mcp/` 目錄
- [ ] 編寫 `test_permission_check.py`
  - [ ] 測試已授權的工具調用成功
  - [ ] 測試未授權的工具調用被攔截
  - [ ] 測試 Permission pattern 匹配邏輯
  - [ ] 測試角色 + 工具權限矩陣
  - [ ] 測試 Permission check 在每個 MCP server 中被調用
- [ ] 編寫 `test_shell_whitelist.py`
  - [ ] 測試白名單內的命令可執行
  - [ ] 測試白名單外的命令被攔截
  - [ ] 測試命令注入嘗試被攔截（`;`, `|`, `&&`, `` ` `` 等）
  - [ ] 測試路徑遍歷嘗試被攔截（`../`）
  - [ ] 測試白名單動態更新
- [ ] 編寫 `test_tool_execution.py`
  - [ ] 測試工具調用完整生命週期
  - [ ] 測試工具執行超時處理
  - [ ] 測試工具錯誤正確傳播
  - [ ] 測試工具結果格式驗證
  - [ ] 測試並發工具調用
- [ ] 編寫 `test_mcp_server_manager.py`
  - [ ] 測試 MCP server 啟動
  - [ ] 測試 MCP server 停止
  - [ ] 測試 MCP server 健康檢查
  - [ ] 測試 MCP server 重啟
- [ ] 建立 `backend/tests/integration/mcp/` 目錄
- [ ] 編寫 `test_mcp_integration.py`
  - [ ] 測試 MCP 工具調用端到端流程
  - [ ] 測試 Permission 攔截流程
  - [ ] 測試多 MCP server 場景

### Story 123-4: Phase 33 驗證 + 覆蓋率報告
- [ ] 執行完整測試套件
  - [ ] `pytest --cov=src --cov-report=html --cov-report=term-missing --cov-branch -v`
  - [ ] 確認 0 failures
  - [ ] 確認覆蓋率 ≥ 60%
- [ ] 生成覆蓋率報告
  - [ ] HTML 報告（`htmlcov/`）
  - [ ] 文字報告（console output）
  - [ ] 按模組覆蓋率明細
- [ ] Phase 33 驗證項目回顧
  - [ ] InMemory 存儲：`grep -r "InMemory" backend/src/` 確認 0 個殘留
  - [ ] Checkpoint 統一：4 系統全部通過 Registry 運作
  - [ ] ContextSynchronizer：Redis Distributed Lock 驗證
  - [ ] Docker：backend + frontend 映像可 build + run
  - [ ] CI/CD：Pipeline 可自動執行
  - [ ] Azure 部署：App Service 正常運行
  - [ ] OTel：Application Insights 中可見 traces/metrics
  - [ ] 結構化日誌：JSON 格式 + Request ID
- [ ] 差距分析文件
  - [ ] 列出覆蓋率 < 50% 的模組
  - [ ] 分析未覆蓋的原因
  - [ ] 建議 Phase 34 需補強的測試區域
- [ ] 撰寫 Phase 33 驗證報告

## 品質檢查

### 代碼品質
- [ ] 測試代碼遵循專案命名規範（`test_{action}_{scenario}_{expected}`）
- [ ] 測試獨立可執行（不依賴執行順序）
- [ ] 測試使用 fixtures 共享 setup（非重複代碼）
- [ ] Mock 使用合理（不過度 mock 導致測試無意義）
- [ ] 無 `time.sleep()` 在測試中（使用 async await）

### 測試覆蓋率目標
- [ ] 整體覆蓋率 ≥ 60%
- [ ] Orchestration 模組 > 70%
- [ ] Auth 模組 > 80%
- [ ] MCP 模組 > 70%
- [ ] Domain Layer > 60%

### 文檔
- [ ] 覆蓋率報告存檔
- [ ] Phase 33 驗證報告完成
- [ ] 差距分析文件完成
- [ ] Sprint 123 結果記錄

## 驗收標準

- [ ] 整體測試覆蓋率 ≥ 60%
- [ ] 所有測試通過（0 failures, 0 errors）
- [ ] 覆蓋率報告已生成並存檔
- [ ] Phase 33 驗證報告確認所有品質目標達成
- [ ] 差距分析文件完成，為 Phase 34 提供改善方向
- [ ] 團隊內部使用 readiness 確認

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 35
**開始日期**: 待定
