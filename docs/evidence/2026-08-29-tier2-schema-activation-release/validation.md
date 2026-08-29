# Tier 2 `005` schema activation release 驗證摘要

- Scope／risk／upstream source：R3 production migration release preparation；verified bridge run `33241665137`與既有schema-activation contract。
- Bridge evidence：exact main `4435fdb…`、target digest `sha256:c0efe0f…`、Trivy success、SSM `Status=Success`／`ResponseCode=0`；Web仍為`sync`且未執行migration。
- Red commit：`0f513da`；Dockerfile缺少OCI revision label、workflow未傳exact `github.sha` build arg時兩項target assertion失敗。
- Green commit：`8f58c32`；final image寫入`org.opencontainers.image.revision`，release workflow以exact approved SHA作唯一值。
- Targeted verification：container、Tier 3 delivery與GitHub workflow contract共51項全綠。
- Full regression：Backend `767 tests collected`，exit code `0`；只有既有Starlette／httpx warning。
- Frontend local：workspace無`npm`，未宣稱本機通過；PR CI的Frontend gate必須全綠後才可合併。
- Boundary：revision metadata不含credential、account、ARN或secret；不改IAM、SSM Document、migration SQL、runtime mode或publisher activation。
- Rollback／stop：PR／CI未完成前不得dispatch activation；activation target digest必須不同於bridge且previous精確為`sha256:c0efe0f…`。
