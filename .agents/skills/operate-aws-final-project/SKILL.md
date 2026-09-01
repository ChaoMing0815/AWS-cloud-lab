---
name: operate-aws-final-project
description: Safely plan, build, inspect, verify, and document the AWS final project for a multiplayer AI text RPG. Use when Codex works in this repository on AWS cost or resource inventory, IAM Identity Center, least-privilege roles and policies, application infrastructure, CloudWatch, SSM, CI/CD, RAG, Agentic AI, architecture diagrams, deployment records, screenshots, or project checkpoints.
---

# 維運 AWS 期末專題

## 核心流程

1. 先讀取 `AGENTS.md`、`docs/product/source-of-truth.md` 與 `docs/handoffs/CURRENT.md`，再依任務路由讀取直接相關文件。只有全域規劃、課程對照、final review 或文件衝突調查，才載入 README、Project Brief、project plan、gantt 與 checkpoints 全集。同一 task 內不得重讀未變更文件。
2. 以已接受的 ADR 為最新決策。若舊文件仍描述 WordPress，標示為待遷移內容，不得用它覆蓋多人 AI 文字 RPG 的決策。
3. 任何 AWS CLI（包含唯讀）都必須先取得使用者對 bounded change batch 的人工核准；不得因命令看似唯讀而自動執行。核准後先完成成本、安全、目前 principal、Region、資源與 IAM 唯讀盤點，使用 `scripts/aws-readonly-inventory.sh` 保存不含 secrets 的原始證據。
   - 涉及 AWS Organizations、Control Tower 或 IAM Identity Center organization instance 時，必須先驗證 Account plan 與 Credits。若為 Free plan，立即停止：建立／加入 Organization 會自動升級 Paid plan、使 Free Tier credits 立即失效且不能降級。列出不建立 Organization 的替代方案並取得使用者對此特定後果的明確確認，普通的「確認啟用」不算充分同意。
4. 每個 AWS change batch 只建立一次 change envelope：account、principal、Region／profile、精確資源、IAM 邊界、費用上限、驗證、rollback 與清理責任。相同 task 內只要 envelope 未擴張即可沿用；account／principal／Region、權限、成本級別、外部傳輸或不可逆性改變時才重新核准。
   - 帳務、Root、MFA、Email 驗證、權限擴張、外部傳輸、production deploy 與不可逆動作必須明確列入人工核准，不得被一般 envelope 默認涵蓋。
5. 依 ADR-0008 執行目前 final delivery scope：可玩 MVP、CloudWatch／SSM、Web／Worker／Data 組件化與 Docker／ECR／GitHub OIDC／SSM 自動部署。Tier 4 微服務與完整 Tier 5 只是 future roadmap，未經新核准不得當成 backlog 或建立資源。
6. 每個 batch 結束時一次執行正面／負面驗證並保存 sanitized evidence；`deployment-log.md` 只記實際 AWS／環境 batch，`checkpoints.md` 與架構文件只在 milestone／Tier gate 改變時更新。

## 專題邊界

- 將 2026-09-07 視為繳交期限。
- 建立 3–5 人、回合制、純文字 MVP；保存房間、玩家、角色、回合與原創劇情。
- 將 AWS 上可驗證的部署視為完成條件，不把只有本機可跑的 Demo 當成最終成果。
- 使用繁體中文撰寫給講師、同學、面試官與使用者閱讀的文件；保留 AWS 服務、程式碼與識別名稱的英文。
- 優先使用最小合理規格；在建立可能計費的資源前說明預估計費面、Budget 狀態與清理計畫。

需要完整背景與衝突處理時，讀取 `references/project-context.md`。

## IAM 與憑證規則

- 人員登入優先使用 IAM Identity Center、MFA 與短期 SSO 憑證。
- 不建立日常使用的 IAM user 長期 Access Key；不在輸出、證據或版本庫保存 password、secret、token、OTP 或 session credential。
- Root 只用於帳號層級必要操作，並確認 MFA。
- 不把 `AdministratorAccess`、`IAMFullAccess` 或服務級 Full Access 掛到應用程式 role。
- 對標準基礎能力使用合適的 AWS managed policy；對專案資源使用限定 ARN、動作與條件的 customer managed policy。
- 將 `iam:PassRole` 限定到明確 role ARN。將 trust policy 限定到實際 principal、service、repository、branch 或 account。
- 只有選定 Lambda 時才建立 Lambda role；只有啟用 CI/CD 時才建立 GitHub OIDC deploy role。
- 優先使用 SSM，避免 public SSH。不得為維運方便開放 `0.0.0.0/0:22`。

設計或驗證 Identity Center、permission set、application role、operator role 或 GitHub OIDC role 時，必須讀取 `references/iam-boundaries.md`。

## AWS change envelope 關卡

每個 bounded batch 開始時確認：

- 目前 principal、account ID、Region 與 SSO profile 已明確。
- Budget 告警、當月成本、現有資源、CloudTrail／Event history 與 IAM 現況已有時間戳證據。
- Account plan 與 Credits 已確認；不得只因 Organizations 或 Identity Center 服務本身不收費，就忽略建立 Organization 對 Free plan 與 credits 的不可逆影響。
- 變更集只包含已選定架構需要的物件；名稱、trust policy、permissions policy 與 tags 已列出。
- 已檢查沒有長期 Access Key、萬用 `iam:PassRole`、應用程式管理員權限或未限定的 secret 讀取。
- 已定義正面測試、負面測試、回復方式與清理責任。

若任何一項未知，先停止 batch 並完成盤點或請使用者處理必要互動。同一 task 中，若 account、principal、Region／profile、核准資源集合、權限邊界與成本級別均未改變，不為每個 AWS API call 重做完整盤點或核可；每個 command 只驗證與 envelope 的 delta。任何 envelope 擴張都必須重新人工核准。

## 證據與完成定義

- 每個 AWS batch 將必要且 sanitized 的 CLI 原始輸出保存到 `docs/evidence/<日期>-<階段>/`；不為每個 command 建立獨立 evidence。
- 將 Console 畫面保存到 `docs/screenshots/`，避免包含 Email、account alias、Access Key ID、token 或其他敏感資訊。
- Batch 結束後在部署紀錄寫一次時間、principal 類型、Region、變更、驗證、證據路徑、費用影響與回復方式。本機 coding／TDD 不寫 deployment log。
- 不因檔案存在就標示完成；只有 AWS 狀態與驗證證據一致時才勾選 checkpoint。
- 驗證 IAM policy 語法與 Access Analyzer；在 CloudTrail 有足夠活動後依實際使用縮減權限。
- 完成階段時，記錄未完成項目、阻塞原因與下一步。

使用證據時讀取 `references/evidence-and-validation.md`。

## 最小觸發範例

`使用 $operate-aws-final-project 先盤點成本與 IAM，再建立 EC2 應用 role，保存證據並更新部署紀錄。`
