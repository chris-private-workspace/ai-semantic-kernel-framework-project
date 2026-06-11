# Feature 09: 提示管理（YAML 模板）

**版本**: 1.0  
**日期**: 2025-11-19  
**狀態**: 草稿

---

## 📑 導航

- [← 返回附錄 B 索引](../../prd-appendix-b-features-8-14.md)
- [← 上一個: Feature 08 - n8n 觸發](./feature-8-n8n-triggering.md)
- [→ 下一個: Feature 10 - 審計追蹤](./feature-10-audit-trail.md)

---

## <a id="f9-prompt-management"></a>F9. 提示管理（YAML 模板）

**功能類別**: Reliability (可靠性)  
**優先級**: P0 (必須擁有)  
**估計開發時間**: 1 週  
**複雜度**: ⭐⭐⭐

---

### 9.1 功能概述

**定義**:
F9（提示管理）提供**集中式 YAML 模板庫**來管理所有 Agent 提示（Prompts），支持**版本控制、變量替換、A/B 測試**。管理員可以在不修改代碼的情況下更新提示內容，並追蹤提示變更對 Agent 輸出質量的影響。

**為什麼重要**:
- **代碼與內容分離**: 提示變更不需要重新部署代碼（從 2 小時降至 2 分鐘）
- **快速迭代**: 市場團隊可以直接優化提示，無需開發團隊介入
- **版本追蹤**: 回滾到歷史提示版本，分析提示變更影響
- **多語言支持**: 未來擴展至多語言（中文、日文、西班牙文）時無需改代碼

**核心能力**:
1. **YAML 模板庫**: 所有提示存儲在 Git 倉庫（`prompts/` 目錄）
2. **變量替換**: 支持 `{customer_name}`, `{ticket_id}` 等動態變量
3. **版本管理**: Git 提交歷史自動追蹤提示變更
4. **A/B 測試**: 同一提示的多個變體（Variant A/B/C），隨機分配流量
5. **提示預覽**: UI 預覽最終渲染後的提示（帶示例數據）
6. **熱重載**: 提示變更後 5 秒內自動生效（無需重啟服務）

**業務價值**:
- **上市時間**: 提示優化從 2 天（代碼變更 + 測試 + 部署）降至 10 分鐘（YAML 編輯 + 提交）
- **質量提升**: A/B 測試發現最優提示，客戶滿意度提升 15%
- **降低風險**: 提示回滾能力，避免生產環境錯誤提示

**現實世界示例**:

**場景**: "客服票務摘要" Agent 的提示優化

**傳統方式（無提示管理）**:
```python
# 硬編碼在代碼中
prompt = f"""
You are a customer service analyst. Summarize the following ticket:

Ticket ID: {ticket_id}
Customer: {customer_name}
Issue: {issue_description}

Provide a concise summary in 2-3 sentences.
"""
```

**變更流程**:
1. 開發人員修改 Python 代碼中的提示字符串
2. 運行單元測試（30 分鐘）
3. 提交 PR，等待審查（1-2 小時）
4. 合併後觸發 CI/CD 部署（30 分鐘）
5. **總耗時**: 2-3 小時

**使用 F9 提示管理後**:
```yaml
# prompts/customer_service/ticket_summary.yaml
version: "1.2"
name: "Ticket Summary Prompt"
description: "Generates concise summary for CS tickets"

variants:
  - id: "control"
    weight: 50  # 50% 流量
    template: |
      You are a customer service analyst. Summarize the following ticket:
      
      Ticket ID: {ticket_id}
      Customer: {customer_name}
      Issue: {issue_description}
      
      Provide a concise summary in 2-3 sentences.
  
  - id: "experiment_empathy"
    weight: 50  # 50% 流量（A/B 測試）
    template: |
      You are an empathetic customer service analyst. Summarize the following ticket with a focus on the customer's emotional state:
      
      Ticket ID: {ticket_id}
      Customer: {customer_name}
      Issue: {issue_description}
      
      Provide a concise summary in 2-3 sentences, highlighting the customer's urgency level.

variables:
  ticket_id:
    type: "string"
    required: true
    example: "TICKET-1234"
  customer_name:
    type: "string"
    required: true
    example: "John Smith"
  issue_description:
    type: "string"
    required: true
    example: "Cannot access account after password reset"
```

**變更流程**:
1. 市場團隊在 Web UI 編輯 YAML 文件（2 分鐘）
2. 點擊「提交變更」（自動 Git commit + push）
3. 系統自動重載提示（5 秒）
4. **總耗時**: 5-10 分鐘

