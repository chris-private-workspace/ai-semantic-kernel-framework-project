# Sprint 96 技術決策

## Decision 96-1: RiskAssessor 架構設計

### 決策

採用策略模式 (Strategy Pattern) 實現風險評估器：
- RiskAssessor 作為主評估器
- RiskPolicies 作為策略集合
- RiskPolicy 作為單一策略

### 理由

1. **解耦**: 策略與評估邏輯分離
2. **可擴展**: 可輕易新增或修改策略
3. **可測試**: 策略可獨立測試
4. **符合 SOLID**: 開放封閉原則

### 替代方案

- 硬編碼映射表: 簡單但不靈活
- 配置文件: 需要額外解析邏輯

---

## Decision 96-2: 風險等級體系

### 決策

使用四級風險等級：

| 等級 | 含義 | 行為 |
|------|------|------|
| LOW | 低風險 | 自動執行 |
| MEDIUM | 中風險 | 記錄審計 |
| HIGH | 高風險 | 需要審批 |
| CRITICAL | 緊急風險 | 多重審批 |

### 理由

1. 與 ITIL 風險框架對齊
2. 直觀易懂
3. 與現有 RiskLevel enum 一致

---

## Decision 96-3: 上下文風險調整

### 決策

支援以下上下文因素調整風險等級：

1. **環境因素**:
   - `is_production`: 生產環境 → 風險提升一級
   - `is_staging`: 測試環境 → 不調整

2. **時間因素**:
   - `is_weekend`: 週末 → 風險提升一級
   - `is_business_hours`: 業務時間外 → 不調整

3. **緊急程度**:
   - `is_urgent`: 緊急 → 風險提升一級

### 理由

1. 生產環境變更風險本質上更高
2. 週末人員較少，問題處理能力降低
3. 符合企業 IT 風險管理實踐

---

## Decision 96-4: API 端點設計

### 決策

```
POST /api/v1/orchestration/intent/classify
POST /api/v1/orchestration/intent/test
```

### 理由

1. RESTful 設計原則
2. 與現有 API 結構一致
3. 分離正式和測試端點

---

## Decision 96-5: RiskAssessment 數據結構

### 決策

```python
@dataclass
class RiskAssessment:
    level: RiskLevel
    score: float              # 0.0 - 1.0
    requires_approval: bool
    approval_type: str        # "single" | "multi" | "none"
    factors: List[RiskFactor]
    reasoning: str
```

### 理由

1. 完整的風險評估信息
2. 支援審計追蹤
3. 可解釋性 (reasoning 欄位)

---

**決策日期**: 2026-01-15
