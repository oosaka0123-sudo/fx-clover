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
5. `docs/FX_Clover_AI学習カリキュラム.md`
6. `docs/FX_Clover_全記事カタログ同期.md`
7. `docs/FX_Clover_READY項目根拠マップ.md`
8. `knowledge/official_sources.json`
9. `knowledge/poconical_curriculum.json`
10. `knowledge/dma25x5_official_sources.json`
11. `knowledge/right_shoulder_official_sources.json`
12. `knowledge/ready_manual_field_registry.json`
13. `knowledge/poconical_post_catalog.json`
14. `sync_fxclover_catalog.py`
15. `validate_poconical_catalog.py`
16. `validate_ready_field_registry.py`
17. `FX_Clover_v1_23_README.md`
18. `release_manifest_v1_23.json`
19. current code / Open Issues / Open PRs / Actions

## Official Source Knowledge Base

ポコニカルの公式根拠は、会話履歴やAIの記憶だけに置かず、Repository内で出典付きに管理します。

- 人間向け一次資料台帳: `docs/FX_Clover_公式一次資料台帳.md`
- AI学習順・公式カリキュラム: `docs/FX_Clover_AI学習カリキュラム.md`
- 全記事メタデータ同期手順: `docs/FX_Clover_全記事カタログ同期.md`
- READY手動6項目の根拠マップ: `docs/FX_Clover_READY項目根拠マップ.md`
- AI / プログラム向け公式資料台帳: `knowledge/official_sources.json`
- マスター講座・問題集の機械可読索引: `knowledge/poconical_curriculum.json`
- DMA25×5公式根拠: `knowledge/dma25x5_official_sources.json`
- 右肩・入れ子フォーメーション公式根拠: `knowledge/right_shoulder_official_sources.json`
- READY手動フィールドの機械可読分類: `knowledge/ready_manual_field_registry.json`
- 公式ポコニカルカテゴリ全記事カタログ: `knowledge/poconical_post_catalog.json`
- 公式カテゴリ同期ツール: `sync_fxclover_catalog.py`
- 全記事カタログValidator: `validate_poconical_catalog.py`

2026-09-04の実同期では、ポコニカルトレード公式カテゴリから **18ページ / 171記事** のメタデータを取得済みです。カタログは記事本文をGitHubへ複製せず、記事ID・公式URL・タイトル・日付・取得元ページだけを保持します。最古の収録記事は基礎記事 `https://fx-clover.com/?p=6913`（2020-06-12）です。

`.github/workflows/poconical-catalog-sync.yml` は毎週の定期同期と手動同期を提供し、実質的な記事メタデータ差分がある時だけautomation branch / PRへ更新を出します。`generated_at_utc` だけの変化では更新PRを作りません。

カタログへ入った記事はすべて `OFFICIAL_BLOG_CATALOG_ENTRY_UNREVIEWED` / `rule_promotion_allowed: false` から開始します。記事が存在することと、その内容を本番READY/TRIGGER条件へ使えることは別です。一次資料レビュー・年代差確認・ルール分類を通過するまで自動昇格させません。

`validate_ready_field_registry.py` は、v1.23の `watch_monitor_v1_4.py` にあるREADY手動6項目と根拠レジストリが完全一致していることをCIで確認します。公式概念の根拠があっても、数値定義が未確認の項目は引き続き手動入力のままです。

公式で確認できた内容と、システム都合の設計仕様を分離します。たとえばM5は公式教材で実際に使用されていますが、公式教材にはM1を使う例もあるため、現行システムの「M5必須」は引き続き設計仕様として扱います。

DMA25×5 / MA25-5は公式資料からポコニカルのコア要素として確認できます。ただし「DMA25×5の内側」の厳密な機械判定条件は未確認のため、推測で本番TRIGGER条件へ固定しません。

右肩は単一価格ではなく、上位環境の中でWトップ / 三尊等のフォーメーションを待つ領域として扱います。公式資料には、右肩の中にさらにWトップ / 三尊ができる入れ子構造や、左右の肩の形成時間をバランスの目安にする説明がありますが、数値許容差は未確認のため研究仕様へ隔離します。

## Current State

- v1.22のMT4データ更新・15分タスク・監視・ローカル通知の約4時間連続稼働テスト：合格
- v1.23自動検証：unittest 70件 + `test_engine.py` 7件 = 77件合格
- 配布検証：PASS
- 公式ポコニカルカテゴリ全記事カタログ：18ページ / 171記事を取得・検証済み
- 全記事カタログ自動更新Workflow：実動確認済み
- 注文実行コード：なし
- 次の実機工程：Surface上でv1.23 MTFエクスポーターをMetaEditorコンパイルし、D1/H4/H1/M15/M5の5CSV取得を確認して5分タスクへ切替

## Important Distinction

公式ルール、設計仕様、研究仕様、手動入力、未検証参考情報を混同しません。公式数値基準がない項目は自動確定せず、手動入力または研究仕様として隔離します。

詳細は `docs/FX_Clover_正式引き継ぎ圧縮完全版_v1_23.md` を参照してください。
