# Tier 0 RDS 暫停節費驗證摘要

- Scope／risk：R3 成本與可用性；只暫停既有 private PostgreSQL RDS，不刪除資料或 stack。
- 執行者／介面：使用者透過 AWS Console 操作；Agent 未執行 AWS CLI、SSM 或其他 AWS 寫入。
- Region／resource：Tokyo `ap-northeast-1`；既有 `co-story-tier0-rds` stack 的 Single-AZ PostgreSQL `db.t4g.micro`。
- 結果：使用者於 2026-08-22 回報 DB instance 狀態為 `Stopped`。
- Cost：停止期間不計 DB instance hours；provisioned storage 與 backup storage 仍持續計費。
- Availability：依賴 PostgreSQL 的 application readiness／遊戲操作在 RDS 重啟前不可用。
- Persistence：停止不刪除 DB data、endpoint、parameter group 或 Security Group。
- Boundary：EC2、public IPv4、HTTPS certificate、IAM、VPC、S3、Secrets Manager 與 Bedrock 未列入本次操作。
- Automatic restart：RDS 最多連續停止 7 天；若未人工啟動，最晚約 2026-08-29 由服務自動啟動。
- Rollback：在 RDS Console 對同一 DB instance 選擇 `Start`，等待 `Available` 後再驗證 application readiness。
- Evidence limitation：目前依使用者即時 Console 回報記錄，尚無去識別化狀態截圖或精確停止時間。
- 官方依據：[Stopping an Amazon RDS DB instance temporarily](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_StopInstance.html)。
