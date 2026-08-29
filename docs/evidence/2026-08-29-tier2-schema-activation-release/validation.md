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

## 首次 production activation 與 SQL 相容性修正

- Run `33242226396`綁定exact main `61a736a1e770f2678e3abe438607e222c1e45bfe`；approval、ARM64 build／push、digest fence與Trivy均通過，target digest為`sha256:811faece…`。
- SSM preflight驗證previous bridge digest `sha256:c0efe0f…`正確，migration因PostgreSQL不存在`jsonb_object_length(jsonb)`而fail closed，response code `2`；未切換target image、未清除bridge marker、未啟用async／publisher。
- Root cause：`005_create_story_job_dispatch_outbox.sql`的payload CHECK誤用不存在的函式；安全目標仍是只允許`schema_version`與`job_id`兩個key。
- Red commit：`1cc347e`；要求以受支援的JSONB key-removal guard取代不存在函式，target test因舊SQL失敗。
- Green commit：`916e76d`；使用`(message_payload - 'schema_version' - 'job_id') = '{}'::jsonb`保留exact-key invariant。
- Targeted verification：migration contracts `7 passed`；代表性sensitivity改回`jsonb_object_length`時target test失敗，還原後通過。
- Full regression：Backend `767 tests collected`，exit code `0`；只有既有Starlette／httpx warning。
- Rollback／residual risk：production inventory仍應為`001`–`004`且active release仍是bridge；修復PR與CI全綠後，必須以新exact main／新digest另行核准activation，不得rerun失敗run。

## 修復後 production activation 完成

- PR #50四項CI全綠並合併為exact main `ae2666ae26da15284e45d7143596f51201e50fe2`；未rerun失敗run。
- Run `33243455252`通過production approval、ARM64 build／push、digest fence、exact-digest Trivy與bounded SSM；target digest為`sha256:abd0f942c036f3794bdb6ed159793106a2bf26ce7f566f0b561a77033c595f13`。
- SSM回`container_release=verified mode=schema-activation`、`Status=Success`與response code `0`；previous digest精確為bridge `sha256:c0efe0f…`。
- 單一bounded postflight確認active image digest吻合、migration inventory精確為`001`–`005`、runtime精確為`sync`、bridge marker已清除。
- Publisher unit、publisher runtime env與publisher container均不存在；未送SQS message、未呼叫Bedrock、未切換Web async。
- 本批完成；下一批若安裝publisher，只允許disabled／inactive狀態，啟用與測試訊息仍需分開核准。
