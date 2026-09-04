# FX-Clover AIレビュー優先キュー

Issue: #16

## 目的

`knowledge/poconical_post_catalog.json` に収録した公式ポコニカルカテゴリ171記事を、漏れなく・重複なく・重要テーマから順に一次資料レビューするための研究キュー。

生成物:

`knowledge/poconical_review_queue.json`

生成ツール:

`build_poconical_review_queue.py`

## 重要な境界

この優先順位は **記事タイトルと既存公式索引を使った研究上の読む順番** であり、売買ルールの重要度・確度・成績を意味しない。

- タイトル一致だけで【公式ルール】へ昇格しない
- 記事本文はキューへ保存しない
- 数値基準を推測しない
- `rule_promotion_allowed: false`
- `orders_enabled: false`
- WATCH / READY / TRIGGERの実行ロジックを変更しない

## 3つのレビュー状態

### EVIDENCE_REVIEWED

既に以下の一次資料台帳の少なくとも1つへ根拠として登録されている記事。

- `official_sources.json`
- `dma25x5_official_sources.json`
- `right_shoulder_official_sources.json`

優先度は `DONE`。

### CURRICULUM_INDEXED_NOT_RULE_REVIEWED

公式マスター講座 / カリキュラムには登録済みだが、記事単位の詳細なルール抽出がまだ終わっていないもの。

「公式講座に載っている」ことと「機械判定できるルールが抽出済み」を分ける。

優先度は `P0`。

### UNREVIEWED

上記どちらにも入っていない公式カテゴリ記事。

タイトルの研究キーワードからP0〜P3へ振り分ける。

## 2026-09-04 初回生成結果

全171記事を exactly once で収録。

レビュー状態:

- `EVIDENCE_REVIEWED`: 14
- `CURRICULUM_INDEXED_NOT_RULE_REVIEWED`: 7
- `UNREVIEWED`: 150

優先度:

- `P0`: 21
- `P1`: 39
- `P2`: 21
- `P3`: 76
- `DONE`: 14

P0先頭は公式マスター講座のうち、右肩・環境認識・エントリー条件に直接近い記事から並ぶ。

## タイトルによる研究トピック

現在は次のテーマを明示的にスコアリングする。

- DMA / MA / 3-3 / 25-5 / MAサンド
- 右肩 / Wトップ / 三尊 / フォーメーション
- 環境認識 / 上位足 / 時間足 / ゾーン
- Fibonacci / FR / FE
- エントリー / タイミング / 初動
- 損切り / 決済 / 利確
- 伸びしろ / 障害 / MAサンド
- マスター講座 / 問題集 / 基礎 / ポコニカル

これは本文の内容を保証するものではない。本文レビューを開始するための検索優先順位だけに使う。

## Validation

`validate_poconical_review_queue.py` は以下を確認する。

- 公式カタログ171記事とキューが完全一致
- 欠落なし
- 重複なし
- 余計な記事なし
- `review_order` が1〜Nを一度ずつ使う
- URL / タイトルがカタログと一致
- 状態 / 優先度が許可値だけ
- 根拠抽出済み記事は `DONE`
- 未レビュー記事に優先理由がある
- 記事本文 / contentを保存しない
- `rule_promotion_allowed: false`
- `orders_enabled: false`

CIではさらにキューを再生成し、コミット済みJSONと完全一致することも確認する。入力台帳・カタログ・優先ロジックが変わったのにキュー更新を忘れた場合は失敗させる。

## 次工程

P0から公式本文を1件ずつ読み、各記事について次を出す。

1. 公式主張
2. 対象テーマ
3. 年代
4. 既存台帳との一致 / 進化 / 矛盾
5. 数値定義の有無
6. 機械判定可能性
7. READY 6項目への影響
8. 公式ルール / 設計仕様 / 研究仕様 / 手動入力の分類

ルール昇格はこの本文レビューを通過したものだけに限定する。
