# --------------------------
# チーム・スケジュール関係
# --------------------------
# 1半荘の人数
PLAYER_COUNT = 4
# 1カードで実行する半荘数
GAMES_PER_CARD = 2

# レギュラーシーズンラベル
REGULAR_PHASE = "regular"
# セミファイナルラベル
SEMIFINAL_PHASE = "semifinal"
# ファイナルラベル
FINAL_PHASE = "final"

# レギュラーシーズンの1チームあたりの半荘数
REGULAR_GAMES_PER_TEAM = 120
# セミファイナルの1チームあたりの半荘数
SEMIFINAL_GAMES_PER_TEAM = 20
# ファイナルの1チームあたりの半荘数
FINAL_GAMES_PER_TEAM = 16

# レギュラーシーズンチーム数
REGULAR_TEAMS = 10
# セミファイナル進出チーム数
SEMIFINAL_TEAMS = 6
# ファイナル進出チーム数
FINAL_TEAMS = 4

# Mリーグポイント持越率
CARRY_OVER_RATE = 0.5

# --------------------------
# 半荘における点数関係
# --------------------------
# 着順による順位点
RANK_POINT = {1: 50.0, 2: 10.0, 3: -10.0, 4: -30.0}

# 得点の上限と下限
MAX_SCORE = 120000
MIN_SCORE = -60000

# 同卓する4人の得点の合計
TOTAL_SCORE = 100000

# 得点の平均
MEAN_SCORE = 25000
# 得点の標準偏差
STANDARD_DEVIATION_SCORE = 18000
# 得点の最小単位（100点刻み）
SCORE_UNIT = 100

# 素点変換用
POINT_CONVERSION_UNIT = 1000
# 素点の基準点
RETURN_SCORE = 30000

# --------------------------
# 動作確認用
# --------------------------
# 直接実行時の半荘数（動作確認用）
DEFAULT_GAME_COUNT = 4
# 直接実行時のシーズン数（動作確認用）
DEFAULT_SEASON_COUNT = 10
