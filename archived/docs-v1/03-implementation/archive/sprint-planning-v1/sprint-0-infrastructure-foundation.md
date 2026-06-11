# Sprint 0: Infrastructure & Foundation - 詳細規劃

> ⚠️ **重要提示**: 本文檔為原始 Kubernetes 版本規劃，已被 MVP 調整版替代  
> 📄 **最新版本**: [Sprint 0 MVP Revised](./sprint-0-mvp-revised.md)  
> 🔄 **主要變更**: Kubernetes → Azure App Service, RabbitMQ → Service Bus, ELK → App Insights

**版本**: 1.0 (已過時 - Superseded)  
**創建日期**: 2025-11-19  
**Sprint 期間**: 2025-11-25 至 2025-12-06 (2週)  
**團隊規模**: 8人 (3後端, 2前端, 1 DevOps, 1 QA, 1 PO)

---

## 📋 Sprint 目標

Sprint 0 的主要目標是建立整個項目的基礎設施，為後續的功能開發做好準備。這是最關鍵的 Sprint，所有 P0 任務必須完成才能進入 Sprint 1。

### 核心目標
1. ✅ 建立開發、測試、生產環境
2. ✅ 實現 CI/CD 自動化流水線
3. ✅ 初始化數據庫架構和遷移框架
4. ✅ 配置身份驗證和授權框架
5. ✅ 部署監控和日誌基礎設施

### 成功標準
- 所有開發人員可以在本地運行完整的應用程序棧
- CI/CD 流水線可以自動構建、測試、部署到 Staging
- 數據庫遷移系統可以正常工作
- OAuth 2.0 身份驗證可以使用 Azure AD 登錄
- Prometheus 和 Grafana 顯示基本的系統指標

---

## 📊 Story Points 分配

**總計劃點數**: 42  
**按優先級分配**:
- P0 (Critical): 34 點 (81%)
- P1 (High): 8 點 (19%)

**按團隊分配**:
- DevOps: 21 點 (50%)
- Backend: 21 點 (50%)

---

## 🎯 Sprint Backlog

### S0-1: Development Environment Setup
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: DevOps  
**依賴**: 無

#### 描述
配置本地開發環境，使用 Docker Compose 編排所有服務，讓開發人員可以一鍵啟動完整的應用程序棧。

#### 驗收標準
- [ ] Docker Compose 配置文件創建完成，包含所有服務
  - PostgreSQL 16 with volume mount
  - Redis 7 with persistence
  - RabbitMQ 3.12 with management UI
  - API Gateway (Kong)
  - Workflow Service
  - Execution Service
  - Agent Service
- [ ] README 包含詳細的本地環境設置指南
- [ ] 提供環境變量模板文件 (.env.example)
- [ ] 所有服務可以正常啟動和相互通信
- [ ] 開發人員可以在 15 分鐘內完成環境搭建

#### 技術實現細節
```yaml
# docker-compose.yml 結構
version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ipa_platform
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
  
  rabbitmq:
    image: rabbitmq:3.12-management-alpine
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5
```

#### 子任務
1. [ ] 創建 Docker Compose 配置文件
2. [ ] 設置 PostgreSQL 初始化腳本
3. [ ] 配置 Redis 持久化
4. [ ] 設置 RabbitMQ 默認 vhost 和權限
5. [ ] 創建開發環境文檔
6. [ ] 編寫環境健康檢查腳本
7. [ ] 測試多開發人員並行環境設置

#### 測試計劃
- 在 3 台不同的開發機器上測試環境搭建流程
- 驗證所有服務的健康檢查都通過
- 確認數據持久化正常工作（重啟容器後數據保留）

---

### S0-2: Kubernetes Cluster Setup
**Story Points**: 8  
**優先級**: P0 - Critical  
**負責人**: DevOps  
**依賴**: 無

#### 描述
在 Azure 上建立 AKS (Azure Kubernetes Service) 集群，配置 Staging 和 Production 環境，實現 RBAC 和 namespace 隔離。

#### 驗收標準
- [ ] AKS 集群創建完成（2 個集群：staging, production）
  - Staging: 3 nodes (Standard_D2s_v3)
  - Production: 5 nodes (Standard_D4s_v3) with autoscaling
- [ ] 配置 RBAC，限制開發人員權限
- [ ] 創建 namespace 隔離不同服務
  - `ipa-platform-core`: 核心服務
  - `ipa-platform-integration`: 集成服務
  - `ipa-platform-monitoring`: 監控服務
- [ ] 安裝 Ingress Controller (NGINX)
- [ ] 配置 Azure Container Registry (ACR) 集成
- [ ] 設置 Azure Managed Identity for Kubernetes
- [ ] 文檔記錄集群訪問和管理流程

