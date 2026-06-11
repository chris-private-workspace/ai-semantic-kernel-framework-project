# 🔄 情況3: 舊功能進階/修正開發

> **使用時機**: 對話進行中，正在開發舊功能的進階或修正
> **目標**: 保持開發流程順暢，及時記錄變更
> **適用場景**: Bug 修復、功能增強、重構

---

## 📋 Prompt 模板

```markdown
我正在 [修復 Bug / 增強功能 / 重構代碼]: [具體描述]

當前狀態: [剛開始 / 進行中 / 測試階段 / 完成]

請幫我:

1. 檢查當前任務狀態
   - 查看 TodoWrite 任務清單
   - 確認已完成和待完成的項目

2. 執行開發任務
   - 根據任務清單逐項執行
   - 每完成一項，更新 TodoWrite 狀態
   - 遇到問題時記錄到 claudedocs/4-changes/

3. 測試驗證
   - 運行相關測試
   - 手動測試功能
   - 記錄測試結果

4. 記錄變更
   - 更新 claudedocs/4-changes/[對應目錄]/FIX-XXX.md 或 CHANGE-XXX.md
   - 記錄問題、解決方案、影響範圍

請保持中文溝通。
```

---

## 🤖 AI 執行模式

### 模式A: Bug 修復流程
```bash
# 1. 理解問題
Read: [相關代碼文件]
Grep: [搜尋錯誤相關代碼]

# 2. 修復
Edit: [修改文件]
Bash: npm run type-check
Bash: npm run lint

# 3. 驗證
Bash: npm run dev (檢查運行狀態)

# 4. 記錄
Write: claudedocs/4-changes/bug-fixes/FIX-XXX-[描述].md

# 5. 更新 TodoWrite
TodoWrite: 標記已完成任務
```

### 模式B: 功能增強流程
```bash
# 1. 檢查現有實現
Read: [現有功能文件]
Grep: [搜尋相關模式]

# 2. 實施增強
Edit/Write: [修改或新增文件]

# 3. 測試
Bash: npm run type-check
Bash: npm run lint
Bash: npm run dev (檢查運行狀態)

# 4. 記錄
Write: claudedocs/4-changes/feature-changes/CHANGE-XXX-[描述].md

# 5. 更新進度
TodoWrite: 更新任務狀態
```

---

## 📝 變更記錄模板

### Bug 修復記錄
```markdown
# FIX-XXX: [Bug 簡述]

> **建立日期**: YYYY-MM-DD
> **嚴重程度**: Critical / High / Medium / Low
> **狀態**: 🔴 待修復 / 🟡 修復中 / ✅ 已修復

## 問題描述
[詳細描述問題，包括復現步驟]

## 根本原因
[分析根本原因]

## 解決方案
[描述解決方案]

## 影響範圍

### 修改文件
| 文件路徑 | 變更說明 |
|---------|----------|
| `src/xxx` | [變更說明] |

### 三層映射系統影響
- **Universal Mapping**: [是否影響]
- **Forwarder Override**: [是否影響]
- **LLM Classification**: [是否影響]

### 信心度路由影響
- **AUTO_APPROVE**: [是否影響]
- **QUICK_REVIEW**: [是否影響]
- **FULL_REVIEW**: [是否影響]

### 國際化 (i18n) 影響
- **翻譯文件**: [是否需要新增/更新翻譯]
- **格式化**: [是否涉及日期/數字/貨幣格式化]

## 測試驗證
- ✅ [測試項目 1]
- ✅ [測試項目 2]
- ✅ TypeScript 檢查通過
- ✅ ESLint 檢查通過

## 相關 Issue/Commit
- Issue: #XXX
- Commit: [commit hash]

---
*修復人: AI Assistant*
*修復時間: YYYY-MM-DD*
```

### 功能增強記錄
```markdown
# CHANGE-XXX: [增強功能簡述]

> **建立日期**: YYYY-MM-DD
> **類型**: 功能增強 / 效能優化 / UI 改善
> **狀態**: 📋 設計中 / 🚧 開發中 / ✅ 完成

## 增強目標
[描述增強的目標和預期效果]

## 設計方案
[描述設計選擇和理由]

## 實施內容

### 新增文件
| 文件路徑 | 用途 |
|---------|------|
| `src/xxx` | [用途說明] |

### 修改文件
| 文件路徑 | 變更說明 |
|---------|----------|
| `src/xxx` | [變更說明] |

## 向後兼容性
- [x] API 簽名保持不變
- [x] 資料結構兼容
- [ ] [其他兼容性說明]

## 驗證結果
- ✅ TypeScript 檢查通過
- ✅ ESLint 檢查通過
- ✅ 功能測試通過

---
*實施人: AI Assistant*
*完成時間: YYYY-MM-DD*
```

---

## 📁 文檔記錄位置

```
claudedocs/4-changes/
├── bug-fixes/              # Bug 修復記錄
│   ├── FIX-001-描述.md
│   ├── FIX-002-描述.md
│   └── ...
└── feature-changes/        # 功能變更記錄（包含重構）
    ├── CHANGE-001-描述.md
    ├── CHANGE-002-描述.md
    └── ...
```

---

## ✅ 驗收標準

### Bug 修復
- [ ] 問題已完全解決
- [ ] 沒有引入新的問題
- [ ] 代碼品質檢查通過
- [ ] 修復報告已記錄到 `claudedocs/4-changes/bug-fixes/`
- [ ] TodoWrite 任務已標記完成

### 功能增強
- [ ] 增強目標已達成
- [ ] 向後兼容性保持
- [ ] 代碼品質檢查通過
- [ ] 增強報告已記錄到 `claudedocs/4-changes/feature-changes/`
- [ ] TodoWrite 任務已標記完成

---

## 🔗 相關文檔

### 開發流程指引
- [情況1: 專案入門](./SITUATION-1-PROJECT-ONBOARDING.md)
- [情況2: 開發前準備](./SITUATION-2-FEATURE-DEV-PREP.md)
- [情況4: 新功能開發](./SITUATION-4-NEW-FEATURE-DEV.md)
- [情況5: 保存進度](./SITUATION-5-SAVE-PROGRESS.md)

### 開發規範
- [CLAUDE.md](../../../CLAUDE.md) - 開發規範
- [技術障礙處理](../../../.claude/rules/technical-obstacles.md)
- [PROJECT-INDEX.md](../../../PROJECT-INDEX.md) - 項目導航

---

**維護者**: AI 助手 + 開發團隊
**最後更新**: 2026-01-18
**版本**: 1.2
