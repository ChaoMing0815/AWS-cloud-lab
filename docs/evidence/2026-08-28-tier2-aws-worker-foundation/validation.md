# Tier 2 AWS Worker foundation 驗證摘要

- Scope／risk／upstream source：R3 IAM／network／cost；使用者核准兩台private Worker與單一NAT Gateway，Credits回報USD 125.59。
- Baseline：治理基準`0932565`；分支`codex/tier2-aws-worker-foundation`。
- Red commit：`08eee3a`；5項contract因template缺失精確失敗。
- Green commits：`84ad620`新增單一20-resource CloudFormation foundation；corrective Red／Green `bc565a8`／`5b37d7a`要求ASG等待route與route-table association後才啟動Worker。
- Targeted verification：IaC 5 passed；含boundary affected suite共20 passed。
- Negative／sensitivity：public IP false→true、DLQ redrive 3→9、Worker新增`SendMessage`均被對應test攔截，mutation已還原。
- Security：Worker無inbound／public IP／SSH key；Web producer與Worker consumer分權；SSE-SQS與TLS deny；DB只接受Worker SG 5432。
- Cost boundary：2×t4g.micro、2×8 GiB gp3、1 NAT／EIP、2 SQS與CloudWatch；執行前仍需Tokyo estimate與cost ceiling人工核准。
- Rollback：尚未建立AWS資源；首次Change Set預期20 Add、0 Modify／Remove／Replacement。
- Residual risk：同AZ不涵蓋AZ failure；NAT 443 egress尚未收斂為service endpoints；SQS runtime／heartbeat／dual-write reconciliation尚未實作。
- Full regression：corrective後branch tip的Backend 685 tests collected、command exit 0（既有環境型skip）；Frontend 96 passed。
