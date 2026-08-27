# Tier 3 T3B 首次 production workflow 驗證

- 日期：2026-08-27
- 結果：Fail closed；production deployment未執行
- GitHub Actions run：`33030554303`
- Approved source：`0add833c10414b1b51cb4733b12b669bdb04f85b`
- Release mode：`legacy-bootstrap`

## 已完成前置

- CloudFormation stack更新為`UPDATE_COMPLETE`：release Document建立新版本，新增獨立legacy rollback Document；沒有IAM／OIDC／ECR replacement。
- Production host bounded Docker bootstrap通過：Amazon Linux 2023、aarch64、Docker active、初始container inventory空白，legacy live／ready均為`200`。
- GitHub `production` environment設定required reviewer、只允許`main`且禁止administrator bypass。
- 四項repository variables已建立；沒有長期AWS access key、secret key或session token。

## Workflow結果

成功步驟：

- approval gate
- OIDC bounded credentials
- ECR login
- ARM64 emulation／Buildx
- immutable commit image build與push

失敗步驟：

- `Scan the exact pushed digest`
- Trivy版本：`v0.70.0`
- 原因：GitHub runner為amd64，而pushed image只含`linux/arm64`；scan未明確指定platform，因此remote resolver尋找`linux/amd64` child並停止。
- 這是artifact/platform解析失敗，不能解讀為「掃描發現零漏洞」或「映像已通過安全gate」。

明確未執行：

- `Release exact digest through bounded SSM document`：`skipped`
- migration
- candidate container啟動與health gate
- production target切換
- public edge post-release驗證

## 安全結論與停止條件

- Production active release維持`tier1-20260825-4a51e0e`；本run未送出SSM release。
- ECR已留下本run推送的ARM64 image，會產生少量storage／scan成本，但不可視為可部署artifact。
- 不得re-run run `33030554303`，不得手動執行SSM release Document。
- 修正必須維持exact pushed digest、`HIGH,CRITICAL`、`ignore-unfixed`與`exit-code: 1`，不得使用VEX、skip、ignorefile或降低severity。
- 修正經Red／Green、PR、CI與merge後，必須以新的exact `main` SHA重新建立並人工核准T3B envelope。

GitHub run：[Tier 3 container release #1](https://github.com/ChaoMing0815/AWS-cloud-lab/actions/runs/33030554303)
