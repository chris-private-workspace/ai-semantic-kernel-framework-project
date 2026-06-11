# Sprint 38 Checklist: Agent 整合與擴展

**Sprint 目標**: 將 Code Interpreter 整合到現有 Agent 工作流程，實現文件處理和結果可視化
**總點數**: 15 Story Points
**狀態**: 📋 計劃中
**前置條件**: Sprint 37 完成
**開始日期**: TBD

---

## 前置條件檢查

### Sprint 37 完成確認
- [ ] AssistantManagerService 實現完成
- [ ] CodeInterpreterAdapter 適配器可用
- [ ] Code Interpreter API 端點運行正常
- [ ] 單元測試全部通過

### 驗證命令
```bash
# 確認 Sprint 37 功能正常
curl http://localhost:8000/api/v1/code-interpreter/health
# 預期: {"status": "healthy", "service": "code-interpreter"}

curl -X POST http://localhost:8000/api/v1/code-interpreter/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(1+1)"}'
# 預期: {"success": true, "output": "2", ...}
```

---

## Story Checklist

### S38-1: Agent 工具擴展 - Code Interpreter 支援 (5 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] Sprint 37 完成
- [ ] 確認 Agent Tool 規範

#### 實現任務
- [ ] 創建目錄 `backend/src/integrations/agent_framework/tools/`
- [ ] 創建 `__init__.py`
- [ ] 創建 `base.py` - Tool 基類
  - [ ] `Tool` 抽象類
  - [ ] `ToolResult` 數據類
- [ ] 創建 `code_interpreter_tool.py`
  - [ ] `CodeInterpreterTool` 類
  - [ ] `run()` 方法實現
  - [ ] `_execute_code()` 實現
  - [ ] `_analyze_file()` 實現
  - [ ] `_generate_visualization()` 實現
  - [ ] `cleanup()` 方法
- [ ] 更新 `tools/__init__.py` 導出

#### 驗證
- [ ] 遵循 Tool 規範接口
- [ ] Agent 可調用此工具
- [ ] 所有操作類型正常工作

---

### S38-2: 文件上傳與處理功能 (5 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] S38-1 完成
- [ ] 確認 Azure OpenAI Files API 可用

#### 實現任務
- [ ] 創建 `assistant/files.py`
  - [ ] `FileInfo` 數據類
  - [ ] `FileStorageService` 類
  - [ ] `upload()` 方法
  - [ ] `upload_from_path()` 方法
  - [ ] `list_files()` 方法
  - [ ] `download()` 方法
  - [ ] `delete()` 方法
- [ ] 擴展 API 端點
  - [ ] `POST /files/upload` - 上傳文件
  - [ ] `GET /files` - 列出文件
  - [ ] `GET /files/{file_id}` - 獲取文件信息
  - [ ] `DELETE /files/{file_id}` - 刪除文件
- [ ] 整合到 CodeInterpreterAdapter
  - [ ] 支援帶文件的分析任務

#### 驗證
- [ ] 文件上傳成功
- [ ] 支援 CSV, Excel, JSON 格式
- [ ] Code Interpreter 可讀取上傳文件

---

### S38-3: 執行結果可視化 (3 pts)

**狀態**: ⏳ 未開始

#### 準備工作
- [ ] S38-2 完成

#### 實現任務
- [ ] 創建 `api/v1/code_interpreter/visualization.py`
  - [ ] `VisualizationRequest` Schema
  - [ ] `GET /visualizations/{file_id}` 端點
  - [ ] `POST /visualizations/generate` 端點
- [ ] 支援圖表類型
  - [ ] bar (柱狀圖)
  - [ ] line (折線圖)
  - [ ] pie (圓餅圖)
  - [ ] scatter (散點圖)
- [ ] 響應格式
  - [ ] 圖片文件流
  - [ ] Base64 編碼選項

#### 驗證
- [ ] 可視化 API 可用
- [ ] 圖片正確生成
- [ ] 圖片可下載/顯示

---

### S38-4: 文檔更新和示例 (2 pts)

**狀態**: ⏳ 未開始

#### 實現任務
- [ ] 更新 OpenAPI 文檔
  - [ ] 所有新端點說明
  - [ ] 請求/響應示例
  - [ ] 錯誤代碼說明
