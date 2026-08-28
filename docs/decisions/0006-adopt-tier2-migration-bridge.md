# ADR-0006：採用 Tier 2 migration bridge 與分離 schema activation

- 狀態：Accepted
- 日期：2026-08-28
- 決策者：專題使用者／Sol R3 設計 gate／整合 task
- 範圍：Tier 2 append-only migration、Tier 3 release driver 與 production runtime 切換

## 背景

目前 active container runtime 的資料庫只有 `001_create_rooms`，但程式庫已存在尚未部署的 `002`、`003`，而 Support persistence PR #25 提供候選 `004`。原本的 digest release 先執行 migration，再驗證 previous runtime；只把 readiness 放寬為版本子集合，無法阻止舊 runtime 在 newer schema 下失敗，且會把 migration 與 runtime promotion 混成同一不可逆風險。

## 決策

1. release mode 分為 `migration-bridge` 與 `schema-activation`，兩者各自需要獨立的 production change envelope；本 ADR 只建立 repo-local contract。
2. `migration-bridge` 必須以 canonical active previous digest 為輸入、legacy input 為空、完全不呼叫 migration。candidate 與 stable Web runtime 固定 `CO_STORY_RESOLUTION_MODE=sync`，保留既有同步 `200` 遊戲流程。
3. bridge 成功後才寫入 root-only、精確兩行、digest-bound 的 verified marker。marker 的 image 必須精確等於 bridge digest。
4. `schema-activation` 在任何 migration 或主機 mutation 前，必須驗證 marker 的 metadata、shape、state 與 previous digest；migration 後再驗一次 marker，再驗 previous bridge runtime與candidate。失敗只回復 verified bridge digest，絕不做 schema downgrade。
5. migration runner 與 readiness 共用同一 validator，只接受完整的已審核前綴：`001`、`001+002`、`001+002+003`、`001+002+003+004`。不得以 set 隱藏重複值；空、gap、unknown、duplicate、malformed 與 DB 不可用均 fail closed。
6. production Worker factory 在 `sync`（及任何非 `async`）mode 下，必須在 queue、Bedrock client 或 claim 前停止。

## 結果與取捨

- schema 前進後的唯一 rollback target 是 verified bridge digest，不得將 legacy runtime 宣稱為 newer schema 的 rollback target。
- bridge 暫時刻意不啟用 async producer／Worker；Tier 2 非同步功能仍保留在後續、獨立核准的 runtime activation 範圍。
- PR #25 在 bridge 已驗證、schema activation 批次另行核准前保持 `DO NOT MERGE`，本決策不構成 AWS 部署核准。
