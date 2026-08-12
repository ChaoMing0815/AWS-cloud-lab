# Tier 0 release／rollback 契約驗證摘要

- 範圍／風險：R3；版本化 runtime、schema compatibility、原子切換與 rollback 安全。
- Sol review：release 必須自帶 `.venv`；activation／rollback 僅在 candidate readiness 成功後切換；Tier 0 schema 要精確相等，禁止 downgrade。
- Red：`435a6d7 test(red): specify release rollback safety contract`；未知 migration 被錯誤接受、shared venv 與四個 release assets 缺失。
- Green：`c6c17b0 feat(green): add safe release rollback contract`；main service 採 release-local venv，schema readiness 精確比對，candidate／migration 皆為獨立 non-root unit。
- Targeted：migration readiness、runtime bundle、release rollback contract 共 18 passed；`bash -n` 兩支 release scripts 通過。
- Full regression：Backend `235 passed, 8 skipped`。
- Sensitivity：將 rollback restore 的 `mv -Tf` 降為 `mv -f`；加強後的 contract 立即失敗，已還原。
- Rollback／residual risk：靜態驗證不能取代 disposable Linux VM／EC2 的 systemd、Nginx、curl 與真實 RDS failure 演練；未在此切片執行任何環境部署。
