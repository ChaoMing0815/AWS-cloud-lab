# 下一對話任務交接：專題 Agent Skill 與 IAM

> 本文件是 2026-08-06 的歷史交接，不代表目前執行入口。2026-08-08 之後請優先讀取 [`2026-08-08-local-mvp.md`](2026-08-08-local-mvp.md)；不得依本文件重新啟用 Organizations 或重做已完成的 Identity Center 步驟。

> 2026-08-07 更正：本交接原本要求「確認或啟用 IAM Identity Center」，但漏列新版 AWS Free plan 建立／加入 Organization 會自動升級 Paid plan、使 Free Tier credits 立即失效且不能降級。此項成本後果優先於下方 Identity Center 建議；任何後續工作不得再依原文直接建立 Organization。

- 交接日期：2026-08-06
- 期末專題繳交日：2026-09-07
- 已確定主題：部署於 AWS 的多人 AI 文字 RPG
- 今日目標：建構期末專題 Agent 所需 Skill，完成 IAM Identity Center 帳號設置，並完成專題所需 IAM roles

## 新 Agent 開工前必讀

1. `AGENTS.md`
2. `README.md`
3. `AWS_Cloud_Engineer_Final_Project_Project_Brief.md`
4. `docs/project-plan.md`
5. `docs/gantt.md`
6. `docs/checkpoints.md`
7. `docs/decisions/0001-select-multiplayer-ai-text-rpg.md`
8. 本交接文件

## 重要現況

- 選題決策已確定，不再以 WordPress 為主題。
- 目前多份舊文件仍以 WordPress AIOps 為主，屬於待遷移狀態；不可將舊文件當成最新選題決策。
- 工作樹已有使用者的未提交變更；不要 reset、checkout 或覆寫無關變更。
- 早期 Budget 畫面 `docs/screenshots/phase0-zero-spend-budget.png` 含帳號識別資訊，已列入 `.gitignore`，不得提交；公開證據改用已裁切的 `phase0-zero-spend-budget-verified.png`。
- 未確認項目：AWS Region、帳號是單一帳號或 Organizations 成員帳號、IAM Identity Center 是否已啟用、目前使用者身分、既有 roles/policies、AWS CLI SSO 狀態。

## 任務執行原則

- 本任務明確涉及建立專案 Skill，必須使用 `skill-creator` skill，並在動作前完整讀取其 `SKILL.md`。
- 不要把 IAM user 與 IAM role 當成同一種身分。
- 人員存取優先使用 IAM Identity Center 與臨時憑證；不建立日常使用的長期 Access Key。
- Root 只用於帳號層級必要操作，且必須啟用 MFA。
- 不建立單一 `AdministratorAccess` 專題帳號或超級應用程式 role。
- 任何 AWS 寫入前先做唯讀盤點，讓使用者看到將建立或修改的對象。
- 涉及費用、帳務、MFA、電子郵件驗證、權限擴張或不可逆操作時，由使用者確認或操作。
- 涉及 Organizations、Control Tower 或 Identity Center organization instance 時，先確認 Account plan／Credits；Free plan 必須停止並揭露 credits 立即失效與無法降級，不能以一般啟用確認代替知情同意。
- 所有完成的 IAM 設定都要保存驗證證據與更新部署紀錄，不只是口頭說明。

## 今日任務順序

### 1. AWS 唯讀盤點與安全前置

- 確認目前 AWS principal，不輸出憑證或 secrets。
- 確認 Region 與 account ID。
- 盤點 IAM Identity Center、users、groups、roles、customer managed policies 與 Access Keys。
- 確認 Root MFA 與 Budget Alarm；若 CLI 無法安全判斷，由使用者在 Console 驗證。
- 確認 CloudTrail 或至少 Event history 可用於後續稽核。

### 2. 建立專題 Agent Skill

使用 `skill-creator` 流程，先定義需求再建立，至少包含：