- [ ] 創建示例代碼
  - [ ] Python SDK 使用示例
  - [ ] cURL 命令示例
  - [ ] 完整工作流示例
- [ ] 更新 README
  - [ ] 添加 Code Interpreter 功能說明
  - [ ] 更新功能列表
  - [ ] 添加快速開始指南

#### 驗證
- [ ] API 文檔完整且準確
- [ ] 示例代碼可運行
- [ ] README 更新完成

---

## 驗證命令

```bash
# 1. 語法檢查
cd backend
python -m py_compile src/integrations/agent_framework/tools/base.py
python -m py_compile src/integrations/agent_framework/tools/code_interpreter_tool.py
python -m py_compile src/integrations/agent_framework/assistant/files.py
python -m py_compile src/api/v1/code_interpreter/visualization.py
# 預期: 無輸出 (無錯誤)

# 2. 類型檢查
mypy src/integrations/agent_framework/tools/
mypy src/integrations/agent_framework/assistant/files.py
# 預期: Success

# 3. 代碼風格
black src/integrations/agent_framework/tools/ --check
black src/integrations/agent_framework/assistant/files.py --check
# 預期: All done!

# 4. 運行單元測試
pytest tests/unit/integrations/agent_framework/tools/ -v --cov
# 預期: 全部通過

# 5. 文件上傳測試
curl -X POST http://localhost:8000/api/v1/code-interpreter/files/upload \
  -F "file=@test_data.csv"
# 預期: {"id": "file-xxx", "filename": "test_data.csv", ...}

# 6. 列出文件
curl http://localhost:8000/api/v1/code-interpreter/files
# 預期: {"files": [...]}

# 7. 生成可視化
curl -X POST http://localhost:8000/api/v1/code-interpreter/visualizations/generate \
  -H "Content-Type: application/json" \
  -d '{"data": {"A": 10, "B": 20, "C": 30}, "chart_type": "bar", "title": "Test Chart"}'
# 預期: {"success": true, "files": [...]}

# 8. 下載可視化圖片
curl http://localhost:8000/api/v1/code-interpreter/visualizations/{file_id} \
  --output chart.png
# 預期: 圖片文件保存成功
```

---

## 完成定義

- [ ] 所有 S38 Story 完成
- [ ] CodeInterpreterTool 整合到 Agent 系統
- [ ] 文件上傳/下載 API 可用
- [ ] 可視化生成 API 可用
- [ ] 測試覆蓋率 > 85%
- [ ] 文檔和示例完成
- [ ] 代碼審查完成
- [ ] 語法/類型/風格檢查全部通過

---

## 輸出產物

| 文件 | 類型 | 說明 |
|------|------|------|
| `src/integrations/agent_framework/tools/__init__.py` | 新增 | 工具模組初始化 |
| `src/integrations/agent_framework/tools/base.py` | 新增 | Tool 基類 |
| `src/integrations/agent_framework/tools/code_interpreter_tool.py` | 新增 | CodeInterpreterTool |
| `src/integrations/agent_framework/assistant/files.py` | 新增 | FileStorageService |
| `src/api/v1/code_interpreter/visualization.py` | 新增 | 可視化 API |
| `src/api/v1/code_interpreter/routes.py` | 修改 | 擴展文件端點 |
| `tests/unit/integrations/agent_framework/tools/` | 新增 | 工具單元測試 |
| `tests/integration/test_file_upload.py` | 新增 | 文件上傳測試 |
| `docs/api/code-interpreter.md` | 新增 | API 文檔 |
| `examples/code_interpreter/` | 新增 | 示例代碼 |

---

## 備註

### 支援的文件格式
- CSV (.csv)
- Excel (.xlsx, .xls)
- JSON (.json)
- Text (.txt)
- Python (.py)

### 圖表類型
| 類型 | 說明 | 適用場景 |
|------|------|---------|
| bar | 柱狀圖 | 類別比較 |
| line | 折線圖 | 趨勢分析 |
| pie | 圓餅圖 | 比例分析 |
| scatter | 散點圖 | 相關性分析 |

### 文件大小限制
- 單個文件最大: 512 MB
- 總存儲限制: 100 GB (Azure 限制)

---

**創建日期**: 2025-12-21
**上次更新**: 2025-12-21
