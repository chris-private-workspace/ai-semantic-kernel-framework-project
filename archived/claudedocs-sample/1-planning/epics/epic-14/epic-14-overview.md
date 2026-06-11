# Epic 14: Company + DocumentFormat Prompt 配置

**Status:** 🚧 規劃中

---

## Epic 概覽

### 目標

為不同的 Company（供應商公司）和 DocumentFormat（文件格式）配置專屬的 GPT Prompt，實現更精準的文件識別和術語分類。

### 問題陳述

目前 GPT Vision 使用統一的 Prompt 進行：
- 文件發行者識別 (Story 0-8)
- 術語分類 (Story 0-10)
- Prompt 優化 (Story 0-11)

但不同供應商的發票格式差異很大：
- **DHL**: 使用特定術語如 "AWB", "Fuel Surcharge"
- **FedEx**: 使用 "Tracking Number", "Fuel Adjustment"
- **其他**: 各有專屬的術語和格式

統一 Prompt 無法針對特定供應商優化，導致：
1. 術語分類準確率受限
2. 無法處理供應商特有的欄位
3. 難以調整不同格式的提取策略

### 解決方案

建立 Prompt 配置系統：
1. **全局 Prompt**: 基礎模板，適用於所有文件
2. **Company Prompt**: 針對特定供應商的覆蓋配置
3. **Format Prompt**: 針對特定文件格式的覆蓋配置
4. **優先級解析**: Format > Company > Global

### 架構設計

```
┌─────────────────────────────────────────────────────────────────┐
│                      Prompt 配置系統                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Global Prompt (基礎模板)                                  │   │
│  │ - 通用識別指令                                            │   │
│  │ - 標準輸出格式                                            │   │
│  │ - 基本術語分類規則                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓ 覆蓋                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Company Prompt (供應商專屬)                               │   │
│  │ - DHL: "識別 AWB, Fuel Surcharge 等術語"                 │   │
│  │ - FedEx: "識別 Tracking Number, Fuel Adjustment"         │   │
│  │ - Maersk: "識別 B/L, Demurrage, Container Fee"           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓ 覆蓋                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Format Prompt (格式專屬)                                  │   │
│  │ - "DHL Express Invoice": 特殊欄位位置                    │   │
│  │ - "DHL Freight Invoice": 不同的術語結構                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Prompt 解析順序:
1. 載入 Global Prompt
2. 如果有 Company Prompt → 合併/覆蓋
3. 如果有 Format Prompt → 合併/覆蓋
4. 返回最終 Prompt
```

### Prompt 類型

| 類型 | 用途 | 配置層級 |
|------|------|----------|
| `ISSUER_IDENTIFICATION` | 文件發行者識別 | Global / Company |
| `TERM_CLASSIFICATION` | 術語分類 | Global / Company / Format |
| `FIELD_EXTRACTION` | 欄位提取增強 | Global / Company / Format |
| `VALIDATION` | 結果驗證 | Global / Company |

### 與 Epic 13 的關係

- **Epic 13**: 欄位映射配置（Azure DI 欄位 → 系統欄位）
- **Epic 14**: Prompt 配置（GPT Vision 提取策略）

兩者互補：
1. Epic 14 的 Prompt 指導 GPT 如何識別和分類
2. Epic 13 的映射將提取結果轉換為系統格式

---

## Stories 列表

| Story ID | 標題 | 估點 | 狀態 |
|----------|------|------|------|
| 14-1 | Prompt 配置模型與 API | 5 | backlog |
| 14-2 | Prompt 配置管理介面 | 5 | backlog |
| 14-3 | Prompt 解析與合併服務 | 5 | backlog |
| 14-4 | GPT Vision 服務整合 | 5 | backlog |

**總估點**: 20 點

---

## Story 摘要

### Story 14-1: Prompt 配置模型與 API

建立 Prompt 配置的資料模型和 CRUD API。

**關鍵產出**:
- `PromptConfig` Prisma 模型
- CRUD REST API (`/api/v1/prompt-configs`)
- 配置驗證服務

### Story 14-2: Prompt 配置管理介面

建立 Prompt 配置的管理後台介面。

**關鍵產出**:
- Prompt 配置列表頁面
- Prompt 編輯器（支援變數、預覽）
- 測試功能（即時測試 Prompt 效果）

