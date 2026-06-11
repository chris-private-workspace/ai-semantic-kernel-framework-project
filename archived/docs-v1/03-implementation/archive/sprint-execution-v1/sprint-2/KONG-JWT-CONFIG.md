# Kong JWT Authentication Configuration

**配置日期**: 2025-11-25
**狀態**: ✅ 完成

---

## 配置概覽

Kong JWT 認證已成功配置於以下服務：

| 服務 | JWT Plugin ID | 狀態 |
|------|--------------|------|
| workflow-service | b30fad6d-3e32-4a27-a929-8550bd1c9197 | ✅ 啟用 |
| agent-service | 5e9bf6b0-b0e9-4b8e-966d-67046dcc4b45 | ✅ 啟用 |
| auth-service | - | 無需 JWT (登入端點) |
| health-service | - | 無需 JWT (公開端點) |

---

## Consumer 配置

```yaml
Consumer:
  username: ipa-platform-user
  custom_id: default-user
  id: 7a008523-998d-46ef-a083-5b4cea5a625f
```

---

## JWT Credentials

```yaml
JWT Credential:
  key: ipa-jwt-key
  secret: 707fde7bb5f14546e4757f73904a7ec61bc8255d8fb1924f566d0d8d4753a284
  algorithm: HS256
  id: 92b959b1-fd57-4e6c-8d5b-81f9b5fbba55
```

**重要**: 生產環境應使用不同的 secret，並存儲在安全的密鑰管理服務中。

---

## JWT Plugin 配置

```yaml
JWT Plugin Config:
  key_claim_name: iss
  secret_is_base64: false
  claims_to_verify: [exp]
```

---

## 生成 JWT Token

### Python 範例

```python
import hmac
import hashlib
import base64
import json
import time

# JWT 配置
jwt_key = 'ipa-jwt-key'
jwt_secret = '707fde7bb5f14546e4757f73904a7ec61bc8255d8fb1924f566d0d8d4753a284'

# Header
header = {'alg': 'HS256', 'typ': 'JWT'}
header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b'=').decode()

# Payload
payload = {
    'iss': jwt_key,  # 必須與 Kong 中註冊的 key 匹配
    'exp': int(time.time()) + 3600,  # 1 小時後過期
    'sub': 'user-id',
    'name': 'User Name'
}
payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=').decode()

# Signature
message = f'{header_b64}.{payload_b64}'
signature = hmac.new(jwt_secret.encode(), message.encode(), hashlib.sha256).digest()
signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()

# Complete JWT
jwt_token = f'{header_b64}.{payload_b64}.{signature_b64}'
print(jwt_token)
```

### 使用 JWT Token

```bash
# API 請求示例
curl -H "Authorization: Bearer <JWT_TOKEN>" http://localhost:8000/api/v1/workflows
```

---

## 測試結果

### 測試 1: 無 JWT Token
```
Request: GET /api/v1/workflows
Response: 401 Unauthorized
Result: ✅ JWT 保護生效
```

### 測試 2: 有效 JWT Token
```
Request: GET /api/v1/workflows (with valid JWT)
Response: 200 OK / 404 Not Found (取決於資料)
Result: ✅ JWT 認證成功
```

### 測試 3: Health Endpoint (無需 JWT)
```
Request: GET /health
Response: 200 OK
Result: ✅ 公開端點正常訪問
```

---

## Kong Admin API 命令

### 查看 JWT Plugins
```bash
curl http://localhost:8001/plugins | jq '.data[] | select(.name=="jwt")'
```

### 查看 Consumers
```bash
curl http://localhost:8001/consumers
```

### 查看 JWT Credentials
```bash
curl http://localhost:8001/consumers/ipa-platform-user/jwt
```

### 添加新 Consumer
```bash
curl -X POST http://localhost:8001/consumers \
  -d "username=new-user" \
  -d "custom_id=user-123"
```

### 為 Consumer 添加 JWT Credential
```bash
curl -X POST http://localhost:8001/consumers/new-user/jwt \
  -d "key=new-jwt-key" \
  -d "secret=your-secret-here" \
  -d "algorithm=HS256"
```

---

## 與後端整合

後端應用需要：

1. **生成 JWT Token**: 在用戶登入成功後生成 JWT
2. **驗證 JWT Token**: Kong 已處理，後端可信任通過的請求
3. **Token 刷新**: 實現 refresh token 機制

### 後端 JWT 配置 (.env)

```bash
# Kong JWT Configuration
KONG_JWT_KEY=ipa-jwt-key
KONG_JWT_SECRET=707fde7bb5f14546e4757f73904a7ec61bc8255d8fb1924f566d0d8d4753a284
KONG_JWT_ALGORITHM=HS256
KONG_JWT_EXPIRY_HOURS=24
```

---

## 安全建議

1. **生產環境**: 使用不同的 JWT secret
2. **密鑰輪換**: 定期更換 JWT secret
3. **短期 Token**: 使用較短的過期時間 (1-24 小時)
4. **Refresh Token**: 實現 refresh token 機制
5. **HTTPS**: 生產環境必須使用 HTTPS
6. **密鑰存儲**: 使用 Azure Key Vault 或類似服務

---

## 相關文檔

- [Kong JWT Plugin 文檔](https://docs.konghq.com/hub/kong-inc/jwt/)
- [S1-8 API Gateway Setup Summary](../sprint-1/S1-8-api-gateway-setup-summary.md)
- [Sprint 2 準備檢查清單](./SPRINT-2-PREP-CHECKLIST.md)
