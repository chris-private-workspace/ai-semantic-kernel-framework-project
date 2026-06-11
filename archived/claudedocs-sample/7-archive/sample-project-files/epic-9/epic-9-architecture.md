# Epic 9: AI Assistant Integration - 技術架構文檔

> **狀態**: 📋 架構設計階段
> **優先級**: 🔥 高
> **關聯文檔**: [Epic 9 概覽](./epic-9-overview.md) | [Epic 9 需求](./epic-9-requirements.md)

---

## 🏗️ 系統架構概覽

### 架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js 14)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  AI Insight  │  │ AI Suggest   │  │  Risk Alert  │         │
│  │  Components  │  │  Components  │  │  Components  │         │
│  │              │  │              │  │              │         │
│  │ - Budget AI  │  │ - Expense AI │  │ - Risk Badge │         │
│  │ - Similar    │  │ - Category   │  │ - Risk Modal │         │
│  │   Cases      │  │   Suggest    │  │ - Trend Chart│         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │ tRPC (Type-safe API)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    tRPC API Layer (packages/api)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │aiSuggestion  │  │ aiAnalysis   │  │  aiReport    │         │
│  │   Router     │  │   Router     │  │   Router     │         │
│  │              │  │              │  │              │         │
│  │- getBudget   │  │- classify    │  │- generate    │         │
│  │  Suggestion  │  │  Expense     │  │  Summary     │         │
│  │- getSimilar  │  │- detectRisk  │  │- getTrends   │         │
│  │  Projects    │  │- predict     │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              AI Service Layer (packages/ai - NEW)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ BudgetAI     │  │ ExpenseAI    │  │  RiskAI      │         │
│  │ Service      │  │  Service     │  │  Service     │         │
│  │              │  │              │  │              │         │
│  │- analyze     │  │- classify    │  │- predict     │         │
│  │  Historical  │  │  Description │  │  Overspend   │         │
│  │- findSimilar │  │- detectAnom  │  │- assess      │         │
│  │- generate    │  │              │  │  Delay       │         │
│  │  Suggestion  │  │              │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ ReportAI     │  │ PromptEngine │  │  CacheManager│         │
│  │ Service      │  │              │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                   ┌─────────┴─────────┐
                   ▼                   ▼
┌──────────────────────────┐ ┌─────────────────────────┐
│   Azure OpenAI Service   │ │  Azure AI Search        │
│                          │ │  (Vector DB)            │
│ - GPT-4 Turbo            │ │                         │
│ - GPT-3.5 Turbo (dev)    │ │ - Semantic Search       │
│ - Embeddings (ada-002)   │ │ - Similar Projects      │
└──────────────────────────┘ └─────────────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │  Redis Cache    │
         │                 │
         │ - AI Results    │
         │ - Embeddings    │
         │ - Rate Limiting │
         └─────────────────┘
```

---

## 📦 新增套件: packages/ai

### 目錄結構

```
packages/ai/
├── src/
│   ├── services/
│   │   ├── budgetAI.ts          # 預算建議 AI 服務
│   │   ├── expenseAI.ts         # 費用分類 AI 服務
│   │   ├── riskAI.ts            # 風險預測 AI 服務
│   │   ├── reportAI.ts          # 報表摘要 AI 服務
│   │   └── index.ts             # 服務統一導出
│   ├── lib/
│   │   ├── openai.ts            # Azure OpenAI 客戶端
│   │   ├── aiSearch.ts          # Azure AI Search 客戶端
│   │   ├── promptEngine.ts      # Prompt 管理引擎
│   │   ├── cacheManager.ts      # 快取管理
│   │   └── utils.ts             # 工具函數
│   ├── prompts/
│   │   ├── budget-suggestion.ts # 預算建議 Prompt
│   │   ├── expense-classification.ts
│   │   ├── risk-prediction.ts
│   │   └── report-summary.ts
│   ├── types/
│   │   ├── ai.ts                # AI 相關 TypeScript 類型
│   │   └── index.ts
│   └── index.ts
├── package.json
├── tsconfig.json
└── README.md
```

### package.json 依賴

```json
{
  "name": "@acme/ai",
  "version": "0.1.0",
  "dependencies": {
    "@azure/openai": "^1.0.0-beta.12",
    "@azure/search-documents": "^12.0.0",
    "zod": "^3.22.4",
    "ioredis": "^5.3.2",
    "superjson": "^2.2.1"
  },
  "devDependencies": {
    "@types/node": "^20.11.0",
    "typescript": "^5.3.3"
  }
}
```

---

## 🔧 核心組件設計

### 1. BudgetAI Service

**職責**: 智能預算建議

**核心方法**:

```typescript
// packages/ai/src/services/budgetAI.ts
import { OpenAIClient } from '@azure/openai';
import { AzureKeyCredential } from '@azure/core-auth';
import { PromptEngine } from '../lib/promptEngine';
import { CacheManager } from '../lib/cacheManager';
import type { BudgetSuggestion, ProjectInput, SimilarProject } from '../types/ai';