#### 技術實現細節
```bash
# AKS 集群創建命令
az aks create \
  --resource-group ipa-platform-rg \
  --name ipa-staging-aks \
  --node-count 3 \
  --node-vm-size Standard_D2s_v3 \
  --enable-managed-identity \
  --enable-addons monitoring \
  --attach-acr ipaplatformacr \
  --network-plugin azure \
  --network-policy azure \
  --kubernetes-version 1.28

# RBAC 配置示例
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: ipa-platform-core
  name: developer
rules:
- apiGroups: ["", "apps", "extensions"]
  resources: ["pods", "deployments", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
```

#### 子任務
1. [ ] 創建 Azure Resource Group
2. [ ] 配置 Azure Container Registry
3. [ ] 創建 Staging AKS 集群
4. [ ] 創建 Production AKS 集群
5. [ ] 安裝和配置 NGINX Ingress Controller
6. [ ] 設置 namespaces 和 RBAC
7. [ ] 配置 Managed Identity 和 ACR 集成
8. [ ] 安裝 cert-manager for SSL certificates
9. [ ] 創建 Kubernetes 管理文檔

#### 測試計劃
- 驗證所有節點健康狀態
- 測試 RBAC 權限（開發人員不能刪除 production pods）
- 確認 ACR 鏡像拉取成功
- 測試 Ingress Controller 路由功能

---

### S0-3: CI/CD Pipeline Implementation
**Story Points**: 8  
**優先級**: P0 - Critical  
**負責人**: DevOps  
**依賴**: S0-2

#### 描述
創建 GitHub Actions 工作流，實現自動化的構建、測試、安全掃描和部署流程。

#### 驗收標準
- [ ] GitHub Actions workflows 創建完成
  - `build.yml`: 構建和單元測試
  - `security-scan.yml`: 安全漏洞掃描
  - `deploy-staging.yml`: 部署到 Staging
  - `deploy-production.yml`: 部署到 Production (需要審批)
- [ ] 自動化測試在每次 PR 時運行
- [ ] Docker 鏡像自動推送到 ACR
- [ ] Staging 環境自動部署 (main 分支)
- [ ] Production 部署需要手動審批
- [ ] 部署失敗時自動回滾
- [ ] Slack/Teams 通知集成

#### 技術實現細節
```yaml
# .github/workflows/build.yml
name: Build and Test

on:
  pull_request:
    branches: [ main, develop ]
  push:
    branches: [ main, develop ]

jobs:
  backend-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup .NET
        uses: actions/setup-dotnet@v3
        with:
          dotnet-version: '8.0.x'
      
      - name: Restore dependencies
        run: dotnet restore
      
      - name: Build
        run: dotnet build --no-restore --configuration Release
      
      - name: Run unit tests
        run: dotnet test --no-build --configuration Release --verbosity normal --collect:"XPlat Code Coverage"
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage.cobertura.xml
          fail_ci_if_error: true
  
  frontend-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Lint
        run: npm run lint
      
      - name: Type check
        run: npm run type-check
      
      - name: Build
        run: npm run build
      
      - name: Run unit tests
        run: npm run test:coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage/lcov.info

  docker-build:
    needs: [backend-build, frontend-build]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Login to ACR
        uses: azure/docker-login@v1
        with:
          login-server: ${{ secrets.ACR_LOGIN_SERVER }}
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}
      
      - name: Build and push images
        run: |
          docker build -t ${{ secrets.ACR_LOGIN_SERVER }}/workflow-service:${{ github.sha }} -f src/WorkflowService/Dockerfile .
          docker push ${{ secrets.ACR_LOGIN_SERVER }}/workflow-service:${{ github.sha }}
          
          docker build -t ${{ secrets.ACR_LOGIN_SERVER }}/execution-service:${{ github.sha }} -f src/ExecutionService/Dockerfile .
          docker push ${{ secrets.ACR_LOGIN_SERVER }}/execution-service:${{ github.sha }}
          
          docker build -t ${{ secrets.ACR_LOGIN_SERVER }}/agent-service:${{ github.sha }} -f src/AgentService/Dockerfile .
          docker push ${{ secrets.ACR_LOGIN_SERVER }}/agent-service:${{ github.sha }}
          
          docker build -t ${{ secrets.ACR_LOGIN_SERVER }}/web-frontend:${{ github.sha }} -f src/WebFrontend/Dockerfile .
          docker push ${{ secrets.ACR_LOGIN_SERVER }}/web-frontend:${{ github.sha }}
```

#### 子任務
1. [ ] 創建 GitHub Actions workflows 目錄結構
2. [ ] 實現 backend build and test workflow
3. [ ] 實現 frontend build and test workflow
4. [ ] 實現 Docker build and push workflow
5. [ ] 實現 security scanning workflow (Trivy, Snyk)
6. [ ] 實現 Staging deployment workflow
7. [ ] 實現 Production deployment workflow with approval
8. [ ] 配置 GitHub Secrets (ACR credentials, Kubernetes config)
9. [ ] 設置 Slack/Teams 通知
10. [ ] 創建 CI/CD 文檔和故障排除指南

