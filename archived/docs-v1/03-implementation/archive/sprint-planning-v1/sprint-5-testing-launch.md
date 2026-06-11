# Sprint 5: Testing & Launch - 詳細規劃

**版本**: 1.0  
**創建日期**: 2025-11-19  
**Sprint 期間**: 2026-02-03 至 2026-02-14 (2週)  
**團隊規模**: 8人

---

## 📋 Sprint 目標

完成全面測試、性能優化、文檔編寫，為生產環境部署做準備。

### 核心目標
1. ✅ 完整的集成測試套件
2. ✅ 負載測試和性能優化
3. ✅ Bug 修復和穩定性提升
4. ✅ 用戶文檔和 API 文檔
5. ✅ UAT 準備和執行
6. ✅ 生產環境部署

### 成功標準
- 所有 P0/P1 Bug 修復
- 性能指標達標（P95 < 5s）
- 負載測試通過（50+ 並發）
- 文檔完整
- UAT 通過

---

## 📊 Story Points 分配

**總計劃點數**: 35

**按優先級分配**:
- P0 (Critical): 26 點 (74%)
- P1 (High): 9 點 (26%)

---

## 🎯 Sprint Backlog

### S5-1: Integration Testing Suite
**Story Points**: 8  
**優先級**: P0 - Critical  
**負責人**: QA Engineer  
**依賴**: 所有 Sprint 1-4 功能

#### 描述

創建完整的集成測試套件，覆蓋所有服務間交互。

#### 驗收標準
- [ ] 測試覆蓋所有 API endpoints
- [ ] 測試工作流完整生命週期
- [ ] 測試 n8n 和 Teams 集成
- [ ] 測試錯誤處理和重試
- [ ] 測試覆蓋率 ≥ 80%

#### 技術實現細節

**1. 集成測試結構**

```
tests/
├── integration/
│   ├── test_workflow_lifecycle.py
│   ├── test_execution_flow.py
│   ├── test_n8n_integration.py
│   ├── test_teams_integration.py
│   ├── test_rbac.py
│   └── test_error_handling.py
└── conftest.py
```

**2. 工作流生命週期測試**

```python
# tests/integration/test_workflow_lifecycle.py
import pytest
from fastapi.testclient import TestClient

def test_complete_workflow_lifecycle(client: TestClient, db, test_user):
    """測試從創建到執行的完整流程"""
    
    # 1. 創建工作流
    workflow_data = {
        "name": "Test Workflow",
        "description": "Integration test workflow",
        "trigger_type": "manual",
        "steps": [
            {
                "order": 1,
                "type": "agent",
                "agent_id": "test-agent-id",
                "config": {
                    "prompt": "Analyze the data",
                    "max_tokens": 500
                }
            }
        ]
    }
    
    response = client.post(
        "/api/workflows/",
        json=workflow_data,
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    assert response.status_code == 201
    workflow_id = response.json()["id"]
    
    # 2. 獲取工作流
    response = client.get(
        f"/api/workflows/{workflow_id}",
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Workflow"
    
    # 3. 執行工作流
    response = client.post(
        f"/api/workflows/{workflow_id}/execute",
        json={"input_data": {"test": "data"}},
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    assert response.status_code == 201
    execution_id = response.json()["id"]
    
    # 4. 檢查執行狀態
    import time
    time.sleep(2)  # 等待執行開始
    
    response = client.get(
        f"/api/executions/{execution_id}",
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] in ["running", "completed"]
    
    # 5. 刪除工作流
    response = client.delete(
        f"/api/workflows/{workflow_id}",
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    assert response.status_code == 200
```

**3. n8n 集成測試**

```python
# tests/integration/test_n8n_integration.py
import hmac
import hashlib
import json

def test_n8n_webhook_with_valid_signature(client, db, test_workflow):
    """測試 n8n webhook 驗證"""
    
    payload = {
        "workflow_id": test_workflow.id,
        "data": {"test": "value"}
    }
    payload_bytes = json.dumps(payload).encode('utf-8')
    
    # 生成有效簽名
    secret = "test-secret-key"
    signature = hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    response = client.post(
        f"/api/webhooks/n8n/{test_workflow.id}",
        json=payload,
        headers={"X-N8n-Signature": signature}
    )
    
    assert response.status_code == 200
    assert "execution_id" in response.json()

def test_n8n_webhook_with_invalid_signature(client, db, test_workflow):
    """測試無效簽名被拒絕"""
    
    response = client.post(
        f"/api/webhooks/n8n/{test_workflow.id}",
        json={"data": "test"},
        headers={"X-N8n-Signature": "invalid-signature"}
    )
    
    assert response.status_code == 401
```

