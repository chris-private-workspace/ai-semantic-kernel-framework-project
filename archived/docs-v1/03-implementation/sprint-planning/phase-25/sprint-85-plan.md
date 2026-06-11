# Sprint 85: Worker 容器化與 K8s 部署

## Sprint Info

| Field | Value |
|-------|-------|
| **Sprint Number** | 85 |
| **Phase** | 25 - 生產環境擴展 |
| **Duration** | 5-7 days |
| **Story Points** | 20 pts |
| **Status** | 計劃中 |
| **Priority** | 🔵 P3 視需求 |

---

## Sprint Goal

實現 Worker 容器化和 Kubernetes 部署，配置 HPA 自動擴展。

---

## Prerequisites

- Phase 21-24 完成 ✅
- Azure Kubernetes Service (AKS) 準備就緒
- Azure Container Registry (ACR) 準備就緒

---

## User Stories

### S85-1: Worker 容器化 + 沙箱增強 (12 pts)

**Description**: 優化 Dockerfile，實現多階段構建、安全加固，並在容器級增強沙箱能力。

**Acceptance Criteria**:
- [ ] 多階段構建優化鏡像大小
- [ ] 非 root 用戶運行
- [ ] 安全掃描通過（Trivy）
- [ ] 健康檢查端點
- [ ] 容器級沙箱目錄隔離

**Files to Create**:
- `backend/Dockerfile` (~80 行)
- `backend/Dockerfile.worker` (~60 行)
- `frontend/Dockerfile` (~50 行)
- `.dockerignore`

**Technical Design**:

**backend/Dockerfile**:
```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# 安全加固
RUN useradd -m -s /bin/bash appuser

# 複製依賴
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

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

---

### S85-2: Kubernetes 部署 (Helm) (8 pts)

**Description**: 創建 Helm Chart，實現完整 K8s 部署。

**Acceptance Criteria**:
- [ ] Helm Chart 結構完整
- [ ] 支援多環境（dev/staging/prod）
- [ ] ConfigMap/Secret 管理
- [ ] Service/Ingress 配置
- [ ] HPA 自動擴展

**Files to Create**:
```
helm/ipa-platform/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   └── _helpers.tpl
```

**Technical Design**:

**helm/ipa-platform/templates/hpa.yaml**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "ipa-platform.fullname" . }}-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "ipa-platform.fullname" . }}-backend
  minReplicas: {{ .Values.backend.hpa.minReplicas }}
  maxReplicas: {{ .Values.backend.hpa.maxReplicas }}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ .Values.backend.hpa.targetCPU }}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: {{ .Values.backend.hpa.targetMemory }}
```

**helm/ipa-platform/values.yaml**:
```yaml
backend:
  replicas: 2
  image:
    repository: your-acr.azurecr.io/ipa-backend
    tag: latest
  resources:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 2000m
      memory: 2Gi
  hpa:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPU: 70
    targetMemory: 80

frontend:
  replicas: 2
  image:
    repository: your-acr.azurecr.io/ipa-frontend
    tag: latest

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: ipa.example.com
      paths:
        - path: /
          pathType: Prefix
```

---

## Deployment Architecture

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
│  │   │ Frontend Pod    │   │ Redis Pod       │                               │    │
│  │   │ (Nginx)         │   │ (Cache)         │                               │    │
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

## Definition of Done

- [ ] 所有 Stories 完成
- [ ] Docker 鏡像成功構建
- [ ] K8s 部署成功運行 2+ 副本
- [ ] HPA 在負載增加時自動擴展
- [ ] 沙箱在容器內正確工作
- [ ] 安全掃描無 Critical/High 漏洞

---

## Success Metrics

| Metric | Target |
|--------|--------|
| 鏡像構建時間 | < 5 分鐘 |
| 部署滾動更新 | 零停機 |
| HPA 擴展響應時間 | < 2 分鐘 |
| 容器啟動時間 | < 30 秒 |

---

**Created**: 2026-01-12
**Story Points**: 20 pts
