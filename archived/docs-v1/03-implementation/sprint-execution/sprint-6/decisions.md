# Sprint 6: 打磨 & 發布 - Decisions Log

記錄 Sprint 6 期間做出的技術和設計決策。

---

## Decision Log

### DEC-S6-001: E2E 測試框架選擇

**日期**: 2025-11-30
**決策**: 使用 pytest + httpx 進行後端 E2E 測試，Playwright 進行前端 E2E 測試

**原因**:
- pytest 已經是專案測試標準
- httpx 提供 async 支持，適合 FastAPI
- Playwright 提供跨瀏覽器測試能力

**影響**: 測試框架一致性，CI 整合更容易

---

### DEC-S6-002: 負載測試工具選擇

**日期**: 2025-11-30
**決策**: 使用 Locust 進行負載測試

**原因**:
- Python 原生，團隊熟悉
- 支持分佈式負載生成
- 提供 Web UI 即時監控

**影響**: 性能測試可重複執行

---

### DEC-S6-003: 生產部署策略

**日期**: 2025-11-30
**決策**: 使用 Azure App Service 藍綠部署 (deployment slots)

**原因**:
- 零停機部署
- 快速回滾能力
- Azure 原生支持

**影響**: 部署流程更安全

---