**4. RBAC 測試**

```python
# tests/integration/test_rbac.py
def test_admin_can_access_admin_api(client, admin_user):
    """管理員可以訪問管理 API"""
    response = client.get(
        "/api/admin/statistics/overview",
        headers={"Authorization": f"Bearer {admin_user.token}"}
    )
    assert response.status_code == 200

def test_regular_user_cannot_access_admin_api(client, regular_user):
    """普通用戶不能訪問管理 API"""
    response = client.get(
        "/api/admin/statistics/overview",
        headers={"Authorization": f"Bearer {regular_user.token}"}
    )
    assert response.status_code == 403

def test_user_can_only_delete_own_workflows(client, db, user1, user2, workflow_owned_by_user1):
    """用戶只能刪除自己的工作流"""
    # user2 嘗試刪除 user1 的工作流
    response = client.delete(
        f"/api/workflows/{workflow_owned_by_user1.id}",
        headers={"Authorization": f"Bearer {user2.token}"}
    )
    assert response.status_code == 403
```

#### 子任務

1. [ ] 設計測試場景
2. [ ] 編寫工作流生命週期測試
3. [ ] 編寫執行流程測試
4. [ ] 編寫集成測試（n8n, Teams）
5. [ ] 編寫 RBAC 測試
6. [ ] 編寫錯誤處理測試
7. [ ] 生成測試覆蓋率報告

---

### S5-2: Load Testing (k6)
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: QA Engineer + DevOps  
**依賴**: S5-3 (性能優化前的基線測試)

#### 描述

使用 k6 進行負載測試，驗證系統在高負載下的表現。

#### 驗收標準
- [ ] 支持 50+ 並發用戶
- [ ] API P95 延遲 < 5s
- [ ] 錯誤率 < 1%
- [ ] 吞吐量 ≥ 100 RPS
- [ ] 無內存泄漏

#### 技術實現細節

**1. 安裝 k6**

```bash
# macOS
brew install k6

# Windows
choco install k6

# Docker
docker pull grafana/k6
```

**2. 負載測試腳本**

```javascript
// tests/load/workflow_execution.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 10 },  // 緩慢爬升到 10 用戶
    { duration: '5m', target: 50 },  // 爬升到 50 用戶
    { duration: '10m', target: 50 }, // 維持 50 用戶 10 分鐘
    { duration: '2m', target: 0 },   // 緩慢降至 0
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'], // P95 < 5s
    http_req_failed: ['rate<0.01'],    // 錯誤率 < 1%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const TOKEN = __ENV.API_TOKEN;

export function setup() {
  // 登錄獲取 token
  const loginRes = http.post(`${BASE_URL}/api/auth/login`, JSON.stringify({
    email: 'test@example.com',
    password: 'password123'
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  return { token: loginRes.json('access_token') };
}

export default function (data) {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${data.token}`,
  };
  
  // 1. 創建工作流
  let createRes = http.post(
    `${BASE_URL}/api/workflows/`,
    JSON.stringify({
      name: `Load Test Workflow ${__VU}`,
      trigger_type: 'manual',
      steps: [
        {
          order: 1,
          type: 'agent',
          agent_id: 'test-agent',
          config: { prompt: 'Hello' }
        }
      ]
    }),
    { headers }
  );
  
  check(createRes, {
    'workflow created': (r) => r.status === 201,
  });
  
  const workflowId = createRes.json('id');
  
  // 2. 執行工作流
  let executeRes = http.post(
    `${BASE_URL}/api/workflows/${workflowId}/execute`,
    JSON.stringify({ input_data: {} }),
    { headers }
  );
  
  check(executeRes, {
    'execution started': (r) => r.status === 201,
  });
  
  // 3. 查詢執行狀態
  let executionId = executeRes.json('id');
  let statusRes = http.get(
    `${BASE_URL}/api/executions/${executionId}`,
    { headers }
  );
  
  check(statusRes, {
    'execution status retrieved': (r) => r.status === 200,
  });
  
  sleep(1);
}

export function teardown(data) {
  // 清理測試數據（可選）
}
```

**3. 運行負載測試**

```bash
# 本地運行
k6 run tests/load/workflow_execution.js

# Docker 運行
docker run -i grafana/k6 run - <tests/load/workflow_execution.js

