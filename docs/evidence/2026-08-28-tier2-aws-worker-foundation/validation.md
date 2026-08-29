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

## Worker log ARN corrective validation

- Finding：執行前IAM檢查發現`AWS::Logs::LogGroup.Arn`已含結尾`:*`，template再附加`:*`會產生非canonical`:*:*`。
- Red：`105138c`新增精確contract，因實際`${WorkerLogGroup.Arn}:*`與預期`${WorkerLogGroup.Arn}`不同而失敗。
- Green：`f557d9f`只移除額外wildcard；專屬test 1 passed，Tier 2 Worker IaC suite 6 passed。
- Sensitivity：暫時恢復額外`:*`後專屬test精確失敗；還原後重新通過。
- Full regression：Backend 686 tests collected／exit 0；Frontend 96 passed。
- AWS freeze：既有Change Set使用舊template SHA，不得執行；必須待修正合併後以新exact HEAD與template SHA重建20-Add Change Set，並重做IAM Access Analyzer。

## SQS TLS policy corrective validation

- AWS結果：使用`main` exact HEAD `209a086`與template SHA-256 `0fb878d6277d7d1f17893aa47f1f713e1282b33f2557bf360720ae3779f1630b`建立的20-Add Change Set，在獲得foundation-only、USD 35成本上限與2026-09-08清理日核准後執行；`StoryQueueTlsPolicy`建立失敗，整體stack已安全回復至`ROLLBACK_COMPLETE`。
- Finding：SQS拒絕單一policy statement同時包含兩個Queue resource；錯誤指出每個statement必須恰好一個resource。帳號與request識別資訊未保存。
- Red：`c4a45b6`要求同一個`AWS::SQS::QueuePolicy`保留兩個Queue綁定，但TLS deny拆成兩個statement，且每個statement只指向一個Queue ARN；舊template精確失敗。
- Green：`93878c9`將main queue與DLQ分成兩個TLS deny statements；CloudFormation resource inventory仍為20，未新增服務或權限。
- Targeted verification：專屬test 1 passed；Tier 2 Worker IaC suite 6 passed。
- Sensitivity：暫時將第一個statement還原為雙Queue resource array後，專屬test精確失敗；mutation還原後重新通過。
- Full regression：Backend 686 tests collected／exit 0；Frontend 96 passed。
- AWS freeze：失敗的Change Set不得重試；修正必須先合併至`main`，再以新的exact HEAD與template SHA-256 `71ed3342ff3570bf6d31978580cb8e0fc52f0acff33930146f2bebe3f660a85c`建立全新Change Set。重新執行前仍須確認20 Add／0 Modify／0 Remove／0 Replacement、property-level diff及IAM Access Analyzer無新增finding。
