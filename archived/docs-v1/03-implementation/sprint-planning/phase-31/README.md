# Phase 31: Security Hardening + Quick Wins

## 概述

Phase 31 是 6 位領域專家深度分析後的**第一優先改善階段**（對應改善方案建議書 Phase A），專注於 **安全加固與速效修復**，目標是讓 IPA Platform 達到「可以安全地內部展示」的狀態。

當前平台安全評分僅 1/10：Auth 覆蓋率 7%（38/528 端點）、無 Rate Limiting、JWT Secret 硬編碼、MCP 28 個 Permission Pattern 完全未啟用、18 個 Mock 類混在生產代碼中。本 Phase 將系統性修復這些問題。

**基於**: [`docs/07-analysis/Overview/IPA-Platform-Improvement-Proposal.md`](../../07-analysis/Overview/IPA-Platform-Improvement-Proposal.md) (Phase A)

## 目標

1. **速效修復** - CORS/Vite 端口不匹配、JWT Secret 硬編碼、authStore PII 洩漏、Docker 預設憑證
2. **全局 Auth** - 從 7% 提升到 100% Auth 覆蓋率，所有 528 端點均需認證
3. **Sessions 偽認證修復** - 移除硬編碼 UUID，接入真實 JWT 用戶提取
4. **Rate Limiting** - 添加 slowapi API 防濫用
5. **Mock 代碼分離** - 18 個 Mock 類從生產代碼遷移到 tests/mocks/，導入 Factory Pattern
6. **InMemory 存儲替換** - InMemoryApprovalStorage 遷移到 Redis
7. **MCP 安全閉環** - Permission Pattern 運行時啟用 + Shell/SSH 命令白名單
8. **並發安全最小修復** - ContextSynchronizer 添加 asyncio.Lock

## 前置條件

- ✅ Phase 29 完成 (Agent Swarm 可視化，Sprint 100-106)
- ✅ AG-UI Protocol SSE 基礎設施就緒
- ✅ 6 位領域專家分析報告完成
- ✅ IPA Platform 統一改善方案建議書完成

## Sprint 規劃

| Sprint | 名稱 | Story Points | 狀態 |
|--------|------|--------------|------|
| [Sprint 111](./sprint-111-plan.md) | Quick Wins + Auth Foundation | 40 點 | 📋 計劃中 |
| [Sprint 112](./sprint-112-plan.md) | Mock Separation + Redis Storage | 45 點 | 📋 計劃中 |
| [Sprint 113](./sprint-113-plan.md) | MCP Security + Validation | 40 點 | 📋 計劃中 |

**總計**: ~125 Story Points (3 Sprints)
**預估時程**: 3 週 (無緩衝 — 所有任務均為安全必要項目)

## 架構概覽

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    Phase 31: Security Hardening 影響範圍                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                           Frontend (React 18)                                │    │
│  │                                                                              │    │
│  │   🔧 vite.config.ts — proxy port 8010→8000                                 │    │
│  │   🔧 authStore.ts — 移除 5 個 console.log (PII 洩漏)                       │    │
│  │                                                                              │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                          │ HTTP                                      │
│                                          ↓                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                           Backend (FastAPI)                                  │    │
│  │                                                                              │    │
│  │   🔒 core/config.py — CORS origin 3000→3005                                │    │
│  │   🔒 core/security.py — JWT Secret 環境變量化                               │    │
│  │   🔒 api/v1/ — 全局 Auth Middleware (528 端點 100% 覆蓋)                   │    │
│  │   🔒 sessions — 移除硬編碼 UUID，真實 JWT 用戶提取                          │    │
│  │   🔒 middleware/rate_limit.py — slowapi Rate Limiting (🆕)                  │    │
│  │   🔒 main.py — reload=True → 環境感知                                       │    │
│  │                                                                              │    │
│  │   ┌──────────────────────────────────────────────────────────────────────┐  │    │
│  │   │                 integrations/orchestration/                           │  │    │
│  │   │   🧹 18 Mock 類 → tests/mocks/ (Factory Pattern)                    │  │    │
│  │   │   🔒 LLMServiceFactory — 移除靜默 fallback                          │  │    │
│  │   └──────────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                              │    │
│  │   ┌──────────────────────────────────────────────────────────────────────┐  │    │
│  │   │                    integrations/mcp/                                  │  │    │
│  │   │   🔒 Permission Pattern 運行時啟用 (28 patterns → 實際檢查)          │  │    │
│  │   │   🔒 Shell/SSH MCP 命令白名單 + HITL 審批                           │  │    │
│  │   └──────────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                              │    │
│  │   ┌──────────────────────────────────────────────────────────────────────┐  │    │
│  │   │                    integrations/hybrid/                               │  │    │
│  │   │   🔒 ContextSynchronizer — asyncio.Lock 最小修復                     │  │    │
│  │   └──────────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                              │    │
│  │   🔒 InMemoryApprovalStorage → Redis (HITL 審批持久化)                    │    │
│  │                                                                              │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                          │                                           │
│                                          ↓                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                      Infrastructure                                          │    │
│  │                                                                              │    │
│  │   🔧 docker-compose.yml — 移除預設 admin/admin123 憑證                     │    │
│  │   🔒 Redis — 新增 ApprovalStorage 持久化                                   │    │
│  │                                                                              │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## 技術棧

