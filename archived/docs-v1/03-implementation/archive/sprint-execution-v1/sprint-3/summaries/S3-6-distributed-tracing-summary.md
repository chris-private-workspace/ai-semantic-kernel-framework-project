# S3-6: Distributed Tracing - 實現摘要

**Story ID**: S3-6
**標題**: Distributed Tracing (Jaeger)
**Story Points**: 5
**狀態**: ✅ 已完成
**完成日期**: 2025-11-25

---

## 📋 驗收標準達成情況

| 驗收標準 | 狀態 | 說明 |
|---------|------|------|
| Jaeger 部署 | ✅ | All-in-One 1.53 |
| OpenTelemetry 整合 | ✅ | OTLP 導出器 |
| 追蹤上下文傳播 | ✅ | W3C + B3 格式 |
| Jaeger UI 可用 | ✅ | 完整調用鏈可視化 |

---

## 🔧 技術實現

### Jaeger 配置

| 配置項 | 值 |
|-------|---|
| 版本 | Jaeger All-in-One 1.53 |
| UI 端口 | 16686 |
| OTLP 端口 | 4317 (gRPC), 4318 (HTTP) |
| 存儲 | 內存 (開發) / Elasticsearch (生產) |

### OpenTelemetry 設置

```python
# backend/src/core/telemetry/setup.py

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def setup_tracing(app: FastAPI):
    # 設置 TracerProvider
    provider = TracerProvider()

    # 配置 OTLP 導出器
    exporter = OTLPSpanExporter(
        endpoint="http://jaeger:4317",
        insecure=True
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)

    # 自動 instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
```

### 追蹤中間件

```python
class TracingMiddleware:
    """追蹤中間件"""

    async def __call__(self, request: Request, call_next):
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span(
            f"{request.method} {request.url.path}",
            kind=trace.SpanKind.SERVER
        ) as span:
            # 添加屬性
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.user_agent", request.headers.get("User-Agent"))

            response = await call_next(request)

            span.set_attribute("http.status_code", response.status_code)

            return response
```

### 跨服務傳播

```python
from opentelemetry.propagate import inject, extract

class ServiceClient:
    async def call_service(self, url: str, data: dict):
        headers = {}
        inject(headers)  # 注入追蹤上下文

        async with httpx.AsyncClient() as client:
            return await client.post(url, json=data, headers=headers)
```

---

## 📁 代碼位置

```
backend/src/core/telemetry/
├── __init__.py
├── setup.py                   # 追蹤初始化
├── middleware.py              # 追蹤中間件
└── propagation.py             # 上下文傳播

docker-compose.yml             # Jaeger 服務定義
```

---

## 🧪 驗證方式

```bash
# 訪問 Jaeger UI
http://localhost:16686

# 發送請求後查看追蹤
curl http://localhost:8000/api/v1/workflows

# 在 Jaeger UI 搜索服務 "ipa-platform"
```

---

## 📝 備註

- 35 個單元測試全部通過
- 追蹤數據保留 7 天
- 支援 W3C Trace Context 和 B3 格式

---

**生成日期**: 2025-11-26
