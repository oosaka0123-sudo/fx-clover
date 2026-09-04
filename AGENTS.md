# AGENTS.md — FX-Clover Project Rules

このRepositoryでは `oosaka0123-sudo/ai-master/AGENTS.md` のGLOBAL MUST / MUST NOTを最優先で適用します。本ファイルはFX-Clover固有の追加ルールです。

## MUST

1. GitHubをFX-Clover固有のSSOTとして扱い、current code / Issue / PR / Actions / Commit / 本Repository内ドキュメントを現在状態の根拠にする。
2. 根拠を必ず次の分類で分離する。
   - 【公式ルール】ポコ本人の公式発言で確認できた内容
   - 【設計仕様】監視システム化のため開発側が定義した内容
   - 【研究仕様】公式未確認だが検証目的で隔離した条件
   - 【手動入力】数値化できない裁量部分
   - 【未検証参考情報】出典なしの一般論や他AI回答。判定へ使用しない
3. 正式監視対象は現在GBPJPY。USDJPY / EURJPY / GBPUSDは研究仕様として本番監視へ混ぜない。
4. D1 / H4 / H1 / M15 / M5の5種類の時間足を扱い、M5執行足はユーザー確認済みの設計仕様として管理する。一次出典確認前に公式ルールへ昇格させない。
5. 公式未確認の数値条件を推測で固定しない。中段レンジ、右肩、DMA25x5内側、障害MA、伸びしろ等は手動入力または研究仕様として隔離する。
6. 未来足を候補選択・判定・バックテストへ使用しない。確定足だけを使う条件はコードとテストの両方で保護する。
7. 研究成績を公式勝率・ライブ性能として表示しない。M15研究とM5評価を混同しない。
8. 変更時は関連テスト・distribution verifier・安全性確認を実行し、EVIDENCEなしに完成扱いしない。
9. Windows / MT4実機でしか確認できない項目は「未確認」と明記し、ローカルテスト成功を実機成功として報告しない。
10. 長時間作業・モデル切替・別AI引き継ぎ時はai-masterのContext Handoff Protocolに従い、このProject内の引き継ぎ正本を更新する。

## MUST NOT

1. 実口座の注文機能を実装しない。
2. `OrderSend` / `OrderClose` / `OrderModify` / `OrderDelete` 等の発注・決済・変更処理を追加しない。
3. `orders_enabled: false` をtrueへ変更しない。
4. TRIGGERを注文イベントへ変更しない。通知候補イベントのまま維持する。
5. spread欠損を0として黙示処理しない。安全側でTRIGGER拒否する。
6. H1 WATCH研究プロキシを公式ルールそのものとして扱わない。
7. FEアンカー、261/261.8、分割割合、DMA適用価格、XMサーバー時刻変換等の未確認項目を創作しない。
8. APIキー、パスワード、口座情報、認証情報、個人情報をCommit / Issue / PRへ保存しない。

## Current Baseline

- 基準版: v1.23
- Strategy: `POCONICAL_ONLY`
- Execution timeframe: `M5`
- Orders: disabled
- 公式一次資料の優先確認済みURL:
  - https://fx-clover.com/?p=7496
  - https://fx-clover.com/?p=8616
  - https://fx-clover.com/?p=7924

## Completion Evidence

Taskに応じて最低限、Implementation / unit tests / distribution verification / code safety scan / PR diff / CI / Windows-MT4 live verificationのうち該当するものを確認する。確認できないものは未確認として残す。
