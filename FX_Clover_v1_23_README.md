# FX-Clover v1.23

ポコニカル専用・GBPJPY・M5必須執行足のマルチタイムフレーム監視版。

## 時間足構成

- D1：データ取得、裁量による大局確認
- H4：データ取得、裁量による上位環境確認
- H1：データ取得。WATCH研究プロキシの参照時間足
- M15：データ取得、中間確認用
- M5：必須の執行足。WATCH・READY・TRIGGER候補を5分確定足で評価

M5必須は今回の確定運用要件として
`DESIGN_TIMEFRAME_CONFIGURATION_USER_CONFIRMED`へ分類する。
公式一次資料のURL・発言位置が登録されるまでは出典付き公式ルール表へ自動昇格しない。

## ポコニカルだけを対象

対象構造は`スラスト → ヨコヨコ → ドーン`。
別案のスラスト戻り売り、エリオット波動カウントは実装しない。
ヨコヨコ、右肩、DMA25×5内側、障害MA、伸びしろ等は手動確認のまま。

## MT4切替手順

1. MetaEditorで`FX_Clover_MTF_Exporter_v1_23.mq4`をコンパイルする。
2. GBPJPY M5チャートを開く。
3. 旧`FX_Clover_M15_Exporter_v1_10`をチャートから外す。
4. 新`FX_Clover_MTF_Exporter_v1_23`をGBPJPY M5チャートへ1つだけ装着する。
5. 自動売買ボタンはオフのままでよい。エクスポーターに注文関数はない。
6. Common FilesへD1/H4/H1/M15/M5の5個のCSVが生成されることを確認する。

## 正式入口（全7件）

1. `RUN_LIVE_CYCLE_v1_23.bat`
2. `INSTALL_5MIN_LIVE_TASK_v1_23.bat`
3. `VERIFY_PACKAGE_v1_23.bat`
4. `TEST_WINDOWS_NOTIFICATION_v1_18.bat`
5. `RUN_SYSTEM_HEALTH_CHECK_v1_23.bat`
6. `START_REVIEW_DESK_v1_13.bat`
7. `RUN_MANUAL_REVIEW_EVALUATION_v1_14.bat`

`INSTALL_5MIN_LIVE_TASK_v1_23.bat`は旧15分タスクを無効化し、
ログオン中の対話セッションへ5分タスクを登録する。

## データ・成績の分離

M5の候補・手動レビュー・通知・状態ファイルは`GBPJPY_M5_*_v1_23`として新設。
既存M15研究成績（293取引、勝率30.38%、PF 0.641）とは混ぜない。
M5について公式勝率・運用勝率はまだ算出していない。

本システムは監視・研究・模擬評価専用であり、実口座への注文機能は存在しない。
