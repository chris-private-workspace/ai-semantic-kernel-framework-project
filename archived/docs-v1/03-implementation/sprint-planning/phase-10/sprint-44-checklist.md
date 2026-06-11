# Sprint 44 Checklist: Session Features

**Sprint 目標**: 實現 Session 進階功能（檔案分析、生成、歷史管理）
**總點數**: 30 Story Points
**狀態**: 📋 計劃中
**前置條件**: Sprint 43 完成
**開始日期**: TBD

---

## 前置條件檢查

### Sprint 43 完成確認
- [ ] WebSocket 連接穩定
- [ ] 串流響應正常
- [ ] 工具調用和審批正常
- [ ] 事件即時推送

### 環境準備
- [ ] 確認 Code Interpreter 可用
- [ ] 確認檔案存儲配置
- [ ] 確認 MCP 權限系統

---

## Story Checklist

### S44-1: 檔案分析功能 (10 pts)

**狀態**: ⏳ 未開始

#### 實現任務

**創建目錄結構**
- [ ] 創建 `backend/src/domain/sessions/files/`
- [ ] 創建 `backend/src/domain/sessions/files/__init__.py`

**實現 FileType 枚舉** (`domain/sessions/files/types.py`)
- [ ] `FileType` 枚舉
  - [ ] DOCUMENT (PDF, Word, Excel, PowerPoint)
  - [ ] IMAGE (PNG, JPG, GIF, WebP)
  - [ ] CODE (Python, JavaScript, TypeScript, etc.)
  - [ ] DATA (CSV, JSON, XML, Parquet)
  - [ ] OTHER
- [ ] `AnalysisType` 枚舉
  - [ ] SUMMARY
  - [ ] EXTRACT
  - [ ] TRANSFORM
  - [ ] QUERY
  - [ ] VISUALIZE

**實現 FileAnalyzer** (`domain/sessions/files/analyzer.py`)
- [ ] `FileAnalyzer` 類
  - [ ] `__init__()` 初始化依賴
  - [ ] `analyze()` 分析檔案
    - [ ] 檢測檔案類型
    - [ ] 選擇分析策略
    - [ ] 執行分析
    - [ ] 返回結果
  - [ ] `_detect_file_type()` 檔案類型檢測
  - [ ] `_analyze_document()` 文件分析
  - [ ] `_analyze_image()` 圖像分析
  - [ ] `_analyze_code()` 代碼分析
  - [ ] `_analyze_data()` 數據分析

**實現 DocumentAnalyzer** (`domain/sessions/files/document_analyzer.py`)
- [ ] `DocumentAnalyzer` 類
  - [ ] `summarize()` 摘要文件
  - [ ] `extract_text()` 提取文字
  - [ ] `extract_tables()` 提取表格
  - [ ] `extract_images()` 提取圖片
  - [ ] `query()` 查詢文件內容

**實現 ImageAnalyzer** (`domain/sessions/files/image_analyzer.py`)
- [ ] `ImageAnalyzer` 類
  - [ ] `describe()` 描述圖像
  - [ ] `extract_text()` OCR 文字提取
  - [ ] `analyze_chart()` 圖表分析
  - [ ] `detect_objects()` 物件檢測

**實現 CodeAnalyzer** (`domain/sessions/files/code_analyzer.py`)
- [ ] `CodeAnalyzer` 類
  - [ ] `explain()` 解釋代碼
  - [ ] `find_issues()` 尋找問題
  - [ ] `suggest_improvements()` 建議改進
  - [ ] `generate_docs()` 生成文檔
  - [ ] `extract_structure()` 提取結構

**實現 DataAnalyzer** (`domain/sessions/files/data_analyzer.py`)
- [ ] `DataAnalyzer` 類
  - [ ] `summarize()` 數據摘要
  - [ ] `describe_schema()` 描述結構
  - [ ] `query()` 查詢數據
  - [ ] `visualize()` 數據視覺化
  - [ ] `transform()` 數據轉換

**整合 Code Interpreter**
- [ ] 注入 Code Interpreter 依賴
- [ ] 實現 Python 執行環境調用
- [ ] 處理執行結果

#### API 端點

