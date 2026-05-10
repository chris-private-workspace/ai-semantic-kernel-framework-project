# 🚀 情況6: 服務啟動 - 啟動本專案所有開發服務

> **使用時機**: 需要啟動專案開發環境的所有服務
> **目標**: 確保 Docker 服務、Backend、Frontend 全部正常運行
> **適用場景**: 每日開發前、系統重啟後、環境初始化

---

## 📋 Prompt 模板 (給開發人員)

```markdown
請幫我啟動 IPA Platform 的所有開發服務。

執行步驟:
1. 檢查當前服務狀態
2. 啟動所有服務 (Docker → Backend → Frontend)
3. 驗證服務是否正常運行
4. 提供訪問連結

如果有任何服務啟動失敗，請提供排錯建議。
```

---

## 🤖 AI 助手執行步驟

### Step 1: 檢查當前服務狀態

```bash
# 使用統一管理腳本檢查狀態
python scripts/dev.py status
```

### Step 2: 啟動所有服務

```bash
# 方式 A: 一鍵啟動所有服務 (推薦)
python scripts/dev.py start

# 方式 B: 分步驟啟動 (需要時)
python scripts/dev.py start docker     # 1. 先啟動 Docker 服務
python scripts/dev.py start backend    # 2. 再啟動 Backend
python scripts/dev.py start frontend   # 3. 最後啟動 Frontend
```

### Step 3: 驗證服務狀態

```bash
# 再次檢查狀態確認所有服務已啟動
python scripts/dev.py status
```

### Step 4: 生成啟動報告

```markdown
# ✅ 服務啟動報告

## 服務狀態
| 服務 | 狀態 | 端口 |
|------|------|------|
| PostgreSQL | ✅ 運行中 | 5432 |
| Redis | ✅ 運行中 | 6379 |
| RabbitMQ | ✅ 運行中 | 5672/15672 |
| Backend | ✅ 運行中 | 8000 |
| Frontend | ✅ 運行中 | 3005 |

## 訪問連結
- Frontend: http://localhost:3005
- Backend API: http://localhost:8000
- API 文檔: http://localhost:8000/docs
- RabbitMQ 管理界面: http://localhost:15672
```

---

## 📚 服務詳細說明

### Docker 服務 (基礎設施)

| 服務 | 容器名稱 | 端口 | 說明 | 健康檢查 |
|------|----------|------|------|----------|
| **PostgreSQL 16** | ipa-postgres | 5432 | 主資料庫 | `pg_isready` |
| **Redis 7** | ipa-redis | 6379 | 緩存和會話 | `redis-cli ping` |
| **RabbitMQ** | ipa-rabbitmq | 5672, 15672 | 消息隊列 | `rabbitmq-diagnostics ping` |

### 應用服務

| 服務 | 技術 | 端口 | 啟動命令 | PID 檔案位置 |
|------|------|------|----------|--------------|
| **Backend** | FastAPI + Uvicorn | 8000 | `uvicorn main:app --reload` | `.pids/backend_8000.pid` |
| **Frontend** | React + Vite | 3005 | `npm run dev` | `.pids/frontend_3005.pid` |

### 認證（本地開發）

本地開發**不需要 WorkOS 帳號**。`.env` 把 `WORKOS_API_KEY` 留空即可：

- OIDC 路由（`/api/v1/auth/login`、`/callback`）會回 503
- 前端 `/auth/login` 頁面在 `import.meta.env.DEV` 下會顯示「Dev login」表單
- 該表單呼叫 `POST /api/v1/auth/dev-login`（prod 會回 404）→ 自動建立 `dev` tenant + dev user，發 `v2_jwt` cookie（roles `platform_admin`），之後 9 個 active 頁都可進
- 完整 stack 連通煙霧測試：`RUN_CONNECTIVITY=1 npm run test:e2e -- connectivity`（需 backend + frontend 都已啟動）

真正 SSO 只在 staging / prod 需要（填 `WORKOS_API_KEY` / `WORKOS_CLIENT_ID` / `OIDC_REDIRECT_URI` / `FRONTEND_BASE_URL` / `COOKIE_SECURE=true`）。

### 監控服務 (可選)

| 服務 | 端口 | 說明 | 啟動方式 |
|------|------|------|----------|
| **Jaeger** | 16686 | 分散式追蹤 | `--monitoring` flag |
| **Prometheus** | 9090 | 指標收集 | `--monitoring` flag |
| **Grafana** | 3001 | 儀表板 | `--monitoring` flag |

```bash
# 啟動包含監控的完整環境
python scripts/dev.py start docker --monitoring
```

---

## 🔧 統一管理命令速查

### 基本命令

