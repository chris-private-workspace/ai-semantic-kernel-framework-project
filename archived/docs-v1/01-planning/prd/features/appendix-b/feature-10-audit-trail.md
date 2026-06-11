# Feature 10: 審計追蹤（追加式日誌）

**版本**: 1.0  
**日期**: 2025-11-19  
**狀態**: 草稿

---

## 📑 導航

- [← 返回附錄 B 索引](../../prd-appendix-b-features-8-14.md)
- [← 上一個: Feature 09 - 提示管理](./feature-9-prompt-management.md)
- [→ 下一個: Feature 11 - Teams 通知](./feature-11-teams-notification.md)

---

## <a id="f10-audit-trail"></a>F10. 審計追蹤（追加式日誌）

**功能類別**: Observability (可觀察性)  
**優先級**: P0 (必須擁有)  
**估計開發時間**: 1 週  
**複雜度**: ⭐⭐⭐

---

### 10.1 功能概述

**定義**:
F10（審計追蹤）提供**不可篡改的追加式日誌系統**，記錄所有用戶操作、配置變更、執行結果，用於合規審計、安全調查、問題排查。所有日誌按時間順序存儲，支持全文搜索和高級過濾。

**為什麼重要**:
- **合規要求**: SOX、GDPR、HIPAA 等法規要求完整的審計日誌
- **安全調查**: 快速追溯可疑操作（如未授權訪問、配置篡改）
- **問題排查**: 重現問題現場，分析執行失敗的根本原因
- **責任追蹤**: 明確每個操作的執行者和時間

**核心能力**:
1. **追加式存儲**: 日誌只能寫入，不能修改或刪除（防篡改）
2. **完整記錄**: 操作前/後狀態快照、用戶身份、IP 地址、時間戳
3. **分類存儲**: 用戶操作、系統事件、執行日誌、配置變更
4. **全文搜索**: Elasticsearch 支持快速搜索（關鍵詞、時間範圍、用戶）
5. **自動歸檔**: 90 天後自動歸檔至冷存儲（S3/Azure Blob）
6. **完整性校驗**: SHA-256 哈希鏈確保日誌未被篡改

**業務價值**:
- **合規成本**: 減少審計準備時間 80%（從 5 天降至 1 天）
- **安全事件響應**: 從 4 小時縮短至 30 分鐘
- **問題排查**: 平均定位時間從 2 小時降至 15 分鐘

**架構圖**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        F10. 審計追蹤架構                               │
└────────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────────┐
   │                      應用層（所有操作）                         │
   │  • 用戶操作（登錄、創建工作流、修改配置）                      │
   │  • 系統事件（執行開始、執行完成、錯誤）                        │
   │  • API 調用（所有 REST API 請求）                              │
   └───────────────────────┬─────────────────────────────────────────┘
                           │ 記錄審計事件
                           ↓
   ┌─────────────────────────────────────────────────────────────────┐
   │                    審計日誌服務                                 │
   │  • 驗證事件格式                                                 │
   │  • 添加元數據（IP、User-Agent、時間戳）                        │
   │  • 計算哈希鏈（防篡改）                                         │
   └───────┬────────────────────────────┬────────────────────────────┘
           │ 寫入                       │ 寫入
           ↓                            ↓
   ┌──────────────┐            ┌──────────────┐
   │ PostgreSQL   │            │ Elasticsearch│
   │ (結構化存儲) │            │ (全文搜索)  │
   │ audit_logs   │            │ audit-logs-* │
   └──────┬───────┘            └──────┬───────┘
          │                            │
          │ 90 天後歸檔                │ 查詢
          ↓                            ↓
   ┌──────────────┐            ┌──────────────┐
   │ S3 / Azure   │            │ Web UI       │
   │ Blob Storage │            │ (審計查詢)  │
   │ (冷存儲)     │            └──────────────┘
   └──────────────┘