**實現分析 API** (`api/v1/sessions/files.py`)
- [ ] `POST /sessions/{id}/files/{fid}/analyze` - 分析檔案
  - [ ] 認證和權限檢查
  - [ ] 分析類型參數
  - [ ] 調用分析器
  - [ ] 返回分析結果

#### 單元測試
- [ ] 創建 `tests/unit/domain/sessions/files/test_analyzer.py`
- [ ] 創建 `tests/unit/domain/sessions/files/test_document_analyzer.py`
- [ ] 創建 `tests/unit/domain/sessions/files/test_image_analyzer.py`
- [ ] 創建 `tests/unit/domain/sessions/files/test_code_analyzer.py`
- [ ] 創建 `tests/unit/domain/sessions/files/test_data_analyzer.py`
- [ ] 測試各類型檔案分析
- [ ] 測試錯誤處理

#### 驗證
```bash
python -m py_compile src/domain/sessions/files/analyzer.py
python -m py_compile src/domain/sessions/files/document_analyzer.py
python -m py_compile src/domain/sessions/files/image_analyzer.py
python -m py_compile src/domain/sessions/files/code_analyzer.py
python -m py_compile src/domain/sessions/files/data_analyzer.py
pytest tests/unit/domain/sessions/files/ -v
```

---

### S44-2: 檔案生成功能 (8 pts)

**狀態**: ⏳ 未開始

#### 實現任務

**實現 GenerationType 枚舉** (`domain/sessions/files/types.py`)
- [ ] `GenerationType` 枚舉
  - [ ] CODE (Python, JavaScript, etc.)
  - [ ] REPORT (Markdown, HTML, PDF)
  - [ ] DATA (CSV, JSON, Excel)
  - [ ] DIAGRAM (Mermaid, PlantUML)
  - [ ] IMAGE (Charts, Graphs)

**實現 FileGenerator** (`domain/sessions/files/generator.py`)
- [ ] `FileGenerator` 類
  - [ ] `__init__()` 初始化依賴
  - [ ] `generate()` 生成檔案
    - [ ] 解析生成請求
    - [ ] 選擇生成策略
    - [ ] 執行生成
    - [ ] 保存檔案
    - [ ] 返回結果
  - [ ] `_generate_code()` 生成代碼
  - [ ] `_generate_report()` 生成報告
  - [ ] `_generate_data()` 生成數據
  - [ ] `_generate_diagram()` 生成圖表
  - [ ] `_generate_image()` 生成圖像

**實現 CodeGenerator** (`domain/sessions/files/code_generator.py`)
- [ ] `CodeGenerator` 類
  - [ ] `generate()` 生成代碼
  - [ ] `refactor()` 重構代碼
  - [ ] `convert()` 轉換語言
  - [ ] `add_tests()` 添加測試

**實現 ReportGenerator** (`domain/sessions/files/report_generator.py`)
- [ ] `ReportGenerator` 類
  - [ ] `generate_markdown()` Markdown 報告
  - [ ] `generate_html()` HTML 報告
  - [ ] `generate_pdf()` PDF 報告
  - [ ] `_apply_template()` 應用模板

**實現 DataExporter** (`domain/sessions/files/data_exporter.py`)
- [ ] `DataExporter` 類
  - [ ] `to_csv()` 導出 CSV
  - [ ] `to_json()` 導出 JSON
  - [ ] `to_excel()` 導出 Excel
  - [ ] `to_parquet()` 導出 Parquet

**實現 DiagramGenerator** (`domain/sessions/files/diagram_generator.py`)
- [ ] `DiagramGenerator` 類
  - [ ] `generate_mermaid()` Mermaid 圖表
  - [ ] `generate_plantuml()` PlantUML 圖表
  - [ ] `generate_flowchart()` 流程圖
  - [ ] `generate_sequence()` 時序圖

#### API 端點

**實現生成 API**
- [ ] `POST /sessions/{id}/generate` - 生成檔案
  - [ ] 認證和權限檢查
  - [ ] 生成類型和參數
  - [ ] 調用生成器
  - [ ] 保存到附件
  - [ ] 返回下載連結

