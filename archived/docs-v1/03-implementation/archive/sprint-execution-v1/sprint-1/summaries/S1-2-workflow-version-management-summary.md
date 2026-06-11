# S1-2: Workflow Service - Version Management 實現指南

**Story ID**: S1-2
**Story Points**: 5
**Priority**: P0 - Critical
**Dependencies**: S1-1 (Workflow Service - Core CRUD)

---

## 📋 Story 描述

實現工作流版本管理功能,包括版本創建、查詢、回滾和比較。確保工作流的每次變更都被追踪,並支持回滾到任意歷史版本。

---

## ✅ 驗收標準

1. ✅ **版本自動創建**: 每次更新 workflow 時自動創建新版本
2. ✅ **版本號自增**: 版本號從 1 開始,每次自動遞增
3. ✅ **版本列表查詢**: 可查詢 workflow 的所有歷史版本
4. ✅ **版本詳情查詢**: 可獲取特定版本的完整定義
5. ✅ **版本回滾**: 可將 workflow 回滾到任意歷史版本
6. ✅ **變更摘要**: 每個版本包含變更說明
7. ✅ **當前版本標記**: Workflow 模型正確追踪 current_version_id
8. ✅ **版本比較**: 可比較兩個版本的差異
9. ✅ **創建者追踪**: 記錄每個版本的創建者
10. ✅ **API 認證**: 所有 endpoints 需要身份驗證

---

## 🏗️ 技術架構

### 數據模型 (已存在)

**WorkflowVersion** 模型:
```python
class WorkflowVersion(Base, UUIDMixin, TimestampMixin):
    workflow_id: UUID          # 所屬 workflow
    version_number: int        # 版本號 (1, 2, 3, ...)
    definition: JSONB          # 完整的 workflow 定義
    change_summary: str        # 變更摘要
    created_by: UUID           # 創建者
    created_at: datetime       # 創建時間
```

**Workflow** 模型關聯:
```python
class Workflow:
    current_version_id: UUID   # 當前版本 ID
    versions: List[WorkflowVersion]  # 所有版本
    current_version: WorkflowVersion  # 當前版本對象
```

### API Endpoints 設計

| Method | Path | 功能 | 請求 | 響應 |
|--------|------|------|------|------|
| GET | /api/v1/workflows/{id}/versions | 獲取版本列表 | - | VersionListResponse |
| GET | /api/v1/workflows/{id}/versions/{version} | 獲取特定版本 | - | VersionResponse |
| POST | /api/v1/workflows/{id}/versions/rollback | 回滾到指定版本 | RollbackRequest | WorkflowResponse |
| GET | /api/v1/workflows/{id}/versions/compare | 比較兩個版本 | v1, v2 query params | VersionCompareResponse |
| POST | /api/v1/workflows/{id}/versions | 手動創建版本快照 | VersionCreateRequest | VersionResponse |

---

## 📝 實現任務

### Task 1: 擴展 Pydantic Schemas

**文件**: `backend/src/domain/workflows/schemas.py`

新增 Schemas:
```python
class VersionResponse(BaseModel):
    """版本響應 schema"""
    id: UUID
    workflow_id: UUID
    version_number: int
    definition: dict[str, Any]  # Complete workflow definition
    change_summary: Optional[str]
    created_by: UUID
    created_at: datetime

class VersionListResponse(BaseModel):
    """版本列表響應"""
    items: List[VersionResponse]
    total: int
    current_version_id: Optional[UUID]

class VersionCreateRequest(BaseModel):
    """手動創建版本請求"""
    change_summary: str = Field(..., min_length=1, max_length=500)

class RollbackRequest(BaseModel):
    """版本回滾請求"""
    version_number: int = Field(..., gt=0, description="回滾到的版本號")
    change_summary: Optional[str] = Field(None, max_length=500)

class VersionCompareResponse(BaseModel):
    """版本比較響應"""
    version1: VersionResponse
    version2: VersionResponse
    differences: dict[str, Any]  # JSON diff
```

### Task 2: 創建 WorkflowVersionRepository

**文件**: `backend/src/infrastructure/database/repositories/workflow_version_repository.py`

實現方法:
```python
class WorkflowVersionRepository:
    async def create_version(
        self,
        workflow: Workflow,
        created_by: UUID,
        change_summary: Optional[str] = None
    ) -> WorkflowVersion:
        """創建新版本 (自動遞增版本號)"""

    async def get_by_workflow_id(
        self,
        workflow_id: UUID
    ) -> List[WorkflowVersion]:
        """獲取 workflow 的所有版本 (按版本號倒序)"""

    async def get_by_version_number(
        self,
        workflow_id: UUID,
        version_number: int
    ) -> Optional[WorkflowVersion]:
        """獲取特定版本"""

    async def get_latest_version_number(
        self,
        workflow_id: UUID
    ) -> int:
        """獲取最新版本號"""

    async def count_versions(
        self,
        workflow_id: UUID
    ) -> int:
        """統計版本數量"""
```

