# Sprint 107 Checklist

## Stories

- [ ] **107-1**: 建立 Azure AI Search 資源
- [ ] **107-2**: 設計索引 Schema
- [ ] **107-3**: 建立索引
- [ ] **107-4**: 配置環境變量
- [ ] **107-5**: 驗證連接

## 驗收標準

### Azure 資源
- [ ] Azure AI Search 服務建立成功
- [ ] 服務端點可存取
- [ ] API Key 取得

### 索引設計
- [ ] index_schema.json 創建
- [ ] 向量搜索配置正確
- [ ] 中文分析器配置

### 環境配置
- [ ] .env.example 更新
- [ ] 本地 .env 配置
- [ ] 敏感資訊安全

### 連接驗證
- [ ] 連接測試通過
- [ ] 索引存在
- [ ] 搜索 API 可用

## 交付物

- [ ] Azure AI Search 服務實例
- [ ] `backend/src/integrations/orchestration/intent_router/semantic_router/index_schema.json`
- [ ] `backend/scripts/create_search_index.py`
- [ ] `backend/scripts/verify_search_connection.py`
- [ ] 更新 `backend/.env.example`

## 備註

- Sprint 107 是 Phase 30 的基礎設施準備
- 完成後即可開始 Sprint 108 的 AzureSemanticRouter 實現