#### 單元測試
- [ ] 創建 `tests/unit/domain/sessions/files/test_generator.py`
- [ ] 創建 `tests/unit/domain/sessions/files/test_code_generator.py`
- [ ] 創建 `tests/unit/domain/sessions/files/test_report_generator.py`
- [ ] 創建 `tests/unit/domain/sessions/files/test_data_exporter.py`
- [ ] 創建 `tests/unit/domain/sessions/files/test_diagram_generator.py`
- [ ] 測試各類型檔案生成
- [ ] 測試模板應用

#### 驗證
```bash
python -m py_compile src/domain/sessions/files/generator.py
python -m py_compile src/domain/sessions/files/code_generator.py
python -m py_compile src/domain/sessions/files/report_generator.py
python -m py_compile src/domain/sessions/files/data_exporter.py
python -m py_compile src/domain/sessions/files/diagram_generator.py
pytest tests/unit/domain/sessions/files/test_*generator*.py -v
pytest tests/unit/domain/sessions/files/test_data_exporter.py -v
```

---

### S44-3: 對話歷史管理 (7 pts)

**狀態**: ⏳ 未開始

#### 實現任務

**實現 HistoryManager** (`domain/sessions/history.py`)
- [ ] `HistoryManager` 類
  - [ ] `__init__(repository)` 初始化
  - [ ] `search()` 搜索歷史
    - [ ] 關鍵字搜索
    - [ ] 時間範圍過濾
    - [ ] Session 過濾
    - [ ] 分頁支持
  - [ ] `get_context()` 獲取上下文
    - [ ] 最近 N 條訊息
    - [ ] 相關訊息
  - [ ] `export()` 導出歷史
    - [ ] JSON 格式
    - [ ] Markdown 格式
    - [ ] HTML 格式
  - [ ] `delete_range()` 刪除範圍
    - [ ] 時間範圍刪除
    - [ ] Session 刪除
    - [ ] 確認機制

**實現書籤功能** (`domain/sessions/bookmarks.py`)
- [ ] `Bookmark` 數據類
  - [ ] id, session_id, message_id
  - [ ] name, description
  - [ ] created_at
- [ ] `BookmarkService` 類
  - [ ] `create()` 創建書籤
  - [ ] `get()` 獲取書籤
  - [ ] `list_by_user()` 列出用戶書籤
  - [ ] `delete()` 刪除書籤

**實現搜索索引** (`domain/sessions/search.py`)
- [ ] `MessageSearchIndex` 類
  - [ ] `index()` 索引訊息
  - [ ] `search()` 全文搜索
  - [ ] `delete()` 刪除索引

#### API 端點

**實現歷史 API**
- [ ] `GET /sessions/history/search` - 搜索歷史
  - [ ] 認證
  - [ ] 搜索參數
  - [ ] 分頁
- [ ] `POST /sessions/history/export` - 導出歷史
  - [ ] 認證
  - [ ] 格式選擇
  - [ ] 返回檔案
- [ ] `POST /sessions/{id}/messages/{mid}/bookmark` - 創建書籤
  - [ ] 認證和權限
  - [ ] 書籤名稱
- [ ] `GET /sessions/bookmarks` - 列出書籤
  - [ ] 認證
  - [ ] 分頁
- [ ] `DELETE /sessions/bookmarks/{bid}` - 刪除書籤
  - [ ] 認證和權限

#### 數據庫遷移
- [ ] 創建 `bookmarks` 表
  ```sql
  CREATE TABLE bookmarks (
      id UUID PRIMARY KEY,
      user_id UUID NOT NULL REFERENCES users(id),
      session_id UUID NOT NULL REFERENCES sessions(id),
      message_id UUID NOT NULL REFERENCES messages(id),
      name VARCHAR(100) NOT NULL,
      description TEXT,
      created_at TIMESTAMP DEFAULT NOW()
  );
  CREATE INDEX idx_bookmarks_user ON bookmarks(user_id);
  ```

#### 單元測試
- [ ] 創建 `tests/unit/domain/sessions/test_history.py`
- [ ] 創建 `tests/unit/domain/sessions/test_bookmarks.py`
- [ ] 創建 `tests/unit/domain/sessions/test_search.py`
- [ ] 測試搜索功能
- [ ] 測試導出功能
- [ ] 測試書籤 CRUD

