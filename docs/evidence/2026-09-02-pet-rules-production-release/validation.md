# 兩日版寵物規則助手 production release 驗證

- 日期：2026-09-02
- Scope／risk：R2 UI／deterministic rules retrieval；沿用既有 `digest-release` production envelope。
- Exact production source：`4db923f4d24aae0aca25c3fbe525f765f9d5023b`。
- Main CI：run `33577941894`；第一次只因 Docker Hub 拉取 BuildKit timeout，在 application build／scan 前停止，failed jobs rerun 的 attempt 2 全綠。
- Release：run `33578331749` 成功；production approval、GitHub OIDC、ARM64 build／immutable push、digest fence、Trivy、bounded SSM 與 delivery metrics均通過。

## Runtime 結果

- Previous／rollback Web digest：`sha256:5a10597d473cd21c5b2754b743f4a48de2be7cae9bd0c1816c535523284df9bd`。
- Active Web digest：`sha256:14d8e0fbc2ef6a5c8363b40e30160a7cd76f42a29d8a506be250263026486d90`。
- SSM release：`Status=Success`、`ResponseCode=0`；delivery metrics `status=success`、`verified=true`。
- Metrics：approval wait `77s`、automation execution `151s`、build and scan `123s`、end-to-end `235s`、SSM release attempt `28s`。
- Web runtime 維持 `async`；migration inventory 維持精確 `001`–`005`。
- Publisher digest維持 `sha256:23357e315e94842cee8455023b1f87f203fca5b1d11b67b714f4af86efaa2a1b`。
- 兩台 private Worker digest維持 `sha256:2d5d5866f54879e79882644f4b45af2475650ddc9972e6b91cfe786886cddfbc`。

## Production acceptance

- Strict TLS：首頁、`/api/v1/live`、`/api/v1/ready` 均回 `200`。
- Viewport：390×844、768×844、1440×900 均無 document horizontal overflow，nav與寵物toggle不重疊。
- 首頁中文片語 `每個選擇，`、`都會成為`、`下一段共同故事。` 不拆分；沒有逗點後孤字或「下一段」斷開。
- 寵物對話框顯示開始遊戲、角色屬性、回合流程、骰點判定、星火、進度／危機／結局六個主題；開啟時動畫暫停。
- 390×844 Demo 的dialog與action form／textarea不相交。
- Supported「星火」查詢回 canonical answer 與 stable citation；unsupported「如何駕駛飛船？」回固定不猜測答案、狀態為「規則資料不足，未進行猜測。」且citation隱藏／空白。
- 玩家導航不再顯示`/support`連結；直接開啟`/support`回到landing composition，寵物助手仍可使用。
- Browser console error／warning均為 `0`。

## 誠實邊界與 rollback

- 本功能是 cited deterministic rules assistant，不是 RAG；沒有 LLM、embedding、vector store、Bedrock、MCP 或 external submit。
- 本次沒有建立第二個 story job、額外 Bedrock invocation 或新的 rules draft。
- 若Web release需回復，使用既有exact-digest流程切回 `sha256:5a10597d473cd21c5b2754b743f4a48de2be7cae9bd0c1816c535523284df9bd`；本次無schema變更，不需要database rollback。
