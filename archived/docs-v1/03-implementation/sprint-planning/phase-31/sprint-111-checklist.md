# Sprint 111 Checklist: Quick Wins + Auth Foundation

## 開發任務

### Story 111-1: CORS Origin 修復
- [ ] 搜索 `backend/src/core/config.py` 中的 CORS_ORIGINS 配置
- [ ] 將 `http://localhost:3000` 修改為 `http://localhost:3005`
- [ ] 搜索其他文件是否有引用 port 3000 的 CORS 配置
- [ ] 確認 CORS middleware 正確套用新的 origin

### Story 111-2: Vite Proxy 修復
- [ ] 開啟 `frontend/vite.config.ts`
- [ ] 找到 proxy 配置的 target 設定
- [ ] 將 `http://localhost:8010` 修改為 `http://localhost:8000`
- [ ] 確認所有 proxy 路徑的 target 一致

### Story 111-3: JWT Secret 環境變量化
- [ ] 搜索 `backend/` 下所有硬編碼 JWT secret 字串
- [ ] 記錄 3 處硬編碼位置
- [ ] 在 `backend/src/core/config.py` 新增 `JWT_SECRET` 環境變量讀取
- [ ] 修改第 1 處硬編碼 → `settings.JWT_SECRET`
- [ ] 修改第 2 處硬編碼 → `settings.JWT_SECRET`
- [ ] 修改第 3 處硬編碼 → `settings.JWT_SECRET`
- [ ] 定義 `UNSAFE_SECRETS` 列表
- [ ] 實現啟動時不安全值 WARNING 檢查
- [ ] 在 `.env.example` 中添加 `JWT_SECRET` 說明
- [ ] 在 `.env` 中設定安全的 JWT_SECRET 值

### Story 111-4: authStore console.log 清理
- [ ] 開啟 `frontend/src/stores/authStore.ts`
- [ ] 找到第 1 個 console.log — 移除
- [ ] 找到第 2 個 console.log — 移除
- [ ] 找到第 3 個 console.log — 移除
- [ ] 找到第 4 個 console.log — 移除
- [ ] 找到第 5 個 console.log — 移除
- [ ] 確認 console.error 語句未被移除
- [ ] 確認移除後 authStore 功能正常

### Story 111-5: Docker 預設憑證修復
- [ ] 搜索 `docker-compose.yml` 中的 `admin123` 或類似弱密碼
- [ ] 搜索 docker-compose override 文件中的弱密碼
- [ ] 將 Grafana admin 密碼改為環境變量 `${GRAFANA_ADMIN_PASSWORD}`
- [ ] 將 n8n admin 密碼改為環境變量（若存在）
- [ ] 設定 fallback 預設值 `please-change-me`
- [ ] 在 `.env.example` 中添加密碼模板

### Story 111-6: Uvicorn reload 環境感知
- [ ] 開啟 `backend/main.py` 或 Uvicorn 啟動配置
- [ ] 找到 `reload=True` 硬編碼位置
- [ ] 新增 `ENVIRONMENT` 環境變量讀取
- [ ] 修改 reload 為 `reload=(env == "development")`
- [ ] 確認 production 環境下 reload=False
- [ ] 在 `.env.example` 中添加 `ENVIRONMENT` 說明

### Story 111-7: 全局 Auth Middleware
- [ ] **Phase 1: 核心驗證函數**
  - [ ] 確認 `backend/src/core/auth.py` 存在或新建
  - [ ] 實現 `HTTPBearer` security scheme
  - [ ] 實現 `get_current_user()` 依賴函數
  - [ ] 實現 JWT decode 邏輯 (HS256)
  - [ ] 實現用戶資訊提取 (user_id, email)
  - [ ] 實現異常處理 (401 Unauthorized)
  - [ ] 編寫 get_current_user 單元測試
- [ ] **Phase 2: 白名單路由定義**
  - [ ] 定義 PUBLIC_ROUTES 列表
  - [ ] 包含 `/api/v1/health`
  - [ ] 包含 `/api/v1/auth/login`
  - [ ] 包含 `/api/v1/auth/register`
  - [ ] 包含 `/docs`, `/redoc`, `/openapi.json`
- [ ] **Phase 3: 全局注入**
  - [ ] 修改 `backend/src/api/v1/__init__.py`
  - [ ] 建立 protected_router (帶 Depends)
  - [ ] 建立 public_router (無 Depends)
  - [ ] 將 39 個 route 模組分配到正確的 router
  - [ ] 驗證現有 38 個已有 auth 的端點不受影響
- [ ] **Phase 4: 端到端驗證**
  - [ ] 未帶 Token 的請求返回 401
  - [ ] 帶有效 Token 的請求正常通過
  - [ ] Token 過期返回 401
  - [ ] 白名單路由無需 Token
  - [ ] 前端 AuthInterceptor 正確帶 Authorization header

### Story 111-8: Sessions 偽認證修復
- [ ] 搜索 `get_current_user_id` 函數定義位置
- [ ] 確認硬編碼 UUID 值
- [ ] 將返回值改為從 JWT Token 中提取 user_id
- [ ] 添加 `Depends(get_current_user)` 參數
- [ ] 搜索所有調用 `get_current_user_id` 的端點
- [ ] 確認所有調用點兼容新的 async 簽名
- [ ] 編寫用戶隔離測試（不同用戶看不到彼此的 session）
- [ ] 確認 session 創建時記錄真實 user_id

### Story 111-9: Rate Limiting
- [ ] 添加 `slowapi>=0.1.9` 到 `requirements.txt`
- [ ] 安裝 slowapi
- [ ] 創建 `backend/src/middleware/rate_limit.py`
- [ ] 實現 Limiter 初始化 (key_func=get_remote_address)
- [ ] 實現 setup_rate_limiting() 函數
- [ ] 在 `backend/main.py` 中調用 setup_rate_limiting()
- [ ] 設定全局預設限制 (100 req/min)
- [ ] 設定登入端點限制 (10 req/min)
- [ ] 設定敏感操作限制 (30 req/min)
- [ ] 實現 development 環境放寬邏輯
- [ ] 驗證超過限制返回 429

## 品質檢查

### 代碼品質
- [ ] Black 格式化通過 (backend)
- [ ] isort 排序通過 (backend)
- [ ] flake8 檢查通過 (backend)
- [ ] mypy 類型檢查通過 (backend)
- [ ] ESLint 檢查通過 (frontend)
- [ ] Prettier 格式化通過 (frontend)

### 測試
- [ ] Auth Middleware 單元測試通過
- [ ] JWT 驗證單元測試通過
- [ ] Rate Limiting 單元測試通過
- [ ] 現有測試套件全部通過（無回歸）
- [ ] 前端→後端 端到端請求測試通過

### 安全檢查
- [ ] 無硬編碼 secret/密碼
- [ ] 無 console.log 洩漏 PII
- [ ] CORS origin 正確
- [ ] JWT Secret 從環境變量讀取
- [ ] Docker 無預設弱密碼

## 驗收標準

- [ ] CORS origin = http://localhost:3005
- [ ] Vite proxy target = http://localhost:8000
- [ ] JWT Secret 硬編碼處 = 0
- [ ] authStore console.log = 0 個
- [ ] Docker 弱密碼 = 0 個
- [ ] Uvicorn reload 僅 development 啟用
- [ ] Auth 覆蓋率 = 100% (528/528)
- [ ] Sessions 使用真實 JWT user_id
- [ ] Rate Limiting 429 可觸發
- [ ] 全部現有測試通過

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 40
**開始日期**: TBD
