# 共演計劃最終交付甘特圖

期末專題繳交日：2026-09-07。

> 排程原則：此表保留已走過的演進路徑；依 [ADR-0008](decisions/0008-fix-final-delivery-scope.md)，最終交付止於 AWS 組件化與自動部署。Tier 4／5 不屬於本次排程或完成條件。

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
| Bounded Support Agent extension |  |  |  |  | X | X |
| 架構圖、證據、README、部署紀錄 | X | X | X | X | X | X |
| Demo 演練、成本檢查與清理 |  |  |  |  |  | X |

## 里程碑

| 里程碑 | 期限 | 可驗收結果 |
| --- | --- | --- |
| M1：產品定義完成 | 8/9 | Research、核准 Spec、題材中立原型、Tier 0–5 對照 |
| M2：本機 MVP 完成 | 8/16 | FastAPI、memory repository、mock storyteller、核心 tests |
| M3：Tier 0 AWS 可玩 | 8/20 | 公開 Web、private DB、Bedrock 一回合、資料持久化與安全證據 |
| M4：Tier 1–2 完成 | 8/25 | CloudWatch／SSM incident Demo、三組件 E2E 與網段證據 |
| M5：組件化與自動部署完成 | 8/31 | private workers 非同步 E2E、自動部署、健康檢查與 rollback 成功 |
| M6：最終交付 | 9/6 | Demo、架構圖、證據索引、secrets／截圖稽核與清理計畫完整 |

## 關鍵路徑

```text
核准 Spec
  → FastAPI monolith + tests
  → Tier 0 AWS vertical slice
  → logs／SSM 與 incident data
  → 組件切割
  → container／pipeline
  → bounded Support Agent extension
  → 最終 Demo
```

## 延誤時的縮減原則

- 不犧牲已核准範圍的安全、費用或證據關卡來換取速度。
- Tier 2 只保留 Web/API、Story Worker、Data 三組件與一條 E2E 流程。
- Tier 3 只保留一條主分支自動部署 pipeline。
- Tier 4 五服務與完整 Tier 5 已移至 future roadmap，不自動開工。

## 繳交日

2026-09-07：提交 GitHub、已實作的 AWS 組件化與自動部署成果、架構圖、成功／負面驗證截圖、README、甘特圖、checkpoints、Demo 與清理紀錄。
