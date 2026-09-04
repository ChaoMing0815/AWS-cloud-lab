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
- Residual：repo-local測試不能保證Nova不再產生invalid sequence；production仍需新Worker digest、兩台runtime env同步、一次bounded故事驗證。
- Governance gate：hotfix branch尚未登記於受保護的`.agents/work-boundaries.json`；機器檢查目前只因`unregistered branch`失敗，需整合task取得明確治理修改授權後補登記，不得繞過。
- Rollback：previous Worker digest＋runtime token值`800`；不影響已合併但尚待展示部署的`Release v1.1.3` Web patch。
