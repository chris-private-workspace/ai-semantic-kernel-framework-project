# Sprint 114: AD 場景基礎建設

## 概述

Sprint 114 是 Phase 32 的第一個 Sprint，專注於建立 AD 帳號管理業務場景的基礎設施：擴展 PatternMatcher 規則庫、配置 LDAP MCP Server、實現 ServiceNow Webhook 接收器和 RITM→Intent 映射管道。

## 目標

1. 擴展 PatternMatcher 規則庫支援 AD 帳號管理模式
2. 配置 LDAP MCP Server 連接 AD 並驗證基本操作
3. 實現 ServiceNow Webhook 真實接收器
4. 建立 RITM Catalog Item → IPA Business Intent 映射管道

## Story Points: 40 點

## 前置條件

- ✅ Phase 31 完成（Security Hardening — Auth 100%、Mock 分離）
- ✅ LDAP MCP Server 模組存在 (`backend/src/integrations/mcp/`)
- ✅ PatternMatcher 規則引擎就緒 (`backend/src/integrations/orchestration/routing/`)
- ✅ ServiceNow 開發實例可用

## 任務分解

### Story 114-1: PatternMatcher AD 規則庫 (2 天, P0)

**目標**: 擴展 PatternMatcher 的 rules.yaml，新增 AD 帳號管理相關的模式匹配規則

**交付物**:
- 修改 `backend/src/integrations/orchestration/routing/rules.yaml`
- 新增 `backend/tests/unit/orchestration/test_ad_pattern_rules.py`

**規則設計**:

```yaml
# AD 帳號管理規則 — 新增到 rules.yaml
ad_account_management:
  # 帳號鎖定/解鎖
  account_unlock:
    patterns:
      - "unlock account *"
      - "帳號解鎖 *"
      - "account locked out *"
      - "AD 帳號被鎖定 *"
    intent: "ad.account.unlock"
    risk_level: "medium"
    workflow_type: "automated"
    required_tools: ["ldap_mcp"]

  # 密碼重設
  password_reset:
    patterns:
      - "reset password *"
      - "密碼重設 *"
      - "password expired *"
      - "AD 密碼重設 *"
    intent: "ad.password.reset"
    risk_level: "medium"
    workflow_type: "automated_with_approval"
    required_tools: ["ldap_mcp"]

  # 群組成員異動
  group_membership:
    patterns:
      - "add * to group *"
      - "remove * from group *"
      - "群組異動 *"
      - "AD 群組新增成員 *"
      - "AD 群組移除成員 *"
    intent: "ad.group.modify"
    risk_level: "high"
    workflow_type: "approval_required"
    required_tools: ["ldap_mcp"]

  # 帳號建立
  account_create:
    patterns:
      - "create AD account *"
      - "新建 AD 帳號 *"
      - "new user account *"
    intent: "ad.account.create"
    risk_level: "high"
    workflow_type: "approval_required"
    required_tools: ["ldap_mcp"]

  # 帳號停用
  account_disable:
    patterns:
      - "disable account *"
      - "停用帳號 *"
      - "deactivate user *"
    intent: "ad.account.disable"
    risk_level: "high"
    workflow_type: "approval_required"
    required_tools: ["ldap_mcp"]
```

**實現方式**:
- 在現有 rules.yaml 的頂層新增 `ad_account_management` 區塊
- 每條規則包含 patterns（多語言）、intent、risk_level、workflow_type、required_tools
- PatternMatcher 根據 patterns 進行 glob/regex 匹配，匹配成功直接返回 intent

**驗收標準**:
- [ ] rules.yaml 包含 5 個 AD 類別（unlock, reset, group, create, disable）
- [ ] 每個類別至少 3 個 patterns（含中文和英文）
- [ ] intent 命名遵循 `ad.*` 命名空間
- [ ] risk_level 正確分類（medium/high）
- [ ] 單元測試覆蓋所有 AD 規則匹配
- [ ] 不影響現有 34 條規則

### Story 114-2: LDAP MCP Server 配置 (1 天, P0)

**目標**: 配置現有 LDAP MCP Server 連接企業 AD，驗證基本 LDAP 操作

**交付物**:
- 修改 `backend/src/integrations/mcp/ldap_server.py`（或對應配置）
- 新增 `backend/src/integrations/mcp/ldap_config.py`
- 新增 `backend/tests/integration/mcp/test_ldap_connectivity.py`

**配置設計**:

