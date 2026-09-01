# Deterministic rules retrieval 驗證摘要

- Scope／risk／upstream source：R2 repo-local Backend retrieval；`docs/features/pet-rules-assistant-two-day.md`。
- Baseline：rules／security／API suites `40 passed`。
- Red commit：`d627a434678cd60937a41016771d05aa74728302`；六類共 12 個繁中自然問法缺少 grounded match，新增案例如預期失敗。
- Green commit：`c5c9e5289afd834c1df56d8247e6b787e2524d78`；只擴充 versioned static record phrases。
- Stable contract：rule IDs、canonical content、citation 與 API request／response schema 均未變更。
- Targeted verification：`test_support_agent_rules.py` 為 `13 passed`。
- Affected verification：rules／security／API suites 為 `47 passed`。
- Full Backend regression：`840 passed, 16 skipped`；只有既有 Starlette／httpx deprecation warning。
- Negative：unknown 維持 `no_grounded_rule`，兩組跨主題查詢維持 `ambiguous_rule_query`，皆無 citation。
- Boundary：`git diff --check`、JSON parse 與 `scripts/check_branch_boundaries.py` 皆須通過。
- Rollback／residual：可回退 Green commit；deterministic allowlist 仍只覆蓋已列詞組，不提供 fuzzy／nearest fallback。
