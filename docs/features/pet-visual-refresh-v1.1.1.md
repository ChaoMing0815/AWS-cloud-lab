# 寵物視覺 refresh v1.1.1

- 狀態：Local candidate；未 push／merge／deploy
- Branch：`codex/pet-visual-refresh-v1-1-1`
- 風險：R2 可觀察 UI／responsive interaction
- 上游：2026-09-02 使用者核准與 [`approval-log.md`](../governance/approval-log.md)

## 固定範圍

- 只修改 Frontend launcher、必要的 responsive collision avoidance、UI tests與本切片文件。
- 不修改 rules retrieval、Backend、API schema、資料庫、RAG、IAM、AWS 資源或 release workflow。
- 玩家可見版本由 `Release v1.1.0` 遞增為 `Release v1.1.1`；後續每次玩家可見 patch 皆須依相同規則遞增。

## 可驗收行為

- Launcher底層保留原生`button`、ARIA、鍵盤、Esc focus return與至少44×44觸控區。
- 視覺上不呈現矩形按鈕；原創像素史萊姆使用半透明膠體、直接長在身體上的眼睛與微笑、底部果凍裙邊／偽足、陰影、跳動與獨立提示泡泡。不得使用深色螢幕臉或分離機械腳。
- 開啟dialog時停止跳動；`prefers-reduced-motion`時完全停用動效。
- 390px下核心composer進入viewport時，寵物與dialog自動停靠於控制區上方；不得遮擋action form／textarea。
- 390／768／1440均不得與topbar nav相交或造成水平溢位。

## Release 邊界

- 本機完成、PR合併與production deployment是三個獨立狀態。
- 未建立exact-main／previous-digest envelope並取得人工核准前，不得部署或把`v1.1.1`描述為production版本。