# 使用環境變量
k6 run --env BASE_URL=https://staging.ipa-platform.com tests/load/workflow_execution.js

# 輸出結果到 InfluxDB + Grafana
k6 run --out influxdb=http://localhost:8086/k6 tests/load/workflow_execution.js
```

#### 子任務

1. [ ] 安裝和配置 k6
2. [ ] 編寫負載測試腳本
3. [ ] 運行基線測試（優化前）
4. [ ] 分析瓶頸
5. [ ] 優化後重新測試
6. [ ] 生成測試報告

---

### S5-3: Performance Optimization
**Story Points**: 8  
**優先級**: P0 - Critical  
**負責人**: Backend Team  
**依賴**: S5-2 (基線測試結果)

#### 描述

根據負載測試結果，優化數據庫查詢、緩存策略、API 性能。

#### 驗收標準
- [ ] API P95 延遲 < 5s
- [ ] 數據庫查詢優化（索引、N+1 問題）
- [ ] Redis 緩存命中率 ≥ 60%
- [ ] 前端資源優化（代碼分割、懶加載）

#### 技術實現細節

**1. 數據庫查詢優化**

```python
# ❌ N+1 問題
workflows = db.query(Workflow).all()
for workflow in workflows:
    print(workflow.creator.name)  # 每次都查詢數據庫

# ✅ 使用 joinedload 預加載
from sqlalchemy.orm import joinedload

workflows = db.query(Workflow).options(
    joinedload(Workflow.creator)
).all()
for workflow in workflows:
    print(workflow.creator.name)  # 不觸發額外查詢
```

**2. 添加數據庫索引**

```python
# alembic migration
def upgrade():
    op.create_index('idx_workflow_created_by', 'workflows', ['created_by'])
    op.create_index('idx_execution_workflow_id', 'executions', ['workflow_id'])
    op.create_index('idx_execution_status', 'executions', ['status'])
    op.create_index('idx_audit_log_user_time', 'audit_logs', ['user_id', 'timestamp'])
