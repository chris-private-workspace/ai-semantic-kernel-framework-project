# Azure Architecture Design - IPA Platform

**版本**: v1.0.0
**日期**: 2025-11-20
**狀態**: Ready for Implementation

---

## 🎯 設計目標

### 核心原則
- **成本優化**: 使用 Azure App Service 替代 Kubernetes (節省 ~60% 成本)
- **簡化運維**: 利用 Azure 託管服務減少運維複雜度
- **彈性擴展**: 支持從 staging 到 production 的平滑擴展
- **安全合規**: 企業級安全和合規要求

### 目標指標
| 指標 | Staging | Production |
|-----|---------|------------|
| **可用性 SLA** | 99.5% | 99.95% |
| **響應時間 (p95)** | < 1s | < 500ms |
| **併發用戶** | 50 | 500 |
| **每月成本** | ~$50 | ~$150-200 |

---

## 🏗️ 整體架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                    Internet / Users                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│          Azure Front Door (Optional for Production)          │
│          - Global Load Balancing                             │
│          - WAF (Web Application Firewall)                    │
│          - CDN for Static Assets                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┴─────────────────────┐
        ↓                                           ↓
┌──────────────────┐                    ┌──────────────────┐
│  App Service     │                    │  App Service     │
│  (Staging)       │                    │  (Production)    │
│                  │                    │                  │
│  - Frontend      │                    │  - Frontend      │
│  - Backend API   │                    │  - Backend API   │
│  - Plan: B1      │                    │  - Plan: S1/P1V2 │
└──────────────────┘                    └──────────────────┘
        ↓                                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    Shared Azure Services                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │ PostgreSQL      │  │ Cache for Redis  │  │ Service    │ │
│  │ Flexible Server │  │ (Standard C1)    │  │ Bus        │ │
│  │ (B1ms/GP_Gen5_2)│  │                  │  │ (Standard) │ │
│  └─────────────────┘  └──────────────────┘  └────────────┘ │
│                                                               │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │ Key Vault       │  │ Storage Account  │  │ Application│ │
│  │ (Standard)      │  │ (StorageV2)      │  │ Insights   │ │
│  │                 │  │                  │  │            │ │
│  └─────────────────┘  └──────────────────┘  └────────────┘ │
│                                                               │
│  ┌─────────────────┐  ┌──────────────────┐                  │
│  │ Azure OpenAI    │  │ Container        │                  │
│  │ (Pay-as-you-go) │  │ Registry (Basic) │                  │
│  │                 │  │                  │                  │
│  └─────────────────┘  └──────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring & Logging                      │
├─────────────────────────────────────────────────────────────┤
│  - Azure Monitor                                             │
│  - Application Insights                                      │
│  - Log Analytics Workspace                                   │
│  - Azure Alerts                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Azure 資源清單

### 1. Resource Group
```yaml
Staging:
  Name: rg-ipa-staging-eastus
  Location: East US
  Tags:
    Environment: staging
    Project: ipa-platform
    CostCenter: engineering

Production:
  Name: rg-ipa-prod-eastus
  Location: East US
  Tags:
    Environment: production
    Project: ipa-platform
    CostCenter: engineering
```

---

### 2. App Service Plan

#### Staging Environment
```yaml
Name: asp-ipa-staging-eastus
SKU: B1 (Basic)
  - 1 vCPU
  - 1.75 GB RAM
  - Auto-scaling: Disabled
  - Cost: ~$13/month
OS: Linux
Runtime: Python 3.11

Features:
  - Custom domains: 支持
  - SSL/TLS: 支持
  - Deployment slots: 不支持 (需要 S1+)
  - Auto-scale: 不支持 (需要 S1+)
```

#### Production Environment
```yaml
Name: asp-ipa-prod-eastus
SKU: S1 (Standard) 或 P1V2 (Premium)

Option 1 - S1 (Standard):
  - 1 vCPU
  - 1.75 GB RAM
  - Auto-scaling: 支持 (1-3 instances)
  - Cost: ~$70/month
  - Deployment slots: 支持 (5 slots)

Option 2 - P1V2 (Premium, 推薦):
  - 1 vCPU
  - 3.5 GB RAM
  - Auto-scaling: 支持 (1-10 instances)
  - Cost: ~$80/month
  - Deployment slots: 支持 (20 slots)
  - VNet integration: 支持
  - Performance: 更好

OS: Linux
Runtime: Python 3.11

Features:
  - Custom domains: 支持
  - SSL/TLS: 支持
  - Deployment slots: 支持 (blue-green deployment)
  - Auto-scale: 支持 (based on CPU/RAM/HTTP queue)
  - Always On: 啟用
```