export class BudgetAIService {
  private openai: OpenAIClient;
  private promptEngine: PromptEngine;
  private cache: CacheManager;

  constructor() {
    this.openai = new OpenAIClient(
      process.env.AZURE_OPENAI_ENDPOINT!,
      new AzureKeyCredential(process.env.AZURE_OPENAI_KEY!)
    );
    this.promptEngine = new PromptEngine();
    this.cache = new CacheManager();
  }

  /**
   * 生成預算建議
   * @param input - 專案輸入資訊 (名稱、類型、時程、描述)
   * @param historicalProjects - 歷史專案資料
   * @returns 預算建議 (範圍、信心度、相似案例)
   */
  async generateBudgetSuggestion(
    input: ProjectInput,
    historicalProjects: Array<{ name: string; type: string; budget: number }>
  ): Promise<BudgetSuggestion> {
    // 檢查快取
    const cacheKey = this.cache.generateKey('budget', input);
    const cached = await this.cache.get<BudgetSuggestion>(cacheKey);
    if (cached) return cached;

    // 建構 Prompt
    const prompt = this.promptEngine.buildBudgetPrompt(input, historicalProjects);

    // 呼叫 Azure OpenAI
    const response = await this.openai.getChatCompletions(
      process.env.AZURE_OPENAI_DEPLOYMENT_NAME!, // gpt-4-turbo
      [
        { role: 'system', content: 'You are a budget planning expert.' },
        { role: 'user', content: prompt }
      ],
      {
        temperature: 0.3, // 降低隨機性
        maxTokens: 500,
        responseFormat: { type: 'json_object' } // 強制 JSON 輸出
      }
    );

    const result = JSON.parse(response.choices[0]?.message?.content || '{}');

    // 驗證結果
    const suggestion: BudgetSuggestion = {
      recommended: result.recommended,
      min: result.min,
      max: result.max,
      confidence: result.confidence,
      reasoning: result.reasoning,
      similarProjects: await this.findSimilarProjects(input)
    };

    // 快取結果 (24 小時)
    await this.cache.set(cacheKey, suggestion, 86400);

    return suggestion;
  }

