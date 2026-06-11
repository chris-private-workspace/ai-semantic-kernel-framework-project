# S0-9: Application Insights Logging 完成總結

**Story ID**: S0-9
**Story Points**: 3
**完成日期**: 2025-11-20
**負責人**: DevOps Team

---

## 📋 目標達成情況

✅ **主要目標**: 配置 Application Insights 集中式日誌記錄和追蹤

### 已完成項目

| 項目 | 狀態 | 說明 |
|-----|------|------|
| 結構化日誌系統 | ✅ | StructuredFormatter + get_logger |
| 日誌輔助工具 | ✅ | log_function_call 裝飾器 |
| KQL 查詢範例 | ✅ | 30+ 個常用查詢 |
| 日誌最佳實踐 | ✅ | 完整的指南文檔 |
| 主應用整合 | ✅ | main.py 使用結構化日誌 |

---

## 📁 新增文件

### 核心實現文件

1. **結構化日誌模組** (`backend/src/core/logging/`)
   - `structured_logger.py` (251 行) - 結構化日誌配置
   - `__init__.py` - 模組導出

### 文檔文件

1. **KQL 查詢範例**: `docs/04-usage/logging-queries.md` (~500 行)
   - 基本查詢
   - 錯誤和異常分析
   - 性能分析
   - 用戶行為分析
   - 依賴關係分析
   - 自定義查詢

2. **日誌最佳實踐**: `docs/04-usage/logging-best-practices.md` (~400 行)
   - 日誌級別使用指南
   - 結構化日誌規範
   - 安全注意事項
   - 性能考慮
   - 常見模式

3. **實現總結**: `docs/03-implementation/S0-9-logging-summary.md` (本文檔)

### 配置更新

1. **主應用**: `backend/main.py` (使用結構化日誌)

---

## 🔧 技術實現細節

### 1. 結構化日誌系統

#### StructuredFormatter

```python
class StructuredFormatter(logging.Formatter):
    """自動添加上下文信息"""

    def format(self, record: logging.LogRecord) -> str:
        # 添加環境、服務名、版本
        record.environment = settings.environment
        record.service_name = settings.app_name
        record.version = settings.app_version
        return super().format(record)
```

**功能**:
- ✅ 自動添加環境信息
- ✅ 統一日誌格式
- ✅ 支持自定義字段

#### 日誌配置

```python
def configure_logging(log_level: Optional[str] = None) -> None:
    """配置應用程序日誌"""

    # 統一格式
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "[%(environment)s] [%(service_name)s:%(version)s] - "
        "%(message)s"
    )

    # 配置處理器
    logging.basicConfig(
        level=log_level or settings.log_level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )
```

### 2. 日誌輔助工具

#### get_logger 函數

```python
def get_logger(name: str, **kwargs) -> logging.Logger:
    """
    獲取帶上下文的日誌記錄器

    Example:
        logger = get_logger(__name__, user_id="123", request_id="abc")
        logger.info("Processing request")
        # 自動包含 user_id 和 request_id
    """
    logger = logging.getLogger(name)
    if kwargs:
        logger = logging.LoggerAdapter(logger, kwargs)
    return logger
```

#### log_function_call 裝飾器

```python
@log_function_call
async def process_workflow(workflow_id: str):
    """自動記錄函數進入、退出和異常"""
    # 業務邏輯
    pass

# 自動生成日誌:
# - Entering process_workflow (args, kwargs)
# - Exiting process_workflow (duration, status)
# - Exception in process_workflow (if error)
```

**功能**:
- ✅ 自動記錄函數進入/退出
- ✅ 測量執行時間
- ✅ 記錄異常和堆棧
- ✅ 支持異步函數

#### ContextLogger

```python
with ContextLogger(user_id="123", request_id="abc") as logger:
    logger.info("Processing request")
    # 所有日誌自動包含上下文
```

---

## 📊 KQL 查詢範例亮點

### 基本查詢

```kusto
# 查看最近的日誌
traces
| where timestamp > ago(1h)
| order by timestamp desc
| take 100
```

### 性能分析

```kusto
# 慢請求分析
requests
| where timestamp > ago(24h)
| where duration > 2000  // > 2 秒
| order by duration desc
| project timestamp, name, url, duration
```

### 錯誤分析

```kusto
# 異常趨勢
exceptions
| where timestamp > ago(7d)
| summarize count() by bin(timestamp, 1h), type
| render timechart
```

### 自定義查詢

```kusto
# 工作流執行日誌
traces
| where message contains "workflow"
| extend workflow_id = tostring(customDimensions.workflow_id)
| where isnotempty(workflow_id)
| project timestamp, workflow_id, message
```

---

## 📖 日誌最佳實踐亮點

### 日誌級別使用

| 級別 | 使用場景 | 範例 |
|------|---------|------|
| DEBUG | 詳細診斷 | 函數進入/退出 |
| INFO | 重要業務流程 | 工作流開始/完成 |
| WARNING | 警告但不影響運行 | 使用棄用功能 |
| ERROR | 錯誤影響功能 | API 調用失敗 |
| CRITICAL | 嚴重錯誤 | 數據庫連接失敗 |

### 安全規範

**絕對不能記錄**:
- ❌ 密碼
- ❌ API 密鑰
- ❌ Token
- ❌ 信用卡號

