# Chat-V2 Drive-Through 發現:python_sandbox 在 chat 主流量壞掉(Windows Selector loop)

**Date**: 2026-06-18
**Type**: Drive-Through finding / Bug diagnosis (fix pending user decision)
**Scope**: 範疇 2 (Tool Layer) — python_sandbox / SandboxBackend wiring on chat 主流量
**Verifier**: 真 UI(Playwright)+ 真後端(uvicorn :8000)+ 真 LLM(Azure gpt-5.2),dan@acme.com / acme-prod

---

## 背景

接續對 chat-v2 主流量做「營運分析師資料分析」drive-through(T1:14 天 p95 延遲 → 要 agent 用 Python 算 mean/std/min/max + 找異常)。目的之一是定位上次「agent 答 219.93 但正確值 = 227.0」的根因(python 算錯 vs LLM 轉述失真)。

---

## 哪些控件/流程「真的能用」(drive-through PASS)

| 項目 | 結果 |
|------|------|
| dev-login(dan@acme.com / acme-prod / admin) | ✅ 可登入 |
| New session 按鈕 | ✅ 真的開乾淨對話(非死控件) |
| mode = real_llm | ✅ 藍色高亮 active(非 echo_demo) |
| 送出訊息 → agent 串流 | ✅ 正常 |
| python_sandbox 觸發 HITL 暫停(MEDIUM / always_ask) | ✅ Approval 卡片正確出現 |
| HITL **Approve & continue** | ✅ 有效(loop 恢復) |
| HITL **Reject** | ✅ 有效(decision=REJECTED → loop 結束) |
| Loop 事件流 / Inspector Turn metadata(tokens/model/trace_id) | ✅ 正確渲染 |

---

## 哪個壞了(drive-through FAIL)

**`python_sandbox` 工具實際執行時立即 `0ms` 失敗,UI 顯示 `unknown tool error`,從未真正執行。**

- agent 連續 3 次嘗試(z-score 法 → IQR 法 → 第 3 次),每次批准後都 ERROR,陷入「失敗→換方法重試→再要批准」迴圈;最終 Reject 後 loop 收場,**沒有產出任何統計答案**。
- 後端 `tool_call_request` 帶的程式碼/資料**完全正確**(`[142,138,...,510]`),所以不是資料錯。

---

## 根因(決定性確認)

### 因果鏈
1. chat path 的 `python_sandbox` 寫死用 **`SubprocessSandbox`**,不是 `default_sandbox()`/Docker
   - `business_domain/_register_all.py::make_default_executor` 呼叫 `register_builtin_tools(...)` 時**未傳 `sandbox_backend`**
   - `tools/__init__.py:89` `make_python_sandbox_handler(sandbox_backend=None)`
   - `exec_tools.py:75` `sandbox = backend or SubprocessSandbox()` → 落到 SubprocessSandbox
2. `SubprocessSandbox.execute` 用 `asyncio.create_subprocess_exec`(`sandbox.py:153`)
3. chat 後端 uvicorn 跑在 **Windows SelectorEventLoop** 上 → `create_subprocess_exec` **立即拋 `NotImplementedError`(訊息為空字串)**
4. 空訊息 → `loop.py:3061` `error=result.error or "unknown tool error"` → UI 顯示「unknown tool error」,`0ms`

### 決定性重現(用後端同一支 python `Python312\python.exe`)
```
PROACTOR  → OK   exit=0  stdout='227.0 222.0208 128.0 920.0'   # mean=227.0 正確
SELECTOR  → RAISED NotImplementedError ('')                     # 空訊息,0ms
```

→ **python 沒算錯**(Proactor 下精確算出 227.0);問題是**工具在 chat 後端的 Selector loop 上根本沒跑**。
→ 上次「219.93」= 工具失敗後 agent 退回(錯誤)心算,**不是 LLM 轉述失真**。

### 補充
- Docker **正在跑**(server 29.5.2,8 容器),sandbox image `ipa-v2-sandbox:latest`(177MB)**已建好** —— 但 chat path 不會用到 Docker。
- sprint 57.118 的「REAL Docker sandbox」是另一個工具 `run_skill_script`(用 `default_sandbox()`→Docker),不是 python_sandbox。
- `SandboxBackend` 自己的 W4P-3 audit 註解已明載:SubprocessSandbox 在 Windows 上「decorative」、PRODUCTION-UNSAFE,「PRODUCTION DEPLOY MUST USE DockerSandbox」。