### Story 14-3: Prompt 解析與合併服務

實現 Prompt 配置的優先級解析和合併邏輯。

**關鍵產出**:
- `PromptResolver` 服務
- 變數替換引擎
- 合併策略（覆蓋 / 附加 / 自訂）

### Story 14-4: GPT Vision 服務整合

將 Prompt 配置系統整合到現有的 GPT Vision 服務中。

**關鍵產出**:
- 修改 `gpt-vision.service.ts` 使用動態 Prompt
- 修改 `ai-term-validation.service.ts` 使用動態 Prompt
- 功能開關和向後兼容

---

## 技術設計

### Prisma Schema

```prisma
model PromptConfig {
  id               String       @id @default(cuid())
  name             String
  description      String?      @db.Text
  promptType       PromptType

  // 適用範圍
  companyId        String?      @map("company_id")
  company          Company?     @relation(fields: [companyId], references: [id])

  documentFormatId String?      @map("document_format_id")
  documentFormat   DocumentFormat? @relation(fields: [documentFormatId], references: [id])

  // Prompt 內容
  systemPrompt     String?      @db.Text @map("system_prompt")
  userPromptTemplate String     @db.Text @map("user_prompt_template")

  // 合併策略
  mergeStrategy    MergeStrategy @default(OVERRIDE)

  // 變數定義
  variables        Json?        // PromptVariable[]

  // 狀態
  isActive         Boolean      @default(true) @map("is_active")
  priority         Int          @default(0)

  // 審計
  createdAt        DateTime     @default(now()) @map("created_at")
  updatedAt        DateTime     @updatedAt @map("updated_at")
  createdById      String       @map("created_by_id")
  createdBy        User         @relation(fields: [createdById], references: [id])

  @@unique([promptType, companyId, documentFormatId])
  @@index([promptType])
  @@index([companyId])
  @@index([documentFormatId])
  @@map("prompt_configs")
}

enum PromptType {
  ISSUER_IDENTIFICATION
  TERM_CLASSIFICATION
  FIELD_EXTRACTION
  VALIDATION
}

enum MergeStrategy {
  OVERRIDE    // 完全覆蓋
  APPEND      // 附加到基礎 Prompt
  PREPEND     // 添加到基礎 Prompt 前面
}
```

### Prompt 變數系統

```typescript
interface PromptVariable {
  name: string;           // 變數名稱，如 "companyName"
  type: 'static' | 'dynamic' | 'context';
  defaultValue?: string;
  description?: string;
}

// 使用方式
const template = `
識別以下發票的發行公司。
已知公司: {{companyName}}
已知術語: {{knownTerms}}
`;

// 解析後
const resolved = `
識別以下發票的發行公司。
已知公司: DHL Express
已知術語: AWB, Fuel Surcharge, Weight Charge
`;
```

### 解析服務

```typescript
interface ResolvedPrompt {
  systemPrompt: string;
  userPrompt: string;
  source: 'global' | 'company' | 'format';
  configId: string;
}

async function resolvePrompt(
  promptType: PromptType,
  context: {
    companyId?: string;
    documentFormatId?: string;
    variables?: Record<string, string>;
  }
): Promise<ResolvedPrompt>;
```

---

## 依賴關係

### 上游依賴
- **Story 0-8**: 文件發行者識別（提供 companyId）
- **Story 0-9**: 文件格式識別（提供 documentFormatId）

### 下游依賴
- **Epic 15**: 統一 3 層機制（使用此 Prompt 配置）

---

## 成功指標

| 指標 | 目標 |
|------|------|
| 術語分類準確率 | 從 85% 提升至 92% |
| 供應商專屬術語識別率 | 95%+ |
| Prompt 配置管理響應時間 | < 200ms |

---

## 風險與緩解

| 風險 | 影響 | 緩解策略 |
|------|------|----------|
| Prompt 過長導致 Token 超限 | GPT 調用失敗 | 設定 Prompt 長度限制和警告 |
| 合併邏輯複雜導致 bug | 結果不可預測 | 完善的測試和預覽功能 |
| 效能影響 | 處理延遲增加 | 配置緩存策略 |

---

*Epic created: 2026-01-02*
*Last updated: 2026-01-02*
