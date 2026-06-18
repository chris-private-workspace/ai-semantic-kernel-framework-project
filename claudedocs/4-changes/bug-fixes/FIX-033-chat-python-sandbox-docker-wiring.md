# FIX-033: chat python_sandbox 在 Windows Selector loop 上 0ms「unknown tool error」

**Date**: 2026-06-18
**Sprint**: drive-through finding (ad-hoc; not a sprint)
**Scope**: 範疇 2 (Tool Layer) — `python_sandbox` SandboxBackend wiring on chat 主流量

## Problem

chat-v2 主流量上,agent 呼叫 `python_sandbox` 工具(批准後)立即 `0ms` 失敗,UI 顯示 `unknown tool error`,工具從未真正執行。agent 連續換方法重試仍全失敗,無法產出統計結果。drive-through 發現(真 UI + 真後端 + 真 LLM)。

## Root Cause

決定性確認(用後端同一支 `Python312\python.exe` 重現):

```
PROACTOR  → OK   exit=0  stdout='227.0 222.0208 128.0 920.0'   # 正確
SELECTOR  → RAISED NotImplementedError ('')                     # 0ms,空訊息
```

因果鏈:
1. chat path 的 `python_sandbox` 落到 **`SubprocessSandbox`**:`business_domain/_register_all.py::make_default_executor` 呼叫 `register_builtin_tools(...)` **未傳 `sandbox_backend`** → `exec_tools.py:75` `backend or SubprocessSandbox()`。
2. `SubprocessSandbox.execute` 用 `asyncio.create_subprocess_exec`(`sandbox.py:153`)。
3. uvicorn 在 **Windows SelectorEventLoop** 上跑 → `create_subprocess_exec` 立即拋 `NotImplementedError`(`str()` 為空)。
4. 空訊息 → `loop.py:3061` `error=result.error or "unknown tool error"` → UI 顯示「unknown tool error」、`0ms`。

補充:`SandboxBackend` 的 W4P-3 audit 註解早已載明 SubprocessSandbox 在 Windows「decorative / PRODUCTION-UNSAFE」、「PRODUCTION DEPLOY MUST USE DockerSandbox」。Docker daemon 在跑、image `ipa-v2-sandbox:latest`(177MB)已建好,但 chat path 未接 Docker。前次「219.93 vs 227.0」即工具失敗後 agent 退回錯誤心算的產物(非 LLM 轉述失真)。

## Solution

`business_domain/_register_all.py`:
- 新增 import `from agent_harness.tools.sandbox import SandboxBackend, default_sandbox`。
- 新增 process-wide lazy singleton `_get_shared_sandbox()`(鏡像 `skills/tool.py:153-161`;`default_sandbox()` 只探測 Docker 一次,非每請求)。
- `make_default_executor` 的 `register_builtin_tools(...)` 加 `sandbox_backend=_get_shared_sandbox()`。

設計理由:
- `default_sandbox()` Docker 可達回 **DockerSandbox**(loop-agnostic:docker SDK 經 `asyncio.to_thread`,不碰 `create_subprocess_exec`),不可達 fallback `SubprocessSandbox`(**CI 行為不變**)。
- 只改 `make_default_executor` 接線點(chat / child / teammate executors),**不改** `make_python_sandbox_handler` 全域預設 → 直接呼叫該 factory 的既有測試不受影響(surgical)。

## Verification

- 重現腳本(Proactor vs Selector)+ UI drive-through 觀察(見 `claudedocs/5-status/chat-v2-python-sandbox-drivethrough-20260618.md`)。
- gate:black/isort/flake8/mypy 乾淨;`test_builtin_tools` + business_domain 工廠/模式 + chat keystone wiring + main flow = **58 tests passed**。
- **修後 drive-through(已執行,真 UI + 真後端重啟 + 真 LLM gpt-5.2)**:
  - 乾淨重啟後端(殺 reloader 56292 + 清 57.97 孤兒 worker 46056),新進程 48612/17376 跑新碼。
  - 重跑 T1,批准 python_sandbox → **工具真的在 Docker 執行**:tool result 帶 `duration_seconds≈0.5-0.6`、真實 `exit_code`/`stderr`;**「0ms unknown tool error」完全消失**。
  - ✅ **FIX-033 scope(讓 python_sandbox 在 chat 真正執行)達成並驗證。**

### ⚠️ 下游新問題(FIX-033 之外,獨立 issue)

修好 wiring 後 drive-through 揭露 2 個 end-to-end 仍未通的下游問題(與本 FIX 無關,留待後續決定):
1. **sandbox image 缺 numpy**:`ipa-v2-sandbox:latest` 無 numpy → agent 的 numpy code 第一次回 `ModuleNotFoundError`(exit_code=1)。
2. **腳本執行 vs REPL 語意**:python_sandbox 跑 `python main.py`(腳本),agent 程式碼以**裸表達式結尾**(如 `(q1,q3,iqr,lb,ub,anom)`)無 `print()` → exit_code=0 但 **stdout 空** → agent 拿不到結果而反覆重試。
   - 可能解:tool description 明示「必須 print()」,或 sandbox 包裝成 auto-display 最後一個表達式(REPL 式)。

## Impact

Backend-only。影響 chat / child / teammate executors 的 `python_sandbox`(改用 Docker)。Docker 不可達環境(CI)維持 SubprocessSandbox 行為,向後相容。無 migration、無 schema、無 frontend 改動。

## Related
- `claudedocs/5-status/chat-v2-python-sandbox-drivethrough-20260618.md`(完整發現 + 證據)
- `agent_harness/tools/sandbox.py`(SandboxBackend / default_sandbox / W4P-3 audit 註解)
- `agent_harness/skills/tool.py:153-161`(被鏡像的 singleton 模式)
