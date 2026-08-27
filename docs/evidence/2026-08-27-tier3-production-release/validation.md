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

## 第二次 T3B fail-closed 與 corrective TDD

- 第二次run：`33032162034`
- Source：`d81e4d7313d42bdec503305d588e782d6272c8f9`
- ARM64 build／immutable push／exact-digest Trivy：通過。
- Release step：失敗。SSM command已送達一個target；`ReleaseCoStoryContainer`在migration回傳nonzero。
- Root cause 1：container內缺少host PostgreSQL `verify-full`指定的`/etc/pki/rds/rds-ca.pem`，migration以TLS錯誤fail closed，且發生在candidate與任何unit／state mutation前。
- Root cause 2：repository variable `TIER3_INSTANCE_ID`含前置Tab／換行；send-command targets曾接受該表示法，但wait／get的instance-id validation失敗。Workflow不能依賴AWS CLI子命令對同一raw值有一致解析。
- 同一SHA的immutable tag已存在，因此不得re-run舊run或改以手動SSM繞過。

### Production postflight

使用者透過唯讀postflight確認legacy仍安全：application active、container service inactive、active release仍為`tier1-20260825-4a51e0e`，installed legacy unit吻合release；release env、transition state、legacy backup與stable assets均不存在，target／candidate container未執行，legacy live／ready均為`200`。Host CA為regular、非symlink、`root:root:644`、app可讀且無不安全write bit。未記錄instance ID、account、ARN、IP或secret。

### Repo-local strict TDD

- Base：`d81e4d7313d42bdec503305d588e782d6272c8f9`
- Red commit：`020fd34449ebea7e91402177828aad04831ea610`
- Green commit：`e7ae5d136ddbd48521fd66d0ef2bcd6ee7c58a7a`
- Red：targeted tests新增canonical target、Document／driver CA guard、image空mountpoint，以及migration／candidate／stable container readonly mount contract；在實作前共有19個預期失敗，全部源自缺少這些行為。
- Green：workflow在credentials／build前只接受`^i-[0-9a-f]{17}$`，不trim raw值，並讓send／wait／get只使用同一validated env。Final image只建立root-owned空目錄，不含CA。Document在第一次login／pull前、driver在common preflight驗證host CA；三個container路徑都readonly bind mount相同absolute path。TLS `verify-full`、release順序、rollback、IAM／OIDC／scan gate均未放寬。
- CloudFormation scope：相對base只有`ContainerReleaseDocument.Properties.Content`不同；`UpdateMethod`仍為`NewVersion`。`LegacyRollbackDocument`、IAM role／policy、OIDC、ECR與AppRole attachment均不變。

### Negative、rollback 與 sensitivity

- Canonical target negative涵蓋前後空白／換行／CRLF、short ID與uppercase；raw repository variable在workflow只出現於validation step。
- CA negative涵蓋missing、symlink、非root owner/group、不安全group／other writable，以及app不可讀；全部在pull／migration前nonzero。
- 既有migration fail、candidate fail、mutation restore、digest rollback與manual legacy rollback suites持續通過；本修正沒有改動rollback順序或state contract。
- Sensitivity 1：暫時把regex放寬為`^i-.*$`，五組不合規ID立即造成測試失敗；恢復後通過。
- Sensitivity 2：暫時移除driver common CA guard，七組不安全CA案例均被測試捕捉；恢復後通過。

### 驗證摘要

- Targeted／Tier 3 affected：`63 passed`。
- Backend regression：全數通過，`8 skipped`為既有optional案例。
- Frontend regression：`94 passed`。
- YAML／CloudFormation parse、`bash -n`與template scope comparison：通過。
- 本機ARM64 image build：通過；image為`linux/arm64`、runtime user `10001:10001`，root-owned mountpoint為`root:root:755`且image內沒有CA；application import通過。因本機無production runtime／database env，不把這次檢查宣稱為production health。
- 本機沒有Trivy executable，因此未另做local scan；既有PR CI的exact ARM64 digest、`HIGH,CRITICAL`、`ignore-unfixed`與`exit-code: 1` gate仍是必要merge條件。
- `git diff --check`與branch boundary將在此evidence commit後做最終核對。

這批修正不是production deploy核准。合併後必須先套用只更新release Document新版本的bounded Change Set、由使用者把repository variable改成canonical exact值，再以新的exact `main` SHA形成並明確核准新的T3B envelope。Run `33030554303`與`33032162034`都不得re-run。