```

---

### 10.2 用戶故事

#### **US-F10-001: 用戶操作日誌記錄**

**優先級**: P0 (必須擁有)  
**估計開發時間**: 2 天  
**複雜度**: ⭐⭐⭐

**用戶故事**:
- **作為** 安全管理員（Tom Wang）
- **我想要** 記錄所有用戶操作（登錄、創建/修改/刪除資源）
- **以便** 我可以在安全事件發生時追溯可疑操作

**驗收標準**:

1. ✅ **登錄日誌**: 記錄成功/失敗的登錄嘗試（用戶名、IP、時間）
2. ✅ **CRUD 操作**: 記錄所有創建/修改/刪除操作（工作流、提示、Agent）
3. ✅ **操作前/後快照**: 保存資源變更前後的完整狀態
4. ✅ **用戶身份**: 記錄操作者的用戶 ID、用戶名、角色
5. ✅ **請求上下文**: IP 地址、User-Agent、請求 ID
6. ✅ **敏感數據脫敏**: 密碼、API Key 等敏感字段自動脫敏

**審計日誌數據結構**:

```json
{
  "id": "audit_abc123",
  "timestamp": "2025-11-19T10:30:45.123Z",
  "event_type": "workflow.update",
  "category": "user_operation",
  "severity": "info",
  
  "actor": {
    "user_id": "user_001",
    "username": "sarah.lin@company.com",
    "role": "admin",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
  },
  
  "resource": {
    "type": "workflow",
    "id": "wf_customer_360",
    "name": "Customer 360 View"
  },
  
  "action": "update",
  "result": "success",
  
  "changes": {
    "before": {
      "status": "active",
      "max_retries": 3,
      "timeout": 300
    },
    "after": {
      "status": "active",
      "max_retries": 5,
      "timeout": 600
    },
    "diff": {
      "max_retries": {"old": 3, "new": 5},
      "timeout": {"old": 300, "new": 600}
    }
  },
  
  "metadata": {
    "request_id": "req_xyz789",
    "session_id": "sess_abc456",
    "correlation_id": "corr_def789"
  },
  
  "hash": "a1b2c3d4e5f6...",
  "previous_hash": "f6e5d4c3b2a1..."
}
```

**Python 實現**:

```python
from fastapi import Request
from datetime import datetime
import hashlib
import json
from typing import Optional, Dict, Any

