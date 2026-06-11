# Sprint 92 技術決策記錄

## 決策列表

### D92-1: Semantic Router 選型

**決策**: 採用 Aurelio Semantic Router

**選項**:
1. Aurelio Semantic Router (選擇)
2. 自建向量相似度匹配
3. 使用 LangChain Router

**選擇**: 選項 1

**理由**:
- 專為語義路由設計的成熟庫
- 支持多種編碼器 (OpenAI, HuggingFace)
- 活躍的社區維護
- 易於與現有架構整合
- 效能優化佳，延遲 < 100ms

---

### D92-2: LLM 分類器模型選擇

**決策**: 使用 Claude Haiku 作為 LLM 分類器

**選項**:
1. Claude Haiku (選擇)
2. Claude Sonnet
3. GPT-4 Turbo
4. 本地部署模型

**選擇**: 選項 1

**理由**:
- 成本效益高：比 Sonnet/GPT-4 便宜
- 延遲低：適合實時分類場景
- 準確度足夠：分類任務不需要最強模型
- 與現有 Claude SDK 整合良好
- 支持 JSON 輸出模式

---

### D92-3: 多任務 Prompt 設計策略

**決策**: 單一 Prompt 同時輸出分類和完整度

**選項**:
1. 單一 Prompt 多任務輸出 (選擇)
2. 分離 Prompt 串行調用
3. 並行調用多個專用 Prompt

**選擇**: 選項 1

**理由**:
- 減少 API 調用次數
- 降低延遲 (單次 vs 多次)
- 減少 token 消耗
- 上下文一致性更好
- 簡化錯誤處理邏輯

---

### D92-4: Semantic Router 編碼器選擇

**決策**: 使用 OpenAI 編碼器 (text-embedding-3-small)

**選項**:
1. OpenAI text-embedding-3-small (選擇)
2. OpenAI text-embedding-ada-002
3. HuggingFace 本地模型
4. Cohere Embed

**選擇**: 選項 1

**理由**:
- 高質量嵌入向量
- 成本合理
- 支持多語言 (中文、英文)
- 與 Aurelio Router 原生整合
- 維度適中 (1536 維)

---

### D92-5: 路由相似度閾值設定

**決策**: 預設閾值 0.85，可配置

**考量**:
- 閾值太高 (>0.9)：假陰性增加，更多請求升級到 LLM
- 閾值太低 (<0.8)：假陽性增加，錯誤分類風險
- 0.85 平衡準確性和覆蓋率

**配置方式**:
- 環境變數: `SEMANTIC_ROUTER_THRESHOLD`
- 預設值: 0.85
- 範圍: 0.70 - 0.95

---

**創建日期**: 2026-01-15
**更新日期**: 2026-01-15
