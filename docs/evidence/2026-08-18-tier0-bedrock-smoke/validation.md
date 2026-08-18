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

## Batch 8A 三玩家單回合結果

- 三個獨立 Browser sessions 以虛構身份加入同房，Lobby 為 `3/5`；三個角色均完成，
  房主開始第 1 回合，全程無 UI 錯誤。
- 三位玩家各提交一個 benign action，所有頁面依序同步 `1/3`、`2/3`、`3/3`。
  房主鎖定後三組骰點均出現；三位玩家各自保留星火，決策狀態跨頁同步。
- 固定待結算結果為進度 `+4`、危機 `+2`。房主結算 exactly 1 次真實 Nova Lite
  回合敘事後進入第 2 回合；正式進度 `4（13%）`、正式危機 `2（7%）`，繁體中文
  敘事、三位玩家 action 與骰點結果均保留。
- 三個 sessions 各自重新整理後仍讀回第 2 回合、進度／危機、AI 敘事與 `0/3`
  等待行動，private RDS refresh gate 通過。重新整理時曾短暫顯示 Landing，隨後
  canonical state 正確恢復；此為 UI loading-shell backlog，不是資料遺失。
- 原始截圖可能包含仍有效的房號／公開 IP，房間存續期間不直接收入 repo；房號只有
  在房間刪除或到期並確認不可加入後，才可作為隨機代碼展示證據。

## Batch 後成本檢查

- 使用者於 AWS Cost Explorer 以 Console 唯讀檢查，回報 Total、Amazon Bedrock、
  Amazon EC2、Amazon RDS 與其他服務目前均為 `0`。
- AWS 帳務可能延遲入帳；此結果代表檢查當下沒有可見異常費用，不宣稱本次資源與
  模型使用永久零成本。後續報告需搭配既有 credits／Budget 與清理計畫說明。

## 尚待驗證

- 去識別化證據整理。
- Smoke room 目前仍為進行中，依最後活動後 7 天到期；產品 UI 只在結局後提供永久
  刪除，不以額外五回合 Bedrock 呼叫換取立即清理。
