# Azure OpenAI Responses API - 重要技術筆記

> **文檔目的**: 記錄 Azure OpenAI Responses API (2025-03-01-preview) 的重要發現，特別是 Code Interpreter 檔案下載功能的實作細節。

---

## 關鍵發現：Container Files API

### 背景

Azure OpenAI 的 **Responses API** (取代舊版 Assistants API) 使用不同的檔案處理機制。Code Interpreter 生成的檔案存放在 **Container** 中，而非傳統的 Files API。

**官方文檔不完整**：截至 2025-12，Microsoft 官方文檔尚未完整說明 Container Files API 的使用方式。此發現來自 Microsoft Q&A 社區解決方案。

### 參考資源

- **Microsoft Q&A - Please Make Code Interpreter usable**
  https://learn.microsoft.com/en-us/answers/questions/5534977

- **Microsoft Q&A - Responses API doesn't support files**
  https://learn.microsoft.com/en-us/answers/questions/5508278

---

## Container Files API 規範

### 下載檔案端點

```
GET {endpoint}/openai/v1/containers/{container_id}/files/{file_id}/content
```

### 參數說明

| 參數 | 說明 | 範例 |
|------|------|------|
| `endpoint` | Azure OpenAI 端點 | `https://xxx.openai.azure.com` |
| `container_id` | 容器 ID，從 response 取得 | `ctnr_abc123...` |
| `file_id` | 檔案 ID，以 `cfile_` 開頭 | `cfile_xyz789...` |

### 請求標頭

```http
api-key: {your_api_key}
```

### 查詢參數

```
api-version=preview
```

**重要**: 使用 `preview` 而非具體日期版本（如 `2025-03-01-preview`）。

---

## 完整請求範例

```http
GET https://your-resource.openai.azure.com/openai/v1/containers/ctnr_abc123/files/cfile_xyz789/content?api-version=preview
Headers:
  api-key: your-api-key-here
```

### cURL 範例

```bash
curl -X GET \
  "https://your-resource.openai.azure.com/openai/v1/containers/{container_id}/files/{file_id}/content?api-version=preview" \
  -H "api-key: your-api-key"
```

---

## 檔案 ID 格式差異

| API 版本 | 檔案 ID 前綴 | 範例 |
|----------|-------------|------|
| **Responses API** (新) | `cfile_` | `cfile_6842f6e5d0d0819...` |
| **Assistants API** (舊) | `assistant-` | `assistant-abc123...` |

---

## 獲取 Container ID 的方法

### 從 Response Output 取得

當 Code Interpreter 執行完成後，response 會包含 `code_interpreter_call` 項目：

```python
for item in response.output:
    if item.type == "code_interpreter_call":
        # container_id 在 item 的 results 中
        for result in item.code_interpreter_call.results:
            if hasattr(result, "container_id"):
                container_id = result.container_id
```

### Python 實作範例

```python
def _extract_container_id(self, response) -> Optional[str]:
    """從 response 中提取 container_id"""
    if not hasattr(response, "output") or not response.output:
        return None

    for item in response.output:
        if hasattr(item, "type") and item.type == "code_interpreter_call":
            code_call = getattr(item, "code_interpreter_call", None)
            if code_call and hasattr(code_call, "results"):
                for result in code_call.results:
                    if hasattr(result, "container_id"):
                        return result.container_id
    return None
```

---

## 常見錯誤與解決方案

### 錯誤 1: API version not supported

```json
{
  "error": {
    "code": "400",
    "message": "API version xxx is not supported"
  }
}
```

**解決**: 使用 `api-version=preview`

### 錯誤 2: 404 Not Found

```json
{
  "error": {
    "code": "404",
    "message": "Container or file not found"
  }
}
```

**可能原因**:
1. container_id 或 file_id 錯誤
2. 容器已過期（Azure 可能有時間限制）
3. Azure 區域尚未完全支援此功能

### 錯誤 3: 使用錯誤的端點格式

```
# 錯誤 - 這是 Assistants API 的格式
GET /openai/files/{file_id}/content

# 正確 - Responses API Container Files 格式
GET /openai/v1/containers/{container_id}/files/{file_id}/content
```

---

## 實作檢查清單

- [ ] 使用正確的端點格式：`/openai/v1/containers/{container_id}/files/{file_id}/content`
- [ ] 使用 `api-version=preview` 查詢參數
- [ ] 使用 `api-key` 標頭（非 `Authorization: Bearer`）
- [ ] 從 `code_interpreter_call` response 正確提取 `container_id`
- [ ] 處理 container/file 可能已過期的情況

---

## 相關檔案

- **實作**: `backend/src/integrations/agent_framework/builders/code_interpreter.py`
- **測試**: `scripts/uat/phase_tests/phase_8_code_interpreter/test_responses_api.py`
- **API 路由**: `backend/src/api/v1/code_interpreter/routes.py`

---

## 版本記錄

| 日期 | 版本 | 說明 |
|------|------|------|
| 2025-12-23 | 1.0 | 初始文檔，記錄 Container Files API 發現 |

---

**Last Updated**: 2025-12-23
**Author**: Claude Code (AI Assistant)
**Status**: Verified Working (7/7 tests passed)
