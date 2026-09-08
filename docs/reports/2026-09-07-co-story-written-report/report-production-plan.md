# 共演計劃 AWS 雲端工程專題報告製作規劃

## 報告定位

本報告是一份給人閱讀的 AWS 雲端工程期末專題報告。主要讀者是授課講師與專題評審，他們具備基本 AWS 知識，但不預設知道「共演計劃」的產品背景、開發歷程或 repository 治理方式。次要讀者是同班學員與技術面試者，他們需要從報告理解系統解決的問題、服務選型、實作結果與限制。

正文不對 Agent 下指令，也不放入 branch、task packet、handoff、驗收 routing 等內部工作語言。Agent 僅在開發方法與風險控管中作為受限制的協作工具說明。內部證據索引、分支邊界與檔案清單移至附錄或編輯底稿，不進入一般敘事。

## 報告結構

最終成果採一冊報告，正文分為六章，另含摘要、參考資料與附錄。正文建議約三十五至四十五頁，附錄依證據數量另計。

### 摘要

以一頁說明產品問題、AWS 解法、完成成果與主要限制。摘要不羅列所有服務，應讓讀者先理解本專題已在 AWS 建立可玩、可觀測、可維運且可回復的多人 AI 故事系統。

### 第一章 緒論

說明多人文字 RPG 的使用情境、開發動機、專題目標、範圍與報告結構。這一章回答「為什麼要做」與「本次做到哪裡」，不談 repository 治理細節，也不使用 Tier 0 至 Tier 5 作為章節骨架。

### 第二章 需求分析與系統設計

整理玩家流程、功能需求、非功能需求、主要風險與系統邊界。應交代房間、角色、回合、故事結果、資料持久化、重複請求、模型失敗與人工維運等需求，並以一張產品流程圖與一張 current production 架構圖建立後續閱讀基礎。

### 第三章 AWS 架構與服務整合

說明 VPC、公私 subnet、EC2、RDS PostgreSQL、IAM、S3、CloudFormation、CloudWatch、SSM、SQS／DLQ、Publisher、兩台 private Worker、Bedrock Nova Lite、Docker、ECR 與 GitHub OIDC／Actions 如何組成同一套系統。每個服務依序回答選用原因、放置位置、權限或網路邊界、實際用途及限制。

### 第四章 系統實作

沿著一次玩家回合說明 Web／API、PostgreSQL、Publisher、SQS、Worker 與 Bedrock 的處理順序，再補充 migration、idempotency、fencing、失敗重試與 Support Widget 的真實能力。Support Widget 應明確寫成具引用規則回答與本機草稿能力的 bounded extension，不稱為 RAG 或自由對話 Agent。

### 第五章 測試部署與維運

說明 strict TDD、CloudFormation template 與 Change Set、版本控制、GitHub Actions、OIDC、Trivy、immutable ECR digest、production approval、SSM release、health gate、rollback、CloudWatch 監控與事件診斷。Agent 的角色放在本章方法段落，限於需求整理、測試、診斷建議與證據彙整；production 權限仍由人掌握。

### 第六章 成果評估與結論

以可玩流程、四人試玩、監控資料、部署結果、安全邊界與回復能力評估成果。結論應區分已證明的結果、尚未觀察的風險與未部署的概念延伸。Route 53、CloudFront／CDN、ELB／ASG、SNS、App Runner、API Gateway、Lambda、SageMaker、DynamoDB、Step Functions、Bedrock Knowledge Bases／RAG 只在本章末段以「未部署的學習延伸」呈現。

### 參考資料與附錄

參考資料包含 AWS 官方文件與專案 ADR。附錄保存測試摘要、證據索引、CloudFormation 資源表、版本與 release 對照、去識別化聲明，以及不適合放在正文的治理資訊。

## 證據圖片配置

