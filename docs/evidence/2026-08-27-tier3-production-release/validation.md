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

## ARM64 exact-digest scan corrective TDD

- 共同治理基準：`a1ef10bf98b63e274d7585e412132d03278a5cc2`
- Red commit：`84a0e61a47fe1ac54ddc7be1a5e701d8b8450be8`
- Green commit：`275a0d4b4b27baa3d5e34f2334f1357256b014da`
- Red：新增workflow contract後，targeted test只因exact-digest scan step缺少`TRIVY_PLATFORM=linux/arm64`而失敗；沒有把本機初始缺少PyYAML的收集錯誤視為Red。
- Green：只在`Scan the exact pushed digest`step增加`env.TRIVY_PLATFORM: linux/arm64`；仍掃描build output的exact pushed digest，並保留`aquasecurity/trivy-action@v0.36.0`、Trivy `v0.70.0`、`CRITICAL,HIGH`、`ignore-unfixed: true`與`exit-code: 1`。
- 代表性sensitivity：暫時移除該scan step的platform env後，同一targeted test如預期因`None != linux/arm64`失敗；恢復後通過。

### 官方語意核對

- [Trivy container image官方文件](https://github.com/aquasecurity/trivy/blob/main/docs/guide/target/container_image.md#scan-image-on-a-specific-architecture-and-os)說明預設會依`linux/amd64`解析image，並以`--platform=os/architecture`選擇目標platform。
- [Trivy官方環境變數規則](https://trivy.dev/docs/v0.69/guide/configuration/#environment-variables)說明CLI flag加`TRIVY_`前綴、轉大寫並將連字號換成底線；因此`--platform`的對應值為`TRIVY_PLATFORM`。
- [trivy-action v0.36.0官方README](https://github.com/aquasecurity/trivy-action/blob/v0.36.0/README.md#environment-variables)明示支援在action step使用Trivy environment variables傳入沒有action input的flags；該release的官方說明亦綁定Trivy `v0.70.0`。

### Repo-local驗證

- YAML parse：`.github/workflows/ci.yml`與`.github/workflows/tier3-release.yml`均通過。
- Targeted／Tier 3 affected：`47 passed`。
- Backend regression：`440 passed, 8 skipped`。
- Frontend regression：`94 passed`。
- `git diff --check`與branch boundary需在evidence commit後以相同治理基準做最終核對。

此修正只是repo-local fail-closed修正，不是production deploy核准。舊run `33030554303`不得re-run；PR／CI／merge完成後，必須以新的exact `main` SHA重新形成並人工核准T3B envelope。