| 技術 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.100+ | 後端框架 |
| python-jose | 3.3+ | JWT 處理 |
| slowapi | 0.1.9+ | Rate Limiting |
| redis-py | 5.0+ | Redis 客戶端 |
| Pydantic | 2.0+ | 數據驗證 |
| React | 18.2+ | 前端框架 |

## 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 全局 Auth 導致現有功能中斷 | 前端請求全部 401 | 分步驟實施：先建 middleware，逐模組啟用，保留白名單路由 (health check, docs) |
| Mock 分離導致匯入錯誤 | 後端無法啟動 | 先建 Factory Pattern，再逐個遷移 Mock，每遷一個跑一次測試 |
| Rate Limiting 影響開發體驗 | 開發環境被限速 | 環境感知：development 環境放寬限制或停用 |
| Redis 連接失敗影響 HITL | 審批功能不可用 | 健康檢查 + fallback 到 InMemory (僅限 development) |
| MCP Permission 檢查阻斷工具調用 | Agent 無法使用工具 | 漸進式啟用：先 log-only 模式，驗證後再改為 enforce 模式 |

## 成功標準

- [ ] CORS origin 正確 (3005)
- [ ] Vite proxy 正確 (8000)
- [ ] JWT Secret 從環境變量讀取，不安全值啟動時警告
- [ ] authStore 零 console.log 輸出
- [ ] Docker 無預設弱密碼
- [ ] Uvicorn reload 僅在 development 環境啟用
- [ ] Auth 覆蓋率 100% (528/528 端點)
- [ ] Sessions 使用真實 JWT 用戶提取
- [ ] Rate Limiting 生效 (可通過 429 驗證)
- [ ] 18 Mock 類全部遷移到 tests/mocks/
- [ ] LLMServiceFactory 無靜默 fallback
- [ ] InMemoryApprovalStorage 替換為 Redis
- [ ] MCP Permission Pattern 運行時啟用
- [ ] Shell/SSH MCP 有命令白名單
- [ ] ContextSynchronizer 有 asyncio.Lock
- [ ] 全局異常處理器不洩漏 error_type
- [ ] 安全評分 1/10 → 6/10
- [ ] 所有測試通過

## 安全評分提升路徑

| 指標 | Before (Phase 29) | After (Phase 31) |
|------|-------------------|-------------------|
| Auth 覆蓋率 | 7% (38/528) | 100% (528/528) |
| Rate Limiting | 無 | 全局啟用 |
| JWT Secret | 硬編碼 | 環境變量 |
| MCP Permission | 0 運行時檢查 | 28 patterns 全部啟用 |
| Mock in Production | 18 類 | 0 類 |
| InMemory Storage | 9 類 (HITL default) | 8 類 (HITL → Redis) |
| PII 洩漏 | 5 console.log | 0 |
| 預設弱密碼 | admin/admin123 | 環境變量化 |
| **安全評分** | **1/10** | **6/10** |

---

**Phase 31 開始時間**: TBD
**預估完成時間**: 3 週
**總 Story Points**: ~125 pts