**推薦**: Production 使用 **P1V2**，獲得更好性能和 VNet integration

---

### 3. App Service (Web Apps)

#### Staging - Backend API
```yaml
Name: app-ipa-backend-staging
App Service Plan: asp-ipa-staging-eastus
Runtime: Python 3.11
Startup Command: gunicorn -w 2 -k uvicorn.workers.UvicornWorker main:app

Configuration:
  Environment Variables:
    ENVIRONMENT: staging
    DATABASE_URL: <from Key Vault>
    REDIS_URL: <from Key Vault>
    SERVICEBUS_CONNECTION_STRING: <from Key Vault>
    APPLICATIONINSIGHTS_CONNECTION_STRING: <from Key Vault>

  Deployment:
    Source: GitHub Actions
    Build: Oryx (automatic Python detection)
    Post-deployment script: alembic upgrade head

  Networking:
    CORS: Enabled (frontend domain)
    HTTPS Only: True
    Minimum TLS: 1.2
```

#### Staging - Frontend
```yaml
Name: app-ipa-frontend-staging
App Service Plan: asp-ipa-staging-eastus
Runtime: Node 20 LTS
Build Command: npm run build
Startup Command: npm run start

Configuration:
  Environment Variables:
    ENVIRONMENT: staging
    NEXT_PUBLIC_API_URL: https://app-ipa-backend-staging.azurewebsites.net
    NEXT_PUBLIC_APP_INSIGHTS_KEY: <from Key Vault>

  Deployment:
    Source: GitHub Actions
    Build: Oryx (automatic Node detection)

  Networking:
    HTTPS Only: True
    Minimum TLS: 1.2
```

#### Production - Backend API
```yaml
Name: app-ipa-backend-prod
App Service Plan: asp-ipa-prod-eastus
Runtime: Python 3.11
Startup Command: gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app

Configuration:
  Environment Variables:
    ENVIRONMENT: production
    DATABASE_URL: <from Key Vault>
    REDIS_URL: <from Key Vault>
    SERVICEBUS_CONNECTION_STRING: <from Key Vault>
    APPLICATIONINSIGHTS_CONNECTION_STRING: <from Key Vault>

  Deployment:
    Source: GitHub Actions
    Deployment Slots: 1 slot (for blue-green)
    Health Check: /health
    Post-deployment script: alembic upgrade head

  Networking:
    CORS: Enabled (frontend domain)
    HTTPS Only: True
    Minimum TLS: 1.2
    VNet Integration: 啟用 (if P1V2)

  Scaling:
    Auto-scale Rules:
      - CPU > 70% → Scale out (+1 instance)
      - CPU < 30% → Scale in (-1 instance)
      - Min instances: 1
      - Max instances: 3 (S1) or 5 (P1V2)

  Always On: True
```

#### Production - Frontend
```yaml
Name: app-ipa-frontend-prod
App Service Plan: asp-ipa-prod-eastus
Runtime: Node 20 LTS
Build Command: npm run build
Startup Command: npm run start

Configuration:
  Environment Variables:
    ENVIRONMENT: production
    NEXT_PUBLIC_API_URL: https://app-ipa-backend-prod.azurewebsites.net
    NEXT_PUBLIC_APP_INSIGHTS_KEY: <from Key Vault>

  Deployment:
    Source: GitHub Actions
    Deployment Slots: 1 slot (for blue-green)
    Health Check: /

  Networking:
    HTTPS Only: True
    Minimum TLS: 1.2

  Always On: True
```

---

### 4. PostgreSQL Flexible Server

#### Staging
```yaml
Name: psql-ipa-staging-eastus
Tier: Burstable
SKU: B1ms (1 vCPU, 2 GB RAM)
Storage: 32 GB (auto-grow enabled)
Backup: 7 days retention
High Availability: Disabled
Cost: ~$15/month

Version: PostgreSQL 16
Authentication: Azure AD + PostgreSQL auth

Networking:
  Public Access: Enabled (with firewall rules)
  Allowed IPs:
    - App Service outbound IPs
    - Developer IPs (for migration)

Databases:
  - ipa_platform_staging
```