#### 測試計劃
- 創建測試 PR 驗證 build workflow 觸發
- 合併到 main 分支驗證自動部署到 Staging
- 模擬部署失敗驗證回滾機制
- 驗證安全掃描可以檢測到已知漏洞

---

### S0-4: Database Infrastructure
**Story Points**: 5  
**優先級**: P0 - Critical  
**負責人**: Backend  
**依賴**: S0-2

#### 描述
建立 PostgreSQL 16 數據庫基礎設施，配置主從複製，初始化數據庫架構，設置遷移框架。

#### 驗收標準
- [ ] PostgreSQL 16 部署到 Kubernetes (使用 StatefulSet)
- [ ] 配置主從複製（1 primary + 2 replicas）
- [ ] 設置自動備份（每天全量備份，保留 30 天）
- [ ] 初始化數據庫架構
  - Users 表
  - Workflows 表
  - WorkflowVersions 表
  - Executions 表
  - ExecutionSteps 表
  - Agents 表
  - AuditLogs 表
- [ ] 配置 Entity Framework Core 遷移
- [ ] 創建數據庫連接字符串管理機制（使用 Key Vault）
- [ ] 實現數據庫健康檢查端點

#### 技術實現細節
```csharp
// Entity Framework Core DbContext
public class IpaPlatformDbContext : DbContext
{
    public DbSet<User> Users { get; set; }
    public DbSet<Workflow> Workflows { get; set; }
    public DbSet<WorkflowVersion> WorkflowVersions { get; set; }
    public DbSet<Execution> Executions { get; set; }
    public DbSet<ExecutionStep> ExecutionSteps { get; set; }
    public DbSet<Agent> Agents { get; set; }
    public DbSet<AuditLog> AuditLogs { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // User entity configuration
        modelBuilder.Entity<User>(entity =>
        {
            entity.ToTable("users");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Email).IsRequired().HasMaxLength(255);
            entity.Property(e => e.DisplayName).IsRequired().HasMaxLength(100);
            entity.HasIndex(e => e.Email).IsUnique();
            entity.HasIndex(e => e.AzureAdObjectId).IsUnique();
        });

        // Workflow entity configuration
        modelBuilder.Entity<Workflow>(entity =>
        {
            entity.ToTable("workflows");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Name).IsRequired().HasMaxLength(200);
            entity.Property(e => e.Description).HasMaxLength(1000);
            entity.Property(e => e.Status).IsRequired().HasMaxLength(50);
            entity.HasIndex(e => new { e.CreatedBy, e.Status });
            
            entity.HasOne(e => e.Creator)
                .WithMany()
                .HasForeignKey(e => e.CreatedBy)
                .OnDelete(DeleteBehavior.Restrict);
        });

        // Execution entity configuration
        modelBuilder.Entity<Execution>(entity =>
        {
            entity.ToTable("executions");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Status).IsRequired().HasMaxLength(50);
            entity.HasIndex(e => new { e.WorkflowId, e.Status, e.StartTime });
            
            entity.HasOne(e => e.Workflow)
                .WithMany()
                .HasForeignKey(e => e.WorkflowId)
                .OnDelete(DeleteBehavior.Restrict);
        });

        // AuditLog entity configuration
        modelBuilder.Entity<AuditLog>(entity =>
        {
            entity.ToTable("audit_logs");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Action).IsRequired().HasMaxLength(100);
            entity.Property(e => e.ResourceType).IsRequired().HasMaxLength(50);
            entity.HasIndex(e => new { e.UserId, e.Timestamp });
            entity.HasIndex(e => new { e.ResourceType, e.ResourceId });
        });
    }
}
```

```yaml
# PostgreSQL StatefulSet 配置
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
  namespace: ipa-platform-core
spec:
  serviceName: postgresql
  replicas: 3
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:16-alpine
        ports:
        - containerPort: 5432
          name: postgresql
        env:
        - name: POSTGRES_DB
          value: ipa_platform
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgresql-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgresql-secret
              key: password
        volumeMounts:
        - name: postgresql-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
  volumeClaimTemplates:
  - metadata:
      name: postgresql-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 50Gi
```

#### 子任務
1. [ ] 設計數據庫架構（ERD 圖）
2. [ ] 創建 Entity Framework Core entities
3. [ ] 創建 DbContext 和配置
4. [ ] 生成初始遷移腳本
5. [ ] 創建 PostgreSQL StatefulSet YAML
6. [ ] 配置 PostgreSQL replication
7. [ ] 設置自動備份腳本（CronJob）
8. [ ] 創建數據庫初始化 Job
9. [ ] 實現健康檢查端點
10. [ ] 編寫數據庫運維文檔