**✅ 正確做法**:
```python
# 只記錄非敏感信息
logger.info("User login", extra={"user_id": user.id})

# 或者脫敏
logger.info("Email", extra={"email_domain": email.split("@")[1]})
```

### 結構化日誌規範

```python
# ✅ 好：使用 extra 添加結構化數據
logger.info(
    "Request processed",
    extra={
        "request_id": "abc123",
        "user_id": "user_456",
        "duration_ms": 150.5,
        "status": "success"
    }
)

# ❌ 差：所有信息都在消息中
logger.info("Request abc123 by user_456 took 150.5ms - success")
```

---

## 🔄 與其他 Stories 的集成

### 依賴關係

| Story | 關係 | 說明 |
|-------|------|------|
| S0-2 (App Service) | ✅ 已完成 | 部署平台 |
| S0-8 (Monitoring) | ✅ 已完成 | Application Insights 配置 |

### 被依賴

| Story | 如何使用 | 說明 |
|-------|---------|------|
| 所有未來 Stories | 日誌記錄 | 使用結構化日誌系統 |
| 業務監控 | KQL 查詢 | 分析業務指標 |

---

## 📊 代碼統計

### 新增代碼量

| 類別 | 文件數 | 代碼行數 |
|------|--------|----------|
| 結構化日誌 | 2 | 251 |
| 配置更新 | 1 | ~10 |
| **總計** | **3** | **~261** |

### 文檔

| 類別 | 文件數 | 字數 (估計) |
|------|--------|--------------|
| KQL 查詢 | 1 | ~4,000 |
| 最佳實踐 | 1 | ~3,500 |
| 實現總結 | 1 | ~1,500 |
| **總計** | **3** | **~9,000** |

---

## 📝 使用範例

### 基本使用

```python
from src.core.logging import get_logger

logger = get_logger(__name__)

# INFO 級別
logger.info(
    "Workflow execution started",
    extra={
        "workflow_id": workflow_id,
        "user_id": user_id
    }
)

# ERROR 級別 with 異常
try:
    result = await risky_operation()
except Exception as e:
    logger.error(
        "Operation failed",
        extra={
            "operation": "risky_operation",
            "error_type": type(e).__name__
        },
        exc_info=True  # 包含堆棧追蹤
    )
```

### 函數追蹤

```python
from src.core.logging import log_function_call

@log_function_call
async def process_workflow(workflow_id: str):
    # 自動記錄:
    # - Entering process_workflow
    # - Exiting process_workflow (duration_ms, status)
    # - Exception (if any)

    result = await execute_workflow(workflow_id)
    return result
```

### 帶上下文的日誌

```python
from src.core.logging import get_logger

# 創建帶默認上下文的日誌器
logger = get_logger(__name__, request_id=request_id, user_id=user_id)

# 所有日誌自動包含 request_id 和 user_id
logger.info("Starting process")
logger.info("Process completed")
```

---

## 🎯 Application Insights 查詢

### 查看結構化日誌

```kusto
traces
| where timestamp > ago(1h)
| extend
    workflow_id = tostring(customDimensions.workflow_id),
    user_id = tostring(customDimensions.user_id),
    duration_ms = toreal(customDimensions.duration_ms)
| project timestamp, message, workflow_id, user_id, duration_ms
```

### 工作流性能分析

```kusto
traces
| where message contains "workflow"
| extend duration_ms = toreal(customDimensions.duration_ms)
| summarize
    count(),
    avg(duration_ms),
    percentile(duration_ms, 95)
    by tostring(customDimensions.workflow_id)
```

---

## ✅ 驗收標準

| 標準 | 狀態 | 說明 |
|------|------|------|
| 結構化日誌配置 | ✅ | StructuredFormatter + get_logger |
| 日誌輔助工具 | ✅ | log_function_call 裝飾器 |
| KQL 查詢範例 | ✅ | 30+ 個查詢範例 |
| 最佳實踐文檔 | ✅ | 完整的使用指南 |
| 安全規範 | ✅ | 敏感數據保護指南 |
| 主應用整合 | ✅ | main.py 使用結構化日誌 |

---

## 🎉 Sprint 0 完成！

**S0-9 完成**: Sprint 0 所有 Story 已完成！

| Story | Points | 狀態 |
|-------|--------|------|
| S0-1: Development Environment | 5 | ✅ |
| S0-2: Azure App Service | 5 | ✅ |
| S0-3: CI/CD Pipeline | 5 | ✅ |
| S0-4: Database Infrastructure | 5 | ✅ |
| S0-5: Redis Cache | 3 | ✅ |
| S0-6: Message Queue | 3 | ✅ |
| S0-7: Authentication Framework | 8 | ✅ |
| S0-8: Monitoring Setup | 5 | ✅ |
| S0-9: Application Insights Logging | 3 | ✅ |

**總計**: 42/38 分 (110.5%) 🎉

---

## 📖 相關文檔

- [KQL 查詢範例](../04-usage/logging-queries.md)
- [日誌最佳實踐](../04-usage/logging-best-practices.md)
- [監控使用指南](../04-usage/monitoring-guide.md)
- [Sprint Status](./sprint-status.yaml)

---

**狀態**: ✅ **已完成**
**完成時間**: 2025-11-20
**總代碼量**: ~261 行
**總文檔量**: ~9,000 字

---

**🎊 Sprint 0 完成！準備進入 Sprint 1！**
