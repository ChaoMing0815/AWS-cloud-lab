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

## AWS foundation deployment

- Merge／template：PR #36的SQS TLS修正已合併；執行基準為`main` exact HEAD `90677f8c31fd587e957675000fc413e747b17f9c`，template SHA-256為`71ed3342ff3570bf6d31978580cb8e0fc52f0acff33930146f2bebe3f660a85c`。
- Preflight stop：首次重建的Change Set property diff仍顯示舊版單一TLS statement／雙Queue resource；在執行前停止並刪除，沒有建立AWS resource或產生該批費用。以exact workspace template重新上傳後，`StoryQueueTlsPolicy`顯示兩個statement且每個只有一個Queue resource。
- Approved envelope：Change Set `tier2-worker-foundation-add20-90677f8-20260829-r3`為20 Add／0 Modify／0 Remove／0 Replacement；成本上限USD 35、清理日2026-09-08，只建立foundation，不部署Worker image、不啟用async。
- CloudFormation：stack `co-story-tier2-worker-foundation`為`CREATE_COMPLETE`，20／20 resources均為`CREATE_COMPLETE`。
- Compute／storage：ASG min／desired／max為2／2／2；兩台`t4g.micro`均running／healthy、無public IPv4、無Key Pair、IMDSv2 required；兩顆root volume均為8 GiB encrypted gp3且in-use。
- SSM／bootstrap：兩台managed node online。第一次Run Command誤選PowerShell document，因Linux無`/usr/bin/pwsh`而立即失敗且未修改instance；改用`AWS-RunShellScript`後兩台均`Success`，Docker為`active`且`docker ps`只有header，沒有Worker container。
- Messaging／observability：主Queue與DLQ的available／in-flight均為0；部署後TLS policy含兩個預期Sid；DLQ alarm為`OK`且actions disabled。
- Network：Worker SG無inbound；egress為HTTPS 443、指向既有DB SG的PostgreSQL 5432，以及抑制AWS預設allow-all的localhost sink `127.0.0.1/32`。DB SG只新增來源為Worker SG的TCP 5432，未使用CIDR。
- Effective IAM：Worker role對主Queue `ReceiveMessage`為Allowed；主Queue `SendMessage`、DLQ `ReceiveMessage`、廣泛／非授權secret與`iam:PassRole`均Denied。既有Web role對主Queue `SendMessage`為Allowed，`ReceiveMessage`／`DeleteMessage`均Denied。
- Validation process：IAM JSON在本次修正前後未變；Console自動finding再次顯示Security／Errors／Warnings／Suggestions均為0。後續若policy document與resolved resource scope未變，沿用已記錄結果，不再要求重貼相同JSON；只有IAM內容或scope改變才重驗。
- Runtime boundary：production active release與Web runtime仍維持精確`sync`；本批沒有pull／run Worker image、沒有傳送SQS message、沒有Bedrock呼叫或async activation。
