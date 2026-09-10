# FX Project Handoff

Updated: 2026-09-10 JST

## Start here

This repository is the technical SSOT for the current GBPJPY short-entry monitoring/research project. The next session should read this file first, then `AGENTS.md`, `docs/FX_Clover_売買ロジック仕様.md`, open Issue #2 and Issue #20, and the current `site/` files.

## Current repository state

- Repository: `oosaka0123-sudo/fx-clover`
- Default branch: `main`
- Main head at handoff start: `8c023dc9df7a2d1f7dfe5a1cdd74869eb88aa426`
- Runtime baseline: v1.23
- Formal monitoring target: GBPJPY
- Timeframes: D1 / H4 / H1 / M15 / M5
- Execution timeframe: M5 (project design, not a universal official requirement)
- Real order execution remains disabled: `orders_enabled: false`
- Do not add OrderSend / OrderClose / OrderModify / OrderDelete or any real-account execution path.

## Trading logic SSOT

`docs/FX_Clover_売買ロジック仕様.md` was added through Issue #28 / PR #29 and merged.

Core sequence:

`上位足下降 → 推進 → 最初の戻し → 右肩 → DMAトリガー → SHORT候補通知`

Keep these classes separate:

- 【公式ルール】
- 【設計仕様】
- 【研究仕様】
- 【手動入力】
- 【未確認】

Do not convert unresolved official concepts into guessed numeric rules.

Important unresolved/manual items still include exact mid-range boundaries, numeric lower-right-shoulder criterion, exact DMA25×5 inside definition, obstacle-MA/downward-room thresholds, FE anchors/allocation, and other items documented in the logic specification.

## Public site

Public URL:

`https://oosaka0123-sudo.github.io/fx-clover/`

Logic page:

`https://oosaka0123-sudo.github.io/fx-clover/trading-logic.html`

Current site source is under `site/` and is published to the `gh-pages` branch by the repository workflow.

The site has already been upgraded to a lightweight motion-rich UI through Issue #30 / PR #31:

- CSS transform/opacity based motion
- IntersectionObserver reveal
- requestAnimationFrame-throttled pointer glow
- terminal/flow/card micro-interactions
- `prefers-reduced-motion` support
- no external animation library
- no image payload increase from that change

## TOP PRIORITY NEXT SESSION — public naming change

The user explicitly decided that GitHub repository naming can be dealt with later. First change only the PUBLIC SITE PRESENTATION.

Target public brand:

- Site brand: `FX Entry Lab`
- Subtitle: `GBPJPY Short Entry Research`
- Public logic name: `右肩戻り売りロジック` or `ショートエントリー研究ロジック`

Replace public-facing uses of:

- `FX-Clover` as the site brand → `FX Entry Lab`
- `ポコニカル` as a headline/product-like name → neutral independent wording such as `右肩戻り売りロジック`

Do NOT rename the GitHub repository yet. Do NOT rewrite the internal evidence/source history merely to hide the source. Official FX-Clover articles may still be identified inside source/evidence sections where needed, but the public site must not look official, affiliated, endorsed, or operated by FX-Clover/Poko.

Recommended footer/disclaimer concept:

> 本サイトは独立した研究・検証用の情報サイトです。特定の公式サービス、運営者、考案者との提携・公認・運営関係はありません。売買助言や自動売買を目的とするものではなく、実注文は行いません。

After editing the site, run the existing site/integrity CI and let the normal main → gh-pages publishing workflow redeploy it. Keep `orders_enabled:false` language visible.

## Entry-timing video request

The user asked for an entry-timing video reconstruction. In the previous chat, six vertical 9:16 storyboard-style still images were generated, but a finished video was NOT produced and the frames were NOT committed to this repository.

Do NOT publish those generated frames as authoritative. They contain public-facing `FX-Clover` / `ポコニカル` branding and some generated explanatory content that is not safe to promote as formal rules (for example a generated retracement zone `38.2%–61.8%` and wording implying improved win rate). Those details are not established by the current SSOT and must be removed/corrected.

For the next video version:

1. Use the neutral `FX Entry Lab` public brand.
2. Base every factual trading statement on `docs/FX_Clover_売買ロジック仕様.md`.
3. Sequence should visually reproduce:
   - upper-timeframe downward environment
   - thrust
   - first pullback
   - right-shoulder area
   - M5 DMA3×3 bearish-body close trigger (project design where applicable)
   - SHORT candidate notification only
4. Clearly show `TRIGGER = 通知候補` and `実注文はしない`.
5. Avoid invented numeric Fibonacci zones, invented win-rate claims, or other unsupported thresholds.

## Runtime blocker

Issue #2 remains open: `Surface実機でv1.23を導入・検証する`.

Still not verified as PASS:

- Windows/MetaEditor real MQL4 compile
- real D1/H4/H1/M15/M5 CSV acquisition on Surface
- actual five-minute scheduled continuous run on Surface

Do not mark Windows/MT4 PASS without real evidence.

When returning to runtime work, resume one physical step at a time. First target is package verification on Surface (`VERIFY_PACKAGE_v1_23.bat`), then MT4 compile and five-timeframe health check.

## Official-source research

Issue #20 remains open for the next P0 official-source batch, including article `?p=8268` and additional DMA/MA/timeframe sources. This can proceed after or in parallel with the public naming cleanup, but it must not silently alter production logic.

## Safety / claims

- No auto trading.
- `orders_enabled: false` stays hard-coded/configured as disabled.
- TRIGGER means candidate notification, not execution.
- No future-bar lookahead.
- Research performance is not official win rate or live performance.
- Do not claim the GitHub source tree is a bit-for-bit mirror of the original 187-file ZIP.
- Do not claim exact `77 PASS`; public wording should remain `unittest 70件がPASS。あわせてengine check scriptも正常完了。`

## Recommended exact restart instruction

`fx-clover の HANDOFF.md を最初に読み、GitHubリポジトリ名は変更せず、まず公開サイトだけを FX Entry Lab / 右肩戻り売りロジック表記へ変更する。既存の軽量モーションは維持し、FX-Clover/ポコニカルを公式ブランドのように見せない。変更後CIとGitHub Pages公開を確認。その後、エントリータイミング動画をSSOT準拠・ブランド中立で作り直す。実注文は禁止、orders_enabled:falseを維持する。`
