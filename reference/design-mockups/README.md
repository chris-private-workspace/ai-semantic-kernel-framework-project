# IPA Platform V2 — Operator Portal (Design Prototype)

> **這是什麼**：一個 hi-fi 互動原型（pure HTML + React via Babel，無 build step），呈現 IPA Platform V2 後台 operator portal 的設計方向。對應 GitHub repo：[`laitim2001/ai-semantic-kernel-framework-project`](https://github.com/laitim2001/ai-semantic-kernel-framework-project)。

---

## 快速開始

```bash
# 任何能 serve static file 的方式都行
python -m http.server 8080
# 或
npx serve .
```

然後開 `http://localhost:8080/index.html`。**不需要 npm install / build**。

技術棧：
- React 18.3.1（UMD via unpkg）
- Babel Standalone 7.29.0（瀏覽器端 JSX 編譯）
- 無 bundler、無 npm dependencies、無 backend

---

## 檔案結構

```
.
├── index.html              # 入口；載入所有 .jsx
├── styles.css              # design tokens + 全域樣式
├── i18n.jsx                # 中英文翻譯字典（t() 函式）
├── tweaks-panel.jsx        # 右上角 Tweaks 面板（換主題、密度、語言）
├── ui.jsx                  # 共用元件（Button / Icon / Badge / Card …）
├── shell.jsx               # ⭐ ROUTES 註冊表 + Sidebar + Topbar
├── topbar-overlays.jsx     # CommandPalette / NotificationsPanel / UserMenu（Topbar 點開的面板）
├── app.jsx                 # Routerￔmount rootￔ元件路由表
├── page-overview.jsx       # ⭐ Unified dashboard（operator landing）
├── page-chat.jsx           # Chat V2 主頁
├── page-governance.jsx     # Governance / Verification / Audit / Redaction
├── page-admin.jsx          # Tenants / Tenant Settings / RBAC / MFA / Profile
├── page-extras.jsx         # Cost / SLA / Memory / Loop Debug / Incidents … + AuthLogin/Callback/Dev
├── page-auth-extras.jsx    # AuthRegister / AuthInvite / AuthMFA / AuthExpired
├── page-tools.jsx          # Tools / Feature Flags
├── page-sse.jsx            # SSE Inspector
├── page-platform.jsx       # State Inspector / Compaction / Workflows / Error Policy
├── page-platform2.jsx      # Tenant Onboarding / Pricing / DevUI / Domain Detail
├── page-agents.jsx         # Orchestrator / Subagents Registry / Subagent Tree
├── page-models.jsx         # Models / JIT Retrieval / Cache Manager
│
├── README.md               # ⬅ 本檔
├── DESIGN_RATIONALE.md     # ⭐ 每個頁面的存在原因（必讀）
└── AGENTS.md               # ⭐ 給未來 AI 助手的開發守則（必讀）
```

---

## ⭐ 必讀文件（修改前請先看）

| 檔案 | 何時讀 |
|---|---|
| `DESIGN_RATIONALE.md` | 想知道某個頁面為什麼存在、對應 V2 哪個範疇規格 |
| `AGENTS.md` | 想新增 / 修改 / 刪除頁面、為下一個 AI 助手 onboarding |
| `shell.jsx` 的 `ROUTES` 陣列 | 看當前所有 menu 項與其狀態（active / proposed / designed） |
| repo 的 `frontend/src/routes.config.ts` | V2 官方頁面註冊表（13 個 ship target） |
| repo 的 `docs/03-implementation/agent-harness-planning/01-eleven-categories-spec.md` | V2 後端 11+1 範疇規格 |

---

## 頁面狀態三色制

每個 menu 項在 `shell.jsx` 註冊時有 3 種狀態標籤：

| 標籤 | 意義 | UI 呈現 |
|---|---|---|
| `active: true` | 已在 V2 routes.config.ts 或設計已 ship | 正常可點 |
| `proposed: true` | V2 後端範疇 spec 內有對應 ABC，但 routes.config.ts 還沒 ship | 藍色 `PROP` 徽章 |
| `designed: true, active: false` | 已畫好，但 V2 registry 還未收錄 | 黃色 `DRAFT` 徽章 |
| 兩者皆無 | 純佔位 | 灰色 `SOON` |

詳細對應表見 `DESIGN_RATIONALE.md`。

---

## 整合進 Claude Code 項目的方式

### 選項 A — 純設計參考（推薦）

把整個資料夾放在 repo 根目錄的 `design/` 或 `frontend/design-prototype/` 下：

```
ai-semantic-kernel-framework-project/
├── backend/
├── frontend/
│   └── src/...
├── design/                ← 放這裡
│   └── operator-portal/
│       ├── index.html
│       ├── *.jsx
│       └── DESIGN_RATIONALE.md
└── docs/
```

優點：與 production code 完全隔離，AI 助手實作 V2 frontend 頁面時可以直接打開 `design/operator-portal/index.html` 在瀏覽器看設計，再對照 `routes.config.ts` 補實作。

### 選項 B — 收進 docs/

把整包放在 `docs/04-design/operator-portal-prototype/`，與其他規格文件並列。

無論哪種放法，**`DESIGN_RATIONALE.md` 與 `AGENTS.md` 一定要跟著走**——它們是未來 AI 助手理解這份原型的鑰匙。

---

## 與 V2 routes.config.ts 的對應關係（摘要）

完整對應表見 `DESIGN_RATIONALE.md`，這裡只給一張統計表：

| 類別 | 本 portal | V2 routes.config.ts | 差距 |
|---|---|---|---|
| V2 ship target 頁面 | 13 | 13 | 100% 對齊 |
| 範疇 spec 對應的 PROP 頁 | 13 | 0 | 為了「展示完整 agent harness 視角」加上 |
| V1 IPA 業務 / 設計擴充頁 | 7 | 0 | 對映業務面向：incidents / domain-* / tenant-onboarding / pricing |

> **設計理念**：本 portal 不只展示「V2 已 ship」，而是把 12 範疇 spec 內每個 ABC 都實體化為一個 operator 視角頁面，讓 stakeholder 能視覺化整套 agent system 的所有控制面。詳見 `DESIGN_RATIONALE.md` §設計哲學。

---

## 已知限制

- **無真實資料**：所有數字、表格、log 都是 mock，寫死在各 `.jsx` 內
- **無真實後端**：頁面間不會持久化資料；hash route 即頁面狀態
- **i18n 限中英**：見 `i18n.jsx`
- **無 build pipeline**：因此檔案數量受控（每檔 < 1000 行）；要新增頁面，建議用 `page-platform3.jsx` 等檔案接續，不要再加大現有檔案

---

## License

與主 repo 一致（Proprietary）。