#### 驗證
```bash
python -m py_compile src/domain/sessions/history.py
python -m py_compile src/domain/sessions/bookmarks.py
python -m py_compile src/domain/sessions/search.py
pytest tests/unit/domain/sessions/test_history.py -v
pytest tests/unit/domain/sessions/test_bookmarks.py -v
pytest tests/unit/domain/sessions/test_search.py -v
```

---

### S44-4: Session 進階功能 (5 pts)

**狀態**: ⏳ 未開始

#### 實現任務

**實現 Session 複製** (`domain/sessions/service.py`)
- [ ] `clone_session()` 複製 Session
  - [ ] 複製配置
  - [ ] 可選複製歷史
  - [ ] 創建新 Session
  - [ ] 返回新 Session

**實現 Session 標籤** (`domain/sessions/tags.py`)
- [ ] `SessionTag` 數據類
  - [ ] id, session_id, name
  - [ ] color, created_at
- [ ] `TagService` 類
  - [ ] `add_tag()` 添加標籤
  - [ ] `remove_tag()` 移除標籤
  - [ ] `list_tags()` 列出標籤
  - [ ] `find_by_tag()` 按標籤查找

**實現 Session 統計** (`domain/sessions/statistics.py`)
- [ ] `SessionStatistics` 數據類
  - [ ] total_messages
  - [ ] total_tokens
  - [ ] total_tool_calls
  - [ ] total_attachments
  - [ ] duration
  - [ ] average_response_time
- [ ] `StatisticsService` 類
  - [ ] `calculate()` 計算統計
  - [ ] `aggregate_user()` 用戶統計
  - [ ] `aggregate_period()` 時段統計

**實現 Session 模板** (`domain/sessions/templates.py`)
- [ ] `SessionTemplate` 數據類
  - [ ] id, name, description
  - [ ] config, system_prompt
  - [ ] created_by, created_at
- [ ] `TemplateService` 類
  - [ ] `create()` 創建模板
  - [ ] `get()` 獲取模板
  - [ ] `list()` 列出模板
  - [ ] `apply()` 應用模板
  - [ ] `delete()` 刪除模板

#### API 端點

**實現進階 API**
- [ ] `POST /sessions/{id}/clone` - 複製 Session
  - [ ] 認證和權限
  - [ ] 複製選項
- [ ] `POST /sessions/{id}/tags` - 添加標籤
- [ ] `DELETE /sessions/{id}/tags/{name}` - 移除標籤
- [ ] `GET /sessions/{id}/statistics` - 獲取統計
- [ ] `GET /sessions/statistics/aggregate` - 聚合統計
- [ ] `POST /sessions/templates` - 創建模板
- [ ] `GET /sessions/templates` - 列出模板
- [ ] `POST /sessions/from-template/{tid}` - 從模板創建

#### 數據庫遷移
- [ ] 創建 `session_tags` 表
  ```sql
  CREATE TABLE session_tags (
      id UUID PRIMARY KEY,
      session_id UUID NOT NULL REFERENCES sessions(id),
      name VARCHAR(50) NOT NULL,
      color VARCHAR(7),
      created_at TIMESTAMP DEFAULT NOW(),
      UNIQUE(session_id, name)
  );
  CREATE INDEX idx_session_tags_name ON session_tags(name);
  ```
- [ ] 創建 `session_templates` 表
  ```sql
  CREATE TABLE session_templates (
      id UUID PRIMARY KEY,
      name VARCHAR(100) NOT NULL,
      description TEXT,
      config JSONB NOT NULL,
      system_prompt TEXT,
      created_by UUID REFERENCES users(id),
      created_at TIMESTAMP DEFAULT NOW(),
      updated_at TIMESTAMP DEFAULT NOW()
  );
  ```

#### 單元測試
- [ ] 創建 `tests/unit/domain/sessions/test_tags.py`
- [ ] 創建 `tests/unit/domain/sessions/test_statistics.py`
- [ ] 創建 `tests/unit/domain/sessions/test_templates.py`
- [ ] 測試 Session 複製
- [ ] 測試標籤功能
- [ ] 測試統計計算
- [ ] 測試模板應用

