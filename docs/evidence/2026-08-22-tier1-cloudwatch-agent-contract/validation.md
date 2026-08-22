# Tier 1 CloudWatch Agent Application Log Contract 驗證摘要

- Scope／risk：R3 observability configuration；只完成 repo-local config 與 runtime path contract，未安裝 Agent、部署 release 或建立 AWS resource／IAM。
- Red：`0c166c8` 定義唯一安全 file source 與固定 destination；`7f5da34` 補上 candidate log 隔離，兩次皆因缺少目標 config／runtime contract 正確失敗。
- Green：`b347abe`；Agent config 只讀 `/var/log/co-story/application.jsonl`，送往 `/co-story/tier1/application` 的 `{instance_id}` stream。
- Source boundary：不收 `/var/log/messages`、secure／auth、Nginx access／error、萬用字元或其他 file source，也不啟用 metrics collection。
- Runtime boundary：正式 service 透過外部 runtime env 寫入唯一被收集的 JSONL；systemd 以 `LogsDirectory=co-story`、mode `0750` 建立受控目錄。
- Candidate boundary：candidate service 寫入獨立 `/var/log/co-story/candidate.jsonl`，不與 active process 共用 rotation，也不被 Agent config 收集。
- Affected：`31 passed`（Agent contract、runtime bundle、rollback、staging 與 public HTTPS release contracts）。
- Full regression：Backend `317 passed, 8 skipped`。
- Sensitivity：Agent 改收 system log、candidate 改寫正式 path、移除 active `LogsDirectory` 三項 mutation 均被測試抓到並已還原。
- Cost：本切片未連線 AWS，新增 AWS 費用為 `0`。
- Pending：Log Group／7 天 retention、Agent 安裝與啟動、最小權限 logs policy、metric filter／alarm 均尚未建立。
- Deployment：AWS active release 仍為 `tier0-20260819-ee128da`；RDS 維持使用者回報的 `Stopped`。
