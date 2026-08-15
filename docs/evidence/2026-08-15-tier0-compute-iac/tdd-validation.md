# Tier 0 EC2＋SSM IaC 驗證摘要

- Scope／risk：R3；public compute、EC2 application role、SSM management plane、public IPv4 固定計費面與 teardown boundary。
- Red：`backend/tests/test_tier0_compute_template.py` 的 5 項 tests 因 `infra/cloudformation/tier0-compute.yaml` 尚未存在而預期失敗。
- Green：template 只含 `AWS::IAM::Role`、`AWS::IAM::InstanceProfile` 與 `AWS::EC2::Instance`。
- Compute：Amazon Linux 2023 ARM64 public SSM AMI parameter、`t4g.micro`、CPU credits standard、8 GiB encrypted gp3、detailed monitoring disabled。
- Network：使用既有 public app subnet 與 App SG、自動 public IPv4；不建立 EIP、NAT、ALB 或新 SG。
- IAM／management：role trust only EC2、`PowerUserAccess` permissions boundary、實際只掛 `AmazonSSMManagedInstanceCore`；沒有 inline policy、secret、Bedrock 或 CloudWatch 權限。
- Host boundary：IMDSv2 required、hop limit 1、metadata tags disabled；沒有 Key Pair、UserData、SSH、runtime environment 或 application deployment。
- Targeted：compute＋network＋IAM contracts `13 passed`。
- Full regression：Backend `257 passed, 8 skipped`；Frontend 未受影響，沿用 `80 passed`。
- Sensitivity：暫時加入 `KeyName` 後 no-SSH contract 如預期失敗；已還原並重新全綠。
- Cost／rollback：EC2＋8 GiB gp3＋1 個 public IPv4 credits burn 上限 `US$20/month`；刪除 stack 會 terminate instance、刪除 root EBS、釋放自動 public IPv4並刪除 role／profile。
- AWS：尚未建立 change set 或任何 Batch 3 resource；全程未使用 AWS CLI。