**架構圖**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          F9. 提示管理架構                              │
└────────────────────────────────────────────────────────────────────────┘

   ┌──────────────┐
   │  Git 倉庫    │  ← 提示模板存儲（prompts/ 目錄）
   │ (prompts/)   │     - ticket_summary.yaml
   └──────┬───────┘     - refund_decision.yaml
          │              - password_reset.yaml
          │ Git Pull
          ↓
   ┌──────────────┐
   │ 提示加載器   │  ← 啟動時/定時（每 5 秒）拉取最新提示
   │(Prompt Loader)│
   └──────┬───────┘
          │
          ↓
   ┌──────────────┐
   │ 提示緩存     │  ← Redis 緩存渲染後的提示（TTL 5 秒）
   │ (Redis)      │     Key: prompt:{name}:v{version}
   └──────┬───────┘
          │
          ↓
   ┌──────────────────────────────────────────────────────────────────┐
   │                       Agent 執行引擎                             │
   │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
   │  │ 1. 選擇變體   │  │ 2. 變量替換   │  │ 3. 調用 LLM   │   │
   │  │   (A/B Test)   │→ │   (Jinja2)     │→ │   (OpenAI)     │   │
   │  └────────────────┘  └────────────────┘  └────────────────┘   │
   └──────────────────────────────────────────────────────────────────┘
          │
          ↓
   ┌──────────────┐
   │ 提示使用日誌 │  ← 記錄每次提示調用（variant, 變量, 執行 ID）
   │(PostgreSQL)  │     用於 A/B 測試分析
   └──────────────┘
          ↓
   ┌──────────────┐
   │ Web UI       │  ← 提示編輯器、預覽、A/B 測試結果儀表板
   │(React)       │
   └──────────────┘
```

---

### 9.2 用戶故事

#### **US-F9-001: YAML 提示模板編輯器**

**優先級**: P0 (必須擁有)  
**估計開發時間**: 2 天  
**複雜度**: ⭐⭐⭐

**用戶故事**:
- **作為** 市場團隊成員（Sarah Lin）
- **我想要** 在 Web UI 中直接編輯提示 YAML 文件
- **以便** 我可以快速優化提示內容，而不需要開發團隊協助

**驗收標準**:

1. ✅ **提示列表**: 顯示所有提示文件（按工作流分組）
2. ✅ **在線編輯器**: 支持 YAML 語法高亮和驗證
3. ✅ **即時預覽**: 右側面板實時預覽渲染後的提示（帶示例數據）
4. ✅ **變量校驗**: 檢測未定義的變量（如 `{ticket_id}` 未在 `variables` 中聲明）
5. ✅ **Git 集成**: 保存時自動 Git commit + push（提交消息自動生成）
6. ✅ **版本歷史**: 查看提示變更歷史（Git log）

**提示編輯器 UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 提示管理 > customer_service/ticket_summary.yaml              [保存] [取消]   │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 📁 提示列表                       │ 📝 YAML 編輯器                            │
│                                   │                                           │
│ 📂 customer_service (5)           │ # prompts/customer_service/              │
│   • ticket_summary.yaml ◀         │ # ticket_summary.yaml                     │
│   • refund_decision.yaml          │                                           │
│   • escalation_check.yaml         │ version: "1.2"                            │
│   • customer_sentiment.yaml       │ name: "Ticket Summary Prompt"             │
│   • sla_priority.yaml             │ description: "Generates concise summary"  │
│                                   │                                           │
│ 📂 it_support (3)                 │ variants:                                 │
│   • password_reset.yaml           │   - id: "control"                         │
│   • access_request.yaml           │     weight: 50                            │
│   • incident_triage.yaml          │     template: |                           │
│                                   │       You are a customer service analyst. │
│ 📂 hr (2)                         │       Summarize the following ticket:     │
│   • leave_approval.yaml           │                                           │
│   • onboarding_checklist.yaml     │       Ticket ID: {ticket_id}              │
│                                   │       Customer: {customer_name}           │
│ [+ 新增提示]                      │       Issue: {issue_description}          │
│                                   │                                           │
│                                   │       Provide a concise summary in 2-3    │
│                                   │       sentences.                          │
│                                   │                                           │
│                                   │ variables:                                │
│                                   │   ticket_id:                              │
│                                   │     type: "string"                        │
│                                   │     required: true                        │
│                                   │     example: "TICKET-1234"                │
│                                   │   customer_name:                          │
│                                   │     type: "string"                        │
│                                   │     required: true                        │
│                                   │     example: "John Smith"                 │
│                                   │                                           │
│                                   │ [✓ YAML 語法正確]                         │
│                                   │                                           │
├───────────────────────────────────┼───────────────────────────────────────────┤
│                                   │                                           │
│ 📊 版本歷史                       │ 🔍 預覽                                   │
│                                   │                                           │
│ v1.2 (當前) - 2025-11-19 10:30   │ 變體: [Control ▼]                        │
│ 修改: 添加情感分析變體            │                                           │
│ 作者: Sarah Lin                   │ 示例數據:                                 │
│                                   │ ┌─────────────────────────────────────┐   │
│ v1.1 - 2025-11-18 14:15           │ │ ticket_id: TICKET-1234              │   │
│ 修改: 簡化輸出為 2-3 句           │ │ customer_name: John Smith           │   │
│ 作者: Alex Chen                   │ │ issue_description: Cannot access... │   │
│                                   │ └─────────────────────────────────────┘   │
│ v1.0 - 2025-11-10 09:00           │                                           │
│ 修改: 初始提示創建                │ 渲染後的提示:                             │
│ 作者: Alex Chen                   │ ┌─────────────────────────────────────┐   │
│                                   │ │ You are a customer service analyst. │   │
│ [查看完整歷史]                    │ │ Summarize the following ticket:     │   │
│                                   │ │                                     │   │
│                                   │ │ Ticket ID: TICKET-1234              │   │
│                                   │ │ Customer: John Smith                │   │
│                                   │ │ Issue: Cannot access account after  │   │
│                                   │ │ password reset                      │   │
│                                   │ │                                     │   │
│                                   │ │ Provide a concise summary in 2-3    │   │
│                                   │ │ sentences.                          │   │
│                                   │ └─────────────────────────────────────┘   │
│                                   │                                           │
│                                   │ [複製到剪貼板] [測試提示]                 │
└───────────────────────────────────┴───────────────────────────────────────────┘
```

