# Code Quality Rules

**Purpose**: 代碼質量標準與 V2 11+1 範疇對齐規範。

**Category**: Development Process / Standards
**Created**: 2025
**Last Modified**: 2026-04-28
**Status**: Active

> **Modification History**
> - 2026-04-28: Enhance for V2 — 新增範疇層級 Coverage 目標、命名一致性、Type Hints 強度、Lint Hook 順序
> - 2025: Initial V1 version (generic Python/TS rules)

---

## Python (Backend)

### Formatting
- **Formatter**: Black (line-length: 100)
- **Import Sorter**: isort (profile: black)
- **Type Checker**: mypy (strict mode)
- **Linter**: flake8

### Quick Commands
```bash
cd backend && black . && isort . && flake8 . && mypy .
```

### Requirements
- Type hints on all public functions
- Docstrings on all public classes/functions
- No unused imports
- No commented-out code in commits

---

## TypeScript (Frontend)

### Formatting
- **Formatter**: Prettier
- **Linter**: ESLint

### Quick Commands
```bash
cd frontend && npm run lint && npm run build
```

### Requirements
- Explicit types (avoid `any`)
- Interface for all component props
- No unused variables
- No console.log in production code

---

## Test Coverage（Baseline）

- Minimum: **80%** coverage（per `testing.md`）
- New features MUST include unit tests
- Never delete tests to make CI pass

---

## Code Review Checklist

- [ ] Code follows project style guides
- [ ] All tests pass
- [ ] No security vulnerabilities
- [ ] No breaking changes without migration plan
- [ ] Documentation updated if needed
- [ ] Anti-patterns checklist (11 points) passed (`anti-patterns-checklist.md`)
- [ ] File header updated (`file-header-convention.md`)
- [ ] Sprint workflow compliance (`sprint-workflow.md`)

---

## V2 新增：範疇層級 Coverage 目標

V2 按 11+1 範疇劃分代碼，各層級 coverage 目標：

### 業務邏輯層（範疇 1-11）

| 範疇 | 目標 | 備註 |
|------|------|------|
| 1. Orchestrator Loop | ≥ 85% | 核心 Loop 邏輯 |
| 2. Tool Layer | ≥ 85% | 工具 registry / schema validate |
| 3. Memory | ≥ 80% | 5 層記憶 + 租戶隔離 |
| 4. Context Management | ≥ 80% | Token counter / compaction |
| 5. Prompt Construction | ≥ 80% | 階層組裝 |
| 6. Output Parsing | ≥ 85% | 工具呼叫解析 |
| 7. State Management | ≥ 85% | Checkpoint / 序列化 |
| 8. Error Handling | ≥ 80% | 重試策略 / 分類 |
| 9. Guardrails | ≥ 85% | 安全檢測 |
| 10. Verification | ≥ 80% | 驗證器 / Self-correction |
| 11. Subagent | ≥ 80% | 子代理執行 |
| **12. Observability** | ≥ 70% | 埋點覆蓋率測試（見 testing.md） |

### 平台層

| 模組 | 目標 | 備註 |
|------|------|------|
| `agent_harness/` (domain) | ≥ 90% | 核心 harness 邏輯 |
| `platform/governance/` | ≥ 95% | 安全核心，不可出錯 |
| `adapters/` | ≥ 85% | 含 contract test（跨 provider） |
| `infrastructure/` | ≥ 70% | DB / Redis / 儲存 |
| `business_domain/` | ≥ 80% | 企業邏輯 |

---

## V2 新增：11+1 範疇命名一致性

代碼中的模組名 / 類名 / 函數名**必須**與對應範疇定義同一詞彙，避免混淆：

### 命名對照

| 違規例 | 正確例 | 說明 |
|-------|--------|------|
| `OrchestrationPipeline` | `AgentLoop` / `LoopExecutor` | 範疇 1 不是 Pipeline |
| `Validator` | `Verifier` | 範疇 10 用 Verifier，避免與 Python 內建混淆 |
| `ToolCall` (ambiguous) | `ToolCallRequest` / `ToolCallExecuted` | 明確狀態 |
| `Memory` | `MemoryLayer` / `MemoryStore` | 5 層分明 |
| `Agent` (broad) | `SubagentExecutor` / `TeammateCommunicator` | 精確角色 |
| `Loop` (V1 遺留) | `AgentLoop` + `LoopState` + `LoopEvent` | 與 TAO/ReAct 詞彙一致 |

### 模組路徑應映射範疇

```
backend/src/agent_harness/
├── orchestrator_loop/      # 範疇 1
│   ├── agent_loop.py       # 類名 AgentLoop
│   └── loop_event.py
├── tools/                  # 範疇 2
│   ├── tool_spec.py        # ToolSpec ABC
│   └── tool_registry.py
├── memory/                 # 範疇 3
│   ├── memory_layer.py     # 5 層結構
│   └── memory_store.py
# ...
```

詳見 `category-boundaries.md`。

---

