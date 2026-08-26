# Tier 3 delivery foundation

- 狀態：Repo-local foundation；尚未部署 AWS
- 範圍：current monolith 的 Docker、ECR、GitHub OIDC、CI build／scan、SSM release、readiness 與 rollback
- 非範圍：產品行為、Storyteller、Web UI、Tier 2 拆分

## 固定 runtime contract

映像使用 Python 3.13、UID／GID `10001:10001`、單一 Uvicorn worker，並保留 `/api/v1/live`、`/api/v1/ready` 與 port `8000`。正式主機以 host network 綁定 `127.0.0.1:8000`，既有 Nginx 仍是唯一 public edge。

映像不包含 runtime env、RDS URL、Bedrock Guardrail ID 或 credential。`/etc/co-story/runtime.env`、`/etc/co-story/database.env` 與 `/var/log/co-story` 由主機在啟動時注入；CloudWatch 既有 safe JSONL 路徑因此不變。

## Delivery flow

```mermaid
flowchart LR
    PR[Pull request / main push] --> Tests[Backend + Frontend tests]
    Tests --> Build[Container build]
    Build --> Scan[Trivy HIGH / CRITICAL gate]
    Manual[workflow_dispatch] --> Approval[production environment approval]
    Approval --> OIDC[Main-only GitHub OIDC]
    OIDC --> ECR[Immutable ECR digest]
    ECR --> SSM[Bounded SSM document]
    SSM --> Candidate[Migration + candidate :8001]
    Candidate --> Health[/live + /ready]
    Health --> Active[Loopback :8000 behind Nginx]
    Health -->|failure| Previous[Previous digest rollback]
```

CI 沒有 `id-token: write`、AWS action 或 deploy 權限。Release workflow 必須來自 `main`，先通過 GitHub `production` environment 的 required reviewer，再取得短期 OIDC credential。Trust subject 固定為 `repo:ChaoMing0815/AWS-cloud-lab:ref:refs/heads/main`。

現有 EC2 是 `t4g` ARM64，因此 production release 以 QEMU／Buildx 明確建立 `linux/arm64` image；不得把 hosted runner 預設的 AMD64 image 當成可部署 artifact。

## Rollback boundary

Release 只接受 `sha256:<64 hex>` target 與 previous digest。首次容器切換先以 previous digest 取代原生 systemd runtime並通過 `/live`、`/ready`，才遷移與驗證 candidate。正式 target restart 或 health gate 失敗時，release script 原子改回 previous digest；不做 schema downgrade，因此 migration 必須維持 backward compatibility。