class AuditLogger:
    """審計日誌記錄器"""
    
    def __init__(self, db_session, es_client):
        self.db = db_session
        self.es = es_client
        self.last_hash = self._get_last_hash()
    
    async def log_user_operation(
        self,
        request: Request,
        event_type: str,
        resource_type: str,
        resource_id: str,
        action: str,
        result: str,
        changes: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """記錄用戶操作"""
        
        # 1. 構建審計事件
        audit_event = {
            "id": f"audit_{self._generate_id()}",
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "category": "user_operation",
            "severity": "error" if result == "failure" else "info",
            
            "actor": {
                "user_id": request.state.user.id,
                "username": request.state.user.username,
                "role": request.state.user.role,
                "ip_address": request.client.host,
                "user_agent": request.headers.get("User-Agent")
            },
            
            "resource": {
                "type": resource_type,
                "id": resource_id
            },
            
            "action": action,
            "result": result,
            
            "changes": self._sanitize_sensitive_data(changes) if changes else None,
            "error": error,
            
            "metadata": {
                "request_id": request.state.request_id,
                "session_id": request.state.session_id
            }
        }
        
        # 2. 計算哈希鏈
        audit_event["previous_hash"] = self.last_hash
        audit_event["hash"] = self._calculate_hash(audit_event)
        self.last_hash = audit_event["hash"]
        
        # 3. 寫入 PostgreSQL（結構化存儲）
        await self._write_to_postgres(audit_event)
        
        # 4. 寫入 Elasticsearch（全文搜索）
        await self._write_to_elasticsearch(audit_event)
    
    def _sanitize_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """脫敏敏感數據"""
        sensitive_fields = ["password", "api_key", "secret", "token"]
        
        sanitized = data.copy()
        for key, value in sanitized.items():
            if any(field in key.lower() for field in sensitive_fields):
                sanitized[key] = "***REDACTED***"
        
        return sanitized
    
    def _calculate_hash(self, event: Dict[str, Any]) -> str:
        """計算事件哈希"""
        # 排除哈希字段本身
        event_copy = {k: v for k, v in event.items() if k not in ["hash", "previous_hash"]}
        event_json = json.dumps(event_copy, sort_keys=True)
        return hashlib.sha256(event_json.encode()).hexdigest()
```

**完成定義**:

- [ ] 用戶操作攔截器（FastAPI Middleware）
- [ ] 審計事件數據模型
- [ ] 敏感數據脫敏邏輯
- [ ] PostgreSQL + Elasticsearch 雙寫
- [ ] 哈希鏈計算（防篡改）

---

#### **US-F10-002: 執行日誌追蹤**

**優先級**: P0 (必須擁有)  
**估計開發時間**: 2 天  
**複雜度**: ⭐⭐⭐

**用戶故事**:
- **作為** DevOps 工程師（Lisa Chen）
- **我想要** 記錄所有工作流執行的詳細日誌（開始、步驟、完成、錯誤）
- **以便** 我可以快速定位執行失敗的根本原因

**驗收標準**:

1. ✅ **執行開始/結束**: 記錄執行 ID、工作流、輸入、輸出
2. ✅ **步驟級日誌**: 記錄每個 Agent 步驟的開始/結束時間、耗時
3. ✅ **LLM 調用日誌**: 記錄提示、響應、Token 數量、成本
4. ✅ **錯誤堆棧**: 完整的錯誤堆棧追蹤
5. ✅ **關聯 ID**: 支持跨服務追蹤（Correlation ID）
6. ✅ **性能指標**: 每個步驟的執行時間、內存使用

**執行日誌結構**:

```json
{
  "id": "audit_exec_001",
  "timestamp": "2025-11-19T10:35:22.456Z",
  "event_type": "execution.step.completed",
  "category": "execution_log",
  "severity": "info",
  
  "execution": {
    "execution_id": "exec_abc123",
    "workflow_id": "wf_customer_360",
    "workflow_name": "Customer 360 View",
    "correlation_id": "corr_xyz789"
  },
  
  "step": {
    "step_id": "step_002",
    "step_name": "query_servicenow",
    "agent_id": "agent_servicenow_query",
    "status": "completed",
    "start_time": "2025-11-19T10:35:20.123Z",
    "end_time": "2025-11-19T10:35:22.456Z",
    "duration_ms": 2333
  },
  
  "llm_call": {
    "model": "gpt-4",
    "prompt_tokens": 450,
    "completion_tokens": 180,
    "total_tokens": 630,
    "cost_usd": 0.0189,
    "latency_ms": 1850
  },
  
  "output": {
    "ticket_count": 15,
    "high_priority_count": 3
  },
  
  "metadata": {
    "memory_mb": 128,
    "cpu_percent": 15.3
  }
}
```

**完成定義**:

- [ ] 執行步驟日誌記錄
- [ ] LLM 調用追蹤
- [ ] 錯誤堆棧捕獲
- [ ] 性能指標收集
- [ ] 關聯 ID 傳播

---

#### **US-F10-003: 審計日誌全文搜索**

**優先級**: P0 (必須擁有)  
**估計開發時間**: 2 天  
**複雜度**: ⭐⭐⭐

**用戶故事**:
- **作為** 合規審計員（Rachel Kim）
- **我想要** 使用關鍵詞、時間範圍、用戶等條件快速搜索審計日誌
- **以便** 我可以在審計時快速找到相關操作記錄

**驗收標準**:

1. ✅ **全文搜索**: 支持關鍵詞搜索（如 "delete workflow"）
2. ✅ **多維過濾**: 按時間範圍、用戶、資源類型、操作類型過濾
3. ✅ **高級查詢**: 支持布林運算（AND、OR、NOT）
4. ✅ **快速響應**: 搜索 100 萬條日誌 <500ms
5. ✅ **結果高亮**: 搜索結果中關鍵詞高亮顯示
6. ✅ **導出報告**: 支持導出為 CSV、JSON、PDF

**審計日誌搜索 UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 審計日誌                                           [導出報告 ▼] [高級搜索]    │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 🔍 搜索                                                                       │
│ ┌───────────────────────────────────────────────────────────────────────┐   │
│ │ delete workflow                                             [搜索]    │   │
│ └───────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│ 📅 時間範圍:  [最近 7 天 ▼]  自定義: [2025-11-12] 至 [2025-11-19]          │
│                                                                               │
│ 👤 用戶:      [所有用戶 ▼]  或輸入: [________________]                       │
│                                                                               │
│ 📦 資源類型:  ☑ 工作流  ☑ Agent  ☑ 提示  ☑ 執行  ☐ 其他                    │
│                                                                               │
│ 🎯 操作類型:  ☑ 創建  ☑ 修改  ☑ 刪除  ☑ 執行  ☐ 其他                        │
│                                                                               │
│ 📊 嚴重程度:  ☑ Info  ☑ Warning  ☑ Error  ☐ Critical                        │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 📋 搜索結果 (共 23 條)                                    按時間倒序 ▼       │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🗑️ 2025-11-19 14:30:22                                                  │ │
│ │ sarah.lin@company.com **deleted** workflow "old_customer_sync"         │ │
│ │ IP: 192.168.1.100 | ID: wf_old_001 | 結果: 成功                        │ │
│ │ [查看詳情]                                                               │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 🗑️ 2025-11-18 09:15:33                                                  │ │
│ │ alex.chen@company.com **deleted** workflow "test_workflow_v1"          │ │
│ │ IP: 10.0.0.50 | ID: wf_test_v1 | 結果: 成功                            │ │
│ │ [查看詳情]                                                               │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ ⚠️ 2025-11-17 16:45:10                                                   │ │
│ │ unknown.user **attempted to delete** workflow "production_workflow"    │ │
│ │ IP: 203.0.113.45 | ID: wf_prod_001 | 結果: 失敗 (權限不足)             │ │
│ │ [查看詳情] [標記為可疑]                                                 │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ [載入更多...]                                                                 │
└───────────────────────────────────────────────────────────────────────────────┘
```

**Elasticsearch 實現**:

```python
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class AuditLogSearchService:
    """審計日誌搜索服務"""
    
    def __init__(self, es_client: Elasticsearch):
        self.es = es_client
        self.index_pattern = "audit-logs-*"
    
    async def search(
        self,
        query: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        users: Optional[List[str]] = None,
        resource_types: Optional[List[str]] = None,
        actions: Optional[List[str]] = None,
        severities: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        搜索審計日誌
        
        返回: {total: int, results: list, took_ms: int}
        """
        
        # 構建 Elasticsearch 查詢
        es_query = {
            "bool": {
                "must": [],
                "filter": []
            }
        }
        
        # 1. 全文搜索
        if query:
            es_query["bool"]["must"].append({
                "multi_match": {
                    "query": query,
                    "fields": [
                        "event_type^2",
                        "action^2",
                        "actor.username",
                        "resource.name",
                        "changes.*",
                        "error"
                    ],
                    "type": "best_fields"
                }
            })
        
        # 2. 時間範圍
        if start_time or end_time:
            time_range = {}
            if start_time:
                time_range["gte"] = start_time.isoformat()
            if end_time:
                time_range["lte"] = end_time.isoformat()
            
            es_query["bool"]["filter"].append({
                "range": {"timestamp": time_range}
            })
        
        # 3. 用戶過濾
        if users:
            es_query["bool"]["filter"].append({
                "terms": {"actor.username": users}
            })
        
        # 4. 資源類型過濾
        if resource_types:
            es_query["bool"]["filter"].append({
                "terms": {"resource.type": resource_types}
            })
        
        # 5. 操作類型過濾
        if actions:
            es_query["bool"]["filter"].append({
                "terms": {"action": actions}
            })
        
        # 6. 嚴重程度過濾
        if severities:
            es_query["bool"]["filter"].append({
                "terms": {"severity": severities}
            })
        
        # 執行搜索
        response = self.es.search(
            index=self.index_pattern,
            body={
                "query": es_query,
                "sort": [{"timestamp": "desc"}],
                "from": (page - 1) * page_size,
                "size": page_size,
                "highlight": {
                    "fields": {
                        "*": {}
                    }
                }
            }
        )
        
        return {
            "total": response["hits"]["total"]["value"],
            "results": [hit["_source"] for hit in response["hits"]["hits"]],
            "highlights": [hit.get("highlight", {}) for hit in response["hits"]["hits"]],
            "took_ms": response["took"]
        }
    
    async def export(
        self,
        format: str,  # csv, json, pdf
        **search_params
    ) -> bytes:
        """導出審計日誌報告"""
        
        # 搜索所有結果（無分頁限制）
        results = await self.search(**search_params, page_size=10000)
        
        if format == "csv":
            return self._export_csv(results["results"])
        elif format == "json":
            return self._export_json(results["results"])
        elif format == "pdf":
            return self._export_pdf(results["results"])
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_csv(self, results: List[Dict]) -> bytes:
        """導出為 CSV"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "timestamp", "user", "action", "resource_type", 
            "resource_id", "result", "ip_address"
        ])
        
        writer.writeheader()
        for result in results:
            writer.writerow({
                "timestamp": result["timestamp"],
                "user": result["actor"]["username"],
                "action": result["action"],
                "resource_type": result["resource"]["type"],
                "resource_id": result["resource"]["id"],
                "result": result["result"],
                "ip_address": result["actor"]["ip_address"]
            })
        
        return output.getvalue().encode('utf-8')
```

**完成定義**:

- [ ] Elasticsearch 全文搜索實現
- [ ] 多維過濾（時間、用戶、資源、操作）
- [ ] 搜索結果高亮
- [ ] 導出功能（CSV、JSON、PDF）
- [ ] 搜索性能優化（<500ms）

---

#### **US-F10-004: 日誌歸檔與完整性校驗**

**優先級**: P1 (重要)  
**估計開發時間**: 2 天  
**複雜度**: ⭐⭐⭐

**用戶故事**:
- **作為** 系統管理員（Mark Lee）
- **我想要** 自動歸檔舊日誌至冷存儲，並確保日誌未被篡改
- **以便** 我可以降低存儲成本並滿足合規要求

**驗收標準**:

1. ✅ **自動歸檔**: 90 天後自動歸檔至 S3/Azure Blob
2. ✅ **壓縮存儲**: 歸檔前壓縮（gzip），減少存儲成本 80%
3. ✅ **哈希鏈校驗**: 定期校驗日誌完整性（SHA-256 哈希鏈）
4. ✅ **篡改檢測**: 檢測到篡改時自動告警
5. ✅ **歸檔檢索**: 支持從歸檔中檢索舊日誌（需 5-10 分鐘）
6. ✅ **保留策略**: 配置不同類型日誌的保留期（如錯誤日誌保留 1 年）

**歸檔策略配置**:

```yaml
# config/audit_retention_policy.yaml
retention_policies:
  - category: "user_operation"
    hot_storage_days: 90      # PostgreSQL + Elasticsearch
    warm_storage_days: 365    # S3 Standard
    cold_storage_days: 2555   # S3 Glacier (7 年)
    
  - category: "execution_log"
    hot_storage_days: 30
    warm_storage_days: 180
    cold_storage_days: 730
    
  - category: "system_event"
    hot_storage_days: 60
    warm_storage_days: 365
    cold_storage_days: 1825

archive_settings:
  compression: "gzip"
  batch_size: 10000          # 每批歸檔 10000 條
  schedule: "0 2 * * *"      # 每天凌晨 2 點執行
  
integrity_check:
  enabled: true
  schedule: "0 3 * * 0"      # 每週日凌晨 3 點
  sample_rate: 0.1           # 隨機抽樣 10% 日誌檢查
```

**Python 實現**:

```python
import gzip
import boto3
from datetime import datetime, timedelta
from typing import List

class AuditLogArchiver:
    """審計日誌歸檔服務"""
    
    def __init__(self, db_session, s3_client: boto3.client):
        self.db = db_session
        self.s3 = s3_client
        self.bucket = "company-audit-logs"
    
    async def archive_old_logs(self, days_threshold: int = 90):
        """歸檔舊日誌"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        # 1. 查詢需要歸檔的日誌
        old_logs = self.db.query(AuditLog).filter(
            AuditLog.timestamp < cutoff_date
        ).limit(10000).all()
        
        if not old_logs:
            return
        
        # 2. 壓縮並上傳至 S3
        archive_file = self._compress_logs(old_logs)
        s3_key = f"audit-logs/{cutoff_date.year}/{cutoff_date.month:02d}/logs_{datetime.utcnow().isoformat()}.json.gz"
        
        self.s3.upload_file(
            Filename=archive_file,
            Bucket=self.bucket,
            Key=s3_key,
            ExtraArgs={
                "StorageClass": "STANDARD_IA",  # 低頻訪問存儲
                "ServerSideEncryption": "AES256"
            }
        )
        
        # 3. 從 PostgreSQL 刪除（已歸檔）
        for log in old_logs:
            self.db.delete(log)
        
        self.db.commit()
        
        logger.info(f"Archived {len(old_logs)} logs to S3: {s3_key}")
    
    def _compress_logs(self, logs: List[AuditLog]) -> str:
        """壓縮日誌"""
        import json
        import tempfile
        
        # 轉換為 JSON
        logs_json = [log.to_dict() for log in logs]
        
        # 寫入臨時文件並壓縮
        temp_file = tempfile.NamedTemporaryFile(suffix=".json.gz", delete=False)
        with gzip.open(temp_file.name, 'wt', encoding='utf-8') as f:
            json.dump(logs_json, f)
        
        return temp_file.name
    
    async def verify_integrity(self, sample_rate: float = 0.1):
        """驗證日誌完整性（哈希鏈）"""
        
        # 1. 隨機抽樣日誌
        total_count = self.db.query(AuditLog).count()
        sample_size = int(total_count * sample_rate)
        
        logs = self.db.query(AuditLog).order_by(
            AuditLog.timestamp
        ).limit(sample_size).all()
        
        # 2. 驗證哈希鏈
        tampered_count = 0
        for i in range(1, len(logs)):
            current_log = logs[i]
            previous_log = logs[i - 1]
            
            # 檢查當前日誌的 previous_hash 是否匹配前一條的 hash
            if current_log.previous_hash != previous_log.hash:
                logger.error(
                    f"Integrity violation detected: Log {current_log.id} "
                    f"has invalid previous_hash"
                )
                tampered_count += 1
            
            # 重新計算當前日誌的哈希
            expected_hash = self._calculate_hash(current_log)
            if current_log.hash != expected_hash:
                logger.error(
                    f"Integrity violation detected: Log {current_log.id} "
                    f"has invalid hash (possibly tampered)"
                )
                tampered_count += 1
        
        if tampered_count > 0:
            # 發送告警
            await self._send_tampering_alert(tampered_count, sample_size)
        
        return {
            "checked": sample_size,
            "tampered": tampered_count,
            "integrity": "OK" if tampered_count == 0 else "VIOLATED"
        }
```

**完成定義**:

- [ ] 自動歸檔任務（定時任務）
- [ ] S3/Azure Blob 上傳
- [ ] gzip 壓縮實現
- [ ] 哈希鏈完整性校驗
- [ ] 篡改檢測告警
- [ ] 歸檔日誌檢索

---

### 10.3 數據庫架構

```sql
-- 審計日誌表（PostgreSQL）
CREATE TABLE audit_logs (
    id VARCHAR(50) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    
    -- 事件分類
    event_type VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,  -- user_operation, execution_log, system_event
    severity VARCHAR(20) NOT NULL,  -- info, warning, error, critical
    
    -- 操作者
    actor_user_id VARCHAR(100),
    actor_username VARCHAR(200),
    actor_role VARCHAR(50),
    actor_ip_address VARCHAR(45),
    actor_user_agent TEXT,
    
    -- 資源
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    resource_name VARCHAR(200),
    
    -- 操作
    action VARCHAR(50),
    result VARCHAR(20),  -- success, failure
    
    -- 變更
    changes_before JSONB,
    changes_after JSONB,
    changes_diff JSONB,
    
    -- 執行上下文（用於執行日誌）
    execution_id VARCHAR(100),
    step_id VARCHAR(50),
    correlation_id VARCHAR(100),
    
    -- 錯誤
    error TEXT,
    
    -- 元數據
    metadata JSONB,
    
    -- 完整性（哈希鏈）
    hash VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64),
    
    -- 歸檔狀態
    archived BOOLEAN DEFAULT false,
    archived_at TIMESTAMP,
    archive_location VARCHAR(500)
);

-- 索引
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_category ON audit_logs(category, timestamp DESC);
CREATE INDEX idx_audit_user ON audit_logs(actor_username, timestamp DESC);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_execution ON audit_logs(execution_id);
CREATE INDEX idx_audit_archived ON audit_logs(archived, timestamp) WHERE NOT archived;

-- 分區表（按月分區，提升查詢性能）
CREATE TABLE audit_logs_2025_11 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

CREATE TABLE audit_logs_2025_12 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');
```

---

### 10.4 非功能需求 (NFR)

| **類別** | **需求** | **目標** | **測量** |
|-------------|----------------|-----------|----------------|
| **性能** | 日誌寫入延遲 | <50ms (異步寫入) | APM 監控 |
| | 搜索響應時間 | <500ms (100 萬條) | Elasticsearch 監控 |
| **容量** | 日誌存儲量 | 支持 10 億條+ | 分區表 + 歸檔 |
| | 寫入吞吐量 | 10000 條/秒 | 批量寫入 + 隊列 |
| **可靠性** | 日誌丟失率 | 0% (持久化) | 雙寫 PostgreSQL + ES |
| | 完整性校驗 | 100% 檢測篡改 | 哈希鏈驗證 |
| **合規** | 日誌保留期 | 7 年（可配置） | 歸檔策略 |

---

### 10.5 測試策略

**單元測試**:

- 哈希鏈計算和驗證
- 敏感數據脫敏邏輯
- 日誌壓縮和解壓縮

**集成測試**:

- 端到端日誌記錄（用戶操作 → 寫入 → 搜索）
- Elasticsearch 全文搜索
- S3 歸檔和檢索

**性能測試**:

- 10000 條/秒寫入壓力測試
- 100 萬條日誌搜索性能測試

**安全測試**:

- 日誌篡改檢測測試
- 敏感數據脫敏驗證

---

### 10.6 風險和緩解

| **風險** | **概率** | **影響** | **緩解** |
|---------|----------------|-----------|---------------|
| Elasticsearch 故障導致搜索不可用 | 中 | 中 | PostgreSQL 降級查詢 + ES 集群 |
| 日誌寫入阻塞主業務 | 低 | 高 | 異步寫入 + 消息隊列 |
| 歸檔日誌檢索緩慢 | 中 | 低 | 設定預期（5-10 分鐘）+ 緩存 |
| 哈希鏈斷裂 | 低 | 高 | 定期完整性檢查 + 告警 |

---

### 10.7 未來增強（MVP 後）

1. **實時日誌流**: WebSocket 實時推送日誌（用於調試）
2. **智能異常檢測**: 使用 ML 檢測異常操作模式
3. **可視化時間線**: 操作時間線可視化（類似 Git log --graph）
4. **跨系統審計**: 集成外部系統日誌（ServiceNow、Active Directory）
5. **區塊鏈存證**: 使用區塊鏈技術進一步增強防篡改能力

---

**✅ F10 完成**：審計追蹤（追加式日誌）功能規範已完整編寫（4 個用戶故事、數據庫架構、NFR、測試策略）。

---
