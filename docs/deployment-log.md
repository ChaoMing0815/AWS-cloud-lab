# 部署紀錄

本文件用來記錄每次 AWS 建置、修改、測試與 Demo 準備。講師或面試官詢問「你做了什麼、為什麼這樣做」時，可用此文件回溯。

## 基本資訊

| 項目 | 內容 |
| --- | --- |
| 專題名稱 | AWS WordPress AIOps Platform |
| 主線題目 | P0-2 WordPress Web/DB 分離 |
| 延伸題目 | P1-2 LangChain 維運 Agent、P1-3 SSM 遠端操作、P3 CI/CD |
| AWS Region | 待確認 |
| VPC CIDR | 待確認 |
| Public Subnet CIDR | 待確認 |
| Private Subnet CIDR | 待確認 |
| EC2 規格 | 待確認 |
| RDS 規格 | 待確認 |

## 變更紀錄

| 日期 | 階段 | 變更內容 | 驗證方式 | 截圖 |
| --- | --- | --- | --- | --- |
| 2026-07-15 | Phase 0 | 建立專題文件、Agent 規範、架構圖與截圖目錄 | GitHub repository 文件可讀 | 待補 |

## AWS Budget Alarm

| 項目 | 狀態 |
| --- | --- |
| 是否已建立 | 尚未確認 |
| 預算金額 | 待確認 |
| 通知 Email | 待確認 |
| 截圖 | 待補 |

## Phase 1：WordPress Web/DB 分離

### VPC

| 項目 | 設定 |
| --- | --- |
| VPC ID | 待補 |
| CIDR | 待補 |
| Public Subnet | 待補 |
| Private Subnet | 待補 |
| Internet Gateway | 待補 |
| NAT Gateway | 待評估 |

### EC2 WordPress

| 項目 | 設定 |
| --- | --- |
| Instance ID | 待補 |
| AMI | 待補 |
| Instance Type | 待補 |
| Public IP / DNS | 待補 |
| Security Group | 待補 |

### RDS MySQL

| 項目 | 設定 |
| --- | --- |
| DB Identifier | 待補 |
| Engine | MySQL |
| Instance Class | 待補 |
| Public Access | 必須為 No |
| Security Group | 只允許 Web SG 連 3306 |

## 驗收紀錄

| 檢核項目 | 狀態 | 證據 |
| --- | --- | --- |
| WordPress 可公開瀏覽 | 待驗證 | 待補 |
| RDS 位於 private subnet | 待驗證 | 待補 |
| DB 無法被外網直接連線 | 待驗證 | 待補 |
| Web SG 可連 DB:3306 | 待驗證 | 待補 |
| WordPress 發文後資料仍存在 | 待驗證 | 待補 |

## Demo 筆記

待補。