#### 測試計劃
- 執行遷移腳本驗證架構創建
- 測試主從複製延遲（< 1 秒）
- 驗證備份和恢復流程
- 模擬 primary 節點故障測試 failover

---

### S0-5: Redis Cache Setup
**Story Points**: 3  
**優先級**: P0 - Critical  
**負責人**: Backend  
**依賴**: S0-2

#### 描述
配置 Redis 7 集群用於緩存和會話管理，實現高可用性和持久化。

#### 驗收標準
- [ ] Redis 7 部署到 Kubernetes (使用 StatefulSet)
- [ ] 配置 Redis Sentinel for high availability (3 nodes)
- [ ] 啟用 AOF (Append-Only File) 持久化
- [ ] 實現 Redis 緩存抽象層
- [ ] 配置緩存過期策略
- [ ] 創建 Redis 連接管理器
- [ ] 實現分佈式鎖機制（使用 RedLock）

#### 技術實現細節
```csharp
// Redis 緩存服務接口
public interface ICacheService
{
    Task<T?> GetAsync<T>(string key, CancellationToken cancellationToken = default);
    Task SetAsync<T>(string key, T value, TimeSpan? expiration = null, CancellationToken cancellationToken = default);
    Task<bool> RemoveAsync(string key, CancellationToken cancellationToken = default);
    Task<bool> ExistsAsync(string key, CancellationToken cancellationToken = default);
    Task<IDistributedLock> AcquireLockAsync(string key, TimeSpan expiration, CancellationToken cancellationToken = default);
}

// Redis 緩存服務實現
public class RedisCacheService : ICacheService
{
    private readonly IConnectionMultiplexer _redis;
    private readonly ILogger<RedisCacheService> _logger;
    private readonly JsonSerializerOptions _jsonOptions;

    public RedisCacheService(
        IConnectionMultiplexer redis,
        ILogger<RedisCacheService> logger)
    {
        _redis = redis;
        _logger = logger;
        _jsonOptions = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
        };
    }

    public async Task<T?> GetAsync<T>(string key, CancellationToken cancellationToken = default)
    {
        var db = _redis.GetDatabase();
        var value = await db.StringGetAsync(key);
        
        if (value.IsNullOrEmpty)
            return default;
        
        return JsonSerializer.Deserialize<T>(value!, _jsonOptions);
    }

    public async Task SetAsync<T>(string key, T value, TimeSpan? expiration = null, CancellationToken cancellationToken = default)
    {
        var db = _redis.GetDatabase();
        var serialized = JsonSerializer.Serialize(value, _jsonOptions);
        await db.StringSetAsync(key, serialized, expiration);
        
        _logger.LogDebug("Cached value for key: {Key} with expiration: {Expiration}", key, expiration);
    }

    public async Task<bool> RemoveAsync(string key, CancellationToken cancellationToken = default)
    {
        var db = _redis.GetDatabase();
        return await db.KeyDeleteAsync(key);
    }

    public async Task<IDistributedLock> AcquireLockAsync(string key, TimeSpan expiration, CancellationToken cancellationToken = default)
    {
        var db = _redis.GetDatabase();
        var lockKey = $"lock:{key}";
        var lockValue = Guid.NewGuid().ToString();
        
        var acquired = await db.StringSetAsync(lockKey, lockValue, expiration, When.NotExists);
        
        if (!acquired)
            throw new InvalidOperationException($"Failed to acquire lock for key: {key}");
        
        return new RedisDistributedLock(db, lockKey, lockValue, _logger);
    }
}
```

#### 子任務
1. [ ] 創建 Redis StatefulSet 配置
2. [ ] 配置 Redis Sentinel
3. [ ] 實現 ICacheService 接口
4. [ ] 實現 RedisCacheService
5. [ ] 實現分佈式鎖機制
6. [ ] 配置 StackExchange.Redis 連接
7. [ ] 創建緩存 middleware
8. [ ] 編寫 Redis 使用文檔

#### 測試計劃
- 測試緩存讀寫性能
- 驗證 Sentinel failover 機制
- 測試分佈式鎖在並發場景下的行為
- 驗證 AOF 持久化恢復

---

### S0-6: Message Queue Setup
**Story Points**: 3  
**優先級**: P0 - Critical  
**負責人**: Backend  
**依賴**: S0-2

#### 描述
部署 RabbitMQ 3.12 消息隊列，配置持久化和監控，為異步任務處理做準備。

#### 驗收標準
- [ ] RabbitMQ 3.12 部署到 Kubernetes
- [ ] 配置 RabbitMQ cluster (3 nodes)
- [ ] 啟用持久化和鏡像隊列
- [ ] 創建必要的 exchanges 和 queues
  - `workflow.events` (topic exchange)
  - `execution.tasks` (direct exchange)
  - `notifications` (fanout exchange)
