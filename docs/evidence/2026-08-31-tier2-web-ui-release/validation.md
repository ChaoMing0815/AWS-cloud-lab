# Tier 2 Web UI digest release 驗證摘要

- Scope／risk／upstream source：R3 release safety；依平行分支治理固定的 `codex/tier2-web-ui-release` contract。
- Baseline：Tier 2＋Tier 3 release suites全綠；Backend full全綠；Frontend 98／98通過。
- Red commit：`a95e099`，7項targeted案例證明source unit會以`sync`覆蓋active `async`，且malformed active mode未fail closed。
- Green commit：`26c4529`，digest-release只接受canonical installed unit的唯一精確`sync|async`。
- Targeted verification：新contract 7／7通過。
- Affected regression：Tier 2 mode transition與Tier 3 delivery／rollback合計128項通過。
- Negative／boundary：missing、duplicate、empty、uppercase、unknown與whitespace mode均在login／pull／migration／mutation前停止。
- Rollback：candidate、promoted installed／stable unit與previous restore均保持同一validated active mode。
- Bridge/schema：既有固定sync、migration skip／activation、digest fence、health、marker與rollback suites全綠。
- Sensitivity：暫時將candidate回退為硬編sync時代表性async測試失敗；還原後7／7通過，mutation未commit。
- Full gate：Backend 824項已收集並全綠（環境型PostgreSQL案例依既有條件skip）；Frontend 98／98通過。
- Residual risk：本批只有repo-local contract證據；未觸發workflow、AWS／SSM、Bedrock或production deploy。
