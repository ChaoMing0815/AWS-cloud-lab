# 寵物視覺 v1.1.1 production release 驗證

- 日期：2026-09-02
- Scope／risk：R2 玩家可見 UI patch；沿用既有 `digest-release` production envelope。
- Exact production source：`4fb06d0fa33c6b4152d20288c7db4ef7d3927794`。
- Main CI：run `33582692830` 成功；Frontend、Backend與container HIGH／CRITICAL scan均通過，`main`事件的branch-boundary依workflow設計跳過。
- Release：run `33583003508` 成功；production approval、GitHub OIDC、ARM64 immutable push、digest fence、exact-digest Trivy、bounded SSM與delivery metrics均通過。

## Runtime 結果

- Previous／rollback Web digest：`sha256:14d8e0fbc2ef6a5c8363b40e30160a7cd76f42a29d8a506be250263026486d90`。
- Active Web digest：`sha256:ad0ee896c1a3e292229a97102b42f2eabd6fd6d2f8590d8c65b255bba163dca4`。
- SSM release：`Status=Success`、`ResponseCode=0`；delivery metrics `status=success`、`verified=true`。
- Metrics：approval wait `216s`、automation execution `151s`、build and scan `126s`、end-to-end `375s`、SSM release attempt `25s`。
- Web runtime沿canonical installed unit維持`async`；migration inventory、Publisher與兩台private Worker均未變。

## Production acceptance

- Strict TLS：首頁、`/api/v1/live`、`/api/v1/ready`均回`200`。
- 首頁玩家可見`Release v1.1.1`，document沒有水平溢位。
- Launcher包含果凍本體、底部裙邊與直接長在身體上的表情；computed body使用圓潤不對稱border radius與半透明mint gradient。
- 舊機器人深色面板與分離機械腿均不存在；底層仍為原生button，`aria-label=開啟規則寵物助手`。
- 等待前端初始化後，點擊寵物可開啟既有規則對話框，`aria-expanded=true`。

## 誠實邊界與 rollback

- 本次只調整Frontend視覺與release marker；rules retrieval、Backend、API、database、migration、RAG、IAM、AWS資源、Publisher、Worker與workflow均未修改。
- 沒有Bedrock／RAG／MCP／external submit、第二個story job或額外模型呼叫。
- 若Web release需回復，使用既有exact-digest流程切回`sha256:14d8e0fbc2ef6a5c8363b40e30160a7cd76f42a29d8a506be250263026486d90`；本次無schema變更，不需要database rollback。