### Task 3: 修改 WorkflowRepository 支持版本管理

**文件**: `backend/src/infrastructure/database/repositories/workflow_repository.py`

修改 `update()` 方法:
```python
async def update(
    self,
    workflow: Workflow,
    workflow_data: WorkflowUpdate,
    created_by: UUID,
    change_summary: Optional[str] = None
) -> Workflow:
    """
    更新 workflow 並自動創建新版本

    Steps:
    1. 獲取當前 workflow 完整定義
    2. 應用更新
    3. 創建新版本 (包含完整定義)
    4. 更新 workflow.current_version_id
    5. 返回更新後的 workflow
    """
```

### Task 4: 實現版本管理 API Routes

**文件**: `backend/src/api/v1/workflows/versions.py` (新建)

```python
from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter()

@router.get("/{workflow_id}/versions", response_model=VersionListResponse)
async def list_versions(workflow_id: UUID, ...):
    """獲取 workflow 的所有版本"""

@router.get("/{workflow_id}/versions/{version_number}", response_model=VersionResponse)
async def get_version(workflow_id: UUID, version_number: int, ...):
    """獲取特定版本詳情"""

@router.post("/{workflow_id}/versions/rollback", response_model=WorkflowResponse)
async def rollback_version(workflow_id: UUID, request: RollbackRequest, ...):
    """回滾到指定版本"""

@router.get("/{workflow_id}/versions/compare", response_model=VersionCompareResponse)
async def compare_versions(
    workflow_id: UUID,
    version1: int = Query(..., gt=0),
    version2: int = Query(..., gt=0),
    ...
):
    """比較兩個版本的差異"""

@router.post("/{workflow_id}/versions", response_model=VersionResponse)
async def create_version_snapshot(
    workflow_id: UUID,
    request: VersionCreateRequest,
    ...
):
    """手動創建當前狀態的版本快照"""
```

### Task 5: 實現版本比較邏輯

**文件**: `backend/src/domain/workflows/version_differ.py` (新建)

```python
from typing import Dict, Any
import json

class VersionDiffer:
    """版本差異比較工具"""

    @staticmethod
    def compare(version1_def: Dict, version2_def: Dict) -> Dict[str, Any]:
        """
        比較兩個版本定義的差異

        Returns:
            {
                "added": {...},      # 新增的欄位
                "removed": {...},    # 刪除的欄位
                "modified": {...},   # 修改的欄位
                "unchanged": {...}   # 未改變的欄位
            }
        """
```

### Task 6: 整合到 Workflows Router

**文件**: `backend/src/api/v1/workflows/routes.py`

修改:
```python
# 導入版本 router
from .versions import router as versions_router

# 包含版本子路由
router.include_router(
    versions_router,
    tags=["Workflow Versions"]
)
```

---

## 🧪 測試計劃

### 單元測試

**測試文件**: `backend/tests/integration/test_workflow_versions.py`

測試場景:
1. **版本自動創建**:
   - 更新 workflow → 驗證新版本創建
   - 版本號正確遞增

2. **版本列表查詢**:
   - 創建多個版本 → 驗證列表完整
   - 驗證排序 (最新在前)

3. **版本詳情查詢**:
   - 查詢特定版本 → 驗證定義正確
   - 查詢不存在版本 → 404

4. **版本回滾**:
   - 回滾到舊版本 → 驗證 workflow 狀態恢復
   - 回滾創建新版本 → 驗證版本號遞增

5. **版本比較**:
   - 比較兩個版本 → 驗證差異正確
   - 無差異情況 → 空差異對象

6. **手動快照**:
   - 創建快照 → 驗證版本創建成功
   - 變更摘要記錄正確

### 集成測試腳本

**腳本**: `backend/scripts/test_workflow_versions_api.py`

完整流程測試:
1. 創建 workflow (版本 1 自動創建)
2. 更新 workflow 3 次 (版本 2, 3, 4)
3. 列出所有版本 (驗證 4 個版本)
4. 獲取版本 2 詳情
5. 比較版本 1 和版本 4
6. 回滾到版本 2 (創建版本 5)
7. 驗證 current_version_id 正確

---

## 🎯 技術決策

### 1. 版本創建時機

**決策**: 每次 `PUT /workflows/{id}` 更新時自動創建版本

**理由**:
- 自動化,無需用戶手動管理
- 確保所有變更都被追踪
- 提供手動快照 API 作為補充

