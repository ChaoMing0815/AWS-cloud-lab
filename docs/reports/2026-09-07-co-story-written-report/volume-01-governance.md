# 退回草稿 第一冊 從產品問題到可驗收的 AWS 系統

本檔已因受眾與專題報告定位不清而退回，只保留作為編輯歷史，不得直接併入正式報告。新版結構與寫作規格以 `report-production-plan.md` 為準。

## 1.1 專題不是把服務堆在一起

「共演計劃」是一個多人 AI 文字 RPG。玩家在同一個故事房間中建立角色、提出行動，系統保存回合狀態，並把已確定的規則結果交給故事生成流程，讓下一段敘事與玩家行為保持因果關係。這個產品問題決定了系統必須同時處理三件事：玩家需要立即看見可理解的遊戲狀態，資料需要能在服務重啟後保存，模型失敗或重複投遞時不能破壞既有回合結果。

因此，本專題的 AWS 實作不是服務清單，而是由產品風險推導出的系統邊界。Web 需要對外提供可玩的入口，PostgreSQL 必須放在 private subnet，故事工作需要與 Web process 分離，模型呼叫需要有明確的錯誤處理，而維運人員需要能透過 SSM 操作，不必依賴 public SSH。每一項服務都必須能回答「它保護哪個產品不變量」以及「失敗時如何回復」。

## 1.2 需求如何被治理成可驗收範圍

產品規則以正式 MVP Spec 為準，文件衝突與交付範圍則由 source-of-truth 索引與 ADR-0008 管理。這個治理方式避免把歷史規劃誤當成今日的驗收標準。最終交付聚焦於 AWS 上可玩的 MVP、可觀測與 SSM 維運、Web／Story Worker／Data 組件化，以及 Docker、ECR、GitHub Actions OIDC、Trivy 與 SSM release pipeline。這些項目都能以 production 狀態、測試結果或 sanitized evidence 驗證。

相對地，Route 53、CloudFront／CDN、ELB／ASG、SNS、App Runner、API Gateway、Lambda、SageMaker、DynamoDB、Step Functions 與 Bedrock Knowledge Bases／RAG，不是本次系統遺漏的必做項目。它們可以在獨立的「概念延伸／未部署」學習報告中討論選型與未來適用情境，但不能寫成現況，也不能用來否定目前交付完成度。這項區分讓報告能誠實呈現已部署能力，也避免為了湊服務數量而擴張成本與權限。

## 1.3 AWS 課程能力如何回到產品價值

網路與資料服務直接支撐「房間狀態不可遺失」：VPC 將 public app subnet 與 private DB subnets 分開，Security Group 僅允許必要的資料庫流量，RDS PostgreSQL 以 managed master password 與加密保存產品資料。EC2 與 IAM role 提供 Web runtime，SSM Session Manager 則把維運入口從 SSH 改為受控管理平面。

CloudWatch 的 logs、metrics、dashboard 與 alarm 把「玩家遇到錯誤」轉成可觀察的運維訊號。AIOps 元件可以摘要 synthetic incident、提出健康檢查建議，但不直接替人執行高風險修復；需要改變狀態的動作仍經過 human-in-the-loop。這個限制不是功能不足，而是把模型判斷與 production authority 分開，避免 AI 建議被誤當成已批准的操作。

Docker、ECR、GitHub OIDC、Actions、Trivy 與 SSM release 則支撐「可重複交付」。Workflow 先完成測試，再建立 immutable image，通過 HIGH／CRITICAL fail-closed 掃描與人工 production approval，最後以 exact digest 配合 health gate 發布；rollback 使用上一個已知 digest，不以模糊的 latest tag 取代版本識別。這使「改一行 code 可以安全到達 production」成為一條有證據的交付鏈，而不是口頭上的自動化宣稱。

## 1.4 Agent 的角色與限制

Agent 在本專題中負責協助需求治理、讀取權威文件、把產品風險轉成測試案例、執行 strict TDD 的本機驗證、檢查分支邊界、整理 sanitized evidence，以及在診斷流程中提出可供人審核的建議。它可以協助辨識文件衝突、提醒成本與權限風險，並把測試結果整理成講師可讀的交付敘述。

Agent 不取代產品 owner、AWS 操作者或 production approval。它不得自行擴張 IAM 權限、建立不可逆資源、執行未核准的 AWS change、把 synthetic incident 寫成真實 outage recovery，也不得把 deterministic Support Widget 描述成 RAG 或自由對話模型。當 evidence 不足時，正確行為是標示缺件與限制，而不是用推測補齊現況。

## 1.5 本冊驗收方式

本冊的主張應回鏈至 `docs/product/source-of-truth.md`、`docs/decisions/0008-fix-final-delivery-scope.md`、`docs/testing-strategy.md` 與 `docs/governance/parallel-branch-boundaries.md`。交付前仍須逐一確認 production evidence 的日期、來源與去識別化狀態；報告排版時，標題與段落應保持完整語意，避免單字獨占一行或單行獨占一頁，並把全形標點視為一個字計算行長與頁面容量。
