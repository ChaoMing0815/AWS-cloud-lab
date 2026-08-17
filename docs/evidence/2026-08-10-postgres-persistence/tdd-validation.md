# PostgreSQL restart persistence：TDD 驗證

- 日期：2026-08-10
- 範圍：本機 PostgreSQL repository、migration、FastAPI composition 與應用重啟
- AWS：未操作，未產生雲端資源或費用

## 完成內容

- ADR-0003 決定以 PostgreSQL `rooms` aggregate JSONB 作為本機 MVP 持久層。
- 建立可重複執行的 `001_create_rooms.sql` 與 migration runner。
- Memory／PostgreSQL adapter 共用 repository contract，完整保存 room、玩家、角色、回合、骰子結果、故事與 session hash。
- `DATABASE_URL` 存在時組裝 PostgreSQL adapter；未設定時維持 Memory adapter，測試可明確注入替身。
- 第二個 FastAPI 應用實例可還原第一個實例建立的 room 與 Host／Player session。
- Demo room 在重啟時重用既有 `BONUS7`，不再觸發唯一鍵衝突。

## Red／Green 證據

| 切片 | Red | Green |
| --- | --- | --- |
| Repository injection | `99c8bac`：`create_app` 尚未接受 repository | `c49c705` |
| Migration schema | `1986aa4`：migration 不存在 | `afdb11f` |
| Migration runner | `4576e7e`：runner module 不存在 | `fa44435` |
| PostgreSQL adapter port | `4d3a038`：adapter 不存在 | `b880e0e` |
| Shared contract | `54e2b48`：PostgreSQL `save()` 尚未實作 | `08c763c` |
| Runtime composition | `c735d00`、`886da45`：`DATABASE_URL` 下仍取得 Memory adapter | `376389c` |
| Restart persistence | `a9f1529`：第二個 app 因 `BONUS7` unique constraint 啟動失敗 | `c97c7b9` |

最初 composition 測試使用 `db.invalid`，但 `RoomService` 啟動會立即建立 Demo room，因此該測試只會得到 DNS／連線錯誤，不能證明 adapter 選擇。測試已改用明確的 `CO_STORY_TEST_DATABASE_URL` 與本機臨時 PostgreSQL，重新取得有效 Red 後才實作 Green。

## 敏感度與完整回歸

- Mutation：刻意讓 PostgreSQL hydrate 丟棄 `entries`。
- 結果：共享 contract 的 PostgreSQL case 失敗，清楚指出 `entries: []` 與預期故事項目不同。
- Mutation 已還原，未提交到 Git。
- Backend：`56 passed`（包含 Memory／PostgreSQL contract、migration、composition、restart）。
- Frontend：`58 passed`。
- 已知非阻擋警告：FastAPI `TestClient` 仍顯示 Starlette/httpx 相容性 deprecation，未造成測試失敗。

## 本機資源清理

- 測試資料庫只綁定 `127.0.0.1:55432`。
- 使用 `--rm` 啟動的 `co-story-postgres-test` 已停止。
- `docker ps -a --filter name=co-story-postgres-test` 無結果，確認容器已移除。
- 測試密碼只用於臨時本機容器與命令，未寫入 repository。

## 尚未涵蓋

- 本證據驗證兩個獨立 FastAPI application instance，不宣稱已完成正式 OS／container deployment restart 演練。
- Persistent idempotency、multi-process compare-and-swap、LLM retry／fallback、AWS RDS 與 private subnet 仍屬後續工作。
