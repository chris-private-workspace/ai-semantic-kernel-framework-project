# Phase 3 根本原因分析報告

**分析日期**: 2025-12-06
**問題**: Phase 3 實現沒有使用 Microsoft Agent Framework 官方 API

---

## 問題摘要

儘管規劃文件明確指示使用官方 API，實際開發卻自行實現了類似功能。

---

## 根本原因分析

### 🔴 原因 1: 技術環境未就緒

**發現**:
```bash
$ python -c "import agent_framework"
ModuleNotFoundError: No module named 'agent_framework'
```

儘管 `requirements.txt` 第 19 行列出：
```
agent-framework>=1.0.0b251120
```

但該包**實際上沒有被安裝**到開發環境中。

**影響**:
- 開發時無法 import 官方類
- 無法驗證代碼是否正確使用 API
- 被迫「模擬」實現

**預防措施**:
1. Sprint 開始前驗證所有依賴已安裝
2. 添加 CI 檢查確保依賴完整
3. 創建 setup 腳本自動驗證環境

---

### 🔴 原因 2: AI 上下文丟失

**發現**:
在長時間的開發會話中，AI (Claude) 可能：
- 忘記了規劃文件中的具體要求
- 沒有在每個文件開始時重新檢查規劃
- 「創造性地」解決問題而不是遵循規劃

**證據**:
規劃文件明確展示了正確的 import：
```python
# Sprint 14 Plan 第 44-49 行
from agent_framework import (
    ConcurrentBuilder,
    AgentExecutor,
    Executor,
    Workflow,
)
```

但實際代碼沒有任何這樣的 import。

**預防措施**:
1. 每個 Story 開始時強制檢查規劃文件
2. 在 checklist 中添加「已驗證使用官方 API」項目
3. 每個文件頭部註釋中引用規劃文件的具體行號

---

### 🔴 原因 3: 缺乏驗證機制

**發現**:
開發過程中沒有機制來驗證是否真正使用了官方 API。

**問題**:
- 代碼審查沒有檢查 import 語句
- 測試沒有驗證使用了正確的類
- 沒有 lint 規則強制 import

**預防措施**:
1. 添加自定義 lint 規則檢查必要的 import
2. 創建驗證腳本掃描所有 adapter 文件
3. 在 PR checklist 中添加「已驗證官方 API 使用」

---

### 🟡 原因 4: 規劃與執行斷層

**發現**:
規劃文件提供了正確的代碼範例，但這些範例沒有被直接複製或使用。

**問題**:
- 規劃文件被視為「參考」而非「規範」
- 開發時傾向於重新設計而非遵循規劃
- 沒有對照規劃進行代碼審查

**預防措施**:
1. 規劃文件中的代碼應該可以直接作為起點
2. 強制使用「先複製規劃代碼，再修改」的流程
3. 定期檢查點對照規劃

---

### 🟡 原因 5: 「適配器」概念被誤解

**發現**:
決策記錄說「創建適配器包裝官方 API」，但實際實現變成了「創建類似功能的替代品」。

**混淆**:
```
✅ 正確理解:
   Adapter 使用官方 API，只是提供不同的接口

❌ 錯誤理解:
   Adapter 重新實現官方 API 的功能
```

**預防措施**:
1. 明確定義「適配器」必須包含官方類的實例
2. 提供正確 vs 錯誤的範例對比
3. 在代碼審查中強調此區別

---

## 驗證清單 (重寫前必須確認)

### 環境準備
- [ ] `pip install agent-framework` 成功
- [ ] `python -c "from agent_framework import ConcurrentBuilder"` 成功
- [ ] 所有官方 Builder 類都可以 import

### 代碼規範
- [ ] 每個 Adapter 文件必須有 `from agent_framework import ...`
- [ ] 每個 Adapter 類必須包含官方類的實例變數 (如 `self._builder`)
- [ ] `build()` 方法必須調用 `self._builder.build()`

### 驗證腳本
```python
# scripts/verify_official_api_usage.py
import ast
import sys
from pathlib import Path

REQUIRED_IMPORTS = {
    'concurrent.py': ['ConcurrentBuilder'],
    'groupchat.py': ['GroupChatBuilder', 'GroupChatDirective'],
    'handoff.py': ['HandoffBuilder'],
    'magentic.py': ['MagenticBuilder'],
    'workflow_executor.py': ['WorkflowExecutor'],
}

def verify_imports(file_path: Path, required: list[str]) -> bool:
    """Verify file imports required classes from agent_framework."""
    content = file_path.read_text()
    tree = ast.parse(content)

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and 'agent_framework' in node.module:
                for alias in node.names:
                    imported.add(alias.name)

    missing = set(required) - imported
    if missing:
        print(f"❌ {file_path}: Missing imports: {missing}")
        return False
    print(f"✅ {file_path}: All required imports present")
    return True

def main():
    builders_dir = Path('backend/src/integrations/agent_framework/builders')
    all_valid = True

    for filename, required in REQUIRED_IMPORTS.items():
        file_path = builders_dir / filename
        if file_path.exists():
            if not verify_imports(file_path, required):
                all_valid = False
        else:
            print(f"⚠️ {file_path}: File not found")

    return 0 if all_valid else 1

if __name__ == '__main__':
    sys.exit(main())
```

---

## 建議的工作流程改進

### 1. Sprint 開始前檢查清單
```markdown
## Sprint 開始前必須完成

- [ ] 運行 `pip install -r requirements.txt`
- [ ] 驗證 `python -c "from agent_framework import ..."` 成功
- [ ] 重新閱讀規劃文件中的代碼範例
- [ ] 確認理解「適配器」的正確含義
```

### 2. 每個 Story 開始時
```markdown
## Story 開始檢查

- [ ] 已閱讀規劃文件 sprint-XX-plan.md 第 YY-ZZ 行的代碼範例
- [ ] 已複製規劃代碼作為起點
- [ ] 已驗證使用了 `from agent_framework import ...`
```

### 3. 每個 Story 完成時
```markdown
## Story 完成驗證

- [ ] 運行 `python scripts/verify_official_api_usage.py`
- [ ] grep "from agent_framework" 在文件中找到正確的 import
- [ ] 代碼中有 `self._builder = OfficialBuilder()` 模式
```

### 4. Sprint 結束前
```markdown
## Sprint 完成驗證

- [ ] 所有 Adapter 文件都 import 了官方類
- [ ] 單元測試驗證了官方 API 的調用
- [ ] 對照規劃文件進行了代碼審查
```

---

## 總結

| 原因類型 | 根本原因 | 嚴重程度 | 可預防性 |
|---------|---------|---------|---------|
| 技術 | 依賴未安裝 | 高 | 高 |
| 流程 | AI 上下文丟失 | 高 | 中 |
| 流程 | 缺乏驗證 | 高 | 高 |
| 理解 | 規劃執行斷層 | 中 | 中 |
| 理解 | 適配器概念誤解 | 中 | 高 |

**最關鍵的改進**:
1. 確保 `agent-framework` 包已安裝並可用
2. 創建驗證腳本自動檢查官方 API 使用
3. 每個 Story 開始時強制檢查規劃文件

---

## 下一步行動

1. **立即**: 安裝 `agent-framework` 包
2. **今天**: 創建驗證腳本
3. **重寫前**: 建立完整的工作流程檢查點
4. **重寫時**: 嚴格遵循規劃文件的代碼範例