  /**
   * 尋找相似專案
   * @param input - 專案輸入資訊
   * @returns 最相似的 3 個專案
   */
  async findSimilarProjects(input: ProjectInput): Promise<SimilarProject[]> {
    // 使用 Azure AI Search 進行語義搜索
    const searchClient = getAISearchClient();

    // 生成 Embedding
    const embedding = await this.openai.getEmbeddings(
      'text-embedding-ada-002',
      [input.description]
    );

    // 向量搜索
    const results = await searchClient.search('*', {
      vectorQueries: [{
        vector: embedding.data[0]!.embedding,
        kNearestNeighborsCount: 3,
        fields: ['descriptionVector']
      }],
      select: ['id', 'name', 'type', 'budget', 'actualBudget']
    });

    return results.results.map(r => ({
      id: r.document.id,
      name: r.document.name,
      type: r.document.type,
      budget: r.document.actualBudget,
      similarity: r.score
    }));
  }
}
```

### 2. ExpenseAI Service

**職責**: 智能費用分類、異常偵測

**核心方法**:

```typescript
// packages/ai/src/services/expenseAI.ts
export class ExpenseAIService {
  /**
   * 分類費用
   * @param description - 費用描述
   * @param amount - 金額
   * @param vendor - 供應商 (可選)
   * @returns 建議類別、信心度、理由
   */
  async classifyExpense(
    description: string,
    amount: number,
    vendor?: string
  ): Promise<ExpenseClassification> {
    // 檢查快取 (相同描述 30 天內有效)
    const cacheKey = this.cache.generateKey('expense', { description });
    const cached = await this.cache.get<ExpenseClassification>(cacheKey);
    if (cached) return cached;

    // Few-shot learning Prompt
    const prompt = this.promptEngine.buildExpensePrompt(description, amount, vendor);

    const response = await this.openai.getChatCompletions(
      process.env.AZURE_OPENAI_DEPLOYMENT_NAME!,
      [
        { role: 'system', content: 'You are an expense categorization expert.' },
        { role: 'user', content: prompt }
      ],
      {
        temperature: 0.1, // 極低溫度確保一致性
        maxTokens: 200,
        responseFormat: { type: 'json_object' }
      }
    );

    const result = JSON.parse(response.choices[0]?.message?.content || '{}');

    const classification: ExpenseClassification = {
      category: result.category,
      confidence: result.confidence,
      reasoning: result.reasoning,
      alternatives: result.alternatives // 備選類別
    };

    await this.cache.set(cacheKey, classification, 2592000); // 30 天

    return classification;
  }

