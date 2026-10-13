# Mリーグモンテカルロシミュレーションツール

本ツールは、Mリーグの現行レギュレーションをモデル化し、
仮想的なリーグ戦を多数回実行するためのツールです。
レギュラーシーズン順位と最終順位の関係を分析したり、
アドバンテージやチームの強さ等を調整したりしてシミュレーションすることで、
どのように結果が変わるかを検証するのに使用します。

---

## 使用技術

- Python 3.13.2

---

## ディレクトリ構成（抜粋）

```
MLeagueMontecarloSimulation/
├── app/                          # シミュレーション本体
│   ├── const.py                  # 定数
│   ├── game.py                   # 1半荘の処理
│   ├── main.py                   # シーズンシミュレーション
│   ├── schedule.py               # 対戦スケジュールの作成
│   └── simulate_phase.py         # フェーズのシミュレーション
├── docs/
│   └── specification.md          # 仕様書
├── test/                         # テストコード
│   ├── test_game.py
│   ├── test_main.py
│   ├── test_schedule.py
│   └── test_simulate_phase.py
├── .pre-commit-config.yaml       # コミット前の自動チェック設定
├── AGENTS.md                     # AIへの作業指示
└── README.md                     # プロジェクトの説明
```

---

## Git 運用方針

- main: 本番用、常にデプロイ可能な状態
- feature/〇〇: 機能ごとの開発ブランチ（例：feature/search-function）
- コミットメッセージはプレフィックス付きで明確に（例：fix:, feat:）

---

## 主な開発環境上での実行コマンド

- ツールの実行
```
python -m app.main
```

- テストコードの実行
```
python -m pytest -s test\test_main.py
```
