# Sprint 44 Technical Decisions: Session Features

## 決策記錄

| ID | 決策 | 日期 | 狀態 |
|----|------|------|------|
| D44-1 | 文件分析使用策略模式 | 2025-12-22 | ⏳ 待實現 |
| D44-2 | 文件生成使用工廠模式 | 2025-12-22 | ⏳ 待實現 |
| D44-3 | 書籤使用獨立表存儲 | 2025-12-22 | ⏳ 待實現 |
| D44-4 | 統計使用延遲計算 | 2025-12-22 | ⏳ 待實現 |

---

## 決策詳情

### D44-1: 文件分析使用策略模式

**背景**: 需要支援多種文件類型的分析

**選項**:
1. 單一分析器處理所有類型
2. 策略模式 - 每種類型獨立分析器
3. 外部服務處理

**決策**: 策略模式

**理由**:
- 易於擴展新文件類型
- 每種類型可獨立優化
- 符合開閉原則
- 便於測試和維護

**設計**:
```python
class FileAnalyzer:
    """主分析器 - 策略選擇器"""

    def analyze(self, attachment, request):
        analyzer = self._get_analyzer(attachment.attachment_type)
        return analyzer.analyze(attachment, request)

    def _get_analyzer(self, file_type):
        strategies = {
            AttachmentType.DOCUMENT: DocumentAnalyzer,
            AttachmentType.IMAGE: ImageAnalyzer,
            AttachmentType.CODE: CodeAnalyzer,
            AttachmentType.DATA: DataAnalyzer,
        }
        return strategies.get(file_type, GenericAnalyzer)()
```

---

### D44-2: 文件生成使用工廠模式

**背景**: 需要生成多種類型的文件

**選項**:
1. 直接在服務中生成
2. 工廠模式創建生成器
3. 模板引擎

**決策**: 工廠模式 + 模板引擎

**理由**:
- 統一的生成介面
- 易於添加新格式
- 模板引擎提供靈活性
- 代碼和報告可複用邏輯

**設計**:
```python
class FileGenerator:
    """文件生成器工廠"""

    def generate(self, gen_type, content, options):
        generator = self._create_generator(gen_type)
        return generator.generate(content, options)

    def _create_generator(self, gen_type):
        factories = {
            GenerationType.CODE: CodeGenerator,
            GenerationType.REPORT: ReportGenerator,
            GenerationType.DATA: DataExporter,
        }
        return factories[gen_type]()
```

---

### D44-3: 書籤使用獨立表存儲

**背景**: 需要管理用戶的訊息書籤

**選項**:
1. 在 Message 表添加 bookmark 欄位
2. 獨立 Bookmark 表
3. 存儲在用戶 metadata 中

**決策**: 獨立 Bookmark 表

**理由**:
- 不影響 Message 表結構
- 支援額外元數據 (名稱、描述)
- 便於查詢和索引
- 支援未來擴展 (分享、分類)

**表結構**:
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

---

### D44-4: 統計使用延遲計算

**背景**: 需要計算 Session 統計數據

**選項**:
1. 實時計算 - 每次請求時計算
2. 預計算 - 定期更新快取
3. 延遲計算 - 按需計算 + 快取

**決策**: 延遲計算 + 快取

**理由**:
- 平衡效能和準確性
- 不頻繁訪問時節省資源
- 快取減少重複計算
- 支援強制刷新

**設計**:
```python
class StatisticsService:
    CACHE_TTL = 300  # 5 分鐘

    async def get_statistics(self, session_id, force_refresh=False):
        cache_key = f"stats:{session_id}"

        if not force_refresh:
            cached = await self._cache.get(cache_key)
            if cached:
                return cached

        stats = await self._calculate(session_id)
        await self._cache.set(cache_key, stats, ttl=self.CACHE_TTL)
        return stats
```

---

**創建日期**: 2025-12-22
**更新日期**: 2025-12-22
