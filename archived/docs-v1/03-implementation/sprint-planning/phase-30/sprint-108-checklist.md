# Sprint 108 Checklist

## Stories

- [ ] **108-1**: AzureSearchClient 封裝
- [ ] **108-2**: EmbeddingService 整合
- [ ] **108-3**: AzureSemanticRouter 實現
- [ ] **108-4**: 整合 BusinessIntentRouter
- [ ] **108-5**: Fallback 機制
- [ ] **108-6**: 單元測試

## 驗收標準

### AzureSearchClient
- [ ] 向量搜索功能正常
- [ ] 混合搜索功能正常
- [ ] CRUD 操作正常
- [ ] 錯誤處理完整

### EmbeddingService
- [ ] Embedding 生成正確
- [ ] 快取機制工作
- [ ] 批量處理支援
- [ ] 錯誤處理完整

### AzureSemanticRouter
- [ ] 語義路由功能正常
- [ ] 閾值過濾正確
- [ ] 結果格式正確
- [ ] 與現有介面相容

### 整合
- [ ] 無縫切換 Azure/內存路由器
- [ ] 三層路由系統正常工作
- [ ] 環境變量控制切換
- [ ] 向後相容

### Fallback
- [ ] 超時處理正確
- [ ] 錯誤降級正常
- [ ] 日誌記錄完整

### 測試
- [ ] 測試覆蓋率 > 85%
- [ ] 所有測試通過

## 交付物

- [ ] `azure_search_client.py`
- [ ] `embedding_service.py`
- [ ] `azure_router.py`
- [ ] `fallback_router.py`
- [ ] 修改 `router.py`
- [ ] 修改 `intent_routes.py`
- [ ] 單元測試文件

## 備註

- Sprint 108 是 Phase 30 的核心實現
- 完成後 AzureSemanticRouter 即可運作
