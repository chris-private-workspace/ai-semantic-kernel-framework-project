# Sprint 85 Checklist: Worker 容器化與 K8s 部署

## Sprint Status

| Metric | Value |
|--------|-------|
| **Total Stories** | 2 |
| **Total Points** | 20 pts |
| **Completed** | 0 |
| **In Progress** | 0 |
| **Status** | 計劃中 |

---

## Stories

### S85-1: Worker 容器化 + 沙箱增強 (12 pts)

**Status**: ⬜ 待開始

**Tasks**:
- [ ] 創建 `backend/Dockerfile`
  - [ ] 多階段構建配置
  - [ ] 非 root 用戶設置
  - [ ] 沙箱目錄創建
  - [ ] 健康檢查配置
- [ ] 創建 `backend/Dockerfile.worker`
  - [ ] Worker 專用配置
  - [ ] 資源限制設置
- [ ] 創建 `frontend/Dockerfile`
  - [ ] Nginx 配置
  - [ ] 靜態資源優化
- [ ] 創建 `.dockerignore`
- [ ] 執行安全掃描（Trivy）
  - [ ] 修復 Critical 漏洞
  - [ ] 修復 High 漏洞
- [ ] 測試本地構建
- [ ] 測試沙箱在容器內工作

**Acceptance Criteria**:
- [ ] 多階段構建優化鏡像大小
- [ ] 非 root 用戶運行
- [ ] 安全掃描通過
- [ ] 健康檢查端點
- [ ] 沙箱正確隔離

---

### S85-2: Kubernetes 部署 (8 pts)

**Status**: ⬜ 待開始

**Tasks**:
- [ ] 創建 Helm Chart 目錄結構
- [ ] 創建 `Chart.yaml`
- [ ] 創建 `values.yaml`
  - [ ] Backend 配置
  - [ ] Frontend 配置
  - [ ] Ingress 配置
  - [ ] HPA 配置
- [ ] 創建 `values-dev.yaml`
- [ ] 創建 `values-prod.yaml`
- [ ] 創建 Templates
  - [ ] `deployment.yaml`
  - [ ] `service.yaml`
  - [ ] `ingress.yaml`
  - [ ] `hpa.yaml`
  - [ ] `configmap.yaml`
  - [ ] `secrets.yaml`
  - [ ] `_helpers.tpl`
- [ ] 測試 `helm lint`
- [ ] 測試 `helm template`
- [ ] 測試 `helm install --dry-run`
- [ ] 部署到 Dev 環境
- [ ] 驗證 HPA 自動擴展

**Acceptance Criteria**:
- [ ] Helm Chart 完整
- [ ] 多環境支援
- [ ] ConfigMap/Secret 管理
- [ ] Service/Ingress 配置
- [ ] HPA 自動擴展

---

## Verification Checklist

### Docker Tests
- [ ] 鏡像構建成功
- [ ] 容器啟動正常
- [ ] 健康檢查通過
- [ ] 沙箱目錄隔離

### Kubernetes Tests
- [ ] Helm lint 通過
- [ ] 部署到 AKS 成功
- [ ] Service 可訪問
- [ ] Ingress 路由正確
- [ ] HPA 觸發擴展

### Security Tests
- [ ] Trivy 掃描通過
- [ ] 無 Critical 漏洞
- [ ] 無 High 漏洞
- [ ] 非 root 運行確認

---

**Last Updated**: 2026-01-12