  /**
   * 偵測異常費用
   * @param expense - 費用資訊
   * @param historicalStats - 歷史統計資料
   * @returns 異常類型、嚴重程度、建議
   */
  async detectAnomaly(
    expense: { description: string; amount: number; category: string },
    historicalStats: { avgAmount: number; stdDev: number; count: number }
  ): Promise<AnomalyDetection> {
    // Z-score 計算
    const zScore = (expense.amount - historicalStats.avgAmount) / historicalStats.stdDev;

    // 異常定義: |Z-score| > 2 (超過 2 個標準差)
    const isAnomaly = Math.abs(zScore) > 2;

    if (!isAnomaly) {
      return { isAnomaly: false };
    }

    // 使用 AI 分析異常原因
    const prompt = `
Expense description: "${expense.description}"
Amount: $${expense.amount}
Category: ${expense.category}
Historical average: $${historicalStats.avgAmount}
Z-score: ${zScore.toFixed(2)}

Why is this expense anomalous? Provide possible reasons.
`;

    const response = await this.openai.getChatCompletions(
      process.env.AZURE_OPENAI_DEPLOYMENT_NAME!,
      [
        { role: 'system', content: 'You are a financial analyst.' },
        { role: 'user', content: prompt }
      ],
      { temperature: 0.5, maxTokens: 300 }
    );

    return {
      isAnomaly: true,
      severity: Math.abs(zScore) > 3 ? 'high' : 'medium',
      zScore,
      reasoning: response.choices[0]?.message?.content || '',
      recommendation: 'Review this expense with PM before approval'
    };
  }
}
```

### 3. RiskAI Service

**職責**: 預測性風險預警

**核心方法**:

```typescript
// packages/ai/src/services/riskAI.ts
export class RiskAIService {
  /**
   * 預測預算超支風險
   * @param project - 專案資訊
   * @returns 風險等級、預測金額、建議措施
   */
  async predictOverspendRisk(
    project: {
      id: string;
      totalBudget: number;
      usedBudget: number;
      progress: number; // 0-100
      remainingDays: number;
    }
  ): Promise<RiskPrediction> {
    // 快速規則引擎 (降低 AI 成本)
    const burnRate = project.usedBudget / (100 - project.progress || 1);
    const projectedTotal = burnRate * 100;
    const overagePercent = ((projectedTotal - project.totalBudget) / project.totalBudget) * 100;

    // 簡單規則
    if (overagePercent < 10) {
      return {
        riskLevel: 'low',
        predictedTotal: projectedTotal,
        confidence: 0.7,
        recommendations: []
      };
    }

    // 複雜情況使用 AI
    const prompt = this.promptEngine.buildRiskPrompt(project, {
      burnRate,
      projectedTotal,
      overagePercent
    });

    const response = await this.openai.getChatCompletions(
      process.env.AZURE_OPENAI_DEPLOYMENT_NAME!,
      [
        { role: 'system', content: 'You are a project risk analyst.' },
        { role: 'user', content: prompt }
      ],
      { temperature: 0.4, maxTokens: 400, responseFormat: { type: 'json_object' } }
    );

    const result = JSON.parse(response.choices[0]?.message?.content || '{}');

    return {
      riskLevel: overagePercent > 30 ? 'high' : overagePercent > 15 ? 'medium' : 'low',
      predictedTotal: projectedTotal,
      confidence: result.confidence,
      reasoning: result.reasoning,
      recommendations: result.recommendations
    };
  }
}
```

### 4. ReportAI Service

**職責**: 自動報表摘要生成

**核心方法**:

```typescript
// packages/ai/src/services/reportAI.ts
export class ReportAIService {
  /**
   * 生成每週報表摘要
   * @param data - 統計資料
   * @returns 自然語言摘要
   */
  async generateWeeklySummary(
    data: {
      totalProjects: number;
      projectsDelta: number;
      totalBudgetUsage: number;
      budgetUsageDelta: number;
      highRiskProjects: Array<{ name: string; reason: string }>;
      completedProjects: number;
    }
  ): Promise<ReportSummary> {
    const prompt = this.promptEngine.buildReportPrompt('weekly', data);

    const response = await this.openai.getChatCompletions(
      process.env.AZURE_OPENAI_DEPLOYMENT_NAME!,
      [
        {
          role: 'system',
          content: 'You are a professional report writer. Generate concise, actionable summaries.'
        },
        { role: 'user', content: prompt }
      ],
      {
        temperature: 0.6, // 適度創意
        maxTokens: 800
      }
    );

    const summary = response.choices[0]?.message?.content || '';

    return {
      executiveSummary: summary,
      keyMetrics: data,
      trends: await this.analyzeTrends(data),
      anomalies: data.highRiskProjects,
      recommendations: await this.generateRecommendations(data)
    };
  }
}
```

---

## 🔑 Prompt Engineering 策略

### Prompt 版本管理

```typescript
// packages/ai/src/prompts/budget-suggestion.ts
export const BUDGET_PROMPT_V1 = `
Given the following project information:
- Name: {{name}}
- Type: {{type}}
- Duration: {{duration}} months
- Description: {{description}}

Historical similar projects:
{{#each historicalProjects}}
- {{name}}: ${{budget}} ({{type}})
{{/each}}

Provide a budget suggestion in JSON format:
{
  "recommended": <number>,
  "min": <number>,
  "max": <number>,
  "confidence": <0-1>,
  "reasoning": "<explanation>"
}
`;

// 版本控制
export const BUDGET_PROMPT_VERSIONS = {
  v1: BUDGET_PROMPT_V1,
  v2: BUDGET_PROMPT_V2, // 未來版本
  current: 'v1'
};
```

### Few-shot Learning 範例

```typescript
// packages/ai/src/prompts/expense-classification.ts
export const EXPENSE_CLASSIFICATION_EXAMPLES = [
  {
    description: "購買 Office 365 年度授權",
    category: "軟體授權",
    reasoning: "明確提到軟體產品和授權類型"
  },
  {
    description: "MacBook Pro 15吋 for 開發人員",
    category: "硬體設備",
    reasoning: "硬體採購，用於開發用途"
  },
  {
    description: "外包開發團隊月費",
    category: "外包服務",
    reasoning: "人力外包服務"
  }
];
```

---

## 📊 資料流設計

### 1. 預算建議流程

```
User Input
    ↓
