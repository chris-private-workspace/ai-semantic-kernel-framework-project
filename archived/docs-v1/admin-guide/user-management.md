# IPA Platform 用戶管理指南

本指南介紹如何管理 IPA Platform 的用戶、角色和權限。

---

## 目錄

1. [用戶管理](#用戶管理)
2. [角色與權限](#角色與權限)
3. [RBAC 配置](#rbac-配置)
4. [審計日誌](#審計日誌)

---

## 用戶管理

### 創建用戶

**通過 UI**:
1. 進入 **設定** → **用戶管理**
2. 點擊 **+ 新增用戶**
3. 填寫用戶資訊
4. 分配角色
5. 點擊 **創建**

**通過 API**:
```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "newuser",
    "full_name": "New User",
    "password": "SecurePass123!",
    "roles": ["user"]
  }'
```

### 用戶狀態

| 狀態 | 說明 |
|------|------|
| `active` | 正常使用 |
| `inactive` | 已停用 |
| `locked` | 因安全原因鎖定 |
| `pending` | 待驗證 |

### 停用/啟用用戶

```bash
# 停用用戶
curl -X PATCH http://localhost:8000/api/v1/users/{user_id}/status \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"is_active": false}'

# 啟用用戶
curl -X PATCH http://localhost:8000/api/v1/users/{user_id}/status \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"is_active": true}'
```

### 重設密碼

```bash
# 管理員重設
curl -X POST http://localhost:8000/api/v1/users/{user_id}/reset-password \
  -H "Authorization: Bearer <admin_token>"

# 用戶自助重設
curl -X POST http://localhost:8000/api/v1/auth/forgot-password \
  -d '{"email": "user@example.com"}'
```

---

## 角色與權限

### 預設角色

| 角色 | 說明 | 權限範圍 |
|------|------|----------|
| `admin` | 系統管理員 | 完整系統權限 |
| `operator` | 操作員 | 執行和監控權限 |
| `developer` | 開發者 | 工作流開發權限 |
| `viewer` | 觀察者 | 只讀權限 |
| `user` | 一般用戶 | 基本使用權限 |

### 權限矩陣

| 權限 | admin | operator | developer | viewer | user |
|------|-------|----------|-----------|--------|------|
| 查看工作流 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 創建工作流 | ✅ | ❌ | ✅ | ❌ | ❌ |
| 編輯工作流 | ✅ | ❌ | ✅ | ❌ | ❌ |
| 刪除工作流 | ✅ | ❌ | ✅ | ❌ | ❌ |
| 執行工作流 | ✅ | ✅ | ✅ | ❌ | ✅ |
| 查看執行 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 取消執行 | ✅ | ✅ | ✅ | ❌ | ❌ |
| 審批檢查點 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 管理用戶 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 管理角色 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 查看審計日誌 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 系統設定 | ✅ | ❌ | ❌ | ❌ | ❌ |

### 創建自定義角色

```bash
curl -X POST http://localhost:8000/api/v1/rbac/roles \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "workflow_manager",
    "description": "管理工作流但無用戶管理權限",
    "permissions": [
      "workflows:read",
      "workflows:create",
      "workflows:update",
      "workflows:delete",
      "executions:read",
      "executions:create",
      "executions:cancel"
    ]
  }'
```

### 分配角色給用戶

```bash
curl -X POST http://localhost:8000/api/v1/rbac/users/{user_id}/roles \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"role_id": "role-xyz"}'
```

---

## RBAC 配置

### 權限定義

```yaml
# 權限命名格式: resource:action
permissions:
  # 工作流權限
  - workflows:read
  - workflows:create
  - workflows:update
  - workflows:delete
  - workflows:execute

  # 執行權限
  - executions:read
  - executions:create
  - executions:cancel
  - executions:retry

  # Agent 權限
  - agents:read
  - agents:create
  - agents:update
  - agents:delete

  # 用戶權限
  - users:read
  - users:create
  - users:update
  - users:delete

  # 系統權限
  - system:settings
  - system:audit
  - system:monitoring
```

### 資源級權限

支持細粒度的資源級權限控制：

```yaml
# 只允許訪問特定工作流
resource_permissions:
  user_id: "user-123"
  permissions:
    - resource_type: "workflow"
      resource_id: "wf-abc"
      actions: ["read", "execute"]

    - resource_type: "workflow"
      resource_id: "wf-xyz"
      actions: ["read", "update", "execute"]
```

### 團隊權限

```yaml
# 團隊配置
teams:
  - name: "IT Operations"
    members:
      - user-001
      - user-002
    workflows:
      - wf-it-001
      - wf-it-002
    permissions:
      - workflows:read
      - workflows:execute
      - executions:read
```

---

## 審計日誌

### 查看審計日誌

```bash
# 獲取審計日誌
curl http://localhost:8000/api/v1/audit/logs \
  -H "Authorization: Bearer <admin_token>" \
  -G \
  -d "start_date=2025-11-01" \
  -d "end_date=2025-11-30" \
  -d "action=user.login"
```

### 審計事件類型

| 事件類型 | 說明 |
|----------|------|
| `user.login` | 用戶登入 |
| `user.logout` | 用戶登出 |
| `user.created` | 創建用戶 |
| `user.updated` | 更新用戶 |
| `user.deleted` | 刪除用戶 |
| `role.assigned` | 分配角色 |
| `role.removed` | 移除角色 |
| `workflow.created` | 創建工作流 |
| `workflow.updated` | 更新工作流 |
| `workflow.deleted` | 刪除工作流 |
| `execution.started` | 開始執行 |
| `execution.completed` | 完成執行 |
| `checkpoint.approved` | 審批通過 |
| `checkpoint.rejected` | 審批拒絕 |

### 審計日誌格式

```json
{
  "id": "audit-abc123",
  "timestamp": "2025-11-26T10:30:00Z",
  "user_id": "user-xyz",
  "user_email": "admin@example.com",
  "action": "workflow.created",
  "resource_type": "workflow",
  "resource_id": "wf-new123",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "details": {
    "workflow_name": "New Workflow",
    "trigger_type": "webhook"
  },
  "status": "success"
}
```

### 匯出審計日誌

```bash
# 匯出為 CSV
curl http://localhost:8000/api/v1/audit/logs/export \
  -H "Authorization: Bearer <admin_token>" \
  -G \
  -d "format=csv" \
  -d "start_date=2025-11-01" \
  -o audit_logs.csv

# 匯出為 JSON
curl http://localhost:8000/api/v1/audit/logs/export \
  -H "Authorization: Bearer <admin_token>" \
  -G \
  -d "format=json" \
  -d "start_date=2025-11-01" \
  -o audit_logs.json
```

---

## 安全最佳實踐

### 1. 最小權限原則

只分配用戶實際需要的權限：

```yaml
# ✅ 好的實踐
user:
  roles: ["developer"]  # 只有開發權限

# ❌ 不好的實踐
user:
  roles: ["admin"]  # 過度授權
```

### 2. 定期審查權限

- 每季度審查用戶權限
- 離職用戶立即停用
- 定期檢查審計日誌

### 3. 強密碼策略

```yaml
password_policy:
  min_length: 12
  require_uppercase: true
  require_lowercase: true
  require_digits: true
  require_special: true
  max_age_days: 90
```

### 4. 會話管理

```yaml
session:
  timeout_minutes: 30
  max_concurrent_sessions: 3
  require_mfa_for_admin: true
```

---

*最後更新: 2025-11-26*
