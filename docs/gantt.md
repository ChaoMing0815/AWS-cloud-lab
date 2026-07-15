# 甘特圖時程

本時程依照講師要求的繳交格式整理，重點是每週都要有可驗收的進度。

## 6 週計畫

| 任務 | W1 | W2 | W3 | W4 | W5 | W6 |
| --- | --- | --- | --- | --- | --- | --- |
| 確認題目與架構設計 | X |  |  |  |  |  |
| AWS 帳號安全、Budget Alarm、IAM 檢查 | X |  |  |  |  |  |
| VPC、public subnet、private subnet、routing | X | X |  |  |  |  |
| EC2 WordPress 部署 |  | X | X |  |  |  |
| RDS MySQL 建置與 Web/DB 串接 |  |  | X |  |  |  |
| Security Group 收斂與連線測試 |  |  | X | X |  |  |
| CloudWatch logs、metrics、dashboard、alarms |  |  |  | X | X |  |
| SSM Session Manager 與 Run Command |  |  |  | X | X |  |
| LangChain 或 AI 維運 Agent 原型 |  |  |  |  | X | X |
| 異常模擬與修復 Demo |  |  |  |  | X | X |
| README、截圖、架構圖 | X | X | X | X | X | X |
| 最終 Demo 演練與資源清理計畫 |  |  |  |  |  | X |

## 里程碑

| 里程碑 | 目標時間 | 驗收標準 |
| --- | --- | --- |
| M1：專案治理完成 | W1 結束 | GitHub repo、專題規劃、Budget Alarm、初版架構 |
| M2：網路基礎完成 | W2 結束 | VPC 具備 public/private subnet 與 routing 設計 |
| M3：Tier 0 系統可運作 | W3 結束 | WordPress 可公開瀏覽，且資料寫入 private RDS |
| M4：安全與可觀測性完成 | W4 結束 | DB 位於 private、SG 收斂、CloudWatch 可看到資料 |
| M5：維運延伸完成 | W5 結束 | SSM 與 AI 分析原型可支援異常處理 |
| M6：期末 Demo 完成 | W6 結束 | Demo、截圖、README、架構圖、檢核清單完整 |

## 每週重點

### Week 1

- 確認題目與範圍
- 建立 GitHub 文件
- 設定 AWS Budgets 告警
- 草擬 VPC 與應用架構

### Week 2

- 建立 VPC、subnet、route table、IGW，並評估是否需要 NAT
- 建立 EC2 基礎環境
- 保存 AWS 截圖

### Week 3

- 安裝與設定 WordPress
- 建立 RDS MySQL
- 串接 WordPress 與 RDS
- 驗證文章資料可持久保存

### Week 4

- 收斂 Security Group
- 確認 RDS 不對外公開
- 加入 CloudWatch logs、metrics、dashboard、alarms
- 啟用 SSM，降低對 SSH 的依賴

### Week 5

- 建立 AI 維運 Agent 原型
- 讀取 CloudWatch logs 或健康檢查輸出
- 模擬網站或 DB 異常
- 使用 SSM 執行維運操作

### Week 6

- 整理最終 README
- 補齊架構圖與網路拓樸
- 整理截圖
- 依照檢核清單演練 Demo
- Demo 後終止不必要資源
