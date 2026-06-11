# AI Assistant Session 開始指引

> 本指引用於每次 AI 助手 Session 開始時的標準流程

---

## Session 開始檢查清單

### 1. 環境確認
- [ ] 確認專案目錄：`ai-document-extraction-project`
- [ ] 確認 Docker 容器運行中（PostgreSQL, pgAdmin）
- [ ] 確認開發伺服器狀態

### 2. 狀態回顧
- [ ] 檢查 `claudedocs/3-progress/daily/` 最新日報
- [ ] 檢查 `claudedocs/2-sprints/current/` 當前 Sprint 狀態
- [ ] 檢查是否有未完成的任務

### 3. 任務確認
- [ ] 確認本次 Session 的目標
- [ ] 建立 TodoWrite 任務列表
- [ ] 評估任務優先級

---

## 快速啟動命令

### 啟動開發環境
```bash
# 啟動資料庫
docker-compose up -d

# 啟動開發伺服器
npm run dev
```

### 檢查專案狀態
```bash
# Git 狀態
git status && git branch

# 測試狀態
npm run type-check
npm run lint
```

---

## 重要文件路徑

| 文件類型 | 路徑 |
|----------|------|
| 專案指引 | `CLAUDE.md` |
| 技術規格 | `docs/03-stories/tech-specs/` |
| 當前 Sprint | `claudedocs/2-sprints/current/` |
| 日報 | `claudedocs/3-progress/daily/` |
| Bug 記錄 | `claudedocs/4-changes/bug-fixes/` |

---

## Session 命名規範

Session ID 格式：`SESSION-YYYYMMDD-XX`
- `YYYYMMDD`：日期
- `XX`：當日序號（01, 02, ...）

範例：`SESSION-20251221-01`

---

## 注意事項

1. **不要停止 Node.js 進程** - 可能影響 Claude Code 本身
2. **遵循技術規格** - 不要擅自偏離設計
3. **記錄所有變更** - 使用 `claudedocs/4-changes/` 記錄
4. **定期更新進度** - 使用 TodoWrite 追蹤任務

---

*指引版本：1.0*
*最後更新：2025-12-21*