```bash
# 狀態檢查
python scripts/dev.py status

# 啟動服務
python scripts/dev.py start              # 啟動全部
python scripts/dev.py start backend      # 只啟動 Backend
python scripts/dev.py start frontend     # 只啟動 Frontend
python scripts/dev.py start docker       # 只啟動 Docker

# 停止服務
python scripts/dev.py stop               # 停止全部
python scripts/dev.py stop backend       # 只停止 Backend
python scripts/dev.py stop frontend      # 只停止 Frontend
python scripts/dev.py stop docker        # 只停止 Docker

# 重啟服務
python scripts/dev.py restart            # 重啟全部
python scripts/dev.py restart backend    # 重啟 Backend
```

### 日誌查看

```bash
# 查看 Docker 服務日誌
python scripts/dev.py logs postgres      # PostgreSQL 日誌
python scripts/dev.py logs redis         # Redis 日誌
python scripts/dev.py logs rabbitmq      # RabbitMQ 日誌
python scripts/dev.py logs docker -f     # 追蹤所有 Docker 日誌
```

### 進階選項

```bash
# 自定義端口
python scripts/dev.py start backend --backend-port 8001
python scripts/dev.py start frontend --frontend-port 3006

# 啟動監控堆疊
python scripts/dev.py start docker --monitoring

# 前台執行 (用於除錯)
python scripts/dev.py start backend --fg
```

---

## ⚠️ 常見問題排解

### 問題 1: 端口被佔用

**症狀**: `Port 8000 in use` 或 `Address already in use`

**解決方案**:
```bash
# 方案 A: 讓腳本自動處理
python scripts/dev.py restart backend

# 方案 B: 手動終止佔用端口的進程
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti :8000 | xargs kill -9
```

### 問題 2: Docker 服務未啟動

**症狀**: Backend 連接資料庫失敗

**解決方案**:
```bash
# 確認 Docker Desktop 已啟動
docker ps

# 啟動 Docker 服務
python scripts/dev.py start docker

# 等待服務健康檢查通過 (約 10 秒)
docker-compose ps
```

### 問題 3: 前端依賴未安裝

**症狀**: Frontend 啟動失敗，提示 `node_modules` 不存在

**解決方案**:
```bash
cd frontend
npm install
cd ..
python scripts/dev.py start frontend
```

### 問題 4: Python 依賴問題

**症狀**: Backend 啟動失敗，import 錯誤

**解決方案**:
```bash
cd backend
pip install -r requirements.txt
cd ..
python scripts/dev.py start backend
```

### 問題 5: 端口處於 TIME_WAIT 狀態

**症狀**: 端口顯示被佔用但找不到進程

**說明**: Windows 上常見，端口需等待 OS 釋放 (通常 30-60 秒)

**解決方案**:
```bash
# 腳本會自動選擇替代端口 (8001, 8010, 8080, 8100)
python scripts/dev.py start backend
# 查看輸出確認實際使用的端口
```

### 問題 6: uvicorn 熱重載不生效 (Windows)

**症狀**: 修改代碼後服務未自動重啟

**解決方案**:
```bash
# 使用 watchfiles 替代預設 watchgod
pip install watchfiles
python scripts/dev.py restart backend
```

### 問題 7: Python 版本不兼容 (新開發環境)

**症狀**: 系統默認 Python 3.14，但專案需要 Python 3.13

**診斷**:
```bash
# 檢查可用的 Python 版本
py -0p

# 預期輸出類似:
# -V:3.14 *        C:\...\python.exe  (默認，有問題)
# -V:3.13          C:\Program Files\Python313\python.exe (需要)
```

**解決方案**:
```bash
# 方案 A: 使用 py launcher 指定版本
py -3.13 scripts/dev.py start

# 方案 B: 創建並使用 Virtual Environment (推薦)
# 見下方「問題 8: Virtual Environment 設置」
```

### 問題 8: Virtual Environment 設置 (新開發環境)

**症狀**: 需要為專案創建獨立的 Python 環境

**注意**: 在 Git Bash 環境下，`python -m venv` 可能有路徑解析問題

**解決方案**:
```bash
# 步驟 1: 刪除舊的 venv (如存在)
rm -rf backend/venv

# 步驟 2: 使用 Python 腳本創建 venv (避免命令行 bug)
"C:\Program Files\Python313\python.exe" -c "
import venv
builder = venv.EnvBuilder(with_pip=True)
builder.create('C:/path/to/project/backend/venv')
"

# 步驟 3: 安裝依賴
backend/venv/Scripts/pip.exe install -r backend/requirements.txt

# 步驟 4: 使用 venv 中的 Python 啟動
backend/venv/Scripts/python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 問題 9: agent_framework API 變更

**症狀**: ImportError - 類名已更改

**已知變更** (版本 1.0.0b260114):
| 舊名稱 | 新名稱 | 狀態 |
|--------|--------|------|
| `HandoffUserInputRequest` | `HandoffAgentUserRequest` | 已重命名 |
| `GroupChatDirective` | - | 已移除 |
| `ManagerSelectionResponse` | - | 已移除 |

**解決方案**:
```python
# 修改導入語句
# 舊:
from agent_framework import HandoffUserInputRequest