- 專題背景、MVP 邊界、截止日與繁體中文文件規範。
- AWS 成本、安全、最小權限、SSM 免 SSH 與證據保存關卡。
- 必讀文件路由與「舊 WordPress 文件不是最新選題」的衝突處理規則。
- Tier 0 優先，再演進 CloudWatch、SSM、CI/CD、RAG 與 Agentic AI。
- 執行 AWS 寫入前的成本／安全／資源盤點檢核。
- 部署紀錄、架構圖、截圖與 checkpoints 的同步更新要求。
- Skill 驗證結果與一個最小觸發測試。

### 3. IAM Identity Center

- 確認或啟用 IAM Identity Center。
- 建立專題使用者／group，建議 group 名稱：`AWSFinalProjectDevelopers`。
- 建立 permission set，建議名稱：`AWSFinalProjectDeveloper`。
- 完成 account assignment、MFA 與登入驗證。
- 設定 AWS CLI SSO profile，不建立長期 Access Key。
- 避免永久使用 `AdministratorAccess`；若 bootstrap 階段暫時需要寬權限，必須記錄理由、期限與收旂步驟。

### 4. 專題 IAM roles 與 policies

至少設計，但只建立當日架構確實需要的 roles：

- `AWSFinalProjectAppRole`：EC2 應用，使用 `AmazonSSMManagedInstanceCore`，加上限定資源的 CloudWatch、Bedrock、Secrets Manager／Parameter Store 權限。
- `AWSFinalProjectLambdaRole`：只在選定 Lambda 時建立，使用基礎執行 policy 加專案資源限定。
- `AWSFinalProjectGitHubDeployRole`：只在啟用 CI/CD 時建立；使用 GitHub OIDC，trust policy 限定 repository 與 branch，不使用 GitHub 長期 AWS keys。
- `AWSFinalProjectOperatorRole`：選配，限定 CloudWatch 讀取與受控 SSM 操作，不允許修改 IAM 或讀取 Secret 明文。

Policy 原則：

- AWS managed policies 只用於標準基礎能力，例如 `AmazonSSMManagedInstanceCore`。
- 與專案 bucket、secret、log group、queue、table、model 或 deployment target 相關的權限，使用 customer managed policies 限定 ARN。
- `iam:PassRole` 限定特定 role ARN，不允許 `Resource: "*"`。
- 不把 `AmazonBedrockFullAccess`、`AmazonS3FullAccess`、`IAMFullAccess` 或 `AdministratorAccess` 掛在應用 role。
- 優先 customer managed policy，避免大量 inline permissions policy；role trust policy 依 principal 單獨設定。
- 使用 IAM Access Analyzer 驗證 policy，有 CloudTrail 資料後再依實際活動縮減權限。

## 今日完成定義

- [ ] 專題 Agent Skill 已建立、驗證並可被觸發。
- [ ] IAM Identity Center 使用者或 group、permission set 與 account assignment 已驗證。
- [ ] MFA 與 AWS CLI SSO 登入已驗證，未用長期 Access Key。
- [ ] 實際所需的專題 roles 已建立，trust policy 與 permissions policy 已通過檢查。
- [ ] 沒有將管理員、IAM Full Access 或各服務 Full Access 授予應用程式。
- [ ] 已執行必要的正面與負面權限測試。
- [ ] 已保存不含 secrets 的 Console／CLI 驗證證據。
- [ ] `docs/deployment-log.md`、`docs/checkpoints.md` 與相關截圖索引已更新。
- [ ] 已記錄今日未完成項目、阻塞原因與下一步。

## 新對話建議開場指令

> 請依 `AGENTS.md`、`docs/decisions/0001-select-multiplayer-ai-text-rpg.md` 與 `docs/handoffs/2026-08-06-skill-and-iam.md` 開始今日任務。使用 `skill-creator` 建構專題 Agent Skill，先進行 AWS 成本與 IAM 唯讀盤點，再協助完成 IAM Identity Center 與專題所需 roles。不建立長期 Access Key，不授予應用程式 AdministratorAccess，並在每一階段保存驗證證據與更新部署紀錄。