**FastAPI 實現**:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yaml
import subprocess
from pathlib import Path
from datetime import datetime

router = APIRouter(prefix="/api/prompts", tags=["prompts"])

PROMPTS_DIR = Path("prompts/")

class PromptUpdateRequest(BaseModel):
    content: str  # YAML 內容
    commit_message: str = None  # 可選提交消息

@router.get("/list")
async def list_prompts():
    """列出所有提示文件"""
    prompts = []
    
    for yaml_file in PROMPTS_DIR.rglob("*.yaml"):
        relative_path = yaml_file.relative_to(PROMPTS_DIR)
        
        # 讀取 YAML 元數據
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Git 最後修改時間
        git_log = subprocess.run(
            ["git", "log", "-1", "--format=%at|%an", str(yaml_file)],
            capture_output=True,
            text=True
        ).stdout.strip().split("|")
        
        prompts.append({
            "path": str(relative_path),
            "name": data.get("name", "Unnamed"),
            "version": data.get("version", "1.0"),
            "category": str(relative_path.parent),
            "last_modified": int(git_log[0]) if git_log else None,
            "last_author": git_log[1] if len(git_log) > 1 else "Unknown"
        })
    
    return {"prompts": prompts}

@router.get("/get/{path:path}")
async def get_prompt(path: str):
    """獲取提示文件內容"""
    file_path = PROMPTS_DIR / path
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return {"content": content}

