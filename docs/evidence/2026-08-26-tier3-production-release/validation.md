# Tier 3 首次 container transition 本機驗證

- 風險：R3；範圍為首次 legacy bootstrap、人工 legacy rollback與既有 digest rollback。
- 基準：`fa543e973f47fb36f0897de1d07650021b75ef11`；未執行任何 AWS、SSM、image push或 production action。
- Red `4bc0187`：首次 transition、failure／rollback與 mode contract。
- Red `1ded566`：target restart與 state／checksum／env／previous fencing。
- Red `c5a76b5`：pre-pull host guards與固定 legacy candidate executable。
- Red `60f8131`：mutation-stage rollback、乾淨重試、failure state與 target-bound asset promotion。
- Corrective targeted `39 passed`；Tier 3 affected `46 passed`；Backend `424 passed, 8 skipped`；Frontend `94 passed`。
- GitHub workflow與 CloudFormation YAML parse通過；template含 6 個 resources與兩個獨立 SSM Documents。
- Sensitivity 暫時移除 digest asset promotion marker，使「target health後才能 promotion」ordering contract精確失敗；還原後單測通過，mutation未保留。
- Corrective本機 ARM64 build、non-root `10001:10001`、固定 release assets、migration與 container `live`／`ready` health通過。
- Trivy `v0.70.0` 以 `HIGH,CRITICAL`、`ignore-unfixed`、`exit-code 1`掃描本機 image tar，0 findings。
- `bash -n`、`git diff --check`與 branch boundary結果，以本分支完成回報為準。
- Evidence 不含 secrets、AWS account、ARN、instance ID或 IP。