---

## 修法選項(待用戶決定)

| 選項 | 改動 | 評估 |
|------|------|------|
| **A(建議)Docker 接線** | `make_default_executor` 把 `register_builtin_tools(..., sandbox_backend=<shared DockerSandbox>)`(經 `default_sandbox()`,做成 process-wide singleton 仿 skills/tool.py) | ✅ 對齊 codebase 自身產線意圖;Docker+image 已就緒;loop-agnostic(用 `asyncio.to_thread`+docker SDK,不碰 `create_subprocess_exec`)。需驗:per-request 不重複 ping Docker |
| B 改 uvicorn 用 Proactor loop | 啟動時 `WindowsProactorEventLoopPolicy()` | ⚠️ 脆弱(uvicorn 可能覆寫);可能影響 Windows DB driver;只解 dev 環境 |
| C SubprocessSandbox loop-agnostic | `sandbox.py` 在獨立 thread 用 Proactor loop 跑子程序 | 自包含,但 SubprocessSandbox 仍無隔離(audit 判 unsafe);治標 |

---

## 修後驗證(FIX-033 + Fix A numpy + Fix B print)— T1/T2/T3 全通 ✅

採選項「修 A+B 再完成三輪」:
- **Fix A**:`docker/sandbox/Dockerfile` 加 `pip install numpy`,rebuild `ipa-v2-sandbox:latest`(numpy 2.4.6;硬化條件下實測 mean 227.0 ✅)。
- **Fix B**:`exec_tools.py` `PYTHON_SANDBOX_SPEC.description` 明示「腳本執行非 REPL、必須 print()、numpy 可用」。
- 乾淨重啟後端(過程踩到並修正了過度激進的孤兒判定:detached 啟動的新進程 launcher 已死,不可當孤兒;應以 StartTime 早於本次重啟判定)。

修後真 UI + 真後端 + 真 LLM gpt-5.2 三輪結果(每輪 HITL Approve,數字均獨立驗算):

| 輪 | 驗證重點 | 結果 |
|----|---------|------|
| **T1** | 工具真執行 + 計劃 + 正確統計 | python_sandbox 在 Docker 跑(無 error)、agent 宣告計劃、stdout `mean 227.0`、agent 答案 **227.0**(= stdout = 獨立計算);IQR 異常 第8天(920)+第14天(510),z-score 第8天。**1 次工具呼叫完成**、Verification passed。「219.93」根除。 |
| **T2** | 跨輪記憶 + 重判 | agent 回想 T1 數據,套新 2σ 規則:門檻 **671.0416**,真正異常**僅第8天920**(510 未達);LLM Judge 0.99。 |
| **T3** | 記憶複用 + 多步比較 | 一次算兩週:w1(227.0/671.04/第8天)+ w2(297.214/357.919/1013.05/第2天1250);結論「兩週各1異常天,但第二週均值更高波動更大 → 第一週較健康」;全數字獨立驗算一致;LLM Judge 0.99。 |

→ **端到端展示成立**:計劃宣告 / python_sandbox 真執行 / HITL 可控 / 跨輪記憶 / 多步推理 / 驗證迴圈,全部真實運作且數字正確。

## 證據檔
- `dt-01-after-login-new-session.png`(real_llm 確認)
- `dt-02-t1-typed.png`(輸入正確)
- `dt-03-t1-after-send.png`(HITL 暫停 + python code)
- `dt-04-t1-python-sandbox-broken-end.png`(修前:3 次 ERROR + REJECTED 收場)
- `dt-05-t1-fix033-docker-executes-but-numpy-and-print.png`(FIX-033 後:Docker 執行但 numpy 缺 + 不 print)
- `dt-06-t1-success-227.png`(A+B 後:227.0 正確 + Verification passed)
- `dt-07-t3-cross-week-memory-success.png`(T3 跨週記憶比較成功)

## 註:工具污染(context-mode plugin)
本次測試在 Claude Code 工具層(Bash/Read/PowerShell)出現 prompt-injection canary 污染(來自 context-mode plugin),詳見 `memory/feedback_context_mode_plugin_prompt_injection.md`。**app 的 UI/SSE(經 Playwright 讀取)全程乾淨**,故以上 app 行為判讀不受污染影響;所有 shell 輸出均已掃 canary 確認乾淨後採信。
