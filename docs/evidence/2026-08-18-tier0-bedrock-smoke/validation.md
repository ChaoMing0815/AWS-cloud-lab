# Tier 0 真實 Guardrail／Bedrock smoke 驗證

## Batch 7 邊界

- 2026-08-18 使用者已明確核准 Batch 7。
- 固定 Guardrail version `1`、Nova Lite Standard、APAC geographic processing；最多 3 次 model invocation、3 次 synthetic Guardrail evaluation，成本硬上限 `US$0.05`。
- 只使用虛構／合成資料；不啟用 invocation logging、不使用 AWS CLI、不新增 AWS resource、IAM 或固定費用。

## ApplyGuardrail 結果

- 從 Console 開啟的 SSM Session，以既有 application virtualenv、SDK 與 instance role 執行 exactly 3 次 `ApplyGuardrail`；此 API 不呼叫 foundation model。
- Benign input：action `NONE`。
- Harmful input：action `GUARDRAIL_INTERVENED`。
- Synthetic EMAIL／PHONE：action `GUARDRAIL_INTERVENED`，輸出以 `{EMAIL}`／`{PHONE}` mask，原值未保留。
- Usage：content policy `3` text units；sensitive information policy `3` text units。
- 依官方單價估算：`3 × 0.15/1000 + 3 × 0.10/1000 = US$0.00075`。

## Batch 7.1／7.1R 修正版部署

- 世界生成 schema／cache 修正 commit `d9c8f4e` 已建立；公開模式 release update
  修正 commit `27bebe2` 會沿用目前 active edge，且 edge 驗證失敗時恢復上一版。
- Release `tier0-20260818-27bebe2` 以既有 private S3／SSM 部署；S3 只讀取 exact
  archive／checksum，`co-story.tar.gz: OK`，未使用 AWS CLI、未呼叫模型。
- 舊 installer 以 `localhost` 驗證 public runtime 的嘗試，以及 caller `umask 0077`
  令 migration venv 無法由 `co-story` 執行的嘗試，均在 active symlink 切換前失敗、
  清除 candidate release 並維持舊版公開服務。第二次以隔離 root subshell
  `umask 022` 執行後成功。
- 最終狀態：`current` 指向 `tier0-20260818-27bebe2`；App／Public Nginx active、
  Staging Nginx inactive、公開 readiness HTTP `200`、首頁 `Cache-Control: no-store`。

## 真實世界生成結果

- 公開 HTTPS 首次真實世界生成已送達 Nova Lite，CloudWatch 出現該 ModelId 的
  `Invocations`、`InputTokenCount` 與 `OutputTokenCount`，沒有 client／server error
  metric；應用 API 回傳 `503`，UI 暫時顯示生成次數由 2 減為 1，但草稿與扣次
  均未持久化，canonical reload 後恢復為 2。原始 access line 含 client IP 與
  room UUID，未收入證據。
- Batch 7.2 已核准並以公開 HTTPS 執行 exactly 1 次真實世界生成：Nova Lite
  回傳符合 schema 的繁體中文草稿，五個 canonical 世界欄位自動填入，UI 無錯誤。
  canonical 生成次數由 `2` 變為 `1`；先前失敗呼叫未持久化扣次，重新載入後
  恢復為 `2`，因此不再沿用「最後一次額度」的舊判讀。剩餘 1 次不作重複驗證。
- 使用者提供的原始畫面含公開 IP 與房間代碼，未直接收入 repo；本節只保存
  去識別化文字結論。

## 尚待驗證

- 三個獨立 Browser session 加入同房、建立角色並完成一個完整回合。
- 真實 storyteller 結算、private RDS refresh、smoke room cleanup 與 Batch 後成本檢查。
