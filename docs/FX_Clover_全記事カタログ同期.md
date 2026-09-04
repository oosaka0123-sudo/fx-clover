# FX-Clover 全記事カタログ同期

Origin: Issue #9
Automation: Issue #13

## 目的

ポコニカルの代表記事だけでなく、公式カテゴリ全体をAIの検索対象へ入れるため、記事本文ではなく **記事メタデータのカタログ** を生成・更新する。

対象カテゴリ:

- `https://fx-clover.com/?cat=526`
- ポコニカルトレード

2026-09-04の実同期では、公式カテゴリ **18ページ / 171記事** を取得した。

生成物:

`knowledge/poconical_post_catalog.json`

最古の収録記事は `https://fx-clover.com/?p=6913`（2020-06-12）。

## なぜ本文をGitHubへ丸ごと保存しないか

このRepositoryで必要なのは、公式記事を漏れなく追跡してAIが必要時に一次資料へ戻れること。

GitHubへ保存するのは以下だけとする。

- 記事ID
- 公式URL
- タイトル
- 公開日 / アーカイブ表示日
- カテゴリID
- 何ページ目から発見したか
- 未レビューであることを示す分類

記事本文そのものは保存しない。

## 同期ツール

`sync_fxclover_catalog.py`

標準ライブラリのみで動作する。

通常実行:

```bash
python sync_fxclover_catalog.py
```

確認だけして書き込まない:

```bash
python sync_fxclover_catalog.py --dry-run
```

最大ページ数を指定:

```bash
python sync_fxclover_catalog.py --max-pages 30
```

ツールは以下のどちらかで正常終了する。

1. 新しい記事IDが1件も見つからないページへ到達
2. 2ページ目以降の範囲外アーカイブがHTTP 404を返す

1ページ目の404は正常終了にせず、取得障害として失敗させる。

## GitHub Actions自動同期

Workflow:

`.github/workflows/poconical-catalog-sync.yml`

### Bootstrap

Issue #13のfeature branchでは、Workflow追加・crawler・test変更を契機に同期を実行し、生成されたカタログを同じbranchへ自動コミットする。

### 定期更新

mainへMerge後は、毎週月曜日 03:17 UTC（日本時間12:17）に定期同期する。

手動の `workflow_dispatch` も利用できる。

既存カタログと比較する際は `generated_at_utc` だけの違いを無視する。記事一覧・日付・タイトル等に実質差分がある時だけ更新対象とする。

main起点で実質差分が見つかった場合は、automation branchへコミットし、GitHub ActionsからPR作成を試行する。Repository設定等で自動PR作成が許可されない場合でも、branchは残し、ログへ警告を出す。

## 生成された記事の扱い

カタログに入っただけでは【公式ルール】にならない。

初期分類:

`OFFICIAL_BLOG_CATALOG_ENTRY_UNREVIEWED`

`rule_promotion_allowed` は必ず `false`。

AIまたは人間が記事を読み、

1. 公式本人の記事であることを確認
2. 記事日時を確認
3. ポコニカルに関係する主張を抽出
4. 後年記事との矛盾 / 進化を確認
5. 公式ルール / 設計仕様 / 研究仕様 / 手動入力へ分類
6. 機械判定できるか確認
7. 数値が書かれていなければ推測しない

というレビューを行って初めて既存の `knowledge/*.json` 台帳へ昇格させる。

## Validation / CI

### Parser test

`test_sync_fxclover_catalog.py`

ネットワークへアクセスせず、ローカルHTML文字列だけで以下を確認する。

- h2 / h3記事リンク抽出
- footer等のh5記事を混ぜない
- 外部URLを除外
- `?p=`記事ID以外を除外
- 日付の正規化
- 隣の記事の日付を借りない
- 重複記事の除外
- 新規記事が無いページで停止
- 範囲外ページ404で正常終了
- 1ページ目404は失敗
- 本文をカタログへ保存しない

### Committed catalog validator

`validate_poconical_catalog.py`

PR / push時の `v1.23 integrity` で常時検証する。

主な検査:

- catalogが空でない
- `post_count` と実件数が一致
- URLが `https://fx-clover.com/?p=...` のみ
- post ID重複なし
- category 526のみ
- `OFFICIAL_BLOG_CATALOG_ENTRY_UNREVIEWED` を維持
- `rule_promotion_allowed: false`
- 記事本文 / contentを保存しない
- `pages_scanned` と最大取得ページが一致
- `orders_enabled: false`

## Safety

この機能は知識ベースの情報収集用であり、

- WATCH
- READY
- TRIGGER
- 発注
- 決済

のロジックを変更しない。

`orders_enabled: false` を維持する。
