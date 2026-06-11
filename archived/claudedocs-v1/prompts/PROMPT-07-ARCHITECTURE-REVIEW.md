# PROMPT-07: ARCHITECTURE REVIEW
# 架構審查與分析

> **用途**: 審查技術架構設計和決策
> **變數**: 無
> **預估時間**: 10-15 分鐘
> **版本**: v3.0.0

---

## 🎯 執行步驟

### Step 1: 讀取架構文檔

```yaml
讀取文件:
  - docs/02-architecture/technical-architecture.md
  - docs/02-architecture/technical-architecture-part2.md
  - docs/02-architecture/technical-architecture-part3.md
  - docs/02-architecture/gate-check/solutioning-gate-check.md

提取信息:
  - 架構設計決策
  - 技術選型
  - 系統組件
  - 數據流
  - 安全架構
  - 部署架構
```

### Step 2: 審查架構質量

```yaml
審查維度:
  1. 功能性 (Functionality):
     - 是否滿足所有功能需求
     - 組件職責是否清晰

  2. 可用性 (Availability):
     - 高可用性設計
     - 容錯機制
     - 災難恢復

  3. 可擴展性 (Scalability):
     - 水平擴展能力
     - 垂直擴展能力
     - 性能瓶頸分析

  4. 安全性 (Security):
     - 認證授權機制
     - 數據加密
     - 安全漏洞防護

  5. 可維護性 (Maintainability):
     - 代碼組織
     - 模塊化設計
     - 技術債務

  6. 性能 (Performance):
     - 響應時間要求
     - 吞吐量要求
     - 資源使用效率

  7. 可觀測性 (Observability):
     - 日誌記錄
     - 監控指標
     - 鏈路追踪
```

### Step 3: 對照 PRD 需求

```yaml
讀取 PRD:
  - docs/01-planning/prd/prd-main.md
  - docs/01-planning/prd/features/*.md

檢查覆蓋度:
  - 所有功能需求是否有對應架構設計
  - 非功能需求是否被滿足
  - 是否有遺漏的需求
```

### Step 4: 識別風險和改進點

```yaml
風險識別:
  - 技術風險
  - 架構風險
  - 依賴風險
  - 性能風險
  - 安全風險

改進建議:
  - 短期改進 (1-2 Sprint)
  - 中期改進 (3-6 個月)
  - 長期改進 (6+ 個月)
```

---

## 📤 輸出格式

