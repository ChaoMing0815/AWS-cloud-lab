# Tier 3 digest driver handoff 驗證摘要

- Scope／risk：R3 production release contract；修正舊 stable driver 執行新版 `digest-release`、使新版 mode-preservation 邏輯無法在同次部署生效的交接缺口。
- Production observation：UI image `sha256:926f19e…` 部署健康，但 Web mode 從 `async` 回退為 `sync`；既有 bounded transition contract 已恢復 `async`，postflight 全數通過。
- Base：`58fc124225b7c1a57827b72758f0829c1103329f`。
- Red：`0b46906`；exact SSM Document harness 證明舊 stable driver 完成 preflight 後，release 沒有交接至 exact target image driver。
- Green：`018ffb9`；`digest-release` 與 bridge／schema mode 共用 exact target image ID、temporary asset metadata、preflight checksum fence及target driver release。
- Targeted：Tier 3 Document、legacy rollback與async release受影響 suites全綠。
- Full regression：Backend全綠（既有conditional skips與Starlette deprecation warning不變）；Frontend `98 passed`。
- Negative／boundary：stable driver仍先驗證目前host state；target driver及unit必須來自exact digest、為regular root-owned assets，preflight後checksum不變才可release。
- Sensitivity：暫時恢復stable-driver release後，新handoff測試精確失敗；mutation已還原且targeted重回全綠。
- Rollback：既有driver／unit backup、state fence、candidate health與previous image restore邏輯未放寬。
- IaC delta：只修改 `ContainerReleaseDocument.Properties.Content`；不改IAM、OIDC、ECR、workflow、image、migration、網路或成本。
- Residual：此repo-local修正尚未建立或執行CloudFormation Change Set；未授權production deployment。