#### 驗證
```bash
python -m py_compile src/domain/sessions/tags.py
python -m py_compile src/domain/sessions/statistics.py
python -m py_compile src/domain/sessions/templates.py
pytest tests/unit/domain/sessions/test_tags.py -v
pytest tests/unit/domain/sessions/test_statistics.py -v
pytest tests/unit/domain/sessions/test_templates.py -v
```

---

## 驗證命令匯總

```bash
# 1. 語法檢查
cd backend
python -m py_compile src/domain/sessions/files/analyzer.py
python -m py_compile src/domain/sessions/files/generator.py
python -m py_compile src/domain/sessions/history.py
python -m py_compile src/domain/sessions/bookmarks.py
python -m py_compile src/domain/sessions/tags.py
python -m py_compile src/domain/sessions/statistics.py
python -m py_compile src/domain/sessions/templates.py

# 2. 運行單元測試
pytest tests/unit/domain/sessions/files/ -v
pytest tests/unit/domain/sessions/test_history.py -v
pytest tests/unit/domain/sessions/test_bookmarks.py -v
pytest tests/unit/domain/sessions/test_tags.py -v
pytest tests/unit/domain/sessions/test_statistics.py -v
pytest tests/unit/domain/sessions/test_templates.py -v

# 3. 覆蓋率檢查
pytest tests/unit/domain/sessions/ -v --cov=src/domain/sessions

# 4. 數據庫遷移
alembic upgrade head
```

---

## 完成定義

- [ ] 所有 S44 Story 完成
- [ ] 檔案分析功能正常
- [ ] 檔案生成功能正常
- [ ] 對話歷史管理正常
- [ ] Session 進階功能正常
- [ ] 測試覆蓋率 > 85%
- [ ] 代碼審查完成
- [ ] API 文檔更新

---

## 輸出產物

| 文件 | 類型 | 說明 |
|------|------|------|
| `domain/sessions/files/__init__.py` | 新增 | 檔案模組 |
| `domain/sessions/files/types.py` | 新增 | 類型定義 |
| `domain/sessions/files/analyzer.py` | 新增 | 檔案分析器 |
| `domain/sessions/files/document_analyzer.py` | 新增 | 文件分析 |
| `domain/sessions/files/image_analyzer.py` | 新增 | 圖像分析 |
| `domain/sessions/files/code_analyzer.py` | 新增 | 代碼分析 |
| `domain/sessions/files/data_analyzer.py` | 新增 | 數據分析 |
| `domain/sessions/files/generator.py` | 新增 | 檔案生成器 |
| `domain/sessions/files/code_generator.py` | 新增 | 代碼生成 |
| `domain/sessions/files/report_generator.py` | 新增 | 報告生成 |
| `domain/sessions/files/data_exporter.py` | 新增 | 數據導出 |
| `domain/sessions/files/diagram_generator.py` | 新增 | 圖表生成 |
| `domain/sessions/history.py` | 新增 | 歷史管理 |
| `domain/sessions/bookmarks.py` | 新增 | 書籤功能 |
| `domain/sessions/search.py` | 新增 | 搜索索引 |
| `domain/sessions/tags.py` | 新增 | 標籤功能 |
| `domain/sessions/statistics.py` | 新增 | 統計功能 |
| `domain/sessions/templates.py` | 新增 | 模板功能 |
| `api/v1/sessions/files.py` | 新增 | 檔案 API |
| `tests/unit/domain/sessions/files/` | 新增 | 檔案測試 |
| `tests/unit/domain/sessions/test_*.py` | 新增 | 進階功能測試 |

---

## Phase 10 完成確認

當 Sprint 44 完成後，Phase 10 Session Mode API 將全部完成：

| Sprint | 內容 | 點數 | 狀態 |
|--------|------|------|------|
| Sprint 42 | Session Management Core | 35 | ⏳ |
| Sprint 43 | Real-time Communication | 35 | ⏳ |
| Sprint 44 | Session Features | 30 | ⏳ |
| **總計** | | **100** | |

---

## 下一步

- Phase 11: 進階功能擴展 (待規劃)
- 系統整合測試
- UAT 驗收測試

---

**創建日期**: 2025-12-22
**上次更新**: 2025-12-22
