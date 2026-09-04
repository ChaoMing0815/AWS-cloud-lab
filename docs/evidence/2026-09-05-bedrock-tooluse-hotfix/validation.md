# Nova Lite ToolUse Hotfix 驗證摘要

- Scope／risk／source：R2；production CloudTrail確認四筆Nova Lite `Converse` forced ToolUse `ModelErrorException`。
- Boundary：只調整Bedrock adapter、production token validation、Worker replacement runtime contract與對應測試；不修改Web、版號、DB、IAM、Queue或workflow。
- Baseline：Bedrock adapter＋production Worker targeted suite全綠；infrastructure suite因本機起始Python缺PyYAML，改用`/private/tmp`隔離venv執行。
- Red commits：`70d10e3`、`1113e44`；缺少`topK=1`及拒絕`3000` token budget時，targeted測試如預期失敗。
- Green commit：`e66877b`；Nova forced-tool request加入`topK=1`，bounded max／runtime contract對齊`3000`。
- Targeted verification：Bedrock、production Worker、production composition與Worker CloudFormation共`143`項通過。
- Full regression：Backend `863`項收集並全數完成；環境型tests維持既有skip，只有既有Starlette `httpx` deprecation warning。
- UI coexistence：完整Frontend `130/130`通過；branch沿用已含`Release v1.1.3`的exact main base，diff沒有`web/**`。
- Negative：非Nova／無tool request不含`additionalModelRequestFields`；`3001`仍fail closed；raw `ModelErrorException`訊息不外洩。
- Sensitivity：暫時把`topK`改為`2`時新增contract test如預期失敗；還原`1`後targeted重新通過。
- Governance／integration：PR #80 完成 hotfix branch boundary 登記與機器檢查；PR #81 合併 hotfix，exact main 為 `3246f2a4ea8c7c1dc9751b8add30ab60dcd4c696`。Main CI run `33896333755` 成功。
- Worker artifact：run `33897173518` 通過 production approval、ARM64 immutable build／push、exact-digest Trivy `HIGH/CRITICAL` fail-closed scan與manifest保存；新 digest為`sha256:1655de7a07b93b08564693d2bfc678ba2d1f616dda01cf74a8efbd920cf084f4`。
- Production rollout：使用者透過 Systems Manager 依序更新兩台private Worker。`ip-10-20-20-170`與`ip-10-20-20-91`均回`worker_hotfix=verified`；雙節點postflight確認service enabled／active、container running、restart `0`、mode `async`、token budget `3000`、exact digest一致且registry auth absent。
- Non-goals：本次未修改或部署Web／Publisher，玩家可見production仍是`Release v1.1.2`；repo main內的`Release v1.1.3`保留供後續獨立Web release。沒有DB、schema、IAM、Queue、CloudFormation資源或固定成本變更。
- Live production validation：使用者另行核准並以一個新房間執行一次bounded玩家故事生成。Browser顯示三位玩家的Round 01行動完整保留、`故事主持人`產生新的完整敘事與下一幕，且沒有`系統備援敘事`或`ModelErrorException`；證明新Worker digest至少成功完成一次live玩家流程。
- Residual：Browser結果無法證明實際Bedrock invocation／retry次數，也不能保證Nova未來永不再產生invalid sequence；未另行查詢或保存raw CloudTrail、DB job payload或模型輸出。驗收只宣稱一次玩家流程成功，不宣稱全面消除服務端模型錯誤。
- Rollback：previous Worker digest＋runtime token值`800`；不影響已合併但尚待展示部署的`Release v1.1.3` Web patch。
