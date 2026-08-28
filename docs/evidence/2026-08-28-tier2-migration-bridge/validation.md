# Tier 2 migration bridge 驗證摘要

- Scope／risk／upstream source：R3 repo-local migration bridge；ADR-0006、2026-08-28 Sol 設計 gate。
- Baseline：相關 migration／release／API／Worker／container contract suite 全綠；僅既有 Starlette deprecation warning。
- Red commit：`bcc891b`（inventory、sync composition、Worker second guard、release mode與marker contract）。
- Green commit：`d9d8a57`。
- Targeted verification：migration readiness、production composition、Tier 2 Worker、Tier 3 release workflow／driver contract 全綠。
- Negative／boundary：empty／gap／unknown／duplicate／malformed inventory、sync Worker、bridge marker missing／stale digest與unknown mode均 fail closed。
- Sensitivity：本機暫時破壞 migration call、inventory allowlist、sync flag、marker digest、rollback restore target與workflow bridge case；每次目標測試皆失敗後立即還原。
- Rollback／residual risk：schema activation只回復 verified bridge digest，不做 downgrade；未執行AWS、SSM、workflow dispatch或production deploy。真實 PostgreSQL process/restart gate仍需獨立非production DSN。
