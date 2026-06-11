# Sprint 121: Checkpoint 統一完成 + CI/CD Pipeline

## 概述

Sprint 121 完成 4 個 Checkpoint 系統的統一遷移（接入 UnifiedCheckpointRegistry），並建立生產級 Dockerfile 和 CI/CD Pipeline，為 Azure 部署做準備。

## 目標

1. 完成 4 個 Checkpoint 系統統一到 UnifiedCheckpointRegistry
2. 建立生產級 Dockerfile（Backend + Frontend），支持 multi-stage builds
3. 建立 CI/CD Pipeline（GitHub Actions 或 Azure DevOps）

## Story Points: 40 點

## 前置條件

- ⬜ Sprint 120 完成（UnifiedCheckpointRegistry 設計完成，第 1 個 Provider 已接入）
- ⬜ InMemory 存儲全部替換完成
- ⬜ GitHub repo 或 Azure DevOps project 可用

## 任務分解

### Story 121-1: 完成 4 Checkpoint 系統統一 (3 天, P1)

**目標**: 將剩餘 3 個 Checkpoint 系統接入 UnifiedCheckpointRegistry，完成全面統一

**交付物**:
- 3 個新的 CheckpointProvider adapter
- 修改各子系統的 checkpoint 調用點
- 遷移驗證測試

**待接入的 Checkpoint 系統**:

| # | 系統 | 難度 | 說明 |
|---|------|------|------|
| 2 | Orchestration Checkpoint | 中 | 編排流程狀態，可能有複雜的巢狀資料 |
| 3 | Workflow Checkpoint | 中 | 工作流步驟狀態，需保持步驟順序 |
| 4 | Session Checkpoint | 低 | 用戶會話狀態，資料結構相對簡單 |

> 第 1 個（Claude SDK Checkpoint）已在 Sprint 120 接入。

**實現方式**:

```python
# 各 Provider Adapter 範例
class OrchestrationCheckpointProvider:
    """Orchestration Checkpoint Provider — 適配 UnifiedCheckpointRegistry"""

    @property
    def provider_name(self) -> str:
        return "orchestration"

    async def save_checkpoint(self, checkpoint_id: str, data: dict, metadata=None):
        # 將原有的 orchestration checkpoint 資料格式
        # 轉換為 UnifiedCheckpointRegistry 的格式
        ...

    async def load_checkpoint(self, checkpoint_id: str):
        # 從 Registry 載入並還原為原有格式
        ...
```

**驗收標準**:
- [ ] 4 個 Checkpoint 系統全部通過 UnifiedCheckpointRegistry 運作
- [ ] 原有各子系統的 checkpoint 行為不變
- [ ] 過期 checkpoint 自動清理功能正常
- [ ] 跨系統 checkpoint 列表查詢正常
- [ ] 單元測試覆蓋率 > 85%
- [ ] 整合測試驗證各系統 save/load 正確

### Story 121-2: Dockerfile 建立 (1.5 天, P0)

**目標**: 建立生產級 Dockerfile，支持 multi-stage builds，確保映像檔安全且輕量

**交付物**:
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `docker-compose.prod.yml`（生產環境 compose）
- `.dockerignore`（前後端各一）

**Backend Dockerfile 設計**:

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim AS production

# 安全：不使用 root 用戶
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

# 從 builder 複製依賴
COPY --from=builder /root/.local /root/.local
COPY . .

# 環境變量
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# 使用 Gunicorn + Uvicorn workers（生產環境）
CMD ["gunicorn", "main:app", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-"]
```

**Frontend Dockerfile 設計**:

```dockerfile
# Stage 1: Builder
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production=false
COPY . .
RUN npm run build

# Stage 2: Production (Nginx)
FROM nginx:alpine AS production

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget -q --spider http://localhost:80 || exit 1

EXPOSE 80
```

**驗收標準**:
- [ ] Backend Dockerfile 可成功 build 並啟動
- [ ] Frontend Dockerfile 可成功 build 並啟動
- [ ] Multi-stage build 確保映像檔輕量（backend < 500MB, frontend < 100MB）
- [ ] 不使用 root 用戶運行
- [ ] Health check 端點正常
- [ ] docker-compose.prod.yml 可一鍵啟動完整環境
- [ ] .dockerignore 排除不必要的檔案

### Story 121-3: CI/CD Pipeline (1.5 天, P0)

**目標**: 建立自動化 CI/CD Pipeline，實現 build → test → deploy 流程

**交付物**:
- `.github/workflows/ci.yml`（或 Azure DevOps pipeline YAML）
- `.github/workflows/deploy.yml`（部署 workflow）

**Pipeline 設計**:

```yaml
# CI Pipeline 架構
name: CI Pipeline

on:
  push:
    branches: [main, feature/*]
  pull_request:
    branches: [main]

jobs:
  # Job 1: Backend 測試
  backend-test:
    - Checkout
    - Setup Python 3.11
    - Install dependencies
    - Run Black (formatting check)
    - Run isort (import check)
    - Run flake8 (linting)
    - Run mypy (type check)
    - Run pytest with coverage
    - Upload coverage report

  # Job 2: Frontend 測試
  frontend-test:
    - Checkout
    - Setup Node 20
    - Install dependencies
    - Run ESLint
    - Run TypeScript check
    - Run tests with coverage
    - Run build

  # Job 3: Docker Build
  docker-build:
    needs: [backend-test, frontend-test]
    - Build backend image
    - Build frontend image
    - Push to container registry (ACR)

  # Job 4: Deploy (main branch only)
  deploy:
    needs: [docker-build]
    if: github.ref == 'refs/heads/main'
    - Deploy to Azure App Service
```

**驗收標準**:
- [ ] Push 到 feature branch 觸發 CI（test only）
- [ ] Push 到 main branch 觸發 CI + CD
- [ ] Backend 測試 job 包含 formatting + linting + type check + pytest
- [ ] Frontend 測試 job 包含 ESLint + TypeScript check + build
- [ ] Docker build job 成功產生映像檔
- [ ] Deploy job 可部署到 Azure App Service
- [ ] Pipeline 失敗時有通知機制
- [ ] 測試覆蓋率報告可在 PR 中查看

## 技術設計

### 新增檔案結構

```
project-root/
├── backend/
│   ├── Dockerfile
│   └── .dockerignore
├── frontend/
│   ├── Dockerfile
│   ├── .dockerignore
│   └── nginx.conf
├── docker-compose.prod.yml
└── .github/
    └── workflows/
        ├── ci.yml
        └── deploy.yml
```

## 依賴

```
# Backend 新增（生產運行）
gunicorn>=21.0

# CI/CD
# GitHub Actions（無額外依賴）
# 或 Azure DevOps Pipeline
```

## 風險

| 風險 | 緩解措施 |
|------|----------|
| Checkpoint 統一導致狀態丟失 | 遷移前備份，新舊並行驗證 |
| Docker build 失敗（依賴問題） | 固定依賴版本，使用 lock file |
| CI Pipeline 超時 | 設定合理 timeout，平行執行 jobs |
| Azure ACR 權限問題 | 提前配置 Service Principal / Managed Identity |

## 完成標準

- [ ] 4 個 Checkpoint 系統全部統一到 UnifiedCheckpointRegistry
- [ ] Backend + Frontend Dockerfile 可成功 build 並運行
- [ ] CI Pipeline 可自動執行 build + test
- [ ] CD Pipeline 可部署到 Azure（或 staging 環境）
- [ ] 所有測試通過

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 40
**開始日期**: 待定