# 新:
from agent_framework import HandoffAgentUserRequest
```

**受影響文件**:
- `backend/src/integrations/agent_framework/builders/handoff.py`
- `backend/src/integrations/agent_framework/builders/groupchat.py`
- `backend/scripts/verify_official_api_usage.py`

### 問題 10: 缺失依賴包

**症狀**: `ModuleNotFoundError` 或 `ImportError`

**常見缺失依賴**:
```bash
# email-validator (pydantic EmailStr 需要)
pip install email-validator

# aiofiles (異步文件操作需要)
pip install aiofiles

# 或一次性安裝
pip install email-validator aiofiles
```

**注意**: 這些依賴已添加到 `requirements.txt`，新安裝應自動包含。

---

## 🔒 環境變數設定

### 必要的 `.env` 檔案

確保專案根目錄有 `.env` 檔案：

```bash
# 複製範例檔案
cp .env.example .env
```

### 關鍵環境變數

```env
# 資料庫
DB_NAME=ipa_platform
DB_USER=ipa_user
DB_PASSWORD=ipa_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis_password

# RabbitMQ
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# Azure OpenAI (Backend 需要)
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

---

## ✅ 驗收標準

服務啟動成功後，AI 助手應確認：

1. **Docker 服務運行中**
   - PostgreSQL: ✅ port 5432
   - Redis: ✅ port 6379
   - RabbitMQ: ✅ port 5672/15672

2. **Backend 可訪問**
   - Health Check: `curl http://localhost:8000/health` 返回 200
   - API 文檔: http://localhost:8000/docs 可正常瀏覽

3. **Frontend 可訪問**
   - 主頁: http://localhost:3005 可正常載入

4. **無錯誤日誌**
   - Backend 控制台無紅色錯誤
   - Docker 日誌無異常

---

## 📊 服務啟動順序說明

```
┌─────────────────────────────────────────────────────────────┐
│                    服務啟動順序圖                            │
└─────────────────────────────────────────────────────────────┘

  1. Docker Services (基礎設施層)
     ┌──────────┐   ┌──────────┐   ┌──────────┐
     │PostgreSQL│   │  Redis   │   │ RabbitMQ │
     │  :5432   │   │  :6379   │   │  :5672   │
     └────┬─────┘   └────┬─────┘   └────┬─────┘
          │              │              │
          └──────────────┼──────────────┘
                         │
                         ▼ (等待 5 秒，確保健康檢查通過)
  2. Backend (應用層)
     ┌─────────────────────────────────────────┐
     │          FastAPI + Uvicorn              │
     │              :8000                       │
     │  ┌─────────────────────────────────┐   │
     │  │ 連接: PostgreSQL, Redis, RabbitMQ │   │
     │  └─────────────────────────────────┘   │
     └─────────────────┬───────────────────────┘
                       │
                       ▼
  3. Frontend (展示層)
     ┌─────────────────────────────────────────┐
     │          React + Vite                   │
     │              :3005                       │
     │  ┌─────────────────────────────────┐   │
     │  │     API 請求 → Backend :8000     │   │
     │  └─────────────────────────────────┘   │
     └─────────────────────────────────────────┘
```

**為什麼要按順序啟動？**
- Backend 需要 Docker 服務 (DB, Cache, Queue) 先就緒
- Frontend 可獨立運行，但 API 調用需要 Backend

---

## 🔗 相關文檔

### 新開發環境
如果您是在**新環境**首次設置，或遇到以下問題：
- bcrypt/passlib 版本衝突
- 資料庫 Schema 不同步
- Alembic 遷移失敗

請參考 **[情況7: 新開發環境設置](./SITUATION-7-NEW-ENV-SETUP.md)**

### 開發流程指引
- [情況1: 專案入門](./SITUATION-1-PROJECT-ONBOARDING.md) - 新開發者了解專案
- [情況2: 開發前準備](./SITUATION-2-FEATURE-DEV-PREP.md) - 開始開發任務前
- [情況5: 保存進度](./SITUATION-5-SAVE-PROGRESS.md) - 提交代碼
- [情況7: 新開發環境設置](./SITUATION-7-NEW-ENV-SETUP.md) - 完整環境初始化

### 技術文檔
- [CLAUDE.md](../../../CLAUDE.md) - 專案總覽和開發指南
- [docker-compose.yml](../../../docker-compose.yml) - Docker 服務配置
- [scripts/dev.py](../../../scripts/dev.py) - 統一環境管理腳本

---

## 📝 快速啟動檢查清單

開發前請確認：

- [ ] Docker Desktop 已啟動
- [ ] `.env` 檔案已設定
- [ ] Python 虛擬環境已啟用 (如使用)
- [ ] Node.js 和 npm 已安裝
- [ ] 網路連接正常 (首次啟動需下載 Docker images)

然後執行：

```bash
python scripts/dev.py start
```

---

**維護者**: AI 助手 + 開發團隊
**最後更新**: 2026-01-16
**版本**: 1.1 (新增問題 7-10: 新開發環境問題排解)