圖片分為「說明圖」與「實機證據」兩類。產品畫面、架構圖、流程圖與 Demo 路徑用來協助讀者理解，不單獨證明 AWS 資源或 production 狀態；CloudFormation、CloudWatch、SSM、OIDC、ECR 與 IAM 的去識別化截圖才用來支持具體完成主張。正文若使用說明圖，圖說必須標明其用途，並在相鄰段落連到對應的實機證據。

既有十四張規劃圖片皆為 `1920×1080`，目前未發現明顯裁切、文字溢位或元件重疊。後續依章節主張選擇必要圖片，避免簡報型示意圖取代 AWS 驗收證據。尤其自動部署與維運章節，應優先呈現 Change Set、OIDC／Trivy／ECR digest／SSM release chain，以及 CloudWatch Dashboard 與核准後的 SSM 健康檢查。

| 圖號建議 | 章節 | 圖片來源 | 圖片要證明的事情 | 使用方式 |
|---|---|---|---|---|
| 圖 1 | 第一章 | `docs/reports/2026-09-02-co-story-final-report/site/public/evidence/gameplay-evidence.png` | 系統已具多人房間、故事、回合與規則結果介面 | 裁去無關邊緣，保留三欄關係；房間碼持續遮蔽 |
| 圖 2 | 第二章 | `docs/reports/2026-09-02-co-story-final-report/site/public/diagrams/production-architecture.svg` | current production 的元件與資料流 | 重新匯出為向量或高解析 PNG，逐項核對 current facts |
| 圖 3 | 第三章 | `docs/screenshots/phase0-tier0-network-change-set.png` | VPC 網路由 CloudFormation Change Set 建立 | 裁切至變更項目與狀態；不露出 account 或資源識別碼 |
| 圖 4 | 第三章 | `docs/screenshots/phase0-tier0-private-db-route.png` | DB subnet 沒有 public internet route | 放大 route table 區域並加簡短圖說 |
| 圖 5 | 第三章 | `docs/screenshots/phase0-tier0-rds-internet-access-disabled.png` | RDS PostgreSQL 未公開連線 | 與圖 4 相鄰排列，避免縮到無法辨讀欄位 |
| 圖 6 | 第三章 | `docs/screenshots/phase0-tier0-ssm-managed-node-online.png` | EC2 已由 SSM 管理 | 保留 Online 與平台資訊；遮蔽 instance ID |
| 圖 7 | 第四章 | `docs/evidence/2026-08-20-tier0-four-player-trial/bedrock-invocations.png` | 試玩期間確有 Bedrock invocation | 與文字中的試玩時段與限制一併說明 |
| 圖 8 | 第四章 | 待製作的 async sequence diagram | 202、Publisher、SQS、Worker、Bedrock、RDS 與 polling 的順序 | 由 canonical evidence 繪製，不用 Console 拼圖代替流程圖 |
| 圖 9 | 第五章 | `docs/evidence/2026-08-25-tier1-completion/system-dashboard.png` | CloudWatch dashboard 已收集 EC2 memory 與 disk 指標 | 保留座標、圖例與時間；圖說說明觀察範圍 |
| 圖 10 | 第五章 | `docs/evidence/2026-08-24-tier1-aiops-agent/ssm-approved-health-check.png` | 人工批准後由 SSM 執行健康檢查 | 保留 Success、response code、live 與 ready 結果 |
| 圖 11 | 第五章 | `docs/evidence/2026-08-26-tier3-control-plane/github-oidc-provider.png` | GitHub Actions 使用 OIDC audience | 與文字中的 repository／branch trust 限制搭配 |
| 圖 12 | 第五章 | `docs/evidence/2026-08-26-tier3-control-plane/ecr-repository-security-settings.png` | ECR immutable、AES-256、scan on push | 維持遮蔽後版本，不另抄完整 ARN |
| 圖 13 | 第五章 | `docs/evidence/2026-08-26-tier3-control-plane/deploy-role-policy-simulator.png` | 不必要權限遭拒絕 | 只呈現一個代表性 negative test，其他結果寫入附錄 |
| 圖 14 | 第五章 | `docs/evidence/2026-08-26-tier3-control-plane/stack-resources-create-complete.png` | control plane 資源建立完成 | 作為 CloudFormation 結果證據，不當作架構圖 |

