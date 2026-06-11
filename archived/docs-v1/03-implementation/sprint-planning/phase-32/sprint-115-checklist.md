# Sprint 115 Checklist: SemanticRouter Real 實現

## 開發任務

### Story 115-1: Azure AI Search 資源建立 + semantic-routes 索引
- [ ] 登入 Azure Portal 建立 Azure AI Search 服務
  - [ ] 名稱: `ipa-semantic-search`
  - [ ] 區域: East US 2
  - [ ] 定價層: Basic
- [ ] 取得 Endpoint URL 和管理 API Key
- [ ] 創建 `index_schema.json`
  - [ ] 定義 id (key field)
  - [ ] 定義 route_name, category, sub_intent (filterable)
  - [ ] 定義 utterance (searchable)
  - [ ] 定義 utterance_vector (1536 dimensions, HNSW)
  - [ ] 定義 workflow_type, risk_level (filterable)
  - [ ] 定義 description (searchable)
  - [ ] 定義 enabled (filterable)
  - [ ] 定義 created_at, updated_at (sortable)
  - [ ] 配置 vectorSearch algorithms (HNSW)
  - [ ] 配置 vectorSearch profiles
- [ ] 創建 `setup_index.py`
  - [ ] 讀取 index_schema.json
  - [ ] 建立或更新索引
  - [ ] 冪等執行（已存在不報錯）
  - [ ] 驗證索引建立成功
- [ ] 更新 `backend/.env.example`
  - [ ] 新增 AZURE_SEARCH_ENDPOINT
  - [ ] 新增 AZURE_SEARCH_API_KEY
  - [ ] 新增 AZURE_SEARCH_INDEX_NAME
  - [ ] 新增 USE_AZURE_SEARCH
  - [ ] 新增 SEMANTIC_SIMILARITY_THRESHOLD
  - [ ] 新增 SEMANTIC_TOP_K
- [ ] 創建連接驗證測試

### Story 115-2: AzureSemanticRouter 實現
- [ ] 創建 `azure_search_client.py`
  - [ ] 實現 `AzureSearchClient` 類
  - [ ] 實現 `vector_search()` — 純向量搜索
  - [ ] 實現 `hybrid_search()` — 混合搜索（向量 + 文字）
  - [ ] 實現 `upload_documents()` — 文檔上傳
  - [ ] 實現 `delete_documents()` — 文檔刪除
  - [ ] 實現 `get_document()` — 單筆查詢
  - [ ] 實現連接池和重試邏輯
  - [ ] 實現 timeout 配置
- [ ] 創建 `embedding_service.py`
  - [ ] 實現 `EmbeddingService` 類
  - [ ] 實現 `get_embedding()` — 單筆向量生成
  - [ ] 實現 `get_embeddings_batch()` — 批次向量生成
  - [ ] 實現 embedding 快取（LRU cache）
  - [ ] 錯誤處理（API 限流、逾時）
- [ ] 創建 `azure_semantic_router.py`
  - [ ] 實現 `AzureSemanticRouter` 類
  - [ ] 實現 `route()` — 主路由方法
  - [ ] 實現 `route_with_scores()` — 帶分數的路由
  - [ ] 實現 similarity_threshold 過濾
  - [ ] 實現結果排序和格式化
- [ ] 修改 `BusinessIntentRouter` Layer 2 初始化
  - [ ] 判斷 `USE_AZURE_SEARCH` 環境變量
  - [ ] True: 初始化 `AzureSemanticRouter`
  - [ ] False: 使用原有 Mock `SemanticRouter`
  - [ ] Fallback 機制（Azure 異常時降級到 Mock）
- [ ] 創建 `backend/tests/unit/orchestration/test_azure_semantic_router.py`
  - [ ] 測試向量搜索（Mock Azure 服務）
  - [ ] 測試混合搜索
  - [ ] 測試 similarity 閾值過濾
  - [ ] 測試結果排序
  - [ ] 測試 fallback 機制
- [ ] 創建 `backend/tests/unit/orchestration/test_embedding_service.py`
  - [ ] 測試單筆 embedding 生成
  - [ ] 測試批次 embedding 生成
  - [ ] 測試快取命中
  - [ ] 測試錯誤處理

### Story 115-3: 路由管理 API + 資料遷移
- [ ] 創建 `route_manager.py`
  - [ ] 實現 `RouteManager` 類
  - [ ] 實現 `create_route()` — 新增路由（含 embedding 生成）
  - [ ] 實現 `get_routes()` — 列出路由（支持過濾）
  - [ ] 實現 `get_route()` — 取得單筆
  - [ ] 實現 `update_route()` — 更新路由（重新生成 embedding）
  - [ ] 實現 `delete_route()` — 刪除路由
  - [ ] 實現 `sync_from_yaml()` — YAML 同步到 Azure
  - [ ] 實現 `search_test()` — 搜索測試
- [ ] 創建 `backend/src/api/v1/orchestration/routes.py`
  - [ ] `POST /api/v1/orchestration/routes` — 新增
  - [ ] `GET /api/v1/orchestration/routes` — 列出
  - [ ] `PUT /api/v1/orchestration/routes/{id}` — 更新
  - [ ] `DELETE /api/v1/orchestration/routes/{id}` — 刪除
  - [ ] `POST /api/v1/orchestration/routes/sync` — 同步
  - [ ] `POST /api/v1/orchestration/routes/search` — 搜索測試
  - [ ] 在主 router 中註冊
- [ ] 創建 `migration.py`
  - [ ] 讀取現有 routes.yaml（15 條路由，56 utterances）
  - [ ] 批次生成 embedding 向量
  - [ ] 上傳到 Azure AI Search
  - [ ] 驗證遷移完整性（數量比對）
  - [ ] 搜索結果比對（Top-5 一致性）
- [ ] 創建 `backend/tests/unit/orchestration/test_route_manager.py`
  - [ ] 測試 CRUD 操作
  - [ ] 測試 YAML 同步
  - [ ] 測試搜索測試功能
- [ ] 創建 `backend/tests/integration/orchestration/test_route_api.py`
  - [ ] 測試 6 個 API 端點
  - [ ] 測試完整 CRUD 流程
  - [ ] 測試錯誤場景

## 品質檢查

### 代碼品質
- [ ] 類型提示完整
- [ ] Docstrings 完整
- [ ] 遵循專案代碼風格
- [ ] 模組導出正確
- [ ] 無硬編碼金鑰（全部從環境變量讀取）

### 測試
- [ ] 單元測試覆蓋率 > 90%
- [ ] 整合測試創建且通過
- [ ] Mock Azure 服務正確設置
- [ ] 遷移腳本可重複執行

### 性能
- [ ] 搜索延遲 < 100ms (P95)
- [ ] Embedding 快取命中率 > 50%
- [ ] 批次操作效率驗證

### 安全
- [ ] Azure API Key 從環境變量讀取
- [ ] 不在日誌中輸出 API Key
- [ ] 路由管理 API 有認證保護

## 驗收標準

- [ ] Azure AI Search 資源和索引建立成功
- [ ] AzureSemanticRouter 正常運作，替代 Mock
- [ ] 15 條路由成功遷移到 Azure AI Search
- [ ] 6 個路由管理 API 端點全部可用
- [ ] 搜索延遲 < 100ms (P95)
- [ ] Fallback 機制正常（Azure 不可用時降級到 Mock）
- [ ] 所有測試通過

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 45
**開始日期**: TBD
