# 專題 Agent Skill 驗證

- Skill：`.agents/skills/operate-aws-final-project`
- 日期：2026-08-06

## 驗證結果

| 驗證 | 結果 |
| --- | --- |
| `quick_validate.py` | `Skill is valid!` |
| Shell 語法 `bash -n` | 通過 |
| 唯讀盤點腳本 `--help` | 通過 |
| `SKILL.md` TODO 搜尋 | 無殘留 TODO |
| 可執行權限 | `-rwxr-xr-x` |

## 最小觸發測試

測試提示：

> 使用 `$operate-aws-final-project` 先盤點 AWS 成本與 IAM，再建立 EC2 應用 role，保存證據並更新部署紀錄。

靜態觸發檢查：通過。Skill frontmatter 的 description 明確涵蓋 AWS 成本／資源盤點、IAM Identity Center、最小權限 roles、部署紀錄、截圖與 checkpoints。

限制：本工作階段不會熱載入剛建立的專案 Skill；應在下一個 Codex 任務以以上提示執行一次實際觸發確認。

## 2026-08-07 成本事件後重新驗證

Skill 已新增 Organizations／Control Tower／Identity Center organization instance 的 Account plan 與 Credits 硬性關卡。

- 原始 Skill 的官方 `quick_validate.py` 驗證結果仍為通過。
- 本次執行環境的 system／workspace Python 缺少 `PyYAML`，官方 validator 無法啟動；未為此安裝套件。
- 以 Ruby YAML 重新檢查 frontmatter：通過。
- 唯讀盤點腳本 `bash -n`：通過。
- TODO／TBD 殘留搜尋：無。
- `git diff --check`：通過。

本次只修改 `SKILL.md` 指令本文，未變更已由官方 validator 驗證過的 frontmatter name／description。
