# Production dependency lock 驗證摘要

- 範圍／風險：R2；Tier 0 runtime dependency lock 與可重現 import。
- Baseline：Backend `224 passed, 8 skipped`。
- Red：`4d340f5 test(red): specify production dependency lock`；目標測試因 `requirements-prod.txt` 不存在而預期失敗。
- Green：`837162d feat(green): lock production runtime dependencies`；直接依賴與完整解析結果均採精確版本，開發依賴引用同一 runtime lock。
- Targeted：`backend/tests/test_production_dependencies.py`，2 passed。
- 乾淨環境：Python 3.13 temporary virtualenv 以 `requirements-prod.txt` 安裝後，`import app.main, boto3, botocore` 成功；未呼叫 AWS。
- Full regression：Backend `226 passed, 8 skipped`。
- Sensitivity：移除 `boto3==1.43.69` 後，required-runtime-package assertion 預期失敗；已還原。
- Residual risk：lock 尚未有 wheel hash；平台／Python 版本變更時須在乾淨環境重新解析與驗證。
