# FX-Clover / ポコニカル自動監視システム

FX-Cloverポコ本人の公式ブログ・公式YouTubeを根拠として、ポコニカルを **監視・研究・通知システム** へ変換するProjectです。

現在の基準版は **v1.23**。正式監視対象は **GBPJPY**、取得時間足は **D1 / H4 / H1 / M15 / M5**、M5を執行足として5分間隔で監視します。

## Safety First

- 実口座の自動売買は行わない
- 注文・決済・変更コードを実装しない
- `orders_enabled: false` を維持する
- AI分類や研究プロキシを公式ルールへ昇格させない
- 未来足を候補選択や判定に使用しない
- 公式未確認事項を推測で埋めない

## Source of Truth

このRepositoryがFX-Clover固有のSSOTです。

新しいChatGPT / Claude Code / Jules / Codex / Copilot等のセッションでは、まず `oosaka0123-sudo/ai-master` のGLOBALルールを読み、その後このRepositoryの以下を確認してください。

1. `README.md`
2. `AGENTS.md`
3. `docs/FX_Clover_正式引き継ぎ圧縮完全版_v1_23.md`
4. `docs/FX_Clover_公式一次資料台帳.md`
5. `knowledge/official_sources.json`
6. `FX_Clover_v1_23_README.md`
7. `release_manifest_v1_23.json`
8. current code / Open Issues / Open PRs / Actions

## Official Source Knowledge Base

ポコニカルの公式根拠は、会話履歴やAIの記憶だけに置かず、Repository内で出典付きに管理します。

- 人間向け一次資料台帳: `docs/FX_Clover_公式一次資料台帳.md`
- AI / プログラム向け機械可読台帳: `knowledge/official_sources.json`

公式で確認できた内容と、システム都合の設計仕様を分離します。たとえばM5は公式教材で実際に使用されていますが、公式教材にはM1を使う例もあるため、現行システムの「M5必須」は引き続き設計仕様として扱います。

## Current State

- v1.22のMT4データ更新・15分タスク・監視・ローカル通知の約4時間連続稼働テスト：合格
- v1.23自動検証：unittest 70件 + `test_engine.py` 7件 = 77件合格
- 配布検証：PASS
- 注文実行コード：なし
- 次の実機工程：Surface上でv1.23 MTFエクスポーターをMetaEditorコンパイルし、D1/H4/H1/M15/M5の5CSV取得を確認して5分タスクへ切替

## Important Distinction

公式ルール、設計仕様、研究仕様、手動入力、未検証参考情報を混同しません。公式数値基準がない項目は自動確定せず、手動入力または研究仕様として隔離します。

詳細は `docs/FX_Clover_正式引き継ぎ圧縮完全版_v1_23.md` を参照してください。
