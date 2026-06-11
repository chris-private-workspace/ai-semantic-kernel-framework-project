# Sprint 121 Checklist: Checkpoint 統一完成 + CI/CD Pipeline

## 開發任務

### Story 121-1: 完成 4 Checkpoint 系統統一
- [ ] 實現 OrchestrationCheckpointProvider adapter
  - [ ] 分析 Orchestration Checkpoint 的資料結構
  - [ ] 實現 `save_checkpoint()` 方法（資料格式轉換）
  - [ ] 實現 `load_checkpoint()` 方法（資料還原）
  - [ ] 實現 `list_checkpoints()` 方法
  - [ ] 實現 `delete_checkpoint()` 方法
  - [ ] 在 UnifiedCheckpointRegistry 中註冊
  - [ ] 更新 Orchestration 模組的 checkpoint 調用點
  - [ ] 驗證編排流程 checkpoint 正常
- [ ] 實現 WorkflowCheckpointProvider adapter
  - [ ] 分析 Workflow Checkpoint 的資料結構
  - [ ] 實現 save / load / list / delete 方法
  - [ ] 在 Registry 中註冊
  - [ ] 更新 Workflow 模組的 checkpoint 調用點
  - [ ] 驗證工作流 checkpoint 正常
- [ ] 實現 SessionCheckpointProvider adapter
  - [ ] 分析 Session Checkpoint 的資料結構
  - [ ] 實現 save / load / list / delete 方法
  - [ ] 在 Registry 中註冊
  - [ ] 更新 Session 模組的 checkpoint 調用點
  - [ ] 驗證會話 checkpoint 正常
- [ ] 統一驗證
  - [ ] 4 個 Provider 全部註冊成功
  - [ ] `list_all()` 可返回所有系統的 checkpoints
  - [ ] `cleanup_expired()` 可清理所有系統的過期 checkpoints
  - [ ] 各系統獨立運作正常
- [ ] 編寫測試
  - [ ] 各 Provider adapter 單元測試
  - [ ] 多 Provider 併存整合測試
  - [ ] cleanup_expired 跨 Provider 測試
  - [ ] 邊界條件測試（空 checkpoint、大量 checkpoint）

### Story 121-2: Dockerfile 建立
- [ ] Backend Dockerfile
  - [ ] Multi-stage build（builder + production）
  - [ ] Python 3.11-slim 基礎映像
  - [ ] 依賴安裝（pip install）
  - [ ] 非 root 用戶運行
  - [ ] HEALTHCHECK 配置
  - [ ] Gunicorn + Uvicorn workers 啟動命令
  - [ ] 環境變量配置（ENVIRONMENT、PYTHONUNBUFFERED 等）
  - [ ] 本地 build 測試通過
  - [ ] 映像大小 < 500MB
- [ ] Frontend Dockerfile
  - [ ] Multi-stage build（builder + production nginx）
  - [ ] Node 20-alpine 基礎映像
  - [ ] npm ci + npm run build
  - [ ] Nginx 配置檔（SPA routing、gzip、cache headers）
  - [ ] HEALTHCHECK 配置
  - [ ] 本地 build 測試通過
  - [ ] 映像大小 < 100MB
- [ ] .dockerignore（Backend）
  - [ ] 排除 `__pycache__/`、`.git/`、`tests/`、`*.pyc`、`.env`
- [ ] .dockerignore（Frontend）
  - [ ] 排除 `node_modules/`、`.git/`、`dist/`、`.env`
- [ ] docker-compose.prod.yml
  - [ ] Backend service 配置
  - [ ] Frontend service 配置
  - [ ] PostgreSQL service 配置
  - [ ] Redis service 配置
  - [ ] Network 配置
  - [ ] Volume 配置（資料持久化）
  - [ ] Environment variables（從 .env 讀取）
  - [ ] 本地 `docker compose -f docker-compose.prod.yml up` 測試通過
- [ ] Frontend nginx.conf
  - [ ] SPA fallback（所有路由指向 index.html）
  - [ ] Gzip 壓縮
  - [ ] 靜態資源 cache headers
  - [ ] Proxy /api 到 backend

### Story 121-3: CI/CD Pipeline
- [ ] CI Pipeline（`.github/workflows/ci.yml`）
  - [ ] Trigger 配置（push main/feature, PR to main）
  - [ ] Backend test job
    - [ ] Setup Python 3.11
    - [ ] Install dependencies
    - [ ] Black formatting check
    - [ ] isort import check
    - [ ] flake8 linting
    - [ ] mypy type check
    - [ ] pytest with coverage
    - [ ] Upload coverage artifact
  - [ ] Frontend test job
    - [ ] Setup Node 20
    - [ ] npm ci
    - [ ] ESLint check
    - [ ] TypeScript check (tsc --noEmit)
    - [ ] npm run build
  - [ ] Docker build job（depends on test jobs）
    - [ ] Build backend image
    - [ ] Build frontend image
    - [ ] Tag with commit SHA
- [ ] Deploy Pipeline（`.github/workflows/deploy.yml`）
  - [ ] Trigger 配置（main branch only）
  - [ ] Push images to Azure Container Registry (ACR)
  - [ ] Deploy to Azure App Service
  - [ ] Post-deploy health check
  - [ ] 失敗通知（GitHub notification / email）
- [ ] Pipeline 環境變量配置
  - [ ] GitHub Secrets 設定文件
  - [ ] ACR credentials
  - [ ] Azure Service Principal

## 品質檢查

### 代碼品質
- [ ] 類型提示完整（CheckpointProvider adapters）
- [ ] Docstrings 完整
- [ ] Dockerfile 遵循最佳實踐（multi-stage, non-root, .dockerignore）
- [ ] CI/CD YAML 語法正確

### 測試
- [ ] Checkpoint 統一：單元測試覆蓋率 > 85%
- [ ] Dockerfile：本地 build + run 測試通過
- [ ] CI Pipeline：至少手動觸發一次成功

### 安全
- [ ] Dockerfile 不包含敏感資訊
- [ ] CI/CD secrets 使用 GitHub Secrets（不在 YAML 中明文）
- [ ] Docker images 無已知 CVE（建議加入 Trivy 掃描）

## 驗收標準

- [ ] 4 個 Checkpoint 系統全部通過 UnifiedCheckpointRegistry 正常運作
- [ ] Backend + Frontend Docker 映像可成功 build 並啟動
- [ ] docker-compose.prod.yml 可一鍵啟動完整環境
- [ ] CI Pipeline 在 push/PR 時自動執行
- [ ] Deploy Pipeline 可部署到 Azure（或驗證部署配置正確）
- [ ] 所有測試通過

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 40
**開始日期**: 待定
