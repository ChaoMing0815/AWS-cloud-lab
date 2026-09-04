# Nova Lite ToolUse 穩定化 Hotfix

- 狀態：Repo-local implementation complete；尚未 push、merge、build 或 deployment
- 風險：R2（LLM adapter、production Worker runtime contract）
- 事故來源：2026-09-04 production CloudTrail 四筆 `Converse` 均回 `ModelErrorException`，訊息為模型產生無效 ToolUse sequence

## 目標行為

1. `amazon.nova-lite-v1:0` 的 forced-tool request維持 `temperature=0`，並額外使用 AWS 建議的 greedy decoding欄位 `additionalModelRequestFields.inferenceConfig.topK=1`。
2. 既有 round／ending structured tool schema的 bounded output budget由`800`提高為`3000`；adapter、production factory、runtime example與Worker replacement bootstrap使用同一上限。
3. 非 Nova model與未使用tool的世界觀生成不得附加Nova專用欄位。
4. `ModelErrorException`維持retryable、去敏的`TRANSIENT_SERVICE_ERROR`，不得保存AWS原始訊息、prompt、response或玩家內容；既有最多三次attempt與房主人工fallback不變。

## 部署與版本邊界

- 本 hotfix 不修改`web/**`或`releaseVersion`，因此玩家可見版本仍由已合併的`Release v1.1.3` UI patch管理。
- Worker image與Web image使用各自既有workflow／rollout；Worker hotfix不得取代或提前觸發明日Web CI/CD展示。
- Production rollout前必須固定exact main SHA、new／previous Worker digest、兩台private Worker target、runtime env由`800`精確更新為`3000`的bounded SSM步驟、health gate與rollback。
- Production驗證最多新增一次明確核准的故事生成；本repo-local切片不呼叫Bedrock。

## 回復方式

兩台Worker恢復previous immutable digest，並把`CO_STORY_BEDROCK_MAX_TOKENS`精確還原為`800`後restart；Web、Publisher、資料庫、Queue、IAM與玩家資料不變。