```markdown
# 架構審查報告

**審查日期**: {REVIEW_DATE}
**審查者**: AI Assistant (PROMPT-07)
**架構版本**: {ARCHITECTURE_VERSION}

---

## 📊 審查摘要

| 維度 | 評分 | 狀態 |
|------|------|------|
| 功能性 | {SCORE}/10 | {STATUS} |
| 可用性 | {SCORE}/10 | {STATUS} |
| 可擴展性 | {SCORE}/10 | {STATUS} |
| 安全性 | {SCORE}/10 | {STATUS} |
| 可維護性 | {SCORE}/10 | {STATUS} |
| 性能 | {SCORE}/10 | {STATUS} |
| 可觀測性 | {SCORE}/10 | {STATUS} |
| **總體評分** | **{TOTAL_SCORE}/70** | **{OVERALL_STATUS}** |

---

## ✅ 架構優勢

### 優勢 1: {STRENGTH_TITLE_1}
**描述**: {DESCRIPTION}
**影響**: {IMPACT}
**建議**: {RECOMMENDATION}

### 優勢 2: {STRENGTH_TITLE_2}
...

---

## ⚠️ 潛在風險

### 風險 1: {RISK_TITLE_1}
**嚴重程度**: {SEVERITY} (Critical/High/Medium/Low)
**描述**: {RISK_DESCRIPTION}
**影響**: {IMPACT}
**緩解措施**: {MITIGATION}
**優先級**: {PRIORITY}

### 風險 2: {RISK_TITLE_2}
...

---

## 🔍 詳細審查

### 1. 功能性審查

**評分**: {SCORE}/10

**優點**:
- ✅ {STRENGTH_1}
- ✅ {STRENGTH_2}

**問題**:
- ⚠️ {ISSUE_1}
- ⚠️ {ISSUE_2}

**建議**:
- {RECOMMENDATION_1}
- {RECOMMENDATION_2}

---

### 2. 可用性審查

**評分**: {SCORE}/10

**高可用設計**:
- {HA_DESIGN_1}
- {HA_DESIGN_2}

**容錯機制**:
- {FAULT_TOLERANCE_1}

**改進建議**:
- {IMPROVEMENT_1}

---

### 3. 可擴展性審查

**評分**: {SCORE}/10

**水平擴展**:
- 支持: {HORIZONTAL_SCALING_SUPPORT}
- 限制: {LIMITATIONS}

**性能瓶頸**:
- {BOTTLENECK_1}
- {BOTTLENECK_2}

**擴展策略**:
- {SCALING_STRATEGY}

---

### 4. 安全性審查

**評分**: {SCORE}/10

**認證授權**:
- 機制: {AUTH_MECHANISM}
- 評估: {ASSESSMENT}

**數據保護**:
- 加密: {ENCRYPTION}
- 評估: {ASSESSMENT}

**安全漏洞檢查**:
- ✅ {SECURITY_CHECK_1}
- ⚠️ {SECURITY_ISSUE_1}

---

### 5. 可維護性審查

**評分**: {SCORE}/10

**代碼組織**:
- {CODE_ORGANIZATION_ASSESSMENT}

**模塊化**:
- {MODULARITY_ASSESSMENT}

**技術債務**:
- {TECHNICAL_DEBT_ASSESSMENT}

---

### 6. 性能審查

**評分**: {SCORE}/10

**性能目標**:
- 響應時間: {RESPONSE_TIME_TARGET}
- 吞吐量: {THROUGHPUT_TARGET}

**性能優化**:
- {OPTIMIZATION_1}
- {OPTIMIZATION_2}

**性能風險**:
- {PERFORMANCE_RISK_1}

---

### 7. 可觀測性審查

**評分**: {SCORE}/10

**日誌記錄**:
- 方案: {LOGGING_SOLUTION}
- 評估: {ASSESSMENT}

**監控指標**:
- 工具: {MONITORING_TOOLS}
- 覆蓋度: {COVERAGE}

**鏈路追踪**:
- 實現: {TRACING_IMPLEMENTATION}

---

## 📋 PRD 需求覆蓋度

### 功能需求覆蓋

| 功能 | PRD 章節 | 架構支持 | 覆蓋度 |
|------|---------|---------|--------|
| {FEATURE_1} | {PRD_SECTION} | {ARCHITECTURE_SUPPORT} | {COVERAGE}% |
| {FEATURE_2} | {PRD_SECTION} | {ARCHITECTURE_SUPPORT} | {COVERAGE}% |

**總體覆蓋度**: {OVERALL_COVERAGE}%

### 非功能需求覆蓋

- ✅ {NFR_1}
- ✅ {NFR_2}
- ⚠️ {NFR_3_PARTIAL}
- ❌ {NFR_4_MISSING}

---

## 💡 改進建議

### 短期改進 (1-2 Sprint)

**優先級 P0**:
1. {SHORT_TERM_IMPROVEMENT_1}
   - 目標: {GOAL}
   - 預估工作量: {EFFORT}

**優先級 P1**:
2. {SHORT_TERM_IMPROVEMENT_2}

---

### 中期改進 (3-6 個月)

1. {MID_TERM_IMPROVEMENT_1}
2. {MID_TERM_IMPROVEMENT_2}

---

### 長期改進 (6+ 個月)

1. {LONG_TERM_IMPROVEMENT_1}
2. {LONG_TERM_IMPROVEMENT_2}

---

## 🎯 行動計劃

### 立即行動 (本 Sprint)
- [ ] {ACTION_ITEM_1}
- [ ] {ACTION_ITEM_2}

### 規劃行動 (下個 Sprint)
- [ ] {ACTION_ITEM_3}
- [ ] {ACTION_ITEM_4}

### 持續改進
- [ ] {CONTINUOUS_IMPROVEMENT_1}
- [ ] {CONTINUOUS_IMPROVEMENT_2}

---

## 📚 參考文檔

- [技術架構](../../docs/02-architecture/technical-architecture.md)
- [PRD 文檔](../../docs/01-planning/prd/prd-main.md)
- [Gate Check](../../docs/02-architecture/gate-check/solutioning-gate-check.md)

---

**生成工具**: PROMPT-07
**版本**: v2.0.0
**下次審查**: {NEXT_REVIEW_DATE}
```

---

## 💡 使用範例

```bash
# 執行架構審查
用戶: "@PROMPT-07-ARCHITECTURE-REVIEW.md"

AI 執行:
1. 讀取所有架構文檔
2. 對 7 個維度進行評分
3. 對照 PRD 檢查需求覆蓋度
4. 識別風險和改進點
5. 生成詳細審查報告

輸出:
---
🏗️ 架構審查完成

總體評分: 58/70 (82.9%)

優勢:
- ✅ Agent Framework 原生支持多 Agent
- ✅ Azure App Service 簡化部署
- ✅ 混合監控方案平衡成本

風險:
- ⚠️ Redis 單點故障風險 (Medium)
- ⚠️ Service Bus 成本可能較高 (Low)
- ⚠️ Agent Framework Preview 穩定性 (High)

建議:
1. 短期: 添加 Redis Sentinel
2. 中期: 評估 Service Bus 替代方案
3. 長期: 準備 Agent Framework GA 升級

報告已保存
---
```

---

## 🔗 相關文檔

- [AI Assistant Instructions](../AI-ASSISTANT-INSTRUCTIONS.md)
- [Technical Architecture](../../docs/02-architecture/technical-architecture.md)
- [PRD](../../docs/01-planning/prd/prd-main.md)

---

**版本**: v3.0.0
**更新日期**: 2025-12-01
