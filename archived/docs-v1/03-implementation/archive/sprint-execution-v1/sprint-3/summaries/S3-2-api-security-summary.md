# S3-2: API Security Hardening - 實現摘要

**Story ID**: S3-2
**標題**: API Security Hardening
**Story Points**: 5
**狀態**: ✅ 已完成
**完成日期**: 2025-11-25

---

## 📋 驗收標準達成情況

| 驗收標準 | 狀態 | 說明 |
|---------|------|------|
| 輸入驗證 | ✅ | Pydantic 驗證 |
| SQL 注入防護 | ✅ | ORM 參數化查詢 |
| API 限流 | ✅ | 每分鐘 60 次 |
| 安全 Headers | ✅ | HSTS, CSP, X-Frame-Options |

---

## 🔧 技術實現

### 輸入驗證

```python
class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)

    @validator('name')
    def validate_name(cls, v):
        # 移除 HTML 標籤
        v = bleach.clean(v, tags=[], strip=True)
        # 檢查非法字符
        if not re.match(r'^[\w\s\-]+$', v):
            raise ValueError('Name contains invalid characters')
        return v
```

### 安全 Headers 中間件

```python
class SecurityHeadersMiddleware:
    """安全 Headers 中間件"""

    async def __call__(self, request: Request, call_next):
        response = await call_next(request)

        # HSTS
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # CSP
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        # 防止 Clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # 防止 MIME Sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS 保護
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response
```

### API 限流

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# 初始化
await FastAPILimiter.init(redis_client)

# 應用限流
@router.post("/workflows")
async def create_workflow(
    data: WorkflowCreate,
    _rate_limit = Depends(RateLimiter(times=60, seconds=60))
):
    pass
```

### CORS 配置

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ipa-platform.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-ID"],
)
```

---

## 📁 代碼位置

```
backend/src/
├── core/security/
│   ├── headers.py             # 安全 Headers
│   ├── rate_limit.py          # 限流配置
│   └── validation.py          # 輸入驗證
└── api/v1/security/
    └── routes.py              # 安全測試端點
```

---

## 🧪 測試覆蓋

- XSS 輸入過濾測試
- SQL 注入防護測試
- 限流功能測試
- 安全 Headers 驗證

---

## 📝 備註

- 所有輸入自動清理 HTML
- ORM 查詢全部參數化
- 限流支援按用戶/IP 配置

---

**生成日期**: 2025-11-26
