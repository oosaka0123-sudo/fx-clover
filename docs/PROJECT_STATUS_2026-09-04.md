# FX-Clover Project Status — 2026-09-04

## Current GitHub baseline

- Repository: `oosaka0123-sudo/fx-clover`
- Default branch: `main`
- Baseline version: `v1.23`
- Strategy: `POCONICAL_ONLY`
- Formal monitoring instrument: `GBPJPY`
- Multi-timeframe set: `D1 / H4 / H1 / M15 / M5`
- Execution timeframe: `M5`
- Orders: disabled (`orders_enabled: false`)
- Real-money order execution is not implemented.

## GitHub synchronization completed

- PR #1 merged into `main`.
- Merge commit: `948b9cd686cdcadec184435420e1dd26227a51ad`
- GitHub Actions on `main` completed successfully.
- Release-critical SHA-256 verification: PASS.
- MQL4 order-function safety scan: PASS.
- v1.23 source, launchers, core dependencies, tests, manifest, handoff docs, and integrity CI are now stored in this repository.

## Safety boundaries

- Do not implement or enable `OrderSend`, `OrderClose`, `OrderModify`, or `OrderDelete`.
- Keep `orders_enabled: false`.
- TRIGGER remains a notification candidate, not an order event.
- H1 WATCH automation remains a research proxy and must not be promoted to an official rule.
- Official unknowns remain manual/research-only until primary-source evidence exists.
- Research results must not be represented as official/live performance.

## Current formal state machine

`NO_TRADE → WATCH → READY → SIMULATED_POSITION → NO_TRADE`

- STOP is a stop-price attribute, not a state.
- EXIT is an end event.
- PARTIAL_TAKE_PROFIT is a partial-exit event.
- SIMULATED_POSITION remains active while any simulated quantity remains.

## Current verified release package

- Package: `FX_v123.zip`
- SHA-256: `680c42e71d1517effcb177edf28e13a1511a44fdee76c7883180a4c086c855cd`
- Previous package validation:
  - `verify_distribution_v1_23.py`: PASS
  - unittest: 70 passed
  - `test_engine.py`: completed successfully
  - no active order functions detected in v1.23 execution code

## Surface / Windows MT4 deployment status

GitHub-side baseline is complete. The following remain intentionally **unverified until Surface evidence is collected**:

- [ ] `VERIFY_PACKAGE_v1_23.bat` PASS on Surface
- [ ] `FX_Clover_MTF_Exporter_v1_23.mq4` MetaEditor compile with 0 errors
- [ ] exporter attached to GBPJPY M5
- [ ] D1/H4/H1/M15/M5 closed-candle CSV generation on the actual MT4 installation
- [ ] `RUN_SYSTEM_HEALTH_CHECK_v1_23.bat` all PASS
- [ ] Windows local notification test PASS
- [ ] old 15-minute scheduled task disabled
- [ ] new 5-minute scheduled task enabled and running
- [ ] several hours of notification-only continuous operation without Traceback / ERROR / FAILED / STALE
- [ ] evidence of WATCH / READY / TRIGGER behavior collected
- [ ] real orders remain zero

Tracking issue: #2 — Surface実機でv1.23を導入・検証する

## Next action

Continue on the Surface from the real-machine verification phase. Do not mark deployment complete until the Windows/MT4 evidence above is captured.
