# AWS Cloud Lab

AWS 雲端工程師培訓期末專題。

本專案用來記錄與實作一個部署在 AWS 上的雲端維運平台。專題會先從可運作的雲端基礎架構開始，再逐步演進到具備 AI 輔助分析與操作能力的 AIOps 平台。

## 專題方向

建議主線：

```text
P0-2 WordPress Web/DB 分離
  -> P1-2 WordPress + LangChain 維運 Agent
  -> P1-3 AWS SSM 免 SSH 遠端操作
  -> P3 CI/CD 演化闖關
  -> 選配 P5 企業級 Agentic AI Capstone
```

這條路線可以先完成講師要求的保底題，再自然延伸到可觀測性、AIOps、安全維運、自動化與企業 AI。

## 核心目標

建立一個可以展示的 AWS 雲端維運平台，具備以下能力：

- 在 AWS 上部署可公開存取的應用程式
- 將資料庫隔離在私有網段
- 透過 CloudWatch 蒐集 logs 與 metrics
- 使用 AI 分析異常並提出修復建議
- 透過 SSM 操作 EC2，不依賴 SSH
- 完整記錄架構圖、截圖、Demo 與驗收結果

## 必備繳交格式

依照講師簡報，每個專題都必須包含：

1. 題目
2. 系統架構
3. 預期成效
4. 甘特圖時程
5. 檢核點

## 專案結構

```text
.
├── README.md
├── AWS_Cloud_Engineer_Final_Project_Project_Brief.md
└── docs/
    ├── project-plan.md
    ├── gantt.md
    └── checkpoints.md
```

## 目前規劃文件

- [專案 Brief](AWS_Cloud_Engineer_Final_Project_Project_Brief.md)
- [專題規劃](docs/project-plan.md)
- [甘特圖時程](docs/gantt.md)
- [檢核清單](docs/checkpoints.md)