## V2 新增：Type Hints 強度

### 最低標準

- **必須**：`agent_harness/` 所有 public 函數 / 類 → 100% type hint
- **必須**：`platform/governance/` → 100% type hint（安全核心）
- **必須**：`adapters/` → 100% type hint
- **建議**：業務層 ≥ 90%

### 執行

```toml
# pyproject.toml
[tool.mypy]
strict = true
warn_unused_ignores = true
plugins = ["sqlalchemy.ext.mypy.plugin"]

# 個別 module 要 skip 必須 # type: ignore[error-code] + 註解原因
```

---

## V2 新增：Cross-platform mypy `# type: ignore[X, unused-ignore]` Pattern

**Source**: Sprint 52.6 retrospective Q4（CI mypy 在 Linux runner 與 Windows 開發機行為不一致 — 某 platform 缺 stub 包）

### 問題

同一 import / Optional unwrap 在不同 platform 上 mypy 行為不同：
- 一邊安裝了 type stub → 該行**不需要** `# type: ignore`
- 另一邊缺 type stub → 該行**需要** `# type: ignore[import-not-found]`

若兩平台都需要 CI 全綠（local Windows 開發 + Linux GitHub Actions），單純加 `# type: ignore` 在缺 stub 一邊可解，但有 stub 一邊會抱怨「unused ignore」（`warn_unused_ignores = true` strict 模式下）。

### 標準解：雙 ignore code

```python
from foo import Bar  # type: ignore[import-not-found, unused-ignore]
```

- `[import-not-found]`：缺 stub 平台抑制找不到錯誤
- `[unused-ignore]`：有 stub 平台允許「無用的 ignore」不報錯

### 三個常見場景

#### 1. Optional dependency（如 redis.asyncio）

```python
# 本地 Linux 安裝了 redis stubs；CI 容器可能未裝
from redis.asyncio import Redis  # type: ignore[import-not-found, unused-ignore]
```

#### 2. Platform-specific module（如 winreg / msvcrt）

```python
import sys

if sys.platform == "win32":
    import winreg  # type: ignore[import-not-found, unused-ignore]
```

#### 3. Conditional Optional unwrap

某些 helper 在 platform A 返回 `T | None` 但在 platform B 返回 `T`：

```python
result: int | None = compute()
# Linux: result is `int`; Windows: result is `int | None`
final: int = result  # type: ignore[assignment, unused-ignore]
```

### 反模式（禁止）

```python
# ❌ 禁止：bare # type: ignore (吞掉所有錯誤類型；無法 grep)
from foo import Bar  # type: ignore

# ❌ 禁止：disable warn_unused_ignores 全域繞過
[tool.mypy]
warn_unused_ignores = false  # ← 會掩蓋 dead ignores

# ❌ 禁止：跨平台分支 if sys.platform: + 雙 import 完整重寫
```

### 適用範圍

只用於**真實**的 cross-platform 不一致場景（CI vs local）。不要當「萬用消音器」濫用。

### Reference

- Sprint 52.6 retrospective Q4：[`docs/03-implementation/agent-harness-execution/phase-52-6/sprint-52-6-ci-restoration/retrospective.md`](../../docs/03-implementation/agent-harness-execution/phase-52-6/sprint-52-6-ci-restoration/retrospective.md)
- mypy docs：[mypy_silencing-linters](https://mypy.readthedocs.io/en/stable/error_code_list.html#code-unused-ignore)

---

## V2 新增：Lint Hook 順序

### Pre-commit Hook (< 10 秒)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/isort
    hooks:
      - id: isort
  - repo: https://github.com/astral-sh/ruff
    hooks:
      - id: ruff
        args: [--fix]
```

### Pre-push Hook (< 60 秒)

```bash
# .git/hooks/pre-push
#!/bin/bash
set -e
echo "Running mypy strict mode..."
python -m mypy backend/src --strict
echo "Running flake8..."
python -m flake8 backend/src
echo "Checking cross-category imports (Phase 49.4+)..."
python scripts/check_cross_category_imports.py
echo "Checking LLM SDK imports..."
python scripts/check_llm_neutrality.py
```

### CI（GitHub Actions）

```yaml
# .github/workflows/code-quality.yml
name: Code Quality
on: [pull_request, push]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install mypy flake8 ruff black isort
      - run: black --check backend
      - run: isort --check backend
      - run: mypy backend/src --strict
      - run: flake8 backend/src
      - run: python scripts/check_cross_category_imports.py
      - run: python scripts/check_llm_neutrality.py
      - run: python scripts/check_tenant_isolation.sh
```

---

## 引用

- **11-test-strategy.md** — 測試策略 / Coverage targets
- **category-boundaries.md** — 11+1 範疇命名與 import 規則
- **anti-patterns-checklist.md** — AP-3 / AP-6 / AP-11
- **llm-provider-neutrality.md** — Lint rule 1-3
- **testing.md** — 測試命令與規範
- **file-header-convention.md** — 檔案開頭規範