@router.post("/save/{path:path}")
async def save_prompt(path: str, request: PromptUpdateRequest):
    """保存提示文件（自動 Git commit）"""
    file_path = PROMPTS_DIR / path
    
    # 1. 驗證 YAML 語法
    try:
        yaml.safe_load(request.content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")
    
    # 2. 寫入文件
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(request.content)
    
    # 3. Git commit + push
    commit_message = request.commit_message or f"Update prompt: {path}"
    
    subprocess.run(["git", "add", str(file_path)], check=True)
    subprocess.run(
        ["git", "commit", "-m", commit_message],
        check=True
    )
    subprocess.run(["git", "push"], check=True)
    
    return {"message": "Prompt saved successfully", "path": path}

@router.get("/history/{path:path}")
async def get_prompt_history(path: str, limit: int = 10):
    """獲取提示變更歷史"""
    file_path = PROMPTS_DIR / path
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Git log
    git_log = subprocess.run(
        [
            "git", "log",
            f"-{limit}",
            "--format=%H|%at|%an|%s",
            str(file_path)
        ],
        capture_output=True,
        text=True
    ).stdout.strip().split("\n")
    
    history = []
    for line in git_log:
        if not line:
            continue
        
        commit_hash, timestamp, author, message = line.split("|", 3)
        history.append({
            "commit": commit_hash,
            "timestamp": int(timestamp),
            "author": author,
            "message": message
        })
    
    return {"history": history}

@router.post("/preview")
async def preview_prompt(yaml_content: str, variables: dict):
    """預覽渲染後的提示"""
    # 解析 YAML
    data = yaml.safe_load(yaml_content)
    
    # 獲取第一個變體的模板
    template_str = data["variants"][0]["template"]
    
    # Jinja2 渲染
    from jinja2 import Template
    template = Template(template_str)
    rendered = template.render(**variables)
    
    return {"rendered": rendered}
```

**完成定義**:

- [ ] 提示列表 API（按工作流分組）
- [ ] YAML 編輯器（語法高亮、驗證）
- [ ] 實時預覽（Jinja2 渲染）
- [ ] Git 集成（自動 commit + push）
- [ ] 版本歷史查詢（Git log）
- [ ] 變量校驗（檢測未定義變量）

---

#### **US-F9-002: 變量替換與 Jinja2 模板引擎**

**優先級**: P0 (必須擁有)  
**估計開發時間**: 1.5 天  
**複雜度**: ⭐⭐

**用戶故事**:
- **作為** Agent 開發者（David Kim）
- **我想要** 在提示中使用動態變量（如 `{customer_name}`）和條件邏輯（如 `{% if urgent %}`）
- **以便** 我可以創建靈活的提示模板，適應不同場景

**驗收標準**:

1. ✅ **基礎變量替換**: 支持 `{variable_name}` 語法
2. ✅ **Jinja2 語法**: 支持 `{% if %}`, `{% for %}`, `{{ variable | filter }}`
3. ✅ **過濾器**: 支持 `upper`, `lower`, `default`, `date_format` 等
4. ✅ **條件渲染**: 根據變量值動態生成提示內容
5. ✅ **錯誤處理**: 缺失必需變量時拋出清晰錯誤
6. ✅ **性能**: 模板編譯後緩存，渲染時間 <10ms

**Jinja2 模板示例**:

```yaml
# prompts/customer_service/ticket_summary.yaml
version: "1.3"
name: "Ticket Summary with Conditional Logic"

variants:
  - id: "control"
    weight: 100
    template: |
      You are a customer service analyst. Summarize the following ticket:
      
      Ticket ID: {{ ticket_id }}
      Customer: {{ customer_name | upper }}
      Issue: {{ issue_description }}
      
      {% if priority == "urgent" %}
      ⚠️ URGENT: This ticket requires immediate attention!
      {% endif %}
      
      {% if previous_tickets_count > 5 %}
      Note: This is a repeat customer with {{ previous_tickets_count }} previous tickets.
      {% endif %}
      
      Provide a concise summary in 2-3 sentences{% if priority == "urgent" %}, prioritizing immediate action items{% endif %}.

variables:
  ticket_id:
    type: "string"
    required: true
    example: "TICKET-1234"
  
  customer_name:
    type: "string"
    required: true
    example: "John Smith"
  
  issue_description:
    type: "string"
    required: true
    example: "Cannot access account after password reset"
  
  priority:
    type: "string"
    required: false
    default: "normal"
    enum: ["low", "normal", "high", "urgent"]
    example: "urgent"
  
  previous_tickets_count:
    type: "integer"
    required: false
    default: 0
    example: 8
```

**Python 實現**:

```python
from jinja2 import Template, TemplateSyntaxError, UndefinedError
from typing import Dict, Any
import yaml

class PromptRenderer:
    """提示渲染器（Jinja2）"""
    
    def __init__(self, prompt_yaml_path: str):
        with open(prompt_yaml_path, 'r', encoding='utf-8') as f:
            self.prompt_data = yaml.safe_load(f)
        
        # 預編譯所有變體模板
        self.compiled_templates = {}
        for variant in self.prompt_data.get("variants", []):
            variant_id = variant["id"]
            template_str = variant["template"]
            self.compiled_templates[variant_id] = Template(template_str)
    
    def render(
        self,
        variant_id: str = None,
        variables: Dict[str, Any] = None
    ) -> str:
        """
        渲染提示模板
        
        參數:
            variant_id: 變體 ID（None = 使用第一個變體）
            variables: 變量字典
        
        返回: 渲染後的提示文本
        """
        variables = variables or {}
        
        # 1. 選擇變體
        if not variant_id:
            variant_id = self.prompt_data["variants"][0]["id"]
        
        if variant_id not in self.compiled_templates:
            raise ValueError(f"Variant not found: {variant_id}")
        
        # 2. 驗證必需變量
        self._validate_variables(variables)
        
        # 3. 應用默認值
        variables_with_defaults = self._apply_defaults(variables)
        
        # 4. 渲染模板
        try:
            template = self.compiled_templates[variant_id]
            rendered = template.render(**variables_with_defaults)
            return rendered.strip()
        
        except UndefinedError as e:
            raise ValueError(f"Missing variable: {str(e)}")
        
        except TemplateSyntaxError as e:
            raise ValueError(f"Template syntax error: {str(e)}")
    
    def _validate_variables(self, variables: Dict[str, Any]):
        """驗證必需變量"""
        var_schema = self.prompt_data.get("variables", {})
        
        for var_name, var_config in var_schema.items():
            if var_config.get("required", False):
                if var_name not in variables:
                    raise ValueError(
                        f"Missing required variable: {var_name}"
                    )
    
    def _apply_defaults(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """應用默認值"""
        var_schema = self.prompt_data.get("variables", {})
        result = variables.copy()
        
        for var_name, var_config in var_schema.items():
            if var_name not in result and "default" in var_config:
                result[var_name] = var_config["default"]
        
        return result


# 使用示例
renderer = PromptRenderer("prompts/customer_service/ticket_summary.yaml")

rendered_prompt = renderer.render(
    variant_id="control",
    variables={
        "ticket_id": "TICKET-5678",
        "customer_name": "Jane Doe",
        "issue_description": "Billing error - charged twice for same service",
        "priority": "urgent",
        "previous_tickets_count": 8
    }
)

print(rendered_prompt)
# 輸出:
# You are a customer service analyst. Summarize the following ticket:
# 
# Ticket ID: TICKET-5678
# Customer: JANE DOE
# Issue: Billing error - charged twice for same service
# 
# ⚠️ URGENT: This ticket requires immediate attention!
# 
# Note: This is a repeat customer with 8 previous tickets.
# 
# Provide a concise summary in 2-3 sentences, prioritizing immediate action items.
```

**完成定義**:

- [ ] Jinja2 模板引擎集成
- [ ] 變量驗證（必需 vs 可選）
- [ ] 默認值應用
- [ ] 過濾器支持（upper, lower, date_format）
- [ ] 條件邏輯（{% if %}, {% for %}）
- [ ] 錯誤處理（清晰錯誤消息）

---

#### **US-F9-003: A/B 測試與流量分配**

**優先級**: P1 (重要)  
**估計開發時間**: 2 天  
**複雜度**: ⭐⭐⭐⭐

**用戶故事**:
- **作為** 產品經理（Michael Tan）
- **我想要** 對同一提示創建多個變體（Variant A/B/C），並自動分配流量進行 A/B 測試
- **以便** 我可以數據驅動地優化提示，找到最佳版本

**驗收標準**:

1. ✅ **多變體支持**: 一個提示文件可包含多個變體（Variant）
2. ✅ **流量權重**: 配置每個變體的流量百分比（如 A=50%, B=30%, C=20%）
3. ✅ **隨機分配**: 根據權重隨機選擇變體（使用執行 ID 作為種子）
4. ✅ **使用追蹤**: 記錄每次提示調用使用了哪個變體
5. ✅ **結果儀表板**: 比較不同變體的成功率、執行時間、用戶評分
6. ✅ **自動勝出**: 達到統計顯著性後，自動將流量切換至最佳變體

**A/B 測試配置示例**:

```yaml
# prompts/customer_service/refund_decision.yaml
version: "2.0"
name: "Refund Decision Prompt - A/B Test"
description: "Testing different approaches for refund decision making"

ab_test:
  enabled: true
  start_date: "2025-11-19"
  end_date: "2025-12-03"  # 2 週測試期
  minimum_samples: 100  # 每個變體至少 100 次調用
  confidence_level: 0.95  # 95% 置信度

variants:
  - id: "control_strict"
    weight: 33
    description: "Baseline - strict refund policy"
    template: |
      You are a customer service analyst evaluating a refund request.
      
      Policy: Refunds are only approved if the product is defective or the order was cancelled within 24 hours.
      
      Request Details:
      - Customer: {{ customer_name }}
      - Order Date: {{ order_date }}
      - Refund Reason: {{ refund_reason }}
      - Product Condition: {{ product_condition }}
      
      Evaluate this request and respond with:
      1. Decision: APPROVE or DENY
      2. Reasoning: 1-2 sentences explaining your decision

  - id: "experiment_empathy"
    weight: 33
    description: "Experiment A - empathetic approach"
    template: |
      You are an empathetic customer service analyst evaluating a refund request.
      
      Policy: Refunds are generally approved if the customer is dissatisfied, unless there is clear evidence of abuse.
      
      Request Details:
      - Customer: {{ customer_name }}
      - Order Date: {{ order_date }}
      - Refund Reason: {{ refund_reason }}
      - Product Condition: {{ product_condition }}
      
      Consider the customer's frustration and evaluate this request with empathy.
      
      Respond with:
      1. Decision: APPROVE or DENY
      2. Reasoning: 1-2 sentences explaining your decision with a compassionate tone

  - id: "experiment_data_driven"
    weight: 34
    description: "Experiment B - data-driven approach"
    template: |
      You are a data-driven customer service analyst evaluating a refund request.
      
      Historical Data:
      - This customer's previous refund requests: {{ previous_refunds }}
      - Customer lifetime value (CLV): ${{ customer_clv }}
      - Average refund rate for this product: {{ product_refund_rate }}%
      
      Request Details:
      - Customer: {{ customer_name }}
      - Order Date: {{ order_date }}
      - Refund Reason: {{ refund_reason }}
      - Product Condition: {{ product_condition }}
      
      Use the historical data to make an informed decision that balances customer satisfaction with business profitability.
      
      Respond with:
      1. Decision: APPROVE or DENY
      2. Reasoning: 1-2 sentences explaining your decision with data points
      3. Risk Score: Low/Medium/High (likelihood of future refund abuse)

variables:
  customer_name:
    type: "string"
    required: true
  order_date:
    type: "string"
    required: true
  refund_reason:
    type: "string"
    required: true
  product_condition:
    type: "string"
    required: true
  previous_refunds:
    type: "integer"
    required: false
    default: 0
  customer_clv:
    type: "number"
    required: false
    default: 0
  product_refund_rate:
    type: "number"
    required: false
    default: 5.0

metrics:
  - name: "approval_rate"
    description: "Percentage of APPROVE decisions"
    target: 0.4  # 期望批准率 40%
  
  - name: "customer_satisfaction"
    description: "Customer rating after refund decision (1-5)"
    target: 4.0  # 期望評分 4.0+
  
  - name: "execution_time"
    description: "LLM execution time (seconds)"
    target: 3.0  # 期望 <3 秒
```

**Python 實現**:

```python
import random
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

class ABTestVariantSelector:
    """A/B 測試變體選擇器"""
    
    def __init__(self, prompt_data: dict):
        self.prompt_data = prompt_data
        self.variants = prompt_data.get("variants", [])
        self.ab_test_config = prompt_data.get("ab_test", {})
    
    def select_variant(self, execution_id: str) -> str:
        """
        選擇變體（基於執行 ID 的確定性隨機）
        
        參數:
            execution_id: 執行 ID（用作隨機種子）
        
        返回: 變體 ID
        """
        # 1. 檢查 A/B 測試是否啟用
        if not self.ab_test_config.get("enabled", False):
            # 未啟用 A/B 測試 - 使用第一個變體
            return self.variants[0]["id"]
        
        # 2. 檢查測試是否在有效期內
        start_date = datetime.fromisoformat(self.ab_test_config.get("start_date"))
        end_date = datetime.fromisoformat(self.ab_test_config.get("end_date"))
        now = datetime.utcnow()
        
        if not (start_date <= now <= end_date):
            # 測試已結束 - 使用權重最高的變體
            return max(self.variants, key=lambda v: v["weight"])["id"]
        
        # 3. 基於執行 ID 的確定性隨機選擇
        # 使用 execution_id 的哈希值作為隨機種子（確保同一執行 ID 總是選擇相同變體）
        hash_value = int(hashlib.md5(execution_id.encode()).hexdigest(), 16)
        random.seed(hash_value)
        
        # 4. 根據權重選擇變體
        total_weight = sum(v["weight"] for v in self.variants)
        rand = random.randint(1, total_weight)
        
        cumulative_weight = 0
        for variant in self.variants:
            cumulative_weight += variant["weight"]
            if rand <= cumulative_weight:
                return variant["id"]
        
        # 默認第一個變體（不應到達這裡）
        return self.variants[0]["id"]


class PromptUsageLogger:
    """提示使用日誌記錄器"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def log_usage(
        self,
        execution_id: str,
        prompt_name: str,
        variant_id: str,
        variables: Dict[str, Any],
        rendered_prompt: str
    ):
        """記錄提示使用"""
        log_entry = PromptUsageLog(
            execution_id=execution_id,
            prompt_name=prompt_name,
            prompt_version=prompt_data["version"],
            variant_id=variant_id,
            variables=variables,
            rendered_prompt=rendered_prompt,
            timestamp=datetime.utcnow()
        )
        
        self.db.add(log_entry)
        self.db.commit()
    
    def log_outcome(
        self,
        execution_id: str,
        outcome: str,  # "success", "error"
        execution_time: float,
        user_rating: Optional[int] = None
    ):
        """記錄執行結果"""
        log_entry = self.db.query(PromptUsageLog).filter_by(
            execution_id=execution_id
        ).first()
        
        if log_entry:
            log_entry.outcome = outcome
            log_entry.execution_time = execution_time
            log_entry.user_rating = user_rating
            self.db.commit()


# 使用示例
selector = ABTestVariantSelector(prompt_data)
variant_id = selector.select_variant(execution_id="exec_abc123")

renderer = PromptRenderer("prompts/customer_service/refund_decision.yaml")
rendered = renderer.render(variant_id=variant_id, variables=variables)

# 記錄使用
logger = PromptUsageLogger(db_session)
logger.log_usage(
    execution_id="exec_abc123",
    prompt_name="refund_decision",
    variant_id=variant_id,
    variables=variables,
    rendered_prompt=rendered
)
```

**A/B 測試結果儀表板 UI**:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ A/B 測試: refund_decision                                    [導出報告]       │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ 📊 測試概覽                                                                   │
│   測試期間: 2025-11-19 至 2025-12-03 (14 天)                                 │
│   狀態: 進行中 (第 7 天)                                                      │
│   總調用次數: 487                                                             │
│                                                                               │
│ ────────────────────────────────────────────────────────────────────────────│
│                                                                               │
│ 🏆 變體性能比較                                                               │
│                                                                               │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 變體           │ 調用次數 │ 批准率   │ 客戶評分 │ 執行時間 │ 勝率   │   │ │
│ ├───────────────┼──────────┼──────────┼──────────┼──────────┼────────┤   │ │
│ │ control_strict│ 161      │ 32.3%    │ 3.2 ⭐   │ 2.8s     │ 15%    │   │ │
│ │ empathy       │ 163      │ 58.9% ↑  │ 4.5 ⭐↑  │ 2.9s     │ 75% 🏆│   │ │
│ │ data_driven   │ 163      │ 45.4%    │ 3.8 ⭐   │ 3.1s     │ 10%    │   │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ 📈 批准率趨勢（最近 7 天）                                                    │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 60% │                           ●─●─●                                   │ │
│ │ 50% │                     ●─●─●                                         │ │
│ │ 40% │               ●─●─●                                               │ │
│ │ 30% │ ●─●─●─●─●─●                                                       │ │
│ │     └──────────────────────────────────────────────────────────────────│ │
│ │       Day1  Day2  Day3  Day4  Day5  Day6  Day7                         │ │
│ │                                                                          │ │
│ │       ● control_strict  ● empathy  ● data_driven                        │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ 🎯 統計顯著性                                                                 │
│   ✅ empathy vs control_strict: p-value = 0.002 (顯著差異，95% 置信度)      │
│   ⚠️ data_driven vs control_strict: p-value = 0.08 (無顯著差異)             │
│                                                                               │
│ 💡 建議                                                                       │
│   "empathy" 變體在批准率和客戶評分上顯著優於其他變體。建議：                 │
│   1. 將 "empathy" 流量權重提升至 80%                                         │
│   2. 再測試 3-5 天以確認結果穩定                                             │
│   3. 如果結果持續，考慮將 "empathy" 設為默認變體                             │
│                                                                               │
│ [提升 empathy 流量] [結束測試] [導出詳細數據]                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

**完成定義**:

- [ ] 變體選擇器（基於權重的隨機分配）
- [ ] 提示使用日誌（記錄變體、變量、結果）
- [ ] A/B 測試儀表板（性能比較）
- [ ] 統計顯著性檢驗（p-value 計算）
- [ ] 自動勝出推薦
- [ ] 流量權重動態調整

---

#### **US-F9-004: 提示熱重載與緩存**

**優先級**: P0 (必須擁有)  
**估計開發時間**: 1.5 天  
**複雜度**: ⭐⭐⭐

**用戶故事**:
- **作為** 運維工程師（Emily Rodriguez）
- **我想要** 提示變更後無需重啟服務即可自動生效
- **以便** 我可以快速部署提示優化，零停機時間

**驗收標準**:

1. ✅ **定時拉取**: 每 5 秒從 Git 倉庫拉取最新提示
2. ✅ **Redis 緩存**: 緩存渲染後的提示（TTL 5 秒）
3. ✅ **變更檢測**: 檢測 Git commit 變更，只重載變更的文件
4. ✅ **原子更新**: 提示更新過程中，舊版本仍可用（無中斷）
5. ✅ **健康檢查**: 驗證新提示 YAML 語法正確後才應用
6. ✅ **通知**: 提示重載成功/失敗時通過 Teams 通知

**Python 實現**:

```python
import time
import subprocess
import yaml
from pathlib import Path
from threading import Thread
from typing import Dict
from redis import Redis
import logging

logger = logging.getLogger(__name__)

class PromptHotReloader:
    """提示熱重載服務"""
    
    def __init__(
        self,
        prompts_dir: Path,
        redis_client: Redis,
        reload_interval: int = 5
    ):
        self.prompts_dir = prompts_dir
        self.redis = redis_client
        self.reload_interval = reload_interval
        
        # 當前加載的提示（內存）
        self.loaded_prompts: Dict[str, dict] = {}
        
        # 最後一次 Git commit hash
        self.last_commit_hash = self._get_current_commit_hash()
        
        # 啟動後台重載線程
        self.reload_thread = Thread(target=self._reload_loop, daemon=True)
        self.reload_thread.start()
    
    def _get_current_commit_hash(self) -> str:
        """獲取當前 Git commit hash"""
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.prompts_dir,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    
    def _reload_loop(self):
        """後台重載循環"""
        while True:
            try:
                self._check_and_reload()
            except Exception as e:
                logger.error(f"Prompt reload failed: {e}")
            
            time.sleep(self.reload_interval)
    
    def _check_and_reload(self):
        """檢查並重載變更的提示"""
        # 1. Git pull
        subprocess.run(
            ["git", "pull"],
            cwd=self.prompts_dir,
            capture_output=True
        )
        
        # 2. 檢查 commit 是否變更
        current_commit = self._get_current_commit_hash()
        
        if current_commit == self.last_commit_hash:
            # 沒有變更
            return
        
        logger.info(f"Detected prompt changes: {self.last_commit_hash} -> {current_commit}")
        
        # 3. 獲取變更的文件列表
        changed_files = subprocess.run(
            [
                "git", "diff", "--name-only",
                self.last_commit_hash, current_commit
            ],
            cwd=self.prompts_dir,
            capture_output=True,
            text=True
        ).stdout.strip().split("\n")
        
        # 4. 重載變更的 YAML 文件
        reload_count = 0
        for file_path in changed_files:
            if not file_path.endswith(".yaml"):
                continue
            
            full_path = self.prompts_dir / file_path
            if not full_path.exists():
                # 文件已刪除
                self._unload_prompt(file_path)
                continue
            
            # 重載提示
            if self._reload_prompt(file_path):
                reload_count += 1
        
        # 5. 更新 last commit hash
        self.last_commit_hash = current_commit
        
        logger.info(f"Reloaded {reload_count} prompts successfully")
        
        # 6. 發送通知（可選）
        # await notification_service.send_teams_message(
        #     f"✅ Prompts reloaded: {reload_count} files updated"
        # )
    
    def _reload_prompt(self, file_path: str) -> bool:
        """重載單個提示文件"""
        full_path = self.prompts_dir / file_path
        
        try:
            # 1. 讀取並驗證 YAML
            with open(full_path, 'r', encoding='utf-8') as f:
                prompt_data = yaml.safe_load(f)
            
            # 2. 驗證必需字段
            if "name" not in prompt_data or "variants" not in prompt_data:
                logger.error(f"Invalid prompt file: {file_path} (missing required fields)")
                return False
            
            # 3. 更新內存中的提示
            self.loaded_prompts[file_path] = prompt_data
            
            # 4. 清除 Redis 緩存（強制重新渲染）
            cache_key_pattern = f"prompt:{prompt_data['name']}:*"
            for key in self.redis.scan_iter(match=cache_key_pattern):
                self.redis.delete(key)
            
            logger.info(f"Reloaded prompt: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to reload prompt {file_path}: {e}")
            return False
    
    def _unload_prompt(self, file_path: str):
        """卸載已刪除的提示"""
        if file_path in self.loaded_prompts:
            del self.loaded_prompts[file_path]
            logger.info(f"Unloaded deleted prompt: {file_path}")
    
    def get_prompt(self, prompt_name: str) -> dict:
        """獲取提示（從內存）"""
        for prompt_data in self.loaded_prompts.values():
            if prompt_data["name"] == prompt_name:
                return prompt_data
        
        raise ValueError(f"Prompt not found: {prompt_name}")


# 使用示例
redis_client = Redis(host="localhost", port=6379, db=0)
reloader = PromptHotReloader(
    prompts_dir=Path("prompts/"),
    redis_client=redis_client,
    reload_interval=5
)

# 提示會自動在後台重載
# 無需手動調用任何方法
```

**Redis 緩存策略**:

```python
import json
from redis import Redis
from typing import Optional

class PromptCache:
    """提示緩存（Redis）"""
    
    def __init__(self, redis_client: Redis, ttl: int = 5):
        self.redis = redis_client
        self.ttl = ttl  # 緩存 TTL（秒）
    
    def get_cached_prompt(
        self,
        prompt_name: str,
        variant_id: str,
        variables: dict
    ) -> Optional[str]:
        """獲取緩存的渲染提示"""
        cache_key = self._build_cache_key(prompt_name, variant_id, variables)
        cached = self.redis.get(cache_key)
        
        if cached:
            return cached.decode('utf-8')
        
        return None
    
    def cache_prompt(
        self,
        prompt_name: str,
        variant_id: str,
        variables: dict,
        rendered_prompt: str
    ):
        """緩存渲染後的提示"""
        cache_key = self._build_cache_key(prompt_name, variant_id, variables)
        self.redis.setex(
            cache_key,
            self.ttl,
            rendered_prompt
        )
    
    def _build_cache_key(
        self,
        prompt_name: str,
        variant_id: str,
        variables: dict
    ) -> str:
        """構建緩存鍵"""
        # 使用變量的哈希值避免鍵過長
        variables_hash = hashlib.md5(
            json.dumps(variables, sort_keys=True).encode()
        ).hexdigest()[:8]
        
        return f"prompt:{prompt_name}:{variant_id}:{variables_hash}"
```

**完成定義**:

- [ ] Git 定時拉取（每 5 秒）
- [ ] 變更檢測（Git diff）
- [ ] YAML 文件驗證（語法檢查）
- [ ] 熱重載實現（無需重啟）
- [ ] Redis 緩存（TTL 5 秒）
- [ ] 健康檢查和通知

---

### 9.3 數據庫架構

```sql
-- 提示使用日誌表
CREATE TABLE prompt_usage_logs (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(100) NOT NULL,
    
    -- 提示信息
    prompt_name VARCHAR(200) NOT NULL,
    prompt_version VARCHAR(20),
    variant_id VARCHAR(50),
    
    -- 變量
    variables JSONB NOT NULL,
    rendered_prompt TEXT,
    
    -- 執行結果
    outcome VARCHAR(20),  -- success, error
    execution_time DECIMAL(10,3),  -- 秒
    user_rating INTEGER,  -- 1-5 星
    
    -- 時間戳
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (execution_id) REFERENCES executions(execution_id)
);

CREATE INDEX idx_prompt_usage_prompt ON prompt_usage_logs(prompt_name, variant_id, timestamp DESC);
CREATE INDEX idx_prompt_usage_execution ON prompt_usage_logs(execution_id);

-- A/B 測試結果統計表（物化視圖）
CREATE MATERIALIZED VIEW prompt_ab_test_stats AS
SELECT
    prompt_name,
    variant_id,
    COUNT(*) as total_calls,
    
    -- 批准率（假設提示輸出包含 APPROVE/DENY）
    COUNT(*) FILTER (WHERE rendered_prompt LIKE '%APPROVE%') * 100.0 / COUNT(*) as approval_rate,
    
    -- 平均評分
    AVG(user_rating) as avg_rating,
    
    -- 平均執行時間
    AVG(execution_time) as avg_execution_time,
    
    -- 成功率
    COUNT(*) FILTER (WHERE outcome = 'success') * 100.0 / COUNT(*) as success_rate,
    
    -- 時間範圍
    MIN(timestamp) as first_call,
    MAX(timestamp) as last_call
FROM prompt_usage_logs
GROUP BY prompt_name, variant_id;

CREATE UNIQUE INDEX idx_ab_test_stats ON prompt_ab_test_stats(prompt_name, variant_id);
```

---

### 9.4 非功能需求 (NFR)

| **類別** | **需求** | **目標** | **測量** |
|-------------|----------------|-----------|----------------|
| **性能** | 提示渲染時間 | <10ms（含緩存） | 性能監控 |
| | Redis 緩存命中率 | ≥80% | Redis INFO 統計 |
| **可靠性** | 提示重載成功率 | ≥99% | 重載日誌分析 |
| | YAML 驗證準確率 | 100%（阻止無效提示） | 驗證測試 |
| **可用性** | 提示變更生效時間 | <10 秒（重載週期） | 端到端測試 |
| | 熱重載零停機 | 100%（無中斷） | 可用性監控 |
| **可維護性** | 提示版本回滾 | <5 分鐘 | Git 操作時間 |

---

### 9.5 測試策略

**單元測試**:

- Jinja2 變量替換（包含默認值、過濾器）
- YAML 驗證邏輯
- A/B 測試變體選擇（權重分配）
- Redis 緩存讀寫

**集成測試**:

- 端到端提示渲染流程
- Git 拉取 + 熱重載
- 提示變更後立即生效（<10 秒）
- A/B 測試日誌記錄

**性能測試**:

- 1000 次/秒提示渲染請求（含緩存）
- Redis 緩存命中率測試

---

### 9.6 風險和緩解

| **風險** | **概率** | **影響** | **緩解** |
|---------|----------------|-----------|---------------|
| 無效 YAML 導致服務崩潰 | 中 | 高 | 嚴格 YAML 驗證 + 健康檢查 |
| Git 拉取失敗 | 低 | 中 | 重試機制 + 使用緩存的舊版本 |
| 提示變更未測試就上線 | 高 | 中 | 強制 A/B 測試流程 + 審查機制 |
| Redis 緩存失效導致性能下降 | 低 | 低 | 降級至無緩存模式（性能稍差但可用） |

---

### 9.7 未來增強（MVP 後）

1. **多語言提示**: 支持中文、日文、西班牙文提示（基於用戶語言自動選擇）
2. **提示優化建議**: 使用 LLM 分析提示效果，自動建議優化
3. **提示片段庫**: 可重用的提示片段（如「客戶服務語氣」、「技術文檔格式」）
4. **可視化提示編輯器**: 拖拽式提示構建器（無需編寫 YAML）
5. **提示沙盒測試**: 在生產環境前進行安全測試

---

**✅ F9 完成**：提示管理（YAML 模板）功能規範已完整編寫（4 個用戶故事、數據庫架構、NFR、測試策略）。

---
