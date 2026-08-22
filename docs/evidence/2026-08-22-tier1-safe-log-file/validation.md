# Tier 1 安全 Application JSONL File Sink 驗證摘要

- Scope／risk：R3 observability security boundary；只完成 repo-local file sink，未建立或修改 AWS resource、IAM、CloudWatch Agent 或 alarm。
- Red：`8f5aea8` 定義 allowlisted request／Storyteller JSONL；`3e33e5f` 補上 `0640`、1 MiB rotation、最多兩份 backup 與 symlink target 拒絕。
- Green：`66cf913`；設定 `CO_STORY_APPLICATION_LOG_PATH` 時，應用只將符合精確 schema 的 `co_story.request` 與 `co_story.storyteller` event 寫入檔案。
- Secret boundary：query、body、cookie、token、raw `uvicorn.access` line 與含額外欄位的 forged safe-logger event 不得進入檔案。
- File boundary：active／rotated files 權限皆為 `0640`；單檔上限 1 MiB，最多保留 active＋2 backups；既有 symlink target 會 fail closed。
- Targeted：`4 passed`（safe application file logging＋既有 structured request logging）。
- Full regression：Backend `315 passed, 8 skipped`。
- Sensitivity：移除精確欄位檢查時測試抓到 forged secret；改成 `0644` 時測試抓到權限回退；停用 symlink guard 時測試抓到未拒絕 target。三項 mutation 均已還原。
- Known warning：Starlette TestClient 對目前 httpx integration 顯示 deprecation warning，不影響本切片判定。
- Runtime boundary：未設定環境變數時不建立檔案；目前 AWS active release 尚未包含此功能。
- Cost：本切片完全在本機執行，新增 AWS 費用為 `0`。
- Next gate：CloudWatch Agent config、固定 Log Group／7 天 retention、最小權限 IAM、metric／alarm 與 SSM document 必須分開完成 TDD、估價與 bounded AWS 核准。
