# 期末專題報告網頁 task packet

## 任務目的

建立一份可在本機瀏覽器播放的繁體中文期末報告網頁，以分段捲動、動畫與可驗證的 AWS 架構圖呈現「共演計劃」從單一 EC2 演進至目前組件化 production 的過程。網頁是視覺與內容的主要編排來源；使用者確認後，另一個交付階段再將固定畫面截取並編排為 PPTX。

## 建議分支

- 分支：`codex/final-report-web`
- 建議基準：包含 `codex/final-report-deck` 最新 README／報告修正，並已由整合 task 登記以下 branch policy 的 exact commit。
- 交付方式：只建立 local commit；不得 merge、push、deploy 或發布網站。

## 建議 branch policy

Purpose：建立本機期末報告 scrollytelling 網頁、動畫架構演進與可重現的 16:9 capture；不修改產品 Web、Backend、README、AWS、workflow、production 或既有 PPTX。

Allowed paths：

```text
docs/reports/2026-09-*-co-story-final-report/site/**
docs/reports/2026-09-*-co-story-final-report/captures/**
docs/reports/2026-09-*-co-story-final-report/web-report-*.md
```

Protected／禁止修改：

- `.agents/work-boundaries.json`、`AGENTS.md` 與治理文件。
- 根 `README.md`、`docs/handoffs/CURRENT.md`、task list、deployment log、source-of-truth。
- 產品 `web/**`、`backend/**`、`ops/**`、`infra/**`、`.github/**`。
- 既有期末 PPTX；截圖轉 PPTX 是後續獨立交付。
- `.openai/hosting.json`、任何 Sites production project 或公開部署設定。

## 執行限制

- 使用 `sites-building` 與 `operate-aws-final-project` Skill。
- 本任務明確採 local-only：不得呼叫 Sites hosting／deploy，不建立公開 URL。
- 不執行 AWS CLI、S3、Bedrock、SSM、workflow dispatch 或 production request。
- 不擷取含 account ID、Email、public IP、endpoint、session、token、secret 或完整 digest 的畫面。
- 不新增 DynamoDB、ALB、ECS、EKS、Lambda、CloudFront、Route 53 或多 AZ 等現況不存在的服務。
- 不呈現課程分級術語；不使用對比式否定句與自我提示文字。
- AWS 服務必須使用官方 AWS Architecture Icons，圖示與服務名稱一一對應。

## 內容來源

依序使用以下 repo-local 文件；禁止遞迴讀取整個 `docs/`：

1. `AGENTS.md`
2. `docs/product/source-of-truth.md`
3. `docs/handoffs/CURRENT.md`
4. `.agents/work-boundaries.json`
5. `docs/governance/parallel-branch-boundaries.md`
6. `docs/testing-strategy.md`
7. `docs/reports/2026-09-02-co-story-final-report/README-update-draft.md`
8. `docs/reports/2026-09-02-co-story-final-report/report-materials.md`
9. `docs/architecture/final-report-diagram-brief.md`
10. 只在需要引用具體數字或畫面時讀取 CURRENT 已列出的 canonical evidence。

## 內容與敘事邊界

### 主線

1. 共演計劃：多人共同決策，後端先判定規則，Bedrock 敘述既定結果。
2. 起始架構：public EC2 上的 Nginx／FastAPI、private RDS 與 Bedrock。
3. 可觀測維運：CloudWatch safe logs／metrics／alarm、Systems Manager 與人工核准。
4. 組件化部署：Web／API＋Publisher、SQS／DLQ、兩台 private Worker、private RDS。
5. 非同步契約：`202 Accepted → polling → applied result`，搭配 retry、DLQ、version guard 與 idempotency。
6. CI/CD：tests、ARM64 image、Trivy、GitHub OIDC、ECR immutable digest、production reviewer、SSM health gate 與 rollback。
7. 安全與觀測：public／private、IAM identity、CloudWatch、AIOps bounded summary 與人工動作。
8. 產品玩法、Support／pet rules assistant、Demo、成本與清理。
9. 成果與可持續演進方向。

### 玩法事實

- 3–5 位玩家，選擇 4／6／8 回合。
- 角色欄位為名稱、背景、性格特質、弱點、勇氣、洞察、羈絆與星火。
- 玩家每回合選擇勇氣、洞察或羈絆作為行動方式。
- 後端擲兩顆六面骰並加入所選行動方式數值；結果為成功、部分成功或失敗。
- 玩家看到骰子後，可消耗 1 點星火使總值增加 1。
- 進度達 100% 時可選擇結束或繼續；回合用完後生成結局，危機影響代價。

