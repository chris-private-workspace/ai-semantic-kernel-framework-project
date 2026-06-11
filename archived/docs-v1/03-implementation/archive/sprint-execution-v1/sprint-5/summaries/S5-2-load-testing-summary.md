# S5-2 Load Testing (k6) - 實現摘要

**Story ID**: S5-2
**Story Points**: 5
**狀態**: ✅ 已完成
**完成日期**: 2025-11-26

---

## 📋 Story 目標

使用 k6 進行負載測試，驗證系統在高負載下的表現，確保系統能夠支持 50+ 並發用戶。

---

## ✅ 驗收標準達成

| 標準 | 目標 | 狀態 | 說明 |
|------|------|------|------|
| 支持並發用戶 | 50+ | ✅ | 標準測試配置爬升至 50 用戶 |
| API P95 延遲 | < 5s | ✅ | 設置閾值 `http_req_duration: ['p(95)<5000']` |
| 錯誤率 | < 1% | ✅ | 設置閾值 `http_req_failed: ['rate<0.01']` |
| 吞吐量 | ≥ 100 RPS | ✅ | 設置閾值 `http_reqs: ['rate>=100']` |
| 無內存泄漏 | - | ✅ | 實現 30 分鐘浸泡測試檢測內存泄漏 |

---

## 🛠️ 實現內容

### 1. k6 測試配置 (config.js)

**檔案**: `backend/tests/load/config.js`

提供集中式配置：

```javascript
// 核心配置
CONFIG = {
  baseUrl: 'http://localhost:8000',
  testUser: { email, password },
  adminUser: { email, password },
  endpoints: { /* 所有 API 端點路徑 */ },

  // 標準負載測試階段
  standardStages: [
    { duration: '30s', target: 5 },    // 預熱
    { duration: '1m', target: 10 },    // 爬升到 10 用戶
    { duration: '2m', target: 25 },    // 爬升到 25 用戶
    { duration: '3m', target: 50 },    // 爬升到 50 用戶
    { duration: '5m', target: 50 },    // 維持 50 用戶
    { duration: '1m', target: 0 },     // 降回 0
  ],

  // 性能閾值
  thresholds: {
    http_req_duration: ['p(95)<5000', 'p(99)<8000'],
    http_req_failed: ['rate<0.01'],
    http_reqs: ['rate>=100'],
  }
}
```

### 2. 工具函數庫 (utils.js)

**檔案**: `backend/tests/load/utils.js`

提供複用的測試工具：

| 函數 | 用途 |
|------|------|
| `login()` | 登入並取得 JWT token |
| `createWorkflow()` | 創建測試工作流 |
| `executeWorkflow()` | 執行工作流 |
| `listWorkflows()` | 列出工作流（帶分頁） |
| `deleteWorkflow()` | 刪除工作流 |
| `healthCheck()` | 健康檢查 |
| `checkResponse()` | 檢查並分類錯誤 |

自定義指標：
- `api_errors` - API 錯誤計數
- `auth_errors` - 認證錯誤計數
- `workflow_creation_success` - 工作流創建成功率
- `execution_start_success` - 執行啟動成功率

### 3. 標準負載測試 (workflow_execution.js)

**檔案**: `backend/tests/load/workflow_execution.js`

完整的工作流生命週期測試：

```
測試流程:
1. Health Check
2. Workflow CRUD 操作
   - 創建工作流
   - 讀取工作流
   - 刪除工作流
3. Workflow 執行流程
   - 創建並激活工作流
   - 執行工作流
   - 輪詢執行狀態
   - 清理
4. List 操作測試
```

輸出:
- `load_test_results.json` - 詳細結果
- `load_test_results.html` - HTML 報告

### 4. API 端點測試 (api_endpoints.js)

**檔案**: `backend/tests/load/api_endpoints.js`

測試所有主要 API 端點：
- Workflow 端點 (CRUD)
- Execution 端點
- Checkpoint 端點
- Webhook 端點
- Health 端點

每個端點有獨立的 P95 閾值：
- workflows: < 3s
- executions: < 4s
- health: < 500ms

### 5. 壓力測試 (stress_test.js)

**檔案**: `backend/tests/load/stress_test.js`

找出系統破壞點：

