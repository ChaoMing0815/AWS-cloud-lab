# Tier 0 stabilization release 驗證摘要

- 日期：2026-08-22
- Branch：`codex/tier0-post-trial-stabilization`
- PR：#5，merge state `CLEAN`
- Release：`tier0-20260822-8bb6bfc`
- Release commit：`8bb6bfc77f1524849ef5c66254c27bd0f8445fb5`
- 結論：**PASS with findings**

## CI 與 release gate

- PR #5 最新 tip 的 GitHub Actions run `32553769222`：Backend／Frontend jobs 均通過。
- 本機 release archive 約 `140 KiB`，只由 `backend/`、`ops/`、`web/` 組成。
- Batch 10A 由使用者明確核准；使用者透過 Console 上傳 archive／checksum 兩個 exact S3 objects，再於 Console 開啟的 SSM Session 讀取相同兩個 objects。
- EC2 端 `sha256sum -c`：`co-story.tar.gz: OK`。
- 部署前：application／public edge `active`、active release `tier0-20260819-ee128da`、RDS readiness `200`。
- 部署後：application／public edge／renewal timer `active`、staging `inactive`、active release `tier0-20260822-8bb6bfc`、previous release `tier0-20260819-ee128da`、RDS readiness `200`、public HTTPS `200`、`Cache-Control: no-store`。
- Installer 保留 previous release 並具 candidate readiness 與 edge verification rollback；本次未觸發 rollback。
- 本批未建立或修改 IAM、CloudFormation、CloudWatch、Guardrail、model 或其他 AWS resource；未呼叫 Bedrock。

## Desktop 與 Safari Browser gate

- 世界尚未開放時，以有效房號加入會留在首頁並顯示「房主尚未開放世界，請稍後再試。」；按鈕恢復可操作。
- 房主角色可成功儲存與改名；畫面顯示「角色已儲存。」，roster 同步更新，Desktop Console error 為 `0`，未再顯示原始 JavaScript exception。
- iPhone Safari 玩家可加入 Lobby 並成功儲存角色；Safari → Desktop roster 自動更新。
- Desktop 房主改名後，iPhone Safari 在未重新整理下自動更新，延遲小於 `10` 秒。
- Desktop 與 Safari 重新整理後資料均正常，確認 private PostgreSQL persistence。

## Findings 與未執行項目

- 新 finding：房主先選 `8` 回合，再因故事背景不足 `50` 字收到 `422` 時，文字欄位仍保留，但回合上限回到 `6`。這是 confirm error-path form state 問題，與已修正的世界生成成功後保留選項屬相鄰但不同的 TDD slice。
- 成功確認世界前再次選擇 `8` 可正常送出；本批為零模型 gate，未點擊「生成世界草稿」，所以沒有宣稱 AWS runtime 已驗證生成成功後的回合選項保留。
- 測試房停在 `LOBBY`；正式產品只允許房主刪除 `COMPLETED` 房間，因此本批未繞過產品規則直接刪 DB，也沒有完成多分頁刪房 polling AWS E2E。匿名測試資料留待 retention cleanup。

## 成本決策

- RDS 在 Batch 10A 前由使用者啟動。後續仍有頻繁 stabilization／Tier 1 工作，因此使用者決定暫時維持運行；預估超過 `48` 小時不使用時才手動停止。
- `48` 小時是本專題的操作門檻，不是 AWS 限制。AWS 官方說明：停止期間不計 DB instance hours，但 provisioned storage 與 backup storage 仍計費；連續停止最長 `7` 天，之後會自動啟動。[AWS RDS 暫停文件](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_StopInstance.html)
- EC2 仍維持運行，以保留目前 public IP certificate／allowlist；S3 release objects 依既有 `7` 日 lifecycle 到期。

## 下一步

1. 依嚴格 TDD 修正 confirm `422` 後回合上限回到 `6`。
2. PR #5 review／merge 前決定是否需要另開 exactly one Bedrock call 的生成後 Browser gate。
3. 下一次有已完成測試房時，再驗證刪房後其他分頁停止 polling 與導回首頁。