### 2. 版本定義內容

**決策**: 存儲完整的 workflow 定義 (包括所有欄位)

**定義結構**:
```json
{
  "name": "Workflow Name",
  "description": "...",
  "status": "active",
  "trigger_type": "manual",
  "trigger_config": {...},
  "tags": ["tag1", "tag2"]
}
```

**理由**:
- 可以完整恢復到任意版本
- 簡化回滾邏輯
- 便於版本比較

### 3. 版本號策略

**決策**: 單調遞增整數,從 1 開始

**規則**:
- 每個 workflow 獨立計數
- 版本號永不重用
- 即使刪除版本,號碼也不回收

### 4. 回滾邏輯

**決策**: 回滾 = 創建新版本 (而非刪除後續版本)

**流程**:
```
當前: v4
回滾到: v2
結果: 創建 v5 (內容 = v2 的內容)
```

**理由**:
- 保留完整歷史
- 可回滾的回滾
- 符合不可變數據原則

### 5. 版本比較算法

**決策**: 使用遞歸 JSON diff

**實現**: 逐層比較對象,標記 added/removed/modified

---

## 📚 API 示例

### 1. 列出版本

```http
GET /api/v1/workflows/{workflow_id}/versions
Authorization: Bearer <token>

Response 200:
{
  "items": [
    {
      "id": "uuid-v4",
      "workflow_id": "uuid-wf",
      "version_number": 4,
      "definition": {...},
      "change_summary": "Updated trigger config",
      "created_by": "uuid-user",
      "created_at": "2025-11-21T14:00:00Z"
    },
    ...
  ],
  "total": 4,
  "current_version_id": "uuid-v4"
}
```

### 2. 獲取特定版本

```http
GET /api/v1/workflows/{workflow_id}/versions/2
Authorization: Bearer <token>

Response 200:
{
  "id": "uuid-v2",
  "workflow_id": "uuid-wf",
  "version_number": 2,
  "definition": {
    "name": "My Workflow",
    "trigger_type": "manual",
    ...
  },
  "change_summary": "Initial version",
  "created_by": "uuid-user",
  "created_at": "2025-11-21T12:00:00Z"
}
```

### 3. 回滾版本

```http
POST /api/v1/workflows/{workflow_id}/versions/rollback
Authorization: Bearer <token>
Content-Type: application/json

{
  "version_number": 2,
  "change_summary": "Rollback due to bug in v4"
}

Response 200:
{
  "id": "uuid-wf",
  "name": "My Workflow",
  "current_version_id": "uuid-v5",  // New version created
  ...
}
```

### 4. 比較版本

```http
GET /api/v1/workflows/{workflow_id}/versions/compare?version1=2&version2=4
Authorization: Bearer <token>

Response 200:
{
  "version1": {...},
  "version2": {...},
  "differences": {
    "modified": {
      "trigger_config": {
        "old": {...},
        "new": {...}
      }
    },
    "added": {},
    "removed": {}
  }
}
```

### 5. 創建快照

```http
POST /api/v1/workflows/{workflow_id}/versions
Authorization: Bearer <token>
Content-Type: application/json

{
  "change_summary": "Manual snapshot before major update"
}

Response 201:
{
  "id": "uuid-new-version",
  "version_number": 5,
  ...
}
```

---

## ⚠️ 注意事項

### 數據一致性

1. **事務管理**: 更新 workflow + 創建版本必須在同一事務中
2. **current_version_id 同步**: 確保始終指向最新版本
3. **並發控制**: 使用數據庫鎖防止版本號衝突

### 性能考慮

1. **版本數量限制**: 建議設置最大版本數 (如 100),超過時清理舊版本
2. **定義大小**: 大型 workflow 定義可能影響存儲和查詢性能
3. **索引優化**: 在 (workflow_id, version_number) 上創建唯一索引

### 安全性

1. **權限檢查**: 只有 workflow 創建者或管理員可回滾
2. **審計日誌**: 版本操作應記錄到 audit_logs 表
3. **敏感數據**: 避免在版本定義中存儲密碼等敏感信息

---

## ✅ Definition of Done

- [ ] 所有 5 個 API endpoints 實現並測試
- [ ] 版本自動創建邏輯集成到 workflow 更新流程
- [ ] 版本比較功能正常工作
- [ ] 回滾功能完整且正確
- [ ] 所有測試通過 (單元 + 集成)
- [ ] API 文檔完整 (OpenAPI)
- [ ] 代碼審查通過
- [ ] 無 P0/P1 bugs

---

**文檔創建日期**: 2025-11-21
**負責人**: Backend Team
**預計完成時間**: 1-2 天