tRPC: aiSuggestion.getBudget
    ↓
BudgetAIService.generateBudgetSuggestion
    ↓
├─ Check Redis Cache ──→ Cache Hit? → Return
│                            ↓ Cache Miss
├─ Query Historical Projects (Prisma)
│   ↓
├─ Build Prompt (PromptEngine)
│   ↓
├─ Call Azure OpenAI API
│   ↓
├─ Parse JSON Response
│   ↓
├─ Find Similar Projects (Azure AI Search)
│   ↓
├─ Cache Result (Redis, 24h)
│   ↓
└─ Return BudgetSuggestion
```

### 2. 風險預測流程 (背景任務)

```
Cron Job (Daily 2:00 AM)
    ↓
Risk Prediction Task
    ↓
For Each Active Project:
    ├─ Fetch Project Data (Prisma)
    ├─ Quick Rule Engine Check
    │   ↓ If simple case
    │   └─→ Return risk level
    │   ↓ If complex case
    ├─ Call RiskAIService.predictOverspendRisk
    │   ↓
    ├─ Update Project Risk Status (Prisma)
    │   ↓
    └─ If High Risk:
        ├─ Create Notification
        └─ Send Email (EmailService)
```

---

## 🚀 API 設計

### tRPC Router: aiSuggestion

```typescript
// packages/api/src/routers/aiSuggestion.ts
import { z } from 'zod';
import { createTRPCRouter, protectedProcedure } from '../trpc';
import { BudgetAIService } from '@acme/ai';

export const aiSuggestionRouter = createTRPCRouter({
  /**
   * 獲取預算建議
   */
  getBudgetSuggestion: protectedProcedure
    .input(z.object({
      projectName: z.string().min(1),
      projectType: z.string().min(1),
      duration: z.number().positive(),
      description: z.string().min(10)
    }))
    .mutation(async ({ ctx, input }) => {
      const budgetAI = new BudgetAIService();

      // 查詢歷史專案
      const historicalProjects = await ctx.prisma.project.findMany({
        where: {
          type: input.projectType,
          status: 'COMPLETED'
        },
        select: {
          name: true,
          type: true,
          budgetPool: { select: { totalAmount: true } }
        },
        take: 10,
        orderBy: { createdAt: 'desc' }
      });

      // 生成建議
      const suggestion = await budgetAI.generateBudgetSuggestion(input, historicalProjects);

      // 記錄使用
      await ctx.prisma.aIUsageLog.create({
        data: {
          userId: ctx.session.user.id,
          feature: 'BUDGET_SUGGESTION',
          inputTokens: 500, // 估算
          outputTokens: 300,
          cost: 0.024 // GPT-4 Turbo
        }
      });

      return suggestion;
    }),

  /**
   * 記錄使用者採納/拒絕行為
   */
  recordFeedback: protectedProcedure
    .input(z.object({
      suggestionId: z.string(),
      action: z.enum(['ACCEPTED', 'REJECTED', 'MODIFIED']),
      originalSuggestion: z.number(),
      finalValue: z.number().optional()
    }))
    .mutation(async ({ ctx, input }) => {
      await ctx.prisma.aIFeedback.create({
        data: {
          userId: ctx.session.user.id,
          feature: 'BUDGET_SUGGESTION',
          action: input.action,
          metadata: {
            original: input.originalSuggestion,
            final: input.finalValue
          }
        }
      });

      return { success: true };
    })
});
```

---

## 💾 數據模型擴展 (Prisma Schema)

```prisma
// packages/db/prisma/schema.prisma

