# Tier 2 Worker foundation Console runbook

- 狀態：Draft；未核准任何Change Set執行
- 操作方式：AWS Console first；使用者是唯一AWS寫入者
- Template：`infra/cloudformation/tier2-worker-foundation.yaml`
- 建議stack：`co-story-tier2-worker-foundation`

## 成本關卡

建立Change Set前，在AWS Pricing Calculator選`ap-northeast-1`，至少納入：

- `2 × t4g.micro`執行至預定清理日
- `2 × 8 GiB gp3`
- `1 × NAT Gateway`時數與預估處理流量
- `1 × public IPv4`
- SQS request、CloudWatch Logs與data transfer的保守估計

記錄增量估價與清理日期。若估價超過本次另行核准的cost ceiling、Credits狀態改變或需要增加第二個NAT／更多compute，停止並回整合task。

## 參數來源

只從既有stack Outputs／Parameters與Console可見resource ARN取得，不輸出secret value：

| Parameter | Source |
| --- | --- |
| `VpcId` | `co-story-tier0-network` Output |
| `PublicAppSubnetId` | `co-story-tier0-network` Output |
| `DbSecurityGroupId` | `co-story-tier0-network` Output |
| `AppRoleName` | 固定`AWSFinalProjectAppRole` |
| `PrivateWorkerSubnetCidr` | 固定`10.20.20.0/24`；先確認VPC無重疊 |
| `Tier3RepositoryArn` | `co-story-tier3-delivery` repository Output／ECR Console ARN |
| `RuntimeSecretArn` | 既有runtime secret ARN；不得讀取或貼出secret value |
| `BedrockModelId` | 固定`amazon.nova-lite-v1:0` |
| `BedrockGuardrailId／Version` | 既有Tier 0 production參數；不輸出Guardrail內容 |

建立Change Set時必須勾選`I acknowledge that AWS CloudFormation might create IAM resources with custom names`，因template建立固定名稱的Worker role、instance profile與Web producer managed policy。

## 預期Change Set

首次Change Set必須恰好是20個`Add`，不應出現既有resource的`Modify`、`Remove`或Replacement：

- Network：1 subnet、1 EIP、1 NAT Gateway、1 route table、1 default route、1 association
- SG：1 Worker SG、2 egress、1 DB ingress
- Queue：2 SQS queues、1 QueuePolicy
- IAM：1 Worker role、1 instance profile、1 Web producer managed policy
- Compute：1 launch template、1 ASG（desired=2）
- Observability：1 log group、1 DLQ alarm

若數量、action或resource type不同，或出現ALB、ECS、EKS、Lambda、KMS key、RDS、第二個NAT，立即停止，不執行Change Set。

## 執行前安全檢查

1. Template／Git commit SHA與本runbook envelope一致。
2. 新增或變更IAM policy document／resolved resource scope時，IAM Access Analyzer Console自動finding的Security／Errors／Warnings／Suggestions均為0，或所有finding已停止並回報。若內容與scope相對已記錄證據未變，沿用既有結果，不重貼相同JSON。
3. Worker trust只含`ec2.amazonaws.com`；permissions boundary為`PowerUserAccess`。
4. Web policy只附加`AWSFinalProjectAppRole`；Worker role不附加到Web instance。
5. Worker無public IP、無KeyName、SG無inbound；DB ingress source為Worker SG而非CIDR。
6. Queue與DLQ均為SSE-SQS；TLS deny、visibility 180秒、redrive 3次。
7. Stack deletion rollback與Demo後清理owner已確認。

## 執行後第一批驗證

本批只驗證foundation，不部署application image：

- Stack `CREATE_COMPLETE`且20項resource完成。
- ASG desired／in-service均為2；兩台EC2無public IPv4、IMDSv2 required。
- 兩台SSM managed node online；不得開SSH或建立Key Pair。
- Docker service active，尚無`co-story-worker` container。
- 主Queue／DLQ為空、TLS policy存在、DLQ alarm初始`OK`且`Actions: No actions`。
- Worker role的正面模擬允許指定Queue receive，負面模擬拒絕`SendMessage`、其他Queue、其他secret、`iam:PassRole`。
- Web role正面模擬允許指定Queue send，負面模擬拒絕receive／delete。
- DB SG只新增Worker SG `5432`；RDS仍`Public access=No`。
- Worker SG無inbound；egress恰好為HTTPS `443`、目的DB SG `5432`，以及抑制AWS預設allow-all的localhost sink `127.0.0.1/32`。

完成上述驗證前，不進行SQS runtime或async activation。

## Rollback／清理

- Change Set未執行：刪除Change Set，不產生費用。
- Stack建立失敗：讓CloudFormation rollback；不要手動保留NAT、EIP或ASG orphan。
- Foundation尚未承載message時：刪除整個stack，確認ASG instances、volumes、NAT Gateway、EIP、queues與log group均已刪除。
- Runtime啟用後不得直接刪stack；必須先停止Web producer、確認主Queue／DLQ／DB job狀態，再走獨立drain與rollback envelope。
