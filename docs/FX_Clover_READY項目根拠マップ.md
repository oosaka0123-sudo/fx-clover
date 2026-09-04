# FX-Clover READY項目 根拠マップ

Issue: #11

## 目的

v1.23のREADY判定で使う手動6項目について、

- 何がポコ本人の公式概念か
- 何がProject側のレビュー用ラベルか
- 何がまだ数値化できないか

を明確に分離する。

機械可読版:

`knowledge/ready_manual_field_registry.json`

検証:

`validate_ready_field_registry.py`

## 現在の重要原則

現行v1.23では、以下6項目は全て手動入力のまま維持する。

- `mid_range`
- `lower_right_shoulder`
- `inside_dma25x5`
- `ma_path_clear`
- `has_room`
- `upper_environment_valid`

レジストリへ公式根拠が登録されたことは、自動判定可能になったことを意味しない。

---

## mid_range

表示: 中段レンジ

【公式概念】

ポコニカルは転換初動そのものではなく、調整後の中段レンジ・フォーメーション初動を主戦場とする。

主な公式資料:

- https://fx-clover.com/?p=7907
- https://fx-clover.com/?p=7924

【未解決】

開始・終了・必要本数・レンジ幅などの機械判定数値。

---

## lower_right_shoulder

表示: 右肩が低い

【公式概念】

Wトップ / 三尊等の右肩で入ること、右肩の中にさらにフォーメーションができる入れ子構造、上位環境と合わせて判断することは公式資料で強く確認できる。

主な公式資料:

- https://fx-clover.com/?p=6913
- https://fx-clover.com/?p=7195
- https://fx-clover.com/?p=7034
- https://fx-clover.com/?p=7043
- https://fx-clover.com/?p=8075
- https://fx-clover.com/?p=8162

【重要】

`lower_right_shoulder` という現行フィールド名はProjectのレビュー用ラベル。

「右肩は必ず何pips低い」「何%低ければ成立」のような普遍数値は、現時点で公式確認できていない。

したがって、この名称をそのまま公式数値ルールと解釈しない。

---

## inside_dma25x5

表示: DMA25x5内側

【公式概念】

MA25-5 / DMA25x5自体はポコニカルの公式コア要素として確認できる。

主な公式資料:

- https://fx-clover.com/?p=6913
- https://fx-clover.com/?p=9611

【未解決】

「内側」が

- 実体
- ヒゲ
- 始値
- 終値
- 全レート
- 距離許容差
- 必要本数

のどれを意味するかを機械判定できる一次定義は未確認。

---

## ma_path_clear

表示: 障害MAなし

【公式概念】

MAサンド、進行方向のMA、値が伸びる空間を確認する考え方は公式資料に存在する。

主な公式資料:

- https://fx-clover.com/?p=8283
- https://fx-clover.com/?p=9217
- https://fx-clover.com/?p=9734

【未解決】

何pips / ATR何倍離れていれば「障害なし」とするか。

---

## has_room

表示: 下方向の伸びしろ

【公式概念】

進行方向に十分な空間があることを重視する考え方は本人の公式資料で確認できる。

主な公式資料:

- https://fx-clover.com/?p=9217
- https://fx-clover.com/?p=9734

【未解決】

十分な伸びしろをpips / ATR / FE / 障害物距離のどれで定義するか、および固定閾値。

---

## upper_environment_valid

表示: 上位環境有効

【公式概念】

上位足の環境認識を先に行い、下位足の右肩だけで入らないことはポコニカルの重要な公式原則。

主な公式資料:

- https://fx-clover.com/?p=6913
- https://fx-clover.com/?p=6940
- https://fx-clover.com/?p=7086
- https://fx-clover.com/?p=7529

【重要】

現在コードのH1 WATCH自動判定は【研究仕様】のプロキシであり、本人の環境認識ルールそのものではない。

---

## CIによる保護

`validate_ready_field_registry.py` はPython標準ライブラリのASTで `watch_monitor_v1_4.py` の `MANUAL_COLUMNS` を読み取り、レジストリと完全一致するか確認する。

以下の場合はFAILする。

- コード側に新しいREADY手動項目が増えたのに根拠レジストリが無い
- レジストリだけに不要項目が残った
- 公式根拠URLが無い
- 未解決項目が記録されていない
- v1.23で自動判定可と誤って設定された
- `orders_enabled` がfalseでない

これにより、今後AIや別AgentがREADY条件を追加する際に「根拠なしの条件が静かに増える」ことを防ぐ。

## 次版への接続

v1.23のハッシュ固定ファイルは変更しない。

次版ではこのレジストリを使ってレビューデスク上に、各項目の

- 公式概念
- 設計仕様
- 手動入力
- 未解決数値
- 公式出典

を表示できる構造へ進める。

自動判定へ移行するのは、一次資料・機械定義・バックテスト・未来足防止テストが揃った項目だけとする。