// AI 使用記錄 (成本追蹤)
model AIUsageLog {
  id           String   @id @default(uuid())
  userId       String
  feature      String   // BUDGET_SUGGESTION, EXPENSE_CLASSIFICATION, etc.
  inputTokens  Int
  outputTokens Int
  cost         Float    // USD
  createdAt    DateTime @default(now())

  user User @relation(fields: [userId], references: [id])

  @@index([userId, createdAt])
  @@index([feature, createdAt])
}

// AI 使用者回饋 (改進模型)
model AIFeedback {
  id        String   @id @default(uuid())
  userId    String
  feature   String
  action    String   // ACCEPTED, REJECTED, MODIFIED
  metadata  Json     // 原始建議、最終值等
  createdAt DateTime @default(now())

  user User @relation(fields: [userId], references: [id])

  @@index([feature, action])
}

// 專案風險狀態 (快取)
model ProjectRisk {
  id              String   @id @default(uuid())
  projectId       String   @unique
  riskLevel       String   // LOW, MEDIUM, HIGH
  predictedTotal  Float
  confidence      Float
  reasoning       String   @db.Text
  recommendations Json
  lastUpdated     DateTime @default(now())

  project Project @relation(fields: [projectId], references: [id])
}

// 關係更新
model User {
  // ... 現有欄位
  aiUsageLogs AIUsageLog[]
  aiFeedbacks AIFeedback[]
}

model Project {
  // ... 現有欄位
  projectRisk ProjectRisk?
}
```

---

## 🔒 安全性設計

### 1. API 金鑰管理
- **儲存**: Azure Key Vault
- **存取**: Managed Identity (無需密碼)
- **輪換**: 每 90 天自動輪換

### 2. 資料隱私
- **PII 遮罩**: 傳送給 AI 前移除個人識別資訊
- **Azure OpenAI**: 資料不外流，不用於訓練
- **Audit Log**: 記錄所有 AI API 呼叫

### 3. Rate Limiting
```typescript
// Rate limiting 實作
const RATE_LIMITS = {
  BUDGET_SUGGESTION: 10, // 每分鐘 10 次
  EXPENSE_CLASSIFICATION: 30, // 每分鐘 30 次
  RISK_PREDICTION: 5 // 每分鐘 5 次
};

// Redis-based rate limiting
async function checkRateLimit(userId: string, feature: string): Promise<boolean> {
  const key = `ratelimit:${feature}:${userId}`;
  const count = await redis.incr(key);

  if (count === 1) {
    await redis.expire(key, 60); // 1 分鐘
  }

  return count <= RATE_LIMITS[feature];
}
```

---

## 📈 監控與告警

### Azure Monitor Metrics

| 指標 | 閾值 | 告警動作 |
|------|------|---------|
| AI API 回應時間 | P95 > 5 秒 | Email + Slack |
| AI API 錯誤率 | > 5% | Email + SMS |
| 每日 AI 成本 | > $10 | Email |
| 快取命中率 | < 30% | Email |

### Application Insights

```typescript
// 自訂事件追蹤
import { TelemetryClient } from 'applicationinsights';

const appInsights = new TelemetryClient(process.env.APPLICATIONINSIGHTS_CONNECTION_STRING);

// 追蹤 AI 使用
appInsights.trackEvent({
  name: 'AI_Budget_Suggestion',
  properties: {
    userId: 'user-123',
    projectType: 'Software Development',
    adopted: true
  },
  measurements: {
    responseTime: 2.5,
    tokensUsed: 800,
    cost: 0.024
  }
});
```

---

## 🔗 相關文檔

- [Epic 9 概覽](./epic-9-overview.md)
- [Epic 9 需求](./epic-9-requirements.md)
- [Epic 9 風險分析](./epic-9-risks.md)

---

## 📝 變更歷史

| 日期 | 版本 | 變更內容 | 作者 |
|------|------|---------|------|
| 2025-11-08 | 1.0 | 初始版本 - Epic 9 技術架構 | AI Assistant |

---

**維護者**: 技術架構團隊
**最後更新**: 2025-11-08
**審核狀態**: 待審核
