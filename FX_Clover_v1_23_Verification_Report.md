# FX-Clover v1.23 Verification Report

## 実装

- D1/H4/H1/M15/M5の確定足をMT4 Common Filesへ個別出力。
- M5確定足を執行足とする独立監視経路。
- 5分タスク。旧15分タスクは登録時に無効化。
- M5専用候補キー・手動レビュー・通知・状態ファイル。
- 5時間足の存在・鮮度を確認する健全性診断。
- M5通知を既存Windows通知の成功ACK・失敗再試行へ追加。

## 分類

- M5必須：設計仕様／ユーザー確認済み運用要件
- H1 WATCH自動判定：研究プロキシ
- 未数値化形状：手動入力
- 実口座注文：なし

Windows MT4でのMQL4実コンパイルと5CSV実生成は実機確認が必要。

## 自動検証結果

- unittest: 70件合格
- `test_engine.py` assert形式: 7件合格
- 合計: 77件合格、失敗0件
- v1.23 distribution verifier: PASS
- M5候補キー、5時間足取得、欠落検出、5分タスク配線、旧15分タスク無効化を検証
- M5初回WATCH通知のベースライン化を検証
- 注文実行コード・MQL4注文関数・WebRequestなし