- [ ] 實現消息發布者抽象
- [ ] 實現消息消費者基礎類
- [ ] 配置 RabbitMQ Management UI
- [ ] 設置監控告警（隊列深度、消費延遲）

#### 技術實現細節
```csharp
// 消息發布者接口
public interface IMessagePublisher
{
    Task PublishAsync<T>(string exchange, string routingKey, T message, CancellationToken cancellationToken = default);
    Task PublishBatchAsync<T>(string exchange, string routingKey, IEnumerable<T> messages, CancellationToken cancellationToken = default);
}

// RabbitMQ 消息發布者實現
public class RabbitMqPublisher : IMessagePublisher
{
    private readonly IConnection _connection;
    private readonly ILogger<RabbitMqPublisher> _logger;
    private readonly JsonSerializerOptions _jsonOptions;

    public RabbitMqPublisher(
        IConnection connection,
        ILogger<RabbitMqPublisher> logger)
    {
        _connection = connection;
        _logger = logger;
        _jsonOptions = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        };
    }

    public async Task PublishAsync<T>(string exchange, string routingKey, T message, CancellationToken cancellationToken = default)
    {
        using var channel = _connection.CreateModel();
        
        var body = JsonSerializer.SerializeToUtf8Bytes(message, _jsonOptions);
        var properties = channel.CreateBasicProperties();
        properties.Persistent = true;
        properties.MessageId = Guid.NewGuid().ToString();
        properties.Timestamp = new AmqpTimestamp(DateTimeOffset.UtcNow.ToUnixTimeSeconds());
        
        channel.BasicPublish(
            exchange: exchange,
            routingKey: routingKey,
            basicProperties: properties,
            body: body);
        
        _logger.LogInformation("Published message to {Exchange} with routing key {RoutingKey}", exchange, routingKey);
    }
}

// 消息消費者基類
public abstract class RabbitMqConsumer<T> : BackgroundService
{
    private readonly IConnection _connection;
    private readonly string _queueName;
    private readonly ILogger _logger;
    private IModel? _channel;

    protected RabbitMqConsumer(
        IConnection connection,
        string queueName,
        ILogger logger)
    {
        _connection = connection;
        _queueName = queueName;
        _logger = logger;
    }

    protected override Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _channel = _connection.CreateModel();
        _channel.BasicQos(prefetchSize: 0, prefetchCount: 10, global: false);
        
        var consumer = new EventingBasicConsumer(_channel);
        consumer.Received += async (model, ea) =>
        {
            try
            {
                var message = JsonSerializer.Deserialize<T>(ea.Body.ToArray());
                await HandleMessageAsync(message!, stoppingToken);
                _channel.BasicAck(deliveryTag: ea.DeliveryTag, multiple: false);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error processing message from queue {QueueName}", _queueName);
                _channel.BasicNack(deliveryTag: ea.DeliveryTag, multiple: false, requeue: true);
            }
        };
        
        _channel.BasicConsume(queue: _queueName, autoAck: false, consumer: consumer);
        
        return Task.CompletedTask;
    }

    protected abstract Task HandleMessageAsync(T message, CancellationToken cancellationToken);
}
```

#### 子任務
1. [ ] 創建 RabbitMQ StatefulSet 配置
2. [ ] 配置 RabbitMQ cluster
3. [ ] 創建 exchanges 和 queues 定義
4. [ ] 實現 IMessagePublisher 接口
5. [ ] 實現 RabbitMqConsumer 基類
6. [ ] 配置 Management UI ingress
7. [ ] 設置 Prometheus exporter for RabbitMQ
8. [ ] 編寫消息隊列使用文檔

#### 測試計劃
- 測試消息發布和消費
- 驗證消息持久化（重啟後消息不丟失）
- 測試消費者失敗重試機制
- 驗證 cluster failover

---

### S0-7: Authentication Framework
**Story Points**: 8  
**優先級**: P0 - Critical  
**負責人**: Backend  
**依賴**: S0-4

#### 描述
實現 OAuth 2.0 + JWT 身份驗證框架，集成 Azure AD，支持 RBAC。

#### 驗收標準
- [ ] 實現 OAuth 2.0 Authorization Code flow
- [ ] 集成 Azure AD (Microsoft Entra ID)
- [ ] 實現 JWT token 生成和驗證
- [ ] 實現 refresh token 機制
- [ ] 創建 authentication middleware
- [ ] 實現 RBAC 基礎框架（角色和權限定義）
- [ ] 創建用戶管理 API endpoints
- [ ] 實現登錄/登出功能
- [ ] 配置 CORS 策略