```python
# ldap_config.py
from pydantic import BaseModel
from typing import Optional


class LDAPConfig(BaseModel):
    """LDAP MCP Server 配置"""
    server_url: str  # ldap://ad.company.com:389
    bind_dn: str  # CN=svc-ipa,OU=ServiceAccounts,DC=company,DC=com
    bind_password: str  # 從環境變量讀取
    search_base: str  # DC=company,DC=com
    user_search_base: str  # OU=Users,DC=company,DC=com
    group_search_base: str  # OU=Groups,DC=company,DC=com
    use_ssl: bool = True
    connection_timeout: int = 10
    operation_timeout: int = 30
    pool_size: int = 5
```

**需驗證的 LDAP 操作**:

| 操作 | LDAP Method | 說明 |
|------|-------------|------|
| 帳號查詢 | `search_s()` | 根據 sAMAccountName 查找用戶 |
| 帳號解鎖 | `modify_s()` | 清除 lockoutTime 屬性 |
| 密碼重設 | `modify_s()` | 修改 unicodePwd 屬性 |
| 群組查詢 | `search_s()` | 查詢群組成員 |
| 群組修改 | `modify_s()` | 修改 member 屬性 |

**驗收標準**:
- [ ] LDAP 配置類定義完成
- [ ] 環境變量配置文檔更新（`.env.example`）
- [ ] LDAP 連接測試通過
- [ ] 5 個基本操作驗證通過（查詢、解鎖、重設、群組查詢、群組修改）
- [ ] 連接池正常運作
- [ ] 錯誤處理完整（連接失敗、認證失敗、操作逾時）

### Story 114-3: ServiceNow Webhook 真實實現 (2 天, P0)

**目標**: 實現真實的 ServiceNow Webhook 接收器，處理 RITM（Requested Item）事件

**交付物**:
- 新增 `backend/src/integrations/orchestration/input/servicenow_webhook.py`
- 新增 `backend/src/api/v1/orchestration/webhooks.py`
- 新增 `backend/tests/unit/orchestration/test_servicenow_webhook.py`
- 新增 `backend/tests/integration/orchestration/test_webhook_api.py`

**Webhook Receiver 設計**:

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class ServiceNowRITMEvent(BaseModel):
    """ServiceNow RITM Webhook Payload"""
    sys_id: str
    number: str  # RITM0012345
    state: str  # "1" (Open), "2" (Work in Progress), etc.
    cat_item: str  # Catalog Item sys_id
    cat_item_name: str  # "AD Account Unlock"
    requested_for: str  # 被請求用戶
    requested_by: str  # 請求人
    short_description: str
    description: Optional[str] = None
    variables: Dict[str, Any] = {}  # 表單變量
    priority: str = "3"
    assignment_group: Optional[str] = None
    sys_created_on: Optional[str] = None


class WebhookAuthConfig(BaseModel):
    """Webhook 認證配置"""
    auth_type: str = "shared_secret"  # shared_secret | oauth2 | basic
    shared_secret: Optional[str] = None
    allowed_ips: list[str] = []


class ServiceNowWebhookReceiver:
    """ServiceNow Webhook 接收器"""

    def __init__(self, auth_config: WebhookAuthConfig):
        self._auth_config = auth_config

    async def validate_request(
        self, headers: Dict[str, str], body: bytes
    ) -> bool:
        """驗證 Webhook 請求的真實性"""

    async def parse_ritm_event(
        self, payload: Dict[str, Any]
    ) -> ServiceNowRITMEvent:
        """解析 RITM 事件 payload"""

    async def process_event(
        self, event: ServiceNowRITMEvent
    ) -> Dict[str, Any]:
        """處理 RITM 事件，轉換為 IPA 處理請求"""
```

**API 端點設計**:

```
POST /api/v1/orchestration/webhooks/servicenow
    Headers: X-ServiceNow-Secret: <shared_secret>
    Body: ServiceNowRITMEvent
    Response: { "status": "accepted", "tracking_id": "..." }
