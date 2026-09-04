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
7. `docs/FX_Clover_AIレビュー優先キュー.md`
8. `docs/FX_Clover_P0マスター講座一次資料レビュー.md`
9. `docs/FX_Clover_READY項目根拠マップ.md`
10. `knowledge/official_sources.json`
11. `knowledge/poconical_curriculum.json`
12. `knowledge/dma25x5_official_sources.json`
13. `knowledge/right_shoulder_official_sources.json`
14. `knowledge/p0_master_course_blog_review.json`
15. `knowledge/ready_manual_field_registry.json`
16. `knowledge/poconical_post_catalog.json`
17. `knowledge/poconical_review_queue.json`
18. `sync_fxclover_catalog.py`
19. `build_poconical_review_queue.py`
20. `validate_poconical_catalog.py`
21. `validate_poconical_review_queue.py`
22. `validate_ready_field_registry.py`
23. `FX_Clover_v1_23_README.md`
24. `release_manifest_v1_23.json`
25. current code / Open Issues / Open PRs / Actions

## Official Source Knowledge Base

ポコニカルの公式根拠は、会話履歴やAIの記憶だけに置かず、Repository内で出典付きに管理します。

- 人間向け一次資料台帳: `docs/FX_Clover_公式一次資料台帳.md`
- AI学習順・公式カリキュラム: `docs/FX_Clover_AI学習カリキュラム.md`
- 全記事メタデータ同期手順: `docs/FX_Clover_全記事カタログ同期.md`
- 171記事のAIレビュー順: `docs/FX_Clover_AIレビュー優先キュー.md`
- P0マスター講座ブログ一次資料レビュー: `docs/FX_Clover_P0マスター講座一次資料レビュー.md`
- READY手動6項目の根拠マップ: `docs/FX_Clover_READY項目根拠マップ.md`
- AI / プログラム向け公式資料台帳: `knowledge/official_sources.json`
- マスター講座・問題集の機械可読索引: `knowledge/poconical_curriculum.json`
- DMA25×5公式根拠: `knowledge/dma25x5_official_sources.json`
- 右肩・入れ子フォーメーション公式根拠: `knowledge/right_shoulder_official_sources.json`
- P0マスター講座ブログ根拠: `knowledge/p0_master_course_blog_review.json`
- READY手動フィールドの機械可読分類: `knowledge/ready_manual_field_registry.json`
- 公式ポコニカルカテゴリ全記事カタログ: `knowledge/poconical_post_catalog.json`
- 優先レビューキュー: `knowledge/poconical_review_queue.json`

2026-09-04の実同期では、ポコニカルトレード公式カテゴリから **18ページ / 171記事** のメタデータを取得済みです。カタログは記事本文をGitHubへ複製せず、記事ID・公式URL・タイトル・日付・取得元ページだけを保持します。最古の収録記事は基礎記事 `https://fx-clover.com/?p=6913`（2020-06-12）です。

`.github/workflows/poconical-catalog-sync.yml` は毎週の定期同期と手動同期を提供し、実質的な記事メタデータ差分がある時だけautomation branch / PRへ更新を出します。`generated_at_utc` だけの変化では更新PRを作りません。

171記事は `build_poconical_review_queue.py` で漏れなくレビュー順へ変換します。初回生成時は根拠抽出済み14件、公式カリキュラム掲載だが詳細抽出未完7件、未レビュー150件でした。

P0マスター講座7記事のブログ本文レビュー後は、**EVIDENCE_REVIEWED=21 / UNREVIEWED=150** へ進み、優先度は **P0=14 / P1=39 / P2=21 / P3=76 / DONE=21** です。現在の先頭P0は `8268「FX ずらした移動平均線DMA【ポコニカル活用エントリーと決済について】」` で、次に上位MA・時間足・3-3関連の記事が続きます。

レビュー優先順位は **研究上の読む順番** であり、売買ルールの重要度・確度ではありません。記事タイトルやカリキュラム一致だけで公式ルールへ昇格させません。`knowledge/poconical_review_queue.json` の全項目は `rule_promotion_allowed: false` を維持します。

P0マスター講座のブログ一次資料レビューでは、右肩・上位環境認識・MA / グランビル・ゾーン / FR・状況別の手法選択が公式の中核概念として補強されました。一方、補足記事 `?p=7616` ではDMA3-3を「最後の見極め」として使いつつ「無くても良い」「好み」とする趣旨が確認できたため、**DMA3-3は公式利用されるが、ポコニカル普遍必須条件とは扱いません**。現行v1.23で3-3を使うことはProject設計として維持します。

動画内で説明される細かなエントリー・決済条件は、動画本文を確認できていない限り推測しません。今回の7記事レビューから新しい本番数値閾値は追加していません。

`validate_poconical_review_queue.py` は、公式171記事カタログとレビューキューが完全一致し、欠落・重複・外部記事・本文保存・ルール自動昇格がないことをCIで確認します。CIではキューを再生成し、コミット済みJSONとの一致も検証します。

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
- 171記事のAIレビュー優先キュー：全件カバー・検証済み
- 公式ブログ本文の根拠抽出済み記事：21件
- P0マスター講座ブログ7件：一次資料レビュー済み
- 注文実行コード：なし
- 次のGitHub研究工程：P0先頭のDMA / MA / 時間足 / 3-3関連公式記事を本文レビュー
- 次の実機工程：Surface上でv1.23 MTFエクスポーターをMetaEditorコンパイルし、D1/H4/H1/M15/M5の5CSV取得を確認して5分タスクへ切替

## Important Distinction

公式ルール、設計仕様、研究仕様、手動入力、未検証参考情報を混同しません。公式数値基準がない項目は自動確定せず、手動入力または研究仕様として隔離します。

詳細は `docs/FX_Clover_正式引き継ぎ圧縮完全版_v1_23.md` を参照してください。
