# UI／像素 Support Widget production release與HTTPS恢復

- Scope／risk：R2玩家可見UI與bounded Support Widget release；Direct IP憑證恢復涉及production TLS，依使用者核准的bounded recovery執行。未建立AWS資源、未變更IAM、RDS、SQS、Publisher、Worker、Bedrock或Support Agent安全邊界。
- Exact source：`main`／`origin/main`／release source均為`1297a6acabaf30ca4ec2205e7641b7ab83cef781`；application code包含`Release v1.1.0`、同源`co-story-mark.svg`、終端敘事視覺與像素Support Widget。
- CI：run `33493821544`的Frontend、Backend、container build與HIGH／CRITICAL scan全部成功；branch boundary在`main`依設計skip。
- Release：workflow run `33494151458`以`digest-release`完成approval、exact source checkout、ARM64 immutable image、target／previous digest fence、Trivy與bounded SSM release；SSM回`Success`／response `0`。Active Web由`sha256:f9cc0e650231096cc6a14de1997181601558314195ad6ca31319ad62eb1abdd4`切換為`sha256:5a10597d473cd21c5b2754b743f4a48de2be7cae9bd0c1816c535523284df9bd`，runtime維持`async`；Publisher與兩台Worker digest未變。
- Delivery metrics：artifact schema `1`、`verified=true`、method `automatic`；end-to-end `183s`、build and scan `135s`、SSM release attempt `27s`、human interaction count `2`。
- Production UI：嚴格TLS恢復後，Browser確認首頁title正確、`Release v1.1.0`可見、品牌SVG載入完成且transform為`none`、Widget toggle可見；Esc關閉後focus回`supportWidgetToggle`。390×844下nav／toggle與dialog／composer均不重疊，首頁與demo無水平溢位，console error／warning為`0`。
- Support邊界：Widget只包裝既有cited／unsupported rules lookup與Player-only `local_draft_only`草稿；沒有Bedrock、RAG、MCP、external submit或自由對話模型。完整`/support`頁仍保留。
- HTTPS事故：release workflow成功後的公開Browser smoke發現既有Direct IP憑證已過期。憑證renewal timer持續active，但自2026-08-28起ACME `http-01`均因公開token回`404`失敗；失敗早於本次UI release，因此不是新Web image造成。
- 根因：Certbot可在`/var/lib/co-story/acme/.well-known/acme-challenge`建立token，Nginx mount namespace亦可見；但父目錄`/var/lib/co-story`為`root:co-story 0750`，Nginx worker的`stat()`回`Permission denied`並對外表現為`404`。SELinux為`Permissive`，port 80與ACME location均正常。
- Recovery：production只加入POSIX ACL `user:nginx:--x`，不授予目錄list、read或write；loopback與外部probe均精確`200`。同一`co-story-certbot-renew.service`隨後`Result=success`／`ExecMainStatus=0`，Nginx config test與reload成功；新憑證有效至2026-09-08，外部strict TLS首頁、`/api/v1/live`、`/api/v1/ready`均為`200`。
- Rollback／residual：ACL可用`setfacl -x u:nginx /var/lib/co-story`精確移除，但在憑證仍依賴此webroot時不得回退。尚未以strict TDD將ACL前置、公開challenge probe、憑證到期與renewal failure gate固化到repo；下一次timer自動renew尚未觀察。不要手動重複renew，先完成repo防回歸或等待下一個受控觀察點。