目前缺少適合正文的 sanitized GitHub Actions 成功流程、Trivy 掃描結果、SQS／DLQ 與兩台 Worker production 狀態圖片。若最終無法補圖，正文使用文字證據與簡化流程圖，不以舊候選簡報截圖替代。

## 文字規範

正文以「本專題」或「我們」為敘事主詞，語氣是學生向講師說明設計與成果。段落先提出問題或結論，再說明選擇、實作、證據與限制。服務名稱保留英文，第一次出現時補上中文用途；內部縮寫與機制第一次出現時用一句話解釋。

每段以三至六句為原則，一段只處理一個主題。正文避免工作指令、檔案路徑、commit SHA、branch 名稱與「驗收 routing」等編輯語言；必要的精確識別資訊移到附錄。減少口號、過度形容、密集條列與轉折否定句，優先直接陳述功能、證據及限制。事實、推論、限制與未來建議應分開寫，測試結果只支持其實際觀察範圍。

## 圖文排版規範

最終 DOCX 使用 A4 直式。建議上、下與右側邊界為 2.5 公分，左側裝訂邊為 3 公分。正文使用可讀的繁體中文字型 12 pt、1.5 倍行距、首行縮排兩個全形字；標題使用無襯線字體並維持黑色。頁碼置於頁尾，圖表依章編號。

標題不得單獨留在頁尾，標題至少與後續兩行正文同頁。啟用段落的 widow／orphan control，避免單字成行與單行成頁。全形標點符號視為一個字，不使用懸掛標點將逗號、句號或括號推出文字邊界。若一行只剩一至二個中文字或標點，優先調整前一句文字或段落寬度，不以縮小正文字級解決。

圖片原則上置於相關說明之後，圖與圖說保持同頁。單張圖片寬度以版心的百分之七十五至一百為範圍；Console 截圖若欄位太小，應裁切重點或拆成兩張，不把整張畫面縮到無法閱讀。每張圖說包含「圖號、證明內容、必要限制」，來源放在圖說後或參考資料，不在圖片上疊加大段文字。

表格只用於比較服務、需求、測試結果或風險，不把長篇敘述塞入儲存格。跨頁表格要重複表頭，圖表前後保留自然段落間距。最終 DOCX 必須逐頁 render 成 PNG，檢查中文換行、全形標點、圖說分頁、圖片解析度、表格跨頁與空白頁，再依檢查結果修正。

## 同一對話內的製作階段

書面報告全程在目前對話內完成，不建立分支對話或另外委派任務。為控制每輪篇幅，內容依下列階段逐步產出；每一階段完成後先確認事實與風格，再繼續下一階段。

1. 摘要、第一章與第二章。來源限於 MVP Spec、ADR-0008、產品流程文件與 production architecture，不加入 Agent 工作指令。
2. 第三章 AWS 架構與服務整合。來源限於 network、RDS、compute、CloudFormation、CloudWatch、SSM 與成本安全證據。
3. 第四章系統實作。來源限於 async flow、Publisher、SQS／DLQ、Worker、Bedrock、migration 與 Support Widget canonical evidence。
4. 第五章、第六章與證據圖片稽核。來源限於 TDD、Tier 3 delivery、CloudWatch／AIOps、四人試玩與 final production evidence；所有未部署服務集中標示。
5. 將確認過的內容整併成同一份 Markdown 母稿，進行跨章去重、架構一致性與 R3 安全敘述審查。
6. 母稿確認後建立 DOCX，執行 render、逐頁視覺 QA、修正與 PDF 輸出。
