# Epic 4: 映射規則管理與自動學習

> **建立日期**: 2025-12-18
> **完成日期**: 2025-12-19
> **狀態**: ✅ 已完成
> **優先級**: High

---

## 1. Epic 目標

### 主要目標
建立映射規則管理系統，支援通用規則和 Forwarder 特定規則的維護，並實現基於用戶修正的自動學習機制。

### 業務價值
- 提供規則管理界面
- 支援規則版本控制
- 自動學習提升準確率
- 減少人工維護成本

### 成功定義
- 完成規則 CRUD 操作
- 實現三層規則優先級
- 建立自動學習管道
- 提供規則效果分析

---

## 2. Epic 範圍

### 包含功能（In Scope）

| Story | 名稱 | 描述 | 狀態 |
|-------|------|------|------|
| 4-1 | 通用規則管理 | Universal 映射規則 CRUD | ✅ |
| 4-2 | Forwarder 規則管理 | 特定 Forwarder 覆蓋規則 | ✅ |
| 4-3 | 規則優先級系統 | 三層規則匹配邏輯 | ✅ |
| 4-4 | 自動學習引擎 | 從修正中學習新規則 | ✅ |
| 4-5 | 規則效果分析 | 命中率與準確度統計 | ✅ |

### 排除功能（Out of Scope）
- 規則匯入匯出（未規劃）
- 規則衝突自動解決

### 依賴項
- Epic 3 審核修正系統
- PostgreSQL 資料庫

---

## 3. 技術架構概覽

### 規則資料模型

```prisma
model MappingRule {
  id            String   @id @default(cuid())
  tier          RuleTier // UNIVERSAL, FORWARDER, LLM
  forwarderId   String?
  sourceTerm    String
  targetCategory String
  confidence    Float
  isActive      Boolean
  createdAt     DateTime
  updatedAt     DateTime
}
```

### 學習管道

```
[用戶修正] → [修正記錄] → [模式分析] → [規則建議] → [人工確認] → [規則生效]
```

---

## 4. 成功指標

| 指標 | 目標 | 實際 |
|------|------|------|
| 規則覆蓋率 | ≥ 85% | ✅ 達成 |
| 自動學習準確率 | ≥ 90% | ✅ 達成 |
| 規則維護效率 | 提升 50% | ✅ 達成 |

---

## 5. 相關文檔

- PRD: `docs/01-planning/prd/prd.md`
- 架構設計: `docs/02-architecture/architecture.md`

---

**維護者**: Development Team
**最後更新**: 2025-12-26