#### 技術實現細節
```csharp
// JWT 配置
public class JwtSettings
{
    public string Issuer { get; set; } = default!;
    public string Audience { get; set; } = default!;
    public string SecretKey { get; set; } = default!;
    public int AccessTokenExpirationMinutes { get; set; } = 60;
    public int RefreshTokenExpirationDays { get; set; } = 7;
}

// JWT Token Service
public class JwtTokenService : ITokenService
{
    private readonly JwtSettings _settings;
    private readonly ILogger<JwtTokenService> _logger;

    public string GenerateAccessToken(User user, IEnumerable<string> roles)
    {
        var claims = new List<Claim>
        {
            new Claim(ClaimTypes.NameIdentifier, user.Id.ToString()),
            new Claim(ClaimTypes.Email, user.Email),
            new Claim(ClaimTypes.Name, user.DisplayName),
            new Claim("azure_ad_object_id", user.AzureAdObjectId)
        };
        
        foreach (var role in roles)
        {
            claims.Add(new Claim(ClaimTypes.Role, role));
        }
        
        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_settings.SecretKey));
        var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);
        
        var token = new JwtSecurityToken(
            issuer: _settings.Issuer,
            audience: _settings.Audience,
            claims: claims,
            expires: DateTime.UtcNow.AddMinutes(_settings.AccessTokenExpirationMinutes),
            signingCredentials: creds);
        
        return new JwtSecurityTokenHandler().WriteToken(token);
    }
}

// Authentication middleware 配置
public static class AuthenticationExtensions
{
    public static IServiceCollection AddIpaAuthentication(this IServiceCollection services, IConfiguration configuration)
    {
        var jwtSettings = configuration.GetSection("Jwt").Get<JwtSettings>();
        services.AddSingleton(jwtSettings);
        
        services.AddAuthentication(options =>
        {
            options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
            options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
        })
        .AddJwtBearer(options =>
        {
            options.TokenValidationParameters = new TokenValidationParameters
            {
                ValidateIssuer = true,
                ValidateAudience = true,
                ValidateLifetime = true,
                ValidateIssuerSigningKey = true,
                ValidIssuer = jwtSettings.Issuer,
                ValidAudience = jwtSettings.Audience,
                IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtSettings.SecretKey)),
                ClockSkew = TimeSpan.Zero
            };
        })
        .AddMicrosoftIdentityWebApi(configuration.GetSection("AzureAd"));
        
        services.AddAuthorization(options =>
        {
            options.AddPolicy("RequireAdministratorRole", policy => 
                policy.RequireRole("Administrator"));
            options.AddPolicy("RequireWorkflowEditPermission", policy => 
                policy.RequireClaim("Permission", "Workflow.Edit"));
        });
        
        return services;
    }
}
```

#### 子任務
1. [ ] 配置 Azure AD 應用註冊
2. [ ] 實現 JwtTokenService
3. [ ] 創建 authentication middleware
4. [ ] 實現登錄 endpoint (POST /api/auth/login)
5. [ ] 實現 refresh token endpoint (POST /api/auth/refresh)
6. [ ] 實現登出 endpoint (POST /api/auth/logout)
7. [ ] 創建用戶管理 endpoints (CRUD)
8. [ ] 實現 RBAC 權限檢查
9. [ ] 配置 CORS 策略
10. [ ] 編寫身份驗證文檔

#### 測試計劃
- 測試 Azure AD OAuth 2.0 flow
- 驗證 JWT token 生成和驗證
- 測試 refresh token 機制
- 驗證 RBAC 權限控制
- 測試 token 過期處理

---

### S0-8: Monitoring Stack
**Story Points**: 5  
**優先級**: P1 - High  
**負責人**: DevOps  
**依賴**: S0-2

#### 描述
部署 Prometheus 和 Grafana 監控棧，配置初始儀表板，實現基礎的系統監控。

#### 驗收標準
- [ ] Prometheus 部署到 Kubernetes
- [ ] Grafana 部署並配置數據源
- [ ] 配置 Prometheus Operator 和 ServiceMonitor
- [ ] 創建初始 Grafana 儀表板
  - Kubernetes 集群監控
  - Node 資源使用率
  - Pod 資源使用率
  - API 請求率和延遲
- [ ] 配置 Alertmanager
- [ ] 設置基本告警規則
  - Pod 重啟過多
  - CPU/Memory 使用率過高
  - API 錯誤率過高
- [ ] 配置 Grafana 用戶和權限