#### Production
```yaml
Name: psql-ipa-prod-eastus
Tier: General Purpose
SKU: GP_Gen5_2 (2 vCPU, 10 GB RAM)
Storage: 128 GB (auto-grow enabled)
Backup: 35 days retention
High Availability: Zone-redundant (if critical)
Cost: ~$120/month (without HA) or ~$240/month (with HA)

Version: PostgreSQL 16
Authentication: Azure AD + PostgreSQL auth

Networking:
  Public Access: Disabled (if VNet integration)
  OR
  Public Access: Enabled with firewall rules
  Allowed IPs:
    - App Service outbound IPs only

Databases:
  - ipa_platform_production

Performance:
  - Connection pooling: PgBouncer (if needed)
  - Read replicas: Optional (for reporting)
```

**成本優化建議**:
- Staging 使用 Burstable B1ms (~$15/month)
- Production 初期使用 GP_Gen5_2 無 HA (~$120/month)
- 需要時再啟用 Zone-redundant HA

---

### 5. Azure Cache for Redis

#### Shared (Staging + Production)
```yaml
Name: redis-ipa-shared-eastus
Tier: Standard
SKU: C1 (1 GB cache)
Cost: ~$75/month

Version: Redis 6.x
TLS: Enabled (minimum 1.2)

Access:
  - Both staging and production App Services
  - Separate database indexes:
    - DB 0: Production
    - DB 1: Staging

Persistence: Disabled (cache only)
Clustering: Disabled (not needed for C1)

Use Cases:
  - Session storage
  - API response caching
  - Distributed locks
  - Rate limiting counters
```

**為什麼共用?**
- C1 (1GB) 足夠兩個環境使用不同 DB index
- 節省成本 (~$75 vs ~$150 兩個獨立實例)
- 如果需要隔離，Production 可升級到獨立 Redis

---

### 6. Azure Service Bus

#### Shared (Staging + Production)
```yaml
Name: sb-ipa-shared-eastus
Tier: Standard
Cost: ~$10/month (base) + usage

Namespaces:
  - Production namespace: sb-ipa-prod
  - Staging namespace: sb-ipa-staging (separate for isolation)

Queues (per namespace):
  - workflow-execution-queue
    - Max size: 5 GB
    - TTL: 14 days
    - Dead-letter queue: Enabled
    - Duplicate detection: 10 minutes

  - agent-task-queue
    - Max size: 5 GB
    - TTL: 7 days
    - Dead-letter queue: Enabled

  - notification-queue
    - Max size: 1 GB
    - TTL: 3 days

Topics/Subscriptions:
  - workflow-events (topic)
    - workflow-started (subscription)
    - workflow-completed (subscription)
    - workflow-failed (subscription)

Features:
  - Sessions: Enabled (for ordered processing)
  - Duplicate detection: Enabled
  - Dead-letter queue: Enabled
```

**建議**: 使用**兩個獨立 namespace** 確保環境隔離

---

### 7. Azure Key Vault

#### Shared (Staging + Production with separation)
```yaml
Name: kv-ipa-shared-eastus
Tier: Standard
Cost: ~$0.03/10,000 operations (~$5/month estimated)

Access Policies:
  Staging App Services:
    - Get Secrets (staging-* secrets)

  Production App Services:
    - Get Secrets (prod-* secrets)

  Developers (via Azure AD):
    - List, Get (for debugging)

Secrets:
  Staging:
    - staging-database-connection-string
    - staging-redis-connection-string
    - staging-servicebus-connection-string
    - staging-openai-api-key
    - staging-jwt-secret-key

  Production:
    - prod-database-connection-string
    - prod-redis-connection-string
    - prod-servicebus-connection-string
    - prod-openai-api-key
    - prod-jwt-secret-key

Networking:
  - Public Access: Enabled (with firewall)
  - Allowed IPs: App Service outbound IPs
  - VNet Integration: Optional (if using P1V2 plan)

Soft Delete: Enabled (90 days)
Purge Protection: Enabled (for production secrets)
```

---

### 8. Azure Storage Account

#### Shared (Staging + Production with containers)
```yaml
Name: stgipasharedeastus (unique global name)
Tier: Standard (StorageV2)
Replication: LRS (Locally Redundant Storage)
Performance: Standard
Cost: ~$5-10/month (depends on usage)

Blob Containers:
  - staging-uploads (for staging file uploads)
  - staging-logs (for staging application logs)
  - prod-uploads (for production file uploads)
  - prod-logs (for production application logs)
  - backups (for database backups)

Access Tier: Hot (for frequently accessed data)

Security:
  - HTTPS Only: Enabled
  - Minimum TLS: 1.2
  - Blob Public Access: Disabled
  - Access via: SAS tokens or Managed Identity

Use Cases:
  - File uploads (workflow attachments)
  - Application logs (long-term storage)
  - Database backups
  - Static assets (if not using CDN)
```