```

**3. Redis 緩存策略**

```python
# app/core/cache.py
from functools import wraps
import json
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache(expire=300):
    """緩存裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成緩存 key
            cache_key = f"{func.__name__}:{json.dumps(kwargs)}"
            
            # 檢查緩存
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # 執行函數
            result = await func(*args, **kwargs)
            
            # 存入緩存
            redis_client.setex(
                cache_key,
                expire,
                json.dumps(result)
            )
            
            return result
        return wrapper
    return decorator

# 使用
@router.get("/api/workflows/")
@cache(expire=60)  # 緩存 1 分鐘
async def list_workflows(db: Session = Depends(get_db)):
    return db.query(Workflow).all()
```

**4. 前端性能優化**

```typescript
// 代碼分割（Lazy Loading）
import { lazy, Suspense } from 'react';

const WorkflowEditor = lazy(() => import('./features/workflows/WorkflowEditor'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <WorkflowEditor />
    </Suspense>
  );
}

// Vite 配置優化
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@radix-ui/react-dialog', '@radix-ui/react-slot'],
          'chart-vendor': ['recharts'],
        },
      },
    },
  },
});
```

#### 子任務

1. [ ] 分析負載測試瓶頸
2. [ ] 優化數據庫查詢（N+1、索引）
3. [ ] 實現 Redis 緩存
4. [ ] 優化前端資源加載
5. [ ] 重新運行負載測試
6. [ ] 驗證性能指標達標

---

### S5-4: Bug Fixing Sprint
**Story Points**: 8  
**優先級**: P0 - Critical  
**負責人**: 全員  
**依賴**: S5-1 (測試發現的 Bug)

#### 描述

修復所有測試階段發現的 Bug，優先處理 P0/P1。

#### 驗收標準
- [ ] 所有 P0 Bug 修復
- [ ] 所有 P1 Bug 修復
- [ ] P2/P3 Bug 分類（可延後到 Phase 2）
- [ ] 回歸測試通過

---

### S5-5: User Documentation
**Story Points**: 5  
**優先級**: P1 - High  
**負責人**: Product Owner + Backend Lead  
**依賴**: 所有功能完成

#### 描述

編寫用戶手冊、API 文檔、管理員指南。

#### 驗收標準
- [ ] 用戶快速入門指南
- [ ] 工作流創建教程
- [ ] API 文檔（OpenAPI/Swagger）
- [ ] 管理員操作手冊
- [ ] 故障排除指南

#### 技術實現細節

**1. 文檔結構**

```
docs/
├── user-guide/
│   ├── getting-started.md
│   ├── creating-workflows.md
│   ├── executing-workflows.md
│   └── monitoring.md
├── admin-guide/
│   ├── installation.md
│   ├── configuration.md
│   ├── user-management.md
│   └── troubleshooting.md
└── api/
    └── openapi.yaml
```

**2. API 文檔自動生成**

```python
# main.py
from fastapi.openapi.docs import get_swagger_ui_html

app = FastAPI(
    title="IPA Platform API",
    description="Intelligent Process Automation Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# 自動生成 OpenAPI schema
@app.get("/api/openapi.json")
async def get_openapi():
    return app.openapi()
```

#### 子任務

1. [ ] 編寫用戶快速入門指南
2. [ ] 編寫工作流創建教程
3. [ ] 生成 API 文檔
4. [ ] 編寫管理員手冊
5. [ ] 編寫故障排除指南
6. [ ] 審查和發布文檔

---

### S5-6: Deployment Runbook
**Story Points**: 3  
**優先級**: P0 - Critical  
**負責人**: DevOps Engineer  
**依賴**: S0-3 (CI/CD Pipeline)

#### 描述

創建生產環境部署檢查清單和回滾程序。

#### 驗收標準
- [ ] 部署前檢查清單
- [ ] 部署步驟文檔
- [ ] 回滾程序
- [ ] 監控和告警配置
- [ ] 災難恢復計劃

#### 技術實現細節

**部署檢查清單**:

```markdown
## Pre-Deployment Checklist

### Infrastructure
- [ ] Kubernetes cluster healthy
- [ ] Database backup completed
- [ ] Redis cluster running
- [ ] RabbitMQ healthy

### Configuration
- [ ] Environment variables set
- [ ] Azure Key Vault accessible
- [ ] SSL certificates valid
- [ ] DNS records configured

### Testing
- [ ] All tests passed in staging
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] UAT approved

### Monitoring
- [ ] Prometheus scraping endpoints
- [ ] Grafana dashboards configured
- [ ] AlertManager rules active
- [ ] Log aggregation working

### Rollback Plan
- [ ] Previous version image available
- [ ] Database migration reversible
- [ ] Rollback procedure tested
```

---

### S5-7: UAT Preparation
**Story Points**: 5  
**優先級**: P1 - High  
**負責人**: Product Owner + QA  
**依賴**: 所有功能完成

#### 描述

準備用戶驗收測試環境，培訓用戶，收集反饋。

#### 驗收標準
- [ ] UAT 環境部署
- [ ] 測試場景準備
- [ ] 用戶培訓完成
- [ ] UAT 反饋收集
- [ ] UAT sign-off

---

## 📈 Sprint 5 Metrics

### Velocity Tracking
- **計劃點數**: 35
- **關鍵任務**: S5-1 (Integration Tests), S5-2 (Load Testing), S5-3 (Performance)

### Risk Register
- 🔴 性能問題可能需要額外時間優化
- 🔴 UAT 可能發現大量 Bug
- 🟡 文檔編寫耗時可能超出估算

### Definition of Done
- [ ] 所有 P0/P1 Bug 修復
- [ ] 測試覆蓋率 ≥ 80%
- [ ] 性能指標達標
- [ ] 負載測試通過
- [ ] 文檔完整
- [ ] UAT 通過
- [ ] 生產環境部署成功

---

## 🚀 Go-Live Checklist

### 技術就緒
- [ ] 所有服務部署成功
- [ ] 數據庫遷移完成
- [ ] SSL 證書配置
- [ ] 監控和告警工作
- [ ] 日誌收集正常
- [ ] 備份策略實施

### 安全就緒
- [ ] 滲透測試通過
- [ ] 安全掃描無高危漏洞
- [ ] RBAC 配置正確
- [ ] 審計日誌啟用
- [ ] Secrets 管理正確

### 運維就緒
- [ ] 部署 Runbook 就緒
- [ ] 回滾程序測試
- [ ] On-call 輪值表
- [ ] 故障響應流程
- [ ] 性能基準建立

### 業務就緒
- [ ] UAT 通過
- [ ] 用戶培訓完成
- [ ] Support 團隊準備就緒
- [ ] 溝通計劃執行
- [ ] Go-Live 日期確定

---

**文檔狀態**: ✅ 已完成  
**上次更新**: 2025-11-19  
**下次審查**: Sprint 5 開始前 (2026-02-03)

**🎉 恭喜！所有 Sprint 規劃完成！**