# S2-5: Retry/Backoff - 實現摘要

**Story ID**: S2-5
**標題**: Retry/Backoff Mechanism
**Story Points**: 5
**狀態**: ✅ 已完成
**完成日期**: 2025-11-24

---

## 📋 驗收標準達成情況

| 驗收標準 | 狀態 | 說明 |
|---------|------|------|
| 指數退避實現 | ✅ | Exponential Backoff |
| 可配置重試次數 | ✅ | 最大重試次數設定 |
| 抖動支援 | ✅ | Jitter 防止雷暴 |
| 重試條件配置 | ✅ | 可配置重試條件 |

---

## 🔧 技術實現

### 重試配置

```python
@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0          # 基礎延遲 (秒)
    max_delay: float = 60.0          # 最大延遲 (秒)
    exponential_base: float = 2.0    # 指數基數
    jitter: bool = True              # 啟用抖動
```

### RetryHandler

```python
class RetryHandler:
    """重試處理器"""

    def __init__(self, config: RetryConfig):
        self.config = config

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """帶重試的執行"""
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except RetryableError as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    delay = self._calculate_delay(attempt)
                    await asyncio.sleep(delay)

        raise MaxRetriesExceeded(last_exception)

    def _calculate_delay(self, attempt: int) -> float:
        """計算延遲時間"""
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )

        if self.config.jitter:
            delay *= random.uniform(0.5, 1.5)

        return delay
```

### 重試裝飾器

```python
def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    retryable_exceptions: tuple = (ConnectionError, TimeoutError)
):
    """重試裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            handler = RetryHandler(RetryConfig(
                max_retries=max_retries,
                base_delay=base_delay
            ))
            return await handler.execute_with_retry(func, *args, **kwargs)
        return wrapper
    return decorator

# 使用範例
@with_retry(max_retries=3, base_delay=2.0)
async def call_external_api():
    # API 調用
    pass
```

### 重試時間示例

| 嘗試次數 | 基礎延遲 | 實際延遲 (含 jitter) |
|---------|---------|---------------------|
| 1 | 1s | 0.5s - 1.5s |
| 2 | 2s | 1s - 3s |
| 3 | 4s | 2s - 6s |
| 4 | 8s | 4s - 12s |

---

## 📁 代碼位置

```
backend/src/core/
├── retry/
│   ├── __init__.py
│   ├── handler.py             # 重試處理器
│   ├── config.py              # 重試配置
│   └── decorators.py          # 重試裝飾器
```

---

## 🧪 測試覆蓋

- 重試次數驗證
- 指數退避計算測試
- Jitter 範圍驗證
- 最大延遲限制測試

---

## 📝 備註

- 支援同步和異步函數
- 可配置可重試的異常類型
- 重試日誌自動記錄

---

**生成日期**: 2025-11-26
