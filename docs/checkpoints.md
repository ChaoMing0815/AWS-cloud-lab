# 專題檢核清單

Demo 當天可用這份清單逐條驗收。

## 講師最低要求

- [ ] 已保存成功部署截圖。
- [ ] 已保存 AWS VPC 截圖。
- [ ] 已包含架構圖。
- [ ] README 說明專題內容與 Demo 方式。
- [ ] GitHub repository 內有完整專題文件。

## 費用控管

- [ ] 建置基礎架構前已設定 AWS Budgets 告警。
- [ ] 盡量使用 Free Tier 或最小合理規格。
- [ ] 除非有明確目的，否則避開高費用服務。
- [ ] 已記錄 Demo 後資源清理或 terminate 計畫。

## P0-2 WordPress Web/DB 分離

- [ ] VPC 具有 public subnet 與 private subnet。
- [ ] WordPress Web server 位於 public subnet。
- [ ] Database 位於 private subnet。
- [ ] Database 無法被外網直接連線。
- [ ] Security Group 只允許 Web server 的 Security Group 連 DB:3306。
- [ ] WordPress 網站可從 public internet 瀏覽。
- [ ] 可以建立 WordPress 文章，重新整理後文章仍存在。
- [ ] 架構圖標示 VPC、subnet、EC2、RDS 與 Security Groups。

## 安全性

- [ ] 資料庫連接埠沒有對 public internet 開放。
- [ ] SSH 沒有大範圍對外開放。
- [ ] 沒有 secrets 被 commit 到 GitHub。
- [ ] 憑證存放於 Parameter Store、Secrets Manager、環境變數或 AWS 管理設定。
- [ ] IAM 權限盡量符合最小權限原則。

## 可觀測性

- [ ] 已設定 CloudWatch Agent 或等效 logging 路徑。
- [ ] Application logs 或 system logs 可在 CloudWatch 查看。
- [ ] 可以看到基本 metrics。
- [ ] Dashboard 或截圖能呈現健康狀態。
- [ ] 至少設定一個 alarm 或告警規則。

## P1-2 WordPress + AI 維運 Agent

- [ ] Agent 可以讀取 logs 或健康狀態。
- [ ] Agent 可以說明模擬的 WordPress 500 或 DB 連線異常。
- [ ] Agent 能回覆清楚的修復建議。
- [ ] Demo 展示偵測、分析、建議動作。
- [ ] Agent 部署在 AWS，例如 EC2 或 Lambda。

## P1-3 AWS SSM 遠端操作

- [ ] EC2 已掛載必要的 SSM IAM role。
- [ ] Session Manager 可以在不開 public SSH 的情況下連線。
- [ ] Run Command 可以對一台或多台 EC2 執行指令。
- [ ] 正常維運流程不需要 public SSH key。
- [ ] 可透過 SSM 展示修復操作。

## 選配 P3 CI/CD

- [ ] 應用或支援服務具有 Dockerfile。
- [ ] GitHub Actions 可以 build image。
- [ ] Image 可以推送到 ECR。
- [ ] 可從 GitHub 觸發部署。
- [ ] Demo 展示 code change 上線到 AWS。

## 最終 Demo 檢核

- [ ] 展示公開的 WordPress 網站。
- [ ] 展示 AWS 架構與 VPC 截圖。
- [ ] 展示 RDS private isolation。
- [ ] 展示 WordPress 文章資料持久保存。
- [ ] 展示 CloudWatch logs 或 metrics。
- [ ] 展示 AI 對異常的分析。
- [ ] 展示 SSM 操作。
- [ ] 展示最終 README 與架構圖。
- [ ] 說明費用控管與資源清理方式。
