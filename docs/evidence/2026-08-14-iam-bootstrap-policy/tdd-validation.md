# IAM Bootstrap Policy 驗證摘要

- Scope／risk／upstream source：R3 IAM 權限與成本防護；依 `AGENTS.md`、專題 Skill、2026-08-14 使用者決策，採一次性 `PowerUserAccess`＋專題前綴 IAM delegation，避免課程期間反覆調整 `ming-dev` 權限。
- Baseline：`f4ff321` 的 Tier 0 network template／contract 未變；Batch 0 已確認 Free plan、MFA、零長期 Access Key、Organizations 缺席與 workload 0。
- Red：`babf59e`；5 個 targeted tests 因 `infra/cloudformation/iam-bootstrap.json` 不存在而失敗。
- Green：`23375e8`；新增 IAM bootstrap CloudFormation JSON、Console runbook 與 policy contract tests。
- Targeted verification：`.venv/bin/python -m pytest -q backend/tests/test_iam_bootstrap_template.py` → `5 passed`。
- Related verification：IAM bootstrap＋Tier 0 network contracts → `8 passed`；JSON 由 `python3 -m json.tool` 成功解析。
- Full regression：Backend JUnit `255 tests`、`0 errors`、`0 failures`、`8 skipped`，即 `247 passed, 8 skipped`。
- Negative／boundary：禁止 Organizations／Control Tower／Identity Center bootstrap、Free plan upgrade、購買承諾、新 IAM user／Access Key；PassRole 只限 `AWSFinalProject*` 與指定 services；新 role 必須使用 `PowerUserAccess` permissions boundary。
- Sensitivity：將 PassRole resource 改為 `*` 時指定測試失敗；移除 `organizations:CreateOrganization` deny 時指定測試失敗；兩項 mutation 均已還原。
- Rollback：Root 先從 group detach `PowerUserAccess`，再刪除 `co-story-iam-bootstrap` stack，使兩份 customer managed policies 與 attachment 回復到原 read-only 基線。
- Residual risk：`PowerUserAccess` 是 AWS 維護的廣泛 service policy且未達 production least privilege；這是使用者為單人課程帳號選定的便利性取捨。AWS policy validation、simulation、CloudFormation change set 與實際 attachment 尚待 Console 驗證。
- AWS 狀態：本機階段未執行 AWS CLI 或 AWS 寫入。