#### 技術實現細節
```yaml
# Prometheus Operator 配置
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: prometheus
  namespace: ipa-platform-monitoring
spec:
  replicas: 2
  retention: 30d
  serviceAccountName: prometheus
  serviceMonitorSelector:
    matchLabels:
      monitoring: enabled
  ruleSelector:
    matchLabels:
      monitoring: enabled
  resources:
    requests:
      memory: 2Gi
      cpu: 1000m
    limits:
      memory: 4Gi
      cpu: 2000m
  storage:
    volumeClaimTemplate:
      spec:
        accessModes:
        - ReadWriteOnce
        resources:
          requests:
            storage: 100Gi

---
# ServiceMonitor for API services
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: api-services
  namespace: ipa-platform-core
  labels:
    monitoring: enabled
spec:
  selector:
    matchLabels:
      app.kubernetes.io/component: api
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics

---
# PrometheusRule for alerting
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: api-alerts
  namespace: ipa-platform-monitoring
  labels:
    monitoring: enabled
spec:
  groups:
  - name: api-service-alerts
    interval: 30s
    rules:
    - alert: HighErrorRate
      expr: |
        sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
        /
        sum(rate(http_requests_total[5m])) by (service)
        > 0.05
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High error rate detected on {{ $labels.service }}"
        description: "Error rate is {{ $value | humanizePercentage }}"
    
    - alert: HighLatency
      expr: |
        histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (service, le))
        > 1
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "High latency detected on {{ $labels.service }}"
        description: "P95 latency is {{ $value }}s"
```

#### 子任務
1. [ ] 部署 Prometheus Operator
2. [ ] 部署 Prometheus instances
3. [ ] 部署 Grafana
4. [ ] 配置 Prometheus data source in Grafana
5. [ ] 創建 Kubernetes cluster 儀表板
6. [ ] 創建 API metrics 儀表板
7. [ ] 配置 Alertmanager
8. [ ] 創建告警規則
9. [ ] 設置告警通知渠道（Email, Slack）
10. [ ] 編寫監控文檔

#### 測試計劃
- 驗證 Prometheus 可以抓取 metrics
- 測試 Grafana 儀表板顯示正常
- 觸發測試告警驗證通知機制
- 驗證數據保留期設置

---

### S0-9: Logging Infrastructure
**Story Points**: 5  
**優先級**: P1 - High  
**負責人**: DevOps  
**依賴**: S0-2

#### 描述
建立 ELK (Elasticsearch, Logstash, Kibana) 棧用於集中式日誌管理，配置日誌收集和分析。

#### 驗收標準
- [ ] Elasticsearch 部署到 Kubernetes (3 nodes cluster)
- [ ] Kibana 部署並配置
- [ ] Fluentd/Fluent Bit 部署為 DaemonSet
- [ ] 配置日誌收集規則
  - 收集所有 Pod stdout/stderr
  - 解析 JSON 格式日誌
  - 添加 Kubernetes metadata
- [ ] 創建 Kibana 索引模式
- [ ] 創建初始日誌儀表板
- [ ] 配置日誌保留策略（30 天）
- [ ] 實現日誌搜索和過濾功能

#### 技術實現細節
```yaml
# Elasticsearch StatefulSet
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: ipa-platform-monitoring
spec:
  serviceName: elasticsearch
  replicas: 3
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
        env:
        - name: cluster.name
          value: ipa-platform-logs
        - name: node.name
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: discovery.seed_hosts
          value: "elasticsearch-0.elasticsearch,elasticsearch-1.elasticsearch,elasticsearch-2.elasticsearch"
        - name: cluster.initial_master_nodes
          value: "elasticsearch-0,elasticsearch-1,elasticsearch-2"
        - name: ES_JAVA_OPTS
          value: "-Xms2g -Xmx2g"
        ports:
        - containerPort: 9200
          name: http
        - containerPort: 9300
          name: transport
        volumeMounts:
        - name: data
          mountPath: /usr/share/elasticsearch/data
        resources:
          requests:
            memory: 4Gi
            cpu: 1000m
          limits:
            memory: 6Gi
            cpu: 2000m
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 200Gi

---
# Fluent Bit DaemonSet
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: ipa-platform-monitoring
spec:
  selector:
    matchLabels:
      app: fluent-bit
  template:
    metadata:
      labels:
        app: fluent-bit
    spec:
      serviceAccountName: fluent-bit
      containers:
      - name: fluent-bit
        image: fluent/fluent-bit:2.2
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
        - name: fluent-bit-config
          mountPath: /fluent-bit/etc/
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
      - name: fluent-bit-config
        configMap:
          name: fluent-bit-config
```

```csharp
// Structured logging with Serilog
public static class LoggingExtensions
{
    public static IServiceCollection AddIpaLogging(this IServiceCollection services, IConfiguration configuration)
    {
        Log.Logger = new LoggerConfiguration()
            .ReadFrom.Configuration(configuration)
            .Enrich.FromLogContext()
            .Enrich.WithProperty("Application", "IPA-Platform")
            .Enrich.WithProperty("Environment", Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT"))
            .Enrich.WithMachineName()
            .Enrich.WithThreadId()
            .WriteTo.Console(new JsonFormatter())
            .WriteTo.Elasticsearch(new ElasticsearchSinkOptions(new Uri(configuration["Elasticsearch:Uri"]))
            {
                AutoRegisterTemplate = true,
                IndexFormat = "ipa-platform-logs-{0:yyyy.MM.dd}",
                NumberOfReplicas = 1,
                NumberOfShards = 2
            })
            .CreateLogger();
        
        services.AddLogging(loggingBuilder =>
        {
            loggingBuilder.ClearProviders();
            loggingBuilder.AddSerilog(dispose: true);
        });
        
        return services;
    }
}
```

