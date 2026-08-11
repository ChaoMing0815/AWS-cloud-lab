# Session security prerequisites TDD 驗證

- Branch：`codex/session-lifecycle`
- Baseline commit：`fbfa7e4`
- 日期：2026-08-11
- 範圍：current-room member authorization、production HTTPS Secure cookie
- AWS 寫入／費用：無

## Baseline

- Session targeted：`../.venv/bin/python -m pytest tests/test_session_api.py -q` → `4 passed`。
- Backend：`../.venv/bin/python -m pytest -q` → `59 passed, 7 skipped`。
- Frontend：bundled Node `node --test 'tests/**/*.test.js'` → `65 passed`。
- 系統 shell 沒有 `npm`；改用工作區內建 Node runtime，確認不是產品 Red。

## Slice 1：current-room member authorization

### Red

- Commit：`e385a67`
- 測試：`test_room_pointer_without_a_member_session_cannot_read_the_room`
- 預期：只有 `co_story_local_room` pointer、沒有有效 Host／Player session 時回 `401 SESSION_NOT_FOUND`。
- 實際：回 `200`，證明 pointer 被錯當授權並可讀取房間。

### Green

- Commit：`6330a45`
- 最小實作：current-room route 先取得 `session_context`；anonymous 不序列化房間。
- Targeted：新拒絕案例與合法 cookie restore 共 `2 passed`。
- Regression：Backend `60 passed, 7 skipped`；Frontend `65 passed`。
- Refactor：無；現有 route 邊界已足以表達此行為。

### Sensitivity

- 暫時移除 anonymous guard。
- 目標測試由 `401` 退回 `200` 並失敗；還原後 `1 passed`。
- 故障注入未提交。

## Slice 2：production HTTPS Secure cookie

### Red

- Commit：`ed7f454`
- 測試：`test_https_mode_marks_all_session_and_room_cookies_secure`
- 預期：`CO_STORY_COOKIE_SECURE=true` 時三個 cookie 都有 `Secure`、`HttpOnly`、`SameSite=Lax`。
- 實際：三個 cookie 都缺少 `Secure`。

### Green

- Commit：`1e75b69`
- 最小實作：composition 讀取 `CO_STORY_COOKIE_SECURE`，透過 router 傳給兩個 cookie helper。
- Targeted：HTTPS mode 與既有 local HTTP restore 共 `2 passed`。
- Regression：Backend `61 passed, 7 skipped`；Frontend `65 passed`。
- Refactor：無；設定只在 composition root 解析，helper 保持單一責任。

### Sensitivity

- 暫時強制 `secure_cookies=False`，忽略環境設定。
- 目標測試因缺少 `Secure` 失敗；還原後 `1 passed`。
- 故障注入未提交。

## TDD 稽核更正

曾建立但未提交一個固定 `Max-Age=604800` 的測試。Sol 安全審查指出上游只核准「session 不晚於房間到期」，尚未核准固定 7 天，且該測試漏掉恢復所需的 local-room pointer。依停止條件立即撤回，工作樹恢復乾淨後才建立正式 Red；未以該測試宣稱成果。

## 未完成

- Server-side expiry、activity refresh 與精確 boundary。
- Transfer code、reassign、舊 Player session revoke 與 concurrency。
- Feature Spec 精確 contract 仍待使用者核准。
- 本次未執行 Browser 或 AWS 驗證；Secure cookie 的真實 HTTPS Browser 驗證留在部署 release gate。