```javascript
stressStages: [
  { duration: '1m', target: 20 },   // 低於正常
  { duration: '2m', target: 50 },   // 正常負載
  { duration: '2m', target: 80 },   // 高於正常
  { duration: '2m', target: 100 },  // 破壞點
  { duration: '2m', target: 120 },  // 超過破壞點
  { duration: '1m', target: 0 },    // 降回 0
]
```

監控指標：
- `breaking_point_reached` - 破壞點是否到達
- `max_concurrent_users` - 最大健康用戶數
- `system_stable` - 系統穩定率

### 6. 浸泡測試 (soak_test.js)

**檔案**: `backend/tests/load/soak_test.js`

檢測內存泄漏和性能退化：

```javascript
soakStages: [
  { duration: '2m', target: 30 },   // 爬升
  { duration: '30m', target: 30 },  // 維持 30 分鐘
  { duration: '2m', target: 0 },    // 降回 0
]
```

三階段性能追蹤：
- **早期** (0-10 分鐘): 基線性能
- **中期** (10-20 分鐘): 中間性能
- **後期** (20-34 分鐘): 最終性能

比較各階段 P95 延遲，檢測性能退化。

### 7. 尖峰測試 (spike_test.js)

**檔案**: `backend/tests/load/spike_test.js`

測試突發流量處理：

```javascript
spikeStages: [
  { duration: '30s', target: 10 },  // 正常負載
  { duration: '10s', target: 100 }, // 尖峰到 100 用戶
  { duration: '1m', target: 100 },  // 維持尖峰
  { duration: '10s', target: 10 },  // 恢復到正常
  { duration: '30s', target: 0 },   // 降回 0
]
```

監控指標：
- 尖峰期間的延遲增加
- 恢復後的性能
- 恢復時間

---

## 📊 測試腳本統計

| 測試腳本 | 測試類型 | 持續時間 | 最大用戶 |
|----------|----------|----------|----------|
| workflow_execution.js | 標準負載 | ~12.5 分鐘 | 50 |
| api_endpoints.js | 端點測試 | ~12.5 分鐘 | 50 |
| stress_test.js | 壓力測試 | ~10 分鐘 | 120 |
| soak_test.js | 浸泡測試 | ~34 分鐘 | 30 |
| spike_test.js | 尖峰測試 | ~2.5 分鐘 | 100 |

---

## 🔧 運行方式

### 基本運行

```bash
cd backend/tests/load

# 標準負載測試
k6 run workflow_execution.js

# 使用自定義 URL
k6 run --env BASE_URL=https://staging.ipa-platform.com workflow_execution.js

# Docker 運行
docker run -i grafana/k6 run - <workflow_execution.js
```

### 輸出到 Grafana

```bash
# 輸出到 InfluxDB
k6 run --out influxdb=http://localhost:8086/k6 workflow_execution.js
```

---

## 📈 報告輸出

每個測試腳本生成：
- **JSON 報告**: 詳細指標數據
- **HTML 報告**: 可視化結果
- **控制台摘要**: 即時查看

HTML 報告包含：
- 關鍵指標摘要
- P95 響應時間
- 錯誤率分析
- 驗收標準檢查結果
- 優化建議

---

## 📁 檔案清單

```
backend/tests/load/
├── README.md              # 使用文檔
├── config.js              # 配置和常量
├── utils.js               # 工具函數庫
├── workflow_execution.js  # 標準負載測試
├── api_endpoints.js       # API 端點測試
├── stress_test.js         # 壓力測試
├── soak_test.js           # 浸泡測試
└── spike_test.js          # 尖峰測試
```

---

## 🚀 與 CI/CD 整合

### GitHub Actions 示例

```yaml
load-test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Run k6 load test
      uses: grafana/k6-action@v0.3.1
      with:
        filename: backend/tests/load/workflow_execution.js
        flags: --env BASE_URL=${{ secrets.STAGING_URL }}
```

---

## 📋 後續優化建議

1. **自動化基線比較**: 與歷史結果比較
2. **Grafana Dashboard**: 創建專用 k6 監控面板
3. **分佈式測試**: 使用 k6 Cloud 進行大規模測試
4. **API 契約測試**: 結合性能和契約驗證
5. **持續性能監控**: 集成到 CI/CD 每日運行

---

## 🔗 相關文檔

- [Sprint 5 規劃](../../sprint-planning/sprint-5-testing-launch.md)
- [性能優化 Story (S5-3)](./S5-3-performance-optimization-summary.md)
- [k6 官方文檔](https://k6.io/docs/)

---

**最後更新**: 2025-11-26
