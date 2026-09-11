# FX Project Handoff

Updated: 2026-09-11 JST

## Start here

This repository is the technical SSOT for the current GBPJPY short-entry monitoring/research project. Read this file first, then `AGENTS.md`, `docs/FX_Clover_売買ロジック仕様.md`, Issue #2, Issue #20, and current `site/` files.

## Current repository state

- Repository: `oosaka0123-sudo/fx-entry-lab`
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

Keep 【公式ルール】 / 【設計仕様】 / 【研究仕様】 / 【手動入力】 / 【未確認】 separate. Do not convert unresolved official concepts into guessed numeric rules. Exact mid-range boundaries, numeric lower-right-shoulder criterion, exact DMA25×5 inside definition, obstacle-MA/downward-room thresholds, FE anchors/allocation and other unresolved items remain manual/research/unknown as documented in the SSOT.

## Public site — completed

Public URL: `https://oosaka0123-sudo.github.io/fx-entry-lab/`

Logic page: `https://oosaka0123-sudo.github.io/fx-entry-lab/trading-logic.html`

PR #33 was merged and Pages published the new public presentation successfully.

- Site brand: `FX Entry Lab`
- Subtitle: `GBPJPY Short Entry Research`
- Public logic name: `右肩戻り売りロジック`
- Project name: `FX Entry Lab`. Derived logic name: `右肩戻り売りロジック` (`Right-Shoulder Pullback Short`).
- The GitHub repository slug is `fx-entry-lab`, aligned with the public `FX Entry Lab` brand.
- `ポコニカル` is retained only when preserving an official source title, quotation, historical label, or source taxonomy. It is not used as this project's product / logic name.
- Independence / no-advice / no-auto-trading disclaimer is present and `orders_enabled:false` remains visible.
- Existing lightweight motion was preserved.

## Entry-timing video — completed outside repository

A new 9:16 entry-timing video was produced using the neutral `FX Entry Lab` brand and SSOT-safe wording.

Sequence: upper-timeframe downward environment → thrust → first pullback → right-shoulder area → M5 DMA3×3 bearish-body close trigger where project design applies → SHORT candidate notification only.

It explicitly shows `TRIGGER = 通知候補`, `実注文はしない`, and `orders_enabled:false`. Unsupported generated claims such as `38.2%–61.8%` or invented win-rate claims were removed. The video is not committed to this repository.

## Surface v1.23 runtime — latest checkpoint

Issue #2 remains OPEN only because the final continuity window and human visual notification confirmation are still pending.

Surface project path: `C:\FX_Clover\v123`

Verified on the real Surface / XMTrading MT4 environment:

- current main is installed locally
- `VERIFY_PACKAGE_v1_23.bat`: PASS
- all 10 release-critical SHA-256 hashes match
- required Python imports: OK
- `orders_enabled:false`
- MetaEditor real compile of `FX_Clover_MTF_Exporter_v1_23.mq4`: `0 errors, 0 warnings`
- v1.23 exporter loads successfully on `GBPJPY,M5`
- D1 / H4 / H1 / M15 / M5 CSV generation works
- latest `system_health_check_v1_23.py`: PASS / `failed_checks=[]`
- `FX_Clover_Live_Monitor_5min`: Ready / LastTaskResult=0
- old `FX_Clover_Live_Monitor_15min`: Disabled
- latest monitor state: `COMPLETED`, WATCH=2, READY=0, fresh alerts=0, `orders_enabled:false`

### H4 history and MT4 profile cleanup

The initial H4 CSV had only 3 closed bars. The GBPJPY/H4 chart was activated directly in MT4 and navigated toward chart history, causing MT4 to load real H4 history. H4 CSV increased from 3 to 2928 closed bars.

Latest five-timeframe counts at the checkpoint:

- D1: 1536
- H4: 2928
- H1: 2489
- M15: 53218
- M5: 151

The MT4 profile had accumulated many duplicate GBPJPY/M15 charts and old exporter attachments from prior setup attempts. Cleanup performed safely:

- 20 duplicate GBPJPY/M15 chart windows were closed through MT4 itself.
- superseded `FX_Clover_M15_Exporter_v1_10` and temporary `FX_H4_History_Warmer` files were moved out of active `MQL4\Experts` into a timestamped disabled archive; they were not deleted.
- backups of the profile were retained.
- active profile now contains the normal non-FX charts plus only GBPJPY/M5 with `FX_Clover_MTF_Exporter_v1_23` and GBPJPY/H4 without an Expert.
- after a clean shutdown/restart, the latest startup loads only `FX_Clover_MTF_Exporter_v1_23 GBPJPY,M5` successfully; old M15 exporter is no longer loaded.

Do not restore the old M15 exporter or temporary warmer unless specifically diagnosing a regression.

### Windows Git line-ending fix — merged

A real Surface checkout initially failed raw SHA verification because Git for Windows `core.autocrlf=true` converted release-critical LF files to CRLF. GitHub blobs were correct.

PR #35 added `.gitattributes` `-text` protection for the 10 byte-hashed critical files plus CI validation. It was verified on Surface using a fresh clone with `core.autocrlf=true`: all hashes matched and `VERIFY_PACKAGE_v1_23.bat` passed. The fix was merged to main and the Surface production clone was synchronized to that main.

## CURRENT PRIORITY — finish Issue #2 continuity evidence

Do not close Issue #2 yet.

Still pending:

1. complete the multi-hour notification-only continuity window
2. confirm scheduler runs continue returning LastTaskResult=0
3. final health check after the continuity window
4. final scan for new `Traceback` / `ERROR` / `FAILED` / `STALE` after the clean MT4 state
5. final WATCH / READY / TRIGGER and notification-log counts
6. human visual confirmation that the Windows test notification actually appeared on screen

`TEST_WINDOWS_NOTIFICATION_v1_18.bat` has returned diagnostic PASS and `notification_display_command_succeeded:true`, but its own diagnostic requires human visual confirmation for actual on-screen display. Do not mark visual notification PASS without the user seeing it.

A one-time follow-up check is scheduled for later on 2026-09-11 to inspect the continuity evidence. Latest runtime checkpoints are also recorded in Issue #2 comments.

## Official-source research

Issue #20 P0 DMA / MA / timeframe batch has advanced by 6 official-source articles: 8268, 7691, 6979, 7022, 7891, 8090. Evidence is stored in `knowledge/p0_dma_ma_timeframe_blog_review.json`. Review queue state is EVIDENCE_REVIEWED=27 / UNREVIEWED=144 / P0=8 / DONE=27. Validators pass and `orders_enabled:false` remains unchanged. No production WATCH / READY / TRIGGER logic was changed and no new universal numeric threshold was promoted. Next P0 begins at article `?p=8343`.

## Safety / claims

- No auto trading.
- `orders_enabled:false` stays hard-coded/configured as disabled.
- TRIGGER means candidate notification, not execution.
- No future-bar lookahead.
- Research performance is not official win rate or live performance.
- Do not claim exact official numeric rules that remain unresolved.
- Do not claim the GitHub source tree is a bit-for-bit mirror of an original ZIP unless separately proven.
- Public wording for test counts should remain `unittest 70件がPASS。あわせてengine check scriptも正常完了。`

## Recommended exact restart instruction

`fx-entry-lab の HANDOFF.md と Issue #2 の最新checkpointを読み、Surface v1.23の連続稼働最終確認から再開して。5分タスクのLastResult、health check、クリーン再起動後のエラーログ、WATCH/READY/TRIGGER件数を確認し、実注文は禁止・orders_enabled:falseを維持する。通知の画面表示だけは人間の目視確認が取れるまでPASSにしない。`
