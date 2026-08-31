# Support Agent API／安全整合驗證摘要

- Scope／risk／upstream：ADR-0005與`support-agent-integration.md`；跨層API為R2，session／CSRF／identity／rate limit為R3。
- Base：初始exact base `6b1f63a`；完成前以merge同步`origin/main` `5fb80fb`，未rebase或force push。
- Contract：`d786984`已先獨立push並由整合task cherry-pick至main；PR diff不重複此protected contract差異。
- Red：原API三批Red之外，`a291ae8`證明idle keys未prune且unique keys可無限增長。
- Green／refactor：原Green／refactor之外，`74bc5cc`加入window pruning與rules 1024／reports 512 active-key capacity。
- Targeted／affected：Support API 22項、`test_support_agent*.py` 64項全綠。
- Backend／Frontend：Backend full 839 collected且無失敗（專用PostgreSQL環境案例明確skip）；Frontend 98項全綠。
- Negative：匿名／純Host／失效session、錯誤CSRF、unknown identity/state欄位、長度／body上限、429、dependency exception與安全serialization均通過。
- Sensitivity：既有security mutations之外，暫時移除pruning或capacity guard均使對應測試轉紅；mutation已還原且targeted重跑全綠。
- Static gates：12份YAML parse、`git diff --check`、`branch_boundary=passed`（8 paths）與本機container build通過。
- CI：原PR tip run `33365284676`四項全綠；bounded-limiter corrective tip將於push後重新執行Backend／Frontend／branch boundary／Trivy container scan。
- Rollback／residual：回退本分支commits即可移除API；limiter僅保證單process，production release前仍須依實際Web process數量review。
