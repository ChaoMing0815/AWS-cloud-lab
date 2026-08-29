# Tier 2 publisher service／release contract 驗證摘要

- Scope／risk／upstream source：Web host的publisher container unit與disabled-only installer；R3；PR #47 runtime與既有Tier 3 exact-image asset model。
- Baseline：Web／Worker container contract與Tier 3 release contract共53項全綠。
- Red commit：`63082b8`；因缺少unit、installer與image assets而5項目標測試失敗。
- Green commit：`03eab84`；新增publisher unit、bounded installer與Dockerfile封裝。
- Targeted verification：publisher、Web／Worker container與Tier 3 release contract共58項全綠。
- Full regression：Backend `766 tests collected`，exit code `0`；只有既有Starlette／httpx deprecation warning。
- Negative／boundary：unit無`[Install]` target、無硬編async／enable、無port；啟動前必須存在獨立`publisher-runtime.env`。
- Installer：只接受root-owned regular `0400` asset；service必須inactive且不得有既有unit；安裝後驗證disabled／inactive，全程不呼叫enable／start／restart。
- Rollback：首次`daemon-reload`失敗時移除新unit並再次reload，不留下半安裝資產。
- Sensitivity：暫時加入`systemctl enable`後目標測試立即失敗；mutation已還原並重跑全綠。
- Residual risk：本批只封裝assets；未安裝host unit、未建立activation file、未部署、未套用`005`、未送SQS，Web仍為`sync`。

## Production 安裝前 static-state 修正

- Preflight：unit刻意沒有`[Install]`；systemd對此回`static`且`is-enabled`可為exit `0`，舊installer會誤判為enabled並移除unit。
- Red commit：`3dad43a`；模擬`static`／exit `0`時，installer錯誤回`unexpected_enabled_service`。
- Green commit：`2294f6c`；只允許`disabled`或`static`，其他enablement state仍fail closed並回復新unit。
- Targeted verification：publisher與Tier 3 delivery contracts共`39 passed`。
- Full regression：Backend `768 tests collected`，exit code `0`；只有既有Starlette／httpx warning。
- Sensitivity：暫時從allowlist移除`static`時新target test失敗；還原後完整regression通過。
- Boundary：沒有加入`enable`／`start`／`restart`，沒有activation env、IAM、AWS resource、SQS或Bedrock變更；production unit仍尚未安裝。
