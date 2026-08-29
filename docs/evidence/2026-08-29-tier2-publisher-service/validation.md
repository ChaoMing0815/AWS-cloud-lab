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

## Production disabled-only 安裝完成

- PR #52四項CI全綠並合併為exact main `9337026dea8f0537ac94b3d0979b00cd45c5e2a1`。
- Run `33246093420`以previous digest `sha256:abd0f942…`完成bounded `digest-release`；exact target digest為`sha256:af120cbbfafe710ea8b9da9fb6e1b67cde57e619d91c4188b88740136485cc59`，Trivy與SSM success／response `0`。
- 使用者透過單一bounded SSM Run Command只從active exact image複製installer與unit；來源檔限制root-owned regular file，且拒絕`[Install]`、enable／start／restart與hardcoded async。
- Installer回`publisher_service=installed:disabled`；postflight為unit `static`、service `inactive`、runtime env absent、publisher container absent、Web `sync`。
- 本批未建立activation env、未啟動publisher、未送SQS message、未呼叫Bedrock、未新增IAM／AWS resource或切換Web async。
- 下一批必須獨立核准runtime env與publisher activation；exactly-one test job及Web async仍是後續不同批次。

## Production publisher activation完成

- 啟動前preflight確認unit為`static`／service為`inactive`、publisher env與container不存在、dispatch outbox總數為`0`，且Web container精確維持`sync`。
- 第一次bounded SSM Run Command因檢查了source asset名稱`co-story-container.service`，在任何變更前回`web_service_not_active`／response `2`；production實際安裝名稱為`co-story.service`，未留下activation env或publisher container。
- 修正唯讀service名稱後，使用者以相同單一Web target重新執行；建立root-owned `0640` activation env，unit仍為`static`且只以人工`start`啟動，未執行`enable`。
- Postflight回`publisher_activation=verified unit=static service=active container=running outbox_total=0 web=sync`；publisher使用active exact digest `sha256:af120cbbfafe710ea8b9da9fb6e1b67cde57e619d91c4188b88740136485cc59`。
- 本批未建立test job、未切換Web async、未新增IAM／AWS resource；空outbox代表publisher未取得可發布工作。本批亦未由Agent執行AWS CLI、S3讀取或Bedrock呼叫。
- Rollback為停止`co-story-publisher.service`、確認`co-story-publisher` container移除，再刪除`/etc/co-story/publisher-runtime.env`。Exactly-one test job與Web async仍須各自獨立核准。
