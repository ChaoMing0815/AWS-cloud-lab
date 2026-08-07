# 共演計劃 Tier 0–5 甘特圖

期末專題繳交日：2026-09-07。

> 排程原則：同一產品逐層演進。每個 Tier 先完成一個能 Demo 的最小切片並保存證據，再增加深度。AWS 帳號與預算關卡未通過前，先完成對應的本機程式、IaC／指令草稿與測試。

## 6 週計畫

| 任務 | W1<br/>7/27–8/2 | W2<br/>8/3–8/9 | W3<br/>8/10–8/16 | W4<br/>8/17–8/23 | W5<br/>8/24–8/30 | W6<br/>8/31–9/6 |
| --- | --- | --- | --- | --- | --- | --- |
| 專題治理、Budget、IAM 與帳號關卡 | X | X | X |  |  |  |
| 需求 Research、MVP Spec、原型 |  | X | X |  |  |  |
| FastAPI、game engine、repository、tests |  | X | X |  |  |  |
| Tier 0：VPC、EC2、private DB、Bedrock |  | 設計 | X | X |  |  |
| Tier 1：CloudWatch、SSM、AIOps incident |  |  | 設計 | X | X |  |
| Tier 2：Web/API、Worker、Data 三組件 |  |  |  | X | X |  |
| Tier 3：Docker、ECR、GitHub Actions |  |  |  | X | X |  |
| Tier 4：五服務拆分與故障隔離 |  |  |  |  | X | X |
| Tier 5：Prompt、RAG、MCP／Tools、監控 |  |  |  |  | X | X |
| 架構圖、證據、README、部署紀錄 | X | X | X | X | X | X |
| Demo 演練、成本檢查與清理 |  |  |  |  |  | X |

## 里程碑

| 里程碑 | 期限 | 可驗收結果 |
| --- | --- | --- |
| M1：產品定義完成 | 8/9 | Research、核准 Spec、題材中立原型、Tier 0–5 對照 |
| M2：本機 MVP 完成 | 8/16 | FastAPI、memory repository、mock storyteller、核心 tests |
| M3：Tier 0 AWS 可玩 | 8/20 | 公開 Web、private DB、Bedrock 一回合、資料持久化與安全證據 |
| M4：Tier 1–2 完成 | 8/25 | CloudWatch／SSM incident Demo、三組件 E2E 與網段證據 |
| M5：Tier 3–4 完成 | 8/31 | 自動部署成功、五服務故障隔離 Demo |
| M6：Tier 5 與最終交付 | 9/6 | RAG／tool／monitoring Demo、文件、截圖、清理計畫完整 |

## 關鍵路徑

```text
核准 Spec
  → FastAPI monolith + tests
  → Tier 0 AWS vertical slice
  → logs／SSM 與 incident data
  → 組件切割
  → container／pipeline
  → 微服務故障隔離
  → RAG／MCP／多 Agent 與監控
  → 最終 Demo
```

## 延誤時的縮減原則

- 不刪除整個 Tier；縮成一個可驗證案例。
- Tier 2 只保留 Web/API、Story Worker、Data 三組件與一條 E2E 流程。
- Tier 3 只保留一條主分支自動部署 pipeline。
- Tier 4 的五服務只實作必要 API 與健康檢查，不追求完整業務功能複製。
- Tier 5 只保留一個 RAG corpus、一個 allowlisted tool、一次人工批准與一張監控圖。
- 不以取消安全、費用或證據關卡換取速度。

## 繳交日

2026-09-07：提交 GitHub、AWS 實作、架構演進圖、成功／負面驗證截圖、README、甘特圖、checkpoints、Demo 與清理紀錄。