---

### 9. Azure OpenAI Service

```yaml
Name: openai-ipa-prod-eastus
Tier: Pay-as-you-go
Cost: Variable (based on tokens)

Deployments:
  - gpt-4 (for complex agent reasoning)
    - Version: Latest
    - TPM (Tokens Per Minute): 10K (可調整)

  - gpt-35-turbo (for simple tasks)
    - Version: Latest
    - TPM: 30K

Networking:
  - Public Access: Enabled (with firewall)
  - Allowed IPs: App Service outbound IPs
  - Private Endpoint: Optional (if needed)

Cost Estimation (monthly):
  - GPT-4: $0.03/1K input tokens, $0.06/1K output tokens
  - Estimated: 1M tokens/month = ~$50-100
```

---

### 10. Application Insights & Monitoring

```yaml
Application Insights:
  Name: appi-ipa-prod-eastus
  Type: Workspace-based
  Cost: Pay-as-you-go (first 5GB/month free)

  Connected Apps:
    - app-ipa-backend-staging
    - app-ipa-frontend-staging
    - app-ipa-backend-prod
    - app-ipa-frontend-prod

  Features:
    - Live Metrics
    - Application Map
    - Transaction Search
    - Failures analysis
    - Performance analysis

Log Analytics Workspace:
  Name: log-ipa-prod-eastus
  Retention: 30 days (standard)
  Cost: ~$2.76/GB ingested

Azure Monitor:
  Alerts:
    - CPU > 80% for 5 minutes
    - Memory > 85% for 5 minutes
    - HTTP 5xx errors > 10 in 5 minutes
    - Database connection failures
    - Service Bus dead-letter queue depth > 0

  Action Groups:
    - Email: team@company.com
    - Teams webhook (optional)
```

---

### 11. Container Registry (Optional)

```yaml
Name: acripaprodeastus
Tier: Basic
Cost: ~$5/month
Storage: 10 GB included

Purpose:
  - Store custom Docker images (if needed)
  - Currently: Use Oryx auto-build
  - Future: Custom container deployments

Images:
  - ipa-backend:latest
  - ipa-backend:staging
  - ipa-backend:v1.0.0
```

**當前階段**: 暫時不需要，使用 App Service Oryx 自動構建

---

## 💰 成本估算

### Staging Environment (每月)
| 服務 | SKU | 數量 | 月費 (USD) |
|-----|-----|------|-----------|
| App Service Plan | B1 | 1 | $13 |
| PostgreSQL | B1ms | 1 | $15 |
| Redis | C1 (shared) | 0.5 | $37.50 |
| Service Bus | Standard | 1 | $10 |
| Key Vault | Standard | shared | $2 |
| Storage | Standard LRS | shared | $3 |
| Application Insights | Pay-as-you-go | - | $5 |
| **Staging Total** | | | **~$85/month** |

### Production Environment (每月)
| 服務 | SKU | 數量 | 月費 (USD) |
|-----|-----|------|-----------|
| App Service Plan | P1V2 | 1 | $80 |
| PostgreSQL | GP_Gen5_2 | 1 | $120 |
| Redis | C1 (shared) | 0.5 | $37.50 |
| Service Bus | Standard | 1 | $10 |
| Key Vault | Standard | shared | $3 |
| Storage | Standard LRS | shared | $5 |
| Application Insights | Pay-as-you-go | - | $10 |
| Azure OpenAI | Pay-as-you-go | - | $50-100 |
| **Production Total** | | | **~$315-365/month** |

### **總計 (Staging + Production)**
**~$400-450/month**

### 成本優化建議
1. **Staging 降級**: B1 → Free tier (F1) = 節省 $13/month
2. **Redis 共用**: C1 兩環境共用 = 節省 $75/month
3. **PostgreSQL Dev/Test**: 使用 Dev/Test 定價 = 節省 15%
4. **Reserved Capacity**: 預付 1-3 年 = 節省 30-50%

**優化後成本**: **~$300-350/month**

---

## 🔐 安全架構

### 1. 身份驗證流程
```
User → Frontend → Azure AD B2C → JWT Token → Backend API
                                              ↓
                                    Validate with Azure AD
```