### Production 事實

- 唯一 public edge 為 Nginx／Web／FastAPI API。
- Publisher、SQS／DLQ、兩台 private Worker、private RDS 與 Bedrock 敘事鏈已存在。
- 兩台 Worker 位於同一 Availability Zone；現況仍有單點與 AZ failure domain。
- SQS 為 at-least-once delivery；PostgreSQL identity、idempotency、lease、fencing、inbox／outbox 與 replay-safe transaction 負責收斂。
- Support／pet rules assistant 採 deterministic cited lookup；問題回報只建立 `local_draft_only` 人工確認草稿。

## 網頁體驗規格

- 採單一路由、分段式 scrollytelling；每個主要 section 對應一個 16:9 capture checkpoint。
- Desktop 第一優先，以 `1920 × 1080` 作為主要展示 viewport；仍須避免窄螢幕水平溢位。
- 支援滑鼠滾輪、觸控板、`ArrowUp`、`ArrowDown`、`PageUp`、`PageDown`、`Home`、`End`。
- 清楚顯示目前章節與閱讀進度，避免讓導覽 UI 搶走內容焦點。
- 動畫使用 opacity、transform、stroke reveal；不使用旋轉、彈跳、粒子或持續閃爍。
- `prefers-reduced-motion: reduce` 時立即顯示穩定的最終狀態。
- 所有字型與圖示為本機資產；現場播放不依賴外部 CDN、API 或網路字型。
- 視覺方向：深色夜幕劇場、暖金、青綠、少量珊瑚色；不使用制式 SaaS landing-page 模板。

## 架構圖與動畫規格

- 使用 DOM／CSS 與圖示元件建立節點；連線可使用 SVG path，但不得用模型生成的裝飾性 SVG 插畫。
- 所有連線先完成路由，再疊放服務節點。
- Web、Queue、Worker、RDS 位於主要水平軸；Bedrock 使用上方 inference lane；CloudWatch、Systems Manager、Human approval 使用下方 control-plane rail。
- 箭頭採 90 度正交路由，端點停在節點外框前，線條不穿越文字、圖示、群組標題或其他箭頭。
- 動畫狀態：
  1. `Classic`：EC2、RDS、Bedrock。
  2. `Observable`：保留既有節點，加入 CloudWatch、Systems Manager 與人工核准。
  3. `Componentized`：加入 Publisher、SQS／DLQ、Worker A／B，將 Bedrock 呼叫移至 Worker。
  4. `Current production`：展開 public、private compute、private data 與 control plane。
- 每個狀態都必須有可直接截圖的靜態停格。

## 建議專案結構

```text
docs/reports/2026-09-02-co-story-final-report/site/
  package.json
  package-lock.json
  index.html
  src/
  public/
    aws-icons/
  tests/
  scripts/
docs/reports/2026-09-02-co-story-final-report/captures/
docs/reports/2026-09-02-co-story-final-report/web-report-validation.md
```

## 開發與驗證

1. 先以測試固定 section IDs、禁止文字、AWS service inventory、鍵盤導覽、reduced motion 與 capture checkpoint contract。
2. 建立第一個可辨識的 opening＋architecture-evolution slice，完成編譯與本機 preview 後再擴充。
3. 完成全部章節、動畫、responsive 與本機資產。
4. 執行 production build、測試與靜態資產檢查。
5. 以瀏覽器檢查 `1920 × 1080` 全部 section；驗證沒有裁切、重疊、水平 overflow、箭頭碰撞或錯誤服務圖示。
6. 對每個 capture checkpoint 輸出固定 16:9 PNG，檢查輸出順序與尺寸。
7. 執行文字掃描，確認沒有課程分級、自我提示、產品幻覺或敏感資訊。
8. 執行 `scripts/check_branch_boundaries.py`，取得 `branch_boundary=passed`。

## 完成定義

- 本機可開啟、可捲動、可鍵盤操作的完整報告網站。
- 架構演進動畫與 reduced-motion 靜態版本皆正確。
- AWS 官方圖示、服務邊界、資料流與 production 證據一致。
- 所有 section 已通過 desktop 視覺 QA；capture checkpoints 可重現。
- 固定 16:9 PNG 已產出，供下一階段編排 PPTX。
- Tests、build、capture validation、文字／敏感資訊掃描與 branch boundary 全部通過。
- 只修改白名單路徑並建立 local commit；不 push、不 deploy。
