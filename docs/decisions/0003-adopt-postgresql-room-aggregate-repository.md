# ADR-0003：PostgreSQL 採 Room aggregate repository

- 狀態：Accepted
- 日期：2026-08-10
- 決策者：專題開發者

## 背景

本機 MVP 已以 `RoomRepository` port 管理完整 `Room` aggregate，但目前只有 process-local `MemoryRoomRepository`。FastAPI process 停止後，房間、玩家、角色、回合、骰點與故事都會遺失，不符合 MVP 與 Tier 0 private data layer 的完成條件。

目前 domain mutation 一律載入整個 `Room`、套用規則後再儲存整個 aggregate。若在持久化第一版立刻拆成 rooms、players、characters、actions、results、stories 多組 table，會在沒有查詢需求的情況下擴大 mapping、transaction 與 migration 範圍。

## 決策

1. Tier 0／本機 MVP 使用 PostgreSQL，並讓 `MemoryRoomRepository` 與 `PostgresRoomRepository` 通過同一組 contract tests。
2. `rooms` table 保存：
   - `id text primary key`
   - `room_code text not null unique`
   - `status text not null`
   - `version integer not null`
   - `payload jsonb not null`
   - `created_at timestamptz not null`
   - `updated_at timestamptz not null`
3. `payload` 保存完整 `Room` aggregate；只保存 session token hash，不保存原始 Host／Player session token。
4. `id`、`room_code`、`status` 與 `version` 保留為明確欄位，供唯一性、路由查找、基本維運與未來 optimistic locking 使用；repository hydrate 時以 payload 為完整 domain 資料來源，並驗證索引欄位一致。
5. Migration 使用版本化 SQL 與最小 migration runner，不為單一 aggregate table 引入 ORM。PostgreSQL driver 使用 Psycopg 3。
6. 未設定 `DATABASE_URL` 時維持 `MemoryRoomRepository`；只有明確設定時才建立 PostgreSQL adapter。設定值不得寫死或 commit。
7. Migration 不在每個 Web worker 啟動時自動執行；本機測試與未來部署流程以獨立 migration command 先行套用。
8. 本機 integration 使用可清理的 PostgreSQL container；未操作 AWS。未來 RDS 只替換連線端點與 secret 來源，不改 application port。

## Transaction 與一致性邊界

- 目前 `RoomService` 採 `get → domain mutation → save`，API 會檢查 client 傳入的 room version。
- 本切片的目標是 durability 與 process restart recovery；Tier 0 單 Web process 沿用現有行為。
- 多 Web process 下，現有 port 尚不能保證讀取與寫入間的原子 compare-and-swap。進入多 process／Tier 2 前，必須擴充 repository／unit-of-work contract，以 `version` conditional update 或 transaction lock 防止 lost update。
- `MemoryIdempotencyStore` 仍是 process-local；跨 restart 的 idempotency record persistence 不包含在本切片，必須作為獨立安全切片處理，不得宣稱已解決跨 restart replay。

## Contract 必驗證行為

- `save → get` 完整 round-trip。
- `get_by_code`、不存在資料與 room code 唯一性。
- 再次儲存相同 room ID 能更新 version 與完整 aggregate。
- 回傳物件與 repository 內部狀態互相隔離。
- world、players、characters、round、progress／danger、dice results、story entries、session hashes 均無資料遺失。
- migration 可由空資料庫建立 schema。
- 使用同一 PostgreSQL 啟動第二個 FastAPI process 後仍能恢復 canonical state。

## 後果

正面：

- 對現有 domain 與 application port 的改動最小。
- 單一 row update 能保存完整 Room aggregate，符合目前一致性邊界。
- 可在本機 PostgreSQL 與 private RDS 間重用 adapter。
- `room_code／status／version` 仍可被索引與監控。

代價：

- JSONB 不適合大量跨房間分析，也不提供細粒度 relational constraint。
- aggregate 增大後，每次 mutation 都會更新完整 payload。
- 未來 Tier 4 微服務拆分時需要資料所有權重整或事件化遷移。

## 不採用方案

- SQLite：無法等價驗證 PostgreSQL JSONB、locking 與未來 RDS 行為。
- 立即全面正規化：目前沒有足夠查詢需求，會顯著放大 MVP 時程與 mapping 風險。
- DynamoDB：與目前課程 private relational data layer、PostgreSQL 規劃及既有 repository 演進路線不一致。
- 啟動時自動 migration：多 worker 可能競爭，部署責任不清楚。

## 回復方式

- 未設定 `DATABASE_URL` 即回到 Memory adapter。
- 本機測試完成後停止並刪除專題 PostgreSQL container／volume。
- migration 只作用於明確命名的專題測試資料庫，不操作其他 database。
