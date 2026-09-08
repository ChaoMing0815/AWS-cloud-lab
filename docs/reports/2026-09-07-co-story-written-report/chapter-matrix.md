# 約六冊章節矩陣

狀態：已停用。正式報告已改為一冊六章，本檔僅保留第一輪規劃歷史。

| 冊次 | 主軸與核心問題 | 主要章節 | AWS 整合重點 | 交付判準 |
|---|---|---|---|---|
| 第一冊 | 產品、需求與治理：為何是多人 AI 文字 RPG？ | 需求邊界、權威文件、成本／安全關卡、Agent 角色 | 以 AWS 目標反推可驗收邊界，不把未採用服務當缺口 | 需求可追溯至 ADR／MVP Spec，風險有 owner |
| 第二冊 | 網路、資料與最小安全基線 | VPC、public/private subnet、SG、RDS PostgreSQL、IAM | Web 對外、資料層私有、role／secret／免 SSH | 拓撲、Change Set、負面測試與 rollback 可核對 |
| 第三冊 | 可玩的 Web 與 AI 故事流程 | Web/API、房間／回合、Bedrock Nova Lite、失敗 UX | EC2 Web、private data path、模型呼叫受 bounded runtime 約束 | 玩家流程與 production evidence 一致 |
| 第四冊 | 非同步組件化與可靠性 | Publisher、SQS/DLQ、兩台 private Worker、idempotency、migration | Web／Worker／Data 邊界與 queue durability | 202 → polling → applied result、duplicate／failure 有證據 |
| 第五冊 | 可觀測、維運與交付自動化 | CloudWatch、AIOps、SSM、Docker、ECR、OIDC／Actions、Trivy | logs／metrics／alarm、人工批准、immutable digest release | 測試、scan、health gate、rollback 可重現 |
| 第六冊 | 產品守門、學習延伸與限制 | Support Widget、human-in-the-loop、測試效益、未部署概念延伸 | deterministic support boundary；未部署服務獨立標示 | current／future 不混淆，列出具體缺件與風險 |