#### 子任務
1. [ ] 部署 Elasticsearch cluster
2. [ ] 部署 Kibana
3. [ ] 部署 Fluent Bit DaemonSet
4. [ ] 創建 Fluent Bit 配置
5. [ ] 配置 Elasticsearch 索引模板
6. [ ] 創建 Kibana 索引模式
7. [ ] 創建日誌儀表板
8. [ ] 配置日誌保留策略（ILM）
9. [ ] 實現應用程序 structured logging
10. [ ] 編寫日誌查詢文檔

#### 測試計劃
- 驗證日誌可以正常收集到 Elasticsearch
- 測試 Kibana 搜索功能
- 驗證 Kubernetes metadata 正確添加
- 測試日誌保留策略自動刪除舊日誌

---

## 📈 Sprint Metrics

### 每日站會議程
- **時間**: 每天上午 10:00
- **時長**: 15 分鐘
- **議程**:
  1. 昨天完成了什麼？
  2. 今天計劃做什麼？
  3. 有什麼阻礙？

### 燃盡圖目標
- 第 1 天: 42 點
- 第 5 天: 25 點 (完成 40%)
- 第 10 天: 0 點 (完成 100%)

### 速度目標
- **計劃速度**: 42 story points
- **目標完成率**: 100% (所有 P0 任務必須完成)

---

## 🚨 風險和緩解策略

### 高風險項目

#### 風險 1: Kubernetes 集群配置延遲
- **嚴重性**: 高
- **概率**: 中
- **影響**: 阻礙所有依賴 K8s 的任務（S0-3, S0-4, S0-5, S0-6, S0-8, S0-9）
- **緩解**:
  - 第一天立即開始 AKS provisioning
  - 使用 Azure 免費額度快速實驗
  - 準備備用方案（使用 Minikube 本地測試）

#### 風險 2: 團隊對新基礎設施的學習曲線
- **嚴重性**: 中
- **概率**: 高
- **影響**: 任務完成時間超過預估
- **緩解**:
  - Sprint 開始前安排 Kubernetes 培訓
  - 創建詳細的設置文檔和故障排除指南
  - Pair programming 讓有經驗的成員帶新成員

#### 風險 3: Azure 資源成本超出預算
- **嚴重性**: 中
- **概率**: 低
- **影響**: 需要重新評估資源配置
- **緩解**:
  - 設置 Azure cost alerts
  - 每天監控資源使用情況
  - Staging 環境使用較小的節點規格

---

## ✅ Definition of Done

### Code Quality
- [ ] Code reviewed and approved by at least one team member
- [ ] All linting rules passed
- [ ] No critical security vulnerabilities (Trivy scan)
- [ ] Infrastructure as Code (IaC) for all deployments

### Functionality
- [ ] Feature meets acceptance criteria
- [ ] Deployed to Staging environment
- [ ] Smoke tests passed
- [ ] Health check endpoints responding

### Documentation
- [ ] Setup guide created/updated
- [ ] Architecture diagrams updated
- [ ] Troubleshooting guide available
- [ ] Runbook for operations team

### Testing
- [ ] Integration tests for critical paths
- [ ] Manual testing by QA
- [ ] Performance baseline established

---

## 📝 Sprint Retrospective Topics

在 Sprint 結束時，團隊應該討論以下問題：

1. **做得好的地方**:
   - 哪些流程運作良好？
   - 哪些決策是正確的？

2. **需要改進的地方**:
   - 遇到了哪些障礙？
   - 哪些任務估算不準確？

3. **行動項目**:
   - 下一個 Sprint 要改變什麼？
   - 需要什麼額外的工具或培訓？

---

## 📚 參考資源

### 文檔
- [Azure Kubernetes Service Documentation](https://docs.microsoft.com/azure/aks/)
- [Kubernetes Official Docs](https://kubernetes.io/docs/)
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [PostgreSQL 16 Release Notes](https://www.postgresql.org/docs/16/)
- [Redis 7 Documentation](https://redis.io/docs/)
- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)

### 內部文檔
- [IPA Platform Technical Architecture](../02-architecture/technical-architecture.md)
- [IPA Platform PRD](../01-planning/prd/prd-features-1-7.md)
- [BMM Workflow Status](../bmm-workflow-status.yaml)

### 工具
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Docker Compose CLI Reference](https://docs.docker.com/compose/reference/)
- [Azure CLI Reference](https://docs.microsoft.com/cli/azure/)

---

**狀態**: Not Started  
**上次更新**: 2025-11-19  
**更新人**: GitHub Copilot
