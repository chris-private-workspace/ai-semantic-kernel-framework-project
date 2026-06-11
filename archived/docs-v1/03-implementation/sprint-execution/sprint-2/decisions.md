# Sprint 2 Decisions

## Decision #1: 連接器抽象層設計

- **日期**: 2025-11-30
- **背景**: 需要支持多個外部系統 (ServiceNow, Dynamics 365, SharePoint)，需要統一的抽象層
- **選項**:
  1. 每個連接器獨立實現 - 快速但難以維護
  2. 抽象基類 + 具體實現 - 統一接口，易於擴展
  3. 插件架構 - 最靈活但複雜度高
- **決定**: 選項 2 - 抽象基類模式
- **原因**:
  - MVP 階段需要平衡開發速度和可維護性
  - BaseConnector 提供統一的 connect/disconnect/execute/health_check 接口
  - ConnectorRegistry 管理連接器生命週期
- **影響**: 未來新增連接器只需繼承 BaseConnector 並實現具體操作

---

## Decision #2: 緩存鍵生成策略

- **日期**: 2025-11-30
- **背景**: LLM 緩存需要唯一且一致的鍵來識別相同的請求
- **選項**:
  1. 簡單字串拼接 - 快速但可能碰撞
  2. SHA256 雜湊 - 安全且分佈均勻
  3. UUID - 唯一但無法重現
- **決定**: 選項 2 - SHA256 雜湊
- **原因**:
  - 相同輸入產生相同雜湊，支持緩存命中
  - 雜湊長度固定，Redis 鍵長度可控
  - 支持長文本 prompt（截斷至 MAX_PROMPT_LENGTH 後雜湊）
- **影響**: 緩存鍵格式為 `llm_cache:{model}:{hash}`

---

## Decision #3: CachedAgentService 包裝器模式

- **日期**: 2025-11-30
- **背景**: 需要在現有 AgentService 上添加緩存功能
- **選項**:
  1. 直接修改 AgentService - 侵入性修改
  2. 裝飾器模式 - 透明包裝
  3. 包裝器服務 - 獨立服務組合
- **決定**: 選項 3 - 包裝器服務 (CachedAgentService)
- **原因**:
  - 不修改原始 AgentService 代碼
  - 支持繞過緩存選項 (bypass_cache)
  - 易於測試和配置
- **影響**: 可選擇使用 AgentService 或 CachedAgentService

---

## Decision #4: 連接器認證策略

- **日期**: 2025-11-30
- **背景**: 不同外部系統使用不同認證方式
- **選項**:
  1. 統一 OAuth2 - 不適用所有系統
  2. 認證類型枚舉 + 策略 - 靈活但需維護
  3. 每個連接器自行處理 - 重複代碼
- **決定**: 選項 2 - AuthType 枚舉 + 認證策略
- **原因**:
  - ServiceNow: Basic Auth
  - Dynamics 365: OAuth2 (Azure AD)
  - SharePoint: OAuth2 (Graph API)
  - 統一 AuthType 枚舉支持未來擴展
- **影響**: ConnectorConfig 包含 auth_type 和 credentials 配置

---

## Decision #5: API 路由分組

- **日期**: 2025-11-30
- **背景**: 新增緩存和連接器 API 需要整合到現有路由結構
- **選項**:
  1. 平面路由 - 所有端點在根級別
  2. 功能分組 - 按功能模組分組
- **決定**: 選項 2 - 功能分組
- **原因**:
  - 現有結構已按模組分組 (agents, workflows, executions, checkpoints)
  - 新增 `/cache` 和 `/connectors` 路由前綴
  - 符合 RESTful 設計原則
- **影響**: API 結構清晰，易於文檔化
