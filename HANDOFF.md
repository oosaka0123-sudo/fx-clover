# FX Project Handoff

Updated: 2026-09-11 JST

## Start here

This repository is the technical SSOT for the current GBPJPY short-entry monitoring/research project. Read this file first, then `AGENTS.md`, `docs/FX_Clover_売買ロジック仕様.md`, Issue #2, Issue #20, and current `site/` files.

## Current repository state

- Repository: `oosaka0123-sudo/fx-clover`
- Default branch: `main`
- Runtime baseline: v1.23
- Formal monitoring target: GBPJPY
- Timeframes: D1 / H4 / H1 / M15 / M5
- Execution timeframe: M5 (project design, not a universal official requirement)
- Real order execution remains disabled: `orders_enabled: false`
- Do not add `OrderSend` / `OrderClose` / `OrderModify` / `OrderDelete` or any real-account execution path.

## Trading logic SSOT

`docs/FX_Clover_売買ロジック仕様.md` is the logic SSOT.

Core sequence:

`上位足下降 → 推進 → 最初の戻し → 右肩 → DMAトリガー → SHORT候補通知`

Keep these classes separate:

- 【公式ルール】
- 【設計仕様】
- 【研究仕様】
- 【手動入力】
- 【未確認】

Do not convert unresolved official concepts into guessed numeric rules. Exact mid-range boundaries, numeric lower-right-shoulder criterion, exact DMA25×5 inside definition, obstacle-MA/downward-room thresholds, FE anchors/allocation and other unresolved items remain manual/research/unknown as documented in the SSOT.

## Public site — completed

Public URL:

`https://oosaka0123-sudo.github.io/fx-clover/`

Logic page:

`https://oosaka0123-sudo.github.io/fx-clover/trading-logic.html`

PR #33 was merged and the Pages workflow published the new public presentation successfully.

Current public brand:

- Site brand: `FX Entry Lab`
- Subtitle: `GBPJPY Short Entry Research`
- Public logic name: `右肩戻り売りロジック`

The GitHub repository name remains `fx-clover`; do not rename it unless the user explicitly decides to do so later.

Public-facing headline/product-style `ポコニカル` branding was neutralized. FX-Clover may still be named where it is clearly serving as primary-source/evidence attribution. The site includes an explicit independence / no-advice / no-auto-trading disclaimer and keeps `orders_enabled:false` visible. Existing lightweight CSS/JS motion was preserved.

## Entry-timing video — completed outside repository

A new 9:16 entry-timing video was produced during the chat using the neutral `FX Entry Lab` brand and SSOT-safe wording.

It follows:

1. upper-timeframe downward environment
2. thrust
3. first pullback
4. right-shoulder area
5. M5 DMA3×3 bearish-body close trigger where project design applies
6. SHORT candidate notification only

It explicitly shows `TRIGGER = 通知候補`, `実注文はしない`, and `orders_enabled:false`.

Unsupported generated claims such as `38.2%–61.8%` retracement zones or invented win-rate claims were removed. The video was not committed to this repository, so do not assume repository assets contain it.

## Surface v1.23 runtime — major checkpoint completed

Issue #2 remains OPEN because the final multi-hour continuity requirement and human visual notification confirmation are still pending.

Current Surface local project path:

`C:\FX_Clover\v123`

Verified on the real Surface / XMTrading MT4 environment:

- current main obtained locally
- `VERIFY_PACKAGE_v1_23.bat`: PASS
- all 10 release-critical SHA-256 hashes match
- required Python imports: OK
- `orders_enabled:false`
- `FX_Clover_MTF_Exporter_v1_23.mq4` placed in the active XMTrading MT4 `MQL4\Experts` directory
- MetaEditor real compile: `0 errors, 0 warnings`
- exporter loaded successfully on `GBPJPY,M5`
- D1 / H4 / H1 / M15 / M5 CSV files generated
- `RUN_SYSTEM_HEALTH_CHECK_v1_23.bat`: PASS with `failed_checks=[]`
- new scheduled task `FX_Clover_Live_Monitor_5min`: registered and enabled
- old scheduled task `FX_Clover_Live_Monitor_15min`: Disabled
- first manual run of new 5-minute task: LastResult=0
- first scheduler-driven run at 2026-09-11 07:07 JST: completed with LastResult=0
- monitor state after scheduler run: `COMPLETED`, M5 execution, `orders_enabled:false`
- observed monitor counts at checkpoint: watch candidates 2, ready confirmed 0, fresh alerts 0

### Important Windows Git line-ending finding

The first local package verification failed only because Git for Windows had `core.autocrlf=true`, converting LF to CRLF in the working tree and therefore changing file hashes. Git blob hashes themselves matched the release manifest.

For this Surface clone, repository-local settings were changed to:

- `core.autocrlf=false`
- `core.eol=lf`

The 10 critical files were then re-expanded from their Git blobs byte-for-byte and package verification passed. Do not reinterpret this as corruption of the GitHub source.

### MT4 profile changes made safely

- The previous GBPJPY/M15 chart using the old M15 exporter was backed up before changing its role.
- The v1.23 MTF exporter is attached to GBPJPY/M5.
- A separate GBPJPY/H4 chart with no Expert was used to force H4 history acquisition.
- H4 history/CSV then appeared and the five-timeframe health check passed.
- Existing backups were retained; do not delete them casually.

## NEXT SESSION / CURRENT PRIORITY — finish Issue #2 runtime evidence

Do not close Issue #2 yet.

Still pending:

1. several hours of notification-only continuous operation
2. final confirmation that scheduler runs continue returning success
3. final health check after the multi-hour window
4. final scan for `Traceback` / `ERROR` / `FAILED` / `STALE`
5. final WATCH / READY / TRIGGER and notification-log counts
6. human visual confirmation that the Windows test notification actually appeared on screen

`TEST_WINDOWS_NOTIFICATION_v1_18.bat` already returned diagnostic PASS and the notification display command succeeded, but its own diagnostic explicitly requires human visual confirmation for actual on-screen display. Do not mark that point PASS without the user seeing it.

Latest checkpoint evidence is recorded in Issue #2 comment posted on 2026-09-11 JST.

## Official-source research

Issue #20 remains open for the next P0 official-source batch, including article `?p=8268` and additional DMA/MA/timeframe sources. This may proceed after the runtime continuity checkpoint, but it must not silently alter production logic.

## Safety / claims

- No auto trading.
- `orders_enabled: false` stays hard-coded/configured as disabled.
- TRIGGER means candidate notification, not execution.
- No future-bar lookahead.
- Research performance is not official win rate or live performance.
- Do not claim exact official numeric rules that remain unresolved.
- Do not claim the GitHub source tree is a bit-for-bit mirror of an original ZIP unless separately proven.
- Public wording for test counts should remain `unittest 70件がPASS。あわせてengine check scriptも正常完了。`

## Recommended exact restart instruction

`fx-clover の HANDOFF.md と Issue #2 の最新checkpointを読み、Surface v1.23の数時間連続稼働確認から再開して。5分タスクのLastResult、health check、エラーログ、WATCH/READY/TRIGGER件数を確認し、実注文は禁止・orders_enabled:falseを維持する。通知の画面表示だけは人間の目視確認が取れるまでPASSにしない。`
