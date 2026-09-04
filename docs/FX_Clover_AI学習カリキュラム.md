# FX-Clover AI学習カリキュラム

Issue: #5

## 目的

FX-Clover / ポコニカルをAIへ「丸暗記」させるのではなく、公式資料を順序付き・出典付きでRepositoryへ構造化し、必要な判断時に検索・参照できる知識ベースを作る。

機械可読版:

- `knowledge/poconical_curriculum.json`
- `knowledge/official_sources.json`
- `knowledge/dma25x5_official_sources.json`

## 最重要方針

公式マスター講座自身が、ポコニカルを単独の裏技ではなく「基礎の集合体」として説明している。

したがってAIも、

環境認識 → ゾーン → MA / グランビル → 波・フォーメーション → 右肩 → Fibonacci → 執行判断 → 損切り / 利確 → 検証

という関係を崩さず学習する。

一部分だけを抜き出して「このローソク足が出たら売り」のようなシステムにはしない。

---

## 推奨取り込み順

### 0. 基礎・講座スタート

- `https://fx-clover.com/?p=7513`
- 公式講座総合入口: `https://fx-clover.com/?page_id=7575`

先に基礎を整えるという公式の学習順をそのまま維持する。

### 1. マスター講座①

- Blog: `https://fx-clover.com/?p=7525`
- Video: `https://youtu.be/EYt3rThjjEA`

主要テーマ:

- フォーメーション右肩
- チャートパターン
- パラメーター
- 移動平均線
- グランビル

### 2. マスター講座②

- Blog: `https://fx-clover.com/?p=7529`
- Video: `https://youtu.be/hbcYrSKrnyc`

主要テーマ:

- ゾーンによる環境認識
- FR
- ゾーンの引き方
- 時間足の使い分け

### 3. マスター講座③

- Blog: `https://fx-clover.com/?p=7535`
- Video: `https://youtu.be/jXwYa9jJ_pg`

主要テーマ:

- 細かいエントリー条件
- エントリーの合図
- どの波のどの部分を狙うか

### 4. マスター講座④

- Blog: `https://fx-clover.com/?p=7540`
- Video: `https://youtu.be/-uxkvMrHS90`

主要テーマ:

- Wフォーメーション
- 1+4のポコ風エリオット
- 右肩の捉え方
- 切り上げ / 斜めライン

### 5. マスター講座⑤

- Blog: `https://fx-clover.com/?p=7545`
- Video: `https://youtu.be/AmLwtgTynX8`

主要テーマ:

- 手法 / 場面の使い分け
- ターゲットゾーン
- グランビル
- 200 / 600パターン
- エントリー / 利確

### 6. 補足講座

- Blog: `https://fx-clover.com/?p=7616`
- Video: `https://youtu.be/mpOlVVHB2h0`

細かなエントリー / 決済とDMA3-3等を補完する。

### 7. 安全な初動・中段レンジ

- `https://fx-clover.com/?p=7924`
- 関連: `https://fx-clover.com/?p=7907`

ポコニカルが転換の初動そのものではなく、調整後の中段レンジ初動を主戦場とする意味を学ぶ。

### 8. 問題集・理解度チェック

- `https://fx-clover.com/?page_id=7731`

AIにとっても、公式側が「何を理解してほしいと考えているか」を抽出する重要な索引として使う。

ただし問題集の短い表現だけで新しい数値ルールを作らない。

### 9. 土曜勉強会・後年記事

マスター講座だけでは不足する実チャート上の例や、後年のルール変化・拡張を追跡する。

古い資料と後年資料が異なる場合は上書きせず、年代差として保存する。

---

## DMA25×5の現在判定

公式根拠:

- `https://fx-clover.com/?p=6913` — 基礎資料で25-5を使用MAとして掲載
- `https://fx-clover.com/?p=9611` — 後年記事で、厳密にはポコニカルはMA25-5を使う旨を本人が明示

よってDMA25×5 / MA25-5自体は【公式コア要素】として扱える。

ただし、現在Repositoryで使われている裁量語「DMA25×5の内側」について、

- ローソク足のどこが内側なら成立か
- ヒゲを含むか
- 実体のみか
- 許容距離
- 何本必要か

等の一次資料による厳密定義はまだ確認できない。

したがって **DMA25×5は公式、`内側`の機械判定は未確定** と分離する。

---

## AI知識ベースの保存単位

各ルールは最低限、以下を持つ。

- `source_url`
- `published / updated`
- `topic`
- `claim`
- `classification`
- `automation_impact`
- `conflict_or_evolution`
- `numeric_definition_status`

分類はProject `AGENTS.md` に従い、

- 公式ルール
- 設計仕様
- 研究仕様
- 手動入力
- 未検証参考情報

を混ぜない。

## 通知システムへの反映条件

公式資料を保存しただけではTRIGGERロジックへ反映しない。

1. 一次資料確認
2. 機械判定可能な定義へ変換
3. 未来足を使わないテストを作成
4. 過去チャートで検証
5. PR / CI / Safety確認
6. 通知専用として反映

の順で進める。

実口座注文は引き続き実装しない。`orders_enabled: false` を維持する。