```

**驗收標準**:
- [ ] Webhook 接收器實現完成
- [ ] 請求驗證邏輯完成（shared secret / IP 白名單）
- [ ] RITM payload 解析正確
- [ ] 冪等處理（重複事件不重複執行）
- [ ] API 端點註冊且可存取
- [ ] 錯誤處理完整（無效 payload、認證失敗、重複事件）
- [ ] 單元測試和整合測試通過

### Story 114-4: RITM→Intent 映射管道 (1 天, P0)

**目標**: 建立 ServiceNow RITM Catalog Item 到 IPA Business Intent 的映射管道

**交付物**:
- 新增 `backend/src/integrations/orchestration/input/ritm_intent_mapper.py`
- 新增 `backend/src/integrations/orchestration/input/ritm_mappings.yaml`
- 新增 `backend/tests/unit/orchestration/test_ritm_intent_mapper.py`

**映射設計**:

```yaml
# ritm_mappings.yaml
# ServiceNow Catalog Item → IPA Intent 映射
mappings:
  - cat_item_name: "AD Account Unlock"
    intent: "ad.account.unlock"
    extract_variables:
      target_user: "variables.affected_user"
      reason: "short_description"

  - cat_item_name: "AD Password Reset"
    intent: "ad.password.reset"
    extract_variables:
      target_user: "variables.affected_user"
      temporary_password: "variables.temp_password"

  - cat_item_name: "AD Group Membership Change"
    intent: "ad.group.modify"
    extract_variables:
      target_user: "variables.affected_user"
      group_name: "variables.group_name"
      action: "variables.action_type"  # add | remove

  - cat_item_name: "New AD Account"
    intent: "ad.account.create"
    extract_variables:
      display_name: "variables.display_name"
      department: "variables.department"
      manager: "variables.manager"

  - cat_item_name: "Disable AD Account"
    intent: "ad.account.disable"
    extract_variables:
      target_user: "variables.affected_user"
      reason: "variables.disable_reason"

# Fallback 策略
fallback:
  strategy: "semantic_router"  # 未匹配時交給 SemanticRouter
  log_unmatched: true
```

**Mapper 設計**:

```python
class RITMIntentMapper:
    """RITM → Intent 映射器"""

    def __init__(self, mappings_path: str = "ritm_mappings.yaml"):
        self._mappings = self._load_mappings(mappings_path)

    def map_ritm_to_intent(
        self, event: ServiceNowRITMEvent
    ) -> IntentMappingResult:
        """將 RITM 事件映射為業務意圖"""

    def extract_variables(
        self, event: ServiceNowRITMEvent, mapping: Dict
    ) -> Dict[str, Any]:
        """從 RITM 事件提取業務變量"""
```

**驗收標準**:
- [ ] YAML 映射文件包含 5 個 AD 場景
- [ ] RITMIntentMapper 正確映射所有已知 Catalog Item
- [ ] 變量提取邏輯正確（支持巢狀路徑）
- [ ] 未知 Catalog Item 觸發 fallback 策略
- [ ] 單元測試覆蓋所有映射和 fallback

## 技術設計

### 目錄結構

```
backend/src/integrations/orchestration/
├── input/                          # 🆕 Input Processing
│   ├── __init__.py
│   ├── servicenow_webhook.py       # ServiceNow Webhook 接收器
│   ├── ritm_intent_mapper.py       # RITM → Intent 映射器
│   └── ritm_mappings.yaml          # 映射配置
├── routing/
│   └── rules.yaml                  # 修改: 新增 AD 規則
└── ...

backend/src/integrations/mcp/
├── ldap_config.py                  # 🆕 LDAP 配置
├── ldap_server.py                  # 修改: 配置更新
└── ...

backend/src/api/v1/orchestration/
├── webhooks.py                     # 🆕 Webhook API 端點
└── ...
```

### 環境變量新增

```bash
# ServiceNow Webhook
SERVICENOW_WEBHOOK_SECRET=<shared-secret>
SERVICENOW_WEBHOOK_ENABLED=true
SERVICENOW_ALLOWED_IPS=10.0.0.0/8,172.16.0.0/12

# LDAP Configuration
LDAP_SERVER_URL=ldap://ad.company.com:389
LDAP_BIND_DN=CN=svc-ipa,OU=ServiceAccounts,DC=company,DC=com
LDAP_BIND_PASSWORD=<password>
LDAP_SEARCH_BASE=DC=company,DC=com
LDAP_USE_SSL=true
```

## 依賴

```
# 無新增 Python 依賴（使用現有套件）
pyyaml>=6.0       # YAML 解析 (已有)
python-ldap>=3.4  # LDAP 操作 (已有)
pydantic>=2.0     # 數據驗證 (已有)
fastapi>=0.100    # API 框架 (已有)
```

## 風險

| 風險 | 緩解措施 |
|------|----------|
| ServiceNow Webhook 格式不確定 | 參考官方文檔，預留 payload 擴展能力 |
| LDAP 連接在開發環境不可用 | 使用 Mock LDAP 進行本地開發和測試 |
| 規則庫擴展影響現有匹配 | 隔離命名空間 `ad.*`，充分回歸測試 |

## 完成標準

- [ ] PatternMatcher 正確匹配所有 AD 帳號管理模式
- [ ] LDAP MCP Server 連接 AD 並完成基本操作
- [ ] ServiceNow Webhook 接收並解析 RITM 事件
- [ ] RITM→Intent 映射管道完整運作
- [ ] 所有測試通過

---

**Sprint 狀態**: 📋 計劃中
**Story Points**: 40
**開始日期**: TBD
