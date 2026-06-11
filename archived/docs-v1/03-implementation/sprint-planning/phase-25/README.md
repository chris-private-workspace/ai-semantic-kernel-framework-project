# Phase 25: 生產環境擴展

## Overview

Phase 25 專注於為生產環境準備 Kubernetes 部署和水平擴展能力，實現 Worker 容器化、HPA 自動擴展、完整監控和災難恢復。

## Phase Status

| Status | Value |
|--------|-------|
| **Phase Status** | 計劃中 |
| **Duration** | 2 sprints |
| **Total Story Points** | 40 pts |
| **Priority** | 🔵 P3 視需求 |
| **Target Start** | Phase 24 完成後 (視業務需求) |

## Sprint Overview

| Sprint | Focus | Story Points | Status | Documents |
|--------|-------|--------------|--------|-----------|
| **Sprint 85** | Worker 容器化與 K8s 部署 | 20 pts | 計劃中 | [Plan](sprint-85-plan.md) / [Checklist](sprint-85-checklist.md) |
| **Sprint 86** | 監控增強與災難恢復 | 20 pts | 計劃中 | [Plan](sprint-86-plan.md) / [Checklist](sprint-86-checklist.md) |
| **Total** | | **40 pts** | | |

---

## 問題背景

### 現狀

1. **App Service 部署限制**
   - 單實例部署，無水平擴展
   - 資源限制固定
   - 部署更新需要停機

2. **監控能力不足**
   - 基礎 Azure Monitor
   - 缺少自定義指標
   - 告警規則有限

3. **災難恢復不完善**
   - 備份策略手動
   - 無自動恢復機制
   - RTO 不明確

### 目標

- 實現 Kubernetes 部署和自動擴展
- 建立完整的 Prometheus + Grafana 監控
- 實現自動化災難恢復

---

## Architecture

### Kubernetes 部署架構

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         Azure Kubernetes Service (AKS)                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │                        IPA Platform Namespace                                │    │
│  │                                                                             │    │
│  │   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐         │    │
│  │   │ Backend Pod 1   │   │ Backend Pod 2   │   │ Backend Pod N   │         │    │
│  │   │ (FastAPI)       │   │ (FastAPI)       │   │ (FastAPI)       │         │    │
│  │   │ + Sandbox       │   │ + Sandbox       │   │ + Sandbox       │         │    │
│  │   └─────────────────┘   └─────────────────┘   └─────────────────┘         │    │
│  │                         ↑                                                   │    │
│  │                    HPA (CPU/Memory/Custom)                                  │    │
│  │                                                                             │    │
│  │   ┌─────────────────┐   ┌─────────────────┐                               │    │
│  │   │ Frontend Pod    │   │ Prometheus      │                               │    │
│  │   │ (Nginx)         │   │ + Grafana       │                               │    │
│  │   └─────────────────┘   └─────────────────┘                               │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
│  External Services:                                                                  │
│  - Azure PostgreSQL (Managed)                                                        │
│  - Azure Redis Cache (Managed)                                                       │
│  - Azure Blob Storage (Backup)                                                       │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Features

### Sprint 85: Worker 容器化與 K8s 部署 (20 pts)

| Story | Description | Points | Priority |
|-------|-------------|--------|----------|
| S85-1 | Worker 容器化 + 沙箱增強 | 12 pts | P3 |
| S85-2 | Kubernetes 部署 (Helm) | 8 pts | P3 |

### Sprint 86: 監控增強與災難恢復 (20 pts)

| Story | Description | Points | Priority |
|-------|-------------|--------|----------|
| S86-1 | Prometheus + Grafana 監控 | 10 pts | P3 |
| S86-2 | 災難恢復 + 自動備份 | 10 pts | P3 |

---

## Technical Details

### Dockerfile (沙箱增強)

```dockerfile
FROM python:3.11-slim

# 安全加固
RUN useradd -m -s /bin/bash appuser

# 安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製代碼
COPY --chown=appuser:appuser . /app
WORKDIR /app

# 沙箱目錄
RUN mkdir -p /data/sandbox && chown appuser:appuser /data/sandbox

# 以非 root 用戶運行
USER appuser

# 健康檢查
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Helm Chart 結構

```
helm/ipa-platform/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   ├── configmap.yaml
│   └── secrets.yaml
```

### HPA 配置

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ipa-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ipa-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Dependencies

### Prerequisites
- Phase 21-24 completed
- Azure Kubernetes Service (AKS)
- Azure Container Registry (ACR)
- Helm 3.x

### New Dependencies
```bash
# 安裝 Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 安裝 kubectl
az aks install-cli
```

---

## Verification

### Sprint 85 驗證
- [ ] Docker 鏡像成功構建
- [ ] K8s 部署成功運行 2+ 副本
- [ ] HPA 在負載增加時自動擴展
- [ ] 沙箱在容器內正確工作

### Sprint 86 驗證
- [ ] Prometheus 收集所有指標
- [ ] Grafana 儀表板顯示正確
- [ ] 備份按計劃執行
- [ ] 災難恢復 RTO < 4 小時

---

## Success Metrics

| Metric | Target |
|--------|--------|
| K8s 部署可用性 | > 99.9% |
| HPA 擴展響應時間 | < 2 分鐘 |
| 監控指標覆蓋率 | 100% |
| 災難恢復 RTO | < 4 小時 |
| 災難恢復 RPO | < 1 小時 |

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| K8s 學習曲線陡峭 | High | High | 階段性培訓，App Service 作為備選 |
| 容器資源不足 | Medium | Medium | 資源監控 + 預警 |
| 數據庫故障 | High | Low | 多區域部署 + 自動故障轉移 |
| 監控告警氾濫 | Medium | Medium | 閾值調整 + 分級告警 |

---

**Created**: 2026-01-12
**Total Story Points**: 40 pts
