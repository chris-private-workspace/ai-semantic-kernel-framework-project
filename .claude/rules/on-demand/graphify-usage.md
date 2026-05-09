# Graphify 使用提示（給 Claude Code）

**Purpose**: 提示 AI 助手如何利用本專案根的 `graphify-out/` 加速閱讀理解，減少不必要的源碼掃描。

**Category**: AI Assistant Tooling
**Created**: 2026-04-28
**Last Modified**: 2026-04-28
**Status**: Active

**Modification History**:
- 2026-04-28: Initial creation — 補充 CLAUDE.md §graphify 段落，定位為純本地閱讀工具

---

## 角色定位（重要）

graphify = **Claude Code 本地閱讀加速器**

- 給 AI 助手（Claude Code）用的內部工具
- 在回答架構或代碼問題前，先讀 graph 比爬全 codebase 省 token
- **不參與** PR review / CI / 工程治理 / 範疇對齐強制
- 不是 dev policy，不影響 commit / merge

---

## 何時讀 graphify

### ✅ 該讀

- 用戶問「這個 module 跟誰有關」「這段架構為何這樣」
- 開始一個跨檔案的研究任務
- 想找 god nodes（最關鍵的概念節點）
- 探索 community（功能群聚）

### ❌ 不必讀

- 用戶給明確路徑要求 Read / Edit
- 純 grep 找字串
- 改一個小 typo / format

---

## 閱讀順序（高效進入）

```
1. graphify-out/GRAPH_REPORT.md  ← 起點
   ├─ L1-10：summary（哪個 god node 重要、整體結構）
   ├─ L2184-2322：god nodes + surprising connections + hyperedges
   └─ L2323+：community 詳細（用 Grep 跳到特定 community）

2. graphify-out/wiki/index.md（若存在）
   ← 比 GRAPH_REPORT 更易讀的概覽，優先此檔
```

---

## 信任度區分（CRITICAL）

當前 graph 約 **25% EXTRACTED / 75% INFERRED**。

| 類型 | 來源 | 信任度 | 怎麼用 |
|------|------|--------|--------|
| **EXTRACTED** | 代碼 AST / 顯式 import | 95%+ | 直接引用 |
| **INFERRED** | LLM 假說 | ~75% | 當假說處理，引用前驗證 |

### 三類資訊的信任策略

| 資訊類型 | 多半是 | 引用策略 |
|---------|-------|--------|
| **God Nodes 與 Community structure** | EXTRACTED | 高信任，直接用 |
| **Surprising Connections** | INFERRED | 假說，引用前用 Read / Grep 驗證 |
| **架構理由（為何 X 連 Y）** | 混合 | 用 `/graphify explain <node>` 看支撐邊類型；若只有 INFERRED 支撐，回答時明示「待驗證」 |

### 範例

```
✅ 正確：
「根據 graphify，god node 02_ToolSpec 跟 04_ContextMgmt 有關係
（INFERRED 邊；用 grep 驗證後，確實在 tools/spec.py:42 import 了
context_mgmt.token_counter）。」

❌ 不好：
「graphify 顯示 02_ToolSpec 與 04_ContextMgmt 強耦合。」
（沒驗證 INFERRED 邊就斷言）
```

---

## 更新節奏

| 動作 | 何時 | 成本 |
|------|------|------|
| `graphify update .` | 代碼變更後（.py / .ts / .tsx） | Free（manifest diff） |
| `/graphify --update` | docs / markdown / PDF / 圖片變更 | Paid (LLM) |
| `/graphify .` | 全重建（罕用） | Paid (LLM) |

預設：每次 code commit 後 `graphify update .` —— 用 manifest diff，小變更幾乎瞬間完成。

---

## Scope Control（避免成本爆炸）

### `.graphifyignore` 必須存在於專案根

`graphify update .` **不會記住**初次 build 時排除哪些目錄。缺少 `.graphifyignore` 會把 `reference/`（2,213 files）/ `claudedocs sample/`（217 files）/ debug PNG（~124 files）全納入。

### 驗證 scope

```bash
python -c "from graphify.detect import detect; from pathlib import Path; r = detect(Path('.')); print(f'{r[\"total_files\"]} files, {r[\"graphifyignore_patterns\"]} ignore patterns')"
# 預期：~3,300 files、30 ignore patterns
```

### 若 > 5,000 files

停下，修 `.graphifyignore`：
- 確認 `node_modules/` / `.venv/` / `archived/` / `reference/` 在內
- 確認 debug 產出物（`*.png` 等）在內

---

## 限制

- INFERRED 邊是 LLM 假說，**不是事實**
- LLM 可能因「兩個 class 都用 logger」就推斷它們有 coupling，實際上沒有
- 整體用作**探索 / 加速理解**，不能當作架構決策的唯一根據

---

## 引用

- `CLAUDE.md` §graphify（L582+）— 主規範
- `graphify-out/GRAPH_REPORT.md` — graph 結構
- `graphify-out/wiki/index.md` — 易讀概覽（若存在）
