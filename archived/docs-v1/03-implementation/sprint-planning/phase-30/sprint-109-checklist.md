# Sprint 109 Checklist

## Stories

- [ ] **109-1**: 路由管理 Service
- [ ] **109-2**: 路由管理 API
- [ ] **109-3**: 資料遷移腳本
- [ ] **109-4**: 驗證遷移
- [ ] **109-5**: API 整合測試
- [ ] **109-6**: 文檔更新

## 驗收標準

### RouteManager Service
- [ ] CRUD 操作正常
- [ ] Embedding 自動生成
- [ ] 同步功能正常
- [ ] 錯誤處理完整

### API 端點
- [ ] POST /routes 創建路由
- [ ] GET /routes 列出路由
- [ ] GET /routes/{id} 獲取路由
- [ ] PUT /routes/{id} 更新路由
- [ ] DELETE /routes/{id} 刪除路由
- [ ] POST /routes/sync 同步路由
- [ ] POST /routes/search 測試搜索

### 資料遷移
- [ ] 15 條路由全部遷移
- [ ] Embedding 正確生成
- [ ] 可在 Azure Portal 查看
- [ ] 遷移日誌完整

### 驗證
- [ ] 路由數量正確
- [ ] 欄位完整
- [ ] 搜索功能正常
- [ ] 結果一致

### 測試
- [ ] 整合測試通過
- [ ] 測試覆蓋率 > 85%

## 交付物

- [ ] `route_manager.py`
- [ ] `route_routes.py`
- [ ] `route_schemas.py`
- [ ] `migrate_routes_to_azure.py`
- [ ] `verify_migration.py`
- [ ] 整合測試文件
- [ ] API 參考文檔
- [ ] 使用指南

## 備註

- 遷移前備份現有 routes.py
- 遷移後保留 routes.py 作為 fallback