### 2. 服務間通信
```
App Service → Managed Identity → Key Vault (get secrets)
App Service → Managed Identity → PostgreSQL (connect)
App Service → Managed Identity → Storage (access blobs)
```

### 3. 網絡安全
- **HTTPS Only**: 所有服務強制 HTTPS
- **TLS 1.2+**: 最低 TLS 版本
- **CORS**: 僅允許前端域名
- **Firewall**: PostgreSQL/Key Vault IP 白名單
- **VNet Integration**: Production 使用 VNet (如果 P1V2)

### 4. 數據安全
- **Encryption at Rest**: 所有 Azure 服務默認啟用
- **Encryption in Transit**: TLS/SSL
- **Key Vault**: 所有密鑰和連接字串存儲在 Key Vault
- **Backup**: PostgreSQL 自動備份 (7-35 days)

---

## 📊 監控與告警

### Application Insights Metrics
- Request rate and duration
- Failed requests (4xx, 5xx)
- Exception tracking
- Dependency tracking (DB, Redis, Service Bus)
- Custom events (workflow execution, agent tasks)

### Azure Monitor Alerts
1. **High CPU Usage**: CPU > 80% for 5 min
2. **High Memory**: Memory > 85% for 5 min
3. **HTTP Errors**: 5xx > 10 in 5 min
4. **Database Issues**: Connection failures
5. **Queue Backlog**: Service Bus queue depth > 1000

### Log Analytics Queries
```kusto
// Failed requests in last 24 hours
requests
| where timestamp > ago(24h)
| where success == false
| summarize count() by resultCode, name

// Slow queries
dependencies
| where type == "SQL"
| where duration > 1000
| project timestamp, name, duration, success

// Exception analysis
exceptions
| where timestamp > ago(24h)
| summarize count() by type, outerMessage
```

---

## 🚀 部署策略

### Staging Environment
```yaml
Deployment:
  Trigger: Push to 'develop' branch
  Strategy: Direct deployment
  Steps:
    1. Run tests
    2. Build application
    3. Deploy to staging
    4. Run smoke tests
    5. Notify team

Rollback:
  - Re-deploy previous commit
  - Database migrations: Manual rollback if needed
```

### Production Environment
```yaml
Deployment:
  Trigger: Push to 'main' branch or manual approval
  Strategy: Blue-Green deployment (using deployment slots)
  Steps:
    1. Run full test suite
    2. Build application
    3. Deploy to 'staging' slot
    4. Run integration tests on slot
    5. Warm up slot (health check)
    6. Manual approval (optional)
    7. Swap staging → production
    8. Monitor for 15 minutes
    9. Keep staging slot as rollback

Rollback:
  - Swap production → staging slot (< 1 minute)
  - Database migrations: Have rollback scripts ready
```

---

## 🔄 災難恢復 (DR)

### Backup Strategy
```yaml
PostgreSQL:
  Automated Backup: Enabled
  Retention:
    - Staging: 7 days
    - Production: 35 days
  Point-in-time Restore: Available
  Geo-redundant: Optional (additional cost)

Application Code:
  Source: GitHub (version controlled)
  Deployment: Reproducible via GitHub Actions

Configuration:
  Secrets: Key Vault (soft-delete enabled)
  Environment vars: Documented in repo

Data:
  User uploads: Storage Account (LRS)
  Logs: Application Insights (30 days retention)
```

### Recovery Time Objectives (RTO/RPO)
| Component | RTO | RPO |
|-----------|-----|-----|
| **App Service** | < 15 min | 0 (stateless) |
| **PostgreSQL** | < 30 min | < 5 min (automated backup) |
| **Redis** | < 5 min | N/A (cache only) |
| **Service Bus** | < 5 min | < 1 min (replicated) |

---

## 📝 下一步行動

### 立即準備 (S0-2)
- [x] 架構設計完成
- [ ] 創建 Azure Bicep/Terraform IaC 模板
- [ ] 準備環境變數配置文件
- [ ] 創建部署檢查清單

### CI/CD 準備 (S0-3)
- [ ] 創建 GitHub Actions workflows
- [ ] 配置 Azure Service Principal
- [ ] 設置 GitHub Secrets
- [ ] 測試部署流程

### 部署前檢查
- [ ] Azure 訂閱權限確認
- [ ] Service Principal 創建
- [ ] Resource Group 創建
- [ ] 執行 IaC 部署
- [ ] 驗證所有服務健康狀態

---

**文檔版本**: v1.0.0
**最後更新**: 2025-11-20
**下次更新**: 部署完成後
